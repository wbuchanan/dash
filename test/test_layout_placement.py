"""`layout(name:row,col)` set the grid's size and nothing else.

``_placement_map`` parses the spec correctly, and ``_compute_grid`` uses it —
to work out how many rows and columns the grid needs. Then
``_assemble_layout`` filled the cells in **registration order** and never
looked at the map again. So

    dash build, layout(s1:1,1 s2:2,2)

produced a 2x2 grid, as asked, with s1 and s2 side by side in the first row
instead of diagonally. Any spec whose order or gaps differ from registration
order was silently rearranged.

The served document has placed correctly since the server layout was written;
this is the standalone half, and the parity test now covers both.
"""
import itertools
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.models import GridPlot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()
_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0],
                    "weight": [2930.0, 3350.0, 2200.0, 1800.0]})


def _render(tmp_path, layout, names):
    tag = next(_SEQ)
    graphs = [{"name": n, "graph_options": {"name": n}, "options": {},
               "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                          "options": {}}]} for n in names]
    spec = tmp_path / f"s_{tag}.json"
    data = tmp_path / f"d_{tag}.json"
    spec.write_text(json.dumps({
        "graphs": graphs, "kpis": [],
        "build_options": {"layout": layout, "link": "", "filter": "",
                          "theme": "", "scheme": "", "session_scheme": "",
                          "title": "", "subtitle": "",
                          "registry": " ".join(names), "tabs": "",
                          "filter_position": "top", "level": "95",
                          "formats": {}}}))
    data.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(str(spec), str(data))
        r.render()
    return r


def _positions(r):
    """{graph name: (row, col)} as the grid actually lays them out."""
    fig_of = {id(f): n for n, f in r.figures.items()}
    out = {}
    seen = set()

    def walk(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    walk(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, GridPlot):
            for child in m.children:
                name = fig_of.get(id(child[0]))
                if name is not None:
                    out[name] = (child[1], child[2])
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                walk(k)

    root = getattr(r, "_last_layout_root", None)
    assert root is not None, "the renderer kept no layout root to inspect"
    walk(root)
    return out


class TestPlacementIsHonoured:
    def test_diagonal_placement(self, tmp_path):
        r = _render(tmp_path, "s1:1,1 s2:2,2", ["s1", "s2"])
        pos = _positions(r)
        assert pos, "no grid positions recovered"
        assert pos["s1"] == (0, 0)
        assert pos["s2"] == (1, 1), (
            f"s2 was placed at {pos['s2']}, not diagonally below s1"
        )

    def test_reversed_order(self, tmp_path):
        """The spec, not the registration order, decides."""
        r = _render(tmp_path, "s1:1,2 s2:1,1", ["s1", "s2"])
        pos = _positions(r)
        assert pos["s1"] == (0, 1)
        assert pos["s2"] == (0, 0)

    def test_an_unplaced_graph_fills_a_free_cell(self, tmp_path):
        r = _render(tmp_path, "s1:2,2", ["s1", "s2", "s3"])
        pos = _positions(r)
        assert pos["s1"] == (1, 1)
        assert pos["s2"] != pos["s3"]
        assert pos["s2"] != (1, 1) and pos["s3"] != (1, 1)

    def test_auto_is_unchanged(self, tmp_path):
        r = _render(tmp_path, "auto", ["s1", "s2", "s3", "s4"])
        pos = _positions(r)
        assert len(set(pos.values())) == 4

    def test_a_plain_grid_is_unchanged(self, tmp_path):
        r = _render(tmp_path, "1 4", ["s1", "s2", "s3", "s4"])
        pos = _positions(r)
        assert {p[0] for p in pos.values()} == {0}
