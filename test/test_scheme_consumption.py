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


def _render(plots=None, *, scheme="", theme="", layout="auto", kpis=None,
            title="", subtitle=""):
    plots = plots or _THREE_SERIES
    spec = make_spec(plots)
    spec["build_options"]["layout"] = layout
    if title:
        spec["build_options"]["title"] = title
    if subtitle:
        spec["build_options"]["subtitle"] = subtitle
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


def _scheme_attr_reads(attr):
    """Line numbers in dash_render.py that READ the scheme attribute *attr*.

    A read is a load of ``self.<attr>`` inside class SchemeParser, of
    ``scheme.<attr>`` or ``<anything>.scheme.<attr>`` (``self.scheme``,
    ``self.mapper.scheme``) elsewhere, or ``getattr(<same>, "<attr>")``.
    Assignments are stores and do not count, and neither does a Bokeh
    property that shares the name (``glyph.fill_alpha = ...``,
    ``fig.title.text_font_size = ...``): its base is no scheme.
    """
    import ast
    with open(os.path.join(_HERE, "..", "dash_render.py"),
              encoding="utf-8") as fh:
        tree = ast.parse(fh.read())

    def _is_scheme(node, in_parser):
        if isinstance(node, ast.Name):
            return node.id == "scheme" or (in_parser and node.id == "self")
        return isinstance(node, ast.Attribute) and node.attr == "scheme"

    reads = []

    def _walk(node, in_parser):
        for child in ast.iter_child_nodes(node):
            inside = in_parser
            if isinstance(child, ast.ClassDef):
                inside = child.name == "SchemeParser"
            if (isinstance(child, ast.Attribute) and child.attr == attr
                    and isinstance(child.ctx, ast.Load)
                    and _is_scheme(child.value, inside)):
                reads.append(child.lineno)
            if (isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == "getattr"
                    and len(child.args) >= 2
                    and isinstance(child.args[1], ast.Constant)
                    and child.args[1].value == attr
                    and _is_scheme(child.args[0], inside)):
                reads.append(child.lineno)
            _walk(child, inside)

    _walk(tree, False)
    return reads


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
        # Three lines, three patterns: s2mono declares p1lineplot solid,
        # p2lineplot dash and p3lineplot vshortdash, and dash drew
        # ['[]', '[8, 4]', '[3, 3]'] (measured 24sep2026).  The floors of
        # three lines and two patterns passed a third line that repeated
        # the second's dash.
        assert len(dashes) == 3, dashes
        assert len(set(dashes)) == 3, (
            f"every line used the same dash pattern {dashes}"
        )
        sp = SchemeParser("s2mono")
        assert dashes == [str(sp.default_line_pattern(i))
                          for i in range(3)], dashes

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
        assert len(colours) == 3, colours
        assert not all(c in ("#000000", "black") for c in colours), (
            f"every line is black; s1mono's color p#line was applied to a "
            f"plain line chart, where Stata reads color p#: {colours}"
        )
        # The colours Stata draws, from the docstring's measurement.  Not
        # all black passed a chart whose third line alone took p3line's
        # black (24sep2026).
        assert colours == ["#606060", "#a0a0a0", "#808080"], (
            f"s1mono's line chart is drawn {colours}; Stata draws "
            f"#606060 / #a0a0a0 / #808080 from color p#"
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
        """The mechanical check that stops this recurring.

        The dashboard carries a title, a subtitle and a KPI so that every
        selector css_block() emits has something it could match; a title
        selector on a dashboard with no title proves nothing either way.
        """
        out, dr = _render(scheme="economist", layout=layout,
                          title="A title", subtitle="A subtitle",
                          kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
                                 "title": "T", "fmt": "%9.1f"}])
        block = dr.scheme.css_block()
        selectors = set(re.findall(r"\.([A-Za-z][\w-]*)\s*\{", block))
        assert selectors, "css_block() emits no class selectors at all"
        # Two spellings, because the dashboard has two kinds of markup.
        # Page chrome is written into the document directly; a KPI card is
        # the text of a Bokeh Div, which reaches the file inside Bokeh's
        # JSON with its quotes escaped as \".  The browser applies the class
        # either way, so a check that saw only the first spelling reported a
        # live class as missing.
        emitted = set(re.findall(r'class="([^"]*)"', out))
        emitted |= set(re.findall(r'class=\\+"([^"\\]+)\\+"', out))
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
        colours = [str(g.fill_color) for g in _scatter_glyphs(dr)]
        econ = SchemeParser("economist")
        want = [econ.default_color(i, "scatter") for i in range(3)]
        # All three series, in order: an overlap of one colour passed a
        # graph whose scheme reached its first series only (24sep2026).
        # economist's first three colours are none of s2color's, the
        # build's scheme here, so this cannot pass by the build's.
        assert not set(want) & {SchemeParser("s2color").default_color(
            i, "scatter") for i in range(3)}
        assert colours == want, (
            f"graph-level scheme(economist) had no effect: drew {colours}, "
            f"economist would give {want}"
        )

    def test_an_unknown_theme_is_reported_not_silently_substituted(self):
        """A name that is neither a theme alias nor a scheme must be named.

        This used to be written against theme(dark), which was documented
        and absent from the map. The better fix was to make the documented
        name work -- dark is s1rcolor, Stata's own dark scheme, which dash
        ships -- so the case is now tested with a name that really is
        unknown. test_theme_aliases.py covers the six that resolve.
        """
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _render(theme="chartreuse")
        msgs = " ".join(str(w.message) for w in caught)
        assert "chartreuse" in msgs, (
            "an unknown theme fell back to s2color in silence"
        )

    def test_theme_dark_draws_statas_dark_scheme(self):
        """The name the help has always advertised now resolves."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _render(theme="dark")
        msgs = " ".join(str(w.message) for w in caught)
        assert "dark" not in msgs, (
            f"theme(dark) is still reported as unknown: {msgs}"
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
        # colorvar() with colordiscrete builds one categorical mapper
        # (measured 24sep2026).  This used to skip when none was built, so
        # losing the mapper -- the very thing under test -- read as a skip.
        assert len(mappers) == 1, (
            f"colorvar(length) colordiscrete built {len(mappers)} "
            f"categorical colour mappers, not one"
        )
        pal = list(mappers[0].palette)
        sch = list(dr.scheme.p_colors)
        # The palette is the scheme's p# cycle, one colour per factor in
        # order and wrapping at fifteen: the thirty lengths drew economist's
        # fifteen twice.  One shared colour passed a palette that took a
        # single colour from the scheme.
        n = len(mappers[0].factors)
        assert n == 30, n
        assert pal == [sch[i % 15] for i in range(n)], (
            f"the discrete palette {pal[:4]} ignores the scheme's "
            f"{sch[:4]}"
        )

    def test_a_schemes_area_intensity_and_minor_grid_reach_both_modes(
            self, tmp_path, monkeypatch):
        """`intensity area' and `color minor_grid' reach the figure, in both
        modes.  They were checked only by counting `.area_alpha' and
        `.minor_grid_color' in dash_render.py's text (below), because no
        shipped scheme can show either: every one says `intensity area
        full', which is Bokeh's own default, and none draws a minor grid.
        So a scheme written here says otherwise (WP-24)."""
        import warnings
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer, Plot
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wp24probe.scheme").write_text(
            "#include s2color\n"
            "intensity area inten40\n"
            "yesno draw_minor_hgrid yes\n"
            "color minor_grid red\n", encoding="utf-8")
        spec = make_spec([{"type": "area", "yvar": "mpg", "xvar": "weight",
                           "options": {}}])
        spec["build_options"]["scheme"] = "wp24probe"
        sp, dp, ap = (str(tmp_path / n) for n in ("s.json", "d.json", "app.py"))
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr = DashRenderer(sp, dp)
            dr.render()
            dash_render.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        attach = "if __name__ != '__main__':\n    make_document(curdoc())"
        assert attach in src
        ns = {"__name__": "_wp24_scheme_app"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(src.replace(attach, "pass"), "_wp24_scheme_app.py",
                         "exec"), ns)
            doc = Document()
            ns["make_document"](doc)
        served = [f for root in doc.roots for f in root.select({"type": Plot})]
        assert len(served) == 1, served
        for mode, fig in (("saved", dr.figures["g1"]), ("served", served[0])):
            areas = [r.glyph for r in fig.renderers
                     if isinstance(r, GlyphRenderer)
                     and type(r.glyph).__name__ == "VArea"]
            assert [a.fill_alpha for a in areas] == [0.4], (mode, areas)
            # draw_minor_hgrid is the HORIZONTAL axis's grid: the x grid.
            assert [str(g.minor_grid_line_color) for g in fig.xgrid] == \
                ["#ff0000"], (mode, [g.minor_grid_line_color for g in fig.xgrid])
            assert [g.minor_grid_line_color for g in fig.ygrid] == [None], mode

    @pytest.mark.parametrize("attr", [
        "fill_alpha", "bar_alpha", "area_alpha", "minor_grid_color",
        pytest.param("text_font_size", marks=pytest.mark.xfail(
            strict=True,
            reason="PRODUCT FINDING 24sep2026: SchemeParser.text_font_size "
                   "(`gsize text') is parsed and read by nothing -- no "
                   "scheme.text_font_size, self.scheme.text_font_size or "
                   "SchemeParser self.text_font_size load anywhere in "
                   "dash_render.py since the legend moved to key_label.  "
                   "The old `.text_font_size' count passed on Bokeh's "
                   "fig.title.text_font_size.  Strict: a consumer, or a "
                   "decision to retire the key, must remove this mark.")),
        "title_color", "heading_font_size",
    ])
    def test_the_key_is_read_somewhere(self, attr):
        """A parsed key with no consumer is a key that does nothing.

        Read from dash_render.py's syntax tree: a load of the SCHEME's
        attribute, not a count of the bare name.  area_alpha and
        minor_grid_color, which only this covered, are also run by the test
        above, since no shipped scheme can show either.

        text_font_size (`gsize text') is read by nothing: the legend takes
        key_label's size (_dash_scheme_chrome) and dash draws no text() box,
        so it is parsed and drawn from nowhere, as note_font_size is.  It
        passed the old count only because `.text_font_size' is also Bokeh's
        own name (fig.title.text_font_size, twice), which a count cannot
        tell apart (WP-24, 24sep2026).  It is a strict xfail, BUGS.md's open
        entry "The scheme's gsize text is parsed and read by nothing"."""
        sp = SchemeParser("s2color")
        # A rename used to skip here, silently dropping the attribute from
        # the check; the list names what SchemeParser must parse.
        assert hasattr(sp, attr), (
            f"SchemeParser no longer parses {attr}; update this list"
        )
        # The reads of the SCHEME's attribute, not of any attribute that
        # happens to share its name: `.fill_alpha' occurs in eleven
        # glyph.fill_alpha writes and `.text_font_size' in Bokeh's
        # fig.title.text_font_size, so the old count of the bare name
        # (>= 2, the definition included) could not fail for either
        # (measured 24sep2026).
        reads = _scheme_attr_reads(attr)
        assert reads, f"scheme.{attr} is parsed and never read"


# ======================================================================
# The lineplot / line distinction, and its fallback chain
# ======================================================================

class TestLinePatternFollowsStatasOwnChain:
    """``p#lineplot`` and ``p#line`` are different stubs, not a preference.

    Stata resolves a plain ``twoway line`` through
    ``linepattern p#lineplot -> plineplot -> p# -> p``
    (``style/seriesstyle-p#line.style`` then ``style/linestyle-p#line.style``,
    documented in ``scheme_line_plots.sthlp``), while ``linepattern p#line``
    belongs to ``style/linestyle-p#.style`` — the connecting line of
    ``twoway connected``.

    The first fix read ``p#line`` for a line plot, which made s2mono's three
    overlaid lines all solid.  The obvious repair — try ``p#lineplot``, fall
    back to ``p#line`` — is wrong in the other direction: s1mono and stmono1
    declare a varied ``p#line`` cycle and no ``lineplot`` key at all, and
    Stata draws their line plots solid.  Measured from Stata's own files:
    only ``scheme-s2mono.scheme`` and ``scheme-s2gmanual.scheme`` declare a
    ``lineplot`` directive; the three in ``scheme-s2color.scheme`` are
    commented-out examples.
    """

    @pytest.mark.parametrize("name", ["s2mono", "sj", "stsj", "stmono2"])
    def test_a_scheme_that_declares_lineplot_varies_the_pattern(self, name):
        sp = SchemeParser(name)
        got = [sp.default_line_pattern(i) for i in range(3)]
        assert got[0] == [], f"{name} p1 should be solid; got {got[0]}"
        assert got[1] and got[2], (
            f"{name} declares linepattern p2lineplot/p3lineplot; got {got}"
        )

    @pytest.mark.parametrize("name", ["s1mono", "stmono1"])
    def test_a_varied_p_hash_line_does_not_leak_into_a_line_plot(self, name):
        """The regression this class exists for."""
        sp = SchemeParser(name)
        assert sp.p_line_patterns[1], (
            f"{name} is expected to declare a varied p#line cycle; the test "
            f"proves nothing otherwise"
        )
        got = [sp.default_line_pattern(i) for i in range(3)]
        assert got == [[], [], []], (
            f"{name} declares no lineplot key, so Stata draws all three "
            f"lines solid; dash drew {got} by falling back to p#line"
        )

    @pytest.mark.parametrize("name", ["s2color", "stcolor", "economist"])
    def test_a_colour_scheme_draws_solid_lines(self, name):
        sp = SchemeParser(name)
        assert [sp.default_line_pattern(i) for i in range(3)] == [[], [], []]

    def test_a_declared_solid_is_not_mistaken_for_an_absent_key(self):
        """A declared ``solid`` is an empty dash list.

        Resolving the chain by truthiness therefore treats it as absent and
        falls through to a dashed entry further down — which is exactly what
        ``scheme-s2gmanual.scheme`` would trigger, declaring
        ``p#lineplot solid`` over a dashed ``p#line``.
        """
        sp = SchemeParser("s2color")
        sp._props = dict(sp._props)
        sp._props["linepattern p2lineplot"] = "solid"
        sp._props["linepattern p2"] = "dash"
        sp._init_properties()
        assert sp.default_line_pattern(1) == [], (
            "a declared solid fell through to the next key in the chain"
        )

    def test_the_chain_continues_past_an_absent_key(self):
        sp = SchemeParser("s2color")
        sp._props = dict(sp._props)
        sp._props.pop("linepattern p2lineplot", None)
        sp._props["linepattern p2"] = "dash"
        sp._init_properties()
        assert sp.default_line_pattern(1), (
            "an absent lineplot key must fall through to `linepattern p#'"
        )

    def test_a_connected_plot_keeps_reading_p_hash_line(self):
        """p#line is not dead — it is the connecting line's stub."""
        sp = SchemeParser("s1mono")
        assert sp.default_connect_pattern(1) == sp.p_line_patterns[1]
        assert sp.default_connect_pattern(1), (
            "s1mono declares linepattern p2line; a connected plot must use it"
        )

    def test_the_rendered_connecting_line_uses_the_connect_pattern(self):
        plots = [
            {"type": "connected", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            {"type": "connected", "yvar": "price", "xvar": "weight",
             "options": {}},
        ]
        _, dr = _render(plots, scheme="s1mono")
        dashes = []
        for fig in dr.figures.values():
            for r in fig.renderers:
                g = getattr(r, "glyph", None)
                if g is not None and type(g).__name__ == "Line":
                    dashes.append(list(g.line_dash))
        assert len(dashes) >= 2, dashes
        assert dashes[1] == SchemeParser("s1mono").default_connect_pattern(1), (
            f"the connecting line ignored p#line: {dashes}"
        )
