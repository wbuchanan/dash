"""A linked graph drawn through a view shows its own rows after a filter move,
when served -- the rows the saved page shows.

Measured 23sep2026 at ad13a0f, sysuse auto, a filter moved in the served app
(make_document on a Document, the widget's registered callback) against the
saved page's own filter callback run under node:

* ``link(g1 g2)``, g1 ``by(foreign)``: a price range of 5000-8000 left the
  saved panels 14 and 9 rows and g2 23; served, the panels drew 9 and 0 and
  g2 9.
* ``link(g1 g2)``, g1 ``if price > 6000`` registered last: dropdown Foreign
  gave g1 9 and g2 22 saved, g1 2 and g2 9 served.
* g1 ``in 1/30`` registered last: dropdown Foreign gave g1 0 saved (the
  first thirty cars are domestic) and g1 22, every foreign car, served.
* A plain linked pair and unlinked graphs agreed.

Every member of a link group draws from ONE source.  The served recompute
wrote each linked graph's -- and each by() panel's -- own filtered rows into
that source in turn, so whichever was written last decided what every
linked graph showed, and it never rebuilt the IndexFilter each panel or
qualified graph draws through: its positions still counted rows of the
unfiltered source, so a view drew rows it does not own or pointed past the
source's end (BokehJS ignores such an index and logs it).  A layer drawn
from a copy of the shared source -- a line in its join order, a jittered
scatter -- is redrawn from the filtered rows on every move and kept the
view too.

The saved page (``_FILTER_JS``) writes the shared source once with the rows
every filter keeps and rebuilds each view's BooleanFilter from the rows its
graph or panel owns.  The served recompute now does the same
(``_dash_refresh_linked``).
"""
import itertools
import json
import os
import subprocess
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (BooleanFilter, CDSView, ColumnDataSource,
                          GlyphRenderer, IndexFilter, RangeSlider, Select,
                          Slider)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_adversarial_matrix import (_DF, _SCATTER, _load_app,  # noqa: E402
                                     _write_inputs)
from test_filter_exclude import _encode, _node  # noqa: E402

_SEQ = itertools.count()
_FIGURE = type(figure())
_EM = chr(0x2014)

#: The widget each filter type builds, the value it is moved to, and the
#: rows of _DF's ten that value keeps.
_MOVES = {
    "dropdown": ({"varname": "foreign", "type": "dropdown"}, "1",
                 _DF["foreign"] == 1.0),
    "range": ({"varname": "price", "type": "range"}, (4000.0, 5000.0),
              (_DF["price"] >= 4000.0) & (_DF["price"] <= 5000.0)),
    "slider": ({"varname": "mpg", "type": "slider"}, 22.0,
               _DF["mpg"] >= 22.0),
}
_WIDGET = {"dropdown": Select, "range": RangeSlider, "slider": Slider}


from conftest import render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402


def _rows_of(mask):
    return frozenset(int(i) for i in _DF.index[mask])


#: The rows each graph or panel owns, written in pandas here rather than by
#: dash's own qualifier reader, so the oracle is not the code under test.
_ALL = _rows_of(_DF["mpg"] == _DF["mpg"])
_DOMESTIC = _rows_of(_DF["foreign"] == 0.0)
_FOREIGN = _rows_of(_DF["foreign"] == 1.0)
_PRICEY = _rows_of(_DF["price"] > 4500.0)
_IN_3_8 = frozenset(range(2, 8))


def _panel(group):
    """A panel's key: the graph's title, then the group as twoway writes
    it -- foreign 0 is "0", which dash wrote "0.0" until WP-23.  Flipped
    (WP-30 P1.15a): the key was the title "g1 — 0"; twoway keeps the title
    and draws the label as a row of its own, so the key is title + " " +
    label (_key)."""
    return "g1 %s" % group


def _key(fig):
    """A figure's key: its title, then its panel label when it has one."""
    from by_panel_probe import panel_label
    lab = panel_label(fig)
    return "%s %s" % (fig.title.text, lab) if lab else fig.title.text


# ---------------------------------------------------------------------------
# Specs
# ---------------------------------------------------------------------------

def _graph(name, plots=None, if_expr="", in_expr="", **go):
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": plots or [dict(_SCATTER)], "graph_options": opts,
            "if_expr": if_expr, "in_expr": in_expr}


def _spec(graphs, filters, link="g1 g2"):
    return {"graphs": graphs, "kpis": [],
            "build_options": {
                "layout": "auto", "link": link, "theme": "", "title": "",
                "subtitle": "", "filters": filters,
                "registry": " ".join(g["graph_options"]["name"]
                                     for g in graphs)}}


def _filter(ftype, exclude=()):
    return dict(_MOVES[ftype][0], exclude=list(exclude))


#: name -> (graphs, {figure title: rows it owns}).  In every case the
#: linked graph drawn through a view is the one the recompute reached LAST,
#: which is what decided the shared source before the fix.
_CASES = {
    "a by() graph beside a plain one": (
        lambda: [_graph("g1", by="foreign"), _graph("g2")],
        {_panel("0"): _DOMESTIC, _panel("1"): _FOREIGN, "g2": _ALL}),
    "a graph with its own if, registered last": (
        lambda: [_graph("g2"), _graph("g1", if_expr="price > 4500")],
        {"g1": _PRICEY, "g2": _ALL}),
    "a graph with its own in, registered last": (
        lambda: [_graph("g2"), _graph("g1", in_expr="3/8")],
        {"g1": _IN_3_8, "g2": _ALL}),
    "a by() graph with a total panel": (
        lambda: [_graph("g1", by="foreign, total"), _graph("g2")],
        {_panel("0"): _DOMESTIC, _panel("1"): _FOREIGN,
         _panel("Total"): _ALL, "g2": _ALL}),
    "a qualified by() graph": (
        lambda: [_graph("g1", if_expr="price > 4500", by="foreign"),
                 _graph("g2")],
        {_panel("0"): _PRICEY & _DOMESTIC,
         _panel("1"): _PRICEY & _FOREIGN, "g2": _ALL}),
}


def _truth(owned, mask):
    """Rows per figure: the rows it owns that the filters keep."""
    keep = _rows_of(mask)
    return {title: [sorted(rows & keep)] for title, rows in owned.items()}


# ---------------------------------------------------------------------------
# The served app: set the widget, call its registered callbacks
# ---------------------------------------------------------------------------

def _served_doc(tmp_path, spec):
    sp, dp = _write_inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "linked_views_%d" % next(_SEQ))
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _fire(doc, var, value):
    """Move the widget filtering *var* to *value* and run the one callback
    registered for it: a Select on "value", a slider on "value_throttled"."""
    [w] = [m for cls in (Select, RangeSlider, Slider)
           for m in doc.select({"type": cls})
           if getattr(m, "_dash_var", None) == var]
    old = w.value
    w.value = value
    fired = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for attr in ("value", "value_throttled"):
            for cb in w._callbacks.get(attr, []):
                cb(attr, old, value)
                fired += 1
    assert fired == 1, "expected one recompute callback, fired %d" % fired


def _drawn_served(r):
    """Row labels a served renderer draws: its source's ``index`` column
    through its view, an index past the source's end ignored as BokehJS
    ignores it."""
    src = r.data_source
    n = len(next(iter(src.data.values()))) if src.data else 0
    labels = list(src.data.get("index", range(n)))
    flt = r.view.filter
    if isinstance(flt, IndexFilter) and flt.indices is not None:
        return sorted(int(labels[i]) for i in flt.indices if 0 <= i < n)
    if isinstance(flt, BooleanFilter) and flt.booleans is not None:
        return sorted(int(labels[i])
                      for i, b in enumerate(list(flt.booleans)[:n]) if b)
    return sorted(int(x) for x in labels)


def _served_figures(doc):
    return {_key(f): f for f in doc.select({"type": _FIGURE})}


def _served_rows(doc):
    return {title: [_drawn_served(r) for r in drawn_renderers(f)
                    if isinstance(r, GlyphRenderer)]
            for title, f in _served_figures(doc).items()}


def _served(tmp_path, spec, moves):
    doc = _served_doc(tmp_path, spec)
    for var, value in moves:
        _fire(doc, var, value)
    return _served_rows(doc)


# ---------------------------------------------------------------------------
# The saved page: its filter callback, run under node
# ---------------------------------------------------------------------------

# BokehJS runs a CustomJS body as a strict-mode function whose parameters
# are the args' names, then cb_obj and cb_data.  Reports every source's rows
# and every BooleanFilter's booleans as the callback left them.
_RUNNER = r"""
"use strict";
const REG = {};
for (const [id, lit] of Object.entries(RAW.models))
    REG[id] = Object.assign({}, lit);
const resolve = (x) => {
  if (Array.isArray(x)) return x.map(resolve);
  if (x && typeof x === "object") {
    if ("__ref__" in x) return REG[x.__ref__];
    const o = {};
    for (const [k, v] of Object.entries(x)) o[k] = resolve(v);
    return o;
  }
  return x;
};
for (const o of Object.values(REG)) {
  if (o.__type__ === "ColumnDataSource") {
    o.selected = {indices: []};
    o.change = {emit() {}};
  } else if (o.__type__ === "BooleanFilter") {
    o.change = {emit() {}};
  }
}
const args = resolve(RAW.args);
const names = Object.keys(args);
new Function(...names, "cb_obj", "cb_data", '"use strict";\n' + RAW.code)(
  ...names.map((n) => args[n]), null, {});
const out = {};
for (const [id, o] of Object.entries(REG)) {
  if (o.__type__ === "ColumnDataSource") {
    out[id] = {ids: o.data[RAW.row_id] || []};
  } else if (o.__type__ === "BooleanFilter") {
    out[id] = {booleans: o.booleans};
  }
}
process.stdout.write(JSON.stringify(out));
"""


def _run_callback(args, code):
    models = {}
    payload = {"models": models, "args": _encode(dict(args), models),
               "code": code, "row_id": dr._ROW_ID_COLUMN}
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("const RAW = " + json.dumps(payload) + ";\n" + _RUNNER)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True, text=True,
                             timeout=120)
        assert res.returncode == 0, res.stderr[:2000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


def _saved(tmp_path, spec, moves):
    """Rows per renderer per figure title on the saved page after *moves*,
    each moved widget's own callback run in turn."""
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    order = [fc["varname"] for fc in spec["build_options"]["filters"]]
    state = {}
    for var, value in moves:
        wi = order.index(var)
        r.filter_widgets[wi].value = value
        cb = r.filter_callbacks[wi]
        assert cb.code == dr._FILTER_JS
        # The callback rebuilds every source it writes from its snapshot
        # and every view from its member rows, so a later run's writes
        # replace an earlier one's; a model it does not write keeps them.
        state.update(_run_callback(cb.args, cb.code))
    out = {}
    for fig in r.figures.values():
        per = []
        for gr in [x for x in drawn_renderers(fig) if isinstance(x, GlyphRenderer)]:
            src = gr.data_source
            ids = (state[src.id]["ids"] if src.id in state
                   else list(src.data[dr._ROW_ID_COLUMN]))
            flt = gr.view.filter
            if isinstance(flt, BooleanFilter) and flt.booleans is not None:
                bools = (state[flt.id]["booleans"] if flt.id in state
                         else list(flt.booleans))
                per.append(sorted(ids[i] for i, b in
                                  enumerate(bools[:len(ids)]) if b))
            else:
                per.append(sorted(ids))
        out[_key(fig)] = per
    return out


# ---------------------------------------------------------------------------
# 1. Each view shows the rows its graph or panel owns, when served
# ---------------------------------------------------------------------------

class TestEachServedViewShowsItsOwnRows:

    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    @pytest.mark.parametrize("case", sorted(_CASES))
    def test_after_one_move(self, tmp_path, case, ftype):
        graphs, owned = _CASES[case]
        _, value, mask = _MOVES[ftype]
        spec = _spec(graphs(), [_filter(ftype)])
        got = _served(tmp_path, spec, [(_MOVES[ftype][0]["varname"], value)])
        assert got == _truth(owned, mask), "%s, %s: %s" % (case, ftype, got)

    def test_a_per_layer_qualifier_keeps_its_panel(self, tmp_path):
        """The second layer of a by() graph draws its panel's rows that its
        own if() keeps -- never another panel's."""
        spec = _spec([_graph("g1", by="foreign",
                             plots=[dict(_SCATTER),
                                    dict(_SCATTER, if_expr="price > 4500")]),
                      _graph("g2")], [_filter("range")])
        got = _served(tmp_path, spec, [("price", (4000.0, 6000.0))])
        keep = _rows_of((_DF["price"] >= 4000.0) & (_DF["price"] <= 6000.0))
        assert got == {
            _panel("0"): [sorted(_DOMESTIC & keep),
                            sorted(_DOMESTIC & _PRICEY & keep)],
            _panel("1"): [sorted(_FOREIGN & keep),
                            sorted(_FOREIGN & _PRICEY & keep)],
            "g2": [sorted(keep)]}


# ---------------------------------------------------------------------------
# 2. The two modes show the same rows after the same move
# ---------------------------------------------------------------------------

_PARITY = dict(_CASES)
# An excluded member of a link group shares the group's source, and is
# filtered with it on the saved page (test_filter_exclude.py): the served
# app must at least agree.
_PARITY["one member excluded, drawn through a view"] = (
    lambda: [_graph("g1", if_expr="price > 4500"), _graph("g2")], None)


class TestBothModesShowTheSameRows:

    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    @pytest.mark.parametrize("case", sorted(_PARITY))
    def test_after_one_move(self, tmp_path, case, ftype):
        graphs, _ = _PARITY[case]
        excl = ["g1"] if "excluded" in case else []
        spec = _spec(graphs(), [_filter(ftype, excl)])
        move = [(_MOVES[ftype][0]["varname"], _MOVES[ftype][1])]
        saved = _saved(tmp_path, spec, move)
        served = _served(tmp_path, spec, move)
        assert served == saved, "%s, %s:\n  saved  %s\n  served %s" % (
            case, ftype, saved, served)


# ---------------------------------------------------------------------------
# 3. Every move starts from the rows each view owns, not the last move's
# ---------------------------------------------------------------------------

_SEQUENCES = {
    "a dropdown moved and moved back to All": (
        lambda: [_graph("g2"), _graph("g1", if_expr="price > 4500")],
        [_filter("dropdown")], [("foreign", "1"), ("foreign", "__all__")],
        {"g1": [sorted(_PRICEY)], "g2": [sorted(_ALL)]}),
    "a range, then a slider beside it": (
        lambda: [_graph("g1", by="foreign"), _graph("g2")],
        [_filter("range"), _filter("slider")],
        [("price", (4000.0, 6000.0)), ("mpg", 20.0)],
        {_panel("0"): [[0, 4]], _panel("1"): [[3]], "g2": [[0, 3, 4]]}),
    "a dropdown, a range, and the dropdown back to All": (
        lambda: [_graph("g1", by="foreign"),
                 _graph("g2", if_expr="price > 4500")],
        [_filter("dropdown"), _filter("range")],
        [("foreign", "1"), ("price", (4000.0, 6000.0)),
         ("foreign", "__all__")],
        {_panel("0"): [[0, 4, 6, 8]], _panel("1"): [[1, 3, 5]],
         "g2": [[1, 3, 4, 6]]}),
}


class TestEveryMoveStartsFromTheOwnedRows:

    @pytest.mark.parametrize("case", sorted(_SEQUENCES))
    def test_the_served_rows(self, tmp_path, case):
        graphs, filters, moves, want = _SEQUENCES[case]
        got = _served(tmp_path, _spec(graphs(), filters), moves)
        assert got == want, "%s: %s" % (case, got)

    @pytest.mark.parametrize("case", sorted(_SEQUENCES))
    def test_the_saved_page_agrees(self, tmp_path, case):
        graphs, filters, moves, _ = _SEQUENCES[case]
        spec = _spec(graphs(), filters)
        assert _served(tmp_path, spec, moves) == _saved(tmp_path, spec,
                                                         moves)


# ---------------------------------------------------------------------------
# 4. The shared source: every filtered row, written once
# ---------------------------------------------------------------------------

def _shared_source(doc):
    """The source g2 -- a linked graph with no view -- draws from."""
    [r] = [r for r in drawn_renderers(_served_figures(doc)["g2"])
           if isinstance(r, GlyphRenderer)]
    assert isinstance(r.view.filter, type(CDSView().filter))
    return r.data_source


class TestTheSharedSourceHoldsEveryFilteredRowOnce:

    # Not a by(foreign) graph under a foreign dropdown: the last panel
    # written then holds every row the dropdown keeps, right by accident.
    @pytest.mark.parametrize("case, ftype", [
        ("a by() graph beside a plain one", "range"),
        ("a by() graph beside a plain one", "slider"),
        ("a graph with its own if, registered last", "dropdown"),
        ("a graph with its own if, registered last", "range"),
        ("a graph with its own if, registered last", "slider"),
    ])
    def test_every_row_the_filters_keep(self, tmp_path, case, ftype):
        graphs, _ = _CASES[case]
        doc = _served_doc(tmp_path, _spec(graphs(), [_filter(ftype)]))
        shared = _shared_source(doc)
        _fire(doc, _MOVES[ftype][0]["varname"], _MOVES[ftype][1])
        assert list(shared.data["index"]) == sorted(_rows_of(
            _MOVES[ftype][2]))

    @pytest.mark.parametrize("case", ["a by() graph beside a plain one",
                                      "a by() graph with a total panel"])
    def test_written_once_per_move(self, tmp_path, case):
        """Each write is the whole source sent to the browser: a by() graph
        of two panels and a plain graph wrote it four times per move."""
        graphs, _ = _CASES[case]
        doc = _served_doc(tmp_path, _spec(graphs(), [_filter("range")]))
        writes = []
        _shared_source(doc).on_change(
            "data", lambda attr, old, new: writes.append(len(new["index"])))
        _fire(doc, "price", (4000.0, 5000.0))
        _fire(doc, "price", (4000.0, 6000.0))
        assert writes == [5, 7]


# ---------------------------------------------------------------------------
# 5. No view points past the end of its source
# ---------------------------------------------------------------------------

class TestNoServedViewPointsPastItsSource:
    """BokehJS ignores an IndexFilter index past its source's end and logs
    an out-of-bounds warning for it; the recompute must never leave one."""

    @pytest.mark.parametrize("case", sorted(_CASES))
    def test_after_each_move(self, tmp_path, case):
        graphs, _ = _CASES[case]
        doc = _served_doc(tmp_path, _spec(graphs(), [_filter("range")]))
        checked = 0
        for value in [(4000.0, 5000.0), (3000.0, 12000.0), (4500.0, 4800.0)]:
            _fire(doc, "price", value)
            for title, fig in _served_figures(doc).items():
                for r in drawn_renderers(fig):
                    flt = getattr(getattr(r, "view", None), "filter", None)
                    if not isinstance(flt, IndexFilter) or \
                            flt.indices is None:
                        continue
                    checked += 1
                    n = len(next(iter(r.data_source.data.values())))
                    past = [i for i in flt.indices if not 0 <= i < n]
                    assert not past, "%s after %s: %s past %d rows" % (
                        title, value, past, n)
        # Every case builds at least one IndexFilter view whose indices the
        # recompute rewrites (1 or 2 per case, x3 moves; measured
        # 24sep2026).  Without this the loop's `continue' let a case that
        # built no IndexFilter -- the very view this test guards -- pass
        # having inspected nothing.
        assert checked >= 3, (
            "%s: no served IndexFilter view was examined" % case)


# ---------------------------------------------------------------------------
# 6. A layer redrawn from a copy of the shared source
# ---------------------------------------------------------------------------

def _field(spec):
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return spec.get("field")
    return getattr(spec, "field", None)


def _points(r):
    """(x, y) pairs a renderer draws through its view."""
    src = r.data_source
    g = r.glyph
    xs = list(src.data[_field(g.x)])
    ys = list(src.data[_field(g.y)])
    n = len(xs)
    flt = r.view.filter
    if isinstance(flt, IndexFilter) and flt.indices is not None:
        keep = [i for i in flt.indices if 0 <= i < n]
    else:
        keep = range(n)
    return sorted((float(xs[i]), float(ys[i])) for i in keep)


class TestALayerRedrawnFromACopyOfTheSharedSource:
    """A linked, qualified line is drawn from a copy of the shared source,
    in its join order, and a jittered scatter from a copy carrying the jitter.
    A move redraws the copy from the layer's own filtered rows; the view it
    was built with counted rows of the unfiltered copy."""

    _WANT = sorted(_PRICEY & _FOREIGN)

    def _moved(self, tmp_path, plot):
        spec = _spec([_graph("g1", plots=[plot], if_expr="price > 4500"),
                      _graph("g2")], [_filter("dropdown")])
        doc = _served_doc(tmp_path, spec)
        _fire(doc, "foreign", "1")
        fig = _served_figures(doc)["g1"]
        return [r for r in drawn_renderers(fig) if isinstance(r, GlyphRenderer)]

    def _want_points(self):
        return sorted((float(_DF["weight"][i]), float(_DF["mpg"][i]))
                      for i in self._WANT)

    @pytest.mark.parametrize("ptype", ["line", "connected"])
    def test_a_line_draws_the_layers_rows(self, tmp_path, ptype):
        rends = self._moved(tmp_path, dict(_SCATTER, type=ptype))
        assert rends
        for r in rends:
            assert _points(r) == self._want_points(), type(r.glyph).__name__

    def test_a_jittered_scatter_draws_the_layers_rows(self, tmp_path):
        rends = self._moved(tmp_path, dict(_SCATTER,
                                           options={"jitter": "5"}))
        assert [_drawn_served(r) for r in rends] == [self._WANT]

    def test_an_excluded_connected_graph(self, tmp_path):
        """connected's markers draw from the shared source and its line from
        the copy, through ONE view.  exclude(g1) leaves g1's line as it was
        drawn; its markers share the group's source, which g2's filter
        writes, and are filtered with the group -- as on the saved page
        (test_filter_exclude.py).  Rebuilding the markers' view must not
        move the line."""
        spec = _spec([_graph("g1", plots=[dict(_SCATTER, type="connected")],
                             if_expr="price > 4500"), _graph("g2")],
                     [_filter("dropdown", ["g1"])])
        doc = _served_doc(tmp_path, spec)
        fig = _served_figures(doc)["g1"]
        [line] = [r for r in drawn_renderers(fig)
                  if type(r.glyph).__name__ == "Line"]
        [marks] = [r for r in drawn_renderers(fig)
                   if type(r.glyph).__name__ == "Scatter"]
        before = _points(line)
        _fire(doc, "foreign", "1")
        assert _drawn_served(marks) == self._WANT
        assert _points(line) == before


# ---------------------------------------------------------------------------
# 7. The helpers
# ---------------------------------------------------------------------------

class TestViewPositions:

    def test_the_positions_of_the_owned_rows_the_source_holds(self):
        pos = {10: 0, 12: 1, 13: 2, 17: 3}
        assert dr._dash_view_positions(pos, {12, 17}) == [1, 3]

    def test_an_owned_row_the_filters_dropped_is_not_drawn(self):
        assert dr._dash_view_positions({10: 0, 12: 1}, {11, 12}) == [1]

    def test_in_the_sources_order_whatever_order_the_rows_come_in(self):
        pos = {5: 0, 3: 1, 9: 2}
        assert dr._dash_view_positions(pos, [9, 5, 3]) == [0, 1, 2]

    def test_no_owned_rows_draw_nothing(self):
        assert dr._dash_view_positions({1: 0}, frozenset()) == []
        assert dr._dash_view_positions({}, {1, 2}) == []


def _fig_with(source, view=None):
    fig = figure()
    kw = {"view": view} if view is not None else {}
    fig.scatter(x="x", y="y", source=source, **kw)
    return fig


class TestLinkedViews:

    def _source(self):
        return ColumnDataSource({"x": [1.0, 2.0, 3.0, 4.0],
                                 "y": [1.0, 2.0, 3.0, 4.0],
                                 "index": [20, 21, 22, 23]})

    def test_each_view_over_the_source_with_the_rows_it_owns(self):
        src = self._source()
        flt = IndexFilter(indices=[1, 3])
        views = dr._dash_linked_views(
            [_fig_with(src, CDSView(filter=flt))], src)
        assert views == [(flt, frozenset({21, 23}))]

    def test_views_over_other_sources_and_unfiltered_ones_are_not(self):
        src, other = self._source(), self._source()
        figs = [_fig_with(src), _fig_with(other, CDSView(
            filter=IndexFilter(indices=[0])))]
        assert dr._dash_linked_views(figs, src) == []

    def test_a_filter_two_renderers_share_is_listed_once(self):
        src = self._source()
        view = CDSView(filter=IndexFilter(indices=[0, 2]))
        fig = _fig_with(src, view)
        fig.scatter(x="x", y="y", source=src, view=view)
        views = dr._dash_linked_views([fig], src)
        assert len(views) == 1 and views[0][1] == frozenset({20, 22})


class TestRefreshLinked:

    def _frame(self, rows):
        return pd.DataFrame({"x": [float(r) for r in rows],
                             "y": [float(r) * 2 for r in rows]},
                            index=list(rows))

    def _source(self):
        return ColumnDataSource({"x": [float(r) for r in range(6)],
                                 "y": [float(r) * 2 for r in range(6)],
                                 "index": list(range(6))})

    def test_the_rows_once_and_every_view_on_its_own_rows(self):
        src = self._source()
        a, b = IndexFilter(indices=[0, 2, 4]), IndexFilter(indices=[1, 5])
        views = [(a, frozenset({0, 2, 4})), (b, frozenset({1, 5}))]
        writes = []
        src.on_change("data", lambda attr, old, new: writes.append(1))
        dr._dash_refresh_linked(src, self._frame([1, 2, 4, 5]), views)
        assert writes == [1]
        assert src.data["index"] == [1, 2, 4, 5]
        assert src.data["x"] == [1.0, 2.0, 4.0, 5.0]
        assert list(a.indices) == [1, 2]
        assert list(b.indices) == [0, 3]

    @pytest.mark.parametrize("rows, first", [([1, 4], "views"),
                                             ([0, 1, 2, 3, 4, 5], "data")])
    def test_no_view_ever_points_past_the_source(self, rows, first):
        """Shrinking, the views move first; growing, the data does -- so
        the browser, applying the changes in order, never sees a view
        longer than its source."""
        src = ColumnDataSource({"x": [0.0, 2.0, 4.0], "y": [0.0, 4.0, 8.0],
                                "index": [0, 2, 4]})
        flt = IndexFilter(indices=[0, 1, 2])
        order = []
        src.on_change("data",
                      lambda attr, old, new: order.append("data"))
        flt.on_change("indices",
                      lambda attr, old, new: order.append("views"))
        dr._dash_refresh_linked(src, self._frame(rows),
                                [(flt, frozenset({0, 1, 2, 3, 4, 5}))])
        assert order[0] == first and sorted(order) == ["data", "views"]

    def test_a_column_the_frame_lacks_is_carried_by_row(self):
        src = self._source()
        src.data = dict(src.data, extra=["a", "b", "c", "d", "e", "f"])
        snap = {c: list(v) for c, v in src.data.items()}
        dr._dash_refresh_linked(src, self._frame([3, 5]), [],
                                snapshot=snap,
                                pos_of={i: i for i in range(6)})
        assert src.data["extra"] == ["d", "f"]


class TestOwnRedrawnViews:

    def test_a_renderer_on_a_redrawn_source_gets_its_own_filter(self):
        shared = ColumnDataSource({"x": [1.0, 2.0, 3.0],
                                   "y": [1.0, 2.0, 3.0]})
        copy = ColumnDataSource(dict(shared.data))
        view = CDSView(filter=IndexFilter(indices=[0, 2]))
        fig = _fig_with(shared, view)
        line = fig.line(x="x", y="y", source=copy, view=view)
        got = dr._dash_own_redrawn_views([fig], {id(copy)})
        [flt] = got[id(copy)]
        assert flt is line.view.filter
        assert flt is not view.filter
        assert list(flt.indices) == [0, 2]
        # The renderer on the shared source keeps the original.
        assert fig.renderers[0].view is view

    def test_a_redrawn_source_drawn_without_a_view_needs_nothing(self):
        copy = ColumnDataSource({"x": [1.0], "y": [1.0]})
        fig = figure()
        fig.line(x="x", y="y", source=copy)
        assert dr._dash_own_redrawn_views([fig], {id(copy)}) == {}
