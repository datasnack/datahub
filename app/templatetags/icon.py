# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

icon_cache = {}


@register.simple_tag
def icon(name, size=16, *, ignore_missing=False, classes=""):
    key = f"{name}-{size}"

    if key in icon_cache:
        return mark_safe(icon_cache[key])  # noqa: S308

    file1 = Path(f"{settings.BASE_DIR}/app/resources/svg/octicons/{name}-{size}.svg")
    file2 = Path(f"{settings.BASE_DIR}/app/resources/svg/{name}-{size}.svg")
    file = None

    if file1.exists():
        file = file1
    elif file2.exists():
        file = file2

    if ignore_missing and file is None:
        return ""

    with file.open() as f:
        svg = f.read().strip()
        svg = svg[:5] + f'class="c-icon {escape(classes)}" ' + svg[5:]
        icon_cache[key] = svg

    return mark_safe(svg)  # noqa: S308
