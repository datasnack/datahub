# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import csv
from pathlib import Path

from psycopg import sql

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from datalayers.models import Datalayer, camel


class Command(BaseCommand):
    help = "Rename key of a Data Layer, or bulk-rename from a CSV file"

    def add_arguments(self, parser):
        # Make positional args optional so --csv can be used instead
        parser.add_argument("old_key", nargs="?", type=str)
        parser.add_argument("new_key", nargs="?", type=str)
        parser.add_argument(
            "--csv",
            dest="csv_file",
            type=str,
            help="Path to a CSV file with columns old_key and new_key",
        )
        parser.add_argument(
            "--separator",
            dest="separator",
            default=",",
            help="CSV column separator (default: ',', common alternative: ';')",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and print planned operations without executing them",
        )

        # --- Granular operation flags ---
        # When none are given all four default to True (full rename).
        # Specifying any subset restricts execution to only those operations.
        parser.add_argument(
            "--rename-model",
            action="store_true",
            default=False,
            help="Rename the key in the datalayer table",
        )
        parser.add_argument(
            "--rename-db",
            action="store_true",
            default=False,
            help="Rename the PostgreSQL data table (ALTER TABLE)",
        )
        parser.add_argument(
            "--rename-class",
            action="store_true",
            default=False,
            help="Rename the class file and class name inside the source file",
        )
        parser.add_argument(
            "--rename-data",
            action="store_true",
            default=False,
            help="Rename the data storage folder(s)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # If no operation flag is explicitly set, default to running all four.
        ops = {
            "model": options["rename_model"],
            "db": options["rename_db"],
            "class": options["rename_class"],
            "data": options["rename_data"],
        }
        if not any(ops.values()):
            ops = {k: True for k in ops}

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry-run mode — no changes will be made.\n")
            )

        active_ops = [k for k, v in ops.items() if v]
        self.stdout.write(f"Active operations: {', '.join(active_ops)}\n")

        # --- Build the list of (old_key, new_key) pairs ---
        if options["csv_file"]:
            pairs = self._load_csv(options["csv_file"], options["separator"])
        elif options["old_key"] and options["new_key"]:
            pairs = [(options["old_key"], options["new_key"])]
        else:
            raise CommandError(
                "Provide either old_key and new_key arguments, or --csv <file>"
            )

        # --- Pre-flight: validate every pair before touching anything ---
        self.stdout.write(f"Validating {len(pairs)} rename(s)...")
        errors = []
        seen_old = {}
        seen_new = {}

        for i, (old_key, new_key) in enumerate(pairs, start=1):
            row_errors = self._validate_rename(old_key, new_key, ops)

            # Catch duplicates within the CSV itself
            if old_key in seen_old:
                row_errors.append(
                    f'old_key "{old_key}" appears in row {seen_old[old_key]} and row {i}'
                )
            else:
                seen_old[old_key] = i

            if new_key in seen_new:
                row_errors.append(
                    f'new_key "{new_key}" appears in row {seen_new[new_key]} and row {i}'
                )
            else:
                seen_new[new_key] = i

            for msg in row_errors:
                errors.append(f"  Row {i} ({old_key} → {new_key}): {msg}")

        if errors:
            error_list = "\n".join(errors)
            raise CommandError(
                f"Validation failed — no changes were made:\n\n{error_list}"
            )

        self.stdout.write(self.style.SUCCESS("All renames validated successfully.\n"))

        if dry_run:
            for old_key, new_key in pairs:
                self.stdout.write(f"  Would rename: {old_key} → {new_key}")
            return

        # --- Execute all renames ---
        for i, (old_key, new_key) in enumerate(pairs, start=1):
            self.stdout.write(f"[{i}/{len(pairs)}] Renaming {old_key} → {new_key}")
            self._rename_one(old_key, new_key, ops)
            self.stdout.write("")  # blank line between renames

        self.stdout.write(
            self.style.SUCCESS(f"Done. {len(pairs)} rename(s) completed.")
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_csv(self, filepath: str, separator: str) -> list[tuple[str, str]]:
        """Parse a CSV file and return a list of (old_key, new_key) tuples."""
        path = Path(filepath)
        if not path.exists():
            raise CommandError(f'CSV file not found: "{filepath}"')

        pairs = []
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter=separator)

            if reader.fieldnames is None:
                raise CommandError("CSV file appears to be empty")

            missing = {"old_key", "new_key"} - set(reader.fieldnames)
            if missing:
                raise CommandError(
                    f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                    f"Found columns: {', '.join(reader.fieldnames)}"
                )

            for lineno, row in enumerate(reader, start=2):  # start=2: header is line 1
                old_key = row["old_key"].strip()
                new_key = row["new_key"].strip()
                if not old_key or not new_key:
                    raise CommandError(
                        f"CSV line {lineno}: old_key and new_key must not be empty"
                    )
                if old_key != new_key:
                    pairs.append((old_key, new_key))

        if not pairs:
            raise CommandError("CSV file contains no data rows")

        return pairs

    def _validate_rename(
        self, old_key: str, new_key: str, ops: dict[str, bool]
    ) -> list[str]:
        """
        Return a list of error strings for this rename pair.

        Only validates what the active operations will actually touch.
        An empty list means the pair is valid.
        """
        errors = []

        if ops["model"]:
            if not Datalayer.objects.filter(key=old_key).exists():
                errors.append(f'origin Data Layer "{old_key}" does not exist')
            if Datalayer.objects.filter(key=new_key).exists():
                errors.append(f'target Data Layer "{new_key}" already exists')

        if ops["db"]:
            if old_key not in connection.introspection.table_names():
                # Not an error — table may simply not be loaded yet; handled at runtime.
                pass

        if ops["class"]:
            new_class = Path(f"src/datalayer/{new_key}.py")
            if new_class.exists():
                errors.append(f'class file "{new_class.as_posix()}" already exists')

        if ops["data"]:
            for base in ("./data/datalayers", "./data/datalayers.local"):
                new_data = Path(f"{base}/{new_key}/")
                if new_data.exists():
                    errors.append(
                        f'new data directory "{new_data.as_posix()}" already exists'
                    )

        return errors

    def _rename_one(self, old_key: str, new_key: str, ops: dict[str, bool]) -> None:
        """Execute a single rename. Assumes _validate_rename passed."""
        # 1. Rename key in datalayer table
        if ops["model"]:
            dl = Datalayer.objects.get(key=old_key)
            dl.key = new_key
            dl.save()
            self.stdout.write(self.style.SUCCESS("  Renamed Data Layer key"))

        # 2. Rename PostgreSQL data table
        if ops["db"]:
            if old_key in connection.introspection.table_names():
                query = sql.SQL("ALTER TABLE {old} RENAME TO {new}").format(
                    old=sql.Identifier(old_key), new=sql.Identifier(new_key)
                )
                with connection.cursor() as c:
                    c.execute(query)
                self.stdout.write(self.style.SUCCESS("  Renamed database table"))
            else:
                self.stdout.write("  Data Layer not loaded — no table to rename")

            # Fetch the (possibly just-renamed) model instance for the vector table check
            dl = Datalayer.objects.get(key=new_key if ops["model"] else old_key)
            if dl.has_class() and dl._get_class().raw_vector_data_table:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Vector data table "{dl._get_class().raw_vector_data_table}" '
                        f"must be renamed/updated manually"
                    )
                )

        # 3. Rename class file and class name inside the file
        if ops["class"]:
            class_path = Path(f"src/datalayer/{old_key}.py")
            if class_path.exists():
                class_path = class_path.rename(f"src/datalayer/{new_key}.py")
                self.stdout.write(self.style.SUCCESS("  Renamed class file"))

                old_camel = camel(old_key)
                new_camel = camel(new_key)
                class_source = class_path.read_text()
                class_path.write_text(class_source.replace(old_camel, new_camel))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Renamed class name: {old_camel} → {new_camel}"
                    )
                )
            else:
                self.stdout.write("  No class file to rename")

        # 4. Rename data storage folders
        if ops["data"]:
            for base in ("./data/datalayers", "./data/datalayers.local"):
                old_data_path = Path(f"{base}/{old_key}/")
                if old_data_path.exists():
                    old_data_path.rename(f"{base}/{new_key}/")
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Renamed data directory: {base}/{new_key}/"
                        )
                    )
                else:
                    self.stdout.write(
                        f"  No data directory to rename: {base}/{old_key}/"
                    )
