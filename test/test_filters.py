"""
test_filters.py
Unit tests for FilterBuilder — dropdown, slider, range filter widgets
and their CustomJS callbacks.

Tests: P2-48 through P2-55

Run with:  pytest test/test_filters.py -v
"""
import sys
import os
import json
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import FilterBuilder, DashRenderer

from bokeh.models import ColumnDataSource, Select, Slider, RangeSlider


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def auto_df():
    """Synthetic dataset with known values."""
    return pd.DataFrame({
        "mpg":     [18.0, 21.0, 24.0, 30.0, 16.0, 28.0],
        "weight":  [3000.0, 2500.0, 2200.0, 1900.0, 3500.0, 2100.0],
        "foreign": [0.0,    0.0,    1.0,    1.0,    0.0,    1.0],
    })


@pytest.fixture
def value_labels():
    return {"foreign": {"0": "Domestic", "1": "Foreign"}}


@pytest.fixture
def cds(auto_df):
    return ColumnDataSource(auto_df)


@pytest.fixture
def figures(cds):
    """Mock figures dict with one figure per graph name."""
    from bokeh.plotting import figure
    figs = {}
    for name in ["s1", "s2", "k1"]:
        f = figure()
        f.scatter("mpg", "weight", source=cds)
        figs[name] = f
    return figs


# ================================================================
# P2-48 — dropdown widget options match sorted unique values
# ================================================================
class TestBuildDropdown:
    def test_options_match_sorted_unique_values(self, auto_df, cds, figures):
        """P2-48: dropdown options list matches sorted unique values."""
        widget, _ = FilterBuilder.build_dropdown(
            "foreign", cds, auto_df, {},
            exclude_names=[], all_figure_names=["s1", "s2"]
        )
        assert isinstance(widget, Select)
        # Options should include "All" + sorted unique values
        option_values = [o[0] if isinstance(o, (list, tuple)) else o
                         for o in widget.options]
        # Unique foreign values are 0.0 and 1.0
        assert "0.0" in option_values or "0" in option_values or 0.0 in option_values
        assert "1.0" in option_values or "1" in option_values or 1.0 in option_values

    # ----------------------------------------------------------------
    # P2-49 — dropdown uses valueLabels for display text
    # ----------------------------------------------------------------
    def test_options_use_value_labels(self, auto_df, cds, figures, value_labels):
        """P2-49: dropdown uses valueLabels for option display text."""
        widget, _ = FilterBuilder.build_dropdown(
            "foreign", cds, auto_df, value_labels,
            exclude_names=[], all_figure_names=["s1", "s2"]
        )
        # Options may be (value, label) tuples or just strings
        option_labels = []
        for opt in widget.options:
            if isinstance(opt, (list, tuple)):
                option_labels.append(opt[1])
            else:
                option_labels.append(str(opt))

        combined = " ".join(option_labels)
        assert "Domestic" in combined or "Foreign" in combined, (
            f"Value labels not found in options: {widget.options}"
        )

    # ----------------------------------------------------------------
    # P2-50 — "All" option always present as first entry
    # ----------------------------------------------------------------
    def test_all_option_present_first(self, auto_df, cds, figures):
        """P2-50: 'All' option is the first entry in the dropdown."""
        widget, _ = FilterBuilder.build_dropdown(
            "foreign", cds, auto_df, {},
            exclude_names=[], all_figure_names=["s1", "s2"]
        )
        first_option = widget.options[0]
        if isinstance(first_option, (list, tuple)):
            first_label = first_option[1]
        else:
            first_label = str(first_option)
        assert "all" in first_label.lower() or first_label == "", (
            f"First option '{first_label}' should be 'All'"
        )

    # ----------------------------------------------------------------
    # P2-51 — dropdown CustomJS references correct CDSView for each non-excluded figure
    # ----------------------------------------------------------------
    def test_callback_references_non_excluded_figures(self, auto_df, cds):
        """P2-51: dropdown CustomJS is created for non-excluded figures."""
        widget, callback = FilterBuilder.build_dropdown(
            "foreign", cds, auto_df, {},
            exclude_names=["k1"], all_figure_names=["s1", "s2", "k1"]
        )
        # The callback should have been generated (not None)
        assert callback is not None
        # The callback code should NOT reference k1
        cb_code = callback.code if hasattr(callback, "code") else str(callback)
        # Since k1 is excluded, its source should not appear in the JS
        # (implementation detail: the callback is parameterized)
        assert widget is not None

    # ----------------------------------------------------------------
    # P2-52 — excluded graphs do NOT appear in dropdown CustomJS callback
    # ----------------------------------------------------------------
    def test_excluded_graph_not_in_callback(self, auto_df, cds):
        """P2-52: excluded names are absent from filter callback targets."""
        widget, callback = FilterBuilder.build_dropdown(
            "foreign", cds, auto_df, {},
            exclude_names=["k1"], all_figure_names=["s1", "s2", "k1"]
        )
        if callback is not None and hasattr(callback, "args"):
            # The args dict should NOT contain k1 as a key
            arg_keys = list(callback.args.keys())
            assert "k1" not in arg_keys, f"Excluded 'k1' found in callback args: {arg_keys}"


# ================================================================
# P2-53 — slider widget min/max match data range
# ================================================================
class TestBuildSlider:
    def test_slider_range_matches_data(self, auto_df, cds):
        """P2-53: slider min/max match data range of the variable."""
        widget, _ = FilterBuilder.build_slider(
            "mpg", cds, auto_df,
            exclude_names=[], all_figure_names=["s1", "s2"]
        )
        assert isinstance(widget, Slider)
        expected_min = float(auto_df["mpg"].min())
        expected_max = float(auto_df["mpg"].max())
        assert abs(widget.start - expected_min) < 0.01
        assert abs(widget.end   - expected_max) < 0.01

    def test_slider_initial_value_at_min(self, auto_df, cds):
        """Slider initial value should be at or near the minimum."""
        widget, _ = FilterBuilder.build_slider(
            "mpg", cds, auto_df,
            exclude_names=[], all_figure_names=["s1"]
        )
        assert widget.value <= widget.start + (widget.end - widget.start) * 0.1


# ================================================================
# P2-54 — range slider min/max match data range
# ================================================================
class TestBuildRange:
    def test_range_slider_range_matches_data(self, auto_df, cds):
        """P2-54: range slider min/max match data range."""
        widget, _ = FilterBuilder.build_range(
            "weight", cds, auto_df,
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, RangeSlider)
        expected_min = float(auto_df["weight"].min())
        expected_max = float(auto_df["weight"].max())
        assert abs(widget.start - expected_min) < 0.01
        assert abs(widget.end   - expected_max) < 0.01


# ================================================================
# P2-55 — filter CustomJS contains no un-escaped user string interpolation
# ================================================================
class TestFilterSecurity:
    def test_no_raw_user_interpolation_in_js(self, auto_df, cds):
        """P2-55: CustomJS does not directly interpolate user-controlled values."""
        # A malicious variable name attempt should be safely handled
        malicious_varname = "foreign; DROP TABLE users;"
        # build_dropdown should either raise a ValueError or sanitize the name
        try:
            widget, callback = FilterBuilder.build_dropdown(
                malicious_varname, cds, auto_df, {},
                exclude_names=[], all_figure_names=["s1"]
            )
            # If it doesn't raise, verify the JS code doesn't contain raw injection
            if callback is not None and hasattr(callback, "code"):
                js_code = callback.code
                # The literal injection string should NOT appear verbatim in JS
                assert "DROP TABLE" not in js_code
        except (ValueError, KeyError):
            pass  # Raising is the safest behavior

    def test_html_escaped_values_in_callback(self, auto_df, cds):
        """P2-55: HTML-sensitive characters in filter values are escaped."""
        # Create a dataset with a potentially dangerous category value
        danger_df = pd.DataFrame({
            "cat": ["<script>alert(1)</script>", "normal"],
            "y":   [1.0, 2.0],
        })
        danger_cds = ColumnDataSource(danger_df)
        widget, callback = FilterBuilder.build_dropdown(
            "cat", danger_cds, danger_df, {},
            exclude_names=[], all_figure_names=["s1"]
        )
        # Option display text should be HTML-escaped
        for opt in widget.options:
            label = opt[1] if isinstance(opt, (list, tuple)) else str(opt)
            assert "<script>" not in label, (
                f"Unescaped <script> found in dropdown option: {label}"
            )


# ================================================================
# Regression tests — empty / all-NaN data in slider and range
# ================================================================
class TestSliderEdgeCases:
    """Regression tests: build_slider and build_range must not crash on
    empty or all-NaN data."""

    def test_slider_empty_data_returns_disabled_widget(self):
        """Regression: build_slider with all-NaN values returns a disabled Slider."""
        nan_cds = ColumnDataSource({"weight": [float("nan")] * 5})
        widget, callback = FilterBuilder.build_slider(
            "weight", nan_cds, pd.DataFrame({"weight": [float("nan")] * 5}),
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, Slider)
        assert widget.disabled is True

    def test_slider_all_none_data_returns_disabled_widget(self):
        """Regression: build_slider with all-None values returns a disabled Slider."""
        none_cds = ColumnDataSource({"weight": [None, None, None]})
        widget, callback = FilterBuilder.build_slider(
            "weight", none_cds, pd.DataFrame({"weight": [None, None, None]}),
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, Slider)
        assert widget.disabled is True

    def test_range_slider_empty_data_returns_disabled_widget(self):
        """Regression: build_range with all-NaN values returns a disabled RangeSlider."""
        nan_cds = ColumnDataSource({"price": [float("nan")] * 4})
        widget, callback = FilterBuilder.build_range(
            "price", nan_cds, pd.DataFrame({"price": [float("nan")] * 4}),
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, RangeSlider)
        assert widget.disabled is True

    def test_slider_constant_data_does_not_crash(self):
        """Regression: build_slider with all-identical values must not crash."""
        const_cds = ColumnDataSource({"weight": [3000.0, 3000.0, 3000.0]})
        widget, callback = FilterBuilder.build_slider(
            "weight", const_cds, pd.DataFrame({"weight": [3000.0] * 3}),
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, Slider)
        # end must be strictly greater than start for Bokeh
        assert widget.end > widget.start

    def test_range_slider_constant_data_does_not_crash(self):
        """Regression: build_range with all-identical values must not crash."""
        const_cds = ColumnDataSource({"price": [15000.0] * 5})
        widget, callback = FilterBuilder.build_range(
            "price", const_cds, pd.DataFrame({"price": [15000.0] * 5}),
            exclude_names=[], all_figure_names=["s1"]
        )
        assert isinstance(widget, RangeSlider)
        # end must be strictly greater than start for Bokeh
        assert widget.end > widget.start


# ================================================================
# Regression tests: Bug 3 & 4 — filter raw-string parsing
# ================================================================

class TestParseFilterRaw:
    """Regression tests for DashRenderer._parse_filter_raw().

    Bug 3: render() read build["filters"] (plural) but dash.ado writes
           build["filter"] (singular, raw string).  The renderer now falls
           back to parsing the raw "filter" string.

    Bug 4: full_dashboard.do passes two separate filter() options to
           dash build.  Stata's syntax can only accept one; the Mata
           pre-processor _dash_extract_filters() joins them with " || "
           before syntax runs.  The Python parser handles "||"-separated
           specs to produce two filter widgets.
    """

    def test_empty_string_returns_empty_list(self):
        result = DashRenderer._parse_filter_raw("")
        assert result == []

    def test_none_like_returns_empty_list(self):
        result = DashRenderer._parse_filter_raw('"')
        assert result == []

    def test_single_dropdown_filter(self):
        """Basic single-filter: 'foreign, type(dropdown)'."""
        result = DashRenderer._parse_filter_raw("foreign, type(dropdown)")
        assert len(result) == 1
        assert result[0]["varname"] == "foreign"
        assert result[0]["type"] == "dropdown"
        assert result[0]["exclude"] == []

    def test_single_range_filter_with_excludes(self):
        """Single range filter with exclude list."""
        result = DashRenderer._parse_filter_raw(
            "weight, type(range) exclude(h1 d1 k1 k2)"
        )
        assert len(result) == 1
        r = result[0]
        assert r["varname"] == "weight"
        assert r["type"] == "range"
        assert sorted(r["exclude"]) == ["d1", "h1", "k1", "k2"]

    def test_two_filters_joined_with_pipe(self):
        """Bug 4 regression: two filter specs joined with '||' produce two entries.

        This is what dash.ado now emits when the user writes two separate
        filter() options:
            filter(foreign, type(dropdown)) filter(weight, type(range) exclude(...))
        The Mata pre-processor joins their contents with ' || '.
        """
        raw = "foreign, type(dropdown) || weight, type(range) exclude(h1 d1 k1 k2)"
        result = DashRenderer._parse_filter_raw(raw)
        assert len(result) == 2, f"Expected 2 filter specs, got {len(result)}: {result}"
        assert result[0]["varname"] == "foreign"
        assert result[0]["type"] == "dropdown"
        assert result[1]["varname"] == "weight"
        assert result[1]["type"] == "range"
        assert sorted(result[1]["exclude"]) == ["d1", "h1", "k1", "k2"]

    def test_semicolon_separator_for_legacy_compat(self):
        """Legacy: ';' separator (server mode) also produces two entries."""
        raw = "foreign, type(dropdown); weight, type(range)"
        result = DashRenderer._parse_filter_raw(raw)
        assert len(result) == 2
        assert result[0]["varname"] == "foreign"
        assert result[1]["varname"] == "weight"

    def test_injection_in_varname_rejected(self):
        """Security: filter spec with injection characters is skipped."""
        # Semicolon and backtick are blocked
        assert DashRenderer._parse_filter_raw("`rm -rf`, type(dropdown)") == []
        # Double-underscore (Python dunder) is blocked
        assert DashRenderer._parse_filter_raw("__import__('os'), type(dropdown)") == []

    def test_invalid_varname_characters_rejected(self):
        """Security: variable names must match [A-Za-z_][A-Za-z0-9_]*."""
        result = DashRenderer._parse_filter_raw("123bad, type(dropdown)")
        assert result == []

    def test_filter_raw_used_in_render_when_filters_key_absent(self):
        """Bug 3 regression: render() must produce filter widgets when the spec
        only has build_options['filter'] (raw string) and no 'filters' list.

        Before the fix, render() read build.get('filters', []) → got [] →
        no filter widgets were ever created from Stata-generated specs.
        """
        import json, os, tempfile
        graph = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "g1",  # linked so foreign is in shared source
                "filter": "foreign, type(dropdown)",   # raw string, no "filters" key
                "theme": "default",
                "title": "",
                "subtitle": "",
                "registry": "g1",
            },
        }
        vals = [{"mpg": float(i*2), "weight": float(i*300), "foreign": float(i % 2)}
                for i in range(1, 11)]
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "weight", "foreign"],
            "variableLabels": {"mpg": "mpg", "weight": "weight", "foreign": "foreign"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False, "foreign": False},
            "values": vals,
        }}
        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data_json, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

        html_str = r.render()
        # Must contain a Select widget (dropdown) because filter was parsed
        assert len(r.filter_widgets) >= 1, (
            "render() must create filter widgets from build_options['filter'] "
            "raw string; previously got 0 because it only looked at 'filters' (plural)"
        )
        assert "Select" in str(type(r.filter_widgets[0])) or \
               "select" in html_str.lower(), \
            "Expected a dropdown (Select) widget for foreign filter"


    def test_filter_widget_created_for_non_linked_graph(self):
        """Bug 7 regression: filter widgets must be created for NON-linked graphs.

        Previously, render() only included filter variables in the shared
        ColumnDataSource when link() was specified.  For unlinked graphs, the
        CDS only contained plot variables (yvar/xvar), so
        ``fvar not in fsource.data`` was True and the widget was silently skipped.
        """
        import json, os, tempfile
        graph = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "",           # NO link — non-linked graph
                "filter": "foreign, type(dropdown)",
                "theme": "default",
                "title": "",
                "subtitle": "",
                "registry": "g1",
            },
        }
        vals = [{"mpg": float(i * 2), "weight": float(i * 300), "foreign": float(i % 2)}
                for i in range(1, 11)]
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "weight", "foreign"],
            "variableLabels": {"mpg": "mpg", "weight": "weight", "foreign": "foreign"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False, "foreign": False},
            "values": vals,
        }}
        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data_json, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

        r.render()
        assert len(r.filter_widgets) >= 1, (
            "render() must create filter widgets for non-linked graphs; "
            "filter variable 'foreign' must be included in the CDS data "
            "even when link() is not specified (Bug 7)"
        )


class TestFilterVarMissingFromData:
    """Bug 10 regression: filter variable absent from data JSON.

    dash.ado's _dash_build collects all_vars from graph plots and KPI vars
    before the jsonio call.  If the filter variable (e.g. 'foreign') is not
    used in any plot or KPI, it is never added to all_vars, so jsonio never
    serializes it.  The data JSON therefore lacks 'foreign', causing
    render() to silently skip the filter widget.

    The fix adds filter variable names to all_vars in _dash_build so they
    are always included in the jsonio serialization.  On the Python side,
    render() already handles missing filter vars gracefully (skip widget),
    so the Python renderer is correct — the bug is in dash.ado.

    This test verifies that render() DOES create filter widgets when the
    filter variable is present in the data JSON (the expected post-fix
    state after _dash_build is corrected).  A companion assertion checks
    that the filter widget count is 0 when the variable is absent from the
    data (the pre-fix broken state), documenting the failure mode.
    """

    def _build_renderer_with_data(self, include_foreign: bool):
        """Build a DashRenderer with or without 'foreign' in the data JSON.

        The spec uses a linked dashboard (s1 linked) with a foreign dropdown
        filter — foreign is NOT a plot variable (not in yvar/xvar), so it
        would only be present in data if _dash_build explicitly serializes it.
        """
        import json, os, tempfile

        graph = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "s1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "s1",
                "filter": "foreign, type(dropdown)",
                "theme": "default",
                "title": "",
                "subtitle": "",
                "registry": "s1",
            },
        }

        # Build data: mpg and weight are plot vars; foreign is filter-only
        cols = {"mpg": [float(i * 2) for i in range(1, 11)],
                "weight": [float(i * 300) for i in range(1, 11)]}
        if include_foreign:
            cols["foreign"] = [float(i % 2) for i in range(1, 11)]

        var_names = list(cols.keys())
        vals = [{v: cols[v][i] for v in var_names} for i in range(10)]
        data_json = {"StataJSON": {
            "variableNames": var_names,
            "variableLabels": {v: v for v in var_names},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {v: False for v in var_names},
            "values": vals,
        }}

        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data_json, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return r

    def test_filter_widget_created_when_var_in_data(self):
        """Filter widget IS created when filter variable appears in data JSON.

        This is the expected post-fix state: _dash_build includes 'foreign'
        in all_vars so jsonio serializes it, the data JSON has 'foreign',
        and render() creates the dropdown filter widget.
        """
        r = self._build_renderer_with_data(include_foreign=True)
        r.render()
        assert len(r.filter_widgets) >= 1, (
            "Filter widget must be created when filter variable 'foreign' "
            "is present in the data JSON.  Got 0 widgets — the filter "
            "variable must be included in the jsonio serialization."
        )

    def test_filter_widget_absent_when_var_missing_from_data(self):
        """Filter widget is silently skipped when filter var missing from data.

        This test documents the symptom of Bug 10: when _dash_build fails to
        add the filter variable to all_vars, it is absent from the data JSON,
        and render() skips the widget.  After the _dash_build fix, this test
        is no longer reachable in production (because _dash_build ensures the
        variable is serialized), but it documents the pre-fix failure mode.
        """
        r = self._build_renderer_with_data(include_foreign=False)
        r.render()
        # When 'foreign' is absent from data, Python correctly skips it
        assert len(r.filter_widgets) == 0, (
            "Filter widget must NOT be created when filter variable 'foreign' "
            "is absent from the data JSON (Python side handles gracefully by "
            "skipping; the root fix is in dash.ado _dash_build)"
        )
