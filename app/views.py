import json

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q


# Create your views here.
from shapes.models import Shape, Type
from datalayers.models import Datalayer
from shapes.models import Shape

def home(request):
    return render(request, "app/home.html", {
        'shapes_count':     Shape.objects.count(),
        'shape_types':      Type.objects.all(),
        'datalayers_count': Datalayer.objects.count(),
    })


def search(request):
    """ Simple LIKE search for data layers and shapes. Returns result in
    format for agolia/autocomplete-js. """

    search_term = request.GET.get('q', '')

    shapes = Shape.objects.filter(name__icontains=search_term)
    datalayers = Datalayer.objects.filter(
        Q(name__icontains=search_term) | Q(key__icontains=search_term)
    )

    results = []

    for s in shapes:
        results.append({
            "url": s.get_absolute_url(),
            "label": f"{s.name} ({s.type.name})",
        })

    for d in datalayers:
        results.append({
            "url": d.get_absolute_url(),
            "label": f"{d.name} ({d.key})",
            "objectID": d.id,
        })

    return JsonResponse({"results": [results]})
