# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django import template

register = template.Library()


@register.simple_tag
def call_method(obj, method_name, *args):
    """https://stackoverflow.com/questions/28513528/passing-arguments-to-model-methods-in-django-templates"""
    method = getattr(obj, method_name)
    return method(*args)
