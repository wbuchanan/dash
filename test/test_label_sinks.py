"""test_label_sinks.py -- every place user text reaches the page, in both
render modes, and how BokehJS renders each one.

ROADMAP.md WP-20, TR-20.3 and acceptance AC-20.2: "A hostile variable label
cannot execute script in either mode."  GAPS.md I3 recorded that dash puts a
user-controlled variable label into HoverTool ``tooltips`` unescaped, and
that the only thing keeping it inert was BokehJS.  This file finds every
place user text lands, records how BokehJS renders it, and pins both.

Method
------
One hostile dashboard is built per payload in each render mode: the saved
page (``DashRenderer``) and the served app (``ServerAppBuilder``, imported
and run the way ``bokeh serve`` runs it).  Every input that can reach the
page carries a tagged payload: variable labels, value labels, string data,
every textbox option, legend and tick labels, the KPI cards, the dashboard
header, filter titles and tab titles.  Then every property of every model
in each document is walked, and each string that holds a tag is recorded
as a *carrier*.

* ``TestInventory`` fails if user text reaches any (model, property) that
  ``CLASSIFIED`` does not name, so a new sink cannot arrive unreviewed.
* ``TestTextSinks`` / ``TestSliderTitles`` / ``TestHtmlSinks`` /
  ``TestDataSinks`` check that each classified sink carries the text the
  way its rendering needs: raw where BokehJS renders text, escaped exactly
  once where it renders HTML.
* ``TestTooltips``, ``TestJavaScript``, ``TestTeX``, ``TestPages`` and
  ``TestServedSource`` pin the rest.  ``TestBokehVersion`` pins the library
  that all of it rests on.

The inventory (bokeh 3.9.0)
---------------------------
"Text" means BokehJS never parses the string as HTML: it is drawn on the
canvas or appended as a DOM text node.

=====================================  ================================  ===========================
input                                  model.property                    rendered as
=====================================  ================================  ===========================
title()                                Title.text                        canvas text
subtitle() note() caption()            Label.text                        canvas text
xtitle() ytitle() ytitle2(), and the   Axis.axis_label                   canvas text
default: the variable label
xlabel(# "text")                       Axis.major_label_overrides, and   canvas text
                                       CustomJSTickFormatter.args
ylabel2(# "text")                      CustomJSTickFormatter.args        canvas text (formatter)
by() panel title: value label          Title.text                        canvas text
colorvar colour bar: variable label    ColorBar.title                    canvas text
legend key: variable label;            LegendItem.label                  DOM text node
legend(label(# "text")); colorvar
key: value label
colorvar legend: variable label        Legend.title                      DOM text node
tooltip row label: variable label      HoverTool.tooltips[i][0]          DOM text node
tooltip row value                      HoverTool.tooltips[i][1]          HTML -- dash writes only
                                                                         ``@{name}{format}`` there
string data values                     ColumnDataSource.data             data: tooltip @{name} is
                                                                         escaped by BokehJS; mlabel
                                                                         LabelSet is canvas text
filter title, dropdown: label() or     Select.title                      DOM text node
the variable label
filter title, slider/range/date        Slider/RangeSlider/DateSlider/    DOM text node, but
                                       DateRangeSlider.title             innerHTML if it holds TeX
dropdown option: value label or        Select.options[i][1]              DOM text node
string value
tabs() title                           TabPanel.title                    DOM text node
KPI title, subtitle, and value         Div.text                          HTML
KPI card rebuilt in the saved page     CustomJS.args kpi_config_json     HTML: _FILTER_JS joins it
                                                                         into Div.text
dashboard title, subtitle              Div.text (Bootstrap: page HTML)   HTML
page title                             <title> / Document.title          escaped by Bokeh's template
=====================================  ================================  ===========================

Why each classification holds (bundled BokehJS, bokeh/server/static/js)
-----------------------------------------------------------------------
* Tooltip rows given as ``(label, field)`` tuples: ``HoverToolView.
  _create_template`` builds the label cell as ``div({...}, `${label}: `)``,
  and ``core/dom``'s element builder appends a string child with
  ``document.createTextNode``, so the label is text whatever it holds,
  including ``@x{safe}``.  The FIELD is different.  ``_render_template``
  passes it to ``replace_placeholders_html``, which escapes each value it
  substitutes (unless the format is ``{safe}``) but leaves the field's own
  literal text alone, then parses the whole string with ``DOMParser`` and
  appends the nodes.  The field is HTML, and user text must never be in it.
  A tooltip given as one string is an HTML template (``_render_tooltips``).
* ``Legend``: each entry is ``div({class: legend_css.label}, `${label}`)``
  and the title ``div({class: legend_css.title}, this.model.title)``.
* ``SelectView.options_el``: ``option({value: label}, label)``.
* ``InputWidgetView._build_title_el`` puts a string title into a ``<label>``
  as a text child; only an ``HTML`` model would be rendered as markup.
* ``TabsView``: ``div({class: [...]}, tab.title)``.
* ``Title``, ``Label``, ``LabelSet``, ``ColorBar`` and axis and tick labels
  are drawn on the canvas.  A TeX string among them is rendered by MathJax
  to an SVG that is drawn as an image, which runs nothing.
* ``Div.text`` is ``innerHTML`` (``MarkupView``), after ``process_tex``
  unless ``disable_math`` is set.

The TeX finding, fixed with this file
-------------------------------------
Two of these sinks render as HTML after all when the text holds a TeX
delimiter pair -- ``$$..$$``, ``\\[..\\]`` or ``\\(..\\)`` -- and MathJax is
loaded:

* ``AbstractSliderView._update_title`` sets ``textContent``, except that for
  a title holding TeX it sets ``innerHTML = process_tex(title)``.
  ``WidgetView.process_tex`` copies the text around the delimiters in
  unchanged, so a variable label such as ``\\(x\\)<img src=x onerror=...>``
  on a range filter put a live ``<img>`` into the page.
* ``Div`` runs ``process_tex`` over its escaped text.  ``bokeh-mathjax.js``
  loads every TeX package, ``html`` among them, with no ``safe`` filter, so
  ``$$\\href{javascript:...}{x}$$`` became a live ``<a href>`` in the card
  and ``\\style{...}`` a style attribute.

A served page always loads MathJax (``bokeh.embed.server`` bundles with
``objs=None``, which forces every component).  A saved page loads it when a
slider title, Div, axis label or text annotation holds a TeX pair
(``bokeh.embed.bundle._model_requires_mathjax``), so the hostile label
switched MathJax on by itself.  Filter titles now pass through
``_dash_inert_tex``, and every Div dash builds sets ``disable_math``.
"""
from __future__ import annotations

import ast
import html
import importlib.util
import io
import itertools
import json
import os
import re
import sys
import tokenize
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pytest

import bokeh
from bokeh.document import Document
from bokeh.embed.util import contains_tex_string
from bokeh.model import Model
from bokeh.models import Div, HoverTool, LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

#: The bokeh versions the behaviour described above was verified on.  See
#: TestBokehVersion for what "verified" means and how to extend this set.
VERIFIED_BOKEH = {"3.8.0", "3.9.0"}

# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------

SCRIPT = "<script>alert(1)</script>"
IMG = "<img src=x onerror=alert(1)>"
QUOTES = "\"dq\" 'sq'"
FIELD = "@x{safe} $index"
SAFE = "{safe}"
#: BokehJS reads each of these as TeX: \( \) inline, $$ $$ and \[ \] display.
TEX_INLINE = "\\(x\\)" + IMG
TEX_DISPLAY = "$$\\href{javascript:alert(1)}{x}$$"
TEX_BRACKET = "\\[\\style{background:url(//evil.example/x)}{x}\\]"

PAYLOADS = {
    "script": SCRIPT,
    "img": IMG,
    "quotes": QUOTES,
    "field": FIELD,
    "safe": SAFE,
    "tex_inline": TEX_INLINE,
    "tex_display": TEX_DISPLAY,
    "tex_bracket": TEX_BRACKET,
    "all": SCRIPT + IMG + QUOTES + " " + FIELD + " " + SAFE,
}
TEX_PAYLOADS = ("tex_inline", "tex_display", "tex_bracket")
MODES = ("standalone", "served")

#: U+2060 WORD JOINER: what _dash_inert_tex puts inside a TeX delimiter.
WJ = "⁠"
#: Every TeX delimiter BokehJS or Bokeh looks for, open or close.
_TEX_DELIM_RE = re.compile(r"\$\$|\\[()\[\]]")

_TAG_RE = re.compile(r"QZ([a-z0-9]+)ZQ")


def tag(sid):
    """The marker an input carries, so its carriers can be found."""
    return f"QZ{sid}ZQ"


def _without(chars, s):
    return "".join(c for c in s if c not in chars)


# ---------------------------------------------------------------------------
# The hostile dashboard
# ---------------------------------------------------------------------------

_N = 12
_DATE0 = 14977.0  # 02jan2001, as a Stata %td
_COLS = ("mpg", "weight", "price", "foreign", "rep", "make", "d", "d2")


def hostile_inputs(payload):
    """``(spec, data, expected)`` for one payload.

    ``expected[sid]`` is the text the input tagged *sid* resolves to once
    dash's own option grammar has read it.  A text sink must carry exactly
    that, and an HTML sink must carry it escaped once.  Where a character of
    the payload is the grammar's own syntax, the payload goes in without it,
    as a Stata user would have to write it: a double quote inside a
    textbox, legend label() or tick label (Stata reads it as the end of the
    string), and a ``/`` or ``:`` in a tabs() title (they separate tabs).
    """
    p = payload
    exp = {}

    def free(sid):
        exp[sid] = tag(sid) + p
        return exp[sid]

    def quoted(sid):
        exp[sid] = tag(sid) + _without('"', p)
        return exp[sid]

    def tab(sid):
        exp[sid] = (tag(sid) + _without("/:", p)).strip()
        return exp[sid]

    df = pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, _N),
        "weight": np.linspace(1760.0, 4840.0, _N),
        "price": np.linspace(3291.0, 15906.0, _N),
        "foreign": [0.0, 1.0] * (_N // 2),
        "rep": [1.0, 2.0, 3.0] * (_N // 3),
        "make": [free(f"sv{i}") for i in range(_N)],
        "d": [_DATE0 + 30.0 * i for i in range(_N)],
        "d2": [_DATE0 + 30.0 * i for i in range(_N)],
    })
    value_labels = {
        "origin": {"0": free("vlo0"), "1": free("vlo1")},
        "replab": {"1": free("vlr1"), "2": free("vlr2"), "3": free("vlr3")},
    }
    data = make_data_json(df, value_labels,
                          {"foreign": "origin", "rep": "replab"})
    sj = data["StataJSON"]
    sj["variableLabels"] = {c: free("vl" + c) for c in _COLS}
    sj["variableIsString"]["make"] = True
    sj["variableTypeIsString"]["make"] = True

    def textbox(sid):
        return '"%s"' % quoted(sid)

    filters = " || ".join([
        'foreign, type(dropdown) label("%s")' % (tag("fdd") + p),
        "make, type(dropdown)",
        "weight, type(range)",
        'price, type(slider) label("%s")' % (tag("fsl") + p),
        "rep, type(slider)",
        "d, type(range)",
        "d2, type(slider)",
    ])
    # The label() text is whatever dash's own filter grammar makes of it.
    for f in dr.DashRenderer._parse_filter_raw(filters):
        if f.get("label"):
            m = _TAG_RE.search(f["label"])
            if m:
                exp[m.group(1)] = f["label"]

    def graph(name, plots, **go):
        opts = {"name": name}
        opts.update(go)
        return {"name": name, "graph_options": opts, "options": {},
                "plots": plots, "if_expr": "", "in_expr": ""}

    graphs = [
        graph("g1", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mlabel": "make"}},
            {"type": "line", "yvar": "price", "xvar": "weight",
             "options": {}},
        ],
            title=textbox("gtitle"), subtitle=textbox("gsub"),
            note=textbox("gnote"), caption=textbox("gcap"),
            hover="make price",
            xlabel='2000 "%s" 3000' % quoted("tick1"),
            legend='label(2 "%s")' % quoted("leglab")),
        graph("g2", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
        ], by="foreign", xtitle=textbox("xtitle"), ytitle=textbox("ytitle")),
        graph("g3", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"colorvar": "rep", "colordiscrete": "yes"}},
        ]),
        graph("g4", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"colorvar": "price"}},
        ]),
        graph("g5", [
            {"type": "histogram", "var": "mpg", "options": {}},
        ]),
        graph("g6", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {"yaxis": "2"}},
        ],
            # GAPS2 B7: ytitle2() is read as a textbox, as ytitle() is, so
            # its text reaches the second axis without quotes or sub-options.
            ytitle2=textbox("ytitle2"),
            ylabel2='5000 "%s" 10000' % quoted("tick2")),
        # WP-28 X2: ztitle() titles the colour key too -- a second source
        # beside the variable label g3/g4 already carry, so two new
        # graphs prove it without disturbing the vlprice/vlrep sinks.
        graph("g7", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"colorvar": "price"}},
        ], ztitle=textbox("zt")),
        graph("g8", [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"colorvar": "rep", "colordiscrete": "yes"}},
        ], ztitle=textbox("zt")),
    ]
    kpis = [
        {"name": "k1", "stat": "mean", "var": "mpg", "fmt": "%9.1f",
         "title": free("ktitle"), "subtitle": free("ksub")},
        # update() naming a by() graph: the saved page used to draw a card
        # per panel, titled "<title> (<value label>)"; one card now, in
        # both modes (test_keyword_names.py).
        {"name": "k2", "stat": "mean", "var": "mpg", "fmt": "%9.1f",
         "update": "g2", "title": free("kftitle")},
        # No statistic: the card shows the value Stata sent.
        {"name": "k3", "title": "k3", "display": free("kval")},
    ]
    spec = {
        "graphs": graphs,
        "kpis": kpis,
        "build_options": {
            "layout": "auto", "link": "", "theme": "", "scheme": "",
            "session_scheme": "",
            "title": free("dtitle"), "subtitle": free("dsub"),
            "registry": "g1 g2 g3 g4 g5 g6 g7 g8 k1 k2 k3",
            "tabs": "%s: g1 g2 g3 k1 / %s: g4 g5 g6 g7 g8 k2 k3"
                    % (tab("tab1"), tab("tab2")),
            "filter": filters,
            "filter_position": "top", "level": "95",
            "formats": {"d": "%td", "d2": "%td"},
        },
    }
    return spec, data, exp


# ---------------------------------------------------------------------------
# Building each mode, and walking what it built
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Carrier:
    """One string holding user text, and where it sits."""
    model: Model
    kind: str   # the model's class name
    prop: str   # the property; "tooltips.label" / "options.value" split out
    text: str


def _strings(value):
    """Every string inside one property value (models are walked apart)."""
    if isinstance(value, str):
        yield value
    elif value is None or isinstance(value, Model):
        return
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, str):
                yield k
            yield from _strings(v)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, np.ndarray):
        if value.dtype == object or value.dtype.kind in "US":
            for v in value.ravel().tolist():
                yield from _strings(v)
    else:
        # A Value spec carries its text; a Field spec names a column.
        for attr in ("value", "field"):
            inner = getattr(value, attr, None)
            if isinstance(inner, str):
                yield inner


def carriers(models):
    """Every string in *models* that holds a tag."""
    out = []
    for m in models:
        kind = type(m).__name__
        for p in sorted(m.properties()):
            try:
                v = getattr(m, p)
            except Exception:  # noqa: BLE001 -- a property with no value
                continue
            if kind == "HoverTool" and p == "tooltips":
                if isinstance(v, str):
                    rows, template = [], [v]
                else:
                    rows, template = list(v or []), []
                for s in template:
                    if _TAG_RE.search(s):
                        out.append(Carrier(m, kind, "tooltips.template", s))
                for row in rows:
                    label, fld = row
                    if _TAG_RE.search(label):
                        out.append(Carrier(m, kind, "tooltips.label", label))
                    if _TAG_RE.search(fld):
                        out.append(Carrier(m, kind, "tooltips.field", fld))
                continue
            if kind == "Select" and p == "options":
                for o in v or []:
                    pair = (o, o) if isinstance(o, str) else tuple(o)
                    for sub, s in zip(("options.value", "options.label"),
                                      pair):
                        if isinstance(s, str) and _TAG_RE.search(s):
                            out.append(Carrier(m, kind, sub, s))
                continue
            for s in _strings(v):
                if _TAG_RE.search(s):
                    out.append(Carrier(m, kind, p, s))
    return out


@dataclass
class Built:
    mode: str
    pid: str
    expected: dict
    models: list
    carriers: list
    html: str = ""
    doc: object = None
    source: str = ""
    warnings: list = field(default_factory=list)


_SEQ = itertools.count()


def _build(root, mode, pid, layout="auto", inputs=None):
    spec, data, expected = inputs or hostile_inputs(PAYLOADS[pid])
    spec["build_options"]["layout"] = layout
    n = next(_SEQ)
    sp = root / f"spec_{n}.json"
    dp = root / f"data_{n}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(data))
    if mode == "standalone":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(str(sp), str(dp))
            page = r.render()
        layout_root = getattr(r, "_last_layout_root", None)
        models = ([] if layout_root is None or layout.startswith("bs")
                  else list(layout_root.references()))
        return Built(mode, pid, expected, models, carriers(models), html=page,
                     warnings=[str(w.message) for w in caught])
    ap = root / f"app_{n}.py"
    # As test_server_facets.served(): the import runs make_document(curdoc())
    # once, outside the capture, so no warning is counted twice.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(
            f"_label_sinks_app_{n}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    seen = {}
    for r in doc.roots:
        for m in r.references():
            seen[m.id] = m
    models = list(seen.values())
    return Built(mode, pid, expected, models, carriers(models), doc=doc,
                 source=ap.read_text(),
                 warnings=[str(w.message) for w in caught])


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """``built(mode, payload_id)``: the hostile dashboard, built once."""
    root = tmp_path_factory.mktemp("label_sinks")
    cache = {}

    def get(mode, pid, layout="auto"):
        key = (mode, pid, layout)
        if key not in cache:
            cache[key] = _build(root, mode, pid, layout)
        return cache[key]

    return get


# ---------------------------------------------------------------------------
# The classification
# ---------------------------------------------------------------------------

CANVAS = "canvas text"
TEXT_NODE = "DOM text node"
SLIDER = "DOM text node, innerHTML if it holds TeX"
HTML = "HTML"
DATA = "data, not rendered as markup"

#: Every (model, property) user text may reach, and how BokehJS renders it.
CLASSIFIED = {
    ("Title", "text"): CANVAS,
    ("Label", "text"): CANVAS,
    ("LinearAxis", "axis_label"): CANVAS,
    ("LogAxis", "axis_label"): CANVAS,
    ("DatetimeAxis", "axis_label"): CANVAS,
    ("LinearAxis", "major_label_overrides"): CANVAS,
    ("ColorBar", "title"): CANVAS,
    ("LegendItem", "label"): TEXT_NODE,
    ("Legend", "title"): TEXT_NODE,
    ("TabPanel", "title"): TEXT_NODE,
    ("Select", "title"): TEXT_NODE,
    ("Select", "options.label"): TEXT_NODE,
    ("HoverTool", "tooltips.label"): TEXT_NODE,
    ("Slider", "title"): SLIDER,
    ("RangeSlider", "title"): SLIDER,
    ("DateSlider", "title"): SLIDER,
    ("DateRangeSlider", "title"): SLIDER,
    ("DatetimeRangeSlider", "title"): SLIDER,
    ("Div", "text"): HTML,
    # The option's value, not its label: compared, never displayed.
    ("Select", "options.value"): DATA,
    ("ColumnDataSource", "data"): DATA,
    # JSON strings a callback parses: the KPI rebuild config, whose title
    # and subtitle it joins into Div.text (see TestHtmlSinks), and the
    # tick-label map a formatter returns from.
    ("CustomJS", "args"): DATA,
    ("CustomJSTickFormatter", "args"): DATA,
    # A colorvar's categories, and the names of its invisible swatch
    # renderers: identifiers BokehJS never puts on the page.
    ("CategoricalColorMapper", "factors"): DATA,
    ("GlyphRenderer", "name"): DATA,
}

#: Where user text must never be.
FORBIDDEN = {
    ("HoverTool", "tooltips.field"):
        "a tooltip field is parsed as HTML (replace_placeholders_html, then "
        "DOMParser) and @name / $name / {safe} in it are interpreted",
    ("HoverTool", "tooltips.template"):
        "a string tooltip is an HTML template",
    ("CustomJS", "code"): "it is JavaScript source",
    ("CustomJSTickFormatter", "code"): "it is JavaScript source",
}


@dataclass(frozen=True)
class Sink:
    sid: str     # test id
    tag: str     # the tagged input it receives
    kinds: tuple  # model class names
    prop: str
    check: str   # "text" | "slider" | "html" | "data" | "json-text" | "json-html"
    modes: tuple = MODES


SINKS = (
    # Canvas text.
    Sink("graph_title", "gtitle", ("Title",), "text", "text"),
    Sink("graph_subtitle", "gsub", ("Label",), "text", "text"),
    Sink("graph_note", "gnote", ("Label",), "text", "text"),
    Sink("graph_caption", "gcap", ("Label",), "text", "text"),
    Sink("xtitle", "xtitle", ("LinearAxis",), "axis_label", "text"),
    Sink("ytitle", "ytitle", ("LinearAxis",), "axis_label", "text"),
    Sink("ytitle2", "ytitle2", ("LinearAxis",), "axis_label", "text"),
    Sink("axis_title_from_variable_label", "vlweight", ("LinearAxis",),
         "axis_label", "text"),
    Sink("xlabel_tick_text", "tick1", ("LinearAxis",),
         "major_label_overrides", "text"),
    Sink("xlabel_tick_formatter_map", "tick1", ("CustomJSTickFormatter",),
         "args", "json-text"),
    Sink("ylabel2_tick_formatter_map", "tick2", ("CustomJSTickFormatter",),
         "args", "json-text"),
    Sink("facet_title_from_value_label", "vlo0", ("Title",), "text", "text"),
    Sink("colorbar_title_from_variable_label", "vlprice", ("ColorBar",),
         "title", "text"),
    # WP-28 X2: ztitle() is a second source for the same (model, property)
    # pair -- the key title gains a second source, none removed.
    Sink("colorbar_title_from_ztitle", "zt", ("ColorBar",), "title", "text"),
    # DOM text nodes.
    Sink("legend_key_from_variable_label", "vlmpg", ("LegendItem",),
         "label", "text"),
    Sink("legend_label_override", "leglab", ("LegendItem",), "label", "text"),
    Sink("colorvar_legend_title_from_variable_label", "vlrep", ("Legend",),
         "title", "text"),
    Sink("colorvar_legend_title_from_ztitle", "zt", ("Legend",), "title",
         "text"),
    Sink("colorvar_legend_key_from_value_label", "vlr1", ("LegendItem",),
         "label", "text"),
    Sink("tab_title", "tab1", ("TabPanel",), "title", "text"),
    Sink("dropdown_title_from_label", "fdd", ("Select",), "title", "text"),
    Sink("dropdown_title_from_variable_label", "vlmake", ("Select",),
         "title", "text"),
    Sink("dropdown_option_from_value_label", "vlo0", ("Select",),
         "options.label", "text"),
    Sink("dropdown_option_from_string_value", "sv0", ("Select",),
         "options.label", "text"),
    Sink("tooltip_label_from_variable_label", "vlmpg", ("HoverTool",),
         "tooltips.label", "text"),
    Sink("tooltip_label_from_hover_variable", "vlmake", ("HoverTool",),
         "tooltips.label", "text"),
    # DOM text nodes that BokehJS switches to innerHTML for TeX.
    Sink("range_title_from_variable_label", "vlweight", ("RangeSlider",),
         "title", "slider"),
    Sink("slider_title_from_label", "fsl", ("Slider",), "title", "slider"),
    Sink("slider_title_from_variable_label", "vlrep", ("Slider",), "title",
         "slider"),
    # A %td variable: both modes build a DateRangeSlider/DateSlider (the
    # served app read no %td for its filters before WP-27 and built numeric
    # ones).  Every one is an AbstractSlider with the same title rendering.
    Sink("date_range_title_from_variable_label", "vld",
         ("DateRangeSlider",), "title", "slider"),
    Sink("date_slider_title_from_variable_label", "vld2",
         ("DateSlider",), "title", "slider"),
    # HTML.
    Sink("kpi_title", "ktitle", ("Div",), "text", "html"),
    Sink("kpi_subtitle", "ksub", ("Div",), "text", "html"),
    Sink("dashboard_title", "dtitle", ("Div",), "text", "html"),
    Sink("dashboard_subtitle", "dsub", ("Div",), "text", "html"),
    Sink("kpi_title_beside_a_by_graph", "kftitle", ("Div",), "text", "html"),
    # The saved page alone shows a value Stata sent without a statistic,
    # and rebuilds cards in the browser.
    Sink("kpi_value", "kval", ("Div",), "text", "html",
         modes=("standalone",)),
    Sink("kpi_rebuild_title", "ktitle", ("CustomJS",), "args", "json-html",
         modes=("standalone",)),
    Sink("kpi_rebuild_subtitle", "ksub", ("CustomJS",), "args", "json-html",
         modes=("standalone",)),
    # Data.
    Sink("string_data_values", "sv0", ("ColumnDataSource",), "data", "data"),
)


def _matching(b, sink):
    t = tag(sink.tag)
    return [c for c in b.carriers
            if c.kind in sink.kinds and c.prop == sink.prop and t in c.text]


def _cases(checks, payloads=tuple(PAYLOADS)):
    return [pytest.param(s, m, p, id=f"{m}-{s.sid}-{p}")
            for s in SINKS if s.check in checks
            for m in s.modes for p in payloads]


def _json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from _json_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _json_strings(v)


# ===========================================================================
# The inventory
# ===========================================================================

class TestInventory:
    """No user text reaches a (model, property) this file has not
    classified, in either mode, whatever the payload."""

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_every_carrier_is_a_classified_sink(self, built, mode, pid):
        b = built(mode, pid)
        assert b.carriers, "the hostile dashboard carried no tagged text"
        bad = {}
        for c in b.carriers:
            key = (c.kind, c.prop)
            if key in FORBIDDEN or key not in CLASSIFIED:
                bad.setdefault(key, c.text)
        assert not bad, (
            f"{mode}: user text reached (model, property) pairs that are "
            f"forbidden or unclassified:\n" + "\n".join(
                f"  {k}: {FORBIDDEN.get(k, 'not classified')} -- e.g. {v!r}"
                for k, v in sorted(bad.items())) +
            "\nFind how BokehJS renders the new property (text, or HTML) in "
            "bokeh/server/static/js, add it to CLASSIFIED, and give it a Sink.")

    @pytest.mark.parametrize("pid", ["all"])
    def test_both_modes_reach_the_same_sinks(self, built, pid):
        """The served app copies the same helpers by source, so the same
        user text lands in the same places.  One difference is expected:
        the saved page alone rebuilds KPI cards in the browser (CustomJS).
        Both build date sliders for a %td filter (the served app built
        numeric ones before WP-27)."""
        std = {(c.kind, c.prop) for c in built("standalone", pid).carriers}
        srv = {(c.kind, c.prop) for c in built("served", pid).carriers}
        saved_only = {("CustomJS", "args")}
        assert std - saved_only == srv, (
            f"only saved: {sorted(std - srv)}; only served: {sorted(srv - std)}")


class TestEverySinkIsReached:
    """Guard against a blind harness: each Sink really is exercised."""

    @pytest.mark.parametrize("sink,mode", [
        pytest.param(s, m, id=f"{m}-{s.sid}") for s in SINKS for m in s.modes])
    def test_the_tagged_input_reaches_its_sink(self, built, sink, mode):
        b = built(mode, "all")
        assert _matching(b, sink), (
            f"{mode}: nothing tagged {tag(sink.tag)!r} reached "
            f"{'/'.join(sink.kinds)}.{sink.prop}; the harness no longer "
            f"exercises the '{sink.sid}' sink")


# ===========================================================================
# How each sink carries the text
# ===========================================================================

class TestTextSinks:
    """A property BokehJS renders as text must carry the user's text raw.

    Escaping it protects nothing -- the property is never parsed -- and
    shows the entities: ``Men's`` became ``Men&#x27;s``."""

    @pytest.mark.parametrize("sink,mode,pid", _cases({"text"}))
    def test_it_carries_the_raw_text(self, built, sink, mode, pid):
        b = built(mode, pid)
        want = b.expected[sink.tag]
        found = _matching(b, sink)
        assert found, f"{sink.sid}: not reached ({mode}, {pid})"
        for c in found:
            assert want in c.text, (
                f"{sink.sid} ({mode}): {c.kind}.{c.prop} = {c.text!r}; "
                f"expected the raw {want!r}.  BokehJS renders it as "
                f"{CLASSIFIED[(c.kind, c.prop)]}, so it must not be escaped.")

    @pytest.mark.parametrize("sink,mode,pid", _cases({"json-text"}))
    def test_a_tick_label_map_carries_the_raw_text(self, built, sink, mode,
                                                   pid):
        b = built(mode, pid)
        want = b.expected[sink.tag]
        found = _matching(b, sink)
        assert found, f"{sink.sid}: not reached ({mode}, {pid})"
        for c in found:
            vals = [v for v in _json_strings(json.loads(c.text))
                    if tag(sink.tag) in v]
            assert vals and all(want in v for v in vals), (
                f"{sink.sid} ({mode}): the formatter's map holds {vals!r}; "
                f"a tick label is canvas text, so it must be the raw {want!r}")

    @pytest.mark.parametrize("mode", MODES)
    def test_mlabel_draws_the_raw_string_column(self, built, mode):
        b = built(mode, "all")
        # LabelSet(text="make") names the column; Bokeh keeps the string.
        sets = [m for m in b.models if isinstance(m, LabelSet)
                and "make" in (m.text, getattr(m.text, "field", None))]
        assert sets, f"{mode}: no LabelSet draws mlabel(make)"
        for ls in sets:
            col = [str(v) for v in ls.source.data["make"]]
            assert b.expected["sv0"] in col, (
                f"{mode}: mlabel's column does not hold the raw string")


class TestSliderTitles:
    """The slider family renders its title as text unless the title holds a
    TeX delimiter pair, when BokehJS 3.9.0 sets ``innerHTML`` and passes the
    text around the delimiters through raw.  So a slider title must never
    hold one: ``_dash_inert_tex`` breaks each delimiter with a U+2060 WORD
    JOINER, which leaves the title looking the same."""

    @pytest.mark.parametrize("sink,mode,pid", _cases({"slider"}))
    def test_it_holds_no_tex_and_shows_the_text(self, built, sink, mode, pid):
        from bokeh.embed.bundle import _model_requires_mathjax
        b = built(mode, pid)
        want = b.expected[sink.tag]
        found = _matching(b, sink)
        assert found, f"{sink.sid}: not reached ({mode}, {pid})"
        for c in found:
            assert not contains_tex_string(c.text), (
                f"{sink.sid} ({mode}): the title {c.text!r} holds TeX, so "
                f"BokehJS renders it with innerHTML and the markup around "
                f"the delimiters goes in raw")
            assert not _TEX_DELIM_RE.search(c.text), (
                f"{sink.sid} ({mode}): {c.text!r} holds a TeX delimiter")
            assert not _model_requires_mathjax(c.model), (
                f"{sink.sid} ({mode}): this slider makes Bokeh load MathJax")
            assert want in c.text.replace(WJ, ""), (
                f"{sink.sid} ({mode}): {c.text!r} does not show {want!r}")
            if pid not in TEX_PAYLOADS:
                assert want in c.text, (
                    f"{sink.sid} ({mode}): a title with no TeX must be the "
                    f"raw text; got {c.text!r}")


class TestHtmlSinks:
    """``Div.text`` is HTML: the user's text must be in it escaped exactly
    once, and the Div must not hand its text to MathJax."""

    @pytest.mark.parametrize("sink,mode,pid", _cases({"html"}))
    def test_it_carries_the_text_escaped_once(self, built, sink, mode, pid):
        b = built(mode, pid)
        want = b.expected[sink.tag]
        esc = html.escape(want)
        found = _matching(b, sink)
        assert found, f"{sink.sid}: not reached ({mode}, {pid})"
        for c in found:
            assert esc in c.text, (
                f"{sink.sid} ({mode}): {html.escape(want)!r} is not in "
                f"{c.text!r}")
            if esc != want:
                assert want not in c.text, (
                    f"{sink.sid} ({mode}): the raw text reached the HTML")
                assert html.escape(esc) not in c.text, (
                    f"{sink.sid} ({mode}): the text was escaped twice")
            assert c.model.disable_math is True, (
                f"{sink.sid} ({mode}): the Div runs its text through MathJax")

    @pytest.mark.parametrize("sink,mode,pid", _cases({"json-html"}))
    def test_the_kpi_rebuild_config_is_escaped_once(self, built, sink, mode,
                                                    pid):
        """_FILTER_JS rebuilds a card by joining these fields into
        ``kpi_div.text``, so they must arrive escaped."""
        b = built(mode, pid)
        want = b.expected[sink.tag]
        found = _matching(b, sink)
        assert found, f"{sink.sid}: not reached ({mode}, {pid})"
        field_name = {"kpi_rebuild_title": "title",
                      "kpi_rebuild_subtitle": "subtitle"}[sink.sid]
        for c in found:
            cfg = json.loads(c.text)
            hits = [k for k in cfg if tag(sink.tag) in k.get(field_name, "")]
            assert hits, f"{sink.sid}: no {field_name} holds the tag"
            for k in hits:
                assert k[field_name] == html.escape(want), (
                    f"{sink.sid}: the rebuild's {field_name} is "
                    f"{k[field_name]!r}; expected {html.escape(want)!r}")


class TestDataSinks:

    @pytest.mark.parametrize("sink,mode,pid", _cases({"data"}))
    def test_string_data_is_carried_raw(self, built, sink, mode, pid):
        b = built(mode, pid)
        want = b.expected[sink.tag]
        found = _matching(b, sink)
        assert found and all(want in c.text for c in found), (
            f"{sink.sid} ({mode}): the data column does not hold {want!r}")


# ===========================================================================
# Tooltips
# ===========================================================================

#: The only fields dash writes: one placeholder per value, @{name} and an
#: optional numeric or date format, and the histogram's "a to b".
_PLACEHOLDER = r"@\{[^\W\d]\w*\}(?:\{[0-9.,%FT ]+\})?"
_FIELD_RE = re.compile(rf"^{_PLACEHOLDER}(?: to {_PLACEHOLDER})?$")


def _hover_tools(b):
    return [m for m in b.models if isinstance(m, HoverTool)]


class TestTooltips:

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_tooltips_are_label_field_pairs(self, built, mode, pid):
        """Never a string (an HTML template), a DOM template or a
        function: only a list of (label, field) tuples renders the label as
        text."""
        tools = _hover_tools(built(mode, pid))
        assert tools, f"{mode}: the dashboard has no HoverTool"
        for t in tools:
            assert isinstance(t.tooltips, list), (
                f"{mode}: tooltips is {type(t.tooltips).__name__}")
            for row in t.tooltips:
                assert (isinstance(row, tuple) and len(row) == 2
                        and all(isinstance(x, str) for x in row)), (
                    f"{mode}: tooltip row {row!r} is not (label, field)")

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_no_field_uses_safe(self, built, mode, pid):
        for t in _hover_tools(built(mode, pid)):
            for _label, fld in t.tooltips:
                assert "safe" not in fld, (
                    f"{mode}: the field {fld!r} renders a value as raw HTML")

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_user_text_never_reaches_a_field(self, built, mode, pid):
        for t in _hover_tools(built(mode, pid)):
            for _label, fld in t.tooltips:
                assert not _TAG_RE.search(fld), (
                    f"{mode}: user text reached the tooltip field {fld!r}")
                assert _FIELD_RE.match(fld), (
                    f"{mode}: {fld!r} is not a field dash writes")

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_the_label_is_the_raw_variable_label(self, built, mode, pid):
        b = built(mode, pid)
        labels = {lab for t in _hover_tools(b) for lab, _f in t.tooltips}
        for v in ("mpg", "weight", "make", "price"):
            assert b.expected["vl" + v] in labels, (
                f"{mode}: no tooltip row is labelled with {v}'s raw label")


class TestAHostileColumnNameCannotOpenATooltipField:
    """A field is ``@{name}``: a ``}`` in the name ends the placeholder and
    the rest of the name is literal field text, which BokehJS parses as
    HTML.  Stata cannot make such a name, but the renderer reads any data
    file it is given."""

    NAME = "x}<img/src=x/onerror=alert(1)>{safe"

    def _inputs(self):
        df = pd.DataFrame({
            "mpg": np.linspace(12.0, 41.0, 6),
            "weight": np.linspace(1760.0, 4840.0, 6),
            self.NAME: np.linspace(1.0, 6.0, 6),
        })
        spec = {
            "graphs": [{"name": "g1",
                        "graph_options": {"name": "g1", "hover": self.NAME},
                        "options": {}, "if_expr": "", "in_expr": "",
                        "plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""},
        }
        return spec, make_data_json(df), {}

    @pytest.mark.parametrize("mode", MODES)
    def test_it_is_refused_and_named(self, tmp_path, mode):
        b = _build(tmp_path, mode, "column", inputs=self._inputs())
        tools = _hover_tools(b)
        assert tools, f"{mode}: no HoverTool at all"
        for t in tools:
            for _label, fld in t.tooltips:
                assert "<" not in fld and "safe" not in fld, (
                    f"{mode}: the column name opened the field: {fld!r}")
                assert _FIELD_RE.match(fld), (
                    f"{mode}: {fld!r} is not a field dash writes")
        assert any("tooltip" in w and "x}" in w for w in b.warnings), (
            f"{mode}: the refused variable was not named: {b.warnings}")


# ===========================================================================
# JavaScript
# ===========================================================================

class TestJavaScript:

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_user_text_never_reaches_javascript_source(self, built, mode,
                                                       pid):
        """CustomJS and CustomJSTickFormatter code is a constant; user text
        travels in ``args``, as JSON the code parses."""
        for m in built(mode, pid).models:
            code = getattr(m, "code", None)
            if isinstance(code, str):
                assert not _TAG_RE.search(code), (
                    f"{mode}: user text is in the source of a "
                    f"{type(m).__name__}: {code[:200]!r}")


# ===========================================================================
# TeX
# ===========================================================================

class TestTeX:

    @pytest.mark.parametrize("pid", list(TEX_PAYLOADS) + ["all"])
    @pytest.mark.parametrize("mode", MODES)
    def test_every_div_disables_math(self, built, mode, pid):
        """Bokeh would load MathJax for a Div holding TeX, and a Div runs
        its text through it: ``\\href`` and ``\\style`` are live there."""
        from bokeh.embed.bundle import _model_requires_mathjax
        divs = [m for m in built(mode, pid).models if isinstance(m, Div)]
        assert divs, f"{mode}: the dashboard has no Div"
        for d in divs:
            assert d.disable_math is True, (
                f"{mode}: a Div hands its text to MathJax: {d.text[:120]!r}")
            assert not _model_requires_mathjax(d)

    @pytest.mark.parametrize("pid", list(TEX_PAYLOADS))
    @pytest.mark.parametrize("mode", MODES)
    def test_no_slider_title_holds_tex(self, built, mode, pid):
        from bokeh.models.widgets.sliders import AbstractSlider
        sliders = [m for m in built(mode, pid).models
                   if isinstance(m, AbstractSlider)]
        assert sliders, f"{mode}: the dashboard has no slider"
        for s in sliders:
            assert not contains_tex_string(s.title or ""), (
                f"{mode}: {type(s).__name__}.title {s.title!r} holds TeX")


class TestInertTex:
    """``_dash_inert_tex`` -- the unit under TestSliderTitles."""

    @pytest.mark.parametrize("text", [
        "$$x$$", "\\(x\\)", "\\[x\\]", "$$$", "$$$$", "a$$$b$$$c",
        "\\\\(x\\\\)", TEX_INLINE, TEX_DISPLAY, TEX_BRACKET,
        "\\(" + "$$" + "\\]",
    ])
    def test_no_delimiter_survives(self, text):
        out = dr._dash_inert_tex(text)
        assert not _TEX_DELIM_RE.search(out), repr(out)
        assert not contains_tex_string(out), repr(out)
        assert out.replace(WJ, "") == text

    @pytest.mark.parametrize("text", [
        "", "Weight (lbs.)", "Price $", "cost $ 5", "R&D <b>", "a\\b",
        "back\\slash", "\\x", "{safe} @x $index",
    ])
    def test_text_without_tex_is_unchanged(self, text):
        assert dr._dash_inert_tex(text) == text

    def test_it_is_idempotent(self):
        once = dr._dash_inert_tex(TEX_INLINE + TEX_DISPLAY + TEX_BRACKET)
        assert dr._dash_inert_tex(once) == once

    def test_a_non_string_is_read_as_text(self):
        assert dr._dash_inert_tex(12) == "12"

    def test_every_slider_family_title_goes_through_it(self):
        # A dropdown is a Select, whose title is a text node, so it keeps
        # its TeX; every slider family title is neutralised.
        for ftype in ("slider", "range"):
            got = dr._dash_filter_title(TEX_INLINE, "v", ftype)
            assert not contains_tex_string(got), (ftype, got)
            assert got.replace(WJ, "").startswith(TEX_INLINE)
        # The fallback, a variable name, too.
        assert not contains_tex_string(
            dr._dash_filter_title("", "$$v$$", "range"))

    def test_a_dropdown_title_keeps_its_text(self):
        got = dr._dash_filter_title(TEX_INLINE, "v", "dropdown")
        assert got == TEX_INLINE and WJ not in got


# ===========================================================================
# The pages
# ===========================================================================

_ANGLED = [p for p in PAYLOADS if "<" in PAYLOADS[p]]


class TestPages:

    @pytest.mark.parametrize("pid", _ANGLED)
    def test_the_saved_page_never_holds_the_raw_payload(self, built, pid):
        """Bokeh escapes the document JSON it embeds, the header Div's text
        is escaped by dash before that, and the <title> by Bokeh's
        template: the raw payload appears nowhere in the file."""
        page = built("standalone", pid).html
        assert PAYLOADS[pid] not in page

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    def test_the_saved_page_title_is_escaped(self, built, pid):
        b = built("standalone", pid)
        m = re.search(r"<title>(.*?)</title>", b.html, re.S)
        assert m, "the saved page has no <title>"
        assert "<" not in m.group(1)
        assert html.unescape(m.group(1)) == b.expected["dtitle"]

    @pytest.mark.parametrize("pid", _ANGLED + ["quotes"])
    def test_the_bootstrap_header_is_escaped(self, built, pid):
        """The Bootstrap page writes the header as page HTML, not a Div."""
        b = built("standalone", pid, "bs")
        for sid, cls in (("dtitle", "db-title"), ("dsub", "db-subtitle")):
            m = re.search(r'class="%s"[^>]*>(.*?)</' % cls, b.html, re.S)
            assert m, f"no .{cls} header in the Bootstrap page"
            assert m.group(1) == html.escape(b.expected[sid])
        assert PAYLOADS[pid] not in b.html

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    def test_the_served_title_is_the_raw_text(self, built, pid):
        """Document.title is text: Bokeh's server template escapes it into
        <title> (``{{ title | e }}``) and BokehJS assigns document.title."""
        b = built("served", pid)
        assert b.doc.title == b.expected["dtitle"]


# ===========================================================================
# The generated app's source
# ===========================================================================

class TestServedSource:

    @pytest.mark.parametrize("pid", list(PAYLOADS))
    def test_user_text_is_only_ever_inside_a_string_literal(self, built,
                                                            pid):
        """Spec and data travel base64-encoded; what the builder writes
        from them (the parsed filters) goes through repr().  So user text
        can appear in the app only inside a string literal."""
        src = built("served", pid).source
        ast.parse(src)
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if _TAG_RE.search(tok.string):
                assert tok.type == tokenize.STRING, (
                    f"user text outside a string literal: {tok.string[:120]!r}")


# ===========================================================================
# The library all of this rests on
# ===========================================================================

class TestBokehVersion:

    def test_bokeh_is_a_version_this_was_verified_on(self):
        """Every text sink above is safe because of how BokehJS renders it,
        not because of anything dash does, so it is pinned to the Bokeh
        versions where that was checked.

        Verified on bokeh 3.9.0, 23sep2026:

        In a browser.  A standalone dashboard whose variable ``y`` had the
        label ``<img src=x onerror="document.title='PWNED'">Y label`` was
        opened in Chromium.  The axis title (canvas) showed the literal text.
        So did the legend entry and the hover tooltip, where the label is a
        text node inside a DIV reading ``<img src=x onerror=...>Y label: ``.
        There was no IMG element anywhere in the document, shadow roots
        included, and ``document.title`` was unchanged.  The page's CSP
        includes ``script-src 'unsafe-inline'``, which would allow an inline
        ``onerror``, so what protected it was BokehJS rendering the label as
        text, not the CSP.

        In the bundled BokehJS source (bokeh/server/static/js):
        ``HoverToolView._create_template`` (label cell as a text child) and
        ``_render_template`` (field through ``replace_placeholders_html``
        and ``DOMParser``); ``core/dom``'s element builder (string children
        via ``document.createTextNode``); the Legend view (labels and title
        as text children); ``SelectView.options_el`` (``option({value:
        label}, label)``); ``InputWidgetView._build_title_el``; ``TabsView``
        (``div(..., tab.title)``); ``MarkupView`` (``innerHTML``, through
        ``process_tex`` unless ``disable_math``);
        ``AbstractSliderView._update_title`` (``innerHTML =
        process_tex(title)`` when the title holds TeX); ``WidgetView.
        process_tex`` (text around the TeX copied through raw); and
        ``bokeh-mathjax.js``'s ``tex2svg`` (``AllPackages``, including
        ``html``: ``\\href``, ``\\style``, ``\\class``, ``\\cssId``).  In
        Python, ``bokeh.embed.bundle._model_requires_mathjax`` and
        ``bundle_for_objs_and_resources`` decide when MathJax is loaded.

        bokeh 3.8.0 -- the version in the Python Stata is configured with
        on the development machine, so the one Stata-built dashboards carry
        -- was compared at step 1 below on 23sep2026: the slider title
        (``innerHTML`` through ``process_tex`` when it holds TeX), the text
        around TeX copied through raw, the input widgets' ``label`` title,
        ``Select`` options, the Legend's labels and title, the tooltip's
        label cell and HTML-parsed field, and ``core/dom``'s
        ``createTextNode`` for string children are the same code as 3.9.0's.
        Steps 2 and 3 were run on 3.8.0 on 24sep2026 (WP-25, when the suite
        first ran under Stata's interpreter): pages built by
        ``/opt/anaconda3/bin/python3`` with bokeh 3.8.0 and the label above
        on ``y``, a saved page and the served app run as ``dash serve``
        runs it (MathJax loaded), were opened in Chromium and a point
        hovered.  In both the axis title showed the literal text, the
        legend entry and the tooltip's label cell were text nodes inside
        DIVs reading it, there was no IMG element anywhere (shadow roots
        included), and ``document.title`` stayed ``dash``.

        To re-verify after a Bokeh upgrade:

        1. Re-read each function named above in the new bundle.  Confirm
           that a string label or title still becomes a text node, that a
           tuple tooltip's field is still the only part parsed as HTML, and
           that the slider and Div TeX paths still behave as
           ``_dash_inert_tex`` and ``disable_math`` assume.
        2. Build a standalone dashboard from a dataset whose variable ``y``
           is labelled ``<img src=x onerror="document.title='PWNED'">Y
           label`` -- the check recorded above.  Open it in a real browser,
           hover a point, and check that the axis title, legend entry and
           tooltip show the literal text, that no IMG element exists
           (search shadow roots too), and that ``document.title`` is
           unchanged.
        3. Repeat step 2 under ``dash serve``, which always loads MathJax.
        4. Run this file, then add the new version to ``VERIFIED_BOKEH``.
        """
        assert bokeh.__version__ in VERIFIED_BOKEH, (
            f"bokeh {bokeh.__version__} is installed, but the text sinks "
            f"test_label_sinks.py pins were verified only on "
            f"{sorted(VERIFIED_BOKEH)}.  Their safety comes from BokehJS "
            f"rendering labels as text, which can change between releases.  "
            f"Re-verify in a browser as this test's docstring describes, "
            f"then add the version to VERIFIED_BOKEH.")
