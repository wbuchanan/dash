"""Computed layers and KPI statistics of a date, in the variable's Stata units
(WP-29 section 05: P0.8 and P0.20).

dash holds a date column in epoch milliseconds, the unit its Bokeh axis is
drawn in.  Every computed layer and every KPI statistic read that column as
it is held, where twoway computes in the variable's own Stata units: days
for %td, milliseconds after 01jan1960 for %tc, and weeks, months, quarters,
half-years or years for the others.  Measured on sysuse sp500 at the WP-29
batch-1 base: ``histogram date, width(30) start(14975)`` drew 15 bars with
every row in the last, a %td density was 3.47e-11 per millisecond where
twoway's is .0029992 per day, ``lpoly close date, bwidth(30)`` drew nothing,
and ``dash kpi sd(date)`` read 9.10e+09 where summarize reads 105.3335.

Every number Stata computes here is read from the committed fixture
``test/fixtures/date_units_truth.json`` (``scripts/extract_date_units_truth.do``);
every position on a date axis from the independent oracles below, never from
the code under test.
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (ColumnDataSource, DatetimeAxis, LinearAxis, LogAxis,
                          Span)
from bokeh.plotting import figure as bokeh_figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_date_range as tdr  # noqa: E402
import test_help_claims_4 as hc4  # noqa: E402
import test_served_dates as tsd  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "date_units_truth.json")
_TRUTH_CACHE = {}


def _truth():
    """The fixture; a missing fixture fails, never skips."""
    if "t" not in _TRUTH_CACHE:
        if not os.path.exists(_FIXTURE):
            pytest.fail("test/fixtures/date_units_truth.json is missing: run "
                        "scripts/extract_date_units_truth.do (WP-29 S05)")
        with open(_FIXTURE, encoding="utf-8") as fh:
            _TRUTH_CACHE["t"] = json.load(fh)
    return _TRUTH_CACHE["t"]


_COLS = ("date", "close", "m", "q", "w", "tc", "yr")


def _df():
    d = _truth()["data"]
    return pd.DataFrame({c: [float(v) for v in d[c]] for c in _COLS})


_FMT = {"date": "%td", "close": "%9.0g", "m": "%tm", "q": "%tq", "w": "%tw",
        "tc": "%tc", "yr": "%ty"}
_SLIDER = ({"varname": "close", "type": "slider"},)
_MODES = ("saved", "served")
_NODE = pytest.mark.skipif(js_runner.NODE is None,
                           reason="node is not installed")


def _spec(plots, kpis=(), go=None, filters=_SLIDER, formats=None):
    fm = dict(_FMT)
    fm.update(formats or {})
    return {"graphs": [{"plots": list(plots),
                        "graph_options": dict({"name": "g1"}, **(go or {})),
                        "if_expr": "", "in_expr": ""}],
            "kpis": list(kpis),
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "", "formats": fm,
                              "filters": list(filters),
                              "registry": " ".join(
                                  ["g1"] + [k["name"] for k in kpis])}}


# ---------------------------------------------------------------------------
# Independent oracles: Stata values to epoch milliseconds.
# ---------------------------------------------------------------------------

def _ts_ms(ts):
    return (ts - pd.Timestamp("1970-01-01")) / pd.Timedelta(milliseconds=1)


def ms_td(v):
    return (v - 3653) * 86_400_000.0


def ms_tm(v):
    v = int(v)
    return _ts_ms(pd.Timestamp(year=1960 + v // 12, month=v % 12 + 1, day=1))


def ms_tm_frac(v):
    f = int(math.floor(v))
    return ms_tm(f) + (v - f) * (ms_tm(f + 1) - ms_tm(f))


def _period_start(f, kind):
    f = int(f)
    if kind == "tm":
        return ms_tm(f)
    if kind == "tq":
        return _ts_ms(pd.Timestamp(year=1960 + f // 4, month=3 * (f % 4) + 1,
                                   day=1))
    if kind == "th":
        return _ts_ms(pd.Timestamp(year=1960 + f // 2, month=6 * (f % 2) + 1,
                                   day=1))
    if kind == "ty":
        return _ts_ms(pd.Timestamp(year=f, month=1, day=1))
    if kind == "tw":
        y, i = 1960 + f // 52, f % 52
        return _ts_ms(pd.Timestamp(year=y, month=1, day=1)
                      + pd.Timedelta(days=7 * i))
    raise ValueError(kind)


def ms_of(v, kind):
    """Epoch ms of the Stata value *v* of *kind* (fractions placed linearly
    between period starts, the way a date axis draws them)."""
    if kind == "td":
        return ms_td(v)
    if kind in ("tc", "tC"):
        return v - 315_619_200_000.0
    if kind == "tw":
        f = int(math.floor(v))
        a = _period_start(f, "tw")
        b = (_period_start(f + 1, "tw") if (f + 1) % 52
             else _ts_ms(pd.Timestamp(year=1960 + (f + 1) // 52, month=1,
                                      day=1)))
        return a + (v - f) * (b - a)
    f = int(math.floor(v))
    a, b = _period_start(f, kind), _period_start(f + 1, kind)
    return a + (v - f) * (b - a)


_KIND_VAR = {"td": "date", "tm": "m", "tq": "q", "tw": "w", "tc": "tc",
             "ty": "yr"}


# ---------------------------------------------------------------------------
# Building and reading a dashboard in either mode.
# ---------------------------------------------------------------------------

def _build(mode, tmp_path, spec, df=None):
    """``(figure, warnings, renderer-or-document)``."""
    df = _df() if df is None else df
    os.makedirs(str(tmp_path), exist_ok=True)
    if mode == "saved":
        r, w = tdr._saved(tmp_path, spec, df)
        (fig,) = list(r.figures.values())
        return fig, w, r
    doc, w = tdr._served(tmp_path, spec, df)
    return tsd._served_fig(doc), w, doc


def _layers(fig):
    """The renderers that draw a computed layer (not the shared rows: a
    served figure's scatter source need not carry the row id)."""
    return [r for r in fig.renderers
            if getattr(r, "glyph", None) is not None
            and type(r.glyph).__name__ != "Scatter"
            and dr._ROW_ID_COLUMN not in r.data_source.data]


def _field(glyph, attr):
    spec = getattr(glyph, attr, None)
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        return spec.get("field")
    return getattr(spec, "field", None)


def _drawn_x(fig):
    """Every x position a computed layer draws, as floats."""
    out = []
    for r in _layers(fig):
        g, data = r.glyph, r.data_source.data
        for attr in ("x", "left", "right"):
            if attr not in g.properties():
                continue
            f = _field(g, attr)
            if f and f in data:
                out.extend(float(v) for v in data[f])
    return np.asarray(out, dtype=float)


def _bars(fig):
    (r,) = [r for r in _layers(fig) if "top" in r.data_source.data]
    d = r.data_source.data
    return (np.asarray(d["left"], float), np.asarray(d["right"], float),
            np.asarray(d["top"], float), r)


def _line(fig, xcol="x", ycol="y"):
    rs = [r for r in _layers(fig) if xcol in r.data_source.data
          and ycol in r.data_source.data
          and type(r.glyph).__name__ == "Line"]
    assert rs, "no line with %s/%s" % (xcol, ycol)
    d = rs[-1].data_source.data
    return (np.asarray(d[xcol], float), np.asarray(d[ycol], float), rs[-1])


def _axis_types(fig):
    return type(fig.xaxis[0]), type(fig.yaxis[0])


def _hist(var, **opts):
    return {"type": "histogram", "var": var,
            "options": {k: str(v) for k, v in opts.items()}}


def _kd(var, **opts):
    return {"type": "kdensity", "var": var,
            "options": {k: str(v) for k, v in opts.items()}}


def _two(ptype, yvar, xvar, **opts):
    return {"type": ptype, "yvar": yvar, "xvar": xvar,
            "options": {k: str(v) for k, v in opts.items()}}


def _agg_configs(r):
    cb = r.filter_callbacks[0]
    return cb.args["agg_configs_json"]


def _raise_constant(c):
    raise ValueError("non-finite number in page JSON: %s" % c)


def _node_parse(text):
    """node's JSON.parse of *text*; raises on a page JSON that would break
    the page's callback."""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("JSON.parse(" + json.dumps(text) + ");")
        path = fh.name
    try:
        res = subprocess.run([js_runner.node(), path], capture_output=True,
                             text=True, timeout=60)
        assert res.returncode == 0, res.stderr[:800]
    finally:
        os.unlink(path)


def _saved_move(r, value):
    """The sources after the close slider moves to *value*, by the page's
    own filter callback under node."""
    w = r.filter_widgets[0]
    cb = r.filter_callbacks[0]
    old = w.value
    w.value = value
    try:
        return hc4._run_js_full(cb.args, cb.code)["sources"]
    finally:
        w.value = old


def _served_move(doc, value):
    w = hc4._served_widget(doc, "close")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tsd._fire(w, value)


def _rel(a, b, tol):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return a.shape == b.shape and np.allclose(a, b, rtol=tol, atol=1e-15)


# ===========================================================================
# P0.8: computed layers on a date in Stata units
# ===========================================================================

class TestTheUnitHelpers:

    _CASES = [("td", 14977.5), ("tc", 1294016400000.0), ("tw", 2132.0),
              ("tm", 492.0), ("tq", 164.0), ("th", 82.0), ("ty", 2001.0)]

    def test_date_units_reads_every_kind(self):
        bad = []
        for kind, v in self._CASES:
            col = dr._stata_dates_to_datetime(pd.Series([v]), kind)
            got = dr._dash_date_units(col, kind)
            if not (len(got) == 1 and abs(got[0] - v) <= 1e-6 * max(1, abs(v))):
                bad.append("%s %s -> %s" % (kind, v, list(got)))
        assert not bad, bad
        nat = dr._dash_date_units(pd.Series([pd.NaT], dtype="datetime64[ms]"),
                                  "td")
        assert np.isnan(nat).all()
        col = dr._stata_dates_to_datetime(pd.Series([14977.0]), "td")
        assert list(dr._dash_date_units(col, "zz")) == [ms_td(14977.0)]

    def test_units_to_axis_places_whole_and_fractional_periods(self):
        got = dr._dash_units_to_axis(np.array([492.0, 492.5, 493.0]), "tm")
        want = [_ts_ms(pd.Timestamp(s)) for s in
                ("2001-01-01", "2001-01-16 12:00", "2001-02-01")]
        assert np.allclose(got, want, rtol=0, atol=1.0), got
        got = dr._dash_units_to_axis(np.array([14977.25]), "td")
        assert abs(got[0] - _ts_ms(pd.Timestamp("2001-01-02 06:00"))) <= 1.0
        got = dr._dash_units_to_axis(np.array([2183.5]), "tw")
        a = _ts_ms(pd.Timestamp("2001-12-24"))
        b = _ts_ms(pd.Timestamp("2002-01-01"))
        assert abs(got[0] - (a + b) / 2) <= 1.0

    def test_units_to_axis_never_raises_on_hostile_values(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            got = dr._dash_units_to_axis(
                [1e300, -1e300, math.nan, math.inf, "x"], "td")
            assert np.isnan(np.asarray(got, float)).all(), got
            got = dr._dash_units_to_axis([10000.0], "ty")
            assert np.isnan(np.asarray(got, float)).all(), got

    def test_axis_vars_reads_a_univariate_first_layer(self):
        assert dr._dash_axis_vars([_hist("date")]) == ("date", "")
        assert dr._dash_axis_vars(
            [_two("scatter", "close", "date")]) == ("date", "close")
        assert dr._dash_axis_vars([]) == ("", "")

    def test_layer_units_drops_unconvertible_rows_jointly(self):
        mp = dr.GlyphMapper()
        mp.date_vars = {"d": "tm"}
        src = ColumnDataSource({"d": [ms_tm(492), 1e18, ms_tm(494)],
                                "w": [1.0, 2.0, math.nan]})
        opts = {"weight": "fweight", "wexp": "w"}
        d, w, wtype = mp._layer_units(src, None, opts, "histogram", "d")
        assert list(d) == [492.0] and list(w) == [1.0] and wtype == "fw"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mp.map_histogram(bokeh_figure(), src, "d", opts)

    def test_on_axis_follows_the_figures_axis(self):
        mp = dr.GlyphMapper()
        mp.date_vars = {"date": "td"}
        vals = np.array([14977.0, 1e9, math.nan])
        fig = bokeh_figure()
        dr._dash_mark_date_axes(fig, "td", None)
        drawn, off = mp._on_axis(fig, vals, "date", "x")
        assert drawn[0] == ms_td(14977.0) and np.isnan(drawn[1:]).all()
        assert list(off) == [False, True, False]
        fig = bokeh_figure()
        dr._dash_mark_date_axes(fig, None, None)
        drawn, off = mp._on_axis(fig, vals, "date", "x")
        assert drawn[0] == 14977.0 and drawn[1] == 1e9 and not off.any()
        drawn, off = mp._on_axis(bokeh_figure(), vals, "date", "x")
        assert drawn[0] == ms_td(14977.0) and list(off) == [False, True, False]
        drawn, off = mp._on_axis(fig, vals, "close", "x")
        assert drawn[0] == 14977.0 and drawn[1] == 1e9 and not off.any()


class TestAUnivariateDateIsOnX:

    @pytest.mark.parametrize("ptype", ["histogram", "kdensity"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_date_axis_is_x(self, tmp_path, mode, ptype):
        """kdensity: D05-1 was struck (01oct2026), so dash keeps its date
        axis where twoway labels numbers."""
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([{"type": ptype, "var": "date",
                                     "options": {}}]))
        xa, ya = _axis_types(fig)
        assert xa is DatetimeAxis and ya is not DatetimeAxis, (xa, ya)

    @pytest.mark.parametrize("fmt", ["%tdCCYY-NN-DD", "%tmMon_CCYY"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_axis_reads_the_variables_format(self, tmp_path, mode, fmt):
        var = "date" if fmt.startswith("%td") else "m"
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([_hist(var)], formats={var: fmt}))
        assert fig.xaxis[0].formatter.args["fmt"] == fmt
        # twoway's measured first ticks are what the writer gives.
        assert dr._dash_fmt_text(14976, "%tdCCYY-NN-DD") == "2001-01-01"
        assert dr._dash_fmt_text(492, "%tmMon_CCYY") == "Jan 2001"

    @pytest.mark.parametrize("mode", _MODES)
    def test_yline_is_a_density(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([_hist("date")], go={"yline": ".002"}))
        spans = [s.location for s in fig.center
                 if isinstance(s, Span) and s.dimension == "width"]
        assert spans == [0.002], spans

    @pytest.mark.parametrize("mode", _MODES)
    def test_xline_and_xlabel_are_days(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([_hist("date")],
                                   go={"xline": "15000",
                                       "xlabel": "15000 15100"}))
        spans = [s.location for s in fig.center
                 if isinstance(s, Span) and s.dimension == "height"]
        assert spans == [ms_td(15000)] == [980380800000.0], spans
        ticks = list(fig.xaxis[0].ticker.ticks)
        assert ticks == [980380800000.0, 989020800000.0], ticks

    @pytest.mark.parametrize("mode", _MODES)
    def test_yscale_log_is_honoured(self, tmp_path, mode):
        fig, w, _c = _build(mode, tmp_path,
                            _spec([_hist("date")], go={"yscale": "log"}))
        assert isinstance(fig.yaxis[0], LogAxis), type(fig.yaxis[0])
        assert not [x for x in w if "date variable ''" in x], w

    @pytest.mark.parametrize("mode", _MODES)
    def test_xscale_log_note_names_the_variable(self, tmp_path, mode):
        _fig, w, _c = _build(mode, tmp_path,
                             _spec([_hist("date")], go={"xscale": "log"}))
        assert [x for x in w if "xscale(log) is meaningless for the date "
                "variable 'date'" in x], w


# ---------------------------------------------------------------------------
# The axis rule (D05-1 struck 01oct2026: dash keeps its date axis)
# ---------------------------------------------------------------------------

_TWOWAY_DATES = ("hist_td", "lowess_td", "mspline_td", "mband_td", "fpfit_td",
                 "fpfitci_td", "hist_then_kd", "scatter_then_lfit", "hist_tm",
                 "scatter_then_lfit_ydate")
_DIVERGES = ("kd_td", "lfit_td", "qfit_td", "lfitci_td", "qfitci_td",
             "lpoly_td", "lpolyci_td", "kd_then_hist", "lfit_then_scatter",
             "lfit_then_lowess", "kd_tm", "lfit_ydate")


def _fit(ptype, yvar="close", xvar="date"):
    o = {"bwidth": "30"} if ptype in ("lpoly", "lpolyci") else {}
    return _two(ptype, yvar, xvar, **o)


_AXIS_PLOTS = {
    "hist_td": [_hist("date")],
    "kd_td": [_kd("date")],
    "lfit_td": [_fit("lfit")],
    "qfit_td": [_fit("qfit")],
    "lfitci_td": [_fit("lfitci")],
    "qfitci_td": [_fit("qfitci")],
    "lpoly_td": [_fit("lpoly")],
    "lpolyci_td": [_fit("lpolyci")],
    "lowess_td": [_fit("lowess")],
    "mspline_td": [_fit("mspline")],
    "mband_td": [_fit("mband")],
    "fpfit_td": [_fit("fpfit")],
    "fpfitci_td": [_fit("fpfitci")],
    "kd_then_hist": [_kd("date"), _hist("date")],
    "hist_then_kd": [_hist("date"), _kd("date")],
    "lfit_then_scatter": [_fit("lfit"), _fit("scatter")],
    "scatter_then_lfit": [_fit("scatter"), _fit("lfit")],
    "lfit_then_lowess": [_fit("lfit"), _fit("lowess")],
    "kd_tm": [_kd("m")],
    "hist_tm": [_hist("m")],
    "lfit_ydate": [_fit("lfit", "date", "close")],
    "scatter_then_lfit_ydate": [_fit("scatter", "date", "close"),
                                _fit("lfit", "date", "close")],
}


def _check_date_axis(tmp_path, mode, case):
    fig, _w, _c = _build(mode, tmp_path, _spec(_AXIS_PLOTS[case]))
    on = _truth()["axis_labels"][case]["date_axis"]
    xa, ya = _axis_types(fig)
    date_ax, other = (xa, ya) if on == "x" else (ya, xa)
    assert date_ax is DatetimeAxis and other is not DatetimeAxis, (
        "%s: x %s, y %s; the date is on %s" % (case, xa.__name__,
                                                ya.__name__, on))


class TestTheAxisRule:

    def test_the_cases_are_split_as_twoway_labels_them(self):
        ax = _truth()["axis_labels"]
        assert {k for k, v in ax.items() if v["dates_shown"]} \
            == set(_TWOWAY_DATES)
        assert {k for k, v in ax.items() if not v["dates_shown"]} \
            == set(_DIVERGES)

    @pytest.mark.parametrize("case", _TWOWAY_DATES)
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_axis_is_twoways(self, tmp_path, mode, case):
        _check_date_axis(tmp_path, mode, case)

    @pytest.mark.parametrize("case", _DIVERGES)
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_unit_labelled_first_layer_keeps_the_date_axis(
            self, tmp_path, mode, case):
        """The ratified divergence (D05-1 struck 01oct2026): twoway labels
        this axis with the variable's numbers, dash keeps its date axis."""
        _check_date_axis(tmp_path, mode, case)

    @pytest.mark.parametrize("ptype", ["lfit", "qfit", "lfitci", "qfitci",
                                       "kdensity", "lpoly", "lpolyci"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_lone_fit_is_drawn_at_its_dates(self, tmp_path, mode, ptype):
        plot = _kd("date") if ptype == "kdensity" else _fit(ptype)
        fig, _w, _c = _build(mode, tmp_path, _spec([plot]))
        assert isinstance(fig.xaxis[0], DatetimeAxis)
        xs = _drawn_x(fig)
        xs = xs[np.isfinite(xs)]
        lo, hi = ms_td(14977), ms_td(15340)
        assert xs.size and xs.min() >= lo - 1 and xs.max() <= hi + 1, (
            xs.min() if xs.size else None, xs.max() if xs.size else None)
        if ptype in ("lpoly", "lpolyci"):
            x, _y, _r = _line(fig, "x_lp", "y_lp")
            assert np.isfinite(x).sum() >= 2


# ---------------------------------------------------------------------------
# histogram, kdensity, lpoly and fpfit against Stata
# ---------------------------------------------------------------------------

_HIST_OPTS = {
    "td:default": ("date", {}),
    "td:w30s14975": ("date", {"width": "30", "start": "14975"}),
    "td:bin10": ("date", {"bin": "10"}),
    "td:discrete": ("date", {"discrete": "1"}),
    "td:frequency": ("date", {"frequency": "1"}),
    "tm:default": ("m", {}),
    "tm:w2s492": ("m", {"width": "2", "start": "492"}),
    "tc:default": ("tc", {}),
    "tc:w7d": ("tc", {"start": "1294012800000", "width": "604800000"}),
    "tw:default": ("w", {}),
    "ty:default": ("yr", {}),
}


class TestHistogramOnADate:

    @pytest.mark.parametrize("key", sorted(_HIST_OPTS))
    @pytest.mark.parametrize("mode", _MODES)
    def test_bars_match_twoway(self, tmp_path, mode, key):
        var, opts = _HIST_OPTS[key]
        t = _truth()["histogram"][key]
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([{"type": "histogram", "var": var,
                                     "options": dict(opts)}]))
        left, _right, top, _r = _bars(fig)
        assert len(top) == t["bin"], (len(top), t["bin"])
        assert _rel(top, t["heights"], 1e-9), (
            "tops %s, twoway %s" % (np.round(top[:4], 9).tolist(),
                                    np.round(t["heights"][:4], 9).tolist()))
        # A discrete bar is centred on its value: its left edge is half a
        # width below twoway's r(start).
        first = t["start"] - (t["width"] / 2 if "discrete" in opts else 0)
        want = ms_of(first, key.split(":")[0])
        assert abs(left[0] - want) <= 1e-12 * abs(want), (left[0], want)

    @pytest.mark.parametrize("mode", _MODES)
    def test_width_and_start_raise_no_bin_limit_note(self, tmp_path, mode):
        _fig, w, _c = _build(mode, tmp_path,
                             _spec([_hist("date", width=30, start=14975)]))
        assert not [x for x in w if "1000 bins" in x], w


_KD_OPTS = {
    "td:range:default": ("date", {"n": "5", "range": "14900 15400"}),
    "td:range:bw10": ("date", {"n": "5", "range": "14900 15400",
                               "bwidth": "10"}),
    "tm:range:bw1": ("m", {"n": "5", "range": "490 505", "bwidth": "1"}),
}


class TestKdensityOnADate:

    @pytest.mark.parametrize("key", sorted(_KD_OPTS))
    @pytest.mark.parametrize("mode", _MODES)
    def test_density_matches_twoway(self, tmp_path, mode, key):
        var, opts = _KD_OPTS[key]
        t = _truth()["kdensity"][key]
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([{"type": "kdensity", "var": var,
                                     "options": dict(opts)}]))
        x, y, _r = _line(fig)
        assert _rel(y, t["y"], 1e-9), (y.tolist(), t["y"])
        oracle = ms_td if var == "date" else ms_tm_frac
        want = [oracle(v) for v in t["x"]]
        assert x.shape == (len(want),) and np.allclose(x, want, rtol=0,
                                                       atol=1.0), (
            x.tolist(), want)
        assert isinstance(fig.xaxis[0], DatetimeAxis)

    @pytest.mark.parametrize("mode", _MODES)
    def test_on_a_date_axis_it_is_drawn_at_the_dates(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path, _spec(
            [_hist("date"), _kd("date", range="14900 15400", n=5,
                                bwidth=10)]))
        x, y, _r = _line(fig)
        want = [ms_td(v) for v in (14900, 15025, 15150, 15275, 15400)]
        assert np.allclose(x, want, rtol=0, atol=1.0), x.tolist()
        assert _rel(y, _truth()["kdensity"]["td:range:bw10"]["y"], 1e-9)


_LP_OPTS = {"td:bw30": ("date", "30"), "tm:bw2": ("m", "2"),
            "tc:bw30d": ("tc", "2592000000")}


class TestLpolyOnADate:

    @pytest.mark.parametrize("key", sorted(_LP_OPTS))
    @pytest.mark.parametrize("mode", _MODES)
    def test_explicit_bwidth_draws_statas_curve(self, tmp_path, mode, key):
        var, bw = _LP_OPTS[key]
        fig, _w, _c = _build(mode, tmp_path, _spec(
            [_two("lpoly", "close", var, bwidth=bw, n=5)]))
        _x, y, _r = _line(fig, "x_lp", "y_lp")
        want = _truth()["lpoly"][key]["y"]
        assert _rel(y, want, 1e-9), (y.tolist(), want)

    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_draws_a_curve(self, tmp_path, mode, ptype):
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([_two(ptype, "close", "date")]))
        _x, y, _r = _line(fig, "x_lp", "y_lp")
        assert np.isfinite(y).sum() >= 2


class TestFpfitOnADate:

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_curve_is_statas(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path,
                             _spec([_two("fpfit", "close", "date")]))
        _x, y, _r = _line(fig, "x_fp", "y_fp")
        want = _truth()["fits"]["fp:td"]["y"]
        assert _rel([y[0], y[-1]], want, 1e-9), ([y[0], y[-1]], want)


_COMPUTED13 = ("histogram", "kdensity", "lfit", "qfit", "lfitci", "qfitci",
               "lowess", "lpoly", "lpolyci", "mspline", "mband", "fpfit",
               "fpfitci")


def _obs_frame():
    return _df().assign(obs=np.arange(1.0, 249.0))


class TestEveryComputedLayer:

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_monthly_lfit_is_statas(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path, _spec(
            [_two("scatter", "close", "m"), _two("lfit", "close", "m")]))
        _x, y, _r = _line(fig)
        want = _truth()["fits"]["lfit:tm"]["y"]
        assert _rel([y[0], y[-1]], want, 1e-9), ([y[0], y[-1]], want)

    @pytest.mark.parametrize("ptype", _COMPUTED13)
    def test_a_monthly_layer_lands_on_its_months(self, tmp_path, ptype):
        if ptype == "histogram":
            layer = _hist("m")
        elif ptype == "kdensity":
            layer = _kd("m")
        else:
            o = {"bwidth": "2"} if ptype in ("lpoly", "lpolyci") else {}
            layer = _two(ptype, "close", "m", **o)
        fig, _w, _c = _build("saved", tmp_path, _spec(
            [_two("scatter", "close", "m"), layer]))
        xs = _drawn_x(fig)
        xs = xs[np.isfinite(xs)]
        lo, hi = ms_tm(492), ms_tm(503)
        assert xs.size and xs.min() >= lo - 1 and xs.max() <= hi + 1, (
            ptype, xs.min() if xs.size else None,
            xs.max() if xs.size else None, lo, hi)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_date_y_is_fitted_in_its_units(self, tmp_path, mode):
        fig, _w, _c = _build(mode, tmp_path, _spec(
            [_two("scatter", "date", "close"), _two("lfit", "date", "close")]))
        _x, y, _r = _line(fig)
        want = [ms_td(v) for v in _truth()["fits"]["lfit:ydate"]["y"]]
        assert np.allclose([y[0], y[-1]], want, rtol=0, atol=1.0), (
            [y[0], y[-1]], want)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units(
            self, tmp_path, mode):
        """D05-4's mixed axis: twoway draws (scatter close obs)(lfit close
        date) on a numeric axis with the fit at the day numbers."""
        fig, _w, _c = _build(mode, tmp_path, _spec(
            [_two("scatter", "close", "obs"), _two("lfit", "close", "date")]),
            _obs_frame())
        assert type(fig.xaxis[0]) is LinearAxis
        x, _y, _r = _line(fig)
        assert abs(x.min() - 14977) <= 1e-6 and abs(x.max() - 15340) <= 1e-6, (
            x.min(), x.max())


# ---------------------------------------------------------------------------
# Out of Stata's dates: dropped with one note, never NaN in page JSON (A1)
# ---------------------------------------------------------------------------

_OOR = {
    "hist_start-700000_w100000": (
        [_hist("date", start=-700000, width=100000)], "1 bar(s)", 7),
    "kd_after_hist_range-1000000_15400": (
        [_hist("date"), _kd("date", range="-1000000 15400", n=5)],
        "2 point(s)", 3),
    "kd_lone_range-1000000_15400": (
        [_kd("date", range="-1000000 15400", n=5)], "2 point(s)", 3),
    "lfit_after_scatter_range-700000_15340": (
        [_two("scatter", "close", "date"),
         _two("lfit", "close", "date", range="-700000 15340")],
        "3 point(s)", 97),
}


def _layer_arrays(fig):
    out = []
    for r in _layers(fig):
        d = r.data_source.data
        out.append({k: np.asarray(d[k], float).tolist() for k in sorted(d)})
    return out


class TestOutOfRange:

    @pytest.mark.parametrize("case", sorted(_OOR))
    @pytest.mark.parametrize("mode", _MODES)
    def test_out_of_range_edges_never_reach_the_page_json(self, tmp_path,
                                                          mode, case):
        plots, note, kept = _OOR[case]
        fig, w, ctx = _build(mode, tmp_path / "a", _spec(plots))
        notes = [x for x in w if "outside Stata's dates" in x]
        assert len(notes) == 1 and note in notes[0], w
        if plots[-1]["type"] == "histogram":
            _l, _rr, top, _r = _bars(fig)
            assert len(top) == kept
        else:
            x, _y, _r = _line(fig)
            assert len(x) == kept and np.isfinite(x).all()
        if mode == "saved":
            text = _agg_configs(ctx)
            json.loads(text, parse_constant=_raise_constant)
            if js_runner.NODE is not None:
                _node_parse(text)
                _saved_move(ctx, ctx.filter_widgets[0].start)
        else:
            sfig, _sw, _r = _build("saved", tmp_path / "b", _spec(plots))
            got, want = _layer_arrays(fig), _layer_arrays(sfig)
            assert len(got) == len(want)
            for a, b in zip(got, want):
                assert sorted(a) == sorted(b)
                for k in a:
                    assert np.allclose(a[k], b[k], rtol=1e-12,
                                       equal_nan=True), k


# ---------------------------------------------------------------------------
# After a filter move
# ---------------------------------------------------------------------------

class TestAfterAFilterMove:

    @_NODE
    def test_saved_histogram_recount_is_per_day(self, tmp_path):
        _fig, _w, r = _build("saved", tmp_path, _spec([_hist("date")]))
        fig = list(r.figures.values())[0]
        _l, _rr, _t, rend = _bars(fig)
        out = _saved_move(r, 1200.0)
        top = np.asarray(out[rend.data_source.id]["top"], float)
        t = _truth()["histogram"]["td:default:fixedgrid:if"]
        nb = t["bin"]
        assert _rel(top[:nb], t["heights"], 1e-9), (top.tolist(),
                                                    t["heights"])
        assert not top[nb:].any()

    @_NODE
    @pytest.mark.parametrize("key,bw", [("td:range:default:if", None),
                                        ("td:range:bw10:if", "10")])
    def test_saved_kdensity_recompute_is_per_day(self, tmp_path, key, bw):
        o = {"range": "14900 15400", "n": "5"}
        if bw:
            o["bwidth"] = bw
        _fig, _w, r = _build("saved", tmp_path,
                             _spec([{"type": "kdensity", "var": "date",
                                     "options": o}]))
        fig = list(r.figures.values())[0]
        _x, _y, rend = _line(fig)
        out = _saved_move(r, 1200.0)
        y = out[rend.data_source.id]["y"]
        assert _rel(y, _truth()["kdensity"][key]["y"], 1e-9), y

    def test_served_layers_after_a_move(self, tmp_path):
        T = _truth()
        # The histogram, re-binned from the kept rows.
        fig, _w, doc = _build("served", tmp_path / "h",
                              _spec([_hist("date")]))
        _served_move(doc, 1200.0)
        left, _r, top, _x = _bars(tsd._served_fig(doc))
        t = T["histogram"]["td:default:if"]
        assert len(top) == t["bin"] and _rel(top, t["heights"], 1e-9), (
            top.tolist(), t["heights"])
        assert abs(left[0] - ms_td(t["start"])) <= 1.0
        # The density.
        fig, _w, doc = _build("served", tmp_path / "k", _spec(
            [_kd("date", range="14900 15400", n=5)]))
        _served_move(doc, 1200.0)
        _x, y, _r = _line(tsd._served_fig(doc))
        assert _rel(y, T["kdensity"]["td:range:default:if"]["y"], 1e-9), y
        # lpoly.
        fig, _w, doc = _build("served", tmp_path / "l", _spec(
            [_two("lpoly", "close", "date", bwidth=30, n=5)]))
        _served_move(doc, 1200.0)
        _x, y, _r = _line(tsd._served_fig(doc), "x_lp", "y_lp")
        assert _rel(y, T["lpoly"]["td:bw30:if"]["y"], 1e-9), y

    @_NODE
    @pytest.mark.parametrize("case", ["histogram", "kdensity",
                                      "histogram-fw-date",
                                      "kdensity-aw-date"])
    def test_an_inert_move_changes_nothing(self, tmp_path, case):
        df = _df()
        df["wd"] = df["date"] - 14900.0
        ptype = case.split("-")[0]
        o = {}
        if case.endswith("-date"):
            o = {"weight": "fweight" if "fw" in case else "aweight",
                 "wexp": "wd"}
        _fig, w, r = _build("saved", tmp_path, _spec(
            [{"type": ptype, "var": "date", "options": o}],
            formats={"wd": "%td"}), df)
        fig = list(r.figures.values())[0]
        if ptype == "histogram":
            _l, _rr, before, rend = _bars(fig)
            col = "top"
        else:
            _x, before, rend = _line(fig)
            col = "y"
        out = _saved_move(r, r.filter_widgets[0].start)
        assert rend.data_source.id in out and len(before), (
            "the layer was not drawn or not recounted: %s" % w)
        after = np.asarray(out[rend.data_source.id][col], float)
        assert _rel(after, before, 1e-12), (after[:4].tolist(),
                                            before[:4].tolist())

    @pytest.mark.parametrize("case", ["mixed-numeric", "lone-date"])
    def test_served_redraw_uses_the_live_figures_axis(self, tmp_path, case):
        if case == "mixed-numeric":
            plots = [_two("scatter", "close", "obs"),
                     _two("lfit", "close", "date")]
            lo, hi = 14977.0, 15340.0
        else:
            plots = [_two("lfit", "close", "date")]
            lo, hi = ms_td(14977), ms_td(15340)
        fig, _w, doc = _build("served", tmp_path, _spec(plots), _obs_frame())
        for moved in (False, True):
            if moved:
                _served_move(doc, 1200.0)
            x, _y, _r = _line(tsd._served_fig(doc))
            x = x[np.isfinite(x)]
            assert x.size and x.min() >= lo - 1e-6 and x.max() <= hi + 1e-6, (
                moved, x.min() if x.size else None)


# ---------------------------------------------------------------------------
# The saved page's JS recount, sliced
# ---------------------------------------------------------------------------

def _run_node(script):
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(script)
        path = fh.name
    try:
        res = subprocess.run([js_runner.node(), path], capture_output=True,
                             text=True, timeout=60)
        assert res.returncode == 0, res.stderr[:1500]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


@_NODE
class TestTheJsUnits:

    def test_the_pair_loop_converts_and_drops_out_of_range(self):
        js = dr._FILTER_JS
        lo = js.index("    let vals, wts = null;")
        hi = js.index("    if (ac.type === 'histogram') {")
        raw = [ms_td(14977), 1e18, ms_td(15000), ms_td(15010), None]
        wts = [ms_td(14980), ms_td(14985), None, ms_td(14995), ms_td(14999)]
        script = (dr._DASH_FMT_JS
                  + "\nconst ac = " + json.dumps(
                      {"type": "histogram", "datekind": "td", "wvar": "w",
                       "wdatekind": "td"})
                  + ";\nconst _ac_data = " + json.dumps({"w": wts})
                  + ";\nconst raw_col = " + json.dumps(raw)
                  + ";\nconst _pick = c => c;\n"
                  + "for (let _i = 0; _i < 1; _i++) {\n" + js[lo:hi]
                  + "\nprocess.stdout.write(JSON.stringify({vals, wts}));\n}")
        out = _run_node(script)
        assert np.allclose(out["vals"], [14977.0, 15010.0]), out
        assert np.allclose(out["wts"], [14980.0, 14995.0]), out

    def test_the_kdensity_branch_evaluates_in_units_and_draws_on_the_axis(
            self):
        vals = [1.0, 2.0, 2.5, 4.0]
        ac = {"type": "kdensity", "kernel": "epanechnikov", "bw_fixed": 1.5,
              "x_grid": [100.0, 200.0, 300.0], "x_eval": [1.0, 2.0, 3.0],
              "wvar": None, "wtype": None}
        out = js_runner.run_filter_js_block("kdensity", ac, vals)
        assert out["x"] == [100.0, 200.0, 300.0]
        want = dr._kde_curve(np.array(vals), np.array([1.0, 2.0, 3.0]), 1.5,
                             "epanechnikov")
        assert np.allclose(out["y"], want, rtol=1e-12), (out["y"], want)

    def test_the_histogram_branch_draws_its_slice(self):
        # Eight unit-wide bars from 0; the first is off the axis, so seven
        # are drawn, normalised over all eight counts.
        vals = [0.5, 1.5, 1.6, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 7.6]
        ue = [1.0, 2, 3, 4, 5, 6, 7, 8]
        ac = {"type": "histogram", "ymode": "density", "start": 0.0,
              "width": 1.0, "bin": 8, "bin_first": 1,
              "bin_edges": [1000.0 * e for e in ue], "unit_edges": ue,
              "discrete": False}
        out = js_runner.run_filter_js_block("histogram", ac, vals)
        counts = [1, 2, 1, 1, 1, 1, 1, 2]
        want = [c / (10 * 1.0) for c in counts[1:]]
        assert np.allclose(out["top"], want), out
        assert out["left"] == ac["bin_edges"][:7]


# ---------------------------------------------------------------------------
# The page configuration
# ---------------------------------------------------------------------------

def _floats(o):
    if isinstance(o, float):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _floats(v)
    elif isinstance(o, list):
        for v in o:
            yield from _floats(v)


class TestTheConfig:

    def test_agg_config_carries_datekind_and_unit_grids(self, tmp_path):
        _f, _w, r = _build("saved", tmp_path / "a",
                           _spec([_hist("date"), _kd("date")]))
        cfgs = json.loads(_agg_configs(r))
        h = [c for c in cfgs if c["type"] == "histogram"][0]
        k = [c for c in cfgs if c["type"] == "kdensity"][0]
        assert h["datekind"] == "td" and k["datekind"] == "td"
        assert all(math.isfinite(v) for v in h["unit_edges"])
        assert all(math.isfinite(v) for v in k["x_eval"])
        _f, _w, r = _build("saved", tmp_path / "b", _spec([_hist("close")]))
        (c,) = json.loads(_agg_configs(r))
        assert not {"datekind", "unit_edges", "x_eval", "bin_first"} & set(c)

    def test_no_config_number_is_non_finite(self, tmp_path):
        corpus = [p for p, _n, _k in _OOR.values()]
        corpus += [[_hist("date")], [_kd("date")], [_hist("m")], [_kd("m")],
                   [_hist("tc")], [_hist("date", discrete=1)]]
        bad = []
        for i, plots in enumerate(corpus):
            _f, _w, r = _build("saved", tmp_path / str(i), _spec(plots))
            for name in ("agg_configs_json", "kpi_config_json"):
                text = r.filter_callbacks[0].args[name]
                for v in _floats(json.loads(text)):
                    if not math.isfinite(v):
                        bad.append((i, name, v))
        assert not bad, bad


class TestTheFixture:

    def test_meta_and_data(self):
        t = _truth()
        m = t["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert len(m["dash_commit"]) == 40 and int(m["dash_commit"], 16) >= 0
        assert m["generated_by"] == "scripts/extract_date_units_truth.do"
        for c in _COLS:
            assert len(t["data"][c]) == 248, c


# ===========================================================================
# P0.20: KPI statistics of a date in Stata units
# ===========================================================================

_KPI_VARS = ("date", "m", "q", "w", "tc", "yr")
_KPI_STATS = ("sd", "var", "iqr", "cv", "sum", "skewness", "mean", "p50",
              "min", "max")
_KPI_PLOTS = [{"type": "scatter", "yvar": "close", "xvar": "date",
               "options": {}}]


def _kpi_def(stat, var, update="filter"):
    return {"name": "k_%s_%s" % (stat, var), "stat": stat, "var": var,
            "fmt": "", "title": "T", "update": update, "if_expr": ""}


def _kpi_spec(kpis, filters=_SLIDER, formats=None):
    return _spec(_KPI_PLOTS, kpis=kpis, filters=filters, formats=formats)


def _want(scope, var, stat):
    return _truth()["kpi"][scope][var][stat]["display"]


_ALL60 = [(v, s) for v in _KPI_VARS for s in _KPI_STATS]


@pytest.fixture(scope="module")
def _first_paint_cards(tmp_path_factory):
    spec = _kpi_spec([_kpi_def(s, v) for v, s in _ALL60])
    r = hc4._saved(tmp_path_factory.mktemp("kpi_saved"), spec, _df())
    saved = hc4._cards(d.text for d in r.kpi_divs.values())
    ns = hc4._served_app(tmp_path_factory.mktemp("kpi_served"), spec, _df())
    served = hc4._served_cards(hc4._served_session(ns))
    return {"saved": saved, "served": served}


_MOVED = [("date", s) for s in ("sd", "var", "iqr", "cv", "sum")] + \
    [("m", "mean"), ("m", "p50")]


def _tm2_frame():
    return pd.DataFrame({"m": [492.0, 494.0], "close": [1.0, 2.0],
                         "date": [14977.0, 15000.0]})


class TestKpiOfADate:

    @pytest.mark.parametrize("var,stat", _ALL60,
                             ids=["%s-%s" % vs for vs in _ALL60])
    @pytest.mark.parametrize("mode", _MODES)
    def test_first_paint(self, _first_paint_cards, mode, var, stat):
        got = _first_paint_cards[mode].get("k_%s_%s" % (stat, var))
        assert got == _want("all", var, stat), (got, _want("all", var, stat))

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_monthly_mean_is_statas_month(self, tmp_path, mode):
        spec = _kpi_spec([_kpi_def("mean", "m"), _kpi_def("p50", "m")])
        if mode == "saved":
            r = hc4._saved(tmp_path, spec, _tm2_frame())
            cards = hc4._cards(d.text for d in r.kpi_divs.values())
        else:
            ns = hc4._served_app(tmp_path, spec, _tm2_frame())
            cards = hc4._served_cards(hc4._served_session(ns))
        assert _want("tm2", "m", "mean") == "2001m2"
        assert cards.get("k_mean_m") == "2001m2", cards
        assert cards.get("k_p50_m") == "2001m2", cards

    @pytest.mark.parametrize("mode", _MODES)
    def test_after_a_move(self, tmp_path, mode):
        spec = _kpi_spec([_kpi_def(s, v) for v, s in _MOVED])
        if mode == "saved":
            if js_runner.NODE is None:
                pytest.skip("node is not installed")
            r = hc4._saved(tmp_path, spec, _df())
            cards = hc4._saved_filter_move(r, 0, 1200.0)
        else:
            ns = hc4._served_app(tmp_path, spec, _df())
            cards = hc4._served_filter_move(ns, "close", 1200.0)
        bad = ["%s(%s): card %r, Stata %r" % (s, v, cards.get(
            "k_%s_%s" % (s, v)), _want("if close>=1200", v, s))
            for v, s in _MOVED
            if cards.get("k_%s_%s" % (s, v)) != _want("if close>=1200", v, s)]
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_after_a_brush(self, tmp_path, mode):
        spec = _kpi_spec([_kpi_def(s, v, update="brush") for v, s in _MOVED],
                         filters=())
        if mode == "saved":
            if js_runner.NODE is None:
                pytest.skip("node is not installed")
            r = hc4._saved(tmp_path, spec, _df())
            cards = hc4._saved_brush(r, "g1", list(range(50)))
        else:
            ns = hc4._served_app(tmp_path, spec, _df())
            cards = hc4._served_brush(ns, list(range(50)))
        bad = ["%s(%s): card %r, Stata %r" % (s, v, cards.get(
            "k_%s_%s" % (s, v)), _want("in 1/50", v, s))
            for v, s in _MOVED
            if cards.get("k_%s_%s" % (s, v)) != _want("in 1/50", v, s)]
        assert not bad, bad

    def test_the_sum_note_names_the_units(self, tmp_path):
        spec = _kpi_spec([_kpi_def("sum", "date")])
        _f, ws, _r = _build("saved", tmp_path / "a", spec)
        _f, wv, _d = _build("served", tmp_path / "b", spec)
        ns = [x for x in ws if "adds up dates" in x]
        nv = [x for x in wv if "adds up dates" in x]
        assert len(ns) == 1 and "days since 01jan1960" in ns[0], ws
        assert nv == ns, (nv, ns)

    @_NODE
    def test_js_drops_out_of_range_values(self, tmp_path):
        spec = _kpi_spec([_kpi_def("sd", "date")])
        r = hc4._saved(tmp_path, spec, _df())
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        (k,) = [c for c in cfg if c.get("varname") == "date"]
        days = [14977.0, 14990.0, 15020.0, 15100.0]
        col = [ms_td(v) for v in days] + [1e18]
        js = dr._FILTER_JS
        helpers = js[js.index("// ---- KPI recompute, shared by"):
                     js.index("dash_apply_kpis(new_data,")]
        pctl = js[js.index("function dash_pctl"):
                  js.index("// agg_sources is a Bokeh model list")]
        script = (dr._DASH_FMT_JS + pctl
                  + '\nconst ROW_ID = "__dash_row__";\n' + helpers
                  + "\nconst data = " + json.dumps(
                      {"date": col, "__dash_row__": list(range(len(col)))})
                  + ";\nlet captured = null;"
                  + "\nconst divs = [{set text(v) { captured = v; }}];"
                  + "\ndash_apply_kpis(data, [" + json.dumps(k) + "], divs,"
                  + " ROW_ID);"
                  + "\nprocess.stdout.write(JSON.stringify(captured));")
        text = _run_node(script)
        _name, got = hc4._card(text)
        want = dr._dash_fmt_text(float(np.std(days, ddof=1)), "%9.0g")
        assert got == want, (got, want)

    def test_a_missing_kind_is_refused(self):
        col = dr._stata_dates_to_datetime(pd.Series([14977.0, 15000.0]), "td")
        with pytest.raises(ValueError):
            dr._dash_kpi_column(col, "sd", "date", None)
        out = dr._dash_kpi_column(col, "count", "date", None)
        assert np.asarray(out, float).dtype == np.float64 and len(out) == 2


class TestTheKpiConfig:

    def test_unitkind_reaches_every_statistic_but_counts(self, tmp_path):
        spec = _kpi_spec([_kpi_def("sd", "date"), _kpi_def("count", "date"),
                          _kpi_def("mean", "close"), _kpi_def("max", "date")])
        r = hc4._saved(tmp_path, spec, _df())
        cfg = {c["name"] if "name" in c else c.get("kname"): c
               for c in json.loads(
                   r.filter_callbacks[0].args["kpi_config_json"])}
        by = {(c.get("stat"), c.get("varname")): c for c in cfg.values()}
        assert by[("sd", "date")]["unitkind"] == "td"
        assert by[("count", "date")]["unitkind"] == ""
        assert by[("mean", "close")]["unitkind"] == ""
        assert by[("max", "date")]["datekind"] == "td"

    def test_the_unit_kind_rule(self):
        assert dr._dash_kpi_unit_kind("sd", "td") == "td"
        assert dr._dash_kpi_unit_kind("count", "td") == ""
        assert dr._dash_kpi_unit_kind("DCOUNT", "tm") == ""
        assert dr._dash_kpi_unit_kind("sd", "zz") == ""
        assert dr._dash_kpi_unit_kind("sd", None) == ""


@_NODE
def test_the_node_tests_ran():
    """The node cases run on any worker; a machine without node skips here
    rather than passing silently."""
    assert js_runner.NODE is not None
    _run_node("process.stdout.write(JSON.stringify(1));")
