"""Regression tests for the serve launcher (GAPS2 F1).

``dash serve`` used to report success (rc 0) when no server had actually
started.  The old inline ``--launch`` block in ``dash_render.py`` started
the generated app with ``Popen(cmd).wait()`` and never read
``returncode``: a port already held by another program failed only on the
CHILD's own process stderr (``OSError: [Errno 48] Address already in
use``), which never reached Stata, and ``dash serve`` returned 0 after
about 1.7 seconds.

``_dash_launch_app`` (TR-09.2) is the fix: it pre-binds the port, runs the
app with piped stdout/stderr, forwards the app's own stdout under a bound,
polls ``/health`` and prints the address once it answers, reads the exit
status, and raises ``RuntimeError`` naming the port and the reason on any
failure -- with the last stderr lines, bounded.  The ``__main__`` block
(TR-09.3) carries that text back through a dict the caller may hand
through ``runpy.run_path``'s ``init_globals`` (``dash.ado``'s
``_dash_serve``, TR-09.4); without one, it prints to stderr and exits 1.
"""
import argparse
import http.server
import io
import json
import os
import socket
import subprocess
import sys
import threading
import time
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0],
                    "weight": [2930.0, 3350.0, 2200.0]})
_SPEC = {
    "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                "plots": [{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}],
                "options": {}}],
    "kpis": [],
    "build_options": {"layout": "auto", "registry": "g1", "level": "95",
                      "formats": {}},
}


class _RecStdin:
    """A fake child's stdin (a copy of test_private_files._RecStdin): it
    records the bytes the launcher hands over, since WP-29 P0.12b (R-9)
    starts the app from the bytes it verified, written as one frame to the
    child's stdin.  No ``buffer``, so ``_dash_child_stdin`` returns it as
    it is."""

    def __init__(self):
        self.writes = []
        self.closed = False

    def write(self, b):
        self.writes.append(bytes(b))
        return len(b)

    def flush(self):
        pass

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _an_app_to_read(tmp_path, monkeypatch):
    """The launcher reads the app it starts through a verified descriptor
    (WP-29 P0.12b, R-9), so the ``"app.py"`` these fakes are launched with
    must exist: a stand-in in the test's own folder, made the working
    folder."""
    (tmp_path / "app.py").write_text("# a stand-in app\n")
    monkeypatch.chdir(tmp_path)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _HeldSocket:
    """A listening socket held on 127.0.0.1 -- the address the app binds
    (``dash_render.py``'s ``_dash_server_app`` default, F1.4).  A holder
    on 0.0.0.0 would leave 127.0.0.1 free beside it on macOS and pass for
    the wrong reason (F1.5), so the holder here is on the loopback address
    and listening, as the measured case is."""

    def __enter__(self):
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._s.bind(("127.0.0.1", 0))
        self._s.listen(1)
        self.port = self._s.getsockname()[1]
        return self

    def __exit__(self, *exc):
        self._s.close()


def _write_inputs(tmp_path, spec=None):
    spec = _SPEC if spec is None else spec
    sp = tmp_path / "spec.json"
    dp = tmp_path / "data.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return str(sp), str(dp)


def _build_app(tmp_path, name="app.py"):
    sp, dp = _write_inputs(tmp_path)
    out = str(tmp_path / name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(out)
    return out


def _fake_popen_class(returncode=0, stdout="", stderr=""):
    """Stands in for ``subprocess.Popen``: a class (not an instance), as
    ``monkeypatch.setattr(subprocess, "Popen", ...)`` needs -- constructing
    it records the command and returns a controllable fake child with
    piped text streams (TR-09.10)."""

    class _FakeProc:
        cmd = None
        kw = None
        waited = False
        terminated = False

        def __init__(self, cmd, **kw):
            _FakeProc.cmd = list(cmd)
            _FakeProc.kw = kw
            self.returncode = returncode
            self.stdin = _RecStdin()
            self.stdout = io.StringIO(stdout)
            self.stderr = io.StringIO(stderr)

        def poll(self):
            return self.returncode

        def wait(self):
            _FakeProc.waited = True
            return self.returncode

        def terminate(self):
            _FakeProc.terminated = True

        def communicate(self):
            return ("", "")

    return _FakeProc


class TestTheLauncherRefusesAHeldPort:
    def test_a_socket_on_loopback_makes_the_launcher_raise(
            self, monkeypatch):
        FakeProc = _fake_popen_class()
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        with _HeldSocket() as held:
            with pytest.raises(RuntimeError) as ei:
                dr._dash_launch_app("app.py", held.port, 0, True)
        assert str(ei.value) == (
            "no server started on port %d: the port is in use" % held.port)
        assert FakeProc.cmd is None, (
            "a child was started against a held port")

    @pytest.mark.serve
    def test_the_childs_bind_failure_is_reported_with_its_stderr(
            self, tmp_path):
        app = _build_app(tmp_path)
        with _HeldSocket() as held:
            t0 = time.time()
            with pytest.raises(RuntimeError) as ei:
                dr._dash_launch_app(app, held.port, 0, True, prebind=False)
            elapsed = time.time() - t0
        msg = str(ei.value)
        assert ("no server started on port %d" % held.port) in msg, msg
        assert "the port is in use" in msg, msg
        assert "Address already in use" in msg, msg
        assert elapsed < 30, elapsed


class TestTheLauncherReportsTheExitStatus:
    def test_a_non_zero_exit_names_the_status_and_carries_stderr(
            self, monkeypatch):
        FakeProc = _fake_popen_class(returncode=3, stderr="boom")
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        port = _free_port()
        with pytest.raises(RuntimeError) as ei:
            dr._dash_launch_app("app.py", port, 0, True, prebind=False)
        msg = str(ei.value)
        assert msg.startswith(
            "no server started on port %d: the app exited with status 3"
            % port), msg
        assert "boom" in msg, msg

    def test_the_stderr_tail_is_the_last_twenty_lines_and_under_4_kb(
            self, monkeypatch):
        lines = ["line %d: %s" % (i, "x" * 280) for i in range(1, 61)]
        lines[9] = lines[9][:-2] + "\x1b\x07"  # a control char in the mix
        stderr_text = "\n".join(lines) + "\n"
        FakeProc = _fake_popen_class(returncode=2, stderr=stderr_text)
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        port = _free_port()
        with pytest.raises(RuntimeError) as ei:
            dr._dash_launch_app("app.py", port, 0, True, prebind=False)
        msg = str(ei.value)
        assert "line 60:" in msg, msg
        assert "line 40:" not in msg, msg
        assert "\x1b" not in msg and "\x07" not in msg
        assert len(msg) <= 4096, len(msg)


class TestTheLauncherForwardsBoundedStdout:
    def test_lines_are_filtered_cut_and_capped(self, monkeypatch, capsys):
        first = ("A" * 700) + "\x1b"
        rest = ["line %d" % i for i in range(2, 301)]
        stdout_text = "\n".join([first] + rest) + "\n"
        FakeProc = _fake_popen_class(returncode=0, stdout=stdout_text)
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        port = _free_port()
        dr._dash_launch_app("app.py", port, 0, True, prebind=False)
        out = capsys.readouterr().out
        lines = out.splitlines()
        forwarded_a = [ln for ln in lines if ln.startswith("A")]
        assert len(forwarded_a) == 1, lines
        assert len(forwarded_a[0]) == 500, len(forwarded_a[0])
        assert "\x1b" not in forwarded_a[0]
        forwarded_rest = [ln for ln in lines if ln.startswith("line ")]
        assert len(forwarded_rest) == 199, len(forwarded_rest)
        assert lines.count("dash: (further app output not shown)") == 1
        assert lines[-1] == "dash: (further app output not shown)", lines[-5:]


class TestTheLauncherPrintsTheUrlOnceHealthAnswers:
    def test_the_ready_line_follows_the_first_health_answer(
            self, monkeypatch, capsys):
        port = _free_port()
        hit = threading.Event()

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    hit.set()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *a):
                pass

        httpd = http.server.HTTPServer(("127.0.0.1", port), _Handler)
        server_thread = threading.Thread(target=httpd.serve_forever,
                                         daemon=True)
        server_thread.start()

        class _FakeProc:
            def __init__(self, cmd, **kw):
                _FakeProc.cmd = list(cmd)
                self.stdin = _RecStdin()
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = None
                self._deadline = None

            def poll(self):
                if self.returncode is None and hit.is_set():
                    if self._deadline is None:
                        self._deadline = time.monotonic() + 0.3
                    elif time.monotonic() >= self._deadline:
                        self.returncode = 0
                return self.returncode

            def wait(self):
                while self.returncode is None:
                    self.poll()
                    time.sleep(0.05)
                return self.returncode

            def terminate(self):
                self.returncode = 0

            def communicate(self):
                return ("", "")

        try:
            monkeypatch.setattr(subprocess, "Popen", _FakeProc)
            dr._dash_launch_app("app.py", port, 0, True, prebind=False,
                                ready_seconds=10)
        finally:
            httpd.shutdown()
        out = capsys.readouterr().out
        needle = "dash: the server answers at http://localhost:%d/" % port
        ready_lines = [ln for ln in out.splitlines() if needle in ln]
        assert len(ready_lines) == 1, out

    def test_no_answer_no_ready_line(self, monkeypatch, capsys):
        class _FakeProc:
            def __init__(self, cmd, **kw):
                _FakeProc.cmd = list(cmd)
                self.stdin = _RecStdin()
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = None
                self._deadline = time.monotonic() + 0.5

            def poll(self):
                if self.returncode is None and \
                        time.monotonic() >= self._deadline:
                    self.returncode = 0
                return self.returncode

            def wait(self):
                while self.returncode is None:
                    self.poll()
                    time.sleep(0.05)
                return self.returncode

            def terminate(self):
                self.returncode = 0

            def communicate(self):
                return ("", "")

        port = _free_port()
        monkeypatch.setattr(subprocess, "Popen", _FakeProc)
        dr._dash_launch_app("app.py", port, 0, True, prebind=False,
                            ready_seconds=10)
        out = capsys.readouterr().out
        assert "dash: the server answers at" not in out, out


class TestTheLaunchReportBox:
    def test_a_failure_lands_in_the_report_dict(self, tmp_path, monkeypatch):
        import runpy
        FakeProc = _fake_popen_class(returncode=3, stderr="boom")
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        sp, dp = _write_inputs(tmp_path)
        out = str(tmp_path / "app_box1.py")
        port = _free_port()
        box = {}
        argv = ["dash_render.py", "--spec", sp, "--data", dp,
                "--output", out, "--mode", "server", "--launch",
                "--port", str(port), "--no-browser"]
        monkeypatch.setattr(sys, "argv", argv)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            runpy.run_path(os.path.join(_ROOT, "dash_render.py"),
                           init_globals={"_dash_launch_report": box},
                           run_name="__main__")
        assert box.get("error", "").startswith(
            "no server started on port %d: the app exited with status 3"
            % port), box

    def test_without_a_box_the_cli_exits_1_with_the_message(
            self, tmp_path, monkeypatch, capsys):
        import runpy
        FakeProc = _fake_popen_class(returncode=3, stderr="boom")
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        sp, dp = _write_inputs(tmp_path)
        out = str(tmp_path / "app_box2.py")
        port = _free_port()
        argv = ["dash_render.py", "--spec", sp, "--data", dp,
                "--output", out, "--mode", "server", "--launch",
                "--port", str(port), "--no-browser"]
        monkeypatch.setattr(sys, "argv", argv)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(SystemExit) as ei:
                runpy.run_path(os.path.join(_ROOT, "dash_render.py"),
                               run_name="__main__")
        assert ei.value.code == 1
        err = capsys.readouterr().err
        assert "exited with status 3" in err, err


class TestPortRefusals:
    @pytest.mark.parametrize("given", [80, 70000])
    def test_the_renderer_cli_refuses(self, tmp_path, monkeypatch, given):
        import runpy
        FakeProc = _fake_popen_class()
        monkeypatch.setattr(subprocess, "Popen", FakeProc)
        sp, dp = _write_inputs(tmp_path)
        out = str(tmp_path / ("app_%d.py" % given))
        argv = ["dash_render.py", "--spec", sp, "--data", dp,
                "--output", out, "--mode", "server", "--launch",
                "--port", str(given), "--no-browser"]
        monkeypatch.setattr(sys, "argv", argv)
        with pytest.raises(SystemExit) as ei:
            runpy.run_path(os.path.join(_ROOT, "dash_render.py"),
                           run_name="__main__")
        assert ei.value.code == 2
        assert not os.path.exists(out)
        assert FakeProc.cmd is None

    def test_port_value_accepts_the_range_and_refuses_the_rest(self):
        for ok, want in (("1024", 1024), (65535, 65535), (" 5006 ", 5006)):
            assert dr._dash_port_value(ok) == want
        for bad in ("80", "70000", "٥٠٠٦",
                    "5_006", "", "5006x"):
            with pytest.raises(argparse.ArgumentTypeError):
                dr._dash_port_value(bad)
