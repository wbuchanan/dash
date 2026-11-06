"""WP-44 section 44-04: date axes as twoway draws them (AX-18, DG-6, DG-4).

twoway labels an axis in the format of the layer its format comes from
(the first layer of the group whose first layer comes last,
:func:`dash_render._dash_axis_tick_formats`); when that layer is a fit,
kdensity, lpoly or an immediate type, the format is ``%9.0g`` and a date
variable's axis is labelled with its numbers (``kdensity date`` on sp500:
15000 ... 15400).  A log scale on a date axis is drawn, ticked and
labelled as the linear date axis is.  Truth:
test/fixtures/date_axis_rule_truth.json (scripts/extract_date_axis_rule_truth.do).

While iterating: ``python3 -m pytest test/test_date_axes_p9.py -q -n0``.
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
import test_default_axes as tda  # noqa: E402
from bokeh.models import DatetimeAxis, LogAxis  # noqa: E402
from conftest import drawn_renderers  # noqa: E402
from test_by_scales import _major_ticks  # noqa: E402
from test_date_range import _filter, _saved, _served, _spec  # noqa: E402
from test_display_format_sites import js_texts  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "date_axis_rule_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_FMT = {"date": "%td", "d2": "%td", "m": "%tm", "v": "%9.0g"}


def _frame():
    """sp500's ranges: date 14977-15340 (02jan2001-31dec2001), close and
    open 965.8-1373.7, m 492-503 (%tm); ``v`` a plain copy of date for a
    range filter, d2 date + 30."""
    n = 60
    date = np.round(np.linspace(14977.0, 15340.0, n))
    return pd.DataFrame({
        "date": date, "d2": date + 30.0, "v": date,
        "close": np.linspace(965.8, 1373.7, n),
        "open": np.linspace(1373.7, 965.8, n),
        "m": np.round(np.linspace(492.0, 503.0, n))})


_DF = _frame()


def _L(t, y=None, x=None, **o):
    p = {"type": t, "options": dict(o)}
    if y is not None:
        p["yvar"] = y
    if x is not None:
        p["xvar"] = x
    return p


def _U(t, var, **o):
    return {"type": t, "var": var, "options": dict(o)}


_SC = _L("scatter", "close", "date")

#: Each ax18 key's dash layers (the fixture's command, layer by layer).
_FIRST = {
    **{f"ax18.first_{t}": [_L(t, "close", "date"), _SC]
       for t in ("lfit", "qfit", "lfitci", "qfitci", "lpoly", "lpolyci",
                 "fpfit", "fpfitci", "lowess", "mspline", "mband")},
    "ax18.first_kdensity": [_U("kdensity", "date"), _SC],
    "ax18.first_histogram": [_U("histogram", "date"), _SC],
    "ax18.first_scatteri": [{"type": "scatteri", "options": {},
                             "values": [[1300.0, 15400.0]]}, _SC],
    "ax18.first_pci": [{"type": "pci", "options": {},
                        "values": [[1300.0, 15200.0, 1400.0, 15300.0]]},
                       _SC],
    "ax18.first_pcarrowi": [{"type": "pcarrowi", "options": {},
                             "values": [[1300.0, 15200.0, 1400.0,
                                         15300.0]]}, _SC],
    "ax18.first_function": [{"type": "function", "expr": "1300",
                             "options": {"range": "15000 15400"}}, _SC],
    "ax18.scatter_first": [_SC, _L("lfit", "close", "date")],
    "ax18.line_first": [_L("line", "close", "date"),
                        _L("lfit", "close", "date")],
    "ax18.lfit_range": [_L("lfit", "close", "date",
                           range="14900 15400"), _SC],
    "ax18.kdensity_alone": [_U("kdensity", "date")],
    "ax18.lfit_alone": [_L("lfit", "close", "date")],
    "ax18.ygrp_lfit_second": [_SC, _L("lfit", "open", "date", yaxis="2")],
    "ax18.ygrp_lfit_first": [_L("lfit", "close", "date"),
                             _L("scatter", "open", "date", yaxis="2")],
}

#: The keys whose y axis carries the date (the axis read is y).
_Y_KEYS = {
    "ax18.y_lfit": [_L("lfit", "date", "close"),
                    _L("scatter", "date", "close")],
    "ax18.y_scatter": [_L("scatter", "date", "close"),
                       _L("lfit", "date", "close")],
    "ax18.hz": [_U("kdensity", "date", horizontal="horizontal")],
}

#: The log keys: (layers, graph options, the axis read).
_LOG = {
    "ax18.log_x_td": ([_L("line", "close", "date")], {"xscale": "log"},
                      "x"),
    "ax18.log_y_td": ([_L("scatter", "date", "close")], {"yscale": "log"},
                      "y"),
    "ax18.log_x4_td": ([_L("line", "close", "date")],
                       {"xscale": "log", "xlabel": "#4"}, "x"),
    "ax18.log_x_tm": ([_L("line", "close", "m")], {"xscale": "log"}, "x"),
    "ax18.log_y_tm": ([_L("scatter", "m", "close")], {"yscale": "log"},
                      "y"),
    "ax18.log_x4_tm": ([_L("line", "close", "m")],
                       {"xscale": "log", "xlabel": "#4"}, "x"),
}


def _units_of(label):
    """A twoway date label's Stata value: ``01apr2001`` (%td), ``2001m4``
    (%tm)."""
    m = re.fullmatch(r"(\d{4})m(\d{1,2})", label)
    if m:
        return (int(m.group(1)) - 1960) * 12 + int(m.group(2)) - 1
    d = pd.Timestamp(label)
    return float((d - pd.Timestamp("1960-01-01")).days)


def _build(tmp_path, mode, plots, go=None, filt=None, table=None):
    spec = _spec(plots, formats=_FMT, graph_options=go or {},
                 filters=[_filter("range", filt)] if filt else None)
    if table:
        spec["build_options"]["stata_ticks"] = table
    if mode == "saved":
        r, w = _saved(tmp_path, spec, _DF)
        return r, list(r.figures.values()), w
    doc, w = _served(tmp_path, spec, _DF)
    return doc, tda.tb._panels(tda.tb._figs_of(doc.roots)), w


def _axis(fig, which):
    side = {"x": "below", "y": "left", "x2": "above"}[which]
    rng = "y_range_name" if which == "y" else "x_range_name"
    name = "x2" if which == "x2" else "default"
    return [a for a in getattr(fig, side) if hasattr(a, "ticker")
            and getattr(a, rng, "default") == name][0]


def _labels(ax):
    """What the axis writes at each of its ticks, under node."""
    t = list(_major_ticks(ax) or [])
    return js_texts(ax.formatter, t, "tick") if t else []


def _want(key, which):
    """twoway's label texts on *which* (x below, y left; x2 above)."""
    row = _T[key]
    if which == "x2":
        pr = row["plotregion"]
        return [t["text"] for t in row["texts"]
                if t["y"] is not None and t["y"] < pr["top"]
                and re.fullmatch(r"[0-9a-z.]+", t["text"])]
    want = row[which + "axis"]["labels"]
    return list(reversed(want)) if which == "y" else want


def _is_date(texts):
    return any(re.search(r"[a-z]", t) for t in texts)


class TestTheFixture:
    def test_it_is_stamped(self):
        assert all(_T["_meta"].get(k) for k in (
            "stata_version", "born_date", "dash_commit", "extracted"))
        # kdensity first: twoway's numbers; scatter first: dates.
        assert _T["ax18.first_kdensity"]["xaxis"]["labels"] == [
            "15000", "15100", "15200", "15300", "15400"]
        assert _T["ax18.scatter_first"]["xaxis"]["labels"][0] == "01jan2001"

    def test_the_member_list_is_the_fixtures(self):
        """A type is a number-first type exactly when twoway labels the
        date axis with numbers when it comes first."""
        got = set()
        for key, row in _T.items():
            m = re.fullmatch(r"ax18\.first_([a-z]+)", key)
            if m and not _is_date(row["xaxis"]["labels"]):
                got.add(m.group(1))
        assert got == set(dr._DASH_NUMBER_FIRST_TYPES)


class TestNumberFirst:
    @pytest.mark.parametrize("mode", MODES)
    def test_each_type(self, tmp_path, mode):
        """Each first-layer probe's x labels are twoway's: numbers on a
        numeric axis where twoway writes numbers, dates on a date axis
        where it writes dates."""
        bad = []
        for i, (key, plots) in enumerate({**_FIRST, **_Y_KEYS}.items()):
            which = "y" if key in _Y_KEYS else "x"
            sub = tmp_path / str(i)
            sub.mkdir()
            _o, figs, _w = _build(sub, mode, plots)
            ax = _axis(figs[0], which)
            want = _want(key, which)
            got = _labels(ax)
            if got != want or isinstance(ax, DatetimeAxis) != _is_date(want):
                bad.append((key, type(ax).__name__, got, want))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_scatter_first_keeps_dates(self, tmp_path, mode):
        _o, figs, _w = _build(tmp_path, mode, _FIRST["ax18.scatter_first"])
        ax = _axis(figs[0], "x")
        assert isinstance(ax, DatetimeAxis)
        assert _labels(ax) == _want("ax18.scatter_first", "x")

    @pytest.mark.parametrize("mode", MODES)
    def test_second_axis(self, tmp_path, mode):
        """`(scatter close date) (lfit open date, xaxis(2))': axis 1 keeps
        its dates; axis 2, the lfit's alone, is labelled with numbers."""
        plots = [_SC, _L("lfit", "open", "date", xaxis="2")]
        _o, figs, _w = _build(tmp_path, mode, plots)
        a1, a2 = _axis(figs[0], "x"), _axis(figs[0], "x2")
        assert isinstance(a1, DatetimeAxis)
        assert _labels(a1) == _want("ax18.y2_first", "x")
        assert not isinstance(a2, DatetimeAxis)
        assert _labels(a2) == _want("ax18.y2_first", "x2")


class TestLogDate:
    @pytest.mark.parametrize("mode", MODES)
    def test_log_with_date_labels(self, tmp_path, mode):
        """xscale(log)/yscale(log) on a date axis: a log axis, twoway's
        date labels, and no warning."""
        bad = []
        for i, (key, (plots, go, which)) in enumerate(_LOG.items()):
            sub = tmp_path / str(i)
            sub.mkdir()
            # Stata's answer over the axis's rows, as the export writes it
            # (twoway's ticks, read off its labels): the model's _tsnatscale
            # #4 over 492-503 ends at 504 where Stata's ends at 501.
            var = "m" if key.endswith("_tm") else "date"
            n = 4 if "_x4_" in key else 5
            table = [[float(_DF[var].min()), float(_DF[var].max()), n,
                      "m" if var == "m" else "d",
                      [_units_of(t) for t in _want(key, which)]]]
            _o, figs, w = _build(sub, mode, plots, go, table=table)
            ax = _axis(figs[0], which)
            got = _labels(ax)
            want = _want(key, which)
            warned = [m for m in w if "meaningless" in m]
            if not isinstance(ax, LogAxis) or got != want or warned:
                bad.append((key, type(ax).__name__, got, want, warned))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_second_axis_log(self, tmp_path, mode):
        """yscale(log axis(2)) on a second axis of dates: a log axis that
        writes dates, the first axis's dates kept, and no warning."""
        plots = [_SC, _L("scatter", "d2", "date", yaxis="2")]
        _o, figs, w = _build(tmp_path, mode, plots, {"yscale2": "log"})
        fig = figs[0]
        y2 = [a for a in fig.right if getattr(a, "y_range_name", "") == "y2"]
        assert len(y2) == 1 and isinstance(y2[0], LogAxis)
        got = _labels(y2[0])
        assert got and all(re.fullmatch(r"\d\d[a-z]{3}200[12]", t)
                           for t in got), got
        assert isinstance(_axis(fig, "x"), DatetimeAxis)
        assert not [m for m in w if "meaningless" in m]

    @pytest.mark.parametrize("mode", MODES)
    def test_every_layer_in_units(self, tmp_path, mode):
        """On a log date axis every layer's date coordinates are drawn in
        Stata's days: an rarea's x and both ends of a pcspike."""
        plots = [{"type": "rarea", "yvar1": "close", "yvar2": "open",
                  "xvar": "date", "options": {}},
                 {"type": "pcspike", "y1var": "close", "x1var": "date",
                  "y2var": "open", "x2var": "d2", "options": {}}]
        _o, figs, _w = _build(tmp_path, mode, plots, {"xscale": "log"})
        fig = figs[0]
        assert isinstance(_axis(fig, "x"), LogAxis)
        seen = []
        for r in drawn_renderers(fig):
            g = getattr(r, "glyph", None)
            for prop in ("x", "x0", "x1", "x2"):
                spec = getattr(g, prop, None) if g is not None else None
                if spec is None or isinstance(spec, (int, float)):
                    continue
                if dr._dash_spec_field(spec):
                    seen.append((type(g).__name__, prop,
                                 dr._dash_spec_units(spec)))
        assert seen and all(k == "td" for _g, _p, k in seen), seen

    @pytest.mark.parametrize("mode", MODES)
    def test_move(self, tmp_path, mode):
        """After a filter move a log date axis is re-ticked over the kept
        rows on the date's calendar, and still writes dates."""
        obj, figs, _w = _build(tmp_path, mode, [_L("line", "close", "date")],
                               {"xscale": "log"}, "v")
        kept = (15050.0, 15250.0)
        if mode == "saved":
            figs = tda._move_saved(obj, "RangeSlider", kept)
        else:
            figs = tda._move_served(obj, "RangeSlider", kept)
        ax = _axis(figs[0], "x")
        lo = float(_DF["date"][_DF["date"] >= kept[0]].min())
        hi = float(_DF["date"][_DF["date"] <= kept[1]].max())
        want = dr._dash_axis_count_ticks(lo, hi, 5, "su:td")
        assert isinstance(ax, LogAxis)
        assert _major_ticks(ax) == want
        assert all(re.fullmatch(r"\d\d[a-z]{3}2001", t) for t in _labels(ax))


# ---------------------------------------------------------------------------
# DG-6: %tC ticks in twoway's raw units
# ---------------------------------------------------------------------------

with open(os.path.join(_HERE, "fixtures", "data_locale_truth.json"),
          encoding="utf-8") as _fh:
    _LOC = json.load(_fh)
_LEAP = list(_LOC["leap.table"])


def _Cofc(t):
    """Stata's Cofc() of %tc milliseconds *t*, from the measured table (a
    local inverse, independent of dash_render): one second per leap second
    whose instant is at or before *t*."""
    return t + 1000.0 * sum(1 for L in _LEAP if L <= t)


def _tc_frame(start, step, n=30):
    t = [start + i * step for i in range(n)]
    return pd.DataFrame({"t": t, "tC": [_Cofc(v) for v in t],
                         "tv": t, "y": [float(i + 1) for i in range(n)]})


#: dg6 keys: (frame, the x variable).  T04/T05: 30 days from
#: tc(01jan2001 00:00:00); *_2016: 30 ten-second steps from
#: tc(31dec2016 23:58:00), across the 2016 leap second.
_TC_FRAMES = {
    "dg6.T04": (_tc_frame(1293926400000.0, 86400000.0), "t"),
    "dg6.T05": (_tc_frame(1293926400000.0, 86400000.0), "tC"),
    "dg6.tc_2016": (_tc_frame(1798847880000.0, 10000.0), "t"),
    "dg6.tC_2016": (_tc_frame(1798847880000.0, 10000.0), "tC"),
}
_TC_FMT = {"t": "%tc", "tC": "%tC", "tv": "%9.0g"}


def _tc_build(tmp_path, mode, df, var, filt=None):
    spec = _spec([_L("scatter", "y", var)], formats=_TC_FMT,
                 filters=[_filter("range", filt)] if filt else None)
    if mode == "saved":
        r, _w = _saved(tmp_path, spec, df)
        return r, list(r.figures.values())
    doc, _w = _served(tmp_path, spec, df)
    return doc, tda.tb._panels(tda.tb._figs_of(doc.roots))


class TestTcTicks:
    @pytest.mark.parametrize("mode", MODES)
    def test_labels_equal_twoway(self, tmp_path, mode):
        """A %tC axis is ticked over its raw values and labelled to the
        second as twoway labels it; a %tc axis is unchanged."""
        bad = []
        for i, (key, (df, var)) in enumerate(_TC_FRAMES.items()):
            sub = tmp_path / str(i)
            sub.mkdir()
            _o, figs = _tc_build(sub, mode, df, var)
            got = _labels(_axis(figs[0], "x"))
            if got != _want(key, "x"):
                bad.append((key, got, _want(key, "x")))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_after_a_move(self, tmp_path, mode):
        """After a filter move the %tC axis is ticked over the kept rows'
        raw values, as twoway ticks them."""
        df, var = _TC_FRAMES["dg6.T05"]
        obj, _figs = _tc_build(tmp_path, mode, df, var, "tv")
        kept = (float(df["t"][5]), float(df["t"][20]))
        if mode == "saved":
            figs = tda._move_saved(obj, "RangeSlider", kept)
        else:
            figs = tda._move_served(obj, "RangeSlider", kept)
        raw = [_Cofc(v) for v in df["t"] if kept[0] <= v <= kept[1]]
        epoch = dr._STATA_EPOCH_UNIX_MS
        want = [v - 1000.0 * sum(1 for k, L in enumerate(_LEAP)
                                 if v >= L + 1000.0 * (k + 1)) + epoch
                for v in dr._dash_natscale_ticks(min(raw), max(raw), 5)]
        assert _major_ticks(_axis(figs[0], "x")) == want

    def test_inverse_round_trip(self):
        """dash's two directions against every measured leap.* pair, in
        Python and in the page's JavaScript."""
        pairs = (list(_LOC["leap.roundtrip"]) + list(_LOC["leap.after_midnight"]))
        tC = [p[0] for p in pairs]
        tc = [p[1] for p in pairs]
        assert [_Cofc(v) for v in tc] == tC
        assert list(dr._dash_tC_from_tc(tc)) == tC
        assert list(dr._dash_tc_from_tC(tC)) == tc
        inside = list(_LOC["leap.inside"])
        assert list(dr._dash_tc_from_tC([p[0] for p in inside])) == [
            p[1] for p in inside]
        import js_runner
        if js_runner.NODE is None:
            pytest.fail("node is required for the page's leap-second code")
        src = (dr._DASH_LEAP_SECONDS_JS
               + "process.stdout.write(JSON.stringify([%s.map(dash_tC_from_tc),"
               " %s.map(dash_tc_from_tC), %s.map(dash_tc_from_tC)]));"
               % (json.dumps(tc), json.dumps(tC),
                  json.dumps([p[0] for p in inside])))
        a, b, c = js_runner.run_js(src)
        assert a == tC and b == tc and c == [p[1] for p in inside]

    def test_js_table_equals_python(self):
        m = re.search(r"const DASH_LEAP_TC = (\[[^\]]*\]);",
                      dr._DASH_LEAP_SECONDS_JS)
        assert m and json.loads(m.group(1)) == list(
            dr._STATA_LEAP_SECONDS_TC_MS) == _LEAP
        assert dr._DASH_LEAP_SECONDS_JS in dr._DASH_AXIS_FINISH_JS

    def test_not_in_the_transforms(self):
        """The leap code rides on the finish code only, never on every date
        column's transform."""
        assert "dash_tC_from_tc" not in dr._DASH_DATE_UNITS_JS
        assert "dash_tc_from_tC" not in dr._DASH_DATE_UNITS_JS
