# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only


from functools import cache
from importlib.util import find_spec
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@cache
def datalayers_path() -> Path:
    ns = settings.DATAHUB_DATALAYERS_MODULE
    try:
        spec = find_spec(ns)
    except ModuleNotFoundError:
        spec = None

    if spec is None:
        raise ImproperlyConfigured(
            f"DATAHUB_DATALAYERS_MODULE={ns!r} cannot be found. "
            f"Create the package or point the setting to an existing one."
        )
    if not spec.submodule_search_locations:
        raise ImproperlyConfigured(
            f"DATAHUB_DATALAYERS_MODULE={ns!r} is a module, not a package "
            f"(it needs to be a folder with an __init__.py)."
        )
    return Path(spec.submodule_search_locations[0])
