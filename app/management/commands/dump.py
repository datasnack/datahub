import datetime as dt
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from datalayers.utils import get_conn_string


class Command(BaseCommand):
    help = "Dump complete database for backup/later restoration."

    user_data_tables = (
        "app_user",
        "app_user_groups",
        "app_user_user_permissions",
        "auth_group",
        "auth_group_permissions",
        "django_admin_log",
    )  # tuple for immutable

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            nargs="?",
            default=None,
            help="Specify the filename for the dump",
        )

        parser.add_argument(
            "--exclude-user-data",
            action="store_true",
            help="Exclude data of user tables (but keep table definition), useful for export to new instances.",
        )

        parser.add_argument(
            "--exclude-user-tables",
            action="store_true",
            help="Exclude user data table definition, only suitable for updates of other existing instances, since table definitions are missing.",
        )

        parser.add_argument(
            "--format",
            choices=["plain", "custom"],
            default="custom",
            help='Specify the data format, choose either "plain" or "custom"',
        )

    def handle(self, *args, **options):
        file = options["file"]
        output_format = options["format"]
        extension = "dump"
        if output_format == "plain":
            extension = "sql"

        if not file:
            file = f"{dt.datetime.now(dt.UTC).strftime('%Y-%m-%d_%H-%M-%S')}_datahub.{extension}"

        path = Path("data/") / file

        try:
            params = [
                "pg_dump",
                f"-F{output_format}",
                "-f",
                f"{path}",
                get_conn_string(sqlalchemy=False),
            ]

            # active sessions should never be dumped
            params.append("--exclude-table-data")
            params.append("django_session")

            if options["exclude_user_data"]:
                for table in self.user_data_tables:
                    params.append("--exclude-table-data")
                    params.append(table)

            if options["exclude_user_tables"]:
                for table in self.user_data_tables:
                    params.append("--exclude-table")
                    params.append(table)

                # Those need to to be excluded when tables are ignored, but need to be
                # present during export with exclude_user_data. They contain no user data
                # but content type information. If they would also be missing during
                # exclude_user_tables foreign key constraints would break.
                # That's the reason why they are added here manually and are not part of
                # this.user_data_tables.
                params.append("--exclude-table")
                params.append("auth_permission")
                params.append("--exclude-table")
                params.append("django_content_type")

            # to capture stderr we need to set "stderr=subprocess.STDOUT", to
            # actually get a string and not a byte string (b'..') we need to set
            # encoding.
            subprocess.check_output(params, stderr=subprocess.STDOUT, encoding="UTF-8")

            self.stdout.write(self.style.SUCCESS(f"Dump written to file: {path}"))

        except subprocess.CalledProcessError as error:
            raise CommandError(error.output) from error
