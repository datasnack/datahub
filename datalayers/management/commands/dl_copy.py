from pathlib import Path


from django.db import connection
from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer, camel


class Command(BaseCommand):
    help = "Rename key of given Data Layer"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str)
        parser.add_argument("target", type=str)

    def handle(self, *args, **options):
        old_key = options["source"]
        new_key = options["target"]

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
                f'Source Data Layer "{old_key}" does not exist'
            ) from None

        # make sure the new_key does NOT  exist
        try:
            _ = Datalayer.objects.get(key=new_key)

            raise CommandError(
                f'Target Data Layer "{new_key}" already exists'
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

        source_tags = dl.tags.all()
        source_sources = dl.sources.all()

        # Reset pk/_state.adding of old class and save new. Yes it's the Django way.
        dl.pk = None
        dl._state.adding = True  # noqa: SLF001

        dl.key = new_key
        dl.name = f"{dl.name} ({new_key})"

        dl.save()

        self.stdout.write(
            self.style.SUCCESS(f"Copied Data Layer {old_key} ->  {new_key}")
        )

        dl.tags.set(source_tags)

        for source in source_sources:
            source.pk = None
            source._state.adding = True  # noqa: SLF001
            source.datalayer = dl
            source.save()

        # Copy class file
        if old_class.exists():
            self.stdout.write(self.style.SUCCESS("Renamed class file."))

            # 5.
            class_source = old_class.read_text()

            old_camel = camel(old_key)
            new_camel = camel(new_key)
            class_source = class_source.replace(old_camel, new_camel)
            new_class.write_text(class_source)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Renamed class name in file {old_camel} -> {new_camel}."
                )
            )
        else:
            self.stdout.write("No class file to copy.")
