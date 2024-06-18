import argparse

import geopandas
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils.timezone import now
from sqlalchemy import create_engine

from shapes.models import Shape, Type


class Command(BaseCommand):
    help = "Load given shapefile structure into the database"

    def add_arguments(self, parser):
        parser.add_argument("file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        file = options["file"]

        engine = create_engine(
            f"postgresql://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{settings.DATABASES['default']['NAME']}"
        )

        gdf = geopandas.read_file(file.name)
        required_cols = ["id", "name", "type", "parent_id", "properties", "geometry"]

        # optional cols, if not set make it empty
        if "properties" not in gdf.columns:
            gdf["properties"] = "{}"

        # make sure our required columns exist
        for col in required_cols:
            if col not in gdf.columns:
                msg = f"{col} column inside geo data is required"
                raise CommandError(msg)

        # first create types from strings
        pos = 1
        type_map = {}
        for t in gdf["type"].unique():
            tobj = Type(key=t, name=t.title(), position=pos)
            tobj.save()
            type_map[t] = tobj.id
            pos += 10

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
        gdf_no_parent = gdf[gdf["parent_id"].isna()].copy()
        gdf_no_parent[
            [
                "created_at",
                "updated_at",
                "id",
                "name",
                "type_id",
                "properties",
                "geometry",
            ]
        ].to_postgis(Shape._meta.db_table, engine, if_exists="append")

        gdf_with_parent = gdf[gdf["parent_id"].notna()].copy()
        gdf_with_parent["parent_id"] = gdf_with_parent["parent_id"].astype(
            "int"
        )  # no isna() rows left => cast to int, so SQLAlchemy can write to PostGis
        gdf_with_parent[
            [
                "created_at",
                "updated_at",
                "id",
                "name",
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
            cursor.execute(f"UPDATE {Shape._meta.db_table} SET area_sqm = \
                ST_Area(ST_Transform(geometry, utmzone(ST_Centroid(geometry))))")
