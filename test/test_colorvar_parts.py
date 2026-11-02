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
