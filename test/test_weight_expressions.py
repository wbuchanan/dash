"""Weight expressions (WP-31 A5).

The defect: ``dash lfit mpg weight [aw=price+1]`` and ``[aw=L.price]`` were
refused, r(198), "must name one variable; dash cannot evaluate a weight
expression", where twoway evaluates the expression and fits with it
(measured on StataNow 19.5: rc 0, the serset of ``[aw=price+1]`` equal to
that of ``[aw=w1]`` with ``w1 = price+1``).

dash.ado now evaluates an expression at export: a canonical time-series
term (``L.price``) becomes the column ``__dasht<k>`` (``_dash_tsop_gen``,
the key list of ``_dash_tsop_rewrite`` holds ``wexp``), any other
expression the column ``__dashw<k>`` (``_dash_wexp_gen``, ``generate
double __dashw<k> = (<expression>)``), named in the spec's ``ts_cols`` with
the expression, which both renderers take in as data
(``_dash_tsop_cols_named``).

The truth is test/fixtures/weight_operator_truth.json, written by
scripts/extract_weight_operator_truth.do; the Stata side (registration,
export, the hostile texts) is pinned by test/test_wp31_truth.cscript
U07-1..U07-3 and test/test_option_validation.cscript U07-7, U07-8.
"""

import json
import os
import re
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Plot

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import make_spec, plot_for  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "weight_operator_truth.json")
with open(FIXTURE, encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_TMP = tempfile.mkdtemp(prefix="dash_wexp_")
_SEQ = iter(range(1, 10 ** 6))


def _read(name):
    with open(os.path.join(REPO, name), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_meta_is_stamped(self):
        meta = _FIX["_meta"]
        assert sorted(meta) == ["born_date", "dash_commit", "extracted",
                                "source", "stata_version"]
        assert meta["source"] == "scripts/extract_weight_operator_truth.do"
        assert re.fullmatch(r"[0-9a-f]{40}", meta["dash_commit"])

    def test_every_case_was_measured(self):
        want = {
            "weights": {"lfit_aw_expr": 0, "lfit_aw_var": 0,
                        "lfit_aw_ts": 0, "lfit_aw_ts_var": 0,
                        "hist_fw_expr": 0, "hist_fw_var": 0,
                        "kde_aw_expr": 0, "kde_aw_var": 0,
                        "lpoly_aw_expr": 0, "lpoly_aw_var": 0,
                        "bad_expr": 111, "bad_var": 111, "bad_syntax": 198},
            "operators": {"mlabel_L": 111, "mlabel_Lnum": 111,
                          "colorvar_L": 101, "mlabvpos_L": 198, "by_L": 101},
            "ydates": {"ylabel": 198, "ytick": 198, "ymlabel": 198,
                       "ymtick": 198, "ylabel2": 198, "ytick2": 198,
                       "yscale": 121, "yscale2": 121, "ylabel_tfmt": 198,
                       "ylabel_tfmt_lit": 0, "ylabel_num": 0},
        }
        for sec, cases in want.items():
            assert sorted(_FIX[sec]) == sorted(cases), sec
            for key, rc in cases.items():
                assert _FIX[sec][key]["rc"] == rc, (sec, key)
        # The expression and its generated twin draw the same serset.
        w = _FIX["weights"]
        for a, b in (("lfit_aw_expr", "lfit_aw_var"),
                     ("lfit_aw_ts", "lfit_aw_ts_var"),
                     ("hist_fw_expr", "hist_fw_var"),
                     ("kde_aw_expr", "kde_aw_var"),
                     ("lpoly_aw_expr", "lpoly_aw_var")):
            assert w[a]["serset"] == w[b]["serset"], a
        assert len(_FIX["data"]["mpg"]) == 74


# ---------------------------------------------------------------------------
# Both renderers read the generated column
# ---------------------------------------------------------------------------
def _frame():
    d = _FIX["data"]
    df = pd.DataFrame({k: [np.nan if v is None else float(v) for v in d[k]]
                       for k in ("mpg", "weight", "price", "rep78", "t")})
    df["w1"] = df["price"] + 1
    df["w3"] = df["rep78"] + 1
    df["__dashw1"] = df["price"] + 1
    df["__dashw2"] = df["rep78"] + 1
    return df


_TS = {"__dashw1": {"expr": "price+1", "label": "price+1"},
       "__dashw2": {"expr": "rep78+1", "label": "rep78+1"}}


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_frame()), fh)
    return tag, sp, dp


def _figs(mode, spec):
    tag, sp, dp = _write(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            return list(r.figures.values())
        ap = os.path.join(_TMP, "app_%d.py" % tag)
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_wexp_app_%d" % tag)
        doc = Document()
        mod.make_document(doc)
    return [m for root in doc.roots for m in root.select({"type": Plot})]


def _drawn(figs):
    """Every glyph's numeric columns, in render order, rounded."""
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            src = getattr(r, "data_source", None)
            if g is None or src is None:
                continue
            cols = {}
            for k, v in src.data.items():
                try:
                    a = np.asarray(v, dtype=float)
                except (TypeError, ValueError):
                    continue
                if a.ndim == 1 and not k.startswith("__dash"):
                    cols[k] = [round(float(x), 9) for x in a]
            out.append((type(g).__name__, sorted(cols.items())))
    return out


#: (type, weight, expression column, its twin variable)
_CASES = [("lfit", "aweight", "__dashw1", "w1"),
          ("qfit", "aweight", "__dashw1", "w1"),
          ("lfitci", "aweight", "__dashw1", "w1"),
          ("lpoly", "aweight", "__dashw1", "w1"),
          ("kdensity", "aweight", "__dashw1", "w1"),
          ("histogram", "fweight", "__dashw2", "w3")]


def _wspec(ptype, wt, col, ts=True):
    p = plot_for(ptype, {"weight": wt, "wexp": col})
    bo = {"ts_cols": dict(_TS)} if ts else {}
    return make_spec([p], build_options=bo)


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestTheRendererReadsTheColumn:
    @pytest.mark.parametrize("ptype,wt,col,twin", _CASES,
                             ids=[c[0] for c in _CASES])
    def test_each_type(self, mode, ptype, wt, col, twin):
        got = _drawn(_figs(mode, _wspec(ptype, wt, col)))
        want = _drawn(_figs(mode, _wspec(ptype, wt, twin)))
        assert got and got == want

    def test_the_lfit_is_twoways(self, mode):
        """The fitted line of [aw=price+1] passes through twoway's serset."""
        ss = _FIX["weights"]["lfit_aw_expr"]["serset"]
        xs, ys = ss["c2"], ss["c1"]
        slope = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
        figs = _figs(mode, _wspec("lfit", "aweight", "__dashw1"))
        lines = [r for f in figs for r in f.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"]
        assert lines
        d = lines[0].data_source.data
        for x, y in zip(d["x"], d["y"]):
            want = ys[0] + slope * (float(x) - xs[0])
            assert abs(float(y) - want) <= 1e-5 * abs(want), (x, y, want)

    def test_the_served_header_lists_wexp_as_a_var_key(self, mode):
        assert "wexp" in dr._DASH_OPT_VAR_KEYS


class TestTheColumnMap:
    def test_the_weight_entries(self):
        spec = {"graphs": [], "build_options": {"ts_cols": dict(_TS)}}
        assert dr._dash_tsop_cols_named(spec) == _TS
        for expr in ("", "price;drop", "a`b", "$x", 'a"b', "a\tb",
                     "p" * 513, 3):
            bad = {"__dashw1": {"expr": expr, "label": "x"}}
            with pytest.raises(ValueError):
                dr._dash_tsop_cols_named(
                    {"graphs": [], "build_options": {"ts_cols": bad}})
        for name in ("__dashw0", "__dashwx", "__dashw12345"):
            bad = {name: {"expr": "price+1", "label": "x"}}
            with pytest.raises(ValueError):
                dr._dash_tsop_cols_named(
                    {"graphs": [], "build_options": {"ts_cols": bad}})


# ---------------------------------------------------------------------------
# dash.ado and dash_parse.mata
# ---------------------------------------------------------------------------
def _mata_function(name):
    src = _read("dash_parse.mata")
    m = re.search(r"\n[a-z ]*\b%s\(.*?\n\}\n" % re.escape(name), src,
                  re.S)
    assert m, name
    return m.group(0)


_NEW_MATA = ("_dash_wexp_ok", "_dash_wexp_reset", "_dash_wexp_rewrite",
             "_dash_wexp_export")


class TestTheMataKeyLists:
    def test_wexp_is_rewritten(self):
        body = _mata_function("_dash_tsop_rewrite")
        keys = re.search(r"keys = \(([^)]*)\)", body).group(1)
        assert '"wexp"' in keys
        body = _mata_function("_dash_wexp_rewrite")
        assert re.search(r'"wexp"', body)
        # Flipped (WP-35 DT-19): the column is named from the export's
        # prefix (_dash_col_pfx), not the __dashw literal -- a fixed
        # __dash name clashed with a user variable so named.
        assert '_dash_col_pfx() + "w"' in body


class TestTheRegistries:
    def test_needed_and_index_agree(self):
        ado = _read("dash.ado")
        needed = re.search(r"local _needed(.*?)\n\s*foreach", ado, re.S)
        assert needed
        words = set(needed.group(1).replace("///", " ").split())
        head = _read("dash_parse.mata").split("\n}\n", 1)[0]
        sys.path.insert(0, HERE)
        import program_coverage_map as pcm
        for fn in _NEW_MATA:
            assert fn in words, fn
            assert re.search(r"\*!   %s\(" % fn, head), fn
            assert fn in pcm.COVERAGE["dash_parse.mata"], fn
        assert re.search(r"(?m)^program define _dash_wexp_gen$", ado)
        assert "_dash_wexp_gen" in pcm.COVERAGE["dash.ado"]


# ---------------------------------------------------------------------------
# WP-31 A5b: a weight that is zero on every row
# ---------------------------------------------------------------------------
#: twoway's words for each type, measured with the console binary
#: (test/fixtures/weighted_markers_truth.json A5b_<type>_expr / _var): the
#: fits say the model could not be fitted and draw nothing; kdensity and
#: histogram draw nothing and say nothing.
_A5B = {"lfit": "(note:  regress could not fit model)",
        "qfit": "(note:  regress could not fit model)",
        "lfitci": "(note:  regress could not fit model)",
        "qfitci": "(note:  regress could not fit model)",
        "fpfit": "(note:  fracpoly could not fit model)",
        "fpfitci": "(note:  fracpoly could not fit model)",
        "kdensity": None, "histogram": None}
_WM_FIX = os.path.join(HERE, "fixtures", "weighted_markers_truth.json")


def _said_and_drawn(mode, spec):
    """The notes a render gives and the rows each glyph draws."""
    df = _frame()
    df["__dashw1"] = 0.0
    df["zero"] = 0.0
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(df), fh)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_a5b_app_%d" % tag)
            doc = Document()
            mod.make_document(doc)
            figs = [m for root in doc.roots
                    for m in root.select({"type": Plot})]
    said = sorted({str(x.message) for x in w})
    rows = [len(next(iter(r.data_source.data.values()), []))
            for f in figs for r in f.renderers
            if getattr(r, "data_source", None) is not None]
    return said, rows


@pytest.mark.parametrize("mode", ["saved", "served"])
@pytest.mark.parametrize("col", ["__dashw1", "zero"], ids=["expr", "var"])
@pytest.mark.parametrize("ptype", sorted(_A5B))
class TestAnAllZeroWeight:
    def test_twoways_note_only(self, mode, col, ptype):
        with open(_WM_FIX, encoding="utf-8") as fh:
            fix = json.load(fh)
        want = _A5B[ptype]
        for k in ("expr", "var"):
            rec = fix["A5b_%s_%s" % (ptype, k)]
            assert rec["rc"] == 0
            assert rec["lines"] == ([want] if want else []), rec["lines"]
        wt = "fweight" if ptype == "histogram" else "aweight"
        said, rows = _said_and_drawn(mode, _wspec(ptype, wt, col))
        weighty = [s for s in said if "weight" in s or "__dash" in s]
        assert not weighty, weighty
        if want:
            assert [s for s in said if want in s], said
        else:
            assert not [s for s in said if "(note:" in s], said
        assert not any(rows), rows


# ---------------------------------------------------------------------------
# WP-31 A5b: the weight text twoway's views take, the notes' words, and
# silence on mspline and mband
# ---------------------------------------------------------------------------
#: The forms of weighted_markers_truth.json X_<type>_<k>, k = 1..9, and
#: twoway's answer on a yxview type (scatter ... tsline, mspline, mband):
#: a text -syntax varlist(min=1 max=1)- reads as one variable is used as
#: typed, token by token (serset.class new, _genwt; series.class new).
_X_FORMS = [("price-price", 101, "- not allowed"),
            ("price - price", 198, "- invalid name"),
            ("(price)", 198, "( invalid name"),
            ("( price )", 198,
             "invalid something: unmatched open parenthesis or bracket"),
            ("pri-pri", 101, "- not allowed"),
            ("price+1", 0, None), ("price-mpg", 0, None),
            ("((price))", 0, None), ("pri", 0, None)]
_X_YXVIEW = ["scatter", "line", "mspline", "mband", "rscatter", "pcscatter",
             "bar", "tsline"]


class TestTheYxviewWeightText:
    def test_the_fixture(self):
        with open(_WM_FIX, encoding="utf-8") as fh:
            fix = json.load(fh)
        for t in _X_YXVIEW + ["function", "lfit"]:
            for k, (form, rc, line) in enumerate(_X_FORMS, 1):
                rec = fix["X_%s_%d" % (t, k)]
                assert form in rec["cmd"]
                if t in ("function", "lfit"):
                    assert rec["rc"] == 0, (t, form)
                else:
                    assert rec["rc"] == rc, (t, form)
                    assert rec["lines"] == ([line] if line else []), (t, form)
        assert fix["X_zero_order"]["rc"] == 101
        assert fix["X_option_order"]["lines"] == ["option bwidth() not allowed"]

    def test_dash_ado_reads_it_as_twoway_does(self):
        ado = _read("dash.ado")
        assert re.search(r"(?m)^program define _dash_wexp_yx$", ado)
        body = ado.split("program define _dash_wexp_yx", 1)[1].split(
            "\nend\n", 1)[0]
        assert "syntax varlist(min=1 max=1 numeric)" in body
        assert ": type" in body
        assert re.search(r"(?m)^\s+_dash_wexp_yx ", ado)
        sys.path.insert(0, HERE)
        import program_coverage_map as pcm
        assert "_dash_wexp_yx" in pcm.COVERAGE["dash.ado"]


def _notes(mode, spec, df):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(df), fh)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            render_models(dr.DashRenderer(sp, dp))
        else:
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_a5bn_app_%d" % tag)
            mod.make_document(Document())
    return sorted({str(x.message) for x in w})


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestTheNotesNameTheExpression:
    def test_a_partly_zero_expression_is_named_as_typed(self, mode):
        df = _frame()
        df["__dashw1"] = np.where(np.arange(len(df)) < 3, 0.0, 1.0)
        said = _notes(mode, _wspec("lfit", "aweight", "__dashw1"), df)
        hit = [s for s in said if "excluded" in s]
        assert hit and all("[aweight=price+1]" in s for s in hit), said
        assert not [s for s in said if "__dashw" in s], said


@pytest.mark.parametrize("mode", ["saved", "served"])
@pytest.mark.parametrize("ptype", ["mspline", "mband"])
class TestMsplineAndMbandSayNothing:
    def test_no_note(self, mode, ptype):
        """weighted_markers_truth.json I_mspline, I_mband: twoway takes the
        weight, draws the unweighted curve and says nothing."""
        with open(_WM_FIX, encoding="utf-8") as fh:
            fix = json.load(fh)
        assert fix["I_" + ptype]["lines"] == []
        said = _notes(mode, _wspec(ptype, "aweight", "w1", ts=False),
                      _frame().drop(columns=["__dashw1", "__dashw2"]))
        assert not [s for s in said if "weight" in s], said


class TestTheHelp:
    def test_an_expression_is_not_said_to_be_refused(self):
        flat = " ".join(_read("dash.sthlp").split())
        assert "one variable rather than an expression" not in flat
