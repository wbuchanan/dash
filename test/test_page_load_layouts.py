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
      if (this.parent == null) window.__dashRootLayouts++;
      return orig.apply(this, a);
    };
  } catch (e) { window.__dashCountErr = String(e); }
}, {capture: true});
"""

_SETTLE_JS = "new Promise(r => setTimeout(r, 1500))"


def _root_layouts(mode, n, tmp_path):
    """Whole-page layouts while a page of *n* scatter graphs loads."""
    spec = bk._spec([bk._graph("g%d" % i, bk._ONE, {}) for i in range(n)])
    page = tmp_path / ("%s_%d.html" % (mode, n))
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
def test_layouts_do_not_grow_with_the_graph_count(mode, tmp_path):
    """Two graphs and sixteen are laid out about as often: at most two
    layouts more for the larger page, and fewer layouts than graphs."""
    few = _root_layouts(mode, 2, tmp_path)
    many = _root_layouts(mode, 16, tmp_path)
    assert many >= 1, many
    assert many <= few + 2 and many < 16, (few, many)
