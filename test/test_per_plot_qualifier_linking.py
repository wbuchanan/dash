"""A per-plot `if` took its layer out of the shared source.

`_apply_graph_filter` gives the layer its own frame, and the renderer wrapped
that frame in a **new** ColumnDataSource::

    source_for_plot = ColumnDataSource(_pdf)

For an unlinked graph that is harmless. For a **linked** one it is not: the
whole point of ``link()`` is that every graph draws from one source, so a
selection in one appears in the others and one filter move reaches them all.
A layer on a source of its own is outside both.

**Measured** on ``link(_all)`` with two graphs, the second layer of the first
carrying ``if foreign==1``: ``g1.r0`` and ``g2.r0`` shared one source and
``g1.r1`` had its own — three renderers, two sources, one of them reachable
by nothing.

The graph-level qualifier already solved this, with a ``CDSView`` over a
``BooleanFilter`` registered through ``_register_view_filter`` so the filter
callback rebuilds the mask when the shared source is shortened. The per-plot
qualifier now does the same, and where a facet view is already on the layer
the two masks are intersected rather than one replacing the other.
"""
import json
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import AllIndices, BooleanFilter, IndexFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_DF = pd.DataFrame({
    "mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0, 27.0, 16.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 2050.0, 3800.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0],
})
_N_FOREIGN = int((_DF["foreign"] == 1).sum())


def _render(tmp_path, link, plots, second_graph=True, graph_if=""):
    graphs = [{"name": "g1", "graph_options": {"name": "g1"},
               "options": {}, "plots": plots}]
    if graph_if:
        graphs[0]["if_expr"] = graph_if
    if second_graph:
        graphs.append({"name": "g2", "graph_options": {"name": "g2"},
                       "options": {},
                       "plots": [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}]})
    names = " ".join(g["name"] for g in graphs)
    spec = tmp_path / f"spec_{abs(hash((link, json.dumps(plots), graph_if)))}.json"
    data = tmp_path / "data.json"
    spec.write_text(json.dumps({
        "graphs": graphs, "kpis": [],
        "build_options": {"layout": "auto", "link": link, "filter": "",
                          "theme": "", "scheme": "", "session_scheme": "",
                          "title": "", "subtitle": "", "registry": names,
                          "tabs": "", "filter_position": "top",
                          "level": "95", "formats": {}}}))
    data.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(str(spec), str(data))
        r.render()
    return r


def _glyphs(fig):
    return [ren for ren in fig.renderers if getattr(ren, "glyph", None)]


def _visible(renderer):
    n = max((len(v) for v in renderer.data_source.data.values()), default=0)
    filt = getattr(getattr(renderer, "view", None), "filter", None)
    if filt is None or isinstance(filt, AllIndices):
        return n
    if isinstance(filt, IndexFilter):
        return len(filt.indices or [])
    if isinstance(filt, BooleanFilter):
        return int(sum(1 for b in (filt.booleans or []) if b))
    return n


_QUALIFIED = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
              "options": {}, "if_expr": "foreign==1"}
_PLAIN = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}


class TestALinkedLayerStaysOnTheSharedSource:
    def test_every_layer_of_a_linked_graph_shares_one_source(self, tmp_path):
        r = _render(tmp_path, "_all", [_PLAIN, dict(_QUALIFIED)])
        srcs = {id(ren.data_source)
                for fig in r.figures.values() for ren in _glyphs(fig)}
        assert len(srcs) == 1, (
            f"link(_all) left {len(srcs)} distinct sources; the qualified "
            f"layer is outside the link"
        )

    def test_the_qualifier_is_still_applied(self, tmp_path):
        r = _render(tmp_path, "_all", [_PLAIN, dict(_QUALIFIED)])
        rends = _glyphs(r.figures["g1"])
        assert len(rends) == 2
        assert _visible(rends[0]) == len(_DF)
        assert _visible(rends[1]) == _N_FOREIGN

    def test_it_is_a_view_not_a_shortened_source(self, tmp_path):
        r = _render(tmp_path, "_all", [_PLAIN, dict(_QUALIFIED)])
        rends = _glyphs(r.figures["g1"])
        filt = getattr(getattr(rends[1], "view", None), "filter", None)
        assert isinstance(filt, BooleanFilter), (
            f"expected a BooleanFilter over the shared source, got {filt!r}"
        )
        assert len(filt.booleans) == len(_DF)

    def test_the_filter_callback_knows_about_it(self, tmp_path):
        """Otherwise the mask stops matching once a filter shortens the source."""
        r = _render(tmp_path, "_all", [_PLAIN, dict(_QUALIFIED)])
        registered = getattr(r, "_view_filters", [])
        masks = [f for _src, f, _ids in registered
                 if isinstance(f, BooleanFilter)
                 and sum(1 for b in f.booleans if b) == _N_FOREIGN]
        assert masks, (
            "the per-plot view was not registered, so a filter move would "
            "leave it masking the wrong rows"
        )


class TestTheUnlinkedCaseIsUnchanged:
    def test_an_unlinked_graph_still_filters_its_layer(self, tmp_path):
        r = _render(tmp_path, "", [_PLAIN, dict(_QUALIFIED)])
        rends = _glyphs(r.figures["g1"])
        assert _visible(rends[0]) == len(_DF)
        assert _visible(rends[1]) == _N_FOREIGN

    def test_a_qualifier_does_not_leak_onto_later_layers(self, tmp_path):
        r = _render(tmp_path, "_all", [dict(_QUALIFIED), _PLAIN])
        rends = _glyphs(r.figures["g1"])
        assert _visible(rends[0]) == _N_FOREIGN
        assert _visible(rends[1]) == len(_DF)


class TestItComposesWithAGraphLevelQualifier:
    def test_the_two_masks_intersect(self, tmp_path):
        """A graph-level `if` and a plot-level one both bind."""
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {}, "if_expr": "weight < 3000"}]
        r = _render(tmp_path, "_all", plots, graph_if="foreign==1")
        rends = _glyphs(r.figures["g1"])
        expected = int(((_DF["foreign"] == 1) & (_DF["weight"] < 3000)).sum())
        assert _visible(rends[0]) == expected, (
            f"expected the intersection ({expected} rows), got "
            f"{_visible(rends[0])}"
        )
