import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from app.models import BearerToken


class ApiAuthMiddleware:
    """
    Middleware component that checks if API routes are authenticated.

    To access the API
    - Either the Data Hub instance is publicly available
    - an authenticated session cookies is part of the request
    - a bearer token Header is set in the request.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        self.required = tuple(re.compile(url) for url in [r"/api/(.*)$"])
        self.exceptions = ()

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # No need to process URLs if user already logged in
        if request.user.is_authenticated:
            return None

        # An exception match should immediately return None
        for url in self.exceptions:
            if url.match(request.path):
                return None

        # Public API, no auth required
        if not settings.DATAHUB_LOGIN_REQUIRED:
            return None

        # Requests matching a restricted URL pattern are returned
        # wrapped with the login_required decorator
        for url in self.required:
            if url.match(request.path):
                auth_header = request.headers.get("authorization")

                if auth_header and auth_header.startswith("Bearer "):
                    _, token = auth_header.split(" ", 2)

                    bearer_token = BearerToken.objects.filter(token=token).first()
                    if bearer_token:
                        # todo: the user owning this bearer token needs to be assigned to the request/session
                        return None

                    return HttpResponse("Unauthorized", status=401)

                return HttpResponse("Unauthorized", status=401)

        # Explicitly return None for all non-matching requests
        return None
