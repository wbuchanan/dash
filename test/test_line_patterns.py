"""Line patterns as twoway draws them (WP-31 E2, with E12's pattern half).

Measured in StataNow 19.5 (`graph export' SVG, 16oct2026;
test/fixtures/symbol_pattern_truth.json, scripts/extract_symbol_pattern_truth.do):

- a named pattern is its style file's numbers in Stata relative units
  (1 rs = min(width, height)/100 of the graph), whatever the pen width
  (vvthin, medium, thick and vthick draw the same dashes) and whatever
  the graph's size (5.5 x 4, 8 x 8 and 8 x 2 alike): dash is 2 rs on,
  1 rs off; dash draws 1 rs as 3.84 px, as every other relative size;
- a formula in lpattern() ("-.", "--..", "_", "-_-", "_--_#") is decoded
  as linepattern.class _DecodePat decodes it; "#", "l" and "ll" are solid;
- an odd-length pattern (longdash_shortdash) ends its period with no gap;
- "-x", "Dash", "DASH" and shortdot are noted ("named style ... not found
  in class linepattern") and drawn solid: names are case-sensitive;
- a scheme's linepattern p1 holding a formula draws solid, silently, and
  one holding an unknown name is noted;
- mlpattern() is accepted and twoway draws the marker outline solid
  (the style is set; neither the SVG nor the PNG renderer dashes it).

dash drew fixed pixel lists ([8, 4] for dash, [2, 4] for dot), refused
every formula, drew "-_-" as dash_dot, lower-cased Dash to dash, and named
mlpattern() as not supported.
"""

import inspect
import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw, _props_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "symbol_pattern_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

T = dr.OptionTranslator
#: dash's pixels per Stata relative unit.
PX_PER_RS = T.PT_PER_RS * T.PX_PER_PT

FILES = ("blank", "dash", "dash_3dot", "dash_dot", "dash_dot_dot", "dot",
         "longdash", "longdash_3dot", "longdash_dot", "longdash_dot_dot",
         "longdash_shortdash", "shortdash", "shortdash_dot",
         "shortdash_dot_dot", "solid", "tight_dot", "vshortdash")
#: The formula probes: f1..f11 in the extractor's order.
FORMULAS = {f"f{i}": TRUTH[f"pat.formula.f{i}"]["text"] for i in range(1, 12)}
VALID = {k: v for k, v in FORMULAS.items() if TRUTH[f"pat.formula.{k}"]["note"] == ""}
NOTED = {k: v for k, v in FORMULAS.items() if TRUTH[f"pat.formula.{k}"]["note"]}


def _period_matches(px, runs_rs, tol=0.6):
    """True when the drawn on/off list (px), repeated, gives twoway's runs
    (rs) to the whole pixel: Bokeh's dash pattern takes integers, so each
    length is twoway's rounded (a run under a pixel draws one), *tol* px
    allowing for the SVG's two decimals.  An empty list is solid: twoway
    wrote no dashes."""
    if not px:
        return runs_rs == []
    if not all(isinstance(v, int) for v in px):
        return False
    want = [r * PX_PER_RS for r in runs_rs]
    got = [px[i % len(px)] for i in range(len(want))]
    return all(abs(a - b) <= tol or (b < 1 and a == 1)
               for a, b in zip(got, want))


def _lines(mode, plots, scheme="s2color"):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    gs = [r.glyph for r in d.figures[0].renderers
          if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)]
    return gs, d.warnings


def _line(**o):
    return plot_for("line", o)


class TestFormulas:
    def test_decodepat_table(self):
        for k, text in VALID.items():
            nums = T.lpattern_formula(text)
            assert nums is not None, text
            assert _period_matches([max(1, round(v * PX_PER_RS)) for v in nums],
                                   TRUTH[f"pat.formula.{k}"]["runs_rs"]), \
                (text, nums, TRUTH[f"pat.formula.{k}"]["runs_rs"][:8])

    def test_l_is_solid(self):
        for text in ("l", "ll", "#", "lll "):
            assert T.lpattern_formula(text) == []

    def test_invalid_char_is_none(self):
        for text in ("-x", "Dash", "", "--a", "1 2"):
            assert T.lpattern_formula(text) is None

    def test_bounded_length(self):
        assert T.lpattern_formula("-" * 200) is not None
        assert T.lpattern_formula("-" * 201) is None


class TestNamedPatterns:
    @pytest.mark.parametrize("name", FILES)
    def test_every_file_name(self, name):
        rec = TRUTH[f"pat.{name}"]
        assert rec["rc"] == 0 and rec["note"] == ""
        px = T.translate_lpattern(name)
        if name == "blank":
            assert rec["segments"] == 0 and px[0] == 0.0
            return
        assert _period_matches(list(px), rec["runs_rs"]), (name, px)

    @pytest.mark.parametrize("w", ["vvthin", "medium", "thick", "vthick"])
    def test_the_pen_width_is_not_the_unit(self, w):
        assert TRUTH[f"pat.dash_w.{w}"]["runs_rs"] == \
            TRUTH["pat.dash_w.medium"]["runs_rs"]
        assert TRUTH["unit_rs_per_number"][w] == pytest.approx(1.0, abs=0.01)
        for mode in MODES:
            gs, _ = _lines(mode, [_line(lpattern="dash", lwidth=w)])
            assert _period_matches(list(gs[0].line_dash),
                                   TRUTH[f"pat.dash_w.{w}"]["runs_rs"])

    def test_the_graph_size_is_not_the_unit(self):
        for k in ("x8y8", "x8y2"):
            assert _period_matches(T.translate_lpattern("dash"),
                                   TRUTH[f"pat.dash_size.{k}"]["runs_rs"])

    @pytest.mark.parametrize("key", sorted(NOTED) + ["shortdot"])
    def test_unknown_is_noted_and_solid(self, key):
        text = FORMULAS.get(key, key)
        rec = TRUTH[f"pat.formula.{key}" if key in FORMULAS else f"pat.{key}"]
        assert rec["note"] == \
            f"named style {text} not found in class linepattern"
        assert rec["segments"] == 0
        with pytest.raises(ValueError):
            T.translate_lpattern(text)

    def test_case_is_twoways(self):
        """Dash and DASH are noted by twoway (E12)."""
        for text in ("Dash", "DASH"):
            with pytest.raises(ValueError):
                T.translate_lpattern(text)

    def test_a_quoted_formula_is_its_text(self):
        assert T.translate_lpattern('"-."') == T.translate_lpattern("-.")


@pytest.mark.parametrize("mode", MODES)
class TestDrawn:
    def test_formula_on_a_line(self, mode):
        gs, msgs = _lines(mode, [_line(lpattern="-_-", lwidth="thick")])
        assert _period_matches(list(gs[0].line_dash),
                               TRUTH["pat.formula.f5"]["runs_rs"])
        assert not [m for m in msgs if "pattern" in m]

    def test_unknown_noted_once(self, mode):
        gs, msgs = _lines(mode, [_line(lpattern="Dash")])
        assert list(gs[0].line_dash) == []
        assert len([m for m in msgs if "lpattern(Dash)" in m]) == 1


class TestSchemePatterns:
    def test_formula_in_scheme_is_solid_silently(self, recwarn):
        """twoway draws a scheme's formula solid with no note."""
        for k in ("s2", "s3"):
            assert TRUTH[f"pat.scheme.{k}"]["segments"] == 0
            assert TRUTH[f"pat.scheme.{k}"]["note"] == ""
        for v in ('"--.."', "--.."):
            sp = _props_scheme({"linepattern p1": v})
            assert sp.p_line_patterns[0] == []
        assert not [w for w in recwarn if "pattern" in str(w.message)]

    def test_a_name_in_scheme(self):
        assert _period_matches(
            _props_scheme({"linepattern p1": "dash"}).p_line_patterns[0],
            TRUTH["pat.scheme.s1"]["runs_rs"])

    def test_invalid_notes_once(self):
        assert TRUTH["pat.scheme.s5"]["note"] == \
            "named style Dash not found in class linepattern"
        with pytest.warns(UserWarning, match="Dash"):
            sp = _props_scheme({"linepattern p1": "Dash"})
        assert sp.p_line_patterns[0] == []


@pytest.mark.parametrize("mode", MODES)
class TestMlpattern:
    def test_outline_is_twoways(self, mode):
        """twoway sets the outline's pattern but draws it solid."""
        for p in ("dash", "dot"):
            rec = TRUTH[f"mlp.{p}"]
            assert rec["setting"] == p and rec["dasharray"] == []
            assert rec.get("png_differs_from_solid") is False
            gs, msgs = _lines(mode, [plot_for(
                "scatter", {"msymbol": "Oh", "mlpattern": p})])
            assert list(gs[0].line_dash) == []
            assert not [m for m in msgs if "mlpattern" in m]

    def test_an_unknown_name_is_noted(self, mode):
        gs, msgs = _lines(mode, [plot_for(
            "scatter", {"msymbol": "Oh", "mlpattern": "Dash"})])
        assert len([m for m in msgs if "mlpattern(Dash)" in m]) == 1


def test_mlpattern_is_not_pending():
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "dash.ado"), encoding="utf-8") as fh:
        ado = fh.read()
    assert "_dash_pending' mlpattern" not in ado
    with open(os.path.join(root, "dash.sthlp"), encoding="utf-8") as fh:
        help_ = fh.read()
    unsup = help_[help_.index("Unsupported"):]
    assert "mlpattern" not in unsup.split("{marker", 1)[0]


def test_translate_lpattern_takes_one_value():
    """The unit is the relative size, not the pen: no width argument."""
    assert list(inspect.signature(T.translate_lpattern).parameters) == \
        ["value"]
