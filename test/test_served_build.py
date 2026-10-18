"""A served session's document is built off the event loop (WP-32, BUGS.md
"Served build on the event loop"; GAPS3 H3).

``make_document`` built every session's dashboard on the server's one
event loop (1.6-4.6 s at 100-200k rows), so while one reader's page was
being built /health, every other session's moves and every new session
waited.  Under ``python app.py`` (and so ``dash serve``) the app's handler
(``_DashBuildHandler``) now builds in Bokeh's ``on_session_created`` hook,
awaited before the session exists, on the process's build threads
(``_dash_build_pool``): Bokeh hands the hook the session's document
before any session holds it, so nothing else reads or writes it there.
The build draws with a mapper and scheme of its own (``_DASH_CTX``), so a
build never swaps the module's, which the loop's moves read.
``modify_document`` then has nothing left to do.  A document built
without a server session (tests, the warm-up, a build's trial, Stata's
process, ``bokeh serve``) is built inline, as before.
"""
import os
import sys
import threading
import time
import warnings

import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_served_worker as tw  # noqa: E402
from test_date_axis_residuals import _digest  # noqa: E402

app_src = tw.app_src
ns = tw.ns
live = tw.live


class _FirstBuildStall:
    """The first build's first ``_compute_kpi`` held until released; every
    other call passes.  Records the thread each call ran on."""

    def __init__(self, ns):
        self.entered, self.release = threading.Event(), threading.Event()
        self.threads, self._first = [], True
        real = ns["_compute_kpi"]

        def stalled(*a, **k):
            self.threads.append(threading.current_thread().name)
            if self._first:
                self._first = False
                self.entered.set()
                self.release.wait(20)
            return real(*a, **k)
        ns["_compute_kpi"] = stalled


def _pull(live, out):
    try:
        out.append(live.session())
    except BaseException as e:  # reported by the test
        out.append(e)


@pytest.mark.serve
class TestTheLoopAnswersWhileASessionBuilds:

    def test_health_and_a_second_session(self, ns, live):
        stall = _FirstBuildStall(ns)
        first = []
        t = threading.Thread(target=_pull, args=(live, first), daemon=True)
        t.start()
        try:
            assert stall.entered.wait(20), "the first build never started"
            assert stall.threads[0].startswith("dash-build"), stall.threads
            took = live.health_seconds()
            assert took < 1.0, "/health took %.2f s during a build" % took
            second = []
            _pull(live, second)
            assert not isinstance(second[0], BaseException), second
            assert live.on_loop(lambda: bool(second[0].document.roots))
            assert first == [], "the first session finished while stalled"
        finally:
            stall.release.set()
        t.join(30)
        assert first and not isinstance(first[0], BaseException), first
        assert live.on_loop(lambda: bool(first[0].document.roots))


class TestTheBuildOffTheLoopDrawsTheSameDocument:

    def test_threaded_equals_inline(self, ns):
        inline = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](inline)
        threaded = Document()
        done = []

        def go():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                done.append(ns["_dash_build_off_loop"](threaded))
        t = threading.Thread(target=go, name="dash-build-probe")
        t.start()
        t.join(60)
        assert done == [True], done
        assert ns["_DASH_CTX"].__dict__.get("mapper") is None
        assert len(threaded.roots) == len(inline.roots) == 1
        assert _digest(threaded.roots[0]) == _digest(inline.roots[0])

    def test_a_failed_build_is_reported_not_raised(self, ns, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError("probe")
        monkeypatch.setitem(ns, "make_document", boom)
        got = ns["_dash_build_off_loop"](Document())
        assert isinstance(got, RuntimeError)


def test_the_launcher_serves_through_the_build_handler(app_src):
    assert "Application(_DashBuildHandler(make_document))" in app_src
    assert "Application(FunctionHandler(make_document))" not in app_src
