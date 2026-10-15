"""
test_mlabel_prefix_suffix.py -- mlabprefix()/mlabsuffix() wrap every
marker label's text and lalign() is taken as twoway takes it (WP-31 C17).

The defect (measured at 783f06a): all three options were undeclared;
``dash scatter mpg weight, mlabel(make) mlabprefix("[") mlabsuffix("]")``
drew "AMC Concord" and named both options in the generic note.

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json): prefix.both draws "[AMC
Concord]"; ``line mpg weight, lalign(center|inside|outside)`` draws the
same picture as without it, rc 0, silent (align.*: one SVG digest);
``lalign(bogus)`` is rc 0 with "named style bogus not found in class
alignstroke, default attributes used".  headlabel is taken on every pc
type (yxyxview_parse:52,67): dash's acceptance stands (U34-10).
"""
import os
import sys

import pytest
from bokeh.models import HoverTool, LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_varlabel_options import T, MODES, ado_text, figs  # noqa: E402

_PRE = {"mlabel": "make", "mlabprefix": '"["', "mlabsuffix": '"]"'}


def _plot(t, **o):
    if t in ("rscatter",):
        return {"type": t, "yvar1": "lo", "yvar2": "hi", "xvar": "weight",
                "options": o}
    return {"type": t, "yvar": "mpg", "xvar": "weight", "options": o}


def _texts(fs):
    out = []
    for f in fs:
        for ls in f.select({"type": LabelSet}):
            col = ls.text if isinstance(ls.text, str) else ls.text.field
            out.extend(str(v) for v in ls.source.data[col])
    return out


def _tooltips(fs):
    return [list(h.tooltips) if isinstance(h.tooltips, list) else h.tooltips
            for f in fs for h in f.select({"type": HoverTool})]


class TestPrefixSuffix:

    def test_the_fixture(self):
        want = [t["text"] for t in T["prefix"]["both"]["texts"]][:3]
        assert want == ["[AMC Concord]", "[AMC Pacer]", "[AMC Spirit]"]
        assert T["prefix"]["both"]["rc"] == 0
        assert T["prefix"]["both"]["notes"] == []

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("t", ("scatter", "bar", "rscatter"))
    def test_text(self, mode, t, tmp_path):
        want = [x["text"] for x in T["prefix"]["both"]["texts"]][:3]
        fs, notes = figs(mode, tmp_path, [_plot(t, **_PRE)])
        got = _texts(fs)
        # rscatter labels both ends.
        assert got == (want * 2 if t == "rscatter" else want), got
        assert not [n for n in notes if "mlabprefix" in n
                    or "mlabsuffix" in n], notes

    @pytest.mark.parametrize("mode", MODES)
    def test_the_tooltip_is_unchanged_by_prefix(self, mode, tmp_path):
        a, _ = figs(mode, tmp_path, [_plot("scatter", mlabel="make")])
        b, _ = figs(mode, tmp_path, [_plot("scatter", **_PRE)])
        assert _tooltips(a) == _tooltips(b)

    def test_the_declarations(self):
        ado = ado_text()
        assert "MLABPREfix(string asis) MLABSUFFix(string asis)" in ado
        for o in ("mlabprefix", "mlabsuffix", "lalign"):
            assert "sreturn local %s " % o in ado, o


class TestAlignment:

    def test_the_fixture(self):
        al = T["align"]
        digests = {al[k]["svg_sha"] for k in ("center", "inside", "outside")}
        assert digests == {al["bogus"]["svg_sha"]}
        assert all(al[k]["notes"] == [] for k in ("center", "inside",
                                                  "outside", "la"))
        assert set(al["bogus"]["notes"]) == {
            "(note:  named style bogus not found in class alignstroke, "
            "default attributes used)"}

    @pytest.mark.parametrize("mode", MODES)
    def test_center_is_silent(self, mode, tmp_path):
        for v in ("center", "inside", "outside"):
            _, notes = figs(mode, tmp_path, [_plot("line", lalign=v)])
            assert not [n for n in notes if "lalign" in n
                        or "alignstroke" in n], (v, notes)

    @pytest.mark.parametrize("mode", MODES)
    def test_inside_is_noted_once(self, mode, tmp_path):
        # Measured: inside draws as twoway's default, so it is silent; a
        # word that is no alignment is named once in twoway's words.
        _, notes = figs(mode, tmp_path, [_plot("line", lalign="bogus")])
        assert [n for n in notes if "alignstroke" in n] == [
            "dash: named style bogus not found in class alignstroke, "
            "default attributes used"]
