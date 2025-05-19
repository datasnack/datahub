import datetime as dt

import pytest

from .base_layer import BaseLayer, LayerTimeResolution, LayerValueType


def test_layer_is_valid_temporal():
    layer = BaseLayer()
    layer.time_col = LayerTimeResolution.YEAR

    assert layer.is_valid_temporal(2000) is True
    assert layer.is_valid_temporal("2000") is False

    layer = BaseLayer()
    layer.time_col = LayerTimeResolution.MONTH

    assert layer.is_valid_temporal(dt.date(2000, 1, 1)) is True
    assert (
        layer.is_valid_temporal(dt.date(2000, 1, 10)) is False
    )  # month values are stored as date, but always on the -01
    assert layer.is_valid_temporal("2000-01") is False
    assert layer.is_valid_temporal("2000-01-01") is False
    assert layer.is_valid_temporal(dt.datetime(2000, 1, 1, tzinfo=dt.UTC)) is False

    layer = BaseLayer()
    layer.time_col = LayerTimeResolution.DAY

    assert layer.is_valid_temporal(dt.date(2000, 1, 1)) is True
    assert layer.is_valid_temporal("2000-01-01") is False
    assert layer.is_valid_temporal(dt.datetime(2000, 1, 1, tzinfo=dt.UTC)) is False


def test_layer_is_valid_value():
    layer = BaseLayer()
    layer.value_type = LayerValueType.PERCENTAGE
    assert layer.is_valid_value(0.0) is True
    assert layer.is_valid_value(0.5) is True
    assert layer.is_valid_value(1.0) is True
    assert layer.is_valid_value("1.0") is False
    assert layer.is_valid_value(100.0) is False
    assert layer.is_valid_value(42.34) is False

    layer = BaseLayer()
    layer.value_type = LayerValueType.BINARY
    assert layer.is_valid_value(True) is True  # noqa: FBT003 (boolean-positional-value-in-call)
    assert layer.is_valid_value(False) is True  # noqa: FBT003 (boolean-positional-value-in-call)
    assert layer.is_valid_value(0) is False
    assert layer.is_valid_value("null") is False
    assert layer.is_valid_value("None") is False
    assert layer.is_valid_value(None) is False

    layer = BaseLayer()
    layer.value_type = LayerValueType.NOMINAL
    layer.nominal_values = ["foo", "bar"]
    assert layer.is_valid_value("foo") is True
    assert layer.is_valid_value(100) is False
    assert layer.is_valid_value("baz") is False

    layer = BaseLayer()
    layer.value_type = LayerValueType.ORDINAL
    layer.ordinal_values = ["low", "high"]
    assert layer.is_valid_value("high") is True
    assert layer.is_valid_value("extreme") is False
