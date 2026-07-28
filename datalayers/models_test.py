# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from sqlalchemy.dialects.postgresql import aggregate_order_by
from meteostat.series.aggregate import aggregate
import datetime as dt

import pytest
import pandas as pd
from pandas.testing import assert_frame_equal


class TestDatalayerProcessedData:
    def test_data_shape(self, dl_listed, shape_country, db):
        # all data
        df = dl_listed.data(shape=shape_country)
        assert df["value"].to_list() == [5, 2, 0, 3, 5, 10, 2, 1]

        # date filter
        df = dl_listed.data(
            shape=shape_country,
            start_date=dt.date(2005, 1, 1),
            end_date=dt.date(2007, 1, 1),
        )
        assert df["value"].to_list() == [10, 2, 1]

        # aggregate
        df = dl_listed.data(shape=shape_country, aggregate="sum")
        assert df["value"].to_list() == [28]

        df = dl_listed.data(
            shape=shape_country,
            start_date=dt.date(2005, 1, 1),
            end_date=dt.date(2007, 1, 1),
            aggregate="sum",
        )
        assert df["value"].to_list() == [13]

        df = dl_listed.data(shape=shape_country, aggregate="min")
        assert df["value"].to_list() == [0]

        df = dl_listed.data(shape=shape_country, aggregate="max")
        assert df["value"].to_list() == [10]

        df = dl_listed.data(shape=shape_country, aggregate="mean")
        assert df["value"].to_list() == [3.5]

        df = dl_listed.data(shape=shape_country, aggregate="median")
        assert df["value"].to_list() == [2.5]

        df = dl_listed.data(shape=shape_country, aggregate="std")
        assert df["value"].to_list() == [3.1622776601683795]

        df = dl_listed.data(shape=shape_country, aggregate="count")
        assert df["value"].to_list() == [8]

    def test_data_shape_type(
        self, dl_listed, type_region, shape_region_upper, shape_region_lower, db
    ):
        # all data
        expected_df = (
            pd.DataFrame(
                data=[
                    {"shape_key": "CC011", "year": 2000, "value": 2},
                    {"shape_key": "CC011", "year": 2001, "value": 0},
                    {"shape_key": "CC011", "year": 2002, "value": 0},
                    {"shape_key": "CC011", "year": 2003, "value": 2},
                    {"shape_key": "CC011", "year": 2004, "value": 5},
                    {"shape_key": "CC011", "year": 2005, "value": 7},
                    {"shape_key": "CC011", "year": 2006, "value": 1},
                    {"shape_key": "CC011", "year": 2007, "value": 1},
                    {"shape_key": "CC012", "year": 2000, "value": 3},
                    {"shape_key": "CC012", "year": 2001, "value": 2},
                    {"shape_key": "CC012", "year": 2002, "value": 0},
                    {"shape_key": "CC012", "year": 2003, "value": 1},
                    {"shape_key": "CC012", "year": 2004, "value": 0},
                    {"shape_key": "CC012", "year": 2005, "value": 3},
                    {"shape_key": "CC012", "year": 2006, "value": 1},
                    {"shape_key": "CC012", "year": 2007, "value": 0},
                ]
            )
            .sort_values(by="year")
            .reset_index(drop=True)
        )
        df = dl_listed.data(shape_type=type_region)
        assert_frame_equal(expected_df, df[["shape_key", "year", "value"]])

        # time slice
        expected_df = (
            pd.DataFrame(
                data=[
                    {"shape_key": "CC011", "year": 2004, "value": 5},
                    {"shape_key": "CC011", "year": 2005, "value": 7},
                    {"shape_key": "CC011", "year": 2006, "value": 1},
                    {"shape_key": "CC012", "year": 2004, "value": 0},
                    {"shape_key": "CC012", "year": 2005, "value": 3},
                    {"shape_key": "CC012", "year": 2006, "value": 1},
                ]
            )
            .sort_values(by="year")
            .reset_index(drop=True)
        )
        df = dl_listed.data(
            shape_type=type_region,
            start_date=dt.date(2004, 1, 1),
            end_date=dt.date(2006, 1, 1),
        )
        assert_frame_equal(expected_df, df[["shape_key", "year", "value"]])

        # agg function
        expected_df = pd.DataFrame(
            data=[
                {"dh_shape_id": shape_region_upper.id, "value": 13},
                {"dh_shape_id": shape_region_lower.id, "value": 4},
            ]
        ).reset_index(drop=True)
        df = dl_listed.data(
            shape_type=type_region,
            start_date=dt.date(2004, 1, 1),
            end_date=dt.date(2006, 1, 1),
            aggregate="sum",
        )
        assert_frame_equal(expected_df, df[["dh_shape_id", "value"]])

        expected_df = pd.DataFrame(
            data=[
                {
                    "dh_shape_id": shape_region_upper.id,
                    "value": 4.333333,
                    "min": 1,
                    "max": 7,
                },
                {
                    "dh_shape_id": shape_region_lower.id,
                    "value": 1.333333,
                    "min": 0,
                    "max": 3,
                },
            ]
        ).reset_index(drop=True)
        df = dl_listed.data(
            shape_type=type_region,
            start_date=dt.date(2004, 1, 1),
            end_date=dt.date(2006, 1, 1),
            aggregate="mean",
        )
        assert_frame_equal(expected_df, df[["dh_shape_id", "value", "min", "max"]])

        expected_df = (
            pd.DataFrame(
                data=[
                    {"year": 2004, "value": 2.5, "min": 0, "max": 5},
                    {"year": 2005, "value": 5, "min": 3, "max": 7},
                    {"year": 2006, "value": 1, "min": 1, "max": 1},
                ]
            )
            .sort_values(by="year")
            .reset_index(drop=True)
        )

        df = dl_listed.data(
            shape_type=type_region,
            start_date=dt.date(2004, 1, 1),
            end_date=dt.date(2006, 1, 1),
            aggregate="mean",
            aggregate_group_by="temporal",
        )
        assert_frame_equal(expected_df, df[["year", "value", "min", "max"]])
