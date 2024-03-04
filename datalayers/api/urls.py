
from django.urls import path, include

from . import views




urlpatterns = [
    path("datalayers/data/", views.data, name="datalayer_data"),


    path("datalayers/plotly/", views.plotly, name="datalayer_plotly"),
]
