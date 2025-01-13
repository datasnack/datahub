import tempfile
from io import BytesIO

import geopandas
import shapely
import shapely.geometry
from geojson import Feature, FeatureCollection, Point, Polygon
from shapely import wkt

from django.conf import settings
from django.http import (
    FileResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from shapes.models import Shape, Type

# Create your views here.


def shape_geometry(request):
    """
    Provide download of geometries for specified shapes in a format like GeoJSON or GeoPackage.

    Probably could be speed up with not using the ORM, tough the ORM classes
    for models provide ways to access the URL etc. Maybe utilize some sort of
    file caching.

    GeoDjango provides a serializer for GeoJSON like:

    >>> from django.core.serializers import serialize
    >>> serialized_data = serialize("geojson", t.shapes.all(), geometry_field="geometry", fields=["name"])

    But it's unclear to me how put something like the URL or type name into the
    fields. Also the performance seemed not great. Due to the different needed
    formats the approach with GeoPandas and using the same structure seems
    preferable anyway.
    """
    query = {
        "shape_id": request.GET.get("shape_id", None),
        "shape_type": request.GET.get("shape_type", None),
        "shape_parent_id": request.GET.get("shape_parent_id", None),
        "format": request.GET.get("format", "geojson"),
        "simplify": request.GET.get("simplify", settings.DATAHUB_GEOMETRY_SIMPLIFY),
    }
    # single, or type?
    shapes = []
    name = ""
    if shape_id := request.GET.get("shape_id", None):
        shapes = [Shape.objects.get(pk=shape_id)]
        name = slugify(shapes[0].name)
    elif (shape_type := request.GET.get("shape_type", None)) and (
        shape_parent_id := request.GET.get("shape_parent_id", None)
    ):
        t = get_object_or_404(Type, key=shape_type)

        shapes = Shape.objects.filter(parent_id=shape_parent_id, type_id=t.id)
        name = slugify("siblings")

    elif shape_type := request.GET.get("shape_type", None):
        t = get_object_or_404(Type, key=shape_type)
        shapes = t.shapes.all()
        name = slugify(t.name)
    elif shape_parent_id := request.GET.get("shape_parent_id", None):
        shape = Shape.objects.get(pk=shape_parent_id)
        shapes = shape.children.all()
        name = slugify(f"{shape.name} children")
    else:
        HttpResponseNotFound("No shapes found")

    name = datahub_key(name)

    # format
    fmt = request.GET.get("format", "geojson")

    # transform objects into GeoDataFrame
    rows = []
    for s in shapes:
        rows.append(
            {
                "id": s.id,
                "url": request.build_absolute_uri(s.get_absolute_url()),
                "name": s.name,
                "area_sqkm": s.area_sqkm,
                "type": s.type.key,
                "geometry": wkt.loads(s.geometry.wkt),
            }
        )
    gdf = geopandas.GeoDataFrame(rows, geometry="geometry")
    gdf = gdf.set_crs(4326)

    if query["simplify"]:
        gdf["geometry"] = gdf["geometry"].simplify(
            tolerance=query["simplify"], preserve_topology=True
        )

    if fmt == "geojson":
        file = BytesIO()
        gdf.to_file(file, driver="GeoJSON")
        file.seek(0)
        response = FileResponse(file, as_attachment=False, filename=f"{name}.geojson")
        response["Content-Type"] = "application/geo+json"
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

    if fmt == "csv":
        file = BytesIO()
        gdf.to_csv(file, index=False)
        file.seek(0)
        return FileResponse(file, as_attachment=True, filename=f"{name}.csv")

    return HttpResponseBadRequest("Invalid format")


def shape_bbox(request):
    if shape_id := request.GET.get("shape_id", None):
        shape = Shape.objects.get(pk=shape_id)
        name = slugify(shape.name)
    else:
        HttpResponseNotFound("No shape found")

    fmt = request.GET.get("format", "geojson")

    geom = wkt.loads(shape.geometry.wkt)
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
        properties={"name": "North-West", "lat": bounds[3], "lng": bounds[0]},
    )

    p_ne = Point((bounds[2], bounds[3]))
    f_ne = Feature(
        geometry=p_ne,
        properties={"name": "North-East", "lat": bounds[3], "lng": bounds[2]},
    )

    p_sw = Point((bounds[0], bounds[1]))
    f_sw = Feature(
        geometry=p_sw,
        properties={"name": "South-West", "lat": bounds[1], "lng": bounds[0]},
    )

    p_se = Point((bounds[2], bounds[1]))
    f_se = Feature(
        geometry=p_se,
        properties={"name": "South-East", "lat": bounds[1], "lng": bounds[2]},
    )

    # Lines
    p_n = Point((bounds[0] + (bounds[2] - bounds[0]) / 2, bounds[3]))
    f_n = Feature(geometry=p_n, properties={"name": "North", "lat": bounds[3]})

    p_e = Point((bounds[2], bounds[1] + (bounds[3] - bounds[1]) / 2))
    f_e = Feature(geometry=p_e, properties={"name": "East", "lng": bounds[2]})

    p_s = Point((bounds[0] + (bounds[2] - bounds[0]) / 2, bounds[1]))
    f_s = Feature(geometry=p_s, properties={"name": "South", "lng": bounds[1]})

    p_w = Point((bounds[0], bounds[1] + (bounds[3] - bounds[1]) / 2))
    f_w = Feature(geometry=p_w, properties={"name": "West", "lng": bounds[0]})

    p_c = Point((geom.centroid.x, geom.centroid.y))
    f_c = Feature(
        geometry=p_c,
        properties={
            "name": "Centroid",
            "": "geometric center of the shape",
            "lat": geom.centroid.y,
            "lng": geom.centroid.x,
        },
    )

    fc = FeatureCollection([f, f_nw, f_ne, f_se, f_sw, f_n, f_s, f_e, f_w, f_c])

    if fmt == "geojson":
        return JsonResponse(fc)

    return HttpResponseBadRequest("Invalid format")
