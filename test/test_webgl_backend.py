"""test_webgl_backend.py -- which backend a figure is drawn with (WP-36
DG-14).

A figure of more than ``_WEBGL_THRESHOLD`` (10,000) rows is drawn with
WebGL.  Two faults: the switch counted the DATASET's rows, so a graph of
``in 1/100`` on 20,000 rows, or a by() panel of 4,000, was WebGL; and
Bokeh's WebGL line shader breaks dashed and dotted lines up (research [B]
section 4.7: ink IoU 0.44-0.80 against canvas at 20,000 vertices), while a
backend is a figure's, not a renderer's.  The rule now: the switch counts
the rows a figure draws (its source's rows, or the rows its view keeps),
and a figure that draws a Line, MultiLine or Step glyph with a dash
pattern stays on canvas.  Both modes decide the same way, so each case
renders the saved page's models (``std``) and the generated app's
document (``srv``).

The pixel check (WebGL actually on, SwiftShader) is the release tier's
test_webgl_backend_browser.py.
"""
import json
import os
import re
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, render_models  # noqa: E402

_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_N = 20_000
_MODES = ["std", "srv"]


# ---------------------------------------------------------------------------
# Specs, data and the two renderers
# ---------------------------------------------------------------------------

def _data(n=_N, groups=5):
    """``x = _n``, ``y = mod(_n, 97)``, ``y2 = y + 1`` and ``g``, *groups*
    equal groups, as StataJSON (built by hand: 20,000 rows through
    ``iterrows`` would cost seconds)."""
    names = ["y", "y2", "x", "g"]
    rows = [{"y": float(i % 97), "y2": float(i % 97 + 1), "x": float(i),
             "g": float((i - 1) * groups // n)} for i in range(1, n + 1)]
    return {"StataJSON": {
        "variableNames": names,
        "variableLabels": {v: "" for v in names},
        "valueLabels": {}, "valueLabelNames": {},
        "variableTypeIsString": {v: False for v in names},
        "values": rows}}


def _plot(ptype, y="y", **opts):
    return {"type": ptype, "yvar": y, "xvar": "x", "options": dict(opts)}


def _graph(name, plots, if_expr="", in_expr="", **go):
    go = dict(go, name=name)
    return {"name": name, "plots": plots, "graph_options": go,
            "options": dict(go), "if_expr": if_expr, "in_expr": in_expr}


def _spec(graphs, **bo):
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
         "registry": " ".join(g["name"] for g in graphs), "tabs": "",
         "filter_position": "top", "level": "95", "formats": {}}
    b.update(bo)
    return {"graphs": graphs, "kpis": [], "build_options": b}


def _write(spec, data):
    d = tempfile.mkdtemp(prefix="dash_webgl_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return d, sp, dp


def _std(spec, data):
    """``{figure key: backend}`` of the saved renderer."""
    _, sp, dp = _write(spec, data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = render_models(dr.DashRenderer(sp, dp))
    return {k: f.output_backend for k, f in r.figures.items()}


def _srv(spec, data):
    """``{figure title or name: backend}`` of the generated app's
    document, its by() chrome cells (``dash_by_*``) aside; figures in
    document order, keyed by position."""
    from bokeh.document import Document
    from bokeh.plotting import figure
    d, sp, dp = _write(spec, data)
    ap = os.path.join(d, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_webgl_app_%d" % id(spec))
        doc = Document()
        mod.make_document(doc)
    out, seen = [], set()
    for root in doc.roots:
        for m in root.references():
            if isinstance(m, figure) and m.id not in seen \
                    and not str(m.name or "").startswith("dash_by_"):
                seen.add(m.id)
                out.append(m)
    return {i: f.output_backend for i, f in enumerate(out)}


def _backends(mode, spec, data):
    """The figures' backends, sorted (keys differ between the modes)."""
    got = (_std if mode == "std" else _srv)(spec, data)
    return sorted(got.values())


# ---------------------------------------------------------------------------
# The switch counts the rows a figure draws
# ---------------------------------------------------------------------------

class TestTheSwitchCountsDrawnRows:

    @pytest.mark.parametrize("mode", _MODES)
    def test_in_1_100_on_20000_rows(self, mode):
        """A graph of ``in 1/100`` draws 100 rows: canvas."""
        spec = _spec([_graph("g1", [_plot("scatter")], in_expr="1/100")])
        assert _backends(mode, spec, _data()) == ["canvas"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_by_panels_count_their_own_rows(self, mode):
        """``by(g)``, five panels of 4,000 rows each: every panel canvas."""
        spec = _spec([_graph("g1", [_plot("scatter")], by="g")])
        assert _backends(mode, spec, _data()) == ["canvas"] * 5

    def test_a_view_counts_its_kept_rows(self):
        """A linked graph draws the link group's shared source through its
        qualifier's view: it counts the rows the view keeps, in both
        modes; the helper reads a BooleanFilter's True values, an
        IndexFilter's indices, else the source's row-id column."""
        from bokeh.models import (BooleanFilter, CDSView,
                                  ColumnDataSource, IndexFilter)
        rid = dr._dash_row_id({})
        src = ColumnDataSource({rid: list(range(30)), "y": [0.0] * 30})
        assert dr._dash_drawn_rows(src, None, rid) == 30
        assert dr._dash_drawn_rows(ColumnDataSource({"z": [0.0] * 40})) \
            == 40
        assert dr._dash_drawn_rows(src, CDSView(filter=BooleanFilter(
            booleans=[True, False, True] * 10)), rid) == 20
        assert dr._dash_drawn_rows(src, CDSView(filter=IndexFilter(
            indices=[1, 4, 9])), rid) == 3
        assert dr._dash_drawn_rows(ColumnDataSource({}), None, rid) == 0
        spec = _spec([_graph("g1", [_plot("scatter")]),
                      _graph("g2", [_plot("scatter")], in_expr="1/50")],
                     link="g1 g2")
        assert _std(spec, _data()) == {"g1": "webgl", "g2": "canvas"}
        assert _backends("srv", spec, _data()) == ["canvas", "webgl"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_prefixed_spec_counts_the_same(self, mode):
        """A spec of another working-column prefix (WP-35 DT-19) renders
        through the module copy of its prefix, and its row-id column is
        that prefix's: ``in 1/100`` is canvas, the whole set WebGL."""
        for in_expr, want in (("1/100", ["canvas"]), ("", ["webgl"])):
            spec = dict(_spec([_graph("g1", [_plot("scatter")],
                                      in_expr=in_expr)]),
                        _dash_prefix="__dsh1_")
            assert _backends(mode, spec, _data()) == want

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_solid_scatter_stays_webgl(self, mode):
        """Guard: 10,001 rows of a solid scatter is WebGL, as before."""
        spec = _spec([_graph("g1", [_plot("scatter")])])
        assert _backends(mode, spec, _data(10_001)) == ["webgl"]


# ---------------------------------------------------------------------------
# A dashed line keeps its figure on canvas
# ---------------------------------------------------------------------------

class TestDashedLinesStayOnCanvas:

    @pytest.mark.parametrize("mode", _MODES)
    def test_lpattern_dash_on_20000_rows(self, mode):
        """``line y x, lpattern(dash)`` over 20,000 rows: canvas; the same
        line solid stays WebGL."""
        dashed = _spec([_graph("g1", [_plot("line", lpattern="dash")])])
        solid = _spec([_graph("g1", [_plot("line")])])
        assert _backends(mode, dashed, _data()) == ["canvas"]
        assert _backends(mode, solid, _data()) == ["webgl"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_dashed_scheme_default_is_canvas(self, mode):
        """s2mono draws its second line dashed by default (linepattern
        p2lineplot dash; s1mono's second line is solid): canvas."""
        spec = _spec([_graph("g1", [_plot("line"), _plot("line", "y2")])],
                     scheme="s2mono")
        assert _backends(mode, spec, _data()) == ["canvas"]

    def test_the_helper(self):
        """A WebGL figure with a dotted line goes to canvas; a solid line
        and a scatter stay WebGL; a canvas figure is left alone."""
        from bokeh.plotting import figure
        f = figure(output_backend="webgl")
        f.scatter([1, 2], [1, 2])
        f.line([1, 2], [1, 2])
        assert dr._dash_dashes_on_canvas(f) is f
        assert f.output_backend == "webgl"
        f.line([1, 2], [2, 1], line_dash="dotted")
        dr._dash_dashes_on_canvas(f)
        assert f.output_backend == "canvas"
        # MultiLine keeps its pattern as text ("solid" is not a dash; a
        # field of per-line patterns may hold one); Step as a list.
        for draw, want in (
                (lambda g: g.multi_line([[1, 2]], [[1, 2]]), "webgl"),
                (lambda g: g.multi_line([[1, 2]], [[1, 2]],
                                        line_dash="dashed"), "canvas"),
                (lambda g: g.multi_line(xs="xs", ys="ys", line_dash="dd",
                                        source={"xs": [[1, 2]],
                                                "ys": [[1, 2]],
                                                "dd": ["dotted"]}),
                 "canvas"),
                (lambda g: g.step([1, 2], [1, 2]), "webgl"),
                (lambda g: g.step([1, 2], [1, 2], line_dash="4 4"),
                 "canvas")):
            g = figure(output_backend="webgl")
            draw(g)
            dr._dash_dashes_on_canvas(g)
            assert g.output_backend == want
        c = figure()
        c.line([1, 2], [1, 2], line_dash="dashed")
        dr._dash_dashes_on_canvas(c)
        assert c.output_backend == "canvas"
        s = figure(output_backend="svg")
        s.line([1, 2], [1, 2], line_dash="dashed")
        dr._dash_dashes_on_canvas(s)
        assert s.output_backend == "svg"


# ---------------------------------------------------------------------------
# The help states the rule
# ---------------------------------------------------------------------------

def _between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


class TestTheHelp:

    def test_the_webgl_paragraph(self):
        with open(_HELP, encoding="utf-8") as fh:
            text = fh.read()
        para = _between(text, "{ul:WebGL.}", "{ul:A served dashboard}")
        flat = re.sub(r"\s+", " ", re.sub(r"\{[a-z]+:([^}]*)\}", r"\1",
                                          para))
        assert "more than 10,000 rows" in flat
        assert "dashed, dotted or patterned line" in flat
        assert "drawn on the ordinary canvas" in flat
        assert "the graph's own" in flat and "not the dataset's" in flat
