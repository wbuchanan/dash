"""test_filter_slider_step.py — a date filter had one reachable notch.

The numeric sliders were fine: ``step = (vmax - vmin) / 100``, so any range
gets a hundred notches. The date sliders computed the same ``vstep`` and then
**never passed it**, so they kept Bokeh's default.

Bokeh's ``DateSlider.step`` and ``DateRangeSlider.step`` are *in units of
days*, and the default is ``1``. So:

  * a ``%tc`` clock variable spanning a single day got **one** notch — the
    slider could not be moved to any useful position;
  * a ``%tm`` monthly series got a step of one day, two orders of magnitude
    finer than any value in the data.

Both are derived from the span here, targeting the same hundred notches the
numeric path gives. A calendar-date variable (``%td`` and the coarser
``%tw %tm %tq %th %ty``) is floored at one whole day, because a fraction of a
day is not a value those variables can take; a clock variable (``%tc``,
``%tC``) is allowed to step below a day, which is the whole point of it.
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json

_MS_DAY = 86_400_000.0


def _render(values, fmt, ftype="range"):
    """Render one date filter.

    ``values`` are Stata SIF values in the unit ``fmt`` implies -- days since
    1960 for %td, months for %tm, milliseconds for %tc -- not epoch
    milliseconds.  Getting that wrong puts every value outside the range the
    renderer can represent, the column is dropped to missing, and the widget
    silently falls back to a numeric RangeSlider, which proves nothing.
    """
    df = pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, len(values)),
        "when": np.array(values, dtype=float),
    })
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "when",
                       "options": {}}])
    spec["build_options"]["filters"] = [
        {"varname": "when", "type": ftype, "exclude": [], "label": ""}]
    spec["build_options"]["formats"] = {"when": fmt}
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr


def _span_days(w):
    return (float(w.end) - float(w.start)) / _MS_DAY


def _step_days(w):
    """The widget's step expressed in days, whatever unit it is typed in.

    Bokeh types DateSlider/DateRangeSlider step in DAYS and
    DatetimeRangeSlider (and a plain Slider over epoch ms) in MILLISECONDS.
    """
    cls = type(w).__name__
    if cls in ("DateSlider", "DateRangeSlider"):
        return float(w.step)
    return float(w.step) / _MS_DAY


def _notches(w):
    """How many positions the user can actually move the handle to."""
    step = _step_days(w)
    return _span_days(w) / step if step else float("inf")


# --- fixtures in Stata SIF units ---
# %tc: milliseconds since 1960-01-01.  One day of readings, 30 min apart.
_TC_BASE = 1_500_000_000_000.0
_CLOCK = [_TC_BASE + i * 1_800_000.0 for i in range(48)]
# %tm: months since 1960-01-01.  Ten years from 2010m1.
_MONTHLY = [600.0 + i for i in range(120)]
# Each calendar kind counts a different period from 1960, so a single list of
# numbers is only valid for one of them: 600 months is 2010, but 600
# half-years is 2260, past the range pandas can represent.
_CALENDAR_START = {"td": 20000.0, "tw": 2800.0, "tm": 600.0,
                   "tq": 200.0, "th": 100.0, "ty": 2010.0}


def _calendar_values(kind, n=120):
    start = _CALENDAR_START[kind.lstrip("%")]
    return [start + i for i in range(n)]
# %td: days since 1960-01-01.  Two months from about 2014.
_DAILY = [20000.0 + i for i in range(60)]


class TestBokehsDefaultIsTheProblem:
    """State the premise, so the test notices if Bokeh changes it."""

    def test_the_date_step_default_is_one_day(self):
        from bokeh.models import DateRangeSlider, DateSlider
        for cls in (DateSlider, DateRangeSlider):
            assert cls.lookup("step").property._default == 1, cls.__name__


class TestAClockFilterIsUsable:

    def test_a_single_day_of_clock_time_has_many_notches(self):
        dr = _render(_CLOCK, "%tc")
        assert dr.filter_widgets, "no filter widget was built"
        w = dr.filter_widgets[0]
        assert _span_days(w) < 2.0, (
            f"the fixture should span under a day; it spans {_span_days(w)}"
        )
        assert _notches(w) >= 50, (
            f"a clock filter spanning {_span_days(w):.3f} days has only "
            f"{_notches(w):.1f} notches at step={w.step}"
        )

    def test_a_clock_filter_may_step_below_a_day(self):
        dr = _render(_CLOCK, "%tc")
        # The widget is typed in milliseconds, so compare in days.
        assert _step_days(dr.filter_widgets[0]) < 1.0

    def test_the_slider_form_too(self):
        dr = _render(_CLOCK, "%tc", ftype="slider")
        w = dr.filter_widgets[0]
        assert _notches(w) >= 50, (
            f"{_notches(w):.1f} notches at step={w.step}"
        )


class TestACalendarFilterStepsInWholeDays:
    """A fraction of a day is not a value a %td variable can take."""

    @pytest.mark.parametrize("kind", ["td", "tw", "tm", "tq", "th"])
    def test_the_step_is_a_whole_number_of_days(self, kind):
        dr = _render(_calendar_values(kind), "%" + kind)
        step = float(dr.filter_widgets[0].step)
        assert step >= 1.0, f"{kind}: step {step} is less than a day"
        assert step == int(step), f"{kind}: step {step} is not whole days"

    def test_a_long_monthly_series_is_not_stepped_one_day_at_a_time(self):
        dr = _render(_MONTHLY, "%tm")
        w = dr.filter_widgets[0]
        assert _span_days(w) > 1000, _span_days(w)
        assert float(w.step) > 1.0, (
            f"a {_span_days(w):.0f}-day span stepped one day at a time needs "
            f"{_span_days(w):.0f} drags to cross"
        )

    def test_a_short_daily_series_still_steps_one_day(self):
        """Flooring must not coarsen a range that is already fine."""
        dr = _render(_DAILY, "%td")
        assert float(dr.filter_widgets[0].step) == 1.0


class TestTheNumericPathIsUnchanged:

    def test_a_numeric_range_still_gets_a_hundredth_of_the_span(self):
        df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 20),
                           "weight": np.linspace(1760.0, 4840.0, 20)})
        spec = make_spec([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}])
        spec["build_options"]["filters"] = [
            {"varname": "weight", "type": "range", "exclude": [],
             "label": ""}]
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(df), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        w = dr.filter_widgets[0]
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert float(w.step) == pytest.approx(
            (float(w.end) - float(w.start)) / 100.0)
