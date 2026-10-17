"""test_kpi_weights.py -- WP-31 H2k: KPI cards take Stata's weights.

``dash kpi mean(mpg) [aw=weight]`` gives the card ``summarize mpg
[aw=weight]``'s answer, for every statistic and every weight class dash kpi
takes (aweight, fweight, iweight), and three statistics join the list:
``kurtosis`` (``summarize, detail``'s r(kurtosis)), ``semean``
(``tabstat``'s se(mean), r(sd)/sqrt(r(N))) and ``range`` (r(max) - r(min)).

Every expected value is Stata's, measured by
``scripts/extract_kpi_weights_truth.do`` into
``test/fixtures/kpi_weights_truth.json`` together with the data it
summarized.  The Python twin (``DashRenderer._kpi_statistic``), the saved
page's script (``dash_apply_kpis`` in ``_FILTER_JS``) and both rendered
modes -- as they open, after a filter move and after a brush -- are held to
it.

Measured (the fixture): an aweight's r(sum) is the sum of weight times value
under the RAW weights; its r(N) is the observation count and its variance
divides by N - 1 after the weights are scaled to sum to N.  An fweight's
r(N) is the sum of the weights.  An iweight's r(N) is the observation count
and its variance divides by the sum of the weights less one; summarize,
detail and tabstat refuse an iweight ("iweights not allowed", r(101)), so
dash kpi takes an iweight only with the statistics plain summarize returns.
"""
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_help_claims_4 as hc4  # noqa: E402
from test_filter_exclude import _node  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "kpi_weights_truth.json")

#: The weight variable of each class in the fixture.
_WVAR = {"aweight": "weight", "fweight": "rep78", "iweight": "weight"}

_PLAIN = ["mean", "sum", "count", "dcount", "min", "max", "sd", "var", "cv",
          "range"]
_DETAIL = ["median", "iqr", "skewness", "kurtosis", "semean", "p25", "p50",
           "p75"]
_FRACTIONAL = ["p1", "p2.5", "p5", "p10", "p33.3", "p66.7", "p90", "p95",
               "p97.5", "p99"]
_ALL = _PLAIN + _DETAIL + _FRACTIONAL

#: (class, scope, variable, weight variable): every scope the fixture holds.
_SCOPES = [("unweighted", "all", "mpg", None),
           ("unweighted", "foreign1", "mpg", None),
           ("aweight", "all", "mpg", "weight"),
           ("aweight", "foreign1", "mpg", "weight"),
           ("aweight", "zero", "mpg", "wz"),
           ("aweight", "price", "price", "weight"),
           ("fweight", "all", "mpg", "rep78"),
           ("fweight", "foreign1", "mpg", "rep78"),
           ("fweight", "price", "price", "rep78"),
           ("iweight", "all", "mpg", "weight"),
           ("iweight", "foreign1", "mpg", "weight")]
_IDS = ["%s-%s" % (c, s) for c, s, _v, _w in _SCOPES]


@pytest.fixture(scope="module")
def truth():
    assert os.path.exists(_FIXTURE), (
        "test/fixtures/kpi_weights_truth.json is missing: the weighted KPI "
        "cards cannot be compared with Stata")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _frame(truth):
    """The data Stata summarized, a missing value NaN."""
    return pd.DataFrame({
        k: [np.nan if v is None else float(v) for v in vals]
        for k, vals in truth["data"].items()})


def _stats_for(kind):
    """The statistics dash kpi takes under *kind* (an iweight: those plain
    summarize returns)."""
    return _PLAIN if kind == "iweight" else _ALL


def _want(sc, stat):
    """Stata's value of *stat* in fixture scope *sc*, None when missing."""
    if stat == "count":
        return sc["N"]
    if stat == "median":
        return sc["p50"]
    if stat == "iqr":
        return sc["p75"] - sc["p25"]
    if stat == "cv":
        return sc["sd"] / sc["mean"]
    if stat == "var":
        return sc["Var"]
    if stat in sc and not isinstance(sc[stat], dict):
        return sc[stat]
    return sc["pctiles"][stat[1:]]


def _rows(df, scope):
    return df["foreign"] == 1 if scope == "foreign1" else pd.Series(
        True, index=df.index)


def _close(got, want):
    if want is None:
        return got is None or (isinstance(got, float) and math.isnan(got))
    return math.isclose(float(got), float(want), rel_tol=1e-9, abs_tol=1e-9)


class TestTheFixture:

    def test_meta_and_scopes(self, truth):
        assert set(truth["_meta"]) >= {"stata_version", "born_date",
                                       "dash_commit", "extracted", "source"}
        assert truth["_meta"]["source"] == "scripts/extract_kpi_weights_truth.do"
        for kind, scope, _v, _w in _SCOPES:
            assert scope in truth[kind], (kind, scope)
        assert truth["pweight_refusal"] == {"rc": 101,
                                            "text": "pweights not allowed"}
        assert truth["iweight_detail_refusal"] == {
            "rc": 101, "text": "iweights not allowed"}
        assert truth["iweight"]["all"]["detail_rc"] == 101
        assert truth["iweight"]["all"]["tabstat_rc"] == 101


class TestWeightedStatistics:

    @pytest.mark.parametrize("kind,scope,var,wvar", _SCOPES, ids=_IDS)
    def test_python_matches_stata(self, truth, kind, scope, var, wvar):
        df = _frame(truth)
        df = df[_rows(df, scope)]
        col = df[var].dropna()
        w = None if wvar is None else df[wvar]
        sc = truth[kind][scope]
        bad = []
        for stat in _stats_for(kind):
            if wvar is None:
                got = dr.DashRenderer._kpi_statistic(col, stat)
            else:
                got = dr.DashRenderer._kpi_statistic(col, stat, weights=w,
                                                     kind=kind)
            if not _close(got, _want(sc, stat)):
                bad.append((stat, got, _want(sc, stat)))
        assert not bad, bad

    def test_tabstat_semean_is_sd_over_root_n(self, truth):
        """The semean the fixture derives is the one tabstat reports."""
        for kind in ("unweighted", "aweight", "fweight"):
            for scope in ("all", "foreign1"):
                sc = truth[kind][scope]
                assert sc["tabstat_semean"] == pytest.approx(
                    sc["semean"], rel=1e-12), (kind, scope)
        assert truth["aweight"]["semean_aw"] == pytest.approx(
            truth["aweight"]["all"]["semean"], rel=1e-12)

    def test_the_weighted_rule_reduces_to_the_unweighted(self, truth):
        df = _frame(truth)
        col = df["price"]
        ones = pd.Series(1.0, index=col.index)
        srt = np.sort(col.to_numpy(float))
        for p in range(1, 100):
            assert (dr._stata_weighted_percentile(srt, np.ones(len(srt)), p)
                    == dr._stata_percentile(srt, p)), p
        for stat in _ALL:
            assert dr.DashRenderer._kpi_statistic(
                col, stat, weights=ones, kind="fweight") == pytest.approx(
                dr.DashRenderer._kpi_statistic(col, stat), rel=1e-12), stat


# ---------------------------------------------------------------------------
# The saved page's script, run under node
# ---------------------------------------------------------------------------

def _cfg(stat, var, wvar, kind, name=None):
    return {"name": name or ("k_" + stat.replace(".", "_")),
            "name_html": name or ("k_" + stat.replace(".", "_")),
            "stat": stat, "varname": var, "fmt": "%20.10f", "storage": "",
            "has_qual": False, "qual_ids": [], "datekind": "",
            "unitkind": "", "title": "T", "subtitle": "S",
            "text_color": "#000000", "color": "#000000", "bgcolor": "",
            "wvar": wvar or "", "wkind": kind if wvar else ""}


def _run_apply_kpis(cfgs, data):
    """The cards dash_apply_kpis writes for *cfgs* over *data* (a column ->
    list map), with the helpers the page and the brush callback carry."""
    js = dr._FILTER_JS
    helpers = js[js.index("// ---- KPI recompute, shared by"):
                 js.index("dash_apply_kpis(new_data,")]
    pctl = js[js.index("function dash_pctl("):
              js.index("// Stata's kernels ([R] kdensity)")]
    clean = {k: [None if (v is None or (isinstance(v, float)
                                        and math.isnan(v))) else v
                 for v in vals] for k, vals in data.items()}
    script = (dr._DASH_FMT_JS + pctl
              + '\nconst ROW_ID = "__dash_row__";\n' + helpers
              + "\nconst data = " + json.dumps(clean)
              + ";\nconst captured = [];"
              + "\nconst cfgs = " + json.dumps(cfgs) + ";"
              + "\nconst divs = cfgs.map((c, i) => ({set text(v) "
              "{ captured[i] = v; }}));"
              + "\ndash_apply_kpis(data, cfgs, divs, ROW_ID);"
              + "\nprocess.stdout.write(JSON.stringify(captured));")
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(script)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True, text=True,
                             timeout=120)
    finally:
        os.unlink(path)
    assert res.returncode == 0, res.stderr[:1500]
    return [hc4._card(t)[1] for t in json.loads(res.stdout)]


class TestTheJavaScriptTwin:

    @pytest.mark.parametrize("kind,scope,var,wvar", _SCOPES, ids=_IDS)
    def test_dash_apply_kpis_matches_stata(self, truth, kind, scope, var,
                                           wvar):
        df = _frame(truth)
        df = df[_rows(df, scope)]
        cols = [var] + ([wvar] if wvar else [])
        data = {c: df[c].tolist() for c in cols}
        data["__dash_row__"] = list(range(len(df)))
        stats = _stats_for(kind)
        texts = _run_apply_kpis([_cfg(s, var, wvar, kind) for s in stats],
                                data)
        sc = truth[kind][scope]
        bad = [(s, t, _want(sc, s)) for s, t in zip(stats, texts)
               if not hc4._agrees(t, _want(sc, s))]
        assert not bad, bad

    def test_the_weight_class_is_read(self, truth):
        """An aweight and an fweight on the same column differ in count,
        sum's scale apart: the class reaches the arithmetic."""
        df = _frame(truth)
        data = {"mpg": df["mpg"].tolist(), "weight": df["weight"].tolist(),
                "__dash_row__": list(range(len(df)))}
        aw, fw = _run_apply_kpis(
            [_cfg("count", "mpg", "weight", "aweight", "a"),
             _cfg("count", "mpg", "weight", "fweight", "f")], data)
        assert float(aw) == 74
        assert float(fw) == truth["aweight"]["all"]["sum_w"]


# ---------------------------------------------------------------------------
# The rendered cards, both modes
# ---------------------------------------------------------------------------

def _wspec(kind, stats, update="both"):
    spec = hc4._kpi_spec("mpg", "none", stats, update=update)
    for k in spec["kpis"]:
        k["weight"] = kind
        k["wexp"] = _WVAR[kind]
    return spec


_CARD_KINDS = ["aweight", "fweight", "iweight"]


class TestTheCardsRender:

    @pytest.mark.parametrize("kind", _CARD_KINDS)
    def test_saved_card_text_is_statas(self, tmp_path, truth, kind):
        stats = _stats_for(kind)
        r = hc4._saved(tmp_path, _wspec(kind, stats), _frame(truth))
        got = hc4._cards(d.text for d in r.kpi_divs.values())
        sc = truth[kind]["all"]
        bad = [(s, got.get(hc4._kname(s)), _want(sc, s)) for s in stats
               if not hc4._agrees(got.get(hc4._kname(s), ""), _want(sc, s))]
        assert not bad, bad

    @pytest.mark.parametrize("kind", _CARD_KINDS)
    def test_served_card_text_is_statas(self, tmp_path, truth, kind):
        stats = _stats_for(kind)
        ns = hc4._served_app(tmp_path, _wspec(kind, stats), _frame(truth))
        got = hc4._served_cards(hc4._served_session(ns))
        sc = truth[kind]["all"]
        bad = [(s, got.get(hc4._kname(s)), _want(sc, s)) for s in stats
               if not hc4._agrees(got.get(hc4._kname(s), ""), _want(sc, s))]
        assert not bad, bad

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("kind", _CARD_KINDS)
    def test_a_filter_move_keeps_the_weights(self, tmp_path, truth, mode,
                                             kind):
        """The dropdown over foreign moved to 1 leaves Stata's
        `summarize mpg [<kind>=<w>] if foreign == 1'."""
        stats = _stats_for(kind)
        spec = _wspec(kind, stats)
        if mode == "saved":
            r = hc4._saved(tmp_path, spec, _frame(truth))
            got = hc4._saved_filter_move(r, 0, "1")
        else:
            ns = hc4._served_app(tmp_path, spec, _frame(truth))
            got = hc4._served_filter_move(ns, "foreign", "1")
        sc = truth[kind]["foreign1"]
        bad = [(s, got.get(hc4._kname(s)), _want(sc, s)) for s in stats
               if not hc4._agrees(got.get(hc4._kname(s), ""), _want(sc, s))]
        assert not bad, bad

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_brush_keeps_the_weights(self, tmp_path, truth, mode):
        """The first 30 rows brushed: the weighted statistics of those rows,
        by the Python twin the fixture pins."""
        kind = "fweight"
        stats = _stats_for(kind)
        spec = _wspec(kind, stats, update="brush")
        df = _frame(truth)
        if mode == "saved":
            r = hc4._saved(tmp_path, spec, df)
            got = hc4._saved_brush(r, "g1", range(30))
        else:
            ns = hc4._served_app(tmp_path, spec, df)
            got = hc4._served_brush(ns, range(30))
        sel = df.iloc[:30]
        col = sel["mpg"].dropna()
        bad = []
        for s in stats:
            want = dr.DashRenderer._kpi_statistic(
                col, s, weights=sel["rep78"], kind=kind)
            want = None if math.isnan(want) else want
            if not hc4._agrees(got.get(hc4._kname(s), ""), want):
                bad.append((s, got.get(hc4._kname(s)), want))
        assert not bad, bad
        unweighted = dr.DashRenderer._kpi_statistic(col, "mean")
        assert not hc4._agrees(got[hc4._kname("mean")], unweighted), (
            "the brushed mean is the unweighted one")


class TestKpiConfig:

    def test_wvar_and_wkind_are_written(self, tmp_path, truth):
        r = hc4._saved(tmp_path, _wspec("aweight", ["mean"]), _frame(truth))
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        assert [(c["wvar"], c["wkind"]) for c in cfg] == [
            ("weight", "aweight")]
        spec = hc4._kpi_spec("mpg", "none", ["mean"])
        r = hc4._saved(tmp_path, spec, _frame(truth))
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        assert [(c["wvar"], c["wkind"]) for c in cfg] == [("", "")]

    def test_wvar_joins_the_brushable_need(self, tmp_path, truth):
        """A weight no graph plots still reaches every brushed source."""
        spec = _wspec("fweight", ["mean"], update="brush")
        r = hc4._saved(tmp_path, spec, _frame(truth))
        cbs = hc4._brush_callbacks(r.sources["g1"])
        assert len(cbs) == 1
        assert "rep78" in r.sources["g1"].data, sorted(r.sources["g1"].data)
