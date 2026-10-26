"""
test_sunflower_refusal.py -- no word is refused by name (WP-31 B2,
flipped by WP-35 PD-10).

WP-31 B2 refused one word by name, r(198), with advice of its own,
through a Mata helper and a branch in _dash_process_segment.  PD-10
(maintainer rulings M1, A2; DECISIONS A-9) removes both: the word gets
the refusal any word that is no plot type gets, "<word> is not a twoway
plot type", r(198), with dash's Supported: list
(test_parser.cscript Q3509-3, test_help_claims_1.cscript HC1-19 and
U56-1, test_wp31_truth.cscript U21-9 run it).  These tests hold the
source to it; the word appears only as test input.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

#: The helper WP-31 B2 added, spelled in two parts so this file names no
#: function of the tree.
_HELPER = "_dash_undrawn_" + "plottype"


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestSunflowerRefused:

    def test_tuple(self):
        # Flipped (WP-35 PD-10): the helper that named one word to refuse
        # was wrong because every word that is no plot type is refused
        # alike; the word is no entry of the plot-type table either.
        mata = _read("dash_parse.mata")
        assert _HELPER not in mata
        start = mata.index("string scalar _dash_expand_plottype_str(")
        body = mata[start:mata.index("\n}\n", start)]
        assert '"sunflower"' not in body

    def test_sentence(self):
        # Flipped (WP-35 PD-10): no advice sentence, no branch on the word.
        ado = _read("dash.ado")
        assert _HELPER not in ado
        assert "density petals" not in ado
        assert not re.search(r'== "sunflower"', ado)

    def test_help(self):
        # Flipped (WP-35 PD-10): the help names the word nowhere as a plot
        # type (it stays among Stata's style-file names).
        help_text = _read("dash.sthlp")
        assert "{ul:Not drawn.}  Two" not in help_text
        assert "{cmd:sunflower} command" not in help_text
        assert "{cmd:twoway sunflower}" not in help_text
