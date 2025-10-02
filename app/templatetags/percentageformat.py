# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template

register = template.Library()


@register.filter
def percentageformat(value, precision=2):
    if value is None:
        return "-"

    # TODO: doesn't handle localization and ltr/rtl
    return "{:.{}f} %".format(value * 100, precision)
