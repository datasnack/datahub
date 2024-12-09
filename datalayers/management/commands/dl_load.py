from pathlib import Path

from django.contrib import messages
from django.core.management.base import BaseCommand, CommandError

from datalayers.utils import loaddata


class Command(BaseCommand):
    help = "Dump complete database for backup/later restoration."

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        file = Path(options["file"])

        msgs = loaddata(file.read_text())

        # the outsourcing in a another functions sucks here, because we can not
        # interact with messages individually, like ask the user for input. but it is how it is...
        for msg in msgs:
            match msg["level"]:
                case messages.ERROR:
                    self.stdout.write(self.style.ERROR(msg["message"]))
                case messages.WARNING:
                    self.stdout.write(self.style.WARNING(msg["message"]))
                case messages.SUCCESS:
                    self.stdout.write(self.style.SUCCESS(msg["message"]))
                case _:
                    self.stdout.write(msg["message"])
