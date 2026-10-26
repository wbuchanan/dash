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
