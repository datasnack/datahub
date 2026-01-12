# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import tempfile
from enum import Enum
from io import BytesIO

import geopandas
import shapely
import shapely.geometry
from geojson import Feature, FeatureCollection, Point, Polygon
from ninja import File, Query, Router, Schema
from pydantic import Field

from django.conf import settings
from django.core.cache import caches
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from app.utils import datahub_key, generate_unique_hash
from shapes.models import Shape, Type

router = Router(tags=["Shapes"])


class ShapeOutputFormat(str, Enum):
    geojson = "geojson"
    gpkg = "gpkg"
    shp = "shp"
    wkt = "wkt"
    csv = "csv"


@router.get(
    "/geometry",
    summary="Shape geometries",
    description="Select geometries of Shapes in different formats.",
)
def shape_geometry(
    request,
    shape_id: int | None = Query(
        None,
        description="ID of the shape",
    ),
    shape_type: str | None = Query(
        None,
        description="key of the shape type",
    ),
    shape_parent_id: int | None = Query(
        None,
        description="ID of a Shape (if present)",
    ),
    simplify: float | None = Query(
        settings.DATAHUB_GEOMETRY_SIMPLIFY,
        description="Apply [`.simplify()`](https://shapely.readthedocs.io/en/latest/manual.html#object.simplify) to the geometries to reduce file size.",
    ),
    fmt: ShapeOutputFormat = Query(  # noqa: B008
        "geojson",
        description="File format of response.",
        alias="format",
    ),
):
    cache = caches["geojson"]
    query = {
        "shape_id": shape_id,
        "shape_type": shape_type,
        "shape_parent_id": shape_parent_id,
        "format": fmt,
        "simplify": simplify,
    }
    if isinstance(query["simplify"], str):
        try:
            query["simplify"] = float(query["simplify"])
        except ValueError:
            query["simplify"] = settings.DATAHUB_GEOMETRY_SIMPLIFY

    # for API calls requesting GeoJSON (map integrations) we provide caching
    if query["format"] == "geojson":
        cache_key = generate_unique_hash(query)
        cached = cache.get(cache_key)
        if cached:
            name = cache.get(f"{cache_key}_name", "download")
            response = HttpResponse(cached, content_type="application/geo+json")
            response["Content-Disposition"] = f'attachment; filename="{name}.geojson"'
            return response

    # single, or type?
    shapes = []
    name = ""
    if shape_id := query["shape_id"]:
        shapes = [Shape.objects.get(pk=shape_id)]
        name = slugify(shapes[0].name)
    elif (shape_type := query["shape_type"]) and (
        shape_parent_id := query["shape_parent_id"]
    ):
        t = get_object_or_404(Type, key=shape_type)

        shapes = Shape.objects.filter(parent_id=shape_parent_id, type_id=t.id)
        name = slugify("siblings")

    elif shape_type := query["shape_type"]:
        t = get_object_or_404(Type, key=shape_type)
        shapes = t.shapes.all()
        name = slugify(t.name)
    elif shape_parent_id := query["shape_parent_id"]:
        shape = Shape.objects.get(pk=shape_parent_id)
        shapes = shape.children.all()
        name = slugify(f"{shape.name} children")
    else:
        # no filter, return all shapes
        shapes = Shape.objects.select_related("type").all()
        name = "shapes"

    name = datahub_key(name)

    # format
    fmt: str = request.GET.get("format", "geojson")

    # transform objects into GeoDataFrame
    rows = []
    for s in shapes:
        rows.append(
            {
                "dh_shape_id": s.id,
                "dh_parent_id": s.parent_id,
                "shape_key": s.key,
                "shape_name": s.name,
                "url": request.build_absolute_uri(s.get_absolute_url()),
                "area_sqkm": s.area_sqkm,
                "type_key": s.type.key,
                "geometry": s.shapely_geometry(),
            }
        )
    gdf = geopandas.GeoDataFrame(rows, geometry="geometry")
    gdf = gdf.set_crs(4326)

    if query["simplify"]:
        gdf["geometry"] = gdf["geometry"].simplify(
            tolerance=query["simplify"], preserve_topology=True
        )

    if fmt == "geojson":
        # save GeoJSON into variable to also put as a string into the Django cache.
        # indent=None to save the whitespace linebreaks
        content = gdf.to_json(indent=None)

        cache_key = generate_unique_hash(query)
        cache.set(cache_key, content)
        cache.set(f"{cache_key}_name", name)

        response = HttpResponse(content, content_type="application/geo+json")
        response["Content-Disposition"] = f'attachment; filename="{name}.geojson"'
        return response

    if fmt == "gpkg":
        file = BytesIO()
        gdf.to_file(file, driver="GPKG")
        file.seek(0)
        return FileResponse(file, as_attachment=True, filename=f"{name}.gpkg")

    if fmt == "shp":
        # extension .shp.zip leads to a zipped shp file with the additional
        # meta data files. Though saving this to BytesIO stream didn't work,
        # since filename can't be used in conjunction with the file stream.
        # so we save it to a temp dir instead and then return the tmp file.
        temp_dir = tempfile.TemporaryDirectory()
        file_name = f"{temp_dir.name}/{name}.shp.zip"
        gdf.to_file(filename=file_name, driver="ESRI Shapefile")
        return FileResponse(
            open(file_name, "rb"), as_attachment=True, filename=f"{name}.shp.zip"
        )

    if fmt == "wkt":
        gdf_wkt = gdf.to_wkt()
        if len(gdf_wkt) == 1:
            content = gdf_wkt.at[0, "geometry"]
            response = HttpResponse(content, content_type="text/plain")
            response["Content-Disposition"] = f'attachment; filename="{name}.wkt"'
            return response

        return HttpResponseBadRequest(
            "WKT export only works for single geometry, use CSV for multiple WKT instead."
        )

    if fmt == "csv":
        file = BytesIO()
        gdf.to_csv(file, index=False)
        file.seek(0)
        return FileResponse(file, as_attachment=True, filename=f"{name}.csv")

    return HttpResponseBadRequest("Invalid format")


@router.get("/bbox")
def shape_bbox(request, shape_id: int):
    if shape_id := request.GET.get("shape_id", None):
        shape = Shape.objects.get(pk=shape_id)
        name = slugify(shape.name)
    else:
        HttpResponseNotFound("No shape found")

    fmt = request.GET.get("format", "geojson")

    geom = shape.shapely_geometry()
    envelope = geom.envelope
    bounds = geom.bounds

    # create GeoJSON struct

    # bbox polygon
    envdict = shapely.geometry.mapping(envelope)
    p = Polygon(envdict["coordinates"])
    f = Feature(geometry=p)

    p_nw = Point((bounds[0], bounds[3]))
    f_nw = Feature(
        geometry=p_nw,
        properties={
            "name": "North-West",
            "values": {"lat": bounds[3], "lng": bounds[0]},
        },
    )

    p_ne = Point((bounds[2], bounds[3]))
    f_ne = Feature(
        geometry=p_ne,
        properties={
            "name": "North-East",
            "values": {"lat": bounds[3], "lng": bounds[2]},
        },
    )

    p_sw = Point((bounds[0], bounds[1]))
    f_sw = Feature(
        geometry=p_sw,
        properties={
            "name": "South-West",
            "values": {"lat": bounds[1], "lng": bounds[0]},
        },
    )

    p_se = Point((bounds[2], bounds[1]))
    f_se = Feature(
        geometry=p_se,
        properties={
            "name": "South-East",
            "values": {"lat": bounds[1], "lng": bounds[2]},
        },
    )

    # Lines
    p_n = Point((bounds[0] + (bounds[2] - bounds[0]) / 2, bounds[3]))
    f_n = Feature(
        geometry=p_n, properties={"name": "North", "values": {"lat": bounds[3]}}
    )

    p_e = Point((bounds[2], bounds[1] + (bounds[3] - bounds[1]) / 2))
    f_e = Feature(
        geometry=p_e, properties={"name": "East", "values": {"lng": bounds[2]}}
    )

    p_s = Point((bounds[0] + (bounds[2] - bounds[0]) / 2, bounds[1]))
    f_s = Feature(
        geometry=p_s, properties={"name": "South", "values": {"lng": bounds[1]}}
    )

    p_w = Point((bounds[0], bounds[1] + (bounds[3] - bounds[1]) / 2))
    f_w = Feature(
        geometry=p_w, properties={"name": "West", "values": {"lng": bounds[0]}}
    )

    p_c = Point((geom.centroid.x, geom.centroid.y))
    f_c = Feature(
        geometry=p_c,
        properties={
            "name": "Centroid",
            "description": "Geometric center of the shape",
            "values": {
                "lat": geom.centroid.y,
                "lng": geom.centroid.x,
            },
        },
    )

    fc = FeatureCollection([f, f_nw, f_ne, f_se, f_sw, f_n, f_s, f_e, f_w, f_c])

    if fmt == "geojson":
        return JsonResponse(fc)

    return HttpResponseBadRequest("Invalid format")
