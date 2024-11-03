import logging

from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from datalayers.models import Datalayer

from .models import Shape, Type

logger = logging.getLogger(__name__)


# Create your views here.
class ShapeListView(ListView):
    """
    List of shapes, filtered by a shape type.

    Technically this could also be a DetailView based on the type, nevertheless
    the intended View is a list of Shapes, so we went for a ListView that feels
    more fitting.
    """

    model = Shape
    context_object_name = "shapes"

    # TODO: get_object_or_404() hit's the database twice!
    # https://stackoverflow.com/q/73241907
    def get_queryset(self):
        qs = super().get_queryset()

        if "type_key" in self.kwargs:
            t = get_object_or_404(Type, key=self.kwargs["type_key"])
            qs = qs.filter(type=t)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "type_key" in self.kwargs:
            context["type"] = get_object_or_404(Type, key=self.kwargs["type_key"])

        return context


class ShapeDetailView(DetailView):
    model = Shape
    context_object_name = "shape"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_layers = Datalayer.objects.all()
        context["datalayers"] = []
        for dl in all_layers:
            if dl.is_loaded():
                if dl.has_class():
                    context["datalayers"].append(dl)
                else:
                    logger.warning("datalayer class is missing key=%s", dl.key)
        return context


def tree(request):
    root_shapes = Shape.objects.filter(parent__isnull=True)
    return render(
        request,
        "shapes/shape_tree.html",
        {
            "shapes": root_shapes,
        },
    )
