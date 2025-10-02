# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView

from app.utils import prase_date_or_today
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

        qs = qs.select_related("type")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = _("Shapes")
        context["show_map"] = False
        context["show_type"] = True

        if "type_key" in self.kwargs:
            context["type"] = get_object_or_404(Type, key=self.kwargs["type_key"])
            context["title"] = context["type"].name
            context["show_map"] = True
            context["show_type"] = False

        return context


class ShapeDetailView(DetailView):
    model = Shape
    slug_field = "key"
    slug_url_kwarg = "key"
    context_object_name = "shape"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["temporal"] = prase_date_or_today(self.request.GET.get("temporal"))

        all_layers = Datalayer.objects.all()
        context["datalayers"] = []
        for dl in all_layers:
            if dl.is_available():
                context["datalayers"].append(dl)

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
