"""Served recompute off the event loop (WP-30 P1.31b).

DROPIN-REMAINING.md P1.31 and GAPS2 F3d: a served filter move recomputed
every layer redraw and KPI statistic inline, on the server's one event
loop, so one reader's lowess move at 100,000 rows held /health, every
other session's moves, brushes and downloads, and new sessions for 8.1 s
(measured at c96facd).  A served move now plans on the loop (widgets read,
masks built), computes on one worker thread per process
(_DashRecomputeWorker, kept in S46's holder as ``recompute``), and applies
in one next-tick callback under the document lock.  A document with no
Bokeh server session (tests, the warm-up, a build's trial, Stata's
process) recomputes inline as before.

The audit of every name the worker reaches (``_WORKER_AUDIT``; verdicts):

| Name reached by the worker | Verdict |
|---|---|
| ``_DASH_MAPPER``, ``_DASH_SCHEME`` | read through ``_dash_cur_mapper()`` /
  ``_dash_cur_scheme()``: the plan's mapper copy and scheme |
| ``_DASH_CTX`` | thread-private |
| the plan, ``_slot`` | the plan is the worker's alone; ``_slot.gen`` is read
  only to skip a stale job, the loop's apply decides |
| ``_df_ref``, ``_agg_srcs``, ``_fgvals``, ``_owner_rows``, ``_kpi_defs``,
  ``_kpi_divs`` (membership only), ``_kpi_qual_rows``, ``_date_vars`` | read
  only after the build |
| ``df``, ``spec``, ``graphs``, ``g``, ``plot``, ``_sort_keys``,
  ``_shared_pos`` (the layer redraws' closures), ``_DASH_TRANSPOSE``,
  ``_GRAPH_SCHEME_PROPS``, ``_DASH_STYLE_ROWS`` (WP-31 E10's embedded
  style rows) | read only after the build |
| ``_DASH_GRAPH_SCHEMES`` (S34's per-scheme cache) | GIL-atomic get/set of
  an equal SchemeParser per name, never iterated |
| ``_DASH_REF_SCHEMES`` (WP-31 E11's per-reference cache) | GIL-atomic
  get/set keyed on (id(scheme), ref) and checked against the scheme
  itself; at worst two equal copies, never iterated |
| ``_go`` (WP-31 D5, the redraw's graph options) | read only after the
  build |
| ``_DASH_NOTED`` (via notes) | GIL-atomic ``in``/``add``; at worst a note
  twice |
| ``_fmt_cache`` | GIL-atomic get/set of equal transforms |
| ``_DASH_STATE.memo`` | every get and put under ``memo_lock`` (S46) |
| ``warnings`` | ``_DashWarnings``: dash's catch_warnings blocks serialised |
| ``_STORAGE_TYPES``, ``_format_kpi``, ``_dash_kpi_card``, live sources,
  ``curdoc`` | never: the apply step, on the loop |
"""
import ast
import concurrent.futures
import os
import sys
import threading
import time
import types
import urllib.request
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Div, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from conftest import make_spec  # noqa: E402
from serve_token_probe import TEST_TOKEN  # noqa: E402
from test_adversarial_matrix import (_SCATTER, _app_source,  # noqa: E402
                                     _kpi, _load_app, _unthrottled)
from test_serve_token import _free_port  # noqa: E402

_REPO = os.path.dirname(_HERE)
_SEQ = iter(range(10 ** 6))
_LOWESS = {"type": "lowess", "yvar": "mpg", "xvar": "weight", "options": {}}
_LFIT = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}

#: Every name the worker path reaches that is not a function, class or
#: module (see the module docstring for each verdict).
_WORKER_AUDIT = {
    "_DASH_CTX", "_DASH_MAPPER", "_DASH_SCHEME", "_DASH_STATE",
    "_DASH_NOTED", "_fmt_cache", "warnings",
    "_slot", "_df_ref", "_agg_srcs", "_fgvals", "_owner_rows",
    "_kpi_defs", "_kpi_divs", "_kpi_qual_rows", "_date_vars",
    "df", "spec", "graphs", "g", "plot", "_sort_keys", "_shared_pos",
    "_DASH_TRANSPOSE", "_GRAPH_SCHEME_PROPS", "_DASH_GRAPH_SCHEMES",
    "_DASH_REF_SCHEMES", "_go", "_DASH_STYLE_ROWS",
    # WP-31 H2t: a table graph's layer carries its text columns, named
    # through _dash_table_vars, which reads by()'s grammar tables -- module
    # constants, read and never written.
    "_DASH_BY_AXES_SPELLINGS", "_DASH_BY_GRAMMAR", "_DASH_BY_SUPPORTED",
    "_DASH_BY_TEXT_SPELLINGS",
}


def _spec():
    return make_spec([dict(_SCATTER), dict(_LOWESS), dict(_LFIT)],
                     filters=[{"varname": "foreign", "type": "dropdown"}],
                     kpis=[_kpi("both")])


@pytest.fixture(scope="module")
def app_src(tmp_path_factory):
    return _app_source(tmp_path_factory.mktemp("wk"), _spec())


def _fresh(app_src):
    return _load_app(app_src, "wk%d" % next(_SEQ))


@pytest.fixture
def ns(app_src):
    return _fresh(app_src)


def _closure(fn, name, seen=None):
    """The function called *name* among *fn*'s closure cells, depth first."""
    seen = set() if seen is None else seen
    if id(fn) in seen:
        return None
    seen.add(id(fn))
    for cell in (getattr(fn, "__closure__", None) or ()):
        try:
            v = cell.cell_contents
        except ValueError:
            continue
        if callable(v) and getattr(v, "__name__", "") == name:
            return v
        if callable(v):
            hit = _closure(v, name, seen)
            if hit is not None:
                return hit
    return None


def _cell(fn, name):
    for n, c in zip(fn.__code__.co_freevars, fn.__closure__ or ()):
        if n == name:
            return c.cell_contents
    raise KeyError(name)


def _select(doc):
    return next(iter(doc.select({"type": Select})))


def _move_cb(doc):
    return _closure(_unthrottled(_select(doc), "value"), "_on_filter_change")


def _build(ns, doc=None):
    doc = Document() if doc is None else doc
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _kpi_text(doc):
    return [d.text for d in doc.select({"type": Div}) if "db-kpi" in d.text]


def _sources(doc):
    out = []
    for s in doc.select({"type": ColumnDataSource}):
        out.append(tuple(sorted(
            (k, tuple(round(v, 9) if isinstance(v, float) else v
                      for v in list(col)))
            for k, col in s.data.items() if k != "index")))
    return sorted(out, key=repr)


def _sync_after(ns, value):
    doc = _build(ns)
    _select(doc).value = value
    return doc


# ===========================================================================
class TestTheQueue:

    @staticmethod
    def _worker(ns, ceiling=20):
        return ns["_DashRecomputeWorker"](ceiling)

    @staticmethod
    def _drain(w, timeout=10):
        # Jobs run first come first served: a last one marks the end.
        done, t0 = threading.Event(), time.monotonic()
        while not w.submit(object(), done.set):
            assert time.monotonic() - t0 < timeout, "the queue stayed full"
            time.sleep(0.01)
        assert done.wait(timeout), "the worker never drained"

    def test_latest_per_session_fifo_across_sessions(self, ns):
        w = self._worker(ns)
        gate, ran = threading.Event(), []
        w.submit("hold", lambda: gate.wait(10))
        for slot, tag in (("a", "a1"), ("b", "b1"), ("a", "a2"), ("c", "c1")):
            w.submit(slot, lambda tag=tag: ran.append(tag))
        gate.set()
        self._drain(w)
        assert ran == ["a2", "b1", "c1"]

    def test_the_ceiling_refuses(self, ns):
        w = self._worker(ns, ceiling=2)
        gate = threading.Event()
        assert w.submit("hold", lambda: gate.wait(10))
        while w._pending:
            time.sleep(0.01)
        assert w.submit("a", lambda: None) and w.submit("b", lambda: None)
        assert w.submit("a", lambda: None)
        assert w.submit("c", lambda: None) is False
        gate.set()
        self._drain(w)

    def test_forget(self, ns):
        w = self._worker(ns)
        gate, ran = threading.Event(), []
        w.submit("hold", lambda: gate.wait(10))
        w.submit("a", lambda: ran.append("a"))
        w.forget("a")
        gate.set()
        self._drain(w)
        assert ran == []

    def test_a_failing_job_does_not_stop_the_worker(self, ns):
        w = self._worker(ns)
        ran = []

        def bad():
            raise RuntimeError("a redraw that fails")
        w.submit("a", bad)
        w.submit("b", lambda: ran.append("b"))
        self._drain(w)
        assert ran == ["b"]

    def test_no_lock_is_held_while_a_job_runs(self, ns):
        w = self._worker(ns)
        done = threading.Event()
        w.submit("a", lambda: w.submit("b", done.set))
        assert done.wait(10)


# ===========================================================================
class TestOneWorkerPerProcess:

    def test_bokeh_serve_reexecution(self, app_src):
        a, b = _fresh(app_src), _fresh(app_src)
        wa, wb = a["_dash_recompute_worker"](), b["_dash_recompute_worker"]()
        assert wa is wb is a["_DASH_STATE"].recompute
        before = {t for t in threading.enumerate()
                  if t.name == "dash-recompute"}
        done = threading.Event()
        wa.submit("x", lambda: None)
        wb.submit("y", done.set)
        assert done.wait(10)
        new = {t for t in threading.enumerate()
               if t.name == "dash-recompute"} - before
        assert new <= {wa._thread} and wa._thread.is_alive()


# ===========================================================================
class TestWhoUsesTheWorker:

    def test_the_rule(self, ns, monkeypatch):
        from bokeh.server.contexts import BokehSessionContext
        wanted = ns["_dash_worker_wanted"]
        served = Document()
        ctx = BokehSessionContext("s57", None, served)
        monkeypatch.setattr(type(served), "session_context",
                            property(lambda d: getattr(d, "_wk_ctx", None)),
                            raising=False)
        served._wk_ctx = ctx
        assert wanted(served)
        assert not wanted(Document())
        # A stand-in context (the suite's served documents) has no
        # server session to apply on: inline.
        fake = Document()
        fake._wk_ctx = types.SimpleNamespace(id="x", request=None)
        assert not wanted(fake)
        monkeypatch.setitem(ns, "_DASH_TRIAL", True)
        assert not wanted(served)
        monkeypatch.setitem(ns, "_DASH_TRIAL", False)
        monkeypatch.setattr(sys, "_is_gil_enabled", lambda: False,
                            raising=False)
        assert not wanted(served)

    def test_in_process_stays_inline(self, ns):
        doc = _build(ns)
        before = _kpi_text(doc)
        _select(doc).value = "1"
        assert _kpi_text(doc) != before
        assert not list(doc.select({"name": "dash_updating"}))
        w = getattr(ns["_DASH_STATE"], "recompute", None)
        assert w is None or not w._pending


# ===========================================================================
class _Live:
    """The app's own launcher Server, in process, its IOLoop on a thread."""

    def __init__(self, ns):
        self.ns, self.port, self.err = ns, _free_port(), None
        ready = threading.Event()

        def run():
            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.srv = ns["_dash_server_app"](port=self.port,
                                                      token=TEST_TOKEN)
                self.srv.start()
                self.loop = self.srv.io_loop
            except BaseException as e:  # reported by __init__
                self.err = e
                ready.set()
                return
            ready.set()
            self.loop.start()
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        assert ready.wait(30) and self.err is None, self.err
        self.clients = []

    def session(self):
        from bokeh.client import pull_session
        c = pull_session(url="http://127.0.0.1:%d/" % self.port,
                         arguments={"token": TEST_TOKEN})
        self.clients.append(c)
        sid = c.id
        return self.on_loop(lambda: next(
            s for s in self.srv.get_sessions("/") if s.id == sid))

    def on_loop(self, fn, timeout=30):
        fut = concurrent.futures.Future()

        def go():
            try:
                fut.set_result(fn())
            except BaseException as e:  # handed to the caller
                fut.set_exception(e)
        self.loop.add_callback(go)
        return fut.result(timeout)

    def locked(self, ss, fn, wait=True):
        """fn() on the loop under *ss*'s document lock."""
        fut = concurrent.futures.Future()

        def go():
            try:
                fut.set_result(fn())
            except BaseException as e:  # handed to the caller
                fut.set_exception(e)
        self.loop.add_callback(
            lambda: ss.document.add_next_tick_callback(go))
        return fut.result(30) if wait else fut

    def wait_for(self, pred, timeout=20):
        t0 = time.monotonic()
        while not self.on_loop(pred):
            assert time.monotonic() - t0 < timeout, "timed out"
            time.sleep(0.02)

    def health_seconds(self):
        t0 = time.monotonic()
        try:
            urllib.request.urlopen(
                "http://127.0.0.1:%d/health" % self.port, timeout=5).read()
        except OSError as e:
            if not hasattr(e, "code"):
                return float("inf")
        return time.monotonic() - t0

    def close(self):
        for c in self.clients:
            try:
                c.close()
            except Exception:  # noqa: BLE001 -- teardown only
                pass
        w = getattr(self.ns["_DASH_STATE"], "recompute", None)
        if w is not None:
            t0 = time.monotonic()
            while w._pending and time.monotonic() - t0 < 10:
                time.sleep(0.02)
        self.loop.add_callback(self.srv.stop)
        self.loop.add_callback(self.loop.stop)
        self.thread.join(10)
        assert w is None or not w._pending, "a job was left waiting"


@pytest.fixture
def live(ns):
    st = ns["_DASH_STATE"]
    st.open.clear()
    srv = _Live(ns)
    try:
        yield srv
    finally:
        srv.close()
        st.open.clear()


class _Stall:
    """_compute_kpi held until released: a recompute that takes as long as
    the test needs, entered on whichever thread runs it."""

    def __init__(self, ns):
        self.entered, self.release = threading.Event(), threading.Event()
        self.threads = []
        real = ns["_compute_kpi"]

        def stalled(*a, **k):
            self.threads.append(threading.current_thread().name)
            self.entered.set()
            self.release.wait(15)
            return real(*a, **k)
        ns["_compute_kpi"] = stalled


def _slot_of(live, ss):
    return live.on_loop(lambda: _cell(_move_cb(ss.document), "_slot"))


def _move(live, ss, value, wait=False):
    return live.locked(ss, lambda: setattr(_select(ss.document), "value",
                                           value), wait=wait)


@pytest.mark.serve
class TestTheLoopAnswersDuringARecompute:

    def test_health_and_a_new_session(self, ns, live):
        ss = live.session()
        stall = _Stall(ns)
        try:
            _move(live, ss, "1")
            assert stall.entered.wait(10)
            took = live.health_seconds()
            assert took < 1.0, "/health took %.2f s during a recompute" % took
            other = live.session()
            assert other.document.roots
        finally:
            stall.release.set()
        slot = _slot_of(live, ss)
        live.wait_for(lambda: slot.applied == slot.gen)


@pytest.mark.serve
class TestBokehThreadRules:

    def test_the_thread_rules(self, ns, live, monkeypatch):
        from bokeh.core.has_props import HasProps
        ss = live.session()
        slot = _slot_of(live, ss)
        seen, writes = [], []
        real_card = ns["_dash_kpi_card"]

        def card(*a, **k):
            seen.append((threading.current_thread().name,
                         ss._pending_writes is not None))
            return real_card(*a, **k)
        ns["_dash_kpi_card"] = card
        real_set = HasProps.__setattr__

        def recorder(self, name, value):
            if threading.current_thread().name == "dash-recompute" and \
                    getattr(self, "document", None) is not None:
                writes.append((type(self).__name__, name))
            return real_set(self, name, value)
        monkeypatch.setattr(HasProps, "__setattr__", recorder)
        stall = _Stall(ns)
        stall.release.set()
        _move(live, ss, "1", wait=True)
        live.wait_for(lambda: slot.applied == slot.gen == 1)
        loop_name = live.on_loop(lambda: threading.current_thread().name)
        assert set(stall.threads) == {"dash-recompute"}
        assert seen and all(t == loop_name and lk for t, lk in seen), seen
        assert writes == []


@pytest.mark.serve
class TestStaleResultsAreDropped:

    def test_two_moves(self, ns, live):
        ss = live.session()
        slot = _slot_of(live, ss)
        stall = _Stall(ns)
        applied = []
        real_card = ns["_dash_kpi_card"]
        ns["_dash_kpi_card"] = lambda *a, **k: (
            applied.append(slot.gen), real_card(*a, **k))[1]
        g0 = live.on_loop(lambda: slot.gen)
        _move(live, ss, "1")
        assert stall.entered.wait(10)
        _move(live, ss, "0", wait=True)
        stall.release.set()
        live.wait_for(lambda: slot.applied == g0 + 2)
        assert applied == [g0 + 2]
        want = _kpi_text(_sync_after(ns, "0"))
        assert live.on_loop(lambda: _kpi_text(ss.document)) == want


@pytest.mark.serve
class TestAsyncEqualsSync:

    def test_corpus(self, ns, live):
        ss = live.session()
        slot = _slot_of(live, ss)
        for value in ("1", "0", ""):
            _move(live, ss, value, wait=True)
            live.wait_for(lambda: slot.applied == slot.gen)
            got = live.on_loop(lambda: (_sources(ss.document),
                                        _kpi_text(ss.document)))
            want = _sync_after(ns, value)
            assert got == (_sources(want), _kpi_text(want)), value


@pytest.mark.serve
class TestTheCue:

    def test_shown_then_hidden(self, ns, live):
        ss = live.session()
        slot = _slot_of(live, ss)
        stall = _Stall(ns)
        cue = live.on_loop(lambda: next(iter(
            ss.document.select({"name": "dash_updating"}))))
        assert live.on_loop(lambda: cue.visible) is False
        _move(live, ss, "1")
        assert stall.entered.wait(10)
        assert live.on_loop(lambda: cue.visible) is True
        assert cue.text == "Updating..."
        stall.release.set()
        live.wait_for(lambda: slot.applied == slot.gen)
        assert live.on_loop(lambda: cue.visible) is False

    def test_a_failed_recompute_clears_it(self, ns, live):
        ss = live.session()
        slot = _slot_of(live, ss)
        before = live.on_loop(lambda: _sources(ss.document))
        real_fig = ns["bokeh_figure"]

        def broken(*a, **k):
            raise RuntimeError("a redraw that fails")
        ns["bokeh_figure"] = broken
        g = live.on_loop(lambda: slot.gen) + 1
        _move(live, ss, "1")
        cue = live.on_loop(lambda: next(iter(
            ss.document.select({"name": "dash_updating"}))))
        live.wait_for(lambda: slot.failed == g)
        assert live.on_loop(lambda: cue.visible) is False
        assert live.on_loop(lambda: _sources(ss.document)) == before
        from bokeh.io import doc as _bdoc
        # Bokeh never undoes its curdoc patch for a callback that raises.
        assert live.on_loop(lambda: len(_bdoc._PATCHED_CURDOCS)) == 0
        ns["bokeh_figure"] = real_fig
        _move(live, ss, "0")
        live.wait_for(lambda: slot.applied == g + 1)


@pytest.mark.serve
class TestAClosedSessionDropsItsResult:

    def test_closed(self, ns, live):
        ss = live.session()
        slot = _slot_of(live, ss)
        stall = _Stall(ns)
        _move(live, ss, "1")
        assert stall.entered.wait(10)
        # As Bokeh's lifecycle handler does once it discards a session.
        live.on_loop(lambda: [cb(ss.document.session_context) for cb in
                              list(ss.document.session_destroyed_callbacks)])
        assert slot.alive is False
        stall.release.set()
        other = live.session()
        oslot = _slot_of(live, other)
        _move(live, other, "1")
        live.wait_for(lambda: oslot.applied == oslot.gen)
        assert slot.applied != slot.gen


# ===========================================================================
class TestTheTripwires:

    def test_the_worker_draws_with_its_own_mapper_and_scheme(self, ns):
        doc = _build(ns)
        cb = _move_cb(doc)
        plan_of, compute = (_closure(cb, "_dash_move_plan"),
                            _closure(cb, "_dash_move_compute"))
        gm = ns["_DASH_MAPPER"]
        dicts = {k: (id(v), dict(v)) for k, v in vars(gm).items()
                 if isinstance(v, dict)}
        plan = plan_of(True)
        assert plan["mapper"] is not gm and plan["scheme"] is ns["_DASH_SCHEME"]
        entered, swapped, seen = (threading.Event(), threading.Event(), [])
        real_add = ns["_dash_add_glyph"]

        def add(mapper, *a, **k):
            entered.set()
            swapped.wait(10)
            seen.append((mapper is plan["mapper"],
                         mapper.scheme is plan["scheme"],
                         mapper.tr._scheme_of() is plan["scheme"]))
            return real_add(mapper, *a, **k)
        ns["_dash_add_glyph"] = add
        out = []
        t = threading.Thread(target=lambda: out.append(compute(plan)))
        t.start()
        assert entered.wait(10)
        # Another session's build swaps the module's scheme on the loop.
        other = ns["SchemeParser"].resolve_or_fallback("s1mono", "test")
        saved = ns["_DASH_SCHEME"]
        ns["_DASH_SCHEME"], gm.scheme = other, other
        swapped.set()
        t.join(30)
        ns["_DASH_SCHEME"], gm.scheme = saved, saved
        assert out and seen and all(all(s) for s in seen), seen
        assert {k: (id(v), dict(v)) for k, v in vars(gm).items()
                if isinstance(v, dict)} == dicts


# ===========================================================================
class TestTheWarningFilters:

    def test_blocks_serialise(self, ns):
        w = ns["warnings"]
        assert type(w).__name__ == "_DashWarnings"
        inside, release, order = threading.Event(), threading.Event(), []

        def holder():
            with w.catch_warnings():
                inside.set()
                release.wait(10)
                order.append("first out")

        def second():
            with w.catch_warnings():
                order.append("second in")
        t1 = threading.Thread(target=holder)
        t1.start()
        assert inside.wait(10)
        t2 = threading.Thread(target=second)
        t2.start()
        t2.join(0.3)
        assert order == []
        release.set()
        t1.join(10)
        t2.join(10)
        assert order == ["first out", "second in"]

    def test_filters_survive(self, ns):
        w = ns["warnings"]
        assert type(w).__name__ == "_DashWarnings"
        before = list(w.filters)

        def blocks():
            for _ in range(100):
                with w.catch_warnings():
                    w.simplefilter("ignore")
        ts = [threading.Thread(target=blocks) for _ in range(2)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(30)
        assert list(w.filters) == before

    def test_no_local_warnings_import(self, app_src):
        """No function opens a catch_warnings block on a warnings module it
        imported itself, which the app's proxy would not serialise (S23's
        note hook imports it locally only to set showwarning)."""
        bad = []
        for node in ast.walk(ast.parse(app_src)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            subs = list(ast.walk(node))
            local = any((isinstance(s, ast.Import) and any(
                a.name == "warnings" for a in s.names)) or (
                isinstance(s, ast.ImportFrom) and s.module == "warnings")
                for s in subs)
            blocks = any(isinstance(s, ast.Attribute)
                         and s.attr == "catch_warnings" for s in subs) or \
                any(isinstance(s, ast.Name) and s.id == "catch_warnings"
                    for s in subs)
            if local and blocks:
                bad.append(node.name)
        assert bad == []


# ===========================================================================
class TestTheWorkerTouchesOnlyAuditedNames:

    def test_the_walk(self, ns):
        doc = _build(ns)
        cb = _move_cb(doc)
        start = _closure(cb, "_dash_move_compute")
        unaudited, seen = set(), set()

        import re as _re
        frozen = (int, float, str, bytes, bool, type(None), tuple,
                  frozenset, _re.Pattern)

        def data(v):
            return not (callable(v) or isinstance(v, types.ModuleType))

        def shared(v):
            return data(v) and not isinstance(v, frozen)

        def walk(fn, path):
            if id(fn) in seen or not hasattr(fn, "__code__"):
                return
            seen.add(id(fn))
            if getattr(fn, "__globals__", None) is not ns:
                return
            codes = [fn.__code__]
            names = set()
            while codes:
                c = codes.pop()
                names.update(c.co_names)
                codes.extend(k for k in c.co_consts if hasattr(k, "co_names"))
            for n in sorted(names):
                if n in ns:
                    v = ns[n]
                    if shared(v):
                        if n not in _WORKER_AUDIT:
                            unaudited.add("%s via %s" % (n, path))
                    elif not data(v):
                        walk(v, path + " > " + n)
            for n, c in zip(fn.__code__.co_freevars, fn.__closure__ or ()):
                try:
                    v = c.cell_contents
                except ValueError:
                    continue
                if shared(v):
                    if n not in _WORKER_AUDIT:
                        unaudited.add("%s via %s" % (n, path))
                elif not data(v):
                    walk(v, path + " > " + n)
        walk(start, "_dash_move_compute")
        # The layer redraws the compute calls through _agg_srcs.
        for key, agg in _closure(cb, "_dash_move_compute").__closure__[
                start.__code__.co_freevars.index("_agg_srcs")
        ].cell_contents.items():
            walk(agg["redraw"], "redraw %r" % (key,))
        assert not unaudited, "\n".join(sorted(unaudited))


# ===========================================================================
class TestTheHelp:

    def test_the_paragraph(self):
        with open(os.path.join(_REPO, "dash.sthlp"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        start = text.index("{ul:Recomputation.}")
        para = text[start:text.index("{pstd}", start)]
        for needle in ("one worker thread", "Updating...", "about 3 minutes"):
            assert needle in para, needle
        assert "one event loop -- runs one" not in para
