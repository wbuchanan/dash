"""test_help_claims_4.py -- dash.sthlp's KPI Cards and Server Mode sections
(WP-23, AC-23.1), held to what Stata computes and what both render modes do.

Every expected number here is Stata's own, read from
``test/fixtures/kpi_pctile_truth.json``; each entry there records the Stata
command that produced it.  Both render modes are measured: the saved page
(``DashRenderer``; its filter and brush callbacks are the JavaScript the page
ships, run under node exactly as attached) and the served app
(``ServerAppBuilder``'s generated source, loaded and given a bokeh Document).

What was measured at 4ede074 before these tests were written:

* ``dash kpi p97.5(price)`` stopped with r(198) although the help promised
  p97.5 (dash.ado; the Stata side is test_help_claims_4.cscript).
* Stata's ``_pctile`` treats n*p/100 as an integer when it is within a
  RELATIVE 1e-15 of one; both renderers used an ABSOLUTE 1e-12.  Measured over
  1,643,898 (n, p) cases, the old rule disagreed with Stata on 1,947 of the
  one- and two-decimal percentiles at n = 10,000 to 1,000,000 -- p81.93 of
  x = 1..10000 read 8194 in both modes where Stata reads 8193.5.
* The saved page's brush callback threw ``ReferenceError: kpi_config is not
  defined`` on every selection, so no ``update(brush)`` or ``update(both)``
  card ever followed a brush on a saved page; the one test of it defined
  ``kpi_config`` in its own harness.
* A percentile of a date variable other than p25, p50 and p75 was printed on
  the saved page as epoch milliseconds (``1.58622e+12``).
* A served card with its own ``in`` range took the first rows of the FILTERED
  frame after a filter move or a brush, not the observations the range names.
* An empty or one-row selection showed ``0`` on the saved page where Stata
  (and the served app) show missing, and an empty ``sum`` showed missing in
  both modes' Python where Stata shows 0.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from itertools import count

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Div, RangeSlider, Select, Slider

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.model import Model  # noqa: E402
from bokeh.models import BooleanFilter, ColumnDataSource  # noqa: E402
from test_adversarial_matrix import _load_app, _write_inputs  # noqa: E402
from test_filter_exclude import _node  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "kpi_pctile_truth.json")
_SEQ = count()


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _auto(truth):
    """sysuse auto's price, mpg, weight, foreign and rep78, as Stata holds
    them (rep78 has five missing values)."""
    return pd.DataFrame({
        k: [np.nan if v is None else float(v) for v in vals]
        for k, vals in truth["auto"].items()})


# ===========================================================================
# Running each render mode
# ===========================================================================

# BokehJS runs a CustomJS body as a strict-mode function whose parameters are
# the args' names, then cb_obj and cb_data.  This runs the body so, with the
# args' Bokeh models replaced by stand-ins (test_filter_exclude._encode), and
# reports the text every Div was left holding.
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
  ...names.map((n) => args[n]), RAW.cb_obj, {});
const out = {divs: {}, sources: {}};
for (const [id, o] of Object.entries(REG)) {
  if (o.__type__ === "Div") out.divs[id] = o.text;
  if (o.__type__ === "ColumnDataSource") out.sources[id] = o.data;
}
process.stdout.write(JSON.stringify(out));
"""


def _plain(v):
    """One value as BokehJS receives it: a datetime is epoch milliseconds,
    a missing number null."""
    if isinstance(v, (np.datetime64, pd.Timestamp)):
        v = pd.Timestamp(v)
        return None if pd.isna(v) else v.value / 1e6
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return None if math.isnan(v) else v
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _encode(v, models):
    """*v* as JSON, each Bokeh model replaced by a reference to ONE stand-in
    (test_filter_exclude's scheme, with datetimes as BokehJS holds them)."""
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


def _run_js(args, code, cb_obj=None):
    """``{Div model id: text}`` after *code* ran with *args* under node."""
    return _run_js_full(args, code, cb_obj)["divs"]


def _run_js_full(args, code, cb_obj=None):
    """``{"divs": {id: text}, "sources": {id: data}}`` after *code* ran."""
    models = {}
    payload = {"models": models, "args": _encode(dict(args), models),
               "code": code, "cb_obj": cb_obj}
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("const RAW = " + json.dumps(payload) + ";\n" + _RUNNER)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True, text=True,
                             timeout=300)
        assert res.returncode == 0, (
            "the page's own callback failed under node:\n" + res.stderr[:1500])
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


_CARD_VALUE = re.compile(r'id="kpi_val_([^"]*)"[^>]*>([^<]*)<')


def _card(text):
    """``(name, value text)`` of one KPI card's HTML."""
    m = _CARD_VALUE.search(text or "")
    assert m, "no KPI value in the card: %r" % (text or "")[:300]
    return m.group(1), m.group(2)


def _cards(texts):
    out = {}
    for t in texts:
        if 'id="kpi_val_' in (t or ""):
            name, val = _card(t)
            out[name] = val
    return out


def _saved(tmp_path, spec, df):
    sp, dp = _write_inputs(tmp_path, spec, df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        r.render()
    return r


def _saved_filter_move(r, index, value):
    """The cards after filter *index* moves to *value*, by the page's own
    filter callback."""
    w = r.filter_widgets[index]
    cb = r.filter_callbacks[index]
    assert cb.code == dr._FILTER_JS
    old = w.value
    w.value = value
    try:
        texts = _run_js(cb.args, cb.code)
    finally:
        w.value = old
    return _cards(texts.values())


def _brush_callbacks(src):
    out = []
    for lst in (src.selected.js_property_callbacks or {}).values():
        out.extend(lst if isinstance(lst, list) else [lst])
    return out


def _saved_brush(r, graph, indices):
    """The cards after rows *indices* of *graph*'s source are selected, by
    the callback the page attached to that source's selection."""
    cbs = _brush_callbacks(r.sources[graph])
    assert len(cbs) == 1, "expected one selection callback, got %d" % len(cbs)
    texts = _run_js(cbs[0].args, cbs[0].code,
                    cb_obj={"indices": list(indices)})
    return _cards(texts.values())


def _served_app(tmp_path, spec, df):
    sp, dp = _write_inputs(tmp_path, spec, df)
    op = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        return _load_app(fh.read(), "hc4_%d" % next(_SEQ))


def _served_session(ns):
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _served_cards(doc):
    return _cards(d.text for d in doc.select({"type": Div}))


def _served_widget(doc, varname):
    ws = [w for w in doc.select({"type": Select})]
    ws += [w for w in doc.select({"type": RangeSlider})]
    ws += [w for w in doc.select({"type": Slider})]
    hit = [w for w in ws if getattr(w, "_dash_var", None) == varname]
    assert len(hit) == 1, "no single widget for %s" % varname
    return hit[0]


def _served_filter_move(ns, varname, value):
    """A fresh session's cards after the widget over *varname* moves."""
    doc = _served_session(ns)
    w = _served_widget(doc, varname)
    old = w.value
    fired = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w.value = value
        # A Select recomputes on "value", a slider on "value_throttled".
        for attr in ("value", "value_throttled"):
            for cb in w._callbacks.get(attr, []):
                cb(attr, old, value)
                fired += 1
    assert fired == 1, "expected one recompute callback, fired %d" % fired
    return _served_cards(doc)


def _served_brush(ns, indices):
    """A fresh session's cards after rows *indices* of the one brushable
    source are selected."""
    doc = _served_session(ns)
    srcs = [s for s in doc.select({"type": dr.ColumnDataSource})
            if "index" in s.data and s.selected._callbacks.get("indices")]
    assert len(srcs) == 1, "expected one brushable source, got %d" % len(srcs)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        srcs[0].selected.indices = list(indices)
    return _served_cards(doc)


# ===========================================================================
# 1. Stata's percentile rule, one order statistic at a time
# ===========================================================================

class _Identity:
    """x = 1..n without the array: _stata_percentile only indexes it."""

    def __init__(self, n):
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        if i < 0:
            i += self.n
        assert 0 <= i < self.n
        return float(i + 1)


def _old_rule(n, p):
    """The rule both renderers used before WP-23: an ABSOLUTE 1e-12."""
    i = n * p / 100.0
    if abs(i - round(i)) < 1e-12:
        k = int(round(i))
        return float(n) if k >= n else 1.0 if k <= 0 else k + 0.5
    return float(min(max(math.ceil(i), 1), n))


class TestStataPercentileRule:
    """_pctile on x = 1..n names the order statistic it takes: an integer j
    is x_(j), j + 0.5 the mean of x_(j) and x_(j+1)."""

    def test_the_cases_include_ones_the_old_rule_got_wrong(self, truth):
        """Guards the two tests below against a fixture that cannot fail."""
        bad = [c for c in truth["rule_cases"]
               if _old_rule(c[0], float(c[1])) != float(c[2])]
        assert len(bad) >= 1900, len(bad)

    def test_python_takes_statas_order_statistic(self, truth):
        bad = []
        for n, p, want in truth["rule_cases"]:
            got = dr._stata_percentile(_Identity(n), float(p))
            if got != float(want):
                bad.append((n, p, want, got))
        assert not bad, (
            "%d of %d cases differ from Stata's _pctile, e.g. %s"
            % (len(bad), len(truth["rule_cases"]), bad[:8]))

    def test_the_saved_pages_javascript_takes_statas_order_statistic(
            self, truth):
        js = dr._FILTER_JS
        fn = js[js.index("function dash_pctl("):
                js.index("// Stata's kernels ([R] kdensity)")]
        cases = [[n, p, float(w)] for n, p, w in truth["rule_cases"]]
        code = (fn + "\nconst CASES = " + json.dumps(cases) + ";\n"
                "const bad = [];\n"
                "for (const [n, p, want] of CASES) {\n"
                "  const x = new Proxy({}, {get: (t, k) => k === 'length' ?"
                " n : Number(k) + 1});\n"
                "  const got = dash_pctl(x, parseFloat(p));\n"
                "  if (got !== want) bad.push([n, p, want, got]);\n"
                "}\n"
                "process.stdout.write(JSON.stringify(bad));\n")
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(code)
            path = fh.name
        try:
            res = subprocess.run([_node(), path], capture_output=True,
                                 text=True, timeout=300)
        finally:
            os.unlink(path)
        assert res.returncode == 0, res.stderr[:1500]
        bad = json.loads(res.stdout)
        assert not bad, (
            "%d of %d cases differ from Stata's _pctile, e.g. %s"
            % (len(bad), len(cases), bad[:8]))

    def test_the_served_app_carries_the_same_rule(self, tmp_path, truth):
        """The app copies _stata_percentile by source; run its copy."""
        spec = _kpi_spec("price", "none", ["p97.5"])
        ns = _served_app(tmp_path, spec, _auto(truth))
        fn = ns["_stata_percentile"]
        bad = [(n, p, w) for n, p, w in truth["rule_cases"]
               if fn(_Identity(n), float(p)) != float(w)]
        assert not bad, bad[:8]


# ===========================================================================
# 2. Every statistic the table lists, and fractional percentiles, against
#    Stata -- initially, after each filter type moves, after a brush, with
#    the KPI's own if and in, in both modes
# ===========================================================================

_TABLE = ["mean", "sum", "count", "dcount", "min", "max", "median", "sd",
          "var", "cv", "iqr", "skewness", "p25", "p50", "p75"]
_FRACTIONAL = ["p0.5", "p2.5", "p10", "p12.5", "p33.3", "p66.7", "p90",
               "p97.5", "p99.5", "p99.9", "p0.001"]
_STATS = _TABLE + _FRACTIONAL

#: One filter of each type, and the value each is moved to.
_FILTERS = [{"varname": "foreign", "type": "dropdown"},
            {"varname": "weight", "type": "range"},
            {"varname": "mpg", "type": "slider"}]
_MOVES = {"dropdown": (0, "foreign", "1"),
          "range": (1, "weight", (2000.0, 3500.0)),
          "slider": (2, "mpg", 22.0)}

#: A KPI's own qualifier: (if, in).
_VARIANTS = {"none": ("", ""), "f1": ("foreign==1", ""),
             "f0": ("foreign==0", ""), "in50": ("", "1/50"),
             "in1": ("", "1/1")}

#: fixture scope -> (the KPI's qualifier, the filter moved, rows brushed).
#: A filter keeps what Stata's qualifier in the fixture names: foreign==1,
#: inrange(weight, 2000, 3500), mpg >= 22; a brush of the first 30 rows is
#: `in 1/30'.
_SCOPES = {
    "all": ("none", None, None),
    "f1": ("f1", None, None),
    "f0": ("f0", None, None),
    "in50": ("in50", None, None),
    "dd": ("none", "dropdown", None),
    "rng": ("none", "range", None),
    "sld": ("none", "slider", None),
    "f0rng": ("f0", "range", None),
    "in50sld": ("in50", "slider", None),
    "in30": ("none", None, 30),
    "f1in30": ("f1", None, 30),
    "empty": ("f0", "dropdown", None),
    "one": ("in1", "slider", None),
}
_FIXTURE_SCOPE = {"dd": "f1"}


def _kname(stat):
    return "k_" + stat.replace(".", "_")


def _kpi_spec(var, variant, stats, update="both", filters=None):
    if_expr, in_expr = _VARIANTS[variant]
    kpis = [{"name": _kname(s), "stat": s, "var": var, "fmt": "%20.10f",
             "title": "T", "subtitle": "S", "color": "", "bgcolor": "",
             "update": update, "if_expr": if_expr, "in_expr": in_expr}
            for s in stats]
    return {
        "graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                               "xvar": "weight", "options": {}}],
                    "graph_options": {"name": "g1", "title": "g1"},
                    "if_expr": "", "in_expr": ""}],
        "kpis": kpis,
        "build_options": {
            "layout": "auto", "link": "", "theme": "", "title": "",
            "subtitle": "",
            "filters": list(_FILTERS if filters is None else filters),
            "registry": "g1 " + " ".join(k["name"] for k in kpis)}}


def _stata_value(truth, var, scope, stat):
    sc = _FIXTURE_SCOPE.get(scope, scope)
    hit = [e for e in truth["auto_kpi"]
           if e["var"] == var and e["scope"] == sc and e["stat"] == stat]
    assert len(hit) == 1, (var, sc, stat)
    return hit[0]["value"]


def _agrees(text, want):
    """A card's text against Stata's value: a missing value is '.'."""
    if want is None:
        return text == "."
    try:
        got = float(text.replace(",", ""))
    except ValueError:
        return False
    return math.isclose(got, float(want), rel_tol=1e-9, abs_tol=1e-9)


_BUILT = {}
_RESULTS = {}


def _results(mode, var, variant, action, truth, tmp_path_factory):
    """Every card of one dashboard -- one KPI per statistic, all with the
    same qualifier -- after *action*: None (as it opens), a filter move's
    name, or a number of leading rows brushed.  The dashboard is built once
    per mode, variable and qualifier; each action runs on its own."""
    key = (mode, var, variant)
    if key not in _BUILT:
        tmp = tmp_path_factory.mktemp("hc4_%s_%s_%s" % key)
        spec = _kpi_spec(var, variant, _STATS)
        _BUILT[key] = (_saved(tmp, spec, _auto(truth)) if mode == "saved"
                       else _served_app(tmp, spec, _auto(truth)))
    obj = _BUILT[key]
    rkey = key + (action,)
    if rkey not in _RESULTS:
        if mode == "saved":
            if action is None:
                out = _cards(d.text for d in obj.kpi_divs.values())
            elif isinstance(action, int):
                out = _saved_brush(obj, "g1", range(action))
            else:
                out = _saved_filter_move(obj, _MOVES[action][0],
                                         _MOVES[action][2])
        else:
            if action is None:
                out = _served_cards(_served_session(obj))
            elif isinstance(action, int):
                out = _served_brush(obj, range(action))
            else:
                out = _served_filter_move(obj, _MOVES[action][1],
                                          _MOVES[action][2])
        _RESULTS[rkey] = out
    return _RESULTS[rkey]


_CASES = [(mode, var, scope) for mode in ("saved", "served")
          for var in ("price", "mpg", "rep78") for scope in _SCOPES]


class TestEveryStatisticIsStatas:
    """dash.sthlp's statistic table, its percentile sentence and its
    Syntax line ([if] [in]) against Stata, in both modes.  price and mpg are
    whole numbers, as Stata stores them; rep78 carries five missing values,
    which is what makes count "non-missing" and dcount "distinct"."""

    @pytest.mark.parametrize("mode, var, scope", _CASES,
                             ids=["-".join(c) for c in _CASES])
    def test_every_card(self, mode, var, scope, truth, tmp_path_factory):
        variant, move, brush = _SCOPES[scope]
        cards = _results(mode, var, variant, move if move else brush, truth,
                         tmp_path_factory)
        bad = []
        for stat in _STATS:
            want = _stata_value(truth, var, scope, stat)
            got = cards.get(_kname(stat))
            if got is None or not _agrees(got, want):
                bad.append("%s: card %r, Stata %r" % (stat, got, want))
        assert not bad, "%s %s(%s) %s:\n  %s" % (
            mode, var, scope, _SCOPES[scope], "\n  ".join(bad))


# ===========================================================================
# 3. The percentile rule where it matters: 10,000 rows, each filter type
# ===========================================================================

_BIG_FILTERS = [{"varname": "g", "type": "dropdown"},
                {"varname": "x", "type": "range"},
                {"varname": "x", "type": "slider"}]
#: fixture scope -> (filter index, value): g == 0; x in 1..10000; x >= 10001.
_BIG_MOVES = {"g0": (0, "0"), "rng": (1, (1.0, 10000.0)),
              "sld": (2, 10001.0)}
_BIG_STATS = ["p81.93", "p81.96", "p64.4", "p16.1", "p97.5", "p0.07"]


def _big_spec(filters):
    kpis = [{"name": _kname(s), "stat": s, "var": "x", "fmt": "%20.10f",
             "title": "T", "update": "filter"} for s in _BIG_STATS]
    return {
        "graphs": [{"plots": [{"type": "scatter", "yvar": "x", "xvar": "g",
                               "options": {}}],
                    "graph_options": {"name": "g1"}, "if_expr": "",
                    "in_expr": ""}],
        "kpis": kpis,
        "build_options": {"layout": "auto", "link": "", "theme": "",
                          "title": "", "subtitle": "", "filters": filters,
                          "registry": "g1 " + " ".join(
                              k["name"] for k in kpis)}}


def _big_df(truth):
    n = truth["big"]["n"]
    x = np.arange(1, n + 1, dtype=float)
    return pd.DataFrame({"x": x, "g": (x > 10000).astype(float)})


def _big_want(truth, scope):
    return {e["stat"]: e["value"] for e in truth["big"]["values"]
            if e["scope"] == scope}


class TestAFractionalPercentileOfTenThousandRows:
    """x = 1..20000.  p81.93 of the first 10,000 is (x_8193 + x_8194)/2 in
    Stata; the absolute 1e-12 rule read n*p/100 = 8193.0000000000018 as not
    an integer and took x_8194, in both modes, on every filter type."""

    def test_the_saved_page_opens_on_statas_values(self, tmp_path, truth):
        r = _saved(tmp_path, _big_spec([]), _big_df(truth))
        got = _cards(d.text for d in r.kpi_divs.values())
        self._check(got, _big_want(truth, "all"), "saved, as it opens")

    def test_the_served_app_opens_on_statas_values(self, tmp_path, truth):
        ns = _served_app(tmp_path, _big_spec([]), _big_df(truth))
        got = _served_cards(_served_session(ns))
        self._check(got, _big_want(truth, "all"), "served, as it opens")

    @pytest.mark.parametrize("scope", sorted(_BIG_MOVES))
    def test_the_saved_page_after_each_filter_type(self, tmp_path, truth,
                                                   scope):
        i, value = _BIG_MOVES[scope]
        r = _saved(tmp_path, _big_spec([_BIG_FILTERS[i]]), _big_df(truth))
        got = _saved_filter_move(r, 0, value)
        self._check(got, _big_want(truth, scope), "saved, " + scope)

    @pytest.mark.parametrize("scope", sorted(_BIG_MOVES))
    def test_the_served_app_after_each_filter_type(self, tmp_path, truth,
                                                   scope):
        i, value = _BIG_MOVES[scope]
        ns = _served_app(tmp_path, _big_spec([_BIG_FILTERS[i]]),
                         _big_df(truth))
        got = _served_filter_move(ns, _BIG_FILTERS[i]["varname"], value)
        self._check(got, _big_want(truth, scope), "served, " + scope)

    @staticmethod
    def _check(got, want, where):
        bad = ["%s: card %r, Stata %r" % (s, got.get(_kname(s)), want[s])
               for s in _BIG_STATS
               if not _agrees(got.get(_kname(s), ""), want[s])]
        assert not bad, where + ":\n  " + "\n  ".join(bad)


# ===========================================================================
# 4. A percentile of a date is a date
# ===========================================================================

def _date_spec(stats, filters=()):
    kpis = [{"name": _kname(s), "stat": s, "var": "date", "fmt": "",
             "title": "T", "update": "filter"} for s in stats]
    return {
        "graphs": [{"plots": [{"type": "scatter", "yvar": "v",
                               "xvar": "date", "options": {}}],
                    "graph_options": {"name": "g1"}, "if_expr": "",
                    "in_expr": ""}],
        "kpis": kpis,
        "build_options": {"layout": "auto", "link": "", "theme": "",
                          "title": "", "subtitle": "",
                          "filters": list(filters),
                          "formats": {"date": "%td", "v": "%9.0g"},
                          "registry": "g1 " + " ".join(
                              k["name"] for k in kpis)}}


def _date_df(truth):
    d = truth["dates"]
    days = np.arange(d["first"], d["first"] + d["n"], dtype=float)
    return pd.DataFrame({"date": days, "v": np.arange(d["n"], dtype=float)})


_DATE_STATS = ["p10", "p97.5", "p0.5", "p50", "median", "min", "max"]


def _as_page_date(stata_days):
    """Stata's day number as ``display %td`` writes it, the text every card
    now shows (WP-28 section 11, GAPS2 E1; the page wrote 02 Jan 2001)."""
    return dr._dash_fmt_text(float(stata_days), "%td")


class TestAPercentileOfADateIsADate:
    """p25, p50 and p75 of a %td variable were drawn as dates and every
    other percentile as epoch milliseconds (p97.5 read 1.58622e+12)."""

    def test_the_saved_page_opens_on_the_dates_stata_computes(self,
                                                              tmp_path,
                                                              truth):
        r = _saved(tmp_path, _date_spec(_DATE_STATS), _date_df(truth))
        got = _cards(d.text for d in r.kpi_divs.values())
        want = {e["stat"]: _as_page_date(e["value"])
                for e in truth["dates"]["values"]}
        bad = ["%s: card %r, Stata %s" % (s, got.get(_kname(s)), want[s])
               for s in _DATE_STATS if got.get(_kname(s)) != want[s]]
        assert not bad, "\n  ".join(bad)

    def test_the_saved_page_keeps_them_dates_after_a_filter_moves(
            self, tmp_path, truth):
        """The slider at its lowest value keeps every row, so the values are
        the unfiltered ones and only the rendering is under test."""
        filt = [{"varname": "v", "type": "slider"}]
        r = _saved(tmp_path, _date_spec(_DATE_STATS, filt), _date_df(truth))
        got = _saved_filter_move(r, 0, 0.0)
        want = {e["stat"]: _as_page_date(e["value"])
                for e in truth["dates"]["values"]}
        bad = ["%s: card %r, Stata %s" % (s, got.get(_kname(s)), want[s])
               for s in _DATE_STATS if got.get(_kname(s)) != want[s]]
        assert not bad, "\n  ".join(bad)

    def test_the_served_app_shows_the_dates_stata_computes(self, tmp_path,
                                                           truth):
        """The served app writes each date statistic as the saved page
        does.  It showed Stata's day number until WP-27 (BUGS.md, "The
        generated server app has no date handling at all"), which the
        help listed as a server-mode limitation."""
        ns = _served_app(tmp_path, _date_spec(_DATE_STATS), _date_df(truth))
        got = _served_cards(_served_session(ns))
        want = {e["stat"]: _as_page_date(e["value"])
                for e in truth["dates"]["values"]}
        bad = ["%s: card %r, Stata %s" % (s, got.get(_kname(s)), want[s])
               for s in _DATE_STATS if got.get(_kname(s)) != want[s]]
        assert not bad, "\n  ".join(bad)


# ===========================================================================
# 5. update() and exclude(), in both modes
# ===========================================================================

def _modes_spec(exclude=()):
    kpis = [{"name": "kf", "stat": "p97.5", "var": "price",
             "fmt": "%20.10f", "title": "F", "update": "filter"},
            {"name": "kb", "stat": "p97.5", "var": "price",
             "fmt": "%20.10f", "title": "B", "update": "brush"},
            {"name": "kfb", "stat": "p97.5", "var": "price",
             "fmt": "%20.10f", "title": "FB", "update": "both"}]
    filt = dict(_FILTERS[1], exclude=list(exclude))
    return {
        "graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                               "xvar": "weight", "options": {}}],
                    "graph_options": {"name": "g1"}, "if_expr": "",
                    "in_expr": ""}],
        "kpis": kpis,
        "build_options": {"layout": "auto", "link": "", "theme": "",
                          "title": "", "subtitle": "", "filters": [filt],
                          "registry": "g1 kf kb kfb"}}


class TestTheUpdateModes:
    """update(filter) follows the filters and not the brush, update(brush)
    the brush and not the filters, update(both) both (dash.sthlp, Update
    modes) -- here with the p97.5 the help promises."""

    @staticmethod
    def _want(truth):
        return {s: _stata_value(truth, "price", s, "p97.5")
                for s in ("all", "rng", "in30")}

    def test_the_saved_page(self, tmp_path, truth):
        r = _saved(tmp_path, _modes_spec(), _auto(truth))
        moved = _saved_filter_move(r, 0, _MOVES["range"][2])
        brushed = _saved_brush(r, "g1", range(30))
        self._check(moved, brushed, self._want(truth))

    def test_the_served_app(self, tmp_path, truth):
        ns = _served_app(tmp_path, _modes_spec(), _auto(truth))
        moved = _served_filter_move(ns, "weight", _MOVES["range"][2])
        brushed = _served_brush(ns, range(30))
        self._check(moved, brushed, self._want(truth))

    @staticmethod
    def _check(moved, brushed, w):
        got = {("filter", "kf"): moved.get("kf"),
               ("filter", "kfb"): moved.get("kfb"),
               ("brush", "kb"): brushed.get("kb"),
               ("brush", "kfb"): brushed.get("kfb")}
        want = {("filter", "kf"): w["rng"], ("filter", "kfb"): w["rng"],
                ("brush", "kb"): w["in30"], ("brush", "kfb"): w["in30"]}
        bad = ["%s after a %s: card %r, Stata %r" % (k[1], k[0], got[k],
                                                     want[k])
               for k in want if not _agrees(got[k] or "", want[k])]
        # The card a callback must leave alone is either not rebuilt at all
        # or still shows its opening value, Stata's unfiltered one.
        for action, cards, k in (("filter", moved, "kb"),
                                 ("brush", brushed, "kf")):
            if k in cards and not _agrees(cards[k], w["all"]):
                bad.append("%s changed on a %s: %r" % (k, action, cards[k]))
        assert not bad, "\n  ".join(bad)


#: fmt() values a card may take, each a format dash kpi accepts.
_FORMATS = ["", "%9.0g", "%9.2f", "%12.0fc", "%12.2fc", "%8.0f", "%10.3e",
            "%9.2g", "%9.3gc", "%-9.2f", "%09.2f", "%12.1e", "%10.4g",
            # WP-28 section 11 (GAPS2 E1): the European and grouped forms
            # and %w.0g, which read 6e+03 at %10.0g, and the %t pictures.
            "%9,2fc", "%10.0g", "%12,0gc", "%tdCCYY-NN-DD", "%tm"]

#: The %t formats a card on a DATE variable takes (its own is %td).
_DATE_FORMATS = ["", "%td", "%tdCCYY-NN-DD", "%tdMonth_DD,_CCYY", "%tm",
                 "%9.2f", "%10.0g"]


class TestACardKeepsItsFormatWhenAFilterMoves:
    """fmt() takes a numeric Stata display format, and the card keeps it:
    the page's recompute wrote %10.3e 6.165e+03 as 6165, %9.2g 6.2e+03 as
    6165 and %-9.2f 6165.26 as 6165 (it knew %w.df alone), and with no
    fmt() wrote 456229000 where the card opened on 4.56229e+08.  A slider
    at its lowest value keeps every row, so only the writing is tested."""

    @staticmethod
    def _spec(var):
        kpis = [{"name": "k%d" % i, "stat": st, "var": var, "fmt": f,
                 "title": "T", "update": "filter"}
                for i, (f, st) in enumerate(
                    [(f, st) for f in _FORMATS
                     for st in ("mean", "sum", "min")])]
        return {"graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "weight", "options": {}}],
                            "graph_options": {"name": "g1"},
                            "if_expr": "", "in_expr": ""}],
                "kpis": kpis,
                "build_options": {"layout": "auto", "link": "", "theme": "",
                                  "title": "", "subtitle": "",
                                  "filters": [{"varname": "mpg",
                                               "type": "slider"}],
                                  "registry": "g1 " + " ".join(
                                      k["name"] for k in kpis)}}

    @pytest.mark.parametrize("var", ["price", "big", "small", "neg"])
    def test_the_saved_page(self, tmp_path, truth, var):
        df = _auto(truth)
        df["big"] = df["price"] * 1000.0
        df["small"] = df["price"] / 1e7
        df["neg"] = -df["price"] / 7.0
        spec = self._spec(var)
        r = _saved(tmp_path, spec, df)
        opened = _cards(d.text for d in r.kpi_divs.values())
        moved = _saved_filter_move(r, 0, float(df["mpg"].min()))
        names = {k["name"]: (k["fmt"], k["stat"]) for k in spec["kpis"]}
        bad = ["%s %s: opened %r, after the move %r" % (names[k][0] or '""',
                                                        names[k][1],
                                                        opened[k], moved[k])
               for k in names if opened[k] != moved.get(k)]
        assert not bad, "\n  ".join(bad)
        # And each is the writer's text of the statistic (WP-28 section
        # 11): %10.0g of 6165.2567 opened on 6e+03 and kept it.
        col = df[var].dropna()
        stat = {"mean": col.mean(), "sum": col.sum(), "min": col.min()}
        bad = ["%s %s: %r, the writer %r" % (f or '""', st, opened[k], w)
               for k, (f, st) in names.items()
               for w in [dr._dash_fmt_text(stat[st], f or "%9.0g")]
               if opened[k] != w]
        assert not bad, "\n  ".join(bad)

    def test_a_date_variable(self, tmp_path, truth):
        """A date statistic of a %td variable keeps fmt()'s picture, or
        the variable's own %td, after the move (WP-28 section 11)."""
        df = _auto(truth)
        df["when"] = np.arange(14611, 14611 + len(df), dtype=float)
        kpis = [{"name": "k%d" % i, "stat": st, "var": "when", "fmt": f,
                 "title": "T", "update": "filter"}
                for i, (f, st) in enumerate(
                    [(f, st) for f in _DATE_FORMATS
                     for st in ("max", "median", "count")])]
        spec = self._spec("when")
        spec["kpis"] = kpis
        spec["build_options"]["formats"] = {"when": "%td"}
        spec["build_options"]["registry"] = "g1 " + " ".join(
            k["name"] for k in kpis)
        r = _saved(tmp_path, spec, df)
        opened = _cards(d.text for d in r.kpi_divs.values())
        moved = _saved_filter_move(r, 0, float(df["mpg"].min()))
        stat = {"max": df["when"].max(), "median": df["when"].median(),
                "count": float(df["when"].count())}
        bad = []
        for k in kpis:
            f = k["fmt"] or ("%td" if k["stat"] != "count" else "%9.0g")
            w = dr._dash_fmt_text(stat[k["stat"]], f)
            if not (opened[k["name"]] == moved.get(k["name"]) == w):
                bad.append("%s %s: opened %r, moved %r, the writer %r" % (
                    k["fmt"] or '""', k["stat"], opened[k["name"]],
                    moved.get(k["name"]), w))
        assert not bad, "\n  ".join(bad)


class TestAHandEditedStatistic:
    """The spec is a file, and a hand-edited one may name any statistic.
    Arabic-Indic digits are digits to Python's \\d and float(), not to the
    page's JavaScript: the saved card opened on a p97.5 computed from them
    and the recompute found no statistic.  Neither mode reads them now, and
    a statistic of 100,000 digits costs neither mode anything."""

    @staticmethod
    def _spec(stat):
        spec = _kpi_spec("price", "none", [], filters=[_FILTERS[1]])
        spec["kpis"] = [{"name": "k1", "stat": stat, "var": "price",
                         "fmt": "%9.0f", "title": "T", "display": "",
                         "update": "filter"}]
        spec["build_options"]["registry"] = "g1 k1"
        return spec

    def test_other_digits_are_no_percentile_in_either_mode(self, tmp_path,
                                                          truth):
        stat = "p٩٧.٥"          # p97.5 in Arabic-Indic digits
        assert dr._dash_kpi_pctile(stat) is None
        with pytest.raises(ValueError):
            dr.DashRenderer._kpi_statistic(_auto(truth)["price"], stat)
        r = _saved(tmp_path, self._spec(stat), _auto(truth))
        opened = _cards(d.text for d in r.kpi_divs.values())["k1"]
        assert opened != "14500"
        moved = _saved_filter_move(r, 0, _MOVES["range"][2])["k1"]
        assert moved == "."
        ns = _served_app(tmp_path, self._spec(stat), _auto(truth))
        assert _served_cards(_served_session(ns))["k1"] == "."

    def test_a_huge_digit_run_is_cheap_in_both_modes(self, tmp_path, truth):
        for stat in ("p" + "9" * 100000, "p1." + "9" * 100000):
            t0 = time.time()
            r = _saved(tmp_path, self._spec(stat), _auto(truth))
            _saved_filter_move(r, 0, _MOVES["range"][2])
            ns = _served_app(tmp_path, self._spec(stat), _auto(truth))
            _served_session(ns)
            assert time.time() - t0 < 60, stat[:12]


class TestTheCardLayout:
    """title() is displayed above the value and subtitle() below it,
    smaller; color() colours the value and bgcolor() the card, a Stata
    colour name meaning Stata's colour (test/fixtures/color_truth.json:
    navy #1a476f, maroon #90353b, gs14 #e0e0e0) -- in both modes, as the
    page opens and after a filter move rebuilds the card."""

    _KPI = {"name": "k1", "stat": "p97.5", "var": "price", "fmt": "%9.0f",
            "title": "The title", "subtitle": "The subtitle",
            "color": "navy", "bgcolor": "gs14", "update": "filter"}

    @staticmethod
    def _truth_hex(name):
        with open(os.path.join(_HERE, "fixtures", "color_truth.json"),
                  encoding="utf-8") as fh:
            return json.load(fh)["colors"][name]["hex"].lower()

    def _check(self, html, where):
        t = html.find(">The title<")
        v = html.find('id="kpi_val_k1"')
        s = html.find(">The subtitle<")
        assert 0 <= t < v < s, "%s: title %d, value %d, subtitle %d" % (
            where, t, v, s)
        sizes = [int(x) for x in re.findall(r"font-size:(\d+)px", html)]
        assert len(sizes) == 3 and sizes[2] < sizes[1], (where, sizes)
        value_style = re.search(r'id="kpi_val_k1" style="([^"]*)"',
                                html).group(1).lower()
        assert "color:" + self._truth_hex("navy") in value_style.replace(
            " ", ""), (where, value_style)
        card_style = re.search(r'class="db-kpi-card" style="([^"]*)"',
                               html).group(1).lower().replace(" ", "")
        assert "background:" + self._truth_hex("gs14") in card_style, (
            where, card_style)

    def _spec(self):
        spec = _kpi_spec("price", "none", [], filters=[_FILTERS[1]])
        spec["kpis"] = [dict(self._KPI)]
        spec["build_options"]["registry"] = "g1 k1"
        return spec

    def test_the_saved_page(self, tmp_path, truth):
        r = _saved(tmp_path, self._spec(), _auto(truth))
        self._check(r.kpi_divs["k1"].text, "saved, as it opens")
        w = r.filter_widgets[0]
        w.value = _MOVES["range"][2]
        texts = _run_js(r.filter_callbacks[0].args, r.filter_callbacks[0].code)
        self._check(texts[r.kpi_divs["k1"].id], "saved, after a move")

    def test_the_served_app(self, tmp_path, truth):
        ns = _served_app(tmp_path, self._spec(), _auto(truth))
        doc = _served_session(ns)
        [card] = [d.text for d in doc.select({"type": Div})
                  if 'id="kpi_val_k1"' in d.text]
        self._check(card, "served, as it opens")
        w = _served_widget(doc, "weight")
        old = w.value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w.value = _MOVES["range"][2]
            for cb in w._callbacks.get("value_throttled", []):
                cb("value_throttled", old, _MOVES["range"][2])
        [card] = [d.text for d in doc.select({"type": Div})
                  if 'id="kpi_val_k1"' in d.text]
        self._check(card, "served, after a move")


class TestATieIsRoundedAsTheCardFirstRoundedIt:
    """Python rounds a tie to even and JavaScript's toFixed rounds it up: a
    median of 20.5 in %9.0f opened as 20 and read 21 after a filter move,
    and 0.25 in %9.1f 0.2 then 0.3."""

    def test_the_saved_page(self, tmp_path):
        df = pd.DataFrame({"t": [20.0, 21.0, 20.0, 21.0],
                           "q": [0.25, 0.25, 0.25, 0.25],
                           "u": [21.0, 22.0, 21.0, 22.0],
                           "x": [1.0, 2.0, 3.0, 4.0]})
        kpis = [{"name": n, "stat": st, "var": v, "fmt": f, "title": "T",
                 "update": "filter"}
                for n, st, v, f in (("k1", "median", "t", "%9.0f"),
                                    ("k2", "mean", "q", "%9.1f"),
                                    ("k3", "median", "u", "%9.0f"),
                                    ("k4", "median", "t", "%9.2g"))]
        spec = {"graphs": [{"plots": [{"type": "scatter", "yvar": "t",
                                       "xvar": "x", "options": {}}],
                            "graph_options": {"name": "g1"},
                            "if_expr": "", "in_expr": ""}],
                "kpis": kpis,
                "build_options": {"layout": "auto", "link": "", "theme": "",
                                  "title": "", "subtitle": "",
                                  "filters": [{"varname": "x",
                                               "type": "slider"}],
                                  "registry": "g1 k1 k2 k3 k4"}}
        r = _saved(tmp_path, spec, df)
        opened = _cards(d.text for d in r.kpi_divs.values())
        # k4 is Stata's %9.2g of 20.5, 21 (WP-28 section 11, GAPS2 E1: the
        # card is written by _dash_fmt_text, not Python's format()).
        assert opened == {"k1": "20", "k2": "0.2", "k3": "22", "k4": "21"}
        assert opened == {k["name"]: dr._dash_fmt_text(v, k["fmt"])
                          for k, v in zip(kpis, (20.5, 0.25, 21.5, 20.5))}
        moved = _saved_filter_move(r, 0, 1.0)
        assert moved == opened


class TestAnyGraphCanBeBrushed:
    """update(brush) follows a brush of whichever graph is brushed: here the
    second of two unlinked graphs, which plots neither the KPI's variable nor
    the first graph's."""

    @staticmethod
    def _spec():
        kpi = {"name": "kb", "stat": "p97.5", "var": "price",
               "fmt": "%20.10f", "title": "B", "update": "brush"}
        spec = _pair_spec(plots2=[{"type": "scatter", "yvar": "rep78",
                                   "xvar": "foreign", "options": {}}])
        spec["kpis"] = [kpi]
        spec["build_options"]["registry"] = "g1 g2 kb"
        return spec

    def test_the_saved_page(self, tmp_path, truth):
        df = _auto(truth)
        r = _saved(tmp_path, self._spec(), df)
        src = r.sources["g2"]
        rows = [int(i) for i in src.data[dr._ROW_ID_COLUMN]]
        picked = list(range(20))
        got = _saved_brush(r, "g2", picked)["kb"]
        want = dr._stata_percentile(
            np.sort(df["price"].to_numpy()[[rows[i] for i in picked]]),
            97.5)
        assert _agrees(got, want), (got, want)

    def test_the_served_app(self, tmp_path, truth):
        df = _auto(truth)
        ns = _served_app(tmp_path, self._spec(), df)
        doc = _served_session(ns)
        srcs = [s for s in doc.select({"type": dr.ColumnDataSource})
                if "index" in s.data and s.selected._callbacks.get("indices")
                and "rep78" in s.data]
        assert len(srcs) == 1, len(srcs)
        labels = list(srcs[0].data["index"])[:20]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            srcs[0].selected.indices = list(range(20))
        got = _served_cards(doc)["kb"]
        want = dr._stata_percentile(
            np.sort(df["price"].to_numpy()[labels]), 97.5)
        assert _agrees(got, want), (got, want)


class TestAStringVariablesCountAndDistinctCount:
    """count is the non-missing values and dcount the distinct ones, for a
    string variable too, whose missing value is "".  With three makes blank
    the saved card counted 74 and 72 (the empty string counted, and as a
    value), and read 0 once a filter moved (the recompute dropped every
    string); Stata counts 71 and 71."""

    @staticmethod
    def _inputs(tmp_path, truth):
        s = truth["strings"]
        df = pd.DataFrame({"make": s["make"],
                           "foreign": [float(v) for v in s["foreign"]],
                           "i": np.arange(1, len(s["make"]) + 1,
                                          dtype=float)})
        kpis = [{"name": "kc", "stat": "count", "var": "make",
                 "fmt": "%9.0f", "title": "C", "update": "filter"},
                {"name": "kd", "stat": "dcount", "var": "make",
                 "fmt": "%9.0f", "title": "D", "update": "filter"}]
        spec = {"graphs": [{"plots": [{"type": "scatter", "yvar": "i",
                                       "xvar": "foreign", "options": {}}],
                            "graph_options": {"name": "g1"},
                            "if_expr": "", "in_expr": ""}],
                "kpis": kpis,
                "build_options": {"layout": "auto", "link": "", "theme": "",
                                  "title": "", "subtitle": "",
                                  "filters": [_FILTERS[0]],
                                  "registry": "g1 kc kd"}}
        sp, dp = _write_inputs(tmp_path, spec, df)
        # make is a string, as jsonio says of a Stata string variable.
        with open(dp, encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("variableIsString", "variableTypeIsString"):
            data["StataJSON"][key]["make"] = True
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        want = {(v["scope"], v["stat"]): v["value"] for v in s["values"]}
        return sp, dp, want

    @staticmethod
    def _check(cards, want, scope, where):
        got = {"count": cards.get("kc"), "dcount": cards.get("kd")}
        bad = ["%s: card %r, Stata %r" % (st, got[st], want[(scope, st)])
               for st in ("count", "dcount")
               if not _agrees(got[st] or "", want[(scope, st)])]
        assert not bad, where + ": " + "; ".join(bad)

    def test_the_saved_page(self, tmp_path, truth):
        sp, dp, want = self._inputs(tmp_path, truth)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        self._check(_cards(d.text for d in r.kpi_divs.values()), want,
                    "all", "saved, as it opens")
        self._check(_saved_filter_move(r, 0, "1"), want, "f1",
                    "saved, foreign = 1")

    def test_the_served_app(self, tmp_path, truth):
        sp, dp, want = self._inputs(tmp_path, truth)
        op = os.path.join(str(tmp_path), "app_str.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "hc4_str_%d" % next(_SEQ))
        self._check(_served_cards(_served_session(ns)), want, "all",
                    "served, as it opens")
        self._check(_served_filter_move(ns, "foreign", "1"), want, "f1",
                    "served, foreign = 1")


# ===========================================================================
# 6. Server Mode's histogram and density rows: what a filter move redraws
# ===========================================================================

_AGG_FILTERS = [{"varname": "weight", "type": "range"}]
_AGG_MOVE = (2000.0, 3500.0)

#: case -> (plot type, graph by(), graph if, plot if).  Each draws a subset
#: of the rows: a by() panel, a graph with its own if, a layer with its own.
_AGG_CASES = {
    "histogram by(foreign)": ("histogram", "foreign", "", ""),
    "histogram, graph if foreign==1": ("histogram", "", "foreign==1", ""),
    "histogram, plot if foreign==1": ("histogram", "", "", "foreign==1"),
    "kdensity by(foreign)": ("kdensity", "foreign", "", ""),
    "kdensity, graph if foreign==1": ("kdensity", "", "foreign==1", ""),
    "histogram, every row": ("histogram", "", "", ""),
    "kdensity, every row": ("kdensity", "", "", ""),
}


def _agg_spec(case, filters=True):
    ptype, by, gif, pif = _AGG_CASES[case]
    plot = {"type": ptype, "var": "mpg",
            "options": {"bin": "5"} if ptype == "histogram" else {},
            "if_expr": pif, "in_expr": ""}
    go = {"name": "g1"}
    if by:
        go["by"] = by
    return {"graphs": [{"plots": [plot], "graph_options": go,
                        "if_expr": gif, "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "",
                              "filters": list(_AGG_FILTERS) if filters
                              else [],
                              "registry": "g1"}}


def _agg_rows(df, case, title):
    """The mpg values a layer draws after the move: the rows the filter
    keeps, within the panel and the qualifier."""
    _p, by, gif, pif = _AGG_CASES[case]
    sub = df[(df.weight >= _AGG_MOVE[0]) & (df.weight <= _AGG_MOVE[1])]
    for q in (gif, pif):
        if q:
            sub = sub.query(q)
    if by:
        sub = sub[sub[by] == float(title.split()[-1])]
    v = sub["mpg"].to_numpy(dtype=float)
    return v[~np.isnan(v)]


def _agg_renderers(figures):
    """``[(figure title, renderer)]`` for every aggregate layer."""
    out = []
    for fig in figures:
        for rr in fig.renderers:
            data = rr.data_source.data
            if "top" in data or ("x" in data and "y" in data
                                 and _ROW_ID_NOT_IN(data)):
                out.append((fig.title.text, rr))
    return out


def _ROW_ID_NOT_IN(data):
    return dr._ROW_ID_COLUMN not in data


class TestTheSavedPageRecountsALayersOwnRows:
    """Standalone "rescales the bars from the rows that pass the filter but
    keeps the bin edges" (dash.sthlp, Server Mode).  A by() panel's, or a
    qualified graph's or layer's, bars and curve were recounted from EVERY
    row that passed the filter: measured, the foreign==0 panel read
    [0.005, 0.098, 0.093, 0.021, 0.010] where its own 30 rows give
    [0, 0.114, 0.076, 0.030, 0.008], and `if foreign==1' read the numbers
    all 47 rows give."""

    @pytest.mark.parametrize("case", sorted(_AGG_CASES))
    def test_after_a_filter_move(self, tmp_path, truth, case):
        df = _auto(truth)
        r = _saved(tmp_path, _agg_spec(case), df)
        w = r.filter_widgets[0]
        cb = r.filter_callbacks[0]
        w.value = _AGG_MOVE
        out = _run_js_full(cb.args, cb.code)["sources"]
        layers = _agg_renderers(r.figures.values())
        assert layers, "no aggregate layer was drawn"
        # `assert layers' passed a by() case that drew one panel's layer of
        # the two, and the missing panel was never recounted.  Measured
        # 24sep2026: one aggregate layer a panel -- titled "0" and "1" under
        # by(foreign) -- and one untitled layer in every other case.
        want_titles = ["0", "1"] if _AGG_CASES[case][1] else [""]
        assert sorted(t for t, _rr in layers) == want_titles, (
            "aggregate layers drawn, by panel title: %s"
            % sorted(t for t, _rr in layers))
        bad = []
        for title, rr in layers:
            src = rr.data_source
            after = out.get(src.id)
            assert after is not None, "%s: the callback did not reach its " \
                "source" % title
            v = _agg_rows(df, case, title)
            if "top" in src.data:
                left = [float(x) for x in src.data["left"]]
                right = [float(x) for x in src.data["right"]]
                for col, edges in (("left", left), ("right", right)):
                    assert [float(x) for x in after.get(col, edges)] \
                        == edges, "%s: the saved page moved its bins" % title
                want = []
                for j, (a, b) in enumerate(zip(left, right)):
                    last = j == len(left) - 1
                    c = int(((v >= a) & ((v <= b) if last else (v < b))).sum())
                    want.append(c / (len(v) * (b - a)))
                got = after["top"]
            else:
                grid = np.asarray(after["x"], dtype=float)
                assert list(grid) == [float(x) for x in src.data["x"]], (
                    "%s: the saved page moved its density grid" % title)
                want = list(dr._kde_curve(v, grid, dr._stata_kde_bandwidth(v),
                                          "epanechnikov"))
                got = after["y"]
            if not np.allclose(np.asarray(got, dtype=float), want,
                               rtol=1e-9, atol=1e-12):
                bad.append("%s: %s, its own rows give %s"
                           % (title, np.round(got, 5)[:6],
                              np.round(want, 5)[:6]))
        assert not bad, "\n  ".join(bad)


class TestTheServedAppRedrawsFromTheFilteredRows:
    """Served: "Yes, including bin edges" -- the panel, graph or layer is
    drawn again from its filtered rows, as a page built from those rows
    draws it."""

    @pytest.mark.parametrize("case", sorted(_AGG_CASES))
    def test_after_a_filter_move(self, tmp_path, truth, case):
        df = _auto(truth)
        ns = _served_app(tmp_path, _agg_spec(case), df)
        doc = _served_session(ns)
        w = _served_widget(doc, "weight")
        old = w.value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w.value = _AGG_MOVE
            for cb in w._callbacks.get("value_throttled", []):
                cb("value_throttled", old, _AGG_MOVE)
        figs = [f for f in doc.select({"type": type(r_fig())})]
        served = {t: rr.data_source.data for t, rr in _agg_renderers(figs)}
        kept = df[(df.weight >= _AGG_MOVE[0]) & (df.weight <= _AGG_MOVE[1])]
        ref = _saved(tmp_path, _agg_spec(case, filters=False),
                     kept.reset_index(drop=True))
        want = {t: rr.data_source.data
                for t, rr in _agg_renderers(ref.figures.values())}
        assert set(served) == set(want), (sorted(served), sorted(want))
        bad = []
        for t in want:
            for col in ("left", "right", "top", "x", "y"):
                if col in want[t]:
                    a = np.asarray(served[t][col], dtype=float)
                    b = np.asarray(want[t][col], dtype=float)
                    if a.shape != b.shape or not np.allclose(a, b, rtol=1e-9):
                        bad.append("%s %s: served %s, page of the kept rows "
                                   "%s" % (t, col, np.round(a, 4)[:6],
                                           np.round(b, 4)[:6]))
        assert not bad, "\n  ".join(bad)


def r_fig():
    from bokeh.plotting import figure
    return figure()


# ===========================================================================
# 7. dash serve launches
# ===========================================================================
# Measured at 4ede074: after `dash scatter mpg weight, name(g1)`,
# `dash serve, port(5127) timeout(1) nobrowser' stopped with
#     ValueError: dash_render: --output must end in .py for mode 'server'
# r(7102), on every launch.  _dash_serve hands the renderer a Stata tempfile
# on purpose -- a registered name is what Stata erases when the command
# ends, and the app it names embeds the data -- and the renderer's output
# check, added later, asked every server-mode path for a .py.  Nothing ran
# the real handoff: the launch test stops early and the browser test uses a
# stub renderer.

class TestTheOutputPathRule:
    """What --output the renderer takes on each route."""

    def test_the_launch_route_takes_a_fresh_stata_tempfile(self, tmp_path):
        p = str(tmp_path / "S_86564.000002")
        assert dr._validate_output_path(p, "server", launch=True) == p

    def test_the_launch_route_takes_a_py(self, tmp_path):
        p = str(tmp_path / "app.py")
        assert dr._validate_output_path(p, "server", launch=True) == p
        open(p, "w").close()
        assert dr._validate_output_path(p, "server", launch=True) == p

    def test_the_launch_route_never_overwrites_a_file_that_is_not_py(
            self, tmp_path):
        p = tmp_path / "notes.txt"
        p.write_text("keep me")
        with pytest.raises(ValueError, match="already exists"):
            dr._validate_output_path(str(p), "server", launch=True)
        assert p.read_text() == "keep me"

    def test_building_a_server_app_still_needs_a_py(self, tmp_path):
        """dash build, server: a file the user keeps is a .py."""
        with pytest.raises(ValueError, match=r"must end in \.py"):
            dr._validate_output_path(str(tmp_path / "S_1.000001"), "server")

    def test_a_standalone_page_still_needs_an_html(self, tmp_path):
        with pytest.raises(ValueError, match=r"must end in \.html"):
            dr._validate_output_path(str(tmp_path / "S_1.000001"),
                                     "standalone", launch=True)

    @pytest.mark.parametrize("bad", ["../S_1.000001", "-S_1.000001",
                                     "S_1\n.000001"])
    def test_the_other_checks_hold_on_the_launch_route(self, tmp_path, bad):
        with pytest.raises(ValueError):
            dr._validate_output_path(os.path.join(str(tmp_path), bad),
                                     "server", launch=True)


def _free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.serve
class TestTheRealHandoffServes:
    """The renderer run exactly as _dash_serve runs it -- runpy on
    dash_render.py with the same sys.argv, the output a fresh extension-less
    tempfile name -- starts a server that answers /health on the port asked
    for, and a Ctrl+C (SIGINT) stops the launcher and the app it started."""

    def test_it_serves_and_stops(self, tmp_path, truth):
        import signal
        import urllib.request
        spec = _kpi_spec("price", "none", ["p97.5"], filters=[])
        sp, dp = _write_inputs(tmp_path, spec, _auto(truth))
        out = str(tmp_path / "S_86564.000002")
        port = _free_port()
        render = os.path.join(os.path.dirname(_HERE), "dash_render.py")
        argv = ["dash_render.py", "--spec", sp, "--data", dp,
                "--output", out, "--mode", "server", "--launch",
                "--port", str(port), "--timeout", "1", "--no-browser"]
        code = ("import sys, runpy; sys.argv = %r; "
                "runpy.run_path(%r, run_name='__main__')" % (argv, render))
        t0 = time.time()
        proc = subprocess.Popen([sys.executable, "-c", code],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        status, body = None, ""
        try:
            deadline = time.time() + 60
            while time.time() < deadline and status is None:
                if proc.poll() is not None:
                    raise AssertionError(
                        "the launcher exited before serving:\n"
                        + proc.stdout.read()[:3000])
                try:
                    with urllib.request.urlopen(
                            "http://127.0.0.1:%d/health" % port,
                            timeout=5) as r:
                        status, body = r.status, r.read().decode()
                except Exception:
                    time.sleep(0.3)
            up = time.time() - t0
            assert status == 200, "no server answered on port %d" % port
            assert json.loads(body).get("status") == "ok", body
            assert os.path.exists(out), "the app was not written"
        finally:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise AssertionError("the launcher did not stop on SIGINT")
        # The app the launcher started is gone with it.
        gone = False
        for _ in range(50):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/health" % port,
                                       timeout=1)
                time.sleep(0.2)
            except Exception:
                gone = True
                break
        assert gone, "the served app outlived its launcher"
        print("\nserved after %.1f s, stopped after %.1f s"
              % (up, time.time() - t0))


# ===========================================================================
# 8. The rest of Server Mode's comparison table and its limitations
# ===========================================================================

def _pair_spec(link="", filters=None, plots2=None):
    """Two graphs; the second draws *plots2* (default: price on weight)."""
    return {"graphs": [
        {"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                    "options": {}}],
         "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": ""},
        {"plots": plots2 or [{"type": "scatter", "yvar": "price",
                              "xvar": "weight", "options": {}}],
         "graph_options": {"name": "g2"}, "if_expr": "", "in_expr": ""}],
        "kpis": [],
        "build_options": {"layout": "auto", "link": link, "theme": "",
                          "title": "", "subtitle": "",
                          "filters": list(filters or []),
                          "registry": "g1 g2"}}


class TestTheSavedPageNeedsNoNetwork:
    """Requires internet / server: No.  BokehJS is written into the page,
    and the page names nothing to fetch."""

    def test_bokehjs_is_inline_and_nothing_is_fetched(self, tmp_path, truth):
        sp, dp = _write_inputs(tmp_path, _pair_spec(), _auto(truth))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(sp, dp).render()
        assert "/* END bokeh.min.js */" in html
        assert not re.findall(r"<script[^>]+\bsrc\s*=", html)
        assert not re.findall(r"<link[^>]+\bhref\s*=", html)


class TestAFitLineOnAFilterMove:
    """Fit-line recompute on filter: No on the saved page, Yes served."""

    _FIT = [{"type": "lfit", "yvar": "price", "xvar": "weight",
             "options": {}}]

    @staticmethod
    def _fit_source(figures):
        for fig in figures:
            for rr in fig.renderers:
                d = rr.data_source.data
                if "x" in d and "y" in d and dr._ROW_ID_COLUMN not in d:
                    return rr.data_source
        raise AssertionError("no fitted line was drawn")

    def test_the_saved_page_keeps_its_line(self, tmp_path, truth):
        spec = _pair_spec(filters=_AGG_FILTERS, plots2=self._FIT)
        r = _saved(tmp_path, spec, _auto(truth))
        src = self._fit_source(r.figures.values())
        before = {c: [float(v) for v in src.data[c]] for c in ("x", "y")}
        r.filter_widgets[0].value = _AGG_MOVE
        out = _run_js_full(r.filter_callbacks[0].args,
                           r.filter_callbacks[0].code)["sources"]
        after = out.get(src.id, before)
        assert {c: [float(v) for v in after[c]] for c in ("x", "y")} \
            == before

    def test_the_served_app_draws_it_again_from_the_kept_rows(self, tmp_path,
                                                              truth):
        df = _auto(truth)
        spec = _pair_spec(filters=_AGG_FILTERS, plots2=self._FIT)
        ns = _served_app(tmp_path, spec, df)
        doc = _served_session(ns)
        w = _served_widget(doc, "weight")
        old = w.value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w.value = _AGG_MOVE
            for cb in w._callbacks.get("value_throttled", []):
                cb("value_throttled", old, _AGG_MOVE)
        got = self._fit_source(doc.select({"type": type(r_fig())}))
        kept = df[(df.weight >= _AGG_MOVE[0]) & (df.weight <= _AGG_MOVE[1])]
        ref = _saved(tmp_path, _pair_spec(plots2=self._FIT),
                     kept.reset_index(drop=True))
        want = self._fit_source(ref.figures.values())
        for c in ("x", "y"):
            assert np.allclose(np.asarray(got.data[c], dtype=float),
                               np.asarray(want.data[c], dtype=float),
                               rtol=1e-9), c


class TestUnderBokehServe:
    """`bokeh serve app.py' serves the dashboard, as bokeh serve's app: its
    own address and port, no /health, no launcher flags and no session
    limits (dash.sthlp, Server Mode)."""

    def test_the_session_limits_do_not_hold(self, tmp_path, truth):
        """bokeh serve runs the script afresh, in a new module, for every
        session (bokeh.application.handlers.code.CodeHandler), so the
        module-level limiter starts empty each time.  With one session a
        client, the launcher's route refuses the second and later sessions
        from one address; bokeh serve's refuses none."""
        from bokeh.application.handlers.code import CodeHandler
        from test_adversarial_matrix import _Req, _SessionDoc, _app_source
        src = _app_source(tmp_path, _pair_spec(), _auto(truth))
        line = [ln for ln in src.split("\n")
                if ln.startswith("_RATE_LIMIT_RPM = ")]
        assert len(line) == 1, "the session limit's constant moved"
        src = src.replace(line[0], "_RATE_LIMIT_RPM = 1")

        def refused(doc):
            return "429 Too Many Requests" in " ".join(
                d.text for d in doc.select({"type": Div}))

        ns = _load_app(src, "hc4_limit_%d" % next(_SEQ))
        launcher = []
        for _ in range(4):
            doc = _SessionDoc(_Req("10.0.0.9"))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ns["make_document"](doc)
            launcher.append(refused(doc))
        assert launcher == [False, True, True, True]

        handler = CodeHandler(source=src,
                              filename=str(tmp_path / "app_bs.py"))
        served = []
        for _ in range(4):
            doc = _SessionDoc(_Req("10.0.0.9"))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                handler.modify_document(doc)
            served.append(refused(doc))
        assert served == [False, False, False, False]

    def test_it_listens_where_bokeh_serve_listens(self):
        """bokeh serve's own --address, which by default is none: Bokeh then
        listens on every interface.  The app's loopback default belongs to
        its launcher, which bokeh serve does not run."""
        from bokeh.command.subcommands.serve import Serve
        opts = {}
        for name, arg in Serve.args:
            opts[name if isinstance(name, str) else name[0]] = arg
        assert opts["--address"].default is None
        assert opts["--port"].default == 5006

    @pytest.mark.serve
    def test_there_is_no_health_route(self, tmp_path):
        from test_server_serves import _Served, _build_app
        app = _build_app(str(tmp_path))
        with _Served(app) as srv:
            assert srv.status("/app") == 200
            assert srv.status("/health") == 404


class TestOneRecomputationAtATime:
    """The launcher's server is one process with one event loop, so the
    recomputations of every session run one at a time."""

    def test_the_launcher_asks_for_one_process(self, tmp_path, truth):
        from test_adversarial_matrix import _app_source
        ns = _load_app(_app_source(tmp_path, _pair_spec(), _auto(truth)),
                       "hc4_procs_%d" % next(_SEQ))
        seen = {}

        def fake_server(apps, **kw):
            seen.update(kw)
            return object()

        ns["Server"] = fake_server
        ns["_dash_server_app"](port=_free_port())
        assert seen.get("num_procs") == 1
        assert seen.get("address") == "127.0.0.1"


class TestTheLauncherOpensABrowserOnlyWhenAsked:
    """`python app.py' opens no browser unless --show is given, and
    --timeout is minutes: the launcher run as __main__, with bokeh's Server
    replaced by a recorder so nothing listens."""

    def test_show_and_timeout(self, tmp_path, truth, monkeypatch):
        import bokeh.server.server as bss
        from test_adversarial_matrix import _app_source
        seen = {}

        class _Loop:
            def add_callback(self, fn, *a):
                seen.setdefault("callbacks", []).append(
                    getattr(fn, "__name__", ""))

            def call_later(self, delay, fn):
                seen["later"] = (delay, getattr(fn, "__name__", ""))

            def start(self):
                seen["loop_started"] = True

            def stop(self):
                pass

        class _Server:
            def __init__(self, apps, **kw):
                seen["kw"] = kw
                self.io_loop = _Loop()

            def start(self):
                seen["started"] = True

            def show(self, *a):
                pass

            def stop(self):
                seen["stopped"] = True

        monkeypatch.setattr(bss, "Server", _Server)
        src = _app_source(tmp_path, _pair_spec(), _auto(truth))
        runs = {}
        for argv in (["app.py"], ["app.py", "--show", "--timeout", "1"]):
            seen.clear()
            monkeypatch.setattr(sys, "argv", argv)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec(compile(src, "app.py", "exec"), {"__name__": "__main__"})
            runs[len(argv)] = dict(seen)
        plain, asked = runs[1], runs[4]
        assert plain["started"] and plain["stopped"]
        assert "show" not in plain.get("callbacks", [])
        assert "later" not in plain
        assert asked.get("callbacks") == ["show"]
        assert asked["later"] == (60, "stop")


@pytest.mark.serve
class TestTheLauncherServes:
    """A real `python app.py', with a limit of one session a client."""

    def test_a_refused_session_gets_the_refusal_page(self, tmp_path):
        from bokeh.client import pull_session
        from test_server_serves import _Launched, _build_app
        app = _build_app(str(tmp_path))
        with _Launched(app, ["--sessions-per-client", "1"]) as srv:
            # _Launched spent the one session when it waited for the app.
            status, page = srv.get("/")
            assert status == 200
            session = pull_session(url=srv.url("/"))
            try:
                texts = [d.text for d in session.document.select(
                    {"type": Div})]
            finally:
                session.close()
            assert len(texts) == 1 and "429 Too Many Requests" in texts[0]
            assert srv.status("/health") == 200

    def test_a_client_that_sends_no_origin_is_admitted(self, tmp_path):
        """The Origin allow-list "is not an access control: a client that is
        not a browser can omit the header".  Bokeh's own client sends none
        (tornado's websocket_connect sets Upgrade, Connection and the
        Sec-WebSocket headers only), and it is served the dashboard."""
        from bokeh.client import pull_session
        from test_server_serves import _Launched, _build_app
        app = _build_app(str(tmp_path))
        with _Launched(app) as srv:
            session = pull_session(url=srv.url("/"))
            try:
                roots = list(session.document.roots)
                texts = " ".join(d.text for d in session.document.select(
                    {"type": Div}))
            finally:
                session.close()
        assert roots and "429" not in texts

    def test_the_page_has_a_mobile_viewport(self, tmp_path):
        """WP-28 E14: the served page now declares the same viewport meta
        the saved page declares (test_geometry.py), through the served
        template (dr._dash_served_template)."""
        from test_server_serves import _Launched, _build_app
        app = _build_app(str(tmp_path))
        with _Launched(app) as srv:
            status, page = srv.get("/")
        # The presence is read on the dashboard's own page, or it proves
        # nothing.  A 4xx or 5xx raises out of get() (a make_document that
        # raises is a 500, measured 24sep2026), but a 200 page that is not
        # the dashboard declares the viewport too, since the template
        # governs every page the launcher serves: a session the limiter
        # refuses is served, with 200, as a page holding only the refusal
        # (test_a_refused_session_gets_the_refusal_page).  Measured
        # 24sep2026: 200, the session Bokeh embeds (its token) and the
        # title the app sets, a charset, a CSP <meta> and one viewport
        # <meta> after it.
        assert status == 200, status
        assert "Bokeh.embed.embed_items" in page and '"token"' in page, (
            page[:600])
        assert "<title>Served Dashboard</title>" in page, page[:600]
        # The control: the same pattern finds the viewport the saved page
        # declares, in the form dash writes it.
        assert re.search(r'<meta[^>]+name="viewport"', dr._CSP_META)
        assert page.count(dr._DASH_VIEWPORT_META) == 1
        assert page.index("Content-Security-Policy") < page.index(
            dr._DASH_VIEWPORT_META)


class TestTheModesDifferHere:
    """What the help's server-mode section says of the two pages, each
    measured (WP-28 E14: the viewport and the dimming below no longer
    differ; the class name and docstring stay to hold the other rows of
    the comparison table)."""

    def test_a_brush_dims_unselected_points_alike_when_served(self,
                                                               tmp_path,
                                                               truth):
        """dr._dash_dim_nonselection, module-level and copied into the
        served app, dims a linked figure's nonselection glyph to
        dr._NONSELECTION_ALPHA in both renderers -- it used to be a
        DashRenderer method the served app could not copy, so a served
        brush always dimmed at Bokeh's own 0.1."""
        spec = _pair_spec(link="g1 g2")
        r = _saved(tmp_path, spec, _auto(truth))
        saved = {round(float(rr.nonselection_glyph.fill_alpha), 4)
                 for fig in r.figures.values() for rr in fig.renderers
                 if hasattr(rr, "nonselection_glyph")}
        ns = _served_app(tmp_path, spec, _auto(truth))
        doc = _served_session(ns)
        served = {round(float(rr.nonselection_glyph.fill_alpha), 4)
                  for fig in doc.select({"type": type(r_fig())})
                  for rr in fig.renderers
                  if hasattr(rr, "nonselection_glyph")}
        assert saved == served == {0.15}

    def test_a_date_is_a_date_in_both_modes(self, tmp_path, truth):
        """The comparison table's Dates row, Yes in both columns since
        WP-27: a date axis, date tooltips and a date slider saved and
        served.  (The date KPI card is TestAPercentileOfADateIsADate.)"""
        from bokeh.models import DateRangeSlider, DatetimeAxis, HoverTool
        spec = _date_spec(["max"], [{"varname": "date", "type": "range"}])
        r = _saved(tmp_path, spec, _date_df(truth))
        [fig] = list(r.figures.values())
        ns = _served_app(tmp_path, spec, _date_df(truth))
        doc = _served_session(ns)
        [sfig] = list(doc.select({"type": type(r_fig())}))
        [w] = [x for x in doc.select({"type": DateRangeSlider})
               if getattr(x, "_dash_var", None) == "date"]
        first = truth["dates"]["first"]
        ms0 = (first - 3653) * 86400000.0
        ms1 = ms0 + (truth["dates"]["n"] - 1) * 86400000.0
        for f, widget in ((fig, r.filter_widgets[0]), (sfig, w)):
            assert isinstance(f.xaxis[0], DatetimeAxis)
            tips = [t.tooltips for t in f.tools if isinstance(t, HoverTool)]
            assert ("date", "@{date}{%F}") in tips[0]
            assert type(widget).__name__ == "DateRangeSlider"
            assert (widget.start, widget.end) == (ms0, ms1)

    def test_the_saved_slider_recomputes_at_every_step(self, tmp_path,
                                                       truth):
        spec = _pair_spec(filters=[{"varname": "mpg", "type": "slider"}])
        r = _saved(tmp_path, spec, _auto(truth))
        assert list((r.filter_widgets[0].js_property_callbacks or {})) \
            == ["change:value"]
        ns = _served_app(tmp_path, spec, _auto(truth))
        doc = _served_session(ns)
        w = _served_widget(doc, "mpg")
        assert list(w._callbacks) == ["value_throttled"]


class TestExcludeLeavesTheCardAlone:
    """name() is the identifier filter(..., exclude()) names; a KPI excluded
    from the filter that moves keeps its value (dash.sthlp, KPI options)."""

    def test_the_saved_page(self, tmp_path, truth):
        r = _saved(tmp_path, _modes_spec(exclude=["kf", "kfb"]),
                   _auto(truth))
        moved = _saved_filter_move(r, 0, _MOVES["range"][2])
        want = _stata_value(truth, "price", "all", "p97.5")
        for k in ("kf", "kfb"):
            assert k not in moved or _agrees(moved[k], want), (k, moved)
        opened = _cards(d.text for d in r.kpi_divs.values())
        assert _agrees(opened["kf"], want), opened

    def test_the_served_app(self, tmp_path, truth):
        ns = _served_app(tmp_path, _modes_spec(exclude=["kf", "kfb"]),
                         _auto(truth))
        moved = _served_filter_move(ns, "weight", _MOVES["range"][2])
        want = _stata_value(truth, "price", "all", "p97.5")
        for k in ("kf", "kfb"):
            assert _agrees(moved[k], want), (k, moved)
