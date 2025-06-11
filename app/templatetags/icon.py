from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

icon_cache = {}


@register.simple_tag
def icon(name, size=16, *, ignore_missing=False, classes=""):
    key = f"{name}-{size}"

    if key in icon_cache:
        return mark_safe(icon_cache[key])  # noqa: S308

    # TODO: the name to the app this templatetag is inside (app) is hardcoded
    file_name = f"{settings.BASE_DIR}/app/static/vendor/icons/{name}-{size}.svg"

    if ignore_missing and not Path(file_name).exists():
        return ""

    with Path(file_name).open() as f:
        svg = f.read().strip()
        svg = svg[:5] + f'class="c-icon {classes}" ' + svg[5:]
        icon_cache[key] = svg

    return mark_safe(svg)  # noqa: S308
