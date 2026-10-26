"""WP-31 A2: dash takes twoway's plot-type spellings and nothing shorter.

twoway reads its plot types with one declaration (twowaygraph_g.class,
program _unab_cmd): `syntax [, SCatter LIne CONnected HISTogram RSCatter
RLine RCONnected MBANDs FN FUNction *]'.  Those eight minimums, mbands and
fn are the only spellings it takes short of a type's full name; every other
word is "<word> is not a twoway plot type", r(198).  Measured 13oct2026
(test/fixtures/bare_prefix_truth.json, scripts/extract_bare_prefix_truth.do):
ar ba sp lfi qfi low lpo fp kde dr tsl tsrl msp are each refused so, and
dash took all thirteen as the type they began (DISCOVERY Q28).

The behaviour is pinned by test/test_parser.cscript U08-5/U08-6,
test/test_help_claims_1.cscript HC1-07/HC1-08 and test_wp31_truth.cscript
U08-1/U08-2; this file reads the table and the refusal from the source.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MATA = os.path.join(ROOT, "dash_parse.mata")
ADO = os.path.join(ROOT, "dash.ado")
FIXTURE = os.path.join(HERE, "fixtures", "bare_prefix_truth.json")

#: twoway's minimums (_unab_cmd); every other type is its full name only.
TWOWAY_MINIMUMS = {"scatter": "sc", "line": "li", "connected": "con",
                   "histogram": "hist", "rscatter": "rsc", "rline": "rl",
                   "rconnected": "rcon", "function": "fun"}

EXTRAS = ("ar", "ba", "sp", "lfi", "qfi", "low", "lpo", "fp", "kde", "dr",
          "tsl", "tsrl", "msp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _table():
    """[(full, minimum), ...] of _dash_expand_plottype_str, in order."""
    src = _read(MATA)
    k = src.index("string scalar _dash_expand_plottype_str")
    block = src[k:src.index("\n}\n", k)]
    return re.findall(r'\("([a-z]+)","([a-z]+)"\)', block), block


class TestTheTable:
    def test_only_twoways_minimums(self):
        rows, _ = _table()
        # 40 -> 42: WP-31 B1 rpcap and rpspike drawn (full names only,
        # test/fixtures/rangept_truth.json abbrev.*).
        # 42 -> 44: WP-31 B4b contour and contourline drawn (full names
        # only, measured 23sep2026: cont .. contourlin are no plot type).
        assert len(rows) == 44, len(rows)
        bad = [(full, mn) for full, mn in rows
               if mn != TWOWAY_MINIMUMS.get(full, full)]
        assert not bad, (
            "rows whose minimum is not twoway's (its eight, else the full "
            "name): %s" % bad)
        assert {f: m for f, m in rows if m != f} == TWOWAY_MINIMUMS

    def test_the_two_other_spellings_stay(self):
        _, block = _table()
        assert 'if (name == "mbands") return("mband")' in block
        assert 'if (name == "fn") return("function")' in block


class TestTheFixture:
    def test_bare_prefix_is_stamped(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            d = json.load(fh)
        assert sorted(d) == ["_meta", "bare", "extras", "mla", "twoways"]
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_bare_prefix_truth.do"
        assert sorted(d["extras"]) == sorted(EXTRAS)
        for w, r in d["extras"].items():
            assert r["rc"] == 198, (w, r)
            assert r["message"] == w + " is not a twoway plot type", (w, r)
        assert sorted(d["twoways"]) == sorted(
            list(TWOWAY_MINIMUMS.values()) + ["mbands", "fn"])
        assert all(r["rc"] == 0 for r in d["twoways"].values())


class TestTheRefusal:
    def test_twoways_sentence_and_the_supported_line(self):
        src = _read(ADO)
        i = src.index('"Supported: scatter line connected')
        # Flipped (WP-35 PD-10): the by-name branch above the sentence is
        # gone; the sentence opens the branch for a word that is no type.
        head = src[src.rindex("if \"`ptype'\" == \"\" {", 0, i):i]
        assert ('mata: _dash_say("err", "", st_local("plottype"), '
                '" is not a twoway plot type")') in head, head
        assert "unrecognised plot type" not in head
        assert "exit(198)" in src[i:i + 600]
