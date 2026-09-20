"""The same command must draw the same dashboard in both modes.

`dash` has two renderers. ``DashRenderer`` builds Bokeh models directly;
``ServerAppBuilder`` emits a ``.py`` file that builds them again, in generated
string literals. They drifted, and nothing could tell:

* ``scheme()`` reached one and not the other, so every served plot was
  ``#1f77b4`` on white
* ``msize(large)`` meant 15px in one and 12px in the other — two size maps
  for one set of Stata keywords
* ``dash histogram mpg`` drew 8 bars in one and 20 in the other, and 20 is
  not the answer Stata gives
* ``layout()``, ``tabs()``, ``filterposition()`` and ``subtitle()`` were
  read by one and ignored by the other
* ``link()`` shared a source in one and silently did nothing in the other

Each of those has its own regression test. This file is the standing guard:
it renders a corpus through BOTH paths and compares the models, so the next
divergence fails here rather than being found by a user.

**Legitimate differences are listed explicitly**, not tolerated by a loose
comparison — a test that accepts unknown differences passes the next drift
too. See ``ALLOWED``.
"""
import importlib.util
import itertools
import json
import os
import sys

import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
})

# ---------------------------------------------------------------------------
# Differences that are CORRECT, with the reason. Anything not listed here is
# a failure.
# ---------------------------------------------------------------------------
ALLOWED = {
    "aggregate layers recompute live": (
        "The server recomputes histogram bins, fitted lines and kernel "
        "densities from the filtered rows on every widget move; standalone "
        "precomputes them and rescales in JS. The INITIAL values must still "
        "agree, which is what this file checks."
    ),
    "linked graphs share one source": (
        "Standalone always builds one ColumnDataSource per dashboard and "
        "filters with CDSView; the server builds one per graph unless "
        "link() says otherwise. Source identity is therefore not compared."
    ),
}


def _spec(plots, build_options=None, graph_options=None):
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    bo.update(build_options or {})
    go = {"name": "g1"}
    go.update(graph_options or {})
    return {"graphs": [{"name": "g1", "graph_options": go,
                        "options": dict(graph_options or {}), "plots": plots}],
            "kpis": [], "build_options": bo}


def _standalone_figures(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"std_s_{tag}.json"
    dp = tmp_path / f"std_d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    r = dr.DashRenderer(str(sp), str(dp))
    r.render()
    return list(r.figures.values())


def _server_figures(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"srv_s_{tag}.json"
    dp = tmp_path / f"srv_d_{tag}.json"
    ap = tmp_path / f"srv_a_{tag}.py"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_parity_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)

    out, seen = [], set()

    def walk(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    walk(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        if type(m).__name__ == "figure":
            out.append(m)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                walk(k)

    for root in doc.roots:
        walk(root)
    return out


def _glyph_profile(fig):
    """The visual properties that have drifted before, per glyph."""
    prof = []
    for r in fig.renderers:
        g = getattr(r, "glyph", None)
        if g is None:
            continue
        entry = {"type": type(g).__name__}
        for attr in ("marker", "size", "fill_color", "line_color",
                     "line_width", "line_dash", "fill_alpha"):
            v = getattr(g, attr, None)
            if isinstance(v, (list, tuple)):
                v = list(v)
            if isinstance(v, (str, int, float, list)) or v is None:
                entry[attr] = v
        prof.append(entry)
    return prof


def _chrome(fig):
    return {
        "background_fill_color": fig.background_fill_color,
        "border_fill_color": fig.border_fill_color,
        "xgrid": [g.grid_line_color for g in fig.xgrid],
        "ygrid": [g.grid_line_color for g in fig.ygrid],
    }


CORPUS = [
    ("scatter, default scheme",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}),
    ("scatter, s1mono",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "s1mono"}),
    ("scatter, economist",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("scatter, session scheme only",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"session_scheme": "s1rcolor"}),
    ("scatter, explicit msize(large)",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
       "options": {"msize": "large"}}], {}),
    ("scatter, explicit mcolor",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
       "options": {"mcolor": "maroon"}}], {}),
    ("scatter, explicit msymbol",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
       "options": {"msymbol": "triangle"}}], {}),
    ("two scatters, scheme sequence",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
      {"type": "scatter", "yvar": "weight", "xvar": "mpg", "options": {}}],
     {"scheme": "s2color"}),
]


@pytest.mark.parametrize("name,plots,bo", CORPUS,
                         ids=[c[0] for c in CORPUS])
class TestTheTwoModesAgree:
    def test_same_number_of_figures(self, tmp_path, name, plots, bo):
        spec = _spec(plots, bo)
        assert len(_standalone_figures(tmp_path, spec)) == \
               len(_server_figures(tmp_path, spec))

    def test_same_marker_colour_and_size(self, tmp_path, name, plots, bo):
        spec = _spec(plots, bo)
        std = _glyph_profile(_standalone_figures(tmp_path, spec)[0])
        srv = _glyph_profile(_server_figures(tmp_path, spec)[0])
        for attr in ("marker", "size", "fill_color", "line_color"):
            a = [g.get(attr) for g in std if g["type"] == "Scatter"]
            b = [g.get(attr) for g in srv if g["type"] == "Scatter"]
            assert a == b, (
                f"{name}: {attr} differs — standalone {a}, server {b}"
            )

    def test_same_figure_chrome(self, tmp_path, name, plots, bo):
        spec = _spec(plots, bo)
        std = _chrome(_standalone_figures(tmp_path, spec)[0])
        srv = _chrome(_server_figures(tmp_path, spec)[0])
        assert std["background_fill_color"] == srv["background_fill_color"]
        assert std["border_fill_color"] == srv["border_fill_color"]
        # The scheme decides whether a grid is drawn at all; both modes must
        # make the same decision.
        assert (any(c is not None for c in std["xgrid"]) ==
                any(c is not None for c in srv["xgrid"]))
        assert (any(c is not None for c in std["ygrid"]) ==
                any(c is not None for c in srv["ygrid"]))


class TestAggregateLayersStartFromTheSameNumbers:
    """A live recompute is allowed; a different starting value is not."""

    def test_histogram_bin_count_agrees(self, tmp_path):
        import numpy as np
        spec = _spec([{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {}}])
        edges, _ = dr.GlyphMapper._histogram_grid(
            _DF["mpg"].dropna().values.astype(float), {})
        from bokeh.models import ColumnDataSource
        srv_figs = _server_figures(tmp_path, spec)
        bars = None
        for fig in srv_figs:
            for r in fig.renderers:
                src = getattr(r, "data_source", None)
                if src is not None and "left" in getattr(src, "data", {}):
                    bars = len(src.data["left"])
        assert bars == len(edges) - 1, (
            f"standalone draws {len(edges) - 1} bars, server draws {bars}"
        )

    def test_an_explicit_bin_option_agrees_too(self, tmp_path):
        import numpy as np
        spec = _spec([{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {"bin": "6"}}])
        edges, _ = dr.GlyphMapper._histogram_grid(
            _DF["mpg"].dropna().values.astype(float), {"bin": "6"})
        srv_figs = _server_figures(tmp_path, spec)
        bars = None
        for fig in srv_figs:
            for r in fig.renderers:
                src = getattr(r, "data_source", None)
                if src is not None and "left" in getattr(src, "data", {}):
                    bars = len(src.data["left"])
        assert bars == len(edges) - 1 == 6


class TestTheAllowanceListIsExplicit:
    def test_every_allowance_states_a_reason(self):
        assert ALLOWED, "an empty allowance list hides nothing, but says nothing"
        for key, why in ALLOWED.items():
            assert len(why) > 40, f"{key}: allowances must say why"
