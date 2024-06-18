from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Datalayer


class Command(BaseCommand):
    help = "Load given shapefile structure into the database"

    def add_arguments(self, parser):
        parser.add_argument("key", type=str)
        parser.add_argument("action", type=str)

    def handle(self, *args, **options):
        dl = Datalayer.objects.get(key=options["key"])

        match options["action"]:
            case "download":
                try:
                    dl.download()
                except NotImplementedError as e:
                    raise CommandError(
                        "This Data Layer has no defined download() method."
                    ) from e
            case "process":
                try:
                    dl.process()
                except NotImplementedError as e:
                    raise CommandError(
                        "This Data Layer has no defined process() method."
                    ) from e
            case _:
                raise CommandError(
                    'Unknown action "%s" to perform on Data Layer' % options["action"]
                )
