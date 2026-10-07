"""
test_key_text_chrome.py -- the colour key's tick texts as the browser
draws them (WP-30 P1.23b).

A ColorBar's ``major_label_overrides`` is a map keyed by the tick's float
position; BokehJS writes a tick's override only when the key equals the
tick exactly, else it falls back to its own text.  The deserialized map is
read from the saved page in headless Chrome (``range_probe.RangeProbe``)
and each FixedTicker tick looked up in it.  Without Chrome these tests
skip, as test_by_scales_chrome.py's do (a skip is not a pass).
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import range_probe  # noqa: E402
import responsive_probe  # noqa: E402
import dash_render as dr  # noqa: E402
import test_date_axis_residuals as tdr  # noqa: E402
from test_date_range import _spec, _write  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the colour key's texts are not measured",
                allow_module_level=True)

#: Headless Chrome: the release tier, not the default run (WP-30 D).
pytestmark = pytest.mark.release

_KEY_TEXTS_JS = """(() => {
  const doc = Bokeh.documents[0];
  const bars = [...doc.all_models].filter(
      m => m.constructor.__name__ === "ColorBar");
  if (bars.length !== 1) { return JSON.stringify(["bars", bars.length]); }
  const cb = bars[0];
  const ticks = cb.ticker.ticks;
  if (!ticks) { return JSON.stringify(["no fixed ticks"]); }
  const ov = cb.major_label_overrides;
  return JSON.stringify(ticks.map(t => ov.get(t)));
})()"""


class TestTheKeyTextReachesThePage:

    def test_the_page_maps_each_tick_to_its_text(self, tmp_path):
        sp, dp = _write(tmp_path, _spec([tdr._sc("date")]), tdr._KEY)
        page = os.path.join(str(tmp_path), "o.html")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(sp, dp, page).render()
        if not os.path.exists(page):
            with open(page, "w", encoding="utf-8") as fh:
                fh.write(html)
        with range_probe.RangeProbe(page) as p:
            got = json.loads(p._eval(_KEY_TEXTS_JS))
            assert got == ["15,000", "15,100", "15,200", "15,300", "15,400"]
            assert p.js_errors() == []
