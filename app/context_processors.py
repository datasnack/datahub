# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django.conf import settings

from app.docs import get_docs_structure
from app.utils.issue_templates import enumerate_issue_templates


def add_datahub_login_required(request):
    return {
        "DATAHUB_VERSION": settings.DATAHUB_VERSION,
        "INSTANCE_VERSION": settings.INSTANCE_VERSION,
        "DATAHUB_CENTER_X": settings.DATAHUB_CENTER_X,
        "DATAHUB_CENTER_Y": settings.DATAHUB_CENTER_Y,
        "DATAHUB_CENTER_ZOOM": settings.DATAHUB_CENTER_ZOOM,
        "datahub_name": settings.DATAHUB_NAME,
        "datahub_login_required": settings.DATAHUB_LOGIN_REQUIRED,
        "DATAHUB_HEAD": settings.DATAHUB_HEAD,
        "DATAHUB_FORGE": settings.DATAHUB_FORGE,
        "DATAHUB_FORGE_ISSUE_SHOW_ADD": settings.DATAHUB_FORGE_ISSUE_SHOW_ADD,
        "DATAHUB_FORGE_ISSUE_TEMPLATES": enumerate_issue_templates(),
        "DOCS_STRUCTURE": get_docs_structure(),
    }
