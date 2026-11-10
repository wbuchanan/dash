"""WP-34 AX-4 (section 34-01): a histogram's bin axis is ticked over its
first and last bin midpoints, as twoway ticks it.

Measured at the batch base (cd6aa39), in both modes: ``histogram mpg`` on
auto drew x ticks 10(10)40 over 9.58-41.42 where twoway draws 15(5)40 over
12-41 (test/fixtures/default_axes_truth.json P08: scale min and max
13.8125 and 39.1875, the first and last bin midpoints).  twoway's scale
runs over each midpoint plus or minus half a bar and the bar's offset:
``histogram mpg, gap(50) baroffset(1)`` and ``baroffset(-1)`` both run
11.09375-41.90625 (measured 22oct2026), so the drawn bars are no tick input
and a shifted bar widens the scale on both sides.

The bars' source carries ``__dash_mid`` (tick input) and
``__dash_span_lo``/``__dash_span_hi`` (the scale's span, hull only); the
saved page's rebin writes all three after a move.  The probes against
twoway are rows H01-H10 of test_default_axes.py's TestStataTruth.

While iterating: ``python3 -m pytest test/test_histogram_bin_axis.py -q``.
"""
import json
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402

P = tda.P
_MODES = ("saved", "served")
_MPG_MIDS = (13.8125, 39.1875)


def _quads(figs):
    return [r for f in figs for r in f.renderers
            if type(getattr(r, "glyph", None)).__name__ in ("Quad",)]


def _quad(mode, options=None, go=None, filt=""):
    figs = tda._figs(mode, tda._spec([P("histogram", "mpg", **(options or {}))],
                                     go, filt=filt))
    return figs[0], _quads(figs)[0]


def _mids(edges):
    return [(float(edges[k]) + float(edges[k + 1])) / 2.0
            for k in range(len(edges) - 1)]


class TestTheTickInput:
    def test_extent_reads_the_midpoints(self):
        f, r = _quad("saved")
        got = dr._dash_layer_extent([r], "x_range_name", "default")
        assert got == pytest.approx(_MPG_MIDS)
        assert dr._dash_layer_extent([r], "x_range_name", "default",
                                     role="base") is None
        # The span is hull only: the first and last bin edges here.
        assert dr._dash_layer_extent([r], "x_range_name", "default",
                                     role="hull") == pytest.approx((12.0,
                                                                    41.0))

    @pytest.mark.parametrize("mode", _MODES)
    def test_hull_keeps_the_edges(self, mode):
        """The scale spans every bar: P08's edges 12-41, and under gap(50)
        baroffset(-1) twoway's symmetric span 11.09375-41.90625."""
        rows = tda._truth()["probes"]
        for opts, cur in (({}, rows["P08"]["x"]["cur"]),
                          ({"gap": "50", "baroffset": "-1"},
                           [11.09375, 41.90625])):
            f, r = _quad(mode, opts)
            lo, hi = tda._inner(f, "x")
            assert (lo, hi) == pytest.approx(tuple(cur))
            d = r.data_source.data
            assert lo <= min(d["left"]) + 1e-9
            assert hi >= max(d["right"]) - 1e-9

    def test_transpose_turns_the_tick_fields(self):
        f, r = _quad("saved", {"horizontal": "horizontal"})
        assert r._dash_tick_fields == {"y": ("__dash_mid",)}
        assert r._dash_span_fields == {"y": ("__dash_span_lo",
                                             "__dash_span_hi")}
        assert dr._dash_layer_extent([r], "y_range_name", "default") \
            == pytest.approx(_MPG_MIDS)
        assert tda._ticks(f, "y") == [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]


class TestThePlan:
    def test_plan_fields(self):
        r = tda._saved(tda._spec([P("histogram", "mpg"),
                                  P("scatter", "mpg", "weight")]))
        plan = json.loads(dr._dash_axis_plan(r.figures, r._facet_map,
                                             zoom=False)[0])
        x = [a for p in plan for pn in p["panels"] for a in pn["axes"]
             if a["letter"] == "x"][0]
        assert all("hfields" in L for L in x["layers"])
        hist = [L for L in x["layers"] if "__dash_mid" in L["fields"]]
        assert len(hist) == 1
        assert hist[0]["fields"] == ["__dash_mid"]
        assert hist[0]["hfields"] == ["__dash_span_lo", "__dash_span_hi"]
        assert [L["hfields"] for L in x["layers"] if L is not hist[0]] \
            == [[]]


class TestAfterAMove:
    def test_saved_rebin(self):
        """After a saved range move the rebinned source keeps its midpoint
        and span columns over the kept grid, and the axis is ticked over
        the first and last midpoints."""
        r = tda._saved(tda._spec([P("histogram", "mpg", gap="50",
                                    baroffset="1")], filt=tda._RANGE[0]))
        figs = tda._move_saved(r, *tda._RANGE[1:])
        # twoway's default grid over the kept rows (WP-31 H6): from the
        # minimum, int(min(sqrt N, 10 log10 N)) bins.
        lo_p, hi_p = tda._RANGE[2]
        df = tda._frame()
        kept = df[(df.price >= lo_p) & (df.price <= hi_p)].mpg
        nb = int(min(math.sqrt(len(kept)), 10 * math.log10(len(kept))))
        w = (kept.max() - kept.min()) / nb
        edges = [kept.min() + w * k for k in range(nb + 1)]
        q = _quads(figs)[0]
        d = q.data_source.data
        mids = _mids(edges)
        assert list(d["__dash_mid"]) == pytest.approx(mids)
        bw = (edges[1] - edges[0]) * 0.5
        assert list(d["__dash_span_lo"]) == pytest.approx(
            [m - 1.5 * bw for m in mids])
        assert list(d["__dash_span_hi"]) == pytest.approx(
            [m + 1.5 * bw for m in mids])
        assert tda._ticks(figs[0], "x") == dr._dash_axis_count_ticks(
            mids[0], mids[-1], 5)

    def test_served_refit(self):
        """The served refit after the same move ticks what the saved page
        ticks."""
        spec = tda._spec([P("histogram", "mpg")], filt=tda._RANGE[0])
        saved = tda._after("saved", spec, *tda._RANGE[1:])
        served = tda._after("served", spec, *tda._RANGE[1:])
        assert tda._ticks(served[0], "x") == tda._ticks(saved[0], "x") \
            == [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
        assert "__dash_mid" in _quads(served)[0].data_source.data


class TestTheGridAfterAMove:
    """twoway draws the histogram of the kept rows on the grid its options
    give over those rows (GlyphMapper._histogram_grid): bin() a count over
    the kept range, width() from the kept minimum, start() over to the kept
    maximum, discrete from the kept values.  The saved page re-bins as the
    served refit does.  Bug (10nov2026): the saved page kept the full
    data's grid for any of these options and marked the layer (bins
    unfiltered); bin(6) moved to Foreign drew its first bar from 12, the
    served page from 14."""

    @staticmethod
    def _bars(figs):
        (q,) = [r for r in _quads(figs)
                if "dash_outline" not in (r.tags or [])]
        d = q.data_source.data
        return [[round(float(v), 9) for v in d[c]]
                for c in ("left", "right", "top")]

    @pytest.mark.parametrize("opts", [
        {"bin": "6"}, {"width": "5"}, {"start": "10"},
        {"start": "10", "width": "5"}, {"bin": "6", "start": "10"},
        {"discrete": "discrete"}, {"discrete": "discrete", "width": "2"},
        {"bin": "6", "fraction": "fraction"}])
    @pytest.mark.parametrize("move", [tda._DROP, tda._RANGE])
    def test_saved_is_served(self, opts, move):
        spec = tda._spec([P("histogram", "mpg", **opts)], filt=move[0])
        saved = self._bars(tda._after("saved", spec, *move[1:]))
        served = self._bars(tda._after("served", spec, *move[1:]))
        assert saved == served
