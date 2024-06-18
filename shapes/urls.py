from django.urls import path

from . import views

app_name = "shapes"
urlpatterns = [
    path("", views.ShapeListView.as_view(), name="shape_detail_all"),
    path("<int:pk>/", views.ShapeDetailView.as_view(), name="shape_detail"),
    path("tools/tree/", views.tree, name="shape_tree"),
    path("<str:type_key>/", views.ShapeListView.as_view(), name="shape_index"),
]
