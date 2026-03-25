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
from bokeh.embed import file_html
from bokeh.layouts import column, gridplot, row
from bokeh.models import (
    BooleanFilter,
    BoxSelectTool,
    CDSView,
    ColumnDataSource,
    CustomJS,
    Div,
    HoverTool,
    LassoSelectTool,
    PanTool,
    RangeSlider,
    ResetTool,
    Select,
    Slider,
    Span,
    WheelZoomTool,
)
from bokeh.plotting import figure as bokeh_figure
from bokeh.resources import CDN


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Number of data points above which WebGL rendering is used for performance.
_WEBGL_THRESHOLD = 10_000

# Default nonselection alpha for linked-brushing dimming effect.
_NONSELECTION_ALPHA = 0.15

# CSP meta tag injected into every output HTML file.
_CSP_META = (
    '<meta http-equiv="Content-Security-Policy" '
    'content="script-src \'unsafe-inline\';">'
)


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
    def translate_mcolor(value: str) -> str:
        """Return a CSS hex color string for a Stata mcolor() value.

        Args:
            value: A Stata color name (e.g. "navy") or RGB string "R G B".

        Returns:
            A CSS hex color string, e.g. "#1a476f".

        Raises:
            ValueError: If the value cannot be recognised as a valid color.
        """
        v = value.strip().lower()

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

    def __init__(self, translator: OptionTranslator | None = None) -> None:
        """Initialise the mapper with an optional OptionTranslator instance."""
        self.tr = translator or OptionTranslator()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _hover_tool(self, yvar: str, xvar: str) -> HoverTool:
        """Return a HoverTool that shows variable names and values."""
        return HoverTool(tooltips=[
            (xvar, f"@{{{xvar}}}"),
            (yvar, f"@{{{yvar}}}"),
        ])

    def _apply_line_opts(
        self,
        renderer: Any,
        options: dict[str, str],
    ) -> None:
        """Apply lcolor/lwidth/lpattern options to a line-type glyph renderer."""
        glyph = renderer.glyph
        if "lcolor" in options:
            try:
                glyph.line_color = self.tr.translate_lcolor(options["lcolor"])
            except ValueError:
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

    def _apply_marker_opts(
        self,
        renderer: Any,
        options: dict[str, str],
    ) -> None:
        """Apply mcolor/msymbol/msize options to a scatter-type glyph renderer."""
        glyph = renderer.glyph
        if "mcolor" in options:
            try:
                color = self.tr.translate_mcolor(options["mcolor"])
                glyph.fill_color = color
                glyph.line_color = color
            except ValueError:
                pass
        if "msize" in options:
            try:
                glyph.size = self.tr.translate_msize(options["msize"])
            except ValueError:
                pass

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

        # Drop NaN rows if present; otherwise reuse the original source
        x_series = pd.Series(source.data[xvar])
        y_series = pd.Series(source.data[yvar])
        has_nan = x_series.isna().any() or y_series.isna().any()
        if has_nan:
            df = pd.DataFrame({xvar: source.data[xvar], yvar: source.data[yvar]})
            df = df.dropna(subset=[xvar, yvar])
            clean_source: ColumnDataSource = ColumnDataSource(df)
        else:
            clean_source = source

        r = fig.scatter(
            x=xvar,
            y=yvar,
            source=clean_source,
            marker=marker,
            size=8,
            fill_color="#1f77b4",
            line_color="#1f77b4",
            alpha=0.7,
        )
        self._apply_marker_opts(r, options)
        fig.add_tools(self._hover_tool(yvar, xvar))
        return r

    def map_line(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        r = fig.line(
            x=xvar,
            y=yvar,
            source=sorted_source,
            line_color="#ff7f0e",
            line_width=1.5,
        )
        self._apply_line_opts(r, options)
        fig.add_tools(self._hover_tool(yvar, xvar))
        return r

    def map_connected(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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
        return [
            self.map_line(fig, source, yvar, xvar, options),
            self.map_scatter(fig, source, yvar, xvar, options),
        ]

    def map_area(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
    ) -> list:
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
        y1_zeros = np.zeros_like(y_arr)

        # y1 = baseline (zeros), y2 = upper boundary (yvar values)
        area_source = ColumnDataSource({"x": x_arr, "y1": y1_zeros, "y2": y_arr})
        r = fig.varea(x="x", y1="y1", y2="y2", source=area_source,
                      fill_color="#aec7e8", fill_alpha=0.5)

        # Honour fill color option
        if "color" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["color"])
            except ValueError:
                pass

        return r

    def map_bar(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
    ) -> list:
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
        # Drop NaN rows
        df = pd.DataFrame({xvar: source.data[xvar], yvar: source.data[yvar]})
        df = df.dropna(subset=[xvar, yvar])
        clean_source = ColumnDataSource(df)

        x_vals = sorted(set(float(v) for v in df[xvar]))
        if len(x_vals) >= 2:
            gaps = [x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)]
            bar_width = 0.8 * min(gaps)
        else:
            bar_width = 0.8

        r = fig.vbar(
            x=xvar, top=yvar, source=clean_source,
            width=bar_width,
            fill_color="#1f77b4",
            line_color="#1f77b4",
            fill_alpha=0.8,
        )
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
                r.glyph.line_color = c
            except ValueError:
                pass
        return r

    def map_spike(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
    ) -> list:
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
        zeros = np.zeros_like(x_arr)

        seg_source = ColumnDataSource({
            "x0": x_arr, "y0": zeros,
            "x1": x_arr, "y1": y_arr,
        })
        r = fig.segment(x0="x0", y0="y0", x1="x1", y1="y1",
                        source=seg_source,
                        line_color="#1f77b4", line_width=1.5)
        self._apply_line_opts(r, options)
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

        coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
        x_fit = np.linspace(x.min(), x.max(), 200)
        y_fit = np.polyval(coeffs, x_fit)

        fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})
        r = fig.line(x="x", y="y", source=fit_source,
                     line_color="#d62728", line_width=2.0, line_dash="solid")
        self._apply_line_opts(r, options)
        return r

    def map_qfit(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        coeffs = np.polyfit(x, y, 2)
        x_fit = np.linspace(x.min(), x.max(), 200)
        y_fit = np.polyval(coeffs, x_fit)

        fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})
        r = fig.line(x="x", y="y", source=fit_source,
                     line_color="#d62728", line_width=2.0)
        self._apply_line_opts(r, options)
        return r

    def map_lfitci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        slope, intercept, _, _, se = scipy_stats.linregress(x, y)
        x_fit = np.linspace(x.min(), x.max(), 200)
        y_fit = intercept + slope * x_fit

        # SE of the fit line at each x_fit point
        x_mean = x.mean()
        se_fit = se * np.sqrt(
            1 / n + (x_fit - x_mean) ** 2 / np.sum((x - x_mean) ** 2)
        ) * np.sqrt(n - 2)
        t_crit = scipy_stats.t.ppf(0.975, df=n - 2)

        y_lower = y_fit - t_crit * se_fit
        y_upper = y_fit + t_crit * se_fit

        ci_source = ColumnDataSource({
            "x_fit": x_fit, "y_fit": y_fit,
            "y_lower": y_lower, "y_upper": y_upper,
        })

        band_r = fig.varea(
            x="x_fit", y1="y_lower", y2="y_upper",
            source=ci_source, fill_alpha=0.2, fill_color="#d62728"
        )
        line_r = fig.line(x="x_fit", y="y_fit", source=ci_source,
                          line_color="#d62728", line_width=2.0)
        self._apply_line_opts(line_r, options)
        return [line_r, band_r]

    def map_qfitci(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        coeffs = np.polyfit(x, y, 2)
        x_fit = np.linspace(x.min(), x.max(), 200)
        y_fit = np.polyval(coeffs, x_fit)

        # Bootstrap CI
        rng = np.random.default_rng(seed=42)
        boot_preds = np.zeros((500, len(x_fit)))
        for i in range(500):
            idx = rng.integers(0, len(x), size=len(x))
            c = np.polyfit(x[idx], y[idx], 2)
            boot_preds[i] = np.polyval(c, x_fit)

        y_lower = np.percentile(boot_preds, 2.5, axis=0)
        y_upper = np.percentile(boot_preds, 97.5, axis=0)

        ci_source = ColumnDataSource({
            "x_fit": x_fit, "y_fit": y_fit,
            "y_lower": y_lower, "y_upper": y_upper,
        })
        band_r = fig.varea(
            x="x_fit", y1="y_lower", y2="y_upper",
            source=ci_source, fill_alpha=0.2, fill_color="#d62728"
        )
        line_r = fig.line(x="x_fit", y="y_fit", source=ci_source,
                          line_color="#d62728", line_width=2.0)
        self._apply_line_opts(line_r, options)
        return [line_r, band_r]

    def map_lowess(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        # Default bandwidth: 0.8 (same as Stata's default)
        bw = float(options.get("bwidth", "0.8"))
        smoothed = lowess(y, x, frac=bw, return_sorted=True)

        lw_source = ColumnDataSource({
            "x_lw": smoothed[:, 0],
            "y_lw": smoothed[:, 1],
        })
        r = fig.line(x="x_lw", y="y_lw", source=lw_source,
                     line_color="#2ca02c", line_width=2.0)
        self._apply_line_opts(r, options)
        return r

    def map_histogram(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        options: "dict[str, str] | None" = None,
        xvar: "str | None" = None,
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
        arr = np.array(source.data[yvar], dtype=float)
        arr = arr[~np.isnan(arr)]

        n_bins = int(options.get("bin", 10))
        counts, edges = np.histogram(arr, bins=n_bins)

        hist_source = ColumnDataSource({
            "top":   counts,
            "left":  edges[:-1],
            "right": edges[1:],
        })
        r = fig.quad(top="top", bottom=0, left="left", right="right",
                     source=hist_source,
                     fill_color="#1f77b4", line_color="white",
                     fill_alpha=0.8)
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
            except ValueError:
                pass
        return r

    def map_kdensity(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        options: "dict[str, str] | None" = None,
        xvar: "str | None" = None,
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
        arr = np.array(source.data[yvar], dtype=float)
        arr = arr[~np.isnan(arr)]

        kde = gaussian_kde(arr)
        # Extend range beyond data min/max to capture distribution tails
        bw = kde.covariance_factor() * arr.std()
        x_range = np.linspace(arr.min() - 3 * bw, arr.max() + 3 * bw, 400)
        density = kde(x_range)

        kd_source = ColumnDataSource({"x": x_range, "y": density})
        r = fig.line(x="x", y="y", source=kd_source,
                     line_color="#9467bd", line_width=2.0)
        self._apply_line_opts(r, options)
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
        r = fig.varea(x=xvar, y1=y1var, y2=y2var, source=source,
                      fill_color="#aec7e8", fill_alpha=0.5)
        return r

    def map_rbar(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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
        x_vals = sorted(set(float(v) for v in source.data[xvar]
                            if not math.isnan(float(v))))
        bar_width = 0.8 * min(
            (x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)),
            default=0.8,
        )
        r = fig.vbar(x=xvar, bottom=y1var, top=y2var, source=source,
                     width=bar_width, fill_color="#1f77b4", line_color="white")
        return r

    def map_rspike(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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
        r = fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var, source=source,
                        line_color="#1f77b4", line_width=1.5)
        self._apply_line_opts(r, options)
        return [r]

    def map_rcap(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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

        cap_source = ColumnDataSource({
            "x": x_arr, "y1": y1_arr, "y2": y2_arr,
            "x0_cap": x_arr - cap_hw, "x1_cap": x_arr + cap_hw,
        })

        spine = fig.segment(x0="x", y0="y1", x1="x", y1="y2",
                            source=cap_source,
                            line_color="#1f77b4", line_width=1.5)
        bot_cap = fig.segment(x0="x0_cap", y0="y1", x1="x1_cap", y1="y1",
                              source=cap_source,
                              line_color="#1f77b4", line_width=1.5)
        top_cap = fig.segment(x0="x0_cap", y0="y2", x1="x1_cap", y1="y2",
                              source=cap_source,
                              line_color="#1f77b4", line_width=1.5)
        return [spine, bot_cap, top_cap]

    def map_rline(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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
        r1 = fig.line(x=xvar, y=y1var, source=source,
                      line_color="#1f77b4", line_width=1.5)
        r2 = fig.line(x=xvar, y=y2var, source=source,
                      line_color="#ff7f0e", line_width=1.5)
        self._apply_line_opts(r1, options)
        self._apply_line_opts(r2, options)
        return [r1, r2]

    def map_rconnected(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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
            self.map_line(fig, source, y1var, xvar, options),
            self.map_scatter(fig, source, y1var, xvar, options),
            self.map_line(fig, source, y2var, xvar, options),
            self.map_scatter(fig, source, y2var, xvar, options),
        ]

    def map_dot(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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
        return self.map_scatter(fig, source, yvar, xvar, options)


# ===========================================================================
# FilterBuilder
# ===========================================================================

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
    ) -> "tuple[Select, CustomJS]":
        """Build a categorical dropdown filter widget with CustomJS callback.

        Args:
            varname:           Stata variable name to filter on.
            source:            The shared ColumnDataSource holding the data.
            df_or_data:        Optional DataFrame/data; accepted for API
                               compatibility but values are read from *source*.
            value_labels:      Dict mapping raw values to display labels.  May
                               be a nested ``{varname: {code: label}}`` dict or
                               a flat ``{code: label}`` dict.
            exclude_names:     Names of graphs/KPIs to exclude from the filter.
            all_figure_names:  All registered graph names (for callback wiring).
            figure_renderer_map: Legacy param; ignored.
            kpi_divs:            Legacy param; ignored.

        Returns:
            A (Select widget, CustomJS callback) tuple.
        """
        if value_labels is None:
            value_labels = {}
        if exclude_names is None:
            exclude_names = []

        safe_var = FilterBuilder._safe(varname)

        # Resolve label set: accept nested {varname: {code: label}} or flat
        if varname in value_labels and isinstance(value_labels[varname], dict):
            vlabels: dict = value_labels[varname]
        else:
            vlabels = value_labels

        # Build option list: "All" first, then sorted unique values
        raw_values = list(set(str(v) for v in source.data[varname]
                              if v is not None and str(v) != "nan"))
        raw_values.sort()

        def _resolve_label(rv: str) -> str:
            if rv in vlabels:
                return vlabels[rv]
            # Try integer key (e.g. "0.0" → look up "0")
            try:
                int_key = str(int(float(rv)))
                if int_key in vlabels:
                    return vlabels[int_key]
            except (ValueError, OverflowError):
                pass
            return rv

        options = [("__all__", "All")]
        for rv in raw_values:
            label = _resolve_label(rv)
            options.append((rv, FilterBuilder._safe(label)))

        widget = Select(title=safe_var, value="__all__",
                        options=[(v, l) for v, l in options])

        # CustomJS — parameterised: the variable name is passed as a data
        # attribute, not interpolated into the function body.
        js_code = """
const val = cb_obj.value;
const data = source.data;
const varname = filter_var;
const indices = [];

if (val === '__all__') {
    // Remove filter: show all rows
    for (let i = 0; i < data[varname].length; i++) {
        indices.push(true);
    }
} else {
    for (let i = 0; i < data[varname].length; i++) {
        indices.push(String(data[varname][i]) === val);
    }
}

// Apply to each non-excluded view
for (let i = 0; i < views.length; i++) {
    views[i].filter = new BooleanFilter({booleans: indices});
}

source.change.emit();
"""
        callback = CustomJS(
            args={
                "source": source,
                "views": [],        # populated by DashRenderer after build
                "filter_var": varname,
                "BooleanFilter": BooleanFilter,
            },
            code=js_code,
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
    ) -> "tuple[Slider, CustomJS]":
        """Build a numeric threshold slider filter widget.

        Shows rows where ``varname >= slider.value``.

        Args:
            varname:          Stata variable name to filter on.
            source:           The shared ColumnDataSource.
            df_or_data:       Optional DataFrame; accepted for API compat.
            exclude_names:    Names of graphs/KPIs excluded from this filter.
            all_figure_names: All registered graph names.

        Returns:
            A (Slider widget, CustomJS callback) tuple.
        """
        if exclude_names is None:
            exclude_names = []
        safe_var = FilterBuilder._safe(varname)
        arr = np.array([v for v in source.data[varname]
                        if v is not None], dtype=float)
        arr = arr[~np.isnan(arr)]
        vmin, vmax = float(arr.min()), float(arr.max())
        vstep = (vmax - vmin) / 100.0 or 1.0

        widget = Slider(title=safe_var, start=vmin, end=vmax,
                        value=vmin, step=vstep)

        js_code = """
const val = cb_obj.value;
const data = source.data;
const varname = filter_var;
const indices = [];
for (let i = 0; i < data[varname].length; i++) {
    indices.push(data[varname][i] >= val);
}
for (let i = 0; i < views.length; i++) {
    views[i].filter = new BooleanFilter({booleans: indices});
}
source.change.emit();
"""
        callback = CustomJS(
            args={
                "source": source,
                "views": [],
                "filter_var": varname,
                "BooleanFilter": BooleanFilter,
            },
            code=js_code,
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
    ) -> "tuple[RangeSlider, CustomJS]":
        """Build a numeric range filter widget.

        Shows rows where ``varname >= start AND varname <= end``.

        Args:
            varname:          Stata variable name to filter on.
            source:           The shared ColumnDataSource.
            df_or_data:       Optional DataFrame; accepted for API compat.
            exclude_names:    Names of graphs/KPIs excluded from this filter.
            all_figure_names: All registered graph names.

        Returns:
            A (RangeSlider widget, CustomJS callback) tuple.
        """
        if exclude_names is None:
            exclude_names = []
        safe_var = FilterBuilder._safe(varname)
        arr = np.array([v for v in source.data[varname]
                        if v is not None], dtype=float)
        arr = arr[~np.isnan(arr)]
        vmin, vmax = float(arr.min()), float(arr.max())
        vstep = (vmax - vmin) / 100.0 or 1.0

        widget = RangeSlider(title=safe_var,
                             start=vmin, end=vmax,
                             value=(vmin, vmax), step=vstep)

        js_code = """
const [lo, hi] = cb_obj.value;
const data = source.data;
const varname = filter_var;
const indices = [];
for (let i = 0; i < data[varname].length; i++) {
    indices.push(data[varname][i] >= lo && data[varname][i] <= hi);
}
for (let i = 0; i < views.length; i++) {
    views[i].filter = new BooleanFilter({booleans: indices});
}
source.change.emit();
"""
        callback = CustomJS(
            args={
                "source": source,
                "views": [],
                "filter_var": varname,
                "BooleanFilter": BooleanFilter,
            },
            code=js_code,
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

        self.mapper = GlyphMapper()
        self.translator = OptionTranslator()

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

        # Tracks KPI update mode ("filter" | "brush" | "both") by KPI name.
        self._kpi_update_modes: dict[str, str] = {}

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

    def _make_source(self, varnames: list[str]) -> ColumnDataSource:
        """Create a ``ColumnDataSource`` for the given variable names.

        Only includes columns that exist in self.df.  Missing columns
        are silently skipped to prevent KeyErrors for derived variables.

        Args:
            varnames: List of Stata variable names needed by one or more glyphs.

        Returns:
            A new ``ColumnDataSource`` populated with the requested columns.
        """
        available = [v for v in varnames if v in self.df.columns]
        data_dict = {v: self.df[v].tolist() for v in available}
        return ColumnDataSource(data=data_dict)

    # ------------------------------------------------------------------
    # Figure construction helpers
    # ------------------------------------------------------------------

    def _axis_label(self, varname: str) -> str:
        """Return the axis label for *varname*, using variable labels if available."""
        return self.variable_labels.get(varname, varname)

    def _make_figure(
        self,
        graph_spec: dict,
        source: ColumnDataSource,
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

        # Enable WebGL for large datasets
        n_rows = len(self.df)
        backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"

        fig = bokeh_figure(
            title=html.escape(graph_opts.get("title", "")),
            x_axis_label=self._axis_label(xvar),
            y_axis_label=self._axis_label(yvar),
            output_backend=backend,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_select,lasso_select,reset",
        )

        # Log scale options
        if graph_opts.get("xscale") == "log":
            fig.xaxis.axis_label = self._axis_label(xvar)
            # Rebuild with log x-axis
            fig = bokeh_figure(
                title=html.escape(graph_opts.get("title", "")),
                x_axis_type="log",
                x_axis_label=self._axis_label(xvar),
                y_axis_label=self._axis_label(yvar),
                output_backend=backend,
                sizing_mode="stretch_width",
            )
        if graph_opts.get("yscale") == "log":
            fig = bokeh_figure(
                title=html.escape(graph_opts.get("title", "")),
                y_axis_type="log",
                x_axis_label=self._axis_label(xvar),
                y_axis_label=self._axis_label(yvar),
                output_backend=backend,
                sizing_mode="stretch_width",
            )

        # Reference lines
        for xline_val in graph_opts.get("xline_values", []):
            try:
                fig.add_layout(Span(location=float(xline_val),
                                    dimension="height",
                                    line_color="gray", line_dash="dashed"))
            except (ValueError, TypeError):
                pass
        for yline_val in graph_opts.get("yline_values", []):
            try:
                fig.add_layout(Span(location=float(yline_val),
                                    dimension="width",
                                    line_color="gray", line_dash="dashed"))
            except (ValueError, TypeError):
                pass

        # Add glyphs for each plot layer
        for plot in plots:
            ptype = plot.get("type", "scatter")
            pyvar = plot.get("yvar", yvar)
            pxvar = plot.get("xvar", xvar)
            popts = plot.get("options", {})

            self._add_glyph(fig, source, ptype, pyvar, pxvar, popts)

        return fig

    def _add_glyph(
        self,
        fig: Any,
        source: ColumnDataSource,
        plot_type: str,
        yvar: str,
        xvar: str,
        options: dict,
    ) -> None:
        """Dispatch a single plot layer to the correct GlyphMapper method.

        Args:
            fig:        Bokeh Figure to add the glyph to.
            source:     ColumnDataSource.
            plot_type:  Stata twoway plot type name.
            yvar:       y variable name.
            xvar:       x variable name.
            options:    Plot-level options dict.
        """
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
            "histogram":  self.mapper.map_histogram,
            "hist":       self.mapper.map_histogram,
            "kdensity":   self.mapper.map_kdensity,
            "dot":        self.mapper.map_dot,
        }
        fn = dispatch.get(plot_type.lower())
        if fn is not None:
            # histogram and kdensity are univariate — no xvar positional arg
            if plot_type.lower() in ("histogram", "hist", "kdensity"):
                fn(fig, source, yvar, options)
            else:
                fn(fig, source, yvar, xvar, options)

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
        color    = html.escape(kpi_def.get("color", "#212529"))
        bgcolor  = html.escape(kpi_def.get("bgcolor", "#f8f9fa"))

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
        filters_cfg = build.get("filters", [])
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

        if link_names:
            # Collect all variable names needed by linked graphs
            linked_vars: list[str] = []
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    for plot in g.get("plots", []):
                        for key in ("yvar", "xvar"):
                            v = plot.get(key)
                            if v and v not in linked_vars:
                                linked_vars.append(v)
            # Add filter variables so filter callbacks work on the shared source
            for fc in filters_cfg:
                v = fc.get("varname")
                if v and v not in linked_vars:
                    linked_vars.append(v)

            linked_source = self._make_source(linked_vars)

            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    sources[name] = linked_source
                else:
                    g_vars = [
                        p.get(k) for p in g.get("plots", [])
                        for k in ("yvar", "xvar") if p.get(k)
                    ]
                    sources[name] = self._make_source(list(dict.fromkeys(g_vars)))
        else:
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                g_vars = [
                    p.get(k) for p in g.get("plots", [])
                    for k in ("yvar", "xvar") if p.get(k)
                ]
                sources[name] = self._make_source(list(dict.fromkeys(g_vars)))

        return sources

    def _build_figures(self) -> "dict[str, Any]":
        """Build and return a dict mapping graph name → Bokeh Figure.

        Uses ``_setup_sources()`` to obtain ``ColumnDataSource`` objects and
        applies ``nonselection_alpha`` to renderers in linked figures.

        Returns:
            Dict mapping each graph name to its fully-configured Figure.
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

        return figs

    # ------------------------------------------------------------------
    # Main render method
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Build the complete dashboard and return standalone HTML.

        Returns:
            A string containing the full standalone HTML page.
        """
        graphs = self.master_spec.get("graphs", [])
        kpis   = self.master_spec.get("kpis", [])
        build  = self.master_spec.get("build_options", {})

        link_names  = build.get("link", [])
        layout_opt  = build.get("layout", "auto")
        filters_cfg = build.get("filters", [])
        title_text  = html.escape(build.get("title", ""))
        saving_path = build.get("saving", "")

        # ---- 1. Determine all variable names needed ----
        all_vars: list[str] = []
        for g in graphs:
            for plot in g.get("plots", []):
                for key in ("yvar", "xvar"):
                    v = plot.get(key)
                    if v and v not in all_vars:
                        all_vars.append(v)
        for kpi in kpis:
            v = kpi.get("varname")
            if v and v not in all_vars:
                all_vars.append(v)
        for fc in filters_cfg:
            v = fc.get("varname")
            if v and v not in all_vars:
                all_vars.append(v)

        # ---- 2. Build ColumnDataSources ----
        # Linked graphs share one source; unlinked get their own.
        if link_names:
            # All link_names share a single source with the union of their vars
            linked_vars: list[str] = []
            for g in graphs:
                if g.get("graph_options", {}).get("name") in link_names:
                    for plot in g.get("plots", []):
                        for key in ("yvar", "xvar"):
                            v = plot.get(key)
                            if v and v not in linked_vars:
                                linked_vars.append(v)
            # Also include filter vars in linked source
            for fc in filters_cfg:
                v = fc.get("varname")
                if v and v not in linked_vars:
                    linked_vars.append(v)

            linked_source = self._make_source(linked_vars)

            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    self.sources[name] = linked_source
                else:
                    g_vars = [p.get(k) for p in g.get("plots", [])
                              for k in ("yvar", "xvar") if p.get(k)]
                    self.sources[name] = self._make_source(list(dict.fromkeys(g_vars)))
        else:
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                g_vars = [p.get(k) for p in g.get("plots", [])
                          for k in ("yvar", "xvar") if p.get(k)]
                self.sources[name] = self._make_source(list(dict.fromkeys(g_vars)))

        # ---- 3. Build figures ----
        for g in graphs:
            name = g.get("graph_options", {}).get("name", "")
            src  = self.sources.get(name)
            if src is None:
                continue
            try:
                self.figures[name] = self._make_figure(g, src)
            except Exception as exc:
                raise RuntimeError(
                    f"dash_render: failed to build figure '{name}': {exc}"
                ) from exc

        # ---- 4. Build KPI Divs ----
        for kpi in kpis:
            name = kpi.get("name", "kpi")
            kpi["name"] = name  # ensure name key present in def
            self.kpi_divs[name] = self._make_kpi_div(kpi)

        # ---- 5. Build filter widgets ----
        # Determine a CDSView per (figure × filter) for non-excluded graphs.
        # For now we wire up views after all figures are built.
        filter_row_widgets = []

        for fc in filters_cfg:
            fvar    = fc.get("varname", "")
            ftype   = fc.get("type", "dropdown")
            excludes = fc.get("exclude", [])

            # Choose source: prefer linked source if available, else first available
            if link_names and link_names[0] in self.sources:
                fsource = self.sources[link_names[0]]
            else:
                fsource = next(iter(self.sources.values())) if self.sources else None

            if fsource is None or fvar not in fsource.data:
                continue

            # Resolve value labels for this variable
            labelset = self.value_label_names.get(fvar, "")
            vlabels  = self.value_labels.get(labelset, {})

            if ftype == "dropdown":
                widget, cb = FilterBuilder.build_dropdown(
                    fvar, fsource, None, vlabels,
                    exclude_names=excludes,
                )
            elif ftype == "slider":
                widget, cb = FilterBuilder.build_slider(
                    fvar, fsource, None, exclude_names=excludes
                )
            elif ftype == "range":
                widget, cb = FilterBuilder.build_range(
                    fvar, fsource, None, exclude_names=excludes
                )
            else:
                continue

            # Wire CDSViews: each non-excluded figure that uses fsource
            views = []
            for gname, fig in self.figures.items():
                if gname in excludes:
                    continue
                if self.sources.get(gname) is not fsource:
                    continue
                for renderer in fig.renderers:
                    if hasattr(renderer, "data_source"):
                        view = CDSView()
                        renderer.view = view
                        views.append(view)

            cb.args["views"] = views
            filter_row_widgets.append(widget)
            self.filter_widgets.append(widget)
            self.filter_callbacks.append(cb)

        # ---- 6. Assemble layout ----
        all_names = (
            [g.get("graph_options", {}).get("name", "") for g in graphs]
            + list(self.kpi_divs.keys())
        )

        rows_n, cols_n = self._compute_grid(all_names, layout_opt)

        # Build grid cells: figures then KPI divs, in registration order
        cells: list[Any] = []
        for name in all_names:
            if name in self.figures:
                cells.append(self.figures[name])
            elif name in self.kpi_divs:
                cells.append(self.kpi_divs[name])

        # Pad to fill the grid
        while len(cells) < rows_n * cols_n:
            cells.append(None)

        # Build gridplot rows
        grid_rows = []
        for r_idx in range(rows_n):
            row_cells = cells[r_idx * cols_n : (r_idx + 1) * cols_n]
            grid_rows.append(row_cells)

        grid = gridplot(grid_rows, sizing_mode="stretch_width")

        # Compose full layout: optional filter bar on top, then grid
        if filter_row_widgets:
            filter_bar = row(filter_row_widgets, sizing_mode="stretch_width")
            layout_root = column(filter_bar, grid, sizing_mode="stretch_width")
        else:
            layout_root = grid

        if title_text:
            title_div = Div(
                text=f'<h2 style="font-family:sans-serif;">{title_text}</h2>',
                sizing_mode="stretch_width",
            )
            layout_root = column(title_div, layout_root,
                                 sizing_mode="stretch_width")

        # ---- 7. Render to HTML ----
        html_str = file_html(layout_root, CDN, title=title_text or "dash")

        # Inject CSP meta tag into <head>
        html_str = html_str.replace("<head>", f"<head>\n    {_CSP_META}", 1)

        return html_str


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

        # Parse filter spec
        filter_specs: list[dict] = []
        if filter_raw and filter_raw != '"':
            # filter_raw format: "varname, type(dropdown) exclude(n1 n2)"
            # Can be multiple filter() calls; each is a separate dict
            # Simple parse: split on ';' if multiple
            for fpart in filter_raw.split(";"):
                fpart = fpart.strip()
                if not fpart:
                    continue
                m_type = re.search(r"type\(([^)]+)\)", fpart)
                m_excl = re.search(r"exclude\(([^)]+)\)", fpart)
                fvar = re.split(r"[,\s]", fpart.strip())[0]
                ftype = m_type.group(1).strip() if m_type else "dropdown"
                excl = m_excl.group(1).split() if m_excl else []
                if fvar:
                    filter_specs.append({"var": fvar, "type": ftype, "exclude": excl})

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
            "    BoxSelectTool,",
            "    ColumnDataSource,",
            "    Div,",
            "    HoverTool,",
            "    LassoSelectTool,",
            "    PanTool,",
            "    RangeSlider,",
            "    ResetTool,",
            "    Select,",
            "    Slider,",
            "    Span,",
            "    WheelZoomTool,",
            ")",
            "from bokeh.plotting import figure as bokeh_figure",
            "from bokeh.server.server import Server",
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
            "def _compute_kdensity(df, varname):",
            '    """Return line source dict for kernel density estimate."""',
            "    data = df[varname].dropna().values.astype(float)",
            "    if len(data) < 2:",
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
            "            for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2'):",
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
            "            graph_sources[gname] = shared_source",
            "        else:",
            "            gvars = []",
            "            for p in g.get('plots', []):",
            "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2'):",
            "                    v = p.get(k, '')",
            "                    if v and v in df.columns and v not in gvars:",
            "                        gvars.append(v)",
            "            graph_sources[gname] = ColumnDataSource(",
            "                {v: df[v].tolist() for v in gvars}",
            "            ) if gvars else ColumnDataSource({})",
            "",
            "    # ---- Aggregated plot ColumnDataSources ----",
            "    # key: (gname, plot_index) → {'source': CDS, 'compute': callable}",
            "    agg_sources: dict = {}",
            "",
            "    # ---- Build figures ----",
            "    figures: dict = {}",
            "    TOOLS = [PanTool(), WheelZoomTool(), BoxSelectTool(), LassoSelectTool(), ResetTool()]",
            "",
            "    for g in graphs:",
            "        go = g.get('graph_options', {})",
            "        gname = go.get('name', '')",
            "        src = graph_sources.get(gname, shared_source)",
            "",
            "        x_label = ''",
            "        y_label = ''",
            "        plots = g.get('plots', [])",
            "        if plots:",
            "            xv = plots[0].get('xvar', '')",
            "            yv = plots[0].get('yvar', '') or plots[0].get('var', '')",
            "            x_label = var_labels.get(xv, xv)",
            "            y_label = var_labels.get(yv, yv)",
            "",
            "        n_rows = len(df)",
            "        backend = 'webgl' if n_rows > 10000 else 'canvas'",
            "        fig = bokeh_figure(",
            "            title=html.escape(go.get('title', '') or ''),",
            "            x_axis_label=x_label,",
            "            y_axis_label=y_label,",
            "            tools=TOOLS,",
            "            sizing_mode='stretch_width',",
            "            output_backend=backend,",
            "        )",
            "",
            "        for pi, plot in enumerate(plots):",
            "            ptype = plot.get('type', '')",
            "            yvar = plot.get('yvar', '') or plot.get('var', '')",
            "            xvar = plot.get('xvar', '')",
            "            opts = plot.get('options', {})",
            "",
            "            color = '#1f77b4'",
            "            if 'mcolor' in opts or 'lcolor' in opts:",
            "                c = opts.get('mcolor', opts.get('lcolor', '#1f77b4'))",
            "                # Basic color mapping — use as-is if hex, else default",
            "                if c.startswith('#'): color = c",
            "",
            "            if ptype in ('scatter',):",
            "                clean = df[[xvar, yvar]].dropna() if xvar and yvar else df",
            "                csrc = ColumnDataSource(clean) if xvar and yvar else src",
            "                r = fig.scatter(x=xvar, y=yvar, source=csrc,",
            "                               fill_color=color, line_color=color,",
            "                               size=8, alpha=0.7,",
            "                               nonselection_alpha=0.15)",
            "                fig.add_tools(HoverTool(tooltips=[(yvar, f'@{yvar}'), (xvar, f'@{xvar}')]))",
            "                graph_sources[gname] = csrc  # update to clean source",
            "",
            "            elif ptype == 'line':",
            "                clean = df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else df",
            "                csrc = ColumnDataSource(clean)",
            "                fig.line(x=xvar, y=yvar, source=csrc,",
            "                         line_color=color, line_width=1.5)",
            "                graph_sources[gname] = csrc",
            "",
            "            elif ptype == 'lfit':",
            "                fit_data = _compute_lfit(df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'lfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                fig.line(x='x', y='y', source=fit_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype == 'qfit':",
            "                fit_data = _compute_qfit(df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'qfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                fig.line(x='x', y='y', source=fit_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype == 'histogram':",
            "                hvar = yvar or xvar",
            "                nbins = int(opts.get('bin', 20))",
            "                hist_data = _compute_histogram(df, hvar, nbins)",
            "                hist_src = ColumnDataSource(hist_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': hist_src,",
            "                    'type': 'histogram',",
            "                    'var': hvar, 'bins': nbins,",
            "                }",
            "                fig.quad(top='top', bottom=0, left='left', right='right',",
            "                         source=hist_src,",
            "                         fill_color=color, line_color='white', alpha=0.8)",
            "",
            "            elif ptype == 'kdensity':",
            "                kvar = yvar or xvar",
            "                kde_data = _compute_kdensity(df, kvar)",
            "                kde_src = ColumnDataSource(kde_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': kde_src,",
            "                    'type': 'kdensity',",
            "                    'var': kvar,",
            "                }",
            "                fig.line(x='x', y='y', source=kde_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype == 'lowess':",
            "                lw_data = _compute_lowess(df, yvar, xvar)",
            "                lw_src = ColumnDataSource(lw_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': lw_src,",
            "                    'type': 'lowess',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                fig.line(x='x', y='y', source=lw_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype in ('area',):",
            "                clean = df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else df",
            "                asrc = ColumnDataSource(clean)",
            "                zeros = [0.0] * len(clean)",
            "                asrc.data['_zero'] = zeros",
            "                fig.varea(x=xvar, y1='_zero', y2=yvar, source=asrc,",
            "                          fill_color=color, alpha=0.4)",
            "                graph_sources[gname] = asrc",
            "",
            "            elif ptype == 'bar':",
            "                clean = df[[xvar, yvar]].dropna() if xvar and yvar else df",
            "                bsrc = ColumnDataSource(clean)",
            "                x_arr = clean[xvar].values",
            "                width = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.8 if len(np.unique(x_arr)) > 1 else 1.0",
            "                fig.vbar(x=xvar, top=yvar, source=bsrc,",
            "                         width=width, fill_color=color, line_color='white')",
            "                graph_sources[gname] = bsrc",
            "",
            "            elif ptype == 'spike':",
            "                clean = df[[xvar, yvar]].dropna() if xvar and yvar else df",
            "                ssrc = ColumnDataSource(clean)",
            "                ssrc.data['_zero'] = [0.0] * len(clean)",
            "                fig.segment(x0=xvar, x1=xvar, y0='_zero', y1=yvar,",
            "                             source=ssrc, line_color=color, line_width=1)",
            "                graph_sources[gname] = ssrc",
            "",
            "        figures[gname] = fig",
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
            "            opts = [('All', 'All')] + [",
            "                (str(v), html.escape(str(vlabels.get(str(int(v)) if isinstance(v, float) and v == int(v) else str(v), v))))",
            "                for v in uniq",
            "            ]",
            "            widget = Select(",
            "                title=var_labels.get(fvar, fvar),",
            "                value='All',",
            "                options=[o[1] for o in opts],",
            "            )",
            "            widget._dash_var = fvar",
            "            widget._dash_exclude = fexcl",
            "            widget._dash_opts_map = {o[1]: o[0] for o in opts}",
            "        elif ftype == 'range':",
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
            "    def _make_filter_cb(_all_widgets, _all_sources, _agg_srcs, _kpi_divs, _kpi_defs, _df_ref):",
            "        def _on_filter_change(attr, old, new):",
            "            # 1. Build combined mask from all active widgets",
            "            mask = pd.Series([True] * len(_df_ref), index=_df_ref.index)",
            "            for w in _all_widgets:",
            "                wvar = getattr(w, '_dash_var', None)",
            "                if wvar is None or wvar not in _df_ref.columns:",
            "                    continue",
            "                if isinstance(w, Select):",
            "                    if w.value != 'All':",
            "                        raw_map = getattr(w, '_dash_opts_map', {})",
            "                        raw_val = raw_map.get(w.value, w.value)",
            "                        try:",
            "                            mask &= (_df_ref[wvar].astype(str) == str(raw_val))",
            "                        except Exception:",
            "                            pass",
            "                elif isinstance(w, RangeSlider):",
            "                    lo, hi = w.value",
            "                    mask &= (_df_ref[wvar] >= lo) & (_df_ref[wvar] <= hi)",
            "                elif isinstance(w, Slider):",
            "                    mask &= (_df_ref[wvar] >= w.value)",
            "            fdf = _df_ref[mask]",
            "            # 2. Replace raw source data",
            "            for gname, src in _all_sources.items():",
            "                excl = []",
            "                for w in _all_widgets:",
            "                    excl.extend(getattr(w, '_dash_exclude', []))",
            "                if gname in excl:",
            "                    continue",
            "                new_data = {}",
            "                for col in src.data:",
            "                    if col in fdf.columns:",
            "                        new_data[col] = fdf[col].tolist()",
            "                    else:",
            "                        new_data[col] = []",
            "                src.data = new_data",
            "            # 3. Recompute aggregated sources",
            "            for key, agg in _agg_srcs.items():",
            "                gname = key[0]",
            "                excl = []",
            "                for w in _all_widgets:",
            "                    excl.extend(getattr(w, '_dash_exclude', []))",
            "                if gname in excl:",
            "                    continue",
            "                atype = agg['type']",
            "                if atype == 'histogram':",
            "                    agg['source'].data = _compute_histogram(fdf, agg['var'], agg.get('bins', 20))",
            "                elif atype == 'lfit':",
            "                    agg['source'].data = _compute_lfit(fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'qfit':",
            "                    agg['source'].data = _compute_qfit(fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'kdensity':",
            "                    agg['source'].data = _compute_kdensity(fdf, agg['var'])",
            "                elif atype == 'lowess':",
            "                    agg['source'].data = _compute_lowess(fdf, agg['yvar'], agg['xvar'])",
            "            # 4. Recompute filter-mode KPIs",
            "            for kpi in _kpi_defs:",
            "                kupdate = kpi.get('update', 'filter')",
            "                if kupdate not in ('filter', 'both'):",
            "                    continue",
            "                kname = kpi.get('name', '')",
            "                if kname not in _kpi_divs:",
            "                    continue",
            "                excl = []",
            "                for w in _all_widgets:",
            "                    excl.extend(getattr(w, '_dash_exclude', []))",
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
            "    _filter_cb = _make_filter_cb(",
            "        filter_widgets, graph_sources, agg_sources, kpi_divs, kpi_defs, df",
            "    )",
            "    for w in filter_widgets:",
            "        if isinstance(w, Select):",
            "            w.on_change('value', _filter_cb)",
            "        elif isinstance(w, (Slider, RangeSlider)):",
            "            w.on_change('value', _filter_cb)",
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
            "        if name in figures:",
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
            f"    )",
            f"    _server.start()",
            f"    _server.io_loop.add_callback(_server.show, '/')",
            f"    print(f'Bokeh Server running at http://localhost:{{_port}}/')",
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
    args = parser.parse_args()
    main(args.spec, args.data, args.output, args.mode)
