# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe

from app.templatetags.icon import icon
from datalayers.models import Datalayer
from shapes.models import Type

register = template.Library()


def _dl_not_found_msg(key: str, user) -> str:
    if user.is_superuser:
        return f"[Data Layer not found ({key})]"

    return "[Data Layer not found]"


@register.simple_tag
def dl_has_data_access(dl: Datalayer, user) -> bool:
    return dl.data_visible_to(user)


@register.simple_tag(takes_context=True)
def dl_count(context):
    user = context["request"].user
    return Datalayer.objects.visible_to(user).count()


@register.simple_tag(takes_context=True)
def dl_link(context, key: str):
    user = context["request"].user
    try:
        datalayer = Datalayer.objects.visible_to(user).get(key=key)
    except Datalayer.DoesNotExist:
        return _dl_not_found_msg(key, user)

    return format_html(
        '<a class="text-reset text-decoration-none" href="{}" title="{}"><code class="text-code">{}</code></a>',
        datalayer.get_absolute_url(),
        datalayer.name,
        key,
    )


@register.simple_tag(takes_context=True)
def dl_spatial(context, key: str, output: str = "all"):
    if output not in ["all", "first", "last"]:
        return f"[Unknown output format '{output}']"

    user = context["request"].user
    try:
        datalayer = Datalayer.objects.visible_to(user).get(key=key)
    except Datalayer.DoesNotExist:
        return _dl_not_found_msg(key, user)

    shape_types = list(datalayer.get_available_shape_types)

    if len(shape_types) == 0:
        return f"[{key} has no shape types]"

    match output:
        case "all":
            html_li = []
            for t in shape_types:
                html_li.append(_format_shape_type(t))

            return format_html(
                "<ul>{}</ul>",
                format_html_join("", "<li>{}</li>", ((item,) for item in html_li)),
            )
        case "first":
            return _format_shape_type(shape_types[0])
        case "last":
            return _format_shape_type(shape_types[-1])


def _format_shape_type(shape_type: Type) -> SafeString:
    return format_html(
        '<a href="{}" title="{}">{}</a>',
        shape_type.get_absolute_url(),
        shape_type.name,
        shape_type.name,
    )


@register.simple_tag(takes_context=True)
def dl_temporal(context, key: str, output: str = "text"):
    if output not in ["text", "key", "icon", "letter", "format"]:
        return f"[Unknown output format '{output}']"

    user = context["request"].user
    try:
        datalayer = Datalayer.objects.visible_to(user).get(key=key)
    except Datalayer.DoesNotExist:
        return _dl_not_found_msg(key, user)

    temporal = datalayer.temporal_resolution

    if temporal is None:
        return "[Unknown, no source file]"

    match output:
        case "text":
            return temporal.text()
        case "key":
            return str(temporal)
        case "icon":
            icon_name = f"calendar-{temporal}"
            return icon(icon_name, ignore_missing=True)
        case "letter":
            return temporal.letter()
        case "format":
            return temporal.format()
