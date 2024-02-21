import importlib.util
import sys

from django.conf import settings
from django.db import models, connection
from django.urls import reverse


# Create your models here.

def camel(s):
    s = s.replace('_', ' ')
    s = s.replace('-', ' ')
    return s.title().replace(' ', '')


class Category(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"

    # Returns the string representation of the model.
    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("datalayers:datalayer_index_category", kwargs={'category_id': self.id})


class Datalayer(models.Model):
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    key         = models.CharField(max_length=255, unique=True, blank=False)
    name        = models.CharField(max_length=255)
    category    = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name='datalayers',
        blank=True, null=True
    )
    description = models.TextField(blank=True)

    # Data type and processing
    necessity        = models.CharField(max_length=255, blank=True)
    format           = models.CharField(max_length=255, blank=True)
    original_unit    = models.CharField(max_length=255, blank=True)
    operation        = models.CharField(max_length=255, blank=True)
    database_unit    = models.CharField(max_length=255, blank=True)
    details_spatial  = models.CharField(max_length=255, blank=True)
    details_temporal = models.CharField(max_length=255, blank=True)
    timeframe        = models.CharField(max_length=255, blank=True)
    related_sources  = models.CharField(max_length=255, blank=True)

    # Metadata
    creator       = models.CharField(max_length=255, blank=True)
    included_date = models.DateField(blank=True, null=True)
    type          = models.CharField(max_length=255, blank=True)
    identifier    = models.CharField(max_length=255, blank=True)
    source        = models.TextField(blank=True)
    source_link   = models.TextField(blank=True)
    citation      = models.TextField(blank=True)
    language      = models.CharField(max_length=255, blank=True)
    license       = models.CharField(max_length=255, blank=True)
    coverage      = models.CharField(max_length=255, blank=True)

    # Returns the string representation of the model.
    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("datalayers:datalayer_detail", kwargs={'pk': self.id})

    def _get_class(self):
        #spec = importlib.util.spec_from_file_location("module.name", settings.DATAHUB_DATALAYER_DIR)


        mod = __import__(f'src.datalayer.{self.key}', fromlist=[camel(self.key)])
        cls = getattr(mod, camel(self.key))()
        cls.layer = self
        return cls

    def has_class(self):
        """ Check if there is a corresponding class with details for
        downloading and processing the data source. """
        try:
            self._get_class()
            return True
        except ModuleNotFoundError:
            # todo: this will also return false if a dependency loaded by the
            # class is not found
            return False

    def is_loaded(self):
        """ Check if the data has been processed and are stored in the
        database. """

        # todo: this runs a database query each time the method is called.
        # we need to run/cache this once per request.
        return self.key in connection.introspection.table_names()

    def download(self):
        """ Automatic download of data source files. """

        cls = self._get_class()
        cls.download()


    def process(self):
        """ Consume/calculate data to insert into the database. """

        cls = self._get_class()
        cls.process()
