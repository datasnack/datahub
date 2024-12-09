from django.conf import settings
from django.template.defaultfilters import slugify


def datahub_key(value: str = "") -> str:
    """Get the ID of the Data Hub instance."""
    key = settings.DATAHUB_KEY

    if not key:
        key = f"{slugify(settings.DATAHUB_NAME)}_"

    return f"{key}{value}"
