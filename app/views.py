from django.contrib.gis.geos import Point
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from datalayers.models import Datalayer
from shapes.models import Shape, Type


def home(request):
    return render(
        request,
        "app/home.html",
        {
            "shapes_count": Shape.objects.count(),
            "shape_types": Type.objects.all(),
            "datalayers_count": Datalayer.objects.count(),
        },
    )


def search(request):
    """
    Perform LIKE search for Data Layers and shapes.

    Returns result in format for agolia/autocomplete-js.
    """
    search_term = request.GET.get("q", "")

    search_filter = request.GET.get("f", "shapes,datalayers").split(",")

    results = []

    if "shapes" in search_filter:
        shapes = Shape.objects.filter(name__icontains=search_term)

        for s in shapes:
            results.append(
                {
                    "url": s.get_absolute_url(),
                    "label": f"{s.name} ({s.type.name})",
                    "objectID": s.id,
                }
            )

    if "datalayers" in search_filter:
        datalayers = Datalayer.objects.filter(
            Q(name__icontains=search_term)
            | Q(key__icontains=search_term)
            | Q(category__name__icontains=search_term)
            | Q(tags__name__icontains=search_term)
        ).distinct("id")

        for d in datalayers:
            results.append(
                {
                    "url": d.get_absolute_url(),
                    "label": f"{d.name} ({d.key})",
                    "objectID": d.id,
                }
            )

    return JsonResponse({"results": [results]})


def tools_picker(request):
    """View for a location picker that selects all available shapes on the location."""
    context = {
        "shapes": None,
        "datalayers": None,
        "point": None,
        "warning": None,
    }

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if lat is not None and lng is not None:
        point = Point(float(lng), float(lat))
        shapes = Shape.objects.filter(geometry__contains=point).order_by(
            "type__position"
        )

        if not shapes:
            context["warning"] = _(
                "The provided location did not intersect with any Shapes."
            )
        else:
            context["shapes"] = shapes
            context["point"] = point

            all_layers = Datalayer.objects.all()
            context["datalayers"] = []
            for layer in all_layers:
                if layer.is_loaded():
                    context["datalayers"].append(layer)

    return render(request, "tools/picker.html", context)
