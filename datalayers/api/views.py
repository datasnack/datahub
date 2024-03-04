from io import BytesIO

import geopandas
import pandas as pd
from shapely import wkt
import numpy as np

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.text import slugify

from shapes.models import Shape, Type
from datalayers.models import Datalayer
from datalayers.utils import get_engine


# Create your views here.

def data(request):

    datalayer_id = request.GET.get('datalayer_id', None)
    datalayer = get_object_or_404(Datalayer, pk=datalayer_id)
    shape_type_key = request.GET.get('shape_type', None)
    shape_type = None

    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)


    params = {}

    if shape_type_key is not None:
        shape_type = get_object_or_404(Type, key=shape_type_key)

    sql = f"SELECT {datalayer.key} as {datalayer.key}, shape_id, {datalayer.temporal_resolution} \
        FROM {datalayer.key} "

    # JOIN
    if shape_type:
        sql += f"JOIN shapes_shape s ON s.id = {datalayer.key}.shape_id "


    # WHERE
    sql += "WHERE 1=1 "

    if start_date:
        sql += f"AND {datalayer.temporal_resolution} >= %(start_date)s "
        params['start_date'] = start_date

    if end_date:
        sql += f"AND {datalayer.temporal_resolution} <= %(end_date)s "
        params['end_date'] = end_date

    if shape_type:
        sql += "AND s.type_id = %(type)s"
        params['type'] = shape_type.id

    print(sql)

    df = pd.read_sql(sql, con=get_engine(), params=params)

    return JsonResponse({
        'data': df.fillna(np.nan).replace([np.nan], [None]).to_dict('records'),
    })


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

    sql = f"SELECT {datalayer.temporal_resolution}, AVG({datalayer.key}) as {datalayer.key} \
        FROM {datalayer.key} \
        JOIN shapes_shape s ON s.id = {datalayer.key}.shape_id \
        WHERE s.type_id = %(type)s \
        GROUP BY {datalayer.key}.{datalayer.temporal_resolution} \
        ORDER BY {datalayer.temporal_resolution}"

    df = pd.read_sql(sql, con=get_engine(), params={'type': shape_type.id})


    json_data = {
        'x': df[str(datalayer.temporal_resolution)].tolist(),
        'y': df[datalayer.key].tolist(),
    }

    return JsonResponse(json_data)

