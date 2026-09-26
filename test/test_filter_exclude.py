"""filter(varname, exclude(name)) leaves the named graph alone, in both modes,
whatever order the graphs were registered in.

Measured 23sep2026 at f92ef65, sysuse auto, graphs g1 and g2, one filter
with exclude(g1), the saved page's own filter callback run under node:

* g1 registered FIRST: selecting Foreign in a foreign dropdown cut g1 from
  74 rows to 22, a price range of 5000-8000 cut it to 23, an mpg slider at
  25 to 19 -- the rows of g2, which the filter does filter.
* g1 registered SECOND: g1 stayed at 74 in all three.
* The served app left g1 at 74 in every order.

The saved page's callback (``_FILTER_JS``) writes every source in
``all_graph_sources`` -- render() leaves an excluded graph's sources out of
it -- and then fell back to its primary ``source``, which render() binds to
the FIRST registered graph's source (the link group's when there is one):
``if (!_srcs.includes(source)) source.data = new_data``.  A primary source
is missing from that list only when every graph drawing from it is
excluded, so the fallback wrote exactly the source exclude() protects, and
wrote the whole dataset's filtered rows into it: an excluded graph with
``if price > 6000`` went from its 23 rows to all 22 foreign cars.  The same
fallback exposed a plain graph registered after a by() graph (the by()
graph's own source is replaced by its panels', so the next graph's source is
the primary) and an excluded link group (the primary is the group's shared
source).

An excluded member of a link() group whose other members are filtered is
filtered with them, in both modes, before and after the fix: the group
draws from one shared source.  ``TestBothModesAgree`` holds the two modes to
the same answer there; it does not pin which answer.
"""
import itertools
import json
import math
import os
import sys
import warnings

import numpy as np
import pytest
from bokeh.document import Document
from bokeh.model import Model
from bokeh.models import (BooleanFilter, ColumnDataSource, Div, GlyphRenderer,
                          RangeSlider, Select, Slider)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from test_adversarial_matrix import (_DF, _SCATTER, _load_app,  # noqa: E402
                                     _write_inputs)

_SEQ = itertools.count()
_FIGURE = type(figure())

#: The value each filter type is moved to, and the rows of _DF's ten it keeps
#: (five each): foreign == 1; 4000 <= price <= 5000; mpg >= 22.
_MOVES = {
    "dropdown": ({"varname": "foreign", "type": "dropdown"}, 1.0),
    "range": ({"varname": "price", "type": "range"}, (4000.0, 5000.0)),
    "slider": ({"varname": "mpg", "type": "slider"}, 22.0),
}
_KEPT = 5
_ALL = len(_DF)


# ---------------------------------------------------------------------------
# Specs
# ---------------------------------------------------------------------------

def _graph(name, if_expr="", **go):
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": [dict(_SCATTER)], "graph_options": opts,
            "if_expr": if_expr, "in_expr": ""}


def _spec(graphs, ftype, exclude, link=""):
    filt = dict(_MOVES[ftype][0], exclude=list(exclude))
    return {"graphs": graphs, "kpis": [],
            "build_options": {
                "layout": "auto", "link": link, "theme": "", "title": "",
                "subtitle": "", "filters": [filt],
                "registry": " ".join(g["graph_options"]["name"]
                                     for g in graphs)}}


def _ordered(order):
    """g1 and g2 with the excluded graph, g1, first or second."""
    g1, g2 = _graph("g1"), _graph("g2")
    return [g1, g2] if order == "excluded_first" else [g2, g1]


# ---------------------------------------------------------------------------
# The saved page: its filter callback, run under node
# ---------------------------------------------------------------------------

#: A thin alias (test/js_runner.py, WP-28 S03): ``test_filter_widget_data.py``
#: imports ``_node`` directly by this name.
_node = js_runner.node


#: ``_plain``, ``_encode`` and ``_stand_in`` stay defined here, unchanged,
#: for two files this section does not edit: ``test_filter_widget_data.py``
#: imports ``_encode`` and ``_node`` directly by these names and this
#: two-argument ``_encode(v, models)`` signature (js_runner's ``encode``
#: takes three), and ``test_date_range.py`` monkeypatches THIS module's
#: ``_plain`` at runtime -- it relies on ``_encode``'s unqualified call to
#: ``_plain`` resolving in this module's own namespace, which only holds if
#: ``_plain``/``_encode`` are real functions here, not aliases of
#: js_runner's.  ``_run_callback`` below no longer uses any of the three:
#: it goes through the shared js_runner module, as every other runner in
#: this package now does.

def _plain(v):
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return None if math.isnan(v) else v
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _encode(v, models):
    """*v* as JSON, each Bokeh model replaced by a reference to ONE stand-in,
    so identity -- ``_srcs.includes(source)`` -- is what the page has."""
    if isinstance(v, Model):
        if v.id not in models:
            models[v.id] = None
            models[v.id] = _stand_in(v, models)
        return {"__ref__": v.id}
    if isinstance(v, dict):
        return {str(k): _encode(x, models) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_encode(x, models) for x in list(v)]
    return _plain(v)


def _stand_in(m, models):
    if isinstance(m, ColumnDataSource):
        return {"__type__": "ColumnDataSource",
                "data": {str(c): _encode(list(v), models)
                         for c, v in m.data.items()}}
    if isinstance(m, BooleanFilter):
        return {"__type__": "BooleanFilter",
                "booleans": [bool(b) for b in (m.booleans or [])]}
    if isinstance(m, Div):
        return {"__type__": "Div", "text": m.text}
    props = m.properties()
    return {"__type__": type(m).__name__,
            **{p: _encode(getattr(m, p), models)
               for p in ("value", "start", "end", "step") if p in props}}


def _run_callback(args, code):
    """Run *code* with *args* under node; ``{model id: {"rows", "ids"}}``
    for every ColumnDataSource the args reach, as the code left it.  A dry
    run (test/js_runner.py, WP-28 S03): nothing is written back into the
    Python models, as ``TestThePrimarySourceFallback`` requires."""
    out = js_runner.JsSession([]).run_code(code, args, commit=False)
    result = {}
    for mid, state in out.items():
        if "data" not in state:
            continue
        cols = list(state["data"].keys())
        rows = len(state["data"][cols[0]]) if cols else 0
        result[mid] = {"rows": rows,
                       "ids": state["data"].get(dr._ROW_ID_COLUMN)}
    return result


def _renderer_source(fig):
    [r] = [r for r in fig.renderers if isinstance(r, GlyphRenderer)]
    assert not isinstance(getattr(r.view, "filter", None), BooleanFilter), (
        "these cases draw no view; count the view's rows before using one")
    return r.data_source


def _rows(src):
    return len(next(iter(src.data.values()))) if src.data else 0


def _saved(tmp_path, spec, value):
    """``(before, after, renderer, callback output)``: rows per figure title
    before the move and after the page's own callback ran."""
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        r.render()
    [w] = r.filter_widgets
    [cb] = r.filter_callbacks
    assert cb.code == dr._FILTER_JS
    w.value = value
    out = _run_callback(cb.args, cb.code)
    before, after = {}, {}
    for fig in r.figures.values():
        src = _renderer_source(fig)
        before[fig.title.text] = _rows(src)
        after[fig.title.text] = (out[src.id]["rows"] if src.id in out
                                 else _rows(src))
    return dict(sorted(before.items())), dict(sorted(after.items())), r, out


# ---------------------------------------------------------------------------
# The served app: set the widget, call its registered callbacks
# ---------------------------------------------------------------------------

def _served_rows(doc):
    return dict(sorted((f.title.text, _rows(_renderer_source(f)))
                       for f in doc.select({"type": _FIGURE})))


def _served(tmp_path, spec, ftype, value):
    """``(before, after)``: rows per figure title in one served session,
    before and after the widget moves."""
    sp, dp = _write_inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "exclude_%d" % next(_SEQ))
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    before = _served_rows(doc)
    cls = {"dropdown": Select, "range": RangeSlider, "slider": Slider}[ftype]
    [w] = list(doc.select({"type": cls}))
    old = w.value
    w.value = value
    fired = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # A Select recomputes on "value", a slider on "value_throttled".
        for attr in ("value", "value_throttled"):
            for cb in w._callbacks.get(attr, []):
                cb(attr, old, value)
                fired += 1
    assert fired == 1, "expected one recompute callback, fired %d" % fired
    return before, _served_rows(doc)


# ---------------------------------------------------------------------------
# 1. The saved page
# ---------------------------------------------------------------------------

class TestTheSavedPageLeavesAnExcludedGraphAlone:

    @pytest.mark.parametrize("order", ["excluded_first", "excluded_second"])
    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    def test_whatever_order_the_graphs_came_in(self, tmp_path, ftype, order):
        spec = _spec(_ordered(order), ftype, ["g1"])
        before, after, _, _ = _saved(tmp_path, spec, _MOVES[ftype][1])
        assert before == {"g1": _ALL, "g2": _ALL}
        assert after == {"g1": _ALL, "g2": _KEPT}, (
            "exclude(g1) with g1 registered %s: %s"
            % (order.split("_")[1], after))

    def test_a_qualified_excluded_graph_keeps_its_own_rows(self, tmp_path):
        """The fallback wrote the whole dataset's filtered rows: g1's
        `if price > 4500' rows became every foreign car, row 5 (price 4453)
        among them."""
        spec = _spec([_graph("g1", if_expr="price > 4500"), _graph("g2")],
                     "dropdown", ["g1"])
        _, _, r, out = _saved(tmp_path, spec, 1.0)
        src = r.sources["g1"]
        want = list(src.data[dr._ROW_ID_COLUMN])
        assert want == [1, 3, 4, 6, 7, 9]
        got = out[src.id]["ids"] if src.id in out else want
        assert got == want
        assert out[r.sources["g2"].id]["rows"] == _KEPT

    def test_a_graph_after_a_by_graph_is_left_alone(self, tmp_path):
        """A by() graph's own source gives way to its panels', which made
        the NEXT graph's source the callback's primary."""
        spec = _spec([_graph("g1", by="foreign"), _graph("g2")], "range",
                     ["g2"])
        before, after, _, _ = _saved(tmp_path, spec, _MOVES["range"][1])
        # A panel is titled "<title> <em dash> <group>", in both modes, the
        # group written as twoway writes it: 0 and 1 (dash wrote 0.0 and
        # 1.0 until WP-23).
        p0, p1 = ("g1 %s %s" % (chr(0x2014), grp) for grp in ("0", "1"))
        assert before == {p0: 5, p1: 5, "g2": _ALL}
        assert after == {p0: 2, p1: 3, "g2": _ALL}

    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    def test_an_excluded_link_group_is_left_alone(self, tmp_path, ftype):
        """The primary is the group's shared source."""
        spec = _spec([_graph("g1"), _graph("g2"), _graph("g3")], ftype,
                     ["g1", "g2"], link="g1 g2")
        _, after, _, _ = _saved(tmp_path, spec, _MOVES[ftype][1])
        assert after == {"g1": _ALL, "g2": _ALL, "g3": _KEPT}


# ---------------------------------------------------------------------------
# 2. The served app (it was right; this holds it there)
# ---------------------------------------------------------------------------

class TestTheServedAppLeavesAnExcludedGraphAlone:

    @pytest.mark.parametrize("order", ["excluded_first", "excluded_second"])
    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    def test_whatever_order_the_graphs_came_in(self, tmp_path, ftype, order):
        spec = _spec(_ordered(order), ftype, ["g1"])
        before, after = _served(tmp_path, spec, ftype, _MOVES[ftype][1])
        assert before == {"g1": _ALL, "g2": _ALL}
        assert after == {"g1": _ALL, "g2": _KEPT}

    @pytest.mark.parametrize("ftype", ["dropdown", "range", "slider"])
    def test_an_excluded_link_group_is_left_alone(self, tmp_path, ftype):
        spec = _spec([_graph("g1"), _graph("g2"), _graph("g3")], ftype,
                     ["g1", "g2"], link="g1 g2")
        _, after = _served(tmp_path, spec, ftype, _MOVES[ftype][1])
        assert after == {"g1": _ALL, "g2": _ALL, "g3": _KEPT}


# ---------------------------------------------------------------------------
# 3. The two modes show the same rows after the same move
# ---------------------------------------------------------------------------

_PARITY = {
    "unlinked, excluded first, dropdown":
        (lambda: _ordered("excluded_first"), "dropdown", ["g1"], ""),
    "unlinked, excluded first, range":
        (lambda: _ordered("excluded_first"), "range", ["g1"], ""),
    "unlinked, excluded first, slider":
        (lambda: _ordered("excluded_first"), "slider", ["g1"], ""),
    "unlinked, excluded second, dropdown":
        (lambda: _ordered("excluded_second"), "dropdown", ["g1"], ""),
    "qualified and excluded, first":
        (lambda: [_graph("g1", if_expr="price > 4500"), _graph("g2")],
         "dropdown", ["g1"], ""),
    "a graph after a by() graph, excluded":
        (lambda: [_graph("g1", by="foreign"), _graph("g2")], "range",
         ["g2"], ""),
    "a link group excluded, beside an unlinked graph":
        (lambda: [_graph("g1"), _graph("g2"), _graph("g3")], "slider",
         ["g1", "g2"], "g1 g2"),
    # Not pinned either way: an excluded member of a link group shares the
    # group's source, and the modes must at least agree about it.
    "one member of a link group excluded, first":
        (lambda: [_graph("g1"), _graph("g2")], "dropdown", ["g1"], "g1 g2"),
    "one member of a link group excluded, second":
        (lambda: [_graph("g2"), _graph("g1")], "range", ["g1"], "g1 g2"),
}


class TestBothModesAgree:

    @pytest.mark.parametrize("case", sorted(_PARITY))
    def test_the_rows_after_a_move(self, tmp_path, case):
        graphs, ftype, excl, link = _PARITY[case]
        spec = _spec(graphs(), ftype, excl, link)
        value = _MOVES[ftype][1]
        s_before, s_after, _, _ = _saved(tmp_path, spec, value)
        v_before, v_after = _served(tmp_path, spec, ftype, value)
        assert s_before == v_before
        assert s_after == v_after, "saved %s, served %s" % (s_after, v_after)


# ---------------------------------------------------------------------------
# 4. What each callback may write, and the fallback's one remaining use
# ---------------------------------------------------------------------------

class TestTheCallbackKnowsWhatItProtects:

    @pytest.mark.parametrize("graphs, excl, link", [
        (lambda: _ordered("excluded_first"), ["g1"], ""),
        (lambda: _ordered("excluded_second"), ["g1"], ""),
        (lambda: [_graph("g1", by="foreign"), _graph("g2")], ["g1"], ""),
        (lambda: [_graph("g1"), _graph("g2"), _graph("g3")], ["g1", "g2"],
         "g1 g2"),
        (lambda: [_graph("g1"), _graph("g2")], ["g1"], "g1 g2"),
        (lambda: [_graph("g1"), _graph("g2")], [], ""),
    ], ids=["first", "second", "by", "link-group", "link-member", "none"])
    def test_every_graph_source_is_filtered_or_protected_not_both(
            self, tmp_path, graphs, excl, link):
        spec = _spec(graphs(), "dropdown", excl, link)
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        [cb] = r.filter_callbacks
        filtered = {s.id for s in cb.args["all_graph_sources"]}
        protected = {s.id for s in cb.args["excluded_sources"]}
        every = {s.id for s in r.sources.values()}
        assert not (filtered & protected)
        assert filtered | protected == every
        assert cb.args["source"].id in every

    @pytest.mark.parametrize("builder", ["build_dropdown", "build_slider",
                                         "build_range"])
    def test_an_unwired_callback_declares_the_argument(self, builder):
        """Each builder's callback carries the argument the page's script
        reads, as it carries every other one render() fills in."""
        src = ColumnDataSource({"foreign": [0.0, 1.0], "mpg": [20.0, 30.0]})
        var = "foreign" if builder == "build_dropdown" else "mpg"
        _, cb = getattr(dr.FilterBuilder, builder)(var, src)
        assert cb.args["excluded_sources"] == []
        assert cb.code == dr._FILTER_JS


def _script_args(source, graph_sources, excluded):
    """Args for the page's script over a four-row frame, a foreign dropdown
    set to 1 (rows 1 and 3)."""
    frame = {"foreign": [0.0, 1.0, 0.0, 1.0], "mpg": [20.0, 30.0, 22.0, 28.0],
             dr._ROW_ID_COLUMN: [0, 1, 2, 3]}
    w = Select(value=1.0, options=[("__all__", "All"), (0.0, "0"), (1.0, "1")])
    return {
        "source": source,
        "orig_source": ColumnDataSource(dict(frame)),
        "all_widgets": [w],
        "filter_specs_json": json.dumps([{"varname": "foreign",
                                          "type": "dropdown",
                                          "sentinel": "__all__",
                                          "numeric": True,
                                          "groups": [[0.0], [1.0]]}]),
        "kpi_config_json": "[]", "kpi_divs": [], "agg_sources": [],
        "agg_configs_json": "[]", "view_filters": [],
        "all_graph_sources": list(graph_sources),
        "all_graph_sources_orig": [ColumnDataSource(dict(s.data))
                                   for s in graph_sources],
        "excluded_sources": list(excluded),
    }


class TestThePrimarySourceFallback:
    """The fallback writes the callback's `source' when render() did not list
    it: kept for a source no graph owns, which no exclude() can name."""

    @staticmethod
    def _frame_source():
        return ColumnDataSource({"foreign": [0.0, 1.0, 0.0, 1.0],
                                 "mpg": [20.0, 30.0, 22.0, 28.0],
                                 dr._ROW_ID_COLUMN: [0, 1, 2, 3]})

    def test_a_source_no_graph_owns_is_still_written(self):
        primary, graph = self._frame_source(), self._frame_source()
        out = _run_callback(_script_args(primary, [graph], []), dr._FILTER_JS)
        assert out[primary.id] == {"rows": 2, "ids": [1, 3]}
        assert out[graph.id] == {"rows": 2, "ids": [1, 3]}

    def test_a_protected_source_is_never_written(self):
        primary, graph = self._frame_source(), self._frame_source()
        out = _run_callback(_script_args(primary, [graph], [primary]),
                            dr._FILTER_JS)
        assert out[primary.id] == {"rows": 4, "ids": [0, 1, 2, 3]}
        assert out[graph.id] == {"rows": 2, "ids": [1, 3]}

    def test_nor_when_every_graph_is_excluded(self):
        primary = self._frame_source()
        out = _run_callback(_script_args(primary, [], [primary]),
                            dr._FILTER_JS)
        assert out[primary.id] == {"rows": 4, "ids": [0, 1, 2, 3]}
