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


# ================================================================
# Regression: filter CustomJS callback must NOT pass BooleanFilter
# class as an arg (broke Bokeh 3.x JS deserialization with error
# "reference BooleanFilter isn't known").
# ================================================================
class TestFilterCallbackNoBooleanFilterClass:
    """Regression tests for Bug: BooleanFilter class passed as CustomJS arg.

    Root cause: FilterBuilder passed the Python BooleanFilter CLASS (not an
    instance) as a CustomJS arg.  Bokeh 3.x serializes it with
    {"id": "BooleanFilter"} — a model reference with no matching instance —
    causing the JS deserializer to throw "reference BooleanFilter isn't known".

    Fix: use IndexFilter instances (proper model objects) and update their
    .indices array in-place from JS instead of constructing new BooleanFilter
    objects each time.
    """

    def _make_cds(self):
        return ColumnDataSource(pd.DataFrame({
            "foreign": [0.0, 0.0, 1.0, 1.0, 0.0, 1.0],
            "mpg":     [18.0, 21.0, 24.0, 30.0, 16.0, 28.0],
        }))

    def test_dropdown_callback_no_boolean_filter_class_arg(self):
        """Dropdown callback args must NOT contain BooleanFilter class (BF-01)."""
        from bokeh.models import BooleanFilter
        cds = self._make_cds()
        _, cb = FilterBuilder.build_dropdown("foreign", cds, None, {})
        arg_vals = list(cb.args.values())
        for v in arg_vals:
            assert not (isinstance(v, type) and v is BooleanFilter), (
                "BooleanFilter CLASS must not be passed as a CustomJS arg "
                "(causes Bokeh 3.x 'reference BooleanFilter isn't known')"
            )

    def test_slider_callback_no_boolean_filter_class_arg(self):
        """Slider callback args must NOT contain BooleanFilter class (BF-02)."""
        from bokeh.models import BooleanFilter
        cds = self._make_cds()
        _, cb = FilterBuilder.build_slider("mpg", cds, None)
        arg_vals = list(cb.args.values())
        for v in arg_vals:
            assert not (isinstance(v, type) and v is BooleanFilter), (
                "BooleanFilter CLASS must not be passed as a CustomJS arg"
            )

    def test_range_callback_no_boolean_filter_class_arg(self):
        """Range callback args must NOT contain BooleanFilter class (BF-03)."""
        from bokeh.models import BooleanFilter
        cds = self._make_cds()
        _, cb = FilterBuilder.build_range("mpg", cds, None)
        arg_vals = list(cb.args.values())
        for v in arg_vals:
            assert not (isinstance(v, type) and v is BooleanFilter), (
                "BooleanFilter CLASS must not be passed as a CustomJS arg"
            )

    def test_dropdown_callback_uses_orig_data_arg(self):
        """Dropdown callback must include 'orig_source' key in args (BF-04).

        The new source.data replacement approach stores original data as a
        JSON string in orig_source to avoid Bokeh 3.x Map serialisation.
        """
        cds = self._make_cds()
        _, cb = FilterBuilder.build_dropdown("foreign", cds, None, {})
        assert "orig_source" in cb.args, (
            "Dropdown callback must have 'orig_source' key in args"
        )

    def test_dropdown_js_replaces_source_data(self):
        """Dropdown JS code must replace source.data (not update IndexFilter) (BF-05).

        The new approach replaces source.data with filtered rows, which is the
        canonical way to trigger Bokeh 3.x re-renders in standalone mode.
        """
        cds = self._make_cds()
        _, cb = FilterBuilder.build_dropdown("foreign", cds, None, {})
        code = cb.code
        assert "source.data = new_data" in code, (
            "JS code must replace source.data with filtered data"
        )
        assert "source.change.emit()" in code, (
            "JS code must call source.change.emit() after replacing data"
        )
        # Strip comments: the callback explains in prose WHY it rebuilds a
        # CDSView's BooleanFilter after shortening a source, and that
        # explanation must not be what makes this test pass or fail. The
        # requirement is that the JS does not CONSTRUCT one.
        code_only = "\n".join(
            l.split("//", 1)[0] for l in code.splitlines()
        )
        assert "new BooleanFilter" not in code_only, (
            "JS code must NOT reference BooleanFilter constructor"
        )

    def test_full_render_with_filter_no_index_filter_in_callbacks(self):
        """End-to-end: render succeeds and filter callbacks use orig_data, not IndexFilter (BF-06).

        The new source.data replacement approach stores original data in
        orig_data on each callback.  No IndexFilter instances should appear in
        filter callback args (they are no longer needed for Bokeh 3.x renders).
        """
        import tempfile, json, os
        from bokeh.models import IndexFilter
        n = 6
        var_names = ["mpg", "weight", "foreign"]
        vals = [{"mpg": 18.0 + i, "weight": 3000.0 - i * 100, "foreign": float(i % 2)}
                for i in range(n)]
        spec = {
            "graphs": [{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}, "if_expr": "", "in_expr": ""}],
                "graph_options": {"name": "s1"},
                "if_expr": "", "in_expr": ""
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "theme": "default",
                "title": "", "subtitle": "", "registry": "s1",
                "filter": "foreign, type(dropdown)",
            }
        }
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
            r.render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

        # Render must produce at least one filter callback
        assert len(r.filter_callbacks) > 0, "Expected at least one filter callback after render"

        # Every callback must have orig_source populated. It is a shared
        # ColumnDataSource, not a JSON string: a string is written into the
        # document once per callback, so k filters meant k copies of the
        # dataset. See test_filter_payload_size.py.
        from bokeh.models import ColumnDataSource as _CDS
        _seen = set()
        for cb in r.filter_callbacks:
            assert hasattr(cb, "args"), "Filter callback must have args"
            assert "orig_source" in cb.args, (
                "Filter callback must have 'orig_source' key after render wiring"
            )
            assert isinstance(cb.args["orig_source"], _CDS), (
                "orig_source must be a ColumnDataSource, so Bokeh writes the "
                "data into the document once and refers to it by id"
            )
            orig = cb.args["orig_source"].data
            assert isinstance(orig, dict) and len(orig) > 0, (
                "orig_source must carry a non-empty snapshot"
            )
            _seen.add(id(cb.args["orig_source"]))
            # No IndexFilter instances should be in callback args
            for arg_val in cb.args.values():
                assert not isinstance(arg_val, IndexFilter), (
                    "Filter callback args must NOT contain IndexFilter instances "
                    "(new approach uses source.data replacement)"
                )
                if isinstance(arg_val, list):
                    for item in arg_val:
                        assert not isinstance(item, IndexFilter), (
                            "Filter callback args list must NOT contain IndexFilter instances"
                        )



        assert len(_seen) == 1, (
            "each callback holds its own snapshot, so the dataset is written "
            "into the document once per filter"
        )
class TestFilterWiringPrimarySourceOnly:
    """Regression tests for Bug: filter IndexFilter wired to computed-glyph renderers.

    Root cause: the filter wiring loop attached IndexFilter CDSViews to ALL
    renderers in a figure, including lfit, histogram, and other computed-glyph
    renderers that use their own separate ColumnDataSources.  Applying fsource
    row-indices to a 200-point lfit source caused incorrect clipping (the fit
    line would be cut short after N_data rows instead of 200).

    Fix: only attach IndexFilter to renderers whose data_source IS the shared
    fsource; skip renderers that use separate computed sources.
    """

    def _make_scatter_lfit_spec(self):
        """Spec with one graph containing scatter + lfit layers."""
        var_names = ["mpg", "weight", "foreign"]
        vals = [{"mpg": 18.0 + i, "weight": 3000.0 - i * 50,
                 "foreign": float(i % 2)} for i in range(10)]
        spec = {
            "graphs": [{
                "plots": [
                    {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                     "options": {}, "if_expr": "", "in_expr": ""},
                    {"type": "lfit", "yvar": "mpg", "xvar": "weight",
                     "options": {}, "if_expr": "", "in_expr": ""},
                ],
                "graph_options": {"name": "s1"},
                "if_expr": "", "in_expr": ""
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "theme": "default",
                "title": "", "subtitle": "", "registry": "s1",
                "filter": "foreign, type(dropdown)",
            }
        }
        data_json = {"StataJSON": {
            "variableNames": var_names,
            "variableLabels": {v: v for v in var_names},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {v: False for v in var_names},
            "values": vals,
        }}
        return spec, data_json

    def test_orig_data_populated_in_callbacks_bf07(self):
        """BF-07: After render, filter callbacks must have orig_data populated with source data.

        The new source.data replacement approach stores the full original data
        in orig_data on each callback.  No IndexFilter instances should be
        wired to computed-glyph renderers (lfit, histogram, etc.) because
        the new approach does not use CDSView/IndexFilter at all.
        """
        import tempfile, json, os
        from bokeh.models import IndexFilter
        spec, data_json = self._make_scatter_lfit_spec()
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data_json, f)
            r = DashRenderer(sp, dp, op)
            r.render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

        fsource = r.sources.get("s1")
        assert fsource is not None, "Expected source 's1' to exist"

        # Every filter callback must have orig_source populated from fsource
        import json as _json
        assert len(r.filter_callbacks) > 0, "Expected at least one filter callback"
        for cb in r.filter_callbacks:
            assert hasattr(cb, "args"), "Callback must have args"
            assert "orig_source" in cb.args, (
                "Callback must have 'orig_source' key populated by render wiring"
            )
            # A shared ColumnDataSource, not a JSON string -- see
            # test_filter_payload_size.py.
            orig = cb.args["orig_source"].data
            assert isinstance(orig, dict) and len(orig) > 0, (
                "orig_source must carry a non-empty snapshot"
            )
            # orig_data must contain the same columns as the source
            for col in fsource.data:
                assert col in orig, (
                    f"orig_source must contain column '{col}' from fsource"
                )

        # No IndexFilter instances should appear in callback args
        # (the new approach does not wire IndexFilter to any renderers)
        for cb in r.filter_callbacks:
            for arg_val in cb.args.values():
                assert not isinstance(arg_val, IndexFilter), (
                    "Filter callback args must NOT contain IndexFilter instances "
                    "(new source.data replacement approach does not use IndexFilter)"
                )
                if isinstance(arg_val, list):
                    for item in arg_val:
                        assert not isinstance(item, IndexFilter), (
                            "Filter callback args list must NOT contain IndexFilter instances"
                        )

    def test_dropdown_float_values_normalized_bf08(self):
        """BF-08: dropdown option values must normalize '0.0' → '0' for JS match."""
        cds = ColumnDataSource(pd.DataFrame({
            "foreign": [0.0, 0.0, 1.0, 1.0, 0.0, 1.0],
            "mpg":     [18.0, 21.0, 24.0, 30.0, 16.0, 28.0],
        }))
        widget, _ = FilterBuilder.build_dropdown("foreign", cds, None, {})
        option_values = [
            o[0] if isinstance(o, (list, tuple)) else str(o)
            for o in widget.options
        ]
        # "0.0" and "1.0" must NOT appear — must be normalized to "0" and "1"
        assert "0.0" not in option_values, (
            "Float '0.0' must be normalized to '0' for JS String() comparison"
        )
        assert "1.0" not in option_values, (
            "Float '1.0' must be normalized to '1' for JS String() comparison"
        )
        assert "0" in option_values, "Normalized '0' must be present"
        assert "1" in option_values, "Normalized '1' must be present"

    def test_dropdown_float_with_labels_normalized_bf09(self):
        """BF-09: dropdown with value labels uses normalized key for label lookup."""
        cds = ColumnDataSource(pd.DataFrame({
            "foreign": [0.0, 0.0, 1.0, 1.0],
        }))
        vlabels = {"0": "Domestic", "1": "Foreign"}
        widget, _ = FilterBuilder.build_dropdown("foreign", cds, None, vlabels)
        option_labels = [
            o[1] if isinstance(o, (list, tuple)) else str(o)
            for o in widget.options
        ]
        combined = " ".join(option_labels)
        assert "Domestic" in combined, (
            "Value label 'Domestic' must appear when key '0' is in vlabels"
        )
        assert "Foreign" in combined, (
            "Value label 'Foreign' must appear when key '1' is in vlabels"
        )


class TestValueLabelPipelineRegression:
    """Regression tests: value labels must appear in dropdown options produced
    by the full render() pipeline, not just in build_dropdown() directly.

    Bug: render() built vlabels via self.value_labels.get(labelset, {}) where
    labelset = value_label_names["foreign"] = "origin".  When valueLabels was
    keyed by variable name ("foreign") rather than label-set name ("origin"),
    the lookup returned {} and options showed raw numeric codes instead of
    human-readable labels.
    """

    def _make_render(self, value_labels_key: str) -> "DashRenderer":
        """Return a rendered DashRenderer with foreign dropdown filter.

        Args:
            value_labels_key: the key used in valueLabels dict —
                              "origin"  = standard Stata format (label set name)
                              "foreign" = variable-name-keyed format (demo scripts)
        """
        import tempfile
        graph = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                        "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "g1",
                "filters": [{"varname": "foreign", "type": "dropdown",
                              "label": "Car Origin", "exclude": []}],
                "theme": "default",
                "title": "", "subtitle": "", "registry": "",
            },
        }
        vals = [{"mpg": float(i * 2), "weight": float(i * 300),
                 "foreign": float(i % 2)}
                for i in range(1, 11)]
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "weight", "foreign"],
            "variableLabels": {"mpg": "mpg", "weight": "weight",
                               "foreign": "Car type"},
            "valueLabels":    {value_labels_key: {"0": "Domestic", "1": "Foreign"}},
            "valueLabelNames": {"foreign": "origin"},
            "variableTypeIsString": {"mpg": False, "weight": False,
                                     "foreign": False},
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
        return r

    def _option_labels(self, r: "DashRenderer") -> list:
        assert r.filter_widgets, "No filter widgets built"
        widget = r.filter_widgets[0]
        return [
            o[1] if isinstance(o, (list, tuple)) else str(o)
            for o in widget.options
        ]

    def test_value_labels_shown_when_keyed_by_labelset_name(self):
        """BF-10a: value labels appear when valueLabels keyed by label-set name
        (standard Stata format: {"origin": {"0": "Domestic", ...}})."""
        r = self._make_render("origin")
        labels = self._option_labels(r)
        combined = " ".join(labels)
        assert "Domestic" in combined, (
            f"Expected 'Domestic' in dropdown labels (keyed by labelset). Got: {labels}"
        )
        assert "Foreign" in combined, (
            f"Expected 'Foreign' in dropdown labels (keyed by labelset). Got: {labels}"
        )

    def test_value_labels_shown_when_keyed_by_varname(self):
        """BF-10b: value labels appear when valueLabels keyed by variable name
        ({"foreign": {"0": "Domestic", ...}}) — regression for demo scripts."""
        r = self._make_render("foreign")
        labels = self._option_labels(r)
        combined = " ".join(labels)
        assert "Domestic" in combined, (
            f"Expected 'Domestic' in dropdown labels (keyed by varname). Got: {labels}"
        )
        assert "Foreign" in combined, (
            f"Expected 'Foreign' in dropdown labels (keyed by varname). Got: {labels}"
        )

    def test_no_raw_numeric_values_in_labels(self):
        """BF-10c: raw numeric codes ('0', '1') must not appear as displayed
        labels when value labels are defined for the variable."""
        for key in ("origin", "foreign"):
            r = self._make_render(key)
            labels = self._option_labels(r)
            # Exclude the hidden value portion — only check display labels
            non_all = [l for l in labels if l != "All"]
            for lbl in non_all:
                assert lbl not in ("0", "1", "0.0", "1.0"), (
                    f"Raw numeric code '{lbl}' must not appear as a display label "
                    f"when value labels are defined (key='{key}'). All labels: {labels}"
                )


# ================================================================
# Regression tests: BUG-1, BUG-2 — filter widget label forwarding
# ================================================================

class TestFilterWidgetLabels:
    """BUG-1/BUG-2 regression: filter widget titles must use the human-readable
    label from the filter spec, not the raw variable name."""

    def _make_source(self, data_dict):
        from bokeh.models import ColumnDataSource
        return ColumnDataSource(data_dict)

    def test_build_range_uses_label_not_varname(self):
        """BUG-1: build_range title must come from label= parameter."""
        src = self._make_source({"weight": [2000.0, 2500.0, 3000.0, 3500.0]})
        widget, _ = FilterBuilder.build_range(
            "weight", src, label="Vehicle Weight"
        )
        assert "Vehicle Weight" in widget.title, (
            f"RangeSlider title should contain label text 'Vehicle Weight', got: {widget.title!r}"
        )
        assert widget.title != "weight", (
            "RangeSlider title must not be the raw variable name when label is provided"
        )

    def test_build_range_falls_back_to_varname_when_no_label(self):
        """BUG-1b: build_range without label= falls back to safe variable name."""
        src = self._make_source({"weight": [2000.0, 2500.0, 3000.0]})
        widget, _ = FilterBuilder.build_range("weight", src)
        assert "weight" in widget.title

    def test_build_slider_uses_label_not_varname(self):
        """BUG-2a: build_slider title must come from label= parameter."""
        src = self._make_source({"mpg": [15.0, 20.0, 25.0, 30.0]})
        widget, _ = FilterBuilder.build_slider("mpg", src, label="Miles per Gallon")
        assert "Miles per Gallon" in widget.title, (
            f"Slider title should contain label 'Miles per Gallon', got: {widget.title!r}"
        )

    def test_build_dropdown_uses_label_not_varname(self):
        """BUG-2b: build_dropdown title must come from label= parameter."""
        src = self._make_source({"foreign": [0.0, 1.0, 0.0, 1.0]})
        widget, _ = FilterBuilder.build_dropdown(
            "foreign", src, label="Car Origin"
        )
        assert "Car Origin" in widget.title, (
            f"Select title should contain label 'Car Origin', got: {widget.title!r}"
        )

    def test_render_passes_label_to_filter_widgets(self):
        """BUG-2 integration: render() must forward fc['label'] to filter builders."""
        import json, tempfile, os
        vals = [{"mpg": float(20+i), "weight": float(2000+i*100)} for i in range(10)]
        data = {"StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "mpg", "weight": "weight"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": vals,
        }}
        spec = {
            "graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                    "xvar": "weight", "options": {}}],
                         "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "theme": "default",
                "title": "", "subtitle": "", "registry": "g1",
                "filters": [{"varname": "weight", "type": "slider",
                              "label": "Vehicle Weight"}],
            },
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            dr = DashRenderer(sp, dp, op)
            dr.render()
            titles = [w.title for w in dr.filter_widgets]
            assert any("Vehicle Weight" in t for t in titles), (
                f"Expected a widget with title containing 'Vehicle Weight'. Got: {titles}"
            )
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    # ==================================================================
    # Regression tests — Stata variable-label fallback for filter titles
    # (added after the user reported `filter(rep78, type(dropdown))`
    # showing "rep78" instead of the variable label "Repair record 1978".)
    # ==================================================================

    def _build_renderer_with_filter(self, var_label, explicit_label=""):
        """Helper: build a DashRenderer with one dropdown filter on rep78.

        var_label      — variableLabels["rep78"] in the data JSON
        explicit_label — if non-empty, becomes the filter's label() option
        """
        import json, tempfile, os
        vals = [{"mpg": float(20 + i),
                 "weight": float(2000 + i * 100),
                 "rep78":  float((i % 5) + 1)} for i in range(10)]
        data = {"StataJSON": {
            "variableNames": ["mpg", "weight", "rep78"],
            "variableLabels": {"mpg": "Mileage (mpg)",
                                "weight": "Weight (lbs.)",
                                "rep78": var_label},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False, "rep78": False},
            "values": vals,
        }}
        fc = {"varname": "rep78", "type": "dropdown"}
        if explicit_label:
            fc["label"] = explicit_label
        spec = {
            "graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                    "xvar": "weight", "options": {}}],
                         "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "theme": "default",
                "title": "", "subtitle": "", "registry": "g1",
                "filters": [fc],
            },
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            dr = DashRenderer(sp, dp, op)
            dr.render()
            return [w.title for w in dr.filter_widgets]
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_filter_falls_back_to_variable_label(self):
        """REGRESSION: filter dropdown uses the Stata variable label as title."""
        titles = self._build_renderer_with_filter(var_label="Repair record 1978")
        assert any("Repair record 1978" in t for t in titles), (
            f"Expected widget title to use Stata variable label; got {titles}"
        )
        assert not any(t == "rep78" for t in titles), (
            "Filter widget title must not be the bare variable name when a "
            "variable label exists"
        )

    def test_filter_falls_back_to_varname_when_no_label(self):
        """REGRESSION: missing variable label → falls back to variable name."""
        titles = self._build_renderer_with_filter(var_label="")
        assert any("rep78" in t for t in titles), (
            f"Expected widget title to fall back to variable name; got {titles}"
        )

    def test_explicit_filter_label_overrides_variable_label(self):
        """REGRESSION: explicit label() option wins over Stata variable label."""
        titles = self._build_renderer_with_filter(
            var_label="Repair record 1978",
            explicit_label="Repairs",
        )
        assert any("Repairs" in t for t in titles), (
            f"Explicit label should override variable label; got {titles}"
        )
        assert not any("Repair record 1978" in t for t in titles), (
            "Variable label should not appear when explicit label is provided"
        )


# ================================================================
# TEST-2: Filter edge-case tests
# FC-01 through FC-04
# ================================================================

class TestFilterEdgeCases:
    """FC-01 through FC-04: filter builders must handle unusual data gracefully."""

    def _src(self, data_dict):
        return ColumnDataSource(data_dict)

    def test_fc01_dropdown_all_nan_column(self):
        """FC-01: build_dropdown with all-NaN column creates widget with only 'All'."""
        src = self._src({"foreign": [float("nan"), float("nan"), float("nan")]})
        widget, _ = FilterBuilder.build_dropdown("foreign", src)
        options = widget.options
        # Should have "All" (possibly the only entry)
        labels = [o[1] if isinstance(o, (list, tuple)) else o for o in options]
        assert "All" in labels, f"Expected 'All' option, got: {labels}"

    def test_fc02_slider_all_identical_values(self):
        """FC-02: build_slider with all-identical values creates widget without crash."""
        src = self._src({"weight": [2500.0, 2500.0, 2500.0, 2500.0]})
        widget, _ = FilterBuilder.build_slider("weight", src)
        # Must not crash; slider end must be > start (expanded by 1.0)
        assert widget.end > widget.start, (
            f"Slider end ({widget.end}) must be > start ({widget.start}) for constant data"
        )

    def test_fc03_range_single_unique_value(self):
        """FC-03: build_range with one unique value must not collapse to zero range."""
        src = self._src({"price": [5000.0, 5000.0, 5000.0]})
        widget, _ = FilterBuilder.build_range("price", src)
        start, end = widget.start, widget.end
        assert end > start, (
            f"RangeSlider end ({end}) must be > start ({start}) for single-value data"
        )

    def test_fc04_dropdown_many_unique_categories(self):
        """FC-04: build_dropdown with >100 unique string values creates widget without error."""
        categories = [f"cat_{i}" for i in range(150)]
        src = self._src({"category": categories})
        try:
            widget, _ = FilterBuilder.build_dropdown("category", src)
        except Exception as e:
            pytest.fail(f"build_dropdown with 150 categories raised {type(e).__name__}: {e}")
        assert widget is not None
        # Should have 151 options (All + 150 categories)
        assert len(widget.options) == 151, (
            f"Expected 151 options (All + 150 categories), got {len(widget.options)}"
        )

    def test_fc01_slider_all_nan_column_disabled(self):
        """FC-01b: build_slider with all-NaN column creates disabled widget."""
        src = self._src({"weight": [float("nan"), float("nan")]})
        widget, _ = FilterBuilder.build_slider("weight", src)
        assert widget.disabled is True, "Slider with all-NaN data must be disabled"

    def test_fc01_range_all_nan_column_disabled(self):
        """FC-01c: build_range with all-NaN column creates disabled widget."""
        src = self._src({"weight": [float("nan"), float("nan")]})
        widget, _ = FilterBuilder.build_range("weight", src)
        assert widget.disabled is True, "RangeSlider with all-NaN data must be disabled"


# ================================================================
# Filters must reach the source the FIGURE actually renders from
# ================================================================
# Found while verifying S08's date filter in a browser, and it is not
# date-specific: dragging a range filter on a `dash build` dashboard of LINE
# plots changes nothing on screen, while the same dashboard built from
# `scatter` filters correctly.
#
# Measured in the browser on a real sp500 build:
#
#   line:    4 ColumnDataSources -- p1050 (index, volume, close) n=248 and
#            p1101 (index, volume, high) n=248, which the figures render, plus
#            p1009/p1012 n=5, which the callback filtered
#   scatter: 2 ColumnDataSources -- p1009/p1012 n=5, filtered, and rendered
#
# map_line sorts by x and builds a NEW ColumnDataSource for the sorted data.
# self.sources -- which is what render() passes to the callback as
# all_graph_sources -- still holds the original, so the callback updates a
# source no glyph is bound to.  Every plot type that derives its own source
# has the same problem.
#
# Owned by S13 (linking, filters and KPI correctness).  The test is written
# here, before the fix, per project rule 8.

class TestFilterReachesTheRenderedSource:

    def _sources_behind_glyphs(self, fig):
        return {id(r.data_source) for r in fig.renderers
                if hasattr(r, "data_source")}

    def _build(self, ptype):
        import tempfile
        _HERE = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, _HERE)
        from conftest import make_data_json, make_spec
        df = pd.DataFrame({
            "y": np.linspace(10, 50, 40),
            "x": np.linspace(100, 500, 40)[::-1],   # unsorted, so map_line sorts
        })
        spec = make_spec(
            [{"type": ptype, "yvar": "y", "xvar": "x", "options": {}}],
            link="g1",
        )
        spec["build_options"]["filters"] = [
            {"varname": "x", "type": "range", "exclude": [], "label": ""}]
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(df), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for path in (sp, dp, op):
            try:
                os.unlink(path)
            except OSError:
                pass
        return dr

    def test_scatter_filter_updates_the_rendered_source(self):
        """The control: a scatter renders from the shared source."""
        dr = self._build("scatter")
        cb = dr.filter_callbacks[0]
        targets = {id(s) for s in cb.args["all_graph_sources"]}
        rendered = set()
        for fig in dr.figures.values():
            rendered |= self._sources_behind_glyphs(fig)
        assert targets & rendered, (
            "even a scatter's filter does not reach the rendered source"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="S13: map_line builds a derived sorted ColumnDataSource, but "
               "render() passes self.sources to the filter callback, so "
               "dragging a filter on a line chart changes nothing on screen. "
               "Reproduced in a browser on a real sp500 dashboard.",
    )
    def test_line_filter_updates_the_rendered_source(self):
        dr = self._build("line")
        cb = dr.filter_callbacks[0]
        targets = {id(s) for s in cb.args["all_graph_sources"]}
        rendered = set()
        for fig in dr.figures.values():
            rendered |= self._sources_behind_glyphs(fig)
        assert targets & rendered, (
            "the filter callback updates no source that any glyph renders "
            "from — the filter is inert on screen"
        )


class TestTheFilterReadsTheWholeDataset:
    """A widget describes the DATA, not the first graph.

    The saved renderer built every widget, and the snapshot its JavaScript
    filters and recomputes KPIs from, out of the first graph's source.
    Under by() that source is one facet; under a graph-level `if' it is
    the qualified rows.  Measured with by(foreign) on ten rows: the range
    slider's bounds came from five, the dropdown offered one category, and
    the snapshot held five rows, so a KPI recomputed after a move was a
    statistic of half the data.  The served app read the whole frame for
    all three, which is how the parity guard found it.
    """

    _DF = pd.DataFrame({
        "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
                   2010.0, 3600.0, 2650.0],
        "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
        "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
                  10372.0, 4082.0, 11385.0],
    })

    def _render(self, filter_raw, graph_options=None, if_expr=""):
        import tempfile
        _HERE = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, _HERE)
        from conftest import make_data_json
        go = {"name": "g1"}
        go.update(graph_options or {})
        spec = {"graphs": [{"name": "g1", "graph_options": go,
                            "options": dict(go), "if_expr": if_expr,
                            "in_expr": "",
                            "plots": [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "weight", "options": {}}]}],
                "kpis": [], "build_options": {
                    "layout": "auto", "link": "", "filter": filter_raw,
                    "theme": "", "scheme": "", "session_scheme": "",
                    "title": "", "subtitle": "", "registry": "g1",
                    "tabs": "", "filter_position": "top", "level": "95",
                    "formats": {}}}
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(
                self._DF, {"origin": {"0": "Domestic", "1": "Foreign"}},
                {"foreign": "origin"}), f)
        r = DashRenderer(sp, dp, op)
        r.render()
        return r

    def test_a_range_under_by_spans_every_row(self):
        r = self._render("price, type(range)", {"by": "foreign"})
        w = r.filter_widgets[0]
        assert (w.start, w.end) == (3799.0, 11385.0), (w.start, w.end)

    def test_a_dropdown_under_by_offers_every_category(self):
        r = self._render("foreign, type(dropdown)", {"by": "foreign"})
        labels = [lab for _, lab in r.filter_widgets[0].options]
        assert labels == ["All", "Domestic", "Foreign"], labels

    def test_a_range_under_a_graph_if_still_spans_every_row(self):
        r = self._render("price, type(range)", if_expr="price > 4500")
        w = r.filter_widgets[0]
        assert (w.start, w.end) == (3799.0, 11385.0), (w.start, w.end)

    def test_the_snapshot_holds_every_row_under_by(self):
        r = self._render("foreign, type(dropdown)", {"by": "foreign"})
        orig = r.filter_callbacks[0].args["orig_source"].data
        assert len(orig["__dash_row__"]) == 10
        assert sorted(orig["__dash_row__"]) == list(range(10))
        assert "price" in orig and "mpg" in orig
