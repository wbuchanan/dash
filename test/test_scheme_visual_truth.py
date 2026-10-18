"""test_scheme_visual_truth.py -- the scheme parser against what Stata drew.

``test/fixtures/scheme_visual/`` holds Stata's own renders of four schemes
and a record of what they show.  For stcolor, s2color, economist and s1mono,
``<scheme>.png`` is a three-series scatter and ``<scheme>_line.png`` three
overlaid line plots, each at the scheme's graph size; ``truth.json`` is what
StataNow 19.5 drew, measured from its SVG export of the same twoway
commands: per scheme the graph size, the graph and plot region backgrounds,
the plot region's border, the legend box, the text sizes and colours, the
p1-p3 markers (symbol, fill, colour, size) and the p1-p3 lines of
``twoway line`` and ``twoway connected`` (colour, pattern, width).

Until 24sep2026 nothing read any of the nine files (GAPS.md L8, ROADMAP
TR-25.4): ``test_fixtures_are_committed.py`` asked git to track them and
said each "is read by the test suite", which was false for these.  This file
holds ``dash_render.SchemeParser`` to the record and ties each PNG to it.

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
  declares none and shows its graph region through), ``legend_bg_color``
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
  that unit, the height being the smaller or equal dimension of all four
  graphs.  ``note_font_size`` (``gsize note``) is drawn by nothing; the
  note is ``note_text_font_size``, its text box's size, as
  ``_dash_text_annotations`` draws it.
* ``graphsize_x``/``graphsize_y`` with ``graph_size_in``; ``symbolsize``
  with the markers' symbolsize name; ``default_marker_size`` and
  ``default_line_width`` in proportion to the drawn sizes, one constant
  over all four schemes and three series: dash's pixel anchors are its own,
  the ratios are Stata's.
* ``apply_to_figure`` on a Bokeh figure: the plot and border fills, and the
  figure's outline with ``plot_region_border``.
* Each PNG: a valid PNG (signature, every chunk's CRC, IHDR first, IEND
  last, the image data inflating to exactly its scanlines), its aspect ratio
  the scheme's graph size within a pixel of rounding (s2color and s1mono are
  1200 x 872 for 872.7), and its top-left pixel the graph region colour.

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
import re
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

#: The four schemes the record measured.
SCHEMES = ("stcolor", "s2color", "economist", "s1mono")
#: Stata's two renders of each, named here so that the fixture guard in
#: test_fixtures_are_committed.py finds every file this test reads.
PNGS = ("stcolor.png", "stcolor_line.png", "s2color.png", "s2color_line.png",
        "economist.png", "economist_line.png", "s1mono.png",
        "s1mono_line.png")
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

def test_the_record_holds_the_four_schemes_and_their_renders():
    """Every comparison below is parametrised over SCHEMES and PNGS; the
    record and the directory must hold exactly those, so a scheme or a
    render cannot drop out of the checks without failing here."""
    truth = _truth()
    assert set(truth["schemes"]) == set(SCHEMES)
    assert set(PNGS) == {f"{s}{suffix}.png" for s in SCHEMES
                         for suffix in ("", "_line")}
    on_disk = sorted(f for f in os.listdir(_DIR) if not f.startswith("."))
    assert on_disk == sorted(PNGS + ("truth.json",)), on_disk
    assert truth["_stata"] == "StataNow 19.5 MP"
    for name in SCHEMES:
        s = truth["schemes"][name]
        for block in ("markers", "lines_twoway_line",
                      "lines_twoway_connected"):
            assert set(s[block]) == {"p1", "p2", "p3"}, (name, block)
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
    """twoway draws these markers opaque (GAPS2 D11 plan step 3, WP-30
    P1.2b): the PNG record holds the unblended hexes, and dash drew each
    marker at alpha 0.8, the scheme's `intensity p' read as an opacity."""
    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure
    import dash_render as _dr
    src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]})
    r = _dr.GlyphMapper(scheme=_parser(name)).map_scatter(
        figure(), src, "y", "x", {}, color_idx=i)
    r = r[0] if isinstance(r, (list, tuple)) else r
    assert (r.glyph.fill_alpha, r.glyph.line_alpha) == (1.0, 1.0), (
        name, i, r.glyph.fill_alpha, r.glyph.line_alpha)


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


@pytest.mark.parametrize("name", SCHEMES)
def test_legend_border_is_what_stata_drew(name):
    lg = _scheme(name)["legend"]
    sp = _parser(name)
    if lg["has_border"]:
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
    names = {m["stata_symbolsize_name"]
             for m in _scheme(name)["markers"].values()}
    assert names == {_parser(name).symbolsize}, (name, names)


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
# The record's own list of disagreements
# ---------------------------------------------------------------------------

#: Every entry of ``repo_scheme_disagreements``, and the test here that
#: holds it.  A new entry fails test_every_recorded_disagreement_is_held
#: until it is given one.
_HELD = {
    ("s1mono", ("color p1line", "color p2line", "color p3line")):
        "test_the_high_severity_disagreements_are_fixed",
    ("s1mono", ("linepattern p2line", "linepattern p3line")):
        "test_the_high_severity_disagreements_are_fixed",
    ("economist", ("gsize note",)):
        "test_text_size_is_what_stata_drew[economist-note]",
    ("economist", ("gsize heading",)):
        "test_text_size_is_what_stata_drew[economist-title]",
}


def test_every_recorded_disagreement_is_held():
    got = {(e["scheme"], tuple(e["keys"]))
           for e in _truth()["repo_scheme_disagreements"]}
    assert got == set(_HELD), sorted(got ^ set(_HELD))


def test_the_high_severity_disagreements_are_fixed():
    """The record's two high-severity entries: s1mono's `color p#line' and
    `linepattern p#line' belong to the connecting line of twoway connected,
    and a plain twoway line reads `color p#' and `linepattern p#lineplot'.
    Checked against the values the entries themselves record."""
    high = [e for e in _truth()["repo_scheme_disagreements"]
            if e["severity"] == "high"]
    assert len(high) == 2, high
    checked = 0
    for e in high:
        sp = _parser(e["scheme"])
        for key, line, conn in zip(e["keys"], e["stata_drew_twoway_line"],
                                   e["stata_drew_twoway_connected"]):
            m = re.fullmatch(r"(color|linepattern) p(\d+)line", key)
            assert m, key
            i = int(m.group(2)) - 1
            if m.group(1) == "color":
                assert sp.default_color(i, "line") == _hex(line), (key, line)
                assert sp.default_color(i, "connected") == _hex(conn), (
                    key, conn)
            else:
                assert (sp.default_line_pattern(i) == []) == (
                    line == "solid"), (key, line)
                assert (sp.default_connect_pattern(i) == []) == (
                    conn == "solid"), (key, conn)
            checked += 1
    assert checked == 5


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
    gx, gy = _scheme(name[:-4].replace("_line", ""))["graph_size_in"]
    # Stata rounds the height to a whole pixel: 1200 wide at 5.5 x 4 in
    # is 872.7 pixels high, and the file is 872.
    assert abs(height - width * gy / gx) < 1, (name, width, height, gx, gy)


@pytest.mark.parametrize("name", PNGS)
def test_each_render_s_corner_is_its_scheme_s_graph_region(name):
    width, _height, ctype, raw, _chunks = _png(name)
    want = _scheme(name[:-4].replace("_line", ""))["graph_region_background"]
    # The first pixel of the first scanline is its bytes as stored, under
    # every filter type: its left, upper and upper-left neighbours are 0.
    bpp = _BPP[ctype]
    assert ctype in (2, 6), (name, ctype)
    pixel = raw[1:1 + bpp]
    got = "#%02x%02x%02x" % tuple(pixel[:3])
    assert got == _hex(want), (name, got, want)
    if ctype == 6:
        assert pixel[3] == 255, (name, pixel)
