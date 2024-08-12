import json
from pathlib import Path
from urllib.parse import quote

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

# todo: hot_file is used for the Vite client tag and each resource once, this should be only checked once per request.


@register.simple_tag
def vite_dev():
    """Include vite dev server client for hot reloading."""
    if settings.DEBUG:
        hot_file = Path(f"{settings.BASE_DIR}/app/static/hot")
        if hot_file.exists():
            dev_server_url = hot_file.read_text()
            return mark_safe(
                f'<script type="module" src="{dev_server_url}/@vite/client"></script>'
            )
    return ""


def _tag_for_type(file):
    if file.endswith("css"):
        return mark_safe(f'<link rel="stylesheet" href="{file}">')

    if file.endswith("js"):
        return mark_safe(f'<script type="module" src="{file}"></script>')

    raise Exception(f"Unknown extension for vite asset: {file}")


@register.simple_tag
def vite_asset(file):
    if settings.DEBUG:
        # if a hot file is present, Vite dev mode runs and we return dev server path
        hot_file = Path(f"{settings.BASE_DIR}/app/static/hot")
        if hot_file.exists():
            dev_server_url = hot_file.read_text()
            return _tag_for_type(f"{dev_server_url}/{quote(file)}")

        # no dev mode look fpr manifest and return last built file
        manifest_file = Path(f"{settings.BASE_DIR}/app/static/build/manifest.json")
    else:
        # look for manifest.json in prod, after collectstatic has been run
        manifest_file = Path(f"{settings.STATIC_ROOT}/build/manifest.json")
        print(manifest_file)

    if not manifest_file.exists():
        raise Exception(f"manifest.json not found at {manifest_file.as_posix()}")

    manifest = json.loads(manifest_file.read_text())

    if file not in manifest:
        raise Exception(f"Unknown file in manifest.json: {file}")

    static = settings.STATIC_URL
    static = static if static.endswith("/") else static + "/"

    return _tag_for_type(f"{static}build/{quote(manifest[file]["file"])}")
