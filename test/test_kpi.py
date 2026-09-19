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
# The test directory too, so the shared conftest helpers are importable by
# name the way the newer test files do it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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

    def test_div_echoes_the_value_it_is_given(self, renderer_with_data):
        """P2-42: the Div renders ``value``, and only ``value``.

        This was called "contains the formatted value" and passed
        ``value="74"`` alongside ``display="74"`` and ``fmt="%9.0fc"``, so it
        could not tell which of the three the Div used and would have passed
        had formatting broken entirely. Measured: the Div echoes ``value``
        and never consults ``fmt`` or ``display``. Formatting happens
        earlier, in ``_format_kpi_value``/``_effective_kpi_fmt``, and is
        covered by test_kpi_values.py — so the honest thing for this test to
        pin is the echo.
        """
        div = renderer_with_data._make_kpi_div({
            "name": "k2", "stat": "count", "var": "mpg",
            "value": "74", "display": "999",
            "fmt": "%9.0fc", "title": "Sample Size", "subtitle": "",
            "color": "", "bgcolor": "", "update": "brush"
        })
        assert "74" in div.text
        assert "999" not in div.text, (
            "the Div used `display' rather than `value'; the two are "
            "different here precisely so this can tell them apart"
        )

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
    """Which callback a KPI's update() mode actually wires.

    These two tests used to read ``renderer._kpi_update_modes``, a dict that
    is initialised and **never written to** — measured by calling
    ``_make_kpi_div`` with update(filter), update(brush) and a mode that does
    not exist, and getting ``{}`` every time. Both assertions were of the
    form ``kpi_info is None or kpi_info == "filter"``, which is true for
    every possible input including nonsense, so they could not fail.

    They assert the real mechanism now: a filter-mode KPI is in the filter
    callback's config and has no selection callback, a brush-mode KPI is the
    other way round, and ``both`` gets both.
    """

    @staticmethod
    def _dash(update):
        import json as _json
        import tempfile as _tf
        import numpy as _np
        import pandas as _pd
        from conftest import make_spec as _ms, make_data_json as _md

        df = _pd.DataFrame({"mpg": _np.linspace(12.0, 41.0, 20),
                            "weight": _np.linspace(1760.0, 4840.0, 20)})
        spec = _ms([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                     "options": {}}])
        spec["kpis"] = [{"name": "k1", "stat": "mean", "var": "mpg",
                         "title": "T", "fmt": "%9.2f", "update": update}]
        spec["build_options"]["registry"] = "k1 g1"
        spec["build_options"]["filters"] = [
            {"varname": "weight", "type": "range", "exclude": [],
             "label": ""}]
        sp = _tf.mkstemp(".json")[1]
        dp = _tf.mkstemp(".json")[1]
        op = _tf.mkstemp(".html")[1]
        with open(sp, "w") as f:
            _json.dump(spec, f)
        with open(dp, "w") as f:
            _json.dump(_md(df), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for q in (sp, dp, op):
            try:
                os.unlink(q)
            except OSError:
                pass
        in_filter = bool(_json.loads(
            dr.filter_callbacks[0].args["kpi_config_json"]))
        n_sel = sum(
            len(getattr(src.selected, "js_property_callbacks", {}) or {})
            for src in dr.sources.values()
            if getattr(src, "selected", None) is not None)
        return in_filter, n_sel

    def test_update_filter_wires_the_filter_callback_only(self):
        in_filter, n_sel = self._dash("filter")
        assert in_filter, "a filter KPI is not in the filter callback"
        assert n_sel == 0, "a filter KPI got a selection callback"

    def test_update_brush_wires_a_selection_callback(self):
        in_filter, n_sel = self._dash("brush")
        assert n_sel > 0, "update(brush) attaches no selection callback"

    def test_update_both_wires_both(self):
        in_filter, n_sel = self._dash("both")
        assert in_filter and n_sel > 0, (in_filter, n_sel)

    def test_no_mode_recomputes_on_nothing(self):
        """The defect these replaced could not see: a frozen card."""
        for mode in ("filter", "brush", "both"):
            in_filter, n_sel = self._dash(mode)
            assert in_filter or n_sel, (
                f"update({mode}) recomputes on neither filters nor brushing"
            )


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


# ================================================================
# Bug 8: Multi-word KPI title/subtitle truncated by Stata word()
# ================================================================
class TestKpiMultiWordTitle:
    """Regression: KPI title/subtitle with spaces must appear in full in the div.

    dash.ado stored all KPI fields in a semicolon-delimited global then
    extracted them with word(subinstr(...,';',' ',.),N).  That method splits
    on any whitespace, so 'Avg MPG' (two tokens) was extracted as just 'Avg'
    at position 6 and 'MPG' was picked up as the subtitle at position 7.

    After the fix (separate per-field globals), the full title string must
    appear intact in the rendered KPI div HTML (Bug 8).
    """

    def _build_renderer_with_kpi(self, kpi_spec: dict, tmp_path) -> DashRenderer:
        """Build a minimal DashRenderer with one KPI card."""
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [kpi_spec],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        data_json = {
            "StataJSON": {
                "variableNames": ["x", "y"],
                "variableLabels": {"x": "x", "y": "y"},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {"x": False, "y": False},
                "values": [{"x": float(i), "y": float(i * 2)} for i in range(1, 11)],
            }
        }
        sp = str(tmp_path / "spec.json")
        dp = str(tmp_path / "data.json")
        op = str(tmp_path / "out.html")
        with open(sp, "w") as f: json.dump(spec, f)
        with open(dp, "w") as f: json.dump(data_json, f)
        open(op, "w").close()
        return DashRenderer(sp, dp, op)

    def test_multiword_title_appears_in_full(self, tmp_path):
        """KPI title 'Avg MPG' must appear in full in div text, not truncated to 'Avg'."""
        kpi = {"name": "k1", "stat": "mean", "var": "y",
               "value": "", "display": "",
               "fmt": "%9.1f", "title": "Avg MPG", "subtitle": "Miles per gallon",
               "color": "#2c3e50", "bgcolor": "#ecf0f1", "update": "filter"}
        r = self._build_renderer_with_kpi(kpi, tmp_path)
        r.render()
        div_html = r.kpi_divs["k1"].text
        assert "Avg MPG" in div_html, (
            f"KPI title 'Avg MPG' must appear in full — got: {div_html!r} "
            "(Bug 8: Stata word() extraction truncates multi-word titles)"
        )
        assert "Miles per gallon" in div_html, (
            f"KPI subtitle 'Miles per gallon' must appear in full — got: {div_html!r}"
        )

    def test_multiword_subtitle_appears_in_full(self, tmp_path):
        """KPI subtitle 'Sample Size' must appear in full, not as first token only."""
        kpi = {"name": "k1", "stat": "count", "var": "y",
               "value": "", "display": "",
               "fmt": "%9.0fc", "title": "Sample Size", "subtitle": "Total observations",
               "color": "", "bgcolor": "", "update": "both"}
        r = self._build_renderer_with_kpi(kpi, tmp_path)
        r.render()
        div_html = r.kpi_divs["k1"].text
        assert "Sample Size" in div_html, (
            f"KPI title 'Sample Size' must appear in full — got: {div_html!r}"
        )
        assert "Total observations" in div_html, (
            f"KPI subtitle 'Total observations' must appear in full — got: {div_html!r}"
        )

    def test_multiword_title_with_color_and_bgcolor(self, tmp_path):
        """Color/bgcolor must be correct even when title/subtitle have spaces.

        The Stata word() bug shifted color to position of last title word;
        this test ensures the hex color actually appears in the rendered div.
        """
        kpi = {"name": "k1", "stat": "mean", "var": "y",
               "value": "", "display": "",
               "fmt": "%9.1f", "title": "Median Price", "subtitle": "1978 USD",
               "color": "#2c3e50", "bgcolor": "#ecf0f1", "update": "filter"}
        r = self._build_renderer_with_kpi(kpi, tmp_path)
        r.render()
        div_html = r.kpi_divs["k1"].text
        assert "Median Price" in div_html, (
            f"Title 'Median Price' must appear in full — got: {div_html!r}"
        )
        assert "1978 USD" in div_html, (
            f"Subtitle '1978 USD' must appear in full — got: {div_html!r}"
        )
        # bgcolor should appear in the div styling
        assert "#ecf0f1" in div_html, (
            f"bgcolor '#ecf0f1' must be in div style — got: {div_html!r} "
            "(Bug 8: bgcolor was shifted by multi-word title tokens)"
        )


# ================================================================
# Bug 12 — Empty color/bgcolor in KPI JSON produces invalid CSS
# ================================================================
class TestKpiEmptyColorFallback:
    """When color or bgcolor is an empty string (not absent), _make_kpi_div
    must fall back to default colors instead of emitting 'color:;' or
    'background:;' which are invalid CSS properties.

    full_dashboard.do's k2/k3/k4 KPI cards have no color/bgcolor specified,
    so Stata writes empty strings in the JSON:  "color":"","bgcolor":"".
    Before the fix, _make_kpi_div emitted style="...background:;...color:;"
    which browsers silently ignore, producing unstyled cards.
    """

    def _make_renderer_with_kpi(self, kpi_def: dict, tmp_path):
        import json, os, tempfile
        from dash_render import DashRenderer

        graphs = [{"plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                               "options": {}, "if_expr": "", "in_expr": ""}],
                   "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": ""}]
        spec = {"graphs": graphs, "kpis": [kpi_def],
                "build_options": {"layout": "auto", "link": "", "filter": "",
                                  "theme": "default", "title": "", "subtitle": "",
                                  "registry": "g1 " + kpi_def.get("name", "k1")}}
        data_dict = {"StataJSON": {"variableNames": ["y", "x"],
                                   "variableLabels": {"y": "y", "x": "x"},
                                   "valueLabels": {}, "valueLabelNames": {},
                                   "variableTypeIsString": {"y": False, "x": False},
                                   "values": [{"y": float(i), "x": float(i)} for i in range(1, 11)]}}
        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data_dict, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return r

    def test_empty_bgcolor_uses_default_not_invalid_css(self, tmp_path):
        """Bug 12: empty bgcolor='' must fall back to default, not emit 'background:;'."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from dash_render import DashRenderer

        kpi_def = {"name": "k2", "stat": "mean", "var": "y",
                   "value": "5.5", "display": "5.5",
                   "fmt": "%9.1f", "title": "Avg Y", "subtitle": "units",
                   "color": "", "bgcolor": "", "update": "filter"}
        r = self._make_renderer_with_kpi(kpi_def, tmp_path)
        r.render()
        div_html = r.kpi_divs["k2"].text
        assert "background:;" not in div_html, (
            "Bug 12: empty bgcolor produced invalid CSS 'background:;'. "
            "_make_kpi_div must fall back to default color '#f8f9fa' when bgcolor is empty."
        )
        # Should contain a valid background color (the default)
        assert "background:#f8f9fa" in div_html or "background: #f8f9fa" in div_html, (
            f"Default bgcolor '#f8f9fa' not found in div HTML: {div_html[:400]}"
        )

    def test_empty_color_uses_default_not_invalid_css(self, tmp_path):
        """Bug 12: empty color='' must fall back to default, not emit 'color:;'."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from dash_render import DashRenderer

        kpi_def = {"name": "k3", "stat": "count", "var": "y",
                   "value": "10", "display": "10",
                   "fmt": "%9.0f", "title": "Count", "subtitle": "",
                   "color": "", "bgcolor": "", "update": "filter"}
        r = self._make_renderer_with_kpi(kpi_def, tmp_path)
        r.render()
        div_html = r.kpi_divs["k3"].text
        assert "color:;" not in div_html, (
            "Bug 12: empty color produced invalid CSS 'color:;'. "
            "_make_kpi_div must fall back to default '#212529' when color is empty."
        )
        # The default color should appear
        assert "#212529" in div_html, (
            f"Default color '#212529' not found in div HTML: {div_html[:400]}"
        )


# ================================================================
# Bug 14 — KPI "var" key not collected in all_vars
# ================================================================
class TestKpiVarKeyInAllVars:
    """Bug 14 regression: render() collected KPI variables via kpi.get('varname')
    but dash.ado emits 'var' not 'varname'.  When a KPI references a variable
    that appears nowhere in any graph plot, the variable would be absent from
    self.df, causing _compute_kpi_stat() to fail silently and fall back to the
    Stata-precomputed display value rather than Python-recomputed value.

    The fix: in the all_vars collection loop, use
        kpi.get("var") or kpi.get("varname", "")
    so that both key spellings are handled.
    """

    def _make_renderer_kpi_only_var(self, tmp_path):
        """Create a renderer where the KPI variable ('z') does NOT appear in any graph.

        Graph plots use only 'y' and 'x'.  The KPI references 'z' exclusively.
        Before the fix, 'z' would be absent from all_vars and therefore absent
        from self.df, causing _compute_kpi_stat to return None / fall back.
        """
        import json, os, tempfile
        from dash_render import DashRenderer

        graphs = [{"plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                               "options": {}, "if_expr": "", "in_expr": ""}],
                   "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": ""}]
        kpi_def = {"name": "k1", "stat": "mean", "var": "z",
                   "value": "999.0", "display": "999.0",
                   "fmt": "%9.1f", "title": "Mean Z", "subtitle": "",
                   "color": "", "bgcolor": "", "update": "filter"}
        spec = {"graphs": graphs, "kpis": [kpi_def],
                "build_options": {"layout": "auto", "link": "", "filter": "",
                                  "theme": "default", "title": "", "subtitle": "",
                                  "registry": "g1 k1"}}
        # Data includes 'z' column with known mean (5.5 for 1..10)
        data_dict = {"StataJSON": {
            "variableNames": ["y", "x", "z"],
            "variableLabels": {"y": "y", "x": "x", "z": "z"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"y": False, "x": False, "z": False},
            "values": [{"y": float(i), "x": float(i), "z": float(i)}
                       for i in range(1, 11)],
        }}
        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data_dict, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return r

    def test_kpi_var_key_loaded_into_dataframe(self):
        """Bug 14: KPI 'var' variable must be present in self.df after load.

        Before fix: kpi.get('varname') returned None when key is 'var',
        so 'z' was absent from all_vars and never loaded into self.df.
        After fix: 'z' is in all_vars and loaded into self.df.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_path:
            r = self._make_renderer_kpi_only_var(tmp_path)
            r.render()
            assert "z" in r.df.columns, (
                "Bug 14: KPI variable 'z' (stored under key 'var') must be "
                "loaded into self.df. Before the fix, kpi.get('varname') silently "
                "returned None and 'z' was excluded from all_vars."
            )

    def test_kpi_var_python_recomputed_not_stata_fallback(self):
        """Bug 14: KPI stat must be Python-recomputed from data, not Stata fallback.

        The KPI is initialized with value='999.0' (wrong Stata value).
        After Python recomputation: mean(z for z in 1..10) = 5.5.
        Before fix: 'z' absent from df → stat falls back to '999.0'.
        After fix: stat is correctly computed as '5.5'.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_path:
            r = self._make_renderer_kpi_only_var(tmp_path)
            r.render()
            k1_div = r.kpi_divs.get("k1")
            assert k1_div is not None, "KPI div 'k1' must be created"
            div_html = k1_div.text
            # The Python-recomputed mean of 1..10 is 5.5
            assert "5.5" in div_html, (
                f"Bug 14: KPI div must show Python-recomputed value '5.5', "
                f"not Stata fallback '999.0'. Got: {div_html[:300]}"
            )
            assert "999" not in div_html, (
                f"Bug 14: Stata fallback value '999' must not appear in KPI div. "
                f"Python recomputation from 'z' column must be used. Got: {div_html[:300]}"
            )
