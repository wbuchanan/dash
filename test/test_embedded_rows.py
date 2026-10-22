"""A page holds only the rows a consumer of it reads (WP-29 P0.11).

GAPS2 I2 / DROPIN-REMAINING P0.11: a saved page embedded every observation
of each drawn variable, the rows ``if`` and ``in`` exclude included, and a
served ``link()`` group sent every row of its shared source.  twoway keeps
only the rows each layer's qualifier selects: ``twoway (scatter mpg weight
if foreign) (scatter mpg weight if price>10000)`` holds sersets of 22 and 10
observations, 30 in all, where dash's saved page held all 74
(test/fixtures/embedded_rows_truth.json, scripts/extract_embedded_rows_truth.do).

The rule (BR-14.1): a page holds a cell of variable *v* on observation *i*
only when a non-literal layer that reads *v* selects *i* through its
graph's and its own qualifiers (by(, total)'s Total rows included), a card
the page recomputes reads *v* on *i*, a filter on *v* reaches *i* through
the graphs, link group and cards it applies to, or ``csv`` is given.  One
function, ``_dash_embed_plan``, decides it in both modes.  Both modes
number the page's rows 0..m-1 (the saved ``__dash_row__``, the served
``index``), so no row number shows where an excluded observation was.

The sentinel battery writes ten rows whose values are unique to their row
(mpg 9001.51.., weight 7001.25.., price 5001.75.., a ``%td`` date and a
string), so a value of an excluded row found anywhere in the page or the
served document names the leak.
"""
import base64
import gzip
import json
import os
import re
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (BooleanFilter, CategoricalColorMapper,
                          ColumnDataSource, GlyphRenderer, IndexFilter,
                          LegendItem, Select)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_served_filter_move as sfm  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_adversarial_matrix import _load_app  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "embedded_rows_truth.json")
_STAT_FIXTURE = os.path.join(_HERE, "fixtures", "qualified_stat_truth.json")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")

_DROPDOWN = "foreign, type(dropdown)"
_RANGE = "price, type(range)"

#: The rows (0-based) each sentinel qualifier column selects.
Q1 = {1, 3, 5, 7, 9}
Q2 = {0, 1, 2}
Q3 = {3, 4, 5}

#: How many node runs this module made (asserted by the last test).
_NODE_RUNS = []


from conftest import render_models  # noqa: E402


def _truth():
    """Stata's answers; the fixture must exist (never skip)."""
    assert os.path.isfile(_FIXTURE), (
        "test/fixtures/embedded_rows_truth.json is missing: run "
        "scripts/extract_embedded_rows_truth.do")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# The sentinel data and the two renderers
# ===========================================================================

def _sentinel_frame():
    """Ten rows (i = 1..10) whose numbers and strings are unique to a row."""
    i = np.arange(1, 11)
    return pd.DataFrame({
        # Not evenly spaced: a histogram's bin edge over some rows must not
        # land on another row's value by arithmetic alone.
        "mpg": 9000.0 + i + 0.5 + 0.01 * i * i,
        "weight": 7000.0 + i + 0.25,
        "price": 5000.0 + i + 0.75,
        "foreign": (i % 2 == 0).astype(float),
        "rep": [3.0, 4.0, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0],
        "when": 15340.0 + i,
        "name": ["sent-%02d" % k for k in i],
        "lab": 60.0 + i,
        "__dashq1": (i % 2 == 0).astype(float),
        "__dashq2": (i <= 3).astype(float),
        "__dashq3": ((i >= 4) & (i <= 6)).astype(float),
    })


_LAB_LABELS = {"labset": {str(60 + k): "lab-%02d" % k for k in range(1, 11)},
               "origin": {"0": "Domestic", "1": "Foreign"}}
_LAB_NAMES = {"lab": "labset", "foreign": "origin"}


def _write_inputs(spec, df=None, strings=("name",)):
    """``(spec path, data path)`` for *spec* over *df* (the sentinels by
    default).  Reserved ``__dash`` columns the spec does not name are
    dropped first: the loader refuses data holding one."""
    df = _sentinel_frame() if df is None else df.copy()
    named = set(dr._dash_qual_cols_named(spec))
    named |= set((spec.get("build_options", {}).get("sort_cols") or {})
                 .values())
    df = df[[c for c in df.columns
             if not str(c).startswith("__dash") or c in named]]
    labels = {k: v for k, v in _LAB_LABELS.items()}
    names = {k: v for k, v in _LAB_NAMES.items() if k in df.columns}
    data = make_data_json(df, labels, names)
    for s in strings:
        if s in df.columns:
            for key in ("variableIsString", "variableTypeIsString"):
                data["StataJSON"][key][s] = True
    tmp = tempfile.mkdtemp(prefix="dash_er_")
    sp = os.path.join(tmp, "spec.json")
    dp = os.path.join(tmp, "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _saved(spec, df=None, strings=("name",)):
    """``(renderer, page, warnings)`` of the saved renderer."""
    sp, dp = _write_inputs(spec, df, strings)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return r, page, sorted(str(w.message) for w in caught)


def _served(spec, df=None, strings=("name",)):
    """``(document, warnings)`` of the served app, loaded in-process with
    no listener (``test_adversarial_matrix._load_app``)."""
    sp, dp = _write_inputs(spec, df, strings)
    ap = os.path.join(os.path.dirname(sp), "app.py")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "er_%d" % abs(hash(sp)))
        doc = Document()
        ns["make_document"](doc)
    return doc, sorted(str(w.message) for w in caught)


def _sspec(graphs=None, plots=None, bo=None, go=None, kpis=None,
           formats=None, **gextra):
    """A sentinel spec: one graph of *plots*, or *graphs* in
    ``tp._spec``'s form; ``formats`` defaults to ``when`` as ``%td``."""
    b = dict(bo or {})
    b.setdefault("formats", formats if formats is not None
                 else {"when": "%td"})
    if graphs is None:
        graphs = [("g1", plots, go, dict(gextra))]
    return tp._spec(None, b, graphs=graphs, kpis=kpis)


def _p(ptype="scatter", qual=None, **kw):
    p = plot_for(ptype, **kw)
    if qual:
        p["qual_col"] = qual
    return p


# ===========================================================================
# Scanners
# ===========================================================================

def _decode_ndarray(obj):
    arr = obj.get("array") or {}
    if arr.get("type") == "bytes":
        raw = base64.b64decode(arr.get("data", ""))
        if raw[:2] == b"\x1f\x8b":         # Bokeh gzips a large array
            raw = gzip.decompress(raw)
        try:
            return np.frombuffer(raw, dtype=obj.get("dtype", "float64"))
        except (TypeError, ValueError):
            return np.array([])
    return np.asarray(arr if isinstance(arr, list) else [], dtype=object)


def _collect_json(obj, nums, strs):
    if isinstance(obj, dict):
        if obj.get("type") == "ndarray" and "array" in obj:
            for v in _decode_ndarray(obj).tolist():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    nums.append(float(v))
                elif isinstance(v, str):
                    strs.append(v)
            return
        for v in obj.values():
            _collect_json(v, nums, strs)
    elif isinstance(obj, list):
        for v in obj:
            _collect_json(v, nums, strs)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        nums.append(float(obj))
    elif isinstance(obj, str):
        strs.append(obj)


_JSON_SCRIPT = re.compile(
    r'<script type="application/json"[^>]*>(.*?)</script>', re.S)


_DOCS_JSON = re.compile(r"const docs_json = '(.*?)';\n", re.S)


def _page_docs(page):
    """Every Bokeh document a saved page embeds: the application/json
    scripts of ``file_html``, and the ``docs_json`` literal of the
    layout(bs) page's ``components``."""
    out = []
    for body in _JSON_SCRIPT.findall(page):
        try:
            out.append(json.loads(body))
        except ValueError:
            continue
    # Flipped (WP-30 P1.5): docs_json read as plain JSON was wrong once
    # every numeric axis carries Stata's writer, because it is a JavaScript
    # string literal and the writer's code holds escaped quotes; the
    # literal is unescaped first.
    for body in _DOCS_JSON.findall(page):
        try:
            out.append(json.loads(body.encode("latin-1", "backslashreplace")
                                   .decode("unicode_escape")))
        except ValueError:
            continue
    return out


def _page_values(page):
    """``(numbers, strings)`` of every embedded JSON document of a saved
    page, base64 ndarrays decoded."""
    nums, strs = [], []
    for d in _page_docs(page):
        _collect_json(d, nums, strs)
    return nums, strs


def _doc_values(models):
    """``(numbers, strings)`` of every property of every model reachable
    from *models* (a Document or a list of models), with no depth cutoff."""
    if isinstance(models, Document):
        roots = list(models.roots)
    else:
        roots = list(models)
    seen_models = set()
    todo = []
    for r in roots:
        todo.extend(r.references())
    nums, strs = [], []
    # id -> object, so a temporary container is kept alive and its id is
    # never reused by a later one (which would then be skipped).
    seen = {}

    def walk(v):
        if isinstance(v, (dict, list, tuple, np.ndarray)):
            if id(v) in seen:
                return
            seen[id(v)] = v
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)
        elif isinstance(v, np.ndarray):
            if np.issubdtype(v.dtype, np.datetime64):
                walk([float(x) for x in
                      v.astype("datetime64[ms]").astype("int64")])
            else:
                walk(v.tolist())
        elif isinstance(v, pd.Series):
            walk(v.tolist())
        elif isinstance(v, bool) or v is None:
            return
        elif isinstance(v, (int, float, np.integer, np.floating)):
            nums.append(float(v))
        elif isinstance(v, str):
            strs.append(v)
        elif hasattr(v, "properties_with_values"):
            if id(v) not in seen_models:
                seen_models.add(id(v))
                walk(v.properties_with_values(include_defaults=False))

    for m in todo:
        if id(m) in seen_models:
            continue
        seen_models.add(id(m))
        walk(m.properties_with_values(include_defaults=False))
    return nums, strs


def _excluded_hits(numbers, strings, frame, allowed):
    """``[(row, column)]`` for every value of a row outside *allowed* found
    in *numbers*/*strings*: mpg, weight, price, when (epoch ms) and name."""
    nums = np.asarray(numbers, dtype=float)
    joined = "\x00".join(strings)
    hits = []
    for row in range(len(frame)):
        if row in allowed:
            continue
        for col in ("mpg", "weight", "price"):
            v = float(frame[col].iloc[row])
            if nums.size and bool((np.abs(nums - v) < 1e-9).any()):
                hits.append((row + 1, col))
        ms = float(frame["when"].iloc[row]) * 86400000.0
        if nums.size and bool((np.abs(nums - ms) < 1e-3).any()):
            hits.append((row + 1, "when"))
        if frame["name"].iloc[row] in joined:
            hits.append((row + 1, "name"))
    return hits


# ===========================================================================
# The battery's cases
# ===========================================================================

def _range_plot(t):
    return _sspec(plots=[_p(t, qual="__dashq1")], bo={"filter": _RANGE})


def _cases():
    u12 = Q1 | Q2
    out = [
        ("plot-if scatter", lambda: _sspec(plots=[_p(qual="__dashq1")]), Q1),
        ("two plots q1 q2",
         lambda: _sspec(plots=[_p(qual="__dashq1"), _p(qual="__dashq2")]),
         u12),
        ("link q1 q2",
         lambda: _sspec(graphs=[("g1", [_p()], None, {"qual_col": "__dashq1"}),
                                ("g2", [_p()], None, {"qual_col": "__dashq2"})],
                        bo={"link": "g1 g2"}), u12),
        ("dropdown + graph q1",
         lambda: _sspec(plots=[_p()], bo={"filter": _DROPDOWN},
                        qual_col="__dashq1"), Q1),
        ("slider + graph q1",
         lambda: _sspec(plots=[_p()], bo={"filter": "price, type(slider)"},
                        qual_col="__dashq1"), Q1),
        ("by(foreign) + plot q2",
         lambda: _sspec(plots=[_p(qual="__dashq2")], go={"by": "foreign"}),
         Q2),
        ("by(foreign, total) + plot q2",
         lambda: _sspec(plots=[dict(_p(qual="__dashq2"),
                                    qual_col_total="__dashq2")],
                        go={"by": "foreign, total"}), Q2),
    ]
    for t in ("line", "area", "bar", "rarea", "rspike", "pcspike"):
        out.append(("%s plot q1 + range" % t,
                    (lambda t=t: _range_plot(t)), Q1))
    for t in ("histogram", "kdensity"):
        out.append(("%s plot q1 + range" % t,
                    (lambda t=t: _range_plot(t)), Q1))
    out += [
        ("option columns",
         lambda: _sspec(plots=[
             _p(qual="__dashq1", options={"mlabel": "name",
                                          "colorvar": "price"}),
             _p("lfit", qual="__dashq1",
                options={"weight": "aweight", "wexp": "price"})],
             go={"hover": "name when"}), Q1),
        ("date x + date range",
         lambda: _sspec(plots=[dict(_p("line", qual="__dashq1"),
                                    xvar="when")],
                        bo={"filter": "when, type(range)"}), Q1),
        ("brush card + link",
         lambda: _sspec(graphs=[("g1", [_p()], None, {"qual_col": "__dashq1"}),
                                ("g2", [_p()], None, {"qual_col": "__dashq2"})],
                        bo={"link": "g1 g2"},
                        kpis=[tp._kpi(update="brush")]), u12),
        ("layout(bs)",
         lambda: _sspec(plots=[_p(qual="__dashq1")], bo={"layout": "bs"}),
         Q1),
        ("tabs",
         lambda: _sspec(graphs=[("g1", [_p(qual="__dashq1")]),
                                ("g2", [_p(qual="__dashq2")])],
                        bo={"tabs": "A: g1 / B: g2"}), u12),
    ]
    return out


_CASES = _cases()
_IDS = [c[0] for c in _CASES]


def _with_a_move(spec):
    """*spec* with a filter to move: its own, else a price range."""
    s = json.loads(json.dumps(spec))
    if not (s["build_options"].get("filter") or "").strip():
        s["build_options"]["filter"] = _RANGE
    return s


def _move_value(widget):
    """A value that drops something: a range's/slider's lower bound raised
    past its first value, a dropdown's first real option."""
    if isinstance(widget, Select):
        real = [v for v, _lab in widget.options if v != "__all__"]
        return real[0] if real else "__all__"
    start, end = float(widget.start), float(widget.end)
    lo = start + (end - start) / 4.0
    if type(widget).__name__ in ("RangeSlider", "DateRangeSlider"):
        return (lo, end)
    return lo


def _saved_models(r):
    """The saved renderer's models: its layout root, or -- a layout(bs)
    page has none -- its figures, widgets, cards and callbacks."""
    if r._last_layout_root is not None:
        return [r._last_layout_root]
    return (list(r.figures.values()) + list(r.filter_widgets)
            + list(r.kpi_divs.values()) + list(r.filter_callbacks))


def _saved_after_move(spec):
    s = _with_a_move(spec)
    r, _page, _ = _saved(s)
    sess = js_runner.JsSession(r.filter_callbacks)
    for w, cb in zip(r.filter_widgets, r.filter_callbacks):
        sess.set(w, _move_value(w))
        sess.run(cb)
        _NODE_RUNS.append(1)
    return r


def _served_after_move(spec):
    s = _with_a_move(spec)
    doc, _ = _served(s)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for w in tp._widgets_of(doc):
            tp._fire(w, _move_value(w))
    return doc


# ===========================================================================
# Units: the plan's helpers
# ===========================================================================

def _frame10():
    return pd.DataFrame({"a": np.arange(10.0), "b": np.arange(10.0) * 2,
                         "c": ["s%d" % i for i in range(10)],
                         "price": np.arange(10.0) + 100})


def _mask(rows, n=10, index=None):
    idx = pd.RangeIndex(n) if index is None else index
    return pd.Series([i in rows for i in range(n)], index=idx)


class TestEmbedRowsOf:
    def test_a_qualifier_column_is_read_by_index(self):
        f = _frame10()
        got = dr._dash_embed_rows_of({"qual_col": "__dashq1"}, f,
                                     {"__dashq1": _mask({2, 4})})
        assert got.tolist() == [i in (2, 4) for i in range(10)]
        assert got.index.equals(f.index)

    def test_a_text_qualifier_counts_in_over_the_frame(self):
        got = dr._dash_embed_rows_of({"in_expr": "3/8"}, _frame10(), {})
        assert got.tolist() == [2 <= i <= 7 for i in range(10)]

    def test_no_qualifier_is_every_row(self):
        f = _frame10()
        assert dr._dash_embed_rows_of({}, f, {}).tolist() == [True] * 10
        assert dr._dash_embed_rows_of("x", f, {}).tolist() == [True] * 10

    def test_an_unknown_column_raises(self):
        with pytest.raises(ValueError):
            dr._dash_embed_rows_of({"qual_col": "__dashq9"}, _frame10(), {})

    def test_a_qualifier_the_whitelist_refuses_is_every_row_quietly(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_embed_rows_of(
                {"if_expr": "__import__('os').system('x')"}, _frame10(), {})
        assert got.tolist() == [True] * 10
        assert [str(w.message) for w in caught] == []


def _plan(spec, frame=None, masks=None, link="", filters=(), csv=False):
    frame = _frame10() if frame is None else frame
    return dr._dash_embed_plan(spec, frame, masks or {}, link,
                               list(filters), csv)


def _g(name, plots, **extra):
    g = {"name": name, "graph_options": {"name": name}, "plots": plots}
    g.update(extra)
    return g


def _sp(y="a", x="b", **kw):
    d = {"type": "scatter", "yvar": y, "xvar": x, "options": {}}
    d.update(kw)
    return d


class TestThePlan:
    def test_a_graph_qualifier_selects_the_graphs_rows(self):
        p = _plan({"graphs": [_g("g1", [_sp()], qual_col="q")]},
                  masks={"q": _mask({1, 2})})
        assert p["graph_rows"]["g1"].tolist() == [i in (1, 2)
                                                  for i in range(10)]
        assert p["rows"].tolist() == p["graph_rows"]["g1"].tolist()

    def test_a_layer_qualifier_intersects_the_graphs(self):
        p = _plan({"graphs": [_g("g1", [_sp(qual_col="p")], qual_col="q")]},
                  masks={"q": _mask({1, 2, 3}), "p": _mask({2, 3, 4})})
        want = [i in (2, 3) for i in range(10)]
        assert p["graph_rows"]["g1"].tolist() == want
        assert p["need"]["a"].tolist() == want
        assert p["need"]["c"].tolist() == [False] * 10

    def test_the_total_panel_adds_its_own_rows(self):
        g = _g("g1", [_sp(qual_col="p", qual_col_total="t")],
               graph_options={"name": "g1", "by": "a, total"})
        p = _plan({"graphs": [g]},
                  masks={"p": _mask({1}), "t": _mask({5})})
        assert p["graph_rows"]["g1"].tolist() == [i in (1, 5)
                                                  for i in range(10)]

    def test_a_literal_layer_reads_no_row(self):
        p = _plan({"graphs": [_g("g1", [{"type": "function", "expr": "x",
                                         "options": {}}])]})
        assert p["graph_rows"]["g1"].tolist() == [False] * 10
        assert p["rows"].tolist() == [False] * 10

    def test_hover_and_by_columns_are_needed_on_the_layers_rows(self):
        g = _g("g1", [_sp(qual_col="p")],
               graph_options={"name": "g1", "hover": "c", "by": "price"})
        p = _plan({"graphs": [g]}, masks={"p": _mask({4})})
        want = [i == 4 for i in range(10)]
        assert p["need"]["c"].tolist() == want
        assert p["need"]["price"].tolist() == want

    def test_option_columns_are_needed_on_the_layers_rows(self):
        opts = {"colorvar": "price", "mlabel": "c", "wexp": "b"}
        p = _plan({"graphs": [_g("g1", [_sp(y="a", x="a", qual_col="p",
                                            options=opts)])]},
                  masks={"p": _mask({6})})
        want = [i == 6 for i in range(10)]
        for c in ("price", "c", "b"):
            assert p["need"][c].tolist() == want, c

    def test_a_brush_card_needs_its_variable_on_every_source(self):
        spec = {"graphs": [_g("g1", [_sp(qual_col="p")])],
                "kpis": [{"name": "k1", "var": "price", "update": "brush"}]}
        p = _plan(spec, masks={"p": _mask({3})})
        assert p["need"]["price"].tolist() == [i == 3 for i in range(10)]

    def test_a_filter_reaches_the_graphs_it_applies_to(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q"),
                           _g("g2", [_sp()], qual_col="r")]}
        p = _plan(spec, masks={"q": _mask({1}), "r": _mask({8})},
                  filters=[{"varname": "price", "type": "range",
                            "exclude": []}])
        assert p["filter_rows"][0].tolist() == [i in (1, 8)
                                                for i in range(10)]
        assert p["need"]["price"].tolist() == [i in (1, 8)
                                               for i in range(10)]

    def test_exclude_narrows_the_reach(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q"),
                           _g("g2", [_sp()], qual_col="r")]}
        p = _plan(spec, masks={"q": _mask({1}), "r": _mask({8})},
                  filters=[{"varname": "price", "type": "range",
                            "exclude": ["g2"]}])
        assert p["filter_rows"][0].tolist() == [i == 1 for i in range(10)]

    def test_a_link_group_is_reached_unless_every_member_is_excluded(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q"),
                           _g("g2", [_sp()], qual_col="r")]}
        masks = {"q": _mask({1}), "r": _mask({8})}
        one = _plan(spec, masks=masks, link="g1 g2",
                    filters=[{"varname": "price", "exclude": ["g1"]}])
        both = _plan(spec, masks=masks, link="g1 g2",
                     filters=[{"varname": "price", "exclude": ["g1", "g2"]}])
        assert one["link_rows"].tolist() == [i in (1, 8) for i in range(10)]
        assert one["filter_rows"][0].tolist() == one["link_rows"].tolist()
        assert both["filter_rows"][0].tolist() == [False] * 10

    def test_a_filter_mode_card_adds_its_own_rows(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q")],
                "kpis": [{"name": "k1", "var": "c", "update": "filter",
                          "qual_col": "k"}]}
        p = _plan(spec, masks={"q": _mask({1}), "k": _mask({7})},
                  filters=[{"varname": "price", "exclude": []}])
        assert p["filter_rows"][0].tolist() == [i in (1, 7)
                                                for i in range(10)]
        assert p["need"]["c"].tolist() == [i == 7 for i in range(10)]

    def test_a_static_card_adds_nothing(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q")],
                "kpis": [{"name": "k1", "var": "c", "update": "filter"}]}
        p = _plan(spec, masks={"q": _mask({1})})
        assert p["rows"].tolist() == [i == 1 for i in range(10)]
        assert p["need"]["c"].tolist() == [False] * 10

    def test_csv_needs_every_cell_and_moves_no_row_set(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q")]}
        f = [{"varname": "price", "exclude": []}]
        masks = {"q": _mask({1})}
        a = _plan(spec, masks=masks, filters=f, csv=False)
        b = _plan(spec, masks=masks, filters=f, csv=True)
        assert all(v.all() for v in b["need"].values())
        assert b["rows"].all()
        assert a["graph_rows"]["g1"].tolist() == b["graph_rows"]["g1"].tolist()
        assert a["filter_rows"][0].tolist() == b["filter_rows"][0].tolist()
        assert a["link_rows"].tolist() == b["link_rows"].tolist()

    def test_an_empty_frame(self):
        f = _frame10().iloc[0:0]
        p = _plan({"graphs": [_g("g1", [_sp()])]}, frame=f,
                  filters=[{"varname": "price"}])
        assert p["rows"].tolist() == []
        assert p["filter_rows"][0].tolist() == []

    def test_served_filter_keys_are_read(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q")]}
        masks = {"q": _mask({2})}
        a = _plan(spec, masks=masks, filters=[{"var": "price"}])
        b = _plan(spec, masks=masks, filters=[{"varname": "price"}])
        assert a["need"]["price"].tolist() == b["need"]["price"].tolist() \
            == [i == 2 for i in range(10)]

    def test_a_graph_options_qualifier_is_ored(self):
        g = _g("g1", [_sp()], graph_options={"name": "g1",
                                             "in_expr": "1/2"})
        p = _plan({"graphs": [g]})
        # The graph dict carries no qualifier of its own: every row, ORed
        # with graph_options' -- never fewer rows than either mode draws.
        assert p["graph_rows"]["g1"].tolist() == [True] * 10
        g2 = _g("g1", [_sp()], if_expr="a > 7",
                graph_options={"name": "g1", "in_expr": "1/2"})
        p2 = _plan({"graphs": [g2]})
        assert p2["graph_rows"]["g1"].tolist() == [i in (0, 1, 8, 9)
                                                   for i in range(10)]

    def test_link_all_is_expanded(self):
        spec = {"graphs": [_g("g1", [_sp()], qual_col="q"),
                           _g("g2", [_sp()], qual_col="r")]}
        p = _plan(spec, masks={"q": _mask({1}), "r": _mask({8})},
                  link="_all")
        assert p["link_rows"].tolist() == [i in (1, 8) for i in range(10)]

    def test_the_filters_are_never_parsed(self):
        spec = {"graphs": [_g("g1", [_sp()])],
                "build_options": {"filter": "price, type(bogus)"}}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            p = _plan(spec)
        assert [str(w.message) for w in caught] == []
        assert p["filter_rows"] == []

    def test_the_renderer_computes_the_plan_once(self, monkeypatch):
        calls = []
        real = dr._dash_embed_plan

        def spy(*a, **k):
            calls.append(1)
            return real(*a, **k)

        monkeypatch.setattr(dr, "_dash_embed_plan", spy)
        _saved(_sspec(plots=[_p(qual="__dashq1")], bo={"filter": _RANGE}))
        assert len(calls) == 1


class TestEmbedValues:
    def test_each_dtype_is_blanked_as_stata_misses_it(self):
        need = pd.Series([True, False])
        f = dr._dash_embed_values(pd.Series([1.5, 2.5]), need)
        assert f.iloc[0] == 1.5 and np.isnan(f.iloc[1])
        d = dr._dash_embed_values(
            pd.Series(pd.to_datetime(["2020-01-01", "2020-01-02"])), need)
        assert d.iloc[0] == pd.Timestamp("2020-01-01") and pd.isna(d.iloc[1])
        assert d.dtype.kind == "M"
        s = dr._dash_embed_values(pd.Series(["x", "y"]), need)
        assert s.tolist() == ["x", ""]
        b = dr._dash_embed_values(pd.Series([True, True]), need)
        assert b.iloc[0] == True and pd.isna(b.iloc[1])  # noqa: E712

    def test_all_needed_returns_the_series_itself(self):
        s = pd.Series([1.0, 2.0])
        assert dr._dash_embed_values(s, pd.Series([True, True])) is s

    def test_none_blanks_everything(self):
        got = dr._dash_embed_values(pd.Series([1.0, 2.0]), None)
        assert got.isna().all()


class TestEmbedFrame:
    def test_rows_and_columns_are_restricted_and_blanked(self):
        f = _frame10()
        plan = {"rows": _mask({1, 2, 3}),
                "need": {"a": _mask({1, 2, 3}), "c": _mask({2})}}
        got = dr._dash_embed_frame(f, plan, ["a", "c"])
        assert list(got.index) == [1, 2, 3]
        assert got["a"].tolist() == [1.0, 2.0, 3.0]
        assert got["c"].tolist() == ["", "s2", ""]

    def test_an_absent_column_is_skipped_and_order_kept(self):
        f = _frame10()
        plan = {"rows": _mask({0}), "need": {"a": _mask({0}),
                                             "b": _mask({0})}}
        got = dr._dash_embed_frame(f, plan, ["b", "zz", "a", "b"])
        assert list(got.columns) == ["b", "a"]
        got2 = dr._dash_embed_frame(f, plan, ["a"], rows=_mask({0, 5}))
        assert list(got2.index) == [0, 5]


class TestThePageIndex:
    def test_kept_rows_are_ranked_first_in_data_order(self):
        got = dr._dash_page_index(pd.RangeIndex(10), _mask({1, 3, 5, 7, 9}))
        assert list(got) == [5, 0, 6, 1, 7, 2, 8, 3, 9, 4]

    def test_every_row_kept_is_the_identity(self):
        got = dr._dash_page_index(pd.RangeIndex(10), _mask(set(range(10))))
        assert list(got) == list(range(10))

    def test_an_empty_frame(self):
        got = dr._dash_page_index(pd.RangeIndex(0),
                                  pd.Series([], dtype=bool))
        assert list(got) == []

    def test_a_non_range_index(self):
        idx = pd.Index([10, 20, 30])
        got = dr._dash_page_index(idx, pd.Series([False, True, True],
                                                 index=idx))
        assert list(got) == [2, 0, 1]


class TestRelabel:
    def test_series_dicts_and_lists_are_relabelled_in_order(self):
        old = pd.RangeIndex(4)
        new = pd.Index([2, 0, 3, 1])
        s = pd.Series([True, False, True, False], index=old)
        plan = {"rows": s, "need": {"a": s.copy()}, "graph_rows": {"g": s},
                "link_rows": s, "filter_rows": [s, s]}
        got = dr._dash_relabel(plan, old, new)
        for v in [got["rows"], got["need"]["a"], got["graph_rows"]["g"],
                  got["link_rows"]] + got["filter_rows"]:
            assert list(v.index) == [2, 0, 3, 1]
            assert v.tolist() == [True, False, True, False]

    def test_a_series_not_indexed_like_the_data_raises(self):
        with pytest.raises(ValueError, match="not indexed like the data"):
            dr._dash_relabel(pd.Series([1, 2]), pd.RangeIndex(10),
                             pd.RangeIndex(10))

    def test_other_values_pass_through(self):
        assert dr._dash_relabel("x", pd.RangeIndex(1), pd.RangeIndex(1)) \
            == "x"
        assert dr._dash_relabel(None, pd.RangeIndex(1),
                                pd.RangeIndex(1)) is None


# ===========================================================================
# Regressions: the sentinel battery
# ===========================================================================

@pytest.mark.parametrize("name,build,allowed", _CASES, ids=_IDS)
class TestTheSavedPageHoldsOnlySelectedRows:
    def test_no_excluded_value_is_embedded(self, name, build, allowed):
        r, page, _ = _saved(build())
        nums, strs = _page_values(page)
        assert nums, "the page decoded to nothing"
        hits = _excluded_hits(nums, strs, _sentinel_frame(), allowed)
        assert hits == [], (name, hits)

    def test_none_after_a_move(self, name, build, allowed):
        r = _saved_after_move(build())
        nums, strs = _doc_values(_saved_models(r))
        hits = _excluded_hits(nums, strs, _sentinel_frame(), allowed)
        assert hits == [], (name, hits)


@pytest.mark.parametrize("name,build,allowed", _CASES, ids=_IDS)
class TestTheServedDocumentHoldsOnlySelectedRows:
    def test_no_excluded_value_is_sent(self, name, build, allowed):
        doc, _ = _served(build())
        nums, strs = _doc_values(doc)
        hits = _excluded_hits(nums, strs, _sentinel_frame(), allowed)
        assert hits == [], ("served:", name, hits)

    def test_none_after_a_filter_move(self, name, build, allowed):
        doc = _served_after_move(build())
        nums, strs = _doc_values(doc)
        hits = _excluded_hits(nums, strs, _sentinel_frame(), allowed)
        assert hits == [], ("served:", name, hits)


def _sources(models):
    out, seen = [], set()
    roots = list(models.roots) if isinstance(models, Document) else models
    for r in roots:
        for m in r.references():
            if isinstance(m, ColumnDataSource) and id(m) not in seen:
                seen.add(id(m))
                out.append(m)
    return out


def _saved_ids(r):
    ids = set()
    for s in _sources(_saved_models(r)):
        for v in s.data.get(dr._ROW_ID_COLUMN, []):
            ids.add(int(v))
    return ids


class TestTheRowsAreTheUnionOfTheQualifiers:
    def test_distinct_row_ids_both_modes(self):
        spec = _sspec(plots=[_p(qual="__dashq1"), _p(qual="__dashq2")])
        r, _, _ = _saved(spec)
        assert _saved_ids(r) == set(range(7)), sorted(_saved_ids(r))
        lspec = _sspec(graphs=[("g1", [_p(qual="__dashq1"),
                                       _p(qual="__dashq2")])],
                       bo={"link": "g1"})
        doc, _ = _served(lspec)
        shared = [s for s in _sources(doc)
                  if getattr(s, "_dash_link_source", False)]
        assert shared, "served: no shared source"
        assert len(shared[0].data["index"]) == 7, (
            "served:", list(shared[0].data["index"]))

    def test_the_page_rows_are_statas_union_on_auto(self, monkeypatch):
        truth = _truth()["p1"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        spec = tp._spec([plot_for("scatter", if_expr="foreign == 1"),
                         plot_for("scatter", if_expr="price > 10000")])
        r, _ = tp._standalone(spec)
        assert len(_saved_ids(r)) == truth["union_n"]
        labels = getattr(r, "_page_labels", None)
        assert labels is not None, "the page records no labels"
        assert [int(l) + 1 for l in labels] == truth["union_obs"]


def _widget_state(w):
    kind = type(w).__name__
    if isinstance(w, Select):
        return (kind, [lab for _v, lab in w.options], bool(w.disabled))
    st = (float(w.start), float(w.end))
    return (kind, st, bool(w.disabled))


def _saved_widgets(spec, df=None):
    r, _, warns = _saved(spec, df)
    return [_widget_state(w) for w in r.filter_widgets], warns


def _served_widgets(spec, df=None):
    doc, warns = _served(spec, df)
    return [_widget_state(w) for w in tp._widgets_of(doc)], warns


class TestTheFilterWidgetSpansItsReach:
    def test_slider_and_range_bounds_both_modes(self, monkeypatch):
        want = tuple(_truth()["p5"]["price_gt_4500"])
        for f, kind in (("price, type(range)", "RangeSlider"),
                        ("price, type(slider)", "Slider")):
            spec = tp._spec([plot_for("scatter")], {"filter": f},
                            if_expr="price > 4500")
            r, _ = tp._standalone(spec)
            (w,) = r.filter_widgets
            assert (type(w).__name__, float(w.start), float(w.end)) == (
                kind, want[0], want[1])
            doc, _ = tp._served(spec)
            (sw,) = tp._widgets_of(doc)
            assert (type(sw).__name__, float(sw.start), float(sw.end)) == (
                kind, want[0], want[1]), "served: %s" % f

    def test_dropdown_values_both_modes(self, monkeypatch):
        want = ["All"] + ["%g" % v for v in _truth()["p4"]["rep78_if_foreign"]]
        auto = sfm._auto().rename(columns={"rep78": "rep"})
        # Flipped (WP-31 H2f): the levels alone were right until a dropdown
        # over a variable with a missing value in its reach listed
        # "(missing)" last; one foreign car's rep78 is missing.
        assert auto.loc[auto["foreign"] == 1, "rep"].isna().any()
        want = want + ["(missing)"]
        monkeypatch.setattr(tp, "_DF", auto)
        spec = tp._spec([plot_for("scatter")], {"filter": "rep, type(dropdown)"},
                        if_expr="foreign == 1")
        r, _ = tp._standalone(spec)
        (w,) = r.filter_widgets
        assert [lab for _v, lab in w.options] == want
        doc, _ = tp._served(spec)
        (sw,) = tp._widgets_of(doc)
        assert [lab for _v, lab in sw.options] == want, "served:"

    def test_exclude_narrows_the_reach(self):
        spec = _sspec(graphs=[("g1", [_p()], None, {"qual_col": "__dashq1"}),
                              ("g2", [_p()], None, {"qual_col": "__dashq2"})],
                      bo={"filter": "price, type(range) exclude(g2)"})
        want = [("RangeSlider", (5002.75, 5010.75), False)]
        assert _saved_widgets(spec)[0] == want
        assert _served_widgets(spec)[0] == want, "served:"

    def test_an_unqualified_filter_mode_card_spans_every_row(self):
        spec = tp._spec([plot_for("scatter")], {"filter": _RANGE},
                        if_expr="price > 4500", kpis=[tp._kpi()])
        r, _ = tp._standalone(spec)
        (w,) = r.filter_widgets
        assert (float(w.start), float(w.end)) == (3799.0, 11385.0)
        doc, _ = tp._served(spec)
        (sw,) = tp._widgets_of(doc)
        assert (float(sw.start), float(sw.end)) == (3799.0, 11385.0), "served:"

    def test_a_label_only_excluded_rows_carry_is_not_listed(self):
        spec = _sspec(plots=[_p()], bo={"filter": "lab, type(dropdown)"},
                      qual_col="__dashq1")
        want = ["All"] + ["lab-%02d" % (i + 1) for i in sorted(Q1)]
        (w,), _ = _saved_widgets(spec)
        assert w[1] == want, w
        (sw,), _ = _served_widgets(spec)
        assert sw[1] == want, ("served:", sw)


class TestAnEmptyReach:
    def test_range_slider_and_dropdown_both_modes(self):
        spec = tp._spec([plot_for("scatter")],
                        {"filter": "price, type(range) || "
                                   "mpg, type(slider) || rep, type(dropdown)"},
                        if_expr="price > 1000000")
        want = [("RangeSlider", (0.0, 1.0), True), ("Slider", (0.0, 1.0), True),
                ("Select", ["All"], False)]
        r, _ = tp._standalone(spec)
        assert [_widget_state(w) for w in r.filter_widgets] == want
        doc, _ = tp._served(spec)
        assert [_widget_state(w) for w in tp._widgets_of(doc)] == want, \
            "served:"

    def test_date_range_both_modes(self):
        spec = tp._spec([plot_for("scatter")], {"filter": "when, type(range)",
                                                "formats": {"when": "%td"}},
                        if_expr="price > 1000000")
        want = [("RangeSlider", (0.0, 1.0), True)]
        r, _ = tp._standalone(spec)
        assert [_widget_state(w) for w in r.filter_widgets] == want
        doc, _ = tp._served(spec)
        assert [_widget_state(w) for w in tp._widgets_of(doc)] == want, \
            "served:"


class TestAFilterEveryTargetExcludes:
    def test_widget_state_both_modes(self):
        spec = tp._spec([plot_for("scatter")],
                        {"filter": "price, type(range) exclude(g1 k1) || "
                                   "rep, type(dropdown) exclude(g1 k1)"},
                        kpis=[tp._kpi()])
        want = [("RangeSlider", (0.0, 1.0), True), ("Select", ["All"], False)]
        r, _ = tp._standalone(spec)
        std = [_widget_state(w) for w in r.filter_widgets]
        assert std == want
        doc, _ = tp._served(spec)
        assert [_widget_state(w) for w in tp._widgets_of(doc)] == std, \
            "served:"

    def test_a_literal_only_dashboard(self):
        spec = tp._spec([plot_for("function")], {"filter": _DROPDOWN})
        r, _ = tp._standalone(spec)
        assert [_widget_state(w) for w in r.filter_widgets] == [
            ("Select", ["All"], False)]
        doc, _ = tp._served(spec)
        assert [_widget_state(w) for w in tp._widgets_of(doc)] == [
            ("Select", ["All"], False)], "served:"


class TestTheFilterTypeFollowsTheReach:
    def test_a_dropdown_within_the_limit_on_its_reach_both_modes(self):
        spec = tp._spec([plot_for("scatter")],
                        {"filter": "price, type(dropdown)",
                         "limits": {"filter_options": 7}},
                        if_expr="price > 4500")
        r, warns = tp._standalone(spec)
        (w,) = r.filter_widgets
        assert isinstance(w, Select) and len(w.options) == 7, w
        assert not [m for m in warns if "drawn as type(range)" in m], warns
        doc, swarns = tp._served(spec)
        (sw,) = tp._widgets_of(doc)
        assert isinstance(sw, Select) and len(sw.options) == 7, ("served:", sw)
        assert not [m for m in swarns if "drawn as type(range)" in m], (
            "served:", swarns)


def _snapshot_rows(r):
    """Row counts of the saved snapshot and the CSV text source."""
    out = {}
    for cb in r.filter_callbacks:
        src = dict(cb.args).get("orig_source")
        if src is not None:
            out["snapshot"] = len(src.data.get(dr._ROW_ID_COLUMN, []))
    return out


class TestCsvDoesNotMoveTheDashboard:
    def test_widgets_sources_and_cards_equal_with_and_without_csv(self):
        base = dict(filter=_RANGE, link="g1 g2")
        graphs = [("g1", [plot_for("scatter")], None,
                   {"if_expr": "price > 4500", "in_expr": ""}),
                  ("g2", [plot_for("scatter")], None,
                   {"if_expr": "foreign == 1", "in_expr": ""})]
        kp = [tp._kpi(update="brush")]
        a = tp._spec(None, dict(base), graphs=graphs, kpis=kp)
        b = tp._spec(None, dict(base, csv="1"), graphs=graphs, kpis=kp)
        ra, _ = tp._standalone(a)
        rb, _ = tp._standalone(b)
        assert [_widget_state(w) for w in ra.filter_widgets] == \
            [_widget_state(w) for w in rb.filter_widgets]
        # The same observations (ids are page ranks, and csv puts every
        # row on the page, so the ranks themselves differ).
        la = [ra._page_labels[int(i)]
              for i in ra.sources["g1"].data[dr._ROW_ID_COLUMN]]
        lb = [rb._page_labels[int(i)]
              for i in rb.sources["g1"].data[dr._ROW_ID_COLUMN]]
        assert la == lb
        _, ca, _ = sfm._saved_selection(a, 0, [0], [[]])
        _, cb_, _ = sfm._saved_selection(b, 0, [0], [[]])
        assert ca == cb_
        assert _snapshot_rows(ra)["snapshot"] == 7
        assert _snapshot_rows(rb)["snapshot"] == 10


class TestRowIdentitiesAreDense:
    def test_ids_are_ranks_of_the_pages_rows(self):
        r, _, _ = _saved(_sspec(plots=[_p(qual="__dashq1")]))
        assert _saved_ids(r) == set(range(5)), sorted(_saved_ids(r))

    def test_member_and_qual_ids_are_within_the_ids(self):
        spec = tp._spec([plot_for("scatter", if_expr="price > 10000")],
                        {"filter": _RANGE}, if_expr="foreign == 1",
                        kpis=[tp._kpi(update="both", if_expr="mpg > 20")])
        r, _ = tp._standalone(spec)
        ids = _saved_ids(r)
        text = json.dumps([dict(cb.args).get("kpi_config_json", "")
                           for cb in r.filter_callbacks])
        found = [int(x) for grp in re.findall(
            r'(?:member_ids|qual_ids)\\?"\s*:\s*\[([^\]]*)\]', text)
            for x in re.findall(r"\d+", grp)]
        reg = getattr(r, "_view_filter_registry", None) or []
        assert set(found) <= ids, (sorted(found), sorted(ids))
        assert ids == set(range(len(ids)))
        assert reg is not None

    def test_an_unranked_label_raises_in_the_aligned_path(self):
        r, _, _ = _saved(_sspec(plots=[_p(qual="__dashq1")]))
        with pytest.raises(ValueError, match="does not hold"):
            r._row_ids_for(r.df.iloc[[0]])
        assert r._row_ids_kept(r.df.iloc[[0, 1]]) == [0]

    def test_member_ids_never_fall_back_to_positions(self):
        r, _, _ = _saved(_sspec(plots=[_p(qual="__dashq1")]))
        frame = r.df.iloc[[1, 2, 3]]
        # Row 2 is not on the page: dropped, never numbered by position.
        assert r._row_ids_kept(frame) == [0, 1]


class TestABrushCountsTheRowsTheGraphShows:
    _SC_IN = tp._spec([plot_for("scatter", in_expr="3/8")],
                      {"filter": _DROPDOWN}, kpis=[tp._kpi(update="brush")])

    def test_a_layers_own_in_after_a_move_both_modes(self):
        want = _truth()["p5"]["mpg_foreign_in_3_8"]["text"]
        mv = ("Select", "Foreign")
        _, std, _ = sfm._saved_selection(self._SC_IN, 0, [0, 1, 2], ["move"],
                                         mv)
        assert std == {"k1": want}, std
        _, srv, _ = sfm._served_selection(self._SC_IN, 0, [0, 1, 2],
                                          ["move"], mv)
        assert srv == {"k1": want}, ("served:", srv)

    def test_a_layers_own_in_cleared_both_modes(self):
        want = _truth()["p5"]["mpg_in_3_8"]["text"]
        _, std, _ = sfm._saved_selection(self._SC_IN, 0, [0, 1], [[]])
        assert std == {"k1": want}, std
        _, srv, _ = sfm._served_selection(self._SC_IN, 0, [0, 1], [[]])
        assert srv == {"k1": want}, ("served:", srv)

    def test_a_qualified_link_groups_cleared_brush_both_modes(self,
                                                              monkeypatch):
        want = _truth()["p4"]["mpg_union"]["text"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        spec = tp._spec(None, {"link": "g1 g2"},
                        graphs=[("g1", [plot_for("scatter")], None,
                                 {"if_expr": "foreign == 1", "in_expr": ""}),
                                ("g2", [plot_for("scatter")], None,
                                 {"if_expr": "price > 10000",
                                  "in_expr": ""})],
                        kpis=[tp._kpi(update="brush")])
        _, std, _ = sfm._saved_selection(spec, 0, [0, 1], [[]])
        assert std == {"k1": want}, std
        _, srv, _ = sfm._served_selection(spec, 0, [0, 1], [[]])
        assert srv == {"k1": want}, ("served:", srv)

    def test_a_by_panel_with_a_layer_qualifier_both_modes(self):
        spec = tp._spec([plot_for("scatter", if_expr="price > 4500")], None,
                        {"by": "foreign"}, kpis=[tp._kpi(update="brush")])
        df = tp._DF
        for fig, f in ((0, 0.0), (1, 1.0)):
            rows = df[(df["foreign"] == f) & (df["price"] > 4500)]
            want = float(rows["mpg"].mean())
            _, std, _ = sfm._saved_selection(spec, fig, [0], [[]])
            assert abs(float(std["k1"]) - want) < 1e-4, (fig, std, want)
            _, srv, _ = sfm._served_selection(spec, fig, [0], [[]])
            assert srv == std, ("served:", fig, srv, std)


def _view_rows(renderer, id_col):
    src = renderer.data_source
    ids = list(src.data.get(id_col, []))
    flt = getattr(getattr(renderer, "view", None), "filter", None)
    if isinstance(flt, BooleanFilter) and flt.booleans is not None:
        return [ids[i] for i, b in enumerate(flt.booleans) if b and i < len(ids)]
    if isinstance(flt, IndexFilter) and flt.indices is not None:
        return [ids[i] for i in flt.indices if 0 <= i < len(ids)]
    return ids


def _scatter_rows(figs, id_col, labels):
    out = []
    for fig in figs:
        rs = [g for g in fig.renderers if isinstance(g, GlyphRenderer)
              and type(g.glyph).__name__ == "Scatter"
              and "mpg" in g.data_source.data]
        got = set()
        for g in rs:
            for v in _view_rows(g, id_col):
                got.add(int(labels[int(v)]) if labels is not None
                        else int(v))
        out.append(sorted(got))
    return out


class TestAfterAMoveBothModesDrawTheSameRows:
    _LO = 4800.0

    def _both(self, spec, oracle):
        r, _ = tp._standalone(spec)
        labels = getattr(r, "_page_labels", None)
        sess = js_runner.JsSession(r.filter_callbacks)
        (w,), (cb,) = r.filter_widgets, r.filter_callbacks
        sess.set(w, (self._LO, float(w.end)))
        sess.run(cb)
        _NODE_RUNS.append(1)
        saved = _scatter_rows(list(r.figures.values()), dr._ROW_ID_COLUMN,
                              labels)
        doc, _ = tp._served(spec)
        (sw,) = tp._widgets_of(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tp._fire(sw, (self._LO, float(sw.end)))
        served = _scatter_rows(sfm._figures(doc), "index", labels)
        assert saved == oracle, (saved, oracle)
        assert served == saved, ("served:", served, saved)

    def test_linked_by_with_a_layer_if(self):
        spec = tp._spec([plot_for("scatter", if_expr="price > 4500")],
                        {"link": "g1", "filter": _RANGE}, {"by": "foreign"})
        df = tp._DF
        oracle = [sorted(df.index[(df["foreign"] == f) & (df["price"] > 4500)
                                  & (df["price"] >= self._LO)])
                  for f in (0.0, 1.0)]
        self._both(spec, oracle)

    def test_linked_graph_if_with_a_layer_if(self):
        spec = tp._spec(None, {"link": "g1 g2", "filter": _RANGE},
                        graphs=[("g1", [plot_for("scatter",
                                                 if_expr="price > 4500")],
                                 None, {"if_expr": "foreign == 1",
                                        "in_expr": ""}),
                                ("g2", [plot_for("scatter")])])
        df = tp._DF
        oracle = [sorted(df.index[(df["foreign"] == 1) & (df["price"] > 4500)
                                  & (df["price"] >= self._LO)]),
                  sorted(df.index[df["price"] >= self._LO])]
        self._both(spec, oracle)


class TestTheJoinKeyFollowsThePagesRows:
    def test_sort_varlist_under_a_layer_if_both_modes(self):
        """sort(price) through the rank column __dashs1, the layer on rows
        4-6, whose ranks run backwards: the line joins rows 6, 5, 4 in
        both modes.  The saved order is read from the line's row ids
        (through ``r._page_labels``) and from its y values; the served
        one from its y values, each sentinel mpg naming its row (a
        served mapper copy's ``index`` is a position in the layer's
        source, E-8 probe 5)."""
        df = _sentinel_frame()
        df["__dashs1"] = [1.0, 2.0, 3.0, 6.0, 5.0, 4.0, 7.0, 8.0, 9.0, 10.0]
        p = dict(_p("line", qual="__dashq3"), sortvars="price")
        spec = _sspec(plots=[p], bo={"sort_cols": {"price": "__dashs1"}})
        r, _, _ = _saved(spec, df)
        labels = getattr(r, "_page_labels", None)

        def obs_of_mpg(vals):
            return [int(df.index[df["mpg"] == float(v)][0]) for v in vals]

        def line_of(figs):
            (fig,) = figs
            (line,) = [g for g in fig.renderers
                       if isinstance(g, GlyphRenderer)
                       and type(g.glyph).__name__ == "Line"]
            return line

        line = line_of(list(r.figures.values()))
        ids = list(line.data_source.data[dr._ROW_ID_COLUMN])
        saved = [int(labels[int(v)]) if labels is not None else int(v)
                 for v in ids]
        assert saved == [5, 4, 3], saved
        assert obs_of_mpg(line.data_source.data[line.glyph.y]) == saved
        doc, _ = _served(spec, df)
        sline = line_of(sfm._figures(doc))
        served = obs_of_mpg(sline.data_source.data[sline.glyph.y])
        assert served == saved, ("served:", served, saved)


# ===========================================================================
# The served index is a page rank (TR-14.16, TR-14.18)
# ===========================================================================

def _index_values_doc(doc):
    out = []
    for s in _sources(doc):
        out.extend(s.data.get("index", []))
    return out


def _walk_cds(obj, out):
    if isinstance(obj, dict):
        if obj.get("name") == "ColumnDataSource" or (
                obj.get("type") == "object"
                and obj.get("name") == "ColumnDataSource"):
            data = (obj.get("attributes") or {}).get("data")
            if isinstance(data, dict):
                entries = data.get("entries") if "entries" in data else None
                items = (entries if entries is not None
                         else list(data.items()))
                for kv in items:
                    k, v = kv[0], kv[1]
                    if k == "index":
                        vals = (_decode_ndarray(v).tolist()
                                if isinstance(v, dict) else v)
                        out.extend(vals)
        for v in obj.values():
            _walk_cds(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_cds(v, out)


def _index_values_page(page):
    out = []
    for d in _page_docs(page):
        _walk_cds(d, out)
    return out


def _in_ranks(values, m):
    return [v for v in values
            if not (float(v) == int(float(v)) and 0 <= int(float(v)) < m)]


_NUMBERED = ["plot-if scatter", "two plots q1 q2", "link q1 q2",
             "by(foreign) + plot q2"]


def _scatter_pairs(figs, id_col):
    """``{mpg: id}`` over every scatter renderer's drawn rows."""
    out = {}
    for fig in figs:
        for g in fig.renderers:
            if not (isinstance(g, GlyphRenderer)
                    and type(g.glyph).__name__ == "Scatter"):
                continue
            d = g.data_source.data
            if "mpg" not in d or id_col not in d:
                continue
            flt = getattr(getattr(g, "view", None), "filter", None)
            pos = range(len(d["mpg"]))
            if isinstance(flt, BooleanFilter) and flt.booleans is not None:
                pos = [i for i, b in enumerate(flt.booleans) if b]
            elif isinstance(flt, IndexFilter) and flt.indices is not None:
                pos = list(flt.indices)
            for i in pos:
                out[float(d["mpg"][i])] = int(d[id_col][i])
    return out


def _case(name):
    return [c for c in _CASES if c[0] == name][0]


class TestTheServedIndexIsARank:
    @pytest.mark.parametrize("name,build,allowed", _CASES, ids=_IDS)
    def test_no_index_label_outside_the_pages_ranks(self, name, build,
                                                    allowed):
        m = len(allowed)
        _r, page, _ = _saved(build())
        bad = _in_ranks(_index_values_page(page), m)
        assert bad == [], (name, m, sorted(set(bad)))
        doc, _ = _served(build())
        bad = _in_ranks(_index_values_doc(doc), m)
        assert bad == [], ("served:", name, m, sorted(set(bad)))

    @pytest.mark.parametrize("name,build,allowed", _CASES, ids=_IDS)
    def test_none_after_a_filter_move(self, name, build, allowed):
        doc = _served_after_move(build())
        bad = _in_ranks(_index_values_doc(doc), len(allowed))
        assert bad == [], ("served:", name, sorted(set(bad)))

    @pytest.mark.parametrize("name", _NUMBERED)
    def test_a_row_is_numbered_as_the_saved_page_numbers_it(self, name):
        """Each drawn row's served ``index`` is the saved page's
        ``__dash_row__`` for the same observation, and ``r._page_labels`` turns
        it into the observation's label."""
        _n, build, _allowed = _case(name)
        r, _, _ = _saved(build())
        labels = getattr(r, "_page_labels", None)
        assert labels is not None, "the saved page records no _page_labels"
        saved = _scatter_pairs(list(r.figures.values()), dr._ROW_ID_COLUMN)
        doc, _ = _served(build())
        served = _scatter_pairs(sfm._figures(doc), "index")
        assert served and served == saved, ("served:", served, saved)
        df = _sentinel_frame()
        for mpg, rank in saved.items():
            obs = int(df.index[df["mpg"] == mpg][0])
            assert int(labels[rank]) == obs, (mpg, rank, obs)

    def test_a_linked_selection_names_the_same_observations_both_modes(self):
        _n, build, allowed = _case("link q1 q2")
        spec = build()
        spec["kpis"] = [tp._kpi(update="brush")]
        spec["build_options"]["registry"] += " k1"
        m = len(allowed)
        r, _, _ = _saved(spec)
        doc, _ = _served(spec)
        shared = [s for s in _sources(doc)
                  if getattr(s, "_dash_link_source", False)][0]
        assert list(shared.data["index"]) == list(range(m)), (
            "served:", list(shared.data["index"]))
        assert list(r._dash_linked_source.data[dr._ROW_ID_COLUMN]) == \
            list(range(m))
        df = _sentinel_frame()
        want_rows = [int(x) for x in r._page_labels[0:2]]
        want = float(df["mpg"].iloc[want_rows].mean())
        _NODE_RUNS.append(1)
        _, std, _ = _sel_saved(spec, [0, 1])
        assert abs(float(std["k1"].replace(",", "")) - want) < 1e-3, std
        srv = _sel_served(spec, [0, 1])
        assert srv == std, ("served:", srv, std)

    def test_a_brush_selection_names_its_observations_both_modes(self):
        spec = tp._spec([plot_for("scatter", if_expr="price > 4500")],
                        {"filter": _RANGE}, kpis=[tp._kpi(update="brush")])
        r, _ = tp._standalone(spec)
        (fig,) = r.figures.values()
        (g,) = [x for x in fig.renderers if isinstance(x, GlyphRenderer)]
        pos = _drawn_positions(g)[:2]
        _, std, _ = sfm._saved_selection(spec, 0, pos, [])
        _NODE_RUNS.append(1)
        doc, _ = tp._served(spec)
        (sfig,) = sfm._figures(doc)
        (sg,) = [x for x in sfig.renderers if isinstance(x, GlyphRenderer)]
        spos = _drawn_positions(sg)[:2]
        srv, _, _ = sfm._served_selection(spec, 0, spos, [])
        std_b, _, _ = sfm._saved_selection(spec, 0, pos, [])
        assert std_b == {"k1": "23.5"}, std_b
        assert srv == {"k1": "23.5"}, ("served:", srv)

    def test_a_qualified_card_after_a_move_both_modes(self):
        spec = _sspec(plots=[_p()], bo={"filter": _RANGE},
                      kpis=[tp._kpi(update="filter", qual_col="__dashq3")],
                      qual_col="__dashq1")
        lo, hi = 5003.0, 5010.75
        df = _sentinel_frame()
        rows = df.iloc[sorted(Q3)]
        rows = rows[(rows["price"] >= lo) & (rows["price"] <= hi)]
        want = float(rows["mpg"].mean())
        r, _, _ = _saved(spec)
        sess = js_runner.JsSession(r.filter_callbacks)
        (w,), (cb,) = r.filter_widgets, r.filter_callbacks
        sess.set(w, (lo, hi))
        sess.run(cb)
        _NODE_RUNS.append(1)
        std = sfm._cards(d.text for d in r.kpi_divs.values())
        assert abs(float(std["k1"].replace(",", "")) - want) < 1e-3, std
        doc, _ = _served(spec)
        (sw,) = tp._widgets_of(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tp._fire(sw, (lo, hi))
        srv = sfm._served_cards(doc)
        assert srv == std, ("served:", srv, std)

    def test_csv_makes_the_relabel_the_identity(self, tmp_path):
        import test_export as te
        spec = te._export_spec()
        spec["graphs"][0]["plots"][0]["in_expr"] = "2/3"
        r = te._saved(tmp_path, spec)
        sdir = tmp_path / "srv"
        sdir.mkdir()
        doc = te._served(sdir, spec)
        if isinstance(doc, tuple):
            doc = doc[0]
        for state in ({}, {"mpg": (26.0, 40.0)}):
            assert te._saved_file(r, state) == te._served_file(doc, state), \
                state
        idx = [list(s.data["index"]) for s in _sources(doc)
               if "mpg" in s.data and "index" in s.data]
        assert [1] in idx, ("served:", idx)

    def test_every_row_source_carries_an_index(self):
        frame_vars = {"mpg", "weight", "price", "foreign", "rep", "when"}
        bad = []
        for t in ("scatter", "line", "connected", "lfit", "histogram",
                  "kdensity", "rarea", "rspike", "pcspike", "area", "bar",
                  "dropline", "dot", "lpoly", "function"):
            for link in ("", "g1"):
                spec = tp._spec([plot_for(t, if_expr="price > 4500")],
                                {"filter": _RANGE, "link": link})
                doc, _ = tp._served(spec)
                # Flipped (WP-34 PIC-1): an area's outline ring is drawn
                # from its fill's source, not from rows (A-6).
                rings = {id(m.data_source) for m in doc.models
                         if "dash_area_outline" in (getattr(m, "tags", None)
                                                    or [])}
                for s in _sources(doc):
                    if id(s) in rings:
                        continue
                    if (frame_vars & set(s.data)) and "index" not in s.data:
                        bad.append((t, link, sorted(s.data)))
        assert bad == [], bad


def _drawn_positions(g):
    flt = getattr(getattr(g, "view", None), "filter", None)
    n = len(next(iter(g.data_source.data.values()), []))
    if isinstance(flt, BooleanFilter) and flt.booleans is not None:
        return [i for i, b in enumerate(flt.booleans) if b]
    if isinstance(flt, IndexFilter) and flt.indices is not None:
        return list(flt.indices)
    return list(range(n))


def _sel_saved(spec, indices):
    sp, dp = _write_inputs(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    src = r._dash_linked_source
    models = {}
    payload = {"models": models, "brush": {}, "indices": list(indices),
               "then": [], "filter": None}
    payload["brushed"] = sfm._encode(src, models)["__ref__"]
    for lst in (src.selected.js_property_callbacks or {}).values():
        for cb in (lst if isinstance(lst, list) else [lst]):
            payload["brush"].setdefault(payload["brushed"], []).append(
                {"args": sfm._encode(dict(cb.args), models), "code": cb.code})
    out = sfm._run_node(payload, sfm._SEL_RUNNER)
    return sfm._cards(out["brushed"]), sfm._cards(out["after"]), None


def _sel_served(spec, indices):
    doc, _ = _served(spec)
    shared = [s for s in _sources(doc)
              if getattr(s, "_dash_link_source", False)][0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shared.selected.indices = list(indices)
    return sfm._served_cards(doc)


# ===========================================================================
# Guards
# ===========================================================================

def _factors(models):
    out = []
    roots = list(models.roots) if isinstance(models, Document) else models
    for r in roots:
        for m in r.references():
            if isinstance(m, CategoricalColorMapper):
                out.append(list(m.factors))
    return out


def _legend_labels(models):
    out = []
    roots = list(models.roots) if isinstance(models, Document) else models
    for r in roots:
        for m in r.references():
            if isinstance(m, LegendItem):
                lab = m.label
                out.append(str(getattr(lab, "value", lab)))
    return out


_COLOR_CASES = {
    "string": lambda: _sspec(plots=[
        _p(qual="__dashq1", options={"colorvar": "name"}),
        _p(qual="__dashq2")]),
    "colorlevels": lambda: _sspec(plots=[
        _p(qual="__dashq1", options={"colorvar": "price",
                                     "colorlevels": "3"}),
        _p(qual="__dashq2")]),
    "linked": lambda: _sspec(graphs=[
        ("g1", [_p(qual="__dashq1", options={"colorvar": "name"})]),
        ("g2", [_p()], None, {"qual_col": "__dashq2"})],
        bo={"link": "g1 g2"}),
}


class TestColorvarReadsTheLayersRows:
    @pytest.mark.parametrize("case", list(_COLOR_CASES))
    def test_no_missing_key_both_modes(self, case):
        spec = _COLOR_CASES[case]()
        r, _, _ = _saved(spec)
        doc, _ = _served(spec)
        sf = _factors([r._last_layout_root])
        vf = _factors(doc)
        for fs in sf + vf:
            assert "__missing__" not in fs, (case, fs)
        for lab in _legend_labels([r._last_layout_root]) + _legend_labels(doc):
            assert "(missing)" not in lab, (case, lab)
        if case in ("string", "linked"):
            want = ["sent-%02d" % (i + 1) for i in sorted(Q1)]
            assert want in sf, (case, sf)
            assert want in vf, ("served:", case, vf)
        assert sf == vf, ("served:", case, sf, vf)


def _auto_spec(plots, **kw):
    return tp._spec(plots, **kw)


class TestWholeDataRulesStillRead:
    def test_lowess_adjust_reads_every_row(self, monkeypatch):
        t = _truth()["p6"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        spec = tp._spec([plot_for("lowess", options={"adjust": "1"})],
                        if_expr="foreign == 1")
        r, _ = tp._standalone(spec)
        (fig,) = r.figures.values()
        (g,) = [x for x in fig.renderers if isinstance(x, GlyphRenderer)]
        ys = [float(v) for v in g.data_source.data[g.glyph.y]]
        assert len(ys) == 22
        assert abs(float(np.mean(ys)) - t["mean"]) < 1e-6

    def test_lpoly_grid_follows_the_datasets_n(self, monkeypatch):
        with open(_STAT_FIXTURE, encoding="utf-8") as fh:
            est = json.load(fh)["layers"]["lpoly"]["foreign1"]["estimation"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        spec = tp._spec([plot_for("lpoly")], if_expr="foreign == 1")
        r, _ = tp._standalone(spec)
        (fig,) = r.figures.values()
        (g,) = [x for x in fig.renderers if isinstance(x, GlyphRenderer)]
        xs = [float(v) for v in g.data_source.data[g.glyph.x] if v == v]
        assert len(xs) == est["n_points"]
        assert abs(xs[-1] - est["x_at_last"]) < 1e-6

    def test_by_panels_are_twoways(self, monkeypatch):
        t = _truth()["p3"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        # dash.ado puts a lone layer's if on its graph (E-2 D1).
        one = tp._spec([plot_for("scatter")], None, {"by": "foreign"},
                       if_expr="foreign == 0")
        two = tp._spec([plot_for("scatter", if_expr="foreign == 0"),
                        plot_for("scatter", if_expr="price > 15000")], None,
                       {"by": "foreign"})
        for spec, key in ((one, "single"), (two, "two")):
            r, _ = tp._standalone(spec)
            assert len(r.figures) == len(t[key]["subtitles"]), key

    def test_missing_values_stay_selected(self, monkeypatch):
        t = _truth()["p2"]
        auto = sfm._auto().rename(columns={"rep78": "rep"})
        monkeypatch.setattr(tp, "_DF", auto)
        spec = tp._spec([plot_for("scatter", yvar="rep")],
                        if_expr="foreign == 0")
        r, _ = tp._standalone(spec)
        # twoway's serset holds the 52 domestic cars, 4 with rep78
        # missing; it draws the 48 others, and so does the page, whose
        # restriction drops no row the graph draws.
        assert t["serset_n"] == t["count_if"] == 52
        assert len(_saved_ids(r)) == t["count_nonmissing"]

    def test_a_static_card_reads_every_row_while_the_page_holds_the_graphs(
            self):
        spec = tp._spec([plot_for("scatter")], kpis=[tp._kpi()],
                        if_expr="foreign == 1")
        r, _ = tp._standalone(spec)
        card = tp._kpi_card(r.kpi_divs["k1"].text)
        assert card[1] == _truth()["p5"]["mpg_all"]["text"]
        assert len(_saved_ids(r)) == 5

    def test_a_text_in_qualifier_is_counted_on_the_whole_data(self,
                                                              monkeypatch):
        t = _truth()["p4"]
        monkeypatch.setattr(tp, "_DF", sfm._auto())
        spec = tp._spec([plot_for("scatter", in_expr="40/60")],
                        if_expr="foreign == 1")
        r, _ = tp._standalone(spec)
        (fig,) = r.figures.values()
        (g,) = [x for x in fig.renderers if isinstance(x, GlyphRenderer)]
        assert len(_drawn_positions(g)) == t["count_foreign_in_40_60"]


class TestTheCsvContract:
    def test_csv_still_embeds_every_row_both_modes(self):
        spec = _sspec(plots=[_p()], bo={"filter": _RANGE, "csv": "1"},
                      qual_col="__dashq1")
        r, page, _ = _saved(spec)
        nums, strs = _page_values(page)
        assert len(_excluded_hits(nums, strs, _sentinel_frame(), Q1)) > 0
        assert _snapshot_rows(r)["snapshot"] == 10
        doc, _ = _served(spec)
        assert any(len(s.data.get("index", [])) == 5 for s in _sources(doc))


def _help():
    with open(_HELP, encoding="utf-8") as fh:
        return " ".join(fh.read().split())


class TestTheHelpSaysSo:
    def test_the_description_says_what_a_saved_page_holds(self):
        h = _help()
        assert "{ul:What a saved page holds.}" in h
        assert "the page numbers its own rows" in h

    def test_the_old_csv_sentence_is_gone(self):
        assert "already contains those rows" not in _help()

    def test_the_filters_paragraph_names_each_empty_widget(self):
        h = _help()
        assert "greyed out" in h and "lists only All" in h

    def test_the_brush_sentence_stays(self):
        assert "then counts the rows that graph shows" in _help()

    def test_the_linking_server_and_limit_sentences(self):
        h = _help()
        assert ("That source holds the observations the group's graphs "
                "draw") in h
        assert "numbered as the saved page numbers them" in h
        # Flipped: the limit sentence is gone -- "A saved page may hold
        # fewer observations than the limit counts" described the cell
        # cap, which the maintainer removed (P4-3, WP-33 33-15).
        assert "than the limit counts" not in h
        assert "{ul:No size limit.}" in h


def test_the_node_cases_ran():
    """The node-run cases above do run: node is found (js_runner.node()
    skips, which is red under DASH_STRICT=1) and a filter script of the
    battery runs under it.  Self-contained, so it holds under xdist,
    where each worker counts only its own tests."""
    js_runner.node()
    before = len(_NODE_RUNS)
    _saved_after_move(_CASES[0][1]())
    assert len(_NODE_RUNS) > before, "no node case ran"
