"""
test_by_grid.py -- by() panels placed, sized and spaced as twoway does
(WP-30 P1.15b).

dash named rows(), holes(), colfirst, compact, iscale() and imargin() as
ignored, drew every panel at the plain graph's size in a ceil(sqrt(n))
grid and gave each panel the whole xsize()/ysize() ratio.  The truth is
test/fixtures/by_grid_truth.json (scripts/extract_by_grid_truth.do):
twoway's cells read from its SVG labels, its size multiplier from the
marker-label font, its panel margins from the graph object, and each
shipped scheme's ``margin by_indiv``.  dash.ado's refusals are compared
with live twoway in test_by_suboptions.cscript BYG-01..BYG-18.
"""

import copy
import json
import math
import os
import re
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import itertools  # noqa: E402
import tempfile  # noqa: E402

import dash_render as dr  # noqa: E402
from conftest import load_app, render_models  # noqa: E402
import test_by_text as tbt  # noqa: E402
from by_panel_probe import by_grid, panel_label  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_grid_truth.json")
_MODES = ("saved", "served")
_T = None
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_grid_")
_UNIT = dr.OptionTranslator.PT_PER_RS * dr.OptionTranslator.PX_PER_PT


def _truth():
    global _T
    if _T is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _T = json.load(fh)
    return _T


def _data():
    """by_text_truth's auto data with twoway's g10 = mod(_n, 10) and
    g3 = mod(_n, 3), as the extractor made them."""
    data = copy.deepcopy(tbt._truth()["data"])
    # WP-33 BY-24: the regenerated fixture's data block is the columnar
    # form dash writes now (dataFormat dash-columns-1); the callers here
    # and in the files that import this one edit rows, so it is given
    # back as the row form ("values", a missing number "null" as the row
    # writer wrote it), which the renderers read too.
    if "columns" in data:
        dr._dash_decode_columns(data)
        cols = data.pop("columns")
        data.pop("dataFormat")
        data["values"] = [
            {v: (c[i] if isinstance(c, list) else
                 ("null" if c[i] != c[i] else float(c[i])))
             for v, c in cols.items()}
            for i in range(data["numberOfRecords"])]
    for i, row in enumerate(data["values"], start=1):
        row["g10"] = float(i % 10)
        row["g3"] = float(i % 3)
    for v in ("g10", "g3"):
        data["variableNames"].append(v)
        data["storageTypes"][v] = "float"
        data["variableIsString"][v] = False
        data["variableLabels"][v] = ""
    data["numberOfVariables"] += 2
    data["variableIndices"] = list(range(1, data["numberOfVariables"] + 1))
    return data


def _many(gos, scheme="s2color"):
    """One spec holding a graph g<i> per graph-options dict of *gos*."""
    graphs = []
    for i, go in enumerate(gos, start=1):
        go = dict(go, name="g%d" % i)
        graphs.append({"name": go["name"], "graph_options": go,
                       "options": dict(go),
                       "plots": [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}],
                       "if_expr": "", "in_expr": ""})
    spec = tbt._spec({}, scheme=scheme)
    spec["graphs"] = graphs
    spec["build_options"]["registry"] = " ".join(g["name"] for g in graphs)
    return spec


def _build(mode, spec):
    """``(roots, notes)`` of *spec* drawn in *mode* over :func:`_data`."""
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_data(), fh)
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            roots = [r._last_layout_root]
        else:
            from bokeh.document import Document
            ap = os.path.join(_TMP, "app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_bg_app_%d" % tag)
            doc = Document()
            mod.make_document(doc)
            roots = list(doc.roots)
    return roots, [str(w.message) for w in caught]


def _grids(roots):
    """Every by() GridPlot under *roots*: a grid holding labelled panels
    (the served dashboard's own grid holds figures too)."""
    from bokeh.models import GridPlot
    out = []
    for root in roots:
        for m in root.references():
            if isinstance(m, GridPlot) and any(
                    type(c[0]).__name__ == "figure" and panel_label(c[0])
                    for c in m.children):
                out.append(m)
    return out


def _cells(grid):
    """``[(label, row, col)]`` of a by() grid, rows re-based past its head."""

    class _R:
        def references(self_inner):
            return [grid]
    panels, _, _ = by_grid(_R())
    return [(panel_label(f), r, c) for r, c, f in panels]


def _grid_probes():
    return sorted(_truth()["grid"])


# ---------------------------------------------------------------------------
class TestTheGrammar:
    def test_python_equals_mata(self):
        with open(os.path.join(_HERE, "..", "dash_parse.mata"),
                  encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("string matrix _dash_by_grammar()", 1)[1]
        body = body.split("return(", 1)[0]
        words = " ".join(re.findall(r's = s \+ "([^"]*)"', body)).split()
        rows = [tuple(words[i:i + 5]) for i in range(0, len(words), 5)]
        py = [(k, mn, str(t), str(st), str(rp))
              for k, (mn, t, st, rp) in dr._DASH_BY_GRAMMAR.items()]
        assert rows == py

    def test_every_spelling_is_twoways(self):
        t = _truth()
        bad = []
        for probe, rec in t["accepted"].items():
            row = dr._dash_by_word(probe)[0]
            if (row is not None) != (rec["rc"] == 0):
                bad.append("%s: twoway rc %d, dash row %r"
                           % (probe, rec["rc"], row))
        for name in t["declared"]:
            full = name.rstrip("()").lower()
            mn = re.match(r"[A-Z0-9]*", name.rstrip("()")).group(0).lower() \
                or full
            row = dr._DASH_BY_GRAMMAR.get(full)
            if row is None or row[0] != mn or bool(row[1]) != \
                    name.endswith("()"):
                bad.append("declared %s: %r" % (name, row))
        for probe, rec in t["refusals"].items():
            toks = dr._dash_by_tokens(probe)
            if len(toks) == 2 and toks[0].split("(")[0] == \
                    toks[1].split("(")[0]:
                row = dr._dash_by_word(toks[0])[0]
                rep = dr._DASH_BY_GRAMMAR[row][3]
                if bool(rep) != (rec["rc"] == 0):
                    bad.append("repeat %s: twoway rc %d, repeat_ok %d"
                               % (probe, rec["rc"], rep))
        assert not bad, "\n".join(bad)


class TestPositions:
    def test_every_probe(self):
        bad = []
        for by, rec in _truth()["grid"].items():
            opts = dr._dash_by_grid_options(by)
            _c, rows, cols, extra = dr._dash_by_positions(rec["n"], opts)
            drawn = extra["drawn"][0]
            want = [tuple(c[1:]) for c in rec["cells"]]
            if (rows, cols) != (rec["rows"], rec["cols"]) or drawn != want:
                bad.append("%s: rows/cols %s vs %s, cells %s vs %s"
                           % (by, (rows, cols), (rec["rows"], rec["cols"]),
                              drawn, want))
        assert not bad, "\n".join(bad)

    def test_full_n_counts_holes_beyond_the_grid(self):
        _c, rows, cols, extra = dr._dash_by_positions(
            5, dr._dash_by_grid_options("rep78, holes(9)"))
        assert (rows, cols, extra["full_n"]) == (2, 3, 6)

    def test_limit_clamps(self):
        _c, rows, cols, extra = dr._dash_by_positions(
            4, {"cols": 10 ** 12})
        assert (rows, cols) == (1, 1000)
        assert extra["drawn"][1:] == (1, 4)


def _grid_category(by):
    """A grid probe's family for the served subset: its by() variable
    and whether it has holes()."""
    var, _, opts = by.partition(",")
    return (var.strip(), bool(re.search(r"\bhol", opts)))


#: Probes per node, one page each, and the gate's served subset (pytest
#: speed, 22oct2026): the first probe of each _grid_category and every
#: third probe of the rest; release checks every probe served.
_GRID_PARAMS = probe_params(_grid_probes(), representative(
    _grid_probes(), _grid_category, stride=3), size=5, saved_size=18)


class TestTheGridIsDrawn:
    @pytest.mark.parametrize("mode,group", _GRID_PARAMS)
    def test_every_probe(self, mode, group):
        probes = list(group)
        roots, _ = _build(mode, _many([{"by": by} for by in probes]))
        grids = _grids(roots)
        assert len(grids) == len(probes)
        seen = {}
        for g in grids:
            seen.setdefault(tuple(sorted(lab for lab, _r, _c in _cells(g))),
                            []).append(g)
        bad = []
        for by in probes:
            want = [tuple(c) for c in _truth()["grid"][by]["cells"]]
            hits = [g for g in seen.get(tuple(sorted(c[0] for c in want)),
                                        []) if sorted(_cells(g)) ==
                    sorted(want)]
            if not hits:
                bad.append(by)
        assert not bad, "no grid drawn in twoway's cells for: %s" % bad


class TestTheSizes:
    def test_multiplier(self):
        bad = []
        for scheme, rows in _truth()["sizes"].items():
            for key, rec in rows.items():
                if key.startswith("plain") or rec.get("mult") is None:
                    continue
                by = re.search(r"by\((.*?)\)(?: xsize| scheme)",
                               rec["options"]).group(1)
                n = 10 if by.startswith("g10") else 2
                got = dr._dash_by_size_mult(by, n)
                want = rec["mult"]
                if abs(got - want) > max(0.005 * want, 1e-9):
                    bad.append("%s %s: %s vs %s" % (scheme, by, got, want))
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", _MODES)
    def test_panels_are_scaled(self, mode):
        spec = _many([{"by": "foreign", "title": "T"}, {}])
        spec["graphs"][1]["graph_options"]["title"] = "T"
        roots, _ = _build(mode, spec)
        grid = _grids(roots)[0]
        panel = next(c[0] for c in grid.children
                     if type(c[0]).__name__ == "figure")
        inside = {id(c[0]) for c in grid.children}
        plain = next(m for r in roots for m in r.references()
                     if type(m).__name__ == "figure"
                     and id(m) not in inside)

        def sizes(f):
            g = f.renderers[0].glyph
            ax = f.yaxis[0]
            return (g.size, g.line_width,
                    float(str(ax.major_label_text_font_size)[:-2]),
                    ax.major_tick_out, ax.axis_line_width)
        got, base = sizes(panel), sizes(plain)
        for a, b in zip(got, base):
            assert a == pytest.approx(0.85 * b, rel=0.02, abs=0.51)
        chrome = [c[0] for c in grid.children
                  if getattr(c[0], "name", None) == "dash_by_foot"]
        assert not chrome or getattr(chrome[0], "_dash_by_scaled",
                                     None) is None
        before = sizes(panel)
        dr._dash_by_scale_panel(panel, 0.5)
        assert sizes(panel) == before

    def test_every_numeric_size_is_scaled(self):
        go = {"name": "g1", "yline": "20"}
        plots = [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mlabel": "rep78"}},
            {"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "rcap", "yvar": "mpg", "y2var": "headroom",
             "xvar": "weight", "options": {}},
        ]
        spec = tbt._spec({})
        g = spec["graphs"][0]
        g["plots"], g["graph_options"], g["options"] = plots, go, dict(go)

        def fig():
            roots, _ = _build("saved", spec)
            return next(m for r in roots for m in r.references()
                        if type(m).__name__ == "figure")

        def snapshot(f):
            out = {}
            for m in f.references():
                for p in m.properties_with_values(include_defaults=True):
                    v = getattr(m, p)
                    if isinstance(v, (int, float, str)) and \
                            not isinstance(v, bool):
                        out[(type(m).__name__, m.id[-8:] and
                             _order(f, m), p)] = v
            return out
        a, b = fig(), fig()
        dr._dash_by_scale_panel(b, 0.5)
        sa, sb = snapshot(a), snapshot(b)
        kinds = {p for v in dr._DASH_BY_SCALED_PROPS.values() for p in v}
        # The models a panel draws; the figure's own border, the zoom
        # overlays, a legend and a colour bar are not panel sizes.
        unscaled = ("figure", "PolyAnnotation", "BoxAnnotation",
                    "AreaVisuals", "Legend", "ColorBar")
        bad = []
        for k, va in sa.items():
            vb = sb.get(k)
            if isinstance(va, float) and math.isnan(va) and \
                    isinstance(vb, float) and math.isnan(vb):
                continue
            if k[2] in kinds and k[0] not in unscaled:
                want = dr._dash_by_scale_value(va, 0.5)
                if isinstance(want, float) and isinstance(vb, int):
                    want = int(round(want))
                if vb != want:
                    bad.append("%s: %r -> %r (want %r)" % (k, va, vb, want))
            elif k[0] == "figure" and k[2] == "outline_line_width":
                # Flipped (WP-41 41-05): the plot region's outline takes
                # by()'s size as its axis lines do (figure_geometry_truth
                # .json P1: both 4.90 of 3960); it was the figure's own
                # border, left alone.
                if vb != dr._dash_by_scale_value(va, 0.5):
                    bad.append("%s: %r -> %r" % (k, va, vb))
            elif vb != va and k[2] not in ("aspect_ratio",):
                bad.append("%s changed: %r -> %r" % (k, va, vb))
        assert not bad, "\n".join(bad[:30])
        assert b._dash_by_scaled == 0.5


def _order(fig, model):
    """A stable key for *model* within *fig*: its kind's position in the
    figure's references, sorted by kind and id order of creation."""
    same = [m for m in fig.references() if type(m) is type(model)]
    same.sort(key=lambda m: int(re.sub(r"\D", "", m.id) or 0))
    return same.index(model)


class TestSpacing:
    def test_every_probe(self):
        bad = []
        for scheme, rows in _truth()["sizes"].items():
            fig0 = type("F", (), {})()
            fig0._dash_by_indiv = dr.SchemeParser(scheme).by_indiv_margin()
            for key, rec in rows.items():
                if "col_gap" not in rec:
                    continue
                by = re.search(r"by\((.*?)\)(?: xsize| scheme)",
                               rec["options"]).group(1)
                got = dr._dash_by_spacing(fig0, dr._dash_by_grid_options(by))
                want = (int(round(rec["row_gap"] * _UNIT)),
                        int(round(rec["col_gap"] * _UNIT)))
                if got != want:
                    bad.append("%s %s: %s vs %s" % (scheme, by, got, want))
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_grid_is_spaced(self, mode):
        roots, _ = _build(mode, _many([{"by": "foreign"},
                                       {"by": "foreign, compact"}],
                                      scheme="stcolor"))
        got = sorted(tuple(g.spacing) for g in _grids(roots))
        assert got == [(0, 0), (int(round(2.4 * _UNIT)),
                                int(round(7.0 * _UNIT)))]


class TestTheIndivTable:
    def test_every_shipped_scheme(self):
        bad = [s for s, rec in _truth()["by_indiv"].items()
               if list(dr.SchemeParser(s).by_indiv_margin()) != rec["sides"]]
        assert not bad


class TestTheArrayRatio:
    @pytest.mark.parametrize("mode", _MODES)
    def test_xsize12_ysize3(self, mode):
        roots, _ = _build(mode, _many([
            {"by": "foreign", "xsize": "12", "ysize": "3"},
            {"by": "foreign", "aspectratio": ".5"}]))
        ratios = sorted(tuple(round(c[0].aspect_ratio, 6)
                              for c in g.children
                              if type(c[0]).__name__ == "figure")
                        for g in _grids(roots))
        # Flipped (WP-45 VF-4): aspectratio(.5) gave the panels 1/.5 as
        # their own ratio; the figure was held in a 160-560 px band at 2.88 pt a unit; twoway
        # draws its graph's shape at 0.72 pt per inch of its smaller side
        # (VF-4, DECISIONS A-1): they start at the scheme's 5.5:4 and the
        # fit hook shapes each plot region (frame_ar) as it lays out.
        assert ratios == [(1.375, 1.375), (2.0, 2.0)]


class TestTheAutoLayoutSeesFacets:
    def test_wide_facets_get_a_row(self):
        wide = type("F", (), {})()
        wide.aspect_ratio, wide._dash_array_ar = 2.0, 4.0
        sq = type("F", (), {})()
        sq.aspect_ratio = 1.0
        figs = {"wide__by__1": wide, "wide__by__2": wide, "sq1": sq,
                "sq2": sq}
        rows = dr._dash_auto_bs_layout(["wide", "sq1", "sq2"], [], figs)
        assert rows[0] == [("wide", 12)]


class TestNamedNoMore:
    def test_drawn_sub_options_are_not_named(self):
        for sub in ("rows(2)", "r(2)", "holes(1 3)", "colfirst", "compact",
                    "style(compact)", "iscale(*.8)", "imargin(small)"):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                out = dr._dash_parse_by("foreign, " + sub)
            assert out[4] == [] and not caught, sub

    def test_capitals_are_named_by_the_renderer(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            out = dr._dash_parse_by("foreign, YRESCALE")
        assert out[4] == ["YRESCALE"]


class TestHostileInput:
    def test_bounded(self):
        for by in ("foreign, " + "compact " * 125000,
                   "foreign, holes(1/1000000)", "foreign, iscale(1e400)",
                   'foreign, imargin("</style>")'):
            t0 = time.perf_counter()
            opts = dr._dash_by_grid_options(by)
            _c, _r, _cc, extra = dr._dash_by_positions(3, opts)
            m = dr._dash_by_size_mult(by, extra["full_n"])
            fig0 = type("F", (), {})()
            sp = dr._dash_by_spacing(fig0, opts)
            # Linear: a million characters in well under the bound even on
            # a loaded worker; a quadratic pass would take minutes.
            assert time.perf_counter() - t0 < 3.0
            assert math.isfinite(m) and 0 <= m <= 10000
            assert all(isinstance(v, int) for v in sp)
