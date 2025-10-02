# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

from django.core.management.base import BaseCommand

from datalayers.models import Datalayer
from datalayers.utils import dumpdata


class Command(BaseCommand):
    help = "Serialize Data Layer metadata into JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )

        parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Specify a file to write the output to instead of the CLI",
        )

    def handle(self, *args, **options):
        output_file = options.get("output")

        keys = [s.strip() for s in options["keys"].split(",")]
        datalayers = []

        for key in keys:
            dls = Datalayer.objects.filter_by_key(key)
            for dl in dls:
                datalayers.append(dl)

        data = dumpdata(datalayers)

        if output_file:
            with Path.open(output_file, "w", encoding="utf-8") as f:
                f.write(data + "\n")
        else:
            self.stdout.write(data)
