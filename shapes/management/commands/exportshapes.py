import argparse
from pathlib import Path

import geopandas
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from shapely import wkt

from shapes.models import Shape


class Command(BaseCommand):
    help = "Export loaded Shapes in different formats"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            nargs="?",
            default=None,
            help="Specify the filename",
        )

        parser.add_argument(
            "--format",
            type=str,
            choices=["csv", "xlsx", "gpkg"],
            required=True,
            help='Specify the format of the file. Must be one of "csv", "excel", or "gpkg".',
        )

        parser.add_argument(
            "--geometry",
            default=True,
            action=argparse.BooleanOptionalAction,
            help="Boolean flag to include geometry. Default is True.",
        )

    def handle(self, *args, **options):
        file = options["file"]
        if not file:
            file = f'shapes.{options["format"]}'

        if not options["geometry"] and options["format"] == "gpkg":
            raise CommandError(
                "--no-geometry can't be used in conjunction with GPKG output."
            )

        path = Path("data/") / file
        shapes = Shape.objects.all().order_by("type__position", "name")

        # transform objects into GeoDataFrame
        rows = []
        for s in shapes:
            r = {
                "id": s.id,
                "name": s.name,
                "type": s.type.key,
            }

            for k, v in s.properties.items():
                r[k] = v

            if options["geometry"]:
                r["geometry"] = wkt.loads(s.geometry.wkt)

            rows.append(r)

        if options["geometry"]:
            gdf = geopandas.GeoDataFrame(rows, geometry="geometry")
            gdf = gdf.set_crs(4326)
        else:
            gdf = pd.DataFrame(rows)

        # Save file according to format
        match options["format"]:
            case "csv":
                gdf.to_csv(path, index=False)
            case "xlsx":
                gdf.to_excel(path, index=False)
            case "gpkg":
                gdf.to_file(path, index=False)
            case _:
                pass
