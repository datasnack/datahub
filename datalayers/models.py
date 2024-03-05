import datetime as dt
from timeit import default_timer as timer
from typing import List, Optional

from django.db import models, connection
from django.urls import reverse
from django.utils.functional import cached_property

from .datasources.base_layer import LayerTimeResolution, LayerValueType

from shapes.models import Shape, Type

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

    doi      = models.CharField(max_length=255, blank=True, null=True)
    datacite = models.JSONField(null=True)
    datacite_fetched_at = models.DateTimeField(null=True)

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

    # --

    @property
    def temporal_resolution(self) -> LayerTimeResolution | None:
        if self.has_class():
            return self._get_class().time_col
        else:
            return None

    @property
    def temporal_resolution_str(self) -> str | None:
        """ Return Enum type of layer as string so we can compare it in
        Django templates. Probably there is a better way... """
        if self.has_class():
            return str(self._get_class().time_col)
        else:
            return None

    @property
    def value_type(self) -> LayerValueType | None:
        if self.has_class():
            return self._get_class().value_type
        else:
            return None

    @property
    def value_type_str(self) -> str | None:
        if self.has_class():
            return str(self._get_class().value_type)
        else:
            return None



    def log(self, level, message, context=None):
        if context is None:
            context = {}

        entry = DatalayerLogEntry(datalayer=self, level=level, message=message, context=context)
        entry.save()

    def info(self, message, context=None):
        self.log(DatalayerLogEntry.INFORMATIONAL, message, context=context)

    def warning(self, message, context=None):
        self.log(DatalayerLogEntry.WARNING, message, context=context)


    @cached_property
    def get_available_shape_types(self) -> List[Type]:
        """ Determines all shape types the datalayer has values for. """

        if not self.is_loaded():
            return []

        with connection.cursor() as c:
            sql = f"SELECT DISTINCT t.id FROM {self.key} AS dl \
                JOIN shapes_shape as s ON s.id = dl.shape_id  \
                JOIN shapes_type as t ON t.id = s.type_id"

            c.execute(sql)
            results = c.fetchall()

        type_ids = []
        for row in results:
            type_ids.append(row[0])

        return Type.objects.filter(id__in=type_ids).order_by('position')

    @cached_property
    def get_available_years(self) -> List[int]:
        """ Finds all years for which data are available. In case of data layers
        with a more detailed time resolution, like month or date, it loads the
        affected years. """

        if not self.is_loaded():
            #self.logger.warning("Peek of data requested but not loaded for shape_id=%s", shape_id)
            return []

        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                sql = f"SELECT DISTINCT year FROM {self.key} ORDER BY year DESC"
            case LayerTimeResolution.DAY:
                sql = f"SELECT DATE_PART('year', date ::date) AS year \
                FROM {self.key} WHERE date is not NULL GROUP BY year ORDER BY year DESC"
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        with connection.cursor() as c:
            c.execute(sql)
            results = c.fetchall()

        years = []
        for row in results:
            years.append(row[0])

        return years



    def _get_class(self):
        #spec = importlib.util.spec_from_file_location("module.name", settings.DATAHUB_DATALAYER_DIR)

        mod = __import__(f'src.datalayer.{self.key}', fromlist=[camel(self.key)])
        cls = getattr(mod, camel(self.key))()
        cls.layer = self
        return cls

    def has_class(self) -> bool:
        """ Check if there is a corresponding class with details for
        downloading and processing the data source. """
        try:
            self._get_class()
            return True
        except ModuleNotFoundError:
            # todo: this will also return false if a dependency loaded by the
            # class is not found
            return False

    @cached_property
    def _database_tables(self):
        """ this caches the query at least per instance but not yet per request
        for alls instances. """
        return connection.introspection.table_names()

    def is_loaded(self) -> bool:
        """ Check if the data has been processed and are stored in the
        database. """

        # todo: this runs a database query each time the method is called.
        # we need to run/cache this once per request.
        return self.key in self._database_tables

    def has_files(self) -> bool:
        """ Check if for the specified download directory of the datalayer files
        are present. """
        if self.has_class():
            return self._get_class().get_data_path().exists()
        else:
            return False

    def value_coverage(self, shape_type: Optional[Type] = None) -> float:

        if not self.is_loaded():
            return None

        expected = self.expected_value_count(shape_type)
        actual   = self.count_values(shape_type)
        return actual / expected

    def expected_value_count(self, shape_type: Optional[Type] = None) -> int:

        if not self.is_loaded():
            return None

        first = self.first_time(shape_type)
        last  = self.last_time(shape_type)

        if shape_type is None:
            type_multiplier = Shape.objects.count()
        else:
            type_multiplier = Shape.objects.filter(type=shape_type).count()

        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                dt_first = dt.datetime(int(first), 1, 1)
                dt_last  = dt.datetime(int(last), 1, 1)
                return (dt_last.year - dt_first.year + 1) * type_multiplier
            case LayerTimeResolution.DAY:
                raise NotImplementedError
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

    def count_values(self, shape_type: Optional[Type] = None):
        if not self.is_loaded():
            return None

        params = {}
        sql = f"SELECT COUNT(*) AS count FROM {self.key} AS dl "

        if shape_type is not None:
            sql += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            sql += "WHERE s.type_id = %(type_id)s "
            params['type_id'] = shape_type.id

        with connection.cursor() as c:
            c.execute(sql, params)
            result = c.fetchone()

        return result[0]

    def first_time(self, shape_type: Optional[Type] = None):
        """ Determines the first point in time a value is available. """
        if not self.is_loaded():
            return None

        params = {}
        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                sql = f"SELECT dl.year FROM {self.key} AS dl "
            case LayerTimeResolution.DAY:
                sql = f"SELECT dl.date FROM {self.key} AS dl "
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        if shape_type is not None:
            sql += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            sql += "WHERE s.type_id = %(type_id)s "
            params['type_id'] = shape_type.id

        sql += "ORDER BY year ASC LIMIT 1"

        with connection.cursor() as c:
            c.execute(sql, params)
            result = c.fetchone()

        return result[0]

    def last_time(self, shape_type: Optional[Type] = None):
        """ Determines the first point in time a value is available. """
        if not self.is_loaded():
            return None

        params = {}
        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                sql = f"SELECT dl.year FROM {self.key} AS dl "
            case LayerTimeResolution.DAY:
                sql = f"SELECT dl.date FROM {self.key} AS dl "
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        if shape_type is not None:
            sql += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            sql += "WHERE s.type_id = %(type_id)s "
            params['type_id'] = shape_type.id

        sql += "ORDER BY year DESC LIMIT 1"
        with connection.cursor() as c:
            c.execute(sql, params)
            result = c.fetchone()

        return result[0]


    # ---

    def download(self):
        """ Automatic download of data source files. """

        start = timer()
        self.info("Starting download")
        cls = self._get_class()
        cls.download()
        end = timer()
        self.info("Finished download", {'end': end, 'duration': end-start})

    def process(self):
        """ Consume/calculate data to insert into the database. """

        start = timer()
        self.info("Starting processing")

        cls = self._get_class()
        cls.process()

        end = timer()
        self.info("Finished processing", {'duration': end-start})


class DatalayerLogEntry(models.Model):

    # levels based on Syslog https://datatracker.ietf.org/doc/html/rfc5424
    EMERGENCY     = 'emerg'
    ALERT         = 'alert'
    CRITICAL      = 'crit'
    ERROR         = 'err'
    WARNING       = 'warning'
    NOTICE        = 'notice'
    INFORMATIONAL = 'info'
    DEBUG         = 'debug'

    SEVERITY_CHOICES = [
        (DEBUG, 'Debug'),
        (INFORMATIONAL, 'Informational'),
        (NOTICE, 'Notice'),
        (WARNING, 'Warning'),
        (ERROR, 'Error'),
        (CRITICAL, 'Critical'),
        (ALERT, 'Alert'),
        (EMERGENCY, 'Emergency')
    ]

    datetime  = models.DateTimeField(auto_now_add=True)
    # updated_at is no really necessary for an read-only log

    # this might be more ore less the channel of the log statement
    datalayer = models.ForeignKey(
        Datalayer,
        on_delete=models.RESTRICT,
        related_name='logentries',
    )

    level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    context = models.JSONField(default=list)
