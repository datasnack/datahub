import argparse

import geopandas
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings

from datalayers.models import Datalayer

class Command(BaseCommand):
    help = "Load given shapefile structure into the database"

    def add_arguments(self, parser):
        parser.add_argument("key", type=str)
        parser.add_argument("action", type=str)

    def handle(self, *args, **options):
        dl = Datalayer.objects.get(key=options['key'])

        match options['action']:
            case 'download':
                dl.download()
            case 'process':
                dl.process()
            case _:
                raise CommandError('Unknown action "%s" to perform on Data Layer' % options['action'])
