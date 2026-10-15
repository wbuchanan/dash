"""
test_axis_suboptions.py -- WP-30 P1.18a: the axis look sub-options.

twoway draws xlabel()/ylabel()'s nolabels, noticks, labcolor(), tlength()
and tposition(), reads every anglestyle name and its axis abbreviations
h, v, rh and rv, gives xtick()/ytick() their own tick look, and draws
xscale()/yscale()'s off, noline, lcolor(), lwidth(), lpattern(), alt and
titlegap() -- on second axes too, and under by() all but off, nolabels,
noticks and titlegap().  dash named each of them and drew none (GAPS2 B21,
B23, D9).  Expected values are twoway's (test/fixtures/
axis_subopt_truth.json, scripts/extract_axis_subopt_truth.do) at 3.84 px
per Stata unit: s2color's tick is 1.3888 units, 5.33 px, drawn 5.
"""
import json
import math
import os
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

from bokeh.models import Axis, LinearAxis, Plot, Select  # noqa: E402

_MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "axis_subopt_truth.json")
_PX = 3.84          # pixels per Stata unit (2.88 pt at 4/3 px per pt)


def _y2_plots():
    return [plot_for("scatter"),
            plot_for("scatter", {"yaxis": "2"}, yvar="price")]


def _figs(mode, go, plots=None, scheme="s2color"):
    """(figures with axes, warnings) one mode draws; by() head and foot
    cells, which carry no axes, are skipped."""
    spec = tp._spec(plots or [plot_for("scatter")], {"scheme": scheme}, go)
    if mode == "saved":
        r, caught = tp._standalone(spec)
        found = list(r._last_layout_root.select({"type": Plot}))
    else:
        doc, caught = tp._served(spec)
        found = list(doc.select({"type": Plot}))
    out = [p for p in found
           if any(isinstance(a, Axis) for side in ("left", "right", "below",
                                                  "above")
                  for a in getattr(p, side))]
    # WP-30 P1.15c: by() panels draw different axes (twoway's outer-axes
    # rule), so two builds' panels are paired in label order, not in
    # select()'s unordered one.
    from by_panel_probe import panel_label
    out.sort(key=panel_label)
    return out, caught


def _axis(fig, letter="y", number=1):
    """The figure's axis *number* of *letter*, searched on both sides."""
    sides = ("left", "right") if letter == "y" else ("below", "above")
    attr = f"{letter}_range_name"
    want = "default" if number == 1 else f"{letter}2"
    for side in sides:
        for a in getattr(fig, side):
            if isinstance(a, Axis) and getattr(a, attr, None) == want:
                return a
    raise AssertionError(f"no {letter}{number} axis")


def _side(fig, ax):
    for side in ("left", "right", "below", "above"):
        if any(a is ax for a in getattr(fig, side)):
            return side
    return None


def _y(mode, go, plots=None, scheme="s2color"):
    figs, caught = _figs(mode, go, plots, scheme)
    return figs[0], _axis(figs[0]), caught


def _notes(caught, text):
    return [w for w in caught if text in w]


# ===========================================================================
# Angles
# ===========================================================================

class TestAngleStyles:
    @pytest.mark.parametrize("mode", _MODES)
    def test_each_anglestyle_name(self, mode):
        bad = []
        for name, deg in dr._DASH_ANGLESTYLES.items():
            _, ax, caught = _y(mode, {"ylabel": f", angle({name})"})
            if not math.isclose(float(ax.major_label_orientation),
                                math.radians(deg), abs_tol=1e-9):
                bad.append((name, ax.major_label_orientation))
            if _notes(caught, "angle"):
                bad.append((name, caught))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_twoways_axis_abbreviations(self, mode):
        want = {"v": 90, "ve": 90, "h": 0, "rh": 180, "rho": 180,
                "rv": 270, "rve": 270}
        bad = []
        for v, deg in want.items():
            _, ax, _c = _y(mode, {"ylabel": f", angle({v})"})
            if not math.isclose(float(ax.major_label_orientation),
                                math.radians(deg), abs_tol=1e-9):
                bad.append((v, ax.major_label_orientation))
        _, ax, caught = _y(mode, {"ylabel": ", angle(r)"})
        assert float(ax.major_label_orientation) == 0.0
        assert len(_notes(caught, "ylabel(angle(r))")) == 1, caught
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_wrong_case_or_unknown_name_is_noted_and_level(self, mode):
        bad = []
        for v in ("Vertical", "V", "Rv", "stacked", "forty", "45deg"):
            _, ax, caught = _y(mode, {"ylabel": f", angle({v})"})
            hits = _notes(caught, f"ylabel(angle({v})) is not a recognised "
                                  "angle")
            if float(ax.major_label_orientation) != 0.0 or len(hits) != 1:
                bad.append((v, ax.major_label_orientation, caught))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_unknown_name_overrides_the_scheme_angle(self, mode):
        # s2color draws the y labels vertical (S15); stacked is drawn 0.
        _, base, _c = _y(mode, {})
        assert math.isclose(float(base.major_label_orientation), math.pi / 2)
        _, ax, _c = _y(mode, {"ylabel": ", angle(stacked)"})
        assert float(ax.major_label_orientation) == 0.0

    @pytest.mark.parametrize("mode", _MODES)
    def test_x_and_second_axes(self, mode):
        fig, _ax, _c = _y(mode, {"xlabel": ", angle(rv)",
                                 "ylabel2": ", angle(rvertical)",
                                 "xlabel2": ", angle(v)"},
                          [plot_for("scatter"),
                           plot_for("scatter", {"yaxis": "2", "xaxis": "2"},
                                    yvar="price")])
        assert math.isclose(_axis(fig, "x").major_label_orientation,
                            math.radians(270))
        assert math.isclose(_axis(fig, "y", 2).major_label_orientation,
                            math.radians(270))
        assert math.isclose(_axis(fig, "x", 2).major_label_orientation,
                            math.radians(90))


# ===========================================================================
# Label visibility, colour and ticks
# ===========================================================================

class TestLabelVisibility:
    @pytest.mark.parametrize("mode", _MODES)
    def test_nolabels_and_the_positive_word(self, mode):
        _, ax, caught = _y(mode, {"ylabel": ", nolabels"})
        assert ax.major_label_text_font_size == "0px"
        assert ax.major_label_standoff == 0
        assert not _notes(caught, "sub-option"), caught
        _, base, _c = _y(mode, {})
        _, ax, _c = _y(mode, {"ylabel": ", labels nolabels"})
        assert ax.major_label_text_font_size == base.major_label_text_font_size

    @pytest.mark.parametrize("mode", _MODES)
    def test_noticks_and_the_positive_word(self, mode):
        _, ax, _c = _y(mode, {"ylabel": ", noticks"})
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 0)
        _, ax, _c = _y(mode, {"ylabel": ", ticks noticks"})
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 5)


class TestLabelColourAndTicks:
    @pytest.mark.parametrize("mode", _MODES)
    def test_labcolor(self, mode):
        _, ax, caught = _y(mode, {"ylabel": ", labcolor(red%50)"})
        assert ax.major_label_text_color == "#ff0000"
        assert ax.major_label_text_alpha == 0.5
        assert not _notes(caught, "labcolor"), caught
        _, ax, caught = _y(mode, {"ylabel": ", labcolor(bogus)"})
        assert ax.major_label_text_color == "#000000"
        assert len(_notes(caught, "labcolor(bogus)")) == 1, caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_tlength_in_stata_units(self, mode):
        want = {"tlength(3)": (0, 12), "tlength(*2)": (0, 11),
                "tlength(bogus)": (0, 15), "tlength(-1)": (4, 0),
                "tlength(0)": (0, 0)}
        bad = []
        for opt, ticks in want.items():
            _, ax, caught = _y(mode, {"ylabel": ", " + opt})
            got = (ax.major_tick_in, ax.major_tick_out)
            n = len(_notes(caught, "tlength"))
            if got != ticks or n != (1 if "bogus" in opt else 0):
                bad.append((opt, got, n))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_tposition(self, mode):
        want = {"o": (0, 5), "outside": (0, 5), "i": (5, 0),
                "inside": (5, 0), "c": (3, 3), "crossing": (3, 3),
                "bogus": (3, 3), "Inside": (3, 3)}
        bad = []
        for v, ticks in want.items():
            _, ax, caught = _y(mode, {"ylabel": f", tposition({v})"})
            got = (ax.major_tick_in, ax.major_tick_out)
            n = len(_notes(caught, f"tposition({v})"))
            if got != ticks or n != (1 if v in ("bogus", "Inside") else 0):
                bad.append((v, got, n))
        assert not bad, bad


class TestTickOnlyStyleIsSeparate:
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_label_look_does_not_reach_the_tick_positions(self, mode):
        _, ax, _c = _y(mode, {"ylabel": ", noticks", "ytick": "25"})
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 0)
        assert (ax.minor_tick_in, ax.minor_tick_out) == (0, 5)
        _, ax, _c = _y(mode, {"ylabel": ", tlength(5)", "ytick": "25"})
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 19)
        assert (ax.minor_tick_in, ax.minor_tick_out) == (0, 5)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_tick_option_has_its_own_look(self, mode):
        _, ax, _c = _y(mode, {"ytick": "25, tlength(5)"})
        assert (ax.minor_tick_in, ax.minor_tick_out) == (0, 19)
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 5)
        _, ax, _c = _y(mode, {"ytick": "25, noticks"})
        assert (ax.minor_tick_in, ax.minor_tick_out) == (0, 0)
        _, ax, _c = _y(mode, {"ytick": "25, tposition(inside)"})
        assert (ax.minor_tick_in, ax.minor_tick_out) == (5, 0)


# ===========================================================================
# The scale look
# ===========================================================================

class TestScaleLook:
    @pytest.mark.parametrize("mode", _MODES)
    def test_off(self, mode):
        fig, base, _c = _y(mode, {})
        grid = [g.grid_line_color for g in fig.ygrid]
        for v in ("off", "off on", "on off"):
            fig, ax, caught = _y(mode, {"yscale": v})
            assert ax.visible is False, v
            assert [g.grid_line_color for g in fig.ygrid] == grid, v
            assert not _notes(caught, "sub-option"), caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_noline_and_lcolor(self, mode):
        bad = []
        for v, want in (("noline", None), ("noline line", None),
                        ("line noline", None), ("noli lc(red)", "#ff0000"),
                        ("lc(red) noline", "#ff0000"),
                        ("noline lwidth(thick)", None)):
            _, ax, _c = _y(mode, {"yscale": v})
            if ax.axis_line_color != want:
                bad.append((v, ax.axis_line_color))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_line_style(self, mode):
        _, ax, _c = _y(mode, {"yscale":
                              "lcolor(red) lwidth(thick) lpattern(dash)"})
        assert ax.axis_line_color == "#ff0000"
        assert math.isclose(ax.axis_line_width, 3.072)
        assert list(ax.axis_line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))
        _, ax, _c = _y(mode, {"yscale": "lc(red) lw(1) lp(shortdash)"})
        assert ax.axis_line_color == "#ff0000"
        assert math.isclose(ax.axis_line_width, 3.84)
        assert list(ax.axis_line_dash) == list(
            dr.OptionTranslator.translate_lpattern("shortdash"))

    @pytest.mark.parametrize("mode", _MODES)
    def test_unknown_line_values_are_noted(self, mode):
        _, base, _c = _y(mode, {})
        for v, check in (
                ("lcolor(bogus)", lambda a: a.axis_line_color == "#000000"),
                ("lwidth(bogus)",
                 lambda a: a.axis_line_width == base.axis_line_width),
                ("lpattern(Dash)", lambda a: list(a.axis_line_dash) == []),
                ("lpattern(bogus)", lambda a: list(a.axis_line_dash) == [])):
            _, ax, caught = _y(mode, {"yscale": v})
            assert check(ax), v
            assert len(_notes(caught, v.split("(")[1].rstrip(")"))) == 1, \
                (v, caught)

    @pytest.mark.parametrize("mode", _MODES)
    def test_titlegap(self, mode):
        bad = []
        for v, want, n in (("titlegap(5)", 19, 0), ("titlegap(-2)", -8, 0),
                           # Flipped (WP-31 D7): *2 of the scheme's
                           # axis_title_gap (1 pt), not of Bokeh's 5 px.
                           ("titlegap(*2)", 3, 0),
                           ("titlegap(bogus)", 15, 1)):
            _, ax, caught = _y(mode, {"yscale": v})
            got = (ax.axis_label_standoff, len(_notes(caught, "titlegap")))
            if got != (want, n):
                bad.append((v, got))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_alt_moves_the_axis(self, mode):
        fig, ax, _c = _y(mode, {"yscale": "alt"})
        assert fig.right[0] is ax
        fig, _ax, _c = _y(mode, {"xscale": "alt"})
        assert fig.above[0] is _axis(fig, "x")
        fig, ax, _c = _y(mode, {"yscale": "alt"}, scheme="economist")
        assert _side(fig, ax) == "left"

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_axis_the_scheme_draws_bare(self, mode):
        _, ax, _c = _y(mode, {}, scheme="economist")
        assert ax.axis_line_color is None
        _, ax, _c = _y(mode, {"yscale": "line"}, scheme="economist")
        assert ax.axis_line_color is not None
        _, ax, _c = _y(mode, {"yscale": "lcolor(red)"}, scheme="economist")
        assert ax.axis_line_color == "#ff0000"
        _, ax, _c = _y(mode, {"ylabel": ", ticks"}, scheme="economist")
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_bad_range_is_noted_once(self, mode):
        _, _ax, caught = _y(mode, {"yscale": "range(abc) noline"})
        assert len(_notes(caught, "range()) ignores abc")) == 1, caught
        assert _notes(caught, "yscale(range()) ignores abc"), caught


class TestSecondAxis:
    @pytest.mark.parametrize("mode", _MODES)
    def test_alt_with_a_second_axis(self, mode):
        p = _y2_plots()
        fig, ax, _c = _y(mode, {"yscale": "alt"}, p)
        assert list(fig.right) == [ax, _axis(fig, "y", 2)]
        fig, ax, _c = _y(mode, {"yscale2": "alt"}, p)
        assert [a for a in fig.left if isinstance(a, Axis)] == \
            [ax, _axis(fig, "y", 2)]
        fig, ax, _c = _y(mode, {"yscale": "alt", "yscale2": "alt"}, p)
        assert _side(fig, ax) == "right"
        assert _side(fig, _axis(fig, "y", 2)) == "left"
        fig, _ax, _c = _y(mode, {"xscale2": "alt"},
                          [plot_for("scatter"),
                           plot_for("scatter", {"xaxis": "2"})])
        assert [a for a in fig.below if isinstance(a, Axis)] == \
            [_axis(fig, "x"), _axis(fig, "x", 2)]

    @pytest.mark.parametrize("mode", _MODES)
    def test_second_axis_look(self, mode):
        fig, _ax, caught = _y(mode, {"yscale2": "off"}, _y2_plots())
        assert _axis(fig, "y", 2).visible is False
        fig, _ax, c2 = _y(mode, {"ylabel2": ", nolabels"}, _y2_plots())
        assert _axis(fig, "y", 2).major_label_text_font_size == "0px"
        fig, _ax, c3 = _y(mode, {"yscale2": "noline lcolor(red)"},
                          _y2_plots())
        assert _axis(fig, "y", 2).axis_line_color == "#ff0000"
        assert not _notes(caught + c2 + c3, "sub-option"), caught + c2 + c3


# ===========================================================================
# by()
# ===========================================================================

def _by_props(ax):
    return (ax.visible, ax.major_label_text_font_size,
            ax.major_label_standoff, ax.major_tick_in, ax.major_tick_out,
            ax.minor_tick_in, ax.minor_tick_out, ax.axis_label_standoff)


class TestUnderBy:
    @pytest.mark.parametrize("mode", _MODES)
    def test_twoways_subset(self, mode):
        base, _c = _figs(mode, {"by": "foreign", "ytick": "25"})
        figs, caught = _figs(mode, {
            "by": "foreign", "yscale": "off titlegap(10)",
            "xscale": "off", "ylabel": ", nolabels noticks",
            "ytick": "25, noticks"})
        assert len(figs) == len(base) == 2
        for f, b in zip(figs, base):
            assert _by_props(_axis(f)) == _by_props(_axis(b))
            assert _axis(f, "x").visible == _axis(b, "x").visible
        assert not _notes(caught, "sub-option"), caught
        figs, caught = _figs(mode, {
            "by": "foreign", "yscale": "noline alt lcolor(red)",
            "ylabel": ", labcolor(red) tlength(5) angle(vertical)"})
        for f in figs:
            ax = _axis(f)
            assert _side(f, ax) == "right"
            assert ax.axis_line_color == "#ff0000"
            assert ax.major_label_text_color == "#ff0000"
            # WP-30 P1.15b: under by() twoway scales panel ticks by its
            # by() multiplier, 0.85 for two panels: tlength(5)'s 19 px is 16.
            assert ax.major_tick_out == 16
            assert math.isclose(ax.major_label_orientation, math.pi / 2)
        b2, _c = _figs(mode, {"by": "foreign"}, _y2_plots())
        f2, caught = _figs(mode, {"by": "foreign", "ylabel2": ", nolabels",
                                  "yscale2": "off"}, _y2_plots())
        for f, b in zip(f2, b2):
            assert _by_props(_axis(f, "y", 2)) == _by_props(_axis(b, "y", 2))
        assert not _notes(caught, "sub-option"), caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_bad_value_is_still_noted(self, mode):
        _f, caught = _figs(mode, {"by": "foreign",
                                  "yscale": "titlegap(bogus)"})
        assert len(_notes(caught, "titlegap(bogus)")) == 1, caught


# ===========================================================================
# Other parsers keep naming the look; quoted text stays text
# ===========================================================================

class TestOtherParsersStillName:
    @pytest.mark.parametrize("mode", _MODES)
    def test_named(self, mode):
        _f, caught = _figs(mode, {"xtick": "2500, labcolor(red) nolabels"})
        hit = _notes(caught, "xtick() sub-option")
        assert hit and "labcolor(red)" in hit[0] and "nolabels" in hit[0], \
            caught
        cv = [plot_for("scatter", {"colorvar": "price"})]
        _f, caught = _figs(mode, {
            "zlabel": "4000 8000, labcolor(red) tlength(2) nolabels",
            "zscale": "alt off noline titlegap(2)"}, cv)
        z = _notes(caught, "zlabel() sub-option")
        assert z and all(t in z[0] for t in ("labcolor(red)", "tlength(2)",
                                             "nolabels")), caught
        zs = _notes(caught, "zscale() sub-option")
        assert zs and all(t in zs[0] for t in ("alt", "off", "noline",
                                               "titlegap(2)")), caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_zlabel_names_each_as_typed(self, mode):
        cv = [plot_for("scatter", {"colorvar": "price"})]
        _f, caught = _figs(mode, {"zlabel": "4000 8000, angle(45)"}, cv)
        z = _notes(caught, "zlabel() sub-option")
        assert z and "angle(45)" in z[0] and "0.785" not in z[0], caught
        _f, caught = _figs(mode, {"zlabel": "4000 8000, angle(stacked)"}, cv)
        z = _notes(caught, "zlabel() sub-option")
        assert z and "angle(stacked)" in z[0], caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_quoted_label_text_is_text(self, mode):
        _, base, _c = _y(mode, {})
        _, ax, caught = _y(mode, {"ylabel": '10 "nolabels" 20 '
                                            '"labcolor(red)" 30 '
                                            '"angle(stacked)"'})
        assert ax.major_label_text_font_size == \
            base.major_label_text_font_size
        assert ax.major_label_text_color == base.major_label_text_color
        assert ax.major_label_orientation == base.major_label_orientation
        assert set(ax.major_label_overrides.values()) == {
            "nolabels", "labcolor(red)", "angle(stacked)"}
        assert not _notes(caught, "angle"), caught


# ===========================================================================
# After a filter move
# ===========================================================================

_MOVE_GO = {"ylabel": ", noticks labcolor(red) angle(rvertical)",
            "yscale": "noline alt"}


def _check_moved(fig):
    ax = _axis(fig)
    assert (ax.major_tick_in, ax.major_tick_out) == (0, 0)
    assert ax.major_label_text_color == "#ff0000"
    assert math.isclose(ax.major_label_orientation, 3 * math.pi / 2)
    assert ax.axis_line_color is None
    assert _side(fig, ax) == "right"


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_look_holds(self, mode):
        spec = tp._spec([plot_for("scatter")],
                        {"scheme": "s2color",
                         "filter": "foreign, type(dropdown)"}, _MOVE_GO)
        if mode == "saved":
            import test_saved_filter_layers as sfl
            r, _c = tp._standalone(spec)
            sfl._move(r, ("Select", "Foreign"))
            figs = list(r._last_layout_root.select({"type": Plot}))
        else:
            doc, _c = tp._served(spec)
            w = [x for x in tp._widgets_of(doc) if isinstance(x, Select)][0]
            raw = [v for v, lab in w.options if lab == "Foreign"][0]
            tp._fire(w, raw)
            figs = list(doc.select({"type": Plot}))
        assert figs
        for f in figs:
            _check_moved(f)


# ===========================================================================
# Unit functions
# ===========================================================================

class TestTheUnitFunctions:
    def test_scale_spec_look(self):
        look = dr._dash_scale_spec("noli lc(red) alt off on titleg(5)")["look"]
        assert look == {"off": True, "line_off": False, "line_on": False,
                        "lcolor": "red", "lwidth": None, "lpattern": None,
                        "titlegap": "5", "alternate": True,
                        # WP-31 D7: the outer gap, line style and extent.
                        "outergap": None, "lstyle": None, "noextend": None}
        assert dr._dash_scale_name("OFF") == "OFF"
        assert dr._dash_scale_name("alt") == "alternate"
        assert dr._dash_scale_name("re") == "re"

    def test_tick_geometry(self):
        g = dr._dash_tick_geometry
        assert g("outside", 5.33) == (0, 5)
        assert g("inside", 5.33) == (5, 0)
        assert g("crossing", 5.33) == (3, 3)
        assert g("outside", -3.84) == (4, 0)
        assert g("outside", 1e9) == (0, 100)
        assert g("inside", float("nan")) == (0, 0)

    def test_tick_position(self):
        p = dr._dash_tick_position
        assert p("o") == "outside" and p("cross") == "crossing"
        assert p("Inside") is None and p("") is None
        assert p("i" * 33) is None

    def test_tick_look(self):
        ax = LinearAxis(major_tick_in=0, major_tick_out=5)
        dr._dash_tick_look(ax, {"tlength": "3"}, option="ylabel")
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 12)
        pair = dr._dash_primary_axes(
            type(Plot().xaxis)([LinearAxis(major_tick_in=0,
                                           major_tick_out=5),
                                LinearAxis(major_tick_in=0,
                                           major_tick_out=5)]),
            "x_range_name")
        dr._dash_tick_look(pair, {"show_ticks": False}, option="ylabel")
        assert [(a.major_tick_in, a.major_tick_out) for a in pair] == \
            [(0, 0), (0, 0)]

    def test_scale_look(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            look = dr._dash_scale_look("range(abc) noline lw(thick)")
        assert look["line_off"] is True and look["lwidth"] == "thick"

    def test_apply_scale_look(self):
        from bokeh.plotting import figure
        fig = figure()
        ax = fig.yaxis[0]
        dr._dash_apply_scale_look(fig, ax, dr._dash_scale_look(
            "off lcolor(red) titlegap(5)"), "yscale")
        assert ax.visible is False and ax.axis_line_color == "#ff0000"
        assert ax.axis_label_standoff == 19

    def test_axis_alternate(self):
        from bokeh.plotting import figure
        fig = figure()
        y1 = fig.yaxis[0]
        dr._dash_axis_alternate(fig, y1, 1)
        assert list(fig.right) == [y1] and y1 not in fig.left
        y2 = LinearAxis()
        fig.add_layout(y2, "right")
        dr._dash_axis_alternate(fig, y2, 2)
        assert list(fig.left)[-1] is y2


class TestAdversarial:
    def test_hostile_values(self):
        long_ = "x" * 10000
        t0 = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            spec = dr._dash_parse_axis_spec(
                f", labcolor({long_}) tposition({long_}) "
                f"tlength({'9' * 10**6}) angle({'1' * 10**6})")
            ax = LinearAxis()
            dr._dash_apply_axis_spec(ax, [], spec, option="ylabel")
            look = dr._dash_scale_look(f"lpattern({long_}) lcolor({long_})")
            dr._dash_apply_scale_look(None, ax, look, "yscale")
        assert time.monotonic() - t0 < 0.5 * 4
        for w in caught:
            assert "<script" not in str(w.message)
            assert len(str(w.message)) < 400
        assert ax.major_label_text_color == "#000000"
        assert list(ax.axis_line_dash) == []


# ===========================================================================
# twoway's truth fixture
# ===========================================================================

@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheTruthFixture:
    def test_meta_is_stamped(self, truth):
        meta = truth["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k

    def test_the_literals_are_twoways(self, truth):
        """Each literal the tests above use, against twoway's members."""
        pr = truth["probes"]
        bad = []

        def mem(pid, name, ax="yaxis1"):
            return ((pr.get(pid) or {}).get("members") or {}).get(
                ax, {}).get(name)

        # Angles in degrees.
        for pid, deg in (("ang_rvertical", 270), ("ang_forty_five", 45),
                         ("ang_v", 90), ("ang_rh", 180), ("ang_rv", 270),
                         ("ang_Vertical", 0), ("ang_stacked", 0),
                         ("xang_rv", 270)):
            ax = "xaxis1" if pid.startswith("x") else "yaxis1"
            got = mem(pid, "tickangle", ax)
            if got is None or abs(float(got) - deg) > 1e-6:
                bad.append((pid, got, deg))
        # Tick lengths (Stata units) at 3.84 px.
        for pid, px in (("lab_tl3", 12), ("lab_tl_bogus", 15),
                        ("lab_tl0", 0)):
            got = mem(pid, "length")
            if got is None or round(float(got) * _PX) != px:
                bad.append((pid, got, px))
        # A bad tposition() is twoway's default attributes (no style name),
        # which it draws crossing the axis (E9).
        for pid, pos in (("lab_tp_inside", "inside"), ("lab_tp_o", "outside"),
                         ("lab_tp_c", "crossing"), ("lab_tp_bogus", "")):
            if mem(pid, "position") != pos:
                bad.append((pid, mem(pid, "position"), pos))
        for pid, gap in (("sc_tgap5", 19), ("sc_tgap_bogus", 15)):
            got = mem(pid, "title_gap")
            if got is None or round(float(got) * _PX) != gap:
                bad.append((pid, got, gap))
        for pid, shown in (("lab_nolabels", "0"), ("lab_lab_nolab", "1"),
                           ("sc_off", "0")):
            key = "draw_view" if pid == "sc_off" else "show_labels"
            if str(mem(pid, key)) != shown:
                bad.append((pid, mem(pid, key), shown))
        for pid, side in (("sc_alt", "right"), ("econ_alt", "left")):
            if mem(pid, "axis_position") != side:
                bad.append((pid, mem(pid, "axis_position"), side))
        for pid, rc, first in (
                ("rf_ang400", 198, "textangle must be between"),
                ("rf_lw_neg", 198, "gm_linewidth must be between"),
                ("rf_OFF", 198, "option OFF not allowed"),
                ("rf_bogus", 198, "option bogus not allowed"),
                ("rf_nodraw_ang", 0, None),
                ("rf_ord_xlab_yscale", 198, "gm_linewidth"),
                ("rf_ord_ylab_xscale", 198, "textangle"),
                ("rf_merge_seg_after", 0, None),
                ("rf_merge_after_seg", 198, "textangle")):
            p = pr.get(pid) or {}
            msgs = p.get("messages") or []
            if p.get("rc") != rc or (first and not (msgs and
                                                    first in msgs[0])):
                bad.append((pid, p.get("rc"), msgs[:1]))
        assert not bad, bad

    def test_the_by_subset(self, truth):
        """Under by() the forms twoway ignores draw the page by() alone
        draws (the SVG's texts, ticks and lines); the others change it."""
        pr = truth["probes"]
        ignored, drawn = set(), set()
        for base, pids in (("by_base", ("by_off", "by_xoff", "by_nolab",
                                        "by_noticks", "by_tgap", "by_noline",
                                        "by_alt", "by_xalt", "by_lc",
                                        "by_labc", "by_tl", "by_tp",
                                        "by_ang", "by_style")),
                           ("by_y2_base", ("by_y2_nolab", "by_y2_off"))):
            for pid in pids:
                (ignored if pr[pid]["svg"] == pr[base]["svg"]
                 else drawn).add(pid)
        assert ignored == {"by_off", "by_xoff", "by_nolab", "by_noticks",
                           "by_tgap", "by_y2_nolab", "by_y2_off"}, ignored
