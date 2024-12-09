import datetime as dt
import subprocess
from pathlib import Path

from taggit.models import TaggedItem

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer
from datalayers.utils import dumpdata


class Command(BaseCommand):
    help = "Dump complete database for backup/later restoration."

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )

        parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Specify a file to write the output to instead of the CLI",
        )

    def handle(self, *args, **options):
        output_file = options.get("output")

        keys = [s.strip() for s in options["keys"].split(",")]
        datalayers = []

        for key in keys:
            dls = Datalayer.objects.filter(key__iregex=key)
            for dl in dls:
                datalayers.append(dl)

        data = dumpdata(datalayers)

        if output_file:
            with Path.open(output_file, "w", encoding="utf-8") as f:
                f.write(data + "\n")
        else:
            self.stdout.write(data)
