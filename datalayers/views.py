from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Datalayer

# Create your views here.
def index(request):
    datalayers = Datalayer.objects.order_by("name")
    return render(request, "datalayers/index.html", {"datalayer": datalayers})


def detail(request, datalayer_id):
    datalayer = get_object_or_404(Datalayer, pk=datalayer_id)
    return render(request, "datalayers/detail.html", {"datalayer": datalayer})