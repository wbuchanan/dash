"""test_kpi_values.py — S13: a KPI must show the statistic the user asked for.

``dash kpi mean(mpg) if foreign==1`` displays the **unconditional** mean.
Stata computes the right number and stores it; ``dash.ado`` then omits the
qualifier from the KPI JSON, so ``_build_kpi_html`` recomputes from the full
frame and overwrites it. Measured in Stata:

    mean(mpg)                  21.297297297297298
    mean(mpg) if foreign==1    24.772727272727273   <- what the card must show

Four more defects in the same family, all confirmed against the current tree:

  * ``p25``/``p75`` are accepted by ``dash kpi`` and computed for the initial
    render, but are absent from the JS recompute list — they fall through to
    ``result = 0`` the first time any filter moves.
  * the displayed precision changes when a filter moves.
  * ``dcount`` is always missing, because ``codebook`` leaves ``r()`` empty.
  * ``update(brush)`` has no standalone selection callback at all.

And one that no plan listed, found during verification and the most serious of
the set for correctness: **every percentile KPI uses pandas' quantile, not
Stata's percentile.** Stata uses Hyndman-Fan **type 2** — ``j = N*p/100``;
integer ``j`` gives ``(x_j + x_{j+1})/2``, otherwise ``x_ceil(j)``. pandas
defaults to type 7 and disagrees: p75 of ``mpg`` is **25** in Stata and
**24.75** in pandas. ``dash_render`` already contains the correct
implementation — ``_stata_percentile()`` — and the KPI paths simply never call
it.

Every expected value here comes from ``test/fixtures/kpi_truth.json``, measured
in Stata with the command recorded beside it.
"""
import json
import math
import os
import re
import shutil
import subprocess
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

_FIXTURE = os.path.join(_HERE, "fixtures", "kpi_truth.json")


@pytest.fixture(scope="module")
def truth():
    """Stata's measured numbers.

    The fixture is part of the repository, so a missing one is a broken
    checkout and fails every test that compares with Stata.  The module was
    marked to skip whole when it was missing: measured 24sep2026, with the
    file moved away all 56 tests skipped -- the 30 that never read it too
    -- and the run exited 0, so every comparison with Stata could vanish
    from a run that reported no failure.
    """
    assert os.path.exists(_FIXTURE), (
        "test/fixtures/kpi_truth.json is missing: the KPI cards cannot be "
        "compared with Stata")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _stat(truth, scope, name):
    """One measured statistic from the fixture.

    Each entry is stored as ``{"cmd": ..., "value": ...}`` so a reviewer can
    re-derive it in Stata; this unwraps the value.
    """
    entry = truth["kpi_stats"][scope][name]
    return float(entry["value"] if isinstance(entry, dict) else entry)


_AUTO_CSV = os.path.join(_HERE, "fixtures", "data", "auto.csv")


@pytest.fixture(scope="module")
def auto():
    """sysuse auto's mpg and weight, at full precision.

    Part of the repository too: missing, it fails rather than skips (it
    skipped, like the fixture above).
    """
    assert os.path.exists(_AUTO_CSV), "test/fixtures/data/auto.csv is missing"
    # float, not int64: make_data_json emits raw values and numpy ints are
    # not JSON-serialisable. Stata stores these as numerics anyway.
    return pd.read_csv(_AUTO_CSV).astype(float)


def _render_kpi(df, *, stat, var, if_expr="", fmt="", extra_cols=None,
                filters=None, update=""):
    plots = [{"type": "scatter", "yvar": var, "xvar": var, "options": {}}]
    spec = make_spec(plots)
    kpi = {"name": "k1", "stat": stat, "var": var, "title": "T", "fmt": fmt}
    if if_expr:
        kpi["if_expr"] = if_expr
    if update:
        kpi["update"] = update
    spec["kpis"] = [kpi]
    spec["build_options"]["registry"] = "k1 g1"
    if filters:
        spec["build_options"]["filters"] = filters
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr


def _card_text(dr):
    return "\n".join(getattr(v, "text", "") for v in dr.kpi_divs.values())


# ======================================================================
# The measured anchor
# ======================================================================

class TestQualifiedKpiShowsTheConditionalStatistic:

    def test_the_anchor_is_what_stata_measured(self, truth):
        a = truth["anchor"]
        assert a["confirmed"] is True
        assert float(a["full_precision"]["value"]) == pytest.approx(
            24.772727272727273)

    def test_an_unqualified_mean_is_the_unconditional_one(self, truth, auto):
        dr = _render_kpi(auto, stat="mean", var="mpg", fmt="%9.4f")
        want = _stat(truth, "all", "mean")
        assert f"{want:.4f}" in _card_text(dr), _card_text(dr)[:300]

    def test_a_qualified_mean_shows_the_conditional_value(self, truth, auto):
        """The card shows 21.2973 where Stata reports 24.7727.

        This compared the card with pandas' mean over a stand-in for foreign
        (weight < 3000), built without the value labels Stata gives foreign,
        so it held dash to pandas on data no Stata user has: measured
        24sep2026, it passed with the renderer decoding a labelled variable
        into its labels before the qualifier ran, which leaves `foreign==1'
        matching nothing on real data.  It now uses sysuse auto's own
        foreign -- test/fixtures/kpi_pctile_truth.json holds the column,
        with mpg and weight row for row as auto.csv has them -- with its
        value labels, the qualifier as Stata's command writes it, and
        compares the card with Stata's own display of summarize mpg if
        foreign==1 at %9.4f.
        """
        with open(os.path.join(_HERE, "fixtures", "kpi_pctile_truth.json"),
                  encoding="utf-8") as fh:
            stata_auto = json.load(fh)["auto"]
        assert [float(v) for v in stata_auto["mpg"]] == list(auto["mpg"])
        assert [float(v) for v in stata_auto["weight"]] == list(auto["weight"])
        df = auto.copy()
        df["foreign"] = [float(v) for v in stata_auto["foreign"]]
        spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                           "options": {}}])
        spec["kpis"] = [{"name": "k1", "stat": "mean", "var": "mpg",
                         "title": "T", "fmt": "%9.4f", "if_expr": "foreign==1"}]
        spec["build_options"]["registry"] = "k1 g1"
        data = make_data_json(df, {"origin": {"0": "Domestic", "1": "Foreign"}},
                              {"foreign": "origin"})
        paths = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(paths[0], "w") as f:
                json.dump(spec, f)
            with open(paths[1], "w") as f:
                json.dump(data, f)
            dr = DashRenderer(*paths)
            dr.render()
        finally:
            for p in paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        text = _card_text(dr)
        shown = re.findall(r'id="kpi_val_k1"[^>]*>([^<]*)<', text)
        want = truth["anchor"]["as_displayed_9_4f"]
        assert want["value"] == "24.7727", want
        assert [s.strip() for s in shown] == [want["value"]], (
            f"the card shows {shown}; Stata's `{want['cmd']}' displays "
            f"{want['value']}; card was: {text[:300]}"
        )

    def test_the_qualifier_reaches_the_renderer_at_all(self, auto):
        df = auto.copy()
        df["foreign"] = np.where(df["weight"] < 3000, 1.0, 0.0)
        dr = _render_kpi(df, stat="mean", var="mpg", if_expr="foreign == 1")
        kpis = dr.master_spec.get("kpis", [])
        assert kpis and kpis[0].get("if_expr"), (
            "the KPI's if_expr is absent from the spec, so the renderer "
            "cannot honour it"
        )


# ======================================================================
# Stata's percentile, not pandas'
# ======================================================================

class TestPercentileKpisUseStatasRule:

    def test_the_two_rules_genuinely_disagree(self, truth, auto):
        """Guard against this test passing vacuously."""
        v = auto["mpg"].to_numpy(float)
        stata = dash_render._stata_percentile(np.sort(v), 75)
        pandas_ = float(pd.Series(v).quantile(0.75))
        assert stata != pytest.approx(pandas_), (
            "the two percentile rules agree on this data, so it cannot "
            "distinguish them"
        )

    @pytest.mark.parametrize("stat,p", [("p25", 25), ("p50", 50),
                                        ("p75", 75)])
    def test_the_kpi_matches_stata(self, truth, auto, stat, p):
        want = _stat(truth, "all", stat)
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%9.4f")
        assert f"{want:.4f}" in _card_text(dr), (
            f"{stat} showed something other than Stata's {want}; card: "
            f"{_card_text(dr)[:200]}"
        )

    def test_no_kpi_path_uses_pandas_quantile(self):
        """The correct implementation already existed in the file."""
        import inspect
        for fn in (DashRenderer._kpi_statistic,
                   DashRenderer._compute_kpi_stat,
                   DashRenderer._compute_kpi_stat_on_df):
            src = inspect.getsource(fn)
            assert ".quantile(" not in src, (
                f"{fn.__name__} still uses pandas' quantile, which is "
                f"Hyndman-Fan type 7; Stata uses type 2"
            )
        assert "_stata_percentile" in inspect.getsource(
            DashRenderer._kpi_statistic)

    def test_median_agrees_with_stata(self, truth, auto):
        want = _stat(truth, "all", "median")
        dr = _render_kpi(auto, stat="median", var="mpg", fmt="%9.4f")
        assert f"{want:.4f}" in _card_text(dr)


# ======================================================================
# Every statistic, against the fixture
# ======================================================================

class TestEveryStatisticMatchesStata:

    @pytest.mark.parametrize("stat", [
        "mean", "sum", "count", "min", "max", "median", "sd",
        "p25", "p50", "p75",
    ])
    def test_unconditional(self, truth, auto, stat):
        want = _stat(truth, "all", stat)
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%12.6f")
        assert f"{want:.6f}" in _card_text(dr), (
            f"{stat}: expected {want:.6f}; card: {_card_text(dr)[:200]}"
        )

    @pytest.mark.parametrize("stat", ["var", "cv", "iqr", "skewness"])
    def test_the_statistics_the_command_does_not_yet_accept(self, truth, auto,
                                                            stat):
        """Capability gap: accepted by neither dash.ado nor the renderer."""
        want = _stat(truth, "all", stat)
        dr = _render_kpi(auto, stat=stat, var="mpg", fmt="%12.6f")
        assert f"{want:.6f}" in _card_text(dr), (
            f"{stat} is not supported; expected {want:.6f}"
        )

    @pytest.mark.parametrize("key,missing_rows", [
        ("mpg_distinct_nonmissing", 0),
        ("mpg_missing_in_1_5_distinct_nonmissing", 5),
    ])
    def test_dcount_returns_a_number(self, truth, auto, key, missing_rows):
        """codebook leaves r() empty, so dcount has always been missing.

        Compared with Stata's own count now.  This read a fixture key,
        ``make_distinct``, that does not exist, so its "want" was always
        None and unused, and it compared the card with pandas' nunique --
        the renderer's own arithmetic, checked against itself.  With the
        first five mpg values missing, Stata counts 21 distinct values, 22
        if missing counted as one: dcount must not count it.
        """
        entry = truth["dcount"]["truth"][key]
        want = int(entry["value"])
        df = auto.copy()
        df.loc[df.index[:missing_rows], "mpg"] = np.nan
        dr = _render_kpi(df, stat="dcount", var="mpg", fmt="%9.0f")
        text = _card_text(dr)
        shown = re.findall(r'id="kpi_val_k1"[^>]*>([^<]*)<', text)
        assert shown == [str(want)], (
            f"dcount shows {shown}; Stata's `{entry['cmd']}' gives {want}; "
            f"card: {text[:300]}")


# ======================================================================
# Behaviour under filtering
# ======================================================================

def _filtered_dashboard(df, stat, fmt=""):
    return _render_kpi(
        df, stat=stat, var="mpg", fmt=fmt,
        filters=[{"varname": "mpg", "type": "range", "exclude": [],
                  "label": ""}],
    )


class TestKpisUnderFiltering:

    @staticmethod
    def _js_kpi(stat, values):
        """Run the SHIPPED KPI recompute for one statistic under node.

        Asserting that a literal like 'p25' appears in the JS would pass or
        fail on an implementation detail -- the branch is a regex over pNN,
        which is better code and invisible to a substring search. This runs
        the code users receive and compares the number it produces.
        """
        import shutil, subprocess, tempfile
        node = shutil.which("node")
        if node is None:
            pytest.skip("node is not installed")
        js = dash_render._FILTER_JS
        helpers = js[js.index("function dash_pctl"):
                     js.index("// agg_sources is a Bokeh model list")]
        lo = js.index("    if (stat === 'count') {")
        hi = js.index("    let fmt;", lo)
        block = js[lo:hi]
        harness = (
            helpers
            + "\nconst vals = " + json.dumps([float(v) for v in values]) + ";"
            + "\nconst stat = " + json.dumps(stat) + ";"
            + "\nlet result = 0;\n" + block
            + "\nprocess.stdout.write(JSON.stringify(result));"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                          delete=False) as fh:
            fh.write(harness)
            path = fh.name
        try:
            res = subprocess.run([node, path], capture_output=True,
                                 text=True, timeout=60)
            assert res.returncode == 0, (
                f"the shipped KPI recompute failed under node:\n"
                f"{res.stderr[:1200]}"
            )
            return json.loads(res.stdout)
        finally:
            os.unlink(path)

    @pytest.mark.parametrize("stat", [
        "mean", "sum", "count", "min", "max", "median", "sd",
        "p25", "p50", "p75", "var", "cv", "iqr", "skewness", "dcount",
    ])
    def test_the_callback_agrees_with_the_initial_render(self, auto, stat):
        """Every supported statistic, recomputed by the shipped JavaScript.

        p25 and p75 had no branch at all and fell through to ``result = 0``
        the first time any filter moved. Adding a statistic that silently
        reads 0 under filtering would be the same defect again, so this
        covers all of them.
        """
        col = auto["mpg"].dropna()
        want = DashRenderer._kpi_statistic(col, stat)
        got = self._js_kpi(stat, col.tolist())
        assert got is not None and got == pytest.approx(want, rel=1e-9), (
            f"{stat}: the callback computes {got}, the initial render "
            f"{want}"
        )

    @pytest.mark.parametrize("stat", ["p25", "p75", "median", "iqr"])
    def test_the_callback_uses_statas_percentile_rule(self, truth, auto, stat):
        """Not merely non-zero -- the same rule as the initial render.

        The assertion ran only where pandas' rule and Stata's give different
        numbers, and on mpg they give the same p25 (18) and median (20), so
        those two cases asserted nothing: measured 24sep2026, both passed
        with the callback's percentile branches removed, reading 0.  Every
        case now compares the callback with Stata's own number (summarize,
        detail), and the guard keeps cases that tell the rules apart (p75 is
        25 in Stata and 24.75 in pandas; iqr 7 and 6.75).
        """
        col = auto["mpg"].dropna()
        got = self._js_kpi(stat, col.tolist())
        scope = truth["kpi_stats"]["all"]
        stata = {s: float(scope[s]["value"])
                 for s in ("p25", "p75", "median", "iqr")}
        assert got == stata[stat], (
            f"{stat}: the callback computes {got}; Stata's "
            f"`{scope[stat]['cmd']}' gives {stata[stat]}"
        )
        pandas_rule = {
            "p25": float(col.quantile(0.25)),
            "p75": float(col.quantile(0.75)),
            "median": float(col.median()),
            "iqr": float(col.quantile(0.75) - col.quantile(0.25)),
        }
        assert {s for s in stata if pandas_rule[s] != stata[s]} == {
            "p75", "iqr"}, pandas_rule

    @staticmethod
    def _js_format(cfg_entry, value):
        """Run the SHIPPED formatting branch of the callback under node."""
        import shutil, subprocess, tempfile
        node = shutil.which("node")
        if node is None:
            pytest.skip("node is not installed")
        js = dash_render._FILTER_JS
        lo = js.index("    let fmt;")
        hi = js.index("    // Rebuild the complete Div HTML", lo)
        block = js[lo:hi]
        # The number writers the branch calls (dash_numfmt and its helpers,
        # WP-23), which sit beside dash_apply_kpis.
        writers = js[js.index("// ---- A number written as the card's"):
                     js.index("function dash_apply_kpis(")]
        harness = (
            writers
            + "\nconst k = " + json.dumps(cfg_entry) + ";"
            + "\nconst result = " + json.dumps(float(value)) + ";\n"
            + block
            + "\nprocess.stdout.write(JSON.stringify(fmt));"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                          delete=False) as fh:
            fh.write(harness)
            path = fh.name
        try:
            res = subprocess.run([node, path], capture_output=True,
                                 text=True, timeout=60)
            assert res.returncode == 0, (
                f"the shipped formatting branch failed under node:\n"
                f"{res.stderr[:1200]}"
            )
            return json.loads(res.stdout)
        finally:
            os.unlink(path)

    @pytest.mark.parametrize("fmt", ["", "%9.4f", "%9.0f", "%12.0fc"])
    def test_the_displayed_value_is_identical_before_and_after_a_filter(
        self, auto, fmt
    ):
        """The card must not change shape the moment a filter moves.

        The initial render fell back to the variable's display format and the
        callback to %9.0f, so with no fmt() a mean read 21.2972972972973 and
        became 21 on the first interaction.
        """
        dr = _filtered_dashboard(auto, "mean", fmt=fmt)
        assert dr.filter_callbacks, "no filter callback was built"
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert cfg, "the KPI did not reach the callback"

        value = DashRenderer._kpi_statistic(auto["mpg"].dropna(), "mean")
        import re
        text = _card_text(dr)
        m = re.search(r">([\-\d,]+\.?\d*(?:e[+\-]?\d+)?)<", text)
        assert m, f"no numeric value in the card: {text[:200]}"
        initial = m.group(1)
        from_js = self._js_format(cfg[0], value)
        assert from_js == initial, (
            f"fmt({fmt!r}): the card shows {initial!r} and the callback "
            f"would show {from_js!r} for the same number"
        )

    def test_the_javascript_uses_statas_percentile_rule(self, truth, auto):
        """The callback must not reintroduce pandas' rule in JavaScript.

        This asserted that the name ``dash_pctl'' was in the script, which
        holds whatever rule the function computes: measured 24sep2026, it
        passed with dash_pctl interpolating linearly, numpy's and pandas'
        default.  It now runs the shipped recompute under node for every
        percentile of mpg the fixture holds -- Stata's summarize, detail --
        and compares each card value with Stata's.  Six of the eleven tell
        the two rules apart (p75 is 25 in Stata, 24.75 interpolated), which
        the last assertion confirms, so a linear rule cannot pass.
        """
        scope = truth["kpi_stats"]["all"]
        mpg = auto["mpg"].dropna()
        stats = ("p1", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99",
                 "median", "iqr")
        want = {s: float((scope.get(s) or scope["_also"][s])["value"])
                for s in stats}
        got = {s: self._js_kpi(s, mpg.tolist()) for s in stats}
        assert got == want, {s: (got[s], want[s]) for s in stats
                             if got[s] != want[s]}
        type7 = truth["percentile_definition"]["do_not_use_these"][
            "numpy_pandas_default_type7"]
        assert float(type7["all_p75_type7"]["value"]) == 24.75 != got["p75"]
        linear = {s: float(np.percentile(mpg, float(s[1:])))
                  for s in stats if s.startswith("p")}
        linear["median"] = float(np.percentile(mpg, 50))
        linear["iqr"] = float(np.percentile(mpg, 75) - np.percentile(mpg, 25))
        assert {s for s in stats if linear[s] != want[s]} == {
            "p10", "p75", "p90", "p95", "p99", "iqr"}


# ======================================================================
# update(brush)
# ======================================================================

def _help_table_cells(feature):
    """``(saved page, served app)``: the two cells of *feature*'s row in
    dash.sthlp's comparison of the two modes (Server Mode)."""
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8",
              errors="replace") as fh:
        lines = [line.strip() for line in fh]
    # The header names the columns: column 38 is the saved page's.
    assert ("{col 5}{it:Feature}{col 38}{it:Saved page}"
            "{col 59}{it:Served app}") in lines
    rows = [line for line in lines
            if line.startswith("{col 5}" + feature + "{col 38}")]
    assert len(rows) == 1, (feature, rows)
    m = re.fullmatch(r"\{col 5\}" + re.escape(feature)
                     + r"\{col 38\}(.*?)\{col 59\}(.*)", rows[0])
    assert m, rows[0]
    return m.group(1), m.group(2)


# BokehJS runs a CustomJS body as a strict-mode function whose parameters are
# its args' names, then cb_obj and cb_data.  The selection callback's args
# are the source brushed, the KPI configuration and the card Divs.
_RUN_SELECTION = r"""
"use strict";
const divs = RAW.divs.map((t) => ({text: t}));
new Function("brush_source", "kpi_config_json", "kpi_divs", "cb_obj",
             "cb_data", '"use strict";\n' + RAW.code)(
    {data: RAW.data}, RAW.kpi_config_json, divs, {indices: RAW.indices}, {});
process.stdout.write(JSON.stringify(divs.map((d) => d.text)));
"""


def _plain(v):
    """One value as BokehJS holds it: a missing number is null."""
    if isinstance(v, (float, np.floating)):
        return None if math.isnan(float(v)) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    return v


def _brushed_cards(dr, indices):
    """Each card's value text after rows *indices* are selected, by the
    selection callback the saved page attaches, run as the page runs it;
    None when the page attaches no selection callback."""
    cbs = []
    for src in dr.sources.values():
        for lst in (src.selected.js_property_callbacks or {}).values():
            cbs.extend(lst if isinstance(lst, list) else [lst])
    if not cbs:
        return None
    assert len(cbs) == 1, "the page attaches %d selection callbacks" % len(cbs)
    [cb] = cbs
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    payload = {
        "data": {str(c): [_plain(v) for v in col]
                 for c, col in cb.args["brush_source"].data.items()},
        "kpi_config_json": cb.args["kpi_config_json"],
        "divs": [d.text for d in cb.args["kpi_divs"]],
        "indices": [int(i) for i in indices],
        "code": cb.code,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("const RAW = " + json.dumps(payload) + ";\n" + _RUN_SELECTION)
        path = fh.name
    try:
        res = subprocess.run([node, path], capture_output=True, text=True,
                             timeout=60)
        assert res.returncode == 0, (
            "the page's selection callback failed under node:\n"
            + res.stderr[:1500])
        texts = json.loads(res.stdout)
    finally:
        os.unlink(path)
    return [v for t in texts
            for v in re.findall(r'id="kpi_val_[^"]*"[^>]*>([^<]*)<', t)]


class TestBrushUpdateIsRealOrDocumentedAsAbsent:

    def test_the_help_and_the_code_agree(self, truth, auto):
        """dash.sthlp says whether a saved page's card follows a brush, and
        the saved page must do what it says.

        This counted ``_kpi_update_modes'' in dash_render.py -- an attribute
        assigned once and read by nothing, so the count said "not
        implemented" -- and then asserted that the help said "not supported"
        or "standalone", and the help says "standalone" in many places: it
        could not fail.  Measured 24sep2026, it passed with the page's
        selection callbacks never attached, and with the help's saved-page
        cell for brushing set to No.

        It now reads that cell -- the "Brush/lasso KPI update" row of the
        comparison table -- and brushes the first thirty rows of sysuse auto
        on a saved page, running the selection callback the page attaches.
        A "Yes" must give Stata's mean of those rows (summarize mpg in 1/30),
        and a "No" no callback at all.  What the served app's cell claims is
        held by test_help_claims_4.py's TestTheUpdateModes::
        test_the_served_app, which brushes the same thirty rows.
        """
        saved, _served = _help_table_cells("Brush/lasso KPI update")
        assert saved in ("Yes", "No"), saved
        want = float(truth["brush"]["mean"]["value"])
        dr = _render_kpi(auto, stat="mean", var="mpg", fmt="%20.10f",
                         update="brush")
        cards = _brushed_cards(dr, range(30))
        if saved == "Yes":
            assert cards is not None, (
                "the help says a saved page's card follows a brush; the page "
                "attaches no selection callback")
            assert len(cards) == 1, cards
            assert float(cards[0]) == pytest.approx(want, rel=1e-9), (
                "after brushing rows 1-30 the card shows %s; Stata's `%s' "
                "gives %r" % (cards[0], truth["brush"]["mean"]["cmd"], want))
        else:
            assert cards is None, (
                "the help says a saved page's card does not follow a brush; "
                "the page follows one: %s" % cards)


# ======================================================================
# The qualifier must survive a filter move
# ======================================================================

class TestQualifiedKpiUnderFiltering:
    """Honouring if_expr only on the initial render is half a fix.

    The initial render now applies the KPI's own qualifier, but the filter
    callback recomputes from the rows that survived the *filter* alone.  So
    ``dash kpi mean(mpg) if foreign==1`` opens at Stata's 24.7727 and jumps to
    the unconditional mean the first time any widget moves -- the same defect,
    one interaction later, and harder to notice because the opening value is
    right.
    """

    @staticmethod
    def _qualified(df):
        return _render_kpi(
            df, stat="mean", var="mpg", if_expr="foreign == 1", fmt="%9.4f",
            filters=[{"varname": "weight", "type": "range", "exclude": [],
                      "label": ""}],
        )

    @staticmethod
    def _df():
        df = pd.read_csv(_AUTO_CSV).astype(float)
        df["foreign"] = np.where(df["weight"] < 3000, 1.0, 0.0)
        return df

    def test_the_callback_receives_the_qualifying_rows(self):
        df = self._df()
        dr = self._qualified(df)
        assert dr.filter_callbacks, "no filter callback was built"
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert cfg, "the KPI did not reach the callback"
        assert cfg[0].get("has_qual") is True, (
            "the callback was told nothing about the KPI's qualifier, so it "
            "recomputes on every filtered row"
        )
        want = set(
            int(i) for i in range(len(df)) if df["foreign"].iloc[i] == 1.0
        )
        assert set(cfg[0].get("qual_ids", [])) == want, (
            "the row identities the qualifier selects were not passed to the "
            "callback"
        )

    def test_an_unqualified_kpi_carries_no_row_list(self):
        """The row list is per-KPI overhead; it must not be paid by default."""
        dr = _render_kpi(
            self._df(), stat="mean", var="mpg", fmt="%9.4f",
            filters=[{"varname": "weight", "type": "range", "exclude": [],
                      "label": ""}],
        )
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert not cfg[0].get("has_qual"), cfg[0]
        assert not cfg[0].get("qual_ids"), (
            "an unqualified KPI shipped a row-identity list it never uses"
        )

    @staticmethod
    def _js_recompute(cfg_entry, rows, varname):
        """Run the SHIPPED KPI recompute over a filtered row payload.

        ``rows`` is a list of ``(row_id, value)`` -- exactly what ``new_data``
        holds after a filter move.
        """
        import shutil, subprocess, tempfile
        node = shutil.which("node")
        if node is None:
            pytest.skip("node is not installed")
        js = dash_render._FILTER_JS
        helpers = js[js.index("function dash_pctl"):
                     js.index("// agg_sources is a Bokeh model list")]
        # The KPI recompute now lives in dash_apply_kpis(), whose parameter
        # is `data_obj' so the brush path can pass the selected rows.
        lo = js.index("    const col = data_obj[k.varname];")
        hi = js.index("    let fmt;", lo)
        block = js[lo:hi]
        payload = {
            "__dash_row__": [int(r) for r, _ in rows],
            varname: [float(v) for _, v in rows],
        }
        harness = (
            helpers
            + '\nconst ROW_ID = "__dash_row__";'
            + "\nconst data_obj = " + json.dumps(payload) + ";"
            + "\nconst k = " + json.dumps(cfg_entry) + ";"
            # The shipped block declares `result` itself and uses `continue`
            # to skip a KPI, so it is run as one iteration of a loop rather
            # than transliterated.
            + "\nlet out = null;"
            + "\nfor (let _once = 0; _once < 1; _once++) {\n"
            + block
            + "\nout = result;\n}"
            + "\nprocess.stdout.write(JSON.stringify(out));"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                          delete=False) as fh:
            fh.write(harness)
            path = fh.name
        try:
            res = subprocess.run([node, path], capture_output=True,
                                 text=True, timeout=60)
            assert res.returncode == 0, (
                f"the shipped KPI recompute failed under node:\n"
                f"{res.stderr[:1200]}"
            )
            return json.loads(res.stdout)
        finally:
            os.unlink(path)

    def test_the_javascript_restricts_the_statistic_to_the_qualifier(self):
        """The number the user sees after moving a widget."""
        df = self._df()
        dr = self._qualified(df)
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])[0]

        # The filter kept every row with weight < 4000; of those, the KPI's
        # own qualifier keeps the ones with foreign == 1.
        kept = [i for i in range(len(df)) if df["weight"].iloc[i] < 4000]
        rows = [(i, df["mpg"].iloc[i]) for i in kept]
        want = float(
            df["mpg"].iloc[[i for i in kept if df["foreign"].iloc[i] == 1.0]]
            .mean()
        )
        unconditional = float(df["mpg"].iloc[kept].mean())
        assert want != pytest.approx(unconditional), (
            "the fixture does not distinguish the two rules"
        )
        got = self._js_recompute(cfg, rows, "mpg")
        assert got == pytest.approx(want, rel=1e-9), (
            f"after a filter move the callback computed {got}; the "
            f"qualified mean is {want} and the unconditional one "
            f"{unconditional}"
        )

    def test_an_unqualified_kpi_is_unaffected(self):
        """The fix must not change the ordinary case."""
        df = self._df()
        dr = _render_kpi(
            df, stat="mean", var="mpg", fmt="%9.4f",
            filters=[{"varname": "weight", "type": "range", "exclude": [],
                      "label": ""}],
        )
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])[0]
        kept = [i for i in range(len(df)) if df["weight"].iloc[i] < 4000]
        rows = [(i, df["mpg"].iloc[i]) for i in kept]
        want = float(df["mpg"].iloc[kept].mean())
        got = self._js_recompute(cfg, rows, "mpg")
        assert got == pytest.approx(want, rel=1e-9), (got, want)

    def test_the_card_opens_and_stays_on_the_same_number(self):
        """End to end: initial render and callback agree for a qualified KPI."""
        import re
        df = self._df()
        dr = self._qualified(df)
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])[0]
        text = _card_text(dr)
        m = re.search(r">([\-\d,]+\.?\d*)<", text)
        assert m, f"no numeric value in the card: {text[:200]}"
        # Every row passes the (untouched) filter, so the callback sees them all.
        rows = [(i, df["mpg"].iloc[i]) for i in range(len(df))]
        got = self._js_recompute(cfg, rows, "mpg")
        # The card is rendered through fmt(%9.4f); compare at that precision.
        assert float(m.group(1).replace(",", "")) == pytest.approx(
            round(got, 4), abs=1e-9), (
            f"the card opens on {m.group(1)} and the first filter move would "
            f"change it to {got}"
        )
