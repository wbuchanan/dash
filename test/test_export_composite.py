"""test_export_composite.py -- the whole dashboard as one PNG or SVG, and
the print layout (WP-31 H2x; DECISIONS A28, A30).

Every top-level grid's toolbar holds three export controls in both modes:
the save button (the grid alone, PNG, unchanged), "Save as SVG" -- which
on a top-level grid writes the composite -- and "Save dashboard", a
``CustomAction`` tagged ``dash_composite_png``.  A by() sub-grid keeps the
grid-alone SVG and gets no composite.  The composite is drawn from Bokeh
model values (``_DASH_COMPOSITE_JS``): the header, the filters' titles
and current values, the tab strip, the KPI cards, then the grid's own
exported image.  Printing fixes the layout at 1000 px and hides the
toolbars and the filters (``_dash_print_models``).

The layout arithmetic and the SVG writer run under node with a fake
``measureText`` of 7 px a character; the Chrome class is the release
tier and reads the files the page writes.
"""
import json
import math
import os
import re
import sys
import tempfile
import time
import warnings

import pytest
from bokeh.layouts import gridplot
from bokeh.models import (AbstractSlider, CustomAction, CustomJS, DataTable,
                          Div,
                          GridPlot, InlineStyleSheet,
                          InputWidget, Plot, SaveTool, Select, Tabs)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import responsive_probe  # noqa: E402
import test_export_svg as tsvg  # noqa: E402
import test_toolbar as tt  # noqa: E402

_PNG = "dash_composite_png"
_SVG = "dash_svg_save"
_CHROME = responsive_probe.find_chrome() is not None
_ARG_KEYS = {"grid", "name", "header", "header_ids", "widget_ids", "tabs_id",
             "kpi_ids", "table_ids"}


def _docs_models(docs):
    return {m.id: m for d in docs for m in d.models}


def _resolved(args, models):
    """The composite's models, as the action looks them up by id."""
    get = models.get
    return {"header": [get(i) if i else t for i, t in
                       zip(args["header_ids"], args["header"])],
            "widgets": [get(i) for i in args["widget_ids"]],
            "tabs": get(args["tabs_id"]) if args["tabs_id"] else None,
            "kpis": [get(i) for i in args["kpi_ids"]],
            "tables": [get(i) for i in args["table_ids"]]}


def _acts(model, tag):
    tools = getattr(getattr(model, "toolbar", None), "tools", None) or ()
    return [t for t in tools
            if isinstance(t, CustomAction) and tag in (t.tags or ())]


def _top_grids(models_roots):
    """The grids no other grid holds: what a reader exports from."""
    out = []

    def walk(m, inside):
        if m is None:
            return
        if isinstance(m, (GridPlot, Plot)):
            if not inside and m.toolbar_location is not None and any(
                    isinstance(t, SaveTool) for t in m.toolbar.tools):
                out.append(m)
            inside = True
        if isinstance(m, GridPlot):
            for c in m.children:
                walk(c[0], inside)
        elif isinstance(m, Tabs):
            for p in m.tabs:
                walk(p.child, inside)
        else:
            for c in getattr(m, "children", None) or []:
                walk(c[0] if isinstance(c, tuple) else c, inside)

    for r in models_roots:
        walk(r, False)
    return out


def _roots(docs):
    return [r for d in docs for r in d.roots]


_MODES = {"saved": tsvg._saved_docs, "served": tsvg._served_docs}


def _rich():
    return tt._spec([tt._graph("g1"), tt._graph("g2", [tt._LINE])],
                    kpis=[tt._kpi()], filter="foreign, type(dropdown)",
                    title="Cars", subtitle="1978")


# ---------------------------------------------------------------------------
# The actions on every toolbar
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", sorted(_MODES))
class TestTheActions:

    def test_three_controls_on_the_top_grid_both_modes(self, tmp_path,
                                                       mode):
        docs = _MODES[mode](tmp_path, _rich())
        grids = _top_grids(_roots(docs))
        assert len(grids) == 1, grids
        (g,) = grids
        tools = list(g.toolbar.tools)
        saves = [t for t in tools if isinstance(t, SaveTool)]
        (svg,) = _acts(g, _SVG)
        pngs = _acts(g, _PNG)
        assert pngs, "no CustomAction tagged dash_composite_png"
        (png,) = pngs
        assert len(saves) == 1
        assert [t for t in tools if isinstance(t, (SaveTool, CustomAction))
                ] == [saves[0], svg, png]
        assert png.description == "Save dashboard"
        assert png.icon == dr._DASH_COMPOSITE_PNG_ICON
        assert png.callback.code == (dr._DASH_COMPOSITE_JS
                                     + dr._DASH_COMPOSITE_SAVE_JS)
        assert svg.callback.code == (dr._DASH_COMPOSITE_JS
                                     + dr._DASH_SVG_SAVE_JS)
        models = _docs_models(docs)
        for act in (svg, png):
            assert set(act.callback.args) == _ARG_KEYS, set(act.callback.args)
            assert act.callback.args["grid"] is g
            assert act.callback.args["name"] == saves[0].filename
            a = _resolved(act.callback.args, models)
            heads = [h if isinstance(h, str) else h.text for h in a["header"]]
            assert "Cars" in heads[0] and "1978" in heads[1], heads
            assert [type(w).__name__ for w in a["widgets"]] == ["Select"]
            assert a["tabs"] is None
            assert len(a["kpis"]) == 1 and "db-kpi-card" in a["kpis"][0].text

    def test_a_second_call_updates_not_adds(self, tmp_path, mode):
        grid = gridplot([[tsvg._fig(), tsvg._fig()]])
        d1, d2 = Div(text="a"), Div(text="b")
        comp = {"header": ["", ""], "header_ids": [d1.id, ""],
                "widget_ids": [], "tabs_id": "", "kpi_ids": [],
                "table_ids": []}
        dr._dash_name_save(grid, None, composite=comp)
        dr._dash_name_save(grid, None,
                           composite=dict(comp, header_ids=[d2.id, ""]))
        (svg,) = _acts(grid, _SVG)
        (png,) = _acts(grid, _PNG)
        for act in (svg, png):
            assert act.callback.args["header_ids"][0] == d2.id
        # without composite, a plain grid keeps today's one action
        plain = gridplot([[tsvg._fig()]])
        dr._dash_name_save(plain)
        assert _acts(plain, _PNG) == []
        assert _acts(plain, _SVG)[0].callback.code == dr._DASH_SVG_SAVE_JS

    def test_tab_grids_and_bs_items_get_them(self, tmp_path, mode):
        docs = _MODES[mode](tmp_path, tt._CORPUS["tabs, one graph left over"]())
        grids = _top_grids(_roots(docs))
        assert len(grids) == 3, grids  # two tabs' grids and the grid left
        models = _docs_models(docs)
        for g in grids:
            (png,) = _acts(g, _PNG)
            assert isinstance(_resolved(png.callback.args, models)["tabs"],
                              Tabs)
        sub = tmp_path / "bs"
        sub.mkdir()
        docs = _MODES[mode](sub, tt._spec(
            [tt._graph("g1"), tt._graph("g2", [tt._LINE])],
            kpis=[tt._kpi()], layout="bs", title="T"))
        grids = _top_grids(_roots(docs))
        names = sorted(_acts(g, _PNG)[0].callback.args["name"]
                       for g in grids)
        assert names == ["g1", "g2"], names
        models = _docs_models(docs)
        for g in grids:
            a = _resolved(_acts(g, _PNG)[0].callback.args, models)
            assert a["kpis"] == []  # D-53f: a KPI is an item of its own
            heads = [h if isinstance(h, str) else h.text for h in a["header"]]
            assert "T" in heads[0], heads
        assert not [m for d in docs for m in d.models
                    if isinstance(m, Div) and _acts(m, _PNG)]

    def test_by_sub_grids_keep_the_grid_alone_svg(self, tmp_path, mode):
        docs = _MODES[mode](tmp_path,
                            tt._CORPUS["a by() graph beside a graph"]())
        (top,) = _top_grids(_roots(docs))
        subs = [c[0] for c in top.children if isinstance(c[0], GridPlot)]
        subs = [s for s in subs if _acts(s, _SVG)]
        assert subs, "no by() sub-grid with a save action"
        for s in subs:
            (svg,) = _acts(s, _SVG)
            assert svg.callback.code == dr._DASH_SVG_SAVE_JS
            assert set(svg.callback.args) == {"grid", "name"}
            assert _acts(s, _PNG) == []

    def test_only_ids_and_names_reach_the_args(self, tmp_path, mode):
        """The action holds no reference to another model (a grid whose
        action held the Tabs would hold every tab's figures), only ids
        that resolve to the composite's models in the same document."""
        docs = _MODES[mode](tmp_path, tt._spec(
            [tt._graph("g1"), tt._graph("g2", [tt._LINE])],
            kpis=[tt._kpi()], filter="foreign, type(dropdown)",
            tabs="A: g2", title="T"))
        grids = _top_grids(_roots(docs))
        models = _docs_models(docs)
        assert grids
        for g in grids:
            for act in _acts(g, _PNG) + _acts(g, _SVG):
                raw = act.callback.args
                assert set(raw) == _ARG_KEYS
                for k, v in raw.items():
                    if k != "grid":
                        flat = v if isinstance(v, list) else [v]
                        assert all(isinstance(x, str) for x in flat), k
                assert all(i in models for k in ("header_ids", "widget_ids",
                                                 "kpi_ids", "table_ids")
                           for i in raw[k] if i)
                a = _resolved(raw, models)
                assert isinstance(raw["name"], str)
                assert len(a["header"]) == 2
                assert all(isinstance(h, (Div, str)) for h in a["header"])
                assert all(isinstance(w, (InputWidget, AbstractSlider))
                           for w in a["widgets"])
                assert a["tabs"] is None or isinstance(a["tabs"], Tabs)
                assert all(isinstance(k, Div) for k in a["kpis"])
                assert all(isinstance(t, DataTable) for t in a["tables"])


class TestTheHelpers:

    def test_the_walk_order_and_the_grid_flag(self):
        from bokeh.layouts import column
        a, b, c = tsvg._fig(), tsvg._fig(), tsvg._fig()
        sub = gridplot([[b]])
        top = gridplot([[a, sub]])
        root = column(Div(text="h"), top, c)
        got = [("Figure" if isinstance(m, Plot) else type(m).__name__,
                inside) for m, inside in dr._dash_layout_walk(root)]
        assert got == [("Column", False), ("Div", False),
                       ("GridPlot", False), ("Figure", True),
                       ("GridPlot", True), ("Figure", True),
                       ("Figure", False)], got
        assert list(dr._dash_layout_walk(None)) == []

    def test_add_composites_returns_the_top_grids(self):
        from bokeh.layouts import column
        sub = dr._dash_name_save(gridplot([[tsvg._fig()]]), "g1")
        top = dr._dash_name_save(gridplot([[tsvg._fig(), sub]]))
        head = dr._dash_header_models("T", "S")
        sel = Select(title="f", options=["a"], value="a")
        root = column(*head, sel, top)
        assert dr._dash_add_composites([root]) == [top]
        (png,) = _acts(top, _PNG)
        a = png.callback.args
        assert a["header_ids"] == [h.id for h in head]
        assert a["widget_ids"] == [sel.id]
        assert _acts(sub, _PNG) == []
        assert dr._dash_add_composites([root], header=("X", None))[0] is top
        a = _acts(top, _PNG)[0].callback.args
        assert (a["header"], a["header_ids"]) == (["X", ""], ["", ""])
        assert dr._dash_add_composites([]) == []


class TestTheConstants:

    def test_the_code_is_fixed_and_plain(self):
        for js in (dr._DASH_COMPOSITE_JS, dr._DASH_COMPOSITE_SAVE_JS):
            for bad in ("eval(", "innerHTML", "fetch(", "DOMParser",
                        "querySelector"):
                assert bad not in js, bad
        assert 'export("png")' in dr._DASH_COMPOSITE_JS
        assert "toBlob" in dr._DASH_COMPOSITE_JS
        assert "function dash_html_escape(" in dr._DASH_COMPOSITE_JS
        # the grid-alone path of the SVG action is unchanged below the branch
        assert dr._DASH_SVG_SAVE_JS.lstrip().startswith(
            'if (typeof header !== "undefined" && header !== null)')

    def test_the_icon_is_a_small_data_uri(self):
        import base64
        icon = dr._DASH_COMPOSITE_PNG_ICON
        head = "data:image/svg+xml;base64,"
        assert icon.startswith(head) and len(icon) <= 1024, len(icon)
        assert base64.b64decode(icon[len(head):]).decode().startswith("<svg")


# ---------------------------------------------------------------------------
# The layout arithmetic, under node
# ---------------------------------------------------------------------------

def _card(title="Mean mpg", value="21.30", sub="all cars", bg="", color=""):
    return dr._dash_kpi_card_html(title, value, sub, color, bg, "k1", None)


def _layout(models, grid_w=1200, grid_h=600):
    src = dr._DASH_COMPOSITE_JS + r"""
const m = %s;
const lay = dash_composite_layout(m, %d, %d, (t, f) => 7 * t.length);
console.log(JSON.stringify(lay));
""" % (json.dumps(models), grid_w, grid_h)
    return js_runner.run_js(src)


def _texts(lay):
    return [(i["text"], i["x"], i["y"], i["font"]) for i in lay["items"]
            if i["kind"] == "text"]


def _grid_item(lay):
    (g,) = [i for i in lay["items"] if i["kind"] == "grid"]
    return g


_SEL = {"type": "Select", "title": "foreign", "value": "1",
        "options": [["0", "Domestic"], ["1", "Foreign"]]}
_RNG = {"type": "RangeSlider", "title": "mpg", "value": [12, 41]}


def _models(**kw):
    m = {"header": ['<h2 class="db-title">Cars &amp; co</h2>',
                    '<p class="db-subtitle">1978</p>'],
         "widgets": [_SEL, _RNG],
         "tabs": {"tabs": [{"title": "A"}, {"title": "B"}], "active": 1},
         "kpis": [{"text": _card()}], "tables": []}
    m.update(kw)
    # a Div is a model with .text; a string stands for itself (layout(bs))
    m["header"] = [({"text": h} if h else "") for h in m["header"]]
    return m


@js_runner.requires_node
class TestTheModelLookup:

    def test_ids_resolve_in_the_grids_document(self):
        out = js_runner.run_js(dr._DASH_COMPOSITE_JS + r"""
const ms = {h1: {text: "T"}, w1: {title: "f"}, t1: {tabs: []}, k1: {text: "k"},
            g1: {visible: true}};
const grid = {document: {get_model_by_id: (i) => ms[i]}};
const m = dash_composite_models(grid, ["", "raw sub"], ["h1", ""], ["w1", "zz"],
                                "t1", ["k1"], ["g1"]);
const none = dash_composite_models(grid, ["A", ""], ["", ""], [], "", [], []);
console.log(JSON.stringify([m, none]));
""")
        m, none = out
        assert m["header"] == [{"text": "T"}, "raw sub"]
        assert m["widgets"] == [{"title": "f"}]  # an unknown id is dropped
        assert m["tabs"] == {"tabs": []} and m["kpis"] == [{"text": "k"}]
        assert m["tables"] == [{"visible": True}]
        assert none == {"header": ["A", ""], "widgets": [], "tabs": None,
                        "kpis": [], "tables": []}


@js_runner.requires_node
class TestTheTextOfHtml:

    def test_each_entity_decodes_once_and_the_tags_go(self):
        """dash_text_of_html decodes the seven entities a Div's text holds,
        once each -- ``&amp;lt;`` stays the text ``&lt;`` -- and drops the
        tags.  Its table is keyed by the entity's name (batch-18 gate): an
        entity spelled out in the code reached the page's JSON escaped a
        second time, which the title-escaping scans read as double escaping
        (test_axis_options TestDashboardTitleEscaping)."""
        out = js_runner.run_js(dr._DASH_COMPOSITE_JS + r"""
console.log(JSON.stringify(dash_text_of_html(
  "<b>R&amp;D &lt;x&gt; &quot;q&quot; Men&#x27;s &#39;a&#39;&nbsp;z</b> &amp;lt;")));
""")
        assert out == "R&D <x> \"q\" Men's 'a' z &lt;"
        for ent in ("&amp;", "&lt;", "&gt;", "&quot;", "&#x27;", "&#39;",
                    "&nbsp;"):
            assert ent not in dr._DASH_COMPOSITE_JS.replace(
                dr._DASH_FMT_JS[dr._DASH_FMT_JS.index(
                    "function dash_html_escape("):dr._DASH_FMT_JS.index(
                    "function dash_civil_from_days(")], ""), ent


@js_runner.requires_node
class TestTheLayoutArithmetic:

    def test_header_then_filters_then_tabs_then_cards_then_grid(self):
        lay = _layout(_models())
        t = _texts(lay)
        assert t[0] == ("Cars & co", 16, 36, "bold 20px sans-serif")
        assert t[1] == ("1978", 16, 58, "14px sans-serif")
        assert t[2] == ("foreign: Foreign", 16, 79, "13px sans-serif")
        assert t[3] == ("mpg: 12 - 41", 16 + 16 * 7 + 24, 79,
                        "13px sans-serif")
        assert t[4] == ("A", 16, 104, "14px sans-serif")
        assert t[5] == ("B", 47, 104, "bold 14px sans-serif")
        (line,) = [i for i in lay["items"] if i["kind"] == "line"]
        assert (line["x1"], line["x2"], line["y1"]) == (47, 54, 108)
        (card,) = [i for i in lay["items"] if i["kind"] == "card"]
        assert (card["x"], card["y"], card["w"], card["h"]) == (
            16, 118, 220, 110)
        assert t[6] == ("Mean mpg", 126, 138, "13px sans-serif")
        assert t[7] == ("21.30", 126, 180, "bold 36px sans-serif")
        assert t[8] == ("all cars", 126, 210, "11px sans-serif")
        g = _grid_item(lay)
        assert (g["x"], g["y"], g["w"], g["h"]) == (0, 244, 1200, 600)
        assert (lay["W"], lay["H"]) == (1200, 244 + 600 + 16)

    def test_filters_wrap_at_the_width(self):
        long = [{"type": "Select", "title": "x" * 32, "value": "a",
                 "options": ["a"]} for _ in range(4)]
        lay = _layout(_models(widgets=long, tabs=None, kpis=[],
                              header=["", ""]), grid_w=300)
        assert lay["W"] == 960
        t = _texts(lay)
        # "x...x: a" is 35 characters, 245 px
        assert [(x, y) for _s, x, y, _f in t] == [
            (16, 29), (285, 29), (554, 29), (16, 49)]
        assert _grid_item(lay)["y"] == 16 + 20 + 24

    def test_card_rows_fill_then_wrap(self):
        lay = _layout(_models(kpis=[{"text": _card()}] * 5, widgets=[],
                              tabs=None, header=["", ""]), grid_w=900)
        cards = [(i["x"], i["y"]) for i in lay["items"]
                 if i["kind"] == "card"]
        n = (960 - 32 + 16) // (220 + 16)
        assert n == 4
        assert cards == [(16 + k * 236, 16) for k in range(4)] + [(16, 142)]
        assert _grid_item(lay)["y"] == 16 + 2 * 126

    def test_no_tabs_no_header_collapses(self):
        lay = _layout(_models(header=["", ""], widgets=[], tabs=None,
                              kpis=[], tables=[]), grid_w=1000,
                      grid_h=400)
        assert [i["kind"] for i in lay["items"]] == ["grid"]
        assert _grid_item(lay)["y"] == 16
        assert (lay["W"], lay["H"]) == (1000, 16 + 400 + 16)

    def test_values_are_the_current_ones(self):
        sel = dict(_SEL, value="0")
        multi = {"type": "MultiChoice", "title": "rep78",
                 "value": ["3", "5"],
                 "options": [["3", "Three"], ["4", "Four"], ["5", "Five"]]}
        cards = [{"text": _card(value="9.99")}]
        lay = _layout(_models(widgets=[sel, multi], kpis=cards, tabs=None))
        got = [s for s, _x, _y, _f in _texts(lay)]
        assert "foreign: Domestic" in got
        assert "rep78: Three, Five" in got
        assert "9.99" in got

    # Flipped: D39 (D-53d) -- an open data table is drawn over its place
    # in the grid's image; the "Data tables are not included" caption is
    # gone.
    def test_open_tables_are_drawn_over_the_grid(self):
        box = {"x": 100, "y": 300, "w": 400, "h": 103,
               "titles": ["Mileage (mpg)", "w" * 80],
               "rows": [["22", "2,930"], ["17", "3,350"], ["25", "2,200"],
                        ["30", "1,800"]]}
        none = _layout(_models(tables=[]))
        lay = _layout(_models(tables=[box]))
        assert "Data tables are not included" not in [
            s for s, *_r in _texts(lay)]
        g = _grid_item(lay)
        assert g["y"] == _grid_item(none)["y"]
        assert (lay["W"], lay["H"]) == (none["W"], none["H"])
        kinds = [i["kind"] for i in lay["items"]]
        # painted after the grid's image, so over it
        assert kinds.index("rect") > kinds.index("grid")
        (rect,) = [i for i in lay["items"] if i["kind"] == "rect"]
        assert (rect["x"], rect["y"], rect["w"], rect["h"]) == (
            100, g["y"] + 300, 400, 103)
        assert rect["fill"] == "#ffffff"
        t = [x for x in _texts(lay) if x[2] > g["y"]]
        y0 = g["y"] + 300
        assert t[0] == ("Mileage (mpg)", 106, y0 + 19,
                        "bold 13px sans-serif")
        # a column is 200 px: the long title is cut to 188 px with "..."
        assert t[1][0].endswith("...") and 7 * len(t[1][0]) <= 188, t[1]
        assert t[1][1] == 306
        # (103 - 28) // 25 = 3 rows fit; the fourth is not drawn
        assert [x[0] for x in t[2:]] == ["22", "2,930", "17", "3,350",
                                         "25", "2,200"]
        assert [x[2] for x in t[2:]] == [y0 + 45] * 2 + [y0 + 70] * 2 + [
            y0 + 95] * 2
        assert {x[3] for x in t[2:]} == {"13px sans-serif"}

    def test_the_table_boxes_come_from_the_views(self):
        """dash_composite_tables reads each shown table's place against
        the grid's and its rows from the table's own source and view
        filter -- never from the page's DOM text."""
        out = js_runner.run_js(dr._DASH_COMPOSITE_JS + r"""
const rect = (l, t, w, h) => ({left: l, top: t, width: w, height: h,
                               right: l + w, bottom: t + h});
const views = new Map();
const mk = (r) => ({el: {isConnected: true, getBoundingClientRect: () => r}});
const src = {data: {a: ["x0", "x1", "x2"], b: [10, 11, 12]}};
const cols = [{field: "a", title: "A"}, {field: "b", title: "B"}];
const t1 = {visible: true, source: src, columns: cols,
            view: {filter: {indices: [2, 0]}}};
const t2 = {visible: false, source: src, columns: cols, view: null};
const t3 = {visible: true, source: src, columns: cols, view: null};
const t4 = {visible: true, source: src, columns: cols, view: null};
views.set(t1, mk(rect(110, 220, 300, 400)));
views.set(t2, mk(rect(110, 220, 300, 400)));
views.set(t3, mk(rect(5000, 220, 300, 100)));
views.set(t4, mk(rect(110, 220, 0, 0)));
globalThis.Bokeh = {index: {find_one: (m) => views.get(m) || null}};
const grid = mk(rect(10, 20, 1000, 800));
console.log(JSON.stringify(dash_composite_tables(grid, [t1, t2, t3, t4, null])));
""")
        assert out == [{"x": 100, "y": 200, "w": 300, "h": 400,
                        "titles": ["A", "B"],
                        "rows": [["x2", "12"], ["x0", "10"]]}]


# ---------------------------------------------------------------------------
# The SVG writer, under node
# ---------------------------------------------------------------------------

_GRID_SVG = ('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" '
             'width="1200" height="600"><path d="M0 0"/></svg>')


def _svg(models, grid_svg=_GRID_SVG):
    src = dr._DASH_COMPOSITE_JS + r"""
const lay = dash_composite_layout(%s, 1200, 600, (t, f) => 7 * t.length);
console.log(JSON.stringify(dash_composite_svg(lay, %s)));
""" % (json.dumps(models), json.dumps(grid_svg))
    return js_runner.run_js(src)


def _svg_items(items):
    src = dr._DASH_COMPOSITE_JS + r"""
console.log(JSON.stringify(dash_composite_svg(%s, "<svg></svg>")));
""" % json.dumps({"W": 960, "H": 300, "items": items})
    return js_runner.run_js(src)


@js_runner.requires_node
class TestTheSvgWriter:

    def test_escapes_every_text(self):
        bad = '<b>&"x'
        esc = '&lt;b&gt;&amp;&quot;x'
        sel = {"type": "Select", "title": bad, "value": "1",
               "options": [["1", bad]]}
        out = _svg(_models(header=['<h2 class="db-title">%s</h2>' % esc, ""],
                           widgets=[sel], kpis=[{"text": _card(title=bad,
                                                               value=bad)}]))
        bodies = re.findall(r"<text\b[^>]*>(.*?)</text>", out)
        assert len(bodies) >= 4, bodies
        for b in bodies:
            assert "<" not in b and '"' not in b, b
            assert not re.search(r"&(?!amp;|lt;|gt;|quot;|#x27;)", b), b
        assert esc in out
        assert "<b>" not in out

    def test_attribute_values_are_escaped(self):
        items = [
            {"kind": "card", "x": 1, "y": 2, "w": 3, "h": 4,
             "fill": '" onload="x'},
            {"kind": "text", "x": 5, "y": 6, "text": "v",
             "font": "13px sans-serif", "color": "url(javascript:1)",
             "align": "left"},
            {"kind": "text", "x": '7" onclick="y', "y": 8, "text": "w",
             "font": '13px" onload="z', "color": "#1a2b3c", "align": "x\""},
        ]
        out = _svg_items(items)
        assert "onload" not in out and "onclick" not in out
        assert "javascript" not in out
        assert 'fill="#ffffff"' in out and 'fill="#000000"' in out
        assert 'fill="#1a2b3c"' in out
        for attr in re.findall(r'\w[\w-]*="([^"]*)"', out):
            assert "<" not in attr, attr
        for ok in ("#1a2b3c", "#1a2b3c80", "steelblue"):
            got = _svg_items([{"kind": "card", "x": 0, "y": 0, "w": 1,
                               "h": 1, "fill": ok}])
            assert 'fill="%s"' % ok in got, ok

    def test_translate_of_the_grid(self):
        out = _svg(_models(header=["", ""], widgets=[], tabs=None, kpis=[],
                           tables=[]))
        assert out.startswith('<svg xmlns="http://www.w3.org/2000/svg" '
                              'width="1200" height="632"')
        assert ('<g transform="translate(0,16)"><svg xmlns="http://www.w3.org'
                '/2000/svg" width="1200" height="600"><path d="M0 0"/></svg>'
                '</g>') in out
        assert "<?xml" not in out


class TestTheBundle:
    """Guard: the BokehJS calls the composite makes are in the shipped
    bundle (_DASH_BOKEH_INTERNALS)."""

    def test_the_calls_exist_in_the_shipped_bokehjs(self):
        from bokeh.util.paths import bokehjs_path
        path = os.path.join(str(bokehjs_path()), "js", "bokeh.min.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        for need in ("find_one", "to_blob", "export(", "canvas"):
            assert need in js, need
        rows = [r for r in dr._DASH_BOKEH_INTERNALS
                if "_DASH_COMPOSITE_JS" in r[0]]
        assert len(rows) == 1 and rows[0][2].startswith(
            "test/test_export_composite.py::TestTheBundle")


# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------

class TestPrint:

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_stylesheet_and_hook_present_both_modes(self, tmp_path, layout):
        spec = tt._spec([tt._graph("g1"), tt._graph("g2", [tt._LINE])],
                        filter="foreign, type(dropdown)", layout=layout)
        _r, page = tt._saved(tmp_path, spec)
        assert page.count("beforeprint") == 1
        assert page.count("@media print") >= 1
        assert "window.onerror = function" in page  # S52's hook beside it
        # the page-level rules name layout(bs)'s own markup only
        assert (".db-container { width: 1000px" in page) == (layout == "bs")
        doc, _ns, _src = tt._served(tmp_path, spec)
        cbs = doc.callbacks._js_event_callbacks["document_ready"]
        assert [c.code for c in cbs].count(dr._DASH_PRINT_HOOK_JS) == 1
        assert cbs[-1].name == "dash_print"

    def test_the_css_is_fixed_text(self):
        css = dr._DASH_PRINT_CSS
        assert css.startswith("@media print {")
        assert ".bk-root" not in css
        assert "1000px" in css and ".db-container" in css
        assert ".db-filter-bar" in css
        assert dr._DASH_PRINT_HIDE_CSS == (
            "@media print { :host { display: none !important; } }")

    def test_toolbars_and_filters_hide(self, tmp_path):
        spec = tt._spec([tt._graph("g1"), tt._graph("g2", [tt._LINE])],
                        filter="foreign, type(dropdown)")
        doc, _ns, _src = tt._served(tmp_path, spec)
        (g,) = _top_grids(doc.roots)
        hide = [s for s in g.toolbar.stylesheets
                if isinstance(s, InlineStyleSheet)
                and s.css == dr._DASH_PRINT_HIDE_CSS]
        assert len(hide) == 1
        (sel,) = [m for m in doc.models if isinstance(m, Select)]
        assert hide[0] in sel.stylesheets

    def test_the_print_models(self):
        fig = figure(tools=dr._DASH_FIGURE_TOOLS)
        root = gridplot([[fig]])
        sheet, hook = dr._dash_print_models([root])
        assert sheet is None and isinstance(hook, CustomJS)
        assert hook.args["roots"] == [root] and hook.name == "dash_print"
        (hide,) = root.toolbar.stylesheets
        assert hide.css == dr._DASH_PRINT_HIDE_CSS
        item = gridplot([[figure(tools=dr._DASH_FIGURE_TOOLS)]])
        css, hook2 = dr._dash_print_models([item], fixed=False)
        assert css == dr._DASH_PRINT_CSS
        assert hook2.args["roots"] == [] and item.stylesheets == []

    @js_runner.requires_node
    def test_the_hook_restores(self):
        out = js_runner.run_js(r"""
const L = {};
globalThis.window = {addEventListener(t, f) { L[t] = f; }};
const r = {sizing_mode: "stretch_width", width: null};
new Function("roots", %s)([r]);
L.beforeprint();
const during = [r.sizing_mode, r.width];
L.afterprint();
console.log(JSON.stringify([during, [r.sizing_mode, r.width]]));
""" % json.dumps(dr._DASH_PRINT_HOOK_JS))
        assert out == [["fixed", 1000], ["stretch_width", None]]


# ---------------------------------------------------------------------------
# In Chrome
# ---------------------------------------------------------------------------

#: Capture every blob the page turns into a URL (its type, size and, for
#: text, its body) and every download's name.
_CAPTURE_JS = r"""
(() => {
  window.__blobs = []; window.__dl = []; window.__alerts = [];
  if (window.__hooked) return 0;
  window.__hooked = true;
  const make = URL.createObjectURL.bind(URL);
  URL.createObjectURL = (b) => {
    const e = {type: b.type, size: b.size, text: null, w: 0, h: 0};
    window.__blobs.push(e);
    if (b.type === "image/png") {
      createImageBitmap(b).then(bm => { e.w = bm.width; e.h = bm.height;
                                        e.text = ""; });
    } else { b.text().then(t => { e.text = t; }); }
    return make(b);
  };
  HTMLAnchorElement.prototype.click = function () {
    window.__dl.push(this.download); };
  window.alert = (m) => { window.__alerts.push(String(m)); };
  return 0;
})()
"""

_DONE_JS = ("JSON.stringify(window.__blobs.length > 0 && "
            "window.__blobs.every(e => e.text !== null))")


def _run_action(p, tag, timeout=30):
    p._eval(_CAPTURE_JS)
    p.in_task("__dash_models('CustomAction').filter(a => a.tags.includes("
              "'%s'))[0].do.emit(undefined);" % tag)
    end = time.time() + timeout
    while time.time() < end and not p.read(_DONE_JS):
        time.sleep(0.2)
    blobs = p.read("JSON.stringify(window.__blobs)")
    dl = p.read("JSON.stringify(window.__dl)")
    assert len(blobs) == 1 and len(dl) == 1, (
        blobs, dl, p.read("JSON.stringify(window.__alerts)"), p.js_errors())
    return blobs[0], dl[0]


def _cb():
    import test_csp_browser
    return test_csp_browser


def _composite_spec(cb):
    return cb._spec([cb._graph("g1", [cb._scatter(mcolor="#123456")])],
                    title="TITLEX", subtitle="SUBX")


def _check_composite(p):
    png, name = _run_action(p, _PNG)
    assert name == "dashboard-full.png", name
    assert png["type"] == "image/png" and png["size"] > 10000, png
    gw = p.read("JSON.stringify((() => { const c = Bokeh.index.find_one("
                "__dash_models('GridPlot')[0]).export('png').canvas; "
                "return [c.width / (window.devicePixelRatio || 1), "
                "c.height / (window.devicePixelRatio || 1)]; })())")
    dpr = p.read("JSON.stringify(window.devicePixelRatio || 1)")
    assert png["w"] == math.ceil(max(gw[0], 960) * dpr), (png, gw)
    assert png["h"] > gw[1] * dpr, (png, gw)
    svg, name = _run_action(p, _SVG)
    assert name == "dashboard-full.svg", name
    assert svg["type"] == "image/svg+xml"
    for label in ("TITLEX", "SUBX"):
        assert re.search(r"<text\b[^>]*>%s</text>" % label,
                         svg["text"]), label
    assert '<g transform="translate(0,' in svg["text"]
    assert len(tsvg._MARK.findall(svg["text"])) == 20


@pytest.mark.release
@pytest.mark.skipif(not _CHROME, reason="headless Chrome is not installed "
                    "(set DASH_CHROME); a skip is red under DASH_STRICT=1")
class TestInChrome:

    def test_saved_composite_png_dimensions_and_text(self):
        cb = _cb()
        d, sp, dp = cb._files("composite", _composite_spec(cb),
                              cb._frame(20))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = tsvg._write(dr.DashRenderer(sp, dp).render(), "page.html")
        with cb._CspProbe(cb._url(page)) as p:
            _check_composite(p)
            assert p.violations() == [] and p.js_errors() == []

    def test_served_composite(self, tmp_path):
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        cb = _cb()
        src = tt._app_source(tmp_path, _composite_spec(cb), cb._frame(20))
        doc = tt._session(tt._load_app(src, "composite_served"))
        page = tsvg._write(file_html(list(doc.roots), INLINE, "served"),
                           "served.html")
        with cb._CspProbe(cb._url(page)) as p:
            _check_composite(p)
            assert p.js_errors() == [], p.js_errors()

    def test_an_open_table_is_drawn_in_the_composite(self):
        """D39 (D-53d): Save as SVG and Save dashboard draw an open data
        table's titles and rows where the table sits."""
        import test_data_table as tdt
        cb = _cb()
        _t, sp, dp = tdt._write(tdt._table_spec({"table": "open"}))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = tsvg._write(dr.DashRenderer(sp, dp).render(), "table.html")
        with cb._CspProbe(cb._url(page)) as p:
            svg, _name = _run_action(p, _SVG)
            texts = re.findall(r"<text\b[^>]*>([^<]*)</text>", svg["text"])
            assert "Mileage (mpg)" in texts, texts
            assert "22" in texts and "2,930" in texts, texts
            assert "Data tables are not included" not in svg["text"]
            png, _name = _run_action(p, _PNG)
            assert png["type"] == "image/png" and png["h"] > 0, png
            assert p.js_errors() == [], p.js_errors()

    def test_print_media_fixes_the_width(self):
        cb = _cb()
        with cb._CspProbe(cb._url(cb._saved_page("rich"))) as p:
            p._send("Emulation.setEmulatedMedia", {"media": "print"})
            p._eval("window.dispatchEvent(new Event('beforeprint')); 0")
            time.sleep(1.0)
            got = p.read(r"""JSON.stringify((() => {
              const root = Bokeh.documents[0].roots()[0];
              const v = Bokeh.index.find_one(root);
              const tb = __dash_models('Toolbar').filter(t => {
                const tv = Bokeh.index.find_one(t);
                return tv && tv.el.isConnected; });
              const shown = tb.filter(t => getComputedStyle(
                Bokeh.index.find_one(t).el).display !== 'none').length;
              const sel = __dash_models('Select').map(s => getComputedStyle(
                Bokeh.index.find_one(s).el).display);
              return [root.sizing_mode, Math.round(
                v.el.getBoundingClientRect().width), tb.length, shown, sel];
            })())""")
            assert got[0] == "fixed" and got[1] == 1000, got
            assert got[2] >= 1 and got[3] == 0, got
            assert got[4] and set(got[4]) == {"none"}, got
            p._eval("window.dispatchEvent(new Event('afterprint')); 0")
            p._send("Emulation.setEmulatedMedia", {"media": ""})
            time.sleep(1.0)
            after = p.read("JSON.stringify(Bokeh.documents[0].roots()[0]"
                           ".sizing_mode)")
            assert after == "stretch_width", after
            assert p.js_errors() == [], p.js_errors()

    def test_print_media_fixes_the_bs_container(self):
        cb = _cb()
        with cb._CspProbe(cb._url(cb._saved_page("bs"))) as p:
            p._send("Emulation.setEmulatedMedia", {"media": "print"})
            time.sleep(0.5)
            got = p.read(r"""JSON.stringify((() => {
              const c = document.querySelector('.db-container');
              const bars = [...document.querySelectorAll('.db-filter-bar')];
              return [Math.round(c.getBoundingClientRect().width),
                      bars.map(b => getComputedStyle(b).display)];
            })())""")
            assert got[0] == 1000, got
            assert set(got[1]) <= {"none"}, got
            p._send("Emulation.setEmulatedMedia", {"media": ""})
            time.sleep(0.5)
            assert p.read("JSON.stringify(Math.round(document.querySelector("
                          "'.db-container').getBoundingClientRect().width))"
                          ) != 1000
            assert p.violations() == [] and p.js_errors() == []
