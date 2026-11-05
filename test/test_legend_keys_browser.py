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


def _ink_x(it):
    """``(left, centre, right)`` of an item's drawn pixels on the page."""
    ink, cv = it["ink"], it["canvas"]
    return (cv[0] + ink[0], cv[0] + (ink[0] + ink[2]) / 2, cv[0] + ink[2])


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
        # The key's left edge is its drawn pixels' (a marker key's canvas
        # is moved into its column, wider than the key: TestKeyBoxes).
        for it in first["items"]:
            gap = (_ink_x(it)[0] - it["text"][2]) / it["fs"]
            assert 0.35 < gap < 0.8, it
        for it in plain["items"]:
            assert it["text"][0] > _ink_x(it)[2], it
        marks, texts = _twoway_keys("stacked")
        fs = texts[0][2]
        twoway_rise = (texts[0][1] - 0.35 * fs - marks[0][2]) / fs
        for it in stacked["items"]:
            assert abs(it["text"][0] - _ink_x(it)[0]) <= 1.5, it
            kc = (it["canvas"][1] + it["canvas"][3]) / 2
            tc = (it["text"][1] + it["text"][3]) / 2
            assert abs((tc - kc) / it["fs"] - twoway_rise) < 0.25, (
                it, twoway_rise)
        # textfirst stacked: the text above its key, both at the left.
        for it in above["items"]:
            assert abs(it["text"][0] - _ink_x(it)[0]) <= 1.5, it
            assert it["text"][3] <= it["canvas"][1] + 1, it
        # textfirst cols(1): the texts end at one x, one keygap before
        # the keys' one column (twoway's anchor-end texts at 2195.82).
        ends = {round(it["text"][2]) for it in col["items"]}
        lefts = {round(it["canvas"][0]) for it in col["items"]}
        assert max(ends) - min(ends) <= 1 and len(lefts) == 1, col


#: Each series legend's keys' inked pixel counts before and after the
#: page's dropdown is moved to TARGET.
_MOVE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const ink = (c) => { const x = c.getContext('2d'); const W = c.width, H = c.height;
    if (!W || !H) return null; const d = x.getImageData(0, 0, W, H).data;
    let n = 0; for (let k = 3; k < d.length; k += 4) if (d[k] > 60) n++; return n; };
  const find = () => { const L = []; const visit = (v) => { if (!v) return;
    if (v.frame && v.renderer_views) for (const [m, rv] of v.renderer_views)
      if (m.type === 'Legend' && m.visible && rv.grid_el && m.name !== 'dash_colorvar_legend') L.push(rv);
    for (const c of (v.child_views || [])) visit(c); };
    ((typeof Bokeh.index[Symbol.iterator] === 'function') ? [...Bokeh.index] : Object.values(Bokeh.index)).forEach(visit); return L; };
  const read = () => find().map(rv => [...rv.grid_el.children].map(e => ink(e.querySelector('canvas'))));
  const before = read();
  let sel = null;
  for (const doc of Bokeh.documents) for (const m of doc.all_models) if (m.type === 'Select') sel = m;
  const opts = sel ? sel.options.map(o => Array.isArray(o) ? o : [o, o]) : [];
  const o = opts.find(o => o[1] === TARGET) || opts[opts.length - 1];
  if (sel) sel.value = String(o[0]);
  // Each legend's keys painted again after the move (headless Chrome
  // runs no animation frame for the page's own repaint).
  setTimeout(() => find().forEach((rv) => rv._paint_glyphs()), 300);
  setTimeout(() => parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, before, after: read(), opts}), '*'), 1500);
}, 3000));
</script>"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestMarkerKeysInChrome:

    def test_size(self, mode):
        """Each marker key's ink is twoway's marker width in text sizes
        (s2color 0.527, msize(large) 0.787: mk_s2color, mk_large), and a
        legend of markers only is as wide as its marker (its key canvas
        within a pixel of the ink); a legend with a line keeps symxsize
        (mk_line).  No CSP violation."""
        legs, viol = _legends(mode, [([_sc(), _sc("headroom")], ""),
                                     ([_sc(msize="large"), _sc("headroom")],
                                      ""),
                                     ([_sc(), _ln()], "")])
        assert viol == []
        plain, large, mixed = legs
        for leg, want in ((plain, [0.527, 0.527]), (large, [0.787, 0.527])):
            for it, w in zip(leg["items"], want):
                ink = it["ink"]
                assert ink is not None, it
                got = (ink[2] - ink[0]) / it["fs"]
                assert abs(got - w) < 0.08, (it, w)
            # The keys are as wide as the widest marker.
            widest = max(it["ink"][2] - it["ink"][0] for it in leg["items"])
            for it in leg["items"]:
                cw = it["canvas"][2] - it["canvas"][0]
                assert abs(cw - widest) <= 1.5, it
        m = mixed["items"][0]
        assert (m["canvas"][2] - m["canvas"][0]) / m["fs"] > 3, m
        assert abs((m["ink"][2] - m["ink"][0]) / m["fs"] - 0.527) < 0.08


def _twoway_after(case):
    """twoway's (text start - key centre) of *case*'s keys, in text
    sizes, by key text."""
    marks, texts = _twoway_keys(case)
    out = []
    for m, t in zip(marks, sorted(texts)):
        out.append(((t[0] - (m[0] + m[1]) / 2) / t[2], (t[0] - m[1]) / t[2]))
    return out


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestKeyBoxesInChrome:

    def test_marker_beside_a_line(self, mode):
        """A marker key beside a line key: the marker's text starts where
        twoway's does from the marker's centre (cell_ctl: 0.82 of a text
        size) and the line's where it did (0.60 after the line's end);
        under cols(1) one key column, the marker centred in the line's
        width and every text at one x (cols1); textfirst's marker text
        ends where twoway's does before the marker (textfirst).  No CSP
        violation."""
        legs, viol = _legends(mode, [([_sc(), _ln()], ""),
                                     ([_sc(), _ln(), _sc("rep78")],
                                      "cols(1)"),
                                     ([_sc(), _ln()], "textfirst")])
        assert viol == []
        mixed, col, first = legs
        (dot_c, _dr), (_lc, line_r) = _twoway_after("cell_ctl")
        dot, line = mixed["items"]
        got = (dot["text"][0] - _ink_x(dot)[1]) / dot["fs"]
        assert abs(got - dot_c) < 0.12, (got, dot_c, dot)
        got = (line["text"][0] - _ink_x(line)[2]) / line["fs"]
        assert abs(got - line_r) < 0.12, (got, line_r, line)
        lefts = {round(it["text"][0]) for it in col["items"]}
        assert max(lefts) - min(lefts) <= 1, col
        centres = [_ink_x(it)[1] for it in col["items"]]
        assert max(centres) - min(centres) <= 1.5, col
        # textfirst: the marker's text ends one key gap before its box.
        marks, texts = _twoway_keys("textfirst")
        tw = ((marks[0][0] + marks[0][1]) / 2 - texts[0][0]) / texts[0][2]
        dot = first["items"][0]
        got = (_ink_x(dot)[1] - dot["text"][2]) / dot["fs"]
        assert abs(got - tw) < 0.12, (got, tw, dot)


def _ink_y(it):
    """An item's drawn pixels' centre below its text's centre."""
    ink, cv = it["ink"], it["canvas"]
    return cv[1] + (ink[1] + ink[3]) / 2 - (it["text"][1] + it["text"][3]) / 2


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestSymplacementInChrome:

    def test_moves(self, mode):
        """symplacement(n) raises both keys by twoway's share of the text
        size (symp_n: 27.97 of 99.99), sw lowers them (symp_sw), c moves
        nothing; cols(1) symplacement(w) puts the marker at the line's
        left (cols1_symp_w: the marker's box, r 22.03, at the line's left
        end).  No CSP violation."""
        legs, viol = _legends(mode, [([_sc(), _ln()], ""),
                                     ([_sc(), _ln()], "symplacement(n)"),
                                     ([_sc(), _ln()], "symplacement(sw)"),
                                     ([_sc(), _ln()], "symplacement(c)"),
                                     ([_sc(), _ln(), _sc("rep78")],
                                      "cols(1) symplacement(w)")])
        assert viol == []
        plain, up, down, centre, west = legs
        tw = 27.965 / 99.99
        for leg, sign in ((up, -1), (down, 1), (centre, 0)):
            for it, p in zip(leg["items"], plain["items"]):
                got = (_ink_y(it) - _ink_y(p)) / it["fs"]
                assert abs(got - sign * tw) < 0.08, (sign, got, it, p)
        dot, line = west["items"][0], west["items"][1]
        # The marker's box left (its ink left plus half its outline) at
        # the line's left.
        box_left = _ink_x(dot)[0] + 0.5 * (
            (dot["ink"][2] - dot["ink"][0]) - 0.4406 * dot["fs"])
        assert abs(box_left - _ink_x(line)[0]) <= 1.5, (dot, line)


#: Each series legend's title box (its text's), its keys' text boxes and
#: the legend's own box, per legend in page order.
_NOTE_JS = r"""
<script>
document.addEventListener('securitypolicyviolation', (e) => {
  (window.__v = window.__v || []).push(e.violatedDirective); });
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const R = (r) => [r.left, r.top, r.right, r.bottom];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.type !== 'Legend' || !m.visible || !rv.grid_el) continue;
        if (m.name === 'dash_colorvar_legend') continue;
        const t = rv.title_el;
        let title = null;
        if (t && t.textContent) { const rg = document.createRange();
          rg.selectNodeContents(t); title = R(rg.getBoundingClientRect()); }
        const keys = [...rv.grid_el.children].map(e => {
          const lab = e.querySelector('.bk-label');
          const rg = document.createRange(); rg.selectNodeContents(lab);
          return {text: R(rg.getBoundingClientRect()),
                  canvas: R(e.querySelector('canvas').getBoundingClientRect()),
                  fs: parseFloat(getComputedStyle(lab).fontSize)}; });
        out.push({title, tfs: t ? parseFloat(getComputedStyle(t).fontSize) : 0,
                  box: R(rv.el.getBoundingClientRect()), keys});
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


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestNoteInChrome:

    def test_under_the_keys(self, mode):
        """legend(note("N")): the note under the keys inside the box,
        left-aligned with the first key, at 0.8 of the key text's size,
        its centre twoway's 1.04 key text sizes under the key texts'
        (legend_keys_truth.json note: 103.8 of 99.99 units), the box
        taller by about twoway's 1.15 text sizes (114.6); caption("C") at
        the key text's size (caption: 1.11 under, 134.5 taller); both,
        the box taller by both (note_caption: 249.1).  No CSP violation."""
        legs, viol = (lambda g: (g["out"], g["V"]))(kb._measure(
            mode, bk._spec([bk._graph("g%d" % i, [_sc(), _ln()],
                                      {"legend": lg}, title=False)
                            for i, lg in enumerate(
                                ["", 'note("N")', 'caption("C")',
                                 'note("N") caption("C")'])],
                           scheme="s2color"), _NOTE_JS)[1400])
        assert viol == []
        plain, note, cap, both = legs
        assert plain["title"] is None
        # Both: the box taller by both gaps and texts (note_caption:
        # 249.12 of 99.99 units).
        fs = both["keys"][0]["fs"]
        grow = ((both["box"][3] - both["box"][1])
                - (plain["box"][3] - plain["box"][1])) / fs
        assert abs(grow - 2.491) < 0.15, (grow, both)
        for leg, ratio, under, taller in ((note, 0.8, 1.038, 1.146),
                                          (cap, 1.0, 1.108, 1.345)):
            k = leg["keys"][0]
            fs = k["fs"]
            assert abs(leg["tfs"] / fs - ratio) < 0.02, leg
            t = leg["title"]
            # The first key is a marker centred in its canvas, its box
            # (its size, 0.4406 text sizes) at the column's left.
            left = (k["canvas"][0] + k["canvas"][2]) / 2 - 0.2203 * fs
            assert abs(t[0] - left) < 0.15 * fs, (left, leg)
            kc = (k["text"][1] + k["text"][3]) / 2
            tc = (t[1] + t[3]) / 2
            assert abs((tc - kc) / fs - under) < 0.15, (tc, kc, fs, leg)
            grow = ((leg["box"][3] - leg["box"][1])
                    - (plain["box"][3] - plain["box"][1])) / fs
            assert abs(grow - taller) < 0.15, (grow, leg, plain)
            assert t[3] <= leg["box"][3] + 0.5


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_weighted_marker_key(mode):
    """A weighted marker layer's key is its unweighted marker (twoway
    wt_large: msize(large)'s r 39.34, 0.787 of a text size across, as
    mk_large's), beside a line key; BokehJS drew it at 0.4 of the key
    box (about 0.5 of a text size, near medium's 0.527 by chance)."""
    w = _sc(weight="aweight", wexp="headroom", msize="large")
    legs, viol = _legends(mode, [([w, _ln()], "")])
    assert viol == []
    it = legs[0]["items"][0]
    assert it["ink"] is not None, it
    assert abs((it["ink"][2] - it["ink"][0]) / it["fs"] - 0.787) < 0.08, it


def test_emptied_layer_draws_no_key():
    """Saved: after the dropdown move foreign == 0, which leaves the
    layer `scatter mpg weight if foreign == 1' no row, its painted key is
    blank and the other layer's is drawn (the painter's early return on
    its layer's view; served, the redraw's proxy view keeps no row and
    BokehJS skips it: test_legend_keys.py::TestThePainterScript)."""
    lay = dict(_sc(), if_expr="foreign == 1")
    spec = bk._spec([bk._graph("g0", [lay, _sc("headroom")], {},
                               title=False)], scheme="s2color",
                    filt="foreign")
    got = kb._measure("saved", spec,
                      _MOVE_JS.replace("TARGET", json.dumps("Domestic")))
    got = got[1400]
    [before], [after] = got["before"], got["after"]
    assert before[0] > 50 and before[1] > 50, got
    assert after[0] <= 0.05 * before[0], got
    assert after[1] >= 0.9 * before[1], got


def _shp(t, **o):
    """*t*'s plot over the columns the probe pages carry."""
    from test_server_layer_defects import plot_for
    p = plot_for(t, dict(o))
    return {k: (v.replace("price", "headroom").replace("foreign", "headroom")
                if isinstance(v, str) else v) for k, v in p.items()}


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestKeyShapesInChrome:

    def test_shapes(self, mode):
        """Each key's ink in its canvas: rcap a line the box's width with
        caps of the cap size (twoway sh_rcap: 44.05 of 99.99-unit text,
        0.44 text sizes); rcapsym and dropline as tall as the marker
        (0.527); pcarrow its barbs (2 x 21.03 units and its 8.64 stroke, 0.507); rarea the box
        filled (sh_rarea: 99.99 units high, 1.0).  No CSP violation."""
        types = ["rcap", "rcapsym", "dropline", "pcarrow", "rarea"]
        legs, viol = _legends(mode, [([_shp(t), _sc()], "") for t in types])
        assert viol == []
        want = {"rcap": 0.44, "rcapsym": 0.527, "dropline": 0.527,
                "pcarrow": 0.507, "rarea": 1.0}
        for t, leg in zip(types, legs):
            it = leg["items"][0]
            ink, cv, fs = it["ink"], it["canvas"], it["fs"]
            assert ink is not None, (t, it)
            cw = cv[2] - cv[0]
            # Every shape spans the key box (a marker at an end drawn
            # whole inside it).
            assert ink[2] - ink[0] >= 0.9 * cw, (t, it)
            h = (ink[3] - ink[1]) / fs
            assert abs(h - want[t]) < 0.1, (t, h, it)
        # dropline's marker is on the right end: the ink is tallest there.
        drop = legs[2]["items"][0]
        assert drop["ink"][2] >= drop["canvas"][2] - drop["canvas"][0] - 1.5

    def test_emptied_rcap_draws_no_key(self, mode):
        """A move that leaves an rcap layer no row blanks its painted key;
        the other layer's key stays."""
        if mode == "served":
            pytest.skip("the served redraw is test_legend_keys.py's "
                        "TestTheShapeScript::test_empty_view_draws_nothing")
        lay = dict(_shp("rcap"), if_expr="foreign == 1")
        spec = bk._spec([bk._graph("g0", [lay, _sc("headroom")], {},
                                   title=False)], scheme="s2color",
                        filt="foreign")
        got = kb._measure("saved", spec,
                          _MOVE_JS.replace("TARGET", json.dumps("Domestic")))
        got = got[1400]
        [before], [after] = got["before"], got["after"]
        assert before[0] > 30 and before[1] > 30, got
        assert after[0] <= 0.05 * before[0], got
        assert after[1] >= 0.9 * before[1], got


#: After a click on the first key of by()'s legend cell: each panel's
#: renderers, [glyph type, visible, is a key proxy].
_BY_CLICK_JS = r"""
<script>
const ERR = [];
addEventListener('error', e => ERR.push(String(e.message)));
function views() {
  const out = [];
  const visit = (v) => { if (!v) return; out.push(v);
    if (v.renderer_views) for (const [m, rv] of v.renderer_views) out.push(rv);
    for (const c of (v.child_views || [])) visit(c); };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return out;
}
const panels = () => views().filter(v => v.model && v.model.type === 'Figure'
    && !String(v.model.name || '').startsWith('dash_by_'))
  .map(v => v.model.renderers.filter(r => r.type === 'GlyphRenderer')
    .map(r => [r.glyph.type, r.visible, (r.tags || []).includes('dash_key_proxy')]));
addEventListener('load', () => setTimeout(() => { try {
  const lv = views().find(v => v.model && v.model.type === 'Legend'
    && v.model.name === 'dash_by_legend_key');
  const res = {found: !!lv, ERR, before: panels()};
  const en = lv ? (lv.entries || [])[0] : null;
  if (en && en.el) {
    for (const t of ['pointerdown', 'pointerup'])
      en.el.dispatchEvent(new PointerEvent(t, {bubbles: true}));
    en.el.click();
  }
  setTimeout(() => { res.after = panels();
    parent.postMessage('DASHPROBE' + JSON.stringify(Object.assign({W: innerWidth}, res)), '*'); }, 500);
  } catch (e) { parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, exc: String(e)}), '*'); }
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_by_click_hides_a_shaped_series(mode):
    """by(foreign): a click on the rcapsym key of by()'s legend cell hides
    its line and both end markers in both panels and leaves the scatter
    (WP-31 D10 through the painted shape's proxies)."""
    spec = bk._spec([bk._graph("g0", [_shp("rcapsym"), _sc()],
                               {"by": "foreign"}, title=False)],
                    scheme="s2color")
    got = kb._measure(mode, spec, _BY_CLICK_JS)[1400]
    assert got.get("found") and got["ERR"] == [], got
    assert len(got["after"]) == 2, got
    for before, after in zip(got["before"], got["after"]):
        drawn = [(g, v) for g, v, p in after if not p]
        assert all(v for g, v, p in before if not p), got
        # The rcapsym layer (a Segment and two Scatters) hidden, the
        # scatter layer kept.
        assert [g for g, v in drawn if not v] == ["Segment", "Scatter",
                                                  "Scatter"], got
        assert [g for g, v in drawn if v] == ["Scatter"], got
