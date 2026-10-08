"""One test per function of ``test/js_runner.py`` (WP-28 S03, CLAUDE.md
rule 3): the shared node runner four private, per-file copies are migrated
onto (``test_saved_filter_layers.py``, ``test_filter_exclude.py``,
``test_help_claims_3.py``, ``test_statistical_helpers.py``).

GAPS2 E2 measured: "Served probe: price to [4000,5000], then foreign=1,
then price back to its full range gives g1=3, g2=5, k1=3, where the
current widgets imply 5 under either rule.  The saved page behaves the
same by construction; its multi-move sequence is unmeasured because the
node harness cannot chain moves."  DISCOVERY Q10 and Q15 answer that: "one
pytest runs node and pandas on the same columns and compares masks", and
"the node runner keeps ColumnDataSource state between calls so a sequence
can be asserted; no browser needed."

``js_runner.node()``/``requires_node`` SKIP when node is absent, naming
``DASH_NODE``; under ``DASH_STRICT=1`` (``make test``, ``make test-dev``)
that skip is a RED run (CLAUDE.md rule 3: a skip is not a pass), by
design -- not a bug in this module or its tests.

Consumers, by section, and the names each imports from ``js_runner``:
S04's ``test_display_format_writer.py`` -- ``run_js``, ``requires_node``;
S05's ``test_histogram_edge_rule.py`` -- ``run_filter_js_block``, ``NODE``
(and ``_hist`` from ``test_statistical_helpers``); S12 and S17 --
``JsSession``, ``mask_parity``.
"""
import math
import os
import re
import shutil
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (BooleanFilter, ColumnDataSource, Div, RangeSlider,
                          Select, Slider)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_filter_exclude as tfe  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_mode_parity import _DF  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


def _page(tmp_path, spec, df=None):
    """Render *spec* (and *df*, else ``tfe._DF``) to a ``DashRenderer``."""
    sp, dp = (tfe._write_inputs(tmp_path, spec, df) if df is not None
              else tfe._write_inputs(tmp_path, spec))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _widgets(r):
    """``{Bokeh widget class name: (widget, its filter callback)}``."""
    return {type(w).__name__: (w, cb)
            for w, cb in zip(r.filter_widgets, r.filter_callbacks)}


#: A page with a foreign dropdown AND a price range filter, one graph.
_TWO_FILTER_SPEC = {
    "graphs": [tfe._graph("g1")], "kpis": [],
    "build_options": {
        "layout": "auto", "link": "", "theme": "", "title": "",
        "subtitle": "", "registry": "g1",
        "filters": [{"varname": "foreign", "type": "dropdown"},
                    {"varname": "price", "type": "range"}]}}


def _kpi_card(name, stat="count", var="mpg"):
    return {"name": name, "stat": stat, "var": var, "fmt": "%9.0f",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter", "if_expr": "", "in_expr": ""}


def _card_value(text, name):
    m = re.search(r'id="kpi_val_%s"[^>]*>([^<]*)<' % re.escape(name),
                  text or "")
    return m.group(1) if m else None


#: One graph, one KPI (count of mpg), a price range filter, neither excluded.
_KPI_SPEC = {
    "graphs": [tfe._graph("g1")], "kpis": [_kpi_card("k1")],
    "build_options": {
        "layout": "auto", "link": "", "theme": "", "title": "",
        "subtitle": "", "registry": "g1 k1",
        "filters": [{"varname": "price", "type": "range"}]}}


# ---------------------------------------------------------------------------
# Node lookup
# ---------------------------------------------------------------------------

class TestNode:
    def test_node_is_the_override_or_the_path_lookup(self, monkeypatch):
        # find_node() rather than importlib.reload: a reload rebinds every
        # function, breaking the aliases other test modules imported.
        monkeypatch.setenv("DASH_NODE", "/x/node")
        assert js_runner.find_node() == "/x/node"
        monkeypatch.delenv("DASH_NODE", raising=False)
        assert js_runner.find_node() == shutil.which("node")

    def test_a_missing_node_skips_with_the_override_named(self, monkeypatch):
        monkeypatch.setattr(js_runner, "NODE", None)
        with pytest.raises(pytest.skip.Exception) as exc:
            js_runner.node()
        assert "DASH_NODE" in str(exc.value)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

class TestEncoding:
    def test_a_model_is_encoded_once_and_referenced_by_id(self):
        src = ColumnDataSource({"x": [1.0, 2.0]})
        models, objs = {}, {}
        out = js_runner.encode({"a": src, "b": src}, models, objs)
        assert out == {"a": {"__ref__": src.id}, "b": {"__ref__": src.id}}
        assert list(models.keys()) == [src.id]
        assert objs[src.id] is src

    def test_nan_inf_and_timestamps_are_json_safe(self):
        assert js_runner.plain(float("nan")) is None
        assert js_runner.plain(np.float64("nan")) is None
        ts = pd.Timestamp("2001-01-02")
        assert js_runner.plain(ts) == dr._dash_json_value(ts)

    def test_every_stand_in_kind_keeps_its_fields(self):
        models, objs = {}, {}
        src = ColumnDataSource({"x": [1.0]})
        bf = BooleanFilter(booleans=[True, False])
        div = Div(text="hi")
        sel = Select(value="1", options=[("1", "1")])
        rs = RangeSlider(start=0, end=10, value=(1, 2), step=1, width=222)
        for m in (src, bf, div, sel, rs):
            js_runner.encode(m, models, objs)
        assert "data" in models[src.id]
        assert models[bf.id]["booleans"] == [True, False]
        assert models[div.id]["text"] == "hi"
        assert models[sel.id]["value"] == "1"
        stand = models[rs.id]
        assert (stand["value"], stand["start"], stand["end"], stand["step"],
               stand["width"]) == ([1.0, 2.0], 0.0, 10.0, 1.0, 222)


# ---------------------------------------------------------------------------
# run_js
# ---------------------------------------------------------------------------

class TestRunJs:
    def test_it_returns_what_node_printed(self):
        assert js_runner.run_js(
            "process.stdout.write(JSON.stringify({a: 1}))") == {"a": 1}

    def test_a_node_error_is_an_assertion_carrying_stderr(self):
        with pytest.raises(AssertionError, match="boom"):
            js_runner.run_js("throw new Error('boom')")


# ---------------------------------------------------------------------------
# JsSession: chained state
# ---------------------------------------------------------------------------

class TestASessionCarriesState:
    def test_two_moves_chain_on_one_session(self, tmp_path):
        """A second move starts from what the first left in the model --
        the state E2's node harness could not carry before this module."""
        r = _page(tmp_path, _TWO_FILTER_SPEC)
        widgets = _widgets(r)
        w_for, cb_for = widgets["Select"]
        w_price, cb_price = widgets["RangeSlider"]
        source = tfe._renderer_source(r.figures["g1"])

        s = js_runner.JsSession(r.filter_callbacks)
        s.set(w_for, 1.0)
        s.run(cb_for)
        assert s.rows(source) == 5  # foreign == 1 alone, of _DF's ten

        # What run 2's payload for `source' is built from: the state run 1
        # committed, not the page's build-time data.
        started_from = {c: list(v) for c, v in source.data.items()}
        s.set(w_price, (4000.0, 5000.0))
        second = s.run(cb_price)
        assert s.rows(source) == 3  # foreign == 1 & price in [4000, 5000]
        assert second[source.id]["data"] != started_from  # it moved on
        assert js_runner.RUNNER  # (the shared script both runs used)
        assert s.runs[0][source.id]["data"] == started_from

    def test_a_dry_run_leaves_the_python_models_untouched(self, tmp_path):
        r = _page(tmp_path, _TWO_FILTER_SPEC)
        w_for, cb_for = _widgets(r)["Select"]
        source = tfe._renderer_source(r.figures["g1"])
        before = {c: list(v) for c, v in source.data.items()}
        s = js_runner.JsSession([])
        w_for.value = "1"
        out = s.run(cb_for, commit=False)
        after = {c: list(v) for c, v in source.data.items()}
        assert after == before
        cols = out[source.id]["data"]
        assert len(next(iter(cols.values()))) == 5

    def test_state_reports_sources_booleans_divs_and_widths(self, tmp_path):
        r = _page(tmp_path, _KPI_SPEC)
        [w], [cb] = r.filter_widgets, r.filter_callbacks
        s = js_runner.JsSession(r.filter_callbacks)
        s.set(w, (4000.0, 5000.0))
        s.run(cb)
        state = s.state()
        # Flipped by WP-29 S12 (P0.17): state() also reports muted,
        # visible and labels, the stale cue's three write-backs.
        assert set(state) == {"sources", "booleans", "divs", "widths",
                              "muted", "visible", "labels"}
        k1 = r.kpi_divs["k1"]
        text = state["divs"].get(k1.id, k1.text)
        assert _card_value(text, "k1") == "5"

    def test_set_returns_the_old_value_and_sets_the_new(self, tmp_path):
        r = _page(tmp_path, _TWO_FILTER_SPEC)
        w_price, _cb = _widgets(r)["RangeSlider"]
        expected_old = w_price.value
        s = js_runner.JsSession([])
        old = s.set(w_price, (4000.0, 5000.0))
        assert old == expected_old
        assert w_price.value == (4000.0, 5000.0)

    def test_a_proto_column_survives_a_run(self, tmp_path):
        df = tfe._DF.rename(columns={"weight": "__proto__"})
        graph = tfe._graph("g1")
        graph["plots"][0]["xvar"] = "__proto__"
        spec = {
            "graphs": [graph], "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "theme": "", "title": "",
                "subtitle": "", "registry": "g1",
                "filters": [{"varname": "foreign", "type": "dropdown"}]}}
        r = _page(tmp_path, spec, df)
        source = tfe._renderer_source(r.figures["g1"])
        w_for, cb_for = _widgets(r)["Select"]
        s = js_runner.JsSession([])
        s.set(w_for, "1")
        s.run(cb_for)
        assert "__proto__" in source.data
        assert [float(v) for v in source.data["__proto__"]] == pytest.approx(
            [3350.0, 1800.0, 3100.0, 2010.0, 2650.0])


# ---------------------------------------------------------------------------
# X1: both twins' masks
# ---------------------------------------------------------------------------

class TestMaskParity:
    def test_a_numeric_range_and_a_slider_agree_in_both_twins(self):
        specs = [{"varname": "price", "type": "range", "sentinel": "__all__"},
                {"varname": "mpg", "type": "slider", "sentinel": "__all__"}]
        values = [(4000.0, 5000.0), 20.0]
        js_mask, pandas_mask = js_runner.mask_parity(_DF, specs, values)
        expected = ((_DF["price"] >= 4000.0) & (_DF["price"] <= 5000.0)
                   & (_DF["mpg"] >= 20.0)).tolist()
        assert js_mask == pandas_mask == expected

    def test_a_string_dropdown_on_exact_text_agrees(self):
        df = pd.DataFrame({"code": ["01", "1", "1.0", "x"]})
        specs = [{"varname": "code", "type": "dropdown", "sentinel": "__all__"}]
        js_mask, pandas_mask = js_runner.mask_parity(df, specs, ["1"])
        # GAPS2 X1: exact text -- '01' and '1.0' are other values.
        assert js_mask == pandas_mask == [False, True, False, False]

    def test_a_missing_value_fails_every_range_in_both_twins(self):
        # The column's own span (3000..6000) is wider than the [4000,
        # 5000] the widget is moved to, so the move is a genuine subset,
        # not the widget's full extent (which restricts nothing).
        df = pd.DataFrame(
            {"price": [3000.0, 4200.0, np.nan, 4800.0, 6000.0]})
        specs = [{"varname": "price", "type": "range", "sentinel": "__all__"}]
        js_mask, pandas_mask = js_runner.mask_parity(
            df, specs, [(4000.0, 5000.0)])
        assert js_mask == pandas_mask == [False, True, False, True, False]

    def test_a_widget_at_its_full_extent_restricts_nothing_in_both_twins(self):
        df = pd.DataFrame({"mpg": [10.0, 20.0, 30.0]})
        specs = [{"varname": "mpg", "type": "slider", "sentinel": "__all__"}]
        values = [{"value": 10.0, "start": 10.0, "end": 30.0}]
        js_mask, pandas_mask = js_runner.mask_parity(df, specs, values)
        assert js_mask == pandas_mask == [True, True, True]

    def test_a_dropdown_on_a_small_number_agrees_since_x1(self):
        """Flipped by section 17 (GAPS2 X1).  History: report B section
        2.1, measured 25sep2026 at 91d97be: on the saved page a
        dropdown's small-number option keeps no row (JS ``String()`` uses
        exponent notation below 1e-6, not at 5e-05, so the option text and
        the column's text never match); the served pandas mask keeps the
        one matching row.  Section 17 (X1: "compare numbers as numbers in
        both modes") turns this into an equality and adds
        ``test_two_values_sharing_a_label_select_both`` beside it (Q26).
        """
        df = pd.DataFrame({"v": [5e-05, 1.0, 2.0]})
        specs = [{"varname": "v", "type": "dropdown", "sentinel": "__all__",
                  "numeric": True}]
        for val in (5e-05, 1.0):
            values = [dr._dash_option_value(val)]
            js_mask, pandas_mask = js_runner.mask_parity(df, specs, values)
            assert js_mask == pandas_mask
            assert sum(js_mask) == 1


# ---------------------------------------------------------------------------
# C2: the recount fragment runner
# ---------------------------------------------------------------------------

class TestRunFilterJsBlock:
    def test_the_histogram_block_runs_the_shipped_code_on_literal_values(self):
        from test_statistical_helpers import _AUTO_MPG, _hist
        tops, _, _, r = _hist(_AUTO_MPG, {"discrete": "discrete", "width": "3",
                                          "frequency": "frequency"})
        ac = r._dash_agg_config
        got = js_runner.run_filter_js_block("histogram", ac, _AUTO_MPG)
        np.testing.assert_array_equal(got["top"], tops)


# ---------------------------------------------------------------------------
# The migrated shims still report what they reported before
# ---------------------------------------------------------------------------

class TestTheMigratedShims:
    def test_filter_exclude_run_callback_reports_rows_and_ids_without_writing_back(self):
        primary = tfe.TestThePrimarySourceFallback._frame_source()
        graph = tfe.TestThePrimarySourceFallback._frame_source()
        args = tfe._script_args(primary, [graph], [])
        before = {c: list(v) for c, v in primary.data.items()}
        out1 = tfe._run_callback(args, dr._FILTER_JS)
        out2 = tfe._run_callback(args, dr._FILTER_JS)
        assert out1 == out2
        assert out1[primary.id] == {"rows": 2, "ids": [1, 3]}
        assert out1[graph.id] == {"rows": 2, "ids": [1, 3]}
        assert {c: list(v) for c, v in primary.data.items()} == before

    def test_help_claims_3_run_saved_reports_rows_and_div_text(self, tmp_path):
        import test_help_claims_3 as thc3
        r = _page(tmp_path, thc3.TestAKpiCardCanBeExcluded.SPEC)
        [w], [cb] = r.filter_widgets, r.filter_callbacks
        w.value = thc3.TestAKpiCardCanBeExcluded.MOVE
        sources, divs = thc3._run_saved(cb.args, cb.code)
        k1, k2 = r.kpi_divs["k1"], r.kpi_divs["k2"]
        assert thc3._card_value(divs.get(k1.id, k1.text), "k1") == "10"
        assert thc3._card_value(divs[k2.id], "k2") == "5"
        assert sources  # rows/ids were reported for at least one source

    def test_the_aliases_s05_imports_exist(self):
        import test_statistical_helpers as tsh
        assert tsh._NODE is js_runner.NODE
        assert tsh._run_filter_js_block is js_runner.run_filter_js_block

    def test_the_aliases_survive_the_node_lookup_test_run_first(
            self, monkeypatch):
        # Regression: TestNode once reloaded js_runner, so a worker that had
        # imported test_statistical_helpers first held stale aliases.
        import test_statistical_helpers as tsh
        TestNode().test_node_is_the_override_or_the_path_lookup(monkeypatch)
        assert tsh._NODE is js_runner.NODE
        assert tsh._run_filter_js_block is js_runner.run_filter_js_block


# ---------------------------------------------------------------------------
# E2: the saved page's own multi-move sequence, chained
# ---------------------------------------------------------------------------

class TestASessionMeasuresE2:
    def test_three_moves_leave_the_saved_page_where_measured(self, tmp_path):
        """Measured 25sep2026 under node (S03), on
        ``TestExcludeHoldsWhileItsOwnFilterMoves.SPEC``
        (test_help_claims_3.py): price -> [4000, 5000], foreign -> "1",
        price -> its full extent leaves the saved page at g1=3, g2=5,
        k1="3" -- exactly GAPS2 E2's served measurement ("price to
        [4000,5000], then foreign=1, then price back to its full range
        gives g1=3, g2=5, k1=3"), confirming the saved page behaves the
        same "by construction" the section file records.

        What the widgets imply at the end (only foreign=1 restricts, and
        nothing excludes foreign's effect) is {"g1": 5, "g2": 5, "k1":
        "5"} -- DIFFERENT from the measured value: g1 and k1 are excluded
        from the price filter's own callback, so they never see the third
        move and stay at the second move's rows.  Section 17 (E2) fixes
        that staleness and flips this test to the implied value.
        """
        import test_help_claims_3 as thc3
        spec = thc3.TestAnExclusionHoldsAgainstEveryMove.SPEC
        r = _page(tmp_path, spec)
        (w_for, w_price), (cb_for, cb_price) = (r.filter_widgets,
                                                r.filter_callbacks)
        g1 = tfe._renderer_source(r.figures["g1"])
        g2 = tfe._renderer_source(r.figures["g2"])
        k1 = r.kpi_divs["k1"]

        s = js_runner.JsSession(r.filter_callbacks)
        s.set(w_price, (4000.0, 5000.0))
        s.run(cb_price)
        s.set(w_for, 1.0)
        s.run(cb_for)
        s.set(w_price, (w_price.start, w_price.end))
        s.run(cb_price)

        result = {"g1": s.rows(g1), "g2": s.rows(g2),
                  "k1": thc3._card_value(k1.text, "k1")}
        # Flipped by section 17 (GAPS2 E2): measured {3, 5, "3"} at
        # 91d97be; now the state the widgets imply.
        assert result == {"g1": 5, "g2": 5, "k1": "5"}


#: apply, confirm the named test fails, revert (mutation table, section file):
#: - skip the write-back when commit is true ->
#:   TestASessionCarriesState::test_two_moves_chain_on_one_session
#: - write back when commit is false ->
#:   test_a_dry_run_leaves_the_python_models_untouched,
#:   TestTheMigratedShims::test_filter_exclude_run_callback_reports_rows_and_ids_without_writing_back
#: - write "const RAW = <literal>" instead of JSON.parse ->
#:   test_a_proto_column_survives_a_run
#: - build the pandas widgets without _dash_ftype in mask_parity ->
#:   TestMaskParity::test_a_numeric_range_and_a_slider_agree_in_both_twins
#: - run the JS side of mask_parity with raw=True always ->
#:   test_a_dropdown_on_a_small_number_agrees_since_x1 (03-05)
#: - pytest.fail instead of pytest.skip in node() ->
#:   TestNode::test_a_missing_node_skips_with_the_override_named
#: - drop "NODE as _NODE" from test_statistical_helpers.py's import ->
#:   TestTheMigratedShims::test_the_aliases_s05_imports_exist


@js_runner.requires_node
class TestTheNewWriteBacks:
    """WP-29 S12 (P0.17): a run commits a renderer's ``muted``, a Title's
    and a Div's ``visible`` and a LegendItem's ``label``, each key on its
    own, so the saved page's stale cue can be measured under node."""

    @staticmethod
    def _models():
        from bokeh.models import GlyphRenderer, LegendItem, Line, Title
        from bokeh.core.properties import value
        src = ColumnDataSource({"x": [1], "y": [2]})
        r = GlyphRenderer(glyph=Line(x="x", y="y"), data_source=src)
        t = Title(text="cue", visible=False)
        d = Div(text="", visible=False)
        it = LegendItem(label=value("Fitted values"), renderers=[r])
        return r, t, d, it

    _CODE = ("r.muted = true; t.visible = true; d.visible = true; "
             "d.text = 'note'; it.label = {value: 'x'};")

    def test_muted_visible_and_label_round_trip(self):
        r, t, d, it = self._models()
        s = js_runner.JsSession([r, t, d, it])
        s.run_code(self._CODE, {"r": r, "t": t, "d": d, "it": it})
        assert (r.muted, t.visible, d.visible, d.text) == (True, True, True,
                                                          "note")
        assert it.label.value == "x"
        st = s.state()
        assert st["muted"][r.id] is True and st["visible"][t.id] is True
        assert st["labels"][it.id] == "x"

        r2, t2, d2, it2 = self._models()
        js_runner.JsSession([]).run_code(
            self._CODE, {"r": r2, "t": t2, "d": d2, "it": it2}, commit=False)
        assert (r2.muted, t2.visible, d2.visible, d2.text) == (
            False, False, False, "")
        assert it2.label.value == "Fitted values"

    def test_a_div_still_commits_its_text_and_a_widget_its_width(self):
        d = Div(text="a")
        sl = Slider(start=0, end=10, value=1, step=1, width=100)
        js_runner.JsSession([]).run_code(
            "d.text = 'b'; s.width = 250;", {"d": d, "s": sl})
        assert d.text == "b" and sl.width == 250


@js_runner.requires_node
class TestRangesAndTickersCommit:
    """WP-30 P1.3a: the axis re-finish writes a Range1d (through setv, as
    BokehJS's HasProps.setv) and a FixedTicker's ticks; a run commits both
    back, and a slider's start/end are still never written."""

    def test_start_end_reset_and_ticks_round_trip(self):
        from bokeh.models import FixedTicker, Range1d
        r = Range1d(start=0.0, end=1.0)
        t = FixedTicker(ticks=[0.0, 1.0])
        sl = RangeSlider(start=0.0, end=10.0, value=(1.0, 2.0), step=1.0)
        js_runner.JsSession([]).run_code(
            "r.setv({reset_start: 2, reset_end: 8, start: 2, end: 8});"
            "t.ticks = [2, 4, 6, 8]; s.start = 5;",
            {"r": r, "t": t, "s": sl})
        assert (r.start, r.end, r.reset_start, r.reset_end) == (2, 8, 2, 8)
        assert list(t.ticks) == [2.0, 4.0, 6.0, 8.0]
        assert sl.start == 0.0
