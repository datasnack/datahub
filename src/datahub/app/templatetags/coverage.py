# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template

from datalayers.models import Datalayer
from shapes.models import Type

register = template.Library()


# TODO: this is more of a hack to allow calling the value_coverage() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def coverage(dl: Datalayer, shape_type: Type):
    return dl.value_coverage(shape_type)
