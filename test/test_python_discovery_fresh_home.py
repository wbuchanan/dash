"""test_python_discovery_fresh_home.py -- dash and dash_setup with no Python
set, in a fresh HOME (WP-36 plat:PT-1, ruling M8, DECISIONS A-8).

A Stata whose HOME holds no profile has ``c(python_exec)`` empty until
``python set exec`` is typed, and finds a Python itself the first time a
``python:`` line runs.  dash used to refuse that state ("Python is required
but is not available to Stata", r(198)); dash_setup refused it the same way.
This starts console Stata through ``scripts/stata_slot.sh`` (one of its three
slots, waited for like any other run) with HOME set to an empty temporary
folder, so the maintainer's own Stata settings are never read or written,
and checks that dash reaches its work and dash_setup checks the Python Stata
found -- installing nothing (``PIP_NO_INDEX=1`` and an empty
``PIP_FIND_LINKS``; the found Python's ``pip list`` is the same before and
after).

Release tier: it holds a Stata slot for about a minute.
"""
import os
import re
import subprocess

import pytest

pytestmark = pytest.mark.release

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOT = os.path.join(REPO, "scripts", "stata_slot.sh")
STATA_BIN = os.environ.get("STATA_BIN", "/usr/local/bin/stata-mp")

if not (os.path.isfile(STATA_BIN) and os.access(STATA_BIN, os.X_OK)):
    pytest.skip("no console Stata at %s (STATA_BIN)" % STATA_BIN,
                allow_module_level=True)

_EXE_DO = """\
python: import sys; from sfi import Macro; Macro.setLocal("_x", sys.executable); Macro.setLocal("_v", "%d.%d" % sys.version_info[:2])
file open fh using "exe.txt", write text replace
file write fh `"`_x'"' _n `"`_v'"' _n
file close fh
"""

_FRESH_DO = """\
adopath ++ "{repo}"
global dash_nobrowser 1
file open fh using "pyx.txt", write text replace
file write fh `"[`c(python_exec)']"'
file close fh
sysuse auto, clear
capture noisily dash scatter mpg weight, saving("p.html", replace)
display "##RC dash " _rc
capture noisily dash_setup
display "##RC setup " _rc
"""


def _stata(run, dofile, env):
    try:
        return subprocess.run(["sh", SLOT, str(run), dofile], env=env,
                              timeout=900, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        pytest.fail("Stata did not finish %s within 900 s; log %s"
                    % (dofile, run / dofile.replace(".do", ".log")))


def _pip_list(exe, env):
    out = subprocess.run([exe, "-m", "pip", "list", "--format=freeze"],
                         env=env, capture_output=True, text=True, timeout=300)
    return out.returncode, out.stdout


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    w = tmp_path_factory.mktemp("fresh")
    for sub in ("home", "wheels", "run"):
        (w / sub).mkdir()
    env = {k: v for k, v in os.environ.items() if k != "DASH_PYTHON_EXEC"}
    env.update(HOME=str(w / "home"), PIP_NO_INDEX="1",
               PIP_FIND_LINKS=str(w / "wheels"),
               PIP_DISABLE_PIP_VERSION_CHECK="1")
    run = w / "run"
    # (i) the Python Stata finds by itself.
    (run / "exe.do").write_text(_EXE_DO, encoding="utf-8")
    _stata(run, "exe.do", env)
    exe_txt = run / "exe.txt"
    assert exe_txt.is_file(), (
        "Q3601-0: exe.do wrote nothing; log:\n"
        + (run / "exe.log").read_text(errors="replace")[-3000:])
    exe, ver = (exe_txt.read_text(encoding="utf-8").splitlines() + ["", ""])[:2]
    assert os.path.isabs(exe) and os.access(exe, os.X_OK), (
        "Q3601-0: the Python Stata found is not an executable path: %r" % exe)
    # Never run a Python below dash's floor (the maintainer, 21oct2026).
    assert re.fullmatch(r"\d+\.\d+", ver) and \
        tuple(int(x) for x in ver.split(".")) >= (3, 11), (
            "Q3601-0: Stata found Python %r at %s, below 3.11" % (ver, exe))
    before = _pip_list(exe, env)
    # (ii) dash and dash_setup with nothing set.
    if any(c in REPO for c in '"`$'):
        pytest.fail("Q3601-0: the repository path holds a quote, a backtick "
                    "or a dollar sign: %s" % REPO)
    (run / "fresh.do").write_text(_FRESH_DO.format(repo=REPO), encoding="utf-8")
    _stata(run, "fresh.do", env)
    # Stata wraps a long line at the column, going on with "> ".
    log = (run / "fresh.log").read_text(encoding="utf-8", errors="replace")
    log = log.replace("\n> ", "")
    # (iii) the same pip list.
    after = _pip_list(exe, env)
    return {"w": w, "run": run, "exe": exe, "log": log,
            "pyx": (run / "pyx.txt").read_text(encoding="utf-8").strip()
            if (run / "pyx.txt").is_file() else None,
            "before": before, "after": after}


class TestAFreshHome:

    def test_no_python_is_set(self, fresh):
        assert fresh["pyx"] == "[]", ("Q3601-1: c(python_exec) was %r in a "
                                      "fresh HOME" % fresh["pyx"])

    def test_nothing_says_python_is_unavailable(self, fresh):
        for said in ("Python is required but is not available",
                     "Python is not available to Stata"):
            assert said not in fresh["log"], ("Q3601-2: " + said + "\n"
                                              + fresh["log"][-3000:])

    def test_dash_reaches_its_work(self, fresh):
        log = fresh["log"]
        if "##RC dash 0" in log:
            assert (fresh["run"] / "p.html").is_file(), "Q3601-3: rc 0, no page"
            return
        want = ("not installed for the Python Stata uses (the Python Stata "
                "found, " + fresh["exe"])
        assert "##RC dash 198" in log and want in log, (
            "Q3601-3: dash neither wrote the page nor named the found "
            "Python's missing packages\n" + log[-3000:])

    def test_dash_setup_checks_the_found_python(self, fresh):
        log = fresh["log"]
        assert re.search(r"^\s*Python \.+ OK\b", log, re.M), (
            "Q3601-4: no Python OK line\n" + log[-3000:])
        assert "Unmet: Python" not in log and \
            "Python (not linked to Stata)" not in log, (
                "Q3601-4: dash_setup counted Python unmet\n" + log[-3000:])
        assert "##RC setup" in log, "Q3601-4: dash_setup did not return"

    def test_nothing_is_installed(self, fresh):
        assert fresh["before"][0] == 0, ("Q3601-5: pip list failed before", fresh["before"])
        assert fresh["after"] == fresh["before"], (
            "Q3601-5: the found Python's packages changed", fresh["before"],
            fresh["after"])
        found = [r for r, d, _ in os.walk(fresh["w"] / "home")
                 if "site-packages" in d]
        assert not found, ("Q3601-5: a site-packages folder was made under "
                           "the fresh HOME", found)
