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
        # Flipped (WP-35 DT-19): the four r(110) refusals named the alias
        # prefix; refusing a __dash variable was wrong because twoway draws
        # it.  The alias is now formed from the spec's prefix, so a user
        # variable __dashu_x is data when the data hold it.
        assert ado.count("its user-variable aliases __dashu_*") == 0
        assert dr._DASH_USER_ALIAS_PREFIX == dr._DASH_RP + "u_" == "__dashu_"
        m = dr._dash_module_for({"_dash_prefix": "__dsh1_"})
        assert m._DASH_USER_ALIAS_PREFIX == "__dsh1_u_"


class TestCellCap:
    """A by()-faceted computed-only graph was counted by its real panels
    for the cells limit (WP-31 G3).  The maintainer removed the size caps
    (P4-3, WP-33 33-15), and the count with them: each old pin is a row."""

    @pytest.mark.parametrize("old, names", [
        ("test_panel_count", ("_dash_by_panel_count",)),
        ("test_counts_planned_rows",
         ("_dash_embedded_cells", "_DASH_COMPUTED_PLOT_CELLS")),
        ("test_lowess_counts_each_row_once", ("_dash_embedded_cells",
                                              "_dash_graph_computed_cells")),
        ("test_no_frame_counts_in_full", ("_dash_embedded_cells",)),
    ], ids=lambda v: v if isinstance(v, str) else None)
    def test_the_count_code_is_gone(self, old, names):
        # Flipped: <old> pinned the panel count the cells limit read; the
        # maintainer removed the size caps (P4-3), so its names are gone.
        for name in names:
            assert not hasattr(dr, name), (old, name)
