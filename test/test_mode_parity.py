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
import copy
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

# Run at batch ends and at release (make test-all, make test-batch), not in
# the default run of the whole suite (test/conftest.py, the batch tier).
pytestmark = pytest.mark.batch
from bokeh.document import Document
from bokeh.models import (Arrow, Band, BoxAnnotation, ColorBar,
                          ColumnDataSource, Div,
                          GridBox, GridPlot, HoverTool,
                          Label, LabelSet, Legend, Node, RangeSlider, Select,
                          Slider, Span, TabPanel, Tabs, Title, ToolProxy,
                          Widget)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, load_app
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
        "columns (WP-21 TR-21.4).  For a layout(bs) entry the WHOLE page is "
        "therefore read from its markup, in page order -- title, subtitle, "
        "filter bar, tabs and grid alike (_bs_markup_page, WP-28 E14) -- "
        "each part spelled as _layout_tree spells its served twin, and the "
        "served document's nested Columns (built only for CSS sizing) are "
        "unwrapped to the same flat list (_unwrap_columns) before the two "
        "are compared.  The grid's cells are placed where a browser at "
        "992px or more places them (a bs row starts a line; a cell that "
        "would carry the line past 12 columns starts the next) and "
        "compared with the served GridBox's children: content, row, "
        "column and spans.  What the markup does below 992px, where it "
        "reflows, has no served counterpart and is not compared; "
        "dash.sthlp says the served grid keeps its spans down to a 768px "
        "window, then stacks, and takes the saved page's half rows and "
        "KPI cell heights between 768 and 991px (TR-27.2, WP-28 E14).  "
        "One difference remains outside this comparison and is not fixed: "
        "under filterposition(left) the saved page draws the title inside "
        "the content column beside the filter sidebar, where the served "
        "app draws it above sidebar and content -- a layout(bs) entry "
        "never sets filterposition(left)."
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
        mod = load_app(ap, f"_parity_{tag}")
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
        # WP-28 E14: a linked figure's nonselection alpha, and whether this
        # renderer draws the link group's own shared source -- a served
        # rspike/rconnected used to build a private source every time, so
        # a selection on the group never reached it, and a served brush
        # dimmed at Bokeh's 0.1 where the saved page dims at 0.15.  Neither
        # was part of the profile, so both drifted unseen.
        ns = getattr(r, "nonselection_glyph", None)
        entry["dim"] = (
            _num(float(ns.fill_alpha))
            if ns is not None and getattr(ns, "fill_alpha", None) is not None
            else None,
            _num(float(ns.line_alpha))
            if ns is not None and getattr(ns, "line_alpha", None) is not None
            else None,
        )
        entry["on_link_source"] = bool(
            getattr(getattr(r, "data_source", None), "_dash_link_source",
                   False))
        # WP-29 P0.17: a saved page mutes a frozen layer while it is
        # stale; the served app refits and never mutes one.
        entry["muted"] = bool(getattr(r, "muted", False))
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
        # WP-29 P0.16: a colour-mapped glyph is compared on its colours --
        # the mapper and the colour value of every drawn row -- not on the
        # name of the derived column it reads, which each mode numbers on
        # its own source (__dash_cvar<k>_<var>).
        _cs = _colour_of(g, data, idx)
        if _cs is not None:
            entry["colour"] = _cs
            for attr in ("fill_color", "line_color"):
                sp = entry.get(attr)
                if (isinstance(sp, tuple) and sp[0] == "field"
                        and (str(sp[1]).startswith(_CVAR_PREFIX)
                             or str(sp[1]).startswith("_cvar_"))):
                    entry[attr] = ("field", "<colour bins>")
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


#: The derived colour column's prefix (WP-29 P0.16); "_cvar_" before it.
_CVAR_PREFIX = getattr(dr, "_DASH_CVAR_PREFIX", "__dash_cvar")


def _colour_of(g, data, idx):
    """A glyph's colour mapping, as plain data: the mapper's type, factors,
    palette, range and nan_color, and the colour value of each drawn row
    (None kept as None).  None for a glyph with no colour mapper."""
    v = getattr(g, "fill_color", None)
    tr = v.get("transform") if isinstance(v, dict) else getattr(
        v, "transform", None)
    field = v.get("field") if isinstance(v, dict) else getattr(
        v, "field", None)
    if tr is None or not isinstance(field, str):
        return None
    col = list((data or {}).get(field, []))
    vals = []
    for i in (idx or []):
        x = col[i] if i < len(col) else None
        if isinstance(x, float):
            x = None if math.isnan(x) else _num(x)
        vals.append(x)
    factors = getattr(tr, "factors", None)
    return {"mapper": type(tr).__name__,
            "factors": list(factors) if factors is not None else None,
            "palette": list(getattr(tr, "palette", []) or []),
            "low": _num(getattr(tr, "low", None)),
            "high": _num(getattr(tr, "high", None)),
            "nan_color": str(getattr(tr, "nan_color", "")),
            "values": vals}


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
            # never drawn, and this profile did not look.  WP-30 P1.2a: a
            # Label pinned to the title by Node coordinates (economist's
            # in-band note) records its target, symbol and anchor.
            def _coord(v):
                if isinstance(v, Node):
                    return ("node", type(v.target).__name__, v.symbol,
                            v.offset)
                return _num(float(v))
            out.append({"kind": "Label", "text": r.text,
                        "font": r.text_font_size, "color": r.text_color,
                        "x": _coord(r.x), "y": _coord(r.y),
                        "x_units": r.x_units, "y_units": r.y_units,
                        "anchor": str(r.anchor),
                        "background": r.background_fill_color,
                        "index": (fig.center.index(r)
                                  if r in fig.center else None)})
        elif isinstance(r, Title) and r is not fig.title \
                and "dash_stale_cue" not in (r.tags or []):
            # WP-30 P1.2a: subtitle(), note() and caption() are side-panel
            # Titles placed by the scheme's clock and justification.
            out.append({"kind": "Title", "text": r.text,
                        "font": r.text_font_size, "color": r.text_color,
                        "align": r.align, "font_style": r.text_font_style,
                        "side": panel.get(id(r)),
                        "background": r.background_fill_color,
                        "rank": [x for x in getattr(fig, panel.get(id(r)))
                                 if isinstance(x, Title)].index(r)})
        elif isinstance(r, Span):
            out.append({"kind": "Span", "dimension": r.dimension,
                        "location": _num(r.location), "color": r.line_color,
                        "width": r.line_width, "dash": list(r.line_dash or []),
                        # WP-29 P0.5: the range the line is drawn on.
                        "range_names": (r.x_range_name, r.y_range_name)})
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
        elif isinstance(r, ColorBar):
            # WP-29 P0.16: the colour bar's title, mapper and range.
            m = r.color_mapper
            out.append({"kind": "ColorBar", "title": r.title,
                        "mapper": type(m).__name__,
                        "low": _num(getattr(m, "low", None)),
                        "high": _num(getattr(m, "high", None)),
                        "side": panel.get(id(r))})
        elif isinstance(r, BoxAnnotation):
            out.append({"kind": "BoxAnnotation",
                        "left": _num(r.left), "right": _num(r.right),
                        "top": _num(r.top), "bottom": _num(r.bottom),
                        "fill": r.fill_color, "alpha": r.fill_alpha})
        elif isinstance(r, Band):
            out.append({"kind": "Band"})
        elif isinstance(r, Arrow):
            out.append({"kind": "Arrow", **_arrow_heads(r)})
    return sorted(out, key=lambda d: json.dumps(d, sort_keys=True,
                                                default=str))


def _arrow_heads(a):
    """What one Arrow annotation draws: its heads, its style, and the
    (x_start, y_start, x_end, y_end) of every arrow it draws, read from
    its source where a coordinate is a field.

    Arrow annotations were not profiled, so pcarrow's heads could stay
    where they were drawn after a filter move while the shafts followed
    it, and every move comparison passed (BUGS.md, 24sep2026).  The rows
    are sorted: one annotation per row and one annotation over a source
    of rows draw the same arrows."""
    data = dict(a.source.data) if a.source is not None else {}
    specs = [_spec_of(getattr(a, k)) for k in ("x_start", "y_start",
                                              "x_end", "y_end")]
    n = max([len(data[s[1]]) for s in specs
             if s[0] == "field" and s[1] in data] or [1])

    def at(s, i):
        v = data[s[1]][i] if s[0] == "field" and s[1] in data else s[1]
        try:
            v = float(dr._dash_float_values(pd.Series([v]))[0])
        except (TypeError, ValueError):
            return str(v)
        return _num(v)

    rows = []
    for i in range(n):
        row = tuple(at(s, i) for s in specs)
        # BokehJS draws no arrow with a missing coordinate.
        if all(isinstance(v, float) and not math.isnan(v) for v in row):
            rows.append(row)
    return {"start": type(a.start).__name__ if a.start else None,
            "end": type(a.end).__name__ if a.end else None,
            "color": a.line_color, "width": a.line_width,
            "arrows": sorted(rows)}


def _arrows_of(annotations):
    """Every arrow the Arrow annotations of one figure profile draw, as
    one sorted list, with each annotation's style."""
    out = []
    for x in annotations:
        if x["kind"] == "Arrow":
            out.extend((x["start"], x["end"], x["color"], x["width"], a)
                       for a in x["arrows"])
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
            # A CustomJSHover is its type and args (WP-28 S12): its id
            # differs per document, its format is what must agree.
            e["formatters"] = {
                k: (str(v) if isinstance(v, str)
                    else (type(v).__name__,
                          sorted((getattr(v, "args", None) or {}).items())))
                for k, v in (t.formatters or {}).items()}
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
                "formatter_args": sorted(
                    (getattr(a.formatter, "args", None) or {}).items()),
                "ticker": type(a.ticker).__name__,
                "ticks": ([_num(float(t)) for t in a.ticker.ticks]
                          if hasattr(a.ticker, "ticks") else None),
                "visible": a.visible,
                # WP-29 P0.5: which range the axis reads, and the tick-only
                # positions ytick()/ytick(..., axis(2)) put on it.
                "range_names": (a.x_range_name, a.y_range_name),
                "tick_extra": (sorted(_num(float(v)) for v in
                                      (a.ticker.args or {}).get("extra", []))
                               if type(a.ticker).__name__ == "CustomJSTicker"
                               else None),
                "label_font": a.axis_label_text_font_size,
                "tick_font": a.major_label_text_font_size,
                "orientation": (ori if isinstance(ori, str)
                                else _num(float(ori))),
                # WP-30 P1.2a: the scheme's axis chrome and panel.
                "label_style": a.axis_label_text_font_style,
                "tick_in": a.major_tick_in, "tick_out": a.major_tick_out,
                "tick_color": a.major_tick_line_color,
                "tick_width": _num(float(a.major_tick_line_width)),
                "line_color": a.axis_line_color,
                "minor_tick_color": a.minor_tick_line_color,
                "panel": next((side for side in ("left", "right", "above",
                                                 "below")
                               if a in getattr(fig, side)), None)}

    def rng(r):
        e = {"type": type(r).__name__}
        for attr in ("start", "end"):
            v = getattr(r, attr, None)
            if isinstance(v, (int, float)):
                e[attr] = _num(float(v))
        if getattr(r, "flipped", None):
            e["flipped"] = True
        # WP-28 B2: which renderers an autorange spans (the saved page
        # limited it to the graph's own source and the served app did not)
        # and which way the axis runs, a Range1d having no flipped.
        rs = getattr(r, "renderers", None)
        e["renderers"] = len(rs) if isinstance(rs, list) else "auto"
        e["reversed"] = dr._dash_range_reversed(r)
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
        # WP-30 P1.2a: the title's alignment and side, the grid patterns.
        "title_align": t.align if t else "",
        "title_location": fig.title_location,
        "xgrid_dash": [list(g.grid_line_dash) for g in fig.xgrid],
        "ygrid_dash": [list(g.grid_line_dash) for g in fig.ygrid],
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


def _is_stale_status(m):
    """The saved page's hidden note that it does not refit (WP-29 P0.17):
    the standalone half of the allowance below, never a served model."""
    if isinstance(m, Div) and "dash_stale_status" in (m.tags or []):
        _allowed("aggregate layers recompute live")
        return True
    return False


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
        return [_layout_tree(x, figures) for x in m
                if not _is_stale_status(x)]
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


#: The saved bs page's title/subtitle, filter bar and tabs cell markers
#: (WP-28 E14): _dash_header_fragments' own tags, and the two literal
#: chunks _render_bootstrap_html writes around the filter bar and the tabs
#: widget (dash_render.py:22712-22736 area).
_BS_TITLE_RE = re.compile(r'<h2 class="db-title"[^>]*>.*?</h2>', re.S)
_BS_SUBTITLE_RE = re.compile(r'<p class="db-subtitle"[^>]*>.*?</p>', re.S)
_BS_FILTER_BAR_START = '<div class="db-row db-filter-bar">'
_BS_TABS_CELL_START = '<div class="db-row db-section"><div class="db-col-md-12">'
_BS_SECTION_ROW = '<div class="db-row db-section">'
_ROOT_ID_RE = re.compile(r'data-root-id="([^"]+)"')


def _bs_markup_page(r, page, figures, embedded):
    """The saved ``layout(bs)`` page's title, subtitle, filter bar, tabs
    and grid, read from the page itself, in PAGE ORDER (WP-28 E14).

    Before this only ``_bs_markup_tree`` (the grid) existed, so a bs entry
    that also set filter(), tabs(), title() or subtitle() had nothing to
    compare those against and ``ALLOWED`` exempted the whole page outside
    the grid -- which is how the filter bar sitting above the title
    instead of below it went unseen here.  Each part is spelled exactly as
    ``_layout_tree`` spells its served twin (a title/subtitle ``<h2>``/
    ``<p>`` as ``("Div", ("text", fragment))``, the filter bar as
    ``("Row", [("Widget", ...), ...])``, the tabs widget and the grid
    through the existing readers), so ``_unwrap_columns(srv_tree)``
    compares directly against the list this returns.
    """
    body = page[page.index('<div class="db-container">'):]
    parts = []

    m = _BS_TITLE_RE.search(body)
    if m:
        parts.append((m.start(), ("Div", ("text", m.group(0)))))
    m = _BS_SUBTITLE_RE.search(body)
    if m:
        parts.append((m.start(), ("Div", ("text", m.group(0)))))

    at = body.find(_BS_FILTER_BAR_START)
    if at >= 0:
        nxt = body.find(_BS_SECTION_ROW, at)
        chunk = body[at:nxt if nxt >= 0 else len(body)]
        widgets = [("Widget", _widget_profile(embedded[rid]))
                  for rid in _ROOT_ID_RE.findall(chunk) if rid in embedded
                  and not _is_stale_status(embedded[rid])]
        parts.append((at, ("Row", widgets)))

    at = body.find(_BS_TABS_CELL_START)
    if at >= 0:
        idm = _ROOT_ID_RE.search(body, at + len(_BS_TABS_CELL_START))
        if idm and idm.group(1) in embedded:
            parts.append((at, _layout_tree(embedded[idm.group(1)], figures)))

    grid_at = None
    for gm in re.finditer(re.escape(_BS_SECTION_ROW), body):
        nxt = body.find(_BS_SECTION_ROW, gm.end())
        chunk = body[gm.start():nxt if nxt >= 0 else len(body)]
        if "db-col-lg-" in chunk:
            grid_at = gm.start()
            break
    parts.append((grid_at if grid_at is not None else len(body),
                 _bs_markup_tree(r, page, figures, embedded)))

    parts.sort(key=lambda p: p[0])
    return [p[1] for p in parts]


def _unwrap_columns(tree):
    """A ``("Column", kids)`` is replaced by its unwrapped kids; a list of
    roots by their concatenation; anything else is kept (WP-28 E14).

    The served bs document nests its title, subtitle, filter bar and
    content in ``Column``s purely for CSS sizing (``sizing_mode``); the
    saved page's markup has no such nesting, so the two are compared as
    flat, page-ordered lists of parts.  A ``Row`` or a ``Tabs``/``GridBox``
    is kept whole -- only a ``Column`` wrapper is removed.
    """
    if isinstance(tree, list):
        out = []
        for t in tree:
            u = _unwrap_columns(t)
            if isinstance(u, list):
                out.extend(u)
            else:
                out.append(u)
        return out
    if (isinstance(tree, tuple) and len(tree) == 2 and tree[0] == "Column"):
        return _unwrap_columns(tree[1])
    return tree


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
    std_cells, srv_cells = [], []
    if root is None:
        # No root to walk: the whole page -- title, subtitle, filter bar,
        # tabs and grid, in page order -- is read from its markup
        # (_bs_markup_page, WP-28 E14); the served document's nested
        # Columns (built only for CSS sizing) are unwrapped to the same
        # flat shape before the two are compared.
        _allowed("layout(bs) is standalone markup")
        std_tree = _bs_markup_page(r, page, std_figs, embedded)
        if len(std_tree) == 1:
            # The same single-root collapse the served side gets from
            # `if len(srv_tree) == 1: srv_tree = srv_tree[0]`: a bs page
            # with nothing above the grid compares bare tuple to bare
            # tuple, not a one-element list to a bare tuple.
            std_tree = std_tree[0]
        std_cells = _bs_grid_cell_classes_from_markup(page)
    else:
        std_tree = _layout_tree(root, std_figs)
    srv_tree = [_layout_tree(x, srv_figs) for x in doc.roots]
    if len(srv_tree) == 1:
        srv_tree = srv_tree[0]
    if root is None:
        srv_tree = _unwrap_columns(srv_tree)
        srv_cells = _bs_grid_cell_classes_from_doc(doc)

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
        # The Row _bs_markup_page places is read from the same widgets;
        # kept as a direct read rather than leaves(std_tree, "Widget") so
        # a reader bug in the Row part cannot also hide from this check.
        std_widgets = [_widget_profile(w) for w in r.filter_widgets]
    else:
        std_widgets = leaves(std_tree, "Widget")
    std_kpis = kpis_of(std_tree)
    pair = {
        "std": {"tree": std_tree, "figures": std_figs, "warnings": std_w,
                "widgets": std_widgets, "kpis": std_kpis,
                "bs": root is None, "cells": std_cells},
        "srv": {"tree": srv_tree, "figures": srv_figs, "warnings": srv_w,
                "widgets": leaves(srv_tree, "Widget"),
                "kpis": kpis_of(srv_tree), "cells": srv_cells},
    }
    _CACHE[name] = pair
    return pair


_BS_GRID_CELL_RE = re.compile(
    r'class="(db-col-12[^"]*)"><div id="[^"]*" data-root-id="([^"]+)"')


def _bs_grid_cell_classes_from_markup(page):
    """``[(lg_span, sorted(classes))]`` for a saved bs page's grid cells,
    in page order -- the class attribute alone, filtered to
    ``db-col-md-N``/``db-col-lg-N``/``db-cell-h-*`` (WP-28 E14)."""
    body = page[page.index('<div class="db-container">'):]
    out = []
    for cls, _root in _BS_GRID_CELL_RE.findall(body):
        lg = re.search(r"db-col-lg-(\d+)", cls)
        classes = sorted(c for c in cls.split()
                         if c.startswith(("db-col-md-", "db-col-lg-",
                                          "db-cell-h-")))
        out.append((int(lg.group(1)) if lg else None, classes))
    return out


def _bs_grid_cell_classes_from_doc(doc):
    """``[(col_span, sorted(css_classes))]`` for the served GridBox's
    children, in children order, filtered the same way (WP-28 E14)."""
    boxes = list(doc.select({"type": GridBox}))
    if not boxes:
        return []
    out = []
    for m, _r, _c, _rs, cs in boxes[0].children:
        classes = sorted(c for c in m.css_classes
                         if c.startswith(("db-col-md-", "db-col-lg-",
                                          "db-cell-h-")))
        out.append((cs, classes))
    return out


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
          # %9.3g is honoured since WP-28 S12 (GAPS2 G6); %12s, a string
          # format, is still named.
          [_sc(mlabel="mpg", mlabformat="%12s")]),
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
    # G16 (WP-28 S14): valuelabel draws foreign's label set at the ticks.
    _case("xlabel(0/1, valuelabel)", [plot_for("scatter", xvar="foreign")],
          None, {"xlabel": "0/1, valuelabel"}),
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
    # WP-28 X2: colorvar()'s explicit forms and the colour key's own z
    # options -- the corpus proves the saved and served mapper draw the
    # same factors and the same key (BR-16.8).
    _case("colorvar() colordiscrete colorcuts(2 4)",
          [_sc(colorvar="rep", colordiscrete="colordiscrete",
               colorcuts="2 4")]),
    _case("colorvar() colorcuts(0 2 4)",
          [_sc(colorvar="rep", colorcuts="0 2 4")]),
    _case("colorvar() colorlevels(4)", [_sc(colorvar="price",
                                            colorlevels="4")]),
    _case("colorvar() colorvarminmax",
          [_sc(colorvar="price", colorvarminmax="colorvarminmax")]),
    _case("colorvar() ztitle on the colour key", [_sc(colorvar="price")],
          None, {"ztitle": "Repair"}),
    _case("colorvar() zlabel, the a(b)c spelling", [_sc(colorvar="price")],
          None, {"zlabel": "1(1)5"}),
    _case("colorvar() zlabel, the normalised spelling",
          [_sc(colorvar="price")], None, {"zlabel": "1 2 3 4 5"}),
    _case("colorvar() zscale(log)", [_sc(colorvar="price")], None,
          {"zscale": "log"}),
    # WP-29 P0.16: the key is drawn from the layer's own rows -- its own
    # if, a linked graph's if and each linked by() panel -- in both modes.
    _case("colorvar() with a layer's own if",
          [plot_for("scatter", {"colorvar": "price"},
                    if_expr="foreign == 1"),
           plot_for("scatter", if_expr="foreign == 0")]),
    _case("colorvar() colordiscrete with a layer's own if",
          [plot_for("scatter", {"colorvar": "rep",
                                "colordiscrete": "colordiscrete"},
                    if_expr="foreign == 1"),
           plot_for("scatter", if_expr="foreign == 0")]),
    _case("colorvar() colorlevels(3) with a layer's own if",
          [plot_for("scatter", {"colorvar": "price", "colorlevels": "3"},
                    if_expr="foreign == 1"),
           plot_for("scatter", if_expr="foreign == 0")]),
    _case("colorvar() on a linked graph with its own if",
          bo={"link": "g1 g2"},
          graphs=[("g1", [_sc(colorvar="price")], None,
                   {"if_expr": "foreign == 1"}),
                  ("g2", [_sc()])]),
    _case("colorvar() under a linked by()", bo={"link": "g1 g2"},
          graphs=[("g1", [_sc(colorvar="price", colorlevels="3")],
                   {"by": "foreign"}),
                  ("g2", [_sc()])]),
    # WP-28 E14: a served rspike or rconnected in a link group used to
    # draw a private source every time, so a selection on the group never
    # reached it; TestRangeLayersInALinkGroup reads on_link_source here.
    _case("rspike and rconnected in a link group", bo={"link": "g1 g2"},
          graphs=[("g1", [plot_for("rspike"), plot_for("rconnected")]),
                  ("g2", [_sc()])]),
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
          {"xlabel": "#5, labcolor(red)", "ytitle": "Miles, orientation(vertical)"}),
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
    # No served test asserted a y-axis label angle (WP-24): the entry above
    # turns the x axis only, and test_help_claims_7.py compares the served
    # ylabel() axis with the served ylabel2() axis, so a served-only fault
    # common to both was invisible.  Measured 24sep2026 with every served
    # y axis reset to "horizontal" after it is labelled: the whole corpus,
    # test_help_claims_7.py and test_graph_options.py's TestAxisLabelAngle
    # stayed green, and this entry fails.  Parity alone passes when both
    # modes drop the angle, so TestTheYLabelAngleEntry pins the value.
    _case("ylabel(, angle(vertical))", [_sc()], None,
          {"ylabel": ", angle(vertical)"}),
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
    # WP-28 B5: order() text, label() by number, a - row, lastlabel().
    _case('legend(order(1 "Group 2" 3 "Three"))',
          [_sc(), plot_for("lfit"), plot_for("qfit")], None,
          {"legend": 'order(1 "Group 2" 3 "Three")'}),
    _case('legend(order(2 1) label(1 "Data"))', [_sc(), plot_for("lfit")],
          None, {"legend": 'order(2 1) label(1 "Data")'}),
    _case('legend(order(1 - "Note" 2))', [_sc(), plot_for("lfit")], None,
          {"legend": 'order(1 - "Note" 2)'}),
    _case('legend(order(2 1) lastlabel(2 "L"))', [_sc(), plot_for("lfit")],
          None, {"legend": 'order(2 1) lastlabel(2 "L")'}),
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
    # WP-28 B3: abbreviated sub-options and axis(2) routing, both modes.
    _case("title c() and xtitle si() abbreviations", [_sc()], None,
          {"title": '"T", c(red)', "xtitle": '"W", si(large)'}),
    _case("ytitle axis(2) routed to the second axis",
          [_sc(), plot_for("line", yvar="price", xvar="weight",
                           options={"yaxis": "2"})], None,
          {"ytitle": '"Volume", axis(2)'}),
    # WP-28 B6: empty text removes both axis titles, both modes.
    _case("xtitle and ytitle given empty", [_sc()], None,
          {"xtitle": '""', "ytitle": '""'}),
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
    # WP-28 E14: the whole page, not the grid alone -- title, subtitle,
    # filter bar and tabs -- read in page order (_bs_markup_page) and
    # compared with the served document flattened the same way
    # (_unwrap_columns); the saved bar now sits below the header.
    _case("layout(bs) with a title, filters and tabs",
          bo={"layout": "bs", "title": "Title", "subtitle": "Sub",
              "filter": "foreign, type(dropdown); price, type(range)",
              "tabs": "A: g2"},
          graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])],
          kpis=[_kpi("k1")]),
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
    # ---- WP-29 P0.4: title options that give only sub-options -------------
    _case("ytitle(, size(large)) keeps the default", [_sc()],
          go={"ytitle": ", size(large)"}),
    _case("xtitle(, color(red)) and ytitle(A,,)", [_sc()],
          go={"xtitle": ", color(red)", "ytitle": "A,,"}),
    _case("a second axis titled by default and by ytitle2(, size(large))",
          [_sc(), plot_for("line", {"yaxis": "2"}, yvar="price")],
          go={"ytitle2": ", size(large)"}),
    # WP-29 P0.1: the joining types under sort, both modes joining in x
    # order (bare, each joins in the data's order: the cases above).
    *[_case(f"{t}, sort", [plot_for(t, {"sort": "sort"})])
      for t in ("line", "connected", "area", "rline", "rarea", "rconnected")],
    # ---- function points Stata computed (WP-29 P0.6) -------------------------
    # The expression is twoway's 2^3^x, which a renderer evaluating it
    # would draw as 2 8 512; the stored points, 1 8 64, are drawn instead.
    _case("function with stored points",
          [plot_for("function", {"range": "0 2", "n": "3"},
                    expr="2^3^x",
                    points={"x0": 0, "dx": 1, "y": [1, 8, 64]})]),
    _case("function points under by()",
          [plot_for("function", {"range": "0 2", "n": "3"},
                    expr="2^3^x",
                    points={"x0": 0, "dx": 1, "y": [1, 8, 64]})],
          None, {"by": "foreign"}),
    # ---- axis(#) routed to the axis it names (WP-29 P0.5) ----------------
    _case("ylabel/yscale/yline/ytick axis(2) routed",
          [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price")],
          go={"ylabel": "5000 10000, axis(2)", "yscale": "log axis(2)",
              "yline": "6000, axis(2)", "ytick": "7500, axis(2)"}),
    _case("xlabel/xscale/xline/xtick axis(2) routed",
          [_sc(), plot_for("scatter", {"xaxis": "2"}, xvar="price")],
          go={"xlabel": "5000 10000, axis(2)", "xscale": "log axis(2)",
              "xline": "6000, axis(2)", "xtick": "7500, axis(2)"}),
    _case("axis(2) under by()",
          [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price")],
          go={"by": "foreign", "ylabel": "5000 10000, axis(2)",
              "yline": "6000, axis(2)", "ytick": "7500, axis(2)"}),
    _case("ylabel2 with no second-axis layer", [_sc()],
          go={"ylabel2": "5"}),
    # ---- by() shared scales and rescale (WP-29 P0.2) -----------------------
    _case("by(foreign, yrescale)", [_sc()], go={"by": "foreign, yrescale"}),
    _case("by(foreign) with yaxis(2)",
          [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price")],
          go={"by": "foreign"}),
    _case("by(foreign, rescale) ylabel(#5)", [_sc()],
          go={"by": "foreign, rescale", "ylabel": "#5"}),
    _case("by(foreign, yrescale) yscale(range(0))", [_sc()],
          go={"by": "foreign, yrescale", "yscale": "range(0)"}),
    _case("by(foreign, yrescale) yscale(range(0)) with every foreign missing",
          [_sc()], go={"by": "foreign, yrescale", "yscale": "range(0)"},
          if_expr="foreign > 5"),
    # WP-29 P0.7: the default bandwidth by Stata's rule (kernel, degree,
    # weights reach it) is the same in both modes.
    _case("lpoly, kernel(biweight) degree(2)",
          [plot_for("lpoly", {"kernel": "biweight", "degree": "2"})]),
    _case("lpolyci, kernel(gaussian) degree(3) aweight",
          [plot_for("lpolyci", {"kernel": "gaussian", "degree": "3",
                                "weight": "aweight", "wexp": "price"})]),
    # WP-29 P0.18: a layer whose own if keeps no row keeps its style in
    # both modes (twoway keys it in its p# style).  bar, rbar and rarea
    # are left out: after the fix they differ only in a warning (the saved
    # page notes "drew nothing", the served app does not), which this
    # section does not change; their served style is pinned by
    # test_emptied_layer_style.py::TestAnEmptiedLayerKeepsItsStyle.
    _case("rspike with its own if that keeps no row",
          [_sc(), plot_for("rspike", if_expr="price > 20000")]),
    # WP-29 P0.11: the page holds only the rows a consumer reads.
    _case("two layers with their own qualifiers, range filter (embed rows)",
          [plot_for("scatter", if_expr="price > 4500"),
           plot_for("scatter", in_expr="1/3")],
          bo={"filter": "price, type(range)"}),
    _case("a linked pair with graph qualifiers (embed rows)",
          bo={"link": "g1 g2", "filter": "price, type(range)"},
          graphs=[("g1", [_sc()], None, {"if_expr": "foreign == 1",
                                         "in_expr": ""}),
                  ("g2", [_sc()], None, {"if_expr": "price > 10000",
                                         "in_expr": ""})]),
    _case("a dropdown under a graph if (embed rows)", [_sc()],
          bo={"filter": "rep, type(dropdown)"}, if_expr="foreign == 1"),
    # WP-30 P1.25a: StataCorp's six internal schemes.  Every shipped scheme
    # reaches both modes through one lookup, so two stand for the six:
    # meta (s2color's chain, legend at 4 o'clock, a minor grid) and
    # stgcolor_mv (the deepest chain).
    *[_case(f"scatter with yline, {s}", [_sc()], {"scheme": s},
            {"yline": "20"})
      for s in ("meta", "stgcolor_mv")],
    _case("scatter, session scheme stcolor_meta", [_sc()],
          {"session_scheme": "stcolor_meta"}),
    # WP-30 S08 (P1.12a): sizes in Stata's units draw alike in both modes.
    _case("S08 msize(*2) mlabgap(1) mlabsize(*2)",
          [_sc(msize="*2", mlabel="foreign", mlabgap="1", mlabsize="*2")]),
    _case("S08 msize(4pt) under stcolor", [_sc(msize="4pt")],
          bo={"scheme": "stcolor"}),
    _case("S08 title size(*1.5) and labsize(10pt)", [_sc()],
          go={"title": "T, size(*1.5)", "ylabel": ", labsize(10pt)"}),
    _case("S08 legend size(5)", [_sc(), plot_for("lfit")],
          go={"legend": "size(5)"}),
    _case("S08 mlabposition(2) and bar labels",
          [_sc(mlabel="foreign", mlabposition="2"),
           plot_for("bar", {"mlabel": "foreign"})]),
    _case("S08 msize(HUGE) noted", [_sc(msize="HUGE")]),
    _case("TeX pairs in every canvas text (WP-30 P1.11a)",
          [_sc(), plot_for("lfit")],
          go={"title": '"\\(y\\)"', "subtitle": '"\\[z\\]"',
              "xtitle": '"$$x$$"', "xlabel": '3000 "\\(t\\)" 4000',
              "legend": 'label(2 "\\(f\\)")'}),
    # WP-30 P1.19: twoway's sub-option spellings, read alike in both modes.
    _case("legend abbreviations", [_sc(), plot_for("lfit")],
          go={"legend": 'c(1) lab(1 "XX") posi(9) s(large) lastlab(2 "ZZ")'}),
    _case("legend rows beat cols", [_sc(), plot_for("lfit")],
          go={"legend": "cols(3) rows(1)"}),
    _case("legend on beats off", [_sc()], go={"legend": "on off"}),
    _case("axis label abbreviations", [_sc()],
          go={"ylabel": ", labs(large) ang(45) for(%9.1f) nog"}),
    _case("quoted axis label text", [_sc()],
          go={"ylabel": '10 "labsize(large)" 20'}),
    _case("xline abbreviations", [_sc()],
          go={"xline": "3000, lc(red) lp(dash) lw(thick)"}),
    _case("title s() is size", [_sc()], go={"title": '"T", s(small)'}),
    # WP-30 P1.1a: one options object per expanded series
    _case("stylelist series, markers",
          [plot_for("scatter", {"mcolor": "red", "msymbol": "O"}, yvar="mpg"),
           plot_for("scatter", {"mcolor": "blue", "msymbol": "T"},
                    yvar="price")]),
    _case("stylelist series, lines",
          [plot_for("line", {"lcolor": "red", "lpattern": "solid"}, yvar="mpg"),
           plot_for("line", {"lcolor": "blue", "lpattern": "dash"},
                    yvar="price")]),
    # WP-30 P1.12b: Stata line widths
    _case("line widths in Stata units",
          [plot_for("line", {"lwidth": "*2"}),
           plot_for("scatter", {"mlwidth": "thick"})],
          go={"xline": "20, lwidth(1pt)", "plotregion": "lwidth(thick)"}),
    _case("vvvthin and none",
          [plot_for("line", {"lwidth": "vvvthin"}),
           plot_for("lfitci", {"alwidth": "none"})]),
    # WP-30 P1.17a: bar widths and range caps
    _case("rbar barwidth(.3)", [plot_for("rbar", {"barwidth": ".3"})]),
    _case("rcap msize(large)", [plot_for("rcap", {"msize": "large"})]),
    # (bare rcapsym is the plot-type entry at the top of the corpus)
    _case("bar on a %tm x", [plot_for("bar", xvar="when")],
          {"formats": {"when": "%tm"}}),
    # WP-30 P1.2a: scheme chrome -- economist's in-band note (placed at
    # fig.center[0], before the yline's Span in both modes), its right-hand
    # y axis and left-hand axis 2; stcolor's dashed grid; s1rcolor's ticks.
    _case("scheme chrome: economist titles, note and axis 2",
          [_sc(), plot_for("line", yvar="price", xvar="weight",
                           options={"yaxis": "2"})], {"scheme": "economist"},
          {"title": "T", "subtitle": "S", "note": "N", "caption": "C",
           "yline": "20", "ylabel2": "5000 10000"}),
    _case("scheme chrome: stcolor grid and xlabel grid", [_sc()],
          {"scheme": "stcolor"}, {"xlabel": ", grid"}),
    _case("scheme chrome: s1rcolor ticks", [_sc()], {"scheme": "s1rcolor"},
          {"title": "T", "note": "N"}),
    # WP-30 P1.2b: intensity drawn as an opaque blend, markers opaque.
    _case("bar, fintensity(150)", [plot_for("bar", {"fintensity": "150"})]),
    _case("area, s1rcolor, fintensity(50)",
          [plot_for("area", {"fcolor": "navy", "fintensity": "50"})],
          {"scheme": "s1rcolor"}),
    _case("rconnected, sttrans", [plot_for("rconnected")],
          {"scheme": "sttrans"}),
    _case("rbar and rarea, color(red)",
          [plot_for("rbar", {"color": "red"}),
           plot_for("rarea", {"color": "red"})]),
    _case("histogram, fcolor(navy) fintensity(50)",
          [plot_for("histogram", {"fcolor": "navy", "fintensity": "50"})]),
    _case("lfitci, fintensity(150)",
          [plot_for("lfitci", {"fintensity": "150"})]),
    # WP-30 P1.23b: colour-key text and computed tooltips
    _case("colorvar() colorcuts() keyed %8.0gc",
          [_sc(colorvar="price", colorcuts="5000 9000")]),
    _case("colorvar() zlabel(, format(%9.2f))", [_sc(colorvar="price")],
          go={"zlabel": ", format(%9.2f)"}),
    _case("histogram, frequency tooltip",
          [plot_for("histogram", {"frequency": "frequency"})]),
    # WP-30 P1.5: axis ticks in twoway's display formats
    # The primary axes' formats are drawn by the second-axis entry, and a
    # bare histogram's height axis by the plot-type entry.
    _case("S18 second axis fallback", [_sc(), _sc(yaxis="2")],
          {"formats": {"weight": "%8.0gc", "mpg": "%9.2f"}}),
    _case("S18 xvarformat and labels", [_sc(xvarformat="%9.2f")], None,
          {"xlabel": '2000 "two" 3000'}),
    _case("S18 date format() picture",
          [plot_for("line", yvar="mpg", xvar="when")], {"formats": {"when": "%td"}},
          {"xlabel": ", format(%tdDD/NN/CCYY)"}),
    _case("S18 unwritable format noted", [_sc()], None,
          {"ylabel": ", format(%12s)"}),
    _case("Fit, range, pc and scatteri keys (WP-30 P1.16)",
          [_sc(), plot_for("lowess"), plot_for("lpolyci"), plot_for("rcap"),
           plot_for("pcspike"), plot_for("scatteri")]),
    _case("First-equals-last titles and axis 2 (WP-30 P1.16)",
          [_sc(), plot_for("scatter", yvar="price"),
           plot_for("rcap", {"yaxis": "2"})]),
]


#: Dates.  The served app had no date handling at all (BUGS.md, "The
#: generated server app has no date handling at all"): measured 23sep2026 a
#: line over a %td ``when`` drew a DatetimeAxis with ``@{when}{%F}`` saved
#: and a LinearAxis over 15340, 15341, ... with ``@{when}`` served, and a
#: date-valued KPI read the day number.  These entries were a hand-made
#: strict xfail until WP-27 loaded the served frame through the saved
#: loader's column reader; every comparison now runs, as for CORPUS.
_W = {"formats": {"when": "%td"}}
DATE_CORPUS = [
    _case("a date on the x axis",
          [plot_for("line", yvar="mpg", xvar="when")], _W),
    _case("a date-valued KPI", [_sc()], _W,
          kpis=[_kpi(stat="max", var="when")]),
    _case("a date KPI: min, median and count", [_sc()], _W,
          kpis=[_kpi(stat="min", var="when"),
                _kpi(name="k2", stat="median", var="when"),
                _kpi(name="k3", stat="count", var="when")]),
    _case("a date on the y axis",
          [plot_for("line", yvar="when", xvar="mpg")], _W),
    _case("a scatter and an lfit over a date",
          [plot_for("scatter", yvar="mpg", xvar="when"),
           plot_for("lfit", yvar="mpg", xvar="when")], _W),
    _case("a monthly date on the x axis",
          [plot_for("connected", yvar="mpg", xvar="when")],
          {"formats": {"when": "%tm"}}),
    _case("a clock on the x axis",
          [plot_for("scatter", yvar="mpg", xvar="when")],
          {"formats": {"when": "%tc"}}),
    _case("hover() of a date", [_sc()], _W, go={"hover": "when"}),
    # WP-29 P0.10: a variable named only in hover(), and one the data
    # does not hold.
    _case("hover() of a variable no layer plots, a dropdown filter",
          [_sc()], {"filter": "foreign, type(dropdown)"}, {"hover": "rep"}),
    _case("hover() naming a variable not in the data", [_sc()], None,
          {"hover": "rep nosuch"}),
    _case("mlabel() of a date",
          [plot_for("scatter", {"mlabel": "when"}, yvar="mpg",
                    xvar="when")], _W),
    _case("by() over a date axis",
          [plot_for("line", yvar="mpg", xvar="when")], _W,
          go={"by": "foreign"}),
    _case("a date range filter",
          [plot_for("line", yvar="mpg", xvar="when")],
          dict(_W, filter="when, type(range)")),
    _case("a date slider filter",
          [plot_for("line", yvar="mpg", xvar="when")],
          dict(_W, filter="when, type(slider)")),
    _case("a date dropdown filter",
          [plot_for("line", yvar="mpg", xvar="when")],
          dict(_W, filter="when, type(dropdown)")),
    _case("xline, xlabel and xscale(range()) on a date axis",
          [plot_for("line", yvar="mpg", xvar="when")], _W,
          go={"xline": "15342", "xlabel": "15340 15345 \"mid\" 15349",
              "xscale": "range(15339 15350)"}),
    # WP-29 P0.8 (section 05): computed layers of a date in its units.
    _case("a histogram of a date, width() and start() in days",
          [plot_for("histogram", {"width": "3", "start": "15340"},
                    var="when")], _W),
    _case("a kdensity of a monthly date",
          [plot_for("kdensity", {"bwidth": "1"}, var="when")],
          {"formats": {"when": "%tm"}}),
    _case("an lpoly over a date, bwidth() in days",
          [plot_for("scatter", yvar="mpg", xvar="when"),
           plot_for("lpoly", {"bwidth": "3"}, yvar="mpg", xvar="when")], _W),
    # D05-1 struck (01oct2026): a lone fit keeps the date axis.
    _case("a lone lfit over a date keeps the date axis",
          [plot_for("lfit", yvar="mpg", xvar="when")], _W),
    # D05-4's mixed axis (section 05 Evidence 8).
    _case("a date fit on an axis shared with a number",
          [plot_for("scatter", yvar="mpg", xvar="weight"),
           plot_for("lfit", yvar="mpg", xvar="when")], _W),
    # WP-29 P0.20 (section 05): KPI statistics of a date in its units.
    _case("spreads and a sum of a date", [_sc()], _W,
          kpis=[_kpi(stat="sd", var="when"),
                _kpi(name="k2", stat="iqr", var="when"),
                _kpi(name="k3", stat="sum", var="when")]),
    # WP-28 B2: the extent after the layers, the same in both modes.
    _case("yscale(range(100))", [_sc()], None, {"yscale": "range(100)"}),
    _case("yscale(r(0 100) rev)", [_sc()], None, {"yscale": "r(0 100) rev"}),
    _case("ylabel(0(20)100, norescale)", [_sc()], None,
          {"ylabel": "0(20)100, norescale"}),
    _case("yscale(range(abc))", [_sc()], None, {"yscale": "range(abc)"}),
]

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
        "dash: mlabformat(%12s) is not a display format dash reproduces",
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
        "labcolor(red)",
    "by() with an unimplemented sub-option":
        "dash: by() sub-option(s) not implemented and ignored: "
        "rows(2) compact",
    "filter() with an unknown type":
        "dash: filter(price, type(bogus)): type() must be one of",
    "yscale(range(abc))":
        "dash: yscale(range()) ignores abc, which is not a number",
    "hover() naming a variable not in the data":
        "dash: hover() of graph 'g1' names variable(s) not in the data -- "
        "'nosuch'",
    # WP-29 P0.2: raised at build time in both modes.
    "by(foreign, yrescale) yscale(range(0))":
        "dash: graph 'g1': by(, yrescale) draws each panel on its own y "
        "scale; yscale(range()) is not applied, as in twoway.",
    # WP-29 P0.5: raised at build time in both modes.
    "ylabel2 with no second-axis layer":
        "dash: graph 'g1': ylabel2() (ylabel(..., axis(2))) is not drawn: "
        "no layer is on yaxis(2).",
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

        A ``layout(bs)`` page has no Bokeh tree: its whole page -- title,
        subtitle, filter bar, tabs and grid -- is read from its markup, in
        page order (``_bs_markup_page``, WP-28 E14), and compared with the
        served document's tree flattened the same way (``_unwrap_columns``,
        ``ALLOWED``).  What the markup does below the grid's 992px
        breakpoint has no served counterpart and stays outside this
        comparison, as does the recorded ``filterposition(left)``
        difference -- a ``layout(bs)`` entry never sets it.
        """
        pair = _render_pair(name, spec)
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


@pytest.mark.parametrize("name", ["scatter"])
def test_an_entrys_comparisons_share_one_group(request, name):
    """Every comparison of an entry carries the entry's xdist group: the
    mark always, and on a ``--dist loadgroup`` worker the group in its node
    id as well, which is what xdist schedules by.  The mark alone was there
    all along and grouped nothing (WP-30 test performance A1,
    test_xdist_groups.py)."""
    mark = request.node.get_closest_marker("xdist_group")
    assert mark is not None and mark.kwargs == {"name": "parity:" + name}
    if (getattr(request.config, "workerinput", None) is not None
            and request.config.getvalue("loadgroup")):
        assert request.node.nodeid.endswith("@parity:" + name), (
            request.node.nodeid)


class TestRangeLayersInALinkGroup:
    """WP-28 E14: a served rspike or rconnected in a link group draws the
    group's shared source, as the saved page does, so a selection on the
    group reaches it too."""

    def test_rspike_and_rconnected_draw_the_groups_source_in_both_modes(
            self):
        entry = next(c for c in CORPUS
                    if c.id == "rspike and rconnected in a link group")
        pair = _render_pair(*entry.values)
        for mode in ("std", "srv"):
            for fig in pair[mode]["figures"]:
                for g in fig["glyphs"]:
                    if g["type"] in ("Segment", "Scatter"):
                        assert g["on_link_source"], (mode, g["type"])
                    elif g["type"] == "Line":
                        assert not g["on_link_source"], (mode, g["type"])


class TestTheBsCellsCarryOneSetOfClasses:
    """WP-28 E14: a served layout(bs) grid's children carry the saved
    page's own db-col-md-N/db-col-lg-N/db-cell-h-* classes."""

    @pytest.mark.parametrize(
        "name,spec", [c for c in CORPUS if c.id.startswith("layout(bs")])
    def test_each_bs_entry(self, name, spec):
        pair = _render_pair(name, spec)
        assert pair["std"]["cells"], name
        assert pair["std"]["cells"] == pair["srv"]["cells"], (
            name, pair["std"]["cells"], pair["srv"]["cells"])


class TestThePagesHeads:
    """WP-28 E14: both pages declare the same viewport meta."""

    def test_both_pages_declare_one_viewport(self):
        from test_csp import _file_context
        _, sp, dp = _write(_spec([_sc()]))
        r = dr.DashRenderer(sp, dp)
        page = r.render()
        assert page.count(dr._DASH_VIEWPORT_META) == 1
        assert page.index("Content-Security-Policy") < page.index(
            dr._DASH_VIEWPORT_META)
        served_page = dr._dash_served_template().render(_file_context())
        assert served_page.count(dr._DASH_VIEWPORT_META) == 1
        assert served_page.index("Content-Security-Policy") < (
            served_page.index(dr._DASH_VIEWPORT_META))


def test_every_must_warn_entry_is_in_the_corpus():
    """A renamed entry would leave its _MUST_WARN line checking nothing."""
    names = {p.values[0] for p in CORPUS + DATE_CORPUS}
    assert set(_MUST_WARN) <= names, sorted(set(_MUST_WARN) - names)


@pytest.mark.parametrize("name,spec", DATE_CORPUS)
class TestTheTwoModesAgreeOnDates(_Agree):
    """See ``DATE_CORPUS``: once a known server gap, now held equal."""


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
                 "lpoly", "rarea", "pcspike", "function", "connected",
                 "pcarrow", "pcbarrow",
                 # WP-29 P0.9: lpolyci's analytic band refits after a move.
                 "lpolyci"]
# bar and rbar widths hold through a move (WP-30 P1.17a); the other eight
# agreed already and are guards.
_MOVED_LAYERS += ["bar", "rbar", "lowess", "qfit", "fpfit", "mband",
                  "mspline", "lpolyci", "qfitci", "fpfitci"]

#: WP-29 P0.18: moves that leave 2 and 1 rows of _DF.
_EMPTYING_MOVES = [
    ("slider to 10000", "price, type(slider)", ("Slider", 10000.0),
     "price >= 10000"),
    ("slider to 11385", "price, type(slider)", ("Slider", 11385.0),
     "price >= 11385"),
]
#: WP-29 P0.18: every layer a move can leave with no drawable rows.
_EMPTIED_LAYERS = ["lowess", "lfit", "qfit", "fpfit", "lpoly", "kdensity",
                   "mband", "mspline", "histogram", "bar", "rbar", "rarea",
                   "rspike"]

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


def _own(name, move, plots, truth, go=None, graphs=None, if_expr="",
         labels=None, fit=None, parity=True):
    return {"name": name, "move": move, "plots": plots, "go": go,
            "graphs": graphs, "if_expr": if_expr, "truth": truth,
            "labels": labels, "fit": fit, "parity": parity}


#: A layer's OWN if()/in() in an UNLINKED graph, after a filter move.  The
#: served recompute wrote every row the move kept for the graph into each
#: layer's source, so the layer's qualifier was lost at the first move:
#: measured 24sep2026 on sysuse auto, `(scatter mpg weight in 40/60) (lfit
#: mpg weight in 40/60)' with the dropdown on Foreign drew all 22 foreign
#: cars where Stata's `count if foreign == 1 in 40/60' and the saved page
#: give 8 (the lfit, redrawn, was already right).  And a column the layer
#: derives -- the marker-label text -- was read at the row label as a
#: position, so under any qualifier the labels named other rows and the
#: column came out shorter than the rest.
#:
#: ``truth`` is ``{figure: {glyph: observations}}``: the observations Stata
#: selects, measured with the console binary on _DF's ten observations
#: (24sep2026, `count if ... in ...' and `list obs weight if ... in ...',
#: quoted per entry).  ``labels`` are the texts Stata writes at them (rep,
#: in data order); ``fit`` is ``(figure, glyph, x ends, y ends)`` from
#: `regress mpg weight' on those rows.  An entry with ``parity`` is also in
#: MOVE_CORPUS, compared whole with the saved renderer.
_OWN_QUALIFIER_MOVES = [
    # count if foreign == 1 in 3/8: 3, observations 4, 6 and 8; regress
    # mpg weight on them: 29.8918 at weight 1800, 18.9792 at 3100.
    _own("a scatter and an lfit, each with its own in, dropdown", _MOVES[0],
         [plot_for("scatter", in_expr="3/8"), plot_for("lfit", in_expr="3/8")],
         {0: {0: [4, 6, 8]}},
         fit=(0, 1, (1800.0, 3100.0), (29.8918, 18.9792))),
    # count if mpg > 18 & price >= 4500 & price <= 11385: 4 (4, 5, 8, 10).
    _own("a scatter with its own if, range", _MOVES[1],
         [plot_for("scatter", if_expr="mpg > 18")], {0: {0: [4, 5, 8, 10]}}),
    # count if mpg > 18 & price >= 4500 in 2/9: 3 (4, 5, 8).
    _own("a scatter with its own if and in, slider", _MOVES[2],
         [plot_for("scatter", if_expr="mpg > 18", in_expr="2/9")],
         {0: {0: [4, 5, 8]}}),
    # The graph's `if mpg > 18' and a range: count if mpg > 18 & price >=
    # 4500 & price <= 11385 in 3/8: 3 (4, 5, 8); without the in: 4.
    _own("a scatter with its own in beside a plain one, under the graph's "
         "if, range", _MOVES[1],
         [plot_for("scatter", in_expr="3/8"), plot_for("scatter")],
         {0: {0: [4, 5, 8], 1: [4, 5, 8, 10]}}, if_expr="mpg > 18"),
    # The graph's `in 2/9': count if foreign == 1 & mpg > 20 in 2/9: 2
    # (4, 8).
    _own("a scatter with its own if, under the graph's in, dropdown",
         _MOVES[0], None, {0: {0: [4, 8]}},
         graphs=[("g1", [plot_for("scatter", if_expr="mpg > 20")], None,
                  {"in_expr": "2/9"})]),
    # by(foreign): count if foreign == 0 & price >= 4500 & price <= 11385
    # in 3/8: 2 (5, 7); foreign == 1: 2 (4, 8).
    _own("a scatter with its own in, under by(), range", _MOVES[1],
         [plot_for("scatter", in_expr="3/8")],
         {0: {0: [5, 7]}, 1: {0: [4, 8]}}, go={"by": "foreign"}),
    # by(rep), every group kept by the move: count if foreign == 1 & mpg >
    # 18 & rep == 3: 1 (6); rep == 4: 2 (8, 10); rep == 5: 1 (4).
    _own("a scatter with its own if, under by(), dropdown", _MOVES[0],
         [plot_for("scatter", if_expr="mpg > 18")],
         {0: {0: [6]}, 1: {0: [8, 10]}, 2: {0: [4]}}, go={"by": "rep"}),
    # The graph's `if mpg > 18', labelled: list obs weight rep if mpg > 18
    # & price >= 4500 & price <= 11385 gives 4, 5, 8, 10 with rep 5, 4, 4,
    # 4.  The labels were read at the row label as a position: served
    # '4', '3' beside four markers, the column two long where the rest
    # are four.
    _own("a labelled scatter under the graph's if, range", _MOVES[1],
         [plot_for("scatter", {"mlabel": "rep"})], {0: {0: [4, 5, 8, 10]}},
         if_expr="mpg > 18", labels=["5", "4", "4", "4"]),
    # Its own if on a range layer: count if mpg > 18 & price >= 4500 &
    # price <= 11385: 4 (4, 5, 8, 10).
    _own("an rspike with its own if, range", _MOVES[1],
         [plot_for("rspike", if_expr="mpg > 18")], {0: {0: [4, 5, 8, 10]}}),
    # count if foreign == 1 in 3/8: 3 (4, 6, 8).
    _own("a dot plot with its own in, dropdown", _MOVES[0],
         [plot_for("dot", in_expr="3/8")], {0: {0: [4, 6, 8]}}),
    # Labelled, with its own in: list obs weight rep if foreign == 1 in
    # 3/8 gives 4, 6, 8 with rep 5, 3, 4.  Compared whole with the saved
    # page since WP-27: its labels are drawn from the layer's own rows,
    # where they labelled every row of the graph's source -- ten labels
    # beside six markers before any move.
    _own("a labelled scatter with its own in, dropdown", _MOVES[0],
         [plot_for("scatter", {"mlabel": "rep"}, in_expr="3/8")],
         {0: {0: [4, 6, 8]}}, labels=["5", "3", "4"]),
    # The connected layers, in since WP-27: the saved page applied the
    # layer's view by position to a copy sorted by x, so `in 3/8' drew
    # the wrong observations (BUGS.md, 24sep2026).  count if foreign == 1
    # in 3/8: 3 (4, 6, 8); count if mpg > 18 & price >= 4500 & price <=
    # 11385: 4 (4, 5, 8, 10) -- the counts measured for the scatter
    # entries above, the same rows.
    _own("a line with its own in, dropdown", _MOVES[0],
         [plot_for("line", in_expr="3/8")], {0: {0: [4, 6, 8]}}),
    _own("a tsline with its own if, range", _MOVES[1],
         [plot_for("tsline", if_expr="mpg > 18")], {0: {0: [4, 5, 8, 10]}}),
    _own("a connected plot with its own in, dropdown", _MOVES[0],
         [plot_for("connected", in_expr="3/8")],
         {0: {0: [4, 6, 8], 1: [4, 6, 8]}}),
    _own("a labelled connected plot with its own if, range", _MOVES[1],
         [plot_for("connected", {"mlabel": "rep"}, if_expr="mpg > 18")],
         {0: {0: [4, 5, 8, 10], 1: [4, 5, 8, 10]}},
         labels=["5", "4", "4", "4"]),
    # rconnected's four glyphs: each end's line and its markers.
    _own("an rconnected with its own in, dropdown", _MOVES[0],
         [plot_for("rconnected", in_expr="3/8")],
         {0: {0: [4, 6, 8], 1: [4, 6, 8], 2: [4, 6, 8], 3: [4, 6, 8]}}),
]


MOVE_CORPUS = [
    # Flipped (WP-29 P0.11): a literal layer reads no row, so its filter
    # reaches none unless a card it recomputes does; an unqualified
    # filter-mode card keeps the widget's reach every row.
    *[_move_case(f"{t}, {m[0]}", m, [plot_for(t)],
                 kpis=([_kpi()] if t in dr._DASH_LITERAL_TYPES else None))
      for t in _MOVED_LAYERS for m in _MOVES],
    # An arrow's heads follow its shafts, with the layer's own in (BUGS.md,
    # 24sep2026: the heads were one fixed annotation per row).
    *[_move_case(f"{t} with its own in, {_MOVES[0][0]}", _MOVES[0],
                 [plot_for(t, in_expr="3/8")]) for t in ("pcarrow", "pcbarrow")],
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
    # A layer's OWN if()/in() in an unlinked graph, after a move: the entries
    # of _OWN_QUALIFIER_MOVES, where Stata's rows are written down.
    *[_move_case(e["name"], e["move"], e["plots"], e["go"],
                 graphs=e["graphs"], if_expr=e["if_expr"])
      for e in _OWN_QUALIFIER_MOVES if e["parity"]],
    # A function layer's stored points are fixed by Stata: a move leaves
    # them where they are, in both modes (WP-29 P0.6).
    _move_case("function with stored points, dropdown", _MOVES[0],
               [_sc(), plot_for("function", {"range": "0 2", "n": "3"},
                                expr="2^3^x",
                                points={"x0": 0, "dx": 1,
                                        "y": [1, 8, 64]})]),
    # WP-29 P0.15: a layer's own if inside a linked by() panel, or inside a
    # linked graph with its own if.  The served app recomputes each layer
    # from its own frame (guards; the saved page is
    # test_saved_filter_layers.py's).
    _move_case("a layer's own if under a linked by(), range", _MOVES[1],
               graphs=[("g1", [_sc(), plot_for("scatter",
                                               if_expr="price > 4500")],
                        {"by": "foreign"}), ("g2", [_sc()])],
               bo={"link": "g1 g2"}),
    _move_case("a layer's own if in a linked graph with its own if, range",
               _MOVES[1],
               graphs=[("g1", [_sc(), plot_for("scatter",
                                               if_expr="price > 4500")],
                        None, {"if_expr": "foreign == 1"}),
                       ("g2", [_sc()])],
               bo={"link": "g1 g2"}),
    # WP-29 P0.2: the panels keep one shared scale after a move.
    _move_case("by(foreign) shared scale, price slider", _MOVES[1], [_sc()],
               go={"by": "foreign"}),
    # WP-29 P0.5: the routed options stay on the second axis after a move.
    _move_case("yaxis(2) with axis(2) options, dropdown", _MOVES[0],
               [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price")],
               go={"ylabel": "5000 10000, axis(2)", "yscale": "log axis(2)",
                   "yline": "6000, axis(2)", "ytick": "7500, axis(2)"}),
    # WP-29 P0.7: the served recompute derives Stata's default bandwidth
    # from the rows the move keeps.
    _move_case("lpoly biweight degree 2, dropdown", _MOVES[0],
               [plot_for("lpoly", {"kernel": "biweight", "degree": "2"})]),
    # WP-29 P0.18: a served bar's width holds through a move (WP-30 P1.17a).
    _move_case("bar under by(rep), dropdown", _MOVES[0], [plot_for("bar")],
               {"by": "rep"}),
    _move_case("rbar under by(foreign), range", _MOVES[1],
               [plot_for("rbar")], {"by": "foreign"}),
    _move_case("a linked pair with a bar, dropdown", _MOVES[0],
               graphs=[("g1", [_sc()]), ("g2", [plot_for("bar")])],
               bo={"link": "g1 g2"}),
    # WP-29 P0.18: a layer a move leaves with 2, 1 or 0 rows keeps its style.
    *[_move_case(f"{t} emptied, {m[0]}", m, [plot_for(t)])
      for t in _EMPTIED_LAYERS for m in _EMPTYING_MOVES],
    # lpoly is left out: on _DF's five domestic rows it draws nothing
    # before the move as well, so the move changes nothing to compare.
    *[_move_case(f"{t} with its own if emptied, slider to 10000",
                 _EMPTYING_MOVES[0],
                 [plot_for(t, if_expr="foreign == 0")])
      for t in _EMPTIED_LAYERS if t != "lpoly"],
    # WP-29 P0.11: restricted pages after a move.
    _move_case("two layers with their own qualifiers (embed rows)", _MOVES[1],
               [plot_for("scatter", if_expr="price > 4500"),
                plot_for("scatter", in_expr="1/3")]),
    _move_case("a linked pair with graph qualifiers (embed rows)", _MOVES[1],
               bo={"link": "g1 g2"},
               graphs=[("g1", [_sc()], None, {"if_expr": "foreign == 1",
                                              "in_expr": ""}),
                       ("g2", [_sc()], None, {"if_expr": "price > 10000",
                                              "in_expr": ""})]),
    # WP-30 P1.25a: StataCorp's six internal schemes, one for the six
    _move_case("scatter with yline under stgcolor_mv, dropdown", _MOVES[0],
               [_sc()], {"yline": "20"}, bo={"scheme": "stgcolor_mv"}),
    # WP-30 P1.1a: one options object per expanded series
    _move_case("stylelist series, dropdown", _MOVES[0],
               [plot_for("scatter", {"mcolor": "red", "msymbol": "O"},
                         yvar="mpg"),
                plot_for("scatter", {"mcolor": "blue", "msymbol": "T"},
                         yvar="price")]),
    # WP-30 P1.12b: Stata line widths
    _move_case("line, lwidth(*2), dropdown", _MOVES[0],
               [plot_for("line", {"lwidth": "*2"})]),
    # WP-30 P1.17a: bar widths and range caps
    _move_case("rcap msize(large), dropdown", _MOVES[0],
               [plot_for("rcap", {"msize": "large"})]),
    _move_case("bar on a %tm x, range", _MOVES[1],
               [plot_for("bar", xvar="when")],
               bo={"formats": {"when": "%tm"}}),
    # WP-30 P1.2a: scheme chrome -- economist's chrome after a move.
    _move_case("scheme chrome: economist, dropdown", _MOVES[0], [_sc()],
               {"title": "T", "note": "N", "caption": "C"},
               bo={"scheme": "economist"}),
    # WP-30 P1.23b: colour-key text and computed tooltips
    # colorcuts(), not the manifest's colorlevels(): the standalone side
    # of a move is rebuilt on the moved rows, whose levels differ by
    # design (the served key keeps the build's levels, as before).
    _move_case("colorvar() colorcuts(), dropdown", _MOVES[0],
               [_sc(colorvar="price", colorcuts="5000 9000")]),
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

    Each entry's served move and saved oracle are rendered once per process
    (``_once``) and shared by its four comparisons, which A1's xdist group
    keeps on one worker; each comparison rendered both, and the arrowhead
    one twice (WP-30 test performance A4).
    """

    #: (which, spec, move or oracle) -> (figures, cards), plain data.
    _RENDERED = {}

    @classmethod
    def _once(cls, render, spec, arg):
        """``render(spec, arg)`` -- ``_served_after_move`` or
        ``_saved_with_qualifier``, each ``(figures, cards)`` of plain data
        -- made once and handed out as copies, so no comparison sees
        another's changes."""
        key = (render.__name__, json.dumps(spec, sort_keys=True),
               json.dumps(arg))
        if key not in cls._RENDERED:
            cls._RENDERED[key] = render(spec, arg)
        return copy.deepcopy(cls._RENDERED[key])

    def _moved(self, spec, action, oracle):
        """``(served, saved)``: the document after the move, and the saved
        renderer given the move's rows as an ``if``."""
        return (self._once(_served_after_move, spec, action),
                self._once(_saved_with_qualifier, spec, oracle))

    def test_same_glyphs_after_the_move(self, name, spec, action, oracle):
        (srv, _), (std, _) = self._moved(spec, action, oracle)
        assert len(std) == len(srv), f"{name}: figure counts differ"
        for i, (a, b) in enumerate(zip(std, srv)):
            diffs = _diff(a["glyphs"], b["glyphs"])
            assert not diffs, _explain(name, f"figure {i} glyphs after the "
                                             f"move", diffs)

    def test_same_labels_after_the_move(self, name, spec, action, oracle):
        (srv, _), (std, _) = self._moved(spec, action, oracle)
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

    def test_same_arrowheads_after_the_move(self, name, spec, action,
                                            oracle):
        """An arrowhead is drawn where the saved renderer draws it from the
        kept rows, on the shaft it heads.  Each head was one Arrow
        annotation fixed to its row, so after a move the shaft went and
        the head stayed (BUGS.md, 24sep2026)."""
        (srv, srv_cards), (std, std_cards) = self._moved(spec, action,
                                                         oracle)
        assert len(std) == len(srv), f"{name}: figure counts differ"
        for i, (a, b) in enumerate(zip(std, srv)):
            ha, hb = _arrows_of(a["annotations"]), _arrows_of(b["annotations"])
            assert ha == hb, (f"{name}: figure {i} arrowheads after the move"
                              f"\n  saved  {ha}\n  served {hb}")
            _assert_heads_on_shafts(name, b)

        srv, std = srv_cards, std_cards
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
        after, _ = self._once(_served_after_move, spec, action)
        assert _diff(before["figures"], after) or "function" in name, (
            f"{name}: the move left every figure unchanged")


def _assert_heads_on_shafts(name, fig):
    """Every arrow a figure's Arrow annotations draw heads a Segment it
    draws, and every Segment of a pcarrow/pcbarrow layer has its head."""
    heads = sorted(a for x in fig["annotations"] if x["kind"] == "Arrow"
                   for a in x["arrows"])
    if not heads:
        return
    shafts = []
    for g in fig["glyphs"]:
        if g["type"] != "Segment":
            continue
        cols = [g["coords"].get(k) for k in ("x0", "y0", "x1", "y1")]
        if not all(c and c[0] not in ("value", "other") for c in cols):
            continue
        shafts.extend(tuple(v) for v in zip(*[c[1] for c in cols]))
    assert heads == sorted(shafts), (f"{name}: the heads are not on the "
                                     f"shafts\n  heads  {heads}\n  shafts "
                                     f"{sorted(shafts)}")


#: _DF's observation number (1-based) by weight, which no two share.
_OBS_OF_WEIGHT = {float(w): i + 1 for i, w in enumerate(_DF["weight"])}


def _observations(glyph):
    """The observations a glyph profile draws, read from its x (a range
    layer's x0), sorted."""
    coord = glyph["coords"].get("x") or glyph["coords"].get("x0")
    assert coord and coord[0] == "weight", glyph["coords"]
    return sorted(_OBS_OF_WEIGHT[float(w)] for w in coord[1])


def _own_spec(entry):
    _, filt, action, oracle = entry["move"]
    spec = _spec(entry["plots"], {"filter": filt}, entry["go"],
                 entry["graphs"], None, entry["if_expr"])
    return spec, action, oracle


@pytest.mark.parametrize("entry", _OWN_QUALIFIER_MOVES,
                         ids=[e["name"] for e in _OWN_QUALIFIER_MOVES])
class TestALayersOwnQualifierAfterAMove:
    """After a filter move each layer draws the observations Stata selects
    for it: its own if()/in() -- the in counted over the whole dataset --
    with the graph's qualifier, its by() group and the move's rows.  Both
    modes, held to Stata's answer (``_OWN_QUALIFIER_MOVES``); the parity
    entries are compared whole with the saved renderer in
    ``TestAFilterMoveAgrees`` as well."""

    def _check(self, figs, entry, mode):
        name = entry["name"]
        assert len(figs) == len(entry["truth"]), (
            f"{name}: {mode} drew {len(figs)} figure(s)")
        for fi, layers in entry["truth"].items():
            glyphs = figs[fi]["glyphs"]
            for gi, want in layers.items():
                got = _observations(glyphs[gi])
                assert got == want, (
                    f"{name}: {mode} figure {fi} glyph {gi} draws "
                    f"observations {got}; Stata selects {want}")
        if entry["fit"]:
            fi, gi, xs, ys = entry["fit"]
            c = figs[fi]["glyphs"][gi]["coords"]
            got = ((c["x"][1][0], c["x"][1][-1]), (c["y"][1][0], c["y"][1][-1]))
            assert got == (xs, ys), (
                f"{name}: {mode} fitted line ends at {got}; Stata's regress "
                f"on the rows gives {(xs, ys)}")

    def test_the_served_app(self, entry):
        spec, action, _ = _own_spec(entry)
        srv, _ = _served_after_move(spec, action)
        self._check(srv, entry, "the served app")
        if entry["labels"] is not None:
            (lab,) = [a for a in srv[0]["annotations"]
                      if a["kind"] == "LabelSet"]
            assert lab["texts"] == entry["labels"], (
                f"{entry['name']}: served labels {lab['texts']}; Stata "
                f"writes {entry['labels']}")

    def test_the_saved_page(self, entry):
        """The saved renderer given the move's rows as an ``if``: its own
        oracle for a move (TestAFilterMoveAgrees)."""
        spec, _, oracle = _own_spec(entry)
        std, _ = _saved_with_qualifier(spec, oracle)
        self._check(std, entry, "the saved page")
        if entry["labels"] is not None and entry["parity"]:
            (lab,) = [a for a in std[0]["annotations"]
                      if a["kind"] == "LabelSet"]
            assert lab["texts"] == entry["labels"], lab["texts"]

    def test_the_move_changes_what_the_layer_draws(self, entry):
        """Guards the guard: before the move the served layers draw other
        observations, so the comparisons above are of the move's work (a
        by() panel the move leaves as it was may draw the same)."""
        spec, _, _ = _own_spec(entry)
        before = _render_pair("own-before:" + entry["name"], spec)
        same = [(fi, gi) for fi, layers in entry["truth"].items()
                for gi, want in layers.items()
                if _observations(
                    before["srv"]["figures"][fi]["glyphs"][gi]) == want]
        assert len(same) < sum(len(v) for v in entry["truth"].values()), (
            f"{entry['name']}: the move changed no layer's rows: {same}")


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
    # To the function's closing brace: the "nhits = 0" this stopped at went
    # with the unreachable ambiguity count (WP-26 TR-26.6, 24sep2026).
    block = src[k:src.index("\n}\n", k)]
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
        ("a y-axis label angle",
         lambda s: any("angle(" in str(g["graph_options"].get("ylabel", ""))
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


class TestAnAliasIsNotAPlotType:
    """``sc``, ``li`` and ``hist`` draw nothing, and say so, in both modes.

    The shared dispatch table carried the three as aliases of scatter, line
    and histogram, and the saved page's univariate set and the served app's
    two re-spellings accepted ``hist``.  dash.ado never writes one: it
    expands a spelling to the full name (``_expand_plottype_str``) before it
    writes a spec -- test_parser.cscript and test_abbreviations.cscript
    certify the expansion -- so only a spec written by hand names one, and
    no test or document did.  Measured on the code before WP-26
    (24sep2026): both modes drew all three as the full type, without a
    word.  WP-26 removed them (TR-26.5): such a layer draws nothing and is
    named in the same words in both modes, and the rest of its graph is
    drawn.  Not corpus entries: TestTheCorpusIsComplete refuses a type the
    code does not draw, which is the point here.
    """

    @pytest.mark.parametrize("alias,full", [
        ("sc", "scatter"), ("li", "line"), ("hist", "histogram")])
    def test_the_same_note_and_nothing_drawn(self, alias, full):
        name = "an alias: " + alias
        layer = dict(plot_for(full), type=alias)
        pair = _render_pair(name, _spec([plot_for("scatter"), layer]))
        note = "no glyph mapper for plot type %r" % (alias,)
        for mode in ("std", "srv"):
            assert [w for w in pair[mode]["warnings"] if note in w], (
                f"{mode} did not refuse `{alias}': {pair[mode]['warnings']}")
        assert pair["std"]["warnings"] == pair["srv"]["warnings"], (
            f"warnings differ\n  standalone {pair['std']['warnings']}"
            f"\n  server     {pair['srv']['warnings']}")
        # The scatter layer is drawn, and nothing else, the same way twice.
        for mode in ("std", "srv"):
            (fig,) = pair[mode]["figures"]
            assert [g["type"] for g in fig["glyphs"]] == ["Scatter"], (
                mode, fig["glyphs"])
        diffs = _diff(pair["std"]["figures"], pair["srv"]["figures"])
        assert not diffs, _explain(name, "figures", diffs)

    def test_the_tables_hold_full_names_only(self):
        """The control, on the tables themselves: every key names the
        method it dispatches to, so no entry is another type's alias."""
        class _Probe:
            def __getattr__(self, attr):
                if attr.startswith("map_"):
                    return attr
                raise AttributeError(attr)

        std, rng = dr._dash_glyph_dispatch(_Probe())
        pc = dr._dash_pc_dispatch(_Probe())
        for table in (std, rng, pc):
            for key, method in table.items():
                assert method == "map_" + key, (key, method)
        assert not {"sc", "li", "hist"} & set(std)
        assert "hist" not in dr._DASH_UNIVARIATE_TYPES


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
      * before either, a copied body referenced `_LPOLY_ROT_C' (lpoly's
        old rule-of-thumb constant, replaced in WP-29 P0.7 by
        `_LPOLY_ROT_GRID' and `_LPOLY_ROT_CONSTANTS'), which is why
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, f"_callee_{tag}")
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


# ---------------------------------------------------------------------------
# The "ylabel(, angle(vertical))" corpus entry draws vertical y labels
# ---------------------------------------------------------------------------

class TestTheYLabelAngleEntry:
    """The entry's own value, in both modes.  The parity checks compare the
    two modes with each other, so they pass when both drop the angle; this
    pins what the entry exists for.  angle(vertical) is Stata's anglestyle
    vertical, 90 degrees (anglestyle-vertical.style; the reader is
    test_twoway_option_parity.py's TestTheAnglestyleReader), which a Bokeh
    axis draws as a major_label_orientation of pi/2 -- the y labels read
    upwards, as twoway draws them.  The control: the bare scatter entry's
    y axis reads "horizontal" through the same profile, so the reader
    tells the two apart."""

    @staticmethod
    def _axes(entry):
        case = next(p for p in CORPUS if p.values[0] == entry)
        pair = _render_pair(*case.values)
        out = {}
        for side in ("std", "srv"):
            figs = pair[side]["figures"]
            assert len(figs) == 1, (entry, side, len(figs))
            out[side] = figs[0]["axes"]
        return out

    def test_both_modes_turn_the_y_labels_vertical(self):
        for side, axes in self._axes("ylabel(, angle(vertical))").items():
            assert [a["orientation"] for a in axes["y"]] == [
                _num(math.pi / 2)], (side, axes["y"])
            # ylabel() turns the y axis alone.
            assert [a["orientation"] for a in axes["x"]] == [
                "horizontal"], (side, axes["x"])

    def test_the_control_reads_horizontal_without_the_option(self):
        """Flipped (WP-30 P1.2a): the bare scatter, under the default
        s2color, takes the scheme's ``anglestyle vertical_tick vertical``,
        so its y labels read upwards as twoway draws them (register
        P1.2.1); the control is now the x axis, which stays horizontal.
        TestTickLabelAngle (test_scheme_chrome.py) pins the explicit
        horizontal case."""
        for side, axes in self._axes("scatter").items():
            assert [a["orientation"] for a in axes["y"]] == [
                _num(math.pi / 2)], (side, axes["y"])
            assert [a["orientation"] for a in axes["x"]] == [
                "horizontal"], (side, axes["x"])



# ---------------------------------------------------------------------------
# hover(): honoured on every layer whose rows are observations, and reported
# on every layer whose rows are not
# ---------------------------------------------------------------------------

#: Layers whose points twoway computes from the observations -- a fitted or
#: smoothed curve, a density, a histogram's bins, a function's grid.  A
#: point of one is not an observation, so no variable of the dataset has a
#: value there to show.
_HOVER_COMPUTED = frozenset({
    "fpfit", "fpfitci", "function", "histogram", "kdensity", "lfit",
    "lfitci", "lowess", "lpoly", "lpolyci", "mband", "mspline", "qfit",
    "qfitci",
})

#: Layers drawn from values typed in the command: no observation at all.
_HOVER_LITERAL = frozenset({"scatteri", "pci", "pcarrowi"})

_ALL_PLOT_TYPES = sorted(dr._dash_plot_type_names())

#: Every other layer draws one mark (or one pair of marks) per observation,
#: and hover() reaches its tooltip.
_HOVER_HONOURED = frozenset(_ALL_PLOT_TYPES) - _HOVER_COMPUTED - _HOVER_LITERAL


def _figures_in(mode, spec):
    """(figures, warnings) of *spec* in *mode*."""
    from bokeh.plotting import figure as _fig
    if mode == "saved":
        r, caught = _standalone(spec)
        return list(r.figures.values()), caught
    doc, caught = _served(spec)
    return [f for root in doc.roots for f in root.select({"type": _fig})], \
        caught


def _hover_notes(caught):
    return [w for w in caught if "hover()" in w]


def _tools_showing(fig, var):
    return [t for t in fig.tools if isinstance(t, HoverTool)
            and isinstance(t.tooltips, list)
            and any(f"@{{{var}}}" in field for _, field in t.tooltips)]


def _assert_rows_align(fig, var="rep"):
    """Every renderer the tooltip reads *var* for carries it, and each row's
    value is the value of the observation that row draws -- identified by
    its weight, which no two observations of _DF share."""
    tools = _tools_showing(fig, var)
    assert tools, "no tooltip shows %r: %s" % (
        var, [t.tooltips for t in fig.tools if isinstance(t, HoverTool)])
    checked = 0
    for t in tools:
        for r in t.renderers:
            data = r.data_source.data
            assert var in data, (type(r.glyph).__name__, sorted(data))
            assert "weight" in data, (type(r.glyph).__name__, sorted(data))
            for w, v in zip(data["weight"], data[var]):
                if w is None or (isinstance(w, float) and math.isnan(w)):
                    continue
                want = _DF.loc[_DF["weight"] == float(w), var]
                assert len(want) == 1, w
                assert float(v) == float(want.iloc[0]), (
                    type(r.glyph).__name__, w, v, want.iloc[0])
                checked += 1
    assert checked, "no row was checked"


def _glyph_fields(r):
    """The variables of _DF a renderer's glyph draws: a column it draws
    that is the variable, or a copy of one (a spike's y1 holds price)."""
    out = set()
    g, data = r.glyph, r.data_source.data
    for name in g.properties_with_values(include_defaults=True):
        f = _spec_of(getattr(g, name, None))
        if f[0] != "field" or f[1] not in data:
            continue
        if f[1] in _DF.columns:
            out.add(f[1])
            continue
        col = [_num(float(v)) for v in data[f[1]]]
        for var in _DF.columns:
            if var in data and col == [_num(float(v)) for v in data[var]]:
                out.add(var)
    return out


class TestTheLayerVariables:
    """``_dash_hover_layer_vars``: what one layer's tooltip names."""

    @pytest.mark.parametrize("plot,want", [
        ({"type": "scatter", "yvar": "price", "xvar": "weight"},
         ["weight", "price"]),
        ({"type": "rcap", "yvar1": "mpg", "yvar2": "price",
          "xvar": "weight"}, ["weight", "mpg", "price"]),
        ({"type": "pcarrow", "y1var": "mpg", "x1var": "weight",
          "y2var": "price", "x2var": "foreign"},
         ["weight", "mpg", "foreign", "price"]),
        ({"type": "scatter", "yvar": "mpg", "xvar": "mpg"}, ["mpg"]),
        ({"type": "scatteri", "values": [[1, 2]]}, []),
        ({"type": "scatter", "yvar": ["x"], "xvar": None}, []),
        (None, []),
    ])
    def test_its_own_variables(self, plot, want):
        assert dr._dash_hover_layer_vars(plot) == want

    def test_a_hostile_name_is_left_out_of_every_layers_tooltip(self):
        """Injection: a name that could close a tooltip placeholder is
        refused in a second layer as in the first."""
        from bokeh.plotting import figure
        bad = "p}<img src=x onerror=alert(1)>"
        fig = figure()
        src = ColumnDataSource({"weight": [1.0], "mpg": [2.0], bad: [3.0]})
        r1 = fig.scatter(x="weight", y="mpg", source=src)
        r2 = fig.scatter(x="weight", y=bad, source=src)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            dr._dash_build_hover(
                fig, "weight", "mpg", "", [],
                layers=[({"type": "scatter", "xvar": "weight",
                          "yvar": "mpg"}, [r1]),
                        ({"type": "scatter", "xvar": "weight",
                          "yvar": bad}, [r2])])
        for t in fig.tools:
            if isinstance(t, HoverTool):
                assert all(bad not in f for _, f in t.tooltips), t.tooltips

    def test_many_layers_of_one_variable_share_one_tool(self):
        """Resource exhaustion: two hundred layers plotting the same
        variables are one HoverTool, not two hundred."""
        from bokeh.plotting import figure
        fig = figure()
        src = ColumnDataSource({"weight": [1.0], "mpg": [2.0]})
        plot = {"type": "scatter", "xvar": "weight", "yvar": "mpg"}
        layers = [(plot, [fig.scatter(x="weight", y="mpg", source=src)])
                  for _ in range(200)]
        dr._dash_build_hover(fig, "weight", "mpg", "", [], layers=layers)
        tools = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert len(tools) == 1 and len(tools[0].renderers) == 200


def _assert_each_layer_names_its_own(fig, mode, extra=()):
    """The tooltip of every renderer drawing mpg names weight and mpg and
    not price; of every one drawing price, weight and price and not mpg;
    each with *extra*."""
    tools = [t for t in fig.tools if isinstance(t, HoverTool)]
    seen = {"mpg": 0, "price": 0}
    for r in fig.renderers:
        drawn = _glyph_fields(r) & {"mpg", "price"}
        if len(drawn) != 1:
            continue
        [own] = drawn
        other = ({"mpg", "price"} - {own}).pop()
        mine = [t for t in tools if r in list(t.renderers or [])]
        assert len(mine) == 1, (mode, type(r.glyph).__name__, own,
                                [t.tooltips for t in mine])
        fields = " ".join(f for _, f in mine[0].tooltips)
        for v in ["weight", own, *extra]:
            assert f"@{{{v}}}" in fields, (mode, own, mine[0].tooltips)
        assert f"@{{{other}}}" not in fields, (mode, own, mine[0].tooltips)
        seen[own] += 1
    assert seen["mpg"] and seen["price"], (mode, seen)


class TestHoverReachesEveryLayerOrIsReported:
    """BUGS.md "hover() is dropped by the mappers that rebuild their source
    from the plotted variables alone".  Measured 24sep2026 with hover(rep),
    a variable no layer plots: 30 of the 40 plot types left it out of the
    tooltip in both modes and said nothing -- the entry's own count of 26
    was taken with hover(foreign), which the pc family draws as a
    coordinate.  Every type now either shows it, row by row, or says why
    it cannot: a computed layer's points are not observations."""

    def test_the_forty_types_are_partitioned(self):
        assert len(_ALL_PLOT_TYPES) == 40, _ALL_PLOT_TYPES
        assert _HOVER_COMPUTED | _HOVER_LITERAL <= set(_ALL_PLOT_TYPES)
        assert len(_HOVER_HONOURED) == 23, sorted(_HOVER_HONOURED)

    @pytest.mark.parametrize("mode", ("saved", "served"))
    @pytest.mark.parametrize("ptype", _ALL_PLOT_TYPES)
    def test_honoured_or_reported(self, mode, ptype):
        spec = _spec([plot_for(ptype)], None, {"hover": "rep"})
        figs, caught = _figures_in(mode, spec)
        notes = _hover_notes(caught)
        if ptype in _HOVER_HONOURED:
            _assert_rows_align(figs[0])
            assert not notes, notes
        else:
            assert not _tools_showing(figs[0], "rep")
            why = ("typed in the command" if ptype in _HOVER_LITERAL
                   else "computed from the observations")
            assert notes == [
                f"dash: hover() does not reach plot 1 ({ptype}) of graph "
                f"'g1': its points are {why}, not observations, so its "
                f"tooltip shows only what it draws."], notes

    @pytest.mark.parametrize("ptype", sorted(_HOVER_HONOURED))
    def test_the_tooltip_follows_a_served_filter_move(self, ptype):
        """A served layer is redrawn after a move; the rows it keeps still
        carry their own values."""
        spec = _spec([plot_for(ptype)], {"filter": "foreign"},
                     {"hover": "rep"})
        doc, _ = _served(spec)
        sel = [w for w in _widgets_of(doc) if isinstance(w, Select)]
        assert sel, "no dropdown"
        raw = [v for v, lab in sel[0].options if lab == "Foreign"]
        _fire(sel[0], raw[0])
        from bokeh.plotting import figure as _fig
        fig = [f for root in doc.roots for f in root.select({"type": _fig})][0]
        _assert_rows_align(fig)
        for t in _tools_showing(fig, "rep"):
            for r in t.renderers:
                ws = [w for w in r.data_source.data["weight"]
                      if w is not None and not (isinstance(w, float)
                                                and math.isnan(w))]
                assert ws and all(
                    _DF.loc[_DF["weight"] == float(w), "foreign"].iloc[0]
                    == 1.0 for w in ws), (ptype, ws)

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_mixed_graph_shows_it_on_the_points_and_names_the_fit(self,
                                                                    mode):
        spec = _spec([plot_for("scatter"), plot_for("lfit")], None,
                     {"hover": "rep"})
        figs, caught = _figures_in(mode, spec)
        _assert_rows_align(figs[0])
        assert _hover_notes(caught) == [
            "dash: hover() does not reach plot 2 (lfit) of graph 'g1': its "
            "points are computed from the observations, not observations, "
            "so its tooltip shows only what it draws."]

    @pytest.mark.parametrize("second", ["scatter", "bar", "spike", "line",
                                        "area", "dot"])
    def test_a_second_layer_of_other_variables_has_the_same_tooltip(
            self, second):
        """The saved page draws every layer from one source holding every
        variable; a served layer source held its own.  A second layer of
        price on weight beside a scatter of mpg was in the tooltip saved
        and out of it served (measured 24sep2026 on scatter and bar), and
        carrying hover()'s columns through line and area widened that."""
        spec = _spec([_sc(), plot_for(second, yvar="price", xvar="weight")],
                     None, {"hover": "rep"})
        got = {}
        for mode in ("saved", "served"):
            figs, _ = _figures_in(mode, spec)
            got[mode] = sorted(
                (json.dumps(list(t.tooltips)),
                 sorted(type(r.glyph).__name__ for r in t.renderers))
                for t in figs[0].tools if isinstance(t, HoverTool))
            _assert_rows_align(figs[0])
            _assert_each_layer_names_its_own(figs[0], mode)
        assert got["saved"] == got["served"], got

    @pytest.mark.parametrize("mode", ("saved", "served"))
    @pytest.mark.parametrize("hover", ["", "rep"])
    def test_each_layers_tooltip_names_its_own_variables(self, mode, hover):
        """``scatter mpg weight || scatter price weight``: the second
        layer's tooltip names weight and price, and the first's weight and
        mpg -- each plus hover()'s variables.  The saved renderer built one
        tooltip from the FIRST layer's variables and pointed it at both, so
        a point of price showed its mpg (BUGS.md, 24sep2026)."""
        spec = _spec([_sc(), plot_for("scatter", yvar="price",
                                      xvar="weight")],
                     None, {"hover": hover} if hover else None)
        figs, _ = _figures_in(mode, spec)
        _assert_each_layer_names_its_own(figs[0], mode,
                                         extra=[hover] if hover else [])

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_by_panels_report_it_once(self, mode):
        spec = _spec([plot_for("lfit")], None,
                     {"hover": "rep", "by": "foreign"})
        figs, caught = _figures_in(mode, spec)
        assert len(figs) >= 2
        assert len(_hover_notes(caught)) == 1, _hover_notes(caught)

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_no_hover_no_note(self, mode):
        _figs, caught = _figures_in(mode, _spec([plot_for("lfit")]))
        assert not _hover_notes(caught)

    # ---- adversarial ----------------------------------------------------

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_huge_hover_list_is_one_note(self, mode):
        """Resource exhaustion: thousands of names are one note per layer,
        and none of them is echoed.  Since WP-29 P0.10 the names the data
        does not hold get their own note, one per graph, naming three and
        counting the rest."""
        names = " ".join(["rep"] + [f"v{i}" for i in range(5000)])
        spec = _spec([plot_for("line"), plot_for("lfit")], None,
                     {"hover": names})
        figs, caught = _figures_in(mode, spec)
        notes = _hover_notes(caught)
        unreached = [n for n in notes if "does not reach" in n]
        missing = [n for n in notes if "not in the data" in n]
        assert len(unreached) == 1, notes
        assert missing == [
            "dash: hover() of graph 'g1' names variable(s) not in the data "
            "-- 'v0', 'v1', 'v2' and 4,997 more; the tooltip leaves them "
            "out."], missing
        assert len(notes) == 2, notes
        assert all("v4999" not in n for n in notes), notes
        _assert_rows_align(figs[0])

    # ---- WP-29 P0.10: a hover() name the data does not hold -------------

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_hover_variable_not_in_the_data_is_named(self, mode):
        spec = _spec([_sc()], None, {"hover": "rep nosuch"})
        figs, caught = _figures_in(mode, spec)
        assert [n for n in caught if "not in the data" in n] == [
            "dash: hover() of graph 'g1' names variable(s) not in the data "
            "-- 'nosuch'; the tooltip leaves them out."]
        assert _tools_showing(figs[0], "rep")
        _assert_rows_align(figs[0])

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_missing_hover_names_are_one_bounded_note(self, mode):
        names = " ".join(["rep"] + [f"v{i}" for i in range(5000)])
        spec = _spec([_sc()], None, {"hover": names})
        _figs, caught = _figures_in(mode, spec)
        missing = [n for n in caught if "not in the data" in n]
        assert missing == [
            "dash: hover() of graph 'g1' names variable(s) not in the data "
            "-- 'v0', 'v1', 'v2' and 4,997 more; the tooltip leaves them "
            "out."], missing
        assert "'v4999'" not in missing[0]
        assert len(missing[0]) <= 400

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_hostile_absent_hover_name_is_shown_bounded(self, mode):
        bad = "x" * 50000 + chr(27) + "<script>" + "y" * 50000
        spec = _spec([_sc()], None, {"hover": bad})
        figs, caught = _figures_in(mode, spec)
        missing = [n for n in caught if "not in the data" in n]
        assert len(missing) == 1, [n[:200] for n in missing]
        note = missing[0]
        assert "\n" not in note and chr(27) not in note
        assert len(note) <= 400
        m = re.search(r" -- ('.*?'); the tooltip", note)
        assert m is not None and len(m.group(1)) <= 82, note
        for f in figs:
            for t in f.tools:
                if isinstance(t, HoverTool) and isinstance(t.tooltips, list):
                    assert all("<script>" not in fld and "{safe}" not in fld
                               for _lab, fld in t.tooltips), t.tooltips

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_by_panels_name_a_missing_variable_once(self, mode):
        spec = _spec([_sc()], None, {"hover": "rep nosuch", "by": "foreign"})
        figs, caught = _figures_in(mode, spec)
        assert len(figs) >= 2
        assert len([n for n in caught if "not in the data" in n]) == 1, \
            caught

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_hostile_graph_name_is_quoted_not_obeyed(self, mode):
        """Injection: the graph's name reaches the note through repr(), one
        line, whatever it holds."""
        evil = "g1\n<script>alert(1)</script>'"
        spec = _spec(graphs=[(evil, [plot_for("kdensity")],
                              {"hover": "rep"})])
        _figs, caught = _figures_in(mode, spec)
        notes = _hover_notes(caught)
        assert len(notes) == 1 and "\n" not in notes[0], notes
        assert repr(evil) in notes[0], notes

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_a_markup_column_never_becomes_a_field(self, mode):
        """Injection: a hover() name that is not a plain name stays out of
        every tooltip on a carried source, as on a scatter's."""
        bad = "rep}<img src=x onerror=alert(1)>"
        df = _DF.assign(**{bad: _DF["rep"]})
        spec = _spec([plot_for("area")], None, {"hover": bad})
        tag = next(_SEQ)
        sp = os.path.join(_TMP, f"spec_mk_{tag}.json")
        dp = os.path.join(_TMP, f"data_mk_{tag}.json")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(df, _VALUE_LABELS, _LABEL_NAMES), fh)
        with mock.patch.object(sys.modules[__name__], "_write",
                               lambda _s: (tag, sp, dp)):
            figs, _caught = _figures_in(mode, spec)
        for t in figs[0].tools:
            if isinstance(t, HoverTool) and isinstance(t.tooltips, list):
                assert all("<img" not in f and "<img" not in lab
                           for lab, f in t.tooltips), t.tooltips


# ---------------------------------------------------------------------------
# A linked by() graph's line and connected layers on a saved build
# ---------------------------------------------------------------------------

def _view_rows(r):
    """The row positions a renderer draws: its source's rows, through its
    view's filters when it has any."""
    n = max((len(v) for v in r.data_source.data.values()), default=0)
    keep = list(range(n))
    view = getattr(r, "view", None)
    for f in (getattr(view, "filters", None) or []) if view else []:
        booleans = getattr(f, "booleans", None)
        indices = getattr(f, "indices", None)
        if booleans is not None:
            keep = [i for i in keep if i < len(booleans) and booleans[i]]
        elif indices is not None:
            s = set(indices)
            keep = [i for i in keep if i in s]
    flt = getattr(view, "filter", None) if view else None
    for f in ([flt] if flt is not None else []):
        booleans = getattr(f, "booleans", None)
        indices = getattr(f, "indices", None)
        if booleans is not None:
            keep = [i for i in keep if i < len(booleans) and booleans[i]]
        elif indices is not None:
            s = set(indices)
            keep = [i for i in keep if i in s]
    return keep


class TestALinkedByGraphsLinesOnASavedBuild:
    """BUGS.md "A linked by() graph with a line or connected layer logs
    Bokeh's E-1024 error on every saved build" (measured 24sep2026 with
    Bokeh 3.9.0): each panel's Line got a CDSView with a BooleanFilter,
    which Bokeh refuses on a connected glyph.  The pin: no E-1024, and
    each panel's line holds its own panel's observations, in the data's
    order within its group, as twoway joins each by() panel (WP-29 P0.1;
    this pinned x order until then, which was wrong)."""

    _SPEC = staticmethod(lambda: _spec(
        build_options={"link": "g1 g2"},
        graphs=[("g1", [plot_for("line"), plot_for("connected")],
                 {"by": "foreign"}),
                ("g2", [_sc()])]))

    def test_no_e1024(self):
        """A handler on Bokeh's own validation logger: pytest's caplog did
        not see these records here (checked 24sep2026), and a guard that
        cannot see the error passes with it."""
        import logging
        seen = []

        class _Keep(logging.Handler):
            def emit(self, record):
                seen.append(record.getMessage())

        lg = logging.getLogger("bokeh.core.validation.check")
        h = _Keep(level=logging.WARNING)
        lg.addHandler(h)
        try:
            _standalone_page(self._SPEC())
        finally:
            lg.removeHandler(h)
        bad = [m for m in seen if "E-1024" in m
               or "CDSVIEW_FILTERS_WITH_CONNECTED" in m]
        assert not bad, bad

    def test_the_guard_sees_e1024(self):
        """The control: the same handler does see an E-1024 Bokeh logs."""
        import logging
        from bokeh.embed import file_html
        from bokeh.models import BooleanFilter, CDSView, ColumnDataSource
        from bokeh.plotting import figure as _fig
        from bokeh.resources import INLINE
        f = _fig()
        f.line("x", "y", source=ColumnDataSource({"x": [1, 2], "y": [1, 2]}),
               view=CDSView(filter=BooleanFilter([True, False])))
        seen = []

        class _Keep(logging.Handler):
            def emit(self, record):
                seen.append(record.getMessage())

        lg = logging.getLogger("bokeh.core.validation.check")
        h = _Keep(level=logging.WARNING)
        lg.addHandler(h)
        try:
            file_html(f, INLINE)
        finally:
            lg.removeHandler(h)
        assert any("E-1024" in m for m in seen), seen

    def test_each_panels_line_holds_its_own_rows(self):
        r, _caught = _standalone(self._SPEC())
        from bokeh.plotting import figure as _fig
        root = getattr(r, "_last_layout_root", None)
        figs = list(root.select({"type": _fig})) if root is not None else []
        panels = []
        for f in figs:
            lines = [x for x in f.renderers if type(x.glyph).__name__ == "Line"]
            if not lines:
                continue
            groups = set()
            for ln in lines:
                data = ln.data_source.data
                xs = [float(data["weight"][i]) for i in _view_rows(ln)]
                groups |= {float(_DF.loc[_DF["weight"] == x, "foreign"]
                                 .iloc[0]) for x in xs}
                # Flipped (WP-29 P0.1): _DF's weights of the panel's group
                # in the data's order, where this held xs == sorted(xs).
                grp = float(_DF.loc[_DF["weight"] == xs[0], "foreign"].iloc[0])
                assert xs == [float(w) for w in
                              _DF.loc[_DF["foreign"] == grp, "weight"]], (
                    "not joined in the data's order", xs)
                assert len(xs) == 5, xs
            assert len(groups) == 1, groups
            panels.append(groups.pop())
        assert sorted(panels) == [0.0, 1.0], panels


# ---------------------------------------------------------------------------
# WP-29 P0.2: a by() graph's panels share range objects the same way in
# both modes.
# ---------------------------------------------------------------------------
_BY_CASES = [c for c in CORPUS
             if any(str((g.get("graph_options") or {}).get("by") or "").strip()
                    for g in c.values[1]["graphs"])]


def _partition(figs, attr):
    """Which panels share a range object, as sorted groups of titles."""
    groups = {}
    for f in sorted(figs, key=lambda f: str(f.title.text if f.title else "")):
        groups.setdefault(id(getattr(f, attr)), []).append(
            str(f.title.text if f.title else ""))
    return sorted(groups.values())


class TestByPanelsShareInBothModes:
    @pytest.mark.parametrize("name,spec", _BY_CASES)
    def test_the_sharing_partition_agrees(self, name, spec):
        from bokeh.plotting import figure as _Fig
        r, _ = _standalone(spec)
        saved = [f for f in r.figures.values() if isinstance(f, _Fig)]
        doc, _ = _served(spec)
        served = [m for root in doc.roots for m in root.references()
                  if isinstance(m, _Fig)]
        for attr in ("x_range", "y_range"):
            assert _partition(saved, attr) == _partition(served, attr), attr


class TestTheServedAppHasNoStaleCue:
    """WP-29 P0.17: the served app refits every layer after a move and
    carries no cue model and no muted renderer (decision M3)."""

    @pytest.mark.parametrize("t,filt,move,go", [
        ("lfit", "foreign, type(dropdown)", ("Select", "Foreign"), None),
        ("histogram", "price, type(range)",
         ("RangeSlider", (4500.0, 11385.0)), {"by": "foreign"}),
        ("lfitci", "price, type(slider)", ("Slider", 4500.0), None),
    ], ids=["lfit dropdown", "histogram by() range", "lfitci slider"])
    def test_no_model_tagged_dash_stale(self, t, filt, move, go):
        from test_server_layer_defects import plot_for
        spec = _spec([_sc(), plot_for(t)], {"filter": filt}, go)
        doc, _ = _served(spec)
        kind, want = move
        w = [x for x in _widgets_of(doc) if type(x).__name__ == kind][0]
        if isinstance(w, Select):
            want = [v for v, lab in w.options if lab == want][0]
        _fire(w, want)
        tagged = [m for m in doc.models
                  if any(str(tg).startswith("dash_stale")
                         for tg in (getattr(m, "tags", None) or []))]
        assert tagged == []
        assert not any(getattr(m, "muted", False) for m in doc.models
                       if type(m).__name__ == "GlyphRenderer")


class TestTheGlyphProfile:

    def test_it_records_muted(self):
        from bokeh.plotting import figure
        fig = figure()
        a = fig.line([1, 2], [1, 2])
        fig.line([1, 2], [2, 1])
        a.muted = True
        prof = _glyph_profile(fig)
        assert [e["muted"] for e in prof] == [True, False]


class TestTheStaleStatusSkip:
    """D12-1: only the saved page's status Div tagged dash_stale_status is
    skipped, through the existing allowance."""

    def test_only_a_div_tagged_dash_stale_status_is_skipped(self):
        keep = Div(text="x", tags=["other"])
        skip = Div(text="", tags=["dash_stale_status"])
        figs = []
        assert _layout_tree([keep, skip], figs) == [("Div", ("text", "x"))]
        assert _is_stale_status(skip) and not _is_stale_status(keep)

    def test_a_saved_page_with_a_fit_and_a_filter_compares_equal_to_its_served_twin(
            self):
        from test_server_layer_defects import plot_for
        spec = _spec([_sc(), plot_for("lfit")],
                     {"filter": "foreign, type(dropdown)"})
        r, _ = _standalone(spec)
        assert any(_is_stale_status(m)
                   for m in r._last_layout_root.references())
        pair = _render_pair("lfit with a dropdown", spec)
        assert pair["std"]["tree"] == pair["srv"]["tree"]
