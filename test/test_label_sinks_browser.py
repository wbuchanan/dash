"""The text sinks in a real browser, for the installed bokeh (WP-30 P1.30,
BR-41.4).

test_label_sinks.py holds that a variable label reaches BokehJS as text;
whether BokehJS then draws it as text is BokehJS's, so it is checked here
in headless Chrome for whichever bokeh this run has -- under both
baselines, so for every minor of the verified window (``VERIFIED_ON`` in
test_label_sinks.py records each).  ``y`` is labelled with an HTML payload;
a point is hovered; the tooltip must show the literal text, no IMG element
may exist anywhere (shadow roots included) and ``document.title`` must not
change.  Saved page and ``python app.py``.

Chrome is ``responsive_probe.find_chrome()``'s; without it the module skips,
and a skip is red under ``DASH_STRICT=1``.
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
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
from conftest import make_data_json, make_spec  # noqa: E402
from test_csp_browser import _CspProbe, _POINT_JS, _TOOLTIP_JS  # noqa: E402
from test_server_serves import _Launched  # noqa: E402

PAYLOAD = "<img src=x onerror=\"document.title='PWNED'\">Y label"

#: Every IMG element in the document, shadow roots included.
_IMGS_JS = r"""
(() => {
  let n = 0;
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'IMG') n += 1; } };
  walk(document);
  return n;
})()
"""


def _files():
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 12),
                       "weight": np.linspace(1760.0, 4840.0, 12)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    d = tempfile.mkdtemp(prefix="dash_sinks_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, variable_labels={"mpg": PAYLOAD}), fh)
    return d, sp, dp


class TestTheTextSinksInChrome:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_label_stays_text(self, mode):
        d, sp, dp = _files()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                try:
                    page = dr.DashRenderer(sp, dp).render()
                finally:
                    curdoc().clear()
                path = os.path.join(d, "page.html")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(page)
            else:
                path = os.path.join(d, "app.py")
                dr.ServerAppBuilder(sp, dp).build(path)
        if mode == "saved":
            self._check("file://" + path)
        else:
            with _Launched(path) as srv:
                self._check(srv.url("/"))

    @staticmethod
    def _check(url):
        with _CspProbe(url) as p:
            title = p._eval("document.title")
            x, y = p.read(_POINT_JS)
            p._send("Input.dispatchMouseEvent",
                    {"type": "mouseMoved", "x": x, "y": y})
            tips = p.wait_change(_TOOLTIP_JS, [], timeout=10)
            assert tips and PAYLOAD in tips[0], tips
            assert p._eval(_IMGS_JS) == 0
            assert p._eval("document.title") == title != "PWNED"
