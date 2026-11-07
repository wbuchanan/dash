"""
test_ax15_residual.py
WP-44 AX-15's residual (BUGS.md "A date axis past Stata's dates is ticked
by natscale; xvarformat(%21x) and a zlabel() format(%21x) are written
%9.0g"): an axis whose layers reach past Stata's dates is ticked as
twoway ticks it, by Stata's own _tsnatscale, and the hexadecimal and
IEEE-byte formats reach an axis and a colour key as twoway writes them,
by a variable's own format, xvarformat()/yvarformat() and zlabel(,
format()).

The truth is test/fixtures/ax15_residual_truth.json
(scripts/extract_ax15_residual_truth.do, StataNow 19.5, stcolor):

* ``tsnatscale`` -- _tsnatscale's answers past Stata's dates: evenly
  spaced, not natscale's round steps (``_tsnatscale 14977 100000000 5,
  daily`` lists 14977 25011233 50007489 75003745 100000001; natscale's
  are 0 2e7 ... 1e8), r(min)/r(max)/r(delta) for a period unit.
* ``graphs`` -- the labels twoway draws: ``past_*`` the x labels of
  ``(line close date) (scatteri ...)`` on sp500, which are the
  _tsnatscale lists written in %td (a value past Stata's dates in
  %9.0g); ``fmt_*`` an axis in a variable's or a layer's %21x, %16H,
  %8H, %16L, %-21x; ``key_*`` a colour key's labels in zlabel(,
  format()), and in %8.0gc whatever its variable's format.

Run with:  pytest test/test_ax15_residual.py -q -n0
"""
import json
import os
import sys
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402
import test_date_axis_residuals as dar  # noqa: E402
from test_display_format_sites import js_texts  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "ax15_residual_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
_TS = _T["tsnatscale"]
_G = _T["graphs"]
_UNIT = {"daily": "d", "monthly": "m", "quarterly": "q", "yearly": "y"}


def _ts_ticks(row):
    """The ticks a _tsnatscale answer stands for, in the unit's values:
    its list, else r(min) to r(max) by r(delta)."""
    if row["list"]:
        return [float(v) for v in row["list"]]
    out, v = [], row["min"]
    while v <= row["max"] + 1e-9 * abs(row["delta"]):
        out.append(float(v))
        v += row["delta"]
    return out


def _rows(*keys):
    """The spec's stata_ticks_build rows for the fixture's answers."""
    return [[_TS[k]["lo"], _TS[k]["hi"], _TS[k]["n"], _UNIT[_TS[k]["unit"]],
             _ts_ticks(_TS[k])] for k in keys]


def _labels(key, side="x"):
    """twoway's labels of a graph row, its axis or key title (the last
    text, which holds a letter past the first character other than a
    date's, an exponent's or a hex digit's) left out."""
    t = list(_G[key][side])
    if t and " " in t[-1] or t and t[-1][:1].isalpha():
        t = t[:-1]
    return t


class TestTheTruth:
    def test_meta(self):
        m = _T["_meta"]
        assert m["source"] == "scripts/extract_ax15_residual_truth.do"
        assert m["stata_version"] and m["dash_commit"]

    @pytest.mark.parametrize("key, graph", [
        ("d_hi8", "past_hi8"), ("d_hi8_n8", "past_hi8_n8"),
        ("d_hi10000", "past_hi10000"), ("d_lo", "past_lo")])
    def test_twoway_draws_tsnatscale(self, key, graph):
        """twoway's x labels are _tsnatscale's list in %td, a value past
        Stata's dates in %9.0g: not natscale's round steps."""
        want = [dr._dash_fmt_text(v, "%td") for v in _TS[key]["list"]]
        assert _labels(graph) == want
        nat = dr._dash_natscale_ticks(_TS[key]["lo"], _TS[key]["hi"],
                                      _TS[key]["n"])
        assert nat != _TS[key]["list"]


# ---------------------------------------------------------------------------
# A date axis past Stata's dates
# ---------------------------------------------------------------------------

def _past_fig(tmp_path, mode, plots, rows, go=None):
    sub = tmp_path / ("p%d" % next(dar._DA_SEQ))
    sub.mkdir()
    spec = dar._spec(plots, formats=dar._DA_FMT, graph_options=go)
    spec["build_options"]["stata_ticks_build"] = rows
    if mode == "saved":
        r, w = dar._saved(sub, spec, dar._DA)
        return list(r.figures.values())[0], w
    doc, w = dar._served(sub, spec, dar._DA)
    return dar.tb_panels(doc)[0], w


_PAST = [
    # (case, plots, go, fixture row, twoway's labels, side)
    ("hi8", [dar._L("line", "close", "date"), dar._si((1300, 1e8))], None,
     "d_hi8", "past_hi8", "below"),
    ("hi8 #8", [dar._L("line", "close", "date"), dar._si((1300, 1e8))],
     {"xlabel": "#8"}, "d_hi8_n8", "past_hi8_n8", "below"),
    ("year 10000", [dar._L("line", "close", "date"),
                    dar._si((1300, 2936550))], None,
     "d_hi10000", "past_hi10000", "below"),
    ("y axis", [dar._L("line", "date", "close"), dar._si((1e8, 1300))],
     None, "d_hi8", None, "left"),
]


@pytest.mark.parametrize("mode", _MODES)
class TestPastDates:
    @pytest.mark.parametrize("case, plots, go, key, graph, side", _PAST,
                             ids=[c[0] for c in _PAST])
    def test_stata_ticks(self, tmp_path, mode, case, plots, go, key, graph,
                         side):
        """Stata's _tsnatscale answer ticks the axis, and each tick is
        written as twoway writes it."""
        fig, _w = _past_fig(tmp_path, mode, plots, _rows(key), go)
        ax = dar._da_axis(fig, side)
        want = dr._dash_literal_to_ms(_TS[key]["list"], "td").tolist()
        assert list(ax.ticker.ticks) == want
        if graph:
            assert js_texts(ax.formatter, want, "tick") == _labels(graph)

    def test_a_period_unit(self, tmp_path, mode):
        """%ty past year 100: r(min) to r(max) by r(delta), year 0 at its
        own place (not 1900)."""
        fig, _w = _past_fig(
            tmp_path, mode, [dar._L("line", "close", "yr"),
                             dar._si((1300, -500))], _rows("y_lo_da"))
        ax = dar._da_axis(fig, "below")
        want = dr._dash_literal_to_ms(_ts_ticks(_TS["y_lo_da"]),
                                      "ty").tolist()
        assert list(ax.ticker.ticks) == want
        assert js_texts(ax.formatter, want, "tick") == _labels("past_ty")


class TestTheOracle:
    def test_asks_tsnatscale_in_stata_numbers(self, monkeypatch, tmp_path):
        """Built inside Stata the page asks _tsnatscale over the axis's
        Stata numbers and draws its list."""
        import test_stata_ticks as tst
        fake = tst._FakeStata()
        orig = fake.SFIToolkit.stata
        row = _TS["d_hi8"]

        def stata(cmd):
            orig(cmd)
            if cmd == "capture _tsnatscale 14977 100000000 5, daily":
                fake._sc.update({"r(min)": row["min"],
                                 "r(max)": row["max"],
                                 "r(n)": float(len(row["list"]))})
                fake._gl["r(list)"] = " ".join(
                    "%.17g" % v for v in row["list"])
                fake._st["rc"] = 0
        fake.SFIToolkit.stata = staticmethod(stata)
        monkeypatch.setitem(sys.modules, "sfi", fake)
        tst._oracle_reset(True)
        try:
            fig, _w = _past_fig(tmp_path, "saved", [
                dar._L("line", "close", "date"), dar._si((1300, 1e8))], [])
        finally:
            tst._oracle_reset(False)
        assert "capture _tsnatscale 14977 100000000 5, daily" in fake.cmds
        ax = dar._da_axis(fig, "below")
        assert list(ax.ticker.ticks) == dr._dash_literal_to_ms(
            row["list"], "td").tolist()

    def test_the_kept_answer(self, monkeypatch):
        """_dash_stata_oracle_kept: Stata's answer, appended to a list
        table as _dash_stata_or_model appends it; None with the oracle
        off, and a table that is no list is left alone."""
        import test_stata_ticks as tst
        monkeypatch.setitem(sys.modules, "sfi",
                            tst._FakeStata(tst._ends))
        assert dr._dash_stata_oracle_kept([], 1.0, 9.0, 5, "") is None
        tst._oracle_reset(True)
        try:
            table = []
            got = dr._dash_stata_oracle_kept(table, 1.0, 9.0, 5, "")
            assert got == [1.0, 9.0]
            assert table == [(1.0, 9.0, 5, "", (1.0, 9.0))]
            assert dr._dash_stata_oracle_kept(None, 2.0, 8.0, 5, "") == \
                [2.0, 8.0]
        finally:
            tst._oracle_reset(False)

    def test_no_answer_keeps_natscale(self):
        """With no Stata answer the axis keeps natscale over its numbers."""
        lo = float(dr._dash_literal_to_ms([14977], "td")[0])
        hi = float(dr._dash_literal_to_ms([1e8], "td")[0])
        want = dr._dash_literal_to_ms(
            dr._dash_natscale_ticks(14977, 1e8, 5), "td").tolist()
        assert dr._dash_off_date_ticks(lo, hi, 5, "td") == want
        assert dr._dash_off_date_ticks(lo, hi, 5, "td", table=[]) == want


# ---------------------------------------------------------------------------
# The dump formats by a variable's format, xvarformat() and zlabel()
# ---------------------------------------------------------------------------

def _auto_figs(mode, plots, formats, go=None):
    from conftest import render_models
    spec = tda._spec(plots, go or {}, formats=formats)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            _tag, sp, dp = tda._write(spec, "auto")
            r = render_models(dr.DashRenderer(sp, dp))
            figs = tb._panels(list(r.figures.values()))
        else:
            figs = tda._figs(mode, spec)
    return figs[0], [str(x.message) for x in w]


_BASE = {"weight": "%8.0gc", "mpg": "%8.0g"}
_DUMP = [
    # (graph row, plot options, formats, letter)
    ("fmt_var21x", {}, {"weight": "%21x"}, "x"),
    ("fmt_xvar21x", {"xvarformat": "%21x"}, {}, "x"),
    ("fmt_xvarl21x", {"xvarformat": "%-21x"}, {}, "x"),
    ("fmt_xvar12s", {"xvarformat": "%12s"}, {}, "x"),
    ("fmt_yvar16H", {"yvarformat": "%16H"}, {}, "y"),
    ("fmt_var8H", {}, {"mpg": "%8H"}, "y"),
    ("fmt_var16L", {}, {"mpg": "%16L"}, "y"),
]


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("key, opts, fmts, letter", _DUMP,
                         ids=[d[0] for d in _DUMP])
def test_axis_dump_formats(mode, key, opts, fmts, letter):
    """A variable's own or a layer's %21x, %16H, %8H, %16L or %-21x labels
    the axis as twoway labels it, with no note."""
    f, msgs = _auto_figs(mode, [P("scatter", "mpg", "weight", **opts)],
                         {**_BASE, **fmts})
    ax = tda._axis(f, letter)
    got = js_texts(ax.formatter, tda._ticks(f, letter), "tick")
    assert got == _labels(key, letter)
    assert not [m for m in msgs if "%9.0g" in m], msgs


_PRICE_FMT = {"price": "%8.0gc"}


@pytest.mark.parametrize("mode", _MODES)
class TestKeyFormats:
    @pytest.mark.parametrize("fmt, key", [
        ("%21x", "key_cv21x"), ("%8L", "key_cv8L"), ("%12s", "key_cv12s"),
        ("%16H", None)])
    def test_zlabel_dump_format(self, tmp_path, mode, fmt, key):
        """zlabel(, format(%21x)), %8L, %12s and %16H write the key as
        twoway writes it (key_cv21x, key_cv8L, key_cv12s; key_z21x and
        key_z16H on a contour), with no note."""
        root, w, _o = dar._build(tmp_path, mode, [dar._sc("price")],
                                 dar._PRICE, formats=_PRICE_FMT,
                                 go={"zlabel": ", format(%s)" % fmt})
        ticks, _ov = dar._bar(root)
        assert dar._bar_texts(root) == [
            dr._dash_fmt_dump(fmt, t) for t in ticks]
        if key:
            assert dar._bar_texts(root) == _labels(key, "right")
        assert dar._znotes(w) == []

    def test_the_variables_format_is_not_the_keys(self, tmp_path, mode):
        """A colour variable in %21x keys in %8.0gc, as twoway keys it
        (key_cvvar21x, key_var21x)."""
        root, _w, _o = dar._build(tmp_path, mode, [dar._sc("price")],
                                  dar._PRICE, formats={"price": "%21x"})
        assert dar._bar_texts(root) == _labels("key_cvvar21x", "right")
