"""
test_natscale_axes.py -- #N ticks on by() panels, log axes, date axes and
where natscale overflows, as twoway draws them.

The defect (BUGS.md, S3): "#N ticks miss twoway's on 3 of 264 measured
axes, and date axes, log axes and by() panels do not follow twoway's
rule".  Measured 24sep2026 with StataNow 19.5; every measurement is in
test/fixtures/natscale_axes_truth.json:

* by(): twoway ticks every panel on one scale, natscale over ALL the
  panels' data -- `twoway scatter mpg weight, by(foreign) ylabel(#5)' draws
  10(10)40 on both panels, whose own data run 12-34 and 14-41, and both
  panels' scales run 12 to 41 (`.Graph.graphs[k].yaxis1').  by(, yrescale)
  gives each panel its own, and dash honours it (WP-29 P0.2): its panels
  then tick per panel, 10(5)35 and 15(5)40, as
  test_by_scales.py::TestRescaleGivesEachPanelItsOwn::test_count_ticks_are_per_panel
  pins.
* yscale(log): the tickset's .trans is 0 -- #N on a log axis is linear
  natscale over the data (154 of 157 random ranges agree with dash's
  natscale model, the three misses being the model's own), drawn where a
  log axis can draw a tick: `yscale(log) ylabel(#5)' on auto's price is
  0(5000)15000, and twoway's 0 lands off the axis, so dash draws 5000,
  10000 and 15000.
* natscale overflows past 2^31 steps (tickset_g.class's "natscale fooled"
  branch): two observations 1e9 and 1e9+1 draw lo-1 and hi+1 (72 cases).
* A date axis is ticked by the compiled _tsnatscale (tickset_g.class's
  set_ticks, for %td %tw %tm %tq %th %ty; natscale for %tc): 280 of 280
  graphs drawn over random date ranges equal `_tsnatscale min max N'.
  dash follows a model fitted to 12,000 of its answers; the agreement it
  reaches is pinned below as a floor.
"""
import importlib.util
import itertools
import json
import math
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "natscale_axes_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_EPOCH = dr._STATA_EPOCH_UNIX_MS


def _expand(mn, mx, step, lst=None):
    if lst:
        return [float(v) for v in lst]
    if not step:
        return [float(mn)]
    out, i = [], 0
    while mn + i * step <= mx + 1e-9 * abs(step) and i < 5000:
        out.append(float(mn + i * step))
        i += 1
    return out


def _same(a, b, tol=1e-6):
    return a is not None and len(a) == len(b) and all(
        abs(x - y) <= tol * max(1.0, abs(y)) for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# natscale's overflow
# ---------------------------------------------------------------------------

class TestNatscaleOverflow:
    @pytest.mark.parametrize("row", _T["overflow"],
                             ids=lambda r: "%s+%s-%d" % (r[0], r[1] - r[0],
                                                         r[2]))
    def test_the_axis_twoway_draws(self, row):
        lo, hi, n, mn, mx, step = row
        got = dr._dash_natscale_ticks(lo, hi, n)
        assert _same(got, _expand(mn, mx, step), 1e-12), (got, mn, mx, step)


# ---------------------------------------------------------------------------
# log axes
# ---------------------------------------------------------------------------

class TestLogAxisTicks:
    def test_the_rule_is_linear_natscale_over_the_data(self):
        """dash's log ticks are its natscale ticks over the data, less the
        ones a log axis cannot draw; natscale is twoway's for 154 of the
        157 measured log axes (the model's own misses)."""
        ok = 0
        for lo, hi, n, mn, mx, step in _T["log"]:
            # Stata's own zero is sometimes 1.4e-17: a zero all the same.
            want = [v for v in _expand(mn, mx, step) if v > 1e-9 * step]
            got = dr._dash_axis_count_ticks(lo, hi, n, "log")
            ok += _same(got, want, 1e-9)
            lin = dr._dash_natscale_ticks(lo, hi, n)
            assert got == [v for v in lin if v > 0] or got is None
        assert ok >= 155, ok

    def test_price_under_yscale_log(self):
        assert dr._dash_axis_count_ticks(3291, 15906, 5, "log") == [
            5000.0, 10000.0, 15000.0]
        assert dr._dash_axis_count_ticks(3291, 15906, 6, "log") == [
            4000.0 + 2000 * i for i in range(7)]

    def test_no_tick_left_is_no_rule(self):
        """natscale(0.2, 0.9, 1) is minmax; a range whose ticks are all at
        or below zero leaves none, and the axis keeps Bokeh's."""
        assert dr._dash_axis_count_ticks(-5, -1, 5, "log") is None


# ---------------------------------------------------------------------------
# date axes
# ---------------------------------------------------------------------------

_UNITS = ("d", "w", "m", "q", "h", "y")


def _ts_cases(unit, rows):
    return [r for r in rows if r[0] == unit]


def _ts_agreement(unit, rows):
    ok = tot = 0
    for u, lo, hi, n, mn, mx, step, lst in _ts_cases(unit, rows):
        tot += 1
        ok += _same(dr._dash_tsnatscale_ticks(lo, hi, n, unit),
                    _expand(mn, mx, step, lst))
    return ok, tot


#: The model's agreement with _tsnatscale over the 2,000 random ranges per
#: unit (test/fixtures/natscale_axes_truth.json "tsnatscale"), measured when
#: the model was fitted; a change to the model may not lower it.
#: WP-30 P1.17b: %td 1042 -> 1161 and its sweeps 1939 -> 2038 when weekly
#: steps moved onto %tw week starts.
_TS_FLOOR = {"d": 1161, "w": 1162, "m": 1298, "q": 1194, "h": 1320,
             "y": 1955}
#: ... and over the sweeps (ts sweeps of hi from a fixed lo, n 3 to 11).
_TS_SWEEP_FLOOR = {"d": 2038, "w": 1466, "m": 5314, "q": 1677, "h": 701}


class TestDateAxisTicks:
    @pytest.mark.parametrize("unit", _UNITS)
    def test_agreement_with_tsnatscale(self, unit):
        ok, tot = _ts_agreement(unit, _T["tsnatscale"])
        assert tot == 2000
        assert ok >= _TS_FLOOR[unit], (unit, ok)

    @pytest.mark.parametrize("unit", ("d", "w", "m", "q", "h"))
    def test_agreement_over_the_sweeps(self, unit):
        ok, tot = _ts_agreement(unit, _T["tsnatscale_sweeps"])
        assert ok >= _TS_SWEEP_FLOOR[unit], (unit, ok, tot)

    def test_the_graphs_twoway_drew(self):
        """240 %td to %ty graphs over random ranges (each _tsnatscale's
        answer over its data, measured): the model draws 163 of them."""
        ok = 0
        for kind, lo, hi, n, mn, mx, step, lst in _T["date_graph"]:
            if kind == "c":
                continue
            ok += _same(dr._dash_tsnatscale_ticks(lo, hi, n, kind),
                        _expand(mn, mx, step, lst))
        assert ok >= 163, ok

    def test_the_models_parts(self):
        """Measured answers each part of the model reproduces: a range of
        one month under #6 extends to four ticks (sweep: 601 -> 599..602 at
        #5 is three extra); 600..700 #5 is 600(24)696; 1978..1985 #5 is
        1978(2)1986; the ladder puts 50 years on 2000."""
        assert dr._dash_ts_tiny(1093, 1094, 6, "m") == [1092.0, 1093.0,
                                                        1094.0, 1095.0]
        assert dr._dash_ts_calendar("m", 600, 700, 5) == [
            600.0 + 24 * i for i in range(5)]
        assert dr._dash_ts_yearly(1978, 1985, 5) == [
            1978.0, 1980.0, 1982.0, 1984.0, 1986.0]
        assert (600.0, 600.0, 480.0) in dr._dash_ts_ladder("m")
        assert dr._dash_ts_candidates("m", 600, 700, 5, 5)
        assert dr._dash_ts_cost(600, 700, 5, 24.0, 600.0, 696.0, 5, 0.0,
                                dr._DASH_TS_PARAMS["m"]) is not None

    def test_the_calendar_conversions(self):
        """%td 15000 is 25jan2001 (month 492 and 24/31); month 492 starts on
        %td 14976 and in %tw week 2132; %tw 2600 starts on %td 18263."""
        assert dr._dash_ts_frac_month(15000) == pytest.approx(492 + 24 / 31)
        assert dr._dash_ts_month_day(492) == 14976.0
        assert dr._dash_ts_month_week(492) == 2132.0
        assert dr._dash_ts_week_day(2600) == 18263.0
        # WP-30 P1.17b: 25jan2001 is in %tw week 2135 (2001w4), which
        # starts on 22jan2001, the first of twoway's weekly ticks over
        # 15000 to 15028 (default_base_truth.json bases.bar_td).
        assert dr._dash_ts_day_week(15000) == 2135.0
        assert dr._dash_ts_week_day(2135) == 14997.0
        assert dr._dash_ts_day_week(18263 + 364) == 2651.0
        assert dr._dash_ts_month_day(10 ** 7) is None
        # `_tsnatscale 12869 12989 4, d': 1995m4 to 1995m8's first days.
        assert dr._dash_ts_daily("d", 12869, 12989, 4) == [
            12874.0, 12904.0, 12935.0, 12965.0, 12996.0]

    def test_one_value_is_less_and_plus_one(self):
        """tickset_g.class set_ticks answers one value before _tsnatscale
        is asked: that value less and plus one."""
        assert dr._dash_tsnatscale_ticks(600, 600, 5, "m") == [599.0, 601.0]

    def test_tc_is_natscale_over_statas_milliseconds(self):
        """%tc takes natscale (ff "c" is not a tsnatscale unit): 36 of the
        40 graphs.  Of the four others, one is the natscale model's own
        miss (635905642491 to 635911227852, #7) and three are ranges of a
        few thousand milliseconds 1e12 from zero, where natscale's 32-bit
        count overflows and its answer is not the rule dash follows (lo-1
        and hi+1 for 460103911213 #2; 1969306040000 to the data's maximum
        by 20000 for 1969306058434 #5; 1728194190000(5000)1728194195000
        for 1728194191589 #6)."""
        ok = 0
        for kind, lo, hi, n, mn, mx, step, lst in _T["date_graph"]:
            if kind != "c":
                continue
            got = dr._dash_axis_count_ticks(lo + _EPOCH, hi + _EPOCH, n, "tc")
            want = [v + _EPOCH for v in _expand(mn, mx, step, lst)]
            ok += _same(got, want, 1e-12)
        assert ok >= 36, ok

    def test_a_date_axis_converts_its_unit(self):
        """%td: the ticks are the model's, in days, as epoch milliseconds;
        %ty the years' 1 January."""
        got = dr._dash_axis_count_ticks(
            15000 * 86400000.0 + _EPOCH, 16000 * 86400000.0 + _EPOCH, 5,
            "td")
        days = dr._dash_tsnatscale_ticks(15000, 16000, 5, "d")
        assert got == [d * 86400000.0 + _EPOCH for d in days]
        def _ms(vals, kind):
            return [float(v) for v in dr._stata_dates_to_datetime(
                pd.Series(vals, dtype="float64"), kind).astype("int64")]
        lo, hi = _ms([1978, 1985], "ty")
        y = dr._dash_axis_count_ticks(lo, hi, 5, "ty")
        assert y == _ms(dr._dash_tsnatscale_ticks(1978, 1985, 5, "y"), "ty")


class TestAdversarial:
    @pytest.mark.parametrize("unit", _UNITS)
    def test_huge_counts_are_bounded(self, unit):
        base = {"d": 15000, "w": 2600, "m": 600, "q": 200, "h": 100,
                "y": 2000}[unit]
        t0 = time.perf_counter()
        for n in (10 ** 9, 2001, 0, -5):
            got = dr._dash_tsnatscale_ticks(base, base + 5000, n, unit)
            assert got is None or len(got) <= dr._MAX_AXIS_TICKS + 1
        assert time.perf_counter() - t0 < 2.0

    @pytest.mark.parametrize("unit", _UNITS)
    @pytest.mark.parametrize("lo,hi", [(float("nan"), 1), (0, float("inf")),
                                       (-1e308, 1e308), ("x", 1), (None, 2),
                                       (5, 5), (7, 3)])
    def test_hostile_ranges(self, unit, lo, hi):
        got = dr._dash_tsnatscale_ticks(lo, hi, 5, unit)
        assert got is None or (all(map(math.isfinite, got))
                               and len(got) <= dr._MAX_AXIS_TICKS + 1)

    def test_extreme_date_ranges(self):
        """01jan0100 to 31dec9999 in each unit; beyond Stata's range there
        is no date axis tick at all."""
        t0 = time.perf_counter()
        for kind, lo, hi in (("td", -679350, 2936549), ("tm", -22320, 96479),
                             ("tq", -7440, 32159), ("th", -3720, 16079),
                             ("tw", -96720, 417039), ("ty", 100, 9999)):
            lo_ms = dr._stata_dates_to_datetime(
                pd.Series([lo, hi]), kind).astype("int64").tolist()
            got = dr._dash_axis_count_ticks(lo_ms[0], lo_ms[1], 12, kind)
            assert got and all(map(math.isfinite, got)), kind
        assert dr._dash_axis_count_ticks(-1e20, 1e20, 5, "td") is None
        assert time.perf_counter() - t0 < 2.0

    @pytest.mark.parametrize("kind", ["evil", None, "../x", 5])
    def test_an_unknown_kind_is_linear(self, kind):
        assert dr._dash_axis_count_ticks(12, 41, 5, kind) == \
            dr._dash_natscale_ticks(12, 41, 5)


# ---------------------------------------------------------------------------
# Both modes, end to end
# ---------------------------------------------------------------------------

_SEQ = itertools.count()
_MODES = ("saved", "served")


def _auto_like():
    """Two groups with auto's extremes: domestic mpg 12-34 and weight
    1800-4840, foreign mpg 14-41 and weight 1760-3420."""
    n = 20
    return pd.DataFrame({
        "mpg": np.r_[np.linspace(12, 34, n), np.linspace(14, 41, n)],
        "weight": np.r_[np.linspace(1800, 4840, n),
                        np.linspace(1760, 3420, n)],
        "foreign": np.r_[np.zeros(n), np.ones(n)],
        "price": np.r_[np.linspace(3291, 15906, n), np.linspace(3748, 12990, n)],
    })


def _spec(plots, go, formats=None):
    g = dict(go, name="g1", title='"t"')
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "", "registry": "g1",
                              "tabs": "", "filter_position": "top",
                              "csv": "0", "level": "95",
                              "formats": dict(formats or {}), "limits": {}}}


def _figures(mode, tmp_path, df, plots, go, formats=None):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, go, formats)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(df)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            figs = r._build_figures()
            return [figs[k] for k in sorted(figs)]
        ap = str(tmp_path / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        ms = importlib.util.spec_from_file_location("_nsax_app_%d" % tag, ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    seen, out = set(), []
    for root in doc.roots:
        for m in root.references():
            if isinstance(m, _fig_cls) and m.id not in seen:
                seen.add(m.id)
                out.append(m)
    return sorted(out, key=lambda f: str(f.title.text if f.title else ""))


def _sc(y, x, **opts):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": opts}


def _axis(side):
    from bokeh.models.axes import ContinuousAxis
    axes = [a for a in side if isinstance(a, ContinuousAxis)]
    assert len(axes) == 1, axes
    return axes[0]


def _ticks(ax):
    from bokeh.models import FixedTicker
    assert isinstance(ax.ticker, FixedTicker), type(ax.ticker).__name__
    return list(ax.ticker.ticks)


@pytest.mark.parametrize("mode", _MODES)
class TestByPanelsShareOneScale:
    def _measured(self, cmd):
        for rec in _T["by"]:
            if rec["command"] == cmd:
                return rec["panels"]
        raise AssertionError(cmd)

    def test_ylabel_count(self, mode, tmp_path):
        """by(foreign) ylabel(#5): 10(10)40 on both panels (measured),
        each panel's range reaching both ends."""
        want = self._measured(
            "twoway scatter mpg weight, by(foreign) ylabel(#5)")
        figs = _figures(mode, tmp_path, _auto_like(), [_sc("mpg", "weight")],
                        {"by": "foreign", "ylabel": "#5"})
        assert len(figs) == len(want) == 2
        for fig, p in zip(figs, want):
            assert _ticks(_axis(fig.left)) == _expand(*p["y_major"])
            assert fig.y_range.start <= 10.0 and fig.y_range.end >= 40.0

    def test_both_axes(self, mode, tmp_path):
        want = self._measured(
            "twoway scatter mpg weight, by(foreign) ylabel(#5) xlabel(#4)")
        figs = _figures(mode, tmp_path, _auto_like(), [_sc("mpg", "weight")],
                        {"by": "foreign", "ylabel": "#5", "xlabel": "#4"})
        for fig, p in zip(figs, want):
            assert _ticks(_axis(fig.left)) == _expand(*p["y_major"])
            assert _ticks(_axis(fig.below)) == _expand(*p["x_major"])

    def test_a_panel_with_no_values_takes_the_common_ticks(self, mode,
                                                          tmp_path):
        """Adversarial: a panel whose y is all missing, and one of a single
        value, draw the other panels' ticks and do not raise."""
        df = _auto_like()
        df = pd.concat([df, pd.DataFrame({
            "mpg": [np.nan, np.nan, 25.0], "weight": [2000.0, 3000.0, 2500.0],
            "foreign": [2.0, 2.0, 3.0], "price": [5000.0] * 3})],
            ignore_index=True)
        figs = _figures(mode, tmp_path, df, [_sc("mpg", "weight")],
                        {"by": "foreign", "ylabel": "#5"})
        assert len(figs) == 4
        for fig in figs:
            assert _ticks(_axis(fig.left)) == [10.0, 20.0, 30.0, 40.0]

    def test_without_by_a_graph_keeps_its_own(self, mode, tmp_path):
        """Control: one group alone is ticked over its own data (12-34:
        10(5)35, measured by(foreign, yrescale) panel 1)."""
        df = _auto_like().iloc[:20]
        figs = _figures(mode, tmp_path, df, [_sc("mpg", "weight")],
                        {"ylabel": "#5"})
        assert _ticks(_axis(figs[0].left)) == [10.0, 15.0, 20.0, 25.0, 30.0,
                                               35.0]


@pytest.mark.parametrize("mode", _MODES)
class TestBothModesTickLogAndDateAxes:
    def test_log_axis(self, mode, tmp_path):
        """yscale(log) ylabel(#5) over price 3291-15906: 5000(5000)15000,
        twoway's 0 dropped."""
        figs = _figures(mode, tmp_path, _auto_like(), [_sc("price", "weight")],
                        {"yscale": "log", "ylabel": "#5"})
        ax = _axis(figs[0].left)
        assert type(ax).__name__ == "LogAxis"
        assert _ticks(ax) == [5000.0, 10000.0, 15000.0]

    def test_td_axis(self, mode, tmp_path):
        """A %td axis from 15000 to 16000: the model's days, as epoch
        milliseconds (Stata: 15066 to 15979 by quarter for #10)."""
        df = pd.DataFrame({"t": np.linspace(15000, 16000, 30).round(),
                           "y": np.arange(30.0)})
        figs = _figures(mode, tmp_path, df, [_sc("y", "t")],
                        {"xlabel": "#10"}, formats={"t": "%td"})
        ax = _axis(figs[0].below)
        assert type(ax).__name__ == "DatetimeAxis"
        days = dr._dash_tsnatscale_ticks(15000, 16000, 10, "d")
        assert _ticks(ax) == [d * 86400000.0 + _EPOCH for d in days]

    def test_tm_axis(self, mode, tmp_path):
        df = pd.DataFrame({"t": np.arange(600.0, 701.0),
                           "y": np.arange(101.0)})
        figs = _figures(mode, tmp_path, df, [_sc("y", "t")],
                        {"xlabel": "#5"}, formats={"t": "%tm"})
        months = dr._dash_tsnatscale_ticks(600, 700, 5, "m")
        want = dr._stata_dates_to_datetime(pd.Series(months), "tm") \
            .astype("int64").tolist()
        assert _ticks(_axis(figs[0].below)) == [float(v) for v in want]

    def test_tc_axis(self, mode, tmp_path):
        """%tc 1261584490467 to 1261589313723, xlabel(#9): Stata draws
        1261584000000(1000000)1261590000000 (measured)."""
        df = pd.DataFrame({"t": np.linspace(1261584490467, 1261589313723, 30),
                           "y": np.arange(30.0)})
        figs = _figures(mode, tmp_path, df, [_sc("y", "t")],
                        {"xlabel": "#9"}, formats={"t": "%tc"})
        want = [1261584000000.0 + 1e6 * i + _EPOCH for i in range(7)]
        assert _ticks(_axis(figs[0].below)) == want
