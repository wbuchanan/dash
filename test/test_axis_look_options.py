"""WP-31 D6: the axis label, tick and grid sub-options are drawn as twoway
draws them (section 33).

dash named labgap(), labjustification(), labalignment(), alternate,
altgap(), tlwidth(), tlcolor(), tlpattern(), glwidth(), glcolor(),
glpattern(), gmin, gmax, nogmin, nogmax, gextend, nogextend and custom in a
"not implemented" note; ylabel(minmax) read the first layer only; and the
label forms twoway refuses were drawn.  twoway's answers are measured in
test/fixtures/axis_look_truth.json (scripts/extract_axis_look_truth.do; SVG
units are 10 per point):

* labgap(): the gap between the tick and its label, default half_tiny (2 pt):
  labgap(small) moves the plot region 59.9 units from the plain graph's,
  labgap(large) 119.9 (labgap_*).
* alternate: the labels alternate between two rows, the first label on the
  row nearest the axis, the second row one label height (the font size)
  further out; altgap() adds to that (alt_default, alt_altgap_large).
* tlpattern() draws nothing different (tl_pattern_dash equals plain), and
  glcolor() does not turn a grid on (gl_color_nogrid equals plain): both
  are accepted in silence.  custom (custom_with equals custom_without),
  gmin, gmax and gextend (gx_gextend equals gx_default) are no-ops.
* nogextend stops the grid at the scale's ends, not the plot region's
  margin (gx_nogextend); a Bokeh grid line spans the frame, so dash still
  names it (residual D6b).
* nogmin drops the grid line at the lowest major tick, nogmax the one at
  the highest; on a typed list of values nogmax drops every grid line
  (ge_list_nogmax, ge_nogmin_nogmax), on a rule only the end
  (ge_range_nogmin, ge_count_nogmin).
* ylabel(minmax) labels the least and greatest value over every layer
  (minmax_two: 5 and 41 over mpg and trunk).
* ##5 on ylabel()/ytick() is "##5 ignored, only allowed for minor ticks"
  (dh_*; WP-31 D1 prints it); a lone ##5 on ylabel() then draws what
  ylabel(none) draws (no labels, ticks or grid), on ytick() nothing.
* ylabel("a"), ylabel(1 "a" "b"), ylabel(#3 #4) and ylabel(1(1)) are
  refused r(198) "invalid label specifier, : <text>:" (ref_*).

While iterating: ``python3 -m pytest test/test_axis_look_options.py -q``.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_default_axes as tda  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "axis_look_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)
_SC = [P("scatter", "mpg", "weight")]
_FORMATS = {"weight": "%8.0gc", "mpg": "%8.0g", "turn": "%8.0g"}
_UNITS_PER_PT = 10.0
T = dr.OptionTranslator


def _figs(mode, go, plots=None):
    """The first figure and every warning the build printed (the saved
    renderer is built here, not through test_default_axes, which silences
    them)."""
    from conftest import render_models
    spec = tda._spec(plots or _SC, go, formats=_FORMATS)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            _tag, sp, dp = tda._write(spec, "auto")
            r = render_models(dr.DashRenderer(sp, dp))
            figs = tb._panels(list(r.figures.values()))
        else:
            figs = tda._figs(mode, spec)
    return figs[0], [str(x.message) for x in w]


def _axis(f, letter):
    return tda._axis(f, letter)


def _grid(f, letter):
    return [g for g in (f.xgrid if letter == "x" else f.ygrid)
            if getattr(g, letter + "_range_name", "default") == "default"][0]


def _twins(f, side):
    return [a for a in getattr(f, side)
            if "dash_alt_axis" in (getattr(a, "tags", None) or [])]


def _plot_left(key):
    return _T[key]["plotregion"]["left"]


# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta(self):
        m = _T["_meta"]
        assert sorted(k for k in m if k != "scheme") == [
            "born_date", "dash_commit", "extracted", "source",
            "stata_version"]
        assert m["source"] == "scripts/extract_axis_look_truth.do"

    def test_keys(self):
        for k in ("plain", "labgap_small", "labgap_large", "alt_default",
                  "alt_altgap_large", "tl_width_thick", "tl_color_red",
                  "tl_pattern_dash", "gl_width_thick", "gl_color_red",
                  "gl_pattern_dash", "gl_color_nogrid", "ge_list_nogmax",
                  "ge_list_nogmin", "ge_count_nogmin", "gx_nogextend",
                  "custom_with", "custom_without", "dh_ylabel", "dh_ytick",
                  "dh_xlabel", "dh_ylabel_list",
                  "minmax_two", "ref_1", "ref_2", "ref_5", "ref_6"):
            assert k in _T, k


class TestLabelLook:
    @pytest.mark.parametrize("mode", _MODES)
    def test_labgap(self, mode):
        # twoway: the default gap is half_tiny (2 pt); labgap(v) moves the
        # labels by v less 2 pt.  Bokeh's standoff is 5 px at the default.
        for key, word in (("labgap_small", "small"),
                          ("labgap_large", "large"), ("labgap_3", "3")):
            moved_pt = (_plot_left(key) - _plot_left("plain")) / _UNITS_PER_PT
            f, msgs = _figs(mode, {"ylabel": ", labgap(%s)" % word})
            got = _axis(f, "y").major_label_standoff
            assert got == round(5 + moved_pt * T.PX_PER_PT), (word, got)
            assert not [m for m in msgs if "labgap" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("word,align", [("left", "left"),
                                            ("center", "center"),
                                            ("right", "right")])
    def test_justification(self, mode, word, align):
        f, msgs = _figs(mode, {"ylabel": ", labjustification(%s)" % word})
        assert _axis(f, "y").major_label_text_align == align
        assert not [m for m in msgs if "labjust" in m]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("word,base", [("top", "top"),
                                           ("middle", "middle"),
                                           ("bottom", "bottom"),
                                           ("baseline", "alphabetic")])
    def test_alignment(self, mode, word, base):
        f, msgs = _figs(mode, {"ylabel": ", labalignment(%s)" % word})
        assert _axis(f, "y").major_label_text_baseline == base
        assert not [m for m in msgs if "labalign" in m]


class TestTickLook:
    @pytest.mark.parametrize("mode", _MODES)
    def test_major(self, mode):
        f, msgs = _figs(mode, {"ylabel":
                               ", tlwidth(thick) tlcolor(red) tlpattern(dash)"})
        ax = _axis(f, "y")
        thick_pt = _T["tl_width_thick"]["hlines"][-2]["width"] / _UNITS_PER_PT
        assert ax.major_tick_line_width == pytest.approx(
            thick_pt * T.PX_PER_PT, abs=0.01)
        assert ax.major_tick_line_color == "#ff0000"
        # twoway draws tlpattern() as solid ticks (tl_pattern_dash).
        assert list(ax.major_tick_line_dash) == []
        assert not [m for m in msgs if "not implemented" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_minor_via_xtick(self, mode):
        f, _msgs = _figs(mode, {"ytick": "15 25 35, tlwidth(thick) tlcolor(red)"})
        ax = _axis(f, "y")
        assert ax.minor_tick_line_width == pytest.approx(2.304 * T.PX_PER_PT,
                                                         abs=0.01)
        assert ax.minor_tick_line_color == "#ff0000"

    def test_the_fixture_draws_the_tick_look(self):
        red = [h for h in _T["tl_color_red"]["hlines"]
               if h["stroke"] == "#ff0000"]
        assert len(red) == 4
        assert _T["tl_pattern_dash"]["hlines"] == _T["plain"]["hlines"]


class TestGridLook:
    @pytest.mark.parametrize("mode", _MODES)
    def test_each(self, mode):
        f, msgs = _figs(mode, {"ylabel":
                               ", grid glwidth(thick) glcolor(red) glpattern(dash)"})
        g = _grid(f, "y")
        assert g.grid_line_width == pytest.approx(2.304 * T.PX_PER_PT,
                                                  abs=0.01)
        assert g.grid_line_color == "#ff0000"
        assert list(g.grid_line_dash) == list(T.translate_lpattern("dash"))
        assert not [m for m in msgs if "not implemented" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_glcolor_leaves_the_grid_off(self, mode):
        assert _T["gl_color_nogrid"]["hlines"] == _T["plain"]["hlines"]
        f, msgs = _figs(mode, {"xlabel": ", glcolor(red)"})
        assert _grid(f, "x").grid_line_color is None
        assert not [m for m in msgs if "not implemented" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_end_lines(self, mode):
        from bokeh.models import CustomJSTicker
        f, _m = _figs(mode, {"ylabel": ", grid nogmin"})
        t = _grid(f, "y").ticker
        assert isinstance(t, CustomJSTicker)
        assert t.major_code == dr._DASH_GRID_NOEND_JS
        assert (t.args["drop_start"], t.args["drop_end"],
                t.args["drop_all"]) == (True, False, False)
        f, _m = _figs(mode, {"ylabel": "10 20 30 40, grid nogmax"})
        t = _grid(f, "y").ticker
        assert t.args["drop_all"] is True
        f, _m = _figs(mode, {"ylabel": ", grid gmin gmax"})
        assert not isinstance(_grid(f, "y").ticker, CustomJSTicker)

    def test_the_fixture_end_rules(self):
        def n(k):
            return len([h for h in _T[k]["hlines"]
                        if h["stroke"] == "#eaf2f3"])
        assert (n("ge_default"), n("ge_list_nogmin"), n("ge_list_nogmax"),
                n("ge_auto_nogmin"), n("ge_auto_nogmax"),
                n("ge_count_nogmin")) == (4, 3, 0, 3, 3, 2)

    def test_noend_js_drops_ends(self):
        src = """
const base = {get_ticks: (s, e) => ({major: [10, 20, 30, 40]})};
const out = [];
for (const a of [[true, false, false], [false, true, false],
                 [true, true, false], [false, true, true]]) {
  const f = new Function("cb_data", "base", "drop_start", "drop_end",
                         "drop_all", %s);
  out.push(f({start: 5, end: 45, range: null, cross_loc: 0}, base,
             a[0], a[1], a[2]));
}
console.log(JSON.stringify(out));
""" % json.dumps(dr._DASH_GRID_NOEND_JS)
        assert js_runner.run_js(src) == [[20, 30, 40], [10, 20, 30],
                                         [20, 30], []]

    @pytest.mark.parametrize("mode", _MODES)
    def test_nogextend_stays_named(self, mode):
        # twoway stops the lines at the scale (gx_nogextend); a Bokeh grid
        # line spans the frame, so dash names it (residual D6b).
        assert _T["gx_gextend"]["hlines"] == _T["gx_default"]["hlines"]
        assert _T["gx_nogextend"]["hlines"][0]["x1"] > \
            _T["gx_default"]["hlines"][0]["x1"]
        _f, msgs = _figs(mode, {"ylabel": ", grid nogextend"})
        assert [m for m in msgs if "nogextend" in m], msgs
        _f, msgs = _figs(mode, {"ylabel": ", grid gextend"})
        assert not [m for m in msgs if "not implemented" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_custom_is_silent(self, mode):
        a = dict(_T["custom_with"], command="")
        b = dict(_T["custom_without"], command="")
        assert a == b
        _f, msgs = _figs(mode, {"ylabel": "10 20 30, custom"})
        assert not [m for m in msgs if "custom" in m], msgs


class TestAlternate:
    @pytest.mark.parametrize("mode", _MODES)
    def test_twin(self, mode):
        from bokeh.models import CustomJSTickFormatter
        f, msgs = _figs(mode, {"xlabel": "1500(500)5000, alternate"})
        tw = _twins(f, "below")
        assert len(tw) == 1
        ax = _axis(f, "x")
        assert ax is not tw[0]
        assert isinstance(ax.formatter, CustomJSTickFormatter)
        assert ax.formatter.args["parity"] == 0
        assert tw[0].formatter.args["parity"] == 1
        assert tw[0].formatter.code == ax.formatter.code == \
            dr._DASH_ALT_LABEL_JS
        assert tw[0].axis_line_color is None
        assert tw[0].major_tick_out == 0 and tw[0].minor_tick_out == 0
        assert tw[0].ticker is ax.ticker
        assert not [m for m in msgs if "alternate" in m], msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_altgap(self, mode):
        # twoway: the second row sits one label height plus altgap()
        # further out (alt_default: 100 units = the 10 pt font; large: 240).
        d0 = 2619.14 - _T["alt_default"]["texts"][5]["y"]
        d1 = 2619.14 - _T["alt_altgap_large"]["texts"][5]["y"]
        assert d0 == pytest.approx(100.0, abs=0.1)
        extra_pt = (d1 - d0) / _UNITS_PER_PT
        f0, _m = _figs(mode, {"xlabel": "1500(500)5000, alternate"})
        f1, msgs = _figs(mode, {"xlabel":
                                "1500(500)5000, alternate altgap(large)"})
        s0 = _twins(f0, "below")[0].major_label_standoff
        s1 = _twins(f1, "below")[0].major_label_standoff
        assert s1 - s0 == pytest.approx(extra_pt * T.PX_PER_PT, abs=1)
        assert not [m for m in msgs if "altgap" in m], msgs

    def test_the_formatter_calls_the_base(self):
        src = """
const base = {doFormat: (ticks, opts) => ticks.map((t) => "L" + t)};
const f = new Function("tick", "index", "ticks", "parity", "base", %s);
const ticks = [1, 2, 3, 4];
const out = [0, 1].map((p) => ticks.map((t, i) => f(t, i, ticks, p, base)));
console.log(JSON.stringify(out));
""" % json.dumps(dr._DASH_ALT_LABEL_JS)
        assert js_runner.run_js(src) == [["L1", "", "L3", ""],
                                         ["", "L2", "", "L4"]]

    def test_the_bokehjs_signature(self):
        # BokehJS calls a CustomJSTickFormatter's code with tick, index and
        # ticks (the installed bokeh.min.js).
        import bokeh
        js = os.path.join(os.path.dirname(bokeh.__file__), "server",
                          "static", "js", "bokeh.min.js")
        with open(js, encoding="utf-8") as fh:
            src = fh.read()
        assert '"tick","index","ticks"' in src.replace(" ", "")

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_twin_is_not_finished(self, mode):
        f, _m = _figs(mode, {"xlabel": "1500(500)5000, alternate"})
        tw = _twins(f, "below")[0]
        assert tw not in list(dr._dash_primary_axes(f.xaxis, "x_range_name"))
        hulls = [e["ax"] for e in getattr(f, "_dash_hull_axes", ())]
        assert all(a is not tw for a in hulls)


class TestDoubleHash:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt,key", [("ylabel", "dh_ylabel"),
                                         ("ytick", "dh_ytick")])
    def test_label(self, mode, opt, key):
        assert _T[key]["log"] == ["##5 ignored, only allowed for minor ticks"]
        f, msgs = _figs(mode, {opt: "##5"})
        assert "dash: ##5 ignored, only allowed for minor ticks" in msgs
        # twoway draws ylabel(##5) as ylabel(none) -- no labels, ticks or
        # grid -- and ytick(##5) as the plain graph.
        tw_labels = [x["text"] for x in _T[key]["texts"]
                     if x["text"].isdigit()]
        got = tda._ticks(f, "y")
        if opt == "ylabel":
            assert tw_labels == [] and list(got) == []
        else:
            assert tw_labels == ["10", "20", "30", "40"]
            assert [float(v) for v in got] == [10.0, 20.0, 30.0, 40.0]


class TestMinmax:
    @pytest.mark.parametrize("mode", _MODES)
    def test_every_layer(self, mode):
        texts = [t["text"] for t in _T["minmax_two"]["texts"]][:2]
        assert texts == ["5", "41"]
        f, _m = _figs(mode, {"ylabel": "minmax"},
                      plots=[P("scatter", "mpg", "weight"),
                             P("scatter", "turn", "weight")])
        assert list(_axis(f, "y").ticker.ticks) == [12.0, 51.0]

    def test_helper_columns(self):
        import pandas as pd
        fr = pd.DataFrame({"a": [1.0, 5.0], "b": [-2.0, 3.0],
                           "lo": [0.0, 1.0], "hi": [9.0, 2.0],
                           "x": [7.0, 8.0], "d": [0.0, 365.0]})
        plots = [{"type": "scatter", "yvar": "a", "xvar": "x"},
                 {"type": "rarea", "yvar1": "lo", "yvar2": "hi",
                  "xvar": "x"},
                 {"type": "line", "yvars": ["b"], "xvar": "d"}]
        y = dr._dash_axis_layer_values(fr, plots, "y")
        assert (float(y.min()), float(y.max())) == (-2.0, 9.0)
        x = dr._dash_axis_layer_values(fr, plots, "x")
        assert (float(x.min()), float(x.max())) == (0.0, 365.0)
        assert dr._dash_axis_layer_values(fr, [], "y") is None


class TestSilentWhenHonoured:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("sub", ["labgap(small)", "labjustification(left)",
                                     "labalignment(top)", "alternate",
                                     "altgap(2)", "tlwidth(thick)",
                                     "tlcolor(red)", "tlpattern(dash)",
                                     "glwidth(thick)", "glcolor(red)",
                                     "glpattern(dash)", "gmin", "nogmin",
                                     "gmax", "nogmax", "gextend",
                                     "custom"])
    def test_no_warning(self, mode, sub):
        _f, msgs = _figs(mode, {"ylabel": ", grid " + sub})
        assert not [m for m in msgs if "not implemented" in m], msgs


class TestTheHonouredSet:
    def test_members(self):
        drawn = {"labgap", "labjustification", "labalignment", "alternate",
                 "altgap", "tlwidth", "tlcolor", "tlpattern", "glwidth",
                 "glcolor", "glpattern", "gmin", "nogmin", "gmax", "nogmax",
                 "gextend", "custom"}
        assert drawn <= dr._DASH_AXLABEL_HONOURED
        for style in ("labstyle", "tstyle", "gstyle", "tlstyle", "glstyle",
                      "nogextend"):
            assert style not in dr._DASH_AXLABEL_HONOURED


class TestTheBoundsFinisher:
    """_dash_axis_bounds: the finisher that ends a noextend-tagged axis at
    its first and last tick (WP-31 D7 tags it; untagged axes keep auto)."""

    def _fig(self, ticker):
        from bokeh.models import LinearAxis, Range1d
        from bokeh.plotting import figure
        f = figure(x_range=Range1d(0, 10), y_range=Range1d(0, 10))
        ax = f.yaxis[0]
        ax.ticker = ticker
        f._dash_margin = {}
        return f, [{"ax": ax, "letter": "y", "name": "default",
                    "kind": None}]

    def test_a_tagged_axis_ends_at_its_ticks(self):
        from bokeh.models import FixedTicker
        f, es = self._fig(FixedTicker(ticks=[2.0, 4.0, 6.0, 12.0]))
        dr._dash_axis_bounds(f, es)
        assert f.yaxis[0].bounds == "auto"
        f.yaxis[0]._dash_noextend = True
        dr._dash_axis_bounds(f, es)
        lo, hi = dr._dash_range_hull(f.y_range)
        assert f.yaxis[0].bounds == (2.0, 6.0) and hi < 12.0

    def test_the_major_ticks_under_a_wrapper(self):
        from bokeh.models import CustomJSTicker, FixedTicker
        base = FixedTicker(ticks=[1.0, 3.0])
        f, _es = self._fig(CustomJSTicker(args={"base": base},
                                          major_code="return [];"))
        assert dr._dash_axis_major_ticks(f.yaxis[0]) == [1.0, 3.0]
        from bokeh.models import BasicTicker
        f, _es = self._fig(BasicTicker())
        assert dr._dash_axis_major_ticks(f.yaxis[0]) is None
