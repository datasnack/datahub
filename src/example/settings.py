# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from datahub.settings import *  # noqa: F403

INSTALLED_APPS += ["example"]
DATAHUB_DATALAYERS_MODULE = "example.datalayer"

SECRET_KEY = "changeme"
