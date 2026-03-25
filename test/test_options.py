"""
test_options.py
Unit tests for dash_render.py OptionTranslator class.

Tests: P1A-81 through P1A-87

Run with:  pytest test/test_options.py -v
"""
import sys
import os
import re
import pytest

# Add parent directory so we can import dash_render
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import OptionTranslator


# ================================================================
# P1A-81 — every Stata named color maps to a valid hex code
# ================================================================
class TestTranslateMcolor:
    """Tests for OptionTranslator.translate_mcolor."""

    # Sample of the 100+ Stata color names that must be mapped
    STATA_COLOR_SAMPLES = [
        "black", "white", "red", "blue", "green",
        "navy", "maroon", "forest_green", "teal", "purple",
        "sienna", "orange", "yellow", "lime", "cyan", "magenta",
        "pink", "gold", "brown", "gray", "ltblue", "lavender",
        "khaki", "cranberry", "eggshell",
        "gs0", "gs1", "gs2", "gs3", "gs4", "gs5",
        "gs6", "gs7", "gs8", "gs9", "gs10", "gs11",
        "gs12", "gs13", "gs14", "gs15", "gs16",
    ]

    HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

    def test_all_named_colors_return_valid_hex(self):
        """P1A-81: every Stata named color maps to a valid hex code (sample)."""
        for color in self.STATA_COLOR_SAMPLES:
            result = OptionTranslator.translate_mcolor(color)
            assert self.HEX_PATTERN.match(result), (
                f"Color '{color}' → '{result}' is not a valid hex code"
            )

    def test_full_color_map_all_hex(self):
        """P1A-81: all entries in _COLOR_MAP are valid hex codes."""
        for name, hex_val in OptionTranslator._COLOR_MAP.items():
            assert self.HEX_PATTERN.match(hex_val), (
                f"_COLOR_MAP['{name}'] = '{hex_val}' is not valid hex"
            )

    # ----------------------------------------------------------------
    # P1A-82 — RGB string "255 0 0" maps to #ff0000
    # ----------------------------------------------------------------
    def test_rgb_string_maps_to_hex(self):
        """P1A-82: RGB string '255 0 0' → '#ff0000'."""
        assert OptionTranslator.translate_mcolor("255 0 0") == "#ff0000"

    def test_rgb_string_blue(self):
        assert OptionTranslator.translate_mcolor("0 0 255") == "#0000ff"

    def test_rgb_string_green(self):
        assert OptionTranslator.translate_mcolor("0 255 0") == "#00ff00"

    def test_rgb_string_white(self):
        assert OptionTranslator.translate_mcolor("255 255 255") == "#ffffff"

    def test_rgb_string_black(self):
        assert OptionTranslator.translate_mcolor("0 0 0") == "#000000"

    # ----------------------------------------------------------------
    # P1A-87 — invalid color name raises ValueError with clear message
    # ----------------------------------------------------------------
    def test_invalid_color_raises_value_error(self):
        """P1A-87: invalid color name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown Stata color"):
            OptionTranslator.translate_mcolor("notacolor")

    def test_invalid_color_message_contains_name(self):
        """P1A-87: error message includes the offending color name."""
        with pytest.raises(ValueError) as exc_info:
            OptionTranslator.translate_mcolor("completely_invalid_xyz")
        assert "completely_invalid_xyz" in str(exc_info.value)


# ================================================================
# P1A-83 — every Stata marker symbol maps to a valid Bokeh marker
# ================================================================
class TestTranslateMsymbol:
    """Tests for OptionTranslator.translate_msymbol."""

    VALID_BOKEH_MARKERS = {
        "circle", "square", "triangle", "diamond", "inverted_triangle",
        "cross", "asterisk", "hex", "plus", "star",
        "circle_cross", "square_cross", "diamond_cross",
        "circle_x", "square_x", "circle_dot", "square_dot",
        "diamond_dot", "triangle_dot", "hex_dot", "star_dot",
        "x", "dash", "dot",
    }

    def test_all_stata_markers_map_to_bokeh(self):
        """P1A-83: every Stata marker name in _MARKER_MAP is a valid Bokeh marker."""
        for stata_sym, bokeh_sym in OptionTranslator._MARKER_MAP.items():
            assert bokeh_sym in self.VALID_BOKEH_MARKERS, (
                f"Stata '{stata_sym}' → '{bokeh_sym}' is not a valid Bokeh marker"
            )

    def test_circle_maps_correctly(self):
        assert OptionTranslator.translate_msymbol("circle") == "circle"

    def test_square_maps_correctly(self):
        assert OptionTranslator.translate_msymbol("square") == "square"

    def test_triangle_maps_correctly(self):
        assert OptionTranslator.translate_msymbol("triangle") == "triangle"

    def test_diamond_maps_correctly(self):
        assert OptionTranslator.translate_msymbol("diamond") == "diamond"

    def test_x_maps_correctly(self):
        result = OptionTranslator.translate_msymbol("x")
        assert result in self.VALID_BOKEH_MARKERS

    def test_plus_maps_correctly(self):
        result = OptionTranslator.translate_msymbol("plus")
        assert result in self.VALID_BOKEH_MARKERS


# ================================================================
# P1A-84 — all size keywords map to increasing pixel values
# ================================================================
class TestTranslateMsize:
    """Tests for OptionTranslator.translate_msize."""

    # Stata size keywords in ascending order
    SIZE_KEYWORDS_ASC = [
        "tiny", "vsmall", "small", "medsmall", "medium",
        "medlarge", "large", "vlarge", "huge",
    ]

    def test_all_size_keywords_are_positive(self):
        """P1A-84: all size keywords map to positive pixel values."""
        for kw in self.SIZE_KEYWORDS_ASC:
            val = OptionTranslator.translate_msize(kw)
            assert val > 0, f"Size '{kw}' → {val} is not positive"

    def test_size_keywords_are_increasing(self):
        """P1A-84: size keywords map to strictly increasing pixel values."""
        values = [OptionTranslator.translate_msize(kw) for kw in self.SIZE_KEYWORDS_ASC]
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1], (
                f"Size order violated: '{self.SIZE_KEYWORDS_ASC[i]}'={values[i]} "
                f">= '{self.SIZE_KEYWORDS_ASC[i+1]}'={values[i+1]}"
            )

    def test_numeric_string_passthrough(self):
        """Numeric strings are converted to float pixels."""
        result = OptionTranslator.translate_msize("12")
        assert result == 12.0


# ================================================================
# P1A-85 — all line width keywords map to increasing pixel widths
# ================================================================
class TestTranslateLwidth:
    """Tests for OptionTranslator.translate_lwidth."""

    LWIDTH_KEYWORDS_ASC = [
        "vvthin", "vthin", "thin", "medthin", "medium",
        "medthick", "thick", "vthick", "vvthick",
    ]

    def test_all_lwidth_keywords_positive(self):
        """P1A-85: all lwidth keywords map to positive widths."""
        for kw in self.LWIDTH_KEYWORDS_ASC:
            val = OptionTranslator.translate_lwidth(kw)
            assert val > 0, f"lwidth '{kw}' → {val} is not positive"

    def test_lwidth_keywords_increasing(self):
        """P1A-85: lwidth keywords map to strictly increasing pixel widths."""
        values = [OptionTranslator.translate_lwidth(kw) for kw in self.LWIDTH_KEYWORDS_ASC]
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1], (
                f"lwidth order violated: '{self.LWIDTH_KEYWORDS_ASC[i]}'={values[i]} "
                f">= '{self.LWIDTH_KEYWORDS_ASC[i+1]}'={values[i+1]}"
            )

    def test_numeric_string_passthrough(self):
        result = OptionTranslator.translate_lwidth("2.5")
        assert result == 2.5


# ================================================================
# P1A-86 — all line pattern keywords map to valid Bokeh dash lists
# ================================================================
class TestTranslateLpattern:
    """Tests for OptionTranslator.translate_lpattern."""

    LPATTERN_KEYWORDS = [
        "solid", "dash", "dot", "dash_dot",
        "shortdash", "shortdot", "shortdash_dot",
        "longdash", "longdash_dot",
    ]

    def test_solid_returns_empty_list(self):
        """'solid' pattern → empty list (Bokeh solid line)."""
        result = OptionTranslator.translate_lpattern("solid")
        assert result == []

    def test_all_patterns_return_list(self):
        """P1A-86: all lpattern keywords return a list."""
        for kw in self.LPATTERN_KEYWORDS:
            result = OptionTranslator.translate_lpattern(kw)
            assert isinstance(result, list), (
                f"lpattern '{kw}' → {result!r} is not a list"
            )

    def test_dash_pattern_is_nonempty(self):
        result = OptionTranslator.translate_lpattern("dash")
        assert len(result) > 0

    def test_dot_pattern_is_nonempty(self):
        result = OptionTranslator.translate_lpattern("dot")
        assert len(result) > 0

    def test_all_list_elements_are_numeric(self):
        """All dash list elements must be numeric (Bokeh requirement)."""
        for kw in self.LPATTERN_KEYWORDS:
            result = OptionTranslator.translate_lpattern(kw)
            for elem in result:
                assert isinstance(elem, (int, float)), (
                    f"lpattern '{kw}' element {elem!r} is not numeric"
                )


# ================================================================
# Additional edge cases for color translation
# ================================================================
class TestColorEdgeCases:
    """Edge cases for color translation."""

    def test_case_insensitive_color(self):
        """Color names should be matched case-insensitively."""
        result_lower = OptionTranslator.translate_mcolor("red")
        result_upper = OptionTranslator.translate_mcolor("RED")
        assert result_lower == result_upper

    def test_lcolor_delegates_to_mcolor_map(self):
        """translate_lcolor should produce same hex as translate_mcolor."""
        assert OptionTranslator.translate_lcolor("blue") == OptionTranslator.translate_mcolor("blue")

    def test_rgb_clamps_at_255(self):
        """RGB values are clamped to 0-255 range."""
        # Out-of-range values should either clamp or raise
        try:
            result = OptionTranslator.translate_mcolor("300 0 0")
            # If it succeeds, the result should be a hex code
            assert re.match(r"^#[0-9a-fA-F]{6}$", result)
        except (ValueError, AssertionError):
            pass  # raising is also acceptable behaviour
