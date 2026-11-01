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
        assert f.aspect_ratio == pytest.approx(7.5 / 4.5)
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
        assert figs[0].aspect_ratio == pytest.approx(ratio)

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
    # percent of four inches, centred (twoway, sizing_truth.json and
    figure_geometry_truth.json G_fx50/G_fy50 keep 7.5 x 4.5)."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt", ["fxsize", "fysize"])
    def test_frame(self, opt, mode):
        assert _truth()["G_" + opt[:2] + "50"]["inches"] == [7.5, 4.5]
        _, figs = _figs(mode, {opt: "50"})
        f = figs[0]
        assert f.aspect_ratio == pytest.approx(7.5 / 4.5)
        assert "max-width" not in dict(f.styles or {})
        est = f._dash_frame_est
        # The 192 px box holds the plot region and its axes, centred: the
        # rest of the nominal 720 x 432 graph is split on its two sides.
        if opt == "fxsize":
            assert f.min_border_left - est["left"] == pytest.approx(264,
                                                                    abs=1)
            assert f.min_border_right - est["right"] == pytest.approx(264,
                                                                      abs=1)
        else:
            assert f.min_border_top - est["above"] == pytest.approx(120,
                                                                    abs=1)
            assert f.min_border_bottom - est["below"] == pytest.approx(
                120, abs=1)
