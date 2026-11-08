"""
test_figure_geometry.py -- twoway's figure shape and size box, by() graphs
included (WP-45 VF-4 with VF-11, GW-20 and sil:SD-21; DECISIONS A-1).
VF-5's size unit is not drawn yet (VF-4 closed in part).

Before: every figure stretched across the page inside a 160-560 px height
band (2.14:1 at 1200 px where twoway's stcolor graph is 7.5 x 4.5,
1.667:1), xsize()/ysize() without aspectratio() changed only the ratio,
aspectratio() alone reshaped the whole figure, relative sizes were a fixed
2.88 pt a unit whatever the scheme (twoway's stcolor unit is 3.24 pt, its
reference side 4.5 inches), fxsize()/fysize() shrank the cell, and a by()
panel carried the band in its stylesheet.

twoway's measured geometry is test/fixtures/figure_geometry_truth.json
(scripts/extract_figure_geometry_truth.do): ``G_stcolor`` is 7.5 x 4.5
inches with tick labels at 11.26 pt, ``G_s2color`` 5.5 x 4 with 10.0 pt
(the ratio 1.125 is the unit's), ``G_xs44`` 4 x 4, ``G_xs9`` 9 x 4.5,
``G_by_xs84`` 8 x 4; ``G_fx50``/``G_fy50`` keep the 7.5 x 4.5 graph.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tbk  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402

_MODES = ("saved", "served")
_FIX = os.path.join(_HERE, "fixtures", "figure_geometry_truth.json")
_ONE = tbk._ONE


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)["probes"]


def _figs(mode, go, scheme="stcolor"):
    """Every figure *mode* draws for ``scatter mpg weight, <go>``."""
    from bokeh.plotting import figure as _fcls
    spec = tbk._spec([tbk._graph("g1", _ONE, go, title=False)],
                     scheme=scheme)
    roots, _, _ = tbk._build(mode, spec)
    out = []
    for root in roots:
        out += [m for m in root.references() if isinstance(m, _fcls)
                and m not in out]
    return roots, out


def _inner(ratio, scheme="stcolor"):
    """The figure's width/height inside the scheme's graph margin (WP-45
    GW-6): the graph region keeps *ratio*."""
    return dr._dash_inner_ratio(ratio, dr._dash_graph_margin_pct(
        {}, dr.SchemeParser(scheme)))


def _pt(css):
    return dr.OptionTranslator.css_to_pt(css)


class TestTheFixture:
    def test_it_is_stamped_and_measured(self):
        with open(_FIX, encoding="utf-8") as fh:
            d = json.load(fh)
        assert d["_meta"]["source"] == \
            "scripts/extract_figure_geometry_truth.do"
        p = d["probes"]
        assert p["G_stcolor"]["canvas"]["w"] == 5400
        assert p["G_stcolor"]["canvas"]["h"] == 3240
        assert p["G_by_stcolor"]["inches"] == [7.5, 4.5]
        assert p["G_xs44"]["inches"] == [4.0, 4.0]
        assert p["G_xs9"]["inches"] == [9.0, 4.5]
        assert p["G_by_xs84"]["inches"] == [8.0, 4.0]


class TestTheThreeCases:
    """D-45-04.a: xsize()/ysize() draw the exact box at 96 px an inch;
    without them the width fills the cell at the scheme's graphsize ratio
    with no height band; aspectratio() alone shapes the plot region."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("probe,go", [
        ("G_xs44", {"xsize": "4", "ysize": "4"}),
        ("G_xs9", {"xsize": "9"}),
    ])
    def test_box(self, probe, go, mode):
        w_in, h_in = _truth()[probe]["inches"]
        _, figs = _figs(mode, go)
        f = figs[0]
        assert f.sizing_mode == "fixed"
        assert (f.width, f.height) == (round(w_in * 96), round(h_in * 96))
        assert f.min_height is None and f.max_height is None
        assert f.aspect_ratio is None

    @pytest.mark.parametrize("mode", _MODES)
    def test_aspectratio_alone_shapes_the_plot_region(self, mode):
        _, figs = _figs(mode, {"aspectratio": "1"})
        f = figs[0]
        assert f.sizing_mode == "stretch_width"
        # Flipped (BUGS.md "A graph's canvas ended before its own x axis,
        # x title and colour key labels"): the figure keeps what the graph
        # margin leaves; its graph region box round it keeps the graph's.
        assert f.aspect_ratio == pytest.approx(_inner(7.5 / 4.5))
        assert f.min_height is None and f.max_height is None
        # Square at the nominal 720 x 432 box (7.5 x 4.5 in at 96 px).
        fw = 720 - f.min_border_left - f.min_border_right
        fh = 432 - f.min_border_top - f.min_border_bottom
        assert fw == pytest.approx(fh, abs=1)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("scheme,ratio", [("stcolor", 7.5 / 4.5),
                                              ("s2color", 5.5 / 4.0)])
    def test_no_band(self, scheme, ratio, mode):
        for go in ({}, {"by": "foreign"}):
            _, figs = _figs(mode, go, scheme)
            for f in figs:
                assert f.min_height is None and f.max_height is None, go
                css = " ".join(getattr(s, "css", "") or ""
                               for s in f.stylesheets)
                assert "max-height" not in css, go
        _, figs = _figs(mode, {}, scheme)
        # Flipped (BUGS.md "A graph's canvas ended before its own x axis,
        # x title and colour key labels"): the figure keeps what the graph
        # margin leaves; its graph region box round it keeps the graph's.
        assert figs[0].aspect_ratio == pytest.approx(_inner(ratio, scheme))

    @pytest.mark.parametrize("mode", _MODES)
    def test_by_box(self, mode):
        roots, figs = _figs(mode, {"by": "foreign", "xsize": "8",
                                   "ysize": "4"})
        grid = tbk._grids(roots)
        grid = next(iter(grid.values()))
        st = dict(grid.styles or {})
        assert st.get("width") == "768px", st
        cbs = [cb for f in figs for k in dr._DASH_SPAN_KEYS
               for cb in f.js_property_callbacks.get("change:" + k, [])
               if cb.code == dr._DASH_BY_FIT_JS]
        assert cbs and cbs[0].args["ratio"] == pytest.approx(2.0)

    def test_the_box(self):
        st = dr.SchemeParser("stcolor")
        gx, gy = st.graphsize_x, st.graphsize_y
        assert dr._dash_graph_box_in({}, gx, gy) is None
        assert dr._dash_graph_box_in({"xsize": "9"}, gx, gy) == (9.0, 4.5)
        assert dr._dash_graph_box_in({"xsize": "abc"}, gx, gy) is None
        assert dr._dash_graph_box_in({"ysize": "2"}, gx, gy) == (7.5, 2.0)

    @requires_node
    def test_the_follow_runs_once_per_size(self):
        """The follow writes on a new drawn size only: run twice at one
        outer size, the second run writes nothing."""
        from bokeh.plotting import figure
        f = figure(width=720, height=432, sizing_mode="stretch_width",
                   aspect_ratio=7.5 / 4.5)
        dr._dash_frame_slack(f, 1.0, "c", 720, 432)
        cbs = [cb for k in ("outer_width", "outer_height")
               for cb in f.js_property_callbacks.get("change:" + k, [])]
        assert len(cbs) == 2 and cbs[0] is cbs[1]
        cb = cbs[0]
        assert cb.code == dr._DASH_GRAPH_MARGIN_JS
        src = """
const fig = {outer_width: 1400, outer_height: 840,
             min_border_left: %d, min_border_right: %d,
             min_border_top: %d, min_border_bottom: %d};
const item = %s;
let writes = 0;
const prox = new Proxy(fig, {set(t, k, v) { writes += 1; t[k] = v;
                                           return true; }});
const run = () => (function (fig, item) { %s })(prox, item);
run(); const first = writes; run();
console.log(JSON.stringify({first: first, second: writes - first,
                            fig: fig}));
""" % (f.min_border_left, f.min_border_right, f.min_border_top,
            f.min_border_bottom, json.dumps(cb.args["item"]), cb.code)
        got = run_js(src)
        assert got["first"] > 0 and got["second"] == 0, got
        g = got["fig"]
        fw = 1400 - g["min_border_left"] - g["min_border_right"]
        fh = 840 - g["min_border_top"] - g["min_border_bottom"]
        assert fw == pytest.approx(fh, abs=1)


class TestTheHelpers:
    def test_border_base(self):
        from bokeh.plotting import figure
        f = figure()
        f.min_border_left = 80
        est = {"left": 45.0, "right": 5.0, "above": 30.0, "below": 45.0}
        assert dr._dash_border_base(f, est) == [80.0, 5.0, 30.0, 45.0]


class TestFxFy:
    """D-45-04.c: fxsize(#)/fysize(#) keep the graph and draw the plot in
    # percent of the scheme's reference side (WP-45 VF-4: 4 inches under
    s2color, 4.5 under stcolor), centred (twoway, sizing_truth.json and
    figure_geometry_truth.json G_fx50/G_fy50 keep 7.5 x 4.5)."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt", ["fxsize", "fysize"])
    def test_frame(self, opt, mode):
        assert _truth()["G_" + opt[:2] + "50"]["inches"] == [7.5, 4.5]
        _, figs = _figs(mode, {opt: "50"})
        f = figs[0]
        # Flipped (BUGS.md "A graph's canvas ended before its own x axis,
        # x title and colour key labels"): the figure keeps what the graph
        # margin leaves; its graph region box round it keeps the graph's.
        assert f.aspect_ratio == pytest.approx(_inner(7.5 / 4.5))
        assert "max-width" not in dict(f.styles or {})
        est = f._dash_frame_est
        # Flipped (WP-45 VF-4): the box was 50% of 4 inches (192 px) under
        # every scheme; twoway's is # percent of the scheme's reference
        # side, 4.5 inches under stcolor (G_fx50: the plot region and its
        # axes 1890..3510 of 5400 SVG units, 2.25 in; G_fy50 810..2430 of
        # 3240), so 216 px holds the plot region and its axes, centred:
        # the rest of the nominal 720 x 432 graph is split on its sides.
        # The axes inside it are drawn at stcolor's 1.125 unit (D66), so
        # each estimated border grows by an eighth beside the slack.
        t = _truth()["G_" + opt[:2] + "50"]

        def grown(side, key):
            return max(5.0, est[key]) * 1.125
        if opt == "fxsize":
            assert f.min_border_left - grown("left", "left") == \
                pytest.approx(252, abs=1)
            assert f.min_border_right - grown("right", "right") == \
                pytest.approx(252, abs=1)
            plot = [r for r in t["rects"] if r["stroke"] is None
                    and r["w"] < 5400][0]
            # twoway's: the plot region less G_stcolor's 409.4-unit y
            # axis on its left starts 1890 units in, (5400 - 1620) / 2.
            assert plot["x"] - 409.4 == pytest.approx(1890, abs=1)
        else:
            assert f.min_border_top - grown("top", "above") == \
                pytest.approx(108, abs=1)
            assert f.min_border_bottom - grown("bottom", "below") == \
                pytest.approx(108, abs=1)
            plot = [r for r in t["rects"] if r["stroke"] is None
                    and r["h"] < 3240][0]
            assert plot["y"] == pytest.approx(810, abs=1)
        assert f._dash_gm_item["fxy"]["ref"] == pytest.approx(4.5)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt", ["fxsize", "fysize"])
    def test_by_array(self, opt, mode):
        """by(foreign) fxsize(50)/fysize(50): twoway keeps the 7.5 x 4.5
        graph and draws the array -- strips, panels and axes -- in 50% of
        the 4.5-inch reference side, centred (G_fx50_by: the panels'
        left 2329.93 of 5400, G_by_stcolor's 553.33 less its 439.93
        units beside the array, 1890 = (5400 - 1620) / 2; G_fy50_by: the
        strips at 848.81 of 3240, by_indiv's 38.91 units under the
        array's top, 809.9).  Before: the array was 192 px at any drawn
        width (unscaled, D66), fysize() shortened the whole graph and
        neither was centred in the graph's height."""
        t = _truth()
        if opt == "fxsize":
            px = t["G_fx50_by"]["rects"][3]["x"]
            base = t["G_by_stcolor"]["rects"][3]["x"]
            assert px - (base - 113.4) == pytest.approx(1890, abs=1)
        else:
            sy = t["G_fy50_by"]["rects"][7]["y"]
            base = t["G_by_stcolor"]["rects"][7]["y"]
            assert sy - (base - 113.4) == pytest.approx(810, abs=1)
        roots, figs = _figs(mode, {"by": "foreign", opt: "50"})
        boxes = [m for r in roots for m in r.references()
                 if "dash_graph_region" in (getattr(m, "tags", None) or [])]
        assert len(boxes) == 1, boxes
        st = dict(boxes[0].styles or {})
        # The graph region keeps the graph's shape and centres the array.
        assert st.get("aspect-ratio") == "7.5 / 4.5", st
        assert st.get("justify-content") == "center", st
        grid = next(iter(tbk._grids(roots).values()))
        cbs = [cb for f in figs for k in dr._DASH_SPAN_KEYS
               for cb in f.js_property_callbacks.get("change:" + k, [])
               if cb.code == dr._DASH_BY_FIT_JS]
        assert cbs, figs
        a = cbs[0].args
        pct = dr._dash_graph_margin_pct({}, dr.SchemeParser("stcolor"))
        inner = 720.0 * (1 - (pct[0] + pct[1]) / 100.0)
        assert a["cnom"] == pytest.approx(inner)
        [wcb] = {cb.id: cb for f in figs for k in dr._DASH_SPAN_KEYS
                 for cb in f.js_property_callbacks.get("change:" + k, [])
                 if cb.code == dr._DASH_WIDTH_SCALE_JS}.values()
        if opt == "fxsize":
            assert a["fx_px"] == 216 and a["fy_px"] is None
            gst = dict(grid.styles or {})
            assert gst["width"] == "%.4g%%" % (216 / inner * 100), gst
            assert gst["margin-left"] == "auto", gst
            # D66: the array's width is 216 nominal px.
            assert wcb.args["nominal"] == pytest.approx(216)
        else:
            # 216 nominal px less the first row's by_indiv top margin
            # (1.2 units: the 9 px row spacing halved at 3.84 px a unit,
            # as a share of the 7.5 in width), which the graph region's
            # padding holds.
            top = round(2.4 * 3.84) / 2.0 / 3.84 * 4.5 / 7.5 / 100 * 720
            assert a["fy_px"] == pytest.approx(216 - top)
            assert a["fx_px"] is None
            assert wcb.args["nominal"] == pytest.approx(inner)


class TestOnePicture:
    """DECISIONS D66 (the maintainer's ruling of 01nov2026): the graph is
    one picture -- every size scales with the drawn width against the
    scheme's inch width, times twoway's unit for the reference side -- and
    a page has one toolbar, laid over the grid, so the graph area is
    twoway's box."""

    def test_entries(self):
        from bokeh.plotting import figure
        f = figure()
        f.xaxis[0].major_label_text_font_size = "10pt"
        r = f.scatter([1], [2], size=6)
        got = [(m, p, b, k) for m, p, b, k in
               dr._dash_width_scale_entries([f])]
        assert (f.xaxis[0], "major_label_text_font_size", 10.0, "css") in got
        assert (r.glyph, "size", 6.0, "num") in got
        # One fixed order: a second build reads the same list.
        assert [(p, b) for _m, p, b, _k in got] == [
            (p, b) for _m, p, b, _k in dr._dash_width_scale_entries([f])]
        assert r.glyph.size == 6

    @requires_node
    def test_the_scale_runs_once_per_width(self):
        from bokeh.plotting import figure
        f = figure()
        f.xaxis[0].major_label_text_font_size = "10pt"
        cb = dr._dash_width_scale(f, [f], 720.0, 4.5)
        assert cb.code == dr._DASH_WIDTH_SCALE_JS
        ents = [[i, p, b, k] for i, (m, p, b, k) in
                enumerate(cb.args["entries"])]
        src = """
const ms = %s.map(() => ({}));
let writes = 0;
const entries = %s.map(([i, p, b, k]) => [new Proxy(ms[i], {set(t, q, v) {
  writes += 1; t[q] = v; return true; }}), p, b, k]);
const anchor = {outer_width: 1400};
const state = {k: null};
const run = () => (function (anchor, entries, plots, nominal, unit, by,
                             state, follows) { %s })(
  anchor, entries, [], 720, 1.125, false, state, []);
run(); const first = writes; run();
console.log(JSON.stringify({first: first, second: writes - first,
                            k: state.k, font: ms[%d].major_label_text_font_size}));
""" % (json.dumps(ents), json.dumps(ents), cb.code,
            [i for i, p, b, k in ents
             if p == "major_label_text_font_size"][0])
        got = run_js(src)
        assert got["first"] > 0 and got["second"] == 0, got
        assert got["k"] == pytest.approx(1400 / 720 * 1.125)
        assert got["font"] == "21.88pt"

    @pytest.mark.parametrize("mode", _MODES)
    def test_one_toolbar(self, mode):
        from bokeh.models import GridPlot
        roots, _ = _figs(mode, {"by": "foreign"})
        grids = [g for r in roots for g in r.select({"type": GridPlot})]
        shown = [g for g in grids if g.toolbar_location is not None]
        assert len(shown) == 1 and shown[0].toolbar.autohide is True
        css = " ".join(getattr(s, "css", "") for s in shown[0].stylesheets)
        assert dr._DASH_TOOLBAR_OVERLAY_CSS in css


    def test_a_grid_in_a_column_cell_loses_its_toolbar(self):
        """The nested grids are found through the layout: a by() grid
        under a strip's Column in a cell, as select() found it."""
        from bokeh.layouts import column, gridplot
        from bokeh.models import Div
        from bokeh.plotting import figure
        inner = gridplot([[figure(), figure()]])
        outer = gridplot([[column(Div(text="strip"), inner), figure()]])
        assert dr._dash_one_toolbar(outer) is outer
        assert inner.toolbar_location is None
        assert outer.toolbar_location is not None and outer.toolbar.autohide


class TestGraphRegion:
    """WP-45 GW-6 (VF-7): the scheme's graph margin is drawn around the
    graph, a by() array included (figure_geometry_truth.json M_stcolor:
    the plot region's top 113.4 of 3240 SVG units below the edge, 3.5% of
    the smaller side; M_by_stcolor alike), in the graph region's fill:
    the figure's (or the by() grid's) own CSS padding, a share of its
    width, inside a box that keeps the graph's shape."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("go", [{}, {"by": "foreign"}])
    def test_the_margin_box(self, go, mode):
        roots, figs = _figs(mode, go)
        boxes = [m for r in roots for m in r.references()
                 if "dash_graph_region" in (getattr(m, "tags", None) or [])]
        assert len(boxes) == 1, boxes
        st = dict(boxes[0].styles or {})
        # 3.5 units of min(7.5, 4.5) in, as a share of the 7.5 in width.
        pct = 3.5 * 4.5 / 7.5
        # Flipped (WP-41 41-05): a by() array's top also holds its first
        # row's by_indiv top margin (1.2 units: the 9 px row spacing
        # halved at 3.84 px a unit), as twoway's strips sit under it.
        top = pct + (round(2.4 * 3.84) / 2.0 / 3.84 * 4.5 / 7.5
                     if go else 0.0)
        assert st["padding"] == " ".join(["%.4g%%" % top]
                                         + ["%.4g%%" % pct] * 3)
        assert st["background-color"].lower() == \
            str(figs[0].border_fill_color).lower()

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_linked_graph_with_its_own_if(self, mode):
        """A linked graph with its own if draws through a row view; the
        saved page took that view for a by() panel's and gave the figure
        neither its box nor its graph margin.  It is drawn as the linked
        graph beside it is, in both modes."""
        import test_mode_parity as tp
        [p] = [p for p in tp.CORPUS if p.values[0]
               == "colorvar() on a linked graph with its own if"]
        if mode == "saved":
            figs = list(tp._standalone(p.values[1])[0].figures.values())
        else:
            from bokeh.plotting import figure as _fcls
            doc = tp._served(p.values[1])[0]
            figs = [f for r in doc.roots for f in r.select({"type": _fcls})]
        assert len(figs) == 2
        for f in figs:
            assert getattr(f, "_dash_nominal_px", None) == (528, 384)
            assert f.aspect_ratio == pytest.approx(figs[0].aspect_ratio)
            assert getattr(f, "_dash_region_cell", None) is not None

    def test_the_inner_ratio(self):
        pct = [2.1] * 4
        r = 7.5 / 4.5
        assert dr._dash_inner_ratio(r, pct) == pytest.approx(
            (1 - 0.042) / (1 / r - 0.042))
        st = dr.SchemeParser("stcolor")
        assert dr._dash_graph_margin_pct({}, st) == pytest.approx([2.1] * 4)

    def test_the_ruler_column(self):
        """by()'s stacking ruler goes just right of the panels: the columns
        from there move one right and a cell spanning across grows one."""
        from bokeh.models import Plot
        def cell(name=None):
            return Plot(name=name) if name else Plot()
        p1, p2, r1 = cell(), cell(), cell("dash_by_r1title")
        head, xt, ru = cell("dash_by_head"), cell("dash_by_xtitle"), \
            cell("dash_by_ruler")
        kids = [(head, 0, 0, 1, 4), (p1, 1, 1), (p2, 1, 2),
                (r1, 1, 3, 1, 1), (xt, 2, 1, 1, 2)]
        out = dr._dash_by_ruler_column(kids, ru)
        got = {id(c[0]): tuple(c[1:]) for c in out}
        assert got[id(ru)] == (1, 3, 1, 1)
        assert got[id(r1)] == (1, 4, 1, 1)
        assert got[id(head)] == (0, 0, 1, 5)
        assert got[id(xt)] == (2, 1, 1, 2)
        assert got[id(p2)] == (1, 2)
        # No panel: the ruler takes the last column, as before.
        out = dr._dash_by_ruler_column([(head, 0, 0, 1, 2)], ru)
        assert tuple(out[-1][1:]) == (0, 2, 1, 1)

    def test_the_panel_borders_and_row_gaps(self):
        """WP-41 41-05: an outer y axis cell reaches into its panel's
        left margin by a scaled negative margin, the y title's cell takes
        that margin on its right; the x title's row keeps half the row
        spacing and the foot's 0.7 units of it."""
        from bokeh.models import Plot
        yax, yt, p1 = Plot(name="dash_by_yaxis_0"), \
            Plot(name="dash_by_ytitle"), Plot()
        xt, foot = Plot(name="dash_by_xtitle"), Plot(name="dash_by_foot")
        dr._dash_by_panel_borders([(yt, 0, 0), (yax, 0, 1), (p1, 0, 2)], 13)
        assert yax.styles["margin-right"] == \
            "calc(-13px * var(--dash-by-k, 1))"
        assert yt.min_border_right == 13 and yt._dash_by_mb
        dr._dash_by_row_gaps([(p1, 0, 0), (xt, 1, 0), (foot, 2, 0)], 9)
        assert xt.styles["margin-top"] == "calc(-4.5px * var(--dash-by-k, 1))"
        u = dr.OptionTranslator.PT_PER_RS * dr.OptionTranslator.PX_PER_PT
        assert foot.styles["margin-top"] == \
            "calc(-%.4gpx * var(--dash-by-k, 1))" % (9 - 0.7 * u)



class TestTheLookupWalk:
    """``_dash_refs``: the models a page's lookup hooks see, as
    ``references()`` finds them, without building unread defaults."""

    @pytest.mark.parametrize("go", [{}, {"by": "foreign"}])
    def test_it_finds_what_references_finds(self, go):
        roots, _ = _figs("saved", go)
        for r in roots:
            assert dr._dash_refs(r) == r.references()

    def test_a_mapper_inside_a_field_transform(self):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        from bokeh.transform import factor_cmap
        fig = figure()
        cmap = factor_cmap("k", palette=["red", "blue"], factors=["a", "b"])
        fig.scatter("x", "y", color=cmap,
                    source=ColumnDataSource({"x": [1], "y": [2], "k": ["a"]}))
        assert cmap.transform in dr._dash_refs(fig)
