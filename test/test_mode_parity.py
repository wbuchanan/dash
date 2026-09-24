"""The same command must draw the same dashboard in both modes.

`dash` has two renderers. ``DashRenderer`` builds Bokeh models directly;
``ServerAppBuilder`` emits a ``.py`` file that builds them again, in generated
string literals. They drifted, and nothing could tell:

* ``scheme()`` reached one and not the other, so every served plot was
  ``#1f77b4`` on white
* ``msize(large)`` meant 15px in one and 12px in the other -- two size maps
  for one set of Stata keywords
* ``dash histogram mpg`` drew 8 bars in one and 20 in the other, and 20 is
  not the answer Stata gives
* ``layout()``, ``tabs()``, ``filterposition()`` and ``subtitle()`` were
  read by one and ignored by the other
* ``link()`` shared a source in one and silently did nothing in the other

Each of those has its own regression test. This file is the standing guard:
it renders a corpus through BOTH paths and compares the models, so the next
divergence fails here rather than being found by a user.

**What this file used to miss.** GAPS.md D8: the corpus covered 17 of 38
plot types, set none of ``by()``, ``link()``, ``filter()``, ``tabs()`` or a
KPI, and the profile collected seven glyph style properties and nothing
else -- not the rows a glyph draws, not the tools, not the tooltips, not the
legend, not the axes, not where a figure sits in the document.  Every
divergence GAPS.md D2-D6 records was invisible to it.  The corpus now covers
every plot type the code dispatches (``TestTheCorpusIsComplete`` derives the
list from the dispatch tables, so a type cannot be added without an entry)
and every cross-cutting feature, and the profile is the whole document:
layout tree, widgets, KPI cards, and for every figure its glyphs with the
rows and coordinates they draw, annotations, legend, tools with their
tooltips, axes and chrome.

**What the wider profile found the day it was written** (each is fixed in
WP-12 or enumerated below with its reason): the served legend hid a layer
on click and the saved one did not; ``legend(position(6) rows(1))`` was
horizontal saved and vertical served; a served histogram titled its y axis
with the variable and the saved one titled it nothing, where Stata writes
"Density"; ``xlabel(2000(1000)4000)`` fixed the ticks saved and was ignored
served; ``yaxis(2)`` built a second axis saved and none served;
``colorvar()`` coloured by the variable saved and by the scheme served; a
``level(90)`` band was drawn at 95% served; a dropdown's option values were
``0``/``1`` saved and ``0.0``/``1.0`` served; a threshold slider was titled
"price >=" saved and "price" served; a KPI card sat before its graph saved
and after it served; the title header was two classed Divs saved and one
inline-styled Div served; a faceted graph inside ``tabs()`` was two panels
saved and one nested grid served.

**Legitimate differences are listed explicitly**, not tolerated by a loose
comparison -- a test that accepts unknown differences passes the next drift
too. See ``ALLOWED``.
"""
import importlib.util
import itertools
import json
import math
import os
import re
import sys
import tempfile
import warnings
from unittest import mock

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (Band, BoxAnnotation, Div, GridPlot, HoverTool,
                          Label, LabelSet, Legend, RangeSlider, Select,
                          Slider, Span, TabPanel, Tabs, ToolProxy, Widget)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json
from test_server_layer_defects import plot_for

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_parity_")

#: Ten observations, five per group, with a second numeric variable, an
#: integer-valued one, and a %td date.  ``foreign`` carries value labels so a
#: dropdown, a facet title and a tooltip all have a label to show.
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "rep": [3.0, 4.0, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0],
    "when": [15340.0, 15341.0, 15342.0, 15343.0, 15344.0, 15345.0, 15346.0,
             15347.0, 15348.0, 15349.0],
})
_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}

# ---------------------------------------------------------------------------
# Differences that are CORRECT, with the reason. Anything not listed here is
# a failure.  Each key is consulted by name in the code below; the guard on
# the list checks that.
# ---------------------------------------------------------------------------
ALLOWED = {
    "aggregate layers recompute live": (
        "The server recomputes histogram bins, fitted lines and kernel "
        "densities from the filtered rows on every widget move; standalone "
        "precomputes them and rescales in JS. The INITIAL values must still "
        "agree, which is what this file checks: the profile carries every "
        "coordinate a glyph draws at build time."
    ),
    "linked graphs share one source": (
        "Standalone always builds one ColumnDataSource per dashboard and "
        "filters with CDSView; the server builds one per graph unless "
        "link() says otherwise. Source identity is therefore not compared; "
        "the rows a renderer draws through its view are."
    ),
    "layout(bs) is standalone markup": (
        "The saved layout(bs) page is HTML: each bs row a flex row of "
        "db-col-lg-N cells, each cell one separately embedded Bokeh "
        "component, so it has no Bokeh layout root to walk.  The served "
        "document draws the same rows and spans as a Bokeh GridBox of 12 "
        "columns (WP-21 TR-21.4).  For a layout(bs) entry the saved tree is "
        "therefore read from the page's markup -- its cells in page order, "
        "each placed where a browser at 992px or more places it (a bs row "
        "starts a line; a cell that would carry the line past 12 columns "
        "starts the next) -- and compared with the served GridBox's "
        "children: content, row, column and spans.  What the markup does "
        "below 992px, where it reflows, has no served counterpart and is "
        "not compared; dash.sthlp says the served grid does not reflow.  "
        "Nor is the rest of the page, which is why a layout(bs) entry sets "
        "no filter(), tabs(), title() or subtitle(): the saved page puts "
        "its filters above the title (or, filterposition(left), beside "
        "it), and the served app -- as the saved page under every other "
        "layout -- below it."
    ),
}


def _allowed(key):
    """The reason for a tolerated difference, looked up where it is
    tolerated -- so the allowance list and the code that honours it cannot
    drift apart (``TestTheAllowanceListIsExplicit``)."""
    return ALLOWED[key]


# ---------------------------------------------------------------------------
# Spec construction
# ---------------------------------------------------------------------------

def _build_options(bo=None):
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
         "registry": "", "tabs": "", "filter_position": "top",
         "level": "95", "formats": {}}
    b.update(bo or {})
    return b


def _spec(plots=None, build_options=None, graph_options=None, graphs=None,
          kpis=None, if_expr="", in_expr=""):
    """A master spec with one graph (``plots``) or several (``graphs``).

    ``graphs`` is a list of ``(name, plots, graph_options, extra)`` where
    ``extra`` holds graph-level keys such as ``if_expr``.  The registry is
    the graphs then the KPIs, in that order, unless ``build_options`` names
    one -- which is the order ``dash.ado`` records for a user who registers
    a graph and then a KPI.
    """
    if graphs is None:
        graphs = [("g1", plots, graph_options,
                   {"if_expr": if_expr, "in_expr": in_expr})]
    gs, names = [], []
    for entry in graphs:
        name, gplots, go, extra = (list(entry) + [None, None])[:4]
        go = dict(go or {})
        go.setdefault("name", name)
        gd = {"name": name, "graph_options": go, "options": dict(go),
              "plots": gplots}
        gd.update(extra or {})
        gs.append(gd)
        names.append(name)
    bo = _build_options(build_options)
    if not bo["registry"]:
        bo["registry"] = " ".join(
            names + [k.get("name", "") for k in (kpis or [])])
    return {"graphs": gs, "kpis": list(kpis or []), "build_options": bo}


def _kpi(name="k1", stat="mean", var="mpg", **kw):
    k = {"name": name, "stat": stat, "var": var, "fmt": "", "title": name,
         "subtitle": "", "color": "", "bgcolor": "", "update": "filter"}
    k.update(kw)
    return k


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_DF, _VALUE_LABELS, _LABEL_NAMES), fh)
    return tag, sp, dp


def _standalone_page(spec):
    """(renderer, warnings, page) from the saved-dashboard renderer."""
    _, sp, dp = _write(spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return r, sorted(str(w.message) for w in caught), page


def _standalone(spec):
    """(renderer, warnings) from the saved-dashboard renderer."""
    r, caught, _page = _standalone_page(spec)
    return r, caught


def _served(spec):
    """(document, warnings) from the generated server app.

    The import is outside the warning capture: a generated app calls
    ``make_document(curdoc())`` at import time, and counting its warnings
    twice would misreport them.  Build-time warnings are captured with the
    document's -- the saved renderer raises everything in one ``render()``,
    so the two lists are comparable only as a whole.
    """
    tag, sp, dp = _write(spec)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms = importlib.util.spec_from_file_location(f"_parity_{tag}", ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return doc, sorted(str(w.message) for w in list(built) + list(caught))


# ---------------------------------------------------------------------------
# Profiles: everything a document shows, as plain comparable data
# ---------------------------------------------------------------------------

def _num(x):
    """A float rounded to six significant digits; the two modes compute
    through the same helpers, so anything looser than this is drift."""
    if isinstance(x, float):
        if math.isnan(x):
            return "nan"
        return float(f"{x:.6g}")
    return x


def _spec_of(v):
    """A Bokeh dataspec as ``("field", name)`` or ``("value", v)``."""
    if isinstance(v, str):
        return ("field", v)
    if isinstance(v, dict):
        if "field" in v:
            return ("field", v["field"])
        if "value" in v:
            return ("value", _num(v["value"]))
    f = getattr(v, "field", None)
    if isinstance(f, str):
        return ("field", f)
    val = getattr(v, "value", None)
    if val is not None and not hasattr(val, "field"):
        return ("value", _num(val))
    if isinstance(v, (int, float)):
        return ("value", _num(v))
    return ("other", str(v)[:40])


def _drawn(r):
    """``(data, row_indices)`` a renderer draws, honouring its CDSView.

    The source's identity is not part of the profile, only the rows seen
    through the view: ``_allowed("linked graphs share one source")``.

    A row the view names past the source's end is not drawn: BokehJS
    ignores such an index (it logs an out-of-bounds warning) and reads a
    BooleanFilter no further than the source's length.  A served view left
    counting the rows of an unfiltered source used to raise IndexError
    here instead of comparing unequal.
    """
    src = getattr(r, "data_source", None)
    if src is None:
        return None, None
    data = dict(src.data)
    first = next(iter(data), None)
    n = len(data[first]) if first else 0
    view = getattr(r, "view", None)
    filt = getattr(view, "filter", None) if view is not None else None
    idx = getattr(filt, "indices", None) if filt is not None else None
    if idx is None and filt is not None:
        bools = getattr(filt, "booleans", None)
        if bools is not None:
            idx = [i for i, b in enumerate(list(bools)[:n]) if b]
    if idx is None:
        return data, list(range(n))
    return data, [i for i in idx if 0 <= i < n]


_STYLE = ("marker", "size", "fill_color", "line_color", "line_width",
          "line_dash", "fill_alpha", "line_alpha", "angle")
_COORDS = ("x", "y", "left", "right", "top", "bottom", "x0", "x1", "y0",
           "y1", "xs", "ys", "base", "upper", "lower", "width", "height")


def _glyph_profile(fig):
    """Per glyph: its type, style, and the rows and coordinates it draws.

    This used to collect seven style properties and nothing else, so a
    served fit drawn from ten rows of the OLD line, a histogram binned over
    unqualified rows, or a pci layer that drew nothing at all, all compared
    equal to the saved dashboard as long as the colour matched.

    The coordinates are the ones drawn at build time; what a widget move
    does to them afterwards is ``_allowed("aggregate layers recompute
    live")`` and is compared by ``TestAFilterMoveAgrees`` against the saved
    renderer given the equivalent qualifier.
    """
    prof = []
    for r in fig.renderers:
        g = getattr(r, "glyph", None)
        if g is None:
            continue
        entry = {"type": type(g).__name__, "visible": r.visible}
        for attr in _STYLE:
            if not hasattr(g, attr):
                continue
            v = getattr(g, attr)
            if isinstance(v, (list, tuple)):
                v = list(v)
            if isinstance(v, (str, int, float, list)) or v is None:
                entry[attr] = v
            else:
                entry[attr] = _spec_of(v)
        data, idx = _drawn(r)
        entry["rows"] = len(idx) if idx is not None else None
        coords = {}
        if data is not None:
            for attr in _COORDS:
                if not hasattr(g, attr):
                    continue
                sp = _spec_of(getattr(g, attr))
                if sp[0] == "field" and sp[1] in data:
                    col = data[sp[1]]
                    vals = []
                    for i in idx:
                        v = col[i]
                        if hasattr(v, "__len__") and not isinstance(v, str):
                            vals.append(tuple(
                                _num(float(z)) if isinstance(z, (int, float))
                                else str(z) for z in v))
                        else:
                            try:
                                vals.append(_num(float(v)))
                            except (TypeError, ValueError):
                                vals.append(str(v))
                    coords[attr] = (sp[1], vals)
                else:
                    coords[attr] = sp
        entry["coords"] = coords
        prof.append(entry)
    return prof


def _label_of(item):
    lab = item.label
    if isinstance(lab, dict):
        return lab.get("value", lab)
    return getattr(lab, "value", str(lab))


def _sides(fig):
    return (list(fig.center) + list(fig.above) + list(fig.below) +
            list(fig.left) + list(fig.right))


def _drawn_text(v):
    """The text a LabelSet draws for one value, as the browser writes it.

    The page interpolates the value into a string, so a float 22.0 is drawn
    "22" and the string "22" is drawn "22": two columns that draw the same
    text compare equal, and a formatted "22.0" does not.
    """
    if isinstance(v, float):
        if math.isnan(v):
            return "NaN"
        if v.is_integer() and abs(v) < 1e21:
            return str(int(v))
        return repr(float(v))
    return str(v)


def _annotations(fig):
    """The annotations a figure carries, as comparable dicts.

    Glyph properties were compared and annotations were not, so the served
    marker labels could use a second size table, a different default font and
    different offsets (measured: 14px at (5, 5) against the renderer's 15px at
    (4, 0)), and the served note and caption could sit on top of each other,
    without this file noticing.  The legend is an annotation too: its keys,
    size, visibility, placement, orientation and click policy all drifted.

    WP-16 added the legend's side panel, columns, rows and label colour: a
    scheme's ``clockdir legend_position`` moves the legend into a panel and
    ``numstyle legend_cols`` sets its columns, and neither was recorded, so
    a placement applied in one mode only would have compared equal.
    """
    out = []
    panel = {}
    for side in ("center", "above", "below", "left", "right"):
        for r in getattr(fig, side):
            panel.setdefault(id(r), side)
    for r in _sides(fig):
        if isinstance(r, LabelSet):
            _, idx = _drawn(r)
            # WP-22: the angle mlabangle() sets and the text each label
            # draws -- the texts mlabformat() formats.  A LabelSet reads its
            # rows from `source', not `data_source', so the texts are taken
            # from there, as the browser draws them.
            _tf = _spec_of(r.text)
            _src = getattr(r, "source", None)
            _col = (list(_src.data.get(_tf[1], []))
                    if _tf[0] == "field" and _src is not None else [])
            out.append({"kind": "LabelSet", "text": _tf,
                        "font": r.text_font_size,
                        "color": _spec_of(r.text_color),
                        "x_offset": r.x_offset, "y_offset": r.y_offset,
                        "angle": _spec_of(r.angle),
                        "angle_units": r.angle_units,
                        "texts": [_drawn_text(v) for v in _col],
                        "rows": len(idx or [])})
        elif isinstance(r, Label):
            # Position too: the served caption sat at y = -12, where the
            # saved renderer's own comment says a Label is clipped and
            # never drawn, and this profile did not look.
            out.append({"kind": "Label", "text": r.text,
                        "font": r.text_font_size, "color": r.text_color,
                        "x": _num(float(r.x)), "y": _num(float(r.y)),
                        "x_units": r.x_units, "y_units": r.y_units})
        elif isinstance(r, Span):
            out.append({"kind": "Span", "dimension": r.dimension,
                        "location": _num(r.location), "color": r.line_color,
                        "width": r.line_width, "dash": list(r.line_dash or [])})
        elif isinstance(r, Legend):
            out.append({"kind": "Legend",
                        "items": [(_label_of(i),
                                   [type(x.glyph).__name__
                                    for x in i.renderers])
                                  for i in r.items],
                        "font": r.label_text_font_size,
                        "label_color": r.label_text_color,
                        "visible": r.visible,
                        "side": panel.get(id(r)),
                        "location": str(r.location),
                        "orientation": r.orientation,
                        "ncols": r.ncols, "nrows": r.nrows,
                        "click_policy": r.click_policy,
                        "background": r.background_fill_color,
                        "border": r.border_line_color})
        elif isinstance(r, BoxAnnotation):
            out.append({"kind": "BoxAnnotation",
                        "left": _num(r.left), "right": _num(r.right),
                        "top": _num(r.top), "bottom": _num(r.bottom),
                        "fill": r.fill_color, "alpha": r.fill_alpha})
        elif isinstance(r, Band):
            out.append({"kind": "Band"})
    return sorted(out, key=lambda d: json.dumps(d, sort_keys=True,
                                                default=str))


def _tools(fig):
    """Tool types, and for a hover its tooltips, formatters and scope.

    GAPS.md D2's hover findings -- no tooltip at all on a served bar, a
    served ``hover(foreign)`` ignored -- were invisible because tools were
    not collected.

    The toolbar's tools are kept in the order the figure holds them (WP-21):
    sorted, two toolbars holding the same tools in a different order
    compared equal.  The hover tools follow them, sorted.
    """
    out, hovers = [], []
    for t in fig.tools:
        e = {"type": type(t).__name__}
        if isinstance(t, HoverTool):
            tt = t.tooltips
            e["tooltips"] = (list(tt) if isinstance(tt, (list, tuple))
                             else str(tt))
            e["formatters"] = {k: str(v) for k, v in
                               (t.formatters or {}).items()}
            e["mode"] = t.mode
            rs = t.renderers
            e["renderers"] = (sorted(type(x.glyph).__name__ for x in rs)
                              if isinstance(rs, list) else str(rs))
            hovers.append(e)
        else:
            out.append(e)
    return out + sorted(hovers, key=lambda d: json.dumps(d, sort_keys=True,
                                                         default=str))


def _grid_toolbar(grid):
    """A grid's own toolbar: the side of the grid it sits on, and what it
    holds besides the proxies for its figures' tools -- the one save button
    ``gridplot()`` merges them into, with the file it writes (WP-21).
    BokehJS exports the whole grid through it.  The side is compared since
    a by() graph's cell on the saved layout(bs) page kept its toolbar on
    the right while the served cell's sat above."""
    return (grid.toolbar_location,
            [(type(t).__name__, getattr(t, "filename", None))
             for t in grid.toolbar.tools if not isinstance(t, ToolProxy)])


def _axes(fig):
    def one(a):
        ori = a.major_label_orientation
        return {"type": type(a).__name__, "label": a.axis_label,
                "formatter": type(a.formatter).__name__,
                "ticker": type(a.ticker).__name__,
                "ticks": ([_num(float(t)) for t in a.ticker.ticks]
                          if hasattr(a.ticker, "ticks") else None),
                "visible": a.visible,
                "label_font": a.axis_label_text_font_size,
                "tick_font": a.major_label_text_font_size,
                "orientation": (ori if isinstance(ori, str)
                                else _num(float(ori)))}

    def rng(r):
        e = {"type": type(r).__name__}
        for attr in ("start", "end"):
            v = getattr(r, attr, None)
            if isinstance(v, (int, float)):
                e[attr] = _num(float(v))
        if getattr(r, "flipped", None):
            e["flipped"] = True
        return e

    return {"x": [one(a) for a in fig.xaxis], "y": [one(a) for a in fig.yaxis],
            "x_range": rng(fig.x_range), "y_range": rng(fig.y_range),
            "extra_x": {k: rng(v) for k, v in fig.extra_x_ranges.items()},
            "extra_y": {k: rng(v) for k, v in fig.extra_y_ranges.items()},
            "x_scale": type(fig.x_scale).__name__,
            "y_scale": type(fig.y_scale).__name__}


def _chrome(fig):
    """The figure's frame: fills, grids, axis lines and text colours, title,
    proportions.

    WP-16 added the MINOR grid colour, the grid line width, the axis line
    and axis text colours and the title's font style.  The minor grid was
    the case in point: both modes drew one under every scheme, and a fix
    to one mode only would have been invisible here because only the major
    grid's colour was recorded.

    The adversarial review of WP-16 (22sep2026) mutated the standalone
    models after a render and found what this profile still could not see:
    the minor grid's WIDTH (only its colour was recorded), the figure's
    ``aspect_ratio`` / ``min_height`` / ``max_height`` (the served app
    takes the scheme's graphsize ratio through its own fallback), and the
    axis line's width (``linewidth axisline``, which the scheme now sets).
    """
    t = fig.title
    ad = fig.toolbar.active_drag

    def axis(a):
        return {"line_color": a.axis_line_color,
                "line_width": _num(float(a.axis_line_width)),
                "label_color": a.axis_label_text_color,
                "tick_color": a.major_label_text_color}

    ar = fig.aspect_ratio
    return {
        "background_fill_color": fig.background_fill_color,
        "border_fill_color": fig.border_fill_color,
        "outline_line_color": fig.outline_line_color,
        "xgrid": [g.grid_line_color for g in fig.xgrid],
        "ygrid": [g.grid_line_color for g in fig.ygrid],
        "xgrid_minor": [g.minor_grid_line_color for g in fig.xgrid],
        "ygrid_minor": [g.minor_grid_line_color for g in fig.ygrid],
        "xgrid_width": [g.grid_line_width for g in fig.xgrid],
        "ygrid_width": [g.grid_line_width for g in fig.ygrid],
        "xgrid_minor_width": [g.minor_grid_line_width for g in fig.xgrid],
        "ygrid_minor_width": [g.minor_grid_line_width for g in fig.ygrid],
        "xaxis": [axis(a) for a in fig.xaxis],
        "yaxis": [axis(a) for a in fig.yaxis],
        "title": t.text if t else "",
        "title_font": t.text_font_size if t else "",
        "title_color": t.text_color if t else "",
        "title_style": t.text_font_style if t else "",
        "width": fig.width, "height": fig.height,
        "aspect_ratio": (_num(float(ar)) if isinstance(ar, (int, float))
                         else ar),
        "min_height": fig.min_height, "max_height": fig.max_height,
        "sizing_mode": fig.sizing_mode,
        "toolbar_location": fig.toolbar_location,
        "active_drag": (type(ad).__name__ if ad not in (None, "auto")
                        else str(ad)),
        "output_backend": fig.output_backend,
    }


def _figure_profile(fig):
    return {"glyphs": _glyph_profile(fig), "annotations": _annotations(fig),
            "tools": _tools(fig), "axes": _axes(fig), "chrome": _chrome(fig)}


_CARD_OPEN = re.compile(r"<div\b([^>]*)>", re.S)


def _css_color_of(style):
    """The ``color:`` declaration of a style attribute's text, anchored at
    a declaration boundary so ``background-color`` never matches."""
    m = re.search(r"(?:^|[;\s])color\s*:\s*([^;\"]+)", style or "")
    return m.group(1).strip() if m else None


def _kpi_card(div):
    """``(name, shown value, class, inline background?, stylesheet css,
    value colour, title colour)`` from a KPI card Div, or None for any
    other Div (or text).

    This reduced a card to ``(name, value)``, so its styling was never
    compared.  WP-16 styles the card from the scheme -- the legend box's
    colours as a ``.db-kpi-card`` class rule on a stylesheet attached to
    the Div, and no inline background unless bgcolor() was given -- and a
    card styled that way in one mode only must fail here.

    The value's and the title's colours were still not recorded (the
    adversarial review of 22sep2026 turned the standalone value #212529
    and the title #6c757d without this file noticing), and they are the
    very defaults WP-16 moved to the scheme's ``color text``: the title
    and subtitle divs carry it, the value div carries color() or it.
    """
    text = div.text if isinstance(div, Div) else div
    if not isinstance(text, str) or "kpi_val_" not in text:
        return None
    rest = text[text.find("kpi_val_"):]
    rest = rest.replace("&gt;", ">").replace("&lt;", "<")
    name = rest[len("kpi_val_"):rest.find('"')]
    o = rest.find(">")
    c = rest.find("<", o)
    m = _CARD_OPEN.search(text)
    attrs = m.group(1) if m else ""
    cls = re.search(r'class="([^"]*)"', attrs)
    style = re.search(r'style="([^"]*)"', attrs)
    inline_bg = bool(style and re.search(
        r"(?:^|[;\s])background(?:-color)?\s*:", style.group(1)))
    sheets = getattr(div, "stylesheets", None) or []
    css = "".join(getattr(s, "css", "") or "" for s in sheets)
    mv = re.search(r'id="kpi_val_[^"]*"\s+style="([^"]*)"', text, re.S)
    value_color = _css_color_of(mv.group(1)) if mv else None
    # The title div is the first div INSIDE the card's outer div.
    inner = _CARD_OPEN.search(text, m.end()) if m else None
    title_style = (re.search(r'style="([^"]*)"', inner.group(1))
                   if inner else None)
    title_color = _css_color_of(title_style.group(1)) if title_style else None
    return (name, rest[o + 1:c].strip(), cls.group(1) if cls else None,
            inline_bg, css, value_color, title_color)


def _widget_profile(w):
    e = {"type": type(w).__name__, "title": getattr(w, "title", None)}
    for attr in ("start", "end", "step"):
        v = getattr(w, attr, None)
        if isinstance(v, (int, float)):
            e[attr] = _num(float(v))
    v = getattr(w, "value", None)
    if isinstance(v, (list, tuple)):
        e["value"] = [_num(float(x)) if isinstance(x, (int, float)) else x
                      for x in v]
    elif isinstance(v, (int, float)):
        e["value"] = _num(float(v))
    elif v is not None:
        e["value"] = v
    opts = getattr(w, "options", None)
    if opts is not None:
        e["options"] = [list(o) if isinstance(o, (list, tuple)) else o
                        for o in opts]
    e["disabled"] = getattr(w, "disabled", None)
    return e


def _layout_tree(m, figures):
    """The document as nested plain data.

    A figure becomes ``("figure", i)`` and its profile is appended to
    ``figures`` -- so the tree compares placement and the figures compare
    content, and a figure's position in the document pairs it with its twin
    in the other mode.
    """
    if (isinstance(m, tuple) and len(m) == 3
            and isinstance(m[1], int) and isinstance(m[2], int)):
        # A GridPlot child is (model, row, col).  The position is part of
        # the layout: three panels in one column and the same three in two
        # columns hold the same children, and compared equal until the
        # mutation that made the served app ignore by(, cols(#)) went
        # unnoticed here.
        return ("at", m[1], m[2], _layout_tree(m[0], figures))
    if (isinstance(m, tuple) and len(m) == 5
            and all(isinstance(x, int) for x in m[1:])):
        # A GridBox child with its spans, (model, row, col, row_span,
        # col_span): the served layout(bs) grid.  The spans are the layout
        # as much as the position is.
        return ("at", m[1], m[2], m[3], m[4], _layout_tree(m[0], figures))
    if isinstance(m, (list, tuple)):
        return [_layout_tree(x, figures) for x in m]
    if m is None:
        return None
    tn = type(m).__name__
    if tn == "figure":
        figures.append(_figure_profile(m))
        return ("figure", len(figures) - 1)
    if isinstance(m, Div):
        card = _kpi_card(m)
        return ("Div", ("kpi",) + card if card else ("text", m.text))
    if isinstance(m, TabPanel):
        return ("TabPanel", m.title, _layout_tree(m.child, figures))
    if isinstance(m, Tabs):
        return ("Tabs", [_layout_tree(t, figures) for t in m.tabs])
    if isinstance(m, Widget):
        return ("Widget", _widget_profile(m))
    if isinstance(m, GridPlot):
        # With its own toolbar: a grid whose save button wrote a different
        # file in one mode compared equal while only its children were read.
        return (tn, _grid_toolbar(m), _layout_tree(m.children, figures))
    kids = getattr(m, "children", None)
    return (tn, _layout_tree(kids, figures) if kids is not None else [])


# ---------------------------------------------------------------------------
# One render per corpus entry, shared by every comparison
# ---------------------------------------------------------------------------

_CACHE = {}

_BS_ROW = '<div class="db-row db-section">'
_BS_CELL = re.compile(r'db-col-lg-(\d+)[^"]*"><div id="[^"]*" '
                      r'data-root-id="([^"]+)"')


def _bs_markup_tree(r, page, figures, embedded=None):
    """The saved ``layout(bs)`` page's grid, read from the page itself.

    Each ``db-row`` is a Bootstrap row and each ``db-col-lg-N`` cell embeds
    one component by ``data-root-id``: a figure, a KPI card, a column of
    per-facet cards, or a by() graph's sub-grid.  *embedded* is every
    component the page embeds, by id, as the renderer handed them to
    ``components()``; the figures and cards alone could not name a sub-grid,
    which is how a corpus without a by() graph under layout(bs) came about.
    A cell is placed where a browser at 992px or more puts it: a row starts
    a new line, and a cell that would carry its line past 12 columns starts
    the next (flex-wrap).  The result is spelled as ``_layout_tree`` spells
    a GridBox, so it compares directly with the served grid.
    """
    models = {m.id: m for m in list(r.figures.values())
              + list(r.kpi_divs.values())}
    models.update(embedded or {})
    body = page[page.index('<div class="db-container">'):]
    cells, line = [], 0
    for chunk in body.split(_BS_ROW)[1:]:
        found = _BS_CELL.findall(chunk)
        used = 0
        for span, root in found:
            span = int(span)
            if used + span > 12:
                line, used = line + 1, 0
            assert root in models, (
                f"a layout(bs) cell embeds {root}, which the page was not "
                f"handed; this reader cannot name it")
            cells.append(("at", line, used, 1, span,
                          _layout_tree(models[root], figures)))
            used += span
        if found:
            line += 1
    return ("GridBox", cells)


def _render_pair(name, spec):
    """``{"std": ..., "srv": ...}`` -- each ``{"tree", "figures", "warnings",
    "widgets", "kpis"}``, and ``"bs"`` on the saved side when the page is
    ``layout(bs)`` markup -- rendered once per corpus entry."""
    if name in _CACHE:
        return _CACHE[name]
    # A layout(bs) page embeds its components one by one; they are read
    # where the renderer hands them over, so its markup reader can name
    # each cell's component.  Every other page embeds one root and never
    # calls components().
    with mock.patch.object(dr, "components", wraps=dr.components) as handed:
        r, std_w, page = _standalone_page(spec)
    embedded = {m.id: m for call in handed.call_args_list
                for m in call.args[0]}
    doc, srv_w = _served(spec)
    std_figs, srv_figs = [], []
    root = getattr(r, "_last_layout_root", None)
    if root is None:
        # No root to walk: the grid is read from the page's markup, and its
        # figures are taken in page order.
        _allowed("layout(bs) is standalone markup")
        std_tree = _bs_markup_tree(r, page, std_figs, embedded)
    else:
        std_tree = _layout_tree(root, std_figs)
    srv_tree = [_layout_tree(x, srv_figs) for x in doc.roots]
    if len(srv_tree) == 1:
        srv_tree = srv_tree[0]

    def leaves(tree, kind):
        out = []

        def visit(t):
            if isinstance(t, tuple) and t and t[0] == kind:
                out.append(t[1])
            if isinstance(t, (list, tuple)):
                for x in t:
                    visit(x)
        visit(tree)
        return out

    def kpis_of(tree):
        return [d[1:] for d in leaves(tree, "Div") if d[0] == "kpi"]

    if root is None:
        # The markup tree holds the grid alone; the widgets sit outside it.
        std_widgets = [_widget_profile(w) for w in r.filter_widgets]
    else:
        std_widgets = leaves(std_tree, "Widget")
    std_kpis = kpis_of(std_tree)
    pair = {
        "std": {"tree": std_tree, "figures": std_figs, "warnings": std_w,
                "widgets": std_widgets, "kpis": std_kpis,
                "bs": root is None},
        "srv": {"tree": srv_tree, "figures": srv_figs, "warnings": srv_w,
                "widgets": leaves(srv_tree, "Widget"),
                "kpis": kpis_of(srv_tree)},
    }
    _CACHE[name] = pair
    return pair


def _diff(a, b, path="", out=None):
    """``[(path, standalone, server), ...]`` where two profiles differ."""
    if out is None:
        out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", a.get(k, "<absent>"),
                            b.get(k, "<absent>")))
            else:
                _diff(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            out.append((f"{path}/len", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append((path, a, b))
    return out


def _explain(name, what, diffs):
    lines = [f"{name}: {what} differ in {len(diffs)} place(s)"]
    for p, x, y in diffs[:15]:
        lines.append(f"  {p or '/'}\n    standalone {x!r}\n    server     {y!r}")
    if len(diffs) > 15:
        lines.append(f"  ... {len(diffs) - 15} more")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------

def _case(name, plots=None, bo=None, go=None, graphs=None, kpis=None,
          if_expr="", in_expr="", marks=()):
    spec = _spec(plots, bo, go, graphs, kpis, if_expr, in_expr)
    return pytest.param(name, spec, id=name, marks=list(marks))


def _sc(**o):
    return plot_for("scatter", o)


CORPUS = [
    # ---- every plot type, bare -------------------------------------------
    *[_case(t, [plot_for(t)]) for t in (
        "scatter", "line", "connected", "area", "bar", "spike", "lfit",
        "qfit", "lfitci", "qfitci", "lowess", "lpoly", "lpolyci", "fpfit",
        "fpfitci", "histogram", "kdensity", "rarea", "rbar", "rspike",
        "rcap", "rline", "rconnected", "dot", "dropline", "rcapsym",
        "scatteri", "pcspike", "pcarrow", "pcbarrow", "pci", "pcscatter",
        "tsline", "tsrline", "mspline", "mband", "rscatter", "function",
        "pccapsym", "pcarrowi")],
    # WP-22: the two twoway types dash drew nowhere until then, with what
    # each honours beyond the bare glyphs -- pccapsym's marker labels (the
    # served pc source must carry the label column) and marker and line
    # options, pcarrowi's immediate labels and clock positions.
    # rep is none of plot_for's four coordinates, so the served source
    # carries the label column only through _dash_pc_source's label_var.
    _case("pccapsym with marker labels and styles",
          [plot_for("pccapsym", {"mlabel": "rep", "msymbol": "D",
                                 "mcolor": "red", "lcolor": "navy"})]),
    _case("pcarrowi with labels and clock positions",
          [plot_for("pcarrowi", {"lcolor": "maroon", "mlabcolor": "navy"},
                    values=[[20.0, 3000.0, 30.0, 4000.0, "A", 3],
                            [25.0, 2000.0, 22.0, 3500.0, "B", None],
                            [24.0, 2500.0, 26.0, 3200.0]])]),
    # scatteri and pci read their immediate values as twoway does
    # (test_immediate_values.py): a scatteri label at its own clock
    # position, at mlabposition()'s, at 12 o'clock for a clock position
    # that is not a whole number, and none for a point with a missing
    # coordinate, which is not drawn; pci draws no label at all.
    _case("scatteri with labels, clock positions and a missing point",
          [plot_for("scatteri", {"mlabcolor": "navy", "mlabposition": "6"},
                    values=[[20.0, 3000.0, "A", 9],
                            [30.0, 4000.0, "B", None],
                            [25.0, 3500.0, "C", 3.5],
                            [None, 2000.0, "D", 3],
                            [24.0, 2500.0]])]),
    _case("pci with labels, clock positions and a missing coordinate",
          [plot_for("pci", {"lcolor": "maroon"},
                    values=[[20.0, 3000.0, 30.0, 4000.0, "A", 3],
                            [25.0, 2000.0, 22.0, 3500.0],
                            [None, 2500.0, 26.0, 3200.0, "B", None]])]),
    # ---- schemes and style, the file's original beat ------------------------
    _case("scatter, s1mono", [_sc()], {"scheme": "s1mono"}),
    _case("scatter, economist", [_sc()], {"scheme": "economist"}),
    _case("scatter, session scheme only", [_sc()],
          {"session_scheme": "s1rcolor"}),
    _case("scatter, explicit msize(large)", [_sc(msize="large")]),
    _case("scatter, explicit mcolor", [_sc(mcolor="maroon")]),
    _case("scatter, explicit msymbol", [_sc(msymbol="triangle")]),
    _case("two scatters, scheme sequence",
          [_sc(), plot_for("scatter", yvar="weight", xvar="mpg")],
          {"scheme": "s2color"}),
    _case("line, economist", [plot_for("line")], {"scheme": "economist"}),
    _case("connected, s1mono", [plot_for("connected")], {"scheme": "s1mono"}),
    _case("scatter with a fit, economist", [_sc(), plot_for("lfit")],
          {"scheme": "economist"}),
    _case("mspline, economist", [plot_for("mspline")],
          {"scheme": "economist"}),
    _case("spike, economist", [plot_for("spike")], {"scheme": "economist"}),
    _case("dropline, economist", [plot_for("dropline")],
          {"scheme": "economist"}),
    # WP-16: what a scheme decides beyond the glyphs -- grids, text sizes
    # and colours, legend placement and columns, the KPI card's colours.
    _case("scheme s1color with a legend and a KPI",
          [_sc(), plot_for("lfit")], {"scheme": "s1color"}, kpis=[_kpi()]),
    _case("scheme economist with title, subtitle, note, caption and a legend",
          [_sc(), plot_for("line")], {"scheme": "economist"},
          {"title": "T", "subtitle": "S", "note": "N", "caption": "C"}),
    _case("scheme stcolor legend default placement",
          [_sc(), plot_for("lfit")], {"scheme": "stcolor"}),
    _case("kpi with explicit bgcolor under economist", [_sc()],
          {"scheme": "economist"}, kpis=[_kpi(bgcolor="#ecf0f1")]),
    # Review R4: a user rows() must not keep the scheme's ncols (s2color's
    # legend_cols is 2); one mode honouring rows(1) alone would show here.
    _case("legend(rows(1)) with three series under s2color",
          [_sc(), plot_for("line"), plot_for("lfit")], {"scheme": "s2color"},
          {"legend": "rows(1)"}),
    _case("line with an explicit line width", [plot_for("line",
                                                        {"lwidth": "thick"})]),
    _case("connected, marker and pattern options",
          [plot_for("connected", {"msymbol": "square", "msize": "large",
                                  "lpattern": "dash"})]),
    _case("bar, width and fill", [plot_for("bar", {"barwidth": "100",
                                                   "bfcolor": "red"})]),
    _case("rcap, line options", [plot_for("rcap", {"lwidth": "thick",
                                                   "lcolor": "navy"})]),
    # WP-22: twoway's connecting-line options.  They style the line in
    # place of lcolor()/lpattern()/lwidth() whatever the order, never the
    # markers, and on a CI type the fit line alone.
    _case("line, clcolor clpattern clwidth",
          [plot_for("line", {"clcolor": "maroon", "clpattern": "dash",
                             "clwidth": "thick"})]),
    _case("connected, lcolor beside clcolor",
          [plot_for("connected", {"lcolor": "navy", "clcolor": "maroon",
                                  "lwidth": "thin", "clwidth": "thick"})]),
    _case("lfitci, clcolor", [plot_for("lfitci", {"clcolor": "maroon"})]),
    _case("kdensity, clpattern", [plot_for("kdensity", {"clpattern": "dot"})]),
    _case("line, a colour clcolor() cannot name",
          [plot_for("line", {"clcolor": "notacolour", "lcolor": "navy"})]),
    _case("lpoly and lpolyci on the same data",
          [plot_for("lpoly"), plot_for("lpolyci")]),
    _case("lpoly, bwidth and degree",
          [plot_for("lpoly", {"bwidth": "400", "degree": "1"})]),
    _case("histogram, bin()", [plot_for("histogram", {"bin": "4"})]),
    _case("histogram, percent", [plot_for("histogram", {"percent": "percent"})]),
    _case("function, range and n",
          [plot_for("function", {"range": "0 5", "n": "7"})]),
    _case("lfitci at level(90)", [plot_for("lfitci")], {"level": "90"}),
    _case("qfitci at level(90)", [plot_for("qfitci")], {"level": "90"}),
    # WP-18: statistical sub-options and weights.  The served app copies
    # GlyphMapper, so a helper left out of _shared_stat_lines, or a weight
    # column the served layer source does not carry, shows up here first.
    _case("mspline, bands(5) n(4)",
          [plot_for("mspline", {"bands": "5", "n": "4"})]),
    _case("lowess, mean", [plot_for("lowess", {"mean": "mean"})]),
    _case("lowess, noweight logit adjust",
          [plot_for("lowess", {"noweight": "noweight", "logit": "logit",
                               "adjust": "adjust"},
                    yvar="foreign", xvar="weight")]),
    _case("lfitci, stdf", [plot_for("lfitci", {"stdf": "stdf"})]),
    _case("qfitci, stdr", [plot_for("qfitci", {"stdr": "stdr"})]),
    _case("histogram, discrete",
          [plot_for("histogram", {"discrete": "discrete"})]),
    _case("lfit [aw=price]",
          [plot_for("lfit", {"weight": "aweight", "wexp": "price"})]),
    _case("kdensity [fw=rep]",
          [plot_for("kdensity", {"weight": "fweight", "wexp": "rep"})]),
    _case("lpolyci at level(90)", [plot_for("lpolyci")], {"level": "90"}),
    _case("fpfitci at level(90)", [plot_for("fpfitci")], {"level": "90"}),
    _case("lfitci with a per-plot level",
          [plot_for("lfitci", {"level": "80"})]),
    _case("histogram, frequency",
          [plot_for("histogram", {"frequency": "frequency"})]),
    _case("histogram, fraction",
          [plot_for("histogram", {"fraction": "fraction"})]),
    _case("kdensity with an explicit ytitle", [plot_for("kdensity")], None,
          {"ytitle": "Density"}),
    # ---- marker labels and hover -------------------------------------------
    _case("scatter with marker labels", [_sc(mlabel="foreign")]),
    _case("scatter with marker labels and a size",
          [_sc(mlabel="foreign", mlabsize="large")]),
    _case("line with marker labels", [plot_for("line", {"mlabel": "foreign"})]),
    _case("rarea with marker labels",
          [plot_for("rarea", {"mlabel": "foreign"})]),
    # WP-22: mlabangle() and mlabformat(), which landed in the note as
    # unknown options and were drawn as if never written.
    _case("scatter with marker labels at mlabangle(45)",
          [_sc(mlabel="foreign", mlabangle="45")]),
    _case("connected with marker labels at mlabangle(vertical)",
          [plot_for("connected", {"mlabel": "rep", "mlabangle": "vertical"})]),
    _case("scatter with numeric marker labels in mlabformat(%9.1fc)",
          [_sc(mlabel="price", mlabformat="%9.1fc")]),
    _case("two layers labelling one variable in two formats",
          [_sc(mlabel="mpg", mlabformat="%9.2f"),
           plot_for("connected", {"mlabel": "mpg", "mlabformat": "%9.0f"})]),
    _case("a format mlabformat() cannot reproduce",
          [_sc(mlabel="mpg", mlabformat="%9.3g")]),
    # Marker labels where twoway draws them (test_marker_label_parity.py):
    # both ends of rcapsym, rconnected and rscatter, the first point of the
    # paired-coordinate types, and the value labels of a labelled variable
    # (foreign carries `origin' here) -- each drawn one way in both modes.
    _case("rcapsym with marker labels at both ends",
          [plot_for("rcapsym", {"mlabel": "rep"})]),
    _case("rconnected with marker labels at both ends",
          [plot_for("rconnected", {"mlabel": "rep"})]),
    _case("rscatter with value-labelled marker labels at both ends",
          [plot_for("rscatter", {"mlabel": "foreign"})]),
    _case("pcscatter with marker labels at the first point",
          [plot_for("pcscatter", {"mlabel": "rep", "mlabangle": "45"})]),
    _case("pcarrow with value-labelled marker labels",
          [plot_for("pcarrow", {"mlabel": "foreign"})]),
    _case("pcbarrow with marker labels", [plot_for("pcbarrow",
                                                   {"mlabel": "rep"})]),
    _case("bar with value-labelled marker labels in mlabformat()",
          [plot_for("bar", {"mlabel": "foreign", "mlabformat": "%9.2f"})]),
    _case("spike, tsline and rcap with mlabel(), which draw no label",
          [plot_for("spike", {"mlabel": "rep"}),
           plot_for("tsline", {"mlabel": "rep"}),
           plot_for("rcap", {"mlabel": "rep"})]),
    # The line options style lines and never the markers.
    _case("scatter and dropline with lcolor() lwidth() lalpha()",
          [_sc(lcolor="red", lwidth="vthick", lalpha="30"),
           plot_for("dropline", {"lcolor": "red", "lwidth": "vthick"})]),
    _case("hover()", [_sc()], None, {"hover": "foreign price"}),
    _case("hover() on a bar", [plot_for("bar")], None, {"hover": "foreign"}),
    _case("hover() on a linked graph", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc()], {"hover": "price"}),
                  ("g2", [plot_for("line")])]),
    _case("marker labels on a linked graph", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc()]),
                  ("g2", [plot_for("line", {"mlabel": "rep"})])]),
    _case("colorvar()", [_sc(colorvar="foreign")]),
    _case("colorvar() colordiscrete",
          [_sc(colorvar="foreign", colordiscrete="colordiscrete")]),
    _case("colorvar() on a continuous variable", [_sc(colorvar="price")]),
    _case("colorvar() with a palette",
          [_sc(colorvar="price", colpalette="magma", colornlevels="8")]),
    _case("colorvar() on a linked graph", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc(colorvar="foreign", colordiscrete="colordiscrete")]),
                  ("g2", [plot_for("line")])]),
    # ---- graph options -------------------------------------------------------
    _case("reference lines", [_sc()], None, {"xline": "3000", "yline": "20"}),
    _case("a styled reference line", [_sc()], None,
          {"xline": "3000, lcolor(red) lpattern(solid) lwidth(thick)"}),
    _case("note and caption", [_sc()], None, {"note": "N", "caption": "C"}),
    _case("note, caption and subtitle with sub-options", [_sc()], None,
          {"note": "N, size(large)", "caption": "C, color(red)",
           "subtitle": "S, size(small) span"}),
    _case("graph title with sub-options", [_sc()], None,
          {"title": "T, size(large) color(red) box"}),
    _case("legend with an unimplemented sub-option",
          [_sc(), plot_for("lfit")], None,
          {"legend": "position(6) span holes(1)"}),
    _case("xscale(range()) and yscale with an unimplemented sub-option",
          [_sc()], None, {"xscale": "range(1500 4500)",
                          "yscale": "reverse noline"}),
    _case("xline with an unimplemented sub-option", [_sc()], None,
          {"xline": "3000, lcolor(red) lstyle(foreground)"}),
    _case("xlabel with an unimplemented sub-option", [_sc()], None,
          {"xlabel": "#5, valuelabel", "ytitle": "Miles, orientation(vertical)"}),
    _case("graph title", [_sc()], None, {"title": "G"}),
    _case("graph title and subtitle with an ampersand", [_sc()], None,
          {"title": "R&D", "subtitle": "a & b"}),
    _case("xtitle and ytitle", [_sc()], None,
          {"xtitle": "Weight", "ytitle": "Miles"}),
    _case("xtitle with an ampersand", [_sc()], None, {"xtitle": "R&D spend"}),
    _case("xlabel and ylabel numlists", [_sc()], None,
          {"xlabel": "2000(1000)4000", "ylabel": "10(10)30"}),
    _case("xlabel(#8, grid) and ylabel(none)", [_sc()], None,
          {"xlabel": "#8, grid", "ylabel": "none"}),
    _case("xlabel(minmax) and ylabel with a format", [_sc()], None,
          {"xlabel": "minmax", "ylabel": ", format(%9.0fc)"}),
    _case("xlabel with labelled ticks and an angle", [_sc()], None,
          {"xlabel": '2000 "two" 4000 "four", angle(45)'}),
    _case("xtick()", [_sc()], None, {"xtick": "2500 3500"}),
    _case("xscale(log)", [_sc()], None, {"xscale": "log"}),
    _case("legend(off)", [_sc(), plot_for("lfit")], None, {"legend": "off"}),
    _case("legend(position(6) rows(1))", [_sc(), plot_for("lfit")], None,
          {"legend": "position(6) rows(1)"}),
    _case("legend(position(3))", [_sc(), plot_for("lfit")], None,
          {"legend": "position(3)"}),
    _case("legend(position(6) ring(0))", [_sc(), plot_for("lfit")], None,
          {"legend": "position(6) ring(0)"}),
    _case("legend(order(2 1))", [_sc(), plot_for("lfit")], None,
          {"legend": "order(2 1)"}),
    _case("legend(size(small))", [_sc(), plot_for("lfit")], None,
          {"legend": "size(small)"}),
    _case("legend(label(1 \"Cars\") cols(2))", [_sc(), plot_for("lfit")],
          None, {"legend": 'label(1 "Cars") cols(2)'}),
    _case("legend(on) for one series", [_sc()], None, {"legend": "on"}),
    _case("yaxis(2) on a second layer",
          [_sc(), plot_for("line", yvar="price", xvar="weight",
                           options={"yaxis": "2"})]),
    _case("yaxis(2) with ytitle2, ylabel2 and yscale2(log)",
          [_sc(), plot_for("line", yvar="price", xvar="weight",
                           options={"yaxis": "2"})], None,
          {"ytitle2": "Price", "ylabel2": "4000 8000", "yscale2": "log"}),
    _case("xaxis(2) on a second layer",
          [_sc(), plot_for("line", yvar="mpg", xvar="price",
                           options={"xaxis": "2"})]),
    _case("yaxis(2) under by()",
          [_sc(), plot_for("line", yvar="price", xvar="weight",
                           options={"yaxis": "2"})], None, {"by": "foreign"}),
    _case("xsize and ysize", [_sc()], None, {"xsize": "6", "ysize": "4"}),
    _case("aspectratio", [_sc()], None, {"aspectratio": "1"}),
    # ---- qualifiers (GAPS.md D3) ------------------------------------------
    _case("graph-level if", [_sc()], if_expr="price > 4500"),
    _case("graph-level in", [_sc()], in_expr="2/6"),
    _case("per-plot if", [_sc(), plot_for("scatter", if_expr="foreign==1")]),
    _case("per-plot if on a histogram",
          [plot_for("histogram", if_expr="foreign==1")]),
    _case("graph-level if under a fit", [_sc(), plot_for("lfit")],
          if_expr="price > 4500"),
    _case("a layer that draws nothing",
          [_sc(), plot_for("scatter", if_expr="foreign==7")]),
    # ---- by() (GAPS.md D4) -------------------------------------------------
    _case("scatter under by()", [_sc()], None, {"by": "foreign"}),
    _case("lfitci under by()", [plot_for("lfitci")], None, {"by": "foreign"}),
    _case("rarea under by()", [plot_for("rarea")], None, {"by": "foreign"}),
    _case("histogram under by(, total)", [plot_for("histogram")], None,
          {"by": "foreign, total"}),
    _case("function under by()", [plot_for("function")], None,
          {"by": "foreign"}),
    _case("pcspike under by()", [plot_for("pcspike")], None,
          {"by": "foreign"}),
    _case("by(, total cols(1))", [_sc()], None, {"by": "foreign, total cols(1)"}),
    _case("by() on two variables", [_sc()], None, {"by": "foreign rep"}),
    _case("by() with an unimplemented sub-option", [_sc()], None,
          {"by": "foreign, rows(2) compact"}),
    _case("by() with a graph-level if", [_sc()], None, {"by": "foreign"},
          if_expr="price > 4500"),
    _case("by() with marker labels and hover",
          [_sc(mlabel="rep")], None, {"by": "foreign", "hover": "price"}),
    # Review R10: the served panel title was html.escape(go["title"]) and
    # the saved one the PARSED text, so title("By") -- stored with its
    # quotes, as Stata's asis declaration keeps them -- served as
    # `&quot;By&quot; -- Domestic'.
    _case("by() with a graph title", [_sc()], None,
          {"by": "foreign", "title": '"By"'}),
    # ---- several graphs, link(), layout() -----------------------------------
    _case("two graphs", graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("two graphs, link()", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("link(_all)", bo={"link": "_all"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("a linked faceted graph", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc()], {"by": "foreign"}),
                  ("g2", [plot_for("line")])]),
    _case("layout(2 1)", bo={"layout": "2 1"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("layout() placement, 1-based", bo={"layout": "g2:1,1 g1:1,2"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("layout() placement, 0-based", bo={"layout": "g2:0,0 g1:0,1"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("layout(bs)", bo={"layout": "bs"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    # Spans, KPI cards, an order that is not the registry's and a row that
    # wraps: the saved markup puts g1 on a line of its own under g2, and the
    # served GridBox must as well (WP-21).
    _case("layout(bs: ...) with KPI cards and a wrapped row",
          bo={"layout": "bs: k2=3 k1=3 / g2=8 g1=6"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])],
          kpis=[_kpi(), _kpi(name="k2", stat="count")]),
    # A by() graph's cell: rep's three panels in the two columns cols(2)
    # asks for, with the cell's toolbar above them, in both modes.  The
    # saved page drew one row of three, its toolbar on the right.
    _case("layout(bs: ...) with a by(, cols(2)) graph",
          bo={"layout": "bs: g1=12 / g2=6"},
          graphs=[("g1", [_sc()], {"by": "rep, cols(2)"}),
                  ("g2", [plot_for("line")])]),
    # ---- filter() -----------------------------------------------------------
    _case("filter(, type(dropdown))", [_sc()],
          {"filter": "foreign, type(dropdown)"}),
    _case("filter(, type(range))", [_sc()], {"filter": "price, type(range)"}),
    _case("filter(, type(slider))", [_sc()], {"filter": "price, type(slider)"}),
    _case("filter(, label())", [_sc()],
          {"filter": 'rep, type(range) label("Repair record")'}),
    _case("filter() with a label the old gate refused", [_sc()],
          {"filter": 'price, type(range) label("R&D __ spend")'}),
    _case("filter() with an unknown type", [_sc()],
          {"filter": "price, type(bogus); foreign, type(dropdown)"}),
    _case("two filters, filterposition(left)", [_sc()],
          {"filter": "foreign, type(dropdown); price, type(range)",
           "filter_position": "left"}),
    _case("a filter on a linked pair",
          bo={"link": "g1 g2", "filter": "foreign, type(dropdown)"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("a filter on a faceted graph", [_sc()],
          {"filter": "price, type(range)"}, {"by": "foreign"}),
    # ---- tabs() --------------------------------------------------------------
    # Groups are separated by "/"; "A: g1; B: g2" was one tab holding g2.
    _case("tabs()", bo={"tabs": "A: g1 / B: g2"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("tabs() with an unassigned item", bo={"tabs": "A: g1"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])]),
    _case("a faceted graph in a tab", bo={"tabs": "A: g1"},
          graphs=[("g1", [_sc()], {"by": "foreign"}),
                  ("g2", [plot_for("line")])]),
    # ---- KPI cards ------------------------------------------------------------
    _case("a KPI card", [_sc()], kpis=[_kpi()]),
    _case("a KPI with fmt(%12.0fc)", [_sc()],
          kpis=[_kpi(var="price", stat="sum", fmt="%12.0fc")]),
    _case("a KPI with no fmt()", [_sc()], kpis=[_kpi(var="price")]),
    _case("a KPI with its own if", [_sc()], kpis=[_kpi(if_expr="foreign==1")]),
    _case("a KPI with its own in", [_sc()], kpis=[_kpi(in_expr="1/3")]),
    _case("a KPI updated by brush", [_sc()],
          kpis=[_kpi(update="brush", update_graph="g1")]),
    _case("a percentile KPI", [_sc()], kpis=[_kpi(stat="p50")]),
    _case("a styled count KPI", [_sc()],
          kpis=[_kpi(stat="count", title="N", subtitle="obs", color="white",
                     bgcolor="#2c3e50")]),
    _case("a KPI on a faceted graph", [_sc()], None, {"by": "foreign"},
          kpis=[_kpi()]),
    # A by() graph named after the KPI's update() mode: the saved page read
    # the mode as the graph's name and drew a card per panel; the served
    # app drew one card.  One card in both modes (test_keyword_names.py).
    _case("a KPI beside a by() graph named filter",
          graphs=[("filter", [_sc()], {"by": "foreign"})], kpis=[_kpi()]),
    _case("a KPI in a tab", bo={"tabs": "A: g1 k1"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])],
          kpis=[_kpi()]),
    _case("a KPI registered before its graph", bo={"registry": "k1 g1"},
          graphs=[("g1", [_sc()])], kpis=[_kpi()]),
    _case("a KPI registered between two graphs", bo={"registry": "g1 k1 g2"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])],
          kpis=[_kpi()]),
    # ---- title, subtitle, header -----------------------------------------------
    _case("title and subtitle", [_sc()], {"title": "T", "subtitle": "S"}),
    _case("a title that needs escaping", [_sc()],
          {"title": "R&D <b>spend</b>", "subtitle": "a < b"}),
    # ---- the immediate path's own spec shape ------------------------------------
    # `dash scatter mpg weight, saving()' writes exactly this (dash.ado, the
    # immediate master_json): one graph with NO name key, graph_options
    # holding only saving(), no kpis, no registry, layout "1 1".  Every other
    # entry here is named, which is how an ordering helper that dropped the
    # empty name shipped a saved dashboard with no figure and rc 0 -- the
    # certification suite caught it, this file did not.
    pytest.param(
        "an unnamed immediate graph",
        {"graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                "xvar": "weight", "options": {},
                                "if_expr": "", "in_expr": ""}],
                     "graph_options": {"saving": "/tmp/x.html"},
                     "if_expr": "", "in_expr": ""}],
         "build_options": {"layout": "1 1", "theme": "",
                           "session_scheme": "stcolor", "level": "95",
                           "formats": {"mpg": "%8.0g", "weight": "%8.0gc"}}},
        id="an unnamed immediate graph"),
    # ---- everything at once ---------------------------------------------------
    _case("everything at once",
          bo={"link": "g1 g2",
              "filter": "foreign, type(dropdown); price, type(range)",
              "tabs": "A: g2", "title": "T", "subtitle": "S",
              "scheme": "economist"},
          graphs=[("g1", [_sc(), plot_for("lfit")],
                   {"by": "foreign", "hover": "price"}),
                  ("g2", [plot_for("line", {"mlabel": "rep"})],
                   {"title": "Two"})],
          kpis=[_kpi(fmt="%9.1f"),
                _kpi(name="k2", stat="count", update="brush",
                     update_graph="g2")]),
]


#: Dates: a KNOWN server gap (BUGS.md, "The generated server app has no date
#: handling at all").  These entries run every comparison the corpus does;
#: the ones the gap breaks are asserted to STILL FAIL, so closing the gap
#: fails here until the entry is moved into CORPUS -- a hand-made strict
#: xfail, kept explicit because an ``xfail`` mark on the whole entry would
#: hide which comparisons the gap does and does not affect.
DATE_CORPUS = [
    _case("a date on the x axis",
          [plot_for("line", yvar="mpg", xvar="when")],
          {"formats": {"when": "%td"}}),
    _case("a date-valued KPI", [_sc()], {"formats": {"when": "%td"}},
          kpis=[_kpi(stat="max", var="when")]),
]

#: Which comparison each date entry is known to fail.
_DATE_GAP = {
    "a date on the x axis": {"glyphs", "axes", "tools"},
    "a date-valued KPI": {"tree", "kpi"},
}

#: The entries a report is the point of, with the report each must make.
#: test_same_warnings compared the two modes' lists alone, so an entry
#: whose report both modes stopped making compared [] with [] and passed.
#: Measured 24sep2026: these eleven are every entry that reports anything
#: but a layer drawn empty (the lpoly entries' "drew nothing" is not what
#: they exist for).
_MUST_WARN = {
    "line, a colour clcolor() cannot name":
        "dash: clcolor(notacolour) is not a recognised colour",
    "a format mlabformat() cannot reproduce":
        "dash: mlabformat(%9.3g) is not a display format dash reproduces",
    "scatteri with labels, clock positions and a missing point":
        "dash: scatteri clock position(s) 3.5 are not a whole number",
    "note, caption and subtitle with sub-options":
        "dash: subtitle() sub-option(s) not implemented and ignored: span",
    "graph title with sub-options":
        "dash: title() sub-option(s) not implemented and ignored: box",
    "legend with an unimplemented sub-option":
        "dash: legend() sub-option(s) not implemented and ignored: "
        "span holes(1)",
    "xscale(range()) and yscale with an unimplemented sub-option":
        "dash: yscale() sub-option(s) not implemented and ignored: noline",
    "xline with an unimplemented sub-option":
        "dash: xline() sub-option(s) not implemented and ignored: "
        "lstyle(foreground)",
    "xlabel with an unimplemented sub-option":
        "dash: xlabel() sub-option(s) not implemented and ignored: "
        "valuelabel",
    "by() with an unimplemented sub-option":
        "dash: by() sub-option(s) not implemented and ignored: "
        "rows(2) compact",
    "filter() with an unknown type":
        "dash: filter(price, type(bogus)): type() must be one of",
}

#: The filter types that build a widget (dash.sthlp); a filter() group of
#: any other type is reported and builds none.
_WIDGET_TYPES = ("dropdown", "range", "slider")


def _widgets_wanted(spec):
    """How many filter widgets *spec*'s filter() builds: one per group whose
    type() is one of _WIDGET_TYPES, or that names no type."""
    groups = [g for g in re.split(r"\|\||;",
                                  spec["build_options"].get("filter") or "")
              if g.strip()]
    n = 0
    for g in groups:
        t = re.search(r"\btype\((\w+)\)", g)
        n += (t is None) or (t.group(1) in _WIDGET_TYPES)
    return n


class _Agree:
    """The comparisons; parametrised by the classes below."""

    def test_same_document_tree(self, name, spec):
        """Where every figure, card and widget sits, in one tree.

        A ``layout(bs)`` page has no Bokeh tree: its grid is read from the
        page's markup (``ALLOWED``), and it is the grid alone -- so a
        ``layout(bs)`` entry must not carry what sits outside it, and its
        served document must be that grid and nothing else.
        """
        pair = _render_pair(name, spec)
        if pair["std"]["bs"]:
            bo = spec["build_options"]
            outside = [k for k in ("filter", "tabs", "title", "subtitle")
                       if bo.get(k)]
            assert not outside, (
                f"{name}: a layout(bs) entry compares the grid alone, and "
                f"sets {outside}: "
                + _allowed("layout(bs) is standalone markup"))
        diffs = _diff(pair["std"]["tree"], pair["srv"]["tree"])
        assert not diffs, _explain(name, "document trees", diffs)

    def test_same_number_of_figures(self, name, spec):
        pair = _render_pair(name, spec)
        assert len(pair["std"]["figures"]) == len(pair["srv"]["figures"]), (
            f"{name}: standalone {len(pair['std']['figures'])} figures, "
            f"server {len(pair['srv']['figures'])}")

    def _each(self, name, spec, key):
        pair = _render_pair(name, spec)
        std, srv = pair["std"]["figures"], pair["srv"]["figures"]
        assert len(std) == len(srv), f"{name}: figure counts differ"
        for i, (a, b) in enumerate(zip(std, srv)):
            diffs = _diff(a[key], b[key])
            assert not diffs, _explain(name, f"figure {i} {key}", diffs)

    def test_same_glyphs(self, name, spec):
        """Every glyph: type, style, rows drawn, coordinates drawn.

        This used to assert four of the seven collected properties, and only
        on Scatter glyphs, so the file was green while the served app drew
        area fills at 0.4 where standalone draws 1.0, histogram bars with a
        white 1.5px outline that standalone does not draw, and faceted
        markers at a fixed size 6 whatever the scheme asked for.
        """
        self._each(name, spec, "glyphs")

    def test_same_annotations(self, name, spec):
        self._each(name, spec, "annotations")

    def test_same_tools(self, name, spec):
        self._each(name, spec, "tools")

    def test_same_axes(self, name, spec):
        self._each(name, spec, "axes")

    def test_same_chrome(self, name, spec):
        pair = _render_pair(name, spec)
        std, srv = pair["std"]["figures"], pair["srv"]["figures"]
        assert len(std) == len(srv), f"{name}: figure counts differ"
        for i, (a, b) in enumerate(zip(std, srv)):
            # toolbar_location included under layout(bs) as well: the served
            # GridBox is not a gridplot, so a figure keeps its own toolbar
            # there, as it does embedded on its own in the saved page.
            diffs = _diff(a["chrome"], b["chrome"])
            assert not diffs, _explain(name, f"figure {i} chrome", diffs)

    def test_same_kpi_cards(self, name, spec):
        pair = _render_pair(name, spec)
        # One card per KPI the spec holds, found in the saved document:
        # a _kpi_card that stopped matching made every entry compare []
        # with [].
        cards = sorted(k[0] for k in pair["std"]["kpis"])
        assert cards == sorted(k["name"] for k in spec.get("kpis", [])), (
            f"{name}: the saved document's KPI cards are {cards}")
        assert pair["std"]["kpis"] == pair["srv"]["kpis"], (
            f"{name}: KPI cards differ\n  standalone {pair['std']['kpis']}"
            f"\n  server     {pair['srv']['kpis']}")

    def test_same_widgets(self, name, spec):
        pair = _render_pair(name, spec)
        # One widget per filter() group that builds one, likewise.
        got = len(pair["std"]["widgets"])
        assert got == _widgets_wanted(spec), (
            f"{name}: the saved document has {got} filter widget(s), its "
            f"filter() builds {_widgets_wanted(spec)}")
        diffs = _diff(pair["std"]["widgets"], pair["srv"]["widgets"])
        assert not diffs, _explain(name, "filter widgets", diffs)

    def test_same_warnings(self, name, spec):
        """A report one mode makes and the other does not is a divergence
        too: GAPS.md D6 was exactly that."""
        pair = _render_pair(name, spec)
        assert pair["std"]["warnings"] == pair["srv"]["warnings"], (
            f"{name}: warnings differ\n  standalone {pair['std']['warnings']}"
            f"\n  server     {pair['srv']['warnings']}")
        # ...and an entry that exists for a report makes it (_MUST_WARN).
        want = _MUST_WARN.get(name)
        if want is not None:
            assert [w for w in pair["std"]["warnings"] if want in w], (
                f"{name}: neither mode reported {want!r}: "
                f"{pair['std']['warnings']}")

    def test_the_profile_is_not_empty(self, name, spec):
        """Guards the guard: comparing two empty lists proves nothing."""
        pair = _render_pair(name, spec)
        figs = pair["std"]["figures"]
        assert figs, f"{name}: no figures collected, so nothing was compared"
        for f in figs:
            assert f["glyphs"], f"{name}: a figure with no glyphs"
            for g in f["glyphs"]:
                assert g["rows"] is not None and g["coords"], (
                    f"{name}: a glyph with no drawn rows or coordinates")


@pytest.mark.parametrize("name,spec", CORPUS)
class TestTheTwoModesAgree(_Agree):
    pass


def test_every_must_warn_entry_is_in_the_corpus():
    """A renamed entry would leave its _MUST_WARN line checking nothing."""
    names = {p.values[0] for p in CORPUS + DATE_CORPUS}
    assert set(_MUST_WARN) <= names, sorted(set(_MUST_WARN) - names)


@pytest.mark.parametrize("name,spec", DATE_CORPUS)
class TestDatesAreAKnownServerGap(_Agree):
    """See ``DATE_CORPUS``: the gap's comparisons must still fail."""

    def _gap(self, name, what, run):
        if what not in _DATE_GAP.get(name, ()):
            run()
            return
        with pytest.raises(AssertionError):
            run()
        pytest.xfail(f"{name}: {what} -- BUGS.md, the generated server app "
                     f"has no date handling; still open, as recorded")

    def test_same_document_tree(self, name, spec):
        self._gap(name, "tree",
                  lambda: _Agree.test_same_document_tree(self, name, spec))

    def test_same_glyphs(self, name, spec):
        self._gap(name, "glyphs",
                  lambda: _Agree.test_same_glyphs(self, name, spec))

    def test_same_axes(self, name, spec):
        self._gap(name, "axes", lambda: _Agree.test_same_axes(self, name, spec))

    def test_same_tools(self, name, spec):
        self._gap(name, "tools",
                  lambda: _Agree.test_same_tools(self, name, spec))

    def test_same_kpi_cards(self, name, spec):
        self._gap(name, "kpi",
                  lambda: _Agree.test_same_kpi_cards(self, name, spec))

    def test_every_gap_entry_is_still_needed(self, name, spec):
        assert name in _DATE_GAP, f"{name} has no recorded gap"


# ---------------------------------------------------------------------------
# After a widget moves: the served document against the saved one given the
# same rows as a qualifier
# ---------------------------------------------------------------------------

def _widgets_of(doc):
    out = []
    seen = set()

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    visit(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, Widget) and hasattr(m, "_dash_var"):
            out.append(m)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    for root in doc.roots:
        visit(root)
    return out


def _fire(widget, value):
    """Set the widget and run the app's own change callbacks, the way Bokeh
    would after a browser event.  A callback reads ``widget.value``, so the
    value is set first."""
    widget.value = value
    for key in ("value", "value_throttled"):
        for cb in list(widget._callbacks.get(key, [])):
            cb("value", None, value)


def _served_after_move(spec, move):
    """Figure profiles and KPI cards of the served document after one
    widget move.  ``move`` is ``(widget type, value)``; for a Select the
    value is the LABEL of the option to pick, so the test does not depend
    on how the option's raw value is spelled."""
    doc, _ = _served(spec)
    kind, want = move
    widgets = [w for w in _widgets_of(doc) if type(w).__name__ == kind]
    assert widgets, f"no {kind} widget in the served document"
    w = widgets[0]
    if isinstance(w, Select):
        raw = [v for v, lab in w.options if lab == want]
        assert raw, f"no option labelled {want!r}: {w.options}"
        _fire(w, raw[0])
    else:
        _fire(w, want)
    figs = []
    _layout_tree(doc.roots[0], figs)
    kpis = [_kpi_card(getattr(m, "text", None)) for m in _walk_models(doc)
            if isinstance(m, Div) and _kpi_card(getattr(m, "text", ""))]
    return figs, kpis


def _walk_models(doc):
    out, seen = [], set()

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    visit(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        out.append(m)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    for root in doc.roots:
        visit(root)
    return out


def _saved_with_qualifier(spec, if_expr):
    """The saved renderer's figures and cards for ``spec`` with ``if_expr``
    added to every graph and every KPI -- the rows the widget selects."""
    q = json.loads(json.dumps(spec))
    q["build_options"]["filter"] = ""
    for g in q["graphs"]:
        own = (g.get("if_expr") or "").strip()
        g["if_expr"] = f"({own}) & ({if_expr})" if own else if_expr
    for k in q["kpis"]:
        own = (k.get("if_expr") or "").strip()
        k["if_expr"] = f"({own}) & ({if_expr})" if own else if_expr
    r, _ = _standalone(q)
    figs = []
    _layout_tree(r._last_layout_root, figs)
    return figs, [_kpi_card(d.text) for d in r.kpi_divs.values()]


_MOVES = [
    ("dropdown to Foreign", "foreign, type(dropdown)", ("Select", "Foreign"),
     "foreign == 1"),
    ("range to 4500-11385", "price, type(range)",
     ("RangeSlider", (4500.0, 11385.0)), "price >= 4500 & price <= 11385"),
    ("slider to 4500", "price, type(slider)", ("Slider", 4500.0),
     "price >= 4500"),
]

_MOVED_LAYERS = ["scatter", "line", "lfit", "lfitci", "histogram", "kdensity",
                 "lpoly", "rarea", "pcspike", "function", "connected"]

#: The plot types twoway draws mlabel() on (test_marker_label_parity.py's
#: measured partition; not imported, since that file imports this one).
_LABELLING_TYPES = ("scatter", "connected", "bar", "dot", "dropline",
                    "rcapsym", "rconnected", "rscatter", "pcscatter",
                    "pccapsym", "pcarrow", "pcbarrow")


def _labels_a_layer(spec):
    """Does *spec* hold a layer that twoway draws marker labels on?"""
    return any(p.get("type") in _LABELLING_TYPES
               and (p.get("options") or {}).get("mlabel")
               for g in spec["graphs"] for p in g.get("plots") or [])


def _move_case(name, move, plots=None, go=None, graphs=None, kpis=None,
               if_expr="", bo=None):
    _, filt, action, oracle = move
    bo = dict(bo or {}, filter=filt)
    spec = _spec(plots, bo, go, graphs, kpis, if_expr)
    return pytest.param(name, spec, action, oracle, id=name)


MOVE_CORPUS = [
    *[_move_case(f"{t}, {m[0]}", m, [plot_for(t)])
      for t in _MOVED_LAYERS for m in _MOVES],
    _move_case("line with marker labels, dropdown", _MOVES[0],
               [plot_for("line", {"mlabel": "rep"})]),
    # twoway draws no marker label on a line (test_marker_label_parity.py),
    # so the entry above compares no label with no label; this one draws
    # them, and test_same_labels_after_the_move asks that it does.
    _move_case("scatter with marker labels, dropdown", _MOVES[0],
               [plot_for("scatter", {"mlabel": "rep"})]),
    # by(rep), not by(foreign): a panel whose group the move empties stays
    # on the served page as an empty panel, and the saved renderer given
    # the qualifier never builds it -- so the groups must all survive.
    _move_case("scatter under by(), dropdown", _MOVES[0], [_sc()],
               {"by": "rep"}),
    _move_case("lfit under by(), range", _MOVES[1], [plot_for("lfit")],
               {"by": "foreign"}),
    _move_case("a KPI, dropdown", _MOVES[0], [_sc()], kpis=[_kpi()]),
    _move_case("a KPI with its own if, range", _MOVES[1], [_sc()],
               kpis=[_kpi(if_expr="foreign == 0")]),
    # Linked: this entry named a linked pair and set no link(), so it
    # compared two unlinked graphs.
    _move_case("a linked pair, dropdown", _MOVES[0],
               graphs=[("g1", [_sc()]), ("g2", [plot_for("lfit")])],
               bo={"link": "g1 g2"}),
    _move_case("a graph with its own if, range", _MOVES[1], [_sc()],
               if_expr="foreign == 0"),
    # A linked graph drawn through a view -- a by() panel, or a graph with
    # its own if/in -- shows the rows it owns that the move keeps.  The
    # served recompute wrote each linked graph's rows into the ONE shared
    # source in turn, so the last one written decided what every linked
    # graph showed, and it never rebuilt a view (measured 23sep2026).
    # Each graph drawn through a view is the one the recompute reached last.
    _move_case("a linked by() graph beside a plain one, range", _MOVES[1],
               graphs=[("g1", [_sc()], {"by": "foreign"}), ("g2", [_sc()])],
               bo={"link": "g1 g2"}),
    _move_case("a linked graph with its own if, registered last, dropdown",
               _MOVES[0],
               graphs=[("g2", [_sc()]),
                       ("g1", [_sc()], None, {"if_expr": "price > 4500"})],
               bo={"link": "g1 g2"}),
    _move_case("a linked graph with its own in, registered last, slider",
               _MOVES[2],
               graphs=[("g2", [_sc()]),
                       ("g1", [_sc()], None, {"in_expr": "3/8"})],
               bo={"link": "g1 g2"}),
    _move_case("a linked qualified by() graph, range", _MOVES[1],
               graphs=[("g1", [_sc()], {"by": "foreign"},
                        {"if_expr": "price > 4500"}), ("g2", [_sc()])],
               bo={"link": "g1 g2"}),
]


@pytest.mark.parametrize("name,spec,action,oracle", MOVE_CORPUS)
class TestAFilterMoveAgrees:
    """The served document after one widget move is the saved document
    drawn from the rows the widget selected.

    The initial draw is compared by ``TestTheTwoModesAgree``; what a widget
    does afterwards is ``_allowed("aggregate layers recompute live")`` --
    the server refits, the saved page rescales in JS -- and this is where
    the refit is checked, since WP-09 left every served computed layer a
    row-index slice of its OLD curve after the first move.
    """

    def test_same_glyphs_after_the_move(self, name, spec, action, oracle):
        srv, _ = _served_after_move(spec, action)
        std, _ = _saved_with_qualifier(spec, oracle)
        assert len(std) == len(srv), f"{name}: figure counts differ"
        for i, (a, b) in enumerate(zip(std, srv)):
            diffs = _diff(a["glyphs"], b["glyphs"])
            assert not diffs, _explain(name, f"figure {i} glyphs after the "
                                             f"move", diffs)

    def test_same_labels_after_the_move(self, name, spec, action, oracle):
        srv, _ = _served_after_move(spec, action)
        std, _ = _saved_with_qualifier(spec, oracle)
        # zip() stops at the shorter list: a figure one mode lost would
        # have had its labels compared with nothing.
        assert len(std) == len(srv), f"{name}: figure counts differ"
        drawn = 0
        for i, (a, b) in enumerate(zip(std, srv)):
            la = [x for x in a["annotations"] if x["kind"] == "LabelSet"]
            lb = [x for x in b["annotations"] if x["kind"] == "LabelSet"]
            drawn += len(la)
            diffs = _diff(la, lb)
            assert not diffs, _explain(name, f"figure {i} labels after the "
                                             f"move", diffs)
        # An entry with a layer twoway labels draws labels, or the check
        # above compared [] with [] -- as every entry did (measured
        # 24sep2026: the one labelled entry labelled a line).
        if _labels_a_layer(spec):
            assert drawn, f"{name}: no marker labels drawn after the move"

    def test_same_kpi_cards_after_the_move(self, name, spec, action, oracle):
        _, srv = _served_after_move(spec, action)
        _, std = _saved_with_qualifier(spec, oracle)
        # One card per KPI, each a card: [] == [] passed for a KPI both
        # modes stopped drawing.
        assert None not in std and sorted(c[0] for c in std) == sorted(
            k["name"] for k in spec.get("kpis", [])), (
            f"{name}: the saved cards are {std}")
        assert std == srv, (f"{name}: KPI cards after the move\n  standalone "
                            f"{std}\n  server     {srv}")

    def test_the_move_changed_something(self, name, spec, action, oracle):
        """Guards the guard: a move that selects every row proves nothing."""
        before, _ = _render_pair(f"move-before:{name}", spec)["srv"], None
        after, _ = _served_after_move(spec, action)
        assert _diff(before["figures"], after) or "function" in name, (
            f"{name}: the move left every figure unchanged")


# ---------------------------------------------------------------------------
# TR-12.4: the corpus covers every plot type the CODE dispatches
# ---------------------------------------------------------------------------

def _ado_supported_types():
    """The list ``dash.ado`` prints for an unrecognised plot type: the
    package's promise to the user, read by the same parser
    test_every_plot_type_draws.py uses."""
    from test_every_plot_type_draws import _advertised_plot_types
    return set(_advertised_plot_types())


def _mata_expanded_types():
    """The full names the Mata abbreviation table expands to."""
    with open(os.path.join(_HERE, "..", "dash_parse.mata"),
              encoding="utf-8") as fh:
        src = fh.read()
    k = src.index("string scalar _expand_plottype_str")
    block = src[k:src.index("nhits = 0", k)]
    names = [full for full, _ in re.findall(r'\("([a-z]+)","([a-z]+)"\)',
                                              block)]
    assert len(names) >= 30, "the Mata plot-type table was not found"
    return set(names)


def _every_case():
    return list(CORPUS) + list(DATE_CORPUS)


def _corpus_types():
    return {plot["type"] for p in _every_case() for g in p.values[1]["graphs"]
            for plot in g["plots"]}


class TestTheCorpusIsComplete:
    """A plot type cannot be added without a parity entry (AC-12.3).

    The canonical set is derived from the CODE -- ``_dash_plot_type_names``
    reads the dispatch tables and the literal-type constant both renderers
    branch on -- and cross-checked against the two other places a plot type
    is named: the Supported: list ``dash.ado`` prints, and the Mata table
    that expands abbreviations.  A name on one side and not another is
    reported as such.
    """

    def test_the_code_set_was_derived(self):
        names = dr._dash_plot_type_names()
        assert len(names) >= 38 and {"scatter", "pci", "function"} <= names

    def test_every_dispatched_type_has_a_bare_entry(self):
        ids = {p.id for p in CORPUS}
        missing = sorted(t for t in dr._dash_plot_type_names() if t not in ids)
        assert not missing, (
            f"plot types the code dispatches with no bare parity entry: "
            f"{missing}. Add `_case(<type>, [plot_for(<type>)])' to CORPUS.")

    def test_the_corpus_names_no_type_the_code_lacks(self):
        extra = sorted(_corpus_types() - dr._dash_plot_type_names())
        assert not extra, f"corpus entries for types the code cannot draw: {extra}"

    def test_dash_ado_promises_exactly_what_the_code_draws(self):
        code, ado = dr._dash_plot_type_names(), _ado_supported_types()
        assert code == ado, (
            f"only in dash_render.py: {sorted(code - ado)}; only in dash.ado "
            f"Supported: {sorted(ado - code)}")

    def test_the_mata_table_expands_exactly_those_names(self):
        code, mata = dr._dash_plot_type_names(), _mata_expanded_types()
        assert code == mata, (
            f"only in dash_render.py: {sorted(code - mata)}; only in "
            f"_expand_plottype_str: {sorted(mata - code)}")

    def test_the_literal_types_are_the_ones_dispatched_by_name(self):
        """scatteri, pci, pcarrowi and function are branched on by name in
        both renderers; the constant is the one place they are listed."""
        assert dr._DASH_LITERAL_TYPES == {"scatteri", "pci", "pcarrowi",
                                          "function"}
        assert dr._DASH_LITERAL_TYPES <= dr._dash_plot_type_names()

    @pytest.mark.parametrize("feature,present", [
        ("by()", lambda s: any(g["graph_options"].get("by")
                               for g in s["graphs"])),
        ("link()", lambda s: bool(s["build_options"].get("link"))),
        ("filter(, type(dropdown))",
         lambda s: "dropdown" in s["build_options"].get("filter", "")),
        ("filter(, type(range))",
         lambda s: "range" in s["build_options"].get("filter", "")),
        ("filter(, type(slider))",
         lambda s: "slider" in s["build_options"].get("filter", "")),
        ("tabs()", lambda s: bool(s["build_options"].get("tabs"))),
        ("a KPI", lambda s: bool(s["kpis"])),
        ("a KPI with a qualifier",
         lambda s: any(k.get("if_expr") or k.get("in_expr")
                       for k in s["kpis"])),
        ("layout() placement",
         lambda s: ":" in s["build_options"].get("layout", "")),
        ("layout(bs)", lambda s: s["build_options"].get("layout") == "bs"),
        ("layout(bs: ...) spans",
         lambda s: s["build_options"].get("layout", "").startswith("bs:")),
        ("a graph-level qualifier",
         lambda s: any(g.get("if_expr") or g.get("in_expr")
                       for g in s["graphs"])),
        ("a per-plot qualifier",
         lambda s: any(p.get("if_expr") or p.get("in_expr")
                       for g in s["graphs"] for p in g["plots"])),
        ("mlabel()", lambda s: any("mlabel" in p.get("options", {})
                                   for g in s["graphs"] for p in g["plots"])),
        # WP-22 TR-22.3.
        ("mlabangle()", lambda s: any("mlabangle" in p.get("options", {})
                                      for g in s["graphs"]
                                      for p in g["plots"])),
        ("mlabformat()", lambda s: any("mlabformat" in p.get("options", {})
                                       for g in s["graphs"]
                                       for p in g["plots"])),
        ("clcolor() clpattern() clwidth()",
         lambda s: any({"clcolor", "clpattern", "clwidth"}
                       & set(p.get("options", {}))
                       for g in s["graphs"] for p in g["plots"])),
        ("hover()", lambda s: any(g["graph_options"].get("hover")
                                  for g in s["graphs"])),
        ("colorvar()", lambda s: any("colorvar" in p.get("options", {})
                                     for g in s["graphs"] for p in g["plots"])),
        ("a weight", lambda s: any("wexp" in p.get("options", {})
                                   for g in s["graphs"] for p in g["plots"])),
        ("a non-default scheme",
         lambda s: bool(s["build_options"].get("scheme"))),
        ("a %td variable", lambda s: bool(s["build_options"].get("formats"))),
        ("title and subtitle",
         lambda s: bool(s["build_options"].get("title"))),
        ("legend()", lambda s: any(g["graph_options"].get("legend")
                                   for g in s["graphs"])),
        ("yaxis(2)", lambda s: any(p.get("options", {}).get("yaxis") == "2"
                                   for g in s["graphs"] for p in g["plots"])),
        ("level()", lambda s: s["build_options"].get("level") != "95"),
        ("an unnamed graph with no registry (the immediate path)",
         lambda s: ("registry" not in s["build_options"]
                    and any("name" not in g.get("graph_options", {})
                            for g in s["graphs"]))),
    ])
    def test_every_cross_cutting_feature_has_an_entry(self, feature, present):
        assert any(present(p.values[1]) for p in _every_case()), (
            f"no corpus entry exercises {feature}")


class TestAggregateLayersStartFromTheSameNumbers:
    """A live recompute is allowed; a different starting value is not."""

    def _served_bars(self, spec):
        doc, _ = _served(spec)
        bars = None
        seen = set()

        def visit(m):
            if isinstance(m, (list, tuple)):
                for x in m:
                    if x is not None and not isinstance(x, (int, float, str)):
                        visit(x)
                return
            if m is None or id(m) in seen:
                return
            seen.add(id(m))
            if type(m).__name__ == "figure":
                for r in m.renderers:
                    src = getattr(r, "data_source", None)
                    if src is not None and "left" in getattr(src, "data", {}):
                        nonlocal bars
                        bars = len(src.data["left"])
            for attr in ("children", "tabs", "child"):
                k = getattr(m, attr, None)
                if k is not None:
                    visit(k)

        for root in doc.roots:
            visit(root)
        return bars

    def test_histogram_bin_count_agrees(self):
        spec = _spec([plot_for("histogram")])
        edges, _ = dr.GlyphMapper._histogram_grid(
            _DF["mpg"].dropna().values.astype(float), {})
        bars = self._served_bars(spec)
        assert bars == len(edges) - 1, (
            f"standalone draws {len(edges) - 1} bars, server draws {bars}")

    def test_an_explicit_bin_option_agrees_too(self):
        spec = _spec([plot_for("histogram", {"bin": "6"})])
        edges, _ = dr.GlyphMapper._histogram_grid(
            _DF["mpg"].dropna().values.astype(float), {"bin": "6"})
        assert self._served_bars(spec) == len(edges) - 1 == 6


class TestTheAllowanceListIsExplicit:
    def test_every_allowance_states_a_reason(self):
        assert ALLOWED, "an empty allowance list hides nothing, but says nothing"
        for key, why in ALLOWED.items():
            assert len(why) > 40, f"{key}: allowances must say why"

    def test_every_allowance_is_consulted_by_name(self):
        """An allowance nothing reads is a comment, not a rule: each key
        must be looked up with ``_allowed()`` at the place it is honoured."""
        with open(__file__, encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.find("def _build_options"):]
        for key in ALLOWED:
            assert f'_allowed("{key}")' in body, (
                f"ALLOWED[{key!r}] is never looked up by the code that "
                f"tolerates it")


class TestTheCopiedHelpersBringTheirCallees:
    """A function copied into the app whose callee stays behind is a NameError.

    `_shared_stat_lines' copies the renderer's own statistical helpers into
    the generated app with `inspect.getsource', which copies the TEXT and not
    what the text calls. It has now happened three times:

      * `_stata_if_to_pandas' gained `_mask_string_literals' and the served
        page raised on every qualifier;
      * `_resolve_seed' gained `_jitter_seed' and the served lpolyci band
        raised on every session;
      * before either, a copied body referenced `_LPOLY_ROT_C', which is why
        `_supply_missing_constants' exists -- but that pass supplies
        CONSTANTS, not functions.

    Each time, the failure surfaced on the served page rather than here. This
    imports the generated app and asks Python to resolve every global the
    copied block refers to.
    """

    @staticmethod
    def _app_module():
        tag = next(_SEQ)
        spec = _spec([plot_for("scatter")])
        sp = os.path.join(_TMP, f"cs_{tag}.json")
        dp = os.path.join(_TMP, f"cd_{tag}.json")
        ap = os.path.join(_TMP, f"ca_{tag}.py")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(_DF), fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        ms = importlib.util.spec_from_file_location(f"_callee_{tag}", ap)
        mod = importlib.util.module_from_spec(ms)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ms.loader.exec_module(mod)
        return mod

    def test_every_global_a_copied_helper_calls_is_defined(self):
        import builtins
        import dis
        import types
        mod = self._app_module()
        names = set(vars(mod))
        missing = {}
        for _n, _obj in list(vars(mod).items()):
            if not isinstance(_obj, types.FunctionType):
                continue
            if getattr(_obj, "__module__", None) != mod.__name__:
                continue
            # co_names mixes globals with ATTRIBUTE names -- `w._dash_var'
            # is in it too -- so read the bytecode and take only the names
            # loaded as globals.
            for _ins in dis.get_instructions(_obj):
                if _ins.opname not in ("LOAD_GLOBAL", "LOAD_NAME"):
                    continue
                _g = _ins.argval
                if not isinstance(_g, str):
                    continue
                if (_g not in names and not hasattr(builtins, _g)):
                    missing.setdefault(_n, set()).add(_g)
        assert not missing, (
            f"the generated app calls names it does not define: {missing}. "
            f"A helper copied by _shared_stat_lines must bring its callees.")

    def test_the_scan_found_the_copied_helpers(self):
        """Guards the guard: an app with no copied functions proves nothing.

        Read from the generated module the scan above reads, as well as
        from _shared_stat_lines' source: a name can stay in that source --
        in a comment, or in an import line it writes -- after the app stops
        carrying a copy the scan can see (the scan reads only functions the
        app itself defines)."""
        import inspect
        import types
        src = inspect.getsource(dr.ServerAppBuilder._shared_stat_lines)
        mod = self._app_module()
        for name in ("_stata_if_to_pandas", "_resolve_seed", "_bootstrap_ci",
                     "_kpi_statistic"):
            assert name in src, f"{name} is no longer copied into the app"
            fn = vars(mod).get(name)
            assert (isinstance(fn, types.FunctionType)
                    and fn.__module__ == mod.__name__), (
                f"{name} is not a function the generated app defines, so "
                f"the scan never read it: {fn!r}")


# ---------------------------------------------------------------------------
# The "tabs()" corpus entry really builds two tabs
# ---------------------------------------------------------------------------

def _glyph_kinds(layout):
    """The glyph type names each figure in *layout* draws, figure by figure."""
    from bokeh.models import GlyphRenderer, Plot
    return [sorted({type(r.glyph).__name__ for r in f.renderers
                    if isinstance(r, GlyphRenderer)})
            for f in layout.select({"type": Plot})]


def _tab_contents(root):
    """``[(title, [glyph kinds of each figure in the tab])]`` for every Tabs
    model under *root*."""
    return [(p.title, _glyph_kinds(p.child))
            for t in root.select({"type": Tabs}) for p in t.tabs]


class TestTheTabsEntryBuildsTwoTabs:
    """The corpus entry named "tabs()" wrote its groups as "A: g1; B: g2".
    tabs() separates groups with "/" (dash.sthlp, _dash_parse_tabs), so that
    string is ONE group, titled "A", whose words are "g1;", "B:" and "g2" --
    and of those only g2 is a registered name.  Measured 23sep2026 at
    ed41e8a: _dash_parse_tabs returned [("A", ["g2"])], both modes built one
    tab holding g2 and left g1 outside, and the parity checks compared two
    one-tab dashboards.  These pin the entry to what its name says: two
    tabs, A holding g1 (a scatter) and B holding g2 (a line), in both
    modes."""

    _WANT = [("A", [["Scatter"]]), ("B", [["Line"]])]

    @staticmethod
    def _spec():
        case = next(p for p in CORPUS if p.values[0] == "tabs()")
        return case.values[1]

    def test_the_string_parses_to_two_tabs(self):
        tabs = self._spec()["build_options"]["tabs"]
        assert dr._dash_parse_tabs(tabs, ["g1", "g2"]) == [
            ("A", ["g1"]), ("B", ["g2"])]

    def test_the_saved_page_builds_two_tabs(self):
        r, _warns = _standalone(self._spec())
        assert _tab_contents(r._last_layout_root) == self._WANT

    def test_the_served_app_builds_two_tabs(self):
        doc, _warns = _served(self._spec())
        got = [c for root in doc.roots for c in _tab_contents(root)]
        assert got == self._WANT
