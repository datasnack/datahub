from django.urls import path, include

from . import views

urlpatterns = [
    path("shapes/geometry/", views.shape_geometry, name="shape_geometry"),
    path("shapes/bbox/", views.shape_bbox, name="shape_bbox"),
]
