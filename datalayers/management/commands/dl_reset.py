from django.core.management.base import BaseCommand

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Resets a processed Data Layer by deleting the data table and log"

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do not prompt for confirmation (unsafe in production!)",
        )

    def handle(self, *args, **options):
        keys = [s.strip() for s in options["keys"].split(",")]

        for key in keys:
            dls = Datalayer.objects.filter_by_key(key)

            if dls.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'No Data Layer were found for "{key}".')
                )
                return

            for dl in dls:
                if not dl.is_loaded():
                    self.stdout.write(
                        self.style.WARNING(
                            f"The Data Layer {dl.key} can't be reset, since it's not loaded."
                        )
                    )
                    continue

                # Confirm if no --noinput
                if not options["noinput"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"This will irreversibly delete processed data and the log for: {dl.key}"
                        )
                    )
                    confirm = input("Are you sure you want to continue? (yes/no): ")
                    if confirm.lower() != "yes":
                        self.stdout.write(self.style.ERROR("Reset cancelled."))
                        return

                dl.reset(data=True, log=True)

                self.stdout.write(self.style.SUCCESS(f"Successfully reset {dl.key}."))
