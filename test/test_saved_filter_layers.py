"""Every layer on a saved page follows a filter move and a brush, and a
layer's own if()/in() draws the observations twoway draws.

The saved page's filter callback (``_FILTER_JS``) is RUN here, under node,
with the widget moved -- not read.  What it leaves in every model is written
back into the Python document, and each figure's glyphs and marker labels
are compared with the saved renderer given the move's rows as an ``if``: the
page after a move must draw what the same page draws of the filtered data,
which is what twoway draws of it (``test_mode_parity.py`` holds that render
to the served app and to Stata's own row counts).  The node run and its
write-back are ``test/js_runner.py``'s ``JsSession`` (WP-28 S03); ``_run``
here is a thin shim over it.

Measured 24sep2026 by WP-24 under node at 7c28802 (BUGS.md): with a move
that keeps 10 rows of 40, scatter and dot followed it while line, tsline,
area, bar, spike, dropline and a connected plot's line stayed at 40 -- each
drew from a copy of the columns its mapper built, which the callback
neither wrote nor recomputed.  The same copy made ``scatter mpg rep78`` on
auto, with rep78 missing on five cars, stay at 69 rows after a move to
Foreign where Stata's ``count if foreign == 1 & !missing(rep78)`` is 21,
and gave it no brush script.  A line with its own ``in 3/8`` drew x 2200,
2650, 2930, 3000, 3100, 3350 where twoway's serset holds observations 3 to
8 (x 2200, 1800, 3000, 3100, 4080, 2010): the view's flags were applied by
position to a copy sorted by x.  A labelled scatter with its own ``in 3/8``
drew ten labels beside six markers.  And a dropdown on a date variable
kept no rows: its options were "2001-01-02 00:00:00" and the script
compared them with the column's epoch milliseconds.
"""
import itertools
import json
import math
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (BooleanFilter, ColumnDataSource, CustomJS, Div,
                          LabelSet, Line, Select)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import JsSession  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from test_mode_parity import (_DF, _LABEL_NAMES, _VALUE_LABELS,  # noqa: E402
                              _arrows_of, _assert_heads_on_shafts, _diff,
                              _explain, _kpi, _layout_tree, _spec)
from test_mode_parity import _served_after_move  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_saved_moves_")

#: (label, filter(), widget kind, the value the widget is moved to -- a
#: Select by its option's LABEL --, the rows it keeps as an ``if``).  Each
#: keeps five of _DF's ten observations (2, 4, 6, 8, 10 for Foreign; 2, 4,
#: 5, 6, 7, 8, 10 by price >= 4500 ...), so every layer has rows to lose.
_MOVES = [
    ("dropdown to Foreign", "foreign, type(dropdown)", ("Select", "Foreign"),
     "foreign == 1"),
    ("range to 4500-11385", "price, type(range)",
     ("RangeSlider", (4500.0, 11385.0)), "price >= 4500 & price <= 11385"),
    ("slider to 4500", "price, type(slider)", ("Slider", 4500.0),
     "price >= 4500"),
]

#: Every plot type that draws one mark per observation.  The fitted and
#: binned types are recomputed by the script from the rows (agg_sources) or
#: are the saved page's documented exception (a fitted line is not refitted,
#: and is marked (WP-29 P0.17),
#: dash.sthlp "What a filter move redraws"); the literal types draw no data.
_ROW_TYPES = ["scatter", "line", "tsline", "connected", "area", "bar",
              "spike", "dropline", "dot", "rarea", "rbar", "rspike", "rcap",
              "rcapsym", "rscatter", "rline", "rconnected", "tsrline",
              "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter"]


# ---------------------------------------------------------------------------
# The page's own callback, run under node (test/js_runner.py, WP-28 S03)
# ---------------------------------------------------------------------------

from conftest import memo_build, render_models  # noqa: E402


def _run(code, args, cb_obj=None):
    """Run *code* under node with *args*; write what it left in every
    ColumnDataSource, BooleanFilter and Div back into the Python models."""
    return JsSession([]).run_code(code, args, cb_obj)


def _write(spec, df):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, _VALUE_LABELS, _LABEL_NAMES), fh)
    return sp, dp


def _render(spec, df=_DF):
    sp, dp = _write(spec, df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _profile(r):
    figs = []
    _layout_tree(r._last_layout_root, figs)
    # The arrowheads too: they were one fixed Arrow annotation per row,
    # outside the profile, so a move left them where they were drawn and
    # every pcarrow case here passed (BUGS.md, 24sep2026).
    return [{"glyphs": f["glyphs"],
             "labels": [a for a in f["annotations"]
                        if a["kind"] == "LabelSet"],
             "arrows": _arrows_of(f["annotations"])} for f in figs]


def _move(r, action):
    """Move the page's widget and run the page's own callback for it."""
    kind, want = action
    ws = [w for w in r.filter_widgets if type(w).__name__ == kind]
    assert len(ws) == 1, f"{len(ws)} {kind} widgets on the page"
    w = ws[0]
    if isinstance(w, Select):
        raw = [v for v, lab in w.options if lab == want]
        assert raw, f"no option labelled {want!r}: {w.options}"
        w.value = raw[0]
    else:
        w.value = want
    cb = r.filter_callbacks[r.filter_widgets.index(w)]
    assert cb.code == dr._FILTER_JS
    _run(cb.code, cb.args)


@memo_build()
def _saved_after_move(spec, action, df=_DF):
    r = _render(spec, df)
    _move(r, action)
    return _profile(r)


@memo_build()
def _saved_of_rows(spec, if_expr, df=_DF):
    """The saved page drawn from the rows the move keeps."""
    q = json.loads(json.dumps(spec))
    q["build_options"]["filter"] = ""
    for g in q["graphs"]:
        own = (g.get("if_expr") or "").strip()
        g["if_expr"] = f"({own}) & ({if_expr})" if own else if_expr
    for k in q["kpis"]:
        own = (k.get("if_expr") or "").strip()
        k["if_expr"] = f"({own}) & ({if_expr})" if own else if_expr
    return _profile(_render(q, df))


def _assert_same(name, after, oracle):
    assert len(after) == len(oracle), f"{name}: figure counts differ"
    for i, (a, b) in enumerate(zip(after, oracle)):
        diffs = _diff(a, b)
        assert not diffs, _explain(name, f"figure {i} after the move", diffs)


def _case(name, move, plots=None, go=None, graphs=None, bo=None, if_expr=""):
    _, filt, action, oracle = move
    spec = _spec(plots, dict(bo or {}, filter=filt), go, graphs, None,
                 if_expr)
    return pytest.param(spec, action, oracle, id=name)


_CORPUS = [
    *[_case(f"{t}, {m[0]}", m, [plot_for(t)])
      for t in _ROW_TYPES for m in _MOVES],
    *[_case(f"{t} under link(), {_MOVES[0][0]}", _MOVES[0], [plot_for(t)],
            bo={"link": "g1"})
      for t in ("line", "connected", "area", "bar", "spike", "dropline")],
    *[_case(f"{t} with its own in, {_MOVES[0][0]}", _MOVES[0],
            [plot_for(t, in_expr="3/8")])
      for t in ("scatter", "line", "tsline", "connected", "rconnected",
                "area", "bar", "spike", "dropline")],
    *[_case(f"{t} with its own if, {_MOVES[1][0]}", _MOVES[1],
            [plot_for(t, if_expr="mpg > 18")])
      for t in ("line", "connected", "rconnected", "pcarrow", "pcbarrow")],
    *[_case(f"{t} with its own in, {m[0]}", m, [plot_for(t, in_expr="3/8")])
      for t in ("pcarrow", "pcbarrow") for m in _MOVES],
    _case("a line under by(), range", _MOVES[1], [plot_for("line")],
          go={"by": "foreign"}),
    _case("a connected plot under a linked by(), dropdown", _MOVES[0],
          graphs=[("g1", [plot_for("connected")], {"by": "rep"}),
                  ("g2", [plot_for("scatter")])],
          bo={"link": "g1 g2"}),
    _case("a labelled scatter, dropdown", _MOVES[0],
          [plot_for("scatter", {"mlabel": "rep"})]),
    _case("a labelled scatter with its own in, dropdown", _MOVES[0],
          [plot_for("scatter", {"mlabel": "rep"}, in_expr="3/8")]),
    _case("a labelled connected plot with its own if, range", _MOVES[1],
          [plot_for("connected", {"mlabel": "rep"}, if_expr="mpg > 18")]),
    # WP-29 P0.15: a layer's own if inside a linked by() panel, or inside a
    # linked graph with its own if.  The page registered, for the callback
    # to rebuild the layer's view from, every row the layer's if selects in
    # the WHOLE dataset, so after a move each panel's layer drew the other
    # panel's rows too (measured: both panels drew observations
    # [1, 3, 4, 6, 7, 9] where the oracle draws [4, 6] and [1, 3, 7, 9]).
    *[_case(f"{t} with its own if under a linked by(), {_MOVES[1][0]}",
            _MOVES[1],
            graphs=[("g1", [plot_for("scatter"),
                            plot_for(t, if_expr="price > 4500")],
                     {"by": "foreign"}),
                    ("g2", [plot_for("scatter")])],
            bo={"link": "g1 g2"})
      for t in ("scatter", "connected", "dot", "rspike", "rconnected",
                "line", "area", "bar", "rcap")],
    *[_case(f"{t} with its own if in a linked graph with its own if, "
            f"{_MOVES[1][0]}", _MOVES[1],
            graphs=[("g1", [plot_for("scatter"),
                            plot_for(t, if_expr="price > 4500")], None,
                     {"if_expr": "foreign == 1"}),
                    ("g2", [plot_for("scatter")])],
            bo={"link": "g1 g2"})
      for t in ("scatter", "connected", "dot", "rspike", "rconnected",
                "line", "area", "bar", "rcap")],
    # WP-30 P1.24: each kept label keeps its own row's clock.
    _case("a scatter labelled at per-row clocks, dropdown", _MOVES[0],
          [plot_for("scatter", {"mlabel": "rep", "mlabvposition": "rep"})]),
    _case("a pcscatter labelled at per-row clocks, range", _MOVES[1],
          [plot_for("pcscatter", {"mlabel": "rep",
                                  "mlabvposition": "rep"})]),
    # WP-30 P1.8a: stairs and ascending breaks are rebuilt from the kept
    # rows (dash_join_rebuild).
    _case("a stairstep line (WP-30 P1.8a)", _MOVES[0],
          [plot_for("line", {"connect": "stairstep"})]),
    _case("an ascending cmissing(n) connected (WP-30 P1.8a)", _MOVES[0],
          [plot_for("connected", {"connect": "ascending",
                                  "cmissing": "n"})]),
    # WP-30 P1.9b: a turned layer after a saved move.
    _case("a turned bar, dropdown", _MOVES[0],
          [plot_for("bar", {"horizontal": "horizontal"})]),
    # (A histogram's bins stay over every row on the saved page, upright
    # or turned (WP-29 P0.17): test_horizontal_moves.py holds it.)
    _case("a turned rcap, range slider", _MOVES[1],
          [plot_for("rcap", {"horizontal": "horizontal"})]),
]


#: Both checks of a corpus case read its moved page (_saved_after_move,
#: kept per case): on one worker it is drawn once (02nov2026).
def xdist_group_of(item):
    if item.cls is not None and item.cls.__name__ == "TestEveryLayerFollowsAMove":
        return "sfl:" + item.callspec.id
    return None


@pytest.mark.parametrize("spec,action,oracle", _CORPUS)
class TestEveryLayerFollowsAMove:
    """After the page's own callback runs, every figure draws what the
    saved renderer draws of the rows the move keeps."""

    def test_the_page_draws_the_kept_rows(self, request, spec, action,
                                           oracle):
        name = request.node.callspec.id
        # Flipped (WP-31 B5c): dot's rows on the saved page are rebuilt
        # over the re-finished axis (dash_fill_dots), so the move to
        # Foreign is held like every other layer's.
        _assert_same(name, _saved_after_move(spec, action),
                     _saved_of_rows(spec, oracle))

    def test_the_move_changed_what_is_drawn(self, request, spec, action,
                                             oracle):
        """Guards the guard: the move is not a no-op for these layers."""
        name = request.node.callspec.id
        before = _profile(_render(spec))
        after = _saved_after_move(spec, action)
        assert _diff(before, after), f"{name}: the move changed nothing"


class TestTheArrowheadsFollowTheShafts:
    """``pcarrow mpg weight price foreign``: after a move each head is on
    the shaft it heads, and there is one per kept row.  Each head was one
    Arrow annotation fixed to its row: after a move to Foreign (Stata's
    ``count if foreign == 1'': 5) ten heads stayed beside five shafts
    (BUGS.md, measured 24sep2026 under node)."""

    @pytest.mark.parametrize("ptype", ["pcarrow", "pcbarrow"])
    @pytest.mark.parametrize("qual,want", [
        ({}, 5),
        # in 3/8 keeps observations 3 to 8, of which 4, 6 and 8 are foreign
        # (``count if foreign == 1 in 3/8'': 3).
        ({"in_expr": "3/8"}, 3),
        # if price > 4500: observations 2, 4, 5, 7, 8, 10; foreign 2, 4, 8,
        # 10 (``count if foreign == 1 & price > 4500'': 4).
        ({"if_expr": "price > 4500"}, 4)])
    def test_one_head_per_kept_shaft(self, ptype, qual, want):
        spec = _spec([plot_for(ptype, **qual)], {"filter": _MOVES[0][1]})
        r = _render(spec)
        _move(r, _MOVES[0][2])
        [fig] = _profile_full(r)
        heads = _arrows_of(fig["annotations"])
        assert len(heads) == want, heads
        _assert_heads_on_shafts(ptype, fig)

    def test_the_heads_draw_from_the_shafts_copy(self):
        """One head script over the copy the shaft draws, which the filter
        script rewrites -- not a model per row, which it cannot reach.
        Flipped (WP-31 C1): an Arrow annotation's source before; now the
        arrowhead script's ``src``, which a data change of it re-runs."""
        r = _render(_spec([plot_for("pcarrow")], {"filter": _MOVES[0][1]}))
        [fig] = r.figures.values()
        [head] = [m for m in fig.references() if isinstance(m, CustomJS)
                  and m.name == "dash_arrow_head"]
        [seg] = [g for g in fig.renderers
                 if type(g.glyph).__name__ == "Segment"]
        assert head.args["src"] is seg.data_source
        assert head in seg.data_source.js_property_callbacks["change:data"]
        assert any(s is head.args["src"]
                   for s in r.derived_source_registry["g1"])


class TestTheArrowHeadHelper:
    """``GlyphMapper._add_arrow_heads``: one Arrow over the source given,
    its ends that source's columns; nothing for a source with no rows."""

    def test_one_annotation_reading_the_columns(self):
        from bokeh.models import Arrow, OpenHead
        from bokeh.plotting import figure
        fig = figure()
        src = ColumnDataSource({"a": [1.0, 2.0], "b": [3.0, 4.0],
                                "c": [5.0, 6.0], "d": [7.0, 8.0]})
        head = dr.GlyphMapper._add_arrow_heads(
            fig, src, "b", "a", "d", "c", "#ff0000", 2.0, end=OpenHead())
        assert [m for m in fig.center if isinstance(m, Arrow)] == [head]
        assert head.source is src
        assert (head.x_start.field, head.y_start.field, head.x_end.field,
                head.y_end.field) == ("a", "b", "c", "d")
        assert head.start is None and head.line_width == 2.0

    def test_no_rows_adds_nothing(self):
        from bokeh.models import OpenHead
        from bokeh.plotting import figure
        fig = figure()
        src = ColumnDataSource({"a": [], "b": [], "c": [], "d": []})
        assert dr.GlyphMapper._add_arrow_heads(
            fig, src, "b", "a", "d", "c", "#000000", 1.0,
            end=OpenHead()) is None
        from bokeh.models import Arrow
        assert not [m for m in fig.center if isinstance(m, Arrow)]

    def test_ten_thousand_arrows_are_one_model(self):
        """Resource exhaustion: an arrow per observation of a large
        dataset is one annotation, not ten thousand models."""
        from bokeh.models import Arrow
        from bokeh.plotting import figure
        n = 10000
        src = ColumnDataSource({"y1": np.arange(n, dtype=float),
                                "x1": np.arange(n, dtype=float),
                                "y2": np.arange(n, dtype=float) + 1,
                                "x2": np.arange(n, dtype=float) + 1})
        fig = figure()
        dr.GlyphMapper().map_pcarrow(fig, src, "y1", "x1", "y2", "x2", {})
        # WP-31 C1: one head glyph over one (empty) head source, filled in
        # the browser; no Arrow annotation.
        assert not [m for m in fig.center if isinstance(m, Arrow)]
        assert len([r for r in fig.renderers
                    if "dash-arrowhead" in (r.tags or [])]) == 1


def _profile_full(r):
    figs = []
    _layout_tree(r._last_layout_root, figs)
    return figs


class TestTheLineFollowsTheMoveAsTwowayDraws:
    """The rows a moved line draws, held to Stata's own count: _DF's
    foreign == 1 observations are 2, 4, 6, 8 and 10 (``count if foreign ==
    1'), and twoway line and connected join them in the data's order,
    weight 3350, 1800, 3100, 2010, 2650; tsline in time order, 1800, 2010,
    2650, 3100, 3350.  Flipped (WP-29 P0.1): line and connected were held
    to x order, which twoway draws only under sort."""

    @pytest.mark.parametrize("ptype", ["line", "tsline", "connected"])
    def test_the_line_draws_the_foreign_cars_in_x_order(self, ptype):
        spec = _spec([plot_for(ptype)], {"filter": _MOVES[0][1]})
        r = _render(spec)
        _move(r, _MOVES[0][2])
        [fig] = r.figures.values()
        [line] = [g for g in fig.renderers if isinstance(g.glyph, Line)]
        xs = [float(x) for x in line.data_source.data["weight"]]
        want = ([1800.0, 2010.0, 2650.0, 3100.0, 3350.0] if ptype == "tsline"
                else [3350.0, 1800.0, 3100.0, 2010.0, 2650.0])
        assert xs == want, xs


class TestAJitteredScatterFollowsAMove:
    """A jittered scatter draws from a copy holding the jittered points.
    A move keeps the points of the rows it keeps, each where it was drawn:
    the jitter is random, so a fresh draw of the kept rows lands elsewhere
    and is not the oracle here.  The slider at 4500 keeps observations 2,
    4, 5, 7, 8 and 10 (``count if price >= 4500'': 6)."""

    @pytest.mark.parametrize("qual", [{}, {"in_expr": "2/9"}])
    def test_the_kept_points_stay_where_they_were(self, qual):
        spec = _spec([plot_for("scatter", {"jitter": "5", "jitterseed": "7"},
                               **qual)], {"filter": _MOVES[2][1]})
        r = _render(spec)
        [fig] = r.figures.values()
        [sc] = [g for g in fig.renderers
                if type(g.glyph).__name__ == "Scatter"]
        # No view: a view's flags would go stale on a shortened copy.
        assert not isinstance(getattr(sc.view, "filter", None),
                              BooleanFilter)
        src = sc.data_source
        rid = dr._ROW_ID_COLUMN
        # G1 (WP-28): the jitter columns are named under the __dash prefix.
        before = {int(i): (x, y) for i, x, y in zip(
            src.data[rid], src.data[dr._DASH_JITTER_X],
            src.data[dr._DASH_JITTER_Y])}
        _move(r, _MOVES[2][2])
        after = {int(i): (x, y) for i, x, y in zip(
            src.data[rid], src.data[dr._DASH_JITTER_X],
            src.data[dr._DASH_JITTER_Y])}
        want_positions = {1, 3, 4, 6, 7, 9}
        if qual:
            want_positions &= set(range(1, 9))   # in 2/9: observations 2..9
        # Flipped (WP-29 P0.11): row ids are the page's ranks, so the
        # observations are mapped through them (identity when every row is
        # on the page; the in 2/9 page holds observations 2..9 only).
        want = {r._row_pos[r.df.index[p]] for p in want_positions}
        assert set(after) == want, sorted(after)
        assert all(after[i] == pytest.approx(before[i]) for i in after)


class TestNoCopyIsDrawnThroughAView:
    """A copy a mapper built is drawn with no view: the view's flags are
    sized to the caller's source, so on a copy they pick rows by position,
    and they go stale when the callback shortens it.  A connected glyph
    drawn through a filtered view is also what Bokeh refuses as E-1024,
    which a linked by() graph with a line printed twice on every build
    (BUGS.md, WP-24)."""

    @pytest.mark.parametrize("spec", [
        _spec(None, {"link": "g1 g2"}, graphs=[
            ("g1", [plot_for(t)], {"by": "foreign"}),
            ("g2", [plot_for("scatter")])])
        for t in ("line", "connected", "rconnected", "rline", "dropline",
                  "rcap", "rcapsym", "rbar")
    ] + [_spec([plot_for(t, in_expr="3/8")]) for t in _ROW_TYPES],
        ids=[f"linked by() {t}" for t in (
            "line", "connected", "rconnected", "rline", "dropline", "rcap",
            "rcapsym", "rbar")] + [f"{t} in 3/8" for t in _ROW_TYPES])
    def test_views_are_over_graph_sources_only(self, spec):
        from bokeh.core.validation import check_integrity
        r = _render(spec)
        graph = {id(s) for s in r.sources.values()}
        for fig in r.figures.values():
            for g in fig.renderers:
                flt = getattr(getattr(g, "view", None), "filter", None)
                if isinstance(flt, BooleanFilter):
                    assert id(g.data_source) in graph, (
                        type(g.glyph).__name__, "drawn from a copy through "
                        "a view")
        models = set(r._last_layout_root.references())
        codes = {i.code for i in check_integrity(models).error}
        assert 1024 not in codes, codes


# ---------------------------------------------------------------------------
# The helpers, one by one
# ---------------------------------------------------------------------------

class TestTheCollectedCopies:
    """``DashRenderer._collect_derived_sources``: the copies of rows a
    figure draws from, and nothing else."""

    def test_a_line_copy_is_listed_and_a_fit_and_the_graph_source_are_not(
            self):
        r = _render(_spec([plot_for("line"), plot_for("lfit"),
                           plot_for("histogram")]))
        [(name, copies)] = r.derived_source_registry.items()
        assert name == "g1"
        [line] = [g for g in r.figures["g1"].renderers
                  if isinstance(g.glyph, Line)
                  and "weight" in g.data_source.data]
        assert len(copies) == 1 and copies[0] is line.data_source
        assert all(s is not r.sources["g1"] for s in copies)
        assert all(dr._ROW_ID_COLUMN in s.data for s in copies)

    def test_a_label_copy_is_listed(self):
        r = _render(_spec([plot_for("scatter", {"mlabel": "rep"},
                                    in_expr="3/8")]))
        [labels] = [m for m in r.figures["g1"].center
                    if isinstance(m, LabelSet)]
        assert any(s is labels.source
                   for s in r.derived_source_registry["g1"])

    def test_a_plain_scatter_has_none(self):
        r = _render(_spec([plot_for("scatter")]))
        assert r.derived_source_registry == {}

    def test_an_excluded_graphs_copies_are_not_written(self):
        spec = _spec(None, {"filter": "foreign, type(dropdown) exclude(g1)"},
                     graphs=[("g1", [plot_for("line")]),
                             ("g2", [plot_for("line")])])
        r = _render(spec)
        [cb] = r.filter_callbacks
        written = {id(s) for s in cb.args["derived_sources"]}
        assert not written & {id(s) for s in
                              r.derived_source_registry["g1"]}
        assert {id(s) for s in r.derived_source_registry["g2"]} <= written


class TestTheSubsetSource:
    """``GlyphMapper._subset_source``: the rows a mask keeps, every
    column, in order, a date column still an array."""

    def test_rows_columns_and_order(self):
        src = ColumnDataSource({
            "a": [1.0, 2.0, 3.0], "s": ["x", "y", "z"],
            "d": np.array(["2001-01-01", "NaT", "2001-01-03"],
                          dtype="datetime64[ms]")})
        out = dr.GlyphMapper._subset_source(src, [True, False, True])
        assert out is not src
        assert list(out.data["a"]) == [1.0, 3.0]
        assert list(out.data["s"]) == ["x", "z"]
        assert out.data["d"].dtype.kind == "M"
        assert list(out.data["d"].astype("int64")) == [978307200000,
                                                       978480000000]


class TestTheSpacingTag:
    """No width is taken from the rows' spacing any more, so nothing records
    a rule for the page's script to recompute (WP-30 P1.17a)."""

    def test_the_rule_is_recorded(self):
        """Flipped (WP-30 P1.17a): twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a); no source is tagged."""
        assert not hasattr(dr.GlyphMapper, "_tag_spacing")
        for ptype in ("bar", "rbar"):
            r = _render(_spec([plot_for(ptype)], {"filter": _MOVES[0][1]}))
            for g in r.figures["g1"].renderers:
                assert not hasattr(g.data_source, "_dash_spacing"), ptype

    @pytest.mark.parametrize("ptype,attr", [("bar", "width"),
                                            ("rbar", "width")])
    def test_a_moved_bar_is_as_wide_as_its_kept_rows_are_spaced(self, ptype,
                                                                 attr):
        """A bar is one x unit wide before and after a move, whatever the
        kept rows' spacing.

        Flipped (WP-30 P1.17a): 56 then 168 was wrong because twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        spec = _spec([plot_for(ptype)], {"filter": _MOVES[0][1]})
        r = _render(spec)
        [bar] = [g for g in r.figures["g1"].renderers
                 if type(g.glyph).__name__ == "VBar"]
        assert bar.glyph.width == pytest.approx(1.0)
        _move(r, _MOVES[0][2])
        assert bar.glyph.width == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Adversarial: what the new arguments carry
# ---------------------------------------------------------------------------

class TestTheCopiesAgainstHostileInput:
    """The copies' column names are the user's variable names, and they
    become JavaScript property keys in the page's script."""

    @pytest.mark.parametrize("name", ["__proto__", "constructor",
                                      "hasOwnProperty"])
    def test_a_variable_named_after_an_object_property_is_kept(self, name):
        df = _DF.rename(columns={"weight": name})
        spec = _spec([{"type": "line", "yvar": "mpg", "xvar": name,
                       "options": {}}], {"filter": _MOVES[0][1]})
        r = _render(spec, df)
        _move(r, _MOVES[0][2])
        [line] = [g for g in r.figures["g1"].renderers
                  if isinstance(g.glyph, Line)]
        xs = [float(x) for x in line.data_source.data[name]]
        # Flipped (WP-29 P0.1): the Foreign cars in the data's order, as
        # twoway joins a line; the name survives either way.
        assert xs == [3350.0, 1800.0, 3100.0, 2010.0, 2650.0], xs

    def test_the_spacing_travels_as_data_not_code(self):
        """Nothing is spliced into the script's text, and no spacing rule
        reaches the page at all.

        Flipped (WP-30 P1.17a): the derived_spacing_json argument is gone
        because twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        r = _render(_spec([plot_for("bar")], {"filter": _MOVES[0][1]}))
        [cb] = r.filter_callbacks
        assert cb.code == dr._FILTER_JS
        assert "derived_spacing_json" not in cb.args
        assert "derived_spacing_glyphs" not in cb.args

    def test_the_copies_snapshots_are_shared_by_every_filter(self):
        """One snapshot per copy, however many filters: a copy per
        callback would grow the page with the filter count, as the
        whole-frame snapshot once did (test_filter_payload_size.py)."""
        spec = _spec([plot_for("line")],
                     {"filter": "foreign, type(dropdown) || "
                                "price, type(range) || mpg, type(slider)"})
        r = _render(spec)
        assert len(r.filter_callbacks) == 3
        snaps = [cb.args["derived_sources_orig"] for cb in
                 r.filter_callbacks]
        assert all(len(s) == 1 for s in snaps)
        assert snaps[0][0] is snaps[1][0] is snaps[2][0]


# ---------------------------------------------------------------------------
# A layer's own if()/in(), as twoway draws it (no move)
# ---------------------------------------------------------------------------

class TestALinesOwnQualifier:
    """``(line mpg weight in 3/8)``: twoway's serset holds observations 3 to
    8, x 2200, 1800, 3000, 3100, 4080, 2010 (measured 24sep2026, BUGS.md),
    and joins them in that, the data's, order (WP-29 P0.1; tsline joins in
    time order).  The saved page drew 2200, 2650, 2930, 3000, 3100, 3350:
    rows 3 to 8 of a copy sorted by x.  ``if mpg > 18' selects observations
    1, 3, 4, 5, 6, 8, 10 (mpg 22, 25, 30, 21, 19, 28, 23).  Flipped (WP-29
    P0.1): line, connected and rconnected were held to x order."""

    _IN_3_8 = [2200.0, 1800.0, 3000.0, 3100.0, 4080.0, 2010.0]
    _IF = [2930.0, 2200.0, 1800.0, 3000.0, 3100.0, 2010.0, 2650.0]

    def _lines(self, plot):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = _render(_spec([plot]))
        [fig] = r.figures.values()
        return ([g for g in fig.renderers if isinstance(g.glyph, Line)],
                caught)

    @pytest.mark.parametrize("ptype", ["line", "tsline", "connected"])
    @pytest.mark.parametrize("qual,want", [
        ({"in_expr": "3/8"}, _IN_3_8), ({"if_expr": "mpg > 18"}, _IF)])
    def test_the_line_draws_the_observations_twoway_draws(self, ptype, qual,
                                                          want):
        [line], _ = self._lines(plot_for(ptype, **qual))
        # Drawn from its own rows: no view is left to apply to them.
        assert not isinstance(getattr(line.view, "filter", None),
                              BooleanFilter)
        xs = [float(x) for x in line.data_source.data["weight"]]
        if ptype == "tsline":
            want = sorted(want)
        assert xs == want, xs

    def test_rconnected_draws_both_ends_from_the_same_rows(self):
        lines, _ = self._lines(plot_for("rconnected", in_expr="3/8"))
        assert len(lines) == 2
        for line in lines:
            xs = [float(x) for x in line.data_source.data["weight"]]
            assert xs == self._IN_3_8, xs


class TestALabelledScattersOwnQualifier:
    """``(scatter mpg weight in 3/8, mlabel(rep))``: twoway's serset holds
    six observations, labelled rep 3, 5, 4, 3, 5, 4 (observations 3 to 8);
    the saved page drew ten labels beside six markers."""

    def test_six_labels_beside_six_markers(self):
        r = _render(_spec([plot_for("scatter", {"mlabel": "rep"},
                                    in_expr="3/8")]))
        [fig] = _profile(r)
        [lab] = fig["labels"]
        assert lab["texts"] == ["3", "5", "4", "3", "5", "4"], lab["texts"]
        assert fig["glyphs"][0]["rows"] == 6


# ---------------------------------------------------------------------------
# A scatter with a missing plotted value
# ---------------------------------------------------------------------------

#: _DF with mpg missing on observations 3 and 4 (one domestic, one
#: foreign): Stata's ``count if foreign == 1 & !missing(mpg)'' is 4
#: (observations 2, 6, 8, 10), and the scatter draws 8 before the move.
_DF_MISSING = _DF.assign(mpg=[22.0, 17.0, np.nan, np.nan, 21.0, 19.0, 14.0,
                              28.0, 16.0, 23.0])


class TestAScatterWithAMissingValue:
    """On auto, ``scatter mpg rep78`` stayed at 69 rows after a move to
    Foreign, where Stata's ``count if foreign == 1 & !missing(rep78)`` is
    21 (measured, BUGS.md); the copy it draws, without the missing rows,
    was outside both scripts."""

    def _spec(self, kpis=None):
        return _spec([plot_for("scatter")], {"filter": _MOVES[0][1]},
                     kpis=kpis)

    def test_the_move_keeps_the_foreign_cars_with_mpg(self):
        after = _saved_after_move(self._spec(), _MOVES[0][2], _DF_MISSING)
        assert after[0]["glyphs"][0]["rows"] == 4
        _assert_same("scatter with a missing mpg", after,
                     _saved_of_rows(self._spec(), _MOVES[0][3], _DF_MISSING))

    def test_a_brush_on_it_recomputes_the_card(self):
        k = _kpi(update="brush", stat="mean", var="price")
        r = _render(self._spec([k]), _DF_MISSING)
        [fig] = r.figures.values()
        [sc] = [g for g in fig.renderers
                if type(g.glyph).__name__ == "Scatter"]
        src = sc.data_source
        cbs = [c for c in src.selected.js_property_callbacks.get(
            "change:indices", []) if isinstance(c, CustomJS)]
        assert len(cbs) == 1, "the drawn source carries no brush script"
        # Brush the first two points it draws: observations 1 and 2,
        # price 4099 and 4749 -- a mean of 4424.
        src.selected.indices = [0, 1]
        _run(cbs[0].code, cbs[0].args, cb_obj=src.selected)
        text = r.kpi_divs["k1"].text
        assert ">4424<" in text, text


class TestALinkedScatterWithAMissingValue:
    """``link(g1 g2)`` with g1 ``scatter mpg weight`` -- mpg missing on
    observations 3 and 4 -- and g2 ``scatter price weight``: a selection of
    observations 1 to 4 in g2 shows on g1 as observations 1 and 2, the two
    of them g1 draws.  g1 drew from its own copy without the missing rows,
    whose selection nothing wrote, so a linked selection never reached it
    (BUGS.md, measured 24sep2026)."""

    def _render(self, bo=None):
        spec = _spec(None, dict({"link": "g1 g2"}, **(bo or {})), graphs=[
            ("g1", [plot_for("scatter")]),
            ("g2", [{"type": "scatter", "yvar": "price", "xvar": "weight",
                     "options": {}}])])
        return _render(spec, _DF_MISSING)

    @staticmethod
    def _scatter(r, name):
        [sc] = [g for g in r.figures[name].renderers
                if type(g.glyph).__name__ == "Scatter"]
        return sc

    @staticmethod
    def _drawn_rows(sc):
        n = len(sc.data_source.data[dr._ROW_ID_COLUMN])
        flt = getattr(getattr(sc, "view", None), "filter", None)
        bools = getattr(flt, "booleans", None)
        return [i for i in range(n) if bools is None or bools[i]]

    def _select(self, sc, indices):
        """Select *indices* of *sc*'s source and run every script the page
        hangs on that selection, as BokehJS would."""
        sc.data_source.selected.indices = list(indices)
        for cb in sc.data_source.selected.js_property_callbacks.get(
                "change:indices", []):
            if isinstance(cb, CustomJS):
                _run(cb.code, cb.args, cb_obj=sc.data_source.selected)

    @staticmethod
    def _selected_observations(sc, drawn):
        ids = sc.data_source.data[dr._ROW_ID_COLUMN]
        return sorted(int(ids[i]) + 1 for i in sc.data_source.selected.indices
                      if i in set(drawn))

    def test_it_draws_the_eight_observations_with_mpg(self):
        r = self._render()
        g1 = self._scatter(r, "g1")
        ids = g1.data_source.data[dr._ROW_ID_COLUMN]
        assert sorted(int(ids[i]) + 1 for i in self._drawn_rows(g1)) == [
            1, 2, 5, 6, 7, 8, 9, 10]

    def test_a_selection_in_the_linked_graph_shows_on_it(self):
        r = self._render()
        g1, g2 = self._scatter(r, "g1"), self._scatter(r, "g2")
        ids2 = list(g2.data_source.data[dr._ROW_ID_COLUMN])
        self._select(g2, [ids2.index(k) for k in (0, 1, 2, 3)])
        assert self._selected_observations(g1, self._drawn_rows(g1)) == [1, 2]

    def test_a_selection_on_it_shows_in_the_linked_graph(self):
        r = self._render()
        g1, g2 = self._scatter(r, "g1"), self._scatter(r, "g2")
        drawn = self._drawn_rows(g1)
        # Its first two drawn points: observations 1 and 2.
        self._select(g1, drawn[:2])
        assert self._selected_observations(g2, self._drawn_rows(g2)) == [1, 2]

    def test_the_view_helper_leaves_other_sources_alone(self):
        """``DashRenderer._linked_scatter_view``: a view only over the link
        group's source, only with a missing value -- jittered or not: a
        jittered scatter draws through it too (TestALinkedJitteredScatter)."""
        r = self._render()
        shared = r.sources["g1"]
        assert r._dash_linked_source is shared
        view = r._linked_scatter_view(shared, "mpg", "weight", {}, None)
        assert list(view.filter.booleans) == [
            not math.isnan(v) for v in _DF_MISSING["mpg"]]
        assert r._linked_scatter_view(shared, "price", "weight", {},
                                      None) is None
        jview = r._linked_scatter_view(shared, "mpg", "weight",
                                       {"jitter": "5"}, None)
        assert list(jview.filter.booleans) == list(view.filter.booleans)
        other = ColumnDataSource(dict(shared.data))
        assert r._linked_scatter_view(other, "mpg", "weight", {},
                                      None) is None

    def test_the_view_helper_keeps_the_layers_own_view(self):
        from bokeh.models import CDSView
        r = self._render()
        shared = r.sources["g1"]
        own = CDSView(filter=BooleanFilter(booleans=[True] * 5 + [False] * 5))
        view = r._linked_scatter_view(shared, "mpg", "weight", {}, own)
        # observations 1-5 minus 3 and 4, whose mpg is missing
        assert list(view.filter.booleans) == [True, True, False, False,
                                              True] + [False] * 5

    def test_a_hostile_variable_name_is_only_a_column(self):
        """Injection: the names reach no script's text; a variable named
        after an object property is masked like any other."""
        df = _DF_MISSING.rename(columns={"mpg": "__proto__"})
        spec = _spec(None, {"link": "g1 g2"}, graphs=[
            ("g1", [{"type": "scatter", "yvar": "__proto__",
                     "xvar": "weight", "options": {}}]),
            ("g2", [{"type": "scatter", "yvar": "price", "xvar": "weight",
                     "options": {}}])])
        r = _render(spec, df)
        g1, g2 = self._scatter(r, "g1"), self._scatter(r, "g2")
        assert g1.data_source is g2.data_source
        assert len(self._drawn_rows(g1)) == 8

    def test_a_move_keeps_the_foreign_cars_with_mpg(self):
        """After a move to Foreign it draws observations 2, 6, 8 and 10
        (Stata's ``count if foreign == 1 & !missing(mpg)'': 4)."""
        r = self._render({"filter": _MOVES[0][1]})
        _move(r, _MOVES[0][2])
        g1 = self._scatter(r, "g1")
        ids = g1.data_source.data[dr._ROW_ID_COLUMN]
        assert sorted(int(ids[i]) + 1 for i in self._drawn_rows(g1)) == [
            2, 6, 8, 10]


class TestALinkedJitteredScatter:
    """``link(g1 g2)`` with g1 ``scatter mpg weight, jitter(5)
    jitterseed(7)`` -- mpg missing on observations 3 and 4 -- and g2
    ``scatter price weight``.  The jittered points were columns of a copy
    of the rows, outside the shared source whose selection IS the link, so
    a selection in g2 never showed on g1 nor one on g1 in g2 (BUGS.md,
    measured 24sep2026 under node).  The jittered columns now live on the
    shared source, one pair per layer, drawn through the layer's view; the
    points are the ones jitter() drew before: ``_apply_jitter`` over the
    layer's rows with both values, in order, with the same seed."""

    _L = TestALinkedScatterWithAMissingValue
    _J = {"jitter": "5", "jitterseed": "7"}

    def _spec(self, bo=None, qual=None, yvar="mpg", g2=None, g1=None):
        return _spec(None, dict({"link": "g1 g2"}, **(bo or {})), graphs=[
            ("g1", g1 or [dict({"type": "scatter", "yvar": yvar,
                                "xvar": "weight", "options": dict(self._J)},
                               **(qual or {}))]),
            ("g2", g2 or [{"type": "scatter", "yvar": "price",
                           "xvar": "weight", "options": {}}])])

    def _render(self, bo=None, qual=None, df=_DF_MISSING, **kw):
        return _render(self._spec(bo, qual, **kw), df)

    @staticmethod
    def _points(sc, rows):
        """{observation: (x, y)} of the drawn *rows* of *sc*."""
        d = sc.data_source.data
        ids = d[dr._ROW_ID_COLUMN]
        return {int(ids[i]) + 1: (float(d[sc.glyph.x][i]),
                                  float(d[sc.glyph.y][i])) for i in rows}

    @staticmethod
    def _expected(obs, df=_DF_MISSING, yvar="mpg"):
        """What jitter(5) jitterseed(7) drew for observations *obs*."""
        idx = [o - 1 for o in obs]
        x = np.asarray(df["weight"], dtype=float)[idx]
        y = np.asarray(df[yvar], dtype=float)[idx]
        xj, yj = dr._apply_jitter(x, y, 5.0, 7)
        return {o: (float(a), float(b)) for o, a, b in zip(obs, xj, yj)}

    def test_it_draws_from_the_linked_source(self):
        r = self._render()
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        assert g1.data_source is g2.data_source

    def test_it_draws_the_points_jitter_drew(self):
        r = self._render()
        g1 = self._L._scatter(r, "g1")
        got = self._points(g1, self._L._drawn_rows(g1))
        want = self._expected([1, 2, 5, 6, 7, 8, 9, 10])
        assert sorted(got) == sorted(want)
        for o in want:
            assert got[o] == pytest.approx(want[o]), o

    def test_a_selection_in_the_linked_graph_shows_on_it(self):
        r = self._render()
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        ids2 = list(g2.data_source.data[dr._ROW_ID_COLUMN])
        self._L._select(self._L, g2, [ids2.index(k) for k in (0, 1, 2, 3)])
        assert self._L._selected_observations(
            g1, self._L._drawn_rows(g1)) == [1, 2]

    def test_a_selection_on_it_shows_in_the_linked_graph(self):
        r = self._render()
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        drawn = self._L._drawn_rows(g1)
        self._L._select(self._L, g1, drawn[:2])
        assert self._L._selected_observations(
            g2, self._L._drawn_rows(g2)) == [1, 2]

    def test_without_a_missing_value_it_is_linked_too(self):
        r = self._render(df=_DF)
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        assert g1.data_source is g2.data_source
        got = self._points(g1, self._L._drawn_rows(g1))
        want = self._expected(list(range(1, 11)), _DF)
        assert sorted(got) == sorted(want)
        assert all(got[o] == pytest.approx(want[o]) for o in want)

    def test_its_own_in_draws_its_rows_where_jitter_drew_them(self):
        """``in 2/9``: observations 2 and 5 to 9 (3 and 4 have no mpg)."""
        r = self._render(qual={"in_expr": "2/9"})
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        assert g1.data_source is g2.data_source
        got = self._points(g1, self._L._drawn_rows(g1))
        want = self._expected([2, 5, 6, 7, 8, 9])
        assert sorted(got) == sorted(want)
        assert all(got[o] == pytest.approx(want[o]) for o in want)

    @pytest.mark.parametrize("qual,want", [
        ({}, {2, 6, 8, 10}),
        ({"in_expr": "2/9"}, {2, 6, 8}),
    ])
    def test_a_move_keeps_its_rows_where_they_were(self, qual, want):
        """A move to Foreign: Stata's ``count if foreign == 1 &
        !missing(mpg)'' is 4, and 3 of them in 2/9."""
        r = self._render({"filter": _MOVES[0][1]}, qual)
        g1 = self._L._scatter(r, "g1")
        before = self._points(g1, self._L._drawn_rows(g1))
        _move(r, _MOVES[0][2])
        after = self._points(g1, self._L._drawn_rows(g1))
        assert set(after) == want
        assert all(after[o] == pytest.approx(before[o]) for o in after)

    def test_two_jittered_layers_keep_their_own_columns(self):
        r = self._render(g2=[{"type": "scatter", "yvar": "price",
                              "xvar": "weight", "options": dict(self._J)}])
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        assert g1.data_source is g2.data_source
        assert {g1.glyph.x, g1.glyph.y}.isdisjoint({g2.glyph.x, g2.glyph.y})
        got = self._points(g2, self._L._drawn_rows(g2))
        want = self._expected(list(range(1, 11)), yvar="price")
        assert all(got[o] == pytest.approx(want[o]) for o in want)

    def test_a_variable_named_like_the_jitter_column_is_kept(self):
        """A Stata variable may be called ``_x_jit``: the glyph now draws
        ``__dash_xjit`` (G1, WP-28), so the variable's own column is never
        touched and its values stay as they were."""
        df = _DF_MISSING.rename(columns={"price": "_x_jit"})
        r = self._render(df=df, g2=[{"type": "scatter", "yvar": "_x_jit",
                                     "xvar": "weight", "options": {}}])
        g1 = self._L._scatter(r, "g1")
        assert g1.glyph.x != "_x_jit"
        d = g1.data_source.data
        assert [float(v) for v in d["_x_jit"]] == [
            float(df["_x_jit"][int(k)]) for k in d[dr._ROW_ID_COLUMN]]

    def test_the_column_helper(self):
        """``GlyphMapper._linked_jitter_columns``: only a link group's
        source; the view's rows with both values get the points, NaN the
        rest; jitter(0) draws the layer's own columns."""
        from bokeh.models import CDSView
        m = dr.GlyphMapper()
        d = {"x": [1.0, 2.0, 3.0, 4.0], "y": [5.0, np.nan, 7.0, 8.0]}
        plain = ColumnDataSource(dict(d))
        assert m._linked_jitter_columns(plain, "x", "y", self._J,
                                        None) is None
        src = ColumnDataSource(dict(d))
        src._dash_link_source = True
        view = CDSView(filter=BooleanFilter(booleans=[True, True, True,
                                                      False]))
        got = m._linked_jitter_columns(src, "x", "y", self._J, view)
        # G1 (WP-28): the jitter columns are named under the __dash prefix.
        assert got == (src, dr._DASH_JITTER_X, dr._DASH_JITTER_Y)
        xj, yj = dr._apply_jitter(np.array([1.0, 3.0]), np.array([5.0, 7.0]),
                                  5.0, 7)
        xs = list(src.data[dr._DASH_JITTER_X])
        assert math.isnan(xs[1]) and math.isnan(xs[3])
        assert [xs[0], xs[2]] == pytest.approx(list(xj))
        assert [src.data[dr._DASH_JITTER_Y][i] for i in (0, 2)] == pytest.approx(
            list(yj))
        # A second layer names its columns past the first's.
        assert m._linked_jitter_columns(src, "x", "y", self._J, None)[1:] \
            == (f"{dr._DASH_JITTER_X}_2", f"{dr._DASH_JITTER_Y}_2")
        assert m._linked_jitter_columns(src, "x", "y", {"jitter": "0"},
                                        None) == (src, "x", "y")

    def test_a_hostile_variable_name_is_only_a_column(self):
        """Injection: a variable named after an object property is jittered
        and masked like any other, through a move, and the page's script
        is the fixed text, which no variable name reaches."""
        df = _DF_MISSING.rename(columns={"mpg": "__proto__"})
        r = self._render({"filter": _MOVES[0][1]}, df=df, yvar="__proto__")
        g1, g2 = self._L._scatter(r, "g1"), self._L._scatter(r, "g2")
        assert g1.data_source is g2.data_source
        assert len(self._L._drawn_rows(g1)) == 8
        assert all(cb.code == dr._FILTER_JS for cb in r.filter_callbacks)
        _move(r, _MOVES[0][2])
        assert set(self._points(g1, self._L._drawn_rows(g1))) == {
            2, 6, 8, 10}

    def test_many_jittered_layers_add_two_columns_each(self):
        """Resource exhaustion: thirty jittered layers in one linked graph
        add sixty columns, no more, each pair distinct."""
        r = self._render(g1=[{"type": "scatter", "yvar": "mpg",
                              "xvar": "weight", "options": dict(self._J)}
                             for _ in range(30)])
        shared = r._dash_linked_source
        scs = [g for g in r.figures["g1"].renderers
               if type(g.glyph).__name__ == "Scatter"]
        assert len(scs) == 30
        assert all(s.data_source is shared for s in scs)
        cols = {c for s in scs for c in (s.glyph.x, s.glyph.y)}
        assert len(cols) == 60
        base = set(_render(self._spec(g1=[{
            "type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": {}}]), _DF_MISSING)._dash_linked_source.data)
        assert set(shared.data) - base == cols


def _served_doc(spec, df):
    """The generated server app's document for *spec* over *df*."""
    from bokeh.document import Document
    sp, dp = _write(spec, df)
    ap = os.path.join(_TMP, f"app_{next(_SEQ)}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_served_jit_{next(_SEQ)}", draw=False)
        doc = Document()
        mod.make_document(doc)
    return doc


class TestALinkedJitteredScatterServed:
    """The served app draws the same scatter the same way: from the link
    group's source, the points jitter() drew, following a move."""

    _T = TestALinkedJitteredScatter

    @staticmethod
    def _scatters(doc):
        from bokeh.models import GlyphRenderer
        out = {}
        for m in doc.select({"type": GlyphRenderer}):
            if type(m.glyph).__name__ != "Scatter":
                continue
            out["g2" if m.glyph.y == "price" else "g1"] = m
        return out

    @staticmethod
    def _rows(sc):
        from test_mode_parity import _drawn
        return _drawn(sc)[1]

    @staticmethod
    def _points(sc, rows):
        d = sc.data_source.data
        lab = d["index"]
        return {int(lab[i]) + 1: (float(d[sc.glyph.x][i]),
                                  float(d[sc.glyph.y][i])) for i in rows}

    @pytest.mark.parametrize("qual,obs", [
        ({}, [1, 2, 5, 6, 7, 8, 9, 10]),
        ({"in_expr": "2/9"}, [2, 5, 6, 7, 8, 9]),
    ])
    def test_it_is_linked_and_draws_what_the_saved_page_draws(self, qual,
                                                               obs):
        t = self._T()
        doc = _served_doc(t._spec(None, qual), _DF_MISSING)
        sc = self._scatters(doc)
        assert sc["g1"].data_source is sc["g2"].data_source
        got = self._points(sc["g1"], self._rows(sc["g1"]))
        want = t._expected(obs)
        assert sorted(got) == obs
        assert all(got[o] == pytest.approx(want[o]) for o in want)

    def test_a_move_keeps_its_rows_where_they_were(self):
        from test_mode_parity import _fire, _widgets_of
        t = self._T()
        doc = _served_doc(t._spec({"filter": _MOVES[0][1]}), _DF_MISSING)
        g1 = self._scatters(doc)["g1"]
        before = self._points(g1, self._rows(g1))
        [w] = [w for w in _widgets_of(doc) if isinstance(w, Select)]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        g1 = self._scatters(doc)["g1"]
        after = self._points(g1, self._rows(g1))
        assert set(after) == {2, 6, 8, 10}
        assert all(after[o] == pytest.approx(before[o]) for o in after)


class TestAnUnlinkedJitteredScatterServed:
    """Without link(), a served filter move keeps a jittered scatter's kept
    points where jitter() drew them, as the saved page does: the saved
    filter script keeps rows of the jittered copy by their row id, so a
    point never moves; the served redraw jittered the kept rows afresh."""

    _T = TestALinkedJitteredScatter
    _S = TestALinkedJitteredScatterServed

    def _spec(self, bo):
        t = self._T()
        spec = t._spec(bo)
        spec.get("build_options", spec).pop("link", None)
        return spec

    def test_the_spec_is_unlinked(self):
        spec = self._spec({"filter": _MOVES[0][1]})
        assert "link" not in spec.get("build_options", {})

    def test_a_move_keeps_its_rows_where_they_were(self):
        from test_mode_parity import _fire, _widgets_of
        doc = _served_doc(self._spec({"filter": _MOVES[0][1]}), _DF_MISSING)
        g1 = self._S._scatters(doc)["g1"]
        before = self._S._points(g1, self._S._rows(g1))
        assert sorted(before) == [1, 2, 5, 6, 7, 8, 9, 10]
        [w] = [w for w in _widgets_of(doc) if isinstance(w, Select)]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        g1 = self._S._scatters(doc)["g1"]
        after = self._S._points(g1, self._S._rows(g1))
        assert set(after) == {2, 6, 8, 10}
        assert all(after[o] == pytest.approx(before[o]) for o in after), (
            {o: (before[o], after[o]) for o in after})


# ---------------------------------------------------------------------------
# A date dropdown
# ---------------------------------------------------------------------------

class TestADateDropdown:
    """A dropdown on a %td variable keeps the rows of the date chosen: the
    option carries the snapshot's epoch milliseconds, which the script
    compares.  Its options read "2001-01-02 00:00:00" and every one kept
    no row (BUGS.md, measured [False] * 4)."""

    def _spec(self):
        return _spec([plot_for("scatter")], {"filter": "when, type(dropdown)",
                                             "formats": {"when": "%td"}})

    def test_every_option_keeps_its_own_row(self):
        r = _render(self._spec())
        [w] = r.filter_widgets
        opts = [(v, lab) for v, lab in w.options if v != w._dash_sentinel]
        assert len(opts) == 10
        for i, (value, label) in enumerate(opts):
            r = _render(self._spec())
            [w] = r.filter_widgets
            w.value = value
            cb = r.filter_callbacks[0]
            _run(cb.code, cb.args)
            [fig] = _profile(r)
            xs = fig["glyphs"][0]["coords"]["x"][1]
            # _DF's `when' runs 15340..15349, one day per observation, so
            # the i-th option is observation i + 1's date.
            assert xs == [float(_DF["weight"][i])], (label, xs)

    def test_the_option_labels_still_read_as_dates(self):
        r = _render(self._spec())
        [w] = r.filter_widgets
        labels = [lab for v, lab in w.options if v != w._dash_sentinel]
        # GAPS2 E3/G6, WP-28 S12: Stata's %td text (was ISO datetime).
        assert labels[0] == dr._dash_fmt_text(15340.0, "%td") \
            == "31dec2001", labels[:2]


class TestTheOptionValueOfADate:
    """``_dash_option_value`` of a date is its epoch milliseconds, as a
    float since GAPS2 X1 (a number is a float, text its exact self)."""

    def test_a_timestamp_is_its_milliseconds(self):
        assert dr._dash_option_value(pd.Timestamp("2001-12-31")) == \
            1009756800000.0

    def test_a_datetime64_is_its_milliseconds(self):
        assert dr._dash_option_value(np.datetime64("2001-12-31")) == \
            1009756800000.0

    def test_a_date_past_2262_does_not_overflow(self):
        v = np.datetime64("9999-12-31", "ms")
        assert dr._dash_option_value(v) == float(
            int(v.astype(np.int64)))

    def test_the_served_mask_still_selects_by_date(self):
        col = pd.Series(pd.to_datetime(["2001-12-31", "2002-01-01", None]))
        want = dr._dash_option_value(col[1])
        assert list(dr._dash_dropdown_mask(col, want)) == [False, True,
                                                           False]

    def test_a_number_and_a_string_are_unchanged(self):
        assert dr._dash_option_value(1.0) == 1.0
        assert dr._dash_option_value("2001-12-31") == "2001-12-31"


# ---------------------------------------------------------------------------
# WP-29 P0.15: a linked layer's own if after moves, against the served app
# ---------------------------------------------------------------------------

def _linked_layer_if_spec(layout):
    """g1 holds a plain scatter and a scatter with its own ``if price >
    4500``, under a linked by(foreign) or in a linked graph with its own
    ``if foreign == 1``; g2 is a plain scatter; a range filter on price."""
    layer = plot_for("scatter", if_expr="price > 4500")
    if layout == "by":
        g1 = ("g1", [plot_for("scatter"), layer], {"by": "foreign"})
    else:
        g1 = ("g1", [plot_for("scatter"), layer], None,
              {"if_expr": "foreign == 1"})
    return _spec(None, {"filter": "price, type(range)", "link": "g1 g2"},
                 None, [g1, ("g2", [plot_for("scatter")])], None, "")


class TestALinkedLayersOwnIfAcrossMoves:
    """WP-29 P0.15: a move, a second move and a reset on ONE page each draw
    what the saved renderer draws of the rows kept; the reset draws the
    first paint again."""

    @pytest.mark.parametrize("layout", ["by", "graph-if"])
    def test_every_step_draws_the_kept_rows(self, layout):
        spec = _linked_layer_if_spec(layout)
        r = _render(spec)
        first = _profile(r)
        ws = [w for w in r.filter_widgets
              if type(w).__name__ == "RangeSlider"]
        assert len(ws) == 1
        w = ws[0]
        full = (float(w.start), float(w.end))
        steps = [((4500.0, 11385.0), "price >= 4500 & price <= 11385"),
                 ((5000.0, 11385.0), "price >= 5000 & price <= 11385"),
                 (full, None)]
        for value, rows in steps:
            _move(r, ("RangeSlider", value))
            oracle = first if rows is None else _saved_of_rows(spec, rows)
            _assert_same(f"{layout} after the move to {value}",
                         _profile(r), oracle)


class TestTheSavedPageAgreesWithTheServedApp:
    """WP-29 P0.15: after a move the saved page draws what the served app
    draws, figure by figure."""

    @pytest.mark.parametrize("layout", ["by", "graph-if"])
    def test_a_qualified_layer_in_a_linked_graph(self, layout):
        spec = _linked_layer_if_spec(layout)
        action = ("RangeSlider", (4500.0, 11385.0))
        saved = _saved_after_move(spec, action)
        served = _served_after_move(spec, action)[0]
        assert len(saved) == len(served), "figure counts differ"
        for i, (a, b) in enumerate(zip(saved, served)):
            diffs = _diff(a["glyphs"], b["glyphs"])
            assert not diffs, _explain(layout, f"figure {i} glyphs, saved "
                                               f"against served", diffs)


class TestTheTruthCheckHelpers:
    """WP-29 P0.15: ``filter_truth_check.layer_rows``, which the Stata
    cases QF-01 and QF-02 read, counts each layer's rows in both modes."""

    def test_layer_rows_reads_both_modes(self):
        import filter_truth_check as ftc
        spec = _spec([plot_for("scatter")],
                     {"filter": "foreign, type(dropdown)"})
        spec["build_options"]["filters"] = [
            {"varname": "foreign", "type": "dropdown"}]
        sp, dp = _write(spec, _DF)
        assert ftc.layer_rows(sp, dp, [(0, 1.0)]) == {
            "saved": [[5]], "served": [[5]]}


# ---------------------------------------------------------------------------
# WP-29 P0.16: the colour key is fixed at build and holds through a move
# ---------------------------------------------------------------------------

def _colour_layouts(opts):
    """(id, spec kwargs) of the four layouts a colorvar() scatter is
    drawn in."""
    lay = plot_for("scatter", dict(opts, colorvar=opts.get("colorvar",
                                                           "price")))
    return [
        ("unlinked", dict(plots=[lay])),
        ("linked graph if", dict(graphs=[
            ("g1", [lay], None, {"if_expr": "foreign == 1"}),
            ("g2", [plot_for("scatter")])], bo={"link": "g1 g2"})),
        # Flipped (WP-30 P1.15c): twoway draws no colour key under by()
        # unless by(, clegend(on)), then one, the first panel's
        # (by_chrome_truth.json q06, q07), so the by() layouts ask for it.
        ("linked by()", dict(graphs=[
            ("g1", [lay], {"by": "foreign, clegend(on)"}),
            ("g2", [plot_for("scatter")])], bo={"link": "g1 g2"})),
        ("unlinked by()", dict(plots=[lay],
                               go={"by": "foreign, clegend(on)"})),
    ]


def _colour_spec(plots=None, go=None, graphs=None, bo=None):
    return _spec(plots, dict(bo or {}, filter="price, type(range)"), go,
                 graphs, None, "")


_KEY_CASES = [
    *[pytest.param(_colour_spec(plots=[plot_for(t, {"colorvar": "price",
                                                     "colorlevels": "3"})]),
                   id=f"{t} colorlevels(3), unlinked")
      for t in ("scatter", "connected", "rconnected", "dot")],
    *[pytest.param(_colour_spec(**kw), id=f"scatter {name}, {lay}")
      for name, opts in (("colorlevels(3)", {"colorlevels": "3"}),
                         ("colordiscrete on rep",
                          {"colorvar": "rep",
                           "colordiscrete": "colordiscrete"}),
                         ("colorcuts(4500 9000)",
                          {"colorcuts": "4500 9000"}))
      for lay, kw in _colour_layouts(opts)],
]

_BAR_CASES = [pytest.param(_colour_spec(**kw), id=lay)
              for lay, kw in _colour_layouts({})]

_RANGE_MOVE = ("RangeSlider", (4500.0, 11385.0))


def _after_move_root(spec, mode):
    """The page's layout root after the range move, in either mode, and
    before it (a fresh render)."""
    import colour_bins as cb  # noqa: F401
    import test_mode_parity as tp
    if mode == "saved":
        before = _render(spec)
        r = _render(spec)
        _move(r, _RANGE_MOVE)
        return before._last_layout_root, r._last_layout_root
    before, _ = tp._served(spec)
    doc, _ = tp._served(spec)
    ws = [w for w in tp._widgets_of(doc)
          if type(w).__name__ == "RangeSlider"]
    tp._fire(ws[0], _RANGE_MOVE[1])
    return before, doc


class TestTheColourKeyHoldsThroughAMove:
    """Every colour a move leaves is a key level, and a continuous key
    spans the rows kept (WP-32 overrides BR-07.4's fixed range: twoway
    draws the key over the rows it draws)."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("spec", _KEY_CASES)
    def test_every_colour_value_is_a_key_level(self, spec, mode):
        import colour_bins as cb
        _before, root = _after_move_root(spec, mode)
        rends = [r for r in cb.colour_renderers(root)
                 if hasattr(cb.colour_mapper(r), "factors")]
        assert rends
        for r in rends:
            factors = set(cb.colour_mapper(r).factors)
            bad = [v for v in cb.drawn_colour_values(r)
                   if v is not None and v not in factors]
            assert not bad, (bad, sorted(factors))

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("spec", _BAR_CASES)
    def test_the_colour_bar_spans_the_kept_rows(self, spec, mode):
        """Flipped (WP-32, BUGS.md "A continuous colour key keeps the
        build's range after a filter move"; it was test_the_colour_bar_
        keeps_its_range, BR-07.4): twoway draws the key over the rows it
        draws (measured 19oct2026: 10-40 over every car, 15-40 over the
        foreign ones), so after a move each continuous mapper spans the
        rows its layer still draws."""
        import colour_bins as cb
        before, after = _after_move_root(spec, mode)
        assert cb.colour_bars(before) and cb.colour_bars(after)
        rends = [r for r in cb.colour_renderers(after)
                 if hasattr(cb.colour_mapper(r), "low")]
        assert rends
        for r in rends:
            # Flipped (WP-32, BUGS.md "After a filter move a colour key
            # leaves out the kept rows whose x or y is missing"): the rows
            # the layer draws through its view, not every row of its
            # source -- a linked by() panel's source holds the other
            # panel's rows too, and twoway keys each panel over its own.
            vals = [float(v) for v in cb.drawn_colour_values(r)
                    if v is not None and math.isfinite(float(v))]
            if not vals:
                continue
            m = cb.colour_mapper(r)
            lo, hi = min(vals), max(vals)
            assert (m.low, m.high) == (lo, hi if hi > lo else lo + 1.0), (
                (m.low, m.high), (lo, hi))
