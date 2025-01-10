from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path('info-map/', views.info_map_base, name='info_map'),
    path('info-map/get-dl-count-for-year-shapes/', views.get_dl_count_for_year_shapes, name='get_dl_count_for_year_shapes'),

    path('temporal-trend/', views.temporal_trend_base, name='temporal_trend'),
    path('temporal-trend/get-shapes-by-shape-id/', views.get_shapes_by_shape_id, name='get_shapes_by_shape_id'),
    path('temporal-trend/get-historical-data-shape/', views.get_historical_data_shape, name='get_historical_data_shape'),

    path('slider/', views.slider_base, name='slider'),
    path('slider/get-datalayer-available-years/', views.get_datalayer_available_years, name='get_datalayer_available_years'),
    path('slider/get-dl-value-for-year-shapes/', views.get_dl_value_for_year_shapes, name='get_dl_value_for_year_shapes'),
    path('slider/get-historical-data-shape/', views.get_historical_data_shape, name='get_historical_data_shape'),
    path('slider/get-historical-data-highest-type/', views.get_historical_data_highest_type, name='get_historical_data_highest_type'),
    path('slider/get-min-max-dl-value/', views.get_min_max_dl_value, name='get_min_max_dl_value'),
]

