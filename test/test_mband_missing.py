"""mband and mspline over data with a missing y or x, drawn as twoway draws
them (WP-31 C6b).

The defect, measured by section 14 (test/fixtures/area_cmissing_truth.json
E04, E05: auto with mpg missing in 10/12): twoway mband drew 9 vertices
where dash drew 8, and mspline 89 where dash drew 78.  Not a cmissing()
effect: dash computed the band count and the bands' x range from the
complete rows only.

twoway's rule, measured 14oct2026 (StataNow 19.5) on auto sorted by weight
with values set missing (the U25 C6b block re-measures it live):

* the default band count is _gs_default_bands.ado's rule on the serset's N:
  every observation of the sample in which y or x is present -- a row with
  y missing counts, a row with both missing does not;
* the bands cut the x range of the observations that have an x, a row with
  y missing included;
* the cross median of a band is taken over its complete rows, and a band
  with none is skipped.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest
from bokeh.models import Line

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "area_cmissing_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json"),
          encoding="utf-8") as _fh:
    _AUTO = json.load(_fh)["datasets"]["auto"]

_MODES = ("saved", "served")


def _auto():
    """auto as the extract script reads it: mpg missing in 10/12."""
    df = pd.DataFrame({"mpg": _AUTO["mpg"], "weight": _AUTO["weight"]},
                      dtype=float)
    df.loc[9:11, "mpg"] = np.nan
    return df


def _sorted_auto():
    """auto sorted by weight (stable), as the C6b probes were measured."""
    df = pd.DataFrame({"mpg": _AUTO["mpg"], "weight": _AUTO["weight"]},
                      dtype=float)
    return df.sort_values("weight", kind="stable").reset_index(drop=True)


def _plot(ptype, **o):
    return {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": o}


def _line(mode, plot, df):
    figs, _ = bg._figs(mode, tempfile.mkdtemp(), bg._spec([plot]), df)
    [g] = [g for g in figs[0].renderers if isinstance(g.glyph, Line)
           and g.glyph.line_alpha != 0]
    d = g.data_source.data
    return (dr._dash_float_values(d[g.glyph.x]),
            dr._dash_float_values(d[g.glyph.y]))


@pytest.mark.parametrize("mode", _MODES)
class TestAgainstTwoway:

    @pytest.mark.parametrize("opts", [{"cmissing": "n"}, {}],
                             ids=["cmissing(n)", "default"])
    @pytest.mark.parametrize("pid,ptype", [("E04", "mband"),
                                           ("E05", "mspline")])
    def test_vertices(self, mode, pid, ptype, opts):
        """Every vertex of twoway's line, in order: the fixture holds the
        SVG's coordinates mapped back to data units, so each is read to
        1e-4 of its axis's span.  cmissing() changes nothing here; the
        served app used to drop the rows missing y from the layer's source
        unless cmissing(n) was given."""
        x, y = _line(mode, _plot(ptype, **opts), _auto())
        [p] = _T[pid]["paths"]
        want = np.asarray(p["pts"], dtype=float)
        assert len(x) == len(want), (len(x), len(want))
        for got, w in ((x, want[:, 0]), (y, want[:, 1])):
            np.testing.assert_allclose(got, w, rtol=0,
                                       atol=1e-4 * (w.max() - w.min()))


# Measured 14oct2026: twoway mband mpg weight's serset on sorted auto.
_PROBES = {
    # mpg missing at the lowest weight: that row still sets the x range.
    "y missing at the x minimum": (
        {"mpg": [0]}, {},
        [(1985, 29), (2200, 25), (2660, 23), (2830, 20), (3310, 19),
         (3690, 17.5), (4045, 14.5), (4310, 17.5), (4780, 12)]),
    # mpg missing on 30 rows: N stays 74, nine bands, two of them empty.
    "y missing on 30 rows": (
        {"mpg": range(30)}, {},
        [(2750, 22.5), (2830, 20), (3310, 19), (3690, 17.5), (4045, 14.5),
         (4310, 17.5), (4780, 12)]),
    # weight missing on 30 rows: N stays 74, the range is the rest's.
    "x missing on 30 rows": (
        {"weight": range(30)}, {},
        [(2830, 21), (3190, 19), (3340, 19), (3600, 18), (3730, 16),
         (4060, 15), (4310, 17.5), (4780, 12)]),
    # both missing on 30 rows: those rows leave N (44, seven bands).
    "both missing on 30 rows": (
        {"mpg": range(30), "weight": range(30)}, {},
        [(2830, 21), (3250, 19), (3420, 18), (3720, 16), (4060, 15),
         (4310, 17.5), (4780, 12)]),
    # a band whose y are all missing is skipped.
    "a band with no y": (
        {"mpg": range(59, 74)}, {"bands": "4"},
        [(2110, 26), (2830, 21.5), (3420, 18)]),
}


class TestTheSample:

    @pytest.mark.parametrize("case", sorted(_PROBES))
    def test_mband_knots(self, case):
        gone, opts, want = _PROBES[case]
        df = _sorted_auto()
        for col, rows in gone.items():
            df.loc[list(rows), col] = np.nan
        x, y = _line("saved", _plot("mband", **opts), df)
        assert list(zip(x, y)) == [(float(a), float(b)) for a, b in want]

    def test_mspline_on_the_same_knots(self):
        """mspline bands(3) n(2) with mpg missing on 30 rows: twoway's
        serset, seven points through the knots (2750, 22.5), (3360, 18.5),
        (4070, 14)."""
        df = _sorted_auto()
        df.loc[list(range(30)), "mpg"] = np.nan
        x, y = _line("saved", _plot("mspline", bands="3", n="2"), df)
        np.testing.assert_allclose(
            x, [2750, 2953.333, 3156.667, 3360, 3596.667, 3833.333, 4070],
            rtol=1e-6)
        np.testing.assert_allclose(
            y, [22.5, 21.15751, 19.82188, 18.5, 16.98449, 15.48759, 14],
            rtol=1e-6)


class TestTheBandSample:

    def test_counts_and_span(self):
        """GlyphMapper._mband_sample: N counts the rows with x or y; the
        span is the x range of the rows with x."""
        x = np.array([1.0, 2, np.nan, 4, np.nan, 9])
        y = np.array([np.nan, 1, 2, 3, np.nan, np.nan])
        n, span = dr.GlyphMapper._mband_sample(x, y)
        assert n == 5 and span == (1.0, 9.0)

    def test_no_x(self):
        n, span = dr.GlyphMapper._mband_sample(
            np.array([np.nan, np.nan]), np.array([1.0, np.nan]))
        assert n == 1 and span is None

    def test_cross_medians_over_a_given_span(self):
        """The span widens the bands; the medians stay the complete rows'."""
        kx, ky = dr.GlyphMapper._cross_medians(
            np.array([2.0, 3, 4]), np.array([5.0, 6, 7]), 2, span=(0.0, 6.0))
        assert list(kx) == [2.0, 3.5] and list(ky) == [5.0, 6.5]
