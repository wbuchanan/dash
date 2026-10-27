"""WP-35 section 35-07 (DT-15): the spellings dash took and twoway refuses.

The maintainer ruled each word (DECISIONS.md P4-7, P4-9, D53; the ruled
lists are test/dash_only_rulings.py): every spelling twoway refuses is
refused as twoway refuses it, with a second line naming twoway's spelling,
except hover() and table, which only a dashboard has.  These tests pin
dash's list (_dash_dashonly_list() in dash_parse.mata) to the rulings and
the fixture, the help paragraph to the kept words, and the known-difference
tables to the ruling.  The refusals themselves run in
test/test_option_validation.cscript Q3507-1 and test/test_wp35_truth.cscript
S07 (Q3507-2).
"""
import ast
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import dash_only_rulings as R  # noqa: E402
import known_differences  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "dash_only_words_truth.json")
_MATA = os.path.join(_REPO, "dash_parse.mata")
_HELP = os.path.join(_REPO, "dash.sthlp")


def _fixture():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _dash_list():
    """The rows of _dash_dashonly_list(), as five-tuples of strings."""
    src = open(_MATA, encoding="utf-8").read()
    i = src.index("string matrix _dash_dashonly_list()")
    body = src[i:src.index("\n}\n", i)]
    rows = re.findall(r'"([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"',
                      body)
    return rows


class TestTheRulings:
    def test_every_row_is_ruled(self):
        """KEEP, REFUSE and ELSEWHERE are disjoint and cover the table's 45
        ruled rows (1-37, 39-41, V1-V5); rows 38 and 42 are 35-04's bw()."""
        keep, refuse, elsewhere = set(R.KEEP), set(R.REFUSE), set(R.ELSEWHERE)
        assert len(keep) == len(R.KEEP) == 2
        assert len(refuse) == len(R.REFUSE) == 41
        assert len(elsewhere) == 2
        assert not (keep & refuse) and not (keep & elsewhere)
        assert not (refuse & elsewhere)
        assert len(keep | refuse | elsewhere) == 45
        assert set(R.HINT) <= refuse
        assert "bw()" not in keep | refuse | elsewhere

    def test_kept_words_are_deliberate(self):
        """A known difference of hover() or table is kept by P4-7, so it is
        in a deliberate dict with a "P4-7: " value, never an open row of
        DT-15 (D-35-07.f)."""
        bad = []
        for name in sorted(os.listdir(_HERE)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(_HERE, name), encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=name)
            for node in tree.body:
                if not (isinstance(node, ast.Assign)
                        and isinstance(node.value, ast.Dict)):
                    continue
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if not any(n == "DELIBERATE" or n.endswith("_DELIBERATE")
                           for n in names):
                    continue
                for k, v in zip(node.value.keys, node.value.values):
                    if not isinstance(k, ast.Constant):
                        continue
                    key = str(k.value).split(":")[-1].strip("()")
                    if key in R.KEEP_SPELLINGS and not (
                            isinstance(v, ast.Constant)
                            and str(v.value).startswith("P4-7: ")):
                        bad.append("%s: %s" % (name, k.value))
        assert not bad, bad
        rows = known_differences.rows_for("DT-15", every_form=True)
        kept = [r for r in rows
                if r.split(": ")[1].split(":")[-1].strip("()")
                in R.KEEP_SPELLINGS]
        assert not kept, kept


class TestTheList:
    def test_dash_list_equals_refuse(self):
        """dash's list is the module's REFUSE words with their hints, in
        order; its fifth column is 1 exactly where twoway refuses the word
        inside p1() (the fixture's p.<word> keys)."""
        rows = _dash_list()
        words = [w for w in R.REFUSE if w.endswith("()")]
        assert [r[0] + "()" for r in rows] == words
        assert [r[3] for r in rows] == [R.HINT[w] for w in words]
        assert all(r[2] == "1" for r in rows)
        fx = _fixture()
        for full, mn, _v, _h, inp in rows:
            assert full.startswith(mn), full
            assert inp == ("1" if fx["p." + full]["rc"] else "0"), full

    def test_the_minimums_are_the_declarations(self):
        """Each minimum is the run of capitals of the word's declaration in
        a dash parser (or, for a word taken only in full, its lower-case
        declaration): dash took exactly those spellings."""
        ado = open(os.path.join(_REPO, "dash.ado"), encoding="utf-8").read()
        for full, mn, *_ in _dash_list():
            decls = {mn.upper() + full[len(mn):]}
            if mn == full:
                decls.add(full)
            assert any(re.search(r"\b%s\(" % re.escape(d), ado)
                       for d in decls), decls


class TestTheFixture:
    def test_readings(self):
        """twoway refuses every ruled word, by name, and takes marker()
        inside p1(); the order probes name what twoway names first."""
        fx = _fixture()
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert fx["_meta"][k], k
        for w in R.REFUSE + R.KEEP:
            key = R.FIXTURE_KEY[w]
            row = fx[key]
            if w.endswith("()") and key not in ("V1", "V2", "V3"):
                assert row["rc"] == 198, w
                assert row["message"] == "option %s() not allowed" % key, w
        assert fx["table"]["message"] == "option table not allowed"
        assert (fx["V1"]["rc"], fx["V1"]["message"]) == (
            198, "invalid kernel function")
        assert (fx["V2"]["rc"], fx["V2"]["message"]) == (
            198, "option(s) ( ) not allowed")
        assert fx["V3"]["rc"] == 7
        assert fx["p.marker"]["rc"] == 0
        assert fx["p.malpha"]["message"] == "option(s) malpha(50) not allowed"
        want = {
            "order.unknown_first": "option bogus not allowed",
            "order.word_first": "option ytitle2() not allowed",
            "order.group_then_comma": "option bogus not allowed",
            "order.p_own_first": "option bogus not allowed",
            "order.p_own_word": "option ytitle2() not allowed",
            "order.p_before_comma": "option(s) malpha(50) not allowed",
            "order.p_after_groups": "option bogus not allowed",
            "order.p_plot_order": "option(s) malpha(50) not allowed",
            "order.p_list": "option(s) malpha(50) jseed(3) not allowed",
            "order.p_own_then_graph":
                "option(s) jseed(3) malpha(50) not allowed",
        }
        for k, line in want.items():
            assert fx[k]["rc"] == 198 and fx[k]["message"] == line, k


#: twoway's note for p1(marker(O)) and mstyle(O) (dash_only_words_truth.json).
_PMARKER_NOTE = ("(note:  named style O not found in class markerstyle, "
                 "default attributes used)")


class TestMarkerInsideP:
    """D62 (DECISIONS.md, 27oct2026): inside p1() twoway reads marker() as
    its markerstyle option, mstyle(); dash drew it as msymbol()."""

    def test_twoway_reads_it_as_mstyle(self):
        """The pictures (SVG digests) and notes: p1(marker(O)) is mstyle(O)
        and the plain graph, with the note; p1(marker(p3)) is mstyle(p3);
        p1(mark(O)) is refused (marker() is taken in full only)."""
        fx = _fixture()
        plain, pm = fx["pmarker.plain"], fx["p.marker"]
        mo, p3, mp3 = (fx["pmarker.mstyle_O"], fx["pmarker.p3"],
                       fx["pmarker.mstyle_p3"])
        assert pm["svg"] == mo["svg"] == plain["svg"]
        assert pm["marker"] == plain["marker"]
        assert pm["notes"] == mo["notes"] == [_PMARKER_NOTE]
        assert plain["notes"] == [] and p3["notes"] == []
        assert p3["svg"] == mp3["svg"] != plain["svg"]
        assert (fx["pmarker.mark"]["rc"], fx["pmarker.mark"]["message"]) == (
            198, "option(s) mark(O) not allowed")

    def test_dash_writes_mstyle(self):
        """_dash_p_seg writes each p#() value's marker() word as mstyle()
        before the plot's parser reads it, so the plot's spec holds the
        mstyle key (drawn as mstyle(), with its note) and no marker key."""
        src = open(_MATA, encoding="utf-8").read()
        i = src.index("string scalar _dash_p_seg(")
        body = src[i:src.index("\n}\n", i)]
        assert re.search(r'_dash_rep_optname\([^)]*\) == "marker"', body)
        assert '"mstyle"' in body


def _help_paragraph():
    txt = open(_HELP, encoding="utf-8").read()
    i = txt.index("{marker dashonly}")
    j = txt.index("{marker", i + 1)
    return txt[i:j]


class TestTheHelp:
    def test_the_paragraph_lists_keep(self):
        """One help paragraph names the options dash has and twoway has
        not: exactly hover() and table."""
        par = _help_paragraph()
        named = set(re.findall(r"\{opt ([a-z]+(?:\(\))?)\}", par))
        assert named == set(R.KEEP), named
        txt = open(_HELP, encoding="utf-8").read()
        assert txt.count("{marker dashonly}") == 1
        assert "{help dash##dashonly:" in txt
