from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db import connection

from dashboard.models import ShapeDataLayerYearStats
from shapes.models import Type, Shape
from datalayers.models import Datalayer


def home(request):
    return render(request, 'home.html')


def info_map_base(request):
    datalayers = Datalayer.objects.all()

    first_entry = ShapeDataLayerYearStats.objects.order_by('year').first()
    min_year = first_entry.year if first_entry else None
    last_entry = ShapeDataLayerYearStats.objects.order_by('year').last()
    max_year = last_entry.year if last_entry else None

    types = Type.objects.order_by('position')

    context = {
        'datalayers': datalayers,
        'min_year': min_year,
        'max_year': max_year,
        'types': types,
        'datahub_center_x': settings.DATAHUB_CENTER_X,
        'datahub_center_y': settings.DATAHUB_CENTER_Y,
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM
    }

    return render(request, 'info_map.html', context)


def get_dl_count_for_year_shapes(request):
    data_layers = request.GET.get('data_layers', '').split(',')
    type_id = request.GET.get('type_id')
    year = int(request.GET['year'])

    shapes = Shape.objects.filter(type_id=type_id)
    shape_dlcount_dict = {shape.id: 0 for shape in shapes}
    shape_dl_dict = {shape.id: [] for shape in shapes}
    shape_missing_dl_dict = {shape.id: [] for shape in shapes}

    for datalayer_str in data_layers:
        datalayer_name = Datalayer.objects.get(key=datalayer_str).name
        for shape in shapes:
            try:
                stat = ShapeDataLayerYearStats.objects.get(shape_id=shape.id, data_layer=datalayer_str, year=year)
                shape_dlcount_dict[shape.id] += 1
                shape_dl_dict[shape.id].append(datalayer_name)
            except ObjectDoesNotExist:
                shape_missing_dl_dict[shape.id].append(datalayer_name)
                continue


    geometries = {shape.id: shape.geometry.geojson for shape in shapes}
    names = {shape.id: shape.name for shape in shapes}

    context = {
        'shape_dlcount_dict': shape_dlcount_dict,
        'shape_dl_dict': shape_dl_dict,
        'shape_missing_dl_dict': shape_missing_dl_dict,
        'geometries': geometries,
        'names': names,
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
    types = Type.objects.order_by('position')[1:]
    datalayers = Datalayer.objects.all()

    context = {
        'types': types,
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

    for shape in shapes:
        geometries[shape.id] = shape.geometry.geojson
        names[shape.id] = shape.name
        try:
            dl_value = ShapeDataLayerYearStats.objects.get(shape_id=shape.id, data_layer=data_layer_key, year=year).value
            dl_values[shape.id] = dl_value
        except ObjectDoesNotExist:
            continue

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
    data = []

    for year in years:
        try:
            stat = ShapeDataLayerYearStats.objects.get(shape_id=shape_id,
                                                       data_layer=data_layer_key,
                                                       year=year)
            value = stat.value
            data.insert(0, {
                'year': year,
                'value': value
            })
        except ObjectDoesNotExist:
            continue

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


# def get_dl_count_for_year_shapes(request):
#     data_layers = request.GET.get('data_layers', '').split(',')
#     type_id = request.GET.get('type_id')
#     year = int(request.GET['year'])
#
#     shapes = Shape.objects.filter(type_id=type_id)
#     shape_dlcount_dict = {shape.id: 0 for shape in shapes}
#     shape_dl_dict = {shape.id: [] for shape in shapes}
#
#     for datalayer_str in data_layers:
#         datalayer = Datalayer.objects.get(key=datalayer_str)
#         if datalayer:
#             if datalayer.temporal_resolution == LayerTimeResolution.YEAR:
#                 for shape in shapes:
#                     dlv = datalayer.value(
#                         shape=shape,
#                         when=dt.datetime(year, 1, 1),
#                         mode="exact",
#                     )
#                     if dlv and dlv.value is not None and dlv.value > 0:
#                         shape_dlcount_dict[shape.id] += 1
#                         shape_dl_dict[shape.id].append(datalayer.name)
#             else:
#                 for shape in shapes:
#                     start_date = dt.datetime(year, 1, 1)
#                     end_date = dt.datetime(year, 12, 31)
#
#                     df = datalayer.data(
#                         shape=shape,
#                         start_date=start_date,
#                         end_date=end_date,
#                     )
#                     if not df.empty:
#                         shape_dlcount_dict[shape.id] += 1
#                         shape_dl_dict[shape.id].append(datalayer.name)
#
#     geometries = {shape.id: shape.geometry.geojson for shape in shapes}
#     names = {shape.id: shape.name for shape in shapes}
#
#     context = {
#         'shape_dlcount_dict': shape_dlcount_dict,
#         'shape_dl_dict': shape_dl_dict,
#         'geometries': geometries,
#         'names': names,
#     }
#
#     return JsonResponse(context, safe=False)


# def get_dl_value_for_year_shapes(request):
#     data_layer_key = request.GET.get('data_layer_key')
#     year = request.GET.get('year')
#     shape_type = request.GET.get('shape_type')
#
#     data_layer = Datalayer.objects.get(key=data_layer_key)
#     shapes = Shape.objects.filter(type_id=shape_type)
#
#     if not year:
#         year = data_layer.get_available_years[0]
#
#     geometries = {}
#     names = {}
#     dl_values = {}
#
#     if data_layer:
#         for shape in shapes:
#             geometries[shape.id] = shape.geometry.geojson
#             names[shape.id] = shape.name
#             if data_layer.temporal_resolution == LayerTimeResolution.YEAR:
#                 query = f"""
#                             SELECT value
#                             FROM {data_layer_key}
#                             WHERE shape_id = %s AND year = %s
#                         """
#                 with connection.cursor() as c:
#                     c.execute(query, [shape.id, year])
#                     res = c.fetchone()
#             else:
#                 query = f"""
#                             SELECT AVG(value)
#                             FROM {data_layer_key}
#                             WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
#                         """
#                 with connection.cursor() as c:
#                     c.execute(query, [shape.id, year])
#                     res = c.fetchone()
#
#             if res is not None:
#                 value = res[0]
#                 dl_values[shape.id] = value
#
#     context = {
#         'geometries': geometries,
#         'names': names,
#         'dl_values': dl_values
#     }
#
#     return JsonResponse(context, safe=False)
