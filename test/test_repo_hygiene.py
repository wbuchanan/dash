"""Repository hygiene (WP-31 I6, S60 D-60g/D-60h): logs are ignored by the
tracked .gitignore, a CI workflow runs make test-dev and make lint, and
make lint exists and is clean."""
import os
import re
import shutil
import subprocess
import sys

import pytest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(*parts):
    with open(os.path.join(_REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


def test_gitignore_excludes_logs():
    lines = [l.strip() for l in _read(".gitignore").splitlines()]
    assert "*.log" in lines


def test_the_workflow_runs_test_dev_and_lint():
    wf = _read(".github", "workflows", "test.yml")
    on = wf.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert re.search(r"^  push:\n    branches: \[s3-bugs, main\]$", on, re.M)
    assert re.search(r"^  pull_request:$", on, re.M)
    assert re.search(r"^  workflow_dispatch:$", on, re.M)
    assert "runs-on: ubuntu-latest" in wf
    assert 'python-version: "3.11"' in wf
    assert re.search(r"run: make test-dev PYTHON=python\b", wf)
    assert re.search(r"run: make lint PYTHON=python\b", wf)
    assert "macOS" in wf and "stata-mp" not in wf
    assert "secrets." not in wf


def test_the_workflow_fits_the_runner():
    """The first run (14nov2026) started pyproject's eight workers on a
    2-CPU, 8 GB runner: it ran out of memory 17 minutes in, at 21%, on
    pace for more than its hour.  Two workers a job, the suite in four
    jobs (DASH_SHARD), each job inside its time limit."""
    wf = _read(".github", "workflows", "test.yml")
    assert re.search(r'run: make test-dev PYTHON=python DEV_STRICT=0 '
                     r'DEV_BASELINE=py311 PYTEST_ARGS="-n 2"$', wf, re.M)
    assert re.search(r"^        shard: \[1, 2, 3, 4\]$", wf, re.M)
    assert re.search(r"^      DASH_SHARD: \$\{\{ matrix\.shard \}\}/4$", wf,
                     re.M)
    assert "fail-fast: false" in wf
    assert re.search(r"^    timeout-minutes: 40$", wf, re.M)
    assert re.search(r"^  cancel-in-progress: true$", wf, re.M)
    # Node.js 20 actions are retired (GitHub's warning on the first run).
    assert "actions/checkout@v5" in wf and "actions/setup-python@v6" in wf
    assert "@v4" not in wf and "setup-python@v5" not in wf


def _ruff():
    if os.environ.get("RUFF"):
        return os.environ["RUFF"].split()
    p = subprocess.run([sys.executable, "-m", "ruff", "--version"],
                       capture_output=True)
    if p.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    exe = shutil.which("ruff")
    return [exe] if exe else None


def test_make_lint_target_exists():
    mk = _read("Makefile")
    m = re.search(r"^lint:\n((?:\t.*\n)+)", mk, re.M)
    assert m, "the Makefile has no lint: target"
    assert "check $(LINT_PATHS) --config ruff.toml" in m.group(1)
    assert "exit 2" in m.group(1)
    assert re.search(r"^LINT_PATHS = dash_render\.py dash_setup_lib\.py "
                     r"test scripts$", mk, re.M)
    assert re.search(r"^\.PHONY:.*\blint\b", mk, re.M)
    toml = _read("ruff.toml")
    assert re.search(r'^select = \["E4", "E7", "E9", "F"\]$', toml, re.M)


def test_ruff_findings_are_zero_or_skip():
    cmd = _ruff()
    if cmd is None:
        pytest.skip("ruff is not installed (make lint says how to install it)")
    p = subprocess.run(cmd + ["check", "dash_render.py", "dash_setup_lib.py",
                              "test", "scripts", "--config", "ruff.toml"],
                       cwd=_REPO, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-1000:]
