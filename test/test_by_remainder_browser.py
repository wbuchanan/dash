"""
test_by_remainder_browser.py -- by()'s overall legend and an emptied
panel in headless Chrome (WP-31 D10, D-36.c and D-36.i).

test_by_remainder.py reads the models; here BokehJS draws both modes'
pages.  A click on the overall legend's first entry (the DOM element
BokehJS 3.9 draws each entry as) hides that series in every panel and
logs no error: a LegendItem may hold another plot's renderers.  On the
saved page a slider move that leaves the Domestic panel without rows hides
it, and the grid keeps its cell blank: the other panel stays where it was
and the grid keeps its height.  Without Chrome these tests skip, as
test_by_axes_keys_browser.py's do.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe as rp  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_remainder as tr  # noqa: E402

if rp.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

_CLICK_JS = r"""
<script>
const ERR = [];
addEventListener('error', e => ERR.push(String(e.message)));
const _ce = console.error; console.error = (...a) => { ERR.push(a.map(String).join(' ')); _ce(...a); };
function views() {
  const out = [];
  const visit = (v) => { if (!v) return; out.push(v);
    if (v.renderer_views) for (const [m, rv] of v.renderer_views) out.push(rv);
    for (const c of (v.child_views || [])) visit(c); };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return out;
}
addEventListener('load', () => setTimeout(() => { try {
  const vs = views();
  const lv = vs.find(v => v.model && v.model.type === 'Legend' && v.model.name === 'dash_by_legend_key');
  const res = {found: !!lv, ERR};
  if (lv) {
    const item = lv.model.items[0];
    res.n = item.renderers.length;
    res.before = item.renderers.map(r => r.visible);
    const en = (lv.entries || [])[0];
    res.entries = (lv.entries || []).length;
    let hit = false;
    if (en && en.el) {
      for (const t of ['pointerdown', 'pointerup']) en.el.dispatchEvent(new PointerEvent(t, {bubbles: true}));
      en.el.click();
      hit = item.renderers.some(r => !r.visible);
    }
    res.hit = hit;
    res.after = item.renderers.map(r => r.visible);
    res.others = lv.model.items.slice(1).map(it => it.renderers.map(r => r.visible));
  }
  setTimeout(() => parent.postMessage('DASHPROBE' + JSON.stringify(Object.assign({W: innerWidth}, res)), '*'), 500);
  } catch (e) { parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, exc: String(e), stack: String(e.stack).slice(0, 400)}), '*'); }
}, 3000));
</script>
"""

_HIDE_JS = r"""
<script>
const ERR = [];
addEventListener('error', e => ERR.push(String(e.message)));
function views() {
  const out = [];
  const visit = (v) => { if (!v) return; out.push(v);
    for (const c of (v.child_views || [])) visit(c); };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return out;
}
function panels() {
  return views().filter(v => v.model && v.model.type === 'Figure')
    .map(v => ({vis: v.model.visible, bbox: [v.bbox.x0, v.bbox.y0, v.bbox.width, v.bbox.height]}));
}
function grids() {
  return views().filter(v => v.model && v.model.type === 'GridPlot')
    .map(v => [v.bbox.width, v.bbox.height]);
}
addEventListener('load', () => setTimeout(() => { try {
  const before = panels(), gb = grids();
  const doc = Bokeh.documents[0];
  const ms = [...(doc._all_models ? doc._all_models.values() : doc.all_models)];
  const s = ms.find(m => m.type === 'Slider');
  s.value = 11000;
  try { s.value_throttled = 11000; } catch (e) {}
  setTimeout(() => {
    for (const v of Object.values(Bokeh.index)) v.after_resize && v.after_resize();
    setTimeout(() => {
      const after = panels(), ga = grids();
      parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, before, after, gb, ga, ERR}), '*');
    }, 800);
  }, 800);
  } catch (e) { parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, exc: String(e)}), '*'); }
}, 3000));
</script>
"""



def _run(js, html):
    mp = pytest.MonkeyPatch()
    mp.setattr(rp, "PROBE_JS", js)
    try:
        return rp.measure_many(html, (1400,))[1400]
    finally:
        mp.undo()


def _page(mode, spec, data):
    if mode == "saved":
        tag = next(bk._SEQ)
        a = os.path.join(bk._TMP, "r_%d.json" % tag)
        b = os.path.join(bk._TMP, "rd_%d.json" % tag)
        with open(a, "w") as fh:
            json.dump(spec, fh)
        with open(b, "w") as fh:
            json.dump(data, fh)
        return bk.dr.DashRenderer(a, b).render()
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    _r, _n, owner = bk._build(mode, spec, data=data)
    return file_html(owner, INLINE, "served")


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_click_hides_every_panel(mode):
    spec = bk._spec([bk._graph("lg", bk._TWO,
                               {"by": "rep78, legend(ring(0))"})],
                    scheme="s2color")
    got = _run(_CLICK_JS, _page(mode, spec, tr._data()))
    assert got.get("found") and got["ERR"] == [], got
    assert got["n"] == 6 and got["hit"]          # the swatch and 5 panels
    assert got["before"] == [True] * 6 and got["after"] == [False] * 6
    assert got["others"] == [[True] * 6]


def test_a_hidden_panel_keeps_its_cell_blank():
    import test_mode_parity as tp
    from conftest import make_data_json
    spec = tp._spec(plots=[{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                    graph_options={"by": "foreign"},
                    build_options={"filter": "price, type(slider)"})
    got = _run(_HIDE_JS, _page("saved", spec, make_data_json(
        tp._DF, tp._VALUE_LABELS, tp._LABEL_NAMES)))
    assert got["ERR"] == [], got
    before, after = got["before"], got["after"]
    assert [p["vis"] for p in after] == [False, True]
    assert after[1]["bbox"] == before[1]["bbox"]
    assert got["ga"] == got["gb"]
