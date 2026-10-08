"""A filter's widget is the data's, whatever the dashboard's graphs select.

Measured 23sep2026 at ad13a0f, in both modes and through dash.ado with the
console binary (sysuse auto):

* g1 carrying ``if price > 1000000`` (no rows) and ``filter(price,
  type(range))`` or ``type(slider)``: the saved page built NO widget and
  warned "filter 'price' type 'range' requires numeric data; skipping
  widget"; the served app built a RangeSlider (a Slider) over the data's
  3,291 to 15,906.  The same when the only graph selects no rows, and when
  g1 is a by() graph and the graph after it selects no rows.
* A dashboard of KPIs alone with any filter: the saved page built no widget
  and warned "filter(price): the variable is not in the data"; the served
  app built it, and its cards followed it.

``DashRenderer._build_filter_widgets`` judged the widget from the callback's
primary source -- the link group's, else the first one registered -- which
is one graph's rows: under that graph's own if/in, or when it is a by()
panel or the graph after one, a subset of the data, possibly empty.  An
empty column carries no numeric type (``pd.Series([])`` is object), so the
numeric test refused it; and with no graph at all there was no primary
source, so every filter was "not in the data".  The served app has always
judged from its whole frame.

Right before the fix, and held here: a date variable passed the numeric
test by accident (its empty column stays a datetime64 array); a first graph
whose rows are all missing on the filter variable kept a float column.
Since WP-29 P0.11 a widget describes the rows its targets select and a
linked group's source holds the group's rows; every shape below carries the
unqualified filter-mode card k1, so each widget's reach is every row and
the expectations are unchanged.  Each test
below also fails before the fix: its loop reaches a shape the saved page got
wrong.

The two modes are held to one answer, a date variable's included: the
served app had no date handling at all until WP-27 (BUGS.md), and each mode
was held to its own answer for a date variable until then.
"""
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (ColumnDataSource, DateRangeSlider, DateSlider,
                          DatetimeRangeSlider, Div, RangeSlider, Select,
                          Slider)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_adversarial_matrix import (_DF, _SCATTER, _kpi,  # noqa: E402
                                     _load_app, _write_inputs)
from test_filter_exclude import _encode, _node  # noqa: E402

_SEQ = itertools.count()
_WIDGETS = (Select, Slider, RangeSlider, DateSlider, DateRangeSlider,
            DatetimeRangeSlider)

# _DF's ten rows, and three variables to filter on.  `m' and `dm' are
# missing on every foreign car (rows 1, 3, 5, 7, 9), so a graph qualified
# `if foreign == 1' draws rows that are all missing on them.
_FRAME = _DF.copy()
_FRAME["m"] = [np.nan if f == 1.0 else 10.0 + i
               for i, f in enumerate(_FRAME["foreign"])]
# Stata %td: 14977 is 02jan2001; every thirty days after it.
_FRAME["dm"] = [np.nan if f == 1.0 else 14977.0 + 30 * i
                for i, f in enumerate(_FRAME["foreign"])]
_FRAME["make"] = ["car%d" % i for i in range(len(_FRAME))]
_STRINGS = ("make",)

_NO_ROWS = "price > 1000000"

# Each shape: (graphs, link).  Every one carries the same KPI, k1.
_SHAPES = {
    "unqualified": (lambda: [_graph("g1"), _graph("g2")], ""),
    "g1 selects no rows": (lambda: [_graph("g1", _NO_ROWS), _graph("g2")], ""),
    "the only graph selects no rows": (lambda: [_graph("g1", _NO_ROWS)], ""),
    "a by() graph, then one that selects no rows": (
        lambda: [_graph("g1", by="foreign"), _graph("g2", _NO_ROWS)], ""),
    "g1's rows are all missing on the variable": (
        lambda: [_graph("g1", "foreign == 1"), _graph("g2")], ""),
    "link(g1 g2), g1 selects no rows": (
        lambda: [_graph("g1", _NO_ROWS), _graph("g2")], "g1 g2"),
    "no graph, the KPI alone": (lambda: [], ""),
}

# `m' over the data: 10, 12, 14, 16, 18 -- whole numbers, so a step of 1.
_WANT_M = {
    "range": {"type": "RangeSlider", "title": "m", "disabled": False,
              "start": 10.0, "end": 18.0, "step": 1, "value": (10.0, 18.0)},
    "slider": {"type": "Slider", "title": "m \u2265", "disabled": False,
               "start": 10.0, "end": 18.0, "step": 1, "value": 10.0},
    "dropdown": {"type": "Select", "title": "m", "disabled": False,
                 "value": "__all__",
                 "options": [("__all__", "All"), (10.0, "10"), (12.0, "12"),
                             (14.0, "14"), (16.0, "16"), (18.0, "18")]},
}

# The saved page's date widgets, and `dm''s first and last dates as the
# epoch milliseconds they carry: 02jan2001 and 30aug2001.
_SAVED_DATE_TYPE = {"range": "DateRangeSlider", "slider": "DateSlider",
                    "dropdown": "Select"}
_DM_FIRST_MS = 978393600000.0
_DM_LAST_MS = 999129600000.0


# ---------------------------------------------------------------------------
# Specs, inputs, and the widgets each mode builds
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


def _graph(name, if_expr="", **go):
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": [dict(_SCATTER)], "graph_options": opts,
            "if_expr": if_expr, "in_expr": ""}


def _spec(shape, fvar, ftype):
    graphs_of, link = _SHAPES[shape]
    graphs = graphs_of()
    names = [g["graph_options"]["name"] for g in graphs] + ["k1"]
    return {"graphs": graphs, "kpis": [_kpi("filter")],
            "build_options": {
                "layout": "auto", "link": link, "theme": "", "title": "",
                "subtitle": "", "formats": {"dm": "%td"},
                "filters": [{"varname": fvar, "type": ftype}],
                "registry": " ".join(names)}}


def _inputs(tmp_path, spec):
    """spec.json and data.json for *spec* over _FRAME, `make' a string."""
    sp, dp = _write_inputs(tmp_path, spec, _FRAME)
    with open(dp, encoding="utf-8") as fh:
        data = json.load(fh)
    for key in ("variableIsString", "variableTypeIsString"):
        for col in _STRINGS:
            data["StataJSON"][key][col] = True
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _describe(w):
    d = {"type": type(w).__name__, "title": w.title,
         "disabled": bool(w.disabled)}
    for p in ("start", "end", "step"):
        if p in w.properties():
            d[p] = getattr(w, p)
    v = w.value
    d["value"] = tuple(v) if isinstance(v, (list, tuple)) else v
    if isinstance(w, Select):
        d["options"] = [tuple(o) if isinstance(o, (list, tuple)) else o
                        for o in w.options]
    return d


def _refusals(caught):
    """The warnings that say a filter got no widget."""
    return [str(c.message) for c in caught
            if "no widget was built" in str(c.message)
            or "skipping widget" in str(c.message)]


def _saved(tmp_path, spec):
    """``(widgets, refusals, renderer)`` for the saved page."""
    sp, dp = _inputs(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return [_describe(w) for w in r.filter_widgets], _refusals(caught), r


def _served(tmp_path, spec):
    """``(widgets, refusals, document)`` for one served session."""
    sp, dp = _inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "fwdata_%d" % next(_SEQ))
    doc = Document()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ns["make_document"](doc)
    widgets = [m for m in doc.select({"type": object})
               if isinstance(m, _WIDGETS)]
    return [_describe(w) for w in widgets], _refusals(caught), doc


def _both(tmp_path, shape, fvar, ftype):
    spec = _spec(shape, fvar, ftype)
    s_w, s_ref, _ = _saved(tmp_path, spec)
    v_w, v_ref, _ = _served(tmp_path, spec)
    return {"saved": s_w, "served": v_w,
            "saved refused": s_ref, "served refused": v_ref}


def _report(wrong):
    return "\n".join("%s:\n    %s" % (shape, got)
                     for shape, got in wrong.items())


# ---------------------------------------------------------------------------
# 1. The widget set, and each widget's options and range
# ---------------------------------------------------------------------------

class TestOneWidgetWhateverTheGraphsSelect:

    @pytest.mark.parametrize("ftype", ["range", "slider", "dropdown"])
    def test_a_numeric_variable(self, tmp_path, ftype):
        want = {"saved": [_WANT_M[ftype]], "served": [_WANT_M[ftype]],
                "saved refused": [], "served refused": []}
        wrong = {}
        for shape in _SHAPES:
            got = _both(tmp_path, shape, "m", ftype)
            if got != want:
                wrong[shape] = got
        assert not wrong, ("filter(m, type(%s)) wanted %s in both modes; "
                           "got\n%s" % (ftype, _WANT_M[ftype], _report(wrong)))

    @pytest.mark.parametrize("ftype", ["range", "slider", "dropdown"])
    def test_a_date_variable(self, tmp_path, ftype):
        """Both modes against the saved page's answer for the unqualified
        dashboard.  Each was held to its own until WP-27 gave the served
        app date handling (BUGS.md, "The generated server app has no date
        handling at all")."""
        want = _both(tmp_path, "unqualified", "dm", ftype)
        [saved] = want["saved"]
        assert want["served"] == want["saved"], want
        assert saved["type"] == _SAVED_DATE_TYPE[ftype]
        if ftype != "dropdown":
            assert (saved["start"], saved["end"]) == (_DM_FIRST_MS,
                                                      _DM_LAST_MS)
        assert len(want["served"]) == 1
        assert want["saved refused"] == want["served refused"] == []
        wrong = {}
        for shape in _SHAPES:
            got = _both(tmp_path, shape, "dm", ftype)
            if got != want:
                wrong[shape] = got
        assert not wrong, ("filter(dm, type(%s)) wanted %s; got\n%s"
                           % (ftype, want, _report(wrong)))

    @pytest.mark.parametrize("ftype", ["range", "slider"])
    def test_a_string_variable_is_refused_by_both(self, tmp_path, ftype):
        """Kept: a string variable gets no range or slider, and the reason
        given is its type, in both modes."""
        refusal = ["dash: filter 'make' type '%s' requires numeric data; "
                   "skipping widget (use type(dropdown) for string "
                   "columns)." % ftype]
        want = {"saved": [], "served": [],
                "saved refused": refusal, "served refused": refusal}
        wrong = {}
        for shape in _SHAPES:
            got = _both(tmp_path, shape, "make", ftype)
            if got != want:
                wrong[shape] = got
        assert not wrong, _report(wrong)


# ---------------------------------------------------------------------------
# 2. With no graph at all, the filter still recomputes the cards
# ---------------------------------------------------------------------------

# BokehJS runs a CustomJS body as a strict-mode function whose parameters are
# the args' names, then cb_obj and cb_data; this runs it under node and
# returns every Div's text as the code left it.
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
for (const [id, o] of Object.entries(REG))
  if (o.__type__ === "Div") out[id] = o.text;
process.stdout.write(JSON.stringify(out));
"""


def _div_texts_after(args, code):
    models = {}
    payload = {"models": models, "args": _encode(dict(args), models),
               "code": code}
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("const RAW = " + json.dumps(payload) + ";\n" + _RUNNER)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True,
                             text=True, timeout=120)
        assert res.returncode == 0, res.stderr[:2000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


def _card_value(text):
    m = re.search(r'id="kpi_val_k1"[^>]*>([^<]*)<', text or "")
    return m.group(1) if m else None


class TestADashboardOfKpisAlone:
    """The KPI is `mean(mpg)`, fmt %9.2f.  On _DF: price in [4000, 5000]
    keeps rows 0, 1, 3, 5, 8 (mpg 22, 17, 30, 19, 16); price >= 5000 keeps
    rows 4, 6, 7, 9 (21, 14, 28, 23); foreign == 1 keeps rows 1, 3, 5, 7, 9
    (17, 30, 19, 28, 23)."""

    @pytest.mark.parametrize("ftype, fvar, value, want", [
        ("range", "price", (4000.0, 5000.0), "20.80"),
        ("slider", "price", 5000.0, "21.50"),
        ("dropdown", "foreign", "1", "23.40"),
    ])
    def test_the_filter_recomputes_the_card_in_both_modes(
            self, tmp_path, ftype, fvar, value, want):
        spec = _spec("no graph, the KPI alone", fvar, ftype)

        _, _, r = _saved(tmp_path, spec)
        assert len(r.filter_widgets) == 1, "the saved page built no widget"
        [w], [cb] = r.filter_widgets, r.filter_callbacks
        assert cb.code == dr._FILTER_JS
        # Not null: the script writes its `source' when no graph owns it.
        assert isinstance(cb.args["source"], ColumnDataSource)
        w.value = value
        texts = _div_texts_after(cb.args, cb.code)
        saved_card = _card_value(texts.get(r.kpi_divs["k1"].id))

        _, _, doc = _served(tmp_path, spec)
        [sw] = [m for m in doc.select({"type": object})
                if isinstance(m, _WIDGETS)]
        old = sw.value
        sw.value = value
        fired = 0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # A Select recomputes on "value", a slider on "value_throttled".
            for attr in ("value", "value_throttled"):
                for scb in sw._callbacks.get(attr, []):
                    scb(attr, old, value)
                    fired += 1
        assert fired == 1
        [served_card] = [_card_value(d.text) for d in doc.select({"type": Div})
                         if _card_value(d.text) is not None]

        assert (saved_card, served_card) == (want, want)


# ---------------------------------------------------------------------------
# 3. The saved page's test of a column is the shared builder's
# ---------------------------------------------------------------------------

_COLUMNS = {
    "float": pd.Series([1.5, 2.5]),
    "int": pd.Series([1, 2]),
    "all missing": pd.Series([np.nan, np.nan]),
    "empty float": pd.Series([], dtype=float),
    "datetime": pd.Series(pd.to_datetime(["2001-01-02", None])),
    "string": pd.Series(["a", "b"]),
    "empty object": pd.Series([], dtype=object),
    "all None": pd.Series([None, None]),
}
_RANGEABLE = {"float": True, "int": True, "all missing": True,
              "empty float": True, "datetime": True, "string": False,
              "empty object": False, "all None": False}


class TestTheRangeableTest:

    @pytest.mark.parametrize("name", sorted(_COLUMNS))
    def test_it_reads_the_columns_type(self, name):
        assert dr._dash_filter_rangeable(_COLUMNS[name]) is _RANGEABLE[name]

    @pytest.mark.parametrize("ftype", ["range", "slider"])
    def test_it_is_the_test_the_builder_both_modes_run_applies(self, ftype):
        """_dash_filter_widget gives no widget exactly where the saved page
        refuses one, so the two modes refuse the same variables."""
        for name, col in _COLUMNS.items():
            built = dr._dash_filter_widget(ftype, "v", col, "v")[0]
            assert (built is not None) is dr._dash_filter_rangeable(col), name
