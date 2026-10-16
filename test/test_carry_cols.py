"""Carried columns reach Bokeh as arrays (WP-31 G4).

``GlyphMapper._carry_cols`` copies the caller's other columns (hover(),
mlabel, the row id) into a derived source.  It upcast every column to
``dtype=object`` and handed Bokeh a Python list, which bokeh 3.8 validates
item by item: 7.5 of 7.7 s on a million-row line (GAPS3 G4).  A numeric
column now stays a float64 array; text stays a list; dates stay arrays.
"""
import time

import numpy as np
import pytest
from bokeh.models import ColumnDataSource

import dash_render as dr


def _carry(src_data, data, selector=None):
    return dr.GlyphMapper._carry_cols(ColumnDataSource(src_data), data,
                                      selector)


class TestArrays:
    def test_numeric_stays_array(self):
        got = _carry({"x": [1.0, 2.0, 3.0], "num": [10.0, np.nan, 30.0]},
                     {"x0": [1.0, 2.0, 3.0]})
        assert isinstance(got["num"], np.ndarray)
        assert got["num"].dtype == np.float64
        assert np.array_equal(got["num"], [10.0, np.nan, 30.0],
                              equal_nan=True)

    def test_int_becomes_float_array(self):
        got = _carry({"x": [1.0, 2.0, 3.0], "id": np.array([1, 2, 3])},
                     {"x0": [1.0, 2.0, 3.0]})
        assert isinstance(got["id"], np.ndarray)
        assert got["id"].dtype == np.float64
        assert got["id"].tolist() == [1.0, 2.0, 3.0]

    def test_text_is_list(self):
        got = _carry({"x": [1.0, 2.0, 3.0], "make": ["a", "b", "c"]},
                     {"x0": [1.0, 2.0, 3.0]})
        assert got["make"] == ["a", "b", "c"]

    def test_dates_stay_arrays(self):
        days = np.array(["2020-01-01", "2020-01-02", "2020-01-03"],
                        dtype="datetime64[ms]")
        got = _carry({"x": [1.0, 2.0, 3.0], "d": days},
                     {"x0": [1.0, 2.0, 3.0]})
        assert isinstance(got["d"], np.ndarray)
        assert got["d"].dtype.kind == "M"
        assert np.array_equal(got["d"], days)

    def test_selector_applies(self):
        got = _carry({"x": [1.0, 2.0, 3.0], "num": [10.0, 20.0, 30.0],
                      "make": ["a", "b", "c"]},
                     {"x0": [1.0, 3.0]}, np.array([True, False, True]))
        assert isinstance(got["num"], np.ndarray)
        assert got["num"].tolist() == [10.0, 30.0]
        assert got["make"] == ["a", "c"]

    @pytest.mark.release
    def test_build_is_faster_than_lists(self):
        n = 200_000
        rng = np.random.default_rng(1)
        cols = {"x": rng.random(n), "y": rng.random(n),
                "h1": rng.random(n), "h2": rng.random(n)}
        derived = {"x0": cols["x"]}
        t0 = time.perf_counter()
        ColumnDataSource(data=dr.GlyphMapper._carry_cols(
            ColumnDataSource(cols), dict(derived)))
        arrays = time.perf_counter() - t0
        t0 = time.perf_counter()
        listed = dict(derived)
        for k, v in cols.items():
            listed[k] = np.asarray(v, dtype=object).tolist()
        ColumnDataSource(data=listed)
        lists = time.perf_counter() - t0
        assert arrays < 0.5 * lists, (arrays, lists)
