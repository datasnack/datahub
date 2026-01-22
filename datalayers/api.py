# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt
from io import BytesIO
from typing import Literal

import numpy as np
import pandas as pd
from ninja import Field, Query, Router, Schema
from ninja.security import SessionAuth
from psycopg import sql

from django.db import connection
from django.forms.models import model_to_dict
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from datalayers.datasources.base_layer import LayerTimeResolution, LayerValueType
from datalayers.models import Datalayer
from datalayers.utils import get_conn_string
from shapes.models import Shape, Type

router = Router(tags=["Data Layers"])


class DatalayerFilterSchema(Schema):
    datalayer_id: int | None = Field(
        None, description="Required if datalayer_key is not set."
    )
    datalayer_key: str | None = Field(
        None, description="Required if datalayer_id is not set."
    )


def _get_datalayer_from_request(filters) -> Datalayer:
    """
    Detect Datalayer from request by ID or key.

    We can reference a datalayer via ID (datalayer_id) or key (datalayer_key)
    in the request. This function checks for both, but ID has priority over key.
    """
    datalayer_id = filters.datalayer_id
    datalayer_key = filters.datalayer_key

    if datalayer_id:
        return get_object_or_404(Datalayer, pk=datalayer_id)

    return get_object_or_404(Datalayer, key=datalayer_key)


@router.get("datalayer/", summary="Data Layer metadata")
def datalayer(
    request,
    fmt: Literal["json", "csv", "excel"] = Query(  # noqa: B008
        "json",
        description="File format of response.",
        alias="format",
    ),
):
    datalayers = Datalayer.objects.all()
    rows = []
    name = "datalayers"

    # handle json before other formats, because we don't need to flatten the
    # nested structure
    if fmt == "json":
        # JsonResponse requires a dict on the top level
        data = {"data": []}

        for d in datalayers:
            r = model_to_dict(d)

            # category is not required!
            r["category"] = d.category.name if d.category else None

            tags = d.tags.all()
            r["tags"] = []
            for t in tags:
                r["tags"].append(model_to_dict(t))

            related = d.related_to.all()
            r["related_to"] = []
            for rl in related:
                r["related_to"].append(rl.key)

            r["sources"] = []
            sources = d.sources.all()
            for _, s in enumerate(sources):
                rs = {}
                rs["pid_type"] = s.pid_type
                rs["pid"] = s.pid
                rs["description"] = s.description

                r["sources"].append(rs)
            data["data"].append(r)

        # print(data)
        return JsonResponse(data)

    for d in datalayers:
        r = model_to_dict(d)

        # category is not required!
        r["category"] = d.category.name if d.category else None

        tags = d.tags.all()
        r["tags"] = []
        for t in tags:
            r["tags"].append(t.name)
        r["tags"] = ",".join(r["tags"])

        related = d.related_to.all()
        r["related_to"] = []
        for rl in related:
            r["related_to"].append(rl.key)
        r["related_to"] = ",".join(r["related_to"])

        sources = d.sources.all()

        for i, s in enumerate(sources):
            key = f"source_{i}"
            r[f"{key}_pid_type"] = s.pid_type
            r[f"{key}_pid"] = s.pid
            r[f"{key}_description"] = s.description

        rows.append(r)
    df = pd.DataFrame(rows)

    # return data according to format
    match fmt:
        case "csv":
            file = BytesIO()
            df.to_csv(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f"{name}.csv")
            response["Content-Type"] = "text/csv"
            return response
        case "excel":
            file = BytesIO()
            df.to_excel(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f"{name}.xlsx")
            response["Content-Type"] = "application/vnd.ms-excel"
            return response
        case _:
            return HttpResponseBadRequest("Invalid format")


@router.get(
    "data/",
    summary="Data download",
    description="Access the harmonized data of a Data Layer.",
)
def data(
    request,
    filters: DatalayerFilterSchema = Query(...),
    shape_id: int | None = Query(
        None,
        description="Filter to specific Shape",
    ),
    shape_type_key: str | None = Query(
        None, description="Filter to specific Shape Type", alias="shape_type"
    ),
    start_date: str | None = Query(
        None,
        description="Include only data at/after the given date. Format according to Data Layer time type.",
    ),
    end_date: str | None = Query(
        None,
        description="Include only data before/at the given date. Format according to Data Layer time type.",
    ),
    aggregate: Literal["sum", "min", "max", "mean", "median", "std", "count"]
    | None = Query(
        None,
        description="[Pandas aggregate function](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.aggregate.html) for `agg()` function to be applied before returning data.",
    ),
    resample: str | None = Query(
        None,
        description="[Pandas Offset string](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects) for `resample()` function to be applied before returning data. Only works on plotly format.",
    ),
    fmt: Literal["json", "csv", "excel", "plotly"] = Query(
        "json",
        description="File format of response.",
        alias="format",
    ),
):
    # determine filters
    datalayer = _get_datalayer_from_request(filters)
    name = datalayer.key

    shape = None
    if shape_id is not None:
        shape = get_object_or_404(Shape, pk=shape_id)
        name = f"{name}_{slugify(shape.name)}"

    shape_type = None
    if shape_type_key is not None:
        shape_type = get_object_or_404(Type, key=shape_type_key)

    # parse date to datetime
    start_date_obj = None
    end_date_obj = None
    if start_date:
        # we use ISO weeks exclusively so we need to tell the parser that it starts on monday.
        if datalayer.temporal_resolution == LayerTimeResolution.WEEK:
            start_date += "-1"
        try:
            start_date_obj = dt.datetime.strptime(
                start_date, datalayer.temporal_resolution.format()
            )
        except ValueError:
            return HttpResponse(
                f"Start date is not valid for data layer, needed format is `{datalayer.temporal_resolution.format()}`",
                status=422,
            )
    if end_date:
        # we use ISO weeks exclusively so we need to tell the parser that it starts on monday.
        if datalayer.temporal_resolution == LayerTimeResolution.WEEK:
            end_date += "-1"

        try:
            end_date_obj = dt.datetime.strptime(
                end_date, datalayer.temporal_resolution.format()
            )
        except ValueError:
            return HttpResponse(
                f"End date is not valid for data layer, needed format is `{datalayer.temporal_resolution.format()}`",
                status=422,
            )

    # get data
    df = datalayer.data(
        start_date=start_date_obj,
        end_date=end_date_obj,
        shape=shape,
        shape_type=shape_type,
    )

    # if a aggregate function is presents
    if aggregate:
        df = df.groupby("dh_shape_id", as_index=False)["value"].agg(aggregate)

    # return data according to format
    match fmt:
        case "csv":
            file = BytesIO()
            df.to_csv(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f"{name}.csv")
            response["Content-Type"] = "text/csv"
            return response
        case "excel":
            file = BytesIO()
            df.to_excel(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f"{name}.xlsx")
            response["Content-Type"] = "application/vnd.ms-excel"
            return response
        case "json":
            return JsonResponse(
                {
                    "temporal_column": str(datalayer.temporal_resolution),
                    "temporal_format": datalayer.temporal_resolution.format_db(),
                    "data": df.fillna(np.nan)
                    .replace([np.nan], [None])
                    .to_dict("records"),
                }
            )
        case "plotly":
            if shape:
                name = f"{shape.name} ({shape.type.name})"

            if aggregate:
                if start_date is None:
                    start_date = datalayer.first_time()
                if end_date is None:
                    end_date = datalayer.last_time()

                x = df.loc[0, "value"]
                if isinstance(x, np.integer):
                    x = int(x)

                json_data = {
                    "name": f"{name} ({aggregate}, {start_date}-{end_date})",
                    "mode": "lines",
                    "x": [start_date, end_date],
                    "y": [x, x],
                    "line": {"width": 2, "dash": "dash"},
                }
                return JsonResponse(json_data)

            if resample and len(resample) > 0:
                df[str(datalayer.temporal_resolution)] = pd.to_datetime(
                    df[str(datalayer.temporal_resolution)]
                )
                df = df.set_index(str(datalayer.temporal_resolution))
                df = df.resample(resample).mean()
                df[str(datalayer.temporal_resolution)] = df.index
                df = df.dropna()

            chart_type = "scatter"
            if datalayer.chart_type == "bar":
                chart_type = "bar"

            json_data = {
                "name": name,
                "type": chart_type,
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["value"].tolist(),
            }
            return JsonResponse(json_data)
        case _:
            return HttpResponseBadRequest("Invalid format")


@router.get(
    "vector/",
    summary="Data Layer vector data",
    description="Returns associated vector data with the Data Layer if available.",
)
def vector(
    request,
    filters: DatalayerFilterSchema = Query(...),
):
    datalayer = _get_datalayer_from_request(filters)

    if not datalayer.has_vector_data():
        return HttpResponseNotFound("Data Layer has no raw vector data")

    geojson = datalayer._get_class().vector_data_map()
    return JsonResponse(geojson)


@router.get("plotly/", summary="Plotly min/max/mean traces")
def plotly(
    request,
    filters: DatalayerFilterSchema = Query(...),
    shape_type_key: str | None = Query(..., alias="shape_type"),
    aggregate: Literal["sum", "min", "max", "mean", "median", "std", "count"]
    | None = Query(
        None,
        description="[Pandas aggregate function](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.aggregate.html) for `agg()` function to be applied before returning data.",
    ),
    resample: str | None = Query(
        None,
        description="[Pandas Offset string](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects) for `resample()` function to be applied before returning data. Only works on plotly format.",
    ),
):
    datalayer = _get_datalayer_from_request(filters)
    shape_type = get_object_or_404(Type, key=shape_type_key)

    # Aggregation over a shape type is not possible with categorical values
    if datalayer.value_type in [
        LayerValueType.NOMINAL,
        LayerValueType.ORDINAL,
        LayerValueType.BINARY,
    ]:
        return JsonResponse({"traces": []})

    query = sql.SQL(
        "SELECT {temporal_column}, AVG(value) AS value, MIN(value) AS min, MAX(value) AS max \
        FROM {table} \
        JOIN shapes_shape s ON s.id = {table}.shape_id \
        WHERE s.type_id = %(type)s \
        GROUP BY {table}.{temporal_column} \
        ORDER BY {temporal_column}"
    ).format(
        table=sql.Identifier(datalayer.key),
        temporal_column=sql.Identifier(str(datalayer.temporal_resolution)),
    )

    df = pd.read_sql(
        query.as_string(connection),
        con=get_conn_string(),
        params={"type": shape_type.id},
    )

    if resample and len(resample) > 0:
        df[str(datalayer.temporal_resolution)] = pd.to_datetime(
            df[str(datalayer.temporal_resolution)]
        )
        df = df.set_index(str(datalayer.temporal_resolution))
        df = df.resample(resample).mean()
        df[str(datalayer.temporal_resolution)] = df.index
        df = df.dropna()

    if aggregate:
        start_date = datalayer.first_time()
        end_date = datalayer.last_time()

        x = df["value"].agg(aggregate)
        if isinstance(x, np.integer):
            x = int(x)

        json_data = {
            "traces": [
                {
                    "name": f"{shape_type.name} ({aggregate}, {start_date}-{end_date})",
                    "mode": "lines",
                    "x": [start_date, end_date],
                    "y": [x, x],
                    "line": {"width": 2, "dash": "dash"},
                }
            ]
        }
        return JsonResponse(json_data)

    # calculate deviation from mean
    df["value_plus"] = df["max"] - df["value"]
    df["value_minus"] = df["value"] - df["min"]

    # if both max/min series are 0 there is no deviation and we do not need to show
    # error bars, this reduces the visual noise in the chart.
    show_error = not ((df["value_plus"] == 0).all() and (df["value_minus"] == 0).all())

    chart_type = "scatter"
    if datalayer.chart_type == "bar":
        chart_type = "bar"

    json_data = {
        "traces": [
            {
                #'x': df.index.values.tolist(),
                "name": f"{shape_type.name} (mean)",
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["value"].tolist(),
                "type": chart_type,
                "error_y": {
                    "type": "data",
                    "symmetric": False,
                    "array": df["value_plus"].tolist(),
                    "arrayminus": df["value_minus"].tolist(),
                }
                if show_error
                else None,
            }
        ]
    }

    return JsonResponse(json_data)


@router.get("meta/", summary="Data Layer Meta and Plot configuration")
def meta(
    request,
    filters: DatalayerFilterSchema = Query(...),
):
    datalayer = _get_datalayer_from_request(filters)

    layout = {
        "title": {
            "text": datalayer.name,
            "subtitle": {
                "text": datalayer.key,
            },
        },
        "xaxis": {},
        "yaxis": {"automargin": True},
        "showlegend": True,
        "legend": {
            "orientation": "h",
            "x": 0,
            "y": -0.2,
        },
        "height": 450,
        "margin": {"l": 50, "r": 10, "b": 100, "t": 50, "pad": 4},
    }

    if datalayer.temporal_resolution == LayerTimeResolution.YEAR:
        layout["xaxis"] = {"title": "Year", "type": "date", "hoverformat": "%Y"}
    elif datalayer.temporal_resolution == LayerTimeResolution.DAY:
        layout["xaxis"] = {"title": "Date", "type": "date", "hoverformat": "%Y-%m-%d"}

    if datalayer.format_suffix():
        layout["yaxis"]["title"] = f"Value [{datalayer.format_suffix()}]"
    else:
        layout["yaxis"]["title"] = "Value"

    if datalayer.value_type == LayerValueType.PERCENTAGE:
        layout["yaxis"]["tickformat"] = f",.{datalayer.format_precision()}%"
        layout["yaxis"]["range"] = [0, 1]
    elif datalayer.value_type == LayerValueType.VALUE:
        layout["yaxis"]["tickformat"] = f",.{datalayer.format_precision()}f"

    shape_types = [
        {"name": st.name, "key": st.key} for st in datalayer.get_available_shape_types
    ]
    shapes = []

    datalayer_shapes = datalayer.get_available_shapes()
    datalayer_shapes_ids = []
    for s in datalayer_shapes:
        datalayer_shapes_ids.append(s.id)

    # todo: access to the shape hierarchy via the ORM is slow, for now we fetch the hierarchy manually.

    # def collect_shapes(shapes: list[Shape], level: int = 0) -> list:
    #    collected_entries = []
    #    for shape in shapes:
    #        prefix = level * " -" + " " if level > 0 else ""
    #        collected_entries.append(
    #            {
    #                "name": f"{prefix}{shape.name} ({shape.key})",
    #                "key": shape.key,
    #                "id": shape.id,
    #                "disabled": shape not in datalayer_shapes,
    #            }
    #        )
    #
    #        if child_shapes := shape.children.all():
    #            collected_entries += collect_shapes(child_shapes, level + 1)
    #
    #    return collected_entries
    #
    # top_shapes = Shape.objects.filter(parent_id__isnull=True)
    # shapes = collect_shapes(top_shapes, 0)

    def load_shapes() -> list[dict]:
        """Fetch shape infos without ORM for performance."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, parent_id, key
                FROM shapes_shape
            """)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return rows  # noqa: RET504 connection needs to be open while we build rows

    def build_tree(flat_list: list[dict]) -> list[dict]:
        """Take flat list of shape dicts with id/parent_id keys and sort them hierarchical, by adding children: list."""
        nodes = {item["id"]: {**item, "children": []} for item in flat_list}
        roots = []

        for node in nodes.values():
            parent_id = node["parent_id"]
            if parent_id is None:
                roots.append(node)
            else:
                parent = nodes.get(parent_id)
                if parent:
                    parent["children"].append(node)

        return roots

    def collect_shapes(shapes: list, level: int = 0) -> list:
        collected_entries = []
        for shape in shapes:
            prefix = level * " -" + " " if level > 0 else ""
            collected_entries.append(
                {
                    "name": f"{prefix}{shape['name']} ({shape['key']})",
                    "key": shape["key"],
                    "id": shape["id"],
                    "disabled": shape["id"] not in datalayer_shapes_ids,
                }
            )

            if len(shape["children"]) > 0:
                collected_entries += collect_shapes(shape["children"], level + 1)

        return collected_entries

    all_shapes = load_shapes()
    tree = build_tree(all_shapes)
    shapes = collect_shapes(tree, 0)

    res = {
        "plotly": {"layout": layout, "config": {"responsive": True}},
        "datalayer": {
            "key": datalayer.key,
            "has_vector_data": datalayer.has_vector_data(),
            "temporal_resolution": str(datalayer.temporal_resolution),
            "available_years": datalayer.get_available_years,
            "first_time": datalayer.first_time(),
            "last_time": datalayer.last_time(),
            "shape_types": shape_types,
            "shapes": shapes,
            "value_type": datalayer.value_type_str,
            "name": datalayer.name,
            "format_suffix": datalayer.format_suffix(),
        },
    }

    return JsonResponse(res)


@router.get(
    "datacite/",
    auth=[SessionAuth()],
    include_in_schema=False,
    summary="Fetch DOI metadata from DataCite API",
)
def datacite(request, pid: str):
    from datacite import DataCiteRESTClient
    from datacite.errors import DataCiteNotFoundError

    dc = DataCiteRESTClient(None, None, None)
    res = {}
    try:
        datacite = dc.get_metadata(pid)
        res["datacite"] = datacite

    except DataCiteNotFoundError:
        res["datacite"] = {}

    return JsonResponse(res)
