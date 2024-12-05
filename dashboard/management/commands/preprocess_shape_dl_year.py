from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError

from dashboard.models import ShapeDataLayerYearStats
from datalayers.datasources.base_layer import LayerTimeResolution
from datalayers.models import Datalayer
from shapes.models import Shape


class Command(BaseCommand):
    help = 'Precompute data layer stats for shapes'

    def handle(self, *args, **kwargs):
        data_layers = Datalayer.objects.all()

        ShapeDataLayerYearStats.objects.all().delete()


        for data_layer in data_layers:
            table_name = data_layer.key
            temporal_resolution = data_layer.temporal_resolution

            if temporal_resolution == LayerTimeResolution.YEAR:
                self.copy_all_entries(table_name, data_layer)
            else:
                self.process_non_yearly_layers(data_layer)

        self.stdout.write(self.style.SUCCESS('Successfully precomputed stats!'))

    def copy_all_entries(self, table_name, data_layer):
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"""
                    INSERT INTO dashboard_shapedatalayeryearstats (shape_id, data_layer, year, value)
                    SELECT shape_id, %s AS data_layer, year, value
                    FROM {table_name}
                """, [data_layer.key])
            except ProgrammingError as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing {table_name}: {str(e)}"))
                return
        self.stdout.write(
            f'Copied data from {table_name}.')

    def process_non_yearly_layers(self, data_layer):
        table_name = data_layer.key

        for shape in Shape.objects.all():
            available_years = data_layer.get_available_years

            for year in available_years:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT AVG(value)
                        FROM {table_name}
                        WHERE shape_id = %s AND EXTRACT(year from date) = %s
                    """, [shape.id, year])
                    result = cursor.fetchone()

                    if result and result[0] is not None:
                        avg_value = result[0]
                        ShapeDataLayerYearStats.objects.create(
                            shape_id=shape.id,
                            data_layer=data_layer.key,
                            year=year,
                            value=avg_value
                        )
            self.stdout.write(
                f'Finished processing data from {table_name}.')
