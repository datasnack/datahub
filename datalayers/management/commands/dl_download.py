from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Download given Data Layers"

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )

    def handle(self, *args, **options):
        keys = [s.strip() for s in options["keys"].split(",")]

        for key in keys:
            dls = Datalayer.objects.filter(key__iregex=key)

            if dls.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'No Data Layer were found for "{key}".')
                )
                return

            for dl in dls:
                try:
                    dl.download()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Data Layer "{dl.key}" has been downloaded.'
                        )
                    )

                except NotImplementedError:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Data Layer "{dl.key}" has no defined download() method.'
                        )
                    )
