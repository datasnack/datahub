from django.contrib import admin

from .models import Category, Datalayer

# Register your models here.
admin.site.register(Category)




class DatalayerAdmin(admin.ModelAdmin):
    list_display = ["name","key"]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "key",
                    "category",
                    'tags',
                    "description",
                ],
            },
        ),
        (
            "Data type and processing",
            {
                "fields": [
                    "necessity",
                    "format",
                    "original_unit",
                    "operation",
                    "database_unit",
                    "details_spatial",
                    "details_temporal",
                    "timeframe",
                    "related_sources"
                ],
            },
        ),
        (
            "Metadata",
            {
                "classes": ["collapse"],
                "fields": [
                    "creator",
                    "included_date",
                    "type",
                    "identifier",
                    "source",
                    "source_link",
                    "citation",
                    "language",
                    "license",
                    "coverage"
                ],
            },
        ),
    ]

    # todo: make field read-only. only allow editing this for "super" admins?
    #def get_readonly_fields(self, request, obj=None):
    #    if obj: # obj is not None, so this is an edit
    #        return ['key',] # Return a list or tuple of readonly fields' names
    #    else: # This is an addition
    #        return []

admin.site.register(Datalayer, DatalayerAdmin)
