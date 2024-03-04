
from django.urls import path

from . import views

app_name = "datalayers"
urlpatterns = [
    #path("", views.index, name="index"),

    path("", views.DatalayerListView.as_view(), name="datalayer_index"),
    path("<int:pk>/", views.DatalayerDetailView.as_view(), name="datalayer_detail"),
    path("<int:pk>/log", views.DatalayerLogView.as_view(), name="datalayer_log"),
    path("<int:pk>/datacite", views.DatalayerDataCiteView.as_view(), name="datalayer_datacite"),


    path("category/<int:category_id>", views.DatalayerListView.as_view(), name="datalayer_index_category"),
]
