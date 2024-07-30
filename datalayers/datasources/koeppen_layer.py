import subprocess
from enum import Enum
from pathlib import Path

import numpy as np

from datalayers.datasources.base_layer import LayerTimeResolution, LayerValueType
from datalayers.datasources.tiff_layer import TiffLayer


class KoeppenLayer(TiffLayer):
    """Extends TiffParameter class for Koeppen data consumption."""

    class ClimateTypes(Enum):
        Af = 1  # Tropical, rainforest
        Am = 2  # Tropical, monsoon
        Aw = 3  # Tropical, savannah
        BWh = 4  # Arid, desert, hot
        BWk = 5  # Arid, desert, cold
        BSh = 6  # Arid, steppe, hot
        BSk = 7  # Arid, steppe, cold
        Csa = 8  # Temperate, dry summer, hot summer
        Csb = 9  # Temperate, dry summer, warm summer
        Csc = 10  # Temperate, dry summer, cold summer
        Cwa = 11  # Temperate, dry winter, hot summer
        Cwb = 12  # Temperate, dry winter, warm summer
        Cwc = 13  # Temperate, dry winter, cold summer
        Cfa = 14  # Temperate, no dry season, hot summer
        Cfb = 15  # Temperate, no dry season, warm summer
        Cfc = 16  # Temperate, no dry season, cold summer
        Dsa = 17  # Cold, dry summer, hot summer
        Dsb = 18  # Cold, dry summer, warm summer
        Dsc = 19  # Cold, dry summer, cold summer
        Dsd = 20  # Cold, dry summer, very cold winter
        Dwa = 21  # Cold, dry winter, hot summer
        Dwb = 22  # Cold, dry winter, warm summer
        Dwc = 23  # Cold, dry winter, cold summer
        Dwd = 24  # Cold, dry winter, very cold winter
        Dfa = 25  # Cold, no dry season, hot summer
        Dfb = 26  # Cold, no dry season, warm summer
        Dfc = 27  # Cold, no dry season, cold summer
        Dfd = 28  # Cold, no dry season, very cold winter
        ET = 29  # Polar, tundra
        EF = 30  # Polar, frost

    def __init__(self) -> None:
        super().__init__()

        self.time_col = LayerTimeResolution.YEAR
        self.value_type = LayerValueType.PERCENTAGE

        self.climate_types: list[self.ClimateTypes] = []

    def get_data_path(self) -> Path:
        return Path("./data/datalayers/koeppen/")

    def download(self):
        url = "https://figshare.com/ndownloader/files/45057352"
        file_name = "koppen_geiger_tif.zip"

        if not Path.is_file(self.get_data_path() / file_name):
            self._save_url_to_file(
                url, folder=self.get_data_path(), file_name=file_name
            )

        if Path.is_file(self.get_data_path() / "legend.txt"):
            return
        try:
            in_file = self.get_data_path() / file_name
            out_dir = self.get_data_path().as_posix()

            subprocess.run(
                f"unzip {in_file} -d {out_dir}",
                shell=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            self.layer.warning("Could not unzip files: %s", error.stderr)

    def get_tiff_files(self, param_dir):
        # We ignore 2041_2070 and 2071_2099 since we are not interested in predictions.
        # Also we would need to decide on a specific scenario.
        folders = ["1901_1930", "1931_1960", "1961_1990", "1991_2020"]

        files = []
        for folder in folders:
            files.append(f"{folder}/koppen_geiger_0p00833333.tif")

        return files

    def consume(self, file, band, shape):
        total_cells = np.count_nonzero(~np.isnan(band))
        values, count = np.unique(band, return_counts=True)
        stats = dict(zip(values, count, strict=True))

        aoi_cells = 0
        for climate_type in self.climate_types:
            if climate_type.value in stats:
                aoi_cells += stats[climate_type.value]
        proportion = aoi_cells / total_cells

        year_start = int(file[0:4])
        year_end = int(file[5:9])

        for year in range(year_start, year_end + 1):
            self.rows.append(
                {
                    "year": year,
                    "shape_id": shape.id,
                    "value": proportion,
                }
            )
