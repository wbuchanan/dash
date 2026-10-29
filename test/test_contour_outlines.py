"""
test_contour_outlines.py -- contour's outlines and heatmap options reach
the renderer and are drawn as twoway draws them (WP-37 TR-13a, ruling
D64).

The defect (found by 37-03): _dash_parse_plot_opts kept outlines and
heatmap as s(_outlines) and s(_heatmap), and _dash_plot_opts_to_json's
key list wrote neither, so a real dash command drew neither; and WP-32's
outlines drawing stroked the bands' boundaries black in the plot.

Measured (test/fixtures/contour_outlines_truth.json,
scripts/extract_contour_outlines_truth.do, graph export SVG under
stcolor): under outlines twoway draws the plot region exactly as without
it -- no black stroke inside it, on sandstone (a full grid, drawn from
twoway's generator), on auto's scattered points (dash's own fit), with
ccuts(), interp(none) and heatmap -- and outlines each box of the colour
key in black at 19.44 SVG units (twice a medium line, clipped to the box)
where each box is otherwise stroked in its own colour at 6.00 (17.28
under s2color: twice its medium line).  heatmap
fills one rectangle per grid node (6,400 on sandstone's 80 x 80 grid, 25
on a 5 x 5 grid) and leaves the key as it is.  contourline takes both
and draws nothing different.  alpattern()'s boundary lines are the same
with outlines.

test_wp37_truth.cscript S06 (Q3706-1..5) checks the Stata side live.
"""
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_contour_gen as cg  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from js_runner import requires_node  # noqa: E402

_ADO = open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8").read()
_FIX = os.path.join(_HERE, "fixtures", "contour_outlines_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("std", "srv")
_MED = float(dr.OptionTranslator.translate_lwidth("medium"))


def _program(name):
    m = re.search(r"^program define " + name + r"\b.*?^end\b", _ADO,
                  re.S | re.M)
    assert m, name
    return m.group(0)


def _scatter_df(n=60):
    """Scattered points: dash fits the surface itself."""
    rng = np.random.default_rng(20261029)
    df = pd.DataFrame({"x": rng.uniform(0, 10, n), "y": rng.uniform(0, 10, n)})
    df["z"] = np.sin(df["x"] / 2) + np.cos(df["y"] / 3)
    df["half"] = (df["y"] >= 5).astype(float)
    return df


def _layer(kind, opts=None):
    """(plot, df) of a contour layer drawn from Stata's polygons ("grid",
    37-03's route) or from dash's own fit ("fit")."""
    o = dict(opts or {})
    if kind == "grid" and not o.get("heatmap"):
        o["contour_gen"] = cg._obj("grid40")
        return cg._plot("contour", o), cg._grid_df()
    return cg._plot("contour", o), (_scatter_df() if kind == "fit"
                                    else cg._grid_df())


def _bars(fig):
    return [m for side in (fig.right, fig.left, fig.above, fig.below,
                           fig.center) for m in side
            if type(m).__name__ == "ContourColorBar"]


def _draw(mode, plot, df):
    figs, msgs = cg._figs_msgs(mode, tp._spec([plot]), df)
    [fig] = figs
    return fig, msgs


def _fill(fig):
    [cr] = cg._crs(fig)
    return cr.fill_renderer.data_source.data


def _key_outlined(bar):
    """True when the bar is outlined black at a medium line and its line
    renderer strokes every level black at a medium line."""
    lr = bar.line_renderer
    g = lr.glyph
    n = len(lr.data_source.data.get("xs", []))
    return (bar.bar_line_color == "#000000"
            and abs(float(bar.bar_line_width) - _MED) < 1e-9
            and n == len(bar.levels)
            and g.line_color == "#000000"
            and abs(float(g.line_width) - _MED) < 1e-9)


class TestTheSpecCarriesThem:
    """The real ado path: the parser returns both in s() under their own
    names and the options writer lists them (s(_heatmap) and s(_outlines)
    were skipped by the writer and by test_mlabvposition's check of it)."""

    def test_the_parser_returns_them_by_name(self):
        body = _program("_dash_parse_plot_opts")
        for o in ("heatmap", "outlines"):
            assert re.search(r"sreturn local %s\b" % o, body), o
            assert not re.search(r"sreturn local _%s\b" % o, body), o

    def test_the_writer_lists_them(self):
        body = _program("_dash_plot_opts_to_json")
        keys = body.split("foreach key in", 1)[1].split("{", 1)[0]
        words = set(re.findall(r"[a-z0-9_]+", keys))
        assert {"heatmap", "outlines"} <= words

    def test_the_contour_check_reads_them_by_name(self):
        body = _program("_dash_contour_check")
        assert "_heatmap" not in body and "_outlines" not in body


class TestTheFixture:

    def test_meta(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "scheme", "source",
                                       "stata_version"]
        assert _T["_meta"]["source"] == \
            "scripts/extract_contour_outlines_truth.do"
        probes = [k for k in _T if k != "_meta"]
        assert len(probes) == 28
        assert all(_T[k]["rc"] == 0 for k in probes)

    @pytest.mark.parametrize("plain,outl", [
        ("ss.default", "ss.outlines"), ("ss.ccuts", "ss.outlines_ccuts"),
        ("ss.none", "ss.outlines_none"), ("ss.heatmap", "ss.outlines_heatmap"),
        ("au.default", "au.outlines"), ("au.none", "au.outlines_none"),
        ("g5.default", "g5.outlines"),
        ("ss.alpattern", "ss.outlines_alpattern"),
        ("s2.default", "s2.outlines")])
    def test_outlines_leaves_the_plot_and_outlines_the_key(self, plain, outl):
        """Twice the scheme's medium line: 19.44 SVG units under stcolor
        (medium 9.72), 17.28 under s2color (8.64)."""
        width = 17.28 if plain.startswith("s2.") else 19.44
        p, o = _T[plain], _T[outl]
        assert outl in p["same_plot_as"]
        assert o["plot_black_strokes"] == 0
        assert len(o["key_boxes"]) == len(p["key_boxes"]) == len(p["cuts"]) + 1
        for a, b in zip(p["key_boxes"], o["key_boxes"]):
            assert a["fill"] == b["fill"]
            assert (a["stroke"], a["stroke_width"]) == (a["fill"], 6.0)
            assert (b["stroke"], b["stroke_width"]) == ("#000000", width)

    @pytest.mark.parametrize("key,rects", [("ss.heatmap", 6400),
                                           ("g5.heatmap", 25)])
    def test_heatmap_is_a_cell_per_node_and_keeps_the_key(self, key, rects):
        h = _T[key]
        assert h["plot_filled_rects"] == rects
        assert h["malformed"] == 0
        assert all(b["stroke"] == b["fill"] for b in h["key_boxes"])

    @pytest.mark.parametrize("ds", ["ss", "au"])
    def test_contourline_takes_both_and_draws_nothing_new(self, ds):
        assert sorted(_T[ds + ".line"]["same_plot_as"]) == [
            ds + ".line_heatmap", ds + ".line_outlines"]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("kind", ["grid", "fit"])
class TestTheDrawing:

    def test_outlines_draws_the_plot_as_without_it(self, mode, kind):
        plot, df = _layer(kind)
        fig0, _ = _draw(mode, plot, df)
        plot, df = _layer(kind, {"outlines": "outlines"})
        fig1, msgs = _draw(mode, plot, df)
        assert not cg._crs(fig1, "dash_contour_lines")
        cg._same_data(_fill(fig1), _fill(fig0))
        assert not [m for m in msgs if "outlines" in m]

    def test_outlines_outlines_the_keys_boxes(self, mode, kind):
        plot, df = _layer(kind, {"outlines": "outlines"})
        fig, _ = _draw(mode, plot, df)
        [bar] = _bars(fig)
        assert _key_outlined(bar)
        plot, df = _layer(kind)
        fig, _ = _draw(mode, plot, df)
        [bar] = _bars(fig)
        assert not _key_outlined(bar)
        assert bar.bar_line_color is None

    def test_heatmap_keeps_the_key(self, mode, kind):
        for opts, outlined in (({"heatmap": "heatmap"}, False),
                               ({"heatmap": "heatmap",
                                 "outlines": "outlines"}, True)):
            plot, df = _layer(kind, opts)
            fig, msgs = _draw(mode, plot, df)
            heat = [r for r in fig.renderers
                    if "dash_contour_heat" in (r.tags or [])]
            assert len(heat) == 1 and len(heat[0].data_source.data["left"])
            [bar] = _bars(fig)
            assert _key_outlined(bar) is outlined
            assert not cg._crs(fig, "dash_contour_lines")
            assert not [m for m in msgs if "heatmap" in m]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("opt", ["outlines", "heatmap"])
def test_contourline_draws_the_same_lines(mode, opt):
    """contourline takes outlines and heatmap and draws its lines as
    without them, from Stata's polygons on a grid (no fallback note)."""
    df = cg._grid_df()
    line = cg._obj("grid40.line")
    base = cg._plot("contourline", {"contour_gen": line})
    with_ = cg._plot("contourline", {"contour_gen": line, opt: opt})
    fig0, _ = _draw(mode, base, df)
    fig1, msgs = _draw(mode, with_, df)
    [a], [b] = cg._crs(fig0), cg._crs(fig1)
    cg._same_data(b.line_renderer.data_source.data,
                  a.line_renderer.data_source.data)
    assert len(fig1.renderers) == len(fig0.renderers)
    assert not [m for m in msgs if "cannot be read" in m or opt in m]
    assert not _bars(fig1)


def test_a_line_object_is_read_under_heatmap():
    """contourline's generator object is read with heatmap set: twoway's
    contourline ignores heatmap."""
    line = cg._obj("grid40.line")
    assert dr._dash_contour_gen_of({"contour_gen": line,
                                    "heatmap": "heatmap"}) is line


def test_the_bar_follow_resizes_the_key_lines():
    """After a move the outlined key strokes every level it now has."""
    from bokeh.plotting import figure
    plot, df = _layer("fit", {"outlines": "outlines"})
    fig, _ = _draw("std", plot, df)
    [bar] = _bars(fig)
    lv = list(bar.levels)
    dr._dash_contour_bar_follow(bar, [lv[0], lv[1], lv[-1]], [], {})
    assert len(bar.levels) == 3
    assert len(bar.line_renderer.data_source.data["xs"]) == 3
    assert _key_outlined(bar)
    # A bar with no outlined key keeps its line renderer as it is.
    f2 = figure()
    cr = f2.contour(x=[[0, 1], [0, 1]], y=[[0, 0], [1, 1]],
                    z=[[0, 1], [1, 2]], levels=[0, 1, 2],
                    fill_color=["#ff0000", "#0000ff"])
    b2 = cr.construct_color_bar()
    dr._dash_contour_bar_follow(b2, [0, 0.5, 1.5, 2], [], {})
    assert len(b2.line_renderer.data_source.data["xs"]) == 0


@requires_node
def test_the_saved_page_moves_the_outlined_key():
    """The saved page's move keeps the outlined key's lines one per level
    (BokehJS paints no key otherwise: "Inconsistent number of line
    contour levels")."""
    df = _scatter_df(80)
    spec = tp._spec([cg._plot("contour", {"outlines": "outlines"})],
                    {"filter": "half, type(dropdown)"})
    r, figs = hm._saved_moved(spec, ("Select", "1"), df)
    [bar] = _bars(figs[0])
    assert _key_outlined(bar)
    assert not cg._crs(figs[0], "dash_contour_lines")
