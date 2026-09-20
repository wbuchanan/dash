"""`link()` was a no-op in server mode.

The generated app builds one ``shared_source`` for the graphs named by
``link()`` and records it in ``graph_sources``. Every plot then ignores it and
builds its own::

    clean = g_df[_sc_cols].dropna() if xvar and yvar else g_df
    csrc = ColumnDataSource(clean) if xvar and yvar else src

**Measured:** two graphs under ``link(_all)`` rendered from two distinct
ColumnDataSources, so a box-select in one could never appear in the other.
``shared_source`` was in the document only when some other path happened to
put it there.

`dash.sthlp` documents `link()` for both modes without qualification.

Linking shares a source, so a graph with its own `if`/`in` qualifier cannot
simply be pointed at it — that would show rows the qualifier excluded. Those
graphs get a ``CDSView`` over the shared source instead, which is how the
standalone renderer has always done it.
"""
import importlib.util
import itertools
import json
import os
import sys

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_DF = pd.DataFrame({
    "mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
})
_SEQ = itertools.count()


def _doc(tmp_path, link="", graph_opts=None, n_graphs=2):
    tag = next(_SEQ)
    names = [f"g{i + 1}" for i in range(n_graphs)]
    graph_opts = graph_opts or {}
    graphs = []
    for n in names:
        go = {"name": n}
        go.update(graph_opts.get(n, {}))
        graphs.append({"name": n, "graph_options": go,
                       "plots": [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}],
                       "options": {}})
    bo = {"layout": "auto", "link": link, "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": " ".join(names), "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    spec = tmp_path / f"s_{tag}.json"
    data = tmp_path / f"d_{tag}.json"
    app = tmp_path / f"a_{tag}.py"
    spec.write_text(json.dumps({"graphs": graphs, "kpis": [],
                                "build_options": bo}))
    data.write_text(json.dumps(make_data_json(_DF)))
    dr.ServerAppBuilder(str(spec), str(data)).build(str(app))
    ms = importlib.util.spec_from_file_location(f"_link_app_{tag}", str(app))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc


def _scatter_renderers(doc):
    out = []
    for m in doc.select({"type": object}):
        src = getattr(m, "data_source", None)
        if isinstance(src, ColumnDataSource) and getattr(m, "glyph", None):
            out.append(m)
    return out


def _distinct_sources(doc):
    return {id(r.data_source) for r in _scatter_renderers(doc)}


class TestLinkSharesASource:
    def test_link_all_gives_every_graph_the_same_source(self, tmp_path):
        doc = _doc(tmp_path, link="_all")
        assert len(_distinct_sources(doc)) == 1, (
            "link(_all) left each graph with its own source, so a selection "
            "in one cannot appear in the other"
        )

    def test_no_link_leaves_them_independent(self, tmp_path):
        doc = _doc(tmp_path, link="")
        assert len(_distinct_sources(doc)) == 2

    def test_an_explicit_list_links_only_those_named(self, tmp_path):
        doc = _doc(tmp_path, link="g1 g2", n_graphs=3)
        srcs = [id(r.data_source) for r in _scatter_renderers(doc)]
        assert len(set(srcs)) == 2, (
            f"expected the two named graphs to share and the third not to, "
            f"got {len(set(srcs))} distinct sources"
        )

    def test_a_selection_in_one_is_visible_to_the_other(self, tmp_path):
        doc = _doc(tmp_path, link="_all")
        rends = _scatter_renderers(doc)
        rends[0].data_source.selected.indices = [1, 2]
        assert rends[1].data_source.selected.indices == [1, 2]


class TestLinkRespectsAQualifier:
    def test_a_qualified_linked_graph_draws_only_its_own_rows(self, tmp_path):
        """Sharing a source must not show rows the `if' excluded."""
        doc = _doc(tmp_path, link="_all",
                   graph_opts={"g2": {"if_expr": "foreign == 1"}})
        rends = _scatter_renderers(doc)
        assert len(_distinct_sources(doc)) == 1, "still one shared source"
        views = [getattr(r, "view", None) for r in rends]
        filtered = [v for v in views
                    if v is not None and getattr(v, "filter", None) is not None]
        assert filtered, "the qualified graph got no view over the shared source"
        idx = None
        for v in filtered:
            f = v.filter
            if hasattr(f, "indices") and f.indices is not None:
                idx = list(f.indices)
        assert idx is not None
        expected = [i for i, v in enumerate(_DF["foreign"]) if v == 1.0]
        assert idx == expected, (
            f"the view shows rows {idx}, the qualifier selects {expected}"
        )
