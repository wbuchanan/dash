"""test_kpi_brush.py — ``update(brush)`` must actually update on a brush.

``dash.sthlp`` documents three KPI update modes and, in its standalone-vs-
server comparison table, says brush updating works in standalone HTML:

    :427  KPI recomputation on filter    Yes (JS aggregation)  Yes
    :428  Histogram recompute on filter  heights; bins marked  heights and bins
    :429  Fit-line recompute on filter   No; marked            Yes
          (lfit, qfit since WP-31 F1a; lowess since F1c)
    :430  Brush/lasso KPI update         Yes                   Yes

Lines 428-429 show the table is written to admit standalone limitations
honestly; line 430 was the false cell.

Measured before the fix, ``update(brush)`` was **worse than unimplemented**:

  * no selection callback was ever created — nothing is attached to any
    source's ``selected`` property, so a brush can change nothing;
  * the mode additionally *excluded* the KPI from the filter callback
    (``_kdef.get("update") not in ("filter", "both")`` → ``continue``), so a
    ``update(brush)`` card was frozen at its initial value forever;
  * the KPI's variable was not even added to the linked source, so there was
    no column to compute from.

``dash.ado`` accepts ``brush`` without a warning and ships it into the
renderer's JSON, and server mode already implements exactly this, with the
same three-valued test and a passing test. Documenting the option away would
mean describing an option that dash still accepts and that has no valid use in
the default output mode, so the honest fix is to implement it.

The arithmetic must not be duplicated. ``_FILTER_JS`` carries Stata's
percentile rule, the date-valued-statistic branch and the ``%9.0g`` general
format, and a second copy would drift — exactly the failure that
``test_kpi_values.py`` exists to prevent. Both paths call one function.
"""
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json


def _df(n=20):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
    })


_PLOTS = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}]


def _render(*, update, var="mpg", filters=None, link=""):
    spec = make_spec(_PLOTS)
    spec["kpis"] = [{"name": "k1", "stat": "mean", "var": var,
                     "title": "T", "fmt": "%9.4f", "update": update}]
    spec["build_options"]["registry"] = "k1 g1"
    if filters:
        spec["build_options"]["filters"] = filters
    if link:
        spec["build_options"]["link"] = link
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df()), f)
    dr = DashRenderer(sp, dp, op)
    out = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return out, dr


def _selection_callbacks(dr):
    """``[(event, CustomJS)]``: every callback on the selection of every
    source the renderer drew from, each source once.

    This counted the KEYS of ``js_property_callbacks'' -- the events -- so
    a callback on the wrong event counted as one: measured 24sep2026, the
    ``> 0'' checks below passed with the brush callback attached to
    ``line_indices'', which a box or lasso selection of markers never
    changes, so no card followed a brush."""
    out, seen = [], set()
    for src in dr.sources.values():
        if id(src) in seen:
            continue
        seen.add(id(src))
        sel = getattr(src, "selected", None)
        for event, cbs in (getattr(sel, "js_property_callbacks", {})
                           or {}).items():
            for cb in (cbs if isinstance(cbs, list) else [cbs]):
                out.append((event, cb))
    return out


def _n_selection_callbacks(dr):
    return len(_selection_callbacks(dr))


def _brush_kpis(dr):
    """``[(event, [KPI names in the callback's configuration])]``."""
    return [(event, [k["name"] for k in json.loads(cb.args["kpi_config_json"])])
            for event, cb in _selection_callbacks(dr)]


_RANGE_FILTER = [{"varname": "weight", "type": "range", "exclude": [],
                  "label": ""}]


class TestABrushKpiCanActuallyRecompute:

    def test_a_selection_callback_is_attached(self):
        """One callback, on the selection's indices, recomputing k1.  (It
        was ``> 0'' of the events: see _selection_callbacks.)"""
        _, dr = _render(update="brush")
        assert _brush_kpis(dr) == [("change:indices", ["k1"])], (
            "update(brush) attaches no selection callback, so the card can "
            "never recompute: %s" % _brush_kpis(dr)
        )

    def test_both_gets_a_selection_callback_too(self):
        _, dr = _render(update="both", filters=_RANGE_FILTER)
        assert _brush_kpis(dr) == [("change:indices", ["k1"])], _brush_kpis(dr)

    def test_both_is_still_in_the_filter_callback(self):
        """The fix must not trade one mode for the other."""
        _, dr = _render(update="both", filters=_RANGE_FILTER)
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert [c["name"] for c in cfg] == ["k1"], cfg

    def test_filter_only_gets_no_selection_callback(self):
        """A dashboard with no brush KPI must be unchanged."""
        _, dr = _render(update="filter", filters=_RANGE_FILTER)
        assert _n_selection_callbacks(dr) == 0

    def test_a_brush_kpi_is_not_silently_frozen(self):
        """The user-visible harm: it updated on nothing at all.

        update(brush) removed the KPI from the filter callback AND attached
        no selection callback, so both counts were zero.

        ``n_filter + n_brush > 0'' passed with the brush callback on an
        event a brush never changes (see _selection_callbacks).  The card
        recomputes on a brush, and -- update(brush), not both -- not on a
        filter move.
        """
        _, dr = _render(update="brush", filters=_RANGE_FILTER)
        n_filter = len(json.loads(
            dr.filter_callbacks[0].args["kpi_config_json"]))
        assert n_filter == 0, n_filter
        assert _brush_kpis(dr) == [("change:indices", ["k1"])], (
            "the card recomputes on neither filters nor brushing: %s"
            % _brush_kpis(dr)
        )

    def test_the_variable_reaches_the_brushed_source(self):
        """A KPI on a variable no graph plots still needs its column."""
        _, dr = _render(update="brush", var="price", link="g1")
        assert any("price" in src.data for src in dr.sources.values()), (
            "the KPI's variable was never added to a source, so the "
            "recompute finds no column and silently does nothing"
        )


class TestTheArithmeticIsNotDuplicated:
    """A second copy of Stata's percentile rule would drift from the first."""

    def test_both_paths_call_one_recompute_function(self):
        assert "dash_apply_kpis" in dash_render._FILTER_JS
        assert "dash_apply_kpis" in dash_render._BRUSH_JS

    @pytest.mark.parametrize("marker", ["function dash_pctl", "'skewness'"])
    def test_the_statistic_is_defined_exactly_once(self, marker):
        both = dash_render._FILTER_JS + dash_render._BRUSH_JS
        assert both.count(marker) == 1, (
            f"{marker!r} appears {both.count(marker)} times across the two "
            f"JS constants; a second copy will drift from _stata_percentile"
        )


# The empty-selection fallback -- no selection means all rows, not no rows,
# as the server path does -- is held by
# TestTheShippedBrushJsActuallyComputes::test_clearing_the_selection_restores_every_row,
# which runs the shipped brush code with nothing selected.  The source-text
# test that stood here (TestTheEmptySelectionFallback::
# test_the_brush_js_falls_back_to_every_row: "length === 0" in _BRUSH_JS) is
# removed.  Measured 24sep2026: with the fallback deleted both failed, and
# with it disabled but its text left in place (`if (idx.length === 0 &&
# false)') the text test passed and the running one failed.


class TestTheDocumentedTableIsNowTrue:

    def test_the_help_still_claims_standalone_brush_support(self):
        """If someone later documents it away, this fails and asks why.

        A structural guard over dash.sthlp's text, which is what it is
        about.  It checked only that the row's label was there, so the row
        could say No for the saved page and pass: measured 24sep2026 with
        the saved page's cell set to No.  It now reads the row's two cells,
        under the header that says which column is which.  That the claim is
        true -- a saved page's card follows a brush -- is
        TestTheShippedBrushJsActuallyComputes here, and, against Stata's
        number, test_kpi_values.py's TestBrushUpdateIsRealOrDocumentedAsAbsent.
        """
        path = os.path.join(_HERE, "..", "dash.sthlp")
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [line.strip() for line in fh]
        assert ("{col 5}{it:Feature}{col 38}{it:Saved page}"
                "{col 59}{it:Served app}") in lines, (
            "the comparison table's header no longer puts the saved page in "
            "column 38")
        rows = [line for line in lines if "Brush/lasso KPI update" in line]
        assert rows == ["{col 5}Brush/lasso KPI update{col 38}Yes{col 59}Yes"], (
            "the comparison table no longer says brushing updates a KPI "
            "card on the saved page and in the served app: %s" % rows
        )


class TestTheShippedBrushJsActuallyComputes:
    """Run the code users receive, not a transliteration of it."""

    @staticmethod
    def _run(cfg_entry, rows, varname, indices):
        import shutil
        import subprocess

        node = shutil.which("node")
        if node is None:
            pytest.skip("node is not installed")
        js = dash_render._FILTER_JS
        helpers = js[js.index("// ---- KPI recompute, shared by"):
                     js.index("dash_apply_kpis(new_data,")]
        pctl = js[js.index("function dash_pctl"):
                  js.index("// agg_sources is a Bokeh model list")]
        payload = {
            "__dash_row__": [int(r) for r, _ in rows],
            varname: [float(v) for _, v in rows],
        }
        harness = (
            # The Stata-format writer the card calls (WP-28 section 11,
            # GAPS2 E1), which the page prepends to its callbacks.
            dash_render._DASH_FMT_JS
            + pctl
            + '\nconst ROW_ID = "__dash_row__";\n'
            + helpers
            + "\nconst brush_source = {data: " + json.dumps(payload) + "};"
            + "\nconst cb_obj = {indices: " + json.dumps(indices) + "};"
            + "\nconst kpi_config = [" + json.dumps(cfg_entry) + "];"
            + "\nlet captured = null;"
            + "\nconst kpi_divs = [{set text(v) { captured = v; }}];"
            + dash_render._BRUSH_JS
            + "\nprocess.stdout.write(captured === null ? 'NONE' : captured);"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                          delete=False) as fh:
            fh.write(harness)
            path = fh.name
        try:
            res = subprocess.run([node, path], capture_output=True,
                                 text=True, timeout=60)
            assert res.returncode == 0, (
                f"the shipped brush callback failed under node:\n"
                f"{res.stderr[:1500]}"
            )
            return res.stdout
        finally:
            os.unlink(path)

    @staticmethod
    def _cfg(dr):
        for src in dr.sources.values():
            for cb in (getattr(src.selected, "js_property_callbacks", {})
                       or {}).values():
                for c in (cb if isinstance(cb, list) else [cb]):
                    return json.loads(c.args["kpi_config_json"])[0]
        raise AssertionError("no brush callback was attached")

    def test_a_selection_gives_the_mean_of_the_selected_rows(self):
        _, dr = _render(update="brush")
        cfg = self._cfg(dr)
        df = _df()
        rows = list(enumerate(df["mpg"].tolist()))
        picked = [0, 1, 2, 3]
        want = float(df["mpg"].iloc[picked].mean())
        out = self._run(cfg, rows, "mpg", picked)
        assert f"{want:.4f}" in out, (
            f"brushing four rows should show {want:.4f}; card read: "
            f"{out[:200]}"
        )

    def test_clearing_the_selection_restores_every_row(self):
        """The fallback the server path uses; blanking the card is wrong."""
        _, dr = _render(update="brush")
        cfg = self._cfg(dr)
        df = _df()
        rows = list(enumerate(df["mpg"].tolist()))
        want = float(df["mpg"].mean())
        out = self._run(cfg, rows, "mpg", [])
        assert f"{want:.4f}" in out, (
            f"clearing a selection should restore the unbrushed "
            f"{want:.4f}; card read: {out[:200]}"
        )

    def test_the_title_survives_the_rebuild(self):
        """The rebuilt card is the card the page opened with, but for its
        number.  ``"T" in out'' -- the title is T -- held with the title in
        the subtitle's place: measured 24sep2026 with the rebuild writing
        each into the other's slot."""
        _, dr = _render(update="brush")
        out = self._run(self._cfg(dr), list(enumerate(_df()["mpg"])), "mpg",
                        [0, 1])
        [card] = [d.text for d in dr.kpi_divs.values()]
        value = r'(id="kpi_val_k1"[^>]*>)[^<]*<'
        assert re.subn(value, r"\1<", out) == (re.sub(value, r"\1<", card), 1), (
            out, card)
        assert '>T</div><div id="kpi_val_k1"' in out, out
