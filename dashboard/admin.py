from django.contrib import admin

from dashboard.models import ShapeDataLayerYearStats


# Register your models here.
class ShapeDataLayerYearStatsAdmin(admin.ModelAdmin):
    list_display = ('shape_id', 'data_layer', 'year', 'value')
    list_filter = ('shape_id', 'data_layer', 'year')

admin.site.register(ShapeDataLayerYearStats, ShapeDataLayerYearStatsAdmin)
