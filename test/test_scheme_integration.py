"""
test_scheme_integration.py
Integration tests for SchemeParser integration into DashRenderer.

Covers: scheme loaded from build_options, applied to figure, CSS injected into HTML.

Run with:  pytest test/test_scheme_integration.py -v
"""
import sys
import os
import json
import re
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer, SchemeParser


# ============================================================
# Helpers
# ============================================================

def _make_renderer(scheme="", plots=None, graph_opts=None):
    """Build a DashRenderer instance with given scheme name in build_options."""
    n = 10
    data = {"x": list(range(n)), "y": [float(i) * 1.5 for i in range(n)]}
    data_json = {
        "StataJSON": {
            "variableNames": list(data.keys()),
            "variableLabels": {k: k for k in data},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {k: False for k in data},
            "values": [{k: data[k][i] for k in data} for i in range(n)],
        }
    }
    if plots is None:
        plots = [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}]
    spec = {
        "graphs": [{
            "plots": plots,
            "graph_options": graph_opts or {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "g1",
            "scheme": scheme,
        },
    }
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data_json, f)
        return DashRenderer(sp, dp, op)
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass


def _render(scheme=""):
    """Return standalone HTML string from a full render with given scheme."""
    dr = _make_renderer(scheme=scheme)
    # Temporarily write to a temp file and return result
    n = 10
    data = {"x": list(range(n)), "y": [float(i) * 1.5 for i in range(n)]}
    data_json = {
        "StataJSON": {
            "variableNames": list(data.keys()),
            "variableLabels": {k: k for k in data},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {k: False for k in data},
            "values": [{k: data[k][i] for k in data} for i in range(n)],
        }
    }
    spec = {
        "graphs": [{
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "g1",
            "scheme": scheme,
        },
    }
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data_json, f)
        return DashRenderer(sp, dp, op).render()
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass


# ============================================================
# SI-01 – 04: Scheme loaded in __init__
# ============================================================

class TestSchemeLoadedInInit:
    def test_default_scheme_is_s2color(self):
        """SI-01: DashRenderer with no scheme uses s2color by default."""
        dr = _make_renderer(scheme="")
        assert isinstance(dr.scheme, SchemeParser)
        # s2color p1 marker color is navy (#1F497D or similar blue)
        p1 = dr.scheme.default_color(0, "scatter")
        assert p1.startswith("#")

    def test_explicit_scheme_loaded(self):
        """SI-02: DashRenderer with scheme='sj' loads sj scheme."""
        dr = _make_renderer(scheme="sj")
        # sj p1 is grey, NOT black.  Stata's scheme-sj.scheme declares no
        # `color p1` of its own; it `#include`s s2mono, whose `color p1 gs6`
        # resolves via color-gs6.style ("96 96 96") to #606060.
        # This previously asserted #000000, which was the old approximate
        # schemes/sj.scheme failing to resolve its colour rather than Stata's
        # real value -- the same silent-black failure that made stcolor
        # unusable.  Verified against /Applications/Stata/ado/base/.
        p1 = dr.scheme.default_color(0, "scatter")
        assert p1 == "#606060"

    def test_invalid_scheme_falls_back_to_s2color(self):
        """SI-03: Unknown scheme name falls back to s2color without crash."""
        dr = _make_renderer(scheme="nonexistent_scheme_xyz")
        assert isinstance(dr.scheme, SchemeParser)

    def test_s1mono_scheme_loaded(self):
        """SI-04: s1mono scheme loads successfully."""
        dr = _make_renderer(scheme="s1mono")
        assert isinstance(dr.scheme, SchemeParser)


# ============================================================
# SI-05 – 07: apply_to_figure called in _make_figure
# ============================================================

#: What Stata's shipped schemes declare, read from its own files
#: (ado/base/s/scheme-*.scheme and ado/base/style/color-*.style, 24sep2026):
#: the graph region (`color background') and the plot region (`color
#: plotregion').  s2color: ltbluishgray "234 242 243" and white; sj
#: includes s2mono: gs15 "240 240 240" and white; s1color and s1mono:
#: white and white; economist: ebg "198 211 223" for both.
#:
#: White is also Bokeh's own default for both regions, and the BokehJS a
#: saved page inlines holds "white" and "#ffffff" whatever the scheme
#: (measured 24sep2026, in an economist page: its colour table, its model
#: defaults, its CSS), so a check that finds white proves nothing: every
#: test below reads a colour no default gives, from the figure or the
#: page's own stylesheet.
_STATA_REGIONS = {
    "s2color":   ("#eaf2f3", "#ffffff"),
    "sj":        ("#f0f0f0", "#ffffff"),
    "s1color":   ("#ffffff", "#ffffff"),
    "s1mono":    ("#ffffff", "#ffffff"),
    "economist": ("#c6d3df", "#c6d3df"),
}


def _head_styles(html_str):
    """The text of each <style> element in the page's <head>."""
    head = re.search(r"<head>(.*?)</head>", html_str, re.S)
    assert head, "the page has no <head>"
    return re.findall(r"<style>(.*?)</style>", head.group(1), re.S)


def _body_backgrounds(html_str):
    """Every `body { background-color: ... }' rule the head's stylesheets
    set, in order."""
    return [m for s in _head_styles(html_str)
            for m in re.findall(r"\bbody\s*\{\s*background-color:\s*([^;}]+);",
                                s)]


class TestApplyToFigureInMakeFigure:
    def _get_fig(self, scheme="s2color"):
        dr = _make_renderer(scheme=scheme)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_s2color_sets_white_background(self):
        """SI-05: s2color scheme sets white background_fill_color on figure
        -- its plot region -- and its graph region, the figure's border,
        ltbluishgray.  White alone is Bokeh's default, so it could not show
        the scheme was applied."""
        fig = self._get_fig("s2color")
        assert (fig.border_fill_color, fig.background_fill_color) \
            == _STATA_REGIONS["s2color"]

    def test_sj_scheme_sets_white_background(self):
        """SI-06: sj scheme also sets white background_fill_color, and its
        own graph region, s2mono's gs15."""
        fig = self._get_fig("sj")
        assert (fig.border_fill_color, fig.background_fill_color) \
            == _STATA_REGIONS["sj"]

    def test_scheme_sets_grid_properties(self):
        """SI-07: apply_to_figure sets grid line properties.

        s2color draws the major grid of the y axis alone
        (draw_major_vgrid yes, draw_major_hgrid no), in ltbluishgray
        (major_grid); Bokeh draws both, in #e5e5e5, so "some grid colour is
        set", which this was, held with the scheme never applied."""
        fig = self._get_fig("s2color")
        assert [g.grid_line_color for g in fig.xgrid] == [None]
        assert [g.grid_line_color for g in fig.ygrid] == ["#eaf2f3"]


# ============================================================
# SI-08 – 10: CSS block injected into HTML
# ============================================================

class TestCssBlockInHtml:
    def test_html_contains_style_tag(self):
        """SI-08: rendered HTML contains a <style> tag from
        scheme.css_block(): the block whole, in a stylesheet of the page's
        head.  Bokeh's own page template has a <style> of its own, so "a
        <style> tag", which this was, was always there."""
        html_str = _render("s2color")
        css = SchemeParser("s2color").css_block()
        assert [s for s in _head_styles(html_str) if css in s], \
            _head_styles(html_str)

    def test_html_contains_scheme_background_color(self):
        """SI-09: rendered HTML contains scheme background color in CSS.

        The page's stylesheet sets the body to s2color's graph region,
        ltbluishgray -- one rule, holding that colour.  This asserted
        "#ffffff" or "white" anywhere in the page, which every page holds
        in its inlined BokehJS whatever the scheme."""
        html_str = _render("s2color")
        assert _body_backgrounds(html_str) == [_STATA_REGIONS["s2color"][0]]

    def test_sj_html_different_from_s2color_html(self):
        """SI-10: different schemes produce different HTML (CSS differs).

        The stylesheets differ, in the graph region each sets.  The whole
        pages always differed, the ids Bokeh gives every model with them."""
        assert _body_backgrounds(_render("s2color")) == ["#eaf2f3"]
        assert _body_backgrounds(_render("sj")) == ["#f0f0f0"]

    def test_html_renders_without_error_all_schemes(self):
        """SI-11: all built-in schemes render to HTML without error -- a
        page holding the figure, styled with that scheme's graph region.
        "len(html) > 100" passed any page at all, one with no figure in it
        included."""
        from bokeh.document import Document
        from bokeh.models import Plot
        import html as _html
        for scheme, (bg, _plot) in _STATA_REGIONS.items():
            html_str = _render(scheme)
            assert _body_backgrounds(html_str) == [bg], scheme
            blocks = re.findall(
                r'<script type="application/json" id="[^"]+">\s*(.*?)\s*'
                r'</script>', html_str, re.S)
            docs = [Document.from_json(d) for b in blocks
                    for d in json.loads(_html.unescape(b)).values()]
            plots = [p for d in docs for p in d.select({"type": Plot})]
            assert len(plots) == 1, (scheme, len(plots))
            assert plots[0].border_fill_color == bg, scheme
