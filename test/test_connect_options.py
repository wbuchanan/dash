"""connect() and cmissing() are drawn as twoway draws them (WP-30 P1.8a).

The defect, measured at c96facd (StataNow 19.5): ``dash scatter y x, c(l)``
drew markers only and named connect() in its note; ``c(J)`` and ``c(L)``
drew the same single straight Line as no option; ``cmissing(n)`` drew a
bridged line (map_line's ``dropna``); and ``function y=sqrt(x^2-1),
range(-2 2)`` drew a gap over its missing middle where twoway bridges it.

twoway's own answers are test/fixtures/connect_truth.json, written by
scripts/extract_connect_truth.do: each probe's command, rc, note and error
lines and the subpaths of its SVG in data units (P probes on data T, F
probes on auto with mpg missing in row 5), the spellings twoway reads as
each style (S), its refusals (R) and the forty types' answers (M).  The
area cases of test_twoway_option_parity.cscript (CM-01..CM-12) hold dash's
parse to the same fixture; this file holds what is drawn, in both modes,
before and after a saved or served filter move.
"""
import json
import os
import random
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import HoverTool, Line, VArea

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import render_models  # noqa: E402
from js_runner import JsSession, requires_node, run_js  # noqa: E402
from test_join_order import (_served, _served_figs, _served_move,  # noqa: E402
                             _figs_of, _write)

_REPO = os.path.join(_HERE, "..")
with open(os.path.join(_HERE, "fixtures", "connect_truth.json"),
          encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_P = _FIX["probes"]

# Data T of the fixture (scripts/extract_connect_truth.do).
_T = pd.DataFrame({
    "x": [2, 5, 3, 6, 1, np.nan, 7, 4],
    "y": [10, 20, np.nan, 40, 50, 45, 60, 70],
    "y2": [12, 22, 32, 42, np.nan, 47, 62, 72],
    "t": [1, 2, 3, 4, 5, 6, 7, 8],
    "foreign": [0, 1, 0, 1, 0, 1, 0, 1],
}, dtype=float)
_T["y3"] = _T["y"] + 1
# Data TIE.
_TIE = pd.DataFrame({"x": [1, 3, 3, 2, 4, 5, 6.0],
                     "y": [10, 20, 30, 40, 50, 60, 70.0]})


def _pl(ptype, y="y", x="x", **o):
    if ptype in ("rline", "rconnected", "rarea", "tsrline"):
        return {"type": ptype, "yvar1": y, "yvar2": "y2", "xvar": x,
                "options": o}
    return {"type": ptype, "yvar": y, "xvar": x, "options": o}


def _fn(expr, **o):
    return {"type": "function", "expr": expr, "options": o}


# Each probe as dash.ado writes it (CM-12 holds dash.ado to these): a
# scatter y given a connect() element is "connected" with its canonical
# style, cmissing() is "n" or "y", per y.
_PROBE_PLOTS = {
    "P01": [_pl("connected", connect="direct")],
    "P02": [_pl("line", connect="stairstep")],
    "P03": [_pl("line", connect="stepstair", sort="sort")],
    "P04": [_pl("line", connect="ascending")],
    "P08": [_pl("line", cmissing="n")],
    "P09": [_pl("connected", connect="direct", cmissing="n")],
    "P10": [_pl("connected", connect="direct", cmissing="n", sort="sort")],
    "P12": [_pl("line", cmissing="n"), _pl("line", y="y2")],
    "P13": [_pl("line", cmissing="n"), _pl("line", y="y2", cmissing="n")],
    "P14": [_pl("rline", cmissing="n")],
    "P15": [_pl("rconnected", cmissing="n")],
    "P16": [_pl("line", cmissing="n", connect="stairstep")],
    "P17": [_pl("line", cmissing="n", connect="ascending")],
    "P18": [_fn("sqrt(x^2-1)", range="-2 2")],
    "P19": [_fn("sqrt(x^2-1)", range="-2 2", cmissing="n")],
    "P20": [_pl("connected", connect="direct"), _pl("scatter", y="y2")],
    "P21": [_pl("scatter"), _pl("connected", y="y2", connect="direct")],
    "P22": [_pl("connected", connect="direct"),
            _pl("connected", y="y2", connect="direct"),
            _pl("connected", y="y3", connect="direct")],
    "P23": [_pl("connected", connect="stairstep"),
            _pl("connected", y="y2", connect="stairstep"),
            _pl("scatter", y="y3")],
    "P24": [_pl("connected", connect="direct"), _pl("scatter", y="y2"),
            _pl("connected", y="y3", connect="stairstep")],
    "P25": [_pl("line", connect="stairstep")],
    "P26": [_pl("connected", connect="direct", sort="sort")],
    "P29": [_pl("tsline", x="t", connect="stairstep")],
    "P29b": [_pl("tsrline", x="t", cmissing="n")],
    "P30": [{"type": "scatteri", "values": [[1.0, 2.0], [3.0, 4.0],
                                            [2.0, 6.0]],
             "options": {"connect": "stairstep"}}],
}
_PROBE_DATA = {"P05": _TIE}
_PROBE_PLOTS["P05"] = [_pl("line", connect="ascending")]
_PROBE_PLOTS["P11"] = [dict(_pl("line", cmissing="n"), if_expr="t != 5")]


def _spec_of(names, bo=None):
    graphs = [(n, _PROBE_PLOTS[n], {}, {"if_expr": "", "in_expr": ""})
              for n in names]
    return tp._spec(graphs=graphs, build_options=bo)


def _saved_render(spec, df):
    _, sp, dp = _write(spec, df, tp._VALUE_LABELS, tp._LABEL_NAMES)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _visible_lines(fig):
    """Each visible Line renderer's (x, y) columns, in drawing order."""
    out = []
    for g in fig.renderers:
        if not isinstance(g.glyph, Line):
            continue
        if g.glyph.line_alpha == 0:
            continue
        d = g.data_source.data
        out.append((dr._dash_float_values(d[g.glyph.x]),
                    dr._dash_float_values(d[g.glyph.y])))
    return out


def _runs(xs, ys):
    """The vertex runs of one Line, split at non-finite values."""
    out, cur = [], []
    for a, b in zip(xs, ys):
        if np.isfinite(a) and np.isfinite(b):
            cur.append((float(a), float(b)))
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _fig_runs(fig):
    return [r for xs, ys in _visible_lines(fig) for r in _runs(xs, ys)]


def _truth_runs(pid):
    return [[tuple(p) for p in sp["pts"]] for sp in _P[pid]["paths"]
            if not sp["closed"]]


def _same(a, b, tol):
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for (x1, y1), (x2, y2) in zip(ra, rb):
            if abs(x1 - x2) > tol[0] or abs(y1 - y2) > tol[1]:
                return False
    return True


def _tol(runs):
    pts = [p for r in runs for p in r] or [(0.0, 0.0)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (2e-3 * max(1.0, max(xs) - min(xs)),
            2e-3 * max(1.0, max(ys) - min(ys)))


# ===========================================================================
# The fixture
# ===========================================================================

class TestTheFixture:

    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        assert {"stata_version", "born_date", "dash_commit",
                "extracted"} <= set(m)
        assert str(m["stata_version"]).startswith("19.")
        missing = [p for p in list(_PROBE_PLOTS) + ["P06", "P07", "R-01",
                                                    "R-02", "C_BOGUS2"]
                   if p not in _P]
        assert not missing, missing
        # The 39 types scripts/extract_connect_truth.do puts each of
        # c(J) c(L) c(i) c(bogus) cmissing(n) cmissing(x) to.
        assert len(_FIX["matrix"]) == 39
        assert all(len(v) == 6 for v in _FIX["matrix"].values())


# ===========================================================================
# The vertex rule and the glyph helper
# ===========================================================================

def _rule_runs(xs, ys, style, cmiss):
    xi, yi = dr._dash_join_vertices(xs, ys, style, cmiss)
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    vx = np.where(xi >= 0, xs[np.clip(xi, 0, None)], np.nan)
    vy = np.where(yi >= 0, ys[np.clip(yi, 0, None)], np.nan)
    return _runs(vx, vy)


class TestTheVertices:

    def test_every_rule(self):
        tx, ty = _T["x"].tolist(), _T["y"].tolist()
        cases = {
            "P02": (tx, ty, "stairstep", "y"),
            "P04": (tx, ty, "ascending", "y"),
            "P05": (_TIE["x"].tolist(), _TIE["y"].tolist(), "ascending",
                    "y"),
            "P08": (tx, ty, "direct", "n"),
            "P16": (tx, ty, "stairstep", "n"),
            "P17": (tx, ty, "ascending", "n"),
        }
        # P03 is joined in x order (sort): the rule is given that order.
        o = np.argsort(np.where(np.isnan(tx), np.inf, tx), kind="stable")
        cases["P03"] = (list(np.asarray(tx)[o]), list(np.asarray(ty)[o]),
                        "stepstair", "y")
        bad = []
        for pid, (xs, ys, st, cm) in cases.items():
            got = _rule_runs(xs, ys, st, cm)
            want = _truth_runs(pid)
            if not _same(got, want, _tol(want)):
                bad.append((pid, got, want))
        # none gives the rows (the glyph hides them); an unknown style is
        # direct; at most 3n - 2 vertices.
        xi, yi = dr._dash_join_vertices(tx, ty, "none", "y")
        if list(xi) != [0, 1, 3, 4, 6, 7] or list(yi) != list(xi):
            bad.append(("none", list(xi)))
        if [list(a) for a in dr._dash_join_vertices(tx, ty, "Bogus", "x")] \
                != [list(a) for a in dr._dash_join_vertices(tx, ty, "direct",
                                                            "y")]:
            bad.append("unknown style or cmissing")
        n = 1000
        xi, _ = dr._dash_join_vertices(np.arange(n), np.arange(n),
                                       "stairstep", "y")
        if len(xi) != 2 * n - 1 or len(xi) > 3 * n - 2:
            bad.append(("bound", len(xi)))
        assert not bad, bad


class TestTheJoinGlyph:

    def test_each_style(self):
        from bokeh.plotting import figure
        mapper = dr.GlyphMapper(dr.SchemeParser())
        bad = []
        for style in ("direct", "ascending", "stairstep", "stepstair",
                      "none"):
            for rowid in (True, False):
                data = {"x": [1.0, 3.0, 2.0], "y": [5.0, 6.0, 7.0],
                        "make": ["a", "b", "c"]}
                if rowid:
                    data[dr._ROW_ID_COLUMN] = [10, 11, 12]
                src = dr.ColumnDataSource(data)
                fig = figure()
                r = dr._dash_join_glyph(
                    mapper, fig, {"connect": style},
                    dict(x="x", y="y", source=src), role="line",
                    hover=("y", "x"))
                if not isinstance(r.glyph, Line):
                    bad.append((style, "not a Line"))
                d = src.data
                real = [i for i, v in enumerate(d["make"]) if v is not None]
                if style in ("direct", "none"):
                    if d["x"] != [1.0, 3.0, 2.0]:
                        bad.append((style, "direct data changed", d["x"]))
                elif style == "stairstep" and rowid:
                    if (list(d["make"]) != ["a", None, "b", None, "c"]
                            or list(d[dr._ROW_ID_COLUMN])
                            != [10, None, 11, None, 12]):
                        bad.append((style, d))
                if rowid and style not in ("direct", "none"):
                    if getattr(src, "_dash_join", None) is None:
                        bad.append((style, "no _dash_join on a row-id source"))
                if not rowid and getattr(src, "_dash_join", None) is not None:
                    bad.append((style, "_dash_join without a row id"))
                if not real:
                    bad.append((style, "no observation kept"))
                hovered = [h for h in fig.tools if isinstance(h, HoverTool)
                           and r in (h.renderers or [])]
                if (style == "none") == bool(hovered):
                    bad.append((style, "hover", len(hovered)))
                if style == "none" and r.glyph.line_alpha != 0:
                    bad.append((style, "visible"))
        assert not bad, bad


class TestHandWrittenSpecs:

    def test_defaults(self):
        for v in ("Bogus", "<script>", "x" * 10000, 3):
            assert dr._dash_join_spec({"connect": v, "cmissing": "x"}) \
                == ("direct", "y")
        assert dr._dash_join_spec(None) == ("direct", "y")


# ===========================================================================
# What is drawn, both modes, against twoway's paths
# ===========================================================================

_DRAWN = ["P01", "P02", "P03", "P04", "P08", "P09", "P10", "P11", "P12",
          "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21",
          "P22", "P23", "P24", "P25", "P26", "P29", "P29b", "P30"]


def _drawn_figs(mode, names, df):
    spec = _spec_of(names)
    if mode == "saved":
        r = _saved_render(spec, df)
        return _figs_of(r._last_layout_root)
    return _served_figs(_served(spec, df))


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestDrawnAsTwowayDrawsThem:
    """Every P probe, each a graph of one page: the visible Lines' vertex
    runs equal twoway's subpaths (scatter given connect(), the styles,
    cmissing(n) per y and per bound, sort, if, function's bridge and
    break, tsline, tsrline, scatteri)."""

    def test_every_probe(self, mode):
        bad = []
        figs = _drawn_figs(mode, _DRAWN, _T)
        assert len(figs) == len(_DRAWN)
        figs_tie = _drawn_figs(mode, ["P05"], _TIE)
        for pid, fig in list(zip(_DRAWN, figs)) + [("P05", figs_tie[0])]:
            got = _fig_runs(fig)
            want = _truth_runs(pid)
            if not _same(got, want, _tol(want)):
                bad.append((pid, [r[:4] for r in got], [r[:4] for r in want]))
        assert not bad, bad


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestConnectNone:

    def test_no_line_key_kept(self, mode):
        spec = tp._spec(graphs=[("g1", [
            _pl("line", connect="none", lcolor="red%50"),
            _pl("connected", y="y2", connect="none")], {"legend": "on"},
            {})])
        if mode == "saved":
            fig = _figs_of(_saved_render(spec, _T)._last_layout_root)[0]
        else:
            fig = _served_figs(_served(spec, _T))[0]
        lines = [g for g in fig.renderers if isinstance(g.glyph, Line)]
        assert len(lines) == 2
        assert all(g.glyph.line_alpha == 0 for g in lines)
        hovered = {id(r) for h in fig.tools if isinstance(h, HoverTool)
                   for r in (h.renderers or [])}
        assert not any(id(g) in hovered for g in lines)
        items = [it for lg in fig.legend for it in lg.items]
        assert len(items) >= 2


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestFitsHonourConnect:
    """Each fit and the fit line of each ci type, stepped under c(J) and
    c(stepstair) as twoway steps it (every other segment level, then
    upright) and hidden under c(i); a ci band drawn from the line's source
    steps with it (F probes: twoway's band is stepped too)."""

    _FITS = ["lfit", "qfit", "lowess", "lpoly", "fpfit", "mspline", "mband",
             "kdensity", "lfitci", "qfitci", "lpolyci", "fpfitci"]

    def test_fit(self, mode):
        rng = np.random.default_rng(40)
        w = np.sort(rng.uniform(1800, 4800, 40))
        df = pd.DataFrame({"weight": w,
                           "mpg": 40 - w / 200 + rng.normal(0, 2, 40)})
        plots = []
        for f in self._FITS:
            for st in ("stairstep", "stepstair", "none"):
                if f == "kdensity":
                    plots.append({"type": f, "var": "mpg",
                                  "options": {"connect": st}})
                else:
                    plots.append({"type": f, "yvar": "mpg",
                                  "xvar": "weight",
                                  "options": {"connect": st}})
        graphs = [("g%d" % i, [p], {}, {}) for i, p in enumerate(plots)]
        spec = tp._spec(graphs=graphs)
        if mode == "saved":
            figs = _figs_of(_saved_render(spec, df)._last_layout_root)
        else:
            figs = _served_figs(_served(spec, df))
        bad = []
        for p, fig in zip(plots, figs):
            st = p["options"]["connect"]
            lines = [g for g in fig.renderers if isinstance(g.glyph, Line)]
            if not lines:
                bad.append((p["type"], st, "no line"))
                continue
            g = lines[0]
            if st == "none":
                if g.glyph.line_alpha != 0:
                    bad.append((p["type"], st, "visible"))
                continue
            xs = dr._dash_float_values(g.data_source.data[g.glyph.x])
            ys = dr._dash_float_values(g.data_source.data[g.glyph.y])
            ok = np.isfinite(xs) & np.isfinite(ys)
            xs, ys = xs[ok], ys[ok]
            first = 0 if st == "stairstep" else 1
            # stairstep: level first (y equal), stepstair: upright first.
            seg = [(ys[i] == ys[i + 1]) if (i % 2 == 0) == (first == 0)
                   else (xs[i] == xs[i + 1]) for i in range(len(xs) - 1)]
            if len(xs) < 3 or not all(seg):
                bad.append((p["type"], st, "not stepped"))
            for b in fig.renderers:
                if (isinstance(b.glyph, VArea)
                        and b.data_source is g.data_source
                        and len(b.data_source.data[b.glyph.x]) != len(
                            g.data_source.data[g.glyph.x])):
                    bad.append((p["type"], st, "band not stepped"))
        assert not bad, bad


# ===========================================================================
# After moves
# ===========================================================================

def _moved_spec(plots):
    return tp._spec(graphs=[("g1", plots, {}, {})],
                    build_options={"filter": "foreign, type(dropdown)"})


def _kept_rows(df, plot):
    """The rows a Foreign move keeps, in the plot's join order (data order;
    x order under sort), as _dash_join_vertices is given them."""
    d = df[df["foreign"] == 1]
    if (plot["options"] or {}).get("sort") == "sort":
        d = d.iloc[np.argsort(np.where(np.isnan(d["x"]), np.inf, d["x"]),
                              kind="stable")]
    return d


_MOVE_CASES = [
    ("cmissing n", _pl("line", cmissing="n")),
    ("ascending", _pl("line", connect="ascending")),
    ("stairstep", _pl("line", connect="stairstep")),
    ("stepstair n", _pl("line", connect="stepstair", cmissing="n")),
]

# Foreign rows of data T: x 5 6 . 4, y 20 40 45 70 -- the missing x is a
# cmissing(n) break, 6 -> 4 an ascending break.


@requires_node
class TestAfterASavedMove:

    def test_breaks_and_stairs_are_rebuilt(self):
        from test_saved_filter_layers import _move
        spec = _moved_spec([p for _, p in _MOVE_CASES])
        r = _saved_render(spec, _T)
        _move(r, ("Select", "Foreign"))
        fig = _figs_of(r._last_layout_root)[0]
        lines = [g for g in fig.renderers if isinstance(g.glyph, Line)]
        bad = []
        for (name, plot), g in zip(_MOVE_CASES, lines):
            d = g.data_source.data
            kept = _kept_rows(_T, plot)
            st, cm = dr._dash_join_spec(plot["options"])
            want = _rule_runs(kept["x"].tolist(), kept["y"].tolist(), st, cm)
            got = _runs(dr._dash_float_values(d["x"]),
                        dr._dash_float_values(d["y"]))
            if got != want:
                bad.append((name, got, want))
            # A break is NaN, never 0; a vertex no row owns has a null id.
            ys = [v for v in d["y"]]
            if any(v == 0 for v in ys):
                bad.append((name, "a vertex at 0"))
            ids = list(d[dr._ROW_ID_COLUMN])
            # null comes back from the page as None or NaN.
            n_real = sum(1 for v in ids if v is not None and v == v)
            if n_real != len(kept if cm == "n" else
                             kept.dropna(subset=["x", "y"])):
                bad.append((name, "row ids", ids))
        assert not bad, bad

    def test_the_brush_ignores_synthetic_rows(self):
        """A sum KPI after a move on a stepped line equals the plain
        line's: the synthetic rows reach no KPI."""
        from test_saved_filter_layers import _move
        outs = []
        for opts in ({}, {"connect": "stairstep"}):
            spec = tp._spec(graphs=[("g1", [_pl("line", **opts)], {}, {})],
                            kpis=[tp._kpi("k1", "sum", "y")],
                            build_options={"filter":
                                           "foreign, type(dropdown)"})
            r = _saved_render(spec, _T)
            _move(r, ("Select", "Foreign"))
            outs.append(re.sub(r"\s+", " ", r.kpi_divs["k1"].text))
        assert outs[0] == outs[1]

    def test_kdensity_keeps_its_stairs(self):
        js = dr._FILTER_JS
        twin = js[js.index("function dash_join_rebuild"):
                  js.index("const ROW_ID = ")]
        own = js[js.index("function dash_own_col"):
                 js.index("// connect() and cmissing() after a move")]
        helpers = js[js.index("function dash_pctl"):
                     js.index("// agg_sources is a Bokeh model list")]
        lo = js.index("} else if (ac.type === 'kdensity') {")
        lo += len("} else if (ac.type === 'kdensity') {")
        end = js.index("src.data = { x: xs, y: ys };",
                       js.index("// DASH_KDE_RULE"))
        hi = js.index("src.change.emit();", end)
        block = js[lo:hi + len("src.change.emit();")]
        vals = [12.0, 14.0, 15.0, 18.0, 21.0, 22.0, 25.0, 30.0]
        ac = {"type": "kdensity", "x_grid": [10.0, 15.0, 20.0, 25.0, 30.0],
              "kernel": "epanechnikov", "bw_rule": "silverman",
              "bw_fixed": None, "wvar": None, "wtype": None,
              "join": {"style": "stairstep"}}
        harness = (own + twin + helpers
                   + "\nconst ac = " + json.dumps(ac)
                   + ";\nconst vals = " + json.dumps(vals)
                   + ";\nconst wts = null;"
                   + "\nconst src = { data: null, change: { emit: () => {} } };"
                   + "\nfor (let _i = 0; _i < 1; _i++) {\n" + block + "\n}"
                   + "\nprocess.stdout.write(JSON.stringify(src.data));")
        out = run_js(harness)
        xs = out["x"]
        assert len(xs) == 9
        assert xs[1] == xs[2] == 15.0 and out["y"][0] == out["y"][1]


@requires_node
class TestTheJsTwin:

    def test_agrees(self):
        js = dr._FILTER_JS
        twin = js[js.index("function dash_own_col"):
                  js.index("const ROW_ID = ")]
        rnd = random.Random(40)
        cases = []
        for _ in range(200):
            n = rnd.randint(0, 12)
            xs = [rnd.choice([None, 1, 2, 3, 3, 4, 5, 6]) for _ in range(n)]
            ys = [rnd.choice([None, 10, 20, 30]) for _ in range(n)]
            cases.append((xs, ys, rnd.choice(
                ["direct", "ascending", "stairstep", "stepstair", "none",
                 "bad"]), rnd.choice(["y", "n"])))
        src = (twin + "\nconst cases = " + json.dumps(cases) + ";\n"
               "const out = cases.map(([xs, ys, st, cm]) => {\n"
               "  const nd = {x: xs, y: ys, id: xs.map((_, i) => i)};\n"
               "  const r = dash_join_rebuild(nd, {x: 'x', y: 'y', style: st,"
               " cmiss: cm}, 'id');\n"
               "  return [r.x.map(v => Number.isNaN(v) ? null : v),"
               " r.y.map(v => Number.isNaN(v) ? null : v), r.id];\n"
               "});\nprocess.stdout.write(JSON.stringify(out));")
        got = run_js(src)
        bad = []
        for (xs, ys, st, cm), (gx, gy, gid) in zip(cases, got):
            fx = np.array([np.nan if v is None else v for v in xs], float)
            fy = np.array([np.nan if v is None else v for v in ys], float)
            xi, yi = dr._dash_join_vertices(fx, fy, st, cm)
            wx = [None if a < 0 or np.isnan(fx[a]) else fx[a] for a in xi]
            wy = [None if b < 0 or np.isnan(fy[b]) else fy[b] for b in yi]
            wid = [int(a) if a >= 0 and a == b else None
                   for a, b in zip(xi, yi)]
            if (gx, gy, gid) != (wx, wy, wid):
                bad.append((xs, ys, st, cm))
        assert not bad, bad[:3]

    def test_no_join_no_arg(self):
        spec = _moved_spec([_pl("line"), _pl("connected", y="y2")])
        r = _saved_render(spec, _T)
        assert r.filter_callbacks
        assert all("derived_join_json" not in cb.args
                   for cb in r.filter_callbacks)
        spec = _moved_spec([_pl("line", cmissing="n")])
        r = _saved_render(spec, _T)
        assert all("derived_join_json" in cb.args
                   for cb in r.filter_callbacks)


class TestAfterAServedMove:

    def test_moves(self):
        spec = _moved_spec([p for _, p in _MOVE_CASES])
        doc, _ = _served_move(spec, _T, ("Select", "Foreign"))
        fig = _served_figs(doc)[0]
        lines = [g for g in fig.renderers if isinstance(g.glyph, Line)]
        bad = []
        for (name, plot), g in zip(_MOVE_CASES, lines):
            kept = _kept_rows(_T, plot)
            st, cm = dr._dash_join_spec(plot["options"])
            want = _rule_runs(kept["x"].tolist(), kept["y"].tolist(), st, cm)
            d = g.data_source.data
            got = _runs(dr._dash_float_values(d["x"]),
                        dr._dash_float_values(d["y"]))
            if got != want:
                bad.append((name, got, want))
        assert not bad, bad


class TestLinkedConnectedMarkers:
    """A linked connected layer with a missing y: its markers take the
    linked view a scatter takes, its cmissing(n) line keeps its break."""

    def test_selection_and_break(self):
        spec = tp._spec(graphs=[
            ("g1", [_pl("connected", connect="direct", cmissing="n")], {},
             {}),
            ("g2", [_pl("scatter", y="y2")], {}, {})],
            build_options={"link": "g1 g2"})
        r = _saved_render(spec, _T)
        fig = _figs_of(r._last_layout_root)[0]
        line = [g for g in fig.renderers if isinstance(g.glyph, Line)][0]
        marks = [g for g in fig.renderers
                 if type(g.glyph).__name__ == "Scatter"][0]
        ys = dr._dash_float_values(line.data_source.data["y"])
        assert np.isnan(ys).any()
        # The markers draw from the linked (shared) source through a view.
        assert type(marks.view.filter).__name__ == "BooleanFilter"
        assert marks.data_source is not line.data_source


# ===========================================================================
# Stata side, the served copy, the help
# ===========================================================================

def _read(name):
    with open(os.path.join(_REPO, name), encoding="utf-8") as fh:
        return fh.read()


class TestTheServedCopy:

    def test_the_app_defines_the_names(self):
        spec = _moved_spec([_pl("line", connect="stairstep")])
        _, sp, dp = _write(spec, _T)
        ap = sp.replace(".json", "_app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            app = fh.read()
        for name in ("_dash_join_glyph", "_dash_join_vertices",
                     "_dash_join_spec", "_dash_join_hide"):
            assert re.search(r"^def %s\(" % name, app, re.M), name


class TestTheAdoText:

    def test_declared_and_wired(self):
        ado = _read("dash.ado")
        for d in ("CMISSing(string asis)", "Connect(string asis)",
                  "CMISSINGS(string asis)"):
            assert d in ado, d
        seg = ado[ado.index("_dash_opts_repeats _dash_parse_plot_opts "
                            "`ptype'"):]
        assert seg.index("_dash_connect_opt") < seg.index("_dash_fold_bw")
        # Flipped (WP-30 P1.8b): _dash_fold_bw and _dash_validate_opts
        # read _rc_own, _cn_ptype but a recast derived layer's own type;
        # _cn_ptype there was wrong because the recast target would judge
        # the layer's own options (recast_truth.json).
        for call in ("_dash_stylelist_check", "_dash_fold_typed",
                     "_dash_sort_opt"):
            assert '%s "`_cn_ptype\'"' % call in ado, call
        for call in ("_dash_fold_bw", "_dash_validate_opts"):
            assert '%s "`_rc_own\'"' % call in ado, call
        assert 'local _rc_own "`_cn_ptype\'"' in ado
        assert '"type":"`_yt\'"' in ado
        mata = _read("dash_parse.mata")
        keys = mata[mata.index("string scalar _dash_stylelist_keys()"):]
        keys = keys[:keys.index("}")]
        assert "connect cmissing" in keys
        # The Mata function dash.ado needs (_needed).
        assert "_dash_connect_canon ///" in ado


class TestTheAdoTables:

    def test_they_are_the_fixtures(self):
        ado = _read("dash.ado")
        body = ado[ado.index("program define _dash_connect_opt"):]
        body = body[:body.index("\nend\n")]
        refuse = re.search(r'local cm_refuse "([^"]*)"', body).group(1)
        M = _FIX["matrix"]
        want_refuse = {t for t in M if M[t]["cmissing(x)"]["rc"] == 101}
        assert set(refuse.split()) == want_refuse
        # Flipped (WP-31 C6): cm_named -- area, rarea and the fits whose
        # cmissing(n) path differs (P2.42, P2.43), named in the note -- was
        # wrong because dash now draws cmissing(n) on every type and
        # connect() on rarea as twoway does (area_cmissing_truth.json A01,
        # R01, R02, E01-E07): both always leave the pending list.
        assert "cm_named" not in body
        assert 'local _cn_rm "connect cmissing"' in body


class TestTheHelp:

    def test_documented(self):
        h = _read("dash.sthlp")
        assert "{ul:Connecting and missing values.}" in h
        para = h[h.index("{ul:Connecting and missing values.}"):]
        para = para[:para.index("{ul:", 5)]
        for w in ("stairstep", "stepstair", "ascending", "cmissing(n)",
                  "cmissings()", "function"):
            assert w in para, w
        assert "use the {cmd:connected} plot type" not in h
