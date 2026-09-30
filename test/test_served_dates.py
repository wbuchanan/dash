"""test_served_dates.py -- the served app reads a Stata date as the saved
page does, and a number given for a date axis is a Stata date (WP-27).

Two BUGS.md entries:

* "The generated server app has no date handling at all".  Measured
  23sep2026 at 4ede074: a line of mpg over a %td ``when`` drew a
  DatetimeAxis with the tooltip ``@{when}{%F}`` saved, and a LinearAxis over
  the raw day numbers 15340, 15341, ... with ``@{when}`` served.  The served
  loader coerced every column with ``pd.to_numeric`` and nothing converted
  the columns a figure draws; KPI cards showed the day number, a range or
  slider filter over a date was a plain RangeSlider/Slider over day numbers.
  The served app now loads its frame through the saved loader's own column
  reader (``_dash_load_columns``), so every figure, tooltip, card, widget
  and filter move is drawn from the same datetime64[ms] columns.

* "A number given for a date axis is read as epoch milliseconds".
  Measured 24sep2026 (WP-25): on a %td axis ``xline(14979)`` was drawn at
  1970-01-01 00:00:14.979 where Stata draws 04jan2001; ``xscale(range(14977
  14980))`` and ``xlabel(14977 14979)`` placed their bounds and ticks in
  1970 too.  twoway reads a number on a date axis as a value of the
  variable, in its unit: days for %td, milliseconds for %tc, periods for
  %tw/%tm/%tq/%th, years for %ty.

Every expected date is Stata's: ``display %tdCCYY-NN-DD 14979`` is
2001-01-04 (the BUGS.md measurement), and 492 (%tm), 164 (%tq), 82 (%th),
2132 (%tw) and 2001 (%ty) are each Stata's first period of 2001 by the
definitions ``_stata_dates_to_datetime`` holds to Stata's measured values
(test_date_range.py).  Epoch milliseconds are days after 01jan1970 times
86,400,000: 2001-01-01 is 978307200000 and 2001-01-04 978566400000.
"""
import json
import math
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (DatetimeAxis, Div, DateRangeSlider, DateSlider,
                          FixedTicker, GlyphRenderer, HoverTool, LinearAxis,
                          Plot, Range1d, RangeSlider, Select, Slider, Span)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_date_range import (_COMPUTED, _DATES, _HALF_GAP, _HI_MS,  # noqa: E402
                             _ISO, _LO_MS, _MS, _PAST, _card, _filter, _frame,
                             _iso, _kpi, _outside, _plot_for, _saved, _served,
                             _spec, _spread_frame, _x_extents)

_DAY = 86_400_000.0
_JAN1_2001 = 978307200000.0
_JAN4_2001 = 978566400000.0


def _figs(doc):
    return [p for p in doc.select({"type": Plot})]


def _served_fig(doc):
    (fig,) = _figs(doc)
    return fig


def _hover_tooltips(fig):
    return [list(t.tooltips or []) for t in fig.tools
            if isinstance(t, HoverTool)]


def _hover_formatters(fig):
    return [dict(t.formatters or {}) for t in fig.tools
            if isinstance(t, HoverTool)]


def _served_widgets(doc, cls):
    return [w for w in doc.select({"type": cls})
            if hasattr(w, "_dash_var")]


def _fire(widget, value):
    """Set the widget and run the app's own change callbacks, as Bokeh does
    after a browser event (test_mode_parity.py's rule)."""
    widget.value = value
    for key in ("value", "value_throttled"):
        for cb in list(widget._callbacks.get(key, [])):
            cb("value", None, value)


def _drawn(fig, var="date"):
    """The ISO dates of every glyph source that carries *var*."""
    out = []
    for r in fig.renderers:
        if isinstance(r, GlyphRenderer) and var in r.data_source.data:
            out.append([_iso(v) for v in r.data_source.data[var]])
    return out


_LINE = [{"type": "line", "yvar": "close", "xvar": "date", "options": {}}]
_SCATTER = [{"type": "scatter", "yvar": "close", "xvar": "date",
             "options": {}}]


# ===========================================================================
# 1. The served figure: a date axis, date coordinates, a date tooltip
# ===========================================================================

class TestTheServedFigureReadsTheDateAsTheSavedOne:

    def test_the_x_axis_is_a_date_axis(self, tmp_path):
        """The BUGS.md case: LinearAxis served, DatetimeAxis saved."""
        r, _w = _saved(tmp_path, _spec(_LINE), _frame())
        doc, _w = _served(tmp_path, _spec(_LINE), _frame())
        assert any(isinstance(a, DatetimeAxis) for a in r.figures["g1"].xaxis)
        fig = _served_fig(doc)
        assert [type(a).__name__ for a in fig.xaxis] == [
            type(a).__name__ for a in r.figures["g1"].xaxis]
        assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis)

    def test_the_tooltip_writes_the_date(self, tmp_path):
        r, _w = _saved(tmp_path, _spec(_LINE), _frame())
        doc, _w = _served(tmp_path, _spec(_LINE), _frame())
        fig = _served_fig(doc)
        assert _hover_tooltips(fig) == _hover_tooltips(r.figures["g1"])
        # GAPS2 E3/G6, WP-28 S12: a Stata-format hover, not {%F}.
        assert any(("date", "@{date}{custom}") in t
                   for t in _hover_tooltips(fig))
        # GAPS2 E3/G6, WP-28 S12: each figure holds its own CustomJSHover
        # model, so compare what they are (type, code, args), not identity.
        def _fm(f):
            return [{k: (type(v).__name__, getattr(v, "code", v),
                         dict(getattr(v, "args", {}) or {}))
                     for k, v in d.items()} for d in _hover_formatters(f)]
        assert _fm(fig) == _fm(r.figures["g1"])

    def test_the_line_draws_every_date_the_saved_one_draws(self, tmp_path):
        """Stata's dates, 31dec9999 included, not its day numbers."""
        doc, _w = _served(tmp_path, _spec(_LINE), _frame())
        drawn = _drawn(_served_fig(doc))
        assert drawn and all(d == _ISO for d in drawn), drawn

    @pytest.mark.parametrize("kind,values,iso", [
        # `display %tdCCYY-NN-DD 14977' 2001-01-02.
        ("td", [14977.0, 14979.0], ["2001-01-02", "2001-01-04"]),
        # tc: 14979 days of milliseconds after 01jan1960.
        ("tc", [14979 * _DAY, 14980 * _DAY], ["2001-01-04", "2001-01-05"]),
        ("tw", [2132.0, 2133.0], ["2001-01-01", "2001-01-08"]),
        ("tm", [492.0, 493.0], ["2001-01-01", "2001-02-01"]),
        ("tq", [164.0, 165.0], ["2001-01-01", "2001-04-01"]),
        ("th", [82.0, 83.0], ["2001-01-01", "2001-07-01"]),
        ("ty", [2001.0, 2002.0], ["2001-01-01", "2002-01-01"]),
    ])
    def test_every_kind_is_drawn_and_labelled_as_saved(self, tmp_path, kind,
                                                       values, iso):
        spec = _spec(_LINE, formats={"date": "%" + kind})
        df = _frame(values)
        r, _w = _saved(tmp_path, spec, df)
        doc, _w = _served(tmp_path, spec, df)
        fig, sfig = _served_fig(doc), r.figures["g1"]
        assert all(d == iso for d in _drawn(fig)), _drawn(fig)
        assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis)
        # The tick formatter matched to the kind, as the saved one.
        assert (fig.xaxis[0].formatter.properties_with_values()
                == sfig.xaxis[0].formatter.properties_with_values())

    def test_a_date_on_the_y_axis(self, tmp_path):
        plots = [{"type": "line", "yvar": "date", "xvar": "close",
                  "options": {}}]
        doc, _w = _served(tmp_path, _spec(plots), _frame())
        fig = _served_fig(doc)
        assert any(isinstance(a, DatetimeAxis) for a in fig.yaxis)
        assert not any(isinstance(a, DatetimeAxis) for a in fig.xaxis)

    def test_a_date_and_a_number_on_one_axis_is_no_date_axis(self, tmp_path):
        """The saved rule (_figure_date_kind): two layers disagreeing about
        the x's kind get a numeric axis, and say nothing."""
        plots = [{"type": "line", "yvar": "close", "xvar": "date",
                  "options": {}},
                 {"type": "scatter", "yvar": "close", "xvar": "close",
                  "options": {}}]
        r, _w = _saved(tmp_path, _spec(plots), _frame())
        doc, _w = _served(tmp_path, _spec(plots), _frame())
        assert [type(a).__name__ for a in _served_fig(doc).xaxis] == [
            type(a).__name__ for a in r.figures["g1"].xaxis]

    def test_xscale_log_on_a_date_axis_warns_and_draws_dates(self, tmp_path):
        spec = _spec(_LINE, graph_options={"xscale": "log"})
        _r, sw = _saved(tmp_path, spec, _frame())
        doc, vw = _served(tmp_path, spec, _frame())
        want = [m for m in sw if "xscale(log) is meaningless" in m]
        assert want and [m for m in vw if "xscale(log)" in m] == want
        assert any(isinstance(a, DatetimeAxis)
                   for a in _served_fig(doc).xaxis)

    @pytest.mark.parametrize("ptype", _COMPUTED)
    def test_every_layer_is_drawn_where_the_saved_one_is(self, tmp_path,
                                                         ptype):
        """Every plot type that reads a date column: the served x extents
        are the saved page's, in milliseconds on the date axis."""
        opts = ({"mlabel": "date"} if ptype in ("rscatter", "pcscatter")
                else {})
        spec = _spec([_plot_for(ptype, opts)])
        r, _w = _saved(tmp_path, spec, _spread_frame())
        doc, _w = _served(tmp_path, spec, _spread_frame())
        served = sorted(_x_extents(_served_fig(doc)))
        saved = sorted(_x_extents(r.figures["g1"]))
        assert served == saved
        assert served and all(_LO_MS - _HALF_GAP <= e[2]
                              and e[3] <= _HI_MS + _HALF_GAP for e in served)

    def test_a_by_graph_over_dates(self, tmp_path):
        df = _spread_frame()
        df["grp"] = [float(i % 2) for i in range(12)]
        spec = _spec([_plot_for("line")], graph_options={"by": "grp"})
        r, _w = _saved(tmp_path, spec, df)
        doc, _w = _served(tmp_path, spec, df)
        figs = _figs(doc)
        assert len(figs) == 2
        for fig in figs:
            assert any(isinstance(a, DatetimeAxis) for a in fig.xaxis)
        served = sorted(sorted(_x_extents(f)) for f in figs)
        saved = sorted(sorted(_x_extents(r.figures[k]))
                       for k in ("g1__by__0", "g1__by__1"))
        assert served == saved

    def test_a_hover_date_on_a_numeric_axis(self, tmp_path):
        spec = _spec([{"type": "scatter", "yvar": "close", "xvar": "close",
                       "options": {}}], graph_options={"hover": "date"})
        r, _w = _saved(tmp_path, spec, _frame())
        doc, _w = _served(tmp_path, spec, _frame())
        fig = _served_fig(doc)
        assert _hover_tooltips(fig) == _hover_tooltips(r.figures["g1"])
        # GAPS2 E3/G6, WP-28 S12: a Stata-format hover, not {%F}.
        assert any(("date", "@{date}{custom}") in t
                   for t in _hover_tooltips(fig))

    def test_a_date_past_statas_range_is_one_missing_point(self, tmp_path):
        """Alone, counted once, in the same words as the saved page."""
        df = _frame(_DATES[:4] + [_PAST])
        _r, sw = _saved(tmp_path, _spec(_SCATTER), df)
        doc, vw = _served(tmp_path, _spec(_SCATTER), df)
        assert _outside(vw) == _outside(sw) and len(_outside(vw)) == 1
        (col,) = _drawn(_served_fig(doc))
        assert col == _ISO[:4]


# ===========================================================================
# 2. KPI cards
# ===========================================================================

class TestTheServedKpiReadsTheDate:

    def test_max_and_min_are_dates(self, tmp_path):
        kpis = [_kpi("k1", "max"), _kpi("k2", "min")]
        doc, _w = _served(tmp_path, _spec(_LINE, kpis=kpis), _frame())
        texts = {d.text for d in doc.select({"type": Div})}
        cards = {n: [_card(t, n) for t in texts if _card(t, n)]
                 for n in ("k1", "k2")}
        # `display %td 2936549' 31dec9999; `display %td 14977' 02jan2001.
        assert cards == {"k1": ["31 Dec 9999"], "k2": ["02 Jan 2001"]}

    def test_a_sum_of_dates_is_named_as_the_saved_page_names_it(
            self, tmp_path):
        kpis = [_kpi("k1", "sum")]
        _r, sw = _saved(tmp_path, _spec(_LINE, kpis=kpis), _frame())
        _doc, vw = _served(tmp_path, _spec(_LINE, kpis=kpis), _frame())
        want = [m for m in sw if "adds up dates" in m]
        assert want and [m for m in vw if "adds up dates" in m] == want

    def test_count_of_a_date_is_a_count(self, tmp_path):
        doc, _w = _served(tmp_path, _spec(_LINE, kpis=[_kpi("k1", "count")]),
                          _frame())
        texts = [d.text for d in doc.select({"type": Div})]
        assert [_card(t, "k1") for t in texts if _card(t, "k1")] == ["5"]


# ===========================================================================
# 3. Filters over a date, and a move of each
# ===========================================================================

class TestTheServedDateFilter:

    def test_a_range_is_a_date_range_over_every_date(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("range")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, DateRangeSlider)
        assert (w.start, w.end) == (_MS[0], _MS[-1])
        assert tuple(w.value) == (_MS[0], _MS[-1])

    def test_a_slider_is_a_date_slider_over_every_date(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("slider")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, DateSlider)
        assert (w.start, w.end, w.value) == (_MS[0], _MS[-1], _MS[0])

    def test_a_dropdown_lists_what_the_saved_one_lists(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("dropdown")])
        r, _w = _saved(tmp_path, spec, _frame())
        doc, _w = _served(tmp_path, spec, _frame())
        (sw,) = [w for w in r.filter_widgets if isinstance(w, Select)]
        (vw,) = _served_widgets(doc, Select)
        assert vw.options == sw.options

    def test_a_range_move_keeps_the_dates_inside_it(self, tmp_path):
        """02jan2001 to 05jan2001: four points, and the card's max is
        05 Jan 2001 (the saved page's callback gives the same,
        test_date_range.py)."""
        spec = _spec(_SCATTER, filters=[_filter("range")],
                     kpis=[_kpi("k1", "max")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, DateRangeSlider)
        _fire(w, (_MS[0], _MS[3]))
        assert _drawn(_served_fig(doc)) == [_ISO[:4]]
        texts = [d.text for d in doc.select({"type": Div})]
        assert [_card(t, "k1") for t in texts if _card(t, "k1")] == [
            "05 Jan 2001"]
        _fire(w, (_MS[0], _MS[4]))
        assert _drawn(_served_fig(doc)) == [_ISO]

    def test_a_slider_move_keeps_the_dates_from_it(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("slider")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, DateSlider)
        _fire(w, _MS[2])
        assert _drawn(_served_fig(doc)) == [_ISO[2:]]

    def test_a_dropdown_move_keeps_its_one_date(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("dropdown")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, Select)
        _fire(w, w.options[2][0])
        assert _drawn(_served_fig(doc)) == [[_ISO[1]]]

    def test_a_redrawn_layer_stays_on_the_date_axis_after_a_move(
            self, tmp_path):
        """An lfit over dates, refitted from the rows the move keeps: every
        x it draws lies among them, in milliseconds."""
        spec = _spec([_plot_for("scatter"), _plot_for("lfit")],
                     filters=[_filter("range")])
        doc, _w = _served(tmp_path, spec, _spread_frame())
        (w,) = _served_widgets(doc, DateRangeSlider)
        hi = _LO_MS + 150 * _DAY
        _fire(w, (_LO_MS, hi))
        ext = _x_extents(_served_fig(doc))
        assert ext and all(_LO_MS - _HALF_GAP <= e[2] and e[3] <= hi
                           for e in ext), ext
        doc.to_json()

    def test_a_move_on_a_numeric_filter_keeps_the_dates(self, tmp_path):
        spec = _spec(_SCATTER, filters=[_filter("range", "close")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, RangeSlider)
        _fire(w, (2.0, 3.0))
        assert _drawn(_served_fig(doc)) == [_ISO[1:3]]
        doc.to_json()

    def test_a_missing_date_survives_a_move(self, tmp_path):
        """A NaT in a list failed the page's JSON (test_dates.py); the move
        writes the column as an array."""
        df = _frame(_DATES[:3] + [math.nan, _DATES[4]])
        spec = _spec([{"type": "scatter", "yvar": "close", "xvar": "close",
                       "options": {}}], filters=[_filter("range", "close")],
                     graph_options={"hover": "date"})
        doc, _w = _served(tmp_path, spec, df)
        (w,) = _served_widgets(doc, RangeSlider)
        _fire(w, (1.0, 4.0))
        doc.to_json()


class TestHostileDateFilterValues:
    """A client sets a widget's value; whatever it sends, the move runs to
    the end and the document still writes."""

    @pytest.mark.parametrize("value", [
        (-1e300, 1e300), (float("nan"), float("nan")), (0, 0),
        (_MS[4], _MS[0])])
    def test_a_range_value_never_raises(self, tmp_path, value):
        spec = _spec(_SCATTER, filters=[_filter("range")])
        doc, _w = _served(tmp_path, spec, _frame())
        (w,) = _served_widgets(doc, DateRangeSlider)
        w.value = value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for cb in list(w._callbacks.get("value_throttled", [])):
                cb("value", None, value)
        doc.to_json()

    def test_an_unreadable_bound_restricts_to_nothing_drawn(self):
        df = pd.DataFrame({"d": pd.Series(
            np.array(["2001-01-02", "2001-01-03"], dtype="datetime64[ms]"))})
        w = RangeSlider(start=0, end=1, value=(0, 1), step=1)
        w._dash_var, w._dash_ftype = "d", "range"
        w.value = (float("nan"), float("nan"))
        assert list(dr._dash_frame_filter_mask(df, [w])) == [False, False]

    def test_a_date_mask_reads_datetime_and_number_bounds_alike(self):
        import datetime as _dt
        df = pd.DataFrame({"d": pd.Series(np.array(
            ["2001-01-02", "2001-01-03", "2001-01-04"],
            dtype="datetime64[ms]"))})
        w = DateRangeSlider(start=_MS[0], end=_MS[2], value=(_MS[0], _MS[2]))
        w._dash_var, w._dash_ftype = "d", "range"
        w.value = (_MS[1], _MS[2])
        by_ms = list(dr._dash_frame_filter_mask(df, [w]))
        w.value = (_dt.date(2001, 1, 3), _dt.date(2001, 1, 4))
        assert list(dr._dash_frame_filter_mask(df, [w])) == by_ms == [
            False, True, True]


# ===========================================================================
# 4. One loader for both modes
# ===========================================================================

class TestOneColumnReader:

    def test_the_app_loads_through_the_saved_reader(self, tmp_path):
        """The served app carries the saved loader's column reader and
        calls it, where it coerced every column with pd.to_numeric."""
        from test_date_range import _write
        sp, dp = _write(tmp_path, _spec(_LINE), _frame())
        ap = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_load_columns(" in src
        loader = src[src.index("def _load_spec_and_data"):]
        loader = loader[:loader.index("\n\n\n")]
        assert "_dash_load_columns(" in loader
        code = "\n".join(ln.split("#")[0] for ln in loader.splitlines())
        assert "pd.to_numeric" not in code

    def test_the_reader_converts_dates_and_numbers(self):
        df = pd.DataFrame({"d": [14977.0, None], "n": ["1", "x"],
                           "s": ["a", "b"]})
        dvars, nfmts = dr._dash_load_columns(
            df, {"d": "%td", "n": "%9.2fc", "s": "%td"}, {"s"})
        assert dvars == {"d": "td"} and nfmts == {"n": "%9.2fc"}
        assert [_iso(v) for v in df["d"]] == ["2001-01-02", None]
        assert str(df["d"].dtype) == "datetime64[ms]"
        assert df["n"].tolist()[0] == 1.0 and math.isnan(df["n"].tolist()[1])
        assert df["s"].tolist() == ["a", "b"]

    def test_a_hostile_format_is_no_date(self):
        df = pd.DataFrame({"d": [1.0]})
        dvars, _ = dr._dash_load_columns(
            df, {"d": "%tq" + "x" * 100000}, set())
        # Any %t<kind> prefix is the kind, as _stata_date_kind reads it.
        assert dvars == {"d": "tq"}
        df = pd.DataFrame({"d": [1.0]})
        dvars, _ = dr._dash_load_columns(df, {"d": ["%td"]}, set())
        assert dvars == {}

    def test_a_million_dates_load_in_bounded_time(self):
        """Vectorised: no Python loop per row."""
        df = pd.DataFrame({"d": np.arange(1_000_000, dtype=float)})
        t0 = time.perf_counter()
        dr._dash_load_columns(df, {"d": "%td"}, set())
        assert time.perf_counter() - t0 < 5.0
        assert str(df["d"].dtype) == "datetime64[ms]"


# ===========================================================================
# 5. A number given for a date axis is a Stata date in the variable's unit
# ===========================================================================

#: (kind, the Stata value of the first period of 2001, its epoch ms).
_KIND_POINTS = [
    ("td", 14979.0, _JAN4_2001),
    ("tc", 14979 * _DAY, _JAN4_2001),
    ("tw", 2132.0, _JAN1_2001),
    ("tm", 492.0, _JAN1_2001),
    ("tq", 164.0, _JAN1_2001),
    ("th", 82.0, _JAN1_2001),
    ("ty", 2001.0, _JAN1_2001),
]


def _both(tmp_path, spec, df):
    r, sw = _saved(tmp_path, spec, df)
    doc, vw = _served(tmp_path, spec, df)
    return [("saved", r.figures["g1"], sw), ("served", _served_fig(doc), vw)]


def _kind_frame(kind, value):
    step = _DAY if kind == "tc" else 1.0
    return _frame([value - step, value, value + step])


def _spans(fig, dim):
    return [s.location for s in fig.center
            if isinstance(s, Span) and s.dimension == dim]


class TestANumberOnADateAxisIsAStataDate:

    def test_xline_on_a_td_axis_is_drawn_at_04jan2001(self, tmp_path):
        """The BUGS.md case: xline(14979) was 1970-01-01 00:00:14.979."""
        spec = _spec(_LINE, graph_options={"xline": "14979"})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            assert _spans(fig, "height") == [_JAN4_2001], mode

    @pytest.mark.parametrize("kind,value,ms", _KIND_POINTS)
    def test_xline_in_every_unit(self, tmp_path, kind, value, ms):
        spec = _spec(_LINE, formats={"date": "%" + kind},
                     graph_options={"xline": repr(value)})
        for mode, fig, _w in _both(tmp_path, spec, _kind_frame(kind, value)):
            assert _spans(fig, "height") == [ms], (mode, kind)

    @pytest.mark.parametrize("kind,value,ms", _KIND_POINTS)
    def test_xscale_range_in_every_unit(self, tmp_path, kind, value, ms):
        spec = _spec(_LINE, formats={"date": "%" + kind},
                     graph_options={"xscale": f"range({value!r} {value!r})"})
        # WP-28 B2: range() widens only; the data run one period either
        # side of it, so the axis spans them, padded (this pinned the
        # degenerate (ms, ms)).
        ends = []
        for mode, fig, _w in _both(tmp_path, spec, _kind_frame(kind, value)):
            assert isinstance(fig.x_range, Range1d), mode
            assert fig.x_range.start < ms < fig.x_range.end, mode
            ends.append((fig.x_range.start, fig.x_range.end))
        assert ends[0] == ends[1], ends

    def test_xscale_range_on_a_td_axis(self, tmp_path):
        """xscale(range(14977 14980)): 02jan2001 and 05jan2001 are dates,
        read in the variable's unit; range() widens only (WP-28 B2), so
        the axis spans the data's 02jan2001 to 31dec9999."""
        spec = _spec(_LINE, graph_options={"xscale": "range(14977 14980)"})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            # The hull the padded Range1d was drawn from (WP-28 B2): the
            # data's 9999-12-31 widens it far past 05jan2001.
            lo, hi = dr._dash_range_hull(fig.x_range)
            assert lo == pytest.approx(_MS[0], abs=1), mode
            assert hi == pytest.approx(_MS[4], abs=1), mode

    def test_one_range_value_inside_the_data_changes_nothing(self,
                                                              tmp_path):
        """Was test_one_range_bound_keeps_the_datas_other, which pinned the
        axis's start at 04jan2001: range() never narrows (WP-28 B2), and
        14979 is the third of the four dates, so the axis spans the data
        (02jan2001 to 05jan2001), padded, and is not narrowed to it."""
        spec = _spec(_LINE, graph_options={"xscale": "range(14979 .)"})
        df = _frame(_DATES[:4])
        for mode, fig, _w in _both(tmp_path, spec, df):
            assert isinstance(fig.x_range, Range1d), mode
            lo, hi = dr._dash_range_hull(fig.x_range)
            assert lo == pytest.approx(_MS[0], abs=1), mode
            assert hi == pytest.approx(_MS[3], abs=1), mode
            assert fig.x_range.start < _JAN4_2001, mode

    def test_xlabel_numbers_tick_at_their_dates(self, tmp_path):
        """xlabel(14977 14979): ticks at 02jan2001 and 04jan2001, written
        as dates."""
        spec = _spec(_LINE, graph_options={"xlabel": "14977 14979"})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            (ax,) = fig.xaxis
            assert isinstance(ax.ticker, FixedTicker), mode
            assert list(ax.ticker.ticks) == [_MS[0], _MS[2]], mode
            assert isinstance(ax, DatetimeAxis), mode

    def test_xlabel_text_labels_are_keyed_by_their_dates(self, tmp_path):
        spec = _spec(_LINE, graph_options={
            "xlabel": '14977 "start" 14979 "mid"'})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            (ax,) = fig.xaxis
            assert list(ax.ticker.ticks) == [_MS[0], _MS[2]], mode
            assert dict(ax.major_label_overrides) == {
                _MS[0]: "start", _MS[2]: "mid"}, mode
            assert json.loads(ax.formatter.args["labels"]) == {
                str(_MS[0]): "start", str(_MS[2]): "mid"}, mode

    def test_xtick_positions_are_dates(self, tmp_path):
        spec = _spec(_LINE, graph_options={"xtick": "14978"})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            (ax,) = fig.xaxis
            assert list(ax.ticker.args["extra"]) == [_MS[1]], mode

    @pytest.mark.parametrize("kind,value,ms", _KIND_POINTS)
    def test_yline_on_a_date_y_axis(self, tmp_path, kind, value, ms):
        plots = [{"type": "line", "yvar": "date", "xvar": "close",
                  "options": {}}]
        spec = _spec(plots, formats={"date": "%" + kind},
                     graph_options={"yline": repr(value)})
        for mode, fig, _w in _both(tmp_path, spec, _kind_frame(kind, value)):
            assert _spans(fig, "width") == [ms], (mode, kind)

    def test_a_numeric_axis_keeps_its_numbers(self, tmp_path):
        """No date variable on the axis: xline(2) is at 2."""
        spec = _spec([{"type": "line", "yvar": "date", "xvar": "close",
                       "options": {}}],
                     graph_options={"xline": "2", "xlabel": "1 3",
                                    "xscale": "range(1 4)"})
        for mode, fig, _w in _both(tmp_path, spec, _frame()):
            assert _spans(fig, "height") == [2.0], mode
            assert list(fig.xaxis[0].ticker.ticks) == [1.0, 3.0], mode
            # range() widens only (WP-28 B2): 1-4 inside close's 1-5.
            assert dr._dash_range_hull(fig.x_range) == pytest.approx(
                (1.0, 5.0)), mode

    def test_a_number_past_statas_range_is_named_and_not_drawn(
            self, tmp_path):
        """`display %td 2936550' prints the number: no date to draw at.
        Named once per option, in the same words in both modes; the lines
        that are dates are drawn."""
        spec = _spec(_LINE, graph_options={"xline": "2936550 14979 1e300"})
        got = []
        for mode, fig, w in _both(tmp_path, spec, _frame()):
            assert _spans(fig, "height") == [_JAN4_2001], mode
            notes = [m for m in w if "xline(" in m and "not a date" in m]
            assert len(notes) == 1, (mode, w)
            got.append(notes)
        assert got[0] == got[1]

    def test_a_thousand_positions_convert_at_once(self, tmp_path):
        vals = " ".join(str(14977 + i) for i in range(1000))
        spec = _spec(_LINE, graph_options={"xline": vals})
        r, _w = _saved(tmp_path, spec, _frame())
        spans = _spans(r.figures["g1"], "height")
        assert len(spans) == 1000 and spans[2] == _JAN4_2001

    def test_the_axis_reader(self):
        assert dr._dash_axis_positions([14979, "x", None, 2936550], "td") == [
            _JAN4_2001, None, None, None]
        assert dr._dash_axis_positions([14979.5], None) == [14979.5]
        assert dr._dash_axis_positions([], "td") == []
