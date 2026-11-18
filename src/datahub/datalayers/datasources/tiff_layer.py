# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import os
from pathlib import Path

import fiona
import numpy as np
import pandas as pd
import rasterio
import rasterio.mask
from shapely import wkt

from shapes.models import Shape

from .base_layer import BaseLayer


class TiffLayer(BaseLayer):
    """Extends BaseParameter class for GeoTiff consumption."""

    def __init__(self) -> None:
        super().__init__()
        self.manual_nodata = None

    def consume(self, file, band, shape):
        """Implement this method in the Derived Data Layer."""
        raise NotImplementedError

    def get_tiff_files(self, param_dir):
        return sorted(
            [
                s
                for s in os.listdir(param_dir)
                if s.rpartition(".")[2] in ("tiff", "tif", "geotiff")
            ]
        )

    def process(self, shapes):
        param_dir = self.get_data_path()
        files = self.get_tiff_files(param_dir)
        file_count = len(files)
        i = 1

        for file in files:
            # self.logger.info("loading file (%s of %s): %s", i, file_count, file)
            i += 1

            with rasterio.open(param_dir / file) as src:
                nodata = src.nodata
                # self.logger.debug("No data is: %s", nodata)

                # GeoTiff has NO NoData meta data set, try to use custom
                # set NoData value
                if nodata is None:
                    nodata = self.manual_nodata

                # make sure manual_nodata is set
                if nodata is None:
                    raise ValueError(f"No NoData value for GeoTiff {file}")

                for shape in shapes:
                    # self.logger.debug("loading shape: %s", shape['name'])
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

                    try:
                        out_image, _ = rasterio.mask.mask(
                            src, mask, crop=True, nodata=nodata
                        )
                        band1 = out_image[0]
                    except ValueError as e:
                        # in case the GeoTiff is not overlapping with the current shape
                        if str(e) == "Input shapes do not overlap raster.":
                            # print(f"{shape} is not covered by raster: {file}")
                            continue

                        # different error, rethrow
                        raise

                    # Get scale and offset from the metadata
                    if src.scales and src.offsets:
                        scale = src.scales[0]
                        offset = src.offsets[0]
                        band1 = band1.astype(float) * scale + offset
                        band1[band1 == (nodata * scale + offset)] = np.nan

                    # To mask NoData cells we use np.nan so we can use np.nan*-methods.
                    # But np.nan is only available inside float arrays, not with
                    # int arrays!
                    # So in case we have a int array GeoTiff, we need to check
                    # and convert it to a float array.
                    if np.issubdtype(band1.dtype, np.integer):
                        band1 = band1.astype(np.float32)

                    band1[band1 == nodata] = np.nan

                    # Check if the mask has identified any cells
                    if np.count_nonzero(~np.isnan(band1)) == 0:
                        self.layer.warning(
                            "For shape %s (id=%s) no cells could be identified inside the mask for file %s",
                            {
                                "shape": shape.name,
                                "shape_id": shape.id,
                                "file": file,
                            },
                        )
                        continue

                    self.consume(file, band1, shape)
