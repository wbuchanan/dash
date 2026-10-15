"""GAPS2 G3: the cells limit counts what the saved page embeds.

The limits exist so nothing "can grow without bound" (dash.sthlp), but the
count used to be every exported variable times every observation, whatever
the page would actually hold. A graph made only of computed layers --
histogram, kdensity, a fit or a smoother -- draws its own bounded output
(bars, a curve, a line), not one glyph per row; GAPS2 measured that
``dash histogram x`` on 5,000,001 observations was refused by default, and
nothing could be drawn past 20,000,000, although the page itself stayed a
few megabytes.

This file pins the renderer's half of the fix: ``_dash_embedded_cells``
decides, from the parsed spec alone (no frame is ever built here -- row
counts are plain numbers, columns are names, exactly how the renderer
calls it with ``self.df.shape[0]`` and ``list(self.df.columns)``), which
columns a saved page's row-drawing layers need and how many cells its
untouched computed-only graphs draw; ``_dash_refuse_oversized`` and
``_report_dataset_shape`` grow an ``extra`` keyword for that count. dash.ado's
side (the Mata accounting and ``_dash_cell_cap``) is pinned by
``test/test_adversarial.cscript`` DL-01..DL-06 and by
``TestTheTwoLanguagesAgree`` below, which reads both files as text.
"""
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
_LIMITS = dr._dash_limits({})


# ---------------------------------------------------------------------------
# Spec builders -- no DataFrame anywhere in this file except TestBothModes.
# ---------------------------------------------------------------------------

def _plot(ptype, **fields):
    p = {"type": ptype, "options": {}}
    p.update(fields)
    return p


def _graph(name, plots, graph_options=None, **extra):
    go = dict(graph_options or {})
    go.setdefault("name", name)
    g = {"name": name, "graph_options": go, "plots": plots}
    g.update(extra)
    return g


def _kpi(name, var, qual_col=""):
    return {"name": name, "var": var, "stat": "mean", "qual_col": qual_col}


def _master(graphs, kpis=None, filter="", link="", csv=False):
    return {
        "graphs": list(graphs),
        "kpis": list(kpis or []),
        "build_options": {
            "filter": filter, "link": link,
            "csv": "1" if csv else "0",
        },
    }


def _bins(n):
    """Stata's default histogram bin count for n observations."""
    if n <= 0:
        return 1
    return max(1, math.floor(min(math.sqrt(n), 10 * math.log10(n))))


class TestTheCount:

    def test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused(self):
        n = 6_000_000
        hist_spec = _master([_graph("g1", [_plot("histogram", var="x")])])
        scatter_spec = _master(
            [_graph("g1", [_plot("scatter", yvar="x", xvar="y")])])

        row_cols, extra = dr._dash_embedded_cells(hist_spec, n, ["x"],
                                                    _LIMITS)
        want_bins = _bins(n)
        assert want_bins == 67, want_bins   # pinned so the test itself is right
        assert row_cols == []
        assert extra == want_bins * 4 == 268
        dr._dash_refuse_oversized(n, len(row_cols), _LIMITS, "dashboard",
                                  extra=extra)   # must not raise

        row_cols2, extra2 = dr._dash_embedded_cells(
            scatter_spec, n, ["x", "y"], _LIMITS)
        assert sorted(row_cols2) == ["x", "y"]
        assert extra2 == 0
        with pytest.raises(dr.DashLimitError, match="12,000,000"):
            dr._dash_refuse_oversized(n, len(row_cols2), _LIMITS,
                                      "dashboard", extra=extra2)

    @pytest.mark.parametrize("reason", ["filter", "link", "csv", "hover"])
    def test_touched_graphs_count_their_rows(self, reason):
        """A filter, link(), csv or hover() that reaches the lone
        histogram graph makes it count its own rows, not its bars."""
        n = 100
        kw = {}
        if reason == "filter":
            kw["filter"] = "x, type(range)"
        elif reason == "link":
            kw["link"] = "_all"
        elif reason == "csv":
            kw["csv"] = True
        graph_options = {"hover": "x"} if reason == "hover" else None
        spec = _master(
            [_graph("g1", [_plot("histogram", var="x")], graph_options)],
            **kw)
        row_cols, extra = dr._dash_embedded_cells(spec, n, ["x"], _LIMITS)
        assert row_cols == ["x"]
        assert extra == 0

    def test_an_untouched_row_drawing_graph_beside_a_computed_one_still_counts_its_own(self):
        """Adding an unrelated row-drawing graph must not exclude the
        computed-only graph's rows from the accounting, nor pull the
        computed-only graph's own column in: each graph's touched status
        is its own (BR-08.4)."""
        n = 100
        spec = _master([
            _graph("g1", [_plot("histogram", var="x")]),
            _graph("g2", [_plot("scatter", yvar="a", xvar="b")]),
        ])
        row_cols, extra = dr._dash_embedded_cells(
            spec, n, ["x", "a", "b"], _LIMITS)
        assert sorted(row_cols) == ["a", "b"]
        assert "x" not in row_cols
        assert extra == _bins(n) * 4

    def test_a_filter_that_excludes_the_graph_does_not_touch_it(self):
        """The filter's own variable still counts (BR-08.4: filter
        variables always count -- a filter widget needs its own column
        whether or not any graph currently listens to it), but excluding
        the lone histogram still keeps ITS row from being drawn in full:
        the extra (bounded, computed) count is unaffected by the filter
        variable happening to share the histogram's own name."""
        n = 100
        spec = _master(
            [_graph("g1", [_plot("histogram", var="x")])],
            filter="fv, type(range) exclude(g1)")
        row_cols, extra = dr._dash_embedded_cells(
            spec, n, ["x", "fv"], _LIMITS)
        assert row_cols == ["fv"]
        assert extra == _bins(n) * 4

    def test_width_discrete_lowess_and_by_are_counted_conservatively(self):
        n = 100
        cases = {
            "width": (_plot("histogram", var="x", options={"width": "1"}),
                      4 * n),
            "discrete": (_plot("histogram", var="x",
                                options={"discrete": "discrete"}), 4 * n),
            "bin": (_plot("histogram", var="x", options={"bin": "27"}),
                    4 * 27),
            "lowess": (_plot("lowess", yvar="x", xvar="y"), 2 * n),
            "kdensity": (_plot("kdensity", var="x"),
                        dr._DASH_COMPUTED_PLOT_CELLS),
        }
        for label, (plot, want) in cases.items():
            spec = _master([_graph("g1", [plot])])
            row_cols, extra = dr._dash_embedded_cells(
                spec, n, ["x", "y"], _LIMITS)
            assert row_cols == [], label
            assert extra == want, (label, extra, want)

        # by() is never treated as computed-only (the actual panel count
        # is not known before the export, and multiplying the generic
        # 120,000 bound by the by_groups LIMIT reads as 12,000,000 --
        # over the default cells limit for ANY dataset, however small,
        # which regressed test_help_claims_6.py's by()-faceted lpoly
        # grid): it is counted in full, as it was before this section.
        spec = _master([_graph("g1", [_plot("histogram", var="x")],
                               {"by": "g"})])
        row_cols, extra = dr._dash_embedded_cells(spec, n, ["x", "g"],
                                                    _LIMITS)
        assert sorted(row_cols) == ["g", "x"]
        assert extra == 0

    def test_kpi_and_filter_variables_always_count(self):
        n = 100
        spec = _master(
            [_graph("g1", [_plot("histogram", var="x")])],
            kpis=[_kpi("k1", "y", qual_col="__dashq1")])
        row_cols, extra = dr._dash_embedded_cells(
            spec, n, ["x", "y", "__dashq1"], _LIMITS)
        assert sorted(row_cols) == ["__dashq1", "y"]
        assert "x" not in row_cols
        assert extra == _bins(n) * 4

        # A filter variable counts even when it excludes the only graph.
        spec2 = _master(
            [_graph("g1", [_plot("histogram", var="x")])],
            filter="fv, type(range) exclude(g1)")
        row_cols2, _extra2 = dr._dash_embedded_cells(
            spec2, n, ["x", "fv"], _LIMITS)
        assert row_cols2 == ["fv"]


    # -- WP-29 P0.10: hover()'s own variables (review A1) ------------------

    def test_a_hover_only_variable_counts_on_a_graph_that_shows_it(self):
        """A variable named only in hover() is embedded, so a scatter
        that can show it counts it (base: ``(['y', 'x'], 0)``)."""
        spec = _master([_graph("g1", [_plot("scatter", yvar="y", xvar="x")],
                               {"hover": "z"})])
        assert dr._dash_embedded_cells(spec, 100, ["x", "y", "z"],
                                       _LIMITS) == (["y", "x", "z"], 0)

    def test_a_hover_variable_on_a_mixed_graph_counts(self):
        spec = _master([_graph(
            "g1", [_plot("scatter", yvar="y", xvar="x"),
                   _plot("lfit", yvar="y", xvar="x")], {"hover": "z"})])
        row_cols, _extra = dr._dash_embedded_cells(
            spec, 100, ["x", "y", "z"], _LIMITS)
        assert row_cols == ["y", "x", "z"]

    def test_a_hover_variable_on_a_computed_only_graph_does_not_count(self):
        """A1: no layer of a lone histogram can show hover()'s variable."""
        spec = _master([_graph("g1", [_plot("histogram", var="x")],
                               {"hover": "z"})])
        assert dr._dash_embedded_cells(spec, 100, ["x", "z"],
                                       _LIMITS) == (["x"], 0)

    def test_a_hover_variable_on_a_literal_only_graph_does_not_count(self):
        for ptype in ("scatteri", "function"):
            spec = _master([_graph("g1", [_plot(ptype)], {"hover": "z"})])
            assert dr._dash_embedded_cells(spec, 100, ["z"],
                                           _LIMITS) == ([], 0), ptype

    def test_a_hover_name_not_in_the_columns_is_not_counted(self):
        spec = _master([_graph("g1", [_plot("scatter", yvar="y", xvar="x")],
                               {"hover": "nosuch"})])
        row_cols, _extra = dr._dash_embedded_cells(
            spec, 100, ["x", "y"], _LIMITS)
        assert "nosuch" not in row_cols

    def test_csv_counts_a_hover_variable_whatever_the_graph(self):
        spec = _master([_graph("g1", [_plot("histogram", var="x")],
                               {"hover": "z"})], csv=True)
        row_cols, _extra = dr._dash_embedded_cells(
            spec, 100, ["x", "y", "z"], _LIMITS)
        assert sorted(row_cols) == ["x", "y", "z"]


class TestTheHoverColumns:
    """WP-29 P0.10 (review A1): which graphs can show hover()'s
    variables, and which names only an unshowing hover() gives."""

    def test_which_graphs_can_show_hover(self):
        def g(*types):
            return _graph("g1", [_plot(t) for t in types])
        assert dr._dash_hover_shown(g("scatter")) is True
        assert dr._dash_hover_shown(g("histogram")) is False
        assert dr._dash_hover_shown(g("scatteri")) is False
        assert dr._dash_hover_shown(g("function")) is False
        assert dr._dash_hover_shown(g("scatter", "lfit")) is True
        assert dr._dash_hover_shown(g("lfit", "kdensity")) is False
        assert dr._dash_hover_shown(g()) is True
        # Exact match, as Mata's _dash_spec_types_in matches it.
        assert dr._dash_hover_shown(
            _graph("g1", [{"type": "Histogram"}])) is True

    def test_the_names_only_an_unshowing_hover_gives(self):
        def hist(name="g1", hover="make", var="price"):
            return _graph(name, [_plot("histogram", var=var)],
                          {"hover": hover})
        un = dr._dash_hover_unembedded
        assert un(_master([hist()])) == {"make"}
        assert un(_master([hist()], csv=True)) == set()
        assert un(_master([hist()], kpis=[_kpi("k1", "make")])) == set()
        assert un(_master([hist(), _graph(
            "g2", [_plot("scatter", yvar="mpg", xvar="weight")],
            {"hover": "make"})])) == set()
        assert un(_master([hist()],
                          filter="make, type(dropdown)")) == set()
        assert un(_master([hist(hover="price")])) == set()
        assert un(_master([_graph(
            "g1", [_plot("scatter", yvar="mpg", xvar="weight")],
            {"hover": "make"})])) == set()


class TestTheRefusalAndTheNote:

    def test_the_message_names_the_computed_values(self):
        with pytest.raises(dr.DashLimitError) as exc:
            dr._dash_refuse_oversized(74, 2, {"cells": 100}, "dashboard",
                                      extra=40)
        msg = str(exc.value)
        assert "188 values (74 observations x 2 variables, and 40 " \
               "values of computed layers)" in msg

        with pytest.raises(dr.DashLimitError) as exc2:
            dr._dash_refuse_oversized(74, 0, {"cells": 30}, "dashboard",
                                      extra=40)
        assert "(the drawn output of its computed layers)" in str(
            exc2.value)

        with pytest.raises(dr.DashLimitError) as exc3:
            dr._dash_refuse_oversized(74, 0, {"cells": 30}, "server app",
                                      extra=40)
        assert ("A served app embeds every observation of every variable "
                "it uses.") in str(exc3.value)

        # Byte-identical to today's message when extra == 0 (control;
        # the same needles test_resource_limits.py pins).
        with pytest.raises(dr.DashLimitError) as exc4:
            dr._dash_refuse_oversized(51, 2, {"cells": 100}, "dashboard")
        msg4 = str(exc4.value)
        for needle in ("102 values", "51 observations x 2 variables",
                       "more than the 100",
                       "keep, drop, sample or collapse",
                       "set global dash_max_cells"):
            assert needle in msg4, (needle, msg4)
        assert "computed layers" not in msg4
        assert "server app" not in msg4

    def test_the_note_reports_embedded_bytes(self, recwarn):
        dr._report_dataset_shape(6_000_000, 0, "dashboard", extra=268)
        assert not recwarn.list

        with pytest.warns(UserWarning, match=r"roughly 288 MB"):
            dr._report_dataset_shape(6_000_000, 2, "dashboard")


class TestBothModes:
    """A small frame under a lowered cells limit: 24 rows, limit 22.
    Today: bins = max(1, floor(min(sqrt(24), 10*log10(24)))) = max(1,
    floor(min(4.899, 13.802))) = 4; 4 bins x 4 cells/bin = 16 <= 22, so
    even before the fix a plain cell-count of rows*cols (24*1=24) was
    refused although the drawn bars (16 values) would fit -- these
    numbers are chosen so the saved histogram is refused pre-fix and
    passes post-fix, and the scatter (24*2=48) is refused either way."""

    _N = 24
    _LIM = {"cells": 22}

    def test_the_saved_page_builds_the_histogram_the_served_app_still_refuses(
            self, monkeypatch):
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
        with pytest.raises(dr.DashLimitError):
            tp._standalone(scatter_spec)

        with pytest.raises(dr.DashLimitError) as exc:
            tp._served(hist_spec)
        assert "server app" in str(exc.value)


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
        assert m is not None, "_dash_computed_plot_cells() not found"
        assert int(m.group(1)) == dr._DASH_COMPUTED_PLOT_CELLS

    def test_the_types_hover_cannot_reach_agree(self):
        """WP-29 P0.10 (review A1): the types whose layers cannot show a
        hover() variable are one rule -- dash.ado's _pt_univar, _pt_onefit
        and _pt_literal (read by _dash_spec_types_in on both routes), the
        renderer's _DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES
        (_dash_hover_shown), and _dash_note_hover_unreached's literal
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

    def test_the_constant_bounds_every_computed_layer(self):
        """Re-derives the bound from dash.ado's own option caps
        (_dash_option_rules, ~1889): n=int,1,300@mspline n=int,2,10000
        bin=int,1,1000 width=pos start=num bands=int,1,200."""
        import re
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        m = re.search(
            r"n=int,1,(\d+)@mspline\s+n=int,\d+,(\d+)\s+bin=int,\d+,\d+"
            r"\s+width=pos\s+start=num\s+bands=int,\d+,(\d+)", ado)
        assert m is not None, "the option-cap line has moved or changed"
        mspline_n_cap, n_cap, bands_cap = (int(x) for x in m.groups())
        fp_grid_max = dr._FP_GRID_MAX
        fit_grid = dr._FIT_GRID
        bound = max(4 * n_cap, 4 * fp_grid_max,
                    2 * ((bands_cap - 1) * mspline_n_cap + bands_cap),
                    4 * fit_grid, 2 * 300)
        assert dr._DASH_COMPUTED_PLOT_CELLS >= bound

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
