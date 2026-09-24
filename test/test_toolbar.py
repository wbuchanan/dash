"""The toolbar, in both render modes (WP-21: TR-21.1, TR-21.2, TR-21.5).

Every figure carries the same nine tools, in the same order, whichever way
the dashboard is rendered: pan, wheel zoom, box zoom, box select, lasso
select, undo, redo, reset and save.  There is no crosshair: in the toolbar a
grid of figures shares, it draws its lines across every figure at once, and
the hover tool already reads values off a figure.

``gridplot()`` merges every figure's ``SaveTool`` into ONE new ``SaveTool``
on the grid's toolbar, and BokehJS exports that tool's parent -- the whole
grid -- as a single PNG.  Bokeh builds the merged tool with no file name, and
BokehJS would then prompt() for one, with ``bokeh_plot`` filled in; every grid
dash builds (the dashboard's, each tab's, each by() graph's panels) names it
``dashboard``.  Under ``layout(bs)`` the saved page embeds each item on its
own, so each keeps its own toolbar, and its save button is named after the
item it holds.

What these tests found before the change: the served app handed ONE list of
five tool objects to every figure it drew, so every toolbar in a served
document held the same instances (``TestTheServedApp``); neither mode had box
zoom, undo, redo or a save button.
"""
import itertools
import json
import os
import re
import sys
import warnings

import pytest
from bokeh.layouts import gridplot
from bokeh.models import (Div, GridPlot, Plot, SaveTool, Tabs, Tool,
                          ToolProxy, WheelZoomTool)
from bokeh.models.tools import Drag
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr
import test_mode_parity as tp
from test_adversarial_matrix import (_app_source, _load_app, _session,
                                     _write_inputs)
from test_server_layer_defects import plot_for

_SEQ = itertools.count()

#: The nine tools every figure carries, in toolbar order.
_NINE = ("PanTool", "WheelZoomTool", "BoxZoomTool", "BoxSelectTool",
         "LassoSelectTool", "UndoTool", "RedoTool", "ResetTool", "SaveTool")

#: Each tool's row label in the help's toolbar table, by its Bokeh alias.
_HELP_LABELS = {"pan": "Pan", "wheel_zoom": "Wheel zoom",
                "box_zoom": "Box zoom", "box_select": "Box select",
                "lasso_select": "Lasso select", "undo": "Undo",
                "redo": "Redo", "reset": "Reset", "save": "Save"}

_ACTIVE = ("active_drag", "active_scroll", "active_tap", "active_multi",
           "active_inspect")


# ---------------------------------------------------------------------------
# Specs and renders
# ---------------------------------------------------------------------------

_SCATTER = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}
_LINE = {"type": "line", "yvar": "price", "xvar": "weight", "options": {}}
_HIST = {"type": "histogram", "var": "mpg", "options": {}}


def _graph(name, plots=None, **gopts):
    go = {"name": name}
    go.update(gopts)
    return {"name": name, "graph_options": go, "options": dict(go),
            "plots": [dict(p) for p in (plots or [_SCATTER])],
            "if_expr": "", "in_expr": ""}


def _kpi(name="k1"):
    return {"name": name, "stat": "mean", "var": "mpg", "fmt": "%9.2f",
            "title": "Mean mpg", "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter", "if_expr": "", "in_expr": ""}


def _spec(graphs, kpis=(), **build):
    """A master spec; the registry is the graphs then the KPIs."""
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "default",
          "title": "", "subtitle": "", "tabs": "", "filter_position": "top",
          "registry": " ".join([g["name"] for g in graphs] +
                               [k["name"] for k in kpis])}
    bo.update(build)
    return {"graphs": list(graphs), "kpis": list(kpis), "build_options": bo}


#: Every kind of grid the dashboard builds, and the cells that go in one.
_CORPUS = {
    "two graphs": lambda: _spec([_graph("g1"), _graph("g2", [_LINE])]),
    "a by() graph beside a graph": lambda: _spec(
        [_graph("g1", by="foreign"), _graph("g2", [_LINE])]),
    "tabs, one graph left over": lambda: _spec(
        [_graph("g1"), _graph("g2", [_LINE]), _graph("g3", [_HIST])],
        tabs="A: g1 / B: g2"),
    "a by() graph in a tab": lambda: _spec(
        [_graph("g1", by="foreign"), _graph("g2", [_LINE])], tabs="A: g1"),
    "a KPI, a filter and a link": lambda: _spec(
        [_graph("g1"), _graph("g2", [_LINE])], kpis=[_kpi()],
        link="g1 g2", filter="foreign, type(dropdown)"),
    "layout() placement": lambda: _spec(
        [_graph("g1"), _graph("g2", [_LINE])], layout="g2:1,1 g1:1,2"),
}


def _saved(tmp_path, spec):
    """``(renderer, html)`` from the saved-dashboard renderer."""
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        html = r.render()
    return r, html


def _served(tmp_path, spec):
    """``(document, namespace, source)``: one session of the generated app."""
    src = _app_source(tmp_path, spec)
    ns = _load_app(src, "toolbar_%d" % next(_SEQ))
    return _session(ns), ns, src


def _walk(model):
    """*model* and every model a layout holds under it, in document order:
    a grid's cells by (row, column), each tab's content, a column's or a
    row's children."""
    if model is None:
        return
    yield model
    if isinstance(model, GridPlot):
        for cell in sorted(model.children, key=lambda c: (c[1], c[2])):
            yield from _walk(cell[0])
    elif isinstance(model, Tabs):
        for panel in model.tabs:
            yield from _walk(panel.child)
    else:
        for child in getattr(model, "children", None) or []:
            yield from _walk(child)


def _saved_models(r):
    root = r._last_layout_root
    assert root is not None, "no layout root: was this a layout(bs) spec?"
    return list(_walk(root))


def _served_models(doc):
    return [m for root in doc.roots for m in _walk(root)]


def _figures(models):
    return [m for m in models if isinstance(m, Plot)]


def _grids(models):
    return [m for m in models if isinstance(m, GridPlot)]


def _names(fig):
    return [type(t).__name__ for t in fig.tools]


def _saves_of(model):
    """``(save tools on the model's own toolbar, save tools a proxy there
    wraps)``.  A proxied SaveTool would export one figure, not the grid."""
    tools = list(model.toolbar.tools)
    direct = [t for t in tools if isinstance(t, SaveTool)]
    proxied = [x for t in tools if isinstance(t, ToolProxy)
               for x in t.tools if isinstance(x, SaveTool)]
    return direct, proxied


def _page_save_filenames(html):
    """The ``filename`` of every SaveTool serialised into a saved page, in
    document order; None for a tool with none.  Anchored on Bokeh's object
    encoding, which the BokehJS library in the page never spells."""
    out = []
    for m in re.finditer(r'\{"type":"object","name":"SaveTool","id":"p\d+"'
                         r'(?:,"attributes":(\{[^{}]*\}))?\}', html):
        out.append(json.loads(m.group(1)).get("filename")
                   if m.group(1) else None)
    return out


def _assert_nine_tools(fig, where):
    names = _names(fig)
    assert tuple(names[:len(_NINE)]) == _NINE, (where, names)
    assert set(names[len(_NINE):]) <= {"HoverTool"}, (where, names)


def _assert_grid_saves_as_dashboard(grid, where):
    direct, proxied = _saves_of(grid)
    assert len(direct) == 1, (where, "save tools on the grid's toolbar",
                              len(direct))
    assert direct[0].filename == "dashboard", (where, direct[0].filename)
    assert not proxied, (where, "a SaveTool inside a ToolProxy")


def _assert_no_shared_tools(figs, where):
    owner = {}
    for i, f in enumerate(figs):
        for t in f.tools:
            assert owner.setdefault(id(t), i) == i, (
                where, "figures %d and %d share one %s"
                % (owner[id(t)], i, type(t).__name__))


# ---------------------------------------------------------------------------
# The tool list
# ---------------------------------------------------------------------------

class TestTheToolList:
    """``_DASH_FIGURE_TOOLS``: one string, read by both modes."""

    def test_it_names_the_nine_tools_in_order(self):
        built = [type(Tool.from_string(a)).__name__
                 for a in dr._DASH_FIGURE_TOOLS.split(",")]
        assert tuple(built) == _NINE

    def test_it_has_no_crosshair(self):
        assert "crosshair" not in dr._DASH_FIGURE_TOOLS

    def test_each_figure_built_from_it_owns_new_tools(self):
        figs = [figure(tools=dr._DASH_FIGURE_TOOLS) for _ in range(3)]
        _assert_no_shared_tools(figs, "figure(tools=_DASH_FIGURE_TOOLS)")
        for f in figs:
            _assert_nine_tools(f, "a bare figure")

    def test_the_grid_name_is_dashboard(self):
        assert dr._DASH_SAVE_NAME == "dashboard"


# ---------------------------------------------------------------------------
# _dash_save_filename
# ---------------------------------------------------------------------------

class TestSaveFilename:
    """A Stata name, or ``dashboard``; nothing else reaches the page."""

    @pytest.mark.parametrize("name", ["g1", "_", "_g", "G_2", "scatter_mpg",
                                      "a" * 32])
    def test_a_stata_name_is_kept(self, name):
        assert dr._dash_save_filename(name) == name

    def test_no_name_is_dashboard(self):
        assert dr._dash_save_filename() == "dashboard"
        assert dr._dash_save_filename(None) == "dashboard"
        assert dr._dash_save_filename("") == "dashboard"

    @pytest.mark.parametrize("name", [
        "1g", "g-1", "g 1", "g1\n", "\ng1", "g1\x00", "../g1", "g1/..",
        "a/b", "C:\\g1", "g1.png", "a" * 33, "g\u00e9", "\uff47\uff11",
        "g1\u202e", "<script>", '"g1"', "' onload='x"])
    def test_anything_else_is_dashboard(self, name):
        assert dr._dash_save_filename(name) == "dashboard"

    @pytest.mark.parametrize("name", [7, 1.5, b"g1", ["g1"], {"g1": 1}])
    def test_a_value_that_is_not_text_is_dashboard(self, name):
        assert dr._dash_save_filename(name) == "dashboard"

    def test_a_huge_name_is_refused_without_being_scanned(self):
        """The pattern is bounded at 32 characters and has no nested
        repetition, so a megabyte of name costs what 33 characters do."""
        assert dr._dash_save_filename("a" * 1_000_000) == "dashboard"
        assert dr._dash_save_filename("a" * 31 + "!" * 1_000_000) == \
            "dashboard"


# ---------------------------------------------------------------------------
# _dash_name_save
# ---------------------------------------------------------------------------

def _fig(tools=None):
    return figure(tools=tools if tools is not None else dr._DASH_FIGURE_TOOLS)


def _save_of(fig):
    (tool,) = [t for t in fig.tools if isinstance(t, SaveTool)]
    return tool


class TestNameSave:
    """Names the save button on a figure's or a grid's own toolbar."""

    def test_a_figure_is_named_and_returned(self):
        f = _fig()
        assert dr._dash_name_save(f, "g1") is f
        assert _save_of(f).filename == "g1"

    def test_a_figure_with_no_name_is_dashboard(self):
        f = _fig()
        dr._dash_name_save(f)
        assert _save_of(f).filename == "dashboard"

    def test_a_name_that_is_not_a_stata_name_is_dashboard(self):
        f = _fig()
        dr._dash_name_save(f, "../../etc/passwd")
        assert _save_of(f).filename == "dashboard"

    def test_the_last_name_wins(self):
        f = _fig()
        dr._dash_name_save(f, "g1")
        dr._dash_name_save(f, "g2")
        assert _save_of(f).filename == "g2"

    def test_gridplot_merges_every_save_tool_into_one_unnamed_tool(self):
        """What the helper exists for, pinned: if Bokeh stops merging the
        save tools this way, naming the grid's would silently do nothing."""
        a, b = _fig(), _fig()
        grid = gridplot([[a, b]])
        direct, proxied = _saves_of(grid)
        assert len(direct) == 1 and not proxied
        assert direct[0] is not _save_of(a) and direct[0] is not _save_of(b)
        assert direct[0].filename is None

    def test_a_grid_is_named_dashboard_and_returned(self):
        a, b = _fig(), _fig()
        grid = gridplot([[a, b]])
        assert dr._dash_name_save(grid) is grid
        _assert_grid_saves_as_dashboard(grid, "gridplot")

    def test_a_grid_leaves_its_figures_own_save_tools_alone(self):
        a, b = _fig(), _fig()
        dr._dash_name_save(gridplot([[a, b]]))
        assert _save_of(a).filename is None and _save_of(b).filename is None

    def test_a_grid_takes_a_name_as_a_figure_does(self):
        grid = dr._dash_name_save(gridplot([[_fig(), _fig()]]), "g2")
        assert _saves_of(grid)[0][0].filename == "g2"

    def test_every_save_tool_on_the_toolbar_is_named(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")     # "SaveTool are being repeated"
            f = figure(tools=[SaveTool(), SaveTool()])
        dr._dash_name_save(f, "g1")
        assert [t.filename for t in f.tools] == ["g1", "g1"]

    def test_a_toolbar_with_no_save_tool_is_left_as_it_is(self):
        f = _fig("pan,reset")
        assert dr._dash_name_save(f, "g1") is f
        assert _names(f) == ["PanTool", "ResetTool"]

    def test_a_model_with_no_toolbar_is_returned_unchanged(self):
        d = Div(text="k1")
        assert dr._dash_name_save(d, "k1") is d


# ---------------------------------------------------------------------------
# The saved page
# ---------------------------------------------------------------------------

class TestTheSavedPage:

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_every_figure_has_the_nine_tools_in_order(self, tmp_path, case):
        r, _ = _saved(tmp_path, _CORPUS[case]())
        figs = _figures(_saved_models(r))
        assert figs, case
        assert len(figs) == len(r.figures), case
        for i, f in enumerate(figs):
            _assert_nine_tools(f, (case, i))
        _assert_no_shared_tools(figs, case)

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_every_grid_saves_as_dashboard(self, tmp_path, case):
        r, html = _saved(tmp_path, _CORPUS[case]())
        grids = _grids(_saved_models(r))
        assert grids, case
        for i, g in enumerate(grids):
            _assert_grid_saves_as_dashboard(g, (case, i))
        # What the browser receives: one named save tool per grid, and every
        # figure's own (merged away, never shown) left unnamed.
        names = _page_save_filenames(html)
        assert names.count("dashboard") == len(grids), (case, names)
        assert names.count(None) == len(r.figures), (case, names)
        assert len(names) == len(grids) + len(r.figures), (case, names)

    def test_the_main_grid_saves_the_whole_grid(self, tmp_path):
        r, _ = _saved(tmp_path, _CORPUS["two graphs"]())
        root = r._last_layout_root
        assert isinstance(root, GridPlot)
        (tool,), _ = _saves_of(root)
        assert tool.filename == "dashboard"
        # A new tool on the grid's toolbar, which BokehJS exports the grid
        # through -- not one figure's own.
        assert all(tool is not _save_of(f) for f in r.figures.values())

    def test_each_tab_saves_its_own_grid(self, tmp_path):
        r, _ = _saved(tmp_path, _CORPUS["tabs, one graph left over"]())
        (tabs,) = [m for m in _saved_models(r) if isinstance(m, Tabs)]
        assert [p.title for p in tabs.tabs] == ["A", "B"]
        for p in tabs.tabs:
            assert isinstance(p.child, GridPlot), p.title
            _assert_grid_saves_as_dashboard(p.child, p.title)
        # and the grid below the tabs, holding g3, has its own
        grids = [g for g in _grids(_saved_models(r))
                 if all(g is not p.child for p in tabs.tabs)]
        assert len(grids) == 1
        _assert_grid_saves_as_dashboard(grids[0], "the grid below the tabs")

    def test_a_by_graph_s_panels_save_as_dashboard(self, tmp_path):
        r, _ = _saved(tmp_path, _CORPUS["a by() graph beside a graph"]())
        root = r._last_layout_root
        facet = [g for g in _grids(_saved_models(r)) if g is not root]
        assert len(facet) == 1
        assert len(_figures(list(_walk(facet[0])))) == 2
        _assert_grid_saves_as_dashboard(facet[0], "the by() grid")
        _assert_grid_saves_as_dashboard(root, "the dashboard's grid")

    def test_no_figure_or_grid_has_a_crosshair(self, tmp_path):
        r, html = _saved(tmp_path, _CORPUS["a by() graph in a tab"]())
        for m in _saved_models(r):
            if isinstance(m, (Plot, GridPlot)):
                assert "Crosshair" not in " ".join(
                    type(t).__name__ for t in m.toolbar.tools)
        assert '"name":"CrosshairTool"' not in html


# ---------------------------------------------------------------------------
# layout(bs): each item keeps its own toolbar
# ---------------------------------------------------------------------------

class TestTheBootstrapPage:

    def test_a_graph_s_save_is_named_after_it(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("scatter_2", [_LINE])],
                     kpis=[_kpi()], layout="bs")
        r, html = _saved(tmp_path, spec)
        assert r._last_layout_root is None
        for key, f in r.figures.items():
            _assert_nine_tools(f, key)
        assert _save_of(r.figures["g1"]).filename == "g1"
        assert _save_of(r.figures["scatter_2"]).filename == "scatter_2"
        # Embedded one by one: no grid, so no merged tool and none unnamed.
        assert sorted(_page_save_filenames(html)) == ["g1", "scatter_2"]

    def test_explicit_spans_name_them_the_same_way(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("g2", [_LINE])],
                     layout="bs: g2=4 g1=8")
        r, html = _saved(tmp_path, spec)
        assert _save_of(r.figures["g1"]).filename == "g1"
        assert _save_of(r.figures["g2"]).filename == "g2"
        assert sorted(_page_save_filenames(html)) == ["g1", "g2"]

    def test_a_by_graph_s_cell_saves_under_the_graph_s_name(self, tmp_path):
        """A by() graph is one bs cell: a sub-grid with one toolbar whose
        save button writes all its panels, named after the graph."""
        spec = _spec([_graph("g1"), _graph("g2", by="foreign")], layout="bs")
        r, html = _saved(tmp_path, spec)
        assert sorted(r.figures) == ["g1", "g2__by__0", "g2__by__1"]
        names = _page_save_filenames(html)
        # g1's own; the g2 cell's merged one; the two panels' own, unnamed.
        assert sorted(n for n in names if n) == ["g1", "g2"], names
        assert names.count(None) == 2, names
        for key in ("g2__by__0", "g2__by__1"):
            assert _save_of(r.figures[key]).filename is None, key

    def test_a_tab_under_bs_saves_its_grid_as_dashboard(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("g2", [_LINE])], layout="bs",
                     tabs="A: g2")
        r, html = _saved(tmp_path, spec)
        assert _save_of(r.figures["g1"]).filename == "g1"
        names = _page_save_filenames(html)
        # g1's own; tab A's grid; g2's own, merged into tab A's and unnamed.
        assert sorted(n for n in names if n) == ["dashboard", "g1"], names
        assert names.count(None) == 1, names
        assert _save_of(r.figures["g2"]).filename is None

    def test_only_a_stata_name_reaches_the_page(self, tmp_path):
        """A hand-built spec whose registered name is not a Stata name gets
        dashboard.png, not a file name the browser has to sanitise."""
        spec = _spec([_graph("../g1")], layout="bs")
        r, html = _saved(tmp_path, spec)
        assert _save_of(r.figures["../g1"]).filename == "dashboard"
        assert [n for n in _page_save_filenames(html) if n] == ["dashboard"]


# ---------------------------------------------------------------------------
# The served app
# ---------------------------------------------------------------------------

class TestTheServedApp:

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_no_two_figures_share_a_tool(self, tmp_path, case):
        """The app used to build ONE list of five tools and hand it to every
        figure, so every toolbar in the document held the same objects."""
        doc, _, _ = _served(tmp_path, _CORPUS[case]())
        figs = _figures(_served_models(doc))
        assert len(figs) >= 2, case
        _assert_no_shared_tools(figs, case)

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_every_figure_has_the_nine_tools_in_order(self, tmp_path, case):
        doc, _, _ = _served(tmp_path, _CORPUS[case]())
        figs = _figures(_served_models(doc))
        assert figs, case
        for i, f in enumerate(figs):
            _assert_nine_tools(f, (case, i))

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_every_grid_saves_as_dashboard(self, tmp_path, case):
        doc, _, _ = _served(tmp_path, _CORPUS[case]())
        grids = _grids(_served_models(doc))
        assert grids, case
        for i, g in enumerate(grids):
            _assert_grid_saves_as_dashboard(g, (case, i))

    def test_tabs_and_a_by_graph_each_save_as_dashboard(self, tmp_path):
        doc, _, _ = _served(tmp_path, _CORPUS["a by() graph in a tab"]())
        models = _served_models(doc)
        (tabs,) = [m for m in models if isinstance(m, Tabs)]
        (panel,) = tabs.tabs
        inner = [g for g in _grids(list(_walk(panel.child)))
                 if g is not panel.child]
        assert len(inner) == 1, "the by() graph's own grid, inside the tab"
        for g in (panel.child, inner[0]):
            _assert_grid_saves_as_dashboard(g, "tab A")

    def test_layout_bs_saves_each_graph_under_its_name(self, tmp_path):
        """A served layout(bs) is a 12-column GridBox (WP-21), not a
        gridplot: nothing merges the toolbars, so each figure keeps its own,
        and its save button writes the graph under its own name -- as the
        saved page's does for the same spec.  (It used to fall back to a
        gridplot saved as dashboard.png; this test pinned that.)"""
        spec = _spec([_graph("g1"), _graph("g2", [_LINE])], layout="bs")
        doc, _, _ = _served(tmp_path, spec)
        models = _served_models(doc)
        assert not _grids(models), "the served layout(bs) is a gridplot again"
        # The toolbars hang off the figures, outside the layout walk.
        served = sorted(t.filename for t in doc.select({"type": SaveTool}))
        assert served == ["g1", "g2"]
        _r, html = _saved(tmp_path, spec)
        assert sorted(_page_save_filenames(html)) == served

    def test_the_app_reads_the_saved_renderer_s_list(self, tmp_path):
        _, ns, src = _served(tmp_path, _CORPUS["two graphs"]())
        assert "TOOLS = [" not in src and "tools=TOOLS" not in src
        assert "tools=_DASH_FIGURE_TOOLS" in src
        assert ns["_DASH_FIGURE_TOOLS"] == dr._DASH_FIGURE_TOOLS
        assert ns["_DASH_SAVE_NAME"] == dr._DASH_SAVE_NAME
        assert ns["_DASH_SAVE_NAME_RE"].pattern == dr._DASH_SAVE_NAME_RE.pattern

    def test_the_app_s_copy_of_the_helpers_behaves_as_the_renderer_s(
            self, tmp_path):
        _, ns, _ = _served(tmp_path, _CORPUS["two graphs"]())
        for name in ("g1", "", None, "../g1", "a" * 33, "g\u00e9", 7):
            assert ns["_dash_save_filename"](name) == \
                dr._dash_save_filename(name), name
        f = _fig()
        assert ns["_dash_name_save"](f, "g9") is f
        assert _save_of(f).filename == "g9"


# ---------------------------------------------------------------------------
# Both modes, compared
# ---------------------------------------------------------------------------

class TestBothModesAgree:
    """The saved page and the served document hold the same toolbars: the
    same tools in the same order on each figure, in document order, and the
    same save name on each grid.  ``test_mode_parity`` compares the tool
    types over its whole corpus; this compares the order and the names."""

    @pytest.mark.parametrize("case", sorted(_CORPUS))
    def test_the_same_toolbars(self, tmp_path, case):
        r, _ = _saved(tmp_path, _CORPUS[case]())
        doc, _, _ = _served(tmp_path, _CORPUS[case]())
        std, srv = _saved_models(r), _served_models(doc)
        std_figs, srv_figs = _figures(std), _figures(srv)
        assert len(std_figs) == len(srv_figs) >= 2, case
        assert [_names(f) for f in std_figs] == \
            [_names(f) for f in srv_figs], case
        std_grids, srv_grids = _grids(std), _grids(srv)
        assert len(std_grids) == len(srv_grids) >= 1, case
        assert [[t.filename for t in _saves_of(g)[0]] for g in std_grids] \
            == [[t.filename for t in _saves_of(g)[0]] for g in srv_grids], \
            case


class TestTheParityGuardSeesAToolbarDrift:
    """``test_mode_parity`` profiles each figure's tools IN ORDER and each
    grid's own toolbar (its save button and file name).  Guards the guard:
    a served document changed after the build, in one of those two ways,
    must differ from the saved one in that profile."""

    @staticmethod
    def _pair():
        spec = tp._spec(graphs=[("g1", [plot_for("scatter")]),
                                ("g2", [plot_for("line")])])
        return tp._standalone(spec)[0], tp._served(spec)[0]

    @staticmethod
    def _diffs(r, doc):
        """``(tree diffs, per-figure tool diffs)``, as test_mode_parity
        computes them."""
        std_figs, srv_figs = [], []
        std = tp._layout_tree(r._last_layout_root, std_figs)
        srv = [tp._layout_tree(x, srv_figs) for x in doc.roots]
        srv = srv[0] if len(srv) == 1 else srv
        assert len(std_figs) == len(srv_figs) == 2
        return (tp._diff(std, srv),
                [d for a, b in zip(std_figs, srv_figs)
                 for d in tp._diff(a["tools"], b["tools"])])

    def test_an_untouched_pair_agrees(self):
        assert self._diffs(*self._pair()) == ([], [])

    def test_the_same_tools_in_another_order_differ(self):
        r, doc = self._pair()
        fig = _figures(_served_models(doc))[0]
        tools = list(fig.tools)
        tools[1], tools[2] = tools[2], tools[1]
        fig.tools = tools
        tree, tools_diff = self._diffs(r, doc)
        assert tools_diff, "a reordered served toolbar compared equal"

    def test_a_grid_that_saves_under_another_name_differs(self):
        r, doc = self._pair()
        (grid,) = _grids(_served_models(doc))
        (save,), _ = _saves_of(grid)
        save.filename = None
        tree, _ = self._diffs(r, doc)
        assert tree, "a served grid with an unnamed save compared equal"


# ---------------------------------------------------------------------------
# What is active when the page opens
# ---------------------------------------------------------------------------

def _bokehjs_default_order():
    """``{tool class: default_order}`` from the BokehJS bundle Bokeh ships.

    BokehJS activates, for ``active_drag="auto"``, the drag tool with the
    LOWEST ``default_order`` -- not the first one listed -- so whether box
    zoom would take over the drag is decided by these numbers.
    """
    import bokeh
    path = os.path.join(os.path.dirname(bokeh.__file__), "server", "static",
                        "js", "bokeh.js")
    cls_re = re.compile(r"\bclass (\w+) extends\b")
    ord_re = re.compile(r"\bthis\.default_order = (\d+);")
    out, cur = {}, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = cls_re.search(line)
            if m:
                cur = m.group(1)
                continue
            m = ord_re.search(line)
            if m and cur and cur not in out:
                out[cur] = int(m.group(1))
    return out


class TestWhatIsActiveWhenThePageOpens:
    """Unchanged by the new tools: a drag pans, and the wheel scrolls the
    page until wheel zoom is clicked."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_every_toolbar_leaves_the_choice_to_bokeh(self, tmp_path, mode):
        spec = _CORPUS["a by() graph in a tab"]()
        if mode == "saved":
            models = _saved_models(_saved(tmp_path, spec)[0])
        else:
            models = _served_models(_served(tmp_path, spec)[0])
        bars = [m for m in models if isinstance(m, (Plot, GridPlot))]
        # The "by() graph in a tab" corpus draws exactly six toolbar-bearing
        # models in each mode -- three GridPlots and three figures (measured
        # 24sep2026) -- and the two modes must match.  `>= 5' passed if a
        # bar went missing.
        assert len(bars) == 6, [type(m).__name__ for m in bars]
        for m in bars:
            for attr in _ACTIVE:
                assert getattr(m.toolbar, attr) == "auto", (
                    type(m).__name__, attr, getattr(m.toolbar, attr))

    def test_pan_is_the_drag_a_page_opens_with(self, tmp_path):
        order = _bokehjs_default_order()
        r, _ = _saved(tmp_path, _CORPUS["two graphs"]())
        for f in r.figures.values():
            drags = [type(t).__name__ for t in f.tools if isinstance(t, Drag)]
            assert sorted(drags) == ["BoxSelectTool", "BoxZoomTool",
                                     "LassoSelectTool", "PanTool"], drags
            missing = [d for d in drags if d not in order]
            assert not missing, ("default_order not found in bokeh.js",
                                 missing)
            first = min(drags, key=lambda d: order[d])
            assert first == "PanTool", {d: order[d] for d in drags}
            assert sum(order[d] == order["PanTool"] for d in drags) == 1

    def test_wheel_zoom_is_off_until_it_is_clicked(self, tmp_path):
        """BokehJS auto-activates a wheel tool only when it has a modifier
        key; with none, the wheel scrolls the page."""
        doc, _, _ = _served(tmp_path, _CORPUS["two graphs"]())
        r, _ = _saved(tmp_path, _CORPUS["two graphs"]())
        figs = list(r.figures.values()) + _figures(_served_models(doc))
        for f in figs:
            (w,) = [t for t in f.tools if isinstance(t, WheelZoomTool)]
            assert not w.modifiers, w.modifiers
            assert f.toolbar.active_scroll == "auto"


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

def _help():
    with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
        return fh.read()


def _toolbar_section():
    h = _help()
    i = h.index("{marker toolbar}")
    j = h.index("{marker ", i + 1)
    return h[i:j]


class TestTheHelpDocumentsTheToolbar:

    def test_the_section_is_in_the_jump_list(self):
        assert '"dash##toolbar"' in _help()

    def test_every_tool_has_a_row_in_order(self):
        sec = _toolbar_section()
        rows = re.findall(r"\{synopt:([^}]*)\}", sec)
        want = [_HELP_LABELS[a] for a in dr._DASH_FIGURE_TOOLS.split(",")]
        assert rows == want, rows

    def test_it_names_the_files_the_save_button_writes(self):
        sec = " ".join(_toolbar_section().split())
        assert "{cmd:dashboard.png}" in sec
        assert "{cmd:layout(bs)}" in sec and "{cmd:g1.png}" in sec

    def test_it_says_there_is_no_crosshair(self):
        assert "no crosshair" in " ".join(_toolbar_section().split())

    def test_the_mode_table_lists_the_toolbar_in_both_modes(self):
        # The comparison table is laid out in {col #} columns (WP-23: as
        # {synopt} rows Stata collapsed the spacing that separated the two
        # modes' cells), so a row is its feature, then one cell per mode.
        h = _help()
        sec = h[h.index("{marker server_mode}"):h.index("{marker limits}")]
        row = [ln for ln in sec.split("\n")
               if re.match(r"\{col \d+\}Toolbar, save as PNG\{col ", ln)]
        assert len(row) == 1, row
        cells = [c.strip() for c in re.split(r"\{col \d+\}", row[0])[2:]]
        assert cells == ["Yes", "Yes"], row
