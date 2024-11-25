import uuid

from django import template

register = template.Library()


@register.simple_tag
def generate_uuid():
    """Generate a unique UUID."""
    return str(uuid.uuid4())
