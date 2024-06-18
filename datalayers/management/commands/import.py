import argparse
import re
import time

import pandas as pd
from datacite import DataCiteRESTClient
from datacite.errors import DataCiteNotFoundError
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from datalayers.models import Category, Datalayer, DatalayerSource


class Command(BaseCommand):
    help = "Load given CSV file of datalayers"

    def add_arguments(self, parser):
        parser.add_argument("file", type=argparse.FileType("r"))

    def handle(self, *args, **options):
        file = options["file"]
        df = pd.read_csv(file.name)

        df = df.fillna("")

        categories = {}

        # Check for already created categories in the Hub
        known_cats = Category.objects.all()
        for c in known_cats:
            categories[c.name] = c

        # Check if the import contains new categories
        for cat in df["category"].unique():
            if cat in categories.keys():
                continue
            c = Category(name=cat)
            c.save()
            categories[cat] = c

        # get already important layer, don't re-import known layers
        known_layers = Datalayer.objects.values_list("key", flat=True)

        # safe relations until all layer are imported
        relations = []

        for _, dl in df.iterrows():
            if dl["key"] in known_layers:
                self.stdout.write(
                    self.style.WARNING(f"Skipping {dl['key']}, already exists")
                )
                continue

            tags = []
            if "tags" in dl:
                if dl["tags"]:
                    tags = dl["tags"].split(",")
                del dl["tags"]

            if "related_to" in dl:
                if dl["related_to"]:
                    related = dl["related_to"].split(",")
                    for r in related:
                        relations.append((dl["key"], r))
                del dl["related_to"]

            # check for sources
            sources = []
            for k, v in dl.items():
                m = re.match(r"source_(\d+)_(\w+)$", k)
                if not m:
                    continue

                if v:
                    if int(m[1]) + 1 > len(sources):
                        sources.append({})
                    sources[int(m[1])][m[2]] = v

                del dl[k]

            # Save Data layer
            dl["category"] = categories[dl["category"]]

            # remove empty fields for data-type columns
            if "date_last_accessed" in dl:
                if not dl["date_last_accessed"]:
                    del dl["date_last_accessed"]
            if "date_included" in dl:
                if not dl["date_included"]:
                    del dl["date_included"]

            # we always use a new ID
            if "id" in dl:
                del dl["id"]

            d = Datalayer(**dl)
            d.save()

            if len(tags):
                d.tags.add(**tags)

            for s in sources:
                ds = DatalayerSource(**s)
                ds.datalayer = d
                ds.save()

            # todo: not yet clear how this should work. definitely needs 1:n relation
            # dc = DataCiteRESTClient(None, None, None)
            # match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', dl['identifier'], re.IGNORECASE)
            # if match:
            #    d.doi = match.group()
            #    try:
            #        d.datacite = dc.get_metadata(d.doi)
            #        d.datacite_fetched_at = now()
            #    except DataCiteNotFoundError:
            #        print("> no data")
            #        pass
            #    time.sleep(1) # don't get banned on the api?

        for rel in relations:
            rel_a = Datalayer.objects.get(key=rel[0])
            if not rel_a:
                self.stdout.write(
                    self.style.WARNING(
                        f"Can't create relation ({rel[0]}<->{rel[1]}), {rel[0]} does not exist"
                    )
                )
                continue

            rel_b = Datalayer.objects.get(key=rel[1])
            if not rel_b:
                self.stdout.write(
                    self.style.WARNING(
                        f"Can't create relation ({rel[0]}<->{rel[1]}), {rel[1]} does not exist"
                    )
                )
                continue

            rel_a.related_to.add(rel_b)
