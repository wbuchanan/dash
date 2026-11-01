"""tabs() and layout() edges (WP-31 D14, section 39).

GAPS3 D14: ``tabs()`` dropped a name that is not registered without a word;
a served ``layout(s1:1,1 s2:1,1)`` put s2 in the cell, and s1 vanished;
a tab could not take its own ``layout()``.

dash.ado now refuses a ``tabs()`` name that is not registered and a
``layout()`` placing two names in one cell (Mata ``_dash_tabs_refusal`` and
``_dash_layout_refusal``; test_option_validation.cscript U39-01).  For a
spec that did not come through dash.ado the renderer drops what it cannot
place and says so: ``_dash_parse_tabs`` warns for an unknown name and for a
per-tab ``layout()`` it cannot read, and ``_dash_layout_check`` reports a
same-cell collision and keeps the first name, so both grids draw it.  A tab
segment may end with ``, layout(rows cols)`` or ``, layout(name:row,col
...)`` over its own names, drawn by ``_dash_tab_grid`` in both renderers.
"""
import itertools
import json
import os
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.models import GridPlot, Tabs

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import load_app, make_data_json, render_models

_FIXTURE = os.path.join(_HERE, "fixtures", "tabs_legend_edges_truth.json")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_tabs_edges_")
_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0],
                    "weight": [2930.0, 3350.0, 2200.0, 1800.0]})
MODES = ("saved", "served")


def _spec(names, layout="auto", tabs=""):
    graphs = [{"name": n, "graph_options": {"name": n, "title": n},
               "options": {},
               "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                          "options": {}}]} for n in names]
    return {"graphs": graphs, "kpis": [],
            "build_options": {"layout": layout, "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "",
                              "registry": " ".join(names), "tabs": tabs,
                              "filter_position": "top", "level": "95",
                              "formats": {}}}


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_DF), fh)
    return tag, sp, dp


def _root(mode, spec):
    """The layout root each mode draws, and the warnings it raised."""
    dr._dash_reset_notes()
    tag, sp, dp = _write(spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            roots = [r._last_layout_root]
        else:
            from bokeh.document import Document
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_tabs_edges_app_%d" % tag, draw=False)
            doc = Document()
            mod.make_document(doc)
            roots = list(doc.roots)
    return roots, [str(w.message) for w in caught]


def _title_of(m):
    t = getattr(m, "title", None)
    return getattr(t, "text", None) if t is not None else None


def _grid_cells(grid):
    """{figure title: (row, col)} of one GridPlot."""
    out = {}
    for child in grid.children:
        title = _title_of(child[0])
        if title is None:
            for sub in child[0].select({"type": dr.Plot}) if hasattr(
                    child[0], "select") else []:
                title = _title_of(sub)
                if title:
                    break
        if title:
            out[title] = (child[1], child[2])
    return out


def _tabs(roots):
    """{tab title: {figure title: (row, col)}} for every Tabs model."""
    out = {}
    for root in roots:
        for t in root.select({"type": Tabs}):
            for p in t.tabs:
                grids = list(p.child.select({"type": GridPlot}))
                cells = {}
                if grids:
                    cells = _grid_cells(grids[0])
                out[p.title] = cells
    return out


def _main_grid(roots):
    """{figure title: (row, col)} of the grid outside every tab."""
    in_tabs = set()
    for root in roots:
        for t in root.select({"type": Tabs}):
            for p in t.tabs:
                in_tabs.update(id(g) for g in p.child.select({"type": GridPlot}))
    for root in roots:
        for g in root.select({"type": GridPlot}):
            if id(g) not in in_tabs:
                return _grid_cells(g)
    return {}


class TestTheFixture:
    def test_meta(self):
        d = json.load(open(_FIXTURE))
        assert sorted(d["_meta"]) == ["born_date", "dash_commit", "extracted",
                                      "source", "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_tabs_legend_edges_truth.do"

    def test_keys(self):
        d = json.load(open(_FIXTURE))
        for grp, keys in (("legend", ("po9_top", "top_po9", "top", "jse47")),
                          ("title", ("prefix_suffix", "suffix_prefix")),
                          ("label", ("one", "one_text")),
                          ("nested", ("region_lcolor_bogus", "region_bad_word",
                                      "title_size_bogus", "title_bad_word"))):
            for k in keys:
                assert {"rc", "lines", "cmd"} <= set(d[grp][k]), (grp, k)


class TestParseTabs:
    def test_shape(self):
        got = dr._dash_parse_tabs("A: g1 g2 / B: g3", ["g1", "g2", "g3"])
        assert got == [("A", ["g1", "g2"], None), ("B", ["g3"], None)]

    def test_unknown_warns(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_parse_tabs("A: nosuch g1 / B: other", ["g1"])
        assert got == [("A", ["g1"], None)]
        msgs = [str(w.message) for w in caught]
        assert any("tabs()" in m and "nosuch" in m and "other" in m
                   and "not placed" in m for m in msgs), msgs
        assert len([m for m in msgs if "tabs()" in m]) == 1, msgs

    def test_known_silent(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_parse_tabs("A: g1 / B: g2", ["g1", "g2"])
        assert not [w for w in caught if "tabs()" in str(w.message)]


class TestPerTabLayout:
    @pytest.mark.parametrize("mode", MODES)
    def test_grid(self, mode):
        roots, _ = _root(mode, _spec(["g1", "g2", "g3"],
                                     tabs="A: g1 g2, layout(1 2) / B: g3"))
        tabs = _tabs(roots)
        assert tabs["A"] == {"g1": (0, 0), "g2": (0, 1)}, tabs
        assert tabs["B"] == {"g3": (0, 0)}, tabs

    @pytest.mark.parametrize("mode", MODES)
    def test_placement(self, mode):
        roots, _ = _root(mode, _spec(
            ["g1", "g2", "g3"],
            tabs="A: g1 g2 g3, layout(g1:2,2 g2:1,1 g3:1,2)"))
        assert _tabs(roots)["A"] == {"g1": (1, 1), "g2": (0, 0),
                                     "g3": (0, 1)}

    @pytest.mark.parametrize("bad", [
        "layout(g3:1,1)",           # a name outside the tab
        "layout(g1:1,1 g2:1,1)",    # two names in one cell
        "layout(bs)",               # no bs inside a tab
        "layout(1 2 3)",            # not a form
        "cols(2)",                  # not layout()
    ])
    def test_bad_forms_warn(self, bad):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_parse_tabs("A: g1 g2, " + bad, ["g1", "g2", "g3"])
        assert got == [("A", ["g1", "g2"], None)], got
        assert any("tabs()" in str(w.message) for w in caught), bad

    def test_comma_after_names_is_the_options_split(self):
        """The first comma after a tab's colon ends its names; a title
        before the colon may hold one."""
        got = dr._dash_parse_tabs("Cars, all: g1 g2, layout(2 1)",
                                  ["g1", "g2"])
        assert got == [("Cars, all", ["g1", "g2"], "2 1")]

    def test_the_tab_grid_helper(self):
        cell = {"a": "A", "b": "B", "c": "C"}.get
        assert dr._dash_tab_grid(["a", "b"], "1 2", cell) == [["A", "B"]]
        assert dr._dash_tab_grid(["a", "b"], "a:1,2 b:1,1", cell) == [
            ["B", "A"]]
        # no layout: today's ceil(sqrt(n)) grid
        assert dr._dash_tab_grid(["a", "b", "c"], None, cell) == [
            ["A", "B"], ["C", None]]


class TestSameCell:
    @pytest.mark.parametrize("mode", MODES)
    def test_saved_first(self, mode):
        roots, msgs = _root(mode, _spec(["s1", "s2"], layout="s1:1,1 s2:1,1"))
        cells = _main_grid(roots)
        assert cells.get("s1") == (0, 0), cells
        # s2 is not drawn over s1: it takes the next free cell, as a
        # name the layout does not place does.
        assert cells.get("s2") not in (None, (0, 0)), cells

    def test_served_first(self):
        self.test_saved_first("served")

    def test_check_reports(self):
        kept, problem = dr._dash_layout_check("s1:1,1 s2:1,1 s3:1,2",
                                              {"s1", "s2", "s3"})
        assert kept == "s1:1,1 s3:1,2", kept
        assert problem and ("s1 and s2 are placed in the same cell 1,1, "
                            "so s2 is drawn in the next free cell"
                            ) in problem, problem


class TestServedCopy:
    def test_names(self):
        """The served app carries _dash_tab_grid beside _dash_parse_tabs."""
        tag, sp, dp = _write(_spec(["g1"], tabs="A: g1"))
        ap = os.path.join(_TMP, "app_names_%d.py" % tag)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        text = open(ap, encoding="utf-8").read()
        assert "def _dash_parse_tabs(" in text
        assert "def _dash_tab_grid(" in text

    def test_template_call(self):
        """The served tab builder is _dash_tab_panels, which draws each tab
        through _dash_tab_grid."""
        import inspect
        assert "_dash_tab_grid(" in inspect.getsource(dr._dash_tab_panels)
