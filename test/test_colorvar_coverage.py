"""WP-31 section 15 (GAPS3 C8a): colorvar() on every plot type twoway
colours, and jitter() on rscatter, rcapsym, pcscatter and pccapsym.

What twoway does is measured, not modelled, by
scripts/extract_colorvar_types_truth.do into
test/fixtures/colorvar_types_truth.json (StataNow 19.5):

* ``types[<t>]``: ``twoway <t> ..., colorvar(z)`` for every type of
  test_twoway_option_parity.cscript's m6 list -- rc, each plot's ``.cvar``
  (the colour variable's serset column, missing when none) and the
  distinct colours of the exported SVG.  ``coloured`` are the 23 types whose
  view carries the colour variable; ``cv_silent`` the 19 where twoway takes
  colorvar() and draws nothing for it (twoway_yxview_parse.class:206-208:
  area, rarea and the classes with ``.allowcolorvar = 0``), where it does
  not even look the variable up (``colorvar(nosuchvar)`` rc 0 there, r(111)
  on a coloured type).
* ``multi_y``: two y variables with colorvar() on scatter line tsline bar
  connected dot dropline spike are r(198) "option colorvar() cannot be
  combined with multiple y variables in a <view> plot" (tsline's view is a
  line).
* ``line_L01``: ``twoway line mpg weight, colorvar(z) sort`` strokes its
  line in 5 colours: one path a level through that level's points
  (WP-32, D39 D-15f; test/test_colorvar_line_levels.py).
* ``jitter``: jitter(5) jitterseed(1) moves every marker of rscatter,
  rcapsym, pcscatter and pccapsym (both ends), at most 2.5% of the axis
  range each way, and leaves the spines where they are.

Both renderers run the same GlyphMapper, and every test that draws runs in
both modes: the saved page (DashRenderer) and the served app
(ServerAppBuilder).
"""
from __future__ import annotations

import itertools
import json
import math
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColorBar, HoverTool, Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
from test_server_layer_defects import (_figures_of, make_spec,  # noqa: E402
                                       plot_for)

_FIX = os.path.join(_HERE, "fixtures", "colorvar_types_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The types twoway colours by colorvar() (measured).
COLOURED = sorted(TRUTH["coloured"])
#: The types twoway takes colorvar() on and draws nothing for (measured).
SILENT = sorted(TRUTH["cv_silent"])
#: The coloured types drawn with Bokeh's Line glyph: one line a level.
LINE_TYPES = ["line", "tsline", "rline", "tsrline"]
#: The four types whose markers twoway jitters and dash did not.
JIT_TYPES = ["rscatter", "rcapsym", "pcscatter", "pccapsym"]
MODES = ["saved", "served"]

#: Sorted by weight, so the data's order and the order of x agree: a
#: line's first point is the first row either way.
_DF = pd.DataFrame({
    "mpg":     [30.0, 28.0, 25.0, 23.0, 22.0, 21.0, 19.0, 17.0, 16.0, 14.0],
    "weight":  [1800.0, 2010.0, 2200.0, 2650.0, 2930.0, 3000.0, 3100.0,
                3350.0, 3600.0, 4080.0],
    "price":   [4816.0, 10372.0, 3799.0, 11385.0, 4099.0, 5788.0, 4453.0,
                4749.0, 4082.0, 5189.0],
    "foreign": [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
    "rep78":   [4.0, 5.0, 3.0, 2.0, 1.0, 3.0, 4.0, 5.0, 2.0, 3.0],
})

_SEQ = itertools.count()
_CACHE: dict = {}


def _write(tmp, spec):
    tag = next(_SEQ)
    sp = tmp / f"cvc_spec_{tag}.json"
    dp = tmp / f"cvc_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return tag, str(sp), str(dp)


def _figs(tmp, mode, plots):
    """The figures of a one-graph spec of *plots*, in *mode*."""
    key = (mode, json.dumps(plots, sort_keys=True))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots)
    tag, sp, dp = _write(tmp, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvc_app_{tag}.py"
            dr.ServerAppBuilder(sp, dp).build(str(ap))
            mod = load_app(str(ap), f"_cvc_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = figs
    return figs


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return tmp_path_factory.mktemp("cvc")


def _fig(tmp, mode, ptype, opts):
    [f] = _figs(tmp, mode, [plot_for(ptype, opts)])
    return f


def _is_field(spec):
    return getattr(spec, "field", None) is not None and \
        getattr(spec, "transform", None) is not None


def _mapped(r):
    """The colour properties of renderer *r*'s glyph that read a field."""
    g = r.glyph
    return [p for p in ("fill_color", "line_color")
            if hasattr(g, p) and _is_field(getattr(g, p))]


def _keys(fig):
    """The colour keys on *fig*: ColorBars and colorvar() Legends.

    Flipped (WP-42 CV-3): twoway draws one key of swatches beside a z
    axis, a key cell (fig._dash_key_cell), which counts with them."""
    out = []
    if getattr(fig, "_dash_key_cell", None) is not None:
        out.append(fig._dash_key_cell)
    for side in (fig.right, fig.left, fig.above, fig.below, fig.center):
        for m in side:
            if isinstance(m, ColorBar):
                out.append(m)
            elif isinstance(m, Legend) and m.name == dr._COLORVAR_LEGEND_NAME:
                out.append(m)
    return out


def _key_level_colour(fig, v):
    """The colour of the key level holding *v* on *fig*'s binned key cell
    (WP-42 CV-3: the key was a ColorBar read through its mapper): one
    swatch a level, cut at the axis's ticks, a value on a cut twoway's
    level below (CV-8)."""
    kc = fig._dash_key_cell._dash_keycell
    cuts = list(kc["ticker"].ticks)
    return list(kc["src"].data["c"])[sum(1 for t in cuts if t < v)]


def _plot_renderers(fig):
    """The renderers a layer draws: the colour key's invisible swatches
    are left out."""
    # WP-42 CV-7: legend-only proxies draw nothing (drawn_renderers)
    return [r for r in drawn_renderers(fig)
            if not str(getattr(r, "name", "") or "").startswith(
                dr._DASH_SWATCH_PREFIX)]


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta(self):
        m = TRUTH["_meta"]
        assert sorted(m) == ["born_date", "dash_commit", "extracted",
                             "source", "stata_version"]
        assert m["source"] == "scripts/extract_colorvar_types_truth.do"
        assert float(m["stata_version"]) >= 19

    def test_every_type_is_measured_once(self):
        assert sorted(COLOURED + SILENT) == sorted(TRUTH["types"])
        assert not set(COLOURED) & set(SILENT)
        assert all(TRUTH["types"][t]["rc"] == 0 for t in TRUTH["types"])

    def test_a_silent_type_never_looks_the_variable_up(self):
        for t in SILENT:
            assert TRUTH["types"][t]["bad_var_rc"] == 0, t
        for t in COLOURED:
            assert TRUTH["types"][t]["bad_var_rc"] == 111, t

    def test_jitter_moved_every_marker_and_no_spine(self):
        for t in JIT_TYPES:
            j = TRUTH["jitter"][t]
            assert j["markers_with"] == j["markers_without"] == j["moved"]
            assert j["max_dx_frac"] <= 0.05 and j["max_dy_frac"] <= 0.05
            assert j["lines_unmoved"]


# ---------------------------------------------------------------------------
# dash.ado: the lists are the measured ones
# ---------------------------------------------------------------------------

def _ado():
    with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


class TestTheAdoText:

    def test_lists_match_the_fixture(self):
        txt = _ado()
        found = re.findall(r'^\s*local cv_silent "([^"]*)"', txt, re.M)
        assert len(found) == 1, found
        assert sorted(found[0].split()) == SILENT
        assert "cv_types" not in txt and "jit_undrawn" not in txt

    def test_the_multi_y_refusal_names_twoways_types(self):
        txt = _ado()
        m = re.search(r'local cv_multi "([^"]*)"', txt)
        assert m, "no cv_multi list"
        want = {k for k, v in TRUTH["multi_y"].items() if v["rc"] == 198}
        assert set(m.group(1).split()) == want
        assert "cannot be combined with multiple y variables in a" in txt


# ---------------------------------------------------------------------------
# Every coloured type is coloured, with one key
# ---------------------------------------------------------------------------

class TestEveryColouredType:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", COLOURED)
    def test_coloured(self, tmp, mode, ptype):
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        rs = _plot_renderers(fig)
        if ptype in LINE_TYPES:
            lines = [r for r in rs if type(r.glyph).__name__ == "Line"]
            assert lines, [type(r.glyph).__name__ for r in rs]
            default = dr.SchemeParser("").default_color(0, "line")
            for r in lines:
                assert isinstance(r.glyph.line_color, str)
                assert r.glyph.line_color != default, ptype
        else:
            assert any(_mapped(r) for r in rs), \
                [(type(r.glyph).__name__, r.glyph.line_color) for r in rs]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", COLOURED)
    def test_one_key(self, tmp, mode, ptype):
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        assert len(_keys(fig)) == 1, ptype

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["rcap", "rcapsym", "dropline",
                                       "pccapsym", "rscatter", "rconnected"])
    def test_every_part_is_coloured(self, tmp, mode, ptype):
        """twoway colours the spine, the caps and the markers alike
        (fixture: the SVG's line strokes and marker fills both take the
        five levels)."""
        t = TRUTH["types"][ptype]
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        rs = [r for r in _plot_renderers(fig)
              if type(r.glyph).__name__ in ("Segment", "Scatter")]
        assert rs and all(_mapped(r) for r in rs), \
            [(type(r.glyph).__name__, _mapped(r)) for r in rs]
        assert len(t["colours_with"]) > len(t.get("colours_without", []))

    @pytest.mark.parametrize("mode", MODES)
    def test_a_discrete_key_on_bars(self, tmp, mode):
        fig = _fig(tmp, mode, "bar", {"colorvar": "rep78",
                                      "colordiscrete": "yes"})
        [vb] = [r for r in _plot_renderers(fig)
                if type(r.glyph).__name__ == "VBar"]
        assert _mapped(vb) == ["fill_color", "line_color"]
        assert vb.glyph.fill_color.field.startswith(dr._DASH_CVAR_PREFIX)
        # Flipped (WP-42 CV-3): a Legend of five items; the key cell's five
        # swatches, each level labelled on its axis.
        [cell] = _keys(fig)
        assert len(cell._dash_keycell["src"].data["c"]) == 5
        assert sorted(cell._dash_key_axis.major_label_overrides) == \
            [1.0, 2.0, 3.0, 4.0, 5.0]


class TestArrowHeads:
    """twoway colours a pcarrow's head with its shaft (fixture
    head_strokes_with: the five levels)."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_heads_take_the_shaft_colours(self, tmp, mode, ptype):
        assert len(TRUTH["types"][ptype]["head_strokes_with"]) == 5
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        # WP-42 CV-7: legend-only proxies draw nothing
        [seg] = [r for r in _plot_renderers(fig)
                 if type(r.glyph).__name__ == "Segment"]
        [hr] = [r for r in fig.renderers
                if "dash-arrowhead" in (r.tags or [])]
        assert _is_field(seg.glyph.line_color)
        assert _is_field(hr.glyph.line_color)
        fld = hr.glyph.line_color.field
        assert fld == seg.glyph.line_color.field
        assert fld in hr.data_source.data
        cb = [m for m in fig.references()
              if type(m).__name__ == "CustomJS"
              and m.name == "dash_arrow_head"]
        assert cb and cb[0].args["cc"] == fld

    @requires_node
    def test_the_head_script_writes_the_colour_column(self):
        import test_arrowheads as ta
        data = ta._rows_data()
        data["__dash_cvar1_z"] = ["a", "b", "c", "d", "e"]
        out = _run_heads_cc(data, "__dash_cvar1_z")
        assert out["__dash_cvar1_z"] == ["a", "b", "c", "d", "e"]
        assert out["row"] == [0, 1, 2, 3, 4]


def _run_heads_cc(data, cc):
    """_DASH_ARROW_HEAD_JS under node with a colour column *cc*."""
    cols = dict(data)
    cols["__dash_head_px"] = [12.0] * len(cols["x1"])
    src = """
const mk = (a, b) => ({compute: (v) => a * v + b, invert: (s) => (s - b) / a});
const xsc = mk(90, 30), ysc = mk(-55, 400);
const view = {frame: {x_scales: new Map([["default", xsc]]),
                      y_scales: new Map([["default", ysc]]),
                      x_scale: xsc, y_scale: ysc},
              canvas_view: {el: {}}};
const Bokeh = {index: {find_one: () => ({plot_view: view})}};
const heads = {tags: [], data: {xs: [], ys: [], row: []}};
const args = {src: {data: %s}, heads: heads,
              hr: {x_range_name: "default", y_range_name: "default"},
              x1: "x1", y1: "y1", x2: "x2", y2: "y2", hpx: "__dash_head_px",
              ends: 1, barb: 0.0, ang: %r, cc: %s};
const f = new Function("Bokeh", ...Object.keys(args), %s);
f(Bokeh, ...Object.values(args));
console.log(JSON.stringify(heads.data));
""" % (json.dumps(cols), math.radians(dr._DASH_ARROW_ANGLE_DEG),
       json.dumps(cc), json.dumps(dr._DASH_ARROW_HEAD_JS))
    return run_js(src)


# ---------------------------------------------------------------------------
# A line is one line a colour level (WP-32, D39 D-15f)
# ---------------------------------------------------------------------------

def _level_lines(fig):
    """{colour: [rep78 of each drawn row]} of the Line renderers."""
    out = {}
    for r in fig.renderers:
        if type(r.glyph).__name__ != "Line":
            continue
        d = r.data_source.data
        vals = [v for v in d.get("rep78", []) if v == v and v is not None]
        if vals:
            out.setdefault(r.glyph.line_color, []).extend(vals)
    return out


class TestLinePerLevel:
    """Flipped (WP-32, D39 D-15f): the whole line took its first point's
    level; it is one line a level, as twoway draws it
    (test/test_colorvar_line_levels.py measures the paths)."""

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["line", "tsline"])
    def test_each_line_is_one_level(self, tmp, mode, ptype):
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        lines = _level_lines(fig)
        assert len(lines) == len(set(_DF["rep78"]))
        for colour, vals in lines.items():
            assert {_key_level_colour(fig, v) for v in vals} == {colour}

    @pytest.mark.parametrize("mode", MODES)
    def test_connected_line_and_markers(self, tmp, mode):
        fig = _fig(tmp, mode, "connected", {"colorvar": "rep78"})
        for colour, vals in _level_lines(fig).items():
            assert {_key_level_colour(fig, v) for v in vals} == {colour}
        [sc] = [r for r in _plot_renderers(fig)
                if type(r.glyph).__name__ == "Scatter"]
        assert _mapped(sc)

    def test_a_missing_first_level_is_the_missing_colour(self, tmp):
        """_colorvar_scalar still reads a line drawn outside map_line."""
        gm = dr.GlyphMapper()
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0],
                                "z": [float("nan"), 1.0, 2.0]})
        r = fig.line(x="x", y="y", source=src)
        gm._apply_colorvar(fig, r, src, {"colorvar": "z",
                                         "colormissing": "red"})
        assert r.glyph.line_color == "#ff0000"

    def test_the_level_index_reads_each_mapper_as_the_scalar_does(self):
        from bokeh.models import (CategoricalColorMapper,
                                  LinearColorMapper, LogColorMapper)
        G = dr.GlyphMapper
        pal = ["#000001", "#000002", "#000003", "#000004"]
        cases = [
            (LinearColorMapper(palette=pal, low=0, high=4),
             [-1.0, 0.0, 0.99, 1.0, 3.99, 4.0, 9.0, float("nan")]),
            (LogColorMapper(palette=pal, low=1, high=16),
             [0.5, 1.0, 2.0, 7.9, 8.0, 16.0, 40.0]),
            (CategoricalColorMapper(palette=pal[:2], factors=["a", "b", "c"]),
             ["a", "b", "c", "d", None]),
        ]
        for mapper, vals in cases:
            spec = {"field": "v", "transform": mapper}
            idx = G._colorvar_level_index(spec, vals)
            for v, k in zip(vals, idx):
                from bokeh.models import ColumnDataSource
                want = G._colorvar_scalar(ColumnDataSource({"v": [v]}),
                                          None, spec)
                assert G._colorvar_level_colour(spec, int(k)) == want, \
                    (type(mapper).__name__, v, k)


# ---------------------------------------------------------------------------
# The silent types: nothing drawn, nothing said
# ---------------------------------------------------------------------------

class TestSilentTypes:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["area", "rarea", "lfit", "histogram",
                                       "kdensity", "pci", "scatteri"])
    def test_nothing_drawn_nothing_said(self, tmp, mode, ptype):
        """dash.ado drops colorvar() on these (U15-01, U15-05); a spec
        written by hand that still carries it draws no key."""
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78"})
        assert _keys(fig) == []
        assert not any(_mapped(r) for r in _plot_renderers(fig))


# ---------------------------------------------------------------------------
# The colour column never reaches a tooltip
# ---------------------------------------------------------------------------

class TestTooltips:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["bar", "rcap", "pccapsym"])
    def test_no_colour_column(self, tmp, mode, ptype):
        fig = _fig(tmp, mode, ptype, {"colorvar": "rep78",
                                      "colordiscrete": "yes"})
        for t in fig.tools:
            if isinstance(t, HoverTool) and t.tooltips:
                assert dr._DASH_CVAR_PREFIX not in json.dumps(
                    list(t.tooltips), default=str)


# ---------------------------------------------------------------------------
# jitter() on rscatter, rcapsym, pcscatter, pccapsym
# ---------------------------------------------------------------------------

def _markers(fig):
    """[(xs, ys)] of the layer's marker renderers, in drawing order."""
    out = []
    for r in _plot_renderers(fig):
        if type(r.glyph).__name__ != "Scatter":
            continue
        if r.glyph.marker == "dash":
            continue
        d = r.data_source.data
        out.append((np.asarray(d[r.glyph.x], dtype=float),
                    np.asarray(d[r.glyph.y], dtype=float)))
    return out


def _segments(fig):
    out = []
    for r in _plot_renderers(fig):
        if type(r.glyph).__name__ != "Segment":
            continue
        d = r.data_source.data
        g = r.glyph
        out.append(tuple(np.asarray(d[c], dtype=float).tolist()
                         for c in (g.x0, g.y0, g.x1, g.y1)))
    return out


_JIT = {"jitter": "5", "jitterseed": "1"}


def _labels_xy(fig):
    """[(x, y, text)] of every marker label the figure draws."""
    from bokeh.models import LabelSet
    out = []
    for side in (fig.center, fig.above, fig.below, fig.left, fig.right):
        for m in side:
            if not isinstance(m, LabelSet):
                continue
            d = m.source.data
            for x, y, t in zip(d[m.x], d[m.y], d[m.text]):
                # A NaN position draws no label (pcscatter's second point).
                if math.isfinite(float(x)) and math.isfinite(float(y)):
                    out.append((float(x), float(y), str(t)))
    return sorted(out, key=str)


class TestJitterFourTypes:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", JIT_TYPES)
    def test_moves(self, tmp, mode, ptype):
        plain = _markers(_fig(tmp, mode, ptype, {}))
        jit = _markers(_fig(tmp, mode, ptype, _JIT))
        x0 = np.concatenate([m[0] for m in plain])
        y0 = np.concatenate([m[1] for m in plain])
        x1 = np.concatenate([m[0] for m in jit])
        y1 = np.concatenate([m[1] for m in jit])
        assert len(x1) == len(x0) and len(x0) > 0
        moved = (np.abs(x1 - x0) > 0) | (np.abs(y1 - y0) > 0)
        assert moved.all(), ptype
        # Half of 5% of each axis's range of the markers drawn.
        bx = 0.025 * (np.nanmax(x0) - np.nanmin(x0)) + 1e-9
        by = 0.025 * (np.nanmax(y0) - np.nanmin(y0)) + 1e-9
        assert np.nanmax(np.abs(x1 - x0)) <= bx
        assert np.nanmax(np.abs(y1 - y0)) <= by

    @pytest.mark.parametrize("ptype", JIT_TYPES)
    def test_seeded(self, tmp, ptype):
        a = _markers(_fig(tmp, "saved", ptype, _JIT))
        b = _markers(_fig(tmp, "served", ptype, _JIT))
        assert len(a) == len(b)
        for (xa, ya), (xb, yb) in zip(a, b):
            assert np.allclose(xa, xb) and np.allclose(ya, yb)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", JIT_TYPES)
    def test_labels_stay_at_the_data(self, tmp, mode, ptype):
        """twoway moves the markers and leaves their mlabel() labels where
        the data are (fixture jitter[<type>].labels_moved == 0); so does
        dash, in both modes."""
        j = TRUTH["jitter"][ptype]
        assert j["labels"] == j["labels_with"] > 0
        assert j["labels_moved"] == 0
        plain = _labels_xy(_fig(tmp, mode, ptype, {"mlabel": "rep78"}))
        moved = _labels_xy(_fig(tmp, mode, ptype,
                                dict(_JIT, mlabel="rep78")))
        assert plain and plain == moved

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ["rcapsym", "pccapsym"])
    def test_spine_unjittered(self, tmp, mode, ptype):
        assert TRUTH["jitter"][ptype]["lines_unmoved"]
        assert _segments(_fig(tmp, mode, ptype, _JIT)) == \
            _segments(_fig(tmp, mode, ptype, {}))


# ---------------------------------------------------------------------------
# The helpers, one by one
# ---------------------------------------------------------------------------

class TestTheHelpers:

    def test_paint_sets_what_the_glyph_has(self):
        from bokeh.models import (ColumnDataSource, LinearColorMapper,
                                  Segment, Scatter)
        gm = dr.GlyphMapper()
        m = LinearColorMapper(palette=["#000000", "#ffffff"], low=0, high=1)
        spec = {"field": "z", "transform": m}
        src = ColumnDataSource({"x": [0.0], "y": [0.0], "z": [1.0]})
        seg, sc = Segment(), Scatter()
        gm._colorvar_paint(seg, src, spec)
        gm._colorvar_paint(sc, src, spec)
        assert _is_field(seg.line_color) and not hasattr(seg, "fill_color")
        assert _is_field(sc.fill_color) and _is_field(sc.line_color)

    def test_paint_gives_a_line_its_first_points_colour(self):
        from bokeh.models import ColumnDataSource, Line, LinearColorMapper
        gm = dr.GlyphMapper()
        m = LinearColorMapper(palette=["#000000", "#ffffff"], low=0, high=1)
        src = ColumnDataSource({"x": [float("nan"), 1.0, 2.0],
                                "y": [1.0, 1.0, 2.0], "z": [0.0, 1.0, 0.0]})
        g = Line(x="x", y="y")
        gm._colorvar_paint(g, src, {"field": "z", "transform": m})
        assert g.line_color == "#ffffff"

    def test_scalar_reads_each_mapper_as_bokehjs_does(self):
        from bokeh.models import (CategoricalColorMapper, ColumnDataSource,
                                  Line, LinearColorMapper, LogColorMapper)
        S = dr.GlyphMapper._colorvar_scalar
        g = Line(x="x", y="y")

        def src(v):
            return ColumnDataSource({"x": [1.0], "y": [1.0], "z": [v]})
        pal = ["#000001", "#000002", "#000003", "#000004"]
        lin = LinearColorMapper(palette=pal, low=0, high=4, nan_color="#aaaaaa")
        assert S(src(0.0), g, {"field": "z", "transform": lin}) == pal[0]
        assert S(src(2.5), g, {"field": "z", "transform": lin}) == pal[2]
        assert S(src(4.0), g, {"field": "z", "transform": lin}) == pal[3]
        assert S(src(9.0), g, {"field": "z", "transform": lin}) == pal[3]
        assert S(src(float("nan")), g,
                 {"field": "z", "transform": lin}) == "#aaaaaa"
        log = LogColorMapper(palette=pal, low=1, high=10000)
        assert S(src(100.0), g, {"field": "z", "transform": log}) == pal[2]
        cat = CategoricalColorMapper(factors=["a", "b"], palette=pal[:2],
                                     nan_color="#bbbbbb")
        assert S(src("b"), g, {"field": "z", "transform": cat}) == pal[1]
        assert S(src(None), g, {"field": "z", "transform": cat}) == "#bbbbbb"
        empty = ColumnDataSource({"x": [], "y": [], "z": []})
        assert S(empty, g, {"field": "z", "transform": lin}) is None

    def test_layer_draws_one_key_and_shares_the_column(self):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        gm = dr.GlyphMapper()
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y0": [0.0, 0.0],
                                "y1": [1.0, 2.0], "z": [1.0, 2.0]})
        a = fig.segment(x0="x", y0="y0", x1="x", y1="y1", source=src)
        b = fig.scatter(x="x", y="y1", source=src)
        gm._colorvar_layer(fig, [(a, src), (b, src)],
                           {"colorvar": "z", "colordiscrete": "yes"})
        assert len(_keys(fig)) == 1
        assert b.glyph.fill_color.field == a.glyph.line_color.field
        assert sum(k.startswith(dr._DASH_CVAR_PREFIX) for k in src.data) == 1
        gm._colorvar_layer(fig, [(a, src)], {})
        assert len(_keys(fig)) == 1

    def test_jitter_points(self):
        G = dr.GlyphMapper._jitter_points
        cols = {"x": [1.0, 2.0, 3.0, 4.0], "y": [10.0, 20.0, 30.0, 40.0]}
        assert G(dict(cols), "x", "y", {}, "rscatter") is False
        out = dict(cols)
        assert G(out, "x", "y", {"jitter": "5", "jitterseed": "2"},
                 "rscatter") is True
        jx = np.asarray(out[dr._DASH_JITTER_X])
        assert np.all(np.abs(jx - np.asarray(cols["x"])) <= 0.025 * 3 + 1e-12)
        again = dict(cols)
        G(again, "x", "y", {"jitter": "5", "jitterseed": "2"}, "rscatter")
        assert again[dr._DASH_JITTER_Y] == out[dr._DASH_JITTER_Y]
        assert out["x"] == cols["x"]
