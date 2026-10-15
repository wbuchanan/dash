"""`color()` set the series colour on five plot types and was reported dead.

Stata's `color(colorstyle)` is the generic series colour: on `scatter` it is
the marker colour, on `line` the line colour, on `bar` and `area` the fill.
dash read it in `map_area`, `map_bar`, `map_histogram`, `map_dropline` and
`map_rcapsym` -- and nowhere else. `scatter` and `line`, the two most common
plot types in Stata, read only `mcolor()` and `lcolor()`.

So `dash scatter mpg weight, color(navy)` drew the scheme's first colour and
printed

    dash: ignoring unsupported option(s): color()

which was half true and wholly unhelpful: the same option on `bar` was
honoured, silently, while still being named in the note.

The existing measurement in test_unsupported_report_is_true.py tested
`color()` on `scatter`, where it really was dead, and so certified it as
ignored -- the plot type, not the option, was what made the comparison come
out empty. `bands()` was certified the same way, tested on `kdensity` where
Stata does not define it at all.
"""
import os
import re
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr

_ADO = os.path.join(_HERE, "..", "dash.ado")

_X = [1760.0, 2200.0, 3000.0, 3600.0, 4840.0]
_Y = [30.0, 26.0, 21.0, 18.0, 12.0]


@pytest.fixture
def gm():
    return dr.GlyphMapper()


@pytest.fixture
def src():
    return ColumnDataSource({"weight": list(_X), "mpg": list(_Y)})


# navy is s2color's FIRST series colour (#1a476f), so asserting that a
# scatter comes out navy proves nothing at all -- it is what the scheme
# draws anyway. Every colour used below is one the scheme does not pick.
_ALIAS = "orange"
_SPECIFIC = "forest_green"


def _hex(name):
    return dr.OptionTranslator().translate_mcolor(name)


def test_the_test_colours_are_not_the_schemes_own():
    """Guards the guard: a colour equal to the default certifies nothing."""
    gm = dr.GlyphMapper()
    for kind in ("scatter", "line", "bar"):
        assert gm.scheme.default_color(0, kind) not in (
            _hex(_ALIAS), _hex(_SPECIFIC)), (
            f"the {kind} default is one of the colours these tests set, so "
            f"they would pass whether or not the option is read"
        )


class TestColorReachesTheCommonPlotTypes:
    def test_scatter_honours_color(self, gm, src):
        r = gm.map_scatter(figure(), src, "mpg", "weight", {"color": _ALIAS})
        assert r.glyph.fill_color == _hex(_ALIAS), (
            "color() does not reach a scatter's markers"
        )
        assert r.glyph.line_color == _hex(_ALIAS)

    def test_line_honours_color(self, gm, src):
        r = gm.map_line(figure(), src, "mpg", "weight", {"color": _ALIAS})
        assert r.glyph.line_color == _hex(_ALIAS), (
            "color() does not reach a line"
        )

    def test_mcolor_still_wins_over_color(self, gm, src):
        """The specific spelling is not overridden by the generic one."""
        r = gm.map_scatter(figure(), src, "mpg", "weight",
                           {"color": _ALIAS, "mcolor": _SPECIFIC})
        assert r.glyph.fill_color == \
            _hex(_SPECIFIC)

    def test_lcolor_still_wins_over_color(self, gm, src):
        r = gm.map_line(figure(), src, "mpg", "weight",
                        {"color": _ALIAS, "lcolor": _SPECIFIC})
        assert r.glyph.line_color == \
            _hex(_SPECIFIC)

    def test_a_bars_own_line_colour_still_wins(self, gm, src):
        """blcolor() is applied after color(); it must stay on top."""
        r = gm.map_bar(figure(), src, "mpg", "weight",
                       {"color": _ALIAS, "blcolor": _SPECIFIC})
        glyph = r.glyph if not isinstance(r, list) else r[0].glyph
        assert glyph.line_color == \
            _hex(_SPECIFIC)

    def test_bar_still_honours_color(self, gm, src):
        r = gm.map_bar(figure(), src, "mpg", "weight", {"color": _ALIAS})
        glyph = r.glyph if not isinstance(r, list) else r[0].glyph
        # Orange (#ff7f00) filled at the bar's intensity, inten80 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        assert glyph.fill_color == "#ff9933"
        assert glyph.line_color == _hex(_ALIAS)

    @pytest.mark.parametrize("mapper,prop,kind", [
        ("map_scatter", "fill_color", "scatter"),
        ("map_line", "line_color", "line"),
    ])
    def test_a_bad_colour_name_does_not_take_the_render_down(
            self, gm, src, mapper, prop, kind):
        """It draws black and says so -- what twoway does with a colour it
        cannot read ("named style ... not found in class color").
        Flipped (WP-30 P1.13a): it drew the scheme's default; twoway draws
        black (colour_grammar_truth.json opt_87, site_02)."""
        dr._dash_reset_notes()          # the note is made once per render
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = getattr(gm, mapper)(figure(), src, "mpg", "weight",
                                    {"color": "not_a_colour"})
        glyph = (r[0] if isinstance(r, list) else r).glyph
        assert getattr(glyph, prop) == "#000000"
        assert ("dash: color(not_a_colour) is not a recognised colour; "
                "using black.") in \
            [str(c.message) for c in caught]


def _pending(prog):
    with open(_ADO, encoding="utf-8") as fh:
        s = fh.read()
    i = s.index("program define " + prog)
    j = s.index("local _dash_unknown", i)
    return re.findall(r"_dash_pending' (\w+)\"", s[i:j])


def _plot_pending():
    """_dash_parse_plot_opts's pending names, with a positive control.

    An absence check on an empty list passes whatever dash.ado says: were
    the local renamed, or its lines reworded, the reader above would find
    nothing and "color not in []" would hold.  at() and fxsize() are
    pending on every plot type -- 44 names in all, measured 24sep2026 -- so
    the reader must find them before its silence about color() means
    anything.  (Flipped, WP-31 D2: b1title() was the second control; it is
    drawn now, as twoway draws it, and pending no more.)
    """
    pending = _pending("_dash_parse_plot_opts")
    assert {"at", "fxsize"} <= set(pending), (
        f"the pending-list reader no longer finds options that are pending: "
        f"{pending}"
    )
    return pending


class TestTheNoteNoLongerNamesThem:
    def test_color_is_not_reported_unsupported(self):
        assert "color" not in _plot_pending(), (
            "color() sets the series colour, but dash.ado still names it in "
            "the ignoring-unsupported note"
        )

    def test_bands_is_not_reported_unsupported(self):
        assert "bands" not in _plot_pending(), (
            "bands() sets the median-band count, but dash.ado still names it "
            "in the ignoring-unsupported note"
        )


class TestBandsSetsTheBandCount:
    """Measured: mband draws 9 bands by Stata's rule, 5 with bands(5)."""

    def _n_points(self, gm, opts):
        rng = np.random.default_rng(1)
        w = np.linspace(1760, 4840, 74)
        m = 40 - 0.0055 * w + rng.normal(0, 1.8, 74)
        s = ColumnDataSource({"weight": w.tolist(), "mpg": m.tolist()})
        r = gm.map_mband(figure(), s, "mpg", "weight", opts)
        ds = (r[0] if isinstance(r, list) else r).data_source
        col = next((c for c in ds.data if len(ds.data[c])), None)
        return len(ds.data[col]) if col else 0

    def test_the_default_is_statas_rule(self, gm):
        assert self._n_points(gm, {}) == 9

    def test_bands_overrides_it(self, gm):
        assert self._n_points(gm, {"bands": "5"}) == 5
        assert self._n_points(gm, {"bands": "20"}) == 20
