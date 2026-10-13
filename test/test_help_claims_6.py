"""test_help_claims_6.py -- WP-23: dash.sthlp's "Statistical Layer Options"
and "Weights" sections, claim by claim (ROADMAP WP-23 AC-23.1, TR-23.3).

Every claim of those two sections is either pinned here or in
``test/test_help_claims_6.cscript`` (the Stata side: what dash.ado accepts,
refuses and writes, measured beside real twoway in the same run), or by an
existing test named in the WP-23 ledger.  Claims about twoway rest on
measurements made with the console binary on 23sep2026 (StataNow 19.5):
each constant below names the twoway command it was read from, and the
plotted points are the serset of the saved ``.gph``, read back with
``graph use`` / ``serset use`` as ROADMAP WP-18's probe notes describe.

The renderer is checked in BOTH render modes -- the saved page
(``DashRenderer``) and the served app (``ServerAppBuilder`` +
``make_document`` on a bokeh ``Document``) -- through the helpers
``test_adversarial_matrix.py`` already uses for that.

What this file found (each with a failing test first, then the fix):

* ``range(# #)`` on ``lfit``, ``qfit``, ``lfitci`` and ``qfitci`` was
  accepted and ignored: the line was drawn over the observed range and
  nothing said so, where twoway draws it over the range given (measured:
  ``twoway lfit mpg weight, range(1000 6000)`` runs 1000 to 6000).
  ``kdensity``'s ``range()`` given high-then-low was refused with a
  warning, where twoway draws the same curve as low-then-high.
* ``width(#)`` on ``kdensity`` -- twoway's synonym for the bandwidth --
  reached the renderer as histogram's bin width and changed nothing.
* ``base(#)`` on ``dropline`` was ignored: the drops always ran to 0.
* ``kernel()`` on ``fpfit`` and ``fpfitci``, which twoway refuses as it
  refuses ``bwidth()`` and ``degree()``, was dropped without the note those
  two get.

The Stata side found three more, in test_help_claims_6.cscript: fpfitci
refused ``stdp`` (HC6-26), kdensity's ``width()`` was registered as the bin
width (HC6-06, 07), and a weight on function, scatteri, pci or pcarrowi got
the wrong code and words (HC6-48).
"""
import ast
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402
from test_adversarial_matrix import (  # noqa: E402
    _app_source, _load_app, _write_inputs)
from test_statistical_helpers import (  # noqa: E402
    _AUTO_FOREIGN, _AUTO_MPG, _AUTO_PRICE, _AUTO_REP78, _AUTO_WEIGHT)

_HELP = os.path.join(_ROOT, "dash.sthlp")
_RENDER = os.path.join(_ROOT, "dash_render.py")
_FIXTURE = os.path.join(_HERE, "fixtures", "stat_truth.json")
_DATA = os.path.join(_HERE, "fixtures", "data")

# sysuse auto, as the columns the claims below are measured on.
#: twoway's default base of `<t> mpg weight' on auto (WP-30 P1.17b;
#: scripts/extract_default_base_truth.do).
with open(os.path.join(_HERE, "fixtures", "default_base_truth.json"),
          encoding="utf-8") as _fh:
    _DEFAULT_BASE = json.load(_fh)["auto"]

_AUTO = pd.DataFrame({
    "mpg": np.asarray(_AUTO_MPG, float),
    "weight": np.asarray(_AUTO_WEIGHT, float),
    "price": np.asarray(_AUTO_PRICE, float),
    "rep78": np.asarray(_AUTO_REP78, float),
    "foreign": np.asarray(_AUTO_FOREIGN, float),
})


# ---------------------------------------------------------------------------
# Both render modes
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


def _renderers(root):
    """Every GlyphRenderer under a saved page's root or a served Document
    (both answer ``select``), a legend's swatch left out: WP-30 P1.15c's
    by() legend draws panel 1's keys from swatch clones on one NaN row."""
    return [r for r in root.select({"type": GlyphRenderer})
            if not dr._dash_is_swatch(r)]


def _both(tmp_path, plots, tag, df=_AUTO, graph_options=None):
    """``{"saved": (renderers, warnings), "served": (renderers, warnings)}``.

    The saved page is ``DashRenderer(...).render()``; the served app is the
    generated source, loaded as a module namespace and given a fresh
    ``Document`` -- the helpers are test_adversarial_matrix.py's.
    """
    spec = make_spec(plots)
    if graph_options:
        spec["graphs"][0]["graph_options"].update(graph_options)
    sp, dp = _write_inputs(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as w1:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    saved = _renderers(r._last_layout_root)
    ns = _load_app(_app_source(tmp_path, spec, df), tag)
    with warnings.catch_warnings(record=True) as w2:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    served = _renderers(doc)
    return {"saved": (saved, [str(x.message) for x in w1]),
            "served": (served, [str(x.message) for x in w2])}


def _data_with(renderers, *keys):
    """The data of each source, carrying every key, that a renderer draws.

    A band layer's line and area share one source, so sources are counted
    once each.
    """
    out, seen = [], set()
    for r in renderers:
        src = r.data_source
        if src.id in seen:
            continue
        seen.add(src.id)
        d = dict(src.data)
        if all(k in d for k in keys):
            out.append({k: np.asarray(d[k], dtype=float) for k in keys})
    return out


def _one(renderers, *keys):
    got = _data_with(renderers, *keys)
    assert got, f"no renderer carries {keys}"
    # A layer's own source is non-empty; the shared scatter source, where
    # there is one, carries the data columns and not these keys.
    got = [g for g in got if len(g[keys[0]])]
    assert len(got) == 1, f"{len(got)} non-empty renderers carry {keys}"
    return got[0]


_MODES = ("saved", "served")


# ===========================================================================
# 1. range(# #) on the fits -- twoway draws the line over the range given
# ===========================================================================
# twoway lfit mpg weight, range(1000 6000), serset 0 of the saved .gph
# (floats): three points, the default for lfit (twoway_lfit_parse.class:
# points = 3).
_LFIT_RANGE = [(1000.0, 33.4315948486328), (3500.0, 18.4098796844482),
               (6000.0, 3.38816261291504)]
# twoway qfit / lfitci / qfitci mpg weight, range(1000 6000): 100 points,
# first and last (x, fit[, lower, upper]).
_QFIT_RANGE_ENDS = [(1000.0, 38.3494186401367), (6000.0, 13.9131460189819)]
_LFITCI_RANGE_ENDS = [(1000.0, 33.4315948486328, 31.1996459960938,
                       35.6635437011719),
                      (6000.0, 3.38816261291504, 0.209617376327515,
                       6.56670761108398)]
_QFITCI_RANGE_ENDS = [(1000.0, 38.3494186401367, 33.2288665771484,
                       43.469970703125),
                      (6000.0, 13.9131460189819, 3.52264165878296,
                       24.3036499023438)]


class TestRangeOnTheFits:
    """``range(# #)`` is read on lfit, qfit, lfitci and qfitci."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_lfit_is_drawn_over_the_range_given(self, tmp_path, mode):
        got = _both(tmp_path, [{"type": "lfit", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"range": "1000 6000"}}],
                    "lfitr")[mode][0]
        d = _one(got, "x", "y")
        assert d["x"][0] == pytest.approx(1000.0)
        assert d["x"][-1] == pytest.approx(6000.0)
        # dash draws the same line at n() = 100 points; every twoway point
        # lies on it.
        for x0, y0 in _LFIT_RANGE:
            assert np.interp(x0, d["x"], d["y"]) == pytest.approx(y0, rel=1e-6)

    @pytest.mark.parametrize("mode", _MODES)
    def test_qfit_is_drawn_over_the_range_given(self, tmp_path, mode):
        got = _both(tmp_path, [{"type": "qfit", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"range": "1000 6000"}}],
                    "qfitr")[mode][0]
        d = _one(got, "x", "y")
        assert len(d["x"]) == 100
        for (x0, y0), i in zip(_QFIT_RANGE_ENDS, (0, -1)):
            assert d["x"][i] == pytest.approx(x0)
            assert d["y"][i] == pytest.approx(y0, rel=1e-6)

    @pytest.mark.parametrize("layer,want", [("lfitci", _LFITCI_RANGE_ENDS),
                                            ("qfitci", _QFITCI_RANGE_ENDS)])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_band_is_drawn_over_the_range_given(self, tmp_path, mode,
                                                    layer, want):
        got = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"range": "1000 6000"}}],
                    layer + "r")[mode][0]
        d = _one(got, "x_fit", "y_fit", "y_lower", "y_upper")
        assert len(d["x_fit"]) == 100
        for (x0, fit, lo, hi), i in zip(want, (0, -1)):
            assert d["x_fit"][i] == pytest.approx(x0)
            assert d["y_fit"][i] == pytest.approx(fit, rel=1e-6)
            assert d["y_lower"][i] == pytest.approx(lo, rel=1e-5, abs=1e-6)
            assert d["y_upper"][i] == pytest.approx(hi, rel=1e-5)

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_two_numbers_may_come_in_either_order(self, tmp_path, mode):
        # twoway lfit mpg weight, range(6000 1000): the same three points,
        # 1000 first.
        got = _both(tmp_path, [{"type": "lfit", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"range": "6000 1000"}}],
                    "lfitrr")[mode][0]
        d = _one(got, "x", "y")
        assert d["x"][0] == pytest.approx(1000.0)
        assert d["x"][-1] == pytest.approx(6000.0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_n_counts_the_points_over_the_range(self, tmp_path, mode):
        # twoway lfit mpg weight, range(1000 6000) n(7): seven points,
        # 1000 to 6000 in equal steps.
        got = _both(tmp_path, [{"type": "lfit", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"range": "1000 6000", "n": "7"}}],
                    "lfitrn")[mode][0]
        d = _one(got, "x", "y")
        np.testing.assert_allclose(d["x"], np.linspace(1000, 6000, 7))

    def test_without_range_the_grid_is_the_observed_range(self):
        """The help: 100 points by default, over the observed range."""
        assert dr._FIT_GRID == 100
        grid = dr._fit_grid(np.array([3.0, 1.0, 2.0]), {})
        assert grid[0] == 1.0 and grid[-1] == 3.0
        assert len(grid) == 100

    def test_function_defaults_to_range_0_1_at_300_points(self):
        """twoway function: range(0 1) and n(300) by default (fixture rules
        function.range and function.n; HC6-18 measures the 300)."""
        assert dr._dash_function_args({}) == ((0.0, 1.0), 300)

    @pytest.mark.parametrize("mode", _MODES)
    def test_function_draws_a_high_then_low_range_as_low_then_high(
            self, tmp_path, mode):
        # twoway function y = x^2, range(1 0) plots range(0 1)'s points
        # (HC6-22).
        def pts(rng, tag):
            got = _both(tmp_path, [{"type": "function", "expr": "x^2",
                                    "options": {"range": rng}}],
                        tag)[mode][0]
            d = _one(got, "x_fn", "y_fn")
            order = np.argsort(d["x_fn"])
            return d["x_fn"][order], d["y_fn"][order]
        a, b = pts("1 0", "fnrr"), pts("0 1", "fnr")
        np.testing.assert_allclose(a[0], b[0], atol=1e-12)
        np.testing.assert_allclose(a[1], b[1], atol=1e-12)


class TestTheFitRangeIsReadSafely:
    """``_fit_grid`` reads ``range()`` as two finite numbers or not at all.

    dash.ado refuses anything but a numlist of two numbers (r(198)); a
    hand-written spec reaches the renderer directly, so the renderer names
    what it cannot read and draws over the observed range.  The number of
    points is ``n()``'s, bounded at 10000 whatever the range.
    """

    @pytest.mark.parametrize("raw", ["abc", "1000", "1 2 3", "nan 5",
                                     "1e999 2", "-inf inf", "1000;6000",
                                     "<script>1</script>", ""])
    def test_an_unreadable_range_draws_the_observed_range(self, raw):
        x = np.array([2.0, 4.0, 8.0])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            grid = dr._fit_grid(x, {"range": raw})
        assert grid[0] == 2.0 and grid[-1] == 8.0
        assert np.all(np.isfinite(grid))
        if raw:
            assert any("range(" in str(m.message) for m in w), raw

    def test_a_huge_range_keeps_the_point_count(self):
        grid = dr._fit_grid(np.array([1.0, 2.0]),
                            {"range": "-1e300 1e300", "n": "10000"})
        assert len(grid) == 10000 and np.all(np.isfinite(grid))

    def test_n_past_its_bound_is_not_honoured(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            grid = dr._fit_grid(np.array([1.0, 2.0]),
                                {"range": "0 1", "n": "100000000"})
        assert len(grid) == dr._FIT_GRID

    def test_equal_ends_draw_one_x(self):
        grid = dr._fit_grid(np.array([1.0, 2.0]), {"range": "3 3"})
        assert np.all(grid == 3.0)


# ===========================================================================
# 2. kdensity: range() in either order, and width() is the bandwidth
# ===========================================================================

class TestKdensityRangeAndWidth:

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_high_then_low_range_is_the_same_span(self, tmp_path, mode):
        # twoway kdensity mpg, range(50 0) draws the curve range(0 50) draws
        # (measured: the two sersets agree to 1.1e-13 in x, 1.4e-15 in y).
        a = _one(_both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                   "options": {"range": "50 0"}}],
                       "kdrr")[mode][0], "x", "y")
        b = _one(_both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                   "options": {"range": "0 50"}}],
                       "kdr")[mode][0], "x", "y")
        np.testing.assert_allclose(a["x"], b["x"])
        np.testing.assert_allclose(a["y"], b["y"])
        assert a["x"][0] == 0.0 and a["x"][-1] == 50.0

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_span_is_the_plots_sample(self, tmp_path, mode):
        # twoway kdensity mpg if foreign: 300 points from 14, the foreign
        # cars' minimum, to 41 (HC6-13).
        got = _both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                "if_expr": "foreign==1", "options": {}}],
                    "kdif")[mode][0]
        x = _one(got, "x", "y")["x"]
        assert (len(x), x[0], x[-1]) == (300, 14.0, 41.0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_width_is_the_bandwidth(self, tmp_path, mode):
        # twoway kdensity mpg, width(2) and bwidth(2): identical sersets.
        a = _one(_both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                   "options": {"width": "2"}}],
                       "kdw")[mode][0], "x", "y")
        b = _one(_both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                   "options": {"bwidth": "2"}}],
                       "kdbw")[mode][0], "x", "y")
        c = _one(_both(tmp_path, [{"type": "kdensity", "var": "mpg",
                                   "options": {}}],
                       "kd0")[mode][0], "x", "y")
        np.testing.assert_allclose(a["y"], b["y"], rtol=1e-12)
        assert not np.allclose(a["y"], c["y"]), (
            "width(2) drew the default bandwidth's curve")

    def test_bwidth_wins_over_width_in_a_hand_written_spec(self, gm):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"mpg": list(_AUTO.mpg)})

        def curve(opts):
            f = figure()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = gm.map_kdensity(f, src, "mpg", opts)
            return np.asarray(r.data_source.data["y"], float)
        np.testing.assert_allclose(curve({"width": "5", "bwidth": "2"}),
                                   curve({"bwidth": "2"}))

    @pytest.mark.parametrize("raw", ["-3", "abc", "inf", "1e999"])
    def test_an_unusable_width_draws_the_default_bandwidth(self, gm, raw):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"mpg": list(_AUTO.mpg)})

        def curve(opts):
            f = figure()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = gm.map_kdensity(f, src, "mpg", opts)
            return np.asarray(r.data_source.data["y"], float)
        np.testing.assert_allclose(curve({"width": raw}), curve({}))


# ===========================================================================
# 3. base() on dropline
# ===========================================================================

class TestDroplineBase:
    """twoway dropline, base(10): the drops run from the point to y = 10
    (measured from the SVG export of ``twoway dropline mpg weight in 1/3,
    base(10)``: the axis starts at 10 and every drop starts there)."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_drops_start_at_base(self, tmp_path, mode):
        got = _both(tmp_path, [{"type": "dropline", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"base": "10"}}],
                    "dlb")[mode][0]
        d = _one(got, "x", "y", "y0")
        assert np.all(d["y0"] == 10.0)
        np.testing.assert_allclose(np.sort(d["y"]), np.sort(_AUTO.mpg))

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_is_zero(self, tmp_path, mode):
        """Flipped: was ``y0 == 0.0`` -- twoway draws a default base as 0
        clamped into the axis's scale (P1.17b): 10 for `dropline mpg
        weight' (fixture default_base_truth.json auto.dropline)."""
        got = _both(tmp_path, [{"type": "dropline", "yvar": "mpg",
                                "xvar": "weight", "options": {}}],
                    "dl0")[mode][0]
        d = _one(got, "x", "y", "y0")
        assert np.all(d["y0"] == _DEFAULT_BASE["dropline"]["drawn_base"])

    @pytest.mark.parametrize("raw", ["abc", "inf", "nan", "1e999", ""])
    def test_an_unusable_base_draws_from_zero(self, gm, raw):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"mpg": [1.0, 2.0], "weight": [3.0, 4.0]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            seg, _dot = gm.map_dropline(figure(), src, "mpg", "weight",
                                        {"base": raw})
        assert list(seg.data_source.data["y0"]) == [0.0, 0.0]


# ===========================================================================
# 4. fpfitci takes stdp: the stdp band, no note
# ===========================================================================

class TestFpfitciStdp:
    """twoway fpfitci accepts stdp (rc 0) and draws its only band; dash.ado
    refused it (r(198) "option stdp not allowed") -- the Stata side is
    test_help_claims_6.cscript HC6-26.  The renderer draws the same band
    with the flag as without it and says nothing."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_band_is_the_default_band(self, tmp_path, mode):
        a = _both(tmp_path, [{"type": "fpfitci", "yvar": "mpg",
                              "xvar": "weight",
                              "options": {"stdp": "stdp"}}], "fpci1")[mode]
        b = _both(tmp_path, [{"type": "fpfitci", "yvar": "mpg",
                              "xvar": "weight", "options": {}}],
                  "fpci0")[mode]
        keys = ("x_fp", "y_fp", "y_lower", "y_upper")
        da, db = _one(a[0], *keys), _one(b[0], *keys)
        for k in keys:
            np.testing.assert_array_equal(da[k], db[k])
        assert not [m for m in a[1] if "stdp" in m], a[1]


class TestFpfitReportsTheSmoothingOptions:
    """twoway fpfit and fpfitci refuse bwidth(), degree() and kernel(),
    r(198) (HC6-30).  dash accepts them so a pasted command still runs and
    says they were ignored -- bwidth() and degree() always did; kernel()
    was accepted and dropped in silence."""

    @pytest.mark.parametrize("layer", ["fpfit", "fpfitci"])
    @pytest.mark.parametrize("opt,val", [("bwidth", "1"), ("degree", "2"),
                                         ("kernel", "gaussian")])
    @pytest.mark.parametrize("mode", _MODES)
    def test_each_is_named_as_ignored(self, tmp_path, mode, layer, opt, val):
        _r, w = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                  "xvar": "weight", "options": {opt: val}}],
                      f"fp{layer}{opt}")[mode]
        assert any(f"does not accept {opt}()" in m and "ignored" in m
                   for m in w), w

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_curve_is_the_plain_curve(self, tmp_path, mode):
        a = _one(_both(tmp_path, [{"type": "fpfit", "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": {"kernel": "gaussian"}}],
                       "fpk")[mode][0], "x_fp", "y_fp")
        b = _one(_both(tmp_path, [{"type": "fpfit", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}],
                       "fp0")[mode][0], "x_fp", "y_fp")
        np.testing.assert_array_equal(a["y_fp"], b["y_fp"])


class TestOptionsTwowayIgnoresAreIgnored:
    """twoway fpfitci and mband accept n() and draw the same points without
    it (HC6-17); so does dash, in both modes."""

    @pytest.mark.parametrize("layer,keys", [
        ("fpfitci", ("x_fp", "y_fp", "y_lower", "y_upper")),
        ("mband", ("x_mb", "y_mb"))])
    @pytest.mark.parametrize("mode", _MODES)
    def test_n_changes_nothing(self, tmp_path, mode, layer, keys):
        a = _one(_both(tmp_path, [{"type": layer, "yvar": "mpg",
                                   "xvar": "weight", "options": {"n": "5"}}],
                       layer + "n5")[mode][0], *keys)
        b = _one(_both(tmp_path, [{"type": layer, "yvar": "mpg",
                                   "xvar": "weight", "options": {}}],
                       layer + "n0")[mode][0], *keys)
        for k in keys:
            np.testing.assert_array_equal(a[k], b[k])


# ===========================================================================
# 5. lpoly and lpolyci: the grid, and the curve at every degree
# ===========================================================================


def _twoway_lpoly_by_panels():
    """twoway lpoly mpg weight, bwidth(400) by(foreign): serset 0 is the
    domestic panel, serset 1 the foreign one; 50 non-missing points each
    (the dataset has 74 rows, so 50 is not capped), spanning each panel's
    own range of weight."""
    return {0: (50, 1800.0, 4840.0), 1: (50, 1760.0, 3420.0)}


class TestLpolyGrid:
    """n() for lpoly and lpolyci, sized as twoway sizes it, in both modes."""

    @pytest.mark.parametrize("layer", ["lpoly", "lpolyci"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_by_panel_keeps_the_fifty_point_grid(self, tmp_path, mode,
                                                   layer):
        got = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"bwidth": "400"}}],
                    layer + "by", graph_options={"by": "foreign"})[mode][0]
        # WP-29 P0.9: lpolyci's band has a source of its own beside the
        # line's (it is drawn only where the standard error is defined), so
        # the curve is the source without y_lower.
        lines = [r for r in got if "y_lower" not in r.data_source.data]
        xs = [d["x_lp"] for d in _data_with(lines, "x_lp", "y_lp")
              if len(d["x_lp"])]
        assert len(xs) == 2, f"{len(xs)} panels drew a curve"
        spans = sorted((len(x), float(x[0]), float(x[-1])) for x in xs)
        want = sorted(_twoway_lpoly_by_panels().values())
        assert spans == [(n, lo, hi) for n, lo, hi in want]

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_if_keeps_the_fifty_point_grid(self, tmp_path, mode):
        # twoway lpoly mpg weight if foreign, bwidth(400): 50 points over
        # the foreign cars' 1760 to 3420 (HC6-16).
        got = _both(tmp_path, [{"type": "lpoly", "yvar": "mpg",
                                "xvar": "weight", "if_expr": "foreign==1",
                                "options": {"bwidth": "400"}}],
                    "lpif")[mode][0]
        x = _one(got, "x_lp", "y_lp")["x_lp"]
        assert (len(x), x[0], x[-1]) == (50, 1760.0, 3420.0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_missing_grid_point_is_skipped_and_the_line_joins(
            self, tmp_path, mode):
        """lpoly mpg weight, bwidth(5) on auto: Stata's grid has 4
        non-missing points of 50 (fixture lpoly auto:bwidth5, ngrid 4), and
        twoway's plotted serset holds only the non-missing points, which
        its line joins (lpoly_twoway: census's serset is its 7 of 50).
        dash draws the same four, and no missing value between them."""
        got = _both(tmp_path, [{"type": "lpoly", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"bwidth": "5"}}],
                    "lpnull")[mode][0]
        d = _one(got, "x_lp", "y_lp")
        want = _fixture()["lpoly"]["auto:bwidth5"]["ngrid"]
        assert want == 4
        assert len(d["y_lp"]) == want and np.all(np.isfinite(d["y_lp"]))

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_bandwidth_too_narrow_for_any_window_draws_nothing(
            self, tmp_path, mode):
        """lpoly death pop, bwidth(5) on census: ngrid 0 in Stata."""
        df = pd.read_csv(os.path.join(_DATA, "census.csv")).dropna()
        df = df.astype(float)
        assert _fixture()["lpoly"]["census:bwidth5"]["ngrid"] == 0
        got = _both(tmp_path, [{"type": "lpoly", "yvar": "death",
                                "xvar": "pop", "options": {"bwidth": "5"}}],
                    "lpnone", df=df)[mode][0]
        drawn = [d for d in _data_with(got, "x_lp", "y_lp")]
        assert drawn and all(len(d["x_lp"]) == 0 for d in drawn)

    @pytest.mark.parametrize("mode", _MODES)
    def test_n_above_the_rows_is_capped_at_them(self, tmp_path, mode):
        # twoway lpoly mpg weight, bwidth(400) n(100): "(n() set to 74)",
        # 74 plotted points.
        got = _both(tmp_path, [{"type": "lpoly", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"bwidth": "400", "n": "100"}}],
                    "lpn100")[mode][0]
        assert len(_one(got, "x_lp", "y_lp")["x_lp"]) == 74


# twoway lpoly mpg weight, bwidth(400) degree(2) / degree(3), serset 0 of
# the saved .gph: fifty points on the grid 1760 + (i - 1) 3080 / 49.  The
# serset holds doubles; the values were exported with %21.15g.
_LPOLY_TRUTH = {
    2: [29.3144860317683, 29.6535913500323, 29.4241857085012,
        28.9738368536758, 28.4456690993328, 27.8512725009375,
        27.2125769991163, 26.5541964573589, 25.8837894313866,
        25.1475571876895, 24.3548092131013, 23.6751694139377,
        23.1213973310415, 22.6238244699796, 22.1222906008788,
        21.6447875490241, 21.3062016833744, 21.0612056799881,
        20.9550830681596, 20.869216894163, 20.6778623876945,
        20.4834311971721, 20.2435437719491, 19.8143011145811,
        19.3900343850962, 19.0089605032029, 18.6637785520818,
        18.2663595149625, 17.8813692931247, 17.4772987963945,
        17.037556031312, 16.5353045264374, 16.1842188143681,
        16.0048143721875, 15.9814332727363, 15.8980000573405,
        15.7864860845329, 15.6907872921102, 15.672495621573,
        15.5807955252878, 15.4935019869788, 15.3936919080531,
        15.182952139457, 14.9391345823269, 14.7054075823399,
        14.5711550247785, 14.0366846671952, 13.1986961570408,
        12.2718902429882, 11.2893483372192],
    3: [27.699593869536, 29.5220434786609, 30.2420531308386,
        30.1246309392054, 29.4154735371166, 28.5686958996809,
        27.6913902005654, 26.7853287099551, 25.8675004585598,
        25.2491231617836, 24.5316401856013, 23.8149283895275,
        23.1766269108779, 22.6260211946934, 22.1263084066463,
        21.7254956421412, 21.4933110780786, 21.1844893591357,
        20.9677133128367, 20.8547794491682, 20.6356356281523,
        20.4413262668103, 20.2528267005728, 19.8924116780585,
        19.4810725214763, 19.052808918882, 18.6280229820738,
        18.1318830392488, 17.6742710490796, 17.2370913332466,
        16.8245618828683, 16.4100017638071, 16.1120922912574,
        16.0356309370851, 16.1369431633345, 16.1611972920339,
        16.1864584727963, 16.2392439329423, 16.2560480739132,
        16.2802956610561, 16.3570626808199, 16.564572973279,
        16.5351946500724, 16.2911695536858, 15.7792654306349,
        14.6725875835786, 13.4524986569564, 12.6608352304008,
        11.9146251987368, 11.9757212483595],
}


class TestLpolyAtEveryDegree:
    """At a given bwidth() the curve is Stata's at every degree dash takes
    -- degree(0) and degree(1) are pinned by test_statistical_truth.py
    against the fixture; these are degree(2) and degree(3)."""

    @pytest.mark.parametrize("degree", [2, 3])
    def test_the_estimator(self, degree):
        x = np.asarray(_AUTO_WEIGHT, float)
        y = np.asarray(_AUTO_MPG, float)
        gx, gy = dr.GlyphMapper._compute_lpoly_fit(
            x, y, bwidth=400.0, degree=degree, n_grid=50)
        np.testing.assert_allclose(gx, np.linspace(1760, 4840, 50))
        np.testing.assert_allclose(gy, _LPOLY_TRUTH[degree], rtol=1e-11)

    @pytest.mark.parametrize("mode", _MODES)
    def test_degree_three_as_drawn(self, tmp_path, mode):
        got = _both(tmp_path, [{"type": "lpoly", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"bwidth": "400",
                                            "degree": "3"}}],
                    "lpd3")[mode][0]
        d = _one(got, "x_lp", "y_lp")
        np.testing.assert_allclose(d["y_lp"], _LPOLY_TRUTH[3], rtol=1e-11)


class TestLpolyciBand:
    """lpolyci's band is Stata's analytic band (WP-29 P0.9, section 11):
    smooth +/- invnormal x the sandwich standard error with a degree p+2
    pilot ([R] lpoly eq. 4; lpoly.ado:319-324), computed once by
    _lpoly_se.  These tests pinned a 200-resample bootstrap percentile band
    (GlyphMapper._bootstrap_ci) and its distance from Stata's; they now
    pin that no resample is drawn and that the band is Stata's."""

    # twoway lpolyci mpg weight, bwidth(400), serset 0, first row:
    # x 1760, smooth 27.8661240248368, band 26.2413063049316 to
    # 29.4909420013428 (23sep2026; twoway's serset holds floats).
    _TW_FIRST = (1760.0, 27.8661240248368, 26.2413063049316,
                 29.4909420013428)

    def test_no_resample_is_drawn(self, monkeypatch):
        """Flipped (P0.9): the spy saw 201 fits, the point estimate and
        200 resamples; now one fit, and _bootstrap_ci is never called."""
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        grids = []
        boots = []
        real = dr.GlyphMapper._compute_lpoly_fit

        def spy(*a, **k):
            grids.append(k.get("x_grid"))
            return real(*a, **k)

        def boot(*a, **k):
            boots.append(1)
            raise AssertionError("lpolyci ran a bootstrap")
        monkeypatch.setattr(dr.GlyphMapper, "_compute_lpoly_fit",
                            staticmethod(spy))
        monkeypatch.setattr(dr.GlyphMapper, "_bootstrap_ci",
                            staticmethod(boot))
        src = ColumnDataSource({"mpg": list(_AUTO.mpg),
                                "weight": list(_AUTO.weight)})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.GlyphMapper().map_lpolyci(
                figure(), src, "mpg", "weight", {"bwidth": "400"})
        assert len(grids) == 1 and grids[0] is None, grids
        assert boots == []

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_line_and_band_are_statas(self, tmp_path, mode):
        """Flipped (P0.9): asserted the lower edge more than 0.1 off
        Stata's (dash's bootstrap gave 25.70 where Stata's is 26.24)."""
        got = _both(tmp_path, [{"type": "lpolyci", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"bwidth": "400"}}],
                    "lpcib")[mode][0]
        d = _one(got, "x_lp", "y_lp", "y_lower", "y_upper")
        x0, fit, lo, hi = self._TW_FIRST
        assert d["x_lp"][0] == x0
        assert d["y_lp"][0] == pytest.approx(fit, rel=1e-12)
        assert d["y_lower"][0] == pytest.approx(lo, rel=1e-6)
        assert d["y_upper"][0] == pytest.approx(hi, rel=1e-6)


# ===========================================================================
# 6. lowess: bwidth(1) is Stata's 0.8, and logit's clamp is Stata's
# ===========================================================================

def _fixture():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


class TestLowessEdges:

    @pytest.mark.parametrize("mode", _MODES)
    def test_bwidth_one_is_drawn_as_point_eight(self, tmp_path, mode):
        """lowess.ado:75-78 resets a bandwidth outside (0, 1) to .8:
        ``twoway lowess mpg weight, bwidth(1)`` and ``bwidth(1.5)`` plot the
        default's serset (measured).  dash draws the default for both, in
        silence, as twoway does (WP-31 C10a; Flipped: it noted bwidth(1) and
        dash.ado refused 1.5)."""
        one, w = _both(tmp_path, [{"type": "lowess", "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": {"bwidth": "1"}}],
                       "lw1")[mode]
        dflt, _ = _both(tmp_path, [{"type": "lowess", "yvar": "mpg",
                                    "xvar": "weight", "options": {}}],
                        "lw8")[mode]
        a, b = _one(one, "x_lw", "y_lw"), _one(dflt, "x_lw", "y_lw")
        np.testing.assert_array_equal(a["y_lw"], b["y_lw"])
        assert not any("bwidth" in m for m in w), w
        big, w = _both(tmp_path, [{"type": "lowess", "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": {"bwidth": "1.5"}}],
                       "lw15")[mode]
        np.testing.assert_array_equal(_one(big, "x_lw", "y_lw")["y_lw"],
                                      b["y_lw"])
        assert not any("bwidth" in m for m in w), w

    @pytest.mark.parametrize("mode", _MODES)
    def test_logit_clamps_only_past_one_in_ten_thousand(self, tmp_path,
                                                        mode):
        """lowess.ado ADJ_LOGIT: a smooth below .0001 becomes 1/N, one above
        1 - .0001 becomes 1 - 1/N; anything between is kept.  Measured:
        ``twoway lowess y x, mean noweight bwidth(.05) logit`` on twenty
        rows (a one-point window, so the smooth is y) plots
        ln(.005/.995) = -5.29330482472449 for y = .005, although .005 is
        below 1/N = .05, and ln(.05/.95) only for y = .00005."""
        y = np.full(20, 0.3)
        y[2], y[6], y[10], y[14] = 0.005, 0.00005, 0.99995, 0.995
        df = pd.DataFrame({"x": np.arange(1.0, 21.0), "y": y})
        got = _both(tmp_path, [{"type": "lowess", "yvar": "y", "xvar": "x",
                                "options": {"mean": "mean",
                                            "noweight": "noweight",
                                            "bwidth": ".05",
                                            "logit": "logit"}}],
                    "lwlogit", df=df)[mode][0]
        d = _one(got, "x_lw", "y_lw")
        want = np.full(20, -0.847297860387204)
        want[2], want[6] = -5.29330482472449, -2.94443897916644
        want[10], want[14] = 2.94443897916644, 5.29330482472449
        np.testing.assert_allclose(d["y_lw"], want, rtol=1e-12)


# ===========================================================================
# 7. mspline and mband: a weight changes nothing, not even a zero or missing
# ===========================================================================

class TestInertWeights:
    """twoway mband mpg weight [aw=w], w zero on the lightest and the
    heaviest car: the serset equals the unweighted one (measured) -- a zero
    weight does not drop its observation there, although it does on every
    other weighted layer (twoway lfit mpg weight [aw=w] runs 1800 to 4720,
    as ``if w > 0`` does)."""

    @staticmethod
    def _df():
        df = _AUTO.copy()
        z = np.ones(len(df))
        z[(df.weight == 4840) | (df.weight == 1760)] = 0.0
        m = np.ones(len(df))
        m[(df.weight == 4840) | (df.weight == 1760)] = np.nan
        df["zw"] = z
        df["mw"] = m
        return df

    @pytest.mark.parametrize("layer,keys", [
        ("mband", ("x_mb", "y_mb")), ("mspline", ("x_sp", "y_sp"))])
    @pytest.mark.parametrize("wvar", ["zw", "mw"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_curve_is_the_unweighted_curve(self, tmp_path, mode, layer,
                                               keys, wvar):
        df = self._df()

        def curve(opts, tag):
            rs = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                   "xvar": "weight", "options": opts}],
                       tag, df=df)[mode][0]
            return _one(rs, *keys)
        weighted = curve({"weight": "aweight", "wexp": wvar},
                         f"{layer}{wvar}")
        plain = curve({}, f"{layer}plain")
        for k in keys:
            np.testing.assert_array_equal(weighted[k], plain[k])
        # The band edges run 1760 to 4840 only if the two zero- or
        # missing-weight cars are still in: with them out, 1800 to 4720.
        assert len(plain[keys[0]]) > 2

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_zero_weight_drops_its_row_on_lfit(self, tmp_path, mode):
        df = self._df()
        got = _both(tmp_path, [{"type": "lfit", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"weight": "aweight",
                                            "wexp": "zw"}}],
                    "lfitzw", df=df)[mode][0]
        d = _one(got, "x", "y")
        assert (d["x"][0], d["x"][-1]) == (1800.0, 4720.0)


class TestTheSessionLevel:
    """"defaulting to the session's c(level) -- so set level 90 is
    honoured, as twoway honours it" (twoway: HC6-25).  dash.ado writes
    c(level) into the spec's build options; with no level() on the layer
    the band is drawn at it, in both modes, on every band layer."""

    @pytest.mark.parametrize("layer,keys", [
        ("lfitci", ("x_fit", "y_lower", "y_upper")),
        ("qfitci", ("x_fit", "y_lower", "y_upper")),
        ("fpfitci", ("x_fp", "y_lower", "y_upper")),
        ("lpolyci", ("x_lp", "y_lower", "y_upper"))])
    @pytest.mark.parametrize("mode", _MODES)
    def test_c_level_is_the_default_level(self, tmp_path, mode, layer,
                                          keys):
        opts = {"bwidth": "400"} if layer == "lpolyci" else {}

        def band(plot_opts, session, tag):
            spec = make_spec([{"type": layer, "yvar": "mpg",
                               "xvar": "weight", "options": plot_opts}])
            if session:
                spec["build_options"]["level"] = session
            sp, dp = _write_inputs(tmp_path, spec, _AUTO)
            if mode == "saved":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = dr.DashRenderer(sp, dp)
                    render_models(r)
                return _one(_renderers(r._last_layout_root), *keys)
            ns = _load_app(_app_source(tmp_path, spec, _AUTO), tag)
            doc = Document()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ns["make_document"](doc)
            return _one(_renderers(doc), *keys)
        at90 = band(dict(opts), "90", layer + "s90")
        own90 = band(dict(opts, level="90"), "", layer + "o90")
        at95 = band(dict(opts), "95", layer + "s95")
        np.testing.assert_allclose(at90["y_lower"], own90["y_lower"])
        np.testing.assert_allclose(at90["y_upper"], own90["y_upper"])
        assert not np.allclose(at90["y_lower"], at95["y_lower"])


class TestBaseOnTheBarPlots:
    """base() on bar, spike and area, in both modes (dropline is
    TestDroplineBase)."""

    @staticmethod
    def _bases(renderers, layer, key):
        vals = []
        for r in renderers:
            g = r.glyph
            if layer == "bar" and hasattr(g, "bottom"):
                b = g.bottom
                fld = b if isinstance(b, str) else getattr(b, "field", None)
                if fld:
                    vals += [float(v) for v in r.data_source.data[fld]]
                    continue
                vals.append(float(b) if isinstance(b, (int, float))
                            else float(getattr(b, "value", np.nan)))
            elif key in r.data_source.data:
                vals += [float(v) for v in r.data_source.data[key]]
        return vals

    @pytest.mark.parametrize("base", ["10", ""])
    @pytest.mark.parametrize("layer,key", [("bar", "bottom"),
                                           ("spike", "y0"),
                                           ("area", "mpg_base")])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_base_is_drawn_and_defaults_to_zero(self, tmp_path, mode,
                                                    layer, key, base):
        opts = {"base": base} if base else {}
        got = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                "xvar": "weight", "options": opts}],
                    layer + "base" + base)[mode][0]
        vals = self._bases(got, layer, key)
        # Flipped: the default was 0.0 -- twoway draws a default base as 0
        # clamped into the axis's scale (P1.17b): 10 on `<layer> mpg
        # weight' (fixture default_base_truth.json auto.<layer>).
        want = float(base) if base else _DEFAULT_BASE[layer]["drawn_base"]
        assert vals and all(v == want for v in vals), (layer, vals)


class TestAPweightIsTheAweightFitWithARobustBand:
    """"A pweight gives the aweight estimates with a robust standard error
    for the band."  twoway lfitci / qfitci / fpfitci mpg weight [pw=price]
    on auto, serset 0 (floats), first and last rows (x, fit, lower, upper);
    the pweight fit equals the aweight fit and the band does not
    (test_help_claims_6.cscript HC6-54)."""

    _TRUTH = {
        "lfitci": ((1760.0, 28.0256633758545, 26.0050773620605,
                    30.0462493896484),
                   (4840.0, 11.0978412628174, 8.87361907958984,
                    13.3220634460449)),
        "qfitci": ((1760.0, 30.0984745025635, 27.2664222717285,
                    32.9305267333984),
                   (4840.0, 13.991870880127, 10.565016746521,
                    17.4187259674072)),
        "fpfitci": ((1760.0, 30.6971530914307, 26.88010597229,
                     34.5141983032227),
                    (4840.0, 13.6615676879883, 11.4321060180664,
                     15.8910293579102)),
    }

    @pytest.mark.parametrize("layer", ["lfitci", "qfitci", "fpfitci"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_band_is_twoways(self, tmp_path, mode, layer):
        xk, yk = ("x_fp", "y_fp") if layer == "fpfitci" else ("x_fit",
                                                               "y_fit")
        got = _both(tmp_path, [{"type": layer, "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"weight": "pweight",
                                            "wexp": "price"}}],
                    layer + "pw")[mode][0]
        d = _one(got, xk, yk, "y_lower", "y_upper")
        for (x0, fit, lo, hi), i in zip(self._TRUTH[layer], (0, -1)):
            assert d[xk][i] == pytest.approx(x0)
            assert d[yk][i] == pytest.approx(fit, rel=1e-6)
            assert d["y_lower"][i] == pytest.approx(lo, rel=1e-6)
            assert d["y_upper"][i] == pytest.approx(hi, rel=1e-6)


# ===========================================================================
# 8. histogram: one value, and discrete's start()
# ===========================================================================

class TestHistogramEdges:

    @pytest.mark.parametrize("opts,edges", [
        # twoway histogram weight if weight == 3200: one bar, 3200 to 3201
        # (serset: centre 3200.5, density 1).
        ({}, (3200.0, 3201.0)),
        # twoway histogram cst, width(3) on a constant 5: 5 to 8, height
        # 1/3; discrete: 4.5 to 5.5.
        ({"width": "3"}, (3200.0, 3203.0)),
        ({"discrete": "discrete"}, (3199.5, 3200.5)),
    ])
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_constant_variable_is_one_bar(self, tmp_path, mode, opts,
                                            edges):
        df = pd.DataFrame({"v": np.full(10, 3200.0)})
        got = _both(tmp_path, [{"type": "histogram", "var": "v",
                                "options": opts}],
                    "hcst" + "".join(opts), df=df)[mode][0]
        d = _one(got, "left", "right", "top")
        assert len(d["left"]) == 1
        assert (d["left"][0], d["right"][0]) == edges
        assert d["top"][0] * (edges[1] - edges[0]) == pytest.approx(1.0)

    @pytest.mark.parametrize("start", ["0", "-3.3"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_start_does_not_move_discrete_bars(self, tmp_path, mode, start):
        # twoway histogram rep78, discrete [start(0) | start(-3.3)]: the
        # same five bars centred on 1..5, densities .0290 .1159 .4348
        # .2609 .1594.
        got = _both(tmp_path, [{"type": "histogram", "var": "rep78",
                                "options": {"discrete": "discrete",
                                            "start": start}}],
                    "hdst" + start.replace(".", "p").replace("-", "m"))
        d = _one(got[mode][0], "left", "right", "top")
        np.testing.assert_allclose((d["left"] + d["right"]) / 2,
                                   [1, 2, 3, 4, 5])
        np.testing.assert_allclose(
            d["top"], [.028985507786274, .115942031145096, .434782594442368,
                       .260869562625885, .159420296549797], rtol=1e-6)


# ===========================================================================
# 9. The default lpoly bandwidth: the numbers the help gives
# ===========================================================================
# r(bwidth) from Stata's `lpoly <y> <x> [weight], nograph' (23sep2026).
_STATA_ROT = {
    "auto mpg on weight": 70.64292135539181,
    "auto price on mpg": .9625182380589853,
    "auto price on rep78": .5386993657559485,
    "auto mpg on weight [aw=price]": 57.6601811789739,
    "census death on pop": 51693.54900092584,
    "sp500 close on volume": 176.1805503850957,
    "nlsw88 wage on ttl_exp": .7440135932182029,
    "auto mpg on weight in 1/7": 77.35273499984294,
}
def _csv(name, y, x):
    df = pd.read_csv(os.path.join(_DATA, name + ".csv")).dropna()
    return df[x].to_numpy(float), df[y].to_numpy(float)


def _dash_rot():
    x, y = np.asarray(_AUTO_WEIGHT, float), np.asarray(_AUTO_MPG, float)
    p, r = np.asarray(_AUTO_PRICE, float), np.asarray(_AUTO_REP78, float)
    ok = np.isfinite(r)
    rot = dr.GlyphMapper._default_lpoly_bwidth
    return {
        "auto mpg on weight": rot(x, y),
        "auto price on mpg": rot(y, p),
        "auto price on rep78": rot(r[ok], p[ok]),
        "auto mpg on weight [aw=price]":
            rot(x, y, dr._dash_lpoly_weights(p, "aw")),
        "census death on pop": rot(*_csv("census", "death", "pop")),
        "sp500 close on volume": rot(*_csv("sp500", "close", "volume")),
        "nlsw88 wage on ttl_exp": rot(*_csv("nlsw88", "wage", "ttl_exp")),
        "auto mpg on weight in 1/7": rot(x[:7], y[:7]),
    }


class TestDefaultBandwidth:

    # WP-29 P0.7 (section 11): these four tests pinned dash's own 0.65
    # (s^2/S)^(1/5) quartic rule, its gaps to Stata (-9.7% ... +14.2%) and
    # its range/10 below eight observations.  The default is now Stata's
    # rule of thumb, so they pin Stata's r(bwidth) instead.

    def test_the_rule_is_the_one_the_help_writes_down(self):
        """The rule is Stata's: r(bwidth) on the eight cases at 1e-8 (the
        first seven cars, a degree-0 rule on 7 points, at 5e-5)."""
        got = _dash_rot()
        for case, want in _STATA_ROT.items():
            tol = 5e-5 if case.endswith("in 1/7") else 1e-8
            assert abs(got[case] / want - 1) <= tol, (case, got[case], want)
        assert not hasattr(dr, "_LPOLY_ROT_C")

    @pytest.mark.parametrize("case", sorted(_STATA_ROT))
    def test_the_gap_to_statas_rule_is_the_one_the_help_gives(self, case):
        """No gap: each case is Stata's r(bwidth)."""
        rel = _dash_rot()[case] / _STATA_ROT[case] - 1.0
        tol = 5e-5 if case.endswith("in 1/7") else 1e-8
        assert abs(rel) <= tol, (case, rel)

    def test_below_eight_observations_it_is_a_tenth_of_the_range(self):
        """Below eight observations the rule is still Stata's: on the first
        seven cars h = 77.35273499984294 (r(ngrid) 10 of 50 points), and on
        the first two to five cars twoway draws nothing."""
        x, y = np.asarray(_AUTO_WEIGHT, float), np.asarray(_AUTO_MPG, float)
        h7 = _dash_rot()["auto mpg on weight in 1/7"]
        assert abs(h7 / 77.35273499984294 - 1) <= 5e-5
        _, yf = dr.GlyphMapper._compute_lpoly_fit(x[:7], y[:7], bwidth=h7,
                                                  n_grid=50)
        assert int(np.isfinite(yf).sum()) == 10
        for k in range(2, 6):
            h = dr.GlyphMapper._default_lpoly_bwidth(x[:k], y[:k])
            _, yf = dr.GlyphMapper._compute_lpoly_fit(x[:k], y[:k],
                                                      bwidth=h, n_grid=50)
            assert not np.isfinite(yf).any(), k

    def test_the_help_gives_those_numbers(self):
        sec = _section("smoother_options", "weights")
        flat = " ".join(sec.split())
        for s in ("use {cmd:lpoly}'s rule of thumb as Stata computes it",
                  "a global polynomial of degree p+3 in powers of x",
                  "an even degree uses the next odd one",
                  "integrated over the central 90% of the range of x",
                  "each {cmd:by()} panel and each {cmd:if} or {cmd:in} gets "
                  "its own",
                  "recomputes it from the rows kept after every filter move",
                  "a constant x, gives a line at 0",
                  "y exactly linear in x at {cmd:degree(0)}"):
            assert s in flat, s
        for gone in ("9.7% below", "185 against Stata's 77.4", "0.65"):
            assert gone not in flat, gone


# ===========================================================================
# 10. What the help says -- the sections themselves
# ===========================================================================

def _help():
    with open(_HELP, encoding="utf-8") as fh:
        return fh.read()


def _section(start, end):
    h = _help()
    i = h.index("{marker %s}" % start)
    j = h.index("{marker %s}" % end, i)
    return h[i:j]


def _entries():
    """``{option: entry text}`` for the synopt table of the section."""
    sec = _section("smoother_options", "weights")
    table = sec[sec.index("{synoptset"):sec.index("{synoptline}")]
    out = {}
    for chunk in re.split(r"\n(?=\{synopt:)", table):
        m = re.match(r"\{synopt:\{opt ([a-z]+)", chunk)
        if m:
            out[m.group(1)] = " ".join(chunk.split())
    return out


# The plot types that take each option, measured with twoway (rc 0 against
# r(198) "option X() not allowed", one probe per type, 23sep2026) and, for
# dash, where the renderer reads it.  The entry must name every one.
_TAKES = {
    "bwidth": ("lpoly", "lpolyci", "kdensity", "lowess"),
    "degree": ("lpoly", "lpolyci"),
    "kernel": ("lpoly", "lpolyci", "kdensity"),
    "n": ("lpoly", "lpolyci", "kdensity", "lfit", "qfit", "lfitci",
          "qfitci", "function", "mspline"),
    "bands": ("mspline", "mband"),
    "range": ("lfit", "qfit", "lfitci", "qfitci", "kdensity", "function"),
    "base": ("bar", "spike", "dropline", "area"),
    "discrete": ("histogram",),
    "stdp": ("lfitci", "qfitci", "fpfitci"),
    "stdf": ("lfitci", "qfitci"),
    "stdr": ("lfitci", "qfitci"),
    "mean": ("lowess",), "noweight": ("lowess",), "adjust": ("lowess",),
    "logit": ("lowess",),
}


class TestTheEntriesSayWhatTakesThem:

    def test_every_option_has_an_entry(self):
        missing = sorted(set(_TAKES) - set(_entries()))
        assert not missing, missing

    @pytest.mark.parametrize("opt", sorted(_TAKES))
    def test_the_entry_names_its_plot_types(self, opt):
        text = _entries()[opt]
        absent = [t for t in _TAKES[opt] if "{cmd:%s}" % t not in text]
        assert not absent, f"{opt}(): the entry does not name {absent}"

    @pytest.mark.parametrize("opt,default", [
        ("bwidth", "0.8"), ("degree", "the default"),
        ("kernel", "{cmd:epanechnikov} (the default)"),
        ("n", "50 by default"), ("n", "300 by default"),
        ("n", "100 by default"), ("n", "default 10"),
        ("bands", "round(min(10 log10"), ("range", "{cmd:range(0 1)}"),
        # Flipped: was "default 0" -- twoway draws a default base as 0
        # clamped into the axis's scale (P1.17b), and the entry says so.
        pytest.param("base", "they are drawn from 0 when the y",
                     id="base-default 0"),
        ("stdp", "(the default)")])
    def test_the_entry_gives_the_default(self, opt, default):
        assert default in _entries()[opt]

    @pytest.mark.parametrize("opt,bound", [
        ("degree", "any whole number from 0 up"),
        ("degree", "refuses more than 3"),
        # Flipped (WP-31 C10a): n(1) and lowess's every bwidth() are
        # twoway's.
        ("n", "1 to 10000"), ("n", "any whole number from 1 up"),
        ("n", "1 to 300"), ("bands", "1 to 200"),
        ("bwidth", "{cmd:lowess} any number"),
        ("range", "Two numbers, in either order"),
        ("base", "any number")])
    def test_the_entry_gives_the_bounds(self, opt, bound):
        assert bound in _entries()[opt]

    def test_the_synonyms_are_named_beside_their_options(self):
        e = _entries()
        # twoway takes bw() as bwidth()'s abbreviation on the bandwidth
        # types and refuses it on the bar family, where dash reads it as
        # barwidth(): a synonym dash alone has.
        assert "{cmd:bw()}" in e["bwidth"]
        assert "a synonym of its own" in e["bwidth"]
        assert "{opt width(#)} is a synonym" in e["bwidth"]
        # twoway histogram's own name is bins(); bin() is its abbreviation
        # (twoway_histogram_parse.class: BINs(numlist ...)), and dash
        # takes both.
        sec = " ".join(_section("smoother_options", "weights").split())
        assert "{cmd:bins()}" in sec and "{cmd:bin()}" in sec


class TestTheCorrectedClaims:
    """Each sentence that was false at 4ede074 is gone, and what replaced it
    is what was measured."""

    def _flat(self, start="smoother_options", end="region_options"):
        return " ".join(_section(start, end).split())

    def test_a_zero_weight_is_not_said_to_leave_everywhere(self):
        flat = self._flat()
        assert "A zero weight leaves its observation out everywhere" \
            not in flat
        assert "except on {cmd:mspline} and {cmd:mband}" in flat

    def test_logits_clamp_is_statas(self):
        flat = self._flat()
        assert "clamping {it:s} to [1/{it:N}" not in flat
        assert "below .0001" in flat and "above 1 - .0001" in flat

    def test_fpfitci_takes_stdp(self):
        flat = self._flat()
        assert "It takes {cmd:stdp} only" not in flat

    def test_the_history_sentence_is_gone(self):
        assert "Earlier versions of this help" not in self._flat()

    def test_estopts_is_said_to_be_ignored(self):
        flat = self._flat()
        assert "{cmd:estopts()}" in flat
        assert re.search(r"estopts\(\)\}[^.]*named in the note", flat) or \
            "named in the note as ignored" in flat

    def test_the_weight_is_exported_only_where_it_is_used(self):
        flat = self._flat("weights", "region_options")
        assert "the weight variable is not exported" in flat

    def test_iweight_on_the_immediate_types_is_twoways_words(self):
        """At 4ede074 every weight on function, scatteri, pci and pcarrowi
        was r(101) "weights not allowed"; twoway's codes and words are
        measured by HC6-48, which dash.ado now reproduces."""
        flat = self._flat("weights", "region_options")
        assert ("{cmd:[iweight=]} on any plot type "
                "({cmd:iweights not allowed})") in flat
        assert ("any weight on {cmd:scatteri}, {cmd:pci} or {cmd:pcarrowi}, "
                "r(198) ({cmd:weights not allowed})") in flat
        assert ("On {cmd:scatter} and the other glyph layers, and on "
                "{cmd:function}, a weight is accepted") in flat

    def test_no_optional_library_is_credited(self):
        """WP-18 moved every statistical layer to numpy: the section credits
        neither scipy nor statsmodels with any work, and the renderer
        imports neither (an AST scan: no import statement, no
        _optional_import of either)."""
        flat = self._flat()
        assert "scipy" not in flat
        assert "no longer needs statsmodels" in flat
        tree = ast.parse(open(_RENDER, encoding="utf-8").read())
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                bad += [a.name for a in node.names
                        if a.name.split(".")[0] in ("scipy", "statsmodels")]
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] in ("scipy",
                                                         "statsmodels"):
                    bad.append(node.module)
            elif isinstance(node, ast.Call) and getattr(
                    node.func, "id", "") == "_optional_import":
                if node.args and isinstance(node.args[0], ast.Constant) \
                        and str(node.args[0].value).split(".")[0] in (
                            "scipy", "statsmodels"):
                    bad.append(node.args[0].value)
        assert not bad, bad


class TestTheWeightTable:
    """The help's per-type table is twoway's acceptance table (the fixture's
    ``weight_acceptance_table``, measured 72 probes) and the renderer's
    ``_DASH_WEIGHT_ACCEPTS``."""

    @staticmethod
    def _table():
        """``{plot type: {weight types}}`` from the section's synopt table.

        A row is ``{synopt:<types>}<weights>{p_end}``; the types part holds
        ``{cmd:...}`` directives, so its end is found by matching braces.
        """
        sec = _section("weights", "region_options")
        # One entry per {synopt:...}{p_end}, its continuation lines joined.
        entries, cur = [], None
        for ln in sec.splitlines():
            if ln.startswith("{synopt:"):
                cur = ln
            elif cur is not None:
                cur += " " + ln.strip()
            if cur is not None and cur.rstrip().endswith("{p_end}"):
                entries.append(cur)
                cur = None
        rows = {}
        for ln in entries:
            depth, end = 0, None
            for i, ch in enumerate(ln):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            head, tail = ln[:end], ln[end + 1:]
            types = re.findall(r"\{cmd:([a-z]+)\}", head)
            kinds = set(re.findall(r"\{cmd:([a-z]weight)\}", tail))
            for t in types:
                rows[t] = kinds
        return rows

    def test_the_table_was_found(self):
        assert len(self._table()) == 13

    def test_it_is_twoways_table(self):
        """lpolyci has no row in the fixture's table; its acceptance is
        measured live, beside dash's, by test_help_claims_6.cscript
        HC6-50."""
        fx = _fixture()["weight_acceptance_table"]
        names = {"aw": "aweight", "fw": "fweight", "pw": "pweight"}
        unmeasured = []
        for t, kinds in self._table().items():
            tw = fx.get("twoway_" + t)
            if tw is None:
                unmeasured.append(t)
                continue
            want = {names[k] for k in ("aw", "fw", "pw")
                    if tw[k]["accepted"]}
            assert kinds == want, (t, kinds, want)
        assert unmeasured == ["lpolyci"], unmeasured

    def test_it_is_the_renderers_table(self):
        names = {"aw": "aweight", "fw": "fweight", "pw": "pweight"}
        for t, kinds in self._table().items():
            want = {names[k] for k in dr._DASH_WEIGHT_ACCEPTS[t]}
            assert kinds == want, (t, kinds, want)
