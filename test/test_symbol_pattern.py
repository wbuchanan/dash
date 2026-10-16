"""Marker symbols as twoway draws them (WP-31 E1, with E12's symbol half).

Measured in StataNow 19.5 (`graph export' SVG, 16oct2026;
test/fixtures/symbol_pattern_truth.json, scripts/extract_symbol_pattern_truth.do):

- every symbol of Stata's table and its synonyms draws (arrow, arrowf, A,
  a, pipe, |, point, p, V and the shorthands): arrow/a is an open head on
  a shaft, arrowf/A a filled head on a shaft, as tall as O; pipe/| is a
  vertical bar as tall as O, turned further by msangle(); point/p is a
  one-unit dot whatever msize() says;
- V is the full-size open chevron and v (= smv) the small one; x (= smx)
  is the small cross, X the full one and lgx the large one; o d s t and
  their hollow forms are the sm* symbols;
- star, asterisk, hexagon, hexagon_hollow and dot are not Stata symbols:
  twoway notes "named style ... not found in class symbol" and draws the
  scheme's symbol; so it does for CIRCLE and Circle (names are
  case-sensitive).

dash drew pipe horizontal, point at full size, V filled, the shorthands
at full size, refused the arrows, pipe's | and V, drew star and its kin,
and lower-cased CIRCLE to circle.
"""

import json
import math
import os
import sys

import pytest
from bokeh.models import GlyphRenderer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "symbol_pattern_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

T = dr.OptionTranslator

#: The Bokeh shape dash draws each Stata name with, and the full-size
#: Stata symbol dash draws that shape for at factor 1 (the factor of a
#: name is its measured height over that symbol's).
SHAPE = {
    "O": ("circle", "O"), "circle": ("circle", "O"), "Oh": ("circle", "O"),
    "o": ("circle", "O"), "oh": ("circle", "O"),
    "smcircle": ("circle", "O"), "smcircle_hollow": ("circle", "O"),
    "D": ("diamond", "D"), "Dh": ("diamond", "D"), "d": ("diamond", "D"),
    "dh": ("diamond", "D"), "smdiamond": ("diamond", "D"),
    "smdiamond_hollow": ("diamond", "D"),
    "S": ("square", "S"), "Sh": ("square", "S"), "s": ("square", "S"),
    "sh": ("square", "S"), "smsquare": ("square", "S"),
    "smsquare_hollow": ("square", "S"),
    "T": ("triangle", "T"), "Th": ("triangle", "T"), "t": ("triangle", "T"),
    "th": ("triangle", "T"), "smtriangle": ("triangle", "T"),
    "smtriangle_hollow": ("triangle", "T"),
    "+": ("plus", "plus"), "plus": ("plus", "plus"),
    "smplus": ("plus", "plus"),
    "X": ("x", "X"), "x": ("x", "X"), "smx": ("x", "X"), "lgx": ("x", "X"),
    "V": ("inverted_triangle", "V"), "v": ("inverted_triangle", "V"),
    "smv": ("inverted_triangle", "V"),
    "arrow": ("triangle", "T"), "a": ("triangle", "T"),
    "arrowf": ("triangle", "T"), "A": ("triangle", "T"),
    "pipe": ("dash", "O"), "|": ("dash", "O"),
}
#: Shapes with an inside, whose hollow form is the outline only.
_FILLABLE = {"circle", "diamond", "square", "triangle", "inverted_triangle"}
NOT_STATA = ("star", "asterisk", "hexagon", "hexagon_hollow", "dot",
             "CIRCLE", "Circle")
SMALL = ("o", "oh", "d", "dh", "s", "sh", "t", "th", "x", "v", "smx", "smv")


def _rec(name):
    return TRUTH["sym." + name]


def _factor(name):
    return _rec(name)["factor"] / _rec(SHAPE[name][1])["factor"]


def _sc(**o):
    return plot_for("scatter", o)


def _drawn(mode, plots, scheme="s2color"):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    ms = [r.glyph for r in d.figures[0].renderers
          if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)
          and type(r.glyph).__name__ == "Scatter"]
    return ms, d.warnings


class TestTheFixture:
    def test_meta(self):
        assert sorted(TRUTH["_meta"]) >= sorted(
            ["born_date", "dash_commit", "extracted", "source",
             "stata_version"])
        assert TRUTH["_meta"]["source"] == \
            "scripts/extract_symbol_pattern_truth.do"

    def test_every_probe(self):
        want = set(SHAPE) | set(NOT_STATA) | {
            "point", "p", "point_large", "pipe_angle45"}
        assert not sorted(w for w in want if "sym." + w not in TRUTH)
        assert all(_rec(n)["rc"] == 0 for n in want)


class TestSymbols:
    @pytest.mark.parametrize("name", sorted(SHAPE))
    def test_every_stata_symbol(self, name):
        """The shape, the hollowness and the size twoway draws, for every
        symbol and synonym of Stata's table."""
        rec = _rec(name)
        assert rec["note"] == ""
        marker, hollow, factor = T.symbol_traits(name, option=True)
        assert marker == SHAPE[name][0]
        if marker in _FILLABLE:
            assert hollow is (not rec["filled"]), name
        assert factor == pytest.approx(_factor(name), abs=0.01), name

    def test_arrowheads_point_up(self):
        assert {_rec(n)["apex"] for n in ("arrow", "a", "arrowf", "A")} \
            == {"up"}

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("name", NOT_STATA)
    def test_non_stata_names_note(self, mode, name):
        """twoway notes the name and draws the scheme's symbol."""
        assert _rec(name)["note"] == \
            f"named style {name} not found in class symbol"
        with pytest.raises(ValueError):
            T.translate_msymbol(name)
        (g,), msgs = _drawn(mode, [_sc(msymbol=name)])
        (ref,), _ = _drawn(mode, [_sc()])
        assert (g.marker, g.size, g.fill_alpha) == \
            (ref.marker, ref.size, ref.fill_alpha)
        hits = [m for m in msgs if "marker symbol" in m and name in m]
        assert len(hits) == 1, msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_pipe_is_vertical(self, mode):
        assert _rec("pipe")["bbox_w"] == 0.0 < _rec("pipe")["bbox_h"]
        for name in ("pipe", "|"):
            (g,), msgs = _drawn(mode, [_sc(msymbol=name)])
            assert g.marker == "dash"
            assert g.angle == pytest.approx(math.pi / 2)
            assert not [m for m in msgs if "symbol" in m]

    @pytest.mark.parametrize("mode", MODES)
    def test_pipe_keeps_msangle(self, mode):
        """twoway turns the vertical bar a further 45 degrees
        counter-clockwise (SVG rotate(-45))."""
        assert _rec("pipe_angle45")["transform"].startswith("rotate(-45")
        (g,), _ = _drawn(mode, [_sc(msymbol="pipe", msangle="45")])
        assert g.angle == pytest.approx(math.pi / 2 + math.pi / 4)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("msize", ["", "large"])
    def test_point_is_one_pixel(self, mode, msize):
        assert _rec("point")["bbox_h"] == _rec("point_large")["bbox_h"] \
            == _rec("p")["bbox_h"]
        assert _rec("point")["stroked"] is False
        for name in ("point", "p"):
            o = {"msymbol": name}
            if msize:
                o["msize"] = msize
            (g,), _ = _drawn(mode, [_sc(**o)])
            assert (g.marker, g.size, g.line_width) == ("circle", 1.0, 0.0)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("name", SMALL)
    def test_shorthands_are_small(self, mode, name):
        """o d s t x v and their hollow forms are the small symbols."""
        full = SHAPE[name][1]
        (g,), _ = _drawn(mode, [_sc(msymbol=name)])
        (f,), _ = _drawn(mode, [_sc(msymbol=full)])
        assert g.size / f.size == pytest.approx(_factor(name), abs=0.01)
        assert _factor(name) < 0.8

    @pytest.mark.parametrize("mode", MODES)
    def test_V_is_the_open_chevron(self, mode):
        """V is v's shape at full size; both are outlines only."""
        assert _rec("V")["filled"] is _rec("v")["filled"] is False
        (big,), _ = _drawn(mode, [_sc(msymbol="V")])
        (small,), _ = _drawn(mode, [_sc(msymbol="v")])
        assert big.marker == small.marker == "inverted_triangle"
        assert big.fill_alpha == small.fill_alpha == 0.0
        assert small.size / big.size == pytest.approx(0.75, abs=0.01)

    def test_case_is_twoways(self):
        """CIRCLE and Circle are noted by twoway; O and o are two symbols."""
        for name in ("CIRCLE", "Circle"):
            assert _rec(name)["note"]
            with pytest.raises(ValueError):
                T.symbol_traits(name)
        assert T.symbol_traits("O")[2] != T.symbol_traits("o")[2]

    def test_a_schemes_x_is_the_full_symbol(self):
        """In a scheme, x and v are symbol-x.style and symbol-v.style, the
        full symbols: s1mono's p5 x is X's size, p15 smx the small one
        (scheme_layer_truth.json); in msymbol() they are smx and smv."""
        with open(os.path.join(os.path.dirname(__file__), "fixtures",
                               "scheme_layer_truth.json"),
                  encoding="utf-8") as fh:
            ext = json.load(fh)["derived"]["s1mono_extent"]
        assert ext[4] == pytest.approx(_rec("X")["bbox_h"], abs=0.1)
        assert ext[14] == pytest.approx(_rec("x")["bbox_h"], abs=0.1)
        assert T.symbol_traits("x")[2] == 1.0
        assert T.symbol_traits("x", option=True)[2] == pytest.approx(
            _factor("x"), abs=0.01)

    def test_no_shipped_scheme_names_a_deleted_symbol(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        bad = []
        for f in sorted(os.listdir(root)):
            if not (f.startswith("dash-") and f.endswith(".scheme")):
                continue
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                for ln in fh:
                    w = ln.split()
                    if len(w) >= 3 and w[0] == "symbol":
                        try:
                            T.translate_msymbol(w[2])
                        except ValueError:
                            bad.append((f, w[1], w[2]))
        assert not bad, bad
