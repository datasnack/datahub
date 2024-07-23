from io import BytesIO

import geopandas
import numpy as np
import pandas as pd
from psycopg import sql
from shapely import wkt

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

from datalayers.models import Datalayer
from shapes.models import Shape, Type

# Create your views here.


def _get_datalayer_from_request(request) -> Datalayer:
    """
    Detect Datalayer from request by ID or key.

    We can reference a datalayer via ID (datalayer_id) or key (datalayer_key)
    in the request. This function checks for both, but ID has priority over key.
    """
    datalayer_id = request.GET.get("datalayer_id", None)
    datalayer_key = request.GET.get("datalayer_key", None)

    if datalayer_id:
        return get_object_or_404(Datalayer, pk=datalayer_id)
    else:
        return get_object_or_404(Datalayer, key=datalayer_key)


def datalayer(request):
    fmt = request.GET.get("format", "json")
    datalayers = Datalayer.objects.all()
    rows = []
    name = "datalayers"

    for d in datalayers:
        r = model_to_dict(d)

        r["category"] = d.category.name

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


def data(request):
    fmt = request.GET.get("format", "json")

    # determine filters
    datalayer = _get_datalayer_from_request(request)
    name = datalayer.key

    shape_id = request.GET.get("shape_id", None)
    shape = None
    if shape_id is not None:
        shape = get_object_or_404(Shape, pk=shape_id)
        name = f"{name}_{slugify(shape.name)}"

    shape_type_key = request.GET.get("shape_type", None)
    shape_type = None
    if shape_type_key is not None:
        shape_type = get_object_or_404(Type, key=shape_type_key)

    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)

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
            json_data = {
                "x": df[str(datalayer.temporal_resolution)].tolist(),
                "y": df["value"].tolist(),
            }
            return JsonResponse(json_data)
        case _:
            return HttpResponseBadRequest("Invalid format")


def vector(request):
    datalayer = _get_datalayer_from_request(request)

    if not datalayer.has_vector_data():
        return HttpResponseNotFound("Data Layer has no raw vector data")

    geojson = datalayer._get_class().vector_data_map()
    return JsonResponse(geojson)


def plotly(request):
    shape_type_key = request.GET.get("shape_type", None)
    datalayer = _get_datalayer_from_request(request)
    shape_type = get_object_or_404(Type, key=shape_type_key)

    query = sql.SQL(
        "SELECT {temporal_column}, AVG(value) AS value \
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
        con=connection,
        params={"type": shape_type.id},
    )

    # df = df.set_index(str(datalayer.temporal_resolution))
    # df = df.resample('W').mean()

    json_data = {
        #'x': df.index.values.tolist(),
        "x": df[str(datalayer.temporal_resolution)].tolist(),
        "y": df["value"].tolist(),
    }

    return JsonResponse(json_data)
