from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def percentageformat(value, precision=2):

    if value is None:
        return "-"

    # todo: doesn't handle localization and ltr/rtl
    return "{:.{}f} %".format(value * 100, precision)
