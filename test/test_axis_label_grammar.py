"""
test_axis_label_grammar.py -- GAPS2 B1 (WP-28 S14): the axis-label options
read Stata's own numlist grammar, value/"text" pairs, multi-line and
compound-quoted labels, and a rule followed by a labelled list.

Before the fix (measured at 91d97be): `xlabel(1 "2019" 2 "2020" 3 "2021")`
drew six unlabelled ticks [1, 2, 3, 2019, 2020, 2021]; `10 20 to 40` drew
10, 20, 40 with `to` as a label; `1/5` and `1[1]3` drew the default ticks
(named as unsupported); `#5 50 "fifty"` lost the #5; a compound-quoted
label became a lone backtick.

twoway's own reading of each form is in test/fixtures/axis_truth.json,
group b1_label (scripts/extract_axis_truth.do).  Forms twoway refuses
(rc 198: a second consecutive string, a label after an increment, a
string before any value, single quotes, bare words, top-level commas) are
dash's own choice -- drawn gracefully, the bad token named.
"""
import importlib.util
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_MODES = ("saved", "served")
_SEQ = itertools.count()
_FIXTURE = os.path.join(_HERE, "fixtures", "axis_truth.json")


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        d = json.load(fh)
    probes = d.get("probes", {})
    if not any(p.get("group") == "b1_label" for p in probes.values()) \
            or "e3_tm_axis_lab" not in probes:
        pytest.fail("axis_truth.json lacks group b1_label / e3_tm_axis_lab: "
                    "task 14-03 must land first")
    return d


def _rep_frame():
    """rep78-like codes 0-6; labels Poor..Excellent on 1-5 (set alrep)."""
    n = 7
    df = pd.DataFrame({"rep78": np.arange(n, dtype=float),
                       "mpg": np.linspace(12, 41, n),
                       "weight": np.linspace(1760, 4840, n),
                       "foreign": np.array([0, 1, 0, 1, 0, 1, 0], float)})
    vl = {"alrep": {"1": "Poor", "2": "Fair", "3": "Average", "4": "Good",
                    "5": "Excellent"},
          "origin": {"0": "Domestic", "1": "Foreign"}}
    names = {"rep78": "alrep", "foreign": "origin"}
    return df, vl, names


def _spec(plots, go, formats=None):
    g = dict(go, name="g1", title='"t"')
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "", "registry": "g1",
                              "tabs": "", "filter_position": "top",
                              "csv": "0", "level": "95",
                              "formats": dict(formats or {}), "limits": {}}}


def _figures(mode, tmp_path, df, plots, go, formats=None, value_labels=None,
             label_names=None, record=None):
    """The figures one mode draws; warnings go to *record* when given."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, go, formats)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(df, value_labels, label_names)),
                  encoding="utf-8")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            figs = r._build_figures()
            out = [figs[k] for k in sorted(figs)]
        else:
            ap = str(tmp_path / ("app_%d.py" % tag))
            dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
            ms = importlib.util.spec_from_file_location("_alg_app_%d" % tag, ap)
            mod = importlib.util.module_from_spec(ms)
            ms.loader.exec_module(mod)
            doc = Document()
            mod.make_document(doc)
            seen, out = set(), []
            for root in doc.roots:
                for m in root.references():
                    if isinstance(m, _fig_cls) and m.id not in seen:
                        seen.add(m.id)
                        out.append(m)
            out.sort(key=lambda f: str(f.title.text if f.title else ""))
    # The generated app runs make_document once at import and once here, so
    # a served warning is recorded twice; each is counted once (set).
    if record is not None:
        record.extend(str(w.message) for w in caught)
    return out


def _sc(y="mpg", x="weight", **o):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": o}


def _xaxis(fig):
    return [a for a in fig.xaxis
            if getattr(a, "x_range_name", "default") == "default"][0]


def _ticks(ax):
    return [float(t) for t in getattr(ax.ticker, "ticks", [])]


def _auto():
    df, _, _ = _rep_frame()
    return df


# ---------------------------------------------------------------------------
class TestLabelledTicks:
    @pytest.mark.parametrize("mode", _MODES)
    def test_value_text_pairs_draw_three_labelled_ticks(self, mode, tmp_path):
        rec = []
        fig = _figures(mode, tmp_path, _auto(), [_sc(x="rep78")],
                       {"xlabel": '1 "2019" 2 "2020" 3 "2021"'}, record=rec)[0]
        ax = _xaxis(fig)
        assert _ticks(ax) == [1.0, 2.0, 3.0]
        assert dict(ax.major_label_overrides) == {1.0: "2019", 2.0: "2020",
                                                  3.0: "2021"}
        assert not [w for w in rec if "xlabel" in w], rec

    def test_a_second_string_is_a_second_line(self):
        t, lab = dr._dash_parse_axis_label_opt('2000 "low" "end" 4000 "high"')
        assert t == [2000.0, 4000.0]
        assert lab == {"2000.0": "low\nend", "4000.0": "high"}

    def test_a_compound_string_is_one_label(self):
        t, lab = dr._dash_parse_axis_label_opt(
            '2000 `"c "q" d"\' 4000 "high"')
        assert lab["2000.0"] == 'c "q" d'

    @pytest.mark.parametrize("mode", _MODES)
    def test_single_quotes_are_characters(self, mode, tmp_path):
        rec = []
        fig = _figures(mode, tmp_path, _auto(), [_sc()],
                       {"xlabel": "2000 'a' 4000"}, record=rec)[0]
        ax = _xaxis(fig)
        assert _ticks(ax) == [2000.0, 4000.0]
        assert not dict(ax.major_label_overrides)
        named = sorted({w for w in rec if "xlabel() sub-option" in w})
        assert len(named) == 1 and "'a'" in named[0]

    def test_a_string_labels_the_last_value_of_its_run(self):
        t, lab = dr._dash_parse_axis_label_opt('2000(1000)4000 "top"')
        assert t == [2000.0, 3000.0, 4000.0]
        assert lab == {"4000.0": "top"}

    def test_a_string_before_any_value_is_named_not_drawn(self):
        spec = dr._dash_parse_axis_spec('"a" 2000')
        assert spec["ticks"] == [2000.0] and spec["labels"] == {}
        assert spec["unsupported"] == ["a"]


_FORMS = [
    ("1/5", [1, 2, 3, 4, 5]), ("5/1", [1, 2, 3, 4, 5]),
    ("-2/2", [-2, -1, 0, 1, 2]), ("1[1]3", [1, 2, 3]),
    ("1(2)10", [1, 3, 5, 7, 9]), ("9(-2)1", [1, 3, 5, 7, 9]),
    ("-1(.5)2.5", [-1, -.5, 0, .5, 1, 1.5, 2, 2.5]),
    ("10 20 to 40", [10, 20, 30, 40]), ("1 2 : 5", [1, 2, 3, 4, 5]),
    ("1 2:5", [1, 2, 3, 4, 5]), ("1 2 3/5 8(2)12", [1, 2, 3, 4, 5, 8, 10, 12]),
    ("1,2,3", [1, 2, 3]), ("1,2,3, grid", [1, 2, 3]),
]


class TestNumlistForms:
    @pytest.mark.parametrize("form,want", _FORMS, ids=[f for f, _ in _FORMS])
    @pytest.mark.parametrize("mode", _MODES)
    def test_each_form_draws_statas_values(self, mode, form, want, tmp_path):
        rec = []
        fig = _figures(mode, tmp_path, _auto(), [_sc(x="rep78")],
                       {"xlabel": form}, record=rec)[0]
        assert _ticks(_xaxis(fig)) == [float(v) for v in want]
        assert not [w for w in rec if "xlabel" in w], rec

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_rule_then_a_labelled_list(self, mode, tmp_path):
        fig = _figures(mode, tmp_path, _auto(), [_sc(y="weight", x="mpg")],
                       {"xlabel": '#5 50 "fifty"'})[0]
        ax = _xaxis(fig)
        ticks = _ticks(ax)
        assert {10.0, 20.0, 30.0, 40.0, 50.0} <= set(ticks), ticks
        assert dict(ax.major_label_overrides) == {50.0: "fifty"}

    @pytest.mark.parametrize("mode", _MODES)
    def test_xlabel2_ytick_and_a_date_axis_share_the_grammar(self, mode,
                                                             tmp_path):
        df = _auto()
        fig = _figures(mode, tmp_path, df,
                       [_sc(), _sc(y="rep78", yaxis="2")],
                       {"ylabel2": "1/3", "xtick": "2000 2500 to 4000"})[0]
        right = [a for a in fig.right
                 if getattr(a, "y_range_name", "") == "y2"][0]
        assert _ticks(right) == [1.0, 2.0, 3.0]
        extra = dict(_xaxis(fig).ticker.args)["extra"]
        assert extra == [2000.0, 2500.0, 3000.0, 3500.0, 4000.0]
        ddf = pd.DataFrame({"y": [1.0, 2.0, 3.0, 4.0],
                            "d": [14977.0, 14978.0, 14979.0, 14980.0]})
        dfig = _figures(mode, tmp_path, ddf, [_sc(y="y", x="d")],
                        {"xlabel": "14977/14980"}, formats={"d": "%td"})[0]
        assert len(_ticks(_xaxis(dfig))) == 4


_HUGE = ["0(0.000001)1000000", "0/2000000", "0 1 to 5000000", "0[0.5]5000"]


class TestTheBound:
    @pytest.mark.parametrize("form", _HUGE)
    @pytest.mark.parametrize("mode", _MODES)
    def test_every_form_is_held_to_the_limit(self, mode, form, tmp_path):
        rec = []
        t0 = time.time()
        if mode == "saved":
            with warnings.catch_warnings(record=True) as c:
                warnings.simplefilter("always")
                spec = dr._dash_parse_axis_spec(form)
            rec = [str(w.message) for w in c]
        else:
            _figures(mode, tmp_path, _auto(), [_sc()], {"xlabel": form},
                     record=rec)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                spec = dr._dash_parse_axis_spec(form)
        assert time.time() - t0 < 30
        assert spec["mode"] == "default" and spec["ticks"] == []
        assert len({w for w in rec if "2,000" in w}) == 1, rec

    @pytest.mark.parametrize("mode", _MODES)
    def test_between_numlists_cap_and_the_bound_the_renderer_expands(
            self, mode, tmp_path):
        rec = []
        fig = _figures(mode, tmp_path, _auto(), [_sc()],
                       {"xlabel": "1/1800"}, record=rec)[0]
        assert len(_ticks(_xaxis(fig))) == 1800
        assert not [w for w in rec if "2,000" in w]
        rec = []
        _figures(mode, tmp_path, _auto(), [_sc()], {"xlabel": "0/2100"},
                 record=rec)
        assert len({w for w in rec if "2,000" in w}) == 1


class TestTheExpander:
    def test_forms(self):
        assert dr._dash_expand_numlist(["1", "2", "3/5", "8(2)12"]) == (
            [1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 12.0], False, [])
        assert dr._dash_expand_numlist(["2000", "(500)", "3000"])[0] == [
            2000.0, 2500.0, 3000.0]

    def test_a_zero_step_is_bad(self):
        assert dr._dash_expand_numlist(["1(0)5"]) == ([], False, ["1(0)5"])

    def test_to_needs_two_values(self):
        v, tm, bad = dr._dash_expand_numlist(["1", "to", "5"])
        assert "to" in bad and not tm

    def test_the_count_is_taken_before_any_value_is_made(self):
        t0 = time.time()
        assert dr._dash_expand_numlist(["0(1e-12)1e6"]) == ([], True, [])
        assert time.time() - t0 < 1

    def test_non_finite_endpoints_do_not_raise(self):
        v, tm, bad = dr._dash_expand_numlist(["1e400", "0(1)1e400", "inf/3"])
        assert v == [] and len(bad) == 3


class TestTheTokenizer:
    def test_compound_quotes_nest(self):
        assert dr._dash_axis_tokens('1 `"a `"b"\' c"\' 2') == [
            ("bare", "1"), ("str", 'a `"b"\' c'), ("bare", "2")]

    def test_an_unclosed_string_runs_to_the_end(self):
        assert dr._dash_axis_tokens('1 "abc 2') == [("bare", "1"),
                                                    ("str", "abc 2")]

    def test_a_comma_inside_a_string_is_text(self):
        assert dr._dash_axis_tokens('1 "a, b"') == [("bare", "1"),
                                                    ("str", "a, b")]

    def test_the_head_split_is_quote_aware(self):
        assert dr._dash_axis_head_split('1 "a, b" 2 "c", grid') == (
            '1 "a, b" 2 "c"', ", grid")
        assert dr._dash_axis_head_split("2000,3000,4000") == (
            "2000,3000,4000", "")


class TestAgainstTwoway:
    def test_every_b1_probe_draws_the_texts_twoway_drew(self, truth,
                                                        tmp_path):
        probes = truth["probes"]
        checked = 0
        for pid, p in sorted(probes.items()):
            if p.get("group") != "b1_label" or pid.startswith("e3_") \
                    or p.get("rc") != 0:
                continue
            opt = p["command"].split(", ", 1)[1]
            key, raw = opt.split("(", 1)
            raw = raw[:-1]
            if key.startswith("xlabel") and "#" not in raw:
                spec = dr._dash_parse_axis_spec(raw)
                texts = [t.replace(",", "") for t in p["texts"]]
                if spec["mode"] == "explicit":
                    for v in spec["ticks"]:
                        lab = spec["labels"].get(str(v))
                        want = lab if lab is not None else "%g" % v
                        assert want in texts, (pid, want, texts)
                checked += 1
            if pid == "a1_hash_list":
                spec = dr._dash_parse_axis_spec(raw)
                assert spec["labels"] == {"3000.0": "three"}
                assert "three" in p["texts"]
        assert checked >= 10

    def test_the_tm_axis_probe_is_recorded(self, truth):
        p = truth["probes"]["e3_tm_axis_lab"]
        base = truth["probes"]["e3_tm_axis"]
        assert p["group"] == "b1_label"
        assert [float(v) for v in "492 495 498 501".split()] == [492.0, 495.0,
                                                                498.0, 501.0]
        assert "492(3)501" in p["command"]
        for t in ("2001m1", "2001m4", "2001m7", "2001m10"):
            assert t in p["texts"]
        assert "2002m1" in base["texts"] and "2002m1" not in p["texts"]

    def test_meta_carries_the_stata_build(self, truth):
        m = truth["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "scheme_in_force"):
            assert k in m, k


class TestHostileLabels:
    @pytest.mark.parametrize("mode", _MODES)
    def test_label_text_stays_data_in_both_modes(self, mode, tmp_path):
        bad = "</script><script>alert(1)</script>"
        fig = _figures(mode, tmp_path, _auto(), [_sc(x="rep78")],
                       {"xlabel": '1 "%s" 2 "x y"' % bad})[0]
        ax = _xaxis(fig)
        assert dict(ax.major_label_overrides)[1.0] == bad
        assert "alert" not in ax.formatter.code
        assert bad in ax.formatter.args["labels"]
