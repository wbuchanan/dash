"""test_cscript_hygiene.py — the certification suite must actually certify.

Two defects, both of which made the Stata suite report success while testing
far less than it claimed.

**The guard that skipped everything.** Every Python-dependent script decided
whether Python was available with ``capture python: pass``.  Measured: that
returns a nonzero rc inside ``run_all_cscripts.do`` on a machine where the
very same session renders Bokeh output through ``dash build`` seconds later.
Nine of the fourteen scripts -- every end-to-end one -- skipped, and the
runner printed ``ALL TESTS PASSED (5 passed, 9 skipped)``.  The replacement
reads ``c(python_exec)``, which is configuration rather than execution and so
cannot fail for reasons unrelated to Python being configured.

**A line of HTML that ended a Stata string.** ``test_e2e_single.cscript``
read the generated dashboard line by line and tested each with
``strpos(lower("`ln'"), "bokeh")``.  Bokeh's HTML contains ``"`` characters,
which closed the Stata string early; the remainder of the line was then
parsed as code and the script died with ``r(111): Security not found`` --
"Security" being a word from the page.  Under the broken Python guard the
script never ran, so the failure was invisible.

Both checks are mechanical and run in the Python suite, because that is the
suite that runs on every change.
"""
import glob
import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSCRIPTS = sorted(glob.glob(os.path.join(_HERE, "*.cscript")))
_RUNNER = os.path.join(_HERE, "run_all_cscripts.do")


def _name(path):
    return os.path.basename(path)


@pytest.fixture(scope="module", params=_CSCRIPTS, ids=_name)
def cscript(request):
    with open(request.param, encoding="utf-8") as fh:
        return request.param, fh.read()


class TestTheAvailabilityGuardIsReliable:

    def test_no_script_probes_python_by_executing_it(self, cscript):
        path, src = cscript
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        lines = code.splitlines()
        bad = []
        for i, line in enumerate(lines):
            if "capture python: pass" not in line:
                continue
            # A bare warm-up is fine and is in fact required; what is not
            # fine is deciding anything from its rc.
            # A bare warm-up before a real probe is fine and is in fact
            # required; what is not fine is concluding "Python is missing"
            # from its rc.
            after = "\n".join(lines[i + 1:i + 5])
            if "Python not available" in after:
                bad.append(i + 1)
        assert not bad, (
            f"{_name(path)} lines {bad}: decides whether Python is available "
            f"by running it; measured, that reports a nonzero rc under the "
            f"runner on a machine where Python works, and the script "
            f"silently skips"
        )

    def test_a_probe_that_must_run_python_retries(self, cscript):
        """Checking for a package can only be done by importing it.

        The first python call of a session fails under the runner whatever it
        is, so such a probe must spend that failure on a throwaway call and
        ask its real question afterwards -- otherwise a machine with bokeh
        installed reports bokeh missing and the script skips.
        """
        path, src = cscript
        code = [l.split("//", 1)[0] for l in src.splitlines()]
        probes = [i for i, l in enumerate(code)
                  if "capture python:" in l and "import" in l]
        if not probes:
            pytest.skip("this script runs no import probe")
        for i in probes:
            window = "\n".join(code[max(0, i - 3):i + 3])
            assert window.count("capture python:") >= 3, (
                f"{_name(path)} line {i + 1}: an import probe with no "
                f"warm-up and no retry; the first python call of the "
                f"session fails under the runner regardless of the import"
            )

    def test_the_runner_does_not_probe_python_by_executing_it(self):
        with open(_RUNNER, encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        assert "capture python" not in code, _RUNNER

    def test_a_script_that_needs_python_says_so_through_the_setting(self,
                                                                    cscript):
        path, src = cscript
        if "SKIP: Python not available" not in src:
            pytest.skip("this script does not depend on Python")
        assert "c(python_exec)" in src, (
            f"{_name(path)} reports Python as unavailable without consulting "
            f"Stata's Python configuration"
        )


class TestNoFileReadMacroIsExpandedInPlainQuotes:
    """A line of data may contain a quote; a line of code must survive it."""

    # `local ln' read from a file, expanded inside "..." rather than `"..."'
    _UNSAFE = re.compile(r'(?<!`)"`(ln|line|l|html_line|content)\'"')

    def test_no_unsafe_expansion(self, cscript):
        path, src = cscript
        bad = []
        for i, line in enumerate(src.splitlines(), 1):
            code = line.split("//", 1)[0]
            if self._UNSAFE.search(code):
                bad.append(f"{_name(path)}:{i}: {line.strip()}")
        assert not bad, (
            "a macro holding a line read from a file is expanded inside "
            "plain double quotes; a quote character in the data ends the "
            "Stata string and the rest of the line is parsed as code:\n"
            + "\n".join(bad)
        )


class TestEveryCscriptIsWiredIntoTheRunner:
    """A script the runner never calls is a script that never certifies."""

    def test_the_runner_calls_it(self, cscript):
        path, _ = cscript
        with open(_RUNNER, encoding="utf-8") as fh:
            runner = fh.read()
        assert _name(path) in runner, (
            f"{_name(path)} exists but run_all_cscripts.do never runs it"
        )
