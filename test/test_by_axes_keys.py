"""
test_by_axes_keys.py -- by() panels share their axes, titles, legend and
colour key as twoway's do, and each panel label sits in twoway's filled
box (WP-30 P1.15c).

dash drew both axes, both axis titles, a legend and a colour key on every
by() panel, named legend(), clegend(), the i* words, edgelabel,
individual and ilegends as ignored, and drew each panel label as plain
text.  The truth is test/fixtures/by_chrome_truth.json
(scripts/extract_by_chrome_truth.do): per probe, twoway's graph object --
which panels draw which axes, axis titles and legends, the overall legend
and colour key and their side, and the style switches its words set --
and, per scheme, the box twoway draws behind each panel label, read from
its SVG export.  Each measured fixture is checked by one test per mode
that loops over every row and reports every mismatch.
"""

import copy
import itertools
import json
import os
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, render_models  # noqa: E402
import test_by_grid as tg  # noqa: E402
import test_by_text as tbt  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from by_panel_probe import (by_grid, panel_label,  # noqa: E402
                            panel_label_title, side_title)

_FIXTURE = os.path.join(_HERE, "fixtures", "by_chrome_truth.json")
_SCHEME_FIXTURE = os.path.join(_HERE, "fixtures", "scheme_truth.json")
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_axes_keys_")
_FIX = None
_BUILT = {}


def _fix():
    global _FIX
    if _FIX is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _FIX = json.load(fh)
    return _FIX


def _p(ptype, y="mpg", x="weight", **opts):
    return {"type": ptype, "yvar": y, "xvar": x, "options": dict(opts)}


_ONE = [_p("scatter")]
_TWO = [_p("scatter"), _p("lfit")]
# headroom stands in for twoway's price on the second axis and in the
# colour key: the probes read which panels draw, not the values.
_DUAL = [_p("scatter"), _p("scatter", y="headroom", yaxis="2")]

#: dash's spelling of each fixture chrome probe: (plots, graph options).
_PROBES = {
    "p01": (_ONE, {"by": "foreign"}),
    "p02": (_TWO, {"by": "foreign"}),
    "p02_s2": (_TWO, {"by": "foreign", "scheme": "s2color"}),
    "p02_ec": (_TWO, {"by": "foreign", "scheme": "economist"}),
    "p03": (_TWO, {"by": "foreign, legend(off)"}),
    "p04": (_TWO, {"by": "foreign", "legend": "off"}),
    "p05": (_TWO, {"by": "foreign, total legend(at(4) pos(0))"}),
    "p06": (_TWO, {"by": "foreign, total"}),
    "p08": (_ONE, {"by": "rep78, holes(2)"}),
    "p09": (_ONE, {"by": "rep78, colfirst"}),
    "p18": (_ONE, {"by": "rep78, iylabels"}),
    "p19": (_ONE, {"by": "foreign, iyaxes noiylabels"}),
    "p20": (_ONE, {"by": "foreign, iyaxes noiyticks"}),
    "p21": (_ONE, {"by": "rep78, iyaxes ixaxes"}),
    "p22": (_ONE, {"by": "rep78, iytitles ixtitles iyaxes ixaxes"}),
    "p23": (_ONE, {"by": "foreign, total noedgelabel"}),
    "p24": (_ONE, {"by": "foreign, total compact"}),
    "p25": (_ONE, {"by": "foreign, noytitles noxtitles"}),
    "p26": (_ONE, {"by": "foreign, individual"}),
    "p27": (_DUAL, {"by": "foreign", "ytitle2": '"Price"'}),
    "p28": (_DUAL, {"by": "foreign, iytitles iyaxes",
                    "ytitle2": '"Price"'}),
    "p32": (_TWO, {"by": "foreign, ilegends"}),
    "p33": (_ONE, {"by": "foreign, legend(on)"}),
    "p34": (_TWO, {"by": "foreign", "legend": "on"}),
    "p40": (_ONE, {"by": "rep78, holes(1 5)"}),
    "p41": (_ONE, {"by": "rep78, colfirst holes(3)"}),
    "p43": (_ONE, {"by": "foreign, total ixaxes"}),
    "p44": (_ONE, {"by": "foreign, iyticks"}),
    "p46": (_TWO, {"by": "foreign, legend(at(3) pos(0))"}),
    "p47": (_ONE, {"by": "foreign rep78, compact"}),
    "p48": (_ONE, {"by": "foreign, yrescale"}),
    "p49": (_ONE, {"by": "foreign, iyaxes noiyaxes"}),
    "p50": (_ONE, {"by": "foreign, noiyaxes iyaxes"}),
    "p51": (_ONE, {"by": "foreign, style(compact) total"}),
    "q06": ([_p("scatter", colorvar="headroom")], {"by": "foreign"}),
    "q07": ([_p("scatter", colorvar="headroom")],
            {"by": "foreign, clegend(on)"}),
    "q08": ([_p("scatter", colorvar="rep78", colordiscrete="yes")],
            {"by": "foreign, clegend(on)"}),
    "q09": ([_p("scatter", colorvar="headroom")],
            {"by": "foreign, clegend(on pos(6))"}),
    "r04": (_TWO, {"by": "foreign, legend(pos(6))",
                   "legend": "order(2 1)"}),
    "r05": (_TWO, {"by": "foreign, legend(pos(9))"}),
    "r06": (_TWO, {"by": "foreign, legend(pos(12) ring(0))"}),
}

#: twoway's relative_position of a key to dash's side of the panels.
_SIDE = {"rightof": "right", "leftof": "left", "above": "above",
         "below": "below", "on": "at"}


def _graph(name, plots, go, title=True):
    go = dict(go, name=name)
    if title:
        go.setdefault("title", '"%s"' % name)
    return {"name": name, "graph_options": go, "options": dict(go),
            "plots": copy.deepcopy(plots), "if_expr": "", "in_expr": ""}


def _spec(graphs, scheme="stcolor", filt=""):
    spec = tbt._spec({}, scheme=scheme, filt=filt)
    spec["graphs"] = graphs
    spec["build_options"]["registry"] = " ".join(g["name"] for g in graphs)
    return spec


def _build(mode, spec, data=None):
    """``(roots, notes, owner)`` of *spec* in *mode*: *owner* is the
    renderer (saved) or the document (served)."""
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data or tg._data(), fh)
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            owner = dr.DashRenderer(sp, dp)
            render_models(owner)
            roots = [owner._last_layout_root]
        else:
            from bokeh.document import Document
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
    notes = [str(w.message) for w in caught]
    if mode == "served":
        # The import draws a document of its own; its notes are the
        # session's, which test_by_text's reader leaves out too.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, "_bak_app_%d" % tag)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            owner = Document()
            mod.make_document(owner)
        roots = list(owner.roots)
        notes += [str(w.message) for w in caught]
    return roots, notes, owner


def _grids(roots):
    """``{graph title: GridPlot}`` of every by() grid under *roots*."""
    from bokeh.models import GridPlot
    out = {}
    for root in roots:
        for m in root.references():
            if not isinstance(m, GridPlot):
                continue
            figs = [c[0] for c in m.children
                    if type(c[0]).__name__ == "figure" and panel_label(c[0])]
            if figs:
                out[str(figs[0].title.text or "")] = m
    return out


def _one_root(grid):
    class _R:
        def references(self_inner):
            return [grid]
    return _R()


def _panels(grid):
    """The grid's panels in grid order."""
    return [f for _, _, f in by_grid(_one_root(grid))[0]]


def _cell(grid, name):
    """``(cell, row, col, rowspan, colspan)`` of the side cell *name*."""
    for c in grid.children:
        if getattr(c[0], "name", None) == name:
            c = tuple(c)
            return c if len(c) == 5 else c + (1, 1)
    return None


def _cell_side(grid, cell):
    """Where *cell* sits against the panels: right, left, above, below or
    at (inside the panel block)."""
    pc = [tuple(c) for c in grid.children
          if type(c[0]).__name__ == "figure"]
    rows = [int(c[1]) for c in pc]
    cols = [int(c[2]) for c in pc]
    r, c = int(cell[1]), int(cell[2])
    if (int(cell[3]), int(cell[4])) == (1, 1) and \
            min(cols) <= c <= max(cols) and r <= max(rows) + 1:
        return "at"
    if c > max(cols):
        return "right"
    if c < min(cols) and int(cell[4]) == 1:
        return "left"
    if r < min(rows):
        return "above"
    if r > max(rows):
        return "below"
    return "at"


def _axis_drawn(fig, which):
    """Whether *fig* draws its primary y (``y``), x (``x``) or second y
    (``y2``) axis; None without one."""
    if which == "y2":
        axes = [a for a in fig.yaxis if a.y_range_name != "default"]
    else:
        axes = dr._dash_primary_axes(getattr(fig, which + "axis"),
                                     which + "_range_name")
    if not axes:
        return None
    return any(a.visible for a in axes)


def _title_drawn(fig, which):
    if which == "y2":
        axes = [a for a in fig.yaxis if a.y_range_name != "default"]
    else:
        axes = dr._dash_primary_axes(getattr(fig, which + "axis"),
                                     which + "_range_name")
    if not axes:
        return None
    return any(a.visible and str(a.axis_label or "") for a in axes)


def _series_legends(fig):
    return [lg for lg in fig.legend
            if getattr(lg, "name", None) != dr._COLORVAR_LEGEND_NAME]


def _colour_keys(fig):
    from bokeh.models import ColorBar, Legend
    out = []
    for side in ("center", "left", "right", "above", "below"):
        for m in getattr(fig, side):
            if (isinstance(m, ColorBar) and m.name != "dash_by_label_box") \
                    or (isinstance(m, Legend)
                        and m.name == dr._COLORVAR_LEGEND_NAME):
                out.append(m)
    return out


def _probe_build(mode):
    """One build per mode of every chrome probe dash can spell, each graph
    titled with its probe id."""
    key = ("probes", mode)
    if key not in _BUILT:
        graphs = [_graph(pid, plots, go) for pid, (plots, go)
                  in sorted(_PROBES.items())]
        roots, notes, owner = _build(mode, _spec(graphs))
        _BUILT[key] = (_grids(roots), notes, owner)
    return _BUILT[key]


def _matched(grid, probe):
    """``[(fixture panel, dash panel)]`` matched by label."""
    figs = {panel_label(f): f for f in _panels(grid)}
    return [(p, figs.get(p["label"])) for p in probe["panels"]]


# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_it_is_stamped(self):
        d = _fix()
        assert all(k in d["_meta"] for k in ("stata_version", "born_date",
                                             "dash_commit", "extracted"))
        missing = [k for k in _PROBES if k not in d["probes"]]
        assert not missing, missing
        assert len(d["label_box"]) == 30
        bad = [k for k, p in d["probes"].items() if p["rc"]]
        assert not bad, bad


class TestTheUnitFunctions:
    def test__dash_by_axes_options(self):
        """Every probe's style switches as twoway read them: the
        abbreviation probes, both xor orders, compact, style(compact) and
        individual."""
        keys = ("edgelabel", "indiv_xaxes", "indiv_yaxes", "indiv_xlabels",
                "indiv_ylabels", "indiv_xticks", "indiv_yticks",
                "indiv_xtitles", "indiv_ytitles", "outer_xtitles",
                "outer_ytitles", "indiv_as_whole", "indiv_legends")
        bad = []
        for pid, p in sorted(_fix()["probes"].items()):
            cmd = p["command"]
            by = cmd[cmd.index("by(") + 3:]
            depth, end = 1, 0
            for i, ch in enumerate(by):
                depth += (ch == "(") - (ch == ")")
                if depth == 0:
                    end = i
                    break
            got = dr._dash_by_axes_options(
                by[:end], dr.SchemeParser(p["scheme"]))["flags"]
            if any(k in ("indiv_xrescale", "indiv_yrescale")
                   for k, v in p["style"].items() if v):
                continue  # rescale turns axes on in _dash_by_axis_flags
            for k in keys:
                if got[k] != p["style"][k]:
                    bad.append((pid, k, got[k], p["style"][k]))
        assert not bad, bad
        out = dr._dash_by_axes_options("foreign, legend(pos(6)) leg(at(2)) "
                                       "clegend(on)")
        assert out["legend"] == "pos(6) at(2)" and out["clegend"] == "on"
        assert dr._dash_by_axes_options(None)["flags"]["edgelabel"]

    def test__dash_by_axis_flags(self):
        """Per panel, the primary y, x and second y axes twoway draws, for
        every fixture probe's grid."""
        bad = []
        for pid, p in sorted(_fix()["probes"].items()):
            if pid.startswith(("a", "q")) or pid not in _PROBES:
                continue
            go = _PROBES[pid][1]
            opts = dr._dash_by_axes_options(go["by"],
                                            dr.SchemeParser(p["scheme"]))
            opts["rescaled"] = dr._dash_by_rescale(go["by"])
            gopts = dr._dash_by_grid_options(go["by"])
            _c, _r, _cc, extra = dr._dash_by_positions(
                p["n"], gopts, legend_at=p["legend_hole"])
            cells = extra["drawn"][0]
            flags = dr._dash_by_axis_flags(dict(enumerate(cells)), opts)
            alt = p["scheme"] == "economist"
            for k, q in enumerate(p["panels"]):
                f = flags[k]
                got = {"y": f["right"] if alt else f["left"], "x": f["x"],
                       "y2": f["left"] if alt else f["right"]}
                for a in ("y", "x", "y2"):
                    if q[a] is not None and got[a] != q[a]:
                        bad.append((pid, k + 1, a, got[a], q[a]))
        assert not bad, bad

    def test__dash_by_axis_side(self):
        from bokeh.plotting import figure
        f = figure()
        assert dr._dash_by_axis_side(f, f.yaxis[0]) == "left"
        assert dr._dash_by_axis_side(f, f.xaxis[0]) == "below"
        assert dr._dash_by_axis_side(f, object()) is None

    def test__dash_by_outer_axes(self):
        """The right panel loses its y axis and every per-panel title; the
        titles come back for the stacked view."""
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        for f in figs:
            f.yaxis.axis_label = "Y"
            f.xaxis.axis_label = "X"
        out = dr._dash_by_outer_axes(figs, {0: (0, 0), 1: (0, 1)},
                                     dr._dash_by_axes_options("g"))
        assert (out["y"], out["x"]) == ("Y", "X")
        assert [f.yaxis[0].visible for f in figs] == [True, False]
        assert [f.xaxis[0].visible for f in figs] == [True, True]
        assert all(a.axis_label is None for f in figs
                   for a in list(f.xaxis) + list(f.yaxis))
        assert ["Y", "X", "Y", "X"] == [r[2] for r in out["restore"]]
        g = figure()
        g.yaxis.axis_label = "Y"
        dr._dash_by_outer_axes([g], {0: (0, 0)},
                               dr._dash_by_axes_options("g, noiylabels "
                                                        "noiyticks"))
        assert g.yaxis[0].major_label_text_font_size == "0px"
        assert g.yaxis[0].major_tick_out == 0

    def test__dash_by_cell(self):
        cell = dr._dash_by_cell(None, "dash_by_legend", (1, None))
        assert type(cell).__name__ == "Plot" and cell.name == "dash_by_legend"
        assert cell.frame_width == 1 and cell.toolbar_location is None
        assert dr._dash_by_cell(None, "dash_by_xtitle",
                                (None, 1)).frame_height == 1

    def test__dash_by_title_cell(self):
        from bokeh.models import LinearAxis
        ax = LinearAxis(axis_label_text_font_size="17px",
                        axis_label_text_color="#123456")
        cell = dr._dash_by_title_cell(None, "dash_by_ytitle", "Y", "left", ax)
        (t,) = [m for m in cell.left if type(m).__name__ == "Title"]
        assert (t.text, t.text_font_size, t.text_color) == (
            "Y", "17px", "#123456")

    def test__dash_by_glyph_fields(self):
        from bokeh.models import Scatter
        assert dr._dash_by_glyph_fields(
            Scatter(x="weight", y="mpg", size=4)) == ["weight", "mpg"]

    def test__dash_by_clone_renderers(self):
        from bokeh.models import ColumnDataSource, GlyphRenderer, Scatter
        r = GlyphRenderer(data_source=ColumnDataSource({"a": [1], "b": [2]}),
                          glyph=Scatter(x="a", y="b", fill_color="red"))
        (c,) = dr._dash_by_clone_renderers([r], "t")
        assert dr._dash_is_swatch(c) and c.glyph is not r.glyph
        assert c.glyph.fill_color == "red"
        assert {k: len(v) for k, v in c.data_source.data.items()} == {
            "a": 1, "b": 1}

    def test__dash_by_clock_side(self):
        assert [dr._dash_by_clock_side(c, 6) for c in
                ("3", "9", "12", "6", "x")] == ["right", "left", "above",
                                                "below", "below"]

    def test__dash_by_legend_cell(self):
        from bokeh.models import (ColumnDataSource, GlyphRenderer, Legend,
                                  LegendItem, Scatter)
        r = GlyphRenderer(data_source=ColumnDataSource({"a": [1], "b": [2]}),
                          glyph=Scatter(x="a", y="b"))
        lg = Legend(items=[LegendItem(label="k", renderers=[r])],
                    orientation="horizontal")
        cell = dr._dash_by_legend_cell(None, "dash_by_legend", "below", lg,
                                       lg.items, "l")
        (new,) = [m for m in cell.above if isinstance(m, Legend)]
        assert new.orientation == "horizontal" and new.click_policy == "none"
        assert [i.label for i in new.items] == [i.label for i in lg.items]

    def test__dash_by_keys(self):
        """The unit half: panel legends hidden, one cell of panel 1's two
        keys below (s2color's 6), none for one key."""
        from bokeh.plotting import figure
        figs = []
        for _ in range(2):
            f = figure()
            f.scatter([1], [1], legend_label="a")
            f.line([1], [1], legend_label="b")
            figs.append(f)
        out = dr._dash_by_keys(figs, dr._dash_by_axes_options("g"),
                               dr.SchemeParser("s2color"))
        assert out["legend"].name == "dash_by_legend"
        assert out["legend_side"] == "below" and out["clegend"] is None
        assert not any(lg.visible for f in figs for lg in f.legend)

    def test__dash_by_layout_options(self):
        assert dr._dash_by_layout_options({"by": "g", "by_cols": "3"})[
            "cols"] == 3
        assert dr._dash_by_layout_options({"by": "g, rows(2)",
                                           "by_cols": "3"})["cols"] == 0

    def test__dash_by_side(self):
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        for f in figs:
            f.scatter([1], [1])
            f.yaxis.axis_label = "Y"
            f.xaxis.axis_label = "X"
        side = dr._dash_by_side(figs, {"by": "g"}, dr.SchemeParser("s2color"))
        assert figs[0]._dash_by_side is side
        names = sorted(c.name for _k, c, _w in side["cells"])
        assert names == ["dash_by_xtitle", "dash_by_ytitle"]
        assert side["hook"].name == "dash_by_stack"

    def test__dash_by_side_grid(self):
        from bokeh.layouts import gridplot
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        grid = gridplot([figs])
        grid.children = [(figs[0], 0, 0), (figs[1], 0, 1)]
        cells = {n: dr._dash_by_cell(None, n) for n in
                 ("dash_by_ytitle", "dash_by_xtitle", "dash_by_legend")}
        side = {"cells": [("ytitle", cells["dash_by_ytitle"], ""),
                          ("xtitle", cells["dash_by_xtitle"], ""),
                          ("legend", cells["dash_by_legend"], "right")]}
        assert dr._dash_by_side_grid(grid, side, 1, 2) == 4
        got = {getattr(c[0], "name", None) or "p": tuple(c[1:])
               for c in grid.children}
        assert got["dash_by_ytitle"] == (0, 0, 1, 1)
        assert got["dash_by_xtitle"] == (1, 1, 1, 2)
        assert got["dash_by_legend"] == (0, 3, 1, 1)
        assert [tuple(c[1:3]) for c in grid.children[:2]] == [(0, 1), (0, 2)]

    def test__dash_by_stack_hook(self):
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        hook = dr._dash_by_stack_hook(figs, [figs[1].yaxis[0]],
                                      [[False, None, "Y", True]], [], figs[0])
        assert hook.code == dr._DASH_BY_STACK_JS
        assert json.loads(hook.args["labels_json"]) == [[False, None, "Y",
                                                         True]]
        assert dr._dash_by_stack_hook(figs[:1], [], [], [], figs[0]) is None
        assert "..." not in dr._DASH_BY_STACK_JS
        assert "__" not in dr._DASH_BY_STACK_JS

    def test__dash_by_stack_hooks(self):
        from bokeh.layouts import column
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        side = dr._dash_by_side(figs, {"by": "g"}, None)
        assert dr._dash_by_stack_hooks([column(*figs)]) == [side["hook"]]
        assert dr._dash_by_stack_hooks([column(figure())]) == []

    def test_reflow_side_columns(self):
        """A by() grid's title and legend columns are max-content and the
        stacking width counts the panel columns only."""
        from bokeh.layouts import gridplot
        from bokeh.plotting import figure
        figs = [figure(), figure()]
        grid = gridplot([figs])
        yt = dr._dash_by_cell(None, "dash_by_ytitle")
        lg = dr._dash_by_cell(None, "dash_by_legend")
        grid.children = [(yt, 0, 0, 1, 1), (figs[0], 0, 1), (figs[1], 0, 2),
                         (lg, 0, 3, 1, 1)]
        dr._dash_reflow(grid)
        assert grid.cols == ["max-content", dr._DASH_BS_TRACK,
                             dr._DASH_BS_TRACK, "max-content"]
        css = grid.stylesheets[-1].css
        assert "max-width: %.2fpx" % (2 * dr._DASH_MIN_COLUMN_PX - 0.02) in css

    def test_spellings_agree_with_the_grammar(self):
        """Every spelling is the same word under S48's grammar, and every
        spelling the grammar gives the word is listed."""
        bad = []
        for key, sps in dr._DASH_BY_AXES_SPELLINGS.items():
            mn = dr._DASH_BY_GRAMMAR[key][0]
            want = tuple(key[:i] for i in range(len(mn), len(key) + 1)
                         if dr._dash_by_word(key[:i])[0] == key)
            if tuple(sps) != want:
                bad.append((key, sps, want))
        assert not bad, bad


@pytest.mark.parametrize("mode", _MODES)
class TestOuterAxes:
    def test_probe(self, mode):
        """Each panel draws the y, x and second y axes twoway draws, for
        every probe."""
        grids, _n, _o = _probe_build(mode)
        bad = []
        for pid in sorted(_PROBES):
            p = _fix()["probes"][pid]
            if pid not in grids:
                bad.append((pid, "no grid"))
                continue
            for q, fig in _matched(grids[pid], p):
                if fig is None:
                    bad.append((pid, q["label"], "no panel"))
                    continue
                for a in ("y", "x", "y2"):
                    got = _axis_drawn(fig, a)
                    if q[a] is not None and got is not None and got != q[a]:
                        bad.append((pid, q["label"], a, got, q[a]))
        assert not bad, bad


@pytest.mark.parametrize("mode", _MODES)
class TestAxisTitlesOnce:
    def test_probe(self, mode):
        """No panel draws an axis title twoway leaves off (a second
        axis's included), and the title cells hold twoway's l1title and
        b1title."""
        grids, _n, _o = _probe_build(mode)
        bad = []
        for pid in sorted(_PROBES):
            p = _fix()["probes"][pid]
            grid = grids[pid]
            for q, fig in _matched(grid, p):
                for a, k in (("y", "ytitle"), ("x", "xtitle"),
                             ("y2", "y2title")):
                    got = _title_drawn(fig, a)
                    if q[k] is not None and got is not None and got != q[k]:
                        bad.append((pid, q["label"], k, got, q[k]))
            for name, want in (("dash_by_ytitle", p["l1title"]),
                               ("dash_by_xtitle", p["b1title"])):
                c = _cell(grid, name)
                text = side_title(c[0])[1] if c is not None else ""
                if pid in ("p27", "p28") and name == "dash_by_ytitle":
                    want = want  # the y title is mpg's in both
                if text != want:
                    bad.append((pid, name, text, want))
        assert not bad, bad


@pytest.mark.parametrize("mode", _MODES)
class TestOneLegend:
    def test_probe(self, mode):
        """Panel legends only where twoway draws them; one overall legend
        of panel 1's keys, in order, on twoway's side or in its hole."""
        grids, _n, _o = _probe_build(mode)
        bad = []
        for pid in sorted(_PROBES):
            if pid.startswith("q"):
                continue
            p = _fix()["probes"][pid]
            grid = grids[pid]
            for q, fig in _matched(grid, p):
                vis = any(lg.visible and lg.items
                          for lg in _series_legends(fig))
                if bool(q["legend"]) != vis:
                    bad.append((pid, q["label"], "panel legend", vis))
            want = bool(p["legend"]["drawn"] or p["legend"]["at_drawn"])
            c = _cell(grid, "dash_by_legend")
            if want != (c is not None):
                bad.append((pid, "overall", c is not None, want))
                continue
            if c is None:
                continue
            side = _cell_side(grid, c)
            if side != _SIDE[p["legend"]["side"]]:
                bad.append((pid, "side", side, p["legend"]["side"]))
            from bokeh.models import Legend
            (lg,) = [m for s in ("left", "right", "above", "below")
                     for m in getattr(c[0], s) if isinstance(m, Legend)]
            first = _series_legends(_panels(grid)[0])[0]
            if [i.label for i in lg.items] != [i.label for i in first.items]:
                bad.append((pid, "items"))
        assert not bad, bad

    def test_a_hole_counts_in_the_grid(self, mode):
        """by(foreign, legend(at(3) pos(0))): a 2 x 2 grid, the legend in
        cell 3 (E4 p46), full_n 3."""
        grids, _n, _o = _probe_build(mode)
        grid = grids["p46"]
        c = _cell(grid, "dash_by_legend")
        pan = [(int(x[1]), int(x[2])) for x in grid.children
               if type(x[0]).__name__ == "figure"]
        r0 = min(r for r, _ in pan)
        c0 = min(cc for _, cc in pan)
        assert sorted((r - r0, cc - c0) for r, cc in pan) == [(0, 0), (0, 1)]
        assert (int(c[1]) - r0, int(c[2]) - c0) == (1, 0)
        assert dr._dash_by_positions(2, {}, legend_at=3)[3]["full_n"] == 3


@pytest.mark.parametrize("mode", _MODES)
class TestTheChromeIsNotData:
    def test_clones_are_not_data(self, mode):
        """The overall legend's renderers are swatch clones on one NaN
        row, reached by no filter callback, and a served move leaves
        them as they were."""
        from bokeh.models import CustomJS, GlyphRenderer
        spec = _spec([_graph("g1", _TWO, {"by": "foreign"})],
                     filt="rep78")
        roots, _n, owner = _build(mode, spec)
        (grid,) = _grids(roots).values()
        cell = _cell(grid, "dash_by_legend")[0]
        clones = [r for r in cell.renderers if isinstance(r, GlyphRenderer)]
        assert clones and all(dr._dash_is_swatch(r) for r in clones)
        ids = {id(r) for r in clones} | {id(r.data_source) for r in clones}
        for root in roots:
            for m in root.references():
                if isinstance(m, CustomJS) and m.name != "dash_by_stack":
                    for v in m.args.values():
                        vs = v if isinstance(v, (list, tuple)) else [v]
                        assert not any(id(x) in ids for x in vs)
        if mode == "served":
            (w,) = [x for x in tp._widgets_of(owner)
                    if type(x).__name__ == "Select"]
            tp._fire(w, w.options[1][0])
        for r in clones:
            vals = list(r.data_source.data.values())
            assert all(len(v) == 1 and v[0] != v[0] for v in vals)


@pytest.mark.parametrize("mode", _MODES)
class TestColourKeyUnderBy:
    def test_key(self, mode):
        """No colour key on any panel; with clegend(on) one key cell,
        bound to panel 1's mapper (continuous) or holding panel 1's
        levels (discrete), on twoway's side."""
        from bokeh.models import ColorBar, Legend
        grids, _n, _o = _probe_build(mode)
        bad = []
        for pid in ("q06", "q07", "q08", "q09"):
            p = _fix()["probes"][pid]
            grid = grids[pid]
            panels = _panels(grid)
            for f in panels:
                if _colour_keys(f):
                    bad.append((pid, "panel key", panel_label(f)))
            c = _cell(grid, "dash_by_clegend")
            if bool(p["clegend"]["drawn"]) != (c is not None):
                bad.append((pid, "overall", c is not None))
                continue
            if c is None:
                continue
            if _cell_side(grid, c) != _SIDE[p["clegend"]["side"]]:
                bad.append((pid, "side", _cell_side(grid, c)))
            bars = [m for s in ("left", "right", "above", "below")
                    for m in getattr(c[0], s) if isinstance(m, ColorBar)]
            legs = [m for s in ("left", "right", "above", "below")
                    for m in getattr(c[0], s) if isinstance(m, Legend)]
            mappers = {id(getattr(getattr(r.glyph, "fill_color", None),
                                  "transform", None))
                       for r in panels[0].renderers}
            if pid == "q08":
                if len(legs) != 1 or not legs[0].items:
                    bad.append((pid, "discrete key"))
            elif len(bars) != 1 or id(bars[0].color_mapper) not in mappers:
                bad.append((pid, "mapper"))
        assert not bad, bad


@pytest.mark.parametrize("mode", _MODES)
class TestAfterAFilterMove:
    def test_chrome_holds(self, mode):
        """After a move the axis flags, cells and the key's binding to
        panel 1's mapper hold; on the saved page no filter callback reaches
        a side cell or a label box."""
        from bokeh.models import ColorBar, CustomJS
        spec = _spec([_graph("g1", [_p("scatter", colorvar="headroom")],
                             {"by": "foreign, clegend(on)"})], filt="rep78")
        roots, _n, owner = _build(mode, spec)
        (grid,) = _grids(roots).values()

        def state():
            panels = _panels(grid)
            key = _cell(grid, "dash_by_clegend")[0]
            (bar,) = [m for m in key.left + key.above
                      if isinstance(m, ColorBar)]
            m = bar.color_mapper
            boxes = [b.major_label_overrides for f in panels
                     for b in f.above if b.name == "dash_by_label_box"]
            return ([(_axis_drawn(f, "y"), _axis_drawn(f, "x"))
                     for f in panels], id(m), boxes)
        before = state()
        if mode == "served":
            (w,) = [x for x in tp._widgets_of(owner)
                    if type(x).__name__ == "Select"]
            tp._fire(w, w.options[1][0])
            assert state()[0] == before[0] and state()[2] == before[2]
            panels = _panels(grid)
            key = _cell(grid, "dash_by_clegend")[0]
            (bar,) = [m for m in key.left + key.above
                      if isinstance(m, ColorBar)]
            mappers = [getattr(r.glyph.fill_color, "transform", None)
                       for r in panels[0].renderers
                       if hasattr(r, "glyph")]
            assert any(m is bar.color_mapper for m in mappers)
        else:
            side_ids = {id(c[0]) for c in grid.children
                        if str(getattr(c[0], "name", "") or "").startswith(
                            "dash_by_")}
            for root in roots:
                for m in root.references():
                    if isinstance(m, CustomJS) and m.name != "dash_by_stack":
                        for v in m.args.values():
                            vs = v if isinstance(v, (list, tuple)) else [v]
                            assert not any(id(x) in side_ids for x in vs)


@pytest.mark.parametrize("mode", _MODES)
class TestTheNotes:
    def test_silent_and_named(self, mode):
        """The words drawn now name nothing; legend(off) outside by() is
        silent, as twoway ignores it; legend(ring(0)) inside by() is drawn
        outside the panels at its compass, as twoway draws it, and names
        nothing (WP-31 D10)."""
        spec = _spec([
            _graph("g1", _TWO, {"by": "foreign, legend(off) iyaxes "
                                      "noedgelabel ilegends clegend(on) ixt"}),
            _graph("g2", _TWO, {"by": "foreign", "legend": "off"}),
            _graph("g3", _TWO, {"by": "foreign, legend(pos(12) ring(0))"})])
        _r, notes, _o = _build(mode, spec)
        assert not [n for n in notes if "by() sub-option" in n], notes
        assert not [n for n in notes if "legend" in n.lower()
                    and "ring(0)" not in n], notes
        ring = [n for n in notes if "ring(0)" in n]
        assert ring == [], notes


@pytest.mark.parametrize("mode", _MODES)
class TestTheToolbar:
    def test_one_save_tool(self, mode):
        """Guard: the grid keeps one SaveTool, which writes <name>.png."""
        from bokeh.models import SaveTool
        grids, _n, _o = _probe_build(mode)
        grid = grids["p02"]
        saves = [t for t in grid.toolbar.tools if isinstance(t, SaveTool)]
        # A sub-grid of an auto layout writes dashboard.png, as before.
        assert len(saves) == 1
        assert saves[0].filename == dr._dash_save_filename(None)


@pytest.mark.parametrize("mode", _MODES)
class TestTheStackHook:
    def test_attached(self, mode):
        """The page runs the stack hook on document_ready; a page with no
        by() grid is serialised as before."""
        spec = _spec([_graph("g1", _ONE, {"by": "foreign"})])
        plain = _spec([_graph("g1", _ONE, {})])
        if mode == "saved":
            pages, plain_roots = [], []
            for sp in (spec, plain):
                tag = next(_SEQ)
                a = os.path.join(_TMP, "h_%d.json" % tag)
                b = os.path.join(_TMP, "hd_%d.json" % tag)
                with open(a, "w") as fh:
                    json.dump(sp, fh)
                with open(b, "w") as fh:
                    json.dump(tg._data(), fh)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = dr.DashRenderer(a, b)
                    pages.append(r.render())
                plain_roots = [r._last_layout_root]
            # Booleans: a failing `in` over a whole page is a costly diff.
            hooked = "dash_by_stack" in pages[0] and "labels_json" in pages[0]
            assert hooked
            # A page with no by() grid attaches no hook.
            assert dr._dash_by_stack_hooks(plain_roots) == []
            plain = "dash_by_stack" in pages[1]
            assert not plain
        else:
            _r, _n, doc = _build(mode, spec)
            hooks = doc.callbacks._js_event_callbacks.get("document_ready", [])
            assert [h.name for h in hooks] == ["dash_by_stack"]
            _r, _n, doc = _build(mode, plain)
            assert not doc.callbacks._js_event_callbacks.get("document_ready")


class TestTheSchemeKeys:
    def test_every_scheme(self):
        """The 26 shipped files carry the by() keys scheme_truth.json
        records, and SchemeParser reads them."""
        with open(_SCHEME_FIXTURE, encoding="utf-8") as fh:
            truth = json.load(fh)
        schemes = truth.get("schemes", truth)
        bad = []
        names = [n for n in schemes if not n.startswith("_")]
        assert len(names) == 26
        for name in names:
            e = schemes[name]
            sp = dr.SchemeParser(name)
            want = {"by_legend_position": e["by_legend_position"],
                    "zyx2_position": e["zyx2legend_position"],
                    "by_label_fill": e["by_label_fill"],
                    "by_label_outline": e["bylabel_outline_color"]}
            for attr, v in want.items():
                got = getattr(sp, attr)
                if str(got).lower() != str(v).lower():
                    bad.append((name, attr, got, v))
            for k in ("edgelabel", "outer_xaxes", "indiv_xlabels",
                      "indiv_as_whole", "indiv_ytitles"):
                if sp.by_flags[k] != e["by_" + k]:
                    bad.append((name, k))
            if sp.by_indiv_margin() != tuple(
                    float(v) for v in sp.margin_sides(e["by_indiv_margin"])):
                bad.append((name, "by_indiv"))
        assert not bad, bad


class TestTheHelp:
    def test_it_documents_shared_axes_and_keys(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        sec = text[text.index("Faceting with by()"):]
        sec = sec[:sec.index("{marker", 10)] if "{marker" in sec[10:] \
            else sec[:20000]
        for word in ("iyaxes", "noedgelabel", "ilegends", "clegend(on)",
                     "individual", "{cmd:at(}", "filled box"):
            assert word in sec, word
        assert "legend() and the i* axis" not in sec


# ---- the panel label's box (ratification row 36) --------------------------

def _boxes(fig):
    from bokeh.models import ColorBar
    return [m for s in ("above", "below") for m in getattr(fig, s)
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box"]


def _box_build(mode):
    key = ("boxes", mode)
    if key not in _BUILT:
        lb = _fix()["label_box"]
        graphs = []
        for pid in sorted(lb):
            if pid in ("box_fcolor", "box_nobox"):
                continue
            by = {"box_two": "foreign rep78",
                  "box_total": "foreign, total"}.get(pid, "foreign")
            graphs.append(_graph(pid, _ONE, {"by": by,
                                             "scheme": lb[pid]["scheme"]}))
        roots, notes, owner = _build(mode, _spec(graphs, scheme="s2color"))
        _BUILT[key] = (_grids(roots), notes, owner)
    return _BUILT[key]


class TestTheLabelBox:
    def test_unit(self):
        from bokeh.models import ColorBar, Title
        from bokeh.plotting import figure
        f = figure()
        t = Title(name="dash_by_label", text="Domestic", align="center",
                  text_font_size="13px")
        f.add_layout(t, "above")
        idx = list(f.above).index(t)
        box = dr._dash_by_label_box(f, dr.SchemeParser("s2color"), 0.85)
        assert isinstance(box, ColorBar) and box.name == "dash_by_label_box"
        assert list(f.above).index(box) == idx and t.visible is False
        assert box.major_label_overrides == {0.5: "Domestic"}
        assert dr._dash_by_label_box(f, None) is box
        g = figure()
        assert dr._dash_by_label_box(g, None) is None
        g.add_layout(Title(name="dash_by_label", text=""), "above")
        assert dr._dash_by_label_box(g, None) is None

    @pytest.mark.parametrize("mode", _MODES)
    def test_scheme_colours(self, mode):
        """Every scheme: each panel's box fill and outline are twoway's,
        and its outline width is twoway's stroke in px."""
        grids, _n, _o = _box_build(mode)
        lb = _fix()["label_box"]
        bad = []
        for pid in sorted(lb):
            if not pid.startswith("box_") or pid in ("box_fcolor",
                                                     "box_nobox"):
                continue
            rec = lb[pid]
            want = rec["panels"][0]["box"]
            unit = rec["units_per_rs"]
            for fig in _panels(grids[pid]):
                (b,) = _boxes(fig) or [None]
                if b is None:
                    bad.append((pid, panel_label(fig), "no box"))
                    continue
                fill = b.color_mapper.palette[0].lower()
                if fill != want["fill"] or \
                        str(b.bar_line_color).lower() != want["outline"]:
                    bad.append((pid, fill, b.bar_line_color, want))
                px = want["stroke_width"] / unit * \
                    dr.OptionTranslator.PT_PER_RS * \
                    dr.OptionTranslator.PX_PER_PT
                if pid != "box_two" and abs(b.bar_line_width - px) > 0.15:
                    bad.append((pid, "width", b.bar_line_width, px))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_height_follows_the_text_and_margins(self, mode):
        grids, _n, _o = _box_build(mode)
        lb = _fix()["label_box"]
        bad = []
        for pid in ("box_s2color", "box_stcolor", "box_economist",
                    "box_two"):
            want = lb[pid]["panels"][0]
            ratio = want["box"]["height"] / want["font_size"]
            b = _boxes(_panels(grids[pid])[0])[0]
            font = float(str(b.major_label_text_font_size)[:-2])
            got = b.height / font
            if abs(got / ratio - 1) > 0.05:
                bad.append((pid, got, ratio))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_label_is_drawn_in_the_box(self, mode):
        """The box draws the hidden Title's finished text, in its colour
        and style (a TeX and an SMCL value label included); economist's is
        left-aligned."""
        data = tg._data()
        data["valueLabels"]["foreign"] = {"0": "$$x$$", "1": "{bf:x}"}
        grids = {}
        for name, scheme in (("g1", "stcolor"), ("g2", "economist")):
            roots, _n, _o = _build(mode, _spec(
                [_graph(name, _ONE, {"by": "foreign"})], scheme=scheme), data)
            grids.update(_grids(roots))
        for name, align in (("g1", 0.5), ("g2", 0.0)):
            for fig in _panels(grids[name]):
                t = panel_label_title(fig)
                (b,) = _boxes(fig)
                assert t.visible is False
                assert b.major_label_overrides == {align: t.text}
                px = dr.OptionTranslator.css_to_pt
                assert abs(px(b.major_label_text_font_size)
                           - px(t.text_font_size)) < 0.01
                assert (b.major_label_text_color, b.major_label_text_font_style
                        ) == (t.text_color, t.text_font_style)
        texts = [panel_label_title(f).text for f in _panels(grids["g1"])]
        assert texts[0] != "$$x$$"  # the TeX pair is broken, as typed
        assert "{bf:" not in texts[1]

    @pytest.mark.parametrize("mode", _MODES)
    def test_which_panels_have_a_box(self, mode):
        grids, _n, _o = _box_build(mode)
        assert [len(_boxes(f)) for f in _panels(grids["box_total"])] == [
            1, 1, 1]
        spec = _spec([_graph("g1", _ONE, {"by": "foreign",
                                          "subtitle": '""'}),
                      _graph("g2", _ONE, {"by": "foreign",
                                          "subtitle": '", fcolor(red)"'})])
        spec["graphs"][1]["graph_options"]["subtitle"] = ", fcolor(red)"
        roots, notes, _o = _build(mode, spec, None)
        grids = _grids(roots)
        assert not grids.get("g1") or not any(
            _boxes(f) for f in _panels(grids["g1"]))
        # WP-31 D10: the graph's own subtitle(, fcolor()) fills every
        # panel label's box, silently, as twoway's (by_chrome_truth
        # box_fcolor).
        for f in _panels(grids["g2"]):
            (b,) = _boxes(f)
            assert b.color_mapper.palette[0].lower() == "#ff0000"
        assert len([n for n in notes if "fcolor" in n]) == 0, notes

    @pytest.mark.parametrize("mode", _MODES)
    def test_after_a_filter_move(self, mode):
        spec = _spec([_graph("g1", [_p("scatter", colorvar="headroom")],
                             {"by": "foreign, clegend(on)"})], filt="rep78")
        roots, _n, owner = _build(mode, spec)
        (grid,) = _grids(roots).values()

        def boxes():
            return [(b.color_mapper.palette, b.bar_line_color, b.height,
                     b.major_label_overrides, b.color_mapper.low,
                     b.color_mapper.high)
                    for f in _panels(grid) for b in _boxes(f)]
        before = boxes()
        assert before and all(x[4:] == (0, 1) for x in before)
        if mode == "served":
            (w,) = [x for x in tp._widgets_of(owner)
                    if type(x).__name__ == "Select"]
            tp._fire(w, w.options[1][0])
        assert boxes() == before
        key = _cell(grid, "dash_by_clegend")[0]
        assert all(b is not k for f in _panels(grid) for b in _boxes(f)
                   for k in key.left + key.above)
