"""WP-44 44-01: an axis title is drawn as twoway draws it (AX-13, PIC-12,
MS-13, MS-11).

twoway's answers are measured in test/fixtures/axis_title_truth.json
(scripts/extract_axis_title_truth.do; SVG units are 10 per point, a rotate
of -90 reads upward):

* orientation(): horizontal and hor draw the y title upright, vertical and
  vert as the plain one (upward), rvertical downward (rotate -270),
  rhorizontal upside down (rotate -180); an unknown word prints "named
  style <w> not found in class tb_orientstyle" and draws upright
  (ax13_or_*).  xtitle("X", orientation(vertical)) turns the x title.
* placement(): along the axis only -- n and ne put a y title's top end at
  the plot region's top, s and sw its bottom end at the bottom; e and w
  leave it; on an x title e and w move it to the right and left ends, n
  leaves it (ax13_place_*, ax13_xplace_*).
* justification(), alignment() and bmargin() without a box draw what the
  plain title draws (ax13_yjust_*, ax13_xjust_*, ax13_align_*,
  ax13_bmargin_large): taken in silence.
* margin() is the title's own margin in screen sides: margin(l+5) moves
  the y title and the plot region 144 units right; margin(large) the
  title 230 and the plot 461 (ax13_margin_*).
* linegap(5) widens the line step from 100 to 244 units
  (ax13_linegap_5 against ax13_two_lines).
* box draws a frame round the title, in the text box style's fill, and
  fcolor()/lcolor()/lwidth() style it (ax13_box*); tstyle(heading) draws
  the title at heading's size, 140 units where the plain one is 100.

While iterating: ``python3 -m pytest test/test_axis_titles_p9.py -q -n0``.
"""
import json
import math
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "axis_title_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)
_SC = [P("scatter", "mpg", "weight")]
_Y2 = [P("scatter", "mpg", "weight"), P("scatter", "price", "weight",
                                        yaxis=2)]
_FORMATS = {"weight": "%8.0gc", "mpg": "%8.0g", "price": "%8.0gc"}
_UNITS_PER_PT = 10.0
_PX = dr.OptionTranslator.PX_PER_PT / _UNITS_PER_PT     # px per SVG unit


def _figs(mode, go, plots=None, scheme=""):
    """The first figure and every warning the build printed."""
    from conftest import render_models
    spec = tda._spec(plots or _SC, go, scheme=scheme, formats=_FORMATS)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            _tag, sp, dp = tda._write(spec, "auto")
            r = render_models(dr.DashRenderer(sp, dp))
            figs = tb._panels(list(r.figures.values()))
        else:
            figs = tda._figs(mode, spec)
    return figs[0], [str(x.message) for x in w]


def _notes(warns):
    return [w for w in warns if "not implemented" in w]


def _text(key, s):
    """The fixture's <text> whose string is *s* (the title)."""
    return next(t for t in _T[key]["texts"] if t["text"] == s)


def _fixture_angle(key, s):
    """twoway's rotate as a Bokeh angle: counter-clockwise radians in
    (-pi, pi]."""
    r = _text(key, s)["rotate"]
    a = math.radians(-(r or 0.0))
    while a > math.pi + 1e-9:
        a -= 2 * math.pi
    return a


def _boxes(f):
    return [m for side in ("left", "right", "below", "above")
            for m in getattr(f, side)
            if "dash_axis_title_box" in (getattr(m, "tags", None) or [])]


def _side_of(f, model):
    return next(sd for sd in ("left", "right", "below", "above")
                if any(m is model for m in getattr(f, sd)))


# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta(self):
        m = _T["_meta"]
        assert m["source"] == "scripts/extract_axis_title_truth.do"
        assert sorted(k for k in m if k != "scheme") == [
            "born_date", "dash_commit", "extracted", "source",
            "stata_version"]

    def test_every_probe_drew(self):
        for k, row in _T.items():
            if k != "_meta":
                assert row["rc"] == 0, (k, row["log"])


_WORDS = ("horizontal", "vertical", "rhorizontal", "rvertical", "hor",
          "vert")


class TestOrientation:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("word", _WORDS)
    def test_each_word(self, mode, word):
        key = "ax13_or_" + word
        f, w = _figs(mode, {"ytitle": f'"Y", orientation({word})'})
        assert not _notes(w), w
        got = tda._axis(f, "y").axis_label_orientation
        assert isinstance(got, float), got
        assert got == pytest.approx(_fixture_angle(key, "Y"), abs=1e-9)

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_unknown_word_draws_upright_with_twoways_note(self, mode):
        # twoway: "named style bogus not found in class tb_orientstyle,
        # default attributes used", and the title drawn upright.
        assert any("tb_orientstyle" in ln for ln in _T["ax13_or_bogus"]
                   ["log"])
        assert _text("ax13_or_bogus", "Y")["rotate"] is None
        f, w = _figs(mode, {"ytitle": '"Y", orientation(bogus)'})
        assert not _notes(w), w
        assert any("tb_orientstyle" in x for x in w), w
        assert tda._axis(f, "y").axis_label_orientation == 0.0

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_x_title_turns(self, mode):
        f, w = _figs(mode, {"xtitle": '"X", orientation(vertical)'})
        assert not _notes(w), w
        assert tda._axis(f, "x").axis_label_orientation == pytest.approx(
            _fixture_angle("ax13_xor_vertical", "X"))

    def test_the_word_table(self):
        # "hor" is read by twoway (ax13_or_hor draws upright) and missing
        # from the table: left for the style-word reader (WP-45 ST-1),
        # which widens _dash_tb_orient's one lookup.
        for word in _WORDS:
            if word == "hor":
                continue
            assert dr._dash_tb_orient(word) == pytest.approx(
                _fixture_angle("ax13_or_" + word, "Y"), abs=1e-9)
        assert dr._dash_tb_orient("bogus") is None


def _along(key, letter, s):
    """Which end of the axis twoway moved the title to: "start" (bottom
    or left), "end" (top or right) or "center"."""
    base = _text("ax13_plain", "Y" if letter == "y" else "X")
    t = _text(key, s)
    if t["anchor"] != base["anchor"]:
        # justification() changes the anchor and not the glyph's place:
        # the text is its own box's width.
        return "center"
    if letter == "y":
        d = t["y"] - base["y"]
        return "center" if abs(d) < 1 else ("end" if d < 0 else "start")
    d = t["x"] - base["x"]
    return "center" if abs(d) < 1 else ("end" if d > 0 else "start")


_PLACED = [("ax13_place_" + p, "y", f"placement({p})")
           for p in ("n", "s", "e", "w", "ne", "sw")] + \
          [("ax13_xplace_" + p, "x", f"placement({p})")
           for p in ("e", "w", "n")] + \
          [("ax13_yjust_" + j, "y", f"justification({j})")
           for j in ("left", "center", "right")] + \
          [("ax13_xjust_" + j, "x", f"justification({j})")
           for j in ("left", "right")] + \
          [("ax13_align_" + a, "y", f"alignment({a})")
           for a in ("top", "bottom")] + \
          [("ax13_bmargin_large", "y", "bmargin(large)")]


class TestPlacement:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("key,letter,sub", _PLACED)
    def test_each_value(self, mode, key, letter, sub):
        s = "Y" if letter == "y" else "X"
        f, w = _figs(mode, {f"{letter}title": f'"{s}", {sub}'})
        assert not _notes(w), w
        ax = tda._axis(f, letter)
        assert ax.axis_label_align == _along(key, letter, s), key
        # No box: the axis keeps its own title.
        assert ax.axis_label == s and not _boxes(f)

    @pytest.mark.parametrize("mode", _MODES)
    def test_linegap(self, mode):
        a0 = _text("ax13_two_lines", "A")
        b0 = _text("ax13_two_lines", "B")
        a = _text("ax13_linegap_5", "A")
        b = _text("ax13_linegap_5", "B")
        step = (b["x"] - a["x"]) / a["size"]
        assert step > (b0["x"] - a0["x"]) / a0["size"] + 1
        f, w = _figs(mode, {"ytitle": '`"A"\' `"B"\', linegap(5)'})
        assert not _notes(w), w
        assert tda._axis(f, "y").axis_label_text_line_height == \
            pytest.approx(step, rel=0.02)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("key,sub", [("ax13_margin_l5", "margin(l+5)"),
                                         ("ax13_margin_large",
                                          "margin(large)")])
    def test_margin(self, mode, key, sub):
        # The title's outer side is how far twoway moved the title; its
        # inner side the rest of the plot region's move.
        p0 = _T["ax13_plain"]["plotregion"]["left"]
        x0 = _text("ax13_plain", "Y")["x"]
        outer = (_text(key, "Y")["x"] - x0) * _PX
        inner = (_T[key]["plotregion"]["left"] - p0) * _PX - outer
        f, w = _figs(mode, {"ytitle": f'"Y", {sub}'})
        assert not _notes(w), w
        (lab,) = _boxes(f)
        assert _side_of(f, lab) == "left"
        sides = dr._dash_axis_title_screen_pad(lab.padding, lab.angle)
        assert sides["left"] == pytest.approx(outer, abs=1)
        assert sides["right"] == pytest.approx(inner, abs=1)
        assert lab.background_fill_color is None
        assert lab.border_line_color is None


class TestBox:
    @pytest.mark.parametrize("mode", _MODES)
    def test_left_box(self, mode):
        rects = _T["ax13_box_colours"]["rects"]
        assert any(r["fill"] == "#ff0000" for r in rects)
        assert any(r["stroke"] == "#0000ff" for r in rects)
        f, w = _figs(mode, {"ytitle": '"Y", box fcolor(red) lcolor(blue) '
                                      'lwidth(thick)'})
        assert not _notes(w), w
        ax = tda._axis(f, "y")
        assert not ax.axis_label
        (lab,) = _boxes(f)
        assert type(lab).__name__ == "Label"
        assert lab.text == "Y"
        assert _side_of(f, lab) == "left"
        # Directly outside its axis.
        assert f.left.index(lab) == f.left.index(ax) + 1
        assert lab.angle == pytest.approx(_fixture_angle("ax13_box", "Y"))
        assert lab.background_fill_color == "#ff0000"
        assert lab.border_line_color == "#0000ff"
        assert lab.border_line_width > 1

    @pytest.mark.parametrize("mode", _MODES)
    def test_plain_box_takes_the_text_box_fill(self, mode):
        plain = {r["fill"] for r in _T["ax13_plain"]["rects"]}
        fills = [r["fill"] for r in _T["ax13_box"]["rects"]
                 if r["fill"] not in plain | {"none", None}]
        f, w = _figs(mode, {"ytitle": '"Y", box'})
        assert not _notes(w), w
        (lab,) = _boxes(f)
        assert lab.background_fill_color == fills[0]
        assert lab.border_line_color is not None

    @pytest.mark.parametrize("mode", _MODES)
    def test_x_box(self, mode):
        f, w = _figs(mode, {"xtitle": '"X", box'})
        assert not _notes(w), w
        (lab,) = _boxes(f)
        assert _side_of(f, lab) == "below"
        assert lab.angle == 0.0
        assert not tda._axis(f, "x").axis_label

    @pytest.mark.parametrize("mode", _MODES)
    def test_right_box(self, mode):
        # twoway draws the box round the axis-2 title, right of the plot.
        r = [x for x in _T["ax13_box_ax2"]["rects"]
             if x["fill"] == "#d9e6eb"][0]
        assert r["x"] > _T["ax13_box_ax2"]["plotregion"]["right"]
        f, w = _figs(mode, {"ytitle2": '"Y", box'}, _Y2)
        assert not _notes(w), w
        ax = tda._axis(f, "y", "y2")
        (lab,) = _boxes(f)
        assert _side_of(f, lab) == "right"
        assert f.right.index(lab) == f.right.index(ax) + 1
        assert lab.angle == pytest.approx(math.pi / 2)
        assert not ax.axis_label

    @pytest.mark.parametrize("mode", _MODES)
    def test_width_and_height_fix_the_box(self, mode):
        f, w = _figs(mode, {"ytitle": '"Y", box width(20) height(10)'})
        assert not _notes(w), w
        (lab,) = _boxes(f)
        cbs = [c for cs in f.js_property_callbacks.values() for c in cs
               if getattr(c, "code", None) == dr._DASH_TEXT_BOX_JS]
        assert cbs and any(it[0] is lab for it in cbs[0].args["items"])

    @pytest.mark.parametrize("mode", _MODES)
    def test_bexpand_stays_named(self, mode):
        # D72: bexpand is named on every title, the box drawn without it.
        f, w = _figs(mode, {"ytitle": '"Y", box bexpand'})
        assert any("bexpand" in x for x in _notes(w)), w
        assert len(_boxes(f)) == 1

    def test_the_box_title_is_not_an_axis(self):
        f, _w = _figs("saved", {"ytitle": '"Y", box'})
        prim = list(dr._dash_primary_axes(f.yaxis, "y_range_name"))
        assert prim and all(type(a).__name__ != "Label" for a in prim)


class TestTstyle:
    @pytest.mark.parametrize("mode", _MODES)
    def test_heading(self, mode):
        want = (_text("ax13_tstyle_heading", "Y")["size"]
                / _text("ax13_plain", "Y")["size"])
        f0, _ = _figs(mode, {"ytitle": '"Y"'})
        f, w = _figs(mode, {"ytitle": '"Y", tstyle(heading)'})
        assert not _notes(w), w
        T = dr.OptionTranslator
        a = T.css_to_pt(tda._axis(f, "y").axis_label_text_font_size)
        b = T.css_to_pt(tda._axis(f0, "y").axis_label_text_font_size)
        assert a / b == pytest.approx(want, rel=0.03)


#: The turned screen rectangle of every Label tagged dash_axis_title_box,
#: and the plot frame, in canvas px (computed as the next paint computes
#: it: virtual time paints no frames).
_BOX_JS = """(() => {
  const out = {labels: [], frame: null};
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      const f = v.frame.bbox;
      out.frame = [f.x0, f.y0, f.x1, f.y1];
      for (const [m, rv] of v.renderer_views) {
        if (!(m.tags || []).includes("dash_axis_title_box")) continue;
        rv.compute_geometry();
        const r = rv._rect;
        if (!r) continue;
        const a = -(m.angle || 0), ca = Math.cos(a), sa = Math.sin(a);
        const xs = [], ys = [];
        for (const lx of [-r.anchor.x * r.width, (1 - r.anchor.x) * r.width])
          for (const ly of [-r.anchor.y * r.height,
                            (1 - r.anchor.y) * r.height]) {
            xs.push(r.sx + lx * ca - ly * sa);
            ys.push(r.sy + lx * sa + ly * ca);
          }
        out.labels.push([Math.min(...xs), Math.min(...ys), Math.max(...xs),
                         Math.max(...ys)]);
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return JSON.stringify(out);
})()"""


def _chrome():
    import responsive_probe
    return responsive_probe.find_chrome()


@pytest.mark.release
@pytest.mark.skipif(_chrome() is None, reason="headless Chrome is not "
                    "installed (set DASH_CHROME); a skip is not a pass")
class TestBoxInChrome:
    """The side-panel Label as BokehJS lays it out on a saved page (the
    served app needs a server, which the tests do not start)."""

    def _measure(self, tmp_path, go, plots=None):
        import range_probe
        spec = tda._spec(plots or _SC, go, formats=_FORMATS)
        _tag, sp, dp = tda._write(spec, "auto")
        page = os.path.join(str(tmp_path), "o%d.html" % _tag)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(sp, dp, page).render()
        if not os.path.exists(page):
            with open(page, "w", encoding="utf-8") as fh:
                fh.write(html)
        with range_probe.RangeProbe(page) as p:
            got = json.loads(p._eval(_BOX_JS))
            assert p.js_errors() == []
        return got

    def test_right_box_in_chrome(self, tmp_path):
        got = self._measure(tmp_path, {"ytitle2": '"Price", box'}, _Y2)
        (b,) = got["labels"]
        f = got["frame"]
        # Right of the plot, turned: taller than wide, level with it.
        assert b[0] > f[2]
        assert b[3] - b[1] > b[2] - b[0]
        assert b[1] > f[1] and b[3] < f[3]

    def test_left_margin_in_chrome(self, tmp_path):
        # margin(l+5): the slot starts at the graph's edge and holds the
        # 144-unit margin outside the text (ax13_margin_l5).
        got = self._measure(tmp_path, {"ytitle": '"Y", margin(l+5)'})
        (b,) = got["labels"]
        assert b[2] <= got["frame"][0]
        assert b[0] == pytest.approx(0, abs=1)
        got0 = self._measure(tmp_path, {"ytitle": '"Y", margin(l+0)'})
        (b0,) = got0["labels"]
        assert (b[2] - b[0]) - (b0[2] - b0[0]) == pytest.approx(
            144 * _PX, abs=1)


def _right_y_axes(f):
    return [a for a in f.right if type(a).__name__.endswith("Axis")
            and a.axis_label]


_RIGHT = [("pic12_y2", {}, _Y2, "", "Price"),
          ("pic12_econ", {}, None, "economist", "Mileage (mpg)"),
          ("pic12_alt", {"yscale": "alt"}, None, "", "Mileage (mpg)"),
          ("pic12_y3", {}, [P("scatter", "mpg", "weight"),
                            P("scatter", "price", "weight", yaxis=3)],
           "", "Price")]


class TestRightTitles:
    """PIC-12: twoway writes every right-hand y title rotate(-90), reading
    upward (pic12_*); BokehJS turns a "parallel" title on the right to
    read downward."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("key,go,plots,scheme,title", _RIGHT,
                             ids=[r[0] for r in _RIGHT])
    def test_upward(self, mode, key, go, plots, scheme, title):
        r = next(t for t in _T[key]["texts"] if t["text"] == title
                 and t["x"] > _T[key]["plotregion"]["right"])
        assert r["rotate"] == -90.0
        f, _w = _figs(mode, go, plots, scheme=scheme)
        axs = _right_y_axes(f)
        assert axs
        for a in axs:
            assert a.axis_label_orientation == pytest.approx(
                _fixture_angle(key, title)), key

    @pytest.mark.parametrize("mode", _MODES)
    def test_left_is_unchanged(self, mode):
        f, _w = _figs(mode, {}, _Y2)
        for side in ("left", "below", "above"):
            for a in getattr(f, side):
                if type(a).__name__.endswith("Axis"):
                    assert a.axis_label_orientation == "parallel", side

    @pytest.mark.parametrize("mode", _MODES)
    def test_explicit_orientation_wins(self, mode):
        assert _text("pic12_y2orient", "P")["rotate"] is None
        f, w = _figs(mode, {"ytitle2": '"P", orientation(horizontal)'}, _Y2)
        assert not _notes(w), w
        (a,) = _right_y_axes(f)
        assert a.axis_label_orientation == 0.0
