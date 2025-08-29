from django.urls import path

from . import views

app_name = "shapes"
urlpatterns = [
    path("", views.ShapeListView.as_view(), name="shape_detail_all"),
    path("<slug:key>/", views.ShapeDetailView.as_view(), name="shape_detail"),
    path("tools/tree/", views.tree, name="shape_tree"),
    path("type/<str:type_key>/", views.ShapeListView.as_view(), name="shape_index"),
]
