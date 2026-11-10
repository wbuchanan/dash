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
from probe_groups import probe_params, representative  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "symbol_pattern_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

T = dr.OptionTranslator

#: The Bokeh shape dash draws each Stata name with, and the full-size
#: Stata symbol dash draws that shape for at factor 1 (the factor of a
#: name is its measured height over that symbol's).
# Flipped (WP-47 PIC-2): diamond, plus, inverted_triangle and triangle for
# the arrows were wrong because twoway's D is a square on its point, V an
# open three-vertex path, + two lines and the arrows a head on a shaft
# (dash's @dash_* defs markers and Bokeh's cross draw them).
SHAPE = {
    "O": ("circle", "O"), "circle": ("circle", "O"), "Oh": ("circle", "O"),
    "o": ("circle", "O"), "oh": ("circle", "O"),
    "smcircle": ("circle", "O"), "smcircle_hollow": ("circle", "O"),
    "D": ("@dash_diamond", "D"), "Dh": ("@dash_diamond", "D"),
    "d": ("@dash_diamond", "D"), "dh": ("@dash_diamond", "D"),
    "smdiamond": ("@dash_diamond", "D"),
    "smdiamond_hollow": ("@dash_diamond", "D"),
    "S": ("square", "S"), "Sh": ("square", "S"), "s": ("square", "S"),
    "sh": ("square", "S"), "smsquare": ("square", "S"),
    "smsquare_hollow": ("square", "S"),
    "T": ("triangle", "T"), "Th": ("triangle", "T"), "t": ("triangle", "T"),
    "th": ("triangle", "T"), "smtriangle": ("triangle", "T"),
    "smtriangle_hollow": ("triangle", "T"),
    "+": ("cross", "plus"), "plus": ("cross", "plus"),
    "smplus": ("cross", "plus"),
    "X": ("x", "X"), "x": ("x", "X"), "smx": ("x", "X"), "lgx": ("x", "X"),
    "V": ("@dash_chevron", "V"), "v": ("@dash_chevron", "V"),
    "smv": ("@dash_chevron", "V"),
    "arrow": ("@dash_arrow", "arrow"), "a": ("@dash_arrow", "arrow"),
    "arrowf": ("@dash_arrowf", "arrowf"), "A": ("@dash_arrowf", "arrowf"),
    "pipe": ("dash", "O"), "|": ("dash", "O"),
}
#: Shapes with an inside, whose hollow form is the outline only.
_FILLABLE = {"circle", "@dash_diamond", "square", "triangle"}
NOT_STATA = ("star", "asterisk", "hexagon", "hexagon_hollow", "dot",
             "CIRCLE", "Circle")
SMALL = ("o", "oh", "d", "dh", "s", "sh", "t", "th", "x", "v", "smx", "smv")


def _rec(name):
    return TRUTH["sym." + name]


#: The height of each Bokeh marker drawn at size 1 (BokehJS: a circle's
#: diameter, a square's and a diamond's height, a triangle's sqrt(3)/2, an
#: x's arms at 45 degrees sqrt(1/2), a dash's length).
BOKEH_H = {"circle": 1.0, "square": 1.0, "@dash_diamond": 1.0, "cross": 1.0,
           "triangle": math.sqrt(3) / 2, "@dash_chevron": 1.0,
           "@dash_arrow": 1.0, "@dash_arrowf": 1.0,
           "x": math.sqrt(0.5), "dash": 1.0}
#: Each shape's width at size 1 (WP-47 PIC-2): the chevron's sides at 60
#: degrees, the arrows' heads 2/3 and 1/2 of their height across.
BOKEH_W = {"circle": 1.0, "square": 1.0, "@dash_diamond": 1.0, "cross": 1.0,
           "triangle": 1.0, "@dash_chevron": 2 / math.sqrt(3),
           "@dash_arrow": 2 / 3, "@dash_arrowf": 0.5, "x": math.sqrt(0.5)}


def _factor(name):
    """The size factor that draws *name* at twoway's height: its measured
    height over O's, over its Bokeh shape's height at size 1 (WP-31 E1)."""
    return (_rec(name)["bbox_h"] / _rec("O")["bbox_h"]
            / BOKEH_H[SHAPE[name][0]])


def _sc(**o):
    return plot_for("scatter", o)


def _drawn(mode, plots, scheme="s2color"):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    ms = [r.glyph for r in drawn_renderers(d.figures[0])
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



#: Symbols per node and the gate's served subset (pytest speed,
#: 22oct2026): the first symbol of each Bokeh marker and height factor
#: (symbols that share both take the same branch) and every fourth symbol
#: of the rest; release checks every symbol served.
_HEIGHT_PARAMS = probe_params(sorted(SHAPE), representative(
    sorted(SHAPE), lambda n: (SHAPE[n][0], round(_factor(n), 3)), stride=4),
    size=8, saved_size=41, modes=MODES)

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
        assert g.size / f.size == pytest.approx(
            _factor(name) / _factor(full), abs=0.01)
        assert _factor(name) / _factor(full) < 0.8

    @pytest.mark.parametrize("mode", MODES)
    def test_V_is_the_open_chevron(self, mode):
        """V is v's shape at full size; both are outlines only."""
        assert _rec("V")["filled"] is _rec("v")["filled"] is False
        (big,), _ = _drawn(mode, [_sc(msymbol="V")])
        (small,), _ = _drawn(mode, [_sc(msymbol="v")])
        # Flipped (WP-47 PIC-2): inverted_triangle was wrong because
        # twoway's V is an open three-vertex path.
        assert _rec("V")["closed"] is False and _rec("V")["vertices"] == 3
        assert big.marker == small.marker == "@dash_chevron"
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

    @pytest.mark.parametrize("mode,group", _HEIGHT_PARAMS)
    def test_every_symbol_is_twoways_height(self, mode, group):
        """Each symbol is drawn as tall, against O, as twoway draws it:
        the diamond 1.42 of O, the triangles and arrows as tall as O (a
        Bokeh triangle is sqrt(3)/2 of its size), lgx 1.41 of X."""
        (o,), _ = _drawn(mode, [_sc(msymbol="O")])
        bad = []
        for name in group:
            (g,), _ = _drawn(mode, [_sc(msymbol=name)])
            if abs(g.size / o.size - _factor(name)) > 0.01:
                bad.append((name, round(g.size / o.size, 4),
                            round(_factor(name), 4)))
            # And as wide (WP-47 PIC-2: Bokeh's diamond was 2/3 as wide);
            # the vertical bar's width is its line's.
            sh = SHAPE[name][0]
            if sh in BOKEH_W:
                want = _rec(name)["bbox_w"] / _rec("O")["bbox_w"]
                got = g.size * BOKEH_W[sh] / o.size
                if abs(got - want) > 0.05 * want:
                    bad.append((name, "width", round(got, 4),
                                round(want, 4)))
        assert not bad, bad

    @pytest.mark.parametrize("mode", MODES)
    def test_a_schemes_point_and_pipe(self, mode, tmp_path, monkeypatch):
        """A scheme's symbol p1 point draws the one-pixel dot and p2 pipe
        the vertical bar, as msymbol() does."""
        from test_scheme_review_fixes import _user_scheme
        name = _user_scheme(tmp_path, monkeypatch, "u40pt.scheme",
                            ["#include s2color", "symbol p1 point",
                             "symbol p2 pipe", "symbol p3 D"])
        ms, _ = _drawn(mode, [_sc(), _sc(), _sc()], scheme=name[:-7])
        (o,), _ = _drawn(mode, [_sc(msymbol="O")])
        assert (ms[0].marker, ms[0].size, ms[0].line_width) == \
            ("circle", 1.0, 0.0)
        assert ms[1].marker == "dash"
        assert ms[1].angle == pytest.approx(math.pi / 2)
        assert ms[2].size / o.size == pytest.approx(_factor("D"), abs=0.01)

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
