"""WP-30 P1.28a: what dash leaves in r() and what it says about graph export.

dash is rclass: a command that writes a file stores its absolute path in
r(filename) and nothing else reaches r(); a command that writes a file
notes, when Stata holds a graph in memory, that graph export writes that
graph and not the dashboard; saving() with a suffix graph export writes
writes HTML (or .py) with a note.  These tests read dash.ado,
dash_parse.mata and dash.sthlp as text; the behaviour is certified by
test_export.cscript GE-01..GE-15, test_path_validation.cscript
GE-16..GE-19, test_serve_launch.cscript GE-20 and test_wp30_truth.cscript
GE-21..GE-24.  test/fixtures/graph_export_truth.json is graph export's
measured behaviour (scripts/extract_graph_export_truth.do).
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "graph_export_truth.json")


def _read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _code(text):
    """Text with // comments and comment-only lines removed."""
    out = []
    for ln in text.splitlines():
        if ln.lstrip().startswith(("//", "*")):
            continue
        out.append(re.sub(r"\s//.*$", "", ln))
    return "\n".join(out)


def _program_body(src, name):
    m = re.search(r"^program define %s(?:,[ \t\w]*)?\s*$(.*?)^end\s*$"
                  % re.escape(name), src, re.M | re.S)
    assert m, "program %s not found" % name
    return m.group(1)


def _mata_body(src, name):
    m = re.search(r"^[a-z ]*\b%s\([^)]*\)\s*\{" % re.escape(name), src, re.M)
    assert m, "Mata function %s not found" % name
    depth, i = 0, m.end() - 1
    while True:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[m.end():i]
        i += 1


def _statements(body):
    return [ln.strip() for ln in _code(body).splitlines() if ln.strip()]


ADO = _read("dash.ado")
MATA = _read("dash_parse.mata")
HELP = _read("dash.sthlp")


class TestDashIsRclass:
    def test_the_program_is_rclass(self):
        assert re.search(r"^program define dash, rclass\s*$", ADO, re.M)

    def test_every_writing_route_posts_the_result(self):
        body = _code(_program_body(ADO, "dash"))
        # Flipped (14oct2026): the twoway-prefix route ("strip") is gone --
        # dash replaces twoway, so `dash twoway ...' is refused r(198).
        assert "_dash_strip_prefix" not in body
        routes = {
            "build": r'_dash_build `macval\(_args\)\'\n\s*_dash_result\n\s*return add\n\s*exit',
            "plot": r'_dash_plot `macval\(0\)\'\n\s*_dash_result\n\s*return add\s*$',
        }
        missing = [k for k, pat in routes.items() if not re.search(pat, body)]
        assert not missing, "routes that do not post the result: %s" % missing
        for sub in ("kpi", "clear", "serve"):
            seg = re.search(r'"%s" \{(.*?)\}' % sub, body, re.S).group(1)
            assert "_dash_result" not in seg and "return" not in seg, sub

    def test_only_the_result_reaches_r(self):
        dash = _code(_program_body(ADO, "dash"))
        assert not re.search(r"\breturn (local|scalar|matrix)\b", dash)
        res = _code(_program_body(ADO, "_dash_result"))
        assert len(re.findall(r"\breturn local\b", res)) == 1
        assert "return local filename `\"`macval(_rf)'\"'" in res
        assert 'st_global("dash__rfile")' in res
        code = _code(ADO)
        assert "$dash__rfile" not in code and "macval(global(" not in code
        # The six sites: read and drop in _dash_result, two sets, two clears.
        assert len(re.findall(r"dash__rfile", code)) == 6


class TestTheWritersSetTheResultLast:
    def test_each_writer_sets_it_last(self):
        for prog, local in (("_dash_render_immediate", "saving_path"),
                            ("_dash_build", "saving")):
            last = _statements(_program_body(ADO, prog))[-1]
            assert last == ('mata: st_global("dash__rfile", _dash_abs_path('
                            'st_local("%s"), c("pwd"), c("os")))' % local), prog

    def test_each_route_clears_it_first(self):
        for prog in ("_dash_plot", "_dash_build"):
            st = _statements(_program_body(ADO, prog))
            assert st[:2] == ["version 19", "capture macro drop dash__rfile"], prog


class TestTheGraphExportNote:
    def test_it_reads_graph_memory_and_uses_the_note_channel(self):
        res = _code(_program_body(ADO, "_dash_result"))
        assert "quietly graph dir, memory" in res
        assert "_dash_graph_names(" in res
        assert res.count("_dash_note(") == 1
        pat = re.compile(r"^\s*((quietly|capture|noisily|cap|qui) +)*"
                         r"(graph +(describe|display|drop|export)|translate) ")
        hits = [ln for ln in _code(ADO).splitlines() if pat.match(ln)]
        assert not hits, hits


class TestTheImageSuffixes:
    def test_the_row_is_the_suffixes_graph_export_recognises(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            fx = json.load(fh)
        written = sorted(k for k, v in fx["suffixes"].items()
                         if "not recognized" not in v["first"])
        body = _mata_body(MATA, "_dash_saving_parse")
        m = re.search(r"sfx = \(([^)]*)\)", body, re.S)
        assert m, "no suffix row in _dash_saving_parse"
        row = re.findall(r'"([a-z]+)"', m.group(1))
        assert sorted(row) == written

    def test_both_routes_note_a_replaced_suffix(self):
        for prog in ("_dash_render_immediate", "_dash_build"):
            body = _code(_program_body(ADO, prog))
            m = re.search(r'if "`_sv_img\'" != "" \{\s*mata: _dash_note\((.*?)\n', body)
            assert m and 'st_local("_sv_img")' in m.group(1), prog


class TestTheHelpStatesWhatDashReturns:
    def test_stored_results_is_a_section_in_the_jump_list(self):
        assert '{viewerjumpto "Exporting"         "dash##export"}' in HELP
        assert '{viewerjumpto "Stored results"    "dash##results"}' in HELP
        sec = HELP.split("{marker results}", 1)[1].split("{marker ", 1)[0]
        assert "{p2col:{cmd:r(filename)}}" in sec
        for route in ("{cmd:dash build} with {cmd:server}", "preview page",
                      "{cmd:dash serve} store nothing",
                      "A command\nthat stops with an error stores nothing"):
            assert route in sec, route

    def test_exporting_states_what_dash_cannot_do(self):
        sec = HELP.split("{marker export}", 1)[1].split("{marker ", 1)[0]
        flat = " ".join(sec.split())
        claims = ['"no Graph window open", {cmd:r(601)}',
                  "graphs in memory: Graph)",
                  "{cmd:saving(fig.png)} writes {cmd:fig.html}",
                  "{cmd:.tif}, {cmd:.gif}, {cmd:.emf} or {cmd:.wmf}",
                  "has no SVG drawing mode",
                  "the tab that is showing and none of the others",
                  "A do-file cannot write an image of a dashboard"]
        missing = [c for c in claims if c not in flat]
        assert not missing, missing


class TestTheGraphExportFixture:
    def test_it_holds_the_measured_answers(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            fx = json.load(fh)
        bad = []
        if sorted(fx["_meta"]) != ["born_date", "dash_commit", "extracted",
                                   "mode", "os", "source", "stata_version"]:
            bad.append("_meta keys %s" % sorted(fx["_meta"]))
        want = {"no_graph": (601, "no Graph window open"),
                "no_such_name": (693, "could not find Graph window"),
                "nodraw_only": (601, "no Graph window open")}
        for k, (rc, first) in want.items():
            if (fx["cases"][k]["rc"], fx["cases"][k]["first"]) != (rc, first):
                bad.append("%s %s" % (k, fx["cases"][k]))
        if fx["cases"]["nodraw_only"]["memory"] != "Graph":
            bad.append("nodraw_only memory")
        if (fx["cases"]["dropped"]["rc"], fx["cases"]["dropped"]["memory"]) != (0, ""):
            bad.append("dropped %s" % fx["cases"]["dropped"])
        s6 = fx["cases"]["saving_png"]
        if (s6["named_as_typed"], s6["gph_appended"]) != (1, 0):
            bad.append("saving_png %s" % s6)
        if fx["return_after_twoway"] != {"macros": 0, "scalars": 0}:
            bad.append("return_after_twoway %s" % fx["return_after_twoway"])
        if len(fx["suffixes"]) != 17:
            bad.append("%d suffix spellings" % len(fx["suffixes"]))
        written = sorted(k for k, v in fx["suffixes"].items()
                         if "not recognized" not in v["first"])
        if written != ["emf", "eps", "gif", "jpeg", "jpg", "pdf", "png", "ps",
                       "svg", "tif", "wmf"]:
            bad.append("recognised %s" % written)
        assert not bad, bad
