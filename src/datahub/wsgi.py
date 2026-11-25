# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
WSGI config for datahub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from .cli import _find_settings

settings = _find_settings() or "datahub.settings.default"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

application = get_wsgi_application()
