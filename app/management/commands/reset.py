from django.core.management.base import BaseCommand
from django.core.management import call_command

from shapes.models import Shape, Type
from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Reset parts of the database (shapes, data-layers, processed-data, django, or everything)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--shapes", action="store_true", help="Drop all shape and shape type models"
        )
        parser.add_argument(
            "--data-layers", action="store_true", help="Drop all data layer models"
        )
        parser.add_argument(
            "--processed-data",
            action="store_true",
            help="Drop all per-layer processed data tables",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Drop everything (equivalent to flush + extras)",
        )

        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do not prompt for confirmation (unsafe in production!)",
        )

    def handle(self, *args, **options):
        # Map CLI flags -> internal names
        mapping = {
            "shapes": "shapes",
            "data_layers": "data-layers",
            "processed_data": "processed-data",
        }

        if options["all"]:
            targets = ["all"]
        else:
            targets = [mapping[name] for name in mapping if options[name]]

        if not targets:
            self.stdout.write(
                self.style.ERROR(
                    "You must specify at least one option: "
                    "--shapes, --data-layers, --processed-data, or --all"
                )
            )
            return

        # Confirm if no --noinput
        if not options["noinput"]:
            self.stdout.write(
                self.style.WARNING(
                    f"This will irreversibly delete: {', '.join(targets)}"
                )
            )
            confirm = input("Are you sure you want to continue? (yes/no): ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.ERROR("Reset cancelled."))
                return

        # Dispatch
        if "all" in targets:
            self.reset_all()
        else:
            if "shapes" in targets:
                self.reset_shapes()
            if "data-layers" in targets:
                self.reset_data_layers()
            if "processed-data" in targets:
                self.reset_processed_data()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully reset {', '.join(targets)}.")
        )

    #
    # ---- Implementation stubs ----
    #
    def reset_shapes(self):
        Shape.objects.all().delete()
        Type.objects.all().delete()

    def reset_data_layers(self):
        Datalayer.objects.all().delete()

    def reset_processed_data(self):
        for dl in Datalayer.objects.all():
            dl.reset(log=True, data=True)

    def reset_all(self):
        self.reset_processed_data()
        self.reset_data_layers()
        self.reset_shapes()
