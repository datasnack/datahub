from django import template

register = template.Library()


@register.filter
def percentageformat(value, precision=2):
    if value is None:
        return "-"

    # TODO: doesn't handle localization and ltr/rtl
    return "{:.{}f} %".format(value * 100, precision)
