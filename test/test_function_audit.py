"""Behavioural tests for the functions WP-24's function audit found
unexercised or unchecked (AC-24.3; CLAUDE.md rule 4).

The audit (``scripts/fncov/``) ran the whole suite under a standard-library
recorder and listed every function of dash_render.py -- and of the server
app it generates -- never executed, in either mode; then broke each executed
function on purpose (its body skipped) and ran the tests that execute it.
Each class below closes one finding, named in its docstring:

* ``never served``: the served app can run the function, and no test had
  ever made it -- so the function was checked in one mode only;
* ``survived``: every test that executes the function still passed with its
  body skipped -- executed only incidentally, with nothing checking it.

Every test here was mutation-checked (AC-24.1): the function under test was
broken in a scratch copy and the test seen to fail.  The mutation each class
was checked against is named in its docstring.
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.events import ButtonClick
from bokeh.models import (ColumnDataSource, Div, GlyphRenderer, HoverTool,
                          Plot, VArea)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, exec_app  # noqa: E402
import colour_bins as cb  # noqa: E402

_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


# ---------------------------------------------------------------------------
# Both modes from one spec
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


def _spec(plots, kpis=None, build_options=None, graph_options=None,
          if_expr=""):
    go = {"name": "g1"}
    go.update(graph_options or {})
    bo = {"layout": "auto", "link": "", "filter": "", "title": "",
          "subtitle": "", "registry": " ".join(
              ["g1"] + [k["name"] for k in (kpis or [])]),
          "tabs": "", "filter_position": "top", "level": "95",
          "formats": {}}
    bo.update(build_options or {})
    return {"graphs": [{"plots": plots, "graph_options": go,
                        "if_expr": if_expr, "in_expr": ""}],
            "kpis": list(kpis or []), "build_options": bo}


def _kpi(name, stat, var, if_expr="", **kw):
    k = {"name": name, "stat": stat, "var": var, "fmt": "", "title": name,
         "subtitle": "", "color": "", "bgcolor": "", "update": "filter",
         "if_expr": if_expr, "in_expr": ""}
    k.update(kw)
    return k


def _write(tmp_path, spec, df, strings=()):
    data = make_data_json(df)
    for key in ("variableIsString", "variableTypeIsString"):
        for s in strings:
            data["StataJSON"][key][s] = True
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _saved(tmp_path, spec, df, strings=()):
    """(renderer, warnings) from the saved-dashboard renderer."""
    sp, dp = _write(tmp_path, spec, df, strings)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r, [str(w.message) for w in caught]


def _app(tmp_path, spec, df, strings=()):
    """The generated app's namespace, its build warnings recorded."""
    sp, dp = _write(tmp_path, spec, df, strings)
    ap = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    assert _ATTACH in src
    ns = {"__name__": "fn_audit_app"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec_app(src.replace(_ATTACH, "pass"), ap, ns)
    return ns, [str(w.message) for w in built]


def _served(tmp_path, spec, df, strings=()):
    """(document, warnings) from one session of the generated app."""
    ns, built = _app(tmp_path, spec, df, strings)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return doc, built + [str(w.message) for w in caught]


def _card_value(text):
    """The shown value of a KPI card's HTML."""
    at = text.find('id="kpi_val_')
    assert at >= 0, text[:200]
    o = text.find(">", at)
    return text[o + 1:text.find("<", o)].strip()


def _saved_cards(r):
    return {k: _card_value(d.text) for k, d in r.kpi_divs.items()}


def _served_cards(doc):
    out = {}
    for d in doc.select({"type": Div}):
        t = d.text or ""
        at = t.find('id="kpi_val_')
        if at >= 0:
            name = t[at + len('id="kpi_val_'):t.find('"', at + 12)]
            out[name] = _card_value(t)
    return out


def _renderers(figs):
    return [r for f in figs for r in f.renderers
            if isinstance(r, GlyphRenderer)]


# ---------------------------------------------------------------------------
# _stata_if_to_pandas: inlist() and inrange(), against Stata itself
# ---------------------------------------------------------------------------

#: x over five observations -- 1, 2, 3, 4 and missing -- twice, so a row
#: set is not an accident of order; w is a distinct power of two per row,
#: so a KPI sum(w) names exactly the rows a qualifier selected.
_Q = pd.DataFrame({
    "x": [1.0, 2.0, 3.0, 4.0, np.nan] * 2,
    "w": [float(2 ** i) for i in range(10)],
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
})

#: StataNow 19.5 MP, 24sep2026, on x = 1, 2, 3, 4, . (the rows each
#: qualifier keeps, as values of x):
#:
#:     gen byte lo_missing   = inrange(x, ., 3)      1 2 3
#:     gen byte hi_missing   = inrange(x, 2, .)      2 3 4
#:     gen byte both_missing = inrange(x, ., .)      1 2 3 4
#:     gen byte plain        = inrange(x, 2, 3)      2 3
#:     gen byte lo_ext       = inrange(x, .a, 3)     1 2 3
#:     gen byte hi_ext       = inrange(x, 2, .z)     2 3 4
#:     gen byte list_missing = inlist(x, ., 1)       1 .
#:     gen byte list_plain   = inlist(x, 1, 4)       1 4
#:
#: A missing bound of inrange() -- . or an extended .a to .z -- is no
#: bound, a missing x is never in range, and inlist() finds a missing value
#: among its values.  (dash's data carries every missing value of x as NaN,
#: so a missing x is asked about only as ..)
_STATA_QUALIFIER_TRUTH = [
    ("inrange(x, ., 3)", {1.0, 2.0, 3.0}),
    ("inrange(x, 2, .)", {2.0, 3.0, 4.0}),
    ("inrange(x, ., .)", {1.0, 2.0, 3.0, 4.0}),
    ("inrange(x, 2, 3)", {2.0, 3.0}),
    ("inrange(x, .a, 3)", {1.0, 2.0, 3.0}),
    ("inrange(x, 2, .z)", {2.0, 3.0, 4.0}),
    ("inlist(x, ., 1)", {1.0, "."}),
    ("inlist(x, 1, 4)", {1.0, 4.0}),
]


def _rows_of(values):
    return [i for i, x in enumerate(_Q["x"])
            if (("." in values) if math.isnan(x) else (x in values))]


class TestQualifierFunctionsSelectStatasRows:
    """``_stata_if_to_pandas``'s ``_inlist`` and ``_inrange``.

    Audit: never served -- the app runs them for every graph, layer and KPI
    qualifier, and no test had put one through the app; the saved-renderer
    tests asserted only ``0 < rows < 74``, which a wrong translation passes.
    Mutations: each helper's body skipped; ``>=`` written as ``>`` in
    ``_inrange``; ``|`` written as ``&`` in ``_inlist``."""

    @pytest.mark.parametrize("expr,keep", _STATA_QUALIFIER_TRUTH)
    def test_the_saved_card_counts_statas_rows(self, tmp_path, expr, keep):
        want = sum(_Q["w"][i] for i in _rows_of(keep))
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     kpis=[_kpi("k1", "sum", "w", if_expr=expr)])
        r, _w = _saved(tmp_path, spec, _Q)
        assert _saved_cards(r)["k1"] == f"{want:g}", expr

    @pytest.mark.parametrize("expr,keep", _STATA_QUALIFIER_TRUTH)
    def test_the_served_card_counts_statas_rows(self, tmp_path, expr, keep):
        want = sum(_Q["w"][i] for i in _rows_of(keep))
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     kpis=[_kpi("k1", "sum", "w", if_expr=expr)])
        doc, _w = _served(tmp_path, spec, _Q)
        assert _served_cards(doc)["k1"] == f"{want:g}", expr

    def test_a_served_graph_draws_the_rows_inlist_keeps(self, tmp_path):
        spec = _spec([{"type": "scatter", "yvar": "w", "xvar": "weight",
                       "options": {}}], if_expr="inlist(x, 1, 4)")
        doc, _w = _served(tmp_path, spec, _Q)
        (rend,) = _renderers(doc.select({"type": Plot}))
        drawn = sorted(rend.data_source.data["w"])
        assert drawn == sorted(_Q["w"][i] for i in _rows_of({1.0, 4.0}))

    def test_string_arguments_are_data_in_both_modes(self, tmp_path):
        df = _Q.copy()
        df["make"] = ["AMC", "BMW", "Buick, Inc", "AMC", "Ford"] * 2
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     kpis=[_kpi("k1", "sum", "w",
                                if_expr='inlist(make, "AMC", "Buick, Inc")')])
        want = sum(df["w"][i] for i in range(10)
                   if df["make"][i] in ("AMC", "Buick, Inc"))
        r, _w = _saved(tmp_path, spec, df, strings=("make",))
        doc, _w2 = _served(tmp_path, spec, df, strings=("make",))
        assert _saved_cards(r)["k1"] == f"{want:g}"
        assert _served_cards(doc)["k1"] == f"{want:g}"

    def test_a_call_inside_the_arguments_runs_in_neither_mode(self, tmp_path):
        """Adversarial, injection: the rewrite happens BEFORE the whitelist,
        so a call smuggled into an argument must still be refused -- and
        refused means not run: the file it would create must not exist."""
        canary = tmp_path / "pwned"
        expr = "inlist(x, 1, open(%r, 'w'))" % str(canary)
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     kpis=[_kpi("k1", "sum", "w", if_expr=expr)])
        r, sw = _saved(tmp_path, spec, _Q)
        doc, vw = _served(tmp_path, spec, _Q)
        assert not canary.exists()
        # Refused, the qualifier is not applied, and the user is told.
        everything = f"{_Q['w'].sum():g}"
        assert _saved_cards(r)["k1"] == everything
        assert _served_cards(doc)["k1"] == everything
        for ws in (sw, vw):
            assert any("if_expr filter skipped" in w for w in ws), ws

    def test_an_enormous_inlist_is_refused_not_recursed(self, tmp_path):
        """Adversarial, exhaustion: a hand-written spec can carry an
        inlist() of any length, and its rewrite is an OR chain as deep as
        the list is long.  It must be refused quickly, in both modes, not
        crash pandas' recursive evaluator."""
        import time
        expr = "inlist(x, %s)" % ", ".join(["1"] * 5000)
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     kpis=[_kpi("k1", "sum", "w", if_expr=expr)])
        t0 = time.monotonic()
        r, sw = _saved(tmp_path, spec, _Q)
        doc, vw = _served(tmp_path, spec, _Q)
        assert time.monotonic() - t0 < 60
        everything = f"{_Q['w'].sum():g}"
        assert _saved_cards(r)["k1"] == everything
        assert _served_cards(doc)["k1"] == everything


# ---------------------------------------------------------------------------
# colorvar(): colorcuts() and colornlevels() bins
# ---------------------------------------------------------------------------

_LE, _DASH = chr(0x2264), chr(0x2013)   # ASCII source, whatever the editor


def _bins(options, values):
    """The bin label _apply_colorvar gives each value, and the factors."""
    gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
    src = ColumnDataSource({"v": list(values),
                            "y": [1.0] * len(values)})
    fig = figure()
    rend = fig.scatter(x="v", y="y", source=src)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gm._apply_colorvar(fig, rend, src, dict(options, colorvar="v"))
    # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
    return cb.colour_values(rend), list(cb.colour_mapper(rend).factors)


class TestColorCutsPutEachPointInItsLabelledBin:
    """``_apply_colorvar``'s interval branch, now the module-level
    ``_dash_colorvar_cuts``/``_dash_colorvar_bins`` (GAPS2 X2).

    Audit: survived -- its three tests read the legend's labels, which are
    built without it, so every point could be coloured into the wrong bin
    (or none) and they passed.  Never served.  Mutations: body skipped;
    ``side="left"`` written as ``side="right"`` (a value on a cut moves up a
    bin)."""

    def test_each_value_lands_in_the_bin_its_label_describes(self):
        got, factors = _bins({"colorcuts": "2000 3000"},
                             [1000.0, 2000.0, 2000.5, 3000.0, 3500.0,
                              np.nan])
        lo, mid, hi = f"{_LE}2,000", f"2,000{_DASH}3,000", ">3,000"  # WP-30 P1.23b: 2000 was wrong because twoway writes key numbers in %8.0gc whatever the variable's format (2,000)
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert got == [lo, lo, mid, mid, hi, None]
        assert factors == [lo, mid, hi]

    def test_a_cut_below_the_minimum_is_dropped_here_too(self):
        """GAPS2 X2: a cut below colorvar's minimum (500, min is 1000)
        gives the same three bins as the two cuts above it alone."""
        got, factors = _bins({"colorcuts": "500 2000 3000"},
                             [1000.0, 2000.0, 2000.5, 3000.0, 3500.0,
                              np.nan])
        lo, mid, hi = f"{_LE}2,000", f"2,000{_DASH}3,000", ">3,000"  # WP-30 P1.23b: 2000 was wrong because twoway writes key numbers in %8.0gc whatever the variable's format (2,000)
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert got == [lo, lo, mid, mid, hi, None]
        assert factors == [lo, mid, hi]

    def test_the_cuts_may_come_in_any_order(self):
        a, _f = _bins({"colorcuts": "3000 2000"}, [2500.0, 1000.0, 4000.0])
        b, _g = _bins({"colorcuts": "2000 3000"}, [2500.0, 1000.0, 4000.0])
        assert a == b == [f"2,000{_DASH}3,000", f"{_LE}2,000", ">3,000"]  # WP-30 P1.23b: 2000 was wrong because twoway writes key numbers in %8.0gc whatever the variable's format (2,000)

    def test_one_cut_makes_two_bins(self):
        got, factors = _bins({"colorcuts": "5"}, [4.0, 5.0, 6.0])
        assert got == [f"{_LE}5", f"{_LE}5", ">5"]
        assert factors == [f"{_LE}5", ">5"]

    @pytest.mark.parametrize("cuts", ["2000 abc", "2000; drop", "2000,3000"])
    def test_a_cut_list_that_is_not_numbers_bins_nothing(self, cuts):
        """Hostile: anything but a numlist is not a numlist."""
        gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
        src = ColumnDataSource({"v": [1000.0, 4000.0], "y": [1.0, 1.0]})
        fig = figure()
        rend = fig.scatter(x="v", y="y", source=src)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm._apply_colorvar(fig, rend, src,
                               {"colorvar": "v", "colorcuts": cuts})
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert not any(str(k).startswith(dr._DASH_CVAR_PREFIX)
                       for k in src.data)

    def test_the_served_scatter_colours_the_same_bins(self, tmp_path):
        df = pd.DataFrame({"mpg": [12.0, 20.0, 20.5, 30.0, 35.0],
                           "weight": [1.0, 2.0, 3.0, 4.0, 5.0]})
        plot = {"type": "scatter", "yvar": "weight", "xvar": "mpg",
                "options": {"colorvar": "mpg", "colorcuts": "20 30"}}
        doc, _w = _served(tmp_path, _spec([plot]), df)
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        (rend,) = cb.colour_renderers(doc)
        data = rend.data_source.data
        pairs = sorted(zip(data["mpg"], data[cb.colour_field(rend)]))
        assert pairs == [(12.0, f"{_LE}20"), (20.0, f"{_LE}20"),
                         (20.5, f"20{_DASH}30"), (30.0, f"20{_DASH}30"),
                         (35.0, ">30")]


class TestColorLevelsPutEachPointInItsLabelledBin:
    """``_apply_colorvar``'s equal-width branch, now the module-level
    ``_dash_colorvar_cuts``/``_dash_colorvar_bins`` called with
    ``closed_ends=True`` (GAPS2 X2): colorlevels()/colornlevels() label
    their outer bins with the column's own minimum and maximum, not an
    open ``<=``/``>``, since they divide the whole data range.

    Audit: survived -- ten tests execute it and read only how many factors
    the legend has.  Mutations: body skipped; the interior edges searched
    with ``side="right"``; the edges taken from ``np.linspace(lo, hi,
    nlevels)`` (one bin too few)."""

    def test_equal_width_bins_over_the_range(self):
        got, factors = _bins({"colornlevels": "2"},
                             [0.0, 4.0, 5.0, 5.5, 10.0, np.nan])
        a, b = f"0{_DASH}5", f"5{_DASH}10"
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert got == [a, a, a, b, b, None]
        assert factors == [a, b]

    def test_four_levels_each_take_their_quarter(self):
        got, _f = _bins({"colornlevels": "4"}, [0.0, 3.0, 6.0, 9.0, 12.0])
        assert got == [f"0{_DASH}3", f"0{_DASH}3", f"3{_DASH}6",
                       f"6{_DASH}9", f"9{_DASH}12"]

    def test_fewer_than_two_levels_is_two(self):
        got, factors = _bins({"colornlevels": "1"}, [0.0, 10.0])
        assert factors == [f"0{_DASH}5", f"5{_DASH}10"]
        assert got == factors

    def test_a_constant_variable_is_one_level(self):
        got, _f = _bins({"colornlevels": "3"}, [7.0, 7.0])
        assert len(set(got)) == 1

    def test_the_served_scatter_colours_the_same_bins(self, tmp_path):
        df = pd.DataFrame({"mpg": [10.0, 14.0, 15.0, 16.0, 20.0],
                           "weight": [1.0, 2.0, 3.0, 4.0, 5.0]})
        plot = {"type": "scatter", "yvar": "weight", "xvar": "mpg",
                "options": {"colorvar": "mpg", "colornlevels": "2"}}
        doc, _w = _served(tmp_path, _spec([plot]), df)
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        (rend,) = cb.colour_renderers(doc)
        data = rend.data_source.data
        a, b = f"10{_DASH}15", f"15{_DASH}20"
        assert sorted(zip(data["mpg"], data[cb.colour_field(rend)])) == [
            (10.0, a), (14.0, a), (15.0, a), (16.0, b), (20.0, b)]


# ---------------------------------------------------------------------------
# _dash_build_hover: the band fallback
# ---------------------------------------------------------------------------

class TestABandAloneStillGetsATooltip:
    """``_dash_build_hover``'s ``_band``.

    Audit: survived -- one test reaches it, with a band whose field is
    refused, where it returns None either way; no test ever saw it build a
    tooltip.  dash.sthlp promises one on every figure.  Mutation: body
    skipped (the band then gets no tooltip)."""

    def _fig(self, x="x_fit", y1="lo", y2="hi"):
        fig = figure()
        src = ColumnDataSource({x: [1.0, 2.0, 3.0], y1: [0.5, 1.5, 2.5],
                                y2: [1.5, 2.5, 3.5]})
        band = fig.add_glyph(src, VArea(x=x, y1=y1, y2=y2))
        return fig, band

    def test_the_band_answers_with_its_three_columns(self):
        fig, band = self._fig()
        dr._dash_build_hover(fig, "weight", "mpg", "", [],
                             var_labels={"weight": "Weight (lbs.)"})
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tool.renderers == [band]
        assert tool.mode == "mouse"
        labels = [lab for lab, _v in tool.tooltips]
        fields = [v.split("}")[0] for _l, v in tool.tooltips]
        assert labels == ["Weight (lbs.)", "y1", "y2"]
        assert fields == ["@{x_fit", "@{lo", "@{hi"]

    def test_a_band_of_dataset_variables_is_labelled_by_them(self):
        fig, _band = self._fig(x="year", y1="low", y2="high")
        dr._dash_build_hover(fig, "", "", "", [],
                             var_labels={"low": "Low price",
                                         "high": "High price"})
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert [lab for lab, _v in tool.tooltips] == [
            "x", "Low price", "High price"]

    def test_a_band_field_that_is_not_a_plain_name_gets_no_tooltip(self):
        """Adversarial, injection: a column named with markup must never
        become a tooltip field, where BokehJS parses `@{...}' as HTML."""
        bad = "hi}<img src=x onerror=alert(1)>"
        fig, _band = self._fig(y2=bad)
        dr._dash_build_hover(fig, "weight", "mpg", "", [])
        for t in fig.tools:
            if isinstance(t, HoverTool):
                assert "<img" not in str(t.tooltips)


# ---------------------------------------------------------------------------
# The served CSV download: calendar dates
# ---------------------------------------------------------------------------

def _epoch_ms(y, m, d=1):
    return float((pd.Timestamp(year=y, month=m, day=d)
                  - pd.Timestamp("1970-01-01")) // pd.Timedelta("1ms"))


class TestTheServedDownloadWritesCalendarDates:
    """``_stata_dates_to_datetime``'s ``_from_parts``, which builds a %tm,
    %tq, %th, %ty or %tw date from its year and month.

    Audit: never served -- the served download converts every Stata date it
    writes through it, and no test had downloaded one of these five kinds
    from the app.  Mutations: body skipped (every date NaT); the month
    taken as ``idx % 12`` without ``+ 1`` (every %tm date a month early).
    The truth is Stata's calendar: 0 is 1960m1, 1960q1, 1960h1 and 1960w1,
    and a %ty value is its year."""

    _CASES = [
        ("%tm", [0.0, 1.0, -1.0, 719.0],
         [(1960, 1), (1960, 2), (1959, 12), (2019, 12)]),
        ("%tq", [0.0, 5.0, -1.0], [(1960, 1), (1961, 4), (1959, 10)]),
        ("%th", [0.0, 1.0, 81.0], [(1960, 1), (1960, 7), (2000, 7)]),
        ("%ty", [1960.0, 2024.0], [(1960, 1), (2024, 1)]),
    ]

    def _download(self, tmp_path, fmt, values):
        df = pd.DataFrame({"mpg": [20.0 + i for i in range(len(values))],
                           "when": values})
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                       "options": {}}],
                     build_options={"csv": "1", "formats": {"when": fmt}})
        doc, _w = _served(tmp_path, spec, df)
        (btn,) = list(doc.select({"name": "dash_csv_download"}))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            btn._trigger_event(ButtonClick(btn))
        cb = btn.js_property_callbacks["change:tags"][0]
        return list(cb.args["src"].data["when"])

    @pytest.mark.parametrize("fmt,values,dates", _CASES)
    def test_each_period_is_its_first_day(self, tmp_path, fmt, values,
                                          dates):
        got = self._download(tmp_path, fmt, values)
        assert got == [_epoch_ms(y, m) for y, m in dates]

    def test_a_week_is_counted_from_the_first_of_january(self, tmp_path):
        # Stata's weeks restart every year: 1960w2 is 8 January, and
        # 1961w1 (value 52) is 1 January 1961.
        got = self._download(tmp_path, "%tw", [1.0, 52.0])
        assert got == [_epoch_ms(1960, 1, 8), _epoch_ms(1961, 1, 1)]

    def test_the_saved_loader_converts_the_same_way(self, tmp_path):
        df = pd.DataFrame({"mpg": [20.0, 21.0, 22.0],
                           "when": [0.0, 1.0, -1.0]})
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                       "options": {}}],
                     build_options={"formats": {"when": "%tm"}})
        r, _w = _saved(tmp_path, spec, df)
        assert list(r.df["when"]) == [pd.Timestamp("1960-01-01"),
                                      pd.Timestamp("1960-02-01"),
                                      pd.Timestamp("1959-12-01")]

    def test_a_missing_or_absurd_date_is_empty_not_an_error(self, tmp_path):
        """Hostile data: a missing month and one far past pandas' range
        convert to nothing, and the download still works."""
        got = self._download(tmp_path, "%tm", [0.0, float("nan"), 1e15])
        assert got[0] == _epoch_ms(1960, 1)
        assert all(v is None or (isinstance(v, float) and math.isnan(v))
                   for v in got[1:]), got


# ---------------------------------------------------------------------------
# filter(): an unknown type()
# ---------------------------------------------------------------------------

class TestAnUnknownFilterTypeIsNamedInBothModes:
    """``_dash_warn_filter_type``.

    Audit: never served -- the app calls it for a filter whose type() it
    cannot build, and no test had given the app one.  Mutation: body
    skipped (no warning; the widget is still left out)."""

    def _spec(self, ftype):
        return _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
                     build_options={"filters": [{"varname": "mpg",
                                                 "type": ftype}]})

    def test_both_modes_say_so_in_the_same_words(self, tmp_path):
        _r, sw = _saved(tmp_path, self._spec("checkbox"), _Q)
        _doc, vw = _served(tmp_path, self._spec("checkbox"), _Q)
        # Flipped (WP-31 H2f): the three types were the list until
        # type(multi).
        want = ("dash: filter(mpg, type(checkbox)): type() must be one of "
                "dropdown, range, slider, multi; no widget was built.")
        assert want in sw
        assert want in vw

    def test_no_widget_is_served_for_it(self, tmp_path):
        from bokeh.models import Select, Slider, RangeSlider
        doc, _w = _served(tmp_path, self._spec("checkbox"), _Q)
        assert not list(doc.select({"type": Select}))
        assert not list(doc.select({"type": Slider}))
        assert not list(doc.select({"type": RangeSlider}))

    def test_markup_in_the_type_is_not_echoed_raw(self, tmp_path):
        """Hostile: the type is echoed into a warning the Stata log shows;
        a control character or a newline must not reach it as written."""
        _doc, vw = _served(tmp_path, self._spec("x\nFAKE LINE\x1b[31m"), _Q)
        hits = [w for w in vw if "type() must be one of" in w]
        assert hits, vw
        assert all("\n" not in w and "\x1b" not in w for w in hits), hits


# ---------------------------------------------------------------------------
# The served app's own copies, for the helpers a hand-built figure reaches
# ---------------------------------------------------------------------------

_APP_NS = {}


def _app_ns(tmp_path_factory):
    """One generated app's namespace, built once for this file: its copies
    of dash_render.py's helpers are what a served session runs."""
    if not _APP_NS:
        ns, _w = _app(tmp_path_factory.mktemp("audit_app"), _spec(
            [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
              "options": {}}]), _Q)
        _APP_NS.update(ns)
    return _APP_NS


@pytest.fixture(scope="module", params=["saved", "served"])
def mode_ns(request, tmp_path_factory):
    """dash_render.py itself, then the generated app's copy of it."""
    if request.param == "saved":
        return vars(dr)
    return _app_ns(tmp_path_factory)


# ---------------------------------------------------------------------------
# _dash_build_hover: a range reads as a range
# ---------------------------------------------------------------------------

class TestARangeReadsAsARange:
    """``_dash_build_hover``'s ``_range``: a glyph whose source is a range's
    x, y1 and y2, and that draws neither an x nor a y, is described as the
    range -- the x, then the lower and the upper value, each under its
    variable's label -- ahead of the segment shape, which would describe the
    same glyph as four loose ends.

    Audit: survived -- 266 tests execute it (every fallback tooltip), all
    passed with its body skipped, and a probe of all 40 plot types drawn
    alone in both modes found none that reaches its tooltip: only a figure
    whose sources do not carry the graph's variables does.  Mutation: body
    skipped (the segment shape then answers with four rows)."""

    def _fig(self):
        from bokeh.models import Segment
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0],
                                "y1": [10.0, 20.0, 30.0],
                                "y2": [15.0, 26.0, 37.0]})
        seg = fig.add_glyph(src, Segment(x0="x", y0="y1", x1="x", y1="y2"))
        return fig, seg

    def test_three_rows_x_then_the_bounds(self, mode_ns):
        fig, seg = self._fig()
        mode_ns["_dash_build_hover"](
            fig, "weight", "mpg", "price", [],
            var_labels={"weight": "Weight (lbs.)", "mpg": "Mileage (mpg)",
                        "price": "Price"})
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tool.renderers == [seg]
        assert tool.mode == "mouse"
        assert [lab for lab, _v in tool.tooltips] == [
            "Weight (lbs.)", "Mileage (mpg)", "Price"]
        assert [v.split("}")[0] for _l, v in tool.tooltips] == [
            "@{x", "@{y1", "@{y2"]

    def test_unnamed_variables_fall_back_to_the_role(self, mode_ns):
        fig, _seg = self._fig()
        mode_ns["_dash_build_hover"](fig, "", "", "", [])
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert [lab for lab, _v in tool.tooltips] == ["x", "y1", "y2"]

    def test_a_source_short_of_y2_is_not_a_range(self, mode_ns):
        from bokeh.models import Segment
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y1": [1.0, 2.0],
                                "top": [3.0, 4.0]})
        fig.add_glyph(src, Segment(x0="x", y0="y1", x1="x", y1="top"))
        mode_ns["_dash_build_hover"](fig, "", "", "", [])
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        # The segment's four ends, not a range's three rows.
        assert len(tool.tooltips) == 4


# ---------------------------------------------------------------------------
# _tooltip_precision
# ---------------------------------------------------------------------------

class TestTooltipPrecisionFollowsTheSpread:
    """``_tooltip_precision``: the number format of every fallback tooltip,
    about four significant figures across the column's spread.

    Audit: named by no test; with its body skipped every fallback field
    read ``@{col}{None}`` and the 400 most focused of the 1,889 tests that
    execute it all passed.  Mutations: body skipped; ``4 -`` written as
    ``3 -`` (one figure fewer everywhere); the column read without the
    ``np.isfinite`` filter."""

    @pytest.mark.parametrize("values,fmt", [
        ([0.0, 1000.0], "0"),
        ([0.0, 1.0], "0.000"),
        ([0.0, 0.01], "0.00000"),
        ([12.0, 41.0], "0.00"),
        ([1.0, 2.0, 3.0, None], "0.000"),
        ([0.0, 1e9], "0"),
        ([0.0, 1e-12], "0.000000"),
    ])
    def test_about_four_significant_figures(self, mode_ns, values, fmt):
        assert mode_ns["_tooltip_precision"](values) == fmt

    def test_a_constant_column_is_read_against_its_value(self, mode_ns):
        f = mode_ns["_tooltip_precision"]
        assert f([5.0, 5.0]) == "0.000"
        assert f([2500.0, 2500.0]) == "0"
        assert f([0.0, 0.0]) == "0.000"

    @pytest.mark.parametrize("values", [[], ["a", "b"],
                                        [float("nan"), float("inf")],
                                        [1.0, float("inf"), float("-inf")]])
    def test_nothing_finite_to_spread_over(self, mode_ns, values):
        """Hostile columns: empty, text, only non-finite; and one finite
        value among infinities, which is read alone."""
        want = "0.000" if values and values[0] == 1.0 else "0.00"
        assert mode_ns["_tooltip_precision"](values) == want

    def test_a_bins_tooltip_carries_it(self, mode_ns):
        from bokeh.models import Quad
        fig = figure()
        src = ColumnDataSource({"left": [0.0, 250.0, 500.0],
                                "right": [250.0, 500.0, 750.0],
                                "top": [3.0, 5.0, 1.0],
                                "bottom": [0.0, 0.0, 0.0]})
        fig.add_glyph(src, Quad(left="left", right="right", top="top",
                                bottom="bottom"))
        mode_ns["_dash_build_hover"](fig, "", "", "", [], univar="price")
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tool.tooltips[0] == ("price", "@{left}{0.0} to @{right}{0.0}")


# ---------------------------------------------------------------------------
# A malformed immediate record, served
# ---------------------------------------------------------------------------

class TestAMalformedImmediateRecordIsRefusedServedToo:
    """``GlyphMapper._immediate_records``'s ``_bad``, which words the
    refusal of a scatteri, pci or pcarrowi record that is not one.

    Audit: never served -- the saved renderer's tests refuse such records,
    and none had handed one to the generated app, which reads the same
    records through the same copied method.  Mutations: ``_bad``'s body
    skipped (``raise None`` is a TypeError, not the refusal); its message's
    ``{names}`` dropped."""

    @pytest.mark.parametrize("ptype,values,why", [
        ("scatteri", [[1.0, "a"]], "has a coordinate that is not a number"),
        ("scatteri", [[1.0, 2.0, "label", 3, "extra"]], "is not one"),
        ("scatteri", [[True, 2.0]], "has a coordinate that is not a number"),
        ("pcarrowi", [[0.0, 0.0, 1.0]], "is not one"),
        ("pci", [["0; import os", 0.0, 1.0, 1.0]],
         "has a coordinate that is not a number"),
    ])
    def test_both_modes_refuse_it_in_the_same_words(self, tmp_path, ptype,
                                                    values, why):
        names = "y, x" if ptype == "scatteri" else "y1, x1, y2, x2"
        want = (f"dash: {ptype} records are [{names}], then an optional "
                f"label and clock position; ")
        spec = _spec([{"type": ptype, "values": values, "options": {}}])
        with pytest.raises(RuntimeError) as saved:
            _saved(tmp_path, spec, _Q)
        ns, _w = _app(tmp_path, spec, _Q)
        with pytest.raises(ValueError) as served:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ns["make_document"](Document())
        for msg in (str(saved.value), str(served.value)):
            assert want in msg, msg
            assert why in msg, msg

    def test_a_control_character_is_not_echoed_raw_either(self, tmp_path):
        """The saved renderer's refusal, likewise."""
        spec = _spec([{"type": "scatteri",
                       "values": [[1.0, "\x1b[31m\nFAKE", 3, 4, 5]],
                       "options": {}}])
        with pytest.raises(RuntimeError) as saved:
            _saved(tmp_path, spec, _Q)
        msg = str(saved.value)
        assert "scatteri records are" in msg
        assert "\x1b" not in msg and "\n" not in msg, msg

    def test_a_control_character_is_not_echoed_raw(self, tmp_path):
        """Hostile: the refused record is echoed into the error the Stata
        log shows; an escape sequence or a newline must not reach it."""
        spec = _spec([{"type": "scatteri",
                       "values": [[1.0, "\x1b[31m\nFAKE", 3, 4, 5]],
                       "options": {}}])
        ns, _w = _app(tmp_path, spec, _Q)
        with pytest.raises(ValueError) as served:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ns["make_document"](Document())
        msg = str(served.value)
        assert "\x1b" not in msg and "\n" not in msg, msg


# ---------------------------------------------------------------------------
# A colour key does not widen the first axis
# ---------------------------------------------------------------------------

def _figures(tmp_path, plots, mode):
    spec = _spec(plots)
    if mode == "saved":
        r, _w = _saved(tmp_path, spec, _Q)
        return list(r.figures.values())
    doc, _w = _served(tmp_path, spec, _Q)
    return list(doc.select({"type": Plot}))


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestAColourKeyDoesNotWidenTheFirstAxis:
    """``_dash_keep_primary_ranges``'s swatch rule: beside a second axis the
    figure's own range reads only the layers drawn on it -- and a discrete
    colour key's invisible swatches, which sit on the first axis, are not a
    layer and must not widen it either.

    Audit: the capped campaign reported the function survived (its 400 most
    focused of 6,871 executing tests); test_help_claims_7.py's
    ``TestTheSecondAxisIsItsOwn::test_the_first_axis_is_scaled_to_its_own_
    layers`` does check the range, and fails with the body skipped.  What
    nothing checked is the swatch rule: with ``and not _dash_is_swatch(r)``
    dropped, test_help_claims_7.py (913 tests), test_dual_axis.py and
    test_colorvar_legend.py all pass.  Mutations: the swatch filter
    dropped (fails served, where the range starts from every renderer);
    body skipped."""

    def test_a_colour_key_swatch_is_not_ranged_over(self, tmp_path, mode):
        (fig,) = _figures(tmp_path, [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"colorvar": "x", "colordiscrete": "1"}},
            {"type": "line", "yvar": "w", "xvar": "weight",
             "options": {"yaxis": "2"}}], mode)
        swatches = [r for r in fig.renderers
                    if str(getattr(r, "name", "") or "").startswith(
                        dr._DASH_SWATCH_PREFIX)]
        assert swatches, "no colour key was drawn"
        # WP-30 P1.3a: the y axis is now a Range1d over its layers' hull and
        # ticks (it listed renderers); the swatches are no part of it and
        # the scatter the key belongs to is.
        ext = dr._dash_layer_extent(
            [r for r in fig.renderers if r not in swatches],
            "y_range_name", "default")
        assert dr._dash_layer_extent(fig.renderers, "y_range_name",
                                     "default") == ext
        ticks = list(fig.yaxis[0].ticker.ticks)
        assert dr._dash_range_hull(fig.y_range) == pytest.approx(
            (min([ext[0]] + ticks), max([ext[1]] + ticks)))
