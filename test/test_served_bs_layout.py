"""layout(bs) when served: the saved page's rows and spans on 12 columns.

WP-21 TR-21.4 / AC-21.3 (GAPS.md H3, "Bootstrap layout in server mode is
unverified").  Measured at ed41e8a, before this: the served app read
``layout(bs...)`` with the placement parser, found no placements and drew
the automatic grid, without a word --

* ``layout(bs)``, two graphs and four KPI cards: a 2 x 3 gridplot in
  registry order (g1 g2 k1 / k2 k3 k4), where the saved page draws the four
  cards in one row at span 3 and the two graphs under them at span 6;
* ``layout(bs: k1=3 k2=3 k3=3 k4=3 / g1=12)``: g1 k1 k2 / k3 k4;
* ``layout(bs: g1=8 g2=6 / g3=4)``: g1 g2 / g3 -- no span read, no wrap;
* ``layout(bs: g2=6)`` of three graphs: g1 g2 / g3, the spec's order lost;
* with ``tabs(A: g2)``: the tab strip above an automatic grid of g1 and g3
  (tabs() itself was honoured, and still is).

Now every item takes its span of a Bokeh GridBox's 12 columns, at the row
and column where the saved page's markup puts it at its large breakpoint:
each bs row a new line, a cell that would carry the row past 12 columns on
the next one (flex-wrap).  The served grid does not reflow at narrower
widths; dash.sthlp says so.

Found on the way, and fixed in the one reader both modes now run: under
``layout(bs)`` with no specification, the saved page put a KPI card that
tabs() had placed into the grid as well -- measured, the card's Div was a
root of its own in the grid and a child of the Tabs, so the card was drawn
twice.  The explicit ``bs:`` form already left it out.
"""
import inspect
import itertools
import json
import os
import re
import sys
import textwrap
import time
import types
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import Column, Div, GridBox, GridPlot, Row, SaveTool, Tabs
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr
from dash_render import DashRenderer
from test_adversarial_matrix import (_DF, _SCATTER, _app_source, _load_app,
                                     _session, _write_inputs)

_SEQ = itertools.count()


# ---------------------------------------------------------------------------
# Specs, the saved page and the served session
# ---------------------------------------------------------------------------

def _graph(name, **go):
    """A scatter titled with its own name, so a served figure says which
    graph it is: the app's figure dictionary is local to make_document."""
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": [dict(_SCATTER)], "graph_options": opts,
            "if_expr": "", "in_expr": ""}


def _kpi(name):
    return {"name": name, "stat": "mean", "var": "mpg", "fmt": "%9.2f",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter", "if_expr": "", "in_expr": ""}


def _spec(graphs, kpis=(), layout="bs", graph_options=None, **bo):
    """Graphs then KPI cards, registered in that order, under *layout*.
    *graph_options* is ``{graph name: {option: value}}``."""
    build = {"layout": layout, "link": "", "theme": "", "title": "",
             "subtitle": "", "registry": " ".join(list(graphs) + list(kpis)),
             "tabs": "", "filter_position": "top"}
    build.update(bo)
    return {"graphs": [_graph(g, **(graph_options or {}).get(g, {}))
                       for g in graphs],
            "kpis": [_kpi(k) for k in kpis],
            "build_options": build}


def _saved(tmp_path, spec):
    """(renderer, page, warnings) from the saved-dashboard renderer."""
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = DashRenderer(sp, dp)
        page = r.render()
    return r, page, [str(w.message) for w in caught]


def _served(tmp_path, spec):
    """One served session's document."""
    return _session(_load_app(_app_source(tmp_path, spec),
                              "bs_%d" % next(_SEQ)))


def _name(m):
    """Which registered item a served grid child draws."""
    if isinstance(m, Div):
        k = re.search(r'id="kpi_val_([^"]+)"', m.text)
        assert k, f"a Div in the grid that is not a KPI card: {m.text[:80]}"
        return k.group(1)
    if isinstance(m, GridPlot):
        return "facets:" + ",".join(c[0].title.text for c in m.children
                                    if c[0] is not None)
    return m.title.text


def _served_grid(doc):
    boxes = list(doc.select({"type": GridBox}))
    assert len(boxes) == 1, f"{len(boxes)} GridBoxes in the served document"
    return boxes[0]


def _served_cells(doc):
    """``[(name, row, col, row_span, col_span), ...]`` of the served grid."""
    return [(_name(m), r, c, rs, cs)
            for m, r, c, rs, cs in _served_grid(doc).children]


_ROW = '<div class="db-row db-section">'
_CELL = re.compile(r'db-col-lg-(\d+)[^"]*"><div id="[^"]*" '
                   r'data-root-id="([^"]+)"')


def _saved_rows(r, page):
    """The saved page's grid, read from its markup: one list per db-row of
    ``(name, span)``, in page order.  A component that is neither a figure
    nor a card (a faceted graph's sub-grid) is ``"?"``."""
    names = {f.id: k for k, f in r.figures.items()}
    names.update({d.id: k for k, d in r.kpi_divs.items()})
    body = page[page.index('<div class="db-container">'):]
    rows = []
    for chunk in body.split(_ROW)[1:]:
        cells = [(names.get(root, "?"), int(span))
                 for span, root in _CELL.findall(chunk)]
        if cells:
            rows.append(cells)
    return rows


def _at_large_breakpoint(rows):
    """Where a browser at 992px or more puts the saved page's cells.

    Written here from the CSS, not taken from dash_render: each db-row is
    ``display:flex; flex-wrap:wrap`` and a ``db-col-lg-N`` cell is N/12 of
    it, so a row starts a new line and a cell that does not fit in what is
    left of its line starts the next one."""
    out, line = [], 0
    for row in rows:
        used = 0
        for name, span in row:
            if used + span > 12:
                line, used = line + 1, 0
            out.append((name, line, used, 1, span))
            used += span
        line += 1
    return out


# ---------------------------------------------------------------------------
# The module-level bs rules, directly
# ---------------------------------------------------------------------------

class TestIsBsLayout:
    @pytest.mark.parametrize("value", ["bs", "BS", "  bs  ", "bs: k1=3 k2=3",
                                       "Bs:g1=12"])
    def test_a_bootstrap_value(self, value):
        assert dr._dash_is_bs_layout(value) is True

    @pytest.mark.parametrize("value", ["", None, "auto", "2 2", "g1:1,1",
                                       "abs", "auto bs"])
    def test_anything_else(self, value):
        assert dr._dash_is_bs_layout(value) is False

    # test_the_renderer_asks_the_same_question stood here, and in the two
    # classes below test_the_renderer_wrapper_runs_the_same_rule and
    # test_the_renderer_wrapper_runs_the_same_reader: each held one of
    # DashRenderer's static methods _is_bootstrap_layout, _auto_bs_layout
    # and _parse_bs_layout equal to the module-level function it delegated
    # to.  Only tests called the three, and WP-26 deleted them (24sep2026),
    # so the three tested nothing that runs; the rules themselves are this
    # file's other tests.


class TestAutoBsLayout:
    def test_kpi_cards_come_first_four_to_a_row(self):
        kpis = ["k1", "k2", "k3", "k4", "k5"]
        rows = dr._dash_auto_bs_layout(["g1"] + kpis, kpis)
        assert rows == [[("k1", 3), ("k2", 3), ("k3", 3), ("k4", 3)],
                        [("k5", 3)], [("g1", 12)]]

    def test_fewer_cards_share_their_row_equally(self):
        assert dr._dash_auto_bs_layout(["k1", "k2", "k3"],
                                       ["k1", "k2", "k3"]) == [
            [("k1", 4), ("k2", 4), ("k3", 4)]]

    def test_one_graph_takes_the_whole_row(self):
        assert dr._dash_auto_bs_layout(["g1"], []) == [[("g1", 12)]]

    @pytest.mark.parametrize("n,per_row", [(2, 2), (3, 2), (4, 2), (5, 3),
                                           (7, 3)])
    def test_graphs_two_to_a_row_then_three(self, n, per_row):
        names = [f"g{i}" for i in range(1, n + 1)]
        rows = dr._dash_auto_bs_layout(names, [])
        assert [n for row in rows for n, _ in row] == names
        assert [len(row) for row in rows] == [
            min(per_row, n - i) for i in range(0, n, per_row)]
        assert {s for row in rows for _, s in row} == {12 // per_row}

    def test_a_wide_figure_takes_a_row_of_its_own(self):
        figs = {"w": types.SimpleNamespace(aspect_ratio=3.0),
                "a": types.SimpleNamespace(aspect_ratio=1.0),
                "b": types.SimpleNamespace(aspect_ratio=1.0)}
        assert dr._dash_auto_bs_layout(["a", "w", "b"], [], figs) == [
            [("w", 12)], [("a", 6), ("b", 6)]]

    def test_a_widish_figure_keeps_its_neighbours_two_to_a_row(self):
        names = ["g1", "g2", "g3", "g4", "g5"]
        figs = {n: types.SimpleNamespace(aspect_ratio=1.0) for n in names}
        figs["g3"] = types.SimpleNamespace(aspect_ratio=2.0)
        rows = dr._dash_auto_bs_layout(names, [], figs)
        assert [len(r) for r in rows] == [2, 2, 1]
        assert {s for r in rows for _, s in r} == {6}

    def test_a_card_the_grid_does_not_hold_is_left_out(self):
        """A KPI card tabs() placed is not in *all_names*; it used to get a
        row anyway, and the saved page drew it twice."""
        assert dr._dash_auto_bs_layout(["g2"], ["k1"]) == [[("g2", 12)]]
        assert dr._dash_auto_bs_layout(["k2", "g2"], ["k1", "k2"]) == [
            [("k2", 12)], [("g2", 12)]]

    def test_nothing_to_lay_out(self):
        assert dr._dash_auto_bs_layout([], []) == [[]]


class TestParseBsLayout:
    def test_bare_bs_is_the_automatic_layout(self):
        names, kpis = ["g1", "g2", "k1"], ["k1"]
        assert (dr._dash_parse_bs_layout("bs", names, kpis)
                == dr._dash_auto_bs_layout(names, kpis))
        assert (dr._dash_parse_bs_layout("  BS ", names, kpis)
                == dr._dash_auto_bs_layout(names, kpis))

    def test_rows_and_spans(self):
        kpis = ["k1", "k2", "k3", "k4"]
        assert dr._dash_parse_bs_layout(
            "bs: k1=3 k2=3 k3=3 k4=3 / g1=12", ["g1"] + kpis, kpis) == [
            [("k1", 3), ("k2", 3), ("k3", 3), ("k4", 3)], [("g1", 12)]]

    def test_a_name_without_a_span_takes_six(self):
        assert dr._dash_parse_bs_layout("bs: g1 / g2=12", ["g1", "g2"],
                                        []) == [[("g1", 6)], [("g2", 12)]]

    def test_an_item_the_spec_does_not_name_follows_full_width(self):
        assert dr._dash_parse_bs_layout(
            "bs: g2=6", ["g1", "g2", "g3"], []) == [
            [("g2", 6)], [("g1", 12)], [("g3", 12)]]

    def test_unknown_names_are_dropped_and_spans_held_to_1_12(self):
        """Both are reported first, by _dash_layout_check; this reader
        keeps what it can read."""
        assert dr._dash_parse_bs_layout(
            "bs: g1=99 nosuch=3 / g2=0", ["g1", "g2"], []) == [
            [("g1", 12)], [("g2", 1)]]

    def test_a_name_outside_the_grid_is_not_placed(self):
        """What tabs() took is not handed in, so it is not placed."""
        assert dr._dash_parse_bs_layout("bs: g1=6 g2=6", ["g1"], []) == [
            [("g1", 6)]]

    def test_the_keyword_is_read_in_any_case(self):
        assert dr._dash_parse_bs_layout("BS: g1=12", ["g1"], []) == [
            [("g1", 12)]]

    def test_a_colon_with_nothing_after_it_is_the_automatic_layout(self):
        assert dr._dash_parse_bs_layout("bs:", ["g1", "g2"], []) == [
            [("g1", 6), ("g2", 6)]]

    def test_a_spec_that_places_nothing_falls_back(self):
        assert dr._dash_parse_bs_layout("bs: nosuch=6", [], []) == [[]]

    def test_a_repeated_name_keeps_its_first_place(self):
        """The reader keeps a name once, at its first place (WP-21).  It
        returned every repeat, and the saved page embedded each one: 100,000
        repeats made an 18.1 MB page of duplicate element ids."""
        assert dr._dash_parse_bs_layout("bs: g1=6 g1=6", ["g1"], []) == [
            [("g1", 6)]]


class TestBsGridCells:
    def test_a_full_row_is_one_line(self):
        assert dr._dash_bs_grid_cells(
            [[("a", 3), ("b", 3), ("c", 3), ("d", 3)]]) == [
            ("a", 0, 0, 1, 3), ("b", 0, 3, 1, 3), ("c", 0, 6, 1, 3),
            ("d", 0, 9, 1, 3)]

    def test_each_bs_row_starts_a_new_line(self):
        assert dr._dash_bs_grid_cells([[("a", 6)], [("b", 6)]]) == [
            ("a", 0, 0, 1, 6), ("b", 1, 0, 1, 6)]

    def test_a_row_past_twelve_wraps(self):
        assert dr._dash_bs_grid_cells([[("a", 8), ("b", 6)], [("c", 4)]]) == [
            ("a", 0, 0, 1, 8), ("b", 1, 0, 1, 6), ("c", 2, 0, 1, 4)]

    def test_a_long_row_wraps_more_than_once(self):
        assert dr._dash_bs_grid_cells([[(n, 5) for n in "abcde"]]) == [
            ("a", 0, 0, 1, 5), ("b", 0, 5, 1, 5), ("c", 1, 0, 1, 5),
            ("d", 1, 5, 1, 5), ("e", 2, 0, 1, 5)]

    def test_exactly_twelve_does_not_wrap(self):
        assert dr._dash_bs_grid_cells([[("a", 7), ("b", 5)]]) == [
            ("a", 0, 0, 1, 7), ("b", 0, 7, 1, 5)]

    def test_an_empty_row_takes_no_line(self):
        assert dr._dash_bs_grid_cells([[("a", 12)], [], [("b", 12)]]) == [
            ("a", 0, 0, 1, 12), ("b", 1, 0, 1, 12)]

    def test_spans_are_held_to_1_12(self):
        assert dr._dash_bs_grid_cells([[("a", 0)], [("b", 99)]]) == [
            ("a", 0, 0, 1, 1), ("b", 1, 0, 1, 12)]

    @pytest.mark.parametrize("rows", [None, [], [[]]])
    def test_nothing_gives_nothing(self, rows):
        assert dr._dash_bs_grid_cells(rows) == []

    @pytest.mark.parametrize("rows", [
        [[("a", 4), ("b", 4), ("c", 4), ("d", 4)]],
        [[("a", 11), ("b", 2), ("c", 10)], [("d", 1)] * 13],
        [[("a", 6)], [("b", 7), ("c", 6), ("d", 5)], [("e", 12)]],
    ])
    def test_it_places_cells_where_the_saved_markup_does(self, rows):
        assert dr._dash_bs_grid_cells(rows) == _at_large_breakpoint(rows)


class TestBsGrid:
    def test_a_gridbox_of_twelve_equal_columns(self):
        f, d = figure(), Div(text="x")
        g = dr._dash_bs_grid([[("a", 8), ("b", 4)]], {"a": f, "b": d}.get)
        assert isinstance(g, GridBox)
        assert g.children == [(f, 0, 0, 1, 8), (d, 0, 8, 1, 4)]
        assert g.cols == ["minmax(0, 1fr)"] * 12
        assert g.spacing == 16
        assert g.sizing_mode == "stretch_width"

    def test_a_name_with_nothing_to_draw_takes_no_columns(self):
        """The saved page leaves a component it has not got out of its row,
        so the next cell moves up into its place."""
        a, b = Div(text="a"), Div(text="b")
        g = dr._dash_bs_grid([[("a", 6), ("gone", 6), ("b", 6)]],
                             {"a": a, "b": b}.get)
        assert g.children == [(a, 0, 0, 1, 6), (b, 0, 6, 1, 6)]

    def test_a_repeated_name_keeps_its_first_cell(self):
        """The saved page writes the component twice and Bokeh fills only the
        first element with its id: the second copy's columns stay empty."""
        a, b = Div(text="a"), Div(text="b")
        g = dr._dash_bs_grid([[("a", 6), ("a", 6), ("b", 6)]],
                             {"a": a, "b": b}.get)
        assert g.children == [(a, 0, 0, 1, 6), (b, 1, 0, 1, 6)]

    def test_a_row_only_repeats_occupy_is_closed_up(self):
        """A line of the saved page's empty copies has no height."""
        a, b = Div(text="a"), Div(text="b")
        g = dr._dash_bs_grid([[("a", 12), ("a", 12), ("a", 12), ("b", 12)]],
                             {"a": a, "b": b}.get)
        assert g.children == [(a, 0, 0, 1, 12), (b, 1, 0, 1, 12)]

    def test_repeats_cannot_grow_the_grid(self):
        """However often a name is repeated, no more rows than items."""
        a, b = Div(text="a"), Div(text="b")
        rows = [[("a", 1)] * 5000 + [("b", 12)], [("a", 12)] * 5000]
        g = dr._dash_bs_grid(rows, {"a": a, "b": b}.get)
        assert g.children == [(a, 0, 0, 1, 1), (b, 1, 0, 1, 12)]

    def test_each_name_is_resolved_once(self):
        """A faceted graph's resolver builds a new sub-grid each call."""
        calls = []

        def cell_of(name):
            calls.append(name)
            return Div(text=name)

        dr._dash_bs_grid([[("a", 6), ("a", 6)], [("b", 12)]], cell_of)
        assert calls == ["a", "b"]

    @pytest.mark.parametrize("rows", [None, [], [[]], [[("gone", 6)]]])
    def test_nothing_to_place_is_an_empty_grid(self, rows):
        g = dr._dash_bs_grid(rows, lambda name: None)
        assert isinstance(g, GridBox) and g.children == []

    def test_a_figure_keeps_its_own_toolbar(self):
        """Not a gridplot, which takes every figure's toolbar into one."""
        f = figure()
        before = f.toolbar_location
        dr._dash_bs_grid([[("a", 12)]], {"a": f}.get)
        assert before is not None and f.toolbar_location == before


class TestTheServedGridIsTheSavedPagesGrid:
    """The constants stand for the saved page's CSS; they must not drift."""

    def test_twelve_columns_as_the_markup_has(self):
        spans = {int(n) for n in re.findall(r"\.db-col-lg-(\d+)\{",
                                            dr._DASH_GRID_CSS)}
        assert spans == set(range(1, dr._DASH_BS_COLUMNS + 1))

    def test_the_gutter_is_the_saved_pages(self):
        css = dr._DASH_GRID_CSS
        pad = re.search(r'\.db-row>\[class\*="db-col"\]\{padding-right:'
                        r'(\d+)px;padding-left:(\d+)px', css)
        assert pad, "the saved grid's cell padding moved"
        assert int(pad.group(1)) + int(pad.group(2)) == dr._DASH_BS_GUTTER_PX
        under = re.search(r"\.db-section\{margin-bottom:(\d+)px\}", css)
        assert under and int(under.group(1)) == dr._DASH_BS_GUTTER_PX

    def test_a_column_is_a_fixed_share_of_the_row(self):
        """A saved column is `flex:0 0 N/12; min-width:0' whatever it holds;
        `1fr' alone would let a wide child widen its own column."""
        assert 'min-width:0' in dr._DASH_GRID_CSS
        assert dr._DASH_BS_TRACK == "minmax(0, 1fr)"


# ---------------------------------------------------------------------------
# The served document against the saved page
# ---------------------------------------------------------------------------

class TestTheServedDocument:
    """Each case: the served GridBox's children, and the saved page's cells
    read from its markup and placed as a browser at its large breakpoint
    places them, against the same written-out expectation."""

    @staticmethod
    def _check(tmp_path, spec, expected):
        r, page, _ = _saved(tmp_path, spec)
        saved = _at_large_breakpoint(_saved_rows(r, page))
        doc = _served(tmp_path, spec)
        served = _served_cells(doc)
        assert served == expected, f"served {served}\n  wanted {expected}"
        assert saved == expected, f"saved {saved}\n  wanted {expected}"
        return r, page, doc

    def test_auto_bs(self, tmp_path):
        self._check(tmp_path, _spec(["g1", "g2"], ["k1", "k2", "k3", "k4"]), [
            ("k1", 0, 0, 1, 3), ("k2", 0, 3, 1, 3), ("k3", 0, 6, 1, 3),
            ("k4", 0, 9, 1, 3), ("g1", 1, 0, 1, 6), ("g2", 1, 6, 1, 6)])

    def test_auto_bs_reads_each_figures_proportions(self, tmp_path):
        """The automatic rule needs the figures' aspect ratios, and the
        served app hands it its own figures: a 10 x 2 graph takes a row of
        its own in both modes."""
        spec = _spec(["a", "w", "b"],
                     graph_options={"w": {"xsize": "10", "ysize": "2"}})
        self._check(tmp_path, spec, [
            ("w", 0, 0, 1, 12), ("a", 1, 0, 1, 6), ("b", 1, 6, 1, 6)])

    def test_rows_and_spans(self, tmp_path):
        spec = _spec(["g1"], ["k1", "k2", "k3", "k4"],
                     layout="bs: k1=3 k2=3 k3=3 k4=3 / g1=12")
        self._check(tmp_path, spec, [
            ("k1", 0, 0, 1, 3), ("k2", 0, 3, 1, 3), ("k3", 0, 6, 1, 3),
            ("k4", 0, 9, 1, 3), ("g1", 1, 0, 1, 12)])

    def test_a_row_past_twelve_wraps(self, tmp_path):
        spec = _spec(["g1", "g2", "g3"], layout="bs: g1=8 g2=6 / g3=4")
        self._check(tmp_path, spec, [
            ("g1", 0, 0, 1, 8), ("g2", 1, 0, 1, 6), ("g3", 2, 0, 1, 4)])

    def test_a_long_row_wraps_twice(self, tmp_path):
        names = ["g1", "g2", "g3", "g4", "g5"]
        spec = _spec(names, layout="bs: " + " ".join(f"{n}=5" for n in names))
        self._check(tmp_path, spec, [
            ("g1", 0, 0, 1, 5), ("g2", 0, 5, 1, 5), ("g3", 1, 0, 1, 5),
            ("g4", 1, 5, 1, 5), ("g5", 2, 0, 1, 5)])

    def test_items_the_spec_does_not_name_follow_full_width(self, tmp_path):
        spec = _spec(["g1", "g2", "g3"], ["k1"], layout="bs: g2=6")
        self._check(tmp_path, spec, [
            ("g2", 0, 0, 1, 6), ("g1", 1, 0, 1, 12), ("g3", 2, 0, 1, 12),
            ("k1", 3, 0, 1, 12)])

    def test_tabs_and_bs(self, tmp_path):
        """A tabbed item is not in the grid; the tab strip sits above it,
        where the saved page puts its tabs section."""
        spec = _spec(["g1", "g2", "g3"], layout="bs: g1=6 g2=6 g3=6",
                     tabs="A: g2")
        r, page, doc = self._check(tmp_path, spec, [
            ("g1", 0, 0, 1, 6), ("g3", 0, 6, 1, 6)])
        root = doc.roots[0]
        assert isinstance(root, Column)
        assert isinstance(root.children[0], Tabs)
        assert root.children[1] is _served_grid(doc)
        tabbed = [m.title.text for m in root.children[0].select(
            {"type": type(figure())})]
        assert tabbed == ["g2"]
        body = page[page.index('<div class="db-container">'):]
        assert body.index('class="db-col-md-12"') < body.index("db-col-lg-")

    def test_auto_bs_leaves_a_tabbed_kpi_card_in_its_tab(self, tmp_path):
        """The saved page used to draw the card in its tab AND in the grid."""
        spec = _spec(["g1", "g2"], ["k1"], tabs="A: g1 k1")
        r, page, doc = self._check(tmp_path, spec, [("g2", 0, 0, 1, 12)])
        assert f'data-root-id="{r.kpi_divs["k1"].id}"' not in page
        tabs = list(doc.select({"type": Tabs}))
        assert len(tabs) == 1
        assert any("kpi_val_k1" in d.text
                   for d in tabs[0].select({"type": Div}))

    def test_every_item_tabbed_leaves_no_grid(self, tmp_path):
        spec = _spec(["g1", "g2"], tabs="A: g1 g2")
        r, page, _ = _saved(tmp_path, spec)
        assert _saved_rows(r, page) == []
        doc = _served(tmp_path, spec)
        assert not list(doc.select({"type": GridBox}))
        assert isinstance(doc.roots[0], Tabs)

    def test_kpi_cards_in_the_grid_are_the_cards(self, tmp_path):
        spec = _spec(["g1"], ["k1", "k2"], layout="bs: k1=6 k2=6 / g1=12")
        r, _, doc = self._check(tmp_path, spec, [
            ("k1", 0, 0, 1, 6), ("k2", 0, 6, 1, 6), ("g1", 1, 0, 1, 12)])
        for (card, *_), name in zip(_served_grid(doc).children, ("k1", "k2")):
            assert isinstance(card, Div) and 'class="db-kpi-card"' in card.text
            assert card.sizing_mode == "stretch_width"
            # The value the saved card shows.
            shown = re.search(r'id="kpi_val_%s"[^>]*>([^<]*)<' % name,
                              r.kpi_divs[name].text).group(1)
            assert f">{shown}<" in card.text

    def test_a_faceted_graph_is_one_cell(self, tmp_path):
        spec = _spec(["g1", "g2"], layout="bs: g1=12 / g2=6",
                     graph_options={"g1": {"by": "foreign"}})
        r, page, _ = _saved(tmp_path, spec)
        assert _saved_rows(r, page) == [[("?", 12)], [("g2", 6)]]
        cells = _served_cells(_served(tmp_path, spec))
        assert [c[1:] for c in cells] == [(0, 0, 1, 12), (1, 0, 1, 6)]
        facets = cells[0][0]
        assert facets.startswith("facets:") and facets.count("g1") == 2
        assert cells[1][0] == "g2"

    def test_a_name_placed_twice_keeps_its_first_cell(self, tmp_path):
        """g1 keeps its first place in both modes, and g2 takes the next.
        The saved page used to write g1's component twice, the second
        element with the same id never filled and its columns left empty,
        while the served grid dropped the repeat: the two disagreed."""
        spec = _spec(["g1", "g2"], layout="bs: g1=6 g1=6 g2=6")
        r, page, _ = _saved(tmp_path, spec)
        want = [("g1", 0, 0, 1, 6), ("g2", 0, 6, 1, 6)]
        assert _at_large_breakpoint(_saved_rows(r, page)) == want
        assert _served_cells(_served(tmp_path, spec)) == want

    def test_a_line_of_repeats_takes_no_space(self, tmp_path):
        """A repeat is dropped before either mode lays the row out, so g2
        sits directly under g1 in both (the saved page used to write an
        empty second copy of g1 on a line of its own)."""
        spec = _spec(["g1", "g2"], layout="bs: g1=12 g1=12 g2=12")
        r, page, _ = _saved(tmp_path, spec)
        want = [("g1", 0, 0, 1, 12), ("g2", 1, 0, 1, 12)]
        assert _at_large_breakpoint(_saved_rows(r, page)) == want
        assert _served_cells(_served(tmp_path, spec)) == want

    def test_figures_keep_their_toolbars_as_on_the_saved_page(self, tmp_path):
        spec = _spec(["g1", "g2"], layout="bs")
        r, _, _ = _saved(tmp_path, spec)
        children = _served_grid(_served(tmp_path, spec)).children
        # g1 and g2 both reach the grid: an empty grid ran the loop zero
        # times and asserted nothing (measured 24sep2026: two children).
        assert len(children) == 2, [c[0].title.text for c in children]
        for fig, *_ in children:
            assert fig.toolbar_location is not None
            assert (fig.toolbar_location
                    == r.figures[fig.title.text].toolbar_location)

    def test_the_grid_has_twelve_equal_columns(self, tmp_path):
        grid = _served_grid(_served(tmp_path, _spec(["g1"])))
        assert grid.cols == [dr._DASH_BS_TRACK] * dr._DASH_BS_COLUMNS
        assert grid.spacing == dr._DASH_BS_GUTTER_PX
        assert grid.sizing_mode == "stretch_width"

    @pytest.mark.parametrize("position", ["top", "left"])
    def test_filters_title_and_subtitle_keep_their_places(self, tmp_path,
                                                          position):
        """Everything around the grid is built as it is for layout(auto):
        the two documents differ in the grid node alone."""
        bo = {"filter": "price, type(range)", "filter_position": position,
              "title": "T", "subtitle": "S"}

        def shape(m):
            if isinstance(m, (GridBox, GridPlot)):
                return "GRID"
            if isinstance(m, Div):
                return ("Div", m.text)
            kids = getattr(m, "children", None)
            if isinstance(m, (Column, Row)) and kids is not None:
                return (type(m).__name__, [shape(k) for k in kids])
            return type(m).__name__

        bs = _served(tmp_path, _spec(["g1", "g2"], layout="bs: g1=6 g2=6",
                                     **bo))
        auto = _served(tmp_path, _spec(["g1", "g2"], layout="auto", **bo))
        assert len(bs.roots) == len(auto.roots) == 1
        assert shape(bs.roots[0]) == shape(auto.roots[0])
        assert "GRID" in repr(shape(bs.roots[0]))
        assert _served_cells(bs) == [("g1", 0, 0, 1, 6), ("g2", 0, 6, 1, 6)]

    def test_a_bs_problem_is_reported_once_and_the_rest_drawn(self, tmp_path):
        """_dash_layout_check reports it when the spec is read (dash.ado
        refuses it); the served grid adds no second report and draws what
        can be read, as the saved page does."""
        spec = _spec(["g1", "g2"], layout="bs: g1=6 nosuch=6")
        _, _, saved_msgs = _saved(tmp_path, spec)
        sp, dp = _write_inputs(tmp_path, spec)
        app = os.path.join(str(tmp_path), "app_problem.py")
        with warnings.catch_warnings(record=True) as built:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "bs_problem")
        with warnings.catch_warnings(record=True) as session:
            warnings.simplefilter("always")
            doc = Document()
            ns["make_document"](doc)

        def layout_msgs(ws):
            return [str(w.message) for w in ws if "layout(" in str(w.message)]

        assert [m for m in saved_msgs if "layout(" in m] == layout_msgs(built)
        assert len(layout_msgs(built)) == 1
        assert "nosuch" in layout_msgs(built)[0]
        assert layout_msgs(session) == []
        assert _served_cells(doc) == [("g1", 0, 0, 1, 6), ("g2", 1, 0, 1, 12)]


# ---------------------------------------------------------------------------
# A by() graph's cell: its panels in the columns cols() asks for
# ---------------------------------------------------------------------------

#: A by() variable of four levels.  foreign's two cannot tell cols(2) from
#: one row, which is how the saved page's one row of panels went unseen.
_DF_REP = _DF.assign(rep=[1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0])


def _saved_by_cell(tmp_path, spec, monkeypatch):
    """The sub-grid the saved bs page embeds in a grid cell -- the by()
    graph's -- taken where the renderer hands its components to
    components(), and found by the root id its cell's markup names."""
    handed = {}
    real = dr.components

    def spy(models, *a, **k):
        handed.update((m.id, m) for m in models)
        return real(models, *a, **k)

    monkeypatch.setattr(dr, "components", spy)
    sp, dp = _write_inputs(tmp_path, spec, _DF_REP)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        page = DashRenderer(sp, dp).render()
    body = page[page.index('<div class="db-container">'):]
    roots = [root for chunk in body.split(_ROW)[1:]
             for _, root in _CELL.findall(chunk)]
    grids = [handed[x] for x in roots if isinstance(handed.get(x), GridPlot)]
    assert len(grids) == 1, f"{len(grids)} sub-grids in the saved bs grid"
    return grids[0]


def _served_by_cell(tmp_path, spec):
    """The sub-grid among the served GridBox's cells."""
    doc = _session(_load_app(_app_source(tmp_path, spec, _DF_REP),
                             "bs_by_%d" % next(_SEQ)))
    grids = [m for m, *_ in _served_grid(doc).children
             if isinstance(m, GridPlot)]
    assert len(grids) == 1, f"{len(grids)} sub-grids in the served GridBox"
    return grids[0]


def _panels(grid):
    """A by() cell as the browser draws it: each panel's title with its row
    and column, the side of the cell its toolbar sits on, and the file its
    save button writes."""
    return ([(f.title.text, r, c) for f, r, c in grid.children],
            grid.toolbar_location,
            [t.filename for t in grid.toolbar.tools
             if isinstance(t, SaveTool)])


class TestAByGraphsCellHonoursCols:
    """by(, cols(#)) under layout(bs), in both modes.

    Every other grid lays a by() graph's panels out through
    _dash_layout_cell, in the columns cols(#) asks for and ceil(sqrt(n))
    without it: the saved page's grid and its tabs, and every served grid,
    the layout(bs) GridBox included.  The saved layout(bs) page built a cell
    of its own, every panel in one row whatever cols() said, with its
    toolbar on the right where every other grid's sits above.  Measured at
    31e76e0: by(rep, cols(2)) of four panels drew one row of four on the
    saved page and two rows of two served; by(foreign, cols(1)) one row of
    two against a column of two; by(rep) one row of four against two rows
    of two.
    """

    @pytest.mark.parametrize("by, layout, where", [
        ("rep, cols(2)", "bs: g1=12 / g2=6",
         [(0, 0), (0, 1), (1, 0), (1, 1)]),
        ("rep, cols(2)", "bs", [(0, 0), (0, 1), (1, 0), (1, 1)]),
        ("rep, cols(3)", "bs: g2=6 / g1=12",
         [(0, 0), (0, 1), (0, 2), (1, 0)]),
        ("rep, cols(1)", "bs: g1=6 g2=6", [(0, 0), (1, 0), (2, 0), (3, 0)]),
        ("foreign, cols(1)", "bs: g1=12 / g2=6", [(0, 0), (1, 0)]),
        # No cols(): the default every other grid uses, ceil(sqrt(4)).
        ("rep", "bs: g1=12 / g2=6", [(0, 0), (0, 1), (1, 0), (1, 1)]),
    ])
    def test_the_saved_cell_is_the_served_cell(self, tmp_path, monkeypatch,
                                               by, layout, where):
        spec = _spec(["g1", "g2"], layout=layout,
                     graph_options={"g1": {"by": by}})
        served = _panels(_served_by_cell(tmp_path, spec))
        saved = _panels(_saved_by_cell(tmp_path, spec, monkeypatch))
        assert [(r, c) for _, r, c in served[0]] == where, served
        assert [(r, c) for _, r, c in saved[0]] == where, saved
        assert saved == served

    def test_the_cell_still_saves_under_the_graph_s_name(self, tmp_path,
                                                         monkeypatch):
        """Laid out by the shared resolver, the cell keeps one toolbar,
        above its panels as every grid's is, and its save button still
        writes the whole cell named after the graph -- not the
        dashboard.png the resolver names a grid everywhere else."""
        spec = _spec(["g1", "g2"], layout="bs",
                     graph_options={"g1": {"by": "rep, cols(2)"}})
        _, side, saves = _panels(_saved_by_cell(tmp_path, spec, monkeypatch))
        assert saves == ["g1"]
        assert side == "above"


class TestAdversarialServedBs:
    """CLAUDE.md rule 18 for ``layout(bs)`` now that the served app reads it:
    a bs spec places registered grid items only, carries none of its own
    text into the document or the app's code, and cannot make the served
    grid bigger than the dashboard.  Registered in test_adversarial_matrix's
    SURFACES under build_options."""

    @pytest.mark.parametrize("token", [
        "G1=6", "g1​=6", "ｇ1=6", "g1 =6", "_all=6", "g2=6",
        "g3:1,1=6", "=6"])
    def test_bypass_only_the_grid_names_are_placed(self, tmp_path, token):
        """A near-miss of a registered name, a name tabs() took (g2), a
        placement-form token: none reaches the grid, and the tabbed item
        stays in its tab alone.  The saved page's grid agrees."""
        spec = _spec(["g1", "g2", "g3"], layout=f"bs: {token} g3=6",
                     tabs="A: g2")
        doc = _served(tmp_path, spec)
        served = _served_cells(doc)
        names = [c[0] for c in served]
        assert sorted(names) == ["g1", "g3"], served
        tabs = list(doc.select({"type": Tabs}))
        assert [m.title.text for m in tabs[0].select(
            {"type": type(figure())})] == ["g2"]
        r, page, _ = _saved(tmp_path, spec)
        assert _at_large_breakpoint(_saved_rows(r, page)) == served

    @pytest.mark.parametrize("payload", [
        "<img src=x onerror=alert('PWNED_7f3a')>",
        "\"><script>PWNED_7f3a()</script>",
        "$$\\href{javascript:PWNED_7f3a}{x}$$",
        "g1=6);__import__('os').system('PWNED_7f3a')#",
        "PWNED_7f3a\"=6'''\n\"\"\"",
    ])
    def test_injection_no_spec_text_reaches_the_document(self, tmp_path,
                                                         payload):
        """The spec is data: embedded as base64, read into names and
        integers, and never written into a model or the app's source."""
        spec = _spec(["g1", "g2"], layout=f"bs: g1=6 {payload}=6 g2=6")
        src = _app_source(tmp_path, spec)
        assert "PWNED_7f3a" not in src
        doc = _session(_load_app(src, "bs_inj_%d" % next(_SEQ)))
        assert sorted(c[0] for c in _served_cells(doc)) == ["g1", "g2"]
        assert "PWNED_7f3a" not in json.dumps(doc.to_json(), default=str)

    def test_exhaustion_repeats_cannot_grow_the_served_grid(self, tmp_path):
        """40,000 repeated placements: the served grid still holds one cell
        an item and no more rows than items, so what a session sends does
        not grow with the spec."""
        layout = "bs: " + "g1=1 " * 20000 + "/ " + "g2=12 " * 20000
        spec = _spec(["g1", "g2"], layout=layout)
        t0 = time.monotonic()
        doc = _served(tmp_path, spec)
        took = time.monotonic() - t0
        assert _served_cells(doc) == [("g1", 0, 0, 1, 1),
                                      ("g2", 1, 0, 1, 12)]
        assert took < 60, f"a served session took {took:.1f}s"


@pytest.mark.serve
class TestUnderBokehServe:
    """The grid as a browser receives it: a real ``bokeh serve`` (no
    browser opened), and the session's document pulled over the WebSocket
    -- so the GridBox, its spans and its column tracks survive the trip."""

    def test_the_pulled_document_holds_the_grid(self, tmp_path):
        from test_server_serves import _pull, _Served
        spec = _spec(["g1", "g2", "g3"], ["k1"],
                     layout="bs: k1=4 g1=8 / g2=6 g3=6")
        sp, dp = _write_inputs(tmp_path, spec)
        app = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with _Served(app) as srv:
            doc, roots = _pull(srv)
        assert len(roots) == 1
        assert _served_cells(doc) == [
            ("k1", 0, 0, 1, 4), ("g1", 0, 4, 1, 8), ("g2", 1, 0, 1, 6),
            ("g3", 1, 6, 1, 6)]
        grid = _served_grid(doc)
        assert grid.cols == [dr._DASH_BS_TRACK] * dr._DASH_BS_COLUMNS
        assert grid.spacing == dr._DASH_BS_GUTTER_PX


class TestTheAppCarriesTheBsRules:
    def test_each_bs_helper_is_copied_verbatim(self, tmp_path):
        """One text of the rules: the app runs the module's own source."""
        src = _app_source(tmp_path, _spec(["g1"]))
        for fn in (dr._dash_is_bs_layout, dr._dash_auto_bs_layout,
                   dr._dash_parse_bs_layout, dr._dash_bs_grid_cells,
                   dr._dash_bs_grid):
            text = textwrap.dedent(inspect.getsource(fn)).rstrip("\n")
            assert text in src, f"{fn.__name__} is not in the app as written"
        for const in ("_MAX_KPIS_PER_ROW", "_DASH_BS_COLUMNS",
                      "_DASH_BS_TRACK", "_DASH_BS_GUTTER_PX"):
            assert f"{const} = {getattr(dr, const)!r}" in src, const

    def test_the_app_reads_bs_with_them(self, tmp_path):
        """make_document decides with the shared predicate and reads the
        rows with the shared reader over the names tabs() left."""
        src = _app_source(tmp_path, _spec(["g1"]))
        body = src[src.index("def make_document"):]
        assert "if _dash_is_bs_layout(layout_opt):" in body
        assert "_dash_parse_bs_layout(layout_opt, grid_names" in body
        assert "_dash_bs_grid(" in body
