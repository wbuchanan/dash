"""Time-series operators in plot varlists (WP-30 P1.7).

The defect: dash refused every time-series operator in a plot varlist,
r(101) "factor-variable and time-series operators not allowed", where
twoway draws ``line D.close date``, ``tsline D.close``, ``lfit close
L.close`` and ``scatter L(1/2).close t`` (measured on StataNow 19.5).

twoway's rules (the fixture's probes):

* operators are taken on scatter, line, connected, area, bar, spike,
  dropline, dot, lfit, qfit, lfitci, qfitci, mspline, mband, the eight
  range types, the five pc types, tsline and tsrline (A01-A29), and
  refused r(101) on fpfit, fpfitci, lowess, lpoly, lpolyci, histogram and
  kdensity (R01-R07);
* each series is computed over every observation under tsset, so an
  ``if`` selects rows of it (V01: D.close at t = 6 is close[6]-close[5]);
  gaps and panels give missing values (V03, V04); the storage type is
  tsrevar's (G01-G03), the format and value labels the base's (F01-F04);
* titles and keys read the base's label, ", " and the operators
  ("Closing price, D"), or the expression for an unlabelled base (T01-T09);
* no tsset, a string base, a factor variable, an unknown operator, a
  missing variable and unsorted data are refused in Stata's words
  (E01-E06).

dash.ado computes each expression into a column ``__dasht<k>`` with
tsrevar and names it in the spec's ``build_options.ts_cols`` with the
expression and twoway's text; both renderers take the column in as data.

The truth is test/fixtures/ts_operator_truth.json, written by
scripts/extract_ts_operator_truth.do: twoway's answers, and for the X
probes the spec and data file dash writes for the same command.
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
from bokeh.models import DatetimeAxis, HoverTool, Plot

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import load_app, render_models  # noqa: E402
from test_saved_filter_layers import _move  # noqa: E402
from test_series_labels import _summary  # noqa: E402

with open(os.path.join(HERE, "fixtures", "ts_operator_truth.json"),
          encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_P = _FIX["probes"]
#: The probes dash exported (spec and data): the renderer's cases.
_X = sorted(p for p in _P if "dash" in _P[p])
_TMP = tempfile.mkdtemp(prefix="dash_tso_")
_SEQ = iter(range(1, 10 ** 6))

#: The attribute pairs a glyph draws a point from: (x side, y side).
_PAIRS = (("x", "y"), ("x", "y1"), ("x", "y2"), ("x0", "y0"),
          ("x1", "y1"), ("x", "top"))
_DAY = np.timedelta64(1, "D")
_EPOCH = np.datetime64("1960-01-01")


# ---------------------------------------------------------------------------
# Both renderers, given a probe's spec and data
# ---------------------------------------------------------------------------
def _write(spec, data):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _inputs(pid):
    d = _P[pid]["dash"]
    return json.loads(json.dumps(d["spec"])), json.loads(json.dumps(d["data"]))


def _saved(spec, data):
    _, sp, dp = _write(spec, data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _served_module(spec, data):
    tag, sp, dp = _write(spec, data)
    ap = os.path.join(_TMP, "app_%d.py" % tag)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    return load_app(ap, "_tso_app_%d" % tag)


def _served(spec, data):
    mod = _served_module(spec, data)
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod.make_document(doc)
    return doc


def _figs(mode, spec, data):
    if mode == "saved":
        return list(_saved(spec, data).figures.values())
    doc = _served(spec, data)
    return [m for root in doc.roots for m in root.select({"type": Plot})]


# ---------------------------------------------------------------------------
# What a figure draws, as twoway's serset names it
# ---------------------------------------------------------------------------
def _num(v):
    if isinstance(v, (np.datetime64, pd.Timestamp)):
        return float((np.datetime64(v, "ms") - _EPOCH) / _DAY)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _key(a, b):
    return (round(a, 6), round(b, 6))


def _drawn_pairs(figs, tsmap):
    """``{(serset x name, serset y name): {(x, y), ...}}`` over every glyph
    that draws a time-series column, a column named as twoway's serset
    names it (``L.close`` -> ``L_close``)."""
    def sname(col):
        return tsmap[col]["expr"].replace(".", "_") if col in tsmap else col
    out = {}
    for f in figs:
        for g in f.renderers:
            glyph = getattr(g, "glyph", None)
            src = getattr(g, "data_source", None)
            if glyph is None or src is None:
                continue
            data = src.data
            for a, b in _PAIRS:
                fa, fb = getattr(glyph, a, None), getattr(glyph, b, None)
                if not (isinstance(fa, str) and isinstance(fb, str)):
                    continue
                if fa not in data or fb not in data:
                    continue
                if fa not in tsmap and fb not in tsmap:
                    continue
                got = out.setdefault((sname(fa), sname(fb)), set())
                for va, vb in zip(data[fa], data[fb]):
                    na, nb = _num(va), _num(vb)
                    if na is not None and nb is not None:
                        got.add(_key(na, nb))
    return out


def _serset_pairs(pid, xa, yb):
    for s in _P[pid]["twoway"]["sersets"]:
        cols = {v["name"]: v["values"] for v in s}
        if xa in cols and yb in cols:
            return {_key(a, b) for a, b in zip(cols[xa], cols[yb])
                    if a is not None and b is not None}
    return None


def _line_off_twoways(pid, figs):
    """The fit points dash draws that are off twoway's fitted line."""
    s = _P[pid]["twoway"]["sersets"][0]
    ys, xs = s[0]["values"], s[1]["values"]
    (x0, y0), (x1, y1) = min(zip(xs, ys)), max(zip(xs, ys))
    bad = []
    for f in figs:
        for g in f.renderers:
            if type(g.glyph).__name__ != "Line":
                continue
            data = g.data_source.data
            for x, y in zip(data.get("x", []), data.get("y", [])):
                want = y0 + (y1 - y0) * (float(x) - x0) / (x1 - x0)
                if abs(float(y) - want) > 1e-6 * max(1.0, abs(want)):
                    bad.append((float(x), float(y), want))
    return bad


def _mismatches(pid, figs):
    """Every way the drawing of probe *pid* differs from twoway's."""
    tw = _P[pid]["twoway"]
    tsmap = dr._dash_tsop_cols_named(_P[pid]["dash"]["spec"])
    out = []
    summ = _summary(figs)
    for side in ("y1", "x1"):
        if summ[side] != tw["titles"][side]:
            out.append("%s %s title: dash %r, twoway %r"
                       % (pid, side, summ[side], tw["titles"][side]))
    if "keys" in tw and summ["keys"] != sorted(tw["keys"]):
        out.append("%s keys: dash %r, twoway %r"
                   % (pid, summ["keys"], sorted(tw["keys"])))
    if _P[pid]["body"].split()[0] in ("lfit", "qfit"):
        bad = _line_off_twoways(pid, figs)
        if bad:
            out.append("%s fit off twoway's line: %r" % (pid, bad[:3]))
    else:
        drawn = _drawn_pairs(figs, tsmap)
        if not drawn:
            out.append("%s draws no time-series column" % pid)
        for (xa, yb), got in sorted(drawn.items()):
            want = _serset_pairs(pid, xa, yb)
            if want is None:
                out.append("%s: no serset holds %s and %s" % (pid, xa, yb))
            elif got != want:
                out.append("%s %s/%s: %d drawn points, %d of twoway's, %d "
                           "differ" % (pid, yb, xa, len(got), len(want),
                                       len(got ^ want)))
    for f in figs:
        for h in f.select({"type": HoverTool}):
            for lab, field in (h.tooltips or []):
                m = re.search(r"@\{(__dasht[0-9]+)\}", str(field))
                if "__dasht" in str(lab) or (
                        m and lab != tsmap.get(m.group(1), {}).get("label")):
                    out.append("%s tooltip %r for %s" % (pid, lab, field))
    # A base with a date format is drawn on a date axis (D.date in %td).
    for s in tw["sersets"]:
        for v in s:
            if not v["format"].startswith("%t"):
                continue
            for name, ent in tsmap.items():
                if ent["expr"].replace(".", "_") != v["name"]:
                    continue
                axes = [a for f in figs for a in f.left + f.below
                        if a.axis_label == ent["label"]]
                if not axes or not all(isinstance(a, DatetimeAxis)
                                       for a in axes):
                    out.append("%s: %s is not on a date axis" % (pid, name))
    if "valuelabel" in _P[pid]["opts"]:
        texts = set()
        for f in figs:
            for a in f.left:
                texts.update(str(t) for t in
                             (getattr(a, "major_label_overrides", {}) or {})
                             .values())
        if not texts or not texts <= set(tw["texts"]):
            out.append("%s value labels: dash %r, twoway's texts %r"
                       % (pid, sorted(texts), tw["texts"]))
    return out


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert m["stata_version"].startswith("19.")
        fams = {re.sub(r"[0-9]+$", "", p) for p in _P}
        assert fams == {"A", "R", "T", "V", "F", "G", "E", "B", "O", "Y"}
        assert [p for p in _P if p[0] == "A" and _P[p]["twoway"]["rc"]] == []
        assert {_P[p]["twoway"]["rc"] for p in _P if p[0] == "R"} == {101}
        assert all(_P[p]["dash"]["rc"] == 0 for p in _X)


# ---------------------------------------------------------------------------
# dash.ado's parsers
# ---------------------------------------------------------------------------
def _program(name):
    with open(os.path.join(REPO, "dash.ado"), encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"^program define %s\b.*?^end$" % re.escape(name), src,
                  re.S | re.M)
    assert m, name
    return m.group(0)


class TestTheParsers:
    def test_ts_is_declared_where_twoway_declares_it(self):
        for name in ("_dash_parse_varpart_3v", "_dash_parse_varpart_4v",
                     "_dash_parse_varpart_ts"):
            assert "syntax varlist(numeric ts)" in _program(name), name
        for name in ("_dash_parse_varpart_std", "_dash_parse_varpart_1v"):
            assert " ts)" not in _program(name), name
        seg = _program("_dash_process_segment")
        assert ('local _pt_nots "fpfit fpfitci lowess lpoly lpolyci"\n'
                "        if `: list ptype in _pt_nots' {\n"
                "            _dash_parse_varpart_std `macval(varpart)'\n"
                "        }\n        else {\n"
                "            _dash_parse_varpart_ts `macval(varpart)'\n"
                in seg)


# ---------------------------------------------------------------------------
# The spec's map, the take-in and the labels
# ---------------------------------------------------------------------------
def _ts_spec(ts_cols):
    return {"graphs": [], "build_options": {"ts_cols": ts_cols}}


class TestTheColumnsAreNamedInTheSpec:
    def test_the_map_rule(self):
        for pid in _X:
            spec = _P[pid]["dash"]["spec"]
            want = spec["build_options"].get("ts_cols", {})
            assert dr._dash_tsop_cols_named(spec) == want, pid
        ok = {"expr": "L.prixé", "label": "Prix, L"}
        assert dr._dash_tsop_cols_named(_ts_spec({"__dasht1": ok})) == {
            "__dasht1": ok}
        assert dr._dash_tsop_cols_named({"graphs": []}) == {}
        bad = [{"__dasht0": {"expr": "L.close", "label": "x"}},
               {"__dashtx": {"expr": "L.close", "label": "x"}},
               {"__dasht12345": {"expr": "L.close", "label": "x"}}]
        for expr in ("L.close;drop", "X.close", "L.1x", "L.a b",
                     "L00.close", "L0.close", "close"):
            bad.append({"__dasht1": {"expr": expr, "label": "x"}})
        bad += [{"__dasht1": {"expr": "L.close", "label": "x" * 245}},
                {"__dasht1": {"expr": "L.close", "label": 3}},
                {"__dasht1": ["L.close"]}, ["__dasht1"]]
        for b in bad:
            with pytest.raises(ValueError):
                dr._dash_tsop_cols_named(_ts_spec(b))


_ENT = {"expr": "D.close", "label": "Closing price, D"}


class TestTakingTheColumnsIn:
    def test_the_take_rule(self):
        df = pd.DataFrame({"t": [1.0, 2.0], "__dasht1": [None, 3.0]})
        spec = _ts_spec({"__dasht1": _ENT})
        out, tsmap = dr._dash_take_tsop_columns(df, spec)
        assert out is df and tsmap == {"__dasht1": _ENT}
        with pytest.raises(ValueError):
            dr._dash_take_tsop_columns(df[["t"]], spec)
        with pytest.raises(ValueError):
            dr._dash_take_tsop_columns(
                pd.DataFrame({"__dasht1": ["a", "b"]}), spec)

    def test_the_qualifier_gate_still_refuses_others(self):
        df = pd.DataFrame({"t": [1.0], "__dasht1": [2.0], "__dasht2": [3.0]})
        out, _ = dr._dash_take_qual_columns(df[["t", "__dasht1"]], {},
                                            keep=("__dasht1",))
        assert list(out.columns) == ["t", "__dasht1"]
        with pytest.raises(ValueError, match="__dasht2"):
            dr._dash_take_qual_columns(df, {}, keep=("__dasht1",))

    def test_served_build_refuses_a_bad_map(self):
        spec, data = _inputs("T04")
        spec["build_options"]["ts_cols"]["__dasht1"]["expr"] = "L.close;x"
        tag, sp, dp = _write(spec, data)
        with pytest.raises(ValueError, match="ts_cols"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(
                    os.path.join(_TMP, "bad_%d.py" % tag))


class TestTheLabels:
    def test_the_label_rule(self):
        labels = {"t": "t", "__dasht1": "__dasht1"}
        out = dr._dash_tsop_labels(labels, {"__dasht1": _ENT})
        assert out == {"t": "t", "__dasht1": "Closing price, D"}
        assert labels["__dasht1"] == "__dasht1"


# ---------------------------------------------------------------------------
# Both modes draw twoway's text, values, formats and value labels
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", ["saved", "served"])
class TestBothModesMatchTwoway:
    def test_every_probe(self, mode):
        bad = []
        for pid in _X:
            spec, data = _inputs(pid)
            bad += _mismatches(pid, _figs(mode, spec, data))
        assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# A filter move selects rows of the computed series; it never recomputes it
# ---------------------------------------------------------------------------
_RANGE = ("RangeSlider", (50.0, 100.0))


def _moved_spec(pid, filt):
    spec, data = _inputs(pid)
    spec["build_options"]["filter"] = filt
    return spec, data


def _kept(pid, xa, yb, lo, hi=None):
    return {(a, b) for a, b in _serset_pairs(pid, xa, yb)
            if a >= lo and (hi is None or a <= hi)}


class TestAFilterMoveKeepsTheComputedSeries:
    def test_saved(self):
        spec, data = _moved_spec("T04", "t, type(range)")
        _, sp, dp = _write(spec, data)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        _move(r, _RANGE)
        tsmap = dr._dash_tsop_cols_named(spec)
        got = _drawn_pairs(list(r.figures.values()), tsmap)
        assert got[("t", "D_close")] == _kept("T04", "t", "D_close", 50, 100)

    @pytest.mark.parametrize("pid", ["T04", "V02"], ids=["line", "lfit"])
    def test_served(self, pid):
        if pid == "V02":
            # lfit close L.close if t>100: the qualifier column taken out,
            # and a slider keeping t >= 101 in its place.
            spec, data = _moved_spec(pid, "t, type(slider)")
            for g in spec["graphs"]:
                for o in [g] + g["plots"]:
                    o["qual_col"] = ""
            # The probe's data hold no t; t is _n in the extractor's data.
            data["variableNames"].remove("__dashq1")
            data["variableNames"].append("t")
            data["values"] = [dict({k: v for k, v in r.items()
                                    if k != "__dashq1"}, t=float(i + 1))
                              for i, r in enumerate(data["values"])]
            move = ("Slider", 101.0)
        else:
            spec, data = _moved_spec(pid, "t, type(range)")
            move = _RANGE
        doc = _served(spec, data)
        w = [w for w in tp._widgets_of(doc) if type(w).__name__ == move[0]]
        assert len(w) == 1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tp._fire(w[0], move[1])
        figs = [m for root in doc.roots for m in root.select({"type": Plot})]
        if pid == "V02":
            assert _line_off_twoways(pid, figs) == []
        else:
            got = _drawn_pairs(figs, dr._dash_tsop_cols_named(spec))
            assert got[("t", "D_close")] == _kept(pid, "t", "D_close",
                                                  50, 100)


# ---------------------------------------------------------------------------
# The served app carries the helpers
# ---------------------------------------------------------------------------
class TestTheServedCopy:
    def test_the_app_defines_the_names(self):
        mod = _served_module(*_inputs("T04"))
        for name in ("_dash_tsop_cols_named", "_dash_take_tsop_columns",
                     "_dash_tsop_labels"):
            assert callable(getattr(mod, name)), name
        for name in ("_DASH_TSOP_PREFIX", "_DASH_TSOP_NAME_RE",
                     "_DASH_TSOP_EXPR_RE", "_DASH_TSOP_LABEL_MAX"):
            assert getattr(mod, name) == getattr(dr, name), name


# ---------------------------------------------------------------------------
# The CSV header and the notes name the expression (commit 2)
# ---------------------------------------------------------------------------
class TestTheCsv:
    def test_the_meta_carries_headers(self):
        args = (["t", "__dasht1"], {}, {}, {}, {})
        plain = dr._dash_csv_meta(*args)
        assert "headers" not in plain
        got = dr._dash_csv_meta(*args, display_names={
            "__dasht1": "D.close", "__dasht9": "L.x", "t": 3})
        assert got.pop("headers") == {"__dasht1": "D.close"}
        assert got == plain

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_header_is_the_expression(self, mode):
        from test_export import _saved_file, _served_file
        spec, data = _inputs("T03")
        spec["build_options"]["csv"] = "1"
        if mode == "saved":
            text = _saved_file(_saved(spec, data), {})
        else:
            text = _served_file(_served(spec, data), {})
        head = text.split("\r\n", 1)[0]
        assert sorted(head.split(",")) == ["L.close", "L2.close", "t"], head
        assert "__dasht" not in text


class TestTheNotes:
    def test_the_display_rule(self):
        names = {"__dasht1": "D.close"}
        assert dr._dash_col_display("__dasht1", names) == "D.close"
        assert dr._dash_col_display("t", names) == "t"
        assert dr._dash_col_display("t") == "t"


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestTheTsColumnNamesNeverReachTheUser:
    def test_case(self, mode):
        """A base whose format the page cannot write (%21x) is named by its
        expression in the note, never as __dasht1."""
        spec, data = _inputs("T05")
        spec["build_options"]["formats"]["__dasht1"] = "%21x"
        _, sp, dp = _write(spec, data)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if mode == "saved":
                render_models(dr.DashRenderer(sp, dp))
            else:
                ap = os.path.join(_TMP, "notes_%d.py" % next(_SEQ))
                dr.ServerAppBuilder(sp, dp).build(ap)
                mod = load_app(ap, "_tso_notes_%d" % next(_SEQ))
                mod.make_document(Document())
        msgs = [str(w.message) for w in caught]
        assert any("variable 'D.y2' has display format" in m for m in msgs), msgs
        assert not [m for m in msgs if "__dasht" in m], msgs
