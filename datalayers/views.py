from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView


from .models import Datalayer, Category

# Create your views here.
class DatalayerListView(ListView):
    model = Datalayer
    context_object_name = "datalayers"

    # todo: get_object_or_404() hit's the database twice!
    # https://stackoverflow.com/q/73241907
    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('category')

        if 'category_id' in self.kwargs:
            c = get_object_or_404(Category, pk=self.kwargs['category_id'])
            qs = qs.filter(category=c)

        if 'tag_slug' in self.kwargs:
            qs = qs.filter(tags__slug__in=[self.kwargs['tag_slug']])

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context



class DatalayerDetailView(DetailView):
    model = Datalayer
    slug_field = 'key'
    slug_url_kwarg = 'key'
    context_object_name = "datalayer"


class DatalayerLogView(DetailView):
    model = Datalayer
    slug_field = 'key'
    slug_url_kwarg = 'key'
    context_object_name = "datalayer"
    template_name = "datalayers/datalayer_log.html"

class DatalayerDataCiteView(DetailView):
    model = Datalayer
    context_object_name = "datalayer"
    slug_field = 'key'
    slug_url_kwarg = 'key'
    template_name = "datalayers/datalayer_datacite.html"
