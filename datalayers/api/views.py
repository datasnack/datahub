from io import BytesIO

import geopandas
import pandas as pd
from shapely import wkt
import numpy as np

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, FileResponse
from django.utils.text import slugify
from django.forms.models import model_to_dict


from shapes.models import Shape, Type
from datalayers.models import Datalayer
from datalayers.utils import get_engine


# Create your views here.


def datalayer(request):
    fmt = request.GET.get('format', 'json')
    datalayers = Datalayer.objects.all()
    rows = []
    name = "datalayers"

    for d in datalayers:
        r = model_to_dict(d)
        r['category'] = d.category.name
        rows.append(r)
    df = pd.DataFrame(rows)

    # return data according to format
    match fmt:
        case 'csv':
            file = BytesIO()
            df.to_csv(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f'{name}.csv')
            response['Content-Type'] = 'text/csv'
            return response
        case 'excel':
            file = BytesIO()
            df.to_excel(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f'{name}.xlsx')
            response['Content-Type'] = 'application/vnd.ms-excel'
            return response
        case _:
            return HttpResponseBadRequest("Invalid format")


def data(request):

    format = request.GET.get('format', 'json')

    # determine filters
    datalayer_id = request.GET.get('datalayer_id', None)
    datalayer = get_object_or_404(Datalayer, pk=datalayer_id)
    name = datalayer.key

    shape_id = request.GET.get('shape_id', None)
    shape = None
    if shape_id is not None:
        shape = get_object_or_404(Shape, pk=shape_id)
        name = f"{name}_{slugify(shape.name)}"

    shape_type_key = request.GET.get('shape_type', None)
    shape_type = None
    if shape_type_key is not None:
        shape_type = get_object_or_404(Type, key=shape_type_key)

    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    # get data
    df = datalayer.data(
        start_date = start_date,
        end_date   = end_date,
        shape      = shape,
        shape_type = shape_type
    )

    # return data according to format
    match format:
        case 'csv':
            file = BytesIO()
            df.to_csv(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f'{name}.csv')
            response['Content-Type'] = 'text/csv'
            return response
        case 'excel':
            file = BytesIO()
            df.to_excel(file, index=False)
            file.seek(0)
            response = FileResponse(file, as_attachment=False, filename=f'{name}.xlsx')
            response['Content-Type'] = 'application/vnd.ms-excel'
            return response
        case 'json':
            return JsonResponse({
                'data': df.fillna(np.nan).replace([np.nan], [None]).to_dict('records'),
            })
        case 'plotly':
            json_data = {
                'x': df[str(datalayer.temporal_resolution)].tolist(),
                'y': df['value'].tolist(),
            }
            return JsonResponse(json_data)
        case _:
            return HttpResponseBadRequest("Invalid format")

def vector(request):
    datalayer_id = request.GET.get('datalayer_id', None)
    datalayer = get_object_or_404(Datalayer, pk=datalayer_id)

    if not datalayer.has_vector_data():
        return HttpResponseNotFound("Data Layer has no raw vector data")

    geojson = datalayer._get_class().vector_data_map()
    return JsonResponse(geojson)


def plotly(request):
    """ Provides download of geometries for specified shapes in a format like
    GeoJSON or GeoPackage.

    Probably could be speed up with not using the ORM, tough the ORM classes
    for models provide ways to access the URL etc. Maybe utilize some sort of
    file caching.

    GeoDjango provides a serializer for GeoJSON like:

    >>> from django.core.serializers import serialize
    >>> serialized_data = serialize("geojson", t.shapes.all(), geometry_field="geometry", fields=["name"])

    But it's unclear to me how put something like the URL or type name into the
    fields. Also the performance seemed not great. Due to the different needed
    formats the approach with GeoPandas and using the same structure seems
    preferable anyway.
    """

    datalayer_id = request.GET.get('datalayer_id', None)
    shape_type_key = request.GET.get('shape_type', None)

    datalayer = get_object_or_404(Datalayer, pk=datalayer_id)
    shape_type = get_object_or_404(Type, key=shape_type_key)

    sql = f"SELECT {datalayer.temporal_resolution}, AVG(value) AS value \
        FROM {datalayer.key} \
        JOIN shapes_shape s ON s.id = {datalayer.key}.shape_id \
        WHERE s.type_id = %(type)s \
        GROUP BY {datalayer.key}.{datalayer.temporal_resolution} \
        ORDER BY {datalayer.temporal_resolution}"

    df = pd.read_sql(sql, con=get_engine(), params={'type': shape_type.id})


    json_data = {
        'x': df[str(datalayer.temporal_resolution)].tolist(),
        'y': df['value'].tolist(),
    }

    return JsonResponse(json_data)

