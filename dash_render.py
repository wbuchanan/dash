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
    Arrow,
    BooleanFilter,
    BoxSelectTool,
    CDSView,
    ColumnDataSource,
    CustomJS,
    Div,
    HoverTool,
    LassoSelectTool,
    NormalHead,
    OpenHead,
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

    def _apply_fill_opts(self, renderer: Any, options: dict[str, str]) -> None:
        """Apply fcolor/fintensity options to a filled glyph renderer.

        Args:
            renderer: A Bokeh GlyphRenderer whose glyph has fill_color /
                      fill_alpha attributes (VArea, VBar, Quad, etc.).
            options:  Translated per-plot options dict.
        """
        glyph = renderer.glyph
        if "fcolor" in options:
            try:
                glyph.fill_color = self.tr.translate_mcolor(options["fcolor"])
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
        self._apply_mlabel_opts(fig, clean_source, options, xvar, yvar)
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
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
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
        # Pass options without mlabel to sub-calls; apply mlabel once below
        opts_no_label = {k: v for k, v in options.items() if k != "mlabel"}
        renderers = [
            self.map_line(fig, source, yvar, xvar, opts_no_label),
            self.map_scatter(fig, source, yvar, xvar, opts_no_label),
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

        self._apply_fill_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    def map_bar(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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
        self._apply_fill_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    def map_spike(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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
        zeros = np.zeros_like(x_arr)

        seg_source = ColumnDataSource({
            "x0": x_arr, "y0": zeros,
            "x1": x_arr, "y1": y_arr,
        })
        r = fig.segment(x0="x0", y0="y0", x1="x1", y1="y1",
                        source=seg_source,
                        line_color="#1f77b4", line_width=1.5)
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

        # Need at least 3 points for a degree-2 polyfit
        if len(x) < 3:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

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

        # Need at least 3 points: df = n-2 must be >= 1, and we need
        # x to vary (non-zero variance) to avoid division by zero in se_fit.
        empty_ci_src = ColumnDataSource({
            "x_fit": [], "y_fit": [], "y_lower": [], "y_upper": []
        })
        if n < 3 or np.std(x) == 0.0:
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=0.2, fill_color="#d62728"
            )
            line_r = fig.line(x="x_fit", y="y_fit", source=empty_ci_src,
                              line_color="#d62728", line_width=2.0)
            return [line_r, band_r]

        slope, intercept, _, _, se = scipy_stats.linregress(x, y)
        x_fit = np.linspace(x.min(), x.max(), 200)
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

        # Need at least 3 points for a degree-2 polyfit
        if len(x) < 3:
            empty_ci_src = ColumnDataSource({
                "x_fit": [], "y_fit": [], "y_lower": [], "y_upper": []
            })
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=0.2, fill_color="#d62728"
            )
            line_r = fig.line(x="x_fit", y="y_fit", source=empty_ci_src,
                              line_color="#d62728", line_width=2.0)
            return [line_r, band_r]

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

        # Need at least 2 points for lowess
        if len(x) < 2:
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
        self._apply_fill_opts(r, options)
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
        self._apply_fill_opts(r, options)
        return [r]

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
        self._apply_fill_opts(r, options)
        return [r]

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

        dl_source = ColumnDataSource({
            "x": x_arr, "y": y_arr, "y0": zeros,
        })
        color = "#1f77b4"
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        seg = fig.segment(x0="x", y0="y0", x1="x", y1="y",
                          source=dl_source, line_color=color, line_width=1.5)
        dot = fig.scatter(x="x", y="y", source=dl_source,
                          fill_color=color, line_color=color, size=8)
        self._apply_line_opts(seg, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return [seg, dot]

    def map_rcapsym(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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

        color = "#1f77b4"
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        spine   = fig.segment(x0="x",     y0="y1",  x1="x",     y1="y2",
                              source=cap_source, line_color=color, line_width=1.5)
        bot_cap = fig.segment(x0="x0_cap", y0="y1", x1="x1_cap", y1="y1",
                              source=cap_source, line_color=color, line_width=1.5)
        top_cap = fig.segment(x0="x0_cap", y0="y2", x1="x1_cap", y1="y2",
                              source=cap_source, line_color=color, line_width=1.5)
        bot_dot = fig.scatter(x="x", y="y1", source=cap_source,
                              fill_color=color, line_color=color, size=7)
        top_dot = fig.scatter(x="x", y="y2", source=cap_source,
                              fill_color=color, line_color=color, size=7)
        self._apply_line_opts(spine, options)
        return [spine, bot_cap, top_cap, bot_dot, top_dot]

    def map_scatteri(
        self,
        fig: Any,
        values: list,
        options: dict[str, str],
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

        y_vals = [float(pair[0]) for pair in values]
        x_vals = [float(pair[1]) for pair in values]
        si_source = ColumnDataSource({"x": x_vals, "y": y_vals})

        color = "#1f77b4"
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
        r = fig.segment(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                        source=source_clean,
                        line_color="#1f77b4", line_width=1.5)
        self._apply_line_opts(r, options)
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

        color = "#1f77b4"
        try:
            if "lcolor" in options:
                color = self.tr.translate_lcolor(options["lcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        seg = fig.segment(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                          source=pc_source, line_color=color, line_width=1.5)

        # Add Arrow head annotations for each row
        for _, row in clean.iterrows():
            arrow = Arrow(
                end=OpenHead(size=10, line_color=color),
                x_start=float(row[x1var]),
                y_start=float(row[y1var]),
                x_end=float(row[x2var]),
                y_end=float(row[y2var]),
                line_color=color,
                line_width=1.5,
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

        color = "#1f77b4"
        try:
            if "lcolor" in options:
                color = self.tr.translate_lcolor(options["lcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        seg = fig.segment(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                          source=pc_source, line_color=color, line_width=1.5)

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
                line_width=1.5,
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
        return self.map_line(fig, source, yvar, xvar, options)

    def map_tsrline(
        self,
        fig: Any,
        source: ColumnDataSource,
        y1var: str,
        y2var: str,
        xvar: str,
        options: dict[str, str],
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
        return self.map_rline(fig, source, y1var, y2var, xvar, options)

    def map_mspline(
        self,
        fig: Any,
        source: ColumnDataSource,
        yvar: str,
        xvar: str,
        options: dict[str, str],
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

        # Need at least 2 valid points for interpolation
        if len(x_clean) < 2:
            empty = ColumnDataSource({"x_ms": [], "y_ms": []})
            return [fig.line(x="x_ms", y="y_ms", source=empty)]

        interp = PchipInterpolator(x_clean, y_clean)
        x_grid = np.linspace(x_clean.min(), x_clean.max(), 200)
        y_grid = interp(x_grid)

        ms_source = ColumnDataSource({"x_ms": x_grid, "y_ms": y_grid})
        r = fig.line(x="x_ms", y="y_ms", source=ms_source,
                     line_color="#2ca02c", line_width=2.0)
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
                     line_color="#d62728", line_width=2.0)
        self._apply_line_opts(r, options)
        return [r]


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
        if len(arr) == 0:
            # No valid data for this variable; return a disabled dummy slider
            widget = Slider(title=safe_var, start=0, end=1, value=0, step=1,
                            disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        # Ensure end > start for Bokeh Slider (required constraint)
        if vmin == vmax:
            vmax = vmin + 1.0
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
        if len(arr) == 0:
            # No valid data for this variable; return a disabled dummy range slider
            widget = RangeSlider(title=safe_var, start=0, end=1,
                                 value=(0, 1), step=1, disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        # Ensure end > start for Bokeh RangeSlider (required constraint)
        if vmin == vmax:
            vmax = vmin + 1.0
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

            # Security: only allow column names, literals, operators
            # Reject any expression containing shell-injection characters or
            # Python code constructs.
            _UNSAFE = _re.compile(r'[;`$\\]|import\s|__|\beval\b|\bexec\b|\bopen\b')
            if _UNSAFE.search(pandas_expr):
                pass  # silently skip unsafe if_expr
            else:
                try:
                    # Validate column names referenced in expression
                    # Use a restricted pandas query with the 'python' engine
                    df = df.query(pandas_expr, engine="python")
                except Exception:
                    pass  # malformed if_expr → no filtering; don't crash

        return df

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

        fig = bokeh_figure(**fig_kwargs)

        # Log scale options
        if graph_opts.get("xscale") == "log":
            # Rebuild with log x-axis
            kw = {**fig_kwargs, "x_axis_type": "log"}
            kw.pop("tools", None)
            fig = bokeh_figure(**kw)
        if graph_opts.get("yscale") == "log":
            kw = {**fig_kwargs, "y_axis_type": "log"}
            kw.pop("tools", None)
            fig = bokeh_figure(**kw)

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

        # Legend placement
        legend_opt = graph_opts.get("legend", "")
        if legend_opt and fig.legend:
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
                fig.legend.visible = False
            elif legend_opt in loc_map and loc_map[legend_opt]:
                try:
                    fig.legend.location = loc_map[legend_opt]
                except Exception:
                    pass

        # Custom axis tick values (xlabel / ylabel)
        from bokeh.models.tickers import FixedTicker
        from bokeh.models.formatters import CustomJSTickFormatter
        for ax_key, axis_obj in (("xlabel", fig.xaxis), ("ylabel", fig.yaxis)):
            raw_ax = graph_opts.get(ax_key, "")
            if raw_ax:
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

        # Plot categories that use non-standard JSON variable keys
        _RANGE_TYPES = frozenset({
            "rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
            "rcapsym", "tsrline",
        })
        _UNIVARIATE_TYPES = frozenset({"histogram", "hist", "kdensity"})
        _PC_TYPES = frozenset({"pcspike", "pcarrow", "pcbarrow"})

        # Add glyphs for each plot layer
        for plot in plots:
            ptype = plot.get("type", "scatter")
            pxvar = plot.get("xvar", xvar)
            popts = plot.get("options", {})

            if ptype.lower() == "scatteri":
                # Inline coordinate list — no shared source variable needed
                self.mapper.map_scatteri(fig, plot.get("values", []), popts)
            elif ptype.lower() in _PC_TYPES:
                py1var = plot.get("y1var", "")
                px1var = plot.get("x1var", "")
                py2var = plot.get("y2var", "")
                px2var = plot.get("x2var", "")
                self._add_pc_glyph(fig, source, ptype, py1var, px1var, py2var, px2var, popts)
            elif ptype.lower() in _RANGE_TYPES:
                py1var = plot.get("yvar1", "")
                py2var = plot.get("yvar2", "")
                self._add_glyph(fig, source, ptype, py1var, pxvar, popts,
                                y2var=py2var)
            elif ptype.lower() in _UNIVARIATE_TYPES:
                pyvar = (plot.get("yvar", "") or plot.get("var", "")
                         or yvar)
                self._add_glyph(fig, source, ptype, pyvar, pxvar, popts)
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
                        n_pts = int(popts["n"])
                    except ValueError:
                        pass
                self.mapper.map_function(fig, pexpr, (x_lo, x_hi), n_pts, popts)
            else:
                pyvar = plot.get("yvar", yvar)
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
        y2var: str = "",
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
            "histogram":  self.mapper.map_histogram,
            "hist":       self.mapper.map_histogram,
            "kdensity":   self.mapper.map_kdensity,
            "dot":        self.mapper.map_dot,
            "dropline":   self.mapper.map_dropline,
            "tsline":     self.mapper.map_tsline,
            "mspline":    self.mapper.map_mspline,
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
        }

        pt = plot_type.lower()

        # Range plots: (fig, source, y1var, y2var, xvar, options)
        rfn = range_dispatch.get(pt)
        if rfn is not None and y2var:
            rfn(fig, source, yvar, y2var, xvar, options)
            return

        fn = dispatch.get(pt)
        if fn is not None:
            # histogram and kdensity are univariate — no xvar positional arg
            if pt in ("histogram", "hist", "kdensity"):
                fn(fig, source, yvar, options)
            else:
                fn(fig, source, yvar, xvar, options)

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
    ) -> None:
        """Dispatch a paired-coordinate plot layer to the correct GlyphMapper method.

        Args:
            fig:        Bokeh Figure to add the glyph to.
            source:     ColumnDataSource.
            plot_type:  Paired-coordinate plot type name (pcspike, pcarrow, pcbarrow).
            y1var:      Start y variable name.
            x1var:      Start x variable name.
            y2var:      End y variable name.
            x2var:      End x variable name.
            options:    Plot-level options dict.
        """
        pc_dispatch = {
            "pcspike":  self.mapper.map_pcspike,
            "pcarrow":  self.mapper.map_pcarrow,
            "pcbarrow": self.mapper.map_pcbarrow,
        }
        fn = pc_dispatch.get(plot_type.lower())
        if fn is not None:
            fn(fig, source, y1var, x1var, y2var, x2var, options)

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
        # Keys that can hold variable names in plot specs
        _VK = ("yvar", "xvar", "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var")

        if link_names:
            # Collect all variable names needed by linked graphs
            linked_vars: list[str] = []
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                if name in link_names:
                    for plot in g.get("plots", []):
                        for key in _VK:
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
                    # Linked graphs share a source; per-graph if/in not applied
                    sources[name] = linked_source
                else:
                    g_vars = [
                        p.get(k) for p in g.get("plots", [])
                        for k in _VK if p.get(k)
                    ]
                    filtered_df = self._apply_graph_filter(g)
                    sources[name] = self._make_source(
                        list(dict.fromkeys(g_vars)), df=filtered_df
                    )
        else:
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                g_vars = [
                    p.get(k) for p in g.get("plots", [])
                    for k in _VK if p.get(k)
                ]
                filtered_df = self._apply_graph_filter(g)
                sources[name] = self._make_source(
                    list(dict.fromkeys(g_vars)), df=filtered_df
                )

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
        _VAR_KEYS = ("yvar", "xvar", "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var")
        all_vars: list[str] = []
        for g in graphs:
            for plot in g.get("plots", []):
                for key in _VAR_KEYS:
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
                        for key in _VAR_KEYS:
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
                              for k in _VAR_KEYS if p.get(k)]
                    self.sources[name] = self._make_source(list(dict.fromkeys(g_vars)))
        else:
            for g in graphs:
                name = g.get("graph_options", {}).get("name", "")
                g_vars = [p.get(k) for p in g.get("plots", [])
                          for k in _VAR_KEYS if p.get(k)]
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
            "        fig = bokeh_figure(**_fig_kw)",
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
            "        # legend placement",
            "        _leg_opt = go.get('legend', '')",
            "        if _leg_opt and fig.legend:",
            "            if _leg_opt == 'off': fig.legend.visible = False",
            "            elif _leg_opt in ('top',): fig.legend.location = 'top_center'",
            "            elif _leg_opt in ('bottom',): fig.legend.location = 'bottom_center'",
            "            elif _leg_opt in ('left',): fig.legend.location = 'center_left'",
            "            elif _leg_opt in ('right',): fig.legend.location = 'center_right'",
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
            "        for _axk, _axobj in (('xlabel', fig.xaxis), ('ylabel', fig.yaxis)):",
            "            _raw_ax = go.get(_axk, '')",
            "            if _raw_ax:",
            "                _tks, _labs = _parse_axlabel(_raw_ax)",
            "                if _tks:",
            "                    _axobj.ticker = _FT(ticks=_tks)",
            "                    if _labs:",
            "                        _axobj.formatter = _CJSF(code=f'const m={_json.dumps(_labs)};return m[String(tick)]||String(tick);')",
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
            "            elif ptype == 'connected':",
            "                clean = df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else df",
            "                csrc = ColumnDataSource(clean)",
            "                fig.line(x=xvar, y=yvar, source=csrc,",
            "                         line_color=color, line_width=1.5)",
            "                fig.scatter(x=xvar, y=yvar, source=csrc,",
            "                            fill_color=color, size=8, alpha=0.7)",
            "                graph_sources[gname] = csrc",
            "",
            "            elif ptype == 'dot':",
            "                clean = df[[xvar, yvar]].dropna() if xvar and yvar else df",
            "                dsrc = ColumnDataSource(clean)",
            "                fig.scatter(x=xvar, y=yvar, source=dsrc,",
            "                            fill_color=color, size=8, alpha=0.7)",
            "                graph_sources[gname] = dsrc",
            "",
            "            elif ptype == 'lfitci':",
            "                fit_data = _compute_lfit(df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'lfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                fig.varea(x='x', y1='y', y2='y', source=fit_src,",
            "                          fill_color=color, alpha=0.2)",
            "                fig.line(x='x', y='y', source=fit_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype == 'qfitci':",
            "                fit_data = _compute_qfit(df, yvar, xvar)",
            "                fit_src = ColumnDataSource(fit_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'source': fit_src,",
            "                    'type': 'qfit',",
            "                    'yvar': yvar, 'xvar': xvar,",
            "                }",
            "                fig.varea(x='x', y1='y', y2='y', source=fit_src,",
            "                          fill_color=color, alpha=0.2)",
            "                fig.line(x='x', y='y', source=fit_src,",
            "                         line_color=color, line_width=2)",
            "",
            "            elif ptype == 'rarea':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.varea(x=xvar, y1=y1var, y2=y2var, source=rsrc,",
            "                              fill_color=color, alpha=0.4)",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'rbar':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    x_arr = rclean[xvar].values",
            "                    rw = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.8 if len(np.unique(x_arr)) > 1 else 1.0",
            "                    fig.vbar(x=xvar, bottom=y1var, top=y2var, source=rsrc,",
            "                             width=rw, fill_color=color, line_color='white')",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'rspike':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var,",
            "                                source=rsrc, line_color=color, line_width=1.5)",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'rcap':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna()",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.segment(x0=xvar, y0=y1var, x1=xvar, y1=y2var,",
            "                                source=rsrc, line_color=color, line_width=1.5)",
            "                    # Horizontal caps",
            "                    x_arr = rclean[xvar].values",
            "                    cap_hw = float(np.diff(np.sort(np.unique(x_arr))).min()) * 0.2 if len(np.unique(x_arr)) > 1 else 0.2",
            "                    cap_data = dict(",
            "                        x0_c=x_arr - cap_hw, x1_c=x_arr + cap_hw,",
            "                        yb=rclean[y1var].values, yt=rclean[y2var].values,",
            "                    )",
            "                    cap_src = ColumnDataSource(cap_data)",
            "                    fig.segment(x0='x0_c', y0='yb', x1='x1_c', y1='yb',",
            "                                source=cap_src, line_color=color, line_width=1.5)",
            "                    fig.segment(x0='x0_c', y0='yt', x1='x1_c', y1='yt',",
            "                                source=cap_src, line_color=color, line_width=1.5)",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'rline':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.line(x=xvar, y=y1var, source=rsrc,",
            "                             line_color=color, line_width=1.5)",
            "                    fig.line(x=xvar, y=y2var, source=rsrc,",
            "                             line_color=color, line_width=1.5, line_dash='dashed')",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'rconnected':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.line(x=xvar, y=y1var, source=rsrc,",
            "                             line_color=color, line_width=1.5)",
            "                    fig.scatter(x=xvar, y=y1var, source=rsrc,",
            "                                fill_color=color, size=6)",
            "                    fig.line(x=xvar, y=y2var, source=rsrc,",
            "                             line_color=color, line_width=1.5, line_dash='dashed')",
            "                    fig.scatter(x=xvar, y=y2var, source=rsrc,",
            "                                fill_color=color, size=6)",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'dropline':",
            "                if yvar and xvar:",
            "                    clean = df[[xvar, yvar]].dropna()",
            "                    dsrc = ColumnDataSource({",
            "                        'x': clean[xvar].values,",
            "                        'y': clean[yvar].values,",
            "                        'y0': np.zeros(len(clean)),",
            "                    })",
            "                    fig.segment(x0='x', y0='y0', x1='x', y1='y',",
            "                                source=dsrc, line_color=color, line_width=1.5)",
            "                    fig.scatter(x='x', y='y', source=dsrc,",
            "                                fill_color=color, line_color=color, size=8)",
            "                    graph_sources[gname] = dsrc",
            "",
            "            elif ptype == 'rcapsym':",
            "                if y1var and y2var and xvar:",
            "                    rcols = [c for c in [y1var, y2var, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna()",
            "                    x_arr = rclean[xvar].values",
            "                    uniq_x = np.unique(x_arr)",
            "                    cap_hw = float(np.diff(np.sort(uniq_x)).min()) * 0.2 if len(uniq_x) > 1 else 0.2",
            "                    cap_data = dict(",
            "                        x=x_arr,",
            "                        y1=rclean[y1var].values, y2=rclean[y2var].values,",
            "                        x0_c=x_arr - cap_hw, x1_c=x_arr + cap_hw,",
            "                    )",
            "                    csrc = ColumnDataSource(cap_data)",
            "                    fig.segment(x0='x', y0='y1', x1='x', y1='y2',",
            "                                source=csrc, line_color=color, line_width=1.5)",
            "                    fig.segment(x0='x0_c', y0='y1', x1='x1_c', y1='y1',",
            "                                source=csrc, line_color=color, line_width=1.5)",
            "                    fig.segment(x0='x0_c', y0='y2', x1='x1_c', y1='y2',",
            "                                source=csrc, line_color=color, line_width=1.5)",
            "                    fig.scatter(x='x', y='y1', source=csrc,",
            "                                fill_color=color, size=7)",
            "                    fig.scatter(x='x', y='y2', source=csrc,",
            "                                fill_color=color, size=7)",
            "                    graph_sources[gname] = csrc",
            "",
            "            elif ptype == 'scatteri':",
            "                vals = plot.get('values', [])",
            "                if vals:",
            "                    si_y = [float(p[0]) for p in vals]",
            "                    si_x = [float(p[1]) for p in vals]",
            "                    si_src = ColumnDataSource({'x': si_x, 'y': si_y})",
            "                    fig.scatter(x='x', y='y', source=si_src,",
            "                                fill_color=color, size=8)",
            "",
            "            elif ptype in ('pcspike', 'pcarrow', 'pcbarrow'):",
            "                pc_y1 = plot.get('y1var', '')",
            "                pc_x1 = plot.get('x1var', '')",
            "                pc_y2 = plot.get('y2var', '')",
            "                pc_x2 = plot.get('x2var', '')",
            "                if pc_y1 and pc_x1 and pc_y2 and pc_x2:",
            "                    cols = [c for c in [pc_y1, pc_x1, pc_y2, pc_x2] if c in df.columns]",
            "                    if len(cols) == 4:",
            "                        pclean = df[cols].dropna()",
            "                        pcsrc = ColumnDataSource(pclean)",
            "                        fig.segment(x0=pc_x1, y0=pc_y1, x1=pc_x2, y1=pc_y2,",
            "                                    source=pcsrc, line_color=color, line_width=1.5)",
            "                        graph_sources[gname] = pcsrc",
            "",
            "            elif ptype == 'tsline':",
            "                clean = df[[xvar, yvar]].dropna().sort_values(xvar) if xvar and yvar else df",
            "                csrc = ColumnDataSource(clean)",
            "                fig.line(x=xvar, y=yvar, source=csrc,",
            "                         line_color=color, line_width=1.5)",
            "                graph_sources[gname] = csrc",
            "",
            "            elif ptype == 'tsrline':",
            "                ts_y1 = plot.get('yvar1', '')",
            "                ts_y2 = plot.get('yvar2', '')",
            "                if ts_y1 and ts_y2 and xvar:",
            "                    rcols = [c for c in [ts_y1, ts_y2, xvar] if c in df.columns]",
            "                    rclean = df[rcols].dropna().sort_values(xvar)",
            "                    rsrc = ColumnDataSource(rclean)",
            "                    fig.line(x=xvar, y=ts_y1, source=rsrc,",
            "                             line_color=color, line_width=1.5)",
            "                    fig.line(x=xvar, y=ts_y2, source=rsrc,",
            "                             line_color=color, line_width=1.5, line_dash='dashed')",
            "                    graph_sources[gname] = rsrc",
            "",
            "            elif ptype == 'mspline':",
            "                if xvar and yvar:",
            "                    try:",
            "                        from scipy.interpolate import PchipInterpolator",
            "                        mclean = df[[xvar, yvar]].dropna().sort_values(xvar)",
            "                        if len(mclean) >= 2:",
            "                            interp = PchipInterpolator(mclean[xvar].values, mclean[yvar].values)",
            "                            x_grid = np.linspace(mclean[xvar].min(), mclean[xvar].max(), 200)",
            "                            y_grid = interp(x_grid)",
            "                            ms_src = ColumnDataSource({'x_ms': x_grid.tolist(), 'y_ms': y_grid.tolist()})",
            "                            fig.line(x='x_ms', y='y_ms', source=ms_src,",
            "                                     line_color=color, line_width=2.0)",
            "                    except Exception:",
            "                        pass",
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
            "                    try: n_pts = int(opts['n'])",
            "                    except ValueError: pass",
            "                _SAFE_NAMES = frozenset({'x', 'pi', 'e'})",
            "                _SAFE_FUNCS = frozenset({'sin','cos','tan','exp','log','log10','sqrt','abs','floor','ceil'})",
            "                def _val_node(node):",
            "                    if isinstance(node, _ast.Expression): _val_node(node.body)",
            "                    elif isinstance(node, _ast.Constant): pass",
            "                    elif isinstance(node, _ast.Name):",
            "                        if node.id not in _SAFE_NAMES: raise ValueError(f'Unsafe name: {node.id!r}')",
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
            "                    fn_src = ColumnDataSource({'x_fn': _x.tolist(), 'y_fn': np.asarray(_y, dtype=float).tolist()})",
            "                    fig.line(x='x_fn', y='y_fn', source=fn_src,",
            "                             line_color=color, line_width=2.0)",
            "                except Exception:",
            "                    pass",
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
