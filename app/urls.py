from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("robots.txt", views.robots_txt),
    path("", views.home, name="home"),
    path("changelog", views.changelog, name="changelog"),
    path("search", views.search, name="search"),
    path("settings", views.user_settings, name="settings"),
    path(
        "settings/create_token",
        views.user_settings_create_token,
        name="settings_create_token",
    ),
    path(
        "settings/delete_token",
        views.user_settings_delete_token,
        name="settings_delete_token",
    ),
    path("tools/picker", views.tools_picker, name="tools_picker"),
]
