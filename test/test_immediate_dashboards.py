"""A dashboard of immediate graphs alone, and what drawing one measured.

Measured 24sep2026 with the console binary at a17c552.  After
``dash scatteri 1 2, name(a1)``, ``dash build`` stopped with "dash build: no
variables identified across registered graphs.", r(198), saved and served,
and with no data in memory the one-line ``dash scatteri 1 2 3 4, saving(f)``
said "no variables identified in plot specification", r(198) -- where twoway
draws scatteri, pci, pcarrowi and function alone, with data in memory or
none.  dash.ado now writes such a dashboard's data file itself: jsonio's
layout holding no variable and no observation, ``_EMPTY_DATA`` below, which
test_parser.cscript P1A-72 and P1A-75 pin on the Stata side.  The one-line
route used to export one observation of the first variable in memory
instead, a placeholder no layer read.

What the same work measured, each against twoway:

* An immediate plot whose every point is missing -- ``scatteri . . . .`` --
  draws nothing in twoway and says nothing.  dash drew nothing and said
  "dash: graph '?' plot 1 (scatteri) drew nothing from 1 observations":
  the observation was the placeholder, and '?' what the saved page called
  a graph with no name (the served app called it '').  An immediate layer
  draws from its own values, not from the observations, so it is not
  reported; a data layer that draws nothing still is, by its graph's name,
  or by its place alone when the graph has none.
* ``twoway function y = sqrt(x), range(-1 1)`` draws the curve from 0 to
  1, and ``log(x)`` over the same range its right half.  dash drew
  nothing and reported the layer empty: numpy warns on the square root of
  a negative number, and the warning, raised inside an eval() whose
  builtins are empty, looked ``__import__`` up there and failed the whole
  layer.  A value Stata cannot hold -- 1/0, x/0, 10^400, exp(1000*x) -- is
  missing in Stata; twoway draws nothing for it, in silence, and dash now
  does the same.  An expression dash refuses to evaluate is still
  reported, in both modes, with data in memory or none.
* twoway ignores if and in on scatteri, pci and function: ``twoway
  scatteri 1 2 3 4 if foreign == 2`` draws both points (from the serset it
  draws).  dash drew them too, and the saved page said the layer's
  qualifier "could not be applied" when the dashboard had no data.
* twoway pci is an immediate pcspike: from its SVG export under s2color,
  stcolor, s1mono, s2mono, s2gmanual and economist, a pci is stroked in
  pcspike's colour -- the plain p# cycle, so s2mono's second plot is
  #A0A0A0 where a line's is #000000 -- at pcspike's width, and keyed in
  the legend as pcspike is.  dash drew pci in line's colour at line's
  width, and with no legend key.  It is drawn by ``map_pcspike`` now, as
  pcarrowi is by ``map_pcarrow``.  (Under economist twoway draws both at
  the scheme's ``linewidth pother``, thick, and dash draws pcspike at
  1.5px: pcspike's own width, the same for pci and pcspike here.)
"""
import itertools
import json
import math
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Legend, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_adversarial_matrix import _load_app  # noqa: E402

#: The data file dash.ado writes for a dashboard that exports no variable.
_EMPTY_DATA = ('{"values":[],"variableIsString":{},"variableNames":[],'
               '"variableLabels":{},"valueLabelNames":{},"valueLabels":{},'
               '"numberOfRecords":0,"numberOfVariables":0}')

#: Six observations, for a dashboard that has data beside its immediate
#: graphs.
_DF = pd.DataFrame({
    "y":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "x":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "m":  [float("nan")] * 6,
    "f":  [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
    "y1": [0.0] * 6, "x1": [0.0] * 6, "y2": [1.0] * 6, "x2": [1.0] * 6,
})

_MODES = ("saved", "served")
_SEQ = itertools.count()


# ===========================================================================
# Harness: a spec in dash.ado's shape, drawn saved and served
# ===========================================================================

def _graph(name, plots, **graph_options):
    """One graph as dash.ado registers it; *name* "" is the one-line form's
    graph, which has none."""
    g = {"plots": plots, "graph_options": dict(graph_options),
         "if_expr": "", "in_expr": ""}
    if name:
        g["name"] = name
        g["graph_options"]["name"] = name
    return g


def _spec(graphs, **build):
    b = {"layout": "auto", "link": "", "theme": "", "title": "",
         "subtitle": "",
         "registry": " ".join(g.get("name", "") for g in graphs).strip()}
    b.update(build)
    return {"graphs": graphs, "kpis": [], "build_options": b}


def _inputs(tmp_path, spec, data):
    """spec.json and data.json.  *data* is the data file's text, or a
    DataFrame written as jsonio writes one."""
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        fh.write(data if isinstance(data, str)
                 else json.dumps(make_data_json(data)))
    return sp, dp


def _saved(tmp_path, spec, data):
    sp, dp = _inputs(tmp_path, spec, data)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        r.render()
    return list(r.figures.values()), [str(w.message) for w in caught]


def _served(tmp_path, spec, data):
    sp, dp = _inputs(tmp_path, spec, data)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "immdash_%d" % next(_SEQ))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return list(doc.select({"type": Plot})), [str(w.message) for w in caught]


def _draw(mode, tmp_path, spec, data=_EMPTY_DATA):
    """(figures, warning texts) for *spec* in *mode*."""
    sub = tmp_path / ("%s_%d" % (mode, next(_SEQ)))
    sub.mkdir()
    return (_saved if mode == "saved" else _served)(sub, spec, data)


def _num(v):
    f = float(v)
    return None if math.isnan(f) else f


def _layers(figs):
    """(glyph class, {glyph field: values}) for each data renderer, NaN as
    None so that two modes can be compared, sorted so that the order the
    served document lists its figures in does not matter."""
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if g is None:
                continue
            data = r.data_source.data
            coords = {}
            for a in ("x", "y", "x0", "y0", "x1", "y1"):
                fld = getattr(g, a, None)
                fld = fld if isinstance(fld, str) else getattr(fld, "field",
                                                               None)
                if fld and fld in data:
                    coords[a] = [_num(v) for v in data[fld]]
            out.append((type(g).__name__, coords))
    return sorted(out, key=repr)


def _empty_reports(warns):
    return [w for w in warns if "drew nothing" in w]


def _one_line(plot_type, figs):
    """The renderers of *figs* whose glyph is a *plot_type* glyph."""
    return [r for f in figs for r in f.renderers
            if type(getattr(r, "glyph", None)).__name__ == plot_type]


# ===========================================================================
# 1. The dashboard is drawn from a data file with no variable in it
# ===========================================================================

_IMMEDIATE = [
    ({"type": "scatteri", "values": [[1.0, 2.0], [3.0, 4.0]],
      "options": {}}, "Scatter"),
    ({"type": "pci", "values": [[0.0, 0.0, 1.0, 1.0]], "options": {}},
     "Segment"),
    ({"type": "pcarrowi", "values": [[0.0, 0.0, 1.0, 1.0, "A", 3]],
      "options": {}}, "Segment"),
    ({"type": "function", "expr": "x^2", "options": {"range": "0 2"}},
     "Line"),
]


class TestTheDataFileIsTheOneDashAdoWrites:
    def test_dash_ado_writes_this_text(self):
        """``_dash_empty_data`` writes exactly ``_EMPTY_DATA``: the two
        halves of the contract are pinned to one text."""
        with open(os.path.join(_HERE, "..", "dash.ado"),
                  encoding="utf-8") as fh:
            ado = fh.read()
        m = re.search(r"(?ms)^program define _dash_empty_data\b(.*?)^end\b",
                      ado)
        assert m, "dash.ado has no _dash_empty_data program"
        w = re.search(r"file write `fh' `\"(.*?)\"'", m.group(1))
        assert w, "_dash_empty_data writes no compound-quoted text"
        assert w.group(1) == _EMPTY_DATA

    def test_it_is_json_with_no_variable_and_no_observation(self):
        d = json.loads(_EMPTY_DATA)
        assert d["values"] == [] and d["variableNames"] == []
        assert d["numberOfRecords"] == 0 and d["numberOfVariables"] == 0


@pytest.mark.parametrize("mode", _MODES)
class TestADashboardOfImmediateGraphsAloneIsDrawn:
    @pytest.mark.parametrize("plot,glyph", _IMMEDIATE,
                             ids=[p["type"] for p, _ in _IMMEDIATE])
    def test_each_type_is_drawn(self, tmp_path, mode, plot, glyph):
        figs, warns = _draw(mode, tmp_path, _spec([_graph("a1", [plot])]))
        assert len(figs) == 1
        drawn = [k for k, c in _layers(figs) if any(c.values())]
        assert glyph in drawn, (mode, _layers(figs))
        assert not _empty_reports(warns), warns

    def test_four_graphs_are_drawn_as_the_saved_page_draws_them(
            self, tmp_path, mode):
        spec = _spec([_graph("a%d" % i, [p])
                      for i, (p, _) in enumerate(_IMMEDIATE, 1)])
        figs, warns = _draw(mode, tmp_path, spec)
        saved, _ = _draw("saved", tmp_path, spec)
        assert len(figs) == 4
        assert _layers(figs) == _layers(saved)
        assert not _empty_reports(warns), warns

    def test_the_one_line_form_is_drawn(self, tmp_path, mode):
        """The one-line route writes a graph with no name, and a spec with
        no kpis."""
        spec = {"graphs": [_graph("", [_IMMEDIATE[0][0]])],
                "build_options": {"layout": "1 1", "theme": ""}}
        figs, warns = _draw(mode, tmp_path, spec)
        assert [k for k, _ in _layers(figs)] == ["Scatter"]
        assert not _empty_reports(warns), warns

    @pytest.mark.parametrize("where", ["graph", "plot"])
    @pytest.mark.parametrize("data,key,text", [
        ("none", "in_expr", "1/1"),
        ("none", "if_expr", "f == 2"),
        ("six", "in_expr", "1/1"),
        ("six", "if_expr", "f == 2"),
    ])
    def test_a_qualifier_is_ignored_as_twoway_ignores_it(
            self, tmp_path, mode, where, data, key, text):
        """twoway draws every point of ``scatteri 1 2 3 4 if foreign == 2``
        and of ``... in 1/1``; so does dash, and says nothing about it.
        With no data -- ``dash scatteri 1 2 if f == 2`` with nothing in
        memory exports no variable -- the saved page said a layer's own
        qualifier "could not be applied", and the served app that its
        ``if_expr`` filter was skipped."""
        plot = {"type": "scatteri", "values": [[1.0, 2.0], [3.0, 4.0]],
                "options": {}}
        g = _graph("a1", [dict(plot, **{key: text}) if where == "plot"
                          else plot])
        if where == "graph":
            g[key] = text
        figs, warns = _draw(mode, tmp_path, _spec([g]),
                            _DF if data == "six" else _EMPTY_DATA)
        assert _layers(figs) == [("Scatter", {"x": [2.0, 4.0],
                                              "y": [1.0, 3.0]})]
        assert not [w for w in warns if "qualifier" in w
                    or "drew nothing" in w], warns

    def test_the_csv_download_is_offered_on_it(self, tmp_path, mode):
        figs, warns = _draw(mode, tmp_path,
                            _spec([_graph("a1", [_IMMEDIATE[0][0]])],
                                  csv="1"))
        assert [k for k, _ in _layers(figs)] == ["Scatter"]


# ===========================================================================
# 2. An immediate layer with every point missing: drawn empty, in silence
# ===========================================================================

_ALL_MISSING = [
    {"type": "scatteri", "values": [[None, None], [None, 2.0]],
     "options": {}},
    {"type": "pci", "values": [[None, 0.0, 1.0, None]], "options": {}},
    {"type": "pcarrowi", "values": [[None, None, None, None, "A", 3]],
     "options": {}},
]


@pytest.mark.parametrize("mode", _MODES)
class TestAnImmediateLayerMissingEverywhereSaysNothing:
    @pytest.mark.parametrize("plot", _ALL_MISSING,
                             ids=[p["type"] for p in _ALL_MISSING])
    @pytest.mark.parametrize("data", ["none", "six"])
    def test_it_is_not_reported(self, tmp_path, mode, plot, data):
        """twoway draws nothing for it and says nothing.  It was reported
        against the observations of the data -- which an immediate layer
        does not draw from -- or, with none, against the placeholder."""
        g = _graph("a1", [plot, {"type": "scatter", "yvar": "y",
                                 "xvar": "x", "options": {}}]
                   if data == "six" else [plot])
        figs, warns = _draw(mode, tmp_path, _spec([g]),
                            _DF if data == "six" else _EMPTY_DATA)
        assert figs
        assert not _empty_reports(warns), warns

    @pytest.mark.parametrize("expr,rng", [
        ("1/0", ""), ("x/0", ""), ("10^400", ""),
        ("sqrt(x)", "-2 -1"), ("exp(1000*x)", "1 2")])
    def test_a_function_missing_everywhere_is_not_reported(
            self, tmp_path, mode, expr, rng):
        """Each is missing in Stata over its range: twoway draws nothing,
        in silence (measured, rc 0)."""
        opts = {"range": rng} if rng else {}
        g = _graph("a1", [{"type": "scatter", "yvar": "y", "xvar": "x",
                           "options": {}},
                          {"type": "function", "expr": expr,
                           "options": opts}])
        figs, warns = _draw(mode, tmp_path, _spec([g]), _DF)
        assert not _empty_reports(warns), warns
        (line,) = _one_line("Line", figs)
        ys = [_num(v) for v in line.data_source.data["y_fn"]]
        assert ys and all(v is None for v in ys), ys


# ===========================================================================
# 3. A function is drawn where it is defined, as twoway draws it
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestAFunctionIsDrawnWhereItIsDefined:
    @pytest.mark.parametrize("expr,want", [
        # twoway's own serset for range(-1 1) n(5): . . 0 .70710678 1
        ("sqrt(x)", [None, None, 0.0, math.sqrt(0.5), 1.0]),
        # log(0) is missing in Stata; numpy's -inf is not drawn either.
        ("log(x)", [None, None, None, math.log(0.5), 0.0]),
    ])
    def test_the_defined_part_is_drawn(self, tmp_path, mode, expr, want):
        g = _graph("a1", [{"type": "function", "expr": expr,
                           "options": {"range": "-1 1", "n": "5"}}])
        figs, warns = _draw(mode, tmp_path, _spec([g]))
        (line,) = _one_line("Line", figs)
        ys = [_num(v) for v in line.data_source.data["y_fn"]]
        assert [v is None for v in ys] == [w is None for w in want], ys
        assert [v for v in ys if v is not None] == pytest.approx(
            [w for w in want if w is not None])
        assert not _empty_reports(warns), warns

    def test_an_infinite_value_is_missing_as_in_stata(self, tmp_path, mode):
        """x/0 is missing in Stata; numpy's inf would reach the page."""
        g = _graph("a1", [{"type": "function", "expr": "1/(x-0.5)",
                           "options": {"range": "0 1", "n": "3"}}])
        figs, _ = _draw(mode, tmp_path, _spec([g]))
        (line,) = _one_line("Line", figs)
        ys = [_num(v) for v in line.data_source.data["y_fn"]]
        assert ys == [-2.0, None, 2.0]


@pytest.mark.parametrize("mode", _MODES)
class TestARejectedExpressionIsStillReported:
    @pytest.mark.parametrize("data", ["none", "six"])
    def test_with_data_or_none(self, tmp_path, mode, data):
        """dash refuses to evaluate it, and the layer is drawn empty.  With
        no data the report was lost: it was given only when the graph had
        observations, which a function does not draw from."""
        g = _graph("a1", [{"type": "function", "expr": "__import__('os')",
                           "options": {}}])
        _, warns = _draw(mode, tmp_path, _spec([g]),
                         _DF if data == "six" else _EMPTY_DATA)
        assert _empty_reports(warns) == [
            "dash: graph 'a1' plot 1 (function) drew nothing."], warns


# ===========================================================================
# 4. A graph with no name is not called '?'
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestALayerThatDrewNothingIsNamedByWhatItHas:
    def test_a_graph_with_no_name_is_named_by_its_place(self, tmp_path,
                                                         mode):
        spec = {"graphs": [_graph("", [{"type": "scatter", "yvar": "m",
                                        "xvar": "x", "options": {}}])],
                "build_options": {"layout": "1 1", "theme": ""}}
        _, warns = _draw(mode, tmp_path, spec, _DF)
        assert _empty_reports(warns) == [
            "dash: plot 1 (scatter) drew nothing from 6 observations."], \
            warns

    def test_a_named_graph_is_named(self, tmp_path, mode):
        g = _graph("g1", [{"type": "scatter", "yvar": "y", "xvar": "x",
                           "options": {}},
                          {"type": "line", "yvar": "m", "xvar": "x",
                           "options": {}}])
        _, warns = _draw(mode, tmp_path, _spec([g]), _DF)
        assert _empty_reports(warns) == [
            "dash: graph 'g1' plot 2 (line) drew nothing from 6 "
            "observations."], warns


class TestTheReportHelpers:
    """``_dash_note_empty_layer`` decides, ``_dash_report_empty_layer``
    words it; both modes call the first."""

    def _notes(self, *args):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_note_empty_layer(*args)
        return [str(w.message) for w in caught]

    def test_a_layer_that_drew_is_not_reported(self):
        src = dr.ColumnDataSource({"x": [1.0]})

        class _R:
            data_source = src
        assert self._notes("g1", 1, "scatter", 6, [_R()]) == []

    @pytest.mark.parametrize("ptype", ["scatteri", "pci", "pcarrowi",
                                       "SCATTERI"])
    def test_an_immediate_layer_is_never_reported(self, ptype):
        assert self._notes("g1", 1, ptype, 6, []) == []
        assert self._notes("g1", 1, ptype, 0, []) == []

    def test_a_function_is_reported_whatever_the_data(self):
        assert self._notes("g1", 2, "function", 0, []) == [
            "dash: graph 'g1' plot 2 (function) drew nothing."]
        assert self._notes("", 2, "function", 6, []) == [
            "dash: plot 2 (function) drew nothing."]

    def test_a_data_layer_is_reported_only_when_there_are_rows(self):
        assert self._notes("g1", 1, "scatter", 0, []) == []
        assert self._notes("g1", 1, "scatter", 1234, []) == [
            "dash: graph 'g1' plot 1 (scatter) drew nothing from 1,234 "
            "observations."]

    def test_the_words(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_report_empty_layer("g1", 3, "lpoly", 74)
            dr._dash_report_empty_layer("", 3, "lpoly", 74)
            dr._dash_report_empty_layer("g1", 3, "function")
        assert [str(w.message) for w in caught] == [
            "dash: graph 'g1' plot 3 (lpoly) drew nothing from 74 "
            "observations.",
            "dash: plot 3 (lpoly) drew nothing from 74 observations.",
            "dash: graph 'g1' plot 3 (function) drew nothing."]

    def test_a_name_is_shown_as_text(self):
        """A graph name is a registry name, but a spec is an input."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_report_empty_layer("{bf:x}'\n", 1, "scatter", 1)
        (msg,) = [str(w.message) for w in caught]
        assert msg.startswith("dash: graph ") and "\n" not in msg


# ===========================================================================
# 5. pci is drawn as twoway draws it: an immediate pcspike
# ===========================================================================

def _pair(kind):
    second = ({"type": "pci", "values": [[0.0, 0.0, 1.0, 1.0]],
               "options": {}} if kind == "pci" else
              {"type": "pcspike", "y1var": "y1", "x1var": "x1",
               "y2var": "y2", "x2var": "x2", "options": {}})
    return _graph("g1", [{"type": "scatteri", "values": [[5.0, 5.0]],
                          "options": {}}, second])


def _segment_style(figs):
    (seg,) = _one_line("Segment", figs)
    g = seg.glyph
    return (str(g.line_color).lower(), g.line_width, list(g.line_dash),
            g.line_alpha)


@pytest.mark.parametrize("mode", _MODES)
class TestPciIsDrawnAsPcspike:
    @pytest.mark.parametrize("scheme", ["s2color", "stcolor", "s1mono",
                                        "s2mono", "s2gmanual", "economist"])
    def test_in_pcspikes_colour_and_width(self, tmp_path, mode, scheme):
        pci, _ = _draw(mode, tmp_path, _spec([_pair("pci")], scheme=scheme),
                       _DF)
        spk, _ = _draw(mode, tmp_path,
                       _spec([_pair("pcspike")], scheme=scheme), _DF)
        assert _segment_style(pci) == _segment_style(spk)

    def test_s2mono_draws_the_second_plot_as_twoway_does(self, tmp_path,
                                                         mode):
        """Measured from twoway's SVG: pci as the second plot under s2mono
        is stroked #A0A0A0, pcspike's colour; a line there is #000000."""
        figs, _ = _draw(mode, tmp_path,
                        _spec([_pair("pci")], scheme="s2mono"), _DF)
        assert _segment_style(figs)[0] == "#a0a0a0"

    def test_it_has_a_legend_key_as_twoway_gives_it(self, tmp_path, mode):
        """``twoway (scatteri 5 5) (pci 0 0 1 1)`` draws a legend of two
        keys, as with pcspike; dash drew none."""
        figs, _ = _draw(mode, tmp_path, _spec([_pair("pci")]), _DF)
        labels = []
        for f in figs:
            for lg in f.select({"type": Legend}):
                for it in lg.items:
                    lab = it.label
                    labels.append(lab.get("value") if isinstance(lab, dict)
                                  else getattr(lab, "value", lab))
        assert labels == ["scatteri", "pci"]

    @pytest.mark.parametrize("opt", [{"lcolor": "maroon"},
                                     {"color": "maroon"}])
    def test_its_colour_options_style_it(self, tmp_path, mode, opt):
        g = _graph("g1", [{"type": "pci", "values": [[0.0, 0.0, 1.0, 1.0]],
                           "options": dict(opt)}])
        figs, _ = _draw(mode, tmp_path, _spec([g]))
        want = dr.GlyphMapper().tr.translate_mcolor("maroon").lower()
        assert _segment_style(figs)[0] == want
