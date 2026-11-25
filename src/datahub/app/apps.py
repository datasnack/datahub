# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datahub.app"

    def ready(self):
        from datahub.conf import datalayers_path

        # try to get the datalayer module path during startup (this ready() method)
        # If the module does not exists/is broken ImproperlyConfigured is raised
        datalayers_path()
