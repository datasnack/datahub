import json
from django.core.management.base import BaseCommand
from django.db import connection

from datalayers.datasources.base_layer import LayerTimeResolution
from datalayers.models import Datalayer
from shapes.models import Shape


class Command(BaseCommand):
    help = 'Preprocess shape data by data layers and store in a JSON file'

    def handle(self, *args, **kwargs):
        data_layers = Datalayer.objects.all()
        shapes = Shape.objects.all()
        year_range = range(2000, 2025)

        preprocessed_data = {}

        for data_layer in data_layers:
            layer_key = data_layer.key
            layer_data = {}

            for year in year_range:
                year_data = {}
                for shape in shapes:
                    shape_id = shape.id
                    year_data[shape_id] = {'count': 0, 'geometry': shape.geometry.geojson, 'name': shape.name}
                    try:
                        if data_layer.temporal_resolution == LayerTimeResolution.YEAR:
                            query = f"""
                                SELECT COUNT(*)
                                FROM {layer_key}
                                WHERE shape_id = %s AND year = %s
                            """
                        else:
                            query = f"""
                                SELECT COUNT(*)
                                FROM {layer_key}
                                WHERE shape_id = %s AND EXTRACT(year FROM date) = %s
                            """

                        with connection.cursor() as c:
                            c.execute(query, [shape_id, year])
                            rec_count = c.fetchone()[0]

                        year_data[shape_id]['count'] = rec_count

                    except Exception as e:
                        pass

                layer_data[year] = year_data

            preprocessed_data[layer_key] = layer_data

        with open('shape_data_layers.json', 'w') as f:
            json.dump(preprocessed_data, f, indent=2)

        self.stdout.write(self.style.SUCCESS('Data successfully preprocessed and saved by data layers.'))
