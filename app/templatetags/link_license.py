import json
from pathlib import Path

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

SPDX = {}
with Path.open("app/resources/spdx/licenses.json") as f:
    spdx_json = json.load(f)

    for license_info in spdx_json["licenses"]:
        SPDX[license_info["licenseId"].lower()] = license_info


@register.filter
def link_license(license_id):
    """Filter to link known SPDX license ids to their source."""
    if license_id is None:
        return ""

    license_key = license_id.lower()
    if license_key in SPDX:
        license_info = SPDX[license_key]

        # in case of ONLY ONE further info link, we link the licenseId to this
        if len(license_info["seeAlso"]) == 1:
            return mark_safe(  # noqa: S308
                f'<a title="{escape(license_info["name"])}" href="{escape(license_info["seeAlso"][0])}">{escape(license_id)}</a>'
            )

    # license id not found, just return the given license information
    return license_id
