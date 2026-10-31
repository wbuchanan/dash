"""
test_by_label_options.py -- a by() panel label's subtitle() sub-options
and its text (WP-41 section 41-06: BY-10, BY-16).

The defect (BY-10): twoway draws the graph's own subtitle(,
justification() nobexpand lwidth() lpattern() span alignment() linegap()
bmargin() placement() orientation()) on every panel label; dash named each
as "not implemented and ignored" and drew the label centred in a
full-width box, in both modes.  BY-16: a date by() variable's panels read
its formatted date where twoway writes the number (14610), and a value
label of quoted parts stayed one line.

The truth is test/fixtures/by_label_truth.json, measured by
scripts/extract_by_label_truth.do on stcolor (5400 x 3240 SVG units): each
probe's label boxes, label texts and plot regions.
"""
import itertools
import json
import math
import os
import sys
import tempfile
import types
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from by_panel_probe import by_grid, panel_label_title  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_label_truth.json")
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_label_")
_TRUTH = None
_NOTE = "subtitle() sub-option"


def _truth():
    global _TRUTH
    if _TRUTH is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _TRUTH = json.load(fh)
    return _TRUTH


def _probe(pid):
    return _truth()["probes"][pid]


def _frame():
    """Twenty cars: mpg, weight, foreign (0/1) and d = 1jan2000 + foreign,
    as the fixture's probes generate it."""
    rng = np.random.default_rng(4106)
    foreign = np.array([0, 1] * 10, dtype=float)
    return pd.DataFrame({"mpg": rng.integers(12, 40, 20).astype(float),
                         "weight": rng.integers(1800, 4800, 20)
                         .astype(float),
                         "foreign": foreign, "d": 14610.0 + foreign})


#: The fixture's value labels: bl.dta's foreign is labelled origin;
#: bl_q.dta's ql gives Domestic two quoted parts (Q01).
_LABELS = {"bl": {"origin": {"0": "Domestic", "1": "Foreign"}},
           "bl_q": {"ql": {"0": '"Dom" "estic"', "1": "Foreign"}}}


def _go_of(options):
    """The probe's graph options: `subtitle(...)' and `by(...)'."""
    go = {}
    for tok in dr._dash_by_tokens(options):
        name, _, arg = tok.partition("(")
        go[name] = arg[:-1]
    return go


def _spec(go, formats=None):
    go = dict(go)
    go["name"] = "g1"
    g = {"name": "g1", "graph_options": go, "options": dict(go),
         "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                    "options": {}}],
         "if_expr": "", "in_expr": ""}
    return {"graphs": [g], "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "", "theme": "",
                "scheme": "stcolor", "session_scheme": "", "title": "",
                "subtitle": "", "registry": "g1", "tabs": "",
                "filter_position": "top", "level": "95",
                "formats": formats or {}}}


def _write(spec, data="bl"):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    (vl,) = _LABELS[data].keys()
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame(), _LABELS[data], {"foreign": vl}),
                  fh)
    return tag, sp, dp


def _build(mode, spec, data="bl"):
    """(roots, notes, owner) of *spec* in *mode*."""
    tag, sp, dp = _write(spec, data)
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            owner = dr.DashRenderer(sp, dp)
            render_models(owner)
            roots = [owner._last_layout_root]
        else:
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
    notes = [str(w.message) for w in caught]
    if mode == "served":
        from bokeh.document import Document
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, "_blo_app_%d" % tag)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            owner = Document()
            mod.make_document(owner)
        roots = list(owner.roots)
        notes += [str(w.message) for w in caught]
    return roots, notes, owner


def _panels(roots):
    from bokeh.models import GridPlot
    for root in roots:
        for m in root.references():
            if isinstance(m, GridPlot) and any(
                    panel_label_title(c[0]) is not None for c in m.children):
                p, _h, _f = by_grid(root)
                return [f for _, _, f in p]
    return []


def _draw(mode, pid=None, go=None, formats=None, data=None):
    """Namespace(panels, notes, owner) of fixture probe *pid* (or graph
    options *go*) drawn in *mode*."""
    if pid is not None:
        p = _probe(pid)
        go = _go_of(p["options"])
        data = data or p["data"]
        if "by(d" in p["options"]:
            formats = dict(formats or {}, d="%td")
    roots, notes, owner = _build(mode, _spec(go, formats), data or "bl")
    return types.SimpleNamespace(panels=_panels(roots), notes=notes,
                                 owner=owner, roots=roots)


def _box(fig):
    """The panel's label ColorBar, or None."""
    for side in ("above", "below"):
        for m in getattr(fig, side):
            if getattr(m, "name", None) == "dash_by_label_box":
                return m
    return None


def _span_items(fig):
    cb = next((c for c in fig.js_property_callbacks.get(
        "change:" + dr._DASH_SPAN_KEYS[0], [])
        if getattr(c, "code", None) == dr._DASH_SPAN_JS), None)
    return [] if cb is None else list(cb.args.get("items", []))


def _font_px(box):
    return float(str(box.major_label_text_font_size).replace("px", ""))


_NAMED = ("L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09",
          "L10", "L11", "L12", "L13", "L15")


# ---------------------------------------------------------------------------
# BY-10
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestLabelOptions:

    @pytest.mark.parametrize("pid", _NAMED)
    def test_no_note(self, mode, pid):
        """Every sub-option the fixture probes is drawn or, where twoway
        draws nothing different (width(), height(), placement() on an
        expanded box), taken in silence: nothing is named."""
        r = _draw(mode, pid)
        assert len(r.panels) == 2
        assert not [n for n in r.notes if _NOTE in n], r.notes

    def test_default_unchanged(self, mode):
        """L00 (and width()/height() alone, L09 and L15, which twoway draws
        as L00): the label centred in a full-width box, no span item."""
        base = None
        for pid in ("L00", "L09", "L15"):
            r = _draw(mode, pid)
            for fig in r.panels:
                box = _box(fig)
                assert box is not None
                assert list(box.ticker.ticks) == [0.5]
                assert box.major_label_text_align == "center"
                assert not [it for it in _span_items(fig)
                            if it[1] == "bylabel"]
                h = box.height
                font = _font_px(box)
                assert box.label_standoff == int(-(h + font) // 2 - 2)
                rec = (box.height, box.label_standoff, box.bar_line_width)
                base = base or rec
                assert rec == base, pid

    def test_justification(self, mode):
        """justification(left|right): the label at that end of its box,
        inset by the box's margin (L01, L02: 16.54 of 3240, stcolor's 0.6
        units at by()'s multiplier), placed at layout time by the span
        hook's bylabel item."""
        for pid, place in (("L01", "left"), ("L02", "right")):
            r = _draw(mode, pid)
            p = _probe(pid)
            b = p["boxes"][0]
            inset_tw = (b["text_x"] - b["x"]) if place == "left" else \
                (b["x"] + b["w"] - b["text_x"])
            for fig in r.panels:
                assert panel_label_title(fig).align == place
                box = _box(fig)
                (it,) = [i for i in _span_items(fig) if i[1] == "bylabel"]
                assert it[0] is box and it[3] == place
                # The inset in px against the font, as twoway's against its
                # font (105.13 units).
                assert abs(it[4] - inset_tw / b["size"] * _font_px(box)) \
                    <= 0.5, (it, inset_tw)

    def test_nobexpand_draws_the_title_box(self, mode):
        """nobexpand (L03): no ColorBar; the label's Title is shown with
        the box's fill and outline round its text, as twoway's box only as
        wide as the text; placement(e) under nobexpand (L12) puts it at
        the right end."""
        for pid, align in (("L03", "center"), ("L12", "right")):
            r = _draw(mode, pid)
            for fig in r.panels:
                assert _box(fig) is None
                t = panel_label_title(fig)
                assert t.visible and t.align == align
                assert t.background_fill_color == \
                    _probe(pid)["boxes"][0]["fill"]
                assert t.border_line_color == \
                    _probe(pid)["boxes"][0]["stroke"]
                assert t.padding > 0

    def test_outline_width_and_pattern(self, mode):
        """lwidth(vthick) lcolor(black) (L04) outlines the box seven times
        the default's width, as twoway's (38.56 against 5.51);
        lpattern(dash) (L05) dashes it."""
        base = _box(_draw(mode, "L00").panels[0]).bar_line_width
        p4, p0 = _probe("L04")["boxes"][0], _probe("L00")["boxes"][0]
        for fig in _draw(mode, "L04").panels:
            box = _box(fig)
            assert box.bar_line_color == "#000000"
            assert abs(box.bar_line_width / base
                       - p4["stroke_width"] / p0["stroke_width"]) < 0.1
        for fig in _draw(mode, "L05").panels:
            box = _box(fig)
            assert list(box.bar_line_dash) == list(
                dr.OptionTranslator.translate_lpattern("dash"))
            assert box.bar_line_color == "#000000"

    def test_span_item(self, mode):
        """span (L06): the box is widened over the panel's y labels at
        layout time (the span hook's bylabel item, mode "span", on the
        panel's graph)."""
        for fig in _draw(mode, "L06").panels:
            (it,) = [i for i in _span_items(fig) if i[1] == "bylabel"]
            assert it[0] is _box(fig) and it[7] == "span" and it[5] == "panel"

    def test_alignment(self, mode):
        """alignment(top) (L07, L16) and alignment(bottom) (L08) raise the
        text in its box, alignment(baseline) (L17) lowers it, by twoway's
        shift against its font (about 0.15 of it); the box keeps its
        height, height() or not (L19)."""
        r0 = _box(_draw(mode, "L00").panels[0])
        t0 = _probe("L00")["boxes"][0]
        for pid in ("L07", "L08", "L16", "L17", "L19"):
            box = _box(_draw(mode, pid).panels[0])
            b = _probe(pid)["boxes"][0]
            # The bar's labels sit above it: a larger standoff raises the
            # text, where twoway's y falls.
            want = -(b["text_y"] - t0["text_y"]) / t0["size"] * _font_px(r0)
            assert box.height == r0.height, pid
            assert abs((box.label_standoff - r0.label_standoff) - want) \
                <= 1.0, (pid, box.label_standoff, r0.label_standoff, want)

    def test_linegap(self, mode):
        """linegap(3) (L10): the line step is the font plus the gap at
        by()'s multiplier, as twoway's 187.82 against its 105.13 font."""
        p = _probe("L10")
        ys = sorted(t["y"] for t in p["svg_texts"]
                    if t["text"] in ("Dom", "estic"))
        want = (ys[1] - ys[0]) / p["boxes"][0]["size"]
        for fig in _draw(mode, go=_go_of(p["options"])).panels:
            box = _box(fig)
            assert abs(box.major_label_text_line_height - want) < 0.03

    def test_bmargin(self, mode):
        """bmargin(medium) (L11): the box keeps that margin outside it on
        every side, as twoway's (96.4 of 3240, 3.5 units at by()'s
        multiplier) against its font.  BokehJS keeps no margin round a
        ColorBar in a side panel, so it is the bar's clear padding."""
        p0, p = _probe("L00")["boxes"][0], _probe("L11")["boxes"][0]
        want = (p["x"] - p0["x"]) / p0["size"]
        assert abs((p["y"] - p0["y"]) - (p["x"] - p0["x"])) < 1.0
        for fig in _draw(mode, "L11").panels:
            box = _box(fig)
            assert box.margin == 0
            assert abs(box.padding - want * _font_px(box)) <= 1.0, \
                box.padding

    def test_orientation_stays_named(self, mode):
        """orientation(vertical) (L14): twoway turns the text (rotate(-90))
        and grows the box to the plot region's height; dash cannot turn
        the label row's text (BokehJS clips a turned Label to the plot
        region), so it is named once and the label drawn as L00 (BUGS.md
        "A by() panel label's orientation() is named, not drawn")."""
        p = _probe("L14")["boxes"][0]
        assert p["angle"] == -90.0
        r = _draw(mode, "L14")
        named = [n for n in r.notes if _NOTE in n]
        assert len(named) == 1 and "orientation(vertical)" in named[0]
        for fig in r.panels:
            assert list(_box(fig).ticker.ticks) == [0.5]


# ---------------------------------------------------------------------------
# BY-10 in headless Chrome
# ---------------------------------------------------------------------------

import responsive_probe  # noqa: E402

#: Each panel's frame, its label box's fill extent (stcolor's #F0F0F0) in
#: the rows above the frame and the dark (text) pixels inside it, canvas
#: px.
_LABEL_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views && v.canvas_view) {
      const f = v.frame.bbox, c = v.bbox;
      const ctx = v.canvas_view.primary.ctx;
      const r = window.devicePixelRatio || 1;
      const y0 = Math.max(0, Math.floor(f.y0 - 120)), y1 = Math.floor(f.y0);
      const W = Math.floor(c.width);
      if (y1 > y0 && W > 0) {
        const img = ctx.getImageData(0, Math.round(y0 * r),
                                     Math.round(W * r),
                                     Math.round((y1 - y0) * r));
        let fill = null, dark = null;
        for (let yy = 0; yy < img.height; yy++) {
          for (let xx = 0; xx < img.width; xx++) {
            const i = 4 * (yy * img.width + xx);
            const R = img.data[i], G = img.data[i + 1], B = img.data[i + 2];
            const x = xx / r, y = y0 + yy / r;
            const add = (b) => b == null ? [x, y, x, y]
              : [Math.min(b[0], x), Math.min(b[1], y),
                 Math.max(b[2], x), Math.max(b[3], y)];
            if (Math.abs(R - 240) <= 2 && Math.abs(G - 240) <= 2
                && Math.abs(B - 240) <= 2) { fill = add(fill); }
            else if (R + G + B < 300) { dark = add(dark); }
          }
        }
        out.push({at: [Math.round(c.x0), Math.round(c.y0)],
                  frame: [f.x0, f.y0, f.x1, f.y1], fill, dark});
      }
    }
    for (const k of (v.child_views || [])) visit(k);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""


def _page(mode, pid):
    """The page *pid* draws in *mode*, as HTML."""
    p = _probe(pid)
    spec = _spec(_go_of(p["options"]),
                 {"d": "%td"} if "by(d" in p["options"] else None)
    if mode == "saved":
        _tag, sp, dp = _write(spec, p["data"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return dr.DashRenderer(sp, dp).render()
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    _r, _n, owner = _build(mode, spec, p["data"])
    return file_html(owner, INLINE, "served")


def _in_chrome(mode, pid):
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _LABEL_JS)
    try:
        got = responsive_probe.measure_many(_page(mode, pid), (1400,))[1400]
    finally:
        mp.undo()
    out = [o for o in got["out"] if o["fill"] is not None]
    return sorted(out, key=lambda o: (o["at"][1], o["at"][0]))


def _chrome_params():
    out = []
    for mode in _MODES:
        for pid in ("L01", "L03", "L06", "L07"):
            marks = () if (mode, pid) == ("saved", "L01") else \
                (pytest.mark.release,)
            out.append(pytest.param(mode, pid, marks=marks,
                                    id="%s-%s" % (mode, pid)))
    return out


@pytest.mark.skipif(responsive_probe.find_chrome() is None,
                    reason="headless Chrome is not installed (set "
                           "DASH_CHROME); the browser check is skipped")
class TestLabelOptionsInChrome:

    @pytest.mark.parametrize("mode,pid", _chrome_params())
    def test_positions_match_twoway(self, mode, pid):
        """The label's text and box against the panel's plot region, as
        twoway draws them, within 2 px once twoway's units are mapped to
        the page by the font (dash's label px against twoway's 105.13
        units): L01 the text inset at the box's left end, L03 the box as
        wide as the text and centred, L06 the box widened left over the y
        labels and right past the frame, L07 the text raised."""
        panels = _in_chrome(mode, pid)
        assert len(panels) == 2, panels
        p = _probe(pid)
        font = _font_px_of(mode, pid)
        s = font / p["boxes"][0]["size"]
        for got, b in zip(panels, p["boxes"]):
            f, fill, dark = got["frame"], got["fill"], got["dark"]
            pr = b["plotregion"]
            if pid == "L01":
                assert abs((dark[0] - fill[0]) - (b["text_x"] - b["x"]) * s) \
                    <= 2.0, got
                assert abs(fill[0] - f[0]) <= 1.5 and abs(fill[2] - f[2]) \
                    <= 1.5, got
            elif pid == "L03":
                # 3 px: Chrome's text metrics against Stata's Helvetica
                # (measured 55 px against 57.35).
                assert abs((fill[2] - fill[0]) - b["w"] * s) <= 3.0, got
                assert abs((fill[0] + fill[2]) / 2 - (f[0] + f[2]) / 2) \
                    <= 2.0, got
            elif pid == "L06":
                # The box runs over the panel's graph as WP-32's spanned
                # boxes on a by() panel do (region "panel": 1.5 units left
                # of its y labels to its right margin), the text centred
                # on it.  twoway's ends differ by a few px at this scale
                # (left 32 px against 25, right 4 against 13): a spanned
                # box's ends are the "panel" region's, not refitted here.
                if pr["x"] - b["x"] > 1:
                    assert fill[0] <= f[0] - 20, got
                assert fill[2] >= f[2], got
                assert abs((dark[0] + dark[2]) / 2
                           - (fill[0] + fill[2]) / 2) <= 2.0, got
            else:
                base = _in_chrome(mode, "L00")[0]
                b0 = _probe("L00")["boxes"][0]
                # Against the box's top edge, which keeps its height (the
                # label row gains the shift as clear space above the box:
                # BokehJS sizes a bar with its labels).
                assert abs((fill[3] - fill[1]) - (base["fill"][3]
                                                  - base["fill"][1])) <= 1.0
                assert abs(((dark[1] - fill[1])
                            - (base["dark"][1] - base["fill"][1]))
                           - (b["text_y"] - b0["text_y"]) * s) <= 2.0, got
                break


def _font_px_of(mode, pid):
    """dash's label font, px (the box's tick label, or the Title's under
    nobexpand)."""
    fig = _draw(mode, pid).panels[0]
    box = _box(fig)
    if box is not None:
        return _font_px(box)
    fs = str(panel_label_title(fig).text_font_size)
    if fs.endswith("pt"):
        return float(fs[:-2]) * dr.OptionTranslator.PX_PER_PT
    return float(fs.replace("px", ""))


class TestTheHelpers:

    def test_label_just(self):
        """_dash_by_label_just: justification()'s spellings; under
        nobexpand only placement()'s compass (L12), justification()
        moving nothing (L20); None for the scheme's."""
        f = dr._dash_by_label_just
        assert f({"justification": "left"}) == "left"
        assert f({"justification": "l"}) == "left"
        assert f({"justification": "r"}) == "right"
        assert f({"justification": "c"}) == "center"
        assert f({"justification": "bogus"}) is None
        assert f({}) is None and f(None) is None
        assert f({"nobexpand": "nobexpand", "justification": "left"}) is None
        for pl, want in (("e", "right"), ("ne", "right"), ("se", "right"),
                         ("w", "left"), ("nw", "left"), ("sw", "left"),
                         ("n", "center"), ("c", "center"), ("east", "right")):
            assert f({"nobexpand": "nobexpand", "placement": pl}) == want, pl
        # placement() on an expanded box draws nothing different (L13).
        assert f({"placement": "e"}) is None


# ---------------------------------------------------------------------------
# BY-16
# ---------------------------------------------------------------------------

def _labels(r):
    return [str(panel_label_title(f).text) for f in r.panels]


@pytest.mark.parametrize("mode", _MODES)
class TestPanelValues:

    def test_date_is_the_number(self, mode):
        """by(d) on a %td date with no value label (D01): each panel reads
        the Stata number, as twoway writes it into a macro."""
        assert _probe("D01")["texts"] == ["14610", "14611"]
        assert _labels(_draw(mode, "D01")) == ["14610", "14611"]

    def test_subtitleformat_var_keeps_dates(self, mode):
        """by(d, subtitleformat(var)) (D02): the variable's own format,
        dates, as twoway draws them."""
        assert _labels(_draw(mode, "D02")) == _probe("D02")["texts"]

    def test_quoted_parts_are_lines(self, mode):
        """A value label of quoted parts (Q01: `"Dom" "estic"') is drawn
        one line per part, its box a line taller (twoway: 243.51 against
        138.38 for a 105.13 font)."""
        p = _probe("Q01")
        assert p["labels"][0] == ["Dom", "estic"]
        r = _draw(mode, "Q01")
        assert _labels(r) == ["Dom\nestic", "Foreign"]
        one = _box(_draw(mode, "L00").panels[0])
        box = _box(r.panels[0])
        want = (p["boxes"][0]["h"] - _probe("L00")["boxes"][0]["h"]) \
            / p["boxes"][0]["size"] * _font_px(box)
        assert abs((box.height - one.height) - want) <= 1.0


class TestQuotedLines:

    def test_quoted_lines_unit(self):
        """_dash_quoted_lines: two or more Stata strings, plain or compound
        quoted, become lines; anything else is the text unchanged."""
        f = dr._dash_quoted_lines
        assert f('"Dom" "estic"') == "Dom\nestic"
        assert f(' "a"  "b" "c" ') == "a\nb\nc"
        assert f('\x60"a"\' \x60"b"\'') == "a\nb"
        assert f('\x60"say "hi""\' "x"') == 'say "hi"\nx'
        for same in ('"one"', "Domestic", '"a" b', 'a "b" "c"', "", '"a""b',
                     '"a" "b', '""'):
            assert f(same) == same, same
        assert f(None) == ""
        long = '"x" ' * 20000
        assert f(long).count("\n") == 19999
