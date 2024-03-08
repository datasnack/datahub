import argparse
import re
import time

import pandas as pd
from datacite import DataCiteRESTClient
from datacite.errors import DataCiteNotFoundError

from django.core.management.base import BaseCommand
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

        # Check for already created categories in the Hub
        known_cats = Category.objects.all()
        for c in known_cats:
            categories[c.name] = c

        # Check if the import contains new categories
        for cat in df['category'].unique():
            if cat in categories.keys():
                continue
            c = Category(name=cat)
            c.save()
            categories[cat] = c

        dc = DataCiteRESTClient(None, None, None)

        # get allready important layer, don't re-import known layers
        known_layers = Datalayer.objects.values_list('key', flat=True)

        for _, dl in df.iterrows():

            if dl['key'] in known_layers:
                self.stdout.write(self.style.WARNING(f"Skipping {dl['key']}, already exists"))
                continue

            dl['category'] = categories[dl['category']]
            d = Datalayer(**dl)

            # todo: not yet clear how this should work. definitely needs 1:n relation
            #match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', dl['identifier'], re.IGNORECASE)
            #if match:
            #    d.doi = match.group()
            #    try:
            #        d.datacite = dc.get_metadata(d.doi)
            #        d.datacite_fetched_at = now()
            #    except DataCiteNotFoundError:
            #        print("> no data")
            #        pass
            #    time.sleep(1) # don't get banned on the api?


            d.save()
