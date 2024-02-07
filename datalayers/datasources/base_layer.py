import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine

from django.conf import settings
from datalayers.models import Datalayer

def get_engine():
    return create_engine(f"postgresql://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{settings.DATABASES['default']['NAME']}")


class BaseLayer(Datalayer):

    def __init__(self):
        self.layer = None
        self.output = 'db'
        self.rows = []
        self.df = None

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
            params = ['wget', "-O", folder / file_name, url]
            subprocess.check_output(params)
            return True
        except subprocess.CalledProcessError as _:
            # -O on wget will create the file regardless if it did exits and
            # could be downloaded. To don't have any empty files, we remove it
            if os.path.exists(folder / file_name):
                os.remove(folder / file_name)

            #self.logger.warning("Could not download file: %s, %s", url, error.stderr)

        return False