from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer
from shapes.models import Shape


class Command(BaseCommand):
    help = "Process given Data Layers"

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="If set, no data will be saved to the database.",
        )

    def handle(self, *args, **options):
        keys = [s.strip() for s in options["keys"].split(",")]

        shapes = Shape.objects.all()

        for key in keys:
            dls = Datalayer.objects.filter(key__iregex=key)

            if dls.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'No Data Layer were found for "{key}".')
                )
                return

            for dl in dls:
                try:
                    dl.process(shapes)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Data Layer "{dl.key}" has been processed ({dl.get_class().len_values()} values).'
                        )
                    )

                    if not options["dry_run"]:
                        dl.get_class().save()
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                'The "--dry-run" option was set, nothing was saved to the database!'
                            )
                        )

                except NotImplementedError:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Data Layer "{dl.key}" has no defined process() method.'
                        )
                    )
