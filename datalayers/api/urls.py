from django.urls import path

from . import views

urlpatterns = [
    path("datalayers/data/", views.data, name="datalayer_data"),
    path("datalayers/datalayer/", views.datalayer, name="datalayer_datalayer"),
    path("datalayers/vector/", views.vector, name="datalayer_vector"),
    path("datalayers/plotly/", views.plotly, name="datalayer_plotly"),
    path("datalayers/meta/", views.meta, name="datalayer_meta"),
]
