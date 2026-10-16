"""lalign()'s abbreviations are twoway's; lalpha() starts past them (WP-31 C17b).

Measured in StataNow 19.5 (16oct2026; test/fixtures/
colour_width_edges_truth.json lal.*, scripts/
extract_colour_width_edges_truth.do): twoway reads la(), lal(), lali(),
lalig() and lalign() on line as lalign() (the line's align setting
"outside" for ...(outside); inside is the default), while l() is
l1title() (the setting stays inside), and refuses lalp() and lalpha()
("option lalp() not allowed", r(198)): lalpha() is dash's own.  dash read
lal() as its lalpha() (lal(inside) refused, "must be a number") and
drew l() as l1title(), as twoway does.  Now LAlign stays at twoway's
minimum and
LALPha() starts at lalp, so no twoway abbreviation reaches a dash-only
option.  The Stata half is test_wp31_truth.cscript U41-15.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from test_abbreviations import _program_body  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

_ADO = os.path.join(_HERE, "..", "dash.ado")
_HLP = os.path.join(_HERE, "..", "dash.sthlp")
LALIGN = ("la", "lal", "lali", "lalig", "lalign")


def _ado():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


class TestLalignAbbreviations:
    def test_twoways_readings(self):
        for ab in LALIGN:
            rec = TRUTH["lal." + ab]
            assert rec["rc"] == 0 and rec["setting"] == "outside", ab
        assert TRUTH["lal.l"]["rc"] == 0
        assert TRUTH["lal.l"]["setting"] == "inside"
        for ab in ("lalp", "lalpha"):
            assert TRUTH["lal." + ab]["rc"] == 198
            assert TRUTH["lal." + ab]["text"] == "option %s() not allowed" % ab

    def test_lalign_is_declared_at_twoways_minimum(self):
        body = _program_body(_ado(), "_dash_label_split")
        assert body.count("LAlign(string)") == 2
        m = re.search(r'regexm\(strlower\(_dash_zyx_text\), "([^"]+)"\)', body)
        for ab in LALIGN:
            assert re.search(m.group(1), " %s(inside)" % ab), ab
        assert not re.search(m.group(1), " l(outside)")
        assert "_lb_lal" not in body

    def test_lalpha_starts_past_them(self):
        src = _ado()
        assert "LALPha(string)" in src and "LALpha(string)" not in src
        with open(_HLP, encoding="utf-8") as fh:
            hlp = fh.read()
        assert "{cmdab:lalp:ha(}" in hlp and "{cmdab:lal:pha(}" not in hlp
