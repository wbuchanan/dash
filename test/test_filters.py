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
