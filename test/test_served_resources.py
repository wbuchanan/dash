"""Served session capacity and memory (WP-30 P1.31a).

DROPIN-REMAINING.md, P1.31: a served app had no concurrent-session cap and
no unused-session lifetime, and each session decoded the whole dataset
again.  Measured at c96facd: 25 held sessions of a 200k-row app took 2 GB,
a connected tab was never discarded, and three documents decoded the data
three times.  Threat: memory exhaustion of the served app by open sessions.
"""
import os
import sys
import threading
import types
import warnings

import numpy as np
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Div, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402
from serve_token_probe import TEST_TOKEN  # noqa: E402
from test_adversarial_matrix import (_SCATTER, _app_source,  # noqa: E402
                                     _kpi, _load_app, _unthrottled)
from test_serve_token import (_app_cmd, _drop_filters, _free_port,  # noqa: E402
                              _Proc, _run_main, _status)

_SEQ = iter(range(10 ** 6))
_LOWESS = {"type": "lowess", "yvar": "mpg", "xvar": "weight", "options": {}}


class _Ctx(types.SimpleNamespace):
    """A served session's context: Bokeh's session id and the request."""


class _Served(Document):
    """A Document served to session *sid*, as Bokeh hands make_document one."""

    def __init__(self, sid):
        super().__init__()
        self._ctx = _Ctx(id=sid, request=types.SimpleNamespace(
            remote_ip="10.0.0.%d" % (hash(sid) % 200 + 1), headers={},
            arguments={"token": [TEST_TOKEN.encode("ascii")]}))

    @property
    def session_context(self):
        return self._ctx


def _reset(ns):
    st = ns["_DASH_STATE"]
    st.open.clear()
    st.payload_key = st.payload = None
    st.memo.clear()
    st.memo_bytes = 0
    st.cap, st.idle = 20, 60
    return st


def _make(ns, doc):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _has_plot(doc):
    return any(type(m).__name__ in ("Plot", "figure") for m in doc.select({}))


def _divs(doc):
    return " ".join(d.text for d in doc.select({"type": Div}))


@pytest.fixture(scope="module")
def app_ns(tmp_path_factory):
    spec = make_spec([dict(_SCATTER)],
                     filters=[{"varname": "foreign", "type": "dropdown"}],
                     kpis=[_kpi("both")])
    return _load_app(_app_source(tmp_path_factory.mktemp("res"), spec), "res")


@pytest.fixture
def ns(app_ns):
    _reset(app_ns)
    yield app_ns
    _reset(app_ns)


@pytest.fixture(scope="module")
def lowess_ns(tmp_path_factory):
    src = _app_source(tmp_path_factory.mktemp("res_lw"),
                      make_spec([dict(_SCATTER), dict(_LOWESS)]))
    return _load_app(src, "res_lw")


def _state():
    st = types.SimpleNamespace()
    st.memo, st.memo_bytes = __import__("collections").OrderedDict(), 0
    st.memo_lock = threading.Lock()
    return st


# ===========================================================================
class TestTheHelpers:

    def test_idle_due(self):
        assert not dr._dash_idle_due(0.0, 10 ** 9, 0)
        assert not dr._dash_idle_due(0.0, 59.9 * 60, 60)
        assert dr._dash_idle_due(0.0, 60 * 60, 60)

    def test_cap_value(self):
        import argparse
        assert [dr._dash_session_cap_value(v)
                for v in ("20", "1000000", "007", 3)] == [20, 1000000, 7, 3]
        bad = []
        for v in ("0", "-1", "1_000", " 20", "２０", "9" * 400,
                  "1000001", "3.5", "", None, True):
            try:
                dr._dash_session_cap_value(v)
                bad.append(v)
            except argparse.ArgumentTypeError as e:
                assert len(str(e)) < 100, str(e)
        assert not bad, bad

    def test_minutes_value(self):
        import argparse
        assert [dr._dash_minutes_value(v)
                for v in ("0", "60", "525600")] == [0, 60, 525600]
        for v in ("525601", "-1", "5m", ""):
            with pytest.raises(argparse.ArgumentTypeError):
                dr._dash_minutes_value(v)

    def test_defaults_from_the_environment(self):
        assert dr._dash_session_defaults({}) == (20, 60)
        assert dr._dash_session_defaults(
            {"DASH_MAX_SESSIONS": "3", "DASH_IDLE_TIMEOUT": "0"}) == (3, 0)
        for env, name in (({"DASH_MAX_SESSIONS": "0"}, "DASH_MAX_SESSIONS"),
                          ({"DASH_IDLE_TIMEOUT": "x"}, "DASH_IDLE_TIMEOUT")):
            with pytest.raises(ValueError, match=name):
                dr._dash_session_defaults(env)

    def test_the_holder_is_one_per_process(self):
        a = dr._dash_served_state()
        assert dr._dash_served_state() is a is sys.modules["_dash_served_state"]
        assert type(a.memo_lock) is type(threading.Lock())


# ===========================================================================
class TestTheDataIsDecodedOncePerProcess:

    def test_five_documents_decode_once(self, ns, monkeypatch):
        calls = []
        real = ns["_dash_read_data_json"]
        monkeypatch.setitem(ns, "_dash_read_data_json",
                            lambda t: calls.append(1) or real(t))
        for _ in range(5):
            assert _has_plot(_make(ns, Document()))
        assert len(calls) == 1

    def test_shared_arrays_are_read_only(self, ns):
        _make(ns, Document())
        _spec, df, _meta = ns["_DASH_STATE"].payload
        blocks = [b.values for b in df._mgr.blocks]
        assert blocks and not any(getattr(a, "flags", None) is not None
                                  and a.flags.writeable for a in blocks)

    def test_a_move_in_one_session_leaves_another_alone(self, ns):
        d1 = _make(ns, Document())
        sel = next(iter(d1.select({"type": Select})))
        sel.value = "1"
        _unthrottled(sel, "value")("value", None, "1")
        d2 = _make(ns, Document())
        n = max(len(s.data.get("mpg", ())) for s in
                d2.select({"type": ColumnDataSource}))
        assert n == 10

    def test_two_module_runs_share_it(self, tmp_path):
        src = _app_source(tmp_path, make_spec([dict(_SCATTER)]))
        a = _load_app(src, "res_a%d" % next(_SEQ))
        st = _reset(a)
        _make(a, Document())
        key = st.payload_key
        b = _load_app(src, "res_b%d" % next(_SEQ))
        assert b["_DASH_STATE"] is st and st.payload_key == key
        calls = []
        real = b["_dash_read_data_json"]
        b["_dash_read_data_json"] = lambda t: calls.append(1) or real(t)
        _make(b, Document())
        assert calls == []
        _reset(a)

    def test_skipped_in_a_trial_or_in_stata(self, ns, monkeypatch):
        st = ns["_DASH_STATE"]
        loader = lambda: ({}, None, {})  # noqa: E731
        monkeypatch.setitem(ns, "_DASH_TRIAL", True)
        assert ns["_dash_shared_payload"](st, "a", "b", loader) == ({}, None, {})
        assert st.payload is None
        monkeypatch.setitem(ns, "_DASH_TRIAL", False)
        monkeypatch.setitem(sys.modules, "sfi", types.ModuleType("sfi"))
        ns["_dash_shared_payload"](st, "a", "b", loader)
        assert st.payload is None

    def test_one_entry_only(self, ns):
        import pandas as pd
        st = ns["_DASH_STATE"]
        f = lambda v: lambda: ({"v": v}, pd.DataFrame({"x": [v]}), {})  # noqa
        ns["_dash_shared_payload"](st, "s1", "d1", f(1.0))
        k1 = st.payload_key
        spec, df, _ = ns["_dash_shared_payload"](st, "s2", "d2", f(2.0))
        assert st.payload_key != k1 and spec == {"v": 2.0}
        assert float(df["x"].iloc[0]) == 2.0


# ===========================================================================
class TestSessionsAreCapped:

    def test_in_process_documents_take_no_slot(self, ns):
        ns["_DASH_STATE"].cap = 3
        for _ in range(5):
            assert _has_plot(_make(ns, Document()))
        assert ns["_DASH_STATE"].open == {}

    def test_bokeh_serve_path_shows_the_busy_text(self, ns, monkeypatch):
        st = ns["_DASH_STATE"]
        st.cap = 1
        assert _has_plot(_make(ns, _Served("s-1")))
        calls = []
        monkeypatch.setitem(ns, "_load_spec_and_data",
                            lambda: calls.append(1))
        st.payload_key = None
        d2 = _make(ns, _Served("s-2"))
        assert not _has_plot(d2) and _divs(d2) == dr._DASH_BUSY_HTML
        assert calls == [] and list(st.open) == ["s-1"]

    def test_a_closed_session_frees_its_place(self, ns):
        st = ns["_DASH_STATE"]
        st.cap = 1
        d1 = _make(ns, _Served("s-1"))
        for cb in list(d1.session_destroyed_callbacks):
            cb(d1.session_context)
            cb(d1.session_context)          # released once, idempotent
        assert st.open == {}
        assert _has_plot(_make(ns, _Served("s-2")))

    @pytest.mark.serve
    def test_the_fourth_page_is_busy(self, tmp_path):
        """Also the keyless client: 403 before the cap is looked at."""
        src = _app_source(tmp_path, make_spec([dict(_SCATTER)]))
        app = str(tmp_path / "app.py")
        port = _free_port()
        base = "http://127.0.0.1:%d/" % port
        with _Proc(_app_cmd(app, port, "--max-sessions", "3"), port=port,
                   env={"DASH_SERVE_TOKEN": TEST_TOKEN}):
            for _ in range(3):
                assert _status(base + "?token=" + TEST_TOKEN)[0] == 200
            st, body, hdr, _r = _status(base + "?token=" + TEST_TOKEN)
            assert st == 503, (st, body[:200])
            assert hdr["Retry-After"] == "30"
            assert body == dr._DASH_BUSY_HTML and "<script" not in body
            assert hdr["Content-Security-Policy"]
            assert hdr["X-Frame-Options"] == "DENY"
            assert _status(base)[0] == 403
        assert src

    def test_a_keyless_client_gets_403_not_503(self, ns):
        import asyncio
        from tornado.web import HTTPError
        st = ns["_DASH_STATE"]
        st.cap = 1
        st.open["x"] = True
        prov = ns["_dash_cap_auth"](ns["_dash_token_auth"](TEST_TOKEN), st)
        from bokeh.server.views.doc_handler import DocHandler
        h = DocHandler.__new__(DocHandler)
        h.request = types.SimpleNamespace(arguments={}, headers={},
                                          query_arguments={})
        with pytest.raises(HTTPError) as e:
            asyncio.run(prov.get_user_async(h))
        assert e.value.status_code == 403


# ===========================================================================
class TestIdleSessionsAreClosed:

    @staticmethod
    def _clocked(ns, monkeypatch):
        clock = [1000.0]
        monkeypatch.setitem(ns, "_time", types.SimpleNamespace(
            monotonic=lambda: clock[0]))
        return clock

    @staticmethod
    def _check(doc):
        cbs = [c for c in doc.session_callbacks
               if type(c).__name__ == "PeriodicCallback"]
        assert len(cbs) == 1
        return cbs[0].callback

    def test_closed_after_the_lifetime(self, ns, monkeypatch):
        clock = self._clocked(ns, monkeypatch)
        doc = _make(ns, _Served("s-1"))
        check = self._check(doc)
        clock[0] += 59 * 60
        check()
        assert _has_plot(doc)
        clock[0] += 60
        check()
        assert not _has_plot(doc)
        assert _divs(doc) == dr._DASH_IDLE_HTML % 60
        assert ns["_DASH_STATE"].open == {} and not doc.session_callbacks

    def test_activity_resets_the_clock(self, ns, monkeypatch):
        clock = self._clocked(ns, monkeypatch)
        doc = _make(ns, _Served("s-1"))
        check = self._check(doc)
        sel = next(iter(doc.select({"type": Select})))
        src = next(m.data_source for m in doc.select({"type": object})
                   if isinstance(getattr(m, "data_source", None),
                                 ColumnDataSource)
                   and m.data_source.selected._callbacks.get("indices"))
        for fire in (lambda: _unthrottled(sel, "value")("value", None, "1"),
                     lambda: _unthrottled(src.selected, "indices")(
                         "indices", [], [0])):
            clock[0] += 59 * 60
            fire()
            clock[0] += 120
            check()
            assert _has_plot(doc)

    def test_zero_means_never(self, ns):
        ns["_DASH_STATE"].idle = 0
        doc = _make(ns, _Served("s-1"))
        assert not [c for c in doc.session_callbacks
                    if type(c).__name__ == "PeriodicCallback"]


# ===========================================================================
class TestTheAppsCommandLine:

    def test_app_parser(self, ns):
        p = ns["_dash_arg_parser"]()
        a = p.parse_args(["--max-sessions", "7", "--idle-timeout", "0"])
        assert (a.max_sessions, a.idle_timeout) == (7, 0)
        d = p.parse_args([])
        assert (d.max_sessions, d.idle_timeout) == (20, 60)
        for bad in (["--max-sessions", "0"], ["--idle-timeout", "-1"]):
            with pytest.raises(SystemExit):
                p.parse_args(bad)

    def test_main_warms_up_first_and_sets_the_server(self, tmp_path,
                                                     monkeypatch, capsys):
        """The preparing line comes first, the data is decoded before the
        Server exists, the banner names the cap and the idle time, and the
        Server gets Bokeh's lifetimes and the cap gate."""
        src = _app_source(tmp_path, make_spec([dict(_SCATTER),
                                               dict(_LOWESS)]))
        monkeypatch.setenv("DASH_SERVE_TOKEN", TEST_TOKEN)
        st = dr._dash_served_state()
        st.payload_key = st.payload = None
        seen = {}
        monkeypatch.setattr(warnings, "showwarning", warnings.showwarning)
        had_notes = "_dash_app_notes" in sys.modules
        try:
            _run_main(src, ["app.py", "--max-sessions", "4",
                            "--idle-timeout", "9"], monkeypatch, seen)
        finally:
            _drop_filters()
            if not had_notes:
                sys.modules.pop("_dash_app_notes", None)
        out = [ln for ln in capsys.readouterr().out.splitlines()
               if not ln.startswith("dash: this Bokeh admits")]
        assert out[0] == "preparing the dashboard (10 rows, lowess)", out
        assert ("Sessions open at once: 4; idle sessions close after 9 "
                "minutes (0 = never).") in out
        kw = seen["kw"]
        assert kw["unused_session_lifetime_milliseconds"] == 15000
        assert kw["check_unused_sessions_milliseconds"] == 5000
        assert type(kw["auth_provider"]).__name__ == "_DashCapAuth"
        assert (st.cap, st.idle) == (4, 9) and st.payload is not None
        st.cap, st.idle, st.payload_key, st.payload = 20, 60, None, None


# ===========================================================================
class TestTheLauncherFlags:

    def test_launch_app_passes_them(self, tmp_path, monkeypatch):
        import subprocess
        from test_serve_lifecycle import _built_app
        from serve_token_probe import FakeStdin
        import io
        app = _built_app(tmp_path)
        rec = {}

        class _Fake:
            def __init__(self, cmd, **kw):
                rec["cmd"] = list(cmd)
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
        dr._dash_launch_app(app, _free_port(), 0, True, prebind=False,
                            max_sessions=7, idle_timeout=0)
        cmd = rec["cmd"]
        i = cmd.index("--max-sessions")
        assert cmd[i + 1] == "7"
        assert cmd[cmd.index("--idle-timeout") + 1] == "0"

    def test_renderer_main_accepts_them(self, tmp_path, monkeypatch):
        """dash_render.py's own command line parses both flags and hands
        them to the launcher as ints (TR-46.13); 0 sessions is refused."""
        with open(dr.__file__, encoding="utf-8") as fh:
            src = fh.read()
        block = src[src.index('if __name__ == "__main__":'):]
        rec = {}

        def _launch(*a, **kw):
            rec.update(kw)

        def run(*flags):
            ns = dict(vars(dr), __name__="__main__", main=lambda *a, **k: {},
                      _dash_launch_app=_launch)
            monkeypatch.setattr(sys, "argv", [
                "dash_render.py", "--spec", "s.json", "--data", "d.json",
                "--output", str(tmp_path / "app.py"), "--mode", "server",
                "--launch", "--no-browser"] + list(flags))
            exec(compile(block, dr.__file__, "exec"), ns)
        run("--max-sessions", "7", "--idle-timeout", "0")
        assert (rec["max_sessions"], rec["idle_timeout"]) == (7, 0)
        run()
        assert (rec["max_sessions"], rec["idle_timeout"]) == (None, None)
        with pytest.raises(SystemExit):
            run("--max-sessions", "0")


# ===========================================================================
class TestTheSavedPageIsUnchanged:

    def test_digest(self, tmp_path):
        """AC-46.7: the served-limit work (cap, idle close, shared payload,
        estimator memo) lives in the generated app only; a saved page with a
        lowess layer, a filter and a KPI is the same page as at af9676f."""
        from conftest import render_models
        from test_adversarial_matrix import _write_inputs
        from test_date_axis_residuals import _digest
        sp, dp = _write_inputs(tmp_path, make_spec(
            [dict(_SCATTER), dict(_LOWESS)],
            filters=[{"varname": "foreign", "type": "dropdown"}],
            kpis=[_kpi("both")]))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp, str(tmp_path / "o.html"))
            render_models(r)
        # Taken at af9676f (ids stripped, gzipped buffers decompressed);
        # re-derived at 3d28881, whose %tw week-start tick port changes only
        # the page's two date-tick CustomJS code strings; and at 76547f8
        # (WP-31 F1a), whose fit prelude changes only the filter callback's
        # code string (every other model property is the same); and at
        # WP-31 F1c, which re-smooths the lowess layer: its source moves into
        # the filter callback's agg_sources with its config, its stale-cue
        # args, caption and 0.3 muted alpha go, and the code string grows
        # (diffed with every code string masked; nothing else differs); and
        # at WP-31 F1b, whose lfitci/qfitci branch changes only the filter
        # callback's code string (the base's _FILTER_JS gives the old
        # digest on the new tree); and at WP-31 F1d, whose lpoly helpers
        # and branch change only that code string too (likewise measured);
        # and at WP-31 F1e, whose lpolyci helpers, branch and cache change
        # only that code string (likewise measured); and at WP-31 C11b,
        # whose exact-fit mark changes only that code string (likewise
        # measured); and at WP-31 F1f, whose mband and mspline helpers and
        # branch change only that code string (likewise measured); and at
        # WP-31 F1g, whose fpfit and fpfitci helpers and branch change only
        # that code string (likewise measured).
        # Re-derived after WP-31 batch 10: B4c's contour branch changes only
        # the filter callback's code; D4 gives the legend the scheme's
        # geometry (glyph size, standoff, margin, padding, spacing, rows).
        # Re-derived after WP-31 batch 11: D7 sets the axis title's
        # standoff to the scheme's axis_title_gap (minuscule, 1 px) where
        # Bokeh's default drew 5; every other model property is the same.
        # Re-derived after WP-31 batch 12: B5c adds an empty "dots" list to
        # each axis of the saved page's axis plan; the rest is code strings.
        # Re-derived after WP-31 E2: line patterns are Stata's numbers in
        # relative units (the minor grid's dot [1, 3] px; [2, 4] before);
        # with WP-31 D12's zoom statement (code only), merged in batch 13.
        # Re-derived after WP-31 G1: the filter mask's code gains the
        # extended-missing option branch (code only); and after WP-31 G2:
        # each Stata writer's args and code carry the page's dp; and after
        # WP-31 C16: the filter code's recast writer (code only); and
        # after WP-31 C11: lpoly's weight threshold in its JS twin; and
        # after WP-31 G7: the writer's %d (code only).
        assert _digest(r._last_layout_root) == _SAVED_DIGEST


_SAVED_DIGEST = (
    # Re-derived on the merged batch 15 (D15, G7 and C11 each re-pinned
    # on its own base; code strings and formatter args).
    # old -> new: G1 the filter mask code (8c7b23d4...); G2 dp
    # (77a8a775...); C16 the recast writer in the filter code
    # (b02f3e94...); C11 lpoly's 1e-14 weight threshold in the filter code
    # (8fb420d4...); G7 the Stata writer reads %d as %td (965dbdfe...)
    # and %tb through its calendar (43f70b01...); D35 the rule-of-thumb
    # constants to pe 31 in the filter code (8848eb94...); H2f the mask's
    # multi and (missing) branches (code only) and the filter row's Reset
    # filters button with its fixed script, the same under both Pythons
    # (96f4d27b...); H2f the filter code's hold and the reset's one run
    # (code and the reset's callback arg), the same under both Pythons
    # (5236a3eb...); H2k the KPI recompute's weights (the filter and brush
    # code) and kpi_config's wvar and wkind keys -- the base's _FILTER_JS
    # and config without the two keys give the old digest on the new tree
    # -- the same under both Pythons; H2l's link groups and brush views;
    # H1 the filter code's try block and twins, the error status Div and
    # its callback arg, the brush code's guard and the window hooks (a
    # dropdown page: no slider); re-derived on the merged batch-17 tree
    # with H1's follow-ups (the fill rebuild's twins in the filter code),
    # the same under both Pythons; b7968590... -> 9aecdc39...: WP-31 H2x
    # the grid's composite export actions (model ids masked by _digest),
    # the print hide stylesheet on the toolbar and the filter, the same
    # under both Pythons
    # the same under both Pythons; b796859... -> 713839d1...: K6 the
    # figure's role="img" and name, the dropdown's and Reset filters'
    # role="group" and name (html_attributes), the same under both Pythons
    # Merged batch 18 (H2x, K6, H3/H4): re-derived on the merged tree;
    # 8af16d2e... -> c2ebbb94...: the batch-18 gate, the composite code's
    # entity table keyed by name, the same under both Pythons.
    # c2ebbb94... -> e3a57293...: WP-31 K6 follow-up, a figure with a
    # toolbar is role="group", not "img" (axe nested-interactive); the
    # same under both Pythons.
    "e3a572938eb8ee5bec3c0ec858c4172371032cdf4661b683895fccad1890042e")


# ===========================================================================
class TestEstimatorMemo:

    def test_hits_misses_and_bit_equal_results(self):
        st = _state()
        calls = []

        def lw(x, y, bw=0.8, mean=False, noweight=False):
            calls.append(1)
            return x * (bw[0] if isinstance(bw, list) else bw), np.where(np.isnan(y), np.nan, y + (1 if mean else 0)
                                    + (2 if noweight else 0))
        f = dr._dash_memo_wrap(lw, "lw", st)
        x = np.arange(5.0)
        y = np.array([1.0, np.nan, 3.0, -0.0, 5.0])
        first = f(x, y, 0.8)
        again = f(x, y, 0.8)
        assert len(calls) == 1
        assert all(a.tobytes() == b.tobytes() for a, b in zip(first, again))
        again[0][0] = 99.0                  # a caller's copy, not the memo's
        assert f(x, y, 0.8)[0][0] == 0.0
        for args, kw in (((x + 1, y, 0.8), {}), ((x, y, 0.5), {}),
                         ((x, y, 0.8), {"mean": True}),
                         ((x, y, 0.8), {"noweight": True})):
            n = len(calls)
            f(*args, **kw)
            assert len(calls) == n + 1, (args, kw)
        f(x, y, [0.8])                      # not memoised: a list argument
        f(x, y, [0.8])
        assert len(calls) == 7

    def test_method_leaves_the_class_out_of_the_key(self):
        st = _state()
        calls = []

        def fp(cls, x):
            calls.append(cls)
            return {"beta": x.copy()}
        f = dr._dash_memo_wrap(fp, "fp", st, method=True)
        f("A", np.ones(3))
        f("B", np.ones(3))
        assert calls == ["A"]

    def test_budget_evicts_lru(self, monkeypatch):
        monkeypatch.setattr(dr, "_DASH_MEMO_BYTES", 3 * (8000 + 64))
        st = _state()
        f = dr._dash_memo_wrap(lambda k: np.zeros(1000) + k, "z", st)
        for k in range(3):
            f(k)
        f(0)                                 # 0 is now the most recent
        f(3)                                 # evicts 1
        assert st.memo_bytes == sum(s for _v, s in st.memo.values())
        assert st.memo_bytes <= dr._DASH_MEMO_BYTES and len(st.memo) == 3
        keys = {dr._dash_memo_key("z", (k,), {}) for k in (0, 2, 3)}
        assert set(st.memo) == keys

    def test_the_lock_guards_get_and_put(self, monkeypatch):
        monkeypatch.setattr(dr, "_DASH_MEMO_BYTES", 6 * (800 + 64))
        st = _state()
        f = dr._dash_memo_wrap(lambda k: np.zeros(100) + k, "z", st)
        errors = []

        def run(seed):
            rng = np.random.default_rng(seed)
            try:
                for k in rng.integers(0, 12, 250):
                    if f(int(k))[0] != k:
                        errors.append(int(k))
            except RuntimeError as e:      # OrderedDict mutated
                errors.append(e)
        ts = [threading.Thread(target=run, args=(i,)) for i in range(8)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        assert not errors
        assert st.memo_bytes == sum(s for _v, s in st.memo.values())
        assert st.memo_bytes <= dr._DASH_MEMO_BYTES

    def test_never_in_stata_or_a_trial(self, monkeypatch):
        st = _state()
        f = dr._dash_memo_wrap(lambda k: np.zeros(3) + k, "z", st)
        monkeypatch.setitem(sys.modules, "sfi", types.ModuleType("sfi"))
        f(1)
        assert not st.memo
        monkeypatch.delitem(sys.modules, "sfi")
        monkeypatch.setitem(dr.__dict__, dr._DASH_TRIAL_FLAG, True)
        f(1)
        assert not st.memo

    def test_the_app_memoises_and_the_saved_renderer_is_untouched(
            self, lowess_ns):
        st = _reset(lowess_ns)
        gm = lowess_ns["GlyphMapper"]
        assert getattr(gm._stata_lowess, "_dash_memo_of", None)
        assert getattr(gm._fp_fit, "_dash_memo_of", None)
        _make(lowess_ns, Document())
        keys = set(st.memo)
        assert keys
        _make(lowess_ns, Document())
        assert set(st.memo) == keys
        assert not hasattr(dr.GlyphMapper._stata_lowess, "_dash_memo_of")
        assert not hasattr(dr.GlyphMapper._fp_fit, "_dash_memo_of")
        _reset(lowess_ns)


# ===========================================================================
# WP-31 H3: the served bundle leaves out Bokeh's MathJax component.  Bokeh's
# server writes every component (``bundle_for_objs_and_resources(None, ...)``
# forces them all on), so a served session fetched bokeh-mathjax (1.79 MB)
# though dash breaks every TeX pair (_dash_inert_tex) and never uses it.
# ===========================================================================
def _server_page(template):
    """The page Bokeh's server writes: its own bundle of server resources
    (``server_html_page_for_session``'s two calls), with ``template``."""
    from bokeh.embed.bundle import bundle_for_objs_and_resources
    from bokeh.embed.elements import html_page_for_render_items
    from bokeh.resources import Resources
    bundle = bundle_for_objs_and_resources(
        None, Resources(mode="server", root_url="/"))
    return html_page_for_render_items(bundle, {}, [], "dash",
                                      template=template)


def _script_srcs(page):
    import re
    return re.findall(r'<script[^>]*\bsrc="([^"]*)"', page)


class TestNoMathjax:
    def test_the_served_page_names_no_mathjax_script(self, ns):
        doc = _make(ns, _Served("s-mj"))
        page = _server_page(doc.template)
        assert _script_srcs(page)
        assert "bokeh-mathjax" not in page

    def test_the_renderers_template_names_none_either(self):
        page = _server_page(dr._dash_served_template())
        assert "bokeh-mathjax" not in page

    def test_every_other_component_is_present(self):
        from bokeh.resources import Resources
        want = [c for c in Resources(mode="server").components
                if c != "bokeh-mathjax"]
        srcs = _script_srcs(_server_page(dr._dash_served_template()))
        names = [s.rsplit("/", 1)[-1].split(".")[0] for s in srcs]
        assert names == want

    def test_only_a_mathjax_element_is_dropped(self):
        tag = '<script type="text/javascript" src="/static/js/%s.min.js">' \
              '</script>'
        text = "\n".join(tag % c for c in ("bokeh", "bokeh-mathjax",
                                           "bokeh-tables"))
        out = str(dr._dash_drop_mathjax(text))
        assert out.count("<script") == 2
        assert "bokeh-mathjax" not in out and "bokeh-tables" in out
        inline = '<script type="text/javascript">var a = "bokeh-mathjax";' \
                 '</script>'
        assert str(dr._dash_drop_mathjax(inline)) == inline
