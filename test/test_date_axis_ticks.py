"""WP-30 S44 (P1.3b): default %td-%ty date axes take twoway's calendar ticks.

twoway ticks a date axis with no label rule as ``#5`` by _tsnatscale over
the data; dash models _tsnatscale (``_dash_tsnatscale_ticks``) and its
saved page runs a JavaScript port of the model (``_DASH_TSNATSCALE_JS``,
proved equal in test_natscale_js.py).  Here: every default date axis,
second date axis, date beside a number and by() date graph of
test/fixtures/date_axes_truth.json (scripts/extract_date_axes_truth.do)
in both modes, at build and after a filter move, and on zoom.  The data
are synthetic with each probe's measured range: the ticks depend on the
range alone.

While iterating: ``python3 -m pytest test/test_date_axis_ticks.py -q``.
"""
import json
import math
import os
import random
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
with open(os.path.join(_HERE, "fixtures", "date_axes_truth.json"),
          encoding="utf-8") as _fh:
    _D = json.load(_fh)
_P = _D["probes"]

#: Each probe's layers, options, axis variable's kind and the axis read.
_BUILD = {
    "TD": ([_L("line", "close", "date")], {}, "td", "x"),
    "N5": ([_L("line", "close", "date")], {"xlabel": "#5"}, "td", "x"),
    "TW": ([_L("scatter", "close", "w")], {}, "tw", "x"),
    "TM": ([_L("scatter", "close", "m")], {}, "tm", "x"),
    "TQ": ([_L("scatter", "close", "q")], {}, "tq", "x"),
    "TH": ([_L("scatter", "close", "h")], {}, "th", "x"),
    "TY": ([_L("line", "close", "y")], {}, "ty", "x"),
    "Y2": ([_L("line", "close", "date"),
            _L("line", "volume", "date", xaxis="2")], {}, "td", "x2"),
    "MIX": ([_L("scatter", "close", "date"), _L("scatter", "close", "obs")],
            {}, "su:td", "x"),
    "MIXN": ([_L("scatter", "close", "date"),
              _L("scatter", "close", "obs")], {"xlabel": "#5"}, "su:td",
             "x"),
    "BY": ([_L("line", "close", "date")], {"by": "g"}, "td", "x"),
}
#: The probes where dash's MOVE-TIME model draws twoway's ticks; at build
#: every probe is Stata's own (WP-31 D15).
#: (The model agrees with _tsnatscale on 52-98% of ranges, A8; these specs
#: carry no stata_ticks, so they draw the model: test_stata_ticks.py draws
#: Stata's.)
_MODEL_AGREES = {"TD", "N5", "TW", "TM", "TQ", "TY", "Y2", "MIX", "MIXN", "BY",
           "IF1", "IF3"}
_FMT = {"date": "%td", "w": "%tw", "m": "%tm", "q": "%tq", "h": "%th",
        "y": "%ty"}
_UNIT = {"td": "d", "tw": "w", "tm": "m", "tq": "q", "th": "h", "ty": "y"}


def _col(lo, hi, n, extra=()):
    v = np.unique(np.round(np.r_[np.linspace(lo, hi, n), list(extra)]))
    return np.resize(v, n)


def _frame():
    """50 rows whose columns span the probes' measured ranges; ``v`` and
    ``mv`` are plain copies of ``date`` and ``m`` for the range filters."""
    n = 50
    p = _P
    date = np.sort(_col(p["TD"]["data_lo"], p["TD"]["data_hi"], n,
                        (p["IF1"]["data_hi"], p["IF2"]["data_hi"])))
    df = pd.DataFrame({
        "date": date,
        "w": np.sort(_col(p["TW"]["data_lo"], p["TW"]["data_hi"], n)),
        "m": np.sort(_col(p["TM"]["data_lo"], p["TM"]["data_hi"], n)),
        "q": np.sort(_col(p["TQ"]["data_lo"], p["TQ"]["data_hi"], n)),
        "h": np.sort(_col(p["TH"]["data_lo"], p["TH"]["data_hi"], n)),
        "y": np.sort(_col(p["TY"]["data_lo"], p["TY"]["data_hi"], n)),
        "obs": np.sort(_col(1.0, 248.0, n)),
        "close": 1100.0 + 5.0 * np.arange(n),
        "volume": 9000.0 + 50.0 * np.arange(n),
        "g": (np.arange(n) % 2).astype(float)})
    for c in ("date", "w", "m", "q", "h", "y"):
        assert df[c].min() == p[{"date": "TD", "w": "TW", "m": "TM",
                                 "q": "TQ", "h": "TH", "y": "TY"}[c]
                                ]["data_lo"]
    df["v"] = df["date"]
    df["mv"] = df["m"]
    return df


_DF = _frame()


def _units(ticks, kind):
    """Ticks on the Bokeh axis (epoch ms, or Stata units for "su:") as the
    variable's Stata values."""
    if kind.startswith("su:"):
        return [float(t) for t in ticks]
    return [round(dr._dash_unix_ms_to_unit(t, _UNIT[kind]), 6)
            for t in ticks]


def _axis(fig, which):
    side, name = {"x": ("below", "default"), "x2": ("above", "x2")}[which]
    return [a for a in getattr(fig, side) if hasattr(a, "ticker")
            and getattr(a, "x_range_name", "default") == name][0]


def _build(tmp_path, mode, plots, go, filt=None):
    spec = _spec(plots, formats=_FMT, graph_options=go,
                 filters=[_filter("range", filt)] if filt else None)
    if mode == "saved":
        r, _w = _saved(tmp_path, spec, _DF)
        return r, list(r.figures.values())
    doc, _w = _served(tmp_path, spec, _DF)
    return doc, tda.tb._panels(tda.tb._figs_of(doc.roots))


def _panels(figs):
    out = [f for f in figs if f.renderers]
    return out


def _check(pid, figs, which, kind, lo, hi, bad):
    """Every drawn panel's *which* axis against the model over *lo*-*hi*
    and, where the model agrees, against twoway's list."""
    want = dr._dash_axis_count_ticks(lo, hi, 5, kind)
    rec = _P[pid].get(which) or _P[pid]["panels"][0][which]
    for f in _panels(figs):
        ax = _axis(f, which)
        t = _major_ticks(ax)
        if t != want or list(ax.ticker.minor_ticks or []) != []:
            bad.append((pid, "model", t, want))
        if pid in _MODEL_AGREES and _units(t, kind) != rec["list"]:
            bad.append((pid, "twoway", _units(t, kind), rec["list"]))


def _bounds(pid, kind):
    """The axis's data range on the Bokeh axis."""
    p = _P[pid]
    lo, hi = p["data_lo"], p["data_hi"]
    if pid.startswith("MIX"):
        # obs from 1 beside the dates in Stata units.
        return 1.0, _P["TD"]["data_hi"]
    k = kind if not kind.startswith("su:") else kind[3:]
    conv = dr._stata_dates_to_datetime(pd.Series([lo, hi]), k)
    return tuple(float(v) for v in conv.astype("int64"))


class TestTheFixture:
    def test_it_is_stamped(self):
        assert all(_D["_meta"].get(k) for k in (
            "stata_version", "born_date", "dash_commit", "extracted"))
        assert all(p["rc"] == 0 for p in _P.values())
        # P07: `line close date' on sp500 ticks quarterly; #5 is the default.
        assert _P["TD"]["x"]["list"] == [14976.0, 15066.0, 15157.0, 15249.0,
                                         15341.0]
        assert _P["N5"]["x"]["list"] == _P["TD"]["x"]["list"]


class TestTheModelIsUnchanged:
    def test_the_pair_is_cpythons_order(self):
        rnd = random.Random(4405)
        xs = [rnd.uniform(-700000, 3000000) for _ in range(200000)]
        xs += [float(v) for v in range(-20, 20)] + [-0.5, -1.5, 7.5]
        bad = [x for x in xs if dr._dash_ts_pair(x)
               != tuple({math.floor(x), math.ceil(x)})]
        assert not bad, bad[:5]


class TestDefaultDateAxes:
    """TD, N5, TW-TY, Y2 (x2), MIX/MIXN (Stata units) and BY: each axis is
    a FixedTicker with no minor ticks holding the model's #5 over its data;
    where the model agrees with twoway, twoway's ticks."""

    @pytest.mark.parametrize("mode", MODES)
    def test_build(self, tmp_path, mode):
        bad = []
        for i, (pid, (plots, go, kind, which)) in enumerate(_BUILD.items()):
            sub = tmp_path / str(i)
            sub.mkdir()
            _r, figs = _build(sub, mode, plots, go)
            lo, hi = _bounds(pid, kind)
            _check(pid, figs, which, kind, lo, hi, bad)
        assert not bad, bad


class TestTheRangeOption:
    """Measured 08oct2026 (StataNow 19.5): a DEFAULT date axis is ticked
    over its data alone and range() widens only the scale -- `twoway (line
    close date) (line d2 date, yaxis(2)), yscale(range(14900 15500)
    axis(2))' keeps 14976(quarterly)15341 on 14900-15500, and a date beside
    a number under xscale(range(-3000 20000)) keeps 0 3653 ... 14610; under
    #5 the range joins the ticks (14884 ... 15522; -3652 ... 18263)."""

    @pytest.mark.parametrize("mode", MODES)
    def test_default_ticks_the_data(self, tmp_path, mode):
        bad = []
        lo, hi = _bounds("TD", "td")
        for i, (go, want) in enumerate((
                ({"xscale": "range(14000 16000)"},
                 dr._dash_axis_count_ticks(lo, hi, 5, "td")),
                ({"xscale": "range(14000 16000)", "xlabel": "#5"},
                 dr._dash_axis_count_ticks(
                     dr._dash_units_to_axis([14000], "td")[0],
                     dr._dash_units_to_axis([16000], "td")[0], 5, "td")))):
            sub = tmp_path / str(i)
            sub.mkdir()
            _r, figs = _build(sub, mode, [_L("line", "close", "date")], go)
            t = _major_ticks(_axis(figs[0], "x"))
            h = dr._dash_range_hull(figs[0].x_range)
            if t != want or h[0] > dr._dash_units_to_axis([14000], "td")[0]:
                bad.append((go, t, want, h))
        assert not bad, bad

    def test_the_kinds(self):
        assert all(dr._dash_ts_kind(k) for k in dr._DASH_TS_UNITS)
        assert all(dr._dash_ts_kind("su:" + k) for k in dr._DASH_TS_UNITS)
        assert not any(dr._dash_ts_kind(k) for k in (
            None, "log", "tc", "tC", "su:", "su:tc", "su:x", 5))


#: The moves: (probe, filter column, kept range) -- each IF probe's subset.
_MOVES = (("IF1", "v", (_P["IF1"]["data_lo"], _P["IF1"]["data_hi"])),
          ("IF2", "v", (_P["IF2"]["data_lo"], _P["IF2"]["data_hi"])),
          ("IF3", "mv", (_P["IF3"]["data_lo"], _P["IF3"]["data_hi"])))


def _move(mode, obj, value):
    if mode == "saved":
        return tda._move_saved(obj, "RangeSlider", value)
    return tda._move_served(obj, "RangeSlider", value)


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", MODES)
    def test_case(self, tmp_path, mode):
        """After each IF probe's move the axis re-ticks over the kept rows
        (the saved page through the JS port, the served app in Python)."""
        bad = []
        built = {}
        for pid, col, kept in _MOVES:
            var = "date" if col == "v" else "m"
            kind = _FMT[var][1:]
            if col not in built:
                sub = tmp_path / col
                sub.mkdir()
                built[col] = _build(sub, mode,
                                    [_L("scatter", "close", var)], {}, col)[0]
            figs = _move(mode, built[col], kept)
            _check(pid, figs, "x", kind, *_bounds(pid, kind), bad)
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_empty_has_no_ticks(self, tmp_path, mode):
        """A move that keeps no row leaves the date axis no tick (WP-32)."""
        # Flipped: keeping the last ticks was wrong because twoway draws a
        # scale with nothing on it empty, with no tick (BUGS.md "Found by
        # the move-parity extension: axes of degenerate or emptied layers
        # after a move").
        obj, figs = _build(tmp_path, mode, [_L("scatter", "close", "date")],
                           {}, "v")
        assert _major_ticks(_axis(figs[0], "x"))
        lo = _P["TD"]["data_lo"]
        figs = _move(mode, obj, (lo + 0.25, lo + 0.75))
        assert _major_ticks(_axis(figs[0], "x")) == []


class TestZoom:
    def test_date_zoom(self, tmp_path):
        """The zoom callback ticks the visible range by the model; back at
        the reset extent it writes the data's ticks."""
        r, figs = _build(tmp_path, "saved", [_L("line", "close", "date")],
                         {})
        fig = figs[0]
        rng = fig.x_range
        cb = tda._zoom_cb(rng)
        lo, hi = float(rng.start), float(rng.end)
        mid = (lo + hi) / 2.0
        home = _major_ticks(_axis(fig, "x"))
        rng.start, rng.end = lo, mid
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        assert _major_ticks(_axis(fig, "x")) == dr._dash_axis_count_ticks(
            lo, mid, 5, "td")
        rng.start, rng.end = rng.reset_start, rng.reset_end
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        assert _major_ticks(_axis(fig, "x")) == home


class TestTheServedCopy:
    def test_names_and_constant(self, tmp_path):
        spec = _spec([_L("line", "close", "date")], formats=_FMT,
                     filters=[_filter("range", "v")])
        from test_date_range import _write
        sp, dp = _write(tmp_path, spec, _DF)
        ap = os.path.join(str(tmp_path), "app.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert re.search(r"^def _dash_ts_pair\(", src, re.M)
        assert re.search(r"^_DASH_TSNATSCALE_JS = ", src, re.M)
        for s in (dr._DASH_AXIS_FINISH_JS, dr._FILTER_JS):
            assert s.count("function dash_tsnatscale(") == 1
            assert "__DASH_" not in s and "@@DASH" not in s
        js = dr._DASH_TSNATSCALE_JS
        # WP-30 P1.17b: 15,682 -> 16,798 with %td weekly steps on %tw week
        # starts (dash_ts_day_week).
        assert len(js) <= 17000
        for word in ("eval(", "Function(", "document", "window"):
            assert word not in js, word


class TestTheHelp:
    def test_the_rule_is_documented(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        assert "DatetimeTicker" not in text
        for words in ("calendar rule", "58-66%", "98%",
                      "re-ticks after a filter move and on zoom"):
            assert words in text, words
