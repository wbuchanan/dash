"""
test_legend_keys_browser.py -- the legend's keys laid out in a browser as
twoway lays them out (WP-43 LT-21, ruling D69).

textfirst and stacked lay each key out with the Legend's own stylesheet
(``_dash_legend_key_order``), so only the browser shows them.  Headless Chrome draws both modes' pages and reads each key's
canvas -- the bounding box of its drawn pixels -- and the boxes of its
canvas and its text, against twoway's measured facts
(legend_keys_truth.json), each in text sizes of its own legend so the
page's width scale drops out.  Without Chrome these tests skip.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_axes_keys_browser as kb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

_TRUTH = json.load(open(os.path.join(_HERE, "fixtures",
                                     "legend_keys_truth.json")))

#: Each series legend's keys: the canvas box, the drawn pixels' box in
#: the canvas (CSS px, null when blank), the text's box and its font
#: size, per legend in page order; and every CSP violation.
_KEYS_JS = r"""
<script>
document.addEventListener('securitypolicyviolation', (e) => {
  (window.__v = window.__v || []).push(e.violatedDirective); });
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const R = (r) => [r.left, r.top, r.right, r.bottom];
  const ink = (c) => {
    const x = c.getContext('2d');
    const W = c.width, H = c.height;
    if (!W || !H) return null;
    const d = x.getImageData(0, 0, W, H).data;
    let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let yy = 0; yy < H; yy++) for (let xx = 0; xx < W; xx++) {
      if (d[(yy * W + xx) * 4 + 3] > 60) {
        if (xx < x0) x0 = xx; if (xx > x1) x1 = xx;
        if (yy < y0) y0 = yy; if (yy > y1) y1 = yy; } }
    const k = c.getBoundingClientRect().width / W;
    return x1 < 0 ? null : [x0 * k, y0 * k, (x1 + 1) * k, (y1 + 1) * k];
  };
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.type !== 'Legend' || !m.visible || !rv.grid_el) continue;
        if (m.name === 'dash_colorvar_legend') continue;
        const items = [...rv.grid_el.children].map(e => {
          const lab = e.querySelector('.bk-label');
          const cv = e.querySelector('canvas');
          const rg = document.createRange(); rg.selectNodeContents(lab);
          return {canvas: R(cv.getBoundingClientRect()), ink: ink(cv),
                  text: R(rg.getBoundingClientRect()),
                  fs: parseFloat(getComputedStyle(lab).fontSize)};
        });
        out.push({items});
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  const roots = (typeof Bokeh.index[Symbol.iterator] === 'function')
    ? [...Bokeh.index] : Object.values(Bokeh.index);
  roots.forEach(visit);
  parent.postMessage('DASHPROBE' + JSON.stringify(
    {W: innerWidth, out, V: window.__v || []}), '*');
}, 3000));
</script>
"""


def _legends(mode, graphs, scheme="s2color"):
    """``(legends, violations)`` of one page holding *graphs*: each a
    ``(plots, legend)`` pair."""
    spec = bk._spec([bk._graph("g%d" % i, plots, {"legend": lg},
                               title=False)
                     for i, (plots, lg) in enumerate(graphs)],
                    scheme=scheme)
    got = kb._measure(mode, spec, _KEYS_JS)[1400]
    return got["out"], got["V"]


def _sc(y="mpg", **o):
    return bk._p("scatter", y=y, **o)


def _ln(y="headroom", **o):
    return bk._p("line", y=y, **o)


def _twoway_keys(case):
    """twoway's keys of fixture *case*: ``[(key extent, text start or
    end, text size), ...]`` in SVG units, from its legend's circles,
    lines and texts below the plot region."""
    row = _TRUTH[case]
    pb = row["plot"]["bottom"]
    marks, texts = [], []
    for e in row["els"]:
        a = e["a"]
        if e["tag"] == "circle" and float(a["cy"]) > pb:
            if "fill:none" in a.get("style", ""):
                continue
            r, cx = float(a["r"]), float(a["cx"])
            marks.append((cx - r, cx + r, float(a["cy"])))
        elif e["tag"] == "line" and "y1" in a and float(a["y1"]) > pb \
                and a["y1"] == a["y2"]:
            marks.append((float(a["x1"]), float(a["x2"]), float(a["y1"])))
        elif e["tag"] == "text" and float(a["y"]) > pb:
            fs = float(a["style"].split("font-size:")[1].split("px")[0])
            texts.append((float(a["x"]), float(a["y"]), fs,
                          a.get("text-anchor", "start")))
    # The key texts: those at or below the keys' row (the axis's own
    # texts sit above it).
    top = min(m[2] for m in marks) - 60
    return sorted(marks), [t for t in texts if t[1] > top]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestKeyOrderInChrome:

    def test_textfirst_and_stacked(self, mode):
        """textfirst: each text ends one keygap left of its key
        (twoway's anchor-end text, 0.56-0.60 of a text size before the
        key); stacked: the text under its key at its left edge, the key
        centre 1.6 text sizes above the text's centre."""
        legs, viol = _legends(mode, [([_sc(), _ln()], ""),
                                     ([_sc(), _ln()], "textfirst"),
                                     ([_sc(), _ln()], "stacked"),
                                     ([_sc(), _ln()], "textfirst stacked"),
                                     ([_sc(), _ln(), _sc("rep78")],
                                      "textfirst cols(1)")])
        assert viol == []
        plain, first, stacked, above, col = legs
        for it in first["items"]:
            gap = (it["canvas"][0] - it["text"][2]) / it["fs"]
            assert 0.35 < gap < 0.8, it
        for it in plain["items"]:
            assert it["text"][0] > it["canvas"][2], it
        marks, texts = _twoway_keys("stacked")
        fs = texts[0][2]
        twoway_rise = (texts[0][1] - 0.35 * fs - marks[0][2]) / fs
        for it in stacked["items"]:
            assert abs(it["text"][0] - it["canvas"][0]) <= 1.5, it
            kc = (it["canvas"][1] + it["canvas"][3]) / 2
            tc = (it["text"][1] + it["text"][3]) / 2
            assert abs((tc - kc) / it["fs"] - twoway_rise) < 0.25, (
                it, twoway_rise)
        # textfirst stacked: the text above its key, both at the left.
        for it in above["items"]:
            assert abs(it["text"][0] - it["canvas"][0]) <= 1.5, it
            assert it["text"][3] <= it["canvas"][1] + 1, it
        # textfirst cols(1): the texts end at one x, one keygap before
        # the keys' one column (twoway's anchor-end texts at 2195.82).
        ends = {round(it["text"][2]) for it in col["items"]}
        lefts = {round(it["canvas"][0]) for it in col["items"]}
        assert max(ends) - min(ends) <= 1 and len(lefts) == 1, col
