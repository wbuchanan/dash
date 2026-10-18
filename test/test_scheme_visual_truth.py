"""test_scheme_visual_truth.py -- the scheme parser against what Stata drew.

``test/fixtures/scheme_visual/`` holds Stata's own renders of every one of
the 26 schemes Stata ships and a record of what they show, all written by
``scripts/extract_scheme_visual_truth.do`` (``make truth``; the SVGs are
read by ``scripts/svg_scheme_visual.py``).  For each scheme
``<scheme>.png`` is a three-series scatter, ``<scheme>_line.png`` three
overlaid line plots and ``<scheme>_hist.png`` a histogram, each at the
scheme's graph size and 400 pixels wide; ``truth.json`` is what twoway
drew, measured from its SVG export of the same commands (and of three
overlaid connected plots): per scheme the graph size, the graph and plot
region backgrounds, the plot region's border, the legend box, the text
sizes and colours, the p1-p3 markers (symbol, fill, colour, size), the
p1-p3 lines of ``twoway line`` and ``twoway connected`` (colour, pattern,
width) and the histogram's bars (fill, outline colour and width).

Until 24sep2026 nothing read the record (GAPS.md L8, ROADMAP TR-25.4).  It
covered four schemes measured by hand and no histogram until WP-32
(18oct2026, BUGS.md "The scheme visual truth covers 4 of 26 schemes and
renders no histogram"; GAPS3 K3), when the generator replaced it: on the
four schemes the hand record held, the generator's reading agrees with it
on every compared fact except economist's legend box, which the hand record
called absent and the SVG draws in the graph region's own colour (the same
look, so the comparison below is unchanged).  The record's hand-written
``repo_scheme_disagreements`` list went with it: each entry is a fact the
parametrised comparisons below now hold for all 26 schemes.

WHAT IS COMPARED (each comparison measured 24sep2026 before it was written)
--------------------------------------------------------------------------
* ``default_color(i, "scatter")`` with the marker's fill and outline
  (``map_scatter`` draws both in it), ``default_color(i, "line")`` with
  ``lines_twoway_line`` and ``default_color(i, "connected")`` with
  ``lines_twoway_connected``: 36 comparisons, all equal -- s1mono's line
  colours #606060, #a0a0a0 and #808080 among them, the record's
  high-severity disagreement, fixed since the record was written.
* ``default_symbol(i)`` with the marker's symbol as dash translates it, and
  the declared symbol with the record's ``solid`` flag: ``default_symbol``
  names the shape alone (``circle_hollow`` and ``circle`` both give
  "circle"), so the fill is read from the declaration.  All equal.
* ``default_line_pattern(i)`` and ``default_connect_pattern(i)`` with the
  pattern.  Stata writes a solid line as one path and explodes a dashed one
  into segments (``_how_measured``), so the record keeps the distinction
  only: its "solid" is an empty dash list and its "dashed" any other.  All
  equal: every line plot solid, s1mono's connected p2 and p3 dashed.
* ``background_color`` with the graph region, ``plotregion_color`` with the
  plot region as drawn (``plot_region_background_effective``: economist
  draws none and shows its graph region through), ``legend_bg_color``
  and ``legend_border_color`` with the legend box.  Where Stata draws no
  legend box (economist) the parser's fill must be the graph region it
  would sit on, and where it draws no visible border (economist; stcolor,
  white on white) the parser's border must be the colour of the fill.
* The text colours with the record's: ``title_color`` (title),
  ``subheading_color`` (subtitle), ``axis_title_color`` (axis title),
  ``key_label_color`` (legend label) and ``note_text_color`` (note, drawn
  by ``_dash_text_annotations`` in the scheme's ``textboxstyle note``
  box).  The record gives
  no colour for tick labels, so ``tick_label_color`` is not compared.
* The text sizes on Stata's unit scale: a size is a relative unit, 100 =
  the graph's smaller dimension, 2.88pt per unit at the 4-inch reference the
  parser's pt strings are stated at, and the record's ``pct_of_height`` is
  that unit, the height being the smaller or equal dimension of every
  scheme's graph.  ``note_font_size`` (``gsize note``) is drawn by nothing; the
  note is ``note_text_font_size``, its text box's size, as
  ``_dash_text_annotations`` draws it.
* ``graphsize_x``/``graphsize_y`` with ``graph_size_in``; ``symbolsize``
  with the markers' symbolsize name (or, for a scheme that gives a number,
  as s1manual's 2.2 does, the drawn size); ``default_marker_size`` and
  ``default_line_width`` in proportion to the drawn sizes, one constant
  over all 26 schemes and three series: dash's pixel anchors are its own,
  the ratios are Stata's.
* ``GlyphMapper.map_histogram``'s bars with the histogram's: the fill and
  outline colours, and the outline's width in the same pixels per percent
  of the height as the line plots'.
* ``apply_to_figure`` on a Bokeh figure: the plot and border fills, and the
  figure's outline with ``plot_region_border``.
* Each PNG: a valid PNG (signature, every chunk's CRC, IHDR first, IEND
  last, the image data inflating to exactly its scanlines), its aspect ratio
  the scheme's graph size within a pixel of rounding, and its top-left pixel
  the graph region colour.

WHERE THE PARSER DISAGREED WITH STATA (fixed in the S3 batch)
------------------------------------------------------------
Two cases, measured 24sep2026, were pinned here as strict xfails until
the S3 batch (24sep2026) fixed them; they are plain assertions now:

* economist's note.  Stata draws note() in the reverse_big text box
  (scheme-economist.scheme: ``textboxstyle note reverse_big``): medlarge,
  4.1660% of the graph's height, in #FFFFFF (both in the record), in a box
  filled with ``color reverse_big``, emidblue (read from the scheme file).
  The parser gave note() the small_body box under every scheme: 8pt
  (2.7778%) in #000000.  It now reads ``textboxstyle note`` and that box's
  keys (``note_text_font_size``, ``note_text_color``,
  ``note_box_fill_color``).
* the plot region's border.  ``apply_to_figure`` outlined the plot region
  in ``color axisline`` (#000000) under every scheme; Stata draws no
  visible border under stcolor or s2color (``color plotregion_line white``
  on a white plot region) or economist (``areastyle twoway_plotregion
  none``).  It now draws the scheme's effective border
  (``plotregion_line_color``, None for none).
  s1mono's black border agrees.
"""
import functools
import json
import os
import struct
import sys
import zlib

import pytest
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from dash_render import OptionTranslator, SchemeParser  # noqa: E402

_DIR = os.path.join(_HERE, "fixtures", "scheme_visual")
_TRUTH = os.path.join(_DIR, "truth.json")

#: The 26 schemes Stata ships (test_scheme_fidelity.EXPECTED_SCHEMES).
SCHEMES = (
    "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
    "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
    "economist", "sj", "s2manual", "s1manual", "s2gmanual", "s2color8",
    "sttrans", "stgcolor_alt", "meta", "stcolor_meta", "stcolor_mv",
    "stcoloralias", "stgcolor_meta", "stgcolor_mv",
)
#: Stata's three renders of each, named here so that the fixture guard in
#: test_fixtures_are_committed.py finds every file this test reads.
PNGS = (
    "stcolor.png", "stcolor_line.png", "stcolor_hist.png",
    "stcolor_alt.png", "stcolor_alt_line.png", "stcolor_alt_hist.png",
    "stgcolor.png", "stgcolor_line.png", "stgcolor_hist.png",
    "stmono1.png", "stmono1_line.png", "stmono1_hist.png",
    "stmono2.png", "stmono2_line.png", "stmono2_hist.png",
    "stsj.png", "stsj_line.png", "stsj_hist.png",
    "s2color.png", "s2color_line.png", "s2color_hist.png",
    "s2mono.png", "s2mono_line.png", "s2mono_hist.png",
    "s2gcolor.png", "s2gcolor_line.png", "s2gcolor_hist.png",
    "s1color.png", "s1color_line.png", "s1color_hist.png",
    "s1mono.png", "s1mono_line.png", "s1mono_hist.png",
    "s1rcolor.png", "s1rcolor_line.png", "s1rcolor_hist.png",
    "economist.png", "economist_line.png", "economist_hist.png",
    "sj.png", "sj_line.png", "sj_hist.png",
    "s2manual.png", "s2manual_line.png", "s2manual_hist.png",
    "s1manual.png", "s1manual_line.png", "s1manual_hist.png",
    "s2gmanual.png", "s2gmanual_line.png", "s2gmanual_hist.png",
    "s2color8.png", "s2color8_line.png", "s2color8_hist.png",
    "sttrans.png", "sttrans_line.png", "sttrans_hist.png",
    "stgcolor_alt.png", "stgcolor_alt_line.png", "stgcolor_alt_hist.png",
    "meta.png", "meta_line.png", "meta_hist.png",
    "stcolor_meta.png", "stcolor_meta_line.png", "stcolor_meta_hist.png",
    "stcolor_mv.png", "stcolor_mv_line.png", "stcolor_mv_hist.png",
    "stcoloralias.png", "stcoloralias_line.png", "stcoloralias_hist.png",
    "stgcolor_meta.png", "stgcolor_meta_line.png", "stgcolor_meta_hist.png",
    "stgcolor_mv.png", "stgcolor_mv_line.png", "stgcolor_mv_hist.png",
)
#: The render suffixes.
_SUFFIXES = ("_line", "_hist", "")
#: The five _meta keys every generated fixture carries
#: (test_fixtures_are_committed.META_KEYS).
_META_KEYS = ("stata_version", "born_date", "dash_commit", "extracted",
              "source")
_GENERATOR = "scripts/extract_scheme_visual_truth.do"
#: p1-p3, zero-based as the parser's methods take them.
SERIES = (0, 1, 2)

#: Stata's unit scale: 100 relative units = the graph's smaller dimension,
#: 2.88pt per unit at the 4-inch reference dash states sizes at.
PT_PER_RELATIVE_UNIT = 2.88
#: Percentage points of the graph's height.  The agreeing sizes are within
#: 0.0021 of the record (s2color's and s1mono's 8pt note: 2.7778 against
#: 2.7757); economist's note is 1.39 off.
PCT_TOL = 0.01
#: Relative spread allowed in a size ratio.  Measured: 0.21% for markers
#: (s1mono's diamond is 1.5314% where its circle is 1.5299%), under 0.01%
#: for line widths.
RATIO_TOL = 0.01

@functools.lru_cache(maxsize=None)
def _truth():
    # Committed (test_fixtures_are_committed.py): a missing record is a
    # defect and fails here, it is not a reason to skip.
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


def _scheme(name):
    return _truth()["schemes"][name]


@functools.lru_cache(maxsize=None)
def _parser(name):
    return SchemeParser(name)


def _hex(value):
    return str(value).lower()


def _pt(size):
    """A parser size string ("14pt", "17.28pt") as a float."""
    assert isinstance(size, str) and size.endswith("pt"), size
    return float(size[:-2])


# ---------------------------------------------------------------------------
# The record itself
# ---------------------------------------------------------------------------

def _scheme_of(png):
    stem = png[:-4]
    for suffix in _SUFFIXES:
        if suffix and stem.endswith(suffix):
            return stem[:-len(suffix)]
    return stem


def test_the_record_holds_every_scheme_and_its_renders():
    """Every comparison below is parametrised over SCHEMES and PNGS; the
    record and the directory must hold exactly those, so a scheme or a
    render cannot drop out of the checks without failing here."""
    truth = _truth()
    assert set(truth["schemes"]) == set(SCHEMES)
    assert set(PNGS) == {f"{s}{suffix}.png" for s in SCHEMES
                         for suffix in _SUFFIXES}
    on_disk = sorted(f for f in os.listdir(_DIR) if not f.startswith("."))
    assert on_disk == sorted(PNGS + ("truth.json",)), on_disk
    meta = truth["_meta"]
    assert [k for k in _META_KEYS if not meta.get(k)] == [], meta
    assert meta["source"] == _GENERATOR
    assert os.path.isfile(os.path.join(_HERE, "..", _GENERATOR))
    for name in SCHEMES:
        s = truth["schemes"][name]
        for block in ("markers", "lines_twoway_line",
                      "lines_twoway_connected"):
            assert set(s[block]) == {"p1", "p2", "p3"}, (name, block)
        # Every one of the 20 observations of each series was found.
        assert {m["n_drawn"] for m in s["markers"].values()} == {20}, name
        assert s["histogram"]["n_bars"] > 0, name
        # pct_of_height is the smaller dimension's unit only while the
        # height is not the larger dimension.
        gx, gy = s["graph_size_in"]
        assert gy <= gx, (name, gx, gy)


# ---------------------------------------------------------------------------
# Series: colours, symbols, patterns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_marker_colour_is_what_stata_drew(name, i):
    m = _scheme(name)["markers"][f"p{i + 1}"]
    got = _parser(name).default_color(i, "scatter")
    assert got == _hex(m["color"]), (name, i, got, m["color"])
    # map_scatter draws the marker's outline in the same colour.
    assert got == _hex(m["outline_color"]), (name, i, got,
                                             m["outline_color"])


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_marker_opacity_is_what_stata_drew(name, i):
    """twoway draws these markers opaque under every scheme but sttrans,
    whose markers it draws at fill-opacity 0.20 (GAPS2 D11 plan step 3,
    WP-30 P1.2b: dash once drew each marker at alpha 0.8, the scheme's
    `intensity p' read as an opacity)."""
    m = _scheme(name)["markers"][f"p{i + 1}"]
    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure
    import dash_render as _dr
    src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]})
    r = _dr.GlyphMapper(scheme=_parser(name)).map_scatter(
        figure(), src, "y", "x", {}, color_idx=i)
    r = r[0] if isinstance(r, (list, tuple)) else r
    assert (r.glyph.fill_alpha, r.glyph.line_alpha) == pytest.approx(
        (m["opacity"], m["outline_opacity"])), (
        name, i, r.glyph.fill_alpha, r.glyph.line_alpha, m)


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_line_plot_colour_is_what_stata_drew(name, i):
    want = _scheme(name)["lines_twoway_line"][f"p{i + 1}"]["color"]
    got = _parser(name).default_color(i, "line")
    assert got == _hex(want), (name, i, got, want)


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_connected_line_colour_is_what_stata_drew(name, i):
    want = _scheme(name)["lines_twoway_connected"][f"p{i + 1}"]["color"]
    got = _parser(name).default_color(i, "connected")
    assert got == _hex(want), (name, i, got, want)


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_marker_symbol_is_what_stata_drew(name, i):
    m = _scheme(name)["markers"][f"p{i + 1}"]
    sp = _parser(name)
    assert sp.default_symbol(i) == OptionTranslator.translate_msymbol(
        m["symbol"]), (name, i, sp.default_symbol(i), m["symbol"])
    # The fill: default_symbol gives the same shape for a hollow symbol.
    declared = sp._props.get(f"symbol p{i + 1}", "").strip().lower()
    filled = (declared not in OptionTranslator._HOLLOW_SYMBOLS
              and declared not in OptionTranslator._INVISIBLE_SYMBOLS)
    assert filled == m["solid"], (name, i, declared, m["solid"])


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_line_plot_pattern_is_what_stata_drew(name, i):
    want = _scheme(name)["lines_twoway_line"][f"p{i + 1}"]["pattern"]
    assert want in ("solid", "dashed"), want
    got = _parser(name).default_line_pattern(i)
    assert (got == []) == (want == "solid"), (name, i, got, want)


@pytest.mark.parametrize("name", SCHEMES)
@pytest.mark.parametrize("i", SERIES)
def test_connected_pattern_is_what_stata_drew(name, i):
    want = _scheme(name)["lines_twoway_connected"][f"p{i + 1}"]["pattern"]
    assert want in ("solid", "dashed"), want
    got = _parser(name).default_connect_pattern(i)
    assert (got == []) == (want == "solid"), (name, i, got, want)


# ---------------------------------------------------------------------------
# Regions and the legend box
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", SCHEMES)
def test_graph_region_is_what_stata_drew(name):
    want = _scheme(name)["graph_region_background"]
    assert _parser(name).background_color == _hex(want)


@pytest.mark.parametrize("name", SCHEMES)
def test_plot_region_is_what_stata_drew(name):
    want = _scheme(name)["plot_region_background_effective"]
    assert _parser(name).plotregion_color == _hex(want)


@pytest.mark.parametrize("name", SCHEMES)
def test_legend_fill_is_what_stata_drew(name):
    s = _scheme(name)
    lg = s["legend"]
    # No box drawn: the legend shows the graph region it sits on (every
    # scheme here puts it outside the plot region).
    want = (lg["background"] if lg["has_background"]
            else s["graph_region_background"])
    assert _parser(name).legend_bg_color == _hex(want), (name, lg)


#: Schemes whose legend outline dash draws differently, each with its open
#: BUGS.md entry; test_legend_border_is_what_stata_drew asserts the
#: difference is still there, so a fix is noticed.
_LEGEND_BORDER_DIFFERS = {
    "meta": "meta's legend has no outline in twoway and a black one in dash",
}


@pytest.mark.parametrize("name", SCHEMES)
def test_legend_border_is_what_stata_drew(name):
    lg = _scheme(name)["legend"]
    sp = _parser(name)
    if name in _LEGEND_BORDER_DIFFERS:
        # twoway: `linestyle legend none' (scheme-meta.scheme), drawn as a
        # zero-opacity stroke; dash keeps s2color's black `legend_line'.
        assert not lg["border_visible"], lg
        assert sp.legend_border_color != sp.legend_bg_color, name
        return
    if lg["has_border"] and lg["border_visible"]:
        assert sp.legend_border_color == _hex(lg["border_color"]), (name, lg)
    # A border in the fill's own colour is not seen.
    seen = sp.legend_border_color != sp.legend_bg_color
    assert seen == (lg["has_border"] and lg["border_visible"]), (
        name, sp.legend_border_color, sp.legend_bg_color, lg)


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

#: (record's text element, the parser attribute dash draws it with)
_TEXT_COLOURS = (("title", "title_color"), ("subtitle", "subheading_color"),
                 ("axis_title", "axis_title_color"),
                 ("legend_label", "key_label_color"),
                 ("note", "note_text_color"))
_TEXT_SIZES = (("title", "heading_font_size"),
               ("subtitle", "subheading_font_size"),
               ("axis_title", "axis_title_font_size"),
               ("tick_label", "tick_label_font_size"),
               ("legend_label", "key_label_font_size"),
               ("note", "note_text_font_size"))


def _text_params(pairs):
    return [pytest.param(name, element, attr, id=f"{name}-{element}")
            for name in SCHEMES for element, attr in pairs]


@pytest.mark.parametrize("name,element,attr", _text_params(_TEXT_COLOURS))
def test_text_colour_is_what_stata_drew(name, element, attr):
    want = _scheme(name)["fonts"][element]["color"]
    got = getattr(_parser(name), attr)
    assert got == _hex(want), (name, element, attr, got, want)


@pytest.mark.parametrize("name,element,attr", _text_params(_TEXT_SIZES))
def test_text_size_is_what_stata_drew(name, element, attr):
    want = _scheme(name)["fonts"][element]["pct_of_height"]
    size = getattr(_parser(name), attr)
    got = _pt(size) / PT_PER_RELATIVE_UNIT
    assert abs(got - want) <= PCT_TOL, (
        f"{name} {element}: {attr} is {size}, {got:.4f}% of the graph's "
        f"height; Stata drew {want}%")


# ---------------------------------------------------------------------------
# Sizes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", SCHEMES)
def test_graph_size_is_what_stata_drew(name):
    gx, gy = _scheme(name)["graph_size_in"]
    sp = _parser(name)
    assert (sp.graphsize_x, sp.graphsize_y) == (gx, gy)


@pytest.mark.parametrize("name", SCHEMES)
def test_symbol_size_is_what_stata_drew(name):
    size = _parser(name).symbolsize
    markers = _scheme(name)["markers"].values()
    try:
        # A number is a percentage of the height (s1manual's 2.2).
        pct = float(size)
    except ValueError:
        names = {m["stata_symbolsize_name"] for m in markers}
        assert names == {size}, (name, names)
    else:
        for m in markers:
            assert m["nominal_size_pct_of_height"] == pytest.approx(
                pct, rel=RATIO_TOL), (name, size, m)


def _ratios(value, record_key, block):
    out = {}
    for name in SCHEMES:
        for i in SERIES:
            drawn = _scheme(name)[block][f"p{i + 1}"][record_key]
            out[(name, i)] = value(_parser(name), i) / drawn
    return out


def test_marker_sizes_keep_the_ratios_stata_drew():
    """dash draws medium at its own 8px; every other size keeps Stata's
    ratio to it, so px per percent of the height is one constant."""
    r = _ratios(lambda sp, i: sp.default_marker_size(i),
                "nominal_size_pct_of_height", "markers")
    assert max(r.values()) / min(r.values()) - 1 <= RATIO_TOL, r


def test_line_widths_keep_the_ratios_stata_drew():
    """economist's `linewidth p 1.2' is four of Stata's mediums, and dash
    draws it four times s2color's 1.5px."""
    r = _ratios(lambda sp, i: sp.default_line_width,
                "width_pct_of_height", "lines_twoway_line")
    assert max(r.values()) / min(r.values()) - 1 <= RATIO_TOL, r


def test_marker_outlines_are_as_wide_as_stata_drew_them():
    """Stata draws every marker's outline at the scheme's `linewidth
    p#mark' chain, which under all four schemes is the width of its lines
    (outline_width_units == the line's width_units: s2color 8.64,
    economist 19.01).  dash drew Bokeh's 1px outline under every scheme
    (BUGS.md, S3); it now draws plot_line_width(i, "mark"), at the
    line's pixel width, so the outline keeps Stata's ratio to the line."""
    for name in SCHEMES:
        sp = _parser(name)
        for i in SERIES:
            mk = _scheme(name)["markers"][f"p{i + 1}"]["outline_width_units"]
            ln = _scheme(name)["lines_twoway_line"][f"p{i + 1}"]["width_units"]
            assert sp.plot_line_width(i, "mark") / sp.plot_line_width(
                i, "lineplot") == pytest.approx(mk / ln), (name, i)


# ---------------------------------------------------------------------------
# apply_to_figure
# ---------------------------------------------------------------------------

def _figure(name):
    fig = figure()
    _parser(name).apply_to_figure(fig)
    return fig


@pytest.mark.parametrize("name", SCHEMES)
def test_apply_to_figure_fills_what_stata_drew(name):
    s = _scheme(name)
    fig = _figure(name)
    assert _hex(fig.background_fill_color) == _hex(
        s["plot_region_background_effective"])
    assert _hex(fig.border_fill_color) == _hex(s["graph_region_background"])


@pytest.mark.parametrize("name", SCHEMES)
def test_apply_to_figure_borders_the_plot_region_as_stata_does(name):
    border = _scheme(name)["plot_region_border"]
    fig = _figure(name)
    outline = fig.outline_line_color
    drawn = (outline is not None and fig.outline_line_alpha > 0
             and fig.outline_line_width > 0
             and _hex(outline) != _hex(fig.background_fill_color))
    assert drawn == border["visible"], (
        f"{name}: dash outlines the plot region in {outline}; Stata's "
        f"border is {border}")
    if border["visible"]:
        assert _hex(outline) == _hex(border["color"]), (outline, border)


# ---------------------------------------------------------------------------
# The histogram
# ---------------------------------------------------------------------------

def _histogram_glyph(name):
    from bokeh.models import ColumnDataSource
    import dash_render as _dr
    src = ColumnDataSource({"v": [1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0, 5.0]})
    r = _dr.GlyphMapper(scheme=_parser(name)).map_histogram(
        figure(), src, "v", {}, color_idx=0)
    r = r[0] if isinstance(r, (list, tuple)) else r
    return r.glyph


@pytest.mark.parametrize("name", SCHEMES)
def test_histogram_bars_are_the_colours_stata_drew(name):
    h = _scheme(name)["histogram"]
    g = _histogram_glyph(name)
    assert _hex(g.fill_color) == _hex(h["fill"]), (name, g.fill_color, h)
    assert g.fill_alpha == pytest.approx(h["fill_opacity"]), (
        name, g.fill_alpha, h)
    assert _hex(g.line_color) == _hex(h["outline_color"]), (
        name, g.line_color, h)


#: Stata's SVG writer draws no stroke narrower than 3 units (1/240 inch):
#: measured 18oct2026, lwidth(vvvthin) and lwidth(vvthin) are 3.00 units
#: on square graphs of 1 to 16 inches, vthin 3.00 up to 2.392 inches and
#: 0.15% of the side above it.  A drawn width at the floor says nothing of
#: the scheme's own width (stcolor's `linewidth histogram vthin' on
#: stgcolor's 2.392-inch height), so it is not compared.
_SVG_MIN_STROKE = 3.0


def test_histogram_outlines_keep_the_ratio_stata_drew():
    """The bars' outline is drawn in the pixels per percent of the height
    that the line plots are (test_line_widths_keep_the_ratios_stata_drew),
    under every scheme whose drawn width is above the SVG writer's floor."""
    floored = {name for name in SCHEMES
               if _scheme(name)["histogram"]["outline_width_units"]
               <= _SVG_MIN_STROKE}
    assert floored == {"stgcolor", "stgcolor_alt", "stgcolor_meta",
                       "stgcolor_mv"}, floored
    r = {name: _histogram_glyph(name).line_width
         / _scheme(name)["histogram"]["outline_width_pct_of_height"]
         for name in SCHEMES if name not in floored}
    lines = _ratios(lambda sp, i: sp.default_line_width,
                    "width_pct_of_height", "lines_twoway_line")
    ref = min(lines.values())
    off = {k: round(v / ref, 3) for k, v in r.items()
           if abs(v / ref - 1) > RATIO_TOL}
    assert not off, off


# ---------------------------------------------------------------------------
# The PNGs
# ---------------------------------------------------------------------------

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
#: Bytes per pixel at bit depth 8, by PNG colour type.
_BPP = {0: 1, 2: 3, 4: 2, 6: 4}


@functools.lru_cache(maxsize=None)
def _png(name):
    """(width, height, colour type, the inflated image data, chunk names)
    of one render, every chunk's CRC checked on the way."""
    with open(os.path.join(_DIR, name), "rb") as fh:
        data = fh.read()
    assert data[:8] == _PNG_SIGNATURE, name
    pos, chunks, idat, ihdr = 8, [], [], None
    while pos < len(data):
        assert pos + 12 <= len(data), f"{name}: truncated chunk at {pos}"
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        crc, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert zlib.crc32(kind + body) & 0xFFFFFFFF == crc, (name, kind)
        chunks.append(kind.decode("ascii"))
        if kind == b"IHDR":
            ihdr = body
        elif kind == b"IDAT":
            idat.append(body)
        pos += 12 + length
    assert ihdr is not None and len(ihdr) == 13, name
    width, height, depth, ctype = struct.unpack(">IIBB", ihdr[:10])
    assert depth == 8 and ctype in _BPP, (name, depth, ctype)
    return width, height, ctype, zlib.decompress(b"".join(idat)), chunks


@pytest.mark.parametrize("name", PNGS)
def test_each_render_is_a_valid_png(name):
    width, height, ctype, raw, chunks = _png(name)
    assert chunks[0] == "IHDR" and chunks[-1] == "IEND", chunks
    assert chunks.count("IEND") == 1 and "IDAT" in chunks, chunks
    # Each scanline is a filter byte and its pixels, no more and no less.
    assert len(raw) == height * (1 + width * _BPP[ctype]), (name, len(raw))
    assert width > 0 and height > 0


@pytest.mark.parametrize("name", PNGS)
def test_each_render_has_its_scheme_s_aspect_ratio(name):
    width, height, _ctype, _raw, _chunks = _png(name)
    gx, gy = _scheme(_scheme_of(name))["graph_size_in"]
    # Stata rounds the height to a whole pixel: 400 wide at 5.5 x 4 in
    # is 290.9 pixels high.
    assert abs(height - width * gy / gx) < 1, (name, width, height, gx, gy)


@pytest.mark.parametrize("name", PNGS)
def test_each_render_s_corner_is_its_scheme_s_graph_region(name):
    width, _height, ctype, raw, _chunks = _png(name)
    want = _scheme(_scheme_of(name))["graph_region_background"]
    # The first pixel of the first scanline is its bytes as stored, under
    # every filter type: its left, upper and upper-left neighbours are 0.
    bpp = _BPP[ctype]
    assert ctype in (2, 6), (name, ctype)
    pixel = raw[1:1 + bpp]
    got = "#%02x%02x%02x" % tuple(pixel[:3])
    assert got == _hex(want), (name, got, want)
    if ctype == 6:
        assert pixel[3] == 255, (name, pixel)
