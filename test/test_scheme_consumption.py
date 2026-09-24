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


# ======================================================================
# Directives only a user's scheme file carries (TR-26.7)
# ======================================================================

class TestDirectivesOnlyAUserSchemeCarries:
    """Four SchemeParser branches that no shipped scheme reaches.

    dash's twenty shipped schemes are flattened translations: every
    #include chain and every p#stub fallback is resolved into explicit keys
    when scripts/extract_scheme_truth.py writes them.  So none of them
    carries

      1. `color plineplot', the line-plot colour of every p# (Stata's
         scheme-s2mono.scheme: `color plineplot black');
      2. `linepattern p1' .. `linepattern p15', the third step of the
         line-plot pattern chain p#lineplot -> plineplot -> p# -> p;
      3. a bare `graphsize N' (scheme-s2color.scheme line 31: `graphsize 5');
      4. `#include <scheme>'.

    A user's scheme may carry any of them -- dash reads a .scheme file from
    the working directory, and Stata's own files carry three of the four
    kinds -- so each test here writes a scheme file into a temporary working
    directory and parses it by name, as dash.sthlp tells a user to.

    The expected values are Stata's, measured 24sep2026 in console StataNow
    19.5 (`stata-mp -b', `graph export' to SVG, graph sizes also read with
    gs_graphinfo): the same scheme text saved as scheme-<name>.scheme in
    Stata's working directory and drawn by twoway on eleven points, as line
    plots unless a test names another plot type.
    An `#include s2color' there is Stata's own scheme-s2color.scheme; here it
    is dash's translation of it.  Where dash disagrees, the test asserts
    Stata's value and is a strict xfail (raises=AssertionError, so only the
    comparison counts; its controls fail through pytest.fail, which the mark
    does not absorb) whose reason names the BUGS.md entry drafted for it.

    The last two tests are not about the four branches.  The measurements
    for (2) and (4) found them: after an `#include s2color', a user's
    `linepattern p#' or `color p#' reaches a line plot in dash, as in
    Stata, but not a marker, a bar or a connected plot's connecting line.
    """

    # The fifteen patterns of scheme-w26lp.scheme, p1 to p15.  None is solid
    # or blank; each has its own linepattern-<name>.style in Stata's style
    # library and its own OptionTranslator._LPATTERN_MAP entry.
    _PATTERNS = ("dash", "dot", "dash_dot", "shortdash", "shortdash_dot",
                 "longdash", "longdash_dot", "vshortdash", "tight_dot",
                 "dash_3dot", "dash_dot_dot", "longdash_3dot",
                 "longdash_dot_dot", "longdash_shortdash",
                 "shortdash_dot_dot")

    # s2color's p1, p2 and p3 as Stata strokes three overlaid lines under
    # scheme-w26inc.scheme, whose only line is `#include s2color'.
    _S2_P123 = ["#1a476f", "#90353b", "#55752f"]

    # y1 .. y15 = x + i on eleven points, as in the do-file.
    _DF = pd.DataFrame(dict(
        [("x", np.arange(11.0))]
        + [("y%d" % i, np.arange(11.0) + i) for i in range(1, 16)]))

    _BUG_BARE_GRAPHSIZE = (
        "BUGS.md (open, recorded 24sep2026 by TR-26.7): \"A bare graphsize "
        "stands in for a missing graphsize x or y, where Stata reads it for "
        "no graph's size\"")
    _BUG_INCLUDE_ORDER = (
        "BUGS.md (open, recorded 24sep2026 by TR-26.7): \"A directive above "
        "an #include survives it, where Stata lets the included scheme "
        "overwrite it\"")
    _BUG_INCLUDE_NOWHERE = (
        "BUGS.md (open, recorded 24sep2026 by TR-26.7): \"An #include that "
        "resolves nowhere is skipped in silence, where Stata draws s2color "
        "in its place and says so\"")
    _BUG_STUB_SHADOW = (
        "BUGS.md (open, recorded 24sep2026 by TR-26.7): \"A user's color p# "
        "or linepattern p# after #include s2color does not reach markers, "
        "bars or connected lines\"")

    @pytest.fixture
    def wd(self, tmp_path, monkeypatch):
        """A fresh working directory, where dash reads a user's scheme."""
        monkeypatch.chdir(tmp_path)
        return tmp_path

    @staticmethod
    def _parse(wd, name, text):
        """Write *text* as <name>.scheme in *wd* and parse it by name.

        Returns the parser and the messages of the warnings it raised."""
        import warnings
        (wd / (name + ".scheme")).write_text(text, encoding="utf-8")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sch = SchemeParser(name)
        return sch, [str(w.message) for w in caught]

    def _lines(self, wd, scheme, n, options=None):
        """A saved one-graph dashboard of n line plots, y1 .. yn on x,
        under the build scheme *scheme*: the figure and its Line glyphs in
        plot order.  *options* maps a plot's index to its options."""
        import warnings
        plots = [{"type": "line", "yvar": "y%d" % (i + 1), "xvar": "x",
                  "options": dict((options or {}).get(i, {}))}
                 for i in range(n)]
        spec = make_spec(plots)
        spec["build_options"]["scheme"] = scheme
        out = wd / ("render%d" % len(list(wd.glob("render*"))))
        out.mkdir()
        sp, dp = str(out / "s.json"), str(out / "d.json")
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(self._DF), f)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr = DashRenderer(sp, dp)
            dr.render()
        # A scheme that failed to resolve falls back to s2color, which is
        # what several of the expected values are.
        if dr.scheme.name != scheme or dr.scheme.is_fallback:
            pytest.fail("the build drew %r, not the scheme %r"
                        % (dr.scheme.name, scheme))
        fig = dr.figures["g1"]
        return fig, [r.glyph for r in fig.renderers
                     if type(getattr(r, "glyph", None)).__name__ == "Line"]

    @staticmethod
    def _base_without_graphsize(wd):
        """w26base.scheme: dash's shipped s2color with its graphsize lines
        taken out, as Stata's scheme-s2color.scheme was for the measurement.

        A base is needed because Stata cannot draw under a scheme with no
        #include at all: `graphsize 3' alone, or `color p1 red' alone,
        makes twoway fail with "option seriesid() not allowed", r(198)."""
        with open(os.path.join(_HERE, "..", "schemes", "s2color.scheme"),
                  encoding="utf-8") as fh:
            kept = [ln for ln in fh.read().splitlines()
                    if ln.split()[:1] != ["graphsize"]]
        (wd / "w26base.scheme").write_text("\n".join(kept) + "\n",
                                           encoding="utf-8")

    # -- 1. color plineplot --------------------------------------------

    def test_color_plineplot_colours_every_line_plot(self, wd):
        """`color plineplot' is the line-plot colour of each p# that has no
        `color p#lineplot' of its own: style/linestyle-p#line.style sets
        the colour from `scheme p#lineplot', which scheme.class resolves
        through p#lineplot -> plineplot -> p# -> p.

        Measured 24sep2026, `twoway (line y1 x) (line y2 x) (line y3 x)':
        under w26plp (`#include s2color', `color plineplot red') the three
        strokes are #FF0000 / #FF0000 / #FF0000; with `color p2lineplot
        blue' added (w26plp2), #FF0000 / #0000FF / #FF0000; under w26inc
        (`#include s2color' alone), #1A476F / #90353B / #55752F.  Stata's
        red and blue are 255 0 0 and 0 0 255, #ff0000 and #0000ff to
        translate_mcolor."""
        plp, _ = self._parse(wd, "w26plp",
                             "#include s2color\ncolor plineplot red\n")
        plp2, _ = self._parse(wd, "w26plp2", "#include s2color\n"
                              "color plineplot red\ncolor p2lineplot blue\n")
        inc, _ = self._parse(wd, "w26inc", "#include s2color\n")
        want = {"w26inc": self._S2_P123,
                "w26plp": ["#ff0000", "#ff0000", "#ff0000"],
                "w26plp2": ["#ff0000", "#0000ff", "#ff0000"]}
        got = {"w26inc": inc.p_lineplot_colors[:3],
               "w26plp": plp.p_lineplot_colors[:3],
               "w26plp2": plp2.p_lineplot_colors[:3]}
        assert got == want
        # ... and what a saved dashboard strokes.
        for name, colours in want.items():
            _fig, lines = self._lines(wd, name, 3)
            assert [str(g.line_color).lower() for g in lines] == colours, (
                name)

    # -- 2. linepattern p1 .. p15 -----------------------------------------

    def test_linepattern_p_hash_patterns_a_line_plot(self, wd):
        """`linepattern p#' is the third step of the line-plot pattern chain
        (linestyle-p#line.style: `set pattern scheme p#lineplot'), and
        s2color declares neither p#lineplot nor plineplot, so p1 .. p15
        decide.

        Measured 24sep2026: under w26lp (`#include s2color', then
        `linepattern p1 dash' .. `linepattern p15 shortdash_dot_dot', the
        fifteen names of _PATTERNS), a twoway of fifteen lines draws each
        line exactly as it draws that line given `lpattern(<its name>)'
        under the same scheme: every dash segment of all fifteen series is
        the same <line> element, coordinate for coordinate, in the two SVGs,
        and the dash and gap lengths, in units of 0.04in (28.8 of the SVG's
        720 per inch), are the linepattern-<name>.style values (dash 2 1,
        dot .1 .7, ...).  The fifteen are pairwise distinct and none is
        solid; under w26inc all fifteen are solid paths.

        So the comparison is by pattern identity: dash must draw line i as
        it draws lpattern(<name i>), translate_lpattern's list.  The lists
        are dash's own renderings of the names (_LPATTERN_MAP: dash [8, 4]
        where Stata's style is 2 1), not Stata's lengths."""
        text = "#include s2color\n" + "".join(
            "linepattern p%d %s\n" % (i + 1, p)
            for i, p in enumerate(self._PATTERNS))
        lp, _ = self._parse(wd, "w26lp", text)
        inc, _ = self._parse(wd, "w26inc", "#include s2color\n")
        named = [dash_render.OptionTranslator.translate_lpattern(p)
                 for p in self._PATTERNS]
        assert all(named) and len({str(d) for d in named}) == 15, named
        assert [inc.default_line_pattern(i) for i in range(15)] == [[]] * 15
        assert [lp.default_line_pattern(i) for i in range(15)] == named
        # The glyphs: the scheme's fifteen lines, the same fifteen given
        # lpattern(<name>) explicitly (the twin of the Stata comparison),
        # and the fifteen under the include alone.
        _f, by_scheme = self._lines(wd, "w26lp", 15)
        _f, by_option = self._lines(
            wd, "w26lp", 15,
            {i: {"lpattern": p} for i, p in enumerate(self._PATTERNS)})
        _f, plain = self._lines(wd, "w26inc", 15)
        assert [list(g.line_dash) for g in by_scheme] == named
        assert [list(g.line_dash) for g in by_option] == named
        assert [list(g.line_dash) for g in plain] == [[]] * 15

    # -- 3. a bare graphsize ------------------------------------------------

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason=_BUG_BARE_GRAPHSIZE)
    def test_a_bare_graphsize_sizes_nothing(self, wd):
        """Stata reads a bare `graphsize N' for no graph's size.

        setscheme stores a two-token line as the class default,
        `.graphsize._default', and scheme.class's `style' program returns
        `_default' only for an EMPTY id, while every graph family asks for
        `scheme x' and `scheme y' (style/graphstyle-default.style: `set
        declared_xsize scheme x').  Measured 24sep2026 on w26base, Stata's
        scheme-s2color.scheme without its three graphsize lines, which draws
        6 x 3in given `graphsize x 6' and `graphsize y 3':

          + `graphsize 3'                  twoway r(198), nothing drawn
          + `graphsize 3', `graphsize x 6'  r(198)
          + `graphsize 3', `graphsize y 3'  r(198)
          s2color's own `graphsize 5' kept, x and y removed: r(198)

        as does w26base with no graphsize at all, or with x or y alone;
        given xsize(6) ysize(3) as options, each of these schemes draws 6 x
        3in.  Under `set trace on', scheme.class's `style' program finds no
        `graphsize x', and graph_g.drawgraph reads `local xsize = .' and
        `local ysize = .' and runs `gdi init . . 234 242 243 , live', which
        is the r(198).  dash reads the bare key as the default of both, so
        it sizes the three (3.0, 3.0), (6.0, 3.0) and (3.0, 3.0).  Stata's
        missing declared size is None in dash's terms -- what graphsize_x
        holds when a scheme declares no size, as w26base alone shows below.
        The cases where dash and Stata agree are
        test_a_bare_graphsize_beside_an_explicit_pair_changes_nothing."""
        self._base_without_graphsize(wd)
        base, _ = self._parse(wd, "w26c0", "#include w26base\n")
        if (base.graphsize_x, base.graphsize_y) != (None, None):
            pytest.fail("control: w26base still declares a size, %r"
                        % ((base.graphsize_x, base.graphsize_y),))
        got = {}
        for name, text in (("w26c1", "graphsize 3\n"),
                           ("w26c3", "graphsize 3\ngraphsize x 6\n"),
                           ("w26d3", "graphsize 3\ngraphsize y 3\n")):
            sch, _ = self._parse(wd, name, "#include w26base\n" + text)
            got[name] = (sch.graphsize_x, sch.graphsize_y)
        assert got == {"w26c1": (None, None), "w26c3": (6.0, None),
                       "w26d3": (None, 3.0)}

    def test_a_bare_graphsize_beside_an_explicit_pair_changes_nothing(
            self, wd):
        """Where x and y are both declared, a bare key changes nothing, in
        Stata and in dash.  Measured 24sep2026: `#include s2color' then
        `graphsize 3' (w26gs2) draws 5.5 x 4in, s2color's own size
        (gs_graphinfo xsize 5.5, ysize 4; SVG width="5.500in"
        height="4.000in"); `graphsize 2', `graphsize x 6', `graphsize y 3'
        on w26base (w26d4) draws 6 x 3in.  A saved dashboard takes each
        pair's proportions as its figure's aspect_ratio: 5.5 / 4 and 6 / 3."""
        self._base_without_graphsize(wd)
        s2, _ = self._parse(wd, "w26gs2", "#include s2color\ngraphsize 3\n")
        pair, _ = self._parse(wd, "w26d4", "#include w26base\ngraphsize 2\n"
                              "graphsize x 6\ngraphsize y 3\n")
        assert (s2.graphsize_x, s2.graphsize_y) == (5.5, 4.0)
        assert (pair.graphsize_x, pair.graphsize_y) == (6.0, 3.0)
        fig_s2, _l = self._lines(wd, "w26gs2", 1)
        fig_pair, _l = self._lines(wd, "w26d4", 1)
        assert fig_s2.aspect_ratio == pytest.approx(5.5 / 4.0)
        assert fig_pair.aspect_ratio == pytest.approx(6.0 / 3.0)

    # -- 4. #include ---------------------------------------------------------

    def test_an_include_supplies_what_the_file_leaves_unsaid(self, wd):
        """Measured 24sep2026: under w26inc, whose only line is `#include
        s2color', Stata draws s2color as it is -- strokes #1A476F / #90353B
        / #55752F, background #EAF2F3, 5.5 x 4in -- and under a scheme with
        no #include it draws nothing (`color p1 red' alone: "option
        seriesid() not allowed", r(198)).  dash's #include resolves to its
        own translation of s2color, which is generated from Stata's file;
        the control is the same kind of file without the #include."""
        inc, _ = self._parse(wd, "w26inc", "#include s2color\n")
        alone, _ = self._parse(wd, "w26gs0", "color p1 red\n")
        assert inc.p_lineplot_colors[:3] == self._S2_P123
        assert inc.background_color == "#eaf2f3"
        assert (inc.graphsize_x, inc.graphsize_y) == (5.5, 4.0)
        assert alone.background_color != "#eaf2f3"
        assert alone.p_lineplot_colors[1:3] != self._S2_P123[1:3]
        assert (alone.graphsize_x, alone.graphsize_y) == (None, None)
        fig, lines = self._lines(wd, "w26inc", 3)
        assert [str(g.line_color).lower() for g in lines] == self._S2_P123
        assert str(fig.border_fill_color).lower() == "#eaf2f3"
        assert fig.aspect_ratio == pytest.approx(5.5 / 4.0)

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason=_BUG_INCLUDE_ORDER)
    def test_an_include_overwrites_the_directives_above_it(self, wd):
        """Stata splices an #include in where it stands: setscheme reads the
        file line by line, runs `.setscheme , scheme(<name>)' at the
        #include, and a later assignment to a key overwrites an earlier
        one.  So a directive ABOVE the #include loses to the included
        scheme's own.  Measured 24sep2026: `color p1 red' then `#include
        s2color' (w26ord) strokes line 1 #1A476F, s2color's navy, and line
        2 #90353B; the two lines the other way round (w26ord2) stroke
        #FF0000 and #90353B.  _parse_file lets the parent fill only the keys
        the child has not set, so dash keeps red either way.  (Stata's
        scheme_files help tells a user to put the #include "before any
        scheme-file entries".)"""
        after, _ = self._parse(wd, "w26ord2",
                               "#include s2color\ncolor p1 red\n")
        if after.p_lineplot_colors[:2] != ["#ff0000", "#90353b"]:
            pytest.fail("control: `#include s2color' then `color p1 red' "
                        "gives %r" % (after.p_lineplot_colors[:2],))
        before, _ = self._parse(wd, "w26ord",
                                "color p1 red\n#include s2color\n")
        assert before.p_lineplot_colors[:2] == ["#1a476f", "#90353b"]

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason=_BUG_INCLUDE_NOWHERE)
    def test_an_include_that_resolves_nowhere_stands_s2color_in(self, wd):
        """Stata does not skip an #include it cannot find: setscheme runs
        `.setscheme , scheme(s2color)' in its place and says so.  Measured
        24sep2026 in a session whose c(scheme) is stcolor: `#include
        w26nosuch' then `color p1 red' (w26bad) prints "(note: scheme
        w26nosuch not found, using s2color)", returns rc 0, and draws
        s2color with p1 red -- strokes #FF0000 / #90353B / #55752F,
        background #EAF2F3, 5.5 x 4in.  dash skips the line in silence, as
        dash.sthlp says it does (TestWhatAnIncludeResolvesTo in
        test_help_claims_8.py holds it to that): p2 and p3 fall to the
        parser's #000000, the background to #d9e8f0, the size to none, and
        nothing is said.  The control is the same file with `#include
        s2color' written out."""
        ref, _ = self._parse(wd, "w26ref",
                             "#include s2color\ncolor p1 red\n")
        want = (["#ff0000", "#90353b", "#55752f"], "#eaf2f3", (5.5, 4.0))
        if (ref.p_lineplot_colors[:3], ref.background_color,
                (ref.graphsize_x, ref.graphsize_y)) != want:
            pytest.fail("control: `#include s2color' then `color p1 red' "
                        "is not s2color with a red p1")
        sch, said = self._parse(wd, "w26bad",
                                "#include w26nosuch\ncolor p1 red\n")
        assert (sch.p_lineplot_colors[:3], sch.background_color,
                (sch.graphsize_x, sch.graphsize_y)) == want
        assert any("w26nosuch" in m and "s2color" in m for m in said), said

    # -- found on the way: what a child's p# reaches through an #include --

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason=_BUG_STUB_SHADOW)
    def test_a_connected_line_follows_the_p_hash_line_chain_to_p_hash(
            self, wd):
        """A connected plot's connecting line is styled by
        style/linestyle-p#.style, `set pattern scheme p#line', and
        scheme.class resolves `p#line' through p#line -> pline -> p# -> p as
        it does every p#stub.  Stata's scheme-s2color.scheme declares no
        `linepattern p#line', so under w26lp the chain reaches the child's
        p#.  Measured 24sep2026: `twoway (connected y1 x) (connected y2 x)
        (connected y3 x)' under w26lp draws the three connecting lines
        exactly as `lpattern(dash)', `lpattern(dot)' and `lpattern(dash_dot)'
        draw them (every segment the same), and solid under w26inc.

        dash draws them solid, for two reasons, and fixing either alone does
        not change that (measured in a scratch copy): the shipped
        schemes/s2color.scheme declares `linepattern p1line solid' ..
        `p15line solid', the extractor's resolution of Stata's chain, so
        the parent's p#line stops the chain before the child's p#; and
        SchemeParser.p_line_patterns reads `linepattern p#line' alone,
        with no chain after it."""
        text = "#include s2color\n" + "".join(
            "linepattern p%d %s\n" % (i + 1, p)
            for i, p in enumerate(self._PATTERNS))
        lp, _ = self._parse(wd, "w26lp", text)
        inc, _ = self._parse(wd, "w26inc", "#include s2color\n")
        if [inc.default_connect_pattern(i) for i in range(3)] != [[]] * 3:
            pytest.fail("control: s2color's connecting lines are not solid")
        assert [lp.default_connect_pattern(i) for i in range(3)] == [
            dash_render.OptionTranslator.translate_lpattern(p)
            for p in self._PATTERNS[:3]]

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason=_BUG_STUB_SHADOW)
    def test_a_child_colour_p_hash_reaches_markers_bars_and_connected_lines(
            self, wd):
        """Stata's scheme-s2color.scheme declares `color p1' .. `color p15'
        and no `color p#mark', `color p#bar' or `color p#line', so a child's
        `color p1' reaches every p1 stub through p#stub -> pstub -> p# -> p.
        Measured 24sep2026 under w26ord2 (`#include s2color', then `color p1
        red'), two series each:

          twoway scatter    series 1 markers fill and outline #FF0000
          twoway connected  series 1 connecting line and markers #FF0000
          twoway bar        series 1 outline #FF0000, fill #FF3333
          twoway line       series 1 #FF0000

        and series 2 in s2color's #90353B (bar fill #A65D62).  The bar fill
        is the outline colour at s2color's bar intensity, 80 per cent toward
        white (0.8 * c + 0.2 * 255 per channel: red gives #FF3333, navy
        #486C8C), so default_color's value for a bar is the outline's.
        Under w26inc every series-1 element is #1A476F (bar fill #486C8C).

        dash gives the line plot red, as Stata does, but the markers, the
        connecting line and the bars navy: the shipped schemes/s2color.scheme
        declares `color p#mark', `color p#bar' and `color p#line' outright
        (the extractor's resolution of Stata's chain, #1a476f for p1), and
        an included key the child does not set stands."""
        red, _ = self._parse(wd, "w26ord2", "#include s2color\ncolor p1 red\n")
        inc, _ = self._parse(wd, "w26inc", "#include s2color\n")
        kinds = ("line", "scatter", "connected", "bar")
        if [inc.default_color(0, k) for k in kinds] != ["#1a476f"] * 4:
            pytest.fail("control: s2color's p1 is not navy for every kind")
        if (red.default_color(0, "line"), red.default_color(1, "scatter")) \
                != ("#ff0000", "#90353b"):
            pytest.fail("control: the child's red did not reach the line "
                        "plot, or reached series 2")
        assert {k: red.default_color(0, k) for k in kinds} == {
            k: "#ff0000" for k in kinds}
