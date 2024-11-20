from typing import Self

from django.contrib.gis.db import models
from django.db import models as djmodels
from django.urls import reverse


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


# Create your models here.
class Shape(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    attribution_text = models.CharField(blank=True, max_length=255)
    attribution_url = models.URLField(blank=True, max_length=255)
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
    properties = models.JSONField(null=True)
    geometry = models.GeometryField(srid=4326)

    objects = MyManager()

    class Meta:
        ordering = ["name"]

    @property
    def area_sqkm(self):
        return self.area_sqm / 1000000

    @property
    def has_properties(self):
        return len(self.properties) > 0

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
