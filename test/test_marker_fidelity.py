"""Marker shapes, empty bins, dot rows, zero weights and the dot floor as
twoway draws them (WP-47 47-06: PIC-2, PIC-9, PIC-10, DG-12, PIC-16).

Measured in StataNow 19.5 (`graph export' SVG):

- test/fixtures/symbol_pattern_truth.json (scripts/extract_symbol_pattern_
  truth.do) holds each symbol's path: D is a square on its point, as wide
  as it is tall (sym.D bbox 62.37 x 62.37); V an open three-vertex path
  (closed false, filled false), its wide side 2/3 of its height above the
  marker's centre; + two crossed lines; arrow/a an open head on a shaft,
  arrowf/A a filled closed head on a shaft;
- test/fixtures/marker_fidelity_truth.json (scripts/extract_marker_
  fidelity_truth.do) S17: msymbol(invisible) prints "named style
  invisible not found in class symbol, default attributes used" and draws
  what the default symbol draws.

dash drew Bokeh's diamond (2/3 as wide), a closed inverted triangle for
V, Bokeh's filled 12-vertex plus for +, a triangle with no shaft for the
arrows, and nothing at all for invisible.
"""

import json
import os
import re
import sys

import pytest
from bokeh.models import CustomJS, GlyphRenderer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from js_runner import run_js  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

_FIX = os.path.join(os.path.dirname(__file__), "fixtures")
with open(os.path.join(_FIX, "symbol_pattern_truth.json"),
          encoding="utf-8") as _fh:
    SYM = json.load(_fh)
with open(os.path.join(_FIX, "marker_fidelity_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The marker dash draws each Stata name with (D-47-06.a).
CUSTOM = {
    **dict.fromkeys(("D", "d", "Dh", "dh", "diamond", "smdiamond",
                     "diamond_hollow", "smdiamond_hollow"), "@dash_diamond"),
    **dict.fromkeys(("V", "v", "smv"), "@dash_chevron"),
    **dict.fromkeys(("arrow", "a"), "@dash_arrow"),
    **dict.fromkeys(("arrowf", "A"), "@dash_arrowf"),
    **dict.fromkeys(("+", "plus", "smplus"), "cross"),
}
#: Each shape's height and width at size 1 (r = 1/2): the bodies of
#: dr._DASH_MARKER_DEFS and BokehJS's cross.
SHAPE_HW = {"@dash_diamond": (1.0, 1.0),
            "@dash_chevron": (1.0, 2.0 / 3 ** 0.5),
            "@dash_arrow": (1.0, 2.0 / 3.0),
            "@dash_arrowf": (1.0, 0.5),
            "cross": (1.0, 1.0)}
#: The fixture record of each name (the diamond's long names are D's,
#: the small ones d's; msymbol(v) is smv).
REC = {"diamond": "D", "diamond_hollow": "Dh", "smdiamond_hollow": "dh"}


def _rec(name):
    return SYM["sym." + REC.get(name, name)]


def _drawn(mode, plots, scheme="s2color"):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    rs = [r for r in drawn_renderers(d.figures[0])
          if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)
          and type(r.glyph).__name__ == "Scatter"]
    return rs, d.warnings


def _sc(**o):
    return plot_for("scatter", o)


def _vertices(d):
    """(vertex count, closed) of a fixture path's first subpath."""
    first = re.split(r"(?=M)", d.strip())
    first = [s for s in first if s][0]
    return len(re.findall(r"[ML]", first)), "Z" in first


def _run_body(body, r=10.0):
    """Run one defs body the way BokehJS compiles it (CustomJS
    _compile_function: new Function(...names, cb_obj, cb_data,
    cb_context, code)) with a recording ctx."""
    src = """
const calls = [];
const ctx = {moveTo: (x, y) => calls.push(["M", x, y]),
             lineTo: (x, y) => calls.push(["L", x, y]),
             closePath: () => calls.push(["Z"])};
const visuals = {fill: {apply: () => calls.push(["fill"])},
                 hatch: {apply: () => calls.push(["hatch"])},
                 line: {apply: () => calls.push(["line"])}};
const out = new Function("cb_obj", "cb_data", "cb_context", %s)(
  null, {ctx, i: 0, r: %r, visuals}, {});
console.log(JSON.stringify({calls, out: out === undefined ? null : 1}));
""" % (json.dumps(body), r)
    return run_js(src)


class TestShapes:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("name", sorted(CUSTOM))
    def test_custom_marker(self, mode, name):
        """Each symbol is drawn with its twoway-shaped marker, whose defs
        entry the glyph carries."""
        (r,), _ = _drawn(mode, [_sc(msymbol=name)])
        want = CUSTOM[name]
        assert r.glyph.marker == want
        if want.startswith("@"):
            assert want in dict(r.glyph.defs)
            assert isinstance(dict(r.glyph.defs)[want], CustomJS)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("name", sorted(CUSTOM))
    def test_width_and_height(self, mode, name):
        """Drawn height and width against O's are twoway's within 5%."""
        (o,), _ = _drawn(mode, [_sc(msymbol="O")])
        (r,), _ = _drawn(mode, [_sc(msymbol=name)])
        h1, w1 = SHAPE_HW.get(r.glyph.marker, (None, None))
        assert h1 is not None, r.glyph.marker
        o_d = SYM["sym.O"]["bbox_h"]
        want_h, want_w = _rec(name)["bbox_h"] / o_d, _rec(name)["bbox_w"] / o_d
        got_h = r.glyph.size * h1 / o.glyph.size
        got_w = r.glyph.size * w1 / o.glyph.size
        assert got_h == pytest.approx(want_h, rel=0.05), name
        assert got_w == pytest.approx(want_w, rel=0.05), name

    @pytest.mark.parametrize("mode", MODES)
    def test_plus_is_two_lines(self, mode):
        assert SYM["sym.+"]["tags"] == ["line", "line"]
        assert SYM["sym.+"]["filled"] is False
        for name in ("+", "plus", "smplus"):
            (r,), _ = _drawn(mode, [_sc(msymbol=name)])
            assert r.glyph.marker == "cross", name

    @pytest.mark.parametrize("mode", MODES)
    def test_invisible_is_noted(self, mode):
        """twoway notes invisible and draws the default symbol (S17)."""
        rec = TRUTH["S17"]
        assert rec["rc"] == 0 and rec["equals_default"] is True
        assert rec["note"] == ("named style invisible not found in class "
                               "symbol, default attributes used")
        (r,), msgs = _drawn(mode, [_sc(msymbol="invisible")])
        (ref,), _ = _drawn(mode, [_sc()])
        assert (r.glyph.marker, r.glyph.size, r.glyph.fill_alpha,
                r.glyph.line_alpha) == (ref.glyph.marker, ref.glyph.size,
                                        ref.glyph.fill_alpha,
                                        ref.glyph.line_alpha)
        hits = [m for m in msgs if "invisible" in m and "symbol" in m]
        assert len(hits) == 1, msgs
        assert "invisible" not in dr.OptionTranslator._MARKER_MAP
        assert "invisible" not in dr.OptionTranslator._INVISIBLE_SYMBOLS

    @pytest.mark.parametrize("name,marker", [
        ("D", "@dash_diamond"), ("V", "@dash_chevron"),
        ("arrow", "@dash_arrow"), ("arrowf", "@dash_arrowf")])
    def test_defs_in_node(self, name, marker):
        """Each body, compiled as BokehJS compiles a function-form
        CustomJS, draws the fixture's vertex count and closedness, fills
        exactly the filled shapes and strokes once."""
        out = _run_body(dr._DASH_MARKER_DEFS[marker])
        calls = out["calls"]
        assert out["out"] is None
        rec = _rec(name)
        assert calls.count(["line"]) == 1
        assert (["fill"] in calls) is bool(rec["filled"])
        pts = [c for c in calls if c[0] in ("M", "L")]
        if rec["d"]:
            n, closed = _vertices(rec["d"][0])
            assert (["Z"] in calls) is closed
            assert len(pts) == len(re.findall(r"[ML]", rec["d"][0]))
        else:   # D: a polygon of four corners
            assert len(pts) == 4 and ["Z"] in calls
            xs = [p[1] for p in pts]
            ys = [p[2] for p in pts]
            assert max(xs) - min(xs) == pytest.approx(max(ys) - min(ys))

    def test_chevron_geometry(self):
        """V's three vertices, against its centre, are twoway's: the wide
        side 2/3 of the height above, the point 1/3 below."""
        out = _run_body(dr._DASH_MARKER_DEFS["@dash_chevron"], r=22.03)
        got = [(round(c[1], 1), round(c[2], 1)) for c in out["calls"]
               if c[0] in ("M", "L")]
        nums = [float(v) for v in re.findall(r"-?\d+\.\d+",
                                             SYM["sym.V"]["d"][0])]
        a = SYM["sym.a"]["d"][0]
        cy = (float(re.findall(r"-?\d+\.\d+", a)[3])
              + float(re.findall(r"-?\d+\.\d+", a)[-1])) / 2.0
        cx = nums[2]
        want = [(round(x - cx, 1), round(y - cy, 1))
                for x, y in zip(nums[0::2], nums[1::2])]
        for (gx, gy), (wx, wy) in zip(got, want):
            assert gx == pytest.approx(wx, abs=0.3)
            assert gy == pytest.approx(wy, abs=0.3)

    def test_function_form(self):
        """Every body is a function body (no ES module, which would be
        compiled from a blob: URL the pages' CSP refuses) and every
        CustomJS is module=False."""
        for name in dr._DASH_MARKER_DEFS:
            defs = dr._dash_marker_defs(name)
            assert list(defs) == [name]
            cb = defs[name]
            assert isinstance(cb, CustomJS) and cb.module is False
            assert not [ln for ln in cb.code.splitlines()
                        if ln.lstrip().startswith(("export", "import"))]
            assert "import(" not in cb.code and "Path2D" not in cb.code
        assert dr._dash_marker_defs("circle") == {}
        assert dr._dash_marker_defs("cross") == {}
        a, b = dr._dash_marker_defs("@dash_diamond"), \
            dr._dash_marker_defs("@dash_diamond")
        assert a["@dash_diamond"] is not b["@dash_diamond"]

    @pytest.mark.parametrize("mode", MODES)
    def test_brushed_copies_share_defs(self, mode):
        (r,), _ = _drawn(mode, [_sc(msymbol="D")])
        for attr in ("nonselection_glyph", "muted_glyph"):
            copy = getattr(r, attr)
            assert copy.marker == "@dash_diamond"
            assert "@dash_diamond" in dict(copy.defs), attr

    @pytest.mark.parametrize("mode", MODES)
    def test_hollow_chevron_never_fills(self, mode):
        (r,), _ = _drawn(mode, [_sc(msymbol="V", mfcolor="red")])
        assert r.glyph.fill_alpha == 0.0
        assert "fill.apply" not in dr._DASH_MARKER_DEFS["@dash_chevron"]
        assert "fill.apply" not in dr._DASH_MARKER_DEFS["@dash_arrow"]
