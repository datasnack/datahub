# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr)
