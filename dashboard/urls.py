from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('slider/', views.slider_view, name='slider_view'),
    path('slider/load-shapes/', views.load_shapes, name='load_shapes'),
]
