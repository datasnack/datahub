import os
import sys
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Swap between different environment configurations using symlinks."

    # Hardcoded lists for symlinked items
    SYMLINKED_FOLDERS = ["src", "data", "docs"]
    SYMLINKED_FILES = [".env"]

    # Version names to ignore
    IGNORED_VERSIONS = {"example"}

    def max_length_symlink_names(self) -> int:
        return max(len(s) for s in self.SYMLINKED_FOLDERS + self.SYMLINKED_FILES)

    def get_alternative_links(self, base_dir, item_name):
        """Find all alternative symlinks for a given item (e.g., src.prod1, src.dev, etc.)."""
        if item_name.startswith("."):
            # For hidden files like .env, look for patterns like .env.prod1
            pattern_prefix = item_name + "."
            return [
                f
                for f in base_dir.iterdir()
                if f.name.startswith(pattern_prefix) and f.name != item_name
            ]
        else:
            # For regular files/folders, look for patterns like src.prod1
            pattern_prefix = item_name + "."
            return [
                f
                for f in base_dir.iterdir()
                if f.name.startswith(pattern_prefix) and f.name != item_name
            ]

    def extract_version_from_name(self, name, base_name):
        """Extract version name from symlink name (e.g., 'prod1' from 'src.prod1')."""
        if base_name.startswith("."):
            parts = name.split(".")
            return parts[2] if len(parts) >= 3 else None

        parts = name.split(".")
        return parts[1] if len(parts) >= 2 else None

    def get_current_target(self, link_path):
        """Get the current target of a symlink or indicate if it's local."""
        if link_path.is_symlink():
            return link_path.resolve()
        return "local"

    def find_available_versions(self, base_dir):
        """Find all versions available across all configured items."""
        all_versions = set()

        # Collect versions from all symlinked items
        for folder in self.SYMLINKED_FOLDERS:
            alt_links = self.get_alternative_links(base_dir, folder)
            folder_versions = {
                self.extract_version_from_name(link.name, folder) for link in alt_links
            }
            folder_versions.discard(None)  # Remove any None values
            folder_versions -= self.IGNORED_VERSIONS  # Remove ignored versions
            all_versions.update(folder_versions)  # Union instead of intersection

        for file in self.SYMLINKED_FILES:
            alt_links = self.get_alternative_links(base_dir, file)
            file_versions = {
                self.extract_version_from_name(link.name, file) for link in alt_links
            }
            file_versions.discard(None)  # Remove any None values
            file_versions -= self.IGNORED_VERSIONS  # Remove ignored versions
            all_versions.update(file_versions)  # Union instead of intersection

        return all_versions

    def display_current_status(self, base_dir):
        """Display current symlink targets."""
        self.stdout.write(self.style.SUCCESS("Current:"))
        width = self.max_length_symlink_names()

        for folder in self.SYMLINKED_FOLDERS:
            folder_link = base_dir / folder
            target = (
                self.get_current_target(folder_link) if folder_link.exists() else "-"
            )
            self.stdout.write(f"{folder: <{width}} -> {target}")

        for file in self.SYMLINKED_FILES:
            file_link = base_dir / file
            target = self.get_current_target(file_link) if file_link.exists() else "-"
            self.stdout.write(f"{file: <{width}} -> {target}")

        self.stdout.write("\n")

    def backup_current_links(self, base_dir, backup_suffix):
        """Backup current symlinks by renaming them."""
        backed_up_items = []

        try:
            for folder in self.SYMLINKED_FOLDERS:
                folder_link = base_dir / folder
                if folder_link.exists():
                    backup_name = f"{folder}.{backup_suffix}"
                    backup_path = base_dir / backup_name
                    folder_link.rename(backup_path)
                    backed_up_items.append((folder_link, backup_path))
                    self.stdout.write(f"  Backed up {folder} as {backup_name}")

            for file in self.SYMLINKED_FILES:
                file_link = base_dir / file
                if file_link.exists():
                    backup_name = f"{file}.{backup_suffix}"
                    backup_path = base_dir / backup_name
                    file_link.rename(backup_path)
                    backed_up_items.append((file_link, backup_path))
                    self.stdout.write(f"  Backed up {file} as {backup_name}")

            return backed_up_items

        except Exception as e:
            # Rollback any successful backups
            for original_path, backup_path in backed_up_items:
                try:
                    backup_path.rename(original_path)
                except Exception:
                    pass
            raise CommandError(f"Failed to backup current links: {e}")

    def swap_to_version(self, base_dir, selected_version):
        """Swap symlinks to the selected version."""
        swapped_items = []

        try:
            for folder in self.SYMLINKED_FOLDERS:
                versioned_link = base_dir / f"{folder}.{selected_version}"
                target_link = base_dir / folder

                # Only swap if the versioned link exists
                if versioned_link.exists():
                    versioned_link.rename(target_link)
                    swapped_items.append((target_link, versioned_link))
                    self.stdout.write(
                        f"  Swapped {folder} to version {selected_version}"
                    )
                else:
                    self.stdout.write(
                        f"  Skipped {folder} (version {selected_version} not available)"
                    )

            for file in self.SYMLINKED_FILES:
                versioned_link = base_dir / f"{file}.{selected_version}"
                target_link = base_dir / file

                # Only swap if the versioned link exists
                if versioned_link.exists():
                    versioned_link.rename(target_link)
                    swapped_items.append((target_link, versioned_link))
                    self.stdout.write(f"  Swapped {file} to version {selected_version}")
                else:
                    self.stdout.write(
                        f"  Skipped {file} (version {selected_version} not available)"
                    )

        except Exception as e:
            # Rollback any successful swaps
            for target_path, versioned_path in swapped_items:
                try:
                    target_path.rename(versioned_path)
                except Exception:
                    pass
            raise CommandError(f"Failed to swap to version {selected_version}: {e}")

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR

        # Find available versions
        versions = self.find_available_versions(base_dir)

        if not versions:
            self.stdout.write(
                self.style.ERROR("No matching versions found for all configured items.")
            )
            sys.exit(1)

        # Display current status
        self.display_current_status(base_dir)

        # List available versions
        self.stdout.write(self.style.SUCCESS("Available versions:"))
        version_list = sorted(list(versions))
        for i, version in enumerate(version_list, 1):
            self.stdout.write(f"{i}. {version}")

        # Ask the user to select a version
        try:
            choice = input("Select a version (enter the number): ")
        except KeyboardInterrupt:
            sys.exit(0)

        try:
            choice = int(choice)
            if choice < 1 or choice > len(version_list):
                raise ValueError
            selected_version = version_list[choice - 1]
        except (ValueError, IndexError):
            self.stdout.write(self.style.ERROR("Invalid choice. Exiting."))
            sys.exit(1)

        self.stdout.write(f"Swapping to version: {selected_version}")

        # Determine backup suffix (current version or 'current' if local)
        current_link = (
            base_dir / self.SYMLINKED_FOLDERS[0]
        )  # Use first folder as reference
        if current_link.is_symlink():
            backup_suffix = current_link.resolve().parent.name
        else:
            backup_suffix = "current"

        # Backup current symlinks
        try:
            self.backup_current_links(base_dir, backup_suffix)
        except CommandError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            sys.exit(1)

        # Swap to selected version
        try:
            self.swap_to_version(base_dir, selected_version)
        except CommandError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            sys.exit(1)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully swapped to version {selected_version}")
        )

        call_command("clearcache")
