"""A served KPI card computed a different statistic from a saved one.

``dash kpi`` accepts fifteen statistics -- ``dash.ado:1828`` lists them:
``mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75``
-- plus any ``pNN``. The standalone renderer computes all of them in
``DashRenderer._kpi_statistic``, and the standalone HTML's own JavaScript
recomputes all of them on a filter move. The generated server app carried a
third, hand-written copy that knew ten.

Measured on a 74-observation fixture, standalone against served:

    var        29.1776918979879       nan
    cv         0.2527358639790006     nan
    iqr        8.381055098622767      nan
    skewness   0.10081938509246473    nan
    p25        17.550972825576864     17.563005323808085
    p75        25.93202792419963      25.741109814826476

So ``dash kpi var(mpg), title(Variance) name(k1)`` followed by ``dash serve``
drew a card reading ``.`` where ``dash build`` drew ``29.18``; and the two
percentiles disagreed because the copy used pandas' linear interpolation
where Stata -- and therefore every other path in dash -- uses its own rule.

These tests compare the served computation against the standalone one for
every statistic dash accepts.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()

# Every statistic `dash kpi' accepts, from dash.ado's own `valid_stats' list.
_VALID_STATS = ["mean", "sum", "count", "dcount", "min", "max", "median",
                "sd", "var", "cv", "iqr", "skewness", "p25", "p50", "p75"]

_RNG = np.random.default_rng(19780101)
_N = 74                                   # auto's observation count
_W = np.linspace(1760.0, 4840.0, _N)
_M = 40.0 - 0.0055 * _W + _RNG.normal(0.0, 1.8, _N)
_DF = pd.DataFrame({"mpg": _M, "weight": _W})


def _spec(stats):
    kpis = [{"name": f"k{i}", "stat": s, "varname": "mpg", "title": s,
             "subtitle": "", "fmt": "%9.4f", "color": "", "bgcolor": "",
             "update": "filter", "if_expr": "", "in_expr": ""}
            for i, s in enumerate(stats)]
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}]}],
            "kpis": kpis,
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}


@pytest.fixture(scope="module")
def served(tmp_path_factory):
    """Import the generated server app once and hand back its module."""
    tmp_path = tmp_path_factory.mktemp("kpistat")
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(_spec(_VALID_STATS)))
    dp.write_text(json.dumps(make_data_json(_DF)))
    ap = tmp_path / f"a_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_kpistat_app_{tag}",
                                                str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    return mod


def _standalone(stat):
    return float(dr.DashRenderer._kpi_statistic(_DF["mpg"].dropna(), stat))


class TestEveryAcceptedStatisticIsServed:
    """The fifteen statistics dash.ado accepts all reach the served app."""

    @pytest.mark.parametrize("stat", _VALID_STATS)
    def test_the_served_value_equals_the_standalone_one(self, stat, served):
        want = _standalone(stat)
        got = float(served._compute_kpi(_DF, stat, "mpg"))
        assert not np.isnan(got), (
            f"`dash kpi {stat}(mpg)' draws a card reading `.' under "
            f"`dash serve'; `dash build' draws {want:.6g}"
        )
        assert got == pytest.approx(want, rel=1e-12, abs=1e-12), (
            f"served {stat} = {got!r}, standalone = {want!r}"
        )

    def test_no_accepted_statistic_is_missing(self, served):
        """Guards the list itself: dash.ado's valid_stats is the contract."""
        dead = [s for s in _VALID_STATS
                if np.isnan(float(served._compute_kpi(_DF, s, "mpg")))]
        assert dead == [], (
            f"{len(dead)} of {len(_VALID_STATS)} accepted statistics are "
            f"NaN in server mode: {dead}"
        )


class TestPercentilesUseStatasRule:
    """pandas' linear interpolation is not Stata's percentile."""

    @pytest.mark.parametrize("stat", ["p25", "p50", "p75", "median", "iqr"])
    def test_the_served_percentile_is_statas(self, stat, served):
        want = _standalone(stat)
        got = float(served._compute_kpi(_DF, stat, "mpg"))
        assert got == pytest.approx(want, rel=1e-12, abs=1e-12), (
            f"served {stat} = {got!r} but Stata's rule gives {want!r}; "
            f"the served copy is using pandas' linear interpolation"
        )

    def test_an_arbitrary_percentile_is_served(self, served):
        """`dash kpi p90(mpg)' is accepted, so it must be computed."""
        for stat in ("p10", "p90", "p33"):
            want = _standalone(stat)
            got = float(served._compute_kpi(_DF, stat, "mpg"))
            assert got == pytest.approx(want, rel=1e-12, abs=1e-12), (
                f"served {stat} = {got!r}, standalone = {want!r}"
            )


class TestDegenerateInputIsStillSafe:
    """A KPI over an empty or constant column must not raise."""

    def test_an_empty_column_gives_nan_not_an_exception(self, served):
        empty = pd.DataFrame({"mpg": pd.Series([], dtype=float)})
        for stat in _VALID_STATS:
            got = float(served._compute_kpi(empty, stat, "mpg"))
            assert isinstance(got, float)
        assert float(served._compute_kpi(empty, "count", "mpg")) == 0.0

    def test_an_unknown_statistic_gives_nan_not_an_exception(self, served):
        got = float(served._compute_kpi(_DF, "no_such_stat", "mpg"))
        assert np.isnan(got)

    def test_a_missing_variable_gives_nan_not_an_exception(self, served):
        got = float(served._compute_kpi(_DF, "mean", "no_such_var"))
        assert np.isnan(got)

    def test_a_constant_column_gives_a_defined_cv_or_nan(self, served):
        const = pd.DataFrame({"mpg": pd.Series([3.0] * 10)})
        assert float(served._compute_kpi(const, "sd", "mpg")) == 0.0
        assert float(served._compute_kpi(const, "var", "mpg")) == 0.0
        assert float(served._compute_kpi(const, "cv", "mpg")) == 0.0
        assert np.isnan(float(served._compute_kpi(const, "skewness", "mpg")))
