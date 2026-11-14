"""test_gallery_panels_browser.py -- a gallery page's panels in headless Chrome.

A gallery page sets each example's twoway picture beside the graph dash
draws for the same command.  scripts/corpus/gallery.panel_page puts each
side in a panel: "Stata on twoway" or "Stata on dash" above, the command
below, dash's panel shaded.  Here the panelled page is loaded under its
Content-Security-Policy: no error, no violation, the label above and the
command below each picture, and twoway's picture and dash's graph region
the same size.  Release tier, as test_image_panel_browser.py.
"""
import os
import sys
import tempfile
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "a skip is red under DASH_STRICT=1", allow_module_level=True)

pytestmark = pytest.mark.release

from scripts.corpus import gallery  # noqa: E402
from test_corpus_gallery import _panel_rows, gallery_page_html  # noqa: E402
from test_csp_browser import _CspProbe, _url  # noqa: E402

_PANELS_JS = r"""
JSON.stringify((() => {
  const rect = (el) => { const b = el.getBoundingClientRect();
                         return [b.left, b.top, b.width, b.height]; };
  const txt = (el) => { const box = el.shadowRoot && el.shadowRoot.querySelector('.bk-clearfix');
                        return box ? box.innerText.trim() : null; };
  const out = [];
  const walk = (v) => {
    if (!v) return;
    const name = v.model && v.model.name;
    if (typeof name === 'string' && name.startsWith('gallery-panel-')) {
      const kids = v.child_views || [];
      const inner = kids[1] ? kids[1].el : null;
      const img = inner && inner.shadowRoot ? inner.shadowRoot.querySelector('img') : null;
      out.push({side: name.slice('gallery-panel-'.length), panel: rect(v.el),
                label: kids[0] ? [txt(kids[0].el), rect(kids[0].el)]
                               : null,
                inner: inner ? rect(img && img.complete ? img : inner) : null,
                img: !!img,
                cmd: kids[2] ? [txt(kids[2].el), rect(kids[2].el)]
                             : null});
      return;
    }
    for (const c of (v.child_views || [])) walk(c);
  };
  for (const v of Object.values(Bokeh.index)) walk(v);
  return out;
})())
"""


def _panelled(tmp):
    rows, kinds = _panel_rows()
    path = os.path.join(tmp, "scatter.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(gallery_page_html(rows, kinds))
    assert gallery.panel_page(path, rows, kinds) == 6
    return path, rows, kinds


class TestInChrome:

    @pytest.mark.parametrize("width", [1400, 2000])
    def test_labels_commands_and_equal_sizes(self, width):
        """On a window narrower than twoway's picture (720 px a cell) and on
        one wider, where the picture once stopped at its own width."""
        with tempfile.TemporaryDirectory(prefix="dash_gallery_panels_") as tmp:
            path, rows, kinds = _panelled(tmp)
            with _CspProbe(_url(path)) as p:
                p._send("Emulation.setDeviceMetricsOverride",
                        {"width": width, "height": 1000, "deviceScaleFactor": 1,
                         "mobile": False})
                end = time.time() + 20
                got = p.read(_PANELS_JS)
                while not (len(got) == 6 and all(g["inner"] and g["inner"][2] > 100
                                                  for g in got)) and time.time() < end:
                    time.sleep(0.25)
                    got = p.read(_PANELS_JS)
                time.sleep(1.0)  # the graphs' late layouts
                got = p.read(_PANELS_JS)
                assert p.violations() == [], p.violations()
                assert p.js_errors() == [], p.js_errors()
        assert [g["side"] for g in got] == ["twoway", "dash"] * 3, got
        for k, row in enumerate(rows):
            tw, da = got[2 * k], got[2 * k + 1]
            for g in (tw, da):
                label, cmd, note = gallery.panel_texts(row, g["side"], kinds[row["id"]])
                assert g["label"][0] == label, g
                assert g["cmd"][0] == cmd, g
                (lx, ly, lw, lh), (ix, iy, iw, ih) = g["label"][1], g["inner"]
                cy = g["cmd"][1][1]
                assert ly + lh <= iy + 1 and iy + ih <= cy + 1, g
            # Side by side, the same width and height (2%); a refused row has
            # no dash graph to compare.
            assert abs(tw["panel"][2] - da["panel"][2]) <= 1, (tw, da)
            if kinds[row["id"]] != "refused":
                assert tw["img"], tw
                # The frames are the same height: an inline <img> left a
                # line's descent (about 5 px) below twoway's picture.
                assert abs(tw["panel"][3] - da["panel"][3]) <= 1, (row["id"], tw, da)
                for i in (2, 3):
                    assert abs(tw["inner"][i] - da["inner"][i]) <= 0.02 * tw["inner"][i], \
                        (row["id"], tw["inner"], da["inner"])
