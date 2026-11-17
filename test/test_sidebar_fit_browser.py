"""
test_sidebar_fit_browser.py -- under layout(bs) and filterposition(left)
nothing a filter widget draws reaches past the sidebar's right edge
(test_sidebar_fit.py has the models; this reads the boxes).

At 1068 px, the user's guide's frame width, the sidebar column is about
180 px wide; the range and slider filters drew to 316 px, under the
first graph (17nov2026).  At a phone's width the sidebar takes the
page's width and the widgets take it with it.

Read in headless Chrome over CDP.  Without Chrome these tests skip.
"""
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

import dash_render as dr  # noqa: E402
from scripts.corpus import dash_run  # noqa: E402
from test_adversarial_matrix import _write_inputs  # noqa: E402
from test_served_bs_layout import _spec  # noqa: E402
from test_sidebar_fit import FILTERS  # noqa: E402

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: The sidebar's right edge and its padding, and the right edge of the
#: furthest box any sidebar item draws (through shadow roots).
_FIT_JS = r"""(() => {
  const col = document.querySelector(".db-sidebar-col");
  if (col == null) { return null; }
  const edge = col.getBoundingClientRect().right;
  const pad = parseFloat(getComputedStyle(col).paddingRight) || 0;
  let reach = -1;
  const walk = (root) => {
    for (const el of root.querySelectorAll("*")) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) { reach = Math.max(reach, r.right); }
      if (el.shadowRoot) { walk(el.shadowRoot); }
    }
  };
  const items = col.querySelectorAll(".db-sidebar-item");
  for (const it of items) { walk(it); }
  return {edge: edge, pad: pad, reach: reach, items: items.length};
})()"""

_SETTLE_JS = "new Promise(r => setTimeout(r, 1500))"


@pytest.mark.parametrize("width", (1068, 375))
def test_the_sidebar_holds_its_widgets(width, tmp_path):
    spec = _spec(["g1", "g2"], layout="bs: g1=6 g2=6", filter=FILTERS,
                 filter_position="left")
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        html = dr.DashRenderer(sp, dp).render()
    page = tmp_path / "sidebar.html"
    page.write_text(html, encoding="utf-8")
    blank = tmp_path / "blank.html"
    blank.write_text("<html><body></body></html>", encoding="utf-8")
    probe = dash_run.CorpusProbe(
        str(blank), timeout=300,
        ready="document.readyState === 'complete'").__enter__()
    try:
        probe.viewport(width, 900)
        probe.navigate(str(page))
        probe.eval_async(_SETTLE_JS)
        got = probe._eval(_FIT_JS)
        errors = probe.js_errors()
    finally:
        probe.__exit__(None, None, None)
    assert errors == []
    assert got is not None and got["items"] >= 4, got
    assert got["reach"] <= got["edge"] + 0.5, got
    # The widgets fill the column to its padding.
    assert got["reach"] >= got["edge"] - got["pad"] - 2, got
