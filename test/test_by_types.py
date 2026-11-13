"""
test_by_types.py -- every plot type's by() panels against twoway's
per-panel data (WP-33 section 33-12, BY-23).

The gap: per-type by() drawing was pinned against twoway only for
function (default range) and lpoly; U60-5 checked histogram, kdensity,
scatter, line and bar only for their panel count and saved/served
agreement, and no fixture held twoway's per-panel data for the fits, ci
bands, smooths, bins, range, pc or immediate types, so a regression would
pass.

The truth is ``test/fixtures/by_types_truth.json``, written by
``scripts/extract_by_types_truth.do``: for each of the 44 plot types under
``by(foreign)`` and ``by(foreign, total)`` (probe ids ``bt_<type>_by`` and
``bt_<type>_total``), every serset twoway builds and, per panel, the one
its plot draws (``.plotregion1.plot1.serset``; mspline frees a serset id
while it builds, so position alone does not say which).  Each probe is
compared in both modes (D-33-12.c):

  panels  the panel count;
  rows    the plot's drawn rows (its data source's length after its
          CDSView filter, halved where both ends share one source) equal the
          serset's rows with no missing value -- every type but the
          computed curves;
  x, y    the extents of the drawn coordinates (each glyph's x-like and
          y-like fields, finite values) equal the serset's minimum and
          maximum of its x and y columns over its drawn rows (first two
          columns not missing: lpoly's grid runs past the points it can
          fit), rtol 1e-9 (1e-6 for computed columns);
  values  the computed curves (fits, smooths, kdensity, function, the ci
          bands): each sampled serset row's y (and ci bounds) equals
          dash's curve at the same x, within rtol 1e-6 -- matched by x
          (lpoly's serset holds rows with a missing value that dash does
          not draw, and lfit's holds 3 points where dash draws 100), the
          curve read between its points where none falls on that x, and
          any of dash's points at a tied x accepted (lowess);
  levels  contour and contourline: the number of fill levels per panel
          (twoway's cuts, read after a draw, plus one).

A difference is listed in ``BY_TYPES_KNOWN`` under the GAPS4 item that
owns it (test/known_differences.py, D-33-10.a).
"""
import itertools
import json
import os
import sys
import tempfile
import types
import warnings

import numpy as np
import pytest

# WP-50 50-03: the batch tier, run at batch ends (make test-all), ruled 13nov2026 at 50-01-04.
pytestmark = pytest.mark.batch

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from by_panel_probe import by_grid  # noqa: E402
from conftest import load_app, render_models  # noqa: E402
from known_differences import dead_rows, known_problems  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_types_truth.json")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_types_")
_TRUTH = None

#: The 44 plot types the probes draw (D-33-12.a), written out so that
#: collection never depends on the fixture.
_TYPES = (
    "area", "bar", "connected", "contour", "contourline", "dot",
    "dropline", "fpfit", "fpfitci", "function", "histogram", "kdensity",
    "lfit", "lfitci", "line", "lowess", "lpoly", "lpolyci", "mband",
    "mspline", "pcarrow", "pcarrowi", "pcbarrow", "pccapsym", "pci",
    "pcscatter", "pcspike", "qfit", "qfitci", "rarea", "rbar", "rcap",
    "rcapsym", "rconnected", "rline", "rpcap", "rpspike", "rscatter",
    "rspike", "scatter", "scatteri", "spike", "tsline", "tsrline")
_PROBE_IDS = tuple("bt_%s_%s" % (t, form) for t in _TYPES
                   for form in ("by", "total"))
_CHECKS = ("panels", "rows", "x", "y", "values", "levels")

#: {"<probe id>:<check>": "<GAPS4 id>"} (D-33-12.d, D-33-10.a).  Empty
#: since WP-41 BY-28 (41-01) cut every contour panel at the first panel's
#: cuts, as twoway does.
BY_TYPES_KNOWN = {}
#: Differences a ruling keeps (D-33-10.a's companion dict; empty).
BY_TYPES_DELIBERATE = {}

_CI = {"lfitci", "qfitci", "fpfitci", "lpolyci"}
_CURVES = {"lfit", "qfit", "fpfit", "lowess", "lpoly", "mband", "mspline",
           "kdensity", "function"} | _CI
_CONTOURS = {"contour", "contourline"}
_SORTED = {"line", "connected", "area", "rline", "rconnected"}
#: Points drawn per observation where one source holds both ends.
_STACKED = {"rscatter": 2, "pcscatter": 2}

#: The role of each serset column, in serset order (measured,
#: by_types_truth.json): y and x; lo and hi a ci band's bounds (y-like);
#: "-" a column not drawn (histogram's base, kdensity's raw variable).
_ROLES = dict(
    {t: ("y", "y", "x") for t in ("rarea", "rbar", "rspike", "rcap",
                                  "rline", "rconnected", "rcapsym",
                                  "rscatter", "tsrline")},
    **{t: ("y", "y", "y", "x") for t in ("rpcap", "rpspike")},
    **{t: ("y", "x", "y", "x") for t in ("pcspike", "pcarrow", "pcbarrow",
                                         "pcscatter", "pccapsym", "pci",
                                         "pcarrowi")},
    **{t: ("y", "lo", "hi", "x") for t in ("lfitci", "qfitci", "fpfitci")},
    lpolyci=("y", "x", "lo", "hi"), histogram=("y", "-", "x"),
    kdensity=("y", "x", "-"), contour=("-", "y", "x"),
    contourline=("-", "y", "x"))

_X_FIELDS = ("x", "x0", "x1", "left", "right", "xs")
_Y_FIELDS = ("y", "y0", "y1", "y2", "top", "bottom", "ys")
#: Glyph fields that hold a type's base, which twoway's serset does not
#: carry (map_bar's __dash_base, map_area's <y>_base, the spike and
#: dropline y0): not part of the drawn data's extent.
_BASE_FIELDS = {"bar": {"bottom"}, "area": {"y1"}, "spike": {"y0"},
                "dropline": {"y0"}}


def _truth():
    global _TRUTH
    if _TRUTH is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _TRUTH = json.load(fh)
    return _TRUTH


def _ptype(pid):
    return pid[3:].rsplit("_", 1)[0]


def _by_spec(pid):
    """The dash spec of probe *pid*: plot_for's dict for its type (sorted
    where the probe sorts; tsline and tsrline over t) under by(foreign)
    or by(foreign, total)."""
    ptype = _ptype(pid)
    plot = plot_for(ptype, {"sort": "sort"} if ptype in _SORTED else {})
    if ptype in ("tsline", "tsrline"):
        plot["xvar"] = "t"
    by = "foreign, total" if pid.endswith("_total") else "foreign"
    go = {"name": "g1", "by": by}
    g = {"name": "g1", "graph_options": go, "options": dict(go),
         "plots": [plot], "if_expr": "", "in_expr": ""}
    return {"graphs": [g], "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "", "theme": "",
                "scheme": "", "session_scheme": "", "title": "",
                "subtitle": "", "registry": "g1", "tabs": "",
                "filter_position": "top", "level": "95", "formats": {}}}


def _draw(mode, spec):
    """The by() panels (figures, in grid order) *mode* draws for *spec*
    (test_by_text.py's _draw, on this fixture's data)."""
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_truth()["data"], fh)
    dr._dash_reset_notes()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            roots = [r._last_layout_root]
        else:
            from bokeh.document import Document
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_bty_app_%d" % tag, draw=False)
            doc = Document()
            mod.make_document(doc)
            roots = list(doc.roots)
    from bokeh.models import GridPlot
    for root in roots:
        if any(isinstance(m, GridPlot)
               and any(type(c[0]).__name__ == "figure" for c in m.children)
               for m in root.references()):
            panels, _head, _foot = by_grid(root)
            return [f for _, _, f in panels]
    return []


# ---------------------------------------------------------------------------
# Reading dash's panels
# ---------------------------------------------------------------------------
def _glyphs(fig):
    """The panel's data renderers: every GlyphRenderer but dot's guide
    dots (tag dash_dots).  Flipped (WP-34 PIC-1): nor an area's outline
    ring (tag dash_area_outline), whose base vertices are no data, nor its
    key swatch -- the outline is the area's whole polygon, one ring
    rebuilt from the fill's source (A-6)."""
    return [r for r in fig.renderers
            if type(r).__name__ == "GlyphRenderer"
            and "dash_dots" not in (r.tags or [])
            and "dash_area_outline" not in (r.tags or [])
            and not getattr(r, "_dash_key_glyph", False)]


def _kept(r):
    """The row indices *r*'s CDSView keeps."""
    data = r.data_source.data
    n = len(next(iter(data.values()))) if data else 0
    f = r.view.filter if r.view is not None else None
    name = type(f).__name__ if f is not None else "AllIndices"
    if name == "AllIndices":
        return np.arange(n)
    if name == "IndexFilter":
        return np.asarray(f.indices, dtype=int)
    if name == "BooleanFilter":
        return np.flatnonzero(np.asarray(f.booleans, dtype=bool))
    raise AssertionError("unhandled view filter %s" % name)


def _field(r, attr):
    """The kept values of glyph field *attr* of *r*, or None when the
    field is a constant or absent."""
    spec = getattr(r.glyph, attr, None)
    if isinstance(spec, dict):
        spec = spec.get("field")
    # Flipped (WP-47 PIC-9): a histogram's count edge is a Field with the
    # empty-bin transform (_DASH_EMPTY_BIN_JS), no longer a bare name; its
    # column is read as before.
    if not isinstance(spec, str) and isinstance(
            getattr(spec, "field", None), str):
        spec = spec.field
    if not isinstance(spec, str) or spec not in r.data_source.data:
        return None
    col = list(r.data_source.data[spec])
    out = []
    for i in _kept(r):
        v = col[i]
        out.extend(np.ravel(np.asarray(v, dtype=float)).tolist()
                   if isinstance(v, (list, tuple, np.ndarray)) else [v])
    return np.asarray(out, dtype=float)


def _extent(ptype, fig, axis):
    """(min, max) of the finite drawn coordinates on *axis* ("x"/"y")."""
    vals = []
    base = _BASE_FIELDS.get(ptype, set())
    for r in _glyphs(fig):
        if ptype == "histogram" and axis == "x":
            left, right = _field(r, "left"), _field(r, "right")
            if left is not None and right is not None:
                vals.append((left + right) / 2.0)
            continue
        for attr in (_X_FIELDS if axis == "x" else _Y_FIELDS):
            if attr in base:
                continue
            v = _field(r, attr)
            if v is not None:
                vals.append(v)
    v = np.concatenate(vals) if vals else np.array([])
    v = v[np.isfinite(v)]
    return (float(v.min()), float(v.max())) if v.size else None


def _rows(ptype, fig):
    """The plot's drawn rows: its first data renderer's kept length, over
    the points it draws per observation (rscatter and pcscatter stack
    both ends in one source, in both modes)."""
    rs = _glyphs(fig)
    return len(_kept(rs[0])) // _STACKED.get(ptype, 1) if rs else 0


def _curves(fig):
    """{"y": (x, y), "lo": (x, lo), "hi": (x, hi)} of a curve panel: the
    fit is the last Line, the band the VArea."""
    out = {}
    for r in _glyphs(fig):
        g = type(r.glyph).__name__
        if g == "Line":
            out["y"] = (_field(r, "x"), _field(r, "y"))
        elif g == "VArea":
            out["lo"] = (_field(r, "x"), _field(r, "y1"))
            out["hi"] = (_field(r, "x"), _field(r, "y2"))
    return out


def _at(xs, ys, x, rtol=1e-6):
    """dash's curve (xs, ys) at *x*: the y of every point whose x is *x*
    (within rtol), else the curve read linearly between its points; []
    when *x* is outside it."""
    ok = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[ok], ys[ok]
    if not xs.size:
        return []
    tol = rtol * max(1.0, float(np.max(np.abs(xs))))
    hit = np.abs(xs - x) <= tol
    if hit.any():
        return ys[hit].tolist()
    order = np.argsort(xs, kind="stable")
    xs, ys = xs[order], ys[order]
    if x < xs[0] or x > xs[-1]:
        return []
    return [float(np.interp(x, xs, ys))]


# ---------------------------------------------------------------------------
# Reading twoway's panels
# ---------------------------------------------------------------------------
def _serset(probe, k):
    return probe["sersets"][probe["panels"][k]["serset"]]


def _cols(ptype, s, role):
    roles = _ROLES.get(ptype, ("y", "x"))
    if role == "y":
        return [j for j, r in enumerate(roles) if r in ("y", "lo", "hi")]
    return [j for j, r in enumerate(roles) if r == role]


def _serset_extent(ptype, s, axis):
    js = _cols(ptype, s, axis)
    lo = [s["drawn_min"][j] for j in js if s["drawn_min"][j] is not None]
    hi = [s["drawn_max"][j] for j in js if s["drawn_max"][j] is not None]
    return (min(lo), max(hi)) if lo else None


def _close(a, b, rtol):
    span = max(abs(b[1] - b[0]), abs(b[0]), abs(b[1]), 1e-300)
    return all(abs(x - y) <= rtol * span for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# The comparison
# ---------------------------------------------------------------------------
def _panel_checks(pid, panels):
    """{"<pid>:<check>": None | "<difference>"} for probe *pid* drawn as
    *panels* (D-33-12.c)."""
    p = _truth()["probes"][pid]
    ptype = _ptype(pid)
    out = {}

    def put(check, bad):
        out["%s:%s" % (pid, check)] = "; ".join(bad) if bad else None

    put("panels", [] if len(panels) == p["n_panels"] else
        ["dash draws %d panels, twoway %d" % (len(panels), p["n_panels"])])
    if len(panels) != p["n_panels"]:
        return out
    if ptype in _CONTOURS:
        bad = []
        for k, fig in enumerate(panels):
            want = len(p["panels"][k]["cuts"]) + 1
            (cr,) = [r for r in fig.renderers
                     if type(r).__name__ == "ContourRenderer"]
            got = len(cr.levels) - 1 if ptype == "contour" \
                else len(cr.levels) + 1
            if got != want:
                bad.append("panel %d: dash %d fill levels (cuts %s), "
                           "twoway %d (cuts %s)" % (
                               k + 1, got, [round(v, 6) for v in cr.levels],
                               want, p["panels"][k]["cuts"]))
        put("levels", bad)
        return out
    rtol = 1e-6 if (ptype in _CURVES or ptype == "histogram") else 1e-9
    rows, ext = {"x": [], "y": []}, []
    bad_rows = []
    for k, fig in enumerate(panels):
        s = _serset(p, k)
        if ptype not in _CURVES:
            got = _rows(ptype, fig)
            if got != s["n_complete"]:
                bad_rows.append("panel %d: dash %d rows, twoway %d"
                                % (k + 1, got, s["n_complete"]))
        for axis in ("x", "y"):
            got, want = _extent(ptype, fig, axis), _serset_extent(ptype, s,
                                                                   axis)
            if got is None or want is None or not _close(got, want, rtol):
                rows[axis].append("panel %d: dash %r, twoway %r"
                                  % (k + 1, got, want))
    if ptype not in _CURVES:
        put("rows", bad_rows)
    put("x", rows["x"])
    put("y", rows["y"])
    if ptype in _CURVES:
        put("values", _value_problems(ptype, p, panels))
    return out


def _value_problems(ptype, p, panels):
    roles = _ROLES.get(ptype, ("y", "x"))
    xj = roles.index("x")
    bad = []
    for k, fig in enumerate(panels):
        s = _serset(p, k)
        curves = _curves(fig)
        for row in s.get("rows") or s.get("samples"):
            x = row[xj]
            if x is None:
                continue
            for j, role in enumerate(roles):
                if role not in ("y", "lo", "hi") or row[j] is None:
                    continue
                if role not in curves:
                    bad.append("panel %d: dash draws no %s" % (k + 1, role))
                    continue
                span = max(abs(s["drawn_max"][j] - s["drawn_min"][j]),
                           abs(row[j]), 1e-300)
                got = _at(curves[role][0], curves[role][1], x)
                if not any(abs(g - row[j]) <= 1e-6 * span for g in got):
                    bad.append("panel %d %s at x=%.10g: dash %s, twoway %.10g"
                               % (k + 1, role, x,
                                  ["%.10g" % g for g in got] or "nothing",
                                  row[j]))
    return bad[:6] + (["... %d more" % (len(bad) - 6)] if len(bad) > 6
                      else [])


def _problems(mode, pid):
    res = _panel_checks(pid, _draw(mode, _by_spec(pid)))
    known = {k: v for k, v in BY_TYPES_KNOWN.items()
             if k.startswith(pid + ":")}
    return known_problems(res, known, "by_types",
                          deliberate=BY_TYPES_DELIBERATE)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_meta_and_probes(self):
        """test/fixtures/by_types_truth.json, by
        scripts/extract_by_types_truth.do: 88 probes, the ids of
        _PROBE_IDS, every one drawn by twoway, each panel naming the
        serset its plot draws."""
        t = _truth()
        assert {"stata_version", "born_date", "dash_commit", "extracted",
                "source"} <= set(t["_meta"])
        assert t["_meta"]["source"] == "scripts/extract_by_types_truth.do"
        assert len(t["probes"]) == 88
        assert sorted(t["probes"]) == sorted(_PROBE_IDS)
        for pid, p in t["probes"].items():
            assert p["rc"] == 0, (pid, p["first_line"])
            assert len(p["panels"]) == p["n_panels"] == \
                (3 if pid.endswith("_total") else 2), pid
            assert all(q["serset"] is not None for q in p["panels"]), pid

    def test_every_type_is_probed(self):
        """_TYPES is every plot type dash draws."""
        assert sorted(_TYPES) == sorted(dr._dash_plot_type_names())


@pytest.mark.parametrize("pid", _PROBE_IDS)
class TestPanelsMatchTwoway:
    def test_saved(self, pid):
        """The saved page's panels against twoway's sersets."""
        assert _problems("saved", pid) == []

    @pytest.mark.batch
    def test_served(self, pid):
        """The served app's panels against twoway's sersets."""
        assert _problems("served", pid) == []


class TestTheKnownDifferences:
    def test_every_known_difference_is_open(self):
        """Rule 3 over every row; every key names a probe and a check."""
        assert dead_rows(BY_TYPES_KNOWN, "by_types") == []
        for key in BY_TYPES_KNOWN:
            pid, _, check = key.partition(":")
            assert pid in _PROBE_IDS and check in _CHECKS, key


# ---------------------------------------------------------------------------
# Unit tests of the readers
# ---------------------------------------------------------------------------
class TestTheReaders:
    def test_at_matches_ties_and_reads_between_points(self):
        xs = np.array([1.0, 2.0, 2.0, 4.0])
        ys = np.array([10.0, 20.0, 21.0, 40.0])
        assert _at(xs, ys, 2.0) == [20.0, 21.0]
        assert _at(xs, ys, 3.0) == [30.5]
        assert _at(xs, ys, 5.0) == []

    def test_close_is_relative_to_the_span(self):
        assert _close((0.0, 1.0), (1e-12, 1.0), 1e-9)
        assert not _close((0.0, 1.0), (1e-3, 1.0), 1e-9)

    def test_serset_columns_by_role(self):
        s = {"drawn_min": [1.0, 0.0, 5.0], "drawn_max": [2.0, 0.0, 9.0]}
        assert _serset_extent("histogram", s, "x") == (5.0, 9.0)
        assert _serset_extent("histogram", s, "y") == (1.0, 2.0)
        assert _serset_extent("rcap", s, "y") == (0.0, 2.0)

    def test_by_spec_shapes(self):
        sp = _by_spec("bt_tsrline_total")
        (plot,) = sp["graphs"][0]["plots"]
        assert plot["xvar"] == "t" and plot["yvar1"] == "mpg"
        assert sp["graphs"][0]["graph_options"]["by"] == "foreign, total"
        assert _by_spec("bt_line_by")["graphs"][0]["plots"][0][
            "options"] == {"sort": "sort"}
