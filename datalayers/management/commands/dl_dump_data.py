# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django.core.management import call_command
from django.core.management.base import BaseCommand

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Dump the processed data of Data Layers."

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of Data Layer keys, you can use * as wildcard.",
        )

        parser.add_argument(
            "--format",
            choices=["plain", "custom"],
            default="custom",
            help='Specify the data format, choose either "plain" (SQL) or "custom" (pg_dump)',
        )

        parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Specify the filename for the dump",
        )

    def handle(self, *args, **options):
        file = options.get("file")
        output_format = options["format"]

        keys = [s.strip() for s in options["keys"].split(",")]
        tables = []

        for key in keys:
            dls = Datalayer.objects.filter_by_key(key)
            for dl in dls:
                if not dl.is_loaded():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Data Layer {dl.key} is not loaded and will not be included in the dump."
                        )
                    )

                tables.append(dl.key)

        if len(tables) == 0:
            self.stdout.write(
                self.style.ERROR("No Data Layers are matching the filter.")
            )
            return

        call_command("dump", tables=tables, file=file, format=output_format)
