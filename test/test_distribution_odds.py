"""
test_distribution_odds.py -- histogram gap() and baroffset(), kdensity
area() and boundary, function droplines() and base(), area nodropbase and
bar baroffset() are drawn as twoway draws them (WP-31 C5).

The defect (GAPS3 C5, re-verified at e0a9cf1): the seven were named in the
"ignoring" note and not drawn -- histogram bars filled their bins, the
density was never scaled or widened, no dropline was drawn, an area always
dropped to its base and an offset bar stood on its x.

twoway's truth (StataNow 19.5, scripts/extract_kde_hist_fn_truth.do,
fixture test/fixtures/kde_hist_fn_truth.json): gap(20) makes a bar 0.8 of
its bin (bar_size 2.9 = 3.625 * .8); baroffset(.5) moves it half a bar;
area(74) multiplies the density by 74; boundary runs the grid from
min - h to max + h; droplines(-1 1) holds the pairs "-1 1" "1 1"; and
nodropbase sets drop_base "no".
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
from js_runner import requires_node  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "kde_hist_fn_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json"),
          encoding="utf-8") as _fh:
    _AUTO = json.load(_fh)["datasets"]["auto"]

_MODES = ("saved", "served")
_ROOT = os.path.join(_HERE, "..")


def _auto():
    return pd.DataFrame({"mpg": _AUTO["mpg"], "weight": _AUTO["weight"]})


def _figs(mode, tmp_path, plots, df=None, formats=None):
    return bg._figs(mode, tmp_path, bg._spec(plots, formats),
                    _auto() if df is None else df)


def _one(figs, name):
    [r] = bg._glyphs(figs, name)
    return r


def _col(r, key):
    return np.asarray(r.data_source.data[key], dtype=float)


def _hist(mode, tmp_path, **o):
    figs, notes = _figs(mode, tmp_path,
                        [{"type": "histogram", "var": "mpg", "options": o}])
    return _one(figs, "Quad"), notes


def _kde(mode, tmp_path, **o):
    figs, notes = _figs(mode, tmp_path,
                        [{"type": "kdensity", "var": "mpg", "options": o}])
    rs = [r for f in figs for r in f.renderers
          if type(getattr(r, "glyph", None)).__name__ == "Line"]
    return rs[0], notes


def _serset_x(key):
    s = _T[key]["serset"]
    # The density's grid: the serset column that is not mpg and spans
    # past the data under boundary.
    return [c for h, c in s.items() if h != "mpg"]


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]
        assert all(_T["_meta"][k] for k in _T["_meta"])

    def test_what_twoway_measured(self):
        assert _T["H01"]["bar_size"] == pytest.approx(
            _T["H00"]["bar_size"] * .8)
        assert _T["H04"]["bar_offset"] == .5
        assert _T["K02"]["message"] == "option area() expects a positive number"
        assert _T["K04"]["message"] == \
            "only one of options range() or boundary is allowed"
        assert _T["H02"]["message"] == "option gap() must be between 0 and 100"
        assert _T["F02"]["message"] == "some droplines not within range() option"
        assert _T["F01"]["droplines"] == '"-1 1" "1 1"'
        assert _T["A01"]["drop_base"] == "no"
        assert _T["B01"]["bar_offset"] == .5


# ---------------------------------------------------------------------------
# histogram gap() and baroffset()
# ---------------------------------------------------------------------------

def _bins(mode, tmp_path):
    r, _ = _hist(mode, tmp_path)
    return _col(r, "left"), _col(r, "right")


@pytest.mark.parametrize("mode", _MODES)
class TestHistogramGap:

    def test_bars_are_shrunk_about_their_centre(self, mode, tmp_path):
        L0, R0 = _bins(mode, tmp_path)
        r, notes = _hist(mode, tmp_path, gap="20")
        L, R = _col(r, "left"), _col(r, "right")
        assert R - L == pytest.approx([_T["H01"]["bar_size"]] * len(L))
        assert (L + R) / 2 == pytest.approx((L0 + R0) / 2)
        # twoway's bin centres (serset) are where the bars stand.
        centres = sorted(_T["H01"]["serset"]["__000002"])
        assert sorted((L + R) / 2) == pytest.approx(centres)
        assert not [n for n in notes if "gap" in n]

    def test_gap_zero_is_unchanged(self, mode, tmp_path):
        L0, R0 = _bins(mode, tmp_path)
        r, _ = _hist(mode, tmp_path, gap="0")
        assert _col(r, "left") == pytest.approx(L0)
        assert _col(r, "right") == pytest.approx(R0)

    def test_baroffset_shifts(self, mode, tmp_path):
        L0, R0 = _bins(mode, tmp_path)
        r, _ = _hist(mode, tmp_path, baroffset=".5", gap="20")
        L, R = _col(r, "left"), _col(r, "right")
        size = _T["H08"]["bar_size"]
        assert R - L == pytest.approx([size] * len(L))
        assert (L + R) / 2 == pytest.approx((L0 + R0) / 2 + .5 * size)


class TestHistogramConfig:

    def test_config_keys(self):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        gm = bg._gm()
        src = ColumnDataSource({"mpg": _AUTO["mpg"]})
        r = gm.map_histogram(figure(), src, "mpg",
                             {"gap": "20", "baroffset": ".5"})
        assert r._dash_agg_config["gap"] == 20.0
        assert r._dash_agg_config["baroffset"] == .5
        r = gm.map_histogram(figure(), src, "mpg", {})
        assert r._dash_agg_config["gap"] == 0.0
        assert r._dash_agg_config["baroffset"] == 0.0

    def test_helper(self):
        L, R = dr.GlyphMapper._hist_bar_edges([0.0, 2.0], [2.0, 4.0], 50, 1)
        assert list(L) == [1.5, 3.5] and list(R) == [2.5, 4.5]
        L, R = dr.GlyphMapper._hist_bar_edges([0.0], [2.0])
        assert list(L) == [0.0] and list(R) == [2.0]


# ---------------------------------------------------------------------------
# kdensity area() and boundary
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestKdensityArea:

    def test_density_times_area(self, mode, tmp_path):
        r0, _ = _kde(mode, tmp_path)
        r, notes = _kde(mode, tmp_path, area="74")
        assert _col(r, "y") == pytest.approx(_col(r0, "y") * 74, rel=1e-12)
        ys = [c for c in _serset_x("K01") if max(c) < 10]
        assert max(_col(r, "y")) == pytest.approx(max(ys[0]), rel=1e-6)
        assert not [n for n in notes if "area" in n]


@pytest.mark.parametrize("mode", _MODES)
class TestKdensityBoundary:

    def test_grid_extends_one_bandwidth(self, mode, tmp_path):
        mpg = np.asarray(_AUTO["mpg"], dtype=float)
        h = dr._stata_kde_bandwidth(mpg)
        r, notes = _kde(mode, tmp_path, boundary="boundary")
        x = _col(r, "x")
        assert x[0] == pytest.approx(mpg.min() - h, rel=1e-12)
        assert x[-1] == pytest.approx(mpg.max() + h, rel=1e-12)
        r, _ = _kde(mode, tmp_path, boundary="boundary", bwidth="2")
        x = _col(r, "x")
        assert (x[0], x[-1]) == pytest.approx((10.0, 43.0))
        assert not [n for n in notes if "boundary" in n]

    def test_matches_twoway(self, mode, tmp_path):
        for key, o in (("K03", {"boundary": "boundary"}),
                       ("K05", {"boundary": "boundary", "bwidth": "2"})):
            r, _ = _kde(mode, tmp_path, **o)
            x = _col(r, "x")
            grid = [c for c in _serset_x(key) if min(c) > 5][0]
            assert (x[0], x[-1]) == pytest.approx((min(grid), max(grid)),
                                                  rel=1e-9), key


class TestKdensityConfig:

    def test_config_keys(self):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        gm = bg._gm()
        src = ColumnDataSource({"mpg": _AUTO["mpg"]})
        r = gm.map_kdensity(figure(), src, "mpg",
                            {"area": "74", "boundary": "boundary"})
        assert r._dash_agg_config["area"] == 74.0
        assert r._dash_agg_config["boundary"] is True
        r = gm.map_kdensity(figure(), src, "mpg", {})
        assert r._dash_agg_config["area"] == 1.0
        assert r._dash_agg_config["boundary"] is False


# ---------------------------------------------------------------------------
# function droplines() and base()
# ---------------------------------------------------------------------------

def _fn_points(lo=-2.0, hi=2.0, n=300, drops=None):
    dx = (hi - lo) / (n - 1)
    pts = {"x0": lo, "dx": dx,
           "y": [float((lo + dx * i) ** 2) for i in range(n)]}
    if drops is not None:
        pts["drops"] = drops
    return pts


def _fn(mode, tmp_path, o, points="auto"):
    # A spec written by hand holds the expression alone (the fallback
    # interpreter reads no "y =").
    p = {"type": "function", "expr": "x^2" if points is None else "y = x^2",
         "options": o}
    if points == "auto":
        p["points"] = _fn_points(drops=[[-1.0, 1.0], [1.0, 1.0]])
    elif points is not None:
        p["points"] = points
    figs, notes = _figs(mode, tmp_path, [p], df=pd.DataFrame({"z": [1.0]}))
    [f] = [f for f in figs if any(
        type(getattr(r, "glyph", None)).__name__ == "Line"
        for r in f.renderers)]
    return f, notes


def _segs(f):
    return [r for r in f.renderers
            if type(getattr(r, "glyph", None)).__name__ == "Segment"]


@pytest.mark.parametrize("mode", _MODES)
class TestDroplines:

    def test_segments_drawn_before_the_curve(self, mode, tmp_path):
        f, notes = _fn(mode, tmp_path, {"range": "-2 2", "droplines": "-1 1",
                                        "base": "1"})
        [s] = _segs(f)
        kinds = [type(getattr(r, "glyph", None)).__name__
                 for r in f.renderers]
        assert kinds.index("Segment") < kinds.index("Line")
        d = s.data_source.data
        assert list(d["x0"]) == [-1.0, 1.0] == list(d["x1"])
        assert list(d["y0"]) == [1.0, 1.0]
        assert list(d["y1"]) == [1.0, 1.0]
        assert not [n for n in notes if "droplines" in n or "base" in n]

    def test_default_base_is_tagged(self, mode, tmp_path):
        f, _ = _fn(mode, tmp_path, {"range": "-2 2", "droplines": "-1 1"})
        [s] = _segs(f)
        [tag] = [t for t in s.tags if str(t).startswith("dash_base:")]
        assert json.loads(tag[len("dash_base:"):])["auto"] is True
        # The y scale spans 0, so twoway's base is 0 (F09).
        assert list(s.data_source.data["y0"]) == [0.0, 0.0]

    def test_stored_drops_win(self, mode, tmp_path):
        f, _ = _fn(mode, tmp_path, {"range": "-2 2", "droplines": ".5"},
                   points=_fn_points(drops=[[.5, 99.0]]))
        [s] = _segs(f)
        assert list(s.data_source.data["y1"]) == [99.0]

    def test_older_points_are_interpolated(self, mode, tmp_path):
        f, _ = _fn(mode, tmp_path, {"range": "-2 2", "droplines": "-1 1"},
                   points=_fn_points())
        [s] = _segs(f)
        assert list(s.data_source.data["y1"]) == pytest.approx([1.0, 1.0],
                                                               abs=1e-3)

    def test_a_hand_written_spec_evaluates(self, mode, tmp_path):
        f, _ = _fn(mode, tmp_path, {"range": "-2 2", "droplines": "-1 1"},
                   points=None)
        [s] = _segs(f)
        assert list(s.data_source.data["y1"]) == pytest.approx([1.0, 1.0])

    def test_no_droplines_no_segment(self, mode, tmp_path):
        f, _ = _fn(mode, tmp_path, {"range": "-2 2"}, points=_fn_points())
        assert _segs(f) == []


class TestDroplineHelpers:

    def test_helper(self):
        f = dr._dash_numlist_floats
        assert f("1 -1 .5") == [-1.0, .5, 1.0]
        assert f("1,2") == [1.0, 2.0]
        assert f("a 2 inf nan") == [2.0]
        assert f(None) == [] and f(["1"]) == [] and f(True) == []
        assert f("") == []

    def test_function_drops(self):
        g = dr._dash_function_drops
        x, y = g({"drops": [[-1, 1], [1, None]]})
        assert list(x) == [-1.0, 1.0] and y[0] == 1.0 and np.isnan(y[1])
        for bad in ({}, {"drops": []}, {"drops": [[1]]},
                    {"drops": [[True, 1]]}, {"drops": [["1", 1]]},
                    {"drops": [[1e400, 1]]}, {"drops": "1 1"}, None):
            assert g(bad) is None, bad


# ---------------------------------------------------------------------------
# area nodropbase
# ---------------------------------------------------------------------------

_XS = [1.0, 2, 3, 4, 5]


@pytest.mark.parametrize("mode", _MODES)
class TestNodropbase:

    def test_patch_closes_on_the_chord(self, mode, tmp_path):
        figs, notes = bg._figs(
            mode, tmp_path,
            bg._spec([{"type": "area", "yvar": "y", "xvar": "x",
                       "options": {"nodropbase": "nodropbase"}}]),
            bg._frame(_XS))
        r = _one(figs, "Patch")
        d = r.data_source.data
        xs = np.asarray(d[r.glyph.x], dtype=float)
        ys = np.asarray(d[r.glyph.y], dtype=float)
        assert list(xs) == _XS
        assert list(ys) == bg._Y
        assert not bg._glyphs(figs, "VArea")
        assert not [n for n in notes if "dropbase" in n]

    def test_default_is_varea(self, mode, tmp_path):
        figs, _ = bg._figs(
            mode, tmp_path,
            bg._spec([{"type": "area", "yvar": "y", "xvar": "x",
                       "options": {}}]),
            bg._frame(_XS))
        assert _one(figs, "VArea") is not None
        assert not bg._glyphs(figs, "Patch")


# ---------------------------------------------------------------------------
# bar baroffset()
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestBaroffset:

    def test_numeric(self, mode, tmp_path):
        figs, notes = bg._figs(mode, tmp_path,
                               bg._spec([bg._bar("bar", baroffset=".5")]),
                               bg._frame(_XS))
        r = bg._vbar(figs)
        assert getattr(r.glyph.x, "field", r.glyph.x) == "__dash_bar_xc"
        xc = _col(r, "__dash_bar_xc")
        # B01: bar_size 1, bar_offset .5 -- each centre half a bar right.
        assert list(xc) == pytest.approx(
            [x + _T["B01"]["bar_offset"] * _T["B01"]["bar_size"]
             for x in _XS])
        assert bg._width_value(r) == pytest.approx(1.0)
        assert not [n for n in notes if "baroffset" in n]
        figs, _ = bg._figs(mode, tmp_path,
                           bg._spec([bg._bar("bar", baroffset="-.5",
                                             barwidth="2")]),
                           bg._frame(_XS))
        assert list(_col(bg._vbar(figs), "__dash_bar_xc")) == \
            pytest.approx([x - 1.0 for x in _XS])

    def test_period_axis(self, mode, tmp_path):
        base = 720.0
        df = bg._frame([base + k for k in range(5)])
        figs, _ = bg._figs(mode, tmp_path,
                           bg._spec([bg._bar("bar", baroffset=".5")],
                                    {"x": "%tm"}), df)
        r = bg._vbar(figs)
        u = np.array([base + k for k in range(5)]) + .5
        lo = dr._dash_units_to_axis(u - .5, "tm")
        hi = dr._dash_units_to_axis(u + .5, "tm")
        assert _col(r, "__dash_bar_xc") == pytest.approx((lo + hi) / 2,
                                                         abs=1.0)
        assert _col(r, "__dash_bar_w") == pytest.approx(hi - lo, abs=1.0)

    def test_no_offset_is_unchanged(self, mode, tmp_path):
        figs, _ = bg._figs(mode, tmp_path, bg._spec([bg._bar("bar")]),
                           bg._frame(_XS))
        assert bg._vbar(figs).glyph.x.field == "x" \
            if hasattr(bg._vbar(figs).glyph.x, "field") \
            else bg._vbar(figs).glyph.x == "x"


# ---------------------------------------------------------------------------
# The served copy and the ado text
# ---------------------------------------------------------------------------

class TestTheServedCopy:

    def test_names(self):
        src = open(os.path.join(_ROOT, "dash_render.py"),
                   encoding="utf-8").read()
        for name in ("_dash_numlist_floats", "_dash_function_drops"):
            assert '"%s"' % name in src, name


def _ado():
    return open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()


def _mata():
    return open(os.path.join(_ROOT, "dash_parse.mata"),
                encoding="utf-8").read()


class TestTheAdoText:

    def test_declared(self):
        ado = _ado()
        for decl in ("GAP(string)", "BAROFFset(string)", "AREA(string)",
                     "BOUNDARY", "DROPlines(string)", "noDROPBase"):
            assert decl in ado, decl
        for key in ("gap", "baroffset", "area", "boundary", "droplines",
                    "nodropbase"):
            assert re.search(r"sreturn local %s +: copy local" % key, ado), key

    def test_no_und_rows_for_the_declared(self):
        m = _mata()
        assert '("baroffset",' not in m
        assert '("boundary",' not in m

    def test_twoways_words(self):
        ado = _ado()
        for key in ("H02", "K02", "K04", "F02", "F04"):
            msg = _T[key]["message"]
            if key == "F04":
                msg = "option base() incorrectly specified, "
            assert msg in ado, key


# ---------------------------------------------------------------------------
# The saved page after a move: a boundary density keeps the grid cue
# ---------------------------------------------------------------------------

class TestBoundaryAfterASavedMove:
    """The saved page re-estimates a kdensity on the build's grid; with
    boundary that grid is [min - h, max + h] of every row, where twoway's
    would be the kept rows' -- so, like any kdensity without range(), the
    layer keeps the "grid" stale cue (WP-29 P0.17), never a silent
    difference (WP-31 C5)."""

    def test_the_kind_is_grid(self):
        assert dr._dash_stale_kind("kdensity",
                                   {"boundary": "boundary"}) == "grid"
        assert dr._dash_stale_kind("kdensity",
                                   {"boundary": "boundary",
                                    "area": "74"}) == "grid"

    @requires_node
    def test_a_move_marks_it(self):
        import test_saved_stale_cue as sc
        from test_mode_parity import _spec
        from test_server_layer_defects import plot_for
        r = sc._render(_spec(
            [plot_for("scatter"),
             plot_for("kdensity", {"boundary": "boundary", "area": "74"})],
            {"filter": "foreign, type(dropdown)"}))
        cue = sc._one_cue(r)
        assert cue.visible is False
        sc._act(r, ("Select", "Foreign"))
        rends = sc._layer_rends(r)
        assert rends and all(x.muted for x in rends)
        assert cue.visible is True
        items = sc._items_of(r.figures["g1"], rends)
        assert items and all(sc._text(i.label).endswith(
            dr._DASH_STALE_SUFFIX["grid"]) for i in items)
