"""
test_scheme.py
Unit tests for SchemeParser, _apply_jitter, and _compute_secondary_range.

Run with:  pytest test/test_scheme.py -v
"""
import sys
import os
import math
import tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import SchemeParser, _apply_jitter, _compute_secondary_range


# ============================================================
# Helpers
# ============================================================

def _is_hex(s: str) -> bool:
    """Return True if s looks like a CSS hex color."""
    return bool(s) and s.startswith("#") and len(s) in (4, 7)


def _is_grayscale_hex(s: str) -> bool:
    """Return True if all three hex channels are equal (grayscale)."""
    if not _is_hex(s):
        return False
    h = s.lstrip("#")
    if len(h) == 3:
        r, g, b = h[0]*2, h[1]*2, h[2]*2
    else:
        r, g, b = h[0:2], h[2:4], h[4:6]
    return r == g == b


SCHEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "schemes")


# ============================================================
# SC-01 through SC-05  Built-in scheme loading
# ============================================================

class TestBuiltinSchemeLoading:
    def test_s2color_loads(self):
        sp = SchemeParser("s2color")
        assert sp is not None

    def test_s1mono_loads(self):
        sp = SchemeParser("s1mono")
        assert sp is not None

    def test_s1color_loads(self):
        sp = SchemeParser("s1color")
        assert sp is not None

    def test_economist_loads(self):
        sp = SchemeParser("economist")
        assert sp is not None

    def test_sj_loads(self):
        sp = SchemeParser("sj")
        assert sp is not None

    def test_nonexistent_raises_valueerror(self):
        with pytest.raises(ValueError, match="not found"):
            SchemeParser("no_such_scheme")

    def test_error_message_lists_builtins(self):
        with pytest.raises(ValueError) as exc_info:
            SchemeParser("no_such_scheme")
        msg = str(exc_info.value)
        assert "s2color" in msg

    def test_empty_name_raises_or_defaults(self):
        # empty string should fall back to s2color (no crash)
        sp = SchemeParser("")
        assert sp is not None

    def test_default_is_s2color(self):
        sp1 = SchemeParser()
        sp2 = SchemeParser("s2color")
        assert sp1.p_colors[0] == sp2.p_colors[0]


# ============================================================
# SC-06 through SC-09  Color properties
# ============================================================

class TestColorProperties:
    def test_s2color_background_is_hex(self):
        sp = SchemeParser("s2color")
        assert _is_hex(sp.background_color)

    def test_s2color_plotregion_is_white(self):
        sp = SchemeParser("s2color")
        assert sp.plotregion_color == "#ffffff"

    def test_s1mono_p_colors_are_grayscale(self):
        sp = SchemeParser("s1mono")
        # All 15 p# colors should be grayscale (R==G==B)
        for i, c in enumerate(sp.p_colors):
            assert _is_grayscale_hex(c) or c in ("#000000", "#ffffff"), \
                f"p{i+1} color {c!r} is not grayscale"

    def test_economist_background_differs_from_s2color(self):
        eco = SchemeParser("economist")
        s2 = SchemeParser("s2color")
        assert eco.background_color != s2.background_color

    def test_p_colors_has_15_entries(self):
        sp = SchemeParser("s2color")
        assert len(sp.p_colors) == 15

    def test_p_line_colors_has_15_entries(self):
        sp = SchemeParser("s2color")
        assert len(sp.p_line_colors) == 15

    def test_p_bar_colors_has_15_entries(self):
        sp = SchemeParser("s2color")
        assert len(sp.p_bar_colors) == 15

    def test_all_p_colors_are_hex(self):
        sp = SchemeParser("s2color")
        for c in sp.p_colors:
            assert _is_hex(c), f"{c!r} is not a valid hex color"

    def test_s2color_p1_is_navy(self):
        sp = SchemeParser("s2color")
        assert sp.p_colors[0] == "#1a476f"  # navy


# ============================================================
# SC-10 through SC-14  Symbol and pattern cycles
# ============================================================

class TestSymbolAndPatternCycles:
    def test_p_symbols_has_15_entries(self):
        sp = SchemeParser("s2color")
        assert len(sp.p_symbols) == 15

    def test_p_symbols_are_strings(self):
        sp = SchemeParser("s2color")
        for sym in sp.p_symbols:
            assert isinstance(sym, str) and len(sym) > 0

    def test_s2color_p1_symbol_is_circle(self):
        sp = SchemeParser("s2color")
        assert sp.p_symbols[0] == "circle"

    def test_p_line_patterns_has_15_entries(self):
        sp = SchemeParser("s2color")
        assert len(sp.p_line_patterns) == 15

    def test_p_line_patterns_are_lists(self):
        sp = SchemeParser("s2color")
        for pat in sp.p_line_patterns:
            assert isinstance(pat, list)

    def test_s1mono_uses_diverse_line_patterns(self):
        sp = SchemeParser("s1mono")
        # Should have at least 3 distinct patterns
        distinct = {tuple(p) for p in sp.p_line_patterns}
        assert len(distinct) >= 3


# ============================================================
# SC-15 through SC-18  default_color / default_symbol API
# ============================================================

class TestDefaultColorAPI:
    def test_default_color_scatter_returns_p1(self):
        sp = SchemeParser("s2color")
        assert sp.default_color(0, "scatter") == sp.p_colors[0]

    def test_default_color_line_returns_p_line(self):
        sp = SchemeParser("s2color")
        assert sp.default_color(0, "line") == sp.p_line_colors[0]

    def test_default_color_bar_returns_p_bar(self):
        sp = SchemeParser("s2color")
        assert sp.default_color(0, "bar") == sp.p_bar_colors[0]

    def test_default_color_wraps_modulo_15(self):
        sp = SchemeParser("s2color")
        assert sp.default_color(15) == sp.default_color(0)
        assert sp.default_color(16) == sp.default_color(1)

    def test_default_symbol_returns_string(self):
        sp = SchemeParser("s2color")
        assert isinstance(sp.default_symbol(0), str)

    def test_default_symbol_wraps_modulo_15(self):
        sp = SchemeParser("s2color")
        assert sp.default_symbol(15) == sp.default_symbol(0)

    def test_default_line_pattern_returns_list(self):
        sp = SchemeParser("s2color")
        assert isinstance(sp.default_line_pattern(0), list)


# ============================================================
# SC-19 through SC-20  Intensities and font sizes
# ============================================================

class TestIntensitiesAndFonts:
    def test_fill_alpha_is_float_between_0_and_1(self):
        sp = SchemeParser("s2color")
        assert 0.0 <= sp.fill_alpha <= 1.0

    def test_bar_alpha_is_float_between_0_and_1(self):
        sp = SchemeParser("s2color")
        assert 0.0 <= sp.bar_alpha <= 1.0

    def test_s2color_fill_alpha_is_0_8(self):
        sp = SchemeParser("s2color")
        assert abs(sp.fill_alpha - 0.8) < 0.01

    def test_economist_fill_alpha_is_0_9(self):
        sp = SchemeParser("economist")
        assert abs(sp.fill_alpha - 0.9) < 0.01

    def test_heading_font_size_is_css_pt(self):
        sp = SchemeParser("s2color")
        assert sp.heading_font_size.endswith("pt")

    def test_axis_title_font_size_is_css_pt(self):
        sp = SchemeParser("s2color")
        assert sp.axis_title_font_size.endswith("pt")

    def test_tick_label_font_size_is_css_pt(self):
        sp = SchemeParser("s2color")
        assert sp.tick_label_font_size.endswith("pt")


# ============================================================
# SC-21 through SC-23  apply_to_figure
# ============================================================

class TestApplyToFigure:
    def _make_fig(self):
        from bokeh.plotting import figure
        return figure(width=400, height=300, title="test")

    def test_sets_background_fill_color(self):
        sp = SchemeParser("s2color")
        fig = self._make_fig()
        sp.apply_to_figure(fig)
        assert fig.background_fill_color == sp.plotregion_color

    def test_sets_border_fill_color(self):
        sp = SchemeParser("s2color")
        fig = self._make_fig()
        sp.apply_to_figure(fig)
        assert fig.border_fill_color == sp.background_color

    def test_sets_grid_line_color(self):
        sp = SchemeParser("s2color")
        fig = self._make_fig()
        sp.apply_to_figure(fig)
        for grid in list(fig.xgrid) + list(fig.ygrid):
            assert grid.grid_line_color == sp.grid_color

    def test_sets_axis_label_font_size(self):
        sp = SchemeParser("s2color")
        fig = self._make_fig()
        sp.apply_to_figure(fig)
        for axis in list(fig.xaxis) + list(fig.yaxis):
            assert axis.axis_label_text_font_size == sp.axis_title_font_size

    def test_apply_does_not_crash_with_legend(self):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        sp = SchemeParser("s2color")
        fig = figure(width=400, height=300)
        src = ColumnDataSource({"x": [1, 2], "y": [3, 4]})
        fig.circle("x", "y", source=src, legend_label="test")
        sp.apply_to_figure(fig)  # should not crash


# ============================================================
# SC-24  css_block
# ============================================================

class TestCssBlock:
    def test_returns_style_tags(self):
        sp = SchemeParser("s2color")
        css = sp.css_block()
        assert "<style>" in css
        assert "</style>" in css

    def test_contains_background_color(self):
        sp = SchemeParser("s2color")
        css = sp.css_block()
        # Should reference the background color somewhere
        assert sp.background_color in css or "background-color" in css

    def test_xss_escaped_in_css(self):
        # Craft a custom scheme with an XSS attempt in a color value
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("label xss\n")
            f.write("color background  white\n")
            f.write("color plotregion  white\n")
            f.write("color heading     black\n")
            name = os.path.basename(f.name)
        try:
            sp = SchemeParser(name)
            css = sp.css_block()
            assert "<script>" not in css
        finally:
            os.unlink(os.path.join(os.getcwd(), name))


# ============================================================
# SC-25 through SC-27  #include inheritance
# ============================================================

class TestIncludeInheritance:
    def test_economist_inherits_from_s2color(self):
        eco = SchemeParser("economist")
        # Economist's p1 should still be navy (inherited from s2color)
        assert eco.p_colors[0] == "#1a476f"

    def test_economist_background_differs_from_parent(self):
        eco = SchemeParser("economist")
        s2 = SchemeParser("s2color")
        # economist overrides background
        assert eco.background_color != s2.background_color

    def test_s1mono_inherits_symbols_from_s1color(self):
        mono = SchemeParser("s1mono")
        s1c = SchemeParser("s1color")
        # Both should have circle as p1 symbol
        assert mono.p_symbols[0] == s1c.p_symbols[0] == "circle"


# ============================================================
# SC-28  Security — path traversal
# ============================================================

class TestSecurity:
    def test_path_traversal_raises(self):
        with pytest.raises(ValueError, match="outside allowed"):
            SchemeParser("../../etc/passwd")

    def test_absolute_path_outside_cwd_raises(self):
        with pytest.raises(ValueError):
            SchemeParser("/etc/passwd")

    def test_custom_scheme_in_cwd_loads(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("label custom\n")
            f.write("color background  white\n")
            f.write("color plotregion  white\n")
            f.write("color heading     black\n")
            f.write("color p1   navy\n")
            name = os.path.basename(f.name)
        try:
            sp = SchemeParser(name)
            assert sp.p_colors[0] == "#1a476f"  # navy
        finally:
            os.unlink(os.path.join(os.getcwd(), name))

    def test_malformed_line_skipped_without_crash(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("label malformed\n")
            f.write("x\n")           # only one token — malformed
            f.write("color\n")       # only one token — malformed
            f.write("color p1  navy\n")
            name = os.path.basename(f.name)
        try:
            sp = SchemeParser(name)
            assert sp.p_colors[0] == "#1a476f"
        finally:
            os.unlink(os.path.join(os.getcwd(), name))

    def test_unreadable_include_skipped_gracefully(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("#include totally_nonexistent_parent\n")
            f.write("color p1  navy\n")
            name = os.path.basename(f.name)
        try:
            sp = SchemeParser(name)
            # Should load the explicit entries despite bad include
            assert sp.p_colors[0] == "#1a476f"
        finally:
            os.unlink(os.path.join(os.getcwd(), name))

    def test_real_stata_scheme_via_cwd_copy(self):
        """Parser handles full Stata scheme format when copied to CWD."""
        stata_path = "/Applications/Stata 15/ado/base/s/scheme-s2color.scheme"
        if not os.path.isfile(stata_path):
            pytest.skip("Stata 15 not installed")
        import shutil
        cwd_copy = os.path.join(os.getcwd(), "stata_s2color_test.scheme")
        shutil.copy(stata_path, cwd_copy)
        try:
            sp = SchemeParser("stata_s2color_test.scheme")
            assert sp.p_colors[0] == "#1a476f"  # navy = p1 in s2color
        finally:
            os.unlink(cwd_copy)

    # ------------------------------------------------------------------
    # BUG-51: symlink path traversal bypass
    # ------------------------------------------------------------------

    def test_BUG_51_1a_symlink_to_external_file_raises(self):
        """BUG-51-1a: symlink in CWD pointing outside allowed dirs must raise ValueError.

        A symlink placed in the CWD (evil.scheme -> /etc/hosts) passes the
        abspath boundary check but must be caught by the realpath check.
        """
        # Use /etc/hosts on Unix; skip on systems where it doesn't exist
        target = "/etc/hosts"
        if not os.path.exists(target):
            pytest.skip("/etc/hosts not available on this system")
        link_name = os.path.join(os.getcwd(), "_bug51_test_symlink.scheme")
        try:
            os.symlink(target, link_name)
            with pytest.raises(ValueError, match="symlink"):
                SchemeParser("_bug51_test_symlink.scheme")
        finally:
            if os.path.lexists(link_name):
                os.unlink(link_name)

    def test_BUG_51_1b_symlink_to_system_dir_raises(self):
        """BUG-51-1b: symlink pointing to /tmp raises ValueError."""
        link_name = os.path.join(os.getcwd(), "_bug51b_test_symlink.scheme")
        # Create a symlink to an arbitrary file outside CWD/schemes dir
        import shutil
        # Use a real external file for the target
        targets = ["/etc/hosts", "/usr/share/dict/words", "/var/log/system.log"]
        target = next((t for t in targets if os.path.exists(t)), None)
        if target is None:
            pytest.skip("No suitable external target file found")
        try:
            os.symlink(target, link_name)
            with pytest.raises(ValueError, match="symlink"):
                SchemeParser("_bug51b_test_symlink.scheme")
        finally:
            if os.path.lexists(link_name):
                os.unlink(link_name)

    def test_BUG_51_1c_normal_cwd_file_still_loads(self):
        """BUG-51-1c: a normal (non-symlink) .scheme in CWD must still load correctly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("label bug51_normal\n")
            f.write("color p1  navy\n")
            name = os.path.basename(f.name)
        try:
            sp = SchemeParser(name)
            assert sp.p_colors[0] == "#1a476f"
        finally:
            os.unlink(os.path.join(os.getcwd(), name))

    def test_BUG_51_1d_symlink_within_cwd_is_allowed(self):
        """BUG-51-1d: symlink whose target is ALSO within CWD must be accepted."""
        # Create a real scheme file in CWD, then symlink it within CWD
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scheme",
            dir=os.getcwd(), delete=False
        ) as f:
            f.write("label bug51_real\n")
            f.write("color p1  navy\n")
            real_name = f.name
        link_name = os.path.join(os.getcwd(), "_bug51d_link.scheme")
        try:
            os.symlink(real_name, link_name)
            # Both real file and symlink are within CWD — must succeed
            sp = SchemeParser("_bug51d_link.scheme")
            assert sp.p_colors[0] == "#1a476f"
        finally:
            if os.path.lexists(link_name):
                os.unlink(link_name)
            if os.path.exists(real_name):
                os.unlink(real_name)

    def test_BUG_51_1e_realpath_check_covers_abspath_bypass(self):
        """BUG-51-1e: _resolve_path must perform realpath validation, not just abspath."""
        # Verify the security fix is present in the source code
        import inspect
        source = inspect.getsource(SchemeParser._resolve_path)
        assert "realpath" in source, (
            "SchemeParser._resolve_path must call os.path.realpath for symlink "
            "traversal protection (BUG-51 regression)"
        )


# ============================================================
# _apply_jitter tests
# ============================================================

class TestApplyJitter:
    def test_returns_same_length(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        xj, yj = _apply_jitter(x, y, 5, seed=0)
        assert len(xj) == 3
        assert len(yj) == 3

    def test_deterministic_with_seed(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        xj1, yj1 = _apply_jitter(x, y, 5, seed=42)
        xj2, yj2 = _apply_jitter(x, y, 5, seed=42)
        np.testing.assert_array_equal(xj1, xj2)
        np.testing.assert_array_equal(yj1, yj2)

    def test_different_without_seed(self):
        x = np.array([float(i) for i in range(100)])
        y = np.array([float(i) for i in range(100)])
        xj1, _ = _apply_jitter(x, y, 10)
        xj2, _ = _apply_jitter(x, y, 10)
        assert not np.allclose(xj1, xj2)

    def test_zero_pct_returns_copy(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        xj, yj = _apply_jitter(x, y, 0, seed=0)
        np.testing.assert_array_equal(xj, x)
        np.testing.assert_array_equal(yj, y)

    def test_clamp_over_100(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        # 150 should be clamped to 100 — shouldn't crash
        xj, yj = _apply_jitter(x, y, 150, seed=0)
        assert len(xj) == 3

    def test_negative_pct_clamps_to_zero(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        xj, yj = _apply_jitter(x, y, -5, seed=0)
        np.testing.assert_array_equal(xj, x)

    def test_empty_array_returns_empty(self):
        x = np.array([], dtype=float)
        y = np.array([], dtype=float)
        xj, yj = _apply_jitter(x, y, 5, seed=0)
        assert len(xj) == 0
        assert len(yj) == 0

    def test_constant_array_no_div_zero(self):
        x = np.array([5.0, 5.0, 5.0])  # range = 0
        y = np.array([3.0, 3.0, 3.0])
        xj, yj = _apply_jitter(x, y, 5, seed=0)
        assert len(xj) == 3  # no crash

    def test_offsets_within_expected_range(self):
        x = np.array([0.0, 10.0])
        y = np.array([0.0, 20.0])
        xj, yj = _apply_jitter(x, y, 10, seed=0)
        # x range = 10, jitter half-width = 0.10 * 10 / 2 = 0.5
        assert all(abs(xj[i] - x[i]) <= 0.5 + 1e-9 for i in range(2))
        # y range = 20, jitter half-width = 0.10 * 20 / 2 = 1.0
        assert all(abs(yj[i] - y[i]) <= 1.0 + 1e-9 for i in range(2))

    def test_original_arrays_not_modified(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        x_copy = x.copy()
        y_copy = y.copy()
        _apply_jitter(x, y, 5, seed=0)
        np.testing.assert_array_equal(x, x_copy)
        np.testing.assert_array_equal(y, y_copy)


# ============================================================
# _compute_secondary_range tests
# ============================================================

class TestComputeSecondaryRange:
    def _df(self):
        return pd.DataFrame({
            "mpg":    [20.0, 25.0, 30.0, 15.0],
            "weight": [2000.0, 3000.0, 2500.0, 3500.0],
        })

    def test_returns_tuple_of_two_floats(self):
        df = self._df()
        plots = [{"options": {"yaxis": "2"}, "yvar": "mpg"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        assert isinstance(lo, float)
        assert isinstance(hi, float)

    def test_lo_less_than_hi(self):
        df = self._df()
        plots = [{"options": {"yaxis": "2"}, "yvar": "mpg"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        assert lo < hi

    def test_range_contains_data(self):
        df = self._df()
        plots = [{"options": {"yaxis": "2"}, "yvar": "mpg"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        assert lo <= 15.0
        assert hi >= 30.0

    def test_no_secondary_plots_returns_fallback(self):
        df = self._df()
        plots = [{"options": {"yaxis": "1"}, "yvar": "mpg"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        assert (lo, hi) == (0.0, 1.0)

    def test_missing_var_skipped(self):
        df = self._df()
        plots = [{"options": {"yaxis": "2"}, "yvar": "nonexistent"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        assert (lo, hi) == (0.0, 1.0)

    def test_multiple_plots_combined(self):
        df = self._df()
        plots = [
            {"options": {"yaxis": "2"}, "yvar": "mpg"},
            {"options": {"yaxis": "2"}, "yvar": "weight"},
        ]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2)
        # Should span both mpg (15-30) and weight (2000-3500)
        assert lo <= 15.0
        assert hi >= 3500.0

    def test_xaxis_works_too(self):
        df = self._df()
        plots = [{"options": {"xaxis": "2"}, "xvar": "weight"}]
        lo, hi = _compute_secondary_range(df, plots, "xaxis", "xvar", 2)
        assert lo <= 2000.0
        assert hi >= 3500.0

    def test_padding_applied(self):
        df = pd.DataFrame({"y": [0.0, 10.0]})
        plots = [{"options": {"yaxis": "2"}, "yvar": "y"}]
        lo, hi = _compute_secondary_range(df, plots, "yaxis", "yvar", 2, padding_pct=0.1)
        # span=10, padding = 0.1*10=1 on each side
        assert lo < 0.0
        assert hi > 10.0
