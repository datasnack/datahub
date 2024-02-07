from django.contrib import admin

from .models import Shape, Type

# Register your models here.


class ShapeAdmin(admin.ModelAdmin):
    readonly_fields=('area_sqm',)

admin.site.register(Shape, ShapeAdmin)


class TypeAdmin(admin.ModelAdmin):
    ordering=['position']
    list_display = ["name","show_in_nav","position"]

admin.site.register(Type, TypeAdmin)
