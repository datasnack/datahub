from io import BytesIO
from typing import Literal

import numpy as np
import pandas as pd
from ninja import File, Query, Router, Schema, Field
from psycopg import sql

from django.db import connection
from django.forms.models import model_to_dict
from django.http import (
    FileResponse,
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

    # get data
    df = datalayer.data(
        start_date=start_date, end_date=end_date, shape=shape, shape_type=shape_type
    )

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
                    "data": df.fillna(np.nan)
                    .replace([np.nan], [None])
                    .to_dict("records"),
                }
            )
        case "plotly":
            if len(resample) > 0:
                df[str(datalayer.temporal_resolution)] = pd.to_datetime(
                    df[str(datalayer.temporal_resolution)]
                )
                df = df.set_index(str(datalayer.temporal_resolution))
                df = df.resample(resample).mean()
                df[str(datalayer.temporal_resolution)] = df.index
                df = df.dropna()

            if shape:
                name = f"{shape.name} ({shape.type.name})"

            json_data = {
                "name": name,
                "type": "scatter",
                "mode": "lines+markers",
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

    if len(resample) > 0:
        df[str(datalayer.temporal_resolution)] = pd.to_datetime(
            df[str(datalayer.temporal_resolution)]
        )
        df = df.set_index(str(datalayer.temporal_resolution))
        df = df.resample(resample).mean()
        df[str(datalayer.temporal_resolution)] = df.index
        df = df.dropna()

    json_data = {
        "traces": [
            {
                #'x': df.index.values.tolist(),
                "name": f"{shape_type.name} (mean)",
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["value"].tolist(),
            },
            {
                "name": f"{shape_type.name} (lower)",
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["min"].tolist(),
                "fill": "tonexty",
                "fillcolor": "rgba(68, 68, 68, 0.3)",
                "line": {"width": 0},
            },
            {
                "name": f"{shape_type.name} (upper)",
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["max"].tolist(),
                "fill": "tonexty",
                "fillcolor": "rgba(68, 68, 68, 0.3)",
                "line": {"width": 0},
            },
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

    res = {
        "plotly": {"layout": layout, "config": {"responsive": True}},
        "datalayer": {
            "temporal_resolution": str(datalayer.temporal_resolution),
            "available_years": datalayer.get_available_years,
            "first_time": datalayer.first_time(),
            "last_time": datalayer.last_time(),
            "shape_types": shape_types,
        },
    }

    return JsonResponse(res)
