import json

from sqlalchemy import create_engine

from django.conf import settings
from django.contrib import messages
from django.core import serializers


def dumpdata(datalayers) -> str:
    """Serialize a list of Data Layers with their dependant models."""
    categories = {}
    sources = []
    tags = []
    tagged_items = []

    for dl in datalayers:
        # aggregate categories over a dict, to prevent multiple same category entries
        if dl.category:
            categories[dl.category.key] = dl.category

        for source in dl.sources.all():
            sources.append(source)

        if False:
            for tag in dl.tags.all():
                tags.append(tag)

                tagged_items.append(
                    TaggedItem(tag_id=tag.id, object_id=dl.id, content_type_id=7)
                )

    objects = list(categories.values()) + tags + datalayers + sources + tagged_items

    return serializers.serialize(
        "json",
        objects,
        indent=2,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )


def loaddata(data: str):
    msgs = []

    objs = json.loads(data)

    for obj in objs:
        # relation does potentially not exist in current hub, so we can't import those
        # in a safe manner for now we strip relations completely and alert the user.
        if obj["model"] == "datalayers.datalayer":
            for relation in obj["fields"]["related_to"]:
                msgs.append(
                    {
                        "level": messages.ERROR,
                        "message": f"Relation {obj['fields']['key']} -> {relation[0]} needs to be created manually.",
                    }
                )
            del obj["fields"]["related_to"]

    data = json.dumps(objs)

    for obj in serializers.deserialize("json", data, ignorenonexistent=True):
        obj_class = obj.object.__class__.__name__
        already_exists = obj.object.pk is not None

        if already_exists:
            msgs.append(
                {
                    "level": messages.WARNING,
                    "message": f"Existing {obj_class} with key={obj.object.natural_key()} will be used.",
                }
            )
        else:
            msgs.append(
                {
                    "level": messages.SUCCESS,
                    "message": f"Creating {obj_class} with key={obj.object.natural_key()}.",
                }
            )

            obj.save()

    return msgs


def get_conn_string(sqlalchemy=True) -> str:
    """
    Database connection string (used for i.e. Pandas).

    This connection string is used for pandas.read_sql() etc. Pandas doesn't like psycopg
    connection objects, raised the following warning:

    > UserWarning: pandas only supports SQLAlchemy connectable (engine/connection) or
    > database string URI or sqlite3 DBAPI2 connection. Other DBAPI2 objects are not
    > tested. Please consider using SQLAlchemy.

    There are some reports that it "works just fine" (https://github.com/pandas-dev/pandas/issues/45660)
    with DBAPI2 objects for PostgreSQL (which psycopg implements, and as such the Django
    django.db.connection also is. I tested it as well and it seemed to work. Though
    there is still the warning, suppressing it could hide different warnings, so we just
    install SQLAlchemy and provide pandas the connection string...

    When you provide a connection object you are responsible for closing. We just use
    the string and let handle pandas the connection itself. This is not ideal, since we
    just install SQLAlchemy for Pandas usage and can't use the global database connection
    provided by Django.
    """
    # in the context of python/pandas we need the extra protocol qualifier so SQLAlchemy
    # selects psycopg v3 and does not try to load psycopg2 v2 (which is NOT installed).
    # but in case for other use cases of the connection string restoring/dumping the
    # database, this extra qualifier would crash the pg_dump/restore commands.
    proto = ""
    if sqlalchemy:
        # Explicitly use "psycopg" (v3) and NOT "psycopg2" (v2)
        proto = "+psycopg"
    return f"postgresql{proto}://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{settings.DATABASES['default']['NAME']}"


def get_engine():
    return create_engine(get_conn_string())


def dictfetchone(cursor):
    """
    Return one row from a cursor as a dict.

    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row is not None:
        return dict(zip(columns, row))
    return None


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.

    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
