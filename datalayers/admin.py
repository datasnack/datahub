from django.contrib import admin

from .models import Category, Datalayer, DatalayerSource

# Register your models here.
admin.site.register(Category)


admin.site.register(DatalayerSource)


class DatalayerSourceAdminInline(admin.TabularInline):
    model = DatalayerSource
    classes = ["collapse"]


class DatalayerAdmin(admin.ModelAdmin):
    list_display = ["name", "key"]
    list_display = ["name", "key", "has_class", "is_loaded"]

    def has_class(self, obj):
        return obj.has_class()

    has_class.short_description = "Class"
    has_class.boolean = True

    def is_loaded(self, obj):
        return obj.is_loaded()

    is_loaded.short_description = "Loaded"
    is_loaded.boolean = True

    inlines = (DatalayerSourceAdminInline,)

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "key",
                    "category",
                    "tags",
                    "description",
                    "operation",
                    "database_unit",
                    "date_included",
                    "related_to",
                ],
            },
        ),
        (
            "Original data metadata",
            {
                "classes": ["collapse"],
                "fields": [
                    "format",
                    "format_description",
                    "format_unit",
                    "spatial_details",
                    "spatial_coverage",
                    "temporal_details",
                    "temporal_coverage",
                    "source",
                    "source_link",
                    "language",
                    "license",
                    "date_published",
                    "date_last_accessed",
                    "citation",
                ],
            },
        ),
    ]

    # todo: make field read-only. only allow editing this for "super" admins?
    # def get_readonly_fields(self, request, obj=None):
    #    if obj: # obj is not None, so this is an edit
    #        return ['key',] # Return a list or tuple of readonly fields' names
    #    else: # This is an addition
    #        return []


admin.site.register(Datalayer, DatalayerAdmin)
