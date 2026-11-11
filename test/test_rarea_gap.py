"""rarea where a row misses one bound, drawn as twoway draws it (WP-47
PIC-17).

twoway's answers are test/fixtures/rarea_gap_truth.json, written by
scripts/extract_rarea_gap_truth.do on eight rows (x = 1..8, lo = x,
hi = 20 + 4*mod(x,2)), each probe with the rows it names missing.  Measured
there (StataNow 19.5, 11nov2026):

* under the default cmissing(y) twoway does NOT break the area at a row
  missing one bound: its one polygon runs forward along the first bound
  (y1) through every row that has it and back along the second (y2)
  through every row that has it (G01, G02, G05, G06; unsorted G08), the
  register's "twoway breaks the area there" was wrong for this case;
* the polygon spans the rows from the first to the last that has y1
  (G04, G13-G18, G20, G21): a y2 point outside them is left out (G04's
  hi1), and where y2 is missing at either end of them the polygon's
  closing edge runs from y1's end point to the nearest y2 point (G15:
  lo8 to hi6) -- dash left those end rows out, so it filled less;
* under cmissing(n) twoway breaks the area at every row missing either
  bound (N01-N05), as dash already did;
* connect(stairstep) with one bound missing (G12, G19) steps each bound
  through its own rows: a residual, filed in BUGS.md, not drawn here.

dash draws the fill as one VArea, whose vertex at each row needs both
bounds: a row missing one takes the point twoway's edge passes at its x,
the straight line between that bound's neighbours, with y1's end points
standing in for a y2 missing at the span's ends (_dash_rarea_one_bound).
The outline Lines are drawn over the same rows, so they follow the
polygon's edges, the closing edge at such an end included.  After a
filter move the saved page recomputes the filled bounds from the kept
rows (_FILTER_JS's dash_rarea_bound_kept over the copy's ``rarea``
record); the served app redraws through map_rarea.
"""
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import stroke_field  # noqa: E402
from js_runner import fit_helpers_js, requires_node, run_js  # noqa: E402
from test_join_order import (_saved_figs, _saved_move, _served_figs,  # noqa: E402
                             _served_move)

with open(os.path.join(_HERE, "fixtures", "rarea_gap_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
#: The stairs residual (BUGS.md "rarea under connect(stairstep) ...").
_STAIRS = ("G12", "G19")
#: The probes drawn on a subset of the rows (twoway's if, dash's move).
_SUBSET = {"G11": 2.0, "G22": 5.0, "G23": 1.0}
#: Grid points within rounding of an edge may fall either side: twoway's
#: SVG coordinates are read back to data units by a fitted axis (1e-6).
_TOL = 12


# ===========================================================================
# Helpers
# ===========================================================================

def _frame(rec, drop=None):
    """The probe's eight rows as the extract script builds them."""
    x = np.arange(1, 9, dtype=float)
    if rec["shuffle"]:
        x = np.array([1, 3, 2, 5, 4, 7, 6, 8], dtype=float)
    df = pd.DataFrame({"x": x, "lo": x.copy(),
                       "hi": 20 + 4 * np.mod(x, 2)})
    for r in rec["lo_missing"]:
        df.loc[int(r) - 1, "lo"] = np.nan
    for r in rec["hi_missing"]:
        df.loc[int(r) - 1, "hi"] = np.nan
    # A filter move to Foreign keeps every row but *drop*'s x.
    df["foreign"] = (df["x"] != (drop if drop is not None else -1)) \
        .astype(float)
    return df


def _options(cmd):
    o = {}
    tail = cmd.split(",", 1)[1] if "," in cmd else ""
    if re.search(r"\bsort\b", tail):
        o["sort"] = "sort"
    if "horizontal" in tail:
        o["horizontal"] = "horizontal"
    m = re.search(r"connect\((\w+)\)", tail)
    if m:
        o["connect"] = m.group(1)
    m = re.search(r"cmissing\((\w+)\)", tail)
    if m:
        o["cmissing"] = m.group(1)
    return o


def _plot(cmd):
    words = cmd.split(",")[0].split()
    return {"type": "rarea", "yvar1": words[2], "yvar2": words[3],
            "xvar": "x", "options": _options(cmd)}


def _inside(poly, pts):
    """Even-odd membership of *pts* (n x 2) in the polygon *poly*."""
    poly = np.asarray(poly, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    res = np.zeros(len(pts), dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if y1 == y2:
            continue
        res ^= (((y1 > y) != (y2 > y))
                & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1))
    return res


_GX, _GY = np.meshgrid(np.arange(0.513, 8.6, 0.0571),
                       np.arange(0.317, 25.6, 0.0913))
_GRID = np.column_stack([_GX.ravel(), _GY.ravel()])


def _rings(rec):
    """twoway's closed subpaths, upright (x, y): the polygons it fills."""
    out = []
    for p in rec["paths"]:
        if p["closed"]:
            pts = [(a, b) for a, b in p["pts"]]
            if "horizontal" in rec["cmd"]:
                pts = [(b, a) for a, b in pts]
            out.append(pts)
    return out


def _twoway_cover(rec):
    cov = np.zeros(len(_GRID), dtype=bool)
    for ring in _rings(rec):
        cov ^= _inside(ring, _GRID)
    return cov


def _area_rows(r):
    """A VArea's (or a turned HArea's) x, y1, y2, upright."""
    d = r.data_source.data
    g = r.glyph
    f = dr._dash_float_values
    if type(g).__name__ == "VArea":
        return f(d[g.x]), f(d[g.y1]), f(d[g.y2])
    return f(d[g.y]), f(d[g.x1]), f(d[g.x2])


def _dash_cover(fig):
    """The grid points dash fills: each VArea's runs of finite rows, as
    Bokeh draws them (forward along y1, back along y2)."""
    cov = np.zeros(len(_GRID), dtype=bool)
    for r in fig.renderers:
        if type(r.glyph).__name__ not in ("VArea", "HArea"):
            continue
        x, a, b = _area_rows(r)
        ok = np.isfinite(x) & np.isfinite(a) & np.isfinite(b)
        run = []
        for i in list(range(len(x))) + [None]:
            if i is not None and ok[i]:
                run.append(i)
                continue
            if run:
                ring = ([(x[j], a[j]) for j in run]
                        + [(x[j], b[j]) for j in run[::-1]])
                cov ^= _inside(ring, _GRID)
            run = []
    return cov


def _norm(pts):
    """A polyline without repeated vertices or vertices on the straight
    segment between their neighbours (they draw nothing of their own),
    to two decimals: twoway's SVG reads back within 1e-3 of the data."""
    out = []
    for p in pts:
        p = (round(float(p[0]), 2) + 0.0, round(float(p[1]), 2) + 0.0)
        if out and out[-1] == p:
            continue
        out.append(p)
    changed = True
    while changed and len(out) > 2:
        changed = False
        for i in range(1, len(out) - 1):
            (x0, y0), (x1, y1), (x2, y2) = out[i - 1], out[i], out[i + 1]
            # On the line and between its neighbours: a vertex past one
            # (a spike) draws a stroke of its own and stays.
            if (abs((x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)) < 0.05
                    and (x1 - x0) * (x2 - x1) + (y1 - y0) * (y2 - y1)
                    >= 0):
                del out[i]
                changed = True
                break
    return out


def _twoway_edges(rec):
    """Per twoway polygon (in x order): its first bound's chain and its
    second bound's chain read forward, the closing edge to y1's end point
    included where y2 has no point at that end -- what dash's two outline
    Lines draw.  lo < 15 < hi in every probe, so a vertex's bound is its
    y's side of 15."""
    lo_first = _plot(rec["cmd"])["yvar1"] == "lo"
    out = []
    for ring in sorted(_rings(rec), key=lambda q: min(p[0] for p in q)):
        body = ring[1:-1] if ring[0] == ring[1] else ring[:-1]
        one = [p for p in body if (p[1] < 15) == lo_first]
        two = [p for p in body if (p[1] < 15) != lo_first][::-1]
        if two and two[0][0] != one[0][0]:
            two = [one[0]] + two
        if two and two[-1][0] != one[-1][0]:
            two = two + [one[-1]]
        out.append((_norm(one), _norm(two)))
    return out


def _dash_edges(fig):
    """dash's two outline Lines (tag dash_rarea_outline), per run of
    finite vertices, normalised."""
    lines = [g for g in fig.renderers
             if "dash_rarea_outline" in (g.tags or [])]
    per = []
    for g in lines:
        d = g.data_source.data
        xs = dr._dash_float_values(d[stroke_field(g, "x")])
        ys = dr._dash_float_values(d[stroke_field(g, "y")])
        runs, cur = [], []
        for a, b in zip(list(xs) + [np.nan], list(ys) + [np.nan]):
            if np.isfinite(a) and np.isfinite(b):
                cur.append((a, b))
            elif cur:
                runs.append(_norm(cur))
                cur = []
        per.append(runs)
    return list(zip(*per)) if len(per) == 2 else per


def _figs(mode, rec, df):
    figs, _ = bg._figs(mode, tempfile.mkdtemp(),
                       bg._spec([_plot(rec["cmd"])]), df)
    return figs


def _probe_frame(pid):
    rec = _T[pid]
    df = _frame(rec)
    if pid in _SUBSET:
        df = df[df["x"] != _SUBSET[pid]].reset_index(drop=True)
    return rec, df


_FILL_IDS = sorted(k for k in _T if k != "_meta" and k not in _STAIRS)
_EDGE_IDS = [k for k in _FILL_IDS
             if not _T[k]["shuffle"] and "horizontal" not in _T[k]["cmd"]]


# ===========================================================================
# The fixture
# ===========================================================================

class TestTheFixture:

    def test_meta(self):
        m = _T["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_rarea_gap_truth.do"

    def test_every_probe_ran(self):
        assert all(r["rc"] == 0 for k, r in _T.items() if k != "_meta")

    def test_the_default_passes_over_a_missing_bound(self):
        """G01: one polygon, its upper edge straight from hi5 to hi3."""
        [ring] = _rings(_T["G01"])
        ring = [(round(a, 2), round(b, 2)) for a, b in ring]
        i = ring.index((5.0, 24.0))
        assert ring[i + 1] == (3.0, 24.0)

    def test_cmissing_n_breaks_there(self):
        spans = [[round(a, 2), round(b, 2)] for a, b in _T["N01"]["polys"]]
        assert spans == [[1.0, 3.0], [5.0, 8.0]]

    def test_the_span_is_the_first_bound_s(self):
        """G04: lo1 and hi8 missing; the polygon runs lo2..lo8 and back
        hi7..hi2 -- hi1 is left out, lo8 kept; G18 (the bounds swapped)
        keeps hi1 and leaves lo8 out."""
        def pts(pid):
            [ring] = _rings(_T[pid])
            return {(round(a, 2), round(b, 2)) for a, b in ring}
        assert (8.0, 8.0) in pts("G04") and (1.0, 24.0) not in pts("G04")
        assert (1.0, 24.0) in pts("G18") and (8.0, 8.0) not in pts("G18")


# ===========================================================================
# The fill and the outline, in both modes
# ===========================================================================

class TestTheFill:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", _FILL_IDS)
    def test_the_fill_is_twoway_s(self, pid, mode):
        rec, df = _probe_frame(pid)
        [fig] = _figs(mode, rec, df)[:1]
        off = int((_dash_cover(fig) != _twoway_cover(rec)).sum())
        assert off <= _TOL, (pid, rec["cmd"], off)


class TestTheOutline:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", _EDGE_IDS)
    def test_the_outline_follows_the_polygon(self, pid, mode):
        rec, df = _probe_frame(pid)
        [fig] = _figs(mode, rec, df)[:1]
        assert _dash_edges(fig) == _twoway_edges(rec), (pid, rec["cmd"])


# ===========================================================================
# After a filter move
# ===========================================================================

def _move_spec(pid):
    rec = _T[pid]
    drop = _SUBSET[pid]
    df = _frame(rec, drop)
    spec = tp._spec(graphs=[("g1", [_plot(rec["cmd"].replace(
        " if x != %g" % drop, ""))], {}, {})],
        build_options={"filter": "foreign, type(dropdown)"})
    return rec, spec, df


class TestAfterAMove:
    """A dropdown move to Foreign leaves the rows of twoway's ``if``: the
    filled bounds are those of the kept rows' polygon (G22: hi4 between
    hi3 and hi6 once x 5 goes; G23: hi2 missing at the kept span's start
    once x 1 goes)."""

    @requires_node
    @pytest.mark.parametrize("pid", sorted(_SUBSET))
    def test_saved_page_under_node(self, pid):
        rec, spec, df = _move_spec(pid)
        [fig] = _saved_figs(_saved_move(spec, df, ("Select", "Foreign")))[:1]
        off = int((_dash_cover(fig) != _twoway_cover(rec)).sum())
        assert off <= _TOL, (pid, off)
        assert _dash_edges(fig) == _twoway_edges(rec), pid

    @pytest.mark.parametrize("pid", sorted(_SUBSET))
    def test_served_app(self, pid):
        rec, spec, df = _move_spec(pid)
        doc, _ = _served_move(spec, df, ("Select", "Foreign"))
        [fig] = _served_figs(doc)[:1]
        off = int((_dash_cover(fig) != _twoway_cover(rec)).sum())
        assert off <= _TOL, (pid, off)
        assert _dash_edges(fig) == _twoway_edges(rec), pid


# ===========================================================================
# The helpers and their JavaScript twin
# ===========================================================================

_NAN = float("nan")


class TestTheHelper:

    def test_the_span_is_the_first_bound_s(self):
        cols = {"x": np.array([1.0, 2, 3, 4]),
                "a": np.array([_NAN, 2, 3, 4]),
                "b": np.array([9.0, 8, 7, _NAN])}
        out, order = dr._dash_rarea_one_bound(cols, np.array([5, 6, 7, 8]),
                                              "x", "a", "b")
        # x 1 has no first bound: left out; b at x 4 is a's end point.
        assert list(order) == [6, 7, 8]
        assert list(out["b"]) == [8, 7, 4]

    def test_a_missing_second_bound_at_the_start(self):
        cols = {"x": np.array([1.0, 2, 3]), "a": np.array([1.0, 2, 3]),
                "b": np.array([_NAN, _NAN, 9])}
        out, _ = dr._dash_rarea_one_bound(cols, np.arange(3), "x", "a", "b")
        # the closing edge from a's first point (1, 1) to (3, 9)
        assert list(out["b"]) == [1, 5, 9]

    def test_no_second_bound(self):
        cols = {"x": np.array([1.0, 2, 3]), "a": np.array([1.0, 5, 3]),
                "b": np.array([_NAN, _NAN, _NAN])}
        out, _ = dr._dash_rarea_one_bound(cols, np.arange(3), "x", "a", "b")
        # twoway closes the first bound's chain on its chord
        assert list(out["b"]) == [1, 2, 3]

    @requires_node
    def test_the_javascript_twin(self):
        """_FILTER_JS's dash_rarea_bound_kept over every row equals
        _dash_rarea_one_bound, on rows with gaps inside and at both
        ends, sorted and not."""
        x = [1.0, 3, 2, 5, 4, 7, 6, 8]
        a = [_NAN, 3, 2, 5, _NAN, 7, 6, 8]
        b = [24.0, _NAN, 20, 24, 20, _NAN, 20, _NAN]
        ids = list(range(8))
        cols = {"x": np.array(x), "a": np.array(a), "b": np.array(b)}
        out, order = dr._dash_rarea_one_bound(cols, np.array(ids), "x",
                                              "a", "b")
        keep = [i for i in ids if np.isfinite(a[i]) or np.isfinite(b[i])]
        rec = {"kind": "rarea", "x": "x", "y1": "a", "y2": "b",
               "raw": [[i, None if not np.isfinite(a[i]) else a[i],
                        None if not np.isfinite(b[i]) else b[i]]
                       for i in ids]}
        rid = dr._ROW_ID_COLUMN
        data = {"x": [x[i] for i in keep], "a": [0.0] * len(keep),
                "b": [0.0] * len(keep), rid: keep}
        got = run_js(fit_helpers_js() + """
const f = (c) => c.map(v => (typeof v === 'number' && isNaN(v)) ? null : v);
const out = dash_rarea_bound_kept(%s, %s, %s);
process.stdout.write(JSON.stringify([out[%s], f(out.x), f(out.a), f(out.b)]));
""" % (json.dumps(data), json.dumps(rec), json.dumps(rid), json.dumps(rid)))
        assert got[0] == [int(i) for i in order]
        assert got[1] == pytest.approx(list(out["x"]))
        assert got[2] == pytest.approx(list(out["a"]))
        assert got[3] == pytest.approx(list(out["b"]))
