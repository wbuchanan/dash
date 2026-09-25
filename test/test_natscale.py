"""
test_natscale.py -- xlabel(#N) and ylabel(#N) ticks where twoway puts them.

The defect (BUGS.md, S3): dash handed #N to Bokeh as desired_num_ticks and
Bokeh chose the positions in the browser.  ``ylabel(#5)`` on auto's mpg drew
15(5)40 over a y range of 10.55 to 42.45; twoway draws 10(10)40.

twoway's rule (tickset_g.class, ``set_ticks``): the builtin ``natscale``
over the axis's data minimum and maximum, ticks from its r(min) in steps of
r(delta) while <= r(max); ``#1`` is the minimum and the maximum.  natscale
is compiled, so dash reproduces it with a model fitted to Stata's answers:
test/fixtures/natscale_truth.json holds them, measured 24sep2026 with
StataNow 19.5 --

* ``drawn``: 264 axes twoway drew, ``twoway scatter <var> __x,
  ylabel(#N)`` for 29 variables of auto, nlsw88, lifeexp and census and
  N = 2..12, read from the graph (``.Graph.yaxis1.major.min/max/delta``);
  each equals ``_natscale <min> <max> N`` over the variable's range;
* ``natscale``: 3,000 random ranges through ``_natscale``.

The model agrees with 261 of the 264 drawn axes (the three it does not are
pinned below as strict xfails, so a better model has to remove them) and
with 98.3% of the random ranges.  Measured in Stata for the end-to-end
cases here (sysuse auto): ``(scatter mpg weight) (line turn weight),
ylabel(#6) xlabel(#4)`` draws y 10(10)50 and x 2000(1000)5000; ``ylabel(#1)``
draws 12 and 41; ``xtick(#3)`` marks 2000(1000)5000; ``ylabel(#6, axis(2))``
over price draws 4000(2000)16000.
"""
import importlib.util
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "natscale_truth.json")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/natscale_truth.json is missing")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


_T = _truth()

#: The drawn axes the model does not reproduce (measured 24sep2026): natscale
#: leaves the lowest tick off (price #4) or reports its r(max) as the data's
#: maximum and steps 20 from 0 (trunk #2, #3), where the model keeps one
#: tick more.
_KNOWN = {("auto", "price", 4), ("auto", "trunk", 2), ("auto", "trunk", 3)}


def _same(a, b, step):
    return len(a) == len(b) and all(abs(x - y) <= 1e-7 * step
                                    for x, y in zip(a, b))


def _drawn_cases():
    out = []
    for r in _T["drawn"]:
        key = (r["dataset"], r["var"], r["n"])
        marks = ([pytest.mark.xfail(strict=True, reason="natscale case the "
                                    "model does not reproduce")]
                 if key in _KNOWN else [])
        out.append(pytest.param(r, id="%s-%s-%d" % key, marks=marks))
    return out


class TestTheRuleAgainstStata:
    @pytest.mark.parametrize("case", _drawn_cases())
    def test_the_axes_twoway_drew(self, case):
        got = dr._dash_natscale_ticks(case["min"], case["max"], case["n"])
        step = case["natscale"][2]
        assert _same(got, case["ticks"], step), (got, case["ticks"])

    def test_the_graph_uses_natscale_over_the_data(self):
        """The fixture's own claim: every drawn axis is natscale's answer
        over the data's minimum and maximum."""
        for r in _T["drawn"]:
            lo, hi, step = r["natscale"]
            t, i = [], 0
            while lo + i * step <= hi + 1e-9 * step:
                t.append(lo + i * step)
                i += 1
            assert _same(t, r["ticks"], step), r

    def test_random_ranges(self):
        """98.3% of Stata's answers over 2,878 random ranges with N >= 2
        (measured 24sep2026: 2,829); the floor is that count."""
        ok = total = 0
        for lo, hi, n, rmin, rmax, step, _rn in _T["natscale"]:
            if n < 2:
                continue
            total += 1
            want, i = [], 0
            while rmin + i * step <= rmax + 1e-9 * step:
                want.append(rmin + i * step)
                i += 1
            ok += _same(dr._dash_natscale_ticks(lo, hi, n), want, step)
        assert total == 2878
        assert ok >= 2829, ok

    def test_the_reported_case(self):
        """auto's mpg, 12 to 41: twoway's ylabel(#5) is 10(10)40."""
        assert dr._dash_natscale_ticks(12, 41, 5) == [10.0, 20.0, 30.0, 40.0]

    def test_one_is_minmax(self):
        assert dr._dash_natscale_ticks(12, 41, 1) == [12.0, 41.0]

    def test_a_single_value(self):
        """tickset's set_ticks: min0 >= max0 gives min0-1 and min0+1."""
        assert dr._dash_natscale_ticks(5, 5, 5) == [4.0, 6.0]

    def test_ticks_are_clean_decimals(self):
        got = dr._dash_natscale_ticks(0.1, 0.9, 9)
        assert got == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


class TestAdversarial:
    """The rule reads numbers only; a count or range that is hostile costs
    bounded time and gives a bounded list."""

    def test_the_largest_count_is_bounded(self):
        t0 = time.perf_counter()
        got = dr._dash_natscale_ticks(0, 1, 10 ** 9)
        assert time.perf_counter() - t0 < 2.0
        assert got and len(got) <= dr._MAX_AXIS_TICKS + 1

    @pytest.mark.parametrize("lo,hi", [(float("nan"), 1), (0, float("inf")),
                                       (-1e308, 1e308), ("x", 1),
                                       (None, 2)])
    def test_non_finite_or_non_numeric_ranges(self, lo, hi):
        got = dr._dash_natscale_ticks(lo, hi, 5)
        assert got is None or all(np.isfinite(got))

    @pytest.mark.parametrize("lo,hi", [(1e-300, 2e-300), (1e300, 3e300),
                                       (-5e-12, 5e-12)])
    def test_extreme_magnitudes(self, lo, hi):
        got = dr._dash_natscale_ticks(lo, hi, 5)
        assert got and all(np.isfinite(got)) and len(got) <= 6

    @pytest.mark.parametrize("tag", ["dash_count:99999999999", "dash_count:",
                                     "dash_count:-3", "dash_count:5;x",
                                     "dash_count:٣", 5, None])
    def test_a_foreign_tag_is_no_count(self, tag):
        from bokeh.models.tickers import BasicTicker
        assert dr._dash_count_of(BasicTicker(tags=[tag])) is None

    def test_the_tag_round_trips(self):
        assert dr._dash_count_of(dr._dash_count_ticker(7)) == 7


# ---------------------------------------------------------------------------
# Both modes, end to end
# ---------------------------------------------------------------------------

_SEQ = itertools.count()
_MODES = ("saved", "served")
_DF = pd.DataFrame({
    "mpg": np.r_[12.0, 41.0, np.linspace(14, 39, 72)],
    "weight": np.r_[1760.0, 4840.0, np.linspace(1800, 4800, 72)],
    "turn": np.r_[31.0, 51.0, np.linspace(32, 50, 72)],
    "price": np.r_[3291.0, 15906.0, np.linspace(3300, 15900, 72)],
})


def _spec(plots, go):
    g = dict(go, name="g1", title='"t"')
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "", "registry": "g1",
                              "tabs": "", "filter_position": "top",
                              "csv": "0", "level": "95", "formats": {},
                              "limits": {}}}


def _figure(mode, tmp_path, plots, go):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, go)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            return list(r._build_figures().values())[0]
        ap = str(tmp_path / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        ms = importlib.util.spec_from_file_location(
            "_natscale_app_%d" % tag, ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1
    return figs[0]


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
class TestBothModesDrawTwowaysTicks:
    def test_the_reported_case(self, mode, tmp_path):
        """ylabel(#5) on mpg: 10(10)40, and the axis reaches 10."""
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"ylabel": "#5"})
        assert _ticks(_axis(fig.left)) == [10.0, 20.0, 30.0, 40.0]
        assert fig.y_range.start is not None and fig.y_range.start <= 10.0

    def test_a_sub_option_leaves_the_rule_alone(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"ylabel": "#5, grid"})
        assert _ticks(_axis(fig.left)) == [10.0, 20.0, 30.0, 40.0]

    def test_xlabel(self, mode, tmp_path):
        """xlabel(#7) on weight, 1760 to 4840: 1500(500)5000 (drawn)."""
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"xlabel": "#7"})
        assert _ticks(_axis(fig.below)) == [1500.0 + 500 * i
                                            for i in range(8)]
        assert fig.x_range.start <= 1500 and fig.x_range.end >= 5000

    def test_every_layer_on_the_axis_counts(self, mode, tmp_path):
        """(scatter mpg weight) (line turn weight), ylabel(#6) xlabel(#4):
        10(10)50 and 2000(1000)5000, measured."""
        plots = [_sc("mpg", "weight"),
                 {"type": "line", "yvar": "turn", "xvar": "weight",
                  "options": {"sort": "sort"}}]
        fig = _figure(mode, tmp_path, plots,
                      {"ylabel": "#6", "xlabel": "#4"})
        assert _ticks(_axis(fig.left)) == [10.0, 20.0, 30.0, 40.0, 50.0]
        assert _ticks(_axis(fig.below)) == [2000.0, 3000.0, 4000.0, 5000.0]

    def test_one_is_the_data_extremes(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"ylabel": "#1"})
        assert _ticks(_axis(fig.left)) == [12.0, 41.0]

    def test_the_second_axis(self, mode, tmp_path):
        """ylabel2(#6) over price: 4000(2000)16000 (drawn, price #6)."""
        plots = [_sc("mpg", "weight"), _sc("price", "weight", yaxis="2")]
        fig = _figure(mode, tmp_path, plots, {"ylabel2": "#6"})
        assert _ticks(_axis(fig.right)) == [4000.0 + 2000 * i
                                            for i in range(7)]

    def test_xtick_marks(self, mode, tmp_path):
        """xtick(#3) on weight marks 2000(1000)5000 (measured,
        `.xaxis1.majornl')."""
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"xtick": "#3"})
        t = _axis(fig.below).ticker
        assert type(t).__name__ == "CustomJSTicker"
        assert "every" not in t.args
        assert t.args["extra"] == [2000.0, 3000.0, 4000.0, 5000.0]
        assert t.minor_code == dr._DASH_TICK_EXTRA_JS

    def test_an_explicit_rule_is_untouched(self, mode, tmp_path):
        """Control: ylabel(15(5)30) keeps its own ticks."""
        fig = _figure(mode, tmp_path, [_sc("mpg", "weight")],
                      {"ylabel": "15(5)30"})
        assert _ticks(_axis(fig.left)) == [15.0, 20.0, 25.0, 30.0]
