"""`dropline` ignored every marker option the help says it takes.

dash.sthlp lists `dropline` among the plot types that accept `mlabel()` and
among those that accept `msangle()`. It honoured neither, and it honoured
`msymbol()`, `msize()` and `malpha()` no better: `map_dropline` built its
scatter renderer with `size=8` and `line_width=1.5` written into the call and
never passed the renderer to `_apply_marker_opts`, which is the one place
those options are read.

    dash dropline mpg weight, msymbol(triangle) msize(large) mlabel(make)

drew default-sized circles with no labels, said nothing, and the note did not
name the options either -- they are honoured elsewhere, so they are not on
the ignoring-unsupported list.

`mlabel()` failed for a second reason: `_apply_mlabel_opts` was called, but
the source it was given carries only x, y, y0 and the two plot variables, so
the label column was never in it.

The two literals are the same ones S11 replaced everywhere else: the marker
size and the line width belong to the scheme, and under economist they are
10.18 and 1.2, not 8 and 1.5.
"""
import os
import sys

import numpy as np
import pytest
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr


@pytest.fixture
def src():
    return ColumnDataSource({
        "mpg":    [22.0, 17.0, 25.0, 30.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0],
        "make":   ["a", "b", "c", "d"],
    })


def _draw(options, scheme="s2color", src=None):
    """Returns (mapper, figure, segment renderer, scatter renderer).

    Named _draw, not _dot: a helper whose name matches a local in the caller
    makes Python treat the name as local throughout the function, and every
    call raises UnboundLocalError before reaching the assertion.
    """
    gm = dr.GlyphMapper(scheme=dr.SchemeParser(scheme))
    fig = figure()
    rs = gm.map_dropline(fig, src, "mpg", "weight", options)
    return gm, fig, rs[0], rs[1]          # segment, scatter


class TestTheMarkerOptionsReachTheDot:
    def test_msymbol_is_honoured(self, src):
        _gm, _f, _seg, dot = _draw({"msymbol": "triangle"}, src=src)
        assert dot.glyph.marker == "triangle", (
            "dropline ignores msymbol(); it draws a circle whatever is asked"
        )

    def test_msize_is_honoured(self, src):
        _gm, _f, _seg, a = _draw({"msize": "large"}, src=src)
        _gm2, _f2, _seg2, b = _draw({"msize": "small"}, src=src)
        assert float(a.glyph.size) > float(b.glyph.size), (
            "dropline ignores msize(); every marker is the same size"
        )

    def test_msangle_is_honoured(self, src):
        _gm, _f, _seg, dot = _draw({"msymbol": "triangle", "msangle": "45"},
                                  src=src)
        assert float(getattr(dot.glyph, "angle", 0) or 0) != 0.0, (
            "dropline ignores msangle(), which dash.sthlp lists it as taking"
        )

    def test_malpha_is_honoured(self, src):
        _gm, _f, _seg, dot = _draw({"malpha": "30"}, src=src)
        assert float(dot.glyph.fill_alpha) == pytest.approx(0.3)

    def test_mcolor_still_wins(self, src):
        """The existing behaviour must survive the change."""
        _gm, _f, _seg, dot = _draw({"mcolor": "maroon"}, src=src)
        assert dot.glyph.fill_color == \
            dr.OptionTranslator().translate_mcolor("maroon")


class TestMarkerLabelsAreDrawn:
    def test_mlabel_produces_a_label_set(self, src):
        _gm, fig, _seg, _dot = _draw({"mlabel": "make"}, src=src)
        labels = [r for r in fig.center if isinstance(r, LabelSet)]
        assert labels, (
            "dash.sthlp lists dropline as taking mlabel(); no labels are "
            "drawn because the label column is not in the source"
        )
        assert labels[0].text == "make"

    def test_no_mlabel_draws_no_labels(self, src):
        """The control: a LabelSet must not appear without the option."""
        _gm, fig, _seg, _dot = _draw({}, src=src)
        assert not [r for r in fig.center if isinstance(r, LabelSet)]


class TestTheSchemeSetsTheSizeAndWidth:
    def test_the_marker_size_comes_from_the_scheme(self, src):
        gm_a, _f, _s, a = _draw({}, scheme="s2color", src=src)
        gm_b, _f2, _s2, b = _draw({}, scheme="economist", src=src)
        assert float(a.glyph.size) == pytest.approx(
            gm_a.scheme.default_marker_size(0))
        assert float(b.glyph.size) == pytest.approx(
            gm_b.scheme.default_marker_size(0))
        assert float(a.glyph.size) != float(b.glyph.size), (
            "the two schemes declare different marker sizes; a literal 8 "
            "would make these equal"
        )

    def test_the_line_width_comes_from_the_scheme(self, src):
        gm_b, _f, seg, _d = _draw({}, scheme="economist", src=src)
        assert float(seg.glyph.line_width) == pytest.approx(
            gm_b.scheme.default_line_width), (
            "the dropline stem is a literal 1.5 whatever the scheme asks for"
        )


class TestScatteriTakesTheSameOptions:
    """dash.sthlp lists scatteri among the plot types msangle() applies to.

    map_scatteri resolved mcolor(), msize() and msymbol() itself and never
    reached _apply_marker_opts, so msangle() and malpha() did nothing there
    either.
    """

    @staticmethod
    def _draw(options):
        gm = dr.GlyphMapper()
        fig = figure()
        r = gm.map_scatteri(fig, [[20.0, 3000.0], [30.0, 4000.0]], options)
        return (r[0] if isinstance(r, list) else r)

    def test_msangle_is_honoured(self):
        r = self._draw({"msymbol": "triangle", "msangle": "45"})
        assert float(getattr(r.glyph, "angle", 0) or 0) != 0.0, (
            "scatteri ignores msangle(), which dash.sthlp lists it as taking"
        )

    def test_malpha_is_honoured(self):
        r = self._draw({"malpha": "30"})
        assert float(r.glyph.fill_alpha) == pytest.approx(0.3)

    def test_the_options_it_already_read_still_work(self):
        r = self._draw({"msymbol": "square", "mcolor": "maroon"})
        assert r.glyph.marker == "square"
        assert r.glyph.fill_color == \
            dr.OptionTranslator().translate_mcolor("maroon")
