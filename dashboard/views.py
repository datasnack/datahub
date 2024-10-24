from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db import connection, ProgrammingError
import datetime as dt

from datalayers.datasources.base_layer import LayerTimeResolution
from shapes.models import Type, Shape
from datalayers.models import Datalayer


def home(request):
    return render(request, 'home.html')


def info_map_base(request):
    shape_types = Type.objects.all()
    datalayers = Datalayer.objects.all()

    min_year = dt.date.today().year
    max_year = 0

    for dl in datalayers:
        available_years = dl.get_available_years
        if available_years:
            min_available_year = min(available_years)
            max_available_year = max(available_years)
            if min_year > min_available_year:
                min_year = min_available_year
            if max_year < max_available_year:
                max_year = max_available_year

    years = range(int(min_year), int(max_year) + 1)

    context = {
        'shape_types': shape_types,
        'years': years,
        'datahub_center_x': settings.DATAHUB_CENTER_X,
        'datahub_center_y': settings.DATAHUB_CENTER_Y,
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM
    }

    return render(request, 'info_map.html', context)


def get_dl_count_for_year_shape(request):
    shape_type = request.GET['shape_type']
    shapes = Shape.objects.filter(type_id=shape_type)

    year = int(request.GET['year'])

    shape_dlcount_dict = {shape.id: 0 for shape in shapes}

    for datalayer in Datalayer.objects.all():
        table_name = datalayer.key
        for shape in shapes:
            rec_count = 0
            try:
                if datalayer.temporal_resolution == LayerTimeResolution.YEAR:
                    query = f"""
                                SELECT COUNT(*)
                                FROM {table_name}
                                WHERE shape_id = %s AND year = %s
                    """
                    with connection.cursor() as c:
                        c.execute(query, [shape.id, year])
                        rec_count = c.fetchone()[0]

                elif datalayer.temporal_resolution == LayerTimeResolution.DAY:
                    query = f"""
                                SELECT COUNT(*)
                                FROM {table_name}
                                WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
                    """
                    with connection.cursor() as c:
                        c.execute(query, [shape.id, year])
                        rec_count = c.fetchone()[0]

            except ProgrammingError as e:
                rec_count = 0

            if rec_count > 0:
                shape_dlcount_dict[shape.id] += 1

    context = {
        'shape_dlcount': shape_dlcount_dict
    }

    return JsonResponse(context, safe=False)


def get_shape_type_geometries(request):
    shape_type = request.GET['shape_type']
    shapes = Shape.objects.filter(type_id=shape_type)

    geometries = {}
    names = {}
    for shape in shapes:
        geometries[shape.id] = shape.geometry.geojson
        names[shape.id] = shape.name

    context = {
        "geometries": geometries,
        "names": names
    }

    return JsonResponse(context, safe=False)


def temporal_trend_base(request):
    types = Type.objects.all().order_by('id')
    datalayers = Datalayer.objects.all()

    context = {
        'types': types,
        'datalayers': datalayers,
        'datahub_center_x': settings.DATAHUB_CENTER_X,
        'datahub_center_y': settings.DATAHUB_CENTER_Y,
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM
    }
    return render(request, 'temporal_trend.html', context)

def get_geometry_shape(request):
    shape_id = request.GET.get('shape_id')
    shape = get_object_or_404(Shape, id=shape_id)

    data = {
        "type": "Feature",
        "geometry": shape.geometry.geojson
    }

    return JsonResponse(data, safe=False)

def get_historical_data(request):
    shape_id = request.GET.get('shape_id')
    data_layer_key = request.GET.get('data_layer_key')

    shape = get_object_or_404(Shape, id=shape_id)
    data_layer = get_object_or_404(Datalayer, key=data_layer_key)

    years = data_layer.get_available_years
    table_name = data_layer.key
    data = []

    for year in years:
        if data_layer.temporal_resolution == LayerTimeResolution.YEAR:
            value_obj = data_layer.value(shape=shape, when=dt.datetime(year, 1, 1))
            value = value_obj.value
        elif data_layer.temporal_resolution == LayerTimeResolution.DAY:
            query = f"""
                        SELECT AVG(value)
                        FROM {table_name}
                        WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
                    """
            with connection.cursor() as c:
                c.execute(query, [shape.id, year])
                value = c.fetchone()[0]
        data.insert(0, {
            'year': year,
            'value': value
        })

    return JsonResponse(data, safe=False)


def slider_base(request):
    shape_types = Type.objects.all()
    datalayers = Datalayer.objects.all()

    context = {
        "shape_types": shape_types,
        "datalayers": datalayers
    }

    return render(request, 'slider.html', context)


def get_shapes_by_shape_id(request):
    type_id = request.GET.get('type_id')
    if type_id:
        shapes = Shape.objects.filter(type_id=type_id).order_by('name')
    else:
        shapes = Shape.objects.all()
    return JsonResponse(list(shapes.values('id', 'name')), safe=False)


def get_datalayer_available_years(request):
    data_layer_key = request.GET.get('data_layer_key')
    data_layer = Datalayer.objects.get(key=data_layer_key)
    if data_layer:
        available_years = data_layer.get_available_years
    else:
        available_years = []
    return JsonResponse(available_years, safe=False)
