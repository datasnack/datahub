import json
from pathlib import Path

from django import forms
from django.utils.translation import gettext_lazy as _


class DatalistTextInput(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def __init__(self, attrs=None, datalist_options=None):
        super().__init__(attrs)
        self.datalist_options = datalist_options or []

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["datalist_options"] = self.datalist_options
        return context


class LicenseWidget(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def get_context(self, name, value, attrs):
        license_options = []

        with open("app/resources/spdx/licenses.json") as f:
            spdx = json.load(f)

            for l in spdx["licenses"]:
                license_options.append(
                    {
                        "value": l["licenseId"],
                        "label": f"{l['name']} ({l['licenseId']})",  # append id to label b/c Firefox does not search/show the value if label is given
                    }
                )

        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = license_options
        context["widget"]["attrs"]["class"] = "vTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context


class FormatWidget(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def get_context(self, name, value, attrs):
        # see: https://www.iana.org/assignments/media-types/media-types.xhtml
        format_options_kv = {
            "application/json": "JSON",
            "application/geo+json": "GeoJSON",
            "application/vnd.shp": "Shapefile",
            "application/geopackage+sqlite3": "GeoPackage",
            "image/tiff": "GeoTIFF",  # we could add `; application=geotiff` but I don't think it would add much benefit?
            "application/pdf": "PDF",
            "text/csv": "CSV",
        }
        format_options = []
        for mime, mime_name in format_options_kv.items():
            format_options.append(
                {
                    "value": mime,
                    "label": f"{mime_name} ({mime})",  # append id to label b/c Firefox does not search/show the value if label is given
                }
            )

        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = format_options
        context["widget"]["attrs"]["class"] = "vTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context


class TemporalResolutionWidget(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def get_context(self, name, value, attrs):
        # Derived from ISO 19115
        format_options_kv = {
            "daily": "Daily",
            "weekly": "Weekly",
            "monthly": "Monthly",
            "annually": "Annually",
            "irregular": "Irregular / cross sectional",
        }
        format_options = []
        for mime, mime_name in format_options_kv.items():
            format_options.append(
                {
                    "value": mime,
                    "label": f"{mime_name} ({mime})",  # append id to label b/c Firefox does not search/show the value if label is given
                }
            )

        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = format_options
        context["widget"]["attrs"]["class"] = "vTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context


class SpatialCoverageWidget(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def get_context(self, name, value, attrs):
        # Derived from ISO 19115
        format_options_kv = {
            "global": "Global",
        }
        format_options = []

        # Append custom codes
        for key, val in format_options_kv.items():
            format_options.append(
                {
                    "value": key,
                    "label": f"{val} ({key})",  # append id to label b/c Firefox does not search/show the value if label is given
                }
            )

        # Append country codes
        with Path.open("app/resources/iso3166/iso-3166-1-alpha3.json") as fp:
            iso6311a4 = json.load(fp)

            for el in iso6311a4:
                format_options.append(
                    {
                        "value": el["alpha3"],
                        "label": f"{el['name']} ({el['alpha3']})",  # append id to label b/c Firefox does not search/show the value if label is given
                    }
                )

        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = format_options
        context["widget"]["attrs"]["class"] = "vTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context


class LanguageWidget(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def get_context(self, name, value, attrs):
        format_options = []

        with Path.open("app/resources/iso639/iso-639-3.json") as fp:
            iso639a2 = json.load(fp)

            for el in iso639a2:
                format_options.append(
                    {
                        "value": el["Id"],
                        "label": f"{el['Ref_Name']} ({el['Id']})",  # append id to label b/c Firefox does not search/show the value if label is given
                    }
                )

        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = format_options
        context["widget"]["attrs"]["class"] = "vTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context
