"""test_scheme_consumption.py — S11: the renderer must USE the translated schemes.

An earlier batch authored fourteen faithful translations. This section is about
the renderer consuming them.

Today only *hue* varies across series. Marker symbol, marker size, line pattern
and line width are identical for every plot, because the keys carrying them are
parsed and dropped — ``default_symbol()`` and ``default_line_pattern()`` exist
with no call sites at all.

And ``css_block()`` — one of only three consumers of the parsed scheme — is
inert twice over:

  * its selectors are ``.dash-title``, ``.dash-subtitle`` and ``.kpi-card``
    while the HTML emits ``db-title``, ``db-subtitle`` and inline-styled KPI
    divs, so all three match nothing;
  * under ``layout(bs)`` the block is embedded **inside another ``<style>``
    element**, because ``css_block()`` returns its own wrapper. Measured: the
    Bootstrap output contains six ``<style>`` tokens with one nested open at
    offset 1269202, so the ``body, .bk-root`` rule is discarded by CSS error
    recovery. ``layout(auto)`` has four, correctly balanced.

The last test class is the one that stops this recurring: every selector
``css_block()`` emits must match a class the HTML actually uses.
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

import dash_render
from dash_render import DashRenderer, SchemeParser

from conftest import make_spec, make_data_json


def _df(n=30):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
        "length": np.linspace(142.0, 233.0, n),
    })


_THREE_SERIES = [
    {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
    {"type": "scatter", "yvar": "price", "xvar": "weight", "options": {}},
    {"type": "scatter", "yvar": "length", "xvar": "weight", "options": {}},
]


def _render(plots=None, *, scheme="", theme="", layout="auto", kpis=None):
    plots = plots or _THREE_SERIES
    spec = make_spec(plots)
    spec["build_options"]["layout"] = layout
    if scheme:
        spec["build_options"]["scheme"] = scheme
    if theme:
        spec["build_options"]["theme"] = theme
    if kpis:
        spec["kpis"] = kpis
        spec["build_options"]["registry"] = "k1 g1"
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df()), f)
    dr = DashRenderer(sp, dp, op)
    out = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return out, dr


def _scatter_glyphs(dr):
    out = []
    for fig in dr.figures.values():
        for r in fig.renderers:
            g = getattr(r, "glyph", None)
            if g is not None and type(g).__name__ == "Scatter":
                out.append(g)
    return out


# ======================================================================
# The per-series style cycle
# ======================================================================

class TestPerSeriesStyleCycle:
    """Only hue varies today. twoway varies four things."""

    def test_three_overlaid_series_get_three_colours(self):
        """The control — this is the one thing that already works."""
        _, dr = _render(scheme="s2color")
        colours = {str(g.fill_color) for g in _scatter_glyphs(dr)}
        assert len(colours) >= 3, colours

    def test_three_overlaid_series_get_different_symbols(self):
        _, dr = _render(scheme="s1mono")
        markers = [str(g.marker) for g in _scatter_glyphs(dr)]
        assert len(markers) >= 3, markers
        assert len(set(markers)) >= 2, (
            f"every series drew the same marker {markers}; the scheme's "
            f"symbol cycle is parsed and discarded"
        )

    def test_the_symbols_come_from_the_scheme(self):
        sp = SchemeParser("s1mono")
        want = [sp.default_symbol(i) for i in range(3)]
        _, dr = _render(scheme="s1mono")
        got = [str(g.marker) for g in _scatter_glyphs(dr)]
        assert got[:3] == want[:3], (got, want)

    def test_default_symbol_has_a_caller(self):
        """It existed only to be unit-tested."""
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count("default_symbol(") >= 2, (
            "default_symbol() is defined and never called"
        )

    def test_default_line_pattern_has_a_caller(self):
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count("default_line_pattern(") >= 2, (
            "default_line_pattern() is defined and never called"
        )

    def test_three_overlaid_lines_get_different_dash_patterns(self):
        """Measured in Stata: a LINE chart takes its pattern from
        ``linepattern p#lineplot``, not from ``linepattern p#line``.

        ``p#line`` governs only the connecting line of ``twoway connected``.
        s2mono and sj declare ``p#lineplot`` and do render dashed; s1mono does
        not declare it and Stata draws all three lines solid. No translated
        scheme in ``schemes/`` carries the key at all, so the cycle cannot
        vary until the translation is completed.
        """
        plots = [
            {"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "line", "yvar": "price", "xvar": "weight", "options": {}},
            {"type": "line", "yvar": "length", "xvar": "weight",
             "options": {}},
        ]
        _, dr = _render(plots, scheme="s2mono")
        dashes = []
        for fig in dr.figures.values():
            for r in fig.renderers:
                g = getattr(r, "glyph", None)
                if g is not None and type(g).__name__ == "Line":
                    dashes.append(str(g.line_dash))
        assert len(dashes) >= 3, dashes
        assert len(set(dashes)) >= 2, (
            f"every line used the same dash pattern {dashes}"
        )

    def test_a_colour_scheme_draws_every_series_with_a_circle(self):
        """Measured: stcolor, s2color and economist all use circle for p1-p3.

        Only the mono schemes vary the symbol. A fix that made every scheme
        cycle through symbols would be WRONG.
        """
        for name in ("stcolor", "s2color", "economist"):
            _, dr = _render(scheme=name)
            markers = {str(g.marker) for g in _scatter_glyphs(dr)}
            assert markers == {"circle"}, (
                f"{name} should draw circles for all three series; got "
                f"{markers}"
            )

    def test_a_line_chart_takes_its_colour_from_p_hash_not_p_hash_line(self):
        """s1mono declares color p#line black; Stata draws #606060/#A0A0A0/
        #808080 for a plain line chart, because p#line is for connected."""
        plots = [
            {"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "line", "yvar": "price", "xvar": "weight", "options": {}},
            {"type": "line", "yvar": "length", "xvar": "weight",
             "options": {}},
        ]
        _, dr = _render(plots, scheme="s1mono")
        colours = []
        for fig in dr.figures.values():
            for r in fig.renderers:
                g = getattr(r, "glyph", None)
                if g is not None and type(g).__name__ == "Line":
                    colours.append(str(g.line_color).lower())
        assert len(colours) >= 3
        assert not all(c in ("#000000", "black") for c in colours), (
            f"every line is black; s1mono's color p#line was applied to a "
            f"plain line chart, where Stata reads color p#: {colours}"
        )

    def test_marker_size_comes_from_the_scheme_not_a_literal(self):
        a, dra = _render(scheme="s2color")
        b, drb = _render(scheme="economist")
        sa = {float(g.size) for g in _scatter_glyphs(dra)}
        sb = {float(g.size) for g in _scatter_glyphs(drb)}
        assert sa and sb
        assert sa != sb or len(sa) > 1, (
            f"marker size is the same literal under both schemes: {sa}"
        )

    @pytest.mark.parametrize("opt,key", [
        ({"msymbol": "diamond"}, "marker"),
        ({"msize": "12"}, "size"),
    ])
    def test_an_explicit_option_beats_the_scheme(self, opt, key):
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": opt}]
        _, dr = _render(plots, scheme="s1mono")
        g = _scatter_glyphs(dr)[0]
        if key == "marker":
            assert str(g.marker) == "diamond"
        else:
            assert float(g.size) == pytest.approx(12.0)


# ======================================================================
# The dead CSS
# ======================================================================

class TestSchemeCssActuallyApplies:

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_the_style_elements_are_balanced_and_not_nested(self, layout):
        """css_block() returns its own <style>; the Bootstrap head wraps it
        in another one, which invalidates the first rule."""
        out, _ = _render(scheme="economist", layout=layout)
        depth = 0
        nested = 0
        for m in re.finditer(r"</?style>", out):
            if m.group() == "<style>":
                depth += 1
                if depth > 1:
                    nested += 1
            else:
                depth -= 1
        assert depth == 0, f"layout({layout}): unbalanced <style> elements"
        assert nested == 0, (
            f"layout({layout}): a <style> element is nested inside another, "
            f"so CSS error recovery discards the rule that follows it"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_every_selector_matches_a_class_the_html_emits(self, layout):
        """The mechanical check that stops this recurring."""
        out, dr = _render(scheme="economist", layout=layout,
                          kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
                                 "title": "T", "fmt": "%9.1f"}])
        block = dr.scheme.css_block()
        selectors = set(re.findall(r"\.([A-Za-z][\w-]*)\s*\{", block))
        assert selectors, "css_block() emits no class selectors at all"
        emitted = set(re.findall(r'class="([^"]*)"', out))
        classes = {c for group in emitted for c in group.split()}
        missing = sorted(s for s in selectors if s not in classes)
        assert not missing, (
            f"layout({layout}): css_block() styles {missing}, which appear "
            f"nowhere in the emitted HTML"
        )

    def test_the_scheme_background_reaches_the_document(self):
        out, dr = _render(scheme="economist", layout="bs")
        bg = dr.scheme.background_color
        assert bg and bg.startswith("#")
        assert bg in out, (
            f"the scheme background {bg} appears nowhere in the output"
        )


# ======================================================================
# Scheme selection
# ======================================================================

class TestSchemeSelection:

    def test_a_build_level_scheme_is_honoured(self):
        _, dr = _render(scheme="economist")
        assert dr.scheme.name == "economist", dr.scheme.name

    def test_a_graph_level_scheme_is_honoured(self):
        """Parsed, escaped into graph_options, and never read."""
        spec = make_spec(_THREE_SERIES)
        spec["graphs"][0]["graph_options"]["scheme"] = "economist"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        colours = {str(g.fill_color) for g in _scatter_glyphs(dr)}
        econ = SchemeParser("economist")
        want = {econ.default_color(i, "scatter") for i in range(3)}
        assert colours & want, (
            f"graph-level scheme(economist) had no effect: drew {colours}, "
            f"economist would give {want}"
        )

    def test_an_unknown_theme_is_reported_not_silently_substituted(self):
        """theme(dark) is documented and absent from the map."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _render(theme="dark")
        msgs = " ".join(str(w.message) for w in caught)
        assert "dark" in msgs, (
            "theme(dark) fell back to s2color in silence; it is documented "
            "in dash.sthlp and absent from the theme map"
        )

    def test_the_report_names_the_supported_set(self):
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _render(scheme="notarealscheme")
        msgs = " ".join(str(w.message) for w in caught)
        assert "s2color" in msgs or "economist" in msgs, (
            f"the message does not name any supported scheme: {msgs}"
        )

    def test_the_session_scheme_is_the_default(self):
        """c(scheme) — dash.ado looks up only c(level), c(sysdir_plus), c(os)."""
        spec = make_spec(_THREE_SERIES)
        spec["build_options"]["scheme"] = ""
        spec["build_options"]["theme"] = ""
        spec["build_options"]["session_scheme"] = "economist"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert dr.scheme.name == "economist", (
            f"c(scheme) was ignored; used {dr.scheme.name}"
        )

    def test_an_explicit_scheme_beats_the_session_scheme(self):
        spec = make_spec(_THREE_SERIES)
        spec["build_options"]["scheme"] = "s1mono"
        spec["build_options"]["session_scheme"] = "economist"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert dr.scheme.name == "s1mono"


# ======================================================================
# The remaining discarded keys
# ======================================================================

class TestNoParsedKeyIsDiscarded:

    def test_legend_styling_comes_from_the_scheme(self):
        """legend_bg_color and legend_border_color had zero consumers."""
        plots = [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}},
        ]
        _, dr = _render(plots, scheme="economist")
        legends = [l for fig in dr.figures.values() for l in fig.legend]
        assert legends, "no legend was drawn on a two-key figure"
        bg = dr.scheme.legend_bg_color
        assert bg, "the scheme records no legend background"
        assert any(str(l.background_fill_color) == bg for l in legends), (
            f"the legend background is "
            f"{[str(l.background_fill_color) for l in legends]}, not the "
            f"scheme's {bg}"
        )

    def test_the_discrete_colorvar_palette_comes_from_the_scheme(self):
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {"colorvar": "length", "colordiscrete": "yes"}}]
        _, dr = _render(plots, scheme="economist")
        from bokeh.models import CategoricalColorMapper
        mappers = [m for fig in dr.figures.values()
                   for m in fig.select({"type": CategoricalColorMapper})]
        if not mappers:
            pytest.skip("no categorical mapper was built")
        pal = set(mappers[0].palette)
        sch = set(dr.scheme.p_colors)
        assert pal & sch, (
            f"the discrete palette {sorted(pal)[:4]} ignores the scheme's "
            f"{sorted(sch)[:4]}"
        )

    @pytest.mark.parametrize("attr", [
        "fill_alpha", "bar_alpha", "area_alpha", "minor_grid_color",
        "text_font_size", "title_color", "heading_font_size",
    ])
    def test_the_key_is_read_somewhere(self, attr):
        """A parsed key with no consumer is a key that does nothing."""
        sp = SchemeParser("s2color")
        if not hasattr(sp, attr):
            pytest.skip(f"SchemeParser does not parse {attr}")
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count(f".{attr}") >= 2, (
            f"scheme.{attr} is parsed and never read"
        )
