"""dash.sthlp's Layout, Tabs, Linking and Brushing, toolbar and Filters
sections (WP-23; lines 586-797 at 4ede074), held to the code in both render
modes.

Each class pins one claim the help makes -- or the corrected claim, where
the help said something the code does not do -- so that the help and the
code cannot drift apart without a test going red.  The Stata side of the
same claims is test_help_claims_3.cscript.

Two claims were false because of defects, fixed with these tests first:

* A filter() group ended at every ``||`` and ``;`` in its text, and
  exclude() was read wherever the word stood.  Measured at 4ede074 through
  dash.ado: ``label("A;B")`` and ``label("A||B")`` stopped dash build with
  "too few quotes" r(132); ``label(A;B)`` was refused as naming a variable
  ``B)``; ``label("exclude(nosuch) me")`` was refused as an exclude() of an
  unregistered graph.  The renderer split the same text the same way, and
  read an apostrophe as a quote: given ``label(Bob's cars) exclude(g2)`` it
  titled the widget "Bob's cars) exclude(g2" and filtered g2 after all, in
  both modes, with rc 0.  A compound-quoted label kept its `" and "' on the
  widget, and ``type(range),exclude(g1)`` was read as a type of
  "range),exclude(g1", so no widget was built.  The help said the text "may
  be anything but a semicolon".
* layout(auto) read the figures' proportions when saved and not when
  served: four graphs drawn xsize(12) ysize(3) were one column of four on
  the saved page and a 2 x 2 grid served.
"""
import inspect
import math
import os
import re
import sys
import warnings

import pytest
from bokeh.models import (Div, GlyphRenderer, GridPlot, HoverTool, RangeSlider,
                          Select, Slider, Tabs, ToolProxy)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_filter_exclude as tfe  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_adversarial_matrix import _app_source  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_FIGURE = tfe._FIGURE


from conftest import render_models  # noqa: E402


def _graphs(n, **go):
    """``n`` scatter graphs g1..gn for ``tp._spec``, each titled by name."""
    return [("g%d" % i, [plot_for("scatter")], dict(go, title="g%d" % i))
            for i in range(1, n + 1)]


def _figures(root_or_renderer):
    """``{title: figure}`` of a saved renderer or a served document."""
    if isinstance(root_or_renderer, dr.DashRenderer):
        figs = root_or_renderer.figures.values()
    else:
        figs = [m for m in tp._walk_models(root_or_renderer)
                if type(m).__name__ == "figure"]
    return {f.title.text: f for f in figs}


def _grid_shape(root):
    """``(rows, cols)`` of the one GridPlot under *root* -- its filled cells;
    gridplot() leaves a None cell out."""
    grids = list(root.select({"type": GridPlot}))
    assert len(grids) == 1, "expected one grid, found %d" % len(grids)
    cells = grids[0].children
    return (max(r for _m, r, _c in cells) + 1,
            max(c for _m, _r, c in cells) + 1)


def _parse(raw):
    """``_dash_parse_filter_raw`` as ``(varname, type, exclude, label)``
    tuples, and the warnings it raised."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        got = dr._dash_parse_filter_raw(raw)
    return ([(g["varname"], g["type"], g["exclude"], g["label"]) for g in got],
            [str(w.message) for w in caught])


# ===========================================================================
# Filters: the text of a group is the user's (dash.sthlp "Filters", label())
# ===========================================================================

class TestAFilterGroupEndsOnlyOutsideItsText:
    """A ``||`` or ``;`` ends a filter() group only outside quotes and
    parentheses, and a sub-option is read only where one stands."""

    @pytest.mark.parametrize("raw,want", [
        ('foreign, type(dropdown) label("A;B")',
         [("foreign", "dropdown", [], "A;B")]),
        ("foreign, type(dropdown) label(A;B)",
         [("foreign", "dropdown", [], "A;B")]),
        ('foreign, type(dropdown) label("A||B") || price, type(range)',
         [("foreign", "dropdown", [], "A||B"), ("price", "range", [], "")]),
        ('foreign, type(dropdown) label("A | B")',
         [("foreign", "dropdown", [], "A | B")]),
        ('price, type(range) label("exclude(g9) of") exclude(g1)',
         [("price", "range", ["g1"], "exclude(g9) of")]),
        ("price, type(range) label(Bob's cars) exclude(g1)",
         [("price", "range", ["g1"], "Bob's cars")]),
        ("foreign, type(dropdown) label(`\"The \"best\" cars\"')",
         [("foreign", "dropdown", [], 'The "best" cars')]),
        ("price, type(range),exclude(g1)",
         [("price", "range", ["g1"], "")]),
        ('price, type(range) label("a ( b") exclude(g1)',
         [("price", "range", ["g1"], "a ( b")]),
    ], ids=["semicolon", "unquoted semicolon", "double bar", "single bar",
            "the word exclude(", "apostrophe", "compound quotes",
            "comma without a blank", "a quoted unbalanced parenthesis"])
    def test_the_group_is_read_whole(self, raw, want):
        got, warns = _parse(raw)
        assert got == want
        assert not warns, warns

    @pytest.mark.parametrize("raw", [
        "foreign, type(dropdown) || price, type(range) exclude(g1)",
        "foreign, type(dropdown); price, type(range) exclude(g1)",
        "foreign, type(dropdown)  ||price, type(range) exclude(g1)",
    ], ids=["double bar", "semicolon, as older specs wrote", "no blank"])
    def test_a_separator_outside_the_text_still_separates(self, raw):
        got, warns = _parse(raw)
        assert got == [("foreign", "dropdown", [], ""),
                       ("price", "range", ["g1"], "")]
        assert not warns, warns

    def test_the_splitter_is_the_one_both_modes_run(self):
        assert dr._dash_filter_split(
            'a, label("x || y; z") || b; c, label(`"q "w" e"\')', True) == [
            'a, label("x || y; z")', "b", 'c, label(`"q "w" e"\')']
        assert dr._dash_filter_split(
            'type(range) label("a b, c"),exclude(g1 g2)   x', False) == [
            "type(range)", 'label("a b, c")', "exclude(g1 g2)", "x"]
        assert dr._dash_filter_split("", True) == []
        assert dr._dash_filter_split(" || ;", True) == []

    def test_the_label_loses_one_pair_of_quotes(self):
        assert dr._dash_filter_label('"Curb weight"') == "Curb weight"
        assert dr._dash_filter_label("Curb weight") == "Curb weight"
        assert dr._dash_filter_label('`"a "b" c"\'') == 'a "b" c'
        assert dr._dash_filter_label("  `\"x\"'  ") == "x"


class TestBothModesShowTheLabelAsWritten:
    """The widget carries the label exactly, in both modes."""

    RAW = ('foreign, type(dropdown) label("Origin; or not") || '
           "price, type(range) label(Bob's cars) exclude(g2) || "
           'rep, type(range) label("A || B")')

    def test_the_widget_titles(self):
        spec = tp._spec(build_options={"filter": self.RAW}, graphs=_graphs(2))
        r, std_w = tp._standalone(spec)
        doc, srv_w = tp._served(spec)
        want = ["Origin; or not", "Bob's cars", "A || B"]
        assert [w.title for w in r.filter_widgets] == want
        assert [w.title for w in tp._widgets_of(doc)] == want
        assert not [w for w in std_w + srv_w if "filter" in w], std_w + srv_w


def _two_graphs(raw):
    """g1 and g2, scatter mpg weight, with the raw filter text *raw*."""
    return {"graphs": [tfe._graph("g1"), tfe._graph("g2")], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "", "filter": raw,
                              "registry": "g1 g2"}}


class TestAnApostropheInALabelLeavesExcludeAlone:
    """label(Bob's cars) exclude(g2): a price move leaves g2 alone."""

    RAW = "price, type(range) label(Bob's cars) exclude(g2)"
    MOVE = (4000.0, 5000.0)

    def test_saved(self, tmp_path):
        before, after, r, _ = tfe._saved(tmp_path, _two_graphs(self.RAW),
                                         self.MOVE)
        assert [w.title for w in r.filter_widgets] == ["Bob's cars"]
        assert before == {"g1": 10, "g2": 10}
        assert after == {"g1": 5, "g2": 10}

    def test_served(self, tmp_path):
        before, after = tfe._served(tmp_path, _two_graphs(self.RAW), "range",
                                    self.MOVE)
        assert before == {"g1": 10, "g2": 10}
        assert after == {"g1": 5, "g2": 10}


class TestAdversarialFilterText:
    """The filter() text surface, attacked three ways (CLAUDE.md rule 18):
    a label that tries to add a group that escapes validation, a label that
    tries to inject a sub-option, and text built to exhaust the reader."""

    def test_bypass_a_label_cannot_add_a_group(self):
        got, warns = _parse('foreign, label("x || nosuchvar, type(range); '
                            '1bad") type(dropdown)')
        assert got == [("foreign", "dropdown", [],
                        "x || nosuchvar, type(range); 1bad")]
        assert not warns

    def test_injection_a_label_cannot_exclude_a_graph(self, tmp_path):
        """exclude(g2) written inside the quoted label is text: a price move
        filters g2 in both modes."""
        raw = 'price, type(range) label("a) exclude(g2) label(b")'
        got, _ = _parse(raw)
        assert got == [("price", "range", [], "a) exclude(g2) label(b")]
        _, s_after, _, _ = tfe._saved(tmp_path, _two_graphs(raw),
                                      (4000.0, 5000.0))
        _, v_after = tfe._served(tmp_path, _two_graphs(raw), "range",
                                 (4000.0, 5000.0))
        assert s_after == v_after == {"g1": 5, "g2": 5}

    def test_exhaustion_a_huge_label_is_read_in_linear_time(self):
        import time
        body = "a;b||c(d)e`f' g;h||(i) " * 5000
        raw = 'foreign, type(dropdown) label("%s") || price' % body
        t0 = time.perf_counter()
        got, _ = _parse(raw)
        took = time.perf_counter() - t0
        assert [g[0] for g in got] == ["foreign", "price"]
        assert got[0][3] == body.strip()
        assert took < 5.0, took


class TestTheCopiedParserBringsItsHelpers:
    def test_the_app_carries_them(self, tmp_path):
        """A structural guard over the app's text, deliberately: the filter
        text helpers are the renderer's own, copied verbatim.  (Measured,
        WP-24: nothing in the app calls these copies -- the served filters
        are parsed at build time by the renderer -- so what this pins is
        text the app carries, not text it runs.)"""
        src = _app_source(tmp_path, _two_graphs("price, type(range)"))
        for fn in (dr._dash_filter_split, dr._dash_filter_label,
                   dr._dash_parse_filter_raw):
            assert inspect.getsource(fn).strip() in src, fn.__name__


# ===========================================================================
# Filters: the rest of the section
# ===========================================================================

class TestADropdownIsTheTypeWhenNoneIsGiven:
    """filter(foreign) builds the dropdown, opening on All, in both modes."""

    def test_both_modes(self):
        spec = tp._spec(build_options={"filter": "foreign"}, graphs=_graphs(1))
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for w in (r.filter_widgets, tp._widgets_of(doc)):
            assert len(w) == 1 and isinstance(w[0], Select)
            assert w[0].options[0] == ("__all__", "All")
            assert w[0].value == "__all__"


class TestARangeKeepsBothOfItsEnds:
    """type(range) keeps lo <= x <= hi, both ends included, in both modes:
    of the ten prices, 4099, 4453, 4749 and 4816 lie in [4099, 4816]."""

    SPEC = {"graphs": [tfe._graph("g1")], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "",
                              "filters": [{"varname": "price",
                                           "type": "range"}],
                              "registry": "g1"}}

    def test_saved(self, tmp_path):
        _, after, _, _ = tfe._saved(tmp_path, self.SPEC, (4099.0, 4816.0))
        assert after == {"g1": 4}

    def test_served(self, tmp_path):
        _, after = tfe._served(tmp_path, self.SPEC, "range", (4099.0, 4816.0))
        assert after == {"g1": 4}


class TestAMovedFilterDropsAMissingValue:
    """The served recompute's mask (the saved page's is pinned in
    test_export.py): at its full extent a range keeps a missing value,
    moved it drops one; a slider likewise."""

    class _W:
        def __init__(self, kind, value, start, end):
            self._dash_var, self._dash_ftype = "x", kind
            self.value, self.start, self.end = value, start, end

    def test_the_served_mask(self):
        import pandas as pd
        df = pd.DataFrame({"x": [1.0, float("nan"), 3.0, 4.0]})
        m = dr._dash_frame_filter_mask
        assert m(df, [self._W("range", (1.0, 4.0), 1.0, 4.0)]).tolist() == [
            True, True, True, True]
        assert m(df, [self._W("range", (1.0, 3.5), 1.0, 4.0)]).tolist() == [
            True, False, True, False]
        assert m(df, [self._W("slider", 1.0, 1.0, 4.0)]).tolist() == [
            True, True, True, True]
        assert m(df, [self._W("slider", 2.0, 1.0, 4.0)]).tolist() == [
            False, False, True, True]


def _kpi_card(name, stat="count", var="mpg"):
    return {"name": name, "stat": stat, "var": var, "fmt": "%9.0f",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter", "if_expr": "", "in_expr": ""}


def _card_value(text, name):
    m = re.search(r'id="kpi_val_%s"[^>]*>([^<]*)<' % re.escape(name),
                  text or "")
    return m.group(1) if m else None


# The saved page's filter callback under node (test/js_runner.py, WP-28
# S03): a dry run, reporting each Div's text as well as each source's rows.

def _run_saved(args, code):
    """``(rows by source id, text by Div id)`` after *code* ran."""
    out = js_runner.JsSession([]).run_code(code, args, commit=False)
    sources, divs = {}, {}
    for mid, state in out.items():
        if "data" in state:
            cols = list(state["data"].keys())
            rows = len(state["data"][cols[0]]) if cols else 0
            sources[mid] = {"rows": rows,
                            "ids": state["data"].get(dr._ROW_ID_COLUMN)}
        elif "text" in state:
            divs[mid] = state["text"]
    return sources, divs


class TestAKpiCardCanBeExcluded:
    """filter(price, ... exclude(k1)): a price move leaves card k1 alone and
    recounts k2, in both modes."""

    SPEC = {"graphs": [tfe._graph("g1")],
            "kpis": [_kpi_card("k1"), _kpi_card("k2")],
            "build_options": {
                "layout": "auto", "link": "", "theme": "", "title": "",
                "subtitle": "", "registry": "g1 k1 k2",
                "filters": [{"varname": "price", "type": "range",
                             "exclude": ["k1"]}]}}
    MOVE = (4000.0, 5000.0)

    def test_saved(self, tmp_path):
        sp, dp = tfe._write_inputs(tmp_path, self.SPEC)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [w], [cb] = r.filter_widgets, r.filter_callbacks
        w.value = self.MOVE
        _, divs = _run_saved(cb.args, cb.code)
        k1, k2 = r.kpi_divs["k1"], r.kpi_divs["k2"]
        assert _card_value(divs.get(k1.id, k1.text), "k1") == "10"
        assert _card_value(divs[k2.id], "k2") == "5"

    def test_served(self, tmp_path):
        from bokeh.document import Document
        sp, dp = tfe._write_inputs(tmp_path, self.SPEC)
        app = os.path.join(str(tmp_path), "app_kx.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = tfe._load_app(fh.read(), "hc3_kx")
        doc = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)
            [w] = list(doc.select({"type": RangeSlider}))
            tp._fire(w, self.MOVE)
        cards = {n: _card_value(d.text, n) for d in doc.select({"type": Div})
                 for n in ("k1", "k2") if _card_value(d.text, n)}
        assert cards == {"k1": "10", "k2": "5"}


class TestAnExcludedMemberOfALinkGroupIsFilteredWithIt:
    """link(g1 g2) and exclude(g1): g1 draws from the group's one source,
    so a move filters it with g2, in both modes; exclude(g1 g2) leaves
    both alone (test_filter_exclude.py)."""

    def _spec(self):
        return tfe._spec([tfe._graph("g1"), tfe._graph("g2")], "dropdown",
                         ["g1"], link="g1 g2")

    def test_saved(self, tmp_path):
        _, after, _, _ = tfe._saved(tmp_path, self._spec(), 1.0)
        assert after == {"g1": 5, "g2": 5}

    def test_served(self, tmp_path):
        _, after = tfe._served(tmp_path, self._spec(), "dropdown", 1.0)
        assert after == {"g1": 5, "g2": 5}


class TestAnExclusionHoldsAgainstEveryMove:
    """What dash.sthlp documents of exclude() (Filters): each graph and
    card is redrawn on every move from the rows kept by the filters that
    do not exclude it, so its state depends only on the widgets.

    Rewritten from TestExcludeHoldsWhileItsOwnFilterMoves (GAPS2 E2): at
    91d97be an excluded graph kept whatever the last move of ANOTHER
    filter wrote (price, foreign, price back gave g1=3, g2=5, k1=3 where
    the widgets imply 5).  foreign == 1 keeps 5 of the 10 rows; with price
    in [4000, 5000] as well, 3 remain.  k1 counts mpg.
    """

    SPEC = {"graphs": [tfe._graph("g1"), tfe._graph("g2")],
            "kpis": [_kpi_card("k1")],
            "build_options": {
                "layout": "auto", "link": "", "theme": "", "title": "",
                "subtitle": "", "registry": "g1 g2 k1",
                "filters": [{"varname": "foreign", "type": "dropdown"},
                            {"varname": "price", "type": "range",
                             "exclude": ["g1", "k1"]}]}}
    PRICE = (4000.0, 5000.0)
    STATES = [{"g1": 10, "g2": 5, "k1": "10"}, {"g1": 5, "g2": 3, "k1": "5"},
              {"g1": 5, "g2": 5, "k1": "5"}, {"g1": 10, "g2": 10, "k1": "10"}]

    def test_saved(self, tmp_path):
        sp, dp = tfe._write_inputs(tmp_path, self.SPEC)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        (w_for, w_price), (cb_for, cb_price) = (r.filter_widgets,
                                                r.filter_callbacks)
        s = js_runner.JsSession(r.filter_callbacks)
        k1 = r.kpi_divs["k1"]

        def state():
            out = {f.title.text: tfe._rows(tfe._renderer_source(f))
                   for f in r.figures.values()}
            out["k1"] = _card_value(k1.text, "k1")
            return out

        full = (w_price.start, w_price.end)
        got = []
        for w, cb, v in ((w_price, cb_price, self.PRICE),
                         (w_for, cb_for, 1.0), (w_price, cb_price, full),
                         (w_for, cb_for, w_for._dash_sentinel)):
            s.set(w, v)
            s.run(cb)
            got.append(state())
        assert got == self.STATES

    def test_served(self, tmp_path):
        from bokeh.document import Document
        sp, dp = tfe._write_inputs(tmp_path, self.SPEC)
        app = os.path.join(str(tmp_path), "app_excl.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = tfe._load_app(fh.read(), "hc3_excl")
        doc = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)

        def state():
            s = tfe._served_rows(doc)
            s.update({"k1": v for v in (_card_value(d.text, "k1")
                                        for d in doc.select({"type": Div}))
                      if v})
            return s

        [w_for] = list(doc.select({"type": Select}))
        [w_price] = list(doc.select({"type": RangeSlider}))
        full = (w_price.start, w_price.end)
        got = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for w, v in ((w_price, self.PRICE), (w_for, 1.0),
                         (w_price, full), (w_for, w_for._dash_sentinel)):
                tp._fire(w, v)
                got.append(state())
        assert got == self.STATES


# ===========================================================================
# Layout
# ===========================================================================

class TestTheAutomaticGridIsOneRuleInBothModes:
    """layout(auto): ceil(sqrt(n)) columns for n items; one column when a
    figure is at least three times as wide as it is tall, and one column
    fewer when one is at least 1.8 times as wide.  Rows follow."""

    @pytest.mark.parametrize("n", [2, 3, 4, 5, 7])
    @pytest.mark.parametrize("shape,go", [
        ("the scheme's", {}),
        ("four times as wide", {"xsize": "12", "ysize": "3"}),
        ("twice as wide", {"xsize": "8", "ysize": "4"}),
    ])
    def test_the_same_grid(self, n, shape, go):
        spec = tp._spec(graphs=_graphs(n, **go))
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        base = math.ceil(math.sqrt(n))
        cols = {"the scheme's": base, "four times as wide": 1,
                "twice as wide": max(1, base - 1)}[shape]
        want = (math.ceil(n / cols), cols)
        assert _grid_shape(r._last_layout_root) == want, "saved"
        assert _grid_shape(doc.roots[0]) == want, "served"

    def test_the_rule(self):
        class _F:
            def __init__(self, ar):
                self.aspect_ratio = ar
        assert dr._dash_auto_grid_cols(0) == 1
        assert [dr._dash_auto_grid_cols(n) for n in range(1, 11)] == [
            1, 2, 2, 2, 3, 3, 3, 3, 3, 4]
        assert dr._dash_auto_grid_cols(9, {"a": _F(1.375)}) == 3
        assert dr._dash_auto_grid_cols(9, {"a": _F(1.0), "b": _F(1.8)}) == 2
        assert dr._dash_auto_grid_cols(9, {"a": _F(3.0)}) == 1
        assert dr._dash_auto_grid_cols(2, {"a": _F(2.0)}) == 1
        assert dr._dash_auto_grid_cols(4, {"a": _F(None)}) == 2

    def test_the_app_carries_the_rule_verbatim(self, tmp_path):
        """A structural guard over the app's text, deliberately: ONE
        automatic-grid rule, the renderer's, copied verbatim and called
        where the served grid is built.  What the rule draws is
        TestTheAutomaticGridIsOneRuleInBothModes."""
        src = _app_source(tmp_path, _two_graphs(""))
        assert inspect.getsource(dr._dash_auto_grid_cols).strip() in src
        assert "_dash_auto_grid_cols(len(grid_names), figures)" in src


class TestItemsFillTheGridInRegistryOrder:
    """Graphs and KPI cards alike, in both modes: k1 registered between g1
    and g2 takes the second cell."""

    def test_both_modes(self):
        spec = tp._spec(graphs=_graphs(2), kpis=[tp._kpi("k1")],
                        build_options={"registry": "g1 k1 g2"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for root in (r._last_layout_root, doc.roots[0]):
            [grid] = list(root.select({"type": GridPlot}))
            order = sorted(grid.children, key=lambda t: (t[1], t[2]))
            kinds = ["kpi" if isinstance(m, Div) else m.title.text
                     for m, _r, _c in order]
            assert kinds == ["g1", "kpi", "g2"]


class TestAnExplicitGridDrawsTheCellsItsItemsReach:
    """layout(2 3): items fill it row by row; a cell no item reaches is
    empty, and a row or column after the last item is not drawn.  gridplot()
    leaves an empty cell out of the GridPlot, and with its rows unset and
    its cols one track size for every column (_dash_reflow's
    minmax(0, 1fr), TR-27.2) BokehJS sizes the CSS grid to the cells that
    are there (CSSGridBoxView._update_layout: nrows, ncols = the largest
    row and column + 1) -- so two items take one row of two columns."""

    @pytest.mark.parametrize("n,cells", [
        (2, {(0, 0), (0, 1)}),
        (4, {(0, 0), (0, 1), (0, 2), (1, 0)}),
    ])
    def test_both_modes(self, n, cells):
        spec = tp._spec(graphs=_graphs(n), build_options={"layout": "2 3"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for root in (r._last_layout_root, doc.roots[0]):
            [grid] = list(root.select({"type": GridPlot}))
            assert {(rr, cc) for _m, rr, cc in grid.children} == cells
            assert grid.rows is None and grid.cols == dr._DASH_BS_TRACK
        # What the grid limit is for: dash lays out every one of the six
        # cells, empty or not, before gridplot() leaves the empty ones out.
        assert r._compute_grid(n, "2 3") == (2, 3)


class TestAGridTooSmallForItsItemsGrowsRows:
    """layout(1 2) given three graphs keeps two columns and adds a row."""

    def test_both_modes(self):
        spec = tp._spec(graphs=_graphs(3), build_options={"layout": "1 2"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        assert _grid_shape(r._last_layout_root) == (2, 2)
        assert _grid_shape(doc.roots[0]) == (2, 2)


class TestAnItemThePlacementDoesNotNameTakesAFreeCell:
    """layout(g2:1,2) with g1, g2 and g3: g2 at row 1 column 2, g1 in the
    first free cell, g3 in a row added for it."""

    def test_both_modes(self):
        spec = tp._spec(graphs=_graphs(3), build_options={"layout": "g2:1,2"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for root in (r._last_layout_root, doc.roots[0]):
            [grid] = list(root.select({"type": GridPlot}))
            where = {m.title.text: (rr, cc) for m, rr, cc in grid.children}
            assert where == {"g2": (0, 1), "g1": (0, 0), "g3": (1, 0)}


class TestTheSavedBootstrapGridReflows:
    """Below 768 pixels every cell takes the whole row; from 768 to 991 a
    cell of four columns or fewer takes half of it; from 992 each takes its
    span."""

    def test_the_breakpoints_are_768_and_992(self):
        css = dr._DASH_GRID_CSS
        md = css.index("@media(min-width:768px){")
        lg = css.index("@media(min-width:992px){")
        assert css.index(".db-col-md-6{") > md
        assert css.index(".db-col-lg-6{") > lg
        assert ".db-col-md-6{" not in css[:md]
        assert ".db-col-lg-6{" not in css[:lg]
        assert ".db-col-12{flex:0 0 100%;max-width:100%}" in css[:md]

    def test_each_cell_carries_its_classes(self):
        spec = tp._spec(graphs=_graphs(4), build_options={
            "layout": "bs: g1=3 g2=4 g3=5 / g4=12"})
        _r, _w, page = tp._standalone_page(spec)
        cells = re.findall(r'<div class="(db-col-12 db-col-sm-12 '
                           r'db-col-md-(\d+) db-col-lg-(\d+))', page)
        spans = [(int(lg), int(md)) for _c, md, lg in cells]
        assert spans == [(3, 6), (4, 6), (5, 5), (12, 12)]


# ===========================================================================
# Tabs
# ===========================================================================

class TestTabsPastTheLimit:
    """Fifty tabs are drawn; an item that only a later tab names is drawn
    below the tabs, in both modes."""

    TABS = " / ".join(["T%d: g1" % i for i in range(1, 51)]
                      + ["T51: g2", "T52: g3"])

    def test_both_modes(self):
        spec = tp._spec(graphs=_graphs(3), build_options={"tabs": self.TABS})
        r, std_w = tp._standalone(spec)
        doc, srv_w = tp._served(spec)
        for root in (r._last_layout_root, doc.roots[0]):
            [tabs] = list(root.select({"type": Tabs}))
            assert len(tabs.tabs) == 50
            inside = {f.title.text for f in tabs.select({"type": _FIGURE})}
            everything = {f.title.text
                          for f in root.select({"type": _FIGURE})}
            assert inside == {"g1"} and everything - inside == {"g2", "g3"}
        note = ("dash: tabs() has 52 tabs, more than the 50 a dashboard "
                "draws; the first 50 are drawn. Set global dash_max_tabs to "
                "draw more (at most 500).")
        assert note in std_w and note in srv_w


class TestTabTitles:
    """A title is used as written less the blanks around it; a group with
    no colon is titled by its place; the first colon ends a title."""

    def test_both_modes(self):
        spec = tp._spec(graphs=_graphs(3), build_options={
            "tabs": "  My  Tab :  g1 / g2 / A:B: g3"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for root in (r._last_layout_root, doc.roots[0]):
            [tabs] = list(root.select({"type": Tabs}))
            assert [t.title for t in tabs.tabs] == ["My  Tab", "Tab 2", "A"]


# ===========================================================================
# Linking and Brushing
# ===========================================================================

def _draws_from_group(fig_scatter, fig_other):
    """Which of *fig_other*'s glyph renderers draw from the source
    *fig_scatter*'s scatter draws -- the link group's."""
    group = {id(r.data_source) for r in fig_scatter.renderers
             if isinstance(r, GlyphRenderer)}
    return [id(r.data_source) in group for r in fig_other.renderers
            if isinstance(r, GlyphRenderer)]


def _linked(ptype):
    spec = tp._spec(graphs=[("g1", [plot_for("scatter")], {"title": "g1"}),
                            ("g2", [plot_for(ptype)], {"title": "g2"})],
                    build_options={"link": "g1 g2"})
    r, _ = tp._standalone(spec)
    doc, _ = tp._served(spec)
    saved, served = _figures(r), _figures(doc)
    return (_draws_from_group(saved["g1"], saved["g2"]),
            _draws_from_group(served["g1"], served["g2"]))


class TestASelectionReachesTheLayersThatDrawTheGroupsRows:
    """A box or lasso selection is the group source's selection, so it
    shows only on a layer drawn from that source."""

    @pytest.mark.parametrize("ptype", ["scatter", "connected", "dot"])
    def test_a_marker_layer_draws_the_group_source(self, ptype):
        saved, served = _linked(ptype)
        assert any(saved) and any(served), (saved, served)

    def test_connected_draws_its_line_from_its_own(self):
        saved, served = _linked("connected")
        assert sorted(saved) == sorted(served) == [False, True]

    @pytest.mark.parametrize("ptype", [
        "line", "area", "bar", "spike", "dropline", "lfit", "qfitci",
        "lowess", "fpfit", "mspline", "mband", "histogram", "kdensity",
        "tsline", "rarea", "rcap", "rline", "rcapsym", "rscatter", "tsrline",
        "pcspike", "pcscatter", "pccapsym",
        # rbar since WP-27: drawn from a copy of its own rows, so the saved
        # page's filter callback keeps a move's rows of it and recomputes
        # the bars' width from them, as the served app draws it.
        "rbar"])
    def test_any_other_layer_draws_from_its_own(self, ptype):
        saved, served = _linked(ptype)
        assert saved and served
        assert not any(saved) and not any(served), (saved, served)

    @pytest.mark.parametrize("ptype", ["rspike", "rconnected"])
    def test_two_range_layers_draw_it_in_both_modes(self, ptype):
        """WP-28 E14: a served rspike or rconnected in a link group now
        draws the group's shared source (_dash_range_source), through a
        view when qualified, exactly as the saved page's mapper does; it
        used to build a private source every time."""
        saved, served = _linked(ptype)
        assert any(saved) and any(served), (saved, served)
        if ptype == "rconnected":
            assert sorted(saved) == sorted(served)


class TestAKpiNameInLinkHasNoEffect:
    """link(k1 g1 g2) links g1 and g2 as link(g1 g2) does; link(k1 g1)
    links nothing to g2."""

    @pytest.mark.parametrize("link,shared", [
        ("k1 g1 g2", True), ("g1 g2", True), ("k1 g1", False)])
    def test_both_modes(self, link, shared):
        spec = tp._spec(graphs=_graphs(2), kpis=[tp._kpi("k1")],
                        build_options={"link": link})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for figs in (_figures(r), _figures(doc)):
            assert _draws_from_group(figs["g1"], figs["g2"]) == [shared]


# ===========================================================================
# The toolbar
# ===========================================================================

class TestOneToolbarPerGrid:
    """A grid's figures share one toolbar above it, whose every tool acts on
    each figure; in both modes."""

    def _roots(self, bo=None, n=3, kpis=None):
        spec = tp._spec(graphs=_graphs(n), build_options=bo, kpis=kpis)
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        return r._last_layout_root, doc.roots[0]

    def test_above_the_grid(self):
        for root in self._roots():
            [grid] = list(root.select({"type": GridPlot}))
            assert grid.toolbar_location == "above"
            assert all(m.toolbar_location is None
                       for m, _r, _c in grid.children)

    def test_each_tool_is_every_figure_s(self):
        for root in self._roots():
            [grid] = list(root.select({"type": GridPlot}))
            proxies = [t for t in grid.toolbar.tools
                       if isinstance(t, ToolProxy)]
            kinds = {}
            for p in proxies:
                kinds.setdefault(type(p.tools[0]).__name__, []).append(
                    len(p.tools))
            for kind in ("PanTool", "WheelZoomTool", "BoxZoomTool",
                         "BoxSelectTool", "LassoSelectTool", "UndoTool",
                         "RedoTool", "ResetTool"):
                assert kinds.get(kind) == [3], (kind, kinds)

    def test_the_image_holds_only_the_grid(self):
        """The save button exports its toolbar's grid: a KPI card is a Div
        in it, which BokehJS draws as blank, and the title and the filters
        sit outside it."""
        for root in self._roots(
                bo={"title": "T", "filter": "foreign, type(dropdown)"},
                n=2, kpis=[tp._kpi("k1")]):
            [grid] = list(root.select({"type": GridPlot}))
            in_grid = {id(m) for m in grid.select({"type": Div})}
            kpi_cells = [m for m, _r, _c in grid.children
                         if isinstance(m, Div)]
            assert len(kpi_cells) == 1
            outside = [m for m in root.select({"type": Div})
                       if id(m) not in in_grid]
            assert any(">T</h2>" in (m.text or "") for m in outside)
            assert not list(grid.select({"type": Select}))
            assert list(root.select({"type": Select}))


class TestLayoutBsGivesEachItemItsOwnToolbar:
    def test_a_graph_s_toolbar_is_beside_it(self):
        spec = tp._spec(graphs=_graphs(2), build_options={"layout": "bs"})
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        for figs in (_figures(r), _figures(doc)):
            assert {f.toolbar_location for f in figs.values()} == {"right"}

    def test_a_by_graph_s_panels_have_theirs_above_them(self):
        """The cell both modes place for a by() graph (_dash_layout_cell)."""
        spec = tp._spec(graphs=[("g1", [plot_for("scatter")],
                                 {"by": "foreign"})],
                        build_options={"layout": "bs"})
        r, _ = tp._standalone(spec)
        cell = dr._dash_layout_cell("g1", r.figures, r._facet_map,
                                    r.kpi_divs, lambda _n: {})
        assert isinstance(cell, GridPlot)
        assert cell.toolbar_location == "above"
        doc, _ = tp._served(spec)
        [grid] = list(doc.roots[0].select({"type": GridPlot}))
        assert grid.toolbar_location == "above"


class TestResetAndHover:
    def _figs(self):
        spec = tp._spec(graphs=[
            ("g1", [plot_for("scatter")], {"title": "g1"}),
            ("g2", [plot_for("function")], {"title": "g2"})])
        r, _ = tp._standalone(spec)
        doc, _ = tp._served(spec)
        return _figures(r), _figures(doc)

    def test_reset_clears_the_selection_too(self):
        """BokehJS's PlotView.reset() clears the view state, the ranges and
        the selection when reset_policy is "standard"."""
        for figs in self._figs():
            assert {f.reset_policy for f in figs.values()} == {"standard"}

    def test_every_figure_has_a_hover_button(self):
        """Tool.visible (Bokeh 3.4's name for toggleable): the inspector's
        button is on the toolbar, and clicking it turns the tooltips off
        and on.  Every figure has tooltips -- a function plot, which had
        none until the tooltip fallback read every glyph's own columns
        (test_help_claims_1.py TestEveryFigureHasTooltips), as much as a
        scatter -- so every figure has the button, in both modes."""
        for figs in self._figs():
            for name in ("g1", "g2"):
                hover = [t for t in figs[name].tools
                         if isinstance(t, HoverTool)]
                assert hover and all(t.visible for t in hover), name


class TestTheBokehJSBehaviourTheHelpRestsOn:
    """What the toolbar and layout text says the browser does is BokehJS's
    doing, read here from the bundle dash inlines, so that a Bokeh upgrade
    that changes it fails a test rather than leaving the help wrong."""

    @staticmethod
    def _bundle():
        import bokeh
        path = os.path.join(os.path.dirname(bokeh.__file__), "server",
                            "static", "js", "bokeh.js")
        with open(path, encoding="utf-8") as fh:
            return " ".join(fh.read().split())

    def test_reset_clears_the_view_the_history_and_the_selection(self):
        js = self._bundle()
        assert ('reset() { if (this.model.reset_policy == "standard") { '
                'this.state.clear(); this.reset_range(); '
                'this.reset_selection(); }') in js

    def test_undo_steps_through_pans_zooms_and_selections(self):
        js = self._bundle()
        for kind in ("pan", "box_zoom", "wheel_zoom"):
            assert 'this.plot_view.state.push("%s", { range:' % kind in js
        for kind in ("box_select", "lasso_select"):
            assert ('this.plot_view.state.push("%s", { selection:' % kind
                    in js)
        assert ("if (state.selection != null) { "
                "this.parent.update_selection(state.selection); }") in js

    def test_a_grid_is_as_large_as_the_cells_it_holds(self):
        js = self._bundle()
        assert "nrows = max(nrows, row + row_span);" in js
        assert "ncols = max(ncols, col + col_span);" in js

    def test_an_image_draws_only_what_has_a_canvas(self):
        """A layout exports its children's images over its background; a
        widget or a Div has no canvas and exports a blank one."""
        js = self._bundle()
        assert ("for (const view of this.child_views) { const region = "
                "view.export(type, hidpi);") in js
        assert ("const canvas = new canvas_1.CanvasLayer(output_backend, "
                "hidpi); const { width, height } = this.bbox; "
                "canvas.resize(width, height); return canvas;") in js


# ===========================================================================
# The help says what these tests pin
# ===========================================================================

def _section(marker, next_marker):
    with open(_HELP, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index("{marker %s}" % marker)
    return text[start:text.index("{marker %s}" % next_marker, start)]


class TestTheHelpSaysSo:
    def test_the_filters_section(self):
        s = " ".join(_section("filters", "kpi").split())
        assert "semicolon internally" not in s
        assert "anything but a semicolon" not in s
        assert "keeps only the last of a repeated option" not in s
        assert "{cmd:||}" in s and "r(111)" in s

    def test_the_layout_section(self):
        s = " ".join(_section("layout", "tabs").split())
        assert "1.8" in s and "three times as wide" in s

    def test_the_linking_section(self):
        s = " ".join(_section("linking", "toolbar").split())
        assert "{cmd:dot}" in s and "{cmd:rbar}" in s

    def test_the_toolbar_section(self):
        s = " ".join(_section("toolbar", "filters").split())
        assert "pans, zooms and box and lasso selections" in s
        assert "what Undo would step back through" in s

    def test_the_tabs_section(self):
        s = " ".join(_section("tabs", "linking").split())
        assert "a note names the rest" not in s
        assert "{cmd:Tab 2}" in s
