"""WP-30 P1.25a: StataCorp's six remaining schemes, twenty-six in all.

The defect (DROPIN-REMAINING.md P1.25, measured 03oct2026 on StataNow 19.5):
Stata's BASE/s holds 26 ``scheme-*.scheme`` files and dash shipped 20.  The
six it did not ship -- meta, stcolor_meta, stcolor_mv, stcoloralias,
stgcolor_meta and stgcolor_mv -- were refused r(198) by ``dash <plot>,
scheme(X)`` ("scheme() must be a shipped scheme, a theme, or a .scheme file
in the working directory") where ``twoway`` draws each with rc 0.  After
``set scheme stcolor_meta`` an unschemed dash graph was drawn as s2color
(border ``#eaf2f3``) with the warning "'stcolor_meta' is not a known theme
or scheme; it was inherited from the session", in both modes, and a user
file's ``#include stcolor_meta`` was read as ``#include s2color``.

twoway's truth, probe ``p1.do`` (03oct2026): ``twoway scatter mpg weight,
yline(20) scheme(X)``, ``graph export`` to SVG, read with
scripts/svg_truth.py::

    meta          5.500in x 4.000in  bg #eaf2f3 marker #1a476f  yline #c10534 solid   tick 79.94
    stcolor_meta  7.500in x 4.500in  bg #ffffff marker #1a85ff  yline #c10534 solid   tick 112.56
    stcolor_mv    6.000in x 4.000in  bg #ffffff marker #1a85ff  yline #000000 solid   tick 100.04
    stcoloralias  7.500in x 4.500in  bg #ffffff marker #1a85ff  yline #000000 dashed  tick 112.56
    stgcolor_meta 3.987in x 2.392in  bg #ffffff marker #1a85ff  yline #c10534 solid   tick 59.84
    stgcolor_mv   3.588in x 2.392in  bg #ffffff marker #1a85ff  yline #000000 solid   tick 59.81
    stcolor       7.500in x 4.500in  bg #ffffff marker #1a85ff  yline #000000 dashed  tick 112.56
    s2color       5.500in x 4.000in  bg #eaf2f3 marker #1a476f  yline #c10534 solid   tick 99.99

``twoway lfitci mpg weight, scheme(S)`` (graph object): meta's band fill and
outline 192 192 192 and fit 26 71 111; the other five 224 224 224 and fit
26 133 255.  The same comparisons are re-measured against dash's pages in
test_wp30_truth.cscript SX-01..SX-08.
"""
import json
import os
import re
import sys
import warnings

import pytest
from bokeh.models import ColorMapper, Plot, Span

# WP-50 50-03: the batch tier, run at batch ends (make test-all), ruled 13nov2026 at 50-01-04.
pytestmark = pytest.mark.batch

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import (  # noqa: E402
    MODES, _ado_block, _ado_list, _draw, _extractor_schemes, _served, each)
from test_server_layer_defects import plot_for  # noqa: E402
from test_served_linked_views import _fire  # noqa: E402
import test_ci_band_style as cb  # noqa: E402

SIX = ("meta", "stcolor_meta", "stcolor_mv", "stcoloralias",
       "stgcolor_meta", "stgcolor_mv")

#: twoway's drawing, measured by p1.do (module docstring).  yline is
#: (colour, solid?); graphsize is (x, y) in inches.
_TWOWAY = {
    "meta": dict(bg="#eaf2f3", marker="#1a476f", yline=("#c10534", True),
                 graphsize=(5.5, 4.0), tick=79.94),
    "stcolor_meta": dict(bg="#ffffff", marker="#1a85ff",
                         yline=("#c10534", True), graphsize=(7.5, 4.5),
                         tick=112.56),
    "stcolor_mv": dict(bg="#ffffff", marker="#1a85ff",
                       yline=("#000000", True), graphsize=(6.0, 4.0),
                       tick=100.04),
    "stcoloralias": dict(bg="#ffffff", marker="#1a85ff",
                         yline=("#000000", False), graphsize=(7.5, 4.5),
                         tick=112.56),
    "stgcolor_meta": dict(bg="#ffffff", marker="#1a85ff",
                          yline=("#c10534", True), graphsize=(3.987, 2.392),
                          tick=59.84),
    "stgcolor_mv": dict(bg="#ffffff", marker="#1a85ff",
                        yline=("#000000", True), graphsize=(3.588, 2.392),
                        tick=59.81),
    # controls
    "stcolor": dict(bg="#ffffff", marker="#1a85ff", yline=("#000000", False),
                    graphsize=(7.5, 4.5), tick=112.56),
    "s2color": dict(bg="#eaf2f3", marker="#1a476f", yline=("#c10534", True),
                    graphsize=(5.5, 4.0), tick=99.99),
}

#: Stata's include chains, root first (the extractor's include_chain).
_CHAINS = {
    "meta": ["s2color", "meta"],
    "stcolor_meta": ["s2color", "stcolor", "stcolor_meta"],
    "stcolor_mv": ["s2color", "stcolor", "stcolor_alt", "stcolor_mv"],
    "stcoloralias": ["s2color", "stcolor", "stcoloralias"],
    "stgcolor_meta": ["s2color", "stcolor", "stcolor_meta", "stgcolor_meta"],
    "stgcolor_mv": ["s2color", "stcolor", "stcolor_alt", "stgcolor_alt",
                    "stgcolor_mv"],
}

#: twoway lfitci's band fill, band outline and fit line (graph object).
_CI = {s: ("#e0e0e0", "#e0e0e0", "#1a85ff") for s in SIX}
_CI["meta"] = ("#c0c0c0", "#c0c0c0", "#1a476f")

_TOKEN = re.compile(r"^[a-z0-9_]{1,32}$")


def _fixture():
    with open(os.path.join(_HERE, "fixtures", "scheme_truth.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _scheme_spec(bo=None, go=None, filt=None):
    """One scatter of mpg on weight with yline(20), a graph option."""
    go = dict(go or {}, yline="20")
    bo = dict(bo or {})
    if filt:
        bo["filter"] = filt
    return tp._spec([plot_for("scatter")], bo, go)


def _span(fig):
    spans = [m for m in fig.select({"type": Span})]
    assert spans, "no Span drawn for yline(20)"
    return spans[0]


def _summary(fig):
    s = _span(fig)
    return (fig.border_fill_color, fig.background_fill_color,
            s.line_color, list(s.line_dash),
            round(float(fig.aspect_ratio or 0), 9),
            fig.yaxis[0].major_label_text_font_size)


def _unknown(msgs):
    return [m for m in msgs
            if "is not a known theme or scheme" in m or "not found" in m]


# ---------------------------------------------------------------------------

class TestTheSixAreShipped:
    # Each of the six has its dash-<name>.scheme: test_scheme_resolution's
    # TestTheShippedListIsOneList::test_every_shipped_name_has_a_file checks
    # it for all twenty-six.

    def test_the_parser_ships_twenty_six(self):
        assert len(dr.SchemeParser._BUILTIN_NAMES) == 26
        assert set(SIX) <= dr.SchemeParser._BUILTIN_NAMES

    @each("name", SIX)
    def test_each_parses_from_its_file_without_a_word(self, name):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            s = dr.SchemeParser(name)
        assert s.is_fallback is False
        assert s.name == name
        assert [str(w.message) for w in caught] == []

    @each("name", SIX)
    def test_the_manifest_ships_each(self, name):
        with open(os.path.join(_ROOT, "dash.pkg"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        assert f"f dash-{name}.scheme" in lines

    def test_dash_ado_and_the_extractor_list_each(self):
        ado = _ado_list(_ado_block(), "_dash_schemes")
        ext = _extractor_schemes()
        for name in SIX:
            assert ado.count(name) == 1, name
            assert ext.count(name) == 1, name


class TestTheFixtureCoversTheSix:
    @each("name", SIX)
    def test_each_is_extracted_with_nothing_unresolvable(self, name):
        doc = _fixture()
        assert name in doc, name
        assert doc[name]["unresolvable"] == []

    @each("name", SIX)
    def test_each_chain_is_statas(self, name):
        assert _fixture()[name]["include_chain"] == _CHAINS[name]

    @each("name", SIX)
    def test_the_shipped_file_draws_the_fixture(self, name):
        rec = _fixture()[name]
        s = dr.SchemeParser(name)
        assert s.p_colors == rec["p_colors"]
        assert s.background_color == rec["background_color"]
        assert s.graphsize_x == pytest.approx(rec["graphsize_x"])
        assert s.graphsize_y == pytest.approx(rec["graphsize_y"])
        assert s.xyline_color == rec["xyline_color"]


class TestTheSixResolveInBothModes:
    @pytest.mark.parametrize("mode", MODES)
    @each("name", SIX)
    def test_by_build_scheme(self, name, mode):
        d = _draw(_scheme_spec({"scheme": name}), mode)
        assert d.scheme.name == name
        assert _unknown(d.warnings) == [], d.warnings
        assert d.fig.border_fill_color == _TWOWAY[name]["bg"]

    @pytest.mark.parametrize("mode", MODES)
    @each("name", SIX)
    def test_by_graph_scheme(self, name, mode):
        """The graph is drawn in its scheme(); the page is not (14nov2026)."""
        d = _draw(_scheme_spec(go={"scheme": name}), mode)
        assert _unknown(d.warnings) == [], d.warnings
        assert d.fig.border_fill_color == _TWOWAY[name]["bg"]

    @each("name", SIX)
    def test_unchanged_after_a_filter_move(self, name):
        spec = _scheme_spec({"scheme": name}, filt="foreign, type(dropdown)")
        saved = _draw(spec, "standalone")
        doc, mod, msgs = _served(spec)
        assert mod._DASH_SCHEME.name == name
        [fig] = [f for f in doc.select({"type": Plot})
                 if f.select({"type": Span})]
        before = _summary(fig)
        _fire(doc, "foreign", "Foreign")
        assert _summary(fig) == before
        assert _summary(saved.fig) == before


class TestTheInheritedSchemeIsOneOfTheSix:
    @each("name", SIX)
    def test_the_session_scheme_resolves(self, name):
        spec = {"graphs": [], "kpis": [],
                "build_options": {"scheme": "", "theme": "",
                                  "session_scheme": name}}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._resolve_scheme_name(spec)
        assert got == name
        assert [str(w.message) for w in caught] == []

    # Drawn as the session scheme, in both modes, without a word:
    # test_scheme_resolution's TestEveryShippedSchemeResolves::
    # test_as_the_session_scheme, for all twenty-six; the six's twoway
    # background is test_by_build_scheme's.


class TestTheSixDrawWhatTwowayDraws:
    @pytest.mark.parametrize("mode", MODES)
    @each("name", SIX)
    def test_the_background_and_first_series(self, name, mode):
        d = _draw(_scheme_spec({"scheme": name}), mode)
        assert d.fig.border_fill_color == _TWOWAY[name]["bg"]
        glyphs = [r.glyph for r in d.fig.renderers
                  if type(r.glyph).__name__ == "Scatter"]
        assert glyphs, "no Scatter glyph"
        assert str(glyphs[0].fill_color).lower() == _TWOWAY[name]["marker"]

    @pytest.mark.parametrize("mode", MODES)
    @each("name", SIX + ("stcolor", "s2color"))
    def test_the_yline_is_the_schemes(self, name, mode):
        d = _draw(_scheme_spec({"scheme": name}), mode)
        s = _span(d.fig)
        colour, solid = _TWOWAY[name]["yline"]
        assert str(s.line_color).lower() == colour
        assert (list(s.line_dash) == []) is solid, s.line_dash

    @pytest.mark.parametrize("mode", MODES)
    @each("name", SIX)
    def test_the_proportions_are_the_graphsize(self, name, mode):
        d = _draw(_scheme_spec({"scheme": name}), mode)
        x, y = _TWOWAY[name]["graphsize"]
        # Flipped (BUGS.md "A graph's canvas ended before its own x axis, x title and
        # colour key labels"): the figure keeps what the graph margin leaves; its
        # graph region box round it keeps the graph's shape.
        assert d.fig.aspect_ratio == pytest.approx(dr._dash_inner_ratio(
            x / y, d.fig._dash_gmargin), abs=1e-9)

    @pytest.mark.parametrize("mode", MODES)
    def test_metas_tick_labels_are_twoways_ratio(self, mode):
        def size(name):
            d = _draw(_scheme_spec({"scheme": name}), mode)
            return float(d.fig.yaxis[0].major_label_text_font_size[:-2])
        ratio = size("meta") / size("s2color")
        assert ratio == pytest.approx(79.94 / 99.99, abs=0.01)

    @pytest.mark.parametrize("mode", MODES)
    def test_metas_legend_sits_at_4_oclock(self, mode):
        d = _draw(_scheme_spec({"scheme": "meta"}), mode)
        assert d.scheme.legend_position == 4

    @each("name", SIX)
    def test_the_ci_band_is_statas(self, name):
        k = cb._parts(cb._draw("lfitci", name, {}).renderers)
        band = k["VArea"][0].glyph
        outline = k["Patch"][0].glyph
        line = k["Line"][0].glyph
        got = (cb._hex(band.fill_color), cb._hex(outline.line_color),
               cb._hex(line.line_color))
        assert got == _CI[name]


class TestStcoloraliasIsDrawnAsStcolor:
    def test_every_parsed_property_but_the_name_is_stcolors(self):
        a, b = vars(dr.SchemeParser("stcoloralias")), vars(
            dr.SchemeParser("stcolor"))
        assert {k for k in a if a[k] != b.get(k)} == {"name"}

    @pytest.mark.parametrize("mode", MODES)
    def test_a_colorvar_scatter_matches_stcolor(self, mode):
        def mapper(name):
            d = _draw(tp._spec([plot_for("scatter", {"colorvar": "price"})],
                               {"scheme": name}, {}), mode)
            assert d.scheme.name == name
            assert _unknown(d.warnings) == [], d.warnings
            ms = list(d.fig.select({"type": ColorMapper}))
            assert ms, "no colour mapper"
            # Flipped (WP-42 CV-8): the glyphs' stepped mapper and the
            # key bar's own mapper are both drawn; compare every mapper,
            # in a fixed order (a set's order picked either one).
            return sorted((list(m.palette), getattr(m, "low", None),
                           getattr(m, "high", None)) for m in ms)
        assert mapper("stcoloralias") == mapper("stcolor")

    def test_the_help_says_so(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        assert "{cmd:zyx2rule colorvar hue}" in text
        assert "drawn as {cmd:stcolor}" in text


class TestAnIncludeOfOneOfTheSixResolves:
    def test_include_stcolor_meta_without_a_note(self, tmp_path,
                                                 monkeypatch):
        (tmp_path / "sx8.scheme").write_text(
            "#include stcolor_meta\ncolor background #ff0000\n",
            encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            s = dr.SchemeParser("sx8")
        assert [str(w.message) for w in caught
                if "not found" in str(w.message)] == []
        assert s.background_color == "#ff0000"
        assert s.p_colors[0] == "#1a85ff"
        assert s.xyline_color == "#c10534"


def _shipped_files():
    return sorted(f for f in os.listdir(_ROOT)
                  if f.startswith("dash-") and f.endswith(".scheme"))


class TestTheSixAreData:
    @each("fname", _shipped_files())
    def test_every_shipped_file_is_flat_and_hex(self, fname):
        with open(os.path.join(_ROOT, fname), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        hexre = re.compile(r"^#[0-9a-f]{6}( ?%\d{1,3})?$|^none$")
        for ln in lines:
            s = ln.strip()
            if not s or s.startswith("*") or s.startswith("//"):
                continue
            assert not s.startswith("#include"), ln
            parts = s.split(None, 2)
            if parts[0] == "color" and len(parts) == 3:
                assert hexre.match(parts[2].strip('"')), ln
            value = " ".join(parts[1:])
            for bad in ("/", "\\", ".."):
                assert bad not in value, ln
            if parts[0] != "label":
                assert '"' not in value or parts[0] == "color", ln
            assert not any(ord(c) < 32 for c in ln), ln

    def test_every_listed_name_is_a_plain_token(self):
        names = (list(dr.SchemeParser._BUILTIN_NAMES)
                 + _ado_list(_ado_block(), "_dash_schemes")
                 + _extractor_schemes())
        assert [n for n in names if not _TOKEN.match(n)] == []

    @each("bad", ["../x", "a/b", "x y", "", "a" * 33, "S2COLOR"])
    def test_the_extractor_refuses_a_name_that_is_not_a_token(
            self, tmp_path, bad, capsys):
        import extract_scheme_truth as mod
        out, d = tmp_path / "o.json", tmp_path / "d"
        rc = mod.main(["--out", str(out), "--schemes-dir", str(d),
                       "--schemes", bad])
        assert rc == 2
        assert not out.exists()
        assert not d.exists() or not any(d.rglob("*"))
        assert "--schemes takes scheme names" in capsys.readouterr().err


class TestMetasMinorGridIsHandedOn:
    @pytest.mark.parametrize("mode", MODES)
    def test_dash_still_draws_metas_minor_grid(self, mode):
        """A guard, not twoway's truth: twoway draws no minor grid under
        meta (it draws minor ticks only under xmtick()/ymtick(), so
        p1_meta.svg has no #505050 line), while meta's ``yesno
        draw_minor_hgrid/draw_minor_vgrid yes`` colours Bokeh's default
        minor grid.  S15 (P1.2a, "no minor ticks unless asked") flips this
        test when it removes Bokeh's default minor positions; the flip is
        S15's, not S07's."""
        d = _draw(_scheme_spec({"scheme": "meta"}), mode)
        assert d.scheme.name == "meta"
        for g in (d.fig.xgrid[0], d.fig.ygrid[0]):
            assert str(g.minor_grid_line_color).lower() == "#505050"
