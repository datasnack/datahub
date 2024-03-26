import datetime as dt
from timeit import default_timer as timer
from typing import List, Optional

import pandas as pd

from django.db import models, connection
from django.urls import reverse
from django.utils.functional import cached_property


from shapes.models import Shape, Type
from datalayers.utils import get_engine, dictfetchone
from .datasources.base_layer import LayerTimeResolution, LayerValueType

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


class DatalayerValue():

    def __init__(self, datalayer, row):
        self.result = row
        self.dl = datalayer

        self.value  = None
        self.time   = None

        if row is not None and "value" in row:
            self.value = row['value']


    def date(self):

        if self.result is None:
            return None

        match self.dl.temporal_resolution:
            case LayerTimeResolution.YEAR:
                if "year" in self.result:
                    return self.result['year']
                return None
            case LayerTimeResolution.DAY:
                if "date" in self.result:
                    return self.result['date'].strftime('%Y-%m-%d')
                return None
            case _:
                raise ValueError(f"Unknown time_col={self.dl.temporal_resolution}")


    def __str__(self):

        if self.result is None:
            return None

        return self.value



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

    # todo: we need a 1:n relationship
    #doi      = models.CharField(max_length=255, blank=True, null=True)
    #datacite = models.JSONField(null=True)
    #datacite_fetched_at = models.DateTimeField(null=True)

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

    def format_precision(self) -> int | None:
        if self.has_class():
            return self._get_class().precision
        else:
            return None

    def format_suffix(self) -> str | None:
        if self.has_class():
            return self._get_class().format_suffix
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

    def debug(self, message, context=None):
        self.log(DatalayerLogEntry.DEBUG, message, context=context)


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

            #raise

            return False

    def has_class_label(self) -> str:
        if self.has_class():
            return _('Source file is available')
        else:
            return _('Source file is not available')

    def has_files_label(self) -> str:
        if self.has_class():
            return _('Data is available local')
        else:
            return _('Data is not available local')

    def is_loaded_label(self) -> str:
        if self.has_class():
            return _('Data is loaded into the database')
        else:
            return _('Data is not loaded into the database')

    def get_class_path(self):
        return Path(f'src/datalayer/{self.key}.py')

    def get_class_source_code(self):
        """ Gets the actual file contents of the data layer source file. """

        p = self.get_class_path()

        if p.exists():
            return p.read_text(encoding="utf-8")

        return None



    def has_vector_data(self) -> bool:
        if self.has_class():
            return self._get_class().raw_vector_data_table is not None
        else:
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


    # --

    def str_format(self, value):

        if self.has_class():
            return self._get_class().str_format(value)

        return value

    def value(self,
        shape: Optional[Shape] = None,
        when: Optional[dt.datetime] = None,
        fallback_parent=False,
        mode='down'):

        if not self.is_loaded():
            return None

        # get the wanted compare operator
        modes = {
            'exact': '=',  # needs to be exactly the given date
            'up':    '>=', # same or next
            'down':  '<='  # same or previous
        }
        if mode not in modes:
            raise ValueError(f"Unknown mode={mode}")

        params = {}
        sql = f"SELECT dl.* FROM {self.key} AS dl "
        sql += "WHERE dl.shape_id = %(shape_id)s "
        params['shape_id'] = shape.id

        if when is not None:
            operator = modes[mode]
            if self.temporal_resolution == LayerTimeResolution.YEAR:
                sql += f"AND dl.year {operator} %(when)s "
                params['when'] = when
            elif self.temporal_resolution == LayerTimeResolution.DAY:
                sql += f"AND dl.date {operator} %(when)s "
                params['when'] = when
            else:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        sort_operator = 'DESC'
        if mode == 'up':
            sort_operator = 'ASC'

        sql += f"ORDER BY dl.{self.temporal_resolution} {sort_operator} LIMIT 1"

        with connection.cursor() as c:
            c.execute(sql, params)
            #result = c.fetchone()
            result = dictfetchone(c)

        print(result)

        dlv = DatalayerValue(self, result)
        return dlv



    def data(self,
        shape: Optional[Shape] = None,
        when: Optional[dt.datetime] = None,
        start_date: Optional[dt.datetime] = None,
        end_date: Optional[dt.datetime] = None,
        shape_type: Optional[Type] = None,
        select_shape_name=True,
        fallback_previous=False) -> pd.DataFrame:
        """ Aggregates the specified data of the data layer. """


        params = {}

        sql = f"SELECT value, shape_id, {self.temporal_resolution} \
            FROM {self.key} "

        # JOIN
        if shape_type or shape:
            sql += f"JOIN shapes_shape s ON s.id = {self.key}.shape_id "


        # WHERE
        sql += "WHERE 1=1 "

        if start_date:
            sql += f"AND {self.temporal_resolution} >= %(start_date)s "
            params['start_date'] = start_date

        if end_date:
            sql += f"AND {self.temporal_resolution} <= %(end_date)s "
            params['end_date'] = end_date

        if shape:
            sql += "AND s.id = %(shape_id)s "
            params['shape_id'] = shape.id

        if shape_type:
            sql += "AND s.type_id = %(type)s "
            params['type'] = shape_type.id

        sql += f"ORDER BY {self.temporal_resolution} ASC"

        df = pd.read_sql(sql, con=get_engine(), params=params)

        return df

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
                return ((last - first).days + 1) * type_multiplier
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
                sql_order = "ORDER BY year ASC LIMIT 1"
            case LayerTimeResolution.DAY:
                sql = f"SELECT dl.date FROM {self.key} AS dl "
                sql_order = "ORDER BY date ASC LIMIT 1"
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        if shape_type is not None:
            sql += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            sql += "WHERE s.type_id = %(type_id)s "
            params['type_id'] = shape_type.id

        sql += sql_order

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
                sql_order = "ORDER BY year DESC LIMIT 1"
            case LayerTimeResolution.DAY:
                sql = f"SELECT dl.date FROM {self.key} AS dl "
                sql_order = "ORDER BY date DESC LIMIT 1"
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        if shape_type is not None:
            sql += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            sql += "WHERE s.type_id = %(type_id)s "
            params['type_id'] = shape_type.id

        sql += sql_order
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
