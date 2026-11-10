"""cmissing(n) on area, rarea and the estimators, and connect() on rarea,
drawn as twoway draws them (WP-31 C6).

The defect, measured at 05736f2 (StataNow 19.5): dash.ado named
``cmissing(n)`` on area, rarea, lowess, lpoly, lpolyci, fpfit, fpfitci,
lfitci and qfitci and ``connect()`` other than direct on rarea in its note
(``_dash_connect_opt``'s ``cm_named``), and the renderer drew the bridged
form: one polygon over a missing row, one unbroken line, a rarea with no
stairs.

twoway's own answers are test/fixtures/area_cmissing_truth.json, written by
scripts/extract_area_cmissing_truth.do on auto with mpg missing in 10/12
(lo = mpg - 2, hi = mpg + 2): each probe's command, the type drawn and the
SVG's subpaths in data units.  Measured there:

* an area or rarea under cmissing(n) is one closed polygon per run of rows
  present in x and the y(s) (A01, R02); cmissing(y) is one (A02, R00);
* area ignores connect() (A03 draws A00's polygon, point for point);
  rarea draws it on both bounds (R01), inserting the stair corner after a
  present row even when the next row is missing, as the line types do not;
* lowess, lpoly, lpolyci, fpfit and fpfitci break where their own result
  is missing (a row in the sample with y missing; an lpoly grid point with
  no neighbours) -- E01, E02, E03, E06, E07; mband and mspline have no
  missing point there (E04, E05) and lfitci/qfitci draw what they draw
  without it (E08 = E12).

dash draws the fill of a split area as ONE VArea whose vertex list holds,
at each gap, two zero-height vertices with no row id (the end of the run
before and the start of the run after, each at its own y), so nothing is
filled between them (section 14 D-14a).  The saved page's re-bridging after
a filter move is done by S52 (batch 17, DECISIONS A23); the served app
redraws through the mapper and is exact (TestAfterAMove).
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
from bokeh.models import Line, VArea

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import render_models  # noqa: E402
# Flipped (WP-47 basic:PT-4): an outline's x and y are the inset
# expression over its source; stroke_field reads the columns it draws.
from conftest import stroke_field  # noqa: E402
from js_runner import fit_helpers_js, requires_node, run_js  # noqa: E402
from test_join_order import (_saved_figs, _saved_move, _served_figs,  # noqa: E402
                             _served_move, _write)

_REPO = os.path.join(_HERE, "..")
with open(os.path.join(_HERE, "fixtures", "area_cmissing_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json"),
          encoding="utf-8") as _fh:
    _AUTO = json.load(_fh)["datasets"]["auto"]

_MODES = ("saved", "served")
_RID = dr._ROW_ID_COLUMN


def _auto(n=None):
    """auto as the extract script reads it: mpg missing in 10/12."""
    df = pd.DataFrame({"mpg": _AUTO["mpg"], "weight": _AUTO["weight"]},
                      dtype=float)
    df.loc[9:11, "mpg"] = np.nan
    df["lo"] = df["mpg"] - 2
    df["hi"] = df["mpg"] + 2
    df["foreign"] = np.arange(len(df)) % 2
    return df.iloc[:n].reset_index(drop=True) if n else df


def _figs(mode, plots, df):
    figs, _ = bg._figs(mode, tempfile.mkdtemp(), bg._spec(plots), df)
    return figs


def _area(**o):
    return {"type": "area", "yvar": "mpg", "xvar": "weight", "options": o}


def _rarea(**o):
    return {"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "weight",
            "options": o}


def _fit(t, **o):
    return {"type": t, "yvar": "mpg", "xvar": "weight", "options": o}


def _vareas(fig):
    return [r for r in fig.renderers if isinstance(r.glyph, VArea)]


def _cols(r):
    d = r.data_source.data
    g = r.glyph
    return (dr._dash_float_values(d[g.x]), dr._dash_float_values(d[g.y1]),
            dr._dash_float_values(d[g.y2]),
            list(d[_RID]) if _RID in d else None)


def _synthetic(rid, y1=None, y2=None):
    """Which vertices no observation owns: a null row id, or -- on a
    source that carries no row id (the served app's) -- a zero-height
    vertex."""
    if rid is None:
        return [bool(a == b) for a, b in zip(y1, y2)]
    return [v is None or (isinstance(v, float) and v != v) for v in rid]


def _fill_runs(r):
    """The filled polygons of one VArea, as twoway writes them: the vertex
    list split at each pair of zero-height vertices no observation owns
    (and at a non-finite vertex), each run's x extent."""
    x, y1, y2, rid = _cols(r)
    syn = _synthetic(rid, y1, y2)
    runs, cur = [], []
    i = 0
    while i < len(x):
        fin = np.isfinite(x[i]) and np.isfinite(y1[i]) and np.isfinite(y2[i])
        if (fin and cur and i + 1 < len(x) and syn[i] and syn[i + 1]
                and y1[i] == y2[i] and y1[i + 1] == y2[i + 1]):
            # A gap's zero-height pair: the run before ends here.
            runs.append(cur)
            cur = []
            i += 2
            continue
        if fin:
            cur.append(x[i])
        elif cur:
            runs.append(cur)
            cur = []
        i += 1
    if cur:
        runs.append(cur)
    return [[min(c), max(c)] for c in runs]


def _same_extents(got, want, tol=2.0):
    return len(got) == len(want) and all(
        abs(a - c) <= tol and abs(b - d) <= tol
        for (a, b), (c, d) in zip(got, want))


def _line_runs(fig, first=True):
    """Each visible Line's vertex runs (split at non-finite), lengths."""
    out = []
    for g in fig.renderers:
        if not isinstance(g.glyph, Line) or g.glyph.line_alpha == 0:
            continue
        d = g.data_source.data
        xs = dr._dash_float_values(d[stroke_field(g, "x")])
        ys = dr._dash_float_values(d[stroke_field(g, "y")])
        runs, n = [], 0
        for a, b in zip(xs, ys):
            if np.isfinite(a) and np.isfinite(b):
                n += 1
            elif n:
                runs.append(n)
                n = 0
        if n:
            runs.append(n)
        out.append(runs)
    return out[0] if (first and out) else out


def _truth_line_runs(pid):
    return [len(p["pts"]) for p in _T[pid]["paths"] if not p["closed"]]


def _outline_runs(fig):
    """rarea's two outline Lines (tag dash_rarea_outline): per Line, its
    runs of finite vertices (split at a non-finite x or y), each run the
    list of its x values (WP-37 DG-5)."""
    out = []
    for g in fig.renderers:
        if "dash_rarea_outline" not in (g.tags or []):
            continue
        d = g.data_source.data
        xs = dr._dash_float_values(d[stroke_field(g, "x")])
        ys = dr._dash_float_values(d[stroke_field(g, "y")])
        runs, cur = [], []
        for a, b in zip(xs, ys):
            if np.isfinite(a) and np.isfinite(b):
                cur.append(float(a))
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        out.append(runs)
    return out


# ===========================================================================
# The fixture
# ===========================================================================

class TestTheFixture:

    def test_it_is_stamped(self):
        m = _T["_meta"]
        assert {"stata_version", "born_date", "dash_commit", "extracted",
                "source"} <= set(m)
        assert str(m["stata_version"]).startswith("19.")
        for k in ("A00", "A01", "A02", "A03", "R00", "R01", "R02", "R03",
                  "E00", "E01", "E02", "E03", "E04", "E05", "E06", "E07"):
            assert _T[k]["rc"] == 0, k
            assert _T[k]["lines"] == [], k


# ===========================================================================
# area
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestAreaSplit:

    def test_fill_collapses_at_the_gap(self, mode):
        """area mpg weight in 1/20, cmissing(n) sort: one VArea whose
        vertex list holds a zero-height pair with no row id at each of the
        two gaps, every vertex finite; the observations keep their ids."""
        fig = _figs(mode, [_area(cmissing="n", sort="sort")], _auto(20))[0]
        [r] = _vareas(fig)
        x, y1, y2, rid = _cols(r)
        assert np.isfinite(x).all() and np.isfinite(y1).all() \
            and np.isfinite(y2).all()
        assert len(_fill_runs(r)) == 3
        if rid is not None:
            syn = np.array(_synthetic(rid))
            assert int(syn.sum()) == 4
            assert np.array_equal(y1[syn], y2[syn])
            # The pairs are adjacent: run end, run start.
            pos = np.flatnonzero(syn)
            assert list(pos[1::2] - pos[0::2]) == [1, 1]

    def test_matches_twoway_extents(self, mode):
        fig = _figs(mode, [_area(cmissing="n", sort="sort")], _auto(20))[0]
        [r] = _vareas(fig)
        assert _same_extents(_fill_runs(r), _T["A01"]["polys"]), (
            _fill_runs(r), _T["A01"]["polys"])

    def test_default_bridges(self, mode):
        for o, pid in (({"sort": "sort"}, "A00"),
                       ({"cmissing": "y", "sort": "sort"}, "A02"),
                       ({"connect": "stairstep", "sort": "sort"}, "A03")):
            fig = _figs(mode, [_area(**o)], _auto(20))[0]
            [r] = _vareas(fig)
            assert _same_extents(_fill_runs(r), _T[pid]["polys"]), (o,)
            if _cols(r)[3] is not None:
                assert not any(_synthetic(_cols(r)[3])), o

    def test_the_outline_breaks(self, mode):
        """An area's outline (drawn when a line option is given) breaks
        where the fill does."""
        fig = _figs(mode, [_area(cmissing="n", sort="sort", lcolor="red")],
                    _auto(20))[0]
        assert len(_line_runs(fig)) == 3


# ===========================================================================
# rarea
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestRareaConnect:

    def test_stairs(self, mode):
        """rarea lo hi weight in 1/20, connect(stairstep) sort: the lower
        bound forward and the upper bound back are twoway's polygon,
        vertex for vertex (R01; the first and last points of the SVG path
        are its move-to and closing repeats)."""
        fig = _figs(mode, [_rarea(connect="stairstep", sort="sort")],
                    _auto(20))[0]
        [r] = _vareas(fig)
        x, y1, y2, _ = _cols(r)
        pts = _T["R01"]["paths"][0]["pts"]
        m = len(x)
        assert len(pts) == 2 * m + 2
        lower = pts[1:1 + m]
        upper = pts[1 + m:1 + 2 * m][::-1]
        for i in range(m):
            assert abs(x[i] - lower[i][0]) < 1.0 and \
                abs(y1[i] - lower[i][1]) < 0.01, (i, x[i], y1[i], lower[i])
            assert abs(x[i] - upper[i][0]) < 1.0 and \
                abs(y2[i] - upper[i][1]) < 0.01, (i, x[i], y2[i], upper[i])

    def test_split(self, mode):
        for o, pid in (({"cmissing": "n", "sort": "sort"}, "R02"),
                       ({"cmissing": "n", "connect": "stepstair",
                         "sort": "sort"}, "R03"),
                       ({"connect": "none", "sort": "sort"}, "R04")):
            fig = _figs(mode, [_rarea(**o)], _auto(20))[0]
            [r] = _vareas(fig)
            assert _same_extents(_fill_runs(r), _T[pid]["polys"]), (
                o, _fill_runs(r), _T[pid]["polys"])

    def test_the_outline_breaks(self, mode):
        """rarea lo hi weight in 1/20, cmissing(n) sort: twoway strokes
        each of its three polygons on its own (R02), so each bound's
        outline is three runs, each over one polygon's x extent; it was
        one run, joined across both gaps (WP-37 DG-5)."""
        fig = _figs(mode, [_rarea(cmissing="n", sort="sort")], _auto(20))[0]
        runs = _outline_runs(fig)
        assert len(runs) == 2
        assert sum(len(r) for r in runs) == 6, runs
        for each in runs:
            ext = [[min(r), max(r)] for r in each]
            assert _same_extents(ext, _T["R02"]["polys"]), (
                ext, _T["R02"]["polys"])

    def test_the_stepstair_outline_breaks(self, mode):
        """connect(stepstair) cmissing(n) (R03): each outline run starts
        where its polygon does -- the second at the missing row's x, 3400,
        where the stair's lead-in corner is (WP-37 DG-5)."""
        fig = _figs(mode, [_rarea(cmissing="n", connect="stepstair",
                                  sort="sort")], _auto(20))[0]
        for each in _outline_runs(fig):
            ext = [[min(r), max(r)] for r in each]
            assert _same_extents(ext, _T["R03"]["polys"]), (
                ext, _T["R03"]["polys"])

    def test_no_outline_spike_at_a_lone_point(self, mode):
        """A present row between two gaps is no polygon in twoway: its
        outline is one vertex (nothing drawn), not a spike from the lower
        bound to the upper one (WP-37 DG-5)."""
        df = pd.DataFrame({"x": np.arange(1.0, 10.0)})
        df["lo"] = df["x"]
        df["hi"] = df["x"] + 2
        df.loc[df["x"].isin([3.0, 5.0]), ["lo", "hi"]] = np.nan
        p = {"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
             "options": {"cmissing": "n"}}
        fig = _figs(mode, [p], df)[0]
        runs = _outline_runs(fig)
        assert len(runs) == 2
        for each in runs:
            assert [r for r in each if 4.0 in r] == [[4.0]], each
            assert [[min(r), max(r)] for r in each] == [
                [1.0, 2.0], [4.0, 4.0], [6.0, 9.0]], each


# ===========================================================================
# The estimators
# ===========================================================================

_EST = [("E01", "lowess"), ("E03", "lpoly"), ("E06", "fpfit")]


@pytest.mark.parametrize("mode", _MODES)
class TestEstimatorsBreak:

    @pytest.mark.parametrize("pid,ptype", _EST)
    def test_each(self, mode, pid, ptype):
        """The line's runs under cmissing(n) are twoway's, run for run."""
        fig = _figs(mode, [_fit(ptype, cmissing="n")], _auto())[0]
        assert _line_runs(fig) == _truth_line_runs(pid), (
            _line_runs(fig), _truth_line_runs(pid))

    @pytest.mark.parametrize("pid,ptype", [("E02", "lpolyci"),
                                           ("E07", "fpfitci")])
    def test_ci(self, mode, pid, ptype):
        """The ci types' line and band both break: as many band polygons
        and line runs as twoway's."""
        fig = _figs(mode, [_fit(ptype, cmissing="n")], _auto())[0]
        assert _line_runs(fig) == _truth_line_runs(pid)
        bands = [r for r in _vareas(fig)]
        polys = [p for p in _T[pid]["paths"] if p["closed"]]
        assert len(_fill_runs(bands[0])) == len(polys)

    @pytest.mark.parametrize("pid,ptype", [("E04", "mband"),
                                           ("E05", "mspline")])
    def test_no_missing_point(self, mode, pid, ptype):
        """mband and mspline have no missing point here: one run."""
        fig = _figs(mode, [_fit(ptype, cmissing="n")], _auto())[0]
        assert len(_line_runs(fig)) == len(_truth_line_runs(pid)) == 1

    def test_default_bridges(self, mode):
        fig = _figs(mode, [_fit("lowess")], _auto())[0]
        assert _line_runs(fig) == _truth_line_runs("E00")


# ===========================================================================
# After a move
# ===========================================================================

class TestAfterAMove:

    def test_served_split(self):
        """The served app redraws a split area through the mapper after a
        filter move: the kept rows' runs, still split (the saved page's
        re-bridging after a move is S52's, DECISIONS A23)."""
        df = _auto(20)
        spec = tp._spec(graphs=[("g1", [_area(cmissing="n", sort="sort")],
                                 {}, {})],
                        build_options={"filter": "foreign, type(dropdown)"})
        doc, _ = _served_move(spec, df, ("Select", "Foreign"))
        fig = _served_figs(doc)[0]
        [r] = _vareas(fig)
        kept = df[df["foreign"] == 1].sort_values("weight", kind="stable")
        ok = kept["mpg"].notna().to_numpy()
        # Runs of present rows in the kept rows' x order.
        want, cur = [], []
        for w, o in zip(kept["weight"], ok):
            if o:
                cur.append(w)
            elif cur:
                want.append([min(cur), max(cur)])
                cur = []
        if cur:
            want.append([min(cur), max(cur)])
        assert _same_extents(_fill_runs(r), want, tol=1e-6), (
            _fill_runs(r), want)


    def test_the_rarea_outline_follows_a_move(self):
        """rarea cmissing(n) after a dropdown move to Foreign: the saved
        page's own filter script (under node) leaves each outline Line
        the runs the served app redraws, one per run of kept present rows
        (WP-37 DG-5)."""
        df = _auto(20)
        spec = tp._spec(graphs=[("g1", [_rarea(cmissing="n", sort="sort")],
                                 {}, {})],
                        build_options={"filter": "foreign, type(dropdown)"})
        saved = _outline_runs(_saved_figs(
            _saved_move(spec, df, ("Select", "Foreign")))[0])
        doc, _ = _served_move(spec, df, ("Select", "Foreign"))
        served = _outline_runs(_served_figs(doc)[0])
        kept = df[df["foreign"] == 1].sort_values("weight", kind="stable")
        want, cur = [], []
        for w, o in zip(kept["weight"], kept["mpg"].notna()):
            if o:
                cur.append(float(w))
            elif cur:
                want.append(cur)
                cur = []
        if cur:
            want.append(cur)
        assert len(want) > 1
        assert served == [want, want], served
        assert saved == served, (saved, served)


# ===========================================================================
# The helpers
# ===========================================================================

class TestTheHelper:

    @requires_node
    @pytest.mark.parametrize("style", ["direct", "stepstair"])
    def test_the_outline_rebuild_twin(self, style):
        """_FILTER_JS's dash_fill_rebuild_kept under an outline's record
        (brk, WP-37 DG-5), every row kept, gives the outline source the
        build wrote: NaN at each gap's pair, so the saved page's rebuild
        breaks where map_rarea does; without brk the pair is pinned."""
        tmp = tempfile.mkdtemp()
        spec = bg._spec([_rarea(cmissing="n", sort="sort", connect=style)])
        r = render_models(dr.DashRenderer(*bg._write(tmp, spec,
                                                     _auto(20))))
        fig = list(r.figures.values())[0]
        outs = [g for g in fig.renderers
                if "dash_rarea_outline" in (g.tags or [])]
        assert len(outs) == 2
        for g in outs:
            d, jn = g.data_source.data, g.data_source._dash_join
            assert jn["brk"] is True and jn["ycols"] == [stroke_field(g, "y")]
            od = {k: [None if (isinstance(v, float) and v != v) else
                      (float(v) if v is not None else None) for v in d[k]]
                  for k in d}
            ids = list(jn["order"])
            js = (fit_helpers_js()
                  + "const OD = " + json.dumps(od) + ";\n"
                  + "const SP = " + json.dumps(jn) + ";\n"
                  + "const K = new Set(" + json.dumps(ids) + ");\n"
                  + "const a = dash_fill_rebuild_kept(OD, SP, "
                  + json.dumps(_RID) + ", K);\n"
                  + "const b = dash_fill_rebuild_kept(OD, Object.assign("
                  "{}, SP, {brk: false}), " + json.dumps(_RID) + ", K);\n"
                  + "const f = (c) => c.map(v => (typeof v === 'number' "
                  "&& isNaN(v)) ? 'nan' : v);\n"
                  + "process.stdout.write(JSON.stringify([f(a[SP.ycols[0]]),"
                  " f(b[SP.ycols[0]]), f(a[SP.x])]));\n")
            got, pinned, gx = run_js(js)
            want = ["nan" if not np.isfinite(v) else float(v)
                    for v in dr._dash_float_values(d[stroke_field(g, "y")])]
            assert got == want, (got, want)
            assert gx == [float(v) for v in d[stroke_field(g, "x")]]
            assert "nan" not in pinned and got.count("nan") == 4

    def test_rows(self):
        """_dash_fill_vertices: the present rows in order, a zero-height
        pair at each gap, leading and trailing missing rows dropped."""
        xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ok = [False, True, False, True, True, False]
        xi, yi, col = dr._dash_fill_vertices(xs, ok, "direct", "n")
        assert list(xi) == [1, 1, 3, 3, 4]
        assert list(yi) == [1, 1, 3, 3, 4]
        assert list(col) == [False, True, True, False, False]
        xi, yi, col = dr._dash_fill_vertices(xs, ok, "direct", "y")
        assert list(xi) == [1, 3, 4] and not col.any()
        # stairstep: the corner after a present row, even when the next
        # row is missing (twoway's rarea, R01).
        xi, yi, col = dr._dash_fill_vertices(xs, ok, "stairstep", "y")
        assert list(zip(xi, yi)) == [(1, 1), (2, 1), (3, 3), (4, 3), (4, 4)]
        xi, yi, col = dr._dash_fill_vertices(xs, ok, "stepstair", "y")
        assert list(zip(xi, yi)) == [(0, 1), (1, 1), (2, 3), (3, 3), (3, 4),
                                     (4, 4)]

    def test_rebuild(self):
        """_dash_fill_rebuild: x from each vertex's x row, the y columns
        from its y row or, at a zero-height vertex, the pin column; the row
        id and every carried column null where no observation owns the
        vertex."""
        data = {"x": [1.0, 2.0, 3.0], "lo": [10.0, np.nan, 30.0],
                "hi": [11.0, np.nan, 31.0], _RID: [7, 8, 9],
                "name": ["a", "b", "c"]}
        xi = np.array([0, 0, 2, 2])
        yi = np.array([0, 0, 2, 2])
        col = np.array([False, True, True, False])
        new = dr._dash_fill_rebuild(data, "x", ("lo", "hi"), "lo", xi, yi,
                                    col)
        assert list(new["x"]) == [1.0, 1.0, 3.0, 3.0]
        assert list(new["lo"]) == [10.0, 10.0, 30.0, 30.0]
        assert list(new["hi"]) == [11.0, 10.0, 30.0, 31.0]
        assert list(new[_RID]) == [7, None, None, 9]
        assert list(new["name"]) == ["a", None, None, "c"]


    def test_insert_breaks(self):
        """_dash_insert_breaks: a NaN point after the points at or below
        each gap's x; nothing when there is no gap."""
        xs, (ys,) = dr._dash_insert_breaks([1.0, 2.0, 3.0], [[5, 6, 7]],
                                           [2.0, 3.5])
        assert list(xs) == [1.0, 2.0, 2.0, 3.0, 3.5]
        assert np.isnan(ys[2]) and np.isnan(ys[4])
        assert list(ys[[0, 1, 3]]) == [5.0, 6.0, 7.0]
        xs, (ys,) = dr._dash_insert_breaks([1.0], [[5]], [])
        assert list(xs) == [1.0] and list(ys) == [5.0]

    def test_fill_split(self):
        """_dash_fill_split rebuilds a band only under cmissing(n) with a
        missing point."""
        from bokeh.models import ColumnDataSource
        data = {"x": [1.0, 2.0, 3.0], "lo": [1.0, np.nan, 3.0],
                "hi": [2.0, np.nan, 4.0]}
        src = ColumnDataSource(dict(data))
        assert not dr._dash_fill_split(src, "x", ("lo", "hi"), "lo", {})
        assert dr._dash_fill_split(src, "x", ("lo", "hi"), "lo",
                                   {"cmissing": "n"})
        assert list(src.data["x"]) == [1.0, 1.0, 3.0, 3.0]
        assert list(src.data["hi"]) == [2.0, 1.0, 3.0, 4.0]
        full = ColumnDataSource({"x": [1.0, 2.0], "lo": [1.0, 2.0],
                                 "hi": [2.0, 3.0]})
        assert not dr._dash_fill_split(full, "x", ("lo", "hi"), "lo",
                                       {"cmissing": "n"})

    def test_gap_x(self):
        """GlyphMapper._cmiss_gap_x: the rows with an x and no y under
        cmissing(n) (fpfit's distinct rule drops an x some row has a y
        at); empty under cmissing(y)."""
        from bokeh.models import ColumnDataSource
        src = ColumnDataSource({"x": [1.0, 2.0, 2.0, 3.0, np.nan],
                                "y": [1.0, np.nan, 5.0, np.nan, np.nan]})
        gm = bg._gm()
        assert list(gm._cmiss_gap_x(src, None, "x", "y",
                                    {"cmissing": "n"})) == [2.0, 3.0]
        assert list(gm._cmiss_gap_x(src, None, "x", "y", {"cmissing": "n"},
                                    distinct=True)) == [3.0]
        assert len(gm._cmiss_gap_x(src, None, "x", "y", {})) == 0
        xs, ys = gm._masked_rows(src, None, "x", "y")
        assert len(xs) == 5 and np.isnan(ys[1])


class TestTheServedCopy:

    def test_name(self):
        """The served app carries both helpers (R2's functions tuple)."""
        spec = tp._spec(graphs=[("g1", [_area(cmissing="n")], {}, {})])
        _, sp, dp = _write(spec, _auto(20))
        ap = sp.replace(".json", "_app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            app = fh.read()
        for n in ("_dash_fill_vertices", "_dash_fill_rebuild"):
            assert re.search(r"^def %s\(" % n, app, re.M), n


# ===========================================================================
# dash.ado
# ===========================================================================

def _read(name):
    with open(os.path.join(_REPO, name), encoding="utf-8") as fh:
        return fh.read()


class TestTheAdoText:

    def test_lists(self):
        """_dash_connect_opt names neither option on any type."""
        ado = _read("dash.ado")
        body = ado[ado.index("program define _dash_connect_opt"):]
        body = body[:body.index("\nend\n")]
        assert "cm_named" not in body
        assert 'local _cn_rm "connect cmissing"' in body

    def test_not_pending(self):
        """The plot parser's pending block lists neither."""
        ado = _read("dash.ado")
        for o in ("cmissing", "connect"):
            assert ("if `: length local %s' local _dash_pending" % o) \
                not in ado, o
