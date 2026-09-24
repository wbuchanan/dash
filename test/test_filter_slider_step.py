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
    # A step of zero moves the handle nowhere.  This returned inf for it,
    # which passed every ">= 50" below (Bokeh accepts step=0; measured
    # 24sep2026).
    assert step > 0, f"the widget's step is {w.step!r}"
    return _span_days(w) / step


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
        # The target is the numeric path's hundred: step = span / 100, in
        # whole milliseconds (846000 here, measured 24sep2026).  ">= 50"
        # alone let the count fall by nearly half.
        assert _notches(w) == pytest.approx(100.0), (
            f"{_notches(w):.2f} notches at step={w.step}"
        )

    def test_a_clock_filter_may_step_below_a_day(self):
        dr = _render(_CLOCK, "%tc")
        # The widget is typed in milliseconds, so compare in days -- and a
        # step of zero is below a day too, so it must be positive.
        assert 0 < _step_days(dr.filter_widgets[0]) < 1.0

    def test_the_slider_form_too(self):
        dr = _render(_CLOCK, "%tc", ftype="slider")
        w = dr.filter_widgets[0]
        assert _notches(w) >= 50, (
            f"{_notches(w):.1f} notches at step={w.step}"
        )
        assert _notches(w) == pytest.approx(100.0), (
            f"{_notches(w):.2f} notches at step={w.step}"
        )


class TestACalendarFilterStepsInWholeDays:
    """A fraction of a day is not a value a %td variable can take."""

    #: kind -> (span of the fixture's 120 periods, in days; the step): a
    #: hundredth of the span rounded to whole days, at least one.  Measured
    #: 24sep2026.
    _STEPS = {"td": (119.0, 1), "tw": (836.0, 8), "tm": (3621.0, 36),
              "tq": (10865.0, 109), "th": (21731.0, 217)}

    @pytest.mark.parametrize("kind", ["td", "tw", "tm", "tq", "th"])
    def test_the_step_is_a_whole_number_of_days(self, kind):
        """Whole days, and the hundredth of the span that makes them.

        ``step >= 1'' and ``step == int(step)'' held for any whole step:
        measured 24sep2026, all five passed with a fiftieth of the span
        (2, 17, 72, 217 and 435 days).  Each step is pinned, with the span
        it is a hundredth of.
        """
        dr = _render(_calendar_values(kind), "%" + kind)
        w = dr.filter_widgets[0]
        span, want = self._STEPS[kind]
        assert type(w).__name__ == "DateRangeSlider", type(w).__name__
        assert _span_days(w) == span, (kind, _span_days(w))
        step = float(w.step)
        assert step == want == max(1, round(span / 100.0)), (
            f"{kind}: step {step} for a {span:.0f}-day span")

    def test_a_long_monthly_series_is_not_stepped_one_day_at_a_time(self):
        """The hundred notches the numeric path gives, in whole days.

        ``step > 1'' let the step fall anywhere above a day: measured
        24sep2026, it passed with a step of 4 days -- 905 notches, a
        thousandth of the span instead of a hundredth.  The span is 2010m1
        to 2019m12, 3621 days; a hundredth of it is 36.21, a whole 36 days,
        100.6 notches (measured the same day).
        """
        dr = _render(_MONTHLY, "%tm")
        w = dr.filter_widgets[0]
        assert type(w).__name__ == "DateRangeSlider", type(w).__name__
        assert _span_days(w) == 3621.0, _span_days(w)
        assert float(w.step) == 36.0, (
            f"a {_span_days(w):.0f}-day span stepped {w.step} days at a time "
            f"has {_notches(w):.1f} notches"
        )
        assert _notches(w) == pytest.approx(100.0, abs=1.0)

    def test_a_short_daily_series_still_steps_one_day(self):
        """Flooring must not coarsen a range that is already fine."""
        dr = _render(_DAILY, "%td")
        assert float(dr.filter_widgets[0].step) == 1.0


class TestTheNumericPathIsUnchanged:

    def test_a_numeric_range_still_gets_a_hundredth_of_the_span(self):
        """A hundredth of the DATA's span, 1760 to 4840.

        This compared the step with the widget's own bounds, so bounds and a
        step wrong together passed: measured 24sep2026, it passed with the
        widget spanning 0 to 4840 at a step of 48.4.
        """
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
        assert type(w).__name__ == "RangeSlider", type(w).__name__
        assert (float(w.start), float(w.end)) == (1760.0, 4840.0)
        assert float(w.step) == pytest.approx((4840.0 - 1760.0) / 100.0)
