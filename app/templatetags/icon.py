from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

icon_cache = {}

@register.simple_tag
def icon(name, size=16):
    key = f"{name}-{size}"

    if key in icon_cache:
        return mark_safe(icon_cache[key])

    file_name = f"{settings.BASE_DIR}/static/vendor/icons/{name}-{size}.svg"
    with open(file_name, 'r',  encoding="utf-8") as f:
        svg = f.read()
        svg = svg[:5] + 'class="c-icon" ' + svg[5:]
        icon_cache[key] = svg

    return mark_safe(svg)
