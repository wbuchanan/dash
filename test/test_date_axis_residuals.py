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

import base64
import gzip
import hashlib
import json
import math
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
    def test_the_key_is_ticked_over_the_kept_days(self, tmp_path, mode):
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
        # Flipped (WP-32, BUGS.md "A colour key ticked by zlabel() or a
        # date, and a zscale(log) line, keep the build's ticks or levels
        # after a filter move"): twoway ticks a date key by natscale over
        # the days it draws, written as numbers (measured 19oct2026:
        # 16,200 ... 16,800 over the foreign cars, 14,500 ... 17,000 over
        # every car), so after the move the bar is ticked over the days
        # its layer keeps.
        (rend,) = cb.colour_renderers(root)
        days = [float(v) for v in dr._dash_date_units(
            cb.colour_values(rend), "td") if math.isfinite(v)]
        want = [dr._dash_fmt_text(t, "%8.0gc") for t in dr._dash_cvar_ticks(
            min(days), max(days), {"mode": "auto"})]
        assert _bar_texts(root) == want
        assert want != ["15,000", "15,100", "15,200", "15,300", "15,400"]
        # Flipped (WP-32, BUGS.md "colorlevels() and colorcuts() keep the
        # build's bins after a filter move"; it pinned the build's bins,
        # WP-29 BR-07.4, which the maintainer's ruling overrides): twoway
        # cuts colorlevels() over the rows it draws (measured 19oct2026:
        # colorlevels(4) over mpg 12-41 cuts at 19.25 26.5 33.75, over
        # 12-24 at 15 18 21), so the three bins span the days kept, in
        # Stata units, and each drawn row's label is one of them.
        (rend2,) = cb.colour_renderers(root2)
        kept = [float(v) for v in dr._dash_date_units(dr._dash_float_values(
            list(rend2.data_source.data["date"]), coerce=True), "td")
            if math.isfinite(v)]
        lo, hi = min(kept), max(kept)
        cuts = [lo + (hi - lo) * i / 3 for i in (1, 2)]
        bounds = [lo] + cuts + [hi]
        assert after[1] == [
            f"{dr._dash_fmt_text(a, '%8.0gc')}\u2013"
            f"{dr._dash_fmt_text(b, '%8.0gc')}"
            for a, b in zip(bounds, bounds[1:])]
        assert after[1] != before[1]
        assert set(after[2]) <= set(after[1])


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
    def test_the_height_row_is_the_y_titles_word(self, tmp_path, mode):
        for measure in ("density", "frequency", "fraction", "percent"):
            o = {} if measure == "density" else {measure: measure}
            root, _w, _o = _build(tmp_path, mode, [_hist(o)], _KEY)
            tips, _f = _tool(root)
            assert tips[1] == (measure.capitalize(), "@{top}"), measure

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

def _gunzip(v):
    """A gzipped base64 array buffer as its raw bytes' hex: the gzip header's
    XFL byte follows the zlib build, not the model (WP-30 S58: Stata's Python
    writes 02 where the development one writes 00)."""
    if isinstance(v, str) and v.startswith("H4sI"):
        return gzip.decompress(base64.b64decode(v)).hex()
    return v


def _digest(model):
    """sha256 of *model*'s page JSON with every id removed and every gzipped
    buffer decompressed.  WP-31 H2x: an id held as a value (the composite
    export's model ids) is masked too, since ids follow Bokeh's own count
    of the models it builds, which differs between Bokeh releases."""
    ids = set()

    def collect(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), str):
                ids.add(o["id"])
            for v in o.values():
                collect(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                collect(v)

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k != "id"}
        # A map's entries are tuples (P1.3a's range callbacks hold ids).
        if isinstance(o, (list, tuple)):
            return [strip(v) for v in o]
        if isinstance(o, str) and o in ids:
            return "<id>"
        return _gunzip(o)
    item = json_item(model)
    collect(item["doc"]["roots"])
    doc = strip(item["doc"]["roots"])
    return hashlib.sha256(
        json.dumps(doc, sort_keys=True).encode("utf-8")).hexdigest()


# Taken at the batch-6 base (4f8e528); never re-baselined.
# Re-derived on the merged batch-6 tree: P1.2b (opaque markers) and P1.5
# (tick formatters) change every figure; a key-free figure is still the
# same in both of its cases, which is what this pins.  Re-derived again on
# the merged batch-7 tree: P1.3a (default axes take twoway's ticks, range
# and margin) changes every figure; and on the batch-9 tree P1.17b's
# axis plan key (autobase) and finish code.  Re-derived on the batch-12
# tree: P1.23a's formatter code (dash_stata_number_of), the plan's "units"
# key and the date-units JS in the finish code; nothing else differs.
# Re-derived for WP-30 P1.3b: the filter callback carries the date model's
# JavaScript port (_DASH_TSNATSCALE_JS inside _DASH_AXIS_FINISH_JS), and
# again for its default-date-axis range() rule (the batch-15 gate).
# Re-derived for WP-30 P1.20b: the axis plan's margin is a per-side pair
# and each panel names its inner box; the finish code pads per side.
# Re-derived for WP-30 P1.21b: the finish code carries dash_refline_extent
# (the filter callback's text only; a plain figure draws no Arrow).
# Re-derived on the merged batch-18 tree: P1.18b's axis plan key (xnr)
# and finish code.  Re-derived for WP-30 P1.28b: the grid's toolbar holds
# the Save as SVG action (the saved digest with the old _dash_name_save
# patched back in is the batch-18 one).  Re-derived for WP-30 P1.17b: the
# finish code's date model puts %td weekly steps on %tw week starts
# (dash_ts_day_week; finish JS text only).
# 228ed963... -> ca4f095c... and 1b348e29... -> fb860211...: D1 the axis
# finisher and zoom code (one CustomJS per page) gain the minor-tick step;
# measured at 3b4ff75 against this tree, the code string is the only
# difference in a plain scatter's models.
# ca4f095c... -> 932c85bd... and fb860211... -> 23c6fcc8...: WP-31 D4 the
# (hidden) legend takes the scheme's key geometry, its grid and its
# panel location from twoway's clock table.
_PLAIN_DIGESTS = {
    # 932c85bd... -> b8c27bfa...: WP-31 D6/D7 the axis finisher's
    # dash_axis_bounds (noextend) joins the page's finish code.
    # b8c27bfa... -> def54a8f...: WP-31 D7 the axis title gap is the
    # scheme's axis_title_gap (1 px, was Bokeh's 5).
    # def54a8f... -> 2e3fd291...: WP-31 D1c the finish code reads a
    # typed list as no ##N rule (finish JS text only).
    # 2e3fd291... -> 83ddae14...: WP-31 B5c the axis plan carries each
    # axis's dot rows (an empty "dots" list here) and the finish code
    # dash_fill_dots.
    # 83ddae14... -> dee5b397...: WP-31 D1b the finish code re-places a
    # far-side or outer axis's minor-label pool (finish JS text only).
    # dee5b397... -> 2e569732...: WP-31 D12 the zoom code ends with the
    # reference lines' dash_refline_extent statement (zoom JS text only).
    # 2e569732... -> 0d452f74...: WP-31 E2 the minor grid's dot is Stata's
    # .1 .7 rs ([1, 3] px; [2, 4] before), merged on D12.
    # 0d452f74... -> 02665fa0...: WP-31 G1/G2 the filter mask's code
    # branch and each Stata writer's args and code carry the page's dp.
    # 02665fa0... -> 5777f9c1...: WP-31 D15 the finish code reads Stata's
    # own ticks (dash_stata_pick) and re-places xtick(#N) (finish JS text
    # only).
    # 5777f9c1... -> 1735f74a...: WP-31 D15 follow-up, a shared by()
    # letter's xtick(#N) in the finish code (finish JS text only).
    # 02665fa0... -> 425a7065...: WP-31 G7 the Stata writer reads %d as
    # %td (writer JS text only); 425a7065... -> aea1fee4...: WP-31 G7 the
    # writer's %tb (writer JS text only).
    # Merged batch 15 (D15, D15 follow-up, G7, C11 degree): 4f04a250...
    # saved, 7533995b... served, re-derived on the merged tree.
    # 4f04a250... -> 913aa1ee... saved, 7533995b... -> e69103bd... served:
    # WP-31 H2x the grid's Save dashboard action and the composite SVG
    # code and ids, the print hide stylesheet on the toolbar (and, served,
    # the root's print hook args); the same under both Pythons.
    # 4f04a250... -> bff51822... saved, 7533995b... -> aee4df70... served:
    # WP-31 K6 the figure's role="img" and aria-label html_attributes,
    # the same under bokeh 3.8 (Stata's Python) and 3.9.
    # Merged batch 18 (H2x, K6): e8b7082b... saved, 9b7c416f... served.
    # e8b7082b... -> 758304bd... saved, 9b7c416f... -> e975974d... served:
    # the batch-18 gate, the composite code's entity table keyed by name
    # (finish JS text only); the same under both Pythons.
    # 758304bd... -> bbe2bc2f... saved, e975974d... -> 9935c1c8... served:
    # WP-31 K6 follow-up, a figure with a toolbar is role="group", not
    # "img" (axe nested-interactive); the same under both Pythons.
    # bbe2bc2f... -> ac6ee365... saved, 9935c1c8... -> 0710df1c... served:
    # WP-32 D-31.a the (hidden) legend's key box is symxsize() by
    # symysize(), 50 x 13 (was 15 x 15); masked model diff, the same under
    # both Pythons.
    # bbe2bc2f... -> fba98ea5... saved, 9935c1c8... -> 7f8f4187... served:
    # WP-32, the finish code gives an axis whose layers draw nothing the
    # empty form (DASH_EMPTY_SCALE; finish JS text only).
    # bbe2bc2f... -> 41fbfc2a... saved, 9935c1c8... -> ecb180dc... served:
    # WP-32 D-53d, the composite actions' toggle_ids arg is table_ids and
    # the composite code draws open tables (masked model diff: nothing
    # else differs); the same under both Pythons.
    # ac6ee365... -> d68dfa44... saved, 0710df1c... -> 35cb03e3... served:
    # the WP-32 merge of D-31.a, D-53d/e, the empty-axis finish and the fit
    # extents (each confirmed by its masked model diff); the same under both
    # Pythons.
    # d68dfa44... -> 9653c56a... saved, 35cb03e3... -> 4fd310cb... served:
    # WP-34 AX-4, every axis-plan layer carries hfields and the finish and
    # filter code read a histogram's midpoint and span columns; the same
    # under both Pythons.
    # 9653c56a... -> a4bad736... saved, 4fd310cb... -> 8d1ef2de... served:
    # WP-34 AX-1, the axis plan's byg key and the finish code's
    # default-axis condition (plan key and finish JS text only); the same
    # under both Pythons.
    # a4bad736... -> 7b91a824... saved, 8d1ef2de... -> 945ef1ea... served:
    # WP-45 VF-4 (brought into WP-41 41-05), the figure loses its
    # 160-560 px height band (max_height and min_height None) and carries
    # its nominal box; twoway draws its graph's shape at any size
    # (DECISIONS A-1); the same under both Pythons.
    # 7b91a824... -> 5b51f15b... saved, 945ef1ea... -> 28fb7ffe... served:
    # WP-45 VF-4 with DECISIONS D66/D67 (the graph drawn as one picture, its width-scale callback on every figure; one toolbar per page, laid over it); the same under both Pythons.
    # 5b51f15b... -> 14933864... saved, 28fb7ffe... -> d46d95fa... served:
    # WP-45 GW-6, the figure's graph-region box (its margin padding, fill
    # and tag in its styles) and the span hook's graph box; the same under
    # both Pythons.
    # 14933864... -> f7c8dba6... saved, d46d95fa... -> cf6d2d71... served:
    # WP-41 41-05, the plot region's outline in the width scale's table;
    # the same under both Pythons.
    # f7c8dba6... -> 36f06f41... saved, cf6d2d71... -> d5a72d60... served:
    # WP-41 41-05, the width scale's by() grid spacing pair and its --dash-by-k length (width-scale JS text only); the same under both Pythons.
    # 36f06f41... -> 9299b510... saved, d5a72d60... -> 2ff9cd13... served:
    # BUGS.md "A graph's canvas ended before its own x axis, x title and
    # colour key labels", the graph region box a column of its own round
    # the figure (the figure keeps the margin's inside ratio) and the
    # width-scale and span JS's graph box; the same under both Pythons.
    ("saved", "plain"):
        "9299b510f9f8e31d7690b6ecf257379c7f21a9092f297089a321c8873642ddf5",
    ("saved", "yaxis2"):
        "9299b510f9f8e31d7690b6ecf257379c7f21a9092f297089a321c8873642ddf5",
    # WP-30 S58: re-derived once gzipped buffers are hashed decompressed,
    # the same under bokeh 3.8 (Stata's Python) and 3.9.
    # 23c6fcc8... -> f8ce3f00... -> 59d68f1d... -> 0440b3d9...: WP-31
    # D6/D7/D1c, as the saved page's; 0440b3d9... -> 5a0efbf6...: WP-31
    # B5c, as the saved page's; 5a0efbf6... -> 8af4b99f...: WP-31 D1b,
    # as the saved page's; 8af4b99f... -> c6afee47...: WP-31 D12, as the
    # saved page's; c6afee47... -> 0a83753e...: WP-31 E2, as the saved
    # page's; 0a83753e... -> 1fc4cc55...: WP-31 G1/G2, as the saved
    # page's; 1fc4cc55... -> 1d5c76fb...: WP-31 D15, as the saved page's;
    # 1d5c76fb... -> f2fa6195...: the D15 follow-up, as the saved page's.
    # page's; 1fc4cc55... -> 6b1271a5...: WP-31 G7, as the saved page's.
    # page's; 1fc4cc55... -> 6b1271a5... -> 86688a59...: WP-31 G7 (%d, %tb),
    # as the saved page's.
    ("served", "plain"):
        "2ff9cd1335d2934aa43b996a63739a371171294acfe74b697cac2efd79d9f322",
    ("served", "yaxis2"):
        "2ff9cd1335d2934aa43b996a63739a371171294acfe74b697cac2efd79d9f322",
}


class TestANonKeyFigureIsUnchanged:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_plain_scatter_builds_the_same_models(self, tmp_path, mode):
        for case in ("plain", "yaxis2"):
            o = {} if case == "plain" else {"yaxis": "2"}
            plot = {"type": "scatter", "yvar": "lo", "xvar": "hi",
                    "options": o}
            root, _w, _o = _build(tmp_path, mode, [plot], _KEY)
            model = root.roots[0] if mode == "served" else root
            assert _digest(model) == _PLAIN_DIGESTS[(mode, case)], case


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


class _Mismatch(Exception):
    """One fixture row that differs; collected, never swallowed: the
    loop that catches it fails naming every such row."""


def _expect(ok, why):
    if not ok:
        raise _Mismatch(why)


def _mismatches(ids, check):
    """``"id: why"`` for each id whose ``check(id)`` raised _Mismatch."""
    bad = []
    for i in ids:
        try:
            check(i)
        except _Mismatch as e:
            bad.append("%s: %s" % (i, str(e).splitlines()[0] if str(e)
                                   else "differs"))
    return bad


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
    def test_every_probe_keys_as_twoway(self, tmp_path, mode):
        """Every probe; the failing probe ids are listed together."""
        truth = _truth()
        pids = sorted(_PROBE_OPTS)
        bad = _mismatches(pids, lambda pid:
                          self._one_probe(tmp_path, pid, mode, truth))
        assert not bad, "%d of %d probes differ:\n%s" % (
            len(bad), len(pids), "\n".join(bad))

    @staticmethod
    def _one_probe(tmp_path, pid, mode, truth):
        p = truth["probes"][pid]
        _expect(p["rc"] == 0, 'p["rc"] == 0')
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
        _expect(got == p["key_texts"], (got, p["key_texts"]))

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


# ==== WP-30 P1.23a (section 35): date positions on every axis ====
#
# Measured at the batch-12 base (f7e034d), both modes alike: a scatteri,
# pci, pcarrowi or function on a %td axis was drawn at its raw number
# (scatteri 1300 15400 at 15400 ms, 1970); a range or pc layer of a date
# y had a LinearAxis in epoch ms; a yaxis(2) layer of a number turned the
# first date axis numeric, and a second axis of dates was a LinearAxis in
# ms; (scatter close date) (scatter close obs) drew the dates near 9.8e11
# beside 1..12; an explicit base(14970) on a date y was 14970 ms.  twoway
# (StataNow 19.5): test/fixtures/date_axis_truth.json
# (scripts/extract_date_axis_truth.do).

import test_default_axes as tda  # noqa: E402
from js_runner import run_js  # noqa: E402
from test_served_dates import _served_fig  # noqa: E402
from bokeh.models import (Arrow, CustomJSTransform, DatetimeAxis,  # noqa: E402,E501
                          DatetimeTicker, DatetimeTickFormatter, LabelSet,
                          Span)

_E = -315619200000.0
_DA_I = np.arange(12)
_DA = pd.DataFrame({"date": 14977.0 + 30 * _DA_I,
                    "d2": 14977.0 + 30 * _DA_I + 30,
                    "m": 492.0 + _DA_I, "yr": 1990.0 + _DA_I,
                    "close": 1200.0 + 10 * _DA_I,
                    "volume": 5000.0 + 100 * _DA_I,
                    "obs": 1.0 + _DA_I, "g": (_DA_I % 2).astype(float)})
_DA_FMT = {"date": "%td", "d2": "%td", "m": "%tm", "yr": "%ty"}
_DA_MOVE = (1200.0, 1266.0)          # the close slider's lower 60%
_DA_SEQ = iter(range(10 ** 6))
_DA_TRUTH = os.path.join(_HERE, "fixtures", "date_axis_truth.json")


def _fld(spec):
    """A coordinate spec's field name, or None for a value."""
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return spec.get("field")
    return getattr(spec, "field", None)


def _units_of(spec):
    """dash's date-units kind of a spec (None before section 35)."""
    return getattr(dr, "_dash_spec_units", lambda _s: None)(spec)


def _np_ms(y, m, d):
    """numpy's epoch ms of a proleptic-Gregorian civil date (the oracle)."""
    return int(((np.datetime64(y - 1970, "Y").astype("datetime64[M]")
                 + (m - 1)).astype("datetime64[D]") + (d - 1))
               .astype("datetime64[ms]").astype(np.int64))


def _L(t, y=None, x=None, **o):
    p = {"type": t, "options": dict(o)}
    if y is not None:
        p["yvar"] = y
    if x is not None:
        p["xvar"] = x
    return p


def _si(*rows, **o):
    return {"type": "scatteri", "values": [list(map(float, r)) for r in rows],
            "options": dict(o)}


def _da_fig(tmp_path, mode, plots, go=None, move=False, by=False):
    """``(fig or [panels], warnings, renderer-or-document)`` of one build;
    *move* sets the close range slider to its lower 60% first."""
    sub = tmp_path / ("da%d" % next(_DA_SEQ))
    sub.mkdir()
    spec = _spec(plots, formats=_DA_FMT, graph_options=go,
                 filters=[_filter("range", "close")] if move else None)
    if mode == "saved":
        r, w = _saved(sub, spec, _DA)
        if move:
            figs = tda._move_saved(r, "RangeSlider", _DA_MOVE)
        else:
            figs = list(r.figures.values())
        return (figs if by else figs[0]), w, r
    doc, w = _served(sub, spec, _DA)
    if move:
        figs = tda._move_served(doc, "RangeSlider", _DA_MOVE)
    else:
        figs = tb_panels(doc)
    return (figs if by else figs[0]), w, doc


def tb_panels(doc):
    import test_by_scales as tb
    return tb._panels(tb._figs_of(doc.roots))


def _da_layer(fig, glyph_type, k=0):
    return [r for r in fig.renderers
            if type(r.glyph).__name__ == glyph_type
            and not dr._dash_is_swatch(r)][k]


def _da_units(r, prop):
    """The values renderer *r* draws for *prop*, in axis units."""
    spec = getattr(r.glyph, prop)
    field = _fld(spec)
    col = dr._dash_float_values(r.data_source.data[field], coerce=True)
    k = _units_of(spec)
    return dr._dash_date_units(col, k) if k else col


def _da_inner(fig, letter, name="default"):
    rng = (getattr(fig, letter + "_range") if name == "default"
           else getattr(fig, "extra_%s_ranges" % letter)[name])
    return dr._dash_range_hull(rng)


def _da_axis(fig, side, name="default"):
    attr = ("x" if side in ("below", "above") else "y") + "_range_name"
    return [a for a in getattr(fig, side) if hasattr(a, "formatter")
            and getattr(a, attr, "default") == name][0]


def _no_note(ws, *words):
    return [w for w in ws if any(t in w for t in words)]


# ---------------------------------------------------------------------------
# Literal layers
# ---------------------------------------------------------------------------

class TestLiteralLayersOnADateAxis:

    def test_the_literal_reader(self):
        m = dr.GlyphMapper.__new__(dr.GlyphMapper)
        f = figure()
        dr._dash_mark_date_axes(f, "td", None)
        got, off = m._literal_on_axis(f, [15400.0, 99999999.0, 1e9,
                                          float("nan")], "x")
        assert got[:2].tolist() == [_ms(15400), 8639684294400000.0]
        assert np.isnan(got[2]) and np.isnan(got[3])
        assert off.tolist() == [False, False, True, False]
        for marks in (None, (None, None)):
            g = figure()
            if marks:
                dr._dash_mark_date_axes(g, *marks)
            v, o = m._literal_on_axis(g, [15400.0], "x")
            assert v.tolist() == [15400.0] and not o.any()

    @pytest.mark.parametrize("mode", MODES)
    def test_literals_are_placed_at_their_dates(self, tmp_path, mode):
        line = _L("line", "close", "date")
        pts = {"x0": 15400.0, "dx": 25.0, "y": [1300.0, 1300.0, 1300.0]}
        fn = {"type": "function", "expr": "1300",
              "options": {"range": "15400 15450", "n": "3"}}
        cases = [
            ("scatteri", [line, _si((1300, 15400))], "Scatter", "x",
             [_ms(15400)]),
            ("pci", [line, {"type": "pci", "options": {},
                            "values": [[1200.0, 15400.0, 1400.0, 15450.0]]}],
             "Segment", "x1", [_ms(15450)]),
            ("pcarrowi", [line, {"type": "pcarrowi", "options": {},
                                 "values": [[1200.0, 15400.0, 1400.0,
                                             15450.0]]}],
             "Segment", "x0", [_ms(15400)]),
            ("function", [line, fn], "Line", "x",
             [_ms(15400), _ms(15425), _ms(15450)]),
            ("function_points", [line, dict(fn, points=pts)], "Line", "x",
             [_ms(15400), _ms(15425), _ms(15450)]),
            ("monthly", [_L("line", "close", "m"), _si((1300, 504))],
             "Scatter", "x", [float(dr._dash_units_to_axis([504], "tm")[0])]),
            ("date_y", [_L("line", "date", "obs"), _si((15000, 6))],
             "Scatter", "y", [_ms(15000)]),
        ]
        bad = []
        for name, plots, gt, prop, want in cases:
            fig, _w, _o = _da_fig(tmp_path, mode, plots)
            r = _da_layer(fig, gt, 0 if gt != "Line" else 1)
            got = _da_units(r, prop).tolist()
            if got != want:
                bad.append((name, got, want))
        # function with no range() runs 0..1 in days, and the hull reaches it.
        fig, _w, _o = _da_fig(tmp_path, mode, [line, {
            "type": "function", "expr": "1300", "options": {"n": "3"}}])
        got = _da_units(_da_layer(fig, "Line", 1), "x").tolist()
        if got != [_ms(0), _ms(0.5), _ms(1)] \
                or _da_inner(fig, "x")[0] > _ms(0):
            bad.append(("norange", got, _da_inner(fig, "x")))
        # A literal on a second date axis.
        fig, _w, _o = _da_fig(tmp_path, mode, [
            line, _L("line", "d2", "date", yaxis="2"),
            _si((15300, 15300), yaxis="2")])
        r = _da_layer(fig, "Scatter")
        if _da_units(r, "y").tolist() != [_ms(15300)] \
                or r.y_range_name != "y2":
            bad.append(("y2", _da_units(r, "y").tolist(), r.y_range_name))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_the_literal_is_in_the_hull(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("line", "close", "date"), _si((1300, 15400))])
        assert _da_inner(fig, "x")[1] >= _ms(15400)

    @pytest.mark.parametrize("mode", MODES)
    def test_the_positions_hold_after_a_filter_move(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("line", "close", "date"), _si((1300, 15400))], move=True)
        assert _da_units(_da_layer(fig, "Scatter"), "x").tolist() == [
            _ms(15400)]
        assert _da_inner(fig, "x")[1] >= _ms(15400)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_literal_on_a_numeric_axis_is_unchanged(self, tmp_path, mode):
        for x in (6.0, 99999999.0):
            fig, w, _o = _da_fig(tmp_path, mode, [
                _L("scatter", "close", "obs"), _si((1300, x))])
            assert _da_units(_da_layer(fig, "Scatter", 1), "x").tolist() \
                == [x]
            assert not _no_note(w, "scatteri"), w


# ---------------------------------------------------------------------------
# Literals past Stata's dates (A77, ratified 06oct2026)
# ---------------------------------------------------------------------------

_KINDS = ("td", "tc", "tC", "tw", "tm", "tq", "th", "ty")


def _period_first_day(kind, y):
    """The Stata number of the first period of year *y*."""
    per = {"tw": 52, "tm": 12, "tq": 4, "th": 2}[kind]
    return (y - 1960) * per


class TestOffDateLiterals:

    def _cases(self):
        nan = float("nan")
        c = [
            ("td", -679351, -59011545600000.0), ("td", -679350,
                                                  -59011459200000.0),
            ("td", 2936549, 253402214400000.0),
            ("td", 2936550, 253402300800000.0),
            ("td", -1500000, -129915619200000.0),
            ("td", 99999999, 8639684294400000.0),
            ("td", 100003653, 8.64e15), ("td", 100003654, nan),
            ("td", -99996347, -8.64e15), ("td", -99996348, nan),
            ("td", 14977.5, _ms(14977) + 43200000),
            ("tc", 8640315619200000, 8.64e15),
            ("tc", 8640315619200001, nan),
            ("tc", -8639684380800000, -8.64e15),
            ("tc", -8639684380800001, nan),
            ("tm", 96479, _np_ms(9999, 12, 1)),
            ("tm", 96480, _np_ms(10000, 1, 1)),
            ("tm", -22321, _np_ms(99, 12, 1)),
            ("tm", -23520, _np_ms(0, 1, 1)),
            ("tm", -22920, _np_ms(50, 1, 1)),
            ("tm", 96480.5, (_np_ms(10000, 1, 1) + _np_ms(10000, 2, 1)) / 2),
            ("ty", 50, _np_ms(50, 1, 1)), ("ty", 0, _np_ms(0, 1, 1)),
            ("ty", -500, -77945673600000.0),
            ("ty", 275760, _np_ms(275760, 1, 1)), ("ty", 275761, nan),
            ("ty", 300001, nan),
        ]
        for y in (99, 100, 9999, 10000):
            c.append(("ty", y, _np_ms(y, 1, 1)))
        for k in ("tw", "tq", "th"):
            for y in (99, 10000):
                c.append((k, _period_first_day(k, y), _np_ms(y, 1, 1)))
        for k in _KINDS:
            for v in (nan, float("inf"), float("-inf"), 1e300, -1e300, "A"):
                c.append((k, v, nan))
        return c

    def test_the_literal_converter(self):
        bad = []
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            for kind, v, want in self._cases():
                got = float(dr._dash_literal_to_ms([v], kind)[0])
                same = (np.isnan(got) and np.isnan(want)) or got == want
                if not same:
                    bad.append((kind, v, got, want))
        assert not bad, bad

    def test_it_equals_the_stata_rule_inside_stata_dates(self):
        rnd = np.random.default_rng(35)
        bad = []
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            for kind in _KINDS:
                lo, hi = dr._dash_date_units(np.array(
                    [dr._STATA_MS_MIN, dr._STATA_MS_MAX], dtype=float)
                    + dr._STATA_EPOCH_UNIX_MS, kind)
                v = rnd.uniform(lo, hi, 10000)
                if kind not in ("td", "tc", "tC"):
                    v[:5000] = np.floor(v[:5000])
                v = np.concatenate([v, [lo, hi]])
                a = dr._dash_literal_to_ms(v, kind)
                b = dr._dash_units_to_axis(v, kind)
                if np.isnan(a).any() or not np.array_equal(a, b):
                    bad.append(kind)
        assert not bad, bad

    def test_the_civil_calendar_round_trips(self):
        years = (list(range(-1000, -989)) + list(range(-1, 102))
                 + [1959, 1960, 1961, 9998, 9999, 10000, 10001, 275759])
        bad = []
        for y in years:
            for m in range(1, 13):
                for d in (1, None):
                    if d is None:
                        nxt = (_np_ms(y + (m == 12), m % 12 + 1, 1)
                               // 86400000)
                        z_want = nxt - 1
                        dd = int(z_want - _np_ms(y, m, 1) // 86400000 + 1)
                    else:
                        z_want = _np_ms(y, m, 1) // 86400000
                        dd = 1
                    z = int(dr._dash_days_from_civil(y, m, dd))
                    back = tuple(int(t) for t in dr._dash_civil_from_days(z))
                    if z != z_want or back != (y, m, dd):
                        bad.append((y, m, dd, z, z_want, back))
        assert not bad, bad[:10]

    def test_the_number_reader(self):
        bad = []
        for kind, v, want in self._cases():
            if isinstance(v, str) or not np.isfinite(want):
                continue
            got = dr._dash_stata_number_of(want, kind)
            exp = float(v) if kind in ("td", "tc", "tC") \
                else float(np.floor(float(v)))
            if got != exp:
                bad.append((kind, v, got, exp))
        rnd = np.random.default_rng(7)
        for kind in _KINDS:
            ms = rnd.uniform(dr._STATA_MS_MIN, dr._STATA_MS_MAX, 10000) \
                + dr._STATA_EPOCH_UNIX_MS
            for x in ms[:: 10]:
                if dr._dash_stata_number_of(x, kind) != \
                        dr._dash_stata_value_of(x, kind):
                    bad.append((kind, x))
                    break
            for x in (float("nan"), float("inf"), float("-inf"),
                      8.64e15 + 1):
                if dr._dash_stata_number_of(x, kind) is not None:
                    bad.append((kind, x))
        if dr._dash_stata_number_of(0.0, "xx") is not None:
            bad.append("kind")
        assert not bad, bad

    def test_the_js_number_reader_equals_the_python_one(self):
        rnd = np.random.default_rng(11)
        probes = [float(w) for _k, _v, w in self._cases() if np.isfinite(w)]
        probes += rnd.uniform(-8.64e15, 8.64e15, 10000).tolist()
        probes += [_np_ms(50, 1, 1), _np_ms(0, 1, 1), 8.64e15, -8.64e15]
        src = ("'use strict';\n" + dr._DASH_FMT_JS
               + "\nconst probes = %s;\nconst kinds = %s;\n"
               "const out = {};\nfor (const k of kinds) out[k] = "
               "probes.map((p) => dash_stata_number_of(p, k));\n"
               "out.nan = [dash_stata_number_of(NaN, 'td'), "
               "dash_stata_number_of(8.64e15 + 1, 'td')];\n"
               "console.log(JSON.stringify(out));\n"
               % (json.dumps(probes), json.dumps(list(_KINDS))))
        got = run_js(src)
        bad = []
        for k in _KINDS:
            for p, g in zip(probes, got[k]):
                if g != dr._dash_stata_number_of(p, k):
                    bad.append((k, p, g))
        assert got["nan"] == [None, None]
        js = dict(zip(probes, got["ty"]))
        assert js[_np_ms(50, 1, 1)] == 50 and js[_np_ms(0, 1, 1)] == 0
        assert dict(zip(probes, got["tm"]))[_np_ms(50, 1, 1)] == -22920
        assert dict(zip(probes, got["td"]))[_np_ms(50, 1, 1)] == -697612
        assert "Date.UTC(" not in dr._DASH_FMT_JS
        assert "Date" not in dr._DASH_DATE_UNITS_JS
        assert not bad, bad[:10]

    def test_the_tick_text_past_stata_dates(self):
        f = dr._dash_fmt_tick_formatter("%td", "td", "", {})
        ticks = [8639684294400000.0, -59011545600000.0, _ms(14977)]
        got = js_texts(f, ticks, "tick")
        assert got == ["1.00e+08", "-679351", "02jan2001"], got
        assert got == [dr._dash_fmt_text(dr._dash_stata_number_of(t, "td"),
                                         "%td") for t in ticks]
        fy = dr._dash_fmt_tick_formatter("%ty", "ty", "", {})
        got = js_texts(fy, [float(_np_ms(-500, 1, 1)),
                            float(_np_ms(50, 1, 1))], "tick")
        assert got == ["-5.0e+02", "50"], got

    def test_the_off_date_ticks_rule(self):
        lo, hi = _ms(14977), 8639684294400000.0
        want = [float(dr._dash_literal_to_ms([t], "td")[0])
                for t in dr._dash_natscale_ticks(14977, 99999999, 5)]
        assert dr._dash_off_date_ticks(lo, hi, 5, "td") == want
        assert dr._dash_axis_count_ticks(lo, hi, 5, "td") == want
        ty = dr._dash_off_date_ticks(float(_np_ms(-500, 1, 1)),
                                     float(_np_ms(2002, 1, 1)), 5, "ty")
        assert _np_ms(0, 1, 1) in ty and -2208988800000.0 not in ty
        assert dr._dash_off_date_ticks(float("nan"), hi, 5, "td") is None

    _DRAWN = [
        ("scatteri_10000", [_si((1300, 2936550))], "Scatter", "x",
         [253402300800000.0]),
        ("scatteri_year99", [_si((1300, -679351))], "Scatter", "x",
         [-59011545600000.0]),
        ("pci_negative", [{"type": "pci", "options": {}, "values": [
            [1200.0, -1500000.0, 1400.0, 15400.0]]}], "Segment", "x0",
         [-129915619200000.0]),
        ("pcarrowi_10000", [{"type": "pcarrowi", "options": {}, "values": [
            [1200.0, 15400.0, 1400.0, 2936550.0]]}], "Segment", "x1",
         [253402300800000.0]),
        ("function_offrange", [{"type": "function", "expr": "1300",
                                "options": {"range": "-700000 -679000",
                                            "n": "2"}}], "Line", "x",
         "literal"),
    ]

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_in_both_modes(self, tmp_path, mode):
        rows = [(n, [_L("line", "close", "date")] + p, g, prop, w)
                for n, p, g, prop, w in self._DRAWN]
        rows += [
            ("ty_negative", [_L("line", "close", "yr"), _si((1300, -500))],
             "Scatter", "x", [-77945673600000.0]),
            ("tm_10000", [_L("line", "close", "m"), _si((1300, 96480))],
             "Scatter", "x", [float(_np_ms(10000, 1, 1))]),
            ("y_axis", [_L("line", "date", "obs"), _si((99999999, 6))],
             "Scatter", "y", [8639684294400000.0]),
        ]
        bad = []
        for name, plots, gt, prop, want in rows:
            if want == "literal":
                want = dr._dash_literal_to_ms([-700000, -679000],
                                              "td").tolist()
            fig, w, _o = _da_fig(tmp_path, mode, plots)
            k = 1 if gt == "Line" else 0
            got = _da_units(_da_layer(fig, gt, k), prop).tolist()
            letter = prop[0]
            side = "below" if letter == "x" else "left"
            lo, hi = _da_inner(fig, letter)
            if got != want or not isinstance(_da_axis(fig, side),
                                             DatetimeAxis) \
                    or not (lo <= min(want) and max(want) <= hi) \
                    or _no_note(w, "scatteri", "pci", "pcarrowi",
                                "function:"):
                bad.append((name, got, want, (lo, hi), w))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_after_a_filter_move(self, tmp_path, mode):
        for plots, want in (
                ([_L("line", "close", "date"), _si((1300, 2936550))],
                 253402300800000.0),
                ([_L("line", "close", "yr"), _si((1300, -500))],
                 -77945673600000.0)):
            fig, _w, _o = _da_fig(tmp_path, mode, plots, move=True)
            assert _da_units(_da_layer(fig, "Scatter"), "x").tolist() == [
                want]
            lo, hi = _da_inner(fig, "x")
            assert lo <= want <= hi
            assert isinstance(_da_axis(fig, "below").ticker, FixedTicker)

    @pytest.mark.parametrize("mode", MODES)
    def test_the_off_date_axis_is_ticked_in_stata_numbers(self, tmp_path,
                                                          mode):
        for plots, kind in (
                ([_L("line", "close", "date"), _si((1300, 99999999))], "td"),
                ([_L("line", "close", "yr"), _si((1300, -500))], "ty")):
            fig, _w, _o = _da_fig(tmp_path, mode, plots)
            ax = _da_axis(fig, "below")
            _c, vals = dr._dash_secondary_values(fig, "x_range_name",
                                                 "default")
            assert isinstance(ax.ticker, FixedTicker)
            assert list(ax.ticker.ticks) == dr._dash_off_date_ticks(
                min(vals), max(vals), 5, kind)
            if kind == "ty":
                assert _np_ms(0, 1, 1) in ax.ticker.ticks
                assert -2208988800000.0 not in ax.ticker.ticks
            for side in ("below", "left", "above", "right"):
                for a in getattr(fig, side):
                    assert not isinstance(getattr(a, "ticker", None),
                                          DatetimeTicker)
                    assert not isinstance(getattr(a, "formatter", None),
                                          DatetimeTickFormatter)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_literal_past_the_browser_is_left_out_with_one_note(
            self, tmp_path, mode):
        fig, w, _o = _da_fig(tmp_path, mode, [
            _L("line", "close", "date"), _si((1300, 1e9)),
            _si((1300, 1e300)), _si((1300, 15400))])
        sc = [r for r in fig.renderers if type(r.glyph).__name__ == "Scatter"]
        assert [len(r.data_source.data["x"]) for r in sc] == [0, 0, 1]
        note = ("dash: scatteri: 1 point(s) past the dates a browser can "
                "draw (years -271821 to 275760) not drawn.")
        assert [x for x in w if "past the dates" in x] == [note], w
        for r in fig.renderers:
            json.dumps({k: list(map(float, v)) if k in ("x", "y") else None
                        for k, v in r.data_source.data.items()},
                       allow_nan=False)

    def test_the_served_build_names_the_literal_past_the_browser(
            self, tmp_path):
        spec = _spec([_L("line", "close", "date"), _si((1300, 1e9))],
                     formats=_DA_FMT)
        sp, dp = _write(tmp_path, spec, _DA)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp, dp).build(
                os.path.join(str(tmp_path), "app.py"), trial=True)
        got = [str(c.message) for c in caught
               if "past the dates a browser" in str(c.message)]
        assert len(got) == 1, got


# ---------------------------------------------------------------------------
# Range and pc layers
# ---------------------------------------------------------------------------

class TestRangeAndPcLayersGetADateAxis:

    def test_the_axis_names_rule(self):
        f = dr._dash_layer_axis_names
        assert f({"type": "rarea", "yvar1": "a", "yvar2": "b",
                  "xvar": "c", "options": {}}, "yvar") == (1, ["a", "b"])
        assert f({"type": "rarea", "yvar1": "a", "yvar2": "b",
                  "xvar": "c", "options": {}}, "xvar") == (1, ["c"])
        assert f({"type": "pcspike", "y1var": "a", "x1var": "b",
                  "y2var": "c", "x2var": "d",
                  "options": {"xaxis": "2"}}, "xvar") == (2, ["b", "d"])
        assert f({"type": "histogram", "var": "a", "options": {}},
                 "xvar") == (1, ["a"])
        assert f({"type": "histogram", "var": "a", "options": {}},
                 "yvar") == (None, [])
        assert f({"type": "scatteri", "options": {}}, "xvar") == (None, [])
        assert f({"type": "scatter", "yvar": "", "xvar": "x",
                  "options": {"yaxis": " 2"}}, "yvar") == (2, [])

    _RANGE = ("rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
              "rcapsym", "rscatter", "tsrline")
    _PC = ("pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter")

    @pytest.mark.parametrize("mode", MODES)
    def test_range_and_pc_types_get_a_date_axis(self, tmp_path, mode):
        rows = [(t, {"type": t, "yvar1": "date", "yvar2": "d2",
                     "xvar": "close", "options": {}}, "left", "below")
                for t in self._RANGE]
        rows += [(t, {"type": t, "y1var": "date", "x1var": "close",
                      "y2var": "d2", "x2var": "volume", "options": {}},
                  "left", "below") for t in self._PC]
        rows += [(t + "_x", {"type": t, "y1var": "close", "x1var": "date",
                             "y2var": "volume", "x2var": "d2",
                             "options": {}}, "below", "left")
                 for t in self._PC]
        bad = []
        for name, plot, dside, nside in rows:
            fig, _w, _o = _da_fig(tmp_path, mode, [plot])
            d, n = _da_axis(fig, dside), _da_axis(fig, nside)
            if not isinstance(d, DatetimeAxis) \
                    or dict(d.formatter.args).get("fmt") != "%td" \
                    or isinstance(n, DatetimeAxis):
                bad.append((name, type(d).__name__, type(n).__name__))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_a_pc_with_one_date_end_is_mixed(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [{
            "type": "pcspike", "y1var": "date", "x1var": "obs",
            "y2var": "close", "x2var": "obs", "options": {}}])
        assert not isinstance(_da_axis(fig, "left"), DatetimeAxis)
        r = _da_layer(fig, "Segment")
        assert _units_of(r.glyph.y0) == "td"
        assert _units_of(r.glyph.y1) is None
        assert _da_units(r, "y0").tolist() == _DA["date"].tolist()

    @pytest.mark.parametrize("mode", MODES)
    def test_the_axis_reads_the_first_bounds_format(self, tmp_path, mode):
        sub = tmp_path / "fmt"
        sub.mkdir()
        spec = _spec([{"type": "rarea", "yvar1": "date", "yvar2": "d2",
                       "xvar": "close", "options": {}}],
                     formats=dict(_DA_FMT, date="%tdCCYY-NN-DD"))
        if mode == "saved":
            fig = _saved(sub, spec, _DA)[0].figures["g1"]
        else:
            fig = _served_fig(_served(sub, spec, _DA)[0])
        assert dict(_da_axis(fig, "left").formatter.args)["fmt"] == \
            "%tdCCYY-NN-DD"

    @pytest.mark.parametrize("mode", MODES)
    def test_after_a_filter_move(self, tmp_path, mode):
        # Two range layers and nothing else: at the base no layer named a
        # date on y (a range layer counted only the fallback), so the axis
        # was a LinearAxis in ms before and after the move.  (An lfit of
        # the date beside them already made a date axis at the base.)
        fig, _w, _o = _da_fig(tmp_path, mode, [
            {"type": "rarea", "yvar1": "date", "yvar2": "d2",
             "xvar": "close", "options": {}},
            {"type": "rcap", "yvar1": "date", "yvar2": "d2",
             "xvar": "close", "options": {}}], move=True)
        assert isinstance(_da_axis(fig, "left"), DatetimeAxis)
        r = _da_layer(fig, "VArea")
        assert _units_of(r.glyph.y1) is None and _units_of(r.glyph.y2) is None
        lo, hi = _da_inner(fig, "y")
        assert lo <= _ms(14977) and _ms(15037) <= hi, (lo, hi)


# ---------------------------------------------------------------------------
# Second axes
# ---------------------------------------------------------------------------

class TestASecondAxisLeavesThePrimaryDate:

    def test_the_decision_partitions_by_axis(self):
        plots = [_L("scatter", "date", "close"),
                 _L("scatter", "volume", "close", yaxis="2")]
        dv = {"date": "td", "d2": "td"}
        assert dr._dash_figure_date_kind(plots, "yvar", "", dv, 1) == "td"
        assert dr._dash_figure_date_kind(plots, "yvar", "", dv,
                                         axis_no=2) is None
        assert dr._dash_axis_vars(plots, axis_no=2) == ("", "volume")
        # With no layer on axis 1 every layer counts there (D-35g).
        lone = [_L("scatter", "date", "close", yaxis="2")]
        assert dr._dash_figure_date_kind(lone, "yvar", "", dv) == "td"

    @pytest.mark.parametrize("mode", MODES)
    def test_a_numeric_second_axis_keeps_the_date_axis(self, tmp_path, mode):
        for plots, dside, nside, name in (
                ([_L("scatter", "date", "close"),
                  _L("scatter", "volume", "close", yaxis="2")],
                 "left", "right", "y2"),
                ([_L("scatter", "close", "date"),
                  _L("scatter", "close", "obs", xaxis="2")],
                 "below", "above", "x2")):
            fig, _w, _o = _da_fig(tmp_path, mode, plots)
            assert isinstance(_da_axis(fig, dside), DatetimeAxis)
            assert not isinstance(_da_axis(fig, nside, name), DatetimeAxis)


class TestASecondDateAxis:

    _Y2 = [_L("line", "close", "date"), _L("line", "d2", "date", yaxis="2")]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_second_axis_is_a_date_axis(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._Y2)
        ax = _da_axis(fig, "right", "y2")
        assert isinstance(ax, DatetimeAxis)
        assert dict(ax.formatter.args)["fmt"] == "%td"
        assert dr._dash_axis_date_kind(fig, "y2") == "td"
        lo, hi = _da_inner(fig, "y", "y2")
        # Flipped: test_a_date_second_axis_is_a_date_axis -- a hull of the
        # data alone (Bokeh's DatetimeTicker) was wrong because twoway ticks
        # date axes by tsnatscale over the data and spans its ticks (P1.3b,
        # M1).
        dlo, dhi = dr._dash_layer_extent(fig.renderers, "y_range_name", "y2",
                                         "td")
        ticks = tb_major(ax)
        assert ticks == dr._dash_axis_count_ticks(dlo, dhi, 5, "td"), ticks
        assert abs(lo - min(ticks + [dlo])) <= 1 \
            and abs(hi - max(ticks + [dhi])) <= 1, (lo, hi)
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("scatter", "close", "obs"),
            _L("scatter", "close", "date", xaxis="2")])
        assert isinstance(_da_axis(fig, "above", "x2"), DatetimeAxis)

    @pytest.mark.parametrize("mode", MODES)
    def test_count_ticks_on_a_date_y2(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._Y2, go={"ylabel2": "#5"})
        ticks = tb_major(_da_axis(fig, "right", "y2"))
        lo, hi = dr._dash_layer_extent(fig.renderers, "y_range_name", "y2",
                                       "td")
        assert ticks == dr._dash_axis_count_ticks(lo, hi, 5, "td"), ticks
        assert all((t - _E) % 86400000 == 0 for t in ticks)

    @pytest.mark.parametrize("mode", MODES)
    def test_line_range_and_labels_on_a_date_y2_are_dates(self, tmp_path,
                                                         mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._Y2, go={
            "yline2": "15200", "yscale2": "range(14900 15500)",
            "ylabel2": "15000 15300"})
        spans = [s for s in fig.center if isinstance(s, Span)
                 and s.y_range_name == "y2"]
        assert [s.location for s in spans] == [_ms(15200)]
        lo, hi = _da_inner(fig, "y", "y2")
        assert abs(lo - _ms(14900)) < 1 and abs(hi - _ms(15500)) < 1
        assert tb_major(_da_axis(fig, "right", "y2")) == [_ms(15000),
                                                          _ms(15300)]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_fit_on_a_date_y2_is_in_ms(self, tmp_path, mode):
        for move in (False, True):
            fig, _w, _o = _da_fig(tmp_path, mode, self._Y2 + [
                _L("lfit", "d2", "date", yaxis="2")], move=move)
            fit = [r for r in fig.renderers
                   if type(r.glyph).__name__ == "Line"
                   and r.y_range_name == "y2"][-1]
            y = _da_units(fit, "y")
            y = y[np.isfinite(y)]
            assert y.size and _ms(15007) - 1 <= y.min() \
                and y.max() <= _ms(15337) + 1, (move, y)
            lo, hi = _da_inner(fig, "y", "y2")
            assert lo > 1e11, (move, lo)

    @pytest.mark.parametrize("mode", MODES)
    def test_yscale2_log_on_a_date_axis_draws_dates(self, tmp_path, mode):
        fig, w, _o = _da_fig(tmp_path, mode, self._Y2,
                             go={"yscale2": "log"})
        assert isinstance(_da_axis(fig, "right", "y2"), DatetimeAxis)
        assert [x for x in w if "yscale2(log)" in x] == [
            "dash: yscale2(log) is meaningless for the date variable 'd2'; "
            "drawing a date axis instead."], w


def tb_major(ax):
    import test_by_scales as tb
    return tb._major_ticks(ax)


# ---------------------------------------------------------------------------
# A date beside a number
# ---------------------------------------------------------------------------

class TestTheUnitRule:

    def _figs(self):
        marked = figure()
        dr._dash_mark_date_axes(marked, "td", None, None, "tm")
        unmarked = figure()
        return marked, unmarked

    def test_axis_kind_reads_the_layers_axis(self):
        m = dr.GlyphMapper.__new__(dr.GlyphMapper)
        marked, unmarked = self._figs()
        assert m._axis_kind(marked, "x") == "td"
        assert m._axis_kind(marked, "y") is None
        assert m._axis_kind(marked, "y", {"yaxis": "2"}) == "tm"
        assert m._axis_kind(marked, "x", {"xaxis": "2"}) is None
        assert m._axis_kind(unmarked, "x") is None

    def test_unit_kind_follows_the_axis(self):
        m = dr.GlyphMapper.__new__(dr.GlyphMapper)
        m.date_vars = {"date": "td", "m": "tm"}
        marked, unmarked = self._figs()
        assert m._unit_kind(marked, "date", "x") == "td"
        assert m._unit_kind(marked, "date", "y") is None
        assert m._unit_kind(marked, "m", "y", {"yaxis": "2"}) == "tm"
        assert m._unit_kind(marked, "close", "x") is None
        assert m._unit_kind(unmarked, "date", "y") == "td"


class TestADateBesideANumber:

    _MIX = [_L("scatter", "close", "date"), _L("scatter", "close", "obs")]

    def test_the_unit_format_rule(self):
        dv = {"date": "td", "m": "tm"}
        f = dr._dash_axis_unit_format
        assert f(self._MIX, "x", dv, _DA_FMT) == "%td"
        assert f(self._MIX[::-1], "x", dv, _DA_FMT) == ""
        assert f([_L("lfit", "close", "date"), self._MIX[1]], "x", dv,
                 _DA_FMT) == ""
        assert f([_si((1, 2)), self._MIX[1]], "x", dv, _DA_FMT) == ""
        assert f([_L("scatter", "close", "m"), self._MIX[1]], "x", dv,
                 _DA_FMT) == "%tm"

    @pytest.mark.parametrize("mode", MODES)
    def test_the_raw_date_is_drawn_in_stata_units(self, tmp_path, mode):
        fig, w, _o = _da_fig(tmp_path, mode, self._MIX)
        assert not isinstance(_da_axis(fig, "below"), DatetimeAxis)
        d, o = _da_layer(fig, "Scatter", 0), _da_layer(fig, "Scatter", 1)
        assert _units_of(d.glyph.x) == "td"
        assert _da_units(d, "x").tolist() == _DA["date"].tolist()
        assert _units_of(o.glyph.x) is None
        assert _units_of(d.glyph.y) is None
        for attr in ("selection_glyph", "nonselection_glyph", "hover_glyph",
                     "muted_glyph"):
            g = getattr(d, attr)
            if g is not None and hasattr(g, "x"):
                assert _units_of(g.x) == "td", attr
        lo, hi = _da_inner(fig, "x")
        assert 0 <= hi <= 20000 and -1000 <= lo, (lo, hi)
        assert not _no_note(w, "date"), w

    @pytest.mark.parametrize("mode", MODES)
    def test_labels_and_jitter_follow(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("scatter", "close", "date", mlabel="close", jitter="5"),
            self._MIX[1]])
        d = _da_layer(fig, "Scatter", 0)
        assert _units_of(d.glyph.x) == "td"
        assert _fld(d.glyph.x) != "date"
        labs = [a for a in fig.center if isinstance(a, LabelSet)]
        assert labs and all(_units_of(a.x) == "td" for a in labs)

    @pytest.mark.parametrize("mode", MODES)
    def test_explicit_labels_count_and_range(self, tmp_path, mode):
        bad = []
        for go in ({"xlabel": "0 5000 10000 15000"}, {"xlabel": "#5"},
                   {"xscale": "range(0 16000)"}):
            fig, _w, _o = _da_fig(tmp_path, mode, self._MIX, go=go)
            lo, hi = _da_inner(fig, "x")
            if not (-1 <= lo and hi <= 16001):
                bad.append((go, lo, hi))
            if go.get("xlabel") == "#5":
                # Flipped: test_explicit_labels_count_and_range -- natscale's
                # 0(5000)15000 was wrong because twoway ticks a date beside
                # a number by tsnatscale in Stata units, 01jan1960 ...
                # 01jan2000 (P1.3b, M1).
                t = tb_major(_da_axis(fig, "below"))
                if t != [0.0, 3653.0, 7305.0, 10958.0, 14610.0]:
                    bad.append((go, t))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_by_panels_share_one_scale_in_stata_units(self, tmp_path, mode):
        figs, _w, _o = _da_fig(tmp_path, mode, self._MIX, go={"by": "g"},
                               by=True)
        figs = [f for f in figs if f.renderers]
        assert len(figs) >= 2
        assert len({id(f.x_range) for f in figs}) == 1
        lo, hi = _da_inner(figs[0], "x")
        assert -1000 <= lo and hi <= 20000, (lo, hi)

    @pytest.mark.parametrize("mode", MODES)
    def test_the_labels_are_the_first_layers_format(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._MIX)
        assert js_texts(_da_axis(fig, "below").formatter, [0.0, 15000.0],
                        "tick") == ["01jan1960", "25jan2001"]
        for plots in (self._MIX[::-1],
                      [_L("lfit", "close", "date"), self._MIX[1]]):
            fig, _w, _o = _da_fig(tmp_path, mode, plots)
            fmt = dict(getattr(_da_axis(fig, "below").formatter, "args",
                               None) or {}).get("fmt", "")
            assert not fmt.startswith("%t"), fmt

    @pytest.mark.parametrize("mode", MODES)
    def test_minmax_reads_stata_units(self, tmp_path, mode):
        bad = []
        for opt in ("xlabel", "xtick"):
            # Flipped (WP-31 D6): minmax spans every layer on the axis, as
            # twoway's does (test/fixtures/axis_look_truth.json
            # minmax_two), the date's in its Stata units beside obs's.
            for plots, want in ((self._MIX, [1.0, 15307.0]),
                                ([_L("lfit", "close", "date"),
                                  self._MIX[1]], [1.0, 15307.0]),
                                (self._MIX[::-1], [1.0, 15307.0])):
                fig, _w, _o = _da_fig(tmp_path, mode, plots,
                                      go={opt: "minmax"})
                ax = _da_axis(fig, "below")
                t = ax.ticker
                got = (sorted(float(v) for v in dict(t.args)["extra"])
                       if opt == "xtick" and hasattr(t, "args")
                       else tb_major(ax))
                if got != want:
                    bad.append((opt, plots[0]["type"], got, want))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_after_a_filter_move(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._MIX, move=True)
        d = _da_layer(fig, "Scatter", 0)
        assert _units_of(d.glyph.x) == "td"
        lo, hi = _da_inner(fig, "x")
        assert -1000 <= lo and hi <= 20000, (lo, hi)

    def test_the_refinish_budget_holds(self):
        import time
        from bokeh.models import ColumnDataSource
        rnd = np.random.default_rng(1)
        n = 500_000
        fig = figure()
        dr._dash_mark_date_axes(fig, None, None)
        days = rnd.integers(14977, 15340, size=n).astype(float)
        fig.scatter(x={"field": "date", "transform":
                       dr._dash_date_transform("td")}, y="y",
                    source=ColumnDataSource({"date": _ms(days),
                                             "y": rnd.normal(size=n)}))
        fig.scatter("obs", "y", source=ColumnDataSource(
            {"obs": rnd.uniform(1, 12, n), "y": rnd.normal(size=n)}))
        fig._dash_margin = {"x": 0.0132, "y": 0.022}
        for ax in (fig.xaxis[0], fig.yaxis[0]):
            ax.ticker = dr._dash_default_ticker(5)
        dr._dash_finish_count_ticks(fig)
        best = 1e9
        for _ in range(3):
            t0 = time.perf_counter()
            dr._dash_refinish_axes({"g": fig}, {})
            best = min(best, time.perf_counter() - t0)
        assert dr._dash_range_hull(fig.x_range)[1] < 20000
        assert best <= 0.2, best

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_bar_beside_a_number(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("bar", "date", "obs"), _L("scatter", "close", "obs")])
        r = _da_layer(fig, "VBar")
        assert _units_of(r.glyph.top) == "td"
        base = dr._dash_float_values(r.data_source.data[
            _fld(r.glyph.bottom)], coerce=True)
        assert set(base.tolist()) == {0.0}, base

    @pytest.mark.parametrize("mode", MODES)
    def test_a_period_bar_on_a_mixed_axis_is_one_unit_wide(self, tmp_path,
                                                           mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("bar", "close", "m"), _L("scatter", "close", "obs")])
        r = _da_layer(fig, "VBar")
        assert r.glyph.width == 1.0
        assert _fld(r.glyph.x) == "m"
        assert _units_of(r.glyph.x) == "tm"
        assert dr.GlyphMapper._BAR_XC not in r.data_source.data

    @pytest.mark.parametrize("mode", MODES)
    def test_xline_on_a_mixed_axis_is_a_stata_value(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, self._MIX,
                              go={"xline": "15200"})
        assert [s.location for s in fig.center if isinstance(s, Span)] == [
            15200.0]


# ---------------------------------------------------------------------------
# The transform
# ---------------------------------------------------------------------------

class TestTheDateTransform:

    def test_one_shared_model_per_kind(self):
        cache = {}
        a = dr._dash_date_transform("td", cache)
        assert a is dr._dash_date_transform("td", cache)
        assert a is not dr._dash_date_transform("tm", cache)
        assert a.tags == ["dash_date_units:td"] and dict(a.args) == {
            "kind": "td"}
        for code in (a.func, a.v_func):
            for bad in ("eval(", "Function(", "document."):
                assert bad not in code
        assert len(dr._DASH_DATE_UNITS_JS) <= 3000

    def test_a_hostile_kind_is_refused(self):
        for k in ("td'); alert(1); //", "", None, "t" * 10000):
            with pytest.raises(ValueError):
                dr._dash_date_transform(k)

    def test_spec_units_reads_only_dash_transforms(self):
        good = dr._dash_date_transform("tq")
        foreign = CustomJSTransform(func="return x;", v_func="return xs;")
        badtag = CustomJSTransform(func="return x;", v_func="return xs;",
                                   tags=["dash_date_units:xx"])
        assert dr._dash_spec_units("date") is None
        assert dr._dash_spec_units({"field": "date"}) is None
        assert dr._dash_spec_units({"field": "d", "transform": foreign}) \
            is None
        assert dr._dash_spec_units({"field": "d", "transform": badtag}) \
            is None
        assert dr._dash_spec_units(object()) is None
        assert dr._dash_spec_units({"field": "d", "transform": good}) == "tq"
        f = figure()
        r = f.scatter(x={"field": "d", "transform": good}, y="y")
        assert dr._dash_spec_units(r.glyph.x) == "tq"

    def test_the_js_twin_equals_the_python_twin(self):
        rnd = np.random.default_rng(3)
        E = dr._STATA_EPOCH_UNIX_MS
        lo, hi = dr._STATA_MS_MIN + E, dr._STATA_MS_MAX + E
        vals = rnd.uniform(lo, hi, 10000).tolist() + [
            lo, hi, lo - 1, hi + 1, 0.0, -1.0]
        code = dr._dash_date_transform("td").v_func
        src = ("const f = new Function('kind', 'xs', \"'use strict';\\n\" "
               "+ %s);\nconst xs = %s.concat([NaN, Infinity, -Infinity, "
               "1e300]);\nconst out = {};\nfor (const k of %s) out[k] = "
               "Array.from(f(k, xs)).map((v) => Number.isNaN(v) ? null : v);"
               "\nconsole.log(JSON.stringify(out));\n"
               % (json.dumps(code), json.dumps(vals), json.dumps(list(_KINDS))))
        got = run_js(src)
        allv = np.array(vals + [np.nan, np.inf, -np.inf, 1e300])
        bad = []
        for k in _KINDS:
            want = dr._dash_date_units(allv, k)
            g = np.array([np.nan if v is None else v for v in got[k]],
                         dtype=float)
            same = (np.isnan(g) == np.isnan(want)) & (
                np.isnan(want) | (g == want))
            if not same.all():
                i = int(np.flatnonzero(~same)[0])
                bad.append((k, allv[i], g[i], want[i]))
        assert not bad, bad

    def test_the_layer_pass_rule(self):
        from bokeh.models import ColumnDataSource
        dv = {"date": "td"}
        src = ColumnDataSource({"date": [_ms(14977)], "y": [1.0]})

        def fig_with(marks):
            f = figure()
            if marks is not None:
                dr._dash_mark_date_axes(f, *marks)
            r = f.scatter("date", "y", source=src)
            return f, r
        raw = _L("scatter", "y", "date")
        f, r = fig_with((None, None))
        # The glyph and each Glyph variant the renderer has.
        assert dr._dash_layer_in_axis_units(f, [r], [], raw, dv) == 3
        assert _units_of(r.glyph.x) == "td"
        assert _units_of(r.nonselection_glyph.x) == "td"
        assert _units_of(r.glyph.y) is None
        # Never stacked on a transform already there.
        assert dr._dash_layer_in_axis_units(f, [r], [], raw, dv) == 0
        for marks, plot in (((None, None), _L("lfit", "y", "date")),
                            ((None, None), _si((1, 2))),
                            (("td", None), raw), (None, raw)):
            f, r = fig_with(marks)
            assert dr._dash_layer_in_axis_units(f, [r], [], plot, dv) == 0
            assert _units_of(r.glyph.x) is None


# ---------------------------------------------------------------------------
# Bases
# ---------------------------------------------------------------------------

class TestABaseOnADateAxis:

    def test_the_base_reader(self):
        m = dr.GlyphMapper.__new__(dr.GlyphMapper)
        m.date_vars = {"date": "td"}
        dated, mixed = figure(), figure()
        dr._dash_mark_date_axes(dated, None, "td")
        dr._dash_mark_date_axes(mixed, None, None)
        assert m._base_in_axis_units(14970.0, "date", dated, {}, "bar") \
            == _ms(14970)
        assert m._base_in_axis_units(14970.0, "date", mixed, {}, "bar") \
            == 14970.0
        assert m._base_in_axis_units(None, "date", dated, {}, "bar") is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._DASH_NOTED.clear()
            assert m._base_in_axis_units(99999999.0, "date", dated, {},
                                         "bar") == 8639684294400000.0
            assert m._base_in_axis_units(1e300, "date", dated, {},
                                         "bar") is None
        notes = [str(c.message) for c in caught]
        assert notes == [
            "dash: bar: base(1e+300) is past the dates a browser can draw "
            "(years -271821 to 275760); drawn from the default base."], notes

    @pytest.mark.parametrize("mode", MODES)
    def test_an_explicit_base_is_a_date(self, tmp_path, mode):
        bad = []
        for t, glyph, prop in (("bar", "VBar", "bottom"),
                               ("spike", "Segment", "y0"),
                               ("dropline", "Segment", "y0"),
                               ("area", "VArea", "y1")):
            for base, want in ((14970, _ms(14970)),
                               (2936550, 253402300800000.0)):
                fig, w, _o = _da_fig(tmp_path, mode, [
                    _L(t, "date", "obs", base=str(base))])
                r = _da_layer(fig, glyph)
                spec = getattr(r.glyph, prop)
                fld = _fld(spec)
                got = (set(dr._dash_float_values(
                    r.data_source.data[fld], coerce=True).tolist())
                       if fld else {float(spec.get("value") if isinstance(
                           spec, dict) else spec)})
                if got != {want} or _no_note(w, "base("):
                    bad.append((t, base, got, w))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_a_base_past_the_browser_is_the_default_with_a_note(
            self, tmp_path, mode):
        fig, w, _o = _da_fig(tmp_path, mode, [
            _L("bar", "date", "obs", base="1e300")])
        notes = [x for x in w if "base(1e+300) is past the dates" in x]
        assert len(notes) == 1, w
        r = _da_layer(fig, "VBar")
        base = dr._dash_float_values(r.data_source.data[
            _fld(r.glyph.bottom)], coerce=True)
        assert np.isfinite(base).all() and (np.abs(base) < 8.64e15).all()

    @pytest.mark.parametrize("mode", MODES)
    def test_after_a_filter_move(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [
            _L("bar", "date", "obs", base="14970")], move=True)
        r = _da_layer(fig, "VBar")
        assert _units_of(r.glyph.top) is None
        spec = r.glyph.bottom
        fld = _fld(spec)
        vals = (set(dr._dash_float_values(r.data_source.data[fld],
                                          coerce=True).tolist())
                if fld else {float(spec)})
        assert vals == {_ms(14970)}, vals


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

def _tagged(model):
    return [m for m in model.references()
            if isinstance(m, CustomJSTransform)
            and any(str(t).startswith("dash_date_units:")
                    for t in (m.tags or []))]


class TestNonDateFiguresAreUnchanged:

    #: Axis classes per case (below, left, right, above), recorded at the
    #: batch-12 base (f7e034d) in both modes.
    _CASES = {
        "scatter": ([_L("scatter", "close", "obs")], None),
        "lfit": ([_L("scatter", "close", "obs"), _L("lfit", "close", "obs")],
                 None),
        "bar": ([_L("bar", "close", "obs")], None),
        "yaxis2": ([_L("scatter", "close", "obs"),
                    _L("scatter", "volume", "obs", yaxis="2")], None),
        "xaxis2": ([_L("scatter", "close", "obs"),
                    _L("scatter", "close", "volume", xaxis="2")], None),
        "by": ([_L("scatter", "close", "obs")], {"by": "g"}),
        "colorvar": ([_L("scatter", "close", "obs", colorvar="volume")],
                     None),
    }

    @pytest.mark.parametrize("mode", MODES)
    def test_no_transform_and_the_same_axes(self, tmp_path, mode):
        bad = []
        for name, (plots, go) in self._CASES.items():
            figs, _w, owner = _da_fig(tmp_path, mode, plots, go=go, by=True)
            for f in figs:
                kinds = [type(a).__name__ for side in
                         ("below", "left", "right", "above")
                         for a in getattr(f, side) if hasattr(a, "ticker")]
                if _tagged(f) or "DatetimeAxis" in kinds \
                        or getattr(f, "_dash_date_kinds2", None) not in (
                            None, (None, None)):
                    bad.append((name, kinds))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_axis_layer_carries_no_transform(self, tmp_path, mode):
        fig, _w, _o = _da_fig(tmp_path, mode, [_L("line", "close", "date")])
        assert not _tagged(fig)


class TestTheDateAxisTruth:

    def test_the_fixture_is_stamped_and_complete(self):
        with open(_DA_TRUTH, encoding="utf-8") as fh:
            d = json.load(fh)
        assert all(k in d["_meta"] for k in ("stata_version", "born_date",
                                             "dash_commit", "extracted"))
        want = {"literals": ("scatteri_td", "pci_td", "pcarrowi_td",
                             "function_range_td", "function_norange_td",
                             "scatteri_tm", "scatteri_offrange",
                             "scatteri_ty_negative"),
                "range": ("rarea_datey", "rcap_datey"),
                "pc": ("datey", "datex"),
                "axis2": ("datey_y2num", "datex_x2num", "y2date",
                          "y2date_n5", "y2date_range", "y2_lfit"),
                "mixed": ("date_first", "obs_first", "td_tm",
                          "minmax_date_first", "minmax_lfit_first",
                          "minmax_obs_first", "bar_date_y"),
                "base": ("bar_date_base",)}
        missing = [(g, k) for g, ks in want.items() for k in ks
                   if k not in d.get(g, {})]
        assert not missing, missing
        assert d["axis2"]["y2date_range"]["y2"] == [14900.0, 15500.0]
        assert d["literals"]["scatteri_td"]["x"] == [14976.0, 15431.0]
