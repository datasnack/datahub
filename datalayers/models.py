import datetime as dt
import logging
import string
from pathlib import Path
from timeit import default_timer as timer
from typing import Optional

import pandas as pd
from psycopg import sql
from taggit.managers import TaggableManager

from django.db import connection, models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from datalayers.utils import dictfetchone
from shapes.models import Shape, Type

from .datasources.base_layer import LayerTimeResolution, LayerValueType

# Create your models here.
logger = logging.getLogger(__name__)


def camel(s):
    s = s.replace("_", " ")
    s = s.replace("-", " ")
    return string.capwords(s).replace(" ", "")


class Category(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    key = models.SlugField(max_length=255, null=False, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return reverse(
            "datalayers:datalayer_index_category", kwargs={"category_id": self.id}
        )


class DatalayerValue:
    def __init__(self, datalayer, row) -> None:
        self.result = row
        self.dl = datalayer

        self.value = None
        self.time = None

        if row is not None and "value" in row:
            self.value = row["value"]

    def date(self):
        if self.result is None:
            return None

        match self.dl.temporal_resolution:
            case LayerTimeResolution.YEAR:
                if "year" in self.result:
                    return self.result["year"]
                return None
            case LayerTimeResolution.DAY:
                if "date" in self.result:
                    return self.result["date"].strftime("%Y-%m-%d")
                return None
            case _:
                msg = f"Unknown time_col={self.dl.temporal_resolution}"
                raise ValueError(msg)

    def timestamp(self):
        if self.result is None:
            return None

        match self.dl.temporal_resolution:
            case LayerTimeResolution.YEAR:
                if "year" in self.result:
                    year = dt.datetime(self.result["year"], 0, 0)
                    return year.timestamp()
                return None
            case LayerTimeResolution.DAY:
                if "date" in self.result:
                    return self.result["date"].timestamp()
                return None
            case _:
                msg = f"Unknown time_col={self.dl.temporal_resolution}"
                raise ValueError(msg)

    def __str__(self) -> str:
        if self.result is None:
            return None

        return self.value


class Datalayer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    key = models.SlugField(max_length=255, null=False, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="datalayers",
        blank=True,
        null=True,
    )
    tags = TaggableManager(blank=True)
    date_included = models.DateField(blank=True, null=True)

    related_to = models.ManyToManyField("self", blank=True)

    # Data Layer metadata and processing
    # original_unit    = models.CharField(max_length=255, blank=True)
    operation = models.CharField(max_length=255, blank=True)
    database_unit = models.CharField(max_length=255, blank=True)

    # Original data source metadata
    format = models.CharField(max_length=255, blank=True)
    format_description = models.TextField(blank=True)
    format_unit = models.CharField(max_length=255, blank=True)

    spatial_details = models.CharField(max_length=255, blank=True)
    spatial_coverage = models.CharField(max_length=255, blank=True)

    temporal_details = models.CharField(max_length=255, blank=True)
    temporal_coverage = models.CharField(max_length=255, blank=True)

    source = models.TextField(blank=True)
    source_link = models.TextField(blank=True)
    language = models.CharField(max_length=255, blank=True)
    license = models.CharField(max_length=255, blank=True)
    date_published = models.TextField(
        blank=True
    )  # no date field. maybe only a year is known.
    date_last_accessed = models.DateField(blank=True, null=True)
    citation = models.TextField(blank=True)

    # creator       = models.CharField(max_length=255, blank=True)
    # type          = models.CharField(max_length=255, blank=True)
    # identifier    = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def get_absolute_url(self):
        return reverse("datalayers:datalayer_detail", kwargs={"key": self.key})

    # --

    @property
    def temporal_resolution(self) -> LayerTimeResolution | None:
        if self.has_class():
            return self._get_class().time_col
        else:
            return None

    @property
    def temporal_resolution_str(self) -> str | None:
        """
        Temporal resolution type Enum as string.

        Return Enum type of layer as string so we can compare it in
        Django templates. Probably there is a better way...
        """
        if self.has_class():
            return str(self._get_class().time_col)

        return None

    @property
    def value_type(self) -> LayerValueType | None:
        if self.has_class():
            return self._get_class().value_type

        return None

    @property
    def value_type_str(self) -> str | None:
        if self.has_class():
            return str(self._get_class().value_type)

        return None

    def format_precision(self) -> int | None:
        if self.has_class():
            return self._get_class().precision

        return None

    def format_suffix(self) -> str | None:
        if self.has_class():
            return self._get_class().format_suffix

        return None

    def log(self, level, message, context=None):
        if context is None:
            context = {}

        entry = DatalayerLogEntry(
            datalayer=self, level=level, message=message, context=context
        )
        entry.save()

    def info(self, message, context=None):
        self.log(DatalayerLogEntry.INFORMATIONAL, message, context=context)

    def warning(self, message, context=None):
        self.log(DatalayerLogEntry.WARNING, message, context=context)

    def debug(self, message, context=None):
        self.log(DatalayerLogEntry.DEBUG, message, context=context)

    @cached_property
    def get_available_shape_types(self) -> list[Type]:
        """Determine all shape types the datalayer has values for."""
        if not self.is_loaded():
            return []

        with connection.cursor() as c:
            query = sql.SQL(
                "SELECT DISTINCT t.id FROM {table} AS dl \
                JOIN shapes_shape as s ON s.id = dl.shape_id  \
                JOIN shapes_type as t ON t.id = s.type_id"
            ).format(table=sql.Identifier(self.key))
            c.execute(query)
            results = c.fetchall()

        type_ids = []
        for row in results:
            type_ids.append(row[0])

        return Type.objects.filter(id__in=type_ids).order_by("position")

    @cached_property
    def get_available_years(self) -> list[int]:
        """
        Find all years for which data are available.

        In case of data layers with a more detailed time resolution, like month or date,
        it loads the affected years.
        """
        if not self.is_loaded():
            # self.logger.warning("Peek of data requested but not loaded for shape_id=%s", shape_id)
            return []

        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                query = sql.SQL(
                    "SELECT DISTINCT year FROM {table} ORDER BY year DESC"
                ).format(table=sql.Identifier(self.key))
            case LayerTimeResolution.DAY:
                query = sql.SQL(
                    "SELECT DATE_PART('year', date ::date) AS year \
                FROM {table} WHERE date is not NULL GROUP BY year ORDER BY year DESC"
                ).format(table=sql.Identifier(self.key))
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        with connection.cursor() as c:
            c.execute(query)
            results = c.fetchall()

        years = []
        for row in results:
            years.append(row[0])

        return years

    def _get_class(self):
        # spec = importlib.util.spec_from_file_location("module.name", settings.DATAHUB_DATALAYER_DIR)

        mod = __import__(f"src.datalayer.{self.key}", fromlist=[camel(self.key)])
        cls = getattr(mod, camel(self.key))()
        cls.layer = self
        return cls

    def has_class(self) -> bool:
        """Check if there is a implementation class for the Data Layer."""
        has_class = False
        try:
            self._get_class()
            has_class = True
        except ModuleNotFoundError as e:
            # TODO: this will also return false if a dependency loaded by the
            # class is not found

            logger.debug("Could not load Data Layer class for %s: %s", self.key, str(e))

            # raise

        except Exception as e:
            logger.exception(
                "Could not load Data Layer class for %s: %s", self.key, str(e)
            )

        return has_class

    def has_source_file(self) -> bool:
        """Check if the source file for a Data Layer exists."""
        return self.get_class_path().exists()

    def get_class_path(self) -> Path:
        return Path(f"src/datalayer/{self.key}.py")

    def get_class_source_code(self):
        """Get the actual file contents of the data layer source file."""
        p = self.get_class_path()

        if p.exists():
            return p.read_text(encoding="utf-8")

        return None

    def has_vector_data(self) -> bool:
        if self.has_class():
            return self._get_class().raw_vector_data_table is not None

        return False

    @cached_property
    def _database_tables(self):
        """
        Get all loaded Data Layers (by looking at the database tables).

        This caches the query at least per instance but not yet per request
        for all instances.
        """
        return connection.introspection.table_names()

    def is_loaded(self) -> bool:
        """Check if the data has been processed and are stored in the database."""
        # TODO: this runs a database query each time the method is called.
        # we need to run/cache this once per request.
        return self.key in self._database_tables

    def has_files(self) -> bool:
        """Check if data of the Data Layer are downloaded and stored locally."""
        if self.has_class():
            return self._get_class().get_data_path().exists()

        return False

    # --

    def leaflet_popup(self):
        if self.has_class():
            if hasattr(self._get_class(), "leaflet_popup") and callable(
                getattr(self._get_class(), "leaflet_popup")
            ):
                return self._get_class().leaflet_popup()

        return None

    def str_format(self, value):
        if self.has_class():
            return self._get_class().str_format(value)

        return value

    def value(
        self,
        shape: Optional[Shape] = None,
        when: Optional[dt.datetime] = None,
        fallback_parent=False,
        mode="down",
    ):
        if not self.is_loaded():
            return None

        # get the wanted compare operator
        modes = {
            "exact": "=",  # needs to be exactly the given date
            "up": ">=",  # same or next
            "down": "<=",  # same or previous
        }
        if mode not in modes:
            raise ValueError(f"Unknown mode={mode}")

        params = {}
        query = "SELECT dl.* FROM {table} AS dl "
        query += "WHERE dl.shape_id = %(shape_id)s "
        params["shape_id"] = shape.id
        operator = ""

        if when is not None:
            operator = modes[mode]
            if self.temporal_resolution == LayerTimeResolution.YEAR:
                query += "AND dl.year {operator} %(when)s "
                params["when"] = when.year
            elif self.temporal_resolution == LayerTimeResolution.DAY:
                query += "AND dl.date {operator} %(when)s "
                params["when"] = when
            else:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        sort_operator = "DESC"
        if mode == "up":
            sort_operator = "ASC"

        query += "ORDER BY dl.{temporal_column} {sort_operator} LIMIT 1"

        query = sql.SQL(query).format(
            table=sql.Identifier(self.key),
            temporal_column=sql.Identifier(str(self.temporal_resolution)),
            operator=sql.SQL(operator),
            sort_operator=sql.SQL(sort_operator),
        )

        with connection.cursor() as c:
            c.execute(query, params)
            # result = c.fetchone()
            result = dictfetchone(c)

        dlv = DatalayerValue(self, result)
        return dlv

    def data(
        self,
        shape: Optional[Shape] = None,
        when: Optional[dt.datetime] = None,
        start_date: Optional[dt.datetime] = None,
        end_date: Optional[dt.datetime] = None,
        shape_type: Optional[Type] = None,
        select_shape_name=True,
        fallback_previous=False,
    ) -> pd.DataFrame:
        """Aggregate the specified data of the data layer."""
        params = {}
        query = "SELECT value, shape_id, {temporal_column} FROM {table} "

        # JOIN
        if shape_type or shape:
            query += "JOIN shapes_shape s ON s.id = {table}.shape_id "

        # WHERE
        query += "WHERE 1=1 "

        if start_date:
            query += "AND {temporal_column} >= %(start_date)s "
            params["start_date"] = start_date

        if end_date:
            query += "AND {temporal_column} <= %(end_date)s "
            params["end_date"] = end_date

        if shape:
            query += "AND s.id = %(shape_id)s "
            params["shape_id"] = shape.id

        if shape_type:
            query += "AND s.type_id = %(type)s "
            params["type"] = shape_type.id

        query += "ORDER BY {temporal_column} ASC"

        query = sql.SQL(query).format(
            table=sql.Identifier(self.key),
            temporal_column=sql.Identifier(str(self.temporal_resolution)),
        )

        return pd.read_sql(query.as_string(connection), con=connection, params=params)

    def value_coverage(self, shape_type: Optional[Type] = None) -> float:
        if not self.is_loaded():
            return None

        expected = self.expected_value_count(shape_type)
        actual = self.count_values(shape_type)

        return actual / expected

    def expected_value_count(self, shape_type: Optional[Type] = None) -> int:
        if not self.is_loaded():
            return None

        first = self.first_time(shape_type)
        last = self.last_time(shape_type)

        if shape_type is None:
            type_multiplier = Shape.objects.count()
        else:
            type_multiplier = Shape.objects.filter(type=shape_type).count()

        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                dt_first = dt.datetime(int(first), 1, 1)
                dt_last = dt.datetime(int(last), 1, 1)
                return (dt_last.year - dt_first.year + 1) * type_multiplier
            case LayerTimeResolution.DAY:
                return ((last - first).days + 1) * type_multiplier
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

    def count_values(self, shape_type: Optional[Type] = None):
        if not self.is_loaded():
            return None

        params = {}
        query = "SELECT COUNT(*) AS count FROM {table} AS dl "

        if shape_type is not None:
            query += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            query += "WHERE s.type_id = %(type_id)s "
            params["type_id"] = shape_type.id

        query = sql.SQL(query).format(table=sql.Identifier(self.key))
        with connection.cursor() as c:
            c.execute(query, params)
            result = c.fetchone()

        return result[0]

    def first_time(
        self, shape_type: Optional[Type] = None, shape: Optional[Shape] = None
    ):
        """Determine the first point in time a value is available."""
        if not self.is_loaded():
            return None

        params = {}
        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                query = "SELECT dl.year FROM {table} AS dl "
                query_order = "ORDER BY year ASC LIMIT 1"
            case LayerTimeResolution.DAY:
                query = "SELECT dl.date FROM {table} AS dl "
                query_order = "ORDER BY date ASC LIMIT 1"
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        # TODO: are shape_type and shape exclusive?
        # technical there are not, but it shoud not lea
        if shape_type is not None:
            query += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            query += "WHERE s.type_id = %(type_id)s "
            params["type_id"] = shape_type.id
        elif shape is not None:
            query += "WHERE s.shape_id = %(shape_id)s "
            params["shape_id"] = shape.id

        query += query_order

        query = sql.SQL(query).format(table=sql.Identifier(self.key))
        with connection.cursor() as c:
            c.execute(query, params)
            result = c.fetchone()

        return result[0]

    def last_time(
        self, shape_type: Optional[Type] = None, shape: Optional[Shape] = None
    ):
        """Determine the first point in time a value is available."""
        if not self.is_loaded():
            return None

        params = {}
        match self.temporal_resolution:
            case LayerTimeResolution.YEAR:
                query = "SELECT dl.year FROM {table} AS dl "
                query_order = "ORDER BY year DESC LIMIT 1"
            case LayerTimeResolution.DAY:
                query = "SELECT dl.date FROM {table} AS dl "
                query_order = "ORDER BY date DESC LIMIT 1"
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

        if shape_type is not None:
            query += "JOIN shapes_shape AS s ON  s.id = dl.shape_id "
            query += "WHERE s.type_id = %(type_id)s "
            params["type_id"] = shape_type.id
        elif shape is not None:
            query += "WHERE s.shape_id = %(shape_id)s "
            params["shape_id"] = shape.id

        query += query_order

        query = sql.SQL(query).format(table=sql.Identifier(self.key))
        with connection.cursor() as c:
            c.execute(query, params)
            result = c.fetchone()

        return result[0]

    # ---

    def download(self):
        """Automatic download of data source files."""
        start = timer()
        self.info("Starting download")
        cls = self._get_class()
        cls.download()
        end = timer()
        self.info("Finished download", {"end": end, "duration": end - start})

    def process(self):
        """Consume/calculate data to insert into the database."""
        start = timer()
        self.info("Starting processing")

        cls = self._get_class()
        cls.process()

        end = timer()
        self.info("Finished processing", {"duration": end - start})


class DatalayerSource(models.Model):
    class SourcePIDType(models.TextChoices):
        DOI = "DOI", _("DOI")
        ROR = "ROR", _("ROR")
        ORCID = "ORCID", _("ORCID")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    datalayer = models.ForeignKey(
        Datalayer,
        on_delete=models.CASCADE,
        related_name="sources",
        blank=True,
        null=True,
    )

    pid_type = models.CharField(
        max_length=255,
        choices=SourcePIDType,
        default=SourcePIDType.DOI,
    )
    pid = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)

    # TODO: bibtex field?

    # in case of DOI
    datacite = models.JSONField(null=True, blank=True, editable=False)
    datacite_fetched_at = models.DateTimeField(null=True, blank=True, editable=False)

    def get_pid_url(self):
        match self.pid_type:
            case DatalayerSource.SourcePIDType.DOI:
                return f"https://doi.org/{self.pid}"

            case DatalayerSource.SourcePIDType.ROR:
                return f"https://ror.org/{self.pid}"

            case DatalayerSource.SourcePIDType.DOI:
                return f"https://orcid.org/{self.pid}"

            case _:
                return "#"


class DatalayerLogEntry(models.Model):
    # levels based on Syslog https://datatracker.ietf.org/doc/html/rfc5424
    EMERGENCY = "emerg"
    ALERT = "alert"
    CRITICAL = "crit"
    ERROR = "err"
    WARNING = "warning"
    NOTICE = "notice"
    INFORMATIONAL = "info"
    DEBUG = "debug"

    SEVERITY_CHOICES = [
        (DEBUG, "Debug"),
        (INFORMATIONAL, "Informational"),
        (NOTICE, "Notice"),
        (WARNING, "Warning"),
        (ERROR, "Error"),
        (CRITICAL, "Critical"),
        (ALERT, "Alert"),
        (EMERGENCY, "Emergency"),
    ]

    datetime = models.DateTimeField(auto_now_add=True)
    # updated_at is no really necessary for an read-only log

    # this might be more ore less the channel of the log statement
    datalayer = models.ForeignKey(
        Datalayer,
        on_delete=models.RESTRICT,
        related_name="logentries",
    )

    level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    context = models.JSONField(default=list)
