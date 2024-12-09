import json

from django import forms
from django.contrib import admin, messages
from django.core import serializers
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import path

from app.utils import datahub_key

from .models import Category, Datalayer, DatalayerSource
from .utils import dumpdata, loaddata

# Register your models here.
admin.site.register(Category)
admin.site.register(DatalayerSource)


@admin.action(permissions=["view"], description="Export selected Data Layers")
def action_dumpdata(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    response["Content-Disposition"] = (
        f'attachment; filename="{datahub_key("datalayers.json")}"'
    )
    response.write(dumpdata(list(queryset)))
    return response


class DatalayerSourceAdminInline(admin.TabularInline):
    model = DatalayerSource
    classes = ["collapse"]


class DatalayerAdmin(admin.ModelAdmin):
    actions = [action_dumpdata]

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

    def get_urls(self):
        """Add custom 'import' URL to the admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "loaddata/",
                self.admin_site.admin_view(self.import_view),
                name="datalayers_datalayer_loaddata",
            ),
        ]
        return custom_urls + urls

    def import_view(self, request):
        if not self.has_add_permission(request):  # Check add permission for this model
            return HttpResponseForbidden(
                "You do not have permission to import data for this model."
            )

        """View logic for the Import page"""
        if request.method == "POST":
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                # Handle file import logic here
                file = form.cleaned_data["file"]
                # Process the uploaded file here (e.g., read CSV, validate, etc.)
                self.loadddata(file.read().decode(), request)

                return redirect("admin:datalayers_datalayer_changelist")
        else:
            form = ImportForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title="Import Data Layers",
        )
        return render(request, "admin/datalayers/datalayer/loaddata.html", context)

    def loadddata(self, data, request):
        msgs = loaddata(data)
        for msg in msgs:
            messages.add_message(request, msg["level"], msg["message"])


class ImportForm(forms.Form):
    """Custom form for the Import page"""

    file = forms.FileField(label="Upload File")


admin.site.register(Datalayer, DatalayerAdmin)
