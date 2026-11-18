# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Add a new Django app to the Data Hub for customization."

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)

    def handle(self, *args, **options):
        dest = Path(f"./src/{options['name']}")

        if dest.exists():
            raise CommandError(f"Target directory for app already exists: {dest}")

        # Create app in new folder
        dest.mkdir(parents=True, exist_ok=True)
        call_command("startapp", options["name"], dest)

        # update name with sub folder prefix
        apps_file = dest / "apps.py"
        apps_content = apps_file.read_text()
        apps_content = apps_content.replace(
            f"name = '{options['name']}'", f'name = "src.{options['name']}"'
        )
        apps_file.write_text(apps_content)

        # remind to update .env file
        self.stdout.write(
            "To use the app, add it to the INSTALLED_USER_APPS env variable."
        )
