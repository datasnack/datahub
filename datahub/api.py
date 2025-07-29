from ninja import NinjaAPI
from ninja.security import APIKeyHeader, SessionAuth

from django.conf import settings

from datalayers.api import router as datalayers_router
from shapes.api import router as shapes_router
from app.models import BearerToken


class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        bearer_token = BearerToken.objects.filter(token=key).first()

        if bearer_token:
            return key

        return False


def anonymous_api_access(request):
    if settings.DATAHUB_LOGIN_REQUIRED:
        return False

    return "anonymous"


auth = [SessionAuth(), ApiKey(), anonymous_api_access]

api = NinjaAPI(
    title="Data Hub API",
    auth=auth,
)

api.add_router("/shapes/", shapes_router)
api.add_router("/datalayers/", datalayers_router)
