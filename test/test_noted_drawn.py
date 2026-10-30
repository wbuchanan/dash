"""test_noted_drawn.py -- options twoway draws that dash named (WP-32).

BUGS.md "Options twoway draws that dash still names: sort on marker types,
mstyle()/mlstyle() on arrows, baroffset() on rbar, mwidth on histogram"
and the entries split from it.  Each was measured 19oct2026 in StataNow
19.5 by graph export SVG (test/fixtures/noted_option_truth.json and the
probes the entries name); each test draws the option in both modes, the
saved page and the served app, and holds dash's geometry to twoway's.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = tsr.MODES


def _renderers(plots, mode, scheme="stcolor"):
    if isinstance(plots, dict):
        plots = [plots]
    d = tsr._draw(tp._spec(list(plots), {"scheme": scheme}, {}), mode)
    return ([r for f in d.figures for r in f.renderers
             if isinstance(r, GlyphRenderer)],
            [m for m in d.warnings if m.startswith("dash")])


def _vbar(plots, mode):
    rs, notes = _renderers(plots, mode)
    [r] = [r for r in rs if type(r.glyph).__name__ == "VBar"][:1]
    return r, notes


def _col(r, field):
    spec = getattr(r.glyph, field)
    name = spec if isinstance(spec, str) else getattr(spec, "field", spec)
    if isinstance(spec, dict):
        name = spec.get("field")
    return np.asarray(r.data_source.data[name], dtype=float)


@pytest.mark.parametrize("mode", MODES)
class TestRbarBaroffset:
    """twoway moves rbar's bars by baroffset() bar widths exactly as it
    moves bar's (measured 19oct2026: for baroffset(1), (-1), (.5) and (5)
    every rbar rect's x equals bar's, against each one's baroffset(0)),
    which map_bar draws (WP-31 C5)."""

    @pytest.mark.parametrize("off", ["1", "-1", ".5", "5"])
    def test_rbar_moves_as_bar_moves(self, mode, off):
        rb, _ = _vbar(plot_for("rbar", {"baroffset": off}), mode)
        r0, _ = _vbar(plot_for("rbar"), mode)
        xs = _col(r0, "x")
        got = _col(rb, "x")
        assert np.allclose(got, xs + float(off) * 1.0, equal_nan=True)

    def test_rbar_baroffset_is_not_named(self, mode):
        _, notes = _vbar(plot_for("rbar", {"baroffset": "1"}), mode)
        assert not [n for n in notes if "baroffset" in n]


def _width(r):
    """(value, units) of a glyph's width spec."""
    w = r.glyph.width
    v = getattr(w, "value", w)
    if isinstance(w, dict):
        v = w.get("value", w.get("field"))
    f = getattr(w, "field", None) or (v if isinstance(v, str) else None)
    if f:
        col = list(r.data_source.data[f])
        assert len(set(col)) <= 1, col
        v = col[0]
    units = getattr(w, "units", None) or getattr(r.glyph, "width_units",
                                                  None)
    if isinstance(w, dict):
        units = w.get("units", units)
    return float(v), units


@pytest.mark.parametrize("mode", MODES)
class TestHistogramMwidth:
    """twoway's histogram with mwidth draws each bar as wide as a marker
    whose size is barwidth() -- the bin width by default -- centred on the
    bin's start (measured 19oct2026: mpg's eight bins of 3.625 drawn
    117.45 of the SVG's 3240, 3.625%, the first centred at the first
    bar's left edge; barwidth(1) 32.4, 1%; msize() changes nothing)."""

    def _bars(self, mode, extra=None):
        o = {"mwidth": "mwidth"}
        o.update(extra or {})
        rs, notes = _renderers(plot_for("histogram", o), mode)
        return rs, notes

    def test_each_bar_is_a_marker_wide_at_the_bin_start(self, mode):
        rs, _ = self._bars(mode)
        q0 = [r for r in _renderers(plot_for("histogram"), mode)[0]
              if type(r.glyph).__name__ == "Quad"][0]
        [vb] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        assert not [r for r in rs if type(r.glyph).__name__ == "Quad"]
        assert np.allclose(_col(vb, "x"), _col(q0, "left"))
        assert np.allclose(_col(vb, "top"), _col(q0, "top"))
        w, units = _width(vb)
        assert units == "screen"
        assert w > 0

    def test_barwidth_is_the_marker_size(self, mode):
        rs, _ = self._bars(mode)
        [a] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        rs1, _ = self._bars(mode, {"barwidth": "1"})
        [b] = [r for r in rs1 if type(r.glyph).__name__ == "VBar"]
        bin_w = float(np.diff(_col(a, "x"))[0])
        assert _width(a)[0] == pytest.approx(bin_w * _width(b)[0], rel=1e-6)

    def test_msize_changes_nothing(self, mode):
        rs, _ = self._bars(mode)
        rs2, _ = self._bars(mode, {"msize": "vlarge"})
        [a] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        [b] = [r for r in rs2 if type(r.glyph).__name__ == "VBar"]
        assert _width(a) == _width(b)


#: The marker types twoway draws in sort order under sort (WP-32;
#: noted_option_truth.json twoway_draws "order": the same marks, SVG
#: circles in x order under sort).
_ORDER_TYPES = ("scatter", "bar", "spike", "dropline", "dot", "rbar",
                "rspike", "rcap", "rcapsym", "rscatter", "rpcap", "rpspike",
                "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter")


def _xfield(r, fields=("x", "x0", "left")):
    g = r.glyph
    for f in fields:
        spec = getattr(g, f, None)
        name = spec if isinstance(spec, str) else getattr(spec, "field", None)
        if isinstance(spec, dict):
            name = spec.get("field")
        if name and name in r.data_source.data:
            return np.asarray(r.data_source.data[name], dtype=float)
    return None


@pytest.mark.parametrize("mode", MODES)
class TestSortOrder:
    """twoway draws a marker layer's points in sort order under sort, the
    later on top (measured 19oct2026: scatter's 74 circles in x order under
    sort, in price order under sort(price))."""

    @pytest.mark.parametrize("ptype", ["scatter", "dropline", "spike",
                                       "rcap", "pcspike"])
    def test_drawn_in_x_order(self, mode, ptype):
        rs, notes = _renderers(plot_for(ptype, {"sort": "sort"}), mode)
        # A pc layer in x2's order (twoway's SVG: the segments' second
        # x ascending), the others in x's.
        f = ("x1",) if ptype.startswith("pc") else ("x", "x0", "left")
        xs = [x for x in (_xfield(r, f) for r in rs) if x is not None
              and len(x) > 3]
        assert xs, "nothing with an x drawn"
        for x in xs:
            ok = x[~np.isnan(x)]
            assert np.all(np.diff(ok) >= 0), (ptype, ok[:10])

    def test_the_data_order_without_sort(self, mode):
        rs, _ = _renderers(plot_for("scatter"), mode)
        [x] = [x for x in (_xfield(r) for r in rs) if x is not None][:1]
        ok = x[~np.isnan(x)]
        assert not np.all(np.diff(ok) >= 0)


@pytest.mark.parametrize("mode", MODES)
class TestHistogramMwidthHorizontal:
    """histogram horizontal mwidth: each bar a marker of barwidth() tall
    -- the bin width by default, 3.625% of the shorter side, barwidth(1)
    1% -- centred on the bin's start, as upright (measured 19oct2026)."""

    def test_turned_bars_are_a_marker_tall(self, mode):
        rs, notes = _renderers(plot_for("histogram", {
            "mwidth": "mwidth", "horizontal": "horizontal"}), mode)
        [hb] = [r for r in rs if type(r.glyph).__name__ == "HBar"]
        up, _ = _renderers(plot_for("histogram", {"mwidth": "mwidth"}), mode)
        [vb] = [r for r in up if type(r.glyph).__name__ == "VBar"]
        assert hb.glyph.height_units == "screen"
        h = hb.glyph.height
        f = h if isinstance(h, str) else getattr(h, "field", None)
        assert list(hb.data_source.data[f]) == list(
            vb.data_source.data[vb.glyph.width if isinstance(
                vb.glyph.width, str) else vb.glyph.width.field])
        assert not [n for n in notes if "mwidth" in n]


@pytest.mark.parametrize("mode", MODES)
class TestRbarMwidthBaroffset:
    """rbar mwidth baroffset(#): each marker-wide bar moved # bar widths
    to the LEFT in screen units -- baroffset(1) by -33.75, (-1) by +33.75,
    (5) by -168.75 of the SVG's units for a 33.75-wide bar, barwidth(2)'s
    64.8-wide bars by -64.8 (measured 19oct2026) -- whatever the x
    spacing, as the bar's own width is."""

    def _rect(self, mode, opts):
        rs, notes = _renderers(plot_for("rbar", opts), mode)
        [r] = [r for r in rs if type(r.glyph).__name__ == "Rect"]
        return r, notes

    def test_the_bars_move_by_screen_widths(self, mode):
        import json
        import shutil
        import subprocess
        r, notes = self._rect(mode, {"mwidth": "mwidth", "baroffset": "1"})
        assert not [n for n in notes if "baroffset" in n]
        f = r.glyph.x if isinstance(r.glyph.x, str) else r.glyph.x.field
        cbs = [cb for fig_r in [r] for cb in
               getattr(r, "_dash_rbo_callbacks", [])]
        assert cbs, "no screen-offset callback"
        cb = cbs[0]
        node = shutil.which("node")
        if node is None:
            pytest.skip("node not found")
        a = cb.args
        xs = list(map(float, a["src"].data[a["xcol"]][:3]))
        prog = ("const src={data:{%s:%s}, change:{emit(){}}};"
                "const rng={start:0,end:10}; const plot={inner_width:100};"
                "const off=%r, px=%r, xcol=%s, col=%s, dim='inner_width';"
                "(function(){%s})();"
                "console.log(JSON.stringify(src.data[col]));") % (
            json.dumps(a["xcol"]), json.dumps(xs), a["off"], a["px"],
            json.dumps(a["xcol"]), json.dumps(a["col"]), cb.code)
        out = json.loads(subprocess.run([node, "-e", prog],
                                        capture_output=True, text=True,
                                        check=True).stdout)
        want = [x - 1.0 * a["px"] * 10 / 100 for x in xs]
        assert out == pytest.approx(want)
        assert f == a["col"]

    def test_without_offset_the_x_is_the_variable(self, mode):
        r, _ = self._rect(mode, {"mwidth": "mwidth"})
        f = r.glyph.x if isinstance(r.glyph.x, str) else r.glyph.x.field
        assert f == "weight"


def _contours(rs):
    return [r for r in rs if type(r).__name__ == "ContourRenderer"]


@pytest.mark.parametrize("mode", MODES)
class TestContourParts:
    """contour's outlines, alpattern() and sort, as twoway draws them on a
    grid (measured 19oct2026, graph export SVG): outlines
    leaves the plot as it is (WP-37 TR-13a: it outlines the key's boxes,
    test_contour_outlines.py); alpattern()
    dashes their hairline boundaries (twoway's .001 line, a third of a
    medium one in its SVG), and sort draws what alpattern(dash) draws."""

    def _figs(self, mode, opts):
        if isinstance(opts, dict):
            opts = [opts]
        d = tsr._draw(tp._spec([plot_for("contour", o) for o in opts],
                               {"scheme": "stcolor"}, {}), mode)
        rs = [r for f in d.figures for r in f.renderers]
        return rs, [m for m in d.warnings if m.startswith("dash")]

    def test_outlines_outlines_the_key_not_the_plot(self, mode):
        """Flipped (WP-37 TR-13a): outlines drew the bands' boundaries black
        at twice a medium line; twoway draws the plot as without it and
        outlines the colour key's boxes (contour_outlines_truth.json)."""
        rs, notes = self._figs(mode, {"outlines": "outlines"})
        cs = _contours(rs)
        assert len(cs) == 1, cs
        assert not [n for n in notes if "outlines" in n]

    @pytest.mark.parametrize("o", [{"alpattern": "dash"}, {"sort": "sort"}])
    def test_alpattern_and_sort_dash_a_hairline(self, mode, o):
        rs, notes = self._figs(mode, o)
        cs = _contours(rs)
        assert len(cs) == 2, cs
        lr = cs[1].line_renderer
        d = lr.data_source.data.get("line_dash")
        dash = list(d[0]) if d else list(lr.glyph.line_dash)
        assert dash not in ([], ["solid"])
        assert not [n for n in notes if "alpattern" in n or "sort" in n]


@pytest.mark.parametrize("mode", MODES)
class TestRbarMwidthBaroffsetTurned:
    """rbar mwidth horizontal baroffset(#): each marker-tall bar moved #
    of its own heights down the screen, toward the lower values -- (1) by
    +33.75 of the SVG's y, (-1) by -33.75, (5) by +168.75 (measured
    19oct2026) -- as upright it moves left."""

    def test_the_turned_bars_move_along_y(self, mode):
        rs, notes = _renderers(plot_for("rbar", {
            "mwidth": "mwidth", "baroffset": "1",
            "horizontal": "horizontal"}), mode)
        [r] = [r for r in rs if type(r.glyph).__name__ == "Rect"]
        cbs = getattr(r, "_dash_rbo_callbacks", [])
        assert cbs, "no screen-offset callback"
        a = cbs[0].args
        assert a["dim"] == "inner_height"
        f = r.glyph.y if isinstance(r.glyph.y, str) else r.glyph.y.field
        assert f == a["col"]
        assert not [n for n in notes if "baroffset" in n]
