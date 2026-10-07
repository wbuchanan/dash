"""
test_ci_band_style.py -- a ci fit's band is drawn in Stata's ci style.

The defect (BUGS.md, S3): "A ci band is filled in its line's colour, where
Stata fills it in pstyle ci".  dash filled lfitci's, qfitci's, lpolyci's and
fpfitci's band in the fit line's p# colour at its own 0.2 alpha, with no
outline, whatever the scheme said.

Stata's truth, measured 24sep2026 with StataNow 19.5 (batch) from the graph
object -- .Graph.plotregion1.plot1.style.area, the band, and plot2's line --
for each of the four ci types under each of the twenty shipped schemes, and
kept in test/fixtures/ci_band_style_truth.json (below).
ci_band_style_truth.json has no generator and covers the twenty schemes
measured 24sep2026; StataCorp's six internal schemes are certified against
twoway's graph object by test_wp30_truth.cscript SX-06 and
test_twenty_six_schemes.py::TestTheSixDrawWhatTwowayDraws::test_the_ci_band_is_statas.
The fixture's truth:

* The band is areastyle ci (style/areastyle-ci.style): its fill is
  ``color ci_area`` at ``intensity ci_area``, its outline ``color
  ci_arealine`` at ``linewidth ci_area`` and ``linepattern ci_area``.  Under
  s2color that is gs12 (#C0C0C0), full, gs12, medium, solid.
* ``pstyle(p#)`` puts the band in p#'s "other" area (style/areastyle-p#
  .style): fill ``color p#other`` at ``intensity p#bar``, outline ``color
  p#otherline`` at ``linewidth p#other`` and ``linepattern p#other``, each
  down Stata's p#stub -> pstub -> p# -> p chain; and the fit line in p#.
  ``pstyle(ci2)`` is the ci2 keys, and ``pstyle(ci)``/``pstyle(ci2)`` draw
  the fit line in ``color ci_line``/``ci2_line``.  A style Stata does not
  know -- p16, P3, bogus -- is "default attributes used", which draws p1.
* The options, as twoway merges them onto the band: fill colour is
  color() < acolor() < fcolor(); outline colour color() < lcolor() <
  acolor() < alcolor(); outline width lwidth() < alwidth(); pattern
  lpattern() < alpattern(); fintensity() the intensity; a colour's %NN its
  opacity.  clcolor() never reaches the band.  A "none" colour draws no fill
  or no outline.
* twoway's SVG export draws the fill as the colour blended towards white by
  its intensity (red at fintensity(50) is #FF8080) at fill-opacity = the
  colour's opacity, and the outline as a closed path round the band.
"""
import itertools
import json
import os
import re
import sys
import time
import warnings
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from dash_render import GlyphMapper, SchemeParser  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "ci_band_style_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

_CI_TYPES = ("lfitci", "qfitci", "lpolyci", "fpfitci")
_SCHEMES = sorted(_T["cases"])

#: Measured, and not held to the graph object here, with the reason:
_NOT_COMPARED = {
    # astyle(), alstyle() and ciplot() are not honoured: dash names them in
    # its note (they are not declared options).
    "astyle", "ciplot",
    # Refused by dash.ado, as by twoway when it draws (r(198)); the graph
    # object holds them only under nodraw.  test_ci_band_options.cscript.
    "alw_neg", "alw_big",
    # A bare number: dash's lwidth() reads one as pixels, and alwidth()
    # reads it as lwidth() does.
    "alw_num",
    # An unknown colour: twoway draws "default attributes" (black under
    # s2color, white under economist); dash notes the name and keeps the
    # scheme's, as it does for every colour option.
    "bogusc",
}
_NO_FILL = {"fcnone", "acnone", "colnone"}
_NO_OUTLINE = {"alcnone", "acnone", "colnone", "lcnone"}
_NO_FIT_LINE = {"colnone", "lcnone"}

#: Stata's widths as dash draws them: medium (.3) 1.5px, thick (.8) 2.5px,
#: vthin (.15) 0.5px on dash's keyword ladder; economist's numeric 1.2 at
#: 5px a unit (SchemeParser._lwidth); none 0.
# Flipped (WP-30 P1.12b): dash's private ladder (medium 1.5 px) became
# Stata units, 1 unit = 3.84 px.
_UNIT_PX = {0.3: 1.152, 0.8: 3.072, 0.15: 0.576, 1.2: 4.608, 0.0: 0.0}


def _opts(text):
    return {k.lower(): v for k, v in re.findall(r"(\w+)\(([^()]*)\)", text)}


#: The schemes whose `system naturally_white' is 0: twoway multiplies an
#: intensity towards black there (scheme-s1rcolor.scheme; SVG, s1rcolor
#: lfitci fintensity(50) #282828, test/fixtures/intensity_truth.json).
_NOT_WHITE = {"s1rcolor"}


def _blend(hexval, f, white=True):
    """twoway's blend at f <= 1: towards white, or (``white`` False,
    naturally_white 0) multiplied towards black (WP-30 P1.2b)."""
    h = hexval.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16)
        v = 255.0 - (255.0 - c) * f if white else c * f
        out.append(int(Decimal(repr(v)).quantize(Decimal("1"),
                                                 rounding=ROUND_HALF_UP)))
    return "#%02x%02x%02x" % tuple(out)


def _dash(pattern_name):
    return list(dr.OptionTranslator.translate_lpattern(pattern_name))


def _hex(c):
    return str(c).lower()


_N = 40
_DF = pd.DataFrame({
    "x": np.linspace(1.0, 40.0, _N),
    "y": np.sin(np.linspace(0, 3, _N)) * 10 + 20 + np.linspace(0, 5, _N),
    "y2": np.cos(np.linspace(0, 3, _N)) * 10 + 30,
})


def _parts(renderers):
    kinds = {}
    for r in renderers:
        kinds.setdefault(type(getattr(r, "glyph", None)).__name__, []).append(r)
    return kinds


def _draw(ptype, scheme, opts, idx=0):
    gm = GlyphMapper(scheme=SchemeParser(scheme))
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        getattr(gm, "map_" + ptype)(fig, ColumnDataSource(_DF), "y", "x",
                                    dict(opts), color_idx=idx)
    return fig


def _check(fig, want, var, scheme=""):
    k = _parts(fig.renderers)
    band, outline, line = k["VArea"][0].glyph, k["Patch"][0].glyph, \
        k["Line"][0].glyph
    if var in _NO_FILL:
        assert band.fill_alpha == 0.0
    else:
        assert _hex(band.fill_color) == _blend(
            want["fill_rgb"], want["fill_intensity"] / 100.0,
            scheme not in _NOT_WHITE), (
            band.fill_color, want)
        assert band.fill_alpha == pytest.approx(want["fill_opacity"] / 100.0)
    if var in _NO_OUTLINE or want["outline_width"] == 0:
        assert outline.line_alpha == 0.0 or outline.line_width == 0
    else:
        assert _hex(outline.line_color) == want["outline_rgb"], (
            outline.line_color, want)
        assert outline.line_alpha == pytest.approx(
            want["outline_opacity"] / 100.0)
        assert outline.line_width == pytest.approx(
            _UNIT_PX[want["outline_width"]])
        assert list(outline.line_dash) == _dash(want["outline_pattern"])
    assert outline.fill_alpha == 0.0
    if var not in _NO_FIT_LINE:
        assert _hex(line.line_color) == want["fit_rgb"], (line.line_color,
                                                         want)
        assert line.line_width == pytest.approx(_UNIT_PX[want["fit_width"]])
        assert list(line.line_dash) == _dash(want["fit_pattern"])


_CASES = [(s, v) for s in _SCHEMES for v in sorted(_T["cases"][s])
          if v not in _NOT_COMPARED]


class TestTheBandAgainstStata:
    @pytest.mark.parametrize("scheme,var", _CASES,
                             ids=["%s-%s" % c for c in _CASES])
    def test_each_measured_case(self, scheme, var):
        """The band's fill, intensity, opacity and outline, and the fit
        line, as Stata draws them, for every ci type measured."""
        want = _T["cases"][scheme][var]
        opts = _opts(_T["options"][var])
        for ptype in want["types"]:
            _check(_draw(ptype, scheme, opts), want, var, scheme)

    def test_the_fixture_covers_every_scheme_and_type(self):
        """ci_band_style_truth.json has no generator and covers the twenty
        schemes measured 24sep2026; StataCorp's six internal schemes are
        certified against twoway's graph object by test_wp30_truth.cscript
        SX-06 and test_twenty_six_schemes.py::TestTheSixDrawWhatTwowayDraws
        ::test_the_ci_band_is_statas."""
        assert len(_SCHEMES) == 20
        for s in _SCHEMES:
            for v in ("def", "p3", "color", "fcolor", "acolor", "alcolor"):
                assert set(_T["cases"][s][v]["types"]) == set(_CI_TYPES)

    @pytest.mark.parametrize("ptype", _CI_TYPES)
    def test_s2colors_band_is_gs12(self, ptype):
        """The number the entry names: gs12, opaque, outlined in gs12."""
        k = _parts(_draw(ptype, "s2color", {}).renderers)
        assert _hex(k["VArea"][0].glyph.fill_color) == "#c0c0c0"
        assert k["VArea"][0].glyph.fill_alpha == 1.0
        assert _hex(k["Patch"][0].glyph.line_color) == "#c0c0c0"

    def test_the_band_does_not_follow_the_plot_index(self):
        """The band is ci whatever p# the line draws in; the line moves."""
        a = _parts(_draw("lfitci", "s2color", {}, idx=0).renderers)
        b = _parts(_draw("lfitci", "s2color", {}, idx=4).renderers)
        assert a["VArea"][0].glyph.fill_color == b["VArea"][0].glyph.fill_color
        assert a["Line"][0].glyph.line_color != b["Line"][0].glyph.line_color

    def test_pstyle_overrides_the_plot_index(self):
        """pstyle(p3) on the fourth plot's layer: band and line in p3."""
        sp = SchemeParser("s2color")
        k = _parts(_draw("lfitci", "s2color", {"pstyle": "p3"},
                         idx=6).renderers)
        assert _hex(k["Line"][0].glyph.line_color) == \
            _hex(sp.default_color(2, "line"))
        assert _hex(k["Patch"][0].glyph.line_color) == "#55752f"


class TestTheOutline:
    @pytest.mark.parametrize("ptype", _CI_TYPES)
    def test_it_is_a_closed_path_round_the_band(self, ptype):
        """twoway strokes the band as one closed path, its ends included."""
        k = _parts(_draw(ptype, "s2color", {}).renderers)
        band = k["VArea"][0]
        data = band.data_source.data
        x = list(data[band.glyph.x])
        lo = list(data[band.glyph.y1])
        hi = list(data[band.glyph.y2])
        out = k["Patch"][0]
        ox = list(out.data_source.data[out.glyph.x])
        oy = list(out.data_source.data[out.glyph.y])
        assert ox == x + x[::-1] + x[:1]
        assert oy == lo + hi[::-1] + lo[:1]

    def test_it_is_drawn_before_the_fit_line(self):
        """Stata draws the band, its outline, then the line over them."""
        names = [type(r.glyph).__name__
                 for r in _draw("lfitci", "s2color", {}).renderers]
        assert names.index("VArea") < names.index("Patch") < \
            names.index("Line")

    @pytest.mark.parametrize("ptype", _CI_TYPES)
    def test_an_empty_layer_draws_an_empty_outline(self, ptype):
        """No rows: nothing drawn, and nothing raised."""
        gm = GlyphMapper(scheme=SchemeParser("s2color"))
        fig = figure()
        src = ColumnDataSource({"x": [], "y": []})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            getattr(gm, "map_" + ptype)(fig, src, "y", "x", {})
        k = _parts(fig.renderers)
        assert _hex(k["VArea"][0].glyph.fill_color) == "#c0c0c0"
        for r in k.get("Patch", []):
            assert all(len(v) == 0 for v in r.data_source.data.values())


class TestTheSchemeKeys:
    def test_a_user_schemes_ci_keys_are_read(self, tmp_path, monkeypatch):
        """`#include s2color' then the ci keys: the band takes them."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "cz.scheme").write_text(
            "#include s2color\ncolor ci_area red\ncolor ci_arealine navy\n"
            "intensity ci_area inten50\nlinewidth ci_area thick\n"
            "linepattern ci_area dash\n", encoding="utf-8")
        k = _parts(_draw("lfitci", "cz.scheme", {}).renderers)
        assert _hex(k["VArea"][0].glyph.fill_color) == _blend("#ff0000", 0.5)
        assert _hex(k["Patch"][0].glyph.line_color) == \
            dr.OptionTranslator.translate_mcolor("navy").lower()
        assert k["Patch"][0].glyph.line_width == pytest.approx(3.072)
        assert list(k["Patch"][0].glyph.line_dash) == _dash("dash")

    def test_a_user_schemes_other_keys_are_read(self, tmp_path, monkeypatch):
        """pstyle(p2) follows p#other -> pother -> p# -> p, as Stata does:
        economist's `linewidth pother thick' is the band's outline."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "oz.scheme").write_text(
            "#include s2color\ncolor p2other red\nlinewidth pother vthick\n"
            "intensity pbar inten30\n", encoding="utf-8")
        k = _parts(_draw("lfitci", "oz.scheme", {"pstyle": "p2"}).renderers)
        assert _hex(k["VArea"][0].glyph.fill_color) == _blend("#ff0000", 0.3)
        assert k["Patch"][0].glyph.line_width == pytest.approx(5.376)

    @pytest.mark.parametrize("scheme", _SCHEMES)
    def test_each_shipped_file_declares_the_ci_keys(self, scheme):
        """Transcribed by scripts/extract_scheme_truth.py, so a user's
        `#include' of a shipped scheme reaches them."""
        sp = SchemeParser(scheme)
        for key in ("color ci_area", "color ci_arealine", "intensity ci_area",
                    "linewidth ci_area", "linepattern ci_area",
                    "color ci2_area", "color ci2_arealine",
                    "linewidth ci2_area", "color ci_line", "linewidth ci",
                    "linepattern ci"):
            assert sp._props.get(key, "").strip(), (scheme, key)

    def test_the_fallback_scheme_draws_s2colors_band(self):
        gm = GlyphMapper(scheme=SchemeParser.fallback())
        fig = figure()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm.map_lfitci(fig, ColumnDataSource(_DF), "y", "x", {})
        k = _parts(fig.renderers)
        assert _hex(k["VArea"][0].glyph.fill_color) == "#c0c0c0"
        assert _hex(k["Patch"][0].glyph.line_color) == "#c0c0c0"


# ---------------------------------------------------------------------------
# Both modes, end to end, with the legend
# ---------------------------------------------------------------------------

_SEQ = itertools.count()


def _spec(plots, scheme):
    return {"graphs": [{"plots": plots,
                        "graph_options": {"name": "g1", "title": '"t"'},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": scheme,
                              "session_scheme": "", "title": "",
                              "subtitle": "", "registry": "g1", "tabs": "",
                              "filter_position": "top", "csv": "0",
                              "level": "95", "formats": {}, "limits": {}}}


def _figure(mode, wd, plots, scheme):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    tag = next(_SEQ)
    sp = wd / ("spec_%d.json" % tag)
    dp = wd / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, scheme)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            return list(r._build_figures().values())[0]
        ap = str(wd / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        mod = load_app(ap, "_cib_app_%d" % tag)
        doc = Document()
        mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1
    return figs[0]


_E2E = [("s2color", "def"), ("s2color", "p3"), ("economist", "p3"),
        ("sttrans", "p3"), ("stcolor", "def"), ("s2color", "acol_alcol"),
        ("s2color", "lw_alw"), ("s2color", "ci2"), ("economist", "ci"),
        ("s2color", "fcop_fint")]


# Each case on the types it was measured on (some on lfitci only), so no
# parameter is a skip: a skip is not a pass (DASH_STRICT).
_E2E_TYPED = [(s, v, pt) for s, v in _E2E for pt in _CI_TYPES
              if pt in _T["cases"][s][v]["types"]]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestBothModes:
    @pytest.mark.parametrize("scheme,var,ptype", _E2E_TYPED,
                             ids=["%s-%s-%s" % c for c in _E2E_TYPED])
    def test_the_band_is_drawn_as_stata_draws_it(self, mode, tmp_path,
                                                 ptype, scheme, var):
        want = _T["cases"][scheme][var]
        plots = [{"type": ptype, "yvar": "y", "xvar": "x",
                  "options": _opts(_T["options"][var])}]
        _check(_figure(mode, tmp_path, plots, scheme), want, var)

    def test_the_legend_key_is_the_band(self, mode, tmp_path):
        """scatter || lfitci, alcolor(red): the band's key is its fill and
        its outline, the fit's key the line."""
        plots = [{"type": "scatter", "yvar": "y", "xvar": "x",
                  "options": {}},
                 {"type": "lfitci", "yvar": "y", "xvar": "x",
                  "options": {"alcolor": "red"}}]
        fig = _figure(mode, tmp_path, plots, "s2color")
        items = {it.label["value"]: it for lg in fig.legend
                 for it in lg.items}
        band = _parts(items["95% CI"].renderers)
        assert _hex(band["VArea"][0].glyph.fill_color) == "#c0c0c0"
        assert _hex(band["Patch"][0].glyph.line_color) == "#ff0000"
        assert "Line" not in band
        fit = _parts(items["Fitted values"].renderers)
        assert set(fit) == {"Line"}

    def test_the_outline_has_no_tooltip_of_its_own(self, mode, tmp_path):
        """A lone lfitci's fallback tooltip answers from the fit line, not
        from the outline's polygon."""
        plots = [{"type": "lfitci", "yvar": "y", "xvar": "x",
                  "options": {}}]
        fig = _figure(mode, tmp_path, plots, "s2color")
        from bokeh.models import HoverTool
        for t in fig.tools:
            if isinstance(t, HoverTool):
                for r in (t.renderers if isinstance(t.renderers, list)
                          else []):
                    assert type(r.glyph).__name__ != "Patch"


# ---------------------------------------------------------------------------
# Adversarial: every new input path
# ---------------------------------------------------------------------------

class TestAdversarial:
    @pytest.mark.parametrize("bad", [
        "p1;import os", "<script>alert(1)</script>", "p" * 10_000, "p0",
        "p-1", "p1e3", "p 3", "p٣", "P3", "p16", "ci3", "", "\x00",
        "p03", "{safe}", "p3\n"], ids=lambda v: repr(v)[:24])
    def test_a_pstyle_dash_does_not_know_is_p1(self, bad):
        """Injection: any pstyle() that is not p1..p15, ci or ci2 -- as
        Stata spells them -- draws p1's band and line, as twoway's
        "default attributes" do (measured: p16, P3, bogus), and raises
        nothing."""
        want = _T["cases"]["s2color"]["p1"]
        if bad == "":
            want = _T["cases"]["s2color"]["def"]
        _check(_draw("lfitci", "s2color", {"pstyle": bad}), want, "p1")

    def test_a_hostile_pstyle_is_named_once_and_shortened(self):
        gm = GlyphMapper(scheme=SchemeParser("s2color"))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._DASH_NOTED.clear()
            gm.map_lfitci(figure(), ColumnDataSource(_DF), "y", "x",
                          {"pstyle": "x" * 5000 + "\n<b>"})
        msgs = [str(m.message) for m in w if "pstyle" in str(m.message)]
        assert msgs, [str(m.message) for m in w]
        assert all(len(m) < 400 and "\n<b>" not in m for m in msgs)

    @pytest.mark.parametrize("key", ["acolor", "alcolor"])
    @pytest.mark.parametrize("bad", [
        "red`=1'", "$(rm -rf)", "<script>", "1e400", "nan", "red%nan",
        "red%1e400", "red%-5", "x" * 100_000, "‮red", "#12345g"], ids=lambda v: repr(v)[:24])
    def test_a_bad_colour_is_noted_and_the_scheme_kept(self, key, bad):
        """Injection and resource exhaustion: nothing raises, nothing of
        the value reaches a glyph, and the band keeps the ci style."""
        t0 = time.perf_counter()
        fig = _draw("lfitci", "s2color", {key: bad})
        assert time.perf_counter() - t0 < 5.0
        k = _parts(fig.renderers)
        if key == "acolor":
            assert _hex(k["VArea"][0].glyph.fill_color) in ("#c0c0c0",
                                                           "#ff0000")
        assert str(k["Patch"][0].glyph.line_color).startswith("#")

    @pytest.mark.parametrize("bad", ["1e400", "inf", "-inf", "nan", "-1",
                                     "bogus", "x" * 100_000, "thick;x"],
                             ids=lambda v: repr(v)[:24])
    def test_a_bad_alwidth_keeps_the_schemes(self, bad):
        k = _parts(_draw("lfitci", "s2color", {"alwidth": bad}).renderers)
        w = k["Patch"][0].glyph.line_width
        assert np.isfinite(w) and 0 <= w <= 1000

    @pytest.mark.parametrize("bad", ["bogus", "-.-" * 50_000, "dash;x",
                                     "<script>", ""], ids=lambda v: repr(v)[:24])
    def test_a_bad_alpattern_keeps_the_schemes(self, bad):
        t0 = time.perf_counter()
        k = _parts(_draw("lfitci", "s2color", {"alpattern": bad}).renderers)
        assert time.perf_counter() - t0 < 5.0
        assert list(k["Patch"][0].glyph.line_dash) == []

    def test_fintensity_out_of_range_is_bounded(self):
        for v in ("-50", "1e400", "inten999", "nan"):
            k = _parts(_draw("lfitci", "s2color",
                             {"fintensity": v}).renderers)
            c = k["VArea"][0].glyph.fill_color
            assert re.fullmatch(r"#[0-9a-f]{6}", _hex(c)), (v, c)
