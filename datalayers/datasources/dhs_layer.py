import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from datalayers.datasources.base_layer import LayerTimeResolution, LayerValueType
from shapes.models import Shape, Type

from .base_layer import BaseLayer


class DhsLayer(BaseLayer):
    def __init__(self) -> None:
        super().__init__()

        self.time_col = LayerTimeResolution.YEAR
        self.value_type = LayerValueType.VALUE

    def get_indicators(self) -> list[str]:
        raise NotImplementedError

    def get_country(self) -> str:
        """Country code, i.e. "TZ"."""
        raise NotImplementedError

    def get_breakdown(self) -> str:
        return "subnational"

    def consume(self, df: pd.DataFrame) -> pd.DataFrame:
        df["value"] = df[self.get_indicators()[0]]
        return df

    def download(self, breakdown="national"):
        self.download_from_dhs("national")
        self.download_from_dhs("subnational")

    def process(self, shapes=None, save_output=False, param_dir=None):
        if shapes is None:
            shapes = Shape.objects.all()

        # first load national level and process it. for the subnational API response
        # national values are not contained
        df = self.get_local_df("_national")  # prepend _ to not match subnational
        countries = Type.objects.get(key="country").shapes.all()

        national_df = self.group_per_study_year_region(
            df, countries, self.get_indicators(), "CountryName"
        )
        national_df = self.consume(national_df)

        # now process subnational level
        df = self.get_local_df("subnational")
        countries = Type.objects.get(key="region").shapes.all()

        subnational_df = self.group_per_study_year_region(
            df, countries, self.get_indicators(), "CharacteristicLabel"
        )
        subnational_df = self.consume(subnational_df)

        self.df = pd.concat([national_df, subnational_df])
        self.save()

    def get_local_df(self, breakdown) -> pd.DataFrame:
        list_of_files = self.get_data_path().glob(f"*{breakdown}*")
        latest_file = max(list_of_files, key=os.path.getctime)
        return pd.read_csv(latest_file)

    def group_per_study_year_region(self, df, shapes, indicators, shape_name_column):
        """
        Process DHS CSV format for Data Hub.

        Depending on national or subnational level the name of the specific region for
        that a value is valid changes.

        - national    -> CountryName
        - subnational -> CharacteristicLabel
        """
        values = []

        # group by survey/year
        for survey_id in df["SurveyId"].unique():
            dfx = df[df["SurveyId"] == survey_id].reset_index()

            year = dfx.at[0, "SurveyYear"]

            for shape in shapes:
                x = {
                    "year": year,
                    "shape_id": shape.id,
                    "survey": survey_id,
                }

                search_name = shape.name

                for indicator in indicators:
                    # note absence of indicator in any case!
                    x[indicator] = None

                    dfxx = dfx[dfx["IndicatorId"] == indicator]

                    if len(dfxx) == 0:
                        # indicator not present for this study/year
                        print("indicator not present for this study/year")
                        continue

                    dfxx[shape_name_column] = dfxx[shape_name_column].str.replace(
                        "..", ""
                    )

                    # indicator for region
                    print(dfxx[shape_name_column].values)
                    sri = dfxx.loc[dfxx[shape_name_column] == search_name]

                    if len(sri) == 0:
                        print(
                            f'for this region no value exists: "{search_name}" (actual region: "{shape.name}")'
                        )
                        # for this region no value exists
                        continue

                    sri = sri.reset_index()

                    if self.value_type == LayerValueType.PERCENTAGE:
                        x[indicator] = sri.at[0, "Value"] / 100
                    else:
                        x[indicator] = sri.at[0, "Value"]

                all_indicators_null = True
                for indicator in indicators:
                    all_indicators_null = all_indicators_null & (x[indicator] is None)

                # Only save if at least one indicator is available (as in not None)
                if not all_indicators_null:
                    values.append(x)

        return pd.DataFrame(values)

    def download_from_dhs(self, breakdown):
        # fetch data
        params = {
            "countryIds": self.get_country(),
            # give region based level, still shows "zones" (tanzania)
            # we have to filter based on the prepended ".." in
            "breakdown": breakdown,
            "indicatorIds": ",".join(self.get_indicators()),
            "lang": "en",
            "returnGeometry": False,
            # "surveyYearStart": 2010,
            "f": "json",
        }
        data_url = "https://api.dhsprogram.com/rest/dhs/data/?" + urlencode(params)
        req = urlopen(data_url)
        resp = json.loads(req.read())
        my_data = resp["Data"]

        df = pd.DataFrame(my_data)

        # safe raw data
        data_dir = self.get_data_path()
        data_dir.mkdir(parents=True, exist_ok=True)

        now = dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%d_%H-%M-%S")
        file = f"{now}_{self.get_breakdown()}_data_{self.layer.key}.csv"

        df.to_csv(data_dir / file, index=False)
