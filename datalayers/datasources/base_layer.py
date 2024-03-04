import os
import subprocess
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from datalayers.utils import get_engine


class LayerTimeResolution(Enum):
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'

    def __str__(self):
        return str(self.value)

class LayerValueType(Enum):
    VALUE = 'value'
    PERCENTAGE = 'percentage'
    BINARY = 'binary'

    def __str__(self):
        return str(self.value)

class BaseLayer():

    def __init__(self):
        self.layer = None
        self.output = 'db'
        self.rows = []
        self.df = None

        self.time_col : LayerTimeResolution = LayerTimeResolution.YEAR
        self.value_type : LayerValueType = LayerValueType.VALUE

        # How many decimal digits should be displayed?
        # Only used in UI for human on the web, API and CSV data are never rounded
        self.precision = 3


    def download(self):
        """ Automatic download of data source files. """
        raise NotImplementedError

    def process(self):
        """ Consume/calculate data to insert into the database. """
        raise NotImplementedError


    def get_data_path(self) -> Path:
        """ Path to where to store the data of the layer. """
        return Path(f"./data/datalayers/{self.layer.key}/")


    def save(self):
        if self.df is None:
            self.df = pd.DataFrame(self.rows)

        if self.output == 'db':
            self.df.to_sql(self.layer.key, get_engine(), if_exists='replace')
        elif self.output == 'fs':
            self.df.to_csv(self.get_data_path() / f'{self.layer.key}.csv', index=False)
        else:
            raise ValueError(f"Unknown save option {self.output}.")

    def _save_url_to_file(self, url, folder=None, file_name=None) -> bool:
        """ Downloads a URL to be saved on the parameter data directory.
        Checks if file has already been downloaded. Return True in case
        file was downloaded/was already downloaded, otherwise False.
        """
        a = urlparse(url)

        if file_name is None:
            file_name = os.path.basename(a.path)

        if folder is None:
            folder = self.get_data_path()

        if os.path.isfile(folder / file_name):
            #self.logger.debug("Skipping b/c already downloaded %s", url)
            return True

        Path(folder).mkdir(parents=True, exist_ok=True)

        try:
            # call wget to download file
            params = ['wget', "-O", folder / file_name, url]
            subprocess.check_output(params)

            # calculate and log md5 of downloaded file
            md5_output = subprocess.check_output(['md5sum', folder / file_name], text=True)
            md5 = md5_output.split(' ', maxsplit=1)[0]
            self.layer.warning("Downloaded file", {'url': url, 'file': (folder / file_name).as_posix(), 'md5': md5})

            return True
        except subprocess.CalledProcessError as error:
            # -O on wget will create the file regardless if it did exits and
            # could be downloaded. To don't have any empty files, we remove it
            if os.path.exists(folder / file_name):
                os.remove(folder / file_name)

            self.layer.warning("Could not download file: %s, %s", {'url': url, 'error_msg': error.stderr})

            #self.logger.warning("Could not download file: %s, %s", url, error.stderr)

        return False
