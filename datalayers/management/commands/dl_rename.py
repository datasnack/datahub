import os
from pathlib import Path

from psycopg import sql

from django.db import connection
from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer, camel


class Command(BaseCommand):
    help = "Rename key of given Data Layer"

    def add_arguments(self, parser):
        parser.add_argument("old_key", type=str)
        parser.add_argument("new_key", type=str)

    def handle(self, *args, **options):
        old_key = options["old_key"]
        new_key = options["new_key"]

        # before renaming we need to check:
        # - does the old_key exist?
        # - does the new_key NOT exist?
        # - does the new_key data dir NOT exist?
        # - does the new_key class file NOT exist?

        # check that the old_key exists
        try:
            dl = Datalayer.objects.get(key=old_key)
        except Datalayer.DoesNotExist:
            raise CommandError(
                f'Origin Data Layer "{old_key}" does not exist'
            ) from None

        # make sure the new_key does NOT  exist
        try:
            _ = Datalayer.objects.get(key=options["new_key"])

            raise CommandError(
                f'Target Data Layer "{options['new_key']}" already exists'
            ) from None
        except Datalayer.DoesNotExist:
            pass

        new_data = Path(f"./data/datalayers/{new_key}/")
        if new_data.exists():
            raise CommandError(
                f'New data directory "{new_data.as_posix()}" already exists'
            ) from None

        old_class = dl.get_class_path()
        new_class = Path(f"src/datalayer/{new_key}.py")

        if new_class.exists():
            raise CommandError(
                f'Data Layer class at  "{new_class.as_posix()}" already exists'
            ) from None

        # 1. Rename in datalayer table (log is not needed, it stores only ref id)
        # 2. Rename data/vector data table
        # 3. Rename data folder
        # 4. Rename file
        # 5. Rename class inside file

        # 1.
        dl.key = new_key
        dl.save()
        self.stdout.write(self.style.SUCCESS("Renamed Data Layer key"))

        # 2.
        # can't use is_loaded() b/c layer is already renamed
        if old_key in connection.introspection.table_names():
            query = sql.SQL("ALTER TABLE {old_table} RENAME TO {new_table}").format(
                old_table=sql.Identifier(old_key), new_table=sql.Identifier(new_key)
            )
            with connection.cursor() as c:
                c.execute(query)
            self.stdout.write(self.style.SUCCESS("Renamed table of Data Layer."))
        else:
            self.stdout.write("Data Layer was not loaded so no table to rename.")

        # vector data tables can have custom name, alert the user if it is set
        if dl.has_class() and dl._get_class().raw_vector_data_table:
            self.stdout.write(
                self.style.WARNING(
                    f'Data Layer has a vector data table named "{dl._get_class().raw_vector_data_table}" you need to rename/change manually.'
                )
            )

        # 3.
        old_data_path = Path(f"./data/datalayers/{old_key}/")
        if old_data_path.exists():
            old_data_path.rename(f"./data/datalayers/{new_key}/")
            self.stdout.write(self.style.SUCCESS("Renamed data directory."))
        else:
            self.stdout.write("No data directory to rename.")

        # 4.
        class_path = Path(f"src/datalayer/{old_key}.py")
        if class_path.exists():
            class_path = class_path.rename(f"src/datalayer/{new_key}.py")
            self.stdout.write(self.style.SUCCESS("Renamed class file."))

            # 5.
            class_source = class_path.read_text()

            old_camel = camel(old_key)
            new_camel = camel(new_key)
            class_source = class_source.replace(old_camel, new_camel)
            class_path.write_text(class_source)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Renamed class name in file {old_camel} -> {new_camel}."
                )
            )
        else:
            self.stdout.write("No class file to rename.")
