import argparse
from pathlib import Path

import geopandas
from shapely import wkt

from django.core.management.base import BaseCommand

from shapes.models import Shape, Type

class Command(BaseCommand):
    help = "Export loaded shapefiles"

    def add_arguments(self, parser):
        parser.add_argument('--format', default=None)
        parser.add_argument('--file', nargs='?', default=None, help='Specify the filename for the dump')

    def handle(self, *args, **options):
        format = options["format"]

        file = options['file']
        if not file:
            file = 'shapes.csv'

        path = Path('data/') / file
        shapes = Shape.objects.all().order_by('type__position', 'name')

        # transform objects into GeoDataFrame
        rows = []
        for s in shapes:
            r = {
                'id': s.id,
                'name': s.name,
                'type': s.type.key,
            }

            for k, v in s.properties.items():
                r[k] = v

            r['geometry'] = wkt.loads(s.geometry.wkt)

            rows.append(r)

        gdf = geopandas.GeoDataFrame(rows, geometry='geometry')
        gdf = gdf.set_crs(4326)

        gdf.to_csv(path, index=False)

