import argparse

import geopandas
from psycopg import sql

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils.timezone import now

from datalayers.utils import get_engine
from shapes.models import Shape, Type


class Command(BaseCommand):
    help = "Load given shapefile structure into the database"

    def add_arguments(self, parser):
        parser.add_argument("file", type=argparse.FileType("r"))
        parser.add_argument(
            "--truncate-shapes-before-import",
            action="store_true",
            help="Truncate existing shapes from the database before importing new ones.",
        )

    def handle(self, *args, **options):
        truncate = options["truncate_shapes_before_import"]
        file = options["file"]

        if truncate:
            self.stdout.write(self.style.WARNING("Truncating shapes table..."))

            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("TRUNCATE TABLE {table}").format(
                        table=sql.Identifier(Shape._meta.db_table)
                    )
                )

        engine = get_engine()

        gdf = geopandas.read_file(file.name)
        required_cols = [
            "id",
            "name",
            "type",
            "parent_id",
            "properties",
            "geometry",
        ]

        # key field is required, but we can fallback to id if not provided
        if "key" not in gdf.columns:
            gdf["key"] = gdf["id"]

        # optional cols, if not set make it empty
        if "description" not in gdf.columns:
            gdf["description"] = ""
        if "license" not in gdf.columns:
            gdf["license"] = ""
        if "properties" not in gdf.columns:
            gdf["properties"] = "{}"
        if "attribution_text" not in gdf.columns:
            gdf["attribution_text"] = ""
        if "attribution_url" not in gdf.columns:
            gdf["attribution_url"] = ""
        if "attribution_html" not in gdf.columns:
            gdf["attribution_html"] = ""

        if "admin" not in gdf.columns:
            gdf["admin"] = None

        # make sure our required columns exist
        for col in required_cols:
            if col not in gdf.columns:
                raise CommandError(f"{col} column inside geo data is required")

        # column types matching the database schema
        gdf["admin"] = gdf["admin"].astype("Int16")  # cast to int with NULL support

        # first create types from strings
        order_position = 1
        type_map = {}
        for t in gdf["type"].unique():
            try:
                tobj = Type.objects.get(key=t)
            except Type.DoesNotExist:
                tobj = Type(key=t, name=t.title(), position=order_position)
                tobj.save()
                order_position += 10

            type_map[t] = tobj.id

        def get_type_id(t) -> int:
            return type_map[t]

        gdf["type_id"] = gdf["type"].apply(get_type_id)
        gdf = gdf.drop(columns=["type"])

        gdf["created_at"] = now()
        gdf["updated_at"] = now()

        # In Geopandas/Pandas there is no None/Null value for Integers. So our
        # parent_id column with the int reference is of type float (b/c upper most
        # shapes have no parent_id).
        # SQLAlchemy / Geopandas to_postgis() can't handle a float in enforcing the
        # foreign key to the parent row.
        # ...so we need to split our input data in parent only rows and child rows
        # and import them separately.
        #
        # Also GeoPandas to_postgis() uses intermediary CSV files, which cast empty
        # strings to NULL. so the Django way of "nullable/empty" strings stored as "" (empty string)
        # clashes during imports, this is why we use `null=True, blank=True` for optional
        # fields in the model (see https://github.com/geopandas/geopandas/issues/2588).
        gdf_no_parent = gdf[gdf["parent_id"].isna()].copy()
        gdf_no_parent[
            [
                "created_at",
                "updated_at",
                "id",
                "key",
                "name",
                "description",
                "admin",
                "license",
                "attribution_text",
                "attribution_url",
                "attribution_html",
                "type_id",
                "properties",
                "geometry",
            ]
        ].to_postgis(Shape._meta.db_table, engine, if_exists="append")

        gdf_with_parent = gdf[gdf["parent_id"].notna()].copy()

        # no isna() rows left => cast to int, so SQLAlchemy can write to PostGIS
        gdf_with_parent["parent_id"] = gdf_with_parent["parent_id"].astype("int")

        gdf_with_parent[
            [
                "created_at",
                "updated_at",
                "id",
                "key",
                "name",
                "description",
                "admin",
                "license",
                "attribution_text",
                "attribution_url",
                "attribution_html",
                "type_id",
                "parent_id",
                "properties",
                "geometry",
            ]
        ].to_postgis(Shape._meta.db_table, engine, if_exists="append")

        # calculate shape area
        # Date are in ESPG:4326 (deg based), so for ST_Area() to produce m2
        # we need to convert to a meters based system. With utmzone() we identify
        # the resp. used UTM Zone that is m based.
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "UPDATE {table} SET area_sqm = \
                ST_Area(ST_Transform(geometry, utmzone(ST_Centroid(geometry))))"
                ).format(table=sql.Identifier(Shape._meta.db_table))
            )
