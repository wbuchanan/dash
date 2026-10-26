"""p1() .. p20() mapped onto their plots (WP-35 syn:SD-3).

twoway hands p<k>() after the plot groups' comma to its k-th plot, each y
of a varlist counted and a ci fit once, and p<j>() inside one plot's
options to that plot's j-th y; a number above 20 is "p21(...):  too many
arguments", r(103) (test/fixtures/pnum_truth.json, written by
scripts/extract_pnum_truth.do).  dash noted p1(), p2() and p20() as not
drawn and refused p3() .. p19() (the generated _dash_tw_takes_tab held
p1 and p20 rows).

No pytest runs Stata: these pin the fixture's readings, the parser's
registration, the stylelist key table against _dash_parse_plot_opts's
declarations, and the generated table.  test_wp35_truth.cscript's S02
(Q3502-1..3) shows dash drawing what twoway draws, in both modes.
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
_MATA = os.path.join(_ROOT, "dash_parse.mata")
_FIX = os.path.join(_HERE, "fixtures", "pnum_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _mata_body(src, name):
    m = re.search(r"^[a-z ]*\b%s\(" % re.escape(name), src, re.M)
    assert m, name
    end = src.index("\n}\n", m.start())
    return src[m.start():end]


class TestTheFixture:
    def test_meta_and_readings(self):
        d = json.load(open(_FIX, encoding="utf-8"))
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_pnum_truth.do"
        p = d["probes"]
        # p3() styles the third plot; p19() and p20() of a one-plot graph
        # change nothing; the second y of a varlist is plot 2.
        assert p["g_p3"]["rc"] == 0 and p["g_p3"]["red"] > 0
        assert p["g_p19"]["red"] == 0 and p["g_p20"]["red"] == 0
        assert p["multi_y"]["red"] > 0 and p["plot_level"]["red"] > 0
        # The plot's own option wins over p#(); the rightmost p#() wins.
        for k in ("prec_own", "prec_grp", "twice", "own_prec", "own_twice"):
            assert p[k]["red"] == 0 and p[k]["blue"] > 0, k
        assert p["own_vs_grp"]["red"] > 0
        # A ci fit takes one plot number (ci_p2), as does a nofit one.
        assert p["ci_p2"]["red"] > 0 and p["ci_after"]["red"] == 0
        assert p["ci_nofit_after"]["red"] > 0
        # Past a plot's ys: dropped silently.
        for k in ("plot_n1", "plot_over", "bars_p1", "bars_p2"):
            assert p[k]["rc"] == 0 and p[k]["red"] == 0, k
        for k in ("g_p21", "g_p100", "own_p21"):
            assert p[k]["rc"] == 103, k
            assert p[k]["first_line"].endswith(":  too many arguments"), k
        assert p["bad_inner"]["rc"] == 198
        assert p["bad_inner"]["first_line"] == "option(s) nosuch(1) not allowed"
        assert p["order_p21"]["first_line"] == "option bogus not allowed"


class TestTheParser:
    def test_take_and_merge_are_defined(self):
        mata = _read(_MATA)
        needed = _program_body(_read(_ADO), "_dash_require_mata")
        needed = needed[needed.index("local _needed"):needed.index(
            "local _missing")]
        for f in ("_dash_p_take", "_dash_p_seg", "_dash_p_unknown"):
            assert re.search(r"^\*!   %s\(" % f, mata, re.M), f
            assert re.search(r"\b%s\b" % f, needed), f
        for f in ("_dash_p_merge", "_dash_p_key"):
            assert re.search(r"^[a-z ]+\b%s\(" % f, mata, re.M), f
        # The graph's p#() is taken before its options are parsed, and the
        # segment's merged before its own.
        plot = _program_body(_read(_ADO), "_dash_plot")
        assert plot.index("_dash_p_take(") < plot.index(
            "_dash_parse_graph_opts , ")
        seg = _program_body(_read(_ADO), "_dash_process_segment")
        assert seg.index("_dash_p_apply ") < seg.index(
            "_dash_parse_plot_opts , ")


class TestTheKeyTable:
    def test_minimums_match_the_declarations(self):
        body = _program_body(_read(_ADO), "_dash_parse_plot_opts")
        syn = body[body.index("syntax [,"):]
        decl = {}
        for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9]*)\((?:string|passthru)",
                             syn):
            w = m.group(1)
            mn = re.match(r"[A-Z0-9]*", w).group(0).lower() or w.lower()
            decl.setdefault(w.lower(), mn)
        mata = _read(_MATA)
        keys = re.search(r'string scalar _dash_stylelist_keys\(\)\s*\{\s*'
                         r'return\((.*?)\)\s*\}', mata, re.S).group(1)
        keys = " ".join(re.findall(r'"([^"]*)"', keys)).split()
        table = re.findall(r'"([a-z]+)", "([a-z]+)"',
                           _mata_body(mata, "_dash_p_key"))
        assert [k for k, _ in table] == keys
        for full, mn in table:
            assert decl[full] == mn, (full, mn, decl.get(full))


class TestTheTakesTable:
    def test_no_p_rows(self):
        body = _mata_body(_read(_MATA), "_dash_tw_takes_tab")
        assert not re.search(r'\("p[0-9]+", ', body)
