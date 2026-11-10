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
from bokeh.models import CustomJS, GlyphRenderer, Plot

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


# ---------------------------------------------------------------------------
# basic:PT-15: the documented plain-type differences (47-06-07)
# ---------------------------------------------------------------------------
def _pt15(mode, plots, df=None, bo=None):
    """The drawing of *plots* over *df* (the parity frame by default)."""
    old = tp._DF
    if df is not None:
        tp._DF = df
    try:
        return _draw(tp._spec(plots, bo or {}), mode)
    finally:
        tp._DF = old


def _finite_xy(r):
    import numpy as np
    d = r.data_source.data
    gx, gy = r.glyph.x, r.glyph.y
    x = np.asarray([np.nan if v is None else v for v in d[gx]], dtype=float)
    y = np.asarray([np.nan if v is None else v for v in d[gy]], dtype=float)
    return int((np.isfinite(x) & np.isfinite(y)).sum())


def _label_rows(fig):
    """How many marker labels the LabelSets of *fig* draw (finite x and
    y)."""
    import numpy as np
    n = 0
    for a in list(fig.center) + list(fig.renderers):
        if type(a).__name__ != "LabelSet":
            continue
        d = a.source.data
        fx, fy = dr._dash_spec_field(a.x), dr._dash_spec_field(a.y)
        if fx not in d or fy not in d:
            continue
        xs = np.asarray([np.nan if v is None else v for v in d[fx]],
                        dtype=float)
        ys = np.asarray([np.nan if v is None else v for v in d[fy]],
                        dtype=float)
        n += int((np.isfinite(xs) & np.isfinite(ys)).sum())
    return n


@pytest.mark.parametrize("mode", MODES)
class TestPT15:
    """twoway's behaviour on the basic:PT-15 cases, measured in
    marker_fidelity_truth.json (scripts/extract_marker_fidelity_truth.do,
    MF_ONLY=PT15): H01/H02 a pc row missing its second point keeps its
    first point's marker and label; A01 mlabangle(400) on pcarrow prints
    twoway's line and draws the arrows without labels; L01 a %td variable
    with value labels labels a labelled value with its label and any
    other value with its number; I01/I02 trailing immediate values are
    dropped in silence."""

    @pytest.mark.parametrize("ptype,probe", [("pcscatter", "H01"),
                                             ("pccapsym", "H02")])
    def test_pc_half_missing(self, mode, ptype, probe):
        import numpy as np
        rec = TRUTH[probe]
        assert rec["rc"] == 0 and rec["lines"] == []
        # five rows, the second missing its second point: 5 + 4 markers
        # and five labels in twoway.
        assert rec["markers"] == 9 and len(rec["labels"]) == 5
        df = tp._DF.iloc[:5].copy()
        df["x2"] = [1.0, np.nan, 3.0, 4.0, 5.0]
        d = _pt15(mode, [plot_for(ptype, {"mlabel": "rep"}, x2var="x2")], df)
        f = d.figures[0]
        mk = [r for r in drawn_renderers(f)
              if type(getattr(r, "glyph", None)).__name__ == "Scatter"
              and not dr._dash_is_swatch(r)]
        assert sum(_finite_xy(r) for r in mk) == rec["markers"]
        assert _label_rows(f) == len(rec["labels"])
        if ptype == "pccapsym":
            segs = [r for r in drawn_renderers(f)
                    if type(getattr(r, "glyph", None)).__name__ == "Segment"]
            want = sum(1 for s in rec["segments"] if s["kind"] == "line")
            got = 0
            for r in segs:
                dd = r.data_source.data
                g = r.glyph
                arr = [np.asarray([np.nan if v is None else v
                                   for v in dd[getattr(g, k)]], dtype=float)
                       for k in ("x0", "y0", "x1", "y1")]
                got += int(np.all([np.isfinite(a) for a in arr], axis=0)
                           .sum())
            assert got == want

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_pcarrow_mlabangle_out_of_range(self, mode, ptype):
        rec = TRUTH["A01"]
        assert rec["rc"] == 0 and rec["labels"] == []
        line = "textangle must be between -360.000 and 360.000"
        assert rec["lines"] == [line]
        d = _pt15(mode, [plot_for(ptype, {"mlabel": "rep",
                                          "mlabangle": "400"})])
        assert _label_rows(d.figures[0]) == 0
        hits = [m for m in d.warnings if "textangle" in m or
                "mlabangle" in m]
        # twoway's line, through the note channel ("dash: ").
        assert hits == ["dash: " + line], d.warnings
        # The arrows are drawn: the same shafts as without labels.
        ref = _pt15(mode, [plot_for(ptype)])
        segs = lambda fig: sorted(type(r.glyph).__name__
                                  for r in drawn_renderers(fig))
        assert segs(d.figures[0]) == segs(ref.figures[0])

    def test_date_mlabel_value_label(self, mode, monkeypatch):
        rec = TRUTH["L01"]
        assert rec["texts"][:5] == ["first", "14977", "third", "14979",
                                    "14980"]
        monkeypatch.setattr(tp, "_VALUE_LABELS", {
            **tp._VALUE_LABELS, "wl": {"15340": "first", "15342": "third"}})
        monkeypatch.setattr(tp, "_LABEL_NAMES",
                            {**tp._LABEL_NAMES, "when": "wl"})
        d = _pt15(mode, [plot_for("scatter", {"mlabel": "when"})],
                  bo={"formats": {"when": "%td"}})
        f = d.figures[0]
        col = dr._DASH_MLABEL_PREFIX + "when"
        texts = None
        for r in f.renderers:
            dd = getattr(getattr(r, "data_source", None), "data", {}) or {}
            if col in dd:
                texts = list(dd[col])
        assert texts is not None
        # twoway's rule on the frame's dates 15340.. (labels on two).
        want = ["first", "15341", "third"] + [str(v) for v in
                                              range(15343, 15350)]
        assert texts == want


class TestPT15Ado:
    def test_no_trailing_note(self):
        """I01/I02: twoway drops trailing immediate values in silence."""
        for k in ("I01", "I02"):
            assert TRUTH[k]["rc"] == 0 and TRUTH[k]["lines"] == []
        with open(os.path.join(os.path.dirname(__file__), "..", "dash.ado"),
                  encoding="utf-8") as fh:
            ado = fh.read()
        assert "ignored '\", st_local(\"_pci_left\")" not in ado
# PIC-9: an empty histogram bin draws nothing
# ---------------------------------------------------------------------------

#: The bar glyphs a histogram layer draws with: its fill and, under
#: lalign(inside) or (outside), its outline-only ``dash_outline`` Quad.
_BAR_GLYPHS = ("Quad", "VBar", "HBar")


def _hist_bars(fig):
    return [r for r in fig.renderers if isinstance(r, GlyphRenderer)
            and type(r.glyph).__name__ in _BAR_GLYPHS
            and not dr._dash_is_swatch(r)]


def _count_edge(r):
    """``(column, transform)`` of the bar edge a bin's count sets -- the
    one whose partner edge is the base: ``top`` upright, ``right`` turned;
    an outline reads its fill's specs (``sp``/``tf`` of its expressions)."""
    g = r.glyph
    for lo, hi in (("bottom", "top"), ("left", "right")):
        v = getattr(g, hi, None)
        e = getattr(v, "expr", None)
        if e is not None and "sp" in (getattr(e, "args", None) or {}):
            sp, tf = e.args["sp"], e.args["tf"]
            if hi in sp and sp[hi][0] and not sp[lo][0]:
                return sp[hi][0], tf.get(hi)
            continue
        if hasattr(g, lo) and isinstance(
                dr._dash_spec_value(getattr(g, lo)), (int, float)) \
                and dr._dash_spec_field(v):
            t = getattr(v, "transform", None)
            return dr._dash_spec_field(v), (
                None if t is None or "Unspecified" in type(t).__name__
                else t)
    raise AssertionError("no count edge on %r" % (r.tags,))


def _run_transform(tf, xs):
    """*tf*'s ``v_func`` and ``func`` over *xs*, compiled as BokehJS's
    CustomJSTransform compiles them (``new Function(...args, "xs", body)``)
    -- each value ``None`` where the result is not finite."""
    names = sorted(tf.args)
    src = """
const xs = %s.map((v) => v === null ? NaN : v);
const vals = [%s];
const v = new Function(%s, "xs", %s)(...vals, xs);
const one = new Function(%s, "x", %s);
const f = (a) => Array.from(a, (t) => Number.isFinite(t) ? t : null);
console.log(JSON.stringify({v: f(v), s: f(xs.map((x) => one(...vals, x)))}));
""" % (json.dumps([None if x != x else float(x) for x in xs]),
       ", ".join(json.dumps(tf.args[k]) for k in names),
       ", ".join(json.dumps(k) for k in names + ["xs"])[:-6],
       json.dumps(tf.v_func),
       ", ".join(json.dumps(k) for k in names + ["x"])[:-5],
       json.dumps(tf.func))
    out = run_js(src)
    assert out["v"] == out["s"], out
    return out["v"]


def _bins_drawn(r):
    """Per bin, does *r* draw it: its count edge after the edge's
    transform is a number (BokehJS's quad draws no bar whose edge is not
    finite)."""
    col, tf = _count_edge(r)
    top = [float(v) for v in r.data_source.data[col]]
    vals = top if tf is None else _run_transform(tf, top)
    return top, [v is not None and v == v for v in vals]


def _strokes(r):
    """Does *r* stroke its bars at all (a width and alpha above 0)?"""
    g = r.glyph
    lw = dr._dash_spec_value(g.line_width)
    la = dr._dash_spec_value(g.line_alpha)
    return bool(lw) and lw > 0 and isinstance(la, (int, float)) and la > 0


class TestEmptyBins:
    """B01 (marker_fidelity_truth.json): twoway's histogram mpg, bin(30)
    draws 21 bars -- 42 elements, a fill and an outline each -- and not
    one element of zero height: an empty bin draws nothing.  dash drew a
    zero-height quad for each empty bin, stroked along the base."""

    def test_twoway_draws_nothing_for_an_empty_bin(self):
        rec = TRUTH["B01"]
        assert rec["rc"] == 0 and rec["zero_height"] == 0
        assert rec["elements"] == 2 * rec["bars"] and rec["bars"] < 30

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("opts", [
        {}, {"lalign": "center"}, {"lalign": "outside"},
        {"horizontal": "horizontal"}, {"discrete": "discrete",
                                       "mwidth": "3"}],
        ids=["inside", "center", "outside", "horizontal", "mwidth"])
    def test_zero_bins_are_unstroked(self, mode, opts):
        """Exactly one renderer of the layer strokes (the outline under
        inside and outside, the fill under center), and it draws no bar
        for an empty bin and every other bar."""
        d = _draw(tp._spec([plot_for("histogram", dict(
            {"bin": "30"} if "discrete" not in opts else {}, **opts))],
            {"scheme": "s2color"}), mode)
        rs = _hist_bars(d.figures[0])
        live = [r for r in rs if _strokes(r)]
        assert len(live) == 1, [r.tags for r in rs]
        top, drawn = _bins_drawn(live[0])
        assert 0.0 in top and any(t > 0 for t in top)
        assert drawn == [t != 0 for t in top], list(zip(top, drawn))

    @pytest.mark.parametrize("mode", MODES)
    def test_the_key_keeps_its_stroke(self, mode):
        """start(0) leaves bin 0 empty, and BokehJS draws a legend item
        with its renderers' visuals at row 0 (GlyphRendererView.
        draw_legend, get_reference_point() ?? 0): the stroke's alpha and
        width stay one number, so the key keeps the bars' outline."""
        from bokeh.models import Legend
        d = _draw(tp._spec([plot_for("histogram", {"bin": "30",
                                                   "start": "0"}),
                            plot_for("scatter")],
                           {"scheme": "s2color"}), mode)
        fig = d.figures[0]
        live = [r for r in _hist_bars(fig) if _strokes(r)]
        assert len(live) == 1
        top, drawn = _bins_drawn(live[0])
        assert top[0] == 0 and not drawn[0]
        items = [it for leg in fig.select(type=Legend) for it in leg.items
                 if live[0] in list(it.renderers or ())]
        assert len(items) == 1

    @pytest.mark.parametrize("mode", MODES)
    def test_after_a_move(self, mode):
        """The saved page's recount (its own filter script, under node)
        and the served recount rewrite the bins' counts: a bin emptied by
        the move draws nothing, and one filled again draws its bar."""
        import js_runner
        spec = tp._spec([plot_for("histogram", {"bin": "6"})],
                        {"scheme": "s2color",
                         "filter": "foreign, type(dropdown)"})
        if mode == "standalone":
            r, _ = tp._standalone(spec)
            fig = list(r.figures.values())[0]
            (w, cb), = [(w, cb) for w, cb in zip(r.filter_widgets,
                                                 r.filter_callbacks)
                        if type(w).__name__ == "Select"]
            session = js_runner.JsSession(r.filter_callbacks)

            def move(label):
                session.set(w, tp._move_widget_value(w, "Select", label))
                session.run(cb)
        else:
            doc, _ = tp._served(spec)
            fig = [p for p in doc.select(dict(type=Plot))
                   if "dash_key_cell" not in (p.tags or [])][0]
            w, = [w for w in tp._widgets_of(doc)
                  if type(w).__name__ == "Select"]

            def move(label):
                tp._fire(w, [v for v, lab in w.options if lab == label][0])
        live, = [r for r in _hist_bars(fig) if _strokes(r)]
        seen = []
        for label in ("Foreign", "Domestic", "All"):
            move(label)
            top, drawn = _bins_drawn(live)
            assert drawn == [t != 0 for t in top], (label, top, drawn)
            seen.append(top)
        # A bin is empty under one move and filled under another.
        assert any(a[i] == 0 and b[i] > 0 or a[i] > 0 and b[i] == 0
                   for a, b in zip(seen, seen[1:])
                   for i in range(min(len(a), len(b))))


# ---------------------------------------------------------------------------
# PIC-10: a dot row for an observation whose y is missing
# ---------------------------------------------------------------------------

def _sp500_45():
    """sysuse sp500 in 1/45 with close missing in row 3, as
    scripts/extract_marker_fidelity_truth.do draws R01/R02 (the dates are
    any 45 distinct days: they place the rows, not the dots)."""
    import numpy as np
    import pandas as pd
    sp = pd.read_csv(os.path.join(_FIX, "data", "sp500.csv")).iloc[:45]
    close = sp["close"].to_numpy(dtype=float).copy()
    close[2] = np.nan
    return pd.DataFrame({"close": close,
                         "date": 14977.0 + np.arange(45, dtype=float)})


def _dot_layer(mode, tmp_path, options):
    import test_bar_range_geometry as bg
    p = {"type": "dot", "yvar": "close", "xvar": "date",
         "options": dict(options)}
    figs, _ = bg._figs(mode, tmp_path, bg._spec([p]), _sp500_45())
    (r,) = [r for r in figs[0].renderers
            if "dash_dots" in (getattr(r, "tags", None) or ())]
    return r


def _js_dots():
    js = dr._DASH_AXIS_FINISH_JS
    a = js.index("function dash_dot_positions(")
    b = js.index("// WP-31 D15:", a)
    return js[a:b]


_DOT_MODES = ("saved", "served")


class TestDotRows:
    """R01/R02 (marker_fidelity_truth.json): twoway's dot close date in
    1/45 (sp500, close missing in row 3) draws 45 rows of 75 dots, 3375 in
    all -- the missing close's row too (yxview_dot_draw.ado
    draw_full_dots loops over every observation, x only) -- and under
    dotextend(no) 1854 dots in 44 rows.  dash drew 44 rows, 3300 dots."""

    @pytest.mark.parametrize("mode", _DOT_MODES)
    def test_count_matches_twoway(self, mode, tmp_path):
        rec = TRUTH["R01"]
        assert rec == {"dots": 3375, "rc": 0, "rows": 45}
        d = _dot_layer(mode, tmp_path, {"ndots": "75"}).data_source.data
        assert (len(d["y"]), len(set(d["x"]))) == (rec["dots"], rec["rows"])

    @pytest.mark.parametrize("mode", _DOT_MODES)
    def test_extend_no_keeps_twoways_count(self, mode, tmp_path):
        rec = TRUTH["R02"]
        d = _dot_layer(mode, tmp_path, {"ndots": "75", "dotextend": "no"}
                       ).data_source.data
        assert (len(d["y"]), len(set(d["x"]))) == (rec["dots"], rec["rows"])

    @pytest.mark.parametrize("mode", _DOT_MODES)
    def test_missing_y_keeps_its_row(self, mode, tmp_path):
        """The missing close's row (its date, 14979) runs the whole scale,
        as every other row does."""
        d = _dot_layer(mode, tmp_path, {}).data_source.data
        runs = {}
        for x, y in zip(d["x"], d["y"]):
            runs.setdefault(float(x), []).append(float(y))
        assert 14979.0 in runs
        assert sorted(runs[14979.0]) == sorted(runs[14977.0])

    def test_extend_words(self):
        """_dash_dot_extends reads dotextend() as twoway's yesno does."""
        for v in ("", "yes", "y", "on", "No", "anything"):
            assert dr._dash_dot_extends({"dotextend": v}), v
        for v in ("n", "no", "off", "f", "fa", "fal", "fals", "false"):
            assert not dr._dash_dot_extends({"dotextend": v}), v
        assert dr._dash_dot_extends(None)

    def test_python_rule(self):
        pos, rows, _ = dr.GlyphMapper._dot_positions(
            0, 1, [0.5, float("nan")], True, 11)
        assert sorted(set(rows.tolist())) == [0, 1]
        assert list(rows).count(1) == list(rows).count(0) > 0

    def test_js_twin_agrees(self):
        """dash_dot_positions and dash_fill_dots (_DASH_AXIS_FINISH_JS):
        under extend the missing value's row is drawn; under
        dotextend(no) it is not; a missing x draws no row either way."""
        src = _js_dots() + r"""
function dash_axis_same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
const out = {};
out.pos = dash_dot_positions(0, 1, [0.5, NaN], true, 11, Infinity)[1];
out.posno = dash_dot_positions(0, 1, [0.5, NaN], false, 11, Infinity)[1];
for (const ext of [true, false]) {
  const ds = {data: {}};
  const ms = {data: {y: [0.5, null, 0.25], x: [1, 2, null]}};
  dash_fill_dots({dots: [{dsrc: 0, msrc: 1, along: "y", across: "x",
                          mfilt: -1, extend: ext, ndots: 11, max: 1e18}]},
                 [ds, ms], 0, 1);
  out[ext ? "fill" : "fillno"] = Array.from(new Set(ds.data.x));
}
console.log(JSON.stringify(out));
"""
        got = run_js(src)
        assert sorted(set(got["pos"])) == [0, 1]
        assert sorted(set(got["posno"])) == [0]
        assert got["fill"] == [1, 2] and got["fillno"] == [1]


# ---------------------------------------------------------------------------
# PIC-16: a dot plot's dot floored on its fill plus outline
# ---------------------------------------------------------------------------

with open(os.path.join(_FIX, "dot_truth.json"), encoding="utf-8") as _fh:
    DOT = json.load(_fh)


class TestDotFloor:
    """dot_truth.json D01 (``dot mpg weight in 1/5``, the default dot):
    twoway strokes a ring of radius 1.49 with a 5.76-wide outline (SVG
    units on its 3960 x 2880 canvas), 8.74 across -- 0.30 rs, 1.52
    outline widths.  dash floored the fill to 1 px before adding the
    0.768 px outline: 1.77 px, 2.30 widths."""

    @pytest.mark.parametrize("mode", MODES)
    def test_outer_diameter(self, mode):
        rec = DOT["D01"]
        (w,) = rec["dot_stroke_width"]
        outer = 2 * rec["dot_r"] + w
        assert outer / (min(rec["canvas"]) / 100) == pytest.approx(
            0.30, abs=0.01)
        d = _draw(tp._spec([plot_for("dot")], {"scheme": "s2color"}), mode)
        (r,) = [r for r in d.figures[0].renderers
                if "dash_dots" in (r.tags or [])]
        g = r.glyph
        drawn = (float(g.size) + float(g.line_width)) / float(g.line_width)
        assert drawn == pytest.approx(outer / w, abs=0.02)

    @pytest.mark.parametrize("mode", MODES)
    def test_at_least_one_pixel(self, mode):
        """With no outline the dot keeps the floor: 1 px across."""
        d = _draw(tp._spec([plot_for("dot", {"dlwidth": "none"})],
                           {"scheme": "s2color"}), mode)
        (r,) = [r for r in d.figures[0].renderers
                if "dash_dots" in (r.tags or [])]
        assert float(r.glyph.size) + float(r.glyph.line_width) \
            == pytest.approx(1.0)


class TestTheHelp:
    """The help's claims PIC-16 and PIC-17 make."""

    _HELP = open(os.path.join(os.path.dirname(__file__), "..", "dash.sthlp"),
                 encoding="utf-8").read()

    @staticmethod
    def _flat(text):
        return " ".join(text.split())

    def test_dot_floor_includes_the_outline(self):
        assert ("a dot is drawn at least one pixel across, its outline "
                "included") in self._flat(self._HELP)

    def test_dot_patterns_whole_pixel(self):
        """PIC-17: Bokeh's DashPattern takes whole pixels, so the
        rounding stays, documented as a difference from twoway."""
        flat = self._flat(self._HELP)
        i = flat.index("{title:Differences from twoway}")
        j = flat.index("{marker subcommands}", i)
        assert ("A line pattern's dashes are drawn to the whole pixel (the "
                "browser library takes whole pixels), so {cmd:dot} and "
                "{cmd:tight_dot} are coarser than {cmd:twoway}'s"
                ) in flat[i:j]
