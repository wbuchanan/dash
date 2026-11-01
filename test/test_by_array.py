"""by()'s array: shrink, the region margins and the outline (WP-31 D10b,
section 39).

Measured (test/fixtures/by_remainder_truth.json, s2color):

- shrink and overallshrink draw the panels' contents smaller by a factor
  that is the panels' share of the graph once by()'s own texts are set
  aside: 0.894 with no text, less 0.0393 for the note (the default
  "Graphs by ..." counts), 0.0600 for a title, 0.0475 for a subtitle,
  0.0466 for a caption and 0.047 for each further line (shrink_*: the
  model's sums hold for title with no note, title and subtitle, a
  two-line title).  A no-word after a yes-word does not undo it; a title()
  outside by() does not count; iscale() multiplies with it.
- by()'s graphregion(margin()) insets the whole array by the margin less
  the scheme's graph margin (medium, 3.5); small (1.2) draws it 2.3 units
  larger, which a dashboard cell cannot; plotregion(margin()) insets the
  panel array by the margin itself.
- by()'s plotregion() outline is drawn once around the array, not on
  every panel (regions_plot_lcolor, regions_plot_outline).
- style(altleg) draws as style(default) (bystyle_altleg).
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
import test_by_axes_keys as tk
import test_by_remainder as tr

MODES = ("saved", "served")
_UNIT = dr.OptionTranslator.PT_PER_RS * dr.OptionTranslator.PX_PER_PT

_GRAPHS = {
    "plain2": (tk._ONE, {"by": "foreign"}),
    "shr2": (tk._ONE, {"by": "foreign, shrink"}),
    "gm_large": (tk._ONE, {"by": "foreign, graphregion(margin(large))"}),
    "pm_large": (tk._ONE, {"by": "foreign, plotregion(margin(large))"}),
    "pm_both": (tk._ONE, {"by": "foreign, graphregion(margin(l+5)) "
                                "plotregion(margin(small))"}),
    "outline": (tk._ONE, {"by": "foreign, plotregion(lcolor(red) "
                                "lwidth(thick))"}),
    "altleg": (tk._TWO, {"by": "rep78, style(altleg)"}),
}
_BUILT = {}


def _build(mode):
    if mode not in _BUILT:
        graphs = [tk._graph(n, p, go) for n, (p, go) in _GRAPHS.items()]
        spec = tk._spec(graphs, scheme="s2color")
        _BUILT[mode] = tk._build(mode, spec, data=tr._data())
    return _BUILT[mode]


def _grid(mode, name):
    roots, _n, _o = _build(mode)
    return tk._grids(roots)[name]


def _notes(mode):
    return _build(mode)[1]


def _probe(pid):
    return tr._probe(pid)


class TestShrinkFactor:
    @pytest.mark.parametrize("pid,base,by", [
        ("shrink_bare_g2", "shrink_base_g2", "g2, shrink"),
        ("shrink_overall_bare_g2", "shrink_base_g2", "g2, overallshrink"),
        ("shrink_shrink_g2", "shrink_base_g2", 'g2, shrink title("T")'),
        ("shrink_nonote", "shrink_base_g2", 'g2, shrink note("")'),
        ("shrink_cap", "shrink_base_g2", 'g2, shrink caption("C")'),
        ("shrink_sub", "shrink_base_g2", 'g2, shrink subtitle("S")'),
        ("shrink_title_nonote", "shrink_base_g2",
         'g2, shrink title("T") note("")'),
        ("shrink_title_sub", "shrink_base_g2",
         'g2, shrink title("T") subtitle("S")'),
        ("shrink_two_titles", "shrink_base_g2", 'g2, shrink title("T" "U")'),
        ("shrink_then_no", "shrink_base_g2", "g2, shrink noshrink"),
        ("shrink_overall_then_no", "shrink_base_g2",
         "g2, overallshrink nooverallshrink"),
        ("shrink_bare_g10", "shrink_base_g10", "g10, shrink"),
    ])
    def test_measured(self, pid, base, by):
        want = _probe(pid)["marker_r"] / _probe(base)["marker_r"]
        got = dr._dash_by_shrink_factor(by)
        assert abs(got - want) < 0.006, (pid, got, want)

    def test_no_shrink_word(self):
        assert dr._dash_by_shrink_factor('g2, title("T") noshrink') == 1.0
        assert dr._dash_by_shrink_factor("g2") == 1.0

    def test_the_multiplier_takes_it(self):
        assert abs(dr._dash_by_size_mult("foreign, shrink", 2)
                   / dr._dash_by_size_mult("foreign", 2)
                   - dr._dash_by_shrink_factor("foreign, shrink")) < 1e-9

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_silently(self, mode):
        assert not [n for n in _notes(mode) if "shrink" in n], _notes(mode)


def _same(a, b):
    """Two CSS percentage lists equal to 0.002 (the sum of two rounded
    %.4g terms, WP-45 GW-6)."""
    x = [float(v) for v in re.findall(r"-?[0-9.]+", str(a))]
    y = [float(v) for v in re.findall(r"-?[0-9.]+", str(b))]
    return len(x) == len(y) and all(abs(p - q) <= 0.002 for p, q in zip(x, y))


class TestArrayInset:
    @staticmethod
    def _pad(mode, name):
        st = dict(_grid(mode, name).styles or {})
        return st.get("padding")

    def test_fixture(self):
        def left(pid):
            return [r for r in _probe(pid)["rects"]
                    if r["fill"] == "#ffffff"][0]["x"]
        base = left("by_foreign")
        assert abs((left("regions_margin") - base) / 28.8 - 4.5) < 0.05
        assert abs((left("regions_margin_l5") - base) / 28.8 - 5.0) < 0.05
        assert abs((left("regions_plot_margin") - base) / 28.8 - 8.0) < 0.05
        assert abs((left("regions_plot_margin_small") - base) / 28.8
                   - 1.2) < 0.05

    # Flipped (WP-32, D39 D-37.a): the inset was fixed px at dash's 4-inch
    # reference (3.84 px a unit), so it stayed put when the page was
    # resized.  twoway's margin is a share of the graph's smaller side, so
    # the inset is a CSS percentage of the cell's width: the units times
    # min(W, H) / W, the graph's own ratio (s2color 5.5 x 4 in: 4 / 5.5),
    # which follows any resize.
    # Flipped (WP-45 GW-6): the padding was the change alone; the scheme's
    # graph margin (s2color's medium, 3.5 units a side) is drawn round the
    # array now, so the padding is the scheme's margin plus the change.
    # Flipped (WP-41 41-05): the top side also holds the first panel
    # row's by_indiv top margin (1.2 units, the grid's 9 px row spacing
    # halved at 3.84 px a unit), between the graph margin and the strips,
    # as twoway's (G_by_stcolor: the strips 1.2 units under the margin).
    @staticmethod
    def _pct(*units):
        k = min(1.0, 4.0 / 5.5)
        top = round(2.4 * 3.84) / 2.0 / 3.84
        return " ".join("%.4g%%" % ((u + 3.5 + (top if i == 0 else 0)) * k)
                        for i, u in enumerate(units))

    @pytest.mark.parametrize("mode", MODES)
    def test_graph_margin(self, mode):
        assert _same(self._pad(mode, "gm_large"), self._pct(4.5, 4.5, 4.5, 4.5))

    @pytest.mark.parametrize("mode", MODES)
    def test_plot_margin(self, mode):
        assert _same(self._pad(mode, "pm_large"), self._pct(8.0, 8.0, 8.0, 8.0))

    @pytest.mark.parametrize("mode", MODES)
    def test_terms_add(self, mode):
        assert _same(self._pad(mode, "pm_both"), self._pct(1.2, 1.2, 1.2, 6.2))

    def test_the_inset_follows_the_graphs_ratio(self):
        """A taller-than-wide graph: min(W, H) is W, the units themselves
        (xsize(3) ysize(6))."""
        st = dr._dash_by_array_styles(
            "foreign, graphregion(margin(large))", dr.SchemeParser("s2color"),
            {"xsize": "3", "ysize": "6"})
        assert st["padding"] == "4.5% 4.5% 4.5% 4.5%"

    @pytest.mark.parametrize("mode", MODES)
    def test_not_named(self, mode):
        assert not [n for n in _notes(mode) if "margin(" in n], _notes(mode)


class TestOutlineOnce:
    def test_fixture(self):
        out = [r for r in _probe("regions_plot_outline")["rects"]
               if r["stroke"] == "#ff0000"]
        assert len(out) == 1 and out[0]["w"] > 3000
        assert len([r for r in _probe("regions_plot_outline4")["rects"]
                    if r["stroke"] == "#ff0000"]) == 1

    @pytest.mark.parametrize("mode", MODES)
    def test_once(self, mode):
        g = _grid(mode, "outline")
        border = dict(g.styles or {}).get("border", "")
        assert "#ff0000" in border and border.endswith("solid #ff0000"), border
        for c in g.children:
            assert str(getattr(c[0], "border_line_color", "")).lower() \
                != "#ff0000"


class TestAltleg:
    def test_fixture(self):
        a, b = _probe("bystyle_altleg"), _probe("bystyle_default")
        assert a["rects"] == b["rects"] and a["texts"] == b["texts"]

    @pytest.mark.parametrize("mode", MODES)
    def test_silent(self, mode):
        assert not [n for n in _notes(mode) if "altleg" in n], _notes(mode)
