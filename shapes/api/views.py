from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.core.serializers import serialize


from shapes.models import Shape, Type


# Create your views here.

def shape_geojson(request):

    shape_id = request.GET.get('shape_id', None)
    if shape_id:
        serialized_data = serialize("geojson", [Shape.objects.get(pk=shape_id)],
                                    geometry_field="geometry",
                                    fields=[
                                        "name",
                                        "type.name"
                                    ])
        return HttpResponse(serialized_data, content_type="application/json")

    shape_type = request.GET.get('shape_type', None)
    if shape_type:
        t = Type.objects.get(key=shape_type)
        serialized_data = serialize("geojson", t.shapes.all(), geometry_field="geometry", fields=["name"])
        return HttpResponse(serialized_data, content_type="application/json")

    return HttpResponseNotFound("Not found")
