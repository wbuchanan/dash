"""Arrowheads drawn from the marker options and the scheme, as twoway draws
them (WP-31 section 02, GAPS3 C1; DECISIONS D1).

The defect, measured at 4e2bd90: pcarrow, pcbarrow and pcarrowi drew every
head as Bokeh's ``OpenHead(size=10)`` (pcbarrow ``NormalHead(size=10)``,
filled black, Bokeh's default): ``msize() mcolor() mfcolor() mlcolor()
mlwidth()`` were written to the spec and never read, the half-angle was
Bokeh's fixed atan(0.5) = 26.57 degrees, and ``mangle()``, ``barbsize()``
and ``headlabel`` were not declared (a generic note named them).

twoway (scripts/extract_arrowhead_truth.do, test/fixtures/
arrowhead_truth.json) draws ``_gr_arrowhead``'s geometry: two open strokes
``msize()`` long (the scheme's ``symbolsize parrow``, 1.52778 rs) at
``mangle()`` (``anglestyle stdarrow``, 28.64 degrees) back along the
shaft; with ``barbsize() > 0`` a filled polygon tip, A, B, C whose B is
``barbsize*cos(mangle)`` behind the tip; the stroke in ``mlcolor()``/
``mcolor()`` (else the shaft's colour) at ``mlwidth()``, the fill in
``mfcolor()``/``mcolor()`` (else the series colour); pcbarrow at both
ends; ``headlabel`` puts the labels at the second point.  A row missing
its second point draws nothing at all -- no shaft, no head and no marker
(``onepoint``: 4 shafts, 8 strokes, 0 circles against 5, 10, 0), so dash
keeps dropping it (D-02.d).  twoway refuses none of barbsize(-1),
barbsize(20000), mangle(400) (rc 0) and notes an unknown name for each.

dash now draws one head glyph per layer (``multi_line`` open, ``patches``
filled) over a source _DASH_ARROW_HEAD_JS fills in screen pixels from the
shaft's source; the size travels with each row in ``__dash_head_px``.
"""
import json
import math
import os
import pathlib
import re
import sys
import tempfile
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import (Arrow, ColumnDataSource, CustomJS, LabelSet,  # noqa: E402
                          MultiLine, Patches)
from bokeh.plotting import figure  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402

# WP-47 MS-15: the marker labels are Text glyph renderers; a reader of the
# LabelSets they were reads them as conftest.MarkerLabels, beside any
# other LabelSet.
from bokeh.models import LabelSet  # noqa: E402
from conftest import MarkerLabels, mlabel_sets  # noqa: E402
_MLS = (LabelSet, MarkerLabels)


def _mls_center(fig):
    return list(fig.center) + mlabel_sets(fig)


def _mls_select(doc):
    return list(doc.select({"type": LabelSet})) + mlabel_sets(doc)


def _mls_all(objs):
    objs = list(objs)
    return objs + mlabel_sets(objs)


_FIX = os.path.join(_HERE, "fixtures", "arrowhead_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The extract script's five rows, y1 x1 y2 x2.
ROWS = [(1, 1, 2, 2), (2, 1, 3, 3), (3, 2, 4, 2), (4, 3, 5, 4), (5, 4, 6, 6)]
TYPES = ["pcarrow", "pcbarrow", "pcarrowi"]
_ENDS = {"pcarrow": 1, "pcbarrow": 2, "pcarrowi": 1}


def _df(rows=ROWS):
    return pd.DataFrame({"y1": [float(r[0]) for r in rows],
                         "x1": [float(r[1]) for r in rows],
                         "y2": [float(r[2]) for r in rows],
                         "x2": [float(r[3]) for r in rows]})


def _draw(ptype, options=None, rows=ROWS, gm=None):
    """(figure, mapper) after drawing *ptype* over *rows*."""
    gm = gm or dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if ptype == "pcarrowi":
            gm.map_pcarrowi(fig, [list(map(float, r)) for r in rows],
                            dict(options or {}))
        else:
            getattr(gm, "map_" + ptype)(fig, ColumnDataSource(_df(rows)),
                                        "y1", "x1", "y2", "x2",
                                        dict(options or {}))
    return fig, gm


def _arrows(fig):
    return [a for a in fig.center if isinstance(a, Arrow)]


def _head_renderers(fig):
    return [r for r in fig.renderers if "dash-arrowhead" in (r.tags or [])]


def _head_cbs(model):
    """The arrowhead scripts reachable from *model*."""
    return [m for m in model.references()
            if isinstance(m, CustomJS) and m.name == "dash_arrow_head"]


def _cb(fig):
    [cb] = _head_cbs(fig)
    return cb


# ---------------------------------------------------------------------------
# The script under node, with a stub view whose scales are linear maps
# ---------------------------------------------------------------------------

#: Unequal x and y factors, y down as on a canvas.
_SX = (90.0, 30.0)
_SY = (-55.0, 400.0)


def _run_heads(data, *, hpx, ends=1, barb=0.0, ang=None, sx=_SX, sy=_SY):
    """Run _DASH_ARROW_HEAD_JS once under node over *data* (a dict of
    columns y1 x1 y2 x2, NaN allowed) and return the head source it
    wrote, ``{"xs", "ys", "row"}``."""
    ang = math.radians(dr._DASH_ARROW_ANGLE_DEG) if ang is None else ang
    cols = dict(data)
    cols["__dash_head_px"] = [hpx] * len(cols["x1"])
    src = """
const mk = (a, b) => ({compute: (v) => a * v + b, invert: (s) => (s - b) / a});
const xsc = mk(%r, %r), ysc = mk(%r, %r);
const view = {frame: {x_scales: new Map([["default", xsc]]),
                      y_scales: new Map([["default", ysc]]),
                      x_scale: xsc, y_scale: ysc},
              canvas_view: {el: {}}};
const Bokeh = {index: {find_one: () => ({plot_view: view})}};
const heads = {tags: [], data: {xs: [], ys: [], row: []}};
const args = {src: {data: %s}, heads: heads,
              hr: {x_range_name: "default", y_range_name: "default"},
              x1: "x1", y1: "y1", x2: "x2", y2: "y2", hpx: "__dash_head_px",
              ends: %d, barb: %r, ang: %r};
const f = new Function("Bokeh", ...Object.keys(args), %s);
f(Bokeh, ...Object.values(args));
console.log(JSON.stringify(heads.data));
""" % (sx[0], sx[1], sy[0], sy[1], json.dumps(cols), int(ends),
       float(barb), float(ang), json.dumps(dr._DASH_ARROW_HEAD_JS))
    return run_js(src)


def _px(xs, ys, sx=_SX, sy=_SY):
    return [(sx[0] * x + sx[1], sy[0] * y + sy[1]) for x, y in zip(xs, ys)]


def _angle(u, v):
    c = (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def _sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def _rows_data(rows=ROWS):
    return {"y1": [float(r[0]) for r in rows], "x1": [float(r[1]) for r in rows],
            "y2": [float(r[2]) for r in rows], "x2": [float(r[3]) for r in rows]}


class TestTheFixture:
    def test_meta_is_stamped(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert TRUTH["_meta"]["source"] == "scripts/extract_arrowhead_truth.do"

    def test_twoways_defaults(self):
        d = TRUTH["heads"]["default"]
        assert d["angle"] == 28.64
        assert d["size_val"] == pytest.approx(1.52778, abs=1e-4)
        assert d["backsize_val"] == 0
        # Two open strokes per head, msize() long, at 28.64 degrees.
        assert d["head_strokes"] == 10 and d["filled_heads"] == 0
        assert d["stroke_len_rs"] == pytest.approx(1.52778, rel=0.002)
        assert d["half_angle"] == pytest.approx(28.64, abs=0.1)
        assert TRUTH["heads"]["pcbarrow"]["head_strokes"] == 20
        assert TRUTH["heads"]["pcbarrow"]["head_stroke_colours"] != ["#000000"]


class TestTheHeadSize:
    @pytest.mark.parametrize("ptype", TYPES)
    def test_default_is_the_schemes_parrow(self, ptype):
        fig, gm = _draw(ptype)
        assert not _arrows(fig)
        src = _cb(fig).args["src"]
        want = gm.scheme.default_arrow_size(0)
        assert list(src.data["__dash_head_px"]) == [want] * len(ROWS)
        # s2color's symbolsize parrow is medium: the marker scatter draws
        # with msize(medium).
        assert want == pytest.approx(gm.tr.translate_msize("medium"))

    @pytest.mark.parametrize("ptype", TYPES)
    @pytest.mark.parametrize("m", ["small", "large", "vlarge", "2", "*2"])
    def test_msize_scales_the_head(self, ptype, m):
        """The column scales as twoway's strokes scale (within 2%)."""
        key = {"*2": "msize_x2"}.get(m, "msize_" + m)
        fig, gm = _draw(ptype, {"msize": m})
        got = _cb(fig).args["src"].data["__dash_head_px"][0]
        base = gm.scheme.default_arrow_size(0)
        want = (TRUTH["heads"][key]["stroke_len_rs"]
                / TRUTH["heads"]["default"]["stroke_len_rs"])
        assert got / base == pytest.approx(want, rel=0.02)

    def test_the_label_radius_reads_the_same_size(self, monkeypatch):
        seen = []
        gm = dr.GlyphMapper()
        real = gm._mlabel_radius_px
        monkeypatch.setattr(gm, "_mlabel_radius_px",
                            lambda o, b: seen.append(b) or real(o, b))
        _draw("pcarrow", {"msize": "large"}, gm=gm)
        assert seen == [gm._arrow_head_px({"msize": "large"}, 0)]


class TestDefaultArrowSize:
    def test_falls_back_to_the_marker_size(self):
        sp = dr.GlyphMapper().scheme
        sp._props = dict(sp._props)
        sp._props.pop("symbolsize parrow", None)
        assert sp.default_arrow_size(3) == sp.default_marker_size(3)

    def test_reads_symbolsize_parrow(self):
        sp = dr.GlyphMapper().scheme
        sp._props = dict(sp._props, **{"symbolsize parrow": "large"})
        assert sp.default_arrow_size(0) == pytest.approx(
            sp._markersize_px("large"))


@requires_node
class TestTheHeadJs:
    def test_open(self):
        hpx = 6.0
        out = _run_heads(_rows_data(), hpx=hpx)
        assert out["row"] == [0, 1, 2, 3, 4]
        for i, (xs, ys) in enumerate(zip(out["xs"], out["ys"])):
            A, T, C = _px(xs, ys)
            y1, x1, y2, x2 = ROWS[i]
            (S,) = _px([x1], [y1])
            (E,) = _px([x2], [y2])
            assert T == pytest.approx(E)
            back = _sub(S, E)
            for P in (A, C):
                assert math.hypot(*_sub(P, T)) == pytest.approx(hpx)
                assert _angle(back, _sub(P, T)) == pytest.approx(28.64)

    def test_closed(self):
        hpx, barb = 6.0, 5.0
        out = _run_heads(_rows_data(), hpx=hpx, barb=barb)
        for i, (xs, ys) in enumerate(zip(out["xs"], out["ys"])):
            assert len(xs) == 4
            T, A, B, C = _px(xs, ys)
            y1, x1, y2, x2 = ROWS[i]
            (S,) = _px([x1], [y1])
            assert math.hypot(*_sub(B, T)) == pytest.approx(
                barb * math.cos(math.radians(28.64)))
            assert _angle(_sub(S, T), _sub(B, T)) == pytest.approx(0, abs=1e-6)

    def test_right_angle(self):
        """barbsize() = msize() puts B at the foot of the perpendicular
        from A: the right angle is at B (twoway measured 89.80 degrees at
        B, 61.53 at A; the plan's "at A" was the wrong vertex)."""
        assert TRUTH["heads"]["barb_msize"]["poly_angle_at_b"] == \
            pytest.approx(90, abs=0.5)
        out = _run_heads(_rows_data(), hpx=6.0, barb=6.0)
        for xs, ys in zip(out["xs"], out["ys"]):
            T, A, B, C = _px(xs, ys)
            assert _angle(_sub(A, B), _sub(T, B)) == pytest.approx(90, abs=0.5)

    def test_both_ends(self):
        out = _run_heads(_rows_data(), hpx=6.0, ends=2)
        assert out["row"] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
        for k, (xs, ys) in enumerate(zip(out["xs"], out["ys"])):
            y1, x1, y2, x2 = ROWS[k // 2]
            tip = (x2, y2) if k % 2 == 0 else (x1, y1)
            other = (x1, y1) if k % 2 == 0 else (x2, y2)
            A, T, C = _px(xs, ys)
            (Tw,) = _px([tip[0]], [tip[1]])
            (Ow,) = _px([other[0]], [other[1]])
            assert T == pytest.approx(Tw)
            assert _angle(_sub(Ow, Tw), _sub(A, T)) == pytest.approx(28.64)

    def test_skips_missing(self):
        d = _rows_data()
        d["y2"][2] = float("nan")
        out = _run_heads(d, hpx=6.0)
        assert out["row"] == [0, 1, 3, 4]

    def test_mangle_45(self):
        assert TRUTH["heads"]["mangle_45"]["half_angle"] == pytest.approx(45, abs=0.1)
        out = _run_heads(_rows_data(), hpx=6.0, ang=math.pi / 4)
        for i, (xs, ys) in enumerate(zip(out["xs"], out["ys"])):
            A, T, C = _px(xs, ys)
            y1, x1, y2, x2 = ROWS[i]
            (S,) = _px([x1], [y1])
            assert _angle(_sub(S, T), _sub(A, T)) == pytest.approx(45)

    @pytest.mark.parametrize("ptype", TYPES)
    def test_triggers(self, ptype):
        fig, _ = _draw(ptype)
        cb = _cb(fig)
        src = cb.args["src"]
        assert cb in src.js_property_callbacks["change:data"]
        assert dr._dash_arrow_head_hooks([fig]) == [cb]
        for rng in (fig.x_range, fig.y_range):
            for ev in ("change:start", "change:end"):
                assert rng.js_property_callbacks[ev].count(cb) == 1
        # The frame's size: a layout that moves the frame inside the same
        # canvas (the width scale's fonts and spacing, which the page now
        # lays out after document_ready) changes no range and no canvas
        # size, and the heads were left sized for the frame before it
        # (TestInChrome, 0.95 of the column).
        for ev in ("change:inner_width", "change:inner_height"):
            assert fig.js_property_callbacks[ev].count(cb) == 1
        # Wired once however often the page asks.
        dr._dash_arrow_head_hooks([fig])
        assert fig.x_range.js_property_callbacks["change:start"].count(cb) == 1
        assert fig.js_property_callbacks["change:inner_width"].count(cb) == 1
        assert "new ResizeObserver" in dr._DASH_ARROW_HEAD_JS
        assert cb.args["ends"] == _ENDS[ptype]


class TestTheScriptHoldsNoFigure:
    def test_no_figure_reaches_another(self, tmp_path):
        """The head script holds the head renderer, never the figure: a
        derived source the page's filter script lists carries it, so a
        figure there made every figure of a page reachable from every
        other (test_bare_intensity.py read other graphs' colours)."""
        from test_server_layer_defects import make_spec, plot_for, standalone
        spec = make_spec([plot_for("pcarrow")],
                         build_options={"filter": "foreign, type(dropdown)"})
        figs, _, _ = standalone(tmp_path, spec)
        for cb in _head_cbs(figs[0]):
            assert "fig" not in cb.args
            assert not [m for m in cb.references()
                        if hasattr(m, "x_range") and hasattr(m, "renderers")]


class TestBarbsize:
    @pytest.mark.parametrize("ptype", TYPES)
    def test_open_by_default(self, ptype):
        fig, _ = _draw(ptype)
        [r] = _head_renderers(fig)
        assert isinstance(r.glyph, MultiLine)
        assert _cb(fig).args["barb"] == 0.0

    @pytest.mark.parametrize("ptype", TYPES)
    def test_filled_when_positive(self, ptype):
        fig, gm = _draw(ptype, {"barbsize": "medium"})
        [r] = _head_renderers(fig)
        assert isinstance(r.glyph, Patches)
        assert r.glyph.fill_color == gm.scheme.default_color(0, "scatter")
        assert r.glyph.fill_color == TRUTH["heads"]["barb_medium"]["poly_fill"]
        assert _cb(fig).args["barb"] == pytest.approx(
            gm.tr.translate_msize("medium"))

    def test_zero_is_open(self):
        fig, _ = _draw("pcarrow", {"barbsize": "0"})
        [r] = _head_renderers(fig)
        assert isinstance(r.glyph, MultiLine)

    def test_a_negative_size_is_drawn_as_twoway_draws_it(self):
        """twoway takes barbsize(-1), rc 0 (fixture refusals.barb_neg): a
        polygon whose back point lies ahead of the tip."""
        assert TRUTH["refusals"]["barb_neg"]["rc"] == 0
        fig, _ = _draw("pcarrow", {"barbsize": "-1"})
        [r] = _head_renderers(fig)
        assert isinstance(r.glyph, Patches) and _cb(fig).args["barb"] < 0

    def test_an_unknown_name_is_noted_and_open(self, recwarn):
        assert TRUTH["refusals"]["barb_abc"]["rc"] == 0
        gm = dr.GlyphMapper()
        assert gm._arrow_barb({"barbsize": "abc"}, 6.0) == 0.0


class TestMangle:
    @pytest.mark.parametrize("ptype", TYPES)
    def test_angle_arg(self, ptype):
        fig, _ = _draw(ptype, {"mangle": "45"})
        assert _cb(fig).args["ang"] == pytest.approx(math.pi / 4)
        fig, _ = _draw(ptype)
        assert _cb(fig).args["ang"] == pytest.approx(math.radians(28.64))

    def test_names_and_any_number(self):
        gm = dr.GlyphMapper()
        assert gm._arrow_angle({"mangle": "forty_five"}) == \
            pytest.approx(math.pi / 4)
        # twoway takes mangle(400) (rc 0, fixture refusals.mangle_400).
        assert TRUTH["refusals"]["mangle_400"]["rc"] == 0
        assert gm._arrow_angle({"mangle": "400"}) == \
            pytest.approx(math.radians(400))
        assert gm._arrow_angle({"mangle": "abc"}) == \
            pytest.approx(math.radians(28.64))

    def test_is_written_not_pending(self):
        with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert "_dash_pending' mangle" not in ado
        assert "mangle barbsize headlabel" in ado

        assert "MANGle(string) BARBSize(string) HEADlabel" in ado


class TestHeadColours:
    def test_stroke(self):
        fig, _ = _draw("pcarrow", {"mcolor": "red"})
        [r] = _head_renderers(fig)
        assert r.glyph.line_color == "#ff0000"
        assert TRUTH["heads"]["mcolor"]["head_stroke_colours"] == ["#ff0000"]
        fig, _ = _draw("pcarrow", {"mcolor": "red", "mlcolor": "blue",
                                   "barbsize": "medium"})
        [r] = _head_renderers(fig)
        assert r.glyph.line_color == TRUTH["heads"]["colours"]["poly_stroke"]

    def test_fill(self):
        fig, _ = _draw("pcarrow", {"mcolor": "red", "mlcolor": "blue",
                                   "mfcolor": "green", "barbsize": "medium"})
        [r] = _head_renderers(fig)
        assert r.glyph.fill_color == TRUTH["heads"]["colours"]["poly_fill"]

    def test_width(self):
        fig, _ = _draw("pcarrow")
        [r0] = _head_renderers(fig)
        fig, _ = _draw("pcarrow", {"mlwidth": "thick"})
        [r1] = _head_renderers(fig)
        c = TRUTH["heads"]["colours"]
        want = c["poly_stroke_width_rs"] / c["shaft_width_rs"]
        assert r1.glyph.line_width / r0.glyph.line_width == \
            pytest.approx(want, rel=0.02)

    def test_line_options_are_the_shafts(self):
        """twoway's lcolor() and lwidth() draw the shaft alone (measured:
        under lcolor(red) lwidth(thick) the heads keep the series colour
        at 0.3 rs, the shaft 0.8 rs red; fixture heads.lcolor)."""
        t = TRUTH["heads"]["lcolor"]
        assert t["shaft_colour"] == "#ff0000"
        assert t["head_stroke_colours"] == ["#1a476f"]
        fig, gm = _draw("pcarrow", {"lcolor": "red", "lwidth": "thick"})
        [r] = _head_renderers(fig)
        assert r.glyph.line_color == gm.scheme.default_color(0, "pcarrow")
        assert r.glyph.line_width == gm.scheme.plot_line_width(0, "arrowline")

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_a_relative_lcolor_is_applied_once(self, ptype):
        """lcolor(*.5) is twoway's #8da3b7 on s2color's #1a476f shaft
        (test_bare_intensity.py P17); it was applied twice, #c6d1db,
        hidden while the head drew the once-applied colour."""
        fig, _ = _draw(ptype, {"lcolor": "*.5"})
        [seg] = [g for g in fig.renderers
                 if type(g.glyph).__name__ == "Segment"]
        assert seg.glyph.line_color == "#8da3b7"

    @pytest.mark.parametrize("ptype", TYPES)
    def test_nothing_is_black(self, ptype):
        for opts in ({}, {"barbsize": "medium"}):
            fig, gm = _draw(ptype, opts)
            [r] = _head_renderers(fig)
            [seg] = [g for g in fig.renderers
                     if type(g.glyph).__name__ == "Segment"]
            assert r.glyph.line_color == seg.glyph.line_color
            assert r.glyph.line_color not in ("black", "#000000")
            if isinstance(r.glyph, Patches):
                assert r.glyph.fill_color not in ("black", "#000000")


class TestHeadlabel:
    def _labels(self, ptype, opts):
        gm = dr.GlyphMapper()
        fig = figure()
        df = _df()
        df["lab"] = list("abcde")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            getattr(gm, "map_" + ptype)(fig, ColumnDataSource(df), "y1",
                                        "x1", "y2", "x2",
                                        dict(opts, mlabel="lab"))
        [ls] = [a for a in _mls_center(fig) if isinstance(a, _MLS)]
        return ls

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_at_the_head(self, ptype):
        assert TRUTH["headlabel"]["with"] == ["head"] * 5
        ls = self._labels(ptype, {"headlabel": "headlabel"})
        assert (ls.x.field if hasattr(ls.x, "field") else ls.x) == "x2"
        assert (ls.y.field if hasattr(ls.y, "field") else ls.y) == "y2"

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_at_the_tail_without(self, ptype):
        assert TRUTH["headlabel"]["without"] == ["tail"] * 5
        ls = self._labels(ptype, {})
        assert (ls.x.field if hasattr(ls.x, "field") else ls.x) == "x1"


class TestOnePointRows:
    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_as_twoway_draws(self, ptype):
        """twoway draws nothing for a row missing its second point."""
        op = TRUTH["onepoint"]
        assert op["markers"] == op["markers_all_present"] == 0
        assert op["shafts"] == op["shafts_all_present"] - 1
        rows = [list(r) for r in ROWS]
        rows[2][2] = float("nan")
        fig, _ = _draw(ptype, rows=rows)
        src = _cb(fig).args["src"]
        assert len(src.data["x1"]) == 4
        assert not [r for r in fig.renderers
                    if type(r.glyph).__name__ == "Scatter"]

    def test_first_point_missing_draws_nothing(self):
        rows = [list(r) for r in ROWS]
        rows[1][1] = float("nan")
        fig, _ = _draw("pcarrow", rows=rows)
        assert len(_cb(fig).args["src"].data["x1"]) == 4


def _head_src_after(spec, move, mode):
    if mode == "saved":
        import test_saved_filter_layers as sfl
        r = sfl._render(spec)
        sfl._move(r, move)
        cbs = []
        for f in r.figures.values():
            cbs += _head_cbs(f)
    else:
        import test_mode_parity as mp
        doc, _ = mp._served(spec)
        kind, want = move
        ws = [w for w in mp._widgets_of(doc) if type(w).__name__ == kind]
        w = ws[0]
        raw = [v for v, lab in w.options if lab == want]
        mp._fire(w, raw[0])
        cbs = []
        for root in doc.roots:
            cbs += _head_cbs(root)
    [cb] = {id(c): c for c in cbs}.values()
    return cb.args["src"]


class TestTheHeadHoldsAcrossAMove:
    """``pcarrow mpg weight price foreign, msize(large)`` moved to Foreign
    (5 rows): the shaft source the script reads keeps the head size on
    every kept row, in both modes."""

    def _spec(self):
        from test_mode_parity import _spec
        from test_server_layer_defects import plot_for
        return _spec([plot_for("pcarrow", {"msize": "large"})],
                     {"filter": "foreign, type(dropdown)"})

    @requires_node
    def test_saved(self):
        src = _head_src_after(self._spec(), ("Select", "Foreign"), "saved")
        want = dr.GlyphMapper()._arrow_head_px({"msize": "large"}, 0)
        assert list(src.data["__dash_head_px"]) == [want] * 5

    def test_served(self):
        src = _head_src_after(self._spec(), ("Select", "Foreign"), "served")
        want = dr.GlyphMapper()._arrow_head_px({"msize": "large"}, 0)
        assert list(src.data["__dash_head_px"]) == [want] * 5

    def test_an_empty_layer_keeps_the_column(self):
        rows = [[float("nan"), 1.0, 2.0, 2.0]]
        fig, _ = _draw("pcarrow", rows=rows)
        src = _cb(fig).args["src"]
        assert "__dash_head_px" in src.data and len(src.data["x1"]) == 0


class TestBothModesDrawTheSameHeads:
    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    def test_same_script_and_args(self, tmp_path, ptype):
        from test_server_layer_defects import (make_spec, plot_for, served,
                                               standalone)
        spec = make_spec([plot_for(ptype, {"barbsize": "medium",
                                           "mangle": "45"})])
        figs_s, _, _ = standalone(tmp_path, spec)
        figs_v, _, _ = served(tmp_path, spec)

        def sig(figs):
            out = []
            for f in figs:
                for cb in _head_cbs(f):
                    a = cb.args
                    out.append((cb.code, a["ends"], a["barb"], a["ang"],
                                a["hpx"], list(a["src"].data["__dash_head_px"]),
                                type(a["hr"].glyph).__name__,
                                a["hr"].glyph.fill_color,
                                a["hr"].glyph.line_color))
            return out
        assert sig(figs_s) and sig(figs_s) == sig(figs_v)


# ---------------------------------------------------------------------------
# The saved page in headless Chrome: the drawn strokes' length and angle
# ---------------------------------------------------------------------------

_CHROME_PROBE = r"""<script>
window.addEventListener('load', () => setTimeout(() => {
  const out = {heads: []};
  try {
    for (const doc of Bokeh.documents) {
      for (const m of doc._all_models.values()) {
        if (m.type !== 'CustomJS' || m.name !== 'dash_arrow_head') continue;
        const a = m.args, view = Bokeh.index.find_one(a.hr).plot_view;
        const xs = view.frame.x_scale, ys = view.frame.y_scale;
        const d = a.src.data, h = a.heads.data;
        out.heads.push({
          hpx: Array.from(d[a.hpx]),
          shafts: Array.from(d[a.x1], (_, i) => [
            xs.compute(d[a.x1][i]), ys.compute(d[a.y1][i]),
            xs.compute(d[a.x2][i]), ys.compute(d[a.y2][i])]),
          heads: h.xs.map((x, k) => x.map((v, j) =>
            [xs.compute(v), ys.compute(h.ys[k][j])])),
          row: Array.from(h.row)});
      }
    }
  } catch (e) { out.err = String(e); }
  const pre = document.createElement('pre'); pre.id = 'r';
  pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
}, 2500));
</script>"""


def chrome_heads(page_html, timeout=90):
    """What the saved page *page_html* draws for its arrowheads in
    headless Chrome, in screen pixels: per arrow layer ``hpx`` (the
    column), ``shafts`` ([X1, Y1, X2, Y2] per row), ``heads`` (each head's
    vertices) and ``row``.  Used by U02-01 too."""
    import html as _html
    import shutil
    import subprocess
    import time
    import responsive_probe as rp
    chrome = rp.find_chrome()
    if chrome is None:
        raise RuntimeError("no Chrome binary")
    work = tempfile.mkdtemp(prefix="dash_u02_")
    try:
        page = os.path.join(work, "page.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(rp.admit_script(page_html, _CHROME_PROBE))
        out = os.path.join(work, "out.html")
        prof = tempfile.mkdtemp(prefix="prof_", dir=work)
        cmd = rp.chrome_argv(chrome) + [
               "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--allow-file-access-from-files",
               "--user-data-dir=" + prof, "--window-size=1200,900",
               "--virtual-time-budget=9000", "--dump-dom", "file://" + page]
        with open(out, "w") as fo, open(os.devnull, "w") as fe:
            proc = subprocess.Popen(cmd, stdout=fo, stderr=fe)
            t0 = time.time()
            try:
                while time.time() - t0 < timeout:
                    time.sleep(0.3)
                    with open(out, encoding="utf-8", errors="replace") as fh:
                        if "</html>" in fh.read() or proc.poll() is not None:
                            break
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
        with open(out, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        m = re.search(r'<pre id="r">(.*?)</pre>', text, re.S)
        if not m:
            raise RuntimeError("the probe reported nothing")
        return json.loads(_html.unescape(m.group(1)))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def head_geometry(layer):
    """(stroke lengths / hpx, half-angles in degrees) of one layer's open
    heads as Chrome drew them."""
    ratios, halves = [], []
    for k, pts in enumerate(layer["heads"]):
        i = layer["row"][k]
        X1, Y1, X2, Y2 = layer["shafts"][i]
        A, T, C = pts
        tip_end = math.hypot(T[0] - X2, T[1] - Y2) < 1e-6
        back = (X1 - X2, Y1 - Y2) if tip_end else (X2 - X1, Y2 - Y1)
        for P in (A, C):
            ratios.append(math.hypot(P[0] - T[0], P[1] - T[1])
                          / layer["hpx"][i])
            halves.append(_angle(back, (P[0] - T[0], P[1] - T[1])))
    return ratios, halves


def _chrome_ok():
    try:
        import responsive_probe as rp
        return rp.find_chrome() is not None
    except ImportError:
        return False


@pytest.mark.skipif(not _chrome_ok(), reason="headless Chrome is not "
                    "installed (set DASH_CHROME); a skip is red under "
                    "DASH_STRICT=1")
class TestInChrome:
    def test_the_saved_page_draws_twoways_head(self, tmp_path):
        from test_server_layer_defects import make_spec, plot_for, standalone
        _, page, _ = standalone(tmp_path, make_spec([plot_for("pcbarrow")]))
        got = chrome_heads(page)
        assert not got.get("err"), got
        [layer] = got["heads"]
        assert len(layer["heads"]) == 2 * len(layer["shafts"])
        ratios, halves = head_geometry(layer)
        assert all(r == pytest.approx(1.0, rel=0.02) for r in ratios)
        assert all(h == pytest.approx(28.64, abs=0.5) for h in halves)
