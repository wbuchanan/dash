"""WP-31 S45 (D15): default and ``#N`` axes take Stata's own ticks at build.

GAPS3 D15: dash ticked every default or ``#N`` axis with a model of
twoway's compiled ``natscale``/``_tsnatscale`` that agrees with Stata on
52-98% of ranges (auto's price ``#4`` and trunk ``#2``/``#3`` were strict
xfails).  Stata offers the routines to any program, so dash.ado asks them
at export (``_dash_axis_ticks_stata``, over the rows each layer's
``__dashq<k>`` columns select, DECISIONS A25) and carries the answers as
``build_options.stata_ticks``: ``[lo, hi, n, unit, ticks]`` per range.
Both renderers draw an entry's ticks when the axis's drawn range is the
entry's, the model otherwise -- so a filter move falls to the model and a
move back to all the data restores Stata's ticks.

Truth: test/fixtures/stata_ticks_truth.json (scripts/
extract_stata_ticks_truth.do): for 17 probes the routine's answer over the
drawn rows equals the ticks twoway drew.  The data here are synthetic with
each probe's measured range: the ticks depend on the range alone.

While iterating: ``python3 -m pytest test/test_stata_ticks.py -q``.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_default_axes as tda  # noqa: E402
from test_by_scales import _major_ticks  # noqa: E402
from test_date_range import _filter, _saved, _served, _spec  # noqa: E402
from test_date_axis_residuals import _L  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "stata_ticks_truth.json"),
          encoding="utf-8") as _fh:
    _D = json.load(_fh)
_P = _D["probes"]

#: The probes drawn on synthetic data here: variable, kind, axis read.
_DRAWN = {"P4": ("price", None, "y"), "T2": ("trunk", None, "y"),
          "T3": ("trunk", None, "y"), "P5": ("price", None, "y"),
          "TD": ("date", "td", "x"), "TW": ("w", "tw", "x"),
          "TM": ("m", "tm", "x"), "TQ": ("q", "tq", "x"),
          "TH": ("h", "th", "x"), "TY": ("y", "ty", "x"),
          "TC": ("tc", "tc", "x")}
_FMT = {"date": "%td", "w": "%tw", "m": "%tm", "q": "%tq", "h": "%th",
        "y": "%ty", "tc": "%tc", "price": "%8.0gc", "trunk": "%8.0g",
        "obs": "%8.0g", "pv": "%8.0g", "g": "%8.0g"}
_UNIT = {"td": "d", "tw": "w", "tm": "m", "tq": "q", "th": "h", "ty": "y"}


def _col(lo, hi, n=50):
    v = np.round(np.linspace(lo, hi, n)) if hi - lo > n else \
        np.linspace(lo, hi, n)
    v[0], v[-1] = lo, hi
    return v


def _frame():
    cols = {}
    for pid, (var, _k, _a) in _DRAWN.items():
        if var not in cols:
            cols[var] = _col(_P[pid]["data_lo"], _P[pid]["data_hi"])
    df = pd.DataFrame(cols)
    df["obs"] = np.arange(len(df), dtype=float)
    df["pv"] = df["price"]
    # Two by() panels over halves of the rows (TestPanels).
    df["g"] = (np.arange(len(df)) >= len(df) // 2).astype(float)
    return df


_DF = _frame()


def _entry(pid):
    p = _P[pid]
    return [p["data_lo"], p["data_hi"], p["n"], p["unit"],
            list(p["stata_ticks"])]


def _plots(pid):
    var, kind, which = _DRAWN[pid]
    return ([_L("scatter", var, "obs")] if which == "y"
            else [_L("scatter", "obs", var)])


def _go(pid):
    n = _P[pid]["n"]
    which = _DRAWN[pid][2]
    return {which + "label": "#%d" % n} if n != 5 else {}


def _build(tmp_path, mode, plots, go, table=None, filt=None):
    spec = _spec(plots, formats=_FMT, graph_options=go,
                 filters=[_filter("range", filt)] if filt else None)
    if table is not None:
        spec["build_options"]["stata_ticks"] = table
    if mode == "saved":
        r, _w = _saved(tmp_path, spec, _DF)
        return r, tda.tb._panels(list(r.figures.values()))
    doc, _w = _served(tmp_path, spec, _DF)
    return doc, tda.tb._panels(tda.tb._figs_of(doc.roots))


def _axis(fig, which):
    side = {"x": "below", "y": "left"}[which]
    return [a for a in getattr(fig, side) if hasattr(a, "ticker")][0]


def _units(ticks, kind):
    """Bokeh positions as Stata values of the axis variable."""
    if kind is None:
        return [float(t) for t in ticks]
    if kind == "tc":
        return [float(t) - dr._STATA_EPOCH_UNIX_MS for t in ticks]
    return [round(dr._dash_unix_ms_to_unit(t, _UNIT[kind]), 6)
            for t in ticks]


def _drawn(figs, pid):
    var, kind, which = _DRAWN[pid]
    return _units(_major_ticks(_axis(figs[0], which)), kind)


class TestTheFixture:
    def test_meta(self):
        assert all(_D["_meta"].get(k) for k in (
            "stata_version", "born_date", "dash_commit", "extracted",
            "source"))
        assert len(_P) >= 17
        assert all(p["rc"] == 0 for p in _P.values())

    def test_stata_agrees_with_itself(self):
        """The routine's answer over the drawn rows is the drawn axis."""
        bad = [k for k, p in _P.items()
               if p["stata_ticks"] != p["drawn_ticks"]]
        assert not bad, bad

    def test_the_cost_is_bounded(self):
        """BR-45.5: a marker, summarize and _natscale over 10^6 rows."""
        assert 0 < _D["time"]["reg_1e6"] < 1.0


class TestTheRoutineRule:
    def test_each_probe(self):
        """_dash_stata_ticks_of turns each recorded answer into the ticks
        twoway drew (natscale: r(min) by r(delta) while at most r(max);
        _tsnatscale: r(list), else r(n) steps)."""
        bad = []
        for pid, p in _P.items():
            r = p["routine"]
            got = dr._dash_stata_ticks_of(
                p["unit"], p["data_lo"], p["data_hi"], r["min"], r["max"],
                r["delta"] if r["delta"] is not None else float("nan"),
                r["n"], " ".join("%.17g" % v for v in r["list"]))
            if got != p["drawn_ticks"]:
                bad.append((pid, got, p["drawn_ticks"]))
        assert not bad, bad

    def test_overflow_is_left_to_the_model(self):
        """natscale's 32-bit step count: twoway draws the ends less and
        plus one, not natscale's answer (the model's rule)."""
        assert dr._dash_stata_ticks_of("", 1e9, 1e9 + 1, 1e9, 1e9 + 1,
                                       0.2, 6, "") is None


class TestBuildTicksAreStatas:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("pid", sorted(set(_DRAWN) - {"P4", "T2",
                                                           "T3"}))
    def test_probe(self, tmp_path, mode, pid):
        _r, figs = _build(tmp_path, mode, _plots(pid), _go(pid),
                          [_entry(pid)])
        assert _drawn(figs, pid) == _P[pid]["drawn_ticks"]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("pid", ["P4", "T2", "T3"])
    def test_auto_misses(self, tmp_path, mode, pid):
        """The three natscale cases the model does not reproduce (D-45b)."""
        _r, figs = _build(tmp_path, mode, _plots(pid), _go(pid),
                          [_entry(pid)])
        assert _drawn(figs, pid) == _P[pid]["drawn_ticks"]


class TestTheFallback:
    @pytest.mark.parametrize("mode", MODES)
    def test_no_key_is_the_model(self, tmp_path, mode):
        _r, figs = _build(tmp_path, mode, _plots("P4"), _go("P4"))
        lo, hi = _P["P4"]["data_lo"], _P["P4"]["data_hi"]
        assert _major_ticks(_axis(figs[0], "y")) == \
            dr._dash_axis_count_ticks(lo, hi, 4)


class TestTheRangeRule:
    def test_mismatch_falls_to_model(self):
        e = _entry("P4")
        tab = dr._dash_stata_tick_table({"stata_ticks": [e]})
        lo, hi = e[0], e[1]
        assert dr._dash_stata_pick(tab, lo, hi, 4, "") == e[4]
        assert dr._dash_stata_pick(tab, lo, hi * (1 + 1e-6), 4, "") is None
        assert dr._dash_stata_pick(tab, lo, hi, 5, "") is None
        assert dr._dash_stata_pick(tab, lo, hi, 4, "d") is None
        assert dr._dash_axis_count_ticks(lo, hi * (1 + 1e-6), 4,
                                         table=tab) == \
            dr._dash_axis_count_ticks(lo, hi * (1 + 1e-6), 4)

    def test_a_bad_table_is_none(self):
        for raw in (None, {}, "x", [[1, 2, 3]], [[1, 2, 5, "z", [1]]],
                    [[1, 2, 5, "", ["a"]]], [[1, 2, 5, "", []]],
                    [[float("nan"), 2, 5, "", [1]]],
                    [[1, 2, True, "", [1]]]):
            assert dr._dash_stata_tick_table({"stata_ticks": raw}) is None
        big = [[0, 1, 5, "", [0.0, 1.0]]] * (dr._DASH_STATA_TICK_MAX + 9)
        assert len(dr._dash_stata_tick_table(
            {"stata_ticks": big})) == dr._DASH_STATA_TICK_MAX

    def test_histogram_axis_has_no_key(self):
        """A computed axis (histogram, kdensity, function) is not asked:
        its drawn range is not its variable's."""
        g = {"plots": [{"type": "histogram", "yvar": "", "xvar": "price",
                        "options": {}}], "graph_options": {}}
        assert dr._dash_stata_tick_requests([g], {}) == []


class TestTheRequests:
    def test_counts_units_and_markers(self):
        g = {"plots": [{"type": "line", "yvar": "close", "xvar": "date",
                        "options": {}, "qual_col": "__dashq2"}],
             "graph_options": {"ylabel": "#7"}, "qual_col": "__dashq1"}
        rq = dr._dash_stata_tick_requests([g], {"date": "%td",
                                                "close": "%9.0g"})
        got = sorted((r["layers"][0][0], r["unit"], r["n"]) for r in rq)
        assert (("date",), "d", 5) in got and (("close",), "", 7) in got
        assert all(r["layers"][0][1] == ("__dashq1", "__dashq2")
                   for r in rq)

    def test_secondary_axes_are_their_own(self):
        g = {"plots": [{"type": "line", "yvar": "a", "xvar": "t",
                        "options": {}},
                       {"type": "line", "yvar": "b", "xvar": "t",
                        "options": {"yaxis": "2"}}], "graph_options": {}}
        ys = [r["layers"] for r in dr._dash_stata_tick_requests([g], {})
              if r["layers"][0][0] in (("a",), ("b",))]
        # Flipped (WP-34 TR-4): a layer's token carries the variables its
        # rows need, so a row with a missing y counts for no axis.
        assert [(("a",), (), ("a", "t"))] in ys \
            and [(("b",), (), ("b", "t"))] in ys

    def test_by_panels_are_asked(self):
        g = {"plots": [{"type": "scatter", "yvar": "price",
                        "xvar": "weight", "options": {}}],
             "graph_options": {"by": "foreign, xrescale"}}
        assert {r["by"] for r in dr._dash_stata_tick_requests([g], {})} \
            == {"foreign"}

    def test_names_only(self):
        """A variable or column that is not a Stata name, or a qualifier
        column dash does not write, is never passed to Stata."""
        g = {"plots": [{"type": "scatter", "yvar": "a;b", "xvar": "x",
                        "options": {}, "qual_col": "q`x'"}],
             "graph_options": {"by": "`bad'"}}
        assert dr._dash_stata_tick_requests([g], {}) == []


class TestTheCompleteCaseTokens:
    def test_complete_case_tokens(self):
        """WP-34 TR-4: each series of a layer carries the variables its rows
        need, the rows the renderers draw (TestTheRowRule): one token per y
        of a multi-y layer or of rline (that y and the x); one with every
        variable for rarea and a pc layer; none for rcap, whose axes read
        each variable over its own rows."""
        g = {"plots": [{"type": "scatter", "yvar": "a b", "xvar": "t",
                        "options": {}},
                       {"type": "rarea", "yvar1": "lo", "yvar2": "hi",
                        "xvar": "t", "options": {}},
                       {"type": "pcspike", "y1var": "p", "x1var": "q",
                        "y2var": "r", "x2var": "s", "options": {}},
                       {"type": "rline", "yvar1": "m", "yvar2": "n",
                        "xvar": "t", "options": {}},
                       {"type": "rcap", "yvar1": "u", "yvar2": "v",
                        "xvar": "t", "options": {}}],
             "graph_options": {}}
        got = {}
        for r in dr._dash_stata_tick_requests([g], {}):
            got.setdefault(r["layers"][0][0] in (("t",), ("q", "s"))
                           and "x" or "y", set()).update(r["layers"])
        assert got["y"] >= {(("a",), (), ("a", "t")),
                            (("b",), (), ("b", "t")),
                            (("lo", "hi"), (), ("lo", "hi", "t")),
                            (("p", "r"), (), ("p", "r", "q", "s")),
                            (("m",), (), ("m", "t")), (("n",), (), ("n", "t")),
                            (("u", "v"), (), ())}
        assert got["x"] >= {(("t",), (), ("a", "t")),
                            (("t",), (), ("b", "t")),
                            (("t",), (), ("lo", "hi", "t")),
                            (("q", "s"), (), ("p", "r", "q", "s")),
                            (("t",), (), ("m", "t")), (("t",), (), ())}


#: WP-34 TR-4: a frame whose first y and last x are missing (y2's least
#: value is in the first row, so a series of y2 alone reaches it).
_RR_N = 40
_RR = pd.DataFrame({
    "y": [float("nan")] + [1.3 * i + 0.7 for i in range(1, _RR_N)],
    "y2": [2.1 * i - 5.3 for i in range(_RR_N)],
    "x": [3.7 * i + 1.9 for i in range(_RR_N - 1)] + [float("nan")],
    "x2": [3.7 * i + 4.1 for i in range(_RR_N)]})
_RR_FMT = {v: "%9.0g" for v in _RR.columns}
_RR_FAMILY = {
    "scatter": _L("scatter", "y", "x"), "line": _L("line", "y", "x"),
    "connected": _L("connected", "y", "x"), "area": _L("area", "y", "x"),
    "bar": _L("bar", "y", "x"), "spike": _L("spike", "y", "x"),
    "dropline": _L("dropline", "y", "x"), "tsline": _L("tsline", "y", "x"),
    "rarea": {"type": "rarea", "yvar1": "y", "yvar2": "y2", "xvar": "x",
              "options": {}},
    "rline": {"type": "rline", "yvar1": "y", "yvar2": "y2", "xvar": "x",
              "options": {}},
    "rcap": {"type": "rcap", "yvar1": "y", "yvar2": "y2", "xvar": "x",
             "options": {}},
    "pcspike": {"type": "pcspike", "y1var": "y", "x1var": "x",
                "y2var": "y2", "x2var": "x2", "options": {}},
    "pcscatter": {"type": "pcscatter", "y1var": "y", "x1var": "x",
                  "y2var": "y2", "x2var": "x2", "options": {}}}
# The other range and pc types: each of the three row rules is held.
_RR_FAMILY.update({t: dict(_RR_FAMILY["rcap"], type=t) for t in (
    "rbar", "rspike", "rcapsym", "rconnected", "rscatter", "tsrline")})
_RR_FAMILY.update({t: dict(_RR_FAMILY["pcspike"], type=t) for t in (
    "pcarrow", "pcbarrow", "pccapsym")})


def _cc_table(plot):
    """The table the export writes under the complete-case rule, computed
    here: per request, the range of its axis variables over the rows where
    every complete-case variable of the layer is non-missing; each entry's
    ticks are four values no model draws (thirds of the range)."""
    g = {"plots": [plot], "graph_options": {}}
    out = {}
    for rq in dr._dash_stata_tick_requests([g], _RR_FMT):
        lo = hi = None
        for vs, _ms, cc in rq["layers"]:
            keep = _RR[list(cc)].notna().all(axis=1)
            for v in vs:
                col = _RR.loc[keep, v]
                lo = col.min() if lo is None else min(lo, col.min())
                hi = col.max() if hi is None else max(hi, col.max())
        letter = "x" if set(rq["layers"][0][0]) <= {"x", "x2"} else "y"
        out[letter] = [float(lo), float(hi), 5, "",
                       [float("%.12g" % (lo + k * (hi - lo) / 3))
                        for k in range(4)]]
    return out


class TestTheRowRule:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("family", sorted(_RR_FAMILY))
    def test_matches_the_drawn_range(self, tmp_path, mode, family):
        """The complete-case rule's range is the range the renderer draws
        on both axes: the pick finds the table's entry and the axis takes
        its ticks (D-34-07.b)."""
        tab = _cc_table(_RR_FAMILY[family])
        assert set(tab) == {"x", "y"}
        spec = _spec([_RR_FAMILY[family]], formats=_RR_FMT)
        spec["build_options"]["stata_ticks"] = list(tab.values())
        if mode == "saved":
            r, _w = _saved(tmp_path, spec, _RR)
            figs = tda.tb._panels(list(r.figures.values()))
        else:
            doc, _w = _served(tmp_path, spec, _RR)
            figs = tda.tb._panels(tda.tb._figs_of(doc.roots))
        for letter in ("x", "y"):
            assert _major_ticks(_axis(figs[0], letter)) == tab[letter][4], \
                letter


class TestHorizontal:
    def test_swapped_words(self):
        """Under horizontal the y variables are drawn on x: their range is
        asked for the drawn x axis (REVIEW-3e F17)."""
        g = {"plots": [{"type": "rcap", "yvar1": "mpg", "yvar2": "mpg",
                        "xvar": "weight", "options": {"horizontal": "1"}}],
             "graph_options": {}}
        rq = dr._dash_stata_tick_requests([g], {})
        # Flipped (WP-34 TR-4): the token gains its complete-case part,
        # empty for rcap, whose axes read each variable over its own rows.
        assert rq and all(r["layers"] in ([(("mpg", "mpg"), (), ())],
                                          [(("weight",), (), ())])
                          for r in rq)

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_x_takes_the_y_variables_ticks(self, tmp_path, mode):
        p = _P["P4"]
        e = [p["data_lo"], p["data_hi"], 5, "", [0.0, 5000.0, 10000.0,
                                               15000.0, 20000.0]]
        layer = {"type": "rcap", "yvar1": "price", "yvar2": "price",
                 "xvar": "obs", "options": {"horizontal": "horizontal"}}
        _r, figs = _build(tmp_path, mode, [layer], {}, [e])
        assert _major_ticks(_axis(figs[0], "x")) == e[4]


def _move(mode, obj, value):
    if mode == "saved":
        return tda._move_saved(obj, "RangeSlider", value)
    return tda._move_served(obj, "RangeSlider", value)


class TestAfterAMove:
    @pytest.mark.parametrize("mode", MODES)
    def test_move_then_back(self, tmp_path, mode):
        """A move falls to the model; a move back to all the data restores
        Stata's ticks (the saved page through the JS twin)."""
        p = _P["P4"]
        obj, figs = _build(tmp_path, mode, _plots("P4"), _go("P4"),
                           [_entry("P4")], filt="pv")
        assert _drawn(figs, "P4") == p["drawn_ticks"]
        kept = (p["data_lo"], 10000.0)
        figs = _move(mode, obj, kept)
        hi = float(_DF.loc[_DF["pv"] <= 10000.0, "price"].max())
        assert _major_ticks(_axis(figs[0], "y")) == \
            dr._dash_axis_count_ticks(p["data_lo"], hi, 4)
        figs = _move(mode, obj, (p["data_lo"], p["data_hi"]))
        assert _drawn(figs, "P4") == p["drawn_ticks"]


class TestNoQualifierText:
    def test_marker_only(self):
        """_dash_axis_ticks_stata reads marker column names and variables,
        never a qualifier's text (DECISIONS A25)."""
        with open(os.path.join(_HERE, "..", "dash.ado"),
                  encoding="utf-8") as fh:
            src = fh.read()
        body = re.search(r"program define _dash_axis_ticks_stata, rclass\n"
                         r"(.*?)\nend\n", src, re.S).group(1)
        assert "replace `lu' = 0 if `m' != 1" in body
        assert "summarize `v' if `lu' & `grp' == `g', meanonly" in body
        assert "confirm numeric variable `m', exact" in body
        for bad in ("_dq_if", "macval(", "if_expr", "`cond'", "`0'"):
            assert bad not in body.split("local layers `0'")[1], bad


@js_runner.requires_node
class TestTheJsPlacer:
    def test_equal(self):
        """dash_axis_ticks with the plan's rows equals the Python placer
        with the table, for every probe in its axis units."""
        cases, want = [], []
        for pid, (var, kind, which) in sorted(_DRAWN.items()):
            p = _P[pid]
            tab = dr._dash_stata_tick_table({"stata_ticks": [_entry(pid)]})
            if kind is None:
                lo, hi = p["data_lo"], p["data_hi"]
            elif kind == "tc":
                lo = p["data_lo"] + dr._STATA_EPOCH_UNIX_MS
                hi = p["data_hi"] + dr._STATA_EPOCH_UNIX_MS
            else:
                lo, hi = (float(v) for v in dr._stata_dates_to_datetime(
                    pd.Series([p["data_lo"], p["data_hi"]]), kind)
                    .astype("int64"))
            rows = [[r[0], r[1], r[3], list(r[4])] for r in tab]
            cases.append([lo, hi, p["n"], kind, rows])
            want.append(dr._dash_axis_count_ticks(lo, hi, p["n"], kind,
                                                  table=tab))
        src = ("const DATA = JSON.parse(" + json.dumps(json.dumps(cases))
               + ");\n" + dr._DASH_AXIS_FINISH_JS + "\nconst out = [];\n"
               "for (const c of DATA) out.push(dash_axis_ticks(c[0], c[1], "
               "c[2], c[3], c[4]));\nprocess.stdout.write("
               "JSON.stringify(out));\n")
        got = js_runner.run_js(src)
        got = json.loads(got) if isinstance(got, str) else got
        assert got == want


class _FakeSfi:
    """The few sfi calls the export helpers make, over plain dicts."""

    def __init__(self, local=None, scalars=None, globs=None):
        loc, sc, gl = dict(local or {}), dict(scalars or {}), dict(globs or {})

        class Macro:
            getLocal = staticmethod(lambda n: loc.get(n, ""))
            getGlobal = staticmethod(lambda n: gl.get(n, ""))

        class Scalar:
            getValue = staticmethod(lambda n: sc.get(n))

        self.Macro, self.Scalar = Macro, Scalar


class TestTheExportHelpers:
    def test_plan(self, monkeypatch):
        """_dash_stata_tick_plan reads the graphs from the caller's locals by
        name and writes _dash_axis_ticks_stata's arguments, ";"-joined:
        names, digits, unit letters, - + : only."""
        g = {"plots": [{"type": "line", "yvar": "close", "xvar": "date",
                        "options": {}, "qual_col": "__dashq1"}],
             "graph_options": {"xlabel": "#4"}}
        monkeypatch.setitem(sys.modules, "sfi", _FakeSfi(
            {"_qg_1": json.dumps(g)}))
        line = dr._dash_stata_tick_plan("_qg_1", json.dumps(
            {"date": "%td"}))
        reqs = line.split(";")
        # Flipped (WP-34 TR-4): a layer's token carries the variables its
        # rows need, so a row with a missing y counts for no axis.
        assert "4 d - date:__dashq1:close+date" in reqs \
            and "5 - - close:__dashq1:close+date" in reqs
        assert re.fullmatch(r"[A-Za-z0-9_ ;:+-]+", line)
        assert dr._dash_stata_tick_plan("_qg_9", "{}") == ""

    def test_take(self, monkeypatch):
        """_dash_stata_ticks_take reads the r() an answer left, in full
        precision, into [lo, hi, n, unit, ticks] entries."""
        p = _P["P4"]
        r = p["routine"]
        sc = {"r(ng)": 2.0, "r(lo1)": p["data_lo"], "r(hi1)": p["data_hi"],
              "r(min1)": r["min"], "r(max1)": r["max"],
              "r(delta1)": r["delta"], "r(n1)": r["n"],
              "r(lo2)": None, "r(hi2)": None}
        monkeypatch.setitem(sys.modules, "sfi", _FakeSfi(scalars=sc))
        got = json.loads("[" + dr._dash_stata_ticks_take("4 - - price:")
                         + "]")
        assert got == [[p["data_lo"], p["data_hi"], 4, "",
                        p["drawn_ticks"]]]
        assert dr._dash_stata_ticks_take("4 z - price:") == ""
        assert dr._dash_stata_ticks_take("") == ""


def _efix(ax):
    from bokeh.models import CustomJSTicker
    t = ax.ticker
    if not isinstance(t, CustomJSTicker):
        return None
    fx = dict(t.args or {}).get("efix")
    return sorted(float(v) for v in fx.ticks) if fx is not None else None


class TestCountTickAndMinmaxMove:
    """D-45c: twoway draws every graph over the rows it keeps, so
    ``ytick(#N)`` and ``ylabel(minmax)`` follow a filter move as ``#N``
    does; both modes, and back."""

    @pytest.mark.parametrize("mode", MODES)
    def test_xtick(self, tmp_path, mode):
        p = _P["P4"]
        obj, figs = _build(tmp_path, mode, _plots("P4"), {"ytick": "#4"},
                           filt="pv")
        lo, hi = p["data_lo"], p["data_hi"]
        assert _efix(_axis(figs[0], "y")) == \
            dr._dash_axis_count_ticks(lo, hi, 4)
        figs = _move(mode, obj, (lo, 10000.0))
        khi = float(_DF.loc[_DF["pv"] <= 10000.0, "price"].max())
        assert _efix(_axis(figs[0], "y")) == \
            dr._dash_axis_count_ticks(lo, khi, 4)
        figs = _move(mode, obj, (lo, hi))
        assert _efix(_axis(figs[0], "y")) == \
            dr._dash_axis_count_ticks(lo, hi, 4)

    @pytest.mark.parametrize("mode", MODES)
    def test_minmax(self, tmp_path, mode):
        p = _P["P4"]
        obj, figs = _build(tmp_path, mode, _plots("P4"),
                           {"ylabel": "minmax"}, filt="pv")
        lo, hi = p["data_lo"], p["data_hi"]
        assert _major_ticks(_axis(figs[0], "y")) == [lo, hi]
        figs = _move(mode, obj, (lo, 10000.0))
        khi = float(_DF.loc[_DF["pv"] <= 10000.0, "price"].max())
        assert _major_ticks(_axis(figs[0], "y")) == [lo, khi]

    def test_tags(self):
        assert dr._DASH_COUNT_TICK_TAG == "dash_count_tick:"
        assert dr._DASH_MINMAX_TAG == "dash_minmax"


def _marker_ticks(lo, hi):
    """Ticks no model gives: they can only come from the table."""
    return [lo, lo + 0.37 * (hi - lo), hi]


class TestPanels:
    @pytest.mark.parametrize("mode", MODES)
    def test_each_panel(self, tmp_path, mode):
        """by(g, xrescale): each panel's x axis takes the entry for its
        own rows' range (dash.ado asks each by() group)."""
        halves = [_DF.loc[_DF["g"] == k, "price"] for k in (0.0, 1.0)]
        # Flipped (WP-34 AX-2): twoway's by() styles set xlabels(#4) as
        # well as ylabels(#4), so a by() panel's x axis looks up count 4.
        table = [[float(h.min()), float(h.max()), 4, "",
                  _marker_ticks(float(h.min()), float(h.max()))]
                 for h in halves]
        _r, figs = _build(tmp_path, mode, [_L("scatter", "obs", "price")],
                          {"by": "g, xrescale"}, table)
        got = [_major_ticks(_axis(f, "x")) for f in figs]
        assert got == [e[4] for e in table]


class TestSecondaryAxes:
    @pytest.mark.parametrize("mode", MODES)
    def test_y2(self, tmp_path, mode):
        """yaxis(2) takes the entry for its own layers' range."""
        lo, hi = float(_DF["trunk"].min()), float(_DF["trunk"].max())
        e = [lo, hi, 5, "", _marker_ticks(lo, hi)]
        _r, figs = _build(tmp_path, mode, [
            _L("scatter", "price", "obs"),
            _L("scatter", "trunk", "obs", yaxis="2")], {}, [e])
        right = [a for a in figs[0].right if hasattr(a, "ticker")]
        assert right and _major_ticks(right[0]) == e[4]


class TestTickMinmaxAndSharedTicks:
    """D15 follow-up: xtick(minmax) follows a move as xlabel(minmax)
    does, and a shared by() letter's xtick(#N) with no count label is
    placed once over every panel's kept rows, in both modes."""

    @pytest.mark.parametrize("mode", MODES)
    def test_tick_minmax(self, tmp_path, mode):
        p = _P["P4"]
        obj, figs = _build(tmp_path, mode, _plots("P4"),
                           {"ytick": "minmax"}, filt="pv")
        lo, hi = p["data_lo"], p["data_hi"]
        assert _efix(_axis(figs[0], "y")) == [lo, hi]
        figs = _move(mode, obj, (lo, 10000.0))
        khi = float(_DF.loc[_DF["pv"] <= 10000.0, "price"].max())
        assert _efix(_axis(figs[0], "y")) == [lo, khi]
        # The marks drawn are efix's (the page writes efix, not extra).
        assert _axis(figs[0], "y").ticker.minor_code == dr._DASH_TICK_EFIX_JS

    @pytest.mark.parametrize("mode", MODES)
    def test_shared_by_letter(self, tmp_path, mode):
        p = _P["P4"]
        lo = p["data_lo"]
        obj, figs = _build(tmp_path, mode, _plots("P4"),
                           {"by": "g", "ylabel": "0(5000)20000",
                            "ytick": "#4"}, filt="pv")
        assert len(figs) == 2
        figs = _move(mode, obj, (lo, 10000.0))
        khi = float(_DF.loc[_DF["pv"] <= 10000.0, "price"].max())
        want = dr._dash_axis_count_ticks(lo, khi, 4)
        assert [_efix(_axis(f, "y")) for f in figs] == [want, want]
