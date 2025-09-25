from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from app.utils import prase_date_or_today
from datalayers.models import Datalayer
from shapes.models import Shape, Type

from .docs import extract_title_from_md, get_docs_structure, render_dj_md_to_html
from .models import BearerToken


@require_GET
def robots_txt(request):
    txt = """User-agent: *
Disallow: /api/
"""
    return HttpResponse(txt, content_type="text/plain")


def home(request):
    # check for translated file
    home_file = None
    language_code = get_language()
    if language_code != "en":  # en is always or default
        translation_file = Path(f"docs/Home.{language_code}.md")
        if translation_file.exists():
            home_file = translation_file

    # no translation found, use default
    if home_file is None:
        default_file = Path("docs/Home.md")
        if default_file.exists():
            home_file = default_file

    if home_file:
        text, title = extract_title_from_md(home_file.read_text(), "Home")
        rendered = render_dj_md_to_html(request, text)

        return render(
            request,
            "app/markdown_page.html",
            {"html": rendered, "title": title},
        )

    # no home file found, return default page
    return render(
        request,
        "app/home.html",
        {
            "shapes_count": Shape.objects.count(),
            "shape_types": Type.objects.order_by("position").all(),
            "datalayers_count": Datalayer.objects.count(),
        },
    )


def docs_view(request, path=""):
    docs = get_docs_structure()

    def rec_search_item(path, docs):
        match = None
        for item in docs:
            if item.is_dir():
                local_match = rec_search_item(path, item.children)
                if local_match:
                    match = local_match
            elif item.url == path:
                match = item

        return match

    item = rec_search_item(path, docs)
    if item is None:
        raise Http404("Page not found")

    text = ""
    title = ""

    try:
        language_code = get_language()
        if language_code != "en" and language_code in item.translations:
            item = item.translations[language_code]

        text, title = extract_title_from_md(item.path.read_text(), item.name)
        rendered = render_dj_md_to_html(request, text)

    except (OSError, UnicodeDecodeError):
        raise Http404("Could not read wiki page")

    return render(
        request,
        "app/markdown_page.html",
        {"html": rendered, "title": title},
    )


def changelog(request):
    text = _(
        "The project has not defined a changelog yet. Create a `CHANGELOG.md` inside your project root to track changes of the project and show them here."
    )

    changelog_file = settings.BASE_DIR / "src/CHANGELOG.md"

    if changelog_file.is_file():
        text = changelog_file.read_text()

    if text.startswith("#"):
        newline_index = text.find("\n")
        if newline_index != -1:
            title = text[1:newline_index].strip()
            text = text[newline_index + 1 :]
        else:
            title = text[1:].strip()
            text = ""  # No content after title
    else:
        title = _("Changelog")

    return render(
        request,
        "app/markdown_page.html",
        {"html": render_dj_md_to_html(request, text), "title": title},
    )


def search(request):
    """
    Perform LIKE search for Data Layers and shapes.

    Returns result in format for agolia/autocomplete-js.
    """
    search_term = request.GET.get("q", "")

    search_filter = request.GET.get("f", "shapes,datalayers").split(",")

    results = []

    if "shapes" in search_filter:
        shapes = Shape.objects.filter(
            Q(name__icontains=search_term) | Q(key__icontains=search_term)
        )

        for s in shapes:
            results.append(
                {
                    "type": "shape",
                    "url": s.get_absolute_url(),
                    "label": s.name,
                    "key": s.type.name,
                    "objectID": s.id,
                }
            )

    if "datalayers" in search_filter:
        datalayers = (
            Datalayer.objects.filter(
                Q(name__icontains=search_term)
                | Q(key__icontains=search_term)
                | Q(category__name__icontains=search_term)
                | Q(tags__name__icontains=search_term)
            )
            # reset potential multi col ordering from model Meta sub-class, so distinct()
            # works as expected that needs to have the same ORDER BY than query.
            .order_by()
            .distinct("id")
        )

        for d in datalayers:
            results.append(
                {
                    "type": "datalayer",
                    "url": d.get_absolute_url(),
                    "label": d.name,
                    "key": d.key,
                    "objectID": d.id,
                }
            )

    return JsonResponse({"results": [results]})


@login_required
def user_settings(request):
    return render(
        request,
        "app/user/settings.html",
        {},
    )


@login_required
@require_POST
def user_settings_create_token(request):
    """Create a new API token for the current user."""
    token = get_random_string(length=64)

    bearer_token = BearerToken()
    bearer_token.user = request.user
    bearer_token.token = token
    bearer_token.description = request.POST.get("description", "")
    bearer_token.save()

    messages.success(
        request,
        _(
            "API token was created: %(token)s Please copy this token to a safe place. It will not be visible again!"
        )
        % {"token": token},
    )

    return redirect("app:settings")


@login_required
@require_POST
def user_settings_delete_token(request):
    """Delete the specified API token for the current user."""
    bearer_token = BearerToken.objects.get(id=request.POST.get("token-id"))

    if bearer_token.user.id == request.user.id:
        bearer_token.delete()

    return redirect("app:settings")


def tools_picker(request):
    """View for a location picker that selects all available shapes on the location."""
    context = {
        "shapes": None,
        "datalayers": None,
        "point": None,
        "warning": None,
    }

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    shape_type = request.GET.get("shape_type")
    temporal = request.GET.get("temporal")
    datalayers = request.GET.get("datalayers")

    if datalayers:
        datalayers = [item.strip() for item in datalayers.split(",")]

    if lat is not None and lng is not None:
        context["dt_temporal"] = prase_date_or_today(temporal)

        point = Point(float(lng), float(lat))
        shapes = Shape.objects.filter(geometry__contains=point).order_by(
            "type__position"
        )

        valid_shape_types = [shape.type.key for shape in shapes]

        if not shapes:
            context["warning"] = _(
                "The provided location did not intersect with any Shapes."
            )
        else:
            context["shapes"] = shapes
            context["point"] = point

            if shape_type in valid_shape_types:
                context["shape_type"] = shape_type
                context["active_shape"] = next(
                    shape for shape in shapes if shape.type.key == shape_type
                )
            else:
                context["shape_type"] = valid_shape_types[0]
                context["active_shape"] = shapes[0]

            if datalayers:
                all_layers = Datalayer.objects.get_datalayers(datalayers)
            else:
                all_layers = Datalayer.objects.all()
            context["datalayers"] = []
            for layer in all_layers:
                if layer.is_available():
                    context["datalayers"].append(layer)

    return render(request, "tools/picker.html", context)
