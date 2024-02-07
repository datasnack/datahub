from django.db import models as djmodels
from django.contrib.gis.db import models


class Type(djmodels.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    key         = models.CharField(max_length=255, unique=True)
    show_in_nav = models.BooleanField(default=True)
    position    = models.PositiveSmallIntegerField(default=1)
    name        = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    # Returns the string representation of the model.
    def __str__(self):
        return str(self.name)

class MyManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return super(MyManager, self).get_queryset(*args, **kwargs).defer("geometry")

# Create your models here.
class Shape(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    type = models.ForeignKey(
        Type,
        on_delete=models.RESTRICT,
        related_name='shapes'
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        related_name='children'
    )
    area_sqm =  models.FloatField(null=True)
    properties = models.JSONField(null=True)
    geometry = models.GeometryField(srid=4326)

    objects = MyManager()

    @property
    def area_sqkm(self):
        return self.area_sqm / 1000000

    # Returns the string representation of the model.
    def __str__(self):
        return str(self.name)

