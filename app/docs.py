# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

import mistune
import yaml

from django.conf import settings
from django.template import RequestContext, Template
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import get_language

from app.utils.mistune import DjangoTemplateRenderer


def get_docs_root() -> Path:
    """Get the docs directory path."""
    return Path(settings.BASE_DIR) / "docs"


def clean_filename(filename: str) -> str:
    """Remove numeric prefixes like 00_, 10_, 20_ from filename, remove optional language suffix (.de.md)."""
    name = filename.rsplit(".", 1)[0]
    cleaned = re.sub(r"^\d+_", "", name)
    cleaned = re.sub(r"\.[a-z]{2}$", "", cleaned)

    return cleaned


def clean_path(path: str) -> str:
    path = path.removeprefix("./")
    path = unquote(path)

    parts = path.split("/")
    cleaned = ""

    # folders
    for i in range(len(parts) - 1):
        cleaned += slugify(parts[i]) + "/"

    # filenames
    cleaned += slugify(clean_filename(parts[-1]))

    return cleaned


def get_language_code(filename: str) -> str:
    """Read the language code from the filename, if non is present return 'en' (default)."""
    m = re.search(r"\.([a-z]{2})\.md$", filename)
    if m:
        return m[1]

    return "en"


@dataclass
class DocItem:
    name: str
    path: Path
    type: str
    url: str
    name_locale: str = field(default_factory=str)
    children: list["DocItem"] = field(default_factory=list)
    translations: dict[str, "DocItem"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        return self.type == "folder"

    def localized_name(self) -> str:
        language_code = get_language()
        if language_code == "en":
            return self.name

        if language_code not in self.translations:
            return self.name

        return self.translations[language_code].name


def get_docs_structure() -> list[DocItem]:
    """
    Build the complete docs navigation structure.

    The functions enumerated all markdown files below the ./docs/ directory.
    """
    docs_root = get_docs_root()

    if not docs_root.exists():
        return []

    def build_tree(path: Path, relative_path="") -> list[DocItem]:
        """Recursively build the tree structure."""
        items = []

        _translations = {}

        # Get all items in current directory
        try:
            all_items = sorted(path.iterdir())
        except (OSError, PermissionError):
            return items

        for item in all_items:
            if item.name.startswith("."):
                continue

            if relative_path == "" and item.name.lower().startswith("home."):
                continue

            item_relative_path = (
                f"{slugify(relative_path)}/{slugify(clean_filename(item.name))}".lstrip(
                    "/"
                )
            )

            if item.is_file() and item.suffix == ".md":
                language_code = get_language_code(item.name)
                clean_name = clean_filename(item.name)

                docitem = DocItem(
                    name=clean_name,
                    path=item,
                    type="file",
                    url=f"{slugify(relative_path)}/{slugify(clean_name)}".lstrip("/"),
                )

                if language_code != "en":
                    attributes = extract_front_matter(docitem.path.read_text())

                    if "title" in attributes:
                        docitem.name = attributes["title"]

                    if clean_name in _translations:
                        _translations[clean_name][language_code] = docitem
                    else:
                        _translations[clean_name] = {language_code: docitem}
                else:
                    if clean_name in _translations:
                        docitem.translations = _translations[clean_name]

                    items.append(docitem)
            elif item.is_dir():
                clean_name = clean_filename(item.name)

                folder_item = DocItem(
                    name=clean_name,
                    path=item,
                    type="folder",
                    url=f"{relative_path}/{clean_name}",
                    children=build_tree(item, item_relative_path),
                )

                # don't add folders without .md files
                if len(folder_item.children) > 0:
                    items.append(folder_item)

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


def extract_front_matter(text):
    """
    Extract YAML front matter from a string.

    Args:
        text (str): The input string containing potential front matter

    Returns:
        dict: Dictionary containing the front matter attributes,
              empty dict if no front matter found
    """
    # Pattern to match YAML front matter between --- or -- delimiters
    pattern = r"^-{2,3}\s*\n(.*?)\n-{2,3}\s*\n"

    match = re.search(pattern, text, re.DOTALL | re.MULTILINE)

    if match:
        yaml_content = match.group(1)
        try:
            front_matter = yaml.safe_load(yaml_content)
            return front_matter if front_matter is not None else {}
        except yaml.YAMLError:
            return {}

    return {}


def extract_title_from_md(text, title):
    pattern = r"^-{2,3}\s*\n(.*?)\n-{2,3}\s*\n"
    text = re.sub(pattern, "", text, flags=re.DOTALL | re.MULTILINE)

    if text.startswith("#"):
        newline_index = text.find("\n")
        if newline_index != -1:
            title = text[1:newline_index].strip()
            text = text[newline_index + 1 :]
        else:
            title = text[1:].strip()
            text = ""  # No content after title

    return text, title


def render_dj_md_to_html(request, text):
    # we first parse the markdown snippet through Django template.
    # i.e. a {% url "..." %} inside a href="..." would get escaped by mistune
    # and then the Django template would fail.
    template = Template(text)
    context = RequestContext(request, None)
    rendered = template.render(context)

    markdown = mistune.create_markdown(
        renderer=DjangoTemplateRenderer(escape=False),
        escape=False,
        plugins=[
            "strikethrough",
            "footnotes",
            "table",
            "speedup",
        ],
    )
    html = markdown(rendered)
    # html = mistune.html(rendered)

    html = html.replace("<table>", '<table class="table table-sm">')

    return mark_safe(html)
