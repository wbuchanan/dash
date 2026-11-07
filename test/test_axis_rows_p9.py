"""
test_axis_rows_p9.py
WP-44 (AX-19, AX-20): the rows an axis reads.

AX-19: twoway reads each variable of a layer over the layer's own rows,
whether or not the layer's other variables are present there -- ``scatter
y x`` with y missing past row 20 ticks x 0(20)100 and ``scatter yy x2``
with x2 missing past row 20 ticks y 0(20)100 -- for every type that draws
its own variables (and lowess, fpfit and fpfitci's x); lfit, qfit, lpoly
and the ci fits tick over the complete rows they fit.  dash dropped the
rows a layer's partner misses from both axes (only rbar, rspike, rcap
and rcapsym kept them).

AX-20: a baroffset() bar is ticked over its data, and its scale is
widened half a bar and |baroffset()| bars each way (yxview.class
minmax_range); dash ticked the moved bars and spanned them only.

The export's requests for Stata's ticks follow the same rule
(test_stata_ticks.py::TestTheCompleteCaseTokens).

The truth is test/fixtures/axis_rows_truth.json
(scripts/extract_axis_rows_truth.do, StataNow 19.5, stcolor): each key's
rc, its axes' label values in Stata units and the range at the plot
region's edges.

Run with:  pytest test/test_axis_rows_p9.py -q
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
from test_by_scales import _major_ticks  # noqa: E402
from test_date_range import _filter, _saved, _served, _spec  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "axis_rows_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
_G = _T["graphs"]
_UNIT = {"%tq": "q", "%td": "d"}


def _frame(data):
    """The data set of extract_axis_rows_truth.do's *data* program, and
    its date formats."""
    if data == "_ar_m":
        n = np.arange(1, 101, dtype=float)
        y = np.where(n <= 20, n, np.nan)
        return pd.DataFrame({
            "x": n, "y": y, "y2": y + 3, "y3": y + 1,
            "yb": np.where(n <= 40, n, np.nan),
            "x2": np.where(n <= 20, n, np.nan), "yy": n, "xd": n + 1,
            "t": 119.0 + n}), {"t": "%tq"}
    k = np.arange(1, 9, dtype=float)
    if data == "_ar_q":
        return pd.DataFrame({"t": 163.0 + k, "y": k, "y0": 0.0 * k}), \
            {"t": "%tq"}
    if data == "_ar_n":
        return pd.DataFrame({"t": k, "y": k}), {}
    return pd.DataFrame({"t": 14975.0 + k, "y": k}), {"t": "%td"}


_PC = ("pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter")


def _layer(text):
    """One layer of a probe's command, as dash.ado writes it."""
    m = re.fullmatch(r"\s*(\w+)\s+([^,]*?)\s*(?:if\s+(.*?))?\s*(?:,(.*))?",
                     text)
    t, vs, opts = m.group(1), m.group(2).split(), m.group(4) or ""
    o = {w: w for w in opts.split()}
    for om in re.finditer(r"(\w+)\(([^)]*)\)", opts):
        o[om.group(1)] = om.group(2)
    for w in list(o):
        if "(" in w:
            del o[w]
    p = {"type": t, "options": o}
    if t == "tsline":
        p.update(yvar=vs[0], xvar="t")
    elif t == "tsrline":
        p.update(yvar1=vs[0], yvar2=vs[1], xvar="t")
    elif t in _PC:
        p.update(y1var=vs[0], x1var=vs[1], y2var=vs[2], x2var=vs[3])
    elif t in ("rpcap", "rpspike"):
        p.update(yvar1=vs[0], yvar2=vs[1], yvar=vs[2], xvar=vs[3])
    elif len(vs) == 3:
        p.update(yvar1=vs[0], yvar2=vs[1], xvar=vs[2])
    else:
        p.update(yvar=vs[0], xvar=vs[1])
    return p, m.group(3)


def _plots(cmd, df):
    """The layers of *cmd* and the frame they draw; a layer's if is
    applied by dropping the rows it leaves out (all this file needs)."""
    body = cmd[len("twoway "):].strip().rstrip(",")
    parts = (re.findall(r"\(([^)]*(?:\([^)]*\)[^)]*)*)\)", body)
             if body.startswith("(") else [body])
    out = []
    for part in parts:
        p, cond = _layer(part)
        if cond:
            mm = re.fullmatch(r"(\w+)\s*<=\s*([\d.]+)", cond.strip())
            df = df.loc[df[mm.group(1)] <= float(mm.group(2))].reset_index(
                drop=True)
        ys = p.get("yvar", "")
        if p["type"] == "scatter" and len(cmd.split(",")[0].split()) > 4 \
                and not cond and len(parts) == 1:
            # scatter y yb x: one layer per y, as dash.ado writes it.
            names = cmd.split(",")[0].split()[2:]
            out += [{"type": "scatter", "yvar": v, "xvar": names[-1],
                     "options": {}} for v in names[:-1]]
            continue
        del ys
        out.append(p)
    return out, df


def _build(mode, tmp_path, plots, df, fmts, table=None, filters=None):
    spec = _spec(plots, formats=fmts, filters=filters)
    if table:
        spec["build_options"]["stata_ticks"] = table
    if mode == "saved":
        r, _w = _saved(tmp_path, spec, df)
        return r, tda.tb._panels(list(r.figures.values()))
    doc, _w = _served(tmp_path, spec, df)
    return doc, tda.tb._panels(tda.tb._figs_of(doc.roots))


def _axis(fig, letter):
    side = {"x": "below", "y": "left"}[letter]
    return [a for a in getattr(fig, side) if hasattr(a, "ticker")][0]


def _units(values, fmt):
    """Bokeh positions in Stata units of a variable of format *fmt*."""
    if fmt not in _UNIT:
        return [float(v) for v in values]
    return [round(dr._dash_unix_ms_to_unit(float(v), _UNIT[fmt]), 6)
            for v in values]


def _fmts(df, dates):
    return {c: dates.get(c, "%9.0g") for c in df.columns}


def _date_letter(plots, dates):
    """The letter the date variable t is drawn on, or None."""
    if not dates or not any(p.get("xvar") == "t" for p in plots):
        return None
    hz = any("horizontal" in p["options"] for p in plots)
    return "y" if hz else "x"


def _drawn(fig, letter, fmt):
    ticks = _units(_major_ticks(_axis(fig, letter)) or [], fmt)
    rng = getattr(fig, letter + "_range")
    return ticks, _units([rng.start, rng.end], fmt)


_AX19 = sorted(k for k, g in _G.items() if k.startswith("ax19_")
               and g["rc"] == 0)
_AX20 = sorted(k for k, g in _G.items() if k.startswith("ax20_"))


def _probe(mode, tmp_path, key, table=None):
    g = _G[key]
    df, dates = _frame(g["data"])
    plots, df = _plots(g["command"], df)
    _r, figs = _build(mode, tmp_path, plots, df, _fmts(df, dates),
                      table=table(plots, df) if table else None)
    dl = _date_letter(plots, dates)
    return {L: _drawn(figs[0], L, dates.get("t") if L == dl else None)
            for L in ("x", "y")}


def _close(got, want, span):
    return all(abs(a - b) <= 0.04 * span for a, b in zip(got, want))


class TestTheFixture:
    def test_meta(self):
        assert all(_T["_meta"].get(k) for k in (
            "stata_version", "born_date", "dash_commit", "extracted",
            "source"))
        assert len(_AX19) >= 40 and len(_AX20) == 10

    def test_the_rule_measured(self):
        """twoway's rule itself: y missing past row 20 still ticks x over
        all 100 rows; x2 missing past row 20 still ticks y over them; an
        lfit ticks over the rows it fits."""
        assert _G["ax19_scatter"]["x"] == [0, 20, 40, 60, 80, 100]
        assert _G["ax19_scatter_xmiss"]["y"] == [0, 20, 40, 60, 80, 100]
        assert _G["ax19_lfit"]["x"] == [0, 5, 10, 15, 20]
        assert _G["ax20_n_three"]["x"] == [0, 2, 4, 6, 8]


class TestEachVariableOverItsOwnRows:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", _AX19)
    def test_each_probe(self, tmp_path, mode, key):
        """Each axis is ticked as twoway ticks it: every variable over
        the layer's own rows."""
        got = _probe(mode, tmp_path, key)
        g = _G[key]
        for L in ("x", "y"):
            assert got[L][0] == [float(v) for v in g[L]], (key, L, got[L])


class TestOffsetBars:
    @staticmethod
    def _table(key):
        """The answer Stata gives at export over each axis's data: the
        bars' own x (the tick input twoway reads) and y."""
        g = _G[key]

        def tab(plots, df):
            hz = "horizontal" in plots[0]["options"]
            fmt = "%tq" if g["data"] == "_ar_q" else \
                "%td" if g["data"] == "_ar_d" else ""
            out = []
            for L, var in (("x", "t"), ("y", "y")):
                drawn = {"x": "y", "y": "x"}[L] if hz else L
                ticks = [float(v) for v in g[drawn]]
                unit = _UNIT.get(fmt, "") if var == "t" else ""
                out.append([float(df[var].min()), float(df[var].max()), 5,
                            unit, ticks])
            return out
        return tab

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", _AX20)
    def test_ticks_and_range(self, tmp_path, mode, key):
        """The bars' own x is the tick input, so Stata's answer over it is
        drawn; the scale spans half a bar and |baroffset()| bars each way
        of every bar, as twoway's (within 4% of the span)."""
        g = _G[key]
        got = _probe(mode, tmp_path, key, table=self._table(key))
        for L in ("x", "y"):
            assert got[L][0] == [float(v) for v in g[L]], (key, L, got[L])
            want = g[L + "_range"]
            assert _close(got[L][1], want, want[1] - want[0]), \
                (key, L, got[L][1], want)


class TestAfterAMove:
    @pytest.mark.parametrize("mode", MODES)
    def test_the_kept_rows_of_each_variable(self, tmp_path, mode):
        """A filter move keeps rows 1-60: x is ticked over the kept rows,
        the 40 whose y is missing among them (0(20)60), and a move back
        restores 0(20)100."""
        df, dates = _frame("_ar_m")
        plots = [{"type": "scatter", "yvar": "y", "xvar": "x",
                  "options": {}}]
        obj, figs = _build(mode, tmp_path, plots, df, _fmts(df, dates),
                           filters=[_filter("range", "yy")])
        assert _major_ticks(_axis(figs[0], "x")) == [0, 20, 40, 60, 80, 100]
        mv = tda._move_saved if mode == "saved" else tda._move_served
        figs = mv(obj, "RangeSlider", (1.0, 60.0))
        assert _major_ticks(_axis(figs[0], "x")) == [0, 20, 40, 60]
        figs = mv(obj, "RangeSlider", (1.0, 100.0))
        assert _major_ticks(_axis(figs[0], "x")) == [0, 20, 40, 60, 80, 100]


class TestTheHelpers:
    _PLOT = {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}

    def test_layer_rows_vars(self):
        """Each letter's variables before horizontal turns them; none for
        a fit twoway ticks over its complete rows; x only for lowess."""
        assert dr._dash_layer_rows_vars(self._PLOT) == {"x": ["x"],
                                                        "y": ["y"]}
        assert dr._dash_layer_rows_vars(
            {"type": "pcspike", "y1var": "a", "x1var": "b", "y2var": "c",
             "x2var": "d"}) == {"x": ["b", "d"], "y": ["a", "c"]}
        assert dr._dash_layer_rows_vars(dict(self._PLOT, type="lfit")) \
            == {"x": [], "y": []}
        assert dr._dash_layer_rows_vars(dict(self._PLOT, type="lowess")) \
            == {"x": ["x"], "y": []}
        assert dr._dash_layer_rows_vars(
            {"type": "histogram", "var": "x"}) == {"x": [], "y": []}

    def test_rows_partial(self):
        """Only a row holding one of the layer's variables and missing
        another makes the hull differ from the drawn rows."""
        nan = float("nan")
        assert dr._dash_rows_partial(self._PLOT, {"x": [1.0, 2.0],
                                                  "y": [1.0, nan]})
        assert not dr._dash_rows_partial(self._PLOT, {"x": [1.0, nan],
                                                      "y": [1.0, nan]})
        assert not dr._dash_rows_partial(self._PLOT, {"x": [1.0]})

    def _layer(self, static=False):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        nan = float("nan")
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [5.0, nan, nan]})
        fig = figure()
        r = fig.scatter(x="x", y="y", source=ColumnDataSource(
            {"x": [1.0], "y": [5.0]}))
        return fig, r, src

    def test_stamp_layer_rows(self):
        """The layer's first renderer carries the rows; a layer whose
        rows are all whole carries none."""
        _fig, r, src = self._layer()
        assert dr._dash_stamp_layer_rows([r], self._PLOT, src) is r
        assert r._dash_rows_hull["x"] == ["x"] \
            and r._dash_rows_hull["source"] is src
        _fig, r2, _src = self._layer()
        from bokeh.models import ColumnDataSource
        whole = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        assert dr._dash_stamp_layer_rows([r2], self._PLOT, whole) is None

    def test_rows_hull_values(self):
        """Each variable over the view's rows, finite ones only."""
        from bokeh.models import CDSView, IndexFilter
        _fig, r, src = self._layer()
        dr._dash_stamp_layer_rows([r], self._PLOT, src)
        assert list(dr._dash_rows_hull_values(r, "x")) == [1.0, 2.0, 3.0]
        assert list(dr._dash_rows_hull_values(r, "y")) == [5.0]
        r._dash_rows_hull["view"] = CDSView(filter=IndexFilter([1, 2]))
        assert list(dr._dash_rows_hull_values(r, "x")) == [2.0, 3.0]
        assert dr._dash_rows_hull_values(r, "y").size == 0

    def test_rows_hull_units(self):
        """A variable's date units come from the glyph field that draws
        it; a plain field has none."""
        _fig, r, src = self._layer()
        dr._dash_stamp_layer_rows([r], self._PLOT, src)
        assert dr._dash_rows_hull_units(r._dash_rows_hull, "x") is None
        from bokeh.models import CustomJSTransform
        r.glyph.x = {"field": "x", "transform": CustomJSTransform(
            v_func="return xs;", tags=[dr._DASH_DATE_UNITS_TAG + "td"])}
        assert dr._dash_rows_hull_units(r._dash_rows_hull, "x") == "td"

    def test_rows_source(self):
        """The served rows source: the layer's variables over every row
        of the frame, with its labels; none for whole rows."""
        df = pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, float("nan")],
                           "z": [0.0, 0.0]}, index=[7, 9])
        s = dr._dash_rows_source(df, self._PLOT)
        assert sorted(s.data) == ["index", "x", "y"]
        assert list(s.data["index"]) == [7, 9]
        assert dr._dash_rows_source(df.dropna(), self._PLOT) is None


class TestTheBarSpan:
    @staticmethod
    def _gm():
        return tda.tb._mapper() if hasattr(tda.tb, "_mapper") else \
            dr.GlyphMapper(dr.SchemeParser("s2color"), dr.OptionTranslator())

    def test_bar_offset_span(self):
        """Half a bar and |baroffset()| bars each way of x; nothing with
        no offset."""
        gm = self._gm()
        xs = pd.Series([1.0, 8.0])
        sp = gm._bar_offset_span("t", xs, 1.0, offset=-3)
        assert list(sp[gm._BAR_LO]) == [-2.5, 4.5]
        assert list(sp[gm._BAR_HI]) == [4.5, 11.5]
        assert gm._bar_offset_span("t", xs, 1.0, offset=0) == {}

    def test_stamp_bar_offset(self):
        """The tick input is the bar's x, the span the two columns."""
        gm = self._gm()

        class R:
            pass
        r = R()
        gm._stamp_bar_offset(r, "t")
        assert r._dash_tick_fields == {"x": ("t",)}
        assert r._dash_span_fields == {"x": (gm._BAR_LO, gm._BAR_HI)}


class TestTheHelp:
    @staticmethod
    def _text():
        from test_help_claims_1 import _help
        return " ".join(_help().split())

    def test_the_rows_sentence(self):
        """The axis paragraph names twoway's rule, with this file's
        measured example (ax19_scatter, ax19_lfit)."""
        assert ("Each variable of a layer is read over the layer's own "
                "rows, as {cmd:twoway} reads it, whether or not the layer's "
                "other variables are there: {cmd:scatter y x} with {cmd:y} "
                "missing past observation 20 of 100 labels x 0(20)100"
                in self._text())
        assert _G["ax19_scatter"]["x"] == [0, 20, 40, 60, 80, 100]

    def test_the_baroffset_sentence(self):
        """baroffset()'s entry gives twoway's ticks and span (ax20_n_three:
        0(2)8, -2.5 to 11.5 within the region's margin)."""
        assert ("The axis is ticked over the bars' own x and spans half a "
                "bar and |{it:#}| bars each way of every bar, as "
                "{cmd:twoway}'s ({cmd:bar y t, baroffset(3)} over t 1 to 8 "
                "labels 0(2)8 and runs from -2.5 to 11.5)." in self._text())
        g = _G["ax20_n_three"]
        assert g["x"] == [0, 2, 4, 6, 8]
        assert -2.9 < g["x_range"][0] < -2.5 and 11.5 < g["x_range"][1] < 11.9
