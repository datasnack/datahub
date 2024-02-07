from django.shortcuts import render

# Create your views here.
from shapes.models import Shape, Type
from datalayers.models import Datalayer

def home(request):
    return render(request, "app/home.html", {
        'shapes_count':     Shape.objects.count(),
        'shape_types':      Type.objects.all(),
        'datalayers_count': Datalayer.objects.count(),
    })
