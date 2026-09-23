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
    InlineStyleSheet,
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

# Number of data points above which WebGL rendering is used.
#
# Deliberately a constant, not derived: it is a property of the BROWSER, not
# of the data or of anything the user typed.  Below roughly this many glyphs
# the canvas backend draws faster and renders text more crisply; above it the
# canvas backend drops frames while panning.  There is nothing in a Stata
# dataset that could tell dash where that crossover is.
# Dataset size, in CELLS (rows x columns), above which dash says the output
# will be large.
#
# Deliberately a constant and deliberately a REPORT rather than a refusal:
# the user may well mean it, and `twoway' does not refuse to plot ten million
# points either. The number is calibrated, not guessed -- measured at roughly
# 34 bytes of HTML per cell, so a million cells is about 33 MB of standalone
# HTML and a comparable base64 payload in a served app. Below it sit every
# dataset that ships with Stata: auto is 888 cells, nlsw88 is 38,182.
_LARGE_DATASET_CELLS = 1_000_000

# Measured bytes of standalone HTML per data cell, used only to put a figure
# in the warning above. It is an order-of-magnitude estimate, not a promise.
_HTML_BYTES_PER_CELL = 34


def _report_dataset_size(df: "pd.DataFrame", mode: str) -> None:
    """Say so, once, when a dataset will make an unwieldy dashboard.

    Neither renderer bounded or reported this. Measured by the adversarial
    pass: 2,000,000 rows by 2 columns rendered to 90.6 MB of HTML at 1.71 GB
    RSS with rc 0 and nothing said, and the served app embeds the same data
    base64 and rebuilds the frame on every session. The user finds out when
    the file will not open, and a Stata user has no way to know in advance --
    `dash scatter y x' looks the same on 74 observations and on ten million.

    Args:
        df:   The frame about to be embedded.
        mode: "dashboard" or "server app", for the message.
    """
    try:
        rows, cols = int(df.shape[0]), int(df.shape[1])
    except (AttributeError, TypeError, ValueError):
        return
    cells = rows * cols
    if cells < _LARGE_DATASET_CELLS:
        return
    mb = cells * _HTML_BYTES_PER_CELL / 1_000_000.0
    warnings.warn(
        f"dash: {rows:,} observations on {cols} variables is a large "
        f"dataset to embed; this {mode} will be roughly {mb:,.0f} MB and "
        f"slow to open. Reduce it with an `if' or `in' qualifier, or keep "
        f"only the variables the dashboard uses.",
        UserWarning, stacklevel=3,
    )


_WEBGL_THRESHOLD = 10_000

# Opacity of the observations NOT selected by a brush.
#
# Deliberately a constant.  It is a legibility judgement -- unselected points
# must stay visible enough to give the selection context, and faint enough
# that the selection reads as the subject -- and no property of the data
# implies a number.  Stata has no equivalent to derive it from: `twoway' has
# no brushing.  A user who wants a different value sets the marker's own
# alpha with malpha() or mcolor(col%nn).
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


_TEXTBOX_SUBOPTS = (
    "size", "color", "colour", "position", "pos", "span", "box", "nobox",
    "justification", "just", "alignment", "margin", "linegap", "bexpand",
    "bmargin", "fcolor", "lcolor", "lwidth", "lpattern", "orientation",
    "ring", "placement", "width", "height", "tstyle", "style",
)
_TEXTBOX_SUBOPT_RE = re.compile(
    r",\s*(?=(?:" + "|".join(_TEXTBOX_SUBOPTS) + r")\b)", re.I)


def _textbox_split_point(text: str) -> int:
    """Index of the comma that starts a textbox's sub-options, or ``-1``.

    Stata writes a textbox option as ``text[, suboptions]``, but the text is
    the user's and may contain commas of its own.  Only a comma outside the
    quoted text can be the separator, so the scan tracks quote state rather
    than letting a regex match anywhere -- the same discipline the Mata
    scanners in ``dash_parse.mata`` apply to the command line.

    Args:
        text: The raw option value, quotes included.

    Returns:
        The index of the separating comma, or ``-1`` when there is none.
    """
    in_quote = False
    for i, ch in enumerate(text):
        if ch == '"':
            in_quote = not in_quote
        elif ch == "," and not in_quote:
            if _TEXTBOX_SUBOPT_RE.match(text, i):
                return i
    return -1


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
    # Only a comma OUTSIDE the user's quoted text introduces sub-options.
    #
    # This used to be a bare _TEXTBOX_SUBOPT_RE.search() over the whole
    # value, so a comma inside the text itself was read as the sub-option
    # separator whenever an ordinary English word happened to follow it --
    # and the keyword list is ordinary English: size, color, just, width,
    # height, style, span, box, margin, position.  Measured,
    #     title("Sales, size matters")   rendered as   "Sales"
    #     title("Revenue, color coded")  rendered as   "Revenue"
    # with the rest of the user's text silently discarded.  twoway keeps it.
    split_at = _textbox_split_point(text)
    tail = ""
    if split_at >= 0:
        m = _TEXTBOX_SUBOPT_RE.match(text, split_at)
        tail = text[m.end():]
        text = text[:split_at]
    text = text.strip()
    # Stata's `asis` declarations keep the quotes the user typed, which is
    # what makes the multi-string form legible here: a text option may be
    # SEVERAL quoted strings, and Stata renders each as its own LINE --
    # title("line one" "line two") is stored as mtextq(`""line one" "line
    # two""') in a .gph and drawn on two lines.
    #
    # These used to be joined with a space, so every such value collapsed
    # onto one line.  BokehJS renders "\n" as a real line break in both Title
    # and Label -- verified visually against bokeh 3.9, not inferred from the
    # model accepting the character.
    #
    # A single quoted string joins to itself, so the ordinary case is
    # untouched and cannot gain a stray break.
    quoted = re.findall(r'"([^"]*)"', text)
    if quoted:
        text = "\n".join(quoted)
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
    if not raw:
        return None
    # A word that is neither a number nor a width keyword raised out of
    # here and aborted the whole standalone render (the served app was
    # silent for the same value).  Named, and the default kept, in both.
    try:
        return OptionTranslator.translate_lwidth(raw)
    except (ValueError, TypeError):
        _dash_style_note("plotregion(lwidth)", raw, "line width",
                         "the default")
        return None


def _extract_finite(
    source: "ColumnDataSource", varname: str, allow_datetime: bool = False,
    view=None,
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
        view: Optional CDSView whose mask restricts the rows read.  The
            distribution layers pass their own view so a qualified histogram
            or kdensity describes the rows the user asked for.  The filter
            widgets deliberately do NOT: a slider's bounds come from the whole
            column, not from whatever a layer happens to be showing.

    Returns:
        1-D numpy float array with None and NaN values removed.
    """
    col = source.data.get(varname, [])
    sel = GlyphMapper._view_mask(view, len(col))
    if sel is not None:
        col = list(np.asarray(col, dtype=object)[sel])
    return _dash_finite_column(col, allow_datetime)


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
    def parse_color_alpha(
        value: str, option: str = "",
    ) -> "tuple[str | None, float | None]":
        """Parse a Stata color+alpha spec such as ``'red%50'`` or ``'%30'``.

        Stata allows an optional ``%N`` suffix on any color spec where *N* is
        0-100 and represents opacity percentage (0 = transparent, 100 = opaque).
        A bare ``%N`` with no color prefix means "use current color, change
        alpha only".

        Args:
            value:  Raw option value from a Stata mcolor()/fcolor()/lcolor()
                    call, e.g. ``"navy%80"`` or ``"%50"`` or ``"navy"``.
            option: The option the value came from.  When given, a colour
                    that cannot be resolved is reported through
                    ``_dash_style_note`` before ``None`` is returned; every
                    option applier passes it, so an unknown colour name is
                    never dropped in silence.

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
                # Unrecognised: the caller keeps its default.  Named when
                # the caller said which option it is reading.
                if option:
                    _dash_style_note(option, value, "colour")

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

        # Passthrough for hex values already in CSS format.
        #
        # The 3- and 6-digit forms are the only ones deliberately accepted:
        # they are what Stata's own scheme files and dash's colour table
        # carry, and what every browser reads the same way.  4- and 8-digit
        # forms carry alpha, which dash sets separately through malpha(),
        # lalpha() and falpha(), so accepting them would give two places to
        # set one property.
        #
        # The length test alone was the whole check, so any 4- or
        # 7-character string starting with '#' was returned as a colour --
        # '#}a{b;c' among them. SchemeParser puts this value into a <style>
        # block where html.escape leaves '{', '}' and ';' alone, so a
        # .scheme file (which the help invites the user to take from the
        # working directory) could close dash's own rule and open its own.
        # The KPI colour path was hardened against exactly this; this was
        # the colour path it did not reach.
        if re.fullmatch(r"#(?:[0-9a-f]{3}|[0-9a-f]{6})", v):
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
        # Numeric passthrough (Stata also accepts raw numbers).  A finite
        # one: float('1e400') is inf, and int(inf) is an OverflowError no
        # caller's `except ValueError' caught, so msize(1e400) aborted the
        # render in both modes.
        try:
            f = float(v)
        except ValueError:
            f = float("nan")
        if math.isfinite(f):
            return max(1, int(f))
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
        # A finite number only: lwidth(1e400) used to come back as inf and
        # be handed to Bokeh as a line width.
        try:
            f = float(v)
        except ValueError:
            f = float("nan")
        if math.isfinite(f):
            return max(0.1, f)
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

    # Where a `net install' really puts things.  Measured, from a real install
    # into a clean PLUS (Stata's own stata.trk records the same destinations):
    #
    #     PLUS/py/dash_render.py          <- EXTENSION subdirectory
    #     PLUS/e/economist.scheme
    #     PLUS/s/s2color.scheme  (+ the other eighteen)
    #
    # Stata files by basename and extension, so the `schemes/' component of
    # each `f schemes/<name>.scheme' manifest line is dropped.  Neither search
    # dir above exists on such a tree, so all twenty schemes fell back --
    # including the default, which made every installed build warn.
    #
    # The `== "py"' guard is what keeps this inert everywhere else.  In the
    # repo, and in a loose copy of dash_render.py sitting in someone's
    # Downloads folder, _PLUS_ROOT is None and nothing below does anything.
    # Without the guard, dirname(dirname(__file__)) would be an unrelated
    # parent directory -- a home directory -- and treating it as an install
    # root would be a real disclosure.
    _PKG_DIR: str = os.path.dirname(os.path.abspath(__file__))
    _PLUS_ROOT: "str | None" = (
        os.path.dirname(_PKG_DIR)
        if os.path.basename(_PKG_DIR) == "py" else None
    )

    # The twenty translated StataCorp schemes dash ships.  Each is a
    # faithful translation of the same-named Stata scheme, generated from
    # test/fixtures/scheme_truth.json by scripts/extract_scheme_truth.py.
    # scheme()/theme() names one of these, a theme alias, or a .scheme file
    # in the working directory (WP-17).  The same twenty are listed by the
    # extractor's SCHEMES and by dash.ado's _dash_shipped_schemes;
    # test_scheme_resolution.py holds the copies equal.
    _BUILTIN_NAMES: frozenset[str] = frozenset({
        # Stata 18+ family (stcolor is Stata's default since v18)
        "stcolor", "stcolor_alt", "stgcolor", "stgcolor_alt", "stmono1",
        "stmono2", "stsj", "sttrans",
        # legacy defaults (s2color was the default from v10 to v17)
        "s2color", "s2color8", "s2mono", "s2gcolor", "s1color", "s1mono",
        "s1rcolor",
        # the black-and-white manual variants
        "s2manual", "s1manual", "s2gmanual",
        # journal styles
        "economist", "sj",
    })

    # Last-resort properties for when NO scheme file can be resolved at all —
    # e.g. an install whose scheme files did not ship.  Mirrors s2color so the
    # output stays recognisable.  Without this, the fallback path re-ran the
    # same failing lookup and raised, so every render on such an install ended
    # in a traceback.  Colour names here must exist in
    # OptionTranslator._COLOR_MAP.
    #
    # "Mirrors s2color" is held to by test_scheme_fallback_provenance.py,
    # which compares every public attribute of fallback() against
    # SchemeParser("s2color") parsed from the shipped file.  It was NOT true
    # when that test was written: twelve attributes differed.
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

        # The non-colour half of the promise.  These were absent, so a
        # fallback render differed from s2color in twelve translated
        # attributes, not just in provenance: no vertical grid
        # (draw_major_vgrid True -> False), grid lines at 0.8 rather than
        # 1.5, area and bar fills at 0.8 rather than opaque, and every font
        # size a step off (heading 14pt -> 13pt, text 11pt -> 10pt, note 8pt
        # -> 9pt).  "Recognisable" is the only reason this dict exists, so it
        # now carries s2color's own values for each.  Read from the shipped
        # schemes/s2color.scheme, which is itself generated from Stata's
        # scheme-s2color.scheme by scripts/extract_scheme_truth.py.
        "color grid":             "#eaf2f3",
        "graphsize x":            "5.5",
        "graphsize y":            "4",
        "gsize axis_title":       "medsmall",
        "gsize heading":          "large",
        "gsize note":             "small",
        "gsize text":             "medium",
        "gsize tick_label":       "medsmall",
        "linewidth major_grid":   "medium",
        "linewidth p":            "medium",
        "numstyle legend_cols":   "2",
        "clockdir legend_position": "6",
        "symbolsize p":           "medium",
        "intensity area":         "full",
        "intensity bar":          "full",
        "intensity p":            "inten80",
        "yesno draw_major_grid":  "no",
        "yesno draw_major_hgrid": "no",
        "yesno draw_major_vgrid": "yes",

        # The directives Stata reads for the text boxes, the minor grid and
        # the legend grid, at s2color's values (scheme-s2color.scheme lines
        # 38, 136-158, 307-322, 1204-1205, 2114-2122).  Parsed since WP-16;
        # test_scheme_fallback_provenance holds this dict to the shipped
        # s2color attribute by attribute, so a directive the parser reads
        # has to be here too.
        "color text":             "black",
        "color body":             "black",
        "color small_body":       "black",
        "color subheading":       "black",
        "color axis_title":       "black",
        "color tick_label":       "black",
        "color key_label":        "black",
        "color foreground":       "black",
        "gsize subheading":       "medium",
        "gsize body":             "medsmall",
        "gsize small_body":       "small",
        "gsize key_label":        "medsmall",
        "linewidth minor_grid":   "thin",
        "linewidth axisline":     "thin",
        "numstyle legend_rows":   "0",
        "yesno draw_minor_grid":  "no",
        "yesno draw_minor_hgrid": "no",
        "yesno draw_minor_vgrid": "no",
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
            f"{', '.join(cls._SCHEME_SEARCH_DIRS)}"
            + (f", {os.path.join(cls._PLUS_ROOT, '<letter>')}"
               if cls._PLUS_ROOT else "")
            + "). Falling back to built-in "
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
    # specifies.  Two more were corrected under WP-16: minuscule is
    # gsize-minuscule.style's 1pt (relative 0.3472, not half_tiny's
    # 0.6944), and vhuge is gsize-vhuge.style's 28pt, not 24.
    _GSIZE_PT: dict[str, str] = {
        "zero":        "0pt",
        "minuscule":   "1pt",    # relative 0.3472
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
        "vhuge":       "28pt",
        "ehuge":       "32pt",
    }

    # A bare number in a `gsize' directive is a Stata relative size: 100 =
    # the graph's smaller dimension.  The keyword table above is stated at
    # Stata's 4-inch reference (medium 3.8194 = 11pt), so the numeric
    # branch uses the same reference: 4in * 72pt / 100 = 2.88pt per unit.
    _GSIZE_NUMERIC_PT_PER_UNIT: float = 2.88
    #: The largest text size a numeric gsize may ask for.  Bokeh's FontSize
    #: property takes any CSS length, so the bound is dash's: a 1000pt
    #: glyph is taller than the graph.
    _GSIZE_MAX_PT: float = 1000.0
    #: The most rows or columns a scheme's legend grid may ask for.  Stata
    #: draws at most one key per plot and dash has no limit of its own, so
    #: the bound only refuses the absurd (`numstyle legend_rows 1000').
    _LEGEND_GRID_MAX: int = 100

    # A bare number in a `linewidth' directive is a Stata linewidth unit
    # (style/linewidth-medium.style: .30).  dash anchors the `medium'
    # keyword at 1.5px through _LWIDTH_MAP, so one unit is 5.0px.
    _LWIDTH_PX_PER_UNIT: float = 5.0

    # Stata symbolsize keyword -> points at Stata's 4-inch reference, from
    # /Applications/StataNow/ado/base/style/symbolsize-<name>.style (a
    # relative size, 100 = the graph's smaller dimension, times 2.88pt).
    # This is NOT the gsize ladder: `symbolsize medium' is 1.52778 relative
    # (4.4pt), where `gsize medium' is 3.8194 (11pt).  _markersize_px used
    # to read the keyword through _GSIZE_PT, so stcolor's `small' and
    # economist's `large' kept the text ratios rather than the marker ones.
    _SYMBOLSIZE_PT: dict[str, float] = {
        "zero":     0.0,
        "vtiny":    0.29,
        "tiny":     1.0,
        "vsmall":   1.5,
        "small":    3.0,
        "medsmall": 3.6,
        "medium":   4.4,
        "medlarge": 5.6,
        "large":    7.0,
        "vlarge":   9.0,
        "huge":     14.0,
        "vhuge":    16.0,
        "ehuge":    32.0,
    }

    # Marker diameter in Bokeh screen pixels.  The RATIOS are Stata's, from
    # _SYMBOLSIZE_PT above; the anchor is dash's own -- medium (4.4pt),
    # which is what s2color asks for, keeps the 8px dash has always drawn,
    # so the default dashboard is unchanged and a scheme that asks for
    # something else gets something else.  Stata sizes a marker relative
    # to a 4-inch-high graph, which no browser has, so a claim of absolute
    # pixel fidelity here would be a fabrication.
    _MARKER_PX_ANCHOR: float = 8.0
    _MARKER_PX_ANCHOR_PT: float = 4.4

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

    @classmethod
    def _installed_letter_dir(cls, name: str) -> "str | None":
        """The install directory that would hold *name*, or None.

        Returns a directory ONLY for one of the twenty names dash ships, and
        only on an installed tree.  That is the whole of the narrowing: the
        join's second component is one of twenty literals matching
        ``^[a-z][a-z0-9_]*$``, so no caller string can steer it out of
        _PLUS_ROOT, and a letter directory is never offered for a name dash
        does not ship.  The letter directories are SHARED -- every package
        whose files start with the same letter installs into them -- so
        resolving an arbitrary name there would expose other packages' files.
        """
        if cls._PLUS_ROOT is None:
            return None
        base = (name or "").strip()
        if os.sep in base or "/" in base:
            return None
        if base.lower().endswith(".scheme"):
            base = base[:-len(".scheme")]
        base = base.lower()
        if base not in cls._BUILTIN_NAMES:
            return None
        return os.path.join(cls._PLUS_ROOT, base[0])

    @classmethod
    def can_resolve(cls, name: str) -> bool:
        """Whether :meth:`_resolve_path` would find *name*.

        True for a shipped scheme and for a ``.scheme`` file in the working
        directory given by bare name or with the extension; False for a
        name no file answers to and for one that fails containment
        (``../x``, an absolute path, a symlink out of the working
        directory).  Quiet: no warning and no exception either way.

        ``_resolve_scheme_name`` asks this before it reports a name as
        unknown, so the gate and the parser cannot disagree about what
        resolves.  They used to: the gate refused any unknown name that did
        not end in ".scheme" before the parser's bare-name branch could
        look in the working directory, while the per-graph swap called the
        parser directly and found the file -- a bare name was drawn on the
        figure and refused for the page chrome.
        """
        raw = (name or "").strip()
        if not raw:
            return False
        # _resolve_path reads only class state.  A bare instance keeps its
        # instance signature, which test_installed_layout calls directly.
        probe = cls.__new__(cls)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                probe._resolve_path(raw)
        except (ValueError, OSError):
            return False
        return True

    def _resolve_path(self, name: str) -> str:
        """Return absolute path for a scheme name, blocking path traversal."""
        # The extension in any case: dash.ado's gate admits S2COLOR.SCHEME.
        is_file_ref = (name.lower().endswith(".scheme") or os.sep in name
                       or "/" in name)

        search_dirs = list(self._SCHEME_SEARCH_DIRS)

        if is_file_ref:
            # Try CWD first, then each scheme search dir
            candidates = [os.path.abspath(os.path.join(os.getcwd(), name))]
            candidates += [
                os.path.abspath(os.path.join(d, name)) for d in search_dirs
            ]
        else:
            # CWD first, then the package's own schemes/.  A bare base name
            # used to be looked for ONLY in the package directory, so
            # dash.sthlp's instruction -- put a .scheme file in the working
            # directory and give its base name -- did not work: the name was
            # reported as an unknown scheme, and only `scheme(mytheme.scheme)'
            # found it. The path validator below applies to these candidates
            # exactly as it does to the file-reference branch.
            candidates = [os.path.abspath(
                os.path.join(os.getcwd(), name + ".scheme"))]
            candidates += [
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

        # Last resort: the file where a `net install' put it.
        #
        # Deliberately NOT a candidate in the loop above, and the letter
        # directory is deliberately NOT appended to `allowed'.  `allowed'
        # also governs the CWD candidate, which the caller fully controls, so
        # adding <PLUS>/s to it would let a symlink named `s2color.scheme'
        # planted in the working directory point at any file in <PLUS>/s --
        # reopening BUG-51 for exactly the twenty names this is meant to
        # help.  Checking one path against its own directory keeps the
        # reachable set byte-identical to before.
        installed_dir = self._installed_letter_dir(name)
        if installed_dir is not None:
            base = name.strip().lower()
            if base.endswith(".scheme"):
                base = base[:-len(".scheme")]
            candidate = os.path.join(installed_dir, base + ".scheme")
            if os.path.isfile(candidate):
                real_dir = os.path.realpath(installed_dir)
                if os.path.realpath(candidate).startswith(real_dir + os.sep):
                    return candidate
                # The file is there but points outside its own directory.
                # Falling through silently would hide a tampered install, so
                # say so and let the caller's fallback take over.
                warnings.warn(
                    f"dash: the installed scheme file for {name!r} at "
                    f"{candidate} resolves outside {installed_dir} and was "
                    "not read. Reinstall dash.",
                    UserWarning,
                    stacklevel=3,
                )

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

    def _color_alpha(
        self, key: str, default: str = "#000000",
        default_alpha: "float | None" = None,
    ) -> "tuple[str, float | None]":
        """``(hex, opacity)`` of a scheme colour: the colour as ``_color``
        reads it, and the opacity its ``%NN`` suffix declares, or None.

        Stata's colour syntax carries an opacity on the colour itself:
        scheme-sttrans.scheme declares every p# colour as ``"26 71 111
        %20"`` and draws it at fill-opacity AND stroke-opacity 0.20
        (measured 22sep2026 in its SVG export).  ``_color`` resolves that
        through ``translate_mcolor``, which strips the suffix, so the
        opacity was read by nothing and sttrans drew opaque.

        An ABSENT key falls back to *default* and *default_alpha* together:
        a scheme that declares only ``color p1 red%50`` gives p1line, p1bar,
        p1mark and p1lineplot the colour and its opacity, as Stata's p#stub
        -> p# chain does.  A PRESENT but unresolvable colour degrades loudly
        through ``_color`` and carries no opacity.
        """
        raw = self._props.get(key, "").strip()
        if not raw:
            return default, default_alpha
        hexval, alpha = OptionTranslator.parse_color_alpha(raw)
        if hexval is None:
            return self._color(key, default), default_alpha
        return hexval, alpha

    def _gsize(self, key: str, default: str = "10pt") -> str:
        raw = self._props.get(key, "").strip().lower()
        if raw in self._GSIZE_PT:
            return self._GSIZE_PT[raw]
        # A bare number is a Stata relative size, 2.88pt per unit at the
        # 4-inch reference the keyword table is stated at.  This used to be
        # int(val * 1.2) floored at 6, dash's own invention: economist's
        # `gsize heading 6.0' drew 7pt where Stata draws 17.28pt, below its
        # own 11pt subtitle.  No floor: Stata has none.
        try:
            val = float(raw)
        except (ValueError, TypeError):
            return default
        if not math.isfinite(val):
            return default
        # Fixed decimals, never `:g': that switched to scientific notation
        # below 1e-4, and Bokeh's FontSize validator rejects `2.88e-05pt',
        # which aborted the whole figure on `gsize body 0.00001'.  Three
        # decimals of a point is finer than anything on screen; trailing
        # zeros go so that 11.0 reads "11pt".  A size that rounds to
        # nothing, or is over 1000pt, is not a size a graph can use: the
        # default, said aloud in the shape `_color' uses.
        pt = round(val * self._GSIZE_NUMERIC_PT_PER_UNIT, 3)
        if not 0 < pt <= self._GSIZE_MAX_PT:
            warnings.warn(
                f"dash scheme: size '{raw}' (from '{key}') is "
                f"{pt:g}pt, outside the (0, {self._GSIZE_MAX_PT:g}]pt a "
                f"graph can draw; falling back to {default}.",
                UserWarning,
                stacklevel=3,
            )
            return default
        return f"{pt:.3f}".rstrip("0").rstrip(".") + "pt"

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
        """A scheme line width in Bokeh pixels.

        A keyword goes through ``OptionTranslator.translate_lwidth`` (the
        _LWIDTH_MAP ladder, medium = 1.5px).  A bare number is a Stata
        linewidth UNIT -- medium is .30 -- scaled by _LWIDTH_PX_PER_UNIT so
        it lands on the same ladder.  A number used to go straight to Bokeh
        as pixels, which drew economist's ``linewidth p 1.2`` (four Stata
        mediums) at 1.2px, thinner than every keyword scheme's 1.5px.
        """
        raw = self._props.get(key, "").strip().lower()
        if not raw:
            return default
        try:
            val = float(raw)
        except ValueError:
            try:
                return OptionTranslator.translate_lwidth(raw)
            except ValueError:
                return default
        if not math.isfinite(val):
            return default
        if val < 0:
            # This was max(0.0, ...): `linewidth major_grid -4' drew an
            # invisible grid and said nothing, where a colour the scheme
            # cannot use is refused aloud.  A zero width is a legitimate
            # request (Stata's `none'); a negative one is not.
            warnings.warn(
                f"dash scheme: line width '{raw}' (from '{key}') is "
                f"negative; falling back to {default:g}px.",
                UserWarning,
                stacklevel=3,
            )
            return default
        return val * self._LWIDTH_PX_PER_UNIT

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

    def _bounded_int(self, key: str, default: "int | None", lo: int,
                     hi: int, what: str) -> "int | None":
        """``_int`` with a range, refused aloud when the value is outside it.

        A user scheme's `clockdir legend_position 99' used to become
        "right" through ``_DASH_CLOCK_SIDE.get(clock, "right")`` and
        `numstyle legend_rows 1e3' a thousand-row legend, without a word,
        where a colour the scheme cannot use is refused with a warning.
        An absent or unparseable value is ordinary inheritance and stays
        silent, as it is for a colour.
        """
        raw = self._props.get(key, "").strip()
        if not raw:
            return default
        val = self._int(key, None)
        if val is None:
            return default
        if lo <= val <= hi:
            return val
        warnings.warn(
            f"dash scheme: {what} '{raw}' (from '{key}') is outside "
            f"{lo}-{hi}; falling back to {default!r}.",
            UserWarning,
            stacklevel=3,
        )
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
        # The text boxes Stata draws each element with (scheme-s2color
        # .scheme and style/textboxstyle-*.style): subtitle() is the
        # subheading box, caption() the body box, note() the small_body box
        # in the BODY colour, legend keys key_label, axis titles axis_title,
        # tick labels tick_label; `color text' is the KPI card's text (the
        # card is drawn as Stata's legend box).  Every shipped scheme
        # declares these; the default is s2color's black.
        self.subheading_color: str = self._color("color subheading", "#000000")
        self.body_color: str = self._color("color body", "#000000")
        # Stata's note textbox (textboxstyle-small_body.style) takes its
        # colour from `color small_body', equal to `color body' in every
        # shipped scheme; read the key Stata reads.
        self.small_body_color: str = self._color("color small_body", "#000000")
        self.text_color: str = self._color("color text", "#000000")
        self.axis_title_color: str = self._color("color axis_title", "#000000")
        self.tick_label_color: str = self._color("color tick_label", "#000000")
        self.key_label_color: str = self._color("color key_label", "#000000")

        # Per-plot color cycles (15 entries), each colour beside the
        # opacity its scheme declares on it (Stata's %NN suffix: sttrans's
        # `color p1 "26 71 111 %20"', shipped as `#1a476f%20'), None where
        # the colour is opaque.  The fixture records the same lists as
        # p_colors_opacity and its line/bar/mark/lineplot twins;
        # default_alpha() reads them where default_color() reads the hex.
        _p = [self._color_alpha(f"color p{i}") for i in range(1, 16)]
        self.p_colors: list[str] = [c for c, _ in _p]
        self.p_alphas: "list[float | None]" = [a for _, a in _p]
        _pl = [
            self._color_alpha(f"color p{i}line", self.p_colors[i - 1],
                              self.p_alphas[i - 1])
            for i in range(1, 16)
        ]
        self.p_line_colors: list[str] = [c for c, _ in _pl]
        self.p_line_alphas: "list[float | None]" = [a for _, a in _pl]
        _pb = [
            self._color_alpha(f"color p{i}bar", self.p_colors[i - 1],
                              self.p_alphas[i - 1])
            for i in range(1, 16)
        ]
        self.p_bar_colors: list[str] = [c for c, _ in _pb]
        self.p_bar_alphas: "list[float | None]" = [a for _, a in _pb]
        _pm = [
            self._color_alpha(f"color p{i}mark", self.p_colors[i - 1],
                              self.p_alphas[i - 1])
            for i in range(1, 16)
        ]
        self.p_mark_colors: list[str] = [c for c, _ in _pm]
        self.p_mark_alphas: "list[float | None]" = [a for _, a in _pm]

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
        _plp = []
        for i in range(1, 16):
            _dc, _da = self._color_alpha("color plineplot",
                                         self.p_colors[i - 1],
                                         self.p_alphas[i - 1])
            _plp.append(self._color_alpha(f"color p{i}lineplot", _dc, _da))
        self.p_lineplot_colors: list[str] = [c for c, _ in _plp]
        self.p_lineplot_alphas: "list[float | None]" = [a for _, a in _plp]

        # Default line/grid widths
        self.default_line_width: float = self._lwidth("linewidth p", 1.5)
        self.grid_line_width: float = self._lwidth("linewidth major_grid", 0.8)
        # `linewidth minor_grid' is `thin' in every shipped scheme.
        self.minor_grid_line_width: float = self._lwidth(
            "linewidth minor_grid", OptionTranslator.translate_lwidth("thin"))
        # `linewidth axisline', `thin' in every shipped scheme.  It was
        # extracted, shipped in all twenty files and the fallback dict,
        # and read by nothing: every axis line was Bokeh's 1px.  Applied
        # in apply_to_figure.  (`color foreground' is carried alongside
        # it in the same files and has no consumer here by design: Stata
        # reads it for elements dash does not draw.)
        self.axis_line_width: float = self._lwidth(
            "linewidth axisline", OptionTranslator.translate_lwidth("thin"))

        # Fill intensities
        self.fill_alpha: float = self._intensity("intensity p", 0.8)
        self.bar_alpha: float = self._intensity("intensity bar", 0.8)
        self.area_alpha: float = self._intensity("intensity area", 0.8)

        # Font sizes
        self.text_font_size: str = self._gsize("gsize text", "10pt")
        self.heading_font_size: str = self._gsize("gsize heading", "13pt")
        self.axis_title_font_size: str = self._gsize("gsize axis_title", "10pt")
        self.tick_label_font_size: str = self._gsize("gsize tick_label", "10pt")
        # `gsize note' exists in every scheme, but Stata's note textbox does
        # not read it (textboxstyle-small_body.style is what note() uses),
        # so this is parsed for the fidelity fixture and drawn from nowhere.
        self.note_font_size: str = self._gsize("gsize note", "9pt")
        # The text-box sizes Stata does read; defaults are s2color's.
        self.subheading_font_size: str = self._gsize("gsize subheading", "11pt")
        self.body_font_size: str = self._gsize("gsize body", "10pt")
        self.small_body_font_size: str = self._gsize("gsize small_body", "8pt")
        self.key_label_font_size: str = self._gsize("gsize key_label", "10pt")

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
        # Stata's real answer for fifteen of the twenty is `yes'.
        self.draw_major_hgrid: bool = self._yesno("yesno draw_major_hgrid", False)
        self.draw_major_vgrid: bool = self._yesno("yesno draw_major_vgrid", False)
        # The minor grid, by the same per-axis rule (axisstyle-horizontal_
        # default.style: `set draw_minor_grid scheme draw_minor_hgrid').
        # Every shipped scheme says no on both axes; `color minor_grid' was
        # applied unconditionally, and Bokeh's five minor ticks per
        # interval then drew four lines Stata never draws.
        self.draw_minor_hgrid: bool = self._yesno("yesno draw_minor_hgrid", False)
        self.draw_minor_vgrid: bool = self._yesno("yesno draw_minor_vgrid", False)

        # Default marker size for the p cycle, and legend placement.
        # Parsed only; consumers land in sections 10 and 11.
        self.symbolsize: str = self._props.get("symbolsize p", "").strip()
        # ...and the size the renderer actually draws.  Parsed but never
        # consumed: every scheme drew an 8px marker, so stcolor's `small'
        # and economist's `large' were indistinguishable.
        self.marker_size: float = self._markersize_px(self.symbolsize)
        # Stata's clockdir is a numeric clock position (1-12), so expose it as
        # a number rather than the raw string — consumers compare it as one.
        # Range-checked: a hostile 99 used to reach _DASH_CLOCK_SIDE.get(
        # clock, "right") and place the legend without a word.
        self.legend_position: "int | None" = self._bounded_int(
            "clockdir legend_position", None, 1, 12, "clock position")
        self.legend_cols: "int | None" = self._bounded_int(
            "numstyle legend_cols", None, 0, self._LEGEND_GRID_MAX,
            "legend column count")
        # `numstyle legend_rows': 0 in every shipped scheme, meaning "as
        # many as the columns need".
        self.legend_rows: int = self._bounded_int(
            "numstyle legend_rows", 0, 0, self._LEGEND_GRID_MAX,
            "legend row count") or 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    #: The plot types whose colour is a MARKER colour: `color p#mark'.
    #: The mapper asks for one of these for the MARKER glyph only: dot asks
    #: for "scatter", dropline's dot for "dropline", rcapsym's symbols for
    #: "rscatter".  A Segment -- spike, rspike, rcap, pcspike, pcarrow,
    #: pcbarrow, the drop of a dropline, the spine and caps of an rcapsym
    #: -- asks with its own type name and falls through to `color p#':
    #: Stata's pstyle keeps p#mark apart from the p# its "other" plots
    #: draw with, and every one of those mappers used to ask for "scatter".
    _MARKER_PLOT_TYPES: frozenset = frozenset({
        "scatter", "scatteri", "dot", "dropline", "rscatter", "pcscatter",
    })

    def _cycle_for(self, plot_type: str) -> str:
        """Which p# colour cycle *plot_type* reads: ``"lineplot"``,
        ``"line"``, ``"bar"``, ``"mark"`` or the plain ``"p"``.

        One dispatch for ``default_color`` and ``default_alpha``, so the
        opacity is always read from the cycle the colour came from.
        """
        # `color p#line' is the CONNECTING line of twoway connected.  A plain
        # line plot reads `color p#lineplot', falling back to `color p#'.
        if plot_type in {"line", "tsline", "tsrline", "mspline", "mband",
                         "rline"}:
            return "lineplot"
        if plot_type in {"connected", "rconnected"}:
            return "line"
        if plot_type in {"bar", "rbar", "area", "rarea", "histogram"}:
            return "bar"
        # A MARKER reads `color p#mark' (style/markerstyle-p#.style), which
        # falls back to `color p#' at parse time.  Equal in every shipped
        # scheme, so nothing rendered changes; a user scheme declaring
        # `color p1mark' used to be read into p_mark_colors and drawn from
        # nowhere.
        if plot_type in self._MARKER_PLOT_TYPES:
            return "mark"
        return "p"

    def default_color(self, index: int, plot_type: str = "scatter") -> str:
        """Return the default CSS hex color for the plot at *index*.

        Args:
            index:     Zero-based plot index within the figure.
            plot_type: The plot type, or the glyph's own class of it: a
                       marker type (``_MARKER_PLOT_TYPES``) reads ``color
                       p#mark``; ``"line"`` and its kin ``color
                       p#lineplot``; ``"connected"`` ``color p#line``;
                       ``"bar"``/``"area"`` ``color p#bar``; anything else
                       (``"spike"``, ``"rcap"``, ``"pcarrow"``, ...) the
                       plain ``color p#``.
        """
        idx = index % 15
        cycle = self._cycle_for(plot_type)
        if cycle == "lineplot":
            return self.p_lineplot_colors[idx]
        if cycle == "line":
            return self.p_line_colors[idx]
        if cycle == "bar":
            return self.p_bar_colors[idx]
        if cycle == "mark":
            return self.p_mark_colors[idx]
        return self.p_colors[idx]

    def default_alpha(self, index: int,
                      plot_type: str = "scatter") -> "float | None":
        """The opacity the scheme declares on the colour ``default_color``
        returns for *index* and *plot_type*, or None when it declares none.

        sttrans declares every p# colour at %20, and Stata draws it as
        fill-opacity and stroke-opacity 0.20: a real opacity, where
        `intensity p inten80' is a lightening that dash only approximates
        as alpha.  A declared opacity therefore wins over ``fill_alpha``,
        ``bar_alpha`` and ``area_alpha`` at every mapper site that draws a
        scheme alpha (``GlyphMapper._scheme_alpha``), and sets a line's
        alpha, which no intensity reaches; a user colour with its own %NN
        still wins over both.
        """
        idx = index % 15
        cycle = self._cycle_for(plot_type)
        if cycle == "lineplot":
            return self.p_lineplot_alphas[idx]
        if cycle == "line":
            return self.p_line_alphas[idx]
        if cycle == "bar":
            return self.p_bar_alphas[idx]
        if cycle == "mark":
            return self.p_mark_alphas[idx]
        return self.p_alphas[idx]

    def _markersize_px(self, keyword: str) -> float:
        """Convert a Stata markersize keyword to Bokeh screen pixels.

        Args:
            keyword: The scheme's ``symbolsize p`` value, e.g. ``"medium"``.
                     A bare number is a Stata relative size (2.88pt per
                     unit at the 4-inch reference, like ``gsize``).

        Returns:
            A diameter in pixels; the anchor is dash's own 8px at Stata's
            ``medium`` (4.4pt), and everything else keeps Stata's ratio to
            it: stcolor's ``small`` is 5.45px, economist's ``large`` 12.73px.
        """
        kw = (keyword or "").strip().lower()
        if not kw:
            return self._MARKER_PX_ANCHOR
        if kw in self._SYMBOLSIZE_PT:
            pt = self._SYMBOLSIZE_PT[kw]
        else:
            try:
                val = float(kw.lstrip("*"))
            except ValueError:
                return self._MARKER_PX_ANCHOR
            if not math.isfinite(val):
                return self._MARKER_PX_ANCHOR
            pt = val * self._GSIZE_NUMERIC_PT_PER_UNIT
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
        # both by default, so dash drew a grid Stata does not draw in
        # fourteen of the twenty shipped schemes -- BOTH grids under
        # s1color, s1manual, s1mono, s1rcolor and stmono1, which draw none
        # at all.
        #
        # `grid_line_color = None' is how the rest of the file expresses "no
        # grid" (see the xlabel(, nogrid) path), so an explicit nogrid and a
        # scheme-level no stay indistinguishable, which is what lets an
        # explicit option override the scheme without special-casing.
        for grids, draw, draw_minor in (
                (fig.xgrid, self.draw_major_hgrid, self.draw_minor_hgrid),
                (fig.ygrid, self.draw_major_vgrid, self.draw_minor_vgrid)):
            for grid in grids:
                grid.grid_line_color = self.grid_color if draw else None
                grid.grid_line_width = self.grid_line_width
                # The minor grid by the same rule.  `color minor_grid' was
                # set unconditionally here, and with Bokeh's five minor
                # ticks per interval that drew four lines per major
                # interval on both axes under every scheme, when no shipped
                # scheme draws a minor grid at all.
                grid.minor_grid_line_color = (self.minor_grid_color
                                              if draw_minor else None)
                grid.minor_grid_line_width = self.minor_grid_line_width

        # The figure title is Stata's heading box: `color heading' and
        # `gsize heading'.  Both were parsed and reached only the dashboard
        # header's CSS; the Bokeh title stayed #444444 / 13px under every
        # scheme, s1rcolor's white-on-black included.  _dash_figure_title
        # runs after this, so an explicit title(, size() color()) wins.
        if fig.title is not None:
            fig.title.text_color = self.title_color
            fig.title.text_font_size = self.heading_font_size

        for axis in list(fig.xaxis) + list(fig.yaxis):
            axis.axis_line_color = self.axis_line_color
            axis.axis_line_width = self.axis_line_width
            axis.axis_label_text_font_size = self.axis_title_font_size
            axis.major_label_text_font_size = self.tick_label_font_size
            # The axis_title and tick_label boxes' colours.
            axis.axis_label_text_color = self.axis_title_color
            axis.major_label_text_color = self.tick_label_color

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
        # The dashboard subtitle is Stata's subheading box, not `gsize
        # text' in the heading colour.
        sc = html.escape(self.subheading_color)
        ss = html.escape(self.subheading_font_size)
        # The KPI card is drawn as Stata's legend box: `color legend' fills
        # it, `color legend_line' borders it, `color text' is its text.  A
        # full `border' shorthand, because the card used to carry an inline
        # `border:1px solid #dee2e6' and a `border-color' alone never won
        # against it.
        lbg = html.escape(self.legend_bg_color)
        lbc = html.escape(self.legend_border_color)
        txt = html.escape(self.text_color)
        return (
            f"  body {{ background-color: {bg}; }}\n"
            f"  .db-title {{ color: {tc}; font-size: {hs}; }}\n"
            f"  .db-subtitle {{ color: {sc}; font-size: {ss}; }}\n"
            f"  .db-kpi-card {{ background-color: {lbg}; "
            f"border: 1px solid {lbc}; color: {txt}; }}\n"
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


# The smallest bar width dash will pass to Bokeh.  Bokeh raises
# "Distances must be positive!" on anything at or below zero, and that
# exception is not confined to the bar -- it loses the whole dashboard.
# The longest function() expression dash will validate.  _validate_expr_node
# recurses once per AST node, so a machine-generated expression of tens of
# thousands of terms raised RecursionError -- which is not a SyntaxError or a
# ValueError, so it escaped the guard and lost the whole dashboard.
_MAX_EXPR_CHARS = 5000


def _floats_only(tree: "_ast.AST") -> "_ast.AST":
    """Make every numeric literal in *tree* a float.

    Stata evaluates in double precision, so ``9^9^9^9`` overflows to missing.
    Python's integer power is exact and unbounded, so the same expression
    computed a number with billions of digits: measured past 20 seconds with
    the GIL held throughout, which means Stata's Break key cannot recover it
    and the process must be killed.

    Turning the constants into floats gives Python the same arithmetic Stata
    has -- ``9.0 ** 9.0 ** 9.0`` is ``inf`` immediately -- so an expression
    that overflows draws nothing instead of never returning.

    Args:
        tree: A parsed, already-validated expression tree.

    Returns:
        The same tree, with integer constants replaced by floats.
    """
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool):
            node.value = float(node.value)
    return _ast.fix_missing_locations(tree)


# Opacity of a confidence band.
#
# Deliberately a constant: it is a legibility judgement -- the band must read
# as an envelope around the fit and not as a filled area in its own right --
# and no scheme key describes it. Every *ci layer uses it, and the generated
# app used to invent its own 0.35 for lpolyci.
_CI_BAND_ALPHA = 0.2

_MIN_BAR_WIDTH = 1e-9

# The largest number of median bands dash will draw.  The generated server
# app has always clamped to this; the standalone renderer had no bound, so
# bands(1000000000) allocated 8 GB for the bin edges alone.
_MAX_MBANDS = 1000


def _with_color_alias(options: dict, specific: str) -> dict:
    """Let Stata's generic ``color()`` stand in for a specific colour option.

    ``color(colorstyle)`` is Stata's series colour: the marker colour on
    ``scatter``, the line colour on ``line``, the fill on ``bar`` and
    ``area``. dash read it in five mappers -- area, bar, histogram, dropline
    and rcapsym -- and nowhere else, so ``dash scatter mpg weight,
    color(navy)`` drew the scheme's colour and reported color() as an option
    it had ignored. The same option on ``bar`` was honoured, and reported
    ignored just the same.

    The specific spelling always wins: a user who wrote both ``color()`` and
    ``mcolor()`` meant the second to be the marker colour.

    Args:
        options:  Translated plot-level options.
        specific: The option ``color()`` stands in for here.

    Returns:
        *options* unchanged, or a copy carrying *specific*.
    """
    generic = str(options.get("color", "") or "").strip()
    if generic and not str(options.get(specific, "") or "").strip():
        return dict(options, **{specific: generic})
    return options


def _jitter_seed(options: dict) -> "int | None":
    """Return the jitter RNG seed a plot asked for, under either spelling.

    Stata's option is ``jitterseed(#)``; ``jseed(#)`` is dash's own shorthand
    and the only one the code used to read. Five separate places read it --
    ``_build_jitter_source``, ``map_dropline``, ``map_scatteri``,
    ``_resolve_seed`` and the generated server app -- so a command pasted out
    of a do-file drew an unseeded cloud, different on every render, while
    dash reported ``jitterseed()`` as an option it had ignored.

    ``jseed()`` wins when both are given: it is the more specific spelling
    and the one a dash user wrote deliberately.

    Args:
        options: Translated plot-level options.

    Returns:
        The seed, or ``None`` when none was given or it is not a
        non-negative integer -- which is reported: numpy's Generator takes
        nothing else, so ``default_rng(-1)`` raised out of the mapper and
        took the render down, and ``2.5`` was quietly truncated to 2.
    """
    for key in ("jseed", "jitterseed"):
        raw = str(options.get(key, "") or "").strip()
        if raw:
            # The same rule as dash.ado's table (jitterseed=int,0): any
            # spelling of a non-negative integer, 123, 123.0 or 1e6 alike.
            try:
                val = float(raw)
            except ValueError:
                val = float("nan")
            if np.isfinite(val) and val >= 0 and val == int(val):
                return int(val)
            # Once per render: every by() panel read it and said so again.
            _dash_warn_once(
                (key, raw, "seed"),
                f"dash: {key}({_dash_display(raw)}) must be a non-negative "
                f"integer; drawing unseeded.",
            )
            return None
    return None


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
        default_level: float = _DEFAULT_LEVEL,
    ) -> None:
        """Initialise the mapper with an optional OptionTranslator and scheme.

        ``default_level`` is the dashboard's c(level), which a confidence
        band draws at when its layer names no level() of its own.  The
        mapper owns it so both render modes resolve it in one place.
        """
        self.tr = translator or OptionTranslator()
        self.default_level: float = float(default_level)
        self.date_vars: dict[str, str] = {}
        self.numeric_formats: dict[str, str] = {}
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
        layer: str = "scatter",
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

        # Through _stat_option_float, as dropline's is: a word or a
        # negative number from a hand-written spec was dropped in silence
        # here while dropline named it.  (dash.ado refuses both before a
        # command gets this far.)  A value above 100 is clamped, as it
        # always was.
        jitter_pct = _stat_option_float(options, "jitter", 0.0, layer,
                                        lo=0.0)
        if jitter_pct is None or jitter_pct <= 0:
            return source, xvar, yvar

        # Clamp to [1, 100]
        jitter_pct = min(100.0, jitter_pct)

        seed_val: int | None = _jitter_seed(options)

        x_arr = np.asarray(source.data[xvar], dtype=float)
        y_arr = np.asarray(source.data[yvar], dtype=float)
        x_jit, y_jit = _apply_jitter(x_arr, y_arr, jitter_pct, seed_val)

        # Build new data dict preserving all original columns
        new_data = {k: list(v) for k, v in source.data.items()}
        new_data["_x_jit"] = x_jit.tolist()
        new_data["_y_jit"] = y_jit.tolist()
        return ColumnDataSource(new_data), "_x_jit", "_y_jit"

    @staticmethod
    def _carry_cols(source, data, selector=None):
        """Copy the caller's other columns into a derived source's data.

        A mapper that rebuilds its source from the plotted variables alone
        drops everything else the caller put there: the marker-label column,
        the row identity, and the variables ``hover()`` asks for.  Three
        mappers had already grown a one-off copy of the mlabel column for
        exactly this reason; this does the same thing once, for every
        column, so ``hover(foreign)`` reaches a bar, a spike and a range cap
        as well.

        A key already present in *data* is never overwritten -- the derived
        columns ("x", "y", "x0") are the ones the glyph reads -- and a column
        whose length does not match is skipped rather than guessed at.

        Args:
            source:   The ColumnDataSource the caller passed in.
            data:     The derived column dict, modified in place.
            selector: A boolean mask or index array applied to each carried
                      column, or None to carry it whole.

        Returns:
            *data*, for chaining.
        """
        try:
            _n = len(next(iter(data.values())))
        except (StopIteration, TypeError):
            return data
        for _k, _v in dict(getattr(source, "data", {}) or {}).items():
            if _k in data:
                continue
            try:
                _col = np.asarray(_v, dtype=object)
                if selector is not None:
                    _col = _col[selector]
                if len(_col) != _n:
                    continue
                data[_k] = _col.tolist()
            except (TypeError, ValueError, IndexError, KeyError):
                continue
        return data

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
            source=source, fill_alpha=_CI_BAND_ALPHA, fill_color=color,
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
        # The name the user wrote, for the note: color() is folded onto
        # lcolor() below, and a note reading lcolor(x) for a color(x) the
        # user never typed would send them to the wrong option.
        _lc_name = ("lcolor" if str(options.get("lcolor", "") or "").strip()
                    else "color")
        # A bar's own blcolor() is applied by map_bar just before this call,
        # so color() must not stand in for lcolor() and overwrite it.
        if not str(options.get("blcolor", "") or "").strip():
            options = _with_color_alias(options, "lcolor")
        if "lcolor" in options:
            if OptionTranslator._means_no_color(options["lcolor"]):
                # Stata draws nothing; this used to resolve through the
                # colour table and paint a line.
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["lcolor"], _lc_name)
                    if color:
                        glyph.line_color = color
                    if alpha is not None and hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = alpha
                except AttributeError:
                    pass
        # An unknown width or pattern used to be dropped without a word
        # (`except ValueError: pass'); it is named, and the scheme's kept.
        if "lwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["lwidth"])
            except ValueError:
                _dash_style_note("lwidth", options["lwidth"], "line width")
        if "lpattern" in options:
            try:
                glyph.line_dash = self.tr.translate_lpattern(options["lpattern"])
            except ValueError:
                _dash_style_note("lpattern", options["lpattern"],
                                 "line pattern")
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
        # The name the user wrote, for the note: color() is folded onto
        # mcolor() below, and a note reading mcolor(x) for a color(x) the
        # user never typed would send them to the wrong option.
        _mc_name = ("mcolor" if str(options.get("mcolor", "") or "").strip()
                    else "color")
        options = _with_color_alias(options, "mcolor")
        # Every unknown style name below is NAMED through _dash_style_note
        # and the scheme's value kept.  These were `except ValueError:
        # pass' -- msymbol(nonsense) drew a circle and said nothing, where
        # twoway prints its `named style not found' note.  AttributeError
        # stays silent: it means the glyph has no such property, which is
        # the mapper's business, not the user's.
        # Handle generic 'm → marker' abbreviation as msymbol alias
        if "marker" in options and "msymbol" not in options:
            try:
                glyph.marker = self.tr.translate_msymbol(options["marker"])
            except ValueError:
                _dash_style_note("marker", options["marker"], "marker symbol")
            except AttributeError:
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
                    color, alpha = self.tr.parse_color_alpha(
                        options["mcolor"], _mc_name)
                    if color:
                        glyph.fill_color = color
                        glyph.line_color = color
                    if alpha is not None:
                        if hasattr(glyph, "fill_alpha"):
                            glyph.fill_alpha = alpha
                        if hasattr(glyph, "line_alpha"):
                            glyph.line_alpha = alpha
                except AttributeError:
                    pass
        if "msymbol" in options:
            try:
                glyph.marker = self.tr.translate_msymbol(options["msymbol"])
            except ValueError:
                _dash_style_note("msymbol", options["msymbol"],
                                 "marker symbol")
            except AttributeError:
                pass
        if "msize" in options:
            try:
                glyph.size = self.tr.translate_msize(options["msize"])
            except ValueError:
                _dash_style_note("msize", options["msize"], "size")
        # mfcolor sets the fill color independently of the line/outline color.
        # Supports color%alpha notation; applied after mcolor so it wins.
        if "mfcolor" in options:
            if OptionTranslator._means_no_color(options["mfcolor"]):
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["mfcolor"], "mfcolor")
                    if color:
                        glyph.fill_color = color
                    if alpha is not None and hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = alpha
                except AttributeError:
                    pass
        # lcolor sets the marker border (outline) color independently of fill.
        if "lcolor" in options:
            if OptionTranslator._means_no_color(options["lcolor"]):
                if hasattr(glyph, "line_alpha"):
                    glyph.line_alpha = 0.0
            else:
                try:
                    color, alpha = self.tr.parse_color_alpha(
                        options["lcolor"], "lcolor")
                    if color and hasattr(glyph, "line_color"):
                        glyph.line_color = color
                    if alpha is not None and hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = alpha
                except AttributeError:
                    pass
        # lwidth sets the marker border width.
        if "lwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["lwidth"])
            except ValueError:
                _dash_style_note("lwidth", options["lwidth"], "line width")
            except AttributeError:
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
                    color, alpha = self.tr.parse_color_alpha(
                        options["mlcolor"], "mlcolor")
                    if color and hasattr(glyph, "line_color"):
                        glyph.line_color = color
                    if alpha is not None and hasattr(glyph, "line_alpha"):
                        glyph.line_alpha = alpha
                except AttributeError:
                    pass
        if "mlwidth" in options:
            try:
                glyph.line_width = self.tr.translate_lwidth(options["mlwidth"])
            except ValueError:
                _dash_style_note("mlwidth", options["mlwidth"], "line width")
            except AttributeError:
                pass
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
                angle_deg = float(str(options["msangle"]).strip())
                if not math.isfinite(angle_deg):
                    raise ValueError(angle_deg)
            except (TypeError, ValueError):
                _dash_style_note("msangle", options["msangle"], "angle")
            else:
                if hasattr(glyph, "angle"):
                    glyph.angle = math.radians(angle_deg)
                    if hasattr(glyph, "angle_units"):
                        glyph.angle_units = "rad"

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
                    color, alpha = self.tr.parse_color_alpha(
                        options["fcolor"], "fcolor")
                    if color:
                        glyph.fill_color = color
                    if alpha is not None and hasattr(glyph, "fill_alpha"):
                        glyph.fill_alpha = alpha
                except AttributeError:
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
                val = str(options["fintensity"]).strip()
                # Stata fintensity: 0-100 (percentage) or keywords inten0-inten100
                if val.startswith("inten"):
                    pct = float(val[5:]) / 100.0
                else:
                    pct = float(val) / 100.0
                if not math.isfinite(pct):
                    raise ValueError(val)
            except (TypeError, ValueError):
                _dash_style_note("fintensity", options["fintensity"],
                                 "fill intensity")
            else:
                pct = max(0.0, min(1.0, pct))
                if hasattr(glyph, "fill_alpha"):
                    glyph.fill_alpha = pct

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
                    visible=False, name=f"{_DASH_SWATCH_PREFIX}{factor}",
                )
                legend_items.append(LegendItem(label=factor, renderers=[_r]))
            if "__missing__" in factors:
                _rm = fig.scatter(
                    x=[float("nan")], y=[float("nan")],
                    color=missing_color, size=0,
                    visible=False, name=f"{_DASH_SWATCH_PREFIX}__missing__",
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

        mlabel_var, _extras = _dash_mlabel_names(options)
        if _extras:
            # dash.ado validates mlabel() as one variable; a spec written by
            # hand may still carry several.  The first labels, the rest are
            # named -- once per render, whatever the source carries.
            _dash_warn_once(
                ("mlabel", str(options["mlabel"]), "extras"),
                f"dash: mlabel({_dash_display(options['mlabel'])}) takes one "
                f"variable; labelling with {_dash_display(mlabel_var)} and "
                f"ignoring {_dash_display(' '.join(_extras))}.",
            )
        if not mlabel_var:
            return
        if mlabel_var not in source.data:
            # Every source that reaches here carries the label column when
            # the data has it (map_line's is the frame, map_dropline's is
            # built with it), so its absence means the data lacks the
            # variable.  A hand-written spec's mistake -- dash.ado refuses
            # it from a command -- used to draw nothing without a word.
            _dash_warn_once(
                ("mlabel", mlabel_var, "missing"),
                f"dash: mlabel({_dash_display(mlabel_var)}): the variable is "
                f"not in the data; drawing no labels.",
            )
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

        # An unknown colour, size, position or gap is NAMED and the default
        # kept; each of these was an `except ValueError: pass'.
        if "mlabcolor" in options:
            try:
                kwargs["text_color"] = self.tr.translate_mcolor(options["mlabcolor"])
            except ValueError:
                _dash_style_note("mlabcolor", options["mlabcolor"], "colour")

        if "mlabsize" in options:
            try:
                size_px = self.tr.translate_msize(options["mlabsize"])
                kwargs["text_font_size"] = f"{size_px}px"
            except ValueError:
                _dash_style_note("mlabsize", options["mlabsize"], "size")

        # mlabposition: Stata clock positions 0-12
        # Clock positions: 3=right (default), 9=left, 12=above, 6=below
        offset_map = {
            0: (0, 0), 1: (3, 3), 2: (3, 2), 3: (4, 0),
            4: (3, -2), 5: (3, -3), 6: (0, -4), 7: (-3, -3),
            8: (-3, -2), 9: (-4, 0), 10: (-3, 2), 11: (-3, 3), 12: (0, 4),
        }
        pos = str(options.get("mlabposition", "3") or "3").strip()
        try:
            p = int(pos)
        except (ValueError, TypeError):
            p = -1
        if p not in offset_map:
            # twoway: mlabposition(13) and (2.5) draw at 3 o'clock with a
            # `named style not found' note; dash used to draw there silently.
            _dash_style_note("mlabposition", pos, "clock position",
                             "3 (right)")
            p = 3
        kwargs["x_offset"], kwargs["y_offset"] = offset_map[p]

        if "mlabgap" in options:
            try:
                # mlabgap(small) threw here and was silently dropped: Stata
                # takes a text size OR a number, and int(float()) accepts
                # only the number.
                gap = int(float(self.tr.translate_msize(options["mlabgap"])))
            except (ValueError, TypeError):
                _dash_style_note("mlabgap", options["mlabgap"], "size")
            else:
                kwargs["x_offset"] = kwargs.get("x_offset", 4) + gap
                kwargs["y_offset"] = kwargs.get("y_offset", 4) + gap

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

    def _scheme_alpha(self, color_idx: int, plot_type: str,
                      intensity_alpha: float) -> float:
        """The alpha the scheme draws the plot at *color_idx* with.

        Stata's intensity (``intensity p inten80``) is a lightening towards
        the background, which dash approximates as alpha; a colour's own
        ``%NN`` suffix IS an opacity.  sttrans declares every p# colour at
        %20, and Stata's SVG export draws fill-opacity and stroke-opacity
        0.20 (measured 22sep2026), where dash drew the intensity's 0.8 like
        every other scheme.  When the scheme declares an opacity it is the
        real value and wins over the approximation.  A user mcolor(),
        fcolor() or lcolor() with its own %NN still wins over both: the
        option appliers run after the glyph is drawn.
        """
        declared = self.scheme.default_alpha(color_idx, plot_type)
        return intensity_alpha if declared is None else declared

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
            # Fill AND outline: Stata's SVG carries fill-opacity and
            # stroke-opacity alike, 0.20 under sttrans.
            alpha=self._scheme_alpha(color_idx, "scatter",
                                     self.scheme.fill_alpha),
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
        _mlab = _dash_mlabel_names(options)[0]
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
        # A line has no intensity-derived alpha (Stata's `intensity p' is
        # for fills), so only a colour's declared opacity sets one:
        # sttrans's %20 is stroke-opacity 0.20 in Stata's own SVG, for a
        # line plot and for connected's connecting line alike.
        _line_alpha = self.scheme.default_alpha(
            color_idx, "connected" if connected else "line")
        if _line_alpha is not None:
            _line_kwargs["line_alpha"] = _line_alpha
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
        # Masked by the layer's own view: a per-plot `if', a by() facet
        # panel or a linked graph's qualifier.  map_area builds its own
        # ColumnDataSource below, so a view attached to the renderer would
        # have nothing left to filter.
        x_arr, y_arr = self._masked(source, view, xvar, yvar)

        # Bokeh's varea joins its points in the order it is given them, and
        # Stata's twoway area draws along x -- so unsorted rows produce a
        # self-intersecting polygon, silently, with every point present and
        # correct.  map_line and map_connected have always sorted; this did
        # not.  Measured on x = [3, 1, 2]: map_line gave [1, 2, 3] and
        # map_area gave [3, 1, 2].  Found while comparing the two render
        # modes, where the generated server app's own area branch sorts and
        # this one did not.
        if len(x_arr):
            _order = np.argsort(x_arr, kind="stable")
            x_arr = x_arr[_order]
            y_arr = y_arr[_order]

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
                      fill_alpha=self._scheme_alpha(
                          color_idx, "area", self.scheme.area_alpha),
                      legend_label=yvar)

        # Honour fill color option.  An unknown name was dropped in silence
        # here, and nothing downstream reads color() for an area.
        if "color" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["color"])
            except ValueError:
                _dash_style_note("color", options["color"], "colour")

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
        # Masked by the layer's own view BEFORE the source is rebuilt.
        # The view's BooleanFilter is sized to the CALLER's source; the
        # source built below is shorter once rows with missing values are
        # dropped, and Bokeh applies a mask by position -- so attaching the
        # view to the rebuilt source selected the wrong observations.
        #
        # The raw mask rather than _masked(): xvar may be a STRING column
        # here (the fallback below spaces string categories uniformly) and
        # _masked casts to float.  Masking before dropna also means the
        # bar width below is derived from the rows actually plotted, so a
        # qualified bar chart looks like the same chart drawn from that
        # subset alone.
        _bar_cols = {xvar: source.data[xvar], yvar: source.data[yvar]}
        # Every other column the caller put in the source rides along: the
        # marker-label column, and any variable hover() names.  A bar chart
        # used to rebuild its source from the two plotted variables alone,
        # so hover(foreign) had nothing to read.
        _bar_n = len(_bar_cols[xvar])
        for _bk, _bv in dict(source.data or {}).items():
            if _bk not in _bar_cols and len(_bv) == _bar_n:
                _bar_cols[_bk] = list(_bv)
        df = pd.DataFrame(_bar_cols)
        _bar_sel = self._view_mask(view, len(df))
        if _bar_sel is not None:
            df = df[_bar_sel]
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

        # barwidth() / width() options override the auto-computed bar width.
        #
        # Read through _stat_option_float so a value that is not a number, not
        # finite, or not positive is REPORTED and the computed width used.
        # A bare float() let barwidth(-5) through to Bokeh, which raised
        # "Distances must be positive!" and lost the whole dashboard -- Stata
        # itself rejects a negative barwidth with a clear r(198).
        for key in ("barwidth", "width"):
            if key in options:
                _bw = _stat_option_float(options, key, None, "bar",
                                         lo=_MIN_BAR_WIDTH)
                if _bw is not None:
                    bar_width = _bw
                break

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
            fill_alpha=self._scheme_alpha(color_idx, "bar",
                                          self.scheme.bar_alpha),
        )
        # The outline takes the colour's declared opacity too: Stata's SVG
        # draws a sttrans bar with stroke-opacity 0.20 beside its
        # fill-opacity 0.20.  No intensity reaches an outline, so nothing
        # is passed where none is declared.
        _bar_line_alpha = self.scheme.default_alpha(color_idx, "bar")
        if _bar_line_alpha is not None:
            _vbar_kwargs["line_alpha"] = _bar_line_alpha
        # No view here: clean_source already holds only the selected rows.
        r = fig.vbar(**_vbar_kwargs)
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
                r.glyph.line_color = c
            except ValueError:
                # _apply_line_opts names color() too, when it folds it onto
                # lcolor() -- which it does not when blcolor() is given, so
                # the note is raised here; once per render either way.
                _dash_style_note("color", options["color"], "colour")
        # bfcolor / blcolor — bar-specific fill / line color overrides.
        # An unknown name is noted, as every other colour option's is.
        if "bfcolor" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["bfcolor"])
            except ValueError:
                _dash_style_note("bfcolor", options["bfcolor"], "colour")
        if "blcolor" in options:
            try:
                r.glyph.line_color = self.tr.translate_mcolor(options["blcolor"])
            except ValueError:
                _dash_style_note("blcolor", options["blcolor"], "colour")
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
        # Masked by the layer's own view BEFORE the source is rebuilt.
        # The view's BooleanFilter is sized to the CALLER's source; the
        # source built below is shorter once rows with missing values are
        # dropped, and Bokeh applies a mask by position -- so attaching the
        # view to the rebuilt source selected the wrong observations.
        x_arr, y_arr = self._masked(source, view, xvar, yvar)
        # base() option sets the spike origin; default 0
        base_val = 0.0
        if "base" in options:
            try:
                base_val = float(options["base"])
            except (ValueError, TypeError):
                pass
        y0_base = np.full_like(x_arr, base_val)

        # The same rows _masked() kept, as positions, so the caller's other
        # columns -- an mlabel, a variable hover() names -- can ride along.
        _spike_sel = self._masked_index(source, view, xvar, yvar)
        seg_source = ColumnDataSource(self._carry_cols(source, {
            "x0": x_arr, "y0": y0_base,
            "x1": x_arr, "y1": y_arr,
        }, _spike_sel))
        _seg_kwargs: dict = dict(x0="x0", y0="y0", x1="x1", y1="y1",
                                  source=seg_source,
                                  line_color=self.scheme.default_color(color_idx, "spike"),
                                  line_width=self.scheme.default_line_width,
                                  legend_label=yvar)
        # No view here: seg_source already holds only the selected rows.
        r = fig.segment(**_seg_kwargs)
        self._apply_line_opts(r, options)
        self._apply_mlabel_opts(fig, source, options, xvar, yvar)
        return r

    # ------------------------------------------------------------------
    # Phase 1B plot types — computed glyphs
    # ------------------------------------------------------------------

    @staticmethod
    def _view_mask(view, n: int) -> "np.ndarray | None":
        """The boolean row mask *view* selects, or ``None`` for "all rows".

        A plain glyph layer can be handed a ``CDSView`` and let Bokeh do the
        filtering.  A computed layer cannot: it builds its own
        ``ColumnDataSource`` from a grid it calculates, so by the time there
        is a renderer to attach a view to, the statistic has already been
        computed from the wrong rows.  Those mappers ask for the mask instead
        and apply it to their input.

        Args:
            view: A ``CDSView``, or ``None``.
            n:    Number of rows in the source the mask must align with.

        Returns:
            A boolean array of length *n*, or ``None`` when there is nothing
            to filter or the view cannot be read.  ``None`` means "use every
            row", which is the behaviour of a layer with no qualifier.
        """
        if view is None:
            return None
        flt = getattr(view, "filter", None)
        if flt is None:
            return None

        booleans = getattr(flt, "booleans", None)
        if booleans is not None:
            mask = np.asarray(booleans, dtype=bool)
        else:
            indices = getattr(flt, "indices", None)
            if indices is None:
                # A filter type this does not understand -- an intersection,
                # a group filter, a custom one.  Drawing every row is wrong
                # but visible; guessing at the filter's meaning is wrong and
                # silent.
                return None
            mask = np.zeros(n, dtype=bool)
            keep = np.asarray(list(indices), dtype=int)
            keep = keep[(keep >= 0) & (keep < n)]
            mask[keep] = True
            return mask

        if mask.size != n:
            # Never apply a mask that does not line up: a shorter one would
            # silently drop the tail of the data and a longer one would
            # raise.  Every mask dash builds is sized from the source's own
            # __dash_row__ column, so this means something else produced it.
            warnings.warn(
                f"dash: a layer's row filter has {mask.size} entries but its "
                f"data has {n} rows, so the filter does not match and was "
                f"ignored; the layer is computed from every row.",
                stacklevel=2,
            )
            return None
        return mask

    @staticmethod
    def _masked(source: ColumnDataSource, view, *varnames: str) -> tuple:
        """Float arrays for *varnames*, restricted to the rows *view* selects.

        Rows where any of the named columns is NaN are dropped together, so
        the returned arrays stay aligned with each other -- the pairing every
        caller relied on when it did this inline.

        Returns:
            One float array per name in *varnames*, in order.
        """
        cols = [np.asarray(source.data[v], dtype=float) for v in varnames]
        n = len(cols[0]) if cols else 0

        sel = GlyphMapper._view_mask(view, n)
        if sel is not None:
            cols = [c[sel] for c in cols]

        finite = ~np.isnan(cols[0])
        for c in cols[1:]:
            finite &= ~np.isnan(c)
        return tuple(c[finite] for c in cols)

    @staticmethod
    def _masked_index(source: ColumnDataSource, view, *varnames: str):
        """Row indices selecting exactly the rows ``_masked`` keeps.

        Positions into ``source.data``, in the original order.  Indices
        rather than arrays, so a caller can carry a NON-NUMERIC column --
        an mlabel, or a variable ``hover()`` names -- through the same
        selection; ``_masked`` coerces everything to float and cannot.
        """
        cols = [np.asarray(source.data[v], dtype=float) for v in varnames]
        n = len(cols[0]) if cols else 0
        idx = np.arange(n)

        sel = GlyphMapper._view_mask(view, n)
        if sel is not None:
            cols = [c[sel] for c in cols]
            idx = idx[sel]

        if cols:
            finite = ~np.isnan(cols[0])
            for c in cols[1:]:
                finite &= ~np.isnan(c)
            idx = idx[finite]
        return idx

    @staticmethod
    def _masked_order(source: ColumnDataSource, view, xvar: str, *others: str):
        """Row indices selecting the drawn rows, in x order.

        ``_masked_index`` sorted by *xvar*.
        """
        idx = GlyphMapper._masked_index(source, view, xvar, *others)
        if len(idx):
            xs = np.asarray(source.data[xvar], dtype=float)[idx]
            idx = idx[np.argsort(xs, kind="stable")]
        return idx

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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        # Need at least 2 points to fit a line
        if len(x) < 2:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
        # _fit_grid is Stata's rule -- n() points, 100 by default, over the
        # OBSERVED range.  This used to be 200 points over a range padded
        # 10% at each end, so lfit and lfitci drew the same fit at different
        # x values and lfit put fitted values on screen at an x no
        # observation reaches, which twoway does not do.
        x_fit = _fit_grid(x, options)
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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        # Need at least 3 points for a degree-2 polyfit
        if len(x) < 3:
            empty = ColumnDataSource({"x": [], "y": []})
            return fig.line(x="x", y="y", source=empty)

        coeffs = np.polyfit(x, y, 2)
        # Stata's grid, as map_lfit uses -- see the note there.
        x_fit = _fit_grid(x, options)
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

        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)
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
                source=empty_ci_src, fill_alpha=_CI_BAND_ALPHA, fill_color=_lfitci_color
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
        _lvl = _resolve_level(options, self.default_level)
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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        # Need at least 3 points for a degree-2 polyfit
        _qfitci_color = self.scheme.default_color(color_idx, "line")
        if len(x) < 3:
            empty_ci_src = ColumnDataSource({
                "x_fit": [], "y_fit": [], "y_lower": [], "y_upper": []
            })
            band_r = fig.varea(
                x="x_fit", y1="y_lower", y2="y_upper",
                source=empty_ci_src, fill_alpha=_CI_BAND_ALPHA, fill_color=_qfitci_color
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
        _lvl = _resolve_level(options, self.default_level)
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

        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        # Need statsmodels, at least 2 points, and x must vary
        if lowess is None or len(x) < 2 or np.std(x) == 0.0:
            empty = ColumnDataSource({"x_lw": [], "y_lw": []})
            _r_empty = fig.line(x="x_lw", y="y_lw", source=empty)
            # An empty layer is still the user's layer: apply the line
            # options so lwidth/lcolor/lpattern survive a bail-out.
            # statsmodels is OPTIONAL, so on a machine without it EVERY
            # lowess layer takes this path.
            self._apply_line_opts(_r_empty, options)
            return _r_empty

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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        _lpolyci_color = self.scheme.default_color(color_idx, "line")
        empty_src = ColumnDataSource({
            "x_lp": [], "y_lp": [], "y_lower": [], "y_upper": []
        })
        if len(x) < 3:
            band_r = fig.varea(
                x="x_lp", y1="y_lower", y2="y_upper",
                source=empty_src, fill_alpha=_CI_BAND_ALPHA, fill_color=_lpolyci_color,
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
            level=_resolve_level(options, self.default_level),
            seed=_resolve_seed(options),
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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        if len(x) < 4:
            empty = ColumnDataSource({"x_fp": [], "y_fp": []})
            r = fig.line(x="x_fp", y="y_fp", source=empty)
            # An empty layer is still the user's layer: style it so
            # lwidth/lcolor/lpattern survive the bail-out.
            self._apply_line_opts(r, options)
            return r

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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x, y = self._masked(source, view, xvar, yvar)

        _fpfitci_color = self.scheme.default_color(color_idx, "line")
        empty_src = ColumnDataSource({
            "x_fp": [], "y_fp": [], "y_lower": [], "y_upper": []
        })
        if len(x) < 4:
            band_r = fig.varea(
                x="x_fp", y1="y_lower", y2="y_upper",
                source=empty_src, fill_alpha=_CI_BAND_ALPHA, fill_color=_fpfitci_color,
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
            level=_resolve_level(options, self.default_level),
            seed=_resolve_seed(options),
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
        arr = _extract_finite(source, yvar, view=view)

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
                     fill_alpha=self._scheme_alpha(
                         color_idx, "histogram", self.scheme.bar_alpha),
                     legend_label=yvar)
        if "color" in options:
            try:
                c = self.tr.translate_mcolor(options["color"])
                r.glyph.fill_color = c
            except ValueError:
                # As map_bar: named here because the lcolor() fold that
                # would name it is skipped when blcolor() is given.
                _dash_style_note("color", options["color"], "colour")
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
            # A denormal width -- width(1e-310) -- makes span/width overflow
            # to inf, and math.ceil(inf) raises OverflowError, which took the
            # whole dashboard down rather than this one histogram.
            _ratio = span / width if width else float("inf")
            if not math.isfinite(_ratio) or _ratio > _MAX_BINS:
                warnings.warn(
                    f"dash: histogram option width({options.get('width')}) "
                    f"would need more than {_MAX_BINS} bins; deriving the "
                    f"width from the data instead.",
                    UserWarning, stacklevel=2,
                )
                width = None
                n_bins = _stata_bin_count(n)
            else:
                n_bins = int(math.ceil(_ratio))
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

        return edges, _dash_histogram_ymode(options)

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
        arr = _extract_finite(source, yvar, view=view)

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
        # Stata's kdensity takes range(# #), the span the density is
        # estimated over. dash read range() in the `function' branch and
        # nowhere else, so `kdensity mpg, range(10 30)' estimated over the
        # default span and said nothing about it.
        _lo, _hi = arr.min() - 3 * bw, arr.max() + 3 * bw
        _rng_raw = str(options.get("range", "") or "").strip()
        if _rng_raw:
            _parts = _rng_raw.split()
            _ok = False
            if len(_parts) == 2:
                try:
                    _a, _b = float(_parts[0]), float(_parts[1])
                    if np.isfinite(_a) and np.isfinite(_b) and _a < _b:
                        _lo, _hi, _ok = _a, _b, True
                except (TypeError, ValueError):
                    pass
            if not _ok:
                warnings.warn(
                    f"dash: kdensity range({_rng_raw}) is not a low-then-high "
                    f"pair of numbers; estimating over the default span.",
                    UserWarning, stacklevel=2,
                )
        x_range = np.linspace(_lo, _hi,
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

        # Sorted for the same reason as map_rline above: a varea joined in
        # dataset order is a band with no relation to the data.  Masked and
        # rebuilt rather than sorted in place, because the source is shared.
        _ord = self._masked_order(source, view, xvar, y1var, y2var)
        _cols = {
            v: np.asarray(source.data[v], dtype=float)[_ord]
            for v in (xvar, y1var, y2var)
        }
        for _extra in (_dash_mlabel_names(options)[0],):
            if _extra and _extra in source.data and _extra not in _cols:
                _cols[_extra] = [source.data[_extra][_i] for _i in _ord]
        source = ColumnDataSource(_cols)
        view = None

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
        # The width is DERIVED from the data, so it must come from the rows
        # this layer draws.  The source below keeps every row -- so the
        # caller's mask lines up with it and the view is attached as usual --
        # but the spacing was taken from the whole column, and a qualifier
        # then changed how WIDE the bars were as well as which appeared.
        # Measured: 0.8 where plotting the same subset alone gives 8.0.
        _rb_x = np.asarray(source.data[xvar], dtype=float)
        _rb_sel = self._view_mask(view, len(_rb_x))
        if _rb_sel is not None:
            _rb_x = _rb_x[_rb_sel]
        x_vals = sorted(set(float(v) for v in _rb_x if not math.isnan(v)))
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

        # bfcolor / blcolor -- the bar-specific fill and line overrides, and
        # then the generic appliers, exactly as map_bar does.  map_rbar had
        # only _apply_fill_opts, so a range bar ignored lwidth(), lcolor(),
        # bfcolor() and blcolor() entirely: measured, bfcolor(red),
        # blcolor(navy) and lwidth(thick) each left the glyph at the scheme
        # defaults.  The generated server app read all four in its own
        # branch, which is how test_server.py's rbar cases caught it the
        # moment rbar started going through the mapper.
        if "bfcolor" in options:
            try:
                r.glyph.fill_color = self.tr.translate_mcolor(options["bfcolor"])
            except ValueError:
                _dash_style_note("bfcolor", options["bfcolor"], "colour")
            except AttributeError:
                pass
        if "blcolor" in options:
            try:
                r.glyph.line_color = self.tr.translate_mcolor(options["blcolor"])
            except ValueError:
                _dash_style_note("blcolor", options["blcolor"], "colour")
            except AttributeError:
                pass
        self._apply_fill_opts(r, options)
        # After bfcolor/blcolor, so blcolor keeps priority for the line.
        self._apply_line_opts(r, options)
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
                                   line_color=self.scheme.default_color(color_idx, "rspike"),
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

        # The width is DERIVED from the data, so it must come from the rows
        # this layer draws.  The source below keeps every row -- so the
        # caller's mask lines up with it and the view is attached as usual --
        # but the spacing was taken from the whole column, and a qualifier
        # then changed how WIDE the bars were as well as which appeared.
        # Measured: 0.8 where plotting the same subset alone gives 8.0.
        # Estimate cap half-width from x spacing
        _cap_x = x_arr
        _cap_sel = self._view_mask(view, len(_cap_x))
        if _cap_sel is not None:
            _cap_x = _cap_x[_cap_sel]
        x_sorted = np.sort(_cap_x[~np.isnan(_cap_x)])
        if len(x_sorted) >= 2:
            cap_hw = 0.2 * np.min(np.diff(x_sorted))
        else:
            cap_hw = 0.2

        _x0_col = f"{xvar}_x0_cap"
        _x1_col = f"{xvar}_x1_cap"
        # The caller's other columns ride along -- the marker-label column,
        # and any variable hover() names.  The source keeps every row here
        # (see above), so they are carried whole.
        cap_source = ColumnDataSource(self._carry_cols(source, {
            xvar: x_arr, y1var: y1_arr, y2var: y2_arr,
            _x0_col: x_arr - cap_hw, _x1_col: x_arr + cap_hw,
        }))

        _rcap_color = self.scheme.default_color(color_idx, "rcap")
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
        # Bokeh joins a line's points in the order it is given them and
        # Stata's twoway rline draws along x, so unsorted rows make both
        # boundaries cross themselves.  The rows cannot be sorted in the
        # SHARED source -- other layers draw from it, and a view over it is
        # an IndexFilter in the original row order -- so the mask is applied
        # here and a sorted source built from the result, exactly as
        # map_area does.  That is also why no view is passed on below: these
        # rows are already the selected ones.
        _ord = self._masked_order(source, view, xvar, y1var, y2var)
        _cols = {
            v: np.asarray(source.data[v], dtype=float)[_ord]
            for v in (xvar, y1var, y2var)
        }
        # Any other column the layer needs -- an mlabel is not numeric, so it
        # rides the same row order rather than going through _masked.
        for _extra in (_dash_mlabel_names(options)[0],):
            if _extra and _extra in source.data and _extra not in _cols:
                _cols[_extra] = [source.data[_extra][_i] for _i in _ord]
        source = ColumnDataSource(_cols)
        view = None

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

        # Apply jitter if requested (jitters x and y).  Read through
        # _stat_option_float: a bare float() here raised out of the mapper
        # on jitter(abc) and took the whole render down.
        _jit = _stat_option_float(options, "jitter", 0.0, "dropline",
                                  lo=0.0, hi=100.0)
        if _jit:
            x_plot, y_plot = _apply_jitter(x_arr, y_arr, _jit,
                                           _jitter_seed(options))
        else:
            x_plot, y_plot = x_arr, y_arr

        _dl_cols: dict = {
            "x": x_plot, "y": y_plot, "y0": zeros,
            xvar: x_arr, yvar: y_arr,
        }
        # _apply_mlabel_opts reads the label column out of THIS source, and
        # the figure's hover tool reads the variables hover() names out of
        # it too, so a source carrying only the two plot variables meant
        # mlabel() drew nothing on a dropline -- which dash.sthlp lists as
        # taking it -- and hover() was dropped.
        dl_source = ColumnDataSource(
            self._carry_cols(source, _dl_cols, mask))
        # Two defaults: the drop is a spike and takes `color p#'; the dot
        # is a marker and takes `color p#mark'.  Both asked for "scatter"
        # once, so a user scheme declaring p1mark recoloured the line.
        seg_color = self.scheme.default_color(color_idx, "spike")
        dot_color = self.scheme.default_color(color_idx, "dropline")
        try:
            if "mcolor" in options:
                seg_color = dot_color = self.tr.translate_mcolor(
                    options["mcolor"])
            elif "color" in options:
                seg_color = dot_color = self.tr.translate_mcolor(
                    options["color"])
        except ValueError:
            pass

        _dl_seg_kwargs: dict = dict(
            x0="x", y0="y0", x1="x", y1="y", source=dl_source,
            line_color=seg_color, line_width=self.scheme.default_line_width)
        _dl_dot_kwargs: dict = dict(
            x="x", y="y", source=dl_source,
            fill_color=dot_color, line_color=dot_color,
            size=self.scheme.default_marker_size(color_idx),
            legend_label=yvar)
        if view is not None:
            _dl_seg_kwargs["view"] = view
            _dl_dot_kwargs["view"] = view
        seg = fig.segment(**_dl_seg_kwargs)
        dot = fig.scatter(**_dl_dot_kwargs)
        self._apply_line_opts(seg, options)
        # msymbol(), msize(), msangle() and malpha() are read here and
        # nowhere else, and the dot was never passed through -- so a dropline
        # drew a default circle whatever was asked for.
        self._apply_marker_opts(dot, options)
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

        # The width is DERIVED from the data, so it must come from the rows
        # this layer draws.  The source below keeps every row -- so the
        # caller's mask lines up with it and the view is attached as usual --
        # but the spacing was taken from the whole column, and a qualifier
        # then changed how WIDE the bars were as well as which appeared.
        # Measured: 0.8 where plotting the same subset alone gives 8.0.
        _cap_x = x_arr
        _cap_sel = self._view_mask(view, len(_cap_x))
        if _cap_sel is not None:
            _cap_x = _cap_x[_cap_sel]
        x_sorted = np.sort(_cap_x[~np.isnan(_cap_x)])
        if len(x_sorted) >= 2:
            cap_hw = 0.2 * float(np.min(np.diff(x_sorted)))
        else:
            cap_hw = 0.2

        cap_source = ColumnDataSource({
            "x": x_arr, "y1": y1_arr, "y2": y2_arr,
            "x0_cap": x_arr - cap_hw, "x1_cap": x_arr + cap_hw,
        })

        # Two defaults: the spine and caps are an rcap and take `color
        # p#'; the symbols are markers and take `color p#mark'.
        color = self.scheme.default_color(color_idx, "rcap")
        mark_color = self.scheme.default_color(color_idx, "rscatter")
        try:
            if "mcolor" in options:
                color = mark_color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = mark_color = self.tr.translate_mcolor(options["color"])
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
                                    fill_color=mark_color, line_color=mark_color, size=7)
        _rcs_tdot_kw: dict  = dict(x="x", y="y2", source=cap_source,
                                    fill_color=mark_color, line_color=mark_color, size=7)
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

        # Apply jitter if requested -- through the reader every jitter()
        # goes through, so a word is named rather than dropped.
        if str(options.get("jitter", "") or "").strip():
            jitter_pct = _stat_option_float(options, "jitter", 0.0,
                                            "scatteri", lo=0.0)
            if jitter_pct is not None and jitter_pct > 0:
                x_vals, y_vals = _apply_jitter(
                    x_vals, y_vals, min(100.0, jitter_pct),
                    _jitter_seed(options))

        si_source = ColumnDataSource({"x": x_vals.tolist(), "y": y_vals.tolist()})

        color = self.scheme.default_color(color_idx, "scatter")
        try:
            if "mcolor" in options:
                color = self.tr.translate_mcolor(options["mcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass

        # The scheme's marker size, not a literal "medium": every other
        # marker-drawing mapper takes its default from the scheme, and
        # scatteri taking "medium" made it 11px under s2color where a
        # scatter beside it is 8.
        #
        # A bad msize()/msymbol() used to raise out of here and abort the
        # whole render -- the one place a style name was fatal.  The
        # default is taken silently: _apply_marker_opts re-reads both
        # options below and raises the one note, as map_scatter's does.
        size = self.scheme.default_marker_size(color_idx)
        if str(options.get("msize", "")).strip():
            try:
                size = self.tr.translate_msize(options["msize"])
            except ValueError:
                pass
        marker = "circle"
        if str(options.get("msymbol", "")).strip():
            try:
                marker = self.tr.translate_msymbol(options["msymbol"])
            except ValueError:
                pass

        r = fig.scatter(x="x", y="y", source=si_source,
                        marker=marker, size=size,
                        fill_color=color, line_color=color)
        # mcolor(), msize() and msymbol() are resolved above; msangle() and
        # malpha() are read only here, and dash.sthlp lists scatteri as
        # taking msangle().
        self._apply_marker_opts(r, options)
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
        # Masked by the layer's own view BEFORE the rows are dropped.  The
        # view's BooleanFilter is sized to the CALLER's source; the source
        # built below is shorter once rows with missing values go, and Bokeh
        # applies a mask by position -- so attaching the view to the rebuilt
        # source selected the wrong observations.
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        })
        _pc_sel = self._view_mask(view, len(clean))
        if _pc_sel is not None:
            clean = clean[_pc_sel]
        clean = clean.dropna()
        source_clean = ColumnDataSource(clean)
        _pcseg_kwargs: dict = dict(x0=x1var, y0=y1var, x1=x2var, y1=y2var,
                                    source=source_clean,
                                    line_color=self.scheme.default_color(color_idx, "pcspike"),
                                    line_width=1.5,
                                    legend_label=y1var)
        # No view here: source_clean already holds only the selected rows.
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

    def map_pci_literal(
        self,
        fig: Any,
        values: list,
        options: "dict[str, str]",
        color_idx: int = 0,
    ) -> list:
        """Draw ``twoway pci``'s literal coordinate pairs as segments.

        ``pci 20 3000 30 4000`` names two points -- ``(y=20, x=3000)`` and
        ``(y=30, x=4000)`` -- and draws a line between them.  More points
        draw more segments, two at a time.  dash.ado writes the list as
        ``[[20,3000],[30,4000]]``, in ``(y, x)`` order, the same order
        ``scatteri`` uses.

        Args:
            fig:       Bokeh Figure object.
            values:    List of ``[y, x]`` pairs from the spec.
            options:   Translated plot-level options dict.
            color_idx: Zero-based plot index, for the scheme's colour cycle.

        Returns:
            List with the single Segment GlyphRenderer.
        """
        pts: "list[tuple[float, float]]" = []
        for pair in values or []:
            try:
                pts.append((float(pair[0]), float(pair[1])))
            except (TypeError, ValueError, IndexError) as exc:
                raise ValueError(
                    "dash: pci coordinates must be numeric y x pairs; got "
                    f"{values!r} ({exc})."
                ) from exc

        if len(pts) % 2:
            warnings.warn(
                f"dash: pci was given {len(pts)} coordinate pairs; they are "
                f"drawn two at a time, so the last one is not drawn.",
                UserWarning, stacklevel=2,
            )

        y0s = [pts[i][0] for i in range(0, len(pts) - 1, 2)]
        x0s = [pts[i][1] for i in range(0, len(pts) - 1, 2)]
        y1s = [pts[i + 1][0] for i in range(0, len(pts) - 1, 2)]
        x1s = [pts[i + 1][1] for i in range(0, len(pts) - 1, 2)]

        src = ColumnDataSource({"x0": x0s, "y0": y0s, "x1": x1s, "y1": y1s})
        color = self.scheme.default_color(color_idx, "line")
        try:
            if "lcolor" in options:
                color = self.tr.translate_mcolor(options["lcolor"])
            elif "color" in options:
                color = self.tr.translate_mcolor(options["color"])
        except ValueError:
            pass
        r = fig.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=src,
                        line_color=color,
                        line_width=self.scheme.default_line_width)
        self._apply_line_opts(r, options)
        return [r]

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
        # Masked by the layer's own view BEFORE the rows are dropped.  The
        # view's BooleanFilter is sized to the CALLER's source; the source
        # built below is shorter once rows with missing values go, and Bokeh
        # applies a mask by position -- so attaching the view to the rebuilt
        # source selected the wrong observations.
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        })
        _pc_sel = self._view_mask(view, len(clean))
        if _pc_sel is not None:
            clean = clean[_pc_sel]
        clean = clean.dropna()

        # Concatenate both endpoint sets into one scatter source
        x_all = np.concatenate([clean[x1var].values, clean[x2var].values])
        y_all = np.concatenate([clean[y1var].values, clean[y2var].values])
        pc_source = ColumnDataSource({"x": x_all.tolist(), "y": y_all.tolist()})

        _pcsc_kwargs: dict = dict(source=pc_source,
                                   size=self.scheme.default_marker_size(color_idx),
                                   color=self.scheme.default_color(color_idx, "scatter"),
                                   legend_label=y1var)
        # No view here: pc_source already holds only the selected rows.
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
        # Masked by the layer's own view BEFORE the rows are dropped.  The
        # view's BooleanFilter is sized to the CALLER's source; the source
        # built below is shorter once rows with missing values go, and Bokeh
        # applies a mask by position -- so attaching the view to the rebuilt
        # source selected the wrong observations.
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        })
        _pc_sel = self._view_mask(view, len(clean))
        if _pc_sel is not None:
            clean = clean[_pc_sel]
        clean = clean.dropna()
        pc_source = ColumnDataSource(clean)

        color = self.scheme.default_color(color_idx, "pcarrow")
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
        # No view here: pc_source already holds only the selected rows.
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
        # Masked by the layer's own view BEFORE the rows are dropped.  The
        # view's BooleanFilter is sized to the CALLER's source; the source
        # built below is shorter once rows with missing values go, and Bokeh
        # applies a mask by position -- so attaching the view to the rebuilt
        # source selected the wrong observations.
        clean = pd.DataFrame({
            y1var: source.data[y1var],
            x1var: source.data[x1var],
            y2var: source.data[y2var],
            x2var: source.data[x2var],
        })
        _pc_sel = self._view_mask(view, len(clean))
        if _pc_sel is not None:
            clean = clean[_pc_sel]
        clean = clean.dropna()
        pc_source = ColumnDataSource(clean)

        color = self.scheme.default_color(color_idx, "pcbarrow")
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
        # No view here: pc_source already holds only the selected rows.
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

        # Masked by the layer's own view BEFORE stacking.  The source built
        # below holds TWO entries per observation, so the caller's row mask
        # cannot be attached to it -- Bokeh applies a mask by position and it
        # would land on the wrong half.  _masked() is deliberately not used:
        # it drops a row when ANY named column is NaN, which would discard
        # the y2 point of an observation whose y1 alone is missing.  The
        # per-entry test below keeps that point, as it always has.
        _rs_sel = self._view_mask(view, len(x_arr))
        if _rs_sel is not None:
            x_arr = x_arr[_rs_sel]
            y1_arr = y1_arr[_rs_sel]
            y2_arr = y2_arr[_rs_sel]

        # Interleave both y-boundary points at the same x
        x_all = np.concatenate([x_arr, x_arr])
        y_all = np.concatenate([y1_arr, y2_arr])
        mask = ~(np.isnan(x_all) | np.isnan(y_all))

        rs_source = ColumnDataSource({
            "x": x_all[mask].tolist(),
            "y": y_all[mask].tolist(),
        })
        _rs_kwargs: dict = dict(source=rs_source,
                                 size=self.scheme.default_marker_size(color_idx),
                                 color=self.scheme.default_color(color_idx, "scatter"),
                                 legend_label=y1var)
        # No view here: rs_source already holds only the selected rows.
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

        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x_clean, y_clean = self._masked(source, view, xvar, yvar)

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
            # An empty layer is still the user's layer: style it so
            # lwidth/lcolor/lpattern survive the bail-out.
            self._apply_line_opts(r, options)
            return [r]

        interp = PchipInterpolator(x_clean, y_clean)
        x_grid = np.linspace(x_clean.min(), x_clean.max(), 200)
        y_grid = interp(x_grid)

        ms_source = ColumnDataSource({"x_sp": x_grid, "y_sp": y_grid})
        r = fig.line(x="x_sp", y="y_sp", source=ms_source,
                     line_color=self.scheme.default_color(color_idx, "line"),
                     line_width=self.scheme.default_line_width,
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
        # Masked by the layer's own view: a per-plot `if', a by()
        # facet panel or a linked graph's qualifier.  Reading the
        # whole source here computed the statistic from rows the user
        # had excluded, and said nothing.
        x_clean, y_clean = self._masked(source, view, xvar, yvar)

        empty = ColumnDataSource({"x_mb": [], "y_mb": []})

        if len(x_clean) < 4:
            r = fig.line(x="x_mb", y="y_mb", source=empty)
            # An empty layer is still the user's layer: style it so
            # lwidth/lcolor/lpattern survive the bail-out.
            self._apply_line_opts(r, options)
            return [r]

        # hi= matches the clamp the generated server app applies, so the two
        # modes draw the same number of bands.  Without it, bands(1e9)
        # allocated 8 GB in np.linspace before any drawing happened.
        requested = _stat_option_float(options, "bands", None, "mband",
                                       lo=1.0, hi=float(_MAX_MBANDS))
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
                     line_width=self.scheme.default_line_width,
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

        if len(expr) > _MAX_EXPR_CHARS:
            warnings.warn(
                f"dash: function expression is {len(expr)} characters, over "
                f"the {_MAX_EXPR_CHARS} limit; the layer is drawn empty. "
                f"Validating it is recursive, one frame per term, so a long "
                f"expression exhausts the stack.",
                UserWarning, stacklevel=2,
            )
            return [fig.line(x="x_fn", y="y_fn", source=empty_source,
                             line_color=self.scheme.default_color(0, "line"),
                             line_width=self.scheme.default_line_width)]

        try:
            tree = _ast.parse(expr, mode="eval")
            _validate_expr_node(tree)
            tree = _floats_only(tree)
            code = compile(tree, "<function>", "eval")
        # RecursionError is neither a SyntaxError nor a ValueError, so a deep
        # expression escaped this guard and took the whole dashboard with it.
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            return [fig.line(x="x_fn", y="y_fn", source=empty_source,
                             line_color=self.scheme.default_color(0, "line"),
                             line_width=self.scheme.default_line_width)]

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
                             line_color=self.scheme.default_color(0, "line"),
                             line_width=self.scheme.default_line_width)]

        fn_source = ColumnDataSource({"x_fn": x_arr, "y_fn": y_arr})
        r = fig.line(x="x_fn", y="y_fn", source=fn_source,
                     line_color=self.scheme.default_color(0, "line"),
                     line_width=self.scheme.default_line_width,
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

    The seed option seeds jitter and, here, the bootstrap confidence bands,
    so a user who needs a different resample draw can ask for one instead of
    always getting seed 42. Stata spells it ``jitterseed()`` and dash also
    accepts ``jseed()``; :func:`_jitter_seed` reads both.
    """
    seed = _jitter_seed(options)
    return default if seed is None else seed


#: The notes already raised this render, keyed ``(option, value, what)``.
#: One bad option is read by more than one site -- ``connected``'s
#: lcolor() by the line and by the marker border, ``rcapsym``'s mcolor()
#: by two dot renderers, everything by every by() panel -- and each said
#: so again: four lines for one mistake, where twoway prints its note
#: once.  Module state, cleared by ``_dash_reset_notes`` at the start of
#: every render in both modes.  The generated app gets its own
#: ``_DASH_NOTED = set()`` written out beside these helpers.
_DASH_NOTED: set = set()


def _dash_reset_notes():
    """Forget the notes of the previous render.

    Called at the top of ``DashRenderer.render()`` and of the served app's
    ``make_document``.  ``clear()``, not a rebinding, so the copy of this
    function in the generated app works on that module's own set.
    """
    _DASH_NOTED.clear()


def _dash_warn_once(key, message, stacklevel=4):
    """``warnings.warn(message)`` unless *key* was already raised this render."""
    if key in _DASH_NOTED:
        return
    _DASH_NOTED.add(key)
    warnings.warn(message, UserWarning, stacklevel=stacklevel)


def _dash_style_note(option, value, what, using="the scheme's default",
                     prefix="dash"):
    """Report a style name dash does not recognise, before the default is used.

    twoway never rejects a bad style name: ``mcolor(notacolour)`` draws with
    ``(note: named style notacolour not found in class color, default
    attributes used)``.  dash does the same, in one wording, from one place,
    once per render.  Before this helper existed the same mistake was
    silently dropped in the option appliers, worded three different ways
    in three others, and an abort of the whole render in ``map_scatteri``.

    Copied into the served app by name beside ``_stat_option_float``, so
    ``GlyphMapper`` and ``OptionTranslator`` -- which the app copies by
    source -- find it there too.

    Args:
        option: The option as the user wrote it (``mcolor``, ``msize``).  A
                sub-option is written as ``plotregion(lcolor)`` and shown
                nested, ``plotregion(lcolor(x))``, as the user typed it.
        value:  Its value, echoed through ``_dash_display`` (printable
                characters only, 80 at most): colour and symbol names are
                not gated by dash.ado, so this may be anything.
        what:   colour / marker symbol / size / line width / line pattern /
                angle / clock position / fill intensity.
        using:  What is drawn instead.
        prefix: ``dash``, or ``dash kpi`` for a KPI's colour.
    """
    shown = _dash_display(value)
    head = (f"{option[:-1]}({shown}))" if option.endswith(")")
            else f"{option}({shown})")
    _dash_warn_once(
        (prefix, option, str(value), what),
        f"{prefix}: {head} is not a recognised {what}; using {using}.",
    )


def _dash_graph_color(option, raw):
    """A graph-level colour as CSS, or ``""`` with a note.

    bgcolor(), plotbgcolor(), plotregion(color()/lcolor()) and
    graphregion(color()) were each an ``except ...: pass`` in the saved
    figure body, and the served app's own resolver returned ``""`` without
    a word, so an unknown colour name at graph level was silent in both
    modes.  One reader for both, through the same translator the plot
    options use, so the two modes accept exactly the same spellings.

    Args:
        option: As written, e.g. ``plotregion(lcolor)``.
        raw:    The colour text.
    """
    try:
        return OptionTranslator.translate_mcolor(raw)
    except (ValueError, TypeError):
        _dash_style_note(option, raw, "colour")
        return ""


def _dash_figure_aspect(graph_opts, scheme_x=None, scheme_y=None):
    """Bokeh's width/height ratio from xsize()/ysize(), else aspectratio().

    Stata's ``aspectratio()`` is height/width and Bokeh's ``aspect_ratio`` is
    width/height, so the value is inverted; the served figure used to pass
    it straight through.  Either of xsize()/ysize() alone keeps the
    scheme's value for the other, exactly as Stata does: xsize(9) under
    stcolor gives 4.5 x 9.  All three are read through ``_stat_option_float``
    so a word or a negative number is named once, in one wording, in both
    modes -- the saved renderer used to name a bad aspectratio() twice and
    the served app not at all.

    Returns:
        The ratio, or None when neither option is usable; the caller may
        then fall back on the scheme's own proportions.
    """
    xs = _stat_option_float(graph_opts, "xsize", None, "graph", lo=0.0)
    ys = _stat_option_float(graph_opts, "ysize", None, "graph", lo=0.0)
    for name, val in (("xsize", xs), ("ysize", ys)):
        if val is not None and val <= 0:
            # Stata returns r(198) for xsize(0) and xsize(-3).
            warnings.warn(
                f"dash: {name}({_dash_display(graph_opts.get(name))}) must "
                f"be a positive number of inches; ignoring it.", UserWarning,
            )
            if name == "xsize":
                xs = None
            else:
                ys = None
    if xs is not None or ys is not None:
        w = xs if xs is not None else scheme_x
        h = ys if ys is not None else scheme_y
        if w and h:
            return float(w) / float(h)

    raw_ar = str(graph_opts.get("aspectratio", "") or "").strip()
    if raw_ar:
        ar = _stat_option_float(graph_opts, "aspectratio", None, "graph",
                                lo=0.0)
        if ar is not None and ar <= 0:
            warnings.warn(
                f"dash: aspectratio({_dash_display(raw_ar)}) must be a "
                f"positive number; ignoring it.", UserWarning,
            )
        elif ar is not None:
            return 1.0 / float(ar)
    return None


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


_LITERAL_MARK = "\x01"


def _mask_string_literals(expr: str) -> "tuple[str, list[str]]":
    """Replace every quoted literal with a placeholder the rewrites ignore.

    Returns ``(masked, literals)``.  The placeholder is ``\x01<i>\x01``:
    it carries no operator, no comma and no identifier, so none of the
    qualifier rewrites can match inside it, and ``inlist(x, <ph>, <ph>)``
    still splits on its commas exactly as before.

    An unterminated quote is masked to the end of the string.  Leaving it
    unmasked would mean the one case where the user most likely mistyped is
    also the one case the rewrites are free to alter.
    """
    out: "list[str]" = []
    lits: "list[str]" = []
    buf = ""
    quote = ""
    i = 0
    while i < len(expr):
        ch = expr[i]
        if quote:
            buf += ch
            if ch == "\\" and i + 1 < len(expr):
                buf += expr[i + 1]
                i += 2
                continue
            if ch == quote:
                out.append(f"{_LITERAL_MARK}{len(lits)}{_LITERAL_MARK}")
                lits.append(buf)
                buf = ""
                quote = ""
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf = ch
            i += 1
            continue
        out.append(ch)
        i += 1
    if buf:                                   # unterminated quote
        out.append(f"{_LITERAL_MARK}{len(lits)}{_LITERAL_MARK}")
        lits.append(buf)
    return "".join(out), lits


def _unmask_string_literals(expr: str, literals: "list[str]") -> str:
    """Put the literals masked by :func:`_mask_string_literals` back."""
    for i, lit in enumerate(literals):
        expr = expr.replace(f"{_LITERAL_MARK}{i}{_LITERAL_MARK}", lit)
    return expr


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

    Quoted string literals are masked out before any rewrite and restored
    afterwards, so a literal is data and not syntax.  Without that,

        if make == "Wow!"

    became ``make == "Wow~"``, matched no rows and drew an empty graph
    without a word -- the rewritten expression is still valid, so nothing
    reported that the qualifier had been altered.  Masking rather than
    splitting, because ``inlist(make, "AMC", "BMW")`` is a legitimate
    qualifier whose arguments ARE literals: the rewrites must still see the
    call, just not the contents of its strings.

    Args:
        expr: A Stata if-qualifier expression.

    Returns:
        An equivalent expression in pandas-query syntax.
    """
    if not expr:
        return expr
    out, _literals = _mask_string_literals(str(expr))

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
    return _unmask_string_literals(out, _literals)


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


def _dash_kpi_card_html(title, value, subtitle, color, bgcolor, name,
                        scheme):
    """One KPI card's markup, for the saved page, the served app and the
    JS rebuild alike.

    The card is Stata's legend box, so its background, border and text
    colour come from the scheme's ``color legend``, ``color legend_line``
    and ``color text`` -- as the ``.db-kpi-card`` rule of
    ``scheme.css_block()``, which the caller attaches to the Div as an
    InlineStyleSheet (a Bokeh 3 Div renders in a shadow root, so a page
    stylesheet never reaches it).  Only the layout is inline; the card
    used to carry ``background:#f8f9fa`` and ``border:1px solid #dee2e6``
    inline under every scheme, and no scheme rule could win against that.

    An explicit ``bgcolor()`` IS inline, so the option beats the scheme;
    the value's colour is ``color()`` when given, else ``color text``.

    Args:
        title, value, subtitle: Raw text; escaped here.
        color, bgcolor:         The KPI's ``color()`` / ``bgcolor()``, ''
                                when not given.
        name:                   The KPI's name, for the value div's id.
        scheme:                 The dashboard's SchemeParser, or None for
                                a spec-JSON caller with no scheme.

    Returns:
        The card's HTML.
    """
    text_color = _sanitize_css_color(
        getattr(scheme, "text_color", "") or "#000000", "#000000")
    # Sanitised, not merely escaped -- see _resolve_kpi_color.  These are
    # interpolated into a style attribute, where html.escape does not stop
    # a CSS property injection.
    _c = _resolve_kpi_color(color, text_color, "color")
    # No default: an absent (or refused) bgcolor() leaves the class rule
    # to colour the card.
    _bg = _resolve_kpi_color(bgcolor, "", "bgcolor")
    _t = html.escape(title or "")
    _s = html.escape(subtitle or "")
    _v = html.escape(str(value))
    _n = html.escape(name or "kpi")
    _bg_decl = f"background:{_bg}; " if _bg else ""
    return (
        f'<div class="db-kpi-card" style="{_bg_decl}border-radius:8px; '
        f'padding:20px; text-align:center; min-width:160px; '
        f'min-height:110px;">'
        f'<div style="font-size:13px; color:{text_color}; '
        f'margin-bottom:6px;">{_t}</div>'
        f'<div id="kpi_val_{_n}" style="font-size:36px; font-weight:bold; '
        f'color:{_c};">{_v}</div>'
        f'<div style="font-size:11px; color:{text_color}; '
        f'margin-top:4px;">{_s}</div>'
        f'</div>'
    )


def _resolve_kpi_color(val: str, default: str, option: str = "") -> str:
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
        option:  ``color`` or ``bgcolor``; when given, a name the translator
                 does not know is reported (``dash kpi: color(x) is not a
                 recognised colour; using the default.``) -- it used to fall
                 to the default without a word in both modes.

    Returns:
        A CSS colour that is safe to interpolate.
    """
    raw = (val or "").strip()
    if not raw:
        return default
    try:
        return _sanitize_css_color(OptionTranslator.translate_mcolor(raw),
                                   default)
    except (ValueError, TypeError):
        pass
    # Not a Stata colour.  A CSS one the browser can draw -- a name it
    # knows, or a hex or functional form the sanitiser accepts -- passes
    # through, as it always has.  The sanitiser's letters-only branch alone
    # let ANY word through, so an unknown name reached the stylesheet as an
    # invalid declaration the browser drops, and no note said so.
    safe = _sanitize_css_color(raw, "")
    if safe and (not raw.isalpha() or raw.lower() in _CSS_NAMED_COLORS):
        return safe
    if option:
        _dash_style_note(option, raw, "colour", "the default", "dash kpi")
    return default


#: The colour names CSS defines (Color Module Level 4's 148, plus the two
#: keywords), for _resolve_kpi_color: a KPI colour that is not a Stata name
#: is honoured when a browser can draw it and named otherwise.  A tuple, so
#: the generated app's copy is written in one order.
_CSS_NAMED_COLORS: tuple = (
    "aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige",
    "bisque", "black", "blanchedalmond", "blue", "blueviolet", "brown",
    "burlywood", "cadetblue", "chartreuse", "chocolate", "coral",
    "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan",
    "darkgoldenrod", "darkgray", "darkgreen", "darkgrey", "darkkhaki",
    "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred",
    "darksalmon", "darkseagreen", "darkslateblue", "darkslategray",
    "darkslategrey", "darkturquoise", "darkviolet", "deeppink",
    "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick",
    "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite",
    "gold", "goldenrod", "gray", "green", "greenyellow", "grey", "honeydew",
    "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender",
    "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral",
    "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgreen",
    "lightgrey", "lightpink", "lightsalmon", "lightseagreen", "lightskyblue",
    "lightslategray", "lightslategrey", "lightsteelblue", "lightyellow",
    "lime", "limegreen", "linen", "magenta", "maroon", "mediumaquamarine",
    "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen",
    "mediumslateblue", "mediumspringgreen", "mediumturquoise",
    "mediumvioletred", "midnightblue", "mintcream", "mistyrose", "moccasin",
    "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange",
    "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise",
    "palevioletred", "papayawhip", "peachpuff", "peru", "pink", "plum",
    "powderblue", "purple", "rebeccapurple", "red", "rosybrown", "royalblue",
    "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna",
    "silver", "skyblue", "slateblue", "slategray", "slategrey", "snow",
    "springgreen", "steelblue", "tan", "teal", "thistle", "tomato",
    "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow",
    "yellowgreen", "transparent", "currentcolor",
)


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
const orig        = orig_source.data;
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
const _srcs_orig = all_graph_sources_orig;
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
    // This source's own snapshot — preserves its unique column set.
    const _orig_i = _srcs_orig[_si].data;
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
        // The same markup _dash_kpi_card_html builds: the scheme's card
        // colours are the .db-kpi-card rule on the Div, so no background
        // is written unless the KPI has an explicit bgcolor().  The value
        // div keeps its id (the name travels HTML-escaped as name_html):
        // the rebuild used to drop it, so the card changed shape on the
        // first filter move.  test_scheme_review_fixes diffs this
        // template against the Python card.
        kpi_div.text = (
            '<div class="db-kpi-card" style="' +
            (k.bgcolor ? 'background:' + k.bgcolor + '; ' : '') +
            'border-radius:8px; padding:20px; ' +
            'text-align:center; min-width:160px; min-height:110px;">' +
            '<div style="font-size:13px; color:' + k.text_color + '; margin-bottom:6px;">' + k.title + '</div>' +
            '<div id="kpi_val_' + k.name_html + '" style="font-size:36px; font-weight:bold; color:' + k.color + ';">' + fmt + '</div>' +
            '<div style="font-size:11px; color:' + k.text_color + '; margin-top:4px;">' + k.subtitle + '</div>' +
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
        column: "Any | None" = None,
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

        # Resolve nested {varname: {code: label}} or flat {code: label}
        if varname in value_labels and isinstance(value_labels[varname], dict):
            vlabels: dict = value_labels[varname]
        else:
            vlabels = value_labels

        # The widget itself comes from the builder the generated app runs
        # as well; `column' is the variable over the WHOLE dataset, so the
        # categories are the data's and not the first graph's.
        _values = column if column is not None else source.data.get(varname, [])
        widget, _sentinel = _dash_filter_widget(
            "dropdown", varname, _values,
            _dash_filter_title(label, FilterBuilder._safe(varname), "dropdown"),
            vlabels)

        callback = CustomJS(
            args={
                "source":            source,
                # JSON strings (not dicts/lists) so Bokeh 3.x serialises
                # them as plain JS strings, not Map objects.  Parsed via
                # JSON.parse() inside _FILTER_JS.  orig_source is a MODEL,
                # not a string: it is shared by every callback so the dataset
                # is written into the document once.
                "orig_source":       ColumnDataSource(),  # populated by DashRenderer.render()
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
                "all_graph_sources_orig": [],   # populated by DashRenderer.render()
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
        column: "Any | None" = None,
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
        _values = column if column is not None else source.data.get(varname, [])
        widget, _ = _dash_filter_widget(
            "slider", varname, _values,
            _dash_filter_title(label, safe_var, "slider"), None, date_kind)
        if widget is None:
            widget = Slider(title=_dash_filter_title(label, safe_var, "slider"),
                            start=0, end=1, value=0, step=1, disabled=True)
        if getattr(widget, "disabled", False):
            callback = CustomJS(args={}, code="")
            return widget, callback

        callback = CustomJS(
            args={
                "source":            source,
                "orig_source":       ColumnDataSource(),
                "all_widgets":       [],
                "filter_specs_json": "[]",
                "kpi_config_json":   "[]",
                "kpi_divs":          [],
                "agg_sources":       [],
                "agg_configs_json":  "[]",
                "all_graph_sources": [],              # populated by DashRenderer.render()
                "all_graph_sources_orig": [],   # populated by DashRenderer.render()
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
        column: "Any | None" = None,
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
        _values = column if column is not None else source.data.get(varname, [])
        widget, _ = _dash_filter_widget(
            "range", varname, _values,
            _dash_filter_title(label, safe_var, "range"), None, date_kind)
        if widget is None:
            widget = RangeSlider(title=_dash_filter_title(label, safe_var, "range"),
                                 start=0, end=1, value=(0, 1), step=1,
                                 disabled=True)
        if getattr(widget, "disabled", False):
            callback = CustomJS(args={}, code="")
            return widget, callback

        callback = CustomJS(
            args={
                "source":            source,
                "orig_source":       ColumnDataSource(),
                "all_widgets":       [],
                "filter_specs_json": "[]",
                "kpi_config_json":   "[]",
                "kpi_divs":          [],
                "agg_sources":       [],
                "agg_configs_json":  "[]",
                "all_graph_sources": [],              # populated by DashRenderer.render()
                "all_graph_sources_orig": [],   # populated by DashRenderer.render()
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
    # s1rcolor is Stata's own dark scheme -- light markers and light text on
    # a black plot region.  dash.sthlp has advertised theme(dark) since the
    # first release and the map had no such key, so the one theme name a user
    # picks precisely because they want a dark dashboard warned that it was
    # unknown and drew s2color, which is white.
    "dark":       "s1rcolor",
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
    # name that is neither an alias, nor a shipped scheme, nor something
    # SchemeParser can resolve -- a .scheme file in the working directory,
    # by bare name or with the extension -- is reported: theme(dark) is
    # documented in dash.sthlp, was absent from the map, and used to fall
    # through to s2color without a word.
    #
    # The parser is asked, not second-guessed.  This gate used to refuse
    # any unknown name that did not end in ".scheme" before _resolve_path's
    # bare-name branch could look in the working directory, while the
    # per-graph swap in _make_figure called the parser directly and found
    # the file: `dash scatter ..., scheme(mytheme)' drew the figure with
    # mytheme and the page chrome with s2color, and `dash build,
    # scheme(mytheme)' drew s2color throughout (measured, WP-17).
    #
    # dash.ado refuses an explicit scheme()/theme() it cannot resolve
    # before Python runs, so a name that arrives here unresolved is the
    # session's own c(scheme) -- 129 third-party schemes on one machine,
    # and cscript's s2color8 before dash shipped it -- or a spec built by
    # hand.  The warning says so.  One line; the words three other tests
    # pin ("is not a known theme or scheme") are kept.
    _lower = _raw_name.lower()
    if (_raw_name and _lower not in _THEME_SCHEME_MAP
            and _lower not in SchemeParser._BUILTIN_NAMES
            and not SchemeParser.can_resolve(_raw_name)):
        warnings.warn(
            f"dash: {_raw_name!r} is not a known theme or scheme; it was "
            "inherited from the session (c(scheme)) because no scheme() or "
            "theme() was given, or came from a spec built without "
            "dash.ado; using s2color. Themes: "
            f"{', '.join(sorted(_THEME_SCHEME_MAP))}. Schemes: "
            f"{', '.join(sorted(SchemeParser._BUILTIN_NAMES))}.",
            UserWarning,
        )
        _raw_name = ""
        _lower = ""
    # A shipped name is accepted in any case -- dash.ado's gate lowers it
    # too -- and handed on lowered, so it resolves on a case-sensitive
    # filesystem as it does on this one, and `scheme.name' is the scheme's
    # own spelling rather than the caller's.  A user file keeps its
    # spelling: the parser looks for that file.
    # ... with or without the extension: scheme(S2COLOR.SCHEME) is the
    # shipped s2color, not a file of that spelling.
    _base = _lower[:-len(".scheme")] if _lower.endswith(".scheme") else _lower
    if _base in SchemeParser._BUILTIN_NAMES:
        _raw_name = _base
        _lower = _base
    _scheme_name: str = (
        _THEME_SCHEME_MAP.get(_lower, _raw_name) or "s2color"
    )
    return _scheme_name


# ---------------------------------------------------------------------------
# Plot-type dispatch, shared by both render modes
# ---------------------------------------------------------------------------
# These live at module level, and the glyph dispatch below is written as
# plain functions taking the mapper as a parameter, for one reason: the
# generated Bokeh Server app copies them into itself with
# ``inspect.getsource``.  That is the same mechanism
# ``ServerAppBuilder._shared_stat_lines`` already uses for the statistical
# helpers, and for the same stated reason -- it copies the SAME source text
# both modes run, so the two cannot drift.
#
# Before this, the server reimplemented every plot type inline as an
# ``if/elif ptype == '...'`` chain of emitted string literals.  Measured:
# ``grep -oE '_DASH_MAPPER\.map_[a-z_]+'`` over this file returned exactly
# one name, ``map_scatter``.  The whole GlyphMapper class was already
# embedded in the app and 38 of its 39 methods were simply never called.

#: Plot categories that use non-standard JSON variable keys.
_DASH_RANGE_TYPES = frozenset({
    "rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
    "rcapsym", "tsrline", "rscatter",
})
_DASH_UNIVARIATE_TYPES = frozenset({"histogram", "hist", "kdensity"})
# pcscatter belongs here: it takes four variables, exactly as the other
# three do.  Left out, it fell through to no branch at all and drew an empty
# plot region with rc 0 and no warning.
_DASH_PC_TYPES = frozenset({"pcspike", "pcarrow", "pcbarrow", "pcscatter"})

#: Plot types that carry no variable names -- an inline coordinate list or
#: an expression.  Both renderers branch on these by name BEFORE the
#: dispatch tables, so this is the one place they are listed; the parity
#: guard derives the full set of plot types from it and the tables.
_DASH_LITERAL_TYPES = frozenset({"scatteri", "pci", "function"})


#: Injection patterns a by() string may not carry.  One copy: the saved
#: renderer and the generated app each used to hold their own.
_DASH_UNSAFE_BY = re.compile(
    r'[;`$\\]|import\s|__|\beval\b|\bexec\b|\bopen\b'
    r'|\bgetattr\b|\bsetattr\b|\bhasattr\b|\bdelattr\b'
)

#: The by() sub-options dash implements, with the abbreviations Stata's
#: by_option grammar allows for them (c:ols, miss:ing; total has none).
_DASH_BY_SUPPORTED = {
    "cols": ("c", "co", "col", "cols"),
    "missing": ("miss", "missi", "missin", "missing"),
    "total": ("total",),
}


def _dash_by_tokens(subopts):
    """Split a by() sub-option string into its options.

    ``rows(2) title("By origin") compact`` is three options, not five words:
    a parenthesised argument may hold spaces and quotes.  Splitting on
    whitespace alone is how ``holes(1 3)`` would be reported as two.
    """
    out, buf, depth, quote = [], [], 0, ""
    for ch in subopts:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in ('"', "'") and depth:
            quote = ch
            buf.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch.isspace() and depth == 0:
            if buf:
                out.append("".join(buf))
                buf = []
            continue
        buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


def _dash_parse_by(by_raw, warn=True):
    """Parse ``by(varlist [, subopts])`` the same way in both render modes.

    Returns ``(varlist, by_cols, by_total, by_missing, unsupported)``.  The
    varlist is "" when the string carries an injection pattern, and callers
    treat an empty varlist as "no faceting", which is what both renderers
    did with their own copies of the check.

    Stata's by() takes some thirty sub-options; dash implements three.  The
    rest used to be matched by nothing and discarded by everything --
    ``by(foreign, rows(2) compact)`` faceted as though the user had typed
    ``by(foreign)``, and nothing said so.  They are named here, once, in
    one warning, because a sub-option that is not implemented must be
    NAMED rather than silently dropped (ROADMAP BR-11.2).  Implementing
    them is other work.

    ``warn=False`` parses without reporting.  The saved renderer parses a
    graph's by() twice -- once to group the frame and once, in the layout,
    for its cols(#) -- and reported the same sub-options twice per render.
    The grouping parse reports; the layout parse does not.
    """
    by_raw = (by_raw or "").strip()
    if not by_raw or _DASH_UNSAFE_BY.search(by_raw):
        return "", 0, False, False, []
    if "," in by_raw:
        varlist_part, subopts = by_raw.split(",", 1)
    else:
        varlist_part, subopts = by_raw, ""
    varlist = varlist_part.strip()
    by_cols, by_total, by_missing = 0, False, False
    unsupported = []
    for tok in _dash_by_tokens(subopts.strip()):
        name = tok.split("(", 1)[0].strip().lower()
        arg = tok[len(name) + 1:-1] if "(" in tok and tok.endswith(")") else ""
        if name in _DASH_BY_SUPPORTED["cols"] and "(" in tok:
            try:
                by_cols = int(arg.strip())
            except ValueError:
                unsupported.append(tok)
        elif name in _DASH_BY_SUPPORTED["total"] and "(" not in tok:
            by_total = True
        elif name in _DASH_BY_SUPPORTED["missing"] and "(" not in tok:
            by_missing = True
        else:
            unsupported.append(tok)
    if unsupported and warn:
        # Names ONLY what was dropped.  Naming the three that work beside
        # them read as though those had been dropped too.
        warnings.warn(
            "dash: by() sub-option(s) not implemented and ignored: "
            + " ".join(unsupported),
            UserWarning, stacklevel=2,
        )
    return varlist, by_cols, by_total, by_missing, unsupported


def _dash_facet_label(by_vars, key, value_label_names=None, value_labels=None,
                      date_vars=None, numeric_formats=None,
                      date_formatter=None):
    """The title of one by() panel, the same in both render modes.

    Value labels where the dataset has them, a date shown as a date, a
    number shown in the variable's own display format, and "Missing" for a
    missing key.  Written once: the generated app carried its own copy of
    the value-label half and none of the rest.

    Args:
        by_vars:            The by() variables, in order.
        key:                The group key -- scalar for one variable, tuple
                            for several.
        value_label_names:  ``{varname: labelset}``.
        value_labels:       ``{labelset: {code: text}}``.
        date_vars:          ``{varname: kind}`` for date variables.
        numeric_formats:    ``{varname: "%9.2f"}`` display formats.
        date_formatter:     ``f(value, kind) -> str``.

    Returns:
        A display string like ``"Domestic"`` or ``"Domestic / 3"``.
    """
    value_label_names = value_label_names or {}
    value_labels = value_labels or {}
    date_vars = date_vars or {}
    numeric_formats = numeric_formats or {}
    keys = [key] if len(by_vars) == 1 else list(key)
    parts = []
    for var, val in zip(by_vars, keys):
        if pd.isna(val):
            parts.append("Missing")
            continue
        _kind = date_vars.get(var)
        if _kind and date_formatter is not None:
            parts.append(date_formatter(val, _kind))
            continue
        _numfmt = numeric_formats.get(var, "")
        if _numfmt:
            parts.append(_format_stata_numeric(val, _numfmt).strip())
            continue
        labelset = value_label_names.get(var, "")
        vlabels = value_labels.get(labelset, {}) if labelset else {}
        # Some callers key valueLabels by variable name rather than by
        # label-set name (regen scripts that pre-date jsonio's format).
        if not vlabels:
            candidate = value_labels.get(var, {})
            if isinstance(candidate, dict):
                vlabels = candidate
        str_val = str(val)
        int_str = (str(int(val)) if isinstance(val, float) and val == int(val)
                   else str_val)
        label = vlabels.get(str_val) or vlabels.get(int_str) or str_val
        parts.append(html.escape(label))
    return " / ".join(parts)



# ===========================================================================
# One implementation, two callers
#
# Everything below runs in BOTH render modes: the saved renderer calls it
# directly and the generated server app copies it in by name (see
# ServerAppBuilder._glyph_layer_lines).  Each helper closes a place where
# test/test_mode_parity.py measured the two renderers drawing the same
# spec two ways.
# ===========================================================================

# ---- The legend -----------------------------------------------------------

#: Stata's clock positions grouped into Bokeh's four side panels.  12 is
#: straight up, 3 right, 6 down, 9 left; ring(0) keeps the legend inside
#: the plot region at the matching inside location instead.
_DASH_CLOCK_SIDE = {
    11: "above", 12: "above", 1: "above",
    2: "right", 3: "right", 4: "right",
    5: "below", 6: "below", 7: "below",
    8: "left", 9: "left", 10: "left",
}
_DASH_CLOCK_INSIDE = {
    11: "top_left", 12: "top_center", 1: "top_right",
    2: "top_right", 3: "center_right", 4: "bottom_right",
    5: "bottom_right", 6: "bottom_center", 7: "bottom_left",
    8: "bottom_left", 9: "center_left", 10: "top_left",
}
#: The bare direction keywords, aliases for a clock position.  "on" and
#: "ring" are NOT placements and must never be in this map: `ring' matched
#: the word inside ring(0) once, and overwrote every inside placement.
_DASH_LEGEND_KEYWORD_LOC = {
    "top": "top_center", "bottom": "bottom_center",
    "left": "center_left", "right": "center_right",
}


def _dash_move_legend(fig, legend, side):
    """Move an attached Legend into one of the figure's side panels, as
    Stata's ring 3: nearest the plot, and centred.

    Bokeh lays a side panel out in list order, the first item nearest the
    plot (``above`` and ``left`` are reversed on the way, to the same
    effect).  ``add_layout`` appends, so the legend went OUTSIDE whatever
    was already there: under s2color ``fig.below`` was ``[axis, note,
    caption, legend]`` and the note and caption sat between the plot and
    the legend; under economist the legend sat between the title and the
    subtitle.  Stata's rings are the other way round -- legend 3, note 4,
    caption 5, subtitle 6, title 7 (scheme-s2color.scheme:1946-1951) --
    so the legend goes in after the panel's axes and before everything
    else.  After the axes, not at index 0: the axis is ring 1-2 and a
    legend between the frame and the tick labels is what no scheme asks
    for.

    A side-panel legend is positioned by its ``location`` within the
    panel, and Bokeh's default ``top_right`` drew it flush right under
    the plot where Stata centres a 6 o'clock legend (and centres a 3
    o'clock one vertically).  Both modes come through here, so they
    cannot disagree.
    """
    from bokeh.models import Axis
    for container in (fig.center, fig.above, fig.below, fig.left, fig.right):
        try:
            if legend in container:
                container.remove(legend)
        except (TypeError, ValueError):
            pass
    panel = list(getattr(fig, side))
    at = next((i for i, m in enumerate(panel) if not isinstance(m, Axis)),
              len(panel))
    panel.insert(at, legend)
    setattr(fig, side, panel)
    legend.location = "center"


def _dash_scheme_chrome(scheme):
    """The legend's chrome and default placement from *scheme*, for both
    modes: the saved renderer's ``_rebuild_legend`` and the served app
    pass this dict to ``_dash_apply_legend``.

    The keys are Stata's legend box: ``color legend`` and ``color
    legend_line`` for the box, the ``key_label`` textbox's size and colour
    for the labels (not ``gsize text``, which the box used to take), and
    ``clockdir legend_position`` / ``numstyle legend_cols`` /
    ``numstyle legend_rows`` for where it sits when the user says nothing.
    """
    return {
        "legend_bg_color": scheme.legend_bg_color,
        "legend_border_color": scheme.legend_border_color,
        "label_text_font_size": scheme.key_label_font_size,
        "label_text_color": scheme.key_label_color,
        "legend_position": getattr(scheme, "legend_position", None),
        "legend_cols": getattr(scheme, "legend_cols", None) or 0,
        "legend_rows": getattr(scheme, "legend_rows", 0) or 0,
    }


def _dash_apply_legend(fig, plot_renderers, legend_opt, var_labels=None,
                       default_level=None, chrome=None, seen=None, key=""):
    """Stata's keys, Stata's drawing rule, and every legend() sub-option.

    ``twoway`` draws a legend if and only if the graph has two or more keys;
    ``legend(on)`` forces one, ``legend(off)`` removes it, and position(),
    ring(0), order(), size(), label(), cols() and rows() are all documented
    in dash.sthlp.  The saved renderer honoured all of them; the generated
    app had its own block that knew off, the four bare keywords, label()
    and cols()/rows(), hard-coded a clickable legend and escaped the keys
    as HTML.  Measured: position(6) was below and horizontal when saved,
    top-right and vertical when served; order(2 1) did nothing served;
    size(small) was 7px saved and 11pt served; a one-series legend(on) was
    visible saved and hidden served.

    click_policy is deliberately left at Bokeh's default: nothing in the
    help promises a clickable legend, and Stata's legend is static.

    Args:
        fig:            The figure, every glyph already added.
        plot_renderers: ``[(plot_spec, [renderer, ...]), ...]`` in draw order.
        legend_opt:     The graph's legend() text, '' when absent.
        var_labels:     ``{varname: label}`` for the series keys.
        default_level:  The dashboard's level(), for a band's key.
        chrome:         ``_dash_scheme_chrome(scheme)``: the box colours,
                        the key_label size and colour, and the scheme's
                        default placement (clock, cols, rows), which
                        applies only when the user gave no position(),
                        ring() or bare keyword.
    """
    from bokeh.models import LegendItem
    legend_opt = str(legend_opt or "")
    chrome = chrome or {}
    if default_level is None:
        default_level = _DEFAULT_LEVEL
    # Before the early return: a sub-option dash has no reading for is
    # dropped whether or not this figure has a legend to apply it to.
    _dash_report_suboptions("legend", _dash_legend_unsupported(legend_opt),
                            seen, key)
    if not fig.legend:
        # The mapper made none (pci, scatteri, lowess): twoway draws none.
        return

    # A discrete colorvar() builds its colour key as a Legend too.  It is
    # not a series key -- Stata suppresses it with clegend(), not legend()
    # -- so it is kept out of the rebuild and stays visible.
    cv_legends = [lg for lg in fig.legend
                  if str(getattr(lg, "name", "") or "") == _COLORVAR_LEGEND_NAME]
    plot_legends = [lg for lg in fig.legend if lg not in cv_legends]
    legend = plot_legends[0] if plot_legends else None

    # 1. The keys, rebuilt IN PLACE on the mapper's own legend.  Raw text:
    #    Bokeh draws a legend label on the canvas, not in the DOM.
    if legend is not None and plot_renderers:
        live = [(plot, [r for r in rends if r in fig.renderers])
                for plot, rends in plot_renderers]
        items = [LegendItem(label={"value": lbl}, renderers=rends)
                 for lbl, rends in _dash_legend_entries(
                     live, var_labels or {}, default_level)]
        if items:
            legend.items = items

    # 2. order() -- 1-based, and it may also DROP keys.
    m_order = re.search(r"\border\s*\(([^)]*)\)", legend_opt)
    if m_order and legend is not None:
        wanted = [int(t) for t in re.findall(r"\d+", m_order.group(1))]
        current = list(legend.items)
        legend.items = [current[i - 1] for i in wanted
                        if 1 <= i <= len(current)]

    # 3. The scheme's chrome on EVERY legend, before the user's options so
    #    an explicit size() still wins.
    for lg in fig.legend:
        if chrome.get("legend_bg_color"):
            lg.background_fill_color = chrome["legend_bg_color"]
        if chrome.get("legend_border_color"):
            lg.border_line_color = chrome["legend_border_color"]
        # The key_label textbox's size and colour ("text_font_size" is the
        # older name of the same slot, kept for a caller-built dict).
        _lsize = (chrome.get("label_text_font_size")
                  or chrome.get("text_font_size"))
        if _lsize:
            lg.label_text_font_size = _lsize
        if chrome.get("label_text_color"):
            lg.label_text_color = chrome["label_text_color"]

    # 4. Placement: position()/ring(0) first; a bare keyword only when
    #    neither is given, because the clock is the more specific form;
    #    and the SCHEME's clock only when the user gave none of the three.
    #    `clockdir legend_position' and `numstyle legend_cols' were parsed
    #    and read by nothing, so every legend sat at Bokeh's top_right
    #    inside the plot where s2color puts it below in two columns.
    m_pos = re.search(r"\b(?:position|pos)\s*\(\s*(\d+)\s*\)", legend_opt)
    m_ring = re.search(r"\bring\s*\(\s*(\d+)\s*\)", legend_opt)
    inside = bool(m_ring) and m_ring.group(1) == "0"
    if legend is not None:
        placed = False
        if m_pos:
            placed = True
            clock = int(m_pos.group(1))
            if inside:
                legend.location = _DASH_CLOCK_INSIDE.get(clock, "top_right")
            else:
                side = _DASH_CLOCK_SIDE.get(clock, "right")
                _dash_move_legend(fig, legend, side)
                legend.orientation = ("horizontal"
                                      if side in ("above", "below")
                                      else "vertical")
        elif not m_ring:
            for kw, loc in _DASH_LEGEND_KEYWORD_LOC.items():
                if re.search(r"\b" + re.escape(kw) + r"\b", legend_opt):
                    placed = True
                    for lg in fig.legend:
                        lg.location = loc
                    break
        if not placed and not m_ring and chrome.get("legend_position"):
            try:
                clock = int(chrome["legend_position"])
            except (TypeError, ValueError):
                clock = None
            if clock is not None:
                side = _DASH_CLOCK_SIDE.get(clock, "right")
                _dash_move_legend(fig, legend, side)
                horizontal = side in ("above", "below")
                legend.orientation = "horizontal" if horizontal else "vertical"
                # Stata's legend_cols is a maximum: 6 o'clock under
                # s2color is two columns, economist's 12 o'clock three; a
                # side legend takes it only when it asks for more than one.
                try:
                    cols = int(chrome.get("legend_cols") or 0)
                    rows = int(chrome.get("legend_rows") or 0)
                except (TypeError, ValueError):
                    cols, rows = 0, 0
                if cols > 0 and (horizontal or cols > 1):
                    legend.ncols = cols
                if rows > 0:
                    legend.nrows = rows

    # 5. label(N "text") overrides.  Escaped: this text is the user's and
    #    the rule is pinned by test_legend_label_xss_escaped.
    if legend is not None:
        for lm in re.finditer(r'label\(\s*(\d+)\s+"([^"]*)"\s*\)', legend_opt):
            idx = int(lm.group(1)) - 1
            if 0 <= idx < len(legend.items):
                legend.items[idx].label = {"value": html.escape(lm.group(2))}

    # 6. cols()/rows() on every legend.  Stata treats the two as
    #    alternatives, so the one the user did not give goes back to
    #    "auto": the scheme's ncols (2 under s2color, 3 under economist)
    #    used to survive a user rows(1), and Bokeh then laid out ncols=2,
    #    nrows=1 and wrapped the third key onto a second row.
    m_cols = re.search(r"\bcols\s*\(\s*(\d+)\s*\)", legend_opt)
    m_rows = re.search(r"\brows\s*\(\s*(\d+)\s*\)", legend_opt)
    for lg in fig.legend:
        try:
            if m_cols:
                lg.ncols = int(m_cols.group(1))
            if m_rows:
                lg.nrows = int(m_rows.group(1))
            if m_cols and not m_rows:
                lg.nrows = "auto"
            elif m_rows and not m_cols:
                lg.ncols = "auto"
        except (ValueError, AttributeError):
            pass

    # 7. size() on every legend, including a colour key: the user asked
    #    for a legend text size, not a plot-legend text size.
    m_size = re.search(r"\bsize\s*\(\s*([^)]+?)\s*\)", legend_opt)
    if m_size:
        try:
            px = f"{OptionTranslator.translate_msize(m_size.group(1)):g}px"
            for lg in fig.legend:
                lg.label_text_font_size = px
        except (ValueError, TypeError):
            # Was dropped in silence; the scheme's legend size stays.
            _dash_style_note("legend(size)", m_size.group(1), "size")

    # 8. Stata's rule governs the SERIES key; `off' is a word match so
    #    legend(pos(6) off) hides it.  A colour key stays visible.
    forced_on = bool(re.search(r"\bon\b", legend_opt))
    turned_off = bool(re.search(r"\boff\b", legend_opt))
    n_keys = len(legend.items) if legend is not None else 0
    show = not (turned_off or (n_keys < 2 and not forced_on))
    for lg in plot_legends:
        lg.visible = show
    for lg in cv_legends:
        lg.visible = True


# ---- Axis titles, ticks and secondary axes -----------------------------------

#: Stata's y-axis title for each histogram scale, measured by exporting
#: `twoway histogram mpg[, percent|frequency|fraction]' to SVG.
_DASH_HIST_YTITLES = {"density": "Density", "fraction": "Fraction",
                      "frequency": "Frequency", "percent": "Percent"}


def _dash_histogram_ymode(options):
    """The scale a histogram draws on: the first of Stata's four flags set,
    density when none is.  One rule for the bars AND the y title."""
    for flag in ("frequency", "percent", "fraction", "density"):
        if str((options or {}).get(flag, "")).strip():
            return flag
    return "density"


def _dash_axis_labels(plots, graph_opts, var_labels, seen=None, key=""):
    """``(x_label, y_label)``: xtitle()/ytitle() first, else Stata's default.

    The default is the FIRST layer's variable label.  For the univariate
    types Stata's own titles, measured by SVG export, are: histogram y
    "Density"/"Percent"/"Frequency"/"Fraction" and x the variable's label;
    kdensity y "kdensity <var>" and x "x".  Both renderers used to title a
    histogram's y axis differently (nothing saved, the variable served),
    and neither as Stata does.

    Canvas text, never html.escape'd: Bokeh draws an axis title as a glyph,
    so escaping made xtitle("R&D spend") read "R&amp;D spend" when served.
    """
    go, vl = graph_opts or {}, var_labels or {}
    p0 = plots[0] if plots else {}
    ptype = str(p0.get("type", "") or "").lower()
    if ptype == "hist":
        ptype = "histogram"
    if ptype in _DASH_UNIVARIATE_TYPES:
        var = p0.get("var", "") or p0.get("yvar", "")
        if ptype == "kdensity":
            x_default = "x"
            y_default = ("kdensity %s" % var) if var else ""
        else:
            x_default = vl.get(var, var)
            y_default = _DASH_HIST_YTITLES[
                _dash_histogram_ymode(p0.get("options"))]
    else:
        xvar, yvar = p0.get("xvar", ""), p0.get("yvar", "")
        x_default, y_default = vl.get(xvar, xvar), vl.get(yvar, yvar)
    # The text, split from its sub-options: xtitle("Weight", size(large))
    # used to title the axis "Weight, size(large)".  size() and color()
    # are applied by _dash_style_axis_titles; the rest is named.
    x_text, _ = _dash_textbox(go.get("xtitle", ""), "xtitle", seen, key)
    y_text, _ = _dash_textbox(go.get("ytitle", ""), "ytitle", seen, key)
    x_label = x_text or x_default
    y_label = y_text or y_default
    return x_label, y_label


def _dash_parse_axis_label_opt(raw):
    """Parse the numlist form of xlabel()/ylabel().

    Supports a pure numeric list, ``"0 2 4 6"``, and a labelled list,
    ``'0 "Zero" 5 "Five"'``.  Invalid tokens are dropped.

    Returns:
        ``(ticks, labels)``: a sorted list of floats and a dict mapping
        ``str(float)`` to its label (empty when none were given).
    """
    ticks = []
    labels = {}
    tokens = re.findall(r'"([^"]*)"'  # double-quoted label
                        r"|'([^']*)'"  # single-quoted label
                        r"|([^\s,\"']+)",  # bare token (number or keyword)
                        str(raw or ""))
    flat = [dq or sq or bare for dq, sq, bare in tokens]
    i = 0
    while i < len(flat):
        tok = flat[i]
        try:
            val = float(tok)
            ticks.append(val)
            if i + 1 < len(flat):
                next_tok = flat[i + 1]
                try:
                    float(next_tok)
                except ValueError:
                    labels[str(val)] = next_tok
                    i += 1
            i += 1
        except ValueError:
            i += 1
    return sorted(ticks), labels


def _dash_parse_axis_spec(raw):
    """Parse Stata's full ``axis_label`` grammar.

    Handles a numlist (including the ``a(b)c`` increment form), ``#N``,
    ``minmax``, ``none``, explicit ``value "label"`` pairs, and the
    sub-options ``format()``, ``labsize()``, ``angle()``, ``grid`` and
    ``nogrid``.  The generated app used to carry a 14-line parser that read
    a bare numlist and angle() and nothing else, so ``xlabel(2000(1000)4000)``
    fixed the ticks when saved and was ignored when served.

    Returns:
        A dict with keys ``mode`` (``"default"``, ``"explicit"``, ``"count"``,
        ``"minmax"`` or ``"none"``), ``ticks``, ``count``, ``labels``,
        ``format``, ``labsize``, ``angle`` and ``grid``.
    """
    out = {"mode": "default", "ticks": [], "count": None,
           "labels": {}, "format": None, "labsize": None,
           "angle": None, "grid": None, "unsupported": []}
    if not raw or not str(raw).strip():
        return out
    text = str(raw)

    # The sub-options are what follows the first comma that introduces a
    # name (Stata also accepts a comma-separated numlist, which must
    # survive).  Each one dash does not honour is recorded, as written, for
    # the caller to name: labcolor(), labgap(), tlength(), valuelabel ...
    # used to be stripped or ignored without a word.
    _m_tail = re.search(r",\s*(?=[A-Za-z_])", text)
    if _m_tail:
        for _tok in _dash_by_tokens(text[_m_tail.end():].strip()):
            if _dash_subopt_name(_tok) not in ("format", "labsize", "angle",
                                               "grid", "nogrid"):
                out["unsupported"].append(_tok)

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
    # Stripping the sub-options above leaves their comma behind, so
    # `#5, grid' arrived here as `#5,' and matched none of the keyword
    # forms: the count was dropped in silence.  Measured 22sep2026.
    head = head.strip().rstrip(",").strip()

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
    ticks = []
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

    bare_ticks, labels = _dash_parse_axis_label_opt(rest)
    ticks.extend(bare_ticks)
    # A bare word in the numlist that is not a number, a label or one of
    # the keyword forms above is a sub-option written before the comma.
    _prev_num = False
    for _dq, _sq, _bare in re.findall(r'"([^"]*)"|\'([^\']*)\'|([^\s,"\']+)',
                                      rest):
        if _bare:
            try:
                float(_bare)
                _prev_num = True
                continue
            except ValueError:
                out["unsupported"].append(_bare)
        _prev_num = False
    if ticks:
        out["mode"] = "explicit"
        out["ticks"] = sorted(set(ticks))
        out["labels"] = labels
    return out


def _dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None,
                          fmt_fallback="", grid_color=None):
    """Apply a parsed ``axis_label`` spec to one axis.

    Args:
        axis_obj:     ``fig.xaxis`` or ``fig.yaxis``.
        grid_obj:     The matching grid, for ``grid``/``nogrid``.
        spec:         The output of :func:`_dash_parse_axis_spec`.
        values:       The variable's values on this axis, for ``minmax``;
                      the graph's own rows, so a qualified graph labels the
                      extremes it draws.
        fmt_fallback: The variable's Stata display format, used when the
                      spec names no format() of its own.
        grid_color:   The scheme's ``color major_grid``, drawn by an
                      explicit ``grid`` on an axis the scheme leaves bare.
                      It was a hard-coded #e5e5e5 in both modes, so
                      ``xlabel(, grid)`` under s1color drew a grid in no
                      scheme's colour.  None keeps that literal for a
                      caller with no scheme.
    """
    from bokeh.models.tickers import FixedTicker, BasicTicker
    from bokeh.models.formatters import (CustomJSTickFormatter,
                                         NumeralTickFormatter)

    mode = spec["mode"]
    if mode == "none":
        # Zero ticks BY INTENT.  Measured: Stata's xlabel(none) also
        # removes the gridlines.
        axis_obj.ticker = FixedTicker(ticks=[])
        for g in grid_obj:
            g.grid_line_color = None
    elif mode == "minmax":
        if values is not None:
            vals = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
            if len(vals):
                axis_obj.ticker = FixedTicker(
                    ticks=[float(vals.min()), float(vals.max())])
    elif mode == "count":
        # Stata's #N is a SUGGESTION -- measured, xlabel(#10) on weight
        # yields eight ticks.  Bokeh's desired_num_ticks means the same.
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

    fmt = spec["format"] or fmt_fallback
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
                    g.grid_line_color = grid_color or "#e5e5e5"
            else:
                g.grid_line_color = None


def _dash_apply_axis_options(fig, graph_opts, xvar, yvar, frame,
                             numeric_formats, seen=None, key="",
                             grid_color=None):
    """xlabel()/ylabel(), with xtick()/ytick() as the fallback, on a figure;
    the sub-options the grammar does not honour are named.  *grid_color*
    is the scheme's grid colour for an explicit ``grid``; both modes pass
    their scheme's."""
    cols = getattr(frame, "columns", [])
    for ax_key, tick_key, axis_obj, grid_obj, var in (
            ("xlabel", "xtick", fig.xaxis, fig.xgrid, xvar),
            ("ylabel", "ytick", fig.yaxis, fig.ygrid, yvar)):
        raw = graph_opts.get(ax_key, "") or graph_opts.get(tick_key, "")
        if not raw:
            continue
        spec = _dash_parse_axis_spec(raw)
        _dash_report_suboptions(ax_key if graph_opts.get(ax_key) else tick_key,
                                spec.get("unsupported", []), seen, key)
        col = frame[var] if var and var in cols else None
        _dash_apply_axis_spec(axis_obj, grid_obj, spec,
                              col, (numeric_formats or {}).get(var, ""),
                              grid_color)


def _dash_add_secondary_axes(fig, plots, graph_opts, frame):
    """Build ``extra_y_ranges['y2']`` / ``extra_x_ranges['x2']`` and their axes.

    A layer with yaxis(2) or xaxis(2) asks for a second axis whose range is
    computed from the rows the graph draws.  The generated app had no
    second axis at all, so the layer was served on the primary range.

    Returns ``(has_y2, has_x2)``.
    """
    from bokeh.models import LinearAxis, LogAxis, Range1d
    from bokeh.models.tickers import FixedTicker
    from bokeh.models.formatters import CustomJSTickFormatter
    has = {}
    for axis_key, var_key, rng_attr, name, side, kw in (
            ("yaxis", "yvar", "extra_y_ranges", "y2", "right", "y_range_name"),
            ("xaxis", "xvar", "extra_x_ranges", "x2", "above", "x_range_name")):
        wanted = any(str(p.get("options", {}).get(axis_key, "1")).strip() == "2"
                     for p in plots)
        has[name] = wanted
        if not wanted:
            continue
        lo, hi = _compute_secondary_range(frame, plots, axis_key, var_key, 2)
        getattr(fig, rng_attr)[name] = Range1d(lo, hi)
        n = name[0]
        is_log, is_rev = _parse_scale_opt(graph_opts.get(f"{n}scale2", ""))
        ax = (LogAxis if is_log else LinearAxis)(
            **{kw: name}, axis_label=graph_opts.get(f"{n}title2", ""))
        fig.add_layout(ax, side)
        if is_rev:
            try:
                getattr(fig, rng_attr)[name].flipped = True
            except AttributeError:
                pass
        raw = graph_opts.get(f"{n}label2", "")
        if raw:
            ticks, labels = _dash_parse_axis_label_opt(raw)
            if ticks:
                ax.ticker = FixedTicker(ticks=ticks)
                if labels:
                    safe = {str(k): html.escape(str(v))
                            for k, v in labels.items()}
                    ax.formatter = CustomJSTickFormatter(
                        code=f"const m = {json.dumps(safe)}; "
                             "return m[String(tick)] || String(tick);")
            ang = _parse_axis_angle(raw)
            if ang is not None:
                ax.major_label_orientation = ang
    return has["y2"], has["x2"]


def _dash_assign_axis_ranges(fig, renderers, options):
    """Put one layer's renderers on the secondary range(s) its yaxis()/xaxis()
    name -- if the figure has them.  A throwaway redraw figure has none."""
    use_y2 = (str((options or {}).get("yaxis", "1")).strip() == "2"
              and "y2" in fig.extra_y_ranges)
    use_x2 = (str((options or {}).get("xaxis", "1")).strip() == "2"
              and "x2" in fig.extra_x_ranges)
    if not (use_y2 or use_x2):
        return
    for r in renderers:
        try:
            if use_y2:
                r.y_range_name = "y2"
            if use_x2:
                r.x_range_name = "x2"
        except AttributeError:
            pass


# ---- Filter widgets -----------------------------------------------------------

def _dash_option_value(v):
    """The one string a dropdown carries for a data value, in both modes.

    ``0.0`` becomes ``'0'`` because the saved page compares ``String(v)`` in
    JavaScript, where ``String(0.0)`` is ``"0"``; the served app used
    ``str(v)`` and carried ``'0.0'``, so the two documents held different
    option values for the same category.
    """
    s = str(v)
    try:
        f = float(s)
        i = int(f)
        if f == i:
            return str(i)
    except (ValueError, TypeError, OverflowError):
        pass
    return s


def _dash_option_sort_key(rv):
    try:
        return (0, float(rv))
    except (ValueError, TypeError):
        return (1, rv)


def _dash_filter_title(label, fallback, ftype):
    """A widget's title: the resolved label, plus the documented inequality
    on a threshold slider (dash.sthlp: "varname >= slider value")."""
    raw = str(label or "").strip() or str(fallback)
    if ftype == "slider" and not raw.endswith(("≥", ">=")):
        raw += " ≥"
    return raw


def _dash_finite_column(col, allow_datetime=False):
    """A float array of the non-missing values of one column.

    A datetime64 column is converted to epoch milliseconds -- the unit Bokeh
    transports datetimes in -- when *allow_datetime* is set.
    """
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


def _dash_filter_widget(ftype, varname, column, title, value_labels=None,
                        date_kind=""):
    """The one filter widget both modes show for ``filter(varname, type())``.

    Args:
        ftype:        ``"dropdown"``, ``"slider"`` or ``"range"``.
        varname:      The variable.
        column:       Its values over the WHOLE dataset -- a widget's
                      categories and bounds describe the data, not whatever
                      the first graph happens to draw.
        title:        The resolved widget title.
        value_labels: ``{code: label}`` for the dropdown's display text.
        date_kind:    The variable's Stata date kind, for a clock series.

    Returns:
        ``(widget, sentinel)``.  The widget is None when the column cannot
        carry a slider or range (a string variable); the caller reports
        that.  An all-missing numeric column gives a disabled widget.
    """
    from bokeh.models import (DateRangeSlider, DateSlider, DatetimeRangeSlider,
                              DatetimeTickFormatter, RangeSlider, Select,
                              Slider)
    series = pd.Series(column)
    is_date = bool(pd.api.types.is_datetime64_any_dtype(series))
    if ftype == "dropdown":
        vlabels = value_labels or {}
        raw_values = sorted(
            {_dash_option_value(v) for v in series.tolist()
             if v is not None and str(v) not in ("nan", "None", "NaT")},
            key=_dash_option_sort_key)
        # A per-widget sentinel absent from the data, so a real category
        # equal to the literal string "__all__" stays selectable.
        sentinel = "__all__"
        while sentinel in raw_values:
            sentinel += "_"

        def _label(rv):
            if rv in vlabels:
                return vlabels[rv]
            try:
                k = str(int(float(rv)))
                if k in vlabels:
                    return vlabels[k]
            except (ValueError, OverflowError):
                pass
            return rv

        options = [(sentinel, "All")] + [
            (rv, html.escape(str(_label(rv)), quote=True)) for rv in raw_values]
        w = Select(title=title, value=sentinel, options=options)
        w._dash_sentinel = sentinel
        w._dash_ftype = "dropdown"
        return w, sentinel
    if ftype not in ("slider", "range"):
        return None, None
    if not (pd.api.types.is_numeric_dtype(series) or is_date):
        return None, None
    arr = _dash_finite_column(series, allow_datetime=True)
    if len(arr) == 0:
        w = (RangeSlider(title=title, start=0, end=1, value=(0, 1), step=1,
                         disabled=True)
             if ftype == "range" else
             Slider(title=title, start=0, end=1, value=0, step=1,
                    disabled=True))
        w._dash_ftype = ftype
        w._dash_is_date = is_date
        return w, None
    vmin, vmax = float(arr.min()), float(arr.max())
    if vmin == vmax:
        vmax = vmin + 1.0
    if is_date and _is_clock_kind(date_kind):
        # DateRangeSlider's step is a whole number of DAYS, so a clock
        # series spanning one day had a single reachable notch.
        step = _clock_slider_step_ms(vmin, vmax)
        w = (DatetimeRangeSlider(title=title, start=vmin, end=vmax,
                                 value=(vmin, vmax), step=step)
             if ftype == "range" else
             Slider(title=title, start=vmin, end=vmax, value=vmin, step=step,
                    format=DatetimeTickFormatter()))
    elif is_date:
        step = _date_slider_step_days(vmin, vmax)
        w = (DateRangeSlider(title=title, start=vmin, end=vmax,
                             value=(vmin, vmax), step=step)
             if ftype == "range" else
             DateSlider(title=title, start=vmin, end=vmax, value=vmin,
                        step=step))
    else:
        # A range of whole numbers steps by 1: (vmax - vmin) / 100 gave
        # rep78, which takes the values 1..5, a step of 0.04.
        step = _whole_number_step(arr, vmax - vmin)
        w = (RangeSlider(title=title, start=vmin, end=vmax,
                         value=(vmin, vmax), step=step)
             if ftype == "range" else
             Slider(title=title, start=vmin, end=vmax, value=vmin, step=step))
    w._dash_ftype = ftype
    w._dash_is_date = is_date
    return w, None


def _dash_dropdown_mask(column, value):
    """The rows a dropdown set to *value* keeps: the Python twin of the
    ``String(orig[fvar][i]) !== val`` test in the saved page's JavaScript.
    Both sides go through ``_dash_option_value``, so ``'1'`` and ``'1.0'``
    select the same rows."""
    want = _dash_option_value(value)
    return pd.Series(column).map(_dash_option_value).to_numpy() == want


# ---- The document: order, cells, tabs, header ----------------------------------

def _dash_layout_order(registry, graphs, kpis):
    """Display order of the registered items: the registry, as typed.

    ``dash.ado`` appends every name() -- graph or KPI -- to ONE registry in
    the order the user issued it, so that order is the user's.  A spec with
    no registry (hand-built) falls back to graphs then KPIs in spec order.
    A registered name that is neither is dropped; a graph or KPI the
    registry omits is appended, so nothing vanishes.

    The saved renderer used to put every KPI first whatever the registry
    said -- a Bootstrap hero-row policy that had leaked into every layout
    -- so the same spec placed a card above its graph when saved and below
    it when served.
    """
    gnames = [str((g.get("graph_options") or {}).get("name")
                  or g.get("name") or "") for g in graphs]
    knames = [str(k.get("name") or "") for k in kpis if k.get("name")]
    # An immediate render -- `dash scatter mpg weight, saving()' -- writes
    # ONE graph with no name and no registry; its figure is keyed '' and
    # must still be placed.  Dropping the empty name here produced a
    # saved dashboard with no figure and rc 0, which the certification
    # suite caught and the Python suite, whose every spec is named, did not.
    known = gnames + knames
    order = [n for n in str(registry or "").split() if n in known]
    seen = set(order)
    for n in known:
        if n not in seen:
            order.append(n)
            seen.add(n)
    return order


def _dash_kpi_keys(name, kpi_divs):
    """The ``kpi_divs`` keys one registered KPI owns: itself, or its
    per-facet cards ``name__by__0``, ``name__by__1`` ... in index order."""
    if name in kpi_divs:
        return [name]
    pre = name + "__by__"
    return sorted((k for k in kpi_divs if k.startswith(pre)),
                  key=lambda k: int(k[len(pre):]) if k[len(pre):].isdigit()
                  else 0)


def _dash_facet_cols(gopts, n_panels):
    """cols(#) from by() first, then the by_cols key, then ceil(sqrt(n))."""
    n_by = _dash_parse_by((gopts.get("by") or ""), warn=False)[1]
    try:
        n_key = int(gopts.get("by_cols", "0") or 0)
    except (ValueError, TypeError):
        n_key = 0
    n = n_by or n_key
    if n <= 0:
        n = min(n_panels, max(1, math.ceil(math.sqrt(n_panels))))
    return n


def _dash_layout_cell(name, figures, facet_map, kpi_divs, gopts_of):
    """The ONE renderable a registered name owns, or None.

    A faceted graph is one cell: its panels in a sub-grid that honours
    by(, cols(#)).  A plain graph is its figure.  A KPI is its card, or a
    column of its per-facet cards.  The grid AND the tab panels call this,
    in both modes -- the saved tabs used to flatten a faceted graph's
    panels into the tab's own grid, ignoring cols(), while the saved grid
    and the served app nested them.
    """
    if name in facet_map:
        figs = [figures[fk] for fk, _ in facet_map[name] if fk in figures]
        if not figs:
            return None
        cn = _dash_facet_cols(gopts_of(name) or {}, len(figs))
        rows = [figs[i:i + cn] for i in range(0, len(figs), cn)]
        while len(rows[-1]) < cn:
            rows[-1].append(None)
        return gridplot(rows, sizing_mode="stretch_width")
    if name in figures:
        return figures[name]
    keys = _dash_kpi_keys(name, kpi_divs)
    if len(keys) == 1:
        return kpi_divs[keys[0]]
    if keys:
        return column(*[kpi_divs[k] for k in keys], sizing_mode="stretch_width")
    return None


def _dash_parse_tabs(tabs_str, all_names):
    """``'Title: a b / Title2: c'`` -> ``[(title, [names])]``, or None.

    Tab titles are the user's text, verbatim.  Only registered names are
    accepted, so a tabs() option cannot place something that was never
    registered.
    """
    if not tabs_str or not str(tabs_str).strip():
        return None
    valid = set(all_names)
    result = []
    for i, segment in enumerate(str(tabs_str).split("/")):
        segment = segment.strip()
        if not segment:
            continue
        if ":" in segment:
            raw_title, _, items_str = segment.partition(":")
            title = raw_title.strip()
            items = [x.strip() for x in items_str.split() if x.strip()]
        else:
            items = [x.strip() for x in segment.split() if x.strip()]
            title = "Tab %d" % (i + 1)
        safe = [x for x in items if x in valid]
        if safe:
            result.append((title, safe))
    return result or None


def _dash_tab_panels(tabs_spec, cell_of):
    """``(Tabs or None, registered names placed)`` from ``[(title, [names])]``.
    Each tab is a ceil(sqrt(n)) grid of the cells its names own."""
    from bokeh.models import TabPanel, Tabs
    panels, placed = [], set()
    for title, names in (tabs_spec or []):
        items = [c for c in (cell_of(n) for n in names) if c is not None]
        if not items:
            continue
        placed.update(names)
        cn = max(1, math.ceil(math.sqrt(len(items))))
        rows = [items[i:i + cn] for i in range(0, len(items), cn)]
        while len(rows[-1]) < cn:
            rows[-1].append(None)
        panels.append(TabPanel(child=gridplot(rows, sizing_mode="stretch_width"),
                               title=title))
    if not panels:
        return None, placed
    return Tabs(tabs=panels, sizing_mode="stretch_width"), placed


def _dash_header_fragments(title_text, subtitle_text):
    """The dashboard header as two HTML fragments, either possibly empty.

    Escaped exactly once here: callers pass RAW text.  The classes are the
    ones the scheme's ``css_block()`` styles; the served app used to emit
    one classless Div with a hard-coded grey subtitle.
    """
    t = (f'<h2 class="db-title" style="margin-bottom:2px;">'
         f'{html.escape(title_text)}</h2>' if title_text else "")
    s = (f'<p class="db-subtitle" style="margin-top:0;margin-bottom:8px;">'
         f'{html.escape(subtitle_text)}</p>' if subtitle_text else "")
    return t, s


def _dash_header_models(title_text, subtitle_text, css=""):
    """The header as Bokeh Divs, for the plain grid and the served app.

    *css* is the scheme's ``css_block()``; a Bokeh 3 Div renders inside a
    shadow root, so the rules are attached to the Div itself rather than
    relied on from the page head.
    """
    from bokeh.models import Div, InlineStyleSheet
    sheets = [InlineStyleSheet(css=css)] if css else []
    return [Div(text=frag, sizing_mode="stretch_width",
                stylesheets=list(sheets))
            for frag in _dash_header_fragments(title_text, subtitle_text)
            if frag]


# ---- Columns a layer's options name, and the mapper's metadata -------------------

#: Plot OPTIONS that name a dataset column the layer's source must carry.
#: The served app carried mlabel() and hover() and nothing else, so
#: `colorvar(foreign)' served drew the scheme colour: _apply_colorvar
#: returns when its column is absent from the source.
_DASH_OPT_VAR_KEYS = ("colorvar", "mlabel")
#: The invisible swatch renderers a discrete colorvar() legend is built from.
_DASH_SWATCH_PREFIX = "_clegend_"


def _dash_mlabel_names(options):
    """``(first, extras)`` from a layer's mlabel() option.

    ``dash.ado`` validates mlabel() as one variable, so from a command it is
    always a single name.  A spec written by hand may carry several; the
    first is the label and the rest are named by ``_apply_mlabel_opts`` so
    that nothing is dropped in silence.  Read here, once, so that the
    column lists, the mappers that rebuild their source and the label
    applier agree on which name that is -- a source built for
    ``"make foreign"`` carried no column of that name, and the label
    applier then found nothing to draw.
    """
    names = str((options or {}).get("mlabel", "") or "").split()
    return (names[0] if names else ""), names[1:]


def _dash_option_columns(options, columns=None):
    """The columns a layer's options name -- colorvar() and mlabel() -- in
    ``_DASH_OPT_VAR_KEYS`` order, de-duplicated, restricted to *columns*
    when one is given."""
    out = []
    for key in _DASH_OPT_VAR_KEYS:
        if key == "mlabel":
            v = _dash_mlabel_names(options)[0]
        else:
            v = str((options or {}).get(key, "") or "").strip()
        if not v or v in out:
            continue
        if columns is not None and v not in columns:
            continue
        out.append(v)
    return out


def _dash_attach_labels(mapper, variable_labels=None, value_labels=None,
                        value_label_names=None, date_vars=None,
                        numeric_formats=None):
    """Give *mapper* the dataset's Stata metadata, in either render mode.

    ``_apply_colorvar`` reads value labels for the colour key and the
    variable label for its title; ``_apply_mlabel_opts`` reads date and
    numeric formats.  The served app built its mapper at module level and
    attached none of these, so a served colour key would have read "0"/"1"
    where the saved one reads "Domestic"/"Foreign".
    """
    mapper.variable_labels = (variable_labels if variable_labels is not None
                              else {})
    mapper.value_labels = value_labels if value_labels is not None else {}
    mapper.value_label_names = (value_label_names
                                if value_label_names is not None else {})
    mapper.date_vars = dict(date_vars or {})
    mapper.numeric_formats = dict(numeric_formats or {})
    return mapper


def _dash_is_swatch(renderer):
    """Is *renderer* one of a discrete colorvar() legend's invisible swatches?
    They are on the figure so the Legend can show a colour; they are not a
    series key and not a source to refresh or redraw on a filter move."""
    return str(getattr(renderer, "name", "") or "").startswith(
        _DASH_SWATCH_PREFIX)


# ---- The dashboard's confidence level ------------------------------------------

def _dash_session_level(build_options, default=_DEFAULT_LEVEL):
    """The dashboard's confidence level: c(level) as dash.ado serialised it.

    A per-plot level() overrides this in ``_resolve_level``; an absent,
    blank, non-numeric or out-of-range value falls back to Stata's factory
    95 with a warning, in BOTH modes.  The served app used to read it,
    unvalidated, for the legend key and not at all for the band -- so a
    served lfitci under `set level 90' drew a 95% band labelled "90% CI".
    """
    raw = str((build_options or {}).get("level", "") or "").strip()
    if not raw:
        return float(default)
    try:
        val = float(raw)
    except ValueError:
        warnings.warn(
            f"dash: could not read the confidence level {raw!r}; "
            f"using {default}.", UserWarning, stacklevel=2)
        return float(default)
    if not (0.0 < val < 100.0):
        warnings.warn(
            f"dash: c(level) of {raw} is outside (0, 100); using {default}.",
            UserWarning, stacklevel=2)
        return float(default)
    return val



# ---- Sub-options: honour, or name ------------------------------------------
#
# dash.sthlp: "Nothing is ever dropped without being named."  It held for
# options (the ignoring note) and, since WP-11, for by()'s sub-options; it
# did not hold for the sub-options of legend(), xlabel()/ylabel(),
# xscale()/yscale(), the textbox options, xline()/yline() or filter().
# Measured 22sep2026, every one of those rendered with no warning in either
# mode.  One report, in by()'s words, from code both modes run.

def _dash_report_suboptions(option, tokens, seen=None, key=""):
    """Name the sub-options of *option* dash does not implement.

    Once per graph per render: the figure body runs once per by() panel,
    and *seen* -- a set the caller keeps for the render -- stops the same
    report repeating per panel.  *key* is the graph's name.
    """
    toks = [t for t in tokens if t]
    if not toks:
        return
    if seen is not None:
        mark = (key, option, tuple(toks))
        if mark in seen:
            return
        seen.add(mark)
    warnings.warn(
        "dash: %s() sub-option(s) not implemented and ignored: %s"
        % (option, " ".join(toks)), UserWarning, stacklevel=2)


def _dash_subopt_name(tok):
    """``holes(1)`` -> ``holes``; ``span`` -> ``span``."""
    return tok.split("(", 1)[0].strip().lower()


#: legend() sub-options _dash_apply_legend honours.
_DASH_LEGEND_SUBOPTS = frozenset({
    "on", "off", "position", "pos", "ring", "order", "label", "cols", "rows",
    "size", "top", "bottom", "left", "right"})


def _dash_legend_unsupported(legend_opt):
    """The legend() tokens dash has no reading for, as the user wrote them."""
    return [t for t in _dash_by_tokens(str(legend_opt or "").strip())
            if _dash_subopt_name(t) not in _DASH_LEGEND_SUBOPTS]


#: Textbox sub-options the figure title, the axis titles, the subtitle, the
#: note and the caption honour.
_DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "colour"})


def _dash_textbox(raw, option, seen=None, key=""):
    """``(text, sub-options)`` of a textbox option, the rest named.

    Only a comma followed by a sub-option name Stata's textbox grammar
    knows starts the sub-options (``_textbox_split_point``), so
    ``title("Sales, size matters")`` keeps its comma; a name in that
    grammar that dash does not honour -- ``orientation()``,
    ``justification()``, ``span`` -- is named here rather than dropped.
    """
    text, opts = _parse_textbox_opt(raw or "")
    raw_s = str(raw or "")
    cut = _textbox_split_point(raw_s)
    if cut >= 0:
        tail = raw_s[cut + 1:]
        bad = [t for t in _dash_by_tokens(tail.strip())
               if _dash_subopt_name(t) not in _DASH_TEXTBOX_HONOURED]
        _dash_report_suboptions(option, bad, seen, key)
    return text, opts


def _dash_figure_title(fig, graph_opts, seen=None, key=""):
    """title() sub-options on the Title model: size() and color(), the
    rest named.  The text itself went in when the figure was made.  The
    served app applied none of them; measured, title("T", size(large)
    color(red)) was 15px red saved and 13px grey served."""
    raw = (graph_opts or {}).get("title", "")
    if not raw or fig.title is None:
        return
    _t_text, _t_opts = _dash_textbox(raw, "title", seen, key)
    if not _t_text or not _t_opts:
        return
    if "size" in _t_opts:
        fig.title.text_font_size = f"{_textbox_size(_t_opts, 16.0):g}px"
    if "color" in _t_opts or "colour" in _t_opts:
        fig.title.text_color = _textbox_color(_t_opts, "#000000")


def _dash_style_axis_titles(fig, graph_opts, seen=None, key=""):
    """xtitle()/ytitle() size() and color() on the axis titles; the text
    was set by _dash_axis_labels, which also names the rest."""
    for opt, axes in (("xtitle", fig.xaxis), ("ytitle", fig.yaxis)):
        raw = (graph_opts or {}).get(opt, "")
        if not raw:
            continue
        _, opts = _parse_textbox_opt(raw)
        if not opts:
            continue
        for ax in axes:
            if "size" in opts:
                ax.axis_label_text_font_size = (
                    f"{_textbox_size(opts, 13.0):g}px")
            if "color" in opts or "colour" in opts:
                ax.axis_label_text_color = _textbox_color(opts, "#000000")


#: Where the note, the caption and the subtitle sit, and their defaults.
#: Measured in Stata: the note is ring(4) and the caption ring(5), so the
#: caption sits BELOW the note, and the note is the smaller of the two.
#: add_layout(..., "below") gives each Label a row of its own.  y = 2.0
#: for both: a negative screen offset was clipped and no dashboard ever
#: drew a caption.
_DASH_TEXTBOX_DEFAULTS = {
    "note":     {"size": 11.0, "color": "#555555", "y": 2.0, "side": "below"},
    "caption":  {"size": 12.0, "color": "#555555", "y": 2.0, "side": "below"},
    "subtitle": {"size": 13.0, "color": "#444444", "y": 0.0, "side": "above"},
}


def _dash_text_annotations(fig, graph_opts, seen=None, key="", scheme=None):
    """note(), caption() and subtitle() as Labels, in both modes.

    The generated app carried its own copy of this loop, with its own
    size and colour helpers; one text now, with the unimplemented
    sub-options named.

    With *scheme* given, the defaults are Stata's text boxes: subtitle()
    is the subheading box (``gsize subheading``, ``color subheading``),
    caption() the body box, and note() the small_body box in its own
    colour (``gsize note`` exists in every scheme and Stata's note
    reads nothing from it).  The sizes reach Bokeh as the scheme's own pt
    strings.  ``_DASH_TEXTBOX_DEFAULTS`` were literal px and #555555 under
    every scheme; they remain the defaults for a caller with no scheme.
    An explicit size() or color() sub-option still wins.
    """
    from bokeh.models import Label
    for ann_key in ("note", "caption", "subtitle"):
        raw = (graph_opts or {}).get(ann_key, "")
        if not raw:
            continue
        text, opts = _dash_textbox(raw, ann_key, seen, key)
        if not text:
            continue
        d = _DASH_TEXTBOX_DEFAULTS[ann_key]
        if scheme is not None:
            size_default, color_default = {
                "subtitle": (scheme.subheading_font_size,
                             scheme.subheading_color),
                "caption": (scheme.body_font_size, scheme.body_color),
                "note": (scheme.small_body_font_size, scheme.small_body_color),
            }[ann_key]
        else:
            size_default, color_default = f"{d['size']:g}px", d["color"]
        # None from either helper means "not given, or refused (and
        # named)": the default applies either way.
        px = _textbox_size(opts, None)
        colour = _textbox_color(opts, None)
        fig.add_layout(Label(
            x=0, y=d["y"], x_units="screen", y_units="screen", text=text,
            text_font_size=(f"{px:g}px" if px is not None else size_default),
            text_color=colour if colour is not None else color_default,
        ), d["side"])


#: xscale()/yscale() sub-options dash honours.
_DASH_SCALE_SUBOPTS = frozenset({"log", "reverse", "range"})


def _dash_scale_spec(raw, option="", seen=None, key=""):
    """``{"log", "reverse", "lo", "hi"}`` for an xscale()/yscale() value,
    every other sub-option named.  This used to warn for five tokens
    (noextend, extend, alt, fextend, nofextend) and drop the rest --
    noline, titlegap(), off -- in silence."""
    toks = _dash_by_tokens(str(raw or "").strip())
    names = [_dash_subopt_name(t) for t in toks]
    if option:
        _dash_report_suboptions(
            option, [t for t, n in zip(toks, names)
                     if n not in _DASH_SCALE_SUBOPTS], seen, key)
    lo, hi = _parse_scale_range(raw or "")
    return {"log": "log" in names, "reverse": "reverse" in names,
            "lo": lo, "hi": hi}


def _dash_apply_scale_ranges(fig, xspec, yspec, frame, xvar, yvar):
    """xscale(range())/yscale(range()) as Range1d bounds, then reverse.

    One bound given keeps the data's own value for the other.  The
    generated app read ``xrange``/``yrange`` keys dash.ado never writes,
    so a served range() was dropped; measured, xscale(range(1500 4500))
    bounded the saved axis and left the served one on its data range.
    """
    from bokeh.models import Range1d
    cols = getattr(frame, "columns", [])
    for spec, attr, var in ((xspec, "x_range", xvar), (yspec, "y_range", yvar)):
        lo, hi = spec.get("lo"), spec.get("hi")
        if lo is None and hi is None:
            continue
        cur = getattr(fig, attr)
        cur_lo, cur_hi = getattr(cur, "start", None), getattr(cur, "end", None)
        if lo is None or hi is None:
            if var and var in cols:
                v = pd.to_numeric(frame[var], errors="coerce").dropna()
                if len(v):
                    cur_lo, cur_hi = float(v.min()), float(v.max())
        new_lo = lo if lo is not None else cur_lo
        new_hi = hi if hi is not None else cur_hi
        if new_lo is not None and new_hi is not None:
            setattr(fig, attr, Range1d(float(new_lo), float(new_hi)))
    for spec, attr in ((xspec, "x_range"), (yspec, "y_range")):
        if spec.get("reverse"):
            try:
                getattr(fig, attr).flipped = True
            except AttributeError:
                pass


#: xline()/yline() sub-options dash honours.
_DASH_REFLINE_SUBOPTS = frozenset({"lcolor", "lpattern", "lwidth"})


def _dash_reference_lines(fig, graph_opts, seen=None, key=""):
    """xline()/yline() as Spans, in both modes: a numlist of positions and
    lcolor()/lpattern()/lwidth(); every other sub-option named.

    Stata's measured default is BLACK dashed at the gridline width.  The
    generated app carried its own copy of this; one text now.
    """
    from bokeh.models import Span
    for opt, dim in (("xline", "height"), ("yline", "width")):
        raw = (graph_opts or {}).get(opt, "")
        values, style, bad = [], {}, []
        if not raw:
            # The legacy list form, xline_values/yline_values: positions
            # only, no sub-options.  dash.ado never writes it; the saved
            # renderer has always accepted it.
            for v in (graph_opts or {}).get(opt + "_values", []) or []:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass
            raw = ""
        for tok in _dash_by_tokens(str(raw).replace(",", " ").strip()) if raw else ():
            name = _dash_subopt_name(tok)
            if "(" in tok and name in _DASH_REFLINE_SUBOPTS:
                style[name] = tok[len(name) + 1:-1].strip() if tok.endswith(")") else ""
                continue
            try:
                values.append(float(tok))
            except ValueError:
                bad.append(tok)
        _dash_report_suboptions(opt, bad, seen, key)
        kw = {"line_color": "#000000", "line_dash": "dashed", "line_width": 1.0}
        # An unknown style inside xline()/yline() is named through the one
        # helper, as a plot option's is: lpattern() and lwidth() were
        # dropped in silence, and lcolor() had a wording of its own.
        for sub, what, fn, attr in (
                ("lcolor", "colour", OptionTranslator.translate_mcolor,
                 "line_color"),
                ("lpattern", "line pattern", OptionTranslator.translate_lpattern,
                 "line_dash"),
                ("lwidth", "line width", OptionTranslator.translate_lwidth,
                 "line_width")):
            if style.get(sub):
                try:
                    kw[attr] = fn(style[sub])
                except (ValueError, TypeError):
                    _dash_style_note(f"{opt}({sub})", style[sub], what,
                                     "the default")
        for v in values:
            fig.add_layout(Span(location=v, dimension=dim, **kw))


#: filter() widget types dash builds.
_DASH_FILTER_TYPES = ("dropdown", "range", "slider")
_DASH_FILTER_SUBOPTS = frozenset({"type", "exclude", "label"})
_DASH_VARNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _dash_display(text, limit=80):
    """User text as a warning may echo it: printable characters only, and
    not more than *limit* of them."""
    s = "".join(ch if ch.isprintable() else "?" for ch in str(text))
    return s if len(s) <= limit else s[:limit - 3] + "..."


def _dash_warn_filter_missing(fvar):
    warnings.warn(
        f"dash: filter({_dash_display(fvar)}): the variable is not in the "
        f"data; no widget was built.", UserWarning, stacklevel=2)


def _dash_warn_filter_type(fvar, ftype):
    warnings.warn(
        f"dash: filter({_dash_display(fvar)}, type({_dash_display(ftype)})): "
        f"type() must be one of {', '.join(_DASH_FILTER_TYPES)}; no widget "
        f"was built.", UserWarning, stacklevel=2)


def _dash_parse_filter_raw(raw, warn=True):
    """Parse ``build_options["filter"]`` into widget specs, refusing aloud.

    ``dash.ado`` emits the option as plain text; several filter() groups
    are joined with ``||`` (``;`` in older specs).  Each group is
    ``varname[, type(...) exclude(...) label(...)]`` and becomes
    ``{"varname", "type", "exclude", "label"}``.

    What is refused, and why that is all: the variable name and every
    exclude() name must be Stata names (they become column and registry
    keys); type() must be a widget dash builds.  The label is text -- a
    Bokeh widget title in the saved page and in the served one, and a
    ``repr`` literal in the generated app -- so nothing in it is
    evaluated anywhere.  A pattern here used to refuse a whole group
    whose text contained ``;`` `` ` `` ``$`` ``\\`` ``__`` or the words
    import, eval, exec, open, getattr -- so label("R&D __ spend") made
    the widget vanish with rc 0 and no message, and ``open the door`` did
    the same.  Refusal is now for the three keys above, and it says so.
    """
    if not raw or raw in ('"', ""):
        return []
    result = []
    for part in raw.replace(";", "||").split("||"):
        part = part.strip()
        if not part:
            continue
        fvar = re.split(r"[,\s]", part)[0].strip()
        if not _DASH_VARNAME_RE.match(fvar):
            if warn:
                warnings.warn(
                    f"dash: filter({_dash_display(part)}) refused: "
                    f"{_dash_display(fvar)!r} is not a valid variable name; "
                    f"no widget was built.", UserWarning, stacklevel=2)
            continue
        rest = part[len(fvar):].lstrip()
        if rest.startswith(","):
            rest = rest[1:]
        ftype, excl, flabel, bad, ok = "dropdown", [], "", [], True
        # Sub-options may be comma-separated as well as space-separated
        # (filter(foreign, type(dropdown), exclude(g1)) is the documented
        # form); a comma between them is not part of a token.
        toks = [t.rstrip(",") for t in _dash_by_tokens(rest.strip())]
        for tok in [t for t in toks if t]:
            name = _dash_subopt_name(tok)
            arg = tok[len(name) + 1:-1] if "(" in tok and tok.endswith(")") else ""
            if name == "type" and "(" in tok:
                ftype = arg.strip().lower()
            elif name == "exclude" and "(" in tok:
                excl = arg.split()
                badx = [x for x in excl if not _DASH_VARNAME_RE.match(x)]
                if badx:
                    if warn:
                        warnings.warn(
                            f"dash: filter({_dash_display(part)}) refused: "
                            f"exclude() names {[_dash_display(x) for x in badx]} "
                            f"are not valid names; no widget was built.",
                            UserWarning, stacklevel=2)
                    ok = False
            elif name == "label" and "(" in tok:
                # The optional quotes are Stata's: label("Curb weight") and
                # label(Curb weight) both reach here verbatim.
                flabel = arg.strip().strip('"').strip()
            else:
                bad.append(tok)
        if not ok:
            continue
        if ftype not in _DASH_FILTER_TYPES:
            if warn:
                _dash_warn_filter_type(fvar, ftype)
            continue
        if warn:
            _dash_report_suboptions("filter", bad)
        result.append({"varname": fvar, "type": ftype, "exclude": excl,
                       "label": flabel})
    return result


def _dash_layer_source(g_df, df, xvar, yvar, label_var, gname, linked_names,
                       shared_source, shared_pos, fallback_src,
                       extra_cols=()):
    """Build the ColumnDataSource, and any view, for one ordinary plot layer.

    Written once because the generated server app repeated this step in every
    one of its per-type branches, and the repetition is where the column-list
    defects lived: a branch that forgot ``dict.fromkeys`` crashes on
    ``scatter mpg mpg`` (``g_df[[c, c]]`` is not a legal selection), and one
    that forgot the linked-source case rendered two linked graphs from two
    distinct sources, so a selection in one never appeared in the other.

    Returns ``(source, view)``.  The view is not None only for a linked graph
    carrying its own if()/in() qualifier: such a graph cannot simply be
    pointed at the shared source, because that would draw rows the qualifier
    excluded, so it gets a CDSView over it instead -- which is how the
    standalone renderer has always done it.
    """
    cols = [c for c in [xvar, yvar, label_var] + list(extra_cols)
            if c and c in g_df.columns]
    cols = list(dict.fromkeys(cols))
    # The NaN drop names only the plotted variables.  An extra column
    # carried for the tooltip must not decide which ROWS are drawn:
    # hover(rep78) would otherwise silently delete the five cars whose
    # rep78 is missing.
    _drop_on = [c for c in [xvar, yvar] if c and c in g_df.columns]
    clean = g_df[cols].dropna(subset=_drop_on) if _drop_on else g_df

    view = None
    if gname in linked_names and xvar and yvar:
        csrc = shared_source
        if len(clean) != len(df):
            pos = [shared_pos[_l] for _l in clean.index if _l in shared_pos]
            view = CDSView(filter=IndexFilter(pos))
    elif xvar and yvar:
        csrc = ColumnDataSource(clean)
    elif yvar and yvar in g_df.columns:
        # A univariate layer -- histogram, kdensity -- draws the frame it
        # was GIVEN.  It used to be handed the graph's initial source, built
        # from the whole dataset before any qualifier, so a served
        # `histogram mpg if foreign==1' binned every observation: measured,
        # three bars where the saved dashboard draws two.
        csrc = ColumnDataSource(clean)
    else:
        csrc = fallback_src
    return csrc, view


def _dash_range_source(g_df, y1var, y2var, xvar, label_var, extra_cols=()):
    """Build the ColumnDataSource for one range-plot layer.

    Range layers name their variables ``y1var``/``y2var``/``xvar`` rather than
    ``yvar``/``xvar``, so they cannot use ``_dash_layer_source``.  The NaN
    drop is done HERE, not in the mapper: ``map_rcap`` and ``map_rcapsym``
    read ``source.data[xvar]`` straight into ``np.array(..., dtype=float)``
    with no guard, so a NaN row reaching them is a crash rather than a gap.
    Every inline range branch dropped first, and this keeps that.

    Returns ``(source, ok)``; ``ok`` is False when a required variable is
    missing, in which case the caller draws nothing, as the branches did.
    """
    if not (y1var and y2var and xvar):
        return None, False
    cols = [c for c in [y1var, y2var, xvar, label_var] + list(extra_cols)
            if c and c in g_df.columns]
    cols = list(dict.fromkeys(cols))
    if not all(v in g_df.columns for v in (y1var, y2var, xvar)):
        return None, False
    # Again, an extra tooltip column does not decide which rows survive.
    return ColumnDataSource(
        g_df[cols].dropna(subset=[y1var, y2var, xvar])), True


def _dash_pc_source(g_df, y1var, x1var, y2var, x2var):
    """Build the ColumnDataSource for one paired-coordinate layer.

    All four variables are required; a pc plot with any of them missing draws
    nothing, which is what each inline branch did.  De-duplicated, because
    ``pcspike y x y x`` is a legal command and ``g_df[[c, c, c, c]]`` is not
    a legal selection -- the branch that forgot this crashed the served app.

    Returns ``(source, ok)``.
    """
    if not (y1var and x1var and y2var and x2var):
        return None, False
    names = [y1var, x1var, y2var, x2var]
    if not all(v in g_df.columns for v in names):
        return None, False
    cols = list(dict.fromkeys(names))
    return ColumnDataSource(g_df[cols].dropna()), True


#: Plot types whose legend key Stata writes as "Fitted values" rather than as
#: the y variable.  Measured: ``twoway (scatter mpg weight) (lfit mpg weight)``
#: has keys ["Mileage (mpg)", "Fitted values"].
_DASH_FIT_TYPES = frozenset({
    "lfit", "qfit", "fpfit", "lpoly", "lowess", "mband", "mspline",
    "function",
})

#: Plot types that produce TWO keys from one layer: the band and the line.
#: Measured: ``twoway lfitci mpg weight`` has keys ["95% CI", "Fitted values"].
_DASH_CI_TYPES = frozenset({"lfitci", "qfitci", "lpolyci", "fpfitci"})


#: Statistics of a DATE variable whose RESULT is itself a date, and so is
#: shown as one.  ``dash kpi max(date)`` on sp500 used to read 15340.
_DASH_DATE_VALUED_STATS = frozenset({"mean", "min", "max", "median", "p50",
                                     "p25", "p75"})


def _dash_effective_kpi_fmt(kpi, varname, numeric_formats=None):
    """The format a KPI card is actually displayed with.

    ``fmt()`` if given, else the variable's own Stata display format, else
    Stata's default ``%9.0g`` -- six significant digits.  Written once
    because the generated server app resolved none of these: it passed
    ``kpi['fmt']`` straight through, so a card with no ``fmt()`` printed
    ``round(value, 4)``.
    """
    explicit = str(kpi.get("fmt", "") or "").strip()
    if explicit:
        return explicit
    own = (numeric_formats or {}).get(varname, "") or ""
    if own:
        return own
    return "%9.0g"


def _dash_format_kpi_value(value, fmt_str, varname="", stat="",
                           date_vars=None, date_formatter=None):
    """Format a KPI value the way the saved dashboard formats it.

    The generated app had its own three-line formatter: it matched
    ``%[w].[d][fge]``, ALWAYS comma-grouped an ``f``, ignored the ``c``
    suffix that asks for grouping, had no ``%9.0g`` default and fell back to
    ``round(value, 4)``.  So ``fmt(%12.0fc)`` was identical to ``fmt(%12.0f)``
    when served, and a card with no ``fmt()`` read 21.2973 in one mode and
    21.2973 or 21.29729... in the other depending on the value.

    Args:
        value:          The statistic.
        fmt_str:        A Stata format string, already resolved by
                        ``_dash_effective_kpi_fmt``.
        varname:        The variable the statistic was taken of.
        stat:           The statistic, which decides whether a date variable
                        produces a date.
        date_vars:      ``{varname: "td"|"tc"|...}``.
        date_formatter: ``f(value, kind) -> str`` for a date-valued result.

    Returns:
        The card's text.
    """
    kind = (date_vars or {}).get(varname)
    if (kind and date_formatter is not None
            and str(stat).lower().strip() in _DASH_DATE_VALUED_STATS):
        return date_formatter(float(value), kind)

    try:
        if math.isnan(float(value)):
            return "."
    except (TypeError, ValueError):
        return str(value)

    fmt = str(fmt_str or "").strip()
    if fmt in ("", "%9.0g"):
        # Stata's default display: six significant digits.  The browser-side
        # callback does the same through toPrecision(6), so the card does not
        # change shape when a filter moves.
        return f"{float(value):g}"

    fmt = fmt.lstrip("%")
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
            formatted = (f"{formatted_int}.{parts[1]}"
                         if len(parts) > 1 and parts[1] else formatted_int)
        except (ValueError, IndexError):
            pass

    return formatted.strip()


def _dash_placement_map(layout_opt, valid_names=None):
    """Parse Stata's ``layout(name:row,col ...)`` form to zero-based cells.

    Both the 1-based form ``dash.sthlp`` documents and the 0-based form
    ``dash.ado``'s regex actually admits are accepted, and normalised here.
    A spec is read as 1-based only when no index is 0, since the two are
    otherwise indistinguishable.

    The generated server app had its own parser that required every index to
    be at least 1, so ``layout(g1:0,0 g2:0,1)`` placed both graphs when the
    dashboard was saved and was discarded without a word when it was served
    -- one spec with two meanings.

    Args:
        layout_opt:  The raw ``layout()`` string.
        valid_names: Names that may be placed; others are ignored.  ``None``
                     accepts any name.

    Returns:
        ``{name: (row, col)}``, zero-based; empty when the string is not a
        placement spec.
    """
    if not layout_opt:
        return {}
    pairs = re.findall(r"([A-Za-z_]\w*)\s*:\s*(\d+)\s*,\s*(\d+)",
                       layout_opt.strip())
    if not pairs:
        return {}
    # Anything else in the string means this is not a placement spec.
    leftover = re.sub(r"[A-Za-z_]\w*\s*:\s*\d+\s*,\s*\d+", "",
                      layout_opt).strip()
    if leftover:
        return {}
    raw = {name: (int(r), int(c)) for name, r, c in pairs
           if valid_names is None or name in valid_names}
    if not raw:
        return {}
    one_based = all(r > 0 and c > 0 for r, c in raw.values())
    if one_based:
        return {n: (r - 1, c - 1) for n, (r, c) in raw.items()}
    return raw


def _dash_legend_key(plot, var_labels=None):
    """The legend key Stata writes for one plot layer.

    Stata labels a data series with the variable LABEL, not its name, and a
    computed layer with "Fitted values".  The generated server app wrote the
    y-variable name for EVERY layer, so a served ``lfitci`` was keyed "mpg"
    where the saved dashboard keys it "95% CI" and "Fitted values" -- there
    was no way to tell the band from the points.

    Args:
        plot:       One plot spec.
        var_labels: ``{varname: label}``.

    Returns:
        The key text.
    """
    var_labels = var_labels or {}
    ptype = str(plot.get("type", "")).lower()
    if ptype in _DASH_FIT_TYPES or ptype in _DASH_CI_TYPES:
        return "Fitted values"
    yvar = (plot.get("yvar", "") or plot.get("var", "")
            or plot.get("yvar1", ""))
    return (var_labels.get(yvar, yvar) or ptype) if yvar else ptype


def _dash_legend_entries(plot_renderers, var_labels=None,
                         default_level=None):
    """``[(key_text, [renderer, ...]), ...]`` for one figure's layers.

    Written once because both renderers need Stata's keying rules, and the
    generated app had none of them: a ``lfitci`` band and its line were one
    key named after the y variable.

    Args:
        plot_renderers: ``[(plot_spec, [renderer, ...]), ...]`` in draw order.
        var_labels:     ``{varname: label}``.
        default_level:  The dashboard's ``level()``, for a CI band's key.

    Returns:
        A list of ``(label, renderers)`` pairs, in order.
    """
    out = []
    for plot, rends in plot_renderers:
        rends = [r for r in rends if not _dash_is_swatch(r)]
        if not rends:
            continue
        ptype = str(plot.get("type", "")).lower()
        if ptype in _DASH_CI_TYPES and len(rends) >= 2:
            # The band is added alongside the line; Stata keys them
            # separately, and the band's key carries the level.
            lvl = _resolve_level(plot.get("options", {}) or {},
                                 _DEFAULT_LEVEL if default_level is None
                                 else default_level)
            band = [r for r in rends
                    if type(getattr(r, "glyph", None)).__name__
                    in ("VArea", "Band", "Patch")]
            line = [r for r in rends if r not in band]
            if band:
                out.append((f"{lvl:g}% CI", band))
            if line:
                out.append(("Fitted values", line))
            continue
        out.append((_dash_legend_key(plot, var_labels), rends))
    return out


def _dash_hover_row(col, label, date_kind="", numeric_fmt=""):
    """One tooltip row for column *col*, honouring its Stata display format.

    Returns ``(field, formatter_key_or_None)``.  A date column shows a date
    rather than the underlying number, and a column with a Stata numeric
    format shows the digits that format asks for.
    """
    if date_kind:
        spec = (f"@{{{col}}}{{%F %T}}" if date_kind == "tc"
                else f"@{{{col}}}{{%F}}")
        return (label, spec), f"@{{{col}}}"
    pattern = _stata_numeric_pattern(numeric_fmt) if numeric_fmt else None
    spec = f"@{{{col}}}{{{pattern}}}" if pattern else f"@{{{col}}}"
    return (label, spec), None


def _dash_build_hover(fig, xvar, y1var, y2var, hover_extra,
                      var_labels=None, date_vars=None, numeric_formats=None,
                      univar=""):
    """Give *fig* its one comprehensive HoverTool, in either render mode.

    GAPS.md D2: ``HoverTool`` was imported into the generated app and never
    instantiated.  The only tooltips a served figure had were the ones
    ``map_scatter`` and ``map_line`` add for themselves, so bar, histogram,
    area, every range type and every fit had none at all, and ``hover()``
    was ignored -- while the saved dashboard built a comprehensive tool here
    and listed the extras.

    The saved renderer had its own defect at the same spot: it built the
    comprehensive tool but removed the mappers' tools only when ``hover()``
    was given, so a plain ``dash scatter mpg weight`` carried TWO HoverTools
    with identical tooltips.  Both are fixed by building the tool in one
    place and clearing what came before, unconditionally.

    Which rows appear is decided from the columns the figure's renderers
    actually carry, so the two modes agree without either of them having to
    know how the other builds its sources.  Renderers that carry every
    referenced column get the comprehensive tool; the rest get the generic
    x/y or bin tooltip they can actually answer, rather than a row of
    ``???``.

    Args:
        fig:              The Bokeh figure, with its renderers already added.
        xvar:             The graph's x variable, or "".
        y1var, y2var:     The graph's y variable(s); y2var is the upper
                          boundary of a range plot, or "".
        hover_extra:      Extra variables named by ``hover()``, as a list.
        var_labels:       ``{varname: label}`` for the tooltip's left column.
        date_vars:        ``{varname: "td"|"tc"|...}`` for date formatting.
        numeric_formats:  ``{varname: "%9.0fc"}`` Stata display formats.
        univar:           The single variable of a ``histogram`` or
                          ``kdensity``, whose bins the fallback tooltip
                          names.  Deliberately NOT folded into *y1var*: a
                          kdensity's y column is a density, and calling it
                          ``mpg`` would be wrong rather than merely vague.
    """
    var_labels = var_labels or {}
    date_vars = date_vars or {}
    numeric_formats = numeric_formats or {}

    # Whatever came before -- a mapper's own per-layer tool, or Bokeh's
    # default -- is replaced, not added to.
    fig.tools = [t for t in fig.tools if not isinstance(t, HoverTool)]

    _rends = [r for r in fig.renderers if getattr(r, "data_source", None)
              is not None]
    if not _rends:
        return

    def _cols_of(rend):
        try:
            return set(rend.data_source.data)
        except (AttributeError, TypeError):
            return set()

    _present = set()
    for _r in _rends:
        _present |= _cols_of(_r)

    _wanted, _seen = [], set()
    for _c in [xvar, y1var, y2var] + list(hover_extra or []):
        if _c and _c not in _seen and _c in _present:
            _wanted.append(_c)
            _seen.add(_c)

    _fields, _formatters = [], {}
    for _c in _wanted:
        _row, _fmt_key = _dash_hover_row(
            _c, var_labels.get(_c, _c), date_vars.get(_c, ""),
            numeric_formats.get(_c, ""))
        _fields.append(_row)
        if _fmt_key:
            _formatters[_fmt_key] = "datetime"

    _full, _rest = [], []
    for _r in _rends:
        (_full if _fields and _seen <= _cols_of(_r) else _rest).append(_r)

    if _fields and _full:
        fig.add_tools(HoverTool(tooltips=_fields, formatters=_formatters,
                                renderers=_full))

    # No renderer carries these columns -- a histogram-only figure, a lone
    # fit line, a density curve -- so fall back to a tooltip built from the
    # generic columns those renderers DO carry ("x"/"y", or a bin's
    # "left"/"right"/"top").  Pointing the comprehensive tooltip at them
    # would print "???" on every row.
    #
    # Only when there is no comprehensive tool.  A figure that has one is
    # already answering for its data layers, and adding a second tool for
    # the fit line on top of it is a change to what the saved dashboard
    # draws, which is not this work package's business.
    if not _full and _rest:
        _fb_src = _rest[0].data_source
        _fb_data = getattr(_fb_src, "data", {})
        _fb_fields, _fb_mode = [], "mouse"
        if "top" in _fb_data and "left" in _fb_data:
            # The bin edges ARE the variable's own values, so the row is
            # named after it.  It used to read "value" whenever the plot
            # carried its variable under the `var' key, which is the key
            # dash.ado writes for every histogram.
            _bin_var = y1var or univar
            _bin_label = var_labels.get(_bin_var, _bin_var or "value")
            _p = _tooltip_precision(_fb_data.get("left", []))
            _fb_fields = [
                (_bin_label, f"@{{left}}{{{_p}}} to @{{right}}{{{_p}}}"),
                ("Count", "@{top}"),
            ]
            # Quad hit-testing wants the cursor exactly on the bar; vline
            # fires anywhere within the bin's x-range.
            _fb_mode = "vline"
        elif "x" in _fb_data and "y" in _fb_data:
            _px = _tooltip_precision(_fb_data.get("x", []))
            _py = _tooltip_precision(_fb_data.get("y", []))
            _fb_fields = [
                (var_labels.get(xvar, xvar or "x"), f"@{{x}}{{{_px}}}"),
                (var_labels.get(y1var, y1var or "y"), f"@{{y}}{{{_py}}}"),
            ]
        if _fb_fields:
            fig.add_tools(HoverTool(tooltips=_fb_fields,
                                    renderers=_rest[:1], mode=_fb_mode))


def _dash_qualified_frame(frame, if_expr, in_expr, where="", copy=True):
    """Return the rows of *frame* that an ``if``/``in`` qualifier selects.

    The one place either renderer turns a Stata qualifier into rows.  There
    used to be five: ``_apply_graph_filter`` here, and four hand-written
    copies inside the generated server app (graph, facet, filter callback,
    and none at all for a plot or a KPI, which is how a per-plot ``if`` came
    to be discarded when served).

    ``if_expr`` is translated out of Stata's grammar and then validated
    against ``_validate_if_expr``'s AST whitelist before it reaches
    ``DataFrame.query``.  An expression that fails the whitelist, or that
    ``query`` cannot run, warns and leaves the frame unfiltered: a qualifier
    that cannot be applied must never silently draw the wrong rows, and must
    never lose the layer either.

    Args:
        frame:    The DataFrame to restrict.
        if_expr:  Stata ``if`` expression, or "".
        in_expr:  Stata ``in`` range as ``"N/M"``, or "".
        where:    Short phrase naming the caller, for the warning text.
        copy:     Copy even when no qualifier applies.  The saved renderer
                  has always copied; a per-layer caller does not need to.

    Returns:
        A (possibly smaller) DataFrame.
    """
    _if = (if_expr or "").strip()
    _in = (in_expr or "").strip()
    if not _if and not _in:
        return frame.copy() if copy else frame

    out = frame
    if _in:
        # Stata's `in N/M' is 1-based and inclusive at both ends.
        _m = re.match(r"^(\d+)/(\d+)$", _in)
        if _m:
            _lo = max(0, int(_m.group(1)) - 1)
            _hi = int(_m.group(2))
            out = out.iloc[_lo:_hi]

    if _if:
        # Stata's qualifier idioms -- missing(), inlist(), inrange() and the
        # "< ." missing test -- become plain comparisons BEFORE validation,
        # so the whitelist sees the whole expression.
        pandas_expr = _stata_if_to_pandas(_if.replace("~=", "!="))
        _label = (" " + where) if where else ""
        if not _validate_if_expr(pandas_expr, out.columns):
            warnings.warn(
                f"dash:{_label} if_expr filter skipped -- invalid syntax "
                f"(<unknown>, line 1)",
                stacklevel=2,
            )
        else:
            try:
                out = out.query(pandas_expr, engine="python")
            except (ValueError, SyntaxError, KeyError, TypeError,
                    NameError) as _qexc:
                # NameError (pandas UndefinedVariableError) is raised when a
                # column the qualifier names was never serialised by Stata.
                warnings.warn(
                    f"dash:{_label} if_expr filter skipped -- {_qexc}",
                    stacklevel=2,
                )

    return out.copy() if (copy and out is frame) else out


def _dash_layer_drew_anything(renderers):
    """Did this plot layer put any data on the figure?

    A layer may add a renderer whose source is empty -- that is how a
    rejected ``function`` expression and an unsupported plot type both appear
    -- so the renderer count alone is not the question.

    Module-level because BOTH renderers ask it.  The saved dashboard has
    warned since WP-02 that a layer drew nothing; the served one said
    nothing at all, which is why every one of D2's divergences was silent.

    Args:
        renderers: The renderers this layer added, in order.

    Returns:
        True if any of them carries at least one value.
    """
    if not renderers:
        return False
    for _r in renderers:
        _src = getattr(_r, "data_source", None)
        if _src is None:
            return True          # an annotation, not a data glyph
        try:
            if any(len(_v) for _v in _src.data.values()):
                return True
        except (AttributeError, TypeError):
            return True          # not inspectable: assume it drew
    return False


def _dash_report_empty_layer(gname, index, ptype, rows):
    """Warn that layer *index* of graph *gname* drew nothing from *rows* rows.

    One text, so the two modes cannot word it differently and a test cannot
    pass against one of them.  Reported only when the graph's own data is
    non-empty: an ``if`` qualifier that selects no rows is the user's doing,
    not a broken layer.
    """
    warnings.warn(
        f"dash: graph {gname!r} plot {index} ({ptype}) drew nothing from "
        f"{rows:,} observations.",
        UserWarning, stacklevel=2,
    )


def _dash_glyph_dispatch(mapper):
    """The one mapping from plot-type name to GlyphMapper method.

    Returns ``(dispatch, range_dispatch)``.  Adding a plot type means adding
    a line here and nothing else: both render modes read this table.
    """
    dispatch = {
        "scatter":    mapper.map_scatter,
        "sc":         mapper.map_scatter,
        "line":       mapper.map_line,
        "li":         mapper.map_line,
        "connected":  mapper.map_connected,
        "area":       mapper.map_area,
        "bar":        mapper.map_bar,
        "spike":      mapper.map_spike,
        "lfit":       mapper.map_lfit,
        "qfit":       mapper.map_qfit,
        "lfitci":     mapper.map_lfitci,
        "qfitci":     mapper.map_qfitci,
        "lowess":     mapper.map_lowess,
        "lpoly":      mapper.map_lpoly,
        "lpolyci":    mapper.map_lpolyci,
        "fpfit":      mapper.map_fpfit,
        "fpfitci":    mapper.map_fpfitci,
        "histogram":  mapper.map_histogram,
        "hist":       mapper.map_histogram,
        "kdensity":   mapper.map_kdensity,
        "dot":        mapper.map_dot,
        "dropline":   mapper.map_dropline,
        "tsline":     mapper.map_tsline,
        "mspline":    mapper.map_mspline,
        "mband":      mapper.map_mband,
    }
    range_dispatch = {
        "rarea":      mapper.map_rarea,
        "rbar":       mapper.map_rbar,
        "rspike":     mapper.map_rspike,
        "rcap":       mapper.map_rcap,
        "rline":      mapper.map_rline,
        "rconnected": mapper.map_rconnected,
        "rcapsym":    mapper.map_rcapsym,
        "tsrline":    mapper.map_tsrline,
        "rscatter":   mapper.map_rscatter,
    }
    return dispatch, range_dispatch


def _dash_pc_dispatch(mapper):
    """Plot-type name to GlyphMapper method, for paired-coordinate plots."""
    return {
        "pcspike":   mapper.map_pcspike,
        "pcarrow":   mapper.map_pcarrow,
        "pcbarrow":  mapper.map_pcbarrow,
        "pci":       mapper.map_pci,
        "pcscatter": mapper.map_pcscatter,
    }


def _dash_plot_type_names(mapper=None):
    """Every canonical plot-type name dash draws, derived from the tables.

    The dispatch tables carry aliases (``sc``, ``li``, ``hist``) that
    ``dash.ado`` never writes, because its Mata expander emits the full name
    before a spec is written; an alias maps to a method named for the full
    name, so keeping only the keys whose method carries their own name drops
    the aliases.  The literal types are added from ``_DASH_LITERAL_TYPES``.
    Both renderers and the parity guard read this, so a plot type cannot be
    added to the code without the guard asking for a corpus entry.
    """
    class _Probe:
        def __getattr__(self, name):
            if name.startswith("map_"):
                return name
            raise AttributeError(name)

    probe = mapper if mapper is not None else _Probe()
    std, rng = _dash_glyph_dispatch(probe)
    pc = _dash_pc_dispatch(probe)
    names = set()
    for table in (std, rng, pc):
        for key, fn in table.items():
            method = fn if isinstance(fn, str) else getattr(fn, "__name__", "")
            if method == "map_" + key:
                names.add(key)
    return frozenset(names | _DASH_LITERAL_TYPES)


def _dash_function_args(options):
    """``range()`` and ``n()`` for a twoway function layer.

    Stata's documented defaults: ``range(0 1)`` when ``range()`` is absent,
    and ``n(300)`` -- twoway_function.sthlp, "If range() is not specified,
    range(0 1) is assumed."  The point count is capped so ``n(1e9)`` cannot
    be used to exhaust memory.

    Returns ``((x_lo, x_hi), n_points)``.
    """
    x_lo, x_hi = 0.0, 1.0
    n_pts = 300
    if "range" in options:
        parts = str(options["range"]).split()
        if len(parts) >= 2:
            try:
                x_lo, x_hi = float(parts[0]), float(parts[1])
            except ValueError:
                pass
    if "n" in options:
        try:
            n_pts = max(2, min(int(options["n"]), 10000))
        except ValueError:
            pass
    return (x_lo, x_hi), n_pts


def _dash_add_glyph(mapper, fig, source, plot_type, yvar, xvar, options,
                    y2var="", view=None, color_idx=0):
    """Dispatch one plot layer to the GlyphMapper method that draws it."""
    dispatch, range_dispatch = _dash_glyph_dispatch(mapper)
    pt = (plot_type or "").lower()

    # Guard: skip the glyph if a required variable is missing from the CDS.
    if pt not in _DASH_PC_TYPES and pt != "pci":
        _vars_needed = [v for v in [yvar, xvar, y2var] if v]
        if _vars_needed and not mapper._check_vars(source, *_vars_needed):
            return None

    # Range plots take (fig, source, y1var, y2var, xvar, options).
    rfn = range_dispatch.get(pt)
    if rfn is not None and y2var:
        return rfn(fig, source, yvar, y2var, xvar, options,
                   view=view, color_idx=color_idx)

    fn = dispatch.get(pt)
    if fn is None:
        # Loud, because silence here is how 38 plot types came to be missing
        # from one render mode without anything noticing.
        warnings.warn(
            "dash: no glyph mapper for plot type %r; nothing was drawn for "
            "that layer." % (plot_type,),
            UserWarning,
            stacklevel=2,
        )
        return None

    # histogram and kdensity are univariate -- no xvar positional argument.
    if pt in _DASH_UNIVARIATE_TYPES:
        return fn(fig, source, yvar, options, view=view, color_idx=color_idx)
    return fn(fig, source, yvar, xvar, options, view=view, color_idx=color_idx)


def _dash_add_pc_glyph(mapper, fig, source, plot_type, y1var, x1var, y2var,
                       x2var, options, view=None, color_idx=0):
    """Dispatch one paired-coordinate layer to its GlyphMapper method."""
    fn = _dash_pc_dispatch(mapper).get((plot_type or "").lower())
    if fn is None:
        warnings.warn(
            "dash: no glyph mapper for paired-coordinate plot type %r; "
            "nothing was drawn for that layer." % (plot_type,),
            UserWarning,
            stacklevel=2,
        )
        return None
    _pc_needed = [v for v in [y1var, x1var, y2var, x2var] if v]
    if _pc_needed and not mapper._check_vars(source, *_pc_needed):
        return None
    return fn(fig, source, y1var, x1var, y2var, x2var, options,
              view=view, color_idx=color_idx)


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
    _OPT_VAR_KEYS: "tuple[str, ...]" = _DASH_OPT_VAR_KEYS

    @staticmethod
    def _collect_plot_vars(plots_list: list) -> list:
        """Return deduplicated list of all variable columns needed by plots."""
        seen: list[str] = []
        for plot in plots_list:
            for key in DashRenderer._VAR_KEYS:
                v = plot.get(key)
                if v and v not in seen:
                    seen.append(v)
            for v in _dash_option_columns(plot.get("options", {})):
                if v not in seen:
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
        self.default_level: float = _dash_session_level(_build_opts)

        _scheme_name: str = _resolve_scheme_name(self.master_spec)
        self.scheme: SchemeParser = SchemeParser.resolve_or_fallback(
            _scheme_name, "the dashboard",
        )

        self.mapper = GlyphMapper(scheme=self.scheme,
                                  default_level=self.default_level)

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
        _dash_attach_labels(self.mapper, self.variable_labels,
                            self.value_labels, self.value_label_names,
                            getattr(self, "date_vars", {}),
                            getattr(self, "numeric_formats", {}))

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
    # The module-level set, so the generated server app applies the same
    # rule.  Kept here because callers and tests name it on the class.
    _DATE_VALUED_STATS = _DASH_DATE_VALUED_STATS

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
        return _dash_effective_kpi_fmt(
            kpi, varname, getattr(self, "numeric_formats", {}))

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
        return _dash_format_kpi_value(
            value, fmt_str, varname, stat,
            date_vars=getattr(self, "date_vars", {}),
            date_formatter=self._format_date_value,
        )

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
        return _dash_qualified_frame(self.df, graph_spec.get("if_expr", ""),
                                     graph_spec.get("in_expr", ""))

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
        varlist, by_cols, by_total, by_missing, _unsup = _dash_parse_by(by_raw)
        return varlist, by_cols, by_total, by_missing

    @staticmethod
    def _parse_filter_raw(raw: str) -> "list[dict]":
        """Parse ``build_options["filter"]``; see ``_dash_parse_filter_raw``,
        the one parser both render modes run."""
        return _dash_parse_filter_raw(raw)

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

        # One parser for both render modes; it rejects injection patterns
        # by returning an empty varlist, and names the sub-options dash
        # does not implement.
        varlist, by_cols_parsed, by_total_parsed, by_missing_parsed, _ = \
            _dash_parse_by(by_raw)

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
        return _dash_facet_label(
            by_vars, key, self.value_label_names, self.value_labels,
            getattr(self, "date_vars", {}),
            getattr(self, "numeric_formats", {}),
            self._format_date_value)

    # ------------------------------------------------------------------
    # Figure construction helpers
    # ------------------------------------------------------------------

    # The module-level sets, so the generated server app keys its legend the
    # same way.  Kept as class attributes because callers and tests name
    # them here.
    _FIT_TYPES = _DASH_FIT_TYPES
    _CI_TYPES = _DASH_CI_TYPES

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
        return _dash_legend_key(plot, getattr(self, "variable_labels", {}))

    def _rebuild_legend(self, fig, plot_renderers: list, graph_opts: dict
                        ) -> None:
        """Stata's legend keys, Stata's rule for drawing one, and every
        legend() sub-option -- through ``_dash_apply_legend``, which the
        generated server app runs as well."""
        _dash_apply_legend(
            fig, plot_renderers, graph_opts.get("legend", ""),
            getattr(self, "variable_labels", {}),
            getattr(self, "default_level", _DEFAULT_LEVEL),
            _dash_scheme_chrome(self.scheme),
            getattr(self, "_reported_subopts", None),
            graph_opts.get("name", ""))

    @staticmethod
    def _move_legend(fig, legend, side: str) -> None:
        """Move an existing Legend into a side panel; see _dash_move_legend."""
        _dash_move_legend(fig, legend, side)

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
        # The options, through the helper the generated app runs as well.
        sx = getattr(self.scheme, "graphsize_x", None)
        sy = getattr(self.scheme, "graphsize_y", None)
        ar = _dash_figure_aspect(graph_opts, sx, sy)
        if ar is not None:
            return ar
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
        """Parse Stata's full ``axis_label`` grammar; see
        ``_dash_parse_axis_spec``, which both render modes run."""
        return _dash_parse_axis_spec(raw)

    @staticmethod
    def _parse_axis_label_opt(raw: str) -> "tuple[list[float], dict[str, str]]":
        """Parse the numlist form of xlabel()/ylabel(); see
        ``_dash_parse_axis_label_opt``."""
        return _dash_parse_axis_label_opt(raw)

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

        # xtitle()/ytitle() first, else Stata's own default, through the
        # helper the generated app runs as well.  Canvas text, NOT html:
        # Bokeh draws a figure title and axis labels as glyphs, so escaping
        # made title("R&D spend") display as "R&amp;D spend".
        _seen = getattr(self, "_reported_subopts", None)
        _gkey = graph_opts.get("name", "")
        x_label, y_label = _dash_axis_labels(plots, graph_opts,
                                             self.variable_labels, _seen, _gkey)

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
        _xsc = _dash_scale_spec(graph_opts.get("xscale", ""), "xscale",
                                _seen, _gkey)
        _ysc = _dash_scale_spec(graph_opts.get("yscale", ""), "yscale",
                                _seen, _gkey)
        _xs_log, _xs_rev = _xsc["log"], _xsc["reverse"]
        _ys_log, _ys_rev = _ysc["log"], _ysc["reverse"]

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

        # Tick formatting matched to the date kind: years for %ty, dates for
        # %td/%tw/%tm/%tq/%th, date and time for %tc/%tC.  An explicit
        # xlabel()/ylabel() tick list still wins -- it is applied later.
        for _axis, _kind in ((fig.xaxis, _x_date), (fig.yaxis, _y_date)):
            if _kind:
                _axis.formatter = _datetime_formatter_for(_kind)

        # Apply scheme defaults (before explicit graph options so they take precedence)
        self.scheme.apply_to_figure(fig)
        # title(), xtitle()/ytitle() sub-options, after the scheme so the
        # user's size() and color() win; the rest named.
        _dash_figure_title(fig, graph_opts, _seen, _gkey)
        _dash_style_axis_titles(fig, graph_opts, _seen, _gkey)

        # Figure background colors
        # bgcolor  → border_fill_color  (outer area around the plot)
        # plotbgcolor → background_fill_color (inner plot canvas)
        # Every colour through _dash_graph_color, the helper the generated
        # app runs as well: an unknown name is named, and the scheme's
        # chrome kept.  Each of these was an `except ...: pass'.
        raw_bgcolor = graph_opts.get("bgcolor", "")
        if raw_bgcolor:
            _c = _dash_graph_color("bgcolor", raw_bgcolor)
            if _c:
                fig.border_fill_color = _c

        raw_plotbgcolor = graph_opts.get("plotbgcolor", "")
        if raw_plotbgcolor:
            _c = _dash_graph_color("plotbgcolor", raw_plotbgcolor)
            if _c:
                fig.background_fill_color = _c

        # plotregion() — inner plot canvas background/border
        # Accepts sub-options: color(X)/fcolor(X) → background_fill_color
        #                      lcolor(X)           → outline_line_color
        #                      lwidth(X)           → outline_line_width
        raw_plotregion = graph_opts.get("plotregion", "")
        if raw_plotregion:
            _pr_bg = _extract_region_color(raw_plotregion)
            if _pr_bg:
                _c = _dash_graph_color("plotregion(color)", _pr_bg)
                if _c:
                    fig.background_fill_color = _c
            _pr_lc = _extract_region_lcolor(raw_plotregion)
            if _pr_lc:
                _c = _dash_graph_color("plotregion(lcolor)", _pr_lc)
                if _c:
                    fig.outline_line_color = _c
            _pr_lw = _extract_region_lwidth(raw_plotregion)
            if _pr_lw is not None:
                fig.outline_line_width = _pr_lw

        # graphregion() — outer graph border / margin area background
        # Accepts sub-options: color(X)/fcolor(X) → border_fill_color
        raw_graphregion = graph_opts.get("graphregion", "")
        if raw_graphregion:
            _gr_bg = _extract_region_color(raw_graphregion)
            if _gr_bg:
                _c = _dash_graph_color("graphregion(color)", _gr_bg)
                if _c:
                    fig.border_fill_color = _c

        # Secondary axes (yaxis(2) / xaxis(2)), through the helper the
        # generated app runs as well -- it used to build no second axis.
        # From the ACTIVE view, not self.df: a graph-level if/in qualifier
        # already narrowed the source, so a right-hand axis computed from
        # the full frame spanned data the graph does not show.
        _has_y2, _has_x2 = _dash_add_secondary_axes(
            fig, plots, graph_opts, _source_frame(source, self.df))

        # xscale(range())/yscale(range()) and reverse, through the helper
        # the generated app runs as well: it read xrange/yrange keys
        # dash.ado never writes, so a served range() was dropped.
        _dash_apply_scale_ranges(fig, _xsc, _ysc, _source_frame(source, self.df),
                                 xvar, yvar)

        # xline()/yline(), through the helper the generated app runs as well.
        _dash_reference_lines(fig, graph_opts, _seen, _gkey)

        # note(), caption(), subtitle(), through the helper the generated
        # app runs as well, at the scheme's text-box sizes and colours.
        _dash_text_annotations(fig, graph_opts, _seen, _gkey, self.scheme)

        # xlabel()/ylabel(), xtick()/ytick(): Stata's full grammar, through
        # the helper the generated app runs as well.  Its own parser read a
        # bare numlist and angle() and nothing else.
        _dash_apply_axis_options(fig, graph_opts, xvar, yvar,
                                 _source_frame(source, self.df),
                                 getattr(self, "numeric_formats", {}),
                                 _seen, _gkey,
                                 grid_color=self.scheme.grid_color)

        # Plot categories that use non-standard JSON variable keys.  Defined
        # at module level so the generated server app shares them rather than
        # carrying its own copy, which is how the two drifted before.
        _RANGE_TYPES = _DASH_RANGE_TYPES
        _UNIVARIATE_TYPES = _DASH_UNIVARIATE_TYPES
        _PC_TYPES = _DASH_PC_TYPES

        # Add glyphs for each plot layer
        for pi, plot in enumerate(plots):
            ptype = plot.get("type", "scatter")
            pxvar = plot.get("xvar", xvar)
            popts = plot.get("options", {})

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

            # Snapshot renderer list so new glyphs can be identified
            _r_before = len(fig.renderers)
            if pi == 0:
                _plot_renderers: list = []

            if ptype.lower() == "scatteri":
                # Inline coordinate list — no shared source variable needed
                self.mapper.map_scatteri(fig, plot.get("values", []), popts, color_idx=pi)
            elif ptype.lower() == "pci":
                # Also an inline coordinate list: `pci 20 3000 30 4000' is
                # written as [[20,3000],[30,4000]], (y, x) pairs taken two at
                # a time.  map_pci delegated to map_pcspike, which wants
                # variable names, so nothing was ever drawn.
                self.mapper.map_pci_literal(fig, plot.get("values", []),
                                            popts, color_idx=pi)
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
                _fn_range, _fn_n = _dash_function_args(popts)
                self.mapper.map_function(fig, pexpr, _fn_range, _fn_n, popts)
            else:
                pyvar = plot.get("yvar", yvar)
                self._add_glyph(fig, source_for_plot, ptype, pyvar, pxvar, popts,
                                view=_plot_view, color_idx=pi)

            _layer_renderers = list(fig.renderers[_r_before:])
            _plot_renderers.append((plot, _layer_renderers))

            # A layer that drew nothing used to say nothing: `pci' and
            # `pcscatter' each produced a titled, axed, empty plot region
            # with rc 0, and the conformance corpus could not see it because
            # every probe in it appends name(), which registers the spec and
            # never renders one.
            #
            # Reported only when the graph's own data is non-empty: an `if'
            # qualifier that selects no rows is the user's doing, not a
            # broken layer, and the optional-package smoothers (lowess,
            # mspline) already name the package they are missing.
            try:
                _rows_here = len(source_for_plot.data.get(
                    next(iter(source_for_plot.data), ""), []))
            except (AttributeError, TypeError, StopIteration):
                _rows_here = 0
            if _rows_here and not self._layer_drew_anything(_layer_renderers):
                _dash_report_empty_layer(
                    graph_opts.get("name", "") or graph_spec.get("name", "?"),
                    pi + 1, ptype, _rows_here)

            # A yaxis(2)/xaxis(2) layer draws on the secondary range.
            _dash_assign_axis_ranges(fig, _layer_renderers, popts)

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

        # ---- The figure's one HoverTool ----
        # Built by _dash_build_hover, which the generated server app runs
        # too.  This used to be a hundred lines here and NOTHING there --
        # HoverTool was imported into the app and never instantiated -- so
        # a served bar, histogram, area, range plot or fit had no tooltip
        # at all and hover() was ignored.  The saved dashboard had its own
        # defect at the same spot: it cleared the mappers' own tools only
        # when hover() was given, so a plain scatter carried two identical
        # HoverTools.
        _hover_extra_str = graph_opts.get("hover", "").strip()
        _p0 = plots[0] if plots else {}
        _dash_build_hover(
            fig, xvar,
            yvar or _p0.get("yvar1", ""),
            _p0.get("yvar2", ""),
            _hover_extra_str.split() if _hover_extra_str else [],
            var_labels=getattr(self, "variable_labels", {}),
            date_vars=getattr(self, "date_vars", {}),
            numeric_formats=getattr(self, "numeric_formats", {}),
            univar=_p0.get("var", ""),
        )

        return fig

    @staticmethod
    def _layer_drew_anything(renderers: list) -> bool:
        """Did this plot layer put any data on the figure?

        Kept as a method because callers and tests name it, but the answer
        comes from the module-level ``_dash_layer_drew_anything`` that the
        generated server app runs too -- one implementation, so a layer that
        is reported empty when saved is reported empty when served.

        Args:
            renderers: The renderers this layer added, in order.

        Returns:
            True if any of them carries at least one value.
        """
        return _dash_layer_drew_anything(renderers)

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
        _dash_add_glyph(self.mapper, fig, source, plot_type, yvar, xvar,
                        options, y2var=y2var, view=view, color_idx=color_idx)

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
        _dash_add_pc_glyph(self.mapper, fig, source, plot_type, y1var, x1var,
                           y2var, x2var, options, view=view,
                           color_idx=color_idx)

    # ------------------------------------------------------------------
    # KPI card construction
    # ------------------------------------------------------------------

    def _make_kpi_div(self, kpi_def: dict) -> Div:
        """Build a styled KPI Div widget from a KPI definition dict.

        Args:
            kpi_def: Dict with keys: title, value, fmt, subtitle, color,
                     bgcolor, update.

        Returns:
            A Bokeh Div carrying the card (``_dash_kpi_card_html``, the
            builder the served app runs as well) and the scheme's CSS as
            an InlineStyleSheet, so the ``.db-kpi-card`` rule reaches the
            Div's shadow root.
        """
        html_content = _dash_kpi_card_html(
            kpi_def.get("title", ""), str(kpi_def.get("value", "")),
            kpi_def.get("subtitle", ""), kpi_def.get("color", ""),
            kpi_def.get("bgcolor", ""), kpi_def.get("name", "kpi"),
            self.scheme)
        return Div(text=html_content, sizing_mode="stretch_width",
                   stylesheets=[InlineStyleSheet(css=self.scheme.css_block())])

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

    @staticmethod
    def _head_of_file_html(page: str) -> str:
        """The contents of the ``<head>`` of a ``file_html`` page.

        This was ``re.search(r"(?s)<head>(.*?)</head>", page)``.  Bokeh
        3.9's inlined bokeh-widgets.min.js contains the literal string
        ``<head></head>`` (DOMPurify's parser setup), so the non-greedy
        match stopped 189,588 characters into a 378,283-character bundle:
        the widgets script was never closed, dash's own ``</head><body>
        <script>`` landed inside it, and every layout(bs) page whose
        document needs that bundle -- a KPI Div, a filter widget -- was a
        blank page with ``Uncaught SyntaxError`` in the console.  The
        checked-in sample pages were made with a bundle that lacked the
        string, so no test noticed.

        The real ``</head>`` is the LAST one before the page's ``<body``:
        ``file_html`` puts every bundle in the head and HTML-escapes the
        document JSON it writes into the body, so nothing after the real
        head can contain either tag.  When the page has no recognisable
        head at all, the full INLINE bundle is returned rather than an
        empty string, so the page can never come out without its scripts.

        Args:
            page: What ``file_html(..., INLINE)`` returned.

        Returns:
            The text between ``<head>`` and its closing tag.
        """
        start = page.find("<head>")
        body_at = page.rfind("<body")
        end = page.rfind("</head>", 0, body_at if body_at >= 0 else None)
        if start < 0 or end < 0 or end < start:
            return INLINE.render_css() + "\n" + INLINE.render_js()
        return page[start + len("<head>"):end]

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
                _kk = _dash_kpi_keys(name, self.kpi_divs)
                if _kk:
                    # A KPI registered under one name may own several
                    # per-facet cards; they travel as one column.
                    all_models.append(
                        self.kpi_divs[_kk[0]] if len(_kk) == 1 else
                        column(*[self.kpi_divs[k] for k in _kk],
                               sizing_mode="stretch_width"))
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
        _extracted_head = self._head_of_file_html(_dummy_html)

        # ---- Get individual Bokeh component divs ----
        script_tag, div_list = components(all_models)
        name_to_div: dict[str, str] = dict(zip(model_keys, div_list))

        # No graph may vanish from a dashboard without an error.
        self._assert_every_graph_was_placed(_placed_figs)

        # ---- Build common HTML sections ----
        _t_frag, _s_frag = _dash_header_fragments(title_text, subtitle_text)
        header_html = ((_t_frag + "\n") if _t_frag else "") + \
            ((_s_frag + "\n") if _s_frag else "")

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

        if filter_position == "left" and filter_row_widgets:
            # Vertical sidebar: filters in a narrow left column, content on right
            sidebar_items_html = "\n".join(
                f'<div class="db-sidebar-item">{d}</div>'
                for d in fw_divs
                if d
            )
            # Tabs BEFORE the grid: dash.sthlp says an item that tabs()
            # does not name is "still drawn, below the tabs", which is what
            # the plain-grid and server layouts do.  Only this one drew the
            # unassigned items above them -- one sentence, two behaviours.
            page_body_html = (
                '<div class="db-row">\n'
                '  <div class="db-col-12 db-col-sm-12 db-col-md-2 db-sidebar-col">\n'
                '    <div class="db-sidebar-label">Filters</div>\n'
                f"    {sidebar_items_html}\n"
                "  </div>\n"
                '  <div class="db-col-12 db-col-sm-12 db-col-md-10">\n'
                f"    {header_html}"
                f"    {tabs_section_html}\n"
                f"    {grid_section_html}\n"
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
                f"{tabs_section_html}\n"
                f"{grid_section_html}\n"
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
        """Parse a ``tabs()`` option string; see ``_dash_parse_tabs``, the
        one parser both render modes run."""
        return _dash_parse_tabs(tabs_str, all_names)

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

        Through ``_dash_tab_panels`` and ``_dash_layout_cell``, which the
        generated app runs as well and which the plain grid uses for its
        cells -- so a faceted graph inside a tab is laid out exactly as it
        is in the grid, in a sub-grid that honours by(, cols(#)).  This
        used to flatten the panels into the tab's own grid, ignoring
        cols(), while the served app nested them.

        Returns:
            A ``(Tabs, placed_names, placed_keys)`` triple.  *placed_names*
            are the REGISTERED names consumed; *placed_keys* the FIGURE
            KEYS, which a faceted graph has several of.
        """
        _graphs = self.master_spec.get("graphs", [])

        def _gopts_of(name):
            return next((g.get("graph_options", {}) for g in _graphs
                         if g.get("graph_options", {}).get("name") == name),
                        {})

        def _cell_of(name):
            return _dash_layout_cell(name, self.figures, self._facet_map,
                                     self.kpi_divs, _gopts_of)

        tabs_widget, placed = _dash_tab_panels(tabs_spec, _cell_of)
        placed_keys: set[str] = set()
        for name in placed:
            placed_keys.update(self._resolve_layout_names(name))
            placed_keys.update(_dash_kpi_keys(name, self.kpi_divs))
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
        return _dash_placement_map(layout_opt)

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
                        # Silent: _expand_by_groups reports the sub-options.
                        varlist_lnk = _dash_parse_by(by_raw_lnk, warn=False)[0]
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
                        # The QUALIFIED frame.  This was self.df, so a linked
                        # `if price > 4500, by(foreign)' faceted every row.
                        by_groups_lnk = self._expand_by_groups(
                            g, base_df=self._apply_graph_filter(g))
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
                # The QUALIFIED frame, not self.df.  Measured on ten rows:
                # `if price > 4500, by(foreign)' faceted 5 + 4 observations
                # when saved and the 2 + 3 that qualify when served.  The
                # base source built in phase 2 was already qualified; the
                # grouping simply did not start from it.
                by_groups = self._expand_by_groups(
                    g, base_df=self._apply_graph_filter(g))
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
        _kpi_text_color = _sanitize_css_color(
            getattr(self.scheme, "text_color", "") or "#000000", "#000000")
        return {
            "name": kname,
            # The value div's id, as _dash_kpi_card_html escapes it, so the
            # JS rebuild can emit the same `id="kpi_val_<name>"'.
            "name_html": html.escape(kname or "kpi"),
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
            # injection.  The SAME resolver and the SAME defaults as the
            # initial render (_dash_kpi_card_html): the value falls back to
            # the scheme's `color text', and an absent bgcolor() is '' so
            # the rebuild writes no background and the class rule applies.
            "text_color": _kpi_text_color,
            "color": _resolve_kpi_color(kdef.get("color", "") or "",
                                        _kpi_text_color, "color"),
            "bgcolor": _resolve_kpi_color(kdef.get("bgcolor", "") or "",
                                          "", "bgcolor"),
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
                _dash_warn_filter_missing(fvar)
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
                    column=self.df[fvar] if fvar in self.df.columns else None,
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
                    column=self.df[fvar] if fvar in self.df.columns else None,
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
                    column=self.df[fvar] if fvar in self.df.columns else None,
                )
            else:
                _dash_warn_filter_type(fvar, ftype)
                continue

            filter_row_widgets.append(widget)
            self.filter_widgets.append(widget)
            self.filter_callbacks.append(cb)
            built_filter_specs.append(fc)  # record only successfully-built specs

        # Wire multi-filter state into every callback.
        # Each callback gets orig_source, all_widgets, filter_specs_json,
        # kpi_config_json, kpi_divs, agg_sources, agg_configs_json so it can
        # re-apply all active filter conditions on every widget change.
        # The unfiltered data every callback reads, held in ONE
        # ColumnDataSource rather than serialised into each callback's args.
        #
        # This used to be `json.dumps(_orig_data)' computed inside the
        # per-callback loop below, so Bokeh wrote a full copy of the dataset
        # into the document for every filter widget -- and because each
        # filter also adds a column to every copy, the growth was quadratic
        # in the filter count. Measured on 8,000 rows x 6 columns: 1.63 MB
        # with no filters, 11.47 MB with five. Bokeh serialises a model once
        # and refers to it by id, so a shared source appears once.
        _orig_data: dict = {}
        if fsource is not None:
            # The WHOLE frame, not the first graph's source.  Under by()
            # that source is one facet and under a graph-level `if' it is
            # the qualified rows; the widgets' categories and bounds and the
            # KPI recompute all read this snapshot.  Measured: by(foreign)
            # left it with five of ten rows.  Every source is masked by row
            # identity against it, so the full frame is what the masking
            # expects.
            for _col in self.df.columns:
                _orig_data[str(_col)] = [DashRenderer._to_serialisable(v)
                                         for v in self.df[_col]]
            _orig_data[_ROW_ID_COLUMN] = list(self._row_ids_for(self.df))
        _orig_snapshot = ColumnDataSource(_orig_data)

        # One snapshot model per graph source, shared by every callback that
        # is not excluding that graph.
        _snapshot_of: "dict[int, ColumnDataSource]" = {}
        for _gsrc in self.sources.values():
            if id(_gsrc) in _snapshot_of:
                continue
            _snapshot_of[id(_gsrc)] = ColumnDataSource({
                _col: [DashRenderer._to_serialisable(v) for v in _arr]
                for _col, _arr in _gsrc.data.items()
            })

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

            _cb.args["orig_source"]       = _orig_snapshot
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
            _cb.args["all_graph_sources_orig"] = [
                _snapshot_of[id(_gsrc)] for _gsrc in _graph_srcs_for_cb
            ]

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
            # A Bootstrap page embeds its components one by one; there is
            # no single Bokeh layout root, which the parity guard records
            # as a legitimate difference.
            self._last_layout_root = None
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

        def _gopts_of(name):
            return next((g.get("graph_options", {}) for g in graphs
                         if g.get("graph_options", {}).get("name") == name),
                        {})

        # One cell per registered name, through the resolver the tab
        # panels and the generated app use as well.
        cells: list[Any] = [
            _dash_layout_cell(name, self.figures, self._facet_map,
                              self.kpi_divs, _gopts_of)
            for name in _grid_names
        ]

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
            # The same two classed Divs the generated app builds, with the
            # scheme's CSS attached to them: the served page has no head
            # to splice a stylesheet into, and a Bokeh 3 Div renders inside
            # a shadow root anyway.
            layout_root = column(
                *_dash_header_models(title_text, subtitle_text,
                                     self.scheme.css_block()),
                layout_root, sizing_mode="stretch_width")

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

        _report_dataset_size(self.df, "dashboard")
        # Sub-option reports already made this render, so a by() panel does
        # not repeat its graph's.
        self._reported_subopts = set()
        # Likewise the style notes: one per (option, value) per render.
        _dash_reset_notes()

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
                # Silent: _expand_by_groups reports the sub-options.
                varlist = _dash_parse_by(by_raw, warn=False)[0]
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
        # The registry, as typed.  This put every KPI first whatever the
        # registry said -- a Bootstrap hero-row policy that had leaked into
        # every layout -- so the same spec placed a card above its graph
        # when saved and below it when served.
        all_names: list[str] = _dash_layout_order(
            build.get("registry", ""), graphs, kpis)
        kpi_names: list[str] = [n for n in all_names
                                if _dash_kpi_keys(n, self.kpi_divs)]

        # Every registered graph must have become a figure. A graph that is
        # dropped between the registry and the dashboard leaves no trace at
        # all -- the file is written, rc is 0, and the user counts the
        # panels to find out. This is the third of the three assertions
        # test_conformance.cscript makes across the corpus.
        _want = {str(_g.get("graph_options", {}).get("name", "")
                     or _g.get("name", "") or "")
                 for _g in graphs}
        _want.discard("")
        # A by() graph becomes one figure per facet panel, keyed by facet,
        # and _facet_map records the owner. Those are present, not dropped.
        _built = set(self.figures) | set(getattr(self, "_facet_map", {}))
        _missing = sorted(_want - _built)
        if _missing:
            warnings.warn(
                f"dash: {len(_missing)} registered graph(s) did not reach "
                f"the dashboard: {', '.join(_missing)}.",
                UserWarning, stacklevel=2,
            )

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
        # The requested name is kept as well as the resolved one.  When
        # resolution falls back, `self.scheme.name' is the literal "s2color"
        # (SchemeParser.fallback sets it), so a message built from it would
        # tell the user they got what they asked for.  Only this string can
        # name what they did NOT get.
        self.scheme_requested: str = _resolve_scheme_name(self.spec)
        self.scheme: SchemeParser = SchemeParser.resolve_or_fallback(
            self.scheme_requested, "the dashboard",
        )

    def _glyph_layer_lines(self) -> "list[str]":
        """Emit the renderer's own glyph layer into the app, verbatim.

        S15-03. The generated app used to carry 46 hand-written ``ptype``
        branches that re-implemented what ``GlyphMapper``'s 39 ``map_*``
        methods already do. They drifted, repeatedly and silently: served
        scatters at alpha 0.7 where the scheme says 0.8, areas at 0.4 against
        1.0, bars outlined white, a served ``lpolyci`` that drew no band at
        all. Each was found by measurement after the fact.

        So the app gets ONE implementation -- this one, copied by
        ``inspect.getsource`` as the statistical helpers already are -- and
        the branches call into it.

        The app stays self-contained, which ``dash.sthlp`` promises in three
        places: nothing is imported from the package, the classes are written
        into the file, and the scheme arrives as a property dict rather than
        as a ``.scheme`` file the app would have to find on disk.

        Returns:
            The lines to write, in dependency order.
        """
        import inspect as _inspect
        import sys as _sys
        import textwrap as _textwrap

        _mod = _sys.modules[__name__]
        out: "list[str]" = [
            "",
            "# ---- The glyph layer, copied verbatim from dash_render.py ----",
            "#",
            "# inspect.getsource, not a transcription: the standalone renderer",
            "# and this file run the SAME map_* methods, so a change to one",
            "# cannot land without the other. S15-03.",
            "",
            "# SchemeParser resolves its bundled schemes/ directory relative",
            "# to __file__. This app is normally imported, and __file__ is",
            "# then set -- but it is also exec()'d, by tests and by anything",
            "# that reads the source and runs it, and there __file__ does not",
            "# exist and the class body raises on definition. The scheme",
            "# arrives below as a property dict, so the directory is never",
            "# read; this only lets the class be defined.",
            "if '__file__' not in globals():",
            "    __file__ = '<dash server app>'",
            "",
        ]

        # Constants these classes reference that are not already written out
        # by _shared_stat_lines and are not modules the app imports.
        _already = set(self._shared_stat_lines())
        for _name in ("_TEXTBOX_SUBOPT_RE",
                      "_COLORVAR_LEGEND_NAME", "_KDE_BANDWIDTH_RULE",
                      "_LPOLY_ROT_C", "_FP_GRID_MAX", "_MAX_MBANDS",
                      "_MIN_BAR_WIDTH", "_MAX_EXPR_CHARS", "_CI_BAND_ALPHA",
                      # _IF_EXPR_ALLOWED_NODES is deliberately absent: it is
                      # a frozenset of AST CLASSES, and repr() of a class is
                      # not source. It is written out by name below.
                      "_IF_EXPR_SAFE_NAMES",
                      # _dash_legend_entries' own type tables.
                      "_DASH_FIT_TYPES", "_DASH_CI_TYPES",
                      "_DASH_DATE_VALUED_STATS",
                      # _dash_parse_by's own tables; the regex is written
                      # out as re.compile(pattern, flags) below.
                      "_DASH_UNSAFE_BY", "_DASH_BY_SUPPORTED",
                      "_NONSELECTION_ALPHA", "_ROW_ID_COLUMN",
                      # The plot-type categories.  The app used to carry its
                      # own copies inside an if/elif chain, which is how the
                      # two modes came to disagree about which types exist.
                      "_DASH_RANGE_TYPES", "_DASH_UNIVARIATE_TYPES",
                      "_DASH_PC_TYPES", "_DASH_LITERAL_TYPES",
                      # The shared legend, axis, column and swatch tables.
                      "_DASH_CLOCK_SIDE", "_DASH_CLOCK_INSIDE",
                      "_DASH_LEGEND_KEYWORD_LOC", "_DASH_HIST_YTITLES",
                      "_DASH_OPT_VAR_KEYS", "_DASH_SWATCH_PREFIX",
                      # _stata_date_kind's own pattern, for an axis format().
                      "_MS_PER_DAY", "_DATE_FMT_RE",
                      # The sub-option tables and the filter parser's own.
                      "_DASH_LEGEND_SUBOPTS", "_DASH_TEXTBOX_HONOURED",
                      "_DASH_TEXTBOX_DEFAULTS", "_DASH_SCALE_SUBOPTS",
                      "_DASH_REFLINE_SUBOPTS", "_DASH_FILTER_TYPES",
                      "_DASH_FILTER_SUBOPTS", "_DASH_VARNAME_RE"):
            _val = getattr(_mod, _name, None)
            if _val is None:
                continue
            if any(_l.startswith(_name + " =") for _l in _already):
                continue
            if hasattr(_val, "pattern") and hasattr(_val, "flags"):
                # repr() of a compiled pattern TRUNCATES anything over 200
                # characters with an ellipsis, which then compiles to a
                # different regex or not at all.
                out.append("%s = re.compile(%r, %d)"
                           % (_name, _val.pattern, int(_val.flags)))
                continue
            out.append("%s = %r" % (_name, _val))
        # _validate_if_expr's node whitelist, written by class name and
        # rebuilt from the `ast` module in the app.  Derived from the LIVE
        # frozenset, so a node added here is added there; repr() of the set
        # itself is not valid source, which is why it is not in the list
        # above.
        out += [
            "_IF_EXPR_ALLOWED_NODES = frozenset(",
            "    getattr(_ast, _n) for _n in %r)" % (
                tuple(sorted(_c.__name__ for _c in _IF_EXPR_ALLOWED_NODES)),),
            "",
        ]

        out += [""]

        # Module-level helpers the classes call. Those _shared_stat_lines
        # already writes are skipped; emitting a def twice is legal but
        # leaves two texts to keep in step, which is the whole problem.
        _emitted_names = {
            _l.split("(")[0][4:] for _l in _already if _l.startswith("def ")
        }
        for _fn_name in ("_parse_textbox_opt", "_textbox_split_point",
                         "_optional_import", "_extract_finite", "_apply_jitter",
                         "_with_color_alias", "_jitter_seed", "_floats_only",
                         "_parse_stata_numeric_fmt", "_format_stata_numeric",
                         # _dash_build_hover's own callees. A copied
                         # function whose callee stays behind is a NameError
                         # on the served page, not here.
                         "_tooltip_precision", "_stata_numeric_pattern",
                         "_format_date_value_standalone", "_fp_grid",
                         "_fp_report_unsupported", "_betacf", "_betainc",
                         "_t_cdf", "_t_ppf",
                         # The shared dispatch.  Copied verbatim, like the
                         # statistical helpers above and for the same reason:
                         # both modes then run the SAME table, so a plot type
                         # added to one is added to both.
                         "_dash_layer_source", "_dash_range_source",
                         "_dash_pc_source", "_dash_function_args",
                         "_dash_glyph_dispatch",
                         "_dash_pc_dispatch", "_dash_add_glyph",
                         "_dash_add_pc_glyph",
                         # A layer that drew nothing has to say so in BOTH
                         # modes, in the same words.
                         "_dash_layer_drew_anything",
                         "_dash_report_empty_layer",
                         # One qualifier reader and ONE whitelist.  The
                         # generated app used to carry its own `_safe_g',
                         # written out as string literals, and applied it at
                         # the graph level only -- a per-plot or per-KPI
                         # `if' was not read at all when served.
                         "_validate_if_expr", "_dash_qualified_frame",
                         # The figure's one HoverTool.  HoverTool was
                         # imported into this app and never instantiated.
                         "_dash_hover_row", "_dash_build_hover",
                         # Stata's legend keying rules.
                         "_dash_legend_key", "_dash_legend_entries",
                         # layout(name:row,col), one parser for one spec.
                         "_dash_placement_map",
                         # The KPI card's format resolution and rendering.
                         "_dash_effective_kpi_fmt",
                         "_dash_format_kpi_value",
                         # by(): one parser, one panel-label rule.
                         "_dash_by_tokens", "_dash_parse_by",
                         "_dash_facet_label",
                         # The plot-type name set the parity guard reads.
                         "_dash_plot_type_names",
                         # The legend, whole: keys, rule, every sub-option,
                         # and the scheme's chrome for it.
                         "_dash_move_legend", "_dash_scheme_chrome",
                         "_dash_apply_legend",
                         # Axis titles, Stata's tick grammar, second axes.
                         "_parse_axis_angle", "_stata_date_kind",
                         "_parse_scale_opt", "_source_frame",
                         "_compute_secondary_range",
                         "_dash_axis_labels",
                         "_dash_parse_axis_label_opt",
                         "_dash_parse_axis_spec", "_dash_apply_axis_spec",
                         "_dash_apply_axis_options",
                         "_dash_add_secondary_axes",
                         "_dash_assign_axis_ranges",
                         # The filter widgets and the rows they select.
                         "_whole_number_step", "_is_clock_kind",
                         "_date_slider_step_days", "_clock_slider_step_ms",
                         "_dash_option_value", "_dash_option_sort_key",
                         "_dash_filter_title", "_dash_finite_column",
                         "_dash_filter_widget", "_dash_dropdown_mask",
                         # The document: order, cells, tabs, header.
                         "_dash_layout_order", "_dash_kpi_keys",
                         "_dash_facet_cols", "_dash_layout_cell",
                         "_dash_parse_tabs", "_dash_tab_panels",
                         "_dash_header_fragments", "_dash_header_models",
                         # The columns a layer's options name.
                         "_dash_mlabel_names", "_dash_option_columns",
                         "_dash_attach_labels",
                         "_dash_is_swatch",
                         # Sub-options: honoured or named, in one text.
                         "_textbox_size", "_textbox_color",
                         "_parse_scale_range",
                         "_dash_report_suboptions", "_dash_subopt_name",
                         "_dash_legend_unsupported", "_dash_textbox",
                         "_dash_figure_title", "_dash_style_axis_titles",
                         "_dash_text_annotations", "_dash_scale_spec",
                         "_dash_apply_scale_ranges", "_dash_reference_lines",
                         "_dash_display",
                         # plotregion(lwidth()) and the KPI colour: the
                         # saved renderer's readers, so a keyword width is
                         # honoured and an unknown colour is named here too.
                         "_extract_region_lwidth",
                         "_resolve_kpi_color", "_sanitize_css_color",
                         "_dash_kpi_card_html",
                         "_dash_warn_filter_missing", "_dash_warn_filter_type",
                         "_dash_parse_filter_raw"):
            if _fn_name in _emitted_names:
                continue
            _fn = getattr(_mod, _fn_name, None)
            if _fn is None:
                continue
            out += _textwrap.dedent(
                _inspect.getsource(_fn)).rstrip("\n").split("\n")
            out += ["", ""]

        # The three classes, in dependency order.
        for _cls in (OptionTranslator, SchemeParser, GlyphMapper):
            out += _inspect.getsource(_cls).rstrip("\n").split("\n")
            out += ["", ""]

        # The scheme, as a property dict rather than a file. SchemeParser
        # reads .scheme files from disk; an app that has been moved, or a
        # machine without dash installed, has none. __new__ plus the parsed
        # properties gives a REAL SchemeParser with no file access, so the
        # served figure is styled by the same code the saved one is.
        out += [
            "_SCHEME_PROPS = %r" % (dict(getattr(self.scheme, "_props", {})),),
            "_DASH_SCHEME_IS_FALLBACK = %r"
            % (bool(getattr(self.scheme, "is_fallback", False)),),
            "_DASH_SCHEME_REQUESTED = %r" % (self.scheme_requested,),
            "",
            "",
            "def _dash_build_scheme():",
            '    """The dashboard\'s scheme, rebuilt without touching the disk."""',
            "    _s = SchemeParser.__new__(SchemeParser)",
            "    _s._props = dict(_SCHEME_PROPS)",
            "    _s.name = %r" % (getattr(self.scheme, "name", "s2color"),),
            "    _s.is_fallback = _DASH_SCHEME_IS_FALLBACK",
            "    _s._init_properties()",
            "    return _s",
            "",
            "",
            "# Provenance travels with the properties.  This used to be\n"
            "# the literal False, so an app built where no .scheme file\n"
            "# could be read was indistinguishable from a healthy one --\n"
            "# and the resolution warning is emitted in the BUILDER's\n"
            "# process, so whoever later runs the app was told nothing.",
            "if _DASH_SCHEME_IS_FALLBACK:",
            "    warnings.warn(",
            "        \"dash: this app was built where no .scheme file \"",
            "        \"could be read. You asked for %s; it is drawing \"",
            "        \"dash's built-in fallback properties, not that \"",
            "        \"scheme. Reinstall dash or run dash_setup, then \"",
            "        \"rebuild the app.\" % (_DASH_SCHEME_REQUESTED,),",
            "        UserWarning, stacklevel=2,",
            "    )",
            "",
            "",
            "_DASH_SCHEME = _dash_build_scheme()",
            "_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)",
            "",
        ]
        return out

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

        out += ["_FIT_GRID = %d" % _FIT_GRID, "",
                "# The style notes already raised this document, keyed",
                "# (option, value, what); _dash_reset_notes clears it at the",
                "# top of make_document, as DashRenderer.render() does.",
                "_DASH_NOTED = set()", "", ""]

        for _fn in (_stat_option_float,
                    # The style note: GlyphMapper and OptionTranslator are
                    # copied by source and call it by name.  With it the
                    # once-per-render set's helpers, and the graph-level
                    # colour and proportion readers the figure block calls.
                    _dash_style_note, _dash_warn_once, _dash_reset_notes,
                    _dash_graph_color, _dash_figure_aspect, _fit_grid,
                    # lpolyci's band is a bootstrap; without these the served
                    # branch was a verbatim copy of lpoly and drew no band.
                    _resolve_level, _dash_session_level,
                    _dash_histogram_ymode, _resolve_seed, _jitter_seed,
                    _stata_percentile, _stata_kde_bandwidth, _kde_curve,
                    _mband_default_bands, _stata_bin_count,
                    _histogram_heights,
                    # Stata's `if' grammar and its arithmetic operators.  The
                    # standalone renderer translates both before parsing; this
                    # file did neither, so `if inlist(rep78,1,2)' filtered
                    # nothing and `function y = x^2' drew nothing at all.
                    #
                    # The two masking helpers come WITH _stata_if_to_pandas:
                    # it calls them, and a copied function whose callees stay
                    # behind raises NameError on the served page rather than
                    # here, where it would be noticed.
                    _mask_string_literals, _unmask_string_literals,
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
                    GlyphMapper._bootstrap_ci,
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
        """Emit the build-time constants the generated app reads.

        The scheme itself travels as ``_SCHEME_PROPS`` (see
        ``_glyph_layer_lines``), from which the app rebuilds a real
        ``SchemeParser`` as ``_DASH_SCHEME``; every figure, legend, label
        and KPI card is styled through that object by the same methods the
        saved renderer runs.  This used to emit a second, hand-copied
        rendering of the scheme -- ``_SCHEME_COLORS``, ``_SCHEME_SYMBOLS``,
        ``_SCHEME_LINE_WIDTH``, ``_SCHEME_CHROME`` and an
        ``_dash_apply_scheme`` that re-implemented ``apply_to_figure`` --
        none of which anything read once ``_DASH_MAPPER`` existed, and
        whose one live copy drifted from the method it shadowed.
        """
        sch = self.scheme
        return [
            "# ---- Build-time constants ----",
            "#",
            "# The scheme's graphsize, for xsize() or ysize() given alone (the",
            "# other dimension is the scheme's) and for the default",
            "# proportions when neither is given, as in the saved figure.",
            "_SCHEME_GRAPHSIZE_X = %r" % (getattr(sch, "graphsize_x", None),),
            "_SCHEME_GRAPHSIZE_Y = %r" % (getattr(sch, "graphsize_y", None),),
            # Same crossover the standalone renderer uses. It was written
            # here as a bare 10000 in three places, so changing it in one
            # mode changed it in one mode.
            "_WEBGL_THRESHOLD = %r" % (_WEBGL_THRESHOLD,),
            # The dataset's Stata display formats, filtered to the ones that
            # mean something numerically.  A module-level constant because
            # _format_kpi is module-level here and has to resolve a KPI's
            # effective format the same way the saved renderer does.
            "_NUM_FORMATS = %r" % ({
                str(_k): str(_v)
                for _k, _v in (self.spec.get("build_options", {})
                               .get("formats", {}) or {}).items()
                if _stata_numeric_pattern(str(_v))},),
            "_CI_BAND_ALPHA = %r" % (_CI_BAND_ALPHA,),
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

        # ServerAppBuilder holds the data as a JSON string, not a frame.
        # Parsing a large one costs about a second, so it is only parsed when
        # it COULD reach the threshold: the smallest plausible cell is about
        # six bytes of JSON (`"a":1,'), so a string shorter than six bytes
        # per cell cannot hold a million cells and needs no parse.
        if len(self._raw_data_str) >= _LARGE_DATASET_CELLS * 6:
            try:
                _d = json.loads(self._raw_data_str)
                # jsonio wraps everything in a "StataJSON" object.
                _d = _d.get("StataJSON", _d)
                _vals = _d.get("values") or []
                _cols = _d.get("variableNames") or (
                    list(_vals[0]) if _vals else [])
                _report_dataset_size(
                    pd.DataFrame(index=range(len(_vals)),
                                 columns=list(_cols)), "server app")
            except (ValueError, TypeError, KeyError, IndexError):
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
            "import os",
            "import re",
            "import ast as _ast",
            # GlyphMapper's signatures annotate with Any, Callable and List.
            # Annotations are evaluated when the class body runs on any
            # interpreter without PEP 649's lazy evaluation -- Stata's
            # embedded Python among them -- and the app then raises
            # NameError at import. It did.
            "from typing import Any, Callable, Iterable, List",
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
            "    InlineStyleSheet,",
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
            "# _sanitize_css_color, copied by name below, reads it under the",
            "# saved renderer's name.",
            "_CSS_COLOR_RE = _CSS_COLOR_RE_APP",
            "",
            "",
            "def _dash_kpi_card(title, value, subtitle, color, bgcolor, name=''):",
            "    # One card, the standalone one, through the builder the saved",
            "    # renderer runs (copied by name), with this dashboard's scheme:",
            "    # the card is the scheme's legend box.  There were five",
            "    # builders and the server's drew the value at 28px where",
            "    # standalone drew it at 36px, with different padding, border",
            "    # and label colours.",
            "    return _dash_kpi_card_html(title, value, subtitle, color, bgcolor,",
            "                               name, _DASH_SCHEME)",
            "",
            "",
            "def _dash_kpi_stylesheets():",
            "    # The scheme's CSS for a KPI Div: a Bokeh 3 Div renders in a",
            "    # shadow root, so the .db-kpi-card rule has to travel on the Div.",
            "    return [InlineStyleSheet(css=_DASH_SCHEME.css_block())]",
            "",
        ] + self._scheme_lines() + self._shared_stat_lines() \
          + self._glyph_layer_lines() + [
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
            "def _compute_lfit(df, yvar, xvar, options=None):",
            '    """Return line source dict for OLS fit of yvar on xvar.',
            "",
            "    _fit_grid is the standalone renderer's own function, copied",
            "    in above, so n() is read here too and both modes draw at the",
            "    same x. The point count was written as a literal 100.",
            '    """',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 2:",
            "        return dict(x=[], y=[])",
            "    coeffs = np.polyfit(clean[xvar].values, clean[yvar].values, 1)",
            "    x_range = _fit_grid(clean[xvar].values, options or {})",
            "    return dict(x=x_range.tolist(), y=np.polyval(coeffs, x_range).tolist())",
            "",
            "",
            "def _compute_qfit(df, yvar, xvar, options=None):",
            '    """Return line source dict for quadratic fit of yvar on xvar."""',
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 3:",
            "        return dict(x=[], y=[])",
            "    coeffs = np.polyfit(clean[xvar].values, clean[yvar].values, 2)",
            "    x_range = _fit_grid(clean[xvar].values, options or {})",
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
            "def _compute_lpolyci(df, yvar, xvar, options=None):",
            '    """Return the lpoly fit and its bootstrap confidence band.',
            "",
            "    The served lpolyci branch used to be a verbatim copy of the",
            "    lpoly one: it drew the smoother and no band at all, so a",
            "    served lpolyci and a saved one were different figures.",
            "    _bootstrap_ci and _compute_lpoly_fit are the standalone",
            "    renderer's own functions, copied in above.",
            '    """',
            "    options = options or {}",
            "    clean = df[[xvar, yvar]].dropna()",
            "    if len(clean) < 3:",
            "        return dict(x_lp=[], y_lp=[], y_lower=[], y_upper=[])",
            "    x = clean[xvar].to_numpy(dtype=float)",
            "    y = clean[yvar].to_numpy(dtype=float)",
            "    bwidth = _stat_option_float(options, 'bwidth', None, 'lpolyci', lo=0.0)",
            "    if bwidth is not None and bwidth <= 0:",
            "        bwidth = None",
            "    degree = int(_stat_option_float(options, 'degree', 0.0, 'lpoly',",
            "                                    lo=0.0, hi=3.0) or 0.0)",
            "    kernel = str(options.get('kernel', '') or 'epanechnikov').strip().lower()",
            "    if kernel not in _KERNELS:",
            "        kernel = 'epanechnikov'",
            "    x_grid, y_fit = _compute_lpoly_fit(x, y, bwidth=bwidth,",
            "                                       degree=degree, kernel=kernel,",
            "                                       n_grid=100)",
            "",
            "    def _fn(xi, yi, _xg):",
            "        _, yb = _compute_lpoly_fit(xi, yi, bwidth=bwidth,",
            "                                   degree=degree, kernel=kernel,",
            "                                   n_grid=100)",
            "        return yb",
            "",
            "    y_lower, y_upper = _bootstrap_ci(",
            "        x, y, x_grid, _fn, fallback=y_fit,",
            "        level=_resolve_level(options), seed=_resolve_seed(options))",
            "    valid = ~np.isnan(y_fit)",
            "    return dict(x_lp=x_grid[valid].tolist(),",
            "                y_lp=y_fit[valid].tolist(),",
            "                y_lower=y_lower[valid].tolist(),",
            "                y_upper=y_upper[valid].tolist())",
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
            "def _format_kpi(value, fmt_str, varname='', stat=''):",
            '    """Format a KPI value, through the saved renderer\'s own formatter.',
            "",
            "    This used to be three lines that matched %[w].[d][fge],",
            "    ALWAYS comma-grouped an `f', ignored the `c' suffix that",
            "    ASKS for grouping, and fell back to round(value, 4) with no",
            "    %9.0g default -- so fmt(%12.0fc) was identical to",
            "    fmt(%12.0f) when served, and a card with no fmt() showed a",
            "    different number of digits than the saved dashboard.",
            '    """',
            "    return _dash_format_kpi_value(",
            "        value, _dash_effective_kpi_fmt(",
            "            {'fmt': fmt_str}, varname, _NUM_FORMATS),",
            "        varname, stat)",
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
            "    # The previous document's style notes, forgotten: one note per",
            "    # (option, value) per render, as DashRenderer.render() does.",
            "    _dash_reset_notes()",
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
            "    # Raw: the header builder escapes it exactly once.",
            "    title_text = bo.get('title', '') or ''",
            "",
            "    var_labels = meta['var_labels']",
            "    # The dataset's Stata display formats, for the tooltip's",
            "    # own number formatting.  Resolved at build time into",
            "    # _NUM_FORMATS with the SAME predicate the saved renderer",
            "    # uses, so `%9.0fc' reads the same in both.",
            "    _num_formats = _NUM_FORMATS",
            "    val_label_names = meta['val_label_names']",
            "    val_labels = meta['val_labels']",
            "    # The dataset's Stata metadata reaches the mapper, as it does",
            "    # when the saved renderer builds one: a served colour key used",
            "    # to read '0'/'1' where the saved one reads the value labels.",
            "    _dash_attach_labels(_DASH_MAPPER, var_labels, val_labels,",
            "                        val_label_names, numeric_formats=_NUM_FORMATS)",
            "    # The session's c(level): a band with no level() of its own",
            "    # draws at it.  It used to reach the legend key and never",
            "    # the band, so `set level 90' served a 95% band labelled 90%.",
            "    _DASH_MAPPER.default_level = _dash_session_level(bo)",
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
            "            # colorvar() and mlabel() name columns too, and so does",
            "            # hover(): a linked graph draws from the shared source,",
            "            # which must carry them.  Measured without this: a linked",
            "            # hover(price) had no price and a linked mlabel(rep) no labels.",
            "            for _cv in _dash_option_columns(p.get('options', {}), df.columns):",
            "                all_vars.add(_cv)",
            "        for _hc in (g.get('graph_options', {}).get('hover', '') or '').split():",
            "            if _hc in df.columns: all_vars.add(_hc)",
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
            "    # ---- The if_expr whitelist ----",
            "    # _validate_if_expr is copied in above, from the same",
            "    # source the saved renderer runs.  This app used to carry",
            "    # its own `_safe_g' written out as string literals: the",
            "    # two node sets happened to agree, and nothing made them.",
            "    _safe_g = _validate_if_expr",
            "",
            "    # ---- Build figures ----",
            "    figures: dict = {}",
            "    TOOLS = [PanTool(), WheelZoomTool(), BoxSelectTool(), LassoSelectTool(), ResetTool()]",
            "",
            "    _redrawn_ids = set()",
            "    # Sub-option reports already made this render, so a by()",
            "    # panel does not repeat its graph's.",
            "    _reported_subopts = set()",
            "",
            "    def _dash_draw_layer(fig, g_df, plot, pi, gname, _ln, _shared, _fallback):",
            '        """Draw one layer of one figure; return (layer_source, [drawn sources]).',

            "        The one place a plot type is dispatched to its mapper,",
            "        for the live figure, for every by() panel, and for the",
            "        redraw a filter move triggers.  Family order is the",
            "        saved renderer's: literal, function, pc, range, else.",
            '        """',
            "        ptype = str(plot.get('type', '') or '').lower()",
            "        if ptype == 'hist':",
            "            ptype = 'histogram'",
            "        opts = plot.get('options', {})",
            "        yvar = plot.get('yvar', '') or plot.get('var', '')",
            "        xvar = plot.get('xvar', '')",
            "        _hv = _hover_cols_of(gname)",
            "        _before = len(fig.renderers)",
            "        _ly_src = None",
            "        if ptype == 'scatteri':",
            "            _DASH_MAPPER.map_scatteri(fig, plot.get('values', []), opts, color_idx=pi)",
            "        elif ptype == 'pci':",
            "            _DASH_MAPPER.map_pci_literal(fig, plot.get('values', []), opts, color_idx=pi)",
            "        elif ptype == 'function':",
            "            _fn_range, _fn_n = _dash_function_args(opts)",
            "            _DASH_MAPPER.map_function(fig, plot.get('expr', ''), _fn_range, _fn_n, opts)",
            "        elif ptype in _DASH_PC_TYPES:",
            "            _ly_src, _ok = _dash_pc_source(",
            "                g_df, plot.get('y1var', ''), plot.get('x1var', ''),",
            "                plot.get('y2var', ''), plot.get('x2var', ''))",
            "            if _ok:",
            "                _dash_add_pc_glyph(",
            "                    _DASH_MAPPER, fig, _ly_src, ptype,",
            "                    plot.get('y1var', ''), plot.get('x1var', ''),",
            "                    plot.get('y2var', ''), plot.get('x2var', ''),",
            "                    opts, color_idx=pi)",
            "        elif ptype in _DASH_RANGE_TYPES:",
            "            y1var = plot.get('yvar1', '') or plot.get('yvar', '') or plot.get('y1var', '')",
            "            y2var = plot.get('yvar2', '') or plot.get('y2var', '')",
            "            _ly_src, _ok = _dash_range_source(",
            "                g_df, y1var, y2var, xvar, opts.get('mlabel', ''),",
            "                extra_cols=_hv + _dash_option_columns(opts, df.columns))",
            "            if _ok:",
            "                _dash_add_glyph(",
            "                    _DASH_MAPPER, fig, _ly_src, ptype, y1var, xvar,",
            "                    opts, y2var=y2var, color_idx=pi)",
            "        else:",
            "            _ly_src, _ly_view = _dash_layer_source(",
            "                g_df, df, xvar, yvar, opts.get('mlabel', ''),",
            "                gname, _ln, _shared, _shared_pos, _fallback,",
            "                extra_cols=_hv + _dash_option_columns(opts, df.columns))",
            "            if _ly_src is not None:",
            "                _dash_add_glyph(",
            "                    _DASH_MAPPER, fig, _ly_src, ptype, yvar, xvar, opts,",
            "                    view=_ly_view, color_idx=pi)",
            "        # A yaxis(2)/xaxis(2) layer draws on the secondary range.",
            "        _dash_assign_axis_ranges(fig, fig.renderers[_before:], opts)",
            "        _srcs = []",
            "        for _rr in fig.renderers[_before:]:",
            "            # A colour key's invisible swatches are not a layer",
            "            # source: not refreshed, not redrawn.",
            "            if _dash_is_swatch(_rr):",
            "                continue",
            "            _rs = getattr(_rr, 'data_source', None)",
            "            if _rs is not None and all(_rs is not _s for _s in _srcs):",
            "                _srcs.append(_rs)",
            "        return _ly_src, _srcs",
            "",
            "    def _hover_cols_of(gname):",
            "        # The columns hover() asks for, carried into every layer",
            "        # source so the tooltip can read them.",
            "        for _gx in graphs:",
            "            if _gx.get('graph_options', {}).get('name', '') == gname.split('__by__')[0]:",
            "                _raw = (_gx.get('graph_options', {}).get('hover', '') or '').strip()",
            "                return [_c for _c in _raw.split() if _c in df.columns]",
            "        return []",
            "",
            "    def _dash_redraw_for(g, plot, pi, gname):",
            '        """A closure that redraws one layer from a frame the callback hands it.',

            "        The frame arrives filtered and, for a by() panel, masked to",
            "        the panel's group.  The layer's own if()/in() is applied",
            "        here, so a qualified fit stays qualified after a filter",
            "        move.  Drawn on a throwaway figure with no linking, because",
            "        only the DATA the mapper produces is wanted.",
            '        """',
            "        _go = g.get('graph_options', {})",
            "        _g_if = (_go.get('if_expr') or g.get('if_expr') or '').strip()",
            "        _g_in = (_go.get('in_expr') or g.get('in_expr') or '').strip()",
            "        _p_if = (plot.get('if_expr') or '').strip()",
            "        _p_in = (plot.get('in_expr') or '').strip()",
            "        def _redraw(frame):",
            "            # The graph's qualifier, then the layer's own where it",
            "            # differs -- the same two steps the live figure took.",
            "            _fr = _dash_qualified_frame(frame, _g_if, _g_in,",
            "                                        'graph %r' % gname, copy=False)",
            "            if (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in):",
            "                _fr = _dash_qualified_frame(_fr, _p_if, _p_in,",
            "                                            'graph %r plot %d' % (gname, pi + 1),",
            "                                            copy=False)",
            "            _tfig = bokeh_figure()",
            "            _ly, _srcs = _dash_draw_layer(_tfig, _fr, plot, pi, gname,",
            "                                          set(), None, None)",
            "            return [_s for _s in _srcs if _s is not _ly]",
            "        return _redraw",
            "",
            "    def _dash_figure_for(g, gname, g_df, _fac_label=None):",
            '        """Build one figure: a graph, or one by() panel of it.',

            "        This is the body of what used to be the per-graph loop.",
            "        The by() panels used to be drawn by two REDUCED copies",
            "        of it -- eighteen plot types, hardcoded marker sizes,",
            "        no hover, Bokeh's default legend -- and the other twenty",
            "        types fell off the end of them and drew nothing.  One",
            "        body, called once per panel, is the only way the panels",
            "        can be the graph.",
            '        """',
            "        go = g.get('graph_options', {})",
            "        _src_list = graph_sources.get(gname)",
            "        src = (_src_list[-1] if isinstance(_src_list, list) and _src_list else shared_source)",
            "        # ---- Per-graph if_expr / in_expr filtering ----",
            "        # Read from graph_options first; fall back to top-level graph key",
            "        # so that qualifiers set by dash.ado at the graph level are honoured.",
            "        _g_if = (go.get('if_expr') or g.get('if_expr') or '').strip()",
            "        _g_in = (go.get('in_expr') or g.get('in_expr') or '').strip()",
            "        # g_df arrives QUALIFIED from the caller: the graph's own",
            "        # rows, or one by() panel's share of them.  It is not",
            "        # re-qualified here -- `in 3/5' is not idempotent.",
            "        # The graph's own rows, before any per-LAYER qualifier",
            "        # narrows them further.  Each layer starts from here.",
            "        _g_df_graph = g_df",
            "",
            "        plots = g.get('plots', [])",
            "        xv = plots[0].get('xvar', '') if plots else ''",
            "        yv = plots[0].get('yvar', '') if plots else ''",
            "        # Canvas text, through the helper the saved renderer runs:",
            "        # this used to html.escape the user's title and to title a",
            "        # histogram's y axis with the variable, where the saved",
            "        # figure titled it nothing and Stata writes 'Density'.",
            "        x_label, y_label = _dash_axis_labels(plots, go, var_labels,",
            "                                             _reported_subopts, gname)",
            "",
            "        n_rows = len(df)",
            "        backend = 'webgl' if n_rows > _WEBGL_THRESHOLD else 'canvas'",
            "        _fig_kw = dict(",
            "            title=_parse_textbox_opt(go.get('title', '') or '')[0],",
            "            x_axis_label=x_label,",
            "            y_axis_label=y_label,",
            "            tools=TOOLS,",
            "            sizing_mode='stretch_width',",
            "            output_backend=backend,",
            "        )",
            "        # xsize()/ysize()/aspectratio(): the helper the saved",
            "        # renderer runs.  This read aspectratio() alone, uninverted,",
            "        # and said nothing for a bad value the saved renderer named.",
            "        # With none given, the scheme's own graphsize ratio, as the",
            "        # saved figure (_resolve_aspect_ratio) -- a served figure",
            "        # used to ignore the scheme's proportions entirely -- held",
            "        # to the same height bounds so a wide page stays scrollable.",
            "        _ar = _dash_figure_aspect(go, _SCHEME_GRAPHSIZE_X, _SCHEME_GRAPHSIZE_Y)",
            "        if _ar is None and _SCHEME_GRAPHSIZE_X and _SCHEME_GRAPHSIZE_Y:",
            "            _ar = float(_SCHEME_GRAPHSIZE_X) / float(_SCHEME_GRAPHSIZE_Y)",
            "        if _ar is not None:",
            "            _fig_kw['aspect_ratio'] = _ar",
            "            _fig_kw['max_height'] = _MAX_FIGURE_HEIGHT",
            "            _fig_kw['min_height'] = _MIN_FIGURE_HEIGHT",
            "        _xsc = _dash_scale_spec(go.get('xscale', ''), 'xscale', _reported_subopts, gname)",
            "        _ysc = _dash_scale_spec(go.get('yscale', ''), 'yscale', _reported_subopts, gname)",
            "        if _xsc['log']: _fig_kw['x_axis_type'] = 'log'",
            "        if _ysc['log']: _fig_kw['y_axis_type'] = 'log'",
            "        fig = bokeh_figure(**_fig_kw)",
            "        # Scheme first, so an explicit graph option still wins --",
            "        # through the SchemeParser method the saved figure uses,",
            "        # not a hand-copied rendering of it.",
            "        _DASH_SCHEME.apply_to_figure(fig)",
            "        # yaxis(2)/xaxis(2): the second axis, from the rows this",
            "        # figure draws.  There used to be none when served.",
            "        _dash_add_secondary_axes(fig, plots, go, g_df)",
            "        # title(), xtitle()/ytitle() sub-options, after the scheme so",
            "        # the user's size() and color() win; the rest named.",
            "        _dash_figure_title(fig, go, _reported_subopts, gname)",
            "        _dash_style_axis_titles(fig, go, _reported_subopts, gname)",
            "        # Initialised with the figure, not with the plot loop: a",
            "        # faceted graph never enters that loop and would reach the",
            "        # legend block with the name unbound.",
            "        _leg_bounds = []",
            "        # range() and reverse are applied by _dash_apply_scale_ranges,",
            "        # after the region colours below, as the saved figure does.",
            "        # bgcolor / plotbgcolor — figure background colors",
            "        # Every colour through _dash_graph_color, the reader the saved",
            "        # figure uses: an unknown name is named, the scheme's kept.",
            "        # _resolve_color returned '' for it without a word.",
            "        _raw_bgc = go.get('bgcolor', '')",
            "        if _raw_bgc:",
            "            _bgc_resolved = _dash_graph_color('bgcolor', _raw_bgc)",
            "            if _bgc_resolved: fig.border_fill_color = _bgc_resolved",
            "        _raw_pbgc = go.get('plotbgcolor', '')",
            "        if _raw_pbgc:",
            "            _pbgc_resolved = _dash_graph_color('plotbgcolor', _raw_pbgc)",
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
            "                _c = _dash_graph_color('plotregion(color)', _pr_bg)",
            "                if _c: fig.background_fill_color = _c",
            "            _pr_lc = _region_lcolor(_raw_pr)",
            "            if _pr_lc:",
            "                _c = _dash_graph_color('plotregion(lcolor)', _pr_lc)",
            "                if _c: fig.outline_line_color = _c",
            "            # lwidth(): the saved renderer's reader, so a keyword",
            "            # (thick) is honoured and a word is named; a bare float()",
            "            # here took neither.",
            "            _pr_lw = _extract_region_lwidth(_raw_pr)",
            "            if _pr_lw is not None: fig.outline_line_width = _pr_lw",
            "        _raw_gr = go.get('graphregion', '')",
            "        if _raw_gr:",
            "            _gr_bg = _region_color(_raw_gr)",
            "            if _gr_bg:",
            "                _c = _dash_graph_color('graphregion(color)', _gr_bg)",
            "                if _c: fig.border_fill_color = _c",
            "        _dash_apply_scale_ranges(fig, _xsc, _ysc, g_df, xv, yv)",
            "        # note(), caption(), subtitle(): the helper the saved renderer",
            "        # runs, at the scheme's text-box sizes and colours.",
            "        _dash_text_annotations(fig, go, _reported_subopts, gname, _DASH_SCHEME)",
            "        # xline()/yline(): the helper the saved renderer runs.",
            "        _dash_reference_lines(fig, go, _reported_subopts, gname)",
            "        # xlabel()/ylabel()/xtick()/ytick(): Stata's full grammar,",
            "        # through the helper the saved renderer runs.  A 14-line",
            "        # parser here read a bare numlist and angle() and nothing",
            "        # else, so xlabel(2000(1000)4000) was ignored when served.",
            "        _dash_apply_axis_options(fig, go, xv, yv, g_df, _num_formats,",
            "                                 _reported_subopts, gname,",
            "                                 grid_color=_DASH_SCHEME.grid_color)",
            "",
            '        # Legend boundaries.  NOT ONE of the 44 glyph calls in this loop',
            '        # passed legend_label, so a served figure had no legend at all --',
            '        # measured on a scatter with an lfit over it: standalone drew one',
            '        # legend with two items, the served document drew none, and there',
            '        # was no way to tell the fit from the points.  Recording where each',
            "        # layer's renderers begin lets the legend be built once, below,",
            '        # instead of threading a label through every call.',
            '        for pi, plot in enumerate(plots):',
            "            # Lower-cased, and `hist' accepted, exactly as the",
            "            # facet chains below and the saved renderer do.  The",
            "            # three tables disagreed about what a type is called;",
            "            # nothing reaches this through dash.ado today, but a",
            "            # spec written by hand or by a future caller would",
            "            # have drawn under by() and not without it.",
            "            ptype = str(plot.get('type', '') or '').lower()",
            "            if ptype == 'hist':",
            "                ptype = 'histogram'",
            "            yvar = plot.get('yvar', '') or plot.get('var', '')",
            "            xvar = plot.get('xvar', '')",
            "            y1var = plot.get('yvar1', '')",
            "            y2var = plot.get('yvar2', '')",
            "            opts = plot.get('options', {})",
            '',
            '            # The PLOT, not a label computed here.  This used to',
            "            # read the y-variable name for every layer, so a",
            '            # served lfitci was keyed "mpg" where the saved',
            '            # dashboard keys it "95%% CI" and "Fitted values".',
            '            # _dash_legend_entries applies Stata\'s own rules,',
            '            # below, once the renderers exist.',
            '            _leg_bounds.append((len(fig.renderers), plot))',
            '            _r_before = len(fig.renderers)',
            '',
            '            # ---- This layer\'s own if()/in() ----',
            '            # GAPS.md D3: no per-plot qualifier was read here at',
            "            # all.  dash.ado promotes the FIRST segment's",
            '            # qualifier to the graph level and leaves every',
            '            # segment carrying its own, because the saved',
            '            # renderer applies them per layer -- so a second',
            "            # segment's `if' was simply discarded when served,",
            '            # and the layer drew every observation.',
            '            #',
            '            # Applied only when it DIFFERS from the graph-level',
            "            # one, which _g_df_graph already carries; that is the",
            '            # same test the saved renderer makes.  A linked',
            '            # graph keeps drawing from the shared source:',
            '            # _dash_layer_source turns a shorter frame into a',
            '            # CDSView over it rather than a source of its own.',
            "            _p_if = (plot.get('if_expr') or '').strip()",
            "            _p_in = (plot.get('in_expr') or '').strip()",
            '            if (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in):',
            '                g_df = _dash_qualified_frame(',
            "                    _g_df_graph, _p_if, _p_in,",
            "                    'graph %r plot %d' % (gname, pi + 1),",
            '                    copy=False)',
            '            else:',
            '                g_df = _g_df_graph',
            '',
            "            # ---- One dispatch, by plot-type family ----",
            "            # WP-09 routed all 38 types through GlyphMapper but left one",
            "            # branch per type standing, each the same eleven lines with",
            "            # a different name in them.  WP-11 folds them into",
            "            # _dash_draw_layer, which the by() panels and the filter",
            "            # callback call as well, so there is exactly one place that",
            "            # decides how a layer is drawn.",
            "            _drawn = _dash_draw_layer(fig, g_df, plot, pi, gname,",
            "                                      linked_names, shared_source, src)",
            "            _ly_src = _drawn[0]",
            "            _r_srcs = _drawn[1]",
            "            if _ly_src is not None and _r_srcs and _ly_src not in _r_srcs:",
            "                # The mapper drew from a source it built.  The layer",
            "                # source is registered as well: graph_sources feeds the",
            "                # brush-to-KPI wiring, which wants a source whose rows",
            "                # ARE data rows (one carrying 'index').",
            "                graph_sources[gname].append(_ly_src)",
            "            for _rs in _r_srcs:",
            "                graph_sources[gname].append(_rs)",
            "            if _r_srcs and any(_rs is not _ly_src for _rs in _r_srcs):",
            "                # A source the mapper BUILT -- a fitted line, a histogram,",
            "                # a line sorted along x -- cannot be refreshed by swapping",
            "                # its columns for the filtered rows: the columns are not",
            "                # dataset columns, or are not in dataset order.  Measured",
            "                # after one filter move: a served lfit was ten points of",
            "                # the OLD line, and a served line was drawn in dataset",
            "                # order, crossing itself.  Such a layer is REDRAWN: the",
            "                # same mapper, the filtered frame, a throwaway figure,",
            "                # and the fresh data copied onto the live sources.",
            "                agg_sources[(gname, pi)] = {",
            "                    'type': ptype,",
            "                    'sources': [_rs for _rs in _r_srcs if _rs is not _ly_src],",
            "                    'redraw': _dash_redraw_for(g, plot, pi, gname),",
            "                }",
            "                for _rs in agg_sources[(gname, pi)]['sources']:",
            "                    _redrawn_ids.add(id(_rs))",
            # Marker labels are the MAPPER's business, in both modes.
            # This is where a second implementation of mlabel() used to
            # live: a hand-written block that ran after the dispatch and
            # added its own LabelSet.  Once every type went through
            # GlyphMapper it became a DUPLICATE -- `dash line mpg weight,
            # mlabel(foreign)' served two LabelSets at the same
            # coordinates, and lpolyci, fpfitci and mband were labelled
            # when the saved dashboard labels neither -- so it is gone,
            # not merely narrowed.  _dash_layer_source already carries the
            # label column into the layer source for the mapper to use.

            # A layer that drew nothing used to say nothing when served,
            # which is why every divergence GAPS.md D2 lists was silent:
            # `pci' produced a titled, axed, empty plot region and rc 0.
            # The saved dashboard has warned since WP-02; this is the same
            # helper, so the two modes word it identically.
            "            if len(g_df) and not _dash_layer_drew_anything(",
            "                    list(fig.renderers[_r_before:])):",
            "                _dash_report_empty_layer(gname, pi + 1, ptype,",
            "                                         len(g_df))",
            "",

            '        # ---- Build the legend ----',
            '        #',
            '        # NOT ONE of the 44 glyph calls in the plot loop passed',
            '        # legend_label, so a served figure had no legend at all -- measured',
            '        # on a scatter with an lfit over it, standalone drew one legend with',
            '        # two items and the served document drew none.  Recording where each',
            "        # layer's renderers begin lets the legend be built once, here,",
            '        # instead of threading a label through every call.',
            "        # A legend is drawn only where the MAPPER made one, which",
            "        # is the rule the saved renderer follows: it rebuilds the",
            "        # keys of a legend Bokeh has already created from the",
            "        # glyphs' legend_label, and returns without building one",
            "        # when there is none.  lowess, scatteri and pci pass no",
            "        # label, and a served figure used to carry a Legend model",
            "        # for them where the saved one carries nothing.",
            "        _plot_rends = []",
            "        for _bi, (_start, _lplot) in enumerate(_leg_bounds):",
            "            _end = (_leg_bounds[_bi + 1][0]",
            "                    if _bi + 1 < len(_leg_bounds) else len(fig.renderers))",
            "            _plot_rends.append((_lplot, [",
            "                fig.renderers[_ri] for _ri in range(_start, _end)",
            "                if 0 <= _ri < len(fig.renderers)]))",
            "        # Keys, Stata's drawing rule and every legend() sub-option,",
            "        # through the helper the saved renderer runs.  This file's",
            "        # own block knew off, four keywords, label() and cols()/rows();",
            "        # position(), ring(0), size(), order() and legend(on) were",
            "        # ignored, the keys were HTML-escaped, and every legend was",
            "        # clickable where the saved one is not.",
            "        _dash_apply_legend(fig, _plot_rends, go.get('legend', ''),",
            "                           var_labels, _DASH_MAPPER.default_level,",
            "                           _dash_scheme_chrome(_DASH_SCHEME),",
            "                           _reported_subopts, gname)",
            "",
            '        # ---- The figure\'s one HoverTool ----',
            '        # GAPS.md D2: HoverTool was imported into this file and',
            '        # never instantiated, so the only tooltips a served',
            "        # figure had were the ones map_scatter and map_line add",
            '        # for themselves -- bar, histogram, area, every range',
            '        # type and every fit had none, and hover() was ignored.',
            '        # _dash_build_hover is the saved renderer\'s own builder,',
            '        # copied in above, so the two cannot word a tooltip',
            '        # differently.',
            "        _hv = (go.get('hover', '') or '').strip()",
            "        _p0 = plots[0] if plots else {}",
            '        _dash_build_hover(',
            "            fig, _p0.get('xvar', ''),",
            "            _p0.get('yvar', '') or _p0.get('yvar1', ''),",
            "            _p0.get('yvar2', ''),",
            '            _hv.split() if _hv else [],',
            '            var_labels=var_labels,',
            '            numeric_formats=_num_formats,',
            "            univar=_p0.get('var', ''),",
            '        )',
            '',
            "        if _fac_label is not None:",
            "            # The panel title is the figure's OWN title text -- the",
            "            # parsed title() the saved renderer joins with the label --",
            "            # not html.escape(go['title']): a Title is drawn on the",
            "            # canvas, and title(\"By\") was served as &quot;By&quot;.",
            "            _own = fig.title.text if fig.title is not None else ''",
            "            fig.title.text = (f'{_own} \u2014 {_fac_label}' if _own",
            "                              else _fac_label)",
            "        return fig",

            "    # ---- Build figures: one call per graph, or per by() panel ----",
            "    _facet_map = {}         # gname -> [(panel_key, label)]",
            "    _facet_group_vals = {}  # panel_key -> (by_vars, group_key)",
            "    for g in graphs:",
            "        go = g.get('graph_options', {})",
            "        gname = go.get('name', '')",
            "        _g_if = (go.get('if_expr') or g.get('if_expr') or '').strip()",
            "        _g_in = (go.get('in_expr') or g.get('in_expr') or '').strip()",
            "        g_df = _dash_qualified_frame(df, _g_if, _g_in, 'graph %r' % gname)",
            "        # One parser for both render modes.  It rejects an",
            "        # injection pattern by returning no variables, and names",
            "        # the sub-options dash does not implement.",
            "        _bv, _bcols, _btotal, _bmissing, _ = _dash_parse_by(",
            "            (go.get('by') or '').strip())",
            "        by_vars = [v for v in _bv.split() if v in df.columns]",
            "        if not by_vars:",
            "            figures[gname] = _dash_figure_for(g, gname, g_df)",
            "            continue",
            "        _btotal = _btotal or go.get('by_total', '0') == '1'",
            "        _bmissing = _bmissing or go.get('by_missing', '0') == '1'",
            "        # The QUALIFIED frame is what is grouped -- the saved",
            "        # renderer grouped the whole dataset until WP-11, and",
            "        # `if price > 4500, by(foreign)' faceted every row.",
            "        work_df = g_df if _bmissing else g_df.dropna(subset=by_vars)",
            "        if work_df.empty:",
            "            # Every by() value is missing: one empty panel, as saved.",
            "            figures[gname] = _dash_figure_for(g, gname, work_df)",
            "            continue",
            "        if gname not in linked_names:",
            "            graph_sources.pop(gname, None)",
            "        _gvars = []",
            "        for _pp in g.get('plots', []):",
            "            for _k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2', 'y1var', 'x1var', 'y2var', 'x2var'):",
            "                _v = _pp.get(_k, '')",
            "                if _v and _v in df.columns and _v not in _gvars:",
            "                    _gvars.append(_v)",
            "        _panels = []",
            "        _groupby = by_vars[0] if len(by_vars) == 1 else by_vars",
            "        for _key, _gdf in work_df.groupby(_groupby, sort=True, dropna=False):",
            "            _vals = (_key,) if len(by_vars) == 1 else _key",
            "            if not _bmissing and any(pd.isna(_v) for _v in _vals):",
            "                continue",
            "            _panels.append((_dash_facet_label(by_vars, _key, val_label_names, val_labels),",
            "                            _gdf, _key))",
            "        if _btotal:",
            "            _panels.append(('Total', work_df, None))",
            "        _entries = []",
            "        for _fi, (_label, _gdf, _key) in enumerate(_panels):",
            "            _fname = f'{gname}__by__{_fi}'",
            "            if gname in linked_names:",
            "                # A panel of a linked graph draws from the shared",
            "                # source through a view, as the saved one does.",
            "                linked_names.add(_fname)",
            "                graph_sources[_fname] = [shared_source]",
            "            else:",
            "                graph_sources[_fname] = [ColumnDataSource(",
            "                    {_v: _gdf[_v].tolist() for _v in _gvars})]",
            "            figures[_fname] = _dash_figure_for(",
            "                g, _fname, _gdf, _fac_label=_label)",
            "            _entries.append((_fname, _label))",
            "            _facet_group_vals[_fname] = (by_vars, _key)",
            "        _facet_map[gname] = _entries",
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
            "        # The card's OWN if()/in().  _compute_kpi used to be",
            "        # handed the whole frame, so a KPI qualified with",
            "        # `if foreign==1' served the unconditional number --",
            "        # a wrong answer presented as a right one.",
            "        _k_df = _dash_qualified_frame(",
            "            df, kpi.get('if_expr', ''), kpi.get('in_expr', ''),",
            "            'kpi %r' % kname, copy=False)",
            "        val = _compute_kpi(_k_df, kstat, kvar)",
            "        disp = _format_kpi(val, kfmt, kvar, kstat)",
            "        div_html = _dash_kpi_card(ktitle, disp, ksub, kcolor, kbg, kname)",
            "        kpi_divs[kname] = Div(text=div_html, sizing_mode='stretch_width',",
            "                              stylesheets=_dash_kpi_stylesheets())",
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
            "        _ftitle = _dash_filter_title(fspec.get('label', ''),",
            "                                     var_labels.get(fvar, fvar), ftype)",
            "        if fvar not in df.columns:",
            "            _dash_warn_filter_missing(fvar)",
            "            continue",
            "        # Value labels, by label set or directly by variable name.",
            "        lset = meta['val_label_names'].get(fvar, '')",
            "        vlabels = meta['val_labels'].get(lset, {}) if lset else {}",
            "        if not vlabels and isinstance(meta['val_labels'].get(fvar), dict):",
            "            vlabels = meta['val_labels'][fvar]",
            "        # The widget itself comes from the builder the saved renderer",
            "        # runs: option values, titles, steps and bounds are one rule.",
            "        widget, _sent = _dash_filter_widget(ftype, fvar, df[fvar], _ftitle, vlabels)",
            "        if widget is None:",
            "            if ftype not in _DASH_FILTER_TYPES:",
            "                _dash_warn_filter_type(fvar, ftype)",
            "            elif ftype in ('range', 'slider'):",
            "                warnings.warn(",
            "                    f\"dash: filter '{fvar}' type '{ftype}' requires numeric \"",
            "                    f\"data; skipping widget (use type(dropdown) for string \"",
            "                    f\"columns).\",",
            "                    stacklevel=2,",
            "                )",
            "            continue",
            "        widget._dash_var = fvar",
            "        widget._dash_exclude = fexcl",
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
            "    def _make_filter_cb(_trig_widget, _all_widgets, _all_sources, _agg_srcs, _kpi_divs, _kpi_defs, _df_ref, _fmap, _fgvals, _orig_src_data, _gquals, _gfac_to_orig, _redrawn=frozenset()):",
            "        def _on_filter_change(attr, old, new):",
            "            # 1. Build combined mask from all active widgets",
            "            mask = pd.Series([True] * len(_df_ref), index=_df_ref.index)",
            "            for w in _all_widgets:",
            "                wvar = getattr(w, '_dash_var', None)",
            "                if wvar is None or wvar not in _df_ref.columns:",
            "                    continue",
            "                _w_kind = getattr(w, '_dash_ftype', '')",
            "                if _w_kind == 'dropdown':",
            "                    # Use per-widget sentinel (may differ from '__all__' when data",
            "                    # contains the literal string '__all__').",
            "                    _w_sentinel = getattr(w, '_dash_sentinel', '__all__')",
            "                    if w.value != _w_sentinel:",
            "                        # The saved page's own match rule: both the",
            "                        # option value and the column go through",
            "                        # _dash_option_value, so '1' and '1.0' agree.",
            "                        mask &= _dash_dropdown_mask(_df_ref[wvar], w.value)",
            "                elif _w_kind == 'range':",
            "                    lo, hi = w.value",
            "                    mask &= (_df_ref[wvar] >= lo) & (_df_ref[wvar] <= hi)",
            "                elif _w_kind == 'slider':",
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
            "                    if id(src) in _redrawn:",
            "                        # A mapper-built source; the redraw below",
            "                        # refreshes it from the filtered frame.",
            "                        continue",
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
            "                # Redraw through the mapper.  This used to dispatch on",
            "                # agg['type'] to a second set of statistical helpers,",
            "                # _compute_<type>, that had drifted from the mappers",
            "                # they twinned: lowess returned x/y for a glyph bound",
            "                # to x_lw/y_lw, lfitci ignored n(), no site registered",
            "                # the plot options at all, and five branches were",
            "                # unreachable.  The mapper that drew the layer draws",
            "                # it again from the filtered frame, and its data is",
            "                # copied onto the live sources, so nothing can drift.",
            "                _fresh = agg['redraw'](agg_fdf)",
            "                for _live, _new in zip(agg['sources'], _fresh):",
            "                    _live.data = dict(_new.data)",
            "                if len(_fresh) != len(agg['sources']):",
            "                    warnings.warn(",
            "                        'dash: %s layer %d redrew %d source(s) where %d were '",
            "                        'expected; the layer may be stale.' % (",
            "                            agg.get('type'), key[1] + 1, len(_fresh), len(agg['sources'])),",
            "                        UserWarning)",
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
            "                _k_fdf = _dash_qualified_frame(",
            "                    fdf, kpi.get('if_expr', ''),",
            "                    kpi.get('in_expr', ''), 'kpi %r' % kname,",
            "                    copy=False)",
            "                val = _compute_kpi(_k_fdf, kpi.get('stat', 'mean'), kpi.get('var', ''))",
            "                disp = _format_kpi(val, kpi.get('fmt', ''),",
            "                                   kpi.get('var', ''),",
            "                                   kpi.get('stat', 'mean'))",
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
            "            _graph_qualifiers, _facet_to_orig, _redrawn_ids",
            "        )",
            "        # Every widget the builder made, whatever its class: a date",
            "        # slider is not a Slider subclass.",
            "        if hasattr(w, '_dash_var'):",
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
            "                _k_sel = _dash_qualified_frame(",
            "                    sel_df, kpi.get('if_expr', ''),",
            "                    kpi.get('in_expr', ''), 'kpi %r' % kname,",
            "                    copy=False)",
            "                val = _compute_kpi(_k_sel, kpi.get('stat', 'mean'), kpi.get('var', ''))",
            "                disp = _format_kpi(val, kpi.get('fmt', ''),",
            "                                   kpi.get('var', ''),",
            "                                   kpi.get('stat', 'mean'))",
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
            "    # Raw: the header builder escapes it exactly once.",
            "    subtitle_text = bo.get('subtitle', '') or ''",
            '',
            "    registry = bo.get('registry', '') or ''",
            "    # The registry as typed, graphs and KPI cards alike -- the",
            "    # saved renderer's rule as well now.",
            "    all_names = _dash_layout_order(registry, graphs, kpi_defs)",
            '',
            '    def _gopts_of(name):',
            '        for _gx in graphs:',
            "            if _gx.get('graph_options', {}).get('name') == name:",
            "                return _gx.get('graph_options', {})",
            '        return {}',
            '',
            '    def _dash_cell(name):',
            '        """The renderable for one registered name, or None -- the',
            '        resolver the saved grid and tabs use as well."""',
            '        return _dash_layout_cell(name, figures, _facet_map, kpi_divs, _gopts_of)',
            '',
            '    def _dash_placements(spec_str):',
            '        """Placements, through the saved renderer\'s own parser.',
            '',
            '        This used to be a second parser that required every',
            '        index to be at least 1, so layout(g1:0,0 g2:0,1) placed',
            '        both graphs when the dashboard was saved and was',
            '        discarded without a word when it was served.',
            '        """',
            '        return _dash_placement_map(spec_str, set(all_names))',
            '',
            '    def _dash_auto_cols(n):',
            '        if n == 0:',
            '            return 1',
            '        if n <= 2:',
            '            return n',
            '        return math.ceil(math.sqrt(n))',
            '',
            '    # ---- tabs() first: a tabbed element is not also in the grid ----',
            '    tabs_spec = _dash_parse_tabs(tabs_opt, all_names)',
            '    tabs_widget, placed_in_tabs = _dash_tab_panels(tabs_spec, _dash_cell)',
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
            "        # The same two classed Divs the saved renderer builds, with",
            "        # the scheme's CSS attached to them.",
            "        layout = column(*_dash_header_models(title_text, subtitle_text,",
            "                                             _DASH_SCHEME.css_block()),",
            "                        layout, sizing_mode='stretch_width')",
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
            "    # Bind loopback unless the operator asks otherwise.",
            "    # Passing no address at all makes Bokeh listen on every",
            "    # interface -- measured as ('0.0.0.0', port) and",
            "    # ('::', port) -- so `dash serve' on a laptop served the",
            "    # whole embedded dataset to the local network. The only",
            "    # gate was allow_websocket_origin, which filters a header",
            "    # the CLIENT supplies: a client that omits Origin, or",
            "    # forges localhost:<port>, completed the handshake.",
            "    # --address 0.0.0.0 still opens it deliberately.",
            "    _kw = {'address': address or '127.0.0.1'}",
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

def _validate_output_path(output_path: str, mode: str) -> str:
    """Refuse an output path this renderer should not write to.

    ``dash.ado`` validates ``saving()`` before it ever gets here, but this
    module is also a command-line program -- the ``--output`` argument below
    reaches ``main()`` with nothing checked at all. The checks mirror
    ``_dash_validate_path`` so the two routes agree about what is
    acceptable; a path that Stata refuses must not be writable by invoking
    the renderer directly.

    Returns the path unchanged, so it can be used inline.
    """
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("dash_render: --output must be a non-empty path.")

    path = output_path

    # A `..` SEGMENT, not the two characters anywhere: `my..report.html` is
    # an ordinary file name and is accepted, as it is on the Stata side.
    parts = re.split(r"[/\\]", path)
    if any(p == ".." for p in parts):
        raise ValueError(
            "dash_render: --output may not contain a '..' path segment "
            "(path traversal not allowed): %r" % (output_path,)
        )

    base = parts[-1] if parts else path
    if base.startswith("-"):
        raise ValueError(
            "dash_render: --output file name may not start with '-'; a shell "
            "would read it as an option: %r" % (output_path,)
        )

    # Control characters have no place in a path and are the usual way a
    # crafted value smuggles a newline into a log or a shell.
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in path):
        raise ValueError(
            "dash_render: --output contains control characters: %r"
            % (output_path,)
        )

    expected = ".py" if mode == "server" else ".html"
    if not base.lower().endswith(expected):
        raise ValueError(
            "dash_render: --output must end in %s for mode %r (got %r)"
            % (expected, mode, output_path)
        )

    return output_path


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
    # The mode is checked BEFORE the path: the expected extension depends on
    # it, so an unknown mode validated against a guessed extension reports
    # the wrong thing. test_server.py::test_main_raises_on_serve_mode caught
    # exactly that -- mode "serve" with a .py output complained about the
    # extension instead of the mode.
    if mode not in ("standalone", "server"):
        raise ValueError(
            f"dash_render: unknown mode '{mode}'. Expected 'standalone' or 'server'."
        )

    _validate_output_path(output_path, mode)

    if mode == "server":
        # --port used to stop here: this call passed three arguments and no
        # port, so every generated app embedded _port = 5006 whatever the
        # user asked for.  `dash serve' did not notice because it passes
        # --port again to the app it launches; `dash build, saving(app.py)
        # server' followed by `python app.py' -- the documented non-blocking
        # route -- served on 5006 regardless.
        builder = ServerAppBuilder(master_spec_path, data_json_path)
        builder.build(output_path, port=max(1024, min(int(port), 65535)))
    else:
        renderer = DashRenderer(master_spec_path, data_json_path)
        html_content = renderer.render()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)


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
