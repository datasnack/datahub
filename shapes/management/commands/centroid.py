from psycopg import sql
from shapely import wkb

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from shapes.models import Shape, Type


class Command(BaseCommand):
    help = "Calculate centroid of all loaded shapes"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with connection.cursor() as c:
            c.execute(
                sql.SQL(
                    "SELECT (ST_Centroid(ST_Union(ST_Centroid(geometry)))) as centroid FROM {table}"
                ).format(table=sql.Identifier(Shape._meta.db_table))
            )
            row = c.fetchone()

        centroid = wkb.loads(row[0])

        self.stdout.write(f"Centroid is: {centroid}")
        self.stdout.write("Set in .env file as follows:")
        self.stdout.write("")
        self.stdout.write(f"DATAHUB_CENTER_X={centroid.x}")
        self.stdout.write(f"DATAHUB_CENTER_Y={centroid.y}")
