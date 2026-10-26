"""
test_command_grammar.py -- the command grammar dash reads before any
option, held to twoway's (WP-35 section 35-09).

test/fixtures/command_grammar_truth.json (scripts/
extract_command_grammar_truth.do) records twoway's answers: a plot-type
word with a capital letter, the graph with no plot and its axis options,
a bare plot after a parenthesised group, and || inside one group.  The
refusals are certified in test/test_parser.cscript (Q3509-2, -3, -5, -7,
-9), the drawings in test/test_wp35_truth.cscript (S09 blocks).
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

with open(os.path.join(_HERE, "fixtures", "command_grammar_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestTheFixture:

    def test_readings(self):
        """The readings each section-35-09 rule rests on."""
        assert _T["_meta"]["source"] == \
            "scripts/extract_command_grammar_truth.do"
        assert (_T["case.Sc"]["rc"], _T["case.Sc"]["message"]) == (
            198, "Sc is not a twoway plot type")
        assert _T["case.Sc"]["lc_rc"] == 0
        assert _T["empty.svg.title"]["rc"] == 0
        assert _T["empty.svg.title"]["lines"] == 0
        assert _T["empty.svg.title"]["texts"] == ["T"]
        assert (_T["empty.xlabel_1_2"]["rc"],
                _T["empty.xlabel_1_2"]["message"]) == (
            198, "xlabels(1 2) not allowed, xaxis1 does not exist")
        assert (_T["group.bare_after"]["rc"],
                _T["group.bare_after"]["nplots"]) == (0, 2)
        assert _T["inner.bare"]["rc"] == 0
        assert _T["inner.piece_comma"]["message"] == "option | not allowed"
        assert (_T["generic.nosuchtype"]["rc"],
                _T["generic.nosuchtype"]["message"]) == (
            198, "nosuchtype is not a twoway plot type")


class TestCase:

    def test_no_strlower_on_the_type(self):
        """The plot-type word is matched as typed: neither the caller in
        _dash_process_segment nor the Mata wrapper lower-cases it (M7:
        lower case only; twoway refuses Sc, Hist, Rsc ...)."""
        ado = _read("dash.ado")
        assert 'mata: _dash_expand_plottype(st_local("plottype"), "_pt_exp")' \
            in ado
        assert "_dash_expand_plottype(strlower(" not in ado
        mata = _read("dash_parse.mata")
        start = mata.index("void _dash_expand_plottype(")
        body = mata[start:mata.index("\n}\n", start)]
        assert "strlower" not in body
        start = mata.index("string scalar _dash_expand_plottype_str(")
        body = mata[start:mata.index("\n}\n", start)]
        assert "strlower" not in body


def _figures(tmp_path, mode, title=""):
    """The figures one mode draws for a graph with no plot
    (test_bare_dash.py's reader)."""
    sys.path.insert(0, _HERE)
    from test_bare_dash import _figures as _bare_figures
    return _bare_figures(tmp_path, mode, title=title)


class TestEmpty:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_no_axis_visible(self, tmp_path, mode):
        """twoway, title(T) draws no axis, tick, label or grid
        (command_grammar_truth.json empty.svg.title: no <line>, the text
        T alone); both modes draw the figure with every axis and grid
        hidden, and the title (plot:PT-4)."""
        from bokeh.models import Axis, Grid
        figs = _figures(tmp_path, mode, title="T")
        assert len(figs) == 1, figs
        f = figs[0]
        axes = list(f.select({"type": Axis}))
        grids = list(f.select({"type": Grid}))
        assert axes and grids, (axes, grids)
        assert [a for a in axes if a.visible] == []
        assert [g for g in grids if g.visible] == []
        assert f.title is not None and f.title.text == "T"
        assert _T["empty.svg.title"]["lines"] == 0


class TestGeneric:

    def test_no_by_name_refusal(self):
        """Every word that is no plot type gets the one generic refusal:
        no Mata helper names a word to refuse with advice, and the type
        check in _dash_process_segment compares the typed word with no
        literal (PD-10)."""
        ado = _read("dash.ado")
        mata = _read("dash_parse.mata")
        for name in ("_dash_undrawn_" + "plottype",
                     "_dash_" + "mata" + "matrix_typed"):
            assert name not in ado, name
            assert name not in mata, name
        start = ado.index("gettoken plottype rest : seg_text")
        block = ado[start:ado.index("_dash_plottype_families", start)]
        assert not re.search(r'"`(plottype|_pt_[a-z]+)\'" == "[a-z]', block)
        assert "plot type dash does not draw" not in ado
        assert "mata matrix plot" not in ado
