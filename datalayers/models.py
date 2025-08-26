import datetime as dt
import logging
import string
from pathlib import Path
from timeit import default_timer as timer
from typing import Optional

import pandas as pd
from psycopg import sql
from taggit.managers import TaggableManager

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connection, models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from datalayers.utils import dictfetchone, get_conn_string
from shapes.models import Shape, Type

from .datasources.base_layer import BaseLayer, LayerTimeResolution, LayerValueType

# Create your models here.
logger = logging.getLogger(__name__)


def camel(s):
    s = s.replace("_", " ")
    s = s.replace("-", " ")
    return string.capwords(s).replace(" ", "")


class CategoryManager(models.Manager):
    def get_by_natural_key(self, key):
        return self.get(key=key)


class Category(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    key = models.SlugField(max_length=255, null=False, unique=True)
    description = models.TextField(blank=True)

    objects = CategoryManager()

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self):
        return reverse(
            "datalayers:datalayer_index_category", kwargs={"category_id": self.id}
        )

    def natural_key(self):
        return (self.key,)


class DatalayerValue:
    def __init__(self, datalayer, row) -> None:
        self.result = row
        self.dl = datalayer

        self.requested_shape = None
        self.requested_ts = None

        self.value = None
        self.shape_id = None
        self.time = None

        if row is not None and "value" in row:
            self.value = row["value"]
            self.shape_id = row["shape_id"]

    def has_value(self) -> bool:
        return self.value is not None

    def set_requested_ts(self, when: dt.date) -> None:
        self.requested_ts = when

    def set_requested_shape(self, shape: Shape) -> None:
        self.requested_shape = shape

    def is_derived_value(self) -> bool:
        # check if either is derived!
        return self.is_derived_temporal() or self.is_derived_spatial()

    def is_derived_spatial(self) -> bool:
        return (
            self.requested_shape is not None
            and self.requested_shape.id != self.shape_id
        )

    def is_derived_temporal(self):
        if self.requested_ts is not None and self.result is not None:
            match self.dl.temporal_resolution:
                case LayerTimeResolution.YEAR:
                    if "year" in self.result:
                        return self.requested_ts.year != int(self.result["year"])
                case LayerTimeResolution.MONTH:
                    date1 = self.requested_ts
                    date2 = self.result["month"]
                    return not (date1.year == date2.year and date1.month == date2.month)

                case LayerTimeResolution.WEEK:
                    date1 = self.requested_ts.isocalendar()
                    date2 = self.result["week"].isocalendar()
                    return not (date1.year == date2.year and date1.week == date2.week)

                case LayerTimeResolution.DAY:
                    date1 = self.requested_ts
                    date2 = self.result["date"]
                    return not (
                        date1.year == date2.year
                        and date1.month == date2.month
                        and date1.day == date2.day
                    )

                case _:
                    msg = f"Unknown time_col={self.dl.temporal_resolution}"
                    raise ValueError(msg)

        return False

    def date(self):
        if self.result is None:
            return None

        match self.dl.temporal_resolution:
            case LayerTimeResolution.YEAR:
                if "year" in self.result:
                    return self.result["year"]
                return None
            case LayerTimeResolution.MONTH:
                if "month" in self.result:
                    return self.result["month"].strftime("%Y-%m")
                return None
            case LayerTimeResolution.WEEK:
                if "date" in self.result:
                    return self.result["week"].strftime("%Y-W%V")
                return None
            case LayerTimeResolution.DAY:
                if "date" in self.result:
                    return self.result["date"].strftime("%Y-%m-%d")
                return None

            case _:
                msg = f"Unknown time_col={self.dl.temporal_resolution}"
                raise ValueError(msg)

    def shape(self) -> Shape | None:
        if self.shape_id:
            return Shape.objects.get(pk=self.shape_id)
        return None

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


class DatalayerManager(models.Manager):
    def get_datalayers(self, keys: list[str]):
        return self.filter(key__in=keys)

    def get_by_natural_key(self, key):
        return self.get(key=key)

    def filter_by_key(self, key: str):
        """Key can be an exact match or a regex."""
        if key.replace("_", "").isalnum():
            return self.filter(key=key)

        return self.filter(key__iregex=key)


class Datalayer(models.Model):
    DATA_TYPES = (
        ("primary", _("Primary data")),
        ("secondary", _("Secondary data")),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    key = models.SlugField(
        max_length=255,
        null=False,
        unique=True,
        help_text=_(
            "Unique key identifying this Data Layer, use only <code>a-z</code>, <code>0-9</code> and <code>_</code>. Follow the convention of <code>&lt;source&gt;_&lt;parameter&gt;</code>."
        ),
    )
    data_type = models.CharField(
        max_length=10,
        choices=DATA_TYPES,
        default="secondary",
        verbose_name=_("Data type"),
        help_text=_(
            "Highlight if this Data Layer uses primary, i.e., you own data, or if it uses secondary data from someone else."
        ),
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="datalayers",
        blank=True,
        null=True,
    )
    tags = TaggableManager(blank=True)

    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        help_text=_(
            'Description of the Data Layer. You can use <a href="https://www.markdownguide.org/cheat-sheet/" target="_blank">Markdown</a> for text formatting, including tables and footnotes.'
        ),
    )
    caveats = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        help_text=_(
            'Describe known issues and caveats of the Data Layer. You can use <a href="https://www.markdownguide.org/cheat-sheet/" target="_blank">Markdown</a> for text formatting, including tables and footnotes.'
        ),
    )

    # Data Layer metadata and processing
    # original_unit    = models.CharField(max_length=255, blank=True)
    operation = models.TextField(
        blank=True,
        help_text=_(
            "Describe the operation performed to harmonize the raw data, i.e., mean, sum, …"
        ),
    )
    database_unit = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "Unit of the harmonized values of this Data Layer, i.e., °C, mm, entities, …"
        ),
    )

    date_included = models.DateField(blank=True, null=True, default=dt.date.today)
    related_to = models.ManyToManyField("self", blank=True)

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

    objects = DatalayerManager()

    # creator       = models.CharField(max_length=255, blank=True)
    # type          = models.CharField(max_length=255, blank=True)
    # identifier    = models.CharField(max_length=255, blank=True)

    _class_instance = None

    class Meta:
        ordering = (
            "key",
            "name",
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"

    def get_absolute_url(self):
        return reverse("datalayers:datalayer_detail", kwargs={"key": self.key})

    def natural_key(self):
        return (self.key,)

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
    def is_categorical(self) -> bool:
        if self.has_class():
            return self.get_class().value_type in [
                LayerValueType.NOMINAL,
                LayerValueType.ORDINAL,
            ]

        return False

    @property
    def value_type_str(self) -> str | None:
        if self.has_class():
            return str(self._get_class().value_type)

        return None

    def get_categorical_values(self) -> list[str]:
        if self.has_class():
            if self.value_type == LayerValueType.NOMINAL:
                return list(self.get_class().nominal_values)
            if self.value_type == LayerValueType.ORDINAL:
                return list(self.get_class().ordinal_values)
        return []

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

    def error(self, message, context=None):
        self.log(DatalayerLogEntry.ERROR, message, context=context)

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
            case LayerTimeResolution.MONTH:
                query = sql.SQL(
                    "SELECT DATE_PART('year', month ::date) AS year \
                FROM {table} WHERE month is not NULL GROUP BY year ORDER BY year DESC"
                ).format(table=sql.Identifier(self.key))
            case LayerTimeResolution.WEEK:
                query = sql.SQL(
                    "SELECT DATE_PART('year', week ::date) AS year \
                FROM {table} WHERE week is not NULL GROUP BY year ORDER BY year DESC"
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

    def get_available_months(self) -> list[dt.date]:
        if not self.is_loaded():
            # self.logger.warning("Peek of data requested but not loaded for shape_id=%s", shape_id)
            return []

        match self.temporal_resolution:
            case LayerTimeResolution.MONTH:
                query = sql.SQL(
                    "SELECT DISTINCT month FROM {table} ORDER BY month DESC"
                ).format(table=sql.Identifier(self.key))
            case _:
                raise ValueError(
                    "Function get_available_months is not defined for Data Layers with time_col != month"
                )

        with connection.cursor() as c:
            c.execute(query)
            results = c.fetchall()

        months = []
        for row in results:
            months.append(row[0])

        return months

    def get_available_weeks(self) -> list[dt.date]:
        if not self.is_loaded():
            # self.logger.warning("Peek of data requested but not loaded for shape_id=%s", shape_id)
            return []

        match self.temporal_resolution:
            case LayerTimeResolution.WEEK:
                query = sql.SQL(
                    "SELECT DISTINCT week FROM {table} ORDER BY week DESC"
                ).format(table=sql.Identifier(self.key))
            case _:
                raise ValueError(
                    "Function get_available_weeks is not defined for Data Layers with time_col != week"
                )

        with connection.cursor() as c:
            c.execute(query)
            results = c.fetchall()

        months = []
        for row in results:
            months.append(row[0])

        return months

    def _import_and_create_class(self) -> BaseLayer:
        # spec = importlib.util.spec_from_file_location("module.name", settings.DATAHUB_DATALAYER_DIR)

        mod = __import__(f"src.datalayer.{self.key}", fromlist=[camel(self.key)])
        cls = getattr(mod, camel(self.key))()
        cls.layer = self
        return cls

    def get_class(self):
        if self._class_instance is None:
            self._class_instance = self._import_and_create_class()
        return self._class_instance

    def _get_class(self):
        return self.get_class()

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

    def is_available(self) -> bool:
        """
        Check if a Data Layer has a class and is loaded into the database.

        It's important to check for both, because downloading/working with data depends
        on the source file to be present, i.e., for time_col. A loaded Data Layer
        without it's source file ise unusable.
        """
        has_class = self.has_class()
        is_loaded = self.is_loaded()

        if is_loaded and not has_class:
            # this get's logged b/c we have a loaded datalayer class WITHOUT a source
            # file. That shouldn't happen!
            logger.warning("datalayer class is missing key=%s", self.key)

        return has_class and is_loaded

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

    def reset(self, *, data: bool = True, log: bool = False):
        if not self.is_loaded():
            return

        # drop processed dat
        if data:
            query = sql.SQL("DROP TABLE {table}").format(table=sql.Identifier(self.key))

            with connection.cursor() as c:
                c.execute(query)

        # drop log for data layer
        if log:
            self.logentries.all().delete()

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
        """Select a single value of the Data Layer for a shape and optional timestamp."""
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
            elif self.temporal_resolution == LayerTimeResolution.MONTH:
                query += "AND dl.month {operator} %(when)s "
                params["when"] = when
            elif self.temporal_resolution == LayerTimeResolution.WEEK:
                query += "AND dl.week {operator} %(when)s "
                # Monday of the ISO week where the given date is in
                params["when"] = when - dt.timedelta(days=when.isoweekday() - 1)
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
            if self.temporal_resolution == LayerTimeResolution.YEAR and isinstance(
                start_date, dt.date
            ):
                start_date = start_date.year

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

        return pd.read_sql(
            query.as_string(connection), con=get_conn_string(), params=params
        )

    def value_coverage(self, shape_type: Optional[Type] = None) -> float:
        if not self.is_loaded():
            return None

        expected = self.expected_value_count(shape_type)
        actual = self.count_values(shape_type)

        if expected is None or actual is None:
            return None

        return actual / expected

    def expected_value_count(self, shape_type: Type | None = None) -> int:
        if not self.is_loaded():
            return None

        first = self.first_time(shape_type)
        last = self.last_time(shape_type)

        if first is None or last is None:
            return None

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
            case LayerTimeResolution.WEEK:
                # last and first are each the monday of the corresponding week
                # to divide correctly we need all days of the last week, so we add 7
                delta_days = (last - first).days + 7
                delta_weeks = delta_days // 7

                return delta_weeks * type_multiplier

            case LayerTimeResolution.MONTH:
                return (
                    (last.year - first.year) * 12 + (last.month - first.month) + 1
                ) * type_multiplier
            case _:
                raise ValueError(f"Unknown time_col={self.temporal_resolution}")

    def count_values(self, shape_type: Type | None = None):
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
            case LayerTimeResolution.WEEK:
                query = "SELECT dl.week FROM {table} AS dl "
                query_order = "ORDER BY week ASC LIMIT 1"
            case LayerTimeResolution.MONTH:
                query = "SELECT dl.month FROM {table} AS dl "
                query_order = "ORDER BY month ASC LIMIT 1"
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

        if not result:
            return None

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
            case LayerTimeResolution.WEEK:
                query = "SELECT dl.week FROM {table} AS dl "
                query_order = "ORDER BY week DESC LIMIT 1"
            case LayerTimeResolution.MONTH:
                query = "SELECT dl.month FROM {table} AS dl "
                query_order = "ORDER BY month DESC LIMIT 1"
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

        if not result:
            return None

        return result[0]

    # ---

    def download(self):
        """Automatic download of data source files."""
        start = timer()
        self.info("Starting download")
        cls = self.get_class()
        cls.download()
        end = timer()
        self.info("Finished download", {"end": end, "duration": end - start})

    def process(self, *args, **kwargs):
        """Consume/calculate data to insert into the database."""
        start = timer()
        self.info("Starting processing")

        cls = self.get_class()
        cls.process(*args, **kwargs)

        end = timer()
        self.info("Finished processing", {"duration": end - start})


class SourceMetadataManager(models.Manager):
    def get_by_natural_key(self, *arg):
        # The SourceMetaData model depends always on a parent DataLayer model. So after
        # deserializing it should always create a new record. To achieve this:
        # a) the natural_key() methods returns (None, ) tp prevent the creation of a pk
        # entry in the export
        # b) this methods just returns a new instance of the SourceMetadata class to force
        # the creation of a new record.
        return SourceMetadata()


class SourceMetadata(models.Model):
    SOURCE_TYPES = (
        ("data", _("Data source")),
        ("information", _("Further information")),
    )

    DISTANCE_TYPES = (
        ("meters", _("Meters")),
        ("kilometers", _("Kilometers")),
        ("degrees", _("Degrees")),
    )

    class SourcePIDType(models.TextChoices):
        DOI = "DOI", _("DOI")
        ROR = "ROR", _("ROR")
        ORCID = "ORCID", _("ORCID")
        URL = "URL", _("URL")
        URN = "URN", _("URN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    position = models.PositiveSmallIntegerField(
        default=0,
        help_text=_(
            "Field to order the meta data entries, if 0 will appended to at the end."
        ),
    )

    datalayer = models.ForeignKey(
        Datalayer,
        on_delete=models.CASCADE,
        related_name="sources",
    )

    pid_type = models.CharField(
        max_length=255,
        choices=SourcePIDType,
        default="",
        blank=True,
        verbose_name=_("PID type"),
        help_text=_("In case of URL put the URL into the PID field."),
    )
    pid = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("PID"),
        help_text=_(
            "Fetching DOI data will overwrite name, license and DataCite fields."
        ),
    )

    metadata_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES,
        default="data",
        verbose_name=_("Metadata type"),
        help_text=_(
            "Differentiate if this an actual data source of the Data Layer or further information."
        ),
    )
    use_for_citation = models.BooleanField(
        default=True,
        help_text=_(
            "Should this source be used in the aggregated citation information of this Data Layer?"
        ),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(  # noqa: DJ001
        blank=True,
        null=True,
        help_text=_(
            'Description of the source. You can use <a href="https://www.markdownguide.org/cheat-sheet/" target="_blank">Markdown</a> for text formatting, including tables and footnotes.'
        ),
    )

    source_name = models.CharField(blank=True, null=True)
    source_link = models.URLField(blank=True, null=True, max_length=2000)

    # Data Hub relevant metadata
    format = models.CharField(
        max_length=255,  # 255 is max length of MIME type per RFC 4288 and RFC 6838
        blank=True,
        help_text=_(
            'File type of the source, preferable it\'s MIME type, see <a target="_blank" href="https://www.iana.org/assignments/media-types/media-types.xhtml">list of available types</a>'
        ),
    )
    format_unit = models.CharField(max_length=255, blank=True)
    format_api = models.BooleanField(
        default=False,
        verbose_name=_("Source is an API"),
        help_text=_(
            "Check, if the source data are dynamically requested from an API. Use format field to specify the format of the data returned by the API, i.e., JSON."
        ),
    )

    spatial_epsg = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("EPSG-Code"),
        help_text=_("EPSG ID of the data source."),
    )

    spatial_coverage = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "What extend of the world dose the source cover, i.e., <code>global</code>, country code (ISO 3611-1 alpha3 preferred, separate by , in case of multiple), degrees"
        ),
    )

    spatial_coverage_west_bound_longitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name=_("[Raster] West (←) bound"),
        help_text=_("Westernmost coordinate (Longitude, -180 to 180)."),
    )
    spatial_coverage_east_bound_longitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name=_("[Raster] East (→) bound"),
        help_text=_("Easternmost coordinate (Longitude, -180 to 180)."),
    )
    spatial_coverage_south_bound_latitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=8,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name=_("[Raster] South (↓) bound"),
        help_text=_("Southernmost coordinate (Latitude, -90 to 90)."),
    )
    spatial_coverage_north_bound_latitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=8,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name=_("[Raster] North (↑) bound"),
        help_text=_("Northernmost coordinate (Latitude, -90 to 90)."),
    )

    spatial_resolution = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "Resolution of the source, i.e., x km for raster data, <code>coordinates</code> for Points, administrative unit/region for vector files."
        ),
    )

    spatial_resolution_x_distance = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("[Raster] cell width value"),
    )
    spatial_resolution_x_unit = models.CharField(
        null=True,
        blank=True,
        choices=DISTANCE_TYPES,
        verbose_name=_("[Raster] cell width unit"),
    )

    spatial_resolution_y_distance = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("[Raster] height value"),
    )
    spatial_resolution_y_unit = models.CharField(
        null=True,
        blank=True,
        choices=DISTANCE_TYPES,
        verbose_name=_("[Raster] cell height unit"),
    )

    temporal_resolution = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "Temporal resolution, like annually, monthly, cross sectional for single points."
        ),
    )
    temporal_coverage_start = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "First temporal point of the source, use ISO format like yyyy[-mm[-dd]]."
        ),
    )
    temporal_coverage_end = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "Last temporal point of the source, use ISO format like yyyy[-mm[-dd]]. For continuously updated sources use ongoing"
        ),
    )

    language = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'Prefer ISO 639-3 language code (3 letters), see <a target="_blank" href="https://iso639-3.sil.org/code_tables/639/data">SIL for full list</a>. Other ISO 639 codes are allowed as well.'
        ),
    )
    license = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("SPDX identifier of the given license if available"),
    )
    date_published = models.CharField(
        blank=True,
        help_text=_("Year of publication in yyyy format."),
    )  # no date field. maybe only a year is known.

    date_last_accessed = models.DateField(blank=True, null=True)

    citation_plain = models.TextField(blank=True)
    citation_bibtex = models.TextField(blank=True)

    # DataCite
    datacite = models.JSONField(null=True, blank=True)
    datacite_fetched_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = SourceMetadataManager()

    class Meta:
        ordering = (
            "datalayer",
            "position",
        )

    # this model has a pre_save signal in signals.py

    def __str__(self) -> str:
        return f"{self.name}"

    def natural_key(self):
        # see comment above in SourceMetadataManager.get_by_natural_key()
        return (None,)

    @property
    def has_spatial_coverage_bbox(self) -> bool:
        """Check if all four directions of the bounding box are set."""
        return (
            self.spatial_coverage_west_bound_longitude
            and self.spatial_coverage_east_bound_longitude
            and self.spatial_coverage_north_bound_latitude
            and self.spatial_coverage_south_bound_latitude
        )

    @property
    def has_spatial_coverage_cell_dimension(self) -> bool:
        """Check if all information for the cell dimensions are set."""
        return (
            self.spatial_resolution_x_distance
            and self.spatial_resolution_x_unit
            and self.spatial_resolution_y_distance
            and self.spatial_resolution_y_unit
        )

    def related_item(self, pid_type, pid):
        dl = self.datalayer

        for source in dl.sources.all():
            if source.pid_type == pid_type and source.pid == pid:
                return source

        return None


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
        on_delete=models.CASCADE,
        related_name="logentries",
    )

    level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    context = models.JSONField(default=list)
