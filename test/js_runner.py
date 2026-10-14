"""One shared runner for the saved page's CustomJS, under node (WP-28 S03).

Why state must be carried: the saved page's filter callback
(``dash_render._FILTER_JS``) recomputes every source, boolean filter, Div
and glyph width it is handed from the widgets' CURRENT values every time it
runs -- exactly as BokehJS runs it in a browser, one call per move.  A test
harness that re-encodes the Bokeh models from Python on every call throws
away what the previous call left there, so a SEQUENCE of moves (E2's
"price to [4000,5000], then foreign=1, then price back to its full range")
was unmeasured on the saved page: each call started over from the page's
build-time data.  ``JsSession`` fixes that: ``.run()``/``.run_code()``
write node's ``data``/``booleans``/``text``/``width`` output back into the
Python models by default, so the next call starts from what the last one
left, the way the browser does.

``JsSession(..., commit=False)`` is the dry-run counterpart, for a test
that reuses one source across independent calls and must not let a run's
result leak into the next one (``test_filter_exclude.py``'s
``TestThePrimarySourceFallback``, and the encoding-only shims below).

The ``"__proto__"`` rule: a Bokeh model's data is written into node as
``JSON.parse(<json string>)``, never as a bare object literal.  A column
literally named ``"__proto__"`` written into an object literal sets the
object's prototype instead of adding a key, and the column silently
vanishes; ``JSON.parse`` has no such special case
(``test_saved_filter_layers.py:186-189``; the page's own guard is
``dash_own_col``, ``dash_render.py:14211-14217``).

``NODE`` honours the ``DASH_NODE`` environment variable before falling back
to ``shutil.which("node")``, and ``node()``/``requires_node`` SKIP (never
fail) when neither finds an interpreter -- naming ``DASH_NODE`` in the
skip reason.  Under ``DASH_STRICT=1`` (``make test``, ``make test-dev``)
a skip is a red run: that is deliberate (CLAUDE.md rule 3), not a bug in
this module.

Consumers, by section: S04's ``test_display_format_writer.py`` imports
``run_js`` and ``requires_node``; S05's ``test_histogram_edge_rule.py``
imports ``run_filter_js_block`` and ``NODE`` from here and ``_hist`` from
``test_statistical_helpers``; S12 and S17 use ``JsSession`` and
``mask_parity`` by those names.  ``test_statistical_helpers.py`` keeps
``_NODE`` and ``_run_filter_js_block`` as aliases of this module's
``NODE``/``run_filter_js_block`` so a file written against either spelling
still collects.

While iterating, run only this file: ``python3 -m pytest
test/test_js_runner.py -q`` (CLAUDE.md rule 11); the whole suite runs once,
before a commit, as ``python3 -m pytest test/ -q``.

No gap closes in this module: it is test-only infrastructure for C2, E2,
E3, G6, X1 (sections 04, 05, 11, 12, 17), not a fix in its own right.
WP-29 S12 adds a renderer's ``muted``, a Title's or Div's ``visible`` and
a LegendItem's ``label`` to what a run reads and commits, each key on its
own, so the saved page's stale cue (P0.17) can be measured under node.
"""
import datetime as _dt
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest
from bokeh.model import Model
from bokeh.core.properties import value as _bk_value
from bokeh.models import (Arrow, BooleanFilter, BoxAnnotation,
                          ColumnDataSource,
                          Div, FixedTicker, GlyphRenderer, LegendItem,
                          Range1d, RangeSlider, Select, Slider, Title)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

# ---------------------------------------------------------------------------
# node lookup
# ---------------------------------------------------------------------------

def find_node():
    """The interpreter's path: an explicit ``DASH_NODE`` override first (a
    machine without node on PATH, or a pinned build), else PATH, else None."""
    return os.environ.get("DASH_NODE") or shutil.which("node")


#: The interpreter's path, resolved once at import by find_node().
NODE = find_node()


def node():
    """*NODE*, or SKIP (never fail) naming ``DASH_NODE``.

    A skip here is a red run under ``DASH_STRICT=1`` (``make test``,
    ``make test-dev``): CLAUDE.md rule 3 wants a real run over a hidden
    gap, so a missing interpreter must not silently pass.
    """
    if NODE is None:
        pytest.skip("node is not installed; set DASH_NODE to its path "
                    "(a skip is red under DASH_STRICT=1)")
    return NODE


#: For a test CLASS: ``@requires_node`` in place of a hand-written
#: ``skipif``, so every node-dependent class skips (and reads red under
#: strict) the same way.
requires_node = pytest.mark.skipif(
    NODE is None, reason="node is not installed; set DASH_NODE")


# ---------------------------------------------------------------------------
# Encoding: Python/Bokeh values -> JSON node can read back
# ---------------------------------------------------------------------------

def plain(v):
    """*v* as a JSON-safe Python scalar (NaN -> None, a Timestamp -> epoch
    milliseconds, as the saved page's own snapshot does)."""
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return None if math.isnan(v) else v
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, (pd.Timestamp, np.datetime64)):
        return dr._dash_json_value(v)
    if isinstance(v, _dt.datetime):
        # A second date column reaches a source as datetime objects (a
        # millisecond datetime64 array's tolist(); WP-30 P1.23a).
        return dr._dash_json_value(pd.Timestamp(v))
    return v


def encode(v, models, objs):
    """*v* as JSON; each Bokeh ``Model`` becomes ONE shared stand-in (in
    *models*, keyed by id, with the live object kept in *objs*) referenced
    everywhere it appears as ``{"__ref__": id}`` -- so identity
    (``_srcs.includes(source)`` in the page's own script) is what the page
    has, and a model is never encoded twice."""
    if isinstance(v, Model):
        if v.id not in models:
            models[v.id] = None  # placeholder: breaks self-reference cycles
            objs[v.id] = v
            models[v.id] = stand_in(v, models, objs)
        return {"__ref__": v.id}
    if isinstance(v, dict):
        return {str(k): encode(x, models, objs) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray, pd.Series)):
        return [encode(x, models, objs) for x in list(v)]
    return plain(v)


def stand_in(m, models, objs):
    """The JSON node sees for model *m*: a source's ``data``, a filter's
    ``booleans``, a Div's ``text``, and whichever of ``value``, ``start``,
    ``end``, ``step``, ``indices``, ``width`` the model has -- the
    superset every write-back rule and every widget kind needs."""
    if isinstance(m, ColumnDataSource):
        return {"__type__": "ColumnDataSource",
                "data": {str(c): encode(list(v), models, objs)
                         for c, v in m.data.items()}}
    if isinstance(m, BooleanFilter):
        return {"__type__": "BooleanFilter",
                "booleans": [bool(b) for b in (m.booleans or [])]}
    if isinstance(m, Div):
        return {"__type__": "Div", "text": m.text, "visible": bool(m.visible)}
    if isinstance(m, GlyphRenderer):
        return {"__type__": "GlyphRenderer", "muted": bool(m.muted),
                "visible": bool(m.visible)}
    if isinstance(m, Title):
        return {"__type__": "Title", "visible": bool(m.visible)}
    if isinstance(m, LegendItem):
        return {"__type__": "LegendItem",
                "label": {"value": _label_text(m.label)}}
    # WP-30 P1.3a: a Range1d's Reset extent and a FixedTicker's ticks, the
    # two models the axis re-finish writes (and reads back, below).
    if isinstance(m, Range1d):
        return {"__type__": "Range1d",
                **{p: plain(getattr(m, p))
                   for p in ("start", "end", "reset_start", "reset_end")}}
    # WP-30 P1.20b: the plot region's inner box, whose edges the
    # re-finish writes.
    if isinstance(m, BoxAnnotation):
        return {"__type__": "BoxAnnotation",
                **{p: plain(getattr(m, p))
                   for p in ("left", "right", "bottom", "top")}}
    # WP-30 P1.21b: an unextended reference line's ends, which the
    # re-finish writes.
    if isinstance(m, Arrow):
        return {"__type__": "Arrow",
                **{p: plain(getattr(m, p))
                   for p in ("x_start", "x_end", "y_start", "y_end")}}
    if isinstance(m, FixedTicker):
        return {"__type__": "FixedTicker",
                "ticks": [plain(v) for v in (m.ticks or [])]}
    props = m.properties()
    return {"__type__": type(m).__name__,
            **{p: encode(getattr(m, p), models, objs)
               for p in ("value", "start", "end", "step", "indices", "width")
               if p in props}}


def _label_text(label):
    """A LegendItem label's text: ``.value`` of a ``Value``, ``"value"``
    of a dict, else ``None`` (a field label)."""
    if isinstance(label, dict):
        return label.get("value")
    return getattr(label, "value", None)


# BokehJS runs a CustomJS body as a strict-mode function whose parameters
# are the args' names, then cb_obj and cb_data.  Lifted, unchanged in
# behaviour, from test_saved_filter_layers.py:142-179 (the superset: it
# carries cb_obj, which test_filter_exclude.py's copy did not need).
RUNNER = r"""
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
  } else if (o.__type__ === "Range1d") {
    // BokehJS's HasProps.setv assigns each attribute in turn.
    o.change = {emit() {}};
    o.setv = function (attrs) { for (const k of Object.keys(attrs)) this[k] = attrs[k]; };
  } else if (o.__type__ === "FixedTicker") {
    o.change = {emit() {}};
  } else if (o.__type__ === "BoxAnnotation" || o.__type__ === "Arrow") {
    o.setv = function (attrs) { for (const k of Object.keys(attrs)) this[k] = attrs[k]; };
  }
}
const args = resolve(RAW.args);
const names = Object.keys(args);
const cb_obj = RAW.cb_obj ? resolve(RAW.cb_obj) : null;
new Function(...names, "cb_obj", "cb_data", '"use strict";\n' + RAW.code)(
  ...names.map((n) => args[n]), cb_obj, {});
const out = {};
for (const [id, o] of Object.entries(REG)) {
  if (o.__type__ === "ColumnDataSource") out[id] = {data: o.data};
  else if (o.__type__ === "BooleanFilter") out[id] = {booleans: o.booleans};
  else if (o.__type__ === "Range1d")
    out[id] = {range: {start: o.start, end: o.end, reset_start: o.reset_start,
                       reset_end: o.reset_end}};
  else if (o.__type__ === "FixedTicker") out[id] = {ticks: Array.from(o.ticks)};
  else if (o.__type__ === "BoxAnnotation")
    out[id] = {box: {left: o.left, right: o.right, bottom: o.bottom, top: o.top}};
  else if (o.__type__ === "Arrow")
    out[id] = {arrow: {x_start: o.x_start, x_end: o.x_end, y_start: o.y_start,
                       y_end: o.y_end}};
  else {
    const e = {};
    for (const k of ["text", "width", "visible", "muted", "label"])
      if (k in o) e[k] = o[k];
    if (Object.keys(e).length) out[id] = e;
  }
}
process.stdout.write(JSON.stringify(out));
"""


# ---------------------------------------------------------------------------
# Running raw JavaScript under node
# ---------------------------------------------------------------------------

def run_js(source, *, timeout=120):
    """Run *source* under node; return ``json.loads`` of what it printed
    to stdout.  A non-zero exit is an ``AssertionError`` carrying stderr."""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(source)
        path = fh.name
    try:
        res = subprocess.run([node(), path], capture_output=True, text=True,
                             timeout=timeout)
        assert res.returncode == 0, res.stderr[:3000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# A session that carries state across moves
# ---------------------------------------------------------------------------

class JsSession:
    """Runs a saved page's CustomJS callbacks under node, carrying state
    across calls the way BokehJS does in a browser: what one callback
    leaves in a ``ColumnDataSource``, ``BooleanFilter``, ``Div`` or width
    is written back into the Python models before the next callback runs.

    *models* is an iterable of Bokeh ``Model``\\ s the session reports on
    through ``.state()`` even before any run reaches them -- typically
    ``r.filter_callbacks`` (each a ``CustomJS`` whose ``args`` reach the
    real sources, widgets, filters and Divs) or a plain list of sources
    and Divs.  Nothing is encoded until a run.
    """

    def __init__(self, models):
        self.models = list(models)
        self.runs = []
        self._seen = {}

    def set(self, widget, value):
        """``widget.value = value``; return the OLD value."""
        old = widget.value
        widget.value = value
        return old

    def run(self, callback, cb_obj=None, *, commit=True):
        """Run one ``CustomJS`` *callback* (its ``.code`` and ``.args``)."""
        assert isinstance(callback.code, str)
        return self.run_code(callback.code, callback.args, cb_obj,
                             commit=commit)

    def run_code(self, code, args, cb_obj=None, *, commit=True):
        """Run *code* with *args* (and optionally *cb_obj*) under node.

        Encodes ``dict(args)`` from the Python models AS THEY ARE NOW --
        so a chained call starts from what the previous call committed,
        not from the page's build-time data.  When *commit* is true (the
        default), every ``data``/``booleans``/``text``/``width`` node
        returns is written back into the real Python model (``None`` ->
        ``np.nan`` in a source's data, as the page's own snapshot holds
        missing values); with ``commit=False`` the Python models are left
        exactly as they were (a dry run).  Returns node's output, a
        ``{model id: {...}}`` dict, and appends it to ``self.runs``.
        """
        models, objs = {}, {}
        payload = {"models": models, "args": encode(dict(args), models, objs),
                   "code": code,
                   "cb_obj": encode(cb_obj, models, objs)
                   if cb_obj is not None else None}
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                         encoding="utf-8") as fh:
            # Parsed, not written as an object literal: in a literal a
            # "__proto__" key sets the prototype, as it does not in the
            # page, whose data BokehJS parses (module docstring).
            fh.write("const RAW = JSON.parse("
                     + json.dumps(json.dumps(payload)) + ");\n" + RUNNER)
            path = fh.name
        try:
            res = subprocess.run([node(), path], capture_output=True,
                                 text=True, timeout=120)
            assert res.returncode == 0, res.stderr[:3000]
            out = json.loads(res.stdout)
        finally:
            os.unlink(path)
        if commit:
            for mid, state in out.items():
                m = objs[mid]
                if "data" in state:
                    m.data = {c: [np.nan if v is None else v for v in col]
                              for c, col in state["data"].items()}
                elif "booleans" in state:
                    m.booleans = list(state["booleans"])
                elif "range" in state or "box" in state or "arrow" in state:
                    for k, v in (state.get("range") or state.get("box")
                                 or state.get("arrow")).items():
                        if isinstance(v, (int, float)) \
                                and not isinstance(v, bool):
                            setattr(m, k, float(v))
                elif "ticks" in state:
                    m.ticks = [float(v) for v in state["ticks"]]
                else:
                    # Each key commits on its own (WP-29 S12): a Div
                    # carries text AND visible, a renderer muted AND
                    # visible.
                    if "text" in state and isinstance(state["text"], str):
                        m.text = state["text"]
                    w = state.get("width")
                    if (isinstance(w, (int, float))
                            and not isinstance(w, bool)):
                        m.width = w
                    for k in ("visible", "muted"):
                        if isinstance(state.get(k), bool):
                            setattr(m, k, state[k])
                    lab = state.get("label")
                    if isinstance(lab, dict) and "value" in lab:
                        m.label = _bk_value(lab["value"])
            self._seen.update(objs)
        self.runs.append(out)
        return out

    def state(self):
        """``{"sources": {id: data}, "booleans": {id: list}, "divs": {id:
        text}, "widths": {id: width}, "muted": {id: bool}, "visible": {id:
        bool}, "labels": {id: text}}`` read from Python NOW, over the
        constructor's models and every model a committed run reached."""
        objs = {m.id: m for m in self.models}
        objs.update(self._seen)
        out = {"sources": {}, "booleans": {}, "divs": {}, "widths": {},
               "muted": {}, "visible": {}, "labels": {}}
        for mid, m in objs.items():
            if isinstance(m, ColumnDataSource):
                out["sources"][mid] = dict(m.data)
            elif isinstance(m, BooleanFilter):
                out["booleans"][mid] = list(m.booleans or [])
            elif isinstance(m, Div):
                out["divs"][mid] = m.text
            elif "width" in m.properties():
                out["widths"][mid] = m.width
            if isinstance(m, GlyphRenderer):
                out["muted"][mid] = bool(m.muted)
            if isinstance(m, (GlyphRenderer, Title, Div)):
                out["visible"][mid] = bool(m.visible)
            if isinstance(m, LegendItem):
                out["labels"][mid] = _label_text(m.label)
        return out

    def rows(self, source):
        """The row count of *source*, as Python holds it now."""
        data = source.data
        return len(next(iter(data.values()))) if data else 0

    def ids(self, source):
        """*source*'s ``_ROW_ID_COLUMN``, as Python holds it now, or
        ``None`` when the column is absent."""
        return source.data.get(dr._ROW_ID_COLUMN)


# ---------------------------------------------------------------------------
# X1: both twins' masks on the same columns
# ---------------------------------------------------------------------------

def mask_parity(df, filter_specs, widget_values, *, raw=False):
    """The saved page's ``dash_filter_mask`` (under node) and the served
    app's ``_dash_frame_filter_mask`` (pandas), run on the same *df*, the
    same *filter_specs* (the list ``filter_specs_json`` carries: one dict
    per widget, passed to both twins UNCHANGED -- any key a later section
    adds, such as S17's ``numeric``/``groups``, reaches both twins as
    given) and the same *widget_values* (one entry per spec: a bare value
    -- dropdown text, slider number, range ``(lo, hi)`` -- or a dict
    ``{"value", "start", "end"}``; a slider or range missing ``start``/
    ``end`` defaults to the column's finite min and max).

    Returns ``(js_mask, pandas_mask)``, each a ``list[bool]`` of
    ``len(df)``.  Never asserts; the caller compares them or records a
    difference.  With ``raw=True`` the JS side's columns are encoded with
    ``plain`` instead of ``dr._dash_json_value``, bypassing the saved
    snapshot's string/number coercion (the default is deliberate: it is
    the saved page's OWN encoding, so the parity reported is the page's).
    """
    to_json = plain if raw else dr._dash_json_value
    orig = {col: [to_json(v) for v in df[col].tolist()] for col in df.columns}

    js_widgets = []
    py_widgets = []
    for spec, wv in zip(filter_specs, widget_values):
        if isinstance(wv, dict):
            value = wv.get("value")
            start = wv.get("start")
            end = wv.get("end")
        else:
            value, start, end = wv, None, None
        varname = spec.get("varname")
        ftype = spec.get("type")
        if ftype in ("slider", "range") and (start is None or end is None):
            arr = (pd.to_numeric(df[varname], errors="coerce")
                  if varname in df.columns else pd.Series([], dtype=float))
            arr = arr[np.isfinite(arr)]
            col_min = float(arr.min()) if len(arr) else 0.0
            col_max = float(arr.max()) if len(arr) else 1.0
            if start is None:
                start = col_min
            if end is None:
                end = col_max
        js_widgets.append({"value": value, "start": start, "end": end})

        sentinel = spec.get("sentinel", "__all__")
        if ftype == "dropdown":
            w = Select(value=value, options=[(value, str(value))])
        elif ftype == "range":
            lo, hi = value
            w = RangeSlider(start=start, end=end, value=(lo, hi), step=1)
        elif ftype == "slider":
            w = Slider(start=start, end=end, value=value, step=1)
        else:
            raise ValueError("unknown filter type %r" % (ftype,))
        w._dash_var = varname
        w._dash_ftype = ftype
        w._dash_sentinel = sentinel
        py_widgets.append(w)

    script = (
        dr._DASH_FILTER_MASK_JS
        + "\nconst orig = " + json.dumps(orig)
        + ";\nconst specs = " + json.dumps(filter_specs)
        + ";\nconst widgets = " + json.dumps(js_widgets)
        + ";\nprocess.stdout.write(JSON.stringify("
        "dash_filter_mask(orig, specs, widgets)));"
    )
    js_mask = run_js(script)
    pandas_mask = dr._dash_frame_filter_mask(df, py_widgets).tolist()
    return js_mask, pandas_mask


# ---------------------------------------------------------------------------
# The histogram/kdensity recount fragment (C2)
# ---------------------------------------------------------------------------

def run_filter_js_block(kind, ac, vals, wts=None):
    """Run the histogram or kdensity branch of dash's REAL ``_FILTER_JS``
    on one aggregate config and the surviving values; return what it puts
    in the source (lifted, unchanged in behaviour, from
    test_statistical_helpers.py:820-856)."""
    js = dr._FILTER_JS
    helpers = js[js.index("function dash_pctl"):
                js.index("// agg_sources is a Bokeh model list")]
    if kind == "histogram":
        lo = js.index("if (ac.type === 'histogram') {")
        hi = js.index("} else if (ac.type === 'kdensity') {")
        block = js[lo + len("if (ac.type === 'histogram') {"):hi]
    else:
        lo = js.index("} else if (ac.type === 'kdensity') {")
        lo += len("} else if (ac.type === 'kdensity') {")
        end = js.index("src.data = { x: xs, y: ys };",
                       js.index("// DASH_KDE_RULE"))
        hi = js.index("src.change.emit();", end)
        block = js[lo:hi + len("src.change.emit();")]
    harness = (
        helpers
        + "\nconst ac = " + json.dumps(ac)
        + ";\nconst vals = " + json.dumps([float(v) for v in vals])
        + ";\nconst wts = " + (json.dumps([float(w) for w in wts])
                               if wts is not None else "null")
        + ";\nconst src = { data: null, change: { emit: () => {} } };"
        + "\nfor (let _i = 0; _i < 1; _i++) {\n" + block + "\n}"
        + "\nprocess.stdout.write(JSON.stringify(src.data));"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        res = subprocess.run([node(), path], capture_output=True, text=True,
                             timeout=60)
        assert res.returncode == 0, res.stderr[:2000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


def fit_helpers_js():
    """The JavaScript a fit branch of ``_FILTER_JS`` needs, run on its own
    (WP-31 F1): the display-format helpers (``dash_stata_value_of``),
    ``dash_own_col`` and ``dash_join_rebuild`` (declared above
    ``dash_pctl``), every helper from ``dash_pctl`` to the "agg_sources"
    comment, and ``ROW_ID``."""
    js = dr._FILTER_JS
    return (dr._DASH_FMT_JS + "\n"
            + js[js.index("function dash_own_col"):js.index("const ROW_ID = ")]
            + js[js.index("function dash_pctl"):
                 js.index("// agg_sources is a Bokeh model list")]
            + "\nconst ROW_ID = " + json.dumps(dr._ROW_ID_COLUMN) + ";\n")


def _floats(v):
    return "[" + ",".join("NaN" if not math.isfinite(float(e)) else repr(float(e))
                          for e in v) + "]"


def run_fit_js_block(ac, x, y, w=None, *, timed=False):
    """Run one fit branch of dash's REAL ``_FILTER_JS`` (WP-31 F1) on the
    kept rows *x*, *y* (Stata units) and weights *w*; return ``src.data``
    (with *timed*, ``{"data": src.data, "ms": node's own time}``).  The
    branch runs from its ``} else if (ac.type === '<type>') {`` line to the
    next branch or the ``// DASH_FIT_BRANCHES_END`` marker; the rows bypass
    ``dash_fit_rows`` (``run_fit_rows`` runs that alone)."""
    js = dr._FILTER_JS
    head = "} else if (ac.type === '%s') {" % ac["type"]
    lo = js.index(head) + len(head)
    nxt = js.find("} else if (ac.type === '", lo)
    end = js.index("// DASH_FIT_BRANCHES_END", lo)
    block = js[lo:nxt if (nxt != -1 and nxt < end) else end]
    harness = (fit_helpers_js()
               + "const ac = " + json.dumps(ac)
               + ";\nconst fx = " + _floats(x)
               + ";\nconst fy = " + _floats(y)
               + ";\nconst fw = " + (_floats(w) if w is not None else "null")
               + ";\nconst src = { data: null, change: { emit: () => {} } };"
               + "\nconst _t0 = process.hrtime.bigint();"
               + "\nfor (let _i = 0; _i < 1; _i++) {\n" + block + "\n}"
               + "\nconst _ms = Number(process.hrtime.bigint() - _t0) / 1e6;"
               + "\nprocess.stdout.write(JSON.stringify("
               + ("{data: src.data, ms: _ms}" if timed else "src.data")
               + "));")
    return run_js(harness)


def run_fit_rows(ac, data, keep=None):
    """``dash_fit_rows`` of ``_FILTER_JS`` on a ``{column: list}`` *data*
    object (a literal, so NaN stays NaN), each column picked at the row
    positions *keep* (a layer's ``member_ids``) when given."""
    pick = ("(c) => c" if keep is None else
            "(c) => c ? %s.map(i => c[i]) : c" % json.dumps(list(keep)))
    return run_js(fit_helpers_js() + "const d = " + json.dumps(data)
                  + ";\nprocess.stdout.write(JSON.stringify(dash_fit_rows("
                  + json.dumps(ac) + ", d, " + pick + ")));")
