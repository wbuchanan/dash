"""test_unknown_options.py -- the words twoway takes that dash leaves to its
catch-all (WP-32).

dash refuses an option word twoway does not take, as twoway refuses it
(BUGS.md "In a few mixed lists dash names another word than twoway names
first, and an unknown lower-case word is noted where twoway refuses it");
what twoway takes and dash does not declare stays named in the note.  The
line between them is dash_parse.mata's _dash_tw_takes_tab, generated from
test/fixtures/unknown_option_truth.json by
scripts/gen_twoway_takes_table.py; test_option_validation.cscript U50 and
test_twoway_option_parity.cscript TP-02 and TP-07 certify the refusals.
"""
import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIX = os.path.join(_ROOT, "test", "fixtures", "unknown_option_truth.json")
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import gen_twoway_takes_table as gen  # noqa: E402


def _fixture():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheTableIsTheFixture:
    def test_the_generated_table_is_current(self):
        rc = subprocess.run([sys.executable, os.path.join(
            _ROOT, "scripts", "gen_twoway_takes_table.py"), "--check"],
            capture_output=True, text=True)
        assert rc.returncode == 0, rc.stderr

    def test_a_refused_probe_has_no_row(self):
        names = {r[0] for r in gen.rows(_fixture())}
        for nm in ("add", "commonscheme", "iscale", "labels", "legloc",
                   "readlog", "serset", "spacers", "useplotregion",
                   "usescheme", "xcommon"):
            assert nm not in names, nm

    def test_each_row_is_what_twoway_took(self):
        fx = _fixture()
        for full, short, value, types, after in gen.rows(fx):
            p = fx["probes"][full]
            assert p["twoway_rc"] in (0, 601)
            assert value == ("1" if "(" in p["option"] else "0")
            want = ("*" if len(p["types_taking"]) == len(fx["types"])
                    else " ".join(p["types_taking"]))
            assert types == want
            assert after == ("1" if p["after_comma_rc"] in (0, 601)
                             else "0")
            k = len(short)
            assert all(rc in (0, 601) for rc in p["spellings_rc"][k - 1:])

    def test_the_shortest_spelling_is_measured(self):
        rows = {r[0]: r for r in gen.rows(_fixture())}
        assert rows["afcolor"][1] == "afc"
        assert rows["bargap"][3] == "area bar spike dropline dot"
        assert rows["below"][4] == "1" and rows["afcolor"][4] == "0"
