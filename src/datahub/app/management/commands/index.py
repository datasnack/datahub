# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from psycopg import sql

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Create indices for all Data Layer tables on the shape_id column."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        datalayers = Datalayer.objects.all()

        for dl in datalayers:
            if not dl.is_loaded():
                continue

            with connection.cursor() as cursor:
                index_name = f"ix_{dl.key}_shape_id"
                table_name = dl.key
                query = sql.SQL(
                    "CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (shape_id)"
                ).format(
                    index_name=sql.Identifier(index_name),
                    table_name=sql.Identifier(table_name),
                )

                cursor.execute(query)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Index '{index_name}' created successfully on '{table_name}.shape_id'"
                    )
                )
