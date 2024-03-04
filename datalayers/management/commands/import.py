import argparse
import re
import time

import pandas as pd
from sqlalchemy import create_engine
from datacite import DataCiteRESTClient
from datacite.errors import DataCiteNotFoundError

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
from django.utils.timezone import now

from datalayers.models import Datalayer, Category

class Command(BaseCommand):
    help = "Load given CSV file of datalayers"

    def add_arguments(self, parser):
        parser.add_argument("file", type=argparse.FileType('r'))

    def handle(self, *args, **options):
        file = options["file"]
        df = pd.read_csv(file.name)

        df = df.fillna('')

        categories = {}
        for cat in df['category'].unique():
            c = Category(name=cat)
            c.save()
            categories[cat] = c

        dc = DataCiteRESTClient(None, None, None)

        for _, dl in df.iterrows():

            dl['category'] = categories[dl['category']]
            d = Datalayer(**dl)

            match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', dl['identifier'], re.IGNORECASE)

            if match:
                d.doi = match.group()

                print(d.doi)

                try:
                    d.datacite = dc.get_metadata(d.doi)
                    d.datacite_fetched_at = now()
                except DataCiteNotFoundError:
                    print("> no data")
                    pass

                time.sleep(1)


            d.save()
