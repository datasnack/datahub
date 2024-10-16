from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
import datetime as dt

from shapes.models import Type, Shape
from datalayers.models import Datalayer


def home(request):
    return render(request, 'home.html')


def temporal_trend_view(request):
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


def load_shapes(request):
    type_id = request.GET.get('type_id')
    if type_id:
        shapes = Shape.objects.filter(type_id=type_id).order_by('name')
    else:
        shapes = Shape.objects.all()
    return JsonResponse(list(shapes.values('id', 'name')), safe=False)


def get_available_years(request):
    data_layer_key = request.GET.get('data_layer_key')
    data_layer = Datalayer.objects.get(key=data_layer_key)
    if data_layer:
        available_years = data_layer.get_available_years
    else:
        available_years = []
    return JsonResponse(available_years, safe=False)

def get_geometry_shape(request):
    shape_id = request.GET.get('shape_id')
    shape = get_object_or_404(Shape, id=shape_id)

    data = {
        "type": "Feature",
        "geometry": shape.geometry.geojson
    }

    return JsonResponse(data, safe=False)

def get_datalayer_for_year(request):
    data_layer_key = request.GET.get('data_layer_key')
    shape_id = request.GET.get('shape_id')
    year = int(request.GET.get('year'))

    data_layer = get_object_or_404(Datalayer, key=data_layer_key)
    shape = get_object_or_404(Shape, id=shape_id)

    value_obj = data_layer.value(shape=shape, when=dt.datetime(year, 1, 1))

    # # Calculate min and max values for the entire data layer across all shapes and years
    # min_value =
    # max_value =

    if value_obj:
        return JsonResponse({
            'value': value_obj.value,
            # 'min_value': min_value,
            # 'max_value': max_value,
        })
    else:
        return JsonResponse({'error': 'No data available'}, status=404)


def get_historical_data(request):
    shape_id = request.GET.get('shape_id')
    data_layer_key = request.GET.get('data_layer_key')

    shape = get_object_or_404(Shape, id=shape_id)
    data_layer = get_object_or_404(Datalayer, key=data_layer_key)

    years = data_layer.get_available_years
    data = []

    for year in years:
        value_obj = data_layer.value(shape=shape, when=dt.datetime(year, 1, 1))
        data.insert(0, {
            'year': year,
            'value': value_obj.value
        })

    return JsonResponse(data, safe=False)


def get_datalayer_name(request):
    data_layer_key = request.GET.get('data_layer_key')
    data_layer = get_object_or_404(Datalayer, key=data_layer_key)

    return JsonResponse(data_layer.name, safe=False)
