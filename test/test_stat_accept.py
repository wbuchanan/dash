"""Statistical-type options twoway accepts (WP-35 section 35-03).

twoway reads lowess m as mean (twoway_lowess_parse.class declares Mean)
and the other spellings and edge values of the statistical types this
section takes (test/fixtures/stat_accept_truth.json, written by
scripts/extract_stat_accept_truth.do); dash refused them.

No pytest runs Stata: these pin the fixture's readings and the parser's
declarations and pipeline order.  test_wp35_truth.cscript's S03 blocks
(Q3503-1 ..) show dash taking and drawing what twoway draws.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_abbreviations import _program_body  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
_ADO = os.path.join(_ROOT, "dash.ado")
_FIX = os.path.join(_HERE, "fixtures", "stat_accept_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _truth():
    return json.load(open(_FIX, encoding="utf-8"))


def _rows(probe):
    """A probe's serset as its rows, sorted: lowess writes the same
    values in another order from one run to the next."""
    s = probe["serset"]
    return sorted(zip(*[s[k] for k in sorted(s)]))


class TestTheFixture:
    def test_readings(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_stat_accept_truth.do"
        # stat:PT-7: lowess m draws lowess mean's curve, not the plain one.
        assert d["lowess_m"]["rc"] == 0 and d["lowess_m"]["notes"] == []
        assert _rows(d["lowess_m"]) == _rows(d["lowess_mean"])
        assert _rows(d["lowess_m"]) != _rows(d["lowess_none"])


class TestTheFold:
    def test_fold_is_defined_and_called_before_the_refusal(self):
        """_dash_fold_stat_words runs after _dash_refuse_unbound and before
        _dash_refuse_unknown (which would refuse m): _dash_refuse_unbound
        parses the list again whenever the catch-all holds another word,
        which would put m back.  It runs again directly after
        _dash_refuse_asp, because _dash_refuse_unknown's re-parse clears
        what the first call wrote."""
        src = _read(_ADO)
        body = _program_body(src, "_dash_fold_stat_words")
        assert body is not None, "_dash_fold_stat_words is not defined"
        assert re.search(r"^\s*version 19\s*$", body, re.M), body[:200]
        seg = _program_body(src, "_dash_process_segment")
        lines = [ln.strip() for ln in seg.splitlines()]

        def at(pred):
            return [i for i, ln in enumerate(lines) if pred(ln)]

        call = at(lambda ln: ln.startswith("_dash_fold_stat_words "))
        unbound = at(lambda ln: ln.startswith("_dash_refuse_unbound "))
        unknown = at(lambda ln: ln.startswith("_dash_refuse_unknown "))
        asp = at(lambda ln: ln == "_dash_refuse_asp")
        assert len(call) == 2 and len(unbound) == 1 and len(unknown) == 1, (
            call, unbound, unknown)
        assert unbound[0] < call[0] < unknown[0], (unbound, call, unknown)
        assert len(asp) == 1 and call[1] == asp[0] + 1, (asp, call)
