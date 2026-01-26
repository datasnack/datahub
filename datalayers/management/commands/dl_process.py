# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

from django.core.management.base import BaseCommand

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
            "--output",
            type=str,
            default="db",
            help="Output target, 'db' for database or path to file (CSV).",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="If set, no data will be saved to the database.",
        )

        parser.add_argument(
            "--save-db-if-exists",
            type=str,
            default="replace",
            choices=["replace", "append"],
            help="If database table already exists set to append.",
        )

        parser.add_argument(
            "--shape-type",
            type=str,
            required=False,
            help="Optional shape type to filter or control processing.",
        )

    def handle(self, *args, **options):
        keys = [s.strip() for s in options["keys"].split(",")]

        if options["shape_type"]:
            shapes = Shape.objects.filter(type__key=options["shape_type"])
        else:
            shapes = Shape.objects.all()

        # wen can use len(shapes) here, since we iterate over the result anyways.
        # using shapes.count() would lead to an extra query `COUNT * ...`
        if len(shapes) == 0:
            self.stdout.write(self.style.WARNING("No shapes found for processing."))
            return

        for key in keys:
            dls = Datalayer.objects.filter_by_key(key)

            if dls.count() == 0:
                self.stdout.write(
                    self.style.WARNING(f'No Data Layer were found for "{key}".')
                )
                return

            for dl in dls:
                try:
                    self.stdout.write(f'Starting processing Data Layer "{dl.key}"...')

                    dl.process(shapes)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Data Layer "{dl.key}" has been processed ({dl.get_class().len_values()} values).'
                        )
                    )

                    if not options["dry_run"]:
                        self.stdout.write(f'Saving processed data for "{dl.key}"...')

                        if options["output"] == "db":
                            dl.get_class().save(
                                db_if_exists=options["save_db_if_exists"]
                            )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Data Layer "{dl.key}" has been saved to database.'
                                )
                            )
                        else:
                            dl.get_class().output = "fs"
                            dl.get_class().save(fs_path=Path(options["output"]))

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Data Layer "{dl.key}" has been saved to filesystem.'
                                )
                            )

                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                'The "--dry-run" option was set, nothing was saved!'
                            )
                        )

                except NotImplementedError:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Data Layer "{dl.key}" has no defined process() method.'
                        )
                    )
