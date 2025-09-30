import logging

from mistune import HTMLRenderer
from mistune.util import escape as escape_text
from mistune.util import safe_entity, striptags

from django.urls import reverse

from datalayers.models import Datalayer
from shapes.models import Shape, Type

logger = logging.getLogger(__name__)


class DjangoTemplateRenderer(HTMLRenderer):
    def link(self, text: str, url: str, title: str | None = None) -> str:
        url = url.strip()

        # link to local markdown file
        if url.startswith("./") and url.endswith(".md"):
            from app.docs import clean_path

            url = reverse(
                "app:docs_page",
                kwargs={"path": clean_path(url)},
            )

        # link to local file
        if url.startswith("./"):
            url = reverse(
                "app:file_download",
                kwargs={"file_path": self.safe_url(url.removeprefix("./"))},
            )

        if url.startswith("shape_key"):
            shape_key = url.replace("shape_key=", "")
            url = reverse(
                "shapes:shape_detail",
                kwargs={"key": shape_key},
            )

            if not text:
                try:
                    shape = Shape.objects.get(key=shape_key)
                    text = shape.name
                except Shape.DoesNotExist:
                    logger.warning(
                        "[docs] tried to lookup shape that does not exists: shape_key=%s",
                        shape_key,
                    )

            s = (
                '<a data-shape-key="'
                + safe_entity(shape_key)
                + '" href="'
                + self.safe_url(url)
                + '"'
            )
            if title:
                s += ' title="' + safe_entity(title) + '"'
            return s + ">" + text + "</a>"

        if url.startswith("type_key"):
            type_key = url.replace("type_key=", "")
            url = reverse(
                "shapes:shape_index",
                kwargs={"type_key": type_key},
            )

            if not text:
                try:
                    shape_type = Type.objects.get(key=type_key)
                    text = shape_type.name
                except Shape.DoesNotExist:
                    logger.warning(
                        "[docs] tried to lookup shape type that does not exists: type_key=%s",
                        type_key,
                    )

            s = (
                '<a data-type-key="'
                + safe_entity(type_key)
                + '" href="'
                + self.safe_url(url)
                + '"'
            )
            if title:
                s += ' title="' + safe_entity(title) + '"'
            return s + ">" + text + "</a>"

        if url.startswith("datalayer_key"):
            datalayer_key = url.replace("datalayer_key=", "")
            url = reverse(
                "datalayers:datalayer_detail",
                kwargs={"key": datalayer_key},
            )

            if not text:
                try:
                    dl = Datalayer.objects.get(key=datalayer_key)
                    text = dl.name
                except Datalayer.DoesNotExist:
                    logger.warning(
                        "[docs] tried to lookup data layer that does not exists: datalayer_key=%s",
                        datalayer_key,
                    )

            s = (
                '<a data-datalayer-key="'
                + safe_entity(datalayer_key)
                + '" href="'
                + self.safe_url(url)
                + '"'
            )
            if title:
                s += ' title="' + safe_entity(title) + '"'
            return s + ">" + text + "</a>"

        return super().link(text, url, title)

    def image(self, text: str, url: str, title: str | None = None) -> str:
        src = reverse(
            "app:file_download",
            kwargs={"file_path": self.safe_url(url.removeprefix("./"))},
        )
        alt = escape_text(striptags(text))
        s = '<img src="' + src + '" alt="' + alt + '"'
        if title:
            s += ' title="' + safe_entity(title) + '"'
        return s + " />"
