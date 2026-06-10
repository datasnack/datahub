# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import mistune

from django import template
from django.utils.safestring import mark_safe
from app.utils.mistune import DjangoTemplateRenderer


register = template.Library()


@register.simple_tag(takes_context=True)
def markdown(context, md):
    """Parse and return Markdown as HTML."""

    user = context["request"].user

    markdown = mistune.create_markdown(
        renderer=DjangoTemplateRenderer(
            escape=True, allow_harmful_protocols=None, user=user
        ),
        escape=True,
        hard_wrap=True,
        plugins=["table", "url", "footnotes"],
    )

    html = markdown(md)

    html = html.replace("<table>", '<table class="table table-sm">')

    return mark_safe(html)  # noqa: S308
