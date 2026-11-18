# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import uuid

from django import template

register = template.Library()


@register.simple_tag
def generate_uuid():
    """Generate a unique UUID."""
    return str(uuid.uuid4())
