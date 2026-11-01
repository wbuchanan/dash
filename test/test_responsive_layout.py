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
import itertools
import json
import os
import re
import subprocess
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
from conftest import make_data_json, load_app

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

from conftest import render_models  # noqa: E402


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
    # BUGS.md "filterposition(left) under layout(auto) makes Bokeh print a
    # W-1005 validation warning": the sidebar beside the automatic grid.
    "auto_filters_left": _spec(_FOUR, _K4, filter=_FILTERS,
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
    # WP-28 E14: the automatic layout(bs) grid the served half rows and KPI
    # cell heights were measured against -- four span-3 KPI cards, two
    # span-6 figures, one span-12 -- at 375/768/1440 (TR-10.12).
    "bs_cards": _spec(_FOUR, _K4, layout="bs"),
}
SERVED = ("bs_facet", "bs_filters_left", "grid_3x2_filters",
          "grid_filters_left", "auto_filters_left", "tabs_facet",
          "facet_linked", "bs_cards")


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
        mod = load_app(ap, "_resp_app_%d" % tag, draw=False)
        doc = Document()
        mod.make_document(doc)
    return doc


def _served_page(spec):
    """The served document's layout as a standalone page: the same Bokeh
    models the server sends, without its Python callbacks, which do not
    change a layout.  Rendered through the served template (WP-28 E14) so
    it declares the saved page's viewport meta, as a real ``bokeh serve``
    session does (``doc.template = _dash_served_template(_dash_new_nonce())``
    in the generated make_document)."""
    import logging
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    doc = _served_doc(spec)
    log = logging.getLogger("bokeh.embed.util")
    level = log.level
    log.setLevel(logging.ERROR)   # "real Python callbacks" in a file
    try:
        return file_html(doc, INLINE, "served",
                         template=dr._dash_served_template())
    finally:
        log.setLevel(level)


def _chrome():
    chrome = rp.find_chrome()
    if chrome is None:
        pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                    "the responsive measurement needs a browser")
    return chrome


#: bs_facet's xsize(10) graph: its box at 96 px an inch (WP-45 VF-4).
FIXED_W = 960


def _check(name, results):
    bad = []
    counts = {r["canvases"] for r in results.values()}
    for w in WIDTHS:
        r = results[w]
        if r["W"] != w:
            bad.append("%d: the iframe reported %r" % (w, r["W"]))
        if r["sw"] > w:
            bad.append("%d: the page is %d px wide" % (w, r["sw"]))
        # Flipped (WP-45 VF-4): bs_facet's xsize(10) ysize(2) graph was
        # stretched inside the 160-560 px band; twoway draws the exact box
        # (960 x 192 px at 96 px an inch, DECISIONS A-1), which keeps its
        # size in a narrower cell that scrolls sideways (the page does not:
        # "sw" above).  Only that box's layers may lie past the edge.
        past = [tuple(int(v) for v in p.rsplit(":", 1)[1].split("+"))
                for p in r.get("past", [])]
        box = [x for x, wd in past if wd == FIXED_W]
        inside = bool(box) and all(x + wd <= box[0] + FIXED_W
                                   for x, wd in past)
        if r["offscreen"] and (name.split()[-1] != "bs_facet"
                               or not inside):
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


@pytest.mark.release  # headless Chrome (WP-30 D)
class TestPagesFitInChrome:
    """The saved page of every layout family, at 375, 768 and 1440 px."""

    @pytest.mark.parametrize("name", sorted(FAMILIES))
    def test_saved_page_fits(self, name):
        chrome = _chrome()
        page = _saved_page(FAMILIES[name])
        _check(name, rp.measure_many(page, WIDTHS, chrome))


@pytest.mark.release  # headless Chrome (WP-30 D)
class TestServedDocumentsFitInChrome:
    """The served document's layout at the same widths (TR-27.2): its
    grids stack as the saved ones do.  The served page declares the saved
    page's viewport meta (WP-28 E14: rendered through
    ``_dash_served_template``), so a phone lays it out at this width
    rather than zooming out a 980px default; this is also the served app
    in a browser window of that width."""

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
        # A page with no policy gains the probe and nothing else.
        assert out == "<html><body>x" + rp.PROBE_JS + "</body></html>"

    def test_with_probe_admits_itself_under_both_policies(self):
        """WP-30 P1.29: a saved page runs only the scripts its policy names
        by hash, a served page only those carrying its nonce; the probe is
        admitted on the page copy under test, and nothing else changes."""
        import base64
        import hashlib
        body = rp.PROBE_JS.split(">", 1)[1].rsplit("</script>", 1)[0]
        digest = base64.b64encode(hashlib.sha256(
            body.encode("utf-8")).digest()).decode("ascii")
        saved = ("<html><head>" + dr._dash_saved_head([])
                 + "</head><body>x</body></html>")
        out = rp.with_probe(saved)
        assert ("script-src 'sha256-%s' 'unsafe-eval'" % digest) in out
        assert out.replace("'sha256-%s' " % digest, "", 1) == \
            saved.replace("</body>", rp.PROBE_JS + "</body>")
        n = "Nonce_-" * 4
        served = ("<html><head>" + dr._dash_csp_meta(dr._dash_csp_served(n))
                  + "</head><body>x</body></html>")
        out = rp.with_probe(served)
        assert '<script nonce="%s">' % n in out
        assert out.count("nonce-%s" % n) == 1
        assert "sha256" not in out

    def test_find_chrome_honours_only_an_executable(self, monkeypatch,
                                                    tmp_path):
        f = tmp_path / "not-chrome"
        f.write_text("")
        f.chmod(0o644)
        monkeypatch.setenv("DASH_CHROME", str(f))
        assert rp.find_chrome() != str(f)

    def test_chrome_starts_native_under_an_x86_64_parent(self, tmp_path):
        """WP-31 S60: below an x86_64 process (Intel Homebrew's bash or
        timeout in /usr/local/bin) a bare ``[chrome, ...]`` ran Chrome's
        x86_64 slice under Rosetta, 30-50 times slower, and the family
        probes passed their 90 s deadline with "the probe reported
        nothing".  chrome_argv starts the native slice."""
        chrome = _chrome()
        argv = rp.chrome_argv(chrome)
        if not rp._host_is_apple_silicon():
            assert argv == [chrome]
            return
        assert argv == ["/usr/bin/arch", "-arm64", chrome]
        if subprocess.run(["/usr/bin/arch", "-x86_64", "/usr/bin/true"],
                          capture_output=True).returncode:
            return   # no Rosetta: nothing can start the x86_64 slice
        page = tmp_path / "p.html"
        page.write_text("<html><body>native-probe</body></html>")
        prof = tmp_path / "prof"
        prof.mkdir()
        p = subprocess.run(
            ["/usr/bin/arch", "-x86_64", "/bin/sh", "-c", 'exec "$@"', "sh"]
            + argv + ["--headless=new", "--disable-gpu", "--no-first-run",
                      "--user-data-dir=%s" % prof, "--dump-dom",
                      "file://%s" % page],
            capture_output=True, text=True, timeout=180)
        assert "native-probe" in p.stdout, p.stderr[-500:]
        assert "Rosetta" not in p.stderr, p.stderr[:500]

    def test_chrome_argv_is_the_binary_off_apple_silicon(self, monkeypatch,
                                                         tmp_path):
        f = tmp_path / "chrome"
        f.write_text("")
        assert rp._native_slice(str(f)) is None
        monkeypatch.setattr(rp, "_NATIVE", {})
        monkeypatch.setattr(rp, "_host_is_apple_silicon", lambda: False)
        assert rp.chrome_argv(str(f)) == [str(f)]

    def test_cells_are_reported(self):
        """TR-10.12: a KPI card's cell is the nearest ancestor with a
        db-cell-h-* class, reported alongside the card itself."""
        chrome = _chrome()
        page = ("<html><body style='margin:0'>"
                "<div class='db-cell-h-md' "
                "style='width:220px;height:150px'>"
                "<div class='db-kpi-card' "
                "style='width:200px;height:80px'>x</div>"
                "</div></body></html>")
        r = rp.measure_many(page, (375,), chrome)[375]
        assert r["cells"] == [[220, 150, "db-cell-h-md"]]

    def test_a_card_with_no_cell_ancestor_reports_none(self):
        chrome = _chrome()
        page = ("<html><body style='margin:0'>"
                "<div class='db-kpi-card' "
                "style='width:200px;height:80px'>x</div>"
                "</body></html>")
        r = rp.measure_many(page, (375,), chrome)[375]
        assert r["cells"] == [[-1, -1, ""]]


# ---------------------------------------------------------------------------
# The model properties and CSS the fix sets (no browser)
# ---------------------------------------------------------------------------

def _css(model):
    return " ".join(getattr(s, "css", s) for s in model.stylesheets)


def _all_models(root, cls):
    return [m for m in root.references() if isinstance(m, cls)]


class TestTheServedPageCarriesTheSavedPagesHead:
    """WP-28 E14: the served page declares the saved page's viewport meta,
    after its Content-Security-Policy meta -- no Chrome needed; this is
    what lets the Chrome measurements below trust the served template."""

    def test_viewport_and_policy(self):
        page = _served_page(FAMILIES["bs_cards"])
        assert page.count(dr._DASH_VIEWPORT_META) == 1
        csp_at = page.lower().find('http-equiv="content-security-policy"')
        assert csp_at >= 0
        assert csp_at < page.index(dr._DASH_VIEWPORT_META)


@pytest.mark.release  # headless Chrome (WP-30 D)
class TestTheServedBsGridReflowsAsTheSavedOne:
    """WP-28 E14: between 768 and 991 px a served layout(bs) grid takes the
    saved page's half rows and KPI cell minimum heights.  The saved page's
    flex-wrap CSS gets this for free; the served GridBox gets one
    stylesheet (_dash_bs_grid_css) built from the same numbers.  Measured
    25sep2026 (dash_render.py Evidence item 4): a served span-3 KPI card
    went from four across at every width to two per line at 768, four
    across again at 1440, and one per line at 375 -- matching the saved
    page's card and canvas counts and widths at every one.

    Cell HEIGHT is a floor (min-height), not a fixed height, and the two
    pages' cards are not byte-identical DOM (a saved card sits inside an
    extra .db-col wrapper; a served card's own host element carries the
    class): measured, the served cell sits almost exactly at the floor
    (130/130/122 at 1440/768/375) while the saved one is a few pixels
    above it at 768/1440 (132) and further above it at 375 (132, where the
    card's own content -- not the floor -- decides the height).  Both
    still meet AC-10.4's floor (>= 130 from 768, >= 120 below it) in both
    modes, which is what is asserted; a byte-identical height is not.
    """

    @pytest.mark.parametrize("name", ["bs_cards", "bs_facet"])
    def test_cards_and_canvases_agree(self, name):
        chrome = _chrome()
        saved = rp.measure_many(_saved_page(FAMILIES[name]), WIDTHS, chrome)
        served = rp.measure_many(_served_page(FAMILIES[name]), WIDTHS,
                                 chrome)
        for w in WIDTHS:
            s, v = saved[w], served[w]
            assert s["kpis"] == v["kpis"], (w, "kpis", s["kpis"], v["kpis"])
            assert s["canvases"] == v["canvases"], (
                w, "canvases", s["canvases"], v["canvases"])
            s_widths = sorted(c[0] for c in s["cells"])
            v_widths = sorted(c[0] for c in v["cells"])
            assert len(s_widths) == len(v_widths) == s["kpis"]
            for a, b in zip(s_widths, v_widths):
                assert abs(a - b) <= 24, (w, s_widths, v_widths)
            for mode, cells in (("saved", s["cells"]), ("served", v["cells"])):
                for cw, ch, cls in cells:
                    frac = cw / w
                    if w == 1440:
                        assert frac < 0.30, (w, mode, cw)
                    elif w == 768:
                        assert 0.40 <= frac <= 0.60, (w, mode, cw)
                    else:
                        assert frac > 0.90, (w, mode, cw)
                    min_h = 130 if w >= 768 else 120
                    assert ch >= min_h, (w, mode, ch)
                    assert cls == "db-cell-h-sm", (w, mode, cls)


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
            render_models(r)
        for s in _all_models(r._last_layout_root, InlineStyleSheet):
            if "container-type" in s.css:
                assert "display:none" not in s.css


def _shares_the_width(cols):
    """Every column an equal share of the grid -- or, in a by() grid,
    every panel column, its axis-title, legend and key columns as wide as
    they hold and its stacking ruler's one pixel (WP-30 P1.15c)."""
    if cols == dr._DASH_BS_TRACK:
        return True
    return (isinstance(cols, list) and dr._DASH_BS_TRACK in cols
            and set(cols) <= {dr._DASH_BS_TRACK, "max-content", "1px"})


class TestEveryGridIsReflowed:
    """Every grid, the filter bar and the sidebar go through _dash_reflow,
    in both modes."""

    def _saved_root(self, spec):
        _, sp, dp = _write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        return r._last_layout_root

    @pytest.mark.parametrize("name", ["grid_3x2_filters", "tabs_facet",
                                      "facet_linked", "grid_filters_left"])
    def test_saved_grids(self, name):
        from bokeh.models import GridPlot, Row
        root = self._saved_root(FAMILIES[name])
        grids = _all_models(root, GridPlot)
        assert grids
        for g in grids:
            assert _shares_the_width(g.cols), g.cols
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
            assert _shares_the_width(g.cols), g.cols
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


class TestTheSidebarPassesBokehValidation:
    """BUGS.md "filterposition(left) under layout(auto) makes Bokeh print a
    W-1005 validation warning on every build".  The sidebar was
    ``column(..., sizing_mode="fixed", width=240)`` with no height, which
    Bokeh's validator reports on every build (W-1005 FIXED_SIZING_MODE,
    measured 24sep2026 through `dash build, filter(foreign)
    filterposition(left)').  The sidebar keeps its fixed 240 px width and
    the height of its widgets -- the drawing -- with no sizing mode that
    asks for a height it does not have.  The Chrome families
    ``auto_filters_left`` and ``grid_filters_left`` measure the page."""

    def _roots(self, mode, name):
        if mode == "saved":
            _, sp, dp = _write(FAMILIES[name])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = dr.DashRenderer(sp, dp)
                render_models(r)
            return [r._last_layout_root]
        return list(_served_doc(FAMILIES[name]).roots)

    @pytest.mark.parametrize("mode", ("saved", "served"))
    @pytest.mark.parametrize("name", ("auto_filters_left",
                                      "grid_filters_left"))
    def test_no_validation_warning(self, mode, name):
        from bokeh.core.validation import check_integrity
        models = set()
        for root in self._roots(mode, name):
            models |= set(root.references())
        issues = check_integrity(models)
        codes = sorted("%s-%d %s" % ("W", w.code, w.name)
                       for w in issues.warning) + sorted(
            "E-%d %s" % (e.code, e.name) for e in issues.error)
        assert codes == [], codes

    def test_the_saved_build_logs_nothing(self):
        """What the user saw: Bokeh's validator writes to the log when the
        page is written."""
        import logging
        seen = []

        class _H(logging.Handler):
            def emit(self, record):
                seen.append(record.getMessage())

        log = logging.getLogger("bokeh.core.validation.check")
        h = _H()
        log.addHandler(h)
        try:
            _saved_page(FAMILIES["auto_filters_left"])
        finally:
            log.removeHandler(h)
        assert not [m for m in seen if "W-1005" in m], seen

    def test_the_guard_sees_w1005(self):
        """Control: the check above reports a fixed column with no height."""
        from bokeh.core.validation import check_integrity
        from bokeh.layouts import column
        from bokeh.models import Div
        bad = column(Div(text="x"), sizing_mode="fixed", width=240)
        issues = check_integrity(set(bad.references()))
        assert [w.code for w in issues.warning] == [1005]

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_the_sidebar_keeps_its_fixed_width(self, mode):
        from bokeh.models import Column
        cols = [m for root in self._roots(mode, "auto_filters_left")
                for m in root.references() if isinstance(m, Column)
                and m.width == dr._SIDEBAR_WIDTH_PX]
        assert len(cols) == 1, cols
        side = cols[0]
        assert side.width_policy == "fixed"
        assert side.sizing_mode is None
        assert side.height is None and side.height_policy in ("auto", "fit")


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
