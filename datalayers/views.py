# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from taggit.models import Tag

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView

from .models import Category, Datalayer, DatalayerLogEntry


# Create your views here.
class DatalayerListView(ListView):
    model = Datalayer
    context_object_name = "datalayers"

    # TODO: get_object_or_404() hit's the database twice!
    # https://stackoverflow.com/q/73241907
    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .visible_to(self.request.user)
            .select_related("category")
            .prefetch_related("tags")
        )

        if "category_id" in self.kwargs:
            c = get_object_or_404(Category, pk=self.kwargs["category_id"])
            qs = qs.filter(category=c)

        if "tag_slug" in self.kwargs:
            qs = qs.filter(tags__slug__in=[self.kwargs["tag_slug"]])

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["full"] = False
        if "full" in self.request.GET and self.request.GET["full"] == "1":
            context["full"] = True

        context["columns"] = [
            "operation",
            "format",
            "spatial_details",
            "spatial_coverage",
            "temporal_details",
            "temporal_coverage",
            "source",
            "language",
            "license",
        ]

        context["title"] = _("Data Layers")
        if "category_id" in self.kwargs:
            c = get_object_or_404(Category, pk=self.kwargs["category_id"])
            context["title"] = c.name

        if "tag_slug" in self.kwargs:
            t = get_object_or_404(Tag, slug=self.kwargs["tag_slug"])
            context["title"] = f"#{t.name}"

        return context


class DatalayerDetailView(DetailView):
    model = Datalayer
    slug_field = "key"
    slug_url_kwarg = "key"
    context_object_name = "datalayer"

    def get_queryset(self):
        return super().get_queryset().visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related"] = self.object.visible_related(self.request.user)
        return context


class DatalayerLogView(PermissionRequiredMixin, ListView):
    model = DatalayerLogEntry
    template_name = "datalayers/datalayer_log.html"
    context_object_name = "logentries"
    paginate_by = 100
    permission_required = "datalayers.view_datalayerlogentry"

    def get_datalayer(self) -> Datalayer:
        if not hasattr(self, "_datalayer"):
            self._datalayer = get_object_or_404(
                Datalayer.objects.visible_to(self.request.user),
                key=self.kwargs["key"],
            )
        return self._datalayer

    def get_queryset(self):
        key = self.kwargs.get("key")
        return DatalayerLogEntry.objects.filter(
            datalayer=self.get_datalayer()
        ).order_by("-datetime")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["datalayer"] = self.get_datalayer()
        return context


class DatalayerDataCiteView(DetailView):
    model = Datalayer
    context_object_name = "datalayer"
    slug_field = "key"
    slug_url_kwarg = "key"
    template_name = "datalayers/datalayer_datacite.html"
