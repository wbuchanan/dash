"""Fractional dates and rarea's one-bound rows, as twoway draws them
(WP-31 G6).

Measured (StataNow 19.5, SVG): ``scatter y m`` with ``%tm`` m = 745, 745.5,
746 places 745.5 exactly halfway between 2022m2 and 2022m3, where dash
floored it onto 2022m2; ``rarea lo hi x`` with hi missing on row 3 of 6 is
the polygon lo1..lo6, hi6, hi5, hi4, hi2, hi1 -- the row keeps its lower
bound, where dash left the row out of both.  Tied sort keys and connected
markers under sort keep twoway's order rule (``_join_order``), which is
not deterministic in twoway either.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402


def _ms(values, kind):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = dr._stata_dates_to_datetime(pd.Series(values), kind,
                                           fractions=True)
    return got.astype("int64").to_numpy()


def _load(cols, formats):
    df = pd.DataFrame(cols)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = dr._dash_load_columns(df, formats, set())
    return df, out


class TestFractionalDates:

    @pytest.mark.parametrize("kind,lo", [("tm", 745.0), ("tq", 248.0),
                                         ("tw", 51.0), ("th", 124.0),
                                         ("ty", 1998.0)])
    def test_tm_half(self, kind, lo):
        a, m, b = _ms([lo, lo + 0.5, lo + 1.0], kind)
        assert m == (a + b) // 2

    def test_td_half(self):
        a, m, b = _ms([20000.0, 20000.5, 20001.0], "td")
        assert m == (a + b) // 2

    def test_the_loader_places_fractions(self):
        df, _nf = _load({"m": [745.0, 745.5, 746.0]}, {"m": "%tm"})
        a, m, b = df["m"].astype("int64").tolist()
        assert m == (a + b) // 2

    def test_the_axis_twin_keeps_the_start(self):
        # The axis code converts whole period numbers; its JavaScript twin
        # (dash_ts_unit_to_ms) is compared without fractions.
        a = _ms([745.0], "tm")[0]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = dr._stata_dates_to_datetime(pd.Series([745.5]), "tm")
        assert got.astype("int64").tolist() == [a]

    def test_the_period_shown_is_still_the_floor(self):
        # Stata displays %tm 745.5 as 2022m2: the inverse reads the period
        # that holds the drawn position.
        m = _ms([745.5], "tm")
        assert dr._dash_period_values(m.astype(float), "tm")[0] == 745.0


def _rarea(y1, y2, x):
    gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
    fig = figure()
    src = ColumnDataSource({"x": x, "lo": y1, "hi": y2})
    gm.map_rarea(fig, src, "lo", "hi", "x", {"sort": "1"})
    [va] = [r for r in fig.renderers if type(r.glyph).__name__ == "VArea"]
    d = va.data_source.data
    return (list(np.asarray(d["x"], float)), list(np.asarray(d["lo"], float)),
            list(np.asarray(d["hi"], float)))


class TestRareaOneBound:

    def test_polygon_keeps_other_bound(self):
        nan = float("nan")
        x, lo, hi = _rarea([1, 2, 3, 4, 5, 6.0],
                           [11, 12, nan, 14, 15, 16.0],
                           [1, 2, 3, 4, 5, 6.0])
        assert x == [1, 2, 3, 4, 5, 6]
        assert lo == [1, 2, 3, 4, 5, 6]
        # the upper edge runs straight from hi2 to hi4
        assert hi == [11, 12, 13, 14, 15, 16]

    def test_an_end_row_is_left_out(self):
        nan = float("nan")
        x, lo, hi = _rarea([1, 2, 3.0], [11, 12, nan], [1, 2, 3.0])
        assert x == [1, 2]

    def test_helper(self):
        cols = {"x": np.array([0.0, 1, 3]), "a": np.array([0.0, np.nan, 3]),
                "b": np.array([5.0, 5, 5])}
        out, order = dr._dash_rarea_one_bound(cols, np.array([7, 8, 9]),
                                              "x", "a", "b")
        assert list(out["a"]) == [0, 1, 3] and list(order) == [7, 8, 9]
