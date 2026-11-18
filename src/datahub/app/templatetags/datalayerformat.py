# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template

from datalayers.models import Datalayer

register = template.Library()


# TODO: this is more of a hack to allow calling the datalayer_value() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def datalayerformat(value, datalayer: Datalayer):
    if value is None:
        return "n/a"

    return datalayer.str_format(value)
