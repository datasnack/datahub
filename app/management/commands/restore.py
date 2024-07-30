import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalayers.utils import get_conn_string


class Command(BaseCommand):
    help = "Restore database from a previous dump."

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        file = Path(options["file"])

        if not file.exists():
            raise CommandError("Given file does not exist.")

        confirmation = input(
            "This will overwrite all previous data. Do you want to continue? (yes/no):"
        )
        if confirmation.lower() != "yes":
            self.stdout.write("Operation aborted, no data was changed.")
            return

        # --clean:     drop all tables, before creating them
        # --if-exists: prevent DROP table -> table does not exist warnings during
        #              import in a empty database
        try:
            params = [
                "pg_restore",
                "--clean",
                "--if-exists",
                "-d",
                get_conn_string(sqlalchemy=False),
                file,
            ]

            # to capture stderr we need to set "stderr=subprocess.STDOUT", to
            # actually get a string and not a byte string (b'..') we need to set
            # encoding.
            subprocess.check_output(params, stderr=subprocess.STDOUT, encoding="UTF-8")
        except subprocess.CalledProcessError as error:
            raise CommandError(error.output) from error
