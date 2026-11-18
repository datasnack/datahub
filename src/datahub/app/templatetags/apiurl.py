# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from urllib.parse import urlencode

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def apiurl(context, route_name, full=False, **kwargs):
    """
    Simple URL tag that:
    1. Resolves the route name (no URL parameters)
    2. Adds all kwargs as GET parameters
    3. Optionally returns fully qualified URLs

    Usage:
    {% apiurl 'api_users' %}
    {% apiurl 'api_users' page=2 limit=10 %}
    {% apiurl 'api_users' full=True page=2 %}
    """
    # Resolve the base URL (no parameters)
    base_url = reverse(f"api-1.0.0:{route_name}")

    # Add GET parameters if any
    if kwargs:
        query_string = urlencode(kwargs, doseq=True)
        base_url = f"{base_url}?{query_string}"

    # Make it fully qualified if requested
    if full:
        request = context.get("request")
        if request:
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            base_url = f"{scheme}://{host}{base_url}"

    return base_url
