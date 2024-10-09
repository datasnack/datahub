from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings

from shapes.models import Type, Shape
from datalayers.models import Datalayer


def home(request):
    return render(request, 'home.html')


def slider_view(request):
    types = Type.objects.all()
    datalayers = Datalayer.objects.all()

    context = {
        'types': types,
        'datalayers': datalayers,
        'datahub_center_x': settings.DATAHUB_CENTER_X,  # Pass center X
        'datahub_center_y': settings.DATAHUB_CENTER_Y,  # Pass center Y
        'datahub_center_zoom': settings.DATAHUB_CENTER_ZOOM  # Pass zoom level
    }
    return render(request, 'slider.html', context)


def load_shapes(request):
    type_id = request.GET.get('type_id')
    if type_id:
        shapes = Shape.objects.filter(type_id=type_id).order_by('name')
    else:
        shapes = Shape.objects.all()
    return JsonResponse(list(shapes.values('id', 'name')), safe=False)

