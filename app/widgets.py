# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
from pathlib import Path

from django import forms


class DatalistTextInput(forms.TextInput):
    template_name = "app/forms/widgets/text_with_datalist.html"

    def __init__(
        self,
        datalist_options: list[dict[str, str]] | dict[str, str] | list[str],
        attrs=None,
    ) -> None:
        super().__init__(attrs)

        options = []

        # Firefox datalist search is complicated, we need to set key AND value in the
        # label for the search to catch it.
        if isinstance(datalist_options, list) and isinstance(datalist_options[0], dict):
            options = datalist_options  # already in correct format
        elif isinstance(datalist_options, list):
            for key in datalist_options:
                options.append({"value": key, "label": key})
        else:
            for key, label in datalist_options.items():
                options.append(
                    {
                        "value": key,
                        "label": f"{key}: {label}",
                    }
                )

        self.datalist_options = options

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_options"] = self.datalist_options
        # firefox clips datalist dropdown width to input field, we use the largest
        # text input class, to give the potential labels enough space to be readable.
        context["widget"]["attrs"]["class"] = "vLargeTextField"
        context["widget"]["attrs"]["list"] = (
            f"{context['widget']['attrs']['id']}_datalist"
        )

        return context


class LicenseWidget(DatalistTextInput):
    def __init__(self, attrs=None) -> None:
        license_options = {}

        with Path("app/resources/spdx/licenses.json").open() as fp:
            spdx = json.load(fp)

            for el in spdx["licenses"]:
                license_options[el["licenseId"]] = el["name"]

        super().__init__(license_options, attrs)


class FormatWidget(DatalistTextInput):
    def __init__(self, attrs=None) -> None:
        # see: https://www.iana.org/assignments/media-types/media-types.xhtml
        format_options_kv = {
            "application/json": "JSON",
            "application/geo+json": "GeoJSON",
            "application/vnd.shp": "Shapefile",
            "application/geopackage+sqlite3": "GeoPackage",
            "image/tiff": "GeoTIFF",  # we could add `; application=geotiff` but I don't think it would add much benefit?
            "application/pdf": "PDF",
            "text/csv": "CSV",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "MS Excel (.xlsx)",
        }
        options = []
        for key, label in format_options_kv.items():
            options.append(
                {
                    "value": key,
                    "label": f"{label} ({key})",
                }
            )

        super().__init__(options, attrs)


class TemporalResolutionWidget(DatalistTextInput):
    def __init__(self, attrs=None) -> None:
        # Derived from ISO 19115
        format_options_kv = {
            "daily": "Daily",
            "weekly": "Weekly",
            "monthly": "Monthly",
            "annually": "Annually",
            "irregular": "Irregular / cross sectional",
        }

        super().__init__(format_options_kv, attrs)


class SpatialCoverageWidget(DatalistTextInput):
    def __init__(self, attrs=None) -> None:
        # Derived from ISO 19115, custom codes
        format_options_kv = {
            "global": "Global",
        }

        # Append country codes
        with Path("app/resources/iso3166/iso-3166-1-alpha3.json").open() as fp:
            iso6311a3 = json.load(fp)

            for el in iso6311a3:
                format_options_kv[el["alpha3"]] = el["name"]

        super().__init__(format_options_kv, attrs)


class LanguageWidget(DatalistTextInput):
    def __init__(self, attrs=None) -> None:
        # Derived from ISO 19115, custom codes
        format_options_kv = {
            "global": "Global",
        }

        # Append country codes
        with Path("app/resources/iso639/iso-639-3.json").open() as fp:
            iso639a2 = json.load(fp)

            for el in iso639a2:
                format_options_kv[el["Id"]] = el["Ref_Name"]

        super().__init__(format_options_kv, attrs)
