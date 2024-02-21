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
        qs = super().get_queryset()

        if 'category_id' in self.kwargs:
            c = get_object_or_404(Category, pk=self.kwargs['category_id'])
            qs = qs.filter(category=c)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context



class DatalayerDetailView(DetailView):
    model = Datalayer
    context_object_name = "datalayer"
