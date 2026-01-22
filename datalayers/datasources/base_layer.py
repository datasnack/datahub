# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt
import os
import subprocess
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import geopandas
import numpy as np
import pandas as pd
from psycopg import sql

from django.db import connection
from django.utils import formats

from datalayers.utils import get_conn_string, get_engine


class LayerTimeResolution(Enum):
    YEAR = "year"
    MONTH = "month"
    # ISO8601 week, starts on Monday. Week 01 is the week containing Jan 4.
    WEEK = "week"
    DAY = "date"

    def __str__(self) -> str:
        return str(self.value)

    def string(self) -> str:
        """Duplicated str method so we can call .string in Django templates."""
        return str(self.value)

    def letter(self) -> str:
        """Unique letter/string describing the temporal resolution."""
        if self == LayerTimeResolution.YEAR:
            return "Y"
        if self == LayerTimeResolution.MONTH:
            return "m"
        if self == LayerTimeResolution.WEEK:
            return "W"  # %V is the ISO8601 week
        if self == LayerTimeResolution.DAY:
            return "d"

        raise ValueError("Unsupported time resolution")

    def format(self) -> str:
        if self == LayerTimeResolution.YEAR:
            return "%Y"
        if self == LayerTimeResolution.MONTH:
            return "%Y-%m"
        if self == LayerTimeResolution.WEEK:
            return "%Y-W%V"  # %V is the ISO8601 week
        if self == LayerTimeResolution.DAY:
            return "%Y-%m-%d"

        raise ValueError("Unsupported time resolution")


class LayerValueType(Enum):
    VALUE = "value"
    FLOAT = "float"
    INTEGER = "integer"
    PERCENTAGE = "percentage"
    BINARY = "binary"
    NOMINAL = "nominal"  # categorical without natural order
    ORDINAL = "ordinal"  # categorical with natural order (i.e., low < medium < high)

    def __str__(self) -> str:
        return str(self.value)


class BaseLayer:
    def __init__(self) -> None:
        self.layer = None
        self.output = "db"
        self.rows = []
        self.df = None

        self.time_col: LayerTimeResolution = LayerTimeResolution.YEAR
        self.value_type: LayerValueType = LayerValueType.VALUE

        self.nominal_values = []
        self.ordinal_values = []

        # line or bar chart
        self.chart_type = "line"

        # Set this to a table name, in that the download method stores raw
        # data, it's expected that those raw data contain a geometry column
        # with some sort of geometry (POINT, POLYGON, ...)
        # Should have the prefix data_
        self.raw_vector_data_table = None

        # How many decimal digits should be displayed?
        # Only used in UI for human on the web, API and CSV data are never rounded
        self.precision = 2

        # Optional suffix for formatting human readable values
        self.format_suffix = None

    @property
    def key(self):
        return self.layer.key

    def download(self):
        """Automatic download of data source files."""
        raise NotImplementedError

    def process(self):
        """Consume/calculate data to insert into the database."""
        raise NotImplementedError

    def get_data_path(self) -> Path:
        """Path to where to store the data of the layer."""
        return Path(f"./data/datalayers/{self.layer.key}/")

    def str_format(self, value) -> str:
        match self.value_type:
            case LayerValueType.PERCENTAGE:
                return f"{formats.number_format(round(value * 100, self.precision))} %"
            case LayerValueType.FLOAT | LayerValueType.VALUE:
                fmt = formats.number_format(round(value, self.precision))
                if self.format_suffix:
                    fmt += f" {self.format_suffix}"
                return fmt
            case _:
                return value

    def is_valid_temporal(self, temporal) -> bool:
        match self.time_col:
            case LayerTimeResolution.YEAR:
                return isinstance(temporal, int)
            case LayerTimeResolution.MONTH:
                if isinstance(temporal, dt.datetime):
                    return False
                return isinstance(temporal, dt.date) and temporal.day == 1
            case LayerTimeResolution.WEEK:
                if isinstance(temporal, dt.datetime):
                    return False
                if not isinstance(temporal, dt.date):
                    return False
                return (
                    temporal.weekday() == 0
                )  # date must be a monday on which the CW starts
            case LayerTimeResolution.DAY:
                if isinstance(temporal, dt.datetime):
                    return False
                return isinstance(temporal, dt.date)
            case _:
                raise ValueError("Unsupported time resolution")

    def is_valid_value(self, value) -> bool:
        match self.value_type:
            case LayerValueType.PERCENTAGE:
                return (
                    isinstance(value, (float, np.floating))
                    and value >= 0.0
                    and value <= 1.0
                )
            case LayerValueType.BINARY:
                return isinstance(value, bool)
            case LayerValueType.NOMINAL:
                return value in self.nominal_values
            case LayerValueType.ORDINAL:
                return value in self.ordinal_values
            case LayerValueType.INTEGER:
                return isinstance(value, int)
            case LayerValueType.FLOAT:
                return isinstance(value, (float, np.floating))
            case LayerValueType.VALUE:
                return True  # no validation of VALUE type
            case _:
                raise ValueError("Unsupported value type")

    def add_value(self, shape, temporal, value, *, validate_value=True):
        """Add new value to Data Layer during processing. Includes type checks for temporal and actual value."""
        if not self.is_valid_temporal(temporal):
            raise ValueError(
                f"Temporal value ({temporal}) is not matching Data Layer ({self.time_col})."
            )

        if validate_value and not self.is_valid_value(value):
            raise ValueError(
                f"Processed value ({value}) is not matching Data Layer ({self.value_type})."
            )

        self.rows.append(
            {
                f"{str(self.time_col)}": temporal,
                "shape_id": shape.id,
                "value": value,
            }
        )

    def has_value(self, shape, temporal) -> bool:
        """Check if a value for the given shape/temporal is already collected."""
        for row in self.rows:
            if row["shape_id"] == shape.id and row[f"{str(self.time_col)}"] == temporal:
                return True

        return False

    def len_values(self) -> int:
        """Get the amount of added values."""
        return len(self.rows)

    def save(self):
        if self.df is None:
            self.df = pd.DataFrame(self.rows)

        if self.output == "db":
            self.df.to_sql(
                self.layer.key, get_engine(), index=False, if_exists="replace"
            )
        elif self.output == "fs":
            self.df.to_csv(self.get_data_path() / f"{self.layer.key}.csv", index=False)
        else:
            raise ValueError(f"Unknown save option {self.output}.")

    def _create_data_dir_if_not_exists(self) -> None:
        Path(self.get_data_path()).mkdir(parents=True, exist_ok=True)

    def _save_url_to_file(self, url, folder=None, file_name=None) -> bool:
        """
        Save file from a URL to local directory.

        Checks if file has already been downloaded. Return True in case
        file was downloaded/was already downloaded, otherwise False.
        """
        a = urlparse(url)

        if file_name is None:
            file_name = os.path.basename(a.path)

        if folder is None:
            folder = self.get_data_path()

        if os.path.isfile(folder / file_name):
            # self.logger.debug("Skipping b/c already downloaded %s", url)
            return True

        Path(folder).mkdir(parents=True, exist_ok=True)

        try:
            # call wget to download file
            params = ["wget", "-O", folder / file_name, url]
            subprocess.check_output(params)

            # calculate and log md5 of downloaded file
            md5_output = subprocess.check_output(
                ["md5sum", folder / file_name], text=True
            )
            md5 = md5_output.split(" ", maxsplit=1)[0]
            self.layer.info(
                "Downloaded file",
                {"url": url, "file": (folder / file_name).as_posix(), "md5": md5},
            )

            return True
        except subprocess.CalledProcessError as error:
            # -O on wget will create the file regardless if it did exits and
            # could be downloaded. To don't have any empty files, we remove it
            if os.path.exists(folder / file_name):
                os.remove(folder / file_name)

            self.layer.warning(
                "Could not download file: %s, %s",
                {"url": url, "error_msg": error.stderr},
            )

            # self.logger.warning("Could not download file: %s, %s", url, error.stderr)

        return False

    def _get_convex_hull_from_db(self):
        """
        Create the convex hull of all loaded shapes and return it.

        Be aware that, the convex hull will include MORE area than the actual
        shapes. Nevertheless it is much faster than UNION/Dissolve of existing
        shapes. Since the function is usually called for extracting from a source
        and in the loading stage an individual mapping for shape/AOI is performed
        , this is not an issue.
        """
        sql = "SELECT ST_ConvexHull(ST_Collect(shape.geometry)) as geometry FROM shapes_shape AS shape"

        gdf = geopandas.GeoDataFrame.from_postgis(
            sql, get_engine(), geom_col="geometry"
        )

        if len(gdf) == 0:
            raise ValueError("No shapes found in database.")

        return gdf.at[0, "geometry"]

    def vector_data_map(self):
        if self.raw_vector_data_table is None:
            return None

        # This query uses ST_AsGeoJSON(t.*) to select a single row of a postgis
        # table as GeoJSON geometry. with the `*` all columns that are not the
        # geometry are read into the GeoJSONs properties.
        # With json_build_object() we aggregate the single Features from the rows
        # into a feature collection which we can directly use on a map, i.e.
        query = sql.SQL("""
        WITH data AS (
            SELECT ST_AsGeoJSON(t.*)::json as feature FROM {table} as t
        )
        SELECT
        json_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(
            feature
            )
        ) AS geojson
        FROM data
        """).format(table=sql.Identifier(self.get_vector_data_table()))

        with connection.cursor() as c:
            c.execute(query)
            result = c.fetchone()

        if result:
            return result[0]

        return None

    def get_vector_data_table(self) -> str | None:
        if not self.raw_vector_data_table:
            return None

        return f"data_{self.key}"

    def write_vector_data_to_db(self, gdf):
        gdf.to_postgis(
            self.get_vector_data_table(),
            con=get_engine(),
            index=False,
            if_exists="replace",
        )

    def get_vector_data_df(self) -> pd.DataFrame:
        if self.raw_vector_data_table is None:
            raise Exception("Data Layer has no configures vector data table")

        query = sql.SQL("SELECT * FROM {table}").format(
            table=sql.Identifier(self.get_vector_data_table())
        )

        return geopandas.read_postgis(
            query.as_string(connection), con=get_conn_string(), geom_col="geometry"
        )
