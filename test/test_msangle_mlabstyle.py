"""
test_msangle_mlabstyle.py -- msangle() reads anglestyle names, mlabstyle()
styles the labels from the scheme's labelstyle and mlalign() is taken as
twoway takes it (WP-31 E3).

The defect (measured at 5f2684a): ``msangle(forty_five)`` drew the markers
unrotated with a note (the applier read a float only, beside
_dash_anglestyle_degrees); mlabstyle() was undeclared (the generic note)
and mlalign() was named whatever its value.  mwidth was declared and drawn
by WP-31 C2 (S03).

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json): msangle(forty_five) draws the
picture msangle(45) draws; msangle(bogus) is rc 0 with "named style bogus
not found in class anglestyle" and draws msangle(0)'s picture;
mlabstyle(p2) colours the labels p2's label colour (#90353b under
s2color) at 3 o'clock; mlabstyle(bogus) is rc 0 with "named style bogus
not found in class labelstyle" and draws black labels at 12 o'clock;
mlalign(inside) draws the picture without the option, center and outside
two others, mlalign(bogus) is rc 0 with a note in class alignstroke.
"""
import math
import os
import sys

import pytest
from bokeh.models import LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from test_varlabel_options import T, MODES, ado_text, figs, sc  # noqa: E402
from conftest import drawn_renderers  # noqa: E402


def _marker_angles(fs):
    out = []
    for f in fs:
        for r in drawn_renderers(f):
            g = getattr(r, "glyph", None)
            if type(g).__name__ == "Scatter":
                a = g.angle
                out.append(float(a if isinstance(a, (int, float))
                                 else getattr(a, "value", a)))
    return out


def _labelsets(fs):
    return [ls for f in fs for ls in f.select({"type": LabelSet})]


class TestMsangle:

    def test_the_fixture(self):
        m = T["msangle"]
        assert m["forty_five"]["svg_sha"] == m["n45"]["svg_sha"]
        assert m["bogus"]["svg_sha"] == m["n0"]["svg_sha"]
        assert m["bogus"]["rc"] == 0
        assert m["bogus"]["notes"] == [
            "(note:  named style bogus not found in class anglestyle, "
            "default attributes used)"]

    @pytest.mark.parametrize("name", sorted(dr._DASH_ANGLESTYLES))
    def test_each_name(self, name, tmp_path):
        fs, notes = figs("saved", tmp_path, [sc(msymbol="T", msangle=name)])
        assert _marker_angles(fs) == [pytest.approx(math.radians(
            dr._DASH_ANGLESTYLES[name]))]
        assert not [n for n in notes if "msangle" in n], notes

    @pytest.mark.parametrize("mode", MODES)
    def test_forty_five_is_45(self, mode, tmp_path):
        a, _ = figs(mode, tmp_path, [sc(msymbol="T", msangle="forty_five")])
        b, _ = figs(mode, tmp_path, [sc(msymbol="T", msangle="45")])
        assert _marker_angles(a) == _marker_angles(b) == [
            pytest.approx(math.pi / 4)]

    @pytest.mark.parametrize("mode", MODES)
    def test_bogus_follows_the_fixture(self, mode, tmp_path):
        # rc 0 in twoway: drawn unrotated, with one note.
        fs, notes = figs(mode, tmp_path, [sc(msymbol="T", msangle="bogus")])
        assert _marker_angles(fs) in ([0.0], [])
        assert len([n for n in notes if "msangle(bogus)" in n]) == 1


class TestLabelStyle:

    def test_p2(self):
        sp = dr.SchemeParser("s2color")
        st = sp.label_style("p2")
        fill = T["mlabstyle"]["p2"]["texts"][0]["fill"]
        assert st["color"].lower() == fill
        assert st["position"] == "3"
        assert sp.label_style("p2bar")["position"] == "12"
        assert sp.label_style("bogus") is None

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn(self, mode, tmp_path):
        fs, notes = figs(mode, tmp_path, [sc(mlabel="make", mlabstyle="p2")])
        [ls] = _labelsets(fs)
        assert ls.text_color.lower() == T["mlabstyle"]["p2"]["texts"][0][
            "fill"]
        assert ls.text_align == "left"           # 3 o'clock
        assert not [n for n in notes if "mlabstyle" in n], notes
        # An explicit mlabcolor() wins.
        fs, _ = figs(mode, tmp_path, [sc(mlabel="make", mlabstyle="p2",
                                         mlabcolor="red")])
        assert _labelsets(fs)[0].text_color.lower() in ("red", "#ff0000")

    @pytest.mark.parametrize("mode", MODES)
    def test_bogus(self, mode, tmp_path):
        rec = T["mlabstyle"]["bogus"]
        assert rec["rc"] == 0 and rec["label_position"] == "12"
        fs, notes = figs(mode, tmp_path, [sc(mlabel="make",
                                             mlabstyle="bogus")])
        [ls] = _labelsets(fs)
        assert rec["texts"][0]["fill"] == "#000000"
        assert ls.text_color.lower() in ("black", "#000000")
        assert (ls.text_align, ls.text_baseline) == ("center", "bottom")
        assert [n for n in notes if "class labelstyle" in n] == [
            "dash: named style bogus not found in class labelstyle, "
            "default attributes used"]


class TestMlalign:

    def test_the_fixture(self):
        m = T["malign"]
        assert m["inside"]["svg_sha"] == T["varlabel"]["plain"]["svg_sha"]
        assert len({m[k]["svg_sha"] for k in ("center", "inside",
                                              "outside")}) == 3

    @pytest.mark.parametrize("mode", MODES)
    def test_notes(self, mode, tmp_path):
        # Flipped (WP-47 basic:PT-6): outside named "drawn centred" was
        # wrong once the renderer draws it (test_stroke_align.py).
        for v, want in (("center", []), ("inside", []), ("outside", []),
                        ("bogus", ["dash: named style bogus not found in "
                                   "class alignstroke, default attributes "
                                   "used"])):
            _, notes = figs(mode, tmp_path, [sc(mlalign=v)])
            assert [n for n in notes if "mlalign" in n
                    or "alignstroke" in n] == want, v

    def test_the_declarations(self):
        ado = ado_text()
        assert "MLABSTyle(string asis)" in ado
        assert "sreturn local mlabstyle " in ado
        assert "local _dash_pending `\"`_dash_pending' mlalign\"'" not in ado
