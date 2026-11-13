"""
test_page_load_layouts.py -- a page of many graphs is laid out a number of
times that does not grow with its graph count (WP-50 WE.7, BUGS.md "A page
of many graphs takes minutes to load").

Each graph's width-scale callback (D66) and figure-margin callback asked
BokehJS to lay its plot out again, one ``setTimeout`` each.  A plot's
``invalidate_layout`` climbs to the root and lays out the whole page, so a
page of n graphs was laid out about 1.7 n times, each layout costing O(n):
the gallery's scatter page (124 examples) did not load in 34 minutes, its
line page (28) took 15 s, where Bokeh alone lays out an 80-row gridplot
once.  The requests now go through one queue (``_DASH_RELAYOUT_JS``) that
lays each root out once per tick.

Read in headless Chrome over CDP: a script added before the page counts
``LayoutDOMView.compute_layout`` on a view with no parent (a whole-page
layout) until the page has settled.  Without Chrome these tests skip.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_axes_keys_browser as bkb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

from scripts.corpus import dash_run  # noqa: E402

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: Added before the page's own scripts (CDP, so the page's CSP does not
#: apply): counts whole-page layouts from the first one on.
_COUNT_JS = r"""
window.__dashRootLayouts = 0; window.__dashCountErr = null;
document.addEventListener("DOMContentLoaded", () => {
  try {
    const L = Bokeh.require("models/layouts/layout_dom").LayoutDOMView;
    const orig = L.prototype.compute_layout;
    L.prototype.compute_layout = function (...a) {
      // A page root only (Bokeh.index): a plot's own layout of its
      // panels, at no cost to the page, has no parent either.
      if (this.parent == null && Bokeh.index != null
          && Object.values(Bokeh.index).includes(this)) {
        window.__dashRootLayouts++;
      }
      return orig.apply(this, a);
    };
  } catch (e) { window.__dashCountErr = String(e); }
}, {capture: true});
"""

_SETTLE_JS = "new Promise(r => setTimeout(r, 1500))"


def _root_layouts(mode, n, tmp_path, go=None):
    """Whole-page layouts while a page of *n* scatter graphs, each with
    the graph options *go*, loads."""
    spec = bk._spec([bk._graph("g%d" % i, bk._ONE, dict(go or {}))
                     for i in range(n)])
    page = tmp_path / ("%s_%d_%d.html" % (mode, n, bool(go)))
    page.write_text(bkb._page(mode, spec), encoding="utf-8")
    blank = tmp_path / "blank.html"
    blank.write_text("<html><body></body></html>", encoding="utf-8")
    probe = dash_run.CorpusProbe(
        str(blank), timeout=300,
        ready="document.readyState === 'complete'").__enter__()
    try:
        probe._send("Page.addScriptToEvaluateOnNewDocument",
                    {"source": _COUNT_JS})
        probe.navigate(str(page))
        probe.eval_async(_SETTLE_JS)
        assert probe._eval("window.__dashCountErr") is None
        return probe._eval("window.__dashRootLayouts")
    finally:
        probe.__exit__(None, None, None)


@pytest.mark.parametrize("mode", ("saved", "served"))
@pytest.mark.parametrize("go", ({}, {"by": "foreign"}), ids=("plain", "by"))
def test_layouts_do_not_grow_with_the_graph_count(mode, go, tmp_path):
    """Two graphs and sixteen are laid out about as often: at most two
    layouts more for the larger page, and fewer layouts than graphs.
    Under by() each graph's fit, span, key and stacked-view callbacks
    set every panel's proportion, box and visibility, and each set laid
    the page out at once (BokehJS lays a model out on a change of a
    layout property): those sets go through the queue as well
    (``dash_batch``).  A by() graph's width scale still lays its spacing
    out as it sets it, which the fit and the spans read
    (test_legend_span_browser.py), so a by() page keeps one layout per
    graph: 20 for sixteen graphs, where it was 225 (14 per graph)."""
    few = _root_layouts(mode, 2, tmp_path, go)
    many = _root_layouts(mode, 16, tmp_path, go)
    assert many >= 1, many
    if go:
        assert many <= few + 16, (few, many)
    else:
        assert many <= few + 2 and many < 16, (few, many)


#: Counts each axis's setv calls (one per change event) while the page
#: loads.
_SETV_JS = r"""
window.__dashAxisSets = {}; window.__dashCountErr = null;
document.addEventListener("DOMContentLoaded", () => {
  try {
    const H = Bokeh.require("core/has_props").HasProps;
    const orig = H.prototype.setv;
    H.prototype.setv = function (attrs, opts) {
      if (this.type === "LinearAxis") {
        window.__dashAxisSets[this.id] = (window.__dashAxisSets[this.id] || 0) + 1;
      }
      return orig.call(this, attrs, opts);
    };
  } catch (e) { window.__dashCountErr = String(e); }
}, {capture: true});
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_the_width_scale_sets_each_model_once(mode, tmp_path):
    """The width scale (D66) sets a model's scaled values together, one
    change event per model: set one by one, each value of a marker
    label set re-rendered it and made the browser work out the page's
    styles again (the gallery's scatter page, 11,174 sets on 2,761
    models).  An axis's eleven scaled values reach it in one setv, where
    they took five."""
    spec = bk._spec([bk._graph("g%d" % i, bk._ONE, {}) for i in range(2)])
    page = tmp_path / ("%s_setv.html" % mode)
    page.write_text(bkb._page(mode, spec), encoding="utf-8")
    blank = tmp_path / "blank.html"
    blank.write_text("<html><body></body></html>", encoding="utf-8")
    probe = dash_run.CorpusProbe(
        str(blank), timeout=300,
        ready="document.readyState === 'complete'").__enter__()
    try:
        probe._send("Page.addScriptToEvaluateOnNewDocument",
                    {"source": _SETV_JS})
        probe.navigate(str(page))
        probe.eval_async(_SETTLE_JS)
        assert probe._eval("window.__dashCountErr") is None
        sets = probe._eval("window.__dashAxisSets")
    finally:
        probe.__exit__(None, None, None)
    assert sets and max(sets.values()) == 1, sets


#: Counts the CSS reads of BokehJS's visual overrides (``--bk-<visual>``):
#: getComputedStyle(...).getPropertyValue("--bk-...").
_BK_READS_JS = r"""
window.__dashBkReads = 0;
const dashOwnGet = CSSStyleDeclaration.prototype.getPropertyValue;
CSSStyleDeclaration.prototype.getPropertyValue = function (name) {
  if (typeof name === "string" && name.startsWith("--bk-")) {
    window.__dashBkReads++;
  }
  return dashOwnGet.call(this, name);
};
"""

_REPAINT_JS = r"""new Promise((resolve) => {
  window.__dashBkReads = 0;
  for (const v of Object.values(Bokeh.index)) {
    if (typeof v.invalidate_layout === "function") { v.invalidate_layout(); }
  }
  setTimeout(() => requestAnimationFrame(() => requestAnimationFrame(
    () => resolve(window.__dashBkReads))), 100);
})"""


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_a_repaint_reads_no_visual_override_from_css(mode, tmp_path):
    """BokehJS reads every colour, alpha and width it draws from the
    element's computed style first (``--bk-line-color`` and the like),
    which makes the browser work out the page's styles again whenever
    the page has changed: 29 of the gallery scatter page's 49 s.  A dash
    page defines no such property (test_no_page_defines_a_visual_override),
    so once the page's callbacks have run, a layout and paint read none."""
    spec = bk._spec([bk._graph("g%d" % i, bk._ONE, {}) for i in range(2)])
    page = tmp_path / ("%s_bk.html" % mode)
    page.write_text(bkb._page(mode, spec), encoding="utf-8")
    blank = tmp_path / "blank.html"
    blank.write_text("<html><body></body></html>", encoding="utf-8")
    probe = dash_run.CorpusProbe(
        str(blank), timeout=300,
        ready="document.readyState === 'complete'").__enter__()
    try:
        probe._send("Page.addScriptToEvaluateOnNewDocument",
                    {"source": _BK_READS_JS})
        probe.navigate(str(page))
        probe.eval_async(_SETTLE_JS)
        reads = probe.eval_async(_REPAINT_JS)
    finally:
        probe.__exit__(None, None, None)
    assert reads == 0, reads


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_no_page_defines_a_visual_override(mode):
    """What makes answering those reads with "" sound: neither dash's
    styles nor BokehJS's own stylesheets on the page define a
    ``--bk-...`` property (BokehJS's bundle names the prefix only, in
    the template its visuals build their names from)."""
    import re
    spec = bk._spec([bk._graph("g0", bk._ONE, {"legend": "on",
                                               "title": '"T"'})])
    html = bkb._page(mode, spec)
    defined = re.findall(r"--bk-[A-Za-z0-9_-]+\s*:", html)
    assert defined == [], defined
