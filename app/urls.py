from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("", views.home, name="home"),
    path("search", views.search, name="search"),
    path("tools/picker", views.tools_picker, name="tools_picker"),
]
