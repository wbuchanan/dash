"""A user variable named like a derived key reaches hover() and mlabel()
(WP-31 G3).

A mapper that rebuilds its source names its own columns ``x``, ``y``,
``top``, ``count`` ...; ``GlyphMapper._carry_cols`` skipped a carried
column whose name was already taken, so ``dropline mpg weight, hover(x)``
with a user variable ``x`` showed weight's values as ``x`` (GAPS3 G3).  The
user's column is now carried as ``__dashu_<name>`` and read from there.
"""
import copy
import os
import sys

import pytest
from bokeh.models import ColumnDataSource, HoverTool

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_grid as tg  # noqa: E402

MODES = ("saved", "served")
_ADO = os.path.join(os.path.dirname(__file__), "..", "dash.ado")


def _data():
    """by_grid's auto data with a user variable x = 1000 + _n - 1."""
    data = copy.deepcopy(tg._data())
    for i, row in enumerate(data["values"]):
        row["x"] = float(1000 + i)
    data["variableNames"].append("x")
    data["storageTypes"]["x"] = "double"
    data["variableIsString"]["x"] = False
    data["variableLabels"]["x"] = ""
    return data


def _build(mode, opts=None, go=None):
    plot = {"type": "dropline", "yvar": "mpg", "xvar": "weight",
            "options": dict(opts or {})}
    spec = tk._spec([tk._graph("g", [plot], dict(go or {}))],
                    scheme="s2color")
    roots, _n, _o = tk._build(mode, spec, data=_data())
    return [m for r in roots for m in r.references()]


class TestUserFieldShadowing:
    def test_carry_aliases_a_taken_key(self):
        src = ColumnDataSource({"x": [7.0, 8.0], "mpg": [1.0, 2.0]})
        got = dr.GlyphMapper._carry_cols(src, {"x": [1.0, 2.0]})
        assert got["x"] == [1.0, 2.0]
        assert got["__dashu_x"].tolist() == [7.0, 8.0]
        assert got["mpg"].tolist() == [1.0, 2.0]

    def test_the_plotted_column_is_not_aliased(self):
        src = ColumnDataSource({"x0": [3.0, 4.0], "y": [1.0, 2.0]})
        got = dr.GlyphMapper._carry_cols(src, {"x0": [3.0, 4.0]})
        assert "__dashu_x0" not in got
        assert dr.GlyphMapper._same_column([1.0, float("nan")],
                                           [1.0, float("nan")])
        assert not dr.GlyphMapper._same_column([1.0, 2.0], [1.0])
        assert not dr.GlyphMapper._same_column(["a"], [1.0])

    def test_user_field(self):
        assert dr.GlyphMapper._user_field("x", {"x": 1, "__dashu_x": 2}) \
            == "__dashu_x"
        assert dr.GlyphMapper._user_field("x", {"x": 1}) == "x"

    @pytest.mark.parametrize("mode", MODES)
    def test_hover_x(self, mode):
        ms = _build(mode, go={"hover": "x"})
        fields = [f for m in ms if isinstance(m, HoverTool)
                  for _l, f in (m.tooltips or [])]
        assert "@{__dashu_x}" in fields, fields
        srcs = [m for m in ms if isinstance(m, ColumnDataSource)
                and "__dashu_x" in m.data]
        assert srcs
        assert sorted(srcs[0].data["__dashu_x"])[:2] == [1000.0, 1001.0]

    @pytest.mark.parametrize("mode", MODES)
    def test_mlabel_x(self, mode):
        ms = _build(mode, opts={"mlabel": "x"})
        col = dr._DASH_MLABEL_PREFIX + "x"
        texts = [t for m in ms if isinstance(m, ColumnDataSource)
                 and col in m.data for t in m.data[col]]
        assert "1000" in texts and "2930" not in texts, texts[:5]

    def test_reserved_alias_prefix_refused_in_ado(self):
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        assert ado.count("its user-variable aliases __dashu_*") == 4


class TestCellCap:
    """A by()-faceted computed-only graph is counted by its real panels,
    not in full (WP-31 G3; dash_parse.mata's _dash_computed_cells is the
    twin, compared in Stata by test_wp31_truth.cscript U43-07)."""

    @staticmethod
    def _frame(n=1000):
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(3)
        g = np.where(np.arange(n) % 3 == 0, np.nan, np.arange(n) % 2)
        return pd.DataFrame({"y": rng.random(n), "g": g})

    @staticmethod
    def _spec(by, ptype="kdensity"):
        return {"graphs": [{"name": "h", "graph_options": {"by": by},
                            "plots": [{"type": ptype, "var": "y",
                                       "options": {}}]}],
                "kpis": [], "build_options": {}}

    def test_panel_count(self):
        df = self._frame()
        assert dr._dash_by_panel_count(df, "g", 100) == 2
        assert dr._dash_by_panel_count(df, "g, missing", 100) == 3
        assert dr._dash_by_panel_count(df, "g, total", 100) == 3
        assert dr._dash_by_panel_count(df, "g", 1) == 1
        assert dr._dash_by_panel_count(df, "nosuch", 100) is None
        assert dr._dash_by_panel_count(None, "g", 100) is None

    def test_counts_planned_rows(self):
        df = self._frame()
        rows, extra = dr._dash_embedded_cells(
            self._spec("g"), len(df), list(df.columns), {}, frame=df)
        assert rows == [] and extra == 2 * dr._DASH_COMPUTED_PLOT_CELLS
        rows, extra = dr._dash_embedded_cells(
            self._spec("g, total"), len(df), list(df.columns), {}, frame=df)
        assert rows == [] and extra == 3 * dr._DASH_COMPUTED_PLOT_CELLS

    def test_lowess_counts_each_row_once(self):
        df = self._frame()
        spec = self._spec("g")
        spec["graphs"][0]["plots"] = [{"type": "lowess", "yvar": "y",
                                       "xvar": "y", "options": {}}]
        _rows, extra = dr._dash_embedded_cells(
            spec, len(df), list(df.columns), {}, frame=df)
        assert extra == 2 * len(df)

    def test_no_frame_counts_in_full(self):
        df = self._frame()
        rows, _extra = dr._dash_embedded_cells(
            self._spec("g"), len(df), list(df.columns), {})
        assert "y" in rows
