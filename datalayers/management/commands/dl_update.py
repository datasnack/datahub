from django.core.management.base import BaseCommand, CommandError

from datalayers.models import Category, Datalayer


class Command(BaseCommand):
    help = "Update attribute of the given Data Layers"

    def add_arguments(self, parser):
        parser.add_argument(
            "keys",
            type=str,
            help="Comma separated list of datalayer keys, you can use * as wildcard.",
        )
        parser.add_argument(
            "--attr",
            type=str,
            required=True,
            help="The attribute to update",
        )
        parser.add_argument(
            "--value",
            type=str,
            required=True,
            help="The value for the attribute",
        )

    def _boolean_input(self, question, default=None) -> bool:
        """Taken from Django core: https://github.com/django/django/blob/59afe61a970dd60df388e7cda9041ef3c0e770cb/django/db/migrations/questioner.py#L87."""
        result = input(f"{question} ")
        if not result and default is not None:
            return default
        while len(result) < 1 or result[0].lower() not in "yn":
            result = input("Please answer yes or no: ")
        return result[0].lower() == "y"

    def handle(self, *args, **options):
        keys = [s.strip() for s in options["keys"].split(",")]

        for key in keys:
            dls = Datalayer.objects.filter(key__iregex=key)

        if dls.count() == 0:
            self.stdout.write(
                self.style.WARNING(f'No Data Layer were found for "{key}".')
            )
            return

        # category update depends on a relation to the category model, so we handle
        # that separately.
        if options["attr"] == "category":
            try:
                category = Category.objects.get(key=options["value"])
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Category with key "{options["value"]}" does not exist.'
                    )
                )

                if not self._boolean_input("Do you want to create the category?"):
                    return

                category = Category.objects.create(
                    key=options["value"], name=options["value"]
                )
                category.save()

            for dl in dls:
                dl.category = category
                dl.save()
                self.stdout.write(self.style.SUCCESS(f'Data Layer "{dl.key}" updated.'))
            return

        # After category updates are out of the way we only have "normal" attributes
        if not hasattr(Datalayer, options["attr"]):
            self.stdout.write(
                self.style.WARNING(f'Data Layer has no attribute "{options["attr"]}".')
            )

            return

        for dl in dls:
            if hasattr(dl, options["attr"]):
                setattr(dl, options["attr"], options["value"])
                dl.save()
                self.stdout.write(self.style.SUCCESS(f'Data Layer "{dl.key}" updated.'))
