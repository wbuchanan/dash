"""WP-42 section 42-02 (CV-1): how a colorvar() layer's parts are painted.

What twoway draws is measured by scripts/extract_colorvar_parts_truth.do
into test/fixtures/colorvar_parts_truth.json (StataNow 19.5):

* ``F_<type>``: ``twoway <type> ..., colorvar(z) colorfillonly`` with z =
  rep78 (missing rows kept): every line part -- a line's level paths,
  connected's line, spikes, drop-line stems, caps, rcapsym's spines and
  the arrows' shafts and heads -- in the level colours (#0000ff ..
  #ffcc00, and #808080 for missing); only the fills of markers and bars
  take the levels, their outlines staying the series colour #1a476f.

Every test that draws runs in both modes: the saved page (DashRenderer)
and the served app (ServerAppBuilder); both run the same GlyphMapper.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import _figures_of, make_spec  # noqa: E402
from test_colorvar_steps import _colour_of, _hex, _rgb  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "colorvar_parts_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
MODES = ["saved", "served"]
F_TYPES = sorted(k[2:] for k in TRUTH if k.startswith("F_"))
# The types whose line parts twoway colours by level under colorfillonly.
LINE_TYPES = [t for t in F_TYPES if TRUTH["F_" + t]["line_strokes"]
              and t != "bar"]

_DF = pd.DataFrame(TRUTH["_data"])

_RANGE = {"rcap", "rcapsym"}
_PC = {"pcspike", "pcarrow", "pccapsym"}
_LINE_GLYPHS = {"Line", "MultiLine", "Segment", "Ray", "Patches", "Patch"}
_MARKER_GLYPHS = {"Scatter", "Circle"}
_BAR_GLYPHS = {"VBar", "HBar", "Quad", "Rect"}

_SEQ = itertools.count()
_CACHE: dict = {}


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return tmp_path_factory.mktemp("cvparts")


def _type_plot(ptype, opts):
    """The plot record dash.ado writes for the fixture's F_<type> command
    (extract_colorvar_parts_truth.do's type table)."""
    o = dict(opts)
    if ptype in _RANGE:
        return {"type": ptype, "yvar1": "y", "yvar2": "y2", "xvar": "t",
                "options": o}
    if ptype in _PC:
        return {"type": ptype, "y1var": "y", "x1var": "t", "y2var": "y2",
                "x2var": "t", "options": o}
    return {"type": ptype, "yvar": "y", "xvar": "t", "options": o}


def _figs(tmp, mode, plots, df=_DF, go=None):
    """The figures of a one-graph spec of *plots* over *df*, in *mode*,
    and the warnings the build gave."""
    key = (mode, json.dumps([plots, go], sort_keys=True), id(df))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots, graph_options=go)
    tag = next(_SEQ)
    sp = tmp / f"cvp_spec_{tag}.json"
    dp = tmp / f"cvp_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(
        df, value_labels=None, value_label_names=None,
        variable_labels=None)))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvp_app_{tag}.py"
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_cvp_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = (figs, [str(w.message) for w in caught])
    return _CACHE[key]


def _rows(renderer):
    """The rows *renderer* draws, through its view's filter."""
    n = max((len(v) for v in renderer.data_source.data.values()),
            default=0)
    flt = getattr(getattr(renderer, "view", None), "filter", None)
    idx = getattr(flt, "indices", None) if flt is not None else None
    if idx is not None:
        return [i for i in idx if i < n]
    bools = getattr(flt, "booleans", None) if flt is not None else None
    if bools is not None:
        return [i for i, b in enumerate(bools) if b and i < n]
    return list(range(n))


def _colours(renderer, prop):
    """The colours *renderer* draws on *prop* over its rows."""
    v = getattr(renderer.glyph, prop, None)
    rows = _rows(renderer)
    if not rows:
        return set()
    field = v.get("field") if isinstance(v, dict) else getattr(
        v, "field", None)
    tr = v.get("transform") if isinstance(v, dict) else getattr(
        v, "transform", None)
    if field is not None and tr is not None:
        col = list(renderer.data_source.data.get(field, []))
        return {_colour_of(tr, col[i]) for i in rows if i < len(col)}
    if v is None or field is not None:
        return set()
    return {_hex(v)}


def _painted(figs):
    """{part: set of colours} over every drawn renderer of *figs*: line
    parts' strokes, markers' and bars' fills and outlines."""
    out = {k: set() for k in ("line_strokes", "marker_fills",
                              "marker_strokes", "bar_fills", "bar_strokes")}
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if g is None or not r.visible or dr._dash_is_swatch(r) \
                    or str(r.name or "") == "__dash_keyproxy":
                continue
            kind = type(g).__name__
            if kind in _LINE_GLYPHS:
                out["line_strokes"] |= _colours(r, "line_color")
            elif kind in _MARKER_GLYPHS:
                out["marker_fills"] |= _colours(r, "fill_color")
                out["marker_strokes"] |= _colours(r, "line_color")
            elif kind in _BAR_GLYPHS:
                out["bar_fills"] |= _colours(r, "fill_color")
                out["bar_strokes"] |= _colours(r, "line_color")
    return out


def _close(got, want):
    """Sorted colour lists equal to within 1/255 a channel."""
    got, want = sorted(got), sorted(want)
    return len(got) == len(want) and all(
        abs(a - b) <= 1 for g, w in zip(got, want)
        for a, b in zip(_rgb(g), _rgb(w)))


_FILLONLY = {"colorvar": "z", "colorfillonly": "colorfillonly"}


class TestTheFixture:

    def test_meta_and_levels(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert meta[k], k
        # Five levels and the missing grey on spike's stems.
        assert len(TRUTH["F_spike"]["line_strokes"]) == 6
        assert "#808080" in TRUTH["F_spike"]["line_strokes"]
        assert TRUTH["F_scatter"]["marker_strokes"] == ["#1a476f"]


class TestFillonlyLines:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", F_TYPES)
    def test_type(self, tmp, ptype, mode):
        truth = TRUTH["F_" + ptype]
        assert truth["rc"] == 0
        figs, _w = _figs(tmp, mode, [_type_plot(ptype, _FILLONLY)])
        got = _painted(figs)
        if ptype != "bar":
            want = sorted(set(truth["line_strokes"])
                          | set(truth["head_strokes"]))
            assert _close(got["line_strokes"], want), (
                ptype, sorted(got["line_strokes"]), want)
        for part in ("marker_fills", "marker_strokes", "bar_fills",
                     "bar_strokes"):
            if truth[part]:
                assert _close(got[part], truth[part]), (
                    ptype, part, sorted(got[part]), truth[part])

    @pytest.mark.parametrize("mode", MODES)
    def test_line_is_split(self, tmp, mode):
        """One Line a level, the missing level's included, as twoway draws
        F_line's six paths."""
        plot = dict(_type_plot("line", _FILLONLY))
        plot["options"] = dict(plot["options"], sort="sort")
        figs, _w = _figs(tmp, mode, [plot])
        lines = [r for f in figs for r in f.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"
                 and _rows(r)]
        colours = {_hex(r.glyph.line_color) for r in lines}
        assert len(lines) == len(TRUTH["F_line"]["line_strokes"])
        assert _close(colours, TRUTH["F_line"]["line_strokes"])

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", F_TYPES)
    def test_silent(self, tmp, ptype, mode):
        """colorfillonly is drawn: the build names nothing about it."""
        _figs_, warns = _figs(tmp, mode, [_type_plot(ptype, _FILLONLY)])
        assert not [w for w in warns if "colorfillonly" in w], warns


# CV-6 and CV-7: the auto data's columns the M*/K* probes use, labelled
# as sysuse auto labels them.
_AUTO = pd.DataFrame({
    "mpg":     [30.0, 28.0, 25.0, 23.0, 22.0, 21.0, 19.0, 17.0, 16.0, 14.0],
    "weight":  [1800.0, 2010.0, 2200.0, 2650.0, 2930.0, 3000.0, 3100.0,
                3350.0, 3600.0, 4080.0],
    "price":   [4816.0, 10372.0, 3799.0, 11385.0, 4099.0, 5788.0, 4453.0,
                4749.0, 4082.0, 5189.0],
    "foreign": [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
    "rep78":   [4.0, 5.0, 3.0, 2.0, 1.0, 3.0, 4.0, 5.0, 2.0, 3.0],
})
_AUTO_LABELS = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
                "price": "Price", "foreign": "Car origin",
                "rep78": "Repair record 1978"}


def _auto_figs(tmp, mode, plots, go=None, df=None, bo=None, ifx=""):
    """_figs over the labelled auto columns (*bo* the build options,
    *ifx* the graph's if qualifier)."""
    df = _AUTO if df is None else df
    key = ("auto", mode, json.dumps([plots, go, bo, ifx], sort_keys=True),
           id(df))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots, graph_options=go, build_options=bo)
    if ifx:
        spec["graphs"][0]["if_expr"] = ifx
    tag = next(_SEQ)
    sp = tmp / f"cvp_spec_{tag}.json"
    dp = tmp / f"cvp_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(
        df, value_labels=None, value_label_names=None,
        variable_labels=_AUTO_LABELS)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvp_app_{tag}.py"
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_cvp_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = figs
    return figs


def _sc(yvar, **o):
    return {"type": "scatter", "yvar": yvar, "xvar": "weight",
            "options": dict(o)}


def _colour_keys(fig):
    """The figure's colour keys: ColorBars (a by() label box's excepted)
    and colour-key Legends."""
    out = []
    for side in (fig.right, fig.left, fig.above, fig.below, fig.center):
        for m in side:
            tn = type(m).__name__
            if (tn in ("ColorBar", "ContourColorBar")
                    and m.name != "dash_by_label_box") or (
                    tn == "Legend"
                    and str(m.name or "") == dr._COLORVAR_LEGEND_NAME):
                out.append(m)
    return out


def _plot_legends(fig):
    """The figure's drawn plot legends (not colour keys)."""
    return [m for side in (fig.right, fig.left, fig.above, fig.below,
                           fig.center) for m in side
            if type(m).__name__ == "Legend" and m.visible
            and str(m.name or "") != dr._COLORVAR_LEGEND_NAME
            and [it for it in m.items if it.visible]]


def _label(it):
    lab = it.label
    if isinstance(lab, dict):
        return lab.get("value")
    return getattr(lab, "value", lab)


_M1 = [_sc("mpg", colorvar="rep78"),
       _sc("price", colorvar="foreign",
           colorallowmultiple="colorallowmultiple")]


class TestOneKeyForTheGraph:

    @pytest.mark.parametrize("mode", MODES)
    def test_last_layers_key(self, tmp, mode):
        """M1: twoway draws one colour key, the last layer's ('Car
        origin', 0 .2 .. 1)."""
        truth = TRUTH["M1"]
        assert truth["rc"] == 0 and truth["key_texts"][-1] == "Car origin"
        assert "Repair record 1978" not in truth["key_texts"]
        [fig] = _auto_figs(tmp, mode, _M1)
        keys = _colour_keys(fig)
        assert len(keys) == 1, [str(k.title) for k in keys]
        assert str(keys[0].title) == "Car origin"

    @pytest.mark.parametrize("mode", MODES)
    def test_plot_legend(self, tmp, mode):
        """M1: and a plot legend keying both series."""
        truth = TRUTH["M1"]
        assert truth["below_texts"][-2:] == ["Mileage (mpg)", "Price"]
        [fig] = _auto_figs(tmp, mode, _M1)
        legs = _plot_legends(fig)
        assert len(legs) == 1, legs
        assert [_label(it) for it in legs[0].items if it.visible] == [
            "Mileage (mpg)", "Price"]

    @pytest.mark.parametrize("mode", MODES)
    def test_lone_layer_has_no_legend(self, tmp, mode):
        """One colorvar layer: one key, no plot legend (twoway's two-key
        rule), before and after this section."""
        [fig] = _auto_figs(tmp, mode, [_sc("mpg", colorvar="rep78")])
        assert len(_colour_keys(fig)) == 1
        assert _plot_legends(fig) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_contour_beside_colorvar(self, tmp, mode):
        """M3: twoway stops with r(198) on contour beside a colorvar()
        layer under colorallowmultiple; dash draws it, and the colorvar
        layer's key never removes contour's own key."""
        assert TRUTH["M3"]["rc"] == 198
        plots = [{"type": "contour", "zvar": "price", "yvar": "mpg",
                  "xvar": "weight", "options": {}},
                 _sc("mpg", colorvar="price",
                     colorallowmultiple="colorallowmultiple")]
        [fig] = _auto_figs(tmp, mode, plots)
        kinds = sorted(type(k).__name__ for k in _colour_keys(fig))
        assert "ContourColorBar" in kinds, kinds


_K9 = [_sc("mpg", colorvar="rep78"), _sc("price")]
_K9_CASES = {
    # probe: (plots, build options, the measured key colour)
    "K9": (_K9, None, TRUTH["K9"]["legend_marker_fills"][0]),
    "K9st": (_K9, {"scheme": "stcolor"},
             [c for c in TRUTH["K9st"]["right_marker_fills"]
              if c != "none"][2]),
    "M2": ([_sc("mpg", colorvar="rep78", colordiscrete="colordiscrete",
                coloruseplegend="coloruseplegend"), _sc("price")], None,
           TRUTH["M2"]["legend_marker_fills"][0]),
}


def _series_item(fig, text):
    """The drawn plot legend's item keyed *text*."""
    [leg] = _plot_legends(fig)
    [it] = [it for it in leg.items if _label(it) == text]
    return it


class TestTheProxySwatch:

    def test_the_measured_colours(self):
        """twoway keys the colorvar series in its pstyle colour: p1
        #1a476f under s2color, #1a85ff under stcolor; under
        coloruseplegend in level 1's (#0000ff)."""
        assert [_K9_CASES[k][2] for k in ("K9", "K9st", "M2")] == [
            "#1a476f", "#1a85ff", "#0000ff"]
        assert TRUTH["K9st"]["key_texts"][:2] == ["Mileage (mpg)", "Price"]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("probe", sorted(_K9_CASES))
    def test_pstyle_colour(self, tmp, probe, mode):
        plots, bo, want = _K9_CASES[probe]
        [fig] = _auto_figs(tmp, mode, plots, bo=bo)
        it = _series_item(fig, "Mileage (mpg)")
        [r] = it.renderers
        assert str(r.name) == "__dash_keyproxy"
        assert _hex(r.glyph.fill_color) == want
        if probe != "M2":
            assert _hex(r.glyph.line_color) == want

    @pytest.mark.parametrize("mode", MODES)
    def test_invisible(self, tmp, mode):
        """The proxy draws nothing (NaN coordinates), is in no HoverTool,
        and holds its layer's rows: the layer's source and filter."""
        [fig] = _auto_figs(tmp, mode, _K9)
        [p] = [r for r in fig.renderers
               if str(r.name or "") == "__dash_keyproxy"]
        base = [r for r in fig.renderers
                if getattr(r, "_dash_key_proxy", None) is p]
        assert len(base) == 1
        for f in ("x", "y"):
            v = getattr(p.glyph, f)
            v = v.get("value") if isinstance(v, dict) else getattr(
                v, "value", v)
            assert v != v, (f, v)
        assert p.data_source is base[0].data_source
        assert p.view.filter is base[0].view.filter
        for t in fig.tools:
            if type(t).__name__ == "HoverTool":
                assert p not in list(t.renderers or []
                                     if t.renderers != "auto" else [])
        assert len(_rows(p)) == len(_rows(base[0])) > 0

    @pytest.mark.parametrize("mode", MODES)
    def test_emptied_layer_has_no_key(self, tmp, mode):
        """scatter mpg weight if foreign == 1, colorvar(rep78) || scatter
        price weight, after the move foreign == 0 that leaves the colorvar
        layer no row: no plot-legend key with a row to draw for it, and
        Price's key stays.  Saved: the page built with the moved qualifier,
        as MOVE_CORPUS's saved side builds it; served: the redraw leaves
        the proxy's view no row, so Bokeh's draw_legend skips the item."""
        lay = dict(_sc("mpg", colorvar="rep78"), if_expr="foreign == 1")
        plots = [lay, _sc("price")]
        if mode == "saved":
            [fig] = _auto_figs(tmp, mode, plots, ifx="foreign == 0")
            keyed = [_label(it) for leg in fig.legend for it in leg.items
                     if it.visible and any(_rows(r) for r in it.renderers)]
            assert "Mileage (mpg)" not in keyed and "Price" in keyed
            return
        import test_mode_parity as tp
        spec = make_spec(plots, build_options={"filter": "foreign"})
        sp, dp = tmp / "cvp_emptied_s.json", tmp / "cvp_emptied_d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(
            _AUTO, variable_labels=_AUTO_LABELS)))
        ap = tmp / "cvp_emptied_app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), "_cvp_emptied", draw=False)
            doc = Document()
            mod.make_document(doc)
            [fig] = _figures_of(doc)
            prox = [r for r in fig.renderers
                    if str(r.name or "") == "__dash_keyproxy"]
            assert len(prox) == 1 and _rows(prox[0])
            [w] = [x for x in tp._widgets_of(doc)
                   if type(x).__name__ == "Select"]
            tp._fire(w, tp._move_widget_value(w, "Select", "0"))
        [fig] = _figures_of(doc)
        assert not [p for p in prox if _rows(p)]
        keyed = [_label(it) for leg in fig.legend for it in leg.items
                 if it.visible and any(_rows(r) for r in it.renderers)]
        assert "Mileage (mpg)" not in keyed and "Price" in keyed

    @pytest.mark.parametrize("mode", MODES)
    def test_by_matches_every_panel(self, tmp, mode):
        """The proxy's visible follows its renderer's, and by()'s legend
        cell matches it to every panel's proxy."""
        figs = _auto_figs(tmp, mode, _K9, go={"by": "foreign"})
        panels = [f for f in figs if any(
            str(r.name or "") == "__dash_keyproxy" for r in f.renderers)]
        assert len(panels) == 2
        [p] = [r for r in panels[0].renderers
               if str(r.name or "") == "__dash_keyproxy"]
        cbs = p.js_property_callbacks.get("change:visible", [])
        assert cbs, "the proxy's visible is not linked"
        got = dr._dash_by_panel_matches([p], panels)
        want = [r for f in panels for r in f.renderers
                if str(r.name or "") == "__dash_keyproxy"]
        assert got == want
