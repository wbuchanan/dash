"""WP-42 section 42-01 (CV-8): an unbinned numeric colorvar() is drawn in
twoway's levels on every coloured type, before and after a filter move.

What twoway draws is measured by scripts/extract_colorvar_steps_truth.do
into test/fixtures/colorvar_steps_truth.json (StataNow 19.5):

* ``T_<type>``: the 17 coloured types that are not a line, colorvar(z)
  with z = price over extract_colorvar_types_truth.do's data: four level
  colours (#0000ff #00ffaa #aaff00 #ff0000), the key ticked 0 5,000
  10,000 15,000 -- the cuts are the key's ticks at or above the minimum,
  n cuts making n + 1 levels in n + 1 steps of the rule.
* ``M_<scheme>``: the mono schemes start at #bfbfbf, not near white.
* ``L_<form>``: zscale(log), zlabel(#3) and a %td colorvar.

Every test that draws runs in both modes: the saved page (DashRenderer)
and the served app (ServerAppBuilder); both run the same GlyphMapper.
"""
from __future__ import annotations

import datetime
import itertools
import json
import math
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColorBar

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import colour_bins as cb  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import _figures_of, make_spec  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "colorvar_steps_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
MODES = ["saved", "served"]
TYPES = sorted(k[2:] for k in TRUTH if k.startswith("T_"))

_TYPES_DF = pd.DataFrame(TRUTH["_data"]["types"])
_AUTO_DF = pd.DataFrame(TRUTH["_data"]["auto"])

_RANGE = {"rbar", "rspike", "rcap", "rcapsym", "rscatter"}
_PC = {"pcspike", "pcarrow", "pcbarrow", "pcscatter", "pccapsym"}
_RANGEPT = {"rpcap", "rpspike"}

_SEQ = itertools.count()
_CACHE: dict = {}


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return tmp_path_factory.mktemp("cvsteps")


def _type_plot(ptype, opts):
    """The plot record dash.ado writes for the fixture's T_<type> command
    (extract_colorvar_steps_truth.do's type table)."""
    o = dict(opts)
    if ptype in _RANGE:
        return {"type": ptype, "yvar1": "y", "yvar2": "y2", "xvar": "t",
                "options": o}
    if ptype in _RANGEPT:
        return {"type": ptype, "yvar1": "y", "yvar2": "y3", "yvar": "y2",
                "xvar": "t", "options": o}
    if ptype in _PC:
        return {"type": ptype, "y1var": "y", "x1var": "t", "y2var": "y2",
                "x2var": "t", "options": o}
    return {"type": ptype, "yvar": "y", "xvar": "t", "options": o}


def _figs(tmp, mode, plots, df, go=None, bo=None):
    """The figures of a one-graph spec of *plots* over *df*, in *mode*."""
    key = (mode, json.dumps([plots, go, bo], sort_keys=True), id(df))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots, graph_options=go, build_options=bo)
    tag = next(_SEQ)
    sp = tmp / f"cvs_spec_{tag}.json"
    dp = tmp / f"cvs_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(
        df, value_labels=None, value_label_names=None,
        variable_labels=None)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvs_app_{tag}.py"
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_cvs_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = figs
    return figs


def _hex(c):
    c = str(c).strip().lower()
    if c.startswith("#") and len(c) == 9:
        c = c[:7]
    return c


def _ms(value):
    """A number, or a date the page holds as a datetime as epoch ms."""
    if type(value).__name__ == "datetime64":
        return float(value.astype("datetime64[ms]").astype("int64"))
    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None) - value.utcoffset()
        return (value - datetime.datetime(1970, 1, 1)).total_seconds() * 1e3
    return float(value)


def _colour_of(mapper, value):
    """The colour Bokeh draws *value* in through *mapper* (BokehJS's
    linear and log scan: equal bins over low .. high, closed below)."""
    if value is None or (isinstance(value, float) and value != value):
        return _hex(mapper.nan_color)
    pal = [_hex(c) for c in mapper.palette]
    name = type(mapper).__name__
    if name == "CategoricalColorMapper":
        fac = list(mapper.factors)
        return pal[fac.index(value)] if value in fac else _hex(
            mapper.nan_color)
    v, lo, hi = _ms(value), _ms(mapper.low), _ms(mapper.high)
    if name == "LogColorMapper":
        v, lo, hi = math.log(v), math.log(lo), math.log(hi)
    if v < lo:
        return pal[0]
    if v > hi:
        return pal[-1]
    k = int((v - lo) / (hi - lo) * len(pal))
    return pal[min(k, len(pal) - 1)]


def _drawn(figs):
    """Every colour-mapped renderer's drawn colours, row by row."""
    out = []
    for f in figs:
        for r in cb.colour_renderers(f):
            m = cb.colour_mapper(r)
            out.append([_colour_of(m, v) for v in cb.drawn_colour_values(r)])
    return out


def _canonical(labels):
    seen, out = {}, []
    for lab in labels:
        seen.setdefault(lab, len(seen))
        out.append(seen[lab])
    return out


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _close(got, want):
    """Sorted colour lists equal to within 1/255 a channel."""
    got, want = sorted(got), sorted(want)
    return len(got) == len(want) and all(
        abs(a - b) <= 1 for g, w in zip(got, want)
        for a, b in zip(_rgb(g), _rgb(w)))


def _bars(figs):
    # Flipped (WP-42 CV-3): dash's colour key was a ColorBar; twoway draws
    # swatches beside a z axis (CV-3): the figure's key cell
    # (colour_bins.KeyView: its axis's ticks and labels, its levels).
    return [v for f in figs for v in cb.key_views(f)]


class TestTheFixture:

    def test_meta_and_levels(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert meta[k], k
        assert TRUTH["T_scatter"]["colours"] == [
            "#0000ff", "#00ffaa", "#aaff00", "#ff0000"]
        assert len(TYPES) == 17


class TestEveryTypeIsStepped:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", TYPES)
    def test_colours(self, tmp, ptype, mode):
        want = TRUTH["T_" + ptype]
        assert want["rc"] == 0
        figs = _figs(tmp, mode, [_type_plot(ptype, {"colorvar": "price"})],
                     _TYPES_DF)
        got = {c for rows in _drawn(figs) for c in rows}
        assert got and _close(got, want["colours"]), (ptype, sorted(got))

    @pytest.mark.parametrize("mode", MODES)
    def test_scatter_partition(self, tmp, mode):
        want = TRUTH["T_scatter"]
        figs = _figs(tmp, mode, [_type_plot("scatter",
                                            {"colorvar": "price"})],
                     _TYPES_DF)
        [rows] = _drawn(figs)
        assert len(rows) == want["n_markers"]
        assert _canonical(rows) == want["fill_groups"]


class TestSchemes:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("scheme", ["s1mono", "stcolor", "s2mono"])
    def test_colours(self, tmp, scheme, mode):
        want = TRUTH["M_" + scheme]
        figs = _figs(tmp, mode, [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"colorvar": "price"}}],
                     _AUTO_DF, bo={"scheme": scheme})
        [rows] = _drawn(figs)
        assert _close(set(rows), want["colours"]), (scheme, sorted(set(rows)))
        assert _canonical(rows) == want["fill_groups"]


_FORMS = {"zlog": ({"zscale": "log"}, {}, "price"),
          "zlab": ({"zlabel": "#3"}, {}, "price"),
          "date": ({}, {"formats": {"d": "%td"}}, "d")}


class TestForms:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe", sorted(_FORMS))
    def test_form(self, tmp, probe, mode):
        go, bo, var = _FORMS[probe]
        want = TRUTH["L_" + probe]
        figs = _figs(tmp, mode, [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"colorvar": var}}],
                     _AUTO_DF, go=go or None, bo=bo or None)
        [rows] = _drawn(figs)
        assert _close(set(rows), want["colours"]), (probe, sorted(set(rows)))
        assert _canonical(rows) == want["fill_groups"]


class TestTheKey:

    @pytest.mark.parametrize("mode", MODES)
    def test_the_bar_is_stepped_and_holds_zero(self, tmp, mode):
        figs = _figs(tmp, mode, [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"colorvar": "price"}}],
                     _AUTO_DF)
        [bar] = _bars(figs)
        [rend] = [r for f in figs for r in cb.colour_renderers(f)]
        glyph_m = cb.colour_mapper(rend)
        ticks = sorted(float(t) for t in bar.ticker.ticks)
        labels = [str(bar.major_label_overrides.get(t, bar
                      .major_label_overrides.get(str(t), "")))
                  for t in bar.ticker.ticks]
        # twoway's key: 0 5,000 10,000 15,000, one swatch a level.
        want = [t for t in TRUTH["M_s2color"]["key_texts"] if t != "Price"]
        assert labels == want, labels
        cuts = [t for t in ticks if t >= min(_AUTO_DF["price"])]
        # Flipped (WP-42 CV-3): one swatch a level, lowest first, between
        # the ticks; the axis from its 0 tick to the maximum.
        assert glyph_m is not None
        assert len(bar.colours) == len(cuts) + 1 == 4
        lo, hi = bar.cell._dash_key_axis.bounds
        assert lo <= ticks[0] and hi >= ticks[-1]
        assert [_hex(c) for c in bar.colours] == TRUTH["M_s2color"][
            "key_fills"]


# ---------------------------------------------------------------------------
# After a filter move: the kept rows cut again, saved (JS) and served
# (Python) alike, and as a build over the kept rows draws them.
# ---------------------------------------------------------------------------

import test_mode_parity as tp  # noqa: E402
import js_runner  # noqa: E402


def _cvar_state(models):
    """(glyph mapper, bar mapper) of the one colour layer among *models*:
    each (palette, low, high)."""
    out = []
    for m in models:
        if isinstance(m, ColorBar) and m.name != "dash_by_label_box":
            bm = m.color_mapper
            out.append(("bar", [_hex(c) for c in bm.palette],
                        round(float(bm.low), 6), round(float(bm.high), 6)))
        sp = cb._colour_spec(m) if hasattr(m, "glyph") else None
        if sp is not None and not dr._dash_is_swatch(m):
            gm = cb._get(sp, "transform")
            out.append(("glyph", [_hex(c) for c in gm.palette],
                        round(float(gm.low), 6), round(float(gm.high), 6)))
    return sorted(out)


class TestTheStepmapRelevel:

    @pytest.mark.parametrize("ptype", ["scatter", "bar"])
    def test_python_and_js_agree(self, ptype):
        spec = tp._spec([tp.plot_for(ptype, {"colorvar": "price"})],
                        {"filter": "foreign, type(dropdown)"})
        oracle = json.loads(json.dumps(spec))
        oracle["build_options"]["filter"] = ""
        for g in oracle["graphs"]:
            g["if_expr"] = "foreign == 1"
        r0, _ = tp._standalone(oracle)
        want = _cvar_state(r0._last_layout_root.references())
        before, _ = tp._standalone(spec)
        assert want != _cvar_state(before._last_layout_root.references())
        # Served (Python twin).
        doc, _ = tp._served(spec)
        w = [x for x in tp._widgets_of(doc)
             if type(x).__name__ == "Select"][0]
        tp._fire(w, tp._move_widget_value(w, "Select", "Foreign"))
        assert _cvar_state([m for root in doc.roots
                            for m in root.references()]) == want
        # Saved (JS twin, under node).
        r, _ = tp._standalone(spec)
        w, cbk = [(w, c) for w, c in zip(r.filter_widgets,
                                         r.filter_callbacks)
                  if type(w).__name__ == "Select"][0]
        session = js_runner.JsSession(r.filter_callbacks)
        session.set(w, tp._move_widget_value(w, "Select", "Foreign"))
        session.run(cbk)
        assert _cvar_state(r._last_layout_root.references()) == want

    def test_the_plan_is_a_stepmap(self):
        spec = tp._spec([tp.plot_for("scatter", {"colorvar": "price"})],
                        {"filter": "foreign, type(dropdown)"})
        r, _ = tp._standalone(spec)
        [plan] = dr._dash_cvar_plans([r._last_layout_root])
        assert plan["kind"] == "stepmap"
        # Flipped (WP-42 CV-3): dash's colour key was a ColorBar with a
        # mapper of its own; twoway draws swatches beside a z axis (CV-3):
        # the plan ticks the key cell's axis and redraws its swatches.
        assert plan["bar"] is None and plan["keycell"] is not None
        assert plan["cbar"] is plan["keycell"]["axis"]
        # The Python twin over the foreign cars' prices: one swatch a
        # level, the axis's low end at or below the first tick.
        dr._dash_cvar_relevel_stepmap(plan, [4749.0, 4816.0, 4453.0,
                                             10372.0, 11385.0])
        src = plan["keycell"]["src"]
        # A level no price reaches draws no swatch, as twoway's (measured
        # 03nov2026): the levels from the lowest to the one holding the
        # highest, 11,385.
        cuts = [t for t in plan["cbar"].ticker.ticks if t >= 4453.0]
        assert len(src.data["c"]) == 1 + sum(1 for t in cuts if t < 11385.0)
        assert plan["cbar"].bounds[0] <= min(plan["cbar"].ticker.ticks)


class TestTheBarHelpers:

    def test_the_bar_palette(self):
        """The levels over one step beyond the end cuts; a zscale(range())
        end beyond that stretches the end level to it (measured 02nov2026:
        zscale(range(0 20000)) keeps price's four levels)."""
        cols = ["#a", "#b", "#c", "#d"]
        assert dr._dash_cvar_bar_palette(cols, [5.0, 10.0, 15.0], 5.0) == (
            cols, 0.0, 20.0)
        pal, lo, hi = dr._dash_cvar_bar_palette(
            cols, [5.0, 10.0, 15.0], 5.0, [None, 30.0], 30)
        assert (lo, hi) == (0.0, 30.0) and len(pal) == 30
        # Bins of 1: 0..5 the first level, 15..30 the last.
        assert pal[:5] == ["#a"] * 5 and pal[15:] == ["#d"] * 15

    def test_the_step_bar(self):
        from bokeh.models import LinearColorMapper
        b = LinearColorMapper(palette=["#000000"], low=0.0, high=1.0)
        dr._dash_cvar_step_bar({"bar": b}, ["#0000ff", "#ff0000"], [4.0],
                               2.0)
        assert (list(b.palette), b.low, b.high) == (
            ["#0000ff", "#ff0000"], 2.0, 6.0)
        dr._dash_cvar_step_bar({}, ["#0000ff"], [1.0], 1.0)

    def test_a_log_key_drops_its_non_positive_ticks(self):
        from bokeh.models import FixedTicker
        bar = ColorBar(ticker=FixedTicker(ticks=[0.0, 5000.0, 10000.0]),
                       major_label_overrides={0.0: "0", 5000.0: "5,000",
                                              10000.0: "10,000"})
        dr._dash_cvar_drop_nonpositive_ticks(bar)
        assert list(bar.ticker.ticks) == [5000.0, 10000.0]
        assert sorted(bar.major_label_overrides.values()) == ["10,000",
                                                              "5,000"]
        dr._dash_cvar_drop_nonpositive_ticks(None)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_log_key_is_ticked_as_twoway(self, tmp, mode):
        figs = _figs(tmp, mode, [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"colorvar": "price"}}],
                     _AUTO_DF, go={"zscale": "log"})
        [bar] = _bars(figs)
        labels = [bar.major_label_overrides.get(t) for t in bar.ticker.ticks]
        assert labels == [t for t in TRUTH["L_zlog"]["key_texts"]
                          if t != "Price"]


# ---------------------------------------------------------------------------
# sil:SD-4: the colour key's thickness is the scheme's gsize clegend_width
# (measured: B_<scheme>, twoway's key 0.9 of it), and the scheme's contour
# keys are read as twoway reads them (Z_<key>: none changes the picture).
# ---------------------------------------------------------------------------

_W42 = {"w42w": "gsize clegend_width small",
        "w42o": "yesno contours_outline yes",
        "w42c": "yesno contours_colorlines yes",
        "w42r": "yesno contours_reversekey yes",
        "w42n": "numstyle contours 4"}


@pytest.fixture(scope="module")
def schemes(tmp_path_factory):
    d = tmp_path_factory.mktemp("w42schemes")
    for name, line in _W42.items():
        (d / f"scheme-{name}.scheme").write_text(
            "#include s2color\n" + line + "\n")
    return str(d)


def _scheme_bo(name, schemes):
    bo = {"scheme": name}
    if name in _W42:
        bo["scheme_dirs"] = [schemes]
    return bo


class _Band(cb.KeyView):
    """A key cell read as a bar, its swatch band the bar's thickness."""

    def __init__(self, cell):
        super().__init__(cell)
        self.width = cell._dash_key_band


def _key_bars(figs):
    # Flipped (WP-42 CV-3): dash's colour key was a ColorBar; twoway draws
    # swatches beside a z axis (CV-3): the key cell's swatch band is the
    # key's thickness (clegend_width).
    return [_Band(v.cell) for f in figs for v in cb.key_views(f)]


class TestTheKeyWidth:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("scheme", ["s2color", "stcolor", "w42w"])
    def test_scheme_width(self, tmp, schemes, scheme, mode):
        want = TRUTH["B_" + scheme]
        figs = _figs(tmp, mode, [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"colorvar": "price"}}],
                     _AUTO_DF, bo=_scheme_bo(scheme, schemes))
        [bar] = _key_bars(figs)
        sp = dr.SchemeParser(scheme, ado_dirs=[schemes])
        assert bar.width == dr._dash_clegend_px(sp.clegend_width_rs)
        [f] = figs
        got = bar.width / float(f.width)
        tw = want["key_width"] / want["graph_width"]
        assert abs(got - tw) <= 0.15 * tw, (got, tw)

    @pytest.mark.parametrize("mode", MODES)
    def test_contour_key(self, tmp, mode):
        figs = _figs(tmp, mode, [{"type": "contour", "zvar": "price",
                                  "yvar": "mpg", "xvar": "weight",
                                  "options": {}}], _AUTO_DF)
        [bar] = _key_bars(figs)
        assert bar.width == dr._dash_clegend_px(
            dr.SchemeParser("s2color").clegend_width_rs)
        [f] = figs
        z = TRUTH["Z_ctl"]
        tw = z["key_width"] / z["graph_width"]
        assert abs(bar.width / float(f.width) - tw) <= 0.15 * tw

    def test_the_width_helper(self):
        # huge (6.9444 units) is 20 pt; twoway's key is 0.9 of it, 24 px.
        assert dr._dash_clegend_px(6.9444) == 24
        assert dr._dash_clegend_px(0.0) == 1
        assert dr.SchemeParser("s2color").clegend_width_rs == pytest.approx(
            6.9444)
        assert dr.SchemeParser("s2color").clegend_height_rs == 0.0


class TestTheSizeHelper:

    def test_the_size_helper(self):
        """The bar takes the scheme's clegend_width, and clegend_height as
        its length only when that is not zero."""
        class _S:
            clegend_width_rs = 2.777
            clegend_height_rs = 25.0
        bar = ColorBar()
        dr._dash_clegend_size(bar, dr.SchemeParser("s2color"))
        assert bar.width == 24 and bar.height == "auto"
        dr._dash_clegend_size(bar, _S())
        assert bar.width == dr._dash_clegend_px(2.777) == 10
        assert bar.height == dr._dash_clegend_px(25.0)
        dr._dash_clegend_size(bar, None)
        assert bar.width == 24


def _contour_look(figs):
    """What a contour figure draws: each renderer's glyph type and colours,
    and the key's palette and ticks."""
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if g is None:
                continue
            out.append((type(g).__name__,
                        repr(getattr(g, "fill_color", None)),
                        repr(getattr(g, "line_color", None)),
                        len(next(iter(r.data_source.data.values()), []))
                        if r.data_source.data else 0))
    for b in _key_bars(figs):
        out.append(("key", repr(getattr(b, "fill_color", None)),
                    list(getattr(b.ticker, "ticks", None) or [])))
    return out


class TestContourSchemeKeys:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe,scheme", [
        ("outline", "w42o"), ("colorlines", "w42c"), ("reversekey", "w42r"),
        ("levels", "w42n")])
    def test_key(self, tmp, schemes, probe, scheme, mode):
        ctl, z = TRUTH["Z_ctl"], TRUTH["Z_" + probe]
        keys = ("lastcuts", "n_path", "n_line", "n_use", "colours",
                "key_width", "key_texts")
        differs = any(z[k] != ctl[k] for k in keys)
        # twoway draws every one of them as it draws s2color (measured):
        # read and ignored, so dash's picture under the scheme is its
        # s2color picture.
        assert not differs, probe
        plot = [{"type": "contour", "zvar": "price", "yvar": "mpg",
                 "xvar": "weight", "options": {}}]
        base = _figs(tmp, mode, plot, _AUTO_DF, bo={"scheme": "s2color"})
        got = _figs(tmp, mode, plot, _AUTO_DF,
                    bo=_scheme_bo(scheme, schemes))
        assert _contour_look(got) == _contour_look(base)

