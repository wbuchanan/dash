"""Both render modes' rows after a sequence of filter moves, for the Stata
certification blocks of section 17 (GAPS2 X1, E2): test_gaps2_truth.cscript
FT-01..FT-06 and test_e2e_filters.cscript FL-X1-1, FL-E2-1, FL-E2-2, and
of WP-29 section 07: test_e2e_filters.cscript QF-01, QF-02 (``layer_rows``)
and test_wp29_truth.cscript CQV-01..CQV-09 (``colour_keys``).

The cscript builds the data in Stata and hands it here through ``sfi``; this
module renders the saved page (its own filter callbacks run under node through
``js_runner.JsSession``) and the served app (its own Python callbacks), moves
the widgets, and returns what each figure and KPI card shows, so Stata can
compare it with its own ``count if`` and ``summarize``.  Nothing here calls
Stata.
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_adversarial_matrix import _load_app  # noqa: E402
from test_help_claims_3 import _card_value  # noqa: E402


from conftest import render_models  # noqa: E402


def frame_from_stata(varnames):
    """The current Stata dataset's *varnames* as a DataFrame and the set of
    string variables among them."""
    from sfi import Data
    cols, strings = {}, set()
    for v in varnames:
        idx = Data.getVarIndex(v)
        if Data.isVarTypeStr(idx):
            strings.add(v)
            cols[v] = [str(x) for x in Data.get(v)]
        else:
            vals = Data.get(v, missingval=np.nan)
            cols[v] = [float(x[0] if isinstance(x, list) else x) for x in vals]
    return pd.DataFrame(cols), strings


def _write(tmp, spec, df, strings):
    data = make_data_json(df)
    for s in strings:
        for key in ("variableIsString", "variableTypeIsString"):
            data["StataJSON"][key][s] = True
    sp = os.path.join(tmp, "spec.json")
    dp = os.path.join(tmp, "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _src(fig):
    from bokeh.models import GlyphRenderer
    [r] = [r for r in fig.renderers if isinstance(r, GlyphRenderer)]
    return r.data_source


def _state(figs, divs, texts_of):
    out = {}
    for f in figs:
        d = _src(f).data
        n = len(next(iter(d.values()))) if d else 0
        ys = [v for v in d.get("mpg", []) if v == v]
        out[f.title.text] = (n, float(np.mean(ys)) if ys else float("nan"))
    for name, text in texts_of(divs).items():
        out[name] = text
    return out


def saved(df, strings, spec, moves):
    """``moves``: [(filter index, value)], a value of None meaning "All" (a
    dropdown's sentinel, a range's full extent).  Returns the state after
    the last move."""
    tmp = tempfile.mkdtemp(prefix="ft_saved_")
    sp, dp = _write(tmp, spec, df, strings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    s = js_runner.JsSession(r.filter_callbacks)
    for fi, value in moves:
        w, cb = r.filter_widgets[fi], r.filter_callbacks[fi]
        if value is None:
            value = (getattr(w, "_dash_sentinel", None)
                     or (w.start, w.end))
        s.set(w, value)
        s.run(cb)
    return _state(r.figures.values(), r.kpi_divs,
                  lambda d: {k: _card_value(v.text, k) for k, v in d.items()}), r


def served(df, strings, spec, moves):
    from bokeh.document import Document
    from bokeh.models import Div
    tmp = tempfile.mkdtemp(prefix="ft_served_")
    sp, dp = _write(tmp, spec, df, strings)
    app = os.path.join(tmp, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "ft_%d" % os.getpid())
        doc = Document()
        ns["make_document"](doc)
        widgets = {w._dash_var: w for w in _walk(doc)
                   if hasattr(w, "_dash_var")}
        order = [f.get("varname") for f in spec["build_options"]["filters"]]
        for fi, value in moves:
            w = widgets[order[fi]]
            if value is None:
                value = (getattr(w, "_dash_sentinel", None)
                         or (w.start, w.end))
            w.value = value
            for key in ("value", "value_throttled"):
                for cb in list(w._callbacks.get(key, [])):
                    cb("value", None, value)
    figs = [m for m in _walk(doc) if type(m).__name__ == "figure"]
    divs = [m for m in _walk(doc) if isinstance(m, Div)]
    names = [k["name"] for k in spec.get("kpis", [])]

    def texts(ds):
        out = {}
        for d in ds:
            for n in names:
                v = _card_value(d.text, n)
                if v:
                    out[n] = v
        return out
    return _state(figs, divs, texts), doc


def _walk(doc):
    out = []
    for root in doc.roots:
        out.extend(root.references())
    return out


def scatter_graph(name, y, x):
    return {"plots": [{"type": "scatter", "yvar": y, "xvar": x,
                       "options": {}}],
            "graph_options": {"name": name, "title": name},
            "if_expr": "", "in_expr": ""}


def kpi(name, var="mpg"):
    return {"name": name, "stat": "count", "var": var, "fmt": "%9.0f",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter", "if_expr": "", "in_expr": ""}


def spec_of(graphs, filters, kpis=()):
    names = [g["graph_options"]["name"] for g in graphs] + [
        k["name"] for k in kpis]
    return {"graphs": graphs, "kpis": list(kpis),
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "",
                              "registry": " ".join(names),
                              "filters": list(filters)}}


def _figure_rows(root):
    """Rows drawn by each visible glyph renderer, per figure in layout
    order, as ``test_mode_parity._layout_tree`` profiles count them."""
    import test_mode_parity as tp
    figs = []
    tp._layout_tree(root, figs)
    return [[g["rows"] for g in f["glyphs"] if g["visible"]] for f in figs]


def layer_rows(spec_path, data_path, moves):
    """WP-29 P0.15 (test_e2e_filters.cscript QF-01, QF-02): the rows each
    layer draws in both modes after ``moves``, ``[(filter index, value)]``
    (a value of None meaning "All").

    Returns ``{"saved": [[rows per visible glyph renderer] per figure in
    layout order], "served": [...]}``.  The saved page runs its own filter
    callbacks under node; the served app runs its own Python callbacks.
    The filter order is the spec's ``build_options["filters"]``, or its
    ``filter`` text as dash.ado writes it.  Nothing
    here calls Stata.
    """
    from bokeh.document import Document
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(spec_path, data_path)
        render_models(r)
    s = js_runner.JsSession(r.filter_callbacks)
    for fi, value in moves:
        w, cb = r.filter_widgets[fi], r.filter_callbacks[fi]
        if value is None:
            value = (getattr(w, "_dash_sentinel", None)
                     or (w.start, w.end))
        s.set(w, value)
        s.run(cb)
    saved_rows = _figure_rows(r._last_layout_root)

    tmp = tempfile.mkdtemp(prefix="ft_layer_rows_")
    app = os.path.join(tmp, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(spec_path, data_path).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "ftl_%d" % os.getpid())
        doc = Document()
        ns["make_document"](doc)
        widgets = {w._dash_var: w for w in _walk(doc)
                   if hasattr(w, "_dash_var")}
        bo = spec["build_options"]
        # A spec dash.ado writes holds the filter() text, not the list.
        order = [f.get("varname") for f in (
            bo.get("filters") or dr._dash_parse_filter_raw(
                bo.get("filter", "") or "", warn=False))]
        for fi, value in moves:
            w = widgets[order[fi]]
            if value is None:
                value = (getattr(w, "_dash_sentinel", None)
                         or (w.start, w.end))
            w.value = value
            for key in ("value", "value_throttled"):
                for cb in list(w._callbacks.get(key, [])):
                    cb("value", None, value)
    return {"saved": saved_rows, "served": _figure_rows(doc.roots[0])}


def _keys_of(root):
    import colour_bins as cb
    out = []
    for f in cb._figures(root):
        out.append({
            "bars": [[float(lo), float(hi)] for lo, hi in cb.colour_bars(f)],
            "factors": [list(cb.colour_mapper(r).factors)
                        for r in cb.colour_renderers(f)
                        if hasattr(cb.colour_mapper(r), "factors")],
            "drawn": [cb.drawn_colour_values(r)
                      for r in cb.colour_renderers(f)],
            "keys": cb.colour_keys(f)})
    return out


def colour_keys(spec_path, data_path):
    """WP-29 P0.16 (test_wp29_truth.cscript CQV-01..CQV-09): each figure's
    colour keys in both modes, in layout order.

    Returns ``{"saved": [fig, ...], "served": [fig, ...]}``, each fig
    ``{"bars": [[low, high], ...], "factors": [[...] per colour-mapped
    renderer], "drawn": [[the colour value of each drawn row] per
    colour-mapped renderer], "keys": <ColorBars + Legends named
    dr._COLORVAR_LEGEND_NAME>}``.  Nothing here calls Stata.
    """
    from bokeh.document import Document
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(spec_path, data_path)
        render_models(r)
    saved_keys = _keys_of(r._last_layout_root)
    tmp = tempfile.mkdtemp(prefix="ft_colour_keys_")
    app = os.path.join(tmp, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(spec_path, data_path).build(app)
        with open(app, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "ftk_%d" % os.getpid())
        doc = Document()
        ns["make_document"](doc)
    return {"saved": saved_keys, "served": _keys_of(doc)}


def put(name, value):
    """A result into a Stata global, as text."""
    from sfi import Macro
    Macro.setGlobal(name, str(value))


# ---------------------------------------------------------------------------
# WP-29 section 12: test_e2e_filters.cscript SCU-01..SCU-03 (P0.17) and
# EW-01 (P0.18)
# ---------------------------------------------------------------------------

def fit_graph(name, y, x, ptype="lfit", options=None, if_expr=""):
    """A graph of one fitted layer, ``(<ptype> y x)`` (SCU-01, SCU-02)."""
    return {"plots": [{"type": ptype, "yvar": y, "xvar": x,
                       "options": dict(options or {}), "if_expr": if_expr}],
            "graph_options": {"name": name, "title": name},
            "if_expr": "", "in_expr": ""}


def bar_graph(name, y, x, ptype="bar", if_expr=""):
    """A graph of one bar layer, ``(<ptype> y x)`` (EW-01)."""
    return {"plots": [{"type": ptype, "yvar": y, "xvar": x, "options": {},
                       "if_expr": if_expr}],
            "graph_options": {"name": name, "title": name},
            "if_expr": "", "in_expr": ""}


def stale_state(r):
    """The saved page's stale cue as the renderer *r* holds it now
    (SCU-01, SCU-02): caption visibility per marked figure, ``muted`` of
    every renderer carrying ``_dash_frozen``, every legend label, and the
    status line's visibility and text."""
    from bokeh.models import Legend
    titles, muted, labels = [], [], []
    for fig in r.figures.values():
        titles += [t.visible for t in fig.above
                   if "dash_stale_cue" in (getattr(t, "tags", None) or [])]
        muted += [x.muted for x in fig.renderers
                  if hasattr(x, "_dash_frozen")]
        for side in (fig.center, fig.above, fig.below, fig.left, fig.right):
            for m in side:
                if isinstance(m, Legend):
                    labels += [getattr(i.label, "value", None)
                               for i in m.items]
    st = (r.filter_callbacks[0].args.get("stale_status")
          if r.filter_callbacks else None)
    return {"titles": titles, "muted": muted, "labels": labels,
            "status_visible": bool(st.visible) if st is not None else False,
            "status_text": st.text if st is not None else ""}


def served_stale_models(doc):
    """How many models of the served document carry a ``dash_stale*`` tag
    (SCU-01: the served app carries no cue)."""
    return sum(1 for m in doc.models
               if any(str(t).startswith("dash_stale")
                      for t in (getattr(m, "tags", None) or [])))


def _one_glyph(fig, kind):
    from bokeh.models import GlyphRenderer
    rs = [r for r in fig.renderers if isinstance(r, GlyphRenderer)
          and type(r.glyph).__name__ == kind]
    assert len(rs) == 1, "%d %s glyphs" % (len(rs), kind)
    return rs[0]


def line_ends(fig):
    """``(x[0], y[0], x[-1], y[-1])`` of *fig*'s single Line (SCU-01)."""
    d = _one_glyph(fig, "Line").data_source.data
    xs = [float(v) for v in d["x"]]
    ys = [float(v) for v in d["y"]]
    return xs[0], ys[0], xs[-1], ys[-1]


def vbar_width(fig):
    """The width *fig*'s single VBar draws (EW-01)."""
    w = _one_glyph(fig, "VBar").glyph.width
    return float(getattr(w, "value", w))


# ---------------------------------------------------------------------------
# WP-31 section 52: test_e2e_filters.cscript U52-01..U52-03 (H1)
# ---------------------------------------------------------------------------

def _u52_doc(page):
    """The Bokeh document JSON a saved page embeds, parsed with ``json``
    (its one ``<script type="application/json">`` element)."""
    at = page.index('<script type="application/json"')
    start = page.index(">", at) + 1
    return json.loads(page[start:page.index("</script>", start)])


def u52_keys(path):
    """``{widget type: [js_property_callbacks keys]}`` of the Slider,
    RangeSlider and Select models in the saved page at *path*."""
    with open(path, encoding="utf-8") as fh:
        doc = _u52_doc(fh.read())
    out = {}

    def walk(v):
        if isinstance(v, dict):
            if v.get("name") in ("Slider", "RangeSlider", "Select") \
                    and isinstance(v.get("attributes"), dict):
                cbs = v["attributes"].get("js_property_callbacks") or {}
                # A Bokeh map is {"type": "map", "entries": [[key, v]]}.
                keys = ([e[0] for e in cbs.get("entries", [])]
                        if cbs.get("type") == "map" else list(cbs))
                out.setdefault(v["name"], []).extend(keys)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(doc)
    return out


def u52_hashes_ok(path):
    """True when every inline script the page at *path* runs is named by
    the page's policy (``_dash_script_hashes`` against the CSP meta)."""
    import html as _html
    import re as _re
    with open(path, encoding="utf-8") as fh:
        page = fh.read()
    m = _re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]*)"',
                   page, _re.I)
    if m is None:
        return False
    policy = _html.unescape(m.group(1))
    hashes = dr._dash_script_hashes(page)
    return bool(hashes) and all(("'sha256-%s'" % h) in policy
                                for h in hashes)
