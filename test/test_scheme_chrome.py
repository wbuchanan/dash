"""Each scheme's chrome, as twoway draws it (WP-30 P1.2a).

DROPIN-REMAINING.md P1.2: "The title is bold and left-aligned (Stata
centres it and does not bold it).  Axis titles are italic.  Subtitle, note
and caption sit at x=0. ... s2color's vertical y tick labels are missing,
as is stcolor's dashed grid. s1rcolor's ticks are invisible (black on
black), and economist's y axis is wrong."

twoway, measured 03oct2026 (StataNow 19.5 MP; p1.do: ``sysuse auto``, then
for S in s2color stcolor s1rcolor economist ``twoway scatter mpg weight,
title("TTL") subtitle("SUB") note("NTE") caption("CAP") xtitle("XTL")
ytitle("YTL") scheme(S)`` and ``graph export ... .svg``; Stata units are
min(W,H)/100 of the viewBox):

    s2color   TTL/SUB middle, normal | NTE/CAP start (plot region left)
              y labels rot -90 | ticks 1.388 rs #000000 width 0.2 rs outside
    stcolor   TTL/SUB middle | grid #F0F0F0 drawn as 2.0-rs dashes
    s1rcolor  ticks #FFFFFF 1.388 rs; y labels rot -90
    economist TTL/SUB/CAP start | NTE end, in the title's band
              y labels right of the plot, no y ticks; x ticks inside
    econ y2   y2 labels left, y2 ticks 1.388 rs; y1 labels right

Register rulings: P1.2.1 (s2color's y labels go vertical; ``ylabel(,
angle(0))`` is the escape), P1.2.6 (economist's note sits in the title
band), P1.2.7 (the minor ticks are S21's: S15 styles them, never removes
them).  ``test/fixtures/chrome_truth.json`` (scripts/extract_chrome_truth
.do) holds twoway's chrome for all 26 schemes; the table tests compare both
modes with it.
"""

import json
import math
import os
import re
import sys
import warnings

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from bokeh.models import Axis, Label, Legend, Node, Title  # noqa: E402

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import each  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "chrome_truth.json")


# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release


def _spec(scheme, graph_opts=None, plots=None):
    """A one-graph spec of the parity corpus's auto-like frame, a scatter
    layer unless *plots* says otherwise."""
    return tp._spec(plots or [tp._sc()], {"scheme": scheme}, graph_opts or {})


def _user(tmp_path, monkeypatch, name, body):
    """Parse a user scheme ``<name>.scheme`` (``#include s2color`` plus
    *body*) from the working directory, as dash finds one."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / (name + ".scheme")).write_text(
        "#include s2color\n" + body, encoding="utf-8")
    return dr.SchemeParser(name)


def _figs(mode, spec):
    figs, _caught = tp._figures_in(mode, spec)
    return figs


def _fig(mode, spec):
    figs = _figs(mode, spec)
    assert len(figs) == 1, len(figs)
    return figs[0]


def _textboxes(fig):
    """[(kind, side, align_or_anchor, text)] for every side-panel Title
    (not the figure's own title, nor the stale cue) and every Label."""
    out = []
    for side in ("above", "below", "left", "right"):
        for r in getattr(fig, side):
            if isinstance(r, Title) and r is not fig.title \
                    and "dash_stale_cue" not in (r.tags or []):
                out.append(("Title", side, r.align, r.text))
    # WP-45 PIC-4: the in-band note is a Label row of the above panel
    # (BokehJS clips fig.center to the frame).
    for r in list(fig.above) + list(fig.center):
        if isinstance(r, Label):
            out.append(("Label", "center", r.anchor, r.text))
    return out


_FULL = {"title": "TTL", "subtitle": "SUB", "note": "NTE", "caption": "CAP",
         "xtitle": "XTL", "ytitle": "YTL"}


def _y2(scheme, go=None):
    return _spec(scheme, go, [tp._sc(), tp.plot_for(
        "line", yvar="price", xvar="weight", options={"yaxis": "2"})])


def _axis2(fig, name="y2", kw="y_range_name"):
    for side in ("left", "right", "above", "below"):
        for a in getattr(fig, side):
            if isinstance(a, Axis) and getattr(a, kw, None) == name:
                return side, a
    return None, None


def _primary_y(fig):
    for side in ("left", "right"):
        for a in getattr(fig, side):
            if isinstance(a, Axis) and a.y_range_name == "default":
                return side, a
    return None, None


@pytest.mark.parametrize("mode", MODES)
class TestTheTitleIsTheHeadingBox:

    @pytest.mark.parametrize("scheme", ["s2color", "stcolor"])
    def test_the_title_is_centred_and_not_bold(self, mode, scheme):
        f = _fig(mode, _spec(scheme, _FULL))
        assert f.title.align == "center"
        assert f.title.text_font_style == "normal"

    def test_economists_title_is_left_and_not_bold(self, mode):
        f = _fig(mode, _spec("economist", _FULL))
        assert f.title.align == "left"
        assert f.title.text_font_style == "normal"

    def test_a_by_panel_title_is_not_bold_and_centred(self, mode):
        figs = _figs(mode, _spec("s2color", {"by": "foreign"}))
        # Flipped (WP-30 P1.15a): the panel's label is its own row (the
        # Title named dash_by_label), as twoway draws it, not its title.
        from by_panel_probe import panel_label_title
        titled = [panel_label_title(f) for f in figs
                  if panel_label_title(f) is not None]
        assert titled
        for t in titled:
            assert t.text_font_style == "normal", t.text
            assert t.align == "center", t.text

    def test_an_explicit_size_and_colour_still_win(self, mode):
        f = _fig(mode, _spec("s2color",
                             {"title": '"TTL", size(small) color(red)'}))
        assert f.title.text_color in ("#ff0000", "red", "#FF0000")
        assert f.title.text_font_size != dr.SchemeParser(
            "s2color").heading_font_size


@pytest.mark.parametrize("mode", MODES)
class TestAxisTitlesAreUpright:

    def test_x_and_y_titles_are_normal(self, mode):
        f = _fig(mode, _spec("s2color", _FULL))
        for a in list(f.xaxis) + list(f.yaxis):
            assert a.axis_label_text_font_style == "normal"

    def test_second_axis_titles_are_normal(self, mode):
        f = _fig(mode, _spec("s2color", {"ytitle2": "P"}, [
            tp._sc(),
            tp.plot_for("line", yvar="price", xvar="weight",
                        options={"yaxis": "2"}),
            tp.plot_for("line", yvar="mpg", xvar="price",
                        options={"xaxis": "2"})]))
        _s, y2 = _axis2(f)
        _s, x2 = _axis2(f, "x2", "x_range_name")
        assert y2 is not None and x2 is not None
        assert y2.axis_label_text_font_style == "normal"
        assert x2.axis_label_text_font_style == "normal"


@pytest.mark.parametrize("mode", MODES)
class TestTextboxesSitAtTheirClock:

    def test_the_subtitle_is_a_centred_title_above(self, mode):
        f = _fig(mode, _spec("s2color", _FULL))
        assert ("Title", "above", "center", "SUB") in _textboxes(f)

    def test_note_and_caption_are_left_titles_below_note_first(self, mode):
        f = _fig(mode, _spec("s2color", _FULL))
        below = [t for t in _textboxes(f) if t[1] == "below"]
        assert below == [("Title", "below", "left", "NTE"),
                         ("Title", "below", "left", "CAP")]

    # Flipped (WP-45 PIC-4): a Label on Title Nodes in fig.center is never
    # painted by BokehJS (it clips the centre to the frame); a row of the
    # above panel on the canvas's top and the frame's right edge is
    # (test_economist_scheme.py::TestTheNoteIsPainted).
    def test_economists_note_is_in_the_title_band(self, mode):
        f = _fig(mode, _spec("economist", _FULL))
        [lab] = [m for m in f.above if isinstance(m, Label)]
        assert lab.text == "NTE"
        assert not [m for m in f.center if isinstance(m, Label)]
        assert isinstance(lab.x, Node) and isinstance(lab.y, Node)
        assert (lab.x.target, lab.y.target) == ("frame", "canvas")
        assert (lab.x.symbol, lab.y.symbol) == ("right", "top")
        assert lab.anchor == "top_right"
        assert lab.background_fill_color == "#7b92a8"

    def test_economists_subtitle_and_caption_are_left(self, mode):
        f = _fig(mode, _spec("economist", _FULL))
        tb = _textboxes(f)
        assert ("Title", "above", "left", "SUB") in tb
        assert ("Title", "below", "left", "CAP") in tb

    def test_the_legend_stays_nearest_the_plot(self, mode):
        f = _fig(mode, _spec("s2color", {"legend": "position(12)",
                                         "subtitle": "SUB"},
                             [tp._sc(), tp.plot_for("lfit")]))
        kinds = [type(r).__name__ for r in f.above
                 if isinstance(r, (Legend, Title))
                 and "dash_stale_cue" not in (r.tags or [])]
        assert kinds == ["Legend", "Title"], kinds

    def test_the_texts_are_canvas_text_as_typed(self, mode):
        f = _fig(mode, _spec("s2color", {"note": "<script>x</script>",
                                         "caption": "R&D"}))
        texts = [t[3] for t in _textboxes(f)]
        assert "<script>x</script>" in texts and "R&D" in texts


_TINY_PX = 1.3888 * 2.88 * 4.0 / 3.0


@pytest.mark.parametrize("mode", MODES)
class TestTickGeometry:

    def test_ticks_are_the_schemes_length_outside(self, mode):
        f = _fig(mode, _spec("s2color"))
        for a in list(f.xaxis) + list(f.yaxis):
            # Bokeh's tick lengths are whole pixels: 5.33px draws 5.
            assert (a.major_tick_in, a.major_tick_out) == (0, round(_TINY_PX))
            assert a.major_tick_line_color == "#000000"

    def test_economists_x_ticks_point_inward(self, mode):
        f = _fig(mode, _spec("economist"))
        for a in f.xaxis:
            assert (a.major_tick_in, a.major_tick_out) == (round(_TINY_PX), 0)

    def test_s1rcolors_ticks_are_white(self, mode):
        f = _fig(mode, _spec("s1rcolor"))
        for a in list(f.xaxis) + list(f.yaxis):
            assert a.major_tick_line_color == "#ffffff"
            assert a.minor_tick_line_color == "#ffffff"

    def test_the_tick_width_is_linewidth_tick(self, mode):
        s = dr.SchemeParser("s2color")
        f = _fig(mode, _spec("s2color"))
        want = s._lwidth("linewidth tick", s.axis_line_width)
        assert s.tick_line_width == want
        for a in list(f.xaxis) + list(f.yaxis):
            assert a.major_tick_line_width == pytest.approx(want)

    def test_an_xtick_only_position_looks_like_a_major_tick(self, mode):
        f = _fig(mode, _spec("s2color", {"xtick": "2500 3500"}))
        a = f.xaxis[0]
        assert (a.minor_tick_in, a.minor_tick_out) == (
            a.major_tick_in, a.major_tick_out)
        assert a.minor_tick_line_color == a.major_tick_line_color


@pytest.mark.parametrize("mode", MODES)
class TestTickLabelAngle:

    def test_s2colors_y_labels_are_vertical(self, mode):
        f = _fig(mode, _spec("s2color"))
        assert f.yaxis[0].major_label_orientation == pytest.approx(
            math.pi / 2)
        assert f.xaxis[0].major_label_orientation == "horizontal"

    def test_stcolors_y_labels_stay_level(self, mode):
        f = _fig(mode, _spec("stcolor"))
        assert f.yaxis[0].major_label_orientation in ("horizontal", 0, 0.0)

    def test_an_explicit_horizontal_angle_wins(self, mode):
        f = _fig(mode, _spec("s2color", {"ylabel": ", angle(horizontal)"}))
        assert f.yaxis[0].major_label_orientation in ("horizontal", 0, 0.0)


@pytest.mark.parametrize("mode", MODES)
class TestGridPattern:

    def test_stcolors_grid_is_dashed(self, mode):
        f = _fig(mode, _spec("stcolor"))
        assert list(f.ygrid[0].grid_line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))

    def test_s2colors_grid_is_solid(self, mode):
        f = _fig(mode, _spec("s2color"))
        assert list(f.ygrid[0].grid_line_dash) == []

    def test_xlabel_grid_keeps_the_schemes_pattern(self, mode):
        f = _fig(mode, _spec("stcolor", {"xlabel": ", grid"}))
        assert f.xgrid[0].grid_line_color is not None
        assert list(f.xgrid[0].grid_line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))


@pytest.mark.parametrize("mode", MODES)
class TestEconomistAxes:

    def test_the_y_axis_is_right_without_line_or_ticks(self, mode):
        f = _fig(mode, _spec("economist"))
        side, a = _primary_y(f)
        assert side == "right"
        assert a.axis_line_color is None
        assert a.major_tick_line_color is None
        assert (a.major_tick_in, a.major_tick_out) == (0, 0)

    def test_axis_two_is_left_with_line_and_inward_ticks(self, mode):
        f = _fig(mode, _y2("economist"))
        side, a = _axis2(f)
        assert side == "left"
        assert a.axis_line_color is not None
        assert a.major_tick_line_color is not None
        assert (a.major_tick_in, a.major_tick_out) == (round(_TINY_PX), 0)
        assert _primary_y(f)[0] == "right"

    def test_ylabel2_reaches_the_left_axis_two(self, mode):
        f = _fig(mode, _y2("economist", {"ylabel2": "5000 10000 15000"}))
        side, a = _axis2(f)
        assert side == "left"
        assert list(a.ticker.ticks) == [5000.0, 10000.0, 15000.0]

    def test_s2colors_axis_two_stays_right(self, mode):
        f = _fig(mode, _y2("s2color"))
        assert _axis2(f)[0] == "right"
        assert _primary_y(f)[0] == "left"


def _chrome_summary(fig):
    def ax(a):
        return (a.major_label_orientation, a.major_tick_in, a.major_tick_out,
                a.major_tick_line_color, a.axis_line_color,
                a.axis_label_text_font_style)
    return {
        "title": (fig.title.align, fig.title.text_font_style),
        "boxes": _textboxes(fig),
        "axes": {side: [ax(a) for a in getattr(fig, side)
                        if isinstance(a, Axis)]
                 for side in ("left", "right", "above", "below")},
        "grid": [list(g.grid_line_dash) for g in fig.xgrid + fig.ygrid],
    }


class TestChromeAfterAMove:

    @pytest.mark.parametrize("scheme", ["s2color", "economist"])
    def test_the_served_chrome_is_unchanged_after_a_move(self, scheme):
        spec = _spec(scheme, _FULL)
        spec["build_options"]["filter"] = "foreign"
        doc, _ = tp._served(spec)
        from bokeh.plotting import figure as _f
        before = [_chrome_summary(f) for root in doc.roots
                  for f in root.select({"type": _f})]
        widgets = [w for w in tp._widgets_of(doc)
                   if type(w).__name__ == "Select"]
        assert widgets
        w = widgets[0]
        tp._fire(w, w.options[-1][0] if isinstance(w.options[-1], tuple)
                 else w.options[-1])
        after = [_chrome_summary(f) for root in doc.roots
                 for f in root.select({"type": _f})]
        assert before and before == after

    def test_no_saved_script_writes_chrome(self):
        from bokeh.models import CustomJS
        r, _c, _page = tp._standalone_page(_spec("s2color", _FULL))
        codes = [m.code for f in r.figures.values()
                 for m in f.document.models if isinstance(m, CustomJS)] \
            if all(getattr(f, "document", None) for f in r.figures.values()) \
            else []
        codes.append(getattr(dr, "_FILTER_JS", ""))
        for code in codes:
            for prop in ("text_font_style", "major_tick_",
                         "major_label_orientation", "grid_line_dash",
                         "axis_line_color", ".align"):
                # A write, not a read: the export's canvas code reads its
                # own items' `.align` (it.align === ...), which is no
                # chrome write.  Flipped: WP-32 D-53d draws table text.
                assert not re.search(re.escape(prop) + r"\w*\s*=(?!=)",
                                     code), prop


class TestTheChromeKeysAreRead:

    def test_s2color_stcolor_s1rcolor_economist_values(self):
        s2 = dr.SchemeParser("s2color")
        assert (s2.tick_angle_x, s2.tick_angle_y) == (0.0, 90.0)
        assert s2.major_grid_dash == [] and s2.tick_color == "#000000"
        assert s2.tick_position == "outside"
        assert s2.text_clock == {"title": 12, "subtitle": 12, "note": 7,
                                 "caption": 7}
        assert set(s2.text_just.values()) == {"center"}
        st = dr.SchemeParser("stcolor")
        assert st.major_grid_dash == dr.OptionTranslator.translate_lpattern(
            "dash")
        assert st.tick_angle_y == 0.0
        s1r = dr.SchemeParser("s1rcolor")
        assert s1r.tick_color == "#ffffff" and s1r.minortick_color == "#ffffff"
        ec = dr.SchemeParser("economist")
        assert ec.tick_position == "inside" and ec.alt_yaxes is True
        assert ec.axis_styles[("y", 1)] == "vertical_nolinetick"
        assert ec.text_clock["note"] == 1 and ec.text_clock["title"] == 11
        assert ec.text_just["heading"] == "left"

    def test_the_tick_length_is_gsize_tick_in_stata_units(self, tmp_path,
                                                          monkeypatch):
        assert dr.SchemeParser("s2color").tick_length_px == pytest.approx(
            _TINY_PX, abs=0.01)
        s = _user(tmp_path, monkeypatch, "tsmall", "gsize tick small\n")
        assert s.tick_length_px == pytest.approx(2.7777 * 2.88 * 4 / 3,
                                                 abs=0.01)

    def test_the_minor_tick_keys_are_read(self):
        """WP-31 D1: every shipped scheme carries the minor-tick stubs the
        generator writes -- `gsize minortick' and `gsize tickgap'
        (half_tiny, half a tick) and `numticks_g horizontal_minor' and
        `vertical_minor' (0: no minor tick unless asked) -- and the parser
        reads them."""
        import glob
        files = sorted(glob.glob(os.path.join(os.path.dirname(dr.__file__),
                                              "dash-*.scheme")))
        assert len(files) == 26
        for f in files:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
            for key in ("gsize minortick", "gsize tickgap",
                        "numticks_g horizontal_minor",
                        "numticks_g vertical_minor"):
                assert re.search(r"^" + key + r"\s", text, re.M), (f, key)
        s2 = dr.SchemeParser("s2color")
        assert s2.minortick_length_px == pytest.approx(_TINY_PX / 2.0,
                                                       abs=0.01)
        assert s2.tickgap_px == pytest.approx(_TINY_PX / 2.0, abs=0.01)
        assert s2.numticks_minor == {"x": 0, "y": 0}

    def test_axisstyle_names_map_to_line_and_tick_flags(self):
        f = dr.SchemeParser._AXISSTYLE_FLAGS
        assert len(f) == 12
        for d in ("horizontal", "vertical"):
            assert f[f"{d}_default"] == (True, True)
            assert f[f"{d}_nogrid"] == (True, True)
            assert f[f"{d}_withgrid"] == (True, True)
            assert f[f"{d}_noline"] == (False, True)
            assert f[f"{d}_notick"] == (True, False)
            assert f[f"{d}_nolinetick"] == (False, False)
        assert dr.SchemeParser("economist").axis_flags("y") == (False, False)
        assert dr.SchemeParser("economist").axis_flags("y", 2) == (True, True)

    def test_axis_side_reads_the_alt_keys(self):
        s2 = dr.SchemeParser("s2color")
        assert [s2.axis_side(w, n) for w in "xy" for n in (1, 2)] == [
            "below", "above", "left", "right"]
        ec = dr.SchemeParser("economist")
        assert [ec.axis_side(w, n) for w in "xy" for n in (1, 2)] == [
            "below", "above", "right", "left"]

    def test_the_bar_and_area_intensity_chains_follow_statas_order(
            self, tmp_path, monkeypatch):
        s = _user(tmp_path, monkeypatch, "tint",
                  "intensity p2bar inten40\nintensity parea inten30\n")
        assert s.p_bar_intensity[0:2] == pytest.approx([0.8, 0.4])
        assert s.p_area_intensity == pytest.approx([0.3] * 15)

    def test_naturally_white(self):
        assert dr.SchemeParser("s2color").naturally_white is True
        assert dr.SchemeParser("s1rcolor").naturally_white is False


_HOSTILE = [
    ("anglestyle vertical_tick Vertical", "tick_angle_y", 0.0),
    ("tickposition axis_tick <script>", "tick_position", "outside"),
    ("axisstyle vertical_default ../../etc/passwd", "axis_styles",
     None),
    ("horizontal heading " + "x" * 5000, "text_just", None),
    ("clockdir note_position 99", "text_clock", None),
    ("system naturally_white 7", "naturally_white", True),
]


class TestHostileChromeKeys:

    @pytest.mark.parametrize("line,attr,want", _HOSTILE,
                             ids=[h[1] for h in _HOSTILE])
    def test_an_unknown_name_falls_back_once(self, tmp_path, monkeypatch,
                                             line, attr, want):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            s = _user(tmp_path, monkeypatch, "hostile", line + "\n")
        notes = [str(w.message) for w in caught]
        assert len(notes) == 1, notes
        assert "<script>" not in notes[0] and len(notes[0]) <= 400
        got = getattr(s, attr)
        if attr == "axis_styles":
            assert got[("y", 1)] == "vertical_default"
        elif attr == "text_just":
            assert got["heading"] == "center"
        elif attr == "text_clock":
            assert got["note"] == 7
        else:
            assert got == want

    @pytest.mark.parametrize("raw", ["1e308", "-5", "nan"])
    def test_an_absurd_tick_length_is_bounded(self, tmp_path, monkeypatch,
                                              raw):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            s = _user(tmp_path, monkeypatch, "tlen", "gsize tick " + raw + "\n")
        assert 0 <= s.tick_length_px <= 100
        assert s.tick_length_px == pytest.approx(4 * 4 / 3)
        assert len([w for w in caught if "tick" in str(w.message)]) == 1


_PLACE = {
    11: ("above", "left"), 10: ("above", "left"),
    12: ("above", None), 0: ("above", None),
    1: ("above", "right"), 2: ("above", "right"),
    3: ("below", "right"), 4: ("below", "right"), 5: ("below", "right"),
    6: ("below", None),
    7: ("below", "left"), 8: ("below", "left"), 9: ("below", "left"),
}


class TestTextboxPlace:

    def test_every_clock(self):
        for clock, (side, align) in _PLACE.items():
            for just in ("left", "center", "right"):
                assert dr._dash_textbox_place(clock, just) == (
                    side, align or just), (clock, just)

    def test_junk_is_the_default(self):
        for clock in (None, "12", 13, -1, True, 3.5):
            assert dr._dash_textbox_place(clock, "left") == (
                "above", "center"), clock
        assert dr._dash_textbox_place(12, "x") == ("above", "center")


# ---------------------------------------------------------------------------
# twoway's chrome for every shipped scheme (test/fixtures/chrome_truth.json,
# scripts/extract_chrome_truth.do), against both modes
# ---------------------------------------------------------------------------

def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


_PROBES = ("economist_y2", "s2color_y2", "s2color_yh", "stcolor_xgrid",
           "s2color_xgrid")
_PX_PER_RS = 2.88 * 4.0 / 3.0


def _tick_view(t):
    if not t or not t.get("n"):
        return {"drawn": False}
    return {"drawn": True, "position": t["position"],
            "length_px": int(round(t["length_rs"] * _PX_PER_RS)),
            "color": t["color"]}


def _twoway_view(rec):
    """twoway's record in the comparison vocabulary."""
    v = {"texts": {k: (t["side"], t["align"],
                       "normal" if t["weight"] == "normal"
                       and t["style"] == "normal" else "styled")
                   for k, t in rec["texts"].items()
                   if k in ("TTL", "SUB", "NTE", "CAP")},
         "label_rotation": {k: rec["label_rotation"][k]
                            for k in ("y", "y2") if k in rec["label_rotation"]},
         "label_side": dict(rec["label_side"]),
         "ticks": {k: _tick_view(t) for k, t in rec["ticks"].items()},
         "axis_line": dict(rec["axis_line"]),
         "grid": {k: (g["drawn"], g["dashed"] if g["drawn"] else None)
                  for k, g in rec["grid"].items()}}
    return v


def _dash_axis_tick(a):
    if a.major_tick_line_color is None or (a.major_tick_in, a.major_tick_out) \
            == (0, 0):
        return {"drawn": False}
    if a.major_tick_in and a.major_tick_out:
        pos, length = "crossing", a.major_tick_in + a.major_tick_out
    elif a.major_tick_in:
        pos, length = "inside", a.major_tick_in
    else:
        pos, length = "outside", a.major_tick_out
    return {"drawn": True, "position": pos, "length_px": length,
            "color": str(a.major_tick_line_color).lower()}


def _dash_view(fig, texts_given):
    """dash's figure in the same vocabulary."""
    v = {"texts": {}, "label_rotation": {}, "label_side": {}, "ticks": {},
         "axis_line": {}, "grid": {}}
    if "TTL" in texts_given:
        v["texts"]["TTL"] = (fig.title_location or "above", fig.title.align,
                             fig.title.text_font_style)
    for kind, side, align, text in _textboxes(fig):
        if text in ("SUB", "NTE", "CAP"):
            if kind == "Label":
                side, align = "above", align.split("_")[-1]
                style = "normal"
            else:
                style = next(r.text_font_style for r in getattr(fig, side)
                             if isinstance(r, Title) and r.text == text)
            v["texts"][text] = (side, align, style)
    for role, (side, a) in (("y", _primary_y(fig)), ("y2", _axis2(fig))):
        if a is None:
            continue
        o = a.major_label_orientation
        v["label_rotation"][role] = 0 if o in ("horizontal", 0) else \
            round(math.degrees(o)) % 360
        v["label_side"][role] = side
        v["ticks"][role] = _dash_axis_tick(a)
        v["axis_line"][role] = a.axis_line_color is not None
    xa = [a for a in fig.below if isinstance(a, Axis)]
    v["ticks"]["x"] = _dash_axis_tick(xa[0])
    v["axis_line"]["x"] = xa[0].axis_line_color is not None
    for k, grids in (("x", fig.xgrid), ("y", fig.ygrid)):
        g = grids[0]
        drawn = g.grid_line_color is not None
        v["grid"][k] = (drawn, bool(list(g.grid_line_dash)) if drawn else None)
    return v


def _probe_spec(name):
    if name.endswith("_y2"):
        return _y2(name[:-3], {"title": "TTL"}), {"TTL"}
    if name == "s2color_yh":
        return _spec("s2color", {"ylabel": ", angle(horizontal)"}), set()
    if name.endswith("_xgrid"):
        return _spec(name[:-6], {"xlabel": ", grid"}), set()
    return _spec(name, _FULL), {"TTL", "SUB", "NTE", "CAP"}


class TestEveryShippedSchemeDrawsItsChrome:

    def test_the_fixture_is_stamped_and_complete(self):
        d = _truth()
        assert set(d) - {"_meta"} == set(dr.SchemeParser._BUILTIN_NAMES) \
            | set(_PROBES)
        assert {"stata_version", "born_date", "dash_commit",
                "extracted"} <= set(d["_meta"])

    @pytest.mark.parametrize("mode", MODES)
    @each("name", sorted(dr.SchemeParser._BUILTIN_NAMES))
    def test_matches_twoway(self, name, mode):
        spec, given = _probe_spec(name)
        want = _twoway_view(_truth()[name])
        got = _dash_view(_fig(mode, spec), given)
        assert got == want

    @pytest.mark.parametrize("mode", MODES)
    @each("name", _PROBES)
    def test_the_extra_probes(self, name, mode):
        spec, given = _probe_spec(name)
        want = _twoway_view(_truth()[name])
        got = _dash_view(_fig(mode, spec), given)
        assert got == want
