import re
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify


def get_docs_root() -> Path:
    """Get the docs directory path."""
    return Path(settings.BASE_DIR) / "docs"


def clean_filename(filename):
    """Remove numeric prefixes like 00_, 10_, 20_ from filename."""
    name = filename.rsplit(".", 1)[0]
    cleaned = re.sub(r"^\d+_", "", name)
    return cleaned


@dataclass
class DocItem:
    name: str
    path: Path
    type: str
    url: str
    children: list["DocItem"] = field(default_factory=list)

    def is_dir(self) -> bool:
        return self.type == "folder"


def get_docs_structure():
    """Build the complete wiki navigation structure."""
    docs_root = get_docs_root()

    if not docs_root.exists():
        return {}

    def build_tree(path: Path, relative_path=""):
        """Recursively build the tree structure."""
        items = []

        # Get all items in current directory
        try:
            all_items = sorted(path.iterdir())
        except (OSError, PermissionError):
            return items

        for item in all_items:
            if item.name.startswith("."):
                continue

            item_relative_path = (
                f"{slugify(relative_path)}/{slugify(clean_filename(item.name))}".lstrip(
                    "/"
                )
            )

            if item.is_file() and item.suffix == ".md":
                clean_name = clean_filename(item.name)
                items.append(
                    DocItem(
                        name=clean_name,
                        path=item,
                        type="file",
                        url=f"{slugify(relative_path)}/{slugify(clean_name)}".lstrip(
                            "/"
                        ),
                    )
                )
            elif item.is_dir():
                clean_name = clean_filename(item.name)
                items.append(
                    DocItem(
                        name=clean_name,
                        path=item,
                        type="folder",
                        url=f"{relative_path}/{clean_name}",
                        children=build_tree(item, item_relative_path),
                    )
                )

        return items

    return build_tree(docs_root)


def get_flat_docs_structure(docs):
    flat_strcuture = {}

    for doc in docs:
        if doc["type"] == "file":
            flat_strcuture[doc["path"]] = doc
        elif doc["type"] == "folder":
            for doc2 in doc["children"]:
                flat_strcuture[doc2["path"]] = doc2

    return flat_strcuture


def extract_title_from_md(text, title):
    if text.startswith("#"):
        newline_index = text.find("\n")
        if newline_index != -1:
            title = text[1:newline_index].strip()
            text = text[newline_index + 1 :]
        else:
            title = text[1:].strip()
            text = ""  # No content after title

    return text, title
