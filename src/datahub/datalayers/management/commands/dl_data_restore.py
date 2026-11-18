# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import pandas as pd

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Dump the processed data of Data Layers."

    def add_arguments(self, parser):
        parser.add_argument(
            "key",
            type=str,
            help="Comma separated list of Data Layer keys, you can use * as wildcard.",
        )

        parser.add_argument(
            "file",
            type=Path,
            help="Specify input filename",
        )

        parser.add_argument(
            "--format",
            choices=["plain", "custom"],
            default="custom",
            help='Specify the data format, choose either "plain" (SQL) or "custom" (pg_dump)',
        )

        parser.add_argument(
            "--save-db-if-exists",
            type=str,
            default="replace",
            choices=["replace", "append"],
            help="If database table already exists set to append.",
        )

    def handle(self, *args, **options):
        file: Path = options["file"]

        if not file.is_file():
            raise CommandError(f"File does not exist: {file}")

        dl: Datalayer = Datalayer.objects.get(key=options["key"])
        df = pd.read_csv(file)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        dl.get_class().df = df
        dl.get_class().save(db_if_exists=options["save_db_if_exists"])
