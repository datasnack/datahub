
from django.urls import path

from . import views

app_name = "datalayers"
urlpatterns = [
    path("", views.index, name="index"),
    path("<int:datalayer_id>/", views.detail, name="detail"),
]