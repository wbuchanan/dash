"""GAPS2 G3 counted what a saved page embeds, for the cells limit; the
maintainer removed the cells and bytes limits (P4-3, WP-33 33-15), and with
them the count.

The count (``_dash_embedded_cells`` and its helpers in dash_render.py,
``_dash_computed_cells`` and its twins in dash_parse.mata, and
``_dash_cell_cap`` in dash.ado) existed only so the cap could be fair to a
graph made only of computed layers.  With no cap a dashboard of any size is
drawn; this file pins that the count is gone (``TestNoSizeCap``), that both
modes draw what the cap refused (``TestBothModes``), and the parts G3 left
that stay: the size note, the computed-only types and the limits table.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
def _plot(ptype, **fields):
    p = {"type": ptype, "options": {}}
    p.update(fields)
    return p


#: The pins whose whole subject was the removed count (WP-33 33-15,
#: D-33-15.e): each old test name with the dash_render names it pinned.
_COUNT = ("_dash_embedded_cells",)
_CAP_CODE_GONE = [
    ("TestTheCount::"
     "test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused",
     _COUNT + ("_dash_refuse_oversized",)),
    ("TestTheCount::test_touched_graphs_count_their_rows", _COUNT),
    ("TestTheCount::"
     "test_an_untouched_row_drawing_graph_beside_a_computed_one_still_"
     "counts_its_own", _COUNT),
    ("TestTheCount::test_a_filter_that_excludes_the_graph_does_not_touch_it",
     _COUNT),
    ("TestTheCount::test_width_discrete_lowess_and_by_are_counted_"
     "conservatively", _COUNT + ("_DASH_COMPUTED_PLOT_CELLS",)),
    ("TestTheCount::test_kpi_and_filter_variables_always_count", _COUNT),
    ("TestTheCount::test_a_hover_only_variable_counts_on_a_graph_that_"
     "shows_it", _COUNT),
    ("TestTheCount::test_a_hover_variable_on_a_mixed_graph_counts", _COUNT),
    ("TestTheCount::test_a_hover_variable_on_a_computed_only_graph_does_"
     "not_count", _COUNT),
    ("TestTheCount::test_a_hover_variable_on_a_literal_only_graph_does_"
     "not_count", _COUNT),
    ("TestTheCount::test_a_hover_name_not_in_the_columns_is_not_counted",
     _COUNT),
    ("TestTheCount::test_csv_counts_a_hover_variable_whatever_the_graph",
     _COUNT),
    ("TestTheHoverColumns::test_which_graphs_can_show_hover",
     ("_dash_hover_shown",)),
    ("TestTheHoverColumns::test_the_names_only_an_unshowing_hover_gives",
     ("_dash_hover_unembedded",)),
    ("TestTheRefusalAndTheNote::test_the_message_names_the_computed_values",
     ("_dash_refuse_oversized",)),
    ("TestTheTwoLanguagesAgree::test_the_constant_bounds_every_computed_layer",
     ("_DASH_COMPUTED_PLOT_CELLS",)),
]


class TestNoSizeCap:

    @pytest.mark.parametrize("old, names", _CAP_CODE_GONE,
                             ids=[o.replace("::", ".")
                                  for o, _ in _CAP_CODE_GONE])
    def test_the_cap_code_is_gone(self, old, names):
        # Flipped: each <old> pinned the count the cells limit read; the
        # maintainer removed the size caps (P4-3), so its names are gone.
        for name in names:
            assert not hasattr(dr, name), (old, name)
        for name in ("_dash_graph_computed_cells", "_dash_by_panel_count",
                     "_dash_graph_qual_cols", "_dash_text_bytes",
                     "_dash_refuse_overbytes"):
            assert not hasattr(dr, name), name


class TestTheRefusalAndTheNote:

    def test_the_note_reports_embedded_bytes(self, recwarn):
        dr._report_dataset_shape(6_000_000, 0, "dashboard", extra=268)
        assert not recwarn.list

        with pytest.warns(UserWarning, match=r"roughly 288 MB"):
            dr._report_dataset_shape(6_000_000, 2, "dashboard")


class TestBothModes:
    """A small frame under the old lowered cells limit, 22: the saved
    histogram was drawn, the saved scatter (24 x 2 = 48 values) and the
    served histogram refused.  With no size cap (P4-3) all three build."""

    _N = 24
    _LIM = {"cells": 22}

    def test_both_modes_build_the_histogram_and_the_scatter(
            self, monkeypatch):
        # Flipped: test_the_saved_page_builds_the_histogram_the_served_app_
        # still_refuses -> test_both_modes_build_the_histogram_and_the_
        # scatter -- the refusals were wrong because the maintainer removed
        # the size caps (P4-3).
        import pandas as pd
        df = pd.DataFrame({
            "mpg": [float(i % 7 + 10) for i in range(self._N)],
            "weight": [float(2000 + 10 * i) for i in range(self._N)],
        })
        monkeypatch.setattr(tp, "_DF", df)
        bo = {"limits": self._LIM}

        hist_spec = tp._spec(
            plots=[_plot("histogram", var="mpg")], build_options=bo)
        r, _w = tp._standalone(hist_spec)
        assert "g1" in r.figures

        scatter_spec = tp._spec(
            plots=[_plot("scatter", yvar="mpg", xvar="weight")],
            build_options=bo)
        r2, _w2 = tp._standalone(scatter_spec)
        assert "g1" in r2.figures

        assert tp._served(hist_spec) is not None


class TestTheTwoLanguagesAgree:

    def test_the_computed_types_and_the_constant_are_the_same_in_dash_ado_and_mata(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        import re
        univar = re.search(
            r'c_local _pt_univar\s+"([^"]*)"', ado).group(1).split()
        onefit = re.search(
            r'c_local _pt_onefit\s+"([^"]*)"', ado).group(1).split()
        assert set(univar) | set(onefit) == dr._DASH_COMPUTED_ONLY_TYPES

        with open(os.path.join(_ROOT, "dash_parse.mata"),
                  encoding="utf-8") as fh:
            mata = fh.read()
        m = re.search(
            r"_dash_computed_plot_cells\(\)\s*\{\s*return\((\d+)\)", mata)
        # Flipped (WP-33 33-15): the bound on a computed layer's drawn
        # values was only for the cells limit, which the maintainer removed
        # (P4-3); both copies of it are gone.
        assert m is None, "_dash_computed_plot_cells() is still in the Mata"
        assert not hasattr(dr, "_DASH_COMPUTED_PLOT_CELLS")

    def test_the_types_hover_cannot_reach_agree(self):
        """WP-29 P0.10 (review A1): the types whose layers cannot show a
        hover() variable are one rule -- dash.ado's _pt_univar, _pt_onefit
        and _pt_literal (read by _dash_spec_types_in on both routes), the
        renderer's _DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES, and _dash_note_hover_unreached's literal
        tables."""
        import inspect
        import re
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        words = set()
        # WP-31 B4b: _pt_contour too -- a contour's polygons are no
        # observations, though its rows are embedded (not computed-only).
        for fam in ("_pt_univar", "_pt_onefit", "_pt_contour",
                    "_pt_literal"):
            m = re.search(r'c_local ' + fam + r'\s+"([^"]*)"', ado)
            assert m is not None, fam
            words |= set(m.group(1).split())
        python = (dr._DASH_COMPUTED_ONLY_TYPES | dr._DASH_LITERAL_TYPES
                  | dr._DASH_CONTOUR_TYPES)
        assert words == set(python)
        src = inspect.getsource(dr._dash_note_hover_unreached)
        start = src.index("computed = frozenset({")
        lit = src.index("literal = frozenset({", start)
        end = src.index("})", lit)
        note = set(re.findall(r'"([a-z]+)"', src[start:end]))
        assert note == words

    def test_the_limits_table_is_untouched(self):
        """Control: repeats test_resource_limits.py's own equality
        assertion (test_dash_ado_has_the_same_defaults_and_ceilings) so a
        regression here is caught beside G3's changes."""
        import re
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        start = ado.index("program define _dash_limit_table")
        body = ado[start:ado.index("\nend", start)]
        rows = dict((k, (int(d), int(c))) for k, d, c in
                    re.findall(r"(\w+)=(\d+),(\d+)", body))
        assert rows == {k: (v[0], v[1]) for k, v in dr._DASH_LIMITS.items()}
