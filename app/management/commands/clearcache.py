# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django.core.cache import caches
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clears the cache. Provide a key to clear a specific cache key or leave blank to clear all."

    def add_arguments(self, parser):
        parser.add_argument(
            "key",
            nargs="?",
            type=str,
            help="Specific cache key to clear (optional). If not provided, clears all cache.",
        )

    def handle(self, *args, **options):
        key = options["key"]

        if key:
            if key in caches:
                caches[key].clear()
                self.stdout.write(self.style.SUCCESS(f"Cache '{key}' cleared."))
            else:
                self.stdout.write(self.style.WARNING(f"Cache '{key}' does not exist."))
        else:
            for key in caches:
                caches[key].clear()
                self.stdout.write(self.style.SUCCESS(f"Cache '{key}' cleared."))
