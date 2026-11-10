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


# ---------------------------------------------------------------------------
# DG-12: zero- and missing-weight markers (47-06-05)
# ---------------------------------------------------------------------------
with open(os.path.join(_FIX, "weighted_markers_truth.json"),
          encoding="utf-8") as _fh:
    WMT = json.load(_fh)


def _weighted(mode, w):
    """The marker renderer of ``scatter mpg weight [aw=wt]`` drawn with the
    weights *w* (one per row of the parity frame)."""
    import numpy as np  # noqa: F401
    old = tp._DF
    tp._DF = old.assign(wt=w)
    try:
        rs, _ = _drawn(mode, [plot_for("scatter", {"weight": "aweight",
                                                   "wexp": "wt"})])
    finally:
        tp._DF = old
    (r,) = rs
    return r


def _size_spec(glyph):
    """(column, CustomJSTransform or None) of a field size spec."""
    s = glyph.size
    if isinstance(s, str):
        return s, None
    return dr._dash_spec_field(s), getattr(s, "transform", None)


def _drawn_sizes(r):
    """The sizes BokehJS draws the renderer's markers at: its size column
    through its transform's v_func, run in node as CustomJSTransform
    compiles it (new Function(...args, "xs", v_func))."""
    col, tf = _size_spec(r.glyph)
    xs = [None if v != v else float(v) for v in r.data_source.data[col]]
    if tf is None or type(tf).__name__ == "UnspecifiedType" \
            or not hasattr(tf, "v_func"):
        return [float("nan") if v is None else v for v in xs]
    args = dict(tf.args)
    src = ("const f = new Function(...%s, 'xs', %s);\n"
           "const xs = %s.map((v) => v === null ? NaN : v);\n"
           "const out = Array.from(f(...%s, xs));\n"
           "console.log(JSON.stringify(out.map((v) => Number.isNaN(v) ? "
           "null : v)));\n" % (json.dumps(list(args)),
                               json.dumps(tf.v_func), json.dumps(xs),
                               json.dumps(list(args.values()))))
    return [float("nan") if v is None else v for v in run_js(src)]


@pytest.mark.parametrize("mode", MODES)
class TestZeroWeights:
    """twoway draws a marker whose weight is zero or missing at size zero:
    a stroked circle of radius 0.25 with the marker's outline width over a
    fill circle half a width wider -- a dot as wide as its outline
    (weighted_markers_truth.json W06_zero, W06_mis: radii 0.25, fill
    radii 4.57, against R_med's 22.03 and 26.35).  dash wrote size 0,
    which BokehJS draws as nothing at all: a stroke round a circle of no
    radius paints no pixel (Chrome, test_csp_browser.py
    test_zero_weights_paint)."""

    @pytest.mark.parametrize("probe", ["W06_zero", "W06_mis"])
    def test_minimal_dot(self, mode, probe):
        import numpy as np
        w = list(tp._DF["price"].astype(float))
        w[0] = 0.0 if probe == "W06_zero" else np.nan
        r = _weighted(mode, w)
        col, _ = _size_spec(r.glyph)
        raw = np.asarray(r.data_source.data[col], dtype=float)
        # The column keeps twoway's size zero (the rescalers' value).
        assert raw[0] == 0.0
        drawn = _drawn_sizes(r)
        lw = float(r.glyph.line_width)
        rec, ref = WMT[probe], WMT["R_med"]
        # px per SVG unit: the layer's nominal size is twoway's nominal
        # ring's diameter.
        k = float(r._dash_wsize_base) / (2.0 * ref["radii"][0])
        want_w = 2.0 * (rec["fill_radii"][0] - rec["radii"][0]) * k
        want_outer = 2.0 * rec["fill_radii"][0] * k
        assert lw == pytest.approx(want_w, abs=0.2)
        # Drawn, not size 0: BokehJS strokes nothing round no radius.
        assert drawn[0] > 0, drawn[:3]
        assert drawn[0] + lw == pytest.approx(want_outer, abs=0.2)
        # The other markers are drawn at their weighted sizes.
        assert np.allclose(drawn[1:], raw[1:])

    def test_negative_still_draws_nothing(self, mode):
        import numpy as np
        w = list(tp._DF["price"].astype(float))
        w[0] = -1.0
        r = _weighted(mode, w)
        assert np.isnan(_drawn_sizes(r)[0])

    def test_js_twin_writes_zero(self, mode):
        """The saved page's rescale after a move writes 0, never NaN, for
        a drawn row whose weight is zero or missing (the transform then
        floors it)."""
        js = dr._FILTER_JS
        body = js[js.index("function dash_weighted_sizes("):
                  js.index("// ---- WP-31 F1: the fit layers' shared helpers")]
        src = body + """
const src = {data: {x: [1, 2, 3, 4], y: [1, 2, 3, NaN],
                    w: [0, null, 4, 9], c: [9, 9, 9, 9]},
             tags: ["dash_wsize=c|w|x|y|6.5|10|"],
             change: {emit: () => {}}};
dash_rescale_wsizes(src);
console.log(JSON.stringify(src.data.c.map((v) => Number.isNaN(v) ? "nan" : v)));
"""
        out = run_js(src)
        assert out[0] == 0 and out[1] == 0
        assert out[2] > 0 and out[3] == "nan"


class TestTheHelpDG12:
    def test_zero_weight_dot(self):
        """HR-19: the help's zero-weight sentence is what dash draws."""
        with open(os.path.join(os.path.dirname(__file__), "..",
                               "dash.sthlp"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        assert ("a zero or missing weight's is drawn at size zero -- a dot "
                "as wide as its outline, as {cmd:twoway} draws it") in text
