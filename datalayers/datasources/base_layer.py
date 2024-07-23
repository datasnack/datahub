import os
import subprocess
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import geopandas
import pandas as pd
from psycopg import sql

from django.db import connection

from datalayers.utils import get_engine


class LayerTimeResolution(Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "date"

    def __str__(self) -> str:
        return str(self.value)


class LayerValueType(Enum):
    VALUE = "value"
    PERCENTAGE = "percentage"
    BINARY = "binary"

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
                return f"{round(value * 100, self.precision)} %"
            case LayerValueType.VALUE:
                fmt = str(round(value, self.precision))
                if self.format_suffix:
                    fmt += f" {self.format_suffix}"
                return fmt
            case _:
                return value

    def save(self):
        if self.df is None:
            self.df = pd.DataFrame(self.rows)

        if self.output == "db":
            self.df.to_sql(self.layer.key, get_engine(), if_exists="replace")
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
            self.layer.warning(
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
        """).format(table=sql.Identifier(self.raw_vector_data_table))

        with connection.cursor() as c:
            c.execute(query)
            result = c.fetchone()

        if result:
            return result[0]

        return None
