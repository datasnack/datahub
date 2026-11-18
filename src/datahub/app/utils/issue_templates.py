# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
from typing import TypedDict
from urllib.parse import urlencode

import yaml

from django.conf import settings


class IssueTemplate(TypedDict):
    name: str
    url: str


def enumerate_issue_templates() -> list[IssueTemplate]:
    issue_templates: list[IssueTemplate] = []

    # If no forge is configured, we have no base URL to link to
    if not settings.DATAHUB_FORGE:
        return issue_templates

    if not settings.DATAHUB_FORGE_ISSUE_SHOW_ADD:
        return issue_templates

    issue_template_path: Path = Path(settings.DATAHUB_FORGE_ISSUE_TEMPLATES_PATH)

    if not issue_template_path.exists():
        return issue_templates

    # Order by name, in case templates are prefixed with 1-, 2-, ... for sorting
    templates = sorted(issue_template_path.glob("*.yaml"))

    for template in templates:
        with template.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        template_name = data.get("name")
        path_in_repo = urlencode(
            {
                "template": f"{settings.DATAHUB_FORGE_ISSUE_TEMPLATES_REPO}{template.name}"
            }
        )
        template_url = f"{settings.DATAHUB_FORGE}/issues/new?{path_in_repo}"

        issue_templates.append(
            {
                "name": template_name,
                "url": template_url,
            }
        )

    return issue_templates
