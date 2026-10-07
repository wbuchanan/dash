"""What a scheme says reaches the page -- measured on the Bokeh models.

WP-16.  The principle (DESIGN.md section 1): a scheme directive that Stata
consumes is consumed by dash, in the place Stata consumes it, on Stata's
unit scale, in both render modes through one implementation.  Where Stata
draws nothing, dash draws nothing.  An explicit option still beats the
scheme.

Every scheme test before this one asserted a PARSED value -- that
``SchemeParser("economist").heading_font_size`` is a "pt" string, that
``minor_grid_color`` equals the fixture -- and nothing looked at a figure.
That is how the four gaps this file closes stayed green for a year.
Measured on 22sep2026 (scratchpad/wp16/probe/baseline.json), for all
fourteen shipped schemes in both modes:

* a MINOR grid was drawn on both axes under every scheme, though no shipped
  scheme asks for one (``yesno draw_minor_hgrid``/``draw_minor_vgrid`` are
  ``no`` in all fourteen) -- so s1color, whose whole point is "no grid",
  drew a dark #505050 minor grid on a white plot;
* ``fig.title`` was Bokeh's #444444 / 13px under every scheme; economist's
  ``gsize heading 6.0`` came out as 7pt (``int(6.0 * 1.2)``), smaller than
  its 11pt subtitle;
* economist's ``linewidth p 1.2`` was drawn as 1.2 px, thinner than
  s2color's medium 1.5 px, where Stata draws it four times thicker;
* the subtitle, note and caption were dash's own 13/11/12 px literals in
  #444444/#555555 under every scheme, white-on-black s1rcolor included;
* axis titles and tick labels were #444444 under every scheme;
* the legend sat top-right, vertical, under every scheme, while s2color
  says clock 6 (below) in two columns, economist clock 12 (above) in three,
  and stcolor clock 3 (right); and once placed there (the adversarial
  review of 22sep2026, findings R2/R3) it was appended OUTERMOST in its
  panel -- under s2color the note and caption sat between the plot and the
  legend, under economist the legend sat between the title and the
  subtitle -- and kept Bokeh's ``top_right`` location, so a below-legend
  hugged the right edge where Stata centres it;
* the KPI card was an inline ``background:#f8f9fa; border:1px solid
  #dee2e6`` under every scheme -- a light card on s1rcolor's black page --
  and the ``.db-kpi-card`` rule ``css_block()`` emits never reached the Div,
  which renders in a shadow root;
* ``xlabel(, grid)`` under a gridless scheme coloured the grid a literal
  #e5e5e5, not the scheme's grid colour;
* every marker was 8 px: stcolor's ``symbolsize small`` and economist's
  ``large`` were indistinguishable.

The expected values come from ``test/fixtures/scheme_truth.json``, the
ground truth extracted from Stata's own scheme and style files, read at
test time.  Sizes are checked on Stata's unit scale (DESIGN.md section 3):
a gsize or symbolsize value is a relative unit, 100 = the graph's smaller
dimension, which at Stata's 4-inch reference is 2.88 pt per unit; a
linewidth unit is anchored at dash's 1.5 px for medium (.30), i.e. 5 px per
unit.  A keyword's expected size is therefore the fixture's relative value
times 2.88, compared to the rendered "pt" string within 0.01 pt -- so the
test does not carry a keyword table of its own.

Rendering goes through the parity file's own helpers so the two modes are
built exactly as ``test_mode_parity.py`` builds them; the served module is
kept so its ``_DASH_SCHEME`` can be read back.  One render per (scheme,
case), cached, whichever assertion asks first.
"""
import os
import re
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.models import Axis, Div, GlyphRenderer, Label, Legend, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

SCHEMES = sorted(dr.SchemeParser._BUILTIN_NAMES)
MODES = ("standalone", "served")
FIXTURE = os.path.join(_HERE, "fixtures", "scheme_truth.json")

#: Stata's unit scale (DESIGN.md section 3).
PT_PER_RELATIVE_UNIT = 2.88      # at the 4-inch reference dimension
PX_PER_LINEWIDTH_UNIT = 5.0      # medium (.30) = 1.5 px
MARKER_PX_ANCHOR = 8.0           # dash draws Stata's medium marker at 8 px
MARKER_PX_ANCHOR_PT = 4.4        # symbolsize medium is 4.4 pt at 4 inches
SIZE_TOL_PT = 0.01
SIZE_TOL_PX = 0.02

#: The schemes Stata draws with no grid at all (AC-16.1).
GRIDLESS = ("s1color", "s1mono", "s1rcolor", "stmono1")

#: The four dashboards each scheme is rendered as, in both modes.
CASES = ("titles", "legend_pos9", "kpi", "kpi_bg", "xgrid")


def _grouped(names, prefix):
    """Parametrise with an xdist group per scheme, so a scheme's renders
    stay on one worker and are made once (pyproject: --dist loadgroup)."""
    return [pytest.param(n, id=n, marks=pytest.mark.xdist_group(
        name=f"{prefix}:{n}")) for n in names]


# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------

_TRUTH = {}


def _fixture():
    """The fixture, read once per process, at test time rather than at
    import: Owner A regenerates it in the same tree."""
    if not _TRUTH:
        import json
        with open(FIXTURE, encoding="utf-8") as fh:
            _TRUTH.update(json.load(fh))
    return _TRUTH


def _truth(scheme, key, *aliases):
    """The fixture's value of *key* for *scheme*.

    A key the fixture lacks fails the case, naming the key.  While WP-16's
    additions to the extractor were landing it skipped instead; WP-16 is
    done and the fixture carries every key these cases read (24sep2026), so
    a missing one is a fixture that lost it, and a skip would pass the case
    unjudged.
    """
    entry = _fixture()[scheme]
    for k in (key,) + aliases:
        if k in entry and entry[k] is not None:
            return entry[k]
    pytest.fail(f"test/fixtures/scheme_truth.json[{scheme!r}] has no "
                f"{key!r}; regenerate the fixture")


def _size_pt(entry):
    """Expected points for a fixture size entry ``{name, value, sztype}``:
    the relative value on Stata's scale at the 4-inch reference."""
    return float(entry["value"]) * PT_PER_RELATIVE_UNIT


def _pt_of(css):
    """The number in a rendered "Npt" string; anything else is a failure
    in its own right, because the contract says the scheme's sizes reach
    Bokeh as pt strings."""
    assert isinstance(css, str) and css.endswith("pt"), (
        f"expected a 'pt' size string from the scheme, got {css!r}")
    return float(css[:-2])


def _line_width_px(entry):
    """Expected pixels for a fixture linewidth entry ``{name, value}``: a
    number is a Stata linewidth unit (x5); a keyword keeps dash's keyword
    ladder, which DESIGN.md section 3 leaves out of scope."""
    name = str(entry["name"]).strip().lower()
    try:
        return float(name) * PX_PER_LINEWIDTH_UNIT
    except ValueError:
        return dr.OptionTranslator.translate_lwidth(name)


def _marker_px(entry):
    """Expected marker diameter for a fixture symbolsize entry."""
    return MARKER_PX_ANCHOR * _size_pt(entry) / MARKER_PX_ANCHOR_PT


def _hex(c):
    return str(c).strip().lower() if c is not None else None


# ---------------------------------------------------------------------------
# Rendering, both modes, through the parity file's helpers
# ---------------------------------------------------------------------------

def _spec_for(scheme, case):
    bo = {"scheme": scheme}
    two = [plot_for("scatter"), plot_for("line")]
    if case == "titles":
        return tp._spec(two, bo, {"title": "T", "subtitle": "S",
                                  "note": "N", "caption": "C"})
    if case == "legend_pos9":
        # No shipped scheme puts its legend at 9 o'clock, so an explicit
        # position(9) differs from every scheme's default; cols(1) too.
        return tp._spec(two, bo, {"legend": "position(9) cols(1)"})
    if case == "kpi":
        return tp._spec([plot_for("scatter")], bo, kpis=[tp._kpi()])
    if case == "kpi_bg":
        return tp._spec([plot_for("scatter")], bo,
                        kpis=[tp._kpi(bgcolor="#ecf0f1")])
    if case == "xgrid":
        return tp._spec([plot_for("scatter")], bo, {"xlabel": ", grid"})
    raise KeyError(case)


def _served_with_module(spec):
    """(document, module): the parity file's ``_served`` keeps only the
    document, and the served scheme lives on the module."""
    tag, sp, dp = tp._write(spec)
    ap = os.path.join(tp._TMP, f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_rendered_{tag}")
        doc = Document()
        mod.make_document(doc)
    curdoc().clear()
    return doc, mod


class _Page:
    """What one mode drew: its figures, its KPI Divs and its scheme."""

    def __init__(self, figures, kpis, scheme):
        self.figures = figures
        self.kpis = kpis
        self.scheme = scheme

    @property
    def fig(self):
        assert len(self.figures) == 1, f"{len(self.figures)} figures"
        return self.figures[0]

    @property
    def css(self):
        return self.scheme.css_block()


_KPI_NAME = re.compile(r'id="kpi_val_([^"]*)"')


def _render(scheme, case, mode):
    spec = _spec_for(scheme, case)
    if mode == "standalone":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r, _ = tp._standalone(spec)
        curdoc().clear()
        return _Page(list(r.figures.values()), dict(r.kpi_divs), r.scheme)
    doc, mod = _served_with_module(spec)
    figs = list(doc.select(dict(type=Plot)))
    kpis = {}
    for d in doc.select(dict(type=Div)):
        m = _KPI_NAME.search(d.text or "")
        if m and "db-kpi-card" in d.text:
            kpis[m.group(1)] = d
    return _Page(figs, kpis, mod._DASH_SCHEME)


_CACHE = {}


def _page(scheme, case, mode):
    key = (scheme, case, mode)
    if key not in _CACHE:
        _CACHE[key] = _render(scheme, case, mode)
    return _CACHE[key]


# ---------------------------------------------------------------------------
# Reading the models
# ---------------------------------------------------------------------------

def _v(x):
    """A Bokeh property value as plain data (a dataspec's value)."""
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, dict):
        if "value" in x:
            return _v(x["value"])
        if "field" in x:
            return ("field", x["field"])
        return {k: _v(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_v(i) for i in x]
    f = getattr(x, "field", None)
    if isinstance(f, str):
        return ("field", f)
    if hasattr(x, "value"):
        return _v(x.value)
    return repr(x)


def _labels(fig, side):
    return [l for l in getattr(fig, side) if isinstance(l, Label)]


def _label(fig, text):
    """The one Label carrying *text* (the subtitle sits above, the note and
    the caption below)."""
    hits = [l for side in ("above", "below") for l in _labels(fig, side)
            if l.text == text]
    assert len(hits) == 1, f"{len(hits)} Labels read {text!r}"
    return hits[0]


def _legend(fig):
    lgs = list(fig.legend)
    assert len(lgs) == 1, f"{len(lgs)} legends"
    return lgs[0]


def _legend_side(fig, lg):
    for side in ("above", "below", "left", "right", "center"):
        if lg in list(getattr(fig, side)):
            return side
    return None


def _glyph(fig, kind):
    hits = [r.glyph for r in fig.renderers
            if isinstance(r, GlyphRenderer) and type(r.glyph).__name__ == kind]
    assert hits, f"no {kind} glyph on the figure"
    return hits[0]


_OUTER_DIV = re.compile(r"<div\b([^>]*)>", re.S)


def _card(div):
    """The KPI card's outer div as plain data: class, style, whether the
    style declares a background, the value div's colour, the stylesheet
    text attached to the Div."""
    text = div.text or ""
    m = _OUTER_DIV.search(text)
    attrs = m.group(1) if m else ""
    cls = re.search(r'class="([^"]*)"', attrs)
    style = re.search(r'style="([^"]*)"', attrs)
    style_s = re.sub(r"\s+", " ", style.group(1)).strip() if style else ""
    mv = re.search(r'id="kpi_val_[^"]*"\s+style="([^"]*)"', text, re.S)
    vcol = None
    if mv:
        mc = re.search(r"(?:^|[;\s])color\s*:\s*([^;\"]+)", mv.group(1))
        vcol = mc.group(1).strip() if mc else None
    return {
        "class": cls.group(1) if cls else None,
        "style": style_s,
        "inline_background": bool(
            re.search(r"(?:^|[;\s])background(?:-color)?\s*:", style_s)),
        "value_color": vcol,
        "css": "".join(getattr(s, "css", "") or "" for s in div.stylesheets),
    }


def _rule(css, selector):
    """The declarations of *selector*'s rule in a CSS block, whitespace
    collapsed, lower-cased; '' when the rule is absent."""
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return re.sub(r"\s+", " ", m.group(1)).strip().lower() if m else ""


def _rule_value(css, selector, prop):
    """One declaration's value, anchored at a declaration boundary so that
    ``color`` never matches inside ``background-color``."""
    m = re.search(r"(?:^|;)\s*" + re.escape(prop) + r"\s*:\s*([^;]+)",
                  _rule(css, selector))
    return m.group(1).strip() if m else None


def _profile(page):
    """Everything this file asserts on, as plain comparable data, so the
    two modes can be compared whole (AC (xii))."""
    figs = []
    for fig in page.figures:
        t = fig.title
        lgs = []
        for lg in fig.legend:
            lgs.append({
                "side": _legend_side(fig, lg),
                "location": str(lg.location),
                "orientation": lg.orientation,
                "ncols": lg.ncols, "nrows": lg.nrows,
                "label_size": lg.label_text_font_size,
                "label_color": _hex(lg.label_text_color),
                "background": _hex(lg.background_fill_color),
                "border": _hex(lg.border_line_color),
                "n_items": len(lg.items),
            })
        figs.append({
            "title": {"text": t.text if t else None,
                      "color": _hex(t.text_color) if t else None,
                      "size": t.text_font_size if t else None},
            "xgrid": [(g.grid_line_color, g.grid_line_width,
                       g.minor_grid_line_color) for g in fig.xgrid],
            "ygrid": [(g.grid_line_color, g.grid_line_width,
                       g.minor_grid_line_color) for g in fig.ygrid],
            "axes": [(a.axis_line_color, a.axis_label_text_color,
                      a.axis_label_text_font_size, a.major_label_text_color,
                      a.major_label_text_font_size)
                     for a in list(fig.xaxis) + list(fig.yaxis)],
            "labels": sorted(
                (side, l.text, l.text_font_size, _hex(l.text_color))
                for side in ("above", "below") for l in _labels(fig, side)),
            "legends": lgs,
            "glyphs": sorted(
                (type(r.glyph).__name__,
                 _v(getattr(r.glyph, "line_width", None)),
                 _v(getattr(r.glyph, "size", None)))
                for r in fig.renderers if isinstance(r, GlyphRenderer)),
        })
    return {"figures": figs,
            "kpis": {k: _card(d) for k, d in page.kpis.items()},
            "css": page.css}


# ---------------------------------------------------------------------------
# (i) the minor grid, (ii) the major grid
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestTheGrids:
    """Stata draws each grid only where the scheme's yesno flag says.

    The x axis is Stata's horizontal axis, whose grid lines are vertical;
    its flags are ``draw_major_hgrid``/``draw_minor_hgrid``.  The y axis
    reads the ``vgrid`` pair.  The fixture records the EFFECTIVE flags after
    the axisstyle indirection (economist's y axis is ``vertical_nolinetick``
    and reads ``draw_major_nlt_vgrid``).
    """

    def test_the_minor_grid_is_drawn_only_where_the_scheme_says(
            self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        minor = _hex(_truth(scheme, "minor_grid_color"))
        for grids, key in ((fig.xgrid, "draw_minor_hgrid"),
                           (fig.ygrid, "draw_minor_vgrid")):
            want = minor if _truth(scheme, key) == "yes" else None
            for g in grids:
                assert _hex(g.minor_grid_line_color) == want, (
                    f"{scheme}/{mode}: {key} is {_truth(scheme, key)!r} but "
                    f"the minor grid is {g.minor_grid_line_color!r}")

    def test_the_major_grid_is_the_schemes_per_axis(self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        colour = _hex(_truth(scheme, "grid_color"))
        for grids, key in ((fig.xgrid, "draw_major_hgrid"),
                           (fig.ygrid, "draw_major_vgrid")):
            want = colour if _truth(scheme, key) == "yes" else None
            for g in grids:
                assert _hex(g.grid_line_color) == want, (
                    f"{scheme}/{mode}: {key} is {_truth(scheme, key)!r} but "
                    f"the major grid is {g.grid_line_color!r}")

    def test_the_major_grid_width_is_the_schemes(self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        want = _line_width_px(_truth(scheme, "grid_line_width"))
        for g in list(fig.xgrid) + list(fig.ygrid):
            assert g.grid_line_width == pytest.approx(want, abs=SIZE_TOL_PX)


@pytest.mark.parametrize("scheme", _grouped(GRIDLESS, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestAC161NoGridWhereStataDrawsNone:
    """AC-16.1: s1color, s1mono, s1rcolor and stmono1 draw no grid at all
    -- no major grid and no minor grid, on either axis, in either mode."""

    def test_no_grid_at_all(self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        for g in list(fig.xgrid) + list(fig.ygrid):
            assert g.grid_line_color is None, (
                f"{scheme}/{mode} draws a major grid {g.grid_line_color!r}")
            assert g.minor_grid_line_color is None, (
                f"{scheme}/{mode} draws a minor grid "
                f"{g.minor_grid_line_color!r}")


# ---------------------------------------------------------------------------
# (iii) the figure title, (v) subtitle / note / caption, (vi) axis text
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestTheText:
    """Stata's textbox styles (DESIGN.md section 2): title() is the heading
    box, subtitle() the subheading box, caption() the body box, note() the
    small_body box -- its own size AND its own colour, ``color small_body``
    (textboxstyle-small_body.style: ``set color scheme small_body``); axis
    titles and tick labels have their own colour keys."""

    def test_the_title_has_the_heading_colour_and_size(self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        assert fig.title.text == "T"
        assert _hex(fig.title.text_color) == _hex(_truth(scheme, "title_color"))
        assert _pt_of(fig.title.text_font_size) == pytest.approx(
            _size_pt(_truth(scheme, "heading_size")), abs=SIZE_TOL_PT)

    def test_the_subtitle_has_the_subheading_size_and_colour(
            self, scheme, mode):
        lab = _label(_page(scheme, "titles", mode).fig, "S")
        assert _pt_of(lab.text_font_size) == pytest.approx(
            _size_pt(_truth(scheme, "subheading_size",
                            "subheading_font_size")), abs=SIZE_TOL_PT)
        assert _hex(lab.text_color) == _hex(_truth(scheme, "subheading_color"))

    def test_the_note_has_its_textboxs_size_colour_and_fill(self, scheme,
                                                            mode):
        """This compared the note to ``body_color`` and passed only because
        body and small_body are the same colour in all fourteen shipped
        schemes; then to ``small_body``, which is the box of most schemes
        but not economist's (``textboxstyle note reverse_big``: white
        medlarge text in an emidblue box) or s1manual's (key_label).  The
        box Stata reads is the scheme's ``textboxstyle note`` (S3 batch)."""
        lab = _label(_page(scheme, "titles", mode).fig, "N")
        assert _pt_of(lab.text_font_size) == pytest.approx(
            _size_pt(_truth(scheme, "note_text_size")), abs=SIZE_TOL_PT)
        assert _hex(lab.text_color) == _hex(_truth(scheme, "note_text_color"))
        fill = _fixture()[scheme]["note_box_fill_color"]
        if fill is None:
            assert lab.background_fill_color is None, lab.background_fill_color
        else:
            assert _hex(lab.background_fill_color) == _hex(fill)

    def test_the_caption_has_the_body_size_and_colour(self, scheme, mode):
        lab = _label(_page(scheme, "titles", mode).fig, "C")
        assert _pt_of(lab.text_font_size) == pytest.approx(
            _size_pt(_truth(scheme, "body_size", "body_font_size")),
            abs=SIZE_TOL_PT)
        assert _hex(lab.text_color) == _hex(_truth(scheme, "body_color"))

    def test_axis_titles_and_tick_labels_take_the_schemes_colours(
            self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        title_c = _hex(_truth(scheme, "axis_title_color"))
        tick_c = _hex(_truth(scheme, "tick_label_color"))
        for ax in list(fig.xaxis) + list(fig.yaxis):
            assert _hex(ax.axis_label_text_color) == title_c, (
                f"{scheme}/{mode}: axis title {ax.axis_label_text_color!r}")
            assert _hex(ax.major_label_text_color) == tick_c, (
                f"{scheme}/{mode}: tick labels {ax.major_label_text_color!r}")

    def test_axis_title_and_tick_label_sizes_are_the_schemes(
            self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        for ax in list(fig.xaxis) + list(fig.yaxis):
            assert _pt_of(ax.axis_label_text_font_size) == pytest.approx(
                _size_pt(_truth(scheme, "axis_title_size")), abs=SIZE_TOL_PT)
            assert _pt_of(ax.major_label_text_font_size) == pytest.approx(
                _size_pt(_truth(scheme, "tick_label_size")), abs=SIZE_TOL_PT)

    def test_the_header_css_carries_the_heading_and_subheading(
            self, scheme, mode):
        """css_block(): .db-title is the heading box, .db-subtitle the
        subheading box (DESIGN.md section 4-B item 9).  The subtitle used
        to take the heading's colour and the body text size."""
        css = _page(scheme, "titles", mode).css
        assert _hex(_rule_value(css, ".db-title", "color")) == \
            _hex(_truth(scheme, "title_color"))
        assert _pt_of(_rule_value(css, ".db-title", "font-size")) == \
            pytest.approx(_size_pt(_truth(scheme, "heading_size")),
                          abs=SIZE_TOL_PT)
        assert _hex(_rule_value(css, ".db-subtitle", "color")) == \
            _hex(_truth(scheme, "subheading_color"))
        assert _pt_of(_rule_value(css, ".db-subtitle", "font-size")) == \
            pytest.approx(_size_pt(_truth(scheme, "subheading_size",
                                          "subheading_font_size")),
                          abs=SIZE_TOL_PT)


@pytest.mark.parametrize("mode", MODES)
class TestS1rcolorTextIsWhite:
    """s1rcolor is white text on a black page; every text colour above is
    white (scheme-s1rcolor.scheme sets every `color <textbox>' to white)."""

    def test_every_text_colour_is_white(self, mode):
        fig = _page("s1rcolor", "titles", mode).fig
        seen = {"title": fig.title.text_color}
        for txt in ("S", "N", "C"):
            seen[txt] = _label(fig, txt).text_color
        for ax in list(fig.xaxis) + list(fig.yaxis):
            seen[f"axis title {ax.id}"] = ax.axis_label_text_color
            seen[f"tick labels {ax.id}"] = ax.major_label_text_color
        seen["legend labels"] = _legend(fig).label_text_color
        wrong = {k: v for k, v in seen.items() if _hex(v) != "#ffffff"}
        assert not wrong, f"s1rcolor/{mode}: not white: {wrong}"


@pytest.mark.parametrize("mode", MODES)
class TestAC162TheEconomistTitleIsLargerThanItsSubtitle:
    """AC-16.2a: economist's ``gsize heading 6.0`` is 17.28 pt on Stata's
    scale (6.0 x 2.88), above its ``gsize subheading medium`` 11 pt.  dash
    drew the title at 7 pt, under the subtitle."""

    def test_title_17_28pt_over_subtitle_11pt(self, mode):
        fig = _page("economist", "titles", mode).fig
        assert fig.title.text_font_size == "17.28pt"
        sub = _label(fig, "S")
        assert sub.text_font_size == "11pt"
        assert _pt_of(fig.title.text_font_size) > _pt_of(sub.text_font_size)


# ---------------------------------------------------------------------------
# (iv) line width, (x) marker size
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestTheGlyphSizes:
    def test_the_line_width_is_the_schemes_on_statas_scale(
            self, scheme, mode):
        line = _glyph(_page(scheme, "titles", mode).fig, "Line")
        want = _line_width_px(_truth(scheme, "default_line_width"))
        assert _v(line.line_width) == pytest.approx(want, abs=SIZE_TOL_PX), (
            f"{scheme}/{mode}: linewidth p "
            f"{_truth(scheme, 'default_line_width')['name']!r} drawn as "
            f"{_v(line.line_width)!r}, want {want}")

    def test_the_marker_size_follows_the_symbolsize_ladder(
            self, scheme, mode):
        sc = _glyph(_page(scheme, "titles", mode).fig, "Scatter")
        want = _marker_px(_truth(scheme, "symbolsize"))
        assert _v(sc.size) == pytest.approx(want, abs=SIZE_TOL_PX), (
            f"{scheme}/{mode}: symbolsize p "
            f"{_truth(scheme, 'symbolsize')['name']!r} drawn as "
            f"{_v(sc.size)!r} px, want {want}")


@pytest.mark.parametrize("mode", MODES)
class TestAC162TheEconomistLineIsThickerThanS2colors:
    """AC-16.2b: economist's ``linewidth p 1.2`` is four medium widths --
    6.0 px against s2color's 1.5 px.  dash drew it as 1.2 px."""

    def test_6_0_over_1_5(self, mode):
        eco = _v(_glyph(_page("economist", "titles", mode).fig, "Line")
                 .line_width)
        s2 = _v(_glyph(_page("s2color", "titles", mode).fig, "Line")
                .line_width)
        assert (eco, s2) == (pytest.approx(6.0), pytest.approx(1.5))
        assert eco > s2


@pytest.mark.parametrize("mode", MODES)
class TestNamedMarkerSizes:
    """The symbolsize keywords are NOT the gsize ladder (DESIGN.md
    section 3): small is 3.0 pt, medium 4.4, large 7.0 at 4 inches."""

    @pytest.mark.parametrize("scheme,px", [
        ("stcolor", 5.45), ("economist", 12.73), ("s2color", 8.0)])
    def test_the_size(self, mode, scheme, px):
        sc = _glyph(_page(scheme, "titles", mode).fig, "Scatter")
        assert round(float(_v(sc.size)), 2) == px


# ---------------------------------------------------------------------------
# (vii) the legend
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestTheLegend:
    """With no legend() placement, the scheme's ``clockdir legend_position``
    decides where the legend sits and ``numstyle legend_cols`` how many
    columns it has; its labels are the key_label textbox."""

    def test_the_default_placement_is_the_schemes_clock(self, scheme, mode):
        fig = _page(scheme, "titles", mode).fig
        lg = _legend(fig)
        clock = int(_truth(scheme, "legend_position"))
        cols = int(_truth(scheme, "legend_cols") or 0)
        side = dr._DASH_CLOCK_SIDE[clock]
        assert _legend_side(fig, lg) == side, (
            f"{scheme}/{mode}: clock {clock} is {side}, legend is in "
            f"{_legend_side(fig, lg)!r}")
        want_orient = "horizontal" if side in ("above", "below") else "vertical"
        assert lg.orientation == want_orient
        if cols > 1:
            assert lg.ncols == cols, (
                f"{scheme}/{mode}: legend_cols {cols}, ncols {lg.ncols!r}")
        else:
            assert lg.ncols in ("auto", 1)

    def test_the_scheme_placed_legend_sits_nearest_the_plot(
            self, scheme, mode):
        """Stata's rings (scheme-s2color.scheme: ``legend_ring 3``,
        ``note_ring 4``, ``caption_ring 5``, ``subtitle_ring 6``,
        ``title_ring 7``): the legend is the annotation nearest the plot,
        inside the note, caption and subtitle, and outside the axis.
        Bokeh lays a side panel out in list order, first nearest the frame
        (``above`` and ``left`` are reversed to the same effect), so in
        its panel the Legend must come after every Axis and before every
        Label.  dash appended it LAST: under s2color the note and caption
        sat between the plot and the legend, under economist the legend
        sat between the title and the subtitle."""
        fig = _page(scheme, "titles", mode).fig
        lg = _legend(fig)
        side = _legend_side(fig, lg)
        panel = list(getattr(fig, side))
        order = [type(r).__name__ for r in panel]
        at = panel.index(lg)
        axes = [i for i, r in enumerate(panel) if isinstance(r, Axis)]
        labels = [i for i, r in enumerate(panel) if isinstance(r, Label)]
        assert all(i < at for i in axes), (
            f"{scheme}/{mode}: the legend sits between the frame and the "
            f"axis in fig.{side}: {order}")
        assert all(at < i for i in labels), (
            f"{scheme}/{mode}: a Label sits between the plot and the "
            f"legend in fig.{side}: {order}")

    def test_the_scheme_placed_legend_is_centred_in_its_panel(
            self, scheme, mode):
        """A legend Stata places at 6, 12, 3 or 9 o'clock is centred on the
        plot; a legend moved into a Bokeh side panel kept the model's
        default ``top_right``, so a below-legend hugged the right edge."""
        lg = _legend(_page(scheme, "titles", mode).fig)
        assert lg.location == "center", (
            f"{scheme}/{mode}: legend location {lg.location!r}")

    def test_the_labels_are_the_key_label_textbox(self, scheme, mode):
        lg = _legend(_page(scheme, "titles", mode).fig)
        assert _pt_of(lg.label_text_font_size) == pytest.approx(
            _size_pt(_truth(scheme, "key_label_size", "key_label_font_size")),
            abs=SIZE_TOL_PT)
        assert _hex(lg.label_text_color) == \
            _hex(_truth(scheme, "key_label_color"))

    def test_the_box_is_the_schemes_legend_colours(self, scheme, mode):
        lg = _legend(_page(scheme, "titles", mode).fig)
        assert _hex(lg.background_fill_color) == \
            _hex(_truth(scheme, "legend_bg_color"))
        assert _hex(lg.border_line_color) == \
            _hex(_truth(scheme, "legend_border_color"))

    def test_an_explicit_position_and_cols_still_win(self, scheme, mode):
        fig = _page(scheme, "legend_pos9", mode).fig
        lg = _legend(fig)
        assert _legend_side(fig, lg) == "left"
        assert lg.orientation == "vertical"
        assert lg.ncols == 1


class TestNamedLegendPlacements:
    @pytest.mark.parametrize("mode", MODES)
    def test_s2color_below_in_two_columns(self, mode):
        fig = _page("s2color", "titles", mode).fig
        lg = _legend(fig)
        assert (_legend_side(fig, lg), lg.orientation, lg.ncols) == \
            ("below", "horizontal", 2)

    @pytest.mark.parametrize("mode", MODES)
    def test_economist_above_in_three_columns(self, mode):
        fig = _page("economist", "titles", mode).fig
        lg = _legend(fig)
        assert (_legend_side(fig, lg), lg.orientation, lg.ncols) == \
            ("above", "horizontal", 3)

    @pytest.mark.parametrize("mode", MODES)
    def test_stcolor_right_vertical(self, mode):
        fig = _page("stcolor", "titles", mode).fig
        lg = _legend(fig)
        assert (_legend_side(fig, lg), lg.orientation) == ("right", "vertical")


# ---------------------------------------------------------------------------
# (viii) the KPI card
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestTheKpiCard:
    """The KPI card is Stata's legend box: ``color legend`` fills it,
    ``color legend_line`` borders it, ``color text`` is its text.  The
    colours travel as the ``.db-kpi-card`` class rule in an InlineStyleSheet
    on the Div (a Bokeh 3 Div renders in a shadow root, so the page's
    ``<style>`` never reaches it); an explicit bgcolor() is inline and
    beats the rule."""

    def test_no_inline_background_without_bgcolor(self, scheme, mode):
        card = _card(_page(scheme, "kpi", mode).kpis["k1"])
        assert card["class"] == "db-kpi-card"
        assert not card["inline_background"], (
            f"{scheme}/{mode}: inline {card['style']!r}")

    def test_the_stylesheet_carries_the_legend_colours(self, scheme, mode):
        card = _card(_page(scheme, "kpi", mode).kpis["k1"])
        rule = _rule(card["css"], ".db-kpi-card")
        assert rule, f"{scheme}/{mode}: no .db-kpi-card rule on the Div"
        lbg = _hex(_truth(scheme, "legend_bg_color"))
        lbc = _hex(_truth(scheme, "legend_border_color"))
        assert re.search(r"background-color:\s*" + re.escape(lbg), rule), rule
        assert re.search(r"border:\s*1px solid " + re.escape(lbc), rule), rule

    def test_the_value_is_the_schemes_text_colour(self, scheme, mode):
        card = _card(_page(scheme, "kpi", mode).kpis["k1"])
        assert _hex(card["value_color"]) == _hex(_truth(scheme, "text_color"))

    def test_an_explicit_bgcolor_is_still_inline(self, scheme, mode):
        card = _card(_page(scheme, "kpi_bg", mode).kpis["k1"])
        assert card["class"] == "db-kpi-card"
        assert re.search(r"background:\s*#ecf0f1", card["style"]), card["style"]


@pytest.mark.parametrize("mode", MODES)
class TestAC163TheEconomistCardIsTheEconomistLegendBox:
    """AC-16.3: under economist the KPI card is #c6d3df, the colour of its
    legend box and page; dash drew a #f8f9fa card with a #dee2e6 border."""

    def test_c6d3df(self, mode):
        card = _card(_page("economist", "kpi", mode).kpis["k1"])
        assert not card["inline_background"], card["style"]
        rule = _rule(card["css"], ".db-kpi-card")
        assert "background-color: #c6d3df" in rule, rule
        assert "border: 1px solid #c6d3df" in rule, rule


# ---------------------------------------------------------------------------
# (ix) xlabel(, grid) under a gridless scheme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("mode", MODES)
class TestXlabelGridUsesTheSchemesGridColour:
    def test_the_grid_the_option_turns_on_is_the_schemes(self, scheme, mode):
        fig = _page(scheme, "xgrid", mode).fig
        want = _hex(_truth(scheme, "grid_color"))
        for g in fig.xgrid:
            assert _hex(g.grid_line_color) == want, (
                f"{scheme}/{mode}: xlabel(, grid) drew {g.grid_line_color!r}, "
                f"the scheme's grid is {want}")
            assert _hex(g.grid_line_color) != "#e5e5e5"


# ---------------------------------------------------------------------------
# (xi) the unit functions
# ---------------------------------------------------------------------------

class TestTheUnitFunctions:
    """DESIGN.md section 3, on the parser itself."""

    @pytest.fixture
    def sp(self):
        return dr.SchemeParser("s2color")

    @pytest.mark.parametrize("raw,want", [
        ("6.0", "17.28pt"), ("0.1", "0.288pt"), ("5.0", "14.4pt")])
    def test_a_numeric_gsize_is_2_88pt_per_unit_with_no_floor(
            self, sp, raw, want):
        sp._props["gsize k"] = raw
        assert sp._gsize("gsize k") == want

    @pytest.mark.parametrize("name,want", [("minuscule", "1pt"),
                                           ("vhuge", "28pt")])
    def test_the_two_corrected_gsize_keywords(self, name, want):
        assert dr.SchemeParser._GSIZE_PT[name] == want

    @pytest.mark.parametrize("raw,want", [("1.2", 6.0), ("0.30", 1.5),
                                          ("3.5", 17.5)])
    def test_a_numeric_linewidth_is_5px_per_stata_unit(self, sp, raw, want):
        sp._props["linewidth k"] = raw
        assert sp._lwidth("linewidth k") == pytest.approx(want)

    def test_medium_keyword_still_anchors_at_1_5(self, sp):
        sp._props["linewidth k"] = "medium"
        assert sp._lwidth("linewidth k") == pytest.approx(1.5)

    def test_the_symbolsize_ladder_is_statas(self):
        want = {"zero": 0, "vtiny": 0.29, "tiny": 1.0, "vsmall": 1.5,
                "small": 3.0, "medsmall": 3.6, "medium": 4.4,
                "medlarge": 5.6, "large": 7.0, "vlarge": 9.0, "huge": 14.0,
                "vhuge": 16.0, "ehuge": 32.0}
        ladder = dr.SchemeParser._SYMBOLSIZE_PT
        assert set(ladder) == set(want)
        for k, v in want.items():
            assert float(ladder[k]) == pytest.approx(v), k
        assert dr.SchemeParser._MARKER_PX_ANCHOR_PT == pytest.approx(4.4)

    @pytest.mark.parametrize("kw,px", [
        ("medium", 8.0), ("small", 8.0 * 3.0 / 4.4),
        ("large", 8.0 * 7.0 / 4.4), ("3.0", 8.0 * 3.0 * 2.88 / 4.4)])
    def test_markersize_px_anchors_medium_at_8px(self, sp, kw, px):
        assert sp._markersize_px(kw) == pytest.approx(px, abs=1e-6)


# ---------------------------------------------------------------------------
# (xii) both modes agree on every value above
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scheme", _grouped(SCHEMES, "scheme"))
@pytest.mark.parametrize("case", CASES)
class TestBothModesAgree:
    def test_same_profile(self, scheme, case):
        std = _profile(_page(scheme, case, "standalone"))
        srv = _profile(_page(scheme, case, "served"))
        diffs = tp._diff(std, srv)
        assert not diffs, tp._explain(f"{scheme}/{case}", "profiles", diffs)

    def test_the_profile_is_not_empty(self, scheme, case):
        p = _profile(_page(scheme, case, "standalone"))
        assert p["figures"] and p["figures"][0]["glyphs"]
        if case.startswith("kpi"):
            assert "k1" in p["kpis"]
