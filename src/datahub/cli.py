# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
import tomllib
from pathlib import Path


def _find_settings() -> str | None:
    # 1. explicit env var wins
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    # 2. look for [tool.datahub] in the nearest pyproject.toml
    for folder in [Path.cwd(), *Path.cwd().parents]:
        pp = folder / "pyproject.toml"
        if pp.exists():
            cfg = tomllib.loads(pp.read_text()).get("tool", {}).get("datahub", {})
            if "settings" in cfg:
                sys.path.insert(0, str(folder))  # make the project importable
                return cfg["settings"]
    return None


def main():
    settings = _find_settings() or "datahub.settings.default"
    os.environ["DJANGO_SETTINGS_MODULE"] = settings
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
