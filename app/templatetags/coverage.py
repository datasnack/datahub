from django import template

from datalayers.models import Datalayer
from shapes.models import Type

register = template.Library()

# todo: this is more of a hack to allow calling the value_coverage() method
# with a parameter from inside a template. Is there a better way?
@register.filter
def coverage(dl: Datalayer, shape_type: Type):
    cov = dl.value_coverage(shape_type)
    return cov
