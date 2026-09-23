"""A served filter move reran every aggregated layer, and nothing throttled it.

BUGS.md, "lowess and fpfit cost more than they need to on large data, and a
served filter move reruns them unthrottled".  Measured: ``_stata_lowess``
takes 4.8 s at 20k rows and fpfit about 2 s at 1e6 rows, and the served app
reruns both -- per layer and per by() panel -- on every filter-widget change:

* a RangeSlider drag fires a ``value`` change on every mouse move, so one
  drag queued dozens of full recomputes;
* a scripted websocket client can send value changes as fast as it likes;
* the server is one process, so while a recompute runs every other session
  waits.

Two changes, tested here:

* a slider recomputes when the drag ENDS -- it is wired to
  ``value_throttled``, which changes once, on release -- and the dropdown
  keeps ``value``;
* every filter and brush callback goes through ``_dash_event_throttle``, a
  token bucket per callback per session: ``burst`` events run at once,
  refilled at ``rate`` per second, and whatever arrives while the bucket is
  empty is folded into ONE trailing call carrying the latest arguments.
"""
import importlib.util
import inspect
import itertools
import json
import os
import sys
import textwrap
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Div, RangeSlider, Select, Slider
from bokeh.server.callbacks import TimeoutCallback

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, make_spec

_SEQ = itertools.count()

#: Ten cars.  mean(mpg) is 21.50 overall, 19.60 domestic, 23.40 foreign and
#: 20.50 for price in [3799, 4500].
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
})
_SCATTER = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}
_DROPDOWN = {"varname": "foreign", "type": "dropdown"}
_RANGE = {"varname": "price", "type": "range"}
_SLIDER = {"varname": "weight", "type": "slider"}


def _kpi(update="filter"):
    return {"name": "k1", "stat": "mean", "var": "mpg", "fmt": "%9.2f",
            "title": "Mean mpg", "subtitle": "", "color": "", "bgcolor": "",
            "update": update, "if_expr": "", "in_expr": ""}


# ---------------------------------------------------------------------------
# Unit tests of the bucket, with a fake document and a fake clock
# ---------------------------------------------------------------------------

class _FakeDoc:
    """Records ``add_timeout_callback(fn, ms)`` instead of scheduling it."""

    def __init__(self):
        self.scheduled = []

    def add_timeout_callback(self, fn, ms):
        self.scheduled.append((fn, ms))
        return object()


class _FakeClock:
    """A clock that moves only when the test moves it."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class _Recorder:
    """The callback being throttled: records every call, raises on request."""

    def __init__(self):
        self.calls = []
        self.fail = False

    def __call__(self, attr, old, new):
        self.calls.append((attr, old, new))
        if self.fail:
            raise RuntimeError("the recompute failed")


def _throttle(**kw):
    fn, doc, clock = _Recorder(), _FakeDoc(), _FakeClock()
    cb = dr._dash_event_throttle(doc, fn, clock=clock, **kw)
    return cb, fn, doc, clock


class TestTheDefaults:
    def test_the_defaults_are_two_per_second_and_a_burst_of_ten(self):
        assert dr._DASH_EVENT_RATE == 2.0
        assert dr._DASH_EVENT_BURST == 10

    def test_the_defaults_are_read_from_the_module_constants(
            self, monkeypatch):
        monkeypatch.setattr(dr, "_DASH_EVENT_BURST", 4)
        monkeypatch.setattr(dr, "_DASH_EVENT_RATE", 8.0)
        cb, fn, doc, clock = _throttle()
        for i in range(5):
            cb("value", None, i)
        assert len(fn.calls) == 4
        (_run, ms), = doc.scheduled
        assert abs(ms - 125) <= 1, ms

    def test_the_clock_defaults_to_time_monotonic(self, monkeypatch):
        import time
        fake = _FakeClock()
        monkeypatch.setattr(time, "monotonic", fake)
        fn, doc = _Recorder(), _FakeDoc()
        cb = dr._dash_event_throttle(doc, fn)
        for i in range(11):
            cb("value", None, i)
        assert len(fn.calls) == 10 and len(doc.scheduled) == 1
        fake.advance(10.0)
        run, _ms = doc.scheduled[0]
        run()
        cb("value", None, "refilled")
        assert fn.calls[-1] == ("value", None, "refilled"), (
            "the default clock is not time.monotonic: moving it did not "
            "refill the bucket"
        )

    @pytest.mark.parametrize("kw", [{"rate": 0}, {"rate": -1.0},
                                    {"rate": float("nan")}, {"burst": 0},
                                    {"burst": 0.5}])
    def test_a_bucket_that_could_never_hold_a_token_is_refused(self, kw):
        with pytest.raises(ValueError):
            dr._dash_event_throttle(_FakeDoc(), _Recorder(),
                                    clock=_FakeClock(), **kw)

    def test_it_is_a_bokeh_on_change_callback(self):
        """Bokeh checks an on_change callback's signature on registration
        and then calls it with (attr, old, new)."""
        cb, fn, _doc, _clock = _throttle()
        w = Select(options=["a", "b"], value="a")
        w.on_change("value", cb)
        w.value = "b"
        assert fn.calls == [("value", "a", "b")]


class TestTheBurst:
    def test_it_runs_immediately_within_the_burst(self):
        cb, fn, doc, _clock = _throttle()
        for i in range(10):
            cb("value", i, i + 1)
        assert fn.calls == [("value", i, i + 1) for i in range(10)]
        assert doc.scheduled == []

    def test_the_event_after_the_burst_is_scheduled_once_for_the_next_token(
            self):
        cb, fn, doc, _clock = _throttle()
        for i in range(10):
            cb("value", None, i)
        cb("value", None, "late")
        assert len(fn.calls) == 10, "the event past the burst ran at once"
        assert len(doc.scheduled) == 1
        run, ms = doc.scheduled[0]
        assert callable(run)
        # The bucket is empty and the clock has not moved: the next token is
        # 1 / rate seconds away.
        assert ms > 0
        assert abs(ms - 500) <= 1, ms

    def test_the_delay_counts_a_partly_refilled_token(self):
        cb, fn, doc, clock = _throttle()
        for i in range(10):
            cb("value", None, i)
        clock.advance(0.2)                  # 0.4 of a token at 2 a second
        cb("value", None, "late")
        (_run, ms), = doc.scheduled
        assert abs(ms - 300) <= 1, ms

    def test_a_thousand_further_events_add_no_second_schedule(self):
        cb, fn, doc, _clock = _throttle()
        for i in range(10 + 1 + 1000):
            cb("value", None, i)
        assert len(fn.calls) == 10
        assert len(doc.scheduled) == 1, (
            f"{len(doc.scheduled)} trailing calls were scheduled; every event "
            f"after the first must be folded into it"
        )


class TestTheTrailingCall:
    def _flooded(self):
        cb, fn, doc, clock = _throttle()
        for i in range(10):
            cb("value", None, i)
        for i in range(1001):
            cb("value", ("old", i), ("new", i))
        (run, ms), = doc.scheduled
        return cb, fn, doc, clock, run, ms

    def test_it_calls_fn_once_with_the_latest_arguments(self):
        _cb, fn, doc, clock, run, ms = self._flooded()
        clock.advance(ms / 1000.0)
        run()
        assert len(fn.calls) == 11
        assert fn.calls[-1] == ("value", ("old", 1000), ("new", 1000))
        assert len(doc.scheduled) == 1, "running it scheduled another"

    def test_it_spends_the_token_it_waited_for(self):
        """After it runs the bucket continues from its state: empty, so the
        next event is scheduled rather than run."""
        cb, fn, doc, clock, run, ms = self._flooded()
        clock.advance(ms / 1000.0)
        run()
        cb("value", None, "straight after")
        assert len(fn.calls) == 11
        assert len(doc.scheduled) == 2
        assert abs(doc.scheduled[1][1] - 500) <= 1, doc.scheduled[1][1]

    def test_events_run_immediately_again_once_the_clock_has_advanced(self):
        cb, fn, doc, clock, run, ms = self._flooded()
        clock.advance(ms / 1000.0)
        run()
        clock.advance(0.5)                  # one token
        cb("value", None, "later")
        assert fn.calls[-1] == ("value", None, "later")
        assert len(doc.scheduled) == 1
        clock.advance(5.0)                  # a full bucket
        for i in range(10):
            cb("value", None, i)
        assert len(fn.calls) == 12 + 10
        assert len(doc.scheduled) == 1


class TestAnExceptionInTheCallback:
    def test_it_propagates_and_the_next_event_still_runs(self):
        cb, fn, doc, _clock = _throttle()
        fn.fail = True
        with pytest.raises(RuntimeError):
            cb("value", None, 1)
        fn.fail = False
        cb("value", None, 2)
        assert [c[2] for c in fn.calls] == [1, 2]
        assert doc.scheduled == []

    def test_one_in_the_trailing_call_leaves_the_throttle_usable(self):
        """The pending flag is cleared before fn runs, so an event after a
        failed trailing call starts a new one instead of vanishing into a
        call that already happened."""
        cb, fn, doc, clock = _throttle()
        for i in range(11):
            cb("value", None, i)
        run, ms = doc.scheduled[0]
        clock.advance(ms / 1000.0)
        fn.fail = True
        with pytest.raises(RuntimeError):
            run()
        fn.fail = False
        cb("value", None, "next")
        assert len(doc.scheduled) == 2, "the event after the failure was lost"
        run2, ms2 = doc.scheduled[1]
        assert abs(ms2 - 500) <= 1, ms2
        clock.advance(ms2 / 1000.0)
        run2()
        assert fn.calls[-1] == ("value", None, "next")
        clock.advance(0.5)
        cb("value", None, "now")
        assert fn.calls[-1] == ("value", None, "now")
        assert len(doc.scheduled) == 2


class TestExplicitSettings:
    def test_an_explicit_burst_overrides_the_default(self):
        cb, fn, doc, _clock = _throttle(burst=3)
        for i in range(4):
            cb("value", None, i)
        assert len(fn.calls) == 3
        assert len(doc.scheduled) == 1

    def test_an_explicit_rate_overrides_the_default(self):
        cb, fn, doc, _clock = _throttle(rate=4.0)
        for i in range(11):
            cb("value", None, i)
        assert len(fn.calls) == 10
        (_run, ms), = doc.scheduled
        assert abs(ms - 250) <= 1, ms

    def test_both_together(self):
        cb, fn, doc, clock = _throttle(rate=1.0, burst=2)
        for i in range(3):
            cb("value", None, i)
        assert len(fn.calls) == 2
        (run, ms), = doc.scheduled
        assert abs(ms - 1000) <= 1, ms
        clock.advance(1.0)
        run()
        assert fn.calls[-1] == ("value", None, 2)


# ---------------------------------------------------------------------------
# The generated app
# ---------------------------------------------------------------------------

def _app(tmp_path, filters=None, kpis=None):
    """(module, path): the generated app for one scatter of mpg on weight."""
    tag = next(_SEQ)
    spec = make_spec([dict(_SCATTER)], filters=filters, kpis=kpis)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    ap = tmp_path / f"a_{tag}.py"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_throttle_app_{tag}",
                                                    str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    return mod, ap


def _session(mod, fake_clock=None, wrapped=None):
    """One served session: a fresh Document through the app's make_document.

    With *fake_clock*, every throttle make_document builds reads it -- the
    helper's ``clock`` argument exists for this -- so "at most ``burst`` at
    once" is exact instead of a race with the machine's speed.  With
    *wrapped*, every callback the throttle hands back is appended to it.
    make_document itself, and the rate and burst it asks for, are untouched.
    """
    real = mod._dash_event_throttle

    def _throttle_in_test(doc, fn, rate=None, burst=None, clock=None):
        cb = real(doc, fn, rate, burst,
                  fake_clock if fake_clock is not None else clock)
        if wrapped is not None:
            wrapped.append(cb)
        return cb

    mod._dash_event_throttle = _throttle_in_test
    doc = Document()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod.make_document(doc)
    finally:
        mod._dash_event_throttle = real
    return doc


def _plain_session(mod):
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod.make_document(doc)
    return doc


def _widget(doc, cls):
    found = [m for m in doc.select({"type": cls}) if type(m) is cls]
    assert len(found) == 1, f"expected one {cls.__name__}, found {len(found)}"
    return found[0]


def _timeouts(doc):
    return [c for c in doc.session_callbacks if isinstance(c, TimeoutCallback)]


def _kpi_text(doc):
    return " ".join(d.text for d in doc.select({"type": Div}))


def _rendered_sources(doc):
    out = []
    for m in doc.select({"type": object}):
        src = getattr(m, "data_source", None)
        if isinstance(src, ColumnDataSource) and src not in out:
            out.append(src)
    return out


def _count_recomputes(mod):
    """Every recompute, filter or brush, computes the one KPI once: count the
    calls from here on, through the app's own namespace."""
    calls = []
    real = mod._compute_kpi

    def _counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    mod._compute_kpi = _counting
    return calls


class TestTheAppCarriesTheThrottle:
    def test_the_app_defines_the_helper_and_its_constants(self, tmp_path):
        mod, ap = _app(tmp_path, filters=[_DROPDOWN])
        assert callable(getattr(mod, "_dash_event_throttle", None)), (
            "the served app has no _dash_event_throttle; make_document's "
            "call to it is a NameError on the served page"
        )
        assert mod._DASH_EVENT_RATE == dr._DASH_EVENT_RATE
        assert mod._DASH_EVENT_BURST == dr._DASH_EVENT_BURST

    def test_the_helper_is_the_renderers_own_text(self, tmp_path):
        """Copied by inspect.getsource like every shared served helper, so
        the throttle the tests above exercise is the one that is served."""
        _mod, ap = _app(tmp_path, filters=[_DROPDOWN])
        src = ap.read_text(encoding="utf-8")
        own = textwrap.dedent(inspect.getsource(dr._dash_event_throttle))
        assert own.rstrip("\n") in src


class TestSlidersRecomputeWhenTheDragEnds:
    @pytest.mark.parametrize("filt, cls", [(_RANGE, RangeSlider),
                                           (_SLIDER, Slider)],
                             ids=["range", "slider"])
    def test_a_slider_is_wired_to_value_throttled_and_not_value(
            self, tmp_path, filt, cls):
        mod, _ap = _app(tmp_path, filters=[filt])
        w = _widget(_plain_session(mod), cls)
        assert w._callbacks.get("value_throttled"), (
            f"the {cls.__name__} has no value_throttled callback"
        )
        assert not w._callbacks.get("value"), (
            f"the {cls.__name__} still recomputes on every mouse move of a "
            f"drag: its callback is under `value'"
        )

    def test_a_dropdown_keeps_value(self, tmp_path):
        mod, _ap = _app(tmp_path, filters=[_DROPDOWN])
        w = _widget(_plain_session(mod), Select)
        assert w._callbacks.get("value"), "the Select has no value callback"
        assert "value_throttled" not in w.properties()

    def test_a_drag_recomputes_once_when_it_ends(self, tmp_path):
        """What a browser sends, applied the way the server applies it:
        ``value`` on every mouse move, then ``value_throttled`` on release.
        The one recompute reads the slider's final position."""
        mod, _ap = _app(tmp_path, filters=[_RANGE], kpis=[_kpi()])
        doc = _session(mod, fake_clock=_FakeClock())
        w = _widget(doc, RangeSlider)
        recomputes = _count_recomputes(mod)
        lo = float(w.start)
        for hi in np.linspace(float(w.end), 4500.0, 50):
            w.set_from_json("value", [lo, float(hi)])
        assert recomputes == [], (
            f"a drag of 50 mouse moves ran {len(recomputes)} recomputes "
            f"before it ended"
        )
        w.set_from_json("value_throttled", [lo, 4500.0])
        assert len(recomputes) == 1
        assert "20.50" in _kpi_text(doc), _kpi_text(doc)


class TestAFloodOfFilterChangesIsThrottled:
    def test_a_thousand_select_changes_run_at_most_burst_recomputes(
            self, tmp_path):
        mod, _ap = _app(tmp_path, filters=[_DROPDOWN], kpis=[_kpi()])
        clock = _FakeClock()
        doc = _session(mod, fake_clock=clock)
        w = _widget(doc, Select)
        (cb,) = w._callbacks["value"]
        recomputes = _count_recomputes(mod)
        for _ in range(1000):
            cb("value", w.value, w.value)
        assert len(recomputes) <= mod._DASH_EVENT_BURST, (
            f"1,000 changes ran {len(recomputes)} full recomputes"
        )
        assert len(recomputes) == mod._DASH_EVENT_BURST
        pending = _timeouts(doc)
        assert len(pending) == 1, (
            f"{len(pending)} trailing calls were scheduled on the document"
        )
        clock.advance(pending[0].timeout / 1000.0)
        pending[0].callback()
        assert len(recomputes) == mod._DASH_EVENT_BURST + 1
        assert _timeouts(doc) == []

    def test_a_client_flood_ends_on_the_last_value_it_sent(self, tmp_path):
        """A scripted client's patches, applied as the server applies them.
        The burst ends on Foreign; the last value sent is Domestic, and the
        trailing recompute must show Domestic."""
        mod, _ap = _app(tmp_path, filters=[_DROPDOWN], kpis=[_kpi()])
        clock = _FakeClock()
        doc = _session(mod, fake_clock=clock)
        w = _widget(doc, Select)
        values = {label: v for v, label in w.options}
        domestic, foreign = values["0"], values["1"]
        recomputes = _count_recomputes(mod)
        for i in range(1001):
            w.set_from_json("value", foreign if i % 2 else domestic)
        assert len(recomputes) == mod._DASH_EVENT_BURST
        assert "23.40" in _kpi_text(doc), _kpi_text(doc)
        (pending,) = _timeouts(doc)
        clock.advance(pending.timeout / 1000.0)
        pending.callback()
        assert len(recomputes) == mod._DASH_EVENT_BURST + 1
        assert "19.60" in _kpi_text(doc), (
            "the trailing recompute did not read the dropdown's final value: "
            + _kpi_text(doc)
        )


class TestTheBrushIsThrottled:
    def test_a_thousand_selections_run_at_most_burst_and_the_last_wins(
            self, tmp_path):
        mod, _ap = _app(tmp_path, kpis=[_kpi(update="brush")])
        clock = _FakeClock()
        doc = _session(mod, fake_clock=clock)
        src = next(s for s in _rendered_sources(doc)
                   if s.selected._callbacks.get("indices"))
        (cb,) = src.selected._callbacks["indices"]
        recomputes = _count_recomputes(mod)
        n = len(src.data["index"])
        for i in range(1000):
            cb("indices", [], [i % n])
        cb("indices", [], [3, 7])
        assert len(recomputes) == mod._DASH_EVENT_BURST, (
            f"1,001 selections ran {len(recomputes)} recomputes"
        )
        (pending,) = _timeouts(doc)
        clock.advance(pending.timeout / 1000.0)
        pending.callback()
        assert len(recomputes) == mod._DASH_EVENT_BURST + 1
        ids = [src.data["index"][3], src.data["index"][7]]
        want = f"{_DF.loc[ids, 'mpg'].mean():.2f}"
        assert want in _kpi_text(doc), (
            f"the trailing brush recompute did not use the last selection "
            f"(mean {want}): {_kpi_text(doc)}"
        )


class TestEveryCallbackGoesThroughTheThrottle:
    def test_every_filter_and_brush_callback_is_a_throttle(self, tmp_path):
        mod, _ap = _app(tmp_path, filters=[_DROPDOWN, _RANGE, _SLIDER],
                        kpis=[_kpi(update="both")])
        wrapped = []
        doc = _session(mod, fake_clock=_FakeClock(), wrapped=wrapped)
        widgets = [m for m in doc.select({"type": object})
                   if hasattr(m, "_dash_var")]
        assert len(widgets) == 3, widgets
        for w in widgets:
            attr = ("value_throttled" if "value_throttled" in w.properties()
                    else "value")
            cbs = w._callbacks.get(attr, [])
            assert cbs and all(c in wrapped for c in cbs), (
                f"the {type(w).__name__} callback is not throttled"
            )
        brushed = [s for s in _rendered_sources(doc)
                   if s.selected._callbacks.get("indices")]
        assert brushed, "no brush callback was wired"
        for s in brushed:
            assert all(c in wrapped for c in s.selected._callbacks["indices"])
