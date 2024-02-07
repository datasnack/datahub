import os
import re
from pathlib import Path

import numpy as np

from datalayers.datasources.tiff_layer import TiffLayer

class CopernicusLayer(TiffLayer):
    """ Extends TiffParameter class for Copernicus consumption. """

    def __init__(self):
        super().__init__()

        self.is_percent = True

        self.area_of_interest = []

        self.mapping = [{
            "meaning": "unknown",
            "value": 0
        },
        {
            "meaning": "ENF_closed",
            "value": 111
        },
        {
            "meaning": "EBF_closed",
            "value": 112
        },
        {
            "meaning": "DNF_closed",
            "value": 113
        },
        {
            "meaning": "DBF_closed",
            "value": 114
        },
        {
            "meaning": "mixed_closed",
            "value": 115
        },
        {
            "meaning": "unknown_closed",
            "value": 116
        },
        {
            "meaning": "ENF_open",
            "value": 121
        },
        {
            "meaning": "EBF_open",
            "value": 122
        },
        {
            "meaning": "DNF_open",
            "value": 123
        },
        {
            "meaning": "DBF_open",
            "value": 124
        },
        {
            "meaning": "mixed_open",
            "value": 125
        },
        {
            "meaning": "unknown_open",
            "value": 126
        },
        {
            "meaning": "shrubland",
            "value": 20
        },
        {
            "meaning": "herbaceous_vegetation",
            "value": 30
        },
        {
            "meaning": "cropland",
            "value": 40
        },
        {
            "meaning": "built-up",
            "value": 50
        },
        {
            "meaning": "bare_sparse_vegetation",
            "value": 60
        },
        {
            "meaning": "snow_ice",
            "value": 70
        },
        {
            "meaning": "permanent_inland_water",
            "value": 80
        },
        {
            "meaning": "herbaceous_wetland",
            "value": 90
        },
        {
            "meaning": "moss_lichen",
            "value": 100
        },
        {
            "meaning": "sea",
            "value": 200
        }]

    def get_data_path(self) -> Path:
        """ Overwrite parameter_id based input directory, because we have
        multiple derives parameters from this source. """
        return Path("./data/datalayers/copernicus_landcover/")

    def download(self):

        # pylint: disable=line-too-long
        urls = [
            'https://zenodo.org/records/3939050/files/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif?download=1',
            'https://zenodo.org/records/3518038/files/PROBAV_LC100_global_v3.0.1_2018-conso_Discrete-Classification-map_EPSG-4326.tif?download=1',
            'https://zenodo.org/records/3518036/files/PROBAV_LC100_global_v3.0.1_2017-conso_Discrete-Classification-map_EPSG-4326.tif?download=1',
            'https://zenodo.org/records/3518026/files/PROBAV_LC100_global_v3.0.1_2016-conso_Discrete-Classification-map_EPSG-4326.tif?download=1',
            'https://zenodo.org/records/3939038/files/PROBAV_LC100_global_v3.0.1_2015-base_Discrete-Classification-map_EPSG-4326.tif?download=1'
        ]
        # pylint: enable=line-too-long

        for url in urls:
            self._save_url_to_file(url, folder=self.get_data_path())


    def get_value_for_key(self, key) -> int:
        """ Returns the value used for a land usage key. """
        for item in self.mapping:
            if item['meaning'] == key:
                return item['value']

        raise ValueError(f"Unknown Copernicus mapping key: {key}.")

    def consume(self, file, band, shape):
        x = re.search(r'([0-9]{4})', os.path.basename(file))
        year = int(x[1])

        total_cells = np.count_nonzero(~np.isnan(band))
        values, count = np.unique(band, return_counts=True)
        stats = dict(zip(values, count))

        aoi_cells = 0
        for key in self.area_of_interest:
            val = self.get_value_for_key(key)

            if val in stats:
                aoi_cells += stats[val]

        self.rows.append({
            'year': year,
            'shape_id': shape.id,
            f'{self.layer.key}': aoi_cells / total_cells,
        })
