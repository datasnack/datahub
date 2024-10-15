from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('temporal-trend/', views.temporal_trend_view, name='temporal_trend_view'),
    path('temporal-trend/load-shapes/', views.load_shapes, name='load_shapes'),
    path('temporal-trend/get-available-years/', views.get_available_years, name='get_available_years'),
    path('temporal-trend/get-geometry-shape/', views.get_geometry_shape, name='get_geometry_shape'),
    path('temporal-trend/get-datalayer-for-year/', views.get_datalayer_for_year, name='get_datalayer_for_year'),
    path('temporal-trend/get-historical-data/', views.get_historical_data, name='get_historical_data'),
    path('temporal-trend/get-datalayer-name/', views.get_datalayer_name, name='get_datalayer_name'),
]
