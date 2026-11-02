"""The served dashboard must be the dashboard `dash build' would have saved.

WP-09 gave both renderers one glyph dispatch, which closed the four
divergences GAPS.md D2 lists by name -- `pci', `fpfitci' and the `pc*' family
with a repeated variable all draw the same models in both modes now, and this
file's first class pins that so the unification cannot be undone quietly.

What WP-09 did NOT close, measured on this branch before any of the fixes
below:

* `mlabel()' was drawn TWICE in server mode for line, connected, dot,
  dropline and tsline -- the mapper labels its own points now, and the
  generated app still ran the hand-written "common mlabel block" over the
  top -- and drawn at all for lpoly, lpolyci, fpfit, fpfitci and mband,
  where the saved dashboard draws none.  Two LabelSets at the same
  coordinates render as doubled, slightly bolder text.
* A per-plot `if'/`in' qualifier was not read in server mode at all.
  `dash (scatter mpg weight) (scatter mpg weight if foreign==1)' drew ten
  points in both layers when served and five in the second layer when saved.
* A KPI's own `if'/`in' was ignored when served: `_compute_kpi(df, ...)' was
  handed the whole frame.  That is a wrong number presented as a right one.
* Only five of the 38 plot types carried a hover tool when served, because
  the only hovers the served figure had were the ones `map_scatter' and
  `map_line' add for themselves.  `hover(foreign)' was ignored entirely.
* A layer that drew nothing said nothing when served.
* `layout(g1:0,0)' placed in the saved dashboard and was silently dropped
  when served; KPI `fmt(%12.0fc)' lost its comma grouping; the legend used
  the y-variable name for every computed layer where the saved dashboard
  says "Fitted values" or "95% CI", at 10pt rather than the scheme's 11pt;
  and an item not named in `tabs()' was drawn above the tabs under
  `layout(bs)' where `dash.sthlp' says below.

Each of those has a class below.  The comparison is always against the
standalone renderer running the SAME spec, because "what the saved dashboard
does" is the specification here.
"""
from __future__ import annotations

import itertools
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import HoverTool, Label, LabelSet, Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, load_app, memo_build

_SEQ = itertools.count()

_DF = pd.DataFrame({
    "mpg":     [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight":  [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
                2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price":   [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
                10372.0, 4082.0, 11385.0],
})

#: Every plot type dash accepts, with the spec shape `dash.ado' writes for it.
_RANGE = {"rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
          "rcapsym", "rscatter", "tsrline"}
_PC = {"pcspike", "pcarrow", "pcbarrow", "pcscatter", "pccapsym"}
#: WP-31 B1: the range-point types, y1 y2 y3 x.
_RANGEPT = {"rpcap", "rpspike"}

#: Derived from the dispatch tables, not written by hand: a plot type added
#: to the code is in every sweep here and in test_server_facets.py the same
#: day, and test_mode_parity.py cross-checks the same set against dash.ado.
ALL_TYPES = sorted(dr._dash_plot_type_names())


def plot_for(ptype, options=None, **extra):
    """The plot dict `dash.ado' emits for *ptype*, with *options* attached."""
    o = dict(options or {})
    if ptype in ("histogram", "kdensity"):
        p = {"type": ptype, "var": "mpg", "options": o}
    elif ptype in _RANGE:
        p = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
             "xvar": "weight", "options": o}
    elif ptype in _PC:
        p = {"type": ptype, "y1var": "mpg", "x1var": "weight",
             "y2var": "price", "x2var": "foreign", "options": o}
    elif ptype in _RANGEPT:
        p = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
             "yvar": "foreign", "xvar": "weight", "options": o}
    elif ptype in ("contour", "contourline"):
        # WP-31 B4b: z y x.
        p = {"type": ptype, "zvar": "price", "yvar": "mpg",
             "xvar": "weight", "options": o}
    elif ptype == "scatteri":
        p = {"type": ptype, "values": [[20.0, 3000.0], [30.0, 4000.0]],
             "options": o}
    elif ptype == "pci":
        # dash.ado writes `pci 20 3000 30 4000' as one record per segment,
        # y1 x1 y2 x2, as it writes pcarrowi's arrows.
        p = {"type": ptype, "values": [[20.0, 3000.0, 30.0, 4000.0]],
             "options": o}
    elif ptype == "pcarrowi":
        # dash.ado writes `pcarrowi 20 3000 30 4000 25 2000 22 3500' as one
        # record per arrow, in twoway's order: y1 x1 y2 x2.
        p = {"type": ptype, "values": [[20.0, 3000.0, 30.0, 4000.0],
                                       [25.0, 2000.0, 22.0, 3500.0]],
             "options": o}
    elif ptype == "function":
        p = {"type": ptype, "expr": "x^2", "options": o}
    else:
        p = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": o}
    p.update(extra)
    return p


def make_spec(plots, build_options=None, graph_options=None, kpis=None):
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    bo.update(build_options or {})
    if kpis and "registry" not in (build_options or {}):
        # Graphs and KPI cards share one registry, and only a registered
        # name is placed in the layout -- an unregistered KPI is built and
        # then dropped, which looks exactly like a KPI that was not built.
        bo["registry"] = " ".join(
            ["g1"] + [k.get("name", "") for k in kpis if k.get("name")])
    go = {"name": "g1"}
    go.update(graph_options or {})
    return {"graphs": [{"name": "g1", "graph_options": go,
                        "options": dict(graph_options or {}),
                        "plots": plots}],
            "kpis": list(kpis or []), "build_options": bo}


def _write(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"spec_{tag}.json"
    dp = tmp_path / f"data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return tag, str(sp), str(dp)


def standalone(tmp_path, spec):
    """(figures, html, warnings) from the saved-dashboard renderer."""
    _, sp, dp = _write(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        html = r.render()
    return list(r.figures.values()), html, [str(w.message) for w in caught]


def served(tmp_path, spec):
    """(figures, document, warnings) from the generated server app.

    The import is deliberately OUTSIDE the warning capture.  A generated app
    calls ``make_document(curdoc())`` at import time, because that is what
    ``bokeh serve`` runs; importing it here and then calling
    ``make_document`` again builds the document twice, and every warning the
    build emits would be counted twice with it.
    """
    tag, sp, dp = _write(tmp_path, spec)
    ap = tmp_path / f"app_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
        mod = load_app(str(ap), f"_wp10_{tag}", draw=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return _figures_of(doc), doc, [str(w.message) for w in caught]


_ONCE_DIR = None


def _once_dir():
    global _ONCE_DIR
    if _ONCE_DIR is None:
        import tempfile
        _ONCE_DIR = __import__("pathlib").Path(tempfile.mkdtemp(prefix="sld_once_"))
    return _ONCE_DIR


@memo_build()
def _standalone_once(spec):
    """``standalone`` kept per spec, for the per-type checks that only read
    it (02nov2026: four classes built every type's page again)."""
    return standalone(_once_dir(), spec)


@memo_build()
def _served_once(spec):
    """``served`` kept per spec, as ``_standalone_once``."""
    return served(_once_dir(), spec)


#: The per-type checks that read _standalone_once/_served_once share one
#: worker per plot type, so each type is built once.
_ONCE_TESTS = frozenset(['test_no_figure_carries_two_identical_hovers', 'test_no_type_is_reported_empty_in_only_one_mode', 'test_the_same_keys_at_the_same_size', 'test_the_same_tooltips_in_both_modes'])


def xdist_group_of(item):
    if item.name.split("[")[0] in _ONCE_TESTS:
        return "sld:" + str(item.callspec.params.get("ptype"))
    return None


def _walk(doc):
    seen, out = set(), []

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


def _figures_of(doc):
    return [m for m in _walk(doc) if type(m).__name__ == "figure"]


# ---------------------------------------------------------------------------
# Comparable profiles
# ---------------------------------------------------------------------------

def glyph_names(figs):
    if not figs:
        return []
    return [type(r.glyph).__name__ for r in figs[0].renderers
            if getattr(r, "glyph", None) is not None]


def label_texts(figs):
    if not figs:
        return []
    f = figs[0]
    return sorted(
        r.text for r in
        list(f.center) + list(f.above) + list(f.below) + list(f.left) +
        list(f.right)
        if isinstance(r, LabelSet)
    )


def tooltips(figs):
    if not figs:
        return []
    return sorted(
        json.dumps(list(t.tooltips), default=str)
        for t in figs[0].tools if isinstance(t, HoverTool) and t.tooltips
    )


def legends(figs):
    if not figs:
        return []
    f = figs[0]
    out = []
    for lg in list(f.center) + list(f.above) + list(f.below) + list(f.right):
        if isinstance(lg, Legend):
            out.append(([_label_of(i) for i in lg.items],
                        lg.label_text_font_size))
    return out


def _label_of(item):
    lab = item.label
    if isinstance(lab, dict):
        return lab.get("value", lab)
    return getattr(lab, "value", str(lab))


def drawn_rows(figs):
    """Rows each renderer actually draws, honouring any CDSView filter."""
    if not figs:
        return []
    out = []
    for r in figs[0].renderers:
        src = getattr(r, "data_source", None)
        if src is None:
            continue
        data = dict(src.data)
        first = next(iter(data), None)
        n = len(data[first]) if first else 0
        view = getattr(r, "view", None)
        filt = getattr(view, "filter", None) if view is not None else None
        idx = getattr(filt, "indices", None) if filt is not None else None
        if idx is None and filt is not None:
            bools = getattr(filt, "booleans", None)
            if bools is not None:
                idx = [i for i, b in enumerate(bools) if b]
        out.append((type(getattr(r, "glyph", None)).__name__,
                    len(idx) if idx is not None else n))
    return out


def _kpi_value_in(text, kname):
    """The number a KPI card shows, read out of either mode's markup.

    The saved dashboard embeds its cards inside Bokeh's JSON payload, where
    the angle brackets are HTML-escaped and the quotes are backslashed; the
    served app holds the same markup raw on a ``Div``.  One reader, so the
    two are compared on the same thing.
    """
    if not isinstance(text, str):
        return None
    marker = "kpi_val_%s" % kname
    at = text.find(marker)
    if at < 0:
        return None
    rest = text[at + len(marker):]
    rest = rest.replace("&gt;", ">").replace("&lt;", "<")
    open_at = rest.find(">")
    if open_at < 0:
        return None
    close_at = rest.find("<", open_at)
    if close_at < 0:
        return None
    return rest[open_at + 1:close_at].strip()


def kpi_text_standalone(tmp_path, spec, kname):
    _, html, _ = standalone(tmp_path, spec)
    return _kpi_value_in(html, kname)


def kpi_text_served(tmp_path, spec, kname):
    _, doc, _ = served(tmp_path, spec)
    for m in _walk(doc):
        got = _kpi_value_in(getattr(m, "text", None), kname)
        if got is not None:
            return got
    return None


# ===========================================================================
# The D2 divergences WP-09 closed, pinned so they cannot reopen
# ===========================================================================

class TestTheUnificationKeepsD2Closed:
    """`pci', `fpfitci' and the `pc*' family drew different models per mode.

    All three were hand-written branches in the generated app: `pci' read
    `y1var/x1var/y2var/x2var' from a spec that carries a `values' array, so
    its gate was never true and the layer drew nothing at all; `fpfitci' was
    a verbatim copy of the `fpfit' branch and drew no confidence band; and
    the `pc*' branches built their column list without de-duplicating, so
    `pcspike mpg weight mpg price' raised ``Expected unique column names''.

    They are closed because every type dispatches through `GlyphMapper' now.
    The point of this class is that the NEXT hand-written branch fails here.
    """

    def test_pci_draws_the_same_segments(self, tmp_path):
        spec = make_spec([plot_for("pci")])
        assert glyph_names(standalone(tmp_path, spec)[0]) == \
               glyph_names(served(tmp_path, spec)[0]) == ["Segment"]

    def test_fpfitci_draws_its_band_in_both_modes(self, tmp_path):
        spec = make_spec([plot_for("fpfitci")])
        std = glyph_names(standalone(tmp_path, spec)[0])
        srv = glyph_names(served(tmp_path, spec)[0])
        assert std == srv
        assert "VArea" in srv, (
            "the served fpfitci drew no confidence band: %r" % srv)

    @pytest.mark.parametrize("ptype", sorted(_PC))
    @pytest.mark.parametrize("repeat", ["y", "x", "none"])
    def test_a_pc_plot_with_a_repeated_variable_agrees(self, tmp_path,
                                                       ptype, repeat):
        p = plot_for(ptype)
        if repeat == "y":
            p["y2var"] = p["y1var"]
        elif repeat == "x":
            p["x2var"] = p["x1var"]
        spec = make_spec([p])
        std = glyph_names(standalone(tmp_path, spec)[0])
        srv = glyph_names(served(tmp_path, spec)[0])
        assert std == srv and srv, (
            "%s with a repeated %s variable: standalone %r, served %r"
            % (ptype, repeat, std, srv)
        )


# ===========================================================================
# mlabel()
# ===========================================================================

class TestMlabelIsDrawnExactlyAsTheSavedDashboardDrawsIt:
    """One LabelSet per labelled layer, and none on a type that has no labels.

    Before WP-10 the generated app ran a hand-written "common mlabel block"
    after the dispatch, on top of the LabelSet the mapper had already added.
    Measured on this data:

        line        saved ['foreign']  served ['foreign', 'foreign']
        connected   saved ['foreign']  served ['foreign', 'foreign']
        dot         saved ['foreign']  served ['foreign', 'foreign']
        dropline    saved ['foreign']  served ['foreign', 'foreign']
        tsline      saved ['foreign']  served ['foreign', 'foreign']
        lpoly       saved []           served ['foreign']
        lpolyci     saved []           served ['foreign']
        fpfit       saved []           served ['foreign']
        fpfitci     saved []           served ['foreign']
        mband       saved []           served ['foreign']

    Two LabelSets at the same coordinates are not invisible -- the text is
    drawn twice, which reads as a bolder, slightly smeared label.
    """

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_the_same_labels_in_both_modes(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype, {"mlabel": "foreign"})])
        std = label_texts(standalone(tmp_path, spec)[0])
        srv = label_texts(served(tmp_path, spec)[0])
        assert std == srv, (
            "%s with mlabel(foreign): saved dashboard draws %r, served "
            "dashboard draws %r" % (ptype, std, srv)
        )

    # line, tsline and spike were listed here too; twoway draws no marker
    # label on them (measured 23sep2026; test_marker_label_parity.py), so
    # they now draw none in either mode, which the parity test above holds.
    @pytest.mark.parametrize("ptype", ["connected", "dot", "dropline",
                                       "scatter", "bar", "pccapsym",
                                       "pcscatter", "pcarrow", "pcbarrow"])
    def test_a_labelled_layer_is_labelled_once(self, tmp_path, ptype):
        """The specific shape of the defect: one layer, two LabelSets.

        Counted as LabelSets rather than by the column they draw: rscatter
        and pcscatter keep their labels under a column of their own."""
        spec = make_spec([plot_for(ptype, {"mlabel": "foreign"})])
        srv = label_texts(served(tmp_path, spec)[0])
        assert len(srv) == 1, (
            "%s drew %d marker-label sets for one layer" % (ptype, len(srv))
        )

    def test_the_generated_app_has_no_second_mlabel_implementation(self):
        """Source guard: the block is gone, not merely unreachable."""
        src = _builder_source()
        assert "Common mlabel block" not in src, (
            "the generated app still carries its own mlabel implementation; "
            "GlyphMapper is the only one that may draw marker labels"
        )


def _builder_source():
    import inspect
    return inspect.getsource(dr.ServerAppBuilder)


# ===========================================================================
# A layer that drew nothing
# ===========================================================================

class TestALayerThatDrewNothingSaysSoInBothModes:
    """GAPS.md D6.  This is what made every D2 divergence silent.

    The saved dashboard has warned since WP-02.  The served one had no
    equivalent, so a layer that produced a titled, axed, empty plot region
    returned rc 0 and said nothing at all.  Both modes now call the same
    ``_dash_report_empty_layer``, so the text cannot drift either.
    """

    def test_a_rejected_function_expression_is_reported(self, tmp_path):
        spec = make_spec([plot_for("function")])
        spec["graphs"][0]["plots"][0]["expr"] = "__import__('os')"
        std = [w for w in standalone(tmp_path, spec)[2] if "drew nothing" in w]
        srv = [w for w in served(tmp_path, spec)[2] if "drew nothing" in w]
        assert srv, "the served app drew an empty function layer in silence"
        assert std == srv, (
            "the two modes word the empty-layer report differently:\n"
            "  saved  %r\n  served %r" % (std, srv)
        )

    def test_the_report_names_the_layer_that_failed(self, tmp_path):
        spec = make_spec([plot_for("scatter"), plot_for("function")])
        spec["graphs"][0]["plots"][1]["expr"] = "open('/tmp/nope')"
        srv = [w for w in served(tmp_path, spec)[2] if "drew nothing" in w]
        assert len(srv) == 1 and "plot 2" in srv[0] and "function" in srv[0], (
            "expected one report naming plot 2 (function), got %r" % (srv,)
        )

    def test_a_layer_that_drew_is_not_reported(self, tmp_path):
        spec = make_spec([plot_for("scatter")])
        assert not [w for w in served(tmp_path, spec)[2]
                    if "drew nothing" in w]

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_no_type_is_reported_empty_in_only_one_mode(self, tmp_path,
                                                        ptype):
        """The sweep: a type that draws when saved must draw when served."""
        spec = make_spec([plot_for(ptype)])
        std = [w for w in _standalone_once(spec)[2] if "drew nothing" in w]
        srv = [w for w in _served_once(spec)[2] if "drew nothing" in w]
        assert std == srv, (
            "%s: saved reports %r, served reports %r" % (ptype, std, srv))


# ===========================================================================
# Qualifiers
# ===========================================================================

class TestAPerPlotQualifierIsRead:
    """GAPS.md D3.  ``plot.get('if_expr')`` appeared nowhere in the served app.

    ``dash.ado`` promotes the FIRST segment's qualifier to the graph level and
    leaves every segment carrying its own, because the saved renderer applies
    them per layer.  The served app read only the graph-level one, so a
    second segment's ``if`` was discarded -- it drew all ten observations
    where the saved dashboard drew five, with no warning and no visible
    difference except the wrong answer.
    """

    def test_a_plot_level_if_selects_rows(self, tmp_path):
        spec = make_spec([plot_for("scatter", if_expr="foreign==1")])
        assert drawn_rows(served(tmp_path, spec)[0]) == \
               drawn_rows(standalone(tmp_path, spec)[0]) == [("Scatter", 5)]

    def test_a_plot_level_in_selects_rows(self, tmp_path):
        spec = make_spec([plot_for("scatter", in_expr="1/3")])
        assert drawn_rows(served(tmp_path, spec)[0]) == \
               drawn_rows(standalone(tmp_path, spec)[0]) == [("Scatter", 3)]

    def test_a_second_layers_qualifier_is_not_lost(self, tmp_path):
        """The shape `dash.ado' actually produces: layer 1 bare, layer 2 if."""
        spec = make_spec([plot_for("scatter"),
                          plot_for("scatter", if_expr="foreign==1")])
        std = drawn_rows(standalone(tmp_path, spec)[0])
        srv = drawn_rows(served(tmp_path, spec)[0])
        assert std == srv, "saved %r, served %r" % (std, srv)
        assert srv == [("Scatter", 10), ("Scatter", 5)]

    @pytest.mark.parametrize("ptype", ["line", "bar", "spike", "area",
                                       "connected", "dropline", "dot"])
    def test_the_qualifier_reaches_every_ordinary_type(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype, if_expr="foreign==1")])
        std = drawn_rows(standalone(tmp_path, spec)[0])
        srv = drawn_rows(served(tmp_path, spec)[0])
        assert std == srv, "%s: saved %r, served %r" % (ptype, std, srv)
        # One renderer per layer (connected and dropline draw two: the line
        # or stem and the markers), each over the five foreign cars
        # (measured 24sep2026).  all() alone passed a layer that drew no
        # renderer in either mode.
        layers = {"connected": 2, "dropline": 2}.get(ptype, 1)
        if ptype == "area":
            # Flipped (WP-34 PIC-1): the outline is the area's whole
            # polygon, one ring rebuilt from the fill's source (A-6) --
            # 5 tops, 5 bases and the closing vertex -- and its key swatch
            # (one row), after the fill.
            assert [n for _, n in srv[1:]] == [11, 1], srv
            srv = srv[:1]
        if ptype == "dot":
            # Its rows of dots come first (WP-31 B5b), 76 for each of the
            # five cars over the scale 10..40 at 75 dots (base 10: one dot
            # to the scale's foot, 75 to its top), then the five markers.
            assert srv[0] == ("Scatter", 5 * 76), srv
            srv = srv[1:]
        assert [n for _, n in srv] == [5] * layers, (
            "%s drew %r rows under `if foreign==1'; five observations "
            "satisfy it" % (ptype, srv)
        )

    def test_a_range_layers_qualifier_is_read(self, tmp_path):
        spec = make_spec([plot_for("rspike", if_expr="foreign==1")])
        std = drawn_rows(standalone(tmp_path, spec)[0])
        srv = drawn_rows(served(tmp_path, spec)[0])
        assert std == srv and srv and all(n == 5 for _, n in srv), (
            "saved %r, served %r" % (std, srv))

    def test_an_injection_in_a_plot_qualifier_does_not_execute(self, tmp_path):
        """The qualifier is an expression the app evaluates; it is whitelisted.

        The served app validates a graph-level qualifier against an AST
        whitelist before handing it to ``query``.  A per-plot qualifier must
        go through the SAME gate, or reading them has opened a hole rather
        than closed a divergence.
        """
        marker = tmp_path / "PWN_QUAL.txt"
        evil = ("foreign == __import__('os').system('touch %s')"
                % str(marker))
        spec = make_spec([plot_for("scatter", if_expr=evil)])
        # This sat in `except Exception: pass', so an app that crashed --
        # before or after reaching the qualifier -- passed.  Nothing raises
        # (measured 24sep2026): the whitelist refuses the qualifier aloud and
        # the layer keeps every row, the contract of _dash_qualified_frame.
        figs, _doc, msgs = served(tmp_path, spec)
        assert not marker.exists(), (
            "a per-plot if() expression executed arbitrary Python")
        assert ("dash: graph 'g1' plot 1 if_expr filter skipped -- invalid "
                "syntax (<unknown>, line 1)") in msgs, msgs
        assert drawn_rows(figs) == [("Scatter", len(_DF))]
        # The gate's own verdict, beside a qualifier it must accept: with
        # the whitelist accepting everything pandas still refuses this
        # payload, so no marker appears either way (measured 24sep2026).
        cols = list(_DF.columns)
        assert dr._validate_if_expr(
            dr._stata_if_to_pandas("foreign==1"), cols) is True
        assert dr._validate_if_expr(dr._stata_if_to_pandas(evil), cols) is False


class TestAKpiQualifierIsApplied:
    """A KPI carrying its own ``if``/``in`` must show the conditional value.

    ``_compute_kpi(df, stat, var)`` was handed the whole frame, so
    ``dash kpi mean(mpg) if foreign==1`` served 21.5 where the saved
    dashboard -- and Stata's own ``summarize`` -- report the mean over the
    five foreign cars.  A wrong number presented as a right one is worse
    than a missing card.
    """

    @staticmethod
    def _kpi(**over):
        k = {"name": "k1", "stat": "mean", "var": "mpg", "label": "M",
             "title": "M", "subtitle": "", "fmt": "", "color": "",
             "bgcolor": "", "update": "", "value": "", "display": ""}
        k.update(over)
        return k

    def test_an_unqualified_kpi_agrees(self, tmp_path):
        spec = make_spec([plot_for("scatter")], kpis=[self._kpi()])
        assert kpi_text_served(tmp_path, spec, "k1") == \
               kpi_text_standalone(tmp_path, spec, "k1")

    def test_a_kpi_if_is_honoured(self, tmp_path):
        spec = make_spec([plot_for("scatter")],
                         kpis=[self._kpi(if_expr="foreign==1")])
        want = _DF.loc[_DF["foreign"] == 1, "mpg"].mean()
        served_text = kpi_text_served(tmp_path, spec, "k1")
        assert served_text == kpi_text_standalone(tmp_path, spec, "k1")
        # The card shows four decimals, so the tolerance is the card's,
        # not the float's.
        assert abs(float(served_text.replace(",", "")) - want) < 1e-3, (
            "served KPI shows %r; mean(mpg) if foreign==1 is %r"
            % (served_text, want)
        )

    def test_a_kpi_in_is_honoured(self, tmp_path):
        spec = make_spec([plot_for("scatter")],
                         kpis=[self._kpi(in_expr="1/3")])
        want = _DF["mpg"].iloc[:3].mean()
        served_text = kpi_text_served(tmp_path, spec, "k1")
        assert served_text == kpi_text_standalone(tmp_path, spec, "k1")
        assert abs(float(served_text.replace(",", "")) - want) < 1e-3

    def test_a_kpi_qualifier_cannot_execute(self, tmp_path):
        marker = tmp_path / "PWN_KPI.txt"
        evil = "foreign == __import__('os').system('touch %s')" % str(marker)
        spec = make_spec([plot_for("scatter")],
                         kpis=[self._kpi(if_expr=evil)])
        # Refused aloud, measured 24sep2026, and the card is still built;
        # this used to sit in `except Exception: pass'.
        _figs, doc, msgs = served(tmp_path, spec)
        assert not marker.exists()
        assert ("dash: kpi 'k1' if_expr filter skipped -- invalid syntax "
                "(<unknown>, line 1)") in msgs, msgs
        assert any(_kpi_value_in(getattr(m, "text", None), "k1") is not None
                   for m in _walk(doc)), "the KPI card was not built"


# ===========================================================================
# Hover
# ===========================================================================

class TestEveryFigureCarriesTheSameHover:
    """GAPS.md D2.  ``HoverTool`` was imported into the app and never used.

    Measured before the fix, with a bare plot of each type:

        bar, histogram, area, dropline, lfit, qfit, rarea, rbar, rspike,
        rcap, rline, rscatter, tsrline     saved 1 tooltip, served NONE
        scatter, line, dot, tsline         saved 2 (!), served 1
        hover(foreign)                     saved 3 rows, served 2

    The saved dashboard's own defect is in that list: it built a
    comprehensive tool and cleared the mappers' per-layer ones only when
    ``hover()`` was given, so a plain scatter carried TWO HoverTools with
    identical tooltips.  One builder now serves both modes, and it clears
    first.
    """

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_the_same_tooltips_in_both_modes(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype)])
        std = tooltips(_standalone_once(spec)[0])
        srv = tooltips(_served_once(spec)[0])
        assert std == srv, (
            "%s: saved tooltips\n  %s\nserved tooltips\n  %s"
            % (ptype, std, srv)
        )

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_hover_adds_its_variable_in_both_modes(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype)], None, {"hover": "foreign"})
        std = tooltips(standalone(tmp_path, spec)[0])
        srv = tooltips(served(tmp_path, spec)[0])
        assert std == srv, (
            "%s with hover(foreign): saved\n  %s\nserved\n  %s"
            % (ptype, std, srv)
        )

    @pytest.mark.parametrize("ptype", ["scatter", "bar", "spike", "dot",
                                       "dropline", "connected", "rspike",
                                       "rcap", "rbar"])
    def test_hover_reaches_the_served_tooltip(self, tmp_path, ptype):
        """AC-10.2, stated positively rather than as a comparison."""
        spec = make_spec([plot_for(ptype)], None, {"hover": "foreign"})
        srv = tooltips(served(tmp_path, spec)[0])
        assert any("foreign" in t for t in srv), (
            "%s: hover(foreign) did not reach the served tooltip: %s"
            % (ptype, srv)
        )

    @pytest.mark.parametrize("ptype", ["bar", "histogram", "area"])
    def test_the_types_ac_10_3_names_have_a_tooltip(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype)])
        assert tooltips(served(tmp_path, spec)[0]), (
            "%s has no hover tool in server mode" % ptype)

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_no_figure_carries_two_identical_hovers(self, tmp_path, ptype):
        """The saved renderer's own half of the defect."""
        spec = make_spec([plot_for(ptype)])
        for mode, figs in (("saved", _standalone_once(spec)[0]),
                           ("served", _served_once(spec)[0])):
            got = tooltips(figs)
            assert len(got) == len(set(got)), (
                "%s %s: the figure carries the same tooltip twice: %s"
                % (ptype, mode, got)
            )

    def test_an_extra_hover_column_does_not_change_which_rows_are_drawn(
            self, tmp_path):
        """hover() names a column to SHOW, not a column to require.

        The served layer source carries the hover columns so the tooltip can
        read them.  Dropping NaN over them as well would silently delete
        every observation whose hover variable is missing.
        """
        df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 3.0],
                           "extra": [1.0, float("nan"), 3.0]})
        tag = next(_SEQ)
        sp = tmp_path / f"hs_{tag}.json"
        dp = tmp_path / f"hd_{tag}.json"
        spec = make_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                           "options": {}}], None, {"hover": "extra"})
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(df)))
        ap = tmp_path / f"ha_{tag}.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_hv_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
        assert drawn_rows(_figures_of(doc)) == [("Scatter", 3)], (
            "hover(extra) deleted the row whose `extra' is missing")


# ===========================================================================
# The smaller divergences (GAPS.md D7)
# ===========================================================================

class TestTheLegendSaysTheSameThing:
    """The served legend named every layer after the y variable.

    Stata keys a computed layer "Fitted values" and a confidence band
    "<level>% CI"; the saved dashboard has done so since WP-02.  The served
    app wrote ``var_labels.get(yvar) or yvar`` for all 38 types, so a served
    ``lfitci`` was keyed "mpg" twice over and there was no way to tell the
    band from the line.  It also styled the keys with the scheme's TICK
    label size rather than its text size -- 10pt against 11pt, and those two
    differ for 13 of the 14 shipped schemes.
    """

    @pytest.mark.parametrize("ptype", ALL_TYPES)
    def test_the_same_keys_at_the_same_size(self, tmp_path, ptype):
        spec = make_spec([plot_for(ptype)])
        std = legends(_standalone_once(spec)[0])
        srv = legends(_served_once(spec)[0])
        assert std == srv, "%s: saved %r, served %r" % (ptype, std, srv)

    @pytest.mark.parametrize("ptype", ["lfitci", "qfitci", "lpolyci",
                                       "fpfitci"])
    def test_a_band_and_its_line_are_keyed_separately(self, tmp_path, ptype):
        """Flipped (WP-30 P1.16): "Fitted values" for every line was wrong
        because twoway keys an lpolyci line "lpoly smooth: <y>" and an
        fpfitci line "Predicted <y>" (series_label_truth.json F22, F20)."""
        line = {"lpolyci": "lpoly smooth: mpg",
                "fpfitci": "Predicted mpg"}.get(ptype, "Fitted values")
        spec = make_spec([plot_for(ptype)])
        srv = legends(served(tmp_path, spec)[0])
        assert srv and srv[0][0] == ["95% CI", line], (
            "%s served legend keys %r" % (ptype, srv))

    def test_the_level_reaches_the_bands_key(self, tmp_path):
        spec = make_spec([plot_for("lfitci", {"level": "90"})],
                         {"level": "90"})
        std = legends(standalone(tmp_path, spec)[0])
        srv = legends(served(tmp_path, spec)[0])
        assert std == srv and srv[0][0][0] == "90% CI", (
            "saved %r, served %r" % (std, srv))

    def test_a_scheme_changes_the_key_size_in_both_modes(self, tmp_path):
        spec = make_spec([plot_for("scatter"), plot_for("lfit")],
                         {"scheme": "economist"})
        std = legends(standalone(tmp_path, spec)[0])
        srv = legends(served(tmp_path, spec)[0])
        assert std == srv, "saved %r, served %r" % (std, srv)


class TestLayoutPlacementMeansOneThing:
    """``layout(g1:0,0)`` placed when saved and was discarded when served.

    The saved renderer accepts both the 1-based form ``dash.sthlp``
    documents and the 0-based form ``dash.ado``'s regex admits, and
    normalises them.  The generated app had a second parser that required
    every index to be at least 1 and dropped the rest without a word.
    """

    @pytest.mark.parametrize("spec_str,want", [
        ("g1:1,1 g2:1,2", {"g1": (0, 0), "g2": (0, 1)}),
        ("g1:0,0 g2:0,1", {"g1": (0, 0), "g2": (0, 1)}),
        ("g1:2,1", {"g1": (1, 0)}),
        ("auto", {}),
        ("2 3", {}),
        ("", {}),
    ])
    def test_the_parser_reads_both_forms(self, spec_str, want):
        assert dr._dash_placement_map(spec_str) == want

    def test_an_unknown_name_is_not_placed(self):
        assert dr._dash_placement_map("g1:1,1 nope:1,2", {"g1"}) == \
               {"g1": (0, 0)}

    def test_the_generated_app_has_no_second_parser(self):
        src = _builder_source()
        assert "_dash_placement_map(spec_str" in src, (
            "the generated app does not use the shared placement parser")
        assert "r_i >= 1 and c_i >= 1" not in src, (
            "the generated app still carries its own 1-based-only parser")


class TestTheKpiCardIsFormattedTheSameWay:
    """``fmt(%12.0fc)`` was identical to ``fmt(%12.0f)`` when served.

    The generated app's ``_format_kpi`` matched ``%[w].[d][fge]``, ALWAYS
    comma-grouped an ``f``, ignored the ``c`` suffix that asks for grouping,
    had no ``%9.0g`` default and fell back to ``round(value, 4)``.
    """

    @staticmethod
    def _kpi(**over):
        k = {"name": "k1", "stat": "sum", "var": "weight", "title": "W",
             "subtitle": "", "fmt": "", "color": "", "bgcolor": "",
             "update": "", "value": "", "display": ""}
        k.update(over)
        return k

    @pytest.mark.parametrize("fmt", ["%12.0fc", "%12.0f", "%9.2f", "%9.0g",
                                     "%12.1fc", ""])
    def test_a_format_reads_the_same_in_both_modes(self, tmp_path, fmt):
        spec = make_spec([plot_for("scatter")], kpis=[self._kpi(fmt=fmt)])
        std = kpi_text_standalone(tmp_path, spec, "k1")
        srv = kpi_text_served(tmp_path, spec, "k1")
        assert std == srv, "fmt(%s): saved %r, served %r" % (fmt, std, srv)

    def test_the_c_suffix_groups_and_the_plain_form_does_not(self, tmp_path):
        """The two must not be the same string, or `c' means nothing."""
        grouped = kpi_text_served(
            tmp_path, make_spec([plot_for("scatter")],
                                kpis=[self._kpi(fmt="%12.0fc")]), "k1")
        plain = kpi_text_served(
            tmp_path, make_spec([plot_for("scatter")],
                                kpis=[self._kpi(fmt="%12.0f")]), "k1")
        assert "," in grouped and "," not in plain, (
            "fmt(%%12.0fc) served %r and fmt(%%12.0f) served %r"
            % (grouped, plain)
        )

    def test_a_variables_own_display_format_is_used(self, tmp_path):
        spec = make_spec([plot_for("scatter")],
                         {"formats": {"weight": "%12.0fc"}},
                         kpis=[self._kpi(fmt="")])
        std = kpi_text_standalone(tmp_path, spec, "k1")
        srv = kpi_text_served(tmp_path, spec, "k1")
        assert std == srv and "," in srv, (
            "the variable's own %%12.0fc was not applied: saved %r, served %r"
            % (std, srv))


class TestTabsAreWhereTheHelpSaysTheyAre:
    """``dash.sthlp``: an item ``tabs()`` does not name is drawn BELOW them.

    True of the plain grid and of server mode, and false under
    ``layout(bs)``, which drew the unassigned items above the tabs.
    """

    def _bs_spec(self):
        spec = make_spec(
            [plot_for("scatter")],
            {"layout": "bs", "tabs": "One: g1", "registry": "g1 g2"})
        spec["graphs"].append({
            "name": "g2", "graph_options": {"name": "g2"}, "options": {},
            "plots": [plot_for("line")]})
        return spec

    def test_the_unassigned_item_is_below_the_tabs(self, tmp_path):
        # This compared html.find("db-section") with html.find("db-grid").
        # No page carries "db-grid" (the renderer emits it nowhere), so the
        # ordering assert under `if grid_at >= 0' never ran, and the first
        # "db-section" is the stylesheet's `.db-section{margin-bottom:16px}'
        # rule, found on every page (measured 24sep2026).  The page BODY is
        # read instead: the tabs cell -- the one wrapper the renderer writes
        # only for the tab strip -- and g2's own root div, by its model id.
        _, sp, dp = _write(tmp_path, self._bs_spec())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            html = r.render()
        body = html[html.index('<div class="db-container">'):]
        tabs_cell = '<div class="db-row db-section"><div class="db-col-md-12">'
        g1_root = 'data-root-id="%s"' % r.figures["g1"].id
        g2_root = 'data-root-id="%s"' % r.figures["g2"].id
        assert body.count(tabs_cell) == 1, "no tabs section was rendered"
        assert body.count(g2_root) == 1, "the unassigned g2 was not placed"
        assert g1_root not in body, "the tabbed g1 was also placed outside"
        assert body.index(tabs_cell) < body.index(g2_root), (
            "under layout(bs) the unassigned items are drawn ABOVE the "
            "tabs; dash.sthlp says below"
        )


# ===========================================================================
# The shared helpers, on their own
# ===========================================================================
#
# Every fix above is one implementation that BOTH renderers run.  The classes
# above prove the two modes agree; these prove the helper is right, so a
# failure says which helper rather than which plot type.

class TestTheQualifierReader:
    """``_dash_qualified_frame``: rows in, rows out, and never a crash."""

    @staticmethod
    def _df():
        return pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0],
                             "b": [0.0, 1.0, 0.0, 1.0]})

    def test_no_qualifier_returns_every_row(self):
        assert len(dr._dash_qualified_frame(self._df(), "", "")) == 4

    def test_no_qualifier_copies_by_default(self):
        df = self._df()
        assert dr._dash_qualified_frame(df, "", "") is not df

    def test_no_qualifier_can_skip_the_copy(self):
        df = self._df()
        assert dr._dash_qualified_frame(df, "", "", copy=False) is df

    def test_an_if_selects_rows(self):
        assert len(dr._dash_qualified_frame(self._df(), "b==1", "")) == 2

    def test_an_in_is_one_based_and_inclusive(self):
        got = dr._dash_qualified_frame(self._df(), "", "2/3")
        assert list(got["a"]) == [2.0, 3.0]

    def test_both_compose(self):
        got = dr._dash_qualified_frame(self._df(), "b==1", "1/2")
        assert list(got["a"]) == [2.0]

    def test_statas_not_equal_is_accepted(self):
        """`~=' is Stata's spelling; only the server used to translate it."""
        assert len(dr._dash_qualified_frame(self._df(), "b ~= 1", "")) == 2

    @pytest.mark.parametrize("expr", [
        "__import__('os').system('true')",
        "@evil",
        "a.__class__",
        "[c for c in ().__class__.__bases__]",
        "b == open('/tmp/x')",
    ])
    def test_an_unsafe_expression_warns_and_filters_nothing(self, expr):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_qualified_frame(self._df(), expr, "")
        assert len(got) == 4, "%r was executed" % expr
        assert any("filter skipped" in str(w.message) for w in caught), (
            "%r was rejected in silence" % expr)

    def test_a_column_that_is_not_there_warns_and_filters_nothing(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_qualified_frame(self._df(), "nosuch==1", "")
        assert len(got) == 4
        assert any("filter skipped" in str(w.message) for w in caught)

    def test_the_caller_is_named_in_the_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_qualified_frame(self._df(), "@evil", "", "kpi 'k1'")
        assert any("kpi 'k1'" in str(w.message) for w in caught)

    def test_a_malformed_in_is_ignored_rather_than_raising(self):
        assert len(dr._dash_qualified_frame(self._df(), "", "notarange")) == 4


class TestTheEmptyLayerReport:
    def test_no_renderers_is_empty(self):
        assert dr._dash_layer_drew_anything([]) is False

    def test_a_renderer_with_rows_drew(self):
        from bokeh.models import ColumnDataSource
        r = type("R", (), {"data_source": ColumnDataSource({"x": [1.0]})})()
        assert dr._dash_layer_drew_anything([r]) is True

    def test_a_renderer_with_no_rows_drew_nothing(self):
        from bokeh.models import ColumnDataSource
        r = type("R", (), {"data_source": ColumnDataSource({"x": []})})()
        assert dr._dash_layer_drew_anything([r]) is False

    def test_a_renderer_with_no_source_counts_as_drawn(self):
        """An annotation is not a data glyph; it must not be called empty."""
        r = type("R", (), {"data_source": None})()
        assert dr._dash_layer_drew_anything([r]) is True

    def test_the_report_names_graph_layer_type_and_rows(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_report_empty_layer("g1", 2, "pci", 1234)
        msg = str(caught[0].message)
        assert "'g1'" in msg and "plot 2" in msg and "pci" in msg
        assert "1,234" in msg


class TestTheLegendKeyRule:
    @pytest.mark.parametrize("ptype", sorted(dr._DASH_FIT_TYPES))
    def test_a_computed_layer_is_keyed_as_twoway_keys_it(self, ptype):
        """Flipped (WP-30 P1.16): "Fitted values" was wrong because twoway
        keys each fit in its own text (series_label_truth.json F01-F16)."""
        want = {"fpfit": "Predicted mpg", "function": "y",
                "lfit": "Fitted values", "qfit": "Fitted values",
                "lowess": "lowess mpg", "lpoly": "lpoly smooth: mpg",
                "mband": "Median bands", "mspline": "Median spline"}
        assert dr._dash_legend_key({"type": ptype, "yvar": "mpg"}) == \
               want[ptype]

    @pytest.mark.parametrize("ptype", sorted(dr._DASH_CI_TYPES))
    def test_a_ci_layer_is_keyed_by_its_line_on_its_own(self, ptype):
        """Flipped (WP-30 P1.16): "Fitted values" was wrong for fpfitci and
        lpolyci because twoway keys their lines "Predicted <y>" and "lpoly
        smooth: <y>" (series_label_truth.json F20, F22)."""
        want = {"fpfitci": "Predicted mpg", "lpolyci": "lpoly smooth: mpg",
                "lfitci": "Fitted values", "qfitci": "Fitted values"}
        assert dr._dash_legend_key({"type": ptype, "yvar": "mpg"}) == \
               want[ptype]

    def test_a_data_layer_is_keyed_with_the_variable_label(self):
        assert dr._dash_legend_key({"type": "scatter", "yvar": "mpg"},
                                   {"mpg": "Mileage (mpg)"}) == \
               "Mileage (mpg)"

    def test_a_data_layer_falls_back_to_the_variable_name(self):
        assert dr._dash_legend_key({"type": "scatter", "yvar": "mpg"}) == "mpg"

    def test_a_univariate_layer_uses_twoways_key(self):
        """WP-29 P0.3 (flipped): twoway keys a histogram by its y-scale word
        and a kdensity layer ``kdensity <name>``, by the NAME even when the
        variable is labelled (HK.svg, KDLAB.svg) -- never by the variable."""
        assert dr._dash_legend_key({"type": "histogram", "var": "mpg"}) == \
               "Density"
        assert dr._dash_legend_key({"type": "histogram", "var": "mpg",
                                    "options": {"percent": "percent"}}) == \
               "Percent"
        assert dr._dash_legend_key({"type": "kdensity", "var": "mpg"},
                                   {"mpg": "Mileage (mpg)"}) == "kdensity mpg"

    def test_an_empty_label_falls_back_to_the_name(self):
        """WP-29 P0.3: Stata's exporter writes "" for an unlabelled variable;
        twoway keys it by its name, never by the plot type."""
        assert dr._dash_legend_key({"type": "scatter", "yvar": "mpg"},
                                   {"mpg": ""}) == "mpg"

    def test_a_range_layer_uses_its_first_boundary(self):
        assert dr._dash_legend_key({"type": "rbar", "yvar1": "lo"}) == "lo"

    def test_an_immediate_layer_is_keyed_as_twoway_keys_it(self):
        """Flipped (WP-30 P1.16): "pci" was wrong because twoway keys pci
        "y/yb" and scatteri "y" (series_label_truth.json I01, I02); a data
        layer with no variable still falls back to its type."""
        assert dr._dash_legend_key({"type": "pci"}) == "y/yb"
        assert dr._dash_legend_key({"type": "scatteri"}) == "y"
        assert dr._dash_legend_key({"type": "scatter"}) == "scatter"

    def test_a_ci_layer_splits_into_a_band_key_and_a_line_key(self):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y1": [0.0, 1.0],
                                "y2": [2.0, 3.0], "y": [1.0, 2.0]})
        band = fig.varea(x="x", y1="y1", y2="y2", source=src)
        line = fig.line(x="x", y="y", source=src)
        got = dr._dash_legend_entries(
            [({"type": "lfitci", "yvar": "mpg", "options": {}},
              [band, line])], {}, 95.0)
        assert [lbl for lbl, _ in got] == ["95% CI", "Fitted values"]
        assert got[0][1] == [band] and got[1][1] == [line]

    def test_the_level_reaches_the_band_key(self):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y1": [0.0, 1.0],
                                "y2": [2.0, 3.0], "y": [1.0, 2.0]})
        band = fig.varea(x="x", y1="y1", y2="y2", source=src)
        line = fig.line(x="x", y="y", source=src)
        got = dr._dash_legend_entries(
            [({"type": "lfitci", "options": {"level": "90"}},
              [band, line])], {}, 95.0)
        assert got[0][0] == "90% CI"

    def test_a_layer_that_drew_nothing_gets_no_key(self):
        assert dr._dash_legend_entries([({"type": "scatter",
                                          "yvar": "mpg"}, [])]) == []

    def test_a_colorvar_swatch_is_not_a_series_key(self):
        swatch = type("R", (), {"name": "_clegend_0", "glyph": None})()
        assert dr._dash_legend_entries(
            [({"type": "scatter", "yvar": "mpg"}, [swatch])]) == []


class TestTheKpiFormatHelpers:
    def test_an_explicit_format_wins(self):
        assert dr._dash_effective_kpi_fmt({"fmt": "%9.2f"}, "w",
                                          {"w": "%12.0fc"}) == "%9.2f"

    def test_the_variables_own_format_is_next(self):
        assert dr._dash_effective_kpi_fmt({"fmt": ""}, "w",
                                          {"w": "%12.0fc"}) == "%12.0fc"

    def test_statas_default_is_last(self):
        assert dr._dash_effective_kpi_fmt({"fmt": ""}, "w", {}) == "%9.0g"

    def test_the_c_suffix_groups(self):
        assert dr._dash_format_kpi_value(1234567.0, "%12.0fc") == "1,234,567"

    def test_without_the_c_suffix_it_does_not(self):
        assert dr._dash_format_kpi_value(1234567.0, "%12.0f") == "1234567"

    def test_grouping_keeps_the_decimals(self):
        assert dr._dash_format_kpi_value(1234.5, "%12.1fc") == "1,234.5"

    def test_the_default_shows_six_significant_digits(self):
        assert dr._dash_format_kpi_value(21.297297297, "%9.0g") == "21.2973"

    def test_an_empty_format_is_the_default(self):
        assert dr._dash_format_kpi_value(21.297297297, "") == "21.2973"

    def test_missing_is_a_dot(self):
        assert dr._dash_format_kpi_value(float("nan"), "%9.2f") == "."

    def test_an_unusable_format_does_not_raise(self):
        assert dr._dash_format_kpi_value(1.0, "%notaformat")

    # WP-28 section 11 (GAPS2 E1): the date_formatter parameter is retired;
    # a date-valued statistic (its Stata value since WP-29 P0.20) is
    # written in its effective %t picture by _dash_fmt_text, as Stata
    # displays it.

    def test_a_date_valued_statistic_is_shown_as_a_date(self):
        # WP-29 P0.20 (section 05): the statistic is the Stata value,
        # 15342 (02jan2002); it was epoch milliseconds.
        got = dr._dash_format_kpi_value(
            15342.0, "%td", "date", "max",
            date_vars={"date": "td"})
        assert got == "02jan2002"
        got = dr._dash_format_kpi_value(
            15342.0, "%tdCCYY-NN-DD", "date", "max",
            date_vars={"date": "td"})
        assert got == "2002-01-02"

    def test_a_non_date_statistic_of_a_date_variable_is_not(self):
        """`count' of a date variable is a count, not a date."""
        got = dr._dash_format_kpi_value(
            4.0, "%9.0g", "date", "count",
            date_vars={"date": "td"})
        assert got == "4"


class TestTheColumnCarry:
    @staticmethod
    def _src():
        from bokeh.models import ColumnDataSource
        return ColumnDataSource({"x": [1.0, 2.0, 3.0],
                                 "extra": ["a", "b", "c"],
                                 "num": [10.0, 20.0, 30.0]})

    def test_other_columns_are_carried(self):
        data = {"x0": [1.0, 2.0, 3.0]}
        got = dr.GlyphMapper._carry_cols(self._src(), data)
        assert got["extra"] == ["a", "b", "c"]
        # A numeric column is carried as a float64 array (WP-31 G4).
        assert got["num"].tolist() == [10.0, 20.0, 30.0]

    def test_an_existing_key_is_never_overwritten(self):
        data = {"x": [9.0, 9.0, 9.0]}
        got = dr.GlyphMapper._carry_cols(self._src(), data)
        assert got["x"] == [9.0, 9.0, 9.0]

    def test_a_selector_is_applied(self):
        import numpy as np
        data = {"x0": [1.0, 3.0]}
        got = dr.GlyphMapper._carry_cols(self._src(), data,
                                         np.array([0, 2]))
        assert got["extra"] == ["a", "c"]

    def test_a_column_of_the_wrong_length_is_skipped(self):
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "short": [1.0]})
        got = dr.GlyphMapper._carry_cols(src, {"x0": [1.0, 2.0, 3.0]})
        assert "short" not in got

    def test_an_empty_derived_dict_is_returned_unchanged(self):
        assert dr.GlyphMapper._carry_cols(self._src(), {}) == {}


class TestTheMaskedIndex:
    @staticmethod
    def _src():
        from bokeh.models import ColumnDataSource
        return ColumnDataSource({"x": [3.0, float("nan"), 1.0, 2.0],
                                 "y": [1.0, 2.0, 3.0, float("nan")]})

    def test_it_drops_the_rows_masked_drops(self):
        idx = dr.GlyphMapper._masked_index(self._src(), None, "x", "y")
        assert list(idx) == [0, 2]

    def test_it_keeps_the_original_order(self):
        idx = dr.GlyphMapper._masked_index(self._src(), None, "x")
        assert list(idx) == [0, 2, 3]

    # Flipped (WP-29 P0.1): _masked_order, the drawn rows in x order, is
    # gone -- twoway joins in the data's order unless sort is given -- and
    # these two hold _join_order under sort to what it pinned.
    def test_join_order_under_sort_is_the_same_rows_sorted_by_x(self):
        src = self._src()
        idx = dr.GlyphMapper._join_order(
            src, dr.GlyphMapper._masked_index(src, None, "x", "y"), "x",
            {"sort": "sort"})
        assert list(idx) == [2, 0]

    def test_join_order_selects_the_masked_rows(self):
        src = self._src()
        a = set(dr.GlyphMapper._masked_index(src, None, "x", "y"))
        b = set(dr.GlyphMapper._join_order(
            src, dr.GlyphMapper._masked_index(src, None, "x", "y"), "x",
            {"sort": "sort"}))
        assert a == b


class TestTheHoverBuilder:
    @staticmethod
    def _fig_with(cols):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        fig = figure()
        fig.scatter(x=list(cols)[0], y=list(cols)[1],
                    source=ColumnDataSource(cols))
        return fig

    def test_it_builds_one_tool(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0]})
        dr._dash_build_hover(fig, "weight", "mpg", "", [])
        assert len([t for t in fig.tools if isinstance(t, HoverTool)]) == 1

    def test_it_clears_what_came_before(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0]})
        fig.add_tools(HoverTool(tooltips=[("old", "@old")]))
        fig.add_tools(HoverTool(tooltips=[("older", "@older")]))
        dr._dash_build_hover(fig, "weight", "mpg", "", [])
        tools = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert len(tools) == 1 and tools[0].tooltips == [
            ("weight", "@{weight}"), ("mpg", "@{mpg}")]

    def test_an_extra_is_added_when_the_column_is_there(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0],
                              "foreign": [0.0]})
        dr._dash_build_hover(fig, "weight", "mpg", "", ["foreign"])
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        assert ("foreign", "@{foreign}") in t.tooltips

    def test_an_extra_that_is_not_there_is_skipped(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0]})
        dr._dash_build_hover(fig, "weight", "mpg", "", ["nosuch"])
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        assert all("nosuch" not in f[1] for f in t.tooltips)

    def test_a_variable_label_names_the_row(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0]})
        dr._dash_build_hover(fig, "weight", "mpg", "", [],
                             var_labels={"mpg": "Mileage (mpg)"})
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        assert ("Mileage (mpg)", "@{mpg}") in t.tooltips

    def test_a_display_format_reaches_the_field(self):
        from bokeh.models import HoverTool
        fig = self._fig_with({"weight": [1.0], "mpg": [2.0]})
        dr._dash_build_hover(fig, "weight", "mpg", "", [],
                             numeric_formats={"mpg": "%9.2f"})
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        assert any(f[0] == "mpg" and "{" in f[1][len("@{mpg}"):]
                   for f in t.tooltips)

    def test_a_histogram_gets_the_bin_tooltip(self):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource, HoverTool
        fig = figure()
        fig.quad(top="top", bottom=0, left="left", right="right",
                 source=ColumnDataSource({"top": [1.0], "left": [0.0],
                                          "right": [1.0]}))
        dr._dash_build_hover(fig, "", "", "", [], univar="mpg")
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        # WP-30 P1.23b: 'Count' was wrong because a histogram's height is
        # the measure its y axis is titled with; an untagged bar is
        # Density, twoway's default.
        assert t.tooltips[0][0] == "mpg" and t.tooltips[1][0] == "Density"
        assert t.mode == "vline"

    def test_a_density_curve_gets_the_generic_tooltip(self):
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource, HoverTool
        fig = figure()
        fig.line(x="x", y="y", source=ColumnDataSource({"x": [1.0, 2.0],
                                                        "y": [3.0, 4.0]}))
        dr._dash_build_hover(fig, "", "", "", [])
        t = [x for x in fig.tools if isinstance(x, HoverTool)][0]
        assert [f[0] for f in t.tooltips] == ["x", "y"]

    def test_a_figure_with_no_renderers_gets_no_tool(self):
        from bokeh.plotting import figure
        from bokeh.models import HoverTool
        fig = figure()
        dr._dash_build_hover(fig, "weight", "mpg", "", [])
        assert not [t for t in fig.tools if isinstance(t, HoverTool)]

    def test_the_comprehensive_tool_wins_over_the_fallback(self):
        """A figure that has both keeps one tool, on the renderers that fit."""
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource, HoverTool
        fig = figure()
        pts = fig.scatter(x="weight", y="mpg",
                          source=ColumnDataSource({"weight": [1.0],
                                                   "mpg": [2.0]}))
        fig.line(x="x", y="y",
                 source=ColumnDataSource({"x": [1.0], "y": [2.0]}))
        dr._dash_build_hover(fig, "weight", "mpg", "", [])
        tools = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert len(tools) == 1 and tools[0].renderers == [pts]
