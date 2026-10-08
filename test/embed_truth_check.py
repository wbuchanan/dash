"""What a saved page and a served app hold, for the Stata certification
block of WP-29 section 14 (P0.11): test_wp29_truth.cscript ER-01..ER-08.

The cscript makes the page and the app with dash itself and hands their
paths here; this module decodes the page's embedded JSON documents
(base64 ndarrays included) or loads the app in-process, with no listener
(``test_adversarial_matrix._load_app``'s rule), and returns plain numbers
and lists, so Stata can compare them with its own ``count``,
``summarize``, ``levelsof`` and twoway's sersets.  Nothing here calls
Stata except ``put``, which sets a global.
"""
import base64
import gzip
import json
import os
import re
import sys
import warnings

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

_ROW = "__dash_row__"
_JSON_SCRIPT = re.compile(
    r'<script type="application/json"[^>]*>(.*?)</script>', re.S)
#: A layout(bs) page embeds its document through Bokeh's components().
_DOCS_JSON = re.compile(r"const docs_json = '(.*?)';\n", re.S)


def _decode(v):
    """A JSON value as a Python list when it is an array or an ndarray."""
    if isinstance(v, dict) and v.get("type") == "ndarray":
        arr = v.get("array") or {}
        if isinstance(arr, dict) and arr.get("type") == "bytes":
            raw = base64.b64decode(arr.get("data", ""))
            if raw[:2] == b"\x1f\x8b":     # Bokeh gzips a large array
                raw = gzip.decompress(raw)
            return np.frombuffer(raw, dtype=v.get("dtype", "float64")).tolist()
        return list(arr) if isinstance(arr, list) else []
    if isinstance(v, list):
        return v
    return []


def _objects(path):
    """``{id: object}`` of every model of every document in the page."""
    with open(path, encoding="utf-8") as fh:
        page = fh.read()
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "object" and "id" in o and "name" in o:
                out[o["id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for body in _JSON_SCRIPT.findall(page) + _DOCS_JSON.findall(page):
        try:
            walk(json.loads(body))
        except ValueError:
            continue
    return out


def _ref(objs, v):
    if isinstance(v, dict) and "id" in v:
        return objs.get(v["id"], v)
    return v


def _data(obj):
    """A ColumnDataSource object's columns, as ``{name: list}``."""
    d = (obj.get("attributes") or {}).get("data")
    if isinstance(d, dict) and "entries" in d:
        items = d["entries"]
    elif isinstance(d, dict):
        items = list(d.items())
    else:
        items = []
    return {k: _decode(v) for k, v in items}


def _sources(objs):
    return [o for o in objs.values() if o.get("name") == "ColumnDataSource"]


def _blank(v):
    if v is None:
        return True
    if isinstance(v, dict) and v.get("type") == "number":
        return str(v.get("value", "")).lower() == "nan"   # Bokeh's NaN
    if isinstance(v, float) and v != v:
        return True
    return isinstance(v, str) and v == ""


def page_rows(path):
    """``{"rows", "cells", "view_counts", "panels"}`` of a saved page:
    the distinct ``__dash_row__`` count over every source; per column, the
    number of distinct row ids carrying a value; per scatter renderer (in
    the page's order) the rows its view selects; each figure's by() label,
    or its title when it has none."""
    objs = _objects(path)
    ids = set()
    cells = {}
    for s in _sources(objs):
        d = _data(s)
        rid = d.get(_ROW)
        if rid is None:
            continue
        ids.update(int(x) for x in rid)
        for col, vals in d.items():
            if col == _ROW:
                continue
            got = cells.setdefault(col, set())
            for r, v in zip(rid, vals):
                if not _blank(v):
                    got.add(int(r))
    views = []
    for o in objs.values():
        if o.get("name") != "GlyphRenderer":
            continue
        a = o.get("attributes") or {}
        glyph = _ref(objs, a.get("glyph"))
        if not isinstance(glyph, dict) or glyph.get("name") != "Scatter":
            continue
        src = _ref(objs, a.get("data_source"))
        n = len(next(iter(_data(src).values()), [])) if isinstance(
            src, dict) else 0
        view = _ref(objs, a.get("view"))
        flt = _ref(objs, ((view or {}).get("attributes") or {}).get("filter"))
        if isinstance(flt, dict) and flt.get("name") == "BooleanFilter":
            b = _decode((flt.get("attributes") or {}).get("booleans"))
            views.append(sum(1 for x in b if x))
        else:
            views.append(n)
    panels = []
    for o in objs.values():
        if o.get("name") != "Figure":
            continue
        a = o.get("attributes") or {}
        # WP-30 P1.15a: a by() panel's label is a row of its own (a Title
        # named dash_by_label), no longer its title.
        rows = [_ref(objs, m) for m in (a.get("above") or []) +
                (a.get("below") or [])]
        lab = [m for m in rows if isinstance(m, dict)
               and (m.get("attributes") or {}).get("name") == "dash_by_label"]
        t = lab[0] if lab else _ref(objs, a.get("title"))
        if isinstance(t, dict):
            panels.append(str((t.get("attributes") or {}).get("text", "")))
    return {"rows": len(ids), "cells": {c: len(v) for c, v in cells.items()},
            "view_counts": views, "panels": panels}


def page_widgets(path):
    """``[(type, start, end, option labels)]`` of a saved page's filter
    widgets."""
    out = []
    for o in _objects(path).values():
        n = o.get("name")
        a = o.get("attributes") or {}
        if n in ("Slider", "RangeSlider"):
            out.append((n, a.get("start"), a.get("end"), []))
        elif n == "Select" and a.get("options") is not None:
            labs = [x[1] if isinstance(x, list) else x
                    for x in a.get("options") or []]
            out.append((n, None, None, labs))
    return out


def page_curve(path):
    """The y values of the page's first Line glyph (a lowess curve)."""
    objs = _objects(path)
    for o in objs.values():
        if o.get("name") != "GlyphRenderer":
            continue
        a = o.get("attributes") or {}
        glyph = _ref(objs, a.get("glyph"))
        if not isinstance(glyph, dict) or glyph.get("name") != "Line":
            continue
        y = (glyph.get("attributes") or {}).get("y")
        field = y.get("field") if isinstance(y, dict) else None
        src = _ref(objs, a.get("data_source"))
        if field and isinstance(src, dict):
            return [float(v) for v in _data(src).get(field, [])]
    return []


def _widget_state(w):
    if type(w).__name__ == "Select":
        return ("Select", None, None, [lab for _v, lab in w.options])
    return (type(w).__name__, float(w.start), float(w.end), [])


def served_state(app_path, moves=()):
    """``(before, after)``, each ``{"shared": rows, "labels": [...],
    "widgets": [...]}``, of the app at *app_path* loaded in-process;
    *moves* is ``[(variable, value)]`` fired through each widget's own
    callbacks."""
    from bokeh.document import Document
    from test_adversarial_matrix import _load_app
    import test_mode_parity as tp
    with open(app_path, encoding="utf-8") as fh:
        src = fh.read()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns = _load_app(src, "er_%d" % os.getpid())
        doc = Document()
        ns["make_document"](doc)

    def state():
        shared = None
        for r in doc.roots:
            for m in r.references():
                if getattr(m, "_dash_link_source", False):
                    shared = m
        labels = list(shared.data.get("index", [])) if shared else []
        return {"shared": len(labels), "labels": labels,
                "widgets": [_widget_state(w) for w in tp._widgets_of(doc)]}

    before = state()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for var, value in moves:
            for w in tp._widgets_of(doc):
                if getattr(w, "_dash_var", None) == var:
                    tp._fire(w, value)
    return before, state()


def put(name, value):
    """A result into a Stata global, as text."""
    from sfi import Macro
    Macro.setGlobal(name, str(value))
