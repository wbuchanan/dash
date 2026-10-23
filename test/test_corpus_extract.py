"""
test_corpus_extract.py -- the corpus extractor's rules (WP-33 33-02).

scripts/corpus/extract.py reads twoway's own examples out of Stata's help
files, the [G] manual (g.pdf through pdftotext), examples/*.do and the
drop-in audit's frozen probes.  Each rule is pinned here on an inline sample
copied from the real file the rule reads.
"""
import json
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts.corpus import extract  # noqa: E402


# ------------------------------------------------------------ help files

class TestHelpLinks:

    def test_plain_and_compound_links(self):
        # base/t/twoway_contour.sthlp:259 (compound) and :268 (plain);
        # base/t/twoway_area.sthlp:246 (gr_example2); tsline.sthlp's tsline_ex.
        text = (
            "{pstd}\n"
            "   \t{cmd:. twoway contour depth northing easting}\n"
            "   \t  {it:({stata `\"gr_example sandstone: twoway contour depth northing easting\"':click to run})}\n"
            "   \t  {it:({stata \"gr_example sandstone: twoway contour depth northing easting, levels(10)\":click to run})}\n"
            "\t  {it:({stata \"gr_example2 twoarea\":click to run})}\n"
            "\t  {it:({stata \"tsline_ex calories2\":click to run})}\n"
            "\t  {it:({stata \"gr_example auto: scatter mpg weight, title({c 34}A{c 34}) note({c -(}it:x{c )-})\":click})}\n"
            "\t  {it:({stata \"help scatter\":see})}\n")
        links = extract.help_links(text, "base/t/x.sthlp")
        assert [l["kind"] for l in links] == ["gr_example", "gr_example",
                                              "gr_example2", "tsline_ex",
                                              "gr_example"]
        assert links[0]["arg"] == "sandstone: twoway contour depth northing easting"
        assert links[0]["line"] == 3 and links[0]["file"] == "base/t/x.sthlp"
        assert links[1]["arg"].endswith("levels(10)")
        assert links[2]["arg"] == "twoarea"
        assert links[3]["arg"] == "calories2"
        assert links[4]["arg"] == 'auto: scatter mpg weight, title("A") note({it:x})'


# ------------------------------------------------------------ gr_example2

_GRINTRO6 = """program grintro6
\tMsg preserve
\tpreserve
\tXeq webuse lifeexp2, clear

\t#delimit ;

\tXeq twoway
\t(scatter lexp gnppc, mlabel(country) mlabv(pos))
\t(line hat gnppc, sort)
\t, xscale(log) xlabel(.5 5 10 15 20 25 30) legend(off)
\t  title("Life expectancy vs. GNP per capita")
\t;
\t#delimit cr
\tMsg restore
end

program markerlabel1
\tMsg preserve
\tpreserve
\tXeq sysuse lifeexp, clear
\tXeq gen pos = 3
\tXeq replace pos = 9 if country=="Honduras"
\t#delimit ;
\tXeq
\tscatter lexp gnppc if region==2,
\t\tmlabel(country) mlabv(pos)
\t\txsca(range(35000))
\t;
\t#delimit cr
\tMsg restore
end
"""

# gr_example2.ado:84-117, quoted whole.
_MARKERLABEL3 = """program markerlabel3
\tMsg preserve
\tpreserve
\tXeq sysuse lifeexp, clear
\tXeq keep if region==2 | region==3
\tXeq replace gnppc = gnppc / 1000
\tXeq label var gnppc "GNP per capita (thousands of dollars)"
\tXeq gen lgnp = log(gnp)
\tXeq qui reg lexp lgnp
\tXeq predict hat
\tXeq label var hat "Linear prediction"
\tXeq replace country = "Trinidad" if country=="Trinidad and Tobago"
\tXeq replace country = "Para" if country == "Paraguay"
\tXeq gen pos = 3
\tXeq replace pos = 9 if lexp > hat
\tXeq replace pos = 3 if country == "Colombia"
\tXeq replace pos = 3 if country == "Para"
\tXeq replace pos = 3 if country == "Trinidad"
\tXeq replace pos = 9 if country == "United States"

\t#delimit ;

\tXeq twoway
\t(scatter lexp gnppc, mlabel(country) mlabv(pos))
\t(line hat gnppc, sort)
\t, xscale(log) xlabel(.5 5 10 15 20 25 30) legend(off)
\t  title("Life expectancy vs. GNP per capita")
\t  subtitle("North, Central, and South America")
\t  note("Data source: World Bank, 1998")
\t  ytitle("Life expectancy at birth (years)")
\t;
\t#delimit cr
\tMsg restore
end
"""


class TestAdoPrograms:

    def test_xeq_and_delimit_blocks(self):
        progs = extract.ado_programs(_GRINTRO6)
        assert progs["grintro6"] == [
            "webuse lifeexp2, clear",
            'twoway (scatter lexp gnppc, mlabel(country) mlabv(pos)) '
            '(line hat gnppc, sort) , xscale(log) xlabel(.5 5 10 15 20 25 30) '
            'legend(off) title("Life expectancy vs. GNP per capita")']
        assert progs["markerlabel1"] == [
            "sysuse lifeexp, clear", "gen pos = 3",
            'replace pos = 9 if country=="Honduras"',
            "scatter lexp gnppc if region==2, mlabel(country) mlabv(pos) "
            "xsca(range(35000))"]
        # tsline_ex.ado's calories: an Xeq continued over /// lines.
        cal = extract.ado_programs(
            "program calories\n\tXeq sysuse tsline2, clear\n"
            "\tXeq tsline calories, ttick(28nov2002, tpos(in))\t///\n"
            "\t\tttext(3470 28nov2002 \"thanks\")\t///\n\t\t// blank\nend\n")
        assert cal["calories"][1] == ('tsline calories, ttick(28nov2002, tpos(in)) '
                                      'ttext(3470 28nov2002 "thanks")')

    def test_split_setup(self):
        pairs, dropped = extract.split_setup([
            "sysuse auto, clear", "gen w2 = weight * 2",
            "twoway scatter mpg weight", "replace w2 = w2 + 1",
            "scatter mpg w2"])
        assert pairs == [(["sysuse auto, clear", "gen w2 = weight * 2"],
                          "twoway scatter mpg weight"),
                         (["sysuse auto, clear", "gen w2 = weight * 2",
                           "replace w2 = w2 + 1"], "scatter mpg w2")]
        assert dropped == []
        assert "twoway" in extract.graph_words() and "lfitci" in extract.graph_words()

    def test_other_commands_are_dropped(self):
        pairs, dropped = extract.split_setup([
            "sysuse auto, clear", "shell rm x", "erase f", "! ls",
            "set more off", "graph combine a b", "twoway scatter mpg weight"])
        assert pairs == [(["sysuse auto, clear"], "twoway scatter mpg weight")]
        assert dropped == ["shell rm x", "erase f", "! ls", "set more off",
                           "graph combine a b"]

    def test_markerlabel3_setup_is_kept(self):
        body = extract.ado_programs(_MARKERLABEL3)["markerlabel3"]
        pairs, dropped = extract.split_setup(body)
        assert dropped == [] and len(pairs) == 1
        setup = pairs[0][0]
        want = ["sysuse lifeexp, clear", "keep if region==2 | region==3",
                "qui reg lexp lgnp", "predict hat", "replace pos = 9 if lexp > hat"]
        idx = [setup.index(w) for w in want]
        assert idx == sorted(idx)
        pairs, dropped = extract.split_setup([
            "sysuse sp500, clear", "by month: egen lo = min(volume)",
            "set obs 3", "set seed 1", "twoway line lo date"])
        assert pairs == [(["sysuse sp500, clear", "by month: egen lo = min(volume)",
                           "set obs 3", "set seed 1"], "twoway line lo date")]
        assert dropped == []


# ---------------------------------------------------------------- g.pdf

_GPDF = (
    "                                     Graph intro — Introduction to graphics 5\n"
    "\n"
    "A quick tour\n"
    "    graph is easy to use:\n"
    "       . use https://www.stata-press.com/data/r19/auto\n"
    "       (1978 automobile data)\n"
    "       . graph twoway scatter mpg weight\n"
    "\n"
    "\f                                     Graph intro — Introduction to graphics 6\n"
    "\n"
    "       . generate w2 = weight/1000\n"
    "       . twoway scatter mpg w2,\n"
    "             title(”A title”)                                saving(yx)\n"
    "\n"
    "     . use https://www.stata-press.com/data/r19/lifeexp2\n"
    "     . twoway (scatter lexp gnppc, mlabel(country) mlabv(pos))\n"
    "     (line hat gnppc, sort)\n"
    "             , xscale(log) legend(off)\n"
    "\n")


class TestGpdf:

    def test_commands_and_setup(self):
        cmds = extract.gpdf_commands(_GPDF)
        assert [c["cmd"] for c in cmds] == [
            "graph twoway scatter mpg weight",
            'twoway scatter mpg w2, title("A title") saving(yx)',
            "twoway (scatter lexp gnppc, mlabel(country) mlabv(pos)) "
            "(line hat gnppc, sort) , xscale(log) legend(off)"]
        assert cmds[0]["entry"] == "Graph intro" and cmds[0]["page"] == 1
        assert cmds[1]["page"] == 2
        assert cmds[0]["setup"] == ["sysuse auto, clear"]
        assert cmds[1]["setup"] == ["sysuse auto, clear", "generate w2 = weight/1000"]
        assert cmds[2]["setup"] == ["webuse lifeexp2, clear"]


# ------------------------------------------------------------ examples/

class TestExamples:

    def test_dash_lines_and_twins(self):
        text = (
            "sysuse auto, clear\n"
            "dash clear\n"
            "generate double mpg_lo = mpg - 3\n"
            "dash scatter   mpg weight,  title(\"scatter\")   name(pt01)\n"
            "dash (scatter mpg weight, hover(make)) ///\n"
            "     (lfit mpg weight), colpalette(tableau) table name(pt02)\n"
            "dash kpi mpg, label(\"MPG\")\n"
            "dash build, saving(x.html) replace\n"
            "sysuse sp500, clear\n"
            "tsset date\n"
            "dash tsline close\n")
        ex = extract.example_commands(text, "examples/x.do")
        assert [e["dash_cmd"] for e in ex] == [
            'dash scatter mpg weight, title("scatter") name(pt01)',
            "dash (scatter mpg weight, hover(make)) (lfit mpg weight), "
            "colpalette(tableau) table name(pt02)",
            "dash tsline close"]
        assert ex[0]["cmd"] == 'twoway scatter mpg weight, title("scatter") name(pt01)'
        # Flipped (D57): a twin is never edited; a line with an option twoway
        # does not have (hover(), colpalette(), table) is no comparison.
        assert ex[1]["cmd"] == ("twoway (scatter mpg weight, hover(make)) (lfit mpg weight), "
                                "colpalette(tableau) table name(pt02)")
        assert [e.get("dropped") for e in ex] == [
            None, "uses an option twoway does not have", None]
        assert ex[0]["setup"] == ["sysuse auto, clear", "generate double mpg_lo = mpg - 3"]
        assert ex[2]["setup"] == ["sysuse sp500, clear", "tsset date"]
        assert ex[1]["line"] == 5 and ex[0]["file"] == "examples/x.do"


class TestDedupeBySourceForm:

    def test_the_written_prefix_does_not_pick_the_kept_duplicate(self):
        # D58: help-twoway_lfit's `scatter mpg weight || lfit mpg weight'
        # stays the kept example though `twoway' is now written before it.
        a = {"id": "help-a-1", "source": "help", "signature": "s",
             "cmd": "twoway scatter mpg weight || lfit mpg weight",
             "source_cmd": "scatter mpg weight || lfit mpg weight"}
        b = {"id": "help-b-2", "source": "help", "signature": "s",
             "cmd": "twoway (scatter mpg weight) (lfit mpg weight)",
             "source_cmd": "twoway (scatter mpg weight) (lfit mpg weight)"}
        kept, _ = extract.dedupe([b, a])
        assert [k["id"] for k in kept] == ["help-a-1"]


class TestTwinIdentity:
    # D57: a pair's two commands differ only in the word twoway (or its
    # absence) against dash.

    def test_twin_mismatch(self):
        m = extract.twin_mismatch
        assert m("twoway scatter mpg weight, ms(oh) ||", "dash scatter mpg weight, ms(oh) ||") \
            is None
        # Flipped (D58): a pair is exactly twoway <rest> and dash <rest>.
        assert m("twoway scatter mpg weight", "dash scatter mpg weight") is None
        assert m("scatter mpg weight", "dash scatter mpg weight")
        assert m("graph twoway line le year", "dash line le year")
        assert extract.twoway_form("graph twoway line le year") == "twoway line le year"
        assert extract.twoway_form("tw (scatter y x)") == "twoway (scatter y x)"
        assert extract.twoway_form("scatter y x") == "twoway scatter y x"
        # The two defects of the 23oct2026 run.
        assert m("twoway scatter mpg weight, colorvar(price) colorlevels(8)",
                 "dash scatter mpg weight, colorvar(price) colpalette(viridis) colorlevels(8)")
        assert m("twoway scatter open close ||", "dash scatter open close")


# ------------------------------------------------------------ audit probes

_APPENDIX = """## Appendix: every verified finding, by area

### plot-types (8)

- **PT-4** The empty graph -- minor
  - twoway: 'twoway, name(e1)' draws rects; 'twoway does not take this option here' and 'graph is not a twoway plot type'.
  - dash: 'dash, saving(empty_dash.html)' draws two axes; bare 'scatter' and 'line' are words; 'scatter mpg weight | x' is not.
  - evidence: `twoway qfitci mpg weight, stdf || scatter mpg weight` webuse lbw and 'dash scatter mpg weight, title(x)'.
  - verifier: 'twoway lfit mpg weight' is a verifier span, read by hand only.

### axes (2)

- **AX-7** Something
  - twoway: 'twoway line mpg weight, sort' draws.
"""


class TestAuditProbes:

    def test_spans_and_prefixes(self):
        got = extract.audit_probe_commands(_APPENDIX)
        assert [(g["finding"], g["cmd"], g["dash_cmd"]) for g in got] == [
            ("plot:PT-4", "twoway qfitci mpg weight, stdf || scatter mpg weight",
             "dash qfitci mpg weight, stdf || scatter mpg weight"),
            ("plot:PT-4", "twoway scatter mpg weight, title(x)",
             "dash scatter mpg weight, title(x)"),
            ("AX-7", "twoway line mpg weight, sort", "dash line mpg weight, sort")]
        assert got[0]["setup"] == ["webuse lbw, clear"]
        assert got[2]["setup"] == ["sysuse auto, clear"]

    def test_freeze_keeps_the_hand_added_block(self, tmp_path):
        audit = tmp_path / "audit.md"
        audit.write_text(_APPENDIX, encoding="utf-8")
        probes = tmp_path / "audit_probes.txt"
        hand = "AX-7\tsysuse auto, clear\ttwoway scatter mpg weight, by(foreign)"
        probes.write_text("# old header\nX-1\tsysuse auto, clear\tscatter a b\n"
                          "X-2\tsysuse auto, clear\tscatter c d\n"
                          + extract.HAND_MARKER + "\n" + hand + "\n", encoding="utf-8")
        assert extract.main(["--freeze-audit", "--out", str(tmp_path / "run"),
                             "--audit", str(audit), "--probes", str(probes)]) == 0
        text = probes.read_text(encoding="utf-8")
        head, tail = text.split(extract.HAND_MARKER)
        assert tail == "\n" + hand + "\n"
        assert head.startswith("# Frozen from the drop-in audit's appendix on ")
        assert [l.split("\t")[2] for l in head.splitlines()[1:]] == [
            "twoway qfitci mpg weight, stdf || scatter mpg weight",
            "twoway scatter mpg weight, title(x)",
            "twoway line mpg weight, sort"]
        assert extract.freeze_audit(str(audit), str(probes)) == 3
        assert probes.read_text(encoding="utf-8").endswith(hand + "\n")
        recs = extract.read_audit_probes(str(probes))
        assert recs[-1]["hand"] is True and recs[0]["hand"] is False
        assert recs[-1]["dash_cmd"] == extract.to_dash(recs[-1]["cmd"])
        assert recs[-1]["setup"] == ["sysuse auto, clear"]
        bad = tmp_path / "bad.txt"
        bad.write_text("# c\nAX-1\tscatter a b\n", encoding="utf-8")
        with pytest.raises(ValueError, match="line 2"):
            extract.read_audit_probes(str(bad))

    def test_the_committed_hand_lines(self):
        path = os.path.join(_ROOT, "scripts", "corpus", "audit_probes.txt")
        lines = open(path, encoding="utf-8").read().split("\n")
        assert lines.count(extract.HAND_MARKER) == 1
        below = [l for l in lines[lines.index(extract.HAND_MARKER) + 1:]
                 if l.strip() and not l.startswith("#")]
        assert below, "no hand-added probe below the marker"
        seen = set()
        for l in [x for x in lines if x.strip() and not x.startswith("#")]:
            seen_key = " ".join(l.split())
            assert seen_key not in seen, l
            seen.add(seen_key)
        for l in below:
            finding, setup, cmd = l.split("\t")
            assert re.match(r"^(?:plot:|basic:|stat:|plat:|syn:|sil:)?[A-Z]{2,4}-[0-9]+$",
                            finding), l
            pairs, dropped = extract.split_setup(setup.split(" ; ") + [cmd])
            assert dropped == [] and len(pairs) == 1, l
            assert extract.plot_type(cmd) is not None, l
            rest = re.sub(r"^\s*(?:twoway\s+)?\(*\s*[A-Za-z_]\w*", "", cmd)
            assert rest.strip(" )"), l
            assert not any(p in cmd for p in ("<", "...", "…", "not allowed",
                                              "invalid", "not a", "does not")), l


# ---------------------------------------------------------------- filters

class TestFilters:

    def test_name_and_saving_are_stripped(self):
        cmd, gone = extract.strip_registry_options(
            "twoway scatter y x, saving(yx) name(g, replace) nodraw")
        assert cmd == "twoway scatter y x"
        assert gone == ["saving(yx)", "name(g, replace)", "nodraw"]
        cmd, gone = extract.strip_registry_options(
            'twoway scatter y x, title("saving(a) name(b)") mlabel(name)')
        assert cmd == 'twoway scatter y x, title("saving(a) name(b)") mlabel(name)'
        assert gone == []

    def test_is_schematic(self):
        for s in ("scatter yvar xvar, ...", "twoway line {it:y} x",
                  "twoway scatter varlist", "twoway connected …",
                  "twoway area yvar1 xvar"):
            assert extract.is_schematic(s), s
        for s in ("twoway scatter mpg weight",
                  'twoway bar maletotal agegrp, horizontal xvarlab(Male)',
                  "twoway function y=exp(-x/6), range(0 12)",
                  'twoway scatter mpg weight, title("Two series from one varlist")'):
            assert not extract.is_schematic(s), s

    def test_plot_type(self):
        assert extract.plot_type("twoway sc mpg weight") == "scatter"
        assert extract.plot_type("tw li mpg weight") == "line"
        assert extract.plot_type("graph twoway con mpg weight") == "connected"
        assert extract.plot_type("gr twoway (hist mpg) (scatter mpg weight)") == "histogram"
        assert extract.plot_type("twoway fn y=x") == "function"
        assert extract.plot_type("scatter mpg weight") == "scatter"
        assert extract.plot_type("tsline close") == "tsline"
        assert extract.plot_type("histogram mpg") is None
        assert extract.plot_type("graph bar mpg") is None
        assert extract.plot_type("twoway s mpg weight") is None

    def test_to_dash(self):
        assert extract.to_dash("twoway scatter y x") == "dash scatter y x"
        assert extract.to_dash("graph twoway (line y x)") == "dash (line y x)"
        assert extract.to_dash("scatter y x") == "dash scatter y x"
        assert extract.to_dash("tw(scatter y x)") == "dash (scatter y x)"


# ---------------------------------------------------------------- ids

class TestIds:

    def test_example_id_is_stable(self):
        a = extract.example_id("help", "twoway_scatter", ["sysuse auto, clear"],
                               "scatter mpg weight")
        assert a == extract.example_id("help", "twoway_scatter",
                                       ["sysuse auto, clear"], "scatter mpg weight")
        assert re.match(r"^help-twoway_scatter-[0-9a-f]{8}$", a)
        assert a != extract.example_id("help", "twoway_scatter",
                                       ["sysuse auto, clear"], "scatter mpg price")
        assert a != extract.example_id("help", "twoway_scatter", [], "scatter mpg weight")


# ---------------------------------------------------------------- dedupe

class TestDedup:

    def test_values_do_not_make_an_example(self):
        s1 = extract.signature("scatter mpg weight, mcolor(red)")
        assert s1 == "scatter|mcolor"
        assert extract.signature("scatter price length, mc(blue)") == s1
        assert extract.signature("scatter mpg weight [aw=pop], mcolor(red)") == s1
        assert extract.signature("scatter mpg weight, msymbol(T)") != s1
        assert extract.plot_types("twoway (scatter y x) (lfit y x)") == ["scatter", "lfit"]
        assert extract.plot_types("scatter y x || lfit y x") == ["scatter", "lfit"]
        assert (extract.signature("twoway (scatter y x) (lfit y x)")
                == extract.signature("scatter y x || lfit y x"))
        assert extract.option_names("scatter y x, legend(off)") == ["legend"]
        assert extract.option_names("scatter y x, leg(ring(0))") == ["legend"]
        assert extract.option_names(
            "twoway (scatter y x, mc(red) msize(2)) (line y x, sort), xla(1 2) by(g, total)"
        ) == ["by", "mcolor", "msize", "sort", "xlabel"]

    def test_option_table_and_expansion(self):
        t = extract.option_table(_ROOT)
        for pair in (("mc", "mcolor"), ("xl", "xlabel"), ("xli", "xline"), ("afc", "afcolor")):
            assert pair in t, pair
        assert extract.expand_option("mc", t) == "mcolor"
        assert extract.expand_option("xla", t) == "xlabel"
        assert extract.expand_option("xli", t) == "xline"
        assert extract.expand_option("nosuch", t) == "nosuch"

    def test_the_kept_example_and_its_duplicates(self):
        recs = [{"id": "audit-x-00000001", "source": "audit", "cmd": "scatter mpg weight, mc(red)"},
                {"id": "gpdf-y-00000002", "source": "gpdf", "cmd": "twoway scatter mpg weight, mcolor(blue)"},
                {"id": "help-z-00000003", "source": "help", "cmd": "scatter price length, mcolor(green)"},
                {"id": "help-z-00000004", "source": "help", "cmd": "scatter price length"}]
        kept, pairs = extract.dedupe(recs)
        assert [k["id"] for k in kept] == ["help-z-00000003", "help-z-00000004"]
        assert kept[0]["duplicates"] == ["audit-x-00000001", "gpdf-y-00000002"]
        assert kept[1]["duplicates"] == []
        assert pairs == [("audit-x-00000001", "help-z-00000003"),
                         ("gpdf-y-00000002", "help-z-00000003")]
        assert kept[0]["sources"] == ["help", "gpdf", "audit"]


# ---------------------------------------------------------------- the run

class TestExtract:

    def test_records_hold_no_machine_path(self, tmp_path, monkeypatch):
        stata = tmp_path / "stata"
        (stata / "ado" / "base" / "t").mkdir(parents=True)
        (stata / "ado" / "base" / "g").mkdir(parents=True)
        (stata / "ado" / "base" / "t" / "twoway_scatter.sthlp").write_text(
            '{it:({stata "gr_example auto: twoway scatter mpg weight, saving(a)":click})}\n'
            '{it:({stata "gr_example auto: scatter price length, mc(red)":click})}\n'
            '{it:({stata "gr_example auto: scatter yvar xvar":click})}\n'
            '{it:({stata "gr_example2 ex1":click})}\n'
            '{it:({stata "gr_example2 nosuch":click})}\n', encoding="utf-8")
        (stata / "ado" / "base" / "g" / "gr_example2.ado").write_text(
            "program ex1\n\tXeq sysuse auto, clear\n\tXeq erase f.gph\n"
            "\tXeq twoway line mpg weight, sort\nend\n", encoding="utf-8")
        monkeypatch.setenv("DASH_STATA_DIR", str(stata))
        out = tmp_path / "run"
        res = extract.extract(str(stata), _ROOT, str(out), pdftotext=None)
        assert res["help"] == 3 and res["gpdf"] == 0 and res["ex"] > 0
        text = (out / "examples.jsonl").read_text(encoding="utf-8")
        recs = [json.loads(l) for l in text.splitlines()]
        assert [r["id"] for r in recs] == sorted(r["id"] for r in recs)
        assert set(recs[0]) == set(extract.KEYS)

        def strings(o):
            if isinstance(o, str):
                yield o
            elif isinstance(o, list):
                for x in o:
                    yield from strings(x)
            elif isinstance(o, dict):
                for x in o.values():
                    yield from strings(x)
        for r in recs:
            for s in strings(r):
                assert not re.match(r"^/(Users|private|var|tmp|home)/", s), s
        help1 = [r for r in recs if r["source"] == "help" and "mpg weight" in r["cmd"]
                 and r["plottype"] == "scatter"]
        assert help1 and help1[0]["stripped"] == ["saving(a)"]
        assert help1[0]["datasets"] == ["auto"]
        dropped = (out / "extract_dropped.tsv").read_text(encoding="utf-8")
        assert "pdftotext" in dropped and "no such program" in dropped
        assert "not a setup command\terase f.gph" in dropped
        assert "schematic\tscatter yvar xvar" in dropped
        kept = {r["id"] for r in recs}
        for ln in (out / "extract_duplicates.tsv").read_text(encoding="utf-8").splitlines()[1:]:
            assert ln.split("\t")[1] in kept
        assert res["kept"] == len(recs)
        # D58: every command is written twoway <rest>, its twin dash <rest>;
        # the id stays the source form's (D-33-02.a), so ids do not move.
        assert all(r["cmd"].startswith("twoway ") for r in recs)
        assert all(r["dash_cmd"] == "dash " + r["cmd"][len("twoway "):] for r in recs)
        price = [r for r in recs if r["cmd"].endswith("price length, mc(red)")]
        assert price and price[0]["cmd"] == "twoway scatter price length, mc(red)"
        assert "source_cmd" not in price[0]
        assert price[0]["id"] == extract.example_id(
            "help", "twoway_scatter", price[0]["setup"], "scatter price length, mc(red)")


# ------------------------------------------- each example's own data (D52)

def _dta(names, release=118):
    """A minimal Stata .dta of release 117-119 holding only these variable names."""
    import struct
    k = len(names)
    width = 33 if release == 117 else 129
    kfmt = "<I" if release == 119 else "<H"
    return (b"<stata_dta><header><release>%d</release><byteorder>LSF</byteorder><K>"
            % release + struct.pack(kfmt, k) + b"</K><N>" + struct.pack("<Q", 0)
            + b"</N><label>\x00\x00</label><timestamp>\x00</timestamp></header><map>"
            + b"\x00" * 112 + b"</map><variable_types>" + b"\x00\x00" * k
            + b"</variable_types><varnames>"
            + b"".join(n.encode().ljust(width, b"\x00") for n in names) + b"</varnames>")


_GPDF_WRAPS = (
    "                         axis label options — Options for specifying axis labels 490\n"
    "\n"
    "       . sysuse sp500\n"
    "       . summarize volume\n"
    "           Variable         Obs        Mean    Std. dev.       Min        Max\n"
    "             volume         248    12320.68    2585.929       4103     23637\n"
    "       . twoway rcap lo hi month,\n"
    "       >           xlabel(1 ”J” 2 ”F”\n"
    "       >                  3 ”M”)\n"
    "       . twoway\n"
    "                 bar maletotal agegrp, horizontal\n"
    "        ||\n"
    "             , xtitle(”Population”)\n"
    "        ysca(noline) ylabel(none)                                        (note 1)\n"
    "        xsca(noline titlegap(-3.5))                                      (note 2)\n"
    "\n"
    "       . clear\n"
    "       . input y1 x1 y2 x2\n"
    "                y1         x1            y2           x2\n"
    "         1. 1.1 1.2 1.3 1.4\n"
    "         2. 2.1 2.2 2.3 2.4\n"
    "         3. end\n"
    "       . twoway pcarrow y1 x1 y2 x2, any_options\n")


class TestGpdfWraps:

    def test_continuations_notes_output_and_input(self):
        cmds = extract.gpdf_commands(_GPDF_WRAPS)
        assert cmds[0]["cmd"] == 'twoway rcap lo hi month, xlabel(1 "J" 2 "F" 3 "M")'
        assert cmds[0]["setup"] == ["sysuse sp500, clear", "summarize volume"]
        assert cmds[1]["cmd"] == ('twoway bar maletotal agegrp, horizontal || , '
                                  'xtitle("Population") ysca(noline) ylabel(none) '
                                  'xsca(noline titlegap(-3.5))')
        assert cmds[2]["setup"][-5:] == ["clear", "input y1 x1 y2 x2", "1.1 1.2 1.3 1.4",
                                         "2.1 2.2 2.3 2.4", "end"]
        assert extract.is_schematic(cmds[2]["cmd"])

    def test_arrows_ellipses_and_survival_setup(self):
        text = ("                  graph combine — Combine multiple graphs 112\n\n"
                "       . twoway histogram lexp, fraction\n"
                "               xsca(alt reverse) horiz\n"
                "               fxsize(25)                                         ← new\n"
                "       . use https://www.stata-press.com/data/r19/cancer, clear\n"
                "       . quietly stset studytime, fail(died)\n"
                "       . quietly streg, distribution(exponential)\n"
                "       . predict S, surv\n"
                "       . graph twoway line S _t, sort\n")
        cmds = extract.gpdf_commands(text)
        assert cmds[0]["cmd"] == ("twoway histogram lexp, fraction xsca(alt reverse) horiz "
                                  "fxsize(25)")
        pairs, dropped = extract.split_setup(cmds[1]["setup"] + [cmds[1]["cmd"]])
        assert dropped == [] and pairs[0][0] == [
            "sysuse cancer, clear", "quietly stset studytime, fail(died)",
            "quietly streg, distribution(exponential)", "predict S, surv"]
        assert extract.is_schematic("scatter . . . , . . . recast(bar)")


class TestHelpers:

    def test_a_called_helper_program_is_inlined(self):
        text = ("program pcarrow1\n\tMsg preserve\n\tpreserve\n\t_arrow_dta1\n"
                "\tXeq twoway pcarrow y1 x1 y2 x2\n\tMsg restore\nend\n\n"
                "program _arrow_dta1\n\tdrop _all\n\tset obs 2\n\tqui gen x1 = 0\nend\n")
        progs = extract.ado_programs(text)
        body = extract.inline_helpers(progs["pcarrow1"], progs)
        assert body == ["drop _all", "set obs 2", "qui gen x1 = 0",
                        "twoway pcarrow y1 x1 y2 x2"]


class TestOwnData:

    def test_dta_varnames(self, tmp_path):
        for rel in (117, 118, 119):
            p = tmp_path / ("d%d.dta" % rel)
            p.write_bytes(_dta(["make", "mpg", "weight"], rel))
            assert extract.dta_varnames(str(p)) == ["make", "mpg", "weight"]
        bad = tmp_path / "x.dta"
        bad.write_bytes(b"not a dta")
        assert extract.dta_varnames(str(bad)) is None

    def test_command_vars(self):
        assert extract.command_vars("twoway (scatter mpg weight if foreign) "
                                    "(lfit mpg weight [aw=pop]), by(foreign)") == \
            ["mpg", "weight"]
        assert extract.command_vars("scatter y1 y2 x || line L.gnp d.r year in 1/5") == \
            ["y1", "y2", "x", "gnp", "r", "year"]
        assert extract.command_vars("twoway function y=exp(x), range(0 1)") == []
        assert extract.command_vars('twoway pcarrowi 0 0 0 1 (3) "3"') == []
        assert extract.command_vars("scatter mpg weight || lfit mpg weight || if !foreign") \
            == ["mpg", "weight"]
        assert extract.command_vars("scatter y* x1-x3") == []
        assert extract.command_vars("twoway (scatter mpg weight || line le year)") == \
            ["mpg", "weight", "le", "year"]

    def test_setup_vars(self):
        ds = {"auto": ["make", "mpg", "weight"]}
        assert extract.setup_vars(["sysuse auto, clear", "gen w2 = weight",
                                   "qui predict double hat, xb"], ds) == \
            {"make", "mpg", "weight", "w2", "hat"}
        assert extract.setup_vars(["drop _all", "set obs 2", "qui gen str time = \"a\"",
                                   "input y x", "1 2", "end", "stset t"], ds) == \
            {"time", "y", "x", "_t", "_d", "_st", "_t0"}
        assert extract.setup_vars([], ds) == set()
        assert extract.setup_vars(["webuse nosuch, clear"], ds) is None
        assert extract.setup_vars(["sysuse auto, clear", "collapse mpg, by(weight)"], ds) \
            is None
        assert extract.setup_vars(["sysuse auto, clear", "encode make, gen(m)"], ds) is None

    def test_infer_setup(self):
        ds = {"auto": ["make", "mpg", "weight", "foreign"], "lifeexp": ["lexp", "gnppc"],
              "uslifeexp2": ["le", "year"]}
        cands = ["uslifeexp2", "auto", "lifeexp"]
        # the setup holds the variables (an abbreviation counts): kept as it is
        assert extract.infer_setup("scatter mp weight", ["sysuse auto, clear"], cands, ds) \
            == (["sysuse auto, clear"], None)
        # no setup, or one whose dataset lacks them: the first dataset that holds them
        assert extract.infer_setup("scatter mpg weight", [], cands, ds) == \
            (["sysuse auto, clear"], None)
        assert extract.infer_setup("scatter mpg weight", ["sysuse uslifeexp2, clear"],
                                   cands, ds) == (["sysuse auto, clear"], None)
        # a unique abbreviation picks a dataset, an ambiguous one does not
        assert extract.infer_setup("scatter mp weight", [], cands, ds) == \
            (["sysuse auto, clear"], None)
        assert extract.infer_setup("scatter m weight", [], cands, ds) == \
            (None, "no dataset holds its variables")
        assert extract.infer_setup("scatter y1 y2 x", [], cands, ds) == \
            (None, "no dataset holds its variables")
        # a setup whose variables cannot be known, and an immediate plot: kept
        assert extract.infer_setup("scatter z q", ["webuse lbw, clear"], cands, ds) == \
            (["webuse lbw, clear"], None)
        assert extract.infer_setup("twoway scatteri 1 2", [], cands, ds) == ([], None)

    def test_extract_loads_or_drops(self, tmp_path, monkeypatch):
        stata = tmp_path / "stata"
        (stata / "ado" / "base" / "a").mkdir(parents=True)
        (stata / "ado" / "base" / "t").mkdir(parents=True)
        (stata / "ado" / "base" / "a" / "auto.dta").write_bytes(
            _dta(["make", "mpg", "weight"]))
        (stata / "ado" / "base" / "t" / "uslifeexp2.dta").write_bytes(_dta(["le", "year"]))
        (stata / "ado" / "base" / "t" / "twoway_scatter.sthlp").write_text(
            '{it:({stata "gr_example auto: twoway scatter mpg weight":click})}\n',
            encoding="utf-8")
        monkeypatch.setenv("DASH_STATA_DIR", str(stata))
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(tmp_path / "cache"))
        monkeypatch.setattr(extract, "_shipped_names", lambda: frozenset({"auto", "uslifeexp2"}))
        assert extract.dataset_vars(str(stata), str(tmp_path / "cache")) == {
            "auto": ["make", "mpg", "weight"], "uslifeexp2": ["le", "year"]}
        pdf = tmp_path / "g.txt"
        pdf.write_text(
            "                  graph twoway — Twoway graphs 213\n\n"
            "       . sysuse uslifeexp2\n"
            "       . scatter mpg weight, ms(O)\n"
            "       . scatter y1 y2 x, ms(O Oh)\n", encoding="utf-8")
        (stata / "docs").mkdir()
        (stata / "docs" / "g.pdf").write_text("x")
        fake = tmp_path / "pdftotext"
        fake.write_text('#!/bin/sh\ncat "%s"\n' % pdf)
        fake.chmod(0o755)
        out = tmp_path / "run"
        extract.extract(str(stata), _ROOT, str(out), pdftotext=str(fake))
        recs = [json.loads(l) for l in (out / "examples.jsonl").read_text().splitlines()]
        g = [r for r in recs if r["source"] == "gpdf"]
        assert [(r["cmd"], r["setup"]) for r in g] == [
            # Flipped (D58): written explicitly with twoway.
            ("twoway scatter mpg weight, ms(O)", ["sysuse auto, clear"])]
        dropped = (out / "extract_dropped.tsv").read_text(encoding="utf-8")
        assert "no dataset holds its variables\tscatter y1 y2 x, ms(O Oh)" in dropped
