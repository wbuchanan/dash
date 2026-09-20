"""`update(brush)` only worked in server mode if `link()` was also given.

The generated app builds one ``shared_source`` for the graphs named by
``link()``, gives every other graph a source of its own, and then attaches
the brush callback to ``shared_source`` — unconditionally::

    shared_source.selected.on_change('indices', _make_brush_cb(...))

So with no ``link()``, the callback sits on a ColumnDataSource that no glyph
renders from. Measured: with ``link()`` absent the document contains exactly
one ColumnDataSource, the graph's own, and ``shared_source`` is not in the
document at all — nothing can select it, so brushing can never fire the
callback and a KPI declared ``update(brush)`` never changes.

`dash.sthlp` lists brush/lasso KPI update as supported in server mode without
qualification.
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

_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0],
                    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0]})
_SEQ = itertools.count()


def _kpi(name="k1", update="brush"):
    return {"name": name, "stat": "mean", "var": "mpg", "value": "22",
            "display": "22.00", "fmt": "%9.2f", "title": "Avg",
            "subtitle": "", "color": "", "bgcolor": "", "update": update,
            "if_expr": "", "in_expr": ""}


def _doc(tmp_path, link="", n_graphs=1, kpis=None, update="brush"):
    tag = next(_SEQ)
    names = [f"g{i + 1}" for i in range(n_graphs)]
    kpis = kpis if kpis is not None else [_kpi(update=update)]
    graphs = [{"name": n, "graph_options": {"name": n},
               "plots": [{"type": "scatter", "yvar": "mpg",
                          "xvar": "weight", "options": {}}],
               "options": {}} for n in names]
    bo = {"layout": "auto", "link": link, "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": " ".join(names + [k["name"] for k in kpis]),
          "tabs": "", "filter_position": "top", "level": "95", "formats": {}}
    spec = tmp_path / f"spec_{tag}.json"
    data = tmp_path / f"data_{tag}.json"
    app = tmp_path / f"app_{tag}.py"
    spec.write_text(json.dumps({"graphs": graphs, "kpis": kpis,
                                "build_options": bo}))
    data.write_text(json.dumps(make_data_json(_DF)))
    dr.ServerAppBuilder(str(spec), str(data)).build(str(app))
    mspec = importlib.util.spec_from_file_location(f"_brush_app_{tag}",
                                                   str(app))
    mod = importlib.util.module_from_spec(mspec)
    mspec.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc


def _rendered_sources(doc):
    """Every ColumnDataSource some glyph actually draws from."""
    out = []
    for m in doc.select({"type": object}):
        src = getattr(m, "data_source", None)
        if isinstance(src, ColumnDataSource) and src not in out:
            out.append(src)
    return out


def _has_selection_callback(src) -> bool:
    sel = getattr(src, "selected", None)
    if sel is None:
        return False
    cbs = getattr(sel, "_callbacks", None) or {}
    return bool(cbs.get("indices"))


class TestBrushReachesTheSourceThatIsDrawn:
    def test_without_link_the_drawn_source_still_gets_the_callback(
            self, tmp_path):
        doc = _doc(tmp_path, link="")
        srcs = _rendered_sources(doc)
        assert srcs, "no rendered source in the document"
        assert any(_has_selection_callback(s) for s in srcs), (
            "update(brush) was wired to a source no glyph renders from"
        )

    def test_with_link_all_it_still_works(self, tmp_path):
        doc = _doc(tmp_path, link="_all")
        assert any(_has_selection_callback(s)
                   for s in _rendered_sources(doc))

    def test_every_graph_can_start_a_brush_when_unlinked(self, tmp_path):
        """Two independent graphs: brushing either must update the KPI."""
        doc = _doc(tmp_path, link="", n_graphs=2)
        srcs = _rendered_sources(doc)
        assert len(srcs) >= 2, f"expected a source per graph, got {len(srcs)}"
        assert all(_has_selection_callback(s) for s in srcs)

    def test_no_brush_kpi_means_no_callback(self, tmp_path):
        """Nothing is wired when no KPI asks for it."""
        doc = _doc(tmp_path, link="", kpis=[_kpi(update="filter")])
        assert not any(_has_selection_callback(s)
                       for s in _rendered_sources(doc))

    def test_update_both_also_wires_the_brush(self, tmp_path):
        doc = _doc(tmp_path, link="", update="both")
        assert any(_has_selection_callback(s)
                   for s in _rendered_sources(doc))


def _kpi_text(doc):
    from bokeh.models import Div
    out = []

    def walk(m, seen=None):
        seen = seen if seen is not None else set()
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    walk(x, seen)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, Div):
            out.append(m.text)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                walk(k, seen)

    for r in doc.roots:
        walk(r)
    return " ".join(out)


class TestTheBrushProducesTheRightNumber:
    """Wiring is not enough: the selected rows must be the right rows."""

    def test_brushing_two_points_gives_their_mean(self, tmp_path):
        doc = _doc(tmp_path, link="")
        src = next(s for s in _rendered_sources(doc)
                   if _has_selection_callback(s))
        # Rows 0 and 1 of the source: mpg 22 and 18 -> mean 20.00
        ids = list(src.data["index"])[:2]
        expected = _DF.loc[[i for i in ids], "mpg"].mean()
        src.selected.indices = [0, 1]
        assert f"{expected:.2f}" in _kpi_text(doc)

    def test_a_source_with_dropped_rows_still_names_the_right_rows(
            self, tmp_path):
        """The bug positional indexing hid.

        The source is ``g_df[cols].dropna()``; reading its selection indices
        as positions in the full frame silently names different rows as soon
        as anything is missing.
        """
        tag = next(_SEQ)
        df = pd.DataFrame({
            "mpg": [99.0, 99.0, 99.0, 11.0, 13.0],
            "weight": [float("nan"), float("nan"), float("nan"),
                       1000.0, 2000.0],
        })
        graphs = [{"name": "g1", "graph_options": {"name": "g1"},
                   "plots": [{"type": "scatter", "yvar": "mpg",
                              "xvar": "weight", "options": {}}],
                   "options": {}}]
        kpis = [_kpi()]
        bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
              "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
              "registry": "g1 k1", "tabs": "", "filter_position": "top",
              "level": "95", "formats": {}}
        spec = tmp_path / f"s_{tag}.json"
        data = tmp_path / f"d_{tag}.json"
        app = tmp_path / f"a_{tag}.py"
        spec.write_text(json.dumps({"graphs": graphs, "kpis": kpis,
                                    "build_options": bo}))
        data.write_text(json.dumps(make_data_json(df)))
        dr.ServerAppBuilder(str(spec), str(data)).build(str(app))
        ms = importlib.util.spec_from_file_location(f"_bd_{tag}", str(app))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)

        src = next(s for s in _rendered_sources(doc)
                   if _has_selection_callback(s))
        # Only rows 3 and 4 survive dropna; selecting both must give
        # mean(11, 13) = 12.00, not mean of rows 0 and 1 (99.00).
        src.selected.indices = [0, 1]
        text = _kpi_text(doc)
        assert "12.00" in text, text
        assert "99.00" not in text
