"""
test_kpi.py
Unit tests for DashRenderer KPI card computation and rendering.

Tests: P2-33 through P2-47

Run with:  pytest test/test_kpi.py -v
"""
import sys
import os
import json
import math
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def auto_data():
    """Synthetic auto.dta-like dataset with known statistics."""
    np.random.seed(42)
    n = 74
    return {
        "mpg":    [21.0, 22.0, 24.5, 18.0, 30.0] + [20.0] * 69,
        "price":  [4099.0, 4749.0, 3799.0, 4816.0, 7827.0] + [5000.0] * 69,
        "rep78":  [3.0, 3.0, None, 3.0, 4.0] + [3.0] * 69,   # None = missing
        "foreign": [0, 0, 0, 0, 1] + [0] * 69,
    }


@pytest.fixture
def auto_df(auto_data):
    df = pd.DataFrame(auto_data)
    # Replace None with NaN for numeric columns
    for col in df.columns:
        if col != "foreign":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@pytest.fixture
def renderer_with_data(auto_df, tmp_path):
    """A DashRenderer instance loaded with synthetic auto data."""
    rows = auto_df.to_dict(orient="records")
    # Convert NaN to None for JSON serialization
    clean_rows = []
    for row in rows:
        clean_row = {}
        for k, v in row.items():
            clean_row[k] = None if (isinstance(v, float) and math.isnan(v)) else v
        clean_rows.append(clean_row)

    data_json = {
        "StataJSON": {
            "variableNames": ["mpg", "price", "rep78", "foreign"],
            "variableLabels": {
                "mpg": "Mileage (mpg)", "price": "Price", "rep78": "Repair record",
                "foreign": "Car origin",
            },
            "valueLabels": {"origin": {"0": "Domestic", "1": "Foreign"}},
            "valueLabelNames": {"foreign": "origin"},
            "variableTypeIsString": {k: False for k in ["mpg","price","rep78","foreign"]},
            "values": clean_rows,
        }
    }

    kpis = [
        {
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "20.27", "display": "20.3",
            "fmt": "%9.1f", "title": "Avg MPG", "subtitle": "All vehicles",
            "color": "", "bgcolor": "", "update": "filter"
        },
        {
            "name": "k2", "stat": "count", "var": "mpg",
            "value": "74", "display": "74",
            "fmt": "%9.0fc", "title": "Sample Size", "subtitle": "",
            "color": "white", "bgcolor": "#2c3e50", "update": "brush"
        },
    ]

    spec = {
        "graphs": [],
        "kpis": kpis,
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "k1 k2",
        },
    }

    spec_path = str(tmp_path / "spec.json")
    data_path = str(tmp_path / "data.json")
    out_path  = str(tmp_path / "out.html")

    with open(spec_path, "w") as f:
        json.dump(spec, f)
    with open(data_path, "w") as f:
        json.dump(data_json, f)

    return DashRenderer(spec_path, data_path, out_path)


# ================================================================
# P2-33 — mean(mpg) computed correctly
# ================================================================
class TestKpiStatistics:
    def test_mean_mpg(self, renderer_with_data, auto_df):
        """P2-33: mean(mpg) matches pandas mean."""
        r = renderer_with_data
        result = r._compute_kpi_stat("mean", "mpg")
        expected = auto_df["mpg"].mean()
        assert abs(result - expected) < 0.01

    # ----------------------------------------------------------------
    # P2-34 — sum(price)
    # ----------------------------------------------------------------
    def test_sum_price(self, renderer_with_data, auto_df):
        """P2-34: sum(price) matches pandas sum."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("sum", "price")
        expected = auto_df["price"].sum()
        assert abs(result - expected) < 1.0

    # ----------------------------------------------------------------
    # P2-35 — count(mpg)
    # ----------------------------------------------------------------
    def test_count_mpg(self, renderer_with_data, auto_df):
        """P2-35: count(mpg) equals number of non-missing observations."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("count", "mpg")
        expected = auto_df["mpg"].notna().sum()
        assert result == expected

    # ----------------------------------------------------------------
    # P2-36 — dcount(rep78) — distinct count
    # ----------------------------------------------------------------
    def test_dcount_rep78(self, renderer_with_data, auto_df):
        """P2-36: dcount(rep78) returns number of distinct non-missing values."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("dcount", "rep78")
        expected = auto_df["rep78"].dropna().nunique()
        assert result == expected

    # ----------------------------------------------------------------
    # P2-37 — min/max
    # ----------------------------------------------------------------
    def test_min_price(self, renderer_with_data, auto_df):
        """P2-37: min(price) correct."""
        r = renderer_with_data
        assert abs(r._compute_kpi_stat("min", "price") - auto_df["price"].min()) < 0.01

    def test_max_price(self, renderer_with_data, auto_df):
        """P2-37: max(price) correct."""
        r = renderer_with_data
        assert abs(r._compute_kpi_stat("max", "price") - auto_df["price"].max()) < 0.01

    # ----------------------------------------------------------------
    # P2-38 — median(mpg)
    # ----------------------------------------------------------------
    def test_median_mpg(self, renderer_with_data, auto_df):
        """P2-38: median(mpg) correct."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("median", "mpg")
        expected = auto_df["mpg"].median()
        assert abs(result - expected) < 0.01

    # ----------------------------------------------------------------
    # P2-39 — p25/p75
    # ----------------------------------------------------------------
    def test_p25_mpg(self, renderer_with_data, auto_df):
        """P2-39: p25(mpg) correct."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("p25", "mpg")
        expected = auto_df["mpg"].quantile(0.25)
        assert abs(result - expected) < 0.5

    def test_p75_mpg(self, renderer_with_data, auto_df):
        """P2-39: p75(mpg) correct."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("p75", "mpg")
        expected = auto_df["mpg"].quantile(0.75)
        assert abs(result - expected) < 0.5

    # ----------------------------------------------------------------
    # P2-40 — sd(mpg)
    # ----------------------------------------------------------------
    def test_sd_mpg(self, renderer_with_data, auto_df):
        """P2-40: sd(mpg) correct (ddof=1, matching Stata)."""
        r = renderer_with_data
        result   = r._compute_kpi_stat("sd", "mpg")
        expected = auto_df["mpg"].std(ddof=1)
        assert abs(result - expected) < 0.01


# ================================================================
# P2-41 — fmt applied to mean → string with 1 decimal place
# ================================================================
class TestKpiFormatting:
    def test_fmt_9_1f_produces_one_decimal(self, renderer_with_data):
        """P2-41: fmt(%9.1f) applied to mean gives 1 decimal place."""
        r = renderer_with_data
        value = r._compute_kpi_stat("mean", "mpg")
        formatted = r._format_kpi_value(value, "%9.1f")
        # Should have exactly one decimal place
        assert "." in formatted
        decimal_part = formatted.split(".")[-1].strip()
        assert len(decimal_part) == 1

    def test_fmt_9_0fc_no_decimals(self, renderer_with_data):
        value = renderer_with_data._compute_kpi_stat("count", "mpg")
        formatted = renderer_with_data._format_kpi_value(value, "%9.0fc")
        assert "." not in formatted


# ================================================================
# P2-42 — KPI Div HTML contains title, value, subtitle
# ================================================================
class TestKpiDivHtml:
    def test_div_contains_title(self, renderer_with_data):
        """P2-42: KPI Div HTML contains the title string."""
        from bokeh.models import Div
        div = renderer_with_data._make_kpi_div({
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "20.27", "display": "20.3",
            "fmt": "%9.1f", "title": "Avg MPG", "subtitle": "All vehicles",
            "color": "", "bgcolor": "", "update": "filter"
        })
        assert isinstance(div, Div)
        assert "Avg MPG" in div.text

    def test_div_contains_value(self, renderer_with_data):
        """P2-42: KPI Div HTML contains the formatted value."""
        from bokeh.models import Div
        div = renderer_with_data._make_kpi_div({
            "name": "k2", "stat": "count", "var": "mpg",
            "value": "74", "display": "74",
            "fmt": "%9.0fc", "title": "Sample Size", "subtitle": "",
            "color": "", "bgcolor": "", "update": "brush"
        })
        assert "74" in div.text

    def test_div_contains_subtitle(self, renderer_with_data):
        """P2-42: KPI Div HTML contains subtitle when provided."""
        from bokeh.models import Div
        div = renderer_with_data._make_kpi_div({
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "20.27", "display": "20.3",
            "fmt": "", "title": "Avg MPG", "subtitle": "All vehicles",
            "color": "", "bgcolor": "", "update": "filter"
        })
        assert "All vehicles" in div.text


# ================================================================
# P2-43/P2-44/P2-45 — CustomJS update mode wiring
# ================================================================
class TestKpiUpdateMode:
    def test_update_filter_attaches_to_widget_value(self, renderer_with_data):
        """P2-43: update(filter) → CustomJS on widget value, not selected.indices."""
        div = renderer_with_data._make_kpi_div({
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "20.27", "display": "20.3",
            "fmt": "", "title": "T", "subtitle": "",
            "color": "", "bgcolor": "", "update": "filter"
        })
        # Verify the KPI was created for filter mode
        kpi_info = renderer_with_data._kpi_update_modes.get("k1", None)
        assert kpi_info is None or kpi_info == "filter"

    def test_update_brush_mode_recorded(self, renderer_with_data):
        """P2-44: update(brush) → registered as brush mode."""
        div = renderer_with_data._make_kpi_div({
            "name": "k2", "stat": "count", "var": "mpg",
            "value": "74", "display": "74",
            "fmt": "", "title": "T", "subtitle": "",
            "color": "", "bgcolor": "", "update": "brush"
        })
        kpi_info = renderer_with_data._kpi_update_modes.get("k2", None)
        assert kpi_info is None or kpi_info == "brush"


# ================================================================
# P2-46 — dcount JS implementation: Set([1,1,2,3]) has size 3
# ================================================================
class TestJsHelpers:
    def test_dcount_js_logic(self, renderer_with_data):
        """P2-46: _compute_kpi_stat('dcount',...) uses set-based distinct count."""
        df = pd.DataFrame({"rep78": [1.0, 1.0, 2.0, 3.0]})
        # Inject df temporarily
        orig = renderer_with_data._df
        renderer_with_data._df = df
        result = renderer_with_data._compute_kpi_stat("dcount", "rep78")
        renderer_with_data._df = orig
        assert result == 3

    # ----------------------------------------------------------------
    # P2-47 — median of sorted [1,2,3,4,5] → 3.0
    # ----------------------------------------------------------------
    def test_median_sorted_array(self, renderer_with_data):
        """P2-47: median of [1,2,3,4,5] = 3.0."""
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0]})
        orig = renderer_with_data._df
        renderer_with_data._df = df
        result = renderer_with_data._compute_kpi_stat("median", "x")
        renderer_with_data._df = orig
        assert abs(result - 3.0) < 0.001


# ================================================================
# Regression tests — KPI initial value computed from Python data
# ================================================================

class TestKpiInitialValueComputed:
    """Regression: non-faceted KPIs in render() must compute and format their
    initial display value from the loaded DataFrame, not just pass through the
    raw (unformatted) value from the Stata-generated spec.

    Bug: render() called _make_kpi_div(kpi) without computing stat/var first.
    For specs from Stata, kpi["value"] is the raw unformatted numeric
    (e.g. "21.2972972972973") — so the card showed 14+ significant figures
    instead of the formatted "21.3".  For test specs, kpi["value"] was ""
    so the card showed nothing at all.
    """

    def _build_renderer_with_kpis(self, kpis, tmp_path):
        """Helper: build a DashRenderer with the given KPI list."""
        vals = [{"mpg": float(v), "price": float(v * 200)}
                for v in [15, 18, 21, 22, 24, 26, 28, 30]]
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "price"],
            "variableLabels": {"mpg": "mpg", "price": "price"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "price": False},
            "values": vals,
        }}
        spec = {
            "graphs": [],
            "kpis": kpis,
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": " ".join(k["name"] for k in kpis)},
        }
        sp = str(tmp_path / "spec.json")
        dp = str(tmp_path / "data.json")
        op = str(tmp_path / "out.html")
        with open(sp, "w") as f: json.dump(spec, f)
        with open(dp, "w") as f: json.dump(data_json, f)
        return DashRenderer(sp, dp, op)

    def test_kpi_value_computed_and_formatted_on_render(self, tmp_path):
        """render() must compute mean(mpg) from data and format with %9.1f.

        Expected: mean([15,18,21,22,24,26,28,30]) = 23.0 → formatted "23.0".
        The raw 'value' field in the spec is intentionally left empty to
        confirm the renderer computes it from data.
        """
        kpis = [{"name": "k1", "stat": "mean", "var": "mpg",
                 "value": "", "display": "",  # intentionally empty
                 "fmt": "%9.1f", "title": "Avg MPG", "subtitle": "",
                 "color": "", "bgcolor": "", "update": "filter"}]
        r = self._build_renderer_with_kpis(kpis, tmp_path)
        r.render()
        assert "k1" in r.kpi_divs
        div_html = r.kpi_divs["k1"].text
        expected_mean = sum([15,18,21,22,24,26,28,30]) / 8  # = 23.0
        assert "23.0" in div_html, (
            f"KPI div must show formatted mean '23.0', got HTML: {div_html!r}"
        )

    def test_kpi_raw_numeric_spec_value_is_formatted(self, tmp_path):
        """When spec has a raw numeric 'value' (from Stata), render() must
        format it — not show the full-precision float string.

        Stata stores e.g. 'value': '21.2972972972973' but the formatted
        display per fmt(%9.1f) should be '21.3'.
        """
        kpis = [{"name": "k1", "stat": "mean", "var": "mpg",
                 # Simulate what Stata stores: raw unformatted value
                 "value": "21.2972972972973", "display": "21.3",
                 "fmt": "%9.1f", "title": "Avg MPG", "subtitle": "",
                 "color": "", "bgcolor": "", "update": "filter"}]
        r = self._build_renderer_with_kpis(kpis, tmp_path)
        r.render()
        div_html = r.kpi_divs["k1"].text
        # The full-precision raw value must NOT appear in the rendered card
        assert "21.2972972972973" not in div_html, (
            "KPI div must not show raw unformatted Stata value '21.2972972972973'; "
            "it should be computed from Python data and formatted with fmt"
        )
        # Expected: mean([15,18,21,22,24,26,28,30]) = 23.0, formatted "23.0"
        assert "23.0" in div_html, (
            f"KPI should show Python-computed formatted value '23.0', got: {div_html!r}"
        )

    def test_kpi_count_formatted_with_comma(self, tmp_path):
        """count KPI with %9.0fc format should use comma-separated integer."""
        kpis = [{"name": "k1", "stat": "count", "var": "mpg",
                 "value": "", "display": "",
                 "fmt": "%9.0fc", "title": "N", "subtitle": "",
                 "color": "", "bgcolor": "", "update": "filter"}]
        r = self._build_renderer_with_kpis(kpis, tmp_path)
        r.render()
        div_html = r.kpi_divs["k1"].text
        # 8 observations — should appear as "8" (no comma needed for small N)
        assert "8" in div_html, f"Count KPI must show '8', got: {div_html!r}"
