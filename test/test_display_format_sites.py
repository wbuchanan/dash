"""Every number-to-text site outside a KPI card writes Stata's display text
(WP-28 section 12, GAPS2 E3 and G6).

GAPS2 E3 measured it: a %td dropdown listed ``2001-12-31 00:00:00`` and a
%9.0fc one ``3799``; date sliders showed ``%d %b %Y`` and stepped span/100
days for every kind, so %tm/%tq/%ty sliders stopped mid-period; a numeric
RangeSlider showed ``0[.]00``; tooltips used ``{%F}`` for every kind but
tc, so %tC lost its time; date axes used one DatetimeTickFormatter per kind,
so a %tm axis read ``Jan 2000`` where twoway shows ``2000m1``.  GAPS2 G6: a
float 0.1 showed as ``0.10000000149011612`` in marker labels and dropdowns,
tooltips used BokehJS's basic formatter (12345.67 became ``1.235e+4``), and
``mlabformat(%9.3g)`` was named and not applied.

Each site is checked in both render modes; the saved page's JavaScript
(CustomJSTickFormatter / CustomJSHover carrying the format in ``args``) is
run under node.  The truth is section 04's writer, ``_dash_fmt_text``,
held to Stata by ``format_truth.json``; the one twoway-drawn truth, the
tick text of a %tm axis, is section 14's probe ``e3_tm_axis_lab`` in
``axis_truth.json``, and its absence FAILS, never skips.
"""
import itertools
import json
import math
import os
import re
import sys
import tempfile
import warnings
from collections import namedtuple

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (CustomJSHover, CustomJSTickFormatter,
                          DateRangeSlider, Div, HoverTool, LabelSet,
                          RangeSlider, Select, Slider)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from js_runner import JsSession, mask_parity, run_js  # noqa: E402,F401
from test_mode_parity import _fire  # noqa: E402

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_fmt_sites_")
_AXIS_TRUTH = os.path.join(_HERE, "fixtures", "axis_truth.json")
MODES = ("standalone", "served")

F01 = float(np.float32(0.1))  # a float-stored 0.1: 0.10000000149011612

# Ten auto-like rows.  when is %td from 02jan2000; whenm %tm 2000m1..m3;
# whenc/whenC one hour apart from 02jan2000 00:00:00 (Stata ms).
_DF = pd.DataFrame({
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "when": [14611.0 + i for i in range(10)],
    "whenm": [480.0, 480.0, 481.0, 481.0, 481.0, 482.0, 482.0, 482.0,
              480.0, 481.0],
    "whenq": [160.0, 160.0, 161.0, 161.0, 162.0, 162.0, 163.0, 163.0,
              160.0, 161.0],
    "whenh": [80.0, 81.0] * 5,
    "whenw": [2080.0, 2081.0, 2082.0, 2083.0, 2084.0] * 2,
    "wheny": [2000.0, 2001.0, 2002.0, 2003.0, 2004.0] * 2,
    "whenc": [14611.0 * 86_400_000 + 3_600_000.0 * i for i in range(10)],
    "whenC": [14611.0 * 86_400_000 + 3_600_000.0 * i for i in range(10)],
    "f": [float(np.float32(0.1 * (i + 1))) for i in range(10)],
})
_FORMATS = {"price": "%8.0gc", "mpg": "%8.0g", "foreign": "%8.0g",
            "when": "%td", "whenm": "%tm", "whenq": "%tq", "whenh": "%th",
            "whenw": "%tw", "wheny": "%ty", "whenc": "%tc", "whenC": "%tC",
            "f": "%9.0g"}
_STORAGE = {"price": "int", "mpg": "int", "foreign": "byte",
            "when": "float", "whenm": "float", "whenq": "float",
            "whenh": "float", "whenw": "float", "wheny": "float",
            "whenc": "double", "whenC": "double", "f": "float"}
_VL = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLN = {"foreign": "origin"}

Built = namedtuple("Built", "mode models warnings obj")


def _graph(name, plots, **go):
    opts = {"name": name}
    opts.update(go)
    return {"name": name, "graph_options": opts, "options": dict(opts),
            "plots": plots, "if_expr": "", "in_expr": ""}


def _scatter(y, x, **opts):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": opts}


def spec_of(graphs=(), filters="", formats=None, kpis=()):
    graphs = list(graphs)
    names = [g["name"] for g in graphs] + [k["name"] for k in kpis]
    return {"graphs": graphs, "kpis": list(kpis),
            "build_options": {
                "layout": "auto", "link": "", "theme": "", "scheme": "",
                "session_scheme": "", "title": "", "subtitle": "",
                "registry": " ".join(names), "tabs": "", "filter": filters,
                "filter_position": "top", "level": "95",
                "formats": dict(_FORMATS if formats is None else formats)}}


def build(mode, spec, df=None, storage=None):
    """The dashboard in *mode*: every model it holds, its warnings, and the
    renderer (saved) or document (served)."""
    df = _DF if df is None else df
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    data = make_data_json(df, _VL, _VLN)
    st = dict(_STORAGE if storage is None else storage)
    data["StataJSON"]["storageTypes"] = {k: v for k, v in st.items()
                                         if k in df.columns}
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    if mode == "standalone":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp)
            r.render()
        root = getattr(r, "_last_layout_root", None)
        models = [] if root is None else list(root.references())
        return Built(mode, models, [str(w.message) for w in caught], r)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_fmtsites_{tag}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    seen = {}
    for root in doc.roots:
        for m in root.references():
            seen[m.id] = m
    return Built(mode, list(seen.values()),
                 [str(w.message) for w in list(built) + list(caught)], doc)


def of_type(b, cls):
    return [m for m in b.models if isinstance(m, cls)]


def widget_for(b, var):
    """The filter widget over *var* (served widgets carry _dash_var; saved
    ones are in filter order, so the title names the variable)."""
    ws = [m for m in b.models
          if isinstance(m, (Select, Slider, RangeSlider, DateRangeSlider))
          or type(m).__name__ in ("DateSlider", "DatetimeRangeSlider")]
    for w in ws:
        if getattr(w, "_dash_var", None) == var:
            return w
    for w in ws:
        if (w.title or "").split(" ")[0] == var:
            return w
    raise AssertionError(f"{b.mode}: no widget over {var}: "
                         f"{[(type(w).__name__, w.title) for w in ws]}")


def js_texts(model, values, param):
    """What *model*'s JavaScript (a CustomJSTickFormatter or CustomJSHover)
    writes for each of *values*, passed as *param* ("tick" or "value"),
    under node -- the page's own code with its own args."""
    assert isinstance(model, (CustomJSTickFormatter, CustomJSHover)), (
        f"not a Stata formatter: {type(model).__name__} "
        f"{getattr(model, 'format', '')!r}")
    names = list(model.args)
    argv = [model.args[k] for k in names]
    extra = ["format", "special_vars"] if param == "value" else [
        "index", "ticks"]
    src = ("const f = new Function(...%s, %s, ...%s, %s);\n"
           "const out = %s.map((v) => f(...%s, v, undefined, undefined));\n"
           "process.stdout.write(JSON.stringify(out));"
           % (json.dumps(names), json.dumps(param), json.dumps(extra),
              json.dumps(model.code), json.dumps(values), json.dumps(argv)))
    return run_js(src)


def ms_of_td(d):
    return (d - 3653) * 86_400_000.0


def truth():
    """axis_truth.json's probes, failing (never skipping) without S14's."""
    if not os.path.exists(_AXIS_TRUTH):
        pytest.fail("section 14 must land first: axis_truth.json is missing")
    with open(_AXIS_TRUTH, encoding="utf-8") as fh:
        t = json.load(fh)
    probes = t.get("probes", {})
    for pid in ("e3_tm_axis_lab", "e3_tm_axis"):
        if pid not in probes:
            pytest.fail(f"section 14 must land first: axis_truth.json has "
                        f"no {pid} probe")
    return probes


# ---------------------------------------------------------------------------
# Dropdowns
# ---------------------------------------------------------------------------

class TestDropdown:

    @pytest.mark.parametrize("mode", MODES)
    def test_labels_are_statas_text_in_both_modes(self, mode):
        b = build(mode, spec_of(
            [_graph("g1", [_scatter("mpg", "price")])],
            filters=" || ".join(f"{v}, type(dropdown)"
                                for v in ("price", "when", "whenm", "f"))))
        price = dict(widget_for(b, "price").options)
        assert "4,099" in price.values(), price
        assert "10,372" in price.values(), price
        when = dict(widget_for(b, "when").options)
        assert "02jan2000" in when.values(), when
        whenm = dict(widget_for(b, "whenm").options)
        assert sorted(v for k, v in whenm.items() if v != "All") == [
            "2000m1", "2000m2", "2000m3"]
        f = dict(widget_for(b, "f").options)
        assert ".1" in f.values() and ".2" in f.values(), f
        # The values are section 17's, unchanged.
        assert 4099.0 in price, price
        assert dr._dash_option_value(F01) in f

    @pytest.mark.parametrize("mode", MODES)
    def test_a_value_label_still_wins(self, mode):
        b = build(mode, spec_of([_graph("g1", [_scatter("mpg", "price")])],
                                filters="foreign, type(dropdown)"))
        labels = [lab for _v, lab in widget_for(b, "foreign").options]
        assert labels == ["All", "Domestic", "Foreign"]

    def test_two_values_with_one_formatted_label_select_both(self):
        # %9.0g: a float-stored 0.1 and a double 0.1000000015 both read .1
        col = pd.Series([F01, 0.1000000015, 0.5])
        w, _ = dr._dash_filter_widget("dropdown", "y", col, "y",
                                      fmt="%9.0g", storage="")
        opts = [(v, lab) for v, lab in w.options if lab != "All"]
        assert [lab for _v, lab in opts] == [".1", ".5"], opts
        # %9.0f: 1.2 and 1.4 are one entry "1" selecting both
        df = pd.DataFrame({"x": [1.2, 1.4, 2.0]})
        w, _ = dr._dash_filter_widget("dropdown", "x", df["x"], "x",
                                      fmt="%9.0f")
        opts = [(v, lab) for v, lab in w.options if lab != "All"]
        assert opts == [(1.2, "1"), (2.0, "2")], opts
        assert w._dash_groups[1.2] == (1.2, 1.4)
        spec = {"varname": "x", "type": "dropdown", "sentinel": "__all__",
                "numeric": True,
                "groups": [list(m) for m in w._dash_groups.values()]}
        js_mask, _ = mask_parity(df, [spec], [1.2])
        assert js_mask == [True, True, False]
        w._dash_var = "x"
        w.value = 1.2
        assert dr._dash_frame_filter_mask(df, [w]).tolist() == [
            True, True, False]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_grouped_entry_reaches_the_page_in_both_modes(self, mode):
        df = _DF.assign(g=[1.2, 1.4, 2.0, 2.2, 1.2, 1.4, 2.0, 2.2, 3.0, 3.0])
        fm = dict(_FORMATS, g="%9.0f")
        b = build(mode, spec_of([_graph("g1", [_scatter("mpg", "price")])],
                                filters="g, type(dropdown)", formats=fm),
                  df=df)
        w = widget_for(b, "g")
        labels = [lab for _v, lab in w.options]
        assert labels == ["All", "1", "2", "3"], labels
        if mode == "standalone":
            specs = json.loads(
                b.obj.filter_callbacks[0].args["filter_specs_json"])
            assert [1.2, 1.4] in specs[0]["groups"]
        else:
            assert w._dash_groups[1.2] == (1.2, 1.4)


# ---------------------------------------------------------------------------
# Sliders
# ---------------------------------------------------------------------------

class TestSliders:

    @pytest.mark.parametrize("mode", MODES)
    def test_numeric_and_td_sliders_carry_a_stata_formatter(self, mode):
        b = build(mode, spec_of([_graph("g1", [_scatter("mpg", "price")])],
                                filters="price, type(range) || "
                                        "when, type(range) || mpg, type(slider)"))
        wp = widget_for(b, "price")
        assert isinstance(wp.format, CustomJSTickFormatter), wp.format
        assert wp.format.args["fmt"] == "%8.0gc"
        assert "%8.0gc" not in wp.format.code
        assert js_texts(wp.format, [4099], "tick") == ["4,099"]
        ww = widget_for(b, "when")
        assert isinstance(ww, DateRangeSlider)
        assert isinstance(ww.format, CustomJSTickFormatter), ww.format
        assert ww.format.args["fmt"] == "%td"
        assert js_texts(ww.format, [ww.start], "tick") == ["02jan2000"]
        wm = widget_for(b, "mpg")
        assert js_texts(wm.format, [14], "tick") == ["14"]

    @pytest.mark.parametrize("mode", MODES)
    def test_period_kinds_are_numeric_sliders_over_period_numbers(self, mode):
        want = {"whenm": (480, 482, "2000m1"), "whenq": (160, 163, "2000q1"),
                "whenh": (80, 81, "2000h1"), "whenw": (2080, 2084, "2000w1"),
                "wheny": (2000, 2004, "2000")}
        b = build(mode, spec_of(
            [_graph("g1", [_scatter("mpg", "price")])],
            filters=" || ".join(f"{v}, type(range)" for v in want)))
        for var, (lo, hi, text) in want.items():
            w = widget_for(b, var)
            assert type(w) is RangeSlider, (var, type(w).__name__)
            assert (w.start, w.end, w.step) == (lo, hi, 1), var
            assert w._dash_unit == "t" + _FORMATS[var][2], var
            assert js_texts(w.format, [lo], "tick") == [text], var
        if mode == "standalone":
            specs = json.loads(
                b.obj.filter_callbacks[0].args["filter_specs_json"])
            assert [s.get("unit") for s in specs] == [
                "tm", "tq", "th", "tw", "ty"]

    def test_a_period_column_with_one_value_or_none(self):
        empty = pd.Series(pd.to_datetime([None, None]))
        w, _ = dr._dash_filter_widget("range", "m", empty, "m",
                                      date_kind="tm", fmt="%tm")
        assert w.disabled
        one = pd.Series(pd.to_datetime(["2000-02-01", "2000-02-01"]))
        w, _ = dr._dash_filter_widget("range", "m", one, "m",
                                      date_kind="tm", fmt="%tm")
        assert (w.start, w.end) == (481, 482)
        w._dash_var = "m"
        df = pd.DataFrame({"m": one})
        w.value = (481, 481)
        assert dr._dash_frame_filter_mask(df, [w]).tolist() == [True, True]

    def test_the_masks_agree_on_a_period_slider_in_both_modes(self):
        df = pd.DataFrame({"m": pd.to_datetime(
            ["2000-01-01", "2000-02-01", "2000-02-01", None, "2000-03-01"])})
        spec = {"varname": "m", "type": "range", "sentinel": "__all__",
                "unit": "tm"}
        js_mask, _ = mask_parity(df, [spec], [{"value": (481, 481),
                                               "start": 480, "end": 482}])
        w = RangeSlider(start=480, end=482, value=(481, 481), step=1)
        w._dash_var, w._dash_ftype, w._dash_unit = "m", "range", "tm"
        py = dr._dash_frame_filter_mask(df, [w]).tolist()
        assert js_mask == py == [False, True, True, False, False]
        # At full extent nothing is dropped, a missing month included.
        js_full, _ = mask_parity(df, [spec], [{"value": (480, 482),
                                               "start": 480, "end": 482}])
        w.value = (480, 482)
        assert js_full == dr._dash_frame_filter_mask(df, [w]).tolist() == [
            True] * 5
        sspec = {"varname": "m", "type": "slider", "sentinel": "__all__",
                 "unit": "tm"}
        js_s, _ = mask_parity(df, [sspec], [{"value": 481, "start": 480,
                                             "end": 482}])
        s = Slider(start=480, end=482, value=481, step=1)
        s._dash_var, s._dash_ftype, s._dash_unit = "m", "slider", "tm"
        assert js_s == dr._dash_frame_filter_mask(df, [s]).tolist() == [
            False, True, True, False, True]

    def _move_spec(self):
        return spec_of([_graph("g1", [_scatter("mpg", "price")])],
                       filters="whenm, type(range)",
                       kpis=[{"name": "k1", "stat": "count", "var": "price",
                              "fmt": "", "title": "k1", "subtitle": "",
                              "color": "", "bgcolor": "",
                              "update": "filter"}])

    def test_a_period_move_reaches_a_card_and_a_graph(self):
        b = build("standalone", self._move_spec())
        r = b.obj
        w = r.filter_widgets[0]
        s = JsSession(r.filter_callbacks)
        s.set(w, (481, 481))
        s.run(r.filter_callbacks[0])
        src = r.figures["g1"].renderers[0].data_source
        feb = sorted(p for p, m in zip(_DF["price"], _DF["whenm"])
                     if m == 481)
        assert sorted(src.data["price"]) == feb
        assert re.search(r'>\s*%d\s*<' % len(feb), r.kpi_divs["k1"].text)
        # served
        b = build("served", self._move_spec())
        w = widget_for(b, "whenm")
        _fire(w, (481, 481))
        figs = [m for m in b.models if type(m).__name__ == "figure"]
        rows = sorted(figs[0].renderers[0].data_source.data["price"])
        assert rows == feb
        divs = [d.text for d in b.obj.select({"type": Div})
                if 'kpi_val_k1' in (d.text or "")]
        assert divs and re.search(r'>\s*%d\s*<' % len(feb), divs[0])


# ---------------------------------------------------------------------------
# Tooltips
# ---------------------------------------------------------------------------

def _hover_rows(b):
    rows, fmts = {}, {}
    for t in of_type(b, HoverTool):
        for lab, fld in t.tooltips:
            rows[lab] = fld
        fmts.update(t.formatters or {})
    return rows, fmts


class TestTooltips:

    @pytest.mark.parametrize("mode", MODES)
    def test_fields_carry_custom_and_a_formatter_with_the_format(self, mode):
        b = build(mode, spec_of([_graph(
            "g1", [_scatter("price", "when")],
            hover="whenc whenC f mpg")]))
        rows, fmts = _hover_rows(b)
        assert rows["price"] == "@{price}{custom}", rows
        assert rows["when"] == "@{when}{custom}", rows
        hp, hw = fmts["@{price}"], fmts["@{when}"]
        assert isinstance(hp, CustomJSHover) and hp.args["fmt"] == "%8.0gc"
        assert isinstance(hw, CustomJSHover) and hw.args["fmt"] == "%td"
        assert "%8.0gc" not in hp.code
        assert js_texts(hp, [4099], "value") == ["4,099"]
        assert js_texts(hw, [ms_of_td(14611)], "value") == ["02jan2000"]
        c_ms = ms_of_td(14611) + 3_600_000
        for var in ("whenc", "whenC"):
            assert js_texts(fmts["@{%s}" % var], [c_ms], "value") == [
                "02jan2000 01:00:00"], var
        assert js_texts(fmts["@{f}"], [F01], "value") == [".1"]
        g = dr._dash_fmt_hover("%10.0g", "", "", {})
        assert js_texts(g, [12345.67], "value") == ["12345.67"]

    @pytest.mark.parametrize("mode", MODES)
    def test_one_formatter_model_per_format_triple(self, mode):
        b = build(mode, spec_of([
            _graph(f"g{i}", [_scatter("price", "when")]) for i in (1, 2, 3)]))
        hovers = of_type(b, CustomJSHover)
        assert len(hovers) == 2, [h.args for h in hovers]
        cache = {}
        a = dr._dash_fmt_tick_formatter("%9.0g", "", "", cache)
        assert dr._dash_fmt_tick_formatter("%9.0g", "", "", cache) is a
        assert dr._dash_fmt_hover("%9.0g", "", "", cache) is not a

    @pytest.mark.parametrize("mode", MODES)
    def test_a_value_labelled_hover_variable_is_not_formatted(self, mode):
        b = build(mode, spec_of([_graph(
            "g1", [_scatter("price", "mpg")], hover="foreign")]))
        rows, fmts = _hover_rows(b)
        fld = [f for f in rows.values() if "foreign" in f]
        assert fld == ["@{__dash_hover_foreign}"], rows
        assert "@{__dash_hover_foreign}" not in fmts
        assert "@{foreign}" not in fmts


# ---------------------------------------------------------------------------
# Date axes
# ---------------------------------------------------------------------------

class TestDateAxis:

    @pytest.mark.parametrize("mode", MODES)
    def test_ticks_read_as_stata_in_both_modes(self, mode):
        probes = truth()
        lab, bare = probes["e3_tm_axis_lab"], probes["e3_tm_axis"]
        ticks = [492.0, 495.0, 498.0, 501.0]
        want = ["2001m1", "2001m4", "2001m7", "2001m10"]
        assert [dr._dash_fmt_text(v, "%tm") for v in ticks] == want
        for t in want:
            assert t in lab["texts"], (t, lab["texts"])
            # The bare probe (no xlabel()) draws the same months too.
            assert t in bare["texts"], (t, bare["texts"])
        fm = dict(_FORMATS, when2="%tdCCYY-NN-DD")
        df = _DF.assign(when2=_DF["when"])
        cases = {"when": ["02jan2000"], "whenm": ["2000m1"],
                 "wheny": ["2000"], "whenc": ["02jan2000 00:00:00"],
                 "when2": ["2000-01-02"]}
        firsts = {"when": ms_of_td(14611), "whenm": 946684800000.0,
                  "wheny": 946684800000.0,
                  "whenc": ms_of_td(14611), "when2": ms_of_td(14611)}
        b = build(mode, spec_of([_graph(f"g_{v}", [_scatter("price", v)])
                                 for v in cases], formats=fm), df=df)
        figs = {f.title.text if f.title else "": f for f in b.models
                if type(f).__name__ == "figure"}
        for v, texts in cases.items():
            [fig] = [f for f in b.models if type(f).__name__ == "figure"
                     and any(getattr(getattr(r, "glyph", None), "x", None)
                             == v for r in f.renderers)]
            fmt = fig.xaxis[0].formatter
            assert isinstance(fmt, CustomJSTickFormatter), (v, fmt)
            assert fmt.args["fmt"] == fm[v], (v, fmt.args)
            assert js_texts(fmt, [firsts[v]], "tick") == texts, v
        # %tm in node as in Python, at the probe's ticks (the %tm axis's
        # ticks are epoch ms of each month's first day).
        f = dr._dash_date_axis_formatter("%tm", "", {})
        ms = [float(pd.Timestamp(2001, 1 + 3 * i, 1).value // 10**6)
              for i in range(4)]
        assert js_texts(f, ms, "tick") == want
        del figs


# ---------------------------------------------------------------------------
# Numeric axis format()
# ---------------------------------------------------------------------------

class TestNumericAxis:

    @pytest.mark.parametrize("mode", MODES)
    def test_format_suboption_is_written_by_the_formatter(self, mode):
        cases = {"%9.0fc": "4,099", "%9.2e": "4.10e+03",
                 "%9.3g": dr._dash_fmt_text(4099, "%9.3g")}
        graphs = [_graph(f"g{i}", [_scatter("price", "mpg")],
                         ylabel=f", format({f})")
                  for i, f in enumerate(cases)]
        graphs.append(_graph("gs", [_scatter("price", "mpg")],
                             ylabel=", format(%12s)"))
        b = build(mode, spec_of(graphs))
        figs = {f.name if getattr(f, "name", None) else None: f
                for f in b.models if type(f).__name__ == "figure"}
        got = {}
        for f in [m for m in b.models if type(m).__name__ == "figure"]:
            fm = f.yaxis[0].formatter
            if isinstance(fm, CustomJSTickFormatter) and "fmt" in fm.args:
                got[fm.args["fmt"]] = js_texts(fm, [4099], "tick")[0]
        assert got == cases, got
        assert any("format(%12s)" in w for w in b.warnings), b.warnings
        del figs

    def test_an_absurd_width_is_bounded_and_named(self):
        spec = dr._dash_parse_axis_spec(", format(%9.999999999f)")
        from bokeh.plotting import figure
        fig = figure()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_apply_axis_spec(fig.yaxis, fig.ygrid, spec)
        assert any("format(" in str(w.message) for w in caught)
        assert not isinstance(fig.yaxis[0].formatter, CustomJSTickFormatter)


# ---------------------------------------------------------------------------
# Marker labels
# ---------------------------------------------------------------------------

def _labelset_texts(b):
    out = {}
    for ls in of_type(b, LabelSet):
        out[ls.text if isinstance(ls.text, str) else ls.text.field] = list(
            ls.source.data[ls.text if isinstance(ls.text, str)
                           else ls.text.field])
    return out


class TestMarkerLabels:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_a_float_and_a_g_variable_in_both_modes(self, mode):
        df = _DF.copy()
        df.loc[3, "f"] = np.nan
        b = build(mode, spec_of([
            _graph("g1", [_scatter("mpg", "price", mlabel="when")]),
            _graph("g2", [_scatter("mpg", "price", mlabel="f")]),
            _graph("g3", [_scatter("mpg", "weight2", mlabel="price")]),
        ]), df=df.assign(weight2=df["mpg"] * 100))
        t = _labelset_texts(b)
        whens = [v for k, v in t.items() if k.endswith("when")][0]
        assert "02jan2000" in whens, whens
        fs = [v for k, v in t.items() if k.endswith("_f")][0]
        assert ".1" in fs and "." in fs, fs
        assert not any(len(str(x)) > 12 for x in fs), fs
        prices = [v for k, v in t.items() if k.endswith("price")][0]
        assert "4,099" in prices, prices

    @pytest.mark.parametrize("mode", MODES)
    def test_mlabformat_g_is_honoured_and_silent(self, mode):
        b = build(mode, spec_of([
            _graph("g1", [_scatter("mpg", "price", mlabel="price",
                                   mlabformat="%9.3g")]),
            _graph("g2", [_scatter("mpg", "price", mlabel="price",
                                   mlabformat="%td")]),
            _graph("g3", [_scatter("mpg", "price", mlabel="mpg",
                                   mlabformat="%12s")]),
        ]))
        t = _labelset_texts(b)
        g = [v for k, v in t.items() if "_fmt_" in k and "4099" in v]
        assert g, t
        assert dr._dash_fmt_text(4099, "%9.3g") in g[0]
        assert not any("mlabformat(%9.3g)" in w for w in b.warnings)
        # A date format on a number stays named (twoway unmeasured).
        assert any("mlabformat(%td)" in w for w in b.warnings)
        assert any("mlabformat(%12s)" in w for w in b.warnings), b.warnings


# ---------------------------------------------------------------------------
# by() titles
# ---------------------------------------------------------------------------

class TestFacetTitles:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_panel_is_titled_as_stata_in_both_modes(self, mode):
        df = _DF.iloc[:3].assign(when2=_DF["when"].iloc[:3])
        fm = dict(_FORMATS, when2="%tdCCYY-NN-DD")
        b = build(mode, spec_of([
            _graph("g1", [_scatter("mpg", "price")], by="when"),
            _graph("g2", [_scatter("mpg", "price")], by="whenm"),
            _graph("g3", [_scatter("mpg", "price")], by="when2"),
        ], formats=fm), df=df)
        titles = {f.title.text for f in b.models
                  if type(f).__name__ == "figure" and f.title is not None}
        for t in ("02jan2000", "2000m1", "2000-01-02"):
            assert t in titles, titles
        assert dr._dash_stata_date_text(14610.0, "%td") == "01jan2000"
        assert dr._dash_stata_date_text(float("nan"), "%td") == "."
        assert dr._dash_stata_date_text(
            pd.Timestamp("2000-01-01"), "%tdCCYY-NN-DD") == "2000-01-01"


# ---------------------------------------------------------------------------
# The CSV
# ---------------------------------------------------------------------------

class TestCsv:

    @pytest.mark.parametrize("script", ["saved", "served"])
    def test_a_float_variable_writes_its_float32_digits(self, script):
        meta = dr._dash_csv_meta(["f", "d", "t"], {"t": "%td"}, {}, {}, {},
                                 storage_types={"f": "float", "d": "double"})
        assert meta["storage"] == {"f": "float", "d": "double"}
        head = (dr._DASH_FILTER_MASK_JS + dr._DASH_CSV_JS
                if script == "saved" else dr._DASH_FMT_JS + dr._DASH_CSV_JS)
        data = {"f": [F01, 12345.6787109375], "d": [1e-7, 123456789012.0],
                "t": [ms_of_td(14611), None]}
        src = (head + "\nprocess.stdout.write(JSON.stringify(dash_csv_text("
               + json.dumps(data) + ", null, [0, 1], "
               + json.dumps(meta) + ")));")
        text = run_js(src)
        assert text.split("\r\n")[1:3] == [
            "0.1,1e-7,2000-01-02", "12345.679,123456789012,"], text


# ---------------------------------------------------------------------------
# The colorvar key
# ---------------------------------------------------------------------------

class TestColorvarLabels:

    @pytest.mark.parametrize("mode", MODES)
    def test_number_labels_use_the_variables_format(self, mode):
        b = build(mode, spec_of([
            _graph("g1", [_scatter("mpg", "weight2", colorvar="price",
                                   colorcuts="4000 6000")]),
            _graph("g2", [_scatter("mpg", "weight2", colorvar="price",
                                   colordiscrete="yes")]),
        ]), df=_DF.assign(weight2=_DF["mpg"] * 100))
        items = []
        for leg in [m for m in b.models if type(m).__name__ == "Legend"]:
            for it in leg.items:
                lab = it.label
                items.append(getattr(lab, "value", lab))
        joined = " | ".join(str(i) for i in items)
        assert "≤4,000" in joined and ">6,000" in joined, joined
        assert "4,000–6,000" in joined, joined
        assert "10,372" in joined, joined


# ---------------------------------------------------------------------------
# Retired helpers
# ---------------------------------------------------------------------------

class TestRetired:

    def test_the_old_formatters_are_gone(self):
        for name in ("_datetime_formatter_for", "_stata_numeric_pattern",
                     "_parse_stata_numeric_fmt", "_format_stata_numeric"):
            assert not hasattr(dr, name), name
        assert not hasattr(dr.GlyphMapper, "_mlabel_date_texts")


# ---------------------------------------------------------------------------
# A move changes no text on the saved page
# ---------------------------------------------------------------------------

class TestParity:

    def test_the_saved_text_after_a_move_equals_before(self):
        b = build("standalone", spec_of(
            [_graph("g1", [_scatter("mpg", "price", mlabel="price")])],
            filters="mpg, type(slider) || price, type(dropdown)"))
        r = b.obj
        slider = [w for w in r.filter_widgets if isinstance(w, Slider)][0]
        drop = [w for w in r.filter_widgets if isinstance(w, Select)][0]
        before_opts = list(drop.options)
        before_fmt = js_texts(slider.format, [slider.start], "tick")
        before_labels = _labelset_texts(b)
        s = JsSession(r.filter_callbacks)
        s.set(slider, slider.start)
        s.run(r.filter_callbacks[0])
        assert list(drop.options) == before_opts
        assert js_texts(slider.format, [slider.start], "tick") == before_fmt
        after = {k: v for k, v in _labelset_texts(b).items()}
        for k, v in before_labels.items():
            assert sorted(map(str, after[k])) == sorted(map(str, v)), k


def test_node_ran():
    """The node cases above ran rather than skipped (a skip is red)."""
    from js_runner import NODE
    assert NODE is not None, "node is required for this file"


# ---------------------------------------------------------------------------
# Out-of-calendar dates, measured with `display %fmt value' in StataMP 19
# (30sep2026), verbatim with Stata's width padding.
# ---------------------------------------------------------------------------

_OUT_OF_CALENDAR = [
    ("%td", 2936549.0, "31dec9999"),
    ("%td", 2936550.0, "  2936550"),
    ("%td", -679351.0, "  -679351"),
    ("%td", -679350.0, "01jan0100"),
    ("%td", 1e10, " 1.00e+10"),
    ("%td", 1e308, "      .z_"),
    ("%td", -1e308, "        ."),
    ("%tc", 1e15, "       1.00000e+15"),
    ("%tc", 1e308, "               .z_"),
    ("%tm", 1e10, "1.0e+10"),
]


class TestOutOfCalendarDates:

    @pytest.mark.parametrize("fmt,value,want", _OUT_OF_CALENDAR)
    def test_python_writes_what_stata_displays(self, fmt, value, want):
        assert dr._dash_fmt(value, fmt) == want
        assert dr._dash_fmt_text(value, fmt) == want.strip()

    def test_javascript_writes_what_stata_displays(self):
        rows = [[f, v] for f, v, _w in _OUT_OF_CALENDAR]
        src = (dr._DASH_FMT_JS + "\nconst rows = " + json.dumps(rows)
               + ";\nprocess.stdout.write(JSON.stringify(rows.map((r) => "
               "[dash_fmt(r[1], r[0], '', false), dash_fmt_text(r[1], r[0], '')])));")
        got = run_js(src)
        assert got == [[w, w.strip()] for _f, _v, w in _OUT_OF_CALENDAR]
