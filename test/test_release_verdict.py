"""scripts/release_verdict.py judges WP-27's release gate from its logs.

The gate (scripts/release_gate.do, run by scripts/run_release_gate.sh and
``make gate``) net installs dash into a scratch PLUS and runs every example
and one page per shipped scheme from the installed tree.  Stata's batch mode
returns no exit status, so the verdict is read from the log; these tests
hold the verdict to failing on each way a release can be wrong, and to
passing only on a run with none of them.
"""
import importlib.util
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "release_verdict", os.path.join(ROOT, "scripts", "release_verdict.py"))
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)

EXAMPLES = sorted(f for f in os.listdir(os.path.join(ROOT, "examples"))
                  if f.endswith(".do"))
with open(os.path.join(ROOT, "dash.pkg"), encoding="utf-8") as _fh:
    _PKG = _fh.read()
SCHEMES = sorted(re.findall(r"^f schemes/(\S+)\.scheme\s*$", _PKG, re.M))
PKG_DATE = re.search(r"^d Distribution-Date:\s*(\d{8})", _PKG, re.M).group(1)
CLEAN_LOG = ". dash build, saving(x.html)\n(dashboard saved)\n"


def _gate_log(**over):
    """A gate log with every result clean; ``over`` replaces lines by tag."""
    lines = ["GATE plus-moved ok=1", "GATE install rc=0"]
    for f in rv.INSTALLED:
        lines.append("GATE installed file=%s rc=0 inplus=1 path=/w/plus/x/%s"
                     % (f, f))
    lines.append("GATE examples n=%d" % len(EXAMPLES))
    for f in EXAMPLES:
        lines.append("GATE example file=%s rc=0 log=/w/logs/example_%s.log"
                     % (f, f))
    lines.append("GATE schemes n=%d" % len(SCHEMES))
    for s in SCHEMES:
        lines.append("GATE scheme name=%s rc=0 log=/w/logs/scheme_%s.log"
                     % (s, s))
    lines += ["GATE adoupdate-same rc=0 pkglist=[]",
              "GATE newer-source bumped=1",
              "GATE trk-source moved=1",
              "GATE adoupdate-newer rc=0 pkglist=[dash]",
              "GATE restored ok=1", "GATE done"]
    text = "\n".join(lines) + "\n"
    for old, new in over.items():
        text = text.replace(old, new)
    return text


def _reader(logs=None):
    logs = logs or {}

    def read(path):
        if path in logs:
            return logs[path]
        if path.startswith("/w/logs/"):
            return CLEAN_LOG
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return read


def _judge(text, logs=None, min_date=None):
    return rv.verdict(text, ROOT, min_date or PKG_DATE, read=_reader(logs))


class TestACleanRunPasses:

    def test_every_result_clean_passes(self):
        ok, lines = _judge(_gate_log())
        assert ok, lines
        assert lines[-1] == "verdict: PASS"
        assert lines[0] == ("release gate: %d of %d examples and %d of %d "
                            "scheme pages clean" % (len(EXAMPLES), len(EXAMPLES),
                                                    len(SCHEMES), len(SCHEMES)))

    def test_the_corpus_is_the_repositorys(self):
        assert len(EXAMPLES) == 12 and len(SCHEMES) >= 14


class TestEachFailureFails:

    @pytest.mark.parametrize("old,new", [
        ("GATE install rc=0", "GATE install rc=601"),
        ("GATE plus-moved ok=1", "GATE plus-moved ok=0"),
        ("file=dash.ado rc=0 inplus=1", "file=dash.ado rc=0 inplus=0"),
        ("file=locator rc=0", "file=locator rc=601"),
        ("GATE adoupdate-same rc=0 pkglist=[]",
         "GATE adoupdate-same rc=0 pkglist=[dash]"),
        ("GATE adoupdate-newer rc=0 pkglist=[dash]",
         "GATE adoupdate-newer rc=0 pkglist=[]"),
        ("GATE newer-source bumped=1", "GATE newer-source bumped=0"),
        ("GATE trk-source moved=1", "GATE trk-source moved=0"),
        ("GATE restored ok=1", "GATE restored ok=0"),
        ("GATE done", ""),
    ])
    def test_a_bad_gate_line(self, old, new):
        ok, lines = _judge(_gate_log(**{old: new}))
        assert not ok and lines[-1] == "verdict: FAIL", lines

    def test_an_example_that_fails(self):
        f = EXAMPLES[0]
        ok, lines = _judge(_gate_log(**{
            "file=%s rc=0" % f: "file=%s rc=198" % f}))
        assert not ok
        assert any(f in l and "rc=198" in l for l in lines)

    def test_an_example_never_run(self):
        f = EXAMPLES[-1]
        text = "\n".join(l for l in _gate_log().splitlines()
                         if "file=%s " % f not in l)
        ok, lines = _judge(text)
        assert not ok
        assert any("%s: reported 0 times" % f in l for l in lines)

    def test_an_example_run_twice(self):
        f = EXAMPLES[0]
        line = [l for l in _gate_log().splitlines() if "file=%s " % f in l][0]
        ok, lines = _judge(_gate_log() + line + "\n")
        assert not ok

    def test_a_shipped_scheme_never_built(self):
        s = SCHEMES[0]
        text = "\n".join(l for l in _gate_log().splitlines()
                         if "name=%s " % s not in l)
        ok, lines = _judge(text)
        assert not ok
        assert any("scheme %s: built 0 times" % s in l for l in lines)

    @pytest.mark.parametrize("printed", [
        "dash: ignoring unsupported option(s): foo",
        "dash: scheme 's1color' was not found for 'g1'; using s2color",
        "dash: by() sub-option(s) not implemented and ignored: xyz",
        "/x/dash_render.py:10: UserWarning: something",
        "ERROR:bokeh.core.validation.check:E-1024 (CDSVIEW_FILTERS_WITH_CONNECTED)",
        "Traceback (most recent call last):",
        "dash: color(zz) is not a recognised colour; ignoring it.",
    ])
    def test_an_example_that_prints_a_diagnostic(self, printed):
        f = EXAMPLES[0]
        ok, lines = _judge(_gate_log(), logs={
            "/w/logs/example_%s.log" % f: CLEAN_LOG + printed + "\n"})
        assert not ok
        assert any("printed: " + printed.strip() in l for l in lines), lines

    def test_a_scheme_page_that_falls_back(self):
        s = SCHEMES[0]
        ok, lines = _judge(_gate_log(), logs={
            "/w/logs/scheme_%s.log" % s:
                "dash: scheme '%s' not found. Using fallback\n" % s})
        assert not ok

    def test_a_missing_log_fails(self):
        f = EXAMPLES[0]

        def read(path):
            return None if path.endswith("example_%s.log" % f) else \
                _reader()(path)
        ok, lines = rv.verdict(_gate_log(), ROOT, PKG_DATE, read=read)
        assert not ok and any("no log" in l for l in lines)

    def test_a_stale_distribution_date_fails(self):
        ok, lines = _judge(_gate_log(), min_date="29991231")
        assert not ok
        assert any("older than the newest change" in l for l in lines)

    def test_no_date_to_compare_with_fails(self):
        ok, lines = rv.verdict(_gate_log(), ROOT, "", read=_reader())
        assert not ok

    def test_an_empty_log_fails(self):
        ok, lines = _judge("")
        assert not ok


class TestWhatCountsAsADiagnostic:

    def test_an_echoed_command_is_not_one(self):
        text = (". // a comment that says fallback and ignoring\n"
                "> scheme(not found) warning\n")
        assert rv.diagnostics(text) == []

    def test_an_example_may_declare_the_note_it_means(self):
        src = '*! release-gate allows: ignoring unsupported option(s): foo\n'
        text = "dash: ignoring unsupported option(s): foo\n"
        assert rv.diagnostics(text, rv.allowed_in(src)) == []
        assert rv.diagnostics("dash: ignoring unsupported option(s): bar\n",
                              rv.allowed_in(src)) != []

    def test_no_shipped_example_declares_a_diagnostic(self):
        """Today every example is meant to run silent; a declaration is a
        decision to review, so adding one changes this test on purpose."""
        for f in EXAMPLES:
            with open(os.path.join(ROOT, "examples", f), encoding="utf-8") as fh:
                assert rv.allowed_in(fh.read()) == (), f

    def test_a_gate_line_with_a_spaced_path_keeps_it_whole(self):
        (tag, kv), = rv.parse(
            "GATE installed file=dash.ado rc=0 inplus=1 path=/a b/c/dash.ado\n")
        assert tag == "installed" and kv["path"] == "/a b/c/dash.ado"


class TestTheGateIsWiredUp:

    def test_make_gate_runs_the_gate_and_release_runs_check_first(self):
        with open(os.path.join(ROOT, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        assert re.search(r"^gate:\n\t.*scripts/run_release_gate\.sh", mk, re.M)
        assert re.search(r"^release: check gate$", mk, re.M)

    def test_the_runner_uses_the_console_binary_in_batch(self):
        with open(os.path.join(ROOT, "scripts", "run_release_gate.sh"),
                  encoding="utf-8") as fh:
            sh = fh.read()
        assert 'arch -arm64 "$STATA" -b do' in sh
        assert 'STATATMP="$dir/tmp/"' in sh
        assert "StataMP.app" not in sh and "open -a" not in sh
        assert "scripts/release_verdict.py" in sh

    def test_the_gate_sets_nobrowser_and_restores_plus(self):
        with open(os.path.join(ROOT, "scripts", "release_gate.do"),
                  encoding="utf-8") as fh:
            do = fh.read()
        assert "global dash_nobrowser 1" in do
        assert 'sysdir set PLUS "`plus0\'"' in do
        assert "set python_exec" not in do

    def test_the_gate_runs_on_stata_and_plus_alone(self):
        """dash needs no other Stata package: the gate kept jsonio's
        directory on the ado-path after dash stopped using jsonio
        (24sep2026), so an install that still needed it would have passed.
        The path is Stata's own directories and the scratch PLUS only."""
        with open(os.path.join(ROOT, "scripts", "release_gate.do"),
                  encoding="utf-8") as fh:
            do = fh.read()
        code = "\n".join(ln.split("//", 1)[0] for ln in do.splitlines()
                         if not ln.lstrip().startswith("*"))
        assert "jsonio" not in code
        sets = re.findall(r'st_global\("S_ADO",\s*(.*)\)\s*$', code, re.M)
        assert sets == ['"BASE;SITE;PLUS"'], sets


class TestTheGateScriptIsReadWhole:

    def test_no_comment_opens_a_block_comment(self):
        """Stata opens a block comment at a /* anywhere outside a string,
        even inside a *! line: the first run of the gate read
        ``examples/*.do`` in its header as one, and every line after it --
        the whole gate -- was a comment, with no GATE line in the log."""
        with open(os.path.join(ROOT, "scripts", "release_gate.do"),
                  encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        bad = [(n, ln) for n, ln in enumerate(lines, 1)
               if "/*" in re.sub(r'"[^"]*"', '""', ln)]
        assert not bad, bad

    def test_the_runner_finds_the_log_batch_stata_names(self):
        """Batch Stata names its log after the command line's last word
        (measured: examples.log), so the runner takes the .log it wrote."""
        with open(os.path.join(ROOT, "scripts", "run_release_gate.sh"),
                  encoding="utf-8") as fh:
            sh = fh.read()
        assert 'ls -t "$dir"/*.log' in sh

    def test_a_wrapped_gate_line_is_joined(self):
        """Stata wraps a log line at its line size and continues it after
        "> "; the first real run's paths were cut there (measured)."""
        (tag, kv), = rv.parse("GATE example file=a.do rc=0 log=/x/very/lo\n"
                              "> ng/path.log\n")
        assert kv["log"] == "/x/very/long/path.log"

    def test_the_gate_sets_a_wide_line_size(self):
        with open(os.path.join(ROOT, "scripts", "release_gate.do"),
                  encoding="utf-8") as fh:
            assert "set linesize 255" in fh.read()
