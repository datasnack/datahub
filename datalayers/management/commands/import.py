import argparse

import pandas as pd
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings

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

        for _, dl in df.iterrows():

            dl['category'] = categories[dl['category']]
            d = Datalayer(**dl)
            d.save()
