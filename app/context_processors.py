from django.conf import settings


def add_datahub_login_required(request):
    return {
        "DATAHUB_VERSION": settings.DATAHUB_VERSION,
        "INSTANCE_VERSION": settings.INSTANCE_VERSION,
        "DATAHUB_CENTER_X": settings.DATAHUB_CENTER_X,
        "DATAHUB_CENTER_Y": settings.DATAHUB_CENTER_Y,
        "DATAHUB_CENTER_ZOOM": settings.DATAHUB_CENTER_ZOOM,
        "datahub_name": settings.DATAHUB_NAME,
        "datahub_login_required": settings.DATAHUB_LOGIN_REQUIRED,
        "DATAHUB_HEAD": settings.DATAHUB_HEAD,
    }
