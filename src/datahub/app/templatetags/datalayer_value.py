# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt

from django import template

from datalayers.models import Datalayer
from shapes.models import Shape

register = template.Library()


@register.simple_tag
def datalayer_value(shape: Shape, datalayer: Datalayer, when: dt.date | None = None):
    # coerce empty string
    if when == "":
        when = None

    return shape.datalayer_value(datalayer, when=when)


# TODO: this is more of a hack to allow calling the datalayer_value() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def datalayer_last_value(shape: Shape, datalayer: Datalayer):
    return shape.datalayer_value(datalayer)


# TODO: this is more of a hack to allow calling the datalayer_value() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def datalayer_first_value(shape: Shape, datalayer: Datalayer):
    return shape.datalayer_value(datalayer, mode="up")
