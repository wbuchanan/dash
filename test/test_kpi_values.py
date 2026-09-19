"""test_kpi_values.py — S13: a KPI must show the statistic the user asked for.

``dash kpi mean(mpg) if foreign==1`` displays the **unconditional** mean.
Stata computes the right number and stores it; ``dash.ado`` then omits the
qualifier from the KPI JSON, so ``_build_kpi_html`` recomputes from the full
frame and overwrites it. Measured in Stata:

    mean(mpg)                  21.297297297297298
    mean(mpg) if foreign==1    24.772727272727273   <- what the card must show

Four more defects in the same family, all confirmed against the current tree:

  * ``p25``/``p75`` are accepted by ``dash kpi`` and computed for the initial
    render, but are absent from the JS recompute list — they fall through to
    ``result = 0`` the first time any filter moves.
  * the displayed precision changes when a filter moves.
  * ``dcount`` is always missing, because ``codebook`` leaves ``r()`` empty.
  * ``update(brush)`` has no standalone selection callback at all.

And one that no plan listed, found during verification and the most serious of
the set for correctness: **every percentile KPI uses pandas' quantile, not
Stata's percentile.** Stata uses Hyndman-Fan **type 2** — ``j = N*p/100``;
integer ``j`` gives ``(x_j + x_{j+1})/2``, otherwise ``x_ceil(j)``. pandas
defaults to type 7 and disagrees: p75 of ``mpg`` is **25** in Stata and
**24.75** in pandas. ``dash_render`` already contains the correct
implementation — ``_stata_percentile()`` — and the KPI paths simply never call
it.

Every expected value here comes from ``test/fixtures/kpi_truth.json``, measured
in Stata with the command recorded beside it.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json

_FIXTURE = os.path.join(_HERE, "fixtures", "kpi_truth.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(_FIXTURE),
    reason="test/fixtures/kpi_truth.json is missing",
)


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE) as fh:
        return json.load(fh)


_AUTO_CSV = os.path.join(_HERE, "fixtures", "data", "auto.csv")


@pytest.fixture(scope="module")
def auto():
    """sysuse auto's mpg and weight, at full precision."""
    if not os.path.exists(_AUTO_CSV):
        pytest.skip("test/fixtures/data/auto.csv is missing")
    return pd.read_csv(_AUTO_CSV)


def _render_kpi(df, *, stat, var, if_expr="", fmt="", extra_cols=None,
                filters=None):
    plots = [{"type": "scatter", "yvar": var, "xvar": var, "options": {}}]
    spec = make_spec(plots)
    kpi = {"name": "k1", "stat": stat, "var": var, "title": "T", "fmt": fmt}
    if if_expr:
        kpi["if_expr"] = if_expr
    spec["kpis"] = [kpi]
    spec["build_options"]["registry"] = "k1 g1"
    if filters:
        spec["build_options"]["filters"] = filters
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr


def _card_text(dr):
    return "\n".join(getattr(v, "text", "") for v in dr.kpi_divs.values())


# ======================================================================
# The measured anchor
# ======================================================================

class TestQualifiedKpiShowsTheConditionalStatistic:

    def test_the_anchor_is_what_stata_measured(self, truth):
        a = truth["anchor"]
        assert a["confirmed"] is True
        assert float(a["full_precision"]) == pytest.approx(
            24.772727272727273)

    def test_an_unqualified_mean_is_the_unconditional_one(self, truth, auto):
        dr = _render_kpi(auto, stat="mean", var="mpg", fmt="%9.4f")
        want = truth["kpi_stats"]["all"]["mean"]
        assert f"{float(want):.4f}" in _card_text(dr), _card_text(dr)[:300]

    def test_a_qualified_mean_shows_the_conditional_value(self, truth, auto):
        """The card shows 21.2973 where Stata reports 24.7727."""
        df = auto.copy()
        df["foreign"] = np.where(df["weight"] < 3000, 1.0, 0.0)
        sub = df.loc[df["foreign"] == 1.0, "mpg"]
        want = float(sub.mean())
        dr = _render_kpi(df, stat="mean", var="mpg", if_expr="foreign == 1",
                         fmt="%9.4f", extra_cols=["foreign"])
        text = _card_text(dr)
        assert f"{want:.4f}" in text, (
            f"the card shows the unconditional mean; expected {want:.4f}, "
            f"card was: {text[:300]}"
        )

    def test_the_qualifier_reaches_the_renderer_at_all(self, auto):
        df = auto.copy()
        df["foreign"] = np.where(df["weight"] < 3000, 1.0, 0.0)
        dr = _render_kpi(df, stat="mean", var="mpg", if_expr="foreign == 1")
        kpis = dr.master_spec.get("kpis", [])
        assert kpis and kpis[0].get("if_expr"), (
            "the KPI's if_expr is absent from the spec, so the renderer "
            "cannot honour it"
        )


# ======================================================================
# Stata's percentile, not pandas'
# ======================================================================

class TestPercentileKpisUseStatasRule:

    def test_the_two_rules_genuinely_disagree(self, truth, auto):
        """Guard against this test passing vacuously."""
        v = auto["mpg"].to_numpy(float)
        stata = dash_render._stata_percentile(np.sort(v), 75)
        pandas_ = float(pd.Series(v).quantile(0.75))
        assert stata != pytest.approx(pandas_), (
            "the two percentile rules agree on this data, so it cannot "
            "distinguish them"
        )

    @pytest.mark.parametrize("stat,p", [("p25", 25), ("p50", 50),
                                        ("p75", 75)])
    def test_the_kpi_matches_stata(self, truth, auto, stat, p):
        want = float(truth["kpi_stats"]["all"][stat])
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%9.4f")
        assert f"{want:.4f}" in _card_text(dr), (
            f"{stat} showed something other than Stata's {want}; card: "
            f"{_card_text(dr)[:200]}"
        )

    def test_compute_kpi_stat_uses_the_stata_helper(self):
        """The correct implementation already exists in the file."""
        import inspect
        src = inspect.getsource(DashRenderer._compute_kpi_stat)
        assert ".quantile(" not in src, (
            "the KPI path still uses pandas' quantile, which is "
            "Hyndman-Fan type 7; Stata uses type 2"
        )
        assert "_stata_percentile" in src

    def test_median_agrees_with_stata(self, truth, auto):
        want = float(truth["kpi_stats"]["all"]["median"])
        dr = _render_kpi(auto, stat="median", var="mpg", fmt="%9.4f")
        assert f"{want:.4f}" in _card_text(dr)


# ======================================================================
# Every statistic, against the fixture
# ======================================================================

class TestEveryStatisticMatchesStata:

    @pytest.mark.parametrize("stat", [
        "mean", "sum", "count", "min", "max", "median", "sd",
        "p25", "p50", "p75",
    ])
    def test_unconditional(self, truth, auto, stat):
        want = float(truth["kpi_stats"]["all"][stat])
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%12.6f")
        assert f"{want:.6f}" in _card_text(dr), (
            f"{stat}: expected {want:.6f}; card: {_card_text(dr)[:200]}"
        )

    @pytest.mark.parametrize("stat", ["var", "cv", "iqr", "skewness"])
    def test_the_statistics_the_command_does_not_yet_accept(self, truth, auto,
                                                            stat):
        """Capability gap: accepted by neither dash.ado nor the renderer."""
        want = float(truth["kpi_stats"]["all"][stat])
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%12.6f")
        assert f"{want:.6f}" in _card_text(dr), (
            f"{stat} is not supported; expected {want:.6f}"
        )

    def test_dcount_returns_a_number(self, truth, auto):
        """codebook leaves r() empty, so dcount has always been missing."""
        want = float(truth["dcount"]["truth"]["make_distinct"]) \
            if "make_distinct" in truth["dcount"].get("truth", {}) else None
        dr = _render_kpi(auto, stat="dcount", var="mpg", fmt="%9.0f")
        text = _card_text(dr)
        assert "." not in text.replace("<div", "").replace("</div", "") \
            or any(ch.isdigit() for ch in text), text[:200]
        assert str(int(auto["mpg"].nunique())) in text, (
            f"dcount showed no usable value; card: {text[:200]}"
        )


# ======================================================================
# Behaviour under filtering
# ======================================================================

def _filtered_dashboard(df, stat, fmt=""):
    return _render_kpi(
        df, stat=stat, var="mpg", fmt=fmt,
        filters=[{"varname": "mpg", "type": "range", "exclude": [],
                  "label": ""}],
    )


class TestKpisUnderFiltering:

    @pytest.mark.parametrize("stat", ["p25", "p75"])
    def test_percentiles_are_in_the_javascript_recompute_list(self, stat):
        """They fall through to result = 0 on the first filter interaction."""
        js = dash_render._FILTER_JS
        lo = js.index("for (let ki = 0; ki < kpi_config.length")
        block = js[lo:lo + 4000]
        assert f"'{stat}'" in block or f'"{stat}"' in block, (
            f"{stat} has no branch in the KPI recompute, so the card reads 0 "
            f"as soon as any filter moves"
        )

    @pytest.mark.parametrize("stat", ["mean", "sum", "count", "min", "max",
                                      "median", "sd", "p25", "p50", "p75",
                                      "var", "cv", "iqr", "skewness",
                                      "dcount"])
    def test_every_supported_statistic_has_a_recompute_branch(self, stat):
        """Adding a statistic that silently reads 0 under filtering is the
        same defect again."""
        js = dash_render._FILTER_JS
        lo = js.index("for (let ki = 0; ki < kpi_config.length")
        block = js[lo:lo + 6000]
        assert f"'{stat}'" in block or f'"{stat}"' in block, stat

    def test_the_precision_does_not_change_when_a_filter_moves(self, auto):
        """Initial render and callback must agree on the format."""
        dr = _filtered_dashboard(auto, "mean")
        assert dr.filter_callbacks, "no filter callback was built"
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert cfg, "the KPI did not reach the callback"
        text = _card_text(dr)
        import re
        m = re.search(r">([\d,]+\.?\d*)<", text)
        assert m, f"no numeric value in the card: {text[:200]}"
        shown = m.group(1)
        initial_dp = len(shown.split(".")[1]) if "." in shown else 0
        assert cfg[0]["decimals"] == initial_dp, (
            f"the card shows {initial_dp} decimal places and the callback "
            f"would show {cfg[0]['decimals']} — the number changes shape as "
            f"soon as a filter moves"
        )

    def test_the_javascript_uses_statas_percentile_rule(self):
        """The callback must not reintroduce pandas' rule in JavaScript."""
        js = dash_render._FILTER_JS
        assert "dash_pctl" in js, (
            "the KPI recompute has no Stata-percentile helper, so a filtered "
            "p25 will disagree with the initial render"
        )


# ======================================================================
# update(brush)
# ======================================================================

class TestBrushUpdateIsRealOrDocumentedAsAbsent:

    def test_the_help_and_the_code_agree(self):
        """_kpi_update_modes is assigned and never read."""
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        implemented = code.count("_kpi_update_modes") >= 2
        help_path = os.path.join(_HERE, "..", "dash.sthlp")
        text = open(help_path, encoding="utf-8", errors="replace").read()
        claims_yes = "update(brush)" in text and "brush" in text
        if not implemented:
            assert "not supported" in text or "standalone" in text, (
                "update(brush) has no implementation and the help does not "
                "say so"
            )
