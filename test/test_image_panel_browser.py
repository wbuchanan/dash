"""test_image_panel_browser.py -- an image panel under the saved page's
Content-Security-Policy, in headless Chrome (WP-33 33-06).

The panel is an ``<img src="data:image/svg+xml;base64,...">`` inside a
Bokeh Div; the saved policy already allows ``img-src data:``, so the
picture loads with no violation.  Release tier, as test_csp_browser.py.
"""
import json
import os
import sys
import tempfile
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "a skip is red under DASH_STRICT=1", allow_module_level=True)

pytestmark = pytest.mark.release

from bokeh.io import curdoc  # noqa: E402

import dash_render as dr  # noqa: E402
from test_csp_browser import _CspProbe, _frame, _graph, _scatter, _url  # noqa: E402,E501
from conftest import make_data_json  # noqa: E402

_SMOKE = os.path.join(_HERE, "fixtures", "svg_truth_smoke.svg")

_IMG_JS = r"""
JSON.stringify((() => {
  const out = [];
  const walk = (root) => {
    for (const el of root.querySelectorAll('*')) {
      if (el.shadowRoot) walk(el.shadowRoot);
    }
    for (const f of root.querySelectorAll('figure.dash-image')) {
      const img = f.querySelector('img');
      const cap = f.querySelector('figcaption');
      out.push([img ? img.naturalWidth : -1, img ? img.complete : false,
                cap ? cap.textContent : null]);
    }
  };
  walk(document);
  return out;
})())
"""


def _page(tmp):
    spec = {"graphs": [_graph("g1", [_scatter()])], "kpis": [],
            "images": [{"name": "im1", "path": _SMOKE,
                        "caption": "Twoway's <picture>", "alt": "twoway",
                        "link": "scatter.html"}],
            "build_options": {"layout": "1 2", "link": "", "theme": "",
                              "title": "", "subtitle": "", "filter": "",
                              "registry": "g1 im1"}}
    sp, dp = os.path.join(tmp, "spec.json"), os.path.join(tmp, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame()), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            page = dr.DashRenderer(sp, dp).render()
        finally:
            curdoc().clear()
    path = os.path.join(tmp, "page.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path


class TestInChrome:

    def test_the_image_loads_with_no_violation(self):
        with tempfile.TemporaryDirectory(prefix="dash_img_csp_") as tmp:
            with _CspProbe(_url(_page(tmp))) as p:
                end = time.time() + 15
                got = p.read(_IMG_JS)
                while not (got and got[0][0] > 0) and time.time() < end:
                    time.sleep(0.2)
                    got = p.read(_IMG_JS)
                assert p.violations() == [], p.violations()
                assert p.js_errors() == [], p.js_errors()
                assert len(got) == 1, got
                width, complete, caption = got[0]
                assert complete and width > 0, got
                assert caption == "Twoway's <picture>", got
