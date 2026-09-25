"""Server mode ignored most of the options that were passed to it.

`dash serve` now forwards the whole build surface (test_serve_options.py),
but forwarding is only half the job. The generated app read exactly two keys
out of ``build_options`` — ``link`` and ``title`` — and derived its grid from
``len(all_names)`` alone. Measured on two apps whose specs differed only in
``layout``, ``tabs``, ``filter_position``, ``subtitle``, ``theme`` or
``scheme``: the generated **code** was byte-identical, and the only change
anywhere in the file was the base64 spec blob the app decodes and then does
not consult.

So in server mode:

* ``layout(2 1)`` drew the same grid as ``layout(auto)``
* ``tabs()`` produced no tab strip
* ``filterposition(left)`` put the filters on top
* ``subtitle()`` was drawn nowhere
* ``scheme()`` and ``theme()`` changed no colour

all with rc 0 and no message. The options were accepted, documented, and
discarded.
"""
import importlib.util
import itertools
import json
import os
import sys
import tempfile

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Column, Div, Row, Tabs

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

_DEFAULT_BO = {
    "layout": "auto", "link": "", "filter": "", "theme": "", "scheme": "",
    "session_scheme": "stcolor", "title": "", "subtitle": "",
    "registry": "", "tabs": "", "filter_position": "top",
    "level": "95", "formats": {},
}


def _graph(name, ptype="scatter"):
    return {"name": name,
            "graph_options": {"name": name},
            "plots": [{"type": ptype, "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "options": {}}


_SEQ = itertools.count()


def _make_doc(tmp_path, build_options, n_graphs=4, kpis=None):
    """Build a server app from a spec and run its make_document().

    Each app gets its own filename.  Two builds sharing one path defeat the
    import system: `layout(4 1)' and `layout(1 4)' produce files of identical
    SIZE, and written in the same second they also share an mtime, so the
    second import silently replayed the first one's __pycache__ entry and the
    comparison passed on the same document twice.
    """
    tag = next(_SEQ)
    names = [f"g{i + 1}" for i in range(n_graphs)]
    kpis = kpis or []
    bo = dict(_DEFAULT_BO)
    bo.update(build_options)
    if not bo["registry"]:
        bo["registry"] = " ".join(names + [k["name"] for k in kpis])

    spec = tmp_path / f"spec_{tag}.json"
    data = tmp_path / f"data_{tag}.json"
    app = tmp_path / f"app_{tag}.py"
    spec.write_text(json.dumps({"graphs": [_graph(n) for n in names],
                                "kpis": kpis, "build_options": bo}))
    data.write_text(json.dumps(make_data_json(_DF)))

    dr.ServerAppBuilder(str(spec), str(data)).build(str(app))
    mspec = importlib.util.spec_from_file_location(f"_dash_app_{tag}", str(app))
    mod = importlib.util.module_from_spec(mspec)
    mspec.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc


def _walk(model, seen=None):
    """Every model reachable from a document root."""
    seen = seen if seen is not None else set()
    if id(model) in seen:
        return
    seen.add(id(model))
    yield model
    for attr in ("children", "tabs", "child"):
        kids = getattr(model, attr, None)
        if kids is None:
            continue
        if not isinstance(kids, (list, tuple)):
            kids = [kids]
        for k in kids:
            if k is None:
                continue
            yield from _walk(k, seen)


def _find(doc, cls):
    out = []
    for root in doc.roots:
        out.extend(m for m in _walk(root) if isinstance(m, cls))
    return out


def _grid_shape(doc):
    """(rows, cols) of the first gridplot found, by its children's coords."""
    from bokeh.models import GridPlot
    grids = _find(doc, GridPlot)
    assert grids, "no GridPlot in the served document"
    coords = [(c[1], c[2]) for c in grids[0].children]
    return (max(r for r, _ in coords) + 1, max(c for _, c in coords) + 1)


class TestLayout:
    def test_layout_n_by_m_is_honoured(self, tmp_path):
        """layout() is rows then columns, as the standalone path reads it."""
        doc = _make_doc(tmp_path, {"layout": "1 4"}, n_graphs=4)
        assert _grid_shape(doc) == (1, 4)
        doc = _make_doc(tmp_path, {"layout": "4 1"}, n_graphs=4)
        assert _grid_shape(doc) == (4, 1)

    def test_a_different_layout_gives_a_different_grid(self, tmp_path):
        wide = _make_doc(tmp_path, {"layout": "4 1"}, n_graphs=4)
        tall = _make_doc(tmp_path, {"layout": "1 4"}, n_graphs=4)
        assert _grid_shape(wide) != _grid_shape(tall)

    def test_auto_still_squares_the_grid(self, tmp_path):
        doc = _make_doc(tmp_path, {"layout": "auto"}, n_graphs=4)
        assert _grid_shape(doc) == (2, 2)

    def test_a_malformed_layout_falls_back_to_auto(self, tmp_path):
        doc = _make_doc(tmp_path, {"layout": "not a grid"}, n_graphs=4)
        assert _grid_shape(doc) == (2, 2)


class TestTabs:
    def test_tabs_produce_a_tab_strip(self, tmp_path):
        doc = _make_doc(tmp_path, {"tabs": "First: g1 g2 / Second: g3 g4"},
                        n_graphs=4)
        tabs = _find(doc, Tabs)
        assert tabs, "tabs() produced no Tabs widget in server mode"
        assert [p.title for p in tabs[0].tabs] == ["First", "Second"]

    def test_no_tabs_option_means_no_tab_strip(self, tmp_path):
        doc = _make_doc(tmp_path, {}, n_graphs=4)
        assert not _find(doc, Tabs)

    def test_a_name_that_is_not_registered_is_dropped(self, tmp_path):
        """Only registered names may be placed — same rule as standalone."""
        doc = _make_doc(tmp_path, {"tabs": "Only: g1 no_such_graph"},
                        n_graphs=4)
        tabs = _find(doc, Tabs)
        assert tabs and [p.title for p in tabs[0].tabs] == ["Only"]


def _has_sidebar(doc):
    """A fixed-width column of widgets beside the content, as standalone builds."""
    return any(
        isinstance(m, Column)
        and m.width_policy == "fixed"
        and m.width == dr._SIDEBAR_WIDTH_PX
        for m in _find(doc, Column)
    )


class TestFilterPosition:
    def test_filterposition_left_builds_a_sidebar(self, tmp_path):
        """The same fixed-width column the standalone path builds.

        A bare `assert some Row exists' passes either way -- the top bar is
        itself a row -- so this asserts the sidebar's own shape.
        """
        doc = _make_doc(tmp_path,
                        {"filter": "foreign, type(dropdown)",
                         "filter_position": "left"}, n_graphs=2)
        assert _has_sidebar(doc), (
            "filterposition(left) produced no sidebar in server mode"
        )

    def test_filterposition_top_does_not(self, tmp_path):
        doc = _make_doc(tmp_path,
                        {"filter": "foreign, type(dropdown)",
                         "filter_position": "top"}, n_graphs=2)
        assert not _has_sidebar(doc)
        assert _find(doc, Row), "the top filter bar is still a row"


class TestSubtitle:
    def test_subtitle_is_rendered(self, tmp_path):
        doc = _make_doc(tmp_path, {"title": "T", "subtitle": "S"}, n_graphs=2)
        text = " ".join(d.text for d in _find(doc, Div))
        assert "S" in text, "subtitle() is drawn nowhere in server mode"

    def test_subtitle_is_escaped(self, tmp_path):
        doc = _make_doc(tmp_path,
                        {"title": "T", "subtitle": "<script>alert(1)</script>"},
                        n_graphs=2)
        text = " ".join(d.text for d in _find(doc, Div))
        assert "<script>" not in text
