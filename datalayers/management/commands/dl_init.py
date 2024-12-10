from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer, camel


class Command(BaseCommand):
    help = "Load given shapefile structure into the database"

    def add_arguments(self, parser):
        parser.add_argument("key", nargs="?", default="", type=str)
        parser.add_argument("--name", nargs="?", default="", type=str)
        parser.add_argument("--template", nargs="?", default="", type=str)

    def handle(self, *args, **options):
        if not options["key"]:
            self.stdout.write("Key of the the new Data Layer (snake_case):")
            options["key"] = input()
        options["key"] = options["key"].strip()

        # handle data base model
        has_dl_model = Datalayer.objects.filter(key=options["key"]).exists()

        if not has_dl_model:
            if not options["name"]:
                self.stdout.write("Name of the the new Data Layer:")
                options["name"] = input()

            options["name"] = options["name"].strip()

            # Create database entry
            dl = Datalayer.objects.create(key=options["key"], name=options["name"])
            dl.save()

            self.stdout.write(
                self.style.SUCCESS("Data Layer model created in database.")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Data Layer with {options["key"]} already exists in the database."
                )
            )

        dl_file = Path(f"src/datalayer/{options['key']}.py")

        # Check if it already exists

        if not dl_file.exists():
            name_camel = camel(options["key"])
            # Create source file
            tpl = f"""from datalayers.datasources.base_layer import BaseLayer


class {name_camel}(BaseLayer):
    def __init__(self) -> None:
        super().__init__()

    def download(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError
"""

            f = dl_file.open("w+")
            f.write(tpl)
            f.close()
            self.stdout.write(self.style.SUCCESS("Data Layer file created."))

        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Data Layer file "{dl_file}" already exists on filesystem'
                )
            )
