"""
dash_render.py
==============
Python rendering engine for the Stata ``dash`` command.

Consumes:
  - A master specification JSON file (produced by dash.ado / dash_parse.mata)
    describing every graph and KPI registered in the current dashboard session.
  - A data JSON file (produced by jsonio) containing the full dataset with all
    Stata metadata preserved (variable labels, value labels, type information).

Produces:
  A standalone HTML file containing an interactive Bokeh dashboard that works
  in any modern browser without a server, internet connection, or installed
  software beyond the browser itself.

Architecture
------------
DashRenderer   – Top-level orchestrator.  Loads data, builds all figures and
                 KPI cards, attaches interactivity, assembles the final layout,
                 and returns the complete HTML string.

GlyphMapper    – Translates each Stata twoway plot type into the appropriate
                 Bokeh glyph call(s).  One method per supported plot type.

OptionTranslator – Converts Stata option values (color names, marker symbols,
                   line widths, etc.) into the equivalent Bokeh property values.

FilterBuilder  – Constructs Bokeh filter widgets (Select, Slider, RangeSlider)
                 together with the CustomJS callbacks that apply BooleanFilters
                 to graph CDSViews and update KPI Div text on interaction.

Security notes
--------------
* All user-supplied strings are HTML-escaped via html.escape() before being
  embedded in Div widgets, titles, or CustomJS templates.
* CustomJS templates use parameterised construction — user values are never
  directly interpolated into JavaScript code paths.
* Output HTML includes a Content-Security-Policy meta tag restricting scripts
  to inline only, preventing loading of external scripts if the file is later
  served from a web server.

Dependencies
------------
  bokeh >= 3.0
  numpy >= 1.23
  scipy >= 1.9
  statsmodels >= 0.13
  pandas >= 1.5

Author:  (see dash.sthlp)
Version: 1.0.0  25mar2026
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Bokeh imports — grouped by sub-module for clarity
# ---------------------------------------------------------------------------
from bokeh.embed import components, file_html
from bokeh.layouts import column, gridplot, row
from bokeh.models import (
    Arrow,
    BooleanFilter,
    BoxSelectTool,
    CDSView,
    ColumnDataSource,
    CustomJS,
    DataRange1d,
    Div,
    HoverTool,
    IndexFilter,
    LassoSelectTool,
    NormalHead,
    OpenHead,
    PanTool,
    RangeSlider,
    ResetTool,
    Select,
    Slider,
    Span,
    TabPanel,
    Tabs,
    WheelZoomTool,
)
from bokeh.plotting import figure as bokeh_figure
from bokeh.resources import CDN, INLINE  # noqa: F401 — CDN kept for server mode


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Number of data points above which WebGL rendering is used for performance.
_WEBGL_THRESHOLD = 10_000

# Default nonselection alpha for linked-brushing dimming effect.
_NONSELECTION_ALPHA = 0.15

# CSP meta tag injected into every output HTML file.
# 'unsafe-eval' is required because Bokeh's CustomJS compiles callback
# code via `new Function(...)` at runtime.  Without it the browser raises
# an EvalError and no filter or interactive callback fires.
_CSP_META = (
    '<meta http-equiv="Content-Security-Policy" '
    "content=\"script-src 'unsafe-inline' 'unsafe-eval';\">"
)

# Bootstrap-compatible 12-column responsive grid CSS (db- prefix avoids
# conflicts if users have Bootstrap already loaded in their browser).
_DASH_GRID_CSS = """\
*,*::before,*::after{box-sizing:border-box}
.db-container{width:100%;padding-right:12px;padding-left:12px;margin:0 auto}
.db-row{display:flex;flex-wrap:wrap;margin-right:-8px;margin-left:-8px}
.db-row>[class*="db-col"]{padding-right:8px;padding-left:8px;min-width:0}
.db-col-1{flex:0 0 8.3333%;max-width:8.3333%}
.db-col-2{flex:0 0 16.6667%;max-width:16.6667%}
.db-col-3{flex:0 0 25%;max-width:25%}
.db-col-4{flex:0 0 33.3333%;max-width:33.3333%}
.db-col-5{flex:0 0 41.6667%;max-width:41.6667%}
.db-col-6{flex:0 0 50%;max-width:50%}
.db-col-7{flex:0 0 58.3333%;max-width:58.3333%}
.db-col-8{flex:0 0 66.6667%;max-width:66.6667%}
.db-col-9{flex:0 0 75%;max-width:75%}
.db-col-10{flex:0 0 83.3333%;max-width:83.3333%}
.db-col-11{flex:0 0 91.6667%;max-width:91.6667%}
.db-col-12{flex:0 0 100%;max-width:100%}
@media(min-width:576px){
.db-col-sm-1{flex:0 0 8.3333%;max-width:8.3333%}
.db-col-sm-2{flex:0 0 16.6667%;max-width:16.6667%}
.db-col-sm-3{flex:0 0 25%;max-width:25%}
.db-col-sm-4{flex:0 0 33.3333%;max-width:33.3333%}
.db-col-sm-5{flex:0 0 41.6667%;max-width:41.6667%}
.db-col-sm-6{flex:0 0 50%;max-width:50%}
.db-col-sm-7{flex:0 0 58.3333%;max-width:58.3333%}
.db-col-sm-8{flex:0 0 66.6667%;max-width:66.6667%}
.db-col-sm-9{flex:0 0 75%;max-width:75%}
.db-col-sm-10{flex:0 0 83.3333%;max-width:83.3333%}
.db-col-sm-11{flex:0 0 91.6667%;max-width:91.6667%}
.db-col-sm-12{flex:0 0 100%;max-width:100%}
}
@media(min-width:768px){
.db-col-md-1{flex:0 0 8.3333%;max-width:8.3333%}
.db-col-md-2{flex:0 0 16.6667%;max-width:16.6667%}
.db-col-md-3{flex:0 0 25%;max-width:25%}
.db-col-md-4{flex:0 0 33.3333%;max-width:33.3333%}
.db-col-md-5{flex:0 0 41.6667%;max-width:41.6667%}
.db-col-md-6{flex:0 0 50%;max-width:50%}
.db-col-md-7{flex:0 0 58.3333%;max-width:58.3333%}
.db-col-md-8{flex:0 0 66.6667%;max-width:66.6667%}
.db-col-md-9{flex:0 0 75%;max-width:75%}
.db-col-md-10{flex:0 0 83.3333%;max-width:83.3333%}
.db-col-md-11{flex:0 0 91.6667%;max-width:91.6667%}
.db-col-md-12{flex:0 0 100%;max-width:100%}
}
@media(min-width:992px){
.db-col-lg-1{flex:0 0 8.3333%;max-width:8.3333%}
.db-col-lg-2{flex:0 0 16.6667%;max-width:16.6667%}
.db-col-lg-3{flex:0 0 25%;max-width:25%}
.db-col-lg-4{flex:0 0 33.3333%;max-width:33.3333%}
.db-col-lg-5{flex:0 0 41.6667%;max-width:41.6667%}
.db-col-lg-6{flex:0 0 50%;max-width:50%}
.db-col-lg-7{flex:0 0 58.3333%;max-width:58.3333%}
.db-col-lg-8{flex:0 0 66.6667%;max-width:66.6667%}
.db-col-lg-9{flex:0 0 75%;max-width:75%}
.db-col-lg-10{flex:0 0 83.3333%;max-width:83.3333%}
.db-col-lg-11{flex:0 0 91.6667%;max-width:91.6667%}
.db-col-lg-12{flex:0 0 100%;max-width:100%}
}
.db-section{margin-bottom:16px}
.db-filter-bar{align-items:center;margin-bottom:12px;padding:8px 0;\
border-bottom:1px solid #dee2e6}
.db-filter-bar .bk-input-group{margin-right:16px}
.db-title{font-family:sans-serif;font-size:1.5rem;font-weight:600;\
margin-bottom:4px;margin-top:0}
.db-subtitle{font-family:sans-serif;font-size:.9rem;color:#6c757d;\
margin-top:0;margin-bottom:12px}
.db-sidebar-col{border-right:1px solid #dee2e6;padding-right:16px}
.db-sidebar-label{font-family:sans-serif;font-size:.8rem;font-weight:600;\
color:#6c757d;text-transform:uppercase;letter-spacing:.05em;\
margin-bottom:12px;margin-top:8px;padding-bottom:4px;\
border-bottom:1px solid #dee2e6}
.db-sidebar-item{margin-bottom:16px}
.db-col-auto{flex:0 0 auto;max-width:100%}
"""


# ===========================================================================
# Region option helpers — parse plotregion() / graphregion() sub-options
# ===========================================================================

def _parse_scale_opt(raw: str) -> "tuple[bool, bool]":
    """Parse an xscale()/yscale() option string for 'log' and 'reverse' sub-options.

    Args:
        raw: The raw option value string, e.g. 'log', 'reverse', 'log reverse'.

    Returns:
        (is_log, is_reverse) as booleans.
    """
    tokens = raw.lower().split()
    return ("log" in tokens), ("reverse" in tokens)


def _parse_axis_angle(raw: str) -> "float | None":
    """Extract angle sub-option from a Stata xlabel()/ylabel() option string.

    Looks for ``angle(#)`` or ``angle(name)`` within the raw axis option string.

    Named orientations:
        horizontal → 0.0 radians
        vertical   → π/2 radians (90°)

    Args:
        raw: Full xlabel()/ylabel() option value string.

    Returns:
        Angle in **radians** as float, or ``None`` if absent or unparseable.
    """
    import math as _math
    m = re.search(r'\bangle\s*\(\s*([^)]+)\s*\)', raw, re.IGNORECASE)
    if not m:
        return None
    val = m.group(1).strip().lower()
    if val == "horizontal":
        return 0.0
    if val == "vertical":
        return _math.pi / 2
    try:
        return _math.radians(float(val))
    except ValueError:
        return None


def _extract_region_color(val: str) -> str:
    """Extract color name from region option value like 'color(ltblue) lwidth(thin)'.

    Accepts color() or fcolor() sub-option.  Returns the raw color string or ''.
    """
    m = re.search(r'\bf?color\s*\(([^)]+)\)', val, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_region_lcolor(val: str) -> str:
    """Extract line-color name from region option value (lcolor() sub-option)."""
    m = re.search(r'\blcolor\s*\(([^)]+)\)', val, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_region_lwidth(val: str) -> float | None:
    """Extract line-width from region option value (lwidth() sub-option).

    Returns numeric pixels or None if absent/invalid.
    """
    m = re.search(r'\blwidth\s*\(([^)]+)\)', val, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).strip()
    try:
        return float(raw)
    except ValueError:
        return OptionTranslator.translate_lwidth(raw) if raw else None


def _extract_finite(source: "ColumnDataSource", varname: str) -> "np.ndarray":
    """Return a float array of non-None, non-NaN values from a CDS column.

    Used by filter builders and distribution mappers to get clean numeric
    arrays from a ColumnDataSource column before computing min/max/std.

    Args:
        source:  ColumnDataSource containing the data.
        varname: Column name to extract.

    Returns:
        1-D numpy float array with None and NaN values removed.
    """
    col = source.data.get(varname, [])
    arr = np.array([v for v in col if v is not None], dtype=float)
    return arr[~np.isnan(arr)]


# ===========================================================================
# OptionTranslator
# ===========================================================================

class OptionTranslator:
    """Translates Stata graph option values to Bokeh property values.

    All translation methods are static — no instance state is required.
    Methods raise ``ValueError`` with a descriptive message for invalid input,
    so that the caller can wrap them in a user-facing error.
    """

    # ------------------------------------------------------------------
    # Stata → hex color mapping
    # Covers all named colors defined in Stata's color scheme documentation.
    # ------------------------------------------------------------------
    _COLOR_MAP: dict[str, str] = {
        # Basic named colors
        "black":         "#000000",
        "white":         "#ffffff",
        "red":           "#ff0000",
        "blue":          "#0000ff",
        "green":         "#00ff00",
        "yellow":        "#ffff00",
        "orange":        "#ffa500",
        "purple":        "#800080",
        "pink":          "#ffc0cb",
        "gray":          "#808080",
        "grey":          "#808080",
        "brown":         "#a52a2a",
        "cyan":          "#00ffff",
        "magenta":       "#ff00ff",
        "lime":          "#00ff00",
        # Stata named colors
        "navy":          "#1a476f",
        "maroon":        "#90353b",
        "forest_green":  "#538d22",
        "dkorange":      "#e07f2c",
        "teal":          "#1b8a7a",
        "cranberry":     "#a00000",
        "lavender":      "#c4b8d5",
        "khaki":         "#d2c58e",
        "sienna":        "#a0522d",
        "emidblue":      "#5f6fa5",
        "emerald":       "#50a050",
        "stone":         "#bfa38a",
        "gold":          "#ffd700",
        "bluishgray":    "#8ea0b4",
        "bluishgrey":    "#8ea0b4",
        "sandb":         "#c2a47e",
        "mint":          "#98f0c0",
        "olive":         "#808000",
        "olive_teal":    "#4b8260",
        "ltblue":        "#add8e6",
        "midblue":       "#4169e1",
        "edkblue":       "#00008b",
        "ltkhaki":       "#f0e68c",
        "midgreen":      "#3a753a",
        "erose":         "#e66a6a",
        "eltblue":       "#b7c9e2",
        "eltgreen":      "#b7d8a0",
        "ebblue":        "#6794a7",
        "dkgreen":       "#006400",
        "dknavy":        "#002060",
        "dimgray":       "#696969",
        "dimgrey":       "#696969",
        "gs0":           "#000000",
        "gs1":           "#1a1a1a",
        "gs2":           "#333333",
        "gs3":           "#4d4d4d",
        "gs4":           "#666666",
        "gs5":           "#808080",
        "gs6":           "#999999",
        "gs7":           "#b3b3b3",
        "gs8":           "#cccccc",
        "gs9":           "#e6e6e6",
        "gs10":          "#f0f0f0",
        "gs11":          "#f5f5f5",
        "gs12":          "#fafafa",
        "gs13":          "#fdfdfd",
        "gs14":          "#ffffff",
        "gs15":          "#ffffff",
        "gs16":          "#ffffff",
        "eggshell":      "#f0ead2",
        # Scheme-specific named colors
        "ltbluishgray":  "#d9e8f0",
        "ltbluishgrey":  "#d9e8f0",
        "ebg":           "#f2e8ca",   # Economist background (cream/tan)
        "edkbg":         "#e8e3d2",   # Economist dark background
        "sunflowerlime": "#c8db2a",
        "chocolate":     "#7b3f00",
        # Transparent / none — map to white (6-char hex; full RGBA not supported here)
        "none":          "#ffffff",
        "":              "#000000",
    }

    # ------------------------------------------------------------------
    # Stata marker symbol → Bokeh marker string
    # ------------------------------------------------------------------
    _MARKER_MAP: dict[str, str] = {
        "circle":          "circle",
        "o":               "circle",
        "circle_hollow":   "circle_dot",
        "oh":              "circle_dot",
        "square":          "square",
        "s":               "square",
        "square_hollow":   "square_dot",
        "sh":              "square_dot",
        "diamond":         "diamond",
        "d":               "diamond",
        "diamond_hollow":  "diamond_dot",
        "dh":              "diamond_dot",
        "triangle":        "triangle",
        "t":               "triangle",
        "triangle_hollow": "inverted_triangle",
        "th":              "inverted_triangle",
        "plus":            "plus",
        "+":               "plus",
        "x":               "x",
        "X":               "x",
        "smcircle":        "circle",
        "smcircle_hollow": "circle_dot",
        "smx":             "x",
        "smsquare":        "square",
        "p":               "circle",
        "pipe":            "dash",
        "T":               "triangle",
        "star":            "star",
        "asterisk":        "asterisk",
        "hexagon":         "hex",
        "hexagon_hollow":  "hex_dot",
        "point":           "circle",
        "dot":             "dot",
    }

    # ------------------------------------------------------------------
    # Stata marker size keyword → pixel size (approximate)
    # ------------------------------------------------------------------
    _SIZE_MAP: dict[str, int] = {
        "tiny":     3,
        "vsmall":   5,
        "small":    7,
        "medsmall": 9,
        "medium":   11,
        "medlarge": 13,
        "large":    15,
        "vlarge":   19,
        "huge":     24,
    }

    # ------------------------------------------------------------------
    # Stata line width keyword → pixel width
    # ------------------------------------------------------------------
    _LWIDTH_MAP: dict[str, float] = {
        "vvthin":   0.2,
        "vthin":    0.5,
        "thin":     0.8,
        "medthin":  1.0,
        "medium":   1.5,
        "medthick": 2.0,
        "thick":    2.5,
        "vthick":   3.5,
        "vvthick":  5.0,
    }

    # ------------------------------------------------------------------
    # Stata line pattern → Bokeh dash specification
    # Bokeh accepts a list of pixel on/off lengths, or the string "solid".
    # ------------------------------------------------------------------
    _LPATTERN_MAP: dict[str, Any] = {
        "solid":      [],
        "l":          [],
        "dash":       [8, 4],
        "-":          [8, 4],
        "dot":        [2, 4],
        ".":          [2, 4],
        "dash_dot":   [8, 4, 2, 4],
        "-_-":        [8, 4, 2, 4],
        "shortdash":      [4, 4],
        "shortdot":       [2, 2],
        "shortdash_dot":  [4, 2, 2, 2],
        "longdash":       [16, 4],
        "longdash_dot":   [16, 4, 2, 4],
        "blank":      [0, 100],
        "b":          [0, 100],
    }

    @staticmethod
    def parse_color_alpha(value: str) -> "tuple[str | None, float | None]":
        """Parse a Stata color+alpha spec such as ``'red%50'`` or ``'%30'``.

        Stata allows an optional ``%N`` suffix on any color spec where *N* is
        0-100 and represents opacity percentage (0 = transparent, 100 = opaque).
        A bare ``%N`` with no color prefix means "use current color, change
        alpha only".

        Args:
            value: Raw option value from a Stata mcolor()/fcolor()/lcolor()
                   call, e.g. ``"navy%80"`` or ``"%50"`` or ``"navy"``.

        Returns:
            A ``(hex_color_or_None, alpha_0_to_1_or_None)`` tuple.  Either
            element can be ``None`` if absent.
        """
        v = value.strip()
        alpha: "float | None" = None
        hex_color: "str | None" = None

        # Split on the LAST '%' to find an optional alpha suffix.
        pct_idx = v.rfind("%")
        if pct_idx >= 0:
            alpha_str = v[pct_idx + 1:].strip()
            color_part = v[:pct_idx].strip()
            try:
                alpha_val = float(alpha_str)
                if 0.0 <= alpha_val <= 100.0:
                    alpha = alpha_val / 100.0
                    v = color_part          # strip alpha from the color string
            except ValueError:
                pass   # '%' is part of the color name — fall through

        # Resolve color (may be empty if bare '%N' form)
        if v:
            try:
                hex_color = OptionTranslator.translate_mcolor(v)
            except ValueError:
                pass   # unrecognised — return None

        return hex_color, alpha

    @staticmethod
    def translate_mcolor(value: str) -> str:
        """Return a CSS hex color string for a Stata mcolor() value.

        Strips any trailing ``%alpha`` suffix before resolving the color so
        that ``translate_mcolor`` can be used as a plain color resolver while
        ``parse_color_alpha`` handles the full ``color%alpha`` syntax.

        Args:
            value: A Stata color name (e.g. "navy"), RGB string "R G B", or
                   hex code.  A ``%N`` alpha suffix is silently stripped.

        Returns:
            A CSS hex color string, e.g. "#1a476f".

        Raises:
            ValueError: If the value cannot be recognised as a valid color.
        """
        # Strip alpha suffix before color resolution
        v = value.strip()
        pct_idx = v.rfind("%")
        if pct_idx >= 0:
            alpha_str = v[pct_idx + 1:].strip()
            try:
                alpha_val = float(alpha_str)
                if 0.0 <= alpha_val <= 100.0:
                    v = v[:pct_idx].strip()
            except ValueError:
                pass  # literal '%' in value — keep as-is
        v = v.lower()

        # RGB triplet: "255 0 128" or "255,0,128"
        parts = v.replace(",", " ").split()
        if len(parts) == 3:
            try:
                r, g, b = (int(p) for p in parts)
                if all(0 <= x <= 255 for x in (r, g, b)):
                    return f"#{r:02x}{g:02x}{b:02x}"
            except ValueError:
                pass

        # Named color lookup (case-insensitive)
        if v in OptionTranslator._COLOR_MAP:
            return OptionTranslator._COLOR_MAP[v]

        # Passthrough for hex values already in CSS format
        if v.startswith("#") and len(v) in (4, 7):
            return v

        raise ValueError(
            f"Unknown Stata color: '{value}'. "
            "Use a Stata named color (e.g. 'navy'), an RGB triplet "
            "(e.g. '0 0 128'), or a hex code (e.g. '#1a476f')."
        )

    @staticmethod
    def translate_msymbol(value: str) -> str:
        """Return a Bokeh marker string for a Stata msymbol() value.

        Args:
            value: A Stata marker name (e.g. "circle", "Oh", "S").

        Returns:
            A Bokeh marker type string, e.g. "circle".

        Raises:
            ValueError: If the symbol is not recognised.
        """
        v = value.strip()
        # Try exact match first, then lower-case
        result = (
            OptionTranslator._MARKER_MAP.get(v)
            or OptionTranslator._MARKER_MAP.get(v.lower())
        )
        if result is None:
            raise ValueError(
                f"Unrecognised Stata marker symbol: '{value}'. "
                "Examples: circle, square, diamond, triangle, plus, x."
            )
        return result

    @staticmethod
    def translate_msize(value: str) -> int:
        """Return a pixel size for a Stata msize() keyword or number.

        Args:
            value: A Stata size keyword (e.g. "medium") or a numeric string.

        Returns:
            An integer pixel size.

        Raises:
            ValueError: If the value is not recognised.
        """
        v = value.strip().lower()
        if v in OptionTranslator._SIZE_MAP:
            return OptionTranslator._SIZE_MAP[v]
        # Numeric passthrough (Stata also accepts raw numbers)
        try:
            return max(1, int(float(v)))
        except ValueError:
            pass
        raise ValueError(
            f"Unrecognised Stata size value: '{value}'. "
            "Use a keyword (tiny … huge) or a positive number."
        )

    @staticmethod
    def translate_lcolor(value: str) -> str:
        """Return a CSS hex color string for a Stata lcolor() value."""
        return OptionTranslator.translate_mcolor(value)

    @staticmethod
    def translate_lwidth(value: str) -> float:
        """Return a pixel line width for a Stata lwidth() value.

        Args:
            value: A Stata line-width keyword or numeric string.

        Returns:
            A float pixel width.

        Raises:
            ValueError: If the value is not recognised.
        """
        v = value.strip().lower()
        if v in OptionTranslator._LWIDTH_MAP:
            return OptionTranslator._LWIDTH_MAP[v]
        try:
            return max(0.1, float(v))
        except ValueError:
            pass
        raise ValueError(
            f"Unrecognised Stata line width: '{value}'. "
            "Use a keyword (vvthin … vvthick) or a positive number."
        )

    @staticmethod
    def translate_lpattern(value: str) -> Any:
        """Return a Bokeh dash specification for a Stata lpattern() value.

        Args:
            value: A Stata line-pattern name (e.g. "dash", "dot").

        Returns:
            The string "solid" or a list of on/off pixel lengths.

        Raises:
            ValueError: If the pattern is not recognised.
        """
        v = value.strip().lower()
        if v in OptionTranslator._LPATTERN_MAP:
            return OptionTranslator._LPATTERN_MAP[v]
        raise ValueError(
            f"Unrecognised Stata line pattern: '{value}'. "
            "Examples: solid, dash, dot, dash_dot, shortdash, longdash."
        )


# ===========================================================================
# SchemeParser — parse Stata .scheme files for Bokeh-mappable properties
# ===========================================================================

class SchemeParser:
    """Parses a Stata .scheme file and extracts properties relevant to Bokeh.

    Supports the ``#include schemename`` inheritance directive.  Child
    properties override parent properties.

    Usage::

        sp = SchemeParser("s2color")          # built-in bundled scheme
        sp = SchemeParser("myscheme.scheme")  # custom file from CWD

    All color values are translated to CSS hex strings via
    ``OptionTranslator.translate_mcolor()``.
    """

    _SCHEMES_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")

    _BUILTIN_NAMES: frozenset[str] = frozenset(
        {"s2color", "s1color", "s1mono", "economist", "sj"}
    )

    # Stata gsize keyword → CSS pt string
    _GSIZE_PT: dict[str, str] = {
        "minuscule": "6pt",
        "third_tiny": "6pt",
        "half_tiny":  "6pt",
        "tiny":     "7pt",
        "vsmall":   "8pt",
        "small":    "9pt",
        "medsmall": "10pt",
        "medium":   "11pt",
        "medlarge": "12pt",
        "large":    "13pt",
        "vlarge":   "15pt",
        "huge":     "18pt",
        "vhuge":    "22pt",
        "zero":     "0pt",
    }

    # Stata intensity keyword → float 0–1
    _INTENSITY: dict[str, float] = {
        "inten0":   0.0,  "inten10":  0.10, "inten20":  0.20,
        "inten30":  0.30, "inten40":  0.40, "inten50":  0.50,
        "inten60":  0.60, "inten70":  0.70, "inten80":  0.80,
        "inten90":  0.90, "inten100": 1.0,  "full":     1.0,
    }

    def __init__(self, scheme_name: str = "s2color") -> None:
        raw = (scheme_name or "s2color").strip()
        path = self._resolve_path(raw)
        raw_props = self._parse_file(path, _visited=set())
        self._props = raw_props
        self._init_properties()

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _resolve_path(self, name: str) -> str:
        """Return absolute path for a scheme name, blocking path traversal."""
        is_file_ref = name.endswith(".scheme") or os.sep in name or "/" in name

        if is_file_ref:
            # Try CWD first, then schemes/
            candidates = [
                os.path.abspath(os.path.join(os.getcwd(), name)),
                os.path.abspath(os.path.join(self._SCHEMES_DIR, name)),
            ]
        else:
            candidates = [
                os.path.abspath(
                    os.path.join(self._SCHEMES_DIR, name + ".scheme")
                )
            ]

        for candidate in candidates:
            # Security: must be within allowed dirs
            allowed = [
                os.path.abspath(self._SCHEMES_DIR),
                os.path.abspath(os.getcwd()),
            ]
            in_allowed = any(
                candidate.startswith(d + os.sep) or candidate == d
                for d in allowed
            )
            if not in_allowed:
                raise ValueError(
                    f"dash scheme: path '{name}' resolves outside allowed "
                    "directories (CWD or the dash schemes/ folder)."
                )
            if os.path.isfile(candidate):
                return candidate

        built_in_list = ", ".join(sorted(self._BUILTIN_NAMES))
        raise ValueError(
            f"dash: scheme '{name}' not found. "
            f"Built-in schemes: {built_in_list}. "
            "For a custom scheme, place a .scheme file in the current "
            "working directory and pass its filename."
        )

    # ------------------------------------------------------------------
    # File parsing
    # ------------------------------------------------------------------

    def _parse_file(self, path: str, _visited: set[str]) -> dict[str, str]:
        """Parse one .scheme file and return a flat key→value dict.

        Handles ``#include`` by recursively loading the parent first;
        child properties override parent properties.
        """
        real = os.path.realpath(path)
        if real in _visited:
            return {}   # circular include guard
        _visited.add(real)

        props: dict[str, str] = {}
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:
            raise ValueError(f"dash: cannot read scheme file '{path}': {exc}") from exc

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("*"):
                continue

            # #include directive — load parent first
            if line.startswith("#include"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    parent_name = parts[1].strip()
                    try:
                        parent_path = self._resolve_path(parent_name)
                        parent_props = self._parse_file(parent_path, _visited)
                        # Parent provides base; will be overridden by child
                        for k, v in parent_props.items():
                            if k not in props:
                                props[k] = v
                    except ValueError:
                        pass  # silently skip unresolvable includes
                continue

            tokens = line.split()
            if len(tokens) < 2:
                continue  # malformed line — skip

            category = tokens[0]
            value = tokens[-1]
            subcats = tokens[1:-1]
            key = (category + " " + " ".join(subcats)).strip() if subcats else category
            props[key] = value

        return props

    # ------------------------------------------------------------------
    # Property extraction
    # ------------------------------------------------------------------

    def _color(self, key: str, default: str = "#000000") -> str:
        """Translate a raw scheme color value to hex, falling back to default."""
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        try:
            return OptionTranslator.translate_mcolor(raw)
        except ValueError:
            return default

    def _gsize(self, key: str, default: str = "10pt") -> str:
        raw = self._props.get(key, "").strip().lower()
        if raw in self._GSIZE_PT:
            return self._GSIZE_PT[raw]
        # Numeric value like "3.0" → assume Stata points → rough CSS approximation
        try:
            val = float(raw)
            return f"{max(6, int(val * 1.2))}pt"
        except (ValueError, TypeError):
            return default

    def _intensity(self, key: str, default: float = 0.8) -> float:
        raw = self._props.get(key, "").strip().lower()
        if raw in self._INTENSITY:
            return self._INTENSITY[raw]
        try:
            return max(0.0, min(1.0, float(raw) / 100.0))
        except (ValueError, TypeError):
            return default

    def _lpattern(self, key: str) -> list:
        raw = self._props.get(key, "solid").strip().lower()
        return OptionTranslator.translate_lpattern(raw)

    def _lwidth(self, key: str, default: float = 1.5) -> float:
        raw = self._props.get(key, "").strip().lower()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            try:
                return OptionTranslator.translate_lwidth(raw)
            except ValueError:
                return default

    def _symbol(self, key: str, default: str = "circle") -> str:
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        try:
            return OptionTranslator.translate_msymbol(raw)
        except ValueError:
            return default

    def _init_properties(self) -> None:
        """Extract all Bokeh-relevant properties into named attributes."""
        # Background / region colors
        self.background_color: str = self._color("color background", "#d9e8f0")
        self.plotregion_color: str = self._color("color plotregion", "#ffffff")
        self.legend_bg_color: str = self._color("color legend", "#ffffff")
        self.legend_border_color: str = self._color("color legend_line", "#000000")
        self.grid_color: str = self._color(
            "color major_grid",
            self._color("color grid", "#d9e8f0"),
        )
        self.minor_grid_color: str = self._color("color minor_grid", "#cccccc")
        self.title_color: str = self._color("color heading", "#000000")
        self.axis_line_color: str = self._color("color axisline", "#000000")

        # Per-plot color cycles (15 entries)
        self.p_colors: list[str] = [
            self._color(f"color p{i}") for i in range(1, 16)
        ]
        self.p_line_colors: list[str] = [
            self._color(f"color p{i}line", self.p_colors[i - 1])
            for i in range(1, 16)
        ]
        self.p_bar_colors: list[str] = [
            self._color(f"color p{i}bar", self.p_colors[i - 1])
            for i in range(1, 16)
        ]
        self.p_mark_colors: list[str] = [
            self._color(f"color p{i}mark", self.p_colors[i - 1])
            for i in range(1, 16)
        ]

        # Marker symbol cycle
        self.p_symbols: list[str] = [
            self._symbol(f"symbol p{i}") for i in range(1, 16)
        ]

        # Line pattern cycle
        self.p_line_patterns: list = [
            self._lpattern(f"linepattern p{i}line") for i in range(1, 16)
        ]

        # Default line/grid widths
        self.default_line_width: float = self._lwidth("linewidth p", 1.5)
        self.grid_line_width: float = self._lwidth("linewidth major_grid", 0.8)

        # Fill intensities
        self.fill_alpha: float = self._intensity("intensity p", 0.8)
        self.bar_alpha: float = self._intensity("intensity bar", 0.8)
        self.area_alpha: float = self._intensity("intensity area", 0.8)

        # Font sizes
        self.text_font_size: str = self._gsize("gsize text", "10pt")
        self.heading_font_size: str = self._gsize("gsize heading", "13pt")
        self.axis_title_font_size: str = self._gsize("gsize axis_title", "10pt")
        self.tick_label_font_size: str = self._gsize("gsize tick_label", "10pt")
        self.note_font_size: str = self._gsize("gsize note", "9pt")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def default_color(self, index: int, plot_type: str = "scatter") -> str:
        """Return the default CSS hex color for the plot at *index*.

        Args:
            index:     Zero-based plot index within the figure.
            plot_type: One of ``"scatter"``, ``"line"``, ``"connected"``,
                       ``"bar"``, ``"area"``, ``"rbar"``, ``"rarea"``.
        """
        idx = index % 15
        if plot_type in {"line", "connected", "tsline", "tsrline",
                         "mspline", "mband", "rline", "rconnected"}:
            return self.p_line_colors[idx]
        if plot_type in {"bar", "rbar", "area", "rarea", "histogram"}:
            return self.p_bar_colors[idx]
        return self.p_colors[idx]

    def default_symbol(self, index: int) -> str:
        """Return the Bokeh marker string for the plot at *index*."""
        return self.p_symbols[index % 15]

    def default_line_pattern(self, index: int) -> list:
        """Return the Bokeh dash list for the line plot at *index*."""
        return self.p_line_patterns[index % 15]

    def apply_to_figure(self, fig: Any) -> None:
        """Apply scheme defaults to *fig*.

        Called before explicit graph_opts so that explicit options override.
        """
        fig.background_fill_color = self.plotregion_color
        fig.border_fill_color = self.background_color
        if self.axis_line_color:
            fig.outline_line_color = self.axis_line_color

        for grid in list(fig.xgrid) + list(fig.ygrid):
            grid.grid_line_color = self.grid_color
            grid.grid_line_width = self.grid_line_width

        for axis in list(fig.xaxis) + list(fig.yaxis):
            axis.axis_line_color = self.axis_line_color
            axis.axis_label_text_font_size = self.axis_title_font_size
            axis.major_label_text_font_size = self.tick_label_font_size

    def css_block(self) -> str:
        """Return a ``<style>`` block for the dashboard outer chrome."""
        bg = html.escape(self.background_color)
        tc = html.escape(self.title_color)
        hs = html.escape(self.heading_font_size)
        ts = html.escape(self.text_font_size)
        lbg = html.escape(self.legend_bg_color)
        return (
            f"<style>\n"
            f"  body, .bk-root {{ background-color: {bg}; }}\n"
            f"  .dash-title {{ color: {tc}; font-size: {hs}; }}\n"
            f"  .dash-subtitle {{ color: {tc}; font-size: {ts}; }}\n"
            f"  .kpi-card {{ background-color: {lbg}; }}\n"
            f"</style>\n"
        )


# ===========================================================================
# Module-level helpers
# ===========================================================================

def _apply_jitter(
    x_arr: "np.ndarray",
    y_arr: "np.ndarray",
    jitter_pct: float,
    seed: "int | None" = None,
) -> "tuple[np.ndarray, np.ndarray]":
    """Return jittered copies of *x_arr* and *y_arr*.

    Args:
        x_arr:      1-D numeric array of x values.
        y_arr:      1-D numeric array of y values (same length).
        jitter_pct: Percentage (1–100) of axis range used as jitter half-width.
        seed:       Optional integer RNG seed for reproducibility.

    Returns:
        ``(x_jit, y_jit)`` — copies with uniform noise added independently
        to each axis.
    """
    if len(x_arr) == 0:
        return x_arr.copy(), y_arr.copy()
    pct = max(0.0, min(100.0, float(jitter_pct))) / 100.0
    if pct == 0.0:
        return x_arr.copy(), y_arr.copy()
    rng = np.random.default_rng(seed)
    x_range = float(np.nanmax(x_arr) - np.nanmin(x_arr)) or 1.0
    y_range = float(np.nanmax(y_arr) - np.nanmin(y_arr)) or 1.0
    half_x = pct * x_range / 2.0
    half_y = pct * y_range / 2.0
    x_noise = rng.uniform(-half_x, half_x, size=len(x_arr))
    y_noise = rng.uniform(-half_y, half_y, size=len(y_arr))
    return x_arr + x_noise, y_arr + y_noise


def _compute_secondary_range(
    df: "pd.DataFrame",
    plots: list[dict],
    axis_key: str,
    var_key: str,
    axis_number: int = 2,
    padding_pct: float = 0.05,
) -> "tuple[float, float]":
    """Compute data min/max for all plot layers assigned to *axis_number*.

    Args:
        df:           Full graph DataFrame (after graph-level filter).
        plots:        List of plot spec dicts for this graph.
        axis_key:     ``"yaxis"`` or ``"xaxis"``.
        var_key:      ``"yvar"`` or ``"xvar"``.
        axis_number:  The secondary axis number (2).
        padding_pct:  Fractional padding added to each side of the range.

    Returns:
        ``(lo, hi)`` range with padding, or ``(0.0, 1.0)`` if no valid data.
    """
    vals: list[float] = []
    for plot in plots:
        opts = plot.get("options", {})
        if str(opts.get(axis_key, "1")).strip() != str(axis_number):
            continue
        varname = plot.get(var_key, "")
        if varname and varname in df.columns:
            col = pd.to_numeric(df[varname], errors="coerce").dropna()
            vals.extend(col.tolist())
    if not vals:
        return 0.0, 1.0
    lo, hi = float(np.min(vals)), float(np.max(vals))
    span = hi - lo if hi != lo else 1.0
    return lo - padding_pct * span, hi + padding_pct * span


# ===========================================================================
# GlyphMapper
# ===========================================================================

class GlyphMapper:
    """Maps Stata twoway plot types to Bokeh glyph renderers.

    Each ``map_*`` method adds one or more glyph renderers to the supplied
    Bokeh ``figure`` and returns a list of the renderers created.  All methods
    operate on a ``ColumnDataSource`` that has already been populated from the
    jsonio data, so the CDS column names are just the Stata variable names.

    Missing-value handling: Stata's system-missing value ``'.'`` is stored as
    ``float('nan')`` in the pandas DataFrame and therefore in the CDS.  Bokeh
    silently skips NaN entries for all glyphs, so no special masking is needed
    at the glyph level — but computed aggregates (lfit, histogram, etc.) must
    drop NaN rows from their input arrays explicitly.
    """

    def __init__(
        self,
        translator: OptionTranslator | None = None,
        scheme: "SchemeParser | None" = None,
    ) -> None:
        """Initialise the mapper with an optional OptionTranslator and scheme."""
        self.tr = translator or OptionTranslator()
        # Defer scheme import to avoid circular dependency; default to s2color
        if scheme is None:
            self.scheme: "SchemeParser" = SchemeParser("s2color")
        else:
            self.scheme = scheme

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Jitter helper
    # ------------------------------------------------------------------

    @staticmethod
    def _build_jitter_source(
        source: ColumnDataSource,
        xvar: str,
        yvar: str,
        options: dict[str, str],
    ) -> "tuple[ColumnDataSource, str, str]":
        """Return a (possibly jittered) source and effective x/y column names.

        If the ``jitter`` option is absent or zero, returns the original
        *source* unchanged.  Otherwise adds ``_x_jit`` / ``_y_jit`` columns
        and returns a new CDS that also contains the original columns so that
        hover tooltips and mlabel annotations can reference them.

        Returns:
            ``(plot_source, effective_xvar, effective_yvar)``
        """
        jitter_raw = options.get("jitter", "").strip()
        if not jitter_raw:
            return source, xvar, yvar

        try:
            jitter_pct = float(jitter_raw)
        except (ValueError, TypeError):
            return source, xvar, yvar

        if jitter_pct <= 0:
            return source, xvar, yvar

        # Clamp to [1, 100]
        jitter_pct = min(100.0, jitter_pct)

        seed_raw = options.get("jseed", "").strip()
        seed_val: int | None = None
        if seed_raw:
            try:
                seed_val = int(float(seed_raw))
            except (ValueError, TypeError):
                pass

        x_arr = np.asarray(source.data[xvar], dtype=float)
        y_arr = np.asarray(source.data[yvar], dtype=float)
        x_jit, y_jit = _apply_jitter(x_arr, y_arr, jitter_pct, seed_val)

        # Build new data dict preserving all original columns
        new_data = {k: list(v) for k, v in source.data.items()}
        new_data["_x_jit"] = x_jit.tolist()
        new_data["_y_jit"] = y_jit.tolist()
        return ColumnDataSource(new_data), "_x_jit", "_y_jit"

    def _hover_tool(self, yvar: str, xvar: str,
                   renderers: "list | None" = None) -> HoverTool:
        """Return a HoverTool scoped to *renderers* (or all if None)."""
        ht = HoverTool(tooltips=[
            (xvar, f"@{{{xvar}}}"),
            (yvar, f"@{{{yvar}}}"),
        ])
        if renderers is not None:
            ht.renderers = renderers
        return ht

    def _check_vars(
        self,
        source: ColumnDataSource,
        *varnames: str,
    ) -> bool:
        """Return True if all non-empty varnames exist in source.data.

        Emits a warning and returns False when any variable is missing so
        callers can skip the glyph rather than raising a KeyError.
        """
        import warnings
        missing = [v for v in varnames if v and v not in source.data]
        if missing:
            warnings.warn(
                f"dash: variable(s) {missing!r} not found in data source; "
                "skipping glyph. Check that all plot variables exist in the dataset.",
                stacklevel=3,
            )
            return False
        return True

    @staticmethod
    def _is_empty(source: ColumnDataSource, *varnames: str) -> bool:
        """Return True if source has no rows (all requested columns are empty).

        Used to short-circuit mapper methods when data is empty so they return
        a lightweight empty glyph instead of potentially emitting NumPy warnings.
        """
        for v in varnames:
            col = source.data.get(v)
            if col is not None and len(col) > 0:
                return False
        return True

    def _render_ci_band(
        self,
        fig: Any,
        source: ColumnDataSource,
        x_col: str,
        y_col: str,
        color: str,
        yvar: str,
        options: "dict[str, str]",
        lo_col: str = "y_lower",
        hi_col: str = "y_upper",
    ) -> "tuple[Any, Any]":
        """Render a confidence-interval band (varea + line) onto *fig*.

        Applies ``_apply_line_opts`` and ``_apply_fill_opts`` from *options*.

        Args:
            fig:     Bokeh Figure.
            source:  ColumnDataSource with the CI columns.
            x_col:   Name of the x column in *source*.
            y_col:   Name of the central-fit y column in *source*.
            color:   Line and fill colour hex string.
            yvar:    Variable name used for the legend label.
            options: Plot-level options dict (lcolor, lwidth, fcolor, …).
            lo_col:  Name of the lower-CI column (default ``"y_lower"``).
            hi_col:  Name of the upper-CI column (default ``"y_upper"``).

        Returns:
            A ``(line_renderer, band_renderer)`` tuple.
        """
        band_r = fig.varea(
            x=x_col, y1=lo_col, y2=hi_col,
            source=source, fill_alpha=0.2, fill_color=color,
        )
        line_r = fig.line(
            x=x_col, y=y_col, source=source,
            line_color=color, line_width=2.0, legend_label=yvar,
        )
        self._apply_line_opts(line_r, options)
        self._apply_fill_opts(band_r, options)
        return line_r, band_r

    @staticmethod
    def _bootstrap_ci(
        x: "np.ndarray",
        y: "np.ndarray",
        x_grid: "np.ndarray",
        fit_fn: "Any",
        n_boot: int = 200,
        seed: int = 42,
        fallback: "np.ndarray | None" = None,
    ) -> "tuple[np.ndarray, np.ndarray]":
        """Compute a bootstrap 95% confidence interval for a smooth fit.

        Args:
            x:        Observed x values (NaN-free).
            y:        Observed y values (NaN-free, same length as x).
            x_grid:   Grid of x values at which predictions are made.
            fit_fn:   Callable ``(xi, yi, xg) -> np.ndarray`` that returns
                      predicted y values on *xg* for a bootstrap sample
                      ``(xi, yi)``.  May raise ``ValueError``,
                      ``LinAlgError``, or ``FloatingPointError`` for
                      degenerate samples — those are caught and replaced
                      with *fallback*.
            n_boot:   Number of bootstrap resamples (default 200).
            seed:     Random-number-generator seed for reproducibility.
            fallback: Array of length ``len(x_grid)`` used when *fit_fn*
                      fails or returns NaN predictions for a resample.
                      Defaults to zeros when ``None``.

        Returns:
            ``(y_lower, y_upper)`` arrays of length ``len(x_grid)``
            representing the 2.5th and 97.5th percentiles of the
            bootstrap distribution.
        """
        n_grid = len(x_grid)
        _fb = fallback if fallback is not None else np.zeros(n_grid)
        rng = np.random.default_rng(seed=seed)
        boot_preds = np.zeros((n_boot, n_grid))
        for i in range(n_boot):
            idx = rng.integers(0, len(x), size=len(x))
            try:
                preds = fit_fn(x[idx], y[idx], x_grid)
                # Replace NaN predictions with the fallback (e.g. the main fit)
                boot_preds[i] = np.where(np.isnan(preds), _fb, preds)
            except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                boot_preds[i] = _fb
        return (
            np.percentile(boot_preds, 2.5, axis=0),
            np.percentile(boot_preds, 97.5, axis=0),
        )

    def _apply_line_opts(
        self,
        renderer: Any,
        options: dict[str, str],
    ) -> None:
        """Apply lcolor/lwidth/lpattern/lalpha options to a line-type glyph renderer."""
        glyph = renderer.glyph
        if "lcolor" in options:
            try:
                color, alpha = self.tr.parse_color_alpha(options["lcolor"])
                if color:
                    glyph.line_color = color
                if alpha is not None and hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = alpha
            except (ValueError, AttributeError):
                pass
        if "lwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["lwidth"])
            except ValueError:
                pass
        if "lpattern" in options:
            try:
                glyph.line_dash = self.tr.translate_lpattern(options["lpattern"])
            except ValueError:
                pass
        # lalpha: standalone line opacity, 0-100%
        if "lalpha" in options:
            try:
                la = float(options["lalpha"].strip())
                if 0.0 <= la <= 100.0 and hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = la / 100.0
            except (ValueError, AttributeError):
                pass

    def _apply_marker_opts(
        self,
        renderer: Any,
        options: dict[str, str],
    ) -> None:
        """Apply mcolor/msymbol/msize/malpha options to a scatter-type glyph renderer.

        Supports Stata's ``color%alpha`` notation on ``mcolor``, ``mfcolor``,
        and ``lcolor`` (e.g. ``mcolor(red%50)``).  A standalone ``malpha``
        option overrides the alpha of both fill and line; ``lalpha`` overrides
        only the line alpha.

        The generic ``marker`` key (produced by the Mata parser's ``m()``
        abbreviation expansion) is treated as an alias for ``msymbol``.
        If both ``marker`` and ``msymbol`` are present, ``msymbol`` wins
        because it is applied last.
        """
        glyph = renderer.glyph
        # Handle generic 'm → marker' abbreviation as msymbol alias
        if "marker" in options and "msymbol" not in options:
            try:
                glyph.marker = self.tr.translate_msymbol(options["marker"])
            except (ValueError, AttributeError):
                pass
        if "mcolor" in options:
            try:
                color, alpha = self.tr.parse_color_alpha(options["mcolor"])
                if color:
                    glyph.fill_color = color
                    glyph.line_color = color
                if alpha is not None:
                    if hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = alpha
                    if hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = alpha
            except (ValueError, AttributeError):
                pass
        if "msymbol" in options:
            try:
                glyph.marker = self.tr.translate_msymbol(options["msymbol"])
            except (ValueError, AttributeError):
                pass
        if "msize" in options:
            try:
                glyph.size = self.tr.translate_msize(options["msize"])
            except ValueError:
                pass
        # mfcolor sets the fill color independently of the line/outline color.
        # Supports color%alpha notation; applied after mcolor so it wins.
        if "mfcolor" in options:
            try:
                color, alpha = self.tr.parse_color_alpha(options["mfcolor"])
                if color:
                    glyph.fill_color = color
                if alpha is not None and hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = alpha
            except (ValueError, AttributeError):
                pass
        # lcolor sets the marker border (outline) color independently of fill.
        if "lcolor" in options:
            try:
                color, alpha = self.tr.parse_color_alpha(options["lcolor"])
                if color and hasattr(glyph, "line_color"):
                    glyph.line_color = color
                if alpha is not None and hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = alpha
            except (ValueError, AttributeError):
                pass
        # lwidth sets the marker border width.
        if "lwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["lwidth"])
            except (ValueError, AttributeError):
                pass
        # malpha: standalone fill+line opacity override, 0-100%.
        # Applied last so it wins over any alpha embedded in mcolor/mfcolor/lcolor.
        if "malpha" in options:
            try:
                ma = float(options["malpha"].strip())
                if 0.0 <= ma <= 100.0:
                    if hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = ma / 100.0
                    if hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = ma / 100.0
            except (ValueError, AttributeError):
                pass
        # lalpha: standalone line-only opacity, 0-100%.
        if "lalpha" in options:
            try:
                la = float(options["lalpha"].strip())
                if 0.0 <= la <= 100.0 and hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = la / 100.0
            except (ValueError, AttributeError):
                pass
        # msangle: rotate all markers by a fixed angle (degrees → radians).
        # Bokeh scatter glyphs support a scalar angle property.
        if "msangle" in options:
            try:
                angle_deg = float(options["msangle"].strip())
                if hasattr(glyph, "angle"):
                    glyph.angle = math.radians(angle_deg)
                    if hasattr(glyph, "angle_units"):
                        glyph.angle_units = "rad"
            except (ValueError, AttributeError):
                pass

    def _apply_fill_opts(self, renderer: Any, options: dict[str, str]) -> None:
        """Apply fcolor/fintensity options to a filled glyph renderer.

        Supports Stata's ``color%alpha`` notation on ``fcolor``
        (e.g. ``fcolor(red%60)``).

        Args:
            renderer: A Bokeh GlyphRenderer whose glyph has fill_color /
                      fill_alpha attributes (VArea, VBar, Quad, etc.).
            options:  Translated per-plot options dict.
        """
        glyph = renderer.glyph
        if "fcolor" in options:
            try:
                color, alpha = self.tr.parse_color_alpha(options["fcolor"])
                if color:
                    glyph.fill_color = color
                if alpha is not None and hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = alpha
            except (ValueError, AttributeError):
                pass
        if "fintensity" in options:
            try:
                val = options["fintensity"].strip()
                # Stata fintensity: 0-100 (percentage) or keywords inten0-inten100
                if val.startswith("inten"):
                    pct = float(val[5:]) / 100.0
                else:
                    pct = float(val) / 100.0
                pct = max(0.0, min(1.0, pct))
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = pct
            except (ValueError, AttributeError):
                pass

    # Supported palette names → Bokeh palette identifiers
    _PALETTE_MAP: "dict[str, str]" = {
        "viridis":    "Viridis256",
        "magma":      "Magma256",
        "inferno":    "Inferno256",
        "plasma":     "Plasma256",
        "cividis":    "Cividis256",
        "turbo":      "Turbo256",
        "blues":      "Blues256",
        "greens":     "Greens256",
        "reds":       "Reds256",
        "greys":      "Greys256",
        "oranges":    "Oranges256",
        "purples":    "Purples256",
        "spectral":   "Spectral11",
        "rdylgn":     "RdYlGn11",
        "rdbu":       "RdBu11",
        "category10": "Category10_10",
        "category20": "Category20_20",
        "set1":       "Set1_9",
        "set2":       "Set2_8",
        "set3":       "Set3_12",
        "paired":     "Paired_12",
    }

    def _apply_colorvar(
        self,
        fig: Any,
        renderer: Any,
        source: "ColumnDataSource",
        options: dict[str, str],
    ) -> None:
        """Map a CDS variable's values to glyph fill/line color.

        When ``colorvar(varname)`` is present and *varname* is a column in
        *source*, a ``LinearColorMapper`` (numeric data) or
        ``CategoricalColorMapper`` (string/boolean data) is applied and a
        ``ColorBar`` is added on the right side of *fig*.

        An optional ``colpalette(name)`` option selects the palette.  Supported
        names are the keys of ``_PALETTE_MAP`` (e.g. ``viridis``, ``magma``,
        ``category10``).  Defaults to ``viridis`` for continuous data and
        ``category10`` for categorical data.

        Args:
            fig:      Bokeh Figure object.
            renderer: GlyphRenderer whose fill/line color will be driven by the
                      mapper.
            source:   ColumnDataSource containing *varname* as a column.
            options:  Per-plot options dict (may contain ``colorvar`` and
                      ``colpalette``).
        """
        varname = options.get("colorvar", "").strip()
        if not varname or varname not in source.data:
            return

        # Security: validate varname is a safe identifier
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname):
            return

        from bokeh.models import (
            LinearColorMapper, CategoricalColorMapper, ColorBar,
        )
        from bokeh import palettes as _bk_palettes

        raw_col = source.data[varname]
        palette_key = options.get("colpalette", "").strip().lower()

        # Determine if the column is numeric or categorical
        try:
            col_vals = np.array(raw_col, dtype=float)
            is_numeric = not np.all(np.isnan(col_vals))
        except (ValueError, TypeError):
            is_numeric = False

        if is_numeric:
            lo = float(np.nanmin(col_vals))
            hi = float(np.nanmax(col_vals))
            if lo == hi:
                hi = lo + 1.0
            pal_name = self._PALETTE_MAP.get(palette_key or "viridis", "Viridis256")
            palette = getattr(_bk_palettes, pal_name, None)
            if palette is None:
                palette = _bk_palettes.Viridis256
            mapper = LinearColorMapper(palette=palette, low=lo, high=hi,
                                       nan_color="grey")
        else:
            # Categorical: convert all values to strings, get unique sorted factors
            factors = sorted({str(v) for v in raw_col
                               if v is not None and str(v) != "nan"})
            if not factors:
                return
            pal_name = self._PALETTE_MAP.get(palette_key or "category10",
                                             "Category10_10")
            palette = getattr(_bk_palettes, pal_name, None)
            if palette is None:
                palette = _bk_palettes.Category10_10
            # Extend palette if more factors than palette entries
            pal_list = list(palette)
            while len(pal_list) < len(factors):
                pal_list += pal_list
            palette = pal_list[:len(factors)]
            # Re-encode source column as strings for CategoricalColorMapper
            source.data[varname] = [str(v) for v in raw_col]
            mapper = CategoricalColorMapper(factors=factors, palette=palette)

        # Apply mapper to the glyph fill and line color
        glyph = renderer.glyph
        color_spec = {"field": varname, "transform": mapper}
        try:
            glyph.fill_color = color_spec
            glyph.line_color = color_spec
        except (AttributeError, ValueError):
            pass

        # Add a ColorBar to the right of the figure
        try:
            color_bar = ColorBar(
                color_mapper=mapper,
                label_standoff=8,
                width=12,
                location=(0, 0),
                title=html.escape(varname),
            )
            fig.add_layout(color_bar, "right")
        except (ValueError, TypeError, KeyError) as _exc:   # noqa: BLE001 — never crash the render
            import warnings
            warnings.warn(f"dash: color bar skipped — {_exc}", stacklevel=2)

    def _apply_mlabel_opts(
        self,
        fig: Any,
        source: "ColumnDataSource",
        options: dict[str, str],
        xvar: str,
        yvar: str,
    ) -> None:
        """Add a LabelSet annotation when the mlabel() option is set.

        Reads ``mlabel``, ``mlabcolor``, ``mlabsize``, ``mlabposition``, and
        ``mlabgap`` from *options* and adds a Bokeh ``LabelSet`` to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  ColumnDataSource that contains the label column.
            options: Translated plot-level options dict.
            xvar:    Name of the x-axis variable column in *source*.
            yvar:    Name of the y-axis variable column in *source*.
        """
        from bokeh.models import LabelSet

        mlabel_var = options.get("mlabel", "")
        if not mlabel_var or mlabel_var not in source.data:
            return

        kwargs: dict[str, Any] = dict(
            x=xvar,
            y=yvar,
            text=mlabel_var,
            source=source,
            text_font_size="10px",
            x_offset=4,
            y_offset=4,
        )

        if "mlabcolor" in options:
            try:
                kwargs["text_color"] = self.tr.translate_mcolor(options["mlabcolor"])
            except ValueError:
                pass

        if "mlabsize" in options:
            try:
                size_px = self.tr.translate_msize(options["mlabsize"])
                kwargs["text_font_size"] = f"{size_px}px"
            except ValueError:
                pass

        # mlabposition: Stata clock positions 0-12
        pos = options.get("mlabposition", "3")
        try:
            p = int(pos)
            # Clock positions: 3=right (default), 9=left, 12=above, 6=below
            offset_map = {
                0: (0, 0), 1: (3, 3), 2: (3, 2), 3: (4, 0),
                4: (3, -2), 5: (3, -3), 6: (0, -4), 7: (-3, -3),
                8: (-3, -2), 9: (-4, 0), 10: (-3, 2), 11: (-3, 3), 12: (0, 4),
            }
            if p in offset_map:
                kwargs["x_offset"], kwargs["y_offset"] = offset_map[p]
        except (ValueError, TypeError):
            pass

        if "mlabgap" in options:
            try:
                gap = int(float(options["mlabgap"]))
                kwargs["x_offset"] = kwargs.get("x_offset", 4) + gap
                kwargs["y_offset"] = kwargs.get("y_offset", 4) + gap
            except (ValueError, TypeError):
                pass

        # mlabwidth: Stata label width in character units.  Bokeh's LabelSet
        # does not support text wrapping, so this option is accepted but has
        # no visual effect.  It is handled here to prevent an "unknown option"
        # error if the user specifies it.
        options.get("mlabwidth")  # consumed; no-op

        ls = LabelSet(**kwargs)
        fig.add_layout(ls)

    # ------------------------------------------------------------------
    # Phase 1A plot types
    # ------------------------------------------------------------------

    def map_scatter(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add a scatter glyph to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y-axis variable (CDS column).
            xvar:    Name of the x-axis variable (CDS column).
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer created.
        """
        marker = "circle"
        if "msymbol" in options:
            try:
                marker = self.tr.translate_msymbol(options["msymbol"])
            except ValueError:
                pass

        if view is not None:
            # Shared source (by+link): skip NaN-drop, use source directly
            clean_source = source
        else:
            # Drop NaN rows if present; otherwise reuse the original source.
            # Preserve all columns so that mlabel and other annotation columns
            # remain available on clean_source.
            x_series = pd.Series(source.data[xvar])
            y_series = pd.Series(source.data[yvar])
            has_nan = x_series.isna().any() or y_series.isna().any()
            if has_nan:
                df = pd.DataFrame({col: source.data[col] for col in source.data})
                df = df.dropna(subset=[xvar, yvar])
                clean_source: ColumnDataSource = ColumnDataSource(df)
            else:
                clean_source = source

        # Apply jitter if requested
        plot_source, eff_x, eff_y = self._build_jitter_source(
            clean_source, xvar, yvar, options
        )

        _default_color = self.scheme.default_color(color_idx, "scatter")
        _scatter_kwargs: dict = dict(
            x=eff_x,
            y=eff_y,
            source=plot_source,
            marker=marker,
            size=8,
            fill_color=_default_color,
            line_color=_default_color,
            alpha=0.7,
            legend_label=yvar,
        )
        if view is not None:
            _scatter_kwargs["view"] = view
        r = fig.scatter(**_scatter_kwargs)
        self._apply_marker_opts(r, options)
        # colorvar: map a variable's values to fill/line color via a color mapper
        self._apply_colorvar(fig, r, plot_source, options)
        # mlabel uses original column names (not jittered) for readable labels
        self._apply_mlabel_opts(fig, plot_source, options, xvar, yvar)
        fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))
        return r

    def map_line(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add a line glyph to *fig*.

        Data is sorted by the x variable before rendering to match Stata
        behaviour (Stata's twoway line auto-sorts by x).

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y-axis variable (CDS column).
            xvar:    Name of the x-axis variable (CDS column).
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer created.
        """
        # Drop NaN and sort by x for correct line rendering
        df = pd.DataFrame({xvar: source.data[xvar], yvar: source.data[yvar]})
        df = df.dropna(subset=[xvar, yvar]).sort_values(xvar)
        sorted_source = ColumnDataSource(df)

        _line_kwargs: dict = dict(
            x=xvar,
            y=yvar,
            source=sorted_source,
            line_color=self.scheme.default_color(color_idx, "line"),
            line_width=1.5,
            legend_label=yvar,
        )
        if view is not None:
            _line_kwargs["view"] = view
        r = fig.line(**_line_kwargs)
        self._apply_line_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))
        return r

    def map_connected(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add connected (line + scatter) glyphs to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y-axis variable.
            xvar:    Name of the x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List of two GlyphRenderers [line_renderer, scatter_renderer].
        """
        # Pass options without mlabel to sub-calls; apply mlabel once below
        opts_no_label = {k: v for k, v in options.items() if k != "mlabel"}
        renderers = [
            self.map_line(fig, source, yvar, xvar, opts_no_label, view=view, color_idx=color_idx),
            self.map_scatter(fig, source, yvar, xvar, opts_no_label, view=view, color_idx=color_idx),
        ]
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return renderers

    def map_area(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add an area glyph (filled between y=0 and y=yvar) to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable (upper boundary).
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            The single VArea GlyphRenderer created.
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y_arr = np.array(source.data[yvar], dtype=float)
        # Drop NaN rows
        mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
        x_arr, y_arr = x_arr[mask], y_arr[mask]
        # base() option sets the lower boundary; default 0
        base_val = 0.0
        if "base" in options:
            try:
                base_val = float(options["base"])
            except (ValueError, TypeError):
                pass
        y1_base = np.full_like(y_arr, base_val)
        _y1_col = f"{yvar}_base"

        # _y1_col = baseline, yvar = upper boundary
        area_source = ColumnDataSource({xvar: x_arr, _y1_col: y1_base, yvar: y_arr})
        r = fig.varea(x=xvar, y1=_y1_col, y2=yvar, source=area_source,
                      fill_color=self.scheme.default_color(color_idx, "area"),
                      fill_alpha=0.5, legend_label=yvar)

        # Honour fill color option
        if "color" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["color"])
            except ValueError:
                pass

        self._apply_fill_opts(r, options)

        # Add an optional border line on top of the area when line options are given.
        # VArea has no native border; a separate Line renderer is required.
        _LINE_KEYS = ("lcolor", "lwidth", "lpattern")
        if any(k in options for k in _LINE_KEYS):
            # Default border color = same as fill color
            border_color = r.glyph.fill_color or "#aec7e8"
            border_source = ColumnDataSource({xvar: x_arr, yvar: y_arr})
            line_r = fig.line(x=xvar, y=yvar, source=border_source,
                               line_color=border_color, line_width=1.5)
            self._apply_line_opts(line_r, options)

        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    def map_bar(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add vertical bar glyphs to *fig*.

        Bar width is automatically computed as 80% of the smallest gap between
        consecutive distinct x values.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y (height) variable.
            xvar:    Name of the x (centre) variable.
            options: Translated plot-level options dict.

        Returns:
            The single VBar GlyphRenderer created.
        """
        if self._is_empty(source, xvar, yvar):
            empty_src = ColumnDataSource({xvar: [], yvar: []})
            return fig.vbar(x=xvar, top=yvar, bottom=0, width=0.8, source=empty_src)
        # Drop NaN rows
        df = pd.DataFrame({xvar: source.data[xvar], yvar: source.data[yvar]})
        df = df.dropna(subset=[xvar, yvar])
        clean_source = ColumnDataSource(df)

        try:
            x_vals = sorted(set(float(v) for v in df[xvar]))
        except (ValueError, TypeError):
            # String xvar: use uniform spacing (bar width = 0.8)
            x_vals = list(range(len(df[xvar].unique())))
        if len(x_vals) >= 2:
            gaps = [x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)]
            bar_width = 0.8 * min(gaps)
        else:
            bar_width = 0.8

        # barwidth() / width() options override the auto-computed bar width
        for key in ("barwidth", "width"):
            if key in options:
                try:
                    bar_width = float(options[key])
                    break
                except (ValueError, TypeError):
                    pass

        # base() option sets the bar bottom; default 0
        base_val = 0.0
        if "base" in options:
            try:
                base_val = float(options["base"])
            except (ValueError, TypeError):
                pass

        _bar_default_color = self.scheme.default_color(color_idx, "bar")
        _vbar_kwargs: dict = dict(
            x=xvar, top=yvar, bottom=base_val, source=clean_source,
            width=bar_width,
            fill_color=_bar_default_color,
            line_color=_bar_default_color,
            legend_label=yvar,
            fill_alpha=0.8,
        )
        if view is not None:
            _vbar_kwargs["view"] = view
        r = fig.vbar(**_vbar_kwargs)
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
                r.glyph.line_color = c
            except ValueError:
                pass
        # bfcolor / blcolor — bar-specific fill / line color overrides
        if "bfcolor" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["bfcolor"])
            except ValueError:
                pass
        if "blcolor" in options:
            try:
                r.glyph.line_color = self.tr.translate_mcolor(options["blcolor"])
            except ValueError:
                pass
        self._apply_fill_opts(r, options)
        # VBar supports line_width/line_dash/line_color natively; lcolor/lwidth/lpattern
        # are applied after bfcolor/blcolor so blcolor retains priority for line color.
        self._apply_line_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    def map_spike(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add vertical spike glyphs (segments from y=0 to y=yvar) to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable (spike top).
            xvar:    Name of the x variable (spike position).
            options: Translated plot-level options dict.

        Returns:
            The single Segment GlyphRenderer created.
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y_arr = np.array(source.data[yvar], dtype=float)
        # Drop NaN rows
        mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
        x_arr, y_arr = x_arr[mask], y_arr[mask]
        # base() option sets the spike origin; default 0
        base_val = 0.0
        if "base" in options:
            try:
                base_val = float(options["base"])
            except (ValueError, TypeError):
                pass
        y0_base = np.full_like(x_arr, base_val)

        seg_source = ColumnDataSource({
            "x0": x_arr, "y0": y0_base,
            "x1": x_arr, "y1": y_arr,
        })
        _seg_kwargs: dict = dict(x0="x0", y0="y0", x1="x1", y1="y1",
                                  source=seg_source,
                                  line_color=self.scheme.default_color(color_idx, "scatter"),
                                  line_width=1.5,
                                  legend_label=yvar)
        if view is not None:
            _seg_kwargs["view"] = view
        r = fig.segment(**_seg_kwargs)
        self._apply_line_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    # ------------------------------------------------------------------
    # Phase 1B plot types — computed glyphs
    # ------------------------------------------------------------------

    def map_lfit(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add an OLS linear fit line to *fig*.

        Computes ``y = a + b*x`` using ``numpy.polyfit``.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y (dependent) variable.
            xvar:    Name of the x (independent) variable.
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer for the fit line.
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        # Drop NaN pairs
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        # Need at least 2 points to fit a line
        if len(x) < 2:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
        # Extend x range by Bokeh's default 10% padding on each side so the
        # fit line spans the full visible plot area, not just the data range.
        _dx_lfit = x.max() - x.min() if x.max() > x.min() else 1.0
        x_fit = np.linspace(x.min() - 0.1 * _dx_lfit, x.max() + 0.1 * _dx_lfit, 200)
        y_fit = np.polyval(coeffs, x_fit)

        fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})
        r = fig.line(x="x", y="y", source=fit_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0, line_dash="solid",
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    def map_qfit(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a quadratic fit line to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer for the fit line.
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        # Need at least 3 points for a degree-2 polyfit
        if len(x) < 3:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        coeffs = np.polyfit(x, y, 2)
        # Extend x range by Bokeh's default 10% padding on each side so the
        # fit line spans the full visible plot area, not just the data range.
        _dx_qfit = x.max() - x.min() if x.max() > x.min() else 1.0
        x_fit = np.linspace(x.min() - 0.1 * _dx_qfit, x.max() + 0.1 * _dx_qfit, 200)
        y_fit = np.polyval(coeffs, x_fit)

        fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})
        r = fig.line(x="x", y="y", source=fit_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    def map_lfitci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a linear fit line with a 95% confidence interval band to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            List with [line_renderer, band_renderer].
        """
        from scipy import stats as scipy_stats

        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        n = len(x)

        # Need at least 3 points: df = n-2 must be >= 1, and we need
        # x to vary (non-zero variance) to avoid division by zero in se_fit.
        empty_ci_src = ColumnDataSource({
            "x_fit": [], "y_fit": [], "y_lower": [], "y_upper": []
        })
        _lfitci_color = self.scheme.default_color(color_idx, "line")
        if n < 3 or np.std(x) == 0.0:
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=0.2, fill_color=_lfitci_color
            )
            line_r = fig.line(x="x_fit", y="y_fit", source=empty_ci_src,
                              line_color=_lfitci_color, line_width=2.0,
                              legend_label=yvar)
            return [line_r, band_r]

        slope, intercept, _, _, se = scipy_stats.linregress(x, y)
        # Extend x range by Bokeh's default 10% padding on each side so the
        # fit line spans the full visible plot area, not just the data range.
        _dx_lfitci = x.max() - x.min() if x.max() > x.min() else 1.0
        x_fit = np.linspace(x.min() - 0.1 * _dx_lfitci, x.max() + 0.1 * _dx_lfitci, 200)
        y_fit = intercept + slope * x_fit

        # SE of the fit line at each x_fit point
        x_mean = x.mean()
        x_ss = np.sum((x - x_mean) ** 2)  # guaranteed > 0 after np.std check
        se_fit = se * np.sqrt(
            1 / n + (x_fit - x_mean) ** 2 / x_ss
        ) * np.sqrt(n - 2)
        t_crit = scipy_stats.t.ppf(0.975, df=n - 2)

        y_lower = y_fit - t_crit * se_fit
        y_upper = y_fit + t_crit * se_fit

        ci_source = ColumnDataSource({
            "x_fit": x_fit, "y_fit": y_fit,
            "y_lower": y_lower, "y_upper": y_upper,
        })

        line_r, band_r = self._render_ci_band(
            fig, ci_source, "x_fit", "y_fit", _lfitci_color, yvar, options
        )
        return [line_r, band_r]

    def map_qfitci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a quadratic fit line with a 95% CI band to *fig*.

        Uses a bootstrap approach (500 resamples) to compute the CI band
        because scipy does not provide analytical CIs for polynomial regression.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            List with [line_renderer, band_renderer].
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        # Need at least 3 points for a degree-2 polyfit
        _qfitci_color = self.scheme.default_color(color_idx, "line")
        if len(x) < 3:
            empty_ci_src = ColumnDataSource({
                "x_fit": [], "y_fit": [], "y_lower": [], "y_upper": []
            })
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=0.2, fill_color=_qfitci_color
            )
            line_r = fig.line(x="x_fit", y="y_fit", source=empty_ci_src,
                              line_color=_qfitci_color, line_width=2.0,
                              legend_label=yvar)
            return [line_r, band_r]

        coeffs = np.polyfit(x, y, 2)
        # Extend x range by Bokeh's default 10% padding on each side so the
        # fit line spans the full visible plot area, not just the data range.
        _dx_qfitci = x.max() - x.min() if x.max() > x.min() else 1.0
        x_fit = np.linspace(x.min() - 0.1 * _dx_qfitci, x.max() + 0.1 * _dx_qfitci, 200)
        y_fit = np.polyval(coeffs, x_fit)

        # Bootstrap CI
        def _qfit_fn(xi: "np.ndarray", yi: "np.ndarray", xg: "np.ndarray") -> "np.ndarray":
            return np.polyval(np.polyfit(xi, yi, 2), xg)

        y_lower, y_upper = GlyphMapper._bootstrap_ci(
            x, y, x_fit, _qfit_fn, n_boot=500, fallback=y_fit
        )

        ci_source = ColumnDataSource({
            "x_fit": x_fit, "y_fit": y_fit,
            "y_lower": y_lower, "y_upper": y_upper,
        })
        line_r, band_r = self._render_ci_band(
            fig, ci_source, "x_fit", "y_fit", _qfitci_color, yvar, options
        )
        return [line_r, band_r]

    def map_lowess(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a LOWESS smoothed line to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer for the LOWESS line.
        """
        from statsmodels.nonparametric.smoothers_lowess import lowess

        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        # Need at least 2 points for lowess, and x must vary
        if len(x) < 2 or np.std(x) == 0.0:
            empty = ColumnDataSource({"x_lw": [], "y_lw": []})
            return fig.line(x="x_lw", y="y_lw", source=empty)

        # Default bandwidth: 0.8 (same as Stata's default)
        bw = float(options.get("bwidth", "0.8"))
        smoothed = lowess(y, x, frac=bw, return_sorted=True)

        lw_source = ColumnDataSource({
            "x_lw": smoothed[:, 0],
            "y_lw": smoothed[:, 1],
        })
        r = fig.line(x="x_lw", y="y_lw", source=lw_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    # ------------------------------------------------------------------
    # Local polynomial smoother (lpoly / lpolyci)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_lpoly_fit(
        x: "np.ndarray",
        y: "np.ndarray",
        bwidth: float = 0.5,
        degree: int = 0,
        n_grid: int = 200,
    ) -> "tuple[np.ndarray, np.ndarray]":
        """Kernel-weighted local polynomial regression.

        Implements Nadaraya–Watson (degree=0) or local-linear (degree=1)
        regression using a Gaussian kernel.  For higher degrees the weights
        are passed to a least-squares polynomial fit at each grid point.

        Args:
            x, y:    Cleaned (no NaN) paired arrays.
            bwidth:  Bandwidth as a fraction of ``x``'s range (0 < bwidth ≤ 1).
            degree:  Polynomial degree (0 = kernel smoother, 1 = local linear,
                     2 = local quadratic).
            n_grid:  Number of evaluation points on the x-grid.

        Returns:
            ``(x_grid, y_fit)`` — 1-D arrays of length *n_grid*.
        """
        x_min, x_max = x.min(), x.max()
        x_range = x_max - x_min or 1.0
        h = bwidth * x_range  # bandwidth in data units

        x_grid = np.linspace(x_min, x_max, n_grid)
        y_fit = np.empty(n_grid)

        for i, x0 in enumerate(x_grid):
            # Gaussian kernel weights
            w = np.exp(-0.5 * ((x - x0) / h) ** 2)
            w_sum = w.sum()
            if w_sum < 1e-12:
                y_fit[i] = np.nan
                continue
            if degree == 0:
                y_fit[i] = np.dot(w, y) / w_sum
            else:
                # Weighted polynomial fit of given degree
                try:
                    coeffs = np.polyfit(x, y, deg=degree, w=w)
                    y_fit[i] = np.polyval(coeffs, x0)
                except (np.linalg.LinAlgError, ValueError):
                    y_fit[i] = np.dot(w, y) / w_sum

        return x_grid, y_fit

    def map_lpoly(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: "dict[str, str]",
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add a local polynomial regression smoother to *fig*.

        Implements Nadaraya–Watson kernel regression (``degree(0)``) or
        local-linear / local-polynomial smoothing (``degree(1)``, ``degree(2)``).
        Mirrors Stata's ``twoway lpoly`` with ``bwidth()`` and ``degree()``
        sub-options.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Plot-level options; supports ``bwidth`` (default 0.5) and
                     ``degree`` (default 0).

        Returns:
            GlyphRenderer for the smoother line.
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        if len(x) < 2:
            empty = ColumnDataSource({"x_lp": [], "y_lp": []})
            return fig.line(x="x_lp", y="y_lp", source=empty)

        bwidth = 0.5
        try:
            bwidth = max(0.01, min(1.0, float(options.get("bwidth", "0.5"))))
        except (ValueError, TypeError):
            pass

        degree = 0
        try:
            degree = max(0, min(3, int(options.get("degree", "0"))))
        except (ValueError, TypeError):
            pass

        x_grid, y_fit = self._compute_lpoly_fit(x, y, bwidth=bwidth,
                                                 degree=degree)
        valid = ~np.isnan(y_fit)
        lp_src = ColumnDataSource({
            "x_lp": x_grid[valid].tolist(),
            "y_lp": y_fit[valid].tolist(),
        })
        r = fig.line(x="x_lp", y="y_lp", source=lp_src,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    def map_lpolyci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: "dict[str, str]",
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a local polynomial smoother with a bootstrap 95% CI band to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Plot-level options; supports ``bwidth`` and ``degree``.

        Returns:
            List with [line_renderer, band_renderer].
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        _lpolyci_color = self.scheme.default_color(color_idx, "line")
        empty_src = ColumnDataSource({
            "x_lp": [], "y_lp": [], "y_lower": [], "y_upper": []
        })
        if len(x) < 3:
            band_r = fig.varea(
                x="x_lp", y1="y_lower", y2="y_upper",
                source=empty_src, fill_alpha=0.2, fill_color=_lpolyci_color,
            )
            line_r = fig.line(x="x_lp", y="y_lp", source=empty_src,
                              line_color=_lpolyci_color, line_width=2.0,
                              legend_label=yvar)
            return [line_r, band_r]

        bwidth = 0.5
        try:
            bwidth = max(0.01, min(1.0, float(options.get("bwidth", "0.5"))))
        except (ValueError, TypeError):
            pass

        degree = 0
        try:
            degree = max(0, min(3, int(options.get("degree", "0"))))
        except (ValueError, TypeError):
            pass

        n_grid = 100  # coarser grid for speed
        x_grid, y_fit = self._compute_lpoly_fit(x, y, bwidth=bwidth,
                                                 degree=degree, n_grid=n_grid)

        # Bootstrap CI (200 resamples for speed)
        def _lpoly_fn(xi: "np.ndarray", yi: "np.ndarray", _xg: "np.ndarray") -> "np.ndarray":
            _, yb = self._compute_lpoly_fit(xi, yi, bwidth=bwidth,
                                            degree=degree, n_grid=n_grid)
            return yb  # NaN entries are replaced by fallback in _bootstrap_ci

        y_lower, y_upper = GlyphMapper._bootstrap_ci(
            x, y, x_grid, _lpoly_fn, n_boot=200, fallback=y_fit
        )

        valid = ~np.isnan(y_fit)
        ci_src = ColumnDataSource({
            "x_lp":    x_grid[valid].tolist(),
            "y_lp":    y_fit[valid].tolist(),
            "y_lower": y_lower[valid].tolist(),
            "y_upper": y_upper[valid].tolist(),
        })
        line_r, band_r = self._render_ci_band(
            fig, ci_src, "x_lp", "y_lp", _lpolyci_color, yvar, options
        )
        return [line_r, band_r]

    # ------------------------------------------------------------------
    # Fractional polynomial fit (fpfit / fpfitci)
    # ------------------------------------------------------------------

    # Standard FP powers used by Stata (Royston & Altman, 1994)
    _FP_POWERS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)

    @staticmethod
    def _fp_transform(x: "np.ndarray", p: float) -> "np.ndarray":
        """Apply a single FP transformation: x^p (p==0 → ln x)."""
        with np.errstate(divide="ignore", invalid="ignore"):
            if p == 0.0:
                result = np.where(x > 0, np.log(x), np.nan)
            else:
                result = np.where(x > 0, np.power(x.astype(float), p), np.nan)
        return result

    @classmethod
    def _fit_fp2(
        cls,
        x: "np.ndarray",
        y: "np.ndarray",
    ) -> "tuple[float, float, np.ndarray]":
        """Fit a degree-2 fractional polynomial to (x, y).

        Tries all unique pairs of powers from ``_FP_POWERS`` and returns the
        pair (p1, p2) that minimises the residual sum of squares, together
        with the fitted OLS coefficient vector.

        Returns:
            ``(p1, p2, coeffs)`` where *coeffs* is [beta0, beta1, beta2] for
            the model ``y = beta0 + beta1*f(x,p1) + beta2*f(x,p2)``.
        """
        from itertools import combinations_with_replacement

        best_rss = np.inf
        best_p1, best_p2 = 1.0, 2.0
        best_coeffs = np.array([y.mean(), 0.0, 0.0])

        pairs = list(combinations_with_replacement(cls._FP_POWERS, 2))
        for p1, p2 in pairs:
            z1 = cls._fp_transform(x, p1)
            z2 = cls._fp_transform(x, p2)
            valid = ~(np.isnan(z1) | np.isnan(z2) | np.isnan(y))
            if valid.sum() < 4:
                continue
            X = np.column_stack([np.ones(valid.sum()), z1[valid], z2[valid]])
            try:
                coeffs, _, _, _ = np.linalg.lstsq(X, y[valid], rcond=None)
                y_pred = X @ coeffs
                rss = float(np.sum((y[valid] - y_pred) ** 2))
                if rss < best_rss:
                    best_rss = rss
                    best_p1, best_p2 = p1, p2
                    best_coeffs = coeffs
            except np.linalg.LinAlgError:
                continue

        return best_p1, best_p2, best_coeffs

    @classmethod
    def _predict_fp2(
        cls,
        x_grid: "np.ndarray",
        p1: float,
        p2: float,
        coeffs: "np.ndarray",
    ) -> "np.ndarray":
        """Evaluate the degree-2 FP model on *x_grid*."""
        z1 = cls._fp_transform(x_grid, p1)
        z2 = cls._fp_transform(x_grid, p2)
        return coeffs[0] + coeffs[1] * z1 + coeffs[2] * z2

    def map_fpfit(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: "dict[str, str]",
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add a fractional polynomial fit line to *fig*.

        Fits a degree-2 FP model (Royston & Altman, 1994) by selecting the
        pair of powers from {−2, −1, −0.5, 0, 0.5, 1, 2, 3} that minimises
        the residual sum of squares.  Mirrors Stata's ``twoway fpfit``.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Plot-level options dict.

        Returns:
            GlyphRenderer for the FP fit line.
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        if len(x) < 4:
            empty = ColumnDataSource({"x_fp": [], "y_fp": []})
            return fig.line(x="x_fp", y="y_fp", source=empty)

        p1, p2, coeffs = self._fit_fp2(x, y)
        # Restrict grid to positive x (FP requires x > 0)
        x_min = max(x[x > 0].min() if (x > 0).any() else 1e-6,
                    float(np.percentile(x, 1)))
        x_max = float(np.percentile(x, 99))
        x_grid = np.linspace(x_min, x_max, 200)
        y_fit = self._predict_fp2(x_grid, p1, p2, coeffs)

        valid = ~np.isnan(y_fit)
        fp_src = ColumnDataSource({
            "x_fp": x_grid[valid].tolist(),
            "y_fp": y_fit[valid].tolist(),
        })
        r = fig.line(x="x_fp", y="y_fp", source=fp_src,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    def map_fpfitci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: "dict[str, str]",
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a fractional polynomial fit with a bootstrap 95% CI band to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Plot-level options dict.

        Returns:
            List with [line_renderer, band_renderer].
        """
        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        _fpfitci_color = self.scheme.default_color(color_idx, "line")
        empty_src = ColumnDataSource({
            "x_fp": [], "y_fp": [], "y_lower": [], "y_upper": []
        })
        if len(x) < 4:
            band_r = fig.varea(
                x="x_fp", y1="y_lower", y2="y_upper",
                source=empty_src, fill_alpha=0.2, fill_color=_fpfitci_color,
            )
            line_r = fig.line(x="x_fp", y="y_fp", source=empty_src,
                              line_color=_fpfitci_color, line_width=2.0,
                              legend_label=yvar)
            return [line_r, band_r]

        p1, p2, coeffs = self._fit_fp2(x, y)
        x_pos = x[x > 0]
        x_min = float(max(x_pos.min() if len(x_pos) else 1e-6,
                          np.percentile(x, 1)))
        x_max = float(np.percentile(x, 99))
        x_grid = np.linspace(x_min, x_max, 150)
        y_fit = self._predict_fp2(x_grid, p1, p2, coeffs)

        def _fp_fn(xi: "np.ndarray", yi: "np.ndarray", xg: "np.ndarray") -> "np.ndarray":
            bp1, bp2, bc = self._fit_fp2(xi, yi)
            return self._predict_fp2(xg, bp1, bp2, bc)

        valid = ~np.isnan(y_fit)
        y_lower, y_upper = GlyphMapper._bootstrap_ci(
            x, y, x_grid, _fp_fn, n_boot=200, fallback=y_fit
        )

        ci_src = ColumnDataSource({
            "x_fp":    x_grid[valid].tolist(),
            "y_fp":    y_fit[valid].tolist(),
            "y_lower": y_lower[valid].tolist(),
            "y_upper": y_upper[valid].tolist(),
        })
        line_r, band_r = self._render_ci_band(
            fig, ci_src, "x_fp", "y_fp", _fpfitci_color, yvar, options
        )
        return [line_r, band_r]

    def map_histogram(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        options: "dict[str, str] | None" = None,
        xvar: "str | None" = None,
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add histogram quad glyphs to *fig*.

        Note: for histograms only one variable (yvar) is binned.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the variable being binned.
            options: Translated plot-level options dict (supports "bin" key).
            xvar:    Ignored; accepted for compatibility with internal dispatch.

        Returns:
            The single Quad GlyphRenderer created.
        """
        if options is None:
            options = {}
        if self._is_empty(source, yvar):
            empty_src = ColumnDataSource({"top": [], "left": [], "right": []})
            return fig.quad(top="top", bottom=0, left="left", right="right",
                            source=empty_src)
        arr = _extract_finite(source, yvar)

        # Cap bin count to prevent resource exhaustion from huge values
        _MAX_BINS = 1000
        n_bins = min(int(options.get("bin", 10)), _MAX_BINS)
        n_bins = max(n_bins, 1)  # Must be at least 1
        counts, edges = np.histogram(arr, bins=n_bins)

        hist_source = ColumnDataSource({
            "top":   counts,
            "left":  edges[:-1],
            "right": edges[1:],
        })
        r = fig.quad(top="top", bottom=0, left="left", right="right",
                     source=hist_source,
                     fill_color=self.scheme.default_color(color_idx, "histogram"),
                     line_color="white",
                     fill_alpha=0.8, legend_label=yvar)
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
            except ValueError:
                pass
        self._apply_fill_opts(r, options)
        # Quad supports line_width/line_dash/line_color for bin border styling
        self._apply_line_opts(r, options)
        # Tag renderer so DashRenderer can wire filter-callback recomputation.
        r._dash_agg_source = hist_source
        r._dash_agg_config = {
            "type":      "histogram",
            "varname":   yvar,
            "bin_edges": edges.tolist(),
        }
        return r

    def map_kdensity(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        options: "dict[str, str] | None" = None,
        xvar: "str | None" = None,
        view=None,
        color_idx: int = 0,
    ) -> "GlyphRenderer":
        """Add a kernel density estimate line to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the variable for which density is estimated.
            options: Translated plot-level options dict.
            xvar:    Ignored; accepted for compatibility with internal dispatch.

        Returns:
            The single GlyphRenderer for the density line.
        """
        from scipy.stats import gaussian_kde

        if options is None:
            options = {}
        arr = _extract_finite(source, yvar)

        # gaussian_kde requires at least 2 points and non-constant data
        if len(arr) < 2 or np.std(arr) == 0.0:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        kde = gaussian_kde(arr)
        # Extend range beyond data min/max to capture distribution tails
        bw = kde.covariance_factor() * arr.std()
        x_range = np.linspace(arr.min() - 3 * bw, arr.max() + 3 * bw, 400)
        density = kde(x_range)

        kd_source = ColumnDataSource({"x": x_range, "y": density})
        r = fig.line(x="x", y="y", source=kd_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        # Tag renderer so DashRenderer can wire filter-callback recomputation.
        # Store the x grid so JS recomputes density at the same points, keeping
        # the axis range stable.  Bandwidth stored for reference; JS uses
        # Silverman's rule on the filtered subset (consistent approximation).
        r._dash_agg_source = kd_source
        r._dash_agg_config = {
            "type":    "kdensity",
            "varname": yvar,
            "x_grid":  x_range.tolist(),
        }
        return r

    # ------------------------------------------------------------------
    # Phase 2 range plot types
    # ------------------------------------------------------------------

    def map_rarea(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a range area glyph (filled between y1 and y2) to *fig*.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Lower boundary variable.
            y2var:  Upper boundary variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single VArea GlyphRenderer.
        """
        if self._is_empty(source, xvar, y1var, y2var):
            empty_src = ColumnDataSource({xvar: [], y1var: [], y2var: []})
            return [fig.varea(x=xvar, y1=y1var, y2=y2var, source=empty_src)]
        _varea_kwargs: dict = dict(x=xvar, y1=y1var, y2=y2var, source=source,
                                    fill_color=self.scheme.default_color(color_idx, "area"),
                                    fill_alpha=0.5,
                                    legend_label=y1var)
        if view is not None:
            _varea_kwargs["view"] = view
        r = fig.varea(**_varea_kwargs)
        self._apply_fill_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [r]

    def map_rbar(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range bar glyphs (bars from y1 to y2) to *fig*.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Bottom boundary variable.
            y2var:  Top boundary variable.
            xvar:   x-axis (bar centre) variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single VBar GlyphRenderer.
        """
        if self._is_empty(source, xvar, y1var, y2var):
            empty_src = ColumnDataSource({xvar: [], y1var: [], y2var: []})
            return [fig.vbar(x=xvar, top=y2var, bottom=y1var, width=0.8, source=empty_src)]
        x_vals = sorted(set(float(v) for v in source.data[xvar]
                            if not math.isnan(float(v))))
        bar_width = 0.8 * min(
            (x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)),
            default=0.8,
        )
        _rbar_kwargs: dict = dict(x=xvar, bottom=y1var, top=y2var, source=source,
                                   width=bar_width,
                                   fill_color=self.scheme.default_color(color_idx, "bar"),
                                   line_alpha=0,
                                   legend_label=y1var)
        if view is not None:
            _rbar_kwargs["view"] = view
        r = fig.vbar(**_rbar_kwargs)
        self._apply_fill_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [r]

    def map_rspike(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range spike glyphs (segments from y1 to y2) to *fig*.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Start y variable.
            y2var:  End y variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single Segment GlyphRenderer.
        """
        if self._is_empty(source, xvar, y1var, y2var):
            empty_src = ColumnDataSource({xvar: [], y1var: [], y2var: []})
            return [fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var, source=empty_src)]
        _rseg_kwargs: dict = dict(x0=xvar, y0=y1var, x1=xvar, y1=y2var, source=source,
                                   line_color=self.scheme.default_color(color_idx, "scatter"),
                                   line_width=1.5,
                                   legend_label=y1var)
        if view is not None:
            _rseg_kwargs["view"] = view
        r = fig.segment(**_rseg_kwargs)
        self._apply_line_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [r]

    def map_rcap(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range cap glyphs (segments + horizontal caps) to *fig*.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Bottom cap position variable.
            y2var:  Top cap position variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List with [spine_renderer, bottom_cap_renderer, top_cap_renderer].
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y1_arr = np.array(source.data[y1var], dtype=float)
        y2_arr = np.array(source.data[y2var], dtype=float)

        # Estimate cap half-width from x spacing
        x_sorted = np.sort(x_arr[~np.isnan(x_arr)])
        if len(x_sorted) >= 2:
            cap_hw = 0.2 * np.min(np.diff(x_sorted))
        else:
            cap_hw = 0.2

        _x0_col = f"{xvar}_x0_cap"
        _x1_col = f"{xvar}_x1_cap"
        cap_source = ColumnDataSource({
            xvar: x_arr, y1var: y1_arr, y2var: y2_arr,
            _x0_col: x_arr - cap_hw, _x1_col: x_arr + cap_hw,
        })

        _rcap_color = self.scheme.default_color(color_idx, "scatter")
        _spine_kwargs: dict = dict(x0=xvar, y0=y1var, x1=xvar, y1=y2var,
                                    source=cap_source,
                                    line_color=_rcap_color, line_width=1.5,
                                    legend_label=y1var)
        _bot_kwargs: dict = dict(x0=_x0_col, y0=y1var, x1=_x1_col, y1=y1var,
                                  source=cap_source,
                                  line_color=_rcap_color, line_width=1.5)
        _top_kwargs: dict = dict(x0=_x0_col, y0=y2var, x1=_x1_col, y1=y2var,
                                  source=cap_source,
                                  line_color=_rcap_color, line_width=1.5)
        if view is not None:
            _spine_kwargs["view"] = view
            _bot_kwargs["view"] = view
            _top_kwargs["view"] = view
        spine = fig.segment(**_spine_kwargs)
        bot_cap = fig.segment(**_bot_kwargs)
        top_cap = fig.segment(**_top_kwargs)
        for seg in (spine, bot_cap, top_cap):
            self._apply_line_opts(seg, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [spine, bot_cap, top_cap]

    def map_rline(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add two connected range lines (lower and upper boundaries) to *fig*.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Lower boundary variable.
            y2var:  Upper boundary variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List with [lower_line_renderer, upper_line_renderer].
        """
        _rl1_kwargs: dict = dict(x=xvar, y=y1var, source=source,
                                  line_color=self.scheme.default_color(color_idx, "line"),
                                  line_width=1.5,
                                  legend_label=y1var)
        _rl2_kwargs: dict = dict(x=xvar, y=y2var, source=source,
                                  line_color=self.scheme.default_color(color_idx + 1, "line"),
                                  line_width=1.5)
        if view is not None:
            _rl1_kwargs["view"] = view
            _rl2_kwargs["view"] = view
        r1 = fig.line(**_rl1_kwargs)
        r2 = fig.line(**_rl2_kwargs)
        self._apply_line_opts(r1, options)
        self._apply_line_opts(r2, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [r1, r2]

    def map_rconnected(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range connected (lines + scatter) glyphs for two boundaries.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Lower boundary variable.
            y2var:  Upper boundary variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List of four renderers [lower_line, lower_scatter, upper_line, upper_scatter].
        """
        return [
            self.map_line(fig, source, y1var, xvar, options, view=view, color_idx=color_idx),
            self.map_scatter(fig, source, y1var, xvar, options, view=view, color_idx=color_idx),
            self.map_line(fig, source, y2var, xvar, options, view=view, color_idx=color_idx + 1),
            self.map_scatter(fig, source, y2var, xvar, options, view=view, color_idx=color_idx + 1),
        ]

    def map_dot(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add dot plot glyphs to *fig*.

        A dot plot in Stata is a scatter plot where the y-axis is categorical
        and dots are stacked horizontally.  This implementation renders a
        standard scatter with the y-variable mapped to the y-axis, which
        approximates the visual output for continuous y values.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable (categorical/grouping variable).
            options: Translated plot-level options dict.

        Returns:
            List containing the single scatter GlyphRenderer.
        """
        return self.map_scatter(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)

    # ------------------------------------------------------------------
    # Phase 3 additional plot types
    # ------------------------------------------------------------------

    def map_dropline(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add dropline glyphs to *fig*: vertical segments from y=0 to y=yvar plus dots.

        Each observation is drawn as a vertical line dropping from the data
        point down to y=0, with a filled circle at the top of each line.
        This is Stata's ``twoway dropline`` appearance.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable (top of each drop).
            xvar:    Name of the x variable (horizontal position).
            options: Translated plot-level options dict.

        Returns:
            List with [segment_renderer, scatter_renderer].
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y_arr = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
        x_arr, y_arr = x_arr[mask], y_arr[mask]
        zeros = np.zeros_like(x_arr)

        # Apply jitter if requested (jitters x and y)
        x_plot, y_plot = _apply_jitter(
            x_arr, y_arr,
            float(options.get("jitter", 0) or 0),
            int(float(options["jseed"])) if "jseed" in options else None,
        ) if options.get("jitter") else (x_arr, y_arr)

        dl_source = ColumnDataSource({
            "x": x_plot, "y": y_plot, "y0": zeros,
            xvar: x_arr, yvar: y_arr,
        })
        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        _dl_seg_kwargs: dict = dict(x0="x", y0="y0", x1="x", y1="y",
                                     source=dl_source, line_color=color, line_width=1.5)
        _dl_dot_kwargs: dict = dict(x="x", y="y", source=dl_source,
                                     fill_color=color, line_color=color, size=8,
                                     legend_label=yvar)
        if view is not None:
            _dl_seg_kwargs["view"] = view
            _dl_dot_kwargs["view"] = view
        seg = fig.segment(**_dl_seg_kwargs)
        dot = fig.scatter(**_dl_dot_kwargs)
        self._apply_line_opts(seg, options)
        self._apply_mlabel_opts(fig, dl_source, options, xvar, yvar)
        return [seg, dot]

    def map_rcapsym(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range cap-with-symbol glyphs to *fig*.

        Identical to ``rcap`` (vertical spine with horizontal end caps) but
        with scatter marker symbols placed at both cap positions, matching
        Stata's ``twoway rcapsym`` appearance.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Bottom cap position variable.
            y2var:  Top cap position variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List of five renderers:
            [spine, bot_cap, top_cap, bot_scatter, top_scatter].
        """
        x_arr  = np.array(source.data[xvar],  dtype=float)
        y1_arr = np.array(source.data[y1var], dtype=float)
        y2_arr = np.array(source.data[y2var], dtype=float)

        x_sorted = np.sort(x_arr[~np.isnan(x_arr)])
        if len(x_sorted) >= 2:
            cap_hw = 0.2 * float(np.min(np.diff(x_sorted)))
        else:
            cap_hw = 0.2

        cap_source = ColumnDataSource({
            "x": x_arr, "y1": y1_arr, "y2": y2_arr,
            "x0_cap": x_arr - cap_hw, "x1_cap": x_arr + cap_hw,
        })

        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        _rcs_spine_kw: dict = dict(x0="x",     y0="y1",  x1="x",     y1="y2",
                                    source=cap_source, line_color=color, line_width=1.5,
                                    legend_label=y1var)
        _rcs_bcap_kw: dict  = dict(x0="x0_cap", y0="y1", x1="x1_cap", y1="y1",
                                    source=cap_source, line_color=color, line_width=1.5)
        _rcs_tcap_kw: dict  = dict(x0="x0_cap", y0="y2", x1="x1_cap", y1="y2",
                                    source=cap_source, line_color=color, line_width=1.5)
        _rcs_bdot_kw: dict  = dict(x="x", y="y1", source=cap_source,
                                    fill_color=color, line_color=color, size=7)
        _rcs_tdot_kw: dict  = dict(x="x", y="y2", source=cap_source,
                                    fill_color=color, line_color=color, size=7)
        if view is not None:
            for _kw in (_rcs_spine_kw, _rcs_bcap_kw, _rcs_tcap_kw, _rcs_bdot_kw, _rcs_tdot_kw):
                _kw["view"] = view
        spine   = fig.segment(**_rcs_spine_kw)
        bot_cap = fig.segment(**_rcs_bcap_kw)
        top_cap = fig.segment(**_rcs_tcap_kw)
        bot_dot = fig.scatter(**_rcs_bdot_kw)
        top_dot = fig.scatter(**_rcs_tdot_kw)
        for seg in (spine, bot_cap, top_cap):
            self._apply_line_opts(seg, options)
        for dot in (bot_dot, top_dot):
            self._apply_marker_opts(dot, options)
        self._apply_mlabel_opts(fig, source, options, xvar, y2var)
        return [spine, bot_cap, top_cap, bot_dot, top_dot]

    def map_scatteri(
        self,
        fig: Any,
        values: list,
        options: dict[str, str],
        color_idx: int = 0,
    ) -> list:
        """Add scatter glyphs from inline literal coordinate pairs to *fig*.

        ``scatteri`` plots fixed (y, x) coordinate pairs specified as
        literals in the command rather than as variable names.  This method
        builds an independent ColumnDataSource from the supplied list.

        Args:
            fig:     Bokeh Figure object.
            values:  List of [y, x] numeric pairs (from JSON ``"values"`` key).
            options: Translated plot-level options dict.

        Returns:
            List with the single scatter GlyphRenderer.
        """
        if not values:
            empty = ColumnDataSource({"x": [], "y": []})
            return [fig.scatter(x="x", y="y", source=empty)]

        y_vals = np.array([float(pair[0]) for pair in values])
        x_vals = np.array([float(pair[1]) for pair in values])

        # Apply jitter if requested
        jitter_raw = options.get("jitter", "")
        if jitter_raw:
            try:
                jitter_pct = float(jitter_raw)
            except (ValueError, TypeError):
                jitter_pct = 0.0
            if jitter_pct > 0:
                seed_raw = options.get("jseed", "")
                seed_val: int | None = None
                if seed_raw:
                    try:
                        seed_val = int(float(seed_raw))
                    except (ValueError, TypeError):
                        pass
                x_vals, y_vals = _apply_jitter(x_vals, y_vals, jitter_pct, seed_val)

        si_source = ColumnDataSource({"x": x_vals.tolist(), "y": y_vals.tolist()})

        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        size = self.tr.translate_msize(options.get("msize", "medium"))
        marker = self.tr.translate_msymbol(options.get("msymbol", "circle"))

        r = fig.scatter(x="x", y="y", source=si_source,
                        marker=marker, size=size,
                        fill_color=color, line_color=color)
        return [r]

    # ------------------------------------------------------------------
    # Phase 4 plot types
    # ------------------------------------------------------------------

    def map_pcspike(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add paired-coordinate spike glyphs (segments from (x1,y1) to (x2,y2)) to *fig*.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            y1var:   Name of the start y variable.
            x1var:   Name of the start x variable.
            y2var:   Name of the end y variable.
            x2var:   Name of the end x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single Segment GlyphRenderer.
        """
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        }).dropna()
        source_clean = ColumnDataSource(clean)
        _pcseg_kwargs: dict = dict(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                                    source=source_clean,
                                    line_color=self.scheme.default_color(color_idx, "scatter"),
                                    line_width=1.5,
                                    legend_label=y1var)
        if view is not None:
            _pcseg_kwargs["view"] = view
        r = fig.segment(**_pcseg_kwargs)
        self._apply_line_opts(r, options)
        return [r]

    def map_pci(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add paired-coordinate line segments to *fig*.

        ``twoway pci`` draws a straight line from ``(x1var, y1var)`` to
        ``(x2var, y2var)`` for each observation.  Implemented identically to
        :meth:`map_pcspike` — both use Bokeh ``Segment`` glyphs.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            y1var:   Name of the start y variable.
            x1var:   Name of the start x variable.
            y2var:   Name of the end y variable.
            x2var:   Name of the end x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single Segment GlyphRenderer.
        """
        return self.map_pcspike(fig, source, y1var, x1var, y2var, x2var, options, view=view, color_idx=color_idx)

    def map_pcscatter(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add paired-coordinate scatter glyphs to *fig*.

        ``twoway pcscatter`` places a scatter marker at each of the two
        endpoints ``(x1var, y1var)`` and ``(x2var, y2var)`` per observation.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            y1var:   Name of the start y variable.
            x1var:   Name of the start x variable.
            y2var:   Name of the end y variable.
            x2var:   Name of the end x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single scatter GlyphRenderer.
        """
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        }).dropna()

        # Concatenate both endpoint sets into one scatter source
        x_all = np.concatenate([clean[x1var].values, clean[x2var].values])
        y_all = np.concatenate([clean[y1var].values, clean[y2var].values])
        pc_source = ColumnDataSource({"x": x_all.tolist(), "y": y_all.tolist()})

        _pcsc_kwargs: dict = dict(source=pc_source,
                                   size=8, color=self.scheme.default_color(color_idx, "scatter"),
                                   legend_label=y1var)
        if view is not None:
            _pcsc_kwargs["view"] = view
        r = fig.scatter("x", "y", **_pcsc_kwargs)
        self._apply_marker_opts(r, options)
        return [r]

    def map_pcarrow(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add paired-coordinate arrow glyphs (segments + arrowheads) to *fig*.

        Each observation draws a directed Arrow from (x1var, y1var) to
        (x2var, y2var) using Bokeh's Arrow annotation with an OpenHead.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            y1var:   Name of the start y variable.
            x1var:   Name of the start x variable.
            y2var:   Name of the end y variable.
            x2var:   Name of the end x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the segment GlyphRenderer (Arrow annotations are layout objects).
        """
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        }).dropna()
        pc_source = ColumnDataSource(clean)

        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "lcolor" in options:
                color = self.tr.translate_lcolor(options["lcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        _pca_seg_kwargs: dict = dict(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                                      source=pc_source, line_color=color, line_width=1.5,
                                      legend_label=y1var)
        if view is not None:
            _pca_seg_kwargs["view"] = view
        seg = fig.segment(**_pca_seg_kwargs)
        self._apply_line_opts(seg, options)

        # Resolve line_width for Arrow annotations (same value as segment after opts applied)
        arrow_lw = seg.glyph.line_width

        # Add Arrow head annotations for each row
        for _, row in clean.iterrows():
            arrow = Arrow(
                end=OpenHead(size=10, line_color=color),
                x_start=float(row[x1var]),
                y_start=float(row[y1var]),
                x_end=float(row[x2var]),
                y_end=float(row[y2var]),
                line_color=color,
                line_width=arrow_lw,
            )
            fig.add_layout(arrow)

        return [seg]

    def map_pcbarrow(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add paired-coordinate bidirectional arrow glyphs to *fig*.

        Each observation draws a bidirectional Arrow from (x1var, y1var) to
        (x2var, y2var) using Bokeh's Arrow annotation with NormalHead on both ends.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            y1var:   Name of the start y variable.
            x1var:   Name of the start x variable.
            y2var:   Name of the end y variable.
            x2var:   Name of the end x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the segment GlyphRenderer (Arrow annotations are layout objects).
        """
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        }).dropna()
        pc_source = ColumnDataSource(clean)

        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "lcolor" in options:
                color = self.tr.translate_lcolor(options["lcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        _pcb_seg_kwargs: dict = dict(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                                      source=pc_source, line_color=color, line_width=1.5,
                                      legend_label=y1var)
        if view is not None:
            _pcb_seg_kwargs["view"] = view
        seg = fig.segment(**_pcb_seg_kwargs)
        self._apply_line_opts(seg, options)

        # Resolve line_width for Arrow annotations (same value as segment after opts applied)
        arrow_lw = seg.glyph.line_width

        # Add bidirectional Arrow annotations for each row
        for _, row in clean.iterrows():
            arrow = Arrow(
                end=NormalHead(size=10, line_color=color),
                start=NormalHead(size=10, line_color=color),
                x_start=float(row[x1var]),
                y_start=float(row[y1var]),
                x_end=float(row[x2var]),
                y_end=float(row[y2var]),
                line_color=color,
                line_width=arrow_lw,
            )
            fig.add_layout(arrow)

        return [seg]

    def map_tsline(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a time-series line glyph to *fig*.

        Delegates directly to ``map_line``.  Provided as a named alias so
        Stata's ``twoway tsline`` syntax is explicitly supported.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x (time) variable.
            options: Translated plot-level options dict.

        Returns:
            The result of ``map_line``.
        """
        return self.map_line(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)

    def map_tsrline(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add time-series range lines to *fig*.

        Delegates directly to ``map_rline``.  Provided as a named alias so
        Stata's ``twoway tsrline`` syntax is explicitly supported.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Lower boundary variable.
            y2var:  Upper boundary variable.
            xvar:   x (time) axis variable.
            options: Translated plot-level options dict.

        Returns:
            The result of ``map_rline``.
        """
        return self.map_rline(fig, source, y1var, y2var, xvar, options, view=view, color_idx=color_idx)

    def map_rscatter(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add range scatter glyphs to *fig*.

        ``twoway rscatter`` places a scatter marker at ``(xvar, y1var)`` and a
        second marker at ``(xvar, y2var)`` for each observation — the range
        equivalent of ``scatter``.

        Args:
            fig:    Bokeh Figure object.
            source: Shared ColumnDataSource.
            y1var:  Lower y-boundary variable.
            y2var:  Upper y-boundary variable.
            xvar:   x-axis variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single scatter GlyphRenderer.
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y1_arr = np.array(source.data[y1var], dtype=float)
        y2_arr = np.array(source.data[y2var], dtype=float)

        # Interleave both y-boundary points at the same x
        x_all = np.concatenate([x_arr, x_arr])
        y_all = np.concatenate([y1_arr, y2_arr])
        mask = ~(np.isnan(x_all) | np.isnan(y_all))

        rs_source = ColumnDataSource({
            "x": x_all[mask].tolist(),
            "y": y_all[mask].tolist(),
        })
        _rs_kwargs: dict = dict(source=rs_source,
                                 size=8, color=self.scheme.default_color(color_idx, "scatter"),
                                 legend_label=y1var)
        if view is not None:
            _rs_kwargs["view"] = view
        r = fig.scatter("x", "y", **_rs_kwargs)
        self._apply_marker_opts(r, options)
        return [r]

    def map_mspline(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a monotone cubic spline (PCHIP) line to *fig*.

        Uses ``scipy.interpolate.PchipInterpolator`` to fit a smooth
        monotone cubic spline through the data points, evaluated on a
        200-point grid spanning the data range.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single GlyphRenderer for the spline line.
        """
        from scipy.interpolate import PchipInterpolator

        x_arr = np.array(source.data[xvar], dtype=float)
        y_arr = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
        x_clean = x_arr[mask]
        y_clean = y_arr[mask]

        # Sort by x
        order = np.argsort(x_clean)
        x_clean = x_clean[order]
        y_clean = y_clean[order]

        # Deduplicate x values — PchipInterpolator requires strictly increasing x.
        # For duplicate x values take the mean y to produce a single representative point.
        unique_x, inv = np.unique(x_clean, return_inverse=True)
        if len(unique_x) < len(x_clean):
            y_agg = np.zeros(len(unique_x))
            counts = np.zeros(len(unique_x))
            for i, j in enumerate(inv):
                y_agg[j] += y_clean[i]
                counts[j] += 1
            x_clean = unique_x
            y_clean = y_agg / counts

        # Need at least 2 valid (distinct) points for interpolation
        if len(x_clean) < 2:
            empty = ColumnDataSource({"x_sp": [], "y_sp": []})
            r = fig.line(x="x_sp", y="y_sp", source=empty)
            return [r]

        interp = PchipInterpolator(x_clean, y_clean)
        x_grid = np.linspace(x_clean.min(), x_clean.max(), 200)
        y_grid = interp(x_grid)

        ms_source = ColumnDataSource({"x_sp": x_grid, "y_sp": y_grid})
        r = fig.line(x="x_sp", y="y_sp", source=ms_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return [r]

    def map_mband(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
        view=None,
        color_idx: int = 0,
    ) -> list:
        """Add a median band smoother to *fig*.

        ``twoway mband`` replicates Stata's median-band plot: the x range is
        divided into equal-width bands and the median of *yvar* within each
        band is plotted as a step-through line.  The number of bands defaults
        to ``min(ceil(n/5), 20)`` so that each band contains at least ~5
        observations on average.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y variable.
            xvar:    Name of the x variable.
            options: Translated plot-level options dict.

        Returns:
            List with the single GlyphRenderer for the median-band line.
        """
        x_arr = np.array(source.data[xvar], dtype=float)
        y_arr = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
        x_clean = x_arr[mask]
        y_clean = y_arr[mask]

        empty = ColumnDataSource({"x_mb": [], "y_mb": []})

        if len(x_clean) < 4:
            r = fig.line(x="x_mb", y="y_mb", source=empty)
            return [r]

        # Number of bands: at least 2, at most 20, targeting ~5 obs per band
        n_bands = int(np.clip(int(np.ceil(len(x_clean) / 5)), 2, 20))
        x_min, x_max = float(x_clean.min()), float(x_clean.max())
        if x_max == x_min:
            r = fig.line(x="x_mb", y="y_mb", source=empty)
            return [r]

        edges = np.linspace(x_min, x_max, n_bands + 1)
        x_mids: list[float] = []
        y_meds: list[float] = []
        for i in range(n_bands):
            lo, hi = edges[i], edges[i + 1]
            # Include right edge in the last band
            in_band = (
                (x_clean >= lo) & (x_clean <= hi) if i == n_bands - 1
                else (x_clean >= lo) & (x_clean < hi)
            )
            if in_band.sum() > 0:
                x_mids.append(float(0.5 * (lo + hi)))
                y_meds.append(float(np.median(y_clean[in_band])))

        if not x_mids:
            r = fig.line(x="x_mb", y="y_mb", source=empty)
            return [r]

        mb_source = ColumnDataSource({"x_mb": x_mids, "y_mb": y_meds})
        r = fig.line(x="x_mb", y="y_mb", source=mb_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=2.0,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return [r]

    def map_function(
        self,
        fig: Any,
        expr: str,
        x_range: tuple = (0.0, 1.0),
        n_points: int = 200,
        options: dict = {},
    ) -> list:
        """Add a mathematical function curve to *fig*.

        Evaluates a user-supplied expression string over a uniform grid and
        renders the result as a line.  The expression is validated against an
        AST whitelist before any evaluation; raw ``eval()`` on unvalidated
        strings is never performed.

        Security: Only a restricted set of AST node types and function names
        is permitted.  ``__builtins__`` is removed from the evaluation
        namespace to prevent access to Python built-ins.

        Args:
            fig:      Bokeh Figure object.
            expr:     Mathematical expression string using variable ``x`` and
                      the safe function names listed below.
            x_range:  ``(x_lo, x_hi)`` tuple defining the evaluation domain.
            n_points: Number of grid points (default 200).
            options:  Translated plot-level options dict.

        Permitted names in expressions:
            Variables: ``x``, ``pi``, ``e``
            Functions: ``sin``, ``cos``, ``tan``, ``exp``, ``log``,
                       ``log10``, ``sqrt``, ``abs``, ``floor``, ``ceil``

        Returns:
            List with the single line GlyphRenderer, or an empty renderer
            if validation or evaluation fails.
        """
        import ast as _ast

        _SAFE_NAMES: frozenset = frozenset({"x", "pi", "e"})
        _SAFE_FUNCS: frozenset = frozenset({
            "sin", "cos", "tan", "exp", "log", "log10",
            "sqrt", "abs", "floor", "ceil",
        })

        def _validate_expr_node(node: _ast.AST) -> None:
            """Recursively validate that *node* contains only safe AST constructs."""
            if isinstance(node, _ast.Expression):
                _validate_expr_node(node.body)
            elif isinstance(node, _ast.Constant):
                pass  # numeric literals are always safe
            elif isinstance(node, _ast.Name):
                if node.id not in _SAFE_NAMES:
                    raise ValueError(
                        f"Unsafe name in function expression: {node.id!r}. "
                        f"Allowed names: {sorted(_SAFE_NAMES)}"
                    )
            elif isinstance(node, (_ast.BinOp, _ast.UnaryOp)):
                # iter_child_nodes on BinOp yields (left, op, right) where op
                # is an operator node (Add, Sub, Mult, etc.).  Operator nodes
                # carry no dangerous payload; skip them explicitly so the
                # else-branch does not reject them.
                _OP_NODES = (
                    _ast.Add, _ast.Sub, _ast.Mult, _ast.Div, _ast.FloorDiv,
                    _ast.Mod, _ast.Pow, _ast.UAdd, _ast.USub, _ast.BitXor,
                    _ast.BitOr, _ast.BitAnd,
                )
                for child in _ast.iter_child_nodes(node):
                    if isinstance(child, _OP_NODES):
                        continue  # safe: pure operator, no state
                    _validate_expr_node(child)
            elif isinstance(node, _ast.Call):
                if (
                    not isinstance(node.func, _ast.Name)
                    or node.func.id not in _SAFE_FUNCS
                ):
                    raise ValueError(
                        f"Disallowed function call in expression. "
                        f"Allowed functions: {sorted(_SAFE_FUNCS)}"
                    )
                for arg in node.args:
                    _validate_expr_node(arg)
                if node.keywords:
                    raise ValueError("Keyword arguments are not allowed in function expressions.")
            else:
                raise ValueError(
                    f"Disallowed AST node type in expression: {type(node).__name__}"
                )

        empty_source = ColumnDataSource({"x_fn": [], "y_fn": []})

        try:
            tree = _ast.parse(expr, mode="eval")
            _validate_expr_node(tree)
            code = compile(tree, "<function>", "eval")
        except (SyntaxError, ValueError):
            return [fig.line(x="x_fn", y="y_fn", source=empty_source,
                             line_color="#d62728", line_width=2.0)]

        x_lo, x_hi = float(x_range[0]), float(x_range[1])
        x_arr = np.linspace(x_lo, x_hi, int(n_points))

        ns: dict = {
            "x":      x_arr,
            "pi":     math.pi,
            "e":      math.e,
            "sin":    np.sin,
            "cos":    np.cos,
            "tan":    np.tan,
            "exp":    np.exp,
            "log":    np.log,
            "log10":  np.log10,
            "sqrt":   np.sqrt,
            "abs":    np.abs,
            "floor":  np.floor,
            "ceil":   np.ceil,
        }

        try:
            # __builtins__ blocked: prevents access to Python built-ins from
            # the evaluated code.  The AST whitelist ensures no harmful nodes
            # reached compile(); this is defence-in-depth.
            y_arr = eval(code, {"__builtins__": {}}, ns)  # noqa: S307 (intentional safe eval)
            y_arr = np.asarray(y_arr, dtype=float)
            # Broadcast scalar results (e.g. "pi", "e", "3.14") to match x_arr length
            if y_arr.ndim == 0:
                y_arr = np.full(len(x_arr), float(y_arr))
        except Exception:
            return [fig.line(x="x_fn", y="y_fn", source=empty_source,
                             line_color="#d62728", line_width=2.0)]

        fn_source = ColumnDataSource({"x_fn": x_arr, "y_fn": y_arr})
        r = fig.line(x="x_fn", y="y_fn", source=fn_source,
                     line_color="#d62728", line_width=2.0,
                     legend_label=expr[:40])
        self._apply_line_opts(r, options)
        return [r]


# ---------------------------------------------------------------------------
# CSS color sanitizer — used to harden KPI color/bgcolor before they are
# embedded in inline style attributes within the filter callback HTML.
# ---------------------------------------------------------------------------

_CSS_COLOR_RE = re.compile(
    r"^\s*(?:"
    r"#[0-9a-fA-F]{3,8}"                                   # hex: #RGB, #RRGGBB, #RRGGBBAA
    r"|rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)"  # rgb(r,g,b)
    r"|rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[\d.]+\s*\)"  # rgba(r,g,b,a)
    r"|hsl\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*\)"           # hsl(h,s%,l%)
    r"|hsla\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*,\s*[\d.]+\s*\)"  # hsla(h,s%,l%,a)
    r"|[a-zA-Z]{2,30}"                                      # named color (letters only)
    r")\s*$"
)


# ---------------------------------------------------------------------------
# if_expr AST whitelist validator — prevents RCE via df.query(engine="python")
# ---------------------------------------------------------------------------
# pandas.DataFrame.query(engine="python") lets callers use @var references to
# access local Python objects.  A crafted expression such as
#   @pd.io.common.os.system("id")  →  triggers os.system() before the filter
# The regex blacklist in the old code did NOT block @ references.
#
# The safe design: parse the user-supplied expression as a Python AST and
# accept only a narrow whitelist of node types (comparisons, boolean ops,
# column-name references, and literals).  Any other node — Call, Attribute,
# Subscript, Lambda, comprehension, etc. — is rejected outright.
# ---------------------------------------------------------------------------

import ast as _ast

_IF_EXPR_ALLOWED_NODES: "frozenset[type]" = frozenset({
    _ast.Expression,
    # Boolean combinators (and/or)
    _ast.BoolOp, _ast.And, _ast.Or,
    # Binary operators — pandas uses & / | / ~ as logical connectives
    # inside query strings; they parse as BinOp(BitAnd/BitOr) in Python AST.
    _ast.BinOp, _ast.BitAnd, _ast.BitOr,
    # Comparison
    _ast.Compare,
    _ast.Eq, _ast.NotEq,
    _ast.Lt, _ast.LtE, _ast.Gt, _ast.GtE,
    _ast.In, _ast.NotIn,
    # Unary (logical not and bitwise invert for ~ operator)
    _ast.UnaryOp, _ast.Not, _ast.Invert, _ast.USub,
    # Literals
    _ast.Constant,
    # Column name references (bare identifiers like `foreign`)
    _ast.Name,
    # Tuple/List used in `col in (1, 2, 3)` tests
    _ast.Tuple, _ast.List,
    # Load context (reading a value)
    _ast.Load,
})

# Safe bare Name values that are not column names
_IF_EXPR_SAFE_NAMES: "frozenset[str]" = frozenset(
    {"True", "False", "None", "nan", "NaN", "inf"}
)


def _validate_if_expr(expr: str, columns: "Iterable[str]") -> bool:
    """Return True only if *expr* is a safe comparison/boolean expression.

    Accepts only column references, numeric/string literals, comparison
    operators (==, !=, <, <=, >, >=, in, not in) and boolean combinators
    (& | ~ not and or).  All other Python constructs — function calls,
    attribute access, subscripts, lambdas, comprehensions, and ``@``
    variable references — are rejected.

    This is the first gate applied before ``df.query()`` to prevent code
    execution via the ``engine="python"`` evaluator.

    Args:
        expr:    The if_expr string from the graph specification.
        columns: Iterable of column names present in the DataFrame.

    Returns:
        True if the expression is safe to pass to ``df.query()``;
        False if any unsafe construct is detected.
    """
    # Hard-reject @ before parsing — catches @-variable references that
    # allow access to local Python objects via pandas query engine.
    if "@" in expr:
        return False
    try:
        tree = _ast.parse(expr, mode="eval")
    except SyntaxError:
        return False
    col_set = frozenset(str(c) for c in columns)
    for node in _ast.walk(tree):
        if type(node) not in _IF_EXPR_ALLOWED_NODES:
            return False
        if isinstance(node, _ast.Name):
            if node.id not in col_set and node.id not in _IF_EXPR_SAFE_NAMES:
                return False
    return True


def _sanitize_css_color(val: str, default: str) -> str:
    """Return *val* if it matches a safe CSS color pattern, else return *default*.

    Prevents CSS style-attribute injection when KPI color/bgcolor values are
    embedded directly into inline-style HTML by the JS filter callback.  Only
    hex, rgb/rgba, hsl/hsla, and letter-only named colors are accepted; any
    value containing quotes, semicolons, parentheses that don't match the
    expected patterns, or other shell/HTML special characters is rejected.

    Args:
        val:     The raw color string from the spec.
        default: A trusted fallback color to use when val is unsafe/empty.

    Returns:
        A CSS-safe color string.
    """
    if not isinstance(val, str) or not val.strip():
        return default
    if _CSS_COLOR_RE.match(val):
        return val.strip()
    return default


# ===========================================================================
# FilterBuilder
# ===========================================================================

# ---------------------------------------------------------------------------
# Shared JavaScript for filter callbacks (all filter widget types)
# ---------------------------------------------------------------------------
# The callback re-applies ALL active filter conditions on the original data
# then replaces source.data (which reliably triggers Bokeh 3.x re-renders),
# clears any lingering selection, and updates KPI Div text via the DOM.
_FILTER_JS = """
// Bokeh 3.x serialises Python dicts as JavaScript Map objects, not plain {}.
// All structured args (orig_data, filter_specs, kpi_config) are therefore
// passed as JSON strings and parsed here to avoid Map-vs-object mismatches.
const orig        = JSON.parse(orig_data_json);
const filter_specs = JSON.parse(filter_specs_json);
const kpi_config  = JSON.parse(kpi_config_json);

const n_rows = orig[Object.keys(orig)[0]].length;
const active = new Array(n_rows).fill(true);

// Re-apply every filter widget's current value
for (let fi = 0; fi < filter_specs.length; fi++) {
    const spec = filter_specs[fi];
    const w    = all_widgets[fi];
    const fvar = spec.varname;
    const ftype = spec.type;

    // Defensive guard: skip if widget ref is missing or column absent from data.
    // In practice filter_specs_json is built only from successfully-built specs
    // so this should never fire, but it prevents a runtime TypeError if the
    // callback is ever invoked with stale or partially-constructed args.
    if (!w || !(fvar in orig)) continue;

    if (ftype === 'dropdown') {
        const val = w.value;
        // Use per-widget sentinel (may differ from '__all__' when data contains
        // the literal '__all__' value — sentinel is then '__all__' + extra '_').
        const sentinel = spec.sentinel || '__all__';
        if (val === sentinel) continue;
        for (let i = 0; i < n_rows; i++) {
            if (active[i] && String(orig[fvar][i]) !== val) active[i] = false;
        }
    } else if (ftype === 'slider') {
        const val = w.value;
        for (let i = 0; i < n_rows; i++) {
            if (active[i] && orig[fvar][i] < val) active[i] = false;
        }
    } else if (ftype === 'range') {
        const lo = w.value[0];
        const hi = w.value[1];
        for (let i = 0; i < n_rows; i++) {
            if (active[i] && (orig[fvar][i] < lo || orig[fvar][i] > hi))
                active[i] = false;
        }
    }
}

// Build new data arrays containing only active rows from the primary source.
// This snapshot is used for KPI value updates and for the primary `source`
// fallback path (when source is not already in all_graph_sources).
const new_data = {};
const cols = Object.keys(orig);
for (const col of cols) { new_data[col] = []; }
for (let i = 0; i < n_rows; i++) {
    if (active[i]) {
        for (const col of cols) { new_data[col].push(orig[col][i]); }
    }
}

// Replace source data in ALL non-excluded graph sources, using each source's
// own per-source original snapshot so that unlinked graphs with different
// column schemas are not corrupted when a single new_data payload is broadcast
// to all sources.  The active[] row-mask is computed from the primary source
// above; since all sources share the same underlying row universe this mask
// applies correctly to every source regardless of column differences.
const _srcs = all_graph_sources;
const _srcs_orig_json = all_graph_sources_orig_json;
for (let _si = 0; _si < _srcs.length; _si++) {
    // Parse this source's own snapshot — preserves its unique column set.
    const _orig_i = JSON.parse(_srcs_orig_json[_si]);
    const _cols_i = Object.keys(_orig_i);
    const _n_i    = _cols_i.length > 0 ? _orig_i[_cols_i[0]].length : 0;
    const _nd_i   = {};
    for (const col of _cols_i) { _nd_i[col] = []; }
    for (let i = 0; i < _n_i; i++) {
        if (i < active.length && active[i]) {
            for (const col of _cols_i) { _nd_i[col].push(_orig_i[col][i]); }
        }
    }
    _srcs[_si].data = _nd_i;
    _srcs[_si].selected.indices = [];
    _srcs[_si].change.emit();
}
// Also update the primary `source` (may overlap with all_graph_sources when linked)
if (!_srcs.includes(source)) {
    source.data = new_data;
    source.selected.indices = [];
    source.change.emit();
}

// Update KPI card values by setting the Bokeh Div model's text property.
//
// WHY NOT document.getElementById:
//   Bokeh 3.x stores the document JSON inside <script type="application/json">.
//   HTML entities (&lt; &gt;) in that block are NOT decoded by the browser
//   before JavaScript reads them, so the Div HTML is stored with literal
//   "&lt;div id=..." strings.  When Bokeh renders innerHTML those become
//   visible text, not DOM nodes — document.getElementById always returns null.
//
// WHY kpi_div.text works:
//   Assigning to a Bokeh model property from CustomJS triggers Bokeh's own
//   change-detection and re-renders the widget with fresh innerHTML, bypassing
//   the serialisation issue entirely.
for (let ki = 0; ki < kpi_config.length; ki++) {
    const k      = kpi_config[ki];
    const kpi_div = kpi_divs[ki];
    if (!kpi_div) continue;

    const col = new_data[k.varname];
    if (!col) continue;
    const vals = col.filter(v => v !== null && v !== undefined && !isNaN(v));

    let result = 0;
    const stat = k.stat;
    if (stat === 'count') {
        result = vals.length;
    } else if (vals.length > 0) {
        if (stat === 'mean') {
            result = vals.reduce((a, b) => a + b, 0) / vals.length;
        } else if (stat === 'sum') {
            result = vals.reduce((a, b) => a + b, 0);
        } else if (stat === 'min') {
            // Iterative reduction avoids RangeError: Maximum call stack
            // size exceeded that spread-based Math.min would hit on large arrays.
            result = vals.reduce((a, b) => a < b ? a : b, vals[0]);
        } else if (stat === 'max') {
            result = vals.reduce((a, b) => a > b ? a : b, vals[0]);
        } else if (stat === 'median' || stat === 'p50') {
            const s = vals.slice().sort((a, b) => a - b);
            const m = Math.floor(s.length / 2);
            result = s.length % 2 === 0 ? (s[m - 1] + s[m]) / 2 : s[m];
        } else if (stat === 'dcount') {
            result = new Set(vals.map(String)).size;
        } else if (stat === 'sd' && vals.length > 1) {
            const mu = vals.reduce((a, b) => a + b, 0) / vals.length;
            result = Math.sqrt(
                vals.reduce((a, b) => a + Math.pow(b - mu, 2), 0) / (vals.length - 1)
            );
        }
    }

    let fmt = result.toFixed(k.decimals);
    if (k.commas) {
        const parts = fmt.split('.');
        parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
        fmt = parts.join('.');
    }

    // Rebuild the complete Div HTML and assign to the Bokeh model property.
    // Using template literals here is fine — the JS is embedded via CustomJS
    // args (never interpolated from user input).
    kpi_div.text = (
        '<div style="background:' + k.bgcolor + '; border-radius:8px; padding:20px; ' +
        'text-align:center; border:1px solid #dee2e6; min-width:160px; min-height:110px;">' +
        '<div style="font-size:13px; color:#6c757d; margin-bottom:6px;">' + k.title + '</div>' +
        '<div style="font-size:36px; font-weight:bold; color:' + k.color + ';">' + fmt + '</div>' +
        '<div style="font-size:11px; color:#6c757d; margin-top:4px;">' + k.subtitle + '</div>' +
        '</div>'
    );
}

// --- Recompute aggregate plots (histogram, kdensity) ---
// agg_sources is a Bokeh model list (plain JS object references).
// agg_configs is parsed from the JSON string arg.
const agg_configs = JSON.parse(agg_configs_json);
for (let ai = 0; ai < agg_configs.length; ai++) {
    const ac  = agg_configs[ai];
    const src = agg_sources[ai];
    if (!src) continue;

    // Pull filtered values for this aggregate variable.
    // new_data already contains only the rows that passed every active filter.
    const raw_col = new_data[ac.varname];
    if (!raw_col) continue;
    const vals = raw_col.filter(v => v !== null && v !== undefined && !isNaN(v));

    if (ac.type === 'histogram') {
        const edges = ac.bin_edges;
        const n_bins = edges.length - 1;
        if (vals.length === 0) {
            // No rows pass the filter — clear histogram to zero rather than
            // leaving stale bars from the previous data visible.
            src.data = {
                top:   new Array(n_bins).fill(0),
                left:  edges.slice(0, n_bins),
                right: edges.slice(1),
            };
            src.change.emit();
            continue;
        }
        const counts = new Array(n_bins).fill(0);
        for (const v of vals) {
            if (v < edges[0] || v > edges[edges.length - 1]) continue;
            if (v === edges[edges.length - 1]) {
                // last bin is closed on the right
                counts[n_bins - 1]++;
            } else {
                for (let b = 0; b < n_bins; b++) {
                    if (v >= edges[b] && v < edges[b + 1]) { counts[b]++; break; }
                }
            }
        }
        src.data = {
            top:   counts,
            left:  edges.slice(0, n_bins),
            right: edges.slice(1),
        };
        src.change.emit();

    } else if (ac.type === 'kdensity') {
        const n = vals.length;
        if (n < 2) {
            // Fewer than 2 data points — clear kdensity curve rather than
            // leaving the previous curve visible as stale data.
            src.data = { x: [], y: [] };
            src.change.emit();
            continue;
        }
        // Silverman's rule for bandwidth on the filtered subset
        const mu = vals.reduce((a, b) => a + b, 0) / n;
        const variance = vals.reduce((a, b) => a + (b - mu) * (b - mu), 0) / (n - 1);
        const sd = Math.sqrt(variance);
        const sorted = vals.slice().sort((a, b) => a - b);
        const q1 = sorted[Math.max(0, Math.floor(0.25 * (n - 1)))];
        const q3 = sorted[Math.min(n - 1, Math.floor(0.75 * (n - 1)))];
        const iqr = q3 - q1;
        const bw_scale = Math.min(sd, iqr > 0 ? iqr / 1.34 : sd);
        const h = 0.9 * bw_scale * Math.pow(n, -0.2);
        if (h <= 0) continue;
        const INV_SQRT_2PI = 0.3989422804014327;
        const xs = ac.x_grid;
        const ys = xs.map(x => {
            let s = 0;
            for (const xi of vals) {
                const z = (x - xi) / h;
                s += Math.exp(-0.5 * z * z);
            }
            return s * INV_SQRT_2PI / (n * h);
        });
        src.data = { x: xs, y: ys };
        src.change.emit();
    }
}
"""


class FilterBuilder:
    """Builds Bokeh filter widgets with secure, parameterized CustomJS callbacks.

    Security: All user-provided variable names and values are HTML-escaped
    before being embedded in any JavaScript string literals.  The JS templates
    use variable references rather than direct code-path interpolation.
    """

    @staticmethod
    def _safe(value: str) -> str:
        """HTML-escape a user-provided string for safe JS embedding."""
        return html.escape(str(value), quote=True)

    @staticmethod
    def build_dropdown(
        varname: str,
        source: ColumnDataSource,
        df_or_data: "Any | None" = None,
        value_labels: "dict | None" = None,
        exclude_names: "list[str] | None" = None,
        all_figure_names: "list[str] | None" = None,
        figure_renderer_map: "dict | None" = None,
        kpi_divs: "dict | None" = None,
        label: str = "",
    ) -> "tuple[Select, CustomJS]":
        """Build a categorical dropdown filter widget with CustomJS callback.

        The callback replaces ``source.data`` with only the rows matching the
        selected value, which reliably triggers Bokeh 3.x re-renders for all
        linked renderers.  ``orig_data``, ``all_widgets``, ``filter_specs``,
        and ``kpi_config`` are placeholder args populated by
        :meth:`DashRenderer.render` after all filter widgets are built.

        Args:
            varname:      Stata variable name to filter on.
            source:       The shared ColumnDataSource.
            df_or_data:   Ignored; kept for API compatibility.
            value_labels: Flat or nested ``{code: label}`` mapping.
            exclude_names: Ignored at build time; used in render wiring.
            all_figure_names: Ignored; kept for API compatibility.
            figure_renderer_map: Ignored; kept for API compatibility.
            kpi_divs: Ignored; kept for API compatibility.

        Returns:
            A ``(Select widget, CustomJS callback)`` tuple.
        """
        if value_labels is None:
            value_labels = {}
        if exclude_names is None:
            exclude_names = []

        safe_var = FilterBuilder._safe(varname)

        # Resolve nested {varname: {code: label}} or flat {code: label}
        if varname in value_labels and isinstance(value_labels[varname], dict):
            vlabels: dict = value_labels[varname]
        else:
            vlabels = value_labels

        # Normalize float-integer option values ("0.0" → "0") for JS match
        def _int_normalized(v) -> str:
            s = str(v)
            try:
                f = float(s)
                i = int(f)
                if f == i:
                    return str(i)
            except (ValueError, TypeError, OverflowError):
                pass
            return s

        raw_values = list(set(
            _int_normalized(v) for v in source.data[varname]
            if v is not None and str(v) not in ("nan", "None")
        ))

        def _sort_key(v: str):
            try:
                return (0, float(v))
            except (ValueError, TypeError):
                return (1, v)
        raw_values.sort(key=_sort_key)

        def _resolve_label(rv: str) -> str:
            if rv in vlabels:
                return vlabels[rv]
            try:
                int_key = str(int(float(rv)))
                if int_key in vlabels:
                    return vlabels[int_key]
            except (ValueError, OverflowError):
                pass
            return rv

        # Compute a per-widget sentinel that is guaranteed absent from the
        # observed raw values to prevent collision when real data contains
        # the literal string "__all__".
        _sentinel = "__all__"
        while _sentinel in raw_values:
            _sentinel += "_"

        options = [(_sentinel, "All")]
        for rv in raw_values:
            options.append((rv, FilterBuilder._safe(_resolve_label(rv))))

        _widget_title = html.escape(label.strip()) if label.strip() else safe_var
        widget = Select(title=_widget_title, value=_sentinel,
                        options=[(v, l) for v, l in options])
        widget._dash_sentinel = _sentinel  # store for filter_specs_json inclusion

        callback = CustomJS(
            args={
                "source":            source,
                # JSON strings (not dicts/lists) so Bokeh 3.x serialises
                # them as plain JS strings, not Map objects.  Parsed via
                # JSON.parse() inside _FILTER_JS.
                "orig_data_json":    "{}",  # populated by DashRenderer.render()
                "all_widgets":       [],    # populated by DashRenderer.render()
                "filter_specs_json": "[]",  # populated by DashRenderer.render()
                "kpi_config_json":   "[]",  # populated by DashRenderer.render()
                # KPI Div model objects — updated via model property, not DOM
                "kpi_divs":          [],    # populated by DashRenderer.render()
                # Aggregate sources (histogram, kdensity) to recompute on filter
                "agg_sources":       [],    # populated by DashRenderer.render()
                "agg_configs_json":  "[]",  # populated by DashRenderer.render()
                # All non-excluded graph sources — populated by DashRenderer.render()
                # so _FILTER_JS can update every graph in an unlinked dashboard
                "all_graph_sources": [],              # populated by DashRenderer.render()
                # Per-source original data snapshots (indexed parallel to
                # all_graph_sources) so _FILTER_JS can rebuild filtered data
                # for each source using its own column schema.  Prevents
                # unlinked graphs with different columns from being corrupted
                # when a single new_data payload is broadcast to all sources.
                "all_graph_sources_orig_json": [],   # populated by DashRenderer.render()
            },
            code=_FILTER_JS,
        )
        widget.js_on_change("value", callback)
        return widget, callback

    @staticmethod
    def build_slider(
        varname: str,
        source: ColumnDataSource,
        df_or_data: "Any | None" = None,
        exclude_names: "list[str] | None" = None,
        all_figure_names: "list[str] | None" = None,
        label: str = "",
    ) -> "tuple[Slider, CustomJS]":
        """Build a numeric threshold slider filter widget.

        Shows rows where ``varname >= slider.value``.  Callback args are
        populated by :meth:`DashRenderer.render`.

        Returns:
            A ``(Slider widget, CustomJS callback)`` tuple.
        """
        if exclude_names is None:
            exclude_names = []
        safe_var = FilterBuilder._safe(varname)
        # Build a title that makes the ≥ inequality explicit to end users.
        _raw_lbl = label.strip() if label.strip() else safe_var
        _slider_title = _raw_lbl if _raw_lbl.endswith(("\u2265", ">=", "≥")) \
            else _raw_lbl + " \u2265"
        arr = _extract_finite(source, varname)
        if len(arr) == 0:
            widget = Slider(title=_slider_title, start=0, end=1, value=0, step=1,
                            disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        if vmin == vmax:
            vmax = vmin + 1.0
        vstep = (vmax - vmin) / 100.0 or 1.0

        widget = Slider(title=_slider_title, start=vmin, end=vmax,
                        value=vmin, step=vstep)

        callback = CustomJS(
            args={
                "source":            source,
                "orig_data_json":    "{}",
                "all_widgets":       [],
                "filter_specs_json": "[]",
                "kpi_config_json":   "[]",
                "kpi_divs":          [],
                "agg_sources":       [],
                "agg_configs_json":  "[]",
                "all_graph_sources": [],              # populated by DashRenderer.render()
                "all_graph_sources_orig_json": [],   # populated by DashRenderer.render()
            },
            code=_FILTER_JS,
        )
        widget.js_on_change("value", callback)
        return widget, callback

    @staticmethod
    def build_range(
        varname: str,
        source: ColumnDataSource,
        df_or_data: "Any | None" = None,
        exclude_names: "list[str] | None" = None,
        all_figure_names: "list[str] | None" = None,
        label: str = "",
    ) -> "tuple[RangeSlider, CustomJS]":
        """Build a numeric range filter widget.

        Shows rows where ``varname >= start AND varname <= end``.  Callback
        args are populated by :meth:`DashRenderer.render`.

        Returns:
            A ``(RangeSlider widget, CustomJS callback)`` tuple.
        """
        if exclude_names is None:
            exclude_names = []
        safe_var = FilterBuilder._safe(varname)
        arr = _extract_finite(source, varname)
        _raw_range_lbl = label.strip() if label.strip() else safe_var
        if len(arr) == 0:
            widget = RangeSlider(title=_raw_range_lbl, start=0, end=1,
                                 value=(0, 1), step=1, disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        if vmin == vmax:
            vmax = vmin + 1.0
        vstep = (vmax - vmin) / 100.0 or 1.0

        widget = RangeSlider(title=_raw_range_lbl,
                             start=vmin, end=vmax,
                             value=(vmin, vmax), step=vstep)

        callback = CustomJS(
            args={
                "source":            source,
                "orig_data_json":    "{}",
                "all_widgets":       [],
                "filter_specs_json": "[]",
                "kpi_config_json":   "[]",
                "kpi_divs":          [],
                "agg_sources":       [],
                "agg_configs_json":  "[]",
                "all_graph_sources": [],              # populated by DashRenderer.render()
                "all_graph_sources_orig_json": [],   # populated by DashRenderer.render()
            },
            code=_FILTER_JS,
        )
        widget.js_on_change("value", callback)
        return widget, callback


# ===========================================================================
# DashRenderer
# ===========================================================================

class DashRenderer:
    """Orchestrates the full Bokeh dashboard build from a master spec JSON.

    Workflow
    --------
    1.  Load the jsonio data JSON → ``pandas.DataFrame`` + metadata.
    2.  Build one ``ColumnDataSource`` per link group (or per figure if unlinked).
    3.  Build one Bokeh ``Figure`` per registered graph, adding glyphs via
        ``GlyphMapper``.
    4.  Build KPI ``Div`` widgets.
    5.  Build filter widgets via ``FilterBuilder`` and wire their CDSView
        references.
    6.  Assemble everything into a Bokeh layout.
    7.  Return the complete standalone HTML string.

    Args:
        master_spec_path: Path to the master specification JSON file written
                          by ``dash.ado`` containing all graph specs, KPI
                          definitions, and build options.
        data_json_path:   Path to the jsonio output JSON file containing the
                          full dataset with Stata metadata.
    """

    # Variable key names used in plot specs — shared by _collect_plot_vars and render()
    _VAR_KEYS: "tuple[str, ...]" = (
        "yvar", "xvar", "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var"
    )
    _OPT_VAR_KEYS: "tuple[str, ...]" = ("colorvar", "mlabel")

    @staticmethod
    def _collect_plot_vars(plots_list: list) -> list:
        """Return deduplicated list of all variable columns needed by plots."""
        seen: list[str] = []
        for plot in plots_list:
            for key in DashRenderer._VAR_KEYS:
                v = plot.get(key)
                if v and v not in seen:
                    seen.append(v)
            for key in DashRenderer._OPT_VAR_KEYS:
                v = plot.get("options", {}).get(key, "").strip()
                if v and v not in seen:
                    seen.append(v)
        return seen

    @staticmethod
    def _collect_graph_vars(df: "pd.DataFrame", g_spec: dict) -> list:
        """Return deduplicated list of variable columns for a graph,
        including hover tooltip variables from graph_options.hover."""
        seen = DashRenderer._collect_plot_vars(g_spec.get("plots", []))
        hover_str = g_spec.get("graph_options", {}).get("hover", "").strip()
        for hv in hover_str.split():
            if hv and hv not in seen and hv in df.columns:
                seen.append(hv)
        return seen

    def __init__(
        self,
        master_spec_path: str,
        data_json_path: str,
        output_path: str = "",
    ) -> None:
        """Initialise the renderer by loading both JSON files.

        Args:
            master_spec_path: Absolute path to master spec JSON.
            data_json_path:   Absolute path to jsonio data JSON.
            output_path:      Optional path where HTML output will be written.

        Raises:
            FileNotFoundError: If either file does not exist.
            ValueError:        If the JSON structure is not as expected.
        """
        self.output_path = output_path

        for path in (master_spec_path, data_json_path):
            if not os.path.isfile(path):
                raise FileNotFoundError(
                    f"dash_render: required file not found: {path}"
                )

        with open(master_spec_path, encoding="utf-8") as f:
            self.master_spec: dict = json.loads(f.read())

        with open(data_json_path, encoding="utf-8") as f:
            self.data_json: dict = json.loads(f.read())

        self.translator = OptionTranslator()

        # Load scheme — falls back to s2color if unrecognised.
        # dash.ado writes build_options["theme"] using Stata theme names; the
        # Python side uses build_options["scheme"] for direct scheme names.
        # Both are honoured here via a theme→scheme mapping.
        _THEME_SCHEME_MAP: dict = {
            "default":    "s2color",
            "clean":      "s1color",
            "mono":       "s1mono",
            "economist":  "economist",
            "sj":         "sj",
        }
        _build_opts: dict = self.master_spec.get("build_options", {})
        # Prefer explicit 'scheme' key; fall back to 'theme' key.
        _raw_name: str = (
            _build_opts.get("scheme", "").strip()
            or _build_opts.get("theme", "").strip()
            or ""
        )
        # Map theme alias to scheme name; if already a valid scheme name pass
        # through unchanged; empty string resolves to s2color.
        _scheme_name: str = (
            _THEME_SCHEME_MAP.get(_raw_name.lower(), _raw_name) or "s2color"
        )
        try:
            self.scheme: SchemeParser = SchemeParser(_scheme_name)
        except (ValueError, OSError):
            self.scheme = SchemeParser("s2color")

        self.mapper = GlyphMapper(scheme=self.scheme)

        # Populated during _load_data()
        self.df: pd.DataFrame = pd.DataFrame()
        self.variable_labels: dict[str, str] = {}
        self.value_labels: dict[str, dict[str, str]] = {}
        self.value_label_names: dict[str, str] = {}
        self.string_vars: set[str] = set()

        # Populated during build phases
        self.sources: dict[str, ColumnDataSource] = {}   # name → CDS
        self.figures: dict[str, Any] = {}                # name → Figure
        self.kpi_divs: dict[str, Div] = {}               # name → Div
        self.filter_widgets: list = []
        self.filter_callbacks: list = []

        # Registry of aggregate sources (histogram bins, KDE curve) that must
        # be recomputed by the JS filter callback.
        # graph_name → [(agg_cds, config_dict), ...]
        # config_dict keys: type, varname, bin_edges (histogram) or x_grid (kdensity)
        self.agg_source_registry: dict = {}

        # Tracks KPI update mode ("filter" | "brush" | "both") by KPI name.
        self._kpi_update_modes: dict[str, str] = {}

        # Facet map: graph_name → [(facet_key, facet_label), ...]
        self._facet_map: dict[str, list[tuple[str, str]]] = {}

        # Facet masks for by()+link() graphs: graph_name → [(label, bool_mask), ...]
        self._facet_masks: dict = {}

        self._load_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> None:
        """Parse the jsonio data JSON into a DataFrame and extract metadata.

        Populates:
          - self.df                  — full dataset as a pandas DataFrame
          - self.variable_labels     — {varname: label}
          - self.value_labels        — {labelset_name: {raw_value: display}}
          - self.value_label_names   — {varname: labelset_name}
          - self.string_vars         — set of variable names that are strings
        """
        stata_json = self.data_json.get("StataJSON", self.data_json)

        # Records
        records = stata_json.get("values", [])
        self.df = pd.DataFrame(records)

        # Variable labels
        self.variable_labels = stata_json.get("variableLabels", {})

        # Value labels — stored as {labelset: {str(code): display_text}}
        self.value_labels = stata_json.get("valueLabels", {})

        # Which variable uses which label set
        self.value_label_names = stata_json.get("valueLabelNames", {})

        # String variable flags
        type_is_string = stata_json.get("variableTypeIsString", {})
        self.string_vars = {k for k, v in type_is_string.items() if v}

        # Convert numeric columns to float so NaN propagates correctly
        for col in self.df.columns:
            if col not in self.string_vars:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

    # ------------------------------------------------------------------
    # _df property — convenience alias for self.df, settable for testing
    # ------------------------------------------------------------------

    @property
    def _df(self) -> pd.DataFrame:
        """Return the loaded dataset DataFrame."""
        return self.df

    @_df.setter
    def _df(self, value: pd.DataFrame) -> None:
        self.df = value

    # ------------------------------------------------------------------
    # KPI statistic computation
    # ------------------------------------------------------------------

    def _compute_kpi_stat(self, stat: str, varname: str) -> float:
        """Compute a summary statistic from self._df.

        Args:
            stat:    One of: mean, sum, count, dcount, min, max, median,
                     sd, p25, p50, p75.
            varname: Column name in self._df.

        Returns:
            Computed statistic as a float.

        Raises:
            ValueError: If stat is unknown or varname not in DataFrame.
        """
        col = self._df[varname].dropna()
        s = stat.strip().lower()
        if s == "mean":
            return float(col.mean())
        if s == "sum":
            return float(col.sum())
        if s == "count":
            return float(len(col))
        if s == "dcount":
            return float(col.nunique())
        if s == "min":
            return float(col.min())
        if s == "max":
            return float(col.max())
        if s in ("median", "p50"):
            return float(col.median())
        if s == "sd":
            return float(col.std(ddof=1))
        if s == "p25":
            return float(col.quantile(0.25))
        if s == "p75":
            return float(col.quantile(0.75))
        raise ValueError(f"Unknown KPI statistic: '{stat}'")

    def _compute_kpi_stat_on_df(
        self, df: "pd.DataFrame", stat: str, varname: str
    ) -> float:
        """Compute a KPI statistic on an arbitrary DataFrame.

        Identical to :meth:`_compute_kpi_stat` but operates on *df* instead
        of ``self._df``.  Used for per-facet KPI computation.

        Args:
            df:      DataFrame to compute the statistic on.
            stat:    One of: mean, sum, count, dcount, min, max, median,
                     sd, p25, p50, p75.
            varname: Column name in *df*.

        Returns:
            Computed statistic as a float.

        Raises:
            ValueError: If stat is unknown or varname not in *df*.
        """
        if varname not in df.columns:
            raise ValueError(f"Variable '{varname}' not in DataFrame")
        col = df[varname].dropna()
        s = stat.strip().lower()
        if s == "mean":
            return float(col.mean())
        if s == "sum":
            return float(col.sum())
        if s == "count":
            return float(len(col))
        if s == "dcount":
            return float(col.nunique())
        if s == "min":
            return float(col.min())
        if s == "max":
            return float(col.max())
        if s in ("median", "p50"):
            return float(col.median())
        if s == "sd":
            return float(col.std(ddof=1))
        if s == "p25":
            return float(col.quantile(0.25))
        if s == "p75":
            return float(col.quantile(0.75))
        raise ValueError(f"Unknown KPI statistic: '{stat}'")

    def _format_kpi_value(self, value: float, fmt_str: str) -> str:
        """Format a numeric value using a Stata format string.

        Supports standard Stata numeric formats: %w.df, %w.dfc (comma).

        Args:
            value:   Numeric value to format.
            fmt_str: Stata format string, e.g. "%9.1f" or "%12.0fc".

        Returns:
            Formatted string (stripped of leading/trailing whitespace).
        """
        fmt = fmt_str.strip().lstrip("%")
        use_comma = fmt.endswith("c")
        if use_comma:
            fmt = fmt[:-1]

        try:
            formatted = f"{value:{fmt}}"
        except (ValueError, TypeError):
            formatted = str(value)

        if use_comma:
            parts = formatted.strip().split(".")
            try:
                int_val = int(parts[0].replace(" ", "").replace(",", ""))
                formatted_int = f"{int_val:,}"
                if len(parts) > 1 and parts[1]:
                    formatted = f"{formatted_int}.{parts[1]}"
                else:
                    formatted = formatted_int
            except (ValueError, IndexError):
                pass

        return formatted.strip()

    # ------------------------------------------------------------------
    # ColumnDataSource management
    # ------------------------------------------------------------------

    def _make_source(
        self,
        varnames: list[str],
        df: "pd.DataFrame | None" = None,
    ) -> ColumnDataSource:
        """Create a ``ColumnDataSource`` for the given variable names.

        Only includes columns that exist in ``df`` (defaults to ``self.df``).
        Missing columns are silently skipped to prevent KeyErrors for derived
        variables.

        Args:
            varnames: List of Stata variable names needed by one or more glyphs.
            df:       Optional DataFrame to use instead of ``self.df``.  Pass a
                      pre-filtered slice to implement per-graph if/in filtering.

        Returns:
            A new ``ColumnDataSource`` populated with the requested columns.
        """
        frame = df if df is not None else self.df
        available = [v for v in varnames if v in frame.columns]
        data_dict = {v: frame[v].tolist() for v in available}
        return ColumnDataSource(data=data_dict)

    def _apply_graph_filter(
        self,
        graph_spec: dict,
    ) -> "pd.DataFrame":
        """Return a filtered copy of ``self.df`` based on per-graph if/in qualifiers.

        Security: ``if_expr`` is translated to a pandas query using a restricted
        engine.  Only column names (validated against ``self.df.columns``),
        numeric/string literals, comparison operators, and boolean connectives
        are allowed.  Any expression that fails to parse or contains disallowed
        constructs raises a ``ValueError`` and leaves the DataFrame unfiltered.

        Args:
            graph_spec: A single graph specification dict containing optional
                        ``"if_expr"`` and ``"in_expr"`` keys.

        Returns:
            A (possibly smaller) DataFrame.
        """
        import re as _re
        df = self.df.copy()

        in_expr = (graph_spec.get("in_expr") or "").strip()
        if in_expr:
            # Format: "N/M" → rows N-1 through M-1 (Stata 1-based indexing)
            m = _re.match(r"^(\d+)/(\d+)$", in_expr)
            if m:
                lo = max(0, int(m.group(1)) - 1)
                hi = int(m.group(2))
                df = df.iloc[lo:hi].copy()

        if_expr = (graph_spec.get("if_expr") or "").strip()
        if if_expr:
            # Replace Stata operators with pandas-compatible equivalents
            pandas_expr = (if_expr
                           .replace(" & ", " & ")
                           .replace(" | ", " | ")
                           .replace("!=", "!=")
                           .replace("==", "==")
                           .replace("~=", "!="))

            # Security: validate against AST whitelist before query execution.
            # _validate_if_expr rejects @-variable references (RCE vector),
            # function calls, attribute access, and all non-comparison nodes.
            # This replaces the old regex blacklist which did not block @.
            if not _validate_if_expr(pandas_expr, df.columns):
                import warnings
                warnings.warn(
                    "dash: if_expr filter skipped — invalid syntax "
                    f"(<unknown>, line 1)",
                    stacklevel=2,
                )
            else:
                try:
                    df = df.query(pandas_expr, engine="python")
                except (ValueError, SyntaxError, KeyError, TypeError,
                        NameError) as _qexc:
                    # NameError / pandas.errors.UndefinedVariableError is raised
                    # when a column referenced in if_expr was not serialised by
                    # Stata (e.g. a qualifier-only variable not in the data file).
                    # Degrade gracefully: warn and return the unfiltered DataFrame.
                    import warnings
                    warnings.warn(
                        f"dash: if_expr filter skipped — {_qexc}",
                        stacklevel=2,
                    )

        return df

    @staticmethod
    def _parse_by_raw(by_raw: str) -> "tuple[str, int, bool, bool]":
        """Parse a ``by()`` option value string into its components.

        Handles the Stata syntax ``varlist [, cols(#) total missing]`` where
        the Mata parser passes the entire content of ``by(...)`` as a single
        string.

        Args:
            by_raw: Raw string from ``graph_options["by"]``, e.g.
                    ``"foreign, cols(2) total"`` or just ``"foreign"``.

        Returns:
            A 4-tuple ``(varlist, by_cols, by_total, by_missing)`` where
            *varlist* is the space-separated variable name(s), *by_cols* is
            the requested column count (0 = auto), and *by_total* /
            *by_missing* are boolean flags.
        """
        import re as _re

        if "," in by_raw:
            varlist_part, subopts = by_raw.split(",", 1)
        else:
            varlist_part, subopts = by_raw, ""

        varlist = varlist_part.strip()
        subopts = subopts.strip()

        cols_m = _re.search(r"\bcols?\((\d+)\)", subopts, _re.IGNORECASE)
        by_cols = int(cols_m.group(1)) if cols_m else 0
        by_total = bool(_re.search(r"\btotal\b", subopts, _re.IGNORECASE))
        by_missing = bool(_re.search(r"\bmissing\b", subopts, _re.IGNORECASE))

        return varlist, by_cols, by_total, by_missing

    @staticmethod
    def _parse_filter_raw(raw: str) -> "list[dict]":
        """Parse a raw filter spec string from build_options[\"filter\"] into a
        structured list suitable for the filter-widget loop in ``render()`` and
        ``_setup_sources()``.

        ``dash.ado`` emits ``build_options.filter`` as a plain Stata option
        string, not a JSON array.  Multiple filter specs are joined with ``||``
        (or ``;`` for legacy server-mode compatibility).

        Format::

            "foreign, type(dropdown)"
            "foreign, type(dropdown) || weight, type(range) exclude(h1 d1)"

        Each spec is parsed into::

            {"varname": str, "type": str, "exclude": [str, ...]}

        Security: variable names are validated against the same ``_UNSAFE``
        pattern used elsewhere in the renderer.

        Args:
            raw: Raw filter option string from ``build_options["filter"]``.

        Returns:
            List of filter spec dicts, one per filter widget.  Empty list if
            the input is empty or contains only unsafe characters.
        """
        import re as _re
        _UNSAFE_F = _re.compile(
            r'[;`$\\]|import\s|__|\beval\b|\bexec\b|\bopen\b'
            r'|\bgetattr\b|\bsetattr\b|\bhasattr\b|\bdelattr\b'
        )

        if not raw or raw in ('"', ""):
            return []

        # Normalise separator: treat ";" as "||" for legacy compatibility
        normalized = raw.replace(";", "||")

        result: list[dict] = []
        for part in normalized.split("||"):
            part = part.strip()
            if not part:
                continue
            # Security: reject injection patterns in filter spec
            if _UNSAFE_F.search(part):
                continue
            # Extract variable name: first token before comma or whitespace
            fvar = _re.split(r"[,\s]", part)[0].strip()
            if not fvar:
                continue
            # Validate variable name characters (alphanumeric + underscore only)
            if not _re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', fvar):
                continue
            m_type = _re.search(r"\btype\(([^)]+)\)", part, _re.IGNORECASE)
            m_excl = _re.search(r"\bexclude\(([^)]+)\)", part, _re.IGNORECASE)
            ftype = m_type.group(1).strip().lower() if m_type else "dropdown"
            excl = m_excl.group(1).split() if m_excl else []
            result.append({"varname": fvar, "type": ftype, "exclude": excl})
        return result

    def _expand_by_groups(
        self,
        graph_spec: dict,
        base_df: "pd.DataFrame | None" = None,
    ) -> "list[tuple[str, pd.DataFrame]]":
        """Return a list of ``(facet_label, filtered_df)`` for ``by()`` groups.

        If no ``by()`` option is present, returns ``[("", df)]`` — a single
        group with an empty label so that callers can iterate uniformly.

        Args:
            graph_spec: A single graph specification dict.
            base_df:    Optional pre-filtered DataFrame (e.g. after if/in).
                        Defaults to ``self.df``.

        Returns:
            List of ``(label, DataFrame)`` tuples, one per facet group.
        """
        import re as _re

        df = base_df if base_df is not None else self.df
        graph_opts = graph_spec.get("graph_options", {})
        by_raw = (graph_opts.get("by") or "").strip()
        if not by_raw:
            return [("", df)]

        # Security: reject injection patterns in by-variable names
        _UNSAFE_BY = _re.compile(
            r'[;`$\\]|import\s|__|\beval\b|\bexec\b|\bopen\b'
            r'|\bgetattr\b|\bsetattr\b|\bhasattr\b|\bdelattr\b'
        )
        if _UNSAFE_BY.search(by_raw):
            return [("", df)]

        # Parse varlist + suboptions from the raw by() string
        varlist, by_cols_parsed, by_total_parsed, by_missing_parsed = \
            self._parse_by_raw(by_raw)

        by_vars = varlist.split()
        # Validate that all by-variables exist in the DataFrame
        valid_vars = [v for v in by_vars if v in df.columns]
        if not valid_vars:
            return [("", df)]

        # Honour both the parsed suboptions and any separate graph_options keys
        # (separate keys take precedence for backwards compatibility with tests
        # that set by_total / by_missing directly).
        by_total = (
            by_total_parsed
            or graph_opts.get("by_total", "0") == "1"
        )
        by_missing = (
            by_missing_parsed
            or graph_opts.get("by_missing", "0") == "1"
        )

        work_df = df.copy()
        if not by_missing:
            work_df = work_df.dropna(subset=valid_vars)

        if work_df.empty:
            return [("", df)]

        groups: list[tuple[str, pd.DataFrame]] = []
        # Use a scalar (not list) for single by-var so groupby returns scalar keys
        groupby_key = valid_vars[0] if len(valid_vars) == 1 else valid_vars
        for key, group_df in work_df.groupby(groupby_key, sort=True, dropna=False):
            key_vals = (key,) if len(valid_vars) == 1 else key
            if not by_missing and any(pd.isna(v) for v in key_vals):
                continue
            label = self._facet_label(valid_vars, key)
            groups.append((label, group_df.copy()))

        if by_total:
            groups.append(("Total", work_df.copy()))

        return groups if groups else [("", df)]

    def _facet_label(self, by_vars: list[str], key) -> str:
        """Build a human-readable label for one facet group key.

        Uses Stata value labels when available.

        Args:
            by_vars: List of by-variable names.
            key:     Group key — scalar for single var, tuple for multiple.

        Returns:
            A display string like ``"Domestic"`` or ``"Domestic / 3"``.
        """
        if len(by_vars) == 1:
            keys = [key]
        else:
            keys = list(key)

        parts = []
        for var, val in zip(by_vars, keys):
            if pd.isna(val):
                parts.append("Missing")
                continue
            labelset = self.value_label_names.get(var, "")
            vlabels = self.value_labels.get(labelset, {}) if labelset else {}
            # Fallback: some callers key valueLabels by variable name rather
            # than label-set name (e.g. regen scripts that pre-date the
            # standard Stata jsonio format).
            if not vlabels:
                candidate = self.value_labels.get(var, {})
                if isinstance(candidate, dict):
                    vlabels = candidate
            # Try raw string and int-string lookups for value labels
            str_val = str(val)
            int_str = str(int(val)) if isinstance(val, float) and val == int(val) else str_val
            label = vlabels.get(str_val) or vlabels.get(int_str) or str_val
            parts.append(html.escape(label))
        return " / ".join(parts)

    # ------------------------------------------------------------------
    # Figure construction helpers
    # ------------------------------------------------------------------

    def _axis_label(self, varname: str) -> str:
        """Return the axis label for *varname*, using variable labels if available."""
        return self.variable_labels.get(varname, varname)

    @staticmethod
    def _parse_axis_label_opt(raw: str) -> "tuple[list[float], dict[str, str]]":
        """Parse a Stata xlabel()/ylabel() option string.

        Supports two forms:
          - Pure numeric list:  "0 2 4 6 8"  →  ticks=[0,2,4,6,8], labels={}
          - Labeled list:       '0 "Zero" 5 "Five"'  →  ticks=[0,5], labels={0.0:"Zero",…}

        Invalid tokens are silently dropped.

        Returns:
            (ticks, labels) where ticks is a sorted list of floats and labels
            is a dict mapping str(float) → label string (empty when no labels given).
        """
        import re
        ticks: list[float] = []
        labels: dict[str, str] = {}
        # Tokenise: quoted strings or whitespace/comma-delimited tokens
        tokens = re.findall(r'"([^"]*)"'  # double-quoted label
                            r"|'([^']*)'"  # single-quoted label
                            r"|([^\s,\"']+)",  # bare token (number or keyword)
                            raw)
        i = 0
        flat: list[str] = []
        for dq, sq, bare in tokens:
            flat.append(dq or sq or bare)

        while i < len(flat):
            tok = flat[i]
            try:
                val = float(tok)
                ticks.append(val)
                # Peek ahead: if next token is a quoted label, consume it
                if i + 1 < len(flat):
                    next_tok = flat[i + 1]
                    try:
                        float(next_tok)   # also a number → no label
                    except ValueError:
                        labels[str(val)] = next_tok
                        i += 1
                i += 1
            except ValueError:
                i += 1  # skip non-numeric bare token

        return sorted(ticks), labels

    def _make_figure(
        self,
        graph_spec: dict,
        source: ColumnDataSource,
        facet_view: "Optional[Any]" = None,
    ) -> Any:
        """Build and return a fully-configured Bokeh Figure for one graph spec.

        Args:
            graph_spec: Parsed specification dict for one graph (output of
                        dash_parse.mata).  Contains "plots" and "graph_options".
            source:     The ColumnDataSource assigned to this figure.

        Returns:
            A Bokeh Figure with all glyphs and graph-level options applied.
        """
        graph_opts = graph_spec.get("graph_options", {})
        plots = graph_spec.get("plots", [])

        # Determine axis variables from the first plot layer
        xvar = plots[0].get("xvar", "") if plots else ""
        yvar = plots[0].get("yvar", "") if plots else ""

        # Resolve axis labels: user-specified xtitle/ytitle take priority
        raw_xtitle = graph_opts.get("xtitle", "")
        raw_ytitle = graph_opts.get("ytitle", "")
        x_label = html.escape(raw_xtitle) if raw_xtitle else self._axis_label(xvar)
        y_label = html.escape(raw_ytitle) if raw_ytitle else self._axis_label(yvar)

        # Enable WebGL for large datasets
        n_rows = len(self.df)
        backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"

        # Aspect ratio
        aspect_ratio = None
        raw_ar = graph_opts.get("aspectratio", "")
        if raw_ar:
            try:
                aspect_ratio = float(raw_ar)
            except (ValueError, TypeError):
                pass

        # Log scale and reverse options.
        # Determine axis types BEFORE creating the figure so that we only ever
        # call bokeh_figure() once.  Previously, log scale caused a second
        # bokeh_figure() call that discarded all styling applied after the first
        # call (scheme, bgcolor, plotbgcolor, plotregion, graphregion).
        _xs_log, _xs_rev = _parse_scale_opt(graph_opts.get("xscale", ""))
        _ys_log, _ys_rev = _parse_scale_opt(graph_opts.get("yscale", ""))

        fig_kwargs = dict(
            title=html.escape(graph_opts.get("title", "")),
            x_axis_label=x_label,
            y_axis_label=y_label,
            output_backend=backend,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_select,lasso_select,reset",
        )
        if aspect_ratio is not None:
            fig_kwargs["aspect_ratio"] = aspect_ratio
        if _xs_log:
            fig_kwargs["x_axis_type"] = "log"
        if _ys_log:
            fig_kwargs["y_axis_type"] = "log"

        fig = bokeh_figure(**fig_kwargs)

        # Apply scheme defaults (before explicit graph options so they take precedence)
        self.scheme.apply_to_figure(fig)

        # Figure background colors
        # bgcolor  → border_fill_color  (outer area around the plot)
        # plotbgcolor → background_fill_color (inner plot canvas)
        raw_bgcolor = graph_opts.get("bgcolor", "")
        if raw_bgcolor:
            try:
                fig.border_fill_color = OptionTranslator.translate_mcolor(raw_bgcolor)
            except (ValueError, TypeError):
                pass

        raw_plotbgcolor = graph_opts.get("plotbgcolor", "")
        if raw_plotbgcolor:
            try:
                fig.background_fill_color = OptionTranslator.translate_mcolor(raw_plotbgcolor)
            except (ValueError, TypeError):
                pass

        # plotregion() — inner plot canvas background/border
        # Accepts sub-options: color(X)/fcolor(X) → background_fill_color
        #                      lcolor(X)           → outline_line_color
        #                      lwidth(X)           → outline_line_width
        raw_plotregion = graph_opts.get("plotregion", "")
        if raw_plotregion:
            _pr_bg = _extract_region_color(raw_plotregion)
            if _pr_bg:
                try:
                    fig.background_fill_color = OptionTranslator.translate_mcolor(_pr_bg)
                except (ValueError, TypeError):
                    pass
            _pr_lc = _extract_region_lcolor(raw_plotregion)
            if _pr_lc:
                try:
                    fig.outline_line_color = OptionTranslator.translate_mcolor(_pr_lc)
                except (ValueError, TypeError):
                    pass
            _pr_lw = _extract_region_lwidth(raw_plotregion)
            if _pr_lw is not None:
                try:
                    fig.outline_line_width = _pr_lw
                except (ValueError, TypeError):
                    pass

        # graphregion() — outer graph border / margin area background
        # Accepts sub-options: color(X)/fcolor(X) → border_fill_color
        raw_graphregion = graph_opts.get("graphregion", "")
        if raw_graphregion:
            _gr_bg = _extract_region_color(raw_graphregion)
            if _gr_bg:
                try:
                    fig.border_fill_color = OptionTranslator.translate_mcolor(_gr_bg)
                except (ValueError, TypeError):
                    pass

        # Secondary axes (yaxis(2) / xaxis(2))
        # Detect whether any plot layers request a secondary axis
        from bokeh.models import LinearAxis, LogAxis
        _has_y2 = any(
            str(p.get("options", {}).get("yaxis", "1")).strip() == "2"
            for p in plots
        )
        _has_x2 = any(
            str(p.get("options", {}).get("xaxis", "1")).strip() == "2"
            for p in plots
        )
        if _has_y2:
            from bokeh.models import Range1d as _Range1d
            _y2_lo, _y2_hi = _compute_secondary_range(
                self.df, plots, "yaxis", "yvar", 2
            )
            fig.extra_y_ranges["y2"] = _Range1d(_y2_lo, _y2_hi)
            _y2_scale_raw = graph_opts.get("yscale2", "")
            _y2_log, _y2_rev = _parse_scale_opt(_y2_scale_raw)
            _y2_ax = (LogAxis if _y2_log else LinearAxis)(
                y_range_name="y2",
                axis_label=html.escape(graph_opts.get("ytitle2", "")),
            )
            fig.add_layout(_y2_ax, "right")
            if _y2_rev:
                try:
                    fig.extra_y_ranges["y2"].flipped = True
                except AttributeError:
                    pass
            # Custom ticks for secondary y-axis
            _raw_yla2 = graph_opts.get("ylabel2", "")
            if _raw_yla2:
                from bokeh.models.tickers import FixedTicker
                from bokeh.models.formatters import CustomJSTickFormatter
                _ticks2, _labels2 = self._parse_axis_label_opt(_raw_yla2)
                if _ticks2:
                    _y2_ax.ticker = FixedTicker(ticks=_ticks2)
                    if _labels2:
                        _safe2 = {str(k): html.escape(str(v)) for k, v in _labels2.items()}
                        _y2_ax.formatter = CustomJSTickFormatter(
                            code=f"const m = {json.dumps(_safe2)}; "
                                 "return m[String(tick)] || String(tick);"
                        )
                _ang2 = _parse_axis_angle(_raw_yla2)
                if _ang2 is not None:
                    _y2_ax.major_label_orientation = _ang2
        if _has_x2:
            from bokeh.models import Range1d as _Range1d
            _x2_lo, _x2_hi = _compute_secondary_range(
                self.df, plots, "xaxis", "xvar", 2
            )
            fig.extra_x_ranges["x2"] = _Range1d(_x2_lo, _x2_hi)
            _x2_scale_raw = graph_opts.get("xscale2", "")
            _x2_log, _x2_rev = _parse_scale_opt(_x2_scale_raw)
            _x2_ax = (LogAxis if _x2_log else LinearAxis)(
                x_range_name="x2",
                axis_label=html.escape(graph_opts.get("xtitle2", "")),
            )
            fig.add_layout(_x2_ax, "above")
            if _x2_rev:
                try:
                    fig.extra_x_ranges["x2"].flipped = True
                except AttributeError:
                    pass
            # Custom ticks for secondary x-axis
            _raw_xla2 = graph_opts.get("xlabel2", "")
            if _raw_xla2:
                from bokeh.models.tickers import FixedTicker
                from bokeh.models.formatters import CustomJSTickFormatter
                _ticks2, _labels2 = self._parse_axis_label_opt(_raw_xla2)
                if _ticks2:
                    _x2_ax.ticker = FixedTicker(ticks=_ticks2)
                    if _labels2:
                        _safe2 = {str(k): html.escape(str(v)) for k, v in _labels2.items()}
                        _x2_ax.formatter = CustomJSTickFormatter(
                            code=f"const m = {json.dumps(_safe2)}; "
                                 "return m[String(tick)] || String(tick);"
                        )
                _ang2 = _parse_axis_angle(_raw_xla2)
                if _ang2 is not None:
                    _x2_ax.major_label_orientation = _ang2

        # Axis range limits (xrange / yrange)
        raw_xrange = graph_opts.get("xrange", "")
        if raw_xrange:
            parts = raw_xrange.split()
            if len(parts) >= 2:
                try:
                    from bokeh.models import Range1d
                    fig.x_range = Range1d(float(parts[0]), float(parts[1]))
                except (ValueError, TypeError):
                    pass

        raw_yrange = graph_opts.get("yrange", "")
        if raw_yrange:
            parts = raw_yrange.split()
            if len(parts) >= 2:
                try:
                    from bokeh.models import Range1d
                    fig.y_range = Range1d(float(parts[0]), float(parts[1]))
                except (ValueError, TypeError):
                    pass

        # Apply axis reversal (after any Range1d replacement so flipped sticks)
        if _xs_rev:
            try:
                fig.x_range.flipped = True
            except AttributeError:
                pass
        if _ys_rev:
            try:
                fig.y_range.flipped = True
            except AttributeError:
                pass

        # Reference lines
        # Reference lines — support both string "xline"/"yline" (parser output)
        # and legacy list "xline_values"/"yline_values" forms.
        def _parse_refline(opt_key: str, list_key: str) -> list:
            """Return a flat list of numeric strings/values for a reference line option."""
            raw = graph_opts.get(opt_key, "")
            if raw:
                # String from Mata parser: space- or comma-separated numbers
                return [v.strip() for v in raw.replace(",", " ").split() if v.strip()]
            return graph_opts.get(list_key, [])

        for xline_val in _parse_refline("xline", "xline_values"):
            try:
                fig.add_layout(Span(location=float(xline_val),
                                    dimension="height",
                                    line_color="gray", line_dash="dashed"))
            except (ValueError, TypeError):
                pass
        for yline_val in _parse_refline("yline", "yline_values"):
            try:
                fig.add_layout(Span(location=float(yline_val),
                                    dimension="width",
                                    line_color="gray", line_dash="dashed"))
            except (ValueError, TypeError):
                pass

        # Note / caption annotations
        from bokeh.models import Label
        for ann_key in ("note", "caption"):
            ann_text = graph_opts.get(ann_key, "")
            if ann_text:
                lbl = Label(
                    x=0, y=0,
                    x_units="screen", y_units="screen",
                    text=html.escape(ann_text),
                    text_font_size="11px",
                    text_color="#555555",
                )
                fig.add_layout(lbl, "below")

        # Subtitle annotation (appears above the plot area)
        subtitle_text = graph_opts.get("subtitle", "")
        if subtitle_text:
            subtitle_lbl = Label(
                x=0, y=0,
                x_units="screen", y_units="screen",
                text=html.escape(subtitle_text),
                text_font_size="13px",
                text_color="#444444",
            )
            fig.add_layout(subtitle_lbl, "above")

        # Custom axis tick values (xlabel / ylabel) and label rotation
        from bokeh.models.tickers import FixedTicker
        from bokeh.models.formatters import CustomJSTickFormatter
        for ax_key, axis_obj in (("xlabel", fig.xaxis), ("ylabel", fig.yaxis)):
            raw_ax = graph_opts.get(ax_key, "")
            if not raw_ax:
                continue
            ticks, labels = self._parse_axis_label_opt(raw_ax)
            if ticks:
                axis_obj.ticker = FixedTicker(ticks=ticks)
                if labels:
                    # Build a safe JS lookup dict; keys and values are HTML-escaped
                    safe_labels = {
                        str(k): html.escape(str(v)) for k, v in labels.items()
                    }
                    js_map = json.dumps(safe_labels)
                    axis_obj.formatter = CustomJSTickFormatter(
                        code=f"const m = {js_map}; return m[String(tick)] || String(tick);"
                    )
            angle_rad = _parse_axis_angle(raw_ax)
            if angle_rad is not None:
                axis_obj.major_label_orientation = angle_rad

        # Plot categories that use non-standard JSON variable keys
        _RANGE_TYPES = frozenset({
            "rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
            "rcapsym", "tsrline", "rscatter",
        })
        _UNIVARIATE_TYPES = frozenset({"histogram", "hist", "kdensity"})
        _PC_TYPES = frozenset({"pcspike", "pcarrow", "pcbarrow"})

        # Add glyphs for each plot layer
        for pi, plot in enumerate(plots):
            ptype = plot.get("type", "scatter")
            pxvar = plot.get("xvar", xvar)
            popts = plot.get("options", {})

            # Determine secondary axis assignments for this plot layer
            _plot_yaxis = str(popts.get("yaxis", "1")).strip()
            _plot_xaxis = str(popts.get("xaxis", "1")).strip()
            _use_y2 = _has_y2 and _plot_yaxis == "2"
            _use_x2 = _has_x2 and _plot_xaxis == "2"

            # Snapshot renderer list so new glyphs can be identified
            _r_before = len(fig.renderers)

            if ptype.lower() == "scatteri":
                # Inline coordinate list — no shared source variable needed
                self.mapper.map_scatteri(fig, plot.get("values", []), popts, color_idx=pi)
            elif ptype.lower() in _PC_TYPES:
                py1var = plot.get("y1var", "")
                px1var = plot.get("x1var", "")
                py2var = plot.get("y2var", "")
                px2var = plot.get("x2var", "")
                self._add_pc_glyph(fig, source, ptype, py1var, px1var, py2var, px2var, popts,
                                   view=facet_view, color_idx=pi)
            elif ptype.lower() in _RANGE_TYPES:
                py1var = plot.get("yvar1", "")
                py2var = plot.get("yvar2", "")
                self._add_glyph(fig, source, ptype, py1var, pxvar, popts,
                                y2var=py2var, view=facet_view, color_idx=pi)
            elif ptype.lower() in _UNIVARIATE_TYPES:
                pyvar = (plot.get("yvar", "") or plot.get("var", "")
                         or yvar)
                self._add_glyph(fig, source, ptype, pyvar, pxvar, popts,
                                view=facet_view, color_idx=pi)
            elif ptype.lower() == "function":
                pexpr = plot.get("expr", "")
                x_lo, x_hi = 0.0, 1.0
                n_pts = 200
                if "range" in popts:
                    parts = popts["range"].split()
                    if len(parts) >= 2:
                        try:
                            x_lo, x_hi = float(parts[0]), float(parts[1])
                        except ValueError:
                            pass
                if "n" in popts:
                    try:
                        # Cap point count to prevent resource exhaustion
                        n_pts = min(int(popts["n"]), 10000)
                        n_pts = max(n_pts, 2)
                    except ValueError:
                        pass
                self.mapper.map_function(fig, pexpr, (x_lo, x_hi), n_pts, popts)
            else:
                pyvar = plot.get("yvar", yvar)
                self._add_glyph(fig, source, ptype, pyvar, pxvar, popts,
                                view=facet_view, color_idx=pi)

            # Assign secondary axis range names to newly added renderers
            if _use_y2 or _use_x2:
                for _r in fig.renderers[_r_before:]:
                    try:
                        if _use_y2:
                            _r.y_range_name = "y2"
                        if _use_x2:
                            _r.x_range_name = "x2"
                    except AttributeError:
                        pass

        # Restrict DataRange1d to primary-source renderers only.
        # Computed-glyph renderers (lfit, histogram, qfit, etc.) use separate
        # ColumnDataSources with different row counts/ranges.  Without this
        # restriction those sources expand the axis range, making the plot
        # wider or taller than the scatter data warrants.  With this fix the
        # axes auto-range based only on the actual data points, while the fit
        # lines (whose x_fit was extended by 10% to match Bokeh's padding) span
        # exactly to the visible edge of the plot area.
        _primary_renderers = [
            r for r in fig.renderers
            if hasattr(r, "data_source") and r.data_source is source
        ]
        if _primary_renderers:
            if isinstance(fig.x_range, DataRange1d):
                fig.x_range.renderers = _primary_renderers
            if isinstance(fig.y_range, DataRange1d):
                fig.y_range.renderers = _primary_renderers

        # Legend placement and label overrides — must run after glyphs are added
        # so that legend items exist and can be manipulated.
        legend_opt = graph_opts.get("legend", "")
        if legend_opt:
            loc_map = {
                "off": None,
                "on": "top_right",
                "ring": "top_right",
                "top": "top_center",
                "bottom": "bottom_center",
                "left": "center_left",
                "right": "center_right",
            }
            if legend_opt == "off":
                for leg in fig.legend:
                    leg.visible = False
            else:
                # Apply position keyword if present (check for keywords in string)
                for kw, loc in loc_map.items():
                    if kw != "off" and loc and re.search(r'\b' + re.escape(kw) + r'\b', legend_opt):
                        for leg in fig.legend:
                            leg.location = loc
                        break

                # Parse label(N "text") overrides — e.g. label(1 "First") label(2 "Second")
                # Security: HTML-escape label text to prevent XSS
                label_overrides: dict[int, str] = {}
                for m in re.finditer(r'label\(\s*(\d+)\s+"([^"]*)"\s*\)', legend_opt):
                    idx = int(m.group(1))
                    text = html.escape(m.group(2))
                    label_overrides[idx] = text
                if label_overrides and fig.legend:
                    items = fig.legend[0].items
                    for n, text in label_overrides.items():
                        item_idx = n - 1  # Stata uses 1-based indexing
                        if 0 <= item_idx < len(items):
                            items[item_idx].label = {"value": text}

                # cols(#) / rows(#) — multi-column/row legend layout
                m_cols = re.search(r'\bcols\s*\(\s*(\d+)\s*\)', legend_opt)
                m_rows = re.search(r'\brows\s*\(\s*(\d+)\s*\)', legend_opt)
                if m_cols:
                    try:
                        ncols = int(m_cols.group(1))
                        for leg in fig.legend:
                            leg.ncols = ncols
                    except (ValueError, AttributeError):
                        pass
                if m_rows:
                    try:
                        nrows = int(m_rows.group(1))
                        for leg in fig.legend:
                            leg.nrows = nrows
                    except (ValueError, AttributeError):
                        pass

        # ---- Comprehensive HoverTool ----
        # Build a comprehensive hover tool to show primary vars + any extras
        # listed in graph_options["hover"].  Always add this to ensure consistent
        # tooltips across all renderers and layouts (especially Bootstrap tabs).
        # If extra hover vars are requested, remove any existing hover tools first.
        _hover_extra_str = graph_opts.get("hover", "").strip()
        _hover_extra = _hover_extra_str.split() if _hover_extra_str else []
        _has_hover = any(isinstance(t, HoverTool) for t in fig.tools)
        if _has_hover and _hover_extra:
            # Remove existing hover tools before adding comprehensive one with extras
            fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]
        if True:  # Always build and add comprehensive hover
            # For range plots (rbar, rcap, rspike, rline, rarea, rconnected),
            # plots[0] uses yvar1/yvar2 keys rather than yvar.
            _p0 = plots[0] if plots else {}
            _yvar_eff = yvar or _p0.get("yvar1", "")
            _y2var_eff = _p0.get("yvar2", "")
            _hover_seen: set = set()
            _hover_fields: list = []
            if xvar and xvar in source.data:
                _hover_fields.append((xvar, f"@{{{xvar}}}"))
                _hover_seen.add(xvar)
            if _yvar_eff and _yvar_eff not in _hover_seen and _yvar_eff in source.data:
                _hover_fields.append((_yvar_eff, f"@{{{_yvar_eff}}}"))
                _hover_seen.add(_yvar_eff)
            if _y2var_eff and _y2var_eff not in _hover_seen and _y2var_eff in source.data:
                _hover_fields.append((_y2var_eff, f"@{{{_y2var_eff}}}"))
                _hover_seen.add(_y2var_eff)
            for _hv in _hover_extra:
                if _hv not in _hover_seen and _hv in source.data:
                    _hover_fields.append((_hv, f"@{{{_hv}}}"))
                    _hover_seen.add(_hv)
            if _hover_fields:
                # Restrict hover to renderers whose CDS contains every
                # referenced column.  Fit-line, density, and histogram
                # renderers use independent CDS objects with generic column
                # names ("x"/"y", "top"/"left"/"right") — hovering over them
                # with field specs that reference original variable names
                # (e.g. "@{mpg}") would return "???" in the tooltip.
                _hover_col_set = {f[0] for f in _hover_fields}
                _data_renderers = [
                    _rend for _rend in fig.renderers
                    if hasattr(_rend, "data_source") and
                    all(c in _rend.data_source.data for c in _hover_col_set)
                ]

                if _data_renderers:
                    fig.add_tools(HoverTool(tooltips=_hover_fields,
                                            renderers=_data_renderers))
                else:
                    # No renderer carries these exact columns (e.g. a
                    # histogram-only figure).  Fall back to a generic tooltip
                    # built from the first renderer's actual CDS columns so
                    # something meaningful is shown rather than "???".
                    _fb_rends = [_r for _r in fig.renderers
                                 if hasattr(_r, "data_source")]
                    if _fb_rends:
                        _fb_src = _fb_rends[0].data_source
                        _fb_fields: list = []
                        _fb_mode = "mouse"
                        # Histogram: "left"/"right" are bin edges, "top" = count
                        # Use mode="vline" so the hover fires anywhere within a
                        # bin's x-range — quad hit-testing requires the cursor
                        # to land exactly on the bar, which is unreliable.
                        if "top" in _fb_src.data and "left" in _fb_src.data:
                            _bin_var = _yvar_eff or "value"
                            _fb_fields = [
                                (_bin_var,  "@{left}{0.2f} to @{right}{0.2f}"),
                                ("Count",   "@{top}"),
                            ]
                            _fb_mode = "vline"
                        # KDE / fit line: "x" and "y" columns
                        elif "x" in _fb_src.data and "y" in _fb_src.data:
                            _fb_fields = [
                                (xvar or "x",     "@{x}{0.3f}"),
                                (_yvar_eff or "y", "@{y}{0.4f}"),
                            ]
                        if _fb_fields:
                            fig.add_tools(HoverTool(tooltips=_fb_fields,
                                                    renderers=_fb_rends[:1],
                                                    mode=_fb_mode))

        return fig

    def _add_glyph(
        self,
        fig: Any,
        source: ColumnDataSource,
        plot_type: str,
        yvar: str,
        xvar: str,
        options: dict,
        y2var: str = "",
        view=None,
        color_idx: int = 0,
    ) -> None:
        """Dispatch a single plot layer to the correct GlyphMapper method.

        Args:
            fig:        Bokeh Figure to add the glyph to.
            source:     ColumnDataSource.
            plot_type:  Stata twoway plot type name.
            yvar:       y variable name (or y1var for range plots).
            xvar:       x variable name.
            options:    Plot-level options dict.
            y2var:      Second y variable for range plot types (empty for
                        non-range plots).
            color_idx:  Zero-based plot index for scheme color cycling.
        """
        # Standard (yvar, xvar) dispatch
        dispatch = {
            "scatter":    self.mapper.map_scatter,
            "sc":         self.mapper.map_scatter,
            "line":       self.mapper.map_line,
            "li":         self.mapper.map_line,
            "connected":  self.mapper.map_connected,
            "area":       self.mapper.map_area,
            "bar":        self.mapper.map_bar,
            "spike":      self.mapper.map_spike,
            "lfit":       self.mapper.map_lfit,
            "qfit":       self.mapper.map_qfit,
            "lfitci":     self.mapper.map_lfitci,
            "qfitci":     self.mapper.map_qfitci,
            "lowess":     self.mapper.map_lowess,
            "lpoly":      self.mapper.map_lpoly,
            "lpolyci":    self.mapper.map_lpolyci,
            "fpfit":      self.mapper.map_fpfit,
            "fpfitci":    self.mapper.map_fpfitci,
            "histogram":  self.mapper.map_histogram,
            "hist":       self.mapper.map_histogram,
            "kdensity":   self.mapper.map_kdensity,
            "dot":        self.mapper.map_dot,
            "dropline":   self.mapper.map_dropline,
            "tsline":     self.mapper.map_tsline,
            "mspline":    self.mapper.map_mspline,
            "mband":      self.mapper.map_mband,
        }
        # Range plot (y1var, y2var, xvar) dispatch
        range_dispatch = {
            "rarea":      self.mapper.map_rarea,
            "rbar":       self.mapper.map_rbar,
            "rspike":     self.mapper.map_rspike,
            "rcap":       self.mapper.map_rcap,
            "rline":      self.mapper.map_rline,
            "rconnected": self.mapper.map_rconnected,
            "rcapsym":    self.mapper.map_rcapsym,
            "tsrline":    self.mapper.map_tsrline,
            "rscatter":   self.mapper.map_rscatter,
        }

        pt = plot_type.lower()

        # Guard: skip glyph if required variables are missing from the CDS
        _pc_types = frozenset({"pcspike", "pcarrow", "pcbarrow", "pci", "pcscatter"})
        if pt not in _pc_types:
            _vars_needed = [v for v in [yvar, xvar, y2var] if v]
            if _vars_needed and not self.mapper._check_vars(source, *_vars_needed):
                return

        # Range plots: (fig, source, y1var, y2var, xvar, options)
        rfn = range_dispatch.get(pt)
        if rfn is not None and y2var:
            rfn(fig, source, yvar, y2var, xvar, options, view=view, color_idx=color_idx)
            return

        fn = dispatch.get(pt)
        if fn is not None:
            # histogram and kdensity are univariate — no xvar positional arg
            if pt in ("histogram", "hist", "kdensity"):
                fn(fig, source, yvar, options, view=view, color_idx=color_idx)
            else:
                fn(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)

    def _add_pc_glyph(
        self,
        fig: Any,
        source: ColumnDataSource,
        plot_type: str,
        y1var: str,
        x1var: str,
        y2var: str,
        x2var: str,
        options: dict,
        view=None,
        color_idx: int = 0,
    ) -> None:
        """Dispatch a paired-coordinate plot layer to the correct GlyphMapper method.

        Args:
            fig:        Bokeh Figure to add the glyph to.
            source:     ColumnDataSource.
            plot_type:  Paired-coordinate plot type name (pcspike, pcarrow, pcbarrow,
                        pci, pcscatter).
            y1var:      Start y variable name.
            x1var:      Start x variable name.
            y2var:      End y variable name.
            x2var:      End x variable name.
            options:    Plot-level options dict.
            color_idx:  Zero-based plot index for scheme color cycling.
        """
        pc_dispatch = {
            "pcspike":   self.mapper.map_pcspike,
            "pcarrow":   self.mapper.map_pcarrow,
            "pcbarrow":  self.mapper.map_pcbarrow,
            "pci":       self.mapper.map_pci,
            "pcscatter": self.mapper.map_pcscatter,
        }
        fn = pc_dispatch.get(plot_type.lower())
        if fn is not None:
            _pc_needed = [v for v in [y1var, x1var, y2var, x2var] if v]
            if _pc_needed and not self.mapper._check_vars(source, *_pc_needed):
                return
            fn(fig, source, y1var, x1var, y2var, x2var, options, view=view, color_idx=color_idx)

    # ------------------------------------------------------------------
    # KPI card construction
    # ------------------------------------------------------------------

    def _make_kpi_div(self, kpi_def: dict) -> Div:
        """Build a styled KPI Div widget from a KPI definition dict.

        Args:
            kpi_def: Dict with keys: title, value, fmt, subtitle, color,
                     bgcolor, update.

        Returns:
            A Bokeh Div widget with inline-styled HTML.
        """
        title    = html.escape(kpi_def.get("title", ""))
        value    = html.escape(str(kpi_def.get("value", "")))
        subtitle = html.escape(kpi_def.get("subtitle", ""))
        color    = html.escape(kpi_def.get("color", "") or "#212529")
        bgcolor  = html.escape(kpi_def.get("bgcolor", "") or "#f8f9fa")

        html_content = f"""
<div style="background:{bgcolor}; border-radius:8px; padding:20px;
            text-align:center; border:1px solid #dee2e6;
            min-width:160px; min-height:110px;">
  <div style="font-size:13px; color:#6c757d; margin-bottom:6px;">{title}</div>
  <div id="kpi_val_{html.escape(kpi_def.get('name','kpi'))}"
       style="font-size:36px; font-weight:bold; color:{color};">{value}</div>
  <div style="font-size:11px; color:#6c757d; margin-top:4px;">{subtitle}</div>
</div>"""
        return Div(text=html_content, sizing_mode="stretch_width")

    # ------------------------------------------------------------------
    # Bootstrap layout helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_bootstrap_layout(layout_opt: str) -> bool:
        """Return True when *layout_opt* requests a Bootstrap grid layout.

        Bootstrap layouts start with the literal token ``bs`` (case-insensitive),
        optionally followed by a colon and an explicit column-span specification::

            layout(bs)                              # auto layout
            layout(bs: k1=3 k2=3 / s1=8 h1=4)     # explicit layout
        """
        return bool(layout_opt) and layout_opt.strip().lower().startswith("bs")

    @staticmethod
    def _auto_bs_layout(
        all_names: "list[str]",
        kpi_names: "list[str]",
    ) -> "list[list[tuple[str, int]]]":
        """Generate an automatic Bootstrap layout.

        KPI cards are placed in a first row with equal column spans (up to 4 per
        row).  Graphs fill subsequent rows at two per row (``col-6`` each), or
        three per row when there are six or more graphs (``col-4`` each).

        Args:
            all_names:  All dashboard element names in display order.
            kpi_names:  Subset of *all_names* that are KPI card names.

        Returns:
            A list of rows, each row being a list of ``(name, col_span)`` tuples.
        """
        graph_names = [n for n in all_names if n not in kpi_names]
        rows: list[list[tuple[str, int]]] = []

        # ---- KPI row(s) ----
        if kpi_names:
            n_kpis = len(kpi_names)
            # Up to 4 KPIs per row; span = 12 // per_row
            per_row = min(n_kpis, 4)
            span = max(1, 12 // per_row)
            for i in range(0, n_kpis, per_row):
                chunk = kpi_names[i : i + per_row]
                rows.append([(name, span) for name in chunk])

        # ---- Graph row(s) ----
        if graph_names:
            n_graphs = len(graph_names)
            if n_graphs == 1:
                per_row = 1
            elif n_graphs <= 4:
                per_row = 2
            else:
                per_row = 3
            span = max(1, 12 // per_row)
            for i in range(0, n_graphs, per_row):
                chunk = graph_names[i : i + per_row]
                rows.append([(name, span) for name in chunk])

        return rows if rows else [[(n, 12 // max(1, len(all_names))) for n in all_names]]

    @staticmethod
    def _parse_bs_layout(
        layout_opt: str,
        all_names: "list[str]",
        kpi_names: "list[str]",
    ) -> "list[list[tuple[str, int]]]":
        """Parse a Bootstrap layout string into rows of ``(name, col_span)`` pairs.

        Syntax::

            bs                              # automatic layout
            bs: name=N ...                  # explicit; / separates rows
            bs: k1=3 k2=3 / s1=8 h1=4

        Column spans are integers in ``[1, 12]``.  Items missing from the spec
        that are present in *all_names* are appended as full-width (``col-12``)
        entries after the last explicit row.

        Security:
            Name tokens are validated against *all_names*; unknown tokens are
            silently dropped.  Span values are clamped to ``[1, 12]``.

        Args:
            layout_opt:  The raw ``layout()`` option string, must start with ``bs``.
            all_names:   All dashboard element names (KPIs first, then graphs).
            kpi_names:   Subset of *all_names* that are KPI card names.

        Returns:
            List of rows, each a list of ``(name, col_span)`` tuples.
        """
        stripped = layout_opt.strip()
        # Pure "bs" or "bs " — auto layout
        if re.match(r"^bs\s*$", stripped, re.IGNORECASE):
            return DashRenderer._auto_bs_layout(all_names, kpi_names)

        # Explicit: "bs: <spec>"
        m = re.match(r"^bs\s*:\s*(.+)$", stripped, re.IGNORECASE | re.DOTALL)
        if not m:
            return DashRenderer._auto_bs_layout(all_names, kpi_names)

        spec_str = m.group(1)
        valid_names = set(all_names)
        placed: set[str] = set()
        rows: list[list[tuple[str, int]]] = []

        for row_str in spec_str.split("/"):
            row: list[tuple[str, int]] = []
            for token in row_str.split():
                token = token.strip()
                if not token:
                    continue
                if "=" in token:
                    parts = token.split("=", 1)
                    name = parts[0].strip()
                    try:
                        span = max(1, min(12, int(parts[1].strip())))
                    except (ValueError, TypeError):
                        span = 6
                else:
                    name = token
                    span = 6  # default span when not specified
                # Security: only accept names present in the registry
                if name in valid_names:
                    row.append((name, span))
                    placed.add(name)
            if row:
                rows.append(row)

        # Append any names not mentioned in the spec as full-width rows
        unplaced = [n for n in all_names if n not in placed]
        for name in unplaced:
            rows.append([(name, 12)])

        return rows if rows else DashRenderer._auto_bs_layout(all_names, kpi_names)

    def _render_bootstrap_html(
        self,
        layout_opt: str,
        all_names: "list[str]",
        kpi_names: "list[str]",
        filter_row_widgets: list,
        title_text: str,
        subtitle_text: str,
        tabs_widget: "Any | None" = None,
        tabbed_names: "set[str] | None" = None,
        filter_position: str = "top",
    ) -> str:
        """Build the final HTML document using a Bootstrap-compatible grid.

        Uses ``bokeh.embed.components()`` to obtain individual ``<div>``
        elements for each Bokeh model and arranges them in the
        :data:`_DASH_GRID_CSS` flexbox 12-column grid.

        Linked brushing and ``CustomJS`` filter callbacks continue to work
        because ``components()`` serialises the entire Bokeh model graph — all
        shared ``ColumnDataSource`` and ``CustomJS`` references — into one
        ``<script>`` block.

        Args:
            layout_opt:          Raw ``layout()`` option string (starts with
                                 ``bs``).
            all_names:           All dashboard element names in display order.
            kpi_names:           Subset that are KPI card names.
            filter_row_widgets:  Bokeh widget models for the filter area.
            title_text:          Dashboard title (may be empty).
            subtitle_text:       Dashboard subtitle (may be empty).
            tabs_widget:         Optional Bokeh ``Tabs`` model containing all
                                 tabbed figures.  When present, tabbed figures
                                 are not added individually to the grid.
            tabbed_names:        Set of element names already placed inside
                                 *tabs_widget*.  These are excluded from the
                                 Bootstrap grid.
            filter_position:     ``"top"`` (horizontal filter bar above the
                                 content) or ``"left"`` (vertical sidebar).

        Returns:
            Complete HTML string.
        """
        import html as _html

        if tabbed_names is None:
            tabbed_names = set()

        # Only names NOT assigned to a tab appear in the Bootstrap grid.
        grid_names = [n for n in all_names if n not in tabbed_names]

        # Parse Bootstrap layout for grid items (KPIs + non-tabbed graphs).
        bs_rows = DashRenderer._parse_bs_layout(layout_opt, grid_names, kpi_names)

        # ---- Collect all Bokeh models ----
        # file_html() + components() must share the same document; both calls
        # discover all transitively-referenced models, so we only pass each
        # root model once.
        all_models: list[Any] = []
        model_keys: list[str] = []

        # 1. Bokeh Tabs widget (contains all tabbed figures recursively)
        if tabs_widget is not None:
            all_models.append(tabs_widget)
            model_keys.append("__tabs__")

        # 2. Grid items — KPIs and non-tabbed graphs
        _added: set[str] = set()
        for row_spec in bs_rows:
            for name, _ in row_spec:
                if name in _added:
                    continue
                if name in self.kpi_divs:
                    all_models.append(self.kpi_divs[name])
                    model_keys.append(name)
                    _added.add(name)
                elif name in self.figures and name not in tabbed_names:
                    all_models.append(self.figures[name])
                    model_keys.append(name)
                    _added.add(name)

        # 3. Filter widgets
        for fw_idx, widget in enumerate(filter_row_widgets):
            all_models.append(widget)
            model_keys.append(f"__fw_{fw_idx}__")

        if not all_models:
            return (
                "<!DOCTYPE html><html><body>"
                "<p style='font-family:sans-serif'>No dashboard content.</p>"
                "</body></html>"
            )

        # ---- Extract minimal Bokeh JS/CSS via file_html() ----
        # file_html() with INLINE selects only the resource bundles needed by
        # this specific model tree (~1.5 MB vs ~3.5 MB from render_js()).
        # Must be called BEFORE components() to avoid document-ownership errors.
        _dummy_col = column(*all_models, sizing_mode="stretch_width")
        _dummy_html = file_html(_dummy_col, INLINE, title=title_text or "dash")
        _head_m = re.search(r"(?s)<head>(.*?)</head>", _dummy_html)
        _extracted_head = _head_m.group(1) if _head_m else ""

        # ---- Get individual Bokeh component divs ----
        script_tag, div_list = components(all_models)
        name_to_div: dict[str, str] = dict(zip(model_keys, div_list))

        # ---- Build common HTML sections ----
        header_html = ""
        if title_text:
            header_html += (
                f'<h2 class="db-title">{_html.escape(title_text)}</h2>\n'
            )
        if subtitle_text:
            header_html += (
                f'<p class="db-subtitle">{_html.escape(subtitle_text)}</p>\n'
            )

        # Bootstrap grid for KPI cards and non-tabbed graphs
        grid_parts: list[str] = []
        for row_spec in bs_rows:
            row_items = [
                (span, name_to_div[name])
                for name, span in row_spec
                if name_to_div.get(name)
            ]
            if not row_items:
                continue
            grid_parts.append('<div class="db-row db-section">')
            for span, div_html in row_items:
                grid_parts.append(
                    f'<div class="db-col-12 db-col-sm-12 db-col-md-{span}">'
                    f"{div_html}"
                    "</div>"
                )
            grid_parts.append("</div>")
        grid_section_html = "\n".join(grid_parts)

        # Tabs widget section
        tabs_section_html = ""
        if "__tabs__" in name_to_div:
            tabs_section_html = (
                '<div class="db-row db-section">'
                '<div class="db-col-md-12">'
                + name_to_div["__tabs__"]
                + "</div></div>"
            )

        # Filter widget divs (order matches filter_row_widgets)
        fw_divs = [
            name_to_div.get(f"__fw_{i}__", "")
            for i in range(len(filter_row_widgets))
        ]

        # ---- Assemble page layout ----
        scheme_css_block = self.scheme.css_block()
        safe_title = _html.escape(title_text or "dash")

        if filter_position == "left" and filter_row_widgets:
            # Vertical sidebar: filters in a narrow left column, content on right
            sidebar_items_html = "\n".join(
                f'<div class="db-sidebar-item">{d}</div>'
                for d in fw_divs
                if d
            )
            page_body_html = (
                '<div class="db-row">\n'
                '  <div class="db-col-12 db-col-sm-12 db-col-md-2 db-sidebar-col">\n'
                '    <div class="db-sidebar-label">Filters</div>\n'
                f"    {sidebar_items_html}\n"
                "  </div>\n"
                '  <div class="db-col-12 db-col-sm-12 db-col-md-10">\n'
                f"    {header_html}"
                f"    {grid_section_html}\n"
                f"    {tabs_section_html}\n"
                "  </div>\n"
                "</div>\n"
            )
        else:
            # Horizontal filter bar above main content
            filter_bar_html = ""
            if any(fw_divs):
                items_html = "\n".join(
                    f'<div class="db-col-auto">{d}</div>'
                    for d in fw_divs
                    if d
                )
                filter_bar_html = (
                    '<div class="db-row db-filter-bar">\n'
                    + items_html
                    + "\n</div>\n"
                )
            page_body_html = (
                f"{filter_bar_html}"
                f"{header_html}"
                f"{grid_section_html}\n"
                f"{tabs_section_html}\n"
            )

        html_str = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            f"{_extracted_head}\n"
            f"  {_CSP_META}\n"
            "  <style>\n"
            f"{_DASH_GRID_CSS}\n"
            f"{scheme_css_block}\n"
            "  </style>\n"
            "</head>\n"
            "<body>\n"
            f"{script_tag}\n"
            '<div class="db-container">\n'
            f"{page_body_html}"
            "</div>\n"
            "</body>\n"
            "</html>"
        )
        return html_str

    @staticmethod
    def _parse_tabs_option(
        tabs_str: str,
        all_names: "list[str]",
    ) -> "list[tuple[str, list[str]]] | None":
        """Parse a ``tabs()`` option string into ``(tab_title, [names])`` pairs.

        Syntax::

            tabname: name1 name2 ... / tabname2: name3 name4 ...

        Tab names are title-cased.  Names absent from *all_names* are silently
        dropped (security: only registered dashboard element names are accepted).

        Args:
            tabs_str:   Raw ``tabs()`` option string from ``build_options``.
            all_names:  All registered dashboard element names.

        Returns:
            List of ``(title, [names])`` tuples, or ``None`` when *tabs_str*
            is empty or produces no valid entries.
        """
        if not tabs_str or not tabs_str.strip():
            return None
        valid = set(all_names)
        result: list[tuple[str, list[str]]] = []
        for i, segment in enumerate(tabs_str.split("/")):
            segment = segment.strip()
            if not segment:
                continue
            if ":" in segment:
                tab_name_raw, items_str = segment.split(":", 1)
                tab_name = tab_name_raw.strip().title()
                items = [n.strip() for n in items_str.split() if n.strip()]
            else:
                items = [n.strip() for n in segment.split() if n.strip()]
                tab_name = f"Tab {i + 1}"
            # Security: only accept names present in the registry
            safe_items = [n for n in items if n in valid]
            if safe_items:
                result.append((tab_name, safe_items))
        return result if result else None

    def _build_tabs_widget(
        self,
        tabs_spec: "list[tuple[str, list[str]]]",
    ) -> "tuple[Any, set[str]]":
        """Build a Bokeh ``Tabs`` widget from a parsed tab specification.

        Each tab's content is laid out as a ``gridplot`` (``ceil(sqrt(N))``
        columns, ``sizing_mode="stretch_width"``) so figures scale to fill the
        available width when the tab is selected.

        Args:
            tabs_spec: List of ``(tab_title, [name, ...])`` from
                       :meth:`_parse_tabs_option`.

        Returns:
            A ``(Tabs, placed_names)`` tuple.  *placed_names* is the set of
            dashboard element names included in the widget so that the caller
            can omit them from the Bootstrap grid.
        """
        placed: set[str] = set()
        tab_panels: list[Any] = []

        for tab_title, names in tabs_spec:
            items: list[Any] = []
            for name in names:
                if name in self._facet_map:
                    for fkey, _label in self._facet_map[name]:
                        fig = self.figures.get(fkey)
                        if fig is not None:
                            items.append(fig)
                    placed.add(name)
                elif name in self.figures:
                    items.append(self.figures[name])
                    placed.add(name)
                elif name in self.kpi_divs:
                    items.append(self.kpi_divs[name])
                    placed.add(name)

            if not items:
                continue

            n = len(items)
            cols_per_row = max(1, math.ceil(math.sqrt(n)))
            rows = [
                items[i : i + cols_per_row]
                for i in range(0, n, cols_per_row)
            ]
            # Pad the last row so gridplot doesn't error on ragged rows
            while len(rows[-1]) < cols_per_row:
                rows[-1].append(None)

            tab_content = gridplot(rows, sizing_mode="stretch_width")
            tab_panels.append(TabPanel(child=tab_content, title=tab_title))

        if not tab_panels:
            return None, placed

        tabs_widget = Tabs(tabs=tab_panels, sizing_mode="stretch_width")
        return tabs_widget, placed

    # ------------------------------------------------------------------
    # Layout assembly helpers
    # ------------------------------------------------------------------

    def _compute_grid(
        self,
        names_or_n: "int | list[str]",
        layout_opt: str,
    ) -> tuple[int, int]:
        """Return (rows, cols) for the dashboard grid.

        Args:
            names_or_n: Either an integer count or a list of graph/KPI names.
            layout_opt: The layout() option string from dash build, e.g.
                        "2 2", "auto", or "s1:1,1 s2:1,2".

        Returns:
            A (rows, cols) integer tuple.
        """
        n = names_or_n if isinstance(names_or_n, int) else len(names_or_n)
        if not layout_opt or layout_opt.strip().lower() == "auto":
            cols = math.ceil(math.sqrt(n)) if n > 0 else 1
            rows = math.ceil(n / cols) if cols > 0 else 1
            return rows, cols

        parts = layout_opt.strip().split()
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                pass

        # Fallback: auto
        cols = math.ceil(math.sqrt(n)) if n > 0 else 1
        rows = math.ceil(n / cols) if cols > 0 else 1
        return rows, cols

    def _pad_grid_children(
        self,
        children: list,
        rows: int,
        cols: int,
    ) -> list:
        """Pad *children* with ``None`` to fill a rows×cols grid.

        Args:
            children: Ordered list of grid cell items (figures, Divs, etc.).
            rows:     Number of grid rows.
            cols:     Number of grid columns.

        Returns:
            A new list of length ``rows * cols`` padded with ``None``.
        """
        padded = list(children)
        target = rows * cols
        while len(padded) < target:
            padded.append(None)
        return padded

    def _setup_sources(self) -> "dict[str, ColumnDataSource]":
        """Build and return a dict mapping graph name → ColumnDataSource.

        Graphs listed in the ``link()`` build option share a single
        ``ColumnDataSource``.  All other graphs receive independent sources.
        ``link('_all')`` links every registered graph.

        Returns:
            Dict mapping each graph name to its ``ColumnDataSource``.
        """
        graphs = self.master_spec.get("graphs", [])
        build = self.master_spec.get("build_options", {})
        # Accept either structured "filters" list (from tests / server mode) or
        # the raw "filter" string emitted by dash.ado build_options.
        filters_cfg = build.get("filters", [])
        if not filters_cfg:
            _raw_f = build.get("filter", "")
            if _raw_f:
                filters_cfg = DashRenderer._parse_filter_raw(_raw_f)
        link_raw = build.get("link", "")

        # Parse link names — strip semicolons, treat as whitespace-delimited
        if isinstance(link_raw, list):
            link_names: list[str] = [str(x) for x in link_raw]
        else:
            link_names = link_raw.replace(";", " ").split()

        all_graph_names = [
            g.get("graph_options", {}).get("name", "") for g in graphs
        ]

        if "_all" in link_names:
            link_names = list(all_graph_names)

        sources: dict[str, ColumnDataSource] = {}
        _VK = DashRenderer._VAR_KEYS
        _OPT_VAR_KEYS = DashRenderer._OPT_VAR_KEYS

        if link_names:
            # First pass: collect all variable names needed by linked graphs,
            # including by-variables for linked graphs that also use by().
            linked_vars: list[str] = []
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    for vname in DashRenderer._collect_graph_vars(self.df, g):
                        if vname not in linked_vars:
                            linked_vars.append(vname)
                    # Also include by-variables so CDSView masks align to the shared source
                    by_raw = (g.get("graph_options", {}).get("by") or "").strip()
                    if by_raw:
                        varlist, _, _, _ = DashRenderer._parse_by_raw(by_raw)
                        for bv in varlist.split():
                            if bv and bv not in linked_vars:
                                linked_vars.append(bv)
            # Add filter variables so filter callbacks work on the shared source
            for fc in filters_cfg:
                v = fc.get("varname")
                if v and v not in linked_vars and v in self.df.columns:
                    linked_vars.append(v)

            # Add KPI variables so JS can recompute KPI card values on filter
            # changes.  Only KPIs that respond to filter events need this.
            kpis_spec = self.master_spec.get("kpis", [])
            for kpi in kpis_spec:
                kupdate = kpi.get("update", "filter")
                if kupdate in ("filter", "both"):
                    kvar = kpi.get("var") or kpi.get("varname", "")
                    if kvar and kvar not in linked_vars and kvar in self.df.columns:
                        linked_vars.append(kvar)

            # Add raw variables for aggregate (histogram/kdensity) non-linked
            # graphs so the JS filter callback can recompute bin counts and
            # density curves from the filtered subset.
            _AGG_TYPES = frozenset({"histogram", "hist", "kdensity"})
            for g in graphs:
                gname = g.get("graph_options", {}).get("name", "")
                if gname in link_names:
                    continue  # already covered by linked plots
                for plot in g.get("plots", []):
                    if plot.get("type", "") in _AGG_TYPES:
                        vname = plot.get("var") or plot.get("yvar", "")
                        if vname and vname not in linked_vars and vname in self.df.columns:
                            linked_vars.append(vname)

            linked_source = self._make_source(linked_vars)

            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    # Linked graphs share a source; per-graph if/in not applied
                    sources[name] = linked_source
                    # For by()+link() graphs, compute CDSView boolean masks
                    by_raw = (g.get("graph_options", {}).get("by") or "").strip()
                    if by_raw:
                        by_groups = self._expand_by_groups(g, base_df=self.df)
                        facet_entries = []
                        facet_masks = []
                        for idx, (label, group_df) in enumerate(by_groups):
                            fkey = f"{name}__by__{idx}"
                            mask = [i in group_df.index for i in self.df.index]
                            facet_entries.append((fkey, label))
                            facet_masks.append((label, mask))
                        self._facet_map[name] = facet_entries
                        self._facet_masks[name] = facet_masks
                else:
                    g_vars = DashRenderer._collect_graph_vars(self.df, g)
                    filtered_df = self._apply_graph_filter(g)
                    sources[name] = self._make_source(g_vars, df=filtered_df)
        else:
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                g_vars = DashRenderer._collect_graph_vars(self.df, g)
                filtered_df = self._apply_graph_filter(g)
                by_groups = self._expand_by_groups(g, base_df=filtered_df)
                if len(by_groups) == 1 and by_groups[0][0] == "":
                    # No faceting — standard path
                    sources[name] = self._make_source(g_vars, df=filtered_df)
                else:
                    # Faceted: one CDS per group
                    facet_entries = []
                    for idx, (label, group_df) in enumerate(by_groups):
                        fkey = f"{name}__by__{idx}"
                        sources[fkey] = self._make_source(g_vars, df=group_df)
                        facet_entries.append((fkey, label))
                    self._facet_map[name] = facet_entries

        return sources

    def _build_figures(self) -> "dict[str, Any]":
        """Build and return a dict mapping graph name → Bokeh Figure.

        Uses ``_setup_sources()`` to obtain ``ColumnDataSource`` objects and
        applies ``nonselection_alpha`` to renderers in linked figures.
        For graphs with ``by()`` faceting, creates one figure per facet
        group, keyed as ``"graphname__by__N"``.

        Returns:
            Dict mapping each graph name (or facet key) to its Figure.

        Raises:
            ValueError: If ``by()`` and ``link()`` are used together (not
                        supported in the current version).
        """
        sources = self._setup_sources()
        build = self.master_spec.get("build_options", {})
        link_raw = build.get("link", "")

        if isinstance(link_raw, list):
            link_names: list[str] = [str(x) for x in link_raw]
        else:
            link_names = link_raw.replace(";", " ").split()

        graphs = self.master_spec.get("graphs", [])
        all_graph_names = [
            g.get("graph_options", {}).get("name", "") for g in graphs
        ]
        if "_all" in link_names:
            link_names = list(all_graph_names)

        figs: dict[str, Any] = {}
        for g in graphs:
            name = g.get("graph_options", {}).get("name", "")

            # Check if this graph is faceted
            if name in self._facet_map:
                shared_src = sources.get(name)
                masks = self._facet_masks.get(name, [])
                for panel_idx, (fkey, label) in enumerate(self._facet_map[name]):
                    # Determine source and optional CDSView for this panel
                    if shared_src is not None and name in link_names:
                        # by()+link() graph: shared source with per-panel CDSView
                        src = shared_src
                        if panel_idx < len(masks):
                            _, mask = masks[panel_idx]
                            panel_view = CDSView(filter=BooleanFilter(booleans=mask))
                        else:
                            panel_view = None
                    else:
                        # Standalone by() graph: per-group source, no view needed
                        src = sources.get(fkey)
                        panel_view = None
                    if src is None:
                        continue
                    try:
                        fig = self._make_figure(g, src, facet_view=panel_view)
                        # Override title to include facet label
                        orig_title = fig.title.text if fig.title else ""
                        if orig_title:
                            fig.title.text = f"{orig_title} — {label}"
                        else:
                            fig.title.text = label
                        figs[fkey] = fig
                    except Exception as exc:
                        raise RuntimeError(
                            f"dash_render: failed to build facet figure "
                            f"'{fkey}': {exc}"
                        ) from exc
            else:
                src = sources.get(name)
                if src is None:
                    continue
                try:
                    fig = self._make_figure(g, src)
                    # Apply nonselection dimming for linked figures
                    if name in link_names:
                        for renderer in fig.renderers:
                            if (hasattr(renderer, "nonselection_glyph")
                                    and renderer.nonselection_glyph is not None):
                                ns = renderer.nonselection_glyph
                                if hasattr(ns, "fill_alpha"):
                                    ns.fill_alpha = _NONSELECTION_ALPHA
                                if hasattr(ns, "line_alpha"):
                                    ns.line_alpha = _NONSELECTION_ALPHA
                    figs[name] = fig
                except Exception as exc:
                    raise RuntimeError(
                        f"dash_render: failed to build figure '{name}': {exc}"
                    ) from exc

        # Store sources on self for test access
        self.sources = sources
        return figs

    # ------------------------------------------------------------------
    # Phase-method helpers called by render()
    # ------------------------------------------------------------------

    @staticmethod
    def _to_serialisable(v: "Any") -> "Any":
        """Convert a single value to a JSON-safe Python scalar."""
        if v is None:
            return None
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except (TypeError, ValueError):
            return str(v) if v is not None else None

    @staticmethod
    def _parse_fmt(fmt: str) -> "tuple[int, bool]":
        """Parse a Stata format string into (decimal_places, use_commas)."""
        m = re.match(r'%[\d]*\.(\d+)f(c)?', (fmt or "").strip())
        if m:
            return int(m.group(1)), m.group(2) == 'c'
        return 0, False

    def _build_kpi_html(self, kpis: list) -> None:
        """Phase 4 of render(): build KPI Div widgets and store in self.kpi_divs.

        For faceted KPIs (``update`` references a faceted graph) one card is
        created per facet group, computing the statistic on each group's
        filtered DataFrame.  For all other KPIs a single card is created,
        recomputing the display value from the loaded DataFrame so the ``fmt``
        format string is applied correctly.

        Reads:  self.df, self._facet_map, self.sources
        Writes: self.kpi_divs
        """
        for kpi in kpis:
            name = kpi.get("name", "kpi")
            kpi["name"] = name  # ensure name key present in def

            update_graph = kpi.get("update", "")
            stat = kpi.get("stat", "")
            varname = kpi.get("var") or kpi.get("varname", "")

            if update_graph and update_graph in self._facet_map and stat and varname:
                # Per-facet KPIs: one card per facet group
                for idx, (fkey, facet_label) in enumerate(
                    self._facet_map[update_graph]
                ):
                    facet_src = self.sources.get(fkey)
                    facet_df = (
                        pd.DataFrame(facet_src.data) if facet_src is not None
                        else pd.DataFrame()
                    )
                    facet_kpi = dict(kpi)
                    fkpi_name = f"{name}__by__{idx}"
                    facet_kpi["name"] = fkpi_name
                    orig_title = facet_kpi.get("title", "")
                    facet_kpi["title"] = (
                        f"{orig_title} ({facet_label})" if orig_title
                        else facet_label
                    )
                    try:
                        val = self._compute_kpi_stat_on_df(facet_df, stat, varname)
                        facet_kpi["value"] = self._format_kpi_value(
                            val, kpi.get("fmt", "")
                        )
                    except (ValueError, KeyError, TypeError):
                        facet_kpi["value"] = "—"
                    self.kpi_divs[fkpi_name] = self._make_kpi_div(facet_kpi)
            else:
                # Non-faceted KPI: recompute from df so fmt is applied correctly
                kpi_copy = dict(kpi)
                if stat and varname and varname in self.df.columns:
                    try:
                        raw_val = self._compute_kpi_stat(stat, varname)
                        kpi_copy["value"] = self._format_kpi_value(
                            raw_val, kpi.get("fmt", "")
                        )
                    except (ValueError, KeyError, TypeError):
                        if not kpi_copy.get("value"):
                            kpi_copy["value"] = kpi.get("display", "")
                elif not kpi_copy.get("value"):
                    kpi_copy["value"] = kpi.get("display", "")
                self.kpi_divs[name] = self._make_kpi_div(kpi_copy)

    def _build_filter_widgets(
        self,
        filters_cfg: list,
        link_names: list,
        kpis: list,
    ) -> list:
        """Phase 5 of render(): build filter widgets and wire multi-filter callbacks.

        For each filter spec, creates the appropriate Bokeh widget (Select,
        Slider, or RangeSlider) and a CustomJS callback that re-applies all
        active filter conditions on every widget change.

        Reads:  self.sources, self.kpi_divs, self.agg_source_registry
        Writes: self.filter_widgets, self.filter_callbacks

        Returns:
            Ordered list of Bokeh widget objects to place in the filter row.
        """
        filter_row_widgets: list = []
        fsource = None
        # Track filter specs that actually produced a widget+callback, in the
        # same order as self.filter_callbacks.  Specs whose variable is missing
        # in the data source are skipped and must NOT appear here, otherwise
        # zip(built_filter_specs, filter_callbacks) would pair the wrong spec
        # with the wrong callback and apply incorrect exclude() lists.
        built_filter_specs: list = []

        for fc in filters_cfg:
            fvar    = fc.get("varname", "")
            ftype   = fc.get("type", "dropdown")
            excludes = fc.get("exclude", [])

            if link_names and link_names[0] in self.sources:
                fsource = self.sources[link_names[0]]
            else:
                fsource = next(iter(self.sources.values())) if self.sources else None

            if fsource is None or fvar not in fsource.data:
                continue

            # Resolve value labels (standard Stata format or direct-by-varname)
            labelset = self.value_label_names.get(fvar, "")
            vlabels  = self.value_labels.get(labelset, {}) if labelset else {}
            if not vlabels:
                candidate = self.value_labels.get(fvar, {})
                if isinstance(candidate, dict):
                    vlabels = candidate

            flabel = fc.get("label", fvar)
            if ftype == "dropdown":
                widget, cb = FilterBuilder.build_dropdown(
                    fvar, fsource, None, vlabels,
                    exclude_names=excludes,
                    label=flabel,
                )
            elif ftype == "slider":
                widget, cb = FilterBuilder.build_slider(
                    fvar, fsource, None, exclude_names=excludes,
                    label=flabel,
                )
            elif ftype == "range":
                widget, cb = FilterBuilder.build_range(
                    fvar, fsource, None, exclude_names=excludes,
                    label=flabel,
                )
            else:
                continue

            cb.args["view_filters"] = []  # no longer used; kept for compat
            filter_row_widgets.append(widget)
            self.filter_widgets.append(widget)
            self.filter_callbacks.append(cb)
            built_filter_specs.append(fc)  # record only successfully-built specs

        # Wire multi-filter state into every callback.
        # Each callback gets orig_data_json, all_widgets, filter_specs_json,
        # kpi_config_json, kpi_divs, agg_sources, agg_configs_json so it can
        # re-apply all active filter conditions on every widget change.
        _orig_data: dict = {}
        if fsource is not None:
            for _col, _arr in fsource.data.items():
                _orig_data[_col] = [DashRenderer._to_serialisable(v) for v in _arr]

        # Build filter_specs from only the successfully-built specs so that
        # JS callbacks index all_widgets correctly (1:1 correspondence).
        # Include per-widget sentinel so _FILTER_JS can check the right
        # "no filter" value — the sentinel may differ from '__all__' when
        # real data contains that literal string.
        _filter_specs: list = [
            {
                "varname":  _fc.get("varname", ""),
                "type":     _fc.get("type", "dropdown"),
                "sentinel": getattr(_w, "_dash_sentinel", "__all__"),
            }
            for _fc, _w in zip(built_filter_specs, self.filter_widgets)
        ]

        _kpi_defs_by_name: dict = {k.get("name", ""): k for k in kpis}

        for _fc, _cb in zip(built_filter_specs, self.filter_callbacks):
            _fc_excludes = [str(x) for x in _fc.get("exclude", [])]
            _kpi_config_for_cb: list = []
            _kpi_divs_for_cb:   list = []
            for _kname, _kdiv in self.kpi_divs.items():
                if _kname in _fc_excludes:
                    continue
                _kdef = _kpi_defs_by_name.get(_kname, {})
                if _kdef.get("update", "filter") not in ("filter", "both"):
                    continue
                _kstat  = _kdef.get("stat", "mean")
                _kvar   = _kdef.get("var") or _kdef.get("varname", "")
                _kfmt   = _kdef.get("fmt", "%9.0f")
                _dec, _comma = DashRenderer._parse_fmt(_kfmt)
                _kpi_config_for_cb.append({
                    "name":     _kname,
                    "stat":     _kstat,
                    "varname":  _kvar,
                    "decimals": _dec,
                    "commas":   _comma,
                    # HTML-escape title/subtitle to prevent DOM XSS when the filter
                    # callback reconstructs kpi_div.text via string concatenation.
                    "title":    html.escape(_kdef.get("title", "") or ""),
                    "subtitle": html.escape(_kdef.get("subtitle", "") or ""),
                    # Sanitize color fields against CSS injection: the JS
                    # callback embeds these directly into style="...color:<val>..."
                    # so an unsanitized value can break out of the attribute.
                    "color":    _sanitize_css_color(
                        _kdef.get("color", "") or "", "#212529"
                    ),
                    "bgcolor":  _sanitize_css_color(
                        _kdef.get("bgcolor", "") or "", "#f8f9fa"
                    ),
                })
                _kpi_divs_for_cb.append(_kdiv)

            _cb.args["orig_data_json"]    = json.dumps(_orig_data)
            _cb.args["all_widgets"]       = list(self.filter_widgets)
            _cb.args["filter_specs_json"] = json.dumps(_filter_specs)
            _cb.args["kpi_config_json"]   = json.dumps(_kpi_config_for_cb)
            _cb.args["kpi_divs"]          = _kpi_divs_for_cb

            # Pass ALL non-excluded graph sources so _FILTER_JS can update every
            # graph in an unlinked dashboard (not just the primary fsource).
            _graph_srcs_for_cb: list = []
            for _gsrc_name, _gsrc in self.sources.items():
                if _gsrc_name in _fc_excludes:
                    continue
                if _gsrc not in _graph_srcs_for_cb:
                    _graph_srcs_for_cb.append(_gsrc)
            _cb.args["all_graph_sources"] = _graph_srcs_for_cb

            # Build per-source original snapshots (indexed parallel to
            # all_graph_sources) so _FILTER_JS can rebuild filtered data for
            # each source using its own column schema.  Without this, assigning
            # a single new_data (built from the primary source) to all sources
            # drops columns that belong to secondary sources only — corrupting
            # unlinked graphs whose schemas differ from the primary source.
            _per_src_orig_json: list = []
            for _gsrc in _graph_srcs_for_cb:
                _src_snap: dict = {
                    _col: [DashRenderer._to_serialisable(v) for v in _arr]
                    for _col, _arr in _gsrc.data.items()
                }
                _per_src_orig_json.append(json.dumps(_src_snap))
            _cb.args["all_graph_sources_orig_json"] = _per_src_orig_json

            _agg_srcs: list = []
            _agg_cfgs: list = []
            for _gname, _agg_list in self.agg_source_registry.items():
                if _gname in _fc_excludes:
                    continue
                for _agg_cds, _agg_cfg in _agg_list:
                    _agg_srcs.append(_agg_cds)
                    _agg_cfgs.append(_agg_cfg)
            _cb.args["agg_sources"]      = _agg_srcs
            _cb.args["agg_configs_json"] = json.dumps(_agg_cfgs)

        return filter_row_widgets

    def _assemble_layout(
        self,
        graphs: list,
        all_names: list,
        kpi_names: list,
        filter_row_widgets: list,
        build: dict,
        title_text: str,
        subtitle_text: str,
    ) -> str:
        """Phase 6 of render(): assemble the Bokeh layout and return standalone HTML.

        Handles both Bootstrap-grid and standard Bokeh-gridplot layouts, with
        optional title/subtitle header and tab groups (Bootstrap mode only).

        Reads:  self.figures, self.kpi_divs, self._facet_map, self.scheme
        Returns:
            Complete standalone HTML string for the dashboard.
        """
        layout_opt      = build.get("layout", "auto")
        tabs_str        = build.get("tabs", "").strip()
        filter_position = build.get("filter_position", "top").strip().lower()
        if filter_position not in ("top", "left"):
            filter_position = "top"

        tabs_widget:  Any       = None
        tabbed_names: set[str]  = set()
        if tabs_str and DashRenderer._is_bootstrap_layout(layout_opt):
            _tabs_spec = DashRenderer._parse_tabs_option(tabs_str, all_names)
            if _tabs_spec:
                tabs_widget, tabbed_names = self._build_tabs_widget(_tabs_spec)

        if DashRenderer._is_bootstrap_layout(layout_opt):
            return self._render_bootstrap_html(
                layout_opt=layout_opt,
                all_names=all_names,
                kpi_names=kpi_names,
                filter_row_widgets=filter_row_widgets,
                title_text=title_text,
                subtitle_text=subtitle_text,
                tabs_widget=tabs_widget,
                tabbed_names=tabbed_names,
                filter_position=filter_position,
            )

        # ---- Standard Bokeh gridplot layout ----
        rows_n, cols_n = self._compute_grid(all_names, layout_opt)
        n_items = len(all_names)
        if n_items > rows_n * cols_n:
            rows_n = math.ceil(n_items / cols_n)

        cells: list[Any] = []
        for name in all_names:
            if name in self._facet_map:
                facet_figs = [
                    self.figures[fkey]
                    for fkey, _ in self._facet_map[name]
                    if fkey in self.figures
                ]
                if facet_figs:
                    gopts = next(
                        (g.get("graph_options", {})
                         for g in graphs
                         if g.get("graph_options", {}).get("name") == name),
                        {},
                    )
                    _, by_cols_from_raw, _, _ = DashRenderer._parse_by_raw(
                        (gopts.get("by") or "")
                    )
                    by_cols_key_raw = gopts.get("by_cols", "0")
                    try:
                        by_cols_key = int(by_cols_key_raw) if by_cols_key_raw else 0
                    except (ValueError, TypeError):
                        by_cols_key = 0
                    by_cols_n = by_cols_from_raw or by_cols_key
                    if by_cols_n <= 0:
                        by_cols_n = min(
                            len(facet_figs),
                            max(1, math.ceil(math.sqrt(len(facet_figs)))),
                        )
                    sub_rows = [
                        facet_figs[i : i + by_cols_n]
                        for i in range(0, len(facet_figs), by_cols_n)
                    ]
                    while len(sub_rows[-1]) < by_cols_n:
                        sub_rows[-1].append(None)
                    cells.append(gridplot(sub_rows, sizing_mode="stretch_width"))
                else:
                    cells.append(None)
            elif name in self.figures:
                cells.append(self.figures[name])
            elif name in self.kpi_divs:
                cells.append(self.kpi_divs[name])

        while len(cells) < rows_n * cols_n:
            cells.append(None)

        grid_rows = [
            cells[r * cols_n : (r + 1) * cols_n] for r in range(rows_n)
        ]
        grid = gridplot(grid_rows, sizing_mode="stretch_width")

        if filter_row_widgets:
            filter_bar  = row(filter_row_widgets, sizing_mode="stretch_width")
            layout_root = column(filter_bar, grid, sizing_mode="stretch_width")
        else:
            layout_root = grid

        if title_text or subtitle_text:
            header_items = []
            if title_text:
                header_items.append(Div(
                    text=(
                        f'<h2 style="font-family:sans-serif;margin-bottom:2px;">'
                        f'{title_text}</h2>'
                    ),
                    sizing_mode="stretch_width",
                ))
            if subtitle_text:
                header_items.append(Div(
                    text=(
                        f'<p style="font-family:sans-serif;color:#555;'
                        f'margin-top:0;margin-bottom:8px;">{subtitle_text}</p>'
                    ),
                    sizing_mode="stretch_width",
                ))
            layout_root = column(*header_items, layout_root,
                                 sizing_mode="stretch_width")

        html_str = file_html(layout_root, INLINE, title=title_text or "dash")

        _scheme_css = self.scheme.css_block()
        html_str = html_str.replace(
            "<head>",
            f"<head>\n    {_CSP_META}\n{_scheme_css}",
            1,
        )
        return html_str

    # ------------------------------------------------------------------
    # Main render method
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Build the complete dashboard and return standalone HTML.

        Orchestrates six phases in order:
          1. Collect all variable names referenced across graphs, KPIs, and filters.
          2. Build ColumnDataSources (shared linked source or per-graph sources).
          2b. Handle by() faceting on unlinked sources.
          3. Build Bokeh figures (and collect aggregate sources).
          4. Build KPI Div widgets  → ``_build_kpi_html``
          5. Build filter widgets and wire callbacks  → ``_build_filter_widgets``
          6. Assemble layout and render HTML  → ``_assemble_layout``

        Returns:
            A string containing the full standalone HTML page.
        """
        graphs = self.master_spec.get("graphs", [])
        kpis   = self.master_spec.get("kpis", [])
        build  = self.master_spec.get("build_options", {})

        # ---- Parse build options ----
        _link_raw_render = build.get("link", [])
        if isinstance(_link_raw_render, list):
            link_names: list[str] = [str(x) for x in _link_raw_render]
        else:
            link_names = _link_raw_render.replace(";", " ").split()
        filters_cfg = build.get("filters", [])
        if not filters_cfg:
            _raw_f = build.get("filter", "")
            if _raw_f:
                filters_cfg = DashRenderer._parse_filter_raw(_raw_f)
        title_text    = html.escape(build.get("title", ""))
        subtitle_text = html.escape(build.get("subtitle", "") or "")

        # ---- 1. Collect all variable names (reference / future use) ----
        all_vars: list[str] = []
        for g in graphs:
            for vname in DashRenderer._collect_plot_vars(g.get("plots", [])):
                if vname not in all_vars:
                    all_vars.append(vname)
        for kpi in kpis:
            v = kpi.get("varname")
            if v and v not in all_vars:
                all_vars.append(v)
        for fc in filters_cfg:
            v = fc.get("varname")
            if v and v not in all_vars:
                all_vars.append(v)
        for g in graphs:
            by_raw = (g.get("graph_options", {}).get("by") or "").strip()
            if by_raw:
                varlist, _, _, _ = DashRenderer._parse_by_raw(by_raw)
                for bv in varlist.split():
                    if bv and bv not in all_vars:
                        all_vars.append(bv)

        # ---- 2. Build ColumnDataSources ----
        if link_names:
            linked_vars: list[str] = []
            for g in graphs:
                gname = g.get("graph_options", {}).get("name", "")
                if gname in link_names:
                    for vname in DashRenderer._collect_graph_vars(self.df, g):
                        if vname not in linked_vars:
                            linked_vars.append(vname)
                    by_raw_lnk = (g.get("graph_options", {}).get("by") or "").strip()
                    if by_raw_lnk:
                        varlist_lnk, _, _, _ = DashRenderer._parse_by_raw(by_raw_lnk)
                        for bv in varlist_lnk.split():
                            if bv and bv not in linked_vars:
                                linked_vars.append(bv)
            for fc in filters_cfg:
                v = fc.get("varname")
                if v and v not in linked_vars and v in self.df.columns:
                    linked_vars.append(v)
            for kpi in kpis:
                kupdate = kpi.get("update", "filter")
                if kupdate in ("filter", "both"):
                    kvar = kpi.get("var") or kpi.get("varname", "")
                    if kvar and kvar not in linked_vars and kvar in self.df.columns:
                        linked_vars.append(kvar)
            _AGG_TYPES_RENDER = frozenset({"histogram", "hist", "kdensity"})
            for g in graphs:
                gname = g.get("graph_options", {}).get("name", "")
                if gname in link_names:
                    continue
                for plot in g.get("plots", []):
                    if plot.get("type", "") in _AGG_TYPES_RENDER:
                        vname = plot.get("var") or plot.get("yvar", "")
                        if vname and vname not in linked_vars and vname in self.df.columns:
                            linked_vars.append(vname)
            linked_source = self._make_source(linked_vars)
            # Per-graph qualifier views for linked graphs.  The shared source
            # supports brush selection across all linked graphs and cannot be
            # filtered per-graph.  CDSView with BooleanFilter applies each
            # graph's if_expr/in_expr mask without modifying the source data.
            _linked_graph_views: dict = {}

            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    self.sources[name] = linked_source
                    # Build a CDSView for linked graphs that have qualifiers.
                    _g_fdf = self._apply_graph_filter(g)
                    if len(_g_fdf) < len(self.df):
                        _df_idx_set = frozenset(_g_fdf.index)
                        _bool_mask = [
                            bool(i in _df_idx_set) for i in self.df.index
                        ]
                        _linked_graph_views[name] = CDSView(
                            filter=BooleanFilter(booleans=_bool_mask)
                        )
                    by_raw_lnk2 = (g.get("graph_options", {}).get("by") or "").strip()
                    if by_raw_lnk2:
                        by_groups_lnk = self._expand_by_groups(g, base_df=self.df)
                        facet_entries_lnk = []
                        facet_masks_lnk   = []
                        for idx, (label, group_df) in enumerate(by_groups_lnk):
                            fkey = f"{name}__by__{idx}"
                            mask = [i in group_df.index for i in self.df.index]
                            facet_entries_lnk.append((fkey, label))
                            facet_masks_lnk.append((label, mask))
                        self._facet_map[name]   = facet_entries_lnk
                        self._facet_masks[name] = facet_masks_lnk
                else:
                    g_vars      = DashRenderer._collect_graph_vars(self.df, g)
                    filtered_df = self._apply_graph_filter(g)
                    self.sources[name] = self._make_source(g_vars, df=filtered_df)
        else:
            for g in graphs:
                name   = g.get("graph_options", {}).get("name", "")
                g_vars = DashRenderer._collect_graph_vars(self.df, g)
                for fc in filters_cfg:
                    fv = fc.get("varname", "")
                    if fv and fv not in g_vars:
                        g_vars.append(fv)
                filtered_df = self._apply_graph_filter(g)
                self.sources[name] = self._make_source(g_vars, df=filtered_df)

        # ---- 2b. Handle by() faceting on unlinked sources ----
        for g in graphs:
            name    = g.get("graph_options", {}).get("name", "")
            by_raw  = (g.get("graph_options", {}).get("by") or "").strip()
            if by_raw and name not in link_names:
                base_src = self.sources.pop(name, None)
                if base_src is None:
                    continue
                by_groups = self._expand_by_groups(g, base_df=self.df)
                if len(by_groups) == 1 and by_groups[0][0] == "":
                    self.sources[name] = base_src
                else:
                    g_vars        = list(base_src.data.keys())
                    facet_entries = []
                    for idx, (label, group_df) in enumerate(by_groups):
                        fkey = f"{name}__by__{idx}"
                        self.sources[fkey] = self._make_source(g_vars, df=group_df)
                        facet_entries.append((fkey, label))
                    self._facet_map[name] = facet_entries

        # ---- 3. Build figures ----
        for g in graphs:
            name = g.get("graph_options", {}).get("name", "")
            if name in self._facet_map:
                shared_src_render = self.sources.get(name)
                masks_render      = self._facet_masks.get(name, [])
                for panel_idx_r, (fkey, label) in enumerate(self._facet_map[name]):
                    if shared_src_render is not None and name in link_names:
                        src = shared_src_render
                        if panel_idx_r < len(masks_render):
                            _, mask_r   = masks_render[panel_idx_r]
                            panel_view_r = CDSView(filter=BooleanFilter(booleans=mask_r))
                        else:
                            panel_view_r = None
                    else:
                        src          = self.sources.get(fkey)
                        panel_view_r = None
                    if src is None:
                        continue
                    try:
                        fig = self._make_figure(g, src, facet_view=panel_view_r)
                        orig_title = fig.title.text if fig.title else ""
                        fig.title.text = f"{orig_title} — {label}" if orig_title else label
                        self.figures[fkey] = fig
                    except Exception as exc:
                        raise RuntimeError(
                            f"dash_render: failed to build facet figure '{fkey}': {exc}"
                        ) from exc
            else:
                src = self.sources.get(name)
                if src is None:
                    continue
                # For linked graphs with if_expr/in_expr, apply a CDSView so
                # the qualifier mask is honoured without filtering the shared source.
                _qual_view = _linked_graph_views.get(name) \
                    if "_linked_graph_views" in dir() else None
                try:
                    self.figures[name] = self._make_figure(
                        g, src, facet_view=_qual_view
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"dash_render: failed to build figure '{name}': {exc}"
                    ) from exc

        # ---- 3b. Collect aggregate sources for filter recomputation ----
        for _gname, _fig in self.figures.items():
            _agg_list = [
                (_r._dash_agg_source, dict(_r._dash_agg_config))
                for _r in _fig.renderers
                if hasattr(_r, "_dash_agg_source") and hasattr(_r, "_dash_agg_config")
            ]
            if _agg_list:
                self.agg_source_registry[_gname] = _agg_list

        # ---- 4. Build KPI Divs ----
        self._build_kpi_html(kpis)

        # ---- 5. Build filter widgets and wire callbacks ----
        filter_row_widgets = self._build_filter_widgets(filters_cfg, link_names, kpis)

        # ---- 6. Assemble layout and render to HTML ----
        all_names:  list[str] = list(self.kpi_divs.keys())
        kpi_names:  list[str] = list(self.kpi_divs.keys())
        for g in graphs:
            all_names.append(g.get("graph_options", {}).get("name", ""))

        return self._assemble_layout(
            graphs=graphs,
            all_names=all_names,
            kpi_names=kpi_names,
            filter_row_widgets=filter_row_widgets,
            build=build,
            title_text=title_text,
            subtitle_text=subtitle_text,
        )


# ===========================================================================
# ServerAppBuilder — generates a standalone Bokeh Server app .py file
# ===========================================================================

class ServerAppBuilder:
    """Generates a self-contained Bokeh Server application Python source file.

    Unlike ``DashRenderer`` (which produces a standalone HTML file with
    ``CustomJS`` callbacks), ``ServerAppBuilder`` produces a ``.py`` file
    that:

    * Embeds all data as base64-encoded JSON — no external file dependencies
      at run time.
    * Uses Python ``on_change`` callbacks for filter widgets and brush
      selection, enabling true dynamic recomputation of aggregated plots
      (histogram, lfit, qfit, kdensity, lowess) and KPI statistics.
    * Can be launched with ``bokeh serve <app.py>`` or executed directly as
      ``python <app.py>``.

    Security notes
    --------------
    * All user-supplied strings (title, KPI labels, variable names in Div
      text) are passed through ``html.escape()`` before being embedded in
      the generated Python file's string literals.
    * The entire data payload is base64-encoded, preventing any special
      characters in data values (quotes, backslashes, newlines) from
      breaking the generated file's syntax.
    * ``allow_websocket_origin`` is restricted to ``['localhost:{port}']``.
    """

    def __init__(self, spec_path: str, data_path: str) -> None:
        """Load and parse spec and data files.

        Args:
            spec_path:  Path to the master specification JSON.
            data_path:  Path to the jsonio data JSON.
        """
        with open(spec_path, "r", encoding="utf-8") as f:
            self.spec: dict = json.load(f)

        with open(data_path, "r", encoding="utf-8") as f:
            self._raw_data_str: str = f.read()

        self._spec_str: str = json.dumps(self.spec)

    def build(self, output_path: str, port: int = 5006) -> None:
        """Generate the Bokeh Server app file and write it to *output_path*.

        Args:
            output_path: Destination path for the generated ``.py`` file.
            port:        Port number to embed in the ``__main__`` launch block.
        """
        # Override port from build_options if present
        bo = self.spec.get("build_options", {})
        if bo.get("port"):
            try:
                port = int(bo["port"])
            except (ValueError, TypeError):
                pass

        source = self._generate_app_source(port)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(source)

    def _embed_data(self) -> tuple[str, str]:
        """Base64-encode spec and data JSON strings.

        Returns:
            Tuple of (spec_b64, data_b64) — ASCII-safe base64 strings safe to
            embed in Python string literals without any escaping.
        """
        import base64
        spec_b64 = base64.b64encode(self._spec_str.encode("utf-8")).decode("ascii")
        data_b64 = base64.b64encode(self._raw_data_str.encode("utf-8")).decode("ascii")
        return spec_b64, data_b64

    def _generate_app_source(self, port: int) -> str:  # noqa: C901 (complexity OK for codegen)
        """Return the full Python source string for the Bokeh Server app.

        The generated file is structured as:
          1. Module docstring + imports
          2. Embedded base64 data constants
          3. Helper functions (_load_spec_and_data, _compute_*, _compute_kpi)
          4. make_document(doc) — Bokeh Server document factory
          5. __main__ launch block

        Args:
            port: Server port number to embed.

        Returns:
            Complete Python source as a string.
        """
        spec_b64, data_b64 = self._embed_data()

        # Gather build options
        bo = self.spec.get("build_options", {})
        title_raw = bo.get("title", "") or ""
        title_safe = html.escape(title_raw)
        layout_opt = bo.get("layout", "auto") or "auto"
        link_opt = bo.get("link", "") or ""
        filter_raw = bo.get("filter", "") or ""
        theme_opt = bo.get("theme", "default") or "default"

        graphs = self.spec.get("graphs", [])
        kpis = self.spec.get("kpis", [])

        # Determine linked graph names
        linked_names: set[str] = set()
        if link_opt == "_all":
            for g in graphs:
                n = g.get("graph_options", {}).get("name", "")
                if n:
                    linked_names.add(n)
        elif link_opt:
            linked_names = set(link_opt.split())

        # Parse filter spec — reuse DashRenderer._parse_filter_raw which handles
        # both "||" (Mata-joined) and ";" (legacy) separators correctly.
        filter_specs: list[dict] = []
        if filter_raw and filter_raw != '"':
            for _fs in DashRenderer._parse_filter_raw(filter_raw):
                # DashRenderer uses "varname" key; ServerAppBuilder uses "var"
                filter_specs.append({
                    "var": _fs["varname"],
                    "type": _fs["type"],
                    "exclude": _fs["exclude"],
                })

        lines: list[str] = []

        # ----------------------------------------------------------------
        # 1. Header + imports
        # ----------------------------------------------------------------
        lines += [
            '"""',
            '# Auto-generated Bokeh Server dashboard — do not edit manually.',
            '# Generated by dash_render.py',
            '# Launch with: bokeh serve <this_file.py>',
            '# Or run directly: python <this_file.py>',
            '"""',
            "",
            "import base64",
            "import html",
            "import json",
            "import math",
            "import re",
            "import numpy as np",
            "import pandas as pd",
            "from scipy import stats as scipy_stats",
            "try:",
            "    import statsmodels.nonparametric.smoothers_lowess as sm_lowess",
            "    _HAS_STATSMODELS = True",
            "except ImportError:",
            "    _HAS_STATSMODELS = False",
            "",
            "from bokeh.application import Application",
            "from bokeh.application.handlers.function import FunctionHandler",
            "from bokeh.layouts import column, gridplot, row",
            "from bokeh.models import (",
            "    Arrow,",
            "    BooleanFilter,",
            "    BoxSelectTool,",
            "    CDSView,",
            "    ColumnDataSource,",
            "    Div,",
            "    HoverTool,",
            "    IndexFilter,",
            "    LabelSet,",
            "    LassoSelectTool,",
            "    NormalHead,",
            "    OpenHead,",
            "    PanTool,",
            "    Range1d,",
            "    RangeSlider,",
            "    ResetTool,",
            "    Select,",
            "    Slider,",
            "    Span,",
            "    WheelZoomTool,",
            ")",
            "from bokeh.plotting import figure as bokeh_figure",
            "from bokeh.server.server import Server",
            "import collections as _collections",
            "import time as _time",
            "from tornado.web import RequestHandler as _RequestHandler",
            "",
            "# ---- Rate limiter configuration ----",
            "_RATE_LIMIT_RPM = 60  # max requests per IP per minute",
            "",
            "class _RateLimiter:",
            "    '''Sliding-window per-IP rate limiter.",
            "    Empty per-IP lists are deleted after pruning so unique-IP churn",
            "    cannot grow _store without bound.  A hard _MAX_IPS cap evicts the",
            "    oldest tracked IP when the store is full.'''",
            "    _MAX_IPS = 10000  # max simultaneous tracked IPs (evict oldest when exceeded)",
            "    def __init__(self, max_rpm=60):",
            "        self._max = max_rpm",
            "        self._window = 60.0",
            "        self._store = {}  # plain dict; keys deleted when empty (not defaultdict)",
            "    def is_allowed(self, ip):",
            "        now = _time.monotonic()",
            "        cutoff = now - self._window",
            "        ts = self._store.get(ip)",
            "        if ts is None:",
            "            ts = []",
            "        else:",
            "            while ts and ts[0] < cutoff:",
            "                ts.pop(0)",
            "            if not ts:",
            "                del self._store[ip]  # prune empty entry — prevents unbounded growth",
            "        if len(ts) >= self._max:",
            "            return False",
            "        # Enforce global IP cap: evict oldest entry when store is full",
            "        if ip not in self._store and len(self._store) >= self._MAX_IPS:",
            "            oldest = next(iter(self._store))",
            "            del self._store[oldest]",
            "        ts.append(now)",
            "        self._store[ip] = ts",
            "        return True",
            "",
            "_LIMITER = _RateLimiter(_RATE_LIMIT_RPM)",
            "",
            "def _client_ip_from_request(req):",
            "    '''Return the best-guess client IP for rate-limiting.",
            "",
            "    Prefers the X-Forwarded-For header (first token in the chain) over",
            "    remote_ip so that each end-user behind a reverse proxy gets their own",
            "    rate-limit bucket instead of being collapsed into the proxy's IP.",
            "    Falls back to remote_ip, then '0.0.0.0' if neither is available.",
            "    '''",
            "    try:",
            "        headers = getattr(req, 'headers', None) or {}",
            "        xff = headers.get('X-Forwarded-For', '')",
            "        if xff:",
            "            first = xff.split(',')[0].strip()",
            "            if first:",
            "                return first",
            "        return getattr(req, 'remote_ip', None) or '0.0.0.0'",
            "    except Exception:",
            "        return '0.0.0.0'",
            "",
            "class _HealthHandler(_RequestHandler):",
            "    '''Health check HTTP handler — returns 200 OK or 429 when rate-limited.'''",
            "    def prepare(self):",
            "        _ip = _client_ip_from_request(self.request)",
            "        if not _LIMITER.is_allowed(_ip):",
            "            self.set_status(429)",
            "            self.set_header('Content-Type', 'application/json')",
            "            self.finish('{\"status\": \"rate_limited\", \"message\": \"Too Many Requests\"}')",
            "    def get(self):",
            "        import datetime as _dt",
            "        self.set_header('Content-Type', 'application/json')",
            "        self.set_status(200)",
            "        ts = _dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')",
            "        self.write('{\"status\": \"ok\", \"timestamp\": \"' + ts + '\"}')",
            "",
        ]

        # ----------------------------------------------------------------
        # 2. Embedded data
        # ----------------------------------------------------------------
        lines += [
            "# ---- Embedded data (base64-encoded to ensure safe embedding) ----",
            f'_SPEC_B64 = "{spec_b64}"',
            f'_DATA_B64 = "{data_b64}"',
            "",
        ]

        # ----------------------------------------------------------------
        # 3. Helper functions
        # ----------------------------------------------------------------
        lines += [
            "# ---- Data loading ----",
            "def _load_spec_and_data():",
            '    """Decode embedded data and return (spec_dict, DataFrame, meta_dict)."""',
            "    spec = json.loads(base64.b64decode(_SPEC_B64).decode('utf-8'))",
            "    data_json = json.loads(base64.b64decode(_DATA_B64).decode('utf-8'))",
            "    # Parse jsonio format",
            "    values = data_json.get('values', [])",
            "    var_names = data_json.get('variableNames', [])",
            "    var_labels = data_json.get('variableLabels', {})",
            "    val_label_names = data_json.get('valueLabelNames', {})",
            "    val_labels = data_json.get('valueLabels', {})",
            "    type_is_str = data_json.get('variableTypeIsString', {})",
            "    if values and var_names:",
            "        rows = []",
            "        for obs in values:",
            "            if isinstance(obs, dict):",
            "                row = {v: obs.get(v) for v in var_names}",
            "            elif isinstance(obs, list):",
            "                row = dict(zip(var_names, obs))",
            "            else:",
            "                row = {}",
            "            rows.append(row)",
            "        df = pd.DataFrame(rows, columns=var_names)",
            "    else:",
            "        df = pd.DataFrame()",
            "    # Convert to numeric where possible",
            "    for col in df.columns:",
            "        if not type_is_str.get(col, False):",
            "            df[col] = pd.to_numeric(df[col], errors='coerce')",
            "    meta = {",
            "        'var_labels': var_labels,",
            "        'val_label_names': val_label_names,",
            "        'val_labels': val_labels,",
            "        'type_is_str': type_is_str,",
            "    }",
            "    return spec, df, meta",
            "",
            "",
            "# ---- Aggregate compute helpers ----",
            "def _compute_histogram(df, varname, bins=20):",
            '    """Return Bokeh quad() source dict from histogram of df[varname]."""',
            "    bins = max(1, min(int(bins), 1000))  # clamp: prevent resource exhaustion",
            "    data = df[varname].dropna().values.astype(float)",
            "    if len(data) == 0:",
            "        return dict(top=[], left=[], right=[])",
            "    hist, edges = np.histogram(data, bins=bins)",
            "    return dict(top=hist.tolist(), left=edges[:-1].tolist(), right=edges[1:].tolist())",
            "",
            "",
            "def _compute_lfit(df, yvar, xvar):",
            '    """Return line source dict for OLS fit of yvar on xvar."""',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 2:",
            "        return dict(x=[], y=[])",
            "    coeffs = np.polyfit(clean[xvar].values, clean[yvar].values, 1)",
            "    x_range = np.linspace(clean[xvar].min(), clean[xvar].max(), 100)",
            "    return dict(x=x_range.tolist(), y=np.polyval(coeffs, x_range).tolist())",
            "",
            "",
            "def _compute_qfit(df, yvar, xvar):",
            '    """Return line source dict for quadratic fit of yvar on xvar."""',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 3:",
            "        return dict(x=[], y=[])",
            "    coeffs = np.polyfit(clean[xvar].values, clean[yvar].values, 2)",
            "    x_range = np.linspace(clean[xvar].min(), clean[xvar].max(), 100)",
            "    return dict(x=x_range.tolist(), y=np.polyval(coeffs, x_range).tolist())",
            "",
            "",
            "def _compute_lfitci(df, yvar, xvar):",
            '    """Return CI band source dict for OLS fit with 95% confidence interval."""',
            "    from scipy import stats as _sp_stats",
            "    clean = df[[xvar, yvar]].dropna()",
            "    x = clean[xvar].values.astype(float)",
            "    y = clean[yvar].values.astype(float)",
            "    n = len(x)",
            "    if n < 3 or float(np.std(x)) == 0.0:",
            "        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])",
            "    slope, intercept, _, _, se = _sp_stats.linregress(x, y)",
            "    x_fit = np.linspace(x.min(), x.max(), 200)",
            "    y_fit = intercept + slope * x_fit",
            "    x_mean = x.mean()",
            "    x_ss = float(np.sum((x - x_mean) ** 2))",
            "    se_fit = se * np.sqrt(1/n + (x_fit - x_mean)**2 / x_ss) * np.sqrt(n - 2)",
            "    t_crit = _sp_stats.t.ppf(0.975, df=n - 2)",
            "    return dict(x_fit=x_fit.tolist(), y_fit=y_fit.tolist(),",
            "                y_lower=(y_fit - t_crit*se_fit).tolist(),",
            "                y_upper=(y_fit + t_crit*se_fit).tolist())",
            "",
            "",
            "def _compute_qfitci(df, yvar, xvar):",
            '    """Return CI band source dict for quadratic fit with 95% confidence interval."""',
            "    from scipy import stats as _sp_stats",
            "    clean = df[[xvar, yvar]].dropna()",
            "    x = clean[xvar].values.astype(float)",
            "    y = clean[yvar].values.astype(float)",
            "    n = len(x)",
            "    if n < 4 or float(np.std(x)) == 0.0:",
            "        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])",
            "    coeffs = np.polyfit(x, y, 2)",
            "    x_fit = np.linspace(x.min(), x.max(), 200)",
            "    y_fit = np.polyval(coeffs, x_fit)",
            "    # Estimate residual SE for prediction interval approximation",
            "    y_pred = np.polyval(coeffs, x)",
            "    residuals = y - y_pred",
            "    se_resid = float(np.std(residuals, ddof=3)) if n > 3 else 0.0",
            "    t_crit = _sp_stats.t.ppf(0.975, df=max(1, n - 3))",
            "    return dict(x_fit=x_fit.tolist(), y_fit=y_fit.tolist(),",
            "                y_lower=(y_fit - t_crit*se_resid).tolist(),",
            "                y_upper=(y_fit + t_crit*se_resid).tolist())",
            "",
            "",
            "def _compute_kdensity(df, varname):",
            '    """Return line source dict for kernel density estimate."""',
            "    data = df[varname].dropna().values.astype(float)",
            "    if len(data) < 2 or float(np.std(data)) == 0.0:",
            "        return dict(x=[], y=[])",
            "    kde = scipy_stats.gaussian_kde(data)",
            "    x_range = np.linspace(data.min(), data.max(), 200)",
            "    return dict(x=x_range.tolist(), y=kde(x_range).tolist())",
            "",
            "",
            "def _compute_lowess(df, yvar, xvar):",
            '    """Return line source dict for LOWESS smoother."""',
            "    clean = df[[xvar, yvar]].dropna().sort_values(xvar)",
            "    if len(clean) < 2:",
            "        return dict(x=[], y=[])",
            "    if _HAS_STATSMODELS:",
            "        smoothed = sm_lowess.lowess(clean[yvar].values, clean[xvar].values, frac=0.5)",
            "        return dict(x=smoothed[:, 0].tolist(), y=smoothed[:, 1].tolist())",
            "    else:",
            "        return dict(x=clean[xvar].tolist(), y=clean[yvar].tolist())",
            "",
            "",
            "def _lpoly_kernel_fit(x, y, bwidth=0.5, degree=0, n_grid=200):",
            '    """Gaussian kernel-weighted local polynomial regression."""',
            "    x_min, x_max = x.min(), x.max()",
            "    x_range = x_max - x_min or 1.0",
            "    h = bwidth * x_range",
            "    x_grid = np.linspace(x_min, x_max, n_grid)",
            "    y_fit = np.empty(n_grid)",
            "    for i, x0 in enumerate(x_grid):",
            "        w = np.exp(-0.5 * ((x - x0) / h) ** 2)",
            "        w_sum = w.sum()",
            "        if w_sum < 1e-12:",
            "            y_fit[i] = np.nan",
            "            continue",
            "        if degree == 0:",
            "            y_fit[i] = np.dot(w, y) / w_sum",
            "        else:",
            "            try:",
            "                c = np.polyfit(x, y, deg=degree, w=w)",
            "                y_fit[i] = np.polyval(c, x0)",
            "            except Exception:",
            "                y_fit[i] = np.dot(w, y) / w_sum",
            "    return x_grid, y_fit",
            "",
            "",
            "def _compute_lpoly(df, yvar, xvar, bwidth=0.5, degree=0):",
            '    """Return line source dict for local polynomial smoother."""',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 2:",
            "        return dict(x_lp=[], y_lp=[])",
            "    x = clean[xvar].values.astype(float)",
            "    y = clean[yvar].values.astype(float)",
            "    x_grid, y_fit = _lpoly_kernel_fit(x, y, bwidth=bwidth, degree=degree)",
            "    valid = ~np.isnan(y_fit)",
            "    return dict(x_lp=x_grid[valid].tolist(), y_lp=y_fit[valid].tolist())",
            "",
            "",
            "_FP_POWERS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)",
            "",
            "",
            "def _fp_transform(x, p):",
            '    """FP power transform: x^p (p==0 -> ln x)."""',
            "    with np.errstate(divide='ignore', invalid='ignore'):",
            "        if p == 0.0:",
            "            return np.where(x > 0, np.log(x.astype(float)), np.nan)",
            "        return np.where(x > 0, np.power(x.astype(float), p), np.nan)",
            "",
            "",
            "def _fit_fp2(x, y):",
            '    """Fit degree-2 FP: return (p1, p2, coeffs)."""',
            "    from itertools import combinations_with_replacement",
            "    best_rss = np.inf",
            "    best_p1, best_p2, best_c = 1.0, 2.0, np.array([y.mean(), 0.0, 0.0])",
            "    for p1, p2 in combinations_with_replacement(_FP_POWERS, 2):",
            "        z1 = _fp_transform(x, p1)",
            "        z2 = _fp_transform(x, p2)",
            "        ok = ~(np.isnan(z1) | np.isnan(z2) | np.isnan(y))",
            "        if ok.sum() < 4: continue",
            "        X = np.column_stack([np.ones(ok.sum()), z1[ok], z2[ok]])",
            "        try:",
            "            c, _, _, _ = np.linalg.lstsq(X, y[ok], rcond=None)",
            "            rss = float(np.sum((y[ok] - X @ c) ** 2))",
            "            if rss < best_rss:",
            "                best_rss, best_p1, best_p2, best_c = rss, p1, p2, c",
            "        except Exception: pass",
            "    return best_p1, best_p2, best_c",
            "",
            "",
            "def _predict_fp2(x_grid, p1, p2, coeffs):",
            '    """Evaluate FP-2 model on x_grid."""',
            "    return coeffs[0] + coeffs[1]*_fp_transform(x_grid, p1) + coeffs[2]*_fp_transform(x_grid, p2)",
            "",
            "",
            "def _compute_fpfit(df, yvar, xvar):",
            '    """Return line source dict for fractional polynomial fit."""',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 4:",
            "        return dict(x_fp=[], y_fp=[])",
            "    x = clean[xvar].values.astype(float)",
            "    y = clean[yvar].values.astype(float)",
            "    p1, p2, coeffs = _fit_fp2(x, y)",
            "    xp = x[x > 0]",
            "    if len(xp) == 0: return dict(x_fp=[], y_fp=[])",
            "    x_grid = np.linspace(float(np.percentile(x, 1)), float(np.percentile(x, 99)), 200)",
            "    x_grid = x_grid[x_grid > 0]",
            "    y_fit = _predict_fp2(x_grid, p1, p2, coeffs)",
            "    valid = ~np.isnan(y_fit)",
            "    return dict(x_fp=x_grid[valid].tolist(), y_fp=y_fit[valid].tolist())",
            "",
            "",
            "def _compute_mspline(df, yvar, xvar):",
            '    """Return spline source dict for mspline (PchipInterpolator)."""',
            "    try:",
            "        from scipy.interpolate import PchipInterpolator",
            "        clean = df[[xvar, yvar]].dropna().sort_values(xvar)",
            "        if len(clean) < 2:",
            "            return {'x_sp': [], 'y_sp': []}",
            "        interp = PchipInterpolator(clean[xvar].values, clean[yvar].values)",
            "        x_grid = np.linspace(float(clean[xvar].min()), float(clean[xvar].max()), 200)",
            "        y_grid = interp(x_grid)",
            "        return {'x_sp': x_grid.tolist(), 'y_sp': y_grid.tolist()}",
            "    except Exception:",
            "        return {'x_sp': [], 'y_sp': []}",
            "",
            "",
            "def _compute_mband(df, yvar, xvar):",
            '    """Return binned-median source dict for mband."""',
            "    try:",
            "        clean = df[[xvar, yvar]].dropna()",
            "        if len(clean) < 4:",
            "            return {'x_mb': [], 'y_mb': []}",
            "        x = clean[xvar].values",
            "        y = clean[yvar].values",
            "        n_bands = int(np.clip(int(np.ceil(len(x) / 5)), 2, 20))",
            "        x_edges = np.linspace(float(x.min()), float(x.max()), n_bands + 1)",
            "        xmids, ymeds = [], []",
            "        for bi in range(n_bands):",
            "            sel = (x >= x_edges[bi]) & ((x < x_edges[bi+1]) if bi < n_bands-1 else (x <= x_edges[bi+1]))",
            "            if sel.sum() > 0:",
            "                xmids.append(float(0.5*(x_edges[bi]+x_edges[bi+1])))",
            "                ymeds.append(float(np.median(y[sel])))",
            "        return {'x_mb': xmids, 'y_mb': ymeds}",
            "    except Exception:",
            "        return {'x_mb': [], 'y_mb': []}",
            "",
            "",
            "def _compute_rscatter(df, yvar1, yvar2, xvar):",
            '    """Return stacked source dict for rscatter (two y-vars over same x)."""',
            "    try:",
            "        if yvar1 not in df.columns or yvar2 not in df.columns or xvar not in df.columns:",
            "            return {'x': [], 'y': []}",
            "        xs = np.concatenate([df[xvar].values, df[xvar].values])",
            "        ys = np.concatenate([df[yvar1].values, df[yvar2].values])",
            "        mask = ~(np.isnan(xs.astype(float)) | np.isnan(ys.astype(float)))",
            "        return {'x': xs[mask].tolist(), 'y': ys[mask].tolist()}",
            "    except Exception:",
            "        return {'x': [], 'y': []}",
            "",
            "",
            "def _compute_pcscatter(df, y1var, x1var, y2var, x2var):",
            '    """Return stacked source dict for pcscatter (two paired coord sets)."""',
            "    try:",
            "        cols = [c for c in [y1var, x1var, y2var, x2var] if c in df.columns]",
            "        if len(cols) != 4:",
            "            return {'x': [], 'y': []}",
            "        clean = df[cols].dropna()",
            "        xs = np.concatenate([clean[x1var].values, clean[x2var].values])",
            "        ys = np.concatenate([clean[y1var].values, clean[y2var].values])",
            "        return {'x': xs.tolist(), 'y': ys.tolist()}",
            "    except Exception:",
            "        return {'x': [], 'y': []}",
            "",
            "",
            "def _compute_kpi(df, stat, varname):",
            '    """Compute a KPI statistic from df[varname]. Returns float."""',
            "    series = df[varname].dropna() if varname in df.columns else pd.Series([], dtype=float)",
            "    if len(series) == 0:",
            "        return float('nan')",
            "    stat = stat.lower()",
            "    if stat == 'mean':   return float(series.mean())",
            "    if stat == 'sum':    return float(series.sum())",
            "    if stat == 'count':  return float(len(series))",
            "    if stat == 'dcount': return float(series.nunique())",
            "    if stat == 'min':    return float(series.min())",
            "    if stat == 'max':    return float(series.max())",
            "    if stat == 'sd':     return float(series.std(ddof=1))",
            "    if stat in ('median', 'p50'): return float(series.median())",
            "    if stat == 'p25':    return float(series.quantile(0.25))",
            "    if stat == 'p75':    return float(series.quantile(0.75))",
            "    return float('nan')",
            "",
            "",
            "def _format_kpi(value, fmt_str):",
            '    """Format a KPI float value using a Stata-style format string.',
            "",
            "    Supports basic numeric Stata formats like %9.1f, %9.0g, %9.0fc.",
            "    Falls back to str(value) for unrecognised formats.",
            '    """',
            "    if math.isnan(value):",
            "        return '.'",
            "    if fmt_str:",
            "        m = re.match(r'%[0-9]*\\.([0-9]+)([fge])', fmt_str)",
            "        if m:",
            "            decimals = int(m.group(1))",
            "            kind = m.group(2)",
            "            if kind == 'f':  return f'{value:,.{decimals}f}'",
            "            if kind == 'g':  return f'{value:.{decimals}g}'",
            "            if kind == 'e':  return f'{value:.{decimals}e}'",
            "    return str(round(value, 4))",
            "",
            "",
        ]

        # ----------------------------------------------------------------
        # 4. make_document(doc)
        # ----------------------------------------------------------------
        lines += [
            "def make_document(doc):",
            '    """Bokeh Server document factory — called once per browser connection.',
            "",
            "    Builds the full dashboard layout including figures, KPI cards,",
            "    filter widgets, and wires all Python callbacks.",
            '    """',
            "    # ---- Rate-limit enforcement at session creation ----",
            "    # Extract client IP via the shared helper which prefers",
            "    # X-Forwarded-For (reverse-proxy client) over remote_ip (proxy IP).",
            "    try:",
            "        _req = doc.session_context.request",
            "        _client_ip = _client_ip_from_request(_req)",
            "    except Exception:",
            "        _client_ip = '0.0.0.0'",
            "    if not _LIMITER.is_allowed(_client_ip):",
            "        doc.add_root(Div(text=(",
            "            '<h2 style=\"font-family:sans-serif;color:#c00\">429 Too Many Requests</h2>'",
            "            '<p style=\"font-family:sans-serif\">Rate limit exceeded. '",
            "            'Please wait a moment before reconnecting.</p>'",
            "        )))",
            "        return",
            "",
            "    spec, df, meta = _load_spec_and_data()",
            "    graphs = spec.get('graphs', [])",
            "    kpi_defs = spec.get('kpis', [])",
            "    bo = spec.get('build_options', {})",
            "    link_opt = bo.get('link', '') or ''",
            "    title_text = html.escape(bo.get('title', '') or '')",
            "",
            "    var_labels = meta['var_labels']",
            "    val_label_names = meta['val_label_names']",
            "    val_labels = meta['val_labels']",
            "",
            "    # ---- Determine linked graphs ----",
            "    linked_names = set()",
            "    if link_opt == '_all':",
            "        for g in graphs:",
            "            n = g.get('graph_options', {}).get('name', '')",
            "            if n: linked_names.add(n)",
            "    elif link_opt:",
            "        linked_names = set(link_opt.split())",
            "",
            "    # ---- Collect all variable names ----",
            "    all_vars = set()",
            "    for g in graphs:",
            "        for p in g.get('plots', []):",
            "            for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2', 'y1var', 'x1var', 'y2var', 'x2var'):",
            "                v = p.get(k, '')",
            "                if v and v in df.columns: all_vars.add(v)",
            "    for kpi in kpi_defs:",
            "        v = kpi.get('var', '')",
            "        if v and v in df.columns: all_vars.add(v)",
            "",
            "    # ---- Build shared ColumnDataSource for linked graphs ----",
            "    linked_vars = list(all_vars)",
            "    shared_source = ColumnDataSource(",
            "        {v: df[v].tolist() if v in df.columns else [] for v in linked_vars}",
            "    ) if linked_vars else ColumnDataSource({})",
            "",
            "    # ---- Per-graph independent sources (for non-linked) ----",
            "    graph_sources: dict = {}",
            "    for g in graphs:",
            "        gname = g.get('graph_options', {}).get('name', '')",
            "        if gname in linked_names:",
            "            graph_sources[gname] = [shared_source]",
            "        else:",
            "            gvars = []",
            "            for p in g.get('plots', []):",
            "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2'):",
            "                    v = p.get(k, '')",
            "                    if v and v in df.columns and v not in gvars:",
            "                        gvars.append(v)",
            "            graph_sources[gname] = [ColumnDataSource(",
            "                {v: df[v].tolist() for v in gvars}",
            "            ) if gvars else ColumnDataSource({})]",
            "",
            "    # ---- Aggregated plot ColumnDataSources ----",
            "    # key: (gname, plot_index) → {'source': CDS, 'compute': callable}",
            "    agg_sources: dict = {}",
            "",
            "    # ---- Color resolution helper (handles named Stata colors + hex + RGB) ----",
            "    _SCOLOR = " + repr(dict(OptionTranslator._COLOR_MAP)),
            "    import re as _re_clr",
            "    def _resolve_color(c):",
            "        if not c or not isinstance(c, str): return ''",
            "        c = c.strip()",
            "        if _re_clr.fullmatch(r'#[0-9a-fA-F]{6}', c): return c",
            "        named = _SCOLOR.get(c.lower())",
            "        if named: return named",
            "        # RGB triplet '255 0 128'",
            "        parts = c.split()",
            "        if len(parts) == 3:",
            "            try:",
            "                r,g,b = [int(x) for x in parts]",
            "                if all(0 <= v <= 255 for v in (r,g,b)):",
            "                    return '#{:02x}{:02x}{:02x}'.format(r,g,b)",
            "            except ValueError: pass",
            "        return ''",
            "",
            "    # ---- AST whitelist validator for if_expr (shared by rendering + faceting) ----",
            "    import ast as _ast_g",
            "    _ALLOWED_G = frozenset({_ast_g.Expression, _ast_g.BoolOp,",
            "        _ast_g.And, _ast_g.Or, _ast_g.BinOp, _ast_g.BitAnd,",
            "        _ast_g.BitOr, _ast_g.Compare, _ast_g.Eq, _ast_g.NotEq,",
            "        _ast_g.Lt, _ast_g.LtE, _ast_g.Gt, _ast_g.GtE,",
            "        _ast_g.In, _ast_g.NotIn, _ast_g.UnaryOp, _ast_g.Not,",
            "        _ast_g.Invert, _ast_g.USub, _ast_g.Constant,",
            "        _ast_g.Name, _ast_g.Tuple, _ast_g.List, _ast_g.Load})",
            "    _SAFE_NAMES_G = frozenset({'True','False','None','nan','NaN','inf'})",
            "    def _safe_g(expr, cols):",
            "        if '@' in expr: return False",
            "        try: tree = _ast_g.parse(expr, mode='eval')",
            "        except SyntaxError: return False",
            "        cs = frozenset(str(c) for c in cols)",
            "        for nd in _ast_g.walk(tree):",
            "            if type(nd) not in _ALLOWED_G: return False",
            "            if isinstance(nd, _ast_g.Name) and nd.id not in cs and nd.id not in _SAFE_NAMES_G: return False",
            "        return True",
            "",
            "    # ---- Build figures ----",
            "    figures: dict = {}",
            "    TOOLS = [PanTool(), WheelZoomTool(), BoxSelectTool(), LassoSelectTool(), ResetTool()]",
            "",
            "    for g in graphs:",
            "        go = g.get('graph_options', {})",
            "        gname = go.get('name', '')",
            "        _src_list = graph_sources.get(gname)",
            "        src = (_src_list[-1] if isinstance(_src_list, list) and _src_list else shared_source)",
            "        # ---- Per-graph if_expr / in_expr filtering ----",
            "        # Read from graph_options first; fall back to top-level graph key",
            "        # so that qualifiers set by dash.ado at the graph level are honoured.",
            "        g_df = df.copy()",
            "        _g_in = (go.get('in_expr') or g.get('in_expr') or '').strip()",
            "        if _g_in:",
            "            _g_m = _re_clr.match(r'^(\\d+)/(\\d+)$', _g_in)",
            "            if _g_m:",
            "                _g_lo = max(0, int(_g_m.group(1)) - 1)",
            "                _g_hi = int(_g_m.group(2))",
            "                g_df = g_df.iloc[_g_lo:_g_hi].copy()",
            "        _g_if = (go.get('if_expr') or g.get('if_expr') or '').strip()",
            "        if _g_if:",
            "            _g_px = _g_if.replace('~=', '!=')",
            "            if _safe_g(_g_px, g_df.columns):",
            "                try: g_df = g_df.query(_g_px, engine='python')",
            "                except Exception: pass",
            "",
            "        x_label = ''",
            "        y_label = ''",
            "        plots = g.get('plots', [])",
            "        if plots:",
            "            xv = plots[0].get('xvar', '')",
            "            yv = plots[0].get('yvar', '') or plots[0].get('var', '')",
            "            raw_xt = go.get('xtitle', '')",
            "            raw_yt = go.get('ytitle', '')",
            "            x_label = html.escape(raw_xt) if raw_xt else var_labels.get(xv, xv)",
            "            y_label = html.escape(raw_yt) if raw_yt else var_labels.get(yv, yv)",
            "",
            "        n_rows = len(df)",
            "        backend = 'webgl' if n_rows > 10000 else 'canvas'",
            "        _fig_kw = dict(",
            "            title=html.escape(go.get('title', '') or ''),",
            "            x_axis_label=x_label,",
            "            y_axis_label=y_label,",
            "            tools=TOOLS,",
            "            sizing_mode='stretch_width',",
            "            output_backend=backend,",
            "        )",
            "        _raw_ar = go.get('aspectratio', '')",
            "        if _raw_ar:",
            "            try: _fig_kw['aspect_ratio'] = float(_raw_ar)",
            "            except (ValueError, TypeError): pass",
            "        _xs_toks = go.get('xscale', '').lower().split()",
            "        _ys_toks = go.get('yscale', '').lower().split()",
            "        if 'log' in _xs_toks: _fig_kw['x_axis_type'] = 'log'",
            "        if 'log' in _ys_toks: _fig_kw['y_axis_type'] = 'log'",
            "        fig = bokeh_figure(**_fig_kw)",
            "        if 'reverse' in _xs_toks:",
            "            try: fig.x_range.flipped = True",
            "            except AttributeError: pass",
            "        if 'reverse' in _ys_toks:",
            "            try: fig.y_range.flipped = True",
            "            except AttributeError: pass",
            "        # bgcolor / plotbgcolor — figure background colors",
            "        _raw_bgc = go.get('bgcolor', '')",
            "        if _raw_bgc:",
            "            _bgc_resolved = _resolve_color(_raw_bgc)",
            "            if _bgc_resolved: fig.border_fill_color = _bgc_resolved",
            "        _raw_pbgc = go.get('plotbgcolor', '')",
            "        if _raw_pbgc:",
            "            _pbgc_resolved = _resolve_color(_raw_pbgc)",
            "            if _pbgc_resolved: fig.background_fill_color = _pbgc_resolved",
            "        # plotregion() / graphregion() — Stata-standard region styling",
            "        def _region_color(val):",
            "            import re as _re2",
            "            m = _re2.search(r'\\bf?color\\s*\\(([^)]+)\\)', val, _re2.IGNORECASE)",
            "            return m.group(1).strip() if m else ''",
            "        def _region_lcolor(val):",
            "            import re as _re2",
            "            m = _re2.search(r'\\blcolor\\s*\\(([^)]+)\\)', val, _re2.IGNORECASE)",
            "            return m.group(1).strip() if m else ''",
            "        _raw_pr = go.get('plotregion', '')",
            "        if _raw_pr:",
            "            _pr_bg = _region_color(_raw_pr)",
            "            if _pr_bg:",
            "                _c = _resolve_color(_pr_bg)",
            "                if _c: fig.background_fill_color = _c",
            "            _pr_lc = _region_lcolor(_raw_pr)",
            "            if _pr_lc:",
            "                _c = _resolve_color(_pr_lc)",
            "                if _c: fig.outline_line_color = _c",
            "            import re as _re_lw",
            "            _pr_lw_m = _re_lw.search(r'\\blwidth\\s*\\(([^)]+)\\)', _raw_pr, _re_lw.IGNORECASE)",
            "            if _pr_lw_m:",
            "                try: fig.outline_line_width = float(_pr_lw_m.group(1).strip())",
            "                except (ValueError, TypeError): pass",
            "        _raw_gr = go.get('graphregion', '')",
            "        if _raw_gr:",
            "            _gr_bg = _region_color(_raw_gr)",
            "            if _gr_bg:",
            "                _c = _resolve_color(_gr_bg)",
            "                if _c: fig.border_fill_color = _c",
            "        # xrange / yrange axis limits",
            "        _raw_xr = go.get('xrange', '')",
            "        if _raw_xr:",
            "            _xr_parts = _raw_xr.split()",
            "            if len(_xr_parts) >= 2:",
            "                try: fig.x_range = Range1d(float(_xr_parts[0]), float(_xr_parts[1]))",
            "                except (ValueError, TypeError): pass",
            "        _raw_yr = go.get('yrange', '')",
            "        if _raw_yr:",
            "            _yr_parts = _raw_yr.split()",
            "            if len(_yr_parts) >= 2:",
            "                try: fig.y_range = Range1d(float(_yr_parts[0]), float(_yr_parts[1]))",
            "                except (ValueError, TypeError): pass",
            "        # note / caption annotations",
            "        from bokeh.models import Label as _Label",
            "        for _ann_key in ('note', 'caption'):",
            "            _ann_txt = go.get(_ann_key, '')",
            "            if _ann_txt:",
            "                fig.add_layout(_Label(x=0, y=0, x_units='screen', y_units='screen',",
            "                    text=html.escape(_ann_txt), text_font_size='11px', text_color='#555555'), 'below')",
            "        # subtitle annotation",
            "        _sub_txt = go.get('subtitle', '')",
            "        if _sub_txt:",
            "            fig.add_layout(_Label(x=0, y=0, x_units='screen', y_units='screen',",
            "                text=html.escape(_sub_txt), text_font_size='13px', text_color='#444444'), 'above')",
            "        # xline / yline reference lines",
            "        for _refkey, _dim in (('xline', 'height'), ('yline', 'width')):",
            "            _refraw = go.get(_refkey, '')",
            "            if _refraw:",
            "                for _rv in str(_refraw).split():",
            "                    try:",
            "                        fig.add_layout(Span(location=float(_rv),",
            "                            dimension=_dim, line_color='#888888',",
            "                            line_dash='dashed', line_width=1.0))",
            "                    except (ValueError, TypeError):",
            "                        pass",
            "        # legend placement and label() overrides",
            "        _leg_opt = go.get('legend', '')",
            "        if _leg_opt and fig.legend:",
            "            if _leg_opt == 'off': fig.legend.visible = False",
            "            else:",
            "                _leg_pos_map = {'top': 'top_center', 'bottom': 'bottom_center',",
            "                    'left': 'center_left', 'right': 'center_right', 'on': 'top_right'}",
            "                import re as _re_leg",
            "                for _kw, _loc in _leg_pos_map.items():",
            "                    if _re_leg.search(r'\\b' + _kw + r'\\b', _leg_opt):",
            "                        fig.legend.location = _loc; break",
            "                # label(N \"text\") overrides — XSS-safe via html.escape",
            "                for _lm in _re_leg.finditer(r'label\\(\\s*(\\d+)\\s+\"([^\"]*)\"\\s*\\)', _leg_opt):",
            "                    _li = int(_lm.group(1)) - 1",
            "                    _lt = html.escape(_lm.group(2))",
            "                    if fig.legend and 0 <= _li < len(fig.legend[0].items):",
            "                        fig.legend[0].items[_li].label = {'value': _lt}",
            "                # cols(#) / rows(#) — multi-column/row legend layout",
            "                _mc = _re_leg.search(r'\\bcols\\s*\\(\\s*(\\d+)\\s*\\)', _leg_opt)",
            "                _mr = _re_leg.search(r'\\brows\\s*\\(\\s*(\\d+)\\s*\\)', _leg_opt)",
            "                if _mc:",
            "                    try:",
            "                        [setattr(_lg, 'ncols', int(_mc.group(1))) for _lg in fig.legend]",
            "                    except (ValueError, AttributeError): pass",
            "                if _mr:",
            "                    try:",
            "                        [setattr(_lg, 'nrows', int(_mr.group(1))) for _lg in fig.legend]",
            "                    except (ValueError, AttributeError): pass",
            "        # xlabel / ylabel custom tick values",
            "        from bokeh.models.tickers import FixedTicker as _FT",
            "        from bokeh.models.formatters import CustomJSTickFormatter as _CJSF",
            "        import re as _re, json as _json",
            "        def _parse_axlabel(raw):",
            "            tks, labs = [], {}",
            "            toks = _re.findall(r'\"([^\"]*)\"|\\'([^\\']*)\\'|([^\\s,\"\\']+)', raw)",
            "            flat = [d or s or b for d,s,b in toks]",
            "            i = 0",
            "            while i < len(flat):",
            "                try:",
            "                    v = float(flat[i]); tks.append(v)",
            "                    if i+1 < len(flat):",
            "                        try: float(flat[i+1])",
            "                        except ValueError: labs[str(v)] = flat[i+1]; i += 1",
            "                except ValueError: pass",
            "                i += 1",
            "            return sorted(tks), labs",
            "        def _parse_axangle(raw):",
            "            import re as _re_ang, math as _math_ang",
            "            _m = _re_ang.search(r'\\bangle\\s*\\(\\s*([^)]+)\\s*\\)', raw, _re_ang.IGNORECASE)",
            "            if not _m: return None",
            "            _v = _m.group(1).strip().lower()",
            "            if _v == 'horizontal': return 0.0",
            "            if _v == 'vertical': return _math_ang.pi / 2",
            "            try: return _math_ang.radians(float(_v))",
            "            except ValueError: return None",
            "        for _axk, _axobj in (('xlabel', fig.xaxis), ('ylabel', fig.yaxis)):",
            "            _raw_ax = go.get(_axk, '')",
            "            if not _raw_ax: continue",
            "            _tks, _labs = _parse_axlabel(_raw_ax)",
            "            if _tks:",
            "                _axobj.ticker = _FT(ticks=_tks)",
            "                if _labs:",
            "                    _axobj.formatter = _CJSF(code=f'const m={_json.dumps(_labs)};return m[String(tick)]||String(tick);')",
            "            _ang = _parse_axangle(_raw_ax)",
            "            if _ang is not None: _axobj.major_label_orientation = _ang",
            "",
            "        for pi, plot in enumerate(plots):",
            "            ptype = plot.get('type', '')",
            "            yvar = plot.get('yvar', '') or plot.get('var', '')",
            "            xvar = plot.get('xvar', '')",
            "            y1var = plot.get('yvar1', '')",
            "            y2var = plot.get('yvar2', '')",
            "            opts = plot.get('options', {})",
            "",
            "            color = '#1f77b4'",
            "            if 'mcolor' in opts or 'lcolor' in opts:",
            "                _c = opts.get('mcolor', opts.get('lcolor', ''))",
            "                _resolved = _resolve_color(_c)",
            "                if _resolved: color = _resolved",
            "            # lwidth / lpattern — common to all line-bearing plot types",
            "            _lw_map = {'vvthin':0.4,'vthin':0.6,'thin':0.8,'medthin':1.0,",
            "                       'medium':1.5,'medthick':2.0,'thick':2.5,'vthick':3.5,'vvthick':5.0}",
            "            _lp_map = {'solid':[],'dash':[8,4],'dot':[2,4],'dash_dot':[8,4,2,4],",
            "                       'shortdash':[4,4],'shortdot':[2,2],'longdash':[16,4],'blank':[0,100]}",
            "            _line_width = _lw_map.get(opts.get('lwidth',''), 1.5)",
            "            _lpattern = opts.get('lpattern', '')",
            "            _line_dash = _lp_map.get(_lpattern, []) if _lpattern else []",
            "",
            "            if ptype in ('scatter',):",
            "                _sc_label_var = opts.get('mlabel', '')",
            "                _sc_cols = [c for c in [xvar, yvar, _sc_label_var] if c and c in g_df.columns]",
            "                clean = g_df[_sc_cols].dropna() if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean) if xvar and yvar else src",
            "                # --- jitter ---",
            "                _jitter_raw = opts.get('jitter', '')",
            "                _eff_x, _eff_y = xvar, yvar",
            "                if _jitter_raw:",
            "                    try:",
            "                        _jitter_pct = float(_jitter_raw)",
            "                    except (ValueError, TypeError):",
            "                        _jitter_pct = 0.0",
            "                    if _jitter_pct > 0:",
            "                        import numpy as _jnp",
            "                        _jseed_raw = opts.get('jseed', '')",
            "                        _jseed = int(float(_jseed_raw)) if _jseed_raw else None",
            "                        try: _jseed = int(float(_jseed_raw)) if _jseed_raw else None",
            "                        except (ValueError, TypeError): _jseed = None",
            "                        _jrng = _jnp.random.default_rng(_jseed)",
            "                        _xa = _jnp.asarray(csrc.data[xvar], dtype=float)",
            "                        _ya = _jnp.asarray(csrc.data[yvar], dtype=float)",
            "                        _xr = float(_jnp.nanmax(_xa) - _jnp.nanmin(_xa)) or 1.0",
            "                        _yr = float(_jnp.nanmax(_ya) - _jnp.nanmin(_ya)) or 1.0",
            "                        _hw_x = min(100.0, _jitter_pct) / 100.0 * _xr / 2.0",
            "                        _hw_y = min(100.0, _jitter_pct) / 100.0 * _yr / 2.0",
            "                        _jdata = dict(csrc.data)",
            "                        _jdata['_x_jit'] = (_xa + _jrng.uniform(-_hw_x, _hw_x, len(_xa))).tolist()",
            "                        _jdata['_y_jit'] = (_ya + _jrng.uniform(-_hw_y, _hw_y, len(_ya))).tolist()",
            "                        csrc = ColumnDataSource(_jdata)",
            "                        _eff_x, _eff_y = '_x_jit', '_y_jit'",
            "                _sc_fill = color",
            "                _mfc_val = opts.get('mfcolor', '')",
            "                if _mfc_val:",
            "                    _mfc_resolved = _resolve_color(_mfc_val)",
            "                    if _mfc_resolved: _sc_fill = _mfc_resolved",
            "                _ms_map = {'circle':'circle','square':'square','triangle':'triangle',",
            "                           'diamond':'diamond','plus':'plus','x':'x',",
            "                           'circle_cross':'circle_cross','circle_x':'circle_x',",
            "                           'square_cross':'square_cross','square_x':'square_x',",
            "                           'asterisk':'asterisk','cross':'cross'}",
            "                _sc_marker = _ms_map.get(opts.get('msymbol',''), 'circle')",
            "                _sz_map = {'tiny':4,'vsmall':5,'small':6,'medsmall':7,'medium':8,",
            "                           'medlarge':10,'large':12,'vlarge':16,'huge':20}",
            "                _sc_size = _sz_map.get(opts.get('msize',''), 8)",
            "                if opts.get('msize','').replace('.','',1).isdigit():",
            "                    _sc_size = float(opts.get('msize','8'))",
            "                _sc_angle_deg = opts.get('msangle', '')",
            "                _sc_angle = math.radians(float(_sc_angle_deg)) if _sc_angle_deg and _sc_angle_deg.strip().lstrip('-').replace('.','',1).isdigit() else 0.0",
            "                r = fig.scatter(x=_eff_x, y=_eff_y, source=csrc,",
            "                               fill_color=_sc_fill, line_color=color,",
            "                               size=_sc_size, marker=_sc_marker, alpha=0.7,",
            "                               angle=_sc_angle, angle_units='rad',",
            "                               nonselection_alpha=0.15)",
            "                fig.add_tools(HoverTool(tooltips=[(yvar, f'@{yvar}'), (xvar, f'@{xvar}')]))",
            "                # mlabel — add LabelSet annotation if option is set",
            "                _mlab_var = opts.get('mlabel', '')",
            "                if _mlab_var and _mlab_var in csrc.data:",
            "                    _mlab_kw = dict(x=xvar, y=yvar, text=_mlab_var, source=csrc,",
            "                                    text_font_size='9px', text_color='#333333',",
            "                                    x_offset=5, y_offset=5)",
            "                    _mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                    if _mlc: _mlab_kw['text_color'] = _mlc",
            "                    _mls_map = {'tiny':'7px','vsmall':'8px','small':'9px','medsmall':'10px',",
            "                                'medium':'11px','medlarge':'12px','large':'14px',",
            "                                'vlarge':'16px','huge':'20px'}",
            "                    _mls = _mls_map.get(opts.get('mlabsize',''), '')",
            "                    if _mls: _mlab_kw['text_font_size'] = _mls",
            "                    # mlabposition — clock position (0-12) → x/y offset",
            "                    _mlabpos_map = {",
            "                        '0':(0,10),'12':(0,10),'1':(7,7),'2':(10,0),'3':(10,-5),",
            "                        '4':(7,-7),'5':(4,-10),'6':(0,-10),'7':(-7,-7),'8':(-10,-5),",
            "                        '9':(-10,0),'10':(-7,7),'11':(-4,10)",
            "                    }",
            "                    _mlp = opts.get('mlabposition', '')",
            "                    if _mlp in _mlabpos_map:",
            "                        _mlabpos_x, _mlabpos_y = _mlabpos_map[_mlp]",
            "                        _mlab_kw['x_offset'] = _mlabpos_x",
            "                        _mlab_kw['y_offset'] = _mlabpos_y",
            "                    fig.add_layout(LabelSet(**_mlab_kw))",
            "                graph_sources[gname].append(csrc)  # update to clean source",
            "",
            "            elif ptype == 'line':",
            "                _line_mlab = opts.get('mlabel', '')",
            "                _line_cols = [c for c in [xvar, yvar, _line_mlab] if c and c in g_df.columns]",
            "                clean = g_df[_line_cols].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean)",
            "                _line_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _line_kw['line_dash'] = _line_dash",
            "                fig.line(x=xvar, y=yvar, source=csrc, **_line_kw)",
            "                graph_sources[gname].append(csrc)",
            "",
            "            elif ptype == 'lfit':",
            "                fit_data = _compute_lfit(g_df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'lfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _lfit_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _lfit_kw['line_dash'] = _line_dash",
            "                fig.line(x='x', y='y', source=fit_src, **_lfit_kw)",
            "",
            "            elif ptype == 'qfit':",
            "                fit_data = _compute_qfit(g_df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'qfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _qfit_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _qfit_kw['line_dash'] = _line_dash",
            "                fig.line(x='x', y='y', source=fit_src, **_qfit_kw)",
            "",
            "            elif ptype == 'histogram':",
            "                hvar = yvar or xvar",
            "                try: nbins = max(1, min(int(opts.get('bin', 20)), 1000))  # clamp: prevent resource exhaustion",
            "                except (ValueError, TypeError): nbins = 20",
            "                hist_data = _compute_histogram(g_df, hvar, nbins)",
            "                hist_src = ColumnDataSource(hist_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': hist_src,",
            "                    'type': 'histogram',",
            "                    'var': hvar, 'bins': nbins,",
            "                }",
            "                _hist_fill = color",
            "                _hfc = opts.get('fcolor', '')",
            "                if _hfc:",
            "                    _hfc_r = _resolve_color(_hfc)",
            "                    if _hfc_r: _hist_fill = _hfc_r",
            "                _hist_alpha = 0.8",
            "                _hfi = opts.get('fintensity', '')",
            "                if _hfi:",
            "                    try:",
            "                        _hv = _hfi.strip()",
            "                        _hist_alpha = min(1.0, max(0.0, float(_hv[5:])/100.0 if _hv.startswith('inten') else float(_hv)/100.0))",
            "                    except (ValueError, AttributeError): pass",
            "                _hist_line = 'white'",
            "                _hlc = opts.get('lcolor', '')",
            "                if _hlc:",
            "                    _hlc_r = _resolve_color(_hlc)",
            "                    if _hlc_r: _hist_line = _hlc_r",
            "                _hist_quad_kw = dict(fill_color=_hist_fill, line_color=_hist_line,",
            "                                     alpha=_hist_alpha, line_width=_line_width)",
            "                if _line_dash: _hist_quad_kw['line_dash'] = _line_dash",
            "                fig.quad(top='top', bottom=0, left='left', right='right',",
            "                         source=hist_src, **_hist_quad_kw)",
            "",
            "            elif ptype == 'kdensity':",
            "                kvar = yvar or xvar",
            "                kde_data = _compute_kdensity(g_df, kvar)",
            "                kde_src = ColumnDataSource(kde_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': kde_src,",
            "                    'type': 'kdensity',",
            "                    'var': kvar,",
            "                }",
            "                _kde_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _kde_kw['line_dash'] = _line_dash",
            "                fig.line(x='x', y='y', source=kde_src, **_kde_kw)",
            "",
            "            elif ptype == 'lowess':",
            "                lw_data = _compute_lowess(g_df, yvar, xvar)",
            "                lw_src = ColumnDataSource(lw_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': lw_src,",
            "                    'type': 'lowess',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _lowess_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _lowess_kw['line_dash'] = _line_dash",
            "                fig.line(x='x', y='y', source=lw_src, **_lowess_kw)",
            "",
            "            elif ptype == 'lpoly':",
            "                _lp_bw = 0.5",
            "                try: _lp_bw = max(0.01, min(1.0, float(opts.get('bwidth', '0.5') or '0.5')))",
            "                except (ValueError, TypeError): pass",
            "                _lp_deg = 0",
            "                try: _lp_deg = max(0, min(3, int(opts.get('degree', '0') or '0')))",
            "                except (ValueError, TypeError): pass",
            "                lp_data = _compute_lpoly(g_df, yvar, xvar, bwidth=_lp_bw, degree=_lp_deg)",
            "                lp_src = ColumnDataSource(lp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': lp_src, 'type': 'lpoly',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                    'bwidth': _lp_bw, 'degree': _lp_deg,",
            "                }",
            "                _lp_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _lp_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_lp', y='y_lp', source=lp_src, **_lp_kw)",
            "",
            "            elif ptype == 'lpolyci':",
            "                _lp_bw = 0.5",
            "                try: _lp_bw = max(0.01, min(1.0, float(opts.get('bwidth', '0.5') or '0.5')))",
            "                except (ValueError, TypeError): pass",
            "                _lp_deg = 0",
            "                try: _lp_deg = max(0, min(3, int(opts.get('degree', '0') or '0')))",
            "                except (ValueError, TypeError): pass",
            "                lp_data = _compute_lpoly(g_df, yvar, xvar, bwidth=_lp_bw, degree=_lp_deg)",
            "                lp_src = ColumnDataSource(lp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': lp_src, 'type': 'lpoly',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                    'bwidth': _lp_bw, 'degree': _lp_deg,",
            "                }",
            "                _lp_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _lp_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_lp', y='y_lp', source=lp_src, **_lp_kw)",
            "",
            "            elif ptype == 'fpfit':",
            "                fp_data = _compute_fpfit(g_df, yvar, xvar)",
            "                fp_src = ColumnDataSource(fp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fp_src, 'type': 'fpfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _fp_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _fp_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_fp', y='y_fp', source=fp_src, **_fp_kw)",
            "",
            "            elif ptype == 'fpfitci':",
            "                fp_data = _compute_fpfit(g_df, yvar, xvar)",
            "                fp_src = ColumnDataSource(fp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fp_src, 'type': 'fpfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _fp_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _fp_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_fp', y='y_fp', source=fp_src, **_fp_kw)",
            "",
            "            elif ptype in ('area',):",
            "                clean = g_df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                asrc = ColumnDataSource(clean)",
            "                _ar_base = 0.0",
            "                try: _ar_base = float(opts.get('base', '0') or '0')",
            "                except (ValueError, TypeError): pass",
            "                asrc.data['_zero'] = [_ar_base] * len(clean)",
            "                _ar_fill = color",
            "                _afc = opts.get('fcolor', '')",
            "                if _afc:",
            "                    _afc_r = _resolve_color(_afc)",
            "                    if _afc_r: _ar_fill = _afc_r",
            "                _ar_alpha = 0.4",
            "                _afi = opts.get('fintensity', '')",
            "                if _afi:",
            "                    try:",
            "                        _av = _afi.strip()",
            "                        _ar_alpha = min(1.0, max(0.0, float(_av[5:])/100.0 if _av.startswith('inten') else float(_av)/100.0))",
            "                    except (ValueError, AttributeError): pass",
            "                fig.varea(x=xvar, y1='_zero', y2=yvar, source=asrc,",
            "                          fill_color=_ar_fill, alpha=_ar_alpha)",
            "                graph_sources[gname].append(asrc)",
            "",
            "            elif ptype == 'bar':",
            "                clean = g_df[[xvar, yvar]].dropna() if xvar and yvar else g_df",
            "                bsrc = ColumnDataSource(clean)",
            "                x_arr = clean[xvar].values",
            "                width = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.8 if len(np.unique(x_arr)) > 1 else 1.0",
            "                for _bwkey in ('barwidth', 'width'):",
            "                    if opts.get(_bwkey):",
            "                        try: width = float(opts[_bwkey]); break",
            "                        except (ValueError, TypeError): pass",
            "                _bar_bottom = 0.0",
            "                try: _bar_bottom = float(opts.get('base', '0') or '0')",
            "                except (ValueError, TypeError): pass",
            "                _bar_fill = color",
            "                _bfc_raw = opts.get('bfcolor', '') or opts.get('fcolor', '')",
            "                if _bfc_raw:",
            "                    _bfc_r = _resolve_color(_bfc_raw)",
            "                    if _bfc_r: _bar_fill = _bfc_r",
            "                _bar_line = 'white'",
            "                _blc_raw = opts.get('blcolor', '')",
            "                if _blc_raw:",
            "                    _blc_r = _resolve_color(_blc_raw)",
            "                    if _blc_r: _bar_line = _blc_r",
            "                _bar_vbar_kw = dict(width=width, fill_color=_bar_fill,",
            "                                   line_color=_bar_line, line_width=_line_width)",
            "                if _line_dash: _bar_vbar_kw['line_dash'] = _line_dash",
            "                fig.vbar(x=xvar, top=yvar, bottom=_bar_bottom, source=bsrc, **_bar_vbar_kw)",
            "                graph_sources[gname].append(bsrc)",
            "",
            "            elif ptype == 'spike':",
            "                clean = g_df[[xvar, yvar]].dropna() if xvar and yvar else g_df",
            "                ssrc = ColumnDataSource(clean)",
            "                _sp_base = 0.0",
            "                try: _sp_base = float(opts.get('base', '0') or '0')",
            "                except (ValueError, TypeError): pass",
            "                ssrc.data['_zero'] = [_sp_base] * len(clean)",
            "                _seg_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _seg_kw['line_dash'] = _line_dash",
            "                fig.segment(x0=xvar, x1=xvar, y0='_zero', y1=yvar,",
            "                             source=ssrc, **_seg_kw)",
            "                graph_sources[gname].append(ssrc)",
            "",
            "            elif ptype == 'connected':",
            "                _conn_mlab = opts.get('mlabel', '')",
            "                _conn_cols = [c for c in [xvar, yvar, _conn_mlab] if c and c in g_df.columns]",
            "                clean = g_df[_conn_cols].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean)",
            "                _conn_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _conn_kw['line_dash'] = _line_dash",
            "                fig.line(x=xvar, y=yvar, source=csrc, **_conn_kw)",
            "                _conn_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                _conn_sz = _conn_ms_map.get(opts.get('msize',''), 8)",
            "                _conn_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus','circle_cross':'circle_cross','circle_dot':'circle_dot','hex':'hex'}",
            "                _conn_sym = _conn_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                _conn_mfc = color",
            "                _conn_mfc_raw = opts.get('mfcolor', '')",
            "                if _conn_mfc_raw:",
            "                    _cmfc_r = _resolve_color(_conn_mfc_raw)",
            "                    if _cmfc_r: _conn_mfc = _cmfc_r",
            "                fig.scatter(x=xvar, y=yvar, source=csrc, marker=_conn_sym,",
            "                            fill_color=_conn_mfc, line_color=color, size=_conn_sz, alpha=0.7)",
            "                graph_sources[gname].append(csrc)",
            "",
            "            elif ptype == 'dot':",
            "                _dot_mlab = opts.get('mlabel', '')",
            "                _dot_cols = [c for c in [xvar, yvar, _dot_mlab] if c and c in g_df.columns]",
            "                clean = g_df[_dot_cols].dropna() if xvar and yvar else g_df",
            "                dsrc = ColumnDataSource(clean)",
            "                _dot_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                _dot_sz = _dot_ms_map.get(opts.get('msize',''), 8)",
            "                _dot_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus','circle_cross':'circle_cross','circle_dot':'circle_dot','hex':'hex'}",
            "                _dot_sym = _dot_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                _dot_mfc = color",
            "                _dot_mfc_raw = opts.get('mfcolor', '')",
            "                if _dot_mfc_raw:",
            "                    _dmfc_r = _resolve_color(_dot_mfc_raw)",
            "                    if _dmfc_r: _dot_mfc = _dmfc_r",
            "                fig.scatter(x=xvar, y=yvar, source=dsrc, marker=_dot_sym,",
            "                            fill_color=_dot_mfc, line_color=color, size=_dot_sz, alpha=0.7)",
            "                graph_sources[gname].append(dsrc)",
            "",
            "            elif ptype == 'lfitci':",
            "                ci_data = _compute_lfitci(g_df, yvar, xvar)",
            "                fit_src = ColumnDataSource(ci_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'lfitci',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _lfci_fill = color",
            "                _lfci_fc = opts.get('fcolor', '')",
            "                if _lfci_fc:",
            "                    _lfci_fc_r = _resolve_color(_lfci_fc)",
            "                    if _lfci_fc_r: _lfci_fill = _lfci_fc_r",
            "                _lfci_alpha = 0.2",
            "                _lfci_fi = opts.get('fintensity', '')",
            "                if _lfci_fi:",
            "                    try:",
            "                        _v = _lfci_fi.strip()",
            "                        _lfci_alpha = min(1.0, max(0.0, float(_v[5:])/100.0 if _v.startswith('inten') else float(_v)/100.0))",
            "                    except (ValueError, AttributeError): pass",
            "                fig.varea(x='x_fit', y1='y_lower', y2='y_upper',",
            "                          source=fit_src, fill_color=_lfci_fill, alpha=_lfci_alpha)",
            "                _lfci_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _lfci_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_fit', y='y_fit', source=fit_src, **_lfci_kw)",
            "",
            "            elif ptype == 'qfitci':",
            "                ci_data = _compute_qfitci(g_df, yvar, xvar)",
            "                fit_src = ColumnDataSource(ci_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'qfitci',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                _qfci_fill = color",
            "                _qfci_fc = opts.get('fcolor', '')",
            "                if _qfci_fc:",
            "                    _qfci_fc_r = _resolve_color(_qfci_fc)",
            "                    if _qfci_fc_r: _qfci_fill = _qfci_fc_r",
            "                _qfci_alpha = 0.2",
            "                _qfci_fi = opts.get('fintensity', '')",
            "                if _qfci_fi:",
            "                    try:",
            "                        _v = _qfci_fi.strip()",
            "                        _qfci_alpha = min(1.0, max(0.0, float(_v[5:])/100.0 if _v.startswith('inten') else float(_v)/100.0))",
            "                    except (ValueError, AttributeError): pass",
            "                fig.varea(x='x_fit', y1='y_lower', y2='y_upper',",
            "                          source=fit_src, fill_color=_qfci_fill, alpha=_qfci_alpha)",
            "                _qfci_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _qfci_kw['line_dash'] = _line_dash",
            "                fig.line(x='x_fit', y='y_fit', source=fit_src, **_qfci_kw)",
            "",
            "            elif ptype == 'rarea':",
            "                if y1var and y2var and xvar:",
            "                    _ra_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _ra_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _ra_fill = color",
            "                    _ra_fc = opts.get('fcolor', '')",
            "                    if _ra_fc:",
            "                        _ra_fc_r = _resolve_color(_ra_fc)",
            "                        if _ra_fc_r: _ra_fill = _ra_fc_r",
            "                    _ra_alpha = 0.4",
            "                    _ra_fi = opts.get('fintensity', '')",
            "                    if _ra_fi:",
            "                        try:",
            "                            _rav = _ra_fi.strip()",
            "                            _ra_alpha = min(1.0, max(0.0, float(_rav[5:])/100.0 if _rav.startswith('inten') else float(_rav)/100.0))",
            "                        except (ValueError, AttributeError): pass",
            "                    fig.varea(x=xvar, y1=y1var, y2=y2var, source=rsrc,",
            "                              fill_color=_ra_fill, alpha=_ra_alpha)",
            "                    if _ra_mlab and _ra_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_ra_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'rbar':",
            "                if y1var and y2var and xvar:",
            "                    _rb_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rb_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    x_arr = rclean[xvar].values",
            "                    rw = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.8 if len(np.unique(x_arr)) > 1 else 1.0",
            "                    _rb_fill = color",
            "                    _rb_bfc = opts.get('bfcolor', '') or opts.get('fcolor', '')",
            "                    if _rb_bfc:",
            "                        _rb_bfc_r = _resolve_color(_rb_bfc)",
            "                        if _rb_bfc_r: _rb_fill = _rb_bfc_r",
            "                    _rb_line = 'white'",
            "                    _rb_blc = opts.get('blcolor', '')",
            "                    if _rb_blc:",
            "                        _rb_blc_r = _resolve_color(_rb_blc)",
            "                        if _rb_blc_r: _rb_line = _rb_blc_r",
            "                    _rbar_kw = dict(width=rw, fill_color=_rb_fill,",
            "                                   line_color=_rb_line, line_width=_line_width)",
            "                    if _line_dash: _rbar_kw['line_dash'] = _line_dash",
            "                    fig.vbar(x=xvar, bottom=y1var, top=y2var, source=rsrc, **_rbar_kw)",
            "                    if _rb_mlab and _rb_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_rb_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'rspike':",
            "                if y1var and y2var and xvar:",
            "                    _rsp_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rsp_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _rsp_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _rsp_kw['line_dash'] = _line_dash",
            "                    fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var,",
            "                                source=rsrc, **_rsp_kw)",
            "                    if _rsp_mlab and _rsp_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_rsp_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'rcap':",
            "                if y1var and y2var and xvar:",
            "                    _rcap_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rcap_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _rcap_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _rcap_kw['line_dash'] = _line_dash",
            "                    fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var,",
            "                                source=rsrc, **_rcap_kw)",
            "                    # Horizontal caps",
            "                    x_arr = rclean[xvar].values",
            "                    cap_hw = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.2 if len(np.unique(x_arr)) > 1 else 0.2",
            "                    cap_data = dict(",
            "                        x0_c=x_arr - cap_hw, x1_c=x_arr + cap_hw,",
            "                        yb=rclean[y1var].values, yt=rclean[y2var].values,",
            "                    )",
            "                    cap_src = ColumnDataSource(cap_data)",
            "                    fig.segment(x0='x0_c', y0='yb', x1='x1_c', y1='yb',",
            "                                source=cap_src, **_rcap_kw)",
            "                    fig.segment(x0='x0_c', y0='yt', x1='x1_c', y1='yt',",
            "                                source=cap_src, **_rcap_kw)",
            "                    if _rcap_mlab and _rcap_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_rcap_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'rline':",
            "                if y1var and y2var and xvar:",
            "                    _rl_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rl_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _rl_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _rl_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=y1var, source=rsrc, **_rl_kw)",
            "                    _rl2_kw = dict(line_color=color, line_width=_line_width, line_dash='dashed')",
            "                    if _line_dash: _rl2_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=y2var, source=rsrc, **_rl2_kw)",
            "                    if _rl_mlab and _rl_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_rl_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'rconnected':",
            "                if y1var and y2var and xvar:",
            "                    _rconn_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rconn_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _rc1_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _rc1_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=y1var, source=rsrc, **_rc1_kw)",
            "                    _rc_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                    _rc_sz = _rc_ms_map.get(opts.get('msize',''), 6)",
            "                    _rc_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus'}",
            "                    _rc_sym = _rc_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                    _rc_mfc = color",
            "                    _rc_mfc_raw = opts.get('mfcolor', '')",
            "                    if _rc_mfc_raw:",
            "                        _rc_mfc_r = _resolve_color(_rc_mfc_raw)",
            "                        if _rc_mfc_r: _rc_mfc = _rc_mfc_r",
            "                    fig.scatter(x=xvar, y=y1var, source=rsrc, marker=_rc_sym,",
            "                                fill_color=_rc_mfc, line_color=color, size=_rc_sz)",
            "                    _rc2_kw = dict(line_color=color, line_width=_line_width, line_dash='dashed')",
            "                    if _line_dash: _rc2_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=y2var, source=rsrc, **_rc2_kw)",
            "                    fig.scatter(x=xvar, y=y2var, source=rsrc, marker=_rc_sym,",
            "                                fill_color=_rc_mfc, line_color=color, size=_rc_sz)",
            "                    if _rconn_mlab and _rconn_mlab in rsrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x=xvar, y=y2var, text=_rconn_mlab, source=rsrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'dropline':",
            "                if yvar and xvar:",
            "                    _dl_mlab = opts.get('mlabel', '')",
            "                    _dl_cols = [c for c in [xvar, yvar, _dl_mlab] if c and c in g_df.columns]",
            "                    clean = g_df[_dl_cols].dropna()",
            "                    dsrc = ColumnDataSource({",
            "                        'x': clean[xvar].values,",
            "                        'y': clean[yvar].values,",
            "                        'y0': np.zeros(len(clean)),",
            "                    })",
            "                    if _dl_mlab and _dl_mlab in clean.columns:",
            "                        dsrc.data[_dl_mlab] = clean[_dl_mlab].values",
            "                    _dl_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _dl_kw['line_dash'] = _line_dash",
            "                    fig.segment(x0='x', y0='y0', x1='x', y1='y',",
            "                                source=dsrc, **_dl_kw)",
            "                    _dl_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                    _dl_sz = _dl_ms_map.get(opts.get('msize',''), 8)",
            "                    _dl_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus'}",
            "                    _dl_sym = _dl_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                    fig.scatter(x='x', y='y', source=dsrc, marker=_dl_sym,",
            "                                fill_color=color, line_color=color, size=_dl_sz)",
            "                    graph_sources[gname].append(dsrc)",
            "",
            "            elif ptype == 'rcapsym':",
            "                if y1var and y2var and xvar:",
            "                    _rcsym_mlab = opts.get('mlabel', '')",
            "                    rcols = [c for c in [y1var, y2var, xvar, _rcsym_mlab] if c and c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna()",
            "                    x_arr = rclean[xvar].values",
            "                    uniq_x = np.unique(x_arr)",
            "                    cap_hw = float(np.diff(np.sort(uniq_x)).min()) * 0.2 if len(uniq_x) > 1 else 0.2",
            "                    cap_data = dict(",
            "                        x=x_arr,",
            "                        y1=rclean[y1var].values, y2=rclean[y2var].values,",
            "                        x0_c=x_arr - cap_hw, x1_c=x_arr + cap_hw,",
            "                    )",
            "                    if _rcsym_mlab and _rcsym_mlab in rclean.columns:",
            "                        cap_data[_rcsym_mlab] = rclean[_rcsym_mlab].values",
            "                    csrc = ColumnDataSource(cap_data)",
            "                    _rcs_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _rcs_kw['line_dash'] = _line_dash",
            "                    fig.segment(x0='x', y0='y1', x1='x', y1='y2',",
            "                                source=csrc, **_rcs_kw)",
            "                    fig.segment(x0='x0_c', y0='y1', x1='x1_c', y1='y1',",
            "                                source=csrc, **_rcs_kw)",
            "                    fig.segment(x0='x0_c', y0='y2', x1='x1_c', y1='y2',",
            "                                source=csrc, **_rcs_kw)",
            "                    _rcsym_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                    _rcsym_sz = _rcsym_ms_map.get(opts.get('msize',''), 7)",
            "                    _rcsym_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus'}",
            "                    _rcsym_sym = _rcsym_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                    _rcsym_mfc = color",
            "                    _rcsym_mfc_raw = opts.get('mfcolor', '')",
            "                    if _rcsym_mfc_raw:",
            "                        _rcsym_mfc_r = _resolve_color(_rcsym_mfc_raw)",
            "                        if _rcsym_mfc_r: _rcsym_mfc = _rcsym_mfc_r",
            "                    fig.scatter(x='x', y='y1', source=csrc, marker=_rcsym_sym,",
            "                                fill_color=_rcsym_mfc, line_color=color, size=_rcsym_sz)",
            "                    fig.scatter(x='x', y='y2', source=csrc, marker=_rcsym_sym,",
            "                                fill_color=_rcsym_mfc, line_color=color, size=_rcsym_sz)",
            "                    if _rcsym_mlab and _rcsym_mlab in csrc.data:",
            "                        _r_mlc = _resolve_color(opts.get('mlabcolor', ''))",
            "                        _r_mlab_kw = dict(x='x', y='y2', text=_rcsym_mlab, source=csrc,",
            "                                          text_font_size='9px', text_color=_r_mlc or '#333333',",
            "                                          x_offset=5, y_offset=5)",
            "                        fig.add_layout(LabelSet(**_r_mlab_kw))",
            "                    graph_sources[gname].append(csrc)",
            "",
            "            elif ptype == 'scatteri':",
            "                vals = plot.get('values', [])",
            "                if vals:",
            "                    si_y = [float(p[0]) for p in vals]",
            "                    si_x = [float(p[1]) for p in vals]",
            "                    si_src = ColumnDataSource({'x': si_x, 'y': si_y})",
            "                    _si_ms_map = {'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}",
            "                    _si_sz = _si_ms_map.get(opts.get('msize',''), 8)",
            "                    _si_sym_map = {'circle':'circle','square':'square','triangle':'triangle','diamond':'diamond','x':'x','plus':'plus'}",
            "                    _si_sym = _si_sym_map.get(opts.get('msymbol',''), 'circle')",
            "                    _si_mfc = color",
            "                    _si_mfc_raw = opts.get('mfcolor', '')",
            "                    if _si_mfc_raw:",
            "                        _si_mfc_r = _resolve_color(_si_mfc_raw)",
            "                        if _si_mfc_r: _si_mfc = _si_mfc_r",
            "                    fig.scatter(x='x', y='y', source=si_src, marker=_si_sym,",
            "                                fill_color=_si_mfc, line_color=color, size=_si_sz)",
            "",
            "            elif ptype == 'pcspike':",
            "                pc_y1 = plot.get('y1var', '')",
            "                pc_x1 = plot.get('x1var', '')",
            "                pc_y2 = plot.get('y2var', '')",
            "                pc_x2 = plot.get('x2var', '')",
            "                if pc_y1 and pc_x1 and pc_y2 and pc_x2:",
            "                    cols = [c for c in [pc_y1, pc_x1, pc_y2, pc_x2] if c in g_df.columns]",
            "                    if len(cols) == 4:",
            "                        pclean = g_df[cols].dropna()",
            "                        pcsrc = ColumnDataSource(pclean)",
            "                        _pcs_kw = dict(line_color=color, line_width=_line_width)",
            "                        if _line_dash: _pcs_kw['line_dash'] = _line_dash",
            "                        fig.segment(x0=pc_x1, y0=pc_y1, x1=pc_x2, y1=pc_y2,",
            "                                    source=pcsrc, **_pcs_kw)",
            "                        graph_sources[gname].append(pcsrc)",
            "",
            "            elif ptype in ('pcarrow', 'pcbarrow'):",
            "                pc_y1 = plot.get('y1var', '')",
            "                pc_x1 = plot.get('x1var', '')",
            "                pc_y2 = plot.get('y2var', '')",
            "                pc_x2 = plot.get('x2var', '')",
            "                if pc_y1 and pc_x1 and pc_y2 and pc_x2:",
            "                    cols = [c for c in [pc_y1, pc_x1, pc_y2, pc_x2] if c in g_df.columns]",
            "                    if len(cols) == 4:",
            "                        pclean = g_df[cols].dropna()",
            "                        pcsrc = ColumnDataSource(pclean)",
            "                        _pca_kw = dict(line_color=color, line_width=_line_width)",
            "                        if _line_dash: _pca_kw['line_dash'] = _line_dash",
            "                        seg = fig.segment(x0=pc_x1, y0=pc_y1, x1=pc_x2, y1=pc_y2,",
            "                                    source=pcsrc, **_pca_kw)",
            "                        for _, _row in pclean.iterrows():",
            "                            _head_cls = NormalHead if ptype == 'pcbarrow' else OpenHead",
            "                            _arrow_kw = dict(end=_head_cls(size=10, line_color=color),",
            "                                x_start=float(_row[pc_x1]), y_start=float(_row[pc_y1]),",
            "                                x_end=float(_row[pc_x2]), y_end=float(_row[pc_y2]),",
            "                                line_color=color, line_width=_line_width)",
            "                            if ptype == 'pcbarrow':",
            "                                _arrow_kw['start'] = NormalHead(size=10, line_color=color)",
            "                            fig.add_layout(Arrow(**_arrow_kw))",
            "                        graph_sources[gname].append(pcsrc)",
            "",
            "            elif ptype == 'tsline':",
            "                _ts_mlab = opts.get('mlabel', '')",
            "                _ts_cols = [c for c in [xvar, yvar, _ts_mlab] if c and c in g_df.columns]",
            "                clean = g_df[_ts_cols].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean)",
            "                _ts_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _ts_kw['line_dash'] = _line_dash",
            "                fig.line(x=xvar, y=yvar, source=csrc, **_ts_kw)",
            "                graph_sources[gname].append(csrc)",
            "",
            "            elif ptype == 'tsrline':",
            "                ts_y1 = plot.get('yvar1', '')",
            "                ts_y2 = plot.get('yvar2', '')",
            "                if ts_y1 and ts_y2 and xvar:",
            "                    rcols = [c for c in [ts_y1, ts_y2, xvar] if c in g_df.columns]",
            "                    rclean = g_df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    _tsr1_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _tsr1_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=ts_y1, source=rsrc, **_tsr1_kw)",
            "                    _tsr2_kw = dict(line_color=color, line_width=_line_width, line_dash='dashed')",
            "                    if _line_dash: _tsr2_kw['line_dash'] = _line_dash",
            "                    fig.line(x=xvar, y=ts_y2, source=rsrc, **_tsr2_kw)",
            "                    graph_sources[gname].append(rsrc)",
            "",
            "            elif ptype == 'mspline':",
            "                if xvar and yvar:",
            "                    ms_data = _compute_mspline(g_df, yvar, xvar)",
            "                    ms_src = ColumnDataSource(ms_data)",
            "                    agg_sources[(gname, pi)] = {",
            "                        'source': ms_src, 'type': 'mspline',",
            "                        'yvar': yvar, 'xvar': xvar,",
            "                    }",
            "                    _ms_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _ms_kw['line_dash'] = _line_dash",
            "                    fig.line(x='x_sp', y='y_sp', source=ms_src, **_ms_kw)",
            "",
            "            elif ptype == 'mband':",
            "                if xvar and yvar:",
            "                    mb_data = _compute_mband(g_df, yvar, xvar)",
            "                    _mb_src = ColumnDataSource(mb_data)",
            "                    agg_sources[(gname, pi)] = {",
            "                        'source': _mb_src, 'type': 'mband',",
            "                        'yvar': yvar, 'xvar': xvar,",
            "                    }",
            "                    if mb_data['x_mb']:",
            "                        _mb_kw = dict(line_color=color, line_width=_line_width)",
            "                        if _line_dash: _mb_kw['line_dash'] = _line_dash",
            "                        fig.line(x='x_mb', y='y_mb', source=_mb_src, **_mb_kw)",
            "",
            "            elif ptype == 'rscatter':",
            "                y1v = plot.get('yvar', '') or plot.get('y1var', '') or plot.get('yvar1', '')",
            "                y2v = plot.get('y2var', '') or plot.get('yvar2', '')",
            "                xv  = plot.get('xvar', '')",
            "                if y1v and y2v and xv:",
            "                    _rs_data = _compute_rscatter(g_df, y1v, y2v, xv)",
            "                    _rs_src = ColumnDataSource(_rs_data)",
            "                    agg_sources[(gname, pi)] = {",
            "                        'source': _rs_src, 'type': 'rscatter',",
            "                        'yvar1': y1v, 'yvar2': y2v, 'xvar': xv,",
            "                    }",
            "                    fig.scatter('x', 'y', source=_rs_src, size=6, color=color, legend_label=y1v)",
            "",
            "            elif ptype in ('pci', 'pcscatter'):",
            "                y1v = plot.get('y1var', '')",
            "                x1v = plot.get('x1var', '')",
            "                y2v = plot.get('y2var', '')",
            "                x2v = plot.get('x2var', '')",
            "                if y1v and x1v and y2v and x2v:",
            "                    _cols = [c for c in [y1v, x1v, y2v, x2v] if c in g_df.columns]",
            "                    if len(_cols) == 4:",
            "                        _pc_clean = g_df[_cols].dropna()",
            "                        if ptype == 'pci':",
            "                            # Use actual column names — the standard replacement loop handles update",
            "                            _pc_src = ColumnDataSource({y1v: _pc_clean[y1v].tolist(), x1v: _pc_clean[x1v].tolist(), y2v: _pc_clean[y2v].tolist(), x2v: _pc_clean[x2v].tolist()})",
            "                            graph_sources[gname].append(_pc_src)",
            "                            _pc_kw = dict(line_color=color, line_width=_line_width)",
            "                            if _line_dash: _pc_kw['line_dash'] = _line_dash",
            "                            fig.segment(x0=x1v, y0=y1v, x1=x2v, y1=y2v, source=_pc_src, **_pc_kw)",
            "                        else:  # pcscatter — stacked coords, needs custom recompute",
            "                            _sc_data = _compute_pcscatter(g_df, y1v, x1v, y2v, x2v)",
            "                            _sc_src = ColumnDataSource(_sc_data)",
            "                            agg_sources[(gname, pi)] = {",
            "                                'source': _sc_src, 'type': 'pcscatter',",
            "                                'y1var': y1v, 'x1var': x1v, 'y2var': y2v, 'x2var': x2v,",
            "                            }",
            "                            fig.scatter('x', 'y', source=_sc_src, size=6, color=color, legend_label=y1v)",
            "",
            "            elif ptype == 'function':",
            "                import ast as _ast",
            "                import math as _math",
            "                pexpr = plot.get('expr', '')",
            "                opts = plot.get('options', {})",
            "                x_lo, x_hi = 0.0, 1.0",
            "                n_pts = 200",
            "                if 'range' in opts:",
            "                    _parts = opts['range'].split()",
            "                    if len(_parts) >= 2:",
            "                        try: x_lo, x_hi = float(_parts[0]), float(_parts[1])",
            "                        except ValueError: pass",
            "                if 'n' in opts:",
            "                    try: n_pts = max(2, min(int(opts['n']), 10000))  # clamp: prevent resource exhaustion",
            "                    except ValueError: pass",
            "                _SAFE_NAMES = frozenset({'x', 'pi', 'e'})",
            "                _SAFE_FUNCS = frozenset({'sin','cos','tan','exp','log','log10','sqrt','abs','floor','ceil'})",
            "                def _val_node(node):",
            "                    if isinstance(node, _ast.Expression): _val_node(node.body)",
            "                    elif isinstance(node, _ast.Constant): pass",
            "                    elif isinstance(node, _ast.Name):",
            "                        if node.id not in _SAFE_NAMES: raise ValueError(f'Unsafe name: {node.id!r}')",
            "                    elif isinstance(node, (_ast.operator, _ast.unaryop)):",
            "                        pass  # operator nodes (Add, Sub, USub, …) carry no dangerous state",
            "                    elif isinstance(node, (_ast.BinOp, _ast.UnaryOp)):",
            "                        for c in _ast.iter_child_nodes(node): _val_node(c)",
            "                    elif isinstance(node, _ast.Call):",
            "                        if not isinstance(node.func, _ast.Name) or node.func.id not in _SAFE_FUNCS:",
            "                            raise ValueError('Disallowed function call')",
            "                        for a in node.args: _val_node(a)",
            "                    else: raise ValueError(f'Disallowed node: {type(node).__name__}')",
            "                try:",
            "                    _tree = _ast.parse(pexpr, mode='eval')",
            "                    _val_node(_tree)",
            "                    _code = compile(_tree, '<function>', 'eval')",
            "                    _x = np.linspace(x_lo, x_hi, n_pts)",
            "                    _ns = {'x': _x, 'pi': _math.pi, 'e': _math.e,",
            "                           'sin': np.sin, 'cos': np.cos, 'tan': np.tan,",
            "                           'exp': np.exp, 'log': np.log, 'log10': np.log10,",
            "                           'sqrt': np.sqrt, 'abs': np.abs, 'floor': np.floor, 'ceil': np.ceil}",
            "                    _y = eval(_code, {'__builtins__': {}}, _ns)",
            "                    _y_arr = np.asarray(_y, dtype=float)",
            "                    # Broadcast scalar constants (e.g. 'pi', '3') to match x length",
            "                    if _y_arr.ndim == 0: _y_arr = np.full(len(_x), float(_y_arr))",
            "                    fn_src = ColumnDataSource({'x_fn': _x.tolist(), 'y_fn': _y_arr.tolist()})",
            "                    _fn_kw = dict(line_color=color, line_width=_line_width)",
            "                    if _line_dash: _fn_kw['line_dash'] = _line_dash",
            "                    fig.line(x='x_fn', y='y_fn', source=fn_src, **_fn_kw)",
            "                except Exception:",
            "                    pass",
            "",
            "            # ---- Common mlabel block (applies to all point/line plot types) ----",
            "            # Runs after each plot type's glyph is rendered",
            "            _mlab_var = opts.get('mlabel', '')",
            "            if (_mlab_var and xvar and yvar",
            "                    and ptype not in ('scatter',)",
            "                    and ptype not in ('histogram','hist','kdensity','lfit','qfit',",
            "                                      'lfitci','qfitci','lowess','mspline','function',",
            "                                      'rarea','rbar','rspike','rcap','rline','rconnected',",
            "                                      'rcapsym','scatteri','pcspike','pcarrow','pcbarrow',",
            "                                      'tsrline')):",
            "                _cur_src_list = graph_sources.get(gname)",
            "                _cur_src = (_cur_src_list[-1] if isinstance(_cur_src_list, list) and _cur_src_list else _cur_src_list)",
            "                if _cur_src and _mlab_var in _cur_src.data:",
            "                    _mlab_kw2 = dict(x=xvar, y=yvar, text=_mlab_var, source=_cur_src,",
            "                                     text_font_size='9px', text_color='#333333',",
            "                                     x_offset=5, y_offset=5)",
            "                    _mlc2 = _resolve_color(opts.get('mlabcolor', ''))",
            "                    if _mlc2: _mlab_kw2['text_color'] = _mlc2",
            "                    _mls_map2 = {'tiny':'7px','vsmall':'8px','small':'9px','medsmall':'10px',",
            "                                 'medium':'11px','medlarge':'12px','large':'14px',",
            "                                 'vlarge':'16px','huge':'20px'}",
            "                    _mls2 = _mls_map2.get(opts.get('mlabsize',''), '')",
            "                    if _mls2: _mlab_kw2['text_font_size'] = _mls2",
            "                    _mlabpos_map2 = {",
            "                        '0':(0,10),'12':(0,10),'1':(7,7),'2':(10,0),'3':(10,-5),",
            "                        '4':(7,-7),'5':(4,-10),'6':(0,-10),'7':(-7,-7),'8':(-10,-5),",
            "                        '9':(-10,0),'10':(-7,7),'11':(-4,10)",
            "                    }",
            "                    _mlp2 = opts.get('mlabposition', '')",
            "                    if _mlp2 in _mlabpos_map2:",
            "                        _xoff2, _yoff2 = _mlabpos_map2[_mlp2]",
            "                        _mlab_kw2['x_offset'] = _xoff2",
            "                        _mlab_kw2['y_offset'] = _yoff2",
            "                    fig.add_layout(LabelSet(**_mlab_kw2))",
            "",
            "        figures[gname] = fig",
            "",
            "    # ---- Persist per-graph qualifier metadata for filter callbacks ----",
            "    # Graph-level if_expr/in_expr are applied during initial rendering",
            "    # but must also be reapplied after each filter interaction so that",
            "    # qualified-out rows are not reintroduced by the callback.",
            "    _graph_qualifiers = {}  # gname → {'if_expr': ..., 'in_expr': ...}",
            "    for _gq in graphs:",
            "        _goq = _gq.get('graph_options', {})",
            "        _gnq = _goq.get('name', '')",
            "        _qi = (_goq.get('if_expr') or _gq.get('if_expr') or '').strip()",
            "        _qn = (_goq.get('in_expr') or _gq.get('in_expr') or '').strip()",
            "        if _qi or _qn:",
            "            _graph_qualifiers[_gnq] = {'if_expr': _qi, 'in_expr': _qn}",
            "",
            "    # ---- by() faceting: split figures into per-group panels ----",
            "    _facet_map = {}  # gname → [(facet_key, label)]",
            "    _facet_group_vals = {}  # facet_key → (by_vars, raw_group_key)",
            "    _UNSAFE_BY = _re_clr.compile(",
            "        r'[;`$\\\\]|import\\s|__|\\beval\\b|\\bexec\\b|\\bopen\\b'",
            "        r'|\\bgetattr\\b|\\bsetattr\\b|\\bhasattr\\b|\\bdelattr\\b'",
            "    )",
            "    for g in graphs:",
            "        go = g.get('graph_options', {})",
            "        gname = go.get('name', '')",
            "        by_raw = (go.get('by') or '').strip()",
            "        if not by_raw or _UNSAFE_BY.search(by_raw):",
            "            continue",
            "        # Parse varlist + suboptions from the raw by() string",
            "        _by_comma = by_raw.split(',', 1)",
            "        _by_varlist = _by_comma[0].strip()",
            "        _by_subopts = _by_comma[1].strip() if len(_by_comma) > 1 else ''",
            "        by_vars = [v for v in _by_varlist.split() if v in df.columns]",
            "        if not by_vars:",
            "            continue",
            "        import re as _re_by",
            "        _cols_m = _re_by.search(r'cols?\\((\\d+)\\)', _by_subopts, _re_by.IGNORECASE)",
            "        by_total = (bool(_re_by.search(r'\\btotal\\b', _by_subopts, _re_by.IGNORECASE))",
            "                    or go.get('by_total', '0') == '1')",
            "        by_missing = (bool(_re_by.search(r'\\bmissing\\b', _by_subopts, _re_by.IGNORECASE))",
            "                      or go.get('by_missing', '0') == '1')",
            "        # Apply graph-level qualifiers before faceting so by() groups",
            "        # are derived only from the qualifier-filtered subset, not global df.",
            "        _by_q_df = df.copy()",
            "        _by_in = (go.get('in_expr') or g.get('in_expr') or '').strip()",
            "        if _by_in:",
            "            _by_m = _re_clr.match(r'^(\\d+)/(\\d+)$', _by_in)",
            "            if _by_m:",
            "                _by_lo = max(0, int(_by_m.group(1)) - 1)",
            "                _by_hi = int(_by_m.group(2))",
            "                _by_q_df = _by_q_df.iloc[_by_lo:_by_hi].copy()",
            "        _by_if = (go.get('if_expr') or g.get('if_expr') or '').strip()",
            "        if _by_if:",
            "            _by_px = _by_if.replace('~=', '!=')",
            "            if _safe_g(_by_px, _by_q_df.columns):",
            "                try: _by_q_df = _by_q_df.query(_by_px, engine='python')",
            "                except Exception: pass",
            "        work_df = _by_q_df",
            "        if not by_missing:",
            "            work_df = work_df.dropna(subset=by_vars)",
            "        if work_df.empty:",
            "            continue",
            "        groupby_key = by_vars[0] if len(by_vars) == 1 else by_vars",
            "        facet_entries = []",
            "        # Remove the unfaceted figure",
            "        orig_fig = figures.pop(gname, None)",
            "        # For linked graphs keep shared source intact; for others pop it",
            "        if gname in linked_names:",
            "            orig_src = graph_sources.get(gname)",
            "        else:",
            "            orig_src = graph_sources.pop(gname, None)",
            "        for _fac_idx, (_fac_key, _fac_gdf) in enumerate(",
            "            work_df.groupby(groupby_key, sort=True, dropna=False)",
            "        ):",
            "            _fac_vals = (_fac_key,) if len(by_vars) == 1 else _fac_key",
            "            if not by_missing and any(pd.isna(v) for v in _fac_vals):",
            "                continue",
            "            # Build facet label using value labels",
            "            _fac_parts = []",
            "            for _bv, _bval in zip(by_vars, _fac_vals):",
            "                if pd.isna(_bval):",
            "                    _fac_parts.append('Missing')",
            "                    continue",
            "                _lset = val_label_names.get(_bv, '')",
            "                _vl = val_labels.get(_lset, {})",
            "                _sv = str(_bval)",
            "                _iv = str(int(_bval)) if isinstance(_bval, float) and _bval == int(_bval) else _sv",
            "                _fac_parts.append(html.escape(_vl.get(_sv) or _vl.get(_iv) or _sv))",
            "            _fac_label = ' / '.join(_fac_parts)",
            "            _fac_name = f'{gname}__by__{_fac_idx}'",
            "            # Build CDS for this facet (linked graphs use shared source + CDSView)",
            "            _fac_gvars = []",
            "            for p in g.get('plots', []):",
            "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2', 'y1var', 'x1var', 'y2var', 'x2var'):",
            "                    v = p.get(k, '')",
            "                    if v and v in _fac_gdf.columns and v not in _fac_gvars:",
            "                        _fac_gvars.append(v)",
            "            if gname in linked_names:",
            "                graph_sources[_fac_name] = [shared_source]",
            "                _fac_mask = [i in _fac_gdf.index for i in df.index]",
            "                _fac_view = CDSView(filter=BooleanFilter(booleans=_fac_mask))",
            "            else:",
            "                graph_sources[_fac_name] = [ColumnDataSource(",
            "                    {v: _fac_gdf[v].tolist() for v in _fac_gvars}",
            "                ) if _fac_gvars else ColumnDataSource({})]",
            "                _fac_view = None",
            "            # Clone the figure for this facet (rebuild from spec)",
            "            _fac_title = html.escape(go.get('title', '') or '')",
            "            if _fac_title:",
            "                _fac_title = f'{_fac_title} \\u2014 {_fac_label}'",
            "            else:",
            "                _fac_title = _fac_label",
            "            _fac_kw = dict(",
            "                title=_fac_title,",
            "                x_axis_label=var_labels.get(",
            "                    g.get('plots', [{}])[0].get('xvar', ''), ''),",
            "                y_axis_label=var_labels.get(",
            "                    g.get('plots', [{}])[0].get('yvar', '') or g.get('plots', [{}])[0].get('var', ''), ''),",
            "                tools=[PanTool(), WheelZoomTool(), BoxSelectTool(), LassoSelectTool(), ResetTool()],",
            "                sizing_mode='stretch_width',",
            "                output_backend='webgl' if len(df) > 10000 else 'canvas',",
            "            )",
            "            _fac_fig = bokeh_figure(**_fac_kw)",
            "            # Render plots on facet figure using facet CDS",
            "            _fac_src_list = graph_sources[_fac_name]",
            "            _fac_src = (_fac_src_list[0] if _fac_src_list else shared_source)",
            "            for pi, plot in enumerate(g.get('plots', [])):",
            "                ptype = plot.get('type', '').lower()",
            "                opts = plot.get('options', {})",
            "                yvar_f = plot.get('yvar', '') or plot.get('var', '')",
            "                xvar_f = plot.get('xvar', '')",
            "                color = _resolve_color(opts.get('lcolor') or opts.get('mcolor', '')) or '#1f77b4'",
            "                _glyph_kw = {'view': _fac_view} if _fac_view is not None else {}",
            "                if ptype == 'scatter':",
            "                    _fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=6, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype == 'line':",
            "                    _fac_fig.line(xvar_f, yvar_f, source=_fac_src, line_width=1.5, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('bar',):",
            "                    _fac_fig.vbar(x=xvar_f, top=yvar_f, source=_fac_src, width=0.8, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype == 'area':",
            "                    _fac_fig.varea(x=xvar_f, y1=0, y2=yvar_f, source=_fac_src, fill_color=color, fill_alpha=0.4, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('histogram', 'hist'):",
            "                    _hvar = plot.get('var', '') or yvar_f",
            "                    _hdata = _compute_histogram(_fac_gdf, _hvar)",
            "                    _hsrc = ColumnDataSource(_hdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _hsrc, 'type': 'histogram', 'var': _hvar, 'bins': 20}",
            "                    _fac_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6, legend_label=_hvar)",
            "                elif ptype == 'lfit':",
            "                    _lfdata = _compute_lfit(_fac_gdf, yvar_f, xvar_f)",
            "                    _lfsrc = ColumnDataSource(_lfdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _lfsrc, 'type': 'lfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _fac_fig.line('x', 'y', source=_lfsrc, line_width=1.5, color=color, legend_label=f'lfit {yvar_f}')",
            "                elif ptype == 'qfit':",
            "                    _qfdata = _compute_qfit(_fac_gdf, yvar_f, xvar_f)",
            "                    _qfsrc = ColumnDataSource(_qfdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _qfsrc, 'type': 'qfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _fac_fig.line('x', 'y', source=_qfsrc, line_width=1.5, color=color, legend_label=f'qfit {yvar_f}')",
            "                elif ptype == 'kdensity':",
            "                    _kdvar = plot.get('var', '') or yvar_f",
            "                    _kddata = _compute_kdensity(_fac_gdf, _kdvar)",
            "                    _kdsrc = ColumnDataSource(_kddata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _kdsrc, 'type': 'kdensity', 'var': _kdvar}",
            "                    _fac_fig.line('x', 'y', source=_kdsrc, line_width=1.5, color=color, legend_label=_kdvar)",
            "                elif ptype == 'lowess':",
            "                    _lwdata = _compute_lowess(_fac_gdf, yvar_f, xvar_f)",
            "                    _lwsrc = ColumnDataSource(_lwdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _lwsrc, 'type': 'lowess', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _fac_fig.line('x', 'y', source=_lwsrc, line_width=1.5, color=color, legend_label=f'lowess {yvar_f}')",
            "                elif ptype in ('lpoly', 'lpolyci'):",
            "                    _lp_bw_f = float(opts.get('bwidth', 0.5))",
            "                    _lp_deg_f = int(opts.get('degree', 0))",
            "                    _lpdata = _compute_lpoly(_fac_gdf, yvar_f, xvar_f, bwidth=_lp_bw_f, degree=_lp_deg_f)",
            "                    _lpsrc = ColumnDataSource(_lpdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _lpsrc, 'type': 'lpoly', 'yvar': yvar_f, 'xvar': xvar_f, 'bwidth': _lp_bw_f, 'degree': _lp_deg_f}",
            "                    _fac_fig.line('x_lp', 'y_lp', source=_lpsrc, line_width=1.5, color=color, legend_label=f'lpoly {yvar_f}')",
            "                elif ptype in ('fpfit', 'fpfitci'):",
            "                    _fpdata = _compute_fpfit(_fac_gdf, yvar_f, xvar_f)",
            "                    _fpsrc = ColumnDataSource(_fpdata)",
            "                    agg_sources[(_fac_name, pi)] = {'source': _fpsrc, 'type': 'fpfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _fac_fig.line('x_fp', 'y_fp', source=_fpsrc, line_width=1.5, color=color, legend_label=f'fpfit {yvar_f}')",
            "                elif ptype in ('connected',):",
            "                    _fac_fig.line(xvar_f, yvar_f, source=_fac_src, line_width=1.5, color=color, **_glyph_kw)",
            "                    _fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=6, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('dot',):",
            "                    _fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=8, color=color, marker='circle', legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('spike',):",
            "                    _fac_fig.segment(x0=xvar_f, y0=0, x1=xvar_f, y1=yvar_f, source=_fac_src, line_width=1.5, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype in ('dropline',):",
            "                    _fac_fig.segment(x0=xvar_f, y0=0, x1=xvar_f, y1=yvar_f, source=_fac_src, line_width=1.0, color=color, **_glyph_kw)",
            "                    _fac_fig.scatter(xvar_f, yvar_f, source=_fac_src, size=6, color=color, legend_label=yvar_f, **_glyph_kw)",
            "                elif ptype == 'mband':",
            "                    if xvar_f and yvar_f:",
            "                        _mb_d = _fac_gdf[[xvar_f, yvar_f]].dropna() if xvar_f in _fac_gdf.columns and yvar_f in _fac_gdf.columns else None",
            "                        if _mb_d is not None and len(_mb_d) >= 4:",
            "                            _mb_x = _mb_d[xvar_f].values; _mb_y = _mb_d[yvar_f].values",
            "                            _n_b = int(np.clip(int(np.ceil(len(_mb_x)/5)), 2, 20))",
            "                            _x_e = np.linspace(_mb_x.min(), _mb_x.max(), _n_b+1)",
            "                            _xm, _ym = [], []",
            "                            for _bi in range(_n_b):",
            "                                _s = (_mb_x >= _x_e[_bi]) & ((_mb_x < _x_e[_bi+1]) if _bi < _n_b-1 else (_mb_x <= _x_e[_bi+1]))",
            "                                if _s.sum(): _xm.append(float(0.5*(_x_e[_bi]+_x_e[_bi+1]))); _ym.append(float(np.median(_mb_y[_s])))",
            "                            if _xm:",
            "                                _fac_fig.line('x_mb', 'y_mb', source=ColumnDataSource({'x_mb': _xm, 'y_mb': _ym}), line_width=1.5, color=color, legend_label=yvar_f)",
            "            figures[_fac_name] = _fac_fig",
            "            facet_entries.append((_fac_name, _fac_label))",
            "            _facet_group_vals[_fac_name] = (by_vars, _fac_key)",
            "        if by_total:",
            "            _tot_name = f'{gname}__by__{len(facet_entries)}'",
            "            _tot_gvars = []",
            "            for p in g.get('plots', []):",
            "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2'):",
            "                    v = p.get(k, '')",
            "                    if v and v in work_df.columns and v not in _tot_gvars:",
            "                        _tot_gvars.append(v)",
            "            graph_sources[_tot_name] = [ColumnDataSource(",
            "                {v: work_df[v].tolist() for v in _tot_gvars}",
            "            )]",
            "            _tot_fig = bokeh_figure(",
            "                title='Total',",
            "                tools=[PanTool(), WheelZoomTool(), BoxSelectTool(), LassoSelectTool(), ResetTool()],",
            "                sizing_mode='stretch_width',",
            "                output_backend='webgl' if len(df) > 10000 else 'canvas',",
            "            )",
            "            _tot_src = graph_sources[_tot_name][0]",
            "            for pi, plot in enumerate(g.get('plots', [])):",
            "                ptype = plot.get('type', '').lower()",
            "                opts = plot.get('options', {})",
            "                yvar_f = plot.get('yvar', '') or plot.get('var', '')",
            "                xvar_f = plot.get('xvar', '')",
            "                color = _resolve_color(opts.get('lcolor') or opts.get('mcolor', '')) or '#1f77b4'",
            "                # Total panel uses full dispatch — same plot types as per-group facets.",
            "                # work_df plays the role of _fac_gdf for aggregates.",
            "                if ptype == 'scatter':",
            "                    _tot_fig.scatter(xvar_f, yvar_f, source=_tot_src, size=6, color=color, legend_label=yvar_f)",
            "                elif ptype == 'line':",
            "                    _tot_fig.line(xvar_f, yvar_f, source=_tot_src, line_width=1.5, color=color, legend_label=yvar_f)",
            "                elif ptype in ('bar',):",
            "                    _tot_fig.vbar(x=xvar_f, top=yvar_f, source=_tot_src, width=0.8, color=color, legend_label=yvar_f)",
            "                elif ptype == 'area':",
            "                    _tot_fig.varea(x=xvar_f, y1=0, y2=yvar_f, source=_tot_src, fill_color=color, fill_alpha=0.4, legend_label=yvar_f)",
            "                elif ptype in ('histogram', 'hist'):",
            "                    _hvar = plot.get('var', '') or yvar_f",
            "                    _hdata = _compute_histogram(work_df, _hvar)",
            "                    _hsrc = ColumnDataSource(_hdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _hsrc, 'type': 'histogram', 'var': _hvar, 'bins': 20}",
            "                    _tot_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6, legend_label=_hvar)",
            "                elif ptype == 'lfit':",
            "                    _lfdata = _compute_lfit(work_df, yvar_f, xvar_f)",
            "                    _lfsrc = ColumnDataSource(_lfdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _lfsrc, 'type': 'lfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _tot_fig.line('x', 'y', source=_lfsrc, line_width=1.5, color=color, legend_label=f'lfit {yvar_f}')",
            "                elif ptype == 'qfit':",
            "                    _qfdata = _compute_qfit(work_df, yvar_f, xvar_f)",
            "                    _qfsrc = ColumnDataSource(_qfdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _qfsrc, 'type': 'qfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _tot_fig.line('x', 'y', source=_qfsrc, line_width=1.5, color=color, legend_label=f'qfit {yvar_f}')",
            "                elif ptype == 'kdensity':",
            "                    _kdvar = plot.get('var', '') or yvar_f",
            "                    _kddata = _compute_kdensity(work_df, _kdvar)",
            "                    _kdsrc = ColumnDataSource(_kddata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _kdsrc, 'type': 'kdensity', 'var': _kdvar}",
            "                    _tot_fig.line('x', 'y', source=_kdsrc, line_width=1.5, color=color, legend_label=_kdvar)",
            "                elif ptype == 'lowess':",
            "                    _lwdata = _compute_lowess(work_df, yvar_f, xvar_f)",
            "                    _lwsrc = ColumnDataSource(_lwdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _lwsrc, 'type': 'lowess', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _tot_fig.line('x', 'y', source=_lwsrc, line_width=1.5, color=color, legend_label=f'lowess {yvar_f}')",
            "                elif ptype in ('lpoly', 'lpolyci'):",
            "                    _lp_bw_t = float(opts.get('bwidth', 0.5))",
            "                    _lp_deg_t = int(opts.get('degree', 0))",
            "                    _lpdata = _compute_lpoly(work_df, yvar_f, xvar_f, bwidth=_lp_bw_t, degree=_lp_deg_t)",
            "                    _lpsrc = ColumnDataSource(_lpdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _lpsrc, 'type': 'lpoly', 'yvar': yvar_f, 'xvar': xvar_f, 'bwidth': _lp_bw_t, 'degree': _lp_deg_t}",
            "                    _tot_fig.line('x_lp', 'y_lp', source=_lpsrc, line_width=1.5, color=color, legend_label=f'lpoly {yvar_f}')",
            "                elif ptype in ('fpfit', 'fpfitci'):",
            "                    _fpdata = _compute_fpfit(work_df, yvar_f, xvar_f)",
            "                    _fpsrc = ColumnDataSource(_fpdata)",
            "                    agg_sources[(_tot_name, pi)] = {'source': _fpsrc, 'type': 'fpfit', 'yvar': yvar_f, 'xvar': xvar_f}",
            "                    _tot_fig.line('x_fp', 'y_fp', source=_fpsrc, line_width=1.5, color=color, legend_label=f'fpfit {yvar_f}')",
            "                elif ptype in ('connected',):",
            "                    _tot_fig.line(xvar_f, yvar_f, source=_tot_src, line_width=1.5, color=color)",
            "                    _tot_fig.scatter(xvar_f, yvar_f, source=_tot_src, size=6, color=color, legend_label=yvar_f)",
            "                elif ptype in ('dot',):",
            "                    _tot_fig.scatter(xvar_f, yvar_f, source=_tot_src, size=8, color=color, marker='circle', legend_label=yvar_f)",
            "                elif ptype in ('spike',):",
            "                    _tot_fig.segment(x0=xvar_f, y0=0, x1=xvar_f, y1=yvar_f, source=_tot_src, line_width=1.5, color=color, legend_label=yvar_f)",
            "                elif ptype in ('dropline',):",
            "                    _tot_fig.segment(x0=xvar_f, y0=0, x1=xvar_f, y1=yvar_f, source=_tot_src, line_width=1.0, color=color)",
            "                    _tot_fig.scatter(xvar_f, yvar_f, source=_tot_src, size=6, color=color, legend_label=yvar_f)",
            "                elif ptype == 'mband':",
            "                    if xvar_f and yvar_f:",
            "                        _mb_d_t = work_df[[xvar_f, yvar_f]].dropna() if xvar_f in work_df.columns and yvar_f in work_df.columns else None",
            "                        if _mb_d_t is not None and len(_mb_d_t) >= 4:",
            "                            _mb_x_t = _mb_d_t[xvar_f].values; _mb_y_t = _mb_d_t[yvar_f].values",
            "                            _n_b_t = int(np.clip(int(np.ceil(len(_mb_x_t)/5)), 2, 20))",
            "                            _x_e_t = np.linspace(_mb_x_t.min(), _mb_x_t.max(), _n_b_t+1)",
            "                            _xm_t, _ym_t = [], []",
            "                            for _bi_t in range(_n_b_t):",
            "                                _s_t = (_mb_x_t >= _x_e_t[_bi_t]) & ((_mb_x_t < _x_e_t[_bi_t+1]) if _bi_t < _n_b_t-1 else (_mb_x_t <= _x_e_t[_bi_t+1]))",
            "                                if _s_t.sum(): _xm_t.append(float(0.5*(_x_e_t[_bi_t]+_x_e_t[_bi_t+1]))); _ym_t.append(float(np.median(_mb_y_t[_s_t])))",
            "                            if _xm_t:",
            "                                _tot_fig.line('x_mb', 'y_mb', source=ColumnDataSource({'x_mb': _xm_t, 'y_mb': _ym_t}), line_width=1.5, color=color, legend_label=yvar_f)",
            "            figures[_tot_name] = _tot_fig",
            "            facet_entries.append((_tot_name, 'Total'))",
            "            _facet_group_vals[_tot_name] = (by_vars, None)  # Total = no group filter",
            "        _facet_map[gname] = facet_entries",
            "",
            "    # ---- Build KPI Divs ----",
            "    kpi_divs: dict = {}",
            "    for kpi in kpi_defs:",
            "        kname = kpi.get('name', '')",
            "        kstat = kpi.get('stat', 'mean')",
            "        kvar  = kpi.get('var', '')",
            "        kfmt  = kpi.get('fmt', '')",
            "        ktitle = html.escape(kpi.get('title', '') or '')",
            "        ksub   = html.escape(kpi.get('subtitle', '') or '')",
            "        kcolor = kpi.get('color', '#333333') or '#333333'",
            "        kbg    = kpi.get('bgcolor', '#f8f9fa') or '#f8f9fa'",
            "        val = _compute_kpi(df, kstat, kvar)",
            "        disp = _format_kpi(val, kfmt)",
            "        div_html = (",
            "            f'<div style=\"background:{html.escape(kbg)};border-radius:8px;'",
            "            f'padding:16px;text-align:center;font-family:sans-serif;\">'",
            "            f'<div style=\"font-size:13px;color:#888;margin-bottom:4px;\">{ktitle}</div>'",
            "            f'<div id=\"kpi_val_{html.escape(kname)}\" style=\"font-size:28px;font-weight:bold;color:{html.escape(kcolor)};\">{html.escape(disp)}</div>'",
            "            f'<div style=\"font-size:11px;color:#aaa;margin-top:4px;\">{ksub}</div>'",
            "            f'</div>'",
            "        )",
            "        kpi_divs[kname] = Div(text=div_html, sizing_mode='stretch_width')",
            "",
            "    # Reverse map: faceted gname → original gname (for qualifier lookup).",
            "    # Faceted graph names (e.g. 'g1 — 0') are children of original names;",
            "    # the qualifier from the original graph applies to all its facets.",
            "    _facet_to_orig = {}",
            "    for _orig_gn, _fentries in _facet_map.items():",
            "        for _fgn, _ in _fentries:",
            "            _facet_to_orig[_fgn] = _orig_gn",
            "",
            "    # ---- Filter widgets + Python callbacks ----",
            "    filter_widgets: list = []",
            "    filter_var_widgets: dict = {}  # var -> widget",
            "    filter_specs_local = []",
            "",
        ]

        # Build filter specs from parsed filter_specs
        if filter_specs:
            lines += [
                "    _filter_specs = " + repr(filter_specs),
                "",
            ]
        else:
            lines += [
                "    _filter_specs = []",
                "",
            ]

        lines += [
            "    for fspec in _filter_specs:",
            "        fvar = fspec['var']",
            "        ftype = fspec['type']",
            "        fexcl = fspec.get('exclude', [])",
            "        if fvar not in df.columns:",
            "            continue",
            "        if ftype == 'dropdown':",
            "            uniq = sorted(df[fvar].dropna().unique())",
            "            # Apply value labels if available",
            "            lset = meta['val_label_names'].get(fvar, '')",
            "            vlabels = meta['val_labels'].get(lset, {})",
            "            # Build (raw_value, display_label) tuples for Select options.",
            "            # Using raw values as option keys avoids label-collision bugs where",
            "            # two categories share the same display label and one becomes",
            "            # Compute a per-widget sentinel absent from actual data values",
            "            # so that real categories equal to '__all__' remain selectable.",
            "            _uniq_strs = set(str(v) for v in uniq)",
            "            _sent = '__all__'",
            "            while _sent in _uniq_strs: _sent += '_'",
            "            opts = [(_sent, 'All')] + [",
            "                (str(v), html.escape(str(vlabels.get(str(int(v)) if isinstance(v, float) and v == int(v) else str(v), v))))",
            "                for v in uniq",
            "            ]",
            "            widget = Select(",
            "                title=var_labels.get(fvar, fvar),",
            "                value=_sent,",
            "                options=opts,",
            "            )",
            "            widget._dash_var = fvar",
            "            widget._dash_exclude = fexcl",
            "            widget._dash_sentinel = _sent",
            "        elif ftype == 'range':",
            "            # Guard: slider/range require a numeric column; fall back gracefully.",
            "            if not pd.api.types.is_numeric_dtype(df[fvar]):",
            "                import warnings",
            "                warnings.warn(",
            "                    f'dash: filter {fvar!r} type \\'range\\' requires numeric data; '",
            "                    f'skipping widget (use type(dropdown) for string columns).',",
            "                    UserWarning, stacklevel=2,",
            "                )",
            "                continue",
            "            vmin = float(df[fvar].min())",
            "            vmax = float(df[fvar].max())",
            "            widget = RangeSlider(",
            "                title=var_labels.get(fvar, fvar),",
            "                start=vmin, end=vmax,",
            "                value=(vmin, vmax),",
            "                step=(vmax - vmin) / 100 if vmax != vmin else 1.0,",
            "            )",
            "            widget._dash_var = fvar",
            "            widget._dash_exclude = fexcl",
            "        elif ftype == 'slider':",
            "            # Guard: slider/range require a numeric column; fall back gracefully.",
            "            if not pd.api.types.is_numeric_dtype(df[fvar]):",
            "                import warnings",
            "                warnings.warn(",
            "                    f'dash: filter {fvar!r} type \\'slider\\' requires numeric data; '",
            "                    f'skipping widget (use type(dropdown) for string columns).',",
            "                    UserWarning, stacklevel=2,",
            "                )",
            "                continue",
            "            vmin = float(df[fvar].min())",
            "            vmax = float(df[fvar].max())",
            "            widget = Slider(",
            "                title=var_labels.get(fvar, fvar),",
            "                start=vmin, end=vmax, value=vmin,",
            "                step=(vmax - vmin) / 100 if vmax != vmin else 1.0,",
            "            )",
            "            widget._dash_var = fvar",
            "            widget._dash_exclude = fexcl",
            "        else:",
            "            continue",
            "        filter_widgets.append(widget)",
            "        filter_var_widgets[fvar] = widget",
            "",
            "    # ---- Wire filter callbacks ----",
            "    # Snapshot original (pre-filter) data for every raw source so that",
            "    # derived columns that are not in _df_ref (e.g. _x_jit/_y_jit from",
            "    # jitter()) can be correctly filtered by row index instead of being",
            "    # blanked with [] after each filter interaction.",
            "    _orig_src_data: dict = {}",
            "    for _gs_list in graph_sources.values():",
            "        for _s in (_gs_list if isinstance(_gs_list, list) else [_gs_list]):",
            "            _orig_src_data[id(_s)] = {c: list(v) for c, v in _s.data.items()}",
            "",
            "    def _make_filter_cb(_trig_widget, _all_widgets, _all_sources, _agg_srcs, _kpi_divs, _kpi_defs, _df_ref, _fmap, _fgvals, _orig_src_data, _gquals, _gfac_to_orig):",
            "        def _on_filter_change(attr, old, new):",
            "            # 1. Build combined mask from all active widgets",
            "            mask = pd.Series([True] * len(_df_ref), index=_df_ref.index)",
            "            for w in _all_widgets:",
            "                wvar = getattr(w, '_dash_var', None)",
            "                if wvar is None or wvar not in _df_ref.columns:",
            "                    continue",
            "                if isinstance(w, Select):",
            "                    # Use per-widget sentinel (may differ from '__all__' when data",
            "                    # contains the literal string '__all__').",
            "                    _w_sentinel = getattr(w, '_dash_sentinel', '__all__')",
            "                    if w.value != _w_sentinel:",
            "                        # w.value is the raw value (Select uses (value, label) tuples)",
            "                        try:",
            "                            mask &= (_df_ref[wvar].astype(str) == str(w.value))",
            "                        except Exception:",
            "                            pass",
            "                elif isinstance(w, RangeSlider):",
            "                    lo, hi = w.value",
            "                    mask &= (_df_ref[wvar] >= lo) & (_df_ref[wvar] <= hi)",
            "                elif isinstance(w, Slider):",
            "                    mask &= (_df_ref[wvar] >= w.value)",
            "            fdf = _df_ref[mask]",
            "            # 2. Replace raw source data (facet-aware)",
            "            excl = getattr(_trig_widget, '_dash_exclude', [])",
            "            for gname, srcs in _all_sources.items():",
            "                if gname in excl:",
            "                    continue",
            "                # For faceted sources, further filter by group value",
            "                if gname in _fgvals:",
            "                    _bvs, _gkey = _fgvals[gname]",
            "                    if _gkey is None:",
            "                        # Total facet: use global filtered data",
            "                        _gdf = fdf",
            "                    else:",
            "                        # Apply group filter on top of global mask",
            "                        _facet_mask = mask.copy()",
            "                        if len(_bvs) == 1:",
            "                            _facet_mask = mask & (_df_ref[_bvs[0]] == _gkey)",
            "                        else:",
            "                            for _bv, _gv in zip(_bvs, _gkey):",
            "                                _facet_mask = _facet_mask & (_df_ref[_bv] == _gv)",
            "                        _gdf = _df_ref[_facet_mask]",
            "                else:",
            "                    _gdf = fdf",
            "                # Reapply graph-level if_expr/in_expr qualifier so that",
            "                # rows excluded by the qualifier are not reintroduced after",
            "                # each filter interaction (Bug #33 fix).",
            "                _orig_gn_cb = _gfac_to_orig.get(gname, gname)",
            "                _qual_cb = _gquals.get(_orig_gn_cb, {})",
            "                _in_cb = _qual_cb.get('in_expr', '').strip()",
            "                _if_cb = _qual_cb.get('if_expr', '').strip()",
            "                if _in_cb:",
            "                    import re as _re_cb",
            "                    _m_cb = _re_cb.match(r'^(\\d+)/(\\d+)$', _in_cb)",
            "                    if _m_cb:",
            "                        _lo_cb = max(0, int(_m_cb.group(1)) - 1)",
            "                        _hi_cb = int(_m_cb.group(2))",
            "                        _gdf = _gdf.iloc[_lo_cb:_hi_cb]",
            "                if _if_cb:",
            "                    import ast as _ast_cb",
            "                    _ALLOW_CB = frozenset({_ast_cb.Expression, _ast_cb.BoolOp,",
            "                        _ast_cb.And, _ast_cb.Or, _ast_cb.BinOp, _ast_cb.BitAnd,",
            "                        _ast_cb.BitOr, _ast_cb.Compare, _ast_cb.Eq, _ast_cb.NotEq,",
            "                        _ast_cb.Lt, _ast_cb.LtE, _ast_cb.Gt, _ast_cb.GtE,",
            "                        _ast_cb.In, _ast_cb.NotIn, _ast_cb.UnaryOp, _ast_cb.Not,",
            "                        _ast_cb.Invert, _ast_cb.USub, _ast_cb.Constant,",
            "                        _ast_cb.Name, _ast_cb.Tuple, _ast_cb.List, _ast_cb.Load})",
            "                    _SNAMES_CB = frozenset({'True','False','None','nan','NaN','inf'})",
            "                    def _safe_g_cb(expr, cols):",
            "                        if '@' in expr: return False",
            "                        try: tree = _ast_cb.parse(expr, mode='eval')",
            "                        except SyntaxError: return False",
            "                        cs = frozenset(str(c) for c in cols)",
            "                        for nd in _ast_cb.walk(tree):",
            "                            if type(nd) not in _ALLOW_CB: return False",
            "                            if isinstance(nd, _ast_cb.Name) and nd.id not in cs and nd.id not in _SNAMES_CB: return False",
            "                        return True",
            "                    _px_cb = _if_cb.replace('~=', '!=')",
            "                    if _safe_g_cb(_px_cb, _gdf.columns):",
            "                        try: _gdf = _gdf.query(_px_cb, engine='python')",
            "                        except Exception: pass",
            "                for src in (srcs if isinstance(srcs, list) else [srcs]):",
            "                    new_data = {}",
            "                    # Row indices of filtered rows in _df_ref.",
            "                    # _df_ref always has a RangeIndex so these are valid",
            "                    # positional offsets into original source arrays.",
            "                    _src_idx = _gdf.index.tolist()",
            "                    # Original (pre-filter) snapshot for this source, used to",
            "                    # restore derived columns (_x_jit etc.) by row index.",
            "                    _snap = _orig_src_data.get(id(src), {})",
            "                    for col in src.data:",
            "                        if col in _gdf.columns:",
            "                            new_data[col] = _gdf[col].tolist()",
            "                        elif col == 'index':",
            "                            new_data[col] = _src_idx",
            "                        else:",
            "                            # Derived column: select from original snapshot by row index.",
            "                            # Preserves _x_jit/_y_jit and other columns not in _df_ref.",
            "                            _orig_col = _snap.get(col, [])",
            "                            n_orig = len(_orig_col)",
            "                            new_data[col] = [_orig_col[i] for i in _src_idx if 0 <= i < n_orig]",
            "                    src.data = new_data",
            "            # 3. Recompute aggregated sources",
            "            for key, agg in _agg_srcs.items():",
            "                gname = key[0]",
            "                if gname in excl:",
            "                    continue",
            "                # Derive per-facet data frame analogously to raw source update.",
            "                # Faceted aggregates must recompute from the facet's subgroup,",
            "                # not from global fdf, to stay in sync after filter changes.",
            "                if gname in _fgvals:",
            "                    _bvs_a, _gkey_a = _fgvals[gname]",
            "                    if _gkey_a is None:",
            "                        agg_fdf = fdf",
            "                    else:",
            "                        _fmask_a = mask.copy()",
            "                        if len(_bvs_a) == 1:",
            "                            _fmask_a = mask & (_df_ref[_bvs_a[0]] == _gkey_a)",
            "                        else:",
            "                            for _bv_a, _gv_a in zip(_bvs_a, _gkey_a):",
            "                                _fmask_a = _fmask_a & (_df_ref[_bv_a] == _gv_a)",
            "                        agg_fdf = _df_ref[_fmask_a]",
            "                else:",
            "                    agg_fdf = fdf",
            "                atype = agg['type']",
            "                if atype == 'histogram':",
            "                    agg['source'].data = _compute_histogram(agg_fdf, agg['var'], agg.get('bins', 20))",
            "                elif atype == 'lfit':",
            "                    agg['source'].data = _compute_lfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'qfit':",
            "                    agg['source'].data = _compute_qfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'kdensity':",
            "                    agg['source'].data = _compute_kdensity(agg_fdf, agg['var'])",
            "                elif atype == 'lowess':",
            "                    agg['source'].data = _compute_lowess(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'lpoly':",
            "                    agg['source'].data = _compute_lpoly(agg_fdf, agg['yvar'], agg['xvar'],",
            "                                                        bwidth=agg.get('bwidth', 0.5),",
            "                                                        degree=agg.get('degree', 0))",
            "                elif atype == 'fpfit':",
            "                    agg['source'].data = _compute_fpfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'lfitci':",
            "                    agg['source'].data = _compute_lfitci(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'qfitci':",
            "                    agg['source'].data = _compute_qfitci(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'mspline':",
            "                    agg['source'].data = _compute_mspline(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'mband':",
            "                    agg['source'].data = _compute_mband(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'rscatter':",
            "                    agg['source'].data = _compute_rscatter(agg_fdf, agg['yvar1'], agg['yvar2'], agg['xvar'])",
            "                elif atype == 'pcscatter':",
            "                    agg['source'].data = _compute_pcscatter(agg_fdf, agg['y1var'], agg['x1var'], agg['y2var'], agg['x2var'])",
            "            # 4. Recompute filter-mode KPIs",
            "            for kpi in _kpi_defs:",
            "                kupdate = kpi.get('update', 'filter')",
            "                if kupdate not in ('filter', 'both'):",
            "                    continue",
            "                kname = kpi.get('name', '')",
            "                if kname not in _kpi_divs:",
            "                    continue",
            "                if kname in excl:",
            "                    continue",
            "                val = _compute_kpi(fdf, kpi.get('stat', 'mean'), kpi.get('var', ''))",
            "                disp = _format_kpi(val, kpi.get('fmt', ''))",
            "                ktitle = html.escape(kpi.get('title', '') or '')",
            "                ksub = html.escape(kpi.get('subtitle', '') or '')",
            "                kcolor = kpi.get('color', '#333333') or '#333333'",
            "                kbg = kpi.get('bgcolor', '#f8f9fa') or '#f8f9fa'",
            "                _kpi_divs[kname].text = (",
            "                    f'<div style=\"background:{html.escape(kbg)};border-radius:8px;'",
            "                    f'padding:16px;text-align:center;font-family:sans-serif;\">'",
            "                    f'<div style=\"font-size:13px;color:#888;margin-bottom:4px;\">{ktitle}</div>'",
            "                    f'<div style=\"font-size:28px;font-weight:bold;color:{html.escape(kcolor)};\">{html.escape(disp)}</div>'",
            "                    f'<div style=\"font-size:11px;color:#aaa;margin-top:4px;\">{ksub}</div>'",
            "                    f'</div>'",
            "                )",
            "        return _on_filter_change",
            "",
            "    for w in filter_widgets:",
            "        _cb_for_w = _make_filter_cb(",
            "            w, filter_widgets, graph_sources, agg_sources, kpi_divs, kpi_defs, df,",
            "            _facet_map, _facet_group_vals, _orig_src_data,",
            "            _graph_qualifiers, _facet_to_orig",
            "        )",
            "        if isinstance(w, Select):",
            "            w.on_change('value', _cb_for_w)",
            "        elif isinstance(w, (Slider, RangeSlider)):",
            "            w.on_change('value', _cb_for_w)",
            "",
            "    # ---- Wire brush selection callbacks ----",
            "    def _make_brush_cb(_kpi_divs, _kpi_defs, _df_ref, _src):",
            "        def _on_selection_change(attr, old, new):",
            "            indices = new",
            "            sel_df = _df_ref.iloc[indices] if indices else _df_ref",
            "            for kpi in _kpi_defs:",
            "                kupdate = kpi.get('update', 'filter')",
            "                if kupdate not in ('brush', 'both'):",
            "                    continue",
            "                kname = kpi.get('name', '')",
            "                if kname not in _kpi_divs:",
            "                    continue",
            "                val = _compute_kpi(sel_df, kpi.get('stat', 'mean'), kpi.get('var', ''))",
            "                disp = _format_kpi(val, kpi.get('fmt', ''))",
            "                ktitle = html.escape(kpi.get('title', '') or '')",
            "                ksub = html.escape(kpi.get('subtitle', '') or '')",
            "                kcolor = kpi.get('color', '#333333') or '#333333'",
            "                kbg = kpi.get('bgcolor', '#f8f9fa') or '#f8f9fa'",
            "                _kpi_divs[kname].text = (",
            "                    f'<div style=\"background:{html.escape(kbg)};border-radius:8px;'",
            "                    f'padding:16px;text-align:center;font-family:sans-serif;\">'",
            "                    f'<div style=\"font-size:13px;color:#888;margin-bottom:4px;\">{ktitle}</div>'",
            "                    f'<div style=\"font-size:28px;font-weight:bold;color:{html.escape(kcolor)};\">{html.escape(disp)}</div>'",
            "                    f'<div style=\"font-size:11px;color:#aaa;margin-top:4px;\">{ksub}</div>'",
            "                    f'</div>'",
            "                )",
            "        return _on_selection_change",
            "",
            "    shared_source.selected.on_change('indices', _make_brush_cb(",
            "        kpi_divs, kpi_defs, df, shared_source",
            "    ))",
            "",
            "    # ---- Assemble grid layout ----",
            "    registry = bo.get('registry', '') or ''",
            "    all_names = registry.split() if registry else (",
            "        [g.get('graph_options', {}).get('name', '') for g in graphs]",
            "        + [k.get('name', '') for k in kpi_defs]",
            "    )",
            "",
            "    n = len(all_names)",
            "    if n == 0:",
            "        cols_n = 1",
            "    elif n <= 2:",
            "        cols_n = n",
            "    else:",
            "        cols_n = math.ceil(math.sqrt(n))",
            "    rows_n = math.ceil(n / cols_n) if cols_n > 0 else 1",
            "",
            "    cells = []",
            "    for name in all_names:",
            "        if name in _facet_map:",
            "            # Build a sub-grid of facet figures",
            "            _fac_figs = [figures[fk] for fk, _ in _facet_map[name] if fk in figures]",
            "            if _fac_figs:",
            "                _go = {}",
            "                for _gx in graphs:",
            "                    if _gx.get('graph_options', {}).get('name') == name:",
            "                        _go = _gx.get('graph_options', {})",
            "                        break",
            "                _by_cols_raw = _go.get('by_cols', '0')",
            "                try: _by_cn = int(_by_cols_raw) if _by_cols_raw else 0",
            "                except (ValueError, TypeError): _by_cn = 0",
            "                if _by_cn <= 0: _by_cn = min(len(_fac_figs), max(1, math.ceil(math.sqrt(len(_fac_figs)))))",
            "                _sub_rows = [_fac_figs[_si:_si+_by_cn] for _si in range(0, len(_fac_figs), _by_cn)]",
            "                while len(_sub_rows[-1]) < _by_cn: _sub_rows[-1].append(None)",
            "                cells.append(gridplot(_sub_rows, sizing_mode='stretch_width'))",
            "            else:",
            "                cells.append(None)",
            "        elif name in figures:",
            "            cells.append(figures[name])",
            "        elif name in kpi_divs:",
            "            cells.append(kpi_divs[name])",
            "    while len(cells) < rows_n * cols_n:",
            "        cells.append(None)",
            "",
            "    grid_rows = [cells[i * cols_n:(i + 1) * cols_n] for i in range(rows_n)]",
            "    grid = gridplot(grid_rows, sizing_mode='stretch_width')",
            "",
            "    if filter_widgets:",
            "        filter_bar = row(filter_widgets, sizing_mode='stretch_width')",
            "        layout = column(filter_bar, grid, sizing_mode='stretch_width')",
            "    else:",
            "        layout = grid",
            "",
            "    if title_text:",
            "        title_div = Div(",
            "            text=f'<h2 style=\"font-family:sans-serif;\">{title_text}</h2>',",
            "            sizing_mode='stretch_width',",
            "        )",
            "        layout = column(title_div, layout, sizing_mode='stretch_width')",
            "",
            "    doc.add_root(layout)",
            "    doc.title = title_text or 'dash'",
            "",
            "",
        ]

        # ----------------------------------------------------------------
        # 5. __main__ block
        # ----------------------------------------------------------------
        lines += [
            f"if __name__ == '__main__':",
            f"    _port = {port}",
            f"    _server = Server(",
            f"        {{'/': Application(FunctionHandler(make_document))}},",
            f"        port=_port,",
            f"        allow_websocket_origin=[f'localhost:{{_port}}'],",
            f"        num_procs=1,",
            f"        extra_patterns=[('/health', _HealthHandler)],",
            f"    )",
            f"    _server.start()",
            f"    _server.io_loop.add_callback(_server.show, '/')",
            f"    print(f'Bokeh Server running at http://localhost:{{_port}}/')",
            f"    print(f'Health check:  http://localhost:{{_port}}/health')",
            f"    print('Press Ctrl+C to stop.')",
            f"    try:",
            f"        _server.io_loop.start()",
            f"    except KeyboardInterrupt:",
            f"        pass",
            f"    finally:",
            f"        _server.stop()",
            f"        print('Server stopped.')",
        ]

        return "\n".join(lines) + "\n"


# ===========================================================================
# Updated CLI entry point — uses argparse for --spec/--data/--output/--mode
# ===========================================================================

def main(
    master_spec_path: str,
    data_json_path: str,
    output_path: str,
    mode: str = "standalone",
) -> None:
    """Build the dashboard and write it to *output_path*.

    Dispatches to ``DashRenderer`` (standalone HTML) or ``ServerAppBuilder``
    (Bokeh Server app ``.py``) depending on *mode*.

    Args:
        master_spec_path: Path to the master specification JSON.
        data_json_path:   Path to the jsonio data JSON.
        output_path:      Destination path for the output file.
        mode:             ``'standalone'`` (default) or ``'server'``.

    Raises:
        ValueError: If *mode* is not a recognised value.
    """
    if mode == "server":
        builder = ServerAppBuilder(master_spec_path, data_json_path)
        builder.build(output_path)
    elif mode == "standalone":
        renderer = DashRenderer(master_spec_path, data_json_path)
        html_content = renderer.render()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    else:
        raise ValueError(f"dash_render: unknown mode '{mode}'. Expected 'standalone' or 'server'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="dash_render.py — Bokeh dashboard renderer for the Stata dash command"
    )
    parser.add_argument("--spec",   required=True, help="Path to master spec JSON")
    parser.add_argument("--data",   required=True, help="Path to jsonio data JSON")
    parser.add_argument("--output", required=True, help="Path for output file (.html or .py)")
    parser.add_argument(
        "--mode",
        default="standalone",
        choices=["standalone", "server"],
        help="Output mode: 'standalone' (HTML) or 'server' (Bokeh Server app .py)",
    )
    # Server-launch options (used with --mode server)
    parser.add_argument(
        "--port",
        type=int,
        default=5006,
        help="TCP port for the Bokeh Server (default: 5006). Only used with --mode server.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help=(
            "Auto-shutdown timeout in minutes (0 = run until interrupted). "
            "Only used with --mode server."
        ),
    )
    parser.add_argument(
        "--no-browser",
        dest="no_browser",
        action="store_true",
        default=False,
        help="Do not open a browser tab after starting the Bokeh Server.",
    )
    args = parser.parse_args()

    # Build the output file (HTML or server app .py)
    main(args.spec, args.data, args.output, args.mode)

    # When mode is 'server', launch the generated Bokeh Server app.
    # This call blocks until the server is stopped (SIGINT / timeout).
    if args.mode == "server":
        import subprocess as _sp
        import sys as _sys
        import time as _time
        import threading as _threading
        import webbrowser as _wb

        _port = max(1024, min(args.port, 65535))
        _cmd = [
            _sys.executable, "-m", "bokeh", "serve",
            args.output,
            "--port", str(_port),
            "--allow-websocket-origin", f"localhost:{_port}",
        ]
        try:
            _proc = _sp.Popen(_cmd)
        except FileNotFoundError:
            import sys as _sys2
            print(
                "dash_render: error — could not launch 'bokeh serve'. "
                "Ensure Bokeh is installed and accessible in the current Python environment.",
                file=_sys2.stderr,
            )
            raise SystemExit(1)

        # Open browser after a short delay unless suppressed
        if not args.no_browser:
            def _open_browser():
                _time.sleep(1.5)
                _wb.open(f"http://localhost:{_port}")
            _bt = _threading.Thread(target=_open_browser, daemon=True)
            _bt.start()

        # Auto-shutdown after timeout minutes (0 = run until interrupted)
        if args.timeout > 0:
            def _auto_stop():
                _time.sleep(args.timeout * 60)
                _proc.terminate()
            _tt = _threading.Thread(target=_auto_stop, daemon=True)
            _tt.start()

        try:
            _proc.wait()
        except KeyboardInterrupt:
            _proc.terminate()
            _proc.wait()
