"""
test_axis_extents.py -- WP-28 section 18 (GAPS2 B2): the extent of an axis.

What was wrong (measured on auto's mpg, 12 to 41, before this section):

* ``ylabel(0(20)100)`` drew the axis to 42 and never showed 60-100: a
  label value only set a FixedTicker and never widened the axis.
* ``yscale(range(100))`` drew the axis from 100 DOWN to 41 (an inverted
  Range1d), ``range(20 30)`` hid every point outside 20-30, and
  ``range(0)`` ended the axis exactly at the data's maximum.
* ``yscale(r(0 100))`` and ``yscale(rev)`` were named as not implemented,
  and so was ``norescale``.
* The served app autoranged its x axis over a fit's 10%-extended grid,
  where the saved page limited it to the scatter.

twoway's rule (axis_label_options.sthlp:344-350, axis_scale_options.sthlp:
144-148 and 336-341): label and tick values widen the axis unless
``norescale``; ``range()`` lists values the axis is widened to include and
"never narrows the scale of an axis or causes data to be omitted"; missing
values are ignored; ``r()`` and ``rev`` are the abbreviations.  dash now
spans the hull of the drawn data, the positions and the range() values,
padded 5% of the hull a side (in log space on a log axis), the same number
in both modes.  Stata's own margin is 2.2% of the canvas, so the fixture
comparisons are of the INNER hull (``_dash_range_hull``), never the drawn
extent.

Truth: ``test/fixtures/axis_truth.json``, group ``b2_extent``, written by
``scripts/extract_axis_truth.do``.
"""
import itertools
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "axis_truth.json")
_SEQ = itertools.count()
_MODES = ("saved", "served")
_DAY = 86_400_000.0


def hull(rng, kind=None):
    return dr._dash_range_hull(rng, kind)


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        t = json.load(fh)
    if not any(p.get("group") == "b2_extent" for p in t["probes"].values()):
        pytest.fail("axis_truth.json has no b2_extent group: section 18 "
                    "task 18-03 must land first")
    return t


def _auto():
    """auto's extremes: mpg 12-41, weight 1760-4840, price 3291-15906."""
    n = 74
    return pd.DataFrame({
        "mpg": np.linspace(12, 41, n),
        "weight": np.linspace(1760, 4840, n),
        "price": np.linspace(3291, 15906, n),
        "foreign": np.array([0.0, 1.0] * 37)[:n],
    })


def _spec(plots, go, formats=None):
    g = dict(go, name="g1", title='"t"')
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "", "registry": "g1",
                              "tabs": "", "filter_position": "top",
                              "csv": "0", "level": "95",
                              "formats": dict(formats or {}), "limits": {}}}


def _figures(mode, tmp_path, df, plots, go, formats=None, notes=None):
    """The figures one mode draws; *notes*, a list, collects its warnings."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, go, formats)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(df)), encoding="utf-8")
    caught = []
    if mode == "saved":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_reset_notes()
            r = dr.DashRenderer(str(sp), str(dp))
            figs = r._build_figures()
            out = [figs[k] for k in sorted(figs)]
    else:
        ap = str(tmp_path / ("app_%d.py" % tag))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
            mod = load_app(ap, "_ext_app_%d" % tag)
        # What the served session says: its own document build.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            doc = Document()
            mod.make_document(doc)
            seen, out = set(), []
            for root in doc.roots:
                for m in root.references():
                    if isinstance(m, _fig_cls) and m.id not in seen:
                        seen.add(m.id)
                        out.append(m)
            out.sort(key=lambda f: str(f.title.text if f.title else ""))
    if notes is not None:
        notes.extend(str(w.message) for w in caught)
    return out


def _sc(y="mpg", x="weight", **opts):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": opts}


def _one(mode, tmp_path, go, plots=None, df=None, formats=None, notes=None):
    figs = _figures(mode, tmp_path, _auto() if df is None else df,
                    plots or [_sc()], go, formats, notes)
    assert len(figs) == 1, len(figs)
    return figs[0]


def _is(rng, name):
    return type(rng).__name__ == name


def _approx(pair, want, rel=1e-6, abs_=1e-6):
    return pair == pytest.approx(want, rel=rel, abs=abs_)


# ---------------------------------------------------------------------------
# Label and tick values widen the axis (BR-18.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestLabelValuesWidenTheAxis:

    def test_ylabel_0_20_100_reaches_100(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"ylabel": "0(20)100"})
        assert _is(fig.y_range, "Range1d"), type(fig.y_range).__name__
        assert _approx(hull(fig.y_range), (0.0, 100.0))

    def test_norescale_draws_the_labels_and_keeps_the_extent(self, mode,
                                                             tmp_path):
        """A list with norescale (probe b2_ylab_list_nr: twoway's axis
        stays 12-41 with the labels drawn outside it)."""
        notes = []
        fig = _one(mode, tmp_path,
                   {"ylabel": "0 20 40 60 80 100, norescale"}, notes=notes)
        (ax,) = fig.yaxis
        assert list(ax.ticker.ticks) == [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]
        # WP-30 P1.3a: a DataRange1d was wrong because every axis now
        # spans its data's hull (twoway's 12-41 here), plus the margin.
        assert _is(fig.y_range, "Range1d")
        assert _approx(hull(fig.y_range), (12.0, 41.0))
        assert not [n for n in notes if "norescale" in n], notes

    def test_a_lone_rule_drops_norescale_as_twoway_does(self, mode,
                                                        tmp_path):
        """twoway records ylabel(0(20)100, norescale) as
        '.major.range_ticks 0 100 20', without norescale, and draws the
        axis widened (probe b2_ylab_0_100_nr, measured 30sep2026)."""
        notes = []
        fig = _one(mode, tmp_path, {"ylabel": "0(20)100, norescale"},
                   notes=notes)
        assert _approx(hull(fig.y_range), (0.0, 100.0))
        assert not [n for n in notes if "norescale" in n], notes

    def test_ytick_50_widens_and_norescale_does_not(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"ytick": "50"})
        assert _is(fig.y_range, "Range1d")
        # WP-30 P1.3a: 12 was wrong because the default axis's natscale
        # ticks (10(10)40) join the hull, as twoway's scale spans them.
        assert _approx(hull(fig.y_range), (10.0, 50.0))
        notes = []
        fig = _one(mode, tmp_path, {"ytick": "50, norescale"}, notes=notes)
        assert _approx(hull(fig.y_range), (10.0, 41.0))
        assert not [n for n in notes if "norescale" in n], notes

    def test_a_labelled_pair_widens(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"ylabel": '0 "zero" 60 "sixty"'})
        assert _approx(hull(fig.y_range), (0.0, 60.0))

    def test_xlabel_widens_x(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"xlabel": "0(1000)6000"})
        assert _approx(hull(fig.x_range), (0.0, 6000.0))


# ---------------------------------------------------------------------------
# range() only ever widens (BR-18.2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestRangeOnlyWidens:

    def test_range_100_widens_up_and_never_inverts(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "range(100)"})
        assert fig.y_range.start < fig.y_range.end, (
            fig.y_range.start, fig.y_range.end)
        assert _approx(hull(fig.y_range), (12.0, 100.0))

    def test_range_20_30_never_narrows(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "range(20 30)"})
        # WP-30 P1.3a: 12 was wrong because the natscale ticks join the hull.
        assert _approx(hull(fig.y_range), (10.0, 41.0))

    def test_range_0_reaches_0_and_keeps_the_top(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "range(0)"})
        assert _approx(hull(fig.y_range), (0.0, 41.0))
        assert fig.y_range.end > 41.0

    def test_r_is_range(self, mode, tmp_path):
        notes = []
        fig = _one(mode, tmp_path, {"yscale": "r(0 100)"}, notes=notes)
        assert _is(fig.y_range, "Range1d")
        assert _approx(hull(fig.y_range), (0.0, 100.0))
        assert not [n for n in notes if "yscale()" in n], notes

    def test_rev_is_reverse(self, mode, tmp_path):
        notes = []
        fig = _one(mode, tmp_path, {"yscale": "rev"}, notes=notes)
        assert dr._dash_range_reversed(fig.y_range)
        assert not [n for n in notes if "yscale()" in n], notes

    @pytest.mark.parametrize("given", ["range(. 60)", "range(60 .)"])
    def test_missing_values_are_ignored(self, mode, tmp_path, given):
        notes = []
        fig = _one(mode, tmp_path, {"yscale": given}, notes=notes)
        # WP-30 P1.3a: 12 was wrong because the natscale ticks join the hull.
        assert _approx(hull(fig.y_range), (10.0, 60.0))
        assert not [n for n in notes if "yscale" in n], notes

    @pytest.mark.parametrize("given", ["range(100 0)", "range(0 50 100)"])
    def test_any_count_in_any_order(self, mode, tmp_path, given):
        fig = _one(mode, tmp_path, {"yscale": given})
        assert fig.y_range.start < fig.y_range.end
        assert _approx(hull(fig.y_range), (0.0, 100.0))

    def test_a_non_number_is_named_once_and_the_axis_left_alone(
            self, mode, tmp_path):
        notes = []
        fig = _one(mode, tmp_path, {"yscale": "range(abc)"}, notes=notes)
        # WP-30 P1.3a: a DataRange1d was wrong because every axis now spans
        # its data and ticks; the bad value leaves that hull alone.
        assert _approx(hull(fig.y_range), (10.0, 41.0))
        want = "dash: yscale(range()) ignores abc, which is not a number"
        assert [n for n in notes if "range()" in n] == [want], notes


class TestTheReader:

    @pytest.mark.parametrize("raw,want", [
        ("range(0 100)", [0.0, 100.0]),
        ("r(5)", [5.0]),
        ("ra(. 3)", [3.0]),
        ("range(1,2,3)", [1.0, 2.0, 3.0]),
        ("range(0(50)100)", [0.0, 50.0, 100.0]),
        ("range()", []),
        ("log", []),
        ("range(1 2) r(3)", [3.0]),
        ("log r(100 . 0,50)", [100.0, 0.0, 50.0]),
    ])
    def test_parse_scale_range_forms(self, raw, want):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert dr._parse_scale_range(raw, "yscale") == want

    def test_scale_names(self):
        assert [dr._dash_scale_name(t) for t in
                ("r(1)", "ra(1)", "range(1)", "rev", "reve", "reverse",
                 "log", "noline", "re")] == [
            "range", "range", "range", "reverse", "reverse", "reverse",
            "log", "noline", "re"]


# ---------------------------------------------------------------------------
# Log and date axes, a degenerate hull (BR-18.4)
# ---------------------------------------------------------------------------

def _td_frame(days):
    return pd.DataFrame({"date": [float(d) for d in days],
                         "close": [float(i + 1) for i in range(len(days))]})


@pytest.mark.parametrize("mode", _MODES)
class TestLogAndDateAxes:

    def test_a_log_hull_is_padded_in_log_space(self, mode, tmp_path):
        from bokeh.models import LogAxis
        fig = _one(mode, tmp_path, {"yscale": "log range(1000 20000)"},
                   plots=[_sc("price")])
        assert any(isinstance(a, LogAxis) for a in fig.yaxis)
        assert _approx(hull(fig.y_range, "log"), (1000.0, 20000.0))
        # Padded in log space by twoway's margin f / (1 - 2f) of the decades
        # a side (WP-30 P1.3a: the old 5% was wrong because twoway's
        # plot-region margin is r x min(W, H), a frame fraction f).
        f = fig._dash_margin["y"]
        lo, hi = math.log10(1000.0), math.log10(20000.0)
        assert fig.y_range.start == pytest.approx(
            10 ** (lo - f / (1 - 2 * f) * (hi - lo)))

    def test_a_td_range_is_in_milliseconds(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"xscale": "range(14900 15400)"},
                   plots=[{"type": "line", "yvar": "close", "xvar": "date",
                           "options": {}}],
                   df=_td_frame([14977, 14979, 14985]),
                   formats={"date": "%td"})
        ep = dr._STATA_EPOCH_UNIX_MS
        # Flipped: test_a_td_range_is_in_milliseconds -- the range() ends
        # alone were wrong because twoway ticks a default date axis by
        # tsnatscale over its data and spans its ticks and range() (P1.3b,
        # M1; measured 08oct2026: range() does not join a default date
        # axis's ticks).
        lo, hi = ep + 14900 * _DAY, ep + 15400 * _DAY
        ticks = dr._dash_axis_count_ticks(ep + 14977 * _DAY,
                                          ep + 14985 * _DAY, 5, "td")
        assert [float(t) for t in fig.xaxis[0].ticker.ticks] == ticks
        assert _approx(hull(fig.x_range),
                       (min(ticks + [lo]), max(ticks + [hi])), rel=1e-9)

    def test_a_degenerate_hull_is_widened_by_one_unit(self, mode, tmp_path):
        df = pd.DataFrame({"mpg": [20.0], "weight": [3000.0]})
        fig = _one(mode, tmp_path, {"yscale": "range(20 20)"}, df=df)
        assert _is(fig.y_range, "Range1d")
        assert fig.y_range.start < 20.0 < fig.y_range.end
        # WP-30 P1.3a: natscale on one value gives [19, 21] (reached), and
        # the hull is padded by twoway's margin, not 5%.
        p = fig._dash_margin["y"] / (1 - 2 * fig._dash_margin["y"]) * 2.0
        assert fig.y_range.start == pytest.approx(19.0 - p)
        assert fig.y_range.end == pytest.approx(21.0 + p)


# ---------------------------------------------------------------------------
# reverse (BR-18.5)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestReverse:

    def test_reverse_with_a_range_is_start_above_end(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "reverse range(0 50)"})
        assert _is(fig.y_range, "Range1d")
        assert fig.y_range.start > fig.y_range.end
        assert _approx(hull(fig.y_range), (0.0, 50.0))

    def test_reverse_alone_keeps_the_flipped_datarange(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "reverse"})
        # WP-30 P1.3a: a flipped DataRange1d was wrong because every axis is
        # now a Range1d over its hull; reversed, it runs high to low.
        assert _is(fig.y_range, "Range1d")
        assert fig.y_range.start > fig.y_range.end
        assert _approx(hull(fig.y_range), (10.0, 41.0))


# ---------------------------------------------------------------------------
# #N over the widened scale (BR-18.6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestCountTicksOverTheHull:

    def test_hash5_with_range_100_ticks_over_the_widened_scale(
            self, mode, tmp_path, truth):
        gs = truth["probes"]["b2_hash5_range100"]["graph_scale"]["y"]
        lo, hi, step = gs["major_min"], gs["major_max"], gs["major_delta"]
        want = [lo + i * step for i in range(int(round((hi - lo) / step)) + 1)]
        fig = _one(mode, tmp_path, {"ylabel": "#5", "yscale": "range(100)"})
        (ax,) = fig.yaxis
        assert list(ax.ticker.ticks) == pytest.approx(want)
        h = hull(fig.y_range)
        assert h[0] <= min(want) + 1e-9 and h[1] >= max(want) - 1e-9


# ---------------------------------------------------------------------------
# The second axes (BR-18.7)
# ---------------------------------------------------------------------------

_Y2 = [_sc(), _sc("price", yaxis="2")]


@pytest.mark.parametrize("mode", _MODES)
class TestSecondAxes:

    def test_yscale2_range_widens_only(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale2": "range(0 20000)"}, plots=_Y2)
        assert _approx(hull(fig.extra_y_ranges["y2"]), (0.0, 20000.0))
        fig = _one(mode, tmp_path, {"yscale2": "range(5000 6000)"}, plots=_Y2)
        # WP-30 P1.3a: 3291 was wrong because the second axis's default
        # natscale ticks (0(5000)15000, twoway's P17) join its hull.
        assert _approx(hull(fig.extra_y_ranges["y2"]), (0.0, 15906.0))

    def test_ylabel2_positions_widen_y2(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"ylabel2": "0(10000)30000"}, plots=_Y2)
        assert _approx(hull(fig.extra_y_ranges["y2"]), (0.0, 30000.0))

    def test_norescale_on_ylabel2(self, mode, tmp_path):
        notes = []
        fig = _one(mode, tmp_path,
                   {"ylabel2": "0 10000 20000 30000, norescale"},
                   plots=_Y2, notes=notes)
        assert _approx(hull(fig.extra_y_ranges["y2"]), (3291.0, 15906.0))
        assert not [n for n in notes if "norescale" in n], notes

    def test_yscale2_reverse_swaps(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale2": "rev range(0 20000)"},
                   plots=_Y2)
        rng = fig.extra_y_ranges["y2"]
        assert rng.start > rng.end
        assert _approx(hull(rng), (0.0, 20000.0))


# ---------------------------------------------------------------------------
# by() panels share one hull (BR-18.8)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestByPanels:

    def test_by_with_range_0_gives_every_panel_one_hull(self, mode,
                                                         tmp_path):
        figs = _figures(mode, tmp_path, _auto(), [_sc()],
                        {"by": "foreign", "yscale": "range(0)"})
        assert len(figs) == 2
        ends = {(f.y_range.start, f.y_range.end) for f in figs}
        assert len(ends) == 1, ends
        for f in figs:
            assert _is(f.y_range, "Range1d")
            assert _approx(hull(f.y_range), (0.0, 41.0))


# ---------------------------------------------------------------------------
# Computed layers and bars (BR-18.3)
# ---------------------------------------------------------------------------

def _glyph_renderers(fig, name):
    return [r for r in fig.renderers
            if type(getattr(r, "glyph", None)).__name__ == name]


@pytest.mark.parametrize("mode", _MODES)
class TestComputedLayers:

    def test_a_fit_beside_a_scatter_with_range_0(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"yscale": "range(0)"},
                   plots=[_sc(), {"type": "lfit", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}])
        lo, hi = hull(fig.y_range)
        assert lo == pytest.approx(0.0)
        fit_y = []
        for r in fig.renderers:
            if r.data_source is not None and "y" in r.data_source.data \
                    and type(r.glyph).__name__ == "Line":
                fit_y.extend(float(v) for v in r.data_source.data["y"])
        assert fit_y and hi >= max(fit_y) - 1e-9
        # WP-30 P1.3a: an x autorange limited to the scatter was wrong
        # because every axis is now a Range1d over every drawn layer.
        assert _is(fig.x_range, "Range1d")


@pytest.mark.parametrize("mode", _MODES)
class TestBars:

    def test_a_bar_keeps_its_outer_half_width(self, mode, tmp_path):
        fig = _one(mode, tmp_path, {"xscale": "range(0)"},
                   plots=[{"type": "bar", "yvar": "mpg", "xvar": "weight",
                           "options": {}}])
        (r,) = _glyph_renderers(fig, "VBar")
        w = r.glyph.width
        if isinstance(w, (int, float)):
            half = float(w) / 2.0
        else:
            field = w if isinstance(w, str) else w.get("field") \
                if isinstance(w, dict) else w.field
            half = float(np.nanmax(np.asarray(r.data_source.data[field],
                                              dtype=float))) / 2.0
        lo, hi = hull(fig.x_range)
        assert lo == pytest.approx(0.0)
        # WP-30 P1.3a: the bar's outer half-width is in the hull; the
        # natscale ticks (to 5000) now reach past it, as twoway's do.
        assert hi == pytest.approx(max(4840.0 + half, 5000.0))
        assert hi > 4840.0 + half - 1e-9


# ---------------------------------------------------------------------------
# Both modes limit their autoranges to the same renderers (BR-18.10)
# ---------------------------------------------------------------------------

class TestPrimaryRenderersInBothModes:

    def test_the_served_datarange_is_limited_like_the_saved_one(self,
                                                                 tmp_path):
        plots = [_sc(), {"type": "lfit", "yvar": "mpg", "xvar": "weight",
                         "options": {}}]
        got = {}
        for mode in _MODES:
            fig = _one(mode, tmp_path, {}, plots=plots)
            # WP-30 P1.3a: a renderer list was wrong because the axis is
            # now a Range1d over every drawn layer, the same in both modes.
            got[mode] = (type(fig.x_range).__name__,
                         tuple(round(v, 9) for v in hull(fig.x_range)))
        assert got["saved"] == got["served"], got
        assert got["saved"][0] == "Range1d"

    def test_the_parity_profile_records_renderers_and_direction(self,
                                                                tmp_path):
        fig = _one("saved", tmp_path, {"yscale": "reverse range(0 50)"})
        prof = tp._axes(fig)
        assert "renderers" in prof["x_range"] and "reversed" in prof["x_range"]
        assert prof["y_range"]["reversed"] is True


# ---------------------------------------------------------------------------
# The helpers
# ---------------------------------------------------------------------------

class TestTheHelpers:

    @pytest.mark.parametrize("kind", [None, "log", "td"])
    @pytest.mark.parametrize("reverse", [False, True])
    def test_range_hull_inverts_padded_range(self, kind, reverse):
        lo, hi = (1000.0, 20000.0) if kind == "log" else (-3.0, 41.0)
        rng = dr._dash_padded_range(lo, hi, kind, reverse)
        assert type(rng).__name__ == "Range1d"
        assert (rng.start > rng.end) is reverse
        assert _approx(dr._dash_range_hull(rng, kind), (lo, hi), rel=1e-9)

    def test_range_reversed(self):
        from bokeh.models import DataRange1d, Range1d
        assert dr._dash_range_reversed(Range1d(start=5, end=1)) is True
        assert dr._dash_range_reversed(Range1d(start=1, end=5)) is False
        assert dr._dash_range_reversed(DataRange1d(flipped=True)) is True
        assert dr._dash_range_reversed(DataRange1d()) is False

    def test_axis_hull_returns_none_without_an_explicit_value(self,
                                                              tmp_path):
        # WP-30 P1.3a: None was wrong because every axis has a hull (its
        # data and ticks); None is left for an axis where nothing is finite.
        fig = _one("saved", tmp_path, {"ylabel": "#5"})
        entries = dr._dash_count_axes(fig, every_axis=True)
        assert entries
        assert all(dr._dash_axis_hull(fig, e) is not None for e in entries)
        for e in entries:
            e.update(lo=None, hi=None, base=None)
            e["ax"] = type("A", (), {"ticker": None})()
            e["pool"] = []
        assert [dr._dash_axis_hull(fig, e) for e in entries] == \
            [None] * len(entries)

    def test_limit_ranges_to_primary(self):
        from bokeh.models import ColumnDataSource, DataRange1d
        from bokeh.plotting import figure
        fig = figure()
        a, b = ColumnDataSource({"x": [1], "y": [1]}), \
            ColumnDataSource({"x": [2], "y": [2]})
        ra = fig.scatter("x", "y", source=a)
        fig.line("x", "y", source=b)
        rb = fig.renderers[1]
        dr._dash_limit_ranges_to_primary(fig, a)
        assert isinstance(fig.x_range, DataRange1d)
        # WP-30 P1.3a: [ra] was wrong because twoway's scale spans every
        # drawn layer, the second source's line included.
        assert list(fig.x_range.renderers) == [ra, rb]
        assert list(fig.y_range.renderers) == [ra, rb]

    def test_hull_ranges_leaves_an_axis_without_a_hull(self, tmp_path):
        # WP-30 P1.3a: an axis with data now has a hull; one whose entries
        # draw nothing finite keeps its range.
        from bokeh.models import DataRange1d
        fig = _one("saved", tmp_path, {})
        es = dr._dash_count_axes(fig, every_axis=True)
        for e in es:
            e.update(lo=None, hi=None, base=None, pool=[])
            e["ax"] = type("A", (), {"ticker": None})()
        fig.y_range = DataRange1d()
        fig.x_range = DataRange1d()
        dr._dash_hull_ranges(fig, es)
        assert _is(fig.y_range, "DataRange1d")
        assert fig._dash_hull_entries == []


# ---------------------------------------------------------------------------
# Against twoway's own drawing (axis_truth.json, group b2_extent)
# ---------------------------------------------------------------------------

#: probe id -> (plots, graph options, axis, kind) for the probes dash draws
#: from the same command on an auto-like frame.
_SAME = {
    "b2_ylab_0_100": ([_sc()], {"ylabel": "0(20)100"}, "y", None),
    "b2_ylab_pair": ([_sc()], {"ylabel": '0 "zero" 60 "sixty"'}, "y", None),
    "b2_ylab_0_100_nr": ([_sc()], {"ylabel": "0(20)100, norescale"}, "y",
                         None),
    "b2_ytick_rule_nr": ([_sc()], {"ytick": "0(20)100, norescale"}, "y",
                         None),
    "b2_ytick_50": ([_sc()], {"ytick": "50"}, "y", None),
    "b2_range_100": ([_sc()], {"yscale": "range(100)"}, "y", None),
    "b2_range_0": ([_sc()], {"yscale": "range(0)"}, "y", None),
    "b2_range_20_30": ([_sc()], {"yscale": "range(20 30)"}, "y", None),
    "b2_r_0_100": ([_sc()], {"yscale": "r(0 100)"}, "y", None),
    "b2_range_dot_60": ([_sc()], {"yscale": "range(. 60)"}, "y", None),
    "b2_range_60_dot": ([_sc()], {"yscale": "range(60 .)"}, "y", None),
    "b2_range_unsorted": ([_sc()], {"yscale": "range(100 0)"}, "y", None),
    "b2_range_three": ([_sc()], {"yscale": "range(0 50 100)"}, "y", None),
    "b2_log_range": ([_sc("price")], {"yscale": "log range(1000 20000)"},
                     "y", "log"),
    "b2_log_r_one": ([_sc("price")], {"yscale": "log r(100000)"}, "y",
                     "log"),
    "b2_rev_range": ([_sc()], {"yscale": "reverse range(0 50)"}, "y", None),
    "b2_xlab_wide": ([_sc()], {"xlabel": "0(1000)6000"}, "x", None),
}


def _b2(truth):
    return {k: v for k, v in truth["probes"].items()
            if v.get("group") == "b2_extent"}


class TestAgainstTwoway:

    def test_every_probe_contains_its_requested_hull(self, truth):
        rule = truth["findings"]["range_rule"]["per_probe"]
        probes = _b2(truth)
        assert len(probes) == 27, sorted(probes)
        verified = 0
        for pid, p in probes.items():
            if p.get("rc") != 0 or rule[pid].get("unverified"):
                continue
            verified += 1
            assert rule[pid]["contains_requested"] is True, (pid, rule[pid])
            assert rule[pid]["narrower_than_data"] is False, (pid, rule[pid])
        assert verified >= 23, verified
        assert truth["findings"]["range_rule"]["all_contain_requested"]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", sorted(_SAME))
    def test_dashs_hull_is_the_requested_hull(self, truth, tmp_path, mode,
                                              pid):
        plots, go, axis, kind = _SAME[pid]
        req = truth["probes"][pid]["requested"][axis]
        fig = _one(mode, tmp_path, go, plots=plots)
        rng = fig.y_range if axis == "y" else fig.x_range
        # WP-30 P1.3a: the requested hull alone was wrong because the axis's
        # placed ticks join the hull, as twoway's scale spans them.
        ax = (fig.yaxis if axis == "y" else fig.xaxis)[0]
        t = ax.ticker
        t = (t.args or {}).get("base", t) if hasattr(t, "args") else t
        ticks = [float(v) for v in getattr(t, "ticks", None) or []
                 if kind != "log" or v > 0]
        want = (min([req[0]] + ticks), max([req[1]] + ticks))
        assert _approx(hull(rng, kind), want, rel=1e-6), (pid, req)

    @pytest.mark.parametrize("mode", _MODES)
    def test_dashs_hull_is_statas_inner_hull_where_ticks_stay_inside(
            self, truth, tmp_path, mode):
        checked = 0
        for pid, (plots, go, axis, kind) in sorted(_SAME.items()):
            p = truth["probes"][pid]
            if not p.get("stata_inner_is_requested", {}).get(axis):
                continue
            inner = p["stata_inner"][axis]
            fig = _one(mode, tmp_path, go, plots=plots)
            rng = fig.y_range if axis == "y" else fig.x_range
            lo, hi = hull(rng, kind)
            span = inner[1] - inner[0]
            assert abs(lo - inner[0]) <= 1e-3 * span, (pid, lo, inner)
            assert abs(hi - inner[1]) <= 1e-3 * span, (pid, hi, inner)
            checked += 1
        assert checked >= 3, checked

    def test_norescale_probes_were_not_widened_by_twoway(self, truth):
        """A list with norescale is not widened; a lone a(b)c rule loses
        norescale in twoway and is (the rule dash follows)."""
        rr = truth["findings"]["range_rule"]
        assert rr["norescale_not_widened"] is True
        assert rr["norescale_dropped_by_a_lone_rule"] is True
        for pid in ("b2_ylab_list_nr", "b2_ytick_50_nr", "b2_xtick_nr"):
            assert rr["per_probe"][pid]["widened_vs_default"] is False, pid
        for pid in ("b2_ylab_0_100_nr", "b2_ytick_rule_nr"):
            assert rr["per_probe"][pid]["widened_vs_default"] is True, pid

    def test_the_graph_scale_verdict_is_recorded(self, truth):
        g = truth["findings"]["graph_scale_matches_svg"]
        print("graph_scale_matches_svg verdict:", g["verdict"],
              "inner:", g["verdict_inner"])
        answers = ("min/max", "curmin/curmax", "both", "none", "mixed")
        assert g["verdict"] in answers and g["verdict_inner"] in answers

    def test_the_fixture_meta_carries_the_four_provenance_keys(self, truth):
        m = truth["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert k in m, k
        assert "scheme_in_force" in m
