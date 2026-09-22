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


def _annotations(fig):
    """The annotations a figure carries, as comparable dicts.

    Glyph properties were compared and annotations were not, so the served
    marker labels could use a second size table, a different default font and
    different offsets (measured: 14px at (5, 5) against the renderer's 15px at
    (4, 0)), and the served note and caption could sit on top of each other,
    without this file noticing.
    """
    from bokeh.models import Label, LabelSet, Span
    out = []
    for r in list(fig.center) + list(fig.above) + list(fig.below) + \
            list(fig.left) + list(fig.right):
        if isinstance(r, LabelSet):
            out.append({"kind": "LabelSet", "text": r.text,
                        "font": r.text_font_size, "color": r.text_color,
                        "x_offset": r.x_offset, "y_offset": r.y_offset})
        elif isinstance(r, Label):
            out.append({"kind": "Label", "text": r.text,
                        "font": r.text_font_size, "color": r.text_color})
        elif isinstance(r, Span):
            out.append({"kind": "Span", "dimension": r.dimension,
                        "location": r.location, "color": r.line_color,
                        "width": r.line_width, "dash": list(r.line_dash or [])})
    return sorted(out, key=lambda d: json.dumps(d, sort_keys=True,
                                                default=str))


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
    # Every entry above is a scatter, which is how seven glyph types and
    # every annotation drifted without this file noticing.
    ("line, default scheme",
     [{"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("line, economist",
     [{"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("area",
     [{"type": "area", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("bar",
     [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("histogram",
     [{"type": "histogram", "yvar": "mpg", "xvar": "", "options": {}}], {}),
    ("kdensity",
     [{"type": "kdensity", "yvar": "mpg", "xvar": "", "options": {}}], {}),
    ("mband",
     [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("dropline",
     [{"type": "dropline", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}),
    ("spike",
     [{"type": "spike", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("connected, s1mono",
     [{"type": "connected", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "s1mono"}),
    ("scatter with a fit, economist",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
      {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("scatter with marker labels",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
       "options": {"mlabel": "foreign"}}], {}),
    ("scatter with an explicit line width",
     [{"type": "line", "yvar": "mpg", "xvar": "weight",
       "options": {"lwidth": "thick"}}], {}),
    ("lpoly and lpolyci on the same data",
     [{"type": "lpoly", "yvar": "mpg", "xvar": "weight", "options": {}},
      {"type": "lpolyci", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}),
    ("dot",
     [{"type": "dot", "yvar": "mpg", "xvar": "weight", "options": {}}], {}),
    ("rcapsym",
     [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "weight",
       "xvar": "foreign", "options": {}}], {}),
    ("scatteri",
     [{"type": "scatteri",
       "values": [[20.0, 3000.0], [30.0, 4000.0]], "options": {}}], {}),
    ("mspline, economist",
     [{"type": "mspline", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("spike, economist",
     [{"type": "spike", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("dropline, economist",
     [{"type": "dropline", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {"scheme": "economist"}),
    ("scatter with marker labels and a size",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
       "options": {"mlabel": "foreign", "mlabsize": "large"}}], {}),
    ("reference lines",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}, {"xline": "3000", "yline": "20"}),
    ("a styled reference line",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}, {"xline": "3000, lcolor(red) lpattern(solid) lwidth(thick)"}),
    ("note and caption",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}, {"note": "N", "caption": "C"}),
    # by() -- the corpus never set it, which is how twenty plot types came
    # to serve empty panels (GAPS.md D4).  These compare the FIRST panel;
    # test_server_facets.py compares every panel of all 38 types.
    ("scatter under by()",
     [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}, {"by": "foreign"}),
    ("lfitci under by()",
     [{"type": "lfitci", "yvar": "mpg", "xvar": "weight", "options": {}}],
     {}, {"by": "foreign"}),
    ("rarea under by()",
     [{"type": "rarea", "yvar1": "mpg", "yvar2": "weight", "xvar": "foreign",
       "options": {}}], {}, {"by": "foreign"}),
    ("histogram under by(, total)",
     [{"type": "histogram", "yvar": "mpg", "xvar": "", "options": {}}],
     {}, {"by": "foreign, total"}),
    ("function under by()",
     [{"type": "function", "expr": "x^2", "options": {}}],
     {}, {"by": "foreign"}),
    ("pcspike under by()",
     [{"type": "pcspike", "y1var": "mpg", "x1var": "weight", "y2var": "mpg",
       "x2var": "foreign", "options": {}}], {}, {"by": "foreign"}),
]


CORPUS = [(c + ({},))[:4] for c in CORPUS]


@pytest.mark.parametrize("name,plots,bo,go", CORPUS,
                         ids=[c[0] for c in CORPUS])
class TestTheTwoModesAgree:
    def test_same_number_of_figures(self, tmp_path, name, plots, bo, go):
        spec = _spec(plots, bo, go)
        assert len(_standalone_figures(tmp_path, spec)) == \
               len(_server_figures(tmp_path, spec))

    def test_same_glyph_properties(self, tmp_path, name, plots, bo, go):
        """Every property _glyph_profile collects, for every glyph type.

        This used to assert four of the seven collected properties, and only
        on Scatter glyphs. line_width, line_dash and fill_alpha were gathered
        and thrown away, and every non-scatter glyph was skipped -- so the
        file was green while the served app drew area fills at 0.4 where
        standalone draws 1.0, histogram bars with a white 1.5px outline that
        standalone does not draw, and faceted markers at a fixed size 6
        whatever the scheme asked for.
        """
        spec = _spec(plots, bo, go)
        std = _glyph_profile(_standalone_figures(tmp_path, spec)[0])
        srv = _glyph_profile(_server_figures(tmp_path, spec)[0])
        assert [g["type"] for g in std] == [g["type"] for g in srv], (
            f"{name}: different glyphs — standalone "
            f"{[g['type'] for g in std]}, server {[g['type'] for g in srv]}"
        )
        for i, (a, b) in enumerate(zip(std, srv)):
            for attr in sorted(set(a) | set(b)):
                assert a.get(attr) == b.get(attr), (
                    f"{name}: glyph {i} ({a['type']}) {attr} differs — "
                    f"standalone {a.get(attr)!r}, server {b.get(attr)!r}"
                )

    def test_same_annotations(self, tmp_path, name, plots, bo, go):
        spec = _spec(plots, bo, go)
        std = _annotations(_standalone_figures(tmp_path, spec)[0])
        srv = _annotations(_server_figures(tmp_path, spec)[0])
        assert std == srv, (
            f"{name}: annotations differ\n  standalone {std}\n  server     {srv}"
        )

    def test_the_profile_is_not_empty(self, tmp_path, name, plots, bo, go):
        """Guards the guard: comparing two empty lists proves nothing."""
        spec = _spec(plots, bo, go)
        std = _glyph_profile(_standalone_figures(tmp_path, spec)[0])
        assert std, f"{name}: no glyphs collected, so nothing was compared"
        assert all(len(g) > 1 for g in std), (
            f"{name}: glyphs carry no comparable properties"
        )

    def test_same_figure_chrome(self, tmp_path, name, plots, bo, go):
        spec = _spec(plots, bo, go)
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


class TestTheCopiedHelpersBringTheirCallees:
    """A function copied into the app whose callee stays behind is a NameError.

    `_shared_stat_lines' copies the renderer's own statistical helpers into
    the generated app with `inspect.getsource', which copies the TEXT and not
    what the text calls. It has now happened three times:

      * `_stata_if_to_pandas' gained `_mask_string_literals' and the served
        page raised on every qualifier;
      * `_resolve_seed' gained `_jitter_seed' and the served lpolyci band
        raised on every session;
      * before either, a copied body referenced `_LPOLY_ROT_C', which is why
        `_supply_missing_constants' exists -- but that pass supplies
        CONSTANTS, not functions.

    Each time, the failure surfaced on the served page rather than here. This
    imports the generated app and asks Python to resolve every global the
    copied block refers to.
    """

    @staticmethod
    def _app_module(tmp_path):
        import importlib.util
        import warnings
        tag = next(_SEQ)
        spec = _spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
        sp = tmp_path / f"cs_{tag}.json"
        dp = tmp_path / f"cd_{tag}.json"
        ap = tmp_path / f"ca_{tag}.py"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(_DF)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_callee_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ms.loader.exec_module(mod)
        return mod

    def test_every_global_a_copied_helper_calls_is_defined(self, tmp_path):
        import types
        mod = self._app_module(tmp_path)
        names = set(vars(mod))
        missing = {}
        for _n, _obj in list(vars(mod).items()):
            if not isinstance(_obj, types.FunctionType):
                continue
            if getattr(_obj, "__module__", None) != mod.__name__:
                continue
            # co_names mixes globals with ATTRIBUTE names -- `w._dash_var'
            # is in it too -- so read the bytecode and take only the names
            # loaded as globals.
            import builtins
            import dis
            for _ins in dis.get_instructions(_obj):
                if _ins.opname not in ("LOAD_GLOBAL", "LOAD_NAME"):
                    continue
                _g = _ins.argval
                if not isinstance(_g, str):
                    continue
                if (_g not in names and not hasattr(builtins, _g)):
                    missing.setdefault(_n, set()).add(_g)
        assert not missing, (
            f"the generated app calls names it does not define: {missing}. "
            f"A helper copied by _shared_stat_lines must bring its callees."
        )

    def test_the_scan_found_the_copied_helpers(self):
        """Guards the guard: an app with no copied functions proves nothing."""
        import inspect
        src = inspect.getsource(dr.ServerAppBuilder._shared_stat_lines)
        for name in ("_stata_if_to_pandas", "_resolve_seed", "_bootstrap_ci",
                     "_kpi_statistic"):
            assert name in src, f"{name} is no longer copied into the app"
