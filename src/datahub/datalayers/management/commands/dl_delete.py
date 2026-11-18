# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from psycopg import sql

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Rename key of given Data Layer"

    def add_arguments(self, parser):
        parser.add_argument("datalayer", type=str)

        parser.add_argument(
            "--data",
            action="store_true",
            default=False,
            help="Delete also the data directory",
        )

    def handle(self, *args, **options):
        key = options["datalayer"]

        # check that the key exists
        try:
            dl = Datalayer.objects.get(key=key)
        except Datalayer.DoesNotExist:
            raise CommandError(f'Data Layer "{key}" does not exist') from None

        if dl.is_loaded():
            query = sql.SQL("DROP TABLE {table}").format(table=sql.Identifier(dl.key))
            with connection.cursor() as c:
                c.execute(query)

            self.stdout.write(
                self.style.SUCCESS(f"Deleted table of Data Layer {dl.key}.")
            )

        if dl.has_class():
            data_dir = dl._get_class().get_data_path()
            class_file = dl.get_class_path()

            if options["data"] and data_dir.exists():
                data_dir.unlink()
                self.stdout.write(
                    self.style.SUCCESS(f"Deleted data dir {data_dir.as_posix()}")
                )

            if class_file.exists():
                class_file.unlink()
                self.stdout.write(
                    self.style.SUCCESS(f"Delete class file {class_file.as_posix()}")
                )

        dl.delete()
        self.stdout.write(self.style.SUCCESS("Deleted Data Layer instance"))
