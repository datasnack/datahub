# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import os
import re
from pathlib import Path

import numpy as np

from datalayers.datasources.base_layer import LayerValueType
from datalayers.datasources.tiff_layer import TiffLayer


class CopernicusLayer(TiffLayer):
    """Extends TiffParameter class for Copernicus consumption."""

    def __init__(self) -> None:
        super().__init__()

        self.value_type = LayerValueType.PERCENTAGE
        self.precision = 2

        self.area_of_interest = []

        self.mapping = [
            {"meaning": "unknown", "value": 0, "color": "#282828"},
            {"meaning": "ENF_closed", "value": 111, "color": "#564925"},
            {"meaning": "EBF_closed", "value": 112, "color": "#43972a"},
            {"meaning": "DNF_closed", "value": 113, "color": "#6f6743"},
            {"meaning": "DBF_closed", "value": 114, "color": "#5cc93b"},
            {"meaning": "mixed_closed", "value": 115, "color": "#56742e"},
            {"meaning": "unknown_closed", "value": 116, "color": "#33761f"},
            {"meaning": "ENF_open", "value": 121, "color": "#65601b"},
            {"meaning": "EBF_open", "value": 122, "color": "#95b336"},
            {"meaning": "DNF_open", "value": 123, "color": "#897523"},
            {"meaning": "DBF_open", "value": 124, "color": "#addb44"},
            {"meaning": "mixed_open", "value": 125, "color": "#93992f"},
            {"meaning": "unknown_open", "value": 126, "color": "#6c8b28"},
            {"meaning": "shrubland", "value": 20, "color": "#f4be4a"},
            {"meaning": "herbaceous_vegetation", "value": 30, "color": "#ffff6e"},
            {"meaning": "cropland", "value": 40, "color": "#e49af9"},
            {"meaning": "built-up", "value": 50, "color": "#e63222"},
            {"meaning": "bare_sparse_vegetation", "value": 60, "color": "#f0f0f0"},
            {"meaning": "snow_ice", "value": 70, "color": "#f0f0f0"},
            {"meaning": "permanent_inland_water", "value": 80, "color": "#1131c0"},
            {"meaning": "herbaceous_wetland", "value": 90, "color": "#41939f"},
            {"meaning": "moss_lichen", "value": 100, "color": "#f7e7a8"},
            {"meaning": "sea", "value": 200, "color": "#00037a"},
        ]

    def get_data_path(self) -> Path:
        """Overwrite input directory, b/c we have multiple derived layers from this source."""
        return Path("./data/datalayers/copernicus_landcover/")

    def download(self):
        # pylint: disable=line-too-long
        urls = [
            "https://zenodo.org/records/3939050/files/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif?download=1",
            "https://zenodo.org/records/3518038/files/PROBAV_LC100_global_v3.0.1_2018-conso_Discrete-Classification-map_EPSG-4326.tif?download=1",
            "https://zenodo.org/records/3518036/files/PROBAV_LC100_global_v3.0.1_2017-conso_Discrete-Classification-map_EPSG-4326.tif?download=1",
            "https://zenodo.org/records/3518026/files/PROBAV_LC100_global_v3.0.1_2016-conso_Discrete-Classification-map_EPSG-4326.tif?download=1",
            "https://zenodo.org/records/3939038/files/PROBAV_LC100_global_v3.0.1_2015-base_Discrete-Classification-map_EPSG-4326.tif?download=1",
        ]
        # pylint: enable=line-too-long

        for url in urls:
            self._save_url_to_file(url, folder=self.get_data_path())

    def get_value_for_key(self, key) -> int:
        """Return the value used for a land usage key."""
        for item in self.mapping:
            if item["meaning"] == key:
                return item["value"]

        raise ValueError(f"Unknown Copernicus mapping key: {key}.")

    def consume(self, file, band, shape):
        x = re.search(r"([0-9]{4})", os.path.basename(file))
        year = int(x[1])

        total_cells = np.count_nonzero(~np.isnan(band))
        values, count = np.unique(band, return_counts=True)
        stats = dict(zip(values, count))

        aoi_cells = 0
        for key in self.area_of_interest:
            val = self.get_value_for_key(key)

            if val in stats:
                aoi_cells += stats[val]

        self.rows.append(
            {
                "year": year,
                "shape_id": shape.id,
                "value": aoi_cells / total_cells,
            }
        )
