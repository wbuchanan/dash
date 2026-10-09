"""WP-30 P1.33: the floor matrix that measures dash's Python floor.

dash_setup declared Python 3.13 as its minimum because 3.13 was the
interpreter Stata was linked to, not because anything needed it.  The floor
is now measured: both pytest suites run under each candidate Python with the
Stata pins (``test/requirements-stata.txt``), the development pins
(``test/requirements-dev.txt``) and a fresh resolve as ``dash_setup``
installs, and a Stata session linked to that Python for one run builds a
saved page and serves the app.

* ``scripts/floor_matrix.sh make`` prepares one scratch venv from wheels only;
  ``run`` runs the suite in it strictly against a named baseline.
* ``make test-floor`` runs one leg by hand; ``make gate`` never does
  (ratification item 25, "Manual only").
* ``scripts/floor_stata_leg.do`` links a Stata session to the venv for that
  session only; ``test/run_all_cscripts.do`` links a certification run to
  ``DASH_PYTHON_EXEC`` the same way.

Every process runs from an argument list, never a shell string.
"""
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conftest as C  # noqa: E402
import test_label_sinks  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "floor_matrix.sh")
STATA_LEG = os.path.join(ROOT, "scripts", "floor_stata_leg.do")
RUNNER = os.path.join(ROOT, "test", "run_all_cscripts.do")

#: The pins files and the baseline whose pins each carries.
PINS = {"requirements-stata.txt": "stata", "requirements-dev.txt": "dev"}
_LINE = re.compile(r"^[A-Za-z0-9_.-]+==[0-9][0-9A-Za-z.]*$")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _pins(name):
    out = {}
    for ln in _read(os.path.join(ROOT, "test", name)).splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            pkg, ver = ln.split("==")
            out[pkg.lower()] = ver
    return out


def _sh(args, env=None, cwd=None):
    """Run the script under sh from an argument list."""
    full = dict(os.environ)
    full.pop("FLOOR_DRY_RUN", None)
    full.update(env or {})
    return subprocess.run(["sh", SCRIPT] + list(args), env=full, cwd=cwd,
                          capture_output=True, text=True, timeout=120)


class TestTheRequirementsFiles:

    def test_each_file_pins_its_baseline_exactly(self):
        for name, base in PINS.items():
            pins = _pins(name)
            want = C._BASELINES[base]
            for pkg in ("bokeh", "numpy", "pandas", "scipy"):
                assert C._mm(pins[pkg]) == want[pkg], (name, pkg, pins[pkg])
            # Flipped (WP-30 P1.30): verified means major.minor (A104).
            assert C._mm(pins["bokeh"]) in test_label_sinks.VERIFIED_BOKEH, name
            for tool in ("pytest", "pytest-xdist", "packaging"):
                assert tool in pins, (name, tool)
            header = _read(os.path.join(ROOT, "test", name)).splitlines()[0]
            assert header.startswith("#"), name

    def test_no_line_can_redirect_an_install(self):
        for name in PINS:
            for ln in _read(os.path.join(ROOT, "test", name)).splitlines():
                s = ln.strip()
                if s and not s.startswith("#"):
                    assert _LINE.match(s), (name, ln)


class TestTheScript:

    def test_usage_and_refusals(self, tmp_path):
        r = _sh([])
        assert r.returncode == 2 and "usage:" in r.stderr, r.stderr
        cases = [
            (["make", "python3", str(tmp_path / "v"), "stata"],
             "absolute path"),
            (["make", str(tmp_path / "nosuch-python"), str(tmp_path / "v"),
              "stata"], "no executable"),
            (["make", sys.executable, str(tmp_path / "v"), "nosuch"],
             "stata, dev or fresh"),
            (["make", sys.executable, "v", "stata"], "absolute path"),
            (["run", str(tmp_path), "py3x; rm"], "baseline"),
            (["run", str(tmp_path), "py311"], "bin/python"),
        ]
        for args, needle in cases:
            r = _sh(args, env={"FLOOR_DRY_RUN": "1", "DASH_NODE": "node"})
            assert r.returncode == 2, (args, r.stdout, r.stderr)
            assert needle in r.stderr, (args, r.stderr)
        assert not (tmp_path / "v").exists()

    def test_a_dry_run_prints_the_exact_commands(self, tmp_path):
        exe = sys.executable
        venv = tmp_path / "m"
        r = _sh(["make", exe, str(venv), "stata"], env={"FLOOR_DRY_RUN": "1"})
        assert r.returncode == 0, r.stderr
        py = "%s/gatevenv/bin/python" % venv
        assert "FLOOR would run: %s -m venv %s/gatevenv" % (exe, venv) in r.stdout
        assert ("FLOOR would run: %s -m pip install --require-virtualenv "
                "--only-binary=:all: -r %s/test/requirements-stata.txt"
                % (py, ROOT)) in r.stdout
        assert not venv.exists()
        r = _sh(["make", exe, str(venv), "fresh"], env={"FLOOR_DRY_RUN": "1"})
        assert r.returncode == 0, r.stderr
        assert "--only-binary=:all: packaging bokeh>=3.8,<3.10" in r.stdout
        assert "-r " not in r.stdout
        run = tmp_path / "r"
        (run / "gatevenv" / "bin").mkdir(parents=True)
        stub = run / "gatevenv" / "bin" / "python"
        stub.write_text("#!/bin/sh\nexit 0\n")
        stub.chmod(0o755)
        r = _sh(["run", str(run), "py311"],
                env={"FLOOR_DRY_RUN": "1", "DASH_NODE": "node"})
        assert r.returncode == 0, r.stderr
        assert "DASH_STRICT=1" in r.stdout
        assert "DASH_BASELINE=py311" in r.stdout
        assert "%s -m pytest test/" % stub in r.stdout

    def test_it_refuses_a_directory_that_is_not_a_venv(self, tmp_path):
        (tmp_path / "gatevenv").mkdir()
        (tmp_path / "gatevenv" / "keep").write_text("x")
        before = sorted(os.listdir(tmp_path / "gatevenv"))
        r = _sh(["make", sys.executable, str(tmp_path), "stata"])
        assert r.returncode == 2
        assert "not a virtual environment" in r.stderr
        assert sorted(os.listdir(tmp_path / "gatevenv")) == before
        assert sorted(os.listdir(tmp_path)) == ["gatevenv"]

    def test_the_header_gives_the_manual_re_measure_procedure(self):
        lines = _read(SCRIPT).splitlines()
        header = []
        for ln in lines[1:]:
            if not ln.startswith("#"):
                break
            header.append(ln)
        text = "\n".join(header)
        for needle in ("make test-floor", "floor_stata_leg.do",
                       "venv-setup2 rc=0 linked=1", "DASH_PYTHON_EXEC",
                       "not part of make gate", "WP-30 P1.33"):
            assert needle in text, needle

    def test_it_names_no_interpreter_and_evaluates_nothing(self):
        text = _read(SCRIPT)
        assert "set -eu" in text
        assert not re.search(r"\beval\b", text)
        for needle in ("python" + "3.1", "/" + "opt/", "/" + "Users/",
                       "ar" + "ch -", "--break-" + "system-packages"):
            assert needle not in text, needle


class TestTheMakeTarget:

    def test_make_test_floor_runs_one_leg(self):
        mk = _read(os.path.join(ROOT, "Makefile"))
        phony = [ln for ln in mk.splitlines() if ln.startswith(".PHONY:")]
        assert phony and "test-floor" in phony[0].split()
        assert re.search(r'@echo "make test-floor .*not part of make gate',
                         mk)
        assert ('sh scripts/floor_matrix.sh run "$(FLOOR_VENV)" '
                '"$(FLOOR_BASELINE)"') in mk
        env = {k: v for k, v in os.environ.items()
               if k not in ("FLOOR_VENV", "FLOOR_BASELINE", "MAKEFLAGS",
                            "MFLAGS")}
        r = subprocess.run(["make", "-s", "test-floor"], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 2, r.stdout + r.stderr
        assert "FLOOR_VENV" in r.stdout + r.stderr


class TestTheStataLeg:

    def test_the_leg_reads_its_paths_and_links_for_one_session(self):
        do = _read(STATA_LEG)
        for needle in (": environment DASH_REPO",
                       ": environment DASH_FLOOR_WORK",
                       "\nglobal dash_nobrowser 1\n", "release_gate_venv.do",
                       "venvuse", "\nversion 19\n",
                       'if `"`macval(repo)\'"\' == ""',
                       "macval(_fl_work)"):
            assert needle in do, needle
        assert "permanently" not in do
        assert not [ln for ln in do.splitlines() if "python:" in ln]
        assert not [ln for ln in do.splitlines()
                    if ln.lstrip().startswith("python ")]


class TestTheCertRunnerLink:

    def test_the_runner_links_only_when_asked(self):
        do = _read(RUNNER)
        end = do.index("// ---- root: end ----")
        assert do.count(": environment DASH_PYTHON_EXEC") == 1
        assert do.index(": environment DASH_PYTHON_EXEC") > end
        assert do.count("python set exec") == 1
        link = do.index("python set exec")
        guard = do.index('if `"`macval(_dash_pyx)\'"\' != "" {')
        assert end < guard < link
        assert "\n}" in do[link:] and do.index("\n}", link) > link
        first_py = do.index("python:", end) if "python:" in do[end:] else len(do)
        first_do = re.search(r'^\s*(capture noisily )?do "', do[end:], re.M)
        assert link < first_py
        assert first_do is None or link < end + first_do.start()
        assert "permanently" not in do
        assert ("DASH_PYTHON_EXEC holds a quote, backquote, dollar sign or "
                "control character") in do
