"""test_server_build_returns.py — building a server app must not start one.

``dash build, saving(app.py) server`` is documented to write a file and
return. It did neither: ``_dash_do_render`` sets ``sys.argv`` with no
``--no-browser`` and no ``--timeout``, then runs ``dash_render.py`` as
``__main__``, whose server branch **launches the app and waits on it**. So the
command opened a browser window and blocked the Stata session forever — the
two ``display`` lines that follow it in ``dash.ado`` never printed.

The renderer's job on this path is to write a file. Starting a server is a
side effect no caller asked for, so launching is opt-in (``--launch``) rather
than opt-out. ``dash serve``, whose job *is* to run one, passes it.

These tests never open a browser: the launching path is exercised only with
``--no-browser``, and the non-launching path opens nothing by construction.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.join(_HERE, "..")
sys.path.insert(0, _REPO)
sys.path.insert(0, _HERE)

from conftest import make_spec, make_data_json

_RENDER = os.path.join(_REPO, "dash_render.py")


@pytest.fixture
def spec_and_data(tmp_path):
    df = pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 12),
        "weight": np.linspace(1760.0, 4840.0, 12),
    })
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    sp = tmp_path / "spec.json"
    dp = tmp_path / "data.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df)))
    return str(sp), str(dp), str(tmp_path / "app.py")


def _run(argv, timeout=45):
    return subprocess.run([sys.executable, _RENDER] + argv,
                          capture_output=True, text=True, timeout=timeout)


class TestBuildingDoesNotLaunch:

    def test_it_returns(self, spec_and_data):
        sp, dp, op = spec_and_data
        try:
            proc = _run(["--spec", sp, "--data", dp, "--output", op,
                         "--mode", "server"])
        except subprocess.TimeoutExpired:
            pytest.fail(
                "building a server app never returned: the renderer launched "
                "the app and waited on it, which is what blocks the Stata "
                "session forever"
            )
        assert proc.returncode == 0, proc.stderr[-2000:]

    def test_it_writes_the_file(self, spec_and_data):
        sp, dp, op = spec_and_data
        _run(["--spec", sp, "--data", dp, "--output", op, "--mode", "server"])
        assert os.path.exists(op)
        assert os.path.getsize(op) > 1000

    def test_the_file_it_writes_is_valid_python(self, spec_and_data):
        import ast
        sp, dp, op = spec_and_data
        _run(["--spec", sp, "--data", dp, "--output", op, "--mode", "server"])
        with open(op, encoding="utf-8") as fh:
            ast.parse(fh.read())

    def test_no_process_is_left_running(self, spec_and_data):
        """A build that leaves a server behind is a build that launched one.

        Matched on THIS build's app path, not on a port: a port check reads
        global machine state and would fail because of anything else
        listening, which is a flaky test rather than a strict one.
        """
        sp, dp, op = spec_and_data
        _run(["--spec", sp, "--data", dp, "--output", op, "--mode", "server"])
        found = subprocess.run(["pgrep", "-f", op], capture_output=True,
                               text=True)
        assert not found.stdout.strip(), (
            f"building left a process running for {op}: "
            f"pids {found.stdout.split()}"
        )


class TestLaunchingIsOptIn:

    def test_the_flag_exists(self):
        proc = _run(["--help"])
        assert "--launch" in proc.stdout, proc.stdout[-1500:]

    def test_standalone_mode_is_unaffected(self, tmp_path):
        df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 8),
                           "weight": np.linspace(1760.0, 4840.0, 8)})
        spec = make_spec([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}])
        sp = tmp_path / "s.json"
        dp = tmp_path / "d.json"
        op = tmp_path / "out.html"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(df)))
        proc = _run(["--spec", str(sp), "--data", str(dp),
                     "--output", str(op), "--mode", "standalone"])
        assert proc.returncode == 0, proc.stderr[-1500:]
        assert op.exists()


class TestTheStataSideAsksForWhatItWants:
    """dash.ado must not rely on the renderer's default to decide this."""

    def test_the_build_path_does_not_ask_to_launch(self):
        with open(os.path.join(_REPO, "dash.ado"), encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("program define _dash_do_render")
        body = src[i:src.index("\nend", i)]
        assert "--launch" not in body, (
            "_dash_do_render is the BUILD path; it must not start a server"
        )

    def test_the_serve_path_asks_to_launch(self):
        with open(os.path.join(_REPO, "dash.ado"), encoding="utf-8") as fh:
            src = fh.read()
        assert '"--launch"' in src, (
            "dash serve must ask for a server explicitly now that launching "
            "is opt-in, or it will only ever write a file"
        )
