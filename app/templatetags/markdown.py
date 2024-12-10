import mistune

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def markdown(md):
    """Parse and return Markdown as HTML."""

    markdown = mistune.create_markdown(
        escape=True, hard_wrap=True, plugins=["table", "url", "footnotes"]
    )

    html = markdown(md)

    html = html.replace("<table>", '<table class="table table-sm">')

    return mark_safe(html)  # noqa: S308
