import datetime as dt
from pathlib import Path

import fiona
import geopandas
import pandas as pd
from meteostat import Daily, Hourly, Stations
from psycopg import sql
from shapely import wkt

from django.db import connection

from datalayers.utils import get_conn_string
from datalayers.datasources.base_layer import LayerTimeResolution, LayerValueType
from shapes.models import Shape

from .base_layer import BaseLayer


class MeteostatLayer(BaseLayer):
    def __init__(self) -> None:
        super().__init__()

        self.time_col = LayerTimeResolution.DAY
        self.value_type = LayerValueType.VALUE

        self.table_name = "meteostat_stations"
        self.raw_vector_data_table = "meteostat_stations"

        # Meteostat layer specifics
        self.meteo_mode = "daily"  # do we need daily or hourly data?
        self.col_of_interest = None

        # Meteostat can't handle Path() object
        Stations.cache_dir = self.get_data_path().as_posix()
        Daily.cache_dir = self.get_data_path().as_posix()
        Hourly.cache_dir = self.get_data_path().as_posix()

    def get_data_path(self) -> Path:
        """Overwrite parameter_id based input directory."""
        return Path("./data/datalayers/meteostat/")

    def stations(self) -> Stations:
        raise NotImplementedError

    def start(self) -> dt.datetime:
        raise NotImplementedError

    def end(self) -> dt.datetime:
        raise NotImplementedError

    def download(self):
        stations = Stations()

        # stations = stations.region("GH")

        stations = stations.bounds(
            (52.675507659705794, 13.088347600424314),
            (52.338245531668925, 13.761159130580843),
        )

        start = dt.datetime(2022, 1, 1, tzinfo=dt.UTC)
        end = dt.datetime(2022, 12, 31, tzinfo=dt.UTC)

        df = stations.fetch()

        # Meteostat ID is not always numerical. Safe the internal Meteostat ID
        # but add an numerical index for smooth PostGIS access
        df["meteostat_id"] = df.index
        df.insert(
            0, "meteostat_id", df.pop("meteostat_id")
        )  # move meteostat ID to second column (directly after index)

        df["id"] = range(1, len(df) + 1)
        df.insert(0, "id", df.pop("id"))

        gdf = geopandas.GeoDataFrame(
            df, geometry=geopandas.points_from_xy(df.longitude, df.latitude)
        )
        gdf = gdf.set_crs("epsg:4326")

        # loop over all stations and collect daily values
        dfs_daily = []
        dfs_hourly = []
        stations_with_no_data = []

        for _, row in gdf.iterrows():
            # daily
            self.layer.debug(
                "Fetching Daily %s (%s)",
                {"name": row["name"], "meteostat_id": row["meteostat_id"]},
            )
            data = Daily(row["meteostat_id"], start, end)
            data = data.fetch()

            self.layer.debug("Found Daily %s rows", len(data))
            data["meteostat_station_id"] = row["id"]

            if len(data) == 0:
                self.layer.info(
                    "Remove station (%s) due to no data in time range",
                    {"meteostat_id": row["meteostat_id"]},
                )
                stations_with_no_data.append(row["id"])
                continue  # in case we have no daily data, also do not query hourly data

            dfs_daily.append(data)

            # hourly
            self.layer.debug(
                "Fetching Hourly %s (%s)",
                {"name": row["name"], "meteostat_id": row["meteostat_id"]},
            )
            data = Hourly(row["meteostat_id"], start, end)
            data = data.fetch()

            self.layer.debug("Found Hourly %s rows", {"len": len(data)})
            data["meteostat_station_id"] = row["id"]
            dfs_hourly.append(data)

        # save to database
        gdf = gdf[
            ~gdf["id"].isin(stations_with_no_data)
        ]  # do not write empty stations to database
        gdf.to_postgis(self.table_name, connection, if_exists="replace")

        merged_df = pd.concat(dfs_daily)
        merged_df.to_sql("meteostat_daily", connection, if_exists="replace")

        merged_df = pd.concat(dfs_hourly)
        merged_df.to_sql("meteostat_hourly", connection, if_exists="replace")

    def get_station_data_for_shape(self, shape):
        # load all stations
        # explicitly set CRS to prevent automatic detection by SQL query for first item
        # this would call the @lru_cache annotated function https://github.com/geopandas/geopandas/blob/main/geopandas/io/sql.py#L469
        # with the given connection and the django ConnectionProxy type is not hashable.
        stations_gdf = geopandas.read_postgis(
            sql.SQL("SELECT * FROM {table}")
            .format(table=sql.Identifier(self.table_name))
            .as_string(connection),
            con=get_conn_string(),
            geom_col="geometry",
            crs="epsg:4326",  # see comment above
        )

        # get all stations inside shape
        gdfx = stations_gdf[stations_gdf.within(shape)].reset_index(drop=True)

        # no station inside shape. find nearest from centroid of shape
        if len(gdfx) == 0:
            query = sql.SQL(
                "SELECT * FROM {table} ORDER BY st_distance( \
                ST_SetSRID({table}.geometry, 4326), \
                ST_SetSRID(ST_GeomFromText(%(centroid)s), 4326) ) ASC LIMIT 1"
            ).format(
                table=sql.Identifier(self.table_name),
            )

            gdfx = geopandas.read_postgis(
                query.as_string(connection),
                con=get_conn_string(),
                params={"centroid": str(shape.centroid)},
                geom_col="geometry",
                crs="epsg:4326",  # see comment above
            )

        station_ids = list(gdfx["id"].unique())

        self.layer.debug(
            "Found stations: %s", {"station_ids": ",".join(map(str, station_ids))}
        )

        if len(station_ids) == 0:
            self.layer.warning("No stations found for shape")
            return pd.DataFrame()

        dfxs = []
        for sid in station_ids:
            table = "meteostat_daily"
            if self.meteo_mode == "hourly":
                table = "meteostat_hourly"

            dfx = pd.read_sql(
                sql.SQL(
                    "SELECT * FROM {table} WHERE meteostat_station_id = %(station_id)s"
                )
                .format(table=sql.Identifier(table))
                .as_string(connection),
                con=get_conn_string(),
                params={"station_id": sid},
            )
            dfxs.append(dfx)

        df = pd.DataFrame()
        if len(dfxs) == 1:
            df = dfxs[0]
        else:
            df = dfxs[0]

            for i in range(1, len(dfxs)):
                # set suffixes manually, for multiple merges, the _x, _y could be duplicate
                #
                # First: (mint) x (mint) -> mint_x, mint_y
                #
                # Second (mint_x, mint_y) x (mint) -> mint_x, mint_y, mint
                #
                # Third merge: (mint_x, mint_y, mint) x (mint) -> error
                # mint would each get _x and _y suffixes, but those already exists.
                # That's why we add the i in the suffix.
                df = df.merge(
                    dfxs[i], how="outer", on="time", suffixes=(f"_x{i}", f"_y{i}")
                )
        if len(df) == 0:
            self.layer.warning("No data found for stations inside shape")

        return df

    def process(self, shapes=None, save_output=False):
        dfns = []

        if shapes is None:
            shapes = Shape.objects.all()

        for shape in shapes:
            if isinstance(shape, Shape):
                # Shape uses the GeoDjango Model and so has not a shapely geometry
                # so convert it. amazing right?
                mask = [wkt.loads(shape.geometry.wkt)]
            elif "geometry" in shape:
                mask = [shape["geometry"]]
            elif "file" in shape:
                with fiona.open(shape["file"], "r") as shapefile:
                    mask = [feature["geometry"] for feature in shapefile]
            else:
                raise ValueError("No geometry found for given shape.")

            # for hourly values on ahum/rhum data layers on a country level (lots of stations)
            # the script crashes on the amount of data. since the value is probably
            # not useful anyway, we skip country level for now.
            # TODO:
            # if self.parameter_id in ['meteo_ahum', 'meteo_rhum'] and shape['type'] == 'country':
            #    continue

            df = self.get_station_data_for_shape(mask[0])

            if len(df) == 0:
                self.layer.warning(
                    "No data found for shape with id %s", {"shape_id": shape.id}
                )
                continue

            # copying to new dataframe might trigger warning, regarding modifying
            # the copy of a dataframe, that is not the case here
            pd.options.mode.chained_assignment = None  # default='warn'

            dfn = self.consume(df, shape)

            dfns.append(dfn)

        self.df = pd.concat(dfns)
        self.save()

    def consume(self, df, shape):
        filter_col = [col for col in df if col.startswith(self.col_of_interest)]

        dfn = df[["time"]]
        dfn = dfn.rename(columns={"time": "date"})

        dfn["date"] = dfn["date"].dt.date
        dfn["shape_id"] = shape.id
        dfn["value"] = df[filter_col].mean(axis=1)
        dfn["value_std"] = df[filter_col].std(axis=1)
        dfn["value_min"] = df[filter_col].min(axis=1)
        dfn["value_max"] = df[filter_col].max(axis=1)
        dfn["value_count"] = df[filter_col].count(axis=1)

        dfn = dfn[dfn["value"].notna()]

        return dfn
