"""A plot layer that drew nothing said nothing.

`pci` and `pcscatter` each produced a titled, axed, empty plot region with
rc 0 and no warning, and nothing in the repository noticed -- because the
299-command conformance corpus appends `name()` to every probe, which
registers the spec and never renders it. The drop-in claim was proved at the
`syntax` layer and no further.

So the renderer now says so. After each layer is dispatched it knows how many
renderers that layer produced and whether any of them holds data; if the
frame has rows and the layer does not, the layer is named:

    dash: graph 'g1' plot 2 (pcscatter) drew nothing from 74 observations.

That turns "draws nothing" from a defect no test could see into one every
render reports, and it is what test_conformance.cscript asserts across the
corpus.

A layer may be legitimately empty -- an `if' qualifier that selects no rows,
or a smoother whose optional package is absent -- so the report fires only
when the graph's own data is non-empty, and the optional-package layers warn
for themselves already.

Since a2c7502 the rule is one function both renderers run,
_dash_note_empty_layer: scatteri, pci and pcarrowi draw from their own values
and are never reported; a function drawn empty is reported whatever the
data, in the form without a count ("dash: graph 'g1' plot 2 (function) drew
nothing."); every other layer as above.  Flipped (WP-30 P1.22): the note now
says why the fallback drew nothing ("drew nothing: it needs the points Stata
computes for it when dash registers the graph, ...").
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr

_DF = pd.DataFrame({
    "y":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "x":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "y2": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "x2": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
})


#: WP-30 P1.22: the one note for a rejected function expression, plot 2.
#: Flipped (WP-31 F2): the note lists the comparisons, logic and functions
#: the fallback reads now.
_REJECTED_FN_NOTE = (
    "dash: graph 'g1' plot 2 (function) drew nothing: it needs the points "
    "Stata computes for it when dash registers the graph, and this spec "
    "carries none; without them dash evaluates only x, _pi, c(pi), "
    "numbers and missing values, + - * / ^, the comparisons "
    "== != ~= > < >= <=, ! ~ & | and sin(), cos(), tan(), exp(), log(), "
    "log10(), sqrt(), abs(), floor(), ceil(), ln(), int(), trunc(), "
    "round(), min(), max(), cond(), normal(), normalden() and "
    "invnormal(), and __import__() is not one of them.")


from conftest import render_models  # noqa: E402


def _render_full(plots, graph_options=None, graph_keys=None):
    """Render; return the renderer and the warnings' messages.

    *graph_keys* go on the graph itself, beside "plots" -- where dash.ado
    writes the graph's qualifier ("if_expr", "in_expr") and where the saved
    renderer reads it (_apply_graph_filter).  Inside graph_options only the
    served app reads a qualifier.
    """
    td = tempfile.mkdtemp()
    graph = {"name": "g1",
             "graph_options": dict(graph_options or {}, name="g1"),
             "options": {}, "plots": plots}
    graph.update(graph_keys or {})
    spec = {"graphs": [graph],
            "kpis": [], "build_options": {"layout": "auto", "level": "95"}}
    sp, dp = os.path.join(td, "s.json"), os.path.join(td, "d.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump({"variableNames": list(_DF.columns),
                   "values": _DF.to_dict("records")}, fh)
    renderer = dr.DashRenderer(sp, dp)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        render_models(renderer)
    return renderer, [str(w.message) for w in caught]


def _render(plots, graph_options=None, graph_keys=None):
    return _render_full(plots, graph_options, graph_keys)[1]


def _empty_reports(msgs):
    return [m for m in msgs if "drew nothing" in m]


class TestALayerThatDrawsNothingIsNamed:
    def test_an_unknown_plot_type_is_reported(self):
        msgs = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {}},
                        {"type": "no_such_plot_type", "yvar": "y",
                         "xvar": "x", "options": {}}])
        hits = _empty_reports(msgs)
        assert hits, f"a layer that drew nothing was not reported: {msgs}"
        assert any("no_such_plot_type" in m for m in hits), (
            f"the report does not name the plot type: {hits}"
        )
        assert any("g1" in m for m in hits), (
            f"the report does not name the graph: {hits}"
        )

    def test_a_function_whose_expression_is_rejected_is_reported(self):
        """The validator refuses it and the layer is drawn empty.

        Flipped (WP-30 P1.22): the note now says why the fallback drew
        nothing."""
        msgs = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {}},
                        {"type": "function", "expr": "__import__('os')",
                         "options": {}}])
        assert _empty_reports(msgs), (
            f"a rejected function expression drew nothing in silence: {msgs}"
        )
        # Since a2c7502 a function is reported in the form without a count:
        # it draws from its own grid and never read the 6 observations.
        assert _empty_reports(msgs) == [_REJECTED_FN_NOTE], msgs

    def test_a_rejected_function_is_reported_when_no_row_is_selected(self):
        """The positive control for the qualifier test below: the same graph
        and the same qualifier, and the report still runs.  A function drawn
        empty is reported whatever the data (since a2c7502); the scatter,
        plot 1, drew from no rows and is not.

        Flipped (WP-30 P1.22): the note now says why the fallback drew
        nothing."""
        msgs = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {}},
                        {"type": "function", "expr": "__import__('os')",
                         "options": {}}],
                       graph_keys={"if_expr": "y > 1000"})
        assert _empty_reports(msgs) == [_REJECTED_FN_NOTE], msgs

    def test_the_report_names_the_observation_count(self):
        msgs = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {}},
                        {"type": "no_such_plot_type", "yvar": "y",
                         "xvar": "x", "options": {}}])
        assert any("6 observation" in m for m in _empty_reports(msgs)), (
            f"the report does not say how many rows were available: {msgs}"
        )


class TestAnOrdinaryGraphIsSilent:
    """The control: a report on every render is a report nobody reads."""

    @pytest.mark.parametrize("ptype", ["scatter", "line", "connected", "area",
                                       "bar", "spike", "histogram", "lfit",
                                       "qfit", "mband", "dropline"])
    def test_a_working_layer_is_not_reported(self, ptype):
        plot = ({"type": ptype, "yvar": "y", "xvar": "", "options": {}}
                if ptype == "histogram"
                else {"type": ptype, "yvar": "y", "xvar": "x", "options": {}})
        msgs = _render([plot])
        assert not _empty_reports(msgs), (
            f"{ptype} draws and was reported as empty: {msgs}"
        )

    def test_a_qualifier_that_selects_no_rows_is_not_reported(self):
        """An empty selection is the user's own doing, not a broken layer."""
        # The qualifier sat inside graph_options until 24sep2026, which the
        # saved renderer never reads: all 6 rows drew and the empty
        # selection was never exercised (measured: the source held 6 rows).
        # At the graph level, where dash.ado writes it, it selects none.
        renderer, msgs = _render_full(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            graph_keys={"if_expr": "y > 1000"})
        rows = {k: len(v) for k, v in renderer.sources["g1"].data.items()}
        assert rows and not any(rows.values()), (
            f"the qualifier selected rows, so nothing here is empty: {rows}"
        )
        assert not _empty_reports(msgs), (
            f"an if() that matches nothing was reported as a broken layer: "
            f"{msgs}"
        )
