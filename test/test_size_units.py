"""
test_size_units.py -- marker, text and label-gap sizes in Stata's units
(WP-30 P1.12a).

The defect (BUGS.md P1.12a): dash read a size through one private pixel
ladder (``OptionTranslator._SIZE_MAP``), so ``msize(medium)`` drew 11 px
against an 8 px default, ``msize(1.52778)`` (Stata's own medium) drew 1 px,
``title("T", size(large))`` drew 15px under a 14pt default title,
``size(5)`` 5px where twoway draws 14.4pt, ``msize(4pt)``, ``*2`` and
``vhuge`` were noted and ignored, and a marker label sat a fixed 4 px from
its point whatever the marker's size.

twoway's truth (StataNow 19.5; s2color 5.5 x 4 in, 1 relative unit =
2.88pt at the 4-inch reference = 3.84 CSS px): ``symbolsize medium`` is
1.52778 units (5.8667 px), ``gsize large`` 4.8611 units (14pt), a bare
number is a relative unit, ``#pt``/``#in``/``#cm`` are absolute and scale
with the graph's smaller side, ``*#`` multiplies what would be drawn, an
unknown or wrong-case name draws medium with a note, and a label's anchor
sits (marker radius + gap) from its point along the clock direction, with
a default gap of ``half_tiny`` (2pt).  Every expectation below is that
literal twoway value, never one computed through dash.

The fixture-driven classes read ``test/fixtures/size_units_truth.json``
(``scripts/extract_size_units_truth.do``).
"""
import itertools
import json
import math
import os
import re
import sys
import time
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_MODES = ("saved", "served")
_PX_PER_RS = 3.84          # 2.88pt x 4/3
_PT_PER_RS = 2.88

# ---------------------------------------------------------------------------
# Building a figure in either mode (copied from test_scheme_linewidth.py's
# ``_figure``, with graph options, build options and the notes added)
# ---------------------------------------------------------------------------

_SEQ = itertools.count()
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "make": ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
             "Buick Electra", "Buick LeSabre", "Buick Opel", "Buick Regal",
             "Buick Riviera", "Buick Skylark"],
})
_DF["mpg2"] = _DF["mpg"] + 5.0
_DF["weight2"] = _DF["weight"] + 300.0


def _spec(plots, scheme, go=None, bo=None):
    g = {"name": "g1", "title": '"t"'}
    g.update(go or {})
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": scheme, "session_scheme": "", "title": "",
         "subtitle": "", "registry": "g1", "tabs": "",
         "filter_position": "top", "csv": "0", "level": "95",
         "formats": {}, "limits": {}}
    b.update(bo or {})
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "build_options": b}


def _inputs(wd, plots, scheme, go, bo):
    tag = next(_SEQ)
    wd = Path(wd)
    sp = wd / ("spec_%d.json" % tag)
    dp = wd / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, scheme, go, bo)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    return tag, str(sp), str(dp)


def _is_figure(m):
    from bokeh.plotting import figure as _fig_cls
    return isinstance(m, _fig_cls)


def _build(mode, wd, plots, scheme="s2color", go=None, bo=None, patch=None):
    """(every figure, the notes, the served document or None).

    *patch* is called with the GlyphMapper class the mode draws with (the
    module's, or the served app's own copy) before anything is drawn.
    """
    from bokeh.document import Document
    tag, sp, dp = _inputs(wd, plots, scheme, go, bo)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            dr._dash_reset_notes()
            if patch is not None:
                patch(dr.GlyphMapper)
            r = dr.DashRenderer(sp, dp)
            figs = list(r._build_figures().values())
            doc = None
        else:
            ap = str(Path(wd) / ("app_%d.py" % tag))
            dr.ServerAppBuilder(sp, dp).build(ap)
            # The app's import renders once on its own; its notes are not
            # the document's (test_option_validation._both loads it so).
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mod = load_app(ap, "_su_app_%d" % tag)
            # The import's own render leaves its models in the global
            # document; clear them so a loop of builds stays as fast as one.
            from bokeh.io import curdoc
            curdoc().clear()
            if patch is not None:
                patch(mod.GlyphMapper)
            doc = Document()
            mod.make_document(doc)
            figs = [m for root in doc.roots for m in root.references()
                    if _is_figure(m)]
    return figs, [str(w.message) for w in caught], doc


def _figure(mode, wd, plots, scheme="s2color", go=None, bo=None):
    """The one figure *plots* draw in *mode* under *scheme*."""
    figs, _, _ = _build(mode, wd, plots, scheme, go, bo)
    assert len(figs) == 1, figs
    return figs[0]


def _figure_notes(mode, wd, plots, scheme="s2color", go=None, bo=None):
    figs, notes, _ = _build(mode, wd, plots, scheme, go, bo)
    assert len(figs) == 1, figs
    return figs[0], notes


def _sc(**o):
    return {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": o}


def _sc2(**o):
    return {"type": "scatter", "yvar": "price", "xvar": "weight",
            "options": o}


# ---------------------------------------------------------------------------
# Reading what was drawn (test-side parsing, never dash's helpers)
# ---------------------------------------------------------------------------

def _pt(css):
    """A CSS font size in points: ``14pt`` 14, ``16px`` 12."""
    m = re.fullmatch(r"\s*([-+]?[0-9]*\.?[0-9]+)(pt|px)\s*", str(css))
    assert m, "not a pt/px size: %r" % (css,)
    v = float(m.group(1))
    return v if m.group(2) == "pt" else v * 0.75


def _scatters(fig):
    return [r for r in fig.renderers
            if type(getattr(r, "glyph", None)).__name__ == "Scatter"]


def _marker(fig):
    """The first Scatter glyph's size, in px."""
    sc = _scatters(fig)
    assert sc, "no Scatter glyph"
    return float(sc[0].glyph.size)


def _of_type(fig, name):
    return [m for m in fig.references() if type(m).__name__ == name]


def _labelsets(fig):
    return _of_type(fig, "LabelSet")


def _one_labelset(fig):
    ls = _labelsets(fig)
    assert len(ls) == 1, ls
    return ls[0]


def _yaxis(fig):
    return fig.left[0]


def _axis2(fig):
    """The second y axis (a yaxis(2) layer's)."""
    axes = [a for a in list(fig.left) + list(fig.right)
            if type(a).__name__.endswith("Axis")
            and getattr(a, "y_range_name", "default") != "default"]
    assert len(axes) == 1, axes
    return axes[0]


def _label_text(fig, text):
    # Flipped (WP-30 P1.2a): Labels only was wrong because twoway places
    # subtitle(), note() and caption() by the scheme's clock, which S15
    # draws as side-panel Titles (the figure's own title excluded).
    hits = [m for m in _of_type(fig, "Label") + _of_type(fig, "Title")
            if m.text == text and m is not fig.title]
    assert len(hits) == 1, hits
    return hits[0]


def _legends(fig):
    lg = _of_type(fig, "Legend")
    assert lg, "no legend"
    return lg


def _colorbar(fig):
    cb = _of_type(fig, "ColorBar")
    assert len(cb) == 1, cb
    return cb[0]


def _size_notes(notes, head):
    """The size notes naming *head* (``msize(abc)``,
    ``title(size(abc))``), however S06 frames them."""
    return [n for n in notes if head in n and "recognised size" in n]


def _assert_one_medium_note(notes, head):
    hits = _size_notes(notes, head)
    assert len(hits) == 1, "expected one note naming %s, got %r" % (
        head, notes)
    if head.startswith("msize("):
        # A marker draws the scheme's own default (its bare symbolsize),
        # as twoway's "default attributes used" does: medium under s2color
        # and stcolor, large under economist (fixture economist_marker_20).
        assert "the scheme's default" in hits[0], hits[0]
    else:
        assert "medium" in hits[0], hits[0]


def _offset(fig):
    ls = _one_labelset(fig)
    return float(ls.x_offset), float(ls.y_offset)


# Twoway's clock directions, in Bokeh's y-up screen offsets.
def _unit(p):
    a = math.radians(90.0 - 30.0 * p)
    return math.cos(a), math.sin(a)


_S2_R = 1.52778 * _PX_PER_RS / 2.0       # 2.93334 px, the default radius
_GAP = 2.0 * 4.0 / 3.0                   # 2pt, 2.66667 px


# ===========================================================================
# 08-01: unit tests of the resolver and its helpers
# ===========================================================================

_SYMBOLSIZE_RS = {
    "zero": 0.0, "vtiny": 0.1, "tiny": 0.34722222, "vsmall": 0.520833,
    "small": 1.04166, "medsmall": 1.25, "medium": 1.52778,
    "medlarge": 1.94444, "large": 2.4306, "vlarge": 3.125,
    "huge": 4.8611, "vhuge": 5.555, "ehuge": 11.111,
}
_SYMBOLSIZE_ABS_PT = {"2-pt": 2, "3-pt": 3, "4-pt": 4, "6-pt": 6,
                      "11-pt": 11, "12-pt": 12, "14-pt": 14, "16-pt": 16,
                      "20-pt": 20, "24-pt": 24}
_GSIZE_RS = {
    "zero": 0.0, "minuscule": 0.3472, "quarter_tiny": 0.34722,
    "third_tiny": 0.46296, "half_tiny": 0.6944, "tiny": 1.3888,
    "vsmall": 2.0833, "small": 2.777, "medsmall": 3.4722,
    "medium": 3.8194, "medlarge": 4.1667, "large": 4.8611,
    "vlarge": 5.5556, "huge": 6.9444, "vhuge": 9.7222, "default": 4.166,
    "tenth": 10.0, "quarter": 25.0, "third": 33.333333333333, "half": 50.0,
    "full": 100.0, "relative0p3": 0.3, "relative0p6": 0.6,
    "relative1p2": 1.2, "relative1p5": 1.5, "relative2p2": 2.2,
    "relative3": 3.0, "relative3p5": 3.5, "relative4": 4.0,
    "relative5": 5.0, "relative8": 8.0, "relative12": 12.0,
}
_GSIZE_ABS_PT = {"1-pt": 1, "2-pt": 2, "3-pt": 3, "4-pt": 4, "6-pt": 6,
                 "8-pt": 8, "10-pt": 10, "11-pt": 11, "12-pt": 12,
                 "14-pt": 14, "16-pt": 16, "20-pt": 20, "24-pt": 24,
                 "32-pt": 32, "180-pt": 180}


def _rs():
    return dr.OptionTranslator.resolve_size


class TestResolveSize:

    def test_a_number_is_statas_relative_unit(self):
        assert _rs()("1.52778", "marker", 4.4) == pytest.approx(4.40001,
                                                                 abs=1e-4)
        assert _rs()("5", "text", 11) == pytest.approx(14.4, abs=1e-6)

    def test_absolute_units_at_the_reference(self):
        assert _rs()("4pt", "marker", 4.4) == pytest.approx(4.0)
        assert _rs()("4pt", "marker", 4.4, 4.5) == pytest.approx(3.5556,
                                                                 abs=1e-4)
        assert _rs()(".1in", "marker", 4.4) == pytest.approx(7.2)
        assert _rs()(".2cm", "marker", 4.4) == pytest.approx(5.669, abs=1e-3)
        assert _rs()("1.52778rs", "marker", 4.4) == pytest.approx(
            4.40001, abs=1e-4)

    def test_a_blank_before_a_unit(self):
        assert _rs()("4 pt", "text", 11) == pytest.approx(4.0)
        assert _rs()("4 in", "text", 11) == pytest.approx(288.0)

    def test_the_multiplier(self):
        assert _rs()("*2", "text", 14) == pytest.approx(28.0)
        assert _rs()("*.5", "text", 14) == pytest.approx(7.0)
        assert _rs()("*-1", "text", 14) == pytest.approx(-14.0)

    def test_every_symbolsize_keyword(self):
        for name, rs in _SYMBOLSIZE_RS.items():
            assert _rs()(name, "marker", 4.4) == pytest.approx(
                rs * 2.88, abs=1e-6), name

    def test_every_gsize_keyword(self):
        for name, rs in _GSIZE_RS.items():
            assert _rs()(name, "text", 11) == pytest.approx(
                rs * 2.88, abs=1e-6), name
            assert _rs()(name, "gap", 2) == pytest.approx(
                rs * 2.88, abs=1e-6), name
        assert _rs()("10-pt", "text", 11) == pytest.approx(10.0)
        for name, pt in _GSIZE_ABS_PT.items():
            assert _rs()(name, "text", 11) == pytest.approx(pt), name
        for name, pt in _SYMBOLSIZE_ABS_PT.items():
            assert _rs()(name, "marker", 4.4) == pytest.approx(pt), name

    def test_names_are_case_sensitive(self):
        for raw in ("HUGE", "Large", "4PT", "4Pt"):
            for kind in ("marker", "text", "gap"):
                with pytest.raises(ValueError):
                    _rs()(raw, kind, 4.4)

    def test_ehuge_and_vtiny_are_not_text_sizes(self):
        for name in ("ehuge", "vtiny"):
            with pytest.raises(ValueError):
                _rs()(name, "text", 11)
        assert _rs()("ehuge", "marker", 4.4) == pytest.approx(11.111 * 2.88)
        assert _rs()("vtiny", "marker", 4.4) == pytest.approx(0.1 * 2.88)

    def test_statas_d_exponent(self):
        assert _rs()("1d3", "text", 11) == pytest.approx(1000 * 2.88)

    def test_what_is_not_a_size_raises(self):
        for raw in ("abc", "", "5px", "inf", "nan", "٥", "0x10",
                    "1_000", "--5", "5e", "5,0", "0" * 64 + "1", "1001"):
            with pytest.raises(ValueError):
                _rs()(raw, "text", 11)

    def test_an_unknown_kind_raises(self):
        with pytest.raises(ValueError):
            _rs()("5", "colour", 11)


class TestStataNumberAndMultiplier:

    def test_stata_number_reads_statas_spellings(self):
        sn = dr.OptionTranslator.stata_number
        assert sn(".5") == pytest.approx(0.5)
        assert sn("-2") == pytest.approx(-2.0)
        assert sn("1e2") == pytest.approx(100.0)
        assert sn("1d3") == pytest.approx(1000.0)
        for bad in ("abc", "inf", "nan", "٥", "1_000", ""):
            assert sn(bad) is None, bad

    def test_size_multiplier_reads_star_number_only(self):
        sm = dr.OptionTranslator.size_multiplier
        assert sm("*2") == pytest.approx(2.0)
        assert sm("* .5") == pytest.approx(0.5)
        for bad in ("2", "**2", "*abc"):
            assert sm(bad) is None, bad


class TestCssHelpers:

    def test_css_pt_writes_two_fixed_decimals(self):
        cp = dr.OptionTranslator.css_pt
        assert cp(7.99776) == "8pt"
        assert cp(14.4) == "14.4pt"
        assert cp(1e-6) == "0pt"
        assert cp(-3) == "0pt"
        assert cp(2880) == "2880pt"
        for v in (1e-6, 1e-9, 2880, 12.444444, 0.005):
            assert "e" not in cp(v).replace("pt", ""), cp(v)

    def test_css_to_pt_reads_pt_and_px(self):
        cp = dr.OptionTranslator.css_to_pt
        assert cp("14pt") == pytest.approx(14.0)
        assert cp("16px") == pytest.approx(12.0)
        assert cp("1em") is None


# ===========================================================================
# 08-01: both modes, end to end
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestTheDefaultSizes:

    def test_the_default_marker(self, mode, tmp_path):
        assert _marker(_figure(mode, tmp_path, [_sc()])) == pytest.approx(
            5.8667, abs=1e-3)
        assert _marker(_figure(mode, tmp_path, [_sc()], "stcolor")) == \
            pytest.approx(4.0, abs=1e-3)
        assert _marker(_figure(mode, tmp_path, [_sc()], "economist")) == \
            pytest.approx(9.3335, abs=1e-3)


@pytest.mark.parametrize("mode", _MODES)
class TestExplicitMarkerSizes:

    def test_medium_equals_the_default(self, mode, tmp_path):
        default = _marker(_figure(mode, tmp_path, [_sc()]))
        assert _marker(_figure(mode, tmp_path, [_sc(msize="medium")])) == \
            default
        assert default == pytest.approx(5.8667, abs=1e-3)

    def test_numbers_units_and_star(self, mode, tmp_path):
        for raw, px in (("1.52778", 5.8667), ("4pt", 5.3333),
                        ("*2", 11.7334), ("vhuge", 21.331), (".1in", 9.6)):
            fig, notes = _figure_notes(mode, tmp_path, [_sc(msize=raw)])
            assert _marker(fig) == pytest.approx(px, abs=1e-3), raw
            assert not _size_notes(notes, "msize("), (raw, notes)

    def test_star_doubles_the_schemes_default(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc(msize="*2")], "stcolor")
        assert _marker(fig) == pytest.approx(8.0, abs=1e-3)

    def test_negative_or_zero_draws_nothing_silently(self, mode, tmp_path):
        for raw in ("-1", "*-1", "-1pt", "0"):
            fig, notes = _figure_notes(mode, tmp_path, [_sc(msize=raw)])
            assert _marker(fig) == 0, raw
            assert not [n for n in notes if "msize(" in n], (raw, notes)


@pytest.mark.parametrize("mode", _MODES)
class TestExplicitTextSizes:

    def test_title_large_is_the_heading(self, mode, tmp_path):
        default = _figure(mode, tmp_path, [_sc()], go={"title": '"T"'})
        fig = _figure(mode, tmp_path, [_sc()],
                      go={"title": '"T", size(large)'})
        assert fig.title.text_font_size == "14pt"
        assert fig.title.text_font_size == default.title.text_font_size

    def test_title_numbers_units_and_star(self, mode, tmp_path):
        for raw, css in (("5", "14.4pt"), ("12pt", "12pt"), ("*2", "28pt"),
                         ("vhuge", "28pt"), ("tenth", "28.8pt"),
                         ("relative3", "8.64pt"), ("10-pt", "10pt"),
                         ("4 pt", "4pt")):
            fig, notes = _figure_notes(mode, tmp_path, [_sc()],
                                       go={"title": '"T", size(%s)' % raw})
            assert fig.title.text_font_size == css, raw
        assert not _size_notes(notes, "size("), notes

    def test_axis_titles_subtitle_note_and_axis_two(self, mode, tmp_path):
        base = _figure(mode, tmp_path, [_sc()], go={"note": '"N"'})
        note_pt = _pt(_label_text(base, "N").text_font_size)
        fig = _figure(mode, tmp_path, [_sc()], go={
            "ytitle": ", size(large)", "subtitle": '"S", size(5)',
            "note": '"N", size(*2)'})
        assert _yaxis(fig).axis_label_text_font_size == "14pt"
        assert _label_text(fig, "S").text_font_size == "14.4pt"
        assert _pt(_label_text(fig, "N").text_font_size) == pytest.approx(
            2 * note_pt, abs=0.01)
        two = _figure(mode, tmp_path, [_sc(), _sc2(yaxis="2")],
                      go={"ytitle2": ", size(5)"})
        assert _axis2(two).axis_label_text_font_size == "14.4pt"

    def test_labsize(self, mode, tmp_path):
        default = _pt(_yaxis(_figure(mode, tmp_path, [_sc()]))
                      .major_label_text_font_size)
        for raw, css in (("5", "14.4pt"), ("medium", "11pt"),
                         ("10pt", "10pt")):
            fig = _figure(mode, tmp_path, [_sc()],
                          go={"ylabel": ", labsize(%s)" % raw})
            assert _yaxis(fig).major_label_text_font_size == css, raw
        fig = _figure(mode, tmp_path, [_sc()], go={"ylabel": ", labsize(*2)"})
        assert _pt(_yaxis(fig).major_label_text_font_size) == pytest.approx(
            2 * default, abs=0.01)

    def test_mlabsize(self, mode, tmp_path):
        for raw, css in (("medium", "11pt"), ("5", "14.4pt"),
                         ("10pt", "10pt")):
            fig = _figure(mode, tmp_path, [_sc(mlabel="make", mlabsize=raw)])
            assert _one_labelset(fig).text_font_size == css, raw

    def test_legend_size(self, mode, tmp_path):
        plots = [_sc(), _sc2(yaxis="2")]
        default = _pt(_legends(_figure(mode, tmp_path, plots))[0]
                      .label_text_font_size)
        for raw, css in (("5", "14.4pt"), ("large", "14pt"),
                         ("12pt", "12pt")):
            fig = _figure(mode, tmp_path, plots,
                          go={"legend": "size(%s)" % raw})
            for lg in _legends(fig):
                assert lg.label_text_font_size == css, raw
        fig = _figure(mode, tmp_path, plots, go={"legend": "size(*2)"})
        for lg in _legends(fig):
            assert _pt(lg.label_text_font_size) == pytest.approx(
                2 * default, abs=0.01)

    def test_the_colour_key(self, mode, tmp_path):
        fig, notes = _figure_notes(mode, tmp_path, [_sc(colorvar="price")],
                                   go={"zlabel": ", labsize(large)"})
        assert _colorbar(fig).major_label_text_font_size == "14pt"
        assert not [n for n in notes if "zlabel" in n or "labsize" in n], \
            notes
        fig = _figure(mode, tmp_path, [_sc(colorvar="price")],
                      go={"ztitle": '"Z", size(large)'})
        assert _colorbar(fig).title_text_font_size == "14pt"


@pytest.mark.parametrize("mode", _MODES)
class TestAbsoluteUnitsFollowTheSchemesReference:

    def test_title_and_marker(self, mode, tmp_path):
        def title(scheme, raw):
            return _pt(_figure(mode, tmp_path, [_sc()], scheme,
                               go={"title": '"T", size(%s)' % raw})
                       .title.text_font_size)
        assert title("stcolor", "14pt") == pytest.approx(12.444, abs=0.01)
        assert title("stcolor", "large") == pytest.approx(14.0, abs=0.01)
        assert title("economist", "14pt") == pytest.approx(25.455, abs=0.01)
        assert title("s2color", "14pt") == pytest.approx(14.0, abs=0.01)
        fig = _figure(mode, tmp_path, [_sc(msize="4pt")], "stcolor")
        assert _marker(fig) == pytest.approx(4.7407, abs=1e-3)


class TestUnknownNamesDrawMedium:

    @pytest.mark.parametrize("mode", _MODES)
    def test_markers(self, mode, tmp_path):
        # An unknown name, a wrong-case name and a wrong-case unit.
        for raw in ("abc", "Large", "4PT"):
            fig, notes = _figure_notes(mode, tmp_path, [_sc(msize=raw)])
            assert _marker(fig) == pytest.approx(5.8667, abs=1e-3), raw
            _assert_one_medium_note(notes, "msize(%s)" % raw)
        fig, notes = _figure_notes(mode, tmp_path, [_sc(msize="abc")],
                                   "stcolor")
        assert _marker(fig) == pytest.approx(5.8667, abs=1e-3)
        _assert_one_medium_note(notes, "msize(abc)")

    @pytest.mark.parametrize("mode", _MODES)
    def test_text_and_gaps(self, mode, tmp_path):
        for raw in ("abc", "LARGE"):
            fig, notes = _figure_notes(mode, tmp_path, [_sc()],
                                       go={"title": '"T", size(%s)' % raw})
            assert fig.title.text_font_size == "11pt", raw
            _assert_one_medium_note(notes, "title(size(%s))" % raw)
        fig, notes = _figure_notes(mode, tmp_path,
                                   [_sc(mlabel="make", mlabsize="abc")])
        assert _one_labelset(fig).text_font_size == "11pt"
        _assert_one_medium_note(notes, "mlabsize(abc)")
        fig, notes = _figure_notes(mode, tmp_path, [_sc(), _sc2(yaxis="2")],
                                   go={"legend": "size(abc)"})
        for lg in _legends(fig):
            assert lg.label_text_font_size == "11pt"
        _assert_one_medium_note(notes, "legend(size(abc))")
        fig, notes = _figure_notes(mode, tmp_path, [_sc()],
                                   go={"ylabel": ", labsize(abc)"})
        assert _yaxis(fig).major_label_text_font_size == "11pt"
        _assert_one_medium_note(notes, "labsize(abc)")
        fig, notes = _figure_notes(mode, tmp_path,
                                   [_sc(mlabel="make", mlabgap="abc")])
        assert _offset(fig) == (pytest.approx(2.933 + 14.667, abs=0.01),
                                pytest.approx(0, abs=1e-6))
        _assert_one_medium_note(notes, "mlabgap(abc)")

    def test_the_medium_of_each_class(self):
        smp = dr.OptionTranslator.size_medium_pt
        assert smp("marker") == pytest.approx(4.40001, abs=1e-4)
        assert smp("text") == pytest.approx(10.99987, abs=1e-4)
        assert smp("gap") == pytest.approx(10.99987, abs=1e-4)


class TestMarkerLabelsFromTheMarkerEdge:

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_gap_is_from_the_edge(self, mode, tmp_path):
        for gap, dx in ((None, 5.6), ("0", 2.933), ("5", 22.133),
                        ("10pt", 16.267), ("*2", 8.267), ("-2", -4.747)):
            o = {"mlabel": "make"}
            if gap is not None:
                o["mlabgap"] = gap
            fig = _figure(mode, tmp_path, [_sc(**o)])
            assert _offset(fig) == (pytest.approx(dx, abs=0.01),
                                    pytest.approx(0, abs=1e-6)), gap

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_radius_follows_msize(self, mode, tmp_path):
        for ms, dx in (("large", 4.667), ("small", 2.0), ("-1", -1.92)):
            fig = _figure(mode, tmp_path,
                          [_sc(mlabel="make", msize=ms, mlabgap="0")])
            assert _offset(fig) == (pytest.approx(dx, abs=0.01),
                                    pytest.approx(0, abs=1e-6)), ms

    @pytest.mark.parametrize("mode", _MODES)
    def test_every_clock(self, mode, tmp_path):
        for p, want in (("12", (0.0, 5.6)), ("2", (4.850, 2.8)),
                        ("4", (4.850, -2.8)), ("6", (0.0, -5.6)),
                        ("9", (-5.6, 0.0))):
            fig = _figure(mode, tmp_path,
                          [_sc(mlabel="make", mlabposition=p)])
            x, y = _offset(fig)
            assert (x, y) == (pytest.approx(want[0], abs=0.01),
                              pytest.approx(want[1], abs=0.01)), p
        fig = _figure(mode, tmp_path, [_sc(mlabel="make", mlabposition="0",
                                           mlabgap="5")])
        assert _offset(fig) == (0, 0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_marker_types(self, mode, tmp_path):
        def pc(t, **o):
            return {"type": t, "y1var": "mpg", "x1var": "weight",
                    "y2var": "mpg2", "x2var": "weight2",
                    "options": dict(o, mlabel="make")}

        def bar(**o):
            return {"type": "bar", "yvar": "mpg", "xvar": "weight",
                    "options": dict(o, mlabel="make")}
        for make in (bar, lambda **o: pc("pcarrow", **o),
                     lambda **o: pc("pcbarrow", **o)):
            fig = _figure(mode, tmp_path, [make()])
            assert math.hypot(*_offset(fig)) == pytest.approx(5.6, abs=0.01)
            fig = _figure(mode, tmp_path, [make(msize="large", mlabgap="0")])
            assert math.hypot(*_offset(fig)) == pytest.approx(4.667,
                                                              abs=0.01)
        fig = _figure(mode, tmp_path, [{
            "type": "scatteri", "values": [[20.0, 3000.0, "lab", 3]],
            "options": {}}])
        assert _offset(fig) == (pytest.approx(5.6, abs=0.01),
                                pytest.approx(0, abs=1e-6))
        fig = _figure(mode, tmp_path, [{
            "type": "pcarrowi",
            "values": [[20.0, 3000.0, 25.0, 3300.0, "lab", 3]],
            "options": {}}])
        assert _offset(fig) == (pytest.approx(5.6, abs=0.01),
                                pytest.approx(0, abs=1e-6))

    @pytest.mark.parametrize("mode", _MODES)
    def test_under_stcolor(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc(mlabel="make")], "stcolor")
        assert _offset(fig) == (pytest.approx(2.0 + 2.667, abs=0.01),
                                pytest.approx(0, abs=1e-6))

    def test_the_radius_helper(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        assert gm._mlabel_radius_px({"msize": "large"}, 5.8667) == \
            pytest.approx(4.6668, abs=1e-3)
        assert gm._mlabel_radius_px({}, 4.0) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# A filter move, the reference stamp and hostile values
# ---------------------------------------------------------------------------

def _sizes(fig):
    """Every size S08 draws on *fig*, in a comparable form."""
    out = {"markers": [round(float(r.glyph.size), 4) for r in _scatters(fig)
                       if isinstance(r.glyph.size, (int, float))],
           "title": fig.title.text_font_size,
           "labels": [(round(float(ls.x_offset), 4),
                       round(float(ls.y_offset), 4), ls.text_font_size)
                      for ls in _labelsets(fig)],
           "ticks": [a.major_label_text_font_size for a in fig.left],
           "legend": [lg.label_text_font_size for lg in _of_type(fig,
                                                                 "Legend")]}
    return out


class TestBothModesAfterAMove:

    def test_sizes_survive_a_move(self, tmp_path):
        from test_served_linked_views import _served_doc, _fire
        from test_adversarial_matrix import _write_inputs
        graph = {"plots": [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"msize": "large"}},
            {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {"mlabel": "foreign", "mlabgap": "5",
                         "yaxis": "2"}}],
            "graph_options": {"name": "g1", "title": '"T", size(*2)',
                              "ylabel": ", labsize(5)",
                              "legend": "size(large)"},
            "if_expr": "", "in_expr": ""}
        spec = {"graphs": [graph], "kpis": [],
                "build_options": {"layout": "auto", "link": "", "theme": "",
                                  "title": "", "subtitle": "",
                                  "filter": "weight, type(range)",
                                  "registry": "g1"}}
        doc = _served_doc(tmp_path, spec)
        [fig] = [m for root in doc.roots for m in root.references()
                 if _is_figure(m)]
        before = _sizes(fig)
        _fire(doc, "weight", (2000.0, 3500.0))
        assert _sizes(fig) == before
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        [saved] = list(r.figures.values())
        assert _sizes(saved) == before
        # twoway's values: msize(large) 2.4306 units, the second layer's
        # label (medium marker) radius 2.933 + 5 units 19.2 px, title 2 x
        # 14pt, labsize(5) 14.4pt, legend large 14pt.
        assert before["markers"][0] == pytest.approx(9.3335, abs=1e-3)
        [lab] = before["labels"]
        assert lab[0] == pytest.approx(22.133, abs=0.01)
        assert before["title"] == "28pt"
        assert before["ticks"][0] == "14.4pt"
        assert before["legend"] and set(before["legend"]) == {"14pt"}

    def test_no_saved_script_writes_a_size(self):
        """Guard (E3): no module-level JavaScript of dash_render writes a
        size, so a saved filter move cannot change one."""
        pat = re.compile(r"\.size\s*=|font_size\s*=|x_offset\s*=|"
                         r"y_offset\s*=")
        scripts = {k: v for k, v in vars(dr).items()
                   if isinstance(v, str) and len(v) > 200
                   and (k.endswith("_JS") or "_JS_" in k or "cb_obj" in v
                        or re.search(r"\b(?:const|let|var)\s+\w+\s*=", v))}
        assert "_FILTER_JS" in scripts, sorted(scripts)
        hits = {k: pat.findall(v) for k, v in scripts.items()
                if pat.search(v)}
        assert hits == {}, hits


_REF = {"s2color": 4.0, "stcolor": 4.5, "economist": 2.2}


class TestTheReferenceStamp:

    @pytest.mark.parametrize("mode", _MODES)
    def test_every_figure_carries_it(self, mode, tmp_path):
        for scheme in sorted(_REF):
            for go in (None, {"by": "foreign"}):
                figs, _, _ = _build(mode, tmp_path, [_sc()], scheme, go)
                assert figs
                for f in figs:
                    assert getattr(f, "_dash_size_ref_in", None) == \
                        pytest.approx(_REF[scheme]), (scheme, go)
            assert dr.SchemeParser(scheme).size_ref_in == pytest.approx(
                _REF[scheme])

    def test_size_ref_of_reads_the_stamp(self):
        ref = dr.OptionTranslator.size_ref_of
        assert ref(object()) == 4.0
        assert ref(types.SimpleNamespace(_dash_size_ref_in=4.5)) == 4.5
        for bad in ("x", float("nan"), -1, 1e9):
            assert ref(types.SimpleNamespace(_dash_size_ref_in=bad)) == 4.0

    def test_it_is_never_serialised(self, tmp_path):
        """Guard: the stamp is a Python attribute only (a non-default
        reference, so a written stamp would show)."""
        _tag, sp, dp = _inputs(tmp_path, [_sc(mlabel="make")], "stcolor",
                               {"title": '"T", size(14pt)'}, None)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(sp, dp).render()
        assert "<html" in html.lower()
        assert "_dash_size_ref_in" not in html


class TestAdversarialSizes:

    def test_a_megabyte_value_is_judged_at_once(self):
        t0 = time.perf_counter()
        with pytest.raises(ValueError):
            dr.OptionTranslator.resolve_size("9" * 10 ** 6, "text", 11)
        assert time.perf_counter() - t0 < 0.1

    def test_hostile_text_never_reaches_a_style(self, tmp_path):
        hostile = "</style><script>x</script>"
        fig, notes = _figure_notes("saved", tmp_path, [_sc()],
                                   go={"title": '"T", size(%s)' % hostile})
        assert fig.title.text_font_size == "11pt"
        hits = _size_notes(notes, "title(size(")
        assert len(hits) == 1, notes
        assert "medium" in hits[0]
        echo = hits[0].split("title(size(", 1)[1].rsplit(")) is not", 1)[0]
        assert len(echo) <= 80 and echo.isprintable(), echo
        _tag, sp, dp = _inputs(tmp_path, [_sc()], "s2color",
                               {"title": '"T", size(%s)' % hostile}, None)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(sp, dp).render()
        assert "<script>x" not in html
        assert hostile not in html
        for style in re.findall(r"font_size\"?\s*:\s*\"([^\"]*)\"", html):
            assert "script" not in style and "<" not in style, style


# ===========================================================================
# 08-03: the fixture (test/fixtures/size_units_truth.json)
# ===========================================================================

_FIXTURE = Path(__file__).parent / "fixtures" / "size_units_truth.json"


def _load_fixture():
    try:
        with open(_FIXTURE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


_TRUTH = _load_fixture()
_PROBES = (_TRUTH or {}).get("probes", {}) if isinstance(_TRUTH, dict) \
    else {}

_SIZE_SITES = ("marker", "title", "subtitle", "ytitle", "labsize",
               "mlabsize", "legend", "zlabel", "ztitle")
_OFFSET_SITES = ("mlabgap", "mlabgap_msize", "origin")


def _value(rec):
    v = rec.get("value")
    v = "" if v is None else str(v).strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        v = v[1:-1]
    return v


def _probe_ids(sites, with_default=False):
    return sorted(k for k, r in _PROBES.items()
                  if r.get("site") in sites
                  and (with_default or _value(r) != ""
                       or r.get("site") in _OFFSET_SITES))


def _num(v):
    """A number out of a fixture value: a list gives its first number."""
    if isinstance(v, (list, tuple)):
        v = next((x for x in v if x not in (None, "")), None)
    if v in (None, "", "."):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _opts_of(command):
    """{option: argument} of a twoway command's options (the last value of
    each option wins)."""
    tail = command.split(",", 1)[1] if "," in command else ""
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"([a-z]+)\(([^()]*)\)", tail)}


_TEXT_SITES = {
    # site: (graph options with the size, reader)
    "title": (lambda v: {"title": '"TTT", size(%s)' % v if v
                         else '"TTT"'},
              lambda f: f.title.text_font_size),
    "subtitle": (lambda v: {"subtitle": '"SSS", size(%s)' % v if v
                            else '"SSS"'},
                 lambda f: _label_text(f, "SSS").text_font_size),
    "ytitle": (lambda v: {"ytitle": ", size(%s)" % v} if v else {},
               lambda f: _yaxis(f).axis_label_text_font_size),
    "labsize": (lambda v: {"ylabel": ", labsize(%s)" % v} if v else {},
                lambda f: _yaxis(f).major_label_text_font_size),
    "legend": (lambda v: {"legend": "size(%s)" % v} if v else {},
               lambda f: _legends(f)[0].label_text_font_size),
    "zlabel": (lambda v: {"zlabel": ", labsize(%s)" % v} if v else {},
               lambda f: _colorbar(f).major_label_text_font_size),
    "ztitle": (lambda v: {"ztitle": '"ZZ", size(%s)' % v if v
                          else '"ZZ"'},
               lambda f: _colorbar(f).title_text_font_size),
}


def _dash_size(mode, wd, site, scheme, v):
    """(dash's size at *site* for value *v*; in px for a marker, else pt)."""
    if site == "marker":
        o = {"msize": v} if v else {}
        return _marker(_figure(mode, wd, [_sc(**o)], scheme))
    if site == "mlabsize":
        o = {"mlabel": "make"}
        if v:
            o["mlabsize"] = v
        return _pt(_one_labelset(_figure(mode, wd, [_sc(**o)],
                                         scheme)).text_font_size)
    go_of, read = _TEXT_SITES[site]
    if site == "legend":
        plots = [_sc(), _sc2(yaxis="2")]
    elif site in ("zlabel", "ztitle"):
        plots = [_sc(colorvar="price")]
    else:
        plots = [_sc()]
    return _pt(read(_figure(mode, wd, plots, scheme, go=go_of(v))))


def _tw_size(rec):
    """twoway's drawn size of a probe in relative units, or 0 when it drew
    nothing."""
    upr = _num(rec.get("units_per_rs")) or 28.8
    if rec.get("site") == "marker":
        d = _num(rec.get("drawn_rs"))
        setting = _num(rec.get("setting"))
        if setting is not None and setting >= 100:
            # A marker wider than the graph (msize(1d3), 1000 units) is
            # not measurable from the SVG's circles: its class setting is
            # what twoway was asked to draw.
            return setting
        return 0.0 if d is None else d
    f = _num(rec.get("font_pt"))
    if f is None:
        f = _num(rec.get("drawn_pt"))
    return 0.0 if f is None else f * 10.0 / upr


def _default_of(rec):
    for k, r in _PROBES.items():
        if (r.get("site") == rec.get("site")
                and r.get("scheme") == rec.get("scheme")
                and _value(r) == ""):
            return r
    pytest.fail("no default probe for %s/%s" % (rec.get("scheme"),
                                                rec.get("site")))


class TestTheFixture:

    def test_the_fixture_exists(self):
        assert _TRUTH is not None, (
            "the fixture %s is missing or unreadable: run "
            "scripts/extract_size_units_truth.do" % _FIXTURE)
        assert _PROBES, "the fixture holds no probes"

    def test_the_meta_stamp(self):
        """Guard (passes once the fixture exists)."""
        assert _TRUTH is not None, "fixture missing: %s" % _FIXTURE
        m = _TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k) not in (None, ""), k

    def test_the_ladders_are_statas(self):
        assert _TRUTH is not None, "fixture missing: %s" % _FIXTURE
        lad = _TRUTH["ladders"]
        ot = dr.OptionTranslator
        for cls, rel, absolute in (
                ("symbolsize", ot._SYMBOLSIZE_RS, ot._SYMBOLSIZE_ABS_PT),
                ("gsize", ot._GSIZE_RS, ot._GSIZE_ABS_PT)):
            want_rel, want_abs = {}, {}
            for name, (val, sztype) in lad[cls].items():
                tgt = want_abs if "pt" in str(sztype).lower() or \
                    "point" in str(sztype).lower() else want_rel
                tgt[name] = float(val)
            assert set(rel) == set(want_rel), (cls, sorted(
                set(rel) ^ set(want_rel)))
            assert set(absolute) == set(want_abs), (cls, sorted(
                set(absolute) ^ set(want_abs)))
            for name, val in want_rel.items():
                assert float(rel[name]) == pytest.approx(val, abs=1e-9), name
            for name, val in want_abs.items():
                assert float(absolute[name]) == pytest.approx(val), name


_MISSING = "fixture-missing"
# Never an empty parameter set (pytest would skip it): without the fixture
# each parametrised test is one node that fails saying so.
_SIZE_IDS = _probe_ids(_SIZE_SITES) or [_MISSING]
_OFFSET_IDS = _probe_ids(_OFFSET_SITES) or [_MISSING]


def _probe(pid):
    assert pid != _MISSING and pid in _PROBES, (
        "the fixture %s is missing or holds no such probes: run "
        "scripts/extract_size_units_truth.do" % _FIXTURE)
    return _PROBES[pid]


class _Mismatch(Exception):
    """One fixture row that differs; collected, never swallowed: the
    loop that catches it fails naming every such row."""


def _expect(ok, why):
    if not ok:
        raise _Mismatch(why)


def _mismatches(ids, check):
    """``"id: why"`` for each id whose ``check(id)`` raised _Mismatch."""
    bad = []
    for i in ids:
        try:
            check(i)
        except _Mismatch as e:
            bad.append("%s: %s" % (i, str(e).splitlines()[0] if str(e)
                                   else "differs"))
    return bad


_DASH_DEFAULTS = {}       # (mode, site, scheme) -> dash's default size


def _every_probe(pids, one, mode, wd):
    """Run *one* over every probe id, then fail once naming each probe
    whose check failed."""
    bad = _mismatches(pids, lambda pid: one(mode, pid, wd))
    assert not bad, "%d of %d probes differ:\n%s" % (
        len(bad), len(pids), "\n".join(bad))


class TestStataRatios:
    """dash against twoway, probe by probe.  A ``*#`` value is compared as
    a ratio to the site's default (dash's own default is not always
    twoway's yet: the marker-label size and the colour key's chrome are
    later sections'); every other value as twoway's drawn size in relative
    units (one unit = 3.84px = 2.88pt in dash)."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_sizes(self, mode, tmp_path):
        """Every size probe; the failing probe ids are listed together."""
        _every_probe(_SIZE_IDS, self._one_size, mode, tmp_path)

    @pytest.mark.parametrize("mode", _MODES)
    def test_label_offsets(self, mode, tmp_path):
        """Every label-offset probe, listed together on failure."""
        _every_probe(_OFFSET_IDS, self._one_offset, mode, tmp_path)

    @staticmethod
    def _one_size(mode, pid, tmp_path):
        rec = _probe(pid)
        site, scheme, v = rec["site"], rec["scheme"], _value(rec)
        got = _dash_size(mode, tmp_path, site, scheme, v)
        tw = _tw_size(rec)
        unit = _PX_PER_RS if site == "marker" else _PT_PER_RS
        if tw <= 0:
            _expect(got == pytest.approx(0, abs=1e-9), "%s: twoway draws nothing, dash draws %r" % (pid, got))
            return
        if v.startswith("*"):
            tw_def = _tw_size(_default_of(rec))
            key = (mode, site, scheme)
            if key not in _DASH_DEFAULTS:
                _DASH_DEFAULTS[key] = _dash_size(mode, tmp_path, site,
                                                 scheme, "")
            dash_def = _DASH_DEFAULTS[key]
            _expect(got / dash_def == pytest.approx(tw / tw_def, rel=0.01), "%s: dash %r/%r against twoway %r/%r" % (pid, got, dash_def,
                                                         tw, tw_def))
        else:
            _expect(got / unit == pytest.approx(tw, rel=0.01, abs=0.005), "%s: dash %.4f units (%r), twoway %.4f units" % (
                    pid, got / unit, got, tw))

    @staticmethod
    def _one_offset(mode, pid, tmp_path):
        rec = _probe(pid)
        site, scheme = rec["site"], rec["scheme"]
        cmd = str(rec.get("command", ""))
        o = _opts_of(cmd)
        opts = {k: o[k] for k in ("msize", "mlabgap", "mlabposition")
                if k in o}
        words = cmd.split(",", 1)[0].split()
        ptype = next((w for w in words if w in (
            "scatter", "bar", "pcarrow", "pcbarrow", "scatteri")), "scatter")
        if ptype == "scatteri":
            plot = {"type": "scatteri", "values": [[20.0, 3000.0, "lab"]],
                    "options": opts}
        elif ptype in ("pcarrow", "pcbarrow"):
            plot = {"type": ptype, "y1var": "mpg", "x1var": "weight",
                    "y2var": "mpg2", "x2var": "weight2",
                    "options": dict(opts, mlabel="make")}
        else:
            plot = {"type": ptype, "yvar": "mpg", "xvar": "weight",
                    "options": dict(opts, mlabel="make")}
        x, y = _offset(_figure(mode, tmp_path, [plot], scheme))
        dx, dy = _num(rec.get("dx_rs")), _num(rec.get("dy_rs"))
        _expect(dx is not None and dy is not None, (pid, rec))
        if site == "origin":
            # The label's distance from its point.  twoway's anchor sits
            # along one axis: beside the point (scatteri, an arrow's tail;
            # its dy is the text's baseline shift) or, when dx is 0, above
            # a bar's top.
            tw = abs(dx) if abs(dx) > 1e-6 else abs(dy)
            _expect(math.hypot(x, y) / _PX_PER_RS == pytest.approx(
                tw, abs=0.02), "%s: dash offset (%r, %r) px, twoway %.4f "
                                "units" % (pid, x, y, tw))
            return
        p = int(opts.get("mlabposition", "3"))
        if p == 0:
            _expect((x, y) == (0, 0), '(x, y) == (0, 0)')
            return
        ux, uy = _unit(p)
        if abs(ux) > 1e-9:
            tw = dx / ux
        elif p == 12:
            tw = -dy
        else:
            # Clock 6: twoway's y difference adds the text's ascent (0.7 x
            # the font, Evidence E5); Bokeh's "top" baseline supplies it.
            upr = _num(rec.get("units_per_rs")) or 28.8
            font = _num(rec.get("font_pt")) or 8.0
            tw = dy - 0.7 * font * 10.0 / upr
        along = (x * ux + y * uy) / _PX_PER_RS
        _expect(along == pytest.approx(tw, abs=0.02), "%s: dash offset (%r, %r) px = %.4f units along clock %d, "
            "twoway %.4f units" % (pid, x, y, along, p, tw))


def _builtin_names():
    return sorted(dr.SchemeParser._BUILTIN_NAMES)


class TestExplicitKeywordEqualsSchemeDefault:

    @pytest.mark.parametrize("mode", _MODES)
    def test_each_scheme(self, mode, tmp_path):
        bad = _mismatches(_builtin_names(), lambda scheme:
                          self._one_scheme(mode, scheme, tmp_path))
        assert not bad, "\n".join(bad)

    @staticmethod
    def _one_scheme(mode, scheme, tmp_path):
        props = dr.SchemeParser(scheme)._props
        kw = {k: str(props.get(k, "")).strip() for k in (
            "symbolsize p", "gsize heading", "gsize tick_label",
            "gsize key_label")}
        plots = [_sc(), _sc2(yaxis="2")]
        default = _figure(mode, tmp_path, plots, scheme,
                          go={"title": '"T"'})
        go = {"title": '"T"'}
        if kw["gsize heading"]:
            go["title"] = '"T", size(%s)' % kw["gsize heading"]
        if kw["gsize tick_label"]:
            go["ylabel"] = ", labsize(%s)" % kw["gsize tick_label"]
        if kw["gsize key_label"]:
            go["legend"] = "size(%s)" % kw["gsize key_label"]
        first = {"msize": kw["symbolsize p"]} if kw["symbolsize p"] else {}
        fig = _figure(mode, tmp_path, [_sc(**first), _sc2(yaxis="2")],
                      scheme, go=go)
        checks = []
        if first:
            checks.append(("msize", _marker(fig), _marker(default), 1e-6))
        if kw["gsize heading"]:
            checks.append(("title", _pt(fig.title.text_font_size),
                           _pt(default.title.text_font_size), 0.01))
        if kw["gsize tick_label"]:
            checks.append(("labsize",
                           _pt(_yaxis(fig).major_label_text_font_size),
                           _pt(_yaxis(default).major_label_text_font_size),
                           0.01))
        if kw["gsize key_label"]:
            checks.append(("legend",
                           _pt(_legends(fig)[0].label_text_font_size),
                           _pt(_legends(default)[0].label_text_font_size),
                           0.01))
        _expect(checks, 'checks')
        for what, got, want, tol in checks:
            _expect(got == pytest.approx(want, abs=tol), (what, got, want, kw))


class TestTheTablesAgree:

    def test_the_scheme_tables_match_the_ladders(self):
        sp, ot = dr.SchemeParser, dr.OptionTranslator
        for k, pt in sp._SYMBOLSIZE_PT.items():
            assert float(pt) == pytest.approx(
                float(ot._SYMBOLSIZE_RS[k]) * 2.88, abs=0.01), k
        both = (set(sp._GSIZE_PT) & set(ot._GSIZE_RS)) - {"third_tiny"}
        assert both
        for k in both:
            assert _pt(sp._GSIZE_PT[k]) == pytest.approx(
                float(ot._GSIZE_RS[k]) * 2.88, abs=0.01), k


_MARKER_TYPES = {
    "scatter": {"type": "scatter", "yvar": "mpg", "xvar": "weight"},
    "connected": {"type": "connected", "yvar": "mpg", "xvar": "weight"},
    "dot": {"type": "dot", "yvar": "mpg", "xvar": "weight"},
    "dropline": {"type": "dropline", "yvar": "mpg", "xvar": "weight"},
    "rcapsym": {"type": "rcapsym", "yvar1": "mpg", "yvar2": "mpg2",
                "xvar": "weight"},
    "rconnected": {"type": "rconnected", "yvar1": "mpg", "yvar2": "mpg2",
                   "xvar": "weight"},
    "rscatter": {"type": "rscatter", "yvar1": "mpg", "yvar2": "mpg2",
                 "xvar": "weight"},
    "pcscatter": {"type": "pcscatter", "y1var": "mpg", "x1var": "weight",
                  "y2var": "mpg2", "x2var": "weight2"},
    "pccapsym": {"type": "pccapsym", "y1var": "mpg", "x1var": "weight",
                 "y2var": "mpg2", "x2var": "weight2"},
    "scatteri": {"type": "scatteri",
                 "values": [[20.0, 3000.0], [30.0, 4000.0]]},
}


def _glyph_props(fig):
    return [(type(r.glyph).__name__,
             {k: repr(v) for k, v in r.glyph.properties_with_values(
                 include_defaults=True).items()})
            for r in fig.renderers if hasattr(r, "glyph")]


class TestEmptyOptionsChangeNothing:
    """Guard: an applier given no option leaves every glyph as built."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_marker_options(self, mode, tmp_path):
        bad = []
        for ptype in sorted(_MARKER_TYPES):
            plot = dict(_MARKER_TYPES[ptype], options={})
            figs, _, _ = _build(mode, tmp_path, [plot])
            built = [_glyph_props(f) for f in figs]
            with pytest.MonkeyPatch.context() as mp:
                def patch(cls, mp=mp):
                    mp.setattr(cls, "_apply_marker_opts",
                               lambda self, r, o: None)
                figs2, _, _ = _build(mode, tmp_path,
                                     [dict(plot, options={})], patch=patch)
                if [_glyph_props(f) for f in figs2] != built:
                    bad.append(ptype)
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_label_options(self, mode, tmp_path):
        plain = _figure(mode, tmp_path, [_sc()])
        lab = _figure(mode, tmp_path, [_sc(mlabel="make")])
        assert len(_labelsets(lab)) == len(_labelsets(plain)) + 1
        assert _glyph_props(lab) == _glyph_props(plain)
