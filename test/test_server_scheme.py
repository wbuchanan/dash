"""Server mode ignored the scheme entirely.

``grep scheme`` over the generated app returned nothing: the builder never
read ``build_options['scheme']`` or ``['theme']``, and the app hardcoded
``color = '#1f77b4'`` for every plot. Measured — two apps whose specs
differed only in ``scheme`` were byte-identical apart from the base64 spec
blob, which the app decodes and then does not consult for this.

So a user who set a scheme, or simply had one set in their Stata session,
got Bokeh's default blue on a white plot region in server mode and their
scheme's colours in standalone. The same command, two colours.

The precedence — scheme(), then theme(), then a scheme named on a graph,
then c(scheme) — is resolved by one function now
(``_resolve_scheme_name``), so the two modes cannot disagree about which
scheme was asked for.
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

_DF = pd.DataFrame({
    "mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0],
})

_SEQ = itertools.count()


def _build_doc(tmp_path, build_options, plots=None):
    tag = next(_SEQ)
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    bo.update(build_options)
    plots = plots or [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}]
    spec = tmp_path / f"spec_{tag}.json"
    data = tmp_path / f"data_{tag}.json"
    app = tmp_path / f"app_{tag}.py"
    spec.write_text(json.dumps({
        "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                    "plots": plots, "options": {}}],
        "kpis": [], "build_options": bo}))
    data.write_text(json.dumps(make_data_json(_DF)))
    dr.ServerAppBuilder(str(spec), str(data)).build(str(app))
    mspec = importlib.util.spec_from_file_location(f"_sch_app_{tag}", str(app))
    mod = importlib.util.module_from_spec(mspec)
    mspec.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc


def _figures(doc):
    """Every figure reachable from a root.

    A GridPlot's `children' are (child, row, col) TUPLES, not models, so a
    walker that recurses straight into them never reaches a figure and the
    test reports an empty document instead of a wrong colour.
    """
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
            kids = getattr(m, attr, None)
            if kids is not None:
                walk(kids)

    for r in doc.roots:
        walk(r)
    return out


def _first_glyph_colour(doc):
    figs = _figures(doc)
    assert figs, "no figure in the served document"
    for r in figs[0].renderers:
        g = getattr(r, "glyph", None)
        for attr in ("fill_color", "line_color"):
            c = getattr(g, attr, None)
            if isinstance(c, str) and c.startswith("#"):
                return c.lower()
    raise AssertionError("no coloured glyph found")


class TestSchemeColour:
    def test_the_scheme_decides_the_glyph_colour(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s1mono"})
        expected = dr.SchemeParser("s1mono").default_color(0, "scatter")
        assert _first_glyph_colour(doc) == expected.lower()

    def test_two_schemes_give_two_colours(self, tmp_path):
        a = _first_glyph_colour(_build_doc(tmp_path, {"scheme": "s1mono"}))
        b = _first_glyph_colour(_build_doc(tmp_path, {"scheme": "economist"}))
        assert a != b, "the scheme changed nothing in server mode"

    def test_theme_is_honoured_when_no_scheme_is_given(self, tmp_path):
        doc = _build_doc(tmp_path, {"theme": "mono"})
        expected = dr.SchemeParser("s1mono").default_color(0, "scatter")
        assert _first_glyph_colour(doc) == expected.lower()

    def test_the_session_scheme_applies_when_nothing_else_is_asked(
            self, tmp_path):
        doc = _build_doc(tmp_path, {"session_scheme": "economist"})
        expected = dr.SchemeParser("economist").default_color(0, "scatter")
        assert _first_glyph_colour(doc) == expected.lower()

    def test_an_explicit_mcolor_still_wins_over_the_scheme(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "economist"},
                         plots=[{"type": "scatter", "yvar": "mpg",
                                 "xvar": "weight",
                                 "options": {"mcolor": "red"}}])
        assert _first_glyph_colour(doc) == "#ff0000"

    def test_successive_plots_walk_the_scheme_sequence(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"}, plots=[
            {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "scatter", "yvar": "weight", "xvar": "mpg", "options": {}},
        ])
        figs = _figures(doc)
        cols = []
        for r in figs[0].renderers:
            c = getattr(getattr(r, "glyph", None), "fill_color", None)
            if isinstance(c, str) and c.startswith("#"):
                cols.append(c.lower())
        assert len(cols) >= 2 and cols[0] != cols[1], (
            "every plot in a graph got the same colour"
        )


class TestSchemeChrome:
    def test_the_plot_region_takes_the_schemes_colour(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "economist"})
        sch = dr.SchemeParser("economist")
        assert _figures(doc)[0].background_fill_color == sch.plotregion_color

    def test_a_scheme_that_draws_no_grid_draws_no_grid(self, tmp_path):
        """s1mono draws neither grid; dash drew both regardless."""
        doc = _build_doc(tmp_path, {"scheme": "s1mono"})
        fig = _figures(doc)[0]
        assert all(g.grid_line_color is None for g in fig.xgrid)
        assert all(g.grid_line_color is None for g in fig.ygrid)

    def test_a_scheme_that_draws_a_grid_draws_it(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"})
        fig = _figures(doc)[0]
        sch = dr.SchemeParser("s2color")
        drawn = [g.grid_line_color for g in fig.xgrid] + \
                [g.grid_line_color for g in fig.ygrid]
        assert any(c is not None for c in drawn) == (
            sch.draw_major_hgrid or sch.draw_major_vgrid)


class TestPrecedenceIsSharedWithStandalone:
    @pytest.mark.parametrize("bo,expected", [
        ({"scheme": "s1mono", "theme": "economist",
          "session_scheme": "s2color"}, "s1mono"),
        ({"theme": "economist", "session_scheme": "s2color"}, "economist"),
        ({"session_scheme": "s1rcolor"}, "s1rcolor"),
        ({}, "s2color"),
    ])
    def test_one_function_answers_for_both_modes(self, bo, expected):
        spec = {"graphs": [], "build_options": bo}
        assert dr._resolve_scheme_name(spec) == expected


class TestSchemeMarkersAndDashes:
    """The scheme decides more than colour, and none of it reached here."""

    def test_the_marker_comes_from_the_scheme(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"})
        expected = dr.SchemeParser("s2color").default_symbol(0)
        markers = [r.glyph.marker for r in _figures(doc)[0].renderers
                   if hasattr(getattr(r, "glyph", None), "marker")]
        assert markers and markers[0] == expected

    def test_a_second_series_gets_the_second_marker(self, tmp_path):
        """Every scatter was a circle, however many shared the figure."""
        doc = _build_doc(tmp_path, {"scheme": "s2color"}, plots=[
            {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "scatter", "yvar": "weight", "xvar": "mpg", "options": {}},
        ])
        sch = dr.SchemeParser("s2color")
        markers = [r.glyph.marker for r in _figures(doc)[0].renderers
                   if hasattr(getattr(r, "glyph", None), "marker")]
        assert markers[:2] == [sch.default_symbol(0), sch.default_symbol(1)]

    def test_an_explicit_msymbol_still_wins(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"},
                         plots=[{"type": "scatter", "yvar": "mpg",
                                 "xvar": "weight",
                                 "options": {"msymbol": "square"}}])
        markers = [r.glyph.marker for r in _figures(doc)[0].renderers
                   if hasattr(getattr(r, "glyph", None), "marker")]
        assert markers and markers[0] == "square"

    def test_the_marker_size_comes_from_the_scheme(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"})
        expected = dr.SchemeParser("s2color").default_marker_size(0)
        sizes = [r.glyph.size for r in _figures(doc)[0].renderers
                 if hasattr(getattr(r, "glyph", None), "size")]
        assert sizes and sizes[0] == expected

    def test_a_line_takes_the_schemes_dash_pattern(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"},
                         plots=[{"type": "line", "yvar": "mpg",
                                 "xvar": "weight", "options": {}}])
        expected = dr.SchemeParser("s2color").default_line_pattern(0)
        dashes = [r.glyph.line_dash for r in _figures(doc)[0].renderers
                  if hasattr(getattr(r, "glyph", None), "line_dash")]
        assert dashes and list(dashes[0]) == list(expected)

    def test_an_explicit_lpattern_still_wins(self, tmp_path):
        doc = _build_doc(tmp_path, {"scheme": "s2color"},
                         plots=[{"type": "line", "yvar": "mpg",
                                 "xvar": "weight",
                                 "options": {"lpattern": "dash"}}])
        dashes = [r.glyph.line_dash for r in _figures(doc)[0].renderers
                  if hasattr(getattr(r, "glyph", None), "line_dash")]
        assert dashes and list(dashes[0]) == [8, 4]
