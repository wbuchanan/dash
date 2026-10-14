"""
test_matamatrix_refusal.py -- twoway's matamatrix() refused by name (WP-31
B3, section 21).

The defect (measured at 7470c65): ``dash scatter matamatrix(M)`` was read
as a varlist and refused "variable matamatrix not found" style, r(101) or
r(111), naming matamatrix(M) as if it were a variable.  twoway plots the
columns of a Mata matrix (twoway_mata.sthlp, "Two-way graphs of mata
matrices"; test/fixtures/rangept_truth.json matamatrix.defined: rc 0),
detected by a varlist that begins, lower case, with ``matamatrix(``
(twoway_yxview_parse.class: ``bsubstr(anything, 1, 11) ==
"matamatrix("``; MATAMATRIX(M) is read as a varlist, matamatrix.upper:
"variable M not found", r(111)).  dash does not draw it (PRD section 7)
and refuses it by name, r(198), with advice (DECISIONS M4).
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

with open(os.path.join(_HERE, "fixtures", "rangept_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_SENTENCE = (" is a twoway mata matrix plot, which dash does not draw. Use "
             "Stata's own twoway ")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestMatamatrixRefused:

    def test_function_and_needed(self):
        mata = _read("dash_parse.mata")
        assert "string scalar _dash_matamatrix_typed(" in mata
        start = mata.index("string scalar _dash_matamatrix_typed(")
        body = mata[start:mata.index("\n}\n", start)]
        # twoway's own test: the first eleven characters, case-sensitive.
        assert '"matamatrix("' in body and "strlower" not in body
        assert "*!   _dash_matamatrix_typed(" in mata
        ado = _read("dash.ado")
        req = ado[ado.index("program define _dash_require_mata"):]
        req = req[:req.index("\nend\n")]
        assert "_dash_matamatrix_typed" in req
        p = _T["probes"]
        assert p["matamatrix.defined"]["rc"] == 0
        assert (p["matamatrix.upper"]["rc"],
                p["matamatrix.upper"]["message"]) == (
            111, "variable M not found")
        assert p["advice.matamatrix"]["message"] == \
            "nosuch is not a mata matrix"

    def test_sentence(self):
        ado = _read("dash.ado")
        assert _SENTENCE in ado
        assert "getmata the columns into variables" in ado
        # The check reads the varpart before any varlist parser does.
        call = ado.index("_dash_matamatrix_typed(st_local(\"varpart\"))")
        parse = ado.index("if `: list ptype in _pt_univar' {", call - 4000)
        assert call < parse

    def test_help(self):
        help_text = _read("dash.sthlp")
        para = help_text[help_text.index("{ul:Not drawn.}"):]
        para = para[:para.index("{marker ")]
        assert "{cmd:matamatrix(}" in para
        assert "{cmd:getmata}" in para
