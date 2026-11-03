"""test_legend_geometry.py -- the legend is laid out as twoway's legend_g
lays it out (WP-31 D4, GAPS3 D4).

GAPS3 D4: the legend's geometry sub-options were named and not drawn, the
scheme's columns were dropped when position() was given, corner clocks
were centred on a side, pos(0) went to the right, ring(0) alone stayed at
Bokeh's top_right, label(1) with no text was dropped and the key size was
Bokeh's own.

Ground truth: test/fixtures/legend_geometry_truth.json, written by
scripts/extract_legend_geometry_truth.do from twoway's class values and
SVG export (720 SVG px per inch; one Stata relative unit is 28.8 SVG px,
2.88 pt, 3.84 px at dash's 4-inch reference).  What it measured that
decides this file's rules:

* label_blank: legend(label(1)) is rc 0 and draws key 1's symbol with no
  text -- the key is blanked, not refused.
* merge / merge_pstyle / merge_style: two keys with the same text are one
  key only when their style is the same too (pstyle(p1) twice: one key, so
  no legend is drawn; with mcolor(red) on one: two keys).  The merge is
  C13's fix (test_legend_histogram_only.py): it is why twoway draws no
  legend for ``histogram mpg || histogram price`` (hist_only: one key),
  while the same pair in two colours draws one (hist_color).
* hist_only: no legend drawn (draw_view 0); hist_on: legend(on) draws it.
* holes(2) cols(2) on three keys: the hole takes position 2 of the grid;
  holes(9) is ignored.  colfirst cols(2): column by column.  rows(3) on
  four keys: two columns of two rows (cols = 1 + int((n-1)/rows)).
* clock_k: 1 and 11 at the ends of the top, 2 and 4 the ends of the right,
  5 and 7 of the bottom, 8 and 10 of the left, 0 the centre of the plot
  region; ring(0) alone sits inside at the scheme's clock (s2color 6:
  bottom centre; stcolor 3: centre right); pos(3) keeps s2color's two
  columns.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "legend_geometry_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: One Stata relative unit in pixels at dash's 4-inch reference.
_PX_PER_UNIT = 2.88 * 4.0 / 3.0
#: One Stata relative unit in the fixture's SVG pixels.
_SVG_PER_UNIT = 28.8


def _px(units):
    return int(round(units * _PX_PER_UNIT))


def _sc(y="mpg", **o):
    return plot_for("scatter", dict(o), yvar=y, xvar="weight")


def _ln(y="mpg", **o):
    return plot_for("line", dict(o), yvar=y, xvar="weight")


TWO = [_sc(), _sc("price")]
THREE = [_sc(), _sc("price"), _sc("rep")]
FOUR = [_sc(), _sc("price"), _sc("rep"), _sc("foreign")]
LINES = [_ln(), _ln("price")]


def _build(mode, plots, legend="", scheme="s2color", go=None):
    """``(fig, warnings)``: the one figure *mode* draws."""
    g = dict(go or {})
    if legend:
        g["legend"] = legend
    spec = tp._spec(plots, {"scheme": scheme}, g)
    figs, caught = tp._figures_in(mode, spec)
    assert len(figs) == 1, len(figs)
    return figs[0], [str(w) for w in caught]


def _legend(fig):
    from bokeh.models import Legend
    lgs = [m for m in fig.select({"type": Legend})
           if str(getattr(m, "name", "") or "") != dr._COLORVAR_LEGEND_NAME]
    assert len(lgs) == 1, lgs
    return lgs[0]


def _panel_of(fig, lg):
    for side in ("above", "below", "left", "right", "center"):
        if lg in list(getattr(fig, side)):
            return side
    return None


def _text(it):
    lab = it.label
    return lab.get("value") if isinstance(lab, dict) else getattr(
        lab, "value", lab)


def _fig_legend(mode, plots, legend="", **kw):
    fig, caught = _build(mode, plots, legend, **kw)
    return fig, _legend(fig), caught


class TestTheFixture:

    def test_stamped_and_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "members", "source"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_geometry_truth.do"
        for k in ["default_geometry", "default_lines", "ring0_default",
                  "cols_with_pos", "holes", "colfirst", "label_blank",
                  "merge", "merge_pstyle", "merge_style", "hist_only",
                  "hist_on", "region", "sizes", "bplacement", "title",
                  "st_default", "st_ring0"] + ["clock_%d" % k
                                               for k in range(13)]:
            assert TRUTH[k]["rc"] == 0, k

    def test_the_measured_outcomes_this_file_rests_on(self):
        assert TRUTH["label_blank"]["drawn"] == 1
        assert [t["text"] for t in TRUTH["label_blank"]["key_texts"]] == [
            "Price"]
        assert TRUTH["hist_only"]["drawn"] == 0
        assert TRUTH["hist_on"]["drawn"] == 1
        assert TRUTH["merge_pstyle"]["keys"] == 1
        assert TRUTH["merge_style"]["keys"] == 2


def _side_and_end(rec):
    """twoway's side and end for a clock_k record: the panel the box sits
    in relative to the plot region, and where along that side."""
    cx, cy = rec["box_centre_rel"]
    if 0 < cx < 1 and 0 < cy < 1:
        return "center", "center"
    side = ("above" if cy < 0 else "below" if cy > 1
            else "left" if cx < 0 else "right")
    pr, box = rec["plot"], rec["box"]
    if side in ("above", "below"):
        if box["right"] > pr["right"] - 60 and box["left"] > pr["left"] + 60:
            end = "right"
        elif box["left"] < pr["left"] + 60 and box["right"] < pr["right"] - 60:
            end = "left"
        else:
            end = "center"
    else:
        h = rec["plot"]["bottom"] - rec["plot"]["top"]
        rel = ((box["top"] + box["bottom"]) / 2 - pr["top"]) / h
        end = "top" if rel < 0.25 else "bottom" if rel > 0.75 else "center"
    return side, end


_EXPECT_LOCATION = {
    ("above", "right"): "top_right", ("above", "left"): "top_left",
    ("above", "center"): "center", ("below", "right"): "bottom_right",
    ("below", "left"): "bottom_left", ("below", "center"): "center",
    ("right", "top"): "top_right", ("right", "bottom"): "bottom_right",
    ("right", "center"): "center", ("left", "top"): "top_left",
    ("left", "bottom"): "bottom_left", ("left", "center"): "center",
    ("center", "center"): "center",
}


@pytest.mark.parametrize("mode", MODES)
class TestDefaultGeometry:

    @pytest.mark.parametrize("scheme", ["s2color", "stcolor"])
    def test_scheme_sizes(self, mode, scheme):
        sp = dr.SchemeParser(scheme)
        _fig, lg, _ = _fig_legend(mode, LINES, scheme=scheme)
        assert lg.glyph_width == _px(sp.legend_key_xsize)
        assert lg.glyph_height == _px(sp.legend_key_ysize)
        assert lg.label_standoff == _px(sp.legend_key_gap)
        # Flipped (WP-31 D4b): keys in one row are colgap() apart, as
        # twoway draws them (legend_remainder_truth.json colgap_zero).
        one_row = lg.nrows == 1 and lg.ncols != 1
        assert lg.spacing == _px(sp.legend_col_gap if one_row
                                 else sp.legend_row_gap)
        assert lg.padding == sp.legend_margin == 5
        assert lg.margin == sp.legend_boxmargin == 5

    def test_s2color_matches_twoways_drawing(self, mode):
        """U31-1 in pixels: twoway's line key is 13 units long, the text
        starts a vsmall gap after it, and two rows are a medsmall key and
        a tiny gap apart."""
        _fig, lg, _ = _fig_legend(mode, LINES)
        ln = TRUTH["default_lines"]["key_lines"][0]
        key_units = abs(ln["x2"] - ln["x1"]) / _SVG_PER_UNIT
        gap_units = (TRUTH["default_lines"]["key_texts"][0]["x"]
                     - max(ln["x1"], ln["x2"])) / _SVG_PER_UNIT
        assert lg.glyph_width == _px(key_units) == 50
        assert lg.label_standoff == _px(gap_units) == 8
        # Flipped (WP-31 D4b): the two keys of one row are the scheme's
        # legend_col_gap (large, 4.8611 units = 19 px) apart, not its row
        # gap (legend_remainder_truth.json colgap_zero).
        assert (lg.glyph_width, lg.glyph_height, lg.label_standoff,
                lg.spacing) == (50, 13, 8, 19)

    def test_a_marker_key_takes_twoways_key_size(self, mode):
        """A legend of marker keys takes twoway's key size, symxsize() by
        symysize() (default_geometry: key_xsize 13, key_ysize 3.4722), as
        every other legend does.  Flipped (WP-32, D39 D-31.a): the key box
        grew to 2.5 times the marker so that Bokeh, which draws a legend
        marker at 0.4 of the box, drew it at the plot's size; the
        maintainer ruled the key size twoway's always."""
        rec = TRUTH["default_geometry"]
        _fig, lg, _ = _fig_legend(mode, TWO)
        assert (lg.glyph_width, lg.glyph_height) == (
            _px(rec["key_xsize"]), _px(rec["key_ysize"])) == (50, 13)

    def test_a_large_marker_does_not_grow_the_key(self, mode):
        """msize(huge) leaves the key box at twoway's size (D-31.a)."""
        _fig, lg, _ = _fig_legend(mode, [_sc(msize="huge"),
                                         _sc("price", msize="huge")])
        assert (lg.glyph_width, lg.glyph_height) == (50, 13)

    def test_forcesize_forces_the_key_box(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO, "forcesize symysize(2)")
        assert (lg.glyph_width, lg.glyph_height) == (50, 8)


@pytest.mark.parametrize("mode", MODES)
class TestSizeOptions:

    @pytest.mark.parametrize("opt,prop,want", [
        ("symxsize(5)", "glyph_width", 19),
        ("symysize(2)", "glyph_height", 8),
        ("keygap(1)", "label_standoff", 4),
        # Flipped (WP-31 D4b): rowgap() spaces rows, so it is read on one
        # column; two keys in one row are colgap() apart.
        ("cols(1) rowgap(3)", "spacing", 12),
        ("colgap(3)", "spacing", 12),
    ])
    def test_each(self, mode, opt, prop, want):
        _fig, lg, caught = _fig_legend(mode, LINES, opt)
        assert getattr(lg, prop) == want
        assert not [w for w in caught if "legend" in w], caught

    def test_the_measured_sizes(self, mode):
        """U31-7's sizes row: symxsize(5) is a 5-unit line key."""
        ln = TRUTH["sizes"]["key_lines"][0]
        _fig, lg, _ = _fig_legend(
            mode, LINES, "symxsize(5) symysize(2) keygap(1) rowgap(3)")
        assert lg.glyph_width == _px(abs(ln["x2"] - ln["x1"])
                                     / _SVG_PER_UNIT)

    def test_multiplier(self, mode):
        _fig, lg, _ = _fig_legend(mode, LINES, "symxsize(*2)")
        assert lg.glyph_width == 100

    def test_bad_value_noted(self, mode):
        """twoway notes symxsize(bogus) and draws medium (symx_bogus)."""
        assert TRUTH["symx_bogus"]["key_xsize"] == pytest.approx(3.8194)
        _fig, lg, caught = _fig_legend(mode, LINES, "symxsize(bogus)")
        assert lg.glyph_width == _px(3.8194)
        assert any("symxsize(bogus)" in w for w in caught), caught


@pytest.mark.parametrize("mode", MODES)
class TestClockTable:

    @pytest.mark.parametrize("clock", list(range(1, 13)))
    def test_corners_and_sides(self, mode, clock):
        side, end = _side_and_end(TRUTH["clock_%d" % clock])
        fig, lg, _ = _fig_legend(mode, TWO, "pos(%d)" % clock)
        assert _panel_of(fig, lg) == side
        assert lg.location == _EXPECT_LOCATION[(side, end)]

    def test_zero_is_the_centre(self, mode):
        assert _side_and_end(TRUTH["clock_0"]) == ("center", "center")
        fig, lg, _ = _fig_legend(mode, TWO, "pos(0)")
        assert _panel_of(fig, lg) == "center"
        assert lg.location == "center"

    @pytest.mark.parametrize("scheme,rec,loc", [
        ("s2color", "ring0_default", "bottom_center"),
        ("stcolor", "st_ring0", "center_right")])
    def test_ring0_takes_the_scheme_clock(self, mode, scheme, rec, loc):
        assert TRUTH[rec]["box_alignment"] in ("south", "east")
        fig, lg, _ = _fig_legend(mode, TWO, "ring(0)", scheme=scheme)
        assert _panel_of(fig, lg) == "center"
        assert lg.location == loc

    def test_scheme_cols_survive_position(self, mode):
        rec = TRUTH["cols_with_pos"]
        assert len({round(t["y"]) for t in rec["key_texts"]}) == 1
        fig, lg, _ = _fig_legend(mode, TWO, "pos(3)")
        assert _panel_of(fig, lg) == "right"
        assert (lg.ncols, lg.nrows) == (2, 1)

    def test_bplacement(self, mode):
        assert TRUTH["bplacement"]["box_alignment"] == "west"
        fig, lg, _ = _fig_legend(mode, TWO, "pos(6) bplacement(w)")
        assert _panel_of(fig, lg) == "below"
        assert lg.location == "center_left"


class TestRingTags:

    def test_ring_tags_order_the_legend(self):
        """A text box tagged ring=2 sits inside the ring-3 legend, one
        tagged ring=4 outside it (DECISIONS A31)."""
        from bokeh.models import Legend, Title
        from bokeh.plotting import figure
        fig = figure()
        inner = Title(text="in", tags=["dash_textbox", "subtitle", "ring=2"])
        outer = Title(text="out", tags=["dash_textbox", "note", "ring=4"])
        fig.below = list(fig.below) + [inner, outer]
        lg = Legend(items=[])
        fig.add_layout(lg)
        dr._dash_move_legend(fig, lg, "below", "center", 3)
        panel = list(fig.below)
        assert panel.index(inner) < panel.index(lg) < panel.index(outer)


@pytest.mark.parametrize("mode", MODES)
class TestHolesAndGrid:

    def test_holes(self, mode):
        rec = TRUTH["holes"]
        ys = [round(t["y"]) for t in rec["key_texts"]]
        assert ys[0] < ys[1] == ys[2]     # the hole took row 1's column 2
        _fig, lg, _ = _fig_legend(mode, THREE, "holes(2) cols(2)")
        assert len(lg.items) == 4
        hole = lg.items[1]
        assert _text(hole) == "" and list(hole.renderers) == []
        assert (lg.ncols, lg.nrows) == (2, 2)

    def test_a_hole_past_the_end_is_ignored(self, mode):
        assert TRUTH["holes_big"]["keys"] == 3
        _fig, lg, _ = _fig_legend(mode, THREE, "holes(9)")
        assert len(lg.items) == 3

    @pytest.mark.parametrize("opt,want", [("rows(3)", (2, 2)),
                                          ("cols(3)", (3, 2))])
    def test_rows_cols_arithmetic(self, mode, opt, want):
        rec = TRUTH["rows3" if opt.startswith("rows") else "cols3"]
        xs = {round(t["x"]) for t in rec["key_texts"]}
        ys = {round(t["y"]) for t in rec["key_texts"]}
        assert (len(xs), len(ys)) == want
        _fig, lg, _ = _fig_legend(mode, FOUR, opt)
        assert (lg.ncols, lg.nrows) == want

    def test_colfirst_permutes(self, mode):
        rec = TRUTH["colfirst"]
        t = {k["text"]: (round(k["x"]), round(k["y"])) for k in rec["key_texts"]}
        assert t["Mileage (mpg)"][0] == t["Price"][0]   # one column
        _fig, lg, _ = _fig_legend(mode, FOUR, "colfirst cols(2)")
        # Bokeh fills a vertical legend's grid column by column.
        assert lg.orientation == "vertical"
        assert (lg.ncols, lg.nrows) == (2, 2)
        assert [_text(i) for i in lg.items] == ["mpg", "price", "rep",
                                                "foreign"]

    def test_row_first_by_default(self, mode):
        _fig, lg, _ = _fig_legend(mode, FOUR)
        assert lg.orientation == "horizontal"


@pytest.mark.parametrize("mode", MODES)
class TestBoxAndText:

    def test_region(self, mode):
        rec = TRUTH["region"]
        assert rec["outline"]["stroke"] == "#ff0000"
        assert rec["box"]["fill"] == "#e0e0e0"
        _fig, lg, _ = _fig_legend(
            mode, TWO, "region(lcolor(red) fcolor(gs14) lwidth(thick))")
        T = dr.OptionTranslator
        assert lg.border_line_color == "#ff0000"
        assert lg.background_fill_color == "#e0e0e0"
        assert lg.border_line_width == pytest.approx(
            T.line_px(T.resolve_size("thick", "line", 0.0)))

    def test_nobox(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO, "nobox")
        assert lg.border_line_color is None
        assert lg.background_fill_color is None

    def test_region_lcolor_none(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO, "region(lcolor(none))")
        assert lg.border_line_color is None

    def test_color(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO, "color(blue)")
        assert lg.label_text_color == dr.OptionTranslator.parse_color_alpha(
            "blue")[0]

    def test_title(self, mode):
        assert TRUTH["title"]["title_text"] == "Keys"
        _fig, lg, _ = _fig_legend(mode, TWO, 'title("Keys")')
        assert lg.title == "Keys"
        assert lg.title_location == "above"

    def test_textwidth(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO, "textwidth(20)")
        assert lg.label_width == _px(20)

    def test_a_bad_region_value_is_noted(self, mode):
        _fig, lg, caught = _fig_legend(mode, TWO,
                                       "region(lwidth(bogus) fcolor(red))")
        assert lg.background_fill_color == "#ff0000"
        assert any("region(lwidth(bogus))" in w for w in caught), caught

    def test_bmargin_and_region_margin(self, mode):
        _fig, lg, _ = _fig_legend(mode, TWO,
                                  "bmargin(large) region(margin(zero))")
        assert lg.margin == _px(8.0)
        assert lg.padding == 0


@pytest.mark.parametrize("mode", MODES)
class TestNamedAndSilent:

    @pytest.mark.parametrize("word", ["span", "forcesize", "bexpand",
                                      "nospan", "noforcesize", "nobexpand"])
    def test_silent(self, mode, word):
        _fig, _lg, caught = _fig_legend(mode, TWO, word)
        assert not [w for w in caught if "not implemented" in w], caught

    # Flipped (WP-31 D4b): colgap() and subtitle() are drawn
    # (test_legend_remainder.py); the rest stay named (M17).
    @pytest.mark.parametrize("word", ["textfirst", "stacked",
                                      "symplacement(e)", 'note("n")',
                                      'caption("c")'])
    def test_named(self, mode, word):
        _fig, _lg, caught = _fig_legend(mode, TWO, word)
        msgs = [w for w in caught if "not implemented" in w]
        assert any(word in m for m in msgs), caught


@pytest.mark.parametrize("mode", MODES)
class TestLabelBlank:

    def test_blank_or_refused(self, mode):
        """twoway: rc 0, key 1's symbol drawn with no text (label_blank)."""
        _fig, lg, _ = _fig_legend(mode, TWO, "label(1)")
        assert [_text(i) for i in lg.items] == ["", "price"]
        assert list(lg.items[0].renderers)
        assert lg.visible is True


@pytest.mark.parametrize("mode", MODES)
class TestByCellLegend:

    def test_props_copied(self, mode):
        """by()'s one legend is a copy of panel 1's: it takes the new key
        geometry (WP-31 D4)."""
        from bokeh.models import Legend
        import test_by_axes_keys as tbk
        plots = tbk._TWO
        spec = tbk._spec([tbk._graph(
            "g1", plots, {"by": "foreign",
                          "legend": "symxsize(5) keygap(1)"})],
            scheme="s2color")
        roots, _notes, _owner = tbk._build(mode, spec)
        cells = [m for root in roots for m in root.references()
                 if isinstance(m, Legend)
                 and str(m.name or "").endswith("_key") and m.items]
        assert cells, sorted({str(m.name) for root in roots
                              for m in root.references()
                              if isinstance(m, Legend)})
        for lg in cells:
            # Flipped (WP-31 D4b): its two keys in one row are colgap()
            # apart (19 px), not the row gap (5).
            assert (lg.glyph_width, lg.label_standoff, lg.spacing,
                    lg.padding, lg.margin) == (19, 4, 19, 5, 5)


@pytest.mark.parametrize("mode", MODES)
class TestColourKeyUntouched:

    def test_unchanged(self, mode):
        from bokeh.models import Legend
        plots = [plot_for("scatter", {"colorvar": "rep",
                                      "colordiscrete": "yes"},
                          yvar="mpg", xvar="weight"), _sc("price")]

        # Flipped (WP-42 CV-3): the colour key was a Legend; twoway draws
        # swatches beside a z axis, the figure's key cell, which legend()'s
        # options leave as they leave the Legend.
        def cv(legend):
            fig, _ = _build(mode, plots, legend)
            assert not [m for m in fig.select({"type": Legend})
                        if str(m.name or "") == dr._COLORVAR_LEGEND_NAME]
            cell = fig._dash_key_cell
            kc = cell._dash_keycell
            return (cell.width, cell.min_border_left, cell.min_border_right,
                    cell._dash_key_side, cell._dash_key_title.text,
                    list(kc["src"].data["c"]), list(kc["src"].data["y"]),
                    dict(kc["axis"].major_label_overrides or {}),
                    cell.visible, cell.background_fill_color)

        assert cv("") == cv('symxsize(5) keygap(1) rowgap(3) holes(1) '
                            'colfirst nobox title("K") '
                            'region(fcolor(red))')
