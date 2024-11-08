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


def get_dl_count_for_year_shapes(request):
    parent_id = request.GET['parent_id']
    if parent_id:
        shapes = Shape.objects.filter(parent_id=parent_id)
    else:
        highest_type = Type.objects.order_by('position').first()
        shapes = Shape.objects.filter(type_id=highest_type.id)

    year = int(request.GET['year'])

    shape_dlcount_dict = {shape.id: 0 for shape in shapes}
    shape_dl_dict = {shape.id: [] for shape in shapes}

    for datalayer in Datalayer.objects.all():
        table_name = datalayer.key
        for shape in shapes:
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

                else:
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
                shape_dl_dict.get(shape.id).append(datalayer.name)

    geometries = {}
    names = {}
    for shape in shapes:
        geometries[shape.id] = shape.geometry.geojson
        names[shape.id] = shape.name

    context = {
        'shape_dlcount_dict': shape_dlcount_dict,
        'shape_dl_dict': shape_dl_dict,
        'geometries': geometries,
        'names': names,
    }

    return JsonResponse(context, safe=False)


def info_map_base(request):
    highest_type = Type.objects.order_by('position').first()
    highest_shape = Shape.objects.filter(type_id=highest_type.id).first()

    datalayers = Datalayer.objects.all()

    min_year = dt.date.today().year
    max_year = 0

    for dl in datalayers:
        table_name = dl.key
        try:
            query = f"""
                        SELECT MIN(year), MAX(year)
                        FROM {table_name}
                    """
            with connection.cursor() as c:
                c.execute(query)
                res = c.fetchone()
            min_available_year = res[0]
            max_available_year = res[1]

        except ProgrammingError as e:
            min_available_year = dt.date.today().year
            max_available_year = 0

        if min_year > min_available_year:
            min_year = min_available_year
        if max_year < max_available_year:
            max_year = max_available_year

    years = range(int(min_year), int(max_year) + 1)

    context = {
        'highest_shape_geometry': highest_shape.geometry.geojson,
        'highest_shape_name': highest_shape.name,
        'years': years,
        'datahub_center_x': settings.DATAHUB_CENTER_X,
        'datahub_center_y': settings.DATAHUB_CENTER_Y,
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM
    }

    return render(request, 'info_map.html', context)


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


def get_historical_data_shape(request):
    shape_id = request.GET.get('shape_id')
    data_layer_key = request.GET.get('data_layer_key')
    shape_name = Shape.objects.get(id=shape_id).name

    data = get_historical_data(shape_id, data_layer_key)

    context = {
        'historical_data': data,
        'shape_name': shape_name,
    }

    return JsonResponse(context, safe=False)


def get_shapes_by_shape_id(request):
    type_id = request.GET.get('type_id')
    if type_id:
        shapes = Shape.objects.filter(type_id=type_id).order_by('name')
    else:
        shapes = Shape.objects.all()
    return JsonResponse(list(shapes.values('id', 'name')), safe=False)


def slider_base(request):
    shape_types = Type.objects.order_by('position')[1:]
    datalayers = Datalayer.objects.all()

    context = {
        "shape_types": shape_types,
        "datalayers": datalayers,
        'datahub_center_x': settings.DATAHUB_CENTER_X,
        'datahub_center_y': settings.DATAHUB_CENTER_Y,
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM
    }

    return render(request, 'slider.html', context)


def get_datalayer_available_years(request):
    data_layer_key = request.GET.get('data_layer_key')
    data_layer = Datalayer.objects.get(key=data_layer_key)
    if data_layer:
        available_years = data_layer.get_available_years
    else:
        available_years = []
    return JsonResponse(available_years, safe=False)


def get_dl_value_for_year_shapes(request):
    data_layer_key = request.GET.get('data_layer_key')
    year = request.GET.get('year')
    shape_type = request.GET.get('shape_type')


    data_layer = Datalayer.objects.get(key=data_layer_key)
    shapes = Shape.objects.filter(type_id=shape_type)

    if not year:
        year = data_layer.get_available_years[0]

    geometries = {}
    names = {}
    dl_values = {}

    if data_layer:
        for shape in shapes:
            geometries[shape.id] = shape.geometry.geojson
            names[shape.id] = shape.name
            if data_layer.temporal_resolution == LayerTimeResolution.YEAR:
                query = f"""
                            SELECT value
                            FROM {data_layer_key}
                            WHERE shape_id = %s AND year = %s
                        """
                with connection.cursor() as c:
                    c.execute(query, [shape.id, year])
                    res = c.fetchone()
            else:
                query = f"""
                            SELECT AVG(value)
                            FROM {data_layer_key}
                            WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
                        """
                with connection.cursor() as c:
                    c.execute(query, [shape.id, year])
                    res = c.fetchone()

            if res is not None:
                value = res[0]
                dl_values[shape.id] = value

    context = {
        'geometries': geometries,
        'names': names,
        'dl_values': dl_values
    }

    return JsonResponse(context, safe=False)


def get_historical_data_highest_type(request):
    data_layer_key = request.GET.get('data_layer_key')
    highest_type = Type.objects.order_by('position').first()
    highest_shape = Shape.objects.filter(type_id=highest_type.id).first()
    highest_shape_name = highest_shape.name

    historical_data = get_historical_data(highest_shape.id, data_layer_key)

    context = {
        'historical_data': historical_data,
        'highest_shape_name': highest_shape_name,
    }

    return JsonResponse(context, safe=False)


def get_historical_data(shape_id, data_layer_key):
    data_layer = get_object_or_404(Datalayer, key=data_layer_key)

    years = data_layer.get_available_years
    table_name = data_layer_key
    data = []

    for year in years:
        if data_layer.temporal_resolution == LayerTimeResolution.YEAR:
            query = f"""
                            SELECT value
                            FROM {table_name}
                            WHERE shape_id = %s AND year = %s
                        """
            with connection.cursor() as c:
                c.execute(query, [shape_id, year])
                res = c.fetchone()
        else:
            query = f"""
                            SELECT AVG(value)
                            FROM {table_name}
                            WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
                        """
            with connection.cursor() as c:
                c.execute(query, [shape_id, year])
                res = c.fetchone()

        if res is not None:
            value = res[0]
            data.insert(0, {
                'year': year,
                'value': value
            })

    return data


def get_min_max_dl_value(request):
    data_layer_key = request.GET.get('data_layer_key')
    shape_type = request.GET.get('shape_type')

    query = f"""
                SELECT MIN(value), MAX(value)
                FROM {data_layer_key} JOIN shapes_shape ON {data_layer_key}.shape_id = shapes_shape.id JOIN shapes_type ON shapes_shape.type_id = shapes_type.id
                WHERE shapes_type.id = {shape_type}

                """
    with connection.cursor() as c:
        c.execute(query)
        res = c.fetchone()

    min_value = res[0]
    max_value = res[1]

    context = {
        'min_value': min_value,
        'max_value': max_value
    }

    return JsonResponse(context, safe=False)


