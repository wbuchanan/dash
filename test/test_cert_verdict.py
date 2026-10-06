"""The certification suite's verdict, and the wiring of `make check' (WP-25).

scripts/cert_verdict.py judges a run of test/run_all_cscripts.do from its log,
because Stata's batch mode does not hand the runner's exit status back: the
run passes only when every script the runner registers reported PASS, none
FAIL or SKIP, and the runner's own summary agrees.  The Makefile, the scripts
it calls and the pre-push hook are checked for what they run.
"""
import os
import re
import stat
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
import cert_verdict as V  # noqa: E402

_RUNNER = """\
capture noisily {
    do "test_a.cscript"
}
cd "`dashdir'"
capture noisily {
    do "test/test_b.cscript"
}
"""


def _log(results, summary=True):
    """A runner log with one line per (status, script) and its summary."""
    lines = [". display as text \"[ RUN ] ...\""]
    for status, name in results:
        tail = {"PASS": "", "FAIL": "  (rc=9)",
                "SKIP": "  (dependency unavailable)"}[status]
        lines.append("[ %s] %s%s" % (status, name, tail))
    n_pass = sum(1 for s, _ in results if s == "PASS")
    n_skip = sum(1 for s, _ in results if s == "SKIP")
    if summary is True:
        lines.append("ALL TESTS PASSED (%d passed, %d skipped)"
                     % (n_pass, n_skip))
    elif summary:
        lines.append(summary)
    return "\n".join(lines) + "\n"


class TestTheRegisteredScripts:

    def test_both_spellings_of_a_do_are_read(self):
        assert V.registered_scripts(_RUNNER) == ["test_a.cscript",
                                                "test_b.cscript"]

    def test_the_real_runner_registers_every_script_in_test(self):
        with open(os.path.join(_HERE, "run_all_cscripts.do"),
                  encoding="utf-8") as fh:
            names = V.registered_scripts(fh.read())
        on_disk = sorted(f for f in os.listdir(_HERE)
                         if f.endswith(".cscript"))
        assert sorted(names) == on_disk
        assert len(names) == len(set(names))


class TestTheVerdict:

    def test_every_script_passed(self):
        ok, lines = V.verdict(_log([("PASS", "test_a.cscript"),
                                    ("PASS", "test_b.cscript")]), _RUNNER)
        assert ok, lines
        assert lines[-1] == "verdict: PASS"
        assert "2 of 2 registered scripts passed" in lines[0]

    @pytest.mark.parametrize("status", ["FAIL", "SKIP"])
    def test_a_failure_or_a_skip_fails_it(self, status):
        text = _log([("PASS", "test_a.cscript"), (status, "test_b.cscript")],
                    summary="SOME TESTS FAILED")
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        word = {"FAIL": "failed", "SKIP": "skipped"}[status]
        assert "  %s: test_b.cscript" % word in lines

    def test_a_skip_fails_it_even_when_the_runner_says_all_passed(self):
        text = _log([("PASS", "test_a.cscript"), ("SKIP", "test_b.cscript")])
        assert "ALL TESTS PASSED (1 passed, 1 skipped)" in text
        ok, _lines = V.verdict(text, _RUNNER)
        assert not ok

    def test_a_script_that_never_reported_fails_it(self):
        text = _log([("PASS", "test_a.cscript")], summary=False)
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        assert "  never reported: test_b.cscript" in lines

    def test_a_script_the_runner_does_not_register_fails_it(self):
        text = _log([("PASS", "test_a.cscript"), ("PASS", "test_b.cscript"),
                     ("PASS", "test_c.cscript")])
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        assert "  reported but not registered: test_c.cscript" in lines

    def test_a_script_reported_twice_fails_it(self):
        text = _log([("PASS", "test_a.cscript"), ("PASS", "test_a.cscript"),
                     ("PASS", "test_b.cscript")])
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        assert "  reported twice: test_a.cscript" in lines

    def test_a_summary_that_disagrees_fails_it(self):
        text = _log([("PASS", "test_a.cscript"), ("PASS", "test_b.cscript")],
                    summary="ALL TESTS PASSED (1 passed, 0 skipped)")
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        assert any("summary does not say all 2 passed" in l for l in lines)

    def test_a_runner_that_registers_nothing_fails_it(self):
        ok, lines = V.verdict(_log([]), "* nothing here\n")
        assert not ok
        assert "  the runner registers no script" in lines

    def test_an_echoed_command_is_not_a_result(self):
        text = ('. display as text "[ PASS] test_b.cscript"\n'
                + _log([("PASS", "test_a.cscript")], summary=False))
        ok, lines = V.verdict(text, _RUNNER)
        assert not ok
        assert "  never reported: test_b.cscript" in lines


class TestTheCommandLine:

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(_ROOT, "scripts", "cert_verdict.py"),
             *args], capture_output=True, text=True, timeout=60)

    def test_it_exits_0_on_a_pass_and_1_on_a_failure(self, tmp_path):
        runner = tmp_path / "run.do"
        runner.write_text(_RUNNER)
        good = tmp_path / "good.log"
        good.write_text(_log([("PASS", "test_a.cscript"),
                              ("PASS", "test_b.cscript")]))
        bad = tmp_path / "bad.log"
        bad.write_text(_log([("PASS", "test_a.cscript"),
                             ("FAIL", "test_b.cscript")],
                            summary="SOME TESTS FAILED"))
        r = self._run(str(good), str(runner))
        assert r.returncode == 0 and "verdict: PASS" in r.stdout, r.stdout
        r = self._run(str(bad), str(runner))
        assert r.returncode == 1 and "verdict: FAIL" in r.stdout, r.stdout

    def test_a_missing_log_fails_it(self, tmp_path):
        runner = tmp_path / "run.do"
        runner.write_text(_RUNNER)
        r = self._run(str(tmp_path / "absent.log"), str(runner))
        assert r.returncode == 1
        assert "no log to judge" in r.stdout

    def test_the_wrong_number_of_arguments_is_a_usage_error(self):
        assert self._run().returncode == 2


def _read(*parts):
    with open(os.path.join(_ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _recipe(makefile, target):
    """The recipe lines of *target* in *makefile*."""
    m = re.search(r"^%s:[^\n]*\n((?:\t[^\n]*\n?)*)" % re.escape(target),
                  makefile, re.M)
    assert m, "the Makefile has no %s target" % target
    return m.group(1)


class TestMakeCheckIsWired:

    def test_check_runs_both_pytest_targets_then_the_certification_suite(self):
        mk = _read("Makefile")
        m = re.search(r"^check:([^\n]*)$", mk, re.M)
        assert m and m.group(1).split() == ["test", "test-dev", "cert"]

    def test_test_is_strict_under_statas_python(self):
        recipe = _recipe(_read("Makefile"), "test")
        assert "scripts/stata_python_exec.sh" in recipe
        assert "DASH_STRICT=1 DASH_BASELINE=stata" in recipe
        assert "-m pytest test/" in recipe

    def test_test_dev_is_strict_under_the_development_interpreter(self):
        recipe = _recipe(_read("Makefile"), "test-dev")
        assert "DASH_STRICT=1 DASH_BASELINE=dev" in recipe
        assert "-m pytest test/" in recipe

    def test_cert_runs_the_suite_and_its_verdict(self):
        assert "scripts/run_cert_suite.sh" in _recipe(_read("Makefile"),
                                                      "cert")
        script = _read("scripts", "run_cert_suite.sh")
        assert "scripts/cert_verdict.py" in script
        assert "test/run_all_cscripts.do" in script

    @pytest.mark.parametrize("name", ["run_cert_suite.sh",
                                      "stata_python_exec.sh",
                                      "stata_slot.sh",
                                      "run_release_gate.sh"])
    def test_stata_runs_only_through_the_console_binary(self, name):
        # WP-30 P1.34: every runner starts Stata through the one wrapper,
        # which names the console binary (STATA_BIN) and picks the slice.
        script = _read("scripts", name)
        assert 'sh "$REPO/scripts/stata_batch.sh" -b do' in script, name
        assert 'REPO="$(cd "$(dirname "$0")/.." && pwd)"' in script, name
        assert 'STATATMP="$dir/tmp/"' in script
        assert '"$STATA"' not in script
        assert "StataMP.app" not in script and "open -a" not in script
        assert "STATA_BIN:-/usr/local/bin/stata-mp" in _read(
            "scripts", "stata_batch.sh")

    def test_the_hook_runs_make_check_and_is_executable(self):
        path = os.path.join(_ROOT, "scripts", "git-hooks", "pre-push")
        assert "exec make check" in _read("scripts", "git-hooks", "pre-push")
        assert os.stat(path).st_mode & stat.S_IXUSR
        assert "core.hooksPath scripts/git-hooks" in _recipe(
            _read("Makefile"), "hooks")
