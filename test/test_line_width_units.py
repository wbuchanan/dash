"""Line widths in Stata's units on Stata's ladder (WP-30 P1.12b).

The defect, measured at c96facd in both modes (saved page and served app
identical line for line)::

    line default 1.5 | economist default 6.0 | lwidth(medium) 1.5 | thin 0.8
    | thick 2.5 | vvvthick 6.6
    lwidth(vvvthin) 1.5 + "dash: lwidth(vvvthin) is not a recognised line
    width; using the scheme's default."
    lwidth(none) 1.5 + note | lwidth(1pt) 1.5 + note | lwidth(*2) 1.5 + note
    lwidth(.3) 0.3 | lwidth(2) 2.0 | lwidth(THICK) 2.5 (no note)

twoway's truth (StataNow 19.5, console, 03oct2026; ``capture noisily twoway
line mpg weight, lwidth(X)`` and ``graph export`` SVG stroke widths,
re-extracted by scripts/extract_line_width_truth.do into
test/fixtures/line_width_truth.json): the ladder is linear in Stata units
(medium .30, thick .8, vvvthick 4.2), one unit is 2.88 pt at the 4-inch
reference, ``*#`` multiplies the site's own default, a non-zero stroke is
floored at 0.3 pt, names are case-sensitive (``THICK`` is noted and the
default drawn), and a negative width is r(198) "gm_linewidth must be
between 0.000 and  1.0e+04".  dash draws 1 unit = 3.84 px.
"""

import itertools
import json
import math
import os
import re
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.document import Document  # noqa: E402
from bokeh.plotting import figure as _Figure  # noqa: E402
from conftest import load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

T = dr.OptionTranslator
_PX = 2.88 * 4 / 3
_FIXTURE = os.path.join(_HERE, "fixtures", "line_width_truth.json")
_SEQ = itertools.count()
_MODES = ["saved", "served"]


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _figure(mode, plots, go=None, scheme=""):
    """(figure, warnings) of a one-graph dashboard in *mode*.  The served
    app is imported outside the warning capture."""
    bo = {"scheme": scheme} if scheme else None
    spec = tp._spec(plots, bo, go)
    tag, sp, dp = tp._write(spec)
    if mode == "saved":
        with warnings.catch_warnings(record=True) as c:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp)
            fig = list(r._build_figures().values())[0]
        return fig, [str(w.message) for w in c]
    ap = os.path.join(tp._TMP, "lw_app_%d.py" % tag)
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_lw_units_%d_%d" % (tag, next(_SEQ)))
    with warnings.catch_warnings(record=True) as c:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _Figure)]
    assert len(figs) == 1
    return figs[0], [str(w.message) for w in list(built) + list(c)]


def _glyph_widths(fig, kind):
    return [r.glyph.line_width for r in fig.renderers
            if hasattr(r, "glyph") and type(r.glyph).__name__ == kind]


def _spans(fig):
    return [a.line_width for a in fig.center if type(a).__name__ == "Span"]


def _site(mode, site, value, scheme=""):
    """(width, warnings) of the one width *site* draws for *value*
    (None = no option)."""
    o = {} if value is None else None
    if site == "line":
        fig, w = _figure(mode, [plot_for("line", o if o is not None
                                         else {"lwidth": value})],
                         scheme=scheme)
        return _glyph_widths(fig, "Line")[0], w
    if site == "clwidth":
        fig, w = _figure(mode, [plot_for("connected", o if o is not None
                                         else {"clwidth": value})],
                         scheme=scheme)
        return _glyph_widths(fig, "Line")[0], w
    if site == "mlwidth":
        fig, w = _figure(mode, [plot_for("scatter", o if o is not None
                                         else {"mlwidth": value})],
                         scheme=scheme)
        return _glyph_widths(fig, "Scatter")[0], w
    if site == "alwidth":
        fig, w = _figure(mode, [plot_for("lfitci", o if o is not None
                                         else {"alwidth": value})],
                         scheme=scheme)
        return _glyph_widths(fig, "Patch")[0], w
    if site == "bar":
        fig, w = _figure(mode, [plot_for("bar", o if o is not None
                                         else {"lwidth": value})],
                         scheme=scheme)
        return _glyph_widths(fig, "VBar")[0], w
    if site == "xline":
        go = {"xline": "20" if value is None else "20, lwidth(%s)" % value}
        fig, w = _figure(mode, [plot_for("line")], go=go, scheme=scheme)
        return _spans(fig)[0], w
    if site == "plotregion":
        go = None if value is None else {"plotregion": "lwidth(%s)" % value}
        fig, w = _figure(mode, [plot_for("line")], go=go, scheme=scheme)
        return fig.outline_line_width, w
    raise AssertionError(site)


def _width_notes(ws):
    return [m for m in ws if "line width" in m]


_SITES = ["line", "clwidth", "mlwidth", "alwidth", "bar", "xline",
          "plotregion"]


class TestTheUnitFunctions:
    def test_line_px_floors_and_converts(self):
        assert T.line_px(0) == 0.0
        assert T.line_px(0.0288) == pytest.approx(0.4)
        assert T.line_px(0.864) == pytest.approx(1.152)
        with pytest.raises(ValueError):
            T.line_px(-1)
        with pytest.raises(ValueError):
            T.line_px(float("nan"))


_LADDER = {"none": 0.0, "vvvthin": 0.4, "vvthin": 0.4, "vthin": 0.576,
           "thin": 0.768, "medthin": 0.96, "medium": 1.152,
           "medthick": 1.728, "thick": 3.072, "vthick": 5.376,
           "vvthick": 9.984, "vvvthick": 16.128}


class TestTheLadderIsStatas:
    def test_each_keyword_is_its_stata_units(self):
        for kw in sorted(_LADDER):
            assert T.translate_lwidth(kw) == pytest.approx(_LADDER[kw]), kw

    def test_ratios_to_medium_are_statas(self):
        lad = _truth()["ladder"]
        med = lad["medium"]["setting"]
        for kw, rec in lad.items():
            if kw in ("none", "vvvthin", "vvthin"):
                continue
            assert (T.translate_lwidth(kw) / T.translate_lwidth("medium")
                    == pytest.approx(rec["setting"] / med)), kw


class TestTheFormsAgainstTwoway:
    def test_each_form_draws_twoways_ratio_to_the_default(self):
        """Every lower-case form of the fixture, as dash's px over its
        medium against twoway's stroke over its default line (s2color),
        within 1% (a non-zero stroke floored at 0.3 pt on both sides)."""
        t = _truth()
        assert t["floor_pt"] == 0.3
        base = t["forms"]["default"]["stroke_pt"]
        med = T.translate_lwidth("medium")
        for fid, rec in t["forms"].items():
            v = rec["value"]
            if fid == "default" or v != v.lower() or rec["rc"] != 0:
                continue
            got = T.translate_lwidth(v) / med
            assert got == pytest.approx(rec["stroke_pt"] / base,
                                        rel=0.01, abs=1e-9), v


class TestNumbersAreStataUnits:
    def test_a_number_is_relative_units(self):
        assert T.translate_lwidth(".3") == pytest.approx(1.152)
        assert T.translate_lwidth("2") == pytest.approx(7.68)
        assert T.translate_lwidth("1e-7") == pytest.approx(0.4)

    def test_a_scheme_number_and_its_keyword_agree(self, tmp_path,
                                                   monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "lwnum.scheme").write_text(
            "#include s2color\nlinewidth p .8\n", encoding="utf-8")
        (tmp_path / "lwkw.scheme").write_text(
            "#include s2color\nlinewidth p thick\n", encoding="utf-8")
        a = dr.SchemeParser("lwnum").default_line_width
        b = dr.SchemeParser("lwkw").default_line_width
        assert a == pytest.approx(b) == pytest.approx(3.072)


class TestAbsoluteUnits:
    def test_points_inches_centimetres_and_rs(self):
        assert T.translate_lwidth("1pt") == pytest.approx(4 / 3)
        assert T.translate_lwidth("1in") == pytest.approx(96.0)
        assert T.translate_lwidth(".5cm") == pytest.approx(18.898, rel=1e-4)
        assert T.translate_lwidth("1rs") == pytest.approx(3.84)
        assert T.translate_lwidth("10000rs") == pytest.approx(38400.0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_reference_length_scales_them(self, mode):
        w, _ = _site(mode, "line", "1pt", scheme="economist")
        d, _ = _site(mode, "line", None, scheme="economist")
        assert w / d == pytest.approx(10.00 / 19.01, rel=0.01)


class TestTheMultiplier:
    @pytest.mark.parametrize("mode", _MODES)
    def test_star_multiplies_the_site_default(self, mode):
        want = {"line": 2.304, "mlwidth": 2.304, "bar": 1.536,
                "alwidth": 2.304, "xline": 2.304, "plotregion": 1.536}
        for site, px in want.items():
            w, ws = _site(mode, site, "*2")
            assert w == pytest.approx(px), site
            assert not _width_notes(ws), (site, ws)
        w, _ = _site(mode, "line", "*2", scheme="economist")
        assert w == pytest.approx(9.216)
        w, _ = _site(mode, "line", "*0")
        assert w == 0.0


class TestVvvthinAndNone:
    @pytest.mark.parametrize("mode", _MODES)
    def test_vvvthin_is_the_hairline(self, mode):
        w, ws = _site(mode, "line", "vvvthin")
        assert w == pytest.approx(0.4)
        assert not _width_notes(ws)

    @pytest.mark.parametrize("mode", _MODES)
    def test_none_draws_nothing(self, mode):
        for site in ("line", "clwidth", "mlwidth", "alwidth", "xline",
                     "plotregion"):
            w, ws = _site(mode, site, "none")
            assert w == 0.0, site
            assert not _width_notes(ws), (site, ws)


class TestTheHairlineFloor:
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_width_below_0_3pt_is_drawn_at_it(self, mode):
        for v in ("vvthin", "1e-7"):
            w, _ = _site(mode, "line", v)
            assert w == pytest.approx(0.4), v
        w, _ = _site(mode, "bar", None, scheme="economist")
        assert w == pytest.approx(0.4)


class TestNamesAreCaseSensitive:
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_capitalised_name_is_noted_and_the_default_drawn(self, mode):
        for v in ("THICK", "Thick", "MEDIUM"):
            w, ws = _site(mode, "line", v)
            assert w == pytest.approx(1.152), v
            assert len([m for m in _width_notes(ws) if v in m]) == 1, ws

    def test_a_capitalised_scheme_keyword_is_noted(self, tmp_path,
                                                   monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "lwcase.scheme").write_text(
            "#include s2color\nlinewidth minor_grid THICK\n",
            encoding="utf-8")
        with warnings.catch_warnings(record=True) as c:
            warnings.simplefilter("always")
            sp = dr.SchemeParser("lwcase")
        assert sp.minor_grid_line_width == pytest.approx(
            T.translate_lwidth("thin"))
        notes = [str(w.message) for w in c
                 if str(w.message).startswith("dash scheme:")
                 and "linewidth minor_grid" in str(w.message)]
        assert len(notes) == 1, [str(w.message) for w in c]


class TestTheDefaultLine:
    def test_each_shipped_scheme_draws_statas_default(self):
        lad = _truth()["ladder"]
        for name in sorted(dr.SchemeParser._BUILTIN_NAMES):
            sp = dr.SchemeParser(name)
            raw = sp._props.get("linewidth p", "medium").strip()
            units = (lad[raw]["setting"] if raw in lad else float(raw))
            assert sp.default_line_width == pytest.approx(
                T.line_px(units * 2.88)), name
        assert dr.SchemeParser("s2color").default_line_width == \
            pytest.approx(1.152)


class TestEveryLineSiteBothModes:
    @pytest.mark.parametrize("mode", _MODES)
    def test_thick_at_every_site(self, mode):
        for site in _SITES:
            w, _ = _site(mode, site, "thick")
            assert w == pytest.approx(3.072), site

    @pytest.mark.parametrize("mode", _MODES)
    def test_1pt_at_every_site(self, mode):
        for site in _SITES:
            w, ws = _site(mode, site, "1pt")
            assert w == pytest.approx(4 / 3, rel=1e-4), site
            assert not _width_notes(ws), (site, ws)


class TestTheRendererBound:
    @pytest.mark.parametrize("mode", _MODES)
    def test_10000_units_is_drawn_and_more_is_noted(self, mode):
        w, _ = _site(mode, "line", "10000rs")
        assert w == pytest.approx(38400.0)
        w, ws = _site(mode, "line", "*40000")
        assert w == pytest.approx(1.152)
        assert len([m for m in ws if "lwidth(*40000)" in m]) == 1, ws


class TestTheRegionAndReflineDefaults:
    def test_region_star_multiplies_the_default_it_is_given(self):
        assert dr._extract_region_lwidth(
            "lwidth(*2)", default_px=3.0) == pytest.approx(6.0)
        assert dr._extract_region_lwidth("lwidth(*2)") == pytest.approx(
            1.536)

    def test_refline_without_a_scheme_is_medium(self):
        from bokeh.models import Span
        fig = _Figure()
        dr._dash_refline_draw(fig, "xline", "height", [1.0], {}, None, Span)
        assert _spans(fig) == [pytest.approx(1.152)]


class TestTheBandOutline:
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_wide_alwidth_is_not_dropped(self, mode):
        w, _ = _site(mode, "alwidth", "300")
        assert w == pytest.approx(1152.0)


# ---- guards (green before and after) -------------------------------------

class TestEmptyOptionsChangeNothing:
    @pytest.mark.parametrize("mode", _MODES)
    def test_every_line_type_draws_the_schemes_width(self, mode):
        sp = dr.SchemeParser("s2color")
        for t in ("line", "connected", "lfit", "qfit", "lowess", "spike",
                  "rline", "rspike", "pcspike"):
            fig, ws = _figure(mode, [plot_for(t)])
            got = [r.glyph.line_width for r in fig.renderers
                   if hasattr(r, "glyph")
                   and type(r.glyph).__name__ in ("Line", "Segment")]
            assert got, t
            assert all(g == pytest.approx(sp.plot_line_width(0, "line"))
                       or g == pytest.approx(sp.default_line_width)
                       for g in got), (t, got)
            assert not _width_notes(ws), (t, ws)


class TestAnUnknownNameKeepsTheSchemeDefault:
    @pytest.mark.parametrize("mode", _MODES)
    def test_economist_abc_is_the_schemes_width(self, mode):
        d, _ = _site(mode, "line", None, scheme="economist")
        w, ws = _site(mode, "line", "abc", scheme="economist")
        assert w == pytest.approx(d)
        assert len([m for m in _width_notes(ws) if "abc" in m]) == 1


class TestAfterAFilterMove:
    def test_served_widths_survive_a_move(self):
        _, filt, action, _ = tp._MOVES[0]
        spec = tp._spec([plot_for("line", {"lwidth": "thick"})],
                        {"filter": filt})
        doc, _ = tp._served(spec)

        def widths():
            return sorted(r.glyph.line_width for m in doc.roots
                          for r in m.references()
                          if type(r).__name__ == "GlyphRenderer"
                          and type(r.glyph).__name__ == "Line")
        before = widths()
        w = [x for x in tp._widgets_of(doc)
             if type(x).__name__ == action[0]][0]
        raw = [v for v, lab in w.options if lab == action[1]][0]
        tp._fire(w, raw)
        assert widths() == before and before

    def test_no_saved_script_writes_a_width(self):
        _, filt, _, _ = tp._MOVES[0]
        spec = tp._spec([plot_for("line", {"lwidth": "thick"})],
                        {"filter": filt})
        r, _ = tp._standalone(spec)
        codes = [m.code for m in r._last_layout_root.references()
                 if type(m).__name__ == "CustomJS"]
        assert codes
        assert all("line_width" not in c for c in codes)
        assert "line_width" not in dr._FILTER_JS


class TestHostileWidths:
    def test_never_raises_out_and_is_linear(self):
        for value in ("x" * 1_000_000, "<script>", "*1e308", "nan", "inf",
                      "1e400pt", "*" + "9" * 500, "-0"):
            t0 = time.perf_counter()
            try:
                w = T.translate_lwidth(value)
            except ValueError:
                w = None
            assert time.perf_counter() - t0 < 0.1, value[:12]
            if w is not None:
                assert math.isfinite(w) and w >= 0, value[:12]


class TestNothingSerialisesAWidthAsText:
    def test_widths_are_numbers_in_the_page(self):
        spec = tp._spec([plot_for("line", {"lwidth": "*2"})], None,
                        {"xline": "20, lwidth(1pt)"})
        _, _, page = tp._standalone_page(spec)
        vals = re.findall(r'"line_width":\s*("[^"]*"|\{[^}]*\}|[^,}\]]+)',
                          page)
        assert vals
        for v in vals:
            v = v.strip()
            if v.startswith("{"):
                assert re.search(r'"value":\s*[0-9.eE+-]+', v), v
            else:
                float(v)


# ---- dash.ado contract ---------------------------------------------------

class TestTheLineWidthRulesAreUnitAware:
    def test_the_four_line_options_carry_u(self):
        from test_option_validation import _parse_rules, _BLOCK
        rules = _parse_rules(_BLOCK)
        got = {o: ps for o, k, ps, ts in rules if "u" in ps}
        assert got == {o: ("0", "10000", "u") for o in
                       ("lwidth", "mlwidth", "clwidth", "alwidth")}

    def test_the_validator_quotes_twoways_words(self):
        from test_abbreviations import _program_body
        with open(os.path.join(os.path.dirname(_HERE), "dash.ado"),
                  encoding="utf-8") as fh:
            body = _program_body(fh.read(), "_dash_validate_value")
        words = "gm_linewidth must be between 0.000 and  1.0e+04"
        assert body.count(words) == 1
        i = body.index('if "`p3\'" == "u"')
        assert i < body.index(words)
