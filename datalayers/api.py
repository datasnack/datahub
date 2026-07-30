# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt
import uuid
from io import BytesIO
from typing import Literal

import numpy as np
import pandas as pd
from ninja import Field, Query, Router, Schema
from ninja.errors import AuthorizationError
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


def _get_datalayer_from_request(request, filters) -> Datalayer:
    """
    Detect Datalayer from request by ID or key.

    We can reference a datalayer via ID (datalayer_id) or key (datalayer_key)
    in the request. This function checks for both, but ID has priority over key.
    """
    lookup = (
        {"pk": filters.datalayer_id}
        if filters.datalayer_id
        else {"key": filters.datalayer_key}
    )

    return get_object_or_404(Datalayer.objects.visible_to(request.user), **lookup)


@router.get("datalayer/", summary="Data Layer metadata")
def datalayer(
    request,
    fmt: Literal["json", "csv", "excel"] = Query(
        "json",
        description="File format of response.",
        alias="format",
    ),
):
    datalayers = Datalayer.objects.visible_to(request.user)
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
        description="Filter to specific Shape by it's Data Hub ID.",
    ),
    shape_key: str | None = Query(
        None,
        description="Filter to specific Shape by it's key (takes precedence over shape_id if both are present).",
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
    resample: str | None = Query(
        None,
        description="[Pandas Offset string](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects) for `resample()` function to be applied before returning data. Only works on plotly format.",
    ),
    resample_agg: Literal["mean", "sum"] = Query(
        "mean",
        description="Aggregation function used in the temporal resampling.",
    ),
    aggregate: Literal["sum", "min", "max", "mean", "median", "std", "count"]
    | None = Query(
        None,
        description="[Pandas aggregate function](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.aggregate.html) for `agg()` function to be applied before returning data.",
    ),
    aggregate_group_by: Literal["spatial", "temporal"] = Query(
        "spatial",
        description="Should the aggregation be performed on the spatial or temporal axis?",
    ),
    color: str | None = Query(
        "#3498db",
        description="Color used in returned plotly traces.",
    ),
    fmt: Literal["json", "csv", "excel", "plotly"] = Query(
        "json",
        description="File format of response.",
        alias="format",
    ),
):
    # determine filters
    datalayer = _get_datalayer_from_request(request, filters)
    name = datalayer.key

    if not datalayer.data_visible_to(request.user):
        raise AuthorizationError

    shape = None
    if shape_id is not None:
        shape = get_object_or_404(Shape, pk=shape_id)
        name = f"{name}_{slugify(shape.name)}"
    elif shape_key is not None:
        shape = get_object_or_404(Shape, key=shape_key)
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
        resample=resample,
        resample_agg=resample_agg,
        aggregate=aggregate,
        aggregate_group_by=aggregate_group_by,
    )

    df["formatted"] = df["value"].apply(datalayer.get_class().str_format)

    # return data according to format
    match fmt:
        case "csv":
            file = BytesIO()
            df.to_csv(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=True, filename=f"{name}.csv")
            response["Content-Type"] = "text/csv; charset=utf-8"
            return response
        case "excel":
            file = BytesIO()
            df.to_excel(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=True, filename=f"{name}.xlsx")
            response["Content-Type"] = "application/vnd.ms-excel"
            return response
        case "json":
            return JsonResponse(
                {
                    "value_type": datalayer.value_type_str,
                    "is_categorical": datalayer.is_categorical,
                    "name": datalayer.name,
                    "format_suffix": datalayer.format_suffix(),
                    "categorical_values": datalayer.get_categorical_values(),
                    "categorical_labels": datalayer.get_categorical_labels(),
                    "categorical_colors": datalayer.get_categorical_colors(),
                    "temporal_column": str(datalayer.temporal_resolution),
                    "temporal_format": datalayer.temporal_resolution.format_db(),
                    "data": df.fillna(np.nan)
                    .replace([np.nan], [None])
                    .to_dict("records"),
                }
            )
        case "plotly":
            # In case no data could be selected, we return with 204 No content
            if len(df) == 0:
                return HttpResponse(status=204)

            name = f"{datalayer.name}: "

            if shape:
                name += f"{shape.name} ({shape.key},{shape.type.name})"
            elif shape_type:
                name += f"{shape_type.name}"

            if resample:
                name += f" resample({aggregate})"

            if aggregate:
                name += f" agg({aggregate})"

            chart_type: Literal["scatter", "bar"] = "scatter"
            if datalayer.chart_type == "bar":
                chart_type = "bar"

            # depending on the trace type (scatter -> line, bar -> marker) a different
            # key is used in plotly.js to set the trace color
            trace_color_key = {"scatter": "line", "bar": "marker"}

            json_data = {"traces": []}

            if aggregate:
                # for single shapes -> get first/last date and put in dashed line
                # for shape type
                # -> if min/max is available put in
                if shape_type:
                    if "min" in df.columns and "max" in df.columns:
                        legendgroup_id = uuid.uuid4()
                        color_limits = hex_to_rgba_string(color, alpha=0.8)
                        color_fill = hex_to_rgba_string(color, alpha=0.2)
                        x = df[str(datalayer.temporal_resolution)].tolist()

                        json_data["traces"].append(
                            {
                                "name": f"{name} (max) ",
                                "x": x,
                                "y": df["max"].tolist(),
                                "type": "scatter",
                                "mode": "lines",
                                "line": {
                                    "color": color_limits,
                                    "dash": "longdash",
                                    "width": 1,
                                },
                                "legendgroup": legendgroup_id,
                                "showlegend": False,
                            }
                        )

                        json_data["traces"].append(
                            {
                                "name": f"{name} (min)",
                                "x": x,
                                "y": df["min"].tolist(),
                                "type": "scatter",
                                "mode": "lines",
                                "fill": "tonexty",
                                "fillcolor": color_fill,
                                "line": {
                                    "color": color_limits,
                                    "dash": "longdash",
                                    "width": 1,
                                },
                                "legendgroup": legendgroup_id,
                                "showlegend": False,
                            }
                        )
                        json_data["traces"].append(
                            {
                                "name": f"{name} (avg/min/max)",
                                "type": chart_type,
                                "x": df[str(datalayer.temporal_resolution)].tolist(),
                                "y": df["value"].tolist(),
                                f"{trace_color_key[chart_type]}": {"color": color},
                                "legendgroup": legendgroup_id,
                            }
                        )
                    else:
                        # shape type aggregation that has no min/max
                        json_data["traces"].append(
                            {
                                "name": name,
                                "type": chart_type,
                                "x": df[str(datalayer.temporal_resolution)].tolist(),
                                "y": df["value"].tolist(),
                                f"{trace_color_key[chart_type]}": {"color": color},
                            }
                        )

                else:
                    # single shape with aggregation
                    plotly_start_date = (
                        start_date_obj.strftime("%Y-%m-%d")
                        if start_date_obj
                        else datalayer.first_time()
                    )
                    plotly_end_date = (
                        end_date_obj.strftime("%Y-%m-%d")
                        if end_date_obj
                        else datalayer.last_time()
                    )

                    x = df.loc[0, "value"]
                    if isinstance(x, np.integer):
                        x = int(x)

                    json_data = {
                        "traces": [
                            {
                                "name": name,
                                "mode": "lines",
                                "x": [plotly_start_date, plotly_end_date],
                                "y": [x, x],
                                "line": {"width": 2, "dash": "dash", "color": color},
                            }
                        ]
                    }

                return JsonResponse(json_data)

            # No aggregation multiple shapes from a shape type
            # or single shape
            if shape_type:
                legendgroup_id = uuid.uuid4()
                # differentiate multiple shape in one response
                # -> each shape one trace
                # and single shape -> one trace
                shape_ids = df["dh_shape_id"].unique()
                color = hex_to_rgba_string(color, alpha=0.2)

                for idx, trace_shape_id in enumerate(shape_ids):
                    dfx = df[df["dh_shape_id"] == trace_shape_id]
                    dfx_shape = Shape.objects.get(pk=trace_shape_id)
                    json_data["traces"].append(
                        {
                            "name": f"{name} ({len(shape_ids)} shapes)",
                            "type": chart_type,
                            "x": dfx[str(datalayer.temporal_resolution)].tolist(),
                            "y": dfx["value"].tolist(),
                            f"{trace_color_key[chart_type]}": {"color": color},
                            "legendgroup": legendgroup_id,
                            "showlegend": (idx == 0),
                            "hovertemplate": (
                                f"<b>{dfx_shape.name}</b><br>"
                                "Temporal: %{x}<br>"
                                "Value: %{y}<extra></extra>"
                            ),
                        }
                    )
            else:
                json_data["traces"].append(
                    {
                        "name": f"{name}",
                        "type": chart_type,
                        "x": df[str(datalayer.temporal_resolution)].tolist(),
                        "y": df["value"].tolist(),
                        f"{trace_color_key[chart_type]}": {"color": color},
                    }
                )

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
    datalayer = _get_datalayer_from_request(request, filters)

    if not datalayer.has_vector_data():
        return HttpResponseNotFound("Data Layer has no raw vector data")

    geojson = datalayer.get_class().vector_data_map()
    return JsonResponse(geojson)


def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")

    if len(hex_color) == 3:  # e.g. #f0a
        hex_color = "".join(c * 2 for c in hex_color)

    if len(hex_color) != 6:
        raise ValueError("Hex color must be 3 or 6 characters long.")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b, alpha)


def hex_to_rgba_string(hex_color, alpha=1.0):
    r, g, b, _ = hex_to_rgba(hex_color, alpha)
    return f"rgba({r}, {g}, {b}, {alpha})"


@router.get("meta/", summary="Data Layer Meta and Plot configuration")
def meta(
    request,
    filters: DatalayerFilterSchema = Query(...),
):
    datalayer = _get_datalayer_from_request(request, filters)

    layout = {
        "xaxis": {
            "autorange": True,
            "rangeslider": {},
        },
        "yaxis": {
            "automargin": True,
        },
        "showlegend": True,
        "legend": {
            "orientation": "v",
            "x": 0.0,
            "xanchor": "left",
            "y": -0.65,  # push below the rangeslider
            "yanchor": "top",
        },
        "margin": {
            "t": 12,
            "r": 12,
            "b": 12,
            "l": 12,
            "pad": 0,
        },
        "height": 450,
    }

    # x-axis
    layout["xaxis"].update(
        {
            "title": {"text": datalayer.temporal_resolution.text()},
            "type": "date",
            "hoverformat": datalayer.temporal_resolution.format(),
        }
    )

    # y-axis
    if datalayer.format_suffix():
        layout["yaxis"]["title"] = {"text": f"Value [{datalayer.format_suffix()}]"}
        layout["yaxis"]["ticksuffix"] = datalayer.format_suffix()

    if datalayer.value_type == LayerValueType.PERCENTAGE:
        layout["yaxis"]["tickformat"] = f",.{datalayer.format_precision()}%"
        layout["yaxis"]["range"] = [0, 1]
    elif datalayer.value_type == LayerValueType.INTEGER:
        layout["yaxis"]["tickformat"] = f",d"
    else:
        layout["yaxis"]["tickformat"] = f",.{datalayer.format_precision()}f"

    shape_types = [
        {"name": st.name, "key": st.key} for st in datalayer.get_available_shape_types
    ]
    shapes = []

    # datalayer_shapes = datalayer.get_available_shapes()
    # datalayer_shapes_ids = []
    # for s in datalayer_shapes:
    #    datalayer_shapes_ids.append(s.id)

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

    # all_shapes = load_shapes()
    # tree = build_tree(all_shapes)
    # shapes = collect_shapes(tree, 0)

    shapes = []

    res = {
        "plotly": {
            "layout": layout,
            "config": {
                "responsive": True,
                "displayModeBar": True,
                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            },
        },
        "datalayer": {
            "key": datalayer.key,
            "has_vector_data": datalayer.has_vector_data(),
            "temporal_resolution": str(datalayer.temporal_resolution),
            "available_years": datalayer.get_available_years,
            "first_time": datalayer.first_value().date(),
            "last_time": datalayer.last_value().date(),
            "shape_types": shape_types,
            "shapes": shapes,
            "value_type": datalayer.value_type_str,
            "is_categorical": datalayer.is_categorical,
            "name": datalayer.name,
            "format_suffix": datalayer.format_suffix(),
            "categorical_values": datalayer.get_categorical_values(),
            "categorical_colors": datalayer.get_categorical_colors(),
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
    # rarely used, inlined import for performance reasons
    from datacite import DataCiteRESTClient  # noqa: PLC0415
    from datacite.errors import DataCiteNotFoundError  # noqa: PLC0415

    dc = DataCiteRESTClient(None, None, None)
    res = {}
    try:
        datacite = dc.get_metadata(pid)
        res["datacite"] = datacite

    except DataCiteNotFoundError:
        res["datacite"] = {}

    return JsonResponse(res)
