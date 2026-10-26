"""
test_matamatrix_refusal.py -- no varlist form is refused by name (WP-31
B3, flipped by WP-35 PD-10).

WP-31 B3 refused one varlist form by name, r(198), with advice of its
own, through a Mata helper and a block in _dash_process_segment.  PD-10
(maintainer rulings M1, A2; DECISIONS A-9) removes both: the form gets
the refusal any unknown token at the head of a varlist gets -- for
``scatter nosuchfn(M)`` "variable M not found", r(111) -- which
test_help_claims_1.cscript U56-1 and test_wp31_truth.cscript U21-10
certify by running both.  These tests hold the source to it; the word
appears only as test input.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

#: The helper WP-31 B3 added, spelled in two parts so this file names no
#: function of the tree.
_HELPER = "_dash_" + "matamatrix_typed"


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestMatamatrixRefused:

    def test_function_and_needed(self):
        # Flipped (WP-35 PD-10): the by-name helper, its header-index line
        # and its _needed entry were wrong because no varlist form is
        # refused by name.
        mata = _read("dash_parse.mata")
        assert _HELPER not in mata
        ado = _read("dash.ado")
        req = ado[ado.index("program define _dash_require_mata"):]
        req = req[:req.index("\nend\n")]
        assert _HELPER not in req
        assert _HELPER not in ado

    def test_sentence(self):
        # Flipped (WP-35 PD-10): the advice sentence is gone; no branch of
        # _dash_process_segment tests the varlist for one form.
        ado = _read("dash.ado")
        assert "is a twoway mata matrix plot" not in ado
        assert "getmata the columns into variables" not in ado
        assert '"matamatrix("' not in ado

    def test_help(self):
        # Flipped (WP-35 PD-10): the help names no such form.
        help_text = _read("dash.sthlp")
        assert "matamatrix" not in help_text
        assert "{cmd:getmata}" not in help_text
