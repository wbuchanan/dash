"""The adversarial review of WP-16, pinned (DESIGN.md section 6.1, R1-R10).

Each test here was written before its fix and observed to fail against the
tree the review measured (CLAUDE.md rule 8).  The findings, with their
evidence, are in scratchpad/wp16/review_result.json; the decisions are
section 6.1 of the WP-16 DESIGN.md.  In one line each:

* R1  a layout(bs) page with a KPI or a filter widget was BLANK: the head
      scrape stopped at the literal ``<head></head>`` inside Bokeh 3.9's
      inlined widgets bundle, cutting the script in half;
* R2  a legend placed into a side panel by the scheme or by position() was
      the OUTERMOST item on that side, so the note and caption (Stata rings
      4 and 5) sat between the plot and the legend (ring 3);
* R3  a side-panel legend kept Bokeh's ``top_right`` location and was drawn
      flush right under the plot where Stata centres it;
* R4  the scheme's ``numstyle legend_cols`` survived a user ``legend(rows(1))``,
      so three keys asked for in one row came out as a 2x2 grid;
* R5  the Segment glyphs of spike, rspike, rcap, pcspike and pcarrow and the
      line halves of dropline and rcapsym took the MARKER colour ``color
      p#mark`` because their mappers asked ``default_color`` for "scatter";
* R6  a numeric ``gsize`` was formatted with ``:g``, which turns to
      scientific notation below 1e-4, and Bokeh's FontSize validator then
      aborted the whole figure on ``2.88e-05pt``;
* R7  ``linewidth axisline`` was extracted, shipped and read by nothing;
* R8  a hostile ``clockdir legend_position 99`` / ``numstyle legend_rows
      1000`` / ``linewidth major_grid -4`` passed without a word;
* R9  the JS rebuild of a KPI card after a filter move dropped the value
      div's ``id="kpi_val_<name>"``;
* R10 the served by() panel title was ``html.escape(go["title"])``, so
      ``title("By")`` was served as ``&quot;By&quot; -- Domestic``.

Rendering goes through the parity file's own helpers, so both modes are
built exactly as ``test_mode_parity.py`` builds them; a user .scheme file is
written into the test's tmp_path, which is made the working directory so
``SchemeParser._resolve_path`` finds it as a file reference.
"""
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import warnings

import pytest
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.models import Axis, GlyphRenderer, Label, Legend, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("standalone", "served")
FIXTURE = os.path.join(_HERE, "fixtures", "scheme_truth.json")

#: The two shipped schemes the review measured, and where their clock puts
#: the legend.
S2COLOR_SIDE = "below"       # clockdir legend_position 6
ECONOMIST_SIDE = "above"     # clockdir legend_position 12


# ---------------------------------------------------------------------------
# Rendering, both modes
# ---------------------------------------------------------------------------

def _standalone(spec):
    """(renderer, figures) from the saved-dashboard renderer."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, _ = tp._standalone(spec)
    curdoc().clear()
    return r, list(r.figures.values())


def _served(spec):
    """(module, figures) from the generated server app."""
    tag, sp, dp = tp._write(spec)
    ap = os.path.join(tp._TMP, f"app_review_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_review_{tag}")
        doc = Document()
        mod.make_document(doc)
    curdoc().clear()
    return mod, list(doc.select(dict(type=Plot)))


def _figures(spec, mode):
    return (_standalone(spec) if mode == "standalone" else _served(spec))[1]


def _fig(spec, mode):
    figs = _figures(spec, mode)
    assert len(figs) == 1, f"{len(figs)} figures"
    return figs[0]


def _two_series(scheme, legend="", **go):
    """A scatter and a line under *scheme*, with a title, a subtitle, a
    note and a caption, so every side panel has a Label to order the
    legend against."""
    opts = {"title": "T", "subtitle": "S", "note": "N", "caption": "C"}
    opts.update(go)
    if legend:
        opts["legend"] = legend
    return tp._spec([plot_for("scatter"), plot_for("line")],
                    {"scheme": scheme}, opts)


def _three_series(scheme, legend):
    return tp._spec([plot_for("scatter"),
                     plot_for("line", yvar="price"),
                     plot_for("connected", yvar="rep")],
                    {"scheme": scheme}, {"legend": legend})


def _legend(fig):
    lgs = list(fig.legend)
    assert len(lgs) == 1, f"{len(lgs)} legends"
    return lgs[0]


def _side_of(fig, lg):
    for side in ("above", "below", "left", "right", "center"):
        if any(m is lg for m in getattr(fig, side)):
            return side
    return None


def _index_of(panel, model):
    return next(i for i, m in enumerate(panel) if m is model)


def _val(x):
    """A Bokeh colour property as its plain value."""
    if isinstance(x, str) or x is None:
        return x
    if isinstance(x, dict) and "value" in x:
        return x["value"]
    return getattr(x, "value", x)


def _glyph_colors(fig):
    """``{"Segment": {line colours}, "Scatter": {fill colours}}`` of the
    figure's real (non-swatch) glyph renderers."""
    out = {"Segment": set(), "Scatter": set()}
    for r in fig.renderers:
        if not isinstance(r, GlyphRenderer) or dr._dash_is_swatch(r):
            continue
        # dot's rows of dots are markerstyle dots, no p# marker (WP-31
        # B5b; test/fixtures/dot_truth.json D01, D25).
        if "dash_dots" in (r.tags or []):
            continue
        kind = type(r.glyph).__name__
        if kind == "Segment":
            out["Segment"].add(str(_val(r.glyph.line_color)).lower())
        elif kind == "Scatter":
            out["Scatter"].add(str(_val(r.glyph.fill_color)).lower())
    return out


def _user_scheme(tmp_path, monkeypatch, name, lines):
    """Write a self-contained user .scheme file and make its directory the
    working directory, which is where a file reference is looked for."""
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return name


def _truth(scheme, key):
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)[scheme][key]


def _line_width_px(entry):
    """Expected pixels for a fixture linewidth entry: a number is a Stata
    linewidth unit (x5); a keyword goes through dash's ladder."""
    name = str(entry["name"]).strip().lower()
    try:
        return float(name) * 5.0
    except ValueError:
        return dr.OptionTranslator.translate_lwidth(name)


# ---------------------------------------------------------------------------
# R1: the Bootstrap page keeps the whole widgets bundle
# ---------------------------------------------------------------------------

class TestBootstrapPageWithWidgets:
    """Bokeh 3.9's inlined bokeh-widgets.min.js contains the literal
    ``<head></head>`` (DOMPurify).  A non-greedy ``<head>(.*?)</head>``
    scrape stopped there, 189,588 characters into the bundle, so the
    script was never closed and dash's own ``</head><body><script>``
    landed inside it: every layout(bs) page with a KPI or a filter widget
    was a white page with ``Uncaught SyntaxError`` in the console."""

    @staticmethod
    def _page(kpis=None, filt=""):
        bo = {"layout": "bs", "scheme": "s2color"}
        if filt:
            bo["filter"] = filt
        spec = tp._spec([plot_for("scatter")], bo, kpis=kpis)
        _, sp, dp = tp._write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        curdoc().clear()
        return page

    def test_a_kpi_page_closes_every_script_it_opens(self):
        page = self._page(kpis=[tp._kpi()])
        assert page.count("<script") == page.count("</script>"), (
            f"{page.count('<script')} script opens, "
            f"{page.count('</script>')} closes: the head scrape cut a "
            "bundle in half")
        assert "/* END bokeh-widgets.min.js */" in page, (
            "the widgets bundle does not reach its own END marker")

    def test_the_kpi_card_is_on_the_page(self):
        """The card travels inside Bokeh's HTML-escaped document JSON, so
        its markup is looked for by name and class, not by literal tag."""
        page = self._page(kpis=[tp._kpi()])
        assert "kpi_val_k1" in page and "db-kpi-card" in page

    def test_a_filter_page_closes_every_script_it_opens(self):
        page = self._page(filt="foreign")
        assert page.count("<script") == page.count("</script>")
        assert "/* END bokeh-widgets.min.js */" in page

    def test_a_page_without_widgets_is_unchanged(self):
        page = self._page()
        assert page.count("<script") == page.count("</script>")
        assert "/* END bokeh.min.js */" in page


# ---------------------------------------------------------------------------
# R2: a side-panel legend is NEAREST the plot (Stata ring 3)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scheme, legend, side", [
    ("s2color", "", S2COLOR_SIDE),
    ("economist", "", ECONOMIST_SIDE),
    ("s2color", "position(12)", "above"),
    ("economist", "position(6)", "below"),
    ("s2color", "position(3)", "right"),
])
class TestSidePanelLegendOrder:
    """Stata's rings: legend 3, note 4, caption 5, subtitle 6, title 7
    (scheme-s2color.scheme:1946-1951) -- the legend is the innermost of
    the text boxes on its side.  Bokeh lays a side panel out in list
    order, first nearest the plot (``above`` reversed), so the Legend has
    to precede every Label in the panel.  It still follows the axis: the
    axis is Stata's ring 1-2, and a legend between the frame and the tick
    labels is not what any scheme asks for."""

    def test_the_legend_precedes_every_label_and_follows_the_axis(
            self, scheme, legend, side, mode):
        fig = _fig(_two_series(scheme, legend), mode)
        lg = _legend(fig)
        assert _side_of(fig, lg) == side
        panel = list(getattr(fig, side))
        li = _index_of(panel, lg)
        labels = [i for i, m in enumerate(panel) if isinstance(m, Label)]
        axes = [i for i, m in enumerate(panel) if isinstance(m, Axis)]
        assert all(li < i for i in labels), (
            f"{scheme}/{mode} legend({legend!r}): Legend at {li} in "
            f"fig.{side}, Labels at {labels}: the note/caption/subtitle "
            "sit between the plot and the legend")
        assert all(i < li for i in axes), (
            f"{scheme}/{mode}: Legend at {li} precedes an axis at {axes}")


# ---------------------------------------------------------------------------
# R3: a side-panel legend is centred
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestSidePanelLegendIsCentred:
    """Bokeh positions a side-panel legend by its ``location``; at the
    default ``top_right`` it is flush right under (or over) the plot.
    Stata centres a 6/12 o'clock legend, and a 3/9 o'clock one vertically."""

    @pytest.mark.parametrize("scheme", ["s2color", "economist", "stcolor"])
    def test_the_schemes_default_placement_is_centred(self, scheme, mode):
        lg = _legend(_fig(_two_series(scheme), mode))
        assert str(lg.location) == "center", (
            f"{scheme}/{mode}: legend.location is {lg.location!r}")

    @pytest.mark.parametrize("legend", ["position(6)", "position(12)",
                                        "position(3)"])
    def test_an_explicit_position_is_centred(self, legend, mode):
        lg = _legend(_fig(_two_series("s2color", legend), mode))
        assert str(lg.location) == "center"

    @pytest.mark.parametrize("legend, loc", [
        ("position(6) ring(0)", "bottom_center"),
        ("position(1) ring(0)", "top_right"),
    ])
    def test_inside_placements_are_unchanged(self, legend, loc, mode):
        fig = _fig(_two_series("s2color", legend), mode)
        lg = _legend(fig)
        assert _side_of(fig, lg) == "center"
        assert str(lg.location) == loc

    @pytest.mark.parametrize("legend", ["top", "bottom", "left", "right"])
    def test_a_bare_direction_word_leaves_the_schemes_placement(self, legend,
                                                                mode):
        """legend(top) and its siblings are not twoway's: it refuses them,
        r(198), and so does dash.ado (WP-23).  They were placed INSIDE the
        plot (top_center, ...), which this test pinned; a spec that carries
        one now keeps the scheme's own placement, below and centred under
        s2color, and the word is named as a sub-option dash does not
        implement."""
        fig = _fig(_two_series("s2color", legend), mode)
        lg = _legend(fig)
        assert _side_of(fig, lg) == "below"
        assert str(lg.location) == "center"


# ---------------------------------------------------------------------------
# R4: rows() and cols() are alternatives
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestRowsAndColsAreAlternatives:
    """s2color's ``numstyle legend_cols 2`` used to survive a user
    ``legend(rows(1))``: Bokeh then laid out ncols=2, nrows=1 and wrapped
    the third key onto a second row.  Stata treats rows() and cols() as
    alternatives, so the one the user did not give is left to Bokeh."""

    def test_rows_alone_frees_the_columns(self, mode):
        lg = _legend(_fig(_three_series("s2color", "rows(1)"), mode))
        assert (lg.ncols, lg.nrows) == ("auto", 1), (
            f"{mode}: (ncols, nrows) = {(lg.ncols, lg.nrows)!r}")

    def test_cols_alone_frees_the_rows(self, mode):
        lg = _legend(_fig(_three_series("s2color", "cols(1)"), mode))
        assert (lg.ncols, lg.nrows) == (1, "auto")

    def test_both_given_rows_wins(self, mode):
        # Was (2, 2): both kept.  WP-30 P1.19 measured twoway drawing the
        # rows whenever rows() and cols() are both given, in either order,
        # so rows() wins and the columns are left to Bokeh (as
        # test_graph_options::test_legend_rows_and_cols_combined pins).
        lg = _legend(_fig(_three_series("s2color", "cols(2) rows(2)"), mode))
        assert (lg.ncols, lg.nrows) == ("auto", 2), (
            f"{mode}: (ncols, nrows) = {(lg.ncols, lg.nrows)!r}")

    def test_neither_given_keeps_the_schemes_columns(self, mode):
        lg = _legend(_fig(_three_series("s2color", ""), mode))
        assert lg.ncols == 2


# ---------------------------------------------------------------------------
# R5: `color p#mark' is a MARKER colour
# ---------------------------------------------------------------------------

LINE = "#111111"
MARK = "#22aa22"
OUTLINE = "#0000ff"

#: What each type draws with which colour under a scheme whose p1 and
#: p1mark differ.  ``S`` is the Segment line colour, ``M`` the Scatter fill.
MARK_CASES = [
    ("scatter",   None, MARK),
    ("scatteri",  None, MARK),
    ("dot",       None, MARK),
    ("rscatter",  None, MARK),
    ("pcscatter", None, MARK),
    ("spike",     LINE, None),
    ("rspike",    LINE, None),
    ("rcap",      LINE, None),
    ("pcspike",   LINE, None),
    ("pcarrow",   LINE, None),
    ("dropline",  LINE, MARK),
    ("rcapsym",   LINE, MARK),
]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("ptype, seg, mark", MARK_CASES,
                         ids=[c[0] for c in MARK_CASES])
class TestMarkColourIsForMarkers:
    """Stata keeps a marker's colours (style/markerstyle-p#.style: fill
    ``color p#markfill``, outline ``color p#markline``) apart from the
    ``p#`` colour its "other" plots draw with: a spike, a range cap, a
    paired-coordinate spike or arrow is a line, and the line half of a
    dropline or rcapsym is one too.  ``color p#mark`` is never a marker
    colour: twoway ignores a user scheme's ``color p1mark green`` (measured
    03oct2026, WP-30 P1.4a).  Only a user scheme can tell them apart.

    Flipped (WP-30 P1.4a): this test expected markers to take ``color
    p1mark``, which followed the wrong chain."""

    def test_markers_take_p1markfill_and_segments_take_p1(
            self, ptype, seg, mark, mode, tmp_path, monkeypatch):
        name = _user_scheme(tmp_path, monkeypatch, "marks.scheme", [
            f"color p1 {LINE}", f"color p1mark {MARK}",
        ])
        spec = tp._spec([plot_for(ptype)], {"scheme": name})
        got = _glyph_colors(_fig(spec, mode))
        if seg is not None:
            assert got["Segment"] == {seg}, (
                f"{ptype}/{mode}: segments drawn in {got['Segment']}, "
                f"expected the p1 colour {seg}")
        if mark is not None:
            assert got["Scatter"] == {LINE}, (
                f"{ptype}/{mode}: markers drawn in {got['Scatter']}: "
                f"`color p1mark' is not a marker colour")
        name = _user_scheme(tmp_path, monkeypatch, "fills.scheme", [
            f"color p1 {LINE}", f"color p1markfill {MARK}",
            f"color p1markline {OUTLINE}",
        ])
        fig = _fig(tp._spec([plot_for(ptype)], {"scheme": name}), mode)
        got = _glyph_colors(fig)
        if seg is not None:
            assert got["Segment"] == {seg}, (ptype, mode, got)
        if mark is not None:
            lines = {str(_val(r.glyph.line_color)).lower()
                     for r in fig.renderers
                     if isinstance(r, GlyphRenderer)
                     and not dr._dash_is_swatch(r)
                     and "dash_dots" not in (r.tags or [])
                     and type(r.glyph).__name__ == "Scatter"}
            assert (got["Scatter"], lines) == ({mark}, {OUTLINE}), (
                ptype, mode, got["Scatter"], lines)


# ---------------------------------------------------------------------------
# R6: a numeric gsize is fixed-decimal and bounded
# ---------------------------------------------------------------------------

class TestNumericGsize:
    """``f"{val * 2.88:g}pt"`` went scientific below 1e-4, and Bokeh's
    FontSize validator rejected ``2.88e-05pt`` -- the whole figure failed
    to build on a scheme saying ``gsize body 0.00001``."""

    @staticmethod
    def _parser(**props):
        sp = dr.SchemeParser.fallback()
        sp._props = {k.replace("__", " "): v for k, v in props.items()}
        return sp

    @pytest.mark.parametrize("raw, want", [
        ("6.0", "17.28pt"),        # economist's heading
        ("3.8194", "11pt"),        # Stata's medium: 11pt, no trailing .0
        ("5.0", "14.4pt"),
        ("0.1", "0.288pt"),
        ("347.2", "999.936pt"),
    ])
    def test_a_value_in_range_is_fixed_decimal(self, raw, want):
        sp = self._parser(gsize__k=raw)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert sp._gsize("gsize k", "9pt") == want

    @pytest.mark.parametrize("raw", ["0.00001", "0.00003", "0", "1e20",
                                     "123456789", "400"])
    def test_a_value_outside_0_to_1000pt_falls_back_with_a_warning(
            self, raw):
        sp = self._parser(gsize__k=raw)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = sp._gsize("gsize k", "9pt")
        assert got == "9pt", f"{raw!r} -> {got!r}"
        msgs = [str(w.message) for w in caught]
        assert any(m.startswith("dash scheme:") and "gsize k" in m
                   for m in msgs), msgs

    @pytest.mark.parametrize("raw, want", [
        ("0.00001", "9pt"), ("0.0001", "9pt"), ("6.0", "17.28pt"),
        ("3.8194", "11pt"), ("1e20", "9pt"),
    ])
    def test_every_rendered_size_is_a_valid_bokeh_font_size(self, raw, want):
        """What the guard is for: the string reaches a FontSize property.

        Bokeh refuses a scientific form ("2.88e-05pt", "1e+20pt") with a
        ValueError; each value here is the one measured 24sep2026, and a
        FontSize takes it unchanged.
        """
        from bokeh.models import Title
        sp = self._parser(gsize__k=raw)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            size = sp._gsize("gsize k", "9pt")
        assert size == want
        assert Title(text_font_size=size).text_font_size == want


# ---------------------------------------------------------------------------
# R7: `linewidth axisline' reaches the axes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestAxisLineWidth:
    """The directive was added to the extractor, the fixture, all fourteen
    scheme files and the fallback dict, and read by nothing: every axis
    line was Bokeh's 1px."""

    @pytest.mark.parametrize("scheme", ["economist", "s2color"])
    def test_a_shipped_schemes_axisline_width_is_on_every_axis(
            self, scheme, mode):
        want = _line_width_px(_truth(scheme, "axis_line_width"))
        fig = _fig(_two_series(scheme), mode)
        axes = list(fig.xaxis) + list(fig.yaxis)
        assert axes
        for ax in axes:
            assert ax.axis_line_width == pytest.approx(want, abs=0.02), (
                f"{scheme}/{mode}: axis_line_width {ax.axis_line_width}, "
                f"scheme says {want}")

    def test_a_numeric_axisline_is_a_stata_linewidth_unit(
            self, mode, tmp_path, monkeypatch):
        name = _user_scheme(tmp_path, monkeypatch, "axis.scheme",
                            ["linewidth axisline 0.6"])
        fig = _fig(tp._spec([plot_for("scatter")], {"scheme": name}), mode)
        # One x axis and one y axis: the loop below passed a figure with
        # no axes at all, having checked nothing (24sep2026).
        axes = list(fig.xaxis) + list(fig.yaxis)
        assert len(axes) == 2, axes
        for ax in axes:
            # Flipped (WP-30 P1.12b): 0.6 Stata units x 3.84 px (was 5 px
            # per unit on dash's private scale, 3.0).
            assert ax.axis_line_width == pytest.approx(2.304, abs=0.02)


def test_the_parser_exposes_axis_line_width():
    sp = dr.SchemeParser("economist")
    assert sp.axis_line_width == pytest.approx(
        dr.OptionTranslator.translate_lwidth("thin"))
    assert dr.SchemeParser.fallback().axis_line_width == pytest.approx(
        dr.OptionTranslator.translate_lwidth("thin"))


# ---------------------------------------------------------------------------
# R8: hostile placement and width values are refused, loudly
# ---------------------------------------------------------------------------

class TestHostileSchemeValues:
    """The colour path warns and falls back on a value it cannot use; the
    clock, the legend grid and the line widths accepted anything."""

    HOSTILE = ["clockdir legend_position 99",
               "numstyle legend_rows 1000",
               "linewidth major_grid -4"]

    def _parse(self, tmp_path, monkeypatch, lines, name="hostile.scheme"):
        fname = _user_scheme(tmp_path, monkeypatch, name, lines)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sp = dr.SchemeParser(fname)
        return sp, [str(w.message) for w in caught
                    if str(w.message).startswith("dash scheme:")]

    def test_three_hostile_values_give_three_warnings_and_the_defaults(
            self, tmp_path, monkeypatch):
        sp, msgs = self._parse(tmp_path, monkeypatch, self.HOSTILE)
        assert len(msgs) == 3, msgs
        for key in ("clockdir legend_position", "numstyle legend_rows",
                    "linewidth major_grid"):
            assert any(key in m for m in msgs), (key, msgs)
        assert sp.legend_position is None
        assert sp.legend_rows == 0
        assert sp.grid_line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("thin"))  # WP-30 P1.2a: the default is the medium/thin rung on Stata's ladder (S13 D-13g)

    def test_a_negative_legend_cols_is_refused(self, tmp_path, monkeypatch):
        sp, msgs = self._parse(tmp_path, monkeypatch,
                               ["numstyle legend_cols -2"])
        assert len(msgs) == 1 and "numstyle legend_cols" in msgs[0], msgs
        assert sp.legend_cols is None

    @pytest.mark.parametrize("key, attr, default", [
        ("linewidth p", "default_line_width",
         dr.OptionTranslator.translate_lwidth("medium")),  # WP-30 P1.2a: the default is the medium/thin rung on Stata's ladder (S13 D-13g)
        # P1.12b and P1.2a: the thin rung on Stata's ladder.
        ("linewidth minor_grid", "minor_grid_line_width",
         dr.OptionTranslator.translate_lwidth("thin")),
        ("linewidth axisline", "axis_line_width",
         dr.OptionTranslator.translate_lwidth("thin")),
    ])
    def test_every_negative_linewidth_is_refused(self, key, attr, default,
                                                 tmp_path, monkeypatch):
        sp, msgs = self._parse(tmp_path, monkeypatch, [f"{key} -1"])
        assert len(msgs) == 1 and key in msgs[0], msgs
        assert getattr(sp, attr) == pytest.approx(default)

    def test_the_clock_boundaries_are_kept(self, tmp_path, monkeypatch):
        sp, msgs = self._parse(tmp_path, monkeypatch,
                               ["clockdir legend_position 12"])
        assert msgs == [] and sp.legend_position == 12
        sp, msgs = self._parse(tmp_path, monkeypatch,
                               ["clockdir legend_position 0"], "zero.scheme")
        assert len(msgs) == 1 and sp.legend_position is None

    def test_the_hostile_scheme_still_renders(self, tmp_path, monkeypatch):
        name = _user_scheme(tmp_path, monkeypatch, "hostile.scheme",
                            self.HOSTILE)
        fig = _fig(_two_series(name), "standalone")
        lg = _legend(fig)
        # No usable clock: the legend stays inside, as a bare scheme's does.
        assert _side_of(fig, lg) == "center"
        # One grid per axis: the loop passed a figure with no grids, having
        # checked the refused width on nothing (24sep2026).
        grids = list(fig.xgrid) + list(fig.ygrid)
        assert len(grids) == 2, grids
        for grid in grids:
            assert grid.grid_line_width == pytest.approx(
                dr.OptionTranslator.translate_lwidth("thin"))  # WP-30 P1.2a: the default is the medium/thin rung on Stata's ladder (S13 D-13g)


# ---------------------------------------------------------------------------
# R9: the JS card rebuild is byte-identical to the Python card
# ---------------------------------------------------------------------------

def _kpi_template_js():
    """The ``kpi_div.text = (...)`` expression of the shipped callback."""
    js = dr._FILTER_JS
    lo = js.index("kpi_div.text = (")
    hi = js.index(");", lo)
    return js[lo + len("kpi_div.text = "):hi + 1]


def _card_via_python(cfg, fmt):
    """The template evaluated as Python: its string literals and ``+`` are
    Python's, ``k.x`` is attribute access, and the one JS ternary is
    rewritten as a conditional expression."""
    expr = _kpi_template_js()
    expr = re.sub(r"\(k\.(\w+) \? (.+?) : ''\)", r"((\2) if k.\1 else '')",
                  expr)
    assert "?" not in expr, "an untranslated JS construct in the template"
    return eval(expr, {"__builtins__": {}},  # noqa: S307 - our own template
                # The value is escaped by the page's dash_html_escape (WP-28
                # section 11, GAPS2 E1), html.escape's twin.
                {"k": types.SimpleNamespace(**cfg), "text": fmt,
                 "dash_html_escape": _html.escape})


def _card_via_node(cfg, fmt):
    """The template evaluated by node.

    Node is the only REAL JavaScript evaluation of the template --
    _card_via_python is a regex rewrite into Python -- so a missing node is
    a failure, as in test_filter_exclude._node.  This returned None and the
    caller skipped the comparison without a word, so on a machine without
    node the JS rebuild went unchecked and the test still passed
    (24sep2026).
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail("node is not installed; the KPI card's JavaScript "
                    "rebuild cannot be run (a silent skip here would hide "
                    "an untested template)")
    harness = (
        dr._DASH_FMT_JS + "\n"
        "const k = " + json.dumps(cfg) + ";\n"
        "const text = " + json.dumps(fmt) + ";\n"
        "const kpi_div = {};\n"
        "kpi_div.text = " + _kpi_template_js() + ";\n"
        "process.stdout.write(kpi_div.text);\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                     delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        res = subprocess.run([node, path], capture_output=True, text=True,
                             timeout=60)
        assert res.returncode == 0, res.stderr[:1200]
        return res.stdout
    finally:
        os.unlink(path)


_VALUE_DIV = re.compile(r'<div id="kpi_val_[^"]*" style="[^"]*">(.*?)</div>',
                        re.S)


@pytest.mark.parametrize("kpi", [
    tp._kpi(),
    tp._kpi(bgcolor="navy", color="red", title="Mean <mpg>",
            subtitle="a & b"),
], ids=["plain", "coloured"])
def test_the_js_rebuild_equals_the_initial_card(kpi):
    """After a filter move the rebuilt card was identical to
    ``_dash_kpi_card_html``'s EXCEPT that the value div lost its
    ``id="kpi_val_<name>"``.  The id is what the brush and filter code, and
    any test, find the value by."""
    spec = tp._spec([plot_for("scatter")], {"scheme": "s2color"},
                    kpis=[kpi])
    r, _ = _standalone(spec)
    initial = r.kpi_divs[kpi["name"]].text
    m = _VALUE_DIV.search(initial)
    assert m, initial
    fmt = m.group(1)
    cfg = r._kpi_callback_config(kpi["name"], kpi)
    assert 'id="kpi_val_' in initial
    assert _card_via_python(cfg, fmt) == initial
    assert _card_via_node(cfg, fmt) == initial


def test_the_carried_name_is_escaped():
    """The id is interpolated into markup by string concatenation, so the
    name travels escaped, exactly as ``_dash_kpi_card_html`` escapes it."""
    spec = tp._spec([plot_for("scatter")], {"scheme": "s2color"},
                    kpis=[tp._kpi()])
    r, _ = _standalone(spec)
    cfg = r._kpi_callback_config('k<1>"', {"name": 'k<1>"', "stat": "mean",
                                           "var": "mpg"})
    assert cfg["name_html"] == _html.escape('k<1>"')


# ---------------------------------------------------------------------------
# R10: the served by() panel title is the parsed title text
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, want", [
    ('"By"', "By"),
    ('"Sales & <returns>"', "Sales & <returns>"),
    ("T", "T"),
])
def test_both_modes_title_a_by_panel_the_same(title, want):
    """The served app html-escaped the RAW option, so ``title("By")`` was
    served as ``&quot;By&quot; -- Domestic``.  Bokeh draws a Title on
    the canvas: there is nothing to escape.  Flipped (WP-30 P1.15a):
    "<title> — Domestic" was wrong because twoway keeps the parsed title
    on every panel and draws the label as a row of its own."""
    from by_panel_probe import is_chrome, panel_label
    spec = tp._spec([plot_for("scatter")], {"scheme": "s2color"},
                    {"title": title, "by": "foreign"})
    titles = {}
    for mode in MODES:
        titles[mode] = sorted((f.title.text, panel_label(f))
                              for f in _figures(spec, mode)
                              if not is_chrome(f))
    assert titles["standalone"] == [(want, "Domestic"),
                                    (want, "Foreign")], titles
    assert titles["served"] == titles["standalone"], titles
