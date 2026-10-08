"""Hollow and small symbols, the symbol cycle on every marker type and the
marker colour keys (WP-30 P1.4a).

Measured in StataNow 19.5 (`graph export' SVG, 03oct2026;
test/fixtures/scheme_layer_truth.json): s1mono's p7-p10 (circle_hollow ..
triangle_hollow) are stroked only; its p11-p14 (smcircle .. smtriangle) are
0.707 of the full symbol (0.751 for smtriangle), with msize() too; under
s1mono the second layer of scatteri, rscatter, pcscatter, dropline and
rcapsym is p2's diamond; `msymbol(Oh) malpha(50)' and `pstyle(p7)
mfcolor(red)' stay hollow.  dash drew every scheme symbol filled and full
size, a circle on those five types, and refilled a hollow marker under
malpha().
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
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "scheme_layer_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

H = math.sqrt(0.5)
T = dr.OptionTranslator


def _markers(plots, scheme, mode):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    return [r.glyph for r in d.figures[0].renderers
            if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)
            and type(r.glyph).__name__ == "Scatter"]


def _sc(**o):
    return plot_for("scatter", o)


class TestSymbolTraits:
    def test_each_stata_name(self):
        cases = {"circle": ("circle", False, 1.0),
                 "Oh": ("circle", True, 1.0),
                 "smcircle": ("circle", False, H),
                 "smcircle_hollow": ("circle", True, H),
                 "smdiamond": ("diamond", False, H),
                 "smsquare": ("square", False, H),
                 "smplus": ("plus", False, H),
                 "smtriangle": ("triangle", False, 0.75),
                 "smx": ("x", False, 1.0), "o": ("circle", False, 1.0)}
        bad = [(n, T.symbol_traits(n)) for n, want in cases.items()
               if T.symbol_traits(n)[:2] != want[:2]
               or abs(T.symbol_traits(n)[2] - want[2]) > 1e-9]
        assert not bad, bad
        assert T.symbol_traits("smv")[2] == 1.0
        with pytest.raises(ValueError):
            T.symbol_traits("bogus")


class TestTheSchemeCycle:
    def test_s1mono_traits(self):
        sp = dr.SchemeParser("s1mono")
        assert sp.p_symbol_hollow == [False] * 6 + [True] * 4 + [False] * 5
        assert sp.p_symbol_factor == pytest.approx(
            [1.0] * 10 + [H, H, H, 0.75, 1.0], abs=1e-4)
        assert sp.default_symbol_traits(16) == ("diamond", False, 1.0)

    def test_colour_schemes_are_plain(self):
        bad = []
        for n in ("s2color", "stcolor", "sttrans", "economist", "s1color"):
            sp = dr.SchemeParser(n)
            if set(zip(sp.p_symbol_hollow, sp.p_symbol_factor)) != \
                    {(False, 1.0)}:
                bad.append(n)
        assert not bad, bad

    def test_the_marker_outline_chain(self):
        """`color p#markline' -> pmarkline -> p# -> p, with its opacity."""
        sp = dr.SchemeParser("sttrans")
        assert sp.default_markline(0) == ("#1a476f", pytest.approx(0.2))
        from test_scheme_resolution import _props_scheme
        sp = _props_scheme({"color p": "red", "color pmarkline": "blue%40"})
        assert sp.default_markline(3) == ("#0000ff", pytest.approx(0.4))


@pytest.mark.parametrize("mode", MODES)
class TestDrawnTraits:
    """The scheme's hollow and small symbols are checked against twoway in
    TestTwowaysSymbols; these are the user's msymbol() branches."""

    def test_a_user_symbol_replaces_the_scheme_s(self, mode):
        ms = _markers([_sc()] * 6 + [_sc(msymbol="O")], "s1mono", mode)
        assert ms[6].fill_alpha == 1.0

    def test_a_user_small_symbol(self, mode):
        for o in ({}, {"msize": "large"}):
            sm, full = (_markers([_sc(msymbol=s, **o)], "s2color", mode)[0]
                        for s in ("smcircle", "circle"))
            assert sm.size == pytest.approx(H * full.size), o


@pytest.mark.parametrize("mode", MODES)
class TestHollowStaysHollow:
    def test_malpha(self, mode):
        """malpha() refilled a hollow marker; the user's Oh and the
        scheme's p7 alike (mfcolor() is checked against twoway below)."""
        g = _markers([_sc(msymbol="Oh", malpha="50")], "s2color", mode)[0]
        assert (g.fill_alpha, g.line_alpha) == (0.0, pytest.approx(0.5))
        ms = _markers([_sc()] * 6 + [_sc(malpha="50")],
                      "s1mono", mode)
        assert ms[6].fill_alpha == 0.0


# ---------------------------------------------------------------------------
# twoway's own SVG: the symbol, sm, cycle and mark probes, one test per mode
# ---------------------------------------------------------------------------

#: twoway's drawn shape -> dash's Bokeh marker.
_SHAPE = {"circle": "circle", "diamond": "diamond", "square": "square",
          "triangle": "triangle", "x": "x", "plus": "plus",
          "v": "inverted_triangle"}
_FILLABLE = {"circle", "diamond", "square", "triangle"}
_CYCLE_PLOT = {"scatteri": "scatteri", "rscatter": "rscatter",
               "pcscatter": "pcscatter", "dropline": "dropline",
               "rcapsym": "rcapsym"}


def _check_layers(tw, ms, where, bad):
    for i, (t, g) in enumerate(zip(tw, ms)):
        if _SHAPE[t["shape"]] != g.marker:
            bad.append(f"{where}[{i}]: shape {t['shape']} vs {g.marker}")
        if t["shape"] in _FILLABLE and t["hollow"] != (g.fill_alpha == 0):
            bad.append(f"{where}[{i}]: hollow {t['hollow']} vs "
                       f"fill_alpha {g.fill_alpha}")


@pytest.mark.parametrize("mode", MODES)
class TestTwowaysSymbols:
    def test_each_probe(self, mode, tmp_path, monkeypatch):
        P = TRUTH["probes"]
        bad = []
        # The s1mono cycle, its sm sizes (against the same full shape), and
        # under msize(large).
        for pid, n, o in (("sy_cycle", 15, {}),
                          ("sy_large", 11, {"msize": "large"})):
            tw = P[pid]["layers"]
            ms = _markers([_sc(**o)] * n, "s1mono", mode)
            _check_layers(tw, ms, pid, bad)
            for sm, full in ((10, 0), (11, 1), (12, 2), (13, 3)):
                if sm >= n:
                    continue
                r_tw = tw[sm]["extent"] / tw[full]["extent"]
                r_d = ms[sm].size / ms[full].size
                if abs(r_tw - r_d) > 0.01 * r_tw:
                    bad.append(f"{pid} p{sm + 1}/p{full + 1}: twoway "
                               f"{r_tw:.4f}, dash {r_d:.4f}")
        ms = _markers([_sc(), _sc(msymbol="smcircle_hollow", mfcolor="red")],
                      "s1mono", mode)
        _check_layers(P["sy_smh_red"]["layers"], ms, "sy_smh_red", bad)
        # twoway's pstyle(p7) layer is p7's style; pstyle() on a marker is
        # named styles' (WP-30 S32), so dash's p7 is the seventh layer.
        ms = _markers([_sc()] * 6 + [_sc(mfcolor="red")], "s1mono", mode)
        _check_layers(P["sy_p7_red"]["layers"], [ms[0], ms[6]],
                      "sy_p7_red", bad)
        for n, r in TRUTH["derived"]["sm_factor"].items():
            f = T._SMALL_SYMBOL_FACTOR[n]
            for size, v in r.items():
                if abs(v - f) > 0.01 * v:
                    bad.append(f"sm_factor {n} {size}: twoway {v}, dash {f}")
        for t in _CYCLE_PLOT:
            tw = P["cy_" + t]["layers"]
            ms = _markers([_sc(), plot_for(t)], "s1mono", mode)
            if _SHAPE[tw[-1]["shape"]] != ms[-1].marker:
                bad.append(f"cy_{t}: {tw[-1]['shape']} vs {ms[-1].marker}")
        # The marker colour keys, through a user scheme each.
        for s, lines in (("w24g", ["color pmarkfill green",
                                   "color pmarkline blue"]),
                         ("w24m", ["color p1mark green", "color pmark red"]),
                         ("w24f", ["color p1markfill green",
                                   "color p1markline blue"])):
            name = _user_scheme(tmp_path, monkeypatch, s + ".scheme",
                                ["#include s2color"] + lines)
            tw = P[f"mk_{s}_2"]["layers"]
            ms = _markers([_sc(), plot_for("scatter", {"yaxis": "2"})],
                          name, mode)
            got = [(str(g.fill_color).lower(), str(g.line_color).lower())
                   for g in ms]
            want = [(t["fill"], t["stroke"]) for t in tw]
            if got != want:
                bad.append(f"mk_{s}_2: twoway {want}, dash {got}")
        assert not bad, bad
