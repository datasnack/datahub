import os
import sys
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Swap instance."

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            nargs="?",
            default=None,
            help="Specify the filename for the dump",
        )

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        src_link = base_dir / "src"
        data_link = base_dir / "data"
        env_link = base_dir / ".env"

        # Find all alternative symlinks like src.prod1, data.prod1, etc.
        alt_src_links = [
            f
            for f in base_dir.iterdir()
            if f.name.startswith("src.") and f.name != "src"
        ]
        alt_data_links = [
            f
            for f in base_dir.iterdir()
            if f.name.startswith("data.") and f.name != "data"
        ]
        alt_env_links = [
            f
            for f in base_dir.iterdir()
            if f.name.startswith(".env.") and f.name != ".env"
        ]

        if not alt_src_links or not alt_data_links or not alt_env_links:
            self.stdout.write(self.style.ERROR("No alternative versions found."))
            sys.exit(1)

        # Extract version names from symlinks (e.g., 'prod1' from 'src.prod1')
        versions = (
            {src.name.split(".")[1] for src in alt_src_links}
            & {data.name.split(".")[1] for data in alt_data_links}
            & {env.name.split(".")[2] for env in alt_env_links}
        )

        if not versions:
            self.stdout.write(
                self.style.ERROR("No matching versions for src and data found.")
            )
            sys.exit(1)

        # Current
        self.stdout.write(self.style.SUCCESS("Current:"))
        src_target = "local"
        if src_link.is_symlink():
            src_target = f"-> {src_link.resolve()}"
        self.stdout.write(f"src {src_target}")
        self.stdout.write("\n")

        # List available versions
        self.stdout.write(self.style.SUCCESS("Available versions:"))
        for i, version in enumerate(versions, 1):
            self.stdout.write(f"{i}. {version}")

        # Ask the user to select a version
        try:
            choice = input("Select a version (enter the number): ")
        except KeyboardInterrupt:
            sys.exit(0)

        try:
            choice = int(choice)
            if choice < 1 or choice > len(versions):
                raise ValueError
            selected_version = list(versions)[choice - 1]
        except (ValueError, IndexError):
            self.stdout.write(self.style.ERROR("Invalid choice. Exiting."))
            sys.exit(1)

        self.stdout.write(f"Swapping to version: {selected_version}")

        # Backup current symlinks by renaming them
        current_src_link = src_link.with_name(f"src.{src_link.resolve().parent.name}")
        current_data_link = data_link.with_name(
            f"data.{data_link.resolve().parent.name}"
        )
        current_env_link = env_link.with_name(f".env.{env_link.resolve().parent.name}")
        src_link.rename(current_src_link)
        data_link.rename(current_data_link)
        env_link.rename(current_env_link)

        # Replace the symlinks with the selected version
        new_src_link = base_dir / f"src.{selected_version}"
        new_data_link = base_dir / f"data.{selected_version}"
        new_env_link = base_dir / f".env.{selected_version}"

        new_src_link.rename("src")
        new_data_link.rename("data")
        new_env_link.rename(".env")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully swapped to version {selected_version}")
        )

        call_command("clearcache")
