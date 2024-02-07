
from django.urls import path

from . import views

app_name = "shapes"
urlpatterns = [
    path("<int:shape_id>/", views.detail, name="detail"),
    path("<str:type_key>/", views.index, name="index"),
    path("geojson/<str:type_key>/", views.geojson, name="geojson"),
]
