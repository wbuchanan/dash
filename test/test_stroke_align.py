"""WP-47 section 47-03: outline alignment of markers and dots as twoway
draws it (basic:PT-6, basic:PT-5).

twoway draws a marker of size ``S`` with an outline ``w`` wide as a fill
circle of diameter ``S + w`` and strokes the ring on the circle of diameter
``S`` under ``inside`` (the scheme's default), on the fill's edge under
``center`` and half a width beyond it under ``outside``
(test/fixtures/stroke_align_truth.json M01-M04 and D01-D04, under stcolor
and s2color, from scripts/extract_stroke_align_truth.do).  Its outer
diameter is ``S + w``, ``S + 2w`` and ``S + 3w``.  Bokeh strokes the
outline centred on the marker's edge, so dash draws the marker at ``S``,
``S + w`` and ``S + 2w``.  An alignment word twoway does not know is noted
(U02, U03) and drawn as the default.
"""
import json
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import dash_render as dr  # noqa: E402
from conftest import drawn_renderers  # noqa: E402
from test_varlabel_options import figs, sc  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "stroke_align_truth.json"),
          encoding="utf-8") as _fh:
    T = json.load(_fh)

MODES = ("saved", "served")
ALIGNS = ("inside", "center", "outside")
_NOTE = ("dash: named style bogus not found in class alignstroke, default "
         "attributes used")


def _k(key):
    """twoway's outer diameter less its nominal size, in outline widths:
    the fill circle is ``S + w`` across and the ring's outer edge is the
    measured ring radius plus half a width (fixture *key*)."""
    m = T[key]
    w = m["stroke_width"]
    nominal = 2 * m["fill_r"] - w
    outer = 2 * (m["ring_r"] + w / 2)
    return (outer - nominal) / w


def _scatters(fs, dots=False):
    out = []
    for f in fs:
        for r in drawn_renderers(f):
            if type(getattr(r, "glyph", None)).__name__ != "Scatter":
                continue
            if "dash_cap" in (r.tags or []) or dr._dash_is_swatch(r):
                continue
            if ("dash_dots" in (r.tags or [])) == dots:
                out.append(r)
    return out


def _dot(**o):
    return {"type": "dot", "yvar": "mpg", "xvar": "weight", "options": o}


class TestTheRule:

    @pytest.mark.parametrize("align, want", [
        ("inside", -2.0), ("center", 0.0), ("outside", 2.0),
        ("bogus", -2.0), ("", -2.0)])
    def test_grow(self, align, want):
        assert dr._dash_stroke_grow(align, 4.0) == want
        assert dr._dash_stroke_grow(align, 0.0) == 0.0
        assert dr._dash_stroke_grow(align, float("nan")) == 0.0
        assert dr._dash_stroke_grow(align, None) == 0.0

    def test_align_reads_the_option_then_the_scheme(self):
        class _S:
            def alignstroke(self, role):
                return "outside" if role == "dotmark" else "center"
        assert dr._dash_stroke_align({"mlalign": "center"}, "mlalign") \
            == "center"
        assert dr._dash_stroke_align({"mlalign": "bogus"}, "mlalign") \
            == "inside"
        assert dr._dash_stroke_align({}, "dlalign", _S(), "dotmark") \
            == "outside"
        assert dr._dash_stroke_align({"dlalign": "x"}, "dlalign", _S(),
                                     "p") == "center"
        assert dr._dash_stroke_align(None, "lalign") == "inside"

    @pytest.mark.parametrize("scheme", ["s2color", "stcolor"])
    def test_scheme_default(self, scheme):
        # twoway's own schemes: every entry is inside (stcolor includes
        # s2color's), and so is a scheme with no entry.
        k = "s2" if scheme == "s2color" else "st"
        for role in ("p", "dotmark", "histogram"):
            want = T["schemes"][k].get(role, T["schemes"]["s2"][role])
            assert dr.SchemeParser(scheme).alignstroke(role) == want
        sp = dr.SchemeParser("s2color")
        sp._props = dict(sp._props, **{"alignstroke p": "outside",
                                       "alignstroke dotmark": "center",
                                       "alignstroke ci": "sideways"})
        assert sp.alignstroke("dotmark") == "center"
        assert sp.alignstroke("p3") == "outside"
        assert sp.alignstroke("ci") == "outside"


class TestMarkers:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("n, align", [(1, "inside"), (2, "center"),
                                          (3, "outside"), (4, "")])
    def test_outer_diameter(self, mode, n, align, tmp_path):
        opts = {"mlwidth": "vthick"}
        base = _scatters(figs(mode, tmp_path, [sc(**opts)])[0])[0].glyph
        if align:
            opts["mlalign"] = align
        fs, notes = figs(mode, tmp_path, [sc(**opts)])
        (r,) = _scatters(fs)
        g = r.glyph
        w = float(g.line_width)
        for k in ("st", "s2"):
            want = base.size + w + (_k("M%02d_%s" % (n, k)) - 1) * w
            assert g.size + w == pytest.approx(want, abs=0.01), (k, align)
        assert not [m for m in notes if "alignstroke" in m
                    or "mlalign" in m]

    @pytest.mark.parametrize("mode", MODES)
    def test_weighted_field_size_is_transformed(self, mode, tmp_path):
        o = {"weight": "aweight", "wexp": "price", "mlalign": "outside"}
        (r,) = _scatters(figs(mode, tmp_path, [sc(**o)])[0])
        spec = r.glyph.size
        assert dr._dash_spec_field(spec), spec
        tf = getattr(spec, "transform", None)
        assert type(tf).__name__ == "CustomJSTransform", spec
        assert tf.args["g"] == pytest.approx(2 * float(r.glyph.line_width))
        # The column keeps twoway's weighted sizes; the default (inside)
        # draws the column itself, moved nothing (g 0).
        # Flipped (WP-47 DG-12): "inside draws the bare column" was wrong
        # because twoway draws a size-zero weighted marker as its minimal
        # dot, which BokehJS paints only through the transform's floor.
        (p,) = _scatters(figs(mode, tmp_path, [sc(
            weight="aweight", wexp="price")])[0])
        assert dr._dash_spec_field(p.glyph.size) == "__dash_wsize"
        assert p.glyph.size.transform.args["g"] == 0.0

    def test_no_outline_no_move(self, tmp_path):
        (r,) = _scatters(figs("saved", tmp_path, [sc(
            mlalign="outside", mlcolor="none")])[0])
        (b,) = _scatters(figs("saved", tmp_path, [sc()])[0])
        assert r.glyph.size == b.glyph.size


class TestDots:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("n, align", [(1, "inside"), (2, "center"),
                                          (3, "outside"), (4, "")])
    def test_dlalign_sizes(self, mode, n, align, tmp_path):
        base = _scatters(figs(mode, tmp_path, [_dot()])[0], dots=True)
        o = {"dlalign": align} if align else {}
        fs, notes = figs(mode, tmp_path, [_dot(**o)])
        dots = _scatters(fs, dots=True)
        assert dots and len(dots) == len(base)
        for d, b in zip(dots, base):
            w = float(d.glyph.line_width)
            assert w > 0
            # The size the dots were given (vtiny, 0.384 px), before the
            # alignment and the 1 px floor (D-18c).  Flipped (WP-47
            # PIC-16): the floor is on the dot as drawn, fill plus
            # outline, at least 1 px.
            nom = d.glyph._dash_stroke_nominal[0]
            assert b.glyph._dash_stroke_nominal[0] == nom
            for k in ("st", "s2"):
                want = nom + (_k("D%02d_%s" % (n, k)) - 1) * w
                assert d.glyph.size == pytest.approx(
                    want if want + w >= 1.0 else 1.0 - w, abs=0.01)
        assert not [m for m in notes if "dlalign" in m
                    or "alignstroke" in m]


class TestSilence:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("align", ALIGNS)
    def test_no_note(self, mode, align, tmp_path):
        for plot in (sc(mlalign=align), _dot(mlalign=align),
                     _dot(dlalign=align)):
            _, notes = figs(mode, tmp_path, [plot])
            assert not [m for m in notes if "align" in m], (plot, notes)

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_mlalign_word(self, mode, tmp_path):
        assert T["U02"]["rc"] == 0
        assert [ln.strip("()").replace("note:  ", "")
                for ln in T["U02"]["lines"]] == [_NOTE[len("dash: "):]]
        fs, notes = figs(mode, tmp_path, [sc(mlalign="bogus")])
        assert [m for m in notes if "alignstroke" in m] == [_NOTE]
        (r,) = _scatters(fs)
        (b,) = _scatters(figs(mode, tmp_path, [sc()])[0])
        assert r.glyph.size == b.glyph.size

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_dlalign_word(self, mode, tmp_path):
        # twoway notes it once and draws the default (U03).
        assert T["U03"]["rc"] == 0
        assert len(T["U03"]["lines"]) == 1
        assert "not found in class alignstroke" in T["U03"]["lines"][0]
        fs, notes = figs(mode, tmp_path, [_dot(dlalign="bogus")])
        assert [m for m in notes if "alignstroke" in m] == [_NOTE]
        dots = _scatters(fs, dots=True)
        base = _scatters(figs(mode, tmp_path, [_dot()])[0], dots=True)
        assert [d.glyph.size for d in dots] == [b.glyph.size for b in base]


# ---------------------------------------------------------------------------
# basic:PT-4: bars, histogram bins and rbar
# ---------------------------------------------------------------------------
from js_runner import requires_node, run_js  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _expr_js(args, data, n):
    """Run ``_DASH_STROKE_EXPR_JS`` under node over *data* with *args*, as
    BokehJS runs a ``CustomJSExpr``: a generator over the source."""
    names = sorted(args)
    return run_js(
        "const GF = Object.getPrototypeOf(function*(){}).constructor;\n"
        "const names = %s, vals = %s;\n"
        "const src = {data: %s, get_length() { return %d; }};\n"
        "const f = new GF(...names, '\"use strict\";\\n' + %s);\n"
        "const r = f.apply(src, names.map((k) => vals[k])).next().value;\n"
        "console.log(JSON.stringify(Array.from(r, (v) => "
        "Number.isFinite(v) ? v : null)));\n"
        % (json.dumps(names), json.dumps(args), json.dumps(data), n,
           json.dumps(dr._DASH_STROKE_EXPR_JS)))


def _fig(xr=(0, 10), yr=(0, 10), size=400):
    """A figure as the outline expressions read it: its inner size and
    its ranges (read by name when they run)."""
    return {"inner_width": size, "inner_height": size,
            "x_range": {"start": xr[0], "end": xr[1]},
            "y_range": {"start": yr[0], "end": yr[1]}}


def _quad_args(which, g, xlog=False, ylog=False, xr=(0, 10), yr=(0, 10)):
    return {"fig": _fig(xr, yr), "xname": "default", "yname": "default",
            "gl": None, "g": g, "which": which,
            "kind": "quad", "xlog": xlog, "ylog": ylog, "wscr": False,
            "hscr": False, "tf": {},
            "sp": {"left": ["l", None], "right": ["r", None],
                   "top": ["t", None], "bottom": ["b", None]}}


def _outlines(fs):
    return [r for f in fs for r in f.renderers
            if "dash_outline" in (r.tags or [])]


class TestRects:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["bar", "histogram", "rbar"])
    def test_outline_renderer(self, mode, ptype, tmp_path):
        fs, notes = figs(mode, tmp_path, [plot_for(ptype, {})])
        (out,) = _outlines(fs)
        fill = out._dash_outline_of
        assert out.data_source is fill.data_source
        assert type(out.glyph).__name__ == "Quad"
        assert fill.glyph.line_alpha == 0
        assert out.glyph.fill_alpha == 0
        assert out.glyph.line_width == fill.glyph.line_width
        assert out.glyph.line_color == fill.glyph.line_color
        for k in ("left", "right", "top", "bottom"):
            e = getattr(out.glyph, k).expr
            assert e.code == dr._DASH_STROKE_EXPR_JS
            assert e.args["which"] == k
            assert e.args["g"] == pytest.approx(
                -float(out.glyph.line_width) / 2)
        f = fs[0]
        rs = list(f.renderers)
        assert rs.index(out) == rs.index(fill) + 1
        # The legend item draws the fill and the stroke.
        for leg in f.legend:
            for it in leg.items:
                if fill in it.renderers:
                    assert out in it.renderers
        # center: the fill keeps its stroke and no outline is added.
        fs, _ = figs(mode, tmp_path, [plot_for(ptype, {"lalign": "center"})])
        assert not _outlines(fs)

    @requires_node
    @pytest.mark.parametrize("align", ALIGNS)
    def test_inset_in_node(self, align):
        g = dr._dash_stroke_grow(align, 8.0)
        data = {"l": [2.0], "r": [4.0], "t": [6.0], "b": [1.0]}
        got = {k: _expr_js(_quad_args(k, g), data, 1)[0]
               for k in ("left", "right", "bottom", "top")}
        u = g * 10 / 400
        assert got["left"] == pytest.approx(2.0 - u)
        assert got["right"] == pytest.approx(4.0 + u)
        assert got["bottom"] == pytest.approx(1.0 - u)
        assert got["top"] == pytest.approx(6.0 + u)

    def test_fixture_rule(self):
        # twoway's outline rect against its fill rect: half a width in,
        # on it, half a width out, on bars, bins, rbar and log axes.
        for k in ("st", "s2"):
            for base, n0 in (("A", 1), ("A", 5), ("A", 9)):
                for j, align in enumerate(ALIGNS + ("",)):
                    m = T["%s%02d_%s" % (base, n0 + j, k)]
                    f, o, w = m["fill"], m["outline"], m["stroke_width"]
                    want = dr._dash_stroke_grow(align or "inside", w)
                    assert f["x"] - o["x"] == pytest.approx(want, abs=0.02)
                    assert (o["x"] + o["w"]) - (f["x"] + f["w"]) == \
                        pytest.approx(want, abs=0.02)
                    assert f["y"] - o["y"] == pytest.approx(want, abs=0.02)
            for key in ("A22_" + k, "A23_" + k):
                m = T[key]
                assert m["outline"]["x"] - m["fill"]["x"] == \
                    pytest.approx(m["stroke_width"] / 2, abs=0.02)
                assert m["outline"]["y"] - m["fill"]["y"] == \
                    pytest.approx(m["stroke_width"] / 2, abs=0.02)

    @requires_node
    def test_log_axis(self):
        g = -4.0
        data = {"l": [2.0], "r": [4.0], "t": [10.0], "b": [0.0]}
        args = _quad_args("top", g, ylog=True, yr=(1, 100))
        (top,) = _expr_js(args, data, 1)
        assert top == pytest.approx(10 * math.exp(g * math.log(100) / 400))
        (bot,) = _expr_js(dict(args, which="bottom"), data, 1)
        assert bot == 0.0
        (nan,) = _expr_js(args, {"l": [2.0], "r": [4.0], "t": [None],
                                 "b": [1.0]}, 1)
        assert nan is None

    @requires_node
    def test_narrow_bar(self):
        # twoway keeps the crossed edges (A24): the outline rect runs from
        # the right edge less half a width to the left edge plus half.
        for k in ("st", "s2"):
            m = T["A24_" + k]
            f, o, w = m["fill"], m["outline"], m["stroke_width"]
            assert f["w"] < w
            assert o["x"] == pytest.approx(f["x"] + f["w"] - w / 2, abs=0.02)
            assert o["w"] == pytest.approx(w - f["w"], abs=0.02)
        g = -8.0
        data = {"l": [5.0], "r": [5.1], "t": [6.0], "b": [1.0]}
        lft = _expr_js(_quad_args("left", g), data, 1)[0]
        rgt = _expr_js(_quad_args("right", g), data, 1)[0]
        assert lft == pytest.approx(5.0 + 0.2) and rgt == pytest.approx(4.9)

    @requires_node
    def test_screen_width_and_vbar(self):
        args = {"fig": _fig(), "xname": "default", "yname": "default",
                "gl": None, "g": -2.0, "kind": "vbar", "xlog": False, "ylog": False,
                "hscr": False, "tf": {},
                "sp": {"x": ["x", None], "width": ["", 40.0],
                       "top": ["t", None], "bottom": ["", 0.0]}}
        data = {"x": [5.0], "t": [8.0]}
        lft = _expr_js(dict(args, which="left", wscr=True), data, 1)[0]
        assert lft == pytest.approx(5.0 - (20 - 2) * 10 / 400)
        lft = _expr_js(dict(args, which="left", wscr=False,
                            sp=dict(args["sp"], width=["", 1.0])), data, 1)[0]
        assert lft == pytest.approx(4.5 + 2 * 10 / 400)


class TestRcap:

    @pytest.mark.parametrize("mode", MODES)
    def test_round_caps(self, mode, tmp_path):
        # twoway rounds the caps and butts the spine (C01).
        for k in ("st", "s2"):
            assert T["C01_" + k]["linecaps"] == ["butt", "round"]
        fs, _ = figs(mode, tmp_path, [plot_for("rcap", {})])
        caps = [r for f in fs for r in drawn_renderers(f)
                if "dash_cap" in (r.tags or [])]
        spines = [r for f in fs for r in drawn_renderers(f)
                  if type(getattr(r, "glyph", None)).__name__ == "Segment"]
        assert caps and spines
        assert {str(c.glyph.line_cap) for c in caps} == {"round"}
        assert {str(s.glyph.line_cap) for s in spines} == {"butt"}


class TestLalignSilence:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("align", ALIGNS)
    def test_no_note(self, mode, align, tmp_path):
        for ptype in ("bar", "histogram", "rbar", "area", "rarea", "line"):
            _, notes = figs(mode, tmp_path, [plot_for(ptype,
                                                      {"lalign": align})])
            assert not [m for m in notes if "align" in m], (ptype, notes)


# ---------------------------------------------------------------------------
# basic:PT-4: area rings, confidence bands and rarea's bounds
# ---------------------------------------------------------------------------
def _ring_js(xsv, ysv, g, which, mode="ring", other=None, size=400,
             rng=(0, 10)):
    data = {"x": xsv, "y": ysv}
    args = {"fig": _fig(rng, rng, size), "xname": "default",
            "yname": "default", "gl": None, "g": g, "which": which,
            "mode": mode, "xs": ["x", None], "ys": ["y", None], "tx": None,
            "ty": None, "xlog": False, "ylog": False, "osrc": None,
            "oth": None, "toth": None, "othx": False}
    if other is not None:
        data["o"] = other
        args.update(oth=["o", None], osrc="@self")
    names = sorted(args)
    return run_js(
        "const GF = Object.getPrototypeOf(function*(){}).constructor;\n"
        "const names = %s, vals = %s;\n"
        "const src = {data: %s, get_length() { return %d; }};\n"
        "if (vals.osrc === '@self') vals.osrc = src;\n"
        "const f = new GF(...names, '\"use strict\";\\n' + %s);\n"
        "const r = f.apply(src, names.map((k) => vals[k])).next().value;\n"
        "console.log(JSON.stringify(Array.from(r, (v) => "
        "Number.isFinite(v) ? v : null)));\n"
        % (json.dumps(names), json.dumps(args), json.dumps(data), len(xsv),
           json.dumps(dr._DASH_STROKE_RING_JS)))


class TestPolygons:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype, tag, how", [
        ("area", "dash_area_outline", "ring"),
        ("rarea", "dash_rarea_outline", "bound"),
        ("lfitci", "dash_ci_outline", "ring")])
    def test_inset_specs(self, mode, ptype, tag, how, tmp_path):
        fs, _ = figs(mode, tmp_path, [plot_for(ptype, {})])
        outs = [r for f in fs for r in drawn_renderers(f)
                if tag in (r.tags or [])]
        assert outs
        for r in outs:
            for k in ("x", "y"):
                e = getattr(r.glyph, k).expr
                assert e.code == dr._DASH_STROKE_RING_JS
                assert e.args["which"] == k and e.args["mode"] == how
                assert e.args["g"] == pytest.approx(
                    -float(r.glyph.line_width) / 2)
        fs, _ = figs(mode, tmp_path, [plot_for(ptype, {"lalign": "center"})])
        for f in fs:
            for r in drawn_renderers(f):
                if tag in (r.tags or []):
                    assert isinstance(r.glyph.x, str)

    @requires_node
    def test_ring_inset_in_node(self):
        sq_x = [2.0, 8.0, 8.0, 2.0, 2.0, None, 1.0]
        sq_y = [2.0, 2.0, 8.0, 8.0, 2.0, None, 1.0]
        g = -8.0
        u = g * 10 / 400
        gx = _ring_js(sq_x, sq_y, g, "x")
        gy = _ring_js(sq_x, sq_y, g, "y")
        for k, (x0, y0) in enumerate(zip(sq_x[:5], sq_y[:5])):
            sx = -1 if x0 < 5 else 1
            sy = -1 if y0 < 5 else 1
            assert gx[k] == pytest.approx(x0 + sx * u)
            assert gy[k] == pytest.approx(y0 + sy * u)
        assert gx[5] is None and gy[5] is None
        assert gx[6] == 1.0 and gy[6] == 1.0
        # A ring smaller than its inset collapses to its centroid.
        tx = [5.0, 5.2, 5.2, 5.0, 5.0]
        ty = [5.0, 5.0, 5.2, 5.2, 5.0]
        assert _ring_js(tx, ty, g, "x") == [pytest.approx(5.1)] * 5
        # A sharp apex moves at most 4|g|.
        wx = [0.0, 10.0, 0.0, 0.0]
        wy = [5.0, 5.0 + 10 * math.tan(math.radians(10)), 6.0, 5.0]
        mx = _ring_js(wx, wy, -2.0, "x")
        my = _ring_js(wx, wy, -2.0, "y")
        d = math.hypot((mx[1] - wx[1]) * 40, (my[1] - wy[1]) * 40)
        assert d <= 4 * 2.0 + 1e-6
        # Bound mode: an upper bound moves toward the lower one.
        by = _ring_js([1.0, 5.0, 9.0], [8.0, 8.0, 8.0], g, "y", "bound",
                      other=[2.0, 2.0, 2.0])
        assert by == [pytest.approx(8.0 + u)] * 3

    @requires_node
    def test_sloped_edge_is_exact(self):
        # twoway's inside picture is its path stroked twice as wide and
        # clipped to it (A21): a band one width wide inside each edge,
        # which the path moved half a width in, stroked, draws.  Every
        # straight edge of A21's path moves exactly that far.
        import re
        for k in ("st", "s2"):
            m = T["A21_" + k]
            assert m["clip"] == "shape"
            w = m["stroke_width"] / 2
            nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", m["d"])]
            pts = list(zip(nums[0::2], nums[1::2]))
            dedup = [pts[0]] + [p for a, p in zip(pts, pts[1:]) if p != a]
            xs_, ys_ = [p[0] for p in dedup], [p[1] for p in dedup]
            g = -w / 2
            mx = _ring_js(xs_, ys_, g, "x", size=5400, rng=(0, 5400))
            my = _ring_js(xs_, ys_, g, "y", size=5400, rng=(0, 5400))
            # A vertex whose miter is capped (its edges turn by more than
            # about 151 degrees: the 1918 dip, the closing corners) is moved 4|g|, not to the
            # edges' offset lines: its edges are left out.
            ring = dedup[:-1]
            nr = len(ring)

            def _unit(a, b):
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy)
                return (dy / L, -dx / L)
            capped = set()
            for v in range(nr):
                n1 = _unit(ring[v - 1], ring[v])
                n2 = _unit(ring[v], ring[(v + 1) % nr])
                ux, uy = n1[0] + n2[0], n1[1] + n2[1]
                L = math.hypot(ux, uy)
                if L < 1e-9 or (ux * n1[0] + uy * n1[1]) / L < 0.25:
                    capped.add(v)
            assert len(capped) <= 6, capped
            bad = []
            for i in range(len(dedup) - 1):
                (x0, y0), (x1, y1) = dedup[i], dedup[i + 1]
                L = math.hypot(x1 - x0, y1 - y0)
                if i % nr in capped or (i + 1) % nr in capped:
                    continue
                # The moved segment's midpoint lies |g| from the edge.
                cx, cy = (mx[i] + mx[i + 1]) / 2, (my[i] + my[i + 1]) / 2
                dist = abs((x1 - x0) * (y0 - cy) - (x0 - cx) * (y1 - y0)) / L
                if abs(dist - abs(g)) > 0.5:
                    bad.append((i, dist))
            assert not bad, (k, bad[:5])


# ---------------------------------------------------------------------------
# basic:PT-4: the helpers, turned layers, recast bins, dates and moves
# ---------------------------------------------------------------------------
class TestTheHelpers:

    def test_stroke_axis(self):
        from bokeh.models import LogScale, Range1d
        from bokeh.plotting import figure
        f = figure(y_axis_type="log")
        f.extra_x_ranges = {"x2": Range1d(0, 1)}
        f.extra_x_scales = {"x2": LogScale()}
        r = f.quad(left=[1], right=[2], top=[3], bottom=[1])
        assert dr._dash_stroke_axis(f, r, "x") == ("default", False)
        assert dr._dash_stroke_axis(f, r, "y") == ("default", True)
        r.x_range_name = "x2"
        assert dr._dash_stroke_axis(f, r, "x") == ("x2", True)

    def test_stroke_spec(self):
        # A Field with no transform (as the turn writes one) carries
        # bokeh's _UnspecifiedType, which a page cannot serialise: it
        # reads as no transform.
        from bokeh.core.property.vectorization import Field, Value
        from bokeh.models import CustomJSTransform
        t = CustomJSTransform(v_func="return xs")
        assert dr._dash_stroke_spec("top") == (["top", None], None)
        assert dr._dash_stroke_spec(Field("top")) == (["top", None], None)
        assert dr._dash_stroke_spec(Field("top", t)) == (["top", None], t)
        assert dr._dash_stroke_spec(Value(2)) == (["", 2.0], None)
        assert dr._dash_stroke_spec(1.5) == (["", 1.5], None)
        assert dr._dash_stroke_spec(True) == (["", None], None)

    def test_stroke_refresh(self):
        # One callback per source and figure, on the frame's size, each
        # outline glyph's width and each range's ends; its args reach the
        # source only (no glyph, no figure: a filter callback that reaches
        # a range must reach no glyph through it).
        from bokeh.models import ColumnDataSource, Quad
        from bokeh.plotting import figure
        f = figure()
        src = ColumnDataSource({"a": [1]})
        q = Quad()
        cb = dr._dash_stroke_refresh(f, src, (q, None))
        assert cb.code == dr._DASH_STROKE_REFRESH_JS
        assert cb.args == {"srcs": [src]}
        assert dr._dash_stroke_refresh(f, src, (q,)) is cb
        for m, props in ((f, ("inner_width", "inner_height")),
                         (q, ("line_width",)),
                         (f.x_range, ("start", "end")),
                         (f.y_range, ("start", "end"))):
            for p in props:
                assert m.js_property_callbacks["change:" + p] == [cb]
        other = dr._dash_stroke_refresh(f, ColumnDataSource({"a": [1]}))
        assert other is not cb

    def test_stroke_rehook(self):
        # The axis finish replaces the build's ranges: the refresh moves
        # onto the new ones (and a second axis's), once each.
        from bokeh.models import ColumnDataSource, Range1d
        from bokeh.plotting import figure
        f = figure()
        assert dr._dash_stroke_rehook(f) == 0
        cb = dr._dash_stroke_refresh(f, ColumnDataSource({"a": [1]}))
        f.x_range = Range1d(0, 1)
        f.extra_y_ranges = {"y2": Range1d(0, 2)}
        assert dr._dash_stroke_rehook(f) == 4
        assert dr._dash_stroke_rehook(f) == 0
        for rng in (f.x_range, f.y_range, f.extra_y_ranges["y2"]):
            for p in ("start", "end"):
                assert rng.js_property_callbacks["change:" + p] == [cb]

    @pytest.mark.parametrize("mode", MODES)
    def test_the_finished_ranges_redraw_the_outline(self, mode, tmp_path):
        # Built on the build's DataRange1d, the outline reads the range the
        # axis finish made and redraws when it moves; it moves half the
        # outline's width as drawn (the glyph's own, which the page
        # scales), not the build's.
        for ptype in ("bar", "area"):
            fs, _ = figs(mode, tmp_path, [plot_for(ptype, {})])
            f = fs[0]
            assert type(f.x_range).__name__ == "Range1d"
            rs = [r for r in f.renderers if {"dash_outline",
                                             "dash_area_outline"}
                  & set(r.tags or [])]
            assert rs
            for r in rs:
                for k in (("left", "top") if ptype == "bar" else ("x",)):
                    a = getattr(r.glyph, k).expr.args
                    assert "xr" not in a and a["xname"] == "default"
                    assert a["gl"] is r.glyph
                cb = f._dash_stroke_refresh[id(r.data_source)]
                for rng in (f.x_range, f.y_range):
                    for p in ("start", "end"):
                        assert cb in rng.js_property_callbacks[
                            "change:" + p]
                assert cb in r.glyph.js_property_callbacks[
                    "change:line_width"]

    @requires_node
    def test_an_empty_source_gives_one_row(self):
        # BokehJS sizes an empty source (a legend key's copy, data {}) as
        # one row, get_length() ?? 1: both expressions return one value,
        # or the glyph's set_data stops the page ("Size mismatch").
        run = ("const GF = Object.getPrototypeOf(function*(){}).constructor;\n"
               "const names = %s, vals = %s;\n"
               "const src = {data: {}, get_length() { return null; }};\n"
               "const f = new GF(...names, '\"use strict\";\\n' + %s);\n"
               "const r = f.apply(src, names.map((k) => vals[k])).next()"
               ".value;\nconsole.log(JSON.stringify(r.length));\n")
        qa = _quad_args("left", -2.0)
        assert run_js(run % (json.dumps(sorted(qa)), json.dumps(qa),
                             json.dumps(dr._DASH_STROKE_EXPR_JS))) == 1
        ra = {"fig": _fig(), "xname": "default", "yname": "default",
              "gl": None, "g": -2.0, "which": "x", "mode": "ring",
              "xs": ["x", None], "ys": ["y", None], "tx": None, "ty": None,
              "xlog": False, "ylog": False, "osrc": None, "oth": None,
              "toth": None, "othx": False}
        assert run_js(run % (json.dumps(sorted(ra)), json.dumps(ra),
                             json.dumps(dr._DASH_STROKE_RING_JS))) == 1

    @requires_node
    def test_the_drawn_width_moves_the_edge(self):
        # gl's width as drawn (a Value), not the build's g, sets the move.
        g = -2.0
        data = {"l": [2.0], "r": [4.0], "t": [6.0], "b": [1.0]}
        a = dict(_quad_args("left", g), gl={"line_width": {"value": 10.0}})
        (lft,) = _expr_js(a, data, 1)
        assert lft == pytest.approx(2.0 + 5.0 * 10 / 400)


class TestTurnedAndRecast:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["bar", "histogram", "rbar"])
    def test_turned_outline(self, mode, ptype, tmp_path):
        # A turned layer's outline reads the turned fill's own specs, and
        # its page serialises (the turn's Fields carry no transform).
        from bokeh.core.serialization import Serializer
        (out,) = _outlines(figs(mode, tmp_path, [plot_for(
            ptype, {"horizontal": "horizontal"})])[0])
        fill = out._dash_outline_of
        g = fill.glyph
        names = dr._DASH_STROKE_RECT_SPECS[type(g).__name__][1]
        for k in ("left", "right", "top", "bottom"):
            a = getattr(out.glyph, k).expr.args
            assert a["sp"] == {n: dr._dash_stroke_spec(getattr(g, n))[0]
                               for n in names}
            # Flipped (WP-47 PIC-9): a turned bin's count edge (right)
            # keeps its empty-bin transform (_DASH_EMPTY_BIN_JS), which the
            # outline reads through; every other edge has none.
            assert all(v is None or (n == "right" and ptype == "histogram"
                                     and v.v_func == dr._DASH_EMPTY_BIN_JS[1])
                       for n, v in a["tf"].items()), a["tf"]
        assert type(g).__name__ in ("HBar", "Quad")
        Serializer().encode(out)

    @pytest.mark.parametrize("mode", MODES)
    def test_recast_histogram_bars(self, mode, tmp_path):
        # histogram recast(rbar): the bars take the bins' outline once
        # (46-02's restyle), drawn by one outline-only Quad, never twice.
        fs, _ = figs(mode, tmp_path, [{"type": "histogram", "var": "mpg",
                                       "options": {"recast": "rbar",
                                                   "lcolor": "red"}}])
        (out,) = _outlines(fs)
        fill = out._dash_outline_of
        assert type(fill.glyph).__name__ == "VBar"
        assert fill.glyph.line_alpha == 0
        assert out.glyph.line_color == "#ff0000"
        assert out.glyph.left.expr.args["g"] == pytest.approx(
            -float(fill.glyph.line_width) / 2)

    @pytest.mark.parametrize("mode", MODES)
    def test_ciplot_bar_keys_its_outline_with_the_band(self, mode, tmp_path):
        # lfitci ciplot(bar): the band's bars and their outline are one
        # key, the fit line the other, in both modes alike.
        fs, _ = figs(mode, tmp_path, [plot_for("lfitci", {"ciplot": "bar"})])
        (out,) = _outlines(fs)
        items = [[r for r in it.renderers] for leg in fs[0].legend
                 for it in leg.items]
        assert [out._dash_outline_of, out] in items
        assert not [i for i in items if out in i and len(i) != 2]

    def test_histogram_reads_alignstroke_histogram(self, tmp_path,
                                                   monkeypatch):
        # D-47-03.b: the bins' default is the scheme's own entry.
        monkeypatch.setattr(
            dr.SchemeParser, "alignstroke",
            lambda self, role="p": "outside" if role == "histogram"
            else "inside")
        fs, _ = figs("saved", tmp_path, [plot_for("histogram")])
        (out,) = _outlines(fs)
        assert out.glyph.left.expr.args["g"] > 0
        fs, _ = figs("saved", tmp_path, [plot_for("bar")])
        (out,) = _outlines(fs)
        assert out.glyph.left.expr.args["g"] < 0


class TestTheRuleDates:

    @pytest.mark.parametrize("mode", MODES)
    def test_axis_units_reach_the_expression(self, mode, tmp_path):
        # TR-47-03.9: a date drawn on a y axis that is no date axis (a
        # number beside it): the outline expression applies the date
        # transform _dash_layer_in_axis_units gave the fill.
        import test_date_axis_residuals as tda
        for plot, fill_cls, prop in (
                (tda._L("bar", "date", "obs"), "VBar", "top"),
                (tda._L("area", "date", "obs"), "VArea", "y2"),
                ({"type": "rarea", "yvar1": "date", "yvar2": "date",
                  "xvar": "obs", "options": {}}, "VArea", "y1")):
            fig, _w, _o = tda._da_fig(tmp_path, mode, [
                plot, tda._L("scatter", "close", "obs")])
            [fill] = [r for r in fig.renderers
                      if type(r.glyph).__name__ == fill_cls
                      and not dr._dash_is_swatch(r)]
            t = getattr(fill.glyph, prop).transform
            assert type(t).__name__ == "CustomJSTransform"
            outs = [r for r in fig.renderers if {
                "dash_outline", "dash_area_outline",
                "dash_rarea_outline"} & set(r.tags or [])]
            assert outs, plot["type"]
            for r in outs:
                if "dash_outline" in r.tags:
                    assert r.glyph.top.expr.args["tf"]["top"] is t
                else:
                    assert r.glyph.y.expr.args["ty"] is t


@requires_node
class TestAfterASavedMove:

    def test_outline_follows_the_move(self):
        # The outline draws over the fill's own source, so a move's rows
        # are its rows: its edges, run in node over the moved source, are
        # the moved bars' edges moved g px.
        import test_join_order as jo
        import test_mode_parity as tp
        spec = tp._spec([plot_for("bar", {"lwidth": "vthick"})],
                        {"filter": "foreign, type(dropdown)"})
        r = jo._saved_move(spec, tp._DF.copy(), jo._FOREIGN)
        [f] = jo._saved_figs(r)
        (out,) = _outlines([f])
        fill = out._dash_outline_of
        assert out.data_source is fill.data_source
        d = fill.data_source.data
        xs = [float(v) for v in d[fill.glyph.x.field if hasattr(
            fill.glyph.x, "field") else fill.glyph.x]]
        assert len(xs) == int((tp._DF["foreign"] == 1).sum())
        a = dict(out.glyph.left.expr.args)
        a.update(fig=_fig((0, 10000), (0, 100)), gl=None, tf={})
        cols = {k: [None if v != v else float(v) for v in d[k]]
                for k in d if k in {s[0] for s in a["sp"].values()}}
        got = _expr_js(a, cols, len(xs))
        w = a["sp"]["width"]
        width = (w[1] if not w[0] else None)
        for x, gl in zip(xs, got):
            assert gl == pytest.approx(
                x - width / 2 - a["g"] * 10000 / 400)
