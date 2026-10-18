"""Regression tests for WP-29 P0.13: the served app's lifecycle.

Measured at 7421d3d (section 08, Evidence §4):

* a SIGKILL or SIGTERM of Stata left the app answering ``/health`` with
  ppid 1, holding its port, beside three 0644 data-bearing files (t3, t4);
* the launcher never called ``sfi.SFIToolkit.pollstd()``, so Break in GUI
  Stata could not stop ``dash serve`` (p7), and a console Ctrl+C returned
  rc 0 (t5, g1);
* every message told GUI users to press Ctrl+C (F9c).

F2 (this file's first half): the child is started with a pipe on its stdin
and ``--parent-watch``; the app's ``_dash_watch_parent`` stops its loop when
the pipe reaches end of file -- which the OS gives it however its Stata ends
-- with a hard exit after a grace period; and the app file is erased once
``/health`` and the app's own banner have both arrived, so no copy of the
data stays on disk while it serves.

Every real-server test builds its URL through ``_url`` (S13 adds its token
there) and frees its port in a ``finally``.
"""
import ast
import http.server
import io
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import types
import urllib.request
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from serve_token_probe import FakeStdin  # noqa: E402  (WP-29 P0.12a)
from conftest import make_data_json  # noqa: E402
from test_serve_launcher import _DF, _SPEC, _free_port  # noqa: E402

_RENDER = os.path.join(_ROOT, "dash_render.py")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _url(port, path, token=None):
    """Every real-server URL, in one place; with *token*, the dashboard's
    key appended (WP-29 P0.12a)."""
    u = "http://127.0.0.1:%d%s" % (port, path)
    if token:
        u += ("&" if "?" in path else "?") + "token=" + token
    return u


def _token_in(rundir, seconds=10):
    """The key in the run folder's link.html (WP-29 P0.12a), waited for."""
    p = os.path.join(rundir, "link.html")
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        try:
            with open(p, encoding="utf-8") as fh:
                m = re.search(r"\?token=([A-Za-z0-9_-]{32,128})", fh.read())
            if m:
                return m.group(1)
        except OSError:
            pass
        time.sleep(0.1)
    raise AssertionError("no link.html in " + rundir)


def _port_free(port):
    """True when 127.0.0.1:*port* binds (SO_REUSEADDR, so a port whose last
    connections are in TIME_WAIT counts as free; A7)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _health(port, timeout=1.0):
    try:
        with urllib.request.urlopen(_url(port, "/health"),
                                    timeout=timeout) as r:
            return r.status
    except Exception:
        return None


def _wait_health(port, seconds, proc=None):
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        if _health(port, 0.5) == 200:
            return True
        if proc is not None and proc.poll() is not None:
            return False
        time.sleep(0.1)
    return False


def _wait_gone(port, seconds):
    """True once /health stops answering and the port binds again."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        if _health(port, 0.3) is None and _port_free(port):
            return True
        time.sleep(0.1)
    return False


def _kill_listeners(port):
    """Kill whatever listens on *port*; quiet when lsof is absent."""
    try:
        out = subprocess.run(
            ["lsof", "-t", "-iTCP:%d" % port, "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return
    for tok in out.split():
        try:
            os.kill(int(tok), signal.SIGKILL)
        except (ValueError, OSError):
            pass


def _run_inputs(tmp_path):
    """A private run folder, as dash serve opens it, holding the spec and
    data; returns the dict of ``_dash_run_open``."""
    run = dr._dash_run_open(str(tmp_path))
    with open(run["spec"], "w") as fh:
        json.dump(_SPEC, fh)
    with open(run["data"], "w") as fh:
        json.dump(make_data_json(_DF), fh)
    return run


def _built_app(tmp_path, name="app.py"):
    sp = tmp_path / "spec_in.json"
    dp = tmp_path / "data_in.json"
    sp.write_text(json.dumps(_SPEC))
    dp.write_text(json.dumps(make_data_json(_DF)))
    out = str(tmp_path / name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(out)
    return out


def _launcher(run, port, timeout_min=1):
    """A parent process that runs the renderer as dash serve does (runpy on
    dash_render.py, with the box); returns the Popen."""
    argv = ["dash_render.py", "--spec", run["spec"], "--data", run["data"],
            "--output", run["app"], "--mode", "server", "--launch",
            "--port", str(port), "--timeout", str(timeout_min),
            "--no-browser"]
    code = ("import sys, runpy; sys.argv = %r; "
            "runpy.run_path(%r, init_globals={'_dash_launch_report': {}}, "
            "run_name='__main__')" % (argv, _RENDER))
    # WP-29 P0.12a: a launcher killed hard leaves its link folder behind
    # (a recorded residual), so its temp folder is the test's own.
    env = dict(os.environ, TMPDIR=os.path.dirname(run["app"]))
    return subprocess.Popen([sys.executable, "-c", code],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, env=env)


class _FakeLoop:
    def __init__(self):
        self.calls = []

    def add_callback(self, fn, *a):
        self.calls.append(fn)

    def stop(self):
        pass


# ===========================================================================
# F2: the parent watch
# ===========================================================================

class TestTheParentWatch:

    def test_eof_on_stdin_asks_the_loop_to_stop(self):
        watch = getattr(dr, "_dash_watch_parent")
        r, w = os.pipe()
        loop = _FakeLoop()
        exits = []
        t = watch(loop, fd=r, grace=30.0, _exit=exits.append)
        os.write(w, b"x")
        os.close(w)
        t.join(5)
        os.close(r)
        assert not t.is_alive()
        assert loop.calls == [loop.stop]
        assert exits == []

    def test_a_loop_that_does_not_stop_is_exited_after_the_grace(self):
        watch = getattr(dr, "_dash_watch_parent")
        r, w = os.pipe()
        loop = _FakeLoop()
        exited = threading.Event()
        codes = []

        def _exit(code):
            codes.append(code)
            exited.set()
        watch(loop, fd=r, grace=0.2, _exit=_exit)
        os.close(w)
        assert exited.wait(5)
        os.close(r)
        assert codes == [0]

    def test_bytes_on_stdin_are_discarded_and_do_not_stop_it(self):
        watch = getattr(dr, "_dash_watch_parent")
        r, w = os.pipe()
        loop = _FakeLoop()
        t = watch(loop, fd=r, grace=30.0, _exit=lambda c: None)
        blob = (b"\x00\n" * 512 + os.urandom(1024)) * 512
        writer = threading.Thread(target=os.write, args=(w, blob))
        writer.start()
        writer.join(10)
        time.sleep(0.3)
        assert loop.calls == []
        assert t.is_alive()
        os.close(w)
        t.join(5)
        os.close(r)
        assert loop.calls == [loop.stop]

    def test_no_stdin_prints_one_line_and_returns_none(self, monkeypatch,
                                                        capsys):
        watch = getattr(dr, "_dash_watch_parent")
        monkeypatch.setattr(sys, "stdin", None)
        assert watch(_FakeLoop()) is None
        out = capsys.readouterr().out
        assert out.count("dash: no standard input to watch") == 1, out


@pytest.mark.serve
class TestTheGeneratedAppWatchesStdin:

    def test_closing_stdin_stops_a_real_app(self, tmp_path):
        app = _built_app(tmp_path)
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, app, "--port", str(port), "--parent-watch"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            # WP-29 P0.12a: a keyless start writes its link folder here.
            env=dict(os.environ, TMPDIR=str(tmp_path)))
        try:
            assert _wait_health(port, 60, proc), (
                proc.poll(), proc.stderr.read()[-2000:]
                if proc.poll() is not None else "")
            proc.stdin.close()
            rc = proc.wait(timeout=5)
            assert rc == 0
            assert _wait_gone(port, 5)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            _kill_listeners(port)

    def test_without_the_flag_stdin_is_ignored(self, tmp_path):
        app = _built_app(tmp_path)
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, app, "--port", str(port)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # WP-29 P0.12a: a keyless start writes its link folder here.
            env=dict(os.environ, TMPDIR=str(tmp_path)))
        try:
            assert _wait_health(port, 60, proc)
            proc.stdin.close()
            time.sleep(2)
            assert proc.poll() is None
            assert _health(port) == 200
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            _kill_listeners(port)


class TestTheLauncherStartsTheChildWatched:

    def _launch(self, tmp_path, monkeypatch):
        app = _built_app(tmp_path)
        rec = {}

        class _Fake:
            def __init__(self, cmd, **kw):
                rec["cmd"], rec["kw"] = list(cmd), kw
                self.stdin = FakeStdin()
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

            def terminate(self):
                pass

            def kill(self):
                pass

        monkeypatch.setattr(subprocess, "Popen", _Fake)
        dr._dash_launch_app(app, _free_port(), 0, True, prebind=False)
        return app, rec["cmd"], rec["kw"]

    def test_the_child_gets_a_stdin_pipe_and_parent_watch(self, tmp_path,
                                                         monkeypatch):
        app, cmd, kw = self._launch(tmp_path, monkeypatch)
        assert kw["stdin"] is subprocess.PIPE
        assert cmd[:5] == [sys.executable, "-P", "-c", dr._DASH_BOOT, app]
        assert "--parent-watch" in cmd[5:], cmd[5:]

    def test_inside_stata_the_child_is_the_linked_python(self, tmp_path,
                                                         monkeypatch):
        """WP-31 I3: inside Stata the child is c(python_exec), the Python
        Stata is linked to, not sys.executable (under a venv link, the
        venv's base)."""
        exe = _fake_python(tmp_path, "python3")
        _stub_linked_sfi(monkeypatch, exe)
        _app, cmd, _kw = self._launch(tmp_path, monkeypatch)
        assert cmd[0] == exe and cmd[1:4] == ["-P", "-c", dr._DASH_BOOT]

    def test_the_child_stays_in_statas_process_group(self, tmp_path,
                                                     monkeypatch):
        """A5a: no new session or process group, so a console Ctrl+C
        reaches the child as it reaches Stata."""
        _app, _cmd, kw = self._launch(tmp_path, monkeypatch)
        for k in ("start_new_session", "process_group", "preexec_fn",
                  "creationflags"):
            assert not kw.get(k), (k, kw.get(k))


@pytest.mark.serve
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
class TestTheServerDiesWithItsLauncher:

    def _die(self, tmp_path, sig):
        run = _run_inputs(tmp_path)
        port = _free_port()
        parent = _launcher(run, port)
        try:
            assert _wait_health(port, 60, parent), "no server answered"
            os.kill(parent.pid, sig)
            parent.wait(timeout=10)
            t0 = time.monotonic()
            gone = _wait_gone(port, 5)
            took = time.monotonic() - t0
            assert gone, "/health still answers %.1f s after the launcher " \
                "died" % took
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait()
            _kill_listeners(port)

    def test_sigkill_of_the_launcher_stops_the_server(self, tmp_path):
        self._die(tmp_path, signal.SIGKILL)

    def test_sigterm_of_the_launcher_stops_the_server(self, tmp_path):
        self._die(tmp_path, signal.SIGTERM)


@pytest.mark.serve
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
class TestNoCopyOfTheDataWhileServing:

    def test_spec_data_and_app_are_gone_once_health_answers(self, tmp_path):
        run = _run_inputs(tmp_path)
        port = _free_port()
        parent = _launcher(run, port)
        try:
            assert _wait_health(port, 60, parent), "no server answered"
            t0 = time.monotonic()
            left = None
            while time.monotonic() - t0 < 5:
                left = [n for n in ("spec", "data", "app")
                        if os.path.exists(run[n])]
                if not left:
                    break
                time.sleep(0.1)
            assert not left, "still on disk while serving: %s" % left
        finally:
            parent.terminate()
            try:
                parent.wait(timeout=15)
            except subprocess.TimeoutExpired:
                parent.kill()
                parent.wait()
            _kill_listeners(port)

    def test_a_new_session_after_the_erase_is_served(self, tmp_path):
        from bokeh.client import pull_session
        run = _run_inputs(tmp_path)
        port = _free_port()
        parent = _launcher(run, port)
        try:
            assert _wait_health(port, 60, parent), "no server answered"
            t0 = time.monotonic()
            while os.path.exists(run["app"]) and time.monotonic() - t0 < 5:
                time.sleep(0.1)
            assert not os.path.exists(run["app"])
            # Flipped (WP-29 P0.12a): the session carries the key from the
            # run folder's link.html.
            key = _token_in(os.path.dirname(run["app"]))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pull_session(url=_url(port, "/"),
                                  arguments={"token": key}) as session:
                    roots = list(session.document.roots)
            assert roots, "the new session has no roots"
        finally:
            parent.terminate()
            try:
                parent.wait(timeout=15)
            except subprocess.TimeoutExpired:
                parent.kill()
                parent.wait()
            _kill_listeners(port)

    def test_the_recompute_needs_no_file(self, tmp_path):
        """Guard (A9 b): the app's text, run from a string after its file is
        deleted, builds a session and recomputes after a filter move."""
        from bokeh.document import Document
        spec = json.loads(json.dumps(_SPEC))
        spec["build_options"]["filter"] = "mpg, type(range)"
        sp = tmp_path / "s.json"
        dp = tmp_path / "d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(_DF)))
        out = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(out)
        with open(out, encoding="utf-8") as fh:
            src = fh.read()
        os.unlink(out)
        ns = {"__name__": "dash_served_app_under_test",
              "__file__": out}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(src, out, "exec"), ns)
            doc = Document()
            ns["make_document"](doc)
        sliders = [m for m in doc.select({"type": dr.RangeSlider})]
        assert len(sliders) == 1
        w = sliders[0]
        before = {id(s): dict(s.data) for s in doc.select(
            {"type": dr.ColumnDataSource})}
        fired = 0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            old = w.value
            new = (old[0], old[0] + (old[1] - old[0]) / 2.0)
            w.value = new
            for attr in ("value", "value_throttled"):
                for cb in w._callbacks.get(attr, []):
                    cb(attr, old, new)
                    fired += 1
        assert fired >= 1
        after = {id(s): dict(s.data) for s in doc.select(
            {"type": dr.ColumnDataSource})}
        assert any(len(list(after[k].values())[0]) != len(
            list(before[k].values())[0]) for k in after
            if before.get(k) and after[k]), "nothing was recomputed"
        assert not os.path.exists(out)

    def test_the_app_never_reads_its_own_file(self, tmp_path):
        """Guard (A9 c): the app never reads its own file, so erasing it
        once it serves loses nothing.  No ``inspect``, ``linecache`` or
        ``runpy``; no ``open`` of ``__file__`` or ``sys.argv``; and
        ``__file__`` is read only as the folder the copied SchemeParser
        searches for shipped .scheme files (``os.path.dirname(
        os.path.abspath(__file__))``; the scheme arrives in the app as a
        property dict, so that folder is never read) or set by the guard
        that lets the class be defined when the source is exec()'d.
        Narrowed from "no __file__ and no open( at all", which the app at
        commit 1 already breaks for those two reasons (measured)."""
        out = _built_app(tmp_path)
        with open(out, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def _is_attr_call(node, dotted):
            if not isinstance(node, ast.Call):
                return False
            f, names = node.func, []
            while isinstance(f, ast.Attribute):
                names.append(f.attr)
                f = f.value
            if isinstance(f, ast.Name):
                names.append(f.id)
            return ".".join(reversed(names)) == dotted

        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "__file__" and \
                    isinstance(node.ctx, ast.Load):
                up = parents.get(node)
                if not (_is_attr_call(up, "os.path.abspath") and
                        _is_attr_call(parents.get(up), "os.path.dirname")):
                    bad.append("__file__ read as a path")
            if isinstance(node, ast.Attribute) and \
                    isinstance(node.value, ast.Name) and \
                    node.value.id in ("inspect", "linecache", "runpy"):
                bad.append(node.value.id + "." + node.attr)
            if isinstance(node, ast.Call) and \
                    isinstance(node.func, ast.Name) and \
                    node.func.id == "open" and node.args:
                arg = ast.dump(node.args[0])
                if "__file__" in arg or "argv" in arg:
                    bad.append("open() of the app's own path")
        assert not bad, sorted(set(bad))


class _HealthStub:
    """A local /health that answers 200 on a free port."""

    def __enter__(self):
        class _H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200 if self.path == "/health" else 404)
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')

            def log_message(self, *a):
                pass

        self.port = _free_port()
        self.httpd = http.server.HTTPServer(("127.0.0.1", self.port), _H)
        threading.Thread(target=self.httpd.serve_forever,
                         daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def _fake_child(banner, seconds=1.5):
    """A fake child that prints *banner* (or nothing) and exits 0 after
    *seconds*."""
    class _Fake:
        def __init__(self, cmd, **kw):
            self.stdin = FakeStdin()
            self.stdout = io.StringIO(
                "Bokeh Server running at http://localhost:1/\n"
                if banner else "starting\n")
            self.stderr = io.StringIO("")
            self.returncode = None
            self._end = time.monotonic() + seconds

        def poll(self):
            if self.returncode is None and time.monotonic() >= self._end:
                self.returncode = 0
            return self.returncode

        def wait(self, timeout=None):
            while self.poll() is None:
                time.sleep(0.05)
            return self.returncode

        def terminate(self):
            self.returncode = 0

        def kill(self):
            self.returncode = -9

    return _Fake


class TestTheEraseRule:

    def _run_app(self, tmp_path):
        run = _run_inputs(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            written = dr.main(run["spec"], run["data"], run["app"],
                              mode="server", launch=True)
        return run, written

    def test_the_app_is_erased_once_health_and_the_banner_arrive(
            self, tmp_path, monkeypatch):
        run, written = self._run_app(tmp_path)
        monkeypatch.setattr(subprocess, "Popen", _fake_child(True))
        with _HealthStub() as hs:
            dr._dash_launch_app(run["app"], hs.port, 0, True, prebind=False,
                                expect=written, erase_app_when_ready=True)
        assert not os.path.exists(run["app"])

    def test_health_without_the_banner_leaves_the_app(self, tmp_path,
                                                      monkeypatch):
        run, written = self._run_app(tmp_path)
        monkeypatch.setattr(subprocess, "Popen", _fake_child(False))
        with _HealthStub() as hs:
            dr._dash_launch_app(run["app"], hs.port, 0, True, prebind=False,
                                expect=written, erase_app_when_ready=True)
        assert os.path.exists(run["app"])

    def test_outside_a_private_run_folder_nothing_is_erased(
            self, tmp_path, monkeypatch):
        user = tmp_path / "mine"
        user.mkdir()
        app = _built_app(user)
        flag = dr._dash_private_run_of(app) is not None
        assert flag is False
        monkeypatch.setattr(subprocess, "Popen", _fake_child(True))
        with _HealthStub() as hs:
            dr._dash_launch_app(app, hs.port, 0, True, prebind=False,
                                erase_app_when_ready=flag)
        assert os.path.exists(app)
        with open(_RENDER, encoding="utf-8") as fh:
            src = fh.read()
        assert "_erase = _dash_private_run_of(args.output) is not None" \
            in src and "erase_app_when_ready=_erase)" in src


class TestTheHelpSaysTheServerStopsWithStata:

    def test_blocking_and_app_paragraphs(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            h = " ".join(fh.read().split())
        assert "stops by itself" in h
        assert "measured on macOS" in h
        assert "once the server answers" in h


# ===========================================================================
# F4: Break stops dash serve, r(1); messages name Break
# ===========================================================================

def _stub_sfi(raise_on=None, when=None):
    """A stand-in for Stata's sfi: BreakError and SFIToolkit.pollstd, which
    counts its calls and raises BreakError on call *raise_on* (1-based) or
    once *when()* is true."""
    mod = types.ModuleType("sfi")

    class BreakError(Exception):
        pass

    calls = []

    def pollstd():
        calls.append(time.monotonic())
        if raise_on is not None and len(calls) == raise_on:
            raise BreakError("Break")
        if when is not None and when():
            raise BreakError("Break")

    mod.BreakError = BreakError
    mod.SFIToolkit = types.SimpleNamespace(pollstd=pollstd)
    mod.calls = calls
    return mod


class _StopRec:
    """A fake child that records how it is stopped: stdin.close, wait with
    its timeout, terminate and kill.  It runs until its stdin is closed
    (or *seconds* pass, or it is killed), then exits *code*."""

    def __init__(self, seconds=30.0, code=0, ignores_close=False,
                 ignores_terminate=False, wait_raises=None, banner=False):
        self.events = []
        self.code = code
        self.ignores_close = ignores_close
        self.ignores_terminate = ignores_terminate
        self.wait_raises = list(wait_raises or [])
        self.returncode = None
        self._end = time.monotonic() + seconds
        rec = self

        class _In:
            def write(self, b):
                rec.events.append("write")
                return len(b)

            def flush(self):
                pass

            def close(self):
                rec.events.append("close")
                if not rec.ignores_close:
                    rec._end = time.monotonic()

        self.stdin = _In()
        self.stdout = io.StringIO(
            "Bokeh Server running at http://localhost:1/\n" if banner else "")
        self.stderr = io.StringIO("")

    def poll(self):
        if self.returncode is None and time.monotonic() >= self._end:
            self.returncode = self.code
        return self.returncode

    def wait(self, timeout=None):
        self.events.append("wait(%s)" % timeout)
        if self.wait_raises:
            raise self.wait_raises.pop(0)
        t_end = None if timeout is None else time.monotonic() + timeout
        while self.poll() is None:
            if t_end is not None and time.monotonic() >= t_end:
                raise subprocess.TimeoutExpired("fake", timeout)
            time.sleep(0.02)
        return self.returncode

    def terminate(self):
        self.events.append("terminate")
        if not self.ignores_terminate:
            self._end = time.monotonic()

    def kill(self):
        self.events.append("kill")
        self.returncode = -9


def _popen_of(child):
    made = []

    def _popen(cmd, **kw):
        made.append(cmd)
        return child
    _popen.made = made
    return _popen


def _app_in_run(tmp_path):
    run = _run_inputs(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        written = dr.main(run["spec"], run["data"], run["app"],
                          mode="server", launch=True)
    return run, written


class TestTheStataPoller:

    def test_inside_stata_it_returns_pollstd_and_break_error(
            self, monkeypatch):
        poller = getattr(dr, "_dash_stata_poller")
        stub = _stub_sfi()
        monkeypatch.setitem(sys.modules, "sfi", stub)
        poll, brk = poller()
        assert poll is stub.SFIToolkit.pollstd
        assert brk == (stub.BreakError,)
        assert poller(stub) == (stub.SFIToolkit.pollstd, (stub.BreakError,))

    def test_outside_stata_it_returns_nothing(self, monkeypatch):
        poller = getattr(dr, "_dash_stata_poller")
        monkeypatch.setitem(sys.modules, "sfi", None)
        assert poller() == (None, ())
        assert poller(types.SimpleNamespace()) == (None, ())


class TestTheLauncherPollsStata:

    def test_pollstd_is_called_while_it_waits(self, tmp_path, monkeypatch):
        run, written = _app_in_run(tmp_path)
        stub = _stub_sfi()
        monkeypatch.setitem(sys.modules, "sfi", stub)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=1.0)))
        dr._dash_launch_app(run["app"], _free_port(), 0, True,
                            prebind=False, expect=written)
        assert len(stub.calls) >= 3, len(stub.calls)

    def test_break_closes_stdin_stops_the_child_and_raises_interrupted(
            self, tmp_path, monkeypatch, capsys):
        run, written = _app_in_run(tmp_path)
        stub = _stub_sfi(raise_on=3)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        child = _StopRec()
        monkeypatch.setattr(subprocess, "Popen", _popen_of(child))
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)
        assert "close" in child.events
        assert child.returncode is not None
        assert "kill" not in child.events
        assert "dash: stopped by Break; the server has stopped." in \
            capsys.readouterr().out

    def test_a_child_that_ignores_the_close_is_terminated_then_killed(self):
        stop = getattr(dr, "_dash_stop_child")
        child = _StopRec(ignores_close=True, ignores_terminate=True)
        stop(child, grace=0.2)
        assert child.events[0] == "close"
        assert "terminate" in child.events and "kill" in child.events
        assert child.events.index("terminate") < child.events.index("kill")
        assert child.events[-1] == "wait(None)"

    def test_break_during_the_build_starts_no_child(self, tmp_path,
                                                     monkeypatch, capsys):
        run, written = _app_in_run(tmp_path)
        stub = _stub_sfi(raise_on=1)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        popen = _popen_of(_StopRec())
        monkeypatch.setattr(subprocess, "Popen", popen)
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                expect=written)
        assert popen.made == []
        assert "dash: stopped by Break; no server was started." in \
            capsys.readouterr().out

    def test_a_break_pending_when_the_child_exits_is_reported(
            self, tmp_path, monkeypatch):
        run, written = _app_in_run(tmp_path)
        stub = _stub_sfi(raise_on=2)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=0.0)))
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)
        assert len(stub.calls) == 2

    def test_keyboard_interrupt_outside_stata_stops_the_same_way(
            self, tmp_path, monkeypatch, capsys):
        run, written = _app_in_run(tmp_path)
        monkeypatch.setitem(sys.modules, "sfi", None)
        child = _StopRec()
        n = []
        real_poll = child.poll

        def _poll():
            n.append(1)
            if len(n) == 3:
                raise KeyboardInterrupt
            return real_poll()
        child.poll = _poll
        monkeypatch.setattr(subprocess, "Popen", _popen_of(child))
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)
        assert "close" in child.events
        assert "dash_render: interrupted; the server has stopped." in \
            capsys.readouterr().out

    def test_break_before_health_answers_is_not_swallowed(
            self, tmp_path, monkeypatch):
        """A1: BreakError is an Exception; a poll inside the /health
        probe's ``except Exception`` would eat it."""
        run, written = _app_in_run(tmp_path)
        stub = _stub_sfi(raise_on=2)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        child = _StopRec(seconds=8.0)
        monkeypatch.setattr(subprocess, "Popen", _popen_of(child))
        t0 = time.monotonic()
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)
        assert time.monotonic() - t0 < 5
        assert "close" in child.events

    def test_an_interrupt_between_popen_and_the_loop_stops_the_child(
            self, tmp_path, monkeypatch):
        """A4: from Popen on, one try/finally: an interrupt during the
        hand-over still stops the child."""
        run, written = _app_in_run(tmp_path)
        monkeypatch.setitem(sys.modules, "sfi", None)
        child = _StopRec()

        def _boom(b):
            raise KeyboardInterrupt
        child.stdin.write = _boom
        monkeypatch.setattr(subprocess, "Popen", _popen_of(child))
        with pytest.raises(getattr(dr, "_DashServeInterrupted")):
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)
        assert "close" in child.events
        assert child.returncode is not None

    def test_a_second_interrupt_during_the_stop_still_kills(self):
        stop = getattr(dr, "_dash_stop_child")
        child = _StopRec(wait_raises=[KeyboardInterrupt()])
        stop(child, grace=5.0)
        assert child.events[:2] == ["close", "wait(5.0)"]
        assert "kill" in child.events
        assert child.events[-1] == "wait(None)"

    @pytest.mark.parametrize("code,interrupted", [
        (130, True), (-signal.SIGINT, True), (0, False),
        (-signal.SIGTERM, False)])
    def test_a_child_exiting_130_is_an_interrupt_and_a_timeout_is_not(
            self, tmp_path, monkeypatch, code, interrupted):
        run, written = _app_in_run(tmp_path)
        monkeypatch.setitem(sys.modules, "sfi", None)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=0.0, code=code)))
        if interrupted:
            with pytest.raises(getattr(dr, "_DashServeInterrupted")):
                dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                    prebind=False, expect=written)
        else:
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                prebind=False, expect=written)

    @pytest.mark.serve
    def test_a_real_server_stops_on_break(self, tmp_path, monkeypatch):
        run, written = _app_in_run(tmp_path)
        port = _free_port()
        up = threading.Event()

        def _probe():
            if _wait_health(port, 60):
                up.set()
        threading.Thread(target=_probe, daemon=True).start()
        stub = _stub_sfi(when=up.is_set)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        t0 = None
        try:
            with pytest.raises(getattr(dr, "_DashServeInterrupted")):
                dr._dash_launch_app(run["app"], port, 0, True,
                                    expect=written)
            t0 = time.monotonic()
            assert up.is_set()
            assert _wait_gone(port, 10)
        finally:
            _kill_listeners(port)


class TestTheLaunchReportBox:

    def _argv(self, tmp_path, monkeypatch):
        run = _run_inputs(tmp_path)
        port = _free_port()
        monkeypatch.setattr(sys, "argv", [
            "dash_render.py", "--spec", run["spec"], "--data", run["data"],
            "--output", run["app"], "--mode", "server", "--launch",
            "--port", str(port), "--no-browser"])
        return run

    def _run(self, box=None):
        import runpy
        g = {} if box is None else {"_dash_launch_report": box}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            runpy.run_path(_RENDER, init_globals=g, run_name="__main__")

    def test_an_interrupt_lands_in_the_box(self, tmp_path, monkeypatch):
        self._argv(tmp_path, monkeypatch)
        monkeypatch.setitem(sys.modules, "sfi", None)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=0.0, code=130)))
        box = {}
        self._run(box)
        assert box.get("interrupted") is True
        assert "error" not in box

    def test_without_a_box_an_interrupt_exits_130(self, tmp_path,
                                                  monkeypatch):
        self._argv(tmp_path, monkeypatch)
        monkeypatch.setitem(sys.modules, "sfi", None)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=0.0, code=130)))
        with pytest.raises(SystemExit) as ei:
            self._run()
        assert ei.value.code == 130

    def test_the_interrupt_is_not_a_runtime_error(self):
        cls = getattr(dr, "_DashServeInterrupted")
        assert issubclass(cls, Exception)
        assert not issubclass(cls, RuntimeError)

    def test_keyboard_interrupt_during_the_build_lands_in_the_box(
            self, tmp_path, monkeypatch):
        self._argv(tmp_path, monkeypatch)
        popen = _popen_of(_StopRec())
        monkeypatch.setattr(subprocess, "Popen", popen)

        def _ki(*_a, **_k):
            raise KeyboardInterrupt
        monkeypatch.setattr(json, "load", _ki)
        box = {}
        try:
            self._run(box)
        except KeyboardInterrupt:
            # Turned into a failure here: an escaped KeyboardInterrupt
            # would stop the whole pytest session.
            pytest.fail("the KeyboardInterrupt escaped dash_render's "
                        "__main__")
        assert box.get("interrupted") is True
        assert popen.made == []


class TestTheStopHint:

    def _ready_line(self, tmp_path, monkeypatch, stub):
        run, written = _app_in_run(tmp_path)
        monkeypatch.setitem(sys.modules, "sfi", stub)
        monkeypatch.setattr(subprocess, "Popen",
                            _popen_of(_StopRec(seconds=1.5)))
        with _HealthStub() as hs:
            dr._dash_launch_app(run["app"], hs.port, 0, True, prebind=False,
                                expect=written)
            return hs.port

    def test_inside_stata_the_ready_line_names_break(self, tmp_path,
                                                      monkeypatch, capsys):
        port = self._ready_line(tmp_path, monkeypatch, _stub_sfi())
        out = capsys.readouterr().out
        assert ("dash: the server answers at http://127.0.0.1:%d/" % port) \
            in out
        assert "press Break (Ctrl+C in console Stata) to stop." in out
        assert "press Ctrl+C to stop." not in out

    def test_outside_stata_it_names_ctrl_c(self, tmp_path, monkeypatch,
                                           capsys):
        self._ready_line(tmp_path, monkeypatch, None)
        out = capsys.readouterr().out
        assert "press Ctrl+C to stop." in out
        assert "Break" not in out


@pytest.mark.serve
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
class TestTheAppBanner:

    def _start(self, tmp_path):
        app = _built_app(tmp_path)
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, app, "--port", str(port), "--parent-watch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
        return proc, port

    def test_parent_watch_prints_no_ctrl_c_line(self, tmp_path):
        proc, port = self._start(tmp_path)
        try:
            assert _wait_health(port, 60, proc)
            proc.stdin.close()
            out = proc.stdout.read()
            proc.wait(timeout=10)
            assert "Stops when the program that started it ends." in out
            assert "Press Ctrl+C to stop." not in out
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            _kill_listeners(port)

    def test_parent_watch_exits_130_on_sigint(self, tmp_path):
        proc, port = self._start(tmp_path)
        try:
            assert _wait_health(port, 60, proc)
            proc.send_signal(signal.SIGINT)
            assert proc.wait(timeout=15) == 130
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            _kill_listeners(port)


class TestTheHelpNamesBreak:

    def test_syntax_description_timeout_and_blocking_paragraph(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            raw = fh.read()
        h = " ".join(raw.split())
        assert "{ul:Launch Bokeh Server (blocking -- press Break to stop)}" \
            in raw
        assert "Stata waits until you press Break (Ctrl+C in console " \
            "Stata), the optional {cmd:timeout()} expires, or Stata itself " \
            "exits." in h
        assert "0 means run until Break (default)" in h
        assert "Break -- the Break button or menu item, or Ctrl+C in " \
            "console Stata -- stops it at once, and the command ends with " \
            "r(1)" in h
        assert "{ul:Live Bokeh Server (blocking — Break to stop)}" in raw
        assert "Stata is blocked until you press Ctrl+C" not in h


class TestTheAdoEndsWithROne:

    def test_serve_reads_interrupted_closes_and_errors_1(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        import re as _re
        m = _re.search(r"(?ms)^program define _dash_serve\n(.*?)^end\b", ado)
        assert m, "dash.ado has no _dash_serve"
        lines = [ln.strip() for ln in m.group(1).splitlines()
                 if ln.strip() and not ln.strip().startswith("//")]
        text = "\n".join(lines)
        assert 'python: _dash_srv_M.setLocal("_srv_brk", "1" if ' \
            '_dash_srv_rep.get("interrupted") else "")' in text
        i_close = max(k for k, ln in enumerate(lines)
                      if ln.startswith("_dash_tmp_close"))
        i_err = lines.index('if "`_srv_brk\'" == "1" error 1')
        assert i_close < i_err
        assert "press Break (Ctrl+C in console Stata) to stop it." in text
        assert "Stata is blocked until the server stops (Ctrl+C)" not in text


# ---------------------------------------------------------------------------
# WP-31 I3: the interpreter dash serve starts its app with
# ---------------------------------------------------------------------------

def _fake_python(tmp_path, name):
    d = tmp_path / "pybin"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text("#!/bin/sh\n")
    p.chmod(0o755)
    return str(p)


def _stub_linked_sfi(monkeypatch, exec_value):
    mod = types.ModuleType("sfi")
    mod.SFIToolkit = types.SimpleNamespace(
        macroExpand=lambda s: {"\x60c(python_exec)'": exec_value}[s])
    monkeypatch.setitem(sys.modules, "sfi", mod)


class TestTheChildInterpreter:

    def test_outside_stata_it_is_this_python(self, monkeypatch):
        monkeypatch.delitem(sys.modules, "sfi", raising=False)
        assert dr._dash_child_python() == sys.executable

    def test_the_linked_python_is_used(self, tmp_path, monkeypatch, capsys):
        exe = _fake_python(tmp_path, "python3.13")
        _stub_linked_sfi(monkeypatch, exe)
        assert dr._dash_child_python() == exe
        assert capsys.readouterr().out == ""

    def test_a_bad_path_falls_back_with_a_note(self, tmp_path, monkeypatch,
                                               capsys):
        _stub_linked_sfi(monkeypatch, str(tmp_path / "nowhere" / "python3"))
        assert dr._dash_child_python() == sys.executable
        out = capsys.readouterr().out
        assert out.count("dash: ") == 1 and sys.executable in out, out
        assert "nowhere" in out

    @pytest.mark.parametrize("bad", ["python3", "bin/python3",
                                     "{dir}/py;thon3", "{dir}/py$thon3",
                                     "{dir}/notpy"])
    def test_a_relative_or_shell_path_is_refused(self, tmp_path, monkeypatch,
                                                 capsys, bad):
        name = os.path.basename(bad.format(dir="x"))
        real = _fake_python(tmp_path, name)
        value = bad.format(dir=os.path.dirname(real))
        _stub_linked_sfi(monkeypatch, value)
        assert dr._dash_child_python() == sys.executable
        assert capsys.readouterr().out.count("dash: ") == 1
