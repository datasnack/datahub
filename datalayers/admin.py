# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import ClassVar

from django import forms
from django.contrib import admin, messages
from django.core import serializers
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path

from app.utils import datahub_key
from app.widgets import (
    FormatWidget,
    LanguageWidget,
    LicenseWidget,
    SpatialCoverageWidget,
    TemporalResolutionWidget,
)

from .forms import SourceMetadataSelectionForm, SourceMetadataSelectionFromForm
from .models import Category, Datalayer, SourceMetadata
from .utils import dumpdata, loaddata

# Register your models here.
admin.site.register(Category)


@admin.action(permissions=["view"], description="Export selected Data Layers")
def action_dumpdata(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    response["Content-Disposition"] = (
        f'attachment; filename="{datahub_key("datalayers.json")}"'
    )
    response.write(dumpdata(list(queryset)))
    return response


@admin.action(permissions=["add"], description="Copy Metadata sources")
def action_copy_sources(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    response["Content-Disposition"] = (
        f'attachment; filename="{datahub_key("datalayers.json")}"'
    )
    response.write(dumpdata(list(queryset)))
    return response


class SourceMetadataForm(forms.ModelForm):
    class Meta:
        model = SourceMetadata
        fields = "__all__"  # noqa: DJ007, its the admin form so we want all fields?
        widgets = {
            "name": forms.TextInput(attrs={"class": "vLargeTextField"}),
            "license": LicenseWidget(),
            "format": FormatWidget(),
            "temporal_resolution": TemporalResolutionWidget(),
            "language": LanguageWidget(),
            "spatial_coverage": SpatialCoverageWidget(),
            "source": forms.TextInput(attrs={"class": "vLargeTextField"}),
            "source_link": forms.TextInput(attrs={"class": "vLargeTextField"}),
        }

    class Media:
        js = ("app/js/admin/pidfetch.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["citation_plain"].widget.attrs.update(
            {
                "rows": 3,
            }
        )
        self.fields["citation_bibtex"].widget.attrs.update(
            {
                "rows": 3,
            }
        )

        self.fields["pid"].widget.attrs.update(
            {
                "class": "js-pidfetch",
            }
        )


class SourceMetadataAdmin(admin.ModelAdmin):
    list_display = ["name", "datalayer"]

    form = SourceMetadataForm


admin.site.register(SourceMetadata, SourceMetadataAdmin)


class SourceMetadataAdminInline(admin.StackedInline):
    model = SourceMetadata
    form = SourceMetadataForm
    extra = 0  # don't add any empty forms
    classes = ["collapse"]


class DatalayerAdmin(admin.ModelAdmin):
    actions = [
        action_dumpdata,
        "copy_source_metadata_action",
        "copy_source_metadata_from_action",
    ]

    list_display = ["name", "key", "has_class", "is_loaded"]

    def has_class(self, obj):
        return obj.has_class()

    has_class.short_description = "Class"
    has_class.boolean = True

    def is_loaded(self, obj):
        return obj.is_loaded()

    is_loaded.short_description = "Loaded"
    is_loaded.boolean = True

    inlines = (SourceMetadataAdminInline,)

    fieldsets: ClassVar = [
        (
            None,
            {
                "fields": [
                    "name",
                    "key",
                    "data_type",
                    "category",
                    "tags",
                    "description",
                    "caveats",
                    "operation",
                    "database_unit",
                    "date_included",
                    "related_to",
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
        """Add custom 'import' URL to the admin."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "loaddata/",
                self.admin_site.admin_view(self.import_view),
                name="datalayers_datalayer_loaddata",
            ),
            path(
                "copy-source-metadata/<int:datalayer_id>/",
                self.admin_site.admin_view(self.copy_source_metadata_view),
                name="copy-source-metadata",
            ),
            path(
                "copy-source-metadata-from/",
                self.admin_site.admin_view(self.copy_source_metadata_from_view),
                name="copy-source-metadata-from",
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

    def copy_source_metadata_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request, "Please select exactly one Datalayer.", level="error"
            )
            return redirect("..")

        datalayer = queryset.first()
        return redirect(f"copy-source-metadata/{datalayer.pk}/")

    copy_source_metadata_action.short_description = (
        "Copy SourceMetadata to another Datalayer"
    )

    def copy_source_metadata_from_action(self, request, queryset):
        selected = request.POST.getlist("_selected_action")
        return redirect(f"copy-source-metadata-from/?ids={','.join(selected)}")

    copy_source_metadata_from_action.short_description = (
        "Copy SourceMetadata from a Datalayer to the selected"
    )

    def copy_source_metadata_view(self, request, datalayer_id):
        if not self.has_add_permission(request):  # Check add permission for this model
            return HttpResponseForbidden(
                "You do not have permission to copy sources for this model."
            )

        datalayer = get_object_or_404(Datalayer, pk=datalayer_id)

        if request.method == "POST":
            form = SourceMetadataSelectionForm(request.POST)
            if form.is_valid():
                selected_metadata = form.cleaned_data["source_metadata"]
                new_datalayer = form.cleaned_data["new_datalayer"]
                delete_existing = form.cleaned_data["delete_existing"]
                append_copy_to_new_name = form.cleaned_data["append_copy_to_new_name"]

                if delete_existing:
                    SourceMetadata.objects.filter(datalayer=new_datalayer).delete()

                for metadata in selected_metadata:
                    metadata.pk = None  # Duplicate object

                    if append_copy_to_new_name:
                        metadata.name = f"{metadata.name} (COPY)"

                    metadata.position = 0  # copied entries will be ordered at the end
                    metadata.datalayer = new_datalayer
                    metadata.save()

                self.message_user(
                    request,
                    f"Copied {len(selected_metadata)} SourceMetadata to {new_datalayer}",
                )
                return redirect("admin:datalayers_datalayer_changelist")

        else:
            form = SourceMetadataSelectionForm(
                datalayer=datalayer,
                initial={"source_metadata": datalayer.sources.all()},
            )

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,  # Ensures admin breadcrumbs and styles
            app_label=self.model._meta.app_label,
            form=form,
            datalayer=datalayer,
            title=f"Copy SourceMetadata from {datalayer.name}",
        )

        return render(
            request, "admin/datalayers/datalayer/select_source_metadata.html", context
        )

    def copy_source_metadata_from_view(self, request):
        if not self.has_add_permission(request):  # Check add permission for this model
            return HttpResponseForbidden(
                "You do not have permission to copy sources for this model."
            )

        if "ids" not in request.GET:
            self.message_user(request, "No items selected!", level=messages.WARNING)
            return redirect("admin:datalayers_datalayer_changelist")

        ids = request.GET["ids"].split(",")

        if request.method == "POST":
            form = SourceMetadataSelectionFromForm(request.POST)
            if form.is_valid():
                source_datalayer = form.cleaned_data["source_datalayer"]
                target_datalayers = form.cleaned_data["target_datalayers"]

                delete_existing = form.cleaned_data["delete_existing"]
                append_copy_to_new_name = form.cleaned_data["append_copy_to_new_name"]

                for target_datalayer in target_datalayers:
                    if delete_existing:
                        SourceMetadata.objects.filter(
                            datalayer=target_datalayer
                        ).delete()

                    for metadata in source_datalayer.sources.all():
                        metadata.pk = None  # Duplicate object

                        if append_copy_to_new_name:
                            metadata.name = f"{metadata.name} (COPY)"

                        metadata.position = (
                            0  # copied entries will be ordered at the end
                        )
                        metadata.datalayer = target_datalayer
                        metadata.save()

                    self.message_user(
                        request,
                        f"Copied SourceMetadata from {source_datalayer} to {target_datalayer}",
                    )

                return redirect("admin:datalayers_datalayer_changelist")

        else:
            form = SourceMetadataSelectionFromForm(
                ids=ids,
            )

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,  # Ensures admin breadcrumbs and styles
            app_label=self.model._meta.app_label,
            form=form,
            title="Select Data Layer to copy SourceMetaData from",
        )

        return render(
            request,
            "admin/datalayers/datalayer/select_source_metadata_from.html",
            context,
        )


class ImportForm(forms.Form):
    """Custom form for the Import page."""

    file = forms.FileField(label="Upload File")


admin.site.register(Datalayer, DatalayerAdmin)
