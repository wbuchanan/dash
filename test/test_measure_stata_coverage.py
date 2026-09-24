"""test_measure_stata_coverage.py -- the coverage measurement measures.

scripts/measure_stata_coverage.py is how WP-24 learned which Stata programs
and Mata functions the certification suite runs (Stata's profiler cannot:
clear all destroys it).  A measurement that silently missed a unit would
report it covered or uncovered wrongly, so each step is held here: the
inventory, the instrumentation (every unit probed exactly once, nothing else
changed), the generated runner, and the reading of what the probes wrote.
Nothing here starts Stata.
"""
import importlib.util
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)


@pytest.fixture(scope="module")
def m():
    """The script under test, loaded without leaving a scripts/__pycache__
    behind (no .gitignore rule covers it)."""
    path = os.path.join(_ROOT, "scripts", "measure_stata_coverage.py")
    spec = importlib.util.spec_from_file_location("_msc_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


_ADO = "\n".join([
    "*! header",
    "program define alpha",          # 2
    "    version 16.0",
    "    syntax [, A(string)]",
    "    display \"a\"",
    "end",
    "/* program define ghost",
    "   end */",
    "program beta, rclass ///",      # 9
    "    sortpreserve",
    "    args x y",
    "    capture program drop alpha",
    "end",
    "program define gamma",          # 14
    "    syntax [, ///",
    "        B(string) ///",
    "    ]",
    "    if 1 {",
    "        args z",
    "    }",
    "end",
    "program drop old_thing",        # 22: not a definition
])

_MATA = "\n".join([
    "mata:",
    "real scalar f1(string scalar s) {",
    "    real scalar n",
    "    return(strlen(s))",
    "}",
    "void f2(string scalar a,",
    "        string scalar b)",
    "{",
    "    st_local(a, b)",
    "}",
    "string scalar f3(string scalar s) { return(s) }",
    "// real scalar f4(real scalar x)",
    "end",
])


class TestTheInventory:

    def test_the_real_sources(self, m):
        units = m.inventory(_ROOT)
        kinds = {}
        for f, kind, _name, _line in units:
            kinds[(f, kind)] = kinds.get((f, kind), 0) + 1
        assert kinds[("dash.ado", "ado")] >= 56
        assert kinds[("dash_setup.ado", "ado")] >= 7
        assert kinds[("dash_parse.mata", "mata")] >= 55
        names = [u[2] for u in units]
        assert len(names) == len(set(names)), "a unit counted twice"

    def test_definitions_only(self, m, tmp_path):
        p = tmp_path / "x.ado"
        p.write_text(_ADO, encoding="utf-8")
        assert m.ado_programs(str(p)) == [("alpha", 2), ("beta", 9),
                                          ("gamma", 14)]
        q = tmp_path / "x.mata"
        q.write_text(_MATA, encoding="utf-8")
        assert m.mata_functions(str(q)) == [("f1", 2), ("f2", 6), ("f3", 11)]


class TestTheInstrumentation:

    def test_ado_entry_and_body_probes(self, m):
        out, names, bodies = m.instrument_ado(_ADO)
        lines = out.split("\n")
        assert names == {"alpha": 1, "beta": 1, "gamma": 1}
        assert bodies == {"alpha", "beta", "gamma"}
        # The entry probe follows the define line and its continuations.
        i = lines.index("program beta, rclass ///")
        assert lines[i + 1] == "    sortpreserve"
        assert lines[i + 2] == '    mata: _pc_rec("ado:beta")'
        # The body probe follows the whole syntax or args statement.
        j = lines.index("    syntax [, A(string)]")
        assert lines[j + 1] == '    mata: _pc_rec("ado+:alpha")'
        j = lines.index("    args x y")
        assert lines[j + 1] == '    mata: _pc_rec("ado+:beta")'
        # gamma's syntax spans three lines: the probe follows the last, and
        # the args inside its if block gets none.
        k = lines.index("    ]")
        assert lines[k + 1] == '    mata: _pc_rec("ado+:gamma")'
        assert out.count("ado+:gamma") == 1
        # A comment is not a definition.
        assert "ghost" not in "".join(l for l in lines if "_pc_rec" in l)
        # Nothing else changed.
        assert "\n".join(l for l in lines if "_pc_rec" not in l) == _ADO

    def test_a_program_that_parses_nothing_gets_no_body_probe(self, m):
        out, names, bodies = m.instrument_ado(
            "program define p\n    display 1\n    args late\nend\n")
        # args after another statement is still the program's own line.
        assert names == {"p": 1} and bodies == {"p"}
        out, names, bodies = m.instrument_ado(
            "program define q\n    display 1\nend\n")
        assert names == {"q": 1} and bodies == set()
        assert "ado+:" not in out

    def test_mata_probe_first_statement(self, m):
        out, names = m.instrument_mata(_MATA)
        assert names == {"f1": 1, "f2": 1, "f3": 1}
        lines = out.split("\n")
        i = lines.index("real scalar f1(string scalar s) {")
        assert lines[i + 1] == '    _pc_rec("mata:f1")'
        j = lines.index("{")
        assert lines[j + 1] == '    _pc_rec("mata:f2")'
        assert ('string scalar f3(string scalar s) { _pc_rec("mata:f3");  '
                'return(s) }') in lines
        # A commented-out signature is not probed.
        assert "f4" not in out.replace("// real scalar f4", "")
        restored = "\n".join(
            l.replace(' _pc_rec("mata:f3"); ', "") for l in lines
            if not re.match(r'^\s*_pc_rec\(', l))
        assert restored == _MATA

    def test_a_signature_with_no_body_is_refused(self, m):
        with pytest.raises(ValueError, match="no opening brace"):
            m.instrument_mata("real scalar f(real scalar x)\n")

    def test_the_real_sources_are_probed_once_each(self, m):
        units = m.inventory(_ROOT)
        seen = {}
        for f in ("dash.ado", "dash_setup.ado"):
            with open(os.path.join(_ROOT, f), encoding="utf-8") as fh:
                _out, names, _b = m.instrument_ado(fh.read())
            seen[f] = names
        with open(os.path.join(_ROOT, "dash_parse.mata"), encoding="utf-8") as fh:
            seen["dash_parse.mata"] = m.instrument_mata(fh.read())[1]
        for f, _kind, name, _line in units:
            assert seen[f].get(name) == 1, (f, name)
        assert sum(len(v) for v in seen.values()) == len(units)


_RUNNER = "\n".join([
    "clear all",
    'adopath ++ "/somewhere/dash/"',
    'local dashdir "/somewhere/dash"',
    'local testdir "`dashdir\'/test"',
    'cd "`dashdir\'"',
    "local n_pass = 0",
    "// " + "-" * 64,
    "// 1. test_a.cscript",
    "// " + "-" * 64,
    'display as text "[ RUN ] test_a.cscript"',
    'cd "`testdir\'"',
    "capture noisily {",
    '    do "test_a.cscript"',
    "}",
    "local rc = _rc",
    "capture program drop _special_a",
    "// " + "-" * 64,
    "// 2. test_b.cscript",
    "// " + "-" * 64,
    'display as text "[ RUN ] test_b.cscript"',
    "capture noisily {",
    '    do "test_b.cscript"',
    "}",
    "local rc = _rc",
    "// " + "-" * 64,
    "// Summary",
    "// " + "-" * 64,
    'display "Results"',
])


class TestTheGeneratedRunner:

    def test_paths_marks_and_flushes(self, m):
        src, n = m.runner_do("/w", "/w/tree", _RUNNER)
        assert n == 2
        assert 'adopath ++ "/w/tree/"' in src
        assert "StataJSON" not in src
        assert 'local dashdir "/w/tree"' in src
        assert 'adopath ++ "/w/lib/"\nmata: mata mlib index' in src
        assert src.count('mata: _pc_mark("test_a.cscript")') == 1
        assert src.count("local rc = _rc\nmata: _pc_flush()") == 2
        assert "/somewhere/dash/" not in src

    def test_a_malformed_runner_is_refused(self, m):
        with pytest.raises(ValueError):
            m.runner_do("/w", "/w/tree", "clear all\n")
        # A second directory on the path (jsonio's, before 24sep2026) is
        # not the runner this reads.
        with pytest.raises(ValueError, match="one adopath line"):
            m.runner_do("/w", "/w/tree", _RUNNER.replace(
                "clear all", 'clear all\nadopath ++ "/somewhere/StataJSON/"'))
        broken = _RUNNER.replace("local rc = _rc\ncapture program drop",
                                 "capture program drop")
        with pytest.raises(ValueError, match="rc captures"):
            m.runner_do("/w", "/w/tree", broken)

    def test_selected_scripts_keep_their_own_blocks(self, m):
        src = m.select_scripts(_RUNNER, ["test_b.cscript", "test_new.cscript"])
        assert src.index("[ RUN ] test_b.cscript") < \
            src.index("[ RUN ] test_new.cscript")
        assert "[ RUN ] test_a.cscript" not in src
        assert "_special_a" not in src
        assert src.rstrip().endswith('display "Results"')
        # A script not in the runner gets a generic block the runner reads.
        out, n = m.runner_do("/w", "/w/tree", src)
        assert n == 2
        assert 'mata: _pc_mark("test_new.cscript")' in out

    def test_a_bad_script_name_is_refused(self, m):
        for bad in ("../x.cscript", "test_a.do", 'test_"x.cscript'):
            with pytest.raises(ValueError):
                m.select_scripts(_RUNNER, [bad])

    def test_the_real_runner_is_read(self, m):
        with open(os.path.join(_HERE, "run_all_cscripts.do"),
                  encoding="utf-8") as fh:
            real = fh.read()
        n_real = len(re.findall(r'^display as text "\[ RUN \] ', real, re.M))
        src, n = m.runner_do("/w", "/w/tree", real)
        assert n == n_real >= 59
        sel = m.select_scripts(real, ["test_parser.cscript"])
        assert m.runner_do("/w", "/w/tree", sel)[1] == 1

    def test_the_recorder_writes_to_the_work_directory(self, m):
        do = m.recorder_do("/w/x")
        assert 'fopen("/w/x/hits.log", "a")' in do
        assert 'mlib create lpcrec, dir("/w/x/lib") replace' in do
        assert "_pc_rec() _pc_mark() _pc_flush(), dir(\"/w/x/lib\")" in do


_HITS = "\n".join([
    "== (runner setup)",
    "== test_a.cscript",
    "## lifetime",
    "+ado:alpha\t1",
    "+mata:f1\t1",
    "+mata:f1\t2",
    "+mata:f1\t4",
    "## lifetime",          # a clear all mid-script: 4 is a lower bound
    "+mata:f1\t1",
    "+mata:f1\t2",
    "=mata:f1\t3",
    "## flushed",
    "== test_b.cscript",
    "## lifetime",
    "+ado+:alpha\t1",
    "=ado+:alpha\t1",
    "## flushed",
    "== test_c.cscript",     # Stata stopped before the flush
    "## lifetime",
    "+mata:f2\t1",
    "+mata:f2\t2",
    "",
])


class TestReadingTheHits:

    def test_counts_lifetimes_and_exactness(self, m, tmp_path):
        p = tmp_path / "hits.log"
        p.write_text(_HITS, encoding="utf-8")
        h = m.parse_hits(str(p))
        assert h["mata:f1"]["calls"] == 7
        assert h["mata:f1"]["exact"] is False
        assert h["mata:f1"]["scripts"] == {"test_a.cscript": 7}
        # Counted in a lifetime a clear all ended, never flushed: a count
        # that is a lower bound, not an exact one.
        assert h["ado:alpha"]["calls"] == 1
        assert h["ado:alpha"]["exact"] is False
        assert h["ado+:alpha"] == {"calls": 1, "exact": True,
                                   "scripts": {"test_b.cscript": 1}}
        # Its last lifetime was never flushed: a lower bound.
        assert h["mata:f2"] == {"calls": 2, "exact": False,
                                "scripts": {"test_c.cscript": 2}}
        assert "mata:f3" not in h

    def test_the_report_names_the_units_never_run(self, m, tmp_path, capsys,
                                                  monkeypatch):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "dash.ado").write_text(_ADO, encoding="utf-8")
        (repo / "dash_setup.ado").write_text("", encoding="utf-8")
        (repo / "dash_parse.mata").write_text(_MATA, encoding="utf-8")
        work = tmp_path / "work"
        work.mkdir()
        (work / "hits.log").write_text(_HITS, encoding="utf-8")
        rows = m.report(str(work), repo=str(repo),
                        json_out=str(work / "r.json"))
        by = {r["name"]: r for r in rows}
        assert by["alpha"]["executed"] and by["alpha"]["body_calls"] == 1
        assert not by["beta"]["executed"] and by["beta"]["body_calls"] == 0
        assert by["f1"]["calls"] == 7 and not by["f1"]["exact"]
        assert by["f2"]["executed"] and not by["f3"]["executed"]
        out = capsys.readouterr().out
        assert "never executed: beta, gamma, f3" in out
        assert (work / "r.json").exists()


class TestPrepare:

    def _fake_repo(self, tmp_path):
        repo = tmp_path / "repo"
        (repo / "test").mkdir(parents=True)
        (repo / "dash.ado").write_text(_ADO, encoding="utf-8")
        (repo / "dash_setup.ado").write_text(
            "program define dash_setup\n    syntax\nend\n", encoding="utf-8")
        (repo / "dash_parse.mata").write_text(_MATA, encoding="utf-8")
        (repo / "test" / "run_all_cscripts.do").write_text(_RUNNER,
                                                           encoding="utf-8")
        (repo / "test" / "test_a.cscript").write_text("", encoding="utf-8")
        (repo / "test" / "test_b.cscript").write_text("", encoding="utf-8")
        return repo

    def test_a_scratch_tree_is_instrumented(self, m, tmp_path):
        repo = self._fake_repo(tmp_path)
        work = tmp_path / "work"
        tree, n = m.prepare(str(work), repo=str(repo))
        assert n == 2
        text = (work / "tree" / "dash.ado").read_text(encoding="utf-8")
        assert '_pc_rec("ado:alpha")' in text
        assert (work / "hits.log").read_text() == ""
        assert (work / "build_recorder.do").exists()
        assert (work / "run_measure.do").exists()
        # The repository itself is never written.
        assert "_pc_rec" not in (repo / "dash.ado").read_text(encoding="utf-8")

    def test_only_the_named_scripts(self, m, tmp_path):
        repo = self._fake_repo(tmp_path)
        _tree, n = m.prepare(str(tmp_path / "work"), repo=str(repo),
                             scripts=["test_b.cscript"])
        assert n == 1
        with pytest.raises(SystemExit):
            m.prepare(str(tmp_path / "w2"), repo=str(repo),
                      scripts=["test_missing.cscript"])

    def test_a_work_directory_inside_the_repository_is_refused(self, m,
                                                               tmp_path):
        repo = self._fake_repo(tmp_path)
        with pytest.raises(SystemExit, match="outside"):
            m.prepare(str(repo / "scratch"), repo=str(repo))

    def test_a_work_path_stata_cannot_quote_is_refused(self, m, tmp_path):
        repo = self._fake_repo(tmp_path)
        with pytest.raises(SystemExit, match="quote"):
            m.prepare(str(tmp_path / 'w"x'), repo=str(repo))


def test_stata_runs_the_console_binary_with_its_own_tmp(m, monkeypatch,
                                                        tmp_path):
    seen = {}

    def fake_run(argv, cwd=None, env=None, check=None):
        seen.update(argv=argv, cwd=cwd, env=env)
    monkeypatch.setattr(m.subprocess, "run", fake_run)
    log = m._stata(str(tmp_path), str(tmp_path / "x.do"))
    assert seen["argv"] == ["arch", "-arm64", "/usr/local/bin/stata-mp",
                            "-b", "do", str(tmp_path / "x.do")]
    assert seen["env"]["STATATMP"] == str(tmp_path / "stata_tmp") + "/"
    assert log == str(tmp_path / "x.log")


def test_units_lists_every_unit(m, capsys):
    assert m.main(["units"]) == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == len(m.inventory(_ROOT))
    assert all(len(l.split("\t")) == 4 for l in lines)
