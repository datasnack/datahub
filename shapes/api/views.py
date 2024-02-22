from io import BytesIO

import geopandas
from shapely import wkt

from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound, HttpResponseBadRequest, FileResponse
from django.utils.text import slugify

from shapes.models import Shape, Type


# Create your views here.

def shape_geometry(request):
    """ Provides download of geometries for specified shapes in a format like
    GeoJSON or GeoPackage.

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

    # single, or type?
    shapes = []
    name = ""
    test = ""
    if shape_id := request.GET.get('shape_id', None):
        shapes = [Shape.objects.get(pk=shape_id)]
        name = slugify(shapes[0].name)
    elif shape_type := request.GET.get('shape_type', None):
        t = get_object_or_404(Type, key=shape_type)
        shapes = t.shapes.all()
        name = slugify(t.name)
    else:
        HttpResponseNotFound("No shapes found")

    # format
    fmt = request.GET.get('format', 'geojson')

    # transform objects into GeoDataFrame
    rows = []
    for s in shapes:
        rows.append({
            'id': s.id,
            'url': request.build_absolute_uri(s.get_absolute_url()),
            'name': s.name,
            'type': s.type.key,
            'geometry': wkt.loads(s.geometry.wkt)
        })
    gdf = geopandas.GeoDataFrame(rows, geometry='geometry')
    gdf = gdf.set_crs(4326)

    if fmt == 'geojson':
        file = BytesIO()
        gdf.to_file(file, driver='GeoJSON')
        file.seek(0)
        response = FileResponse(file, as_attachment=False, filename=f'{name}.geojson')
        response['Content-Type'] = 'application/geo+json'
        return response

    if fmt == 'gpkg':
        file = BytesIO()
        gdf.to_file(file, driver='GPKG')
        file.seek(0)
        return FileResponse(file, as_attachment=True, filename=f'{name}.gpkg')

    if fmt == 'shp':
        file = BytesIO()
        gdf.to_file(file)
        file.seek(0)
        return FileResponse(file, as_attachment=True, filename=f'{name}.shp')

    return HttpResponseBadRequest("Invalid format")
