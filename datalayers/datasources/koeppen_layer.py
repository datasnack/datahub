import os
import subprocess
from pathlib import Path

import numpy as np

from datalayers.datasources.base_layer import LayerTimeResolution, LayerValueType
from datalayers.datasources.tiff_layer import TiffLayer


class KoeppenLayer(TiffLayer):
    """Extends TiffParameter class for Koeppen data consumption."""

    def __init__(self):
        super().__init__()

        self.time_col = LayerTimeResolution.YEAR
        self.value_type = LayerValueType.PERCENTAGE

        # GeoTiff files have no `NoData`-value set. But the value 0 is used
        # for water bodies and has no meaning for the climate zones. We use
        # this as NoData value.
        self.manual_nodata = 0

        self.area_of_interest = []

    def get_data_path(self) -> Path:
        """Overwrite parameter_id based input directory, because we have
        multiple derives parameters from this source."""
        return Path("./data/datalayers/koeppen/")

    def download(self):
        url = "https://figshare.com/ndownloader/files/12407516"

        if not os.path.isfile(self.get_data_path() / "Beck_KG_V1.zip"):
            self._save_url_to_file(
                url, folder=self.get_data_path(), file_name="Beck_KG_V1.zip"
            )

        if os.path.isfile(self.get_data_path() / "legend.txt"):
            return
        try:
            in_file = self.get_data_path() / "Beck_KG_V1.zip"
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
        # files = sorted([s for s in os.listdir(param_dir) if s.rpartition('.')[2] in ('tiff','tif')])

        # only one file is of interest for us
        return ["Beck_KG_V1_present_0p0083.tif"]

    def consume(self, file, band, shape):
        total_cells = np.count_nonzero(~np.isnan(band))
        values, count = np.unique(band, return_counts=True)
        stats = dict(zip(values, count))

        aoi_cells = 0
        for key in self.area_of_interest:
            if key in stats:
                aoi_cells += stats[key]

        self.rows.append(
            {
                "year": 2016,
                "shape_id": shape.id,
                "value": aoi_cells / total_cells,
            }
        )
