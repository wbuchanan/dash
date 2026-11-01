"""
test_area_outline.py -- an area plot and its legend key are outlined all
round, as twoway outlines them (WP-34 PIC-1, RH-14; DECISIONS A-6).

The defect (audit PIC-1): twoway strokes the polygon an area fills -- its
top, its base and the two short edges that close it -- in the p#area line
style (colour p#arealine -> parealine -> p# -> p, width linewidth p#area),
and outlines the legend key.  dash drew no outline unless lcolor(),
lwidth(), lpattern() or a named line style asked for one, and then along
the top only; the key was a plain filled rectangle.

Truth: test/fixtures/area_outline_truth.json (scripts/
extract_area_outline_truth.do): the outline and fill colours of plots 1-3
in ten schemes, and the subpaths twoway strokes for `twoway area le_wm
year' (one closed subpath with base corners), the same with nodropbase
(one closed subpath, no base corners) and with cmissing(n) over a gap (two
closed subpaths with base corners).
"""
import itertools
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure as _Figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from dash_render import SchemeParser  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from js_runner import JsSession, requires_node  # noqa: E402
from test_mode_parity import (_DF, _LABEL_NAMES, _VALUE_LABELS,  # noqa: E402
                              _fire, _spec, _widgets_of)
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "area_outline_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_US = pd.DataFrame({"year": _T["data"]["year"],
                    "le_wm": _T["data"]["le_wm"]})
_US["le_x"] = _US["le_wm"] * 0.8
_US["g"] = (_US["year"] >= 1950).astype(float)
#: The gap probe: `replace le_wm = . in 40/45' (rows 39-44 from 0).
_GAP = _US.copy()
_GAP.loc[39:44, "le_wm"] = np.nan

_SCHEMES = sorted(_T["schemes"])
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_area_outline_")


def _area(options=None, yvar="le_wm"):
    return {"type": "area", "yvar": yvar, "xvar": "year",
            "options": dict(options or {})}


def _build(mode, spec, df=_US, labels=False):
    """(root model, document or renderer) of *spec* over *df*."""
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, _VALUE_LABELS, _LABEL_NAMES)
                  if labels else make_data_json(df), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = render_models(dr.DashRenderer(sp, dp))
            return r._last_layout_root, r
        from bokeh.document import Document
        ap = os.path.join(_TMP, "app_%d.py" % tag)
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_area_outline_app_%d" % tag, draw=False)
        doc = Document()
        mod.make_document(doc)
        return doc.roots[0], doc


def _figs(root):
    return sorted((m for m in root.references() if isinstance(m, _Figure)),
                  key=lambda f: f.id)


def _fig(mode, plots, scheme="stcolor", df=_US, go=None, bo=None):
    root, _ = _build(mode, _spec(plots, dict(bo or {}, scheme=scheme), go),
                     df)
    figs = _figs(root)
    assert len(figs) == 1, len(figs)
    return figs[0]


def _rings(fig):
    return [r for r in fig.renderers
            if "dash_area_outline" in (getattr(r, "tags", None) or [])]


def _fills(fig):
    return [r for r in fig.renderers
            if type(getattr(r, "glyph", None)).__name__
            in ("VArea", "HArea", "Patch")]


def _swatches(fig):
    return [r for r in fig.renderers if getattr(r, "_dash_key_glyph", False)]


def _xy(ring_r):
    d = ring_r.data_source.data
    g = ring_r.glyph
    return (np.asarray(d[g.x], dtype=float), np.asarray(d[g.y], dtype=float))


def _runs(xs, ys):
    """The NaN-separated runs of a ring, as lists of (x, y)."""
    out, cur = [], []
    for x, y in zip(xs, ys):
        if not (np.isfinite(x) and np.isfinite(y)):
            if cur:
                out.append(cur)
            cur = []
            continue
        cur.append((float(x), float(y)))
    if cur:
        out.append(cur)
    return out


def _shape(run):
    """The extractor's reading of a subpath: closed, and with a vertex at
    the lowest value at both its smallest and its largest x."""
    ys = [p[1] for p in run]
    xs = [p[0] for p in run]
    lo, xmin, xmax = min(ys), min(xs), max(xs)
    at = lambda x: any(abs(p[0] - x) < 1e-9 and abs(p[1] - lo) < 1e-9
                       for p in run)
    closed = run[0] == run[-1]
    return {"closed": closed, "base_corners": bool(at(xmin) and at(xmax))}


# ---------------------------------------------------------------------------
# The style chain
# ---------------------------------------------------------------------------

class TestTheStyle:
    @pytest.mark.parametrize("scheme", _SCHEMES)
    def test_matches_twoway(self, scheme):
        sp = SchemeParser(scheme)
        for k, want in enumerate(_T["schemes"][scheme]):
            st = sp.area_line_style(k)
            assert st["line"].lower() == want["line"], (scheme, k, st)
            assert st["line_width"] == sp.plot_line_width(k, "area")
            assert isinstance(st["line_dash"], list)


# ---------------------------------------------------------------------------
# The ring helper and its script
# ---------------------------------------------------------------------------

_NAN = float("nan")


def _same(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return a.shape == b.shape and bool(np.array_equal(a, b, equal_nan=True))


class TestTheRing:
    def test_the_helper(self):
        ring = dr._dash_area_ring
        x, y = ring([1, 2, 3], [0, 0, 0], [5, 6, 7])
        assert _same(x, [1, 2, 3, 3, 2, 1, 1])
        assert _same(y, [5, 6, 7, 0, 0, 0, 5])
        # A NaN row splits the run.
        x, y = ring([1, 2, 3, 4], [0, 0, 0, 0], [5, _NAN, 7, 8])
        assert _same(x, [1, 1, 1, _NAN, 3, 4, 4, 3, 3])
        assert _same(y, [5, 0, 5, _NAN, 7, 8, 0, 0, 7])
        # breaks split it too (map_area's zero-height gap vertices).
        x, y = ring([1, 2, 3, 4], [0, 0, 0, 0], [5, 6, 7, 8],
                    breaks=[False, True, True, False])
        assert _same(x, [1, 1, 1, _NAN, 4, 4, 4])
        assert _same(y, [5, 0, 5, _NAN, 8, 0, 8])
        # nodropbase: the tops and the closing chord.
        x, y = ring([1, 2, 3], None, [5, 6, 7], drop=False)
        assert _same(x, [1, 2, 3, 1]) and _same(y, [5, 6, 7, 5])
        # A one-row run and no rows.
        x, y = ring([1], [0], [5])
        assert _same(x, [1, 1, 1]) and _same(y, [5, 0, 5])
        x, y = ring([], [], [])
        assert len(x) == 0 and len(y) == 0

    @requires_node
    def test_js_twin(self):
        xs = [1.0, 2.0, 2.0, 4.0, 4.0, 5.0, 6.0]
        b = [0.0] * 7
        t = [5.0, 6.0, 6.0, 7.0, 7.0, _NAN, 9.0]
        rid = [0, 1, None, None, 3, 4, 5]
        brk = [v is None for v in rid]
        cases = [
            (dict(rid=dr._ROW_ID_COLUMN, pins=[]),
             {dr._ROW_ID_COLUMN: rid}, dr._dash_area_ring(xs, b, t, brk)),
            (dict(rid="", pins=[2, 3]), {},
             dr._dash_area_ring(xs, b, t, brk)),
            (dict(rid="", pins=[]), {}, dr._dash_area_ring(xs, b, t, None)),
            (dict(rid="", pins=[], y1=""), {},
             dr._dash_area_ring(xs, None, t, None, drop=False)),
        ]
        for kw, extra, (wx, wy) in cases:
            src = ColumnDataSource(dict({"x": xs, "b": b, "t": t}, **extra))
            ring = ColumnDataSource({"x": [], "t": []})
            args = dict(src=src, ring=ring, x="x", y1="b", y2="t")
            args.update(kw)
            JsSession([]).run_code(dr._DASH_AREA_RING_JS, args)
            assert _same(ring.data["x"], wx), (kw, ring.data["x"], wx)
            assert _same(ring.data["t"], wy), (kw, ring.data["t"], wy)
        # A row-id column the source lacks: nothing is written.
        src = ColumnDataSource({"x": xs, "b": b, "t": t})
        ring = ColumnDataSource({"x": [9.0], "t": [9.0]})
        JsSession([]).run_code(dr._DASH_AREA_RING_JS, dict(
            src=src, ring=ring, x="x", y1="b", y2="t",
            rid=dr._ROW_ID_COLUMN, pins=[]))
        assert list(ring.data["x"]) == [9.0]

    def test_the_finish_rewrites_the_ring(self):
        fig = _fig("saved", [_area()])
        (fill,) = _fills(fig)
        (ring_r,) = _rings(fig)
        assert "y" in dr._dash_auto_base_props(ring_r, "y")
        assert "x" in dr._dash_auto_base_props(ring_r, "x")
        d = fill.data_source.data
        want = dr._dash_area_ring(d["year"], d["le_wm_base"], d["le_wm"])
        # A provisional base and a stale ring: the finish rewrites both.
        d["le_wm_base"] = np.full(len(d["le_wm"]), -5.0)
        ring_r.data_source.data = {"year": [0.0], "le_wm": [0.0]}
        assert dr._dash_finish_auto_bases(fig) >= 1
        assert dr._dash_area_ring_write(fill) is True
        got = _xy(ring_r)
        assert _same(got[0], want[0]) and _same(got[1], want[1])


# ---------------------------------------------------------------------------
# The outline drawn
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestTheOutline:
    @pytest.mark.parametrize("scheme", _SCHEMES)
    def test_default_outline(self, mode, scheme):
        fig = _fig(mode, [_area()], scheme)
        lines = [r for r in fig.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"]
        rings = _rings(fig)
        assert len(rings) == 1 and lines == rings, fig.renderers
        st = SchemeParser(scheme).area_line_style(0)
        g = rings[0].glyph
        assert g.line_color.lower() == st["line"].lower() \
            == _T["schemes"][scheme][0]["line"]
        assert g.line_width == st["line_width"]
        assert list(g.line_dash) == list(st["line_dash"])

    @pytest.mark.parametrize("probe", ["plain", "gap", "nodrop"])
    def test_ring_matches_twoway(self, mode, probe):
        opts = {"plain": {}, "gap": {"cmissing": "n"},
                "nodrop": {"nodropbase": "nodropbase"}}[probe]
        fig = _fig(mode, [_area(opts)], df=_GAP if probe == "gap" else _US)
        (ring_r,) = _rings(fig)
        runs = _runs(*_xy(ring_r))
        assert [_shape(r) for r in runs] == _T["paths"][probe], runs

    def test_restyle(self, mode):
        tr = dr.OptionTranslator.translate_lwidth
        cases = [({"lcolor": "red"}, "line_color", "#ff0000"),
                 ({"lwidth": "thick"}, "line_width", tr("thick")),
                 ({"lpattern": "dash"}, "line_dash", [8, 4]),
                 ({"color": "green"}, "line_color", None),
                 ({"lstyle": "p3"}, "line_color", "#00bf7f")]
        for opts, attr, want in cases:
            fig = _fig(mode, [_area(opts)])
            (ring_r,) = _rings(fig)
            got = getattr(ring_r.glyph, attr)
            if want is None:
                # color() sets the outline too (twoway): the fill's colour.
                want = dr.OptionTranslator().parse_color_alpha("green", "color")[0]
            got = list(got) if isinstance(got, (list, tuple)) else got
            assert got == want, (opts, got, want)

    def test_gap_and_move(self, mode):
        spec = _spec([_area({"cmissing": "n"})],
                     {"scheme": "stcolor",
                      "filter": "year, type(range)"})
        root, owner = _build(mode, spec, _GAP)
        if mode == "saved":
            ws = [w for w in owner.filter_widgets
                  if type(w).__name__ == "RangeSlider"]
            w = ws[0]
            w.value = (1920.0, 1990.0)
            cb = owner.filter_callbacks[owner.filter_widgets.index(w)]
            JsSession([]).run_code(cb.code, cb.args)
        else:
            (w,) = [w for w in _widgets_of(owner)
                    if type(w).__name__ == "RangeSlider"]
            _fire(w, (1920.0, 1990.0))
        (fig,) = _figs(root)
        (fill,) = _fills(fig)
        (ring_r,) = _rings(fig)
        if mode == "saved":
            # The browser runs the fill source's ring script on the
            # assignment; the node harness runs the filter alone.
            for cb in fill.data_source.js_property_callbacks.get(
                    "change:data", []):
                if getattr(cb, "name", "") == "dash_area_ring":
                    JsSession([]).run_code(cb.code, cb.args)
        d = fill.data_source.data
        xs = np.asarray(d["year"], dtype=float)
        ok = np.isfinite(xs)
        assert 1920 <= np.nanmin(xs[ok]) and np.nanmax(xs[ok]) <= 1990
        runs = _runs(*_xy(ring_r))
        # Rows 40-45 (1939-1944) are missing: two runs, each closed with
        # its base corners, the base the finished base.
        assert [_shape(r) for r in runs] == _T["paths"]["gap"], runs
        base = float(np.nanmin(np.asarray(d["le_wm_base"], dtype=float)))
        for r in runs:
            assert min(p[1] for p in r) == pytest.approx(base)
            assert min(p[0] for p in r) >= 1920
            assert max(p[0] for p in r) <= 1990

    def test_nodropbase(self, mode):
        fig = _fig(mode, [_area({"nodropbase": "nodropbase"})])
        (fill,) = _fills(fig)
        assert type(fill.glyph).__name__ == "Patch"
        (ring_r,) = _rings(fig)
        x, y = _xy(ring_r)
        d = fill.data_source.data
        wx = list(d["year"]) + [d["year"][0]]
        wy = list(d["le_wm"]) + [d["le_wm"][0]]
        assert _same(x, wx) and _same(y, wy)

    def test_recast_area(self, mode):
        # RH-14: a fit drawn as an area (qfit, recast(area)) is outlined.
        fig = _fig(mode, [{"type": "qfit", "yvar": "le_wm", "xvar": "year",
                           "options": {"recast": "area"}}])
        (ring_r,) = _rings(fig)
        assert ring_r.glyph.line_color.lower() == _T["schemes"]["stcolor"][
            0]["line"]
        assert [_shape(r) for r in _runs(*_xy(ring_r))] == \
            _T["paths"]["plain"]

    def test_no_hover_on_the_ring(self, mode):
        for plots, df in (([_area()], _US),
                          ([_area({"cmissing": "n"})], _GAP),
                          ([{"type": "qfit", "yvar": "le_wm",
                             "xvar": "year",
                             "options": {"recast": "area"}}], _US)):
            fig = _fig(mode, plots, df=df)
            (ring_r,) = _rings(fig)
            (fill,) = _fills(fig)
            hovered = [r for t in fig.tools if isinstance(t, HoverTool)
                       for r in (t.renderers if isinstance(t.renderers, list)
                                 else [])]
            assert ring_r not in hovered
            assert fill in hovered

    def test_horizontal(self, mode):
        fig = _fig(mode, [_area({"horizontal": "horizontal"})])
        (fill,) = _fills(fig)
        assert type(fill.glyph).__name__ == "HArea"
        (ring_r,) = _rings(fig)
        g = ring_r.glyph
        # Turned with the fill: x reads the values, y the year.
        assert g.y == fill.glyph.y and g.x == fill.glyph.x2, (g.x, g.y)
        runs = _runs(*_xy(ring_r))
        assert len(runs) == 1 and runs[0][0] == runs[0][-1]

    def test_no_tick_input(self, mode):
        fig = _fig(mode, [_area()])
        # The ticks and span of today's tree (measured at cd6aa39).
        assert list(fig.yaxis[0].ticker.ticks) == [40.0, 50.0, 60.0, 70.0,
                                                   80.0]
        assert fig.y_range.start == pytest.approx(36.11275946025105)
        assert fig.y_range.end == pytest.approx(80.98723853974896)
        (fill,) = _fills(fig)
        (ring_r,) = _rings(fig)
        for attr in ("x_range_name", "y_range_name"):
            assert dr._dash_layer_extent([fill, ring_r], attr, "default") \
                == dr._dash_layer_extent([fill], attr, "default")

    def test_recast_area_after_a_move(self, mode):
        """kdensity mpg, recast(area) range(10 45) under a range move: the
        fill alone is the recount target, and the ring follows the
        recounted fill (the saved page through the fill source's script,
        the served app through its redraw)."""
        from test_saved_filter_layers import _MOVES as _SMOVES
        mv = _SMOVES[1]
        spec = _spec([plot_for("kdensity", {"recast": "area",
                                            "range": "10 45"})],
                     {"filter": mv[1]})
        root, owner = _build(mode, spec, _DF, labels=True)
        (fig,) = _figs(root)
        (fill,) = [g for g in _fills(fig)
                   if getattr(g, "_dash_area_ring", None) is not None]
        (ring_r,) = _rings(fig)
        (sw,) = _swatches(fig)
        if mode == "saved":
            assert getattr(fill, "_dash_agg_config", None) is not None
        assert getattr(ring_r, "_dash_agg_config", None) is None
        assert getattr(sw, "_dash_agg_config", None) is None
        before = list(fill.data_source.data["y"])
        if mode == "saved":
            from test_saved_filter_layers import _move, _run
            _move(owner, mv[2])
            (cb,) = [c for c in fill.data_source.js_property_callbacks[
                "change:data"] if getattr(c, "name", "") == "dash_area_ring"]
            _run(cb.code, cb.args)
        else:
            (w,) = [w for w in _widgets_of(owner)
                    if type(w).__name__ == mv[2][0]]
            _fire(w, mv[2][1])
            (fig,) = _figs(root)
            (fill,) = [g for g in _fills(fig)
                       if getattr(g, "_dash_area_ring", None) is not None]
            (ring_r,) = _rings(fig)
        d = fill.data_source.data
        assert not _same(d["y"], before)
        wx, wy = dr._dash_area_ring(d["x"], d["y_base"], d["y"], None)
        got = ring_r.data_source.data
        assert _same(got["x"], wx) and _same(got["y"], wy)


# ---------------------------------------------------------------------------
# The legend key
# ---------------------------------------------------------------------------

def _legends(root):
    return [m for m in root.references() if isinstance(m, Legend)]


def _key_renderers(root):
    return [[r for r in it.renderers] for lg in _legends(root)
            for it in lg.items]


@pytest.mark.parametrize("mode", _MODES)
class TestTheKey:
    def test_key_is_outlined(self, mode):
        root, _ = _build(mode, _spec([_area(), _area(yvar="le_x")],
                                     {"scheme": "stcolor"}))
        (fig,) = _figs(root)
        sws = _swatches(fig)
        assert len(sws) == 2
        keys = _key_renderers(root)
        assert keys == [[sws[0]], [sws[1]]], keys
        fills, rings = _fills(fig), _rings(fig)
        for sw, fill, ring_r in zip(sws, fills, rings):
            assert type(sw.glyph).__name__ == "Quad"
            assert sw.glyph.fill_color == fill.glyph.fill_color
            assert sw.glyph.line_color == ring_r.glyph.line_color
            assert sw.glyph.line_width == ring_r.glyph.line_width

    def test_order_and_by(self, mode):
        root, _ = _build(mode, _spec([_area(), _area(yvar="le_x")],
                                     {"scheme": "stcolor"},
                                     {"legend": "order(2 1)"}))
        (fig,) = _figs(root)
        sws = _swatches(fig)
        assert _key_renderers(root) == [[sws[1]], [sws[0]]]
        root, _ = _build(mode, _spec([_area(), _area(yvar="le_x")],
                                     {"scheme": "stcolor"}, {"by": "g"}))
        panels = [f for f in _figs(root) if _fills(f)]
        assert len(panels) == 2
        (lg,) = [g for g in _legends(root) if g.visible]
        for k, item in enumerate(lg.items):
            want = {_swatches(f)[k].id for f in panels}
            got = {r.id for r in item.renderers
                   if not r.name.startswith("_clegend_by_")}
            assert got == want, (k, got, want)
            # by()'s own key glyph is a clone of the outlined swatch.
            (clone,) = [r for r in item.renderers
                        if r.name.startswith("_clegend_by_")]
            assert clone.glyph.line_color == \
                _swatches(panels[0])[k].glyph.line_color

    def test_click_hides_the_area(self, mode):
        root, _ = _build(mode, _spec([_area(), _area(yvar="le_x")],
                                     {"scheme": "stcolor"}, {"by": "g"}))
        panels = [f for f in _figs(root) if _fills(f)]
        assert len(panels) == 2
        (lg,) = [g for g in _legends(root) if g.visible]
        assert lg.click_policy == "hide"
        for k, item in enumerate(lg.items):
            for f in panels:
                sw = _swatches(f)[k]
                assert sw in item.renderers
                targets = {cb.args.get("other").id for cb in
                           sw.js_property_callbacks.get("change:visible", [])
                           if cb.args.get("other") is not None}
                assert targets == {_fills(f)[k].id, _rings(f)[k].id}
        # A plain legend stays static.
        root, _ = _build(mode, _spec([_area(), _area(yvar="le_x")],
                                     {"scheme": "stcolor"}))
        (lg,) = [g for g in _legends(root) if g.visible]
        assert lg.click_policy == "none"

    def test_colorvar_swatch(self, mode):
        plain = _fig(mode, [_area()])
        cv = _fig(mode, [_area({"colorvar": "le_x"})])
        (a,) = _swatches(plain)
        (b,) = _swatches(cv)
        for attr in ("fill_color", "line_color"):
            assert isinstance(getattr(b.glyph, attr), str)
            assert getattr(b.glyph, attr) == getattr(a.glyph, attr)
        (ra,) = _rings(plain)
        (rb,) = _rings(cv)
        assert rb.glyph.line_color == ra.glyph.line_color \
            == SchemeParser("stcolor").area_line_style(0)["line"]

    def test_ci_fitplot_area(self, mode):
        def keys(opts):
            root, _ = _build(mode, _spec([plot_for("lfitci", opts)]),
                             _DF, labels=True)
            (fig,) = _figs(root)
            out = [(it, list(it.renderers)) for lg in _legends(root)
                   for it in lg.items]
            return fig, out

        fig, out = keys({"fitplot": "area"})
        assert len(out) == 2, out
        band, fit = out[0][1], out[1][1]
        # The band's own VArea and outline (no swatch, no area ring).
        assert "VArea" in [type(r.glyph).__name__ for r in band]
        assert not any(getattr(r, "_dash_area_ring", None)
                       or getattr(r, "_dash_key_glyph", False)
                       or "dash_area_outline" in (r.tags or [])
                       for r in band)
        assert len(fit) == 1 and getattr(fit[0], "_dash_key_glyph", False)
        fig, out = keys({"ciplot": "area"})
        assert len(out) == 2, out
        band, fit = out[0][1], out[1][1]
        assert len(band) == 1 and getattr(band[0], "_dash_key_glyph", False)
        assert getattr(band[0], "_dash_ci_band", False)
        assert all(type(r.glyph).__name__ == "Line" for r in fit)
        fig, out = keys({"fitplot": "area", "nofit": "nofit"})
        assert len(out) == 1, out


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

_HELP = os.path.join(_HERE, "..", "dash.sthlp")


def _flat():
    with open(_HELP, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


class TestTheHelp:
    def test_sentences(self):
        text = _flat()
        assert ("An {cmd:area} is outlined whole, as {cmd:twoway} strokes "
                "its polygon: along its top, its base and the two short "
                "edges at its first and last points (under "
                "{cmd:nodropbase}, along the chord that closes it), in the "
                "scheme's area line colour, width and pattern, which "
                "{cmd:color()}, {cmd:lcolor()}, {cmd:lwidth()}, "
                "{cmd:lpattern()} and the named line styles restyle; a "
                "{cmd:cmissing(n)} gap breaks it where it breaks the fill, "
                "and its legend key is the outlined fill.") in text
        assert ("an area's outline width ({cmd:linewidth pbar} and "
                "{cmd:linewidth parea}; an area is outlined by default, as "
                "{cmd:twoway} outlines it)") in text
