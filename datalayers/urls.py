
from django.urls import path

from datalayers.views import DatalayerListView, DatalayerDetailView
from . import views

app_name = "datalayers"
urlpatterns = [
    #path("", views.index, name="index"),

    path("", DatalayerListView.as_view(), name="datalayer_index"),
    path("<int:pk>/", DatalayerDetailView.as_view(), name="datalayer_detail"),

    path("category/<int:category_id>", DatalayerListView.as_view(), name="datalayer_index_category"),


]
