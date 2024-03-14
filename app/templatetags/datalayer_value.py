from django import template

from datalayers.models import Datalayer
from shapes.models import Shape

register = template.Library()

# todo: this is more of a hack to allow calling the datalayer_value() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def datalayer_value(shape: Shape, datalayer: Datalayer):
    return shape.datalayer_value(datalayer)


# todo: this is more of a hack to allow calling the datalayer_value() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def datalayer_first_value(shape: Shape, datalayer: Datalayer):
    return shape.datalayer_value(datalayer, mode="up")
