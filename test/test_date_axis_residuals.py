"""Date-axis residuals of WP-30 P1.23 (DROPIN-REMAINING.md:134-144).

Part b (section 17, P1.23b): date and format text in colour keys and in
the computed layers' tooltips.  Measured before the fix (both modes,
identical):

    scatter close open, colorvar(date)              bar on Bokeh's own ticker
                                                    (numbers near 9.8e+11)
    ... colorlevels(3)                              9.78394e+11-9.87898e+11 ...
    ... colorcuts(15100 15200)                      <=9.78394e+11, >9.78394e+11
    ... zlabel(, format(%td))                       'auto' plus a note
    scatter mpg weight, colorvar(price) colorcuts(5000 9000), price %9.0g
                                                    <=5000, 5000-9000, >9000
    histogram date                                  @{left}{0} (epoch ms), Count
    kdensity date                                   rows named x and y

twoway (StataNow 19.5, sysuse sp500, date %td 14977..15340) keys
``15,000 15,100 15,200 15,300 15,400``; colorlevels(3) ``15,098 15,219``;
colorcuts(15100 15200) ``15,100 15,200``; zlabel(, format(%td))
``25jan2001 05may2001 13aug2001 21nov2001 01mar2002``: Stata units in
``%8.0gc`` whatever the variable's display format, or zlabel()'s
format().  ``display %td 14977`` is ``02jan2001``.  The fixture
test/fixtures/key_text_truth.json (scripts/extract_key_text_truth.do)
holds every probe.

Part a (section 35, P1.23a) appends its classes below section 17's.
"""

import hashlib
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.embed import json_item
from bokeh.models import (ColorBar, ColumnDataSource, CustomJSHover,
                          FixedTicker, HoverTool, Legend, RangeSlider)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import colour_bins as cb  # noqa: E402
from conftest import exec_app  # noqa: E402
from test_date_range import (_ATTACH, _saved, _spec, _filter,  # noqa: E402
                             _write)
from test_display_format_sites import js_texts  # noqa: E402
from test_mode_parity import _fire  # noqa: E402
from js_runner import JsSession  # noqa: E402

MODES = ("saved", "served")
_TRUTH = os.path.join(_HERE, "fixtures", "key_text_truth.json")


def _ms(d):
    """A %td day as the page holds it: epoch milliseconds."""
    return (d - 3653) * 86400000.0


# sp500's first and last dates, so twoway's sp500 key texts apply.
_KEY_DATES = [14977.0 + 33 * i for i in range(11)] + [15340.0]
_KEY = pd.DataFrame({"date": _KEY_DATES,
                     "lo": [float(i) for i in range(12)],
                     "hi": [float(i) for i in range(12)]})
_TM = pd.DataFrame({"m": [float(v) for v in range(492, 505)],
                    "lo": [float(i) for i in range(13)],
                    "hi": [float(i) for i in range(13)]})
_TC = pd.DataFrame({"tc": [d * 86400000.0 for d in _KEY_DATES],
                    "lo": [float(i) for i in range(12)],
                    "hi": [float(i) for i in range(12)]})
_PRICE_V = [3291, 4099, 4749, 5079, 5788, 6295, 7827, 8814, 9735, 11385,
            13466, 15906]
_PRICE = pd.DataFrame({"price": [float(v) for v in _PRICE_V],
                       "lo": [float(i) for i in range(12)],
                       "hi": [float(i) for i in range(12)]})


def _served(tmp_path, spec, data):
    """(document, warnings) from one session of the generated app.  The
    app is generated and imported outside the warning capture; only the
    session's own build is captured."""
    sp, dp = _write(tmp_path, spec, data)
    ap = os.path.join(str(tmp_path), "app.py")
    dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    assert _ATTACH in src
    ns = {"__name__": "date_axis_residuals_app"}
    exec_app(src.replace(_ATTACH, "pass"), ap, ns)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    doc.to_json()
    return doc, [str(w.message) for w in caught]


def _sc(var, **opts):
    o = {"colorvar": var}
    o.update(opts)
    return {"type": "scatter", "yvar": "lo", "xvar": "hi", "options": o}


def _build(tmp_path, mode, plots, data, formats=None, go=None,
           filters=None):
    """(root, warnings, renderer-or-document) in *mode*."""
    spec = _spec(plots, formats=formats or {"date": "%td"},
                 graph_options=go, filters=filters)
    if mode == "saved":
        r, w = _saved(tmp_path, spec, data)
        return r._last_layout_root, w, r
    doc, w = _served(tmp_path, spec, data)
    return doc, w, doc


def _bar(root):
    """(ticks, {tick: text}) of the one ColorBar, or (None, None)."""
    bars = [a for f in cb._figures(root) for a in f.right
            if isinstance(a, ColorBar)]
    assert len(bars) == 1, bars
    b = bars[0]
    if not isinstance(b.ticker, FixedTicker):
        return b.ticker, None
    return list(b.ticker.ticks), dict(b.major_label_overrides)


def _bar_texts(root):
    ticks, ov = _bar(root)
    assert isinstance(ticks, list), ticks
    return [ov.get(t) for t in ticks]


def _keys(root):
    """The colorvar Legend's labels."""
    legs = [a for f in cb._figures(root) for a in f.right
            if isinstance(a, Legend)
            and str(a.name or "") == dr._COLORVAR_LEGEND_NAME]
    assert len(legs) == 1, legs
    return [it.label.get("value") if isinstance(it.label, dict)
            else getattr(it.label, "value", it.label) for it in legs[0].items]


def _factors(root):
    (rend,) = cb.colour_renderers(root)
    return list(cb.colour_mapper(rend).factors)


def _tool(root):
    """(tooltips, formatters) of the figure's one HoverTool."""
    tools = [t for f in cb._figures(root) for t in f.tools
             if isinstance(t, HoverTool)]
    assert len(tools) == 1, tools
    return list(tools[0].tooltips), dict(tools[0].formatters or {})


def _znotes(warns, what="zlabel"):
    return [w for w in warns if what in w]


# ===========================================================================
# The colour key of a date is in its Stata units
# ===========================================================================

class TestADateColourKeyIsInStataUnits:

    @pytest.mark.parametrize("mode", MODES)
    def test_the_bar_ticks_a_date_at_twoways_numbers(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("date")], _KEY)
        ticks, ov = _bar(root)
        want = (15000, 15100, 15200, 15300, 15400)
        assert ticks == [_ms(t) for t in want]
        assert [ov[t] for t in ticks] == [
            "15,000", "15,100", "15,200", "15,300", "15,400"]

    @pytest.mark.parametrize("mode", MODES)
    def test_colorlevels_bins_and_labels_in_stata_units(self, tmp_path,
                                                         mode):
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("date", colorlevels="3")], _KEY)
        assert _factors(root) == ["14,977–15,098", "15,098–15,219",
                                  "15,219–15,340"]
        (rend,) = cb.colour_renderers(root)
        f = _factors(root)
        got = [f.index(v) for v in cb.colour_values(rend)]
        assert got == [0] * 4 + [1] * 4 + [2] * 4

    @pytest.mark.parametrize("mode", MODES)
    def test_colorcuts_are_read_in_stata_units(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("date", colorcuts="15100 15200")], _KEY)
        f = _factors(root)
        assert f == ["≤15,100", "15,100–15,200", ">15,200"]
        (rend,) = cb.colour_renderers(root)
        assert [f.index(v) for v in cb.colour_values(rend)] == [
            0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2]

    @pytest.mark.parametrize("mode", MODES)
    def test_colordiscrete_levels_are_stata_numbers(self, tmp_path, mode):
        df = pd.DataFrame({"date": [14977.0, 14978.0, 14979.0, 14980.0,
                                    14983.0],
                           "lo": [0.0, 1, 2, 3, 4], "hi": [0.0, 1, 2, 3, 4]})
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("date", colordiscrete="colordiscrete")],
                              df)
        assert _keys(root) == ["14,977", "14,978", "14,979", "14,980",
                               "14,983"]

    @pytest.mark.parametrize("mode", MODES)
    def test_colorvarminmax_ticks_the_first_and_last_date(self, tmp_path,
                                                          mode):
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("date", colorvarminmax="1")], _KEY)
        ticks, ov = _bar(root)
        assert _ms(14977) in ticks and _ms(15340) in ticks
        assert ov[_ms(14977)] == "14,977" and ov[_ms(15340)] == "15,340"

    @pytest.mark.parametrize("mode", MODES)
    def test_a_period_key_is_in_its_own_units(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("m")], _TM,
                              formats={"m": "%tm"})
        assert _bar_texts(root) == ["490", "495", "500", "505"]
        root2, _w2, _o2 = _build(tmp_path, mode,
                                 [_sc("m", colorlevels="3")], _TM,
                                 formats={"m": "%tm"})
        assert _factors(root2) == ["492–496", "496–500", "500–504"]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_tc_key_is_in_statas_milliseconds(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("tc")], _TC,
                              formats={"tc": "%tc"})
        texts = _bar_texts(root)
        assert len(texts) == 5 and set(texts) == {"1.3e+12"}

    @pytest.mark.parametrize("mode", MODES)
    def test_the_key_is_unchanged_after_a_filter_move(self, tmp_path, mode):
        filt = [_filter("range", "lo")]
        root, _w, obj = _build(tmp_path, mode, [_sc("date")], _KEY,
                               filters=filt)
        root2, _w2, obj2 = _build(tmp_path, mode,
                                  [_sc("date", colorlevels="3")], _KEY,
                                  filters=filt)

        def _state():
            (rend,) = cb.colour_renderers(root2)
            return (_bar(root), _factors(root2),
                    sorted(map(str, cb.drawn_colour_values(rend))))

        before = _state()
        for o in (obj, obj2):
            if mode == "saved":
                s = JsSession(o.filter_callbacks)
                sl = [w for w in o.filter_widgets
                      if isinstance(w, RangeSlider)][0]
                s.set(sl, (2, 9))
                for cbk in o.filter_callbacks:
                    s.run(cbk)
            else:
                import test_mode_parity as mp
                sl = [w for w in mp._widgets_of(o)
                      if isinstance(w, RangeSlider)][0]
                _fire(sl, (2, 9))
        after = _state()
        assert _bar_texts(root) == ["15,000", "15,100", "15,200", "15,300",
                                    "15,400"]
        assert after[0] == before[0]
        assert after[1] == before[1]
        # The drawn rows' labels are each still one of the key's factors.
        assert set(after[2]) <= set(before[1])


class TestZlabelOnAColourKey:

    @pytest.mark.parametrize("mode", MODES)
    def test_format_td_writes_dates(self, tmp_path, mode):
        root, w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                             go={"zlabel": ", format(%td)"})
        assert _bar_texts(root) == ["25jan2001", "05may2001", "13aug2001",
                                    "21nov2001", "01mar2002"]
        assert _znotes(w) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_count_ticks_are_twoways(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                              go={"zlabel": "#3"})
        ticks, ov = _bar(root)
        assert ticks == [_ms(t) for t in (15000, 15200, 15400)]
        assert [ov[t] for t in ticks] == ["15,000", "15,200", "15,400"]

    @pytest.mark.parametrize("mode", MODES)
    def test_minmax_ticks_the_first_and_last(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                              go={"zlabel": "minmax"})
        assert _bar_texts(root) == ["14,977", "15,340"]

    @pytest.mark.parametrize("mode", MODES)
    def test_explicit_ticks_and_labels_are_stata_values(self, tmp_path,
                                                        mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                              go={"zlabel": '15000 "start" 15300 "end"'})
        ticks, ov = _bar(root)
        assert ticks == [_ms(15000), _ms(15300)]
        assert ov == {_ms(15000): "start", _ms(15300): "end"}

    @pytest.mark.parametrize("mode", MODES)
    def test_a_numeric_format_writes_the_stored_value(self, tmp_path, mode):
        root, w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                             go={"zlabel": ", format(%9.1fc)"})
        assert _bar_texts(root) == ["15,000.0", "15,100.0", "15,200.0",
                                    "15,300.0", "15,400.0"]
        assert _znotes(w) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_format_reaches_the_binned_labels(self, tmp_path, mode):
        root, w, _o = _build(tmp_path, mode, [_sc("date", colorlevels="3")],
                             _KEY, go={"zlabel": ", format(%td)"})
        assert _factors(root) == ["02jan2001–03may2001",
                                  "03may2001–01sep2001",
                                  "01sep2001–31dec2001"]
        assert _znotes(w) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_format_reaches_a_discrete_key_silently(self, tmp_path, mode):
        root, w, _o = _build(tmp_path, mode,
                             [_sc("price", colordiscrete="colordiscrete")],
                             _PRICE.iloc[:5].reset_index(drop=True),
                             formats={"price": "%9.0g"},
                             go={"zlabel": ", format(%9.2f)"})
        assert _keys(root) == ["3291.00", "4099.00", "4749.00", "5079.00",
                               "5788.00"]
        assert _znotes(w) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_zscale_range_is_read_in_stata_units(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                              go={"zscale": "range(14600 15700)"})
        assert cb.colour_bars(root) == [(_ms(14600), _ms(15700))]
        assert _bar_texts(root) == ["15,000", "15,100", "15,200", "15,300",
                                    "15,400"]

    @pytest.mark.parametrize("mode", MODES)
    def test_an_unwritable_format_draws_g_and_is_named(self, tmp_path, mode):
        root, w, _o = _build(tmp_path, mode, [_sc("date")], _KEY,
                             go={"zlabel": ", format(%21x)"})
        assert _bar_texts(root) == ["15000", "15100", "15200", "15300",
                                    "15400"]
        assert len([x for x in w if "format(%21x)" in x]) == 1


class TestANumberKeyIsInTwowaysCommaFormat:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_g_formatted_variable_keys_with_commas(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("price", colorcuts="5000 9000")], _PRICE,
                              formats={"price": "%9.0g"})
        assert _factors(root) == ["≤5,000", "5,000–9,000", ">9,000"]

    @pytest.mark.parametrize("mode", MODES)
    def test_the_bar_ticks_a_number_at_twoways_numbers(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_sc("price")], _PRICE,
                              formats={"price": "%9.0g"})
        ticks, ov = _bar(root)
        assert ticks == [0.0, 5000.0, 10000.0, 15000.0]
        assert [ov[t] for t in ticks] == ["0", "5,000", "10,000", "15,000"]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_discrete_number_key_uses_commas(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode,
                              [_sc("price", colordiscrete="colordiscrete")],
                              _PRICE.iloc[:5].reset_index(drop=True),
                              formats={"price": "%9.0g"})
        assert _keys(root) == ["3,291", "4,099", "4,749", "5,079", "5,788"]


# ===========================================================================
# The computed layers' tooltips
# ===========================================================================

def _hist(o=None, var="date"):
    return {"type": "histogram", "var": var, "options": dict(o or {})}


class TestFallbackTooltipsUseDisplayFormats:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_histograms_bins_are_dates(self, tmp_path, mode):
        root, _w, _o = _build(tmp_path, mode, [_hist()], _KEY)
        tips, fmts = _tool(root)
        assert tips == [("date", "@{left}{custom} to @{right}{custom}"),
                        ("Density", "@{top}")]
        f = fmts["@{left}"]
        assert isinstance(f, CustomJSHover)
        assert {k: f.args[k] for k in ("fmt", "kind", "storage")} == {
            "fmt": "%td", "kind": "td", "storage": ""}
        assert js_texts(f, [_ms(14977)], "value") == ["02jan2001"]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_formatted_histograms_bins_have_commas(self, tmp_path, mode):
        df = pd.DataFrame({"big": [1000000.0 + 50000 * i for i in range(12)],
                           "lo": [float(i) for i in range(12)]})
        root, _w, _o = _build(tmp_path, mode, [_hist(var="big")], df,
                              formats={"big": "%12.0fc"})
        _tips, fmts = _tool(root)
        f = fmts["@{left}"]
        assert (f.args["fmt"], f.args["kind"]) == ("%12.0fc", "")
        assert js_texts(f, [1250000.0], "value") == ["1,250,000"]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_fit_on_a_date_axis_writes_dates(self, tmp_path, mode):
        plot = {"type": "lfit", "yvar": "lo", "xvar": "date", "options": {}}
        root, _w, _o = _build(tmp_path, mode, [plot], _KEY)
        tips, fmts = _tool(root)
        assert tips[0][0] == "date" and tips[0][1].endswith("{custom}")
        fx = fmts[tips[0][1].split("{custom}")[0]]
        assert fx.args["kind"] == "td"
        assert tips[1] == ("lo", tips[1][1])
        assert tips[1][1].endswith("{0.00}")

    @pytest.mark.parametrize("mode", MODES)
    def test_a_kdensity_names_its_variable_and_density(self, tmp_path, mode):
        plot = {"type": "kdensity", "var": "date", "options": {}}
        root, _w, _o = _build(tmp_path, mode, [plot], _KEY)
        tips, _f = _tool(root)
        assert [t[0] for t in tips] == ["date", "Density"]
        assert tips[0][1] == "@{x}{custom}"

    @pytest.mark.parametrize("mode", MODES)
    def test_the_tooltips_survive_a_filter_move(self, tmp_path, mode):
        root, _w, obj = _build(tmp_path, mode, [_hist()], _KEY,
                               filters=[_filter("range", "lo")])
        before = _tool(root)
        quads = [r for f in cb._figures(root) for r in f.renderers
                 if "left" in r.data_source.data]
        if mode == "saved":
            s = JsSession(obj.filter_callbacks)
            sl = [w for w in obj.filter_widgets
                  if isinstance(w, RangeSlider)][0]
            s.set(sl, (2, 9))
            for cbk in obj.filter_callbacks:
                s.run(cbk)
        else:
            import test_mode_parity as mp
            sl = [w for w in mp._widgets_of(obj)
                  if isinstance(w, RangeSlider)][0]
            _fire(sl, (2, 9))
        after = _tool(root)
        assert after[0] == before[0]
        assert ({k: dict(v.args) for k, v in after[1].items()}
                == {k: dict(v.args) for k, v in before[1].items()})
        left0 = float(quads[0].data_source.data["left"][0])
        want = dr._dash_fmt_text(dr._dash_stata_value_of(left0, "td"), "%td")
        assert js_texts(after[1]["@{left}"], [left0], "value") == [want]

    def test_a_variable_with_no_format_keeps_todays_precision(self):
        fig = figure()
        src = ColumnDataSource({"left": [1.5, 2.5], "right": [2.5, 3.5],
                                "top": [1.0, 2.0]})
        fig.quad(left="left", right="right", top="top", bottom=0,
                 source=src)
        dr._dash_build_hover(fig, "", "", "", [], univar="price")
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tool.tooltips[0][1] == "@{left}{0.000} to @{right}{0.000}"


class TestHistogramTooltipNamesItsMeasure:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("measure", ["density", "frequency", "fraction",
                                         "percent"])
    def test_the_height_row_is_the_y_titles_word(self, tmp_path, measure,
                                                 mode):
        o = {} if measure == "density" else {measure: measure}
        root, _w, _o = _build(tmp_path, mode, [_hist(o)], _KEY)
        tips, _f = _tool(root)
        assert tips[1] == (measure.capitalize(), "@{top}")

    def test_an_untagged_quad_is_density(self):
        fig = figure()
        src = ColumnDataSource({"left": [1.0], "right": [2.0], "top": [3.0]})
        fig.quad(left="left", right="right", top="top", bottom=0,
                 source=src)
        dr._dash_build_hover(fig, "", "", "", [], univar="v")
        (tool,) = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tool.tooltips[1][0] == "Density"

    @pytest.mark.parametrize("mode", MODES)
    def test_an_emptied_histogram_is_tagged_too(self, tmp_path, mode):
        plot = dict(_hist(), if_expr="lo > 99")
        root, _w, _o = _build(tmp_path, mode, [plot], _KEY)
        quads = [r for f in cb._figures(root) for r in f.renderers
                 if "top" in r.data_source.data]
        assert quads and all("dash_hist_density" in (r.tags or [])
                             for r in quads)


# ===========================================================================
# The helpers
# ===========================================================================

class TestTheKeyHelpers:

    def test_the_key_format_rule(self):
        f = dr._dash_key_format
        assert f({}) == ("%8.0gc", None)
        assert f({"zlabel": ", format(%td)"}) == ("%td", None)
        assert f({"zlabel": ', format("%9.2f")'}) == ("%9.2f", None)
        assert f({"zlabel": ", format(%21x)"}) == ("%9.0g", "%21x")
        assert f({"zlabel": ", format(%12s)"}) == ("%9.0g", "%12s")
        assert f({"zlabel": ", format()"}) == ("%8.0gc", None)
        long = "%" + "9" * 199
        fmt, bad = f({"zlabel": ", format(%s)" % long})
        assert fmt == "%9.0g" and bad == long[:60]

    def test_key_ticks_positions_and_text(self):
        pos, ov = dr._dash_key_ticks([15100.0, 15000.0], "td", "%8.0gc")
        assert pos == [_ms(15000), _ms(15100)]
        assert ov == {_ms(15000): "15,000", _ms(15100): "15,100"}
        pos, ov = dr._dash_key_ticks([5000.0], "", "%8.0gc")
        assert pos == [5000.0] and ov == {5000.0: "5,000"}
        pos, ov = dr._dash_key_ticks([15000.0, 15300.0], "td", "%8.0gc",
                                     {"15000.0": "start"})
        assert ov == {_ms(15000): "start", _ms(15300): "15,300"}
        pos, ov = dr._dash_key_ticks([15000.0, 3000000.0], "td", "%8.0gc")
        assert pos == [_ms(15000)]

    def test_the_measure_word_reads_the_tag(self):
        fig = figure()
        for mode, word in dr._DASH_HIST_YTITLES.items():
            r = fig.quad(left=[0], right=[1], top=[1], bottom=0)
            r.tags = ["dash_hist_" + mode]
            assert dr._dash_hist_measure(r) == word
        r = fig.quad(left=[0], right=[1], top=[1], bottom=0)
        r.tags = ["dash_hist_bogus"]
        assert dr._dash_hist_measure(r) == "Density"

    def test_the_fallback_format_rule(self):
        ff = dr._dash_fallback_format
        fm = {"date": "%td", "big": "%12.0fc", "s": "%9s"}
        dv = {"date": "td"}
        h = ff("date", "td", fm, dv, {})
        assert (h.args["fmt"], h.args["kind"]) == ("%td", "td")
        h = ff("date", None, fm, dv, {})
        assert (h.args["fmt"], h.args["kind"]) == ("%td", "")
        h = ff("big", None, fm, dv, {})
        assert (h.args["fmt"], h.args["kind"]) == ("%12.0fc", "")
        assert ff("s", None, fm, dv, {}) is None
        assert ff("nope", None, fm, dv, {}) is None
        assert ff("a}b", None, {"a}b": "%9.0g"}, {}, {}) is None


# ===========================================================================
# A figure with no colour key and no computed layer is unchanged
# ===========================================================================

def _digest(model):
    """sha256 of *model*'s page JSON with every id removed."""
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k != "id"}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o
    item = json_item(model)
    doc = strip(item["doc"]["roots"])
    return hashlib.sha256(
        json.dumps(doc, sort_keys=True).encode("utf-8")).hexdigest()


# Taken at the batch-6 base (4f8e528); never re-baselined.
# Re-derived on the merged batch-6 tree: P1.2b (opaque markers) and P1.5
# (tick formatters) change every figure; a key-free figure is still the
# same in both of its cases, which is what this pins.
_PLAIN_DIGESTS = {
    ("saved", "plain"):
        "17bf383e1c3543b1a677a9f55521e5e815755601fc41e2483c1ef2eec694bae6",
    ("saved", "yaxis2"):
        "17bf383e1c3543b1a677a9f55521e5e815755601fc41e2483c1ef2eec694bae6",
    ("served", "plain"):
        "0a1fa55d399232fff208041d4eb3f84d20f12ee9ea3c920b9de99cbe5deffa37",
    ("served", "yaxis2"):
        "0a1fa55d399232fff208041d4eb3f84d20f12ee9ea3c920b9de99cbe5deffa37",
}


class TestANonKeyFigureIsUnchanged:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", ["plain", "yaxis2"])
    def test_a_plain_scatter_builds_the_same_models(self, tmp_path, mode,
                                                    case):
        o = {} if case == "plain" else {"yaxis": "2"}
        plot = {"type": "scatter", "yvar": "lo", "xvar": "hi", "options": o}
        root, _w, _o = _build(tmp_path, mode, [plot], _KEY)
        model = root.roots[0] if mode == "served" else root
        assert _digest(model) == _PLAIN_DIGESTS[(mode, case)]


# ===========================================================================
# twoway's own texts (test/fixtures/key_text_truth.json)
# ===========================================================================

def _truth():
    if not os.path.exists(_TRUTH):
        pytest.fail("test/fixtures/key_text_truth.json is missing; run "
                    "scripts/extract_key_text_truth.do")
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


#: Each key probe's dash options: (plot options, graph options).
_PROBE_OPTS = {
    "k_date": ({}, {}),
    "k_date_lev3": ({"colorlevels": "3"}, {}),
    "k_date_cuts": ({"colorcuts": "15100 15200"}, {}),
    "k_date_td": ({}, {"zlabel": ", format(%td)"}),
    "k_date_n3": ({}, {"zlabel": "#3"}),
    "k_date_minmax": ({}, {"zlabel": "minmax"}),
    "k_date_lbl": ({}, {"zlabel": '15000 "start" 15300 "end"'}),
    "k_date_f91": ({}, {"zlabel": ", format(%9.1fc)"}),
    "k_date_lev_td": ({"colorlevels": "3"}, {"zlabel": ", format(%td)"}),
    "k_date_zrange": ({}, {"zscale": "range(14600 15700)"}),
    "k_date_tm": ({}, {"zlabel": ", format(%tm)"}),
    "k_tm": ({}, {}),
    "k_tc": ({}, {}),
    "k_dn": ({}, {}),
    "k_price_gc": ({}, {}),
    "k_price_g": ({}, {}),
    "k_price_cuts": ({"colorcuts": "5000 9000"}, {}),
    "k_price_lev3": ({"colorlevels": "3"}, {}),
    "k_price_f92": ({}, {"zlabel": ", format(%9.2f)"}),
    "k_price_quoted": ({}, {"zlabel": ', format("%9.2f")'}),
    "k_big": ({}, {}),
    "k_tiny": ({}, {}),
    "k_mid": ({}, {}),
    "k_six": ({}, {}),
}


def _inner_bounds(factors):
    texts = []
    for f in factors:
        for part in str(f).lstrip("≤>").split("–"):
            if part not in texts:
                texts.append(part)
    if factors and not str(factors[0]).startswith("≤"):
        texts = texts[1:-1]
    return texts


class TestTheKeyTextTruth:

    def test_the_fixture_is_stamped(self):
        meta = _truth()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k

    def test_the_key_format_is_eight_wide_comma_general(self):
        disp = _truth()["display"]
        assert disp
        for v, t in disp.items():
            assert dr._dash_fmt_text(float(v), "%8.0gc") == \
                t["%8.0gc"].strip(), v
        assert "," not in disp["15000"]["%7.0gc"]
        assert "," in disp["123456.25"]["%9.0gc"]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("pid", sorted(_PROBE_OPTS))
    def test_every_probe_keys_as_twoway(self, tmp_path, pid, mode):
        p = _truth()["probes"][pid]
        assert p["rc"] == 0
        var = p["var"]
        n = len(p["data"])
        df = pd.DataFrame({var: [np.nan if v is None else v
                                 for v in p["data"]],
                           "lo": [float(i) for i in range(n)],
                           "hi": [float(i) for i in range(n)]})
        popts, go = _PROBE_OPTS[pid]
        root, _w, _o = _build(tmp_path, mode, [_sc(var, **popts)], df,
                              formats={var: p["format"]}, go=go)
        if p["kind"] == "bins":
            got = _inner_bounds(_factors(root))
        else:
            got = _bar_texts(root)
        assert got == p["key_texts"]

    def test_the_histogram_measures_are_twoways_titles(self):
        probes = _truth()["probes"]
        for m in ("density", "frequency", "fraction", "percent"):
            assert probes["h_" + m]["ytitle"] == dr._DASH_HIST_YTITLES[m]

    def test_twoway_refuses_what_dash_refuses(self):
        probes = _truth()["probes"]
        for pid, f in (("f_bogus", "bogus"), ("f_92x", "%9.2x"),
                       ("f_tdbogus", "%tdbogus")):
            assert probes[pid]["rc"] == 198
            assert probes[pid]["err"] == "invalid format, " + f
        for pid in ("f_12s", "f_21x"):
            assert probes[pid]["rc"] == 0
