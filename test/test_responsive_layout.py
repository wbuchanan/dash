"""
test_responsive_layout.py -- no dashboard scrolls sideways, at a phone, a
tablet or a desktop width (TR-27.2).

The defect (release gate WP-27, measured in headless Chrome through an
iframe exactly 375 px wide): the saved examples/geometry_responsive.do page
(layout(bs)) kept its by(foreign) facet panels side by side at 266 px each,
the page 545 px wide with one figure offscreen, although dash.sthlp says
that under layout(bs) "below 768 every item takes the whole row"; and
examples/full_dashboard.do (layout(3 2)) kept two 220 px columns, the page
440 px wide with two figures offscreen.  Every gridplot() grid -- the
layout(r c) and automatic grids, each tab's grid and each facet grid --
sized its columns `auto', so no column could be narrower than its figure's
natural minimum (about 220 px); a 1 x 4 grid overflowed a 768 px window
the same way.  The filter bar was a Bokeh row that did not wrap (411 px at
375), and the filterposition(left) sidebar kept its 240 px beside the grid.

Fixed by _dash_reflow (dash_render.py), which every grid, the filter bar
and the sidebar row pass through, in both render modes.

Two kinds of test:

* TestPagesFitInChrome / TestServedDocumentsFitInChrome render pages from
  specs with the Python renderer (no Stata) and measure them in headless
  Chrome at 375, 768 and 1440 px (test/responsive_probe.py, the gate's own
  method): no horizontal scroll, no figure or KPI card offscreen, none
  overlapping another, every figure at least MIN_FIGURE_PX wide and
  MIN_FIGURE_H tall.  Without Chrome they skip, and a skip fails a
  DASH_STRICT=1 run (conftest.py).
* TestReflowModel and the rest: the Bokeh model properties and CSS the
  fix sets, with no browser.
"""
import importlib.util
import itertools
import json
import os
import re
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr
import responsive_probe as rp
from conftest import make_data_json

WIDTHS = (375, 768, 1440)
#: The narrowest a figure may be drawn at any of WIDTHS.  A grid column
#: stacks below _DASH_MIN_COLUMN_PX (240), so no figure is drawn narrower
#: than that, less the layout(bs) cell padding and rounding.
MIN_FIGURE_PX = 200
#: The shortest: a figure squeezed by a flex container collapsed to 160 px
#: of a 375 px width before the sidebar fix; 100 catches a collapse.
MIN_FIGURE_H = 100

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_resp_spec_")

_rng = np.random.default_rng(1)
_N = 74
_DF = pd.DataFrame({
    "mpg": _rng.integers(12, 41, _N).astype(float),
    "weight": _rng.integers(1760, 4841, _N).astype(float),
    "price": _rng.integers(3291, 15907, _N).astype(float),
    "length": _rng.integers(142, 234, _N).astype(float),
    "foreign": _rng.choice([0.0, 1.0], _N),
    "rep78": _rng.choice([1.0, 2.0, 3.0, 4.0, 5.0], _N),
})
_VL = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLN = {"foreign": "origin"}


# ---------------------------------------------------------------------------
# Specs: one per layout family
# ---------------------------------------------------------------------------

def _sc(y, x):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": {}}


def _graph(name, plots, **go):
    go = dict(go)
    go["name"] = name
    go.setdefault("title", name)
    go.setdefault("xtitle", "Weight (lbs.)")
    go.setdefault("ytitle", "Mileage (mpg)")
    return {"name": name, "graph_options": go, "options": dict(go),
            "plots": plots, "if_expr": "", "in_expr": ""}


def _kpi(name):
    return {"name": name, "stat": "mean", "var": "mpg", "fmt": "%9.1f",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter"}


def _spec(graphs, kpis=(), **bo):
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": "", "session_scheme": "", "title": "Responsive",
         "subtitle": "", "registry": "", "tabs": "",
         "filter_position": "top", "level": "95", "formats": {}}
    b.update(bo)
    if not b["registry"]:
        b["registry"] = " ".join([g["name"] for g in graphs]
                                 + [k["name"] for k in kpis])
    return {"graphs": list(graphs), "kpis": list(kpis), "build_options": b}


_FOUR = [
    _graph("s1", [_sc("mpg", "weight")]),
    _graph("h1", [{"type": "histogram", "var": "price", "options": {}}],
           xtitle="Price", ytitle="Count"),
    _graph("s2", [_sc("mpg", "length")], xtitle="Length"),
    _graph("d1", [{"type": "kdensity", "var": "mpg", "options": {}}],
           xtitle="MPG", ytitle="Density"),
]
_K4 = [_kpi("k1"), _kpi("k2"), _kpi("k3"), _kpi("k4")]
_FILTERS = "foreign, type(dropdown); weight, type(range)"

FAMILIES = {
    # examples/geometry_responsive.do's shape: layout(bs), KPIs, a wide
    # graph and a by(foreign) facet grid.
    "bs_facet": _spec([_graph("wide", [_sc("mpg", "weight")],
                              xsize="10", ysize="2"),
                       _graph("f", [_sc("mpg", "weight")], by="foreign")],
                      _K4, layout="bs"),
    "bs_filters_left": _spec(_FOUR, _K4, layout="bs", filter=_FILTERS,
                             filter_position="left"),
    # examples/full_dashboard.do's shape: layout(3 2), link(), filters.
    "grid_3x2_filters": _spec(_FOUR, _K4, layout="3 2", link="s1 s2",
                              filter=_FILTERS),
    "grid_auto": _spec(_FOUR, _K4),
    "grid_1x4": _spec(_FOUR, layout="1 4"),
    "grid_filters_left": _spec(_FOUR, _K4, layout="3 2", filter=_FILTERS,
                               filter_position="left"),
    "tabs": _spec(_FOUR, _K4, tabs="A: s1 h1 k1 k2 / B: s2 d1 k3 k4"),
    "tabs_facet": _spec([_graph("f", [_sc("mpg", "weight")], by="rep78"),
                         _graph("s1", [_sc("mpg", "weight")])],
                        tabs="A: f s1"),
    "facet": _spec([_graph("f", [_sc("mpg", "weight")], by="rep78")]),
    "facet_linked": _spec([_graph("f", [_sc("mpg", "weight")], by="foreign"),
                           _graph("s1", [_sc("mpg", "weight")])],
                          link="_all"),
    "facet_cols4": _spec([_graph("f", [_sc("mpg", "weight")],
                                 by="rep78, cols(4)")]),
}
SERVED = ("bs_facet", "bs_filters_left", "grid_3x2_filters",
          "grid_filters_left", "tabs_facet", "facet_linked")


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_DF, _VL, _VLN), fh)
    return tag, sp, dp


def _saved_page(spec):
    _, sp, dp = _write(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.DashRenderer(sp, dp).render()


def _served_doc(spec):
    from bokeh.document import Document
    tag, sp, dp = _write(spec)
    ap = os.path.join(_TMP, "app_%d.py" % tag)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        ms = importlib.util.spec_from_file_location("_resp_app_%d" % tag, ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    return doc


def _served_page(spec):
    """The served document's layout as a standalone page: the same Bokeh
    models the server sends, without its Python callbacks, which do not
    change a layout."""
    import logging
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    doc = _served_doc(spec)
    log = logging.getLogger("bokeh.embed.util")
    level = log.level
    log.setLevel(logging.ERROR)   # "real Python callbacks" in a file
    try:
        return file_html(doc, INLINE, "served")
    finally:
        log.setLevel(level)


def _chrome():
    chrome = rp.find_chrome()
    if chrome is None:
        pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                    "the responsive measurement needs a browser")
    return chrome


def _check(name, results):
    bad = []
    counts = {r["canvases"] for r in results.values()}
    for w in WIDTHS:
        r = results[w]
        if r["W"] != w:
            bad.append("%d: the iframe reported %r" % (w, r["W"]))
        if r["sw"] > w:
            bad.append("%d: the page is %d px wide" % (w, r["sw"]))
        if r["offscreen"]:
            bad.append("%d: %d item(s) offscreen" % (w, r["offscreen"]))
        if r["overlap"]:
            bad.append("%d: %d overlapping pair(s)" % (w, r["overlap"]))
        if not r["canvases"]:
            bad.append("%d: no figure drawn" % w)
        elif r["min_width"] < MIN_FIGURE_PX:
            bad.append("%d: a figure %d px wide" % (w, r["min_width"]))
        elif r["min_height"] < MIN_FIGURE_H:
            bad.append("%d: a figure %d px tall" % (w, r["min_height"]))
    if len(counts) != 1:
        bad.append("the figure count changes with width: %s" % sorted(counts))
    assert not bad, "%s: %s\n%s" % (name, "; ".join(bad), json.dumps(
        results, indent=1))


class TestPagesFitInChrome:
    """The saved page of every layout family, at 375, 768 and 1440 px."""

    @pytest.mark.parametrize("name", sorted(FAMILIES))
    def test_saved_page_fits(self, name):
        chrome = _chrome()
        page = _saved_page(FAMILIES[name])
        _check(name, rp.measure_many(page, WIDTHS, chrome))


class TestServedDocumentsFitInChrome:
    """The served document's layout at the same widths (TR-27.2): its
    grids stack as the saved ones do.  A phone shows the served app at
    desktop width (it declares no viewport; dash.sthlp says so), so this
    is the served app in a browser window of that width."""

    @pytest.mark.parametrize("name", SERVED)
    def test_served_document_fits(self, name):
        chrome = _chrome()
        page = _served_page(FAMILIES[name])
        _check("served " + name, rp.measure_many(page, WIDTHS, chrome))


class TestTheProbe:
    """The measurement itself: an overflowing page is reported as one."""

    def test_a_wide_page_is_reported(self):
        chrome = _chrome()
        page = ("<html><head></head><body style='margin:0'>"
                "<canvas width='600' height='200' style='width:600px;"
                "height:200px'></canvas></body></html>")
        r = rp.measure_many(page, (375,), chrome)[375]
        assert r["W"] == 375 and r["sw"] >= 600
        assert r["offscreen"] == 1 and r["min_width"] == 600

    def test_overlap_is_reported(self):
        chrome = _chrome()
        page = ("<html><body style='margin:0'>"
                "<canvas style='position:absolute;left:0;top:0;width:200px;"
                "height:100px'></canvas>"
                "<canvas style='position:absolute;left:50px;top:50px;"
                "width:200px;height:100px'></canvas></body></html>")
        r = rp.measure_many(page, (375,), chrome)[375]
        assert r["overlap"] == 1 and r["offscreen"] == 0

    def test_with_probe_goes_before_body_end(self):
        out = rp.with_probe("<html><body>x</body></html>")
        assert out.index("DASHPROBE") < out.index("</body>")
        assert "DASHPROBE" in rp.with_probe("<p>no body</p>")

    def test_find_chrome_honours_only_an_executable(self, monkeypatch,
                                                    tmp_path):
        f = tmp_path / "not-chrome"
        f.write_text("")
        f.chmod(0o644)
        monkeypatch.setenv("DASH_CHROME", str(f))
        assert rp.find_chrome() != str(f)


# ---------------------------------------------------------------------------
# The model properties and CSS the fix sets (no browser)
# ---------------------------------------------------------------------------

def _css(model):
    return " ".join(getattr(s, "css", s) for s in model.stylesheets)


def _all_models(root, cls):
    return [m for m in root.references() if isinstance(m, cls)]


class TestReflowModel:
    """_dash_reflow, on each kind of model it is given."""

    def _grid(self, ncols, nrows=1):
        from bokeh.layouts import gridplot
        from bokeh.plotting import figure
        rows = [[figure() for _ in range(ncols)] for _ in range(nrows)]
        return gridplot(rows, sizing_mode="stretch_width")

    def test_a_gridplot_gets_equal_shrinkable_columns(self):
        g = dr._dash_reflow(self._grid(2))
        assert g.cols == dr._DASH_BS_TRACK == "minmax(0, 1fr)"

    def test_a_gridplot_stacks_below_ncols_times_the_minimum(self):
        for n in (2, 3, 4):
            css = _css(dr._dash_reflow(self._grid(n)))
            assert ":host { container-type: inline-size; }" in css
            want = n * dr._DASH_MIN_COLUMN_PX - 0.02
            assert "@container (max-width: %.2fpx)" % want in css
            assert (":host > .bk-GridBox { display: flex; "
                    "flex-direction: column; }") in css

    def test_a_one_column_grid_gets_no_query(self):
        g = dr._dash_reflow(self._grid(1, nrows=3))
        assert g.cols == dr._DASH_BS_TRACK
        assert "@container" not in _css(g)

    def test_the_minimum_is_240(self):
        assert dr._DASH_MIN_COLUMN_PX == 240
        assert dr._DASH_BS_STACK_BELOW_PX == 768

    def test_a_gridbox_stacks_below_768_of_window(self):
        from bokeh.models import GridBox
        from bokeh.plotting import figure
        g = dr._dash_reflow(GridBox(children=[(figure(), 0, 0),
                                              (figure(), 0, 1)]))
        css = _css(g)
        assert "@media (max-width: 767.98px)" in css
        assert "display: flex !important" in css
        assert "flex-direction: column !important" in css
        assert "@container" not in css

    def test_a_row_wraps_and_stacks_only_when_asked(self):
        from bokeh.layouts import row
        from bokeh.models import Div
        wrapped = _css(dr._dash_reflow(row(Div(), Div()), stack=False))
        assert wrapped == ":host { flex-wrap: wrap !important; }"
        stacked = _css(dr._dash_reflow(row(Div(), Div())))
        assert ":host { flex-wrap: wrap !important; }" in stacked
        assert "@media (max-width: 767.98px)" in stacked
        assert "flex-direction: column !important" in stacked
        # Without this the grid below the sidebar collapsed to 0 px tall:
        # a Bokeh row child's flex basis is 0.
        assert ":host > * { flex: 0 0 auto; }" in stacked

    def test_it_appends_and_returns_the_model(self):
        from bokeh.layouts import row
        from bokeh.models import Div, InlineStyleSheet
        r = row(Div(), Div())
        mine = InlineStyleSheet(css=".x{}")
        r.stylesheets = [mine]
        assert dr._dash_reflow(r) is r
        assert r.stylesheets[0] is mine and len(r.stylesheets) == 2


class TestReflowAdversarial:
    """Nothing the user writes reaches the CSS, and odd grids stay bounded."""

    def test_non_integer_positions_are_skipped(self):
        from bokeh.layouts import gridplot
        from bokeh.plotting import figure
        g = gridplot([[figure(), figure()]], sizing_mode="stretch_width")

        class Fake:
            children = [(None, 0, "1; } :host { display:none"),
                        (None, 0, 1)]
            stylesheets = []
            cols = None
        f = Fake()
        dr._dash_reflow(f)
        css = _css(f)
        assert "display:none" not in css
        assert "max-width: 479.98px" in css
        dr._dash_reflow(g)
        assert re.fullmatch(r"[\w\s:{}().;>,\-!@]+", _css(g))

    def test_a_huge_column_count_is_a_number_not_a_loop(self):
        class Fake:
            children = [(None, 0, 10 ** 9)]
            stylesheets = []
            cols = None
        f = Fake()
        dr._dash_reflow(f)
        assert len(_css(f)) < 300

    def test_a_title_cannot_reach_the_stylesheet(self):
        spec = _spec([_graph("f", [_sc("mpg", "weight")], by="foreign",
                             title="x} :host{display:none} @media{")],
                     layout="2 1")
        from bokeh.models import InlineStyleSheet
        r_spec = spec
        _, sp, dp = _write(r_spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        for s in _all_models(r._last_layout_root, InlineStyleSheet):
            if "container-type" in s.css:
                assert "display:none" not in s.css


class TestEveryGridIsReflowed:
    """Every grid, the filter bar and the sidebar go through _dash_reflow,
    in both modes."""

    def _saved_root(self, spec):
        _, sp, dp = _write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        return r._last_layout_root

    @pytest.mark.parametrize("name", ["grid_3x2_filters", "tabs_facet",
                                      "facet_linked", "grid_filters_left"])
    def test_saved_grids(self, name):
        from bokeh.models import GridPlot, Row
        root = self._saved_root(FAMILIES[name])
        grids = _all_models(root, GridPlot)
        assert grids
        for g in grids:
            assert g.cols == dr._DASH_BS_TRACK
        rows = _all_models(root, Row)
        assert all("flex-wrap: wrap" in _css(x) for x in rows)

    @pytest.mark.parametrize("name", ["grid_3x2_filters", "tabs_facet",
                                      "bs_facet", "grid_filters_left"])
    def test_served_grids(self, name):
        from bokeh.models import GridBox, GridPlot, Row
        doc = _served_doc(FAMILIES[name])
        models = [m for root in doc.roots for m in root.references()]
        grids = [m for m in models if isinstance(m, GridPlot)]
        for g in grids:
            assert g.cols == dr._DASH_BS_TRACK
        boxes = [m for m in models if type(m) is GridBox]
        for b in boxes:
            assert "@media (max-width: 767.98px)" in _css(b)
        assert grids or boxes
        for x in (m for m in models if isinstance(m, Row)):
            assert "flex-wrap: wrap" in _css(x)

    def test_the_facet_grid_on_a_bs_page_stacks(self):
        page = _saved_page(FAMILIES["bs_facet"])
        assert "container-type: inline-size" in page
        assert "@container (max-width: 479.98px)" in page

    def test_the_filter_bar_does_not_stack_but_the_sidebar_does(self):
        from bokeh.models import Row
        top = self._saved_root(FAMILIES["grid_3x2_filters"])
        bars = _all_models(top, Row)
        assert bars and all("@media" not in _css(b) for b in bars)
        left = self._saved_root(FAMILIES["grid_filters_left"])
        rows = _all_models(left, Row)
        assert any("flex-direction: column" in _css(b) for b in rows)

    def test_the_app_copies_the_helper_and_its_constants(self):
        _, sp, dp = _write(FAMILIES["grid_3x2_filters"])
        ap = os.path.join(_TMP, "app_src_%d.py" % next(_SEQ))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        src = open(ap).read()
        assert "def _dash_reflow(" in src
        assert "_DASH_MIN_COLUMN_PX = 240" in src
        assert "_DASH_BS_STACK_BELOW_PX = 768" in src
        assert "_dash_reflow(gridplot(grid_rows" in src
        assert "_dash_reflow(row(filter_widgets" in src


class TestKpiCardMayNarrow:
    """A KPI card's 160 px minimum yields to a narrower cell: the served
    layout(bs) grid beside the filter sidebar at 768 px gave a span-3 card
    about 120 px, and the 160 px card pushed the page to 813 px."""

    def test_python_card(self):
        card = dr._dash_kpi_card_html("T", "1", "", "", "", "k1",
                                      dr.SchemeParser("s2color"))
        assert "min-width:min(160px,100%)" in card
        assert "min-width:160px" not in card

    def test_js_rebuild_card(self):
        # The filter callback rebuilds the card from a JS template, which
        # must keep the Python card's markup (test_scheme_review_fixes).
        src = open(dr.__file__, encoding="utf-8").read()
        assert "min-width:160px" not in src
        assert src.count("min-width:min(160px,100%)\">") == 2

    def test_rendered_card(self):
        page = _saved_page(_spec([_graph("s1", [_sc("mpg", "weight")])],
                                 [_kpi("k1")]))
        assert "min-width:min(160px,100%)" in page
