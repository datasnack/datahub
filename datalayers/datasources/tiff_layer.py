import os
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import rasterio.mask
import fiona
from shapely import wkt

from .base_layer import BaseLayer

from shapes.models import Shape

class TiffLayer(BaseLayer):
    """ Extends BaseParameter class for GeoTiff consumption. """

    def __init__(self):
        super().__init__()
        self.manual_nodata = None

    def consume(self, file, band, shape):
        """ Derived layer need to implement this method. """
        raise NotImplementedError

    def get_tiff_files(self, param_dir):
        files = sorted([s for s in os.listdir(param_dir) if s.rpartition('.')[2] in ('tiff','tif')])
        return files

    def process(self, shapes=None, save_output=False, param_dir=None):

        if param_dir is None:
            param_dir = self.get_data_path()

        files = self.get_tiff_files(param_dir)

        if shapes is None:
            shapes = Shape.objects.all()
            #shapes = self._get_shapes_from_db()

        file_count = len(files)
        i = 1

        for file in files:
            #self.logger.info("loading file (%s of %s): %s", i, file_count, file)
            i += 1

            with rasterio.open(param_dir / file) as src:
                nodata = src.nodata
                #self.logger.debug("No data is: %s", nodata)

                # GeoTiff has NO NoData meta data set, try to use custom
                # set NoData value
                if nodata is None:
                    nodata = self.manual_nodata

                # make sure manual_nodata is set
                if nodata is None:
                    raise ValueError(f"No NoData value for GeoTiff {file}")

                for shape in shapes[:1]:
                    print(shape)
                    
                    #self.logger.debug("loading shape: %s", shape['name'])
                    if isinstance(shape, Shape):

                        # Shape uses the GeoDjango Model and so has not a shapely geometry
                        # so convert it. amazing right?


                        mask = [wkt.loads(shape.geometry.wkt)]
                    elif "geometry" in shape:
                        mask = [shape['geometry']]
                    elif "file" in shape:
                        with fiona.open(shape['file'], "r") as shapefile:
                            mask = [feature["geometry"] for feature in shapefile]
                    else:
                        raise ValueError("No geometry found for given shape.")
                    
                    out_image, _ = rasterio.mask.mask(src, mask, crop=True, nodata=nodata)
                    band1 = out_image[0]

                    # To mask NoData cells we use np.nan so we can use np.nan*-methods.
                    # But np.nan is only available inside float arrays, not with
                    # int arrays!
                    # So in case we have a int array GeoTiff, we need to check
                    # and convert it to a float array.
                    if np.issubdtype(band1.dtype, np.integer):
                        band1 = band1.astype(np.float32)

                    band1[band1==nodata] = np.nan

                    self.consume(file, band1, shape)

        self.save()
