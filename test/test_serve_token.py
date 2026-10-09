"""test_serve_token.py -- the served dashboard needs its key (WP-29 P0.12a).

Measured at the base: ``python app.py`` answered ``GET /`` 200 to a client
with no credential, and ``bokeh.client.pull_session`` -- no credential, no
Origin -- received a ColumnDataSource with every value of ``mpg``.  On a
machine with more than one account, any account could read the dashboard's
data while it was served.

Two gates close it.  Gate A, a Bokeh ``AuthProvider`` (``_dash_token_auth``),
refuses every page, ``/autoload.js``, ``/metadata`` and websocket request
without the key with a constant 403, before any handler runs (``python
app.py`` and ``dash serve``).  Gate B, in ``make_document``
(``_dash_session_token_ok``), refuses every session without the key before
the rate limiter and before the data is decoded: under ``bokeh serve``, which
gives a script no Tornado hook, it is the only gate.  The app never runs
without a key: started with none it makes its own, writes its link to a 0600
``link.html`` in a fresh 0700 folder, and prints only that file's path
(ratified 01oct2026); when no file can be written anywhere it prints the link
once after a warning and keeps serving (round 2).
"""
import asyncio
import ast
import base64
import contextlib
import errno
import inspect
import io
import json
import logging
import os
import re
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
import types
import urllib.error
import urllib.request
import warnings
import zlib

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import serve_token_probe  # noqa: E402
from serve_token_probe import (TEST_TOKEN, FakeStdin, LINK_RE,  # noqa: E402
                               drop_holder, link_path_in, read_link,
                               token_args)
from conftest import make_spec  # noqa: E402
from test_adversarial_matrix import (_SCATTER, _LiveApp,  # noqa: E402
                                     _SessionDoc, _app_source,
                                     _launcher_said, _load_app)
from test_server_serves import _build_app  # noqa: E402

T = TEST_TOKEN
_KEY43 = re.compile(r"[A-Za-z0-9_-]{43}")
_SEQ = iter(range(10 ** 6))
_LOGGERS = ("tornado.access", "tornado.general", "tornado.application")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _req(args, remote_ip="10.0.0.1", **headers):
    return types.SimpleNamespace(remote_ip=remote_ip, headers=headers,
                                 arguments=args)


def _drop_filters():
    for name in _LOGGERS:
        lg = logging.getLogger(name)
        for f in list(lg.filters):
            if getattr(f, "_dash_redacts_queries", False):
                lg.removeFilter(f)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """No test makes a key outside its own folder, inherits a key from the
    environment, or leaves a holder or a log filter behind."""
    monkeypatch.delenv("DASH_SERVE_TOKEN", raising=False)
    tdir = tmp_path / "tmp"
    tdir.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tdir))
    drop_holder()
    yield str(tdir)
    drop_holder()
    _drop_filters()


@pytest.fixture(scope="module")
def app_src(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tok_app")
    return _app_source(tmp, make_spec([dict(_SCATTER)]))


def _ns(src):
    return _load_app(src, "tok_%d" % next(_SEQ))


def _session(ns, doc):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _has_plot(doc):
    return any(type(m).__name__ == "Plot" or type(m).__name__ == "figure"
               for m in doc.select({}))


def _divs(doc):
    return " ".join(getattr(m, "text", "") or ""
                    for m in doc.select({}) if type(m).__name__ == "Div")


def _refused(doc):
    return not _has_plot(doc) and "403" in _divs(doc)


def _link_dirs(tdir):
    return sorted(p for p in os.listdir(tdir) if p.startswith("dash-link-"))


def _mode(path):
    return oct(stat.S_IMODE(os.stat(path).st_mode))[-3:]


def _lines(text):
    return [ln for ln in text.splitlines()
            if not ln.startswith("dash: this Bokeh admits")]


class _RecServer:
    made = []

    def __init__(self, apps, **kw):
        self.kw = kw
        self.stopped = 0
        _RecServer.made.append(self)

    def stop(self):
        self.stopped += 1


def _admits(provider, key):
    h = types.SimpleNamespace(request=_req(token_args(key)))
    try:
        return asyncio.run(provider.get_user_async(h)) == "dash"
    except Exception:
        return False


class _ServedDoc(_SessionDoc):
    """A session of a served app: a request with the server-side address
    (``connection.stream.socket.getsockname``) and the app's path."""

    def __init__(self, request, sockname=("127.0.0.1", 5123), url="/app"):
        super().__init__(request)
        sock = types.SimpleNamespace(getsockname=lambda: sockname)
        request.connection = types.SimpleNamespace(
            stream=types.SimpleNamespace(socket=sock))
        self._url = url

    @property
    def session_context(self):
        return types.SimpleNamespace(
            request=self._matrix_request,
            server_context=types.SimpleNamespace(
                application_context=types.SimpleNamespace(url=self._url)))


def _fake_doc(sockname=("::1", 5123, 0, 0), url="/app", ws=False):
    conn = None if ws else types.SimpleNamespace(
        stream=types.SimpleNamespace(socket=types.SimpleNamespace(
            getsockname=lambda: sockname)))
    return types.SimpleNamespace(session_context=types.SimpleNamespace(
        server_context=types.SimpleNamespace(
            application_context=types.SimpleNamespace(url=url)),
        request=types.SimpleNamespace(arguments={}, connection=conn)))


def _status(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.headers, \
                r.reason
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers, \
            e.reason


def _pull_rows(url, key=None):
    """(rows of mpg, the document's Div text) of a pulled session."""
    from bokeh.client import pull_session
    kw = {"arguments": {"token": key}} if key else {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pull_session(url=url, **kw) as s:
            n = 0
            for m in s.document.select({}):
                data = getattr(m, "data", None)
                if isinstance(data, dict) and "mpg" in data:
                    n = max(n, len(data["mpg"]))
            return n, _divs(s.document), _has_plot(s.document)


def _ws(port, origin, jwt=None, path="", key=T):
    """``(status, first message type)`` of a browser's websocket handshake:
    the keyed page's session JWT (or *jwt*), then ``<path>/ws`` with the
    Bokeh subprotocol, as BokehJS asks."""
    if jwt is None:
        with urllib.request.urlopen(
                "http://127.0.0.1:%d%s/?token=%s" % (port, path, key)
                if not path else
                "http://127.0.0.1:%d%s?token=%s" % (port, path, key),
                timeout=10) as r:
            page = r.read().decode("utf-8", "replace")
        m = re.search(r'"token":\s*"([^"]+)"', page)
        assert m, "the served page carries no session token"
        jwt = m.group(1)
    wkey = base64.b64encode(os.urandom(16)).decode("ascii")
    request = ("GET %s/ws HTTP/1.1\r\nHost: 127.0.0.1:%d\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
               "Sec-WebSocket-Protocol: bokeh, %s\r\nOrigin: %s\r\n\r\n"
               ) % (path, port, wkey, jwt, origin)
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.sendall(request.encode("utf-8"))
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = s.recv(4096)
            assert chunk, "closed inside the response"
            buf += chunk
        head, _, buf = buf.partition(b"\r\n\r\n")
        st = int(re.match(rb"HTTP/1\.[01] (\d{3}) ", head).group(1))
        if st != 101:
            return st, None

        def _take(n):
            nonlocal buf
            while len(buf) < n:
                chunk = s.recv(4096)
                assert chunk, "closed inside a frame"
                buf += chunk
            out, buf = buf[:n], buf[n:]
            return out

        b0, b1 = _take(2)
        size = b1 & 0x7F
        if size == 126:
            size = struct.unpack(">H", _take(2))[0]
        elif size == 127:
            size = struct.unpack(">Q", _take(8))[0]
        return 101, json.loads(_take(size))["msgtype"]


class _Proc:
    """A live process (the app, ``bokeh serve`` or a patched start), its
    output kept by a reader thread; stopped with SIGINT, so its ``finally``
    and ``atexit`` run, then killed if it will not stop."""

    def __init__(self, cmd, env=None, ready="/health", port=None, cwd=None):
        self.cmd = cmd
        self.port = port
        self.ready = ready
        self.cwd = cwd
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("DASH_SERVE_TOKEN", "BOKEH_ALLOW_WS_ORIGIN")}
        for k, v in (env or {}).items():
            if v is None:
                self.env.pop(k, None)
            else:
                self.env[k] = v
        self.lines = []
        self.proc = None

    def _read(self):
        for line in iter(self.proc.stdout.readline, ""):
            self.lines.append(line.rstrip("\n"))

    def said(self):
        return "\n".join(self.lines)

    def __enter__(self):
        self.proc = subprocess.Popen(
            self.cmd, env=self.env, cwd=self.cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            errors="replace")
        threading.Thread(target=self._read, daemon=True).start()
        try:
            deadline = time.monotonic() + 60
            while True:
                st = _status("http://127.0.0.1:%d%s" % (self.port,
                                                        self.ready))[0] \
                    if self._listening() else None
                if st == 200:
                    break
                if self.proc.poll() is not None:
                    time.sleep(0.3)
                    raise AssertionError("exited early:\n" + self.said())
                if time.monotonic() > deadline:
                    raise AssertionError("never answered:\n" + self.said())
                time.sleep(0.2)
        except BaseException:
            self.stop()
            raise
        return self

    def _listening(self):
        try:
            with socket.create_connection(("127.0.0.1", self.port), 1):
                return True
        except OSError:
            return False

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=15)
        time.sleep(0.2)

    def __exit__(self, *exc):
        self.stop()
        return False

    def wait_for(self, pred, seconds=15):
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            if pred(self.said()):
                return True
            time.sleep(0.1)
        return pred(self.said())


def _app_cmd(app, port, *extra):
    return [sys.executable, app, "--port", str(port)] + list(extra)


def _bs_cmd(app, port, allow_127=True, *extra):
    cmd = [sys.executable, "-m", "bokeh", "serve", app, "--port", str(port),
           "--allow-websocket-origin", "localhost:%d" % port]
    if allow_127:
        cmd += ["--allow-websocket-origin", "127.0.0.1:%d" % port]
    return cmd + list(extra)


#: A start whose every tempfile.mkdtemp fails (process-wide; Evidence §7).
_PATCH = ("import sys, tempfile, runpy\n"
          "def _no(*a, **k):\n"
          "    raise PermissionError(13, 'Permission denied')\n"
          "tempfile.mkdtemp = _no\n")
_PATCH_APP = _PATCH + ("sys.argv = sys.argv[1:]\n"
                       "runpy.run_path(sys.argv[0], run_name='__main__')\n")
_PATCH_SHOW = _PATCH + (
    "import webbrowser\n"
    "def _rec(*a, **k):\n"
    "    print('dash-test: opener called', flush=True)\n"
    "    return True\n"
    "webbrowser.open = _rec\n"
    "sys.argv = sys.argv[1:]\n"
    "runpy.run_path(sys.argv[0], run_name='__main__')\n")
_PATCH_BS = _PATCH + ("import bokeh.__main__\n"
                      "sys.argv = ['bokeh', 'serve'] + sys.argv[1:]\n"
                      "bokeh.__main__.main()\n")


def _keyed_live(app):
    return _LiveApp(app, env={"DASH_SERVE_TOKEN": T})


@pytest.fixture(scope="module")
def live_app_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tok_live")
    _app_source(tmp, make_spec([dict(_SCATTER)]))
    return os.path.join(str(tmp), "app.py")


@pytest.fixture(scope="module")
def bs_app_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tok_bs")
    return _build_app(str(tmp))


# ===========================================================================
# The helpers
# ===========================================================================
class TestTheTokenHelpers:

    def test_new_tokens_are_43_urlsafe_and_unique(self):
        keys = [dr._dash_new_token() for _ in range(1000)]
        assert all(_KEY43.fullmatch(k) for k in keys)
        assert len(set(keys)) == 1000
        assert all(dr._dash_token_valid(k) for k in keys)

    def test_invalid_shapes_are_refused(self):
        bad = ["", "a" * 31, "a" * 129, "a" * 31 + "+", "a" * 31 + "/",
               "a" * 31 + "=", "a" * 31 + "\x00", "a" * 31 + "а",
               " " + "a" * 32, "a" * 32 + "\n", None, 123, b"\xff" * 40]
        for v in bad:
            assert dr._dash_token_valid(v) is False, repr(v)[:40]
        t0 = time.monotonic()
        assert dr._dash_token_valid("a" * 10000) is False
        assert time.monotonic() - t0 < 0.05
        for v in ("a" * 32, "A-_9" * 10, b"a" * 40):
            assert dr._dash_token_valid(v) is True, v

    def test_the_right_token_matches_and_a_near_miss_does_not(self):
        assert dr._dash_token_matches(T, T)
        assert dr._dash_token_matches(T.encode(), T)
        assert not dr._dash_token_matches(T[:-1] + "Q", T)
        assert not dr._dash_token_matches(None, T)
        assert not dr._dash_token_matches("", T)
        assert not dr._dash_token_matches("short", "short")
        assert not dr._dash_token_matches(T, None)

    def test_matching_is_constant_time(self):
        tree = ast.parse(inspect.getsource(dr._dash_token_matches))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "attr", getattr(n.func, "id", ""))
                 == "compare_digest"]
        assert calls
        assert not any(isinstance(n, (ast.Eq, ast.NotEq))
                       for n in ast.walk(tree))

    def test_one_value_takes_exactly_one(self):
        assert dr._dash_one_value(["x"]) == "x"
        assert dr._dash_one_value(["x", "y"]) is None
        assert dr._dash_one_value([]) is None
        assert dr._dash_one_value("x") == "x"

    def test_the_environment_token_is_read_only_when_valid(self):
        assert dr._dash_env_token({"DASH_SERVE_TOKEN": T}) == T
        assert dr._dash_env_token({"DASH_SERVE_TOKEN": "abc"}) is None
        assert dr._dash_env_token({}) is None

    def test_the_request_token_is_read_from_query_or_ws_jwt(self):
        from bokeh.util.token import generate_jwt_token

        def h(args=None, **headers):
            return types.SimpleNamespace(request=types.SimpleNamespace(
                arguments=args or {}, headers=headers))

        assert dr._dash_request_token(h({"token": [b"T"]})) == b"T"
        assert dr._dash_request_token(h({"token": [b"T", b"T"]})) is None
        jwt = generate_jwt_token("A" * 44, extra_payload={
            "arguments": {"token": [T]}})
        assert dr._dash_request_token(h(**{
            "Sec-WebSocket-Protocol": "bokeh, " + jwt})) == T
        assert dr._dash_request_token(h(**{
            "Sec-WebSocket-Protocol": "bokeh, x.y"})) is None
        assert dr._dash_request_token(h(**{
            "Sec-WebSocket-Protocol": "evil, " + jwt})) is None
        assert dr._dash_request_token(h(**{
            "Sec-WebSocket-Protocol": "bokeh, " + "a" * 20000})) is None

    def test_a_jwt_that_inflates_is_refused_quickly(self, monkeypatch):
        def jwt_of(n):
            bomb = zlib.compress(b"0" * n, 9)
            member = base64.urlsafe_b64encode(bomb).decode().rstrip("=")
            head = base64.urlsafe_b64encode(json.dumps(
                {"session_id": "x", "__bk__zlib_": member}).encode()
            ).decode().rstrip("=")
            return head + ".sig"
        # 10 MB: its JWT is itself past the header bound.  8 MB fits under
        # it, so only the inflation probe can refuse it.
        big, fits = jwt_of(10 * 1024 * 1024), jwt_of(8 * 1024 * 1024)
        assert len(big) > dr._DASH_WS_PROTOCOL_MAX
        assert len(fits) <= dr._DASH_WS_PROTOCOL_MAX
        import bokeh.util.token as _bt
        decoded = []
        monkeypatch.setattr(_bt, "get_token_payload",
                            lambda t: decoded.append(t) or {})
        for jwt in (big, fits):
            t0 = time.monotonic()
            assert dr._dash_ws_payload("bokeh, " + jwt) is None
            assert time.monotonic() - t0 < 0.5
        assert decoded == [], "Bokeh's unbounded decoder was reached"

    def test_the_provider_refuses_with_403_and_admits_with_the_token(self):
        from bokeh.server.auth_provider import AuthProvider
        from tornado.web import HTTPError
        prov = dr._dash_token_auth(T)
        assert isinstance(prov, AuthProvider)
        ok = types.SimpleNamespace(request=_req(token_args()))
        assert asyncio.run(prov.get_user_async(ok)) == "dash"
        bad = types.SimpleNamespace(request=_req(token_args(T[:-1] + "Q")))
        with pytest.raises(HTTPError) as e:
            asyncio.run(prov.get_user_async(bad))
        assert e.value.status_code == 403
        assert e.value.reason == dr._DASH_TOKEN_REFUSAL
        with pytest.raises(ValueError):
            dr._dash_token_auth("short")

    def test_the_login_url_also_refuses(self):
        from tornado.web import HTTPError
        prov = dr._dash_token_auth(T)
        with pytest.raises(HTTPError) as e:
            prov.get_login_url(types.SimpleNamespace(request=_req({})))
        assert e.value.status_code == 403

    def test_the_redaction_strips_every_query(self):
        assert dr._dash_redact_query(
            "GET /?token=T&x=1 (127.0.0.1) 1.0ms") == \
            "GET /?<query redacted> (127.0.0.1) 1.0ms"
        s = "is Python available on this PATH?"
        assert dr._dash_redact_query(s) == s
        assert dr._dash_redact_query("http://127.0.0.1:5/?token=T") == \
            "http://127.0.0.1:5/?<query redacted>"
        assert dr._dash_redact_query("a " + T + " b", T) == "a <key> b"

    def test_the_access_filter_rewrites_the_record(self):
        rec = logging.LogRecord(
            "tornado.access", logging.WARNING, __file__, 1, "%d %s %.2fms",
            (403, "GET /?token=" + T + " (127.0.0.1)", 1.0), None)
        assert dr._dash_redact_access_record(rec) is True
        msg = rec.getMessage()
        assert T not in msg and "?<query redacted>" in msg

    def test_the_filter_installs_once(self, app_src):
        _drop_filters()
        dr._dash_install_access_log_redaction()
        dr._dash_install_access_log_redaction()
        _ns(app_src)
        n = [f for f in logging.getLogger("tornado.access").filters
             if getattr(f, "_dash_redacts_queries", False)]
        assert len(n) == 1

    def test_the_tokenized_url(self):
        u = dr._dash_tokenized_url
        assert u(5006, T) == "http://127.0.0.1:5006/?token=" + T
        for a in (None, "", "0.0.0.0", "localhost", "127.0.0.1"):
            assert u(5006, T, a).startswith("http://127.0.0.1:5006/")
        for a in ("::", "::1"):
            assert u(5006, T, a).startswith("http://[::1]:5006/")
        assert u(5006, T, "192.168.1.5").startswith(
            "http://192.168.1.5:5006/")
        assert u(5006, T, "fe80::1").startswith("http://[fe80::1]:5006/")
        for args in ((5006, T, "fe80::1%en0"), (5006, T, "a b"),
                     (5006, "bad!"), (80, T), (70000, T)):
            with pytest.raises(ValueError):
                u(*args)
        assert u(5006, T, path="/app") == \
            "http://127.0.0.1:5006/app?token=" + T
        assert u(5006, T, path="/my app") == \
            "http://127.0.0.1:5006/my%20app?token=" + T
        assert u(5006, T, path="/a?x") == \
            "http://127.0.0.1:5006/a%3Fx?token=" + T
        for p in ("app", None):
            with pytest.raises(ValueError):
                u(5006, T, path=p)

    def test_the_redirect_page_escapes_and_sends_no_referrer(self):
        page = dr._dash_redirect_page("http://127.0.0.1:5/?token=a&b=c")
        assert '<meta name="referrer" content="no-referrer">' in page
        assert 'http-equiv="refresh"' in page
        assert "token=a&amp;b=c" in page
        evil = dr._dash_redirect_page('http://x/"><script>')
        assert "<script" not in evil
        assert "&quot;&gt;&lt;script&gt;" in evil

    def test_opening_never_puts_the_token_in_argv(self, _isolated):
        url = "http://127.0.0.1:5006/?token=" + T
        got = []

        def rec(u):
            got.append(u)
            return True

        d = dr._dash_open_tokenized(url, platform="linux", environ={},
                                    opener=rec, out=io.StringIO())
        assert len(got) == 1 and got[0].startswith("file://")
        assert T not in got[0]
        p = os.path.join(d, "open.html")
        assert _mode(p) == "600" and _mode(d) == "700"
        with open(p, encoding="utf-8") as fh:
            assert dr._dash_redirect_page(url) == fh.read()
        osa, op = [], []
        r = dr._dash_open_tokenized(url, platform="darwin", environ={},
                                    opener=op.append, osa=osa.append)
        assert osa == [url] and op == [] and r is None
        got.clear()
        d2 = dr._dash_open_tokenized(url, platform="darwin",
                                     environ={"BROWSER": "x"}, opener=rec,
                                     osa=osa.append, out=io.StringIO())
        assert len(got) == 1 and got[0].startswith("file://") and d2
        assert osa == [url]

    def test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none(
            self, _isolated, monkeypatch):
        import webbrowser
        url = "http://127.0.0.1:5006/?token=" + T
        for exc, name in ((OSError(errno.ENOSPC, "No space left on device"),
                           "OSError"),
                          (PermissionError(13, "Permission denied"),
                           "PermissionError")):
            def _raise(*a, **k):
                raise exc
            monkeypatch.setattr(dr, "_dash_private_page", _raise)
            for plat, env in (("linux", {}), ("darwin", {"BROWSER": "x"})):
                rec, osa, wb = [], [], []
                monkeypatch.setattr(webbrowser, "open",
                                    lambda u, *a, **k: wb.append(u))
                out = io.StringIO()
                r = dr._dash_open_tokenized(url, platform=plat, environ=env,
                                            opener=rec.append,
                                            osa=osa.append, out=out)
                assert r is None
                assert rec == [] and osa == [] and wb == []
                lines = out.getvalue().splitlines()
                assert lines == [
                    "dash: the browser was not opened: its page could not "
                    "be written (%s); open the dashboard's link instead."
                    % name]
                assert not any(T in ln or "?token=" in ln or "http" in ln
                               for ln in lines)
        assert not [p for p in os.listdir(_isolated)
                    if p.startswith("dash-open-")]

    def test_the_token_line_is_bounded(self):
        def pipe_with(data, close=True):
            r, w = os.pipe()
            os.write(w, data)
            if close:
                os.close(w)
            return r, w

        r, w = pipe_with((T + "\nmore").encode(), close=False)
        assert dr._dash_read_token_line(r) == T
        assert os.read(r, 10) == b"more"
        os.close(r)
        os.close(w)
        r, _ = pipe_with(b"a" * 300 + b"\n")
        assert dr._dash_read_token_line(r) is None
        os.close(r)
        r, _ = pipe_with(b"abc")
        assert dr._dash_read_token_line(r) is None
        os.close(r)
        r, _ = pipe_with("éé\n".encode("utf-8"))
        assert dr._dash_read_token_line(r) is None
        os.close(r)
        r, _ = pipe_with((T + "\r\n").encode())
        assert dr._dash_read_token_line(r) == T
        os.close(r)

    def test_the_private_page_is_0600_in_a_0700_folder(self, _isolated,
                                                       monkeypatch):
        out = io.StringIO()
        d, p = dr._dash_private_page("<p>x</p>", "dash-link-", "link.html",
                                     out=out)
        assert os.path.dirname(d) == _isolated
        assert os.path.basename(d).startswith("dash-link-")
        assert p == os.path.join(d, "link.html")
        assert _mode(d) == "700" and _mode(p) == "600"
        with open(p, encoding="utf-8") as fh:
            assert fh.read() == "<p>x</p>"
        assert out.getvalue() == ""
        old = os.umask(0)
        try:
            d2, p2 = dr._dash_private_page("y", "dash-link-", "link.html",
                                           out=out)
        finally:
            os.umask(old)
        assert _mode(p2) == "600"
        shutil.rmtree(d, True)
        shutil.rmtree(d2, True)

        real_open = os.open

        def _no(path, *a, **k):
            if os.fspath(path).endswith("link.html"):
                raise OSError(errno.EIO, "I/O error")
            return real_open(path, *a, **k)
        monkeypatch.setattr(os, "open", _no)
        with pytest.raises(OSError):
            dr._dash_private_page("z", "dash-link-", "link.html", out=out)
        assert _link_dirs(_isolated) == []

    def test_a_page_the_disk_will_not_keep_private_is_written_with_a_note(
            self, _isolated, monkeypatch, capsys):
        seen = []
        real_fstat = os.fstat
        monkeypatch.setattr(os, "fchmod",
                            lambda fd, m: seen.append(m), raising=False)

        def loose(fd):
            st = real_fstat(fd)
            return os.stat_result((st.st_mode | 0o044,) + tuple(st)[1:])
        monkeypatch.setattr(os, "fstat", loose)
        text = "<p>" + T + "</p>"
        out = io.StringIO()
        d, p = dr._dash_private_page(text, "dash-link-", "link.html", out=out)
        with open(p, encoding="utf-8") as fh:
            assert fh.read() == text
        assert seen == [0o600]
        # Flipped (WP-30 P1.26b): the note is a note, printed through
        # _dash_emit_note in twoway's form, never on *out*.
        assert out.getvalue() == ""
        lines = capsys.readouterr().err.splitlines()
        assert len(lines) == 1 and lines[0].startswith("(note:  dash: ")
        assert p in lines[0] and "TMPDIR" in lines[0] and T not in lines[0]
        shutil.rmtree(d, True)

        def foreign(fd):
            st = real_fstat(fd)
            t = list(tuple(st))
            t[4] = os.geteuid() + 1
            return os.stat_result(tuple(t))
        monkeypatch.setattr(os, "fstat", foreign)
        out = io.StringIO()
        with pytest.raises(OSError):
            dr._dash_private_page(text, "dash-link-", "link.html", out=out)
        assert out.getvalue() == ""
        assert _link_dirs(_isolated) == []

    def test_the_announcement_names_the_file_never_the_key(self, _isolated):
        url = "http://127.0.0.1:5006/?token=" + T
        out = io.StringIO()
        d = dr._dash_announce_key(url, out=out)
        p = os.path.join(d, "link.html")
        assert out.getvalue().splitlines() == [dr._DASH_LINK_SAID, p]
        with open(p, encoding="utf-8") as fh:
            assert fh.read() == dr._dash_redirect_page(url)
        assert _mode(p) == "600" and _mode(d) == "700"
        out = io.StringIO()
        d2 = dr._dash_announce_key(url, out=out, hint="H")
        lines = out.getvalue().splitlines()
        assert lines == [dr._DASH_LINK_SAID,
                         os.path.join(d2, "link.html"), "H"]
        assert not any(T in ln or "?token=" in ln for ln in lines)

    def test_an_unwritable_link_is_printed_once_with_a_warning(
            self, _isolated, monkeypatch):
        def _raise(*a, **k):
            raise PermissionError(13, "Permission denied")
        monkeypatch.setattr(dr, "_dash_private_page", _raise)
        url = "http://127.0.0.1:5006/?token=" + T
        out = io.StringIO()
        assert dr._dash_announce_key(url, out=out) is None
        lines = out.getvalue().splitlines()
        assert lines == [dr._DASH_LINK_UNWRITTEN % "PermissionError", url]
        out = io.StringIO()
        dr._dash_announce_key(url, out=out, hint="H")
        lines = out.getvalue().splitlines()
        assert lines == [dr._DASH_LINK_UNWRITTEN % "PermissionError", url,
                         "H"]
        assert [ln for ln in lines if T in ln] == [url]
        assert _link_dirs(_isolated) == []
        assert dr._DASH_LINK_UNWRITTEN.count("%s") == 1
        warn = dr._DASH_LINK_UNWRITTEN % "PermissionError"
        assert T not in warn and os.sep not in warn

    def test_the_process_key_is_made_once(self):
        h1 = dr._dash_process_key()
        h2 = dr._dash_process_key()
        assert h1 is h2
        assert dr._dash_token_valid(h1.key) and len(h1.key) == 43
        assert sys.modules["_dash_serve_key"] is h1
        sys.modules["_dash_serve_key"] = types.ModuleType("x")
        h3 = dr._dash_process_key()
        assert h3 is not h1 and dr._dash_token_valid(h3.key)
        assert sys.modules["_dash_serve_key"] is h3

    def test_the_bokeh_serve_key_announces_once_from_a_page_request(
            self, _isolated, monkeypatch):
        out = io.StringIO()
        assert dr._dash_bokeh_serve_key(
            types.SimpleNamespace(session_context=None), out=out) is None
        assert "_dash_serve_key" not in sys.modules
        k = dr._dash_bokeh_serve_key(_fake_doc(ws=True), out=out)
        assert dr._dash_token_valid(k) and out.getvalue() == ""
        assert dr._dash_bokeh_serve_key(_fake_doc(), out=out) == k
        lines = out.getvalue().splitlines()
        assert len(lines) == 3
        assert lines[0] == dr._DASH_LINK_SAID
        assert lines[1].endswith("link.html")
        assert lines[2] == dr._DASH_BS_ORIGIN_HINT % 5123
        with open(lines[1], encoding="utf-8") as fh:
            assert "http://127.0.0.1:5123/app?token=" + k in fh.read()
        assert not any(k in ln for ln in lines)
        assert dr._dash_bokeh_serve_key(_fake_doc(), out=out) == k
        assert len(out.getvalue().splitlines()) == 3
        assert len(_link_dirs(_isolated)) == 1
        drop_holder()
        monkeypatch.setenv("DASH_SERVE_TOKEN", "weak!value")
        out = io.StringIO()
        assert dr._dash_bokeh_serve_key(_fake_doc(), out=out) is None
        lines = out.getvalue().splitlines()
        assert len(lines) == 1 and "DASH_SERVE_TOKEN" in lines[0]
        assert "weak!value" not in lines[0]
        assert dr._dash_bokeh_serve_key(_fake_doc(), out=out) is None
        assert len(out.getvalue().splitlines()) == 1
        assert len(_link_dirs(_isolated)) == 1

    def test_the_bokeh_serve_link_that_cannot_be_written_is_printed_once(
            self, _isolated, monkeypatch):
        def _raise(*a, **k):
            raise OSError(errno.ENOSPC, "No space left on device")
        monkeypatch.setattr(dr, "_dash_private_page", _raise)
        out = io.StringIO()
        k = dr._dash_bokeh_serve_key(_fake_doc(), out=out)
        assert dr._dash_token_valid(k)
        lines = out.getvalue().splitlines()
        assert lines == [dr._DASH_LINK_UNWRITTEN % "OSError",
                         "http://127.0.0.1:5123/app?token=" + k,
                         dr._DASH_BS_ORIGIN_HINT % 5123]
        for doc in (_fake_doc(), _fake_doc(ws=True), _fake_doc()):
            assert dr._dash_bokeh_serve_key(doc, out=out) == k
        assert out.getvalue().splitlines() == lines
        assert len([ln for ln in lines if k in ln]) == 1
        assert _link_dirs(_isolated) == []

    def test_the_probe_knows_the_announcement(self):
        assert serve_token_probe.LINK_SAID == dr._DASH_LINK_SAID
        assert link_path_in(serve_token_probe.LINK_SAID +
                            "\n/x/link.html\n") == "/x/link.html"


# ===========================================================================
# Gate B, in process
# ===========================================================================
class TestTheSessionGate:

    @pytest.fixture
    def ns(self, app_src):
        ns = _ns(app_src)
        ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN
        return ns

    def test_a_session_without_the_token_gets_only_the_refusal(self, ns):
        def _spy(*a, **k):
            raise AssertionError("the data was decoded for a refused session")
        ns["_load_spec_and_data"] = _spy
        doc = _session(ns, _SessionDoc(_req({})))
        assert not _has_plot(doc)
        assert len(doc.roots) == 1
        assert "403" in _divs(doc) and "DASH_SERVE_TOKEN" in _divs(doc)

    def test_the_gate_runs_before_the_limiter(self, ns):
        real = ns["_SESSION_LIMITER"]
        calls = []

        class _Spy:
            def is_allowed(self, ip):
                calls.append(ip)
                return real.is_allowed(ip)
        ns["_SESSION_LIMITER"] = _Spy()
        _session(ns, _SessionDoc(_req({})))
        assert calls == []
        doc = _session(ns, _SessionDoc(_req(token_args())))
        assert len(calls) == 1 and _has_plot(doc)

    def test_no_configured_token_makes_one_and_still_refuses(
            self, ns, _isolated, capsys):
        ns["_DASH_SERVE_TOKEN"] = None
        doc = _session(ns, _ServedDoc(_req({})))
        assert _refused(doc)
        key = sys.modules["_dash_serve_key"].key
        assert dr._dash_token_valid(key) and len(key) == 43
        dirs = _link_dirs(_isolated)
        assert len(dirs) == 1
        p = os.path.join(_isolated, dirs[0], "link.html")
        assert _mode(p) == "600" and _mode(os.path.dirname(p)) == "700"
        with open(p, encoding="utf-8") as fh:
            assert "http://127.0.0.1:5123/app?token=" + key in fh.read()
        said = capsys.readouterr().out
        assert p in said and key not in said and "?token=" not in said
        assert _refused(_session(ns, _ServedDoc(_req(token_args()))))
        assert _refused(_session(ns, _ServedDoc(_req({}))))
        assert len(_link_dirs(_isolated)) == 1
        assert _has_plot(_session(ns, _ServedDoc(_req(token_args(key)))))

    def test_a_context_without_a_request_is_refused(self, ns):
        class _NoReq(_SessionDoc):
            @property
            def session_context(self):
                return types.SimpleNamespace(request=None)
        assert _refused(_session(ns, _NoReq(None)))

    def test_an_in_process_document_still_builds(self, ns):
        from bokeh.document import Document
        assert _has_plot(_session(ns, Document()))

    def test_bytes_and_str_values_both_match(self, ns):
        assert _has_plot(_session(ns, _SessionDoc(_req({"token": [T]}))))
        assert _has_plot(_session(ns, _SessionDoc(_req(token_args()))))

    def test_the_refusal_names_no_request_data(self, ns):
        doc = _session(ns, _SessionDoc(_req(
            {"token": ["<script>x</script>"]},
            **{"X-Forwarded-For": "MARKER-7731"})))
        text = _divs(doc)
        assert _refused(doc)
        assert "<script" not in text and "MARKER-7731" not in text

    def test_a_refused_session_keeps_the_policy(self, ns):
        doc = _session(ns, _SessionDoc(_req({})))
        assert _refused(doc)
        from test_csp import _page_for
        assert doc.template is not None
        assert "Content-Security-Policy" in _page_for(doc)

    def test_the_env_token_is_the_gate_under_bokeh_serve(
            self, app_src, tmp_path, monkeypatch):
        from bokeh.application.handlers.code import CodeHandler
        handler = CodeHandler(source=app_src,
                              filename=str(tmp_path / "app_bs.py"))

        def run(args):
            doc = _SessionDoc(_req(args))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                handler.modify_document(doc)
            return doc
        monkeypatch.setenv("DASH_SERVE_TOKEN", TEST_TOKEN)
        assert _has_plot(run(token_args()))
        assert "_dash_serve_key" not in sys.modules
        monkeypatch.delenv("DASH_SERVE_TOKEN")
        drop_holder()
        assert _refused(run(token_args()))
        assert dr._dash_token_valid(sys.modules["_dash_serve_key"].key)


# ===========================================================================
# The generated app: Gate A, the self-made key, __main__
# ===========================================================================
def _run_main(src, argv, monkeypatch, seen):
    """Run the app's ``__main__`` with Bokeh's Server replaced by a recorder
    and its loop by a fake that records ``call_later``."""
    import bokeh.server.server as bss

    class _Loop:
        def add_callback(self, fn, *a):
            seen.setdefault("callbacks", []).append(
                getattr(fn, "__name__", ""))

        def call_later(self, delay, fn, *a):
            seen.setdefault("later", []).append((delay, fn) + a)

        def start(self):
            seen["loop_started"] = True

        def stop(self):
            pass

    class _Server:
        def __init__(self, apps, **kw):
            seen["kw"] = kw
            self.io_loop = _Loop()

        def start(self):
            seen["started"] = True

        def show(self, *a):
            seen["show"] = True

        def stop(self):
            seen["stopped"] = True

    monkeypatch.setattr(bss, "Server", _Server)
    monkeypatch.setattr(sys, "argv", argv)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(src, "app.py", "exec"), {"__name__": "__main__"})


def _main_text(src):
    i = src.index("if __name__ == '__main__':")
    out = []
    for ln in src[i:].split("\n"):
        s = ln.strip()
        if s.startswith("#"):
            continue
        out.append(ln)
    return "\n".join(out)


class TestTheGeneratedAppIsGated:

    def test_every_server_the_app_builds_has_the_token_provider(
            self, app_src, _isolated, capsys, monkeypatch):
        ns = _ns(app_src)
        _RecServer.made = []
        ns["Server"] = _RecServer
        ns["_DASH_SERVE_TOKEN"] = None
        capsys.readouterr()
        ns["_dash_server_app"](token=T)
        prov = _RecServer.made[-1].kw["auth_provider"]
        # WP-30 P1.31a: Gate A inside the open-session cap's provider.
        assert type(prov).__name__ == "_DashCapAuth"
        assert ns["_DASH_SERVE_TOKEN"] == T
        assert _lines(capsys.readouterr().out) == []
        assert ns["_DASH_LINK_DIR"] is None
        ns["_DASH_SERVE_TOKEN"] = None
        ns["_dash_server_app"]()
        key = ns["_DASH_SERVE_TOKEN"]
        assert dr._dash_token_valid(key) and len(key) == 43 and key != T
        prov = _RecServer.made[-1].kw["auth_provider"]
        # WP-30 P1.31a: Gate A inside the open-session cap's provider.
        assert type(prov).__name__ == "_DashCapAuth"
        assert _admits(prov, key) and not _admits(prov, T)
        d = ns["_DASH_LINK_DIR"]
        p = os.path.join(d, "link.html")
        assert os.path.basename(d).startswith("dash-link-")
        assert _mode(d) == "700" and _mode(p) == "600"
        with open(p, encoding="utf-8") as fh:
            assert ("http://127.0.0.1:%d/?token=%s" % (ns["_port"], key)) \
                in fh.read()
        out = _lines(capsys.readouterr().out)
        assert out == [dr._DASH_LINK_SAID, p]

    def test_a_key_whose_link_cannot_be_written_is_printed_once_and_served(
            self, app_src, _isolated, capsys):
        ns = _ns(app_src)

        def _raise(*a, **k):
            raise PermissionError(13, "Permission denied")
        ns["_dash_private_page"] = _raise
        _RecServer.made = []
        ns["Server"] = _RecServer
        ns["_DASH_SERVE_TOKEN"] = None
        capsys.readouterr()
        srv = ns["_dash_server_app"]()
        assert srv is _RecServer.made[-1] and srv.stopped == 0
        assert ns["_DASH_LINK_DIR"] is None
        key = ns["_DASH_SERVE_TOKEN"]
        assert _lines(capsys.readouterr().out) == [
            dr._DASH_LINK_UNWRITTEN % "PermissionError",
            "http://127.0.0.1:%d/?token=%s" % (ns["_port"], key)]
        assert _admits(srv.kw["auth_provider"], key)
        ns["_dash_server_app"]()
        assert _lines(capsys.readouterr().out) == []
        assert _refused(_session(ns, _SessionDoc(_req({}))))
        assert _lines(capsys.readouterr().out) == []

    def test_an_address_no_link_can_name_stops_the_server(
            self, app_src, _isolated, capsys):
        ns = _ns(app_src)
        _RecServer.made = []
        ns["Server"] = _RecServer
        ns["_DASH_SERVE_TOKEN"] = None
        with pytest.raises(RuntimeError) as e:
            ns["_dash_server_app"](address="fe80::1%en0")
        msg = str(e.value)
        assert "DASH_SERVE_TOKEN" in msg and "fe80::1%en0" in msg
        assert ns["_DASH_SERVE_TOKEN"] not in msg
        assert _RecServer.made[-1].stopped == 1

    def test_an_invalid_token_argument_is_refused(self, app_src):
        ns = _ns(app_src)
        _RecServer.made = []
        ns["Server"] = _RecServer
        with pytest.raises(ValueError) as e:
            ns["_dash_server_app"](token="weak!value")
        assert "weak!value" not in str(e.value)
        assert _RecServer.made == []

    def test_the_app_source_holds_no_key(self, app_src):
        tree = ast.parse(app_src)
        skip = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id in ("_SPEC_B64",
                                                         "_DATA_B64")
                    for t in node.targets):
                for sub in ast.walk(node.value):
                    skip.add(id(sub))
        hits = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in skip
                and re.fullmatch(r"[A-Za-z0-9_-]{32,128}", n.value)]
        # The one such constant at the base is the function parser's
        # name alphabet (WP-29 P0.6, _stata_fn_parse's namech): every name
        # character once, in order -- no key.
        alphabet = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
                    "0123456789")
        assert [h for h in hits if h != alphabet] == []
        assert "\n_DASH_SERVE_TOKEN = None\n" in app_src

    def test_the_launcher_resolves_the_token_before_it_serves(self, app_src):
        m = _main_text(app_src)
        assert m.index("_dash_resolve_token(") < m.index("_dash_server_app(")
        assert m.index("_dash_install_access_log_redaction()") < \
            m.index("_server.start()")
        assert "_server.show" not in m
        assert "print(_dash_url" not in m and "_dash_tok_made" not in m
        assert "_DASH_LINK_DIR" in m[m.index("finally:"):]

    def test_show_opens_the_tokenized_loopback_link(
            self, app_src, _isolated, monkeypatch, capsys):
        import webbrowser
        monkeypatch.setenv("BROWSER", "x")
        opened = []

        def rec(uri, *a, **k):
            path = urllib.request.url2pathname(uri[len("file://"):])
            with open(path, encoding="utf-8") as fh:
                opened.append((path, fh.read()))
            return True
        monkeypatch.setattr(webbrowser, "open", rec)
        seen = {}
        _run_main(app_src, ["app.py", "--show"], monkeypatch, seen)
        assert len(opened) == 1
        path, text = opened[0]
        m = re.search(r"http://127\.0\.0\.1:(\d+)/\?token=([A-Za-z0-9_-]+)",
                      text)
        assert m and len(m.group(2)) == 43
        d = os.path.dirname(path)
        assert (dr._DASH_REDIRECT_TTL_S, shutil.rmtree, d, True) in \
            seen.get("later", [])
        assert not os.path.exists(d)
        assert "show" not in seen
        assert type(seen["kw"]["auth_provider"]).__name__ == "_DashCapAuth"

    def test_the_app_prints_its_link_files_path_never_the_key(
            self, app_src, _isolated, monkeypatch, capsys):
        seen = {}
        capsys.readouterr()
        _run_main(app_src, ["app.py"], monkeypatch, seen)
        out = capsys.readouterr().out
        p = link_path_in(out)
        assert p and p.endswith("link.html")
        assert not os.path.exists(p), "the link folder outlived the app"
        assert "?token=" not in out
        assert not re.search(r"[A-Za-z0-9_-]{43}", out.replace(p, ""))
        assert "Bokeh Server running at http://127.0.0.1:" in out
        assert "localhost" not in out
        monkeypatch.setenv("DASH_SERVE_TOKEN", TEST_TOKEN)
        seen = {}
        _run_main(app_src, ["app.py"], monkeypatch, seen)
        out = capsys.readouterr().out
        assert link_path_in(out) is None
        assert _link_dirs(_isolated) == []
        assert TEST_TOKEN not in out and "?token=" not in out
        assert "Bokeh Server running at http://127.0.0.1:" in out
        assert "localhost" not in out

    def test_the_app_records_its_link_while_it_serves(
            self, app_src, _isolated, monkeypatch, capsys):
        """The link file exists while the loop runs (the read_link check of
        test_the_app_prints_its_link_files_path_never_the_key's file)."""
        import bokeh.server.server as bss
        seen = {}
        orig = None

        def start_loop():
            p = link_path_in(capsys.readouterr().out)
            seen["during"] = read_link(p)

        class _Loop:
            def add_callback(self, fn, *a):
                pass

            def call_later(self, *a):
                pass

            def start(self):
                start_loop()

            def stop(self):
                pass

        class _Server:
            def __init__(self, apps, **kw):
                self.io_loop = _Loop()
                self.kw = kw

            def start(self):
                pass

            def stop(self):
                pass
        monkeypatch.setattr(bss, "Server", _Server)
        monkeypatch.setattr(sys, "argv", ["app.py", "--port", "5123"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(app_src, "app.py", "exec"), {"__name__": "__main__"})
        mode, dmode, host, port, path, key = seen["during"]
        assert (mode, dmode, host, port, path) == ("600", "700", "127.0.0.1",
                                                  5123, "/")
        assert len(key) == 43
        del orig


# ===========================================================================
# The app's own resolution of a supplied key
# ===========================================================================
class TestTheAppResolvesItsToken:

    @pytest.fixture
    def ns(self, app_src):
        return _ns(app_src)

    def _args(self, flag):
        return types.SimpleNamespace(token_stdin=flag)

    def _fd(self, data):
        r, w = os.pipe()
        os.write(w, data)
        os.close(w)
        return r

    def test_precedence_stdin_then_env_else_none(self, ns):
        t1, t2 = "a" * 40, "b" * 40
        env = {"DASH_SERVE_TOKEN": t2}
        fd = self._fd((t1 + "\n").encode())
        assert ns["_dash_resolve_token"](self._args(True), fd=fd,
                                         environ=env) == t1
        os.close(fd)
        assert "DASH_SERVE_TOKEN" not in env
        env = {"DASH_SERVE_TOKEN": t2}
        assert ns["_dash_resolve_token"](self._args(False),
                                         environ=env) == t2
        assert "DASH_SERVE_TOKEN" not in env
        env = {}
        assert ns["_dash_resolve_token"](self._args(False),
                                         environ=env) is None

    def test_a_weak_env_token_is_refused_without_echo(self, ns):
        env = {"DASH_SERVE_TOKEN": "weak!value"}
        with pytest.raises(ValueError) as e:
            ns["_dash_resolve_token"](self._args(False), environ=env)
        assert "DASH_SERVE_TOKEN" in str(e.value)
        assert "weak!value" not in str(e.value)
        assert "DASH_SERVE_TOKEN" not in env

    def test_a_bad_stdin_line_is_refused(self, ns):
        for data in (b"a" * 300 + b"\n", b"\n", "é" .encode() * 40 +
                     b"\n"):
            fd = self._fd(data)
            with pytest.raises(ValueError):
                ns["_dash_resolve_token"](self._args(True), fd=fd,
                                          environ={})
            os.close(fd)

    @pytest.mark.serve
    def test_a_weak_env_token_stops_the_app(self, live_app_path):
        env = {k: v for k, v in os.environ.items()}
        env["DASH_SERVE_TOKEN"] = "weak!value"
        r = subprocess.run(_app_cmd(live_app_path, _free_port()), env=env,
                           capture_output=True, text=True, timeout=120,
                           stdin=subprocess.DEVNULL)
        assert r.returncode == 2
        assert "DASH_SERVE_TOKEN" in r.stderr
        assert "weak!value" not in r.stderr + r.stdout


# ===========================================================================
# The launcher hands the key over
# ===========================================================================
class _HealthStub:
    """A local /health that answers *code* on every probe."""

    def __init__(self, code=200):
        import http.server
        self.code = code
        stub = self

        class _H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(stub.code)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *a):
                pass
        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), _H)
        self.port = self.httpd.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def _fake_child_class(state, passes=5, stdout="", stderr="", rc=0,
                      stdin=None, link=None):
    """A fake Popen: its stdin a FakeStdin, its poll answering None for
    *passes* calls after the launcher printed its ready line, then *rc*;
    each poll records whether and with what mode *link* existed."""

    class _Child:
        def __init__(self, cmd, **kw):
            state["cmd"] = list(cmd)
            state["kw"] = kw
            state["proc"] = self
            self.stdin = stdin if stdin is not None else FakeStdin()
            self.stdout = io.StringIO(stdout)
            self.stderr = io.StringIO(stderr)
            self.returncode = None
            self.polls_after = 0
            self.pid = 1

        def poll(self):
            if self.returncode is not None:
                return self.returncode
            if getattr(self.stdin, "closed", False):
                # The parent watch: end of file on stdin stops the app.
                self.returncode = 0
                return self.returncode
            if link is not None and os.path.exists(link()):
                state.setdefault("link_seen", (
                    _mode(link()), open(link(), encoding="utf-8").read()))
            if state.get("ready_seen") or (state.get("out") and
                                           "the server answers at" in
                                           state["out"]()):
                state["ready_seen"] = True
                self.polls_after += 1
                if self.polls_after > passes:
                    self.returncode = rc
                    state["exited"] = True
            return self.returncode

        def wait(self, timeout=None):
            t0 = time.monotonic()
            while self.poll() is None:
                if timeout is not None and time.monotonic() - t0 > timeout:
                    raise subprocess.TimeoutExpired("fake", timeout)
                time.sleep(0.02)
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9
    return _Child


@pytest.fixture
def launch(tmp_path, monkeypatch):
    """The launcher with a fake child: an app file to read and a 0700 run
    folder; returns a runner and the shared state."""
    app = tmp_path / "app.py"
    app.write_text("# a stand-in app\n")
    run_dir = tmp_path / "run"
    run_dir.mkdir(mode=0o700)
    os.chmod(run_dir, 0o700)
    state = {"app": str(app), "run_dir": str(run_dir)}
    stops = []
    real_stop = dr._dash_stop_child

    def _rec_stop(proc, *a, **k):
        stops.append(state.get("exited", False))
        return real_stop(proc, *a, **k)
    monkeypatch.setattr(dr, "_dash_stop_child", _rec_stop)
    state["stops"] = stops
    return state


def _launch(state, monkeypatch, capsys, port, link_dir="run", **child):
    buf = io.StringIO()
    state["out"] = buf.getvalue
    ld = state["run_dir"] if link_dir == "run" else link_dir
    if "link" not in child and ld is not None:
        child["link"] = lambda: os.path.join(ld, "link.html")
    monkeypatch.setattr(subprocess, "Popen", _fake_child_class(state,
                                                               **child))
    with contextlib.redirect_stdout(buf):
        try:
            dr._dash_launch_app(state["app"], port, 0, True, prebind=False,
                                ready_seconds=10, link_dir=ld)
        finally:
            state["said"] = buf.getvalue()
    return state["said"]


class TestTheLauncherPassesTheToken:

    def test_the_token_goes_to_stdin_not_argv(self, launch, monkeypatch,
                                              capsys):
        with _HealthStub() as hs:
            _launch(launch, monkeypatch, capsys, hs.port)
        cmd = launch["cmd"]
        assert "--token-stdin" in cmd
        assert cmd.index("--token-stdin") > cmd.index(launch["app"])
        proc = launch["proc"]
        key = proc.stdin.key_line()
        assert dr._dash_token_valid(key)
        assert not any(key in c or _KEY43.fullmatch(c) for c in cmd)
        assert launch["kw"]["stdin"] is subprocess.PIPE
        with open(launch["app"], "rb") as fh:
            frame = dr._dash_app_frame(fh.read())
        assert proc.stdin.writes[:-1] == [frame]
        assert proc.stdin.writes[-1] == (key + "\n").encode("ascii")
        assert not any(key.encode() in w for w in proc.stdin.writes[:-1])
        assert launch.get("closed_before_exit") is None
        assert launch["exited"]

    def test_the_pipe_stays_open_while_the_child_serves(self, launch,
                                                        monkeypatch, capsys):
        seen = []
        orig = _fake_child_class

        def cls(state, **kw):
            C = orig(state, **kw)

            class _C(C):
                def poll(self):
                    if self.returncode is None:
                        seen.append(self.stdin.closed)
                    return C.poll(self)
            return _C
        with _HealthStub() as hs:
            buf = io.StringIO()
            launch["out"] = buf.getvalue
            monkeypatch.setattr(subprocess, "Popen", cls(launch))
            with contextlib.redirect_stdout(buf):
                dr._dash_launch_app(launch["app"], hs.port, 0, True,
                                    prebind=False, ready_seconds=10,
                                    link_dir=launch["run_dir"])
        assert seen and not any(seen)

    def test_the_ready_line_and_the_link_file(self, launch, monkeypatch,
                                              capsys):
        with _HealthStub() as hs:
            said = _launch(launch, monkeypatch, capsys, hs.port)
            port = hs.port
        key = launch["proc"].stdin.key_line()
        lines = said.splitlines()
        p = os.path.join(launch["run_dir"], "link.html")
        i = [j for j, ln in enumerate(lines)
             if ln.startswith("dash: the server answers at "
                              "http://127.0.0.1:%d/" % port)]
        assert len(i) == 1
        assert lines[i[0] + 1] == dr._DASH_LINK_SAID
        assert lines[i[0] + 2] == p
        mode, text = launch["link_seen"]
        assert mode == "600"
        assert "http://127.0.0.1:%d/?token=%s" % (port, key) in text
        assert not os.path.exists(p)
        assert key not in said

    def test_without_a_run_folder_the_link_goes_to_a_private_temp_folder(
            self, launch, monkeypatch, capsys, _isolated):
        holder = {}

        def link():
            p = link_path_in(launch["out"]())
            if p:
                holder["p"] = p
                holder.setdefault("dmode", _mode(os.path.dirname(p)))
            return p or "/nonexistent/link.html"
        with _HealthStub() as hs:
            _launch(launch, monkeypatch, capsys, hs.port, link_dir=None,
                    link=link)
        p = holder["p"]
        assert os.path.dirname(os.path.dirname(p)) == _isolated
        assert holder["dmode"] == "700"
        assert not os.path.exists(os.path.dirname(p))

    def test_a_429_from_health_still_counts_as_answering(
            self, launch, monkeypatch, capsys):
        with _HealthStub(429) as hs:
            said = _launch(launch, monkeypatch, capsys, hs.port)
        assert "dash: the server answers at http://127.0.0.1:%d/" % hs.port \
            in said
        assert dr._DASH_LINK_SAID in said

    def test_a_404_from_health_is_not_answering(self, launch, monkeypatch,
                                                capsys):
        state = launch
        with _HealthStub(404) as hs:
            buf = io.StringIO()
            state["out"] = buf.getvalue
            C = _fake_child_class(state)

            class _C(C):
                n = 0

                def poll(self):
                    _C.n += 1
                    if _C.n > 8:
                        self.returncode = 0
                    return self.returncode
            monkeypatch.setattr(subprocess, "Popen", _C)
            with contextlib.redirect_stdout(buf):
                dr._dash_launch_app(state["app"], hs.port, 0, True,
                                    prebind=False, ready_seconds=10,
                                    link_dir=state["run_dir"])
        assert "the server answers at" not in buf.getvalue()

    def test_the_stderr_tail_and_forwarded_lines_are_redacted(
            self, launch, monkeypatch, capsys):
        """The fake child learns the key from its stdin, prints it in an
        access-log line and bare, and exits 3 with it in stderr."""
        state = launch
        state["out"] = lambda: ""
        C = _fake_child_class(state, rc=3)

        class _C(C):
            def __init__(self, cmd, **kw):
                super().__init__(cmd, **kw)
                self.stdout = _LateStream(self)
                self.stderr = _LateStream(self)

            def poll(self):
                key = self.stdin.key_line()
                if key and self.returncode is None:
                    self.stdout.feed("GET /?token=%s&x=1 (127.0.0.1)\n%s\n"
                                     % (key, key))
                    self.stderr.feed("boom " + key + "\n")
                    time.sleep(0.3)
                    self.returncode = 3
                return self.returncode
        monkeypatch.setattr(subprocess, "Popen", _C)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with pytest.raises(RuntimeError) as e:
                dr._dash_launch_app(state["app"], _free_port(), 0, True,
                                    prebind=False, ready_seconds=10,
                                    link_dir=state["run_dir"])
        key = state["proc"].stdin.key_line()
        assert key
        assert key not in str(e.value) and key not in buf.getvalue()
        assert "<query redacted>" in buf.getvalue()
        assert "boom" in str(e.value)

    def test_a_child_that_cannot_take_the_key_is_stopped(
            self, launch, monkeypatch, capsys):
        state = launch
        state["out"] = lambda: ""
        monkeypatch.setattr(subprocess, "Popen", _fake_child_class(
            state, stdin=FakeStdin(break_after=1)))
        with pytest.raises(RuntimeError) as e:
            dr._dash_launch_app(state["app"], _free_port(), 0, True,
                                prebind=False, ready_seconds=10,
                                link_dir=state["run_dir"])
        assert "key" in str(e.value)
        assert state["stops"], "the child was not stopped"

    def test_a_run_folder_that_refuses_the_link_moves_it_to_a_private_folder(
            self, tmp_path, monkeypatch, capsys):
        sysdir = tmp_path / "sys"
        sysdir.mkdir()
        monkeypatch.setattr(tempfile, "tempdir", str(sysdir))
        run_dir = tmp_path / "run"
        run_dir.mkdir(mode=0o700)
        url = "http://127.0.0.1:5006/?token=" + T
        for exc in (dr._DashUnsafePath("x"),
                    OSError(errno.EACCES, "Permission denied")):
            def _raise(*a, **k):
                raise exc
            monkeypatch.setattr(dr, "_dash_private_write", _raise)
            capsys.readouterr()
            p, d = dr._dash_write_link(str(run_dir), url)
            assert os.path.dirname(p) == d
            assert os.path.dirname(d) == str(sysdir)
            assert os.path.basename(d).startswith("dash-link-")
            assert os.path.basename(p) == "link.html"
            assert _mode(p) == "600" and _mode(d) == "700"
            with open(p, encoding="utf-8") as fh:
                assert fh.read() == dr._dash_redirect_page(url)
            assert capsys.readouterr().out == ""
            shutil.rmtree(d)

        def _nospace(*a, **k):
            raise OSError(errno.ENOSPC, "No space left on device")
        monkeypatch.setattr(dr, "_dash_private_page", _nospace)
        with pytest.raises(OSError) as e:
            dr._dash_write_link(str(run_dir), url)
        assert e.value.errno == errno.ENOSPC
        assert capsys.readouterr().out == ""

    def test_a_link_file_that_cannot_be_private_moves_to_a_private_folder(
            self, tmp_path, monkeypatch, capsys):
        sysdir = tmp_path / "sys"
        sysdir.mkdir()
        monkeypatch.setattr(tempfile, "tempdir", str(sysdir))
        run_dir = tmp_path / "run"
        run_dir.mkdir(mode=0o700)
        url = "http://127.0.0.1:5006/?token=" + T
        p, d = dr._dash_write_link(str(run_dir), url)
        assert p == str(run_dir / "link.html") and d is None
        os.unlink(p)
        target = str(run_dir / "link.html")
        real = os.lstat

        def lstat(path, *a, **k):
            st = real(path, *a, **k)
            if os.fspath(path) == target:
                return os.stat_result((0o100644,) + tuple(st)[1:])
            return st
        monkeypatch.setattr(os, "lstat", lstat)
        capsys.readouterr()
        p, d = dr._dash_write_link(str(run_dir), url)
        assert os.path.dirname(d) == str(sysdir) and d is not None
        assert p == os.path.join(d, "link.html")
        assert _mode(p) == "600" and _mode(d) == "700"
        assert not os.path.exists(target)
        got = capsys.readouterr()
        assert "note:" not in got.out + got.err

    def test_a_link_no_folder_can_keep_private_is_written_with_a_note(
            self, tmp_path, monkeypatch, capsys):
        sysdir = tmp_path / "sys"
        sysdir.mkdir()
        monkeypatch.setattr(tempfile, "tempdir", str(sysdir))
        run_dir = tmp_path / "run"
        run_dir.mkdir(mode=0o700)
        url = "http://127.0.0.1:5006/?token=" + T
        target = str(run_dir / "link.html")
        real_l, real_f = os.lstat, os.fstat

        def lstat(path, *a, **k):
            st = real_l(path, *a, **k)
            if os.fspath(path) == target:
                return os.stat_result((0o100644,) + tuple(st)[1:])
            return st

        def fstat(fd):
            st = real_f(fd)
            return os.stat_result((st.st_mode | 0o044,) + tuple(st)[1:])
        monkeypatch.setattr(os, "lstat", lstat)
        monkeypatch.setattr(os, "fstat", fstat)
        monkeypatch.setattr(os, "fchmod", lambda fd, m: None, raising=False)
        capsys.readouterr()
        p, d = dr._dash_write_link(str(run_dir), url)
        assert os.path.dirname(d) == str(sysdir)
        assert p == os.path.join(d, "link.html")
        with open(p, encoding="utf-8") as fh:
            assert fh.read() == dr._dash_redirect_page(url)
        assert not os.path.exists(target)
        # Flipped (WP-30 P1.26b): one note in twoway's form on stderr
        # (_dash_emit_note), where it was a "dash: note: " stdout line.
        lines = capsys.readouterr().err.splitlines()
        assert len(lines) == 1 and lines[0].startswith("(note:  dash: ")
        assert p in lines[0] and T not in lines[0] and \
            "?token=" not in lines[0]

    def test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served(
            self, launch, monkeypatch, capsys, _isolated):
        def _unsafe(*a, **k):
            raise dr._DashUnsafePath("x")

        def _nospace(*a, **k):
            raise OSError(errno.ENOSPC, "No space left on device")

        def child_out(state):
            C = _fake_child_class(state, passes=5)

            class _C(C):
                def __init__(self, cmd, **kw):
                    super().__init__(cmd, **kw)
                    self.stdout = _LateStream(self)

                def poll(self):
                    key = self.stdin.key_line()
                    if key and not getattr(self, "_said", False):
                        self._said = True
                        self.stdout.feed("GET /?token=%s (127.0.0.1)\n" % key)
                    return C.poll(self)
            return _C

        for patch_write in (True, False):
            st = dict(launch)
            st.pop("exited", None)
            st.pop("ready_seen", None)
            st["stops"] = launch["stops"]
            del st["stops"][:]
            monkeypatch.setattr(dr, "_dash_private_page", _nospace)
            if patch_write:
                monkeypatch.setattr(dr, "_dash_private_write", _unsafe)
            else:
                monkeypatch.undo()
                monkeypatch.setattr(tempfile, "tempdir", _isolated)
                monkeypatch.setattr(dr, "_dash_private_page", _nospace)
                real_l = os.lstat
                target = os.path.join(st["run_dir"], "link.html")

                def lstat(path, *a, **k):
                    s = real_l(path, *a, **k)
                    if os.fspath(path) == target:
                        return os.stat_result((0o100644,) + tuple(s)[1:])
                    return s
                monkeypatch.setattr(os, "lstat", lstat)
                rec = []
                real_stop = dr._dash_stop_child

                def _rec_stop(proc, *a, **k):
                    rec.append(st.get("exited", False))
                    return real_stop(proc, *a, **k)
                monkeypatch.setattr(dr, "_dash_stop_child", _rec_stop)
                st["stops"] = rec
            buf = io.StringIO()
            st["out"] = buf.getvalue
            with _HealthStub() as hs:
                monkeypatch.setattr(subprocess, "Popen", child_out(st))
                with contextlib.redirect_stdout(buf):
                    dr._dash_launch_app(st["app"], hs.port, 0, True,
                                        prebind=False, ready_seconds=10,
                                        link_dir=st["run_dir"])
                port = hs.port
            proc = st["proc"]
            assert proc.polls_after > 5
            assert not [s for s in st["stops"] if not s]
            key = proc.stdin.key_line()
            lines = buf.getvalue().splitlines()
            i = [j for j, ln in enumerate(lines) if ln.startswith(
                "dash: the server answers at http://127.0.0.1:%d/" % port)]
            assert len(i) == 1
            assert lines[i[0] + 1] == dr._DASH_LINK_UNWRITTEN % "OSError"
            assert lines[i[0] + 2] == "http://127.0.0.1:%d/?token=%s" % (
                port, key)
            assert len([ln for ln in lines if key in ln]) == 1
            assert dr._DASH_LINK_SAID not in lines
            assert not os.path.exists(os.path.join(st["run_dir"],
                                                   "link.html"))
            assert _link_dirs(_isolated) == []


class _LateStream:
    """A child's text stream the fake child feeds as it runs; readline
    waits for a line, and ends once the child has exited and nothing is
    left."""

    def __init__(self, proc):
        self.proc = proc
        self.buf = []
        self.lock = threading.Lock()

    def feed(self, text):
        with self.lock:
            self.buf.extend(io.StringIO(text).readlines())

    def readline(self):
        while True:
            with self.lock:
                if self.buf:
                    return self.buf.pop(0)
            if self.proc.returncode is not None:
                return ""
            time.sleep(0.01)

    def close(self):
        pass


# ===========================================================================
# Live: python app.py
# ===========================================================================
@pytest.mark.serve
class TestTheServedAppRequiresItsToken:

    def test_a_session_without_the_token_reads_no_rows(self, live_app_path):
        from bokeh.client import pull_session
        with _keyed_live(live_app_path) as app:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pytest.raises(OSError):
                    with pull_session(url="http://127.0.0.1:%d/"
                                      % app.port) as s:
                        rows = [m for m in s.document.select({})
                                if "mpg" in (getattr(m, "data", {}) or {})]
                        raise AssertionError("served %d sources" % len(rows))

    def test_the_page_without_the_token_is_403(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            st, body, headers, reason = _status(
                "http://127.0.0.1:%d/" % app.port)
            assert st == 403
            assert reason == dr._DASH_TOKEN_REFUSAL

    def test_a_wrong_or_doubled_token_is_403(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            base = "http://127.0.0.1:%d/" % app.port
            for q in ("?token=" + "x" * 43, "?token=" + T[:-1] + "Q",
                      "?token=%s&token=%s" % (T, T)):
                assert _status(base + q)[0] == 403, q

    def test_the_right_token_serves_the_dashboard(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            st, body, _, _ = _status("http://127.0.0.1:%d/?token=%s"
                                     % (app.port, T))
            assert st == 200 and "<title>" in body
            n, _, plot = _pull_rows("http://127.0.0.1:%d/" % app.port, T)
            assert n == 10 and plot

    def test_the_browser_path_opens_the_websocket(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            assert _ws(app.port, "http://127.0.0.1:%d" % app.port) == \
                (101, "ACK")

    def test_a_forged_session_jwt_is_refused(self, live_app_path):
        from bokeh.util.token import generate_jwt_token
        with _keyed_live(live_app_path) as app:
            origin = "http://127.0.0.1:%d" % app.port
            for extra in (None, {"arguments": {"token": ["x" * 43]}}):
                forged = generate_jwt_token("A" * 44, extra_payload=extra)
                assert _ws(app.port, origin, jwt=forged) == (403, None)

    def test_autoload_and_metadata_need_the_token(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            b = "http://127.0.0.1:%d" % app.port
            a = b + "/autoload.js?bokeh-autoload-element=x"
            assert _status(a)[0] == 403
            assert _status(b + "/metadata")[0] == 403
            assert _status(a + "&token=" + T)[0] == 200
            assert _status(b + "/metadata?token=" + T)[0] == 200

    def test_health_and_static_stay_open(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            b = "http://127.0.0.1:%d" % app.port
            assert _status(b + "/health")[0] == 200
            assert _status(b + "/static/js/bokeh.min.js")[0] == 200

    def test_a_refusal_carries_the_headers_and_reflects_nothing(
            self, live_app_path):
        from test_csp import _assert_headers
        with _keyed_live(live_app_path) as app:
            st, body, headers, _ = _status(
                "http://127.0.0.1:%d/?token=%%3Cscript%%3E" % app.port)
            assert st == 403
            _assert_headers(headers, "the 403")
            assert "<script" not in body

    def test_unauthenticated_requests_do_not_spend_the_session_budget(
            self, live_app_path):
        port = _free_port()
        with _Proc(_app_cmd(live_app_path, port, "--sessions-per-client",
                            "1"), env={"DASH_SERVE_TOKEN": T},
                   port=port):
            for _ in range(50):
                assert _status("http://127.0.0.1:%d/" % port)[0] == 403
            n, divs, plot = _pull_rows("http://127.0.0.1:%d/" % port, T)
            assert "429" not in divs and plot and n == 10

    def test_a_keyless_start_makes_a_key_and_a_private_link(
            self, live_app_path):
        port = _free_port()
        with _Proc(_app_cmd(live_app_path, port), port=port) as app:
            p = link_path_in(app.said())
            assert p, app.said()
            mode, dmode, host, lport, path, key = read_link(p)
            assert (mode, dmode, host, lport, path) == (
                "600", "700", "127.0.0.1", port, "/")
            assert len(key) == 43
            b = "http://127.0.0.1:%d/" % port
            assert _status(b)[0] == 403
            assert _status(b + "?token=" + key)[0] == 200
            assert _pull_rows(b, key)[0] == 10
            with pytest.raises(OSError):
                _pull_rows(b, T)
            app.stop()
            assert key not in app.said()
            assert not os.path.exists(os.path.dirname(p))

    def _unwritable(self, live_app_path, show):
        port = _free_port()
        cmd = [sys.executable, "-c", _PATCH_SHOW if show else _PATCH_APP,
               live_app_path, "--port", str(port)] + (["--show"] if show
                                                      else [])
        env = {"BROWSER": "dash-test-no-browser"} if show else {}
        before = set(os.listdir(tempfile.gettempdir()))
        with _Proc(cmd, env=env, port=port) as app:
            warn = dr._DASH_LINK_UNWRITTEN % "PermissionError"
            lines = app.lines
            assert app.wait_for(lambda s: warn in s), app.said()
            i = lines.index(warn)
            m = LINK_RE.fullmatch(lines[i + 1])
            assert m and m.group(1) == "127.0.0.1"
            assert int(m.group(2)) == port and m.group(3) == "/"
            key = m.group(4)
            b = "http://127.0.0.1:%d/" % port
            assert _status(b)[0] == 403
            assert _status(b + "?token=" + key)[0] == 200
            assert _pull_rows(b, key)[0] == 10
            if show:
                opener = ("dash: the browser was not opened: its page could "
                          "not be written (PermissionError); open the "
                          "dashboard's link instead.")
                assert app.wait_for(lambda s: opener in s)
                assert app.said().count(opener) == 1
                time.sleep(5)
                assert app.proc.poll() is None
                assert _status(b + "?token=" + key)[0] == 200
                assert "dash-test: opener called" not in app.said()
            for _ in range(2):
                _status(b + "?token=" + key)
                _status(b)
            _pull_rows(b, key)
            assert len([ln for ln in lines if key in ln]) == 1
            assert lines.count(warn) == 1
            app.stop()
        after = set(os.listdir(tempfile.gettempdir()))
        assert not [p for p in after - before
                    if p.startswith(("dash-link-", "dash-open-"))]

    def test_a_keyless_start_whose_link_cannot_be_written_prints_it_once_and_serves(
            self, live_app_path):
        self._unwritable(live_app_path, show=False)

    def test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves(
            self, live_app_path):
        self._unwritable(live_app_path, show=True)

    def test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving(
            self, tmp_path, monkeypatch):
        from test_serve_lifecycle import _built_app, _kill_listeners
        app = _built_app(tmp_path)
        run_dir = tmp_path / "run"
        run_dir.mkdir(mode=0o700)

        def _unsafe(*a, **k):
            raise dr._DashUnsafePath("x")

        def _nospace(*a, **k):
            raise OSError(errno.ENOSPC, "No space left on device")
        monkeypatch.setattr(dr, "_dash_private_write", _unsafe)
        monkeypatch.setattr(dr, "_dash_private_page", _nospace)
        procs = []
        real_popen = subprocess.Popen

        def popen(*a, **k):
            p = real_popen(*a, **k)
            procs.append(p)
            return p
        monkeypatch.setattr(subprocess, "Popen", popen)
        lock = threading.Lock()
        chunks = []

        class _Buf(io.TextIOBase):
            def write(self, s):
                with lock:
                    chunks.append(s)
                return len(s)

        def said():
            with lock:
                return "".join(chunks)
        port = _free_port()
        err = []

        def run():
            try:
                dr._dash_launch_app(app, port, 2, True, prebind=False,
                                    link_dir=str(run_dir))
            except BaseException as e:   # recorded, asserted below
                err.append(e)
        with contextlib.redirect_stdout(_Buf()):
            th = threading.Thread(target=run, daemon=True)
            th.start()
            try:
                warn = dr._DASH_LINK_UNWRITTEN % "OSError"
                t0 = time.monotonic()
                while warn not in said() and time.monotonic() - t0 < 60:
                    time.sleep(0.1)
                time.sleep(0.5)
                lines = said().splitlines()
                assert warn in lines, said()
                i = lines.index(warn)
                assert lines[i - 1].startswith(
                    "dash: the server answers at http://127.0.0.1:%d/" % port)
                m = LINK_RE.fullmatch(lines[i + 1])
                assert m, lines[i + 1]
                key = m.group(4)
                assert _status(lines[i + 1])[0] == 200
                assert _pull_rows("http://127.0.0.1:%d/" % port, key)[0] > 0
                _pull_rows("http://127.0.0.1:%d/" % port, key)
                time.sleep(0.5)
            finally:
                for p in procs:
                    if p.poll() is None:
                        p.terminate()
                th.join(30)
                _kill_listeners(port)
        assert not err, err
        assert len([ln for ln in said().splitlines() if key in ln]) == 1

    def test_the_token_is_per_launch(self, live_app_path):
        keys = []
        for _ in range(2):
            port = _free_port()
            with _Proc(_app_cmd(live_app_path, port), port=port) as app:
                p = link_path_in(app.said())
                keys.append(read_link(p)[5])
                if len(keys) == 2:
                    assert _status("http://127.0.0.1:%d/?token=%s"
                                   % (port, keys[0]))[0] == 403
        assert keys[0] != keys[1]

    def test_the_access_log_never_carries_the_token(self, live_app_path):
        with _keyed_live(live_app_path) as app:
            b = "http://127.0.0.1:%d/" % app.port
            for q in ("?token=%s&token=%s" % (T, T), "?token=" + T,
                      "?token=" + "w" * 43):
                _status(b + q)
            time.sleep(0.5)
            said = _launcher_said(app)
            assert T not in said
            assert "<query redacted>" in said

    def test_the_link_never_reaches_an_ipv6_squatter(self, live_app_path):
        port = _free_port()
        try:
            sq = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sq.bind(("::1", port))
            sq.listen(5)
        except OSError:
            pytest.skip("this host cannot bind the IPv6 loopback")
        heard = []

        def listen():
            sq.settimeout(0.2)
            while not stop.is_set():
                try:
                    c, _ = sq.accept()
                except OSError:
                    continue
                c.settimeout(1)
                try:
                    heard.append(c.recv(4096))
                except OSError:
                    pass
                c.close()
        stop = threading.Event()
        th = threading.Thread(target=listen, daemon=True)
        th.start()
        try:
            with _Proc(_app_cmd(live_app_path, port), port=port) as app:
                p = link_path_in(app.said())
                mode, dmode, host, lport, path, key = read_link(p)
                assert host == "127.0.0.1"
                with open(p, encoding="utf-8") as fh:
                    url = LINK_RE.search(fh.read()).group(0)
                assert _status(url)[0] == 200
        finally:
            stop.set()
            th.join(5)
            sq.close()
        assert not [h for h in heard if key.encode() in h]

    def test_gate_a_and_gate_b_agree_in_process(self, app_src):
        ns = _ns(app_src)
        port = _free_port()
        box = {}
        ready = threading.Event()

        def serve():
            asyncio.set_event_loop(asyncio.new_event_loop())
            srv = ns["_dash_server_app"](port=port, token=T)
            box["srv"] = srv
            srv.start()
            ready.set()
            srv.io_loop.start()
        th = threading.Thread(target=serve, daemon=True)
        th.start()
        assert ready.wait(30)
        try:
            assert ns["_DASH_SERVE_TOKEN"] == T
            n, _, plot = _pull_rows("http://127.0.0.1:%d/" % port, T)
            assert n == 10 and plot
        finally:
            srv = box["srv"]
            srv.io_loop.add_callback(srv.io_loop.stop)
            th.join(10)
            srv.stop()


# ===========================================================================
# Live: bokeh serve app.py
# ===========================================================================
@pytest.mark.serve
class TestBokehServeAlwaysHasAKey:

    def _start(self, app, env=None, allow_127=True):
        port = _free_port()
        return _Proc(_bs_cmd(app, port, allow_127), env=env, port=port,
                     ready="/static/js/bokeh.min.js",
                     cwd=os.path.dirname(app))

    def test_without_the_env_the_app_makes_a_key_and_announces_it(
            self, bs_app_path):
        with self._start(bs_app_path) as bs:
            u = "http://127.0.0.1:%d/app" % bs.port
            assert _status(u)[0] == 200
            assert bs.wait_for(lambda s: link_path_in(s) is not None), \
                bs.said()
            n, divs, plot = _pull_rows(u)
            assert not plot and "DASH_SERVE_TOKEN" in divs and \
                "link.html" in divs
            hint = dr._DASH_BS_ORIGIN_HINT % bs.port
            assert bs.wait_for(lambda s: hint in s)
            p = link_path_in(bs.said())
            mode, dmode, host, lport, path, key = read_link(p)
            assert (mode, dmode, host, lport, path) == (
                "600", "700", "127.0.0.1", bs.port, "/app")
            assert len(key) == 43
            n, divs, plot = _pull_rows(u, key)
            assert plot and n == 20
            n, divs, plot = _pull_rows(u, T)
            assert not plot
            before = bs.said().count(dr._DASH_LINK_SAID)
            _status(u)
            time.sleep(0.5)
            assert bs.said().count(dr._DASH_LINK_SAID) == before == 1
            bs.stop()
            assert key not in bs.said()
            assert not os.path.exists(os.path.dirname(p))

    def test_a_websocket_first_session_leaves_the_link_to_the_first_page(
            self, bs_app_path):
        with self._start(bs_app_path) as bs:
            u = "http://127.0.0.1:%d/app" % bs.port
            n, divs, plot = _pull_rows(u)
            assert not plot
            time.sleep(0.5)
            assert dr._DASH_LINK_SAID not in bs.said()
            assert _status(u)[0] == 200
            assert bs.wait_for(lambda s: link_path_in(s) is not None)
            assert bs.said().count(dr._DASH_LINK_SAID) == 1
            key = read_link(link_path_in(bs.said()))[5]
            assert _pull_rows(u, key)[2]

    def test_with_the_origin_flag_the_link_opens_the_websocket(
            self, bs_app_path):
        env = {"DASH_SERVE_TOKEN": T}
        for flag, want in ((True, 101), (False, 403)):
            with self._start(bs_app_path, env=env, allow_127=flag) as bs:
                st = _ws(bs.port, "http://127.0.0.1:%d" % bs.port,
                         path="/app")[0]
                assert st == want, (flag, st)

    def test_a_set_but_invalid_env_refuses_every_session(self, bs_app_path):
        with self._start(bs_app_path,
                         env={"DASH_SERVE_TOKEN": "weak!value"}) as bs:
            u = "http://127.0.0.1:%d/app" % bs.port
            for key in (None, "weak!value", T):
                assert not _pull_rows(u, key)[2], key
            said = bs.said()
            assert len([ln for ln in said.splitlines()
                        if "DASH_SERVE_TOKEN" in ln]) == 1
            assert "weak!value" not in said
            assert dr._DASH_LINK_SAID not in said

    def test_with_the_env_the_link_needs_the_token(self, bs_app_path):
        with self._start(bs_app_path, env={"DASH_SERVE_TOKEN": T}) as bs:
            u = "http://127.0.0.1:%d/app" % bs.port
            assert not _pull_rows(u)[2]
            n, _, plot = _pull_rows(u, T)
            assert plot and n == 20
            assert _status(u)[0] == 200
            time.sleep(0.5)
            assert dr._DASH_LINK_SAID not in bs.said()

    def test_an_unwritable_link_is_printed_once_per_app_path(
            self, bs_app_path):
        port = _free_port()
        cmd = [sys.executable, "-c", _PATCH_BS, bs_app_path, "--port",
               str(port), "--allow-websocket-origin", "127.0.0.1:%d" % port]
        with _Proc(cmd, port=port, ready="/static/js/bokeh.min.js",
                   cwd=os.path.dirname(bs_app_path)) as bs:
            u = "http://127.0.0.1:%d/app" % port
            assert _status(u)[0] == 200
            warn = dr._DASH_LINK_UNWRITTEN % "PermissionError"
            assert bs.wait_for(lambda s: warn in s), bs.said()
            hint = dr._DASH_BS_ORIGIN_HINT % port
            assert bs.wait_for(lambda s: hint in s)
            lines = list(bs.lines)
            i = lines.index(warn)
            m = LINK_RE.fullmatch(lines[i + 1])
            assert m and m.group(3) == "/app" and int(m.group(2)) == port
            assert lines[i + 2] == hint
            key = m.group(4)
            n, _, plot = _pull_rows(u, key)
            assert plot and n == 20
            for _ in range(3):
                _status(u)
            _status(u + "?token=" + key)
            time.sleep(0.5)
            assert len([ln for ln in bs.lines if key in ln]) == 1
            assert bs.lines.count(warn) == 1
