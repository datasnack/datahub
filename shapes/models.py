from typing import Self

from shapely import wkt

from django.contrib.gis.db import models
from django.db import models as djmodels
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Type(djmodels.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    key = models.CharField(max_length=255, unique=True)
    show_in_nav = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    # Returns the string representation of the model.
    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return reverse("shapes:shape_index", kwargs={"type_key": self.key})


class MyManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return super(MyManager, self).get_queryset(*args, **kwargs).defer("geometry")


NO_DEFAULT = object()  # Sentinel value to detect if no default was provided


# Create your models here.
class Shape(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    key = models.SlugField(max_length=255, null=False, unique=True)
    admin = models.PositiveSmallIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    license = models.TextField(
        blank=True,
        null=True,
        help_text=_("SPDX identifier of the license if available."),
    )
    attribution_text = models.TextField(blank=True, null=True)
    attribution_url = models.URLField(blank=True, null=True)
    attribution_html = models.TextField(blank=True, null=True)

    type = models.ForeignKey(
        Type,
        on_delete=models.RESTRICT,
        related_name="shapes",
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        related_name="children",
    )
    area_sqm = models.FloatField(null=True)
    properties = models.JSONField(blank=True, null=True)
    geometry = models.GeometryField(srid=4326)

    objects = MyManager()

    class Meta:
        ordering = ["name"]

    @property
    def area_sqkm(self):
        return self.area_sqm / 1000000

    @property
    def has_properties(self, default=None):
        return len(self.properties) > 0

    def get_property(self, key: str, default=NO_DEFAULT):
        if self.has_properties and key in self.properties:
            return self.properties[key]

        if default is NO_DEFAULT:
            raise Exception("Shape has no property with key=%s", key)

        return default

    def shapely_geometry(self):
        # todo: can this loose CRS?
        # todo: why is even necessary, doesn't GeoDjango provide a sensible way to get
        # the geometry for use with shapely?
        return wkt.loads(self.geometry.wkt)

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return reverse("shapes:shape_detail", kwargs={"pk": self.id})

    def has_parent(self) -> bool:
        return self.parent is not None

    def is_parent_of(self, shape: Self) -> bool:
        if self.id == shape.id:
            return True

        # breath search first
        for child in self.children.all():
            if child.id == shape.id or child.is_parent_of(shape):
                return True

        return False

    def datalayer_value(self, dl, when=None, mode="down"):
        value = dl.value(self, mode=mode, when=when)

        if not value.has_value() and self.has_parent():
            value = self.parent.datalayer_value(dl, when=when, mode=mode)

            value.set_requested_shape(self)

        value.set_requested_ts(when)

        return value
