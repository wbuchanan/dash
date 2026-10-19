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


_NOTED = os.path.join(_ROOT, "test", "fixtures", "noted_option_truth.json")
_ADO = os.path.join(_ROOT, "dash.ado")


def _noted():
    with open(_NOTED, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheRefusedTableIsTheNotedFixture:
    """WP-32 (BUGS.md "dash names in its note, as not drawn, options twoway
    refuses on that plot type"): _dash_tw_refuses_tab holds the options
    dash declares that twoway refuses, on the types it refuses them, from
    test/fixtures/noted_option_truth.json; test_option_validation.cscript
    U52 certifies the refusals."""

    def test_each_shortest_spelling_is_the_one_dash_declares(self):
        import re
        with open(_ADO, encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("program define _dash_parse_plot_opts")
        body = src[i:src.index("\nend", i)]
        for full, short in gen.DECLARED.items():
            caps = [m.group(1) for m in re.finditer(
                r"\b([A-Za-z0-9]+)(?:\(string(?: asis)?\))?(?=[\s/])", body)
                if m.group(1).lower() == full]
            assert caps, full
            mn = "".join(ch for ch in caps[0] if ch.isupper() or ch.isdigit())
            assert (mn.lower() or full) == short, (full, caps[0])

    def test_each_row_is_what_twoway_refused(self):
        nx = _noted()
        types = nx["types"]
        rows = gen.refused_rows(nx)
        assert {r[0] for r in rows} == set(gen.DECLARED)
        for full, short, ts, after in rows:
            opt = [o for o in nx["probes"] if o.split("(", 1)[0] == full][0]
            ref = [t for t in types
                   if nx["probes"][opt][t]["twoway_rc"] == 198]
            assert ts == ("*" if len(ref) == len(types) else " ".join(ref))
            for t in ref:
                assert (nx["probes"][opt][t]["twoway_message"]
                        == "option %s not allowed"
                        % (full + ("()" if "(" in opt else "")))
        by = {r[0]: r for r in rows}
        assert by["filter"][3] == "1" and by["link"][3] == "1"
        assert by["at"][3] == "0"
        kept = set(types) - set(by["headlabel"][2].split())
        assert kept == {"rpcap", "rpspike", "pcspike", "pccapsym", "pcarrow",
                        "pcbarrow", "pcscatter", "pci", "pcarrowi"}


class TestTheSilentTableIsTheNotedFixture:
    """WP-32 (BUGS.md "dash names options twoway takes and draws nothing
    of, where twoway is silent"): _dash_tw_silent_tab holds, for each
    option on dash's pending lists, the types where twoway draws the same
    picture with it; test_option_validation.cscript U55 certifies the
    silence."""

    def test_each_row_is_where_twoway_draws_the_same(self):
        nx = _noted()
        rows = dict(gen.silent_rows(nx))
        for opt, by in nx["probes"].items():
            name = opt.split("(", 1)[0]
            if name not in rows:
                continue
            for t in rows[name].split():
                assert by[t]["twoway_rc"] == 0, (opt, t)
                assert by[t]["twoway_draws"] is False, (opt, t)

    def test_a_drawn_or_unmeasured_type_has_no_row(self):
        rows = dict(gen.silent_rows(_noted()))
        assert "bar" not in rows["acolor"].split()
        assert "scatter" in rows["acolor"].split()
        assert "contour" not in rows["bmlinestyle"].split()
        assert "scatter" not in rows["sort"].split()
        assert "lfit" in rows["sort"].split()
        assert "pcspike" in rows["headlabel"].split()
