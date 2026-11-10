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
        # draws the column itself.
        (p,) = _scatters(figs(mode, tmp_path, [sc(
            weight="aweight", wexp="price")])[0])
        assert isinstance(p.glyph.size, str)

    def test_no_outline_no_move(self, tmp_path):
        (r,) = _scatters(figs("saved", tmp_path, [sc(
            mlalign="outside", mlcolor="none")])[0])
        (b,) = _scatters(figs("saved", tmp_path, [sc()])[0])
        assert r.glyph.size == b.glyph.size


class TestSilence:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("align", ALIGNS)
    def test_no_note(self, mode, align, tmp_path):
        for plot in (sc(mlalign=align), _dot(mlalign=align)):
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
