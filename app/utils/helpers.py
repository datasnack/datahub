import contextlib
import datetime as dt
import hashlib

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.dateparse import parse_date


def datahub_key(value: str = "") -> str:
    """Get the ID of the Data Hub instance."""
    key = settings.DATAHUB_KEY

    if not key:
        key = f"{slugify(settings.DATAHUB_NAME)}_"

    return f"{key}{value}"


def prase_date_or_today(date_str: str) -> dt.date:
    """Parse yyyy-mm-dd string and return Date object, if malformed string or invalid date, returns todays date."""
    parsed_date = None
    if date_str:
        with contextlib.suppress(ValueError):
            parsed_date = parse_date(date_str)

    if parsed_date is None:
        parsed_date = dt.datetime.now(tz=dt.UTC).date()

    return parsed_date


def dict_to_string(input_dict):
    """Convert a dictionary to a deterministic string."""
    parts = [f"{key}={value}" for key, value in sorted(input_dict.items())]
    return "&".join(parts)


def generate_unique_hash(input_dict):
    """Generate a unique hash based on the input dictionary."""
    serialized = dict_to_string(input_dict)
    hash_object = hashlib.sha256(serialized.encode())
    return hash_object.hexdigest()
