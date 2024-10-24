from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path('info-map/', views.info_map_base, name='info_map'),
    path('info-map/get-dl-count-for-year-shape/', views.get_dl_count_for_year_shape, name='get_dl_count_for_year_shape'),
    path('info-map/get-shape-type-geometries/', views.get_shape_type_geometries, name='get_shape_type_geometries'),

    path('temporal-trend/', views.temporal_trend_base, name='temporal_trend'),
    path('temporal-trend/get-shapes-by-shape-id/', views.get_shapes_by_shape_id, name='get_shapes_by_shape_id'),
    path('temporal-trend/get-historical-data/', views.get_historical_data, name='get_historical_data'),

    path('slider/', views.slider_base, name='slider'),
    path('slider/load-shapes/', views.get_shapes_by_shape_id, name='get_shapes_by_shape_id'),
    path('slider/get-datalayer-available-years/', views.get_datalayer_available_years, name='get_datalayer_available_years'),
]

