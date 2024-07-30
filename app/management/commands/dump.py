import datetime as dt
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalayers.utils import get_conn_string


class Command(BaseCommand):
    help = "Dump complete database for backup/later restoration."

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            nargs="?",
            default=None,
            help="Specify the filename for the dump",
        )

    def handle(self, *args, **options):
        file = options["file"]
        if not file:
            file = f"{dt.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_datahub.dump"

        path = Path("data/") / file

        try:
            params = [
                "pg_dump",
                "-Fc",
                "-f",
                f"{path}",
                get_conn_string(sqlalchemy=False),
            ]

            # to capture stderr we need to set "stderr=subprocess.STDOUT", to
            # actually get a string and not a byte string (b'..') we need to set
            # encoding.
            subprocess.check_output(params, stderr=subprocess.STDOUT, encoding="UTF-8")

            self.stdout.write(self.style.SUCCESS(f"Dump written to file: {path}"))

        except subprocess.CalledProcessError as error:
            raise CommandError(error.output) from error
