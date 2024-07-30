from sqlalchemy import create_engine

from django.conf import settings


def get_conn_string() -> str:
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
    # Explicitly use "psycopg" (v3) and NOT "psycopg2" (v2)
    return f"postgresql+psycopg://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{settings.DATABASES['default']['NAME']}"


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
