"""Time-series operators in an option's variables (WP-31 A6).

The defect: ``mlabel(L.make)``, ``colorvar(L.mpg)`` and ``by(L.foreign)``
were refused r(198), "must name a variable, not a time-series expression",
on tsset data (and as "variable L.make not found", r(111), on data not
tsset), where twoway answers each in its own words and code, whatever the
tsset: mlabel() "variable L not found", r(111); colorvar() and by()
"factor-variable and time-series operators not allowed", r(101);
mlabvposition() "L.pos invalid name", r(198) (measured on StataNow 19.5,
test/fixtures/weight_operator_truth.json ``operators``).  twoway draws none
of them, so dash draws none: it refuses each with twoway's line and code
(``_dash_validate_value``, the var/varlist/byvarlist branch).

The Stata side is pinned by test/test_wp31_truth.cscript U07-4 (each form,
tsset and not, against the fixture) and test/test_option_validation.cscript
U07-9 (the mlabel() types that drop or refuse the option first).
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

with open(os.path.join(HERE, "fixtures", "weight_operator_truth.json"),
          encoding="utf-8") as _fh:
    _OPS = json.load(_fh)["operators"]


def _branch():
    """dash.ado's var/varlist/byvarlist branch of _dash_validate_value."""
    with open(os.path.join(REPO, "dash.ado"), encoding="utf-8") as fh:
        src = fh.read()
    start = src.index('else if inlist("`kind\'", "var", "varlist", '
                      '"byvarlist") {')
    end = src.index('else if "`kind\'" == "scheme" {', start)
    return src[start:end]


class TestOperatorForms:
    def test_twoway_draws_none_of_them(self):
        """D-07.c: a form twoway draws would be routed to a column; the
        fixture records that twoway refuses every one."""
        assert sorted(_OPS) == ["by_L", "colorvar_L", "mlabel_L",
                                "mlabel_Lnum", "mlabvpos_L"]
        assert all(rec["rc"] != 0 for rec in _OPS.values())

    def test_each_refusal_is_twoways(self):
        body = _branch()
        # colorvar() and by(): twoway's line and code.
        text = _OPS["colorvar_L"]["text"]
        assert text == _OPS["by_L"]["text"]
        assert _OPS["colorvar_L"]["rc"] == _OPS["by_L"]["rc"] == 101
        m = re.search(r'display as error "%s"\s*\n\s*exit 101' %
                      re.escape(text), body)
        assert m, text
        # mlabel(): "variable <operators> not found", r(111).
        assert _OPS["mlabel_L"]["text"] == "variable L not found"
        assert _OPS["mlabel_L"]["rc"] == _OPS["mlabel_Lnum"]["rc"] == 111
        assert re.search(r'_dash_say\("err", "variable ", '
                         r'st_local\("_tsops"\), " not found"\)\s*\n\s*'
                         r'exit 111', body)

    def test_the_operator_test_is_version_free(self):
        """regexm's engine follows the caller's version; the operator test
        is ustrregexm's, which does not."""
        body = _branch()
        assert 'regexm(scalar(`K\'), "^[LlFfDdSs]' not in body.replace(
            "ustrregexm", "")
        assert 'ustrregexm(scalar(`K\'), "^[LlFfDdSs]' in body
