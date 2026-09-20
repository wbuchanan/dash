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
import warnings
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
# Optional scientific dependencies
# ---------------------------------------------------------------------------
# One bootstrap resample count for every CI layer.  These call sites had
# drifted to 200 in three places and 500 in a fourth, with the docstring
# claiming 200 -- so the same band was computed to different precision
# depending on which plot type drew it.
_N_BOOT_DEFAULT = 200

# Stata's factory default confidence level.  dash.ado serializes the SESSION
# value of c(level), so `set level 90` is honoured; this is only the fallback
# for a spec that predates that (an older dash.ado against a newer renderer).
_DEFAULT_LEVEL = 95.0

# Fractional-polynomial fits are drawn on this grid by BOTH fpfit and fpfitci.
# They used 200 and 150 respectively, over different x-ranges, so the same
# curve drawn two ways did not overlay.
# fpfit/fpfitci evaluate at the distinct observed x values, exactly as Stata
# does -- this is a cap for resource exhaustion, not a grid size.
_FP_GRID_MAX = 1000

# Bootstrap KPI cards per row.  A design choice about legibility, not
# something derivable from the content.
_MAX_KPIS_PER_ROW = 4

# The band within which a figure's aspect ratio is honoured, in pixels.
# Outside it the ratio yields, so that one square panel cannot fill an entire
# screen and a 10x2in panel on a phone does not collapse to a 73px sliver.
# Measured at 375px: without the floor, xsize(10) ysize(2) rendered 367x74.
_MAX_FIGURE_HEIGHT = 560
_MIN_FIGURE_HEIGHT = 160

# Stata's fit-line grid: n() defaults to 100 and the points run from the
# observed minimum to the observed maximum --
# x_i = min + (i-1)*(max-min)/(n-1), from ado/base/_/_gs_x_create.ado.
# dash used 200 points and padded the range by 10% on each side, so its fit
# line extended past the data where Stata's stops at it.
_FIT_GRID = 100

# Fan-Gijbels rule-of-thumb constant for the default lpoly bandwidth.  Measured
# against Stata, NOT derived: see GlyphMapper._default_lpoly_bwidth.
_LPOLY_ROT_C = 0.65



# ======================================================================
# Stata display formats
# ======================================================================
# Stata's display formats never leave Stata on their own: jsonio cannot emit
# them (its metaprint() branch is gated on a concatenation of `metaprint' and
# `filenm', so a non-empty filenm() makes it unmatchable, and StataAllToJSON
# has no format field at all -- it holds Variables.getDisplayFmt() internally
# and never serializes it).  dash therefore carries them itself, in its own
# master JSON, under build_options["formats"].  jsonio is not modified.
#
# What jsonio DOES do with a %t* variable is worse than dropping the format:
# it renders the variable THROUGH the format and emits a JSON string, while
# still reporting variableIsString=false.  sp500's `date` arrived as
# "02jan2001", _load_data coerced it to NaN, every row was dropped, and
# `dash line close date` produced a dashboard with zero data points.
# dash.ado now swaps a date variable to a plain numeric format for the
# duration of the jsonio call so the SIF value is transported intact.

_STATA_DATE_KINDS = frozenset({"tc", "tC", "td", "th", "tm", "tq", "tw", "ty"})

# %t or %-t, then exactly one kind letter, CASE SENSITIVELY -- %tc and %tC are
# different formats -- optionally followed by a custom date picture.
_DATE_FMT_RE = re.compile(r"^%-?t([cCdhmqwy])")

_STATA_EPOCH = pd.Timestamp("1960-01-01")


def _tooltip_precision(values) -> str:
    """Choose a tooltip number format from the spread of *values*.

    The fallback tooltips carried three different hardcoded precisions
    (``0.2f``, ``0.3f``, ``0.4f``) in three adjacent branches, so the same
    quantity was shown to different accuracy depending on which glyph was
    under the cursor.

    Args:
        values: The column the tooltip will show.

    Returns:
        A Bokeh number format such as ``"0.00"``.
    """
    try:
        arr = np.asarray(list(values), dtype=float)
        arr = arr[np.isfinite(arr)]
    except (TypeError, ValueError):
        return "0.00"
    if arr.size == 0:
        return "0.00"
    spread = float(np.nanmax(arr) - np.nanmin(arr))
    if spread <= 0:
        spread = abs(float(arr[0])) or 1.0
    # Aim for roughly four significant figures across the visible range.
    decimals = int(min(6, max(0, 4 - math.floor(math.log10(spread)) - 1)))
    return "0" if decimals == 0 else "0." + "0" * decimals


def _format_date_value_standalone(value, kind: str) -> str:
    """Render one date value; the module-level twin of
    :meth:`DashRenderer._format_date_value`, for callers that have no
    renderer instance (the glyph mapper builds marker labels on its own)."""
    try:
        ts = (pd.Timestamp(value) if not isinstance(value, (int, float))
              else pd.Timestamp(float(value), unit="ms"))
    except (TypeError, ValueError, OverflowError):
        return str(value)
    if pd.isna(ts):
        return ""
    if kind == "ty":
        return f"{ts.year}"
    if kind in ("tc", "tC"):
        return ts.strftime("%d %b %Y %H:%M:%S")
    if kind in ("tm", "tq", "th"):
        return ts.strftime("%b %Y")
    return ts.strftime("%d %b %Y")


def _is_datetime_column(source, varname: str) -> bool:
    """True when *varname* in *source* holds datetime values.

    A datetime64 column fails ``is_numeric_dtype``, and the range and slider
    filters skipped any column that failed it (commit b25584c, added for
    string columns) -- so a date range filter produced NO WIDGET at all.

    Args:
        source:  A ColumnDataSource or mapping.
        varname: Column name.

    Returns:
        Whether the column is datetime-like.
    """
    try:
        col = source.data[varname]
    except (AttributeError, KeyError, TypeError):
        return False
    try:
        return bool(pd.api.types.is_datetime64_any_dtype(pd.Series(col)))
    except (TypeError, ValueError):
        return False


def _datetime_formatter_for(kind: str):
    """A DatetimeTickFormatter matched to a Stata date kind.

    Args:
        kind: One of :data:`_STATA_DATE_KINDS`.

    Returns:
        A configured ``DatetimeTickFormatter``.
    """
    from bokeh.models import DatetimeTickFormatter

    if kind == "ty":
        return DatetimeTickFormatter(years="%Y", months="%Y", days="%Y")
    if kind in ("tc", "tC"):
        return DatetimeTickFormatter(
            years="%Y", months="%b %Y", days="%d %b %Y",
            hours="%d %b %H:%M", minutes="%H:%M", seconds="%H:%M:%S",
        )
    if kind in ("tm", "tq", "th"):
        return DatetimeTickFormatter(years="%Y", months="%b %Y",
                                     days="%b %Y")
    return DatetimeTickFormatter(years="%Y", months="%b %Y", days="%d %b %Y")


def _stata_date_kind(fmt: "str | None") -> "str | None":
    """Classify a Stata display format as one of the eight date kinds.

    Args:
        fmt: A Stata format string such as ``"%td"``, ``"%tdCCYY-NN-DD"`` or
             ``"%9.0fc"``.

    Returns:
        ``"td"``, ``"tc"``, ``"tC"``, ``"tw"``, ``"tm"``, ``"tq"``, ``"th"``
        or ``"ty"``; ``None`` when the format is not a date format.
    """
    if not fmt or not isinstance(fmt, str):
        return None
    m = _DATE_FMT_RE.match(fmt.strip())
    if not m:
        return None
    return "t" + m.group(1)


def _stata_dates_to_datetime(values: "pd.Series", kind: str) -> "pd.Series":
    """Convert Stata SIF values of a given date *kind* to datetime64.

    ``%tw``, ``%tm``, ``%tq`` and ``%th`` count CALENDAR periods, not
    fixed-length intervals, so they cannot be converted by multiplication;
    the timestamp is built from the period index.  ``%ty`` is the year
    itself and is not offset from 1960 at all (verified: ``display %ty 38``
    prints ``38``).

    Args:
        values: Numeric Stata values.
        kind:   One of :data:`_STATA_DATE_KINDS`.

    Returns:
        A datetime64 Series; unconvertible entries are ``NaT``.
    """
    v = pd.to_numeric(pd.Series(values).reset_index(drop=True),
                      errors="coerce")

    if kind == "tC":
        warnings.warn(
            "dash: %tC is a leap-second-corrected millisecond count. dash "
            "converts it with the same epoch as %tc, so timestamps are off "
            "by the accumulated leap seconds (up to 27 seconds for recent "
            "dates). Use %tc if that matters.",
            UserWarning, stacklevel=3,
        )

    def _from_parts(year, month):
        frame = pd.DataFrame({
            "year": year, "month": month,
            "day": np.ones(len(year), dtype="float64"),
        })
        ok = frame["year"].notna()
        out = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
        if ok.any():
            out.loc[ok] = pd.to_datetime(frame.loc[ok].astype("int64"),
                                          errors="coerce")
        return out

    try:
        if kind in ("tc", "tC"):
            out = _STATA_EPOCH + pd.to_timedelta(v, unit="ms", errors="coerce")
        elif kind == "td":
            out = _STATA_EPOCH + pd.to_timedelta(v, unit="D", errors="coerce")
        elif kind == "ty":
            out = _from_parts(v, pd.Series(np.ones(len(v))))
        elif kind == "tm":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 12.0), (idx % 12) + 1)
        elif kind == "tq":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 4.0), 3 * (idx % 4) + 1)
        elif kind == "th":
            idx = np.floor(v)
            out = _from_parts(1960 + np.floor(idx / 2.0), 6 * (idx % 2) + 1)
        elif kind == "tw":
            # Stata's weeks restart every year: week 52 is the last one, and
            # week 0 of a year is 1 January.  They are not 7-day offsets from
            # a single epoch.
            idx = np.floor(v)
            years = 1960 + np.floor(idx / 52.0)
            weeks = idx % 52
            base = _from_parts(years, pd.Series(np.ones(len(v))))
            out = base + pd.to_timedelta(weeks * 7, unit="D", errors="coerce")
        else:
            return pd.Series(pd.NaT, index=v.index, dtype="datetime64[ns]")
    except (OverflowError, ValueError, pd.errors.OutOfBoundsDatetime):
        out = pd.Series(pd.NaT, index=v.index, dtype="datetime64[ns]")

    out = pd.Series(out).reset_index(drop=True)
    lost = int((v.notna() & out.isna()).sum())
    if lost:
        # Stata's date range is wider than pandas' nanosecond datetime64
        # (1677-2262).  Coerce rather than raise, but never silently.
        warnings.warn(
            f"dash: {lost} value(s) of a %{kind} variable fall outside the "
            f"range of dates this renderer can represent (roughly 1677-2262) "
            f"and are shown as missing.",
            UserWarning, stacklevel=3,
        )
    return out


def _parse_stata_numeric_fmt(fmt: "str | None") -> "tuple | None":
    """Split a Stata numeric format into ``(width, decimals, kind, comma)``.

    Only the fixed (``f``) and exponential (``e``) families are recognised.
    ``%g`` is Stata's DEFAULT numeric format and expresses no user intent, so
    it is deliberately not reproduced -- a ``%g`` value is left alone.

    Args:
        fmt: A Stata format string.

    Returns:
        ``(width, decimals, kind, comma)`` or ``None``.
    """
    if not fmt or not isinstance(fmt, str):
        return None
    m = re.fullmatch(r"%(-)?(\d+)\.(\d+)(f|e)(c)?", fmt.strip())
    if not m:
        return None
    return int(m.group(2)), int(m.group(3)), m.group(4), bool(m.group(5))


def _stata_numeric_pattern(fmt: "str | None") -> "str | None":
    """Return a Bokeh/numbro tick pattern for a Stata numeric format.

    ``%9.0fc`` becomes ``"0,0"`` and ``%9.2f`` becomes ``"0.00"``.  Axis
    ticks and tooltips take a pattern rather than a formatted value.

    Args:
        fmt: A Stata format string.

    Returns:
        The pattern, or ``None`` when dash does not reproduce that format.
    """
    parsed = _parse_stata_numeric_fmt(fmt)
    if parsed is None:
        return None
    _w, dec, kind, comma = parsed
    if kind != "f":
        return None
    head = "0,0" if comma else "0"
    return f"{head}.{'0' * dec}" if dec else head


def _format_stata_numeric(value: float, fmt: "str | None") -> str:
    """Format *value* the way Stata's display format would.

    Reproduces the MEANING of the format -- decimal places, comma grouping,
    and the width-driven fallbacks Stata applies when a value does not fit --
    but not Stata's fixed-width left padding, which exists to align console
    columns and has none in an HTML dashboard.

    Stata's fallbacks, both measured: when a comma-grouped value would
    overflow the width the commas are dropped (``%9.0fc`` of -1234567.891 is
    ``-1234568``), and when it still does not fit the value goes to
    scientific notation with two mantissa decimals (``%9.2f`` of 1234567.891
    is ``1.23e+06``, and ``%12.2fc`` of 1e12 is ``1.00e+12`` -- two decimals
    at both widths and at both decimal counts, in every measured case).

    Args:
        value: The number to format.
        fmt:   A Stata format string.

    Returns:
        The formatted text, or ``""`` for a missing value.
    """
    parsed = _parse_stata_numeric_fmt(fmt)
    try:
        val = float(value)
    except (TypeError, ValueError):
        return ""
    if not np.isfinite(val):
        return ""
    if parsed is None:
        return f"{val:g}"

    width, dec, kind, comma = parsed

    if kind == "e":
        return f"{val:.{dec}e}"

    plain = f"{val:.{dec}f}"
    if comma:
        grouped = f"{val:,.{dec}f}"
        if len(grouped) <= width:
            return grouped
    if len(plain) <= width:
        return plain
    # Two mantissa decimals: measured for %9.0f, %9.2f and %12.2fc, i.e. at
    # two different widths and two different decimal counts.
    return f"{val:.2e}"


def _optional_import(module: str, attr: "str | None", package: str, feature: str):
    """Import an optional dependency, warning instead of raising.

    ``dash`` needs ``scipy`` only for CI bands, ``kdensity`` and ``mspline``,
    and ``statsmodels`` only for ``lowess``.  Neither is required to render a
    scatter, a line, a histogram, a fit, or anything else.  A missing or broken
    package must therefore degrade that one plot type to an empty glyph — the
    same shape already used by the minimum-N guards throughout this module —
    rather than abort the entire dashboard.

    ``Exception`` is caught rather than ``ImportError`` deliberately: a package
    can be present but unimportable because one of *its* dependencies is
    missing, which surfaces as an unrelated error type.

    ``__import__`` is used rather than ``importlib.import_module`` so that this
    keeps the semantics of the plain ``from x import y`` statements it
    replaced — the IMPORT_NAME opcode always routes through ``__import__``,
    which is both what the interpreter does and what makes the behaviour
    observable to tests that patch it.

    Args:
        module:  Dotted module path to import.
        attr:    Attribute to pull off the module, or None for the module.
        package: Distribution name to name in the warning (for dash_setup).
        feature: The dash plot type this enables, named in the warning.

    Returns:
        The imported object, or None if the import failed.
    """

    try:
        mod = __import__(module, fromlist=[attr] if attr else ["__name__"])
        return getattr(mod, attr) if attr else mod
    except Exception as exc:
        warnings.warn(
            f"dash: {feature} requires the '{package}' package, which could "
            f"not be imported ({type(exc).__name__}: {exc}). The {feature} "
            f"layer will be drawn empty. Run dash_setup to install or repair "
            f"'{package}'.",
            UserWarning,
            stacklevel=3,
        )
        return None


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Number of data points above which WebGL rendering is used for performance.
_WEBGL_THRESHOLD = 10_000

# Default nonselection alpha for linked-brushing dimming effect.
_NONSELECTION_ALPHA = 0.15

# Every ColumnDataSource carries this column: the row's position in the
# primary frame.  The filter callback used to compute one boolean mask from
# the primary source and apply it BY ROW INDEX to every source, on the
# strength of an inline comment claiming they all shared a row universe.
# They do not -- a by() graph gets one source per facet holding only that
# facet's rows, and a qualified graph a pre-filtered one -- so the mask
# landed on different observations entirely.  Masking on identity rather
# than position is robust to a shorter or reordered source.  An integer is
# enough; a string key would cost real bytes in a file already over a
# megabyte.
_ROW_ID_COLUMN = "__dash_row__"
# Marks the Legend that a discrete colorvar() builds, so the plot-legend
# rebuild can leave it alone.  A colour key is not a series key: Stata
# suppresses it with clegend(), not legend().
_COLORVAR_LEGEND_NAME = "_dash_clegend"
# Width of the filterposition(left) sidebar on the plain layout path, in
# pixels.  The Bootstrap path expresses the same thing as a grid span; this
# path has no grid to span, so it needs a number.  Wide enough for a slider
# plus its title at the default font.
_SIDEBAR_WIDTH_PX = 240

# Milliseconds in a day.  Bokeh transports datetimes as epoch milliseconds,
# but DateSlider.step and DateRangeSlider.step are in units of DAYS.
_MS_PER_DAY = 86_400_000.0
# Stata date formats whose values are whole calendar days or coarser.  A
# fraction of a day is not a value these can take, so their slider step is
# floored at one day.  %tc and %tC are clock values and are not in this set.
_CALENDAR_DATE_KINDS = frozenset({"td", "tw", "tm", "tq", "th", "ty"})


def _is_clock_kind(kind: str) -> bool:
    """True for Stata's clock formats, whose values are finer than a day."""
    return str(kind or "").lstrip("%") in ("tc", "tC")


def _date_slider_step_days(vmin: float, vmax: float) -> int:
    """Whole-day step for a calendar-date slider over ``vmin``..``vmax`` ms.

    Bokeh's ``DateSlider.step`` and ``DateRangeSlider.step`` are typed
    ``Int`` and documented "in units of days", and default to 1.  dash
    computed a step and never passed it, so a ten-year monthly series was
    stepped one day at a time -- two orders of magnitude finer than any value
    in the data, and a thousand drags to cross.

    Targets the same hundred notches the numeric path gives, floored at one
    whole day because these widgets cannot express less and because a
    fraction of a day is not a value a %td variable can take.

    Args:
        vmin: Lowest value, in epoch milliseconds.
        vmax: Highest value, in epoch milliseconds.

    Returns:
        A whole number of days, at least 1.
    """
    span_days = max(0.0, (float(vmax) - float(vmin)) / _MS_PER_DAY)
    return max(1, int(round(span_days / 100.0)))


def _clock_slider_step_ms(vmin: float, vmax: float) -> int:
    """Millisecond step for a clock slider over ``vmin``..``vmax`` ms.

    A ``%tc`` variable is why ``DateRangeSlider`` is the wrong widget: its
    step is a whole number of DAYS, so a clock series spanning one day had a
    single reachable notch.  ``DatetimeRangeSlider`` steps in milliseconds.

    Args:
        vmin: Lowest value, in epoch milliseconds.
        vmax: Highest value, in epoch milliseconds.

    Returns:
        A whole number of milliseconds, at least 1.
    """
    return max(1, int(round(max(0.0, float(vmax) - float(vmin)) / 100.0)))

# CSP meta tag injected into every output HTML file.
# 'unsafe-eval' is required because Bokeh's CustomJS compiles callback
# code via `new Function(...)` at runtime.  Without it the browser raises
# an EvalError and no filter or interactive callback fires.
_CSP_META = (
    '<meta http-equiv="Content-Security-Policy" '
    "content=\"script-src 'unsafe-inline' 'unsafe-eval';\">"
    # Without this a mobile browser lays the page out at its 980px default
    # and zooms the whole thing out to fit, so every breakpoint below 980px
    # is unreachable on a phone and the text is unreadable.  Found by opening
    # a dashboard at 375px: window.innerWidth reported 980.
    '\n<meta name="viewport" content="width=device-width, initial-scale=1">'
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
/* Cell heights keyed to a cell's span.  Every cell used to get the same
   height, so a narrow col-4 cell was as tall as a full-width col-12 one and
   looked stretched.  A min-height rather than a fixed height, so the cell
   still grows with its content and the layout stays responsive. */
.db-cell-h-sm{min-height:130px}
.db-cell-h-md{min-height:150px}
.db-cell-h-lg{min-height:170px}
@media(max-width:767px){
.db-cell-h-sm,.db-cell-h-md,.db-cell-h-lg{min-height:120px}
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
    """Parse an xscale()/yscale() option string for 'log' and 'reverse'.

    Args:
        raw: The raw option value string, e.g. 'log', 'reverse', 'log reverse'.

    Returns:
        (is_log, is_reverse) as booleans.
    """
    tokens = raw.lower().split()
    return ("log" in tokens), ("reverse" in tokens)


def _parse_scale_range(raw: str) -> "tuple[float | None, float | None]":
    """Extract ``range(# [#])`` from an xscale()/yscale() option string.

    Working range code already existed but was keyed on ``xrange``/``yrange``,
    which ``dash.ado`` never emits -- a dead read that made the option look
    implemented.  ``range()`` is Stata's actual spelling, and it may give one
    bound or two.

    Args:
        raw: The raw option value.

    Returns:
        ``(lo, hi)``, either of which may be None.
    """
    m = re.search(r"\brange\s*\(\s*([^)]*?)\s*\)", raw or "", re.I)
    if not m:
        return None, None
    parts = m.group(1).replace(",", " ").split()
    vals: list = []
    for tok in parts[:2]:
        try:
            vals.append(float(tok))
        except ValueError:
            vals.append(None)
    while len(vals) < 2:
        vals.append(None)
    return vals[0], vals[1]


def _report_unhandled_scale_opts(raw: str, which: str) -> None:
    """Report xscale()/yscale() sub-options dash does not implement."""
    for tok in ("noextend", "extend", "alt", "fextend", "nofextend"):
        if re.search(r"\b" + tok + r"\b", raw or "", re.I):
            warnings.warn(
                f"dash: {which}({tok}) is not implemented and is being "
                f"ignored.", UserWarning, stacklevel=3,
            )


_TEXTBOX_SUBOPTS = (
    "size", "color", "colour", "position", "pos", "span", "box", "nobox",
    "justification", "just", "alignment", "margin", "linegap", "bexpand",
    "bmargin", "fcolor", "lcolor", "lwidth", "lpattern", "orientation",
    "ring", "placement", "width", "height", "tstyle", "style",
)
_TEXTBOX_SUBOPT_RE = re.compile(
    r",\s*(?=(?:" + "|".join(_TEXTBOX_SUBOPTS) + r")\b)", re.I)


def _textbox_size(opts: dict, default: float) -> float:
    """Resolve a textbox size() sub-option to pixels.

    NOTE: the defaults passed in are literals for now.  S11 wires the general
    scheme mechanism; the scheme keys these should come from are already
    parsed.
    """
    raw = opts.get("size", "")
    if not raw:
        return default
    try:
        return float(OptionTranslator.translate_msize(raw))
    except (ValueError, TypeError):
        warnings.warn(
            f"dash: size({raw}) is not a recognised text size; ignoring it.",
            UserWarning, stacklevel=3,
        )
        return default


def _textbox_color(opts: dict, default: str) -> str:
    """Resolve a textbox color() sub-option to CSS."""
    raw = opts.get("color", "") or opts.get("colour", "")
    if not raw:
        return default
    try:
        return OptionTranslator.translate_mcolor(raw)
    except (ValueError, TypeError):
        warnings.warn(
            f"dash: color({raw}) is not a recognised colour; ignoring it.",
            UserWarning, stacklevel=3,
        )
        return default


def _parse_textbox_opt(raw: str) -> "tuple[str, dict]":
    """Split a title/subtitle/note/caption option into text and sub-options.

    The leak this fixes was a parsing defect made inconsistent by Stata's
    ``string`` vs ``string asis`` declarations: ``title()`` arrived without
    its quotes but WITH its sub-option text, so
    ``title("My Title", size(large) color(red))`` rendered the literal
    ``My Title , size(large) color(red)``; ``note()`` arrived with both, so
    ``note("n=74", span)`` rendered ``"n=74", span``, quotes and all.

    One parser handles both shapes, so they cannot diverge again.

    Args:
        raw: The raw option value.

    Returns:
        ``(text, suboptions)``.
    """
    if not raw:
        return "", {}
    text = str(raw)
    m = _TEXTBOX_SUBOPT_RE.search(text)
    tail = ""
    if m:
        tail = text[m.end():]
        text = text[:m.start()]
    text = text.strip()
    # Stata's `asis` declarations keep the quotes the user typed.  A title
    # may also be several quoted strings, one per line.
    quoted = re.findall(r'"([^"]*)"', text)
    if quoted:
        text = " ".join(quoted)
    else:
        text = text.strip('"').strip()

    opts: dict = {}
    for m2 in re.finditer(r"\b([A-Za-z_]+)\s*\(\s*([^)]*?)\s*\)", tail):
        opts[m2.group(1).lower()] = m2.group(2).strip()
    for flag in ("span", "box", "nobox"):
        if re.search(r"\b" + flag + r"\b", tail, re.I):
            opts[flag] = flag
    return text, opts


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


def _extract_finite(
    source: "ColumnDataSource", varname: str, allow_datetime: bool = False,
) -> "np.ndarray":
    """Return a float array of non-None, non-NaN values from a CDS column.

    Used by filter builders and distribution mappers to get clean numeric
    arrays from a ColumnDataSource column before computing min/max/std.

    Args:
        source:  ColumnDataSource containing the data.
        varname: Column name to extract.
        allow_datetime: When True, a datetime64 column is converted to epoch
            milliseconds -- the representation Bokeh itself transports
            datetimes in -- so slider bounds can be computed from it.  The
            default is False so no existing caller changes behaviour.

    Returns:
        1-D numpy float array with None and NaN values removed.
    """
    col = source.data.get(varname, [])
    if allow_datetime:
        series = pd.Series(col)
        if pd.api.types.is_datetime64_any_dtype(series):
            # Cast to an explicit millisecond unit first.  pandas 3 preserves
            # the resolution it inferred, so this column can be
            # datetime64[us] or [ns]; dividing a raw astype("int64") by a
            # fixed constant silently yields seconds for one and
            # milliseconds for the other.
            ms = series.dropna().astype("datetime64[ms]").astype("int64")
            return ms.to_numpy(dtype=float)
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

    # Stata's own colour table, extracted from
    # <ado>/base/style/color-<name>.style, each of which sets the colour
    # with a `set rgb "R G B"' line.  Those files are the authority: a
    # name's appearance in a Stata graph is whatever the file says.
    #
    # 52 of these 92 were wrong.  The whole gs0-gs16 ramp was -- gs10 was
    # #f0f0f0, a near-white, where Stata's is #a0a0a0, and gs14 and gs15
    # were both pure white -- so a scheme built on greys rendered as a
    # white page.  Twelve of the fifteen s2color p# colours were wrong
    # too, so the default palette of the default scheme was not Stata's.
    # The wrong values were plausible CSS colours (green was #00ff00, the
    # CSS keyword, where Stata's green is #008000), which is why they
    # never looked obviously broken.
    #
    # Regenerate with scripts/extract_color_truth.py; the fidelity check
    # is test/test_color_fidelity.py.
    _COLOR_MAP: dict[str, str] = {
        # Named colours
        "black":           "#000000",
        "blue":            "#0000ff",
        "bluishgray":      "#d9e6eb",
        "bluishgray8":     "#d2d7e4",
        "brown":           "#9c8847",
        "chocolate":       "#804000",
        "cranberry":       "#c10534",
        "cyan":            "#00ffff",
        "dimgray":         "#e8e8e8",
        "dkgreen":         "#006000",
        "dknavy":          "#1e2d53",
        "dkorange":        "#e37e00",
        "ebblue":          "#008bbc",
        "ebg":             "#c6d3df",
        "edkbg":           "#b2bfcb",
        "edkblue":         "#3e647d",
        "eggshell":        "#fffbf0",
        "eltblue":         "#82c0e9",
        "eltgreen":        "#97b6b0",
        "emerald":         "#2d6d66",
        "emidblue":        "#7b92a8",
        "erose":           "#bfa19c",
        "forest_green":    "#55752f",
        "gold":            "#ffd200",
        "gray":            "#808080",
        "green":           "#008000",
        "khaki":           "#cac27e",
        "lavender":        "#938dd2",
        "lime":            "#00ff00",
        "ltblue":          "#add8e6",
        "ltbluishgray":    "#eaf2f3",
        "ltbluishgray8":   "#e1e6f0",
        "ltkhaki":         "#e5daa5",
        "magenta":         "#ff00ff",
        "maroon":          "#90353b",
        "midblue":         "#0080ff",
        "midgreen":        "#00b000",
        "mint":            "#00ff80",
        "navy":            "#1a476f",
        "navy8":           "#273f6f",
        "none":            "#000000",
        "olive":           "#5c4717",
        "olive_teal":      "#c0dcc0",
        "orange":          "#ff7f00",
        "orange_red":      "#ff4500",
        "pink":            "#ff0080",
        "purple":          "#800080",
        "red":             "#ff0000",
        "sand":            "#d9c263",
        "sandb":           "#ffe474",
        "sienna":          "#a0522d",
        "stblue":          "#1a85ff",
        "stc1":            "#1a85ff",
        "stc10":           "#faa307",
        "stc11":           "#758bfd",
        "stc12":           "#fed9b7",
        "stc13":           "#08234c",
        "stc14":           "#f88dad",
        "stc15":           "#0f5156",
        "stc2":            "#d41159",
        "stc3":            "#00bf7f",
        "stc4":            "#ffd400",
        "stc5":            "#4f2c99",
        "stc6":            "#ff6333",
        "stc7":            "#4db7ff",
        "stc8":            "#7c0015",
        "stc9":            "#0fefaf",
        "stgreen":         "#00bf7f",
        "stone":           "#d7d29e",
        "stred":           "#d41159",
        "styellow":        "#ffd400",
        "sunflowerlime":   "#eaffaa",
        "teal":            "#6e8e84",
        "white":           "#ffffff",
        "yellow":          "#ffff00",

        # The gs0-gs16 grey ramp
        "gs0":             "#000000",
        "gs1":             "#101010",
        "gs2":             "#202020",
        "gs3":             "#303030",
        "gs4":             "#404040",
        "gs5":             "#505050",
        "gs6":             "#606060",
        "gs7":             "#707070",
        "gs8":             "#808080",
        "gs9":             "#909090",
        "gs10":            "#a0a0a0",
        "gs11":            "#b0b0b0",
        "gs12":            "#c0c0c0",
        "gs13":            "#d0d0d0",
        "gs14":            "#e0e0e0",
        "gs15":            "#f0f0f0",
        "gs16":            "#ffffff",

        # stcolor's own palette names, which the scheme file defines
        # rather than a color-*.style file.

        # An unset colour option.  Not a Stata name; kept because callers
        # resolve an empty option through this table.
        "":                "#000000",

        # British spellings, dash's own convenience.  Stata accepts only
        # the US forms, so these are aliases, not Stata names.
        "bluishgrey":      "#d9e6eb",
        "dimgrey":         "#e8e8e8",
        "grey":            "#808080",
        "ltbluishgrey":    "#eaf2f3",
    }

    # ------------------------------------------------------------------
    # Stata marker symbol → Bokeh marker string
    # ------------------------------------------------------------------
    # Stata marker names that mean "draw the outline only".  The symbol
    # itself is the solid shape; the fill is switched off when applied.
    _HOLLOW_SYMBOLS: frozenset = frozenset({
        "oh", "sh", "dh", "th", "circle_hollow", "square_hollow",
        "diamond_hollow", "triangle_hollow", "hexagon_hollow",
        "smcircle_hollow", "smsquare_hollow", "smdiamond_hollow",
        "smtriangle_hollow",
    })
    # Stata marker names that mean "draw nothing".  msymbol(i) silently drew
    # a visible marker.
    _INVISIBLE_SYMBOLS: frozenset = frozenset({"i", "none", "invisible"})

    _MARKER_MAP: dict[str, str] = {
        "i":               "circle",
        "none":            "circle",
        "invisible":       "circle",
        "circle":          "circle",
        "o":               "circle",
        # A HOLLOW Stata marker is the solid shape with no fill, not a
        # different glyph.  These mapped to Bokeh's *_dot markers, which draw
        # a filled shape with a dot in it -- so Oh, Sh and Dh all rendered
        # FILLED.  The shape is the solid one and _HOLLOW_SYMBOLS makes the
        # fill transparent.
        "circle_hollow":   "circle",
        "oh":              "circle",
        "square":          "square",
        "s":               "square",
        "square_hollow":   "square",
        "sh":              "square",
        "diamond":         "diamond",
        "d":               "diamond",
        "diamond_hollow":  "diamond",
        "dh":              "diamond",
        "triangle":        "triangle",
        "t":               "triangle",
        "triangle_hollow": "triangle",
        "th":              "triangle",
        "plus":            "plus",
        "+":               "plus",
        "x":               "x",
        "X":               "x",
        "smcircle":        "circle",
        "smcircle_hollow": "circle",
        "smx":             "x",
        "smsquare":        "square",
        "p":               "circle",
        "pipe":            "dash",
        "T":               "triangle",
        "star":            "star",
        "asterisk":        "asterisk",
        "hexagon":         "hex",
        "hexagon_hollow":  "hex",
        "point":           "circle",
        "dot":             "dot",
        # Remaining symbol-<name>.style entries from Stata's style library.
        # The mono schemes (s1mono, s2mono, sj, stmono1/2, stsj) cycle through
        # smdiamond and smtriangle, which previously raised out of SchemeParser
        # and made a faithful translation of those schemes unparseable.
        "smdiamond":          "diamond",
        "smdiamond_hollow":   "diamond",
        "smtriangle":         "triangle",
        "smtriangle_hollow":  "triangle",
        "smsquare_hollow":    "square",
        "smplus":             "plus",
        "v":                  "inverted_triangle",
        "smv":                "inverted_triangle",
        "lgx":                "x",
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
        # The remainder of Stata's line-pattern set.  Every name here has a
        # corresponding linepattern-<name>.style in Stata's style library, and
        # real schemes use them — s1rcolor and the st* family declare
        # vshortdash, which previously raised straight out of SchemeParser.
        "vshortdash":          [3, 3],
        "tight_dot":           [1, 2],
        "dash_3dot":           [8, 4, 2, 4, 2, 4, 2, 4],
        "dash_dot_dot":        [8, 4, 2, 4, 2, 4],
        "longdash_3dot":       [16, 4, 2, 4, 2, 4, 2, 4],
        "longdash_dot_dot":    [16, 4, 2, 4, 2, 4],
        "longdash_shortdash":  [16, 4, 4, 4],
        "shortdash_dot_dot":   [4, 2, 2, 2, 2, 2],
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

    # Stata's colour token meaning "draw nothing".  Its own
    # color-none.style sets rgb "0 0 0" and then says `* values should not
    # matter' -- Stata never paints it.  dash mapped the name to white, which
    # was invisible on a white background and an opaque blob everywhere else;
    # taking the style file literally would paint it black.  Neither is what
    # Stata draws, so the token is handled rather than translated.
    _NO_COLOR: frozenset = frozenset({"none"})

    @staticmethod
    def _means_no_color(value) -> bool:
        """True when a colour option asks for nothing to be drawn."""
        return str(value).strip().lower() in OptionTranslator._NO_COLOR

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

    # A `net install` may flatten a `f schemes/x.scheme` manifest line to
    # `<install dir>/x.scheme` instead of preserving the subdirectory.  Search
    # both layouts so the package works however Stata chose to place the files.
    _SCHEME_SEARCH_DIRS: "tuple[str, ...]" = (
        _SCHEMES_DIR,
        os.path.dirname(os.path.abspath(__file__)),
    )

    # The translated StataCorp schemes dash ships.  Each is a faithful
    # translation of the same-named Stata scheme, generated from
    # test/fixtures/scheme_truth.json by scripts/extract_scheme_truth.py.
    # Section 11 restricts scheme()/theme() to exactly this set.
    _BUILTIN_NAMES: frozenset[str] = frozenset({
        # Stata 18+ family (stcolor is Stata's default since v18)
        "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
        # legacy defaults (s2color was the default from v10 to v17)
        "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
        # journal styles
        "economist", "sj",
    })

    # Last-resort properties for when NO scheme file can be resolved at all —
    # e.g. an install whose scheme files did not ship.  Mirrors s2color so the
    # output stays recognisable.  Without this, the fallback path re-ran the
    # same failing lookup and raised, so every render on such an install ended
    # in a traceback.  Names here must exist in OptionTranslator._COLOR_MAP.
    _FALLBACK_PROPS: "dict[str, str]" = {
        "color background": "ltbluishgray",
        "color plotregion": "white",
        "color legend":     "white",
        "color legend_line": "black",
        "color major_grid": "ltbluishgray",
        "color minor_grid": "gs5",
        "color heading":    "dknavy",
        "color axisline":   "black",
        "color p1":  "navy",         "color p2":  "maroon",
        "color p3":  "forest_green", "color p4":  "dkorange",
        "color p5":  "teal",         "color p6":  "cranberry",
        "color p7":  "lavender",     "color p8":  "khaki",
        "color p9":  "sienna",       "color p10": "emidblue",
        "color p11": "emerald",      "color p12": "brown",
        "color p13": "erose",        "color p14": "gold",
        "color p15": "bluishgray",
    }

    @classmethod
    def fallback(cls) -> "SchemeParser":
        """Return a usable scheme without reading any file.

        Used only when scheme resolution has already failed — this must never
        raise, because it is the last line of defence before a render aborts.
        """
        inst = cls.__new__(cls)
        inst._props = dict(cls._FALLBACK_PROPS)
        # _FALLBACK_PROPS mirrors s2color, so that is what this renders as;
        # is_fallback records that no file was read, which the name alone
        # cannot express.
        inst.name = "s2color"
        inst.is_fallback = True
        inst._init_properties()
        return inst

    @classmethod
    def resolve_or_fallback(cls, name: str, context: str) -> "SchemeParser":
        """Build a SchemeParser for *name*, degrading instead of raising.

        Tries *name*, then the package default, then an in-memory fallback.
        Emits a UserWarning naming the directories searched when it has to
        fall all the way back, since that means the install is incomplete.
        """

        for idx, candidate in enumerate((name, "s2color")):
            if not candidate:
                continue
            try:
                return cls(candidate)
            except (ValueError, OSError) as exc:
                if idx == 0:
                    # Stata returns rc 0 here and prints
                    #   note: scheme X not found, using s2color
                    # so dash does not abort either -- but it must not be
                    # silent, or scheme(typo) renders s2color and looks
                    # like the scheme was applied.
                    warnings.warn(
                        f"dash: scheme {candidate!r} was not found for "
                        f"{context}; using s2color. Supported schemes: "
                        f"{', '.join(sorted(cls._BUILTIN_NAMES))}. "
                        f"({exc})",
                        UserWarning,
                        stacklevel=3,
                    )
                continue
        warnings.warn(
            f"dash: no scheme file could be resolved for {context} (searched "
            f"{', '.join(cls._SCHEME_SEARCH_DIRS)}). Falling back to built-in "
            "defaults. The package's schemes/ directory appears to be missing "
            "— reinstall dash or run dash_setup.",
            UserWarning,
            stacklevel=3,
        )
        return cls.fallback()

    # Stata gsize keyword -> CSS pt string.
    #
    # These are Stata's OWN numbers, read from /Applications/StataNow/ado/
    # base/style/gsize-<name>.style, each of which states its point size in a
    # comment ("* 8 pt based on a 4 inch high graph") beside the relative
    # value it sets.  Six of the previous fourteen entries disagreed with
    # them -- tiny was 7pt against Stata's 4, vsmall 8 against 6, small 9
    # against 8, large 13 against 14, vlarge 15 against 16, huge 18 against
    # 20 -- so a scheme asking for small text got a size Stata never
    # specifies.
    _GSIZE_PT: dict[str, str] = {
        "zero":        "0pt",
        "minuscule":   "2pt",    # relative 0.6944
        "quarter_tiny": "1pt",   # relative 0.3472
        "third_tiny":  "1pt",    # relative 0.4630
        "half_tiny":   "2pt",    # relative 0.6944
        "tiny":        "4pt",
        "vsmall":      "6pt",
        "small":       "8pt",
        "medsmall":    "10pt",
        "medium":      "11pt",
        "medlarge":    "12pt",
        "large":       "14pt",
        "vlarge":      "16pt",
        "huge":        "20pt",
        "vhuge":       "24pt",
        "ehuge":       "32pt",
    }

    # Marker diameter in Bokeh screen pixels for each Stata markersize
    # keyword.  The RATIOS are Stata's, from _GSIZE_PT above; the anchor is
    # dash's own -- medium, which is what s2color asks for, keeps the size
    # dash has always drawn, so the default dashboard is unchanged and a
    # scheme that asks for something else now gets something else.  Stata
    # sizes a marker relative to a 4-inch-high graph, which no browser has,
    # so a claim of absolute pixel fidelity here would be a fabrication.
    _MARKER_PX_ANCHOR: float = 8.0
    _MARKER_PX_ANCHOR_PT: float = 11.0

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
        # Which scheme this actually is.  Callers had no way to ask, so
        # nothing could check that scheme() had been honoured, and a silent
        # fallback was indistinguishable from a successful resolution.
        self.name: str = os.path.splitext(os.path.basename(path))[0]
        self.is_fallback: bool = False
        self._init_properties()

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _resolve_path(self, name: str) -> str:
        """Return absolute path for a scheme name, blocking path traversal."""
        is_file_ref = name.endswith(".scheme") or os.sep in name or "/" in name

        search_dirs = list(self._SCHEME_SEARCH_DIRS)

        if is_file_ref:
            # Try CWD first, then each scheme search dir
            candidates = [os.path.abspath(os.path.join(os.getcwd(), name))]
            candidates += [
                os.path.abspath(os.path.join(d, name)) for d in search_dirs
            ]
        else:
            candidates = [
                os.path.abspath(os.path.join(d, name + ".scheme"))
                for d in search_dirs
            ]

        # Security: a resolved path must lie within an allowed directory.
        # Loop-invariant, so computed once.
        allowed = [os.path.abspath(d) for d in search_dirs]
        allowed.append(os.path.abspath(os.getcwd()))

        for candidate in candidates:
            in_allowed = any(
                candidate.startswith(d + os.sep) or candidate == d
                for d in allowed
            )
            if not in_allowed:
                raise ValueError(
                    f"dash scheme: path '{name}' resolves outside allowed "
                    "directories (CWD or the dash schemes/ folder)."
                )
            # Security: also validate the *realpath* so that symlinks pointing
            # outside allowed directories are rejected.  Without this check a
            # symlink placed in the CWD (e.g. evil.scheme -> /etc/passwd) would
            # pass the abspath boundary check above and silently read the target.
            real_candidate = os.path.realpath(candidate)
            real_allowed = [os.path.realpath(d) for d in allowed]
            real_in_allowed = any(
                real_candidate.startswith(rd + os.sep) or real_candidate == rd
                for rd in real_allowed
            )
            if not real_in_allowed:
                raise ValueError(
                    f"dash scheme: path '{name}' resolves via symlink outside "
                    "allowed directories (CWD or the dash schemes/ folder). "
                    "Symlinks pointing to external paths are not permitted."
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
        """Translate a raw scheme colour to hex, degrading loudly if it cannot.

        An ABSENT key falls back silently — that is ordinary inheritance, and
        every scheme leaves most keys unset.  But a key that is PRESENT and
        unresolvable is a defect in the scheme or in the colour table, and must
        say so: silently returning the default here is what made the whole
        stcolor scheme render every series black, because `color p1 stc1` could
        not be resolved and nothing reported it.
        """
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        try:
            return OptionTranslator.translate_mcolor(raw)
        except ValueError:
            warnings.warn(
                f"dash scheme: colour '{raw}' (from '{key}') is not a colour "
                f"dash recognises; falling back to {default}. The rendered "
                "colour will not match Stata's.",
                UserWarning,
                stacklevel=3,
            )
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
        """Translate a scheme line pattern, degrading loudly rather than raising.

        A scheme declaring a pattern dash cannot express must not abort the
        whole render — but it must not vanish silently either, which is the
        failure mode that let an unresolvable colour turn every series black.
        """
        raw = self._props.get(key, "solid").strip().lower()
        try:
            return OptionTranslator.translate_lpattern(raw)
        except ValueError:
            warnings.warn(
                f"dash scheme: line pattern '{raw}' (from '{key}') is not "
                "recognised; falling back to solid.",
                UserWarning,
                stacklevel=3,
            )
            return []

    def _lpattern_chain(self, keys: "tuple[str, ...]") -> list:
        """Resolve a line pattern through Stata's own fallback chain.

        The first key that is actually PRESENT wins, even when its value is
        ``solid``: a declared solid translates to an empty dash list, so a
        truthiness test would treat it as absent and fall through to a
        dashed entry further down the chain.

        Args:
            keys: Scheme keys in Stata's resolution order, most specific
                  first.

        Returns:
            A Bokeh dash list; empty means solid.
        """
        for key in keys:
            if self._props.get(key, "").strip():
                return self._lpattern(key)
        return []

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

    def _float(self, key: str, default: "float | None") -> "float | None":
        """Return a scheme value as a float, or *default* if absent/unparseable."""
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    def _yesno(self, key: str, default: bool) -> bool:
        """Return a Stata `yesno` scheme directive as a bool."""
        raw = self._props.get(key, "").strip().lower()
        if raw in ("yes", "y", "1", "true", "on"):
            return True
        if raw in ("no", "n", "0", "false", "off"):
            return False
        return default

    def _int(self, key: str, default: "int | None") -> "int | None":
        """Return a scheme value as an int, or *default* if absent/unparseable."""
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        try:
            return int(float(raw))
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

        # Line pattern cycles.  These are two DIFFERENT stubs, not a
        # preference order.
        #
        # Stata resolves a plain `twoway line' through
        #   linepattern p#lineplot -> plineplot -> p# -> p
        # (style/seriesstyle-p#line.style -> style/linestyle-p#line.style,
        # and scheme_line_plots.sthlp), while `linepattern p#line' belongs to
        # style/linestyle-p#.style, the CONNECTING line of twoway connected.
        # Reading p#line for a line plot made three overlaid lines under
        # s2mono all solid where Stata draws solid / dash / vshortdash.
        #
        # Falling back from p#lineplot to p#line would be just as wrong in
        # the other direction: s1mono and stmono1 declare a varied p#line
        # cycle and no lineplot key at all, and Stata draws their line plots
        # solid.  So the fallback follows Stata's own chain and stops at the
        # shared `linepattern p'.
        #
        # `declared' rather than truthiness, because a DECLARED solid is an
        # empty dash list and is indistinguishable from an absent key by
        # truth value -- scheme-s2gmanual declares `p#lineplot solid' over a
        # dashed p#line, which a truthiness test would silently misrender.
        self.p_lineplot_patterns: list = [
            self._lpattern_chain(
                (f"linepattern p{i}lineplot", "linepattern plineplot",
                 f"linepattern p{i}", "linepattern p"))
            for i in range(1, 16)
        ]
        # Kept under its historical name for the connected-plot path and for
        # the scheme fixture, which still means p#line by it.
        self.p_line_patterns: list = [
            self._lpattern(f"linepattern p{i}line") for i in range(1, 16)
        ]
        # Colour of a plain line plot: `color p#lineplot' where the scheme
        # declares it, `color p#' otherwise -- NOT `color p#line'.  s1mono
        # declares `color p#line black'; Stata draws #606060 / #a0a0a0 /
        # #808080 for three overlaid line charts, and dash drew three
        # identical black lines.
        self.p_lineplot_colors: list[str] = [
            self._color(f"color p{i}lineplot",
                        self._color("color plineplot", self.p_colors[i - 1]))
            for i in range(1, 16)
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

        # Graph dimensions, in inches, as Stata schemes declare them.
        # Parsed here only; section 10 consumes them for figure proportions.
        # `graphsize x`/`graphsize y` override a bare `graphsize`, matching
        # Stata, which treats the bare form as a square default.
        _gs_both = self._float("graphsize", None)
        self.graphsize_x: "float | None" = self._float("graphsize x", _gs_both)
        self.graphsize_y: "float | None" = self._float("graphsize y", _gs_both)

        # Grid visibility.
        #
        # A Stata grid belongs to an AXIS, and the key is named for that
        # axis's orientation, not for the direction of the lines:
        #   style/axisstyle-horizontal_default.style:18
        #       set draw_major_grid    scheme draw_major_hgrid
        #   style/axisstyle-vertical_default.style:18
        #       set draw_major_grid    scheme draw_major_vgrid
        # The horizontal axis is x, and its major grid lines are the VERTICAL
        # ones at the x ticks; the vertical axis is y, and its lines are
        # HORIZONTAL.  The comment that used to sit here had it backwards.
        #
        # The y-axis flag came from `yesno draw_major_grid', which is DEAD at
        # scheme level -- grep "scheme draw_major_grid" over Stata's
        # style/ directory returns nothing.  Every scheme declares it `no',
        # so the flag read False everywhere and looked plausible, while
        # Stata's real answer for ten of the fourteen is `yes'.
        self.draw_major_hgrid: bool = self._yesno("yesno draw_major_hgrid", False)
        self.draw_major_vgrid: bool = self._yesno("yesno draw_major_vgrid", False)

        # Default marker size for the p cycle, and legend placement.
        # Parsed only; consumers land in sections 10 and 11.
        self.symbolsize: str = self._props.get("symbolsize p", "").strip()
        # ...and the size the renderer actually draws.  Parsed but never
        # consumed: every scheme drew an 8px marker, so stcolor's `small'
        # and economist's `large' were indistinguishable.
        self.marker_size: float = self._markersize_px(self.symbolsize)
        # Stata's clockdir is a numeric clock position (1-12), so expose it as
        # a number rather than the raw string — consumers compare it as one.
        self.legend_position: "int | None" = self._int(
            "clockdir legend_position", None)
        self.legend_cols: "int | None" = self._int("numstyle legend_cols", None)

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
        # `color p#line' is the CONNECTING line of twoway connected.  A plain
        # line plot reads `color p#lineplot', falling back to `color p#'.
        if plot_type in {"line", "tsline", "tsrline", "mspline", "mband",
                         "rline"}:
            return self.p_lineplot_colors[idx]
        if plot_type in {"connected", "rconnected"}:
            return self.p_line_colors[idx]
        if plot_type in {"bar", "rbar", "area", "rarea", "histogram"}:
            return self.p_bar_colors[idx]
        return self.p_colors[idx]

    def _markersize_px(self, keyword: str) -> float:
        """Convert a Stata markersize keyword to Bokeh screen pixels.

        Args:
            keyword: The scheme's ``symbolsize p`` value, e.g. ``"medium"``.
                     A bare number is taken as points.

        Returns:
            A diameter in pixels; the anchor is dash's own 8px at Stata's
            ``medium``, and everything else keeps Stata's ratio to it.
        """
        kw = (keyword or "").strip().lower()
        if not kw:
            return self._MARKER_PX_ANCHOR
        pt_str = self._GSIZE_PT.get(kw, "")
        if not pt_str:
            try:
                pt = float(kw.lstrip("*"))
            except ValueError:
                return self._MARKER_PX_ANCHOR
        else:
            pt = float(pt_str[:-2])
        px = self._MARKER_PX_ANCHOR * pt / self._MARKER_PX_ANCHOR_PT
        # A zero-size marker is invisible, which is a legitimate request; a
        # negative one is not expressible.
        return max(0.0, px)

    def default_symbol(self, index: int) -> str:
        """Return the Bokeh marker string for the plot at *index*."""
        return self.p_symbols[index % 15]

    def default_line_pattern(self, index: int) -> list:
        """Return the Bokeh dash list for the line plot at *index*."""
        return self.p_lineplot_patterns[index % 15]

    def default_connect_pattern(self, index: int) -> list:
        """Return the dash list for a connected plot's connecting line."""
        return self.p_line_patterns[index % 15]

    def default_marker_size(self, index: int = 0) -> float:
        """Return the marker diameter in pixels for the plot at *index*."""
        return self.marker_size

    def apply_to_figure(self, fig: Any) -> None:
        """Apply scheme defaults to *fig*.

        Called before explicit graph_opts so that explicit options override.
        """
        fig.background_fill_color = self.plotregion_color
        fig.border_fill_color = self.background_color
        if self.axis_line_color:
            fig.outline_line_color = self.axis_line_color

        # Per axis, because the scheme decides each one separately.  This
        # loop used to colour every grid unconditionally, and Bokeh draws
        # both by default, so dash drew a grid Stata does not draw in ten of
        # the fourteen shipped schemes -- BOTH grids under s1color, s1mono,
        # s1rcolor and stmono1, which draw none at all.
        #
        # `grid_line_color = None' is how the rest of the file expresses "no
        # grid" (see the xlabel(, nogrid) path), so an explicit nogrid and a
        # scheme-level no stay indistinguishable, which is what lets an
        # explicit option override the scheme without special-casing.
        for grids, draw in ((fig.xgrid, self.draw_major_hgrid),
                            (fig.ygrid, self.draw_major_vgrid)):
            for grid in grids:
                grid.grid_line_color = self.grid_color if draw else None
                grid.grid_line_width = self.grid_line_width
                # `color minor_grid' was parsed and never read; Bokeh draws
                # no minor grid by default, so the scheme's choice never
                # appeared.
                grid.minor_grid_line_color = self.minor_grid_color

        for axis in list(fig.xaxis) + list(fig.yaxis):
            axis.axis_line_color = self.axis_line_color
            axis.axis_label_text_font_size = self.axis_title_font_size
            axis.major_label_text_font_size = self.tick_label_font_size

    def css_block(self) -> str:
        """Return the scheme's CSS rules for the dashboard outer chrome.

        Rules only -- no ``<style>`` wrapper.  It used to return its own,
        and the Bootstrap head embeds the result inside another ``<style>``;
        measured, the Bootstrap output carried six ``<style>`` tokens with
        one nested open, and CSS error recovery discarded the rule that
        followed it.  ``css_style_element()`` adds the wrapper for the one
        caller that needs a complete element.

        The selectors are the classes the dashboard actually emits.  They
        used to be ``.dash-title``, ``.dash-subtitle`` and ``.kpi-card``
        while the HTML emitted ``db-title``, ``db-subtitle`` and an
        unclassed KPI div, so all three matched nothing and the block was
        inert even where it was not nested.
        """
        bg = html.escape(self.background_color)
        tc = html.escape(self.title_color)
        hs = html.escape(self.heading_font_size)
        ts = html.escape(self.text_font_size)
        lbg = html.escape(self.legend_bg_color)
        lbc = html.escape(self.legend_border_color)
        return (
            f"  body {{ background-color: {bg}; }}\n"
            f"  .db-title {{ color: {tc}; font-size: {hs}; }}\n"
            f"  .db-subtitle {{ color: {tc}; font-size: {ts}; }}\n"
            f"  .db-kpi-card {{ background-color: {lbg}; "
            f"border-color: {lbc}; }}\n"
        )

    def css_style_element(self) -> str:
        """Return :meth:`css_block` wrapped in a complete ``<style>``."""
        return f"<style>\n{self.css_block()}</style>\n"


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


def _md_span(span: int) -> int:
    """The medium-breakpoint span for a cell whose large-breakpoint span is *span*.

    A tablet is not a wide display: four columns that work at 1440px are
    cramped at 768px, so anything narrower than a half width doubles up.

    Args:
        span: The 12-column span used at the large breakpoint.

    Returns:
        The span to use at the medium breakpoint.
    """
    if span <= 3:
        return 6
    if span <= 4:
        return 6
    return span


def _cell_height_class(span: int) -> str:
    """A height class keyed to a cell's span.

    Every Bootstrap cell used to get the same height, so a col-4 cell was as
    tall as a col-12 one and the narrow one looked stretched.  Height follows
    width so cells keep a sensible shape.

    Args:
        span: The cell's 12-column span.

    Returns:
        The class suffix.
    """
    if span >= 12:
        return "lg"
    if span >= 6:
        return "md"
    return "sm"


def _source_frame(source, fallback: "pd.DataFrame") -> "pd.DataFrame":
    """Return the rows a figure is actually drawing, as a DataFrame.

    Args:
        source:   The figure's ColumnDataSource.
        fallback: Used when the source has no usable data.

    Returns:
        A DataFrame view of the source.
    """
    try:
        data = dict(source.data)
    except (AttributeError, TypeError):
        return fallback
    if not data:
        return fallback
    try:
        return pd.DataFrame(data)
    except (ValueError, TypeError):
        return fallback


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
        # Defer scheme import to avoid circular dependency; default to s2color.
        # Must not raise: on an install missing schemes/ this is reached before
        # any user-facing error handling exists.
        if scheme is None:
            self.scheme: "SchemeParser" = SchemeParser.resolve_or_fallback(
                "s2color", "the glyph mapper",
            )
        else:
            self.scheme = scheme
        # Stata label metadata, populated by DashRenderer after _load_data().
        # Used by _apply_colorvar to render value labels in legends and by
        # other consumers that need human-readable variable display names.
        self.variable_labels: dict[str, str]              = {}
        self.value_labels:    dict[str, dict[str, str]]   = {}
        self.value_label_names: dict[str, str]            = {}

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
            line_color=color, line_width=self.scheme.default_line_width, legend_label=yvar,
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
        n_boot: int = _N_BOOT_DEFAULT,
        seed: int = 42,
        fallback: "np.ndarray | None" = None,
        level: float = _DEFAULT_LEVEL,
    ) -> "tuple[np.ndarray, np.ndarray]":
        """Compute a bootstrap confidence interval for a smooth fit.

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
            level:    Confidence level in percent, e.g. 95.
            fallback: Array of length ``len(x_grid)`` used when *fit_fn*
                      fails or returns NaN predictions for a resample.
                      Defaults to zeros when ``None``.

        Returns:
            ``(y_lower, y_upper)`` arrays of length ``len(x_grid)``
            representing the (100-level)/2 and 100-(100-level)/2 percentiles of the
            bootstrap distribution.
        """
        n_grid = len(x_grid)
        _fb = fallback if fallback is not None else np.zeros(n_grid)
        _tail = (100.0 - float(level)) / 2.0
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
            np.percentile(boot_preds, _tail, axis=0),
            np.percentile(boot_preds, 100.0 - _tail, axis=0),
        )

    def _apply_line_opts(
        self,
        renderer: Any,
        options: dict[str, str],
    ) -> None:
        """Apply lcolor/lwidth/lpattern/lalpha options to a line-type glyph renderer."""
        glyph = renderer.glyph
        if "lcolor" in options:
            if OptionTranslator._means_no_color(options["lcolor"]):
                # Stata draws nothing; this used to resolve through the
                # colour table and paint a line.
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["lcolor"])
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
            if OptionTranslator._means_no_color(options["mcolor"]):
                # Stata draws nothing.  fcolor(none) was already handled;
                # mcolor(none) resolved through the colour table instead.
                for _attr in ("fill_alpha", "line_alpha"):
                    if hasattr(glyph, _attr):
                        setattr(glyph, _attr, 0.0)
            else:
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
            if OptionTranslator._means_no_color(options["mfcolor"]):
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["mfcolor"])
                    if color:
                        glyph.fill_color = color
                    if alpha is not None and hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = alpha
                except (ValueError, AttributeError):
                    pass
        # lcolor sets the marker border (outline) color independently of fill.
        if "lcolor" in options:
            if OptionTranslator._means_no_color(options["lcolor"]):
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["lcolor"])
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
        # mlcolor()/mlwidth() are the marker's OWN border options.  The
        # border used to be taken from lcolor(), the CONNECTING LINE colour,
        # which is wrong in both directions: mlcolor() did nothing and
        # lcolor() restyled the marker.  Applied after lcolor so they win.
        if "mlcolor" in options:
            raw_mlc = str(options["mlcolor"]).strip().lower()
            if raw_mlc == "none":
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(options["mlcolor"])
                    if color and hasattr(glyph, "line_color"):
                        glyph.line_color = color
                    if alpha is not None and hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = alpha
                except (ValueError, AttributeError):
                    warnings.warn(
                        f"dash: mlcolor({options['mlcolor']}) is not a "
                        f"recognised colour; ignoring it.", UserWarning,
                    )
        if "mlwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["mlwidth"])
            except (ValueError, AttributeError):
                warnings.warn(
                    f"dash: mlwidth({options['mlwidth']}) is not a recognised "
                    f"line width; ignoring it.", UserWarning,
                )
        # fcolor(none)/mfcolor(none) mean TRANSPARENT.  "none" resolved to
        # #ffffff, which paints an opaque white blob over whatever is behind.
        for _fk in ("mfcolor", "fcolor"):
            if str(options.get(_fk, "")).strip().lower() == "none":
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = 0.0
        # Hollow and invisible symbols, applied last so an explicit alpha
        # cannot resurrect them.
        _sym_raw = str(options.get("msymbol", options.get("marker", ""))
                       ).strip().lower()
        if _sym_raw in OptionTranslator._HOLLOW_SYMBOLS:
            if hasattr(glyph, "fill_alpha"):
                glyph.fill_alpha = 0.0
        elif _sym_raw in OptionTranslator._INVISIBLE_SYMBOLS:
            if hasattr(glyph, "fill_alpha"):
                glyph.fill_alpha = 0.0
            if hasattr(glyph, "line_alpha"):
                glyph.line_alpha = 0.0
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
            if str(options["fcolor"]).strip().lower() == "none":
                # Stata's fcolor(none) is TRANSPARENT.  It resolved to
                # #ffffff, painting an opaque white blob.
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(options["fcolor"])
                    if color:
                        glyph.fill_color = color
                    if alpha is not None and hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = alpha
                except (ValueError, AttributeError):
                    pass
        # falpha()/fa() -- used nine times in examples/comprehensive_demo.do
        # and never read.
        for _ak in ("falpha", "fa"):
            if _ak in options:
                _fa = _stat_option_float(options, _ak, None, "fill",
                                         lo=0.0, hi=100.0)
                if _fa is not None and hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = _fa / 100.0
                break
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

        Supports Stata 18 colorvar_options:
            colorvar(varname)   — variable whose values drive the color mapping
            colordiscrete       — treat a numeric variable as discrete categories
            coloruseplegend     — add a plot legend instead of a ColorBar
            colornlevels(#)     — quantize continuous data into # equal-width levels
            colorcuts(numlist)  — custom cut-point boundaries for continuous data
            colormissing(color) — Bokeh color for missing/NaN values (default: grey)
            colpalette(name)    — palette name; see _PALETTE_MAP for supported keys

        Numeric columns default to a LinearColorMapper (viridis palette).
        String columns, or numeric columns with colordiscrete / colornlevels /
        colorcuts, use a CategoricalColorMapper (category10 palette).
        """
        varname = options.get("colorvar", "").strip()
        if not varname or varname not in source.data:
            return

        # Security: validate varname is a safe Stata identifier
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname):
            return

        from bokeh.models import (
            LinearColorMapper, CategoricalColorMapper, ColorBar,
            Legend, LegendItem,
        )
        from bokeh import palettes as _bk_palettes

        raw_col       = source.data[varname]
        palette_key   = options.get("colpalette", "").strip().lower()
        force_discrete = bool(options.get("colordiscrete"))
        # coloruseplegend is accepted for Stata 18 compatibility but is now
        # redundant for discrete mappings — discrete always renders a Legend.
        # The variable kept here for clarity / future use.
        _use_plegend  = bool(options.get("coloruseplegend"))  # noqa: F841
        # colormissing() went to Bokeh untranslated, so any Stata colour
        # name Bokeh does not happen to share -- eltblue, ltbluishgray, the
        # whole Stata palette -- raised out of the mapper and took the entire
        # render down with it.
        _raw_missing = options.get("colormissing", "").strip()
        missing_color = "#808080"
        if _raw_missing:
            try:
                missing_color = self.tr.translate_mcolor(_raw_missing)
            except (ValueError, TypeError):
                warnings.warn(
                    f"dash: colormissing({_raw_missing}) is not a recognised "
                    f"colour; using grey.", UserWarning,
                )

        # Stata label metadata, populated by DashRenderer after _load_data().
        # Used to render value labels on legend entries and to display the
        # variable label as the legend/colorbar title.
        var_display = self.variable_labels.get(varname, "") or varname
        labelset    = self.value_label_names.get(varname, "")
        vlabels     = self.value_labels.get(labelset, {}) if labelset else {}
        if not vlabels:
            _candidate = self.value_labels.get(varname, {})
            if isinstance(_candidate, dict):
                vlabels = _candidate

        def _vlookup(v: float) -> str:
            """Return the Stata value label for v if defined, else numeric str.

            Stata value labels are keyed on the integer code as a string
            (e.g. "0" → "Domestic"); fall back to a generic numeric repr.
            """
            try:
                if float(v).is_integer():
                    key = str(int(v))
                else:
                    key = f"{v:g}"
            except (TypeError, ValueError):
                key = str(v)
            return vlabels.get(key, f"{v:g}")

        # Parse colornlevels (must be an integer >= 2)
        nlevels = None
        try:
            nlevels = int((options.get("colornlevels") or "").strip())
            nlevels = max(2, nlevels)
        except (ValueError, TypeError):
            nlevels = None

        # Parse colorcuts (space-separated numlist → sorted float list)
        cuts = None
        cuts_str = (options.get("colorcuts") or "").strip()
        if cuts_str:
            try:
                cuts = sorted(float(x) for x in cuts_str.split())
            except ValueError:
                cuts = None

        # Determine whether the column is numeric
        try:
            col_vals = np.array(raw_col, dtype=float)
            is_numeric = not np.all(np.isnan(col_vals))
        except (ValueError, TypeError):
            is_numeric = False
            col_vals = None

        needs_binning = cuts is not None or nlevels is not None
        use_discrete  = force_discrete or not is_numeric or needs_binning

        # ------------------------------------------------------------------
        # DISCRETE path — CategoricalColorMapper
        # ------------------------------------------------------------------
        if use_discrete:
            color_field = varname  # overridden for derived bin columns

            if is_numeric and (force_discrete or needs_binning):
                color_field = f"_cvar_{varname}_bin"

                if cuts is not None:
                    # User-supplied boundaries: bins are (-∞, c0], (c0, c1], …, (cN, +∞)
                    n_bins = len(cuts) + 1
                    labels = []
                    for i in range(n_bins):
                        lo_b = cuts[i - 1] if i > 0 else None
                        hi_b = cuts[i]     if i < len(cuts) else None
                        if lo_b is None:
                            labels.append(f"\u2264{hi_b:g}")
                        elif hi_b is None:
                            labels.append(f">{lo_b:g}")
                        else:
                            labels.append(f"{lo_b:g}\u2013{hi_b:g}")

                    def _assign_cut(v: float) -> str:
                        if np.isnan(v):
                            return "__missing__"
                        idx = int(np.searchsorted(cuts, v, side="left"))
                        return labels[min(idx, n_bins - 1)]

                    binned = [_assign_cut(v) for v in col_vals]

                elif nlevels is not None:
                    # Equal-width quantization into nlevels bins
                    lo_v = float(np.nanmin(col_vals))
                    hi_v = float(np.nanmax(col_vals))
                    if lo_v == hi_v:
                        hi_v = lo_v + 1.0
                    edges  = np.linspace(lo_v, hi_v, nlevels + 1)
                    labels = [f"{edges[i]:g}\u2013{edges[i + 1]:g}"
                              for i in range(nlevels)]
                    inner  = edges[1:-1]  # interior boundaries for searchsorted

                    def _assign_nlev(v: float) -> str:
                        if np.isnan(v):
                            return "__missing__"
                        idx = int(np.searchsorted(inner, v, side="left"))
                        return labels[min(idx, nlevels - 1)]

                    binned = [_assign_nlev(v) for v in col_vals]

                else:
                    # colordiscrete: each distinct numeric value → its own category.
                    # Resolve the Stata value label for each level so the legend
                    # shows e.g. "Domestic"/"Foreign" instead of "0"/"1".
                    non_nan = [v for v in col_vals if not np.isnan(v)]
                    unique_sorted = sorted(set(non_nan))
                    val_label = {v: _vlookup(v) for v in unique_sorted}
                    labels = [val_label[v] for v in unique_sorted]
                    binned = [
                        "__missing__" if np.isnan(v) else val_label[v]
                        for v in col_vals
                    ]

                has_missing = any(b == "__missing__" for b in binned)
                source.data[color_field] = binned
                factors = labels + (["__missing__"] if has_missing else [])

            else:
                # Already categorical (string / object column)
                factors = sorted(
                    str(v) for v in raw_col
                    if v is not None and str(v) != "nan"
                )
                source.data[varname] = [str(v) for v in raw_col]
                has_missing = False

            if not factors:
                return

            non_missing_factors = [f for f in factors if f != "__missing__"]
            # With no explicit palette(), the discrete colours are the
            # scheme's own p1-p15 cycle -- the same colours the scheme gives
            # overlaid series.  Bokeh's Category10 was used unconditionally,
            # so `scatter mpg weight, colorvar(rep78) colordiscrete' drew
            # Bokeh's blue/orange/green on an economist or mono dashboard.
            if not palette_key and getattr(self.scheme, "p_colors", None):
                pal_list = list(self.scheme.p_colors)
            else:
                pal_name = self._PALETTE_MAP.get(palette_key or "category10",
                                                 "Category10_10")
                pal_list = list(getattr(_bk_palettes, pal_name,
                                        _bk_palettes.Category10_10))
            while len(pal_list) < len(non_missing_factors):
                pal_list += pal_list
            pal_colors = pal_list[:len(non_missing_factors)]
            if "__missing__" in factors:
                pal_colors = pal_colors + [missing_color]

            mapper     = CategoricalColorMapper(factors=factors, palette=pal_colors)
            color_spec = {"field": color_field, "transform": mapper}
            glyph      = renderer.glyph
            try:
                glyph.fill_color = color_spec
                glyph.line_color = color_spec
            except (AttributeError, ValueError):
                pass

            # Discrete mappings always render as a Bokeh Legend with one entry
            # per category — matches Stata 18's default colordiscrete behavior
            # ("color legend" with discrete swatches) and ensures users can
            # identify the colored categories by name. Dummy invisible
            # renderers carry the per-factor color into the legend item.
            legend_items = []
            for factor, color in zip(non_missing_factors,
                                     pal_colors[:len(non_missing_factors)]):
                _r = fig.scatter(
                    x=[float("nan")], y=[float("nan")],
                    color=color, size=0,
                    visible=False, name=f"_clegend_{factor}",
                )
                legend_items.append(LegendItem(label=factor, renderers=[_r]))
            if "__missing__" in factors:
                _rm = fig.scatter(
                    x=[float("nan")], y=[float("nan")],
                    color=missing_color, size=0,
                    visible=False, name="_clegend___missing__",
                )
                legend_items.append(LegendItem(label="(missing)", renderers=[_rm]))
            # Tagged, so _rebuild_legend can tell a colour key from a plot
            # legend.  Inspecting the items instead does not survive the
            # rewrite it has to survive, and gets the mixed case (a colorvar
            # plot and a plain plot in one figure) wrong.
            fig.add_layout(
                Legend(items=legend_items, title=html.escape(var_display),
                       name=_COLORVAR_LEGEND_NAME),
                "right",
            )

        # ------------------------------------------------------------------
        # CONTINUOUS path — LinearColorMapper
        # ------------------------------------------------------------------
        else:
            lo = float(np.nanmin(col_vals))
            hi = float(np.nanmax(col_vals))
            if lo == hi:
                hi = lo + 1.0
            pal_name = self._PALETTE_MAP.get(palette_key or "viridis", "Viridis256")
            palette  = getattr(_bk_palettes, pal_name, _bk_palettes.Viridis256)
            mapper   = LinearColorMapper(palette=palette, low=lo, high=hi,
                                         nan_color=missing_color)
            color_spec = {"field": varname, "transform": mapper}
            glyph      = renderer.glyph
            try:
                glyph.fill_color = color_spec
                glyph.line_color = color_spec
            except (AttributeError, ValueError):
                pass

            try:
                fig.add_layout(
                    ColorBar(color_mapper=mapper, label_standoff=8,
                             width=12, location=(0, 0),
                             title=html.escape(var_display)),
                    "right",
                )
            except (ValueError, TypeError, KeyError) as _exc:  # noqa: BLE001
                warnings.warn(f"dash: color bar skipped — {_exc}", stacklevel=2)

        # ------------------------------------------------------------------
        # Strip the auto-generated `legend_label=yvar` item for *renderer*
        # from any pre-existing Legend on the figure.
        #
        # When colorvar is applied, the colorvar Legend (or ColorBar) on the
        # right is the canonical color identifier; the in-plot "mpg" item
        # added by `fig.scatter(..., legend_label=yvar)` becomes redundant
        # and visually clutters the plot area.
        #
        # The colorvar Legend we just added uses dummy invisible scatter
        # renderers, so filtering on `renderer` (the original glyph) does
        # not touch the colorvar Legend's own items.
        # ------------------------------------------------------------------
        for _slot in (fig.right, fig.left, fig.above, fig.below, fig.center):
            for _lay in list(_slot):
                if isinstance(_lay, Legend):
                    _lay.items = [
                        it for it in _lay.items
                        if renderer not in list(it.renderers or [])
                    ]
                    if not _lay.items:
                        try:
                            _slot.remove(_lay)
                        except ValueError:
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

        # mlabel(datevar) labelled points with the raw Stata value.  Bokeh
        # renders whatever is in the column, so a formatted text column is
        # derived beside it rather than reformatting in the browser.
        text_col = mlabel_var
        _kind = getattr(self, "date_vars", {}).get(mlabel_var)
        _numfmt = getattr(self, "numeric_formats", {}).get(mlabel_var, "")
        if _kind or _numfmt:
            text_col = f"__mlabel__{mlabel_var}"
            if text_col not in source.data:
                raw = list(source.data[mlabel_var])
                if _kind:
                    rendered = [_format_date_value_standalone(v, _kind)
                                for v in raw]
                else:
                    rendered = [_format_stata_numeric(v, _numfmt).strip()
                                for v in raw]
                source.data[text_col] = rendered

        kwargs: dict[str, Any] = dict(
            x=xvar,
            y=yvar,
            text=text_col,
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
                # mlabgap(small) threw here and was silently dropped: Stata
                # takes a text size OR a number, and int(float()) accepts
                # only the number.
                gap = int(float(self.tr.translate_msize(options["mlabgap"])))
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
        # The scheme's symbol cycle.  default_symbol() existed with no call
        # site at all, so every series drew a circle and a mono scheme --
        # whose whole point is that the symbol distinguishes the series,
        # because the colour does not -- was unreadable.  Colour schemes
        # declare circle for every p#, so they are unaffected.
        marker = self.scheme.default_symbol(color_idx)
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
            size=self.scheme.default_marker_size(color_idx),
            fill_color=_default_color,
            line_color=_default_color,
            alpha=self.scheme.fill_alpha,
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
        connected: bool = False,
    ) -> "GlyphRenderer":
        """Add a line glyph to *fig*.

        Data is sorted by the x variable before rendering to match Stata
        behaviour (Stata's twoway line auto-sorts by x).

        Args:
            connected: True when this line is the connecting line of a
                       ``twoway connected``, which Stata styles from the
                       ``p#line`` stub rather than from ``p#lineplot``.

        Args:
            fig:     Bokeh Figure object.
            source:  Shared ColumnDataSource.
            yvar:    Name of the y-axis variable (CDS column).
            xvar:    Name of the x-axis variable (CDS column).
            options: Translated plot-level options dict.

        Returns:
            The single GlyphRenderer created.
        """
        # Drop NaN and sort by x for correct line rendering.
        # The marker-label column is carried across too: it used to be left
        # behind, so mlabel() on a line plot had to fall back to the
        # unsorted source, which still holds the rows dropped here.
        _cols = {xvar: source.data[xvar], yvar: source.data[yvar]}
        _mlab = (options or {}).get("mlabel", "")
        if _mlab and _mlab in source.data and _mlab not in _cols:
            _cols[_mlab] = source.data[_mlab]
        df = pd.DataFrame(_cols)
        df = df.dropna(subset=[xvar, yvar]).sort_values(xvar)
        sorted_source = ColumnDataSource(df)

        _line_kwargs: dict = dict(
            x=xvar,
            y=yvar,
            source=sorted_source,
            line_color=self.scheme.default_color(
                color_idx, "connected" if connected else "line"),
            line_width=self.scheme.default_line_width,
            legend_label=yvar,
        )
        # The scheme's dash cycle.  default_line_pattern() had no call site,
        # so three overlaid lines were three solid lines of the same weight
        # whatever the scheme said.  A solid pattern is an empty list, which
        # Bokeh already means by "no dash", so it is passed only when the
        # scheme asks for something else.
        _dash = (self.scheme.default_connect_pattern(color_idx) if connected
                 else self.scheme.default_line_pattern(color_idx))
        if _dash:
            _line_kwargs["line_dash"] = _dash
        if view is not None:
            _line_kwargs["view"] = view
        r = fig.line(**_line_kwargs)
        self._apply_line_opts(r, options)
        # The SORTED source, so labels cover exactly the rows the
        # line covers.  (The pairing was already correct with the original
        # source -- each row carries its own x, y and label together -- but
        # the unsorted source still holds the NaN rows map_line dropped,
        # which would label points the line does not draw.)
        self._apply_mlabel_opts(fig, sorted_source, options, xvar, yvar)
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
            self.map_line(fig, source, yvar, xvar, opts_no_label, view=view,
                          color_idx=color_idx, connected=True),
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
                      # `intensity area' was parsed and never read, so an
                      # area was half-transparent whatever the scheme said.
                      fill_alpha=self.scheme.area_alpha, legend_label=yvar)

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
                               line_color=border_color, line_width=self.scheme.default_line_width)
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
            # `intensity bar' was parsed and never read.
            fill_alpha=self.scheme.bar_alpha,
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
                                  line_width=self.scheme.default_line_width,
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
                     line_width=self.scheme.default_line_width, line_dash="solid",
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
                     line_width=self.scheme.default_line_width,
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
        scipy_stats = _optional_import("scipy", "stats", "scipy", "lfitci")

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
        if scipy_stats is None or n < 3 or np.std(x) == 0.0:
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=0.2, fill_color=_lfitci_color
            )
            line_r = fig.line(x="x_fit", y="y_fit", source=empty_ci_src,
                              line_color=_lfitci_color, line_width=self.scheme.default_line_width,
                              legend_label=yvar)
            return [line_r, band_r]

        slope, intercept, _, _, se = scipy_stats.linregress(x, y)
        # Extend x range by Bokeh's default 10% padding on each side so the
        # fit line spans the full visible plot area, not just the data range.
        x_fit = _fit_grid(x, options)
        y_fit = intercept + slope * x_fit

        # stdp -- the standard error of the PREDICTION of the mean, which is
        # what Stata's twoway lfitci uses (twoway__lfit_serset.ado:81-95):
        #     stdp = s * sqrt(1/n + (x0 - xbar)^2 / Sxx)
        # with s the residual standard deviation.  linregress returns the
        # standard error of the SLOPE, and s = se_slope * sqrt(Sxx).
        # dash multiplied by sqrt(n-2) instead of sqrt(Sxx), so every
        # confidence band was wrong by a factor of sqrt(Sxx/(n-2)) -- on
        # sysuse auto that is a band roughly 90 times too wide.
        x_mean = x.mean()
        x_ss = np.sum((x - x_mean) ** 2)  # guaranteed > 0 after np.std check
        se_resid = se * np.sqrt(x_ss)
        se_fit = se_resid * np.sqrt(1 / n + (x_fit - x_mean) ** 2 / x_ss)
        _lvl = _resolve_level(options)
        t_crit = _t_ppf(0.5 + _lvl / 200.0, df=n - 2)

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
                              line_color=_qfitci_color, line_width=self.scheme.default_line_width,
                              legend_label=yvar)
            return [line_r, band_r]

        coeffs = np.polyfit(x, y, 2)
        x_fit = _fit_grid(x, options)
        y_fit = np.polyval(coeffs, x_fit)

        # Stata's twoway qfitci uses the analytic stdp of the quadratic
        # regression, exactly as lfitci does for the linear one -- not a
        # bootstrap.  A bootstrap gave a band that was close in shape but
        # never equal, and that moved between runs unless the seed was fixed.
        _lvl = _resolve_level(options)
        # The design is CENTRED AND SCALED before the Gram matrix is formed.
        # On raw x the columns are 1, ~3e3 and ~1e7, giving a condition number
        # around 2.6e16 -- at which point the pseudo-inverse discards a real
        # singular value and the confidence band comes out about half as wide
        # as Stata's.  Rescaling is a reparameterisation of the same column
        # space, so the prediction variance is unchanged and the arithmetic
        # is well conditioned.
        _mu = float(np.mean(x))
        _sd = float(np.std(x)) or 1.0
        _z = (x - _mu) / _sd
        _zg = (x_fit - _mu) / _sd
        X = np.column_stack([np.ones_like(_z), _z, _z * _z])
        Xg = np.column_stack([np.ones_like(_zg), _zg, _zg * _zg])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            XtX_inv = np.linalg.inv(X.T @ X)
            resid = y - X @ beta
            df = max(1, len(x) - 3)
            s2 = float(resid @ resid) / df
            var_fit = np.einsum("ij,jk,ik->i", Xg, XtX_inv, Xg)
            se_fit = np.sqrt(np.maximum(s2 * var_fit, 0.0))
            t_crit = _t_ppf(0.5 + _lvl / 200.0, df=df)
            y_lower = y_fit - t_crit * se_fit
            y_upper = y_fit + t_crit * se_fit
        except np.linalg.LinAlgError:
            y_lower, y_upper = GlyphMapper._bootstrap_ci(
                x, y, x_fit, lambda xi, yi, xg: np.polyval(np.polyfit(xi, yi, 2), xg),
                fallback=y_fit, level=_lvl, seed=_resolve_seed(options),
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
        # Validate the user's option FIRST.  If statsmodels is missing the
        # layer degrades to an empty line, but a typo in bwidth() is the
        # user's to fix and must be reported either way -- and it used to
        # propagate a ValueError out of here and kill the entire render.
        bw = _stat_option_float(options, "bwidth", 0.8, "lowess",
                                lo=0.0, hi=1.0)
        if bw is None or bw <= 0.0:
            bw = 0.8

        lowess = _optional_import(
            "statsmodels.nonparametric.smoothers_lowess", "lowess",
            "statsmodels", "lowess",
        )

        x = np.array(source.data[xvar], dtype=float)
        y = np.array(source.data[yvar], dtype=float)
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        # Need statsmodels, at least 2 points, and x must vary
        if lowess is None or len(x) < 2 or np.std(x) == 0.0:
            empty = ColumnDataSource({"x_lw": [], "y_lw": []})
            return fig.line(x="x_lw", y="y_lw", source=empty)

        # Stata's lowess bwidth() is the fraction of the sample in each local
        # regression; its default is 0.8.  Resolved above.
        smoothed = lowess(y, x, frac=bw, return_sorted=True)

        lw_source = ColumnDataSource({
            "x_lw": smoothed[:, 0],
            "y_lw": smoothed[:, 1],
        })
        r = fig.line(x="x_lw", y="y_lw", source=lw_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=self.scheme.default_line_width,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        return r

    # ------------------------------------------------------------------
    # Local polynomial smoother (lpoly / lpolyci)
    # ------------------------------------------------------------------

    @staticmethod
    def _default_lpoly_bwidth(x: "np.ndarray", y: "np.ndarray") -> float:
        """Rule-of-thumb local-polynomial bandwidth, in x's own units.

        dash used a fixed 0.5 regardless of the data, which is meaningless
        once the bandwidth is absolute: 0.5 is a sensible window for a
        variable measured in units and a vanishing one for a variable
        measured in thousands.  On ``sysuse auto`` it produced a bandwidth of
        1540 where Stata's is 70.6 -- a 22-fold oversmooth.

        This is the Fan-Gijbels rule of thumb: fit a global 4th-degree
        polynomial, take its residual variance and the sum of squared second
        derivatives at the observations, and scale.

        HONESTY NOTE: this APPROXIMATES Stata's ROT, it does not reproduce it.
        Stata's `lpoly` estimates the residual variance locally rather than
        from a global fit, and that part was not reproducible from the
        published documentation.  Measured against Stata on seven datasets
        (N from 74 to 2246, x-scales differing by three orders of magnitude)
        the implied constant ranged over [0.597, 0.720]; _LPOLY_ROT_C is the
        middle of that range, so the default bandwidth lands within about
        +/-11% of Stata's.  Users who need Stata's exact smoother should give
        `bwidth()`, which IS exact.  See test/fixtures/stat_truth.json.

        Args:
            x, y: Cleaned paired arrays.

        Returns:
            A positive bandwidth in the units of *x*.
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        n = len(x)
        span = float(np.max(x) - np.min(x)) if n else 0.0
        fallback = (span / 10.0) if span > 0 else 1.0
        if n < 8:
            return fallback
        try:
            coeffs = np.polyfit(x, y, 4)
            resid = y - np.polyval(coeffs, x)
            sigma2 = float(resid @ resid) / max(1, n - 5)
            d2 = np.polyder(np.poly1d(coeffs), 2)
            denom = float(np.sum(d2(x) ** 2))
            if not (sigma2 > 0 and denom > 0):
                return fallback
            h = _LPOLY_ROT_C * (sigma2 / denom) ** 0.2
        except (np.linalg.LinAlgError, ValueError, FloatingPointError):
            return fallback
        return h if (np.isfinite(h) and h > 0) else fallback

    @staticmethod
    def _compute_lpoly_fit(
        x: "np.ndarray",
        y: "np.ndarray",
        bwidth: "float | None" = None,
        degree: int = 0,
        n_grid: int = 200,
        kernel: str = "epanechnikov",
    ) -> "tuple[np.ndarray, np.ndarray]":
        """Kernel-weighted local polynomial regression.

        Implements Nadaraya–Watson (degree=0) or local-linear (degree=1)
        regression.  For higher degrees the weights are passed to a
        least-squares polynomial fit at each grid point.

        Args:
            x, y:    Cleaned (no NaN) paired arrays.
            bwidth:  Bandwidth **in the units of x**, as Stata's ``bwidth()``
                     means it.  ``None`` derives one from the data.
            degree:  Polynomial degree (0 = kernel smoother, 1 = local linear,
                     2 = local quadratic).
            n_grid:  Number of evaluation points on the x-grid.
            kernel:  A key of :data:`_KERNELS`; Stata's default is
                     epanechnikov.

        Returns:
            ``(x_grid, y_fit)`` — 1-D arrays of length *n_grid*.
        """
        x_min, x_max = x.min(), x.max()
        if bwidth is None or not (bwidth > 0):
            bwidth = GlyphMapper._default_lpoly_bwidth(x, y)
        # Stata's bwidth() is an absolute bandwidth in data units.  dash used
        # to clamp it to [0.01, 1.0] and multiply by the x-range, so bwidth(5)
        # on a variable spanning thousands became the whole dataset -- the
        # exact opposite of the narrow window the user asked for.
        h = float(bwidth)

        support, kfn = _KERNELS.get(kernel, _KERNELS["epanechnikov"])
        x_grid = np.linspace(x_min, x_max, n_grid)
        y_fit = np.empty(n_grid)

        for i, x0 in enumerate(x_grid):
            z = (x - x0) / h
            if np.isfinite(support):
                w = np.zeros_like(z)
                inside = np.abs(z) < support
                if inside.any():
                    w[inside] = kfn(z[inside])
            else:
                w = kfn(z)
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

        bwidth = _stat_option_float(options, "bwidth", None, "lpoly", lo=0.0)
        if bwidth is not None and bwidth <= 0.0:
            warnings.warn(
                f"dash: lpoly option bwidth({options.get('bwidth')}) must be "
                f"positive; deriving it from the data instead.",
                UserWarning, stacklevel=2,
            )
            bwidth = None

        degree = int(_stat_option_float(options, "degree", 0.0, "lpoly",
                                        lo=0.0, hi=3.0) or 0.0)

        kernel = str(options.get("kernel", "") or "epanechnikov").strip().lower()
        if kernel not in _KERNELS:
            warnings.warn(
                f"dash: lpoly kernel({options.get('kernel')}) is not one of "
                f"{sorted(_KERNELS)}; using epanechnikov.",
                UserWarning, stacklevel=2,
            )
            kernel = "epanechnikov"

        x_grid, y_fit = self._compute_lpoly_fit(x, y, bwidth=bwidth,
                                                 degree=degree, kernel=kernel)
        valid = ~np.isnan(y_fit)
        lp_src = ColumnDataSource({
            "x_lp": x_grid[valid].tolist(),
            "y_lp": y_fit[valid].tolist(),
        })
        r = fig.line(x="x_lp", y="y_lp", source=lp_src,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=self.scheme.default_line_width,
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
                              line_color=_lpolyci_color, line_width=self.scheme.default_line_width,
                              legend_label=yvar)
            return [line_r, band_r]

        # The same resolution map_lpoly uses.  This was left on the pre-S07
        # code -- bwidth clamped to [0.01, 1.0] as a FRACTION, no kernel
        # lookup at all -- so `lpoly y x, bwidth(500)' and
        # `lpolyci y x, bwidth(500)' asked for one smoother and got two, and
        # kernel() was read by nothing here.  Silently, in both cases: the
        # curve is drawn, it is simply not the curve that was asked for, and
        # the band is then computed around the wrong curve.
        bwidth = _stat_option_float(options, "bwidth", None, "lpoly", lo=0.0)
        if bwidth is not None and bwidth <= 0.0:
            warnings.warn(
                f"dash: lpolyci option bwidth({options.get('bwidth')}) must "
                f"be positive; deriving it from the data instead.",
                UserWarning, stacklevel=2,
            )
            bwidth = None

        degree = int(_stat_option_float(options, "degree", 0.0, "lpoly",
                                        lo=0.0, hi=3.0) or 0.0)

        kernel = str(options.get("kernel", "") or "epanechnikov").strip().lower()
        if kernel not in _KERNELS:
            warnings.warn(
                f"dash: lpolyci kernel({options.get('kernel')}) is not one of "
                f"{sorted(_KERNELS)}; using epanechnikov.",
                UserWarning, stacklevel=2,
            )
            kernel = "epanechnikov"

        n_grid = 100  # coarser grid for speed
        x_grid, y_fit = self._compute_lpoly_fit(x, y, bwidth=bwidth,
                                                 degree=degree, kernel=kernel,
                                                 n_grid=n_grid)

        # Bootstrap CI (200 resamples for speed).  The resamples must use the
        # same smoother as the point estimate, or the band is not a band
        # around the line that is drawn.
        def _lpoly_fn(xi: "np.ndarray", yi: "np.ndarray", _xg: "np.ndarray") -> "np.ndarray":
            _, yb = self._compute_lpoly_fit(xi, yi, bwidth=bwidth,
                                            degree=degree, kernel=kernel,
                                            n_grid=n_grid)
            return yb  # NaN entries are replaced by fallback in _bootstrap_ci

        y_lower, y_upper = GlyphMapper._bootstrap_ci(
            x, y, x_grid, _lpoly_fn, fallback=y_fit,
            level=_resolve_level(options), seed=_resolve_seed(options),
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

        _fp_report_unsupported(options, "fpfit")
        p1, p2, coeffs = self._fit_fp2(x, y)
        x_grid = _fp_grid(x)
        y_fit = self._predict_fp2(x_grid, p1, p2, coeffs)

        valid = ~np.isnan(y_fit)
        fp_src = ColumnDataSource({
            "x_fp": x_grid[valid].tolist(),
            "y_fp": y_fit[valid].tolist(),
        })
        r = fig.line(x="x_fp", y="y_fp", source=fp_src,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=self.scheme.default_line_width,
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
                              line_color=_fpfitci_color, line_width=self.scheme.default_line_width,
                              legend_label=yvar)
            return [line_r, band_r]

        _fp_report_unsupported(options, "fpfitci")
        p1, p2, coeffs = self._fit_fp2(x, y)
        x_grid = _fp_grid(x)
        y_fit = self._predict_fp2(x_grid, p1, p2, coeffs)

        def _fp_fn(xi: "np.ndarray", yi: "np.ndarray", xg: "np.ndarray") -> "np.ndarray":
            bp1, bp2, bc = self._fit_fp2(xi, yi)
            return self._predict_fp2(xg, bp1, bp2, bc)

        valid = ~np.isnan(y_fit)
        y_lower, y_upper = GlyphMapper._bootstrap_ci(
            x, y, x_grid, _fp_fn, fallback=y_fit,
            level=_resolve_level(options), seed=_resolve_seed(options),
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

        edges, ymode = self._histogram_grid(arr, options)
        counts, _ = np.histogram(arr, bins=edges)
        tops = _histogram_heights(counts, edges, ymode)

        hist_source = ColumnDataSource({
            "top":   tops,
            "left":  edges[:-1],
            "right": edges[1:],
        })
        r = fig.quad(top="top", bottom=0, left="left", right="right",
                     source=hist_source,
                     fill_color=self.scheme.default_color(color_idx, "histogram"),
                     line_color="white",
                     # `intensity bar' -- a histogram is a bar plot in
                     # Stata's own scheme vocabulary.
                     fill_alpha=self.scheme.bar_alpha, legend_label=yvar)
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
            # The y-axis family must be recomputed under a filter too: a
            # density histogram of a filtered subset has to renormalise to the
            # surviving rows, or the curve silently stops integrating to 1.
            "ymode":     ymode,
        }
        return r

    @staticmethod
    def _histogram_grid(
        arr: "np.ndarray", options: "dict[str, str]",
    ) -> "tuple[np.ndarray, str]":
        """Resolve Stata's histogram bin grid and y-axis family.

        Stata's precedence ([R] histogram): ``width()`` and ``start()``
        together define the grid explicitly; ``bin()`` instead sets a count
        over the observed range; with neither, the count comes from the data
        via :func:`_stata_bin_count`.

        Args:
            arr:     Finite observations being binned.
            options: Translated plot-level options.

        Returns:
            ``(edges, ymode)`` where *ymode* is one of ``"density"``,
            ``"fraction"``, ``"frequency"`` or ``"percent"``.
        """
        _MAX_BINS = 1000
        n = len(arr)
        a_min = float(arr.min()) if n else 0.0
        a_max = float(arr.max()) if n else 1.0

        start = _stat_option_float(options, "start", None, "histogram")
        if start is None:
            start = a_min
        width = _stat_option_float(options, "width", None, "histogram", lo=0.0)
        if width is not None and width <= 0.0:
            warnings.warn(
                f"dash: histogram option width({options.get('width')}) must be "
                f"positive; deriving the width from the data instead.",
                UserWarning, stacklevel=2,
            )
            width = None

        span = a_max - start
        if span <= 0.0:
            span = abs(a_max) or 1.0

        if width is not None:
            n_bins = int(math.ceil(span / width))
        else:
            requested = _stat_option_float(options, "bin", None, "histogram", lo=1.0)
            n_bins = int(requested) if requested is not None else _stata_bin_count(n)

        n_bins = max(1, n_bins)
        if n_bins > _MAX_BINS:
            # Kept from the original: an enormous bin() is a resource-exhaustion
            # vector.  Now reported rather than applied silently.
            warnings.warn(
                f"dash: histogram bin count {n_bins} exceeds the {_MAX_BINS} "
                f"limit; using {_MAX_BINS} bins.",
                UserWarning, stacklevel=2,
            )
            n_bins = _MAX_BINS
            width = None

        if width is None:
            width = span / n_bins

        edges = start + width * np.arange(n_bins + 1, dtype=float)
        # The last edge must cover the data even when start()/width() were
        # given explicitly, or np.histogram silently drops the top
        # observations.
        #
        # The comparison needs a tolerance.  When width was DERIVED as
        # span / n_bins, edges[-1] is a_max in exact arithmetic but can land a
        # few ulps below it in floating point -- and then this appended a bin
        # about 1e-14 wide.  A density is count / (total * width), so that bin
        # became a spike twelve orders of magnitude above every real bar and
        # flattened the rest of the histogram to nothing.  Measured on a
        # 74-observation fixture: bin(6) and bin(12) each drew one bar more
        # than asked for, of width 7.105e-15 and density 1.902e+12.
        _edge_tol = 1e-9 * max(abs(float(a_max)), abs(float(start)),
                               float(width), 1.0)
        if edges[-1] < a_max - _edge_tol:
            edges = np.append(edges, a_max)

        ymode = "density"
        for flag in ("frequency", "percent", "fraction", "density"):
            if str(options.get(flag, "")).strip():
                ymode = flag
                break
        return edges, ymode

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
        if options is None:
            options = {}
        arr = _extract_finite(source, yvar)

        # Stata's kernels are implemented directly (see _KERNELS): scipy's
        # gaussian_kde can only ever be Gaussian, so it could not express
        # kernel() at all, and Stata's default kernel is epanechnikov.
        if len(arr) < 2 or np.std(arr) == 0.0:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        kernel = str(options.get("kernel", "") or "epanechnikov").strip().lower()
        if kernel not in _KERNELS:
            warnings.warn(
                f"dash: kdensity kernel({options.get('kernel')}) is not one of "
                f"{sorted(_KERNELS)}; using epanechnikov.",
                UserWarning, stacklevel=2,
            )
            kernel = "epanechnikov"

        default_bw = _stata_kde_bandwidth(arr)
        bw = _stat_option_float(options, "bwidth", default_bw, "kdensity",
                                lo=0.0)
        if bw is None or bw <= 0.0:
            if str(options.get("bwidth", "")).strip():
                warnings.warn(
                    f"dash: kdensity option bwidth({options.get('bwidth')}) "
                    f"must be positive; deriving it from the data instead.",
                    UserWarning, stacklevel=2,
                )
            bw = default_bw
        if bw <= 0.0:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        n_pts = _stat_option_float(options, "n", 300.0, "kdensity", lo=2.0,
                                   hi=10000.0) or 300.0
        # Extend beyond the data so the tails of the kernel are drawn.
        x_range = np.linspace(arr.min() - 3 * bw, arr.max() + 3 * bw,
                              int(n_pts))
        density = _kde_curve(arr, x_range, bw, kernel)

        kd_source = ColumnDataSource({"x": x_range, "y": density})
        r = fig.line(x="x", y="y", source=kd_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=self.scheme.default_line_width,
                     legend_label=yvar)
        self._apply_line_opts(r, options)
        # Tag renderer so DashRenderer can wire filter-callback recomputation.
        # The JS recomputes on the same x grid, with the same kernel and the
        # same bandwidth rule (_KDE_BANDWIDTH_RULE), so an inert filter leaves
        # the curve exactly where it was.  An explicit bwidth() is passed
        # through as a fixed bandwidth; otherwise the JS re-derives it from the
        # filtered rows, which is what Stata would do on that subset.
        r._dash_agg_source = kd_source
        r._dash_agg_config = {
            "type":      "kdensity",
            "varname":   yvar,
            "x_grid":    x_range.tolist(),
            "kernel":    kernel,
            "bw_rule":   _KDE_BANDWIDTH_RULE,
            "bw_fixed":  (float(bw)
                          if str(options.get("bwidth", "")).strip() else None),
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
                                   line_width=self.scheme.default_line_width,
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
                                    line_color=_rcap_color, line_width=self.scheme.default_line_width,
                                    legend_label=y1var)
        _bot_kwargs: dict = dict(x0=_x0_col, y0=y1var, x1=_x1_col, y1=y1var,
                                  source=cap_source,
                                  line_color=_rcap_color, line_width=self.scheme.default_line_width)
        _top_kwargs: dict = dict(x0=_x0_col, y0=y2var, x1=_x1_col, y1=y2var,
                                  source=cap_source,
                                  line_color=_rcap_color, line_width=self.scheme.default_line_width)
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
                                  line_width=self.scheme.default_line_width,
                                  legend_label=y1var)
        _rl2_kwargs: dict = dict(x=xvar, y=y2var, source=source,
                                  line_color=self.scheme.default_color(color_idx + 1, "line"),
                                  line_width=self.scheme.default_line_width)
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

        # A malformed values array used to surface as a bare
        # "could not convert string to float: 'A'", which says nothing about
        # where it came from.  Name the plot type and the offending pair.
        try:
            y_vals = np.array([float(pair[0]) for pair in values])
            x_vals = np.array([float(pair[1]) for pair in values])
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(
                "dash: scatteri coordinates must be numeric y x pairs; got "
                f"{values!r} ({exc}). Marker labels go after each pair, as in: "
                'scatteri 20 3000 "A" 30 4000 "B"'
            ) from exc

        # An optional third element on a pair is that point's marker label:
        #   scatteri 20 3000 "A" 30 4000 "B"  ->  [[20,3000,"A"],[30,4000,"B"]]
        _labels = [
            (str(pair[2]) if len(pair) > 2 and pair[2] is not None else "")
            for pair in values
        ]
        _has_labels = any(_labels)

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
        # Marker labels, one per point, from the optional third element.
        if _has_labels:
            from bokeh.models import LabelSet
            _lsrc = ColumnDataSource({
                "x": list(x_vals), "y": list(y_vals), "lab": _labels,
            })
            fig.add_layout(LabelSet(
                x="x", y="y", text="lab", source=_lsrc,
                x_offset=4, y_offset=4,
                text_font_size=self.scheme.text_font_size,
            ))

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
        PchipInterpolator = _optional_import(
            "scipy.interpolate", "PchipInterpolator", "scipy", "mspline",
        )

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

        # Needs scipy, and at least 2 valid (distinct) points for interpolation
        if PchipInterpolator is None or len(x_clean) < 2:
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

        requested = _stat_option_float(options, "bands", None, "mband", lo=1.0)
        n_bands = (int(requested) if requested is not None
                   else _mband_default_bands(len(x_clean)))
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
                # Stata plots CROSS-MEDIANS: the median x and the median y of
                # the observations inside the band, not the band's midpoint.
                # With unevenly spread x the midpoint can sit where there is
                # no data at all.
                x_mids.append(float(np.median(x_clean[in_band])))
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
        n_points: int = 300,
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
            n_points: Number of grid points.  Stata's default is 300.
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

        expr = _stata_expr_to_python(expr)

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


def _mband_default_bands(n: int) -> int:
    """Stata's default number of median bands.

    ``round(min(sqrt(N), 10*log10(N)))`` -- the same expression as the
    histogram bin rule, but ROUNDED where the histogram rule truncates.

    NOTE: this is NOT what Stata documents.  `help twoway_mband` says
    ``max(10, round(10*log10(N)))``, which would give 19 bands on auto where
    Stata actually draws 9.  The graph engine computes the count internally
    and no .ado exposes it, so this rule was recovered by measurement: it
    reproduces all 14 probed (N, bands) pairs, from N=25 to N=2246.  See
    ``mband_default_band_count_rule_search`` in test/fixtures/stat_truth.json.

    dash previously used an invented ``clip(ceil(n/5), 2, 20)``, which gives
    15 bands on auto.

    Args:
        n: Number of usable observations.

    Returns:
        The band count, at least 1.
    """
    if n < 1:
        return 1
    return max(1, int(round(min(math.sqrt(n), 10.0 * math.log10(n)))))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    TINY, EPS, ITMAX = 1e-300, 3e-16, 300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < TINY:
        d = TINY
    d = 1.0 / d
    h = d
    for m in range(1, ITMAX + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY:
            d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY:
            c = TINY
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < TINY:
            d = TINY
        c = 1.0 + aa / c
        if abs(c) < TINY:
            c = TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log1p(-x))
    front = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + b * math.log1p(-x) + a * math.log(x)
    ) * _betacf(b, a, 1.0 - x) / b


def _t_cdf(t: float, df: float) -> float:
    """CDF of Student's t with *df* degrees of freedom."""
    xx = df / (df + t * t)
    p = 0.5 * _betainc(0.5 * df, 0.5, xx)
    return 1.0 - p if t > 0 else p


def _t_ppf(p: float, df: float) -> float:
    """Inverse CDF of Student's t, WITHOUT scipy.

    ``map_qfitci`` is required to work with scipy unavailable
    (test_dependency_guards.TestQfitciNeedsNoScipy), and it now needs a t
    quantile because Stata's twoway qfitci uses an analytic band rather than
    a bootstrap.  Rather than either bolting on a scipy import or accepting a
    band that does not match Stata, the quantile is computed here: the t CDF
    from the regularised incomplete beta, then inverted by bisection.

    Accuracy is checked against scipy in test_statistical_defaults.py
    wherever scipy is installed.

    Args:
        p:  Probability in (0, 1).
        df: Degrees of freedom, > 0.

    Returns:
        The quantile t such that P(T <= t) = p.
    """
    if not (0.0 < p < 1.0):
        raise ValueError(f"_t_ppf: p must be in (0, 1), got {p!r}")
    if df <= 0:
        raise ValueError(f"_t_ppf: df must be positive, got {df!r}")
    if abs(p - 0.5) < 1e-15:
        return 0.0
    lo, hi = -1.0, 1.0
    while _t_cdf(lo, df) > p:
        lo *= 2.0
        if lo < -1e12:
            break
    while _t_cdf(hi, df) < p:
        hi *= 2.0
        if hi > 1e12:
            break
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13 * max(1.0, abs(mid)):
            break
    return 0.5 * (lo + hi)


def _fit_grid(x: "np.ndarray", options: dict) -> "np.ndarray":
    """The x values a fitted line is drawn at, as Stata chooses them.

    ``x_i = min + (i-1)*(max-min)/(n-1)`` for i = 1..n, with ``n()``
    defaulting to 100 and min/max the OBSERVED range
    (ado/base/_/_gs_x_create.ado).

    Args:
        x:       Cleaned x observations.
        options: Translated plot-level options; ``n()`` overrides the count.

    Returns:
        The evaluation grid.
    """
    n_pts = int(_stat_option_float(options, "n", float(_FIT_GRID), "fit",
                                   lo=2.0, hi=10000.0) or _FIT_GRID)
    lo, hi = float(np.min(x)), float(np.max(x))
    if not (hi > lo):
        hi = lo + 1.0
    return np.linspace(lo, hi, n_pts)


def _fp_grid(x: "np.ndarray") -> "np.ndarray":
    """The x values a fractional-polynomial fit is evaluated at.

    Stata's ``twoway fpfit`` and ``fpfitci`` use NO grid: both evaluate at the
    distinct observed x values, so the number of points is data-dependent and
    the two overlay exactly.  dash used a 200-point linspace for fpfit and a
    150-point one for fpfitci, both truncated to the 1st-99th percentile and
    each computing that truncation slightly differently -- so the band and the
    line it belonged to did not lie on top of each other, and both ends of the
    fit were cut off.

    A fractional polynomial needs x > 0, so non-positive observations are
    dropped.

    Args:
        x: Cleaned x observations.

    Returns:
        Sorted distinct positive x values, capped at _FP_GRID_MAX points.
    """
    pos = np.unique(x[x > 0])
    if len(pos) == 0:
        return np.array([1e-6, 1.0])
    if len(pos) == 1:
        return np.array([float(pos[0])])
    if len(pos) > _FP_GRID_MAX:
        # Resource guard: the bootstrap band costs O(n_boot * n_points), so a
        # dataset with a hundred thousand distinct x values would hang the
        # render.  Fall back to an even grid across the same range.
        return np.linspace(float(pos[0]), float(pos[-1]), _FP_GRID_MAX)
    return pos.astype(float)


def _fp_report_unsupported(options: dict, layer: str) -> None:
    """Report fpfit sub-options that Stata itself rejects.

    ``dash.sthlp`` documented ``bwidth()`` and ``degree()`` for fpfit; Stata
    rejects both with r(198) ("option bwidth() not allowed"), and there is no
    bandwidth concept in a fractional polynomial at all.  Silently ignoring
    them would leave the user believing they had an effect.
    """
    for key in ("bwidth", "degree"):
        if str(options.get(key, "")).strip():
            warnings.warn(
                f"dash: {layer} does not accept {key}() -- neither does "
                f"Stata's twoway {layer}, which rejects it with r(198). "
                f"The option is being ignored.",
                UserWarning, stacklevel=3,
            )


def _resolve_level(options: dict, default: float = _DEFAULT_LEVEL) -> float:
    """Return the confidence level for a CI layer.

    Args:
        options: Translated plot-level options; ``level()`` wins when present.
        default: The session default, from ``c(level)``.

    Returns:
        A level strictly inside (0, 100).
    """
    raw = options.get("level", None)
    if raw is None or str(raw).strip() == "":
        return float(default)
    try:
        val = float(str(raw).strip())
    except (TypeError, ValueError):
        warnings.warn(
            f"dash: level({raw}) is not a number; using {default}.",
            UserWarning, stacklevel=3,
        )
        return float(default)
    if not (0.0 < val < 100.0):
        warnings.warn(
            f"dash: level({raw}) must be between 0 and 100; using {default}.",
            UserWarning, stacklevel=3,
        )
        return float(default)
    return val


def _resolve_seed(options: dict, default: int = 42) -> int:
    """Return the RNG seed for a resampling layer.

    ``jseed()`` is the only seed option dash declares; it seeds jitter and,
    here, the bootstrap confidence bands, so a user who needs a different
    resample draw can ask for one instead of always getting seed 42.
    """
    raw = options.get("jseed", "")
    if str(raw).strip():
        try:
            return int(float(str(raw).strip()))
        except (TypeError, ValueError):
            pass
    return default


def _stat_option_float(
    options: dict,
    key: str,
    default: "float | None",
    layer: str,
    lo: "float | None" = None,
    hi: "float | None" = None,
) -> "float | None":
    """Read a numeric statistical option, reporting bad input instead of dying.

    Several statistical layers read their parameters with a bare ``float()``.
    A non-numeric value there does not degrade the layer -- it propagates out
    of the mapper and takes the entire render down, so one typo in one option
    loses the whole dashboard.

    Args:
        options: Translated plot-level options.
        key:     Option name, e.g. ``"bwidth"``.
        default: Value to use when the option is absent or unusable.
        layer:   Plot type name, used in the warning text.
        lo, hi:  Inclusive bounds; a value outside them is reported and the
                 default used.

    Returns:
        The coerced value, or *default*.
    """
    raw = options.get(key, None)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        val = float(str(raw).strip())
    except (TypeError, ValueError):
        warnings.warn(
            f"dash: {layer} option {key}({raw}) is not a number; using "
            f"{default!r} instead.",
            UserWarning, stacklevel=3,
        )
        return default
    if not np.isfinite(val):
        warnings.warn(
            f"dash: {layer} option {key}({raw}) is not finite; using "
            f"{default!r} instead.",
            UserWarning, stacklevel=3,
        )
        return default
    if (lo is not None and val < lo) or (hi is not None and val > hi):
        bounds = f"[{lo}, {hi}]" if lo is not None and hi is not None else (
            f">= {lo}" if lo is not None else f"<= {hi}")
        warnings.warn(
            f"dash: {layer} option {key}({raw}) is outside {bounds}; using "
            f"{default!r} instead.",
            UserWarning, stacklevel=3,
        )
        return default
    return val


# Stata's kernel definitions ([R] kdensity).  z = (x - x_i) / h.  Each entry
# is (support half-width, callable); outside the support the weight is zero.
# epanechnikov is Stata's DEFAULT -- dash previously always used gaussian, via
# scipy's gaussian_kde, which could not express any other kernel.
_KERNELS: dict = {
    "epanechnikov": (math.sqrt(5.0),
                     lambda z: 0.75 * (1.0 - z * z / 5.0) / math.sqrt(5.0)),
    "epan2":        (1.0, lambda z: 0.75 * (1.0 - z * z)),
    "biweight":     (1.0, lambda z: (15.0 / 16.0) * (1.0 - z * z) ** 2),
    "cosine":       (0.5, lambda z: 1.0 + np.cos(2.0 * np.pi * z)),
    "gaussian":     (np.inf,
                     lambda z: np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)),
    "rectangle":    (1.0, lambda z: np.full_like(z, 0.5)),
    "triangle":     (1.0, lambda z: 1.0 - np.abs(z)),
    "parzen":       (1.0, lambda z: np.where(
                        np.abs(z) <= 0.5,
                        (4.0 / 3.0) - 8.0 * z * z + 8.0 * np.abs(z) ** 3,
                        (8.0 / 3.0) * (1.0 - np.abs(z)) ** 3)),
}

# Named in the JavaScript too, so the two implementations cannot drift apart
# without the test that compares them noticing.  See DASH_KDE_RULE in _FILTER_JS.
_KDE_BANDWIDTH_RULE = "silverman-0.9-min-sd-iqr/1.349"


def _stata_percentile(sorted_arr: "np.ndarray", p: float) -> float:
    """Stata's percentile, which is not numpy's.

    [R] summarize: with ``i = n*p/100``, the percentile is
    ``(x_(i) + x_(i+1))/2`` when *i* is an integer and ``x_(ceil(i))``
    otherwise.  numpy interpolates linearly instead, and the difference is
    not cosmetic: using numpy's rule made dash's kernel-density bandwidth
    differ from Stata's in the third significant figure on auto/mpg.

    Args:
        sorted_arr: Observations sorted ascending.
        p:          Percentile in [0, 100].

    Returns:
        The percentile value.
    """
    n = len(sorted_arr)
    if n == 0:
        return float("nan")
    i = n * p / 100.0
    if abs(i - round(i)) < 1e-12:
        k = int(round(i))
        if k >= n:
            return float(sorted_arr[-1])
        if k <= 0:
            return float(sorted_arr[0])
        return float((sorted_arr[k - 1] + sorted_arr[k]) / 2.0)
    k = int(math.ceil(i))
    return float(sorted_arr[min(max(k, 1), n) - 1])


def _stata_kde_bandwidth(arr: "np.ndarray") -> float:
    """Stata's default kernel-density bandwidth.

    [R] kdensity: ``w = 0.9 * m * n^(-1/5)`` where
    ``m = min(sd, interquartile range / 1.349)``, with the IQR taken under
    STATA's percentile definition (see :func:`_stata_percentile`).

    Verified exact to ten decimal places against Stata: ``kdensity mpg`` on
    ``sysuse auto`` returns r(bwidth) = 1.9746142001, and so does this.

    dash previously used scipy's Scott factor on the initial render while the
    filter callback used this rule, so the curve jumped the first time any
    filter was touched even when no rows were removed.  One rule, both paths.

    Args:
        arr: Finite observations.

    Returns:
        The bandwidth in data units; 0.0 when it is not computable.
    """
    n = len(arr)
    if n < 2:
        return 0.0
    sd = float(np.std(arr, ddof=1))
    srt = np.sort(np.asarray(arr, dtype=float))
    iqr = _stata_percentile(srt, 75) - _stata_percentile(srt, 25)
    m = min(sd, iqr / 1.349) if iqr > 0 else sd
    if m <= 0:
        m = sd
    if m <= 0:
        return 0.0
    return 0.9 * m * n ** (-0.2)


def _kde_curve(
    arr: "np.ndarray", grid: "np.ndarray", h: float, kernel: str,
) -> "np.ndarray":
    """Evaluate a kernel density estimate on *grid*.

    Args:
        arr:    Finite observations.
        grid:   Points at which to evaluate the density.
        h:      Bandwidth in data units.
        kernel: A key of :data:`_KERNELS`.

    Returns:
        Density values, one per grid point.
    """
    support, kfn = _KERNELS[kernel]
    n = len(arr)
    out = np.empty(len(grid), dtype=float)
    for i, x0 in enumerate(grid):
        z = (x0 - arr) / h
        if np.isfinite(support):
            inside = np.abs(z) < support
            w = np.zeros_like(z)
            if inside.any():
                w[inside] = kfn(z[inside])
        else:
            w = kfn(z)
        out[i] = w.sum() / (n * h)
    return out


def _histogram_heights(
    counts: "np.ndarray", edges: "np.ndarray", ymode: str,
) -> "np.ndarray":
    """Scale raw bin counts into Stata's chosen y-axis family.

    Stata's histogram plots DENSITY by default for a continuous variable, so
    the bar areas integrate to 1.  dash plotted raw counts, which is Stata's
    ``frequency`` option.

    Args:
        counts: Raw per-bin counts.
        edges:  Bin edges, length ``len(counts) + 1``.
        ymode:  ``"density"``, ``"fraction"``, ``"frequency"`` or ``"percent"``.

    Returns:
        The bar heights.
    """
    counts = np.asarray(counts, dtype=float)
    total = float(counts.sum())
    if total <= 0:
        return counts
    if ymode == "frequency":
        return counts
    if ymode == "fraction":
        return counts / total
    if ymode == "percent":
        return 100.0 * counts / total
    widths = np.diff(np.asarray(edges, dtype=float))
    widths[widths == 0] = 1.0
    return counts / (total * widths)


def _stata_bin_count(n: int) -> int:
    """Stata's default number of histogram bins for *n* observations.

    ``k = min(sqrt(n), 10*ln(n)/ln(10))``, TRUNCATED.  Verified against Stata
    on two datasets: auto/mpg (n=74) gives 8, nlsw88/wage (n=2246) gives 33 --
    both of which round UP to 9 and 34, so the rule truncates rather than
    rounds.  See test/fixtures/stat_truth.json.

    Args:
        n: Number of non-missing observations.

    Returns:
        The bin count, at least 1.
    """
    if n < 1:
        return 1
    k = min(math.sqrt(n), 10.0 * math.log(n) / math.log(10.0))
    return max(1, int(k))


def _stata_expr_to_python(expr: str) -> str:
    """Rewrite Stata's arithmetic operators into their Python spellings.

    Stata writes exponentiation as ``^``.  Python reads ``^`` as a bitwise
    XOR, which is a legal operator node, so ``x^2`` passes the AST whitelist
    unchanged and only fails at evaluation time with a TypeError on the float
    array -- drawing an empty line instead of a parabola.

    Only the operator is rewritten, and only outside string literals.  The
    caller validates the REWRITTEN expression, so this adds nothing to what
    the whitelist permits.

    Args:
        expr: A Stata expression, e.g. ``"x^2"`` or ``"2*x^3 - 1"``.

    Returns:
        The equivalent Python expression, e.g. ``"x**2"``.
    """
    out: list[str] = []
    quote = ""
    for ch in expr:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        out.append("**" if ch == "^" else ch)
    return "".join(out)


def _stata_if_to_pandas(expr: str) -> str:
    """Rewrite Stata's qualifier idioms into plain comparison expressions.

    ``if !missing(rep78)``, ``if inlist(rep78,1,2)`` and ``if rep78 < .`` are
    the three most common qualifier forms in real Stata code, and all three
    failed validation, warned, and rendered the graph UNFILTERED.

    This is a TRANSLATION performed BEFORE validation, not a loosening of the
    whitelist.  Every rewrite produces only comparisons and boolean
    combinators -- the node types the validator already permits -- so the
    validator is unchanged and still sees the whole expression.  A hostile
    argument inside one of these functions does not survive: it either
    produces a Call node, which the whitelist rejects, or malformed output,
    which fails to parse.  Covered by the adversarial tests in
    test/test_axis_options.py.

    Args:
        expr: A Stata if-qualifier expression.

    Returns:
        An equivalent expression in pandas-query syntax.
    """
    if not expr:
        return expr
    out = str(expr)

    # inlist(x, a, b, ...) -> ((x == a) | (x == b) | ...)
    def _inlist(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) < 2 or not parts[0]:
            return m.group(0)
        var, vals = parts[0], [p for p in parts[1:] if p]
        if not vals:
            return m.group(0)
        return "(" + " | ".join(f"({var} == {v})" for v in vals) + ")"

    out = re.sub(r"\binlist\s*\(([^()]*)\)", _inlist, out)

    # inrange(x, a, b) -> ((x >= a) & (x <= b))
    def _inrange(m):
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) != 3 or not all(parts):
            return m.group(0)
        v, lo, hi = parts
        return f"(({v} >= {lo}) & ({v} <= {hi}))"

    out = re.sub(r"\binrange\s*\(([^()]*)\)", _inrange, out)

    # missing(x) -> (x != x).  NaN is the only value not equal to itself.
    out = re.sub(r"\bmissing\s*\(([^()]*)\)",
                 lambda m: f"({m.group(1).strip()} != {m.group(1).strip()})",
                 out)

    # Stata's missing idioms against the sort-last dot.
    out = re.sub(r"([A-Za-z_]\w*)\s*<\s*\.(?!\d)", r"(\1 == \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*<=\s*\.(?!\d)", r"(\1 == \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*!=\s*\.(?!\d)", r"(\1 == \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*~=\s*\.(?!\d)", r"(\1 == \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*==\s*\.(?!\d)", r"(\1 != \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*>=\s*\.(?!\d)", r"(\1 != \1)", out)
    out = re.sub(r"([A-Za-z_]\w*)\s*>\s*\.(?!\d)", r"(\1 != \1)", out)

    # Stata's ~= is !=, and its ! is a logical not; leave != alone.
    out = out.replace("~=", "!=")
    out = re.sub(r"!(?!=)", "~", out)
    return out


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


def _resolve_kpi_color(val: str, default: str) -> str:
    """Resolve a KPI colour to something safe to put in a style attribute.

    Two bugs met here.

    SECURITY: ``_make_kpi_div`` applied only ``html.escape`` before
    interpolating the value into ``style="...color:{color};"``.  html.escape
    neutralises the quote characters, so it does block an attribute breakout
    -- but a CSS *property* injection needs none of them.  ``;``, ``(`` and
    ``)`` pass straight through, so ``red; background:url(http://evil/x)``
    became a second declaration and the browser honoured it.  The project
    already had ``_sanitize_css_color`` and the JS filter-callback path called
    it; only the initial render did not, so a KPI was unsafe until the first
    time a filter moved.

    CORRECTNESS: the value is a STATA colour name, not a CSS one.  ``navy``
    reached the browser as CSS navy (#000080) where Stata's navy is #1a476f,
    and ``gs10`` or ``red%50`` -- both legitimate in Stata -- are not CSS at
    all, so sanitising without translating first turned them into the default
    grey.  Worse, the two paths then disagreed and the card changed colour on
    the first filter interaction.

    Translate first, then sanitise: a Stata name becomes a hex value, which
    the sanitiser accepts, and anything the translator cannot resolve still
    faces the sanitiser.

    Args:
        val:     The raw ``color()``/``bgcolor()`` value.
        default: A trusted fallback.

    Returns:
        A CSS colour that is safe to interpolate.
    """
    raw = (val or "").strip()
    if not raw:
        return default
    try:
        translated = OptionTranslator.translate_mcolor(raw)
    except (ValueError, TypeError):
        translated = raw
    return _sanitize_css_color(translated, default)


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
// above.  Sources do NOT share a row universe -- a by() graph has one
// source per facet and a qualified graph a pre-filtered one -- so the mask
// applies correctly to every source regardless of column differences.
const _srcs = all_graph_sources;
const _srcs_orig_json = all_graph_sources_orig_json;
const ROW_ID = "__dash_row__";

// The set of row identities that survived every active filter, taken from
// the PRIMARY snapshot.  Masking on identity rather than on position is what
// makes a shorter source -- a by() facet, or a qualified graph -- mask
// correctly; `active[i]` for such a source used to mean the primary's row i,
// a different observation entirely.
const _primary_ids = orig[ROW_ID];
const _active_ids = new Set();
if (_primary_ids) {
    for (let i = 0; i < _primary_ids.length; i++) {
        if (active[i]) _active_ids.add(_primary_ids[i]);
    }
}

// Row identities each source kept, so a CDSView over it can be rebuilt.
const _kept_ids_by_src = [];

for (let _si = 0; _si < _srcs.length; _si++) {
    // Parse this source's own snapshot — preserves its unique column set.
    const _orig_i = JSON.parse(_srcs_orig_json[_si]);
    const _cols_i = Object.keys(_orig_i);
    const _n_i    = _cols_i.length > 0 ? _orig_i[_cols_i[0]].length : 0;
    const _ids_i  = _orig_i[ROW_ID];
    const _nd_i   = {};
    const _kept_i = [];
    for (const col of _cols_i) { _nd_i[col] = []; }
    for (let i = 0; i < _n_i; i++) {
        // Fall back to the old positional test only when a source predates
        // the row identity, so an older spec still filters as it used to.
        const keep = _ids_i && _primary_ids
            ? _active_ids.has(_ids_i[i])
            : (i < active.length && active[i]);
        if (keep) {
            for (const col of _cols_i) { _nd_i[col].push(_orig_i[col][i]); }
            if (_ids_i) _kept_i.push(_ids_i[i]);
        }
    }
    _kept_ids_by_src.push(_kept_i);
    _srcs[_si].data = _nd_i;
    _srcs[_si].selected.indices = [];
    _srcs[_si].change.emit();
}

// A linked by() graph draws its panels as CDSViews over ONE shared source,
// with a BooleanFilter built at render time and sized to the unfiltered
// frame.  Replacing the source's data above leaves those booleans the wrong
// length, so every panel would mask the wrong rows.  Rebuild each one
// against the rows its source actually kept.
for (const vf of (view_filters || [])) {
    const _si = vf.src_index;
    if (_si === undefined || _si === null) continue;
    const kept = _kept_ids_by_src[_si] || [];
    const member = new Set(vf.member_ids || []);
    vf.filter.booleans = kept.map(id => member.has(id));
    vf.filter.change.emit();
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
// ---- KPI recompute, shared by the filter path and the brush path ----
//
// ONE function on purpose.  It carries Stata's percentile rule, the
// date-valued-statistic branch and the %9.0g general format, all of which
// have to agree with _stata_percentile() and _effective_kpi_fmt() in Python.
// A second copy for the brush path would drift from this one, which is the
// failure test_kpi_values.py exists to catch.
//
// `data_obj' is a column->array map already restricted to the rows that
// should count: the filter path passes the rows that survived every widget,
// the brush path passes the rows the user selected.
function dash_apply_kpis(data_obj, kpi_config, kpi_divs, ROW_ID) {
    for (let ki = 0; ki < kpi_config.length; ki++) {
        const k      = kpi_config[ki];
        const kpi_div = kpi_divs[ki];
        if (!kpi_div) continue;

        const col = data_obj[k.varname];
        if (!col) continue;
        // A KPI with its own if/in qualifier is restricted to the rows that
        // qualifier selects, intersected with the rows the filters kept.  Without
        // this the card opens on the conditional value and silently becomes the
        // unconditional one the first time any widget moves.
        let src_col = col;
        if (k.has_qual) {
            const qset = new Set(k.qual_ids || []);
            const rids = data_obj[ROW_ID];
            src_col = [];
            if (rids) {
                for (let qi = 0; qi < col.length; qi++) {
                    if (qset.has(rids[qi])) src_col.push(col[qi]);
                }
            }
        }
        const vals = src_col.filter(v => v !== null && v !== undefined && !isNaN(v));

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
            } else if (stat === 'dcount') {
                result = new Set(vals.map(String)).size;
            } else if (stat === 'sd' && vals.length > 1) {
                const mu = vals.reduce((a, b) => a + b, 0) / vals.length;
                result = Math.sqrt(
                    vals.reduce((a, b) => a + Math.pow(b - mu, 2), 0) / (vals.length - 1)
                );
            } else if (stat === 'var' && vals.length > 1) {
                const mu = vals.reduce((a, b) => a + b, 0) / vals.length;
                result = vals.reduce((a, b) => a + Math.pow(b - mu, 2), 0)
                         / (vals.length - 1);
            } else if (stat === 'cv' && vals.length > 1) {
                const mu = vals.reduce((a, b) => a + b, 0) / vals.length;
                const sd = Math.sqrt(
                    vals.reduce((a, b) => a + Math.pow(b - mu, 2), 0) / (vals.length - 1)
                );
                result = mu ? sd / mu : NaN;
            } else if (stat === 'skewness' && vals.length > 1) {
                // Stata's biased m3 / m2^1.5, matching the Python side.
                const mu = vals.reduce((a, b) => a + b, 0) / vals.length;
                const m2 = vals.reduce((a, b) => a + Math.pow(b - mu, 2), 0) / vals.length;
                const m3 = vals.reduce((a, b) => a + Math.pow(b - mu, 3), 0) / vals.length;
                result = m2 > 0 ? m3 / Math.pow(m2, 1.5) : NaN;
            } else {
                // median, p50, p25, p75 and any other pNN.  dash_pctl is
                // STATA's percentile rule, the same one _stata_percentile
                // implements in Python -- p25/p75 used to have no branch at all
                // here and fell through to result = 0 on the first filter move,
                // and a rule that merely looked reasonable would disagree with
                // the initial render.
                const s = vals.slice().sort((a, b) => a - b);
                if (stat === 'median') {
                    result = dash_pctl(s, 50);
                } else if (stat === 'iqr') {
                    result = dash_pctl(s, 75) - dash_pctl(s, 25);
                } else {
                    const mp = /^p(\\d{1,2}(?:\\.\\d+)?)$/.exec(stat);
                    if (mp) result = dash_pctl(s, parseFloat(mp[1]));
                }
            }
        }

        let fmt;
        if (k.datekind) {
            // The value is epoch milliseconds; render it the way the first
            // render did, or a filtered date KPI reads as a raw number.
            const d = new Date(result);
            const MON = ['Jan','Feb','Mar','Apr','May','Jun',
                         'Jul','Aug','Sep','Oct','Nov','Dec'];
            if (isNaN(d.getTime())) {
                fmt = '—';
            } else if (k.datekind === 'ty') {
                fmt = String(d.getUTCFullYear());
            } else if (k.datekind === 'tc' || k.datekind === 'tC') {
                fmt = ('0' + d.getUTCDate()).slice(-2) + ' ' + MON[d.getUTCMonth()] +
                      ' ' + d.getUTCFullYear() + ' ' +
                      ('0' + d.getUTCHours()).slice(-2) + ':' +
                      ('0' + d.getUTCMinutes()).slice(-2) + ':' +
                      ('0' + d.getUTCSeconds()).slice(-2);
            } else if (k.datekind === 'tm' || k.datekind === 'tq' ||
                       k.datekind === 'th') {
                fmt = MON[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
            } else {
                fmt = ('0' + d.getUTCDate()).slice(-2) + ' ' + MON[d.getUTCMonth()] +
                      ' ' + d.getUTCFullYear();
            }
        } else {
            if (k.general) {
                // Stata's %9.0g: six significant digits, the same as Python's
                // f"{value:g}" on the initial render.
                fmt = String(Number(result.toPrecision(6)));
            } else {
            fmt = result.toFixed(k.decimals);
            if (k.commas) {
                const parts = fmt.split('.');
                parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
                fmt = parts.join('.');
            }
            }
        }

        // Rebuild the complete Div HTML and assign to the Bokeh model property.
        // Using template literals here is fine — the JS is embedded via CustomJS
        // args (never interpolated from user input).
        kpi_div.text = (
            '<div class="db-kpi-card" style="background:' + k.bgcolor +
            '; border-radius:8px; padding:20px; ' +
            'text-align:center; border:1px solid #dee2e6; min-width:160px; min-height:110px;">' +
            '<div style="font-size:13px; color:#6c757d; margin-bottom:6px;">' + k.title + '</div>' +
            '<div style="font-size:36px; font-weight:bold; color:' + k.color + ';">' + fmt + '</div>' +
            '<div style="font-size:11px; color:#6c757d; margin-top:4px;">' + k.subtitle + '</div>' +
            '</div>'
        );
    }
}

dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);

// --- Recompute aggregate plots (histogram, kdensity) ---
// STATA's percentile ([R] summarize), not numpy's: with i = n*p/100 the
// percentile is (x_(i)+x_(i+1))/2 for integer i and x_(ceil(i)) otherwise.
// This must stay identical to _stata_percentile() in Python, because the KDE
// bandwidth is derived from it and the two curves have to coincide.
// `sorted` must be ascending.
function dash_pctl(sorted, p) {
    const n = sorted.length;
    if (n === 0) return NaN;
    const i = n * p / 100;
    const r = Math.round(i);
    if (Math.abs(i - r) < 1e-12) {
        if (r >= n) return sorted[n - 1];
        if (r <= 0) return sorted[0];
        return (sorted[r - 1] + sorted[r]) / 2;
    }
    const k = Math.ceil(i);
    return sorted[Math.min(Math.max(k, 1), n) - 1];
}
// Stata's kernels ([R] kdensity), mirroring _KERNELS in dash_render.py.
function dash_kernel(name) {
    const S5 = Math.sqrt(5);
    switch (name) {
        case 'gaussian':
            return z => Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
        case 'epan2':
            return z => (Math.abs(z) < 1 ? 0.75 * (1 - z * z) : 0);
        case 'biweight':
            return z => (Math.abs(z) < 1 ? (15 / 16) * Math.pow(1 - z * z, 2) : 0);
        case 'cosine':
            return z => (Math.abs(z) < 0.5 ? 1 + Math.cos(2 * Math.PI * z) : 0);
        case 'rectangle':
            return z => (Math.abs(z) < 1 ? 0.5 : 0);
        case 'triangle':
            return z => (Math.abs(z) < 1 ? 1 - Math.abs(z) : 0);
        case 'parzen':
            return z => {
                const a = Math.abs(z);
                if (a >= 1) return 0;
                return a <= 0.5 ? (4 / 3) - 8 * z * z + 8 * a * a * a
                                : (8 / 3) * Math.pow(1 - a, 3);
            };
        default:  // epanechnikov -- Stata's default
            return z => (Math.abs(z) < S5 ? 0.75 * (1 - z * z / 5) / S5 : 0);
    }
}
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
        // Bar HEIGHTS must be rescaled for the surviving rows -- a density
        // histogram of a filtered subset still has to integrate to 1.  The
        // bin BOUNDARIES deliberately stay put: a grid that moves as you drag
        // a filter is far more confusing than one that does not, and with
        // start()/width() now explicit the grid is the user's choice.
        const dash_scale = function (counts) {
            let total = 0;
            for (const c of counts) total += c;
            if (total <= 0) return counts;
            const mode = ac.ymode || 'density';
            if (mode === 'frequency') return counts;
            if (mode === 'fraction')  return counts.map(c => c / total);
            if (mode === 'percent')   return counts.map(c => 100 * c / total);
            return counts.map((c, i) => {
                const w = edges[i + 1] - edges[i];
                return c / (total * (w || 1));
            });
        };
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
            top:   dash_scale(counts),
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
        // DASH_KDE_RULE: silverman-0.9-min-sd-iqr/1.349
        // This MUST stay identical to _stata_kde_bandwidth() in Python
        // ([R] kdensity: w = 0.9 * m * n^(-1/5), m = min(sd, IQR/1.349)).
        // When the two disagreed, touching any filter moved the curve even
        // though no rows had been removed.
        let h;
        if (ac.bw_fixed !== null && ac.bw_fixed !== undefined) {
            h = ac.bw_fixed;          // explicit bwidth() stays fixed
        } else {
            const mu = vals.reduce((a, b) => a + b, 0) / n;
            const variance = vals.reduce((a, b) => a + (b - mu) * (b - mu), 0) / (n - 1);
            const sd = Math.sqrt(variance);
            const sorted = vals.slice().sort((a, b) => a - b);
            const q1 = dash_pctl(sorted, 25);
            const q3 = dash_pctl(sorted, 75);
            const iqr = q3 - q1;
            let m = iqr > 0 ? Math.min(sd, iqr / 1.349) : sd;
            if (!(m > 0)) m = sd;
            h = 0.9 * m * Math.pow(n, -0.2);
        }
        if (!(h > 0)) continue;
        const kfn = dash_kernel(ac.kernel || 'epanechnikov');
        const xs = ac.x_grid;
        const ys = xs.map(x => {
            let s = 0;
            for (const xi of vals) s += kfn((x - xi) / h);
            return s / (n * h);
        });
        src.data = { x: xs, y: ys };
        src.change.emit();
    }
}
"""


# ===========================================================================
# Brush/lasso KPI recompute
# ===========================================================================
#
# dash.sthlp documents update(brush) and update(both), and its
# standalone-vs-server table says brush updating works in standalone HTML.
# It did not: nothing was attached to any source's `selected' property, and
# the mode ALSO removed the KPI from the filter callback, so an update(brush)
# card was frozen at its initial value forever.  Server mode already
# implemented the same three-valued rule, so the static renderer was the
# outlier.
#
# The arithmetic is NOT repeated here.  dash_apply_kpis() is defined in
# _FILTER_JS and carries Stata's percentile rule, the date-valued-statistic
# branch and the %9.0g general format; a second copy would drift from
# _stata_percentile() in Python.  The two constants are concatenated at
# wiring time so the function is in scope.
_BRUSH_JS = """
// `brush_source' is the source the user brushed; cb_obj is its Selection.
const idx = (cb_obj && cb_obj.indices) ? cb_obj.indices : [];
const src_data = brush_source.data;
const cols = Object.keys(src_data);

// Nothing selected means every row, not no rows -- the same fallback the
// server path uses (`sel_df = _df_ref.iloc[indices] if indices else _df_ref').
// Without it, clearing a selection would blank every card instead of
// restoring it.
const sel = {};
if (idx.length === 0) {
    for (const c of cols) sel[c] = src_data[c];
} else {
    for (const c of cols) {
        const col = src_data[c];
        sel[c] = idx.map(i => col[i]);
    }
}

dash_apply_kpis(sel, kpi_config, kpi_divs, ROW_ID);
"""


def _whole_number_step(arr: "np.ndarray", span: float) -> float:
    """The slider step for a column, 1 when every value is a whole number.

    Args:
        arr:  The finite values behind the widget.
        span: ``vmax - vmin``.

    Returns:
        A positive step.
    """
    try:
        finite = np.asarray(arr, dtype=float)
        finite = finite[np.isfinite(finite)]
        if finite.size and np.all(finite == np.floor(finite)):
            return 1.0
    except (TypeError, ValueError):
        pass
    return float(span) / 100.0 or 1.0


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

        # NOT html.escape'd.  Bokeh renders a widget title as text and
        # escapes it itself, so escaping here escaped it twice:
        # label(R&D spend) displayed as "R&amp;D spend" on a dropdown while
        # the two slider paths, which do not escape, showed it correctly.
        # Same shape as the figure-title double-escape this file already
        # fixed.  Measured: the raw payload reaches the document in neither
        # path.
        _widget_title = label.strip() if label.strip() else safe_var
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
        date_kind: str = "",
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
        arr = _extract_finite(source, varname, allow_datetime=True)
        if len(arr) == 0:
            widget = Slider(title=_slider_title, start=0, end=1, value=0, step=1,
                            disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        if vmin == vmax:
            vmax = vmin + 1.0
        # A range of whole numbers steps by 1.  (vmax - vmin) / 100.0 gave
        # rep78, which takes the values 1..5, a step of 0.04, so the handle
        # stopped at 1.04, 1.08, ... and a user could not select `2'.
        vstep = _whole_number_step(arr, vmax - vmin)

        if _is_datetime_column(source, varname):
            if _is_clock_kind(date_kind):
                # Bokeh has no DatetimeSlider, and DateSlider's step is a
                # whole number of DAYS, so a clock series spanning a day had
                # one reachable notch.  A numeric Slider over epoch
                # milliseconds can step finely; the formatter makes the
                # handle read as a time rather than as a big integer.
                from bokeh.models import DatetimeTickFormatter
                widget = Slider(
                    title=_slider_title, start=vmin, end=vmax, value=vmin,
                    step=_clock_slider_step_ms(vmin, vmax),
                    format=DatetimeTickFormatter(),
                )
            else:
                from bokeh.models import DateSlider
                # Bokeh's date step is in DAYS and defaults to 1; the step
                # computed above was never passed.
                widget = DateSlider(
                    title=_slider_title, start=vmin, end=vmax, value=vmin,
                    step=_date_slider_step_days(vmin, vmax))
        else:
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
        date_kind: str = "",
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
        is_date = _is_datetime_column(source, varname)
        arr = _extract_finite(source, varname, allow_datetime=True)
        _raw_range_lbl = label.strip() if label.strip() else safe_var
        if len(arr) == 0:
            widget = RangeSlider(title=_raw_range_lbl, start=0, end=1,
                                 value=(0, 1), step=1, disabled=True)
            callback = CustomJS(args={}, code="")
            return widget, callback
        vmin, vmax = float(arr.min()), float(arr.max())
        if vmin == vmax:
            vmax = vmin + 1.0
        # A range of whole numbers steps by 1.  (vmax - vmin) / 100.0 gave
        # rep78, which takes the values 1..5, a step of 0.04, so the handle
        # stopped at 1.04, 1.08, ... and a user could not select `2'.
        vstep = _whole_number_step(arr, vmax - vmin)

        if is_date:
            # Bokeh transports datetimes as epoch milliseconds, which is the
            # same number the filter JS compares against, so the existing
            # comparison works unchanged -- verified by the round-trip test.
            if _is_clock_kind(date_kind):
                # DateRangeSlider's step is a whole number of DAYS, so a
                # clock series spanning one day had a single reachable
                # notch.  DatetimeRangeSlider steps in milliseconds.
                from bokeh.models import DatetimeRangeSlider
                widget = DatetimeRangeSlider(
                    title=_raw_range_lbl, start=vmin, end=vmax,
                    value=(vmin, vmax),
                    step=_clock_slider_step_ms(vmin, vmax))
            else:
                from bokeh.models import DateRangeSlider
                # The step computed above is in the transported unit (epoch
                # ms) and was never passed, so this kept Bokeh's default of
                # one day whatever the span.
                widget = DateRangeSlider(
                    title=_raw_range_lbl, start=vmin, end=vmax,
                    value=(vmin, vmax),
                    step=_date_slider_step_days(vmin, vmax))
        else:
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

# Stata theme names are aliases for schemes.  dash.ado writes
# build_options["theme"] using them; build_options["scheme"] takes a scheme
# name directly.
_THEME_SCHEME_MAP: "dict[str, str]" = {
    "default":    "s2color",
    "clean":      "s1color",
    "mono":       "s1mono",
    "economist":  "economist",
    "sj":         "sj",
}


def _resolve_scheme_name(master_spec: dict) -> str:
    """Return the scheme name a spec asks for, after every fallback.

    Precedence: ``scheme()``, then ``theme()``, then a ``scheme()`` written on
    a graph, then the session's own ``c(scheme)``, then ``s2color``.

    One function, because there are two renderers.  ``ServerAppBuilder``
    used to consult none of these keys -- ``grep scheme`` over the generated
    app returned nothing -- so the same command produced the user's scheme in
    standalone and Bokeh's default blue on a served page.

    Args:
        master_spec: The parsed master specification.

    Returns:
        A scheme name suitable for :meth:`SchemeParser.resolve_or_fallback`.
    """
    _build_opts: dict = master_spec.get("build_options", {})

    # A scheme() written on a single graph rather than on `dash build'.
    # `dash scatter mpg weight, scheme(economist)' takes the immediate
    # render path, which writes its own build_options with no scheme key
    # in it at all, and stores the option on the graph -- where nothing
    # read it.  The explicit option lost to the session's c(scheme), and
    # lost silently: a dashboard appeared, just not the one asked for.
    #
    # A dashboard draws one page, so several graphs cannot each have
    # their own.  The first one wins and the rest are named, rather than
    # picking one of several user intentions without saying which.
    # dash.ado emits a graph as
    #     {"plots":[...], "graph_options":{...}, "if_expr":"", "in_expr":""}
    # -- "options" is a PLOT key and appears on no graph it writes.  Reading
    # "options" here made this whole branch dead against real output: it fired
    # only for hand-built test fixtures, which is why the tests that covered
    # it passed while `dash scatter mpg weight, scheme(economist)' still drew
    # the session's scheme.  "options" is kept as a fallback so those fixtures
    # keep working.
    _graph_schemes: list = []
    for _g in master_spec.get("graphs", []):
        if not isinstance(_g, dict):
            continue
        _go = _g.get("graph_options") or _g.get("options") or {}
        if not isinstance(_go, dict):
            continue
        _gs = str(_go.get("scheme", "") or "").strip()
        if _gs:
            _graph_schemes.append(
                (str(_go.get("name", "") or _g.get("name", "")), _gs))
    _graph_scheme: str = _graph_schemes[0][1] if _graph_schemes else ""
    if len({_s for _n, _s in _graph_schemes}) > 1:
        _others = ", ".join(
            f"{_n or '?'}: {_s}" for _n, _s in _graph_schemes[1:]
        )
        warnings.warn(
            f"dash: a dashboard draws one scheme; using "
            f"{_graph_scheme!r} from the first graph and ignoring "
            f"{_others}. Set the scheme once with "
            f"`dash build, scheme()'.", UserWarning,
        )

    # Prefer explicit 'scheme' key, then 'theme', then a scheme named on
    # a graph, then the session's own c(scheme).  The session scheme is
    # what a Stata user has already chosen for every graph they draw, so
    # ignoring it made dash the one command in their session that did not
    # look like the rest.
    _raw_name: str = (
        _build_opts.get("scheme", "").strip()
        or _build_opts.get("theme", "").strip()
        or _graph_scheme
        or _build_opts.get("session_scheme", "").strip()
        or ""
    )
    # theme() takes Stata theme names, which are aliases for schemes.  A
    # name that is neither a known alias nor a known scheme is reported:
    # theme(dark) is documented in dash.sthlp, is absent from the map, and
    # used to fall through to s2color without a word.
    _lower = _raw_name.lower()
    if (_raw_name and _lower not in _THEME_SCHEME_MAP
            and _lower not in SchemeParser._BUILTIN_NAMES
            and not _raw_name.endswith(".scheme")):
        warnings.warn(
            f"dash: {_raw_name!r} is not a known theme or scheme; using "
            f"s2color. Themes: "
            f"{', '.join(sorted(_THEME_SCHEME_MAP))}. Schemes: "
            f"{', '.join(sorted(SchemeParser._BUILTIN_NAMES))}.",
            UserWarning,
        )
        _raw_name = ""
        _lower = ""
    _scheme_name: str = (
        _THEME_SCHEME_MAP.get(_lower, _raw_name) or "s2color"
    )
    return _scheme_name


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

        _build_opts: dict = self.master_spec.get("build_options", {})

        # Session confidence level, serialized from c(level) by dash.ado.  A
        # per-plot level() overrides it.  Absent (an older dash.ado against a
        # newer renderer) it falls back to Stata's factory default.
        self.default_level: float = _DEFAULT_LEVEL
        _raw_level = str(_build_opts.get("level", "")).strip()
        if _raw_level:
            try:
                _lv = float(_raw_level)
                if 0.0 < _lv < 100.0:
                    self.default_level = _lv
                else:
                    warnings.warn(
                        f"dash: c(level) of {_raw_level} is outside (0, 100); "
                        f"using {_DEFAULT_LEVEL}.", UserWarning,
                    )
            except ValueError:
                warnings.warn(
                    f"dash: could not read the confidence level {_raw_level!r}; "
                    f"using {_DEFAULT_LEVEL}.", UserWarning,
                )

        _scheme_name: str = _resolve_scheme_name(self.master_spec)
        self.scheme: SchemeParser = SchemeParser.resolve_or_fallback(
            _scheme_name, "the dashboard",
        )

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

        # Propagate Stata label metadata to the GlyphMapper so that
        # _apply_colorvar (and any future consumer) can render value labels
        # and human-readable display names in legends/labels.
        # Display-format context, so marker labels can render a date as a
        # date rather than as the underlying Stata value.
        self.mapper.date_vars         = dict(getattr(self, "date_vars", {}))
        self.mapper.numeric_formats   = dict(getattr(self, "numeric_formats", {}))
        self.mapper.variable_labels   = self.variable_labels
        self.mapper.value_labels      = self.value_labels
        self.mapper.value_label_names = self.value_label_names

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

        # String variable flags.
        # Real jsonio emits "variableIsString"; "variableTypeIsString" is what
        # StataAllToJSON's field list advertises and what dash read until now,
        # so string detection never actually ran in production -- every string
        # column was coerced to NaN.  Both keys are honoured.
        type_is_string = dict(stata_json.get("variableTypeIsString", {}) or {})
        type_is_string.update(stata_json.get("variableIsString", {}) or {})
        self.string_vars = {k for k, v in type_is_string.items() if v}

        # Stata display formats, carried in the spec because jsonio cannot
        # emit them.  Absent (an older dash.ado against a newer renderer) this
        # is empty and every column takes exactly the path it took before.
        formats = self.master_spec.get("build_options", {}).get("formats", {})
        if not isinstance(formats, dict):
            formats = {}
        self.formats: dict[str, str] = {str(k): str(v)
                                        for k, v in formats.items()}
        self.date_vars: dict[str, str] = {}
        self.numeric_formats: dict[str, str] = {}

        for col in self.df.columns:
            if col in self.string_vars:
                continue
            kind = _stata_date_kind(self.formats.get(col))
            if kind is None:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                pattern = _stata_numeric_pattern(self.formats.get(col))
                if pattern is not None:
                    self.numeric_formats[col] = self.formats[col]
                continue

            raw = self.df[col]
            numeric = pd.to_numeric(raw, errors="coerce")
            if numeric.notna().any() or raw.isna().all():
                converted = _stata_dates_to_datetime(numeric, kind)
            else:
                # Legacy transport: jsonio renders a %t* variable THROUGH its
                # display format and emits a string ("02jan2001"), so a spec
                # from an older dash.ado carries text here.  Coercing it to
                # NaN drops every row of the dataset, which is how
                # `dash line close date` came to produce an empty dashboard.
                converted = pd.to_datetime(raw.astype(str).str.strip(),
                                            errors="coerce")
                if converted.isna().all() and raw.notna().any():
                    warnings.warn(
                        f"dash: variable '{col}' has display format "
                        f"{self.formats.get(col)!r} but arrived as text this "
                        f"renderer could not read as a date; it is shown as "
                        f"missing. Re-run with a current dash.ado.",
                        UserWarning,
                    )
            self.df[col] = pd.Series(converted).to_numpy()
            self.date_vars[col] = kind

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

    # KPI statistics whose RESULT is itself a date when the variable is one.
    # count and dcount are counts; sd is a duration; sum is meaningless.
    _DATE_VALUED_STATS = frozenset({"mean", "min", "max", "median", "p50",
                                    "p25", "p75"})

    def _kpi_column(self, col: "pd.Series", stat: str, varname: str
                    ) -> "pd.Series":
        """Coerce a KPI column to something the statistic can be taken of.

        A datetime column becomes epoch milliseconds -- the representation
        Bokeh itself uses -- so min, max, mean and the percentiles all work;
        :meth:`_format_kpi_value` turns the answer back into a date.

        Args:
            col:     The raw column.
            stat:    The requested statistic.
            varname: Column name, for the warning text.

        Returns:
            A numeric Series.
        """
        if not pd.api.types.is_datetime64_any_dtype(col):
            return col
        if str(stat).lower().strip() == "sum":
            warnings.warn(
                f"dash: sum({varname}) adds up dates, which has no meaning. "
                f"The result is shown as a number of milliseconds since "
                f"01jan1960.",
                UserWarning,
            )
        return col.dropna().astype("datetime64[ms]").astype("int64")

    @staticmethod
    def _kpi_statistic(col: "pd.Series", stat: str) -> float:
        """Compute one KPI statistic the way Stata computes it.

        Two places computed these and both used pandas' defaults.  The
        percentile rule is the one that matters: Stata uses Hyndman-Fan
        **type 2** -- ``j = N*p/100``; an integer ``j`` gives
        ``(x_j + x_{j+1})/2``, otherwise ``x_ceil(j)`` -- and pandas defaults
        to type 7.  They disagree on real data: p75 of ``mpg`` in
        ``sysuse auto`` is 25 in Stata and 24.75 in pandas.  The correct
        implementation already existed in this module as
        ``_stata_percentile``; the KPI paths simply never called it.

        Variance and standard deviation use N-1, and skewness is the biased
        m3/m2^1.5, both matching Stata.

        Args:
            col:  The column, already reduced to non-missing values.
            stat: The statistic name.

        Returns:
            The value.

        Raises:
            ValueError: for an unknown statistic.
        """
        s = str(stat).lower().strip()
        if s == "count":
            return float(len(col))
        if s == "dcount":
            return float(col.nunique())
        if len(col) == 0:
            return float("nan")
        if s == "mean":
            return float(col.mean())
        if s == "sum":
            return float(col.sum())
        if s == "min":
            return float(col.min())
        if s == "max":
            return float(col.max())
        if s == "sd":
            return float(col.std(ddof=1))
        if s == "var":
            return float(col.var(ddof=1))
        if s == "cv":
            m = float(col.mean())
            return float(col.std(ddof=1) / m) if m else float("nan")
        if s == "skewness":
            # Stata's biased m3 / m2^1.5, not the sample-corrected form.
            v = col.to_numpy(dtype=float)
            m = v.mean()
            m2 = ((v - m) ** 2).mean()
            m3 = ((v - m) ** 3).mean()
            return float(m3 / m2 ** 1.5) if m2 > 0 else float("nan")

        srt = np.sort(col.to_numpy(dtype=float))
        if s == "iqr":
            return float(_stata_percentile(srt, 75)
                         - _stata_percentile(srt, 25))
        if s in ("median", "p50"):
            return float(_stata_percentile(srt, 50))
        m_p = re.fullmatch(r"p(\d{1,2}(?:\.\d+)?)", s)
        if m_p:
            return float(_stata_percentile(srt, float(m_p.group(1))))
        raise ValueError(f"Unknown KPI statistic: '{stat}'")

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
        col = self._kpi_column(col, stat, varname)
        return self._kpi_statistic(col, stat)

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
        col = self._kpi_column(col, stat, varname)
        return self._kpi_statistic(col, stat)

    def _effective_kpi_fmt(self, kpi: dict, varname: str) -> str:
        """The format a KPI is actually displayed with.

        The initial render fell back to the variable's Stata display format
        when ``fmt()`` was absent, and the filter callback fell back to
        ``%9.0f``, so a card that read 21.2973 became 21 the first time any
        filter moved.  Both paths resolve the format here.

        Args:
            kpi:     The KPI spec.
            varname: The variable the statistic is taken of.

        Returns:
            A Stata format string, possibly empty.
        """
        explicit = str(kpi.get("fmt", "") or "").strip()
        if explicit:
            return explicit
        own = getattr(self, "numeric_formats", {}).get(varname, "") or ""
        if own:
            return own
        # Neither given: Stata's own default display, %9.0g, which shows six
        # significant digits.  Both paths implement it -- the callback used
        # %9.0f (no decimals at all) and the initial render printed the raw
        # float, so a card read 21.2972972972973 and became 21 the first time
        # a filter moved.
        return "%9.0g"

    def _format_kpi_value(self, value: float, fmt_str: str,
                          varname: str = "", stat: str = "") -> str:
        """Format a KPI value using a Stata format string.

        Supports standard Stata numeric formats: %w.df, %w.dfc (comma).  A
        statistic of a DATE variable whose result is itself a date is
        rendered as a date rather than as the raw Stata value -- ``dash kpi
        max(date)`` on sp500 used to read 15340.

        Args:
            value:   Numeric value to format.
            fmt_str: Stata format string, e.g. "%9.1f" or "%12.0fc".
            varname: The variable the statistic was taken of.
            stat:    The statistic, which decides whether a date variable
                     produces a date.

        Returns:
            Formatted string (stripped of leading/trailing whitespace).
        """
        kind = getattr(self, "date_vars", {}).get(varname)
        if kind and str(stat).lower().strip() in self._DATE_VALUED_STATS:
            return self._format_date_value(float(value), kind)

        # No explicit fmt(): fall back to the variable's Stata display
        # format, exactly as _effective_kpi_fmt resolves it for the callback.
        if not fmt_str.strip():
            own = getattr(self, "numeric_formats", {}).get(varname, "")
            if own:
                return _format_stata_numeric(value, own).strip()

        if fmt_str.strip() in ("", "%9.0g"):
            # Stata's default display: six significant digits.  The callback
            # does the same via toPrecision(6), so the card does not change
            # shape when a filter moves.
            return f"{float(value):g}"

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
        # The row's position in the primary frame, so the filter callback can
        # mask this source by identity however short or reordered it is.
        data_dict[_ROW_ID_COLUMN] = self._row_ids_for(frame)
        return ColumnDataSource(data=data_dict)

    def _register_view_filter(self, source, bool_filter, member_ids) -> None:
        """Remember a CDSView's BooleanFilter and the rows it selects.

        A linked by() graph draws its panels as views over ONE shared source,
        with booleans sized to the unfiltered frame.  The filter callback
        replaces that source's data with fewer rows and never touched the
        booleans, so after any filter move each panel masked the wrong rows.

        Args:
            source:      The ColumnDataSource the view is over.
            bool_filter: The view's BooleanFilter.
            member_ids:  Row identities belonging to this view.
        """
        if not hasattr(self, "_view_filters"):
            self._view_filters = []
        self._view_filters.append((source, bool_filter, list(member_ids)))

    def _view_filter_args(self, ordered_sources: list) -> list:
        """Build the callback's ``view_filters`` argument.

        Args:
            ordered_sources: The sources passed as ``all_graph_sources``; a
                view is indexed against this list so the JS can find the rows
                its source kept.

        Returns:
            A list of ``{"filter": BooleanFilter, "src_index": int,
            "member_ids": [...]}``.
        """
        out = []
        for source, bool_filter, member_ids in getattr(self, "_view_filters",
                                                        []):
            try:
                idx = ordered_sources.index(source)
            except ValueError:
                continue
            out.append({"filter": bool_filter, "src_index": idx,
                        "member_ids": member_ids})
        return out

    def _kpi_qualifier_row_ids(self, kpi_def: dict) -> "list[int] | None":
        """Row identities a KPI's own if/in qualifier selects.

        Returns ``None`` when the KPI carries no qualifier, so the caller can
        tell "no restriction" from "a restriction that happens to be empty" --
        an empty list must blank the card, not show every row.

        Args:
            kpi_def: The KPI specification, with optional ``if_expr`` /
                ``in_expr`` keys.

        Returns:
            One integer per qualifying row, or None if unqualified.
        """
        if not (str(kpi_def.get("if_expr", "") or "").strip()
                or str(kpi_def.get("in_expr", "") or "").strip()):
            return None
        try:
            return self._row_ids_for(self._apply_graph_filter(kpi_def))
        except (ValueError, KeyError, TypeError):
            # _apply_graph_filter already warns; a qualifier that cannot be
            # applied must not silently become "every row" in the browser
            # while the initial render used the full frame too.
            return None

    def _row_ids_for(self, frame: "pd.DataFrame") -> "list[int]":
        """Return each row's position in the primary frame.

        Derived sources are slices of ``self.df`` and keep its index, so the
        index is the identity.  A frame that somehow does not align falls
        back to its own positions, which is no worse than the positional
        masking this replaces.

        Args:
            frame: The frame this source is being built from.

        Returns:
            One integer per row.
        """
        try:
            pos = {idx: i for i, idx in enumerate(self.df.index)}
            return [int(pos.get(idx, i)) for i, idx in enumerate(frame.index)]
        except (AttributeError, TypeError):
            return list(range(len(frame)))

    @staticmethod
    def _df_for_source(source: ColumnDataSource) -> pd.DataFrame:
        """Return a DataFrame view of a ColumnDataSource's columns.

        Used to re-filter a shared source for a single plot layer that carries
        its own if/in qualifier, without disturbing the other layers.
        """
        return pd.DataFrame({k: list(v) for k, v in source.data.items()})

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
            # Translate Stata's qualifier idioms -- missing(), inlist(),
            # inrange() and the "< ." missing test -- into plain comparisons
            # BEFORE validation, so the whitelist is unchanged and still sees
            # the whole expression.
            pandas_expr = _stata_if_to_pandas(if_expr)

            # Security: validate against AST whitelist before query execution.
            # _validate_if_expr rejects @-variable references (RCE vector),
            # function calls, attribute access, and all non-comparison nodes.
            # This replaces the old regex blacklist which did not block @.
            if not _validate_if_expr(pandas_expr, df.columns):
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
            # label() had no regex here at all, so the key the widget-title
            # resolver reads FIRST was simply absent and every filter fell
            # back to the variable name.  dash.ado did not reject the
            # suboption either, so the user got silence rather than an error.
            # The optional quotes are Stata's: label("Curb weight") and
            # label(Curb weight) both reach here verbatim.
            m_label = _re.search(r'\blabel\(\s*"?([^)"]*)"?\s*\)',
                                 part, _re.IGNORECASE)
            ftype = m_type.group(1).strip().lower() if m_type else "dropdown"
            excl = m_excl.group(1).split() if m_excl else []
            flabel = m_label.group(1).strip() if m_label else ""
            result.append({"varname": fvar, "type": ftype, "exclude": excl,
                           "label": flabel})
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
            # All facet-key values are missing (by_missing=False) — return an
            # empty-DataFrame group so callers create a zero-row source rather
            # than falling back to the full original dataset.
            return [("", work_df.copy())]

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

        # Defensive fallback: if the groupby loop produced no groups (should
        # not happen given the dropna / by_missing logic above), return an
        # empty-row group rather than the original full dataset.
        return groups if groups else [("", work_df.copy())]

    def _format_date_value(self, value, kind: str) -> str:
        """Render one value of a date variable the way its format implies.

        Args:
            value: A Timestamp, datetime64 or epoch-millisecond number.
            kind:  One of :data:`_STATA_DATE_KINDS`.

        Returns:
            The formatted date, or ``str(value)`` if it cannot be read.
        """
        return _format_date_value_standalone(value, kind)

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
            # A by() on a date variable produced facet titles reading the
            # underlying Stata value.
            _kind = getattr(self, "date_vars", {}).get(var)
            if _kind:
                parts.append(self._format_date_value(val, _kind))
                continue
            _numfmt = getattr(self, "numeric_formats", {}).get(var, "")
            if _numfmt:
                parts.append(_format_stata_numeric(val, _numfmt).strip())
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

    # Plot types whose legend key Stata writes as "Fitted values" rather
    # than as the y variable.  Measured: twoway (scatter mpg weight)
    # (lfit mpg weight) has keys ["Mileage (mpg)", "Fitted values"].
    _FIT_TYPES = frozenset({
        "lfit", "qfit", "fpfit", "lpoly", "lowess", "mband", "mspline",
        "function",
    })
    # Plot types that produce TWO keys from one plot: the band and the line.
    # Measured: twoway lfitci mpg weight has keys ["95% CI", "Fitted values"].
    _CI_TYPES = frozenset({"lfitci", "qfitci", "lpolyci", "fpfitci"})

    def _legend_key(self, plot: dict) -> str:
        """The legend key Stata would write for one plot layer.

        Stata labels a data series with the variable LABEL, not the variable
        name -- ``scatter mpg weight`` keys read "Mileage (mpg)".  dash
        labelled every series with the raw y-variable name, so a scatter and
        its fit line collided into a single merged key.

        Args:
            plot: One plot spec.

        Returns:
            The key text.
        """
        ptype = str(plot.get("type", "")).lower()
        if ptype in self._FIT_TYPES or ptype in self._CI_TYPES:
            return "Fitted values"
        yvar = (plot.get("yvar", "") or plot.get("var", "")
                or plot.get("yvar1", ""))
        return self._axis_label(yvar) if yvar else ptype

    def _rebuild_legend(self, fig, plot_renderers: list, graph_opts: dict
                        ) -> None:
        """Give the figure Stata's legend keys, and Stata's rule for drawing one.

        ``twoway`` draws a legend **if and only if the graph has two or more
        keys**.  One key, no legend, whatever else is passed:
        ``legend(position(6))`` on a one-key plot draws nothing, and only
        ``legend(on)`` forces one.  Measured over 55 probes; see
        ``findings.legend_rule`` in test/fixtures/axis_truth.json.

        dash passed ``legend_label=<yvar>`` from every glyph, so a
        single-series plot always got a legend ``twoway`` would not draw --
        and two layers of the same y variable merged into one key.

        Args:
            fig:             The figure, with every glyph already added.
            plot_renderers:  ``[(plot_spec, [renderer, ...]), ...]``.
            graph_opts:      Graph-level options.
        """
        from bokeh.models import Legend, LegendItem

        legend_opt = str(graph_opts.get("legend", "") or "")
        if not fig.legend:
            return

        # A discrete colorvar() builds its colour key as a Legend too, and on
        # a single-plot figure it is fig.legend[0].  This method used to take
        # that one, overwrite its per-category items with a single key
        # labelled with the y variable, and then hide it under Stata's
        # fewer-than-two-keys rule -- coloured points and no way to read
        # them.  A colour key is not a series key, so it is kept out of the
        # rebuild entirely.
        #
        # The chrome loop below still runs over EVERY legend: skipping it
        # when the colour key is the only legend would silently reinstate a
        # Bokeh-default legend on a themed plot region, which is a bug this
        # file already fixed once.
        _cv_legends = [l for l in fig.legend
                       if str(getattr(l, "name", "") or "")
                       == _COLORVAR_LEGEND_NAME]
        _plot_legends = [l for l in fig.legend if l not in _cv_legends]

        legend = _plot_legends[0] if _plot_legends else None
        if legend is not None and plot_renderers:
            items: list = []
            for plot, rends in plot_renderers:
                # The dummy swatch renderers a colorvar() builds are not
                # plot layers and must not become series keys.
                rends = [r for r in rends if r in fig.renderers
                         and not str(getattr(r, "name", "") or "")
                         .startswith("_clegend_")]
                if not rends:
                    continue
                ptype = str(plot.get("type", "")).lower()
                if ptype in self._CI_TYPES and len(rends) >= 2:
                    # The band is added alongside the line; Stata keys them
                    # separately, and the band's key carries the level.
                    lvl = _resolve_level(plot.get("options", {}) or {},
                                         getattr(self, "default_level",
                                                 _DEFAULT_LEVEL))
                    lvl_txt = (f"{lvl:g}")
                    band = [r for r in rends
                            if type(getattr(r, "glyph", None)).__name__
                            in ("VArea", "Band", "Patch")]
                    line = [r for r in rends if r not in band]
                    if band:
                        items.append(LegendItem(label={"value": f"{lvl_txt}% CI"},
                                                renderers=band))
                    if line:
                        items.append(LegendItem(label={"value": "Fitted values"},
                                                renderers=line))
                    continue
                items.append(LegendItem(
                    label={"value": self._legend_key(plot)}, renderers=rends))
            if items:
                legend.items = items

        # order() -- 1-based, and it may also DROP keys.
        m_order = re.search(r"\border\s*\(([^)]*)\)", legend_opt)
        if m_order:
            wanted = [int(t) for t in re.findall(r"\d+", m_order.group(1))]
            src = list(legend.items)
            legend.items = [src[i - 1] for i in wanted
                            if 1 <= i <= len(src)]

        # ---- Stata's clock positions -------------------------------
        # 12 o'clock is straight up, 3 is right, 6 is down, 9 is left.  The
        # measured placements group into the four sides; ring(0) keeps the
        # legend inside the plot region instead of in a side panel.
        _CLOCK_SIDE = {
            11: "above", 12: "above", 1: "above",
            2: "right", 3: "right", 4: "right",
            5: "below", 6: "below", 7: "below",
            8: "left", 9: "left", 10: "left",
        }
        _CLOCK_INSIDE = {
            11: "top_left", 12: "top_center", 1: "top_right",
            2: "top_right", 3: "center_right", 4: "bottom_right",
            5: "bottom_right", 6: "bottom_center", 7: "bottom_left",
            8: "bottom_left", 9: "center_left", 10: "top_left",
        }
        # The scheme's own legend chrome, applied BEFORE the user's
        # legend() options so an explicit size() still wins.
        # legend_bg_color and legend_border_color were parsed and had zero
        # consumers, so an economist dashboard drew a Bokeh-default legend
        # on top of an economist plot region.
        for leg in fig.legend:
            if self.scheme.legend_bg_color:
                leg.background_fill_color = self.scheme.legend_bg_color
            if self.scheme.legend_border_color:
                leg.border_line_color = self.scheme.legend_border_color
            if self.scheme.text_font_size:
                leg.label_text_font_size = self.scheme.text_font_size

        m_pos = re.search(r"\b(?:position|pos)\s*\(\s*(\d+)\s*\)",
                          legend_opt)
        m_ring = re.search(r"\bring\s*\(\s*(\d+)\s*\)", legend_opt)
        inside = bool(m_ring) and m_ring.group(1) == "0"
        if m_pos and legend is not None:
            clock = int(m_pos.group(1))
            if inside:
                legend.location = _CLOCK_INSIDE.get(clock, "top_right")
            else:
                side = _CLOCK_SIDE.get(clock, "right")
                self._move_legend(fig, legend, side)
                legend.orientation = ("horizontal"
                                      if side in ("above", "below")
                                      else "vertical")

        m_size = re.search(r"\bsize\s*\(\s*([^)]+?)\s*\)", legend_opt)
        if m_size:
            try:
                _px = (f"{OptionTranslator.translate_msize(m_size.group(1)):g}"
                       "px")
                # Every legend on the figure, including a colour key: the
                # user asked for a legend text size, not for a plot-legend
                # text size.
                for leg in fig.legend:
                    leg.label_text_font_size = _px
            except (ValueError, TypeError):
                pass

        forced_on = bool(re.search(r"\bon\b", legend_opt))
        turned_off = bool(re.search(r"\boff\b", legend_opt))
        n_keys = len(legend.items) if legend is not None else 0

        # Stata's rule governs the SERIES key.  A colour key is separate --
        # Stata suppresses it with clegend(), not legend() -- so it stays
        # visible, and a one-series colorvar plot keeps the only legend that
        # tells the reader what the colours mean.
        _show = not (turned_off or (n_keys < 2 and not forced_on))
        for leg in _plot_legends:
            leg.visible = _show
        for leg in _cv_legends:
            leg.visible = True

    def _apply_axis_spec(self, fig, axis_obj, grid_obj, spec: dict,
                         varname: str = "") -> None:
        """Apply a parsed ``axis_label`` spec to one axis.

        Args:
            fig:       The figure (for its data ranges).
            axis_obj:  ``fig.xaxis`` or ``fig.yaxis``.
            grid_obj:  The matching grid, for ``grid``/``nogrid``.
            spec:      The output of :meth:`_parse_axis_spec`.
            varname:   The variable on this axis, so a tick format can fall
                       back to its Stata display format.
        """
        from bokeh.models.tickers import FixedTicker, BasicTicker
        from bokeh.models.formatters import (CustomJSTickFormatter,
                                             NumeralTickFormatter)

        mode = spec["mode"]
        if mode == "none":
            # Zero ticks BY INTENT.  It used to produce zero by accident,
            # because every token was dropped.  Measured: Stata's
            # xlabel(none) also removes the gridlines.
            axis_obj.ticker = FixedTicker(ticks=[])
            for g in grid_obj:
                g.grid_line_color = None
        elif mode == "minmax":
            col = self.df[varname] if varname in getattr(
                self.df, "columns", []) else None
            if col is not None:
                vals = pd.to_numeric(col, errors="coerce").dropna()
                if len(vals):
                    axis_obj.ticker = FixedTicker(
                        ticks=[float(vals.min()), float(vals.max())])
        elif mode == "count":
            # Stata's #N is a SUGGESTION -- measured, xlabel(#10) on weight
            # yields eight ticks.  Bokeh's desired_num_ticks means the same
            # thing, so the option maps onto it rather than onto a fixed list.
            axis_obj.ticker = BasicTicker(desired_num_ticks=spec["count"])
        elif mode == "explicit" and spec["ticks"]:
            axis_obj.ticker = FixedTicker(ticks=spec["ticks"])
            if spec["labels"]:
                safe = {str(k): html.escape(str(v))
                        for k, v in spec["labels"].items()}
                axis_obj.formatter = CustomJSTickFormatter(
                    code=f"const m = {json.dumps(safe)}; "
                         "return m[String(tick)] || String(tick);")
                axis_obj.major_label_overrides = {
                    float(k): v for k, v in spec["labels"].items()}

        fmt = spec["format"] or getattr(self, "numeric_formats", {}).get(
            varname, "")
        if fmt:
            pattern = _stata_numeric_pattern(fmt)
            if pattern is not None:
                axis_obj.formatter = NumeralTickFormatter(format=pattern)
            elif spec["format"] and _stata_date_kind(fmt) is None:
                warnings.warn(
                    f"dash: axis format({spec['format']}) is not a numeric "
                    f"display format dash reproduces; the ticks are "
                    f"unformatted.", UserWarning,
                )

        if spec["labsize"]:
            try:
                axis_obj.major_label_text_font_size = (
                    f"{OptionTranslator.translate_msize(spec['labsize']):g}px")
            except (ValueError, TypeError):
                warnings.warn(
                    f"dash: labsize({spec['labsize']}) is not a recognised "
                    f"text size; ignoring it.", UserWarning,
                )
        if spec["angle"] is not None:
            axis_obj.major_label_orientation = spec["angle"]
        if spec["grid"] is not None:
            for g in grid_obj:
                if spec["grid"]:
                    if g.grid_line_color is None:
                        g.grid_line_color = "#e5e5e5"
                else:
                    g.grid_line_color = None

    @staticmethod
    def _move_legend(fig, legend, side: str) -> None:
        """Move an existing Legend into one of the figure's side panels.

        Args:
            fig:    The figure.
            legend: The Legend model already attached to it.
            side:   ``"above"``, ``"below"``, ``"left"`` or ``"right"``.
        """
        for container in (fig.center, fig.above, fig.below, fig.left,
                          fig.right):
            try:
                if legend in container:
                    container.remove(legend)
            except (TypeError, ValueError):
                pass
        fig.add_layout(legend, side)

    def _resolve_aspect_ratio(self, graph_opts: dict) -> "float | None":
        """Return Bokeh's width/height ratio for this figure.

        Stata expresses proportions three ways and dash honoured none of
        them.  Note the inversion: **Stata's aspectratio() is
        height/width**, and Bokeh's ``aspect_ratio`` is **width/height**.
        dash passed the value straight through, so every request came out
        upside down -- ``aspectratio(0.5)`` asks for a plot region half as
        tall as it is wide, and dash drew one twice as tall as it is wide.
        Measured on a 600x600 export: ``aspectratio(0.25)`` yields a plot
        region 542x152, i.e. h/w = 0.28.

        Args:
            graph_opts: The graph's options.

        Returns:
            A width/height ratio, or None to leave Bokeh's default.
        """
        xs = _stat_option_float(graph_opts, "xsize", None, "graph", lo=0.0)
        ys = _stat_option_float(graph_opts, "ysize", None, "graph", lo=0.0)
        for name, val in (("xsize", xs), ("ysize", ys)):
            if val is not None and val <= 0:
                # Stata returns r(198) for xsize(0) and xsize(-3).
                warnings.warn(
                    f"dash: {name}({graph_opts.get(name)}) must be a positive "
                    f"number of inches; ignoring it.", UserWarning,
                )
                if name == "xsize":
                    xs = None
                else:
                    ys = None

        # Either one alone keeps the scheme's value for the other, exactly as
        # Stata does: xsize(9) under stcolor gives 4.5 x 9.
        sx = getattr(self.scheme, "graphsize_x", None)
        sy = getattr(self.scheme, "graphsize_y", None)
        if xs is not None or ys is not None:
            w = xs if xs is not None else sx
            h = ys if ys is not None else sy
            if w and h:
                return float(w) / float(h)

        raw_ar = str(graph_opts.get("aspectratio", "") or "").strip()
        if raw_ar:
            ar = _stat_option_float(graph_opts, "aspectratio", None, "graph",
                                    lo=0.0)
            if ar is None or ar <= 0:
                warnings.warn(
                    f"dash: aspectratio({raw_ar}) must be a positive number; "
                    f"ignoring it.", UserWarning,
                )
            else:
                return 1.0 / float(ar)

        if sx and sy:
            return float(sx) / float(sy)
        return None

    def _figure_date_kind(
        self, plots: list, key: str, fallback: str,
    ) -> "str | None":
        """Return the date kind of the variable on one axis, or None.

        Every plot on the figure has to agree: a graph overlaying a date
        series and a numeric one cannot have a date axis, and silently
        picking the first plot's answer would misplace the other.

        Args:
            plots:    The figure's plot specs.
            key:      ``"xvar"`` or ``"yvar"``.
            fallback: The variable to use when a plot does not name one.

        Returns:
            The date kind, or ``None``.
        """
        if not getattr(self, "date_vars", None):
            return None
        kinds = set()
        for plot in plots or []:
            name = plot.get(key, "") or (
                plot.get("var", "") if key == "yvar" else "") or fallback
            if not name:
                continue
            kinds.add(self.date_vars.get(name))
        if not kinds:
            return None
        if len(kinds) > 1 or None in kinds:
            return None
        return kinds.pop()

    def _axis_label(self, varname: str) -> str:
        """Return the axis label for *varname*, using variable labels if available."""
        return self.variable_labels.get(varname, varname)

    @staticmethod
    def _parse_axis_spec(raw: str) -> dict:
        """Parse Stata's full ``axis_label`` grammar.

        Handles a numlist (including the ``a(b)c`` increment form), ``#N``,
        ``minmax``, ``none``, explicit ``value "label"`` pairs, and the
        sub-options ``format()``, ``labsize()``, ``angle()``, ``grid`` and
        ``nogrid``.  Everything but the quoted-label handling and ``angle()``
        used to be discarded: ``xlabel(#10)``, ``xlabel(minmax)``,
        ``xlabel(1990(5)2020)`` and ``ylabel(, format(%9.0fc))`` were all
        ACCEPTED and all produced zero ticks.

        Args:
            raw: The raw option value.

        Returns:
            A dict with keys ``mode`` (one of ``"default"``, ``"explicit"``,
            ``"count"``, ``"minmax"``, ``"none"``), ``ticks``, ``count``,
            ``labels``, ``format``, ``labsize``, ``angle`` and ``grid``.
        """
        out: dict = {"mode": "default", "ticks": [], "count": None,
                     "labels": {}, "format": None, "labsize": None,
                     "angle": None, "grid": None}
        if not raw or not str(raw).strip():
            return out
        text = str(raw)

        out["angle"] = _parse_axis_angle(text)
        m = re.search(r"\bformat\s*\(\s*([^)]+?)\s*\)", text, re.I)
        if m:
            out["format"] = m.group(1).strip()
        m = re.search(r"\blabsize\s*\(\s*([^)]+?)\s*\)", text, re.I)
        if m:
            out["labsize"] = m.group(1).strip()
        if re.search(r"\bnogrid\b", text, re.I):
            out["grid"] = False
        elif re.search(r"\bgrid\b", text, re.I):
            out["grid"] = True

        # Strip every recognised sub-option so only the numlist remains.
        head = re.sub(r"\b(?:format|labsize|angle|labcolor|labgap|tlength|"
                      r"labstyle|tstyle|tposition)\s*\([^)]*\)", " ",
                      text, flags=re.I)
        head = re.sub(r"\b(?:no)?grid\b", " ", head, flags=re.I)
        # Only a comma that INTRODUCES SUB-OPTIONS separates; Stata also
        # accepts a comma-separated numlist, so xlabel(1,3,5) must survive.
        m_sub = re.search(r",\s*(?=[A-Za-z_])", head)
        if m_sub:
            head = head[:m_sub.start()]
        head = head.strip()

        if re.fullmatch(r"none", head, re.I):
            out["mode"] = "none"
            return out
        if re.fullmatch(r"minmax", head, re.I):
            out["mode"] = "minmax"
            return out
        m = re.fullmatch(r"#\s*(\d+)", head)
        if m:
            out["mode"] = "count"
            out["count"] = max(1, int(m.group(1)))
            return out

        # a(b)c increment form, possibly repeated and mixed with bare values.
        ticks: list[float] = []
        rest = head
        for m in re.finditer(
                r"(-?[\d.eE+]+)\s*\(\s*(-?[\d.eE+]+)\s*\)\s*(-?[\d.eE+]+)",
                head):
            try:
                a, b, c = (float(m.group(1)), float(m.group(2)),
                           float(m.group(3)))
            except ValueError:
                continue
            if b == 0:
                continue
            n_steps = int(math.floor((c - a) / b + 1e-9))
            ticks.extend(a + b * i for i in range(max(0, n_steps) + 1))
            rest = rest.replace(m.group(0), " ")

        bare_ticks, labels = DashRenderer._parse_axis_label_opt(rest)
        ticks.extend(bare_ticks)
        if ticks:
            out["mode"] = "explicit"
            out["ticks"] = sorted(set(ticks))
            out["labels"] = labels
        return out

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

    def _apply_nonselection_dimming(self, fig) -> None:
        """Dim a linked figure's non-selected points to dash's own alpha.

        Bokeh attaches a nonselection glyph of its own at alpha 0.1, so
        brushing does dim -- but dash's chosen ``_NONSELECTION_ALPHA`` was
        applied only in ``_build_figures``, which ``render()`` never called,
        so the constant the package documents had never reached a shipped
        dashboard.

        Args:
            fig: A figure belonging to a link group.
        """
        for renderer in fig.renderers:
            ns = getattr(renderer, "nonselection_glyph", None)
            if ns is None:
                continue
            if hasattr(ns, "fill_alpha"):
                ns.fill_alpha = _NONSELECTION_ALPHA
            if hasattr(ns, "line_alpha"):
                ns.line_alpha = _NONSELECTION_ALPHA

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

        # A graph-level scheme() was parsed, escaped into graph_options and
        # then never read, so `dash scatter ..., scheme(economist)' drew the
        # build's scheme and returned rc 0.  Swap it in for the duration of
        # this figure -- both here and on the mapper, which is what colours
        # the glyphs.
        _gscheme = str(graph_opts.get("scheme", "") or "").strip()
        if _gscheme:
            _saved_scheme, _saved_mapper = self.scheme, self.mapper.scheme
            self.scheme = SchemeParser.resolve_or_fallback(
                _gscheme, f"graph {graph_opts.get('name', '') or '(unnamed)'}")
            self.mapper.scheme = self.scheme
            try:
                return self._make_figure_body(graph_spec, source, facet_view)
            finally:
                self.scheme, self.mapper.scheme = _saved_scheme, _saved_mapper
        return self._make_figure_body(graph_spec, source, facet_view)

    def _make_figure_body(
        self,
        graph_spec: dict,
        source: ColumnDataSource,
        facet_view: "Optional[Any]" = None,
    ) -> Any:
        """The body of :meth:`_make_figure`, run under the graph's scheme."""
        graph_opts = graph_spec.get("graph_options", {})
        plots = graph_spec.get("plots", [])

        # Determine axis variables from the first plot layer
        xvar = plots[0].get("xvar", "") if plots else ""
        yvar = plots[0].get("yvar", "") if plots else ""

        # Resolve axis labels: user-specified xtitle/ytitle take priority
        raw_xtitle = graph_opts.get("xtitle", "")
        raw_ytitle = graph_opts.get("ytitle", "")
        # Canvas text, NOT html: Bokeh draws a figure title and axis labels
        # as glyphs, so escaping made title("R&D spend") display as
        # "R&amp;D spend".  _axis_label() never escaped the variable labels it
        # returns and was already correct -- that is the evidence that the
        # escaping here was the bug rather than the protection.  Everything
        # that genuinely reaches the DOM is still escaped.
        x_label = raw_xtitle if raw_xtitle else self._axis_label(xvar)
        y_label = raw_ytitle if raw_ytitle else self._axis_label(yvar)

        # Enable WebGL for large datasets
        n_rows = len(self.df)
        backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"

        # Figure proportions.  Precedence, documented in dash.sthlp:
        #   1. xsize()/ysize()  2. aspectratio()  3. the scheme's graphsize
        # Nothing set any of these before: every figure was emitted with
        # sizing_mode="stretch_width" and Bokeh's default height, so there was
        # no way at all -- option, scheme or data -- to influence proportions.
        aspect_ratio = self._resolve_aspect_ratio(graph_opts)

        # Log scale and reverse options.
        # Determine axis types BEFORE creating the figure so that we only ever
        # call bokeh_figure() once.  Previously, log scale caused a second
        # bokeh_figure() call that discarded all styling applied after the first
        # call (scheme, bgcolor, plotbgcolor, plotregion, graphregion).
        _xs_log, _xs_rev = _parse_scale_opt(graph_opts.get("xscale", ""))
        _ys_log, _ys_rev = _parse_scale_opt(graph_opts.get("yscale", ""))

        fig_kwargs = dict(
            title=_parse_textbox_opt(graph_opts.get("title", ""))[0],
            x_axis_label=x_label,
            y_axis_label=y_label,
            output_backend=backend,
            sizing_mode="stretch_width",
            # With an aspect ratio and a stretched width, a square figure in
            # a full-width cell on a 1440px display would be 1400px tall.
            # The ratio is honoured up to this height so a dashboard stays
            # scrollable; documented in dash.sthlp.
            max_height=_MAX_FIGURE_HEIGHT,
            min_height=_MIN_FIGURE_HEIGHT,
            tools="pan,wheel_zoom,box_select,lasso_select,reset",
        )
        if aspect_ratio is not None:
            fig_kwargs["aspect_ratio"] = aspect_ratio
        # Axis type is decided ONCE, before the single bokeh_figure() call.
        # Commit c3941de fixed a bug caused by re-creating a figure to change
        # its axis type; do not reintroduce it.
        _x_date = self._figure_date_kind(plots, "xvar", xvar)
        _y_date = self._figure_date_kind(plots, "yvar", yvar)

        if _x_date and _xs_log:
            warnings.warn(
                f"dash: xscale(log) is meaningless for the date variable "
                f"'{xvar}'; drawing a date axis instead.",
                UserWarning,
            )
            _xs_log = False
        if _y_date and _ys_log:
            warnings.warn(
                f"dash: yscale(log) is meaningless for the date variable "
                f"'{yvar}'; drawing a date axis instead.",
                UserWarning,
            )
            _ys_log = False

        if _x_date:
            fig_kwargs["x_axis_type"] = "datetime"
        elif _xs_log:
            fig_kwargs["x_axis_type"] = "log"
        if _y_date:
            fig_kwargs["y_axis_type"] = "datetime"
        elif _ys_log:
            fig_kwargs["y_axis_type"] = "log"

        fig = bokeh_figure(**fig_kwargs)

        # title() sub-options: applied to the Title model, since the text
        # itself went in via fig_kwargs.
        _t_text, _t_opts = _parse_textbox_opt(graph_opts.get("title", ""))
        if _t_text and _t_opts and fig.title is not None:
            if "size" in _t_opts:
                fig.title.text_font_size = (
                    f"{_textbox_size(_t_opts, 16.0):g}px")
            if "color" in _t_opts or "colour" in _t_opts:
                fig.title.text_color = _textbox_color(_t_opts, "#000000")

        # Tick formatting matched to the date kind: years for %ty, dates for
        # %td/%tw/%tm/%tq/%th, date and time for %tc/%tC.  An explicit
        # xlabel()/ylabel() tick list still wins -- it is applied later.
        for _axis, _kind in ((fig.xaxis, _x_date), (fig.yaxis, _y_date)):
            if _kind:
                _axis.formatter = _datetime_formatter_for(_kind)

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
            # From the ACTIVE view, not self.df: a graph-level if/in
            # qualifier already narrowed the source, so computing the
            # right-hand axis from the full frame left it spanning data the
            # graph does not show.
            _y2_lo, _y2_hi = _compute_secondary_range(
                _source_frame(source, self.df), plots, "yaxis", "yvar", 2
            )
            fig.extra_y_ranges["y2"] = _Range1d(_y2_lo, _y2_hi)
            _y2_scale_raw = graph_opts.get("yscale2", "")
            _y2_log, _y2_rev = _parse_scale_opt(_y2_scale_raw)
            _y2_ax = (LogAxis if _y2_log else LinearAxis)(
                y_range_name="y2",
                axis_label=graph_opts.get("ytitle2", ""),
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
                _source_frame(source, self.df), plots, "xaxis", "xvar", 2
            )
            fig.extra_x_ranges["x2"] = _Range1d(_x2_lo, _x2_hi)
            _x2_scale_raw = graph_opts.get("xscale2", "")
            _x2_log, _x2_rev = _parse_scale_opt(_x2_scale_raw)
            _x2_ax = (LogAxis if _x2_log else LinearAxis)(
                x_range_name="x2",
                axis_label=graph_opts.get("xtitle2", ""),
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

        # Axis range limits, from Stata's xscale(range())/yscale(range()).
        # The previous implementation read graph_opts["xrange"]/["yrange"],
        # keys dash.ado has never emitted -- it looked implemented and was
        # dead.  Those keys are gone; range() is the option Stata documents.
        from bokeh.models import Range1d as _Rng
        for _raw_sc, _which, _axis_attr in (
            (graph_opts.get("xscale", ""), "xscale", "x_range"),
            (graph_opts.get("yscale", ""), "yscale", "y_range"),
        ):
            _report_unhandled_scale_opts(_raw_sc, _which)
            _lo, _hi = _parse_scale_range(_raw_sc)
            if _lo is None and _hi is None:
                continue
            _cur = getattr(fig, _axis_attr)
            _cur_lo = getattr(_cur, "start", None)
            _cur_hi = getattr(_cur, "end", None)
            if _lo is None or _hi is None:
                # One bound given: keep the data's own value for the other.
                _col = xvar if _axis_attr == "x_range" else yvar
                if _col in getattr(self.df, "columns", []):
                    _v = pd.to_numeric(self.df[_col], errors="coerce").dropna()
                    if len(_v):
                        _cur_lo = float(_v.min())
                        _cur_hi = float(_v.max())
            _new_lo = _lo if _lo is not None else _cur_lo
            _new_hi = _hi if _hi is not None else _cur_hi
            if _new_lo is not None and _new_hi is not None:
                setattr(fig, _axis_attr, _Rng(float(_new_lo), float(_new_hi)))

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
        def _parse_refline(opt_key: str, list_key: str) -> "tuple[list, dict]":
            """Return the reference-line positions AND their style sub-options.

            dash.ado passes lcolor()/lpattern()/lwidth() through intact and
            this parser used to float-cast every token and discard them,
            forcing every reference line to grey dashed.  Measured in Stata,
            the default is BLACK dashed -- not grey -- and the sub-options
            take effect.
            """
            raw = graph_opts.get(opt_key, "")
            if not raw:
                return list(graph_opts.get(list_key, [])), {}
            head, opts = _parse_textbox_opt(raw)
            # _parse_textbox_opt strips quotes; a numlist has none, and it
            # splits off exactly the sub-option tail we want.
            values = [v.strip() for v in head.replace(",", " ").split()
                      if v.strip()]
            return values, opts

        def _refline_kwargs(opts: dict) -> dict:
            """Bokeh Span properties for a set of reference-line sub-options."""
            kw: dict = {
                # Stata's measured default: black, dashed, scheme gridline
                # width.  dash forced grey.
                "line_color": "#000000",
                "line_dash":  "dashed",
                "line_width": 1.0,
            }
            if opts.get("lcolor"):
                try:
                    kw["line_color"] = OptionTranslator.translate_mcolor(
                        opts["lcolor"])
                except (ValueError, TypeError):
                    warnings.warn(
                        f"dash: lcolor({opts['lcolor']}) on a reference line "
                        f"is not a recognised colour; ignoring it.",
                        UserWarning,
                    )
            if opts.get("lpattern"):
                try:
                    kw["line_dash"] = OptionTranslator.translate_lpattern(
                        opts["lpattern"])
                except (ValueError, TypeError):
                    pass
            if opts.get("lwidth"):
                try:
                    kw["line_width"] = OptionTranslator.translate_lwidth(
                        opts["lwidth"])
                except (ValueError, TypeError):
                    pass
            return kw

        _xl_vals, _xl_opts = _parse_refline("xline", "xline_values")
        _xl_kw = _refline_kwargs(_xl_opts)
        for xline_val in _xl_vals:
            try:
                fig.add_layout(Span(location=float(xline_val),
                                    dimension="height", **_xl_kw))
            except (ValueError, TypeError):
                pass
        _yl_vals, _yl_opts = _parse_refline("yline", "yline_values")
        _yl_kw = _refline_kwargs(_yl_opts)
        for yline_val in _yl_vals:
            try:
                fig.add_layout(Span(location=float(yline_val),
                                    dimension="width", **_yl_kw))
            except (ValueError, TypeError):
                pass

        # ---- Note / caption ----
        # Both used to be a Label at screen (0, 0) added "below", so they were
        # drawn ON TOP OF EACH OTHER.  Measured in Stata: the note is ring(4)
        # and the caption ring(5), i.e. the caption sits BELOW the note, and
        # the note is the smaller of the two.
        from bokeh.models import Label
        _TEXTBOX_DEFAULTS = {
            "note":     {"size": 11.0, "color": "#555555", "y": 2.0},
            "caption":  {"size": 12.0, "color": "#555555", "y": -12.0},
        }
        for ann_key in ("note", "caption"):
            ann_raw = graph_opts.get(ann_key, "")
            if not ann_raw:
                continue
            ann_text, ann_opts = _parse_textbox_opt(ann_raw)
            if not ann_text:
                continue
            d = _TEXTBOX_DEFAULTS[ann_key]
            lbl = Label(
                x=0, y=d["y"],
                x_units="screen", y_units="screen",
                text=ann_text,
                text_font_size=f"{_textbox_size(ann_opts, d['size']):g}px",
                text_color=_textbox_color(ann_opts, d["color"]),
            )
            fig.add_layout(lbl, "below")

        # Subtitle annotation (appears above the plot area)
        subtitle_text, subtitle_opts = _parse_textbox_opt(
            graph_opts.get("subtitle", ""))
        if subtitle_text:
            subtitle_lbl = Label(
                x=0, y=0,
                x_units="screen", y_units="screen",
                text=subtitle_text,
                text_font_size=f"{_textbox_size(subtitle_opts, 13.0):g}px",
                text_color=_textbox_color(subtitle_opts, "#444444"),
            )
            fig.add_layout(subtitle_lbl, "above")

        # Custom axis tick values (xlabel / ylabel) and label rotation
        from bokeh.models.tickers import FixedTicker
        from bokeh.models.formatters import CustomJSTickFormatter
        for ax_key, axis_obj, grid_obj, var in (
            ("xlabel", fig.xaxis, fig.xgrid, xvar),
            ("ylabel", fig.yaxis, fig.ygrid, yvar),
        ):
            raw_ax = graph_opts.get(ax_key, "")
            tick_key = "xtick" if ax_key == "xlabel" else "ytick"
            raw_tick = graph_opts.get(tick_key, "")
            if not raw_ax and not raw_tick:
                continue
            spec = self._parse_axis_spec(raw_ax or raw_tick)
            self._apply_axis_spec(fig, axis_obj, grid_obj, spec, var)

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
            # A CI layer with no level() of its own inherits the session's.
            if "level" not in popts and self.default_level != _DEFAULT_LEVEL:
                popts = dict(popts, level=str(self.default_level))

            # A qualifier written on THIS layer applies to THIS layer only.
            #   dash (scatter y x) (scatter y x if foreign)
            # Previously only the first layer's if_expr was read, and it was
            # promoted to the graph and applied to every layer -- so the
            # qualifier above either filtered both layers or neither.
            # tsline/tsrline need a time variable.  Without one the x column
            # name is "", which surfaced deep inside Bokeh as a bare KeyError
            # reported to the user as r(7102) with an empty message.
            if ptype.lower() in ("tsline", "tsrline") and not str(pxvar).strip():
                raise ValueError(
                    "dash: %s needs a time variable but none was given and the "
                    "data are not tsset. Either tsset the data first, or give "
                    "the x variable explicitly, as in: dash %s <yvar> <timevar>"
                    % (ptype, ptype)
                )

            _p_if = (plot.get("if_expr") or "").strip()
            _p_in = (plot.get("in_expr") or "").strip()
            _g_if = (graph_spec.get("if_expr") or "").strip()
            _g_in = (graph_spec.get("in_expr") or "").strip()
            source_for_plot = source
            _plot_view = facet_view
            if (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in):
                try:
                    # _apply_graph_filter filters self.df, so restrict to the
                    # rows this source actually carries afterwards -- a faceted
                    # or already-qualified source is a subset of self.df.
                    _pdf = self._apply_graph_filter(
                        {"if_expr": _p_if, "in_expr": _p_in}
                    )
                    # A CDSView over the source the graph already draws from,
                    # NOT a ColumnDataSource of its own.  A layer on a private
                    # source is outside link() -- measured on link(_all) with
                    # two graphs, the qualified layer had its own source while
                    # the other two shared one -- and outside the filter
                    # callback, which only ever touches the sources it was
                    # given.  Every source carries __dash_row__, the row's
                    # position in self.df, so the mask is by identity and
                    # holds however short or reordered the source is.
                    _ids = list(source.data.get(_ROW_ID_COLUMN, []))
                    if not _ids:
                        raise ValueError("source carries no row identity")
                    _pos = {idx: i for i, idx in enumerate(self.df.index)}
                    _wanted = {_pos.get(i, -1) for i in _pdf.index}
                    _mask = [bool(r in _wanted) for r in _ids]
                    # Intersect with a view already on this layer -- a facet
                    # panel, or a linked graph's own qualifier -- rather than
                    # replacing it and losing that restriction.
                    _prev = (getattr(facet_view, "filter", None)
                             if facet_view is not None else None)
                    _prev_bools = getattr(_prev, "booleans", None)
                    if _prev_bools is not None and len(_prev_bools) == len(_mask):
                        _mask = [bool(a and b)
                                 for a, b in zip(_prev_bools, _mask)]
                    _pf = BooleanFilter(booleans=_mask)
                    _plot_view = CDSView(filter=_pf)
                    self._register_view_filter(
                        source, _pf, self._row_ids_for(_pdf))
                except Exception as _pexc:          # never lose the layer
                    warnings.warn(
                        f"dash: per-plot qualifier on layer {pi + 1} could not "
                        f"be applied ({_pexc}); the layer is drawn unfiltered.",
                        stacklevel=2,
                    )

            # Determine secondary axis assignments for this plot layer
            _plot_yaxis = str(popts.get("yaxis", "1")).strip()
            _plot_xaxis = str(popts.get("xaxis", "1")).strip()
            _use_y2 = _has_y2 and _plot_yaxis == "2"
            _use_x2 = _has_x2 and _plot_xaxis == "2"

            # Snapshot renderer list so new glyphs can be identified
            _r_before = len(fig.renderers)
            if pi == 0:
                _plot_renderers: list = []

            if ptype.lower() == "scatteri":
                # Inline coordinate list — no shared source variable needed
                self.mapper.map_scatteri(fig, plot.get("values", []), popts, color_idx=pi)
            elif ptype.lower() in _PC_TYPES:
                py1var = plot.get("y1var", "")
                px1var = plot.get("x1var", "")
                py2var = plot.get("y2var", "")
                px2var = plot.get("x2var", "")
                self._add_pc_glyph(fig, source_for_plot, ptype, py1var, px1var, py2var, px2var, popts,
                                   view=_plot_view, color_idx=pi)
            elif ptype.lower() in _RANGE_TYPES:
                py1var = plot.get("yvar1", "")
                py2var = plot.get("yvar2", "")
                self._add_glyph(fig, source_for_plot, ptype, py1var, pxvar, popts,
                                y2var=py2var, view=_plot_view, color_idx=pi)
            elif ptype.lower() in _UNIVARIATE_TYPES:
                pyvar = (plot.get("yvar", "") or plot.get("var", "")
                         or yvar)
                self._add_glyph(fig, source_for_plot, ptype, pyvar, pxvar, popts,
                                view=_plot_view, color_idx=pi)
            elif ptype.lower() == "function":
                pexpr = plot.get("expr", "")
                # Stata's documented defaults for twoway function:
                # range(0 1) when range() is absent, and n(300).
                # (twoway_function.sthlp: "If range() is not specified,
                # range(0 1) is assumed.")
                x_lo, x_hi = 0.0, 1.0
                n_pts = 300
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
                self._add_glyph(fig, source_for_plot, ptype, pyvar, pxvar, popts,
                                view=_plot_view, color_idx=pi)

            _plot_renderers.append((plot, list(fig.renderers[_r_before:])))

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

        # ---- Legend: Stata's keys, and Stata's rule for showing one ----
        self._rebuild_legend(fig, locals().get("_plot_renderers", []),
                             graph_opts)

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
            # The bare direction keywords, as aliases for the clock
            # positions.  "on" and "ring" are NOT placements and must not be
            # in this map: `ring` matched the word inside `ring(0)`, so every
            # inside placement _rebuild_legend had just computed was
            # overwritten with top_right, and `on` would clobber a position
            # given alongside it.  Visibility and clock positions are decided
            # in _rebuild_legend; this block only handles the keyword aliases
            # and the label() overrides.
            loc_map = {
                "top": "top_center",
                "bottom": "bottom_center",
                "left": "center_left",
                "right": "center_right",
            }
            if legend_opt.strip() == "off":
                for leg in fig.legend:
                    leg.visible = False
            else:
                # A clock position or ring() has already been resolved, and
                # is more specific than a bare keyword.
                _has_explicit_placement = re.search(
                    r"\b(?:position|pos|ring)\s*\(", legend_opt)
                if not _has_explicit_placement:
                    for kw, loc in loc_map.items():
                        if re.search(r'\b' + re.escape(kw) + r'\b', legend_opt):
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
            _hover_formatters: dict = {}

            def _hover_row(col: str) -> None:
                """Add one tooltip row, honouring the variable's Stata format.

                Rows were labelled with the raw variable NAME even though
                self.variable_labels is loaded and already used for axis
                titles, and a date column showed its underlying number.
                """
                kind = getattr(self, "date_vars", {}).get(col)
                if kind:
                    spec = f"@{{{col}}}{{%F}}" if kind != "tc" else \
                           f"@{{{col}}}{{%F %T}}"
                    _hover_formatters[f"@{{{col}}}"] = "datetime"
                else:
                    pattern = getattr(self, "numeric_formats", {}).get(col, "")
                    bokeh_pat = _stata_numeric_pattern(pattern) if pattern else None
                    spec = (f"@{{{col}}}{{{bokeh_pat}}}" if bokeh_pat
                            else f"@{{{col}}}")
                _hover_fields.append((self._axis_label(col), spec))
                _hover_seen.add(col)

            if xvar and xvar in source.data:
                _hover_row(xvar)
            if _yvar_eff and _yvar_eff not in _hover_seen and _yvar_eff in source.data:
                _hover_row(_yvar_eff)
            if _y2var_eff and _y2var_eff not in _hover_seen and _y2var_eff in source.data:
                _hover_row(_y2var_eff)
            for _hv in _hover_extra:
                if _hv not in _hover_seen and _hv in source.data:
                    _hover_row(_hv)
            if _hover_fields:
                # Restrict hover to renderers whose CDS contains every
                # referenced column.  Fit-line, density, and histogram
                # renderers use independent CDS objects with generic column
                # names ("x"/"y", "top"/"left"/"right") — hovering over them
                # with field specs that reference original variable names
                # (e.g. "@{mpg}") would return "???" in the tooltip.
                _hover_col_set = set(_hover_seen)
                _data_renderers = [
                    _rend for _rend in fig.renderers
                    if hasattr(_rend, "data_source") and
                    all(c in _rend.data_source.data for c in _hover_col_set)
                ]

                if _data_renderers:
                    fig.add_tools(HoverTool(tooltips=_hover_fields,
                                            formatters=_hover_formatters,
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
                        # One precision, derived from the spread of the
                        # data, rather than three different hardcoded ones
                        # (0.2f, 0.3f, 0.4f) in three adjacent branches.
                        if "top" in _fb_src.data and "left" in _fb_src.data:
                            _bin_var = self._axis_label(_yvar_eff or "value")
                            _p = _tooltip_precision(_fb_src.data.get("left", []))
                            _fb_fields = [
                                (_bin_var,
                                 f"@{{left}}{{{_p}}} to @{{right}}{{{_p}}}"),
                                ("Count",   "@{top}"),
                            ]
                            _fb_mode = "vline"
                        # KDE / fit line: "x" and "y" columns
                        elif "x" in _fb_src.data and "y" in _fb_src.data:
                            _px = _tooltip_precision(_fb_src.data.get("x", []))
                            _py = _tooltip_precision(_fb_src.data.get("y", []))
                            _fb_fields = [
                                (self._axis_label(xvar or "x"),
                                 f"@{{x}}{{{_px}}}"),
                                (self._axis_label(_yvar_eff or "y"),
                                 f"@{{y}}{{{_py}}}"),
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
        # Sanitised, not merely escaped -- see _resolve_kpi_color.  These
        # are interpolated into a style attribute, where html.escape does not
        # stop a CSS property injection.
        color    = _resolve_kpi_color(kpi_def.get("color", ""), "#212529")
        bgcolor  = _resolve_kpi_color(kpi_def.get("bgcolor", ""), "#f8f9fa")

        html_content = f"""
<div class="db-kpi-card" style="background:{bgcolor}; border-radius:8px;
            padding:20px; text-align:center; border:1px solid #dee2e6;
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
        figures: "dict | None" = None,
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
            # A KPI card has no aspect ratio to derive a count from -- four
            # per row is a legibility judgement, not a derivable quantity, so
            # it is a named constant rather than a bare literal.
            per_row = min(n_kpis, _MAX_KPIS_PER_ROW)
            span = max(1, 12 // per_row)
            for i in range(0, n_kpis, per_row):
                chunk = kpi_names[i : i + per_row]
                rows.append([(name, span) for name in chunk])

        # ---- Graph row(s) ----
        if graph_names:
            n_graphs = len(graph_names)
            # Derived from each figure's OWN proportions, not from the
            # count alone and not from the widest figure on the dashboard: a
            # panel wide enough to need a full row should take one without
            # pushing every other graph onto a row of its own.
            def _ar_of(nm):
                _f = (figures or {}).get(nm)
                _a = getattr(_f, "aspect_ratio", None) if _f else None
                return float(_a) if _a else 0.0

            _wide = [n for n in graph_names if _ar_of(n) >= 2.5]
            _rest = [n for n in graph_names if n not in _wide]

            for name in _wide:
                rows.append([(name, 12)])

            if _rest:
                n_rest = len(_rest)
                if n_rest == 1:
                    per_row = 1
                elif max((_ar_of(n) for n in _rest), default=0.0) >= 1.8:
                    per_row = min(2, n_rest)
                elif n_rest <= 4:
                    per_row = 2
                else:
                    per_row = 3
                span = max(1, 12 // per_row)
                for i in range(0, n_rest, per_row):
                    chunk = _rest[i : i + per_row]
                    rows.append([(name, span) for name in chunk])

        return rows if rows else [[(n, 12 // max(1, len(all_names))) for n in all_names]]

    @staticmethod
    def _parse_bs_layout(
        layout_opt: str,
        all_names: "list[str]",
        kpi_names: "list[str]",
        figures: "dict | None" = None,
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
            return DashRenderer._auto_bs_layout(all_names, kpi_names, figures)

        # Explicit: "bs: <spec>"
        m = re.match(r"^bs\s*:\s*(.+)$", stripped, re.IGNORECASE | re.DOTALL)
        if not m:
            return DashRenderer._auto_bs_layout(all_names, kpi_names, figures)

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

        return rows if rows else DashRenderer._auto_bs_layout(all_names, kpi_names, figures)

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
        tabbed_keys: "set[str] | None" = None,
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
            tabbed_keys:         Set of FIGURE KEYS already placed inside
                                 *tabs_widget*.  Differs from *tabbed_names*
                                 for a faceted graph, whose registered name
                                 is not any of its figure keys.
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
        if tabbed_keys is None:
            # An older caller passing only names: the two spaces coincide for
            # every graph that is not faceted.
            tabbed_keys = set(tabbed_names)

        # Only names NOT assigned to a tab appear in the Bootstrap grid.
        grid_names = [n for n in all_names if n not in tabbed_names]

        # Parse Bootstrap layout for grid items (KPIs + non-tabbed graphs).
        bs_rows = DashRenderer._parse_bs_layout(
            layout_opt, grid_names, kpi_names, self.figures)

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
        # Figure keys, not registered names -- this is the set the
        # "no graph vanishes" guard is checked against.
        _placed_figs: set[str] = set(tabbed_keys)
        for row_spec in bs_rows:
            for name, _ in row_spec:
                if name in _added:
                    continue
                if name in self.kpi_divs:
                    all_models.append(self.kpi_divs[name])
                    model_keys.append(name)
                    _added.add(name)
                    continue
                # A faceted graph owns several figures; they go into one cell
                # as a sub-grid so the user's span arithmetic still holds.
                keys = [k for k in self._resolve_layout_names(name)
                        if k not in tabbed_keys]
                if not keys:
                    continue
                if len(keys) == 1:
                    all_models.append(self.figures[keys[0]])
                else:
                    all_models.append(gridplot(
                        [[self.figures[k] for k in keys]],
                        sizing_mode="stretch_width",
                        toolbar_location="right",
                    ))
                model_keys.append(name)
                _added.add(name)
                _placed_figs.update(keys)

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

        # No graph may vanish from a dashboard without an error.
        self._assert_every_graph_was_placed(_placed_figs)

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
                (span, name_to_div[name], name in kpi_names)
                for name, span in row_spec
                if name_to_div.get(name)
            ]
            if not row_items:
                continue
            grid_parts.append('<div class="db-row db-section">')
            for span, div_html, _is_kpi in row_items:
                grid_parts.append(
                    f'<div class="db-col-12 db-col-sm-12 '
                    f'db-col-md-{_md_span(span)} db-col-lg-{span}'
                    # A graph cell takes its height from the figure's own
                    # aspect ratio; forcing a min-height on it leaves dead
                    # space under a short wide panel.  A KPI card has no
                    # intrinsic height, so it still gets one.
                    f'{" db-cell-h-" + _cell_height_class(span) if _is_kpi else ""}">'
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
                # The user's text, verbatim.  This was .title()-cased, so
                # tabs(MPG stuff: u1) rendered "Mpg Stuff" and an acronym
                # could not survive.
                tab_name = tab_name_raw.strip()
                items = [n.strip() for n in items_str.split() if n.strip()]
            else:
                items = [n.strip() for n in segment.split() if n.strip()]
                tab_name = f"Tab {i + 1}"
            # Security: only accept names present in the registry
            safe_items = [n for n in items if n in valid]
            if safe_items:
                result.append((tab_name, safe_items))
        return result if result else None

    def _resolve_layout_names(self, name: str) -> "list[str]":
        """Return the figure keys a registered graph name owns.

        A faceted graph is stored under generated keys ``name__by__0``,
        ``name__by__1``, ... so a layout that looks the name up directly in
        ``self.figures`` misses it and drops the graph from the dashboard
        with no error.  ``_build_tabs_widget`` consulted ``_facet_map`` and
        got this right; the Bootstrap grid did not.  Two implementations of
        one lookup is how they diverged, so there is now one.

        Args:
            name: A registered graph or KPI name.

        Returns:
            The figure keys, in panel order; empty if the name is unknown.
        """
        if name in getattr(self, "_facet_map", {}):
            return [fkey for fkey, _label in self._facet_map[name]
                    if fkey in self.figures]
        if name in self.figures:
            return [name]
        return []

    def _assert_every_graph_was_placed(self, placed_keys: "set[str]") -> None:
        """Raise if any built figure never reached the document.

        The faceted-graph defect was one instance of a class: a layout path
        that cannot resolve a name skips it silently.  This is the guard that
        catches the rest of the class -- it is worth more than the specific
        fix.

        Args:
            placed_keys: Figure keys the layout actually emitted.

        Raises:
            ValueError: naming every graph that was built and not placed.
        """
        missing = [k for k in self.figures if k not in placed_keys]
        if not missing:
            return
        # Report the user-facing registered name, not the generated facet key.
        facet_owner = {
            fkey: owner
            for owner, entries in getattr(self, "_facet_map", {}).items()
            for fkey, _ in entries
        }
        names = sorted({facet_owner.get(k, k) for k in missing})
        raise ValueError(
            "dash: the following graph(s) were built but never placed in the "
            "dashboard: " + ", ".join(names) + ". This is a layout defect in "
            "dash, not an error in your command; please report it with the "
            "layout() option you used."
        )

    def _build_tabs_widget(
        self,
        tabs_spec: "list[tuple[str, list[str]]]",
    ) -> "tuple[Any, set[str], set[str]]":
        """Build a Bokeh ``Tabs`` widget from a parsed tab specification.

        Each tab's content is laid out as a ``gridplot`` (``ceil(sqrt(N))``
        columns, ``sizing_mode="stretch_width"``) so figures scale to fill the
        available width when the tab is selected.

        Args:
            tabs_spec: List of ``(tab_title, [name, ...])`` from
                       :meth:`_parse_tabs_option`.

        Returns:
            A ``(Tabs, placed_names, placed_keys)`` triple.

            *placed_names* are the REGISTERED names consumed, which is what
            the caller needs to decide which elements to leave out of the
            Bootstrap grid.  *placed_keys* are the FIGURE KEYS consumed,
            which is what the caller needs to record as placed.

            They differ for a faceted graph -- registered ``g``, figures
            ``g__by__0``, ``g__by__1`` -- and returning only the first made
            the Bootstrap caller use registered names in figure-key space.
            A faceted graph inside a tab was therefore placed in the widget
            and recorded nowhere, and vanished from the dashboard with rc 0
            until the "no graph vanishes" guard started catching it.
        """
        placed: set[str] = set()
        placed_keys: set[str] = set()
        tab_panels: list[Any] = []

        for tab_title, names in tabs_spec:
            items: list[Any] = []
            for name in names:
                if name in self._facet_map:
                    for fkey, _label in self._facet_map[name]:
                        fig = self.figures.get(fkey)
                        if fig is not None:
                            items.append(fig)
                            placed_keys.add(fkey)
                    placed.add(name)
                elif name in self.figures:
                    items.append(self.figures[name])
                    placed.add(name)
                    placed_keys.add(name)
                elif name in self.kpi_divs:
                    items.append(self.kpi_divs[name])
                    placed.add(name)
                    placed_keys.add(name)

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
            return None, placed, placed_keys

        tabs_widget = Tabs(tabs=tab_panels, sizing_mode="stretch_width")
        return tabs_widget, placed, placed_keys

    # ------------------------------------------------------------------
    # Layout assembly helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _placement_map(layout_opt: str) -> "dict[str, tuple[int, int]]":
        """Parse Stata's ``layout(name:row,col ...)`` placement form.

        Validated in ``dash.ado`` and documented in ``dash.sthlp``, and never
        implemented: ``_compute_grid`` split on whitespace and called
        ``int(parts[0])`` on ``"s1:1,1"``, which raises, so every placement
        spec silently became the automatic grid.

        Both the 1-based form the help documents and the 0-based form
        ``dash.ado``'s regex actually admits are accepted, and normalised to
        0-based here.  A spec is treated as 1-based only when no index is 0,
        since the two are otherwise indistinguishable.

        Args:
            layout_opt: The raw ``layout()`` string.

        Returns:
            ``{name: (row, col)}``, zero-based; empty when the string is not
            a placement spec.
        """
        if not layout_opt:
            return {}
        pairs = re.findall(
            r"([A-Za-z_]\w*)\s*:\s*(\d+)\s*,\s*(\d+)",
            layout_opt.strip())
        if not pairs:
            return {}
        # Anything else in the string means this is not a placement spec.
        leftover = re.sub(r"[A-Za-z_]\w*\s*:\s*\d+\s*,\s*\d+", "",
                          layout_opt).strip()
        if leftover:
            return {}
        raw = {name: (int(r), int(c)) for name, r, c in pairs}
        one_based = all(r > 0 and c > 0 for r, c in raw.values())
        if one_based:
            return {n: (r - 1, c - 1) for n, (r, c) in raw.items()}
        return raw

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
            cols = self._default_grid_cols(n)
            rows = math.ceil(n / cols) if cols > 0 else 1
            return rows, cols

        parts = layout_opt.strip().split()
        if len(parts) == 2:
            try:
                # Clamp to minimum 1 so a zero-column layout can never cause
                # ZeroDivisionError in _assemble_layout (math.ceil(n / cols_n)).
                return max(1, int(parts[0])), max(1, int(parts[1]))
            except ValueError:
                pass

        placement = self._placement_map(layout_opt)
        if placement:
            rows = max(r for r, _ in placement.values()) + 1
            cols = max(c for _, c in placement.values()) + 1
            # A graph the spec omits is appended, as the Bootstrap path does,
            # so it needs a row of its own.
            named = set(placement)
            extra = [nm for nm in (names_or_n
                                   if isinstance(names_or_n, list) else [])
                     if nm not in named]
            if extra:
                rows += math.ceil(len(extra) / max(1, cols))
            return max(1, rows), max(1, cols)

        # Fallback: auto
        cols = self._default_grid_cols(n)
        rows = math.ceil(n / cols) if cols > 0 else 1
        return rows, cols

    def _default_grid_cols(self, n: int) -> int:
        """Columns for an automatic grid of *n* figures.

        ``ceil(sqrt(n))`` is a reasonable default and stays, but it is now
        aware of the proportions the figures actually have: a dashboard of
        wide figures wants fewer columns than one of square figures, or every
        cell is squeezed.

        Args:
            n: Number of figures.

        Returns:
            The column count, at least 1.
        """
        if n <= 0:
            return 1
        cols = math.ceil(math.sqrt(n))
        ratios = [float(f.aspect_ratio) for f in self.figures.values()
                  if getattr(f, "aspect_ratio", None)]
        if ratios:
            widest = max(ratios)
            if widest >= 3.0:
                cols = 1
            elif widest >= 1.8:
                cols = max(1, cols - 1)
        return max(1, cols)

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
        """Build the dashboard's ColumnDataSources.

        A thin wrapper over :meth:`_build_sources_and_figures`, which is the
        single implementation.  This used to be a second copy of render()'s
        phases; the two drifted, and since nothing outside the tests called
        this one, the behaviours it had and render() lacked never shipped.

        Returns:
            ``{graph name: ColumnDataSource}``.
        """
        spec = self.master_spec
        build = spec.get("build_options", {})
        graphs = spec.get("graphs", [])
        kpis = spec.get("kpis", [])
        link_names, filters_cfg = self._parse_link_and_filters(build)
        self._build_sources_and_figures(graphs, kpis, link_names, filters_cfg)
        return self.sources

    def _build_figures(self) -> "dict[str, Any]":
        """Build the dashboard's Bokeh figures.

        A thin wrapper over :meth:`_build_sources_and_figures`; see
        :meth:`_setup_sources` for why the wrappers exist.

        Returns:
            ``{figure key: Figure}``.  A faceted graph contributes one entry
            per panel, keyed ``name__by__N``.
        """
        self._setup_sources()
        return self.figures

    def _to_serialisable(v: "Any") -> "Any":
        """Convert a single value to a JSON-safe Python scalar.

        A datetime becomes epoch MILLISECONDS, which is exactly how Bokeh
        transports a datetime column to the browser.  Without this,
        ``float(v)`` raises on a Timestamp and the fallback ``str(v)`` wrote
        "2001-01-02 00:00:00" into the snapshot -- so the filter callback
        compared a string against the slider's numeric bounds, dragging the
        slider filtered nothing, and every date KPI collapsed to 0.
        """
        if v is None:
            return None
        if isinstance(v, (pd.Timestamp, np.datetime64)) or hasattr(v, "year"):
            try:
                ts = pd.Timestamp(v)
            except (TypeError, ValueError):
                return str(v)
            if pd.isna(ts):
                return None
            return float(ts.value // 1_000_000)
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

    @staticmethod
    def _parse_link_and_filters(build: dict) -> "tuple[list, list]":
        """Read link() and filter() out of build_options.

        Shared so render() and the wrappers cannot disagree about what was
        asked for -- which is how link(_all) came to work in one and not the
        other.

        Args:
            build: The spec's build_options.

        Returns:
            ``(link_names, filters_cfg)``.
        """
        raw = build.get("link", [])
        if isinstance(raw, list):
            link_names = [str(x) for x in raw]
        else:
            link_names = raw.replace(";", " ").split()
        filters_cfg = build.get("filters", [])
        if not filters_cfg:
            raw_f = build.get("filter", "")
            if raw_f:
                filters_cfg = DashRenderer._parse_filter_raw(raw_f)
        return link_names, filters_cfg

    def _build_sources_and_figures(
        self,
        graphs: list,
        kpis: list,
        link_names: list,
        filters_cfg: list,
    ) -> None:
        """Build every ColumnDataSource and every Figure.

        THE single implementation of what used to exist twice.
        ``render()`` had its own copy of these phases and
        ``_setup_sources``/``_build_figures`` had another, and the two had
        already drifted: the helpers expanded ``link(_all)`` and applied
        dash's own non-selection alpha, and ``render()`` -- the path every
        user reaches -- did neither.  Nothing outside the tests called the
        helpers, so both behaviours looked implemented and neither
        shipped.

        The helpers are kept as thin wrappers rather than deleted: they
        are the only way a test can get at the Figure objects, ~90 call
        sites across eleven test files use them, and ``render()`` returns
        HTML.  What mattered was one implementation, not one entry point.

        Args:
            graphs:      The spec's graph list.
            kpis:        The spec's KPI list.
            link_names:  Graph names sharing one source; ``_all`` is
                         expanded here, once, for every caller.
            filters_cfg: Parsed filter specs.

        Writes: self.sources, self.figures, self._facet_map,
                self._facet_masks, self.agg_source_registry
        """
        all_graph_names = [
            g.get("graph_options", {}).get("name", "") for g in graphs
        ]
        # link(_all) is documented and was expanded only in the two dead
        # helpers, so the shipped path produced an unlinked dashboard and
        # returned rc 0.
        if "_all" in link_names:
            link_names[:] = [n for n in all_graph_names if n]

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
                # "brush" too: a brush KPI still needs its column on the
                # source it is brushing, or the recompute finds nothing.
                if kupdate in ("filter", "brush", "both"):
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
                        _qf = BooleanFilter(booleans=_bool_mask)
                        _linked_graph_views[name] = CDSView(filter=_qf)
                        self._register_view_filter(
                            linked_source, _qf, self._row_ids_for(_g_fdf))
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
                    # No faceting (by() vars missing from df) OR all facet
                    # values are NaN (work_df became empty after dropna).
                    # In the all-missing case by_groups[0][1] is an empty
                    # DataFrame — build a zero-row source so the graph renders
                    # empty instead of falling back to the full original source.
                    if len(by_groups[0][1]) == 0:
                        self.sources[name] = self._make_source(
                            list(base_src.data.keys()), df=by_groups[0][1]
                        )
                    else:
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
                            _pf = BooleanFilter(booleans=mask_r)
                            panel_view_r = CDSView(filter=_pf)
                            # The booleans are sized to the UNFILTERED frame;
                            # once the callback shortens the shared source
                            # they must be rebuilt, so record which rows
                            # belong to this panel.
                            self._register_view_filter(
                                shared_src_render, _pf,
                                [i for i, keep in enumerate(mask_r) if keep])
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
                        if name in link_names:
                            self._apply_nonselection_dimming(fig)
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
                    _fig = self._make_figure(g, src, facet_view=_qual_view)
                    if name in link_names:
                        self._apply_nonselection_dimming(_fig)
                    self.figures[name] = _fig
                except Exception as exc:
                    raise RuntimeError(
                        f"dash_render: failed to build figure '{name}': {exc}"
                    ) from exc



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
                            val, self._effective_kpi_fmt(kpi, varname),
                            varname, stat
                        )
                    except (ValueError, KeyError, TypeError):
                        facet_kpi["value"] = "—"
                    self.kpi_divs[fkpi_name] = self._make_kpi_div(facet_kpi)
            else:
                # Non-faceted KPI: recompute from df so fmt is applied correctly
                kpi_copy = dict(kpi)
                if stat and varname and varname in self.df.columns:
                    try:
                        # Honour the KPI's own if/in qualifier.  Stata
                        # computes the right value and stores it; this
                        # recompute used to run on the FULL frame and
                        # overwrite it, so `dash kpi mean(mpg) if foreign==1`
                        # displayed the unconditional 21.2973 where Stata's
                        # summarize reports 24.7727.
                        _kdf = self._apply_graph_filter(kpi)
                        raw_val = self._compute_kpi_stat_on_df(
                            _kdf, stat, varname)
                        kpi_copy["value"] = self._format_kpi_value(
                            raw_val, self._effective_kpi_fmt(kpi, varname),
                            varname, stat
                        )
                    except (ValueError, KeyError, TypeError):
                        if not kpi_copy.get("value"):
                            kpi_copy["value"] = kpi.get("display", "")
                elif not kpi_copy.get("value"):
                    kpi_copy["value"] = kpi.get("display", "")
                self.kpi_divs[name] = self._make_kpi_div(kpi_copy)

    def _kpi_callback_config(self, kname: str, kdef: dict) -> dict:
        """One KPI's payload for a JS recompute callback.

        Extracted so the filter path and the brush path cannot disagree.
        Every field has to match what the initial render did -- the format,
        the colour, the qualifier -- or the card changes the moment the user
        touches anything.

        Args:
            kname: The KPI's registered name.
            kdef:  Its specification dict.

        Returns:
            One entry of the JS side's ``kpi_config``.
        """
        kstat = kdef.get("stat", "mean")
        kvar = kdef.get("var") or kdef.get("varname", "")
        # The SAME resolution the initial render uses, or the card changes
        # shape on the first interaction.
        kfmt = self._effective_kpi_fmt(kdef, kvar)
        dec, comma = DashRenderer._parse_fmt(kfmt)
        # A KPI carrying its own if/in must keep carrying it.  The callback
        # works on row identities, so the qualifier travels as the set of
        # rows it selects rather than as an expression -- no evaluator in the
        # browser, nothing to inject into.  Only a qualified KPI pays for it.
        qual_ids = self._kpi_qualifier_row_ids(kdef)
        return {
            "name": kname,
            "stat": kstat,
            "varname": kvar,
            "decimals": dec,
            "commas": comma,
            "has_qual": qual_ids is not None,
            "qual_ids": qual_ids if qual_ids is not None else [],
            # No fixed format anywhere: both sides fall back to Stata's
            # general display rather than to two different defaults.
            "general": kfmt.strip() in ("", "%9.0g"),
            # A statistic of a date variable whose result is itself a date
            # has to be re-rendered as a date, not as a number of ms.
            "datekind": (
                getattr(self, "date_vars", {}).get(kvar, "")
                if str(kstat).lower().strip() in self._DATE_VALUED_STATS
                else ""
            ),
            # HTML-escaped to prevent DOM XSS when the callback rebuilds
            # kpi_div.text by string concatenation.
            "title": html.escape(kdef.get("title", "") or ""),
            "subtitle": html.escape(kdef.get("subtitle", "") or ""),
            # Sanitised, not merely escaped: these are interpolated into a
            # style attribute, where html.escape does not stop a CSS property
            # injection.  The SAME resolver as the initial render.
            "color": _resolve_kpi_color(kdef.get("color", "") or "",
                                        "#212529"),
            "bgcolor": _resolve_kpi_color(kdef.get("bgcolor", "") or "",
                                          "#f8f9fa"),
        }

    def _wire_brush_callbacks(self, kpis: list) -> int:
        """Attach a selection callback for every ``update(brush|both)`` KPI.

        ``dash.sthlp`` documents the mode and its standalone-vs-server table
        claims it works in standalone HTML.  Nothing was attached to any
        source's ``selected`` property, and the mode also excluded the KPI
        from the filter callback, so such a card recomputed on nothing at
        all.  Server mode already implements the same rule.

        Args:
            kpis: The spec's KPI list.

        Returns:
            How many callbacks were attached.  Zero leaves the document
            byte-identical to a dashboard with no brush KPI.
        """
        defs = {k.get("name", ""): k for k in kpis}
        cfg: list = []
        divs: list = []
        for kname, kdiv in self.kpi_divs.items():
            kdef = defs.get(kname, {})
            if kdef.get("update", "filter") not in ("brush", "both"):
                continue
            cfg.append(self._kpi_callback_config(kname, kdef))
            divs.append(kdiv)
        if not cfg:
            return 0

        # The helper lives in _FILTER_JS; concatenating puts it in scope
        # without giving the brush path its own copy of the arithmetic.
        _helpers = _FILTER_JS[
            _FILTER_JS.index("// ---- KPI recompute, shared by"):
            _FILTER_JS.index("dash_apply_kpis(new_data,")
        ]
        code = (
            'const ROW_ID = "%s";\n' % _ROW_ID_COLUMN
            + _helpers + _BRUSH_JS
        )

        n = 0
        seen: set = set()
        for src in self.sources.values():
            if id(src) in seen:
                continue
            seen.add(id(src))
            try:
                src.selected.js_on_change("indices", CustomJS(
                    args={
                        "brush_source": src,
                        "kpi_config_json": json.dumps(cfg),
                        "kpi_divs": divs,
                    },
                    code=code,
                ))
                n += 1
            except (AttributeError, ValueError):
                continue
        return n

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

            # Resolve filter widget title:
            #   1. explicit label() option from the filter spec
            #   2. Stata variable label (e.g. "Repair record 1978")
            #   3. variable name (final fallback)
            flabel = (fc.get("label") or "").strip() \
                     or self.variable_labels.get(fvar, "").strip() \
                     or fvar
            if ftype == "dropdown":
                widget, cb = FilterBuilder.build_dropdown(
                    fvar, fsource, None, vlabels,
                    exclude_names=excludes,
                    label=flabel,
                )
            elif ftype == "slider":
                # Guard: slider requires numeric data.  Mirror the server-side
                # is_numeric_dtype check so string columns skip gracefully.
                _sl_col = fsource.data.get(fvar, [])
                # A datetime64 column is not "numeric" by this test, but it is
                # perfectly filterable -- it used to be dropped silently.
                if not (pd.api.types.is_numeric_dtype(pd.Series(_sl_col))
                        or _is_datetime_column(fsource, fvar)):
                    warnings.warn(
                        f"dash: filter '{fvar}' type 'slider' requires numeric "
                        f"data; skipping widget (use type(dropdown) for string "
                        f"columns).",
                        stacklevel=2,
                    )
                    continue
                widget, cb = FilterBuilder.build_slider(
                    fvar, fsource, None, exclude_names=excludes,
                    label=flabel,
                    date_kind=getattr(self, "date_vars", {}).get(fvar, ""),
                )
            elif ftype == "range":
                # Same guard for range slider.
                _rng_col = fsource.data.get(fvar, [])
                # A datetime64 column is not "numeric" by this test, but it is
                # perfectly filterable -- it used to be dropped silently.
                if not (pd.api.types.is_numeric_dtype(pd.Series(_rng_col))
                        or _is_datetime_column(fsource, fvar)):
                    warnings.warn(
                        f"dash: filter '{fvar}' type 'range' requires numeric "
                        f"data; skipping widget (use type(dropdown) for string "
                        f"columns).",
                        stacklevel=2,
                    )
                    continue
                widget, cb = FilterBuilder.build_range(
                    fvar, fsource, None, exclude_names=excludes,
                    label=flabel,
                    date_kind=getattr(self, "date_vars", {}).get(fvar, ""),
                )
            else:
                continue

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
                _kpi_config_for_cb.append(
                    self._kpi_callback_config(_kname, _kdef))
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

            # Each facet/qualifier CDSView, with the row identities that
            # belong to it, so the callback can rebuild its BooleanFilter
            # after the source it is over has been shortened.
            _cb.args["view_filters"] = self._view_filter_args(
                _graph_srcs_for_cb)

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
        tabbed_keys:  set[str]  = set()
        # Every layout, not just Bootstrap.  tabs() used to be parsed,
        # validated against the registry, carried into Python and then
        # dropped unless layout(bs) -- with no warning and rc 0.  Measured:
        # under layout(auto), the DEFAULT, the rendered document was
        # byte-identical with and without the option.  The widget
        # _build_tabs_widget returns is an ordinary Bokeh Tabs; nothing
        # about it is Bootstrap-specific.
        if tabs_str:
            _tabs_spec = DashRenderer._parse_tabs_option(tabs_str, all_names)
            if _tabs_spec:
                (tabs_widget, tabbed_names,
                 tabbed_keys) = self._build_tabs_widget(_tabs_spec)

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
                tabbed_keys=tabbed_keys,
                filter_position=filter_position,
            )

        # ---- Standard Bokeh gridplot layout ----
        rows_n, cols_n = self._compute_grid(all_names, layout_opt)
        n_items = len(all_names)
        if n_items > rows_n * cols_n:
            rows_n = math.ceil(n_items / cols_n)

        # A tabbed element is drawn inside the Tabs widget, so it must not
        # also take a grid cell.
        _grid_names = [n for n in all_names if n not in tabbed_names]
        if tabs_widget is not None:
            rows_n, cols_n = self._compute_grid(_grid_names, layout_opt)
            n_items = len(_grid_names)
            if n_items and n_items > rows_n * cols_n:
                rows_n = math.ceil(n_items / cols_n)

        cells: list[Any] = []
        for name in _grid_names:
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

        # layout(name:row,col) decides WHERE each element goes, not merely how
        # big the grid is.  _placement_map was consulted by _compute_grid and
        # by nothing else, so the grid came out the right size and was then
        # filled in registration order: `layout(s1:1,1 s2:2,2)' put s2 beside
        # s1 instead of diagonally below it, and any spec whose order or gaps
        # differ from registration order was silently rearranged.  The served
        # document has placed correctly since the server layout was written;
        # this is the standalone half.
        _by_name = dict(zip(_grid_names, cells))
        _placed = {nm: rc
                   for nm, rc in self._placement_map(layout_opt).items()
                   if nm in _by_name}

        while len(cells) < rows_n * cols_n:
            cells.append(None)

        if _placed:
            _slots: "list[list[Any]]" = [[None] * cols_n
                                         for _ in range(rows_n)]
            for _nm, (_r, _c) in _placed.items():
                if 0 <= _r < rows_n and 0 <= _c < cols_n:
                    _slots[_r][_c] = _by_name.get(_nm)
            # Anything the spec did not place fills the remaining cells in
            # registration order, which is what the Bootstrap path does.
            _free = [(r, c) for r in range(rows_n) for c in range(cols_n)
                     if _slots[r][c] is None]
            for _nm in [n for n in _grid_names if n not in _placed]:
                if not _free:
                    break
                _r, _c = _free.pop(0)
                _slots[_r][_c] = _by_name.get(_nm)
            grid_rows = _slots
        else:
            grid_rows = [
                cells[r * cols_n : (r + 1) * cols_n] for r in range(rows_n)
            ]
        grid = gridplot(grid_rows, sizing_mode="stretch_width")

        # The tabs widget sits above the remaining grid.  An empty grid --
        # every element tabbed -- would otherwise contribute a stray blank
        # row.
        if tabs_widget is not None:
            _content = (column(tabs_widget, grid, sizing_mode="stretch_width")
                        if cells and any(c is not None for c in cells)
                        else tabs_widget)
        else:
            _content = grid

        if filter_row_widgets:
            # filterposition(left) was honoured only by the Bootstrap path;
            # under layout(auto) the document was identical for top and
            # left.  A Bokeh column beside the content is the plain-path
            # equivalent of the Bootstrap sidebar -- the db-sidebar-* markup
            # and its CSS exist only inside the Bootstrap document.
            if filter_position == "left":
                _sidebar = column(*filter_row_widgets, sizing_mode="fixed",
                                  width=_SIDEBAR_WIDTH_PX)
                layout_root = row(_sidebar, _content,
                                  sizing_mode="stretch_width")
            else:
                filter_bar = row(*filter_row_widgets,
                                 sizing_mode="stretch_width")
                layout_root = column(filter_bar, _content,
                                     sizing_mode="stretch_width")
        else:
            layout_root = _content

        if title_text or subtitle_text:
            header_items = []
            # The same classes the Bootstrap layout uses, so the scheme's
            # title colour and heading size reach both.  These carried a
            # hardcoded colour and no class, so `dash build, scheme(economist)
            # layout(auto)' drew an economist dashboard with a #555 subtitle
            # under a default-coloured heading.
            if title_text:
                header_items.append(Div(
                    text=(
                        f'<h2 class="db-title" style="margin-bottom:2px;">'
                        f'{html.escape(title_text)}</h2>'
                    ),
                    sizing_mode="stretch_width",
                ))
            if subtitle_text:
                header_items.append(Div(
                    text=(
                        f'<p class="db-subtitle" '
                        f'style="margin-top:0;margin-bottom:8px;">'
                        f'{html.escape(subtitle_text)}</p>'
                    ),
                    sizing_mode="stretch_width",
                ))
            layout_root = column(*header_items, layout_root,
                                 sizing_mode="stretch_width")

        # Kept so tests can inspect the models the browser will build,
        # rather than the serialised document -- Bokeh escapes model text
        # again on its way into the embedded JSON, which is correct and
        # would otherwise read as a double escape.
        self._last_layout_root = layout_root
        html_str = file_html(layout_root, INLINE, title=title_text or "dash")

        # A complete element here: this path splices into an existing <head>
        # that has no <style> of its own.  The Bootstrap path below is
        # already inside one, which is why css_block() no longer carries a
        # wrapper.
        _scheme_css = self.scheme.css_style_element()
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
        link_names, filters_cfg = self._parse_link_and_filters(build)
        # Carried RAW; every site that puts these into HTML escapes them
        # itself.  Escaping here as well was a double escape in the
        # Bootstrap path.
        title_text    = build.get("title", "")
        subtitle_text = build.get("subtitle", "") or ""

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

        self._build_sources_and_figures(
            graphs, kpis, link_names, filters_cfg)

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

        # A brush KPI recomputes on a SELECTION change, which is independent
        # of the filter widgets -- a dashboard with no filters at all can
        # still have one.  Returns 0 and attaches nothing when no KPI asks
        # for it, so an ordinary dashboard is unchanged.
        self._n_brush_callbacks = self._wire_brush_callbacks(kpis)

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

        # The same scheme the standalone renderer would resolve, from the
        # same function.  This builder used to consult neither `scheme' nor
        # `theme': `grep scheme' over a generated app returned nothing, and
        # every plot came out Bokeh's default blue no matter what the user
        # had set -- in their session or on the command.
        self.scheme: SchemeParser = SchemeParser.resolve_or_fallback(
            _resolve_scheme_name(self.spec), "the dashboard",
        )

    @staticmethod
    def _shared_stat_lines() -> "list[str]":
        """Emit the renderer's own statistical helpers into the app.

        Not a transcription -- ``inspect.getsource`` copies the SAME source
        text the standalone renderer runs, so the two cannot drift.  Every
        one of these is a module-level function (or, for ``_KERNELS``, a
        module-level literal) with no dependency beyond ``math`` and
        ``numpy``, both of which the generated app already imports.

        They existed here before as hand-written copies that had been left
        behind when S07 rewrote the originals to Stata's rules.  Measured on
        a 74-observation fixture:

        * kdensity used ``scipy.stats.gaussian_kde`` -- a Gaussian kernel on
          Scott's rule, neither Stata's kernel nor Stata's bandwidth -- and
          read neither ``kernel()`` nor ``bwidth()``.
        * mband drew 15 bands where Stata draws 9, each at the bin midpoint
          rather than the band's own median x.
        * lowess ran at ``frac=0.5``; Stata's default is 0.8.
        * the lfitci band was 0.0015 wide where standalone's is 1.39, and
          did not move with ``level()``.
        """
        import inspect as _inspect
        import sys as _sys
        import textwrap as _textwrap

        out: "list[str]" = [
            "# ---- Statistical helpers, copied verbatim from dash_render.py ----",
            "#",
            "# inspect.getsource, not a transcription: the standalone renderer",
            "# and this file run the SAME text, so a change to Stata's rules",
            "# cannot land in one mode and not the other.",
            "",
        ]

        # _KERNELS is a module-level dict of lambdas, so repr() cannot carry
        # it; the assignment's own source is sliced out of the file instead.
        _src_lines = _inspect.getsource(_sys.modules[__name__]).splitlines()
        _start = next(i for i, l in enumerate(_src_lines)
                      if l.startswith("_KERNELS: dict = {"))
        _end = next(i for i in range(_start, len(_src_lines))
                    if _src_lines[i].rstrip() == "}")
        out += _src_lines[_start:_end + 1]
        out += ["", ""]

        out += ["_FIT_GRID = %d" % _FIT_GRID, "", ""]

        for _fn in (_stat_option_float, _fit_grid,
                    _stata_percentile, _stata_kde_bandwidth, _kde_curve,
                    _mband_default_bands, _stata_bin_count,
                    _histogram_heights,
                    # Stata's `if' grammar and its arithmetic operators.  The
                    # standalone renderer translates both before parsing; this
                    # file did neither, so `if inlist(rep78,1,2)' filtered
                    # nothing and `function y = x^2' drew nothing at all.
                    _stata_if_to_pandas, _stata_expr_to_python):
            out += _textwrap.dedent(
                _inspect.getsource(_fn)).rstrip("\n").split("\n")
            out += ["", ""]

        # Four of them are staticmethods on a class.  Their bodies reference
        # no self or cls, so dropping the decorator makes each a module-level
        # function of the same name -- again the SAME text.
        #
        # _kpi_statistic is here because `dash kpi' accepts fifteen statistics
        # (dash.ado's `valid_stats') and the hand-written copy this file used
        # to carry knew ten.  var(), cv(), iqr() and skewness() each drew a
        # card reading `.' under `dash serve' and a number under `dash build',
        # p25/p75 disagreed because the copy used pandas' linear interpolation
        # rather than Stata's percentile, and `count' over a filtered-to-empty
        # selection read `.' where standalone reads 0.
        for _sm in (GlyphMapper._histogram_grid,
                    GlyphMapper._default_lpoly_bwidth,
                    GlyphMapper._compute_lpoly_fit,
                    DashRenderer._kpi_statistic):
            _lines = _textwrap.dedent(
                _inspect.getsource(_sm)).rstrip("\n").split("\n")
            while _lines and _lines[0].strip().startswith("@"):
                _lines = _lines[1:]
            _lines = [_l.replace("GlyphMapper._", "_")
                       .replace("DashRenderer._", "_") for _l in _lines]
            out += _lines + ["", ""]

        # Whatever module-level CONSTANTS those bodies reference must come
        # with them.  Found by scanning rather than listed, so adding a
        # constant to one of the copied functions cannot leave the generated
        # app raising NameError at import -- which _LPOLY_ROT_C did.
        import re as _re_const
        _mod = _sys.modules[__name__]
        _names = set()
        for _l in out:
            _names.update(_re_const.findall(r"\b_[A-Z][A-Z0-9_]*\b", _l))
        import ast as _ast_const
        _consts = []
        for _nm in sorted(_names):
            # Already written out above, as a plain or an annotated
            # assignment.  _KERNELS is the annotated one, and it holds
            # lambdas, so repr() of it is not even valid Python.
            if any(_l.startswith(_nm + " =") or _l.startswith(_nm + ":")
                   for _l in out):
                continue
            _val = getattr(_mod, _nm, None)
            try:
                if _ast_const.literal_eval(repr(_val)) != _val:
                    continue
            except (ValueError, SyntaxError, TypeError):
                continue                      # not expressible as a literal
            _consts.append("%s = %r" % (_nm, _val))
        if _consts:
            out = (out[:1]
                   + ["", "# Constants the copied helpers reference."]
                   + _consts + [""] + out[1:])
        return out

    def _scheme_lines(self) -> "list[str]":
        """Emit the resolved scheme as data the generated app can read.

        The scheme is resolved here, in-process, where ``SchemeParser`` is
        available; the app receives the answers rather than the machinery, so
        it stays runnable without ``dash_render.py`` on the path.

        The 15 entries are Stata's ``p1``-``p15``; ``default_color`` wraps
        with ``index % 15`` and so does the generated lookup.
        """
        sch = self.scheme
        kinds = ("scatter", "line", "connected", "bar", "area", "histogram",
                 "rbar", "rarea", "rline", "rconnected", "tsline", "mspline",
                 "mband")
        colors = {k: [sch.default_color(i, k) for i in range(15)]
                  for k in kinds}
        return [
            "# ---- Scheme, resolved at build time ----",
            "#",
            "# scheme() / theme() / c(scheme) used to reach nothing here, so a",
            "# served dashboard was Bokeh's default blue whatever the user had",
            "# set.  These are the same values SchemeParser gives the",
            "# standalone renderer, written out as data so this file still",
            "# runs without dash_render.py on the path.",
            "_SCHEME_NAME = %r" % sch.name,
            "_SCHEME_COLORS = %r" % (colors,),
            "_SCHEME_SYMBOLS = %r" % ([sch.default_symbol(i)
                                       for i in range(15)],),
            "_SCHEME_MARKER_SIZE = %r" % (sch.default_marker_size(0),),
            "_SCHEME_LINE_PATTERNS = %r" % ([sch.default_line_pattern(i)
                                             for i in range(15)],),
            "_SCHEME_CONNECT_PATTERNS = %r" % ([sch.default_connect_pattern(i)
                                                for i in range(15)],),
            "_SCHEME_CHROME = %r" % ({
                "plotregion_color": sch.plotregion_color,
                "background_color": sch.background_color,
                "axis_line_color": sch.axis_line_color,
                "grid_color": sch.grid_color,
                "grid_line_width": sch.grid_line_width,
                "minor_grid_color": sch.minor_grid_color,
                "draw_major_hgrid": bool(sch.draw_major_hgrid),
                "draw_major_vgrid": bool(sch.draw_major_vgrid),
                "axis_title_font_size": sch.axis_title_font_size,
                "tick_label_font_size": sch.tick_label_font_size,
                "legend_bg_color": sch.legend_bg_color,
                "legend_border_color": sch.legend_border_color,
                "legend_position": getattr(sch, "legend_position", "") or "",
                "legend_cols": getattr(sch, "legend_cols", 0) or 0,
            },),
            "",
            "",
            "def _dash_scheme_color(index, plot_type='scatter'):",
            "    # The scheme's colour for plot *index* of this type.",
            "    _seq = _SCHEME_COLORS.get(plot_type) or _SCHEME_COLORS['scatter']",
            "    return _seq[index % len(_seq)]",
            "",
            "",
            "def _dash_scheme_symbol(index):",
            "    # The scheme's marker for plot *index*.  Every scatter used to",
            "    # be a circle regardless of the scheme, and regardless of how",
            "    # many series shared the figure.",
            "    return _SCHEME_SYMBOLS[index % len(_SCHEME_SYMBOLS)]",
            "",
            "",
            "def _dash_scheme_dash(index, plot_type):",
            "    # The scheme's dash pattern, for the plot types that have one.",
            "    # `color p#line' is the CONNECTING line of twoway connected; a",
            "    # plain line reads p#lineplot.  Same split as the standalone",
            "    # renderer, so the two modes dash the same series alike.",
            "    if plot_type in ('line', 'tsline', 'tsrline', 'mspline',",
            "                     'mband', 'rline'):",
            "        return _SCHEME_LINE_PATTERNS[index % len(_SCHEME_LINE_PATTERNS)]",
            "    if plot_type in ('connected', 'rconnected'):",
            "        return _SCHEME_CONNECT_PATTERNS[index % len(_SCHEME_CONNECT_PATTERNS)]",
            "    return []",
            "",
            "",
            "def _dash_style_legend(lg):",
            "    # The scheme's legend chrome, so a served legend matches the",
            "    # one the standalone renderer draws.",
            "    _c = _SCHEME_CHROME",
            "    try:",
            "        lg.background_fill_color = _c['legend_bg_color']",
            "        lg.border_line_color = _c['legend_border_color']",
            "        lg.label_text_font_size = _c['tick_label_font_size']",
            "        if _c.get('legend_position'):",
            "            lg.location = _c['legend_position']",
            "        if _c.get('legend_cols'):",
            "            lg.ncols = int(_c['legend_cols'])",
            "    except (AttributeError, KeyError, TypeError, ValueError):",
            "        pass",
            "",
            "",
            "def _dash_apply_scheme(fig):",
            "    # Scheme chrome, applied before any explicit graph option, in",
            "    # the same order the standalone renderer uses -- so an explicit",
            "    # option still overrides the scheme in both modes.",
            "    _c = _SCHEME_CHROME",
            "    fig.background_fill_color = _c['plotregion_color']",
            "    fig.border_fill_color = _c['background_color']",
            "    if _c['axis_line_color']:",
            "        fig.outline_line_color = _c['axis_line_color']",
            "    for _grids, _draw in ((fig.xgrid, _c['draw_major_hgrid']),",
            "                          (fig.ygrid, _c['draw_major_vgrid'])):",
            "        for _g in _grids:",
            "            _g.grid_line_color = _c['grid_color'] if _draw else None",
            "            _g.grid_line_width = _c['grid_line_width']",
            "            _g.minor_grid_line_color = _c['minor_grid_color']",
            "    for _ax in list(fig.xaxis) + list(fig.yaxis):",
            "        _ax.axis_line_color = _c['axis_line_color']",
            "        _ax.axis_label_text_font_size = _c['axis_title_font_size']",
            "        _ax.major_label_text_font_size = _c['tick_label_font_size']",
        ]

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

        # Filters, taken the SAME way the standalone path takes them.
        #
        # This read only build_options["filter"], the raw option string, and
        # never build_options["filters"], the already-parsed list that
        # DashRenderer prefers.  A spec carrying the parsed form therefore
        # produced a server app with no filter widgets at all -- measured on
        # a served document: not one Select model, for the feature server
        # mode is sold on.
        #
        # label() is carried through too; it was dropped here, so a filter
        # would have fallen back to the variable name even once the parser
        # learned to read it.
        filter_specs: list[dict] = []
        _pre = bo.get("filters", []) or []
        if _pre:
            for _fs in _pre:
                _v = str(_fs.get("varname") or _fs.get("var") or "").strip()
                if not _v:
                    continue
                filter_specs.append({
                    "var": _v,
                    "type": _fs.get("type", "dropdown"),
                    "exclude": _fs.get("exclude", []) or [],
                    "label": (_fs.get("label") or "").strip(),
                })
        elif filter_raw and filter_raw != '"':
            # DashRenderer._parse_filter_raw handles both "||" (Mata-joined)
            # and ";" (legacy) separators, and now label() too.
            for _fs in DashRenderer._parse_filter_raw(filter_raw):
                # DashRenderer uses "varname"; ServerAppBuilder uses "var".
                filter_specs.append({
                    "var": _fs["varname"],
                    "type": _fs["type"],
                    "exclude": _fs["exclude"],
                    "label": (_fs.get("label") or "").strip(),
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
            "import ipaddress as _ipaddress",
            "import html",
            "import json",
            "import math",
            "import re",
            "import numpy as np",
            "import warnings",
            "import pandas as pd",
            "# Guarded, like every optional dependency on the standalone",
            "# path.  This was a bare module-scope import, so a missing scipy",
            "# aborted the WHOLE app -- measured, a plain scatter that uses no",
            "# scipy raised ModuleNotFoundError on import while the standalone",
            "# renderer rendered the same spec fine.  `except Exception', not",
            "# ImportError: a package that is present but broken raises",
            "# something else, which is why _optional_import catches Exception.",
            "try:",
            "    from scipy import stats as scipy_stats",
            "    _HAS_SCIPY = True",
            "except Exception:",
            "    scipy_stats = None",
            "    _HAS_SCIPY = False",
            "try:",
            "    import statsmodels.nonparametric.smoothers_lowess as sm_lowess",
            "    _HAS_STATSMODELS = True",
            "except Exception:",
            "    # Not `except ImportError': a package that is present but",
            "    # broken raises something else, and _optional_import on the",
            "    # standalone path catches Exception for exactly that reason.",
            "    sm_lowess = None",
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
            "    Legend,",
            "    LegendItem,",
            "    Span,",
            "    TabPanel,",
            "    Tabs,",
            "    WheelZoomTool,",
            ")",
            "from bokeh.io import curdoc",
            "from bokeh.plotting import figure as bokeh_figure",
            "from bokeh.server.server import Server",
            "import collections as _collections",
            "import time as _time",
            "from tornado.web import RequestHandler as _RequestHandler",
            "",
            "# ---- Rate limiter configuration ----",
            "# Width of the filterposition(left) sidebar, shared with the",
            "# standalone renderer so the two documents match.",
            "_SIDEBAR_WIDTH_PX = %d" % _SIDEBAR_WIDTH_PX,
            "",
            "# Stata msize() keyword -> pixels, the same map OptionTranslator",
            "# uses, so one keyword means one size in both modes.",
            "_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),),
            "",
            "# Stata colour name / hex / 'R G B' triplet -> CSS hex.  At module",
            "# scope because the KPI card builder below needs it too, and two",
            "# copies of a colour table is how the modes drifted in the first",
            "# place.",
            "_SCOLOR = " + repr(dict(OptionTranslator._COLOR_MAP)),
            "import re as _re_clr",
            "",
            "",
            "def _resolve_color(c):",
            "    if not c or not isinstance(c, str): return ''",
            "    c = c.strip()",
            "    if _re_clr.fullmatch(r'#[0-9a-fA-F]{6}', c): return c",
            "    named = _SCOLOR.get(c.lower())",
            "    if named: return named",
            "    # RGB triplet '255 0 128'",
            "    parts = c.split()",
            "    if len(parts) == 3:",
            "        try:",
            "            r,g,b = [int(x) for x in parts]",
            "            if all(0 <= v <= 255 for v in (r,g,b)):",
            "                return '#{:02x}{:02x}{:02x}'.format(r,g,b)",
            "        except ValueError: pass",
            "    return ''",
            "",
            "",
            "# A KPI colour lands inside style=\"...color:{c};\", where",
            "# html.escape does NOT stop a CSS *property* injection: ';', '('",
            "# and ')' pass straight through.  Measured before this existed,",
            "#   color(red; background:url(http://evil/x))",
            "# reached the served document as a second declaration the browser",
            "# honours.  The standalone renderer resolved this long ago; only",
            "# the generated app had not.",
            "#",
            "# The value is also a STATA colour name, not a CSS one -- navy is",
            "# #1a476f, not #000080, and gs10 and red%50 are not CSS at all --",
            "# so it is translated first and sanitised after.",
            "_CSS_COLOR_RE_SRC = %r" % (_CSS_COLOR_RE.pattern,),
            "import re as _re_kpi",
            "_CSS_COLOR_RE_APP = _re_kpi.compile(_CSS_COLOR_RE_SRC)",
            "",
            "",
            "def _dash_kpi_color(val, default):",
            "    raw = (val or '').strip()",
            "    if not raw:",
            "        return default",
            "    translated = _resolve_color(raw) or raw",
            "    if isinstance(translated, str) and _CSS_COLOR_RE_APP.match(translated):",
            "        return translated.strip()",
            "    return default",
            "",
            "",
            "def _dash_kpi_card(title, value, subtitle, color, bgcolor, name=''):",
            "    # One card, the standalone one.  There were five builders and",
            "    # the server's drew the value at 28px where standalone drew it",
            "    # at 36px, with different padding, border and label colours.",
            "    _c = _dash_kpi_color(color, '#212529')",
            "    _bg = _dash_kpi_color(bgcolor, '#f8f9fa')",
            "    _t = html.escape(title or '')",
            "    _s = html.escape(subtitle or '')",
            "    _v = html.escape(str(value))",
            "    _n = html.escape(name or 'kpi')",
            "    return (",
            "        f'<div class=\"db-kpi-card\" style=\"background:{_bg}; border-radius:8px;'",
            "        f' padding:20px; text-align:center; border:1px solid #dee2e6;'",
            "        f' min-width:160px; min-height:110px;\">'",
            "        f'<div style=\"font-size:13px; color:#6c757d; margin-bottom:6px;\">{_t}</div>'",
            "        f'<div id=\"kpi_val_{_n}\" style=\"font-size:36px; font-weight:bold;'",
            "        f' color:{_c};\">{_v}</div>'",
            "        f'<div style=\"font-size:11px; color:#6c757d; margin-top:4px;\">{_s}</div>'",
            "        f'</div>'",
            "    )",
            "",
        ] + self._scheme_lines() + self._shared_stat_lines() + [
            "",
            "_RATE_LIMIT_RPM = 60   # max dashboard session connections per IP per minute",
            "_HEALTH_LIMIT_RPM = 600  # max /health requests per IP per minute (infrastructure checks)",
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
            "            # Least RECENTLY SEEN, not first inserted.  Insertion",
            "            # order let a sprayer of 10,000 fresh keys evict the",
            "            # record of a client that is still active, which makes",
            "            # the cap itself an eviction primitive.",
            "            oldest = min(self._store,",
            "                         key=lambda k: self._store[k][-1]",
            "                         if self._store[k] else 0)",
            "            del self._store[oldest]",
            "        ts.append(now)",
            "        self._store[ip] = ts",
            "        return True",
            "",
            "# Separate limiters so health checks and dashboard sessions do not",
            "# compete for the same per-IP budget.  Infrastructure liveness probes",
            "# poll /health frequently; exhausting the shared bucket would cause",
            "# false-negative health signals even when the service is fully healthy.",
            "_SESSION_LIMITER = _RateLimiter(_RATE_LIMIT_RPM)",
            "_HEALTH_LIMITER  = _RateLimiter(_HEALTH_LIMIT_RPM)",
            "# Legacy alias kept for backwards compat with any external scripts that",
            "# reference _LIMITER directly (deprecated — use _SESSION_LIMITER instead).",
            "_LIMITER = _SESSION_LIMITER",
            "",
            "# X-Forwarded-For is set by the CLIENT unless a proxy you control",
            "# overwrites it, so trusting it by default made the rate limiter",
            "# bypassable by one header.  Measured against a running server,",
            "# 700 requests each: no header gave 599 x 200 then 101 x 429; a",
            "# varying spoofed header gave 700 x 200 and not one 429.  A",
            "# CONSTANT spoofed value was limited, which proves the header was",
            "# the bucket key rather than ignored.",
            "#",
            "# The handling is kept, because behind a real reverse proxy",
            "# remote_ip collapses every end user into one bucket (BUGS.md,",
            "# BUG-41).  It is opt-in: --trust-forwarded-for, or set this to",
            "# True, only when a proxy you control rewrites the header.",
            "_TRUST_FORWARDED_FOR = False",
            "",
            "",
            "def _client_ip_from_request(req):",
            "    '''Return the bucket key for rate-limiting.",
            "",
            "    remote_ip, which the peer cannot forge, unless the operator has",
            "    said an upstream proxy may be trusted -- in which case the",
            "    forwarded client address is used, validated as an IP and kept in",
            "    its own key space so a forged value cannot land in a real",
            "    peer's bucket.",
            "    '''",
            "    try:",
            "        remote = getattr(req, 'remote_ip', None) or '0.0.0.0'",
            "        if not _TRUST_FORWARDED_FOR:",
            "            return remote",
            "        headers = getattr(req, 'headers', None) or {}",
            "        xff = headers.get('X-Forwarded-For', '')",
            "        if xff:",
            "            # The LAST token is the hop our own proxy appended;",
            "            # earlier ones are whatever the client sent.",
            "            tok = xff.split(',')[-1].strip()",
            "            try:",
            "                _ipaddress.ip_address(tok)",
            "            except ValueError:",
            "                return remote",
            "            # Prefixed: a forwarded 10.0.0.1 and a real peer",
            "            # 10.0.0.1 are different clients and must not share a",
            "            # bucket.",
            "            return 'xff:' + tok",
            "        return remote",
            "    except Exception:",
            "        return '0.0.0.0'",
            "",
            "class _HealthHandler(_RequestHandler):",
            "    '''Health check HTTP handler — returns 200 OK or 429 when rate-limited.",
            "    Uses _HEALTH_LIMITER (separate from _SESSION_LIMITER) so infrastructure",
            "    liveness probes never deplete the dashboard session budget.'''",
            "    def prepare(self):",
            "        _ip = _client_ip_from_request(self.request)",
            "        if not _HEALTH_LIMITER.is_allowed(_ip):",
            "            self.set_status(429)",
            "            self.set_header('Content-Type', 'application/json')",
            "            self.finish('{\"status\": \"rate_limited\", \"message\": \"Too Many Requests\"}')",
            "    def get(self):",
            "        import datetime as _dt",
            "        self.set_header('Content-Type', 'application/json')",
            "        self.set_status(200)",
            "        # datetime.utcnow() is deprecated and warns on 3.12+; the",
            "        # timezone-aware form is the replacement and gives the",
            "        # same Z-suffixed UTC string.",
            "        ts = _dt.datetime.now(_dt.timezone.utc).strftime(",
            "            '%Y-%m-%dT%H:%M:%SZ')",
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
            "    # jsonio has emitted the payload both flat and wrapped in a",
            "    # 'StataJSON' key over its life.  DashRenderer accepts both;",
            "    # this read only the top level, so a wrapped payload gave the",
            "    # app zero rows, an empty ColumnDataSource, and glyphs",
            "    # referring to columns that do not exist (Bokeh logs",
            "    # BAD_COLUMN_NAME and serves a blank plot).",
            "    data_json = data_json.get('StataJSON', data_json)",
            "    values = data_json.get('values', [])",
            "    var_names = data_json.get('variableNames', [])",
            "    var_labels = data_json.get('variableLabels', {})",
            "    val_label_names = data_json.get('valueLabelNames', {})",
            "    val_labels = data_json.get('valueLabels', {})",
            "    # jsonio emits 'variableIsString'.  This asked for",
            "    # 'variableTypeIsString', which real jsonio output does not",
            "    # contain, so the lookup defaulted to False for every column",
            "    # and pd.to_numeric(errors='coerce') turned EVERY STRING",
            "    # VARIABLE INTO NaN -- measured: make became float64 nan where",
            "    # the standalone renderer keeps 'car0'.  A dropdown filter on",
            "    # a string variable therefore had no values, mlabel() labelled",
            "    # nothing and by() on a string grouped nothing, silently.",
            "    type_is_str = data_json.get('variableIsString') \\",
            "                  or data_json.get('variableTypeIsString', {})",
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
            "def _dash_slider_step(vmin, vmax, values):",
            "    # A range of whole numbers steps by 1.  (vmax - vmin) / 100",
            "    # gave rep78, which takes the values 1..5, a step of 0.04 --",
            "    # so the handle stopped at 1.04, 1.08, ... and a user could",
            "    # not select `2'.",
            "    _span = float(vmax) - float(vmin)",
            "    try:",
            "        _arr = np.asarray(values, dtype=float)",
            "        _arr = _arr[np.isfinite(_arr)]",
            "        if _arr.size and np.all(_arr == np.floor(_arr)):",
            "            return 1.0",
            "    except (TypeError, ValueError):",
            "        pass",
            "    return (_span / 100.0) or 1.0",
            "",
            "",
            'def _compute_histogram(df, varname, options=None):',
            "    # The renderer's own grid and height rules.  This used to be",
            '    # np.histogram(data, bins=<int>) returning RAW COUNTS, so start() and',
            "    # width() were dropped and the y-axis was permanently Stata's",
            "    # `frequency'.  Measured on auto/mpg: standalone tops [0.0522, 0.0969,",
            '    # 0.0485] (density, the default), served [14, 26, 13].  The same',
            '    # command, two different quantities, with no note that the axis had',
            '    # changed meaning.',
            '    options = options or {}',
            '    data = df[varname].dropna().values.astype(float)',
            '    if len(data) == 0:',
            '        return dict(top=[], left=[], right=[])',
            '    edges, ymode = _histogram_grid(data, options)',
            '    counts, _ = np.histogram(data, bins=edges)',
            '    tops = _histogram_heights(counts, edges, ymode)',
            '    return dict(top=np.asarray(tops).tolist(),',
            '                left=np.asarray(edges[:-1]).tolist(),',
            '                right=np.asarray(edges[1:]).tolist())',
            '',
            '',
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
            'def _compute_lfitci(df, yvar, xvar, level=None):',
            "    # `se' from linregress is the standard error of the SLOPE, not the",
            '    # residual standard error.  It was used where the residual SE belongs',
            '    # and then multiplied by sqrt(n-2) to compensate; measured on a',
            '    # 74-point fixture the band came out 0.0015 wide where the standalone',
            "    # renderer's is 1.39 -- a hairline drawn on the fit and labelled a",
            '    # confidence interval.  s = se_slope * sqrt(Sxx) recovers it.',
            '    if not _HAS_SCIPY:',
            '        # scipy is optional.  These two were the only places the',
            '        # generated app still hard-required it, and the exception',
            '        # escaped make_document -- so a user without scipy got no',
            '        # dashboard at all, where the standalone path draws an',
            '        # empty band and warns.',
            '        warnings.warn(',
            '            "dash: a confidence band needs scipy, which could not "',
            '            "be imported; the band is drawn empty. Run dash_setup.",',
            '            UserWarning,',
            '        )',
            '        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])',
            '    from scipy import stats as _sp_stats',
            '    clean = df[list(dict.fromkeys([xvar, yvar]))].dropna()',
            '    x = clean[xvar].values.astype(float)',
            '    y = clean[yvar].values.astype(float)',
            '    n = len(x)',
            '    if n < 3 or float(np.std(x)) == 0.0:',
            '        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])',
            '    slope, intercept, _, _, se_slope = _sp_stats.linregress(x, y)',
            '    x_fit = _fit_grid(x, {})',
            '    y_fit = intercept + slope * x_fit',
            '    x_mean = float(x.mean())',
            '    x_ss = float(np.sum((x - x_mean) ** 2))',
            '    se_resid = float(se_slope) * math.sqrt(x_ss)',
            '    se_fit = se_resid * np.sqrt(1.0 / n + (x_fit - x_mean) ** 2 / x_ss)',
            '    t_crit = _sp_stats.t.ppf(0.5 + _dash_level(level) / 200.0, df=n - 2)',
            '    return dict(x_fit=x_fit.tolist(), y_fit=y_fit.tolist(),',
            '                y_lower=(y_fit - t_crit * se_fit).tolist(),',
            '                y_upper=(y_fit + t_crit * se_fit).tolist())',
            '',
            '',
            "_DASH_LEVEL_CACHE = []",
            "",
            "",
            'def _dash_level(level=None):',
            "    # A per-plot level() wins over the session's c(level), as in Stata.",
            '    # This took no argument, so level() on the plot was ignored and every',
            '    # band in server mode was drawn at c(level).',
            "    if level not in (None, ''):",
            '        try:',
            '            _pl = float(level)',
            '            if 0.0 < _pl < 100.0:',
            '                return _pl',
            '        except (TypeError, ValueError):',
            '            pass',
            '    if not _DASH_LEVEL_CACHE:',
            '        try:',
            "            _s = json.loads(base64.b64decode(_SPEC_B64).decode('utf-8'))",
            "            _lv = float(_s.get('build_options', {}).get('level', 95.0))",
            '            if not (0.0 < _lv < 100.0):',
            '                _lv = 95.0',
            '        except Exception:',
            '            _lv = 95.0',
            '        _DASH_LEVEL_CACHE.append(_lv)',
            '    return _DASH_LEVEL_CACHE[0]',
            '',
            '',
            'def _compute_qfitci(df, yvar, xvar, level=None):',
            "    # The standalone renderer's computation: the design is CENTRED AND",
            '    # SCALED before the Gram matrix is formed, because on raw x the columns',
            '    # are 1, ~3e3 and ~1e7 and the pseudo-inverse discards a real singular',
            '    # value.  This emitted a FLAT band of width t * sd(residuals), which is',
            '    # not a confidence interval for the mean at all.',
            '    if not _HAS_SCIPY:',
            '        # scipy is optional.  These two were the only places the',
            '        # generated app still hard-required it, and the exception',
            '        # escaped make_document -- so a user without scipy got no',
            '        # dashboard at all, where the standalone path draws an',
            '        # empty band and warns.',
            '        warnings.warn(',
            '            "dash: a confidence band needs scipy, which could not "',
            '            "be imported; the band is drawn empty. Run dash_setup.",',
            '            UserWarning,',
            '        )',
            '        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])',
            '    from scipy import stats as _sp_stats',
            '    clean = df[list(dict.fromkeys([xvar, yvar]))].dropna()',
            '    x = clean[xvar].values.astype(float)',
            '    y = clean[yvar].values.astype(float)',
            '    n = len(x)',
            '    if n < 4 or float(np.std(x)) == 0.0:',
            '        return dict(x_fit=[], y_fit=[], y_lower=[], y_upper=[])',
            '    coeffs = np.polyfit(x, y, 2)',
            '    x_fit = _fit_grid(x, {})',
            '    y_fit = np.polyval(coeffs, x_fit)',
            '    _mu = float(np.mean(x))',
            '    _sd = float(np.std(x)) or 1.0',
            '    _z = (x - _mu) / _sd',
            '    _zg = (x_fit - _mu) / _sd',
            '    X = np.column_stack([np.ones_like(_z), _z, _z * _z])',
            '    Xg = np.column_stack([np.ones_like(_zg), _zg, _zg * _zg])',
            '    try:',
            '        beta, *_ = np.linalg.lstsq(X, y, rcond=None)',
            '        XtX_inv = np.linalg.inv(X.T @ X)',
            '        resid = y - X @ beta',
            '        _df = max(1, n - 3)',
            '        s2 = float(resid @ resid) / _df',
            "        var_fit = np.einsum('ij,jk,ik->i', Xg, XtX_inv, Xg)",
            '        se_fit = np.sqrt(np.maximum(s2 * var_fit, 0.0))',
            '        t_crit = _sp_stats.t.ppf(0.5 + _dash_level(level) / 200.0, df=_df)',
            '        y_lower = y_fit - t_crit * se_fit',
            '        y_upper = y_fit + t_crit * se_fit',
            '    except np.linalg.LinAlgError:',
            '        y_lower, y_upper = y_fit, y_fit',
            '    return dict(x_fit=x_fit.tolist(), y_fit=y_fit.tolist(),',
            '                y_lower=np.asarray(y_lower).tolist(),',
            '                y_upper=np.asarray(y_upper).tolist())',
            '',
            '',
            'def _compute_kdensity(df, varname, options=None):',
            "    # Stata's kernel and Stata's bandwidth, from the renderer's own",
            '    # helpers.  This used to call scipy.stats.gaussian_kde -- a Gaussian',
            "    # kernel on Scott's rule -- and read neither kernel() nor bwidth(),",
            "    # so the served curve was not the standalone one and was not Stata's.",
            '    options = options or {}',
            '    data = df[varname].dropna().values.astype(float)',
            '    if len(data) < 2 or float(np.std(data)) == 0.0:',
            '        return dict(x=[], y=[])',
            "    kernel = str(options.get('kernel', '') or 'epanechnikov').strip().lower()",
            '    if kernel not in _KERNELS:',
            "        kernel = 'epanechnikov'",
            '    h = 0.0',
            '    try:',
            "        h = float(options.get('bwidth', '') or 0.0)",
            '    except (TypeError, ValueError):',
            '        h = 0.0',
            '    if h <= 0.0:',
            '        h = _stata_kde_bandwidth(data)',
            '    if h <= 0.0:',
            '        return dict(x=[], y=[])',
            '    try:',
            "        n_pts = int(float(options.get('n', '') or 0))",
            '    except (TypeError, ValueError):',
            '        n_pts = 0',
            '    if n_pts <= 1:',
            '        n_pts = 200',
            '    n_pts = max(2, min(n_pts, 10000))  # clamp: prevent resource exhaustion',
            '    lo, hi = float(data.min()), float(data.max())',
            "    _rng = str(options.get('range', '') or '').split()",
            '    if len(_rng) == 2:',
            '        try:',
            '            lo, hi = float(_rng[0]), float(_rng[1])',
            '        except ValueError:',
            '            lo, hi = float(data.min()), float(data.max())',
            '    if not (hi > lo):',
            '        return dict(x=[], y=[])',
            '    grid = np.linspace(lo, hi, n_pts)',
            '    return dict(x=grid.tolist(),',
            '                y=_kde_curve(data, grid, h, kernel).tolist())',
            '',
            '',
            "def _compute_lowess(df, yvar, xvar, options=None):",
            '    """Return line source dict for LOWESS smoother."""',
            "    options = options or {}",
            "    # Stata's lowess bwidth() is the fraction of the sample in each",
            "    # local regression and its default is 0.8.  This was frac=0.5,",
            "    # so the served curve was smoother than the standalone one from",
            "    # the same command, and neither was what bwidth() asked for.",
            "    _bw = _stat_option_float(options, 'bwidth', 0.8, 'lowess',",
            "                             lo=0.0, hi=1.0)",
            "    if _bw is None or _bw <= 0.0:",
            "        _bw = 0.8",
            "    clean = df[list(dict.fromkeys([xvar, yvar]))].dropna().sort_values(xvar)",
            "    if len(clean) < 2:",
            "        return dict(x=[], y=[])",
            "    if _HAS_STATSMODELS:",
            "        smoothed = sm_lowess.lowess(clean[yvar].values, clean[xvar].values, frac=_bw)",
            "        return dict(x=smoothed[:, 0].tolist(), y=smoothed[:, 1].tolist())",
            "    # Empty and loud, NOT the raw data.  This used to return the",
            "    # cleaned points themselves, so a user with no statsmodels was",
            "    # shown their own scatter joined up and told it was a lowess",
            "    # curve -- measured, x and y matched the raw columns exactly,",
            "    # 20 of 20 points, with no warning and rc 0.  The standalone",
            "    # path warns and draws an empty line for the same input.",
            "    import warnings as _w",
            "    _w.warn(",
            "        \"dash: lowess requires the 'statsmodels' package, which \"",
            "        \"could not be imported; the layer is drawn empty rather \"",
            "        \"than as the raw data. Run dash_setup.\",",
            "        UserWarning, stacklevel=2)",
            "    return dict(x=[], y=[])",
            "",
            "",
            'def _compute_lpoly(df, yvar, xvar, options=None):',
            "    # The renderer's own _compute_lpoly_fit, with Stata's semantics:",
            '    # bwidth() is an ABSOLUTE bandwidth in x-units with a data-driven',
            '    # default, and kernel() selects from _KERNELS.  This file used to carry',
            '    # its own _lpoly_kernel_fit with a hard-coded Gaussian weight and a',
            '    # bwidth treated as a FRACTION of the x-range clamped to [0.01, 1.0],',
            '    # so bwidth(500) on weight became the whole range and kernel() was read',
            '    # by nothing -- up to 7.5 mpg away from the standalone curve for the',
            '    # same command.',
            '    options = options or {}',
            '    clean = df[list(dict.fromkeys([xvar, yvar]))].dropna()',
            '    if len(clean) < 2:',
            '        return dict(x_lp=[], y_lp=[])',
            '    x = clean[xvar].values.astype(float)',
            '    y = clean[yvar].values.astype(float)',
            "    bwidth = _stat_option_float(options, 'bwidth', None, 'lpoly', lo=0.0)",
            '    if bwidth is not None and bwidth <= 0.0:',
            '        bwidth = None',
            "    degree = int(_stat_option_float(options, 'degree', 0.0, 'lpoly',",
            '                                    lo=0.0, hi=3.0) or 0.0)',
            "    kernel = str(options.get('kernel', '') or 'epanechnikov').strip().lower()",
            '    if kernel not in _KERNELS:',
            "        kernel = 'epanechnikov'",
            '    x_grid, y_fit = _compute_lpoly_fit(x, y, bwidth=bwidth, degree=degree,',
            '                                       kernel=kernel)',
            '    valid = ~np.isnan(y_fit)',
            '    return dict(x_lp=np.asarray(x_grid)[valid].tolist(),',
            '                y_lp=np.asarray(y_fit)[valid].tolist())',
            '',
            '',
            "_FP_POWERS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)",
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
            'def _compute_mband(df, yvar, xvar, options=None):',
            "    # Stata's band count and the band's OWN median x.  This used to bin by",
            '    # clip(ceil(n/5), 2, 20) and place each point at the bin midpoint: 15',
            '    # bands on auto where Stata draws 9, at the wrong x.',
            '    options = options or {}',
            '    try:',
            '        clean = df[list(dict.fromkeys([xvar, yvar]))].dropna()',
            '        if len(clean) < 2:',
            "            return {'x_mb': [], 'y_mb': []}",
            '        x = clean[xvar].values.astype(float)',
            '        y = clean[yvar].values.astype(float)',
            '        try:',
            "            n_bands = int(float(options.get('bands', '') or 0))",
            '        except (TypeError, ValueError):',
            '            n_bands = 0',
            '        if n_bands <= 0:',
            '            n_bands = _mband_default_bands(len(x))',
            '        n_bands = max(1, min(n_bands, 1000))  # clamp',
            '        x_edges = np.linspace(float(x.min()), float(x.max()), n_bands + 1)',
            '        xmids, ymeds = [], []',
            '        for bi in range(n_bands):',
            '            if bi < n_bands - 1:',
            '                sel = (x >= x_edges[bi]) & (x < x_edges[bi + 1])',
            '            else:',
            '                sel = (x >= x_edges[bi]) & (x <= x_edges[bi + 1])',
            '            if sel.sum() > 0:',
            '                xmids.append(float(np.median(x[sel])))',
            '                ymeds.append(float(np.median(y[sel])))',
            "        return {'x_mb': xmids, 'y_mb': ymeds}",
            '    except Exception:',
            "        return {'x_mb': [], 'y_mb': []}",
            '',
            '',
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
            '    """Compute a KPI statistic from df[varname]. Returns float.',
            "",
            "    Delegates to _kpi_statistic, which is the standalone",
            "    renderer's own function copied in verbatim above -- so a",
            "    served card and a saved one cannot compute differently.",
            "    An unknown statistic raises there and is reported as a",
            "    missing value here, exactly as an empty column is.",
            '    """',
            "    try:",
            "        series = (df[varname].dropna() if varname in df.columns",
            "                  else pd.Series([], dtype=float))",
            "        return float(_kpi_statistic(series, stat))",
            "    except Exception:",
            "        return float('nan')",
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
            "    if not _SESSION_LIMITER.is_allowed(_client_ip):",
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
            "    #",
            "    # 'index' carries the frame's own row labels.  Without it a",
            "    # selection on this source cannot be mapped back to rows, and",
            "    # a linked graph's brush would compute over the wrong ones.",
            "    linked_vars = list(all_vars)",
            "    _shared_data = {v: df[v].tolist() if v in df.columns else []",
            "                    for v in linked_vars}",
            "    _shared_data['index'] = list(df.index)",
            "    shared_source = ColumnDataSource(_shared_data)",
            "    # Positions in shared_source, by row label, for the CDSView a",
            "    # qualified linked graph needs.",
            "    _shared_pos = {_lbl: _i for _i, _lbl in enumerate(df.index)}",
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
            "            _g_px = _stata_if_to_pandas(_g_if.replace('~=', '!='))",
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
            "        # Scheme first, so an explicit graph option still wins.",
            "        _dash_apply_scheme(fig)",
            "        # Initialised with the figure, not with the plot loop: a",
            "        # faceted graph never enters that loop and would reach the",
            "        # legend block with the name unbound.",
            "        _leg_bounds = []",
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
            '        # Legend boundaries.  NOT ONE of the 44 glyph calls in this loop',
            '        # passed legend_label, so a served figure had no legend at all --',
            '        # measured on a scatter with an lfit over it: standalone drew one',
            '        # legend with two items, the served document drew none, and there',
            '        # was no way to tell the fit from the points.  Recording where each',
            "        # layer's renderers begin lets the legend be built once, below,",
            '        # instead of threading a label through every call.',
            '        for pi, plot in enumerate(plots):',
            "            ptype = plot.get('type', '')",
            "            yvar = plot.get('yvar', '') or plot.get('var', '')",
            "            xvar = plot.get('xvar', '')",
            "            y1var = plot.get('yvar1', '')",
            "            y2var = plot.get('yvar2', '')",
            "            opts = plot.get('options', {})",
            '',
            "            _leg_lbl = (opts.get('legendlabel', '')",
            "                        or var_labels.get(yvar, '') or yvar",
            "                        or var_labels.get(y1var, '') or y1var or ptype)",
            '            _leg_bounds.append((len(fig.renderers), str(_leg_lbl)))',
            '',
            '            color = _dash_scheme_color(pi, ptype)',
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
            "            _line_dash = (_lp_map.get(_lpattern, []) if _lpattern",
            "                          else _dash_scheme_dash(pi, ptype))",
            "",
            "            if ptype in ('scatter',):",
            "                _sc_label_var = opts.get('mlabel', '')",
            "                _sc_cols = [c for c in [xvar, yvar, _sc_label_var] if c and c in g_df.columns]",
            "                _sc_cols = list(dict.fromkeys(_sc_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
            "                clean = g_df[_sc_cols].dropna() if xvar and yvar else g_df",
            "                # link() shares a source; it used to record one in",
            "                # graph_sources and then build a fresh one here, so",
            "                # two graphs under link(_all) rendered from two",
            "                # distinct sources and a selection in one could",
            "                # never appear in the other.",
            "                #",
            "                # A graph with its own if()/in() cannot simply be",
            "                # pointed at the shared source -- that would draw",
            "                # rows the qualifier excluded -- so it gets a",
            "                # CDSView over it instead, which is how the",
            "                # standalone renderer has always done it.",
            "                _sc_view = None",
            "                if gname in linked_names and xvar and yvar:",
            "                    csrc = shared_source",
            "                    if len(clean) != len(df):",
            "                        _sc_pos = [_shared_pos[_l] for _l in clean.index",
            "                                   if _l in _shared_pos]",
            "                        _sc_view = CDSView(filter=IndexFilter(_sc_pos))",
            "                else:",
            "                    csrc = ColumnDataSource(clean) if xvar and yvar else src",
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
            "                _sc_marker = _ms_map.get(opts.get('msymbol',''), _dash_scheme_symbol(pi))",
            "                # The standalone renderer's own map.  These used to be",
            "                # two scales for one set of Stata keywords, so",
            "                # msize(large) drew at 15px in one mode and 12px in",
            "                # the other, from the same command.",
            "                _sz_map = _SIZE_MAP",
            "                _sc_size = _sz_map.get(opts.get('msize',''), _SCHEME_MARKER_SIZE)",
            "                if opts.get('msize','').replace('.','',1).isdigit():",
            "                    _sc_size = float(opts.get('msize','8'))",
            "                _sc_angle_deg = opts.get('msangle', '')",
            "                _sc_angle = math.radians(float(_sc_angle_deg)) if _sc_angle_deg and _sc_angle_deg.strip().lstrip('-').replace('.','',1).isdigit() else 0.0",
            "                _sc_extra = {'view': _sc_view} if _sc_view is not None else {}",
            "                r = fig.scatter(x=_eff_x, y=_eff_y, source=csrc,",
            "                               fill_color=_sc_fill, line_color=color,",
            "                               size=_sc_size, marker=_sc_marker, alpha=0.7,",
            "                               angle=_sc_angle, angle_units='rad',",
            "                               nonselection_alpha=0.15, **_sc_extra)",
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
            "                _line_cols = list(dict.fromkeys(_line_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
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
            "                    'opts': opts,",
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
            "                    'opts': opts,",
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
            "                # No bin() -> Stata's rule over the observed rows,",
            "                # not a literal 20.  The count is then held fixed:",
            "                # the server recomputes the bin EDGES and heights",
            "                # live, which is the documented difference between",
            "                # the modes, but a histogram whose number of bars",
            "                # changes as you drag a slider is not reporting the",
            "                # same statistic twice.",
            '                # _histogram_grid resolves bin()/start()/width() and the',
            '                # y-axis family together, exactly as the standalone',
            '                # renderer does; the count is no longer resolved here.',
            '                hist_data = _compute_histogram(g_df, hvar, opts)',
            "                hist_src = ColumnDataSource(hist_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
            "                    'source': hist_src,",
            "                    'type': 'histogram',",
            "                    'var': hvar,",
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
            "                kde_data = _compute_kdensity(g_df, kvar, opts)",
            "                kde_src = ColumnDataSource(kde_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
            "                    'source': kde_src,",
            "                    'type': 'kdensity',",
            "                    'var': kvar,",
            "                }",
            "                _kde_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _kde_kw['line_dash'] = _line_dash",
            "                fig.line(x='x', y='y', source=kde_src, **_kde_kw)",
            "",
            "            elif ptype == 'lowess':",
            "                lw_data = _compute_lowess(g_df, yvar, xvar, opts)",
            "                lw_src = ColumnDataSource(lw_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
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
            "                lp_data = _compute_lpoly(g_df, yvar, xvar, opts)",
            "                lp_src = ColumnDataSource(lp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
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
            "                lp_data = _compute_lpoly(g_df, yvar, xvar, opts)",
            "                lp_src = ColumnDataSource(lp_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
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
            "                    'opts': opts,",
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
            "                    'opts': opts,",
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
            "                _conn_cols = list(dict.fromkeys(_conn_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
            "                clean = g_df[_conn_cols].dropna().sort_values(xvar) if xvar and yvar else g_df",
            "                csrc = ColumnDataSource(clean)",
            "                _conn_kw = dict(line_color=color, line_width=_line_width)",
            "                if _line_dash: _conn_kw['line_dash'] = _line_dash",
            "                fig.line(x=xvar, y=yvar, source=csrc, **_conn_kw)",
            "                _conn_ms_map = dict(_SIZE_MAP)",
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
            "                _dot_cols = list(dict.fromkeys(_dot_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
            "                clean = g_df[_dot_cols].dropna() if xvar and yvar else g_df",
            "                dsrc = ColumnDataSource(clean)",
            "                _dot_ms_map = dict(_SIZE_MAP)",
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
            "                ci_data = _compute_lfitci(g_df, yvar, xvar, opts.get('level'))",
            "                fit_src = ColumnDataSource(ci_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
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
            "                ci_data = _compute_qfitci(g_df, yvar, xvar, opts.get('level'))",
            "                fit_src = ColumnDataSource(ci_data)",
            "                agg_sources[(gname, pi)] = {",
            "                    'opts': opts,",
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
            "                    _rc_ms_map = dict(_SIZE_MAP)",
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
            "                    _dl_cols = list(dict.fromkeys(_dl_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
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
            "                    _dl_ms_map = dict(_SIZE_MAP)",
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
            "                    _rcsym_ms_map = dict(_SIZE_MAP)",
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
            "                    _si_ms_map = dict(_SIZE_MAP)",
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
            "                _ts_cols = list(dict.fromkeys(_ts_cols))  # `scatter mpg mpg' is legal; g_df[[c, c]] is not",
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
            "                    mb_data = _compute_mband(g_df, yvar, xvar, opts)",
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
            "                    _cols = list(dict.fromkeys(_cols))",
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
            "                # Stata's ^ is exponentiation; Python's is XOR.",
            "                # Translate before parsing, as the standalone",
            "                # renderer does -- the AST whitelist then sees the",
            "                # rewritten text, so nothing is loosened.",
            "                pexpr = _stata_expr_to_python(plot.get('expr', ''))",
            "                opts = plot.get('options', {})",
            "                x_lo, x_hi = 0.0, 1.0",
            "                n_pts = 300",
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
            '        # ---- Build the legend ----',
            '        #',
            '        # NOT ONE of the 44 glyph calls in the plot loop passed',
            '        # legend_label, so a served figure had no legend at all -- measured',
            '        # on a scatter with an lfit over it, standalone drew one legend with',
            '        # two items and the served document drew none.  Recording where each',
            "        # layer's renderers begin lets the legend be built once, here,",
            '        # instead of threading a label through every call.',
            '        if _leg_bounds and fig.renderers:',
            '            _items = []',
            '            for _bi, (_start, _lbl) in enumerate(_leg_bounds):',
            '                _end = (_leg_bounds[_bi + 1][0]',
            '                        if _bi + 1 < len(_leg_bounds) else len(fig.renderers))',
            '                _rends = [fig.renderers[_ri] for _ri in range(_start, _end)',
            '                          if 0 <= _ri < len(fig.renderers)]',
            '                if _rends:',
            "                    _items.append(LegendItem(label={'value': html.escape(_lbl)},",
            '                                             renderers=_rends))',
            '            if _items:',
            "                _lg = Legend(items=_items, location='top_right')",
            "                _lg.click_policy = 'hide'",
            '                # twoway draws no legend for a single series; the standalone',
            '                # renderer builds one and hides it, so both documents carry',
            '                # the same models.',
            '                _lg.visible = len(_items) > 1',
            '                fig.add_layout(_lg)',
            '                _dash_style_legend(_lg)',
            '',
            '        # legend() is applied AFTER the legend exists.  This block used to',
            '        # be emitted before the plot loop, where fig.legend was empty, so',
            '        # legend(position(6)), legend(order()), legend(cols()) and',
            '        # legend(off) all acted on nothing.',
            "        _leg_opt = go.get('legend', '')",
            '        if _leg_opt and fig.legend:',
            '            import re as _re_leg',
            '            # A WORD, not the whole option string: this was compared for',
            "            # exact equality with 'off', so legend(pos(6) off) did nothing.",
            "            if _re_leg.search(r'\\boff\\b', _leg_opt):",
            '                for _lg0 in fig.legend:',
            '                    _lg0.visible = False',
            '            else:',
            "                # 'on' is NOT a placement; the standalone renderer removed",
            '                # it from this map as a bug.',
            "                _leg_pos_map = {'top': 'top_center', 'bottom': 'bottom_center',",
            "                                'left': 'center_left', 'right': 'center_right'}",
            '                for _kw, _loc in _leg_pos_map.items():',
            "                    if _re_leg.search(r'\\b' + _kw + r'\\b', _leg_opt):",
            '                        for _lg0 in fig.legend:',
            '                            _lg0.location = _loc',
            '                        break',
            '                for _lm in _re_leg.finditer(r\'label\\(\\s*(\\d+)\\s+"([^"]*)"\\s*\\)\', _leg_opt):',
            '                    _li = int(_lm.group(1)) - 1',
            '                    _lt = html.escape(_lm.group(2))',
            '                    if fig.legend and 0 <= _li < len(fig.legend[0].items):',
            "                        fig.legend[0].items[_li].label = {'value': _lt}",
            "                _mc = _re_leg.search(r'\\bcols\\s*\\(\\s*(\\d+)\\s*\\)', _leg_opt)",
            "                _mr = _re_leg.search(r'\\brows\\s*\\(\\s*(\\d+)\\s*\\)', _leg_opt)",
            '                for _lg0 in fig.legend:',
            '                    try:',
            '                        if _mc: _lg0.ncols = int(_mc.group(1))',
            '                        if _mr: _lg0.nrows = int(_mr.group(1))',
            '                    except (ValueError, AttributeError):',
            '                        pass',
            '',
            '        # xlabel / ylabel custom tick values',
            '',
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
            "            _by_px = _stata_if_to_pandas(_by_if.replace('~=', '!='))",
            "            if _safe_g(_by_px, _by_q_df.columns):",
            "                try: _by_q_df = _by_q_df.query(_by_px, engine='python')",
            "                except Exception: pass",
            "        work_df = _by_q_df",
            "        if not by_missing:",
            "            work_df = work_df.dropna(subset=by_vars)",
            "        if work_df.empty:",
            "            # All facet-key values are missing (by_missing=False).",
            "            # Zero out the original unfaceted source so the graph",
            "            # renders with no data rows instead of falling back to",
            "            # the full un-faceted dataset.",
            "            _empty_srcs = graph_sources.get(gname, [])",
            "            for _es in (_empty_srcs if isinstance(_empty_srcs, list) else [_empty_srcs]):",
            "                if _es is not None:",
            "                    _es.data = {_col: [] for _col in _es.data}",
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
            "            _dash_apply_scheme(_fac_fig)",
            "            # Render plots on facet figure using facet CDS",
            "            _fac_src_list = graph_sources[_fac_name]",
            "            _fac_src = (_fac_src_list[0] if _fac_src_list else shared_source)",
            "            for pi, plot in enumerate(g.get('plots', [])):",
            "                ptype = plot.get('type', '').lower()",
            "                opts = plot.get('options', {})",
            "                yvar_f = plot.get('yvar', '') or plot.get('var', '')",
            "                xvar_f = plot.get('xvar', '')",
            "                color = (_resolve_color(opts.get('lcolor') or opts.get('mcolor', ''))",
            "                         or _dash_scheme_color(pi, ptype))",
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
            "                    _hdata = _compute_histogram(_fac_gdf, _hvar, opts)",
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
            "                    _lpdata = _compute_lpoly(_fac_gdf, yvar_f, xvar_f, opts)",
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
            "            _dash_apply_scheme(_tot_fig)",
            "            _tot_src = graph_sources[_tot_name][0]",
            "            for pi, plot in enumerate(g.get('plots', [])):",
            "                ptype = plot.get('type', '').lower()",
            "                opts = plot.get('options', {})",
            "                yvar_f = plot.get('yvar', '') or plot.get('var', '')",
            "                xvar_f = plot.get('xvar', '')",
            "                color = (_resolve_color(opts.get('lcolor') or opts.get('mcolor', ''))",
            "                         or _dash_scheme_color(pi, ptype))",
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
            "                    _hdata = _compute_histogram(work_df, _hvar, opts)",
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
            "                    _lpdata = _compute_lpoly(work_df, yvar_f, xvar_f, opts)",
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
            "        ktitle = kpi.get('title', '') or ''",
            "        ksub   = kpi.get('subtitle', '') or ''",
            "        kcolor = kpi.get('color', '') or ''",
            "        kbg    = kpi.get('bgcolor', '') or ''",
            "        val = _compute_kpi(df, kstat, kvar)",
            "        disp = _format_kpi(val, kfmt)",
            "        div_html = _dash_kpi_card(ktitle, disp, ksub, kcolor, kbg, kname)",
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
            "        # The explicit label(), then the Stata variable label,",
            "        # then the bare name -- the same three steps the",
            "        # standalone renderer resolves a widget title by.  This",
            "        # file read only the last two, so",
            "        # filter(rep78, label(\"Repair record\")) showed up",
            "        # titled `rep78'.",
            "        _ftitle = (str(fspec.get('label', '') or '').strip()",
            "                   or var_labels.get(fvar, fvar))",
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
            "                title=_ftitle,",
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
            "            # Guard: all-missing numeric column produces NaN bounds — skip.",
            "            if not (math.isfinite(vmin) and math.isfinite(vmax)):",
            "                import warnings",
            "                warnings.warn(",
            "                    f'dash: filter {fvar!r} type \\'range\\' has no finite values; '",
            "                    f'skipping widget.',",
            "                    UserWarning, stacklevel=2,",
            "                )",
            "                continue",
            "            if vmin == vmax: vmax = vmin + 1.0",
            "            widget = RangeSlider(",
            "                title=_ftitle,",
            "                start=vmin, end=vmax,",
            "                value=(vmin, vmax),",
            "                step=_dash_slider_step(vmin, vmax, df[fvar].values),",
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
            "            # Guard: all-missing numeric column produces NaN bounds — skip.",
            "            if not (math.isfinite(vmin) and math.isfinite(vmax)):",
            "                import warnings",
            "                warnings.warn(",
            "                    f'dash: filter {fvar!r} type \\'slider\\' has no finite values; '",
            "                    f'skipping widget.',",
            "                    UserWarning, stacklevel=2,",
            "                )",
            "                continue",
            "            if vmin == vmax: vmax = vmin + 1.0",
            "            widget = Slider(",
            "                title=_ftitle,",
            "                start=vmin, end=vmax, value=vmin,",
            "                step=_dash_slider_step(vmin, vmax, df[fvar].values),",
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
            "                    _px_cb = _stata_if_to_pandas(_if_cb.replace('~=', '!='))",
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
            "                    agg['source'].data = _compute_histogram(agg_fdf, agg['var'], agg.get('opts') or {})",
            "                elif atype == 'lfit':",
            "                    agg['source'].data = _compute_lfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'qfit':",
            "                    agg['source'].data = _compute_qfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'kdensity':",
            "                    agg['source'].data = _compute_kdensity(agg_fdf, agg['var'], agg.get('opts') or {})",
            "                elif atype == 'lowess':",
            "                    agg['source'].data = _compute_lowess(agg_fdf, agg['yvar'], agg['xvar'], agg.get('opts') or {})",
            "                elif atype == 'lpoly':",
            "                    agg['source'].data = _compute_lpoly(",
            "                        agg_fdf, agg['yvar'], agg['xvar'],",
            "                        agg.get('opts') or {})",
            "                elif atype == 'fpfit':",
            "                    agg['source'].data = _compute_fpfit(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'lfitci':",
            "                    agg['source'].data = _compute_lfitci(agg_fdf, agg['yvar'], agg['xvar'], (agg.get('opts') or {}).get('level'))",
            "                elif atype == 'qfitci':",
            "                    agg['source'].data = _compute_qfitci(agg_fdf, agg['yvar'], agg['xvar'], (agg.get('opts') or {}).get('level'))",
            "                elif atype == 'mspline':",
            "                    agg['source'].data = _compute_mspline(agg_fdf, agg['yvar'], agg['xvar'])",
            "                elif atype == 'mband':",
            "                    agg['source'].data = _compute_mband(agg_fdf, agg['yvar'], agg['xvar'], agg.get('opts') or {})",
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
            "                ktitle = kpi.get('title', '') or ''",
            "                ksub = kpi.get('subtitle', '') or ''",
            "                kcolor = kpi.get('color', '') or ''",
            "                kbg = kpi.get('bgcolor', '') or ''",
            "                _kpi_divs[kname].text = _dash_kpi_card(ktitle, disp, ksub, kcolor, kbg, kname)",
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
            "            # Selection indices are positions in THIS source, and a",
            "            # plot's source is g_df[cols].dropna() -- not the frame.",
            "            # Reading them as positions in _df_ref therefore named",
            "            # the wrong rows whenever anything had been dropped.",
            "            # Bokeh keeps the original labels in the 'index' column,",
            "            # so the mapping is by row identity, as the standalone",
            "            # path does it.",
            "            if not indices:",
            "                sel_df = _df_ref",
            "            else:",
            "                _ids = _src.data.get('index')",
            "                if _ids is None:",
            "                    _n = len(_df_ref)",
            "                    sel_df = _df_ref.iloc[[i for i in indices",
            "                                           if 0 <= i < _n]]",
            "                else:",
            "                    _labels = [_ids[i] for i in indices",
            "                               if 0 <= i < len(_ids)]",
            "                    _idx = _df_ref.index",
            "                    sel_df = _df_ref.loc[[l for l in _labels",
            "                                          if l in _idx]]",
            "            for kpi in _kpi_defs:",
            "                kupdate = kpi.get('update', 'filter')",
            "                if kupdate not in ('brush', 'both'):",
            "                    continue",
            "                kname = kpi.get('name', '')",
            "                if kname not in _kpi_divs:",
            "                    continue",
            "                val = _compute_kpi(sel_df, kpi.get('stat', 'mean'), kpi.get('var', ''))",
            "                disp = _format_kpi(val, kpi.get('fmt', ''))",
            "                ktitle = kpi.get('title', '') or ''",
            "                ksub = kpi.get('subtitle', '') or ''",
            "                kcolor = kpi.get('color', '') or ''",
            "                kbg = kpi.get('bgcolor', '') or ''",
            "                _kpi_divs[kname].text = _dash_kpi_card(ktitle, disp, ksub, kcolor, kbg, kname)",
            "        return _on_selection_change",
            "",
            "    # Wire the brush to every source a glyph actually draws from.",
            "    #",
            "    # This used to be one line -- shared_source.selected.on_change",
            "    # -- and shared_source is rendered by nothing: each plot builds",
            "    # its own ColumnDataSource from the cleaned frame.  Measured:",
            "    # with a KPI declared update(brush), the served document",
            "    # contained exactly one ColumnDataSource, the graph's own, and",
            "    # shared_source was not in the document at all.  Nothing could",
            "    # select it, so the KPI never changed -- with or without",
            "    # link(), which the earlier reading of this blamed.",
            "    #",
            "    # Only sources carrying an 'index' column are wired: that is",
            "    # what marks a source whose rows ARE data rows.  A histogram's",
            "    # bins or a fitted line's points have no row identity, and",
            "    # mapping a selection on them back to observations would",
            "    # produce a confident, wrong number.",
            "    if any(k.get('update', 'filter') in ('brush', 'both')",
            "           for k in kpi_defs):",
            "        _brush_wired = set()",
            "        for _bsrcs in graph_sources.values():",
            "            for _bsrc in (_bsrcs if isinstance(_bsrcs, list) else [_bsrcs]):",
            "                if id(_bsrc) in _brush_wired:",
            "                    continue",
            "                if 'index' not in getattr(_bsrc, 'data', {}):",
            "                    continue",
            "                _brush_wired.add(id(_bsrc))",
            "                _bsrc.selected.on_change('indices', _make_brush_cb(",
            "                    kpi_divs, kpi_defs, df, _bsrc",
            "                ))",
            "",
            '    # ---- Assemble grid layout ----',
            '    #',
            '    # layout(), tabs(), filterposition() and subtitle() used to be read by',
            '    # nothing here: the grid came from len(all_names) alone and the other',
            '    # three keys were decoded out of the spec and dropped.  Two apps whose',
            '    # specs differed only in these were byte-identical.',
            "    layout_opt = (bo.get('layout', '') or 'auto').strip()",
            "    tabs_opt = bo.get('tabs', '') or ''",
            "    filter_position = (bo.get('filter_position', '') or 'top').strip().lower()",
            "    subtitle_text = html.escape(bo.get('subtitle', '') or '')",
            '',
            "    registry = bo.get('registry', '') or ''",
            '    all_names = registry.split() if registry else (',
            "        [g.get('graph_options', {}).get('name', '') for g in graphs]",
            "        + [k.get('name', '') for k in kpi_defs]",
            '    )',
            '',
            '    def _dash_cell(name):',
            '        """The renderable for one registered name, or None."""',
            '        if name in _facet_map:',
            '            _fac_figs = [figures[fk] for fk, _ in _facet_map[name] if fk in figures]',
            '            if not _fac_figs:',
            '                return None',
            '            _go = {}',
            '            for _gx in graphs:',
            "                if _gx.get('graph_options', {}).get('name') == name:",
            "                    _go = _gx.get('graph_options', {})",
            '                    break',
            "            _by_cols_raw = _go.get('by_cols', '0')",
            '            try:',
            '                _by_cn = int(_by_cols_raw) if _by_cols_raw else 0',
            '            except (ValueError, TypeError):',
            '                _by_cn = 0',
            '            if _by_cn <= 0:',
            '                _by_cn = min(len(_fac_figs), max(1, math.ceil(math.sqrt(len(_fac_figs)))))',
            '            _sub_rows = [_fac_figs[_si:_si + _by_cn]',
            '                         for _si in range(0, len(_fac_figs), _by_cn)]',
            '            while len(_sub_rows[-1]) < _by_cn:',
            '                _sub_rows[-1].append(None)',
            "            return gridplot(_sub_rows, sizing_mode='stretch_width')",
            '        if name in figures:',
            '            return figures[name]',
            '        if name in kpi_divs:',
            '            return kpi_divs[name]',
            '        return None',
            '',
            '    def _dash_placements(spec_str):',
            '        """Parse \'name:row,col\' placements; 1-based in the option, 0-based here."""',
            '        out = {}',
            '        for tok in spec_str.split():',
            "            if ':' not in tok:",
            '                continue',
            "            nm, _, rc = tok.partition(':')",
            "            if ',' not in rc:",
            '                continue',
            "            r_s, _, c_s = rc.partition(',')",
            '            try:',
            '                r_i, c_i = int(r_s), int(c_s)',
            '            except ValueError:',
            '                continue',
            '            if nm in all_names and r_i >= 1 and c_i >= 1:',
            '                out[nm] = (r_i - 1, c_i - 1)',
            '        return out',
            '',
            '    def _dash_auto_cols(n):',
            '        if n == 0:',
            '            return 1',
            '        if n <= 2:',
            '            return n',
            '        return math.ceil(math.sqrt(n))',
            '',
            '    def _dash_parse_tabs(tabs_str, names):',
            '        """\'Title: a b / Title2: c\' -> [(title, [names])], or None.',
            '',
            '        Only names in the registry are accepted, so a tabs() option cannot',
            '        place something that was never registered.  Same rule, and the same',
            '        separator, as the standalone path.',
            '        """',
            '        if not tabs_str or not tabs_str.strip():',
            '            return None',
            '        valid = set(names)',
            '        result = []',
            "        for i, segment in enumerate(tabs_str.split('/')):",
            '            segment = segment.strip()',
            '            if not segment:',
            '                continue',
            "            if ':' in segment:",
            "                raw_title, _, items_str = segment.partition(':')",
            '                title = raw_title.strip()',
            '                items = [x.strip() for x in items_str.split() if x.strip()]',
            '            else:',
            '                items = [x.strip() for x in segment.split() if x.strip()]',
            "                title = 'Tab %d' % (i + 1)",
            '            safe = [x for x in items if x in valid]',
            '            if safe:',
            '                result.append((title, safe))',
            '        return result or None',
            '',
            '    # ---- tabs() first: a tabbed element is not also in the grid ----',
            '    tabs_spec = _dash_parse_tabs(tabs_opt, all_names)',
            '    tabs_widget = None',
            '    placed_in_tabs = set()',
            '    if tabs_spec:',
            '        _panels = []',
            '        for _title, _names in tabs_spec:',
            '            _items = [c for c in (_dash_cell(n) for n in _names) if c is not None]',
            '            if not _items:',
            '                continue',
            '            placed_in_tabs.update(_names)',
            '            _tc = max(1, math.ceil(math.sqrt(len(_items))))',
            '            _trows = [_items[_i:_i + _tc] for _i in range(0, len(_items), _tc)]',
            '            while len(_trows[-1]) < _tc:',
            '                _trows[-1].append(None)',
            '            _panels.append(TabPanel(',
            "                child=gridplot(_trows, sizing_mode='stretch_width'),",
            '                title=_title,',
            '            ))',
            '        if _panels:',
            "            tabs_widget = Tabs(tabs=_panels, sizing_mode='stretch_width')",
            '',
            '    grid_names = [n for n in all_names if n not in placed_in_tabs]',
            '',
            "    # ---- layout(): 'auto', 'N M', or 'name:row,col' placements ----",
            "    placement = {} if layout_opt.lower() in ('', 'auto') else _dash_placements(layout_opt)",
            '    placement = {k: v for k, v in placement.items() if k in grid_names}',
            '    parts = layout_opt.split()',
            '    rows_n = cols_n = 0',
            "    if layout_opt.lower() not in ('', 'auto') and len(parts) == 2:",
            '        try:',
            '            # Clamped to 1: a zero-column grid divides by zero below.',
            '            rows_n, cols_n = max(1, int(parts[0])), max(1, int(parts[1]))',
            '        except ValueError:',
            '            rows_n = cols_n = 0',
            '    if not rows_n and placement:',
            '        rows_n = max(r for r, _ in placement.values()) + 1',
            '        cols_n = max(c for _, c in placement.values()) + 1',
            '        _extra = [n for n in grid_names if n not in placement]',
            '        if _extra:',
            '            rows_n += math.ceil(len(_extra) / max(1, cols_n))',
            '    if not rows_n:',
            '        # auto, or a layout() this path could not read (a Bootstrap spec',
            '        # reaches the standalone renderer only; the server document has no',
            '        # Bootstrap markup to place it in).',
            '        cols_n = _dash_auto_cols(len(grid_names))',
            '        rows_n = math.ceil(len(grid_names) / cols_n) if cols_n > 0 else 1',
            '',
            '    if len(grid_names) > rows_n * cols_n:',
            '        rows_n = math.ceil(len(grid_names) / max(1, cols_n))',
            '',
            '    if placement:',
            '        _slots = [[None] * cols_n for _ in range(rows_n)]',
            '        _taken = set()',
            '        for _nm, (_r, _c) in placement.items():',
            '            if 0 <= _r < rows_n and 0 <= _c < cols_n:',
            '                _slots[_r][_c] = _dash_cell(_nm)',
            '                _taken.add(_nm)',
            '        _free = [(r, c) for r in range(rows_n) for c in range(cols_n)',
            '                 if _slots[r][c] is None]',
            '        for _nm in [n for n in grid_names if n not in _taken]:',
            '            if not _free:',
            '                break',
            '            _r, _c = _free.pop(0)',
            '            _slots[_r][_c] = _dash_cell(_nm)',
            '        grid_rows = _slots',
            '    else:',
            '        cells = [_dash_cell(n) for n in grid_names]',
            '        while len(cells) < rows_n * cols_n:',
            '            cells.append(None)',
            '        grid_rows = [cells[i * cols_n:(i + 1) * cols_n] for i in range(rows_n)]',
            '',
            "    grid = gridplot(grid_rows, sizing_mode='stretch_width')",
            '',
            '    # A tab strip sits above whatever grid is left.  An empty grid -- every',
            '    # element tabbed -- would otherwise contribute a blank row.',
            '    if tabs_widget is not None:',
            "        content = (column(tabs_widget, grid, sizing_mode='stretch_width')",
            '                   if grid_names else tabs_widget)',
            '    else:',
            '        content = grid',
            '',
            '    if filter_widgets:',
            "        if filter_position == 'left':",
            '            # The plain-path equivalent of the Bootstrap sidebar: a',
            '            # fixed-width column beside the content, exactly as the',
            '            # standalone renderer builds it.',
            "            sidebar = column(*filter_widgets, sizing_mode='fixed',",
            '                             width=_SIDEBAR_WIDTH_PX)',
            "            layout = row(sidebar, content, sizing_mode='stretch_width')",
            '        else:',
            "            filter_bar = row(filter_widgets, sizing_mode='stretch_width')",
            "            layout = column(filter_bar, content, sizing_mode='stretch_width')",
            '    else:',
            '        layout = content',
            '',
            '    if title_text or subtitle_text:',
            "        _head = ''",
            '        if title_text:',
            '            _head += f\'<h2 style="font-family:sans-serif;margin-bottom:2px;">{title_text}</h2>\'',
            '        if subtitle_text:',
            '            _head += (f\'<div style="font-family:sans-serif;font-size:14px;\'',
            '                      f\'color:#666;margin-top:0;">{subtitle_text}</div>\')',
            "        title_div = Div(text=_head, sizing_mode='stretch_width')",
            "        layout = column(title_div, layout, sizing_mode='stretch_width')",
            '',
            '    doc.add_root(layout)',
            "    doc.title = title_text or 'dash'",
            "",
            "",
        ]

        # ----------------------------------------------------------------
        # 5. __main__ block
        # ----------------------------------------------------------------
        lines += [
            "# ----------------------------------------------------------------",
            "# Attach the document.",
            "#",
            "# This used to live ONLY inside `if __name__ == \"__main__\"`, and",
            "# nothing here called curdoc().  Bokeh's CodeRunner executes an app",
            "# script under a synthetic module name (bokeh_app_<uuid>), so that",
            "# guard is never satisfied and nothing attached the document.",
            "# Measured under `bokeh serve app.py`: docs_json was literally {},",
            "# zero roots, the title absent and /health 404 -- an entirely blank",
            "# page from the only workflow dash documents.  `python app.py`",
            "# worked, and nothing tells a user to run it that way.",
            "#",
            "# curdoc() under `bokeh serve` is the per-session document Bokeh",
            "# has already created.  Run as a plain script it is a throwaway",
            "# document nothing serves, so the __main__ launcher below still",
            "# builds its own Server and is unaffected.",
            "_port = %d" % port,
            "",
            "if __name__ != '__main__':",
            "    make_document(curdoc())",
            "",
            "",
            "def _dash_server_app(port=None, address=None, origins=None):",
            "    \"\"\"Build the Server used by the `python app.py` launcher.",
            "",
            "    allow_websocket_origin used to be the single literal",
            "    localhost:<port>, so reaching the app as 127.0.0.1 or from",
            "    another machine got a blank page with no way to widen it.",
            "    Both spellings of loopback are accepted by default and",
            "    --allow-websocket-origin adds more.",
            "    \"\"\"",
            "    _p = int(port or _port)",
            "    _origins = [f'localhost:{_p}', f'127.0.0.1:{_p}']",
            "    for _o in (origins or []):",
            "        if _o and _o not in _origins:",
            "            _origins.append(_o)",
            "    _kw = {}",
            "    if address:",
            "        _kw['address'] = address",
            "    return Server(",
            "        {'/': Application(FunctionHandler(make_document))},",
            "        port=_p,",
            "        allow_websocket_origin=_origins,",
            "        num_procs=1,",
            "        extra_patterns=[('/health', _HealthHandler)],",
            "        **_kw",
            "    )",
            "",
            "",
            "if __name__ == '__main__':",
            "    # Run as a script, this app serves ITSELF, which is how",
            "    # /health exists at all: `bokeh serve' owns its Tornado",
            "    # application and gives an app script no supported way to add",
            "    # a route, so an app served that way has a working dashboard",
            "    # and no health endpoint.  Project rule 17 asks for one, so",
            "    # this is the launcher dash points users at.",
            "    import argparse as _ap",
            "    _p = _ap.ArgumentParser(description='Serve this dash dashboard.')",
            "    _p.add_argument('--port', type=int, default=_port,",
            "                    help='TCP port to listen on.')",
            "    _p.add_argument('--address', default=None,",
            "                    help='Interface to bind (default: loopback).')",
            "    _p.add_argument('--allow-websocket-origin', action='append',",
            "                    default=None, dest='origins',",
            "                    help='Extra Host values to accept; repeatable. '",
            "                         'Needed to reach the app as 127.0.0.1 or "
            "over a LAN.')",
            "    _p.add_argument('--trust-forwarded-for', action='store_true',",
            "                    dest='trust_xff',",
            "                    help='Believe X-Forwarded-For for rate limiting. '",
            "                         'Only behind a proxy you control: the header '",
            "                         'is client-settable otherwise.')",
            "    _p.add_argument('--show', action='store_true',",
            "                    help='Open a browser window once the server is up.')",
            "    _p.add_argument('--timeout', type=int, default=0,",
            "                    help='Shut down after N minutes (0 = never).')",
            "    _a = _p.parse_args()",
            "    if _a.trust_xff:",
            "        _TRUST_FORWARDED_FOR = True",
            "    _port = max(1024, min(int(_a.port), 65535))",
            "    _server = _dash_server_app(port=_port, address=_a.address,",
            "                               origins=_a.origins)",
            "    _server.start()",
            "    # A browser opens only when asked.  It used to open",
            "    # unconditionally, so every scripted or batch run took over the",
            "    # user's screen.",
            "    if _a.show:",
            "        _server.io_loop.add_callback(_server.show, '/')",
            "    if _a.timeout > 0:",
            "        _server.io_loop.call_later(_a.timeout * 60,",
            "                                   _server.io_loop.stop)",
            "    print(f'Bokeh Server running at http://localhost:{_port}/')",
            "    print(f'Health check:  http://localhost:{_port}/health')",
            "    print('Press Ctrl+C to stop.')",
            f"    try:",
            f"        _server.io_loop.start()",
            f"    except KeyboardInterrupt:",
            f"        pass",
            f"    finally:",
            f"        _server.stop()",
            f"        print('Server stopped.')",
        ]

        lines = self._supply_missing_constants(lines)
        return "\n".join(lines) + "\n"

    @staticmethod
    def _supply_missing_constants(lines: "list[str]") -> "list[str]":
        """Define any module constant the generated app refers to but lacks.

        The app is assembled from many separate blocks of emitted text, and a
        block that uses one of this module's UPPERCASE constants has no way to
        say so.  Two landed at once -- ``_LPOLY_ROT_C`` and ``_FP_POWERS`` --
        each raising ``NameError`` at import of the generated file, which is
        the worst place to find out.

        Scanned rather than listed, so the next one cannot repeat it.  Only
        values whose ``repr`` round-trips through ``ast.literal_eval`` are
        written; anything else (``_KERNELS`` holds lambdas) is left to the
        block that copies its source.

        Args:
            lines: The assembled source, one line each.

        Returns:
            The same lines, with any missing definitions inserted after the
            imports.
        """
        import ast as _ast_sup
        import re as _re_sup
        import sys as _sys_sup

        src = "\n".join(lines)
        used = set(_re_sup.findall(r"\b_[A-Z][A-Z0-9_]*\b", src))
        assigned = set(_re_sup.findall(
            r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=\n]+)?=", src, _re_sup.MULTILINE))
        mod = _sys_sup.modules[__name__]

        missing = []
        for name in sorted(used - assigned):
            val = getattr(mod, name, None)
            if val is None:
                continue
            try:
                if _ast_sup.literal_eval(repr(val)) != val:
                    continue
            except (ValueError, SyntaxError, TypeError):
                continue
            missing.append("%s = %r" % (name, val))
        if not missing:
            return lines

        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import = i
        out = list(lines)
        out[last_import + 1:last_import + 1] = (
            ["", "# Constants the copied helpers refer to."] + missing + [""])
        return out


# ===========================================================================
# Updated CLI entry point — uses argparse for --spec/--data/--output/--mode
# ===========================================================================

def main(
    master_spec_path: str,
    data_json_path: str,
    output_path: str,
    mode: str = "standalone",
    port: int = 5006,
) -> None:
    """Build the dashboard and write it to *output_path*.

    Dispatches to ``DashRenderer`` (standalone HTML) or ``ServerAppBuilder``
    (Bokeh Server app ``.py``) depending on *mode*.

    Args:
        master_spec_path: Path to the master specification JSON.
        data_json_path:   Path to the jsonio data JSON.
        output_path:      Destination path for the output file.
        mode:             ``'standalone'`` (default) or ``'server'``.
        port:             Port to embed in the generated server app.  Ignored
                          for standalone.  ``build_options["port"]`` still
                          wins, because that is what dash.ado writes.

    Raises:
        ValueError: If *mode* is not a recognised value.
    """
    if mode == "server":
        # --port used to stop here: this call passed three arguments and no
        # port, so every generated app embedded _port = 5006 whatever the
        # user asked for.  `dash serve' did not notice because it passes
        # --port again to the app it launches; `dash build, saving(app.py)
        # server' followed by `python app.py' -- the documented non-blocking
        # route -- served on 5006 regardless.
        builder = ServerAppBuilder(master_spec_path, data_json_path)
        builder.build(output_path, port=max(1024, min(int(port), 65535)))
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
    parser.add_argument(
        "--launch",
        action="store_true",
        default=False,
        help=(
            "After writing a server app, start it and wait. Off by default: "
            "writing a file must not start a server as a side effect. "
            "`dash serve' passes this; `dash build, server' does not."
        ),
    )
    args = parser.parse_args()

    # Build the output file (HTML or server app .py)
    main(args.spec, args.data, args.output, args.mode, args.port)

    # When mode is 'server' AND the caller asked for it, launch the app.
    #
    # This used to happen unconditionally, so `dash build, saving(app.py)
    # server' -- documented to write a file and return -- opened a browser
    # and blocked the Stata session forever on _proc.wait().  The two
    # `display' lines that follow it in dash.ado never printed, and killing
    # Stata left the server orphaned.  Writing a file must not start a
    # server as a side effect, so launching is opt-in.
    if args.mode == "server" and args.launch:
        import subprocess as _sp
        import sys as _sys
        import time as _time
        import threading as _threading
        import webbrowser as _wb

        _port = max(1024, min(args.port, 65535))
        # Run the generated app AS A SCRIPT, not through `bokeh serve'.
        #
        # `bokeh serve' owns its Tornado application and gives an app script
        # no supported way to register a route, so /health could never exist
        # on this path -- measured, it returned 404, while project rule 17
        # asks for a health endpoint.  The generated app builds its own
        # Server with extra_patterns, so running it directly is what makes
        # /health real.  It also means --port and the websocket origins reach
        # the server that is actually listening: the port argument used to be
        # passed to `bokeh serve' but never to the builder, so every app
        # embedded 5006 whatever was asked for.
        _cmd = [
            _sys.executable, args.output,
            "--port", str(_port),
        ]
        if not args.no_browser:
            _cmd.append("--show")
        if args.timeout > 0:
            _cmd += ["--timeout", str(args.timeout)]
        try:
            _proc = _sp.Popen(_cmd)
        except FileNotFoundError:
            import sys as _sys2
            print(
                "dash_render: error — could not launch the dashboard app. "
                "Ensure Bokeh is installed and accessible in the current Python environment.",
                file=_sys2.stderr,
            )
            raise SystemExit(1)

        try:
            _proc.wait()
        except KeyboardInterrupt:
            _proc.terminate()
            _proc.wait()
