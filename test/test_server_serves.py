"""test_server_serves.py — the app must work under ``bokeh serve``.

Every one of the ~450 existing server tests calls ``make_document`` directly.
None of them starts a server. So nothing noticed that the documented workflow
produces **nothing at all**.

Measured, before the fix, on a generated app served with
``bokeh serve app.py``:

    docs_json      {}          (literally empty)
    roots          0
    page title     absent
    /health        404

The cause is one line of structure. The generated file binds ``make_document``
to a ``Server`` and registers ``/health`` only inside::

    if __name__ == '__main__':

and never calls ``curdoc()`` — zero occurrences in the whole file. Bokeh's
``CodeRunner`` executes an app script under a synthetic module name
(``bokeh_app_<uuid>``), so that guard is **always false** and nothing ever
attaches the document. ``python app.py`` works, and no documented workflow
uses it: ``dash serve`` runs ``bokeh serve``, ``dash.ado`` tells the user to
run ``bokeh serve``, and ``dash.sthlp`` documents ``bokeh serve``.

These tests start a real server. They are slow, so they are marked
``serve`` — deselect with ``-m 'not serve'`` — but they are the only tests in
the suite that exercise the path a user takes.

No browser is ever opened: ``bokeh serve`` is run without ``--show`` and the
pages are fetched with ``urllib``.
"""
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from dash_render import ServerAppBuilder

from conftest import make_spec, make_data_json

pytestmark = pytest.mark.serve


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _build_app(tmpdir, *, title="Served Dashboard", filters=None, kpis=None,
               plots=None):
    df = pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 20),
        "weight": np.linspace(1760.0, 4840.0, 20),
        "foreign": np.array([0.0, 1.0] * 10),
    })
    spec = make_spec(plots or [{"type": "scatter", "yvar": "mpg",
                                "xvar": "weight", "options": {}}])
    spec["build_options"]["title"] = title
    if filters:
        spec["build_options"]["filters"] = filters
    if kpis:
        spec["kpis"] = kpis
        spec["build_options"]["registry"] = "k1 g1"
    sp = os.path.join(tmpdir, "spec.json")
    dp = os.path.join(tmpdir, "data.json")
    op = os.path.join(tmpdir, "app.py")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    ServerAppBuilder(sp, dp).build(op)
    return op


class _Served:
    """A running ``bokeh serve``, torn down on exit.

    Never passes ``--show``: starting a browser window per test would take
    over the user's desktop, which is exactly what the standalone path's
    ``nobrowser`` option exists to prevent.
    """

    def __init__(self, app_path, extra_args=()):
        self.port = _free_port()
        self.app = app_path
        self.proc = None
        self.extra = list(extra_args)

    def __enter__(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "bokeh", "serve", self.app,
             "--port", str(self.port),
             "--allow-websocket-origin", f"localhost:{self.port}"]
            + self.extra,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            cwd=os.path.dirname(self.app) or ".")
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise AssertionError(
                    f"bokeh serve exited early:\n{out[:3000]}")
            try:
                self.get("/app")
                return self
            except Exception:
                time.sleep(0.4)
        raise AssertionError("bokeh serve never answered")

    def __exit__(self, *exc):
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except Exception:
                self.proc.kill()
        return False

    def url(self, path):
        return f"http://localhost:{self.port}{path}"

    def get(self, path, timeout=10):
        with urllib.request.urlopen(self.url(path), timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")

    def status(self, path):
        try:
            return self.get(path)[0]
        except urllib.error.HTTPError as e:
            return e.code


class _Launched:
    """The generated app running ITSELF, which is how /health exists.

    ``bokeh serve`` owns its Tornado application and gives an app script no
    supported way to register a route, so a health endpoint cannot exist on
    that path.  The app builds its own ``Server`` with ``extra_patterns``,
    and that is the launcher ``dash serve`` uses.

    ``--show`` is never passed, so no browser opens.
    """

    def __init__(self, app_path, extra_args=()):
        self.port = _free_port()
        self.app = app_path
        self.proc = None
        self.extra = list(extra_args)

    def __enter__(self):
        self.proc = subprocess.Popen(
            [sys.executable, self.app, "--port", str(self.port)] + self.extra,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            cwd=os.path.dirname(self.app) or ".")
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise AssertionError(f"the app exited early:\n{out[:3000]}")
            try:
                self.get("/")
                return self
            except urllib.error.HTTPError:
                return self
            except Exception:
                time.sleep(0.4)
        raise AssertionError("the app never answered")

    __exit__ = _Served.__exit__
    url = _Served.url
    get = _Served.get
    status = _Served.status

    def get_from(self, host, path, timeout=10):
        u = f"http://{host}:{self.port}{path}"
        with urllib.request.urlopen(u, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")


def _pull(srv):
    """The document a browser would actually receive.

    Under ``bokeh serve`` the initial HTML deliberately carries an EMPTY
    ``docs_json``; the document is delivered over the WebSocket once the page
    connects. So "docs_json is {}" in the HTML is normal Bokeh behaviour and
    cannot distinguish a working app from one that attaches nothing —
    measured: it is ``{}`` either way. ``pull_session`` opens the same session
    a browser would and returns the real document.
    """
    from bokeh.client import pull_session
    session = pull_session(url=srv.url("/app"))
    try:
        doc = session.document
        return doc, list(doc.roots)
    finally:
        session.close()


def _model_names(doc):
    return {type(m).__name__ for m in doc.select({})}


@pytest.fixture(scope="module")
def app_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestTheServedDocumentIsNotEmpty:
    """The test this file exists for."""

    def test_the_document_has_roots(self, app_dir):
        app = _build_app(app_dir)
        with _Served(app) as srv:
            doc, roots = _pull(srv)
            assert roots, (
                "bokeh serve delivered a document with NO ROOTS; the app "
                "bound make_document only under `if __name__ == \"__main__\"`, "
                "which Bokeh never satisfies -- it runs an app script under a "
                "synthetic module name"
            )

    def test_the_title_reaches_the_document(self, app_dir):
        app = _build_app(app_dir, title="Served Dashboard")
        with _Served(app) as srv:
            doc, _ = _pull(srv)
            assert doc.title == "Served Dashboard", doc.title


class TestTheServedDocumentHasTheContent:

    def test_a_figure_is_served(self, app_dir):
        """By TYPE, not by class name.

        Bokeh 3.9 calls the model ``figure``, lowercase; asserting on the
        string "Figure" would fail for a served document that is perfectly
        correct, and would silently start passing again if the name changed
        back.
        """
        from bokeh.models import Plot
        app = _build_app(app_dir)
        with _Served(app) as srv:
            doc, _ = _pull(srv)
            assert list(doc.select({"type": Plot})), sorted(_model_names(doc))

    def test_the_figure_has_its_data(self, app_dir):
        """An attached document with an empty source is still a blank chart."""
        from bokeh.models import ColumnDataSource
        app = _build_app(app_dir)
        with _Served(app) as srv:
            doc, _ = _pull(srv)
            sources = list(doc.select({"type": ColumnDataSource}))
            assert sources, "no ColumnDataSource in the served document"
            best = max(
                (len(next(iter(s.data.values()), [])) for s in sources),
                default=0)
            assert best >= 20, (
                f"the served source holds {best} rows; the data never "
                f"reached it, so every glyph refers to a column that does "
                f"not exist"
            )

    def test_a_filter_widget_is_served(self, app_dir):
        from bokeh.models import Select
        app = _build_app(
            app_dir, filters=[{"varname": "foreign", "type": "dropdown",
                               "exclude": [], "label": ""}])
        with _Served(app) as srv:
            doc, _ = _pull(srv)
            widgets = list(doc.select({"type": Select}))
            assert widgets, (
                f"the filter widget did not reach the served document: "
                f"{sorted(_model_names(doc))}"
            )
            assert widgets[0].options, "the dropdown has no options"

    def test_a_kpi_card_is_served(self, app_dir):
        app = _build_app(app_dir, kpis=[{
            "name": "k1", "stat": "mean", "var": "mpg", "title": "Avg MPG",
            "fmt": "%9.2f"}])
        with _Served(app) as srv:
            doc, _ = _pull(srv)
            from bokeh.models import Div
            texts = " ".join(d.text or ""
                             for d in doc.select({"type": Div}))
            assert "Avg MPG" in texts, texts[:300]


class TestTheHtmlIsNotTheDocument:
    """Why the obvious measurement is the wrong one.

    Recorded because the plan's own evidence for this defect was
    ``docs_json == {}`` read out of the HTML, which is true of a perfectly
    healthy Bokeh server app.
    """

    def test_the_served_html_carries_an_empty_docs_json(self, app_dir):
        import re as _re
        app = _build_app(app_dir)
        with _Served(app) as srv:
            _, page = srv.get("/app")
            blocks = [m.group(1) for m in _re.finditer(
                r'<script type="application/json"[^>]*>\s*(.*?)\s*</script>',
                page, re.S)]
            assert blocks, "no JSON block in the page at all"
            assert any(b.strip() == "{}" for b in blocks), (
                "Bokeh changed how it delivers the document; the tests above "
                "pull the session precisely because the HTML used not to "
                "contain it"
            )


class TestHealthOnTheLauncher:
    """Project rule 17 asks for a health endpoint that responds.

    It lives on the app's own server.  ``bokeh serve`` gives an app script no
    supported way to register a route -- measured: the only objects reachable
    from ``curdoc().session_context`` are the ApplicationContext and its io
    loop, never the Tornado application -- so ``/health`` cannot exist there.
    ``dash serve`` therefore runs the app directly rather than shelling out to
    ``bokeh serve``, which it used to do, and which is why /health returned
    404 on the one path dash documents.
    """

    def test_health_returns_200(self, app_dir):
        app = _build_app(app_dir)
        with _Launched(app) as srv:
            assert srv.status("/health") == 200

    def test_health_reports_a_status(self, app_dir):
        app = _build_app(app_dir)
        with _Launched(app) as srv:
            payload = json.loads(srv.get("/health")[1])
            assert payload.get("status") in ("ok", "healthy"), payload

    def test_the_dashboard_is_served_too(self, app_dir):
        app = _build_app(app_dir, title="Launcher Dashboard")
        with _Launched(app) as srv:
            _, page = srv.get("/")
            assert "Launcher Dashboard" in page

    def test_the_requested_port_is_the_one_used(self, app_dir):
        """--port used to be passed to `bokeh serve' and never to the app,
        so every generated app embedded 5006 whatever was asked for."""
        app = _build_app(app_dir)
        with _Launched(app) as srv:
            assert srv.status("/health") == 200
            _, body = srv.get("/health")
            assert json.loads(body)

    def test_loopback_by_either_name_is_accepted(self, app_dir):
        """allow_websocket_origin was the single literal localhost:<port>, so
        reaching the app as 127.0.0.1 got a blank page and there was no way
        to widen it."""
        app = _build_app(app_dir, title="Origin Test")
        with _Launched(app) as srv:
            for host in ("localhost", "127.0.0.1"):
                status, page = srv.get_from(host, "/health")
                assert status == 200, host
            status, page = srv.get_from("127.0.0.1", "/")
            assert status == 200
            assert "Origin Test" in page, (
                "the document is empty when reached as 127.0.0.1"
            )

    def test_an_extra_origin_can_be_added(self, app_dir):
        app = _build_app(app_dir)
        with _Launched(app, extra_args=["--allow-websocket-origin",
                                        "dash.example:8080"]) as srv:
            assert srv.status("/health") == 200


class TestTheLauncherOpensNoBrowser:
    """A server that opens a window on every start is unusable in batch."""

    def test_show_is_opt_in(self, app_dir):
        app = _build_app(app_dir)
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        assert "--show" in src, "there is no way to ask for a browser at all"
        i = src.index("_server.io_loop.add_callback(_server.show")
        window = src[max(0, i - 400):i]
        assert "_a.show" in window, (
            "the browser is opened unconditionally; it must be opt-in"
        )


class TestTheGeneratedSourceBindsAtModuleScope:
    """A cheap guard, so the slow tests above are not the only defence."""

    def test_the_app_calls_curdoc(self, app_dir):
        app = _build_app(app_dir)
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert "curdoc()" in code, (
            "the generated app never calls curdoc(), so nothing attaches the "
            "document when Bokeh runs it as an app script"
        )

    def test_the_binding_is_not_only_under_the_main_guard(self, app_dir):
        app = _build_app(app_dir)
        with open(app, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        guard = next((i for i, l in enumerate(lines)
                      if l.startswith("if __name__ ==")), len(lines))
        # The guard must actually be there: with the `next(..., len(lines))'
        # fallback, a generated app that dropped its `if __name__' block
        # would make `before' the WHOLE file, and "curdoc() in before" pass
        # on the very binding that then sits under no guard (24sep2026).
        assert guard < len(lines), (
            "the generated app has no `if __name__ == \"__main__\"' guard; "
            "the split below would read the whole file")
        before = "\n".join(lines[:guard])
        assert "curdoc()" in before, (
            "the document is attached only inside `if __name__ == "
            "\"__main__\"`, which Bokeh's app runner never satisfies"
        )

    def test_health_is_registered_outside_the_main_guard(self, app_dir):
        """bokeh serve never reaches the __main__ block."""
        app = _build_app(app_dir)
        with open(app, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        guard = next((i for i, l in enumerate(lines)
                      if l.startswith("if __name__ ==")), len(lines))
        assert guard < len(lines), (
            "the generated app has no `if __name__ == \"__main__\"' guard; "
            "the split below would read the whole file")
        before = "\n".join(lines[:guard])
        assert "/health" in before, (
            "/health is registered only under the __main__ guard"
        )
