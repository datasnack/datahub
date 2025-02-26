from django.urls import path

from . import views
from . import views_datacite

urlpatterns = [
    path("datalayers/data/", views.data, name="datalayer_data"),
    path("datalayers/datalayer/", views.datalayer, name="datalayer_datalayer"),
    path("datalayers/vector/", views.vector, name="datalayer_vector"),
    path("datalayers/plotly/", views.plotly, name="datalayer_plotly"),
    path("datalayers/meta/", views.meta, name="datalayer_meta"),
    path("datalayers/datacite/", views_datacite.datacite, name="datalayers_datacite"),
]
