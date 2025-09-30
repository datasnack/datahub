from pathlib import Path

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def file(path: str) -> str:
    return reverse("app:file_download", kwargs={"file_path": path.removeprefix("./")})
