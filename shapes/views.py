from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse
from django.core.serializers import serialize


from .models import Shape, Type


# Create your views here.



def index(request, type_key):
    t = Type.objects.get(key=type_key)
    return render(request, "shapes/index.html", {
        "type":   t,
        "shapes": t.shapes.all
    })


def detail(request, shape_id):
    shape = get_object_or_404(Shape, pk=shape_id)
    return render(request, "shapes/detail.html", {"shape": shape})

def geojson(request, type_key):
    t = Type.objects.get(key=type_key)
    serialized_data = serialize("geojson", t.shapes.all(), geometry_field="geometry", fields=["name"])
    return HttpResponse(serialized_data, content_type="application/json")
