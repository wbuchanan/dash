"""test_webgl_backend_browser.py -- a dashed line drawn with WebGL actually
on (WP-36 DG-14, release tier).

Bokeh's WebGL line shader breaks dashed and dotted lines up (research [B]
section 4.7: on SwiftShader, ink IoU against the canvas drawing of 0.57-0.86
for dashed lines at 20,000 vertices).  Every other browser probe passes
``--disable-gpu``, which turns WebGL off completely, so none of them could
show it.  This probe adds ``--enable-unsafe-swiftshader`` (Chrome's software
WebGL), shows WebGL is on, and pins that a dashed line above the threshold
is drawn on canvas: its ink matches a reference page of the same spec built
with the threshold out of reach.

Ink is [B]'s rule: a pixel of the figure's own PNG export
(``export('png').canvas``) with alpha > 0 and red < 128, read inside the
plot frame, where only the line draws dark.
"""
import json
import os
import sys
import tempfile
import warnings
from unittest import mock

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "a skip is red under DASH_STRICT=1", allow_module_level=True)

#: Headless Chrome: the release tier, not the default run.
pytestmark = pytest.mark.release

from bokeh.io import curdoc  # noqa: E402

import dash_render as dr  # noqa: E402
import test_csp_browser  # noqa: E402
from test_webgl_backend import _data, _graph, _plot, _spec  # noqa: E402


class _GlProbe(test_csp_browser._CspProbe):
    """A page probe with WebGL on: SwiftShader instead of no GPU at all."""
    CHROME_GPU_FLAGS = ("--disable-gpu", "--enable-unsafe-swiftshader")


#: The page's one figure, its view and whether that view draws with WebGL.
_FIG_JS = r"""
const __dash_fig = () => {
  for (const d of Bokeh.documents) {
    for (const m of d.all_models) {
      if (m && m.output_backend !== undefined && m.renderers !== undefined
          && m.toolbar !== undefined
          && !String(m.name || "").startsWith("dash_by_")) {
        return Bokeh.index.find_one(m);
      }
    }
  }
  return null;
};
"""

#: [backend, webgl on, frame-ink bitmap as a string of 0/1] of the figure.
_INK_JS = _FIG_JS + r"""
(() => {
  const v = __dash_fig();
  const cv = v.export('png').canvas;
  const k = cv.width / v.bbox.width;
  const f = v.frame.bbox;
  const x0 = Math.ceil(f.left * k) + 2, y0 = Math.ceil(f.top * k) + 2;
  const w = Math.floor(f.width * k) - 4, h = Math.floor(f.height * k) - 4;
  const px = cv.getContext('2d').getImageData(x0, y0, w, h).data;
  let bits = '';
  for (let i = 0; i < px.length; i += 4) {
    bits += (px[i + 3] > 0 && px[i] < 128) ? '1' : '0';
  }
  return JSON.stringify([v.model.output_backend,
                         v.canvas_view.webgl != null, w, h, bits]);
})()
"""


def _page(spec, data, threshold=None):
    """The saved page of *spec* over *data*, with ``_WEBGL_THRESHOLD`` at
    *threshold* when given; its path."""
    d = tempfile.mkdtemp(prefix="dash_webgl_page_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    out = os.path.join(d, "page.html")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            if threshold is None:
                page = dr.DashRenderer(sp, dp).render()
            else:
                with mock.patch.object(dr, "_WEBGL_THRESHOLD", threshold):
                    page = dr.DashRenderer(sp, dp).render()
        finally:
            curdoc().clear()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    return out


def _ink(path):
    with _GlProbe("file://" + path) as p:
        return json.loads(p._eval(_INK_JS))


def _iou(a, b):
    both = sum(1 for x, y in zip(a, b) if x == "1" and y == "1")
    either = sum(1 for x, y in zip(a, b) if x == "1" or y == "1")
    return both / either if either else 1.0


class TestWebglPixels:

    def test_webgl_is_on_in_the_probe(self):
        """A 20,000-row solid scatter: the figure is WebGL and its canvas
        view holds a WebGL context -- without it the next test could not
        fail."""
        page = _page(_spec([_graph("g1", [_plot("scatter")])]), _data())
        backend, gl, *_ = _ink(page)
        assert backend == "webgl"
        assert gl is True

    def test_a_dashed_line_matches_a_canvas_reference(self):
        """``line y x, lpattern(dash) lwidth(thick)`` on 20,000 rows is drawn
        on canvas, and its ink matches the same spec drawn on canvas by
        construction (IoU >= 0.95; canvas against canvas is 1.0, WebGL's
        best dashed case [B] measured 0.86)."""
        spec = _spec([_graph("g1", [_plot("line", lpattern="dash",
                                          lwidth="thick")])])
        data = _data()
        got = _ink(_page(spec, data))
        ref = _ink(_page(spec, data, threshold=10 ** 9))
        assert ref[0] == "canvas" and ref[1] is False
        assert got[2:4] == ref[2:4]
        assert ref[4].count("1") > 1000
        iou = _iou(got[4], ref[4])
        assert iou >= 0.95, \
            "drawn %s, ink IoU %.3f against canvas" % (got[0], iou)
        assert (got[0], got[1]) == ("canvas", False)
