"""dash.sthlp, Region Styling to Marker and Transparency Options, claim by claim.

ROADMAP WP-23 (AC-23.1, AC-23.2), GAPS.md F4.  The sections of dash.sthlp
headed Region Styling Options, Axis and Display Options, Mapping a Variable
to Colour, Figure proportions and Marker and Transparency Options make
claims about what the saved page (DashRenderer) and the served app
(ServerAppBuilder + make_document) draw.  Every claim below was measured in
both render modes, 23sep2026; where the code did not do what the help said
and could be made to in a contained change, the code was fixed and the test
was written first.  The Stata side of the same claims -- what dash.ado
accepts, refuses and names in its note, measured against twoway in the same
run -- is certified by test/test_help_claims_7.cscript.

What twoway draws, where a claim is about twoway, was measured with the
console binary and SVG exports (the WP-23 work notes hold the probes):

* ``msangle(90)`` exports as ``transform="rotate(-90.00 ...)"``: SVG's y axis
  points down, so twoway turns a marker COUNTER-clockwise.
* ``color(red)`` on ``rarea`` fills the band #FF3333 and strokes it #FF0000;
  on ``rbar`` the same; on ``lfitci`` the confidence band is filled #FF0000
  and the fit line stroked #FF0000.
* ``jitter()`` moves the markers of scatter, connected, rconnected, dot,
  dropline, scatteri, rscatter, rcapsym, pcscatter and pccapsym, and never a
  line, a spike, a cap, a bar or an area.
* ``legend(top)``, ``legend(bottom)``, ``legend(left)`` and
  ``legend(right)`` are refused, "option top not allowed", r(198).
"""
import json
import math
import os
import re
import sys

import pytest
from bokeh.models import (BasicTicker, ColorBar, CustomJSTickFormatter,
                          FixedTicker, Grid,
                          HoverTool, Legend, LinearAxis, LogAxis,
                          NumeralTickFormatter, Range1d)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_MODES = ("saved", "served")
_TYPES = sorted(dr._dash_plot_type_names())

#: The plot types whose SERVED half a per-type sweep keeps (WP-30 test
#: performance E), one per family: point, line, area/range, bar,
#: fit/smooth, pc.  The saved half keeps every type.  The served app draws
#: through the same GlyphMapper text (copied by inspect.getsource), and
#: test_mode_parity's corpus compares every dispatched type in both modes;
#: TestTheSecondAxisFitsTheLayer keeps both halves whole.
_SERVED_TYPES = ("scatter", "line", "rarea", "bar", "lfitci", "pccapsym")


def _types_by_mode(types, served=_SERVED_TYPES):
    """``(ptype, mode)`` parameters: every type saved, and the types in
    *served* served too; the ids are the ones the two stacked decorators
    gave (``scatter-saved``)."""
    return ([pytest.param(t, "saved", id=f"{t}-saved") for t in types]
            + [pytest.param(t, "served", id=f"{t}-served")
               for t in types if t in served])


# ---------------------------------------------------------------------------
# Rendering in one mode or the other
# ---------------------------------------------------------------------------

def _figures(model):
    return list(model.select({"type": figure})) if model is not None else []


_RENDERED = {}


def _render(mode, plots, go=None, bo=None):
    """``(figure, warnings)`` for a one-graph spec, in *mode*.

    Memoised per process on the spec's text: the per-type classes render
    the same unoptioned layer again and again as their baseline, and every
    caller only reads what comes back.
    """
    key = (mode, json.dumps(plots, sort_keys=True),
           json.dumps(go, sort_keys=True), json.dumps(bo, sort_keys=True))
    if key not in _RENDERED:
        _RENDERED[key] = _render_uncached(mode, plots, go, bo)
    return _RENDERED[key]


def _render_uncached(mode, plots, go=None, bo=None):
    spec = tp._spec(plots, bo, go)
    if mode == "saved":
        r, caught = tp._standalone(spec)
        figs = _figures(getattr(r, "_last_layout_root", None))
    else:
        doc, caught = tp._served(spec)
        figs = [f for root in doc.roots for f in _figures(root)]
    assert figs, f"no figure was drawn in the {mode} mode"
    return figs[0], caught


def _glyphs(fig):
    """The glyph renderers a layer drew -- not a colour key's swatches,
    and not dot's rows of dots, which are drawn in markerstyle dots and
    which no marker or colour option reaches (WP-31 B5b; twoway's
    color(), mcolor(), msymbol(), pstyle() and mstyle() leave them black:
    test/fixtures/dot_truth.json D23-D26)."""
    return [r for r in fig.renderers
            if getattr(r, "glyph", None) is not None
            and not dr._dash_is_swatch(r)
            and "dash_dots" not in (getattr(r, "tags", None) or ())]


def _is_cap(r):
    """A range cap: a "dash" marker drawn as a line (map_rcap, tagged
    dash_cap), which twoway draws in the line style -- no marker option
    turns, reshapes or fades it, and its fill is never drawn (WP-31 B1:
    rpcap's caps beside its marker)."""
    return "dash_cap" in (getattr(r, "tags", None) or ())


def _field(glyph, attr):
    v = getattr(glyph, attr, None)
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get("field")
    return getattr(v, "field", None)


def _rows(r):
    """The row indices a renderer draws through its view."""
    src = r.data_source
    first = next(iter(src.data), None)
    n = len(src.data[first]) if first else 0
    filt = getattr(getattr(r, "view", None), "filter", None)
    idx = getattr(filt, "indices", None) if filt is not None else None
    if idx is None and filt is not None:
        bools = getattr(filt, "booleans", None)
        if bools is not None:
            idx = [i for i, b in enumerate(list(bools)[:n]) if b]
    return list(range(n)) if idx is None else [i for i in idx if 0 <= i < n]


_Y_FIELDS = ("y", "y0", "y1", "y2", "top", "bottom")
_X_FIELDS = ("x", "x0", "x1", "left", "right")


def _constant(glyph, attr):
    """A coordinate given as a number rather than a column (a bar's
    bottom=0), or None."""
    v = getattr(glyph, attr, None)
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict) and isinstance(v.get("value"), (int, float)):
        return float(v["value"])
    val = getattr(v, "value", None)
    return float(val) if isinstance(val, (int, float)) else None


def _drawn_extent(fig, which):
    """(min, max) of every coordinate the layers on the secondary *which*
    ("y2" or "x2") range draw, through their views."""
    attr, fields = (("y_range_name", _Y_FIELDS) if which == "y2"
                    else ("x_range_name", _X_FIELDS))
    vals = []
    for r in _glyphs(fig):
        if getattr(r, attr, "default") != which:
            continue
        rows = _rows(r)
        for f in fields:
            if not hasattr(r.glyph, f):
                continue
            name = _field(r.glyph, f)
            if not name:
                c = _constant(r.glyph, f)
                if c is not None and math.isfinite(c) and rows:
                    vals.append(c)
                continue
            if name not in r.data_source.data:
                continue
            col = list(r.data_source.data[name])
            for i in rows:
                try:
                    v = float(col[i])
                except (TypeError, ValueError, IndexError):
                    continue
                if math.isfinite(v):
                    vals.append(v)
    return (min(vals), max(vals)) if vals else (None, None)


def _axis2(fig, which):
    if which == "y2":
        return [a for a in fig.right if isinstance(a, (LinearAxis, LogAxis))
                and a.y_range_name == "y2"][0]
    return [a for a in fig.above if isinstance(a, (LinearAxis, LogAxis))
            and a.x_range_name == "x2"][0]


# ===========================================================================
# 1. Region Styling Options
# ===========================================================================

#: (option, value, figure attribute, expected).  Every region option in
#: every colour notation the help names: a Stata colour name, an RGB
#: triplet in quotes, and a hex string.  dash.ado keeps the quotes inside
#: plotregion() and graphregion(), which are declared `string asis'
#: (test_help_claims_7.cscript HC7-04), and a colour read with its quotes
#: was an unknown colour: plotregion(color("255 0 0")) drew the scheme's
#: white and said "not a recognised colour".
_REGION = [
    ("plotregion", "color(navy)", "background_fill_color", "#1a476f"),
    ("plotregion", 'color("255 0 0")', "background_fill_color", "#ff0000"),
    ("plotregion", "color(#1a476f)", "background_fill_color", "#1a476f"),
    ("plotregion", "fcolor(navy)", "background_fill_color", "#1a476f"),
    ("plotregion", "lcolor(maroon)", "outline_line_color", "#90353b"),
    ("plotregion", 'lcolor("255 0 0")', "outline_line_color", "#ff0000"),
    ("plotregion", "lcolor(#ff0000)", "outline_line_color", "#ff0000"),
    # Flipped (WP-30 P1.12b): 2 Stata units x 3.84 px (was 2 px).
    ("plotregion", "lwidth(2)", "outline_line_width", 7.68),
    ("plotregion", "lwidth(thick)", "outline_line_width",
     dr.OptionTranslator.translate_lwidth("thick")),
    ("graphregion", "color(forest_green)", "border_fill_color", "#55752f"),
    ("graphregion", 'color("255 0 0")', "border_fill_color", "#ff0000"),
    ("graphregion", "color(#1a476f)", "border_fill_color", "#1a476f"),
    ("graphregion", "fcolor(navy)", "border_fill_color", "#1a476f"),
    ("graphregion", 'fcolor("0 0 255")', "border_fill_color", "#0000ff"),
    # Flipped (WP-30 P1.20a): bgcolor() setting the border was wrong
    # because twoway paints bgcolor() under the graph region (region_truth.json D26-D29); alone it leaves the scheme's
    # graph region (test_region_truth.py carries the canvas cases).
    ("bgcolor", "navy", "border_fill_color",
     dr.SchemeParser("s2color").background_color),
    ("bgcolor", "255 0 0", "border_fill_color",
     dr.SchemeParser("s2color").background_color),
    ("bgcolor", "#1a476f", "border_fill_color",
     dr.SchemeParser("s2color").background_color),
    ("plotbgcolor", "maroon", "background_fill_color", "#90353b"),
    ("plotbgcolor", "255 0 0", "background_fill_color", "#ff0000"),
    ("plotbgcolor", "#ff0000", "background_fill_color", "#ff0000"),
]


#: The rows whose SERVED half TestRegionColours keeps (WP-30 test
#: performance E): each option, each colour notation and a width once.  The
#: saved half keeps every row; both modes read the options through the same
#: reader, _dash_apply_regions (WP-30 P1.20a).
_REGION_SERVED = ("plotregion(color(navy))", 'plotregion(lcolor("255 0 0"))',
                  "plotregion(lwidth(thick))", "graphregion(color(#1a476f))",
                  "bgcolor(255 0 0)", "plotbgcolor(maroon)")


def _region_by_mode():
    """``(opt, value, attr, want, mode)``: every row saved, the
    ``_REGION_SERVED`` rows served, with the ids the stacked decorators
    gave."""
    out = []
    for mode in _MODES:
        for o, v, a, w in _REGION:
            rid = f"{o}({v})"
            if mode == "saved" or rid in _REGION_SERVED:
                out.append(pytest.param(o, v, a, w, mode, id=f"{rid}-{mode}"))
    return out


class TestRegionColours:
    """dash.sthlp, Region Styling Options: each option sets the Bokeh
    property the help names, from a colour in each notation it names."""

    @pytest.mark.parametrize("opt,value,attr,want,mode", _region_by_mode())
    def test_the_option_sets_the_property(self, mode, opt, value, attr, want):
        fig, caught = _render(mode, [plot_for("scatter")], {opt: value})
        got = getattr(fig, attr)
        if isinstance(want, float):
            assert got == pytest.approx(want), (opt, value, got)
        else:
            assert str(got).lower() == want, (
                f"{opt}({value}) left {attr} at {got!r} in the {mode} mode, "
                f"not {want!r}; notes: {caught}")
        assert not [w for w in caught if "colour" in w or "color" in w], (
            f"{opt}({value}) was reported as an unknown colour: {caught}")

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_unknown_colour_is_named_and_drawn_black(self, mode):
        """Flipped (WP-30 P1.13a): twoway draws an unknown region colour
        black (colour_grammar_truth.json site_08); this kept the scheme's."""
        fig, caught = _render(mode, [plot_for("scatter")],
                              {"plotregion": "color(notacolour)"})
        assert fig.background_fill_color == "#000000"
        assert any("notacolour" in w for w in caught), caught


# ===========================================================================
# 2. Secondary axes: ylabel2() and xlabel2() take ylabel()'s grammar
# ===========================================================================

_Y2 = [plot_for("line"), plot_for("line", {"yaxis": "2"}, yvar="price")]
_X2 = [plot_for("line"), plot_for("line", {"xaxis": "2"}, xvar="price")]


def _ticker_profile(axis, text=""):
    """What an axis label option set on *axis*: the ticker, and the format,
    size and angle when *text* asks for them (the two axes' untouched
    defaults are the scheme's, which is not what is compared here)."""
    t = axis.ticker
    out = {"type": type(t).__name__}
    if isinstance(t, FixedTicker):
        out["ticks"] = [float(v) for v in t.ticks]
    if isinstance(t, BasicTicker):
        out["desired"] = t.desired_num_ticks
    if "format" in text:
        fmt = axis.formatter
        # GAPS2 E3/G6, WP-28 S12: format() is a CustomJSTickFormatter
        # carrying the Stata format in args["fmt"].
        out["format"] = (fmt.args.get("fmt")
                         if isinstance(fmt, CustomJSTickFormatter)
                         else type(fmt).__name__)
    if "labsize" in text:
        out["labsize"] = axis.major_label_text_font_size
    if "angle" in text:
        out["angle"] = axis.major_label_orientation
    return out


#: The label forms dash.sthlp documents for xlabel()/ylabel(), each of which
#: GAPS.md F4 measured giving the secondary axis nothing at all.
_GRAMMAR = ["#5", "4000(2000)12000", "4000 8000 12000", "none",
            "4000 8000, format(%9.2f)", "#4, labsize(large)",
            "4000 8000, angle(45)"]


class TestSecondaryAxisLabelGrammar:
    """dash.sthlp, Secondary axes: ylabel2() and xlabel2() take the grammar
    xlabel() and ylabel() take.  They read a bare numlist and nothing else:
    #5, 10(5)40, minmax, none, format(), labsize() and grid all left the
    second axis at its default ticks without a word."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("text", _GRAMMAR)
    def test_ylabel2_reads_what_ylabel_reads(self, mode, text):
        prim, _ = _render(mode, [plot_for("line", yvar="price")],
                          {"ylabel": text})
        sec, caught = _render(mode, _Y2, {"ylabel2": text})
        want = _ticker_profile(prim.yaxis[0], text)
        got = _ticker_profile(_axis2(sec, "y2"), text)
        assert got == want, (
            f"ylabel2({text}) drew {got} on the right-hand axis where "
            f"ylabel({text}) draws {want} ({mode}); notes: {caught}")

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("text", _GRAMMAR)
    def test_xlabel2_reads_what_xlabel_reads(self, mode, text):
        prim, _ = _render(mode, [plot_for("line", xvar="price")],
                          {"xlabel": text})
        sec, caught = _render(mode, _X2, {"xlabel2": text})
        want = _ticker_profile(prim.xaxis[0], text)
        got = _ticker_profile(_axis2(sec, "x2"), text)
        assert got == want, (
            f"xlabel2({text}) drew {got} on the top axis where "
            f"xlabel({text}) draws {want} ({mode}); notes: {caught}")

    @pytest.mark.parametrize("mode", _MODES)
    def test_minmax_labels_the_extremes_of_the_second_axis_data(self, mode):
        fig, _ = _render(mode, _Y2, {"ylabel2": "minmax"})
        prices = tp._DF["price"]
        assert _ticker_profile(_axis2(fig, "y2"))["ticks"] == [
            float(prices.min()), float(prices.max())]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("which,opt,plots", [("y2", "ylabel2", _Y2),
                                                 ("x2", "xlabel2", _X2)])
    def test_grid_draws_gridlines_at_the_second_axis_ticks(self, mode, which,
                                                          opt, plots):
        def grids(fig):
            ax = _axis2(fig, which)
            return [g for g in fig.center if isinstance(g, Grid)
                    and g.axis is ax and g.grid_line_color is not None]
        on, _ = _render(mode, plots, {opt: "4000 8000, grid"})
        off, _ = _render(mode, plots, {opt: "4000 8000"})
        assert grids(on), f"{opt}(, grid) drew no gridlines ({mode})"
        assert not grids(off), f"{opt}() without grid drew gridlines ({mode})"

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_suboption_it_does_not_honour_is_named(self, mode):
        # Flipped (WP-30 P1.18a): labcolor() is drawn; labgap() is not.
        _, caught = _render(mode, _Y2, {"ylabel2": "4000 8000, labgap(2)"})
        assert any("ylabel2() sub-option" in w and "labgap(2)" in w
                   for w in caught), caught

    @pytest.mark.parametrize("mode", _MODES)
    def test_value_label_pairs_still_label_the_ticks(self, mode):
        fig, _ = _render(mode, _Y2, {"ylabel2": '5000 "Low" 10000 "High"'})
        ax = _axis2(fig, "y2")
        assert _ticker_profile(ax)["ticks"] == [5000.0, 10000.0]
        assert "Low" in str(ax.formatter.args) and "High" in str(
            ax.formatter.args)


# ===========================================================================
# 3. yaxis(2) and xaxis(2): the second axis is scaled to that layer's data
# ===========================================================================

#: Every plot type whose data do not sit under the plot's yvar/xvar keys.
#: _compute_secondary_range read only those keys, so each of these drew on
#: a secondary range of 0 to 1 -- off the axis, in both modes.
_OFF_KEY_TYPES = sorted(dr._DASH_RANGE_TYPES | dr._DASH_PC_TYPES
                        | {"histogram", "kdensity", "function", "scatteri",
                           "pci", "pcarrowi"})


def _y2_layer(ptype, axis):
    extra, opts = {}, {axis: "2"}
    if ptype == "function":
        extra["expr"] = "50 + x"
    if ptype in ("lpoly", "lpolyci"):
        # Ten observations: the rule-of-thumb bandwidth leaves every grid
        # point without a neighbour, and lpoly draws nothing on either axis
        # (and says so).  A wide bandwidth draws the curve.
        opts["bwidth"] = "1500"
    return plot_for(ptype, opts, **extra)


class TestTheSecondAxisFitsTheLayer:
    """dash.sthlp, Secondary axes: "yaxis(2) on any plot layer ... a
    right-hand y axis scaled to that layer's own data"."""

    # WP-30 P1.3a: "no more than 1.25 x the drawn extent" was wrong
    # because the second axis is now ticked as twoway ticks it (natscale)
    # and spans the hull of its layer's data and those ticks, padded by
    # twoway's margin; a default bar/area/spike/dropline base is no part
    # of twoway's scale (P1.3.7).
    @staticmethod
    def _check(fig, name, ptype, mode):
        letter = name[0]
        rng = getattr(fig, "extra_%s_ranges" % letter)[name]
        ext = dr._dash_layer_extent(fig.renderers, letter + "_range_name",
                                    name)
        assert ext is not None, f"{ptype} drew nothing on {name} ({mode})"
        ax = [a for a in getattr(fig, "right" if letter == "y" else "above")
              + getattr(fig, "left" if letter == "y" else "below")
              if getattr(a, letter + "_range_name", "") == name][0]
        ticks = list(getattr(ax.ticker, "ticks", None) or [])
        lo, hi = min([ext[0]] + ticks), max([ext[1]] + ticks)
        got = dr._dash_range_hull(rng)
        # A bar is one x unit wide: its outer half-width is in the hull.
        half = 0.5 if letter == "x" and ptype in ("bar", "rbar") else 0.0
        lo, hi = lo - half, hi + half
        assert got == pytest.approx((lo, hi), rel=1e-9, abs=1e-9), (
            f"{ptype} on {name}: hull {got} of data {ext} and ticks {ticks} "
            f"({mode})")

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", _TYPES)
    def test_the_right_hand_axis_spans_the_layer(self, mode, ptype):
        fig, _ = _render(mode, [plot_for("line"), _y2_layer(ptype, "yaxis")])
        self._check(fig, "y2", ptype, mode)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", _TYPES)
    def test_the_top_axis_spans_the_layer(self, mode, ptype):
        fig, _ = _render(mode, [plot_for("line"), _y2_layer(ptype, "xaxis")])
        self._check(fig, "x2", ptype, mode)


# ===========================================================================
# 4. colorvar(): where it is drawn
# ===========================================================================

#: The plot types that colour their observations by colorvar().
#: Flipped (WP-31 C8a): every type twoway colours
#: (test/fixtures/colorvar_types_truth.json "coloured"); the four that
#: drew their markers through map_scatter were the old list.  On the types
#: twoway drops it on, dash.ado drops it too (test_help_claims_7.cscript
#: HC7-02), so a spec carrying it there draws nothing for it.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "colorvar_types_truth.json"),
          encoding="utf-8") as _cvt:
    _CV_TYPES = set(json.load(_cvt)["coloured"])
#: The coloured types drawn with Bokeh's Line glyph alone: one colour a
#: line, its first point's level (D-15f), so no glyph reads a field.
_CV_LINE_TYPES = {"line", "tsline", "rline", "tsrline"}


def _colour_mapped(fig):
    out = {"field": False, "bar": False, "key": False}
    for r in _glyphs(fig):
        for attr in ("fill_color", "line_color"):
            v = getattr(r.glyph, attr, None)
            if (isinstance(v, dict) and v.get("transform") is not None) or \
                    getattr(v, "transform", None) is not None:
                out["field"] = True
    for side in ("right", "left", "above", "below", "center"):
        for m in getattr(fig, side):
            if isinstance(m, ColorBar):
                out["bar"] = True
            if isinstance(m, Legend) and \
                    str(m.name or "") == dr._COLORVAR_LEGEND_NAME:
                out["key"] = True
    return out


class TestWhereColorvarIsDrawn:

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_a_continuous_colorvar(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"colorvar": "price"})])
        got = _colour_mapped(fig)
        if ptype in _CV_TYPES:
            assert got == {"field": ptype not in _CV_LINE_TYPES, "bar": True,
                           "key": False}, got
        else:
            assert got == {"field": False, "bar": False, "key": False}, got

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_a_discrete_colorvar(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"colorvar": "foreign",
                                                 "colordiscrete": "1"})])
        got = _colour_mapped(fig)
        if ptype in _CV_TYPES:
            assert got == {"field": ptype not in _CV_LINE_TYPES,
                           "bar": False, "key": True}, got
        else:
            assert got == {"field": False, "bar": False, "key": False}, got

    @pytest.mark.parametrize("mode", _MODES)
    def test_legend_off_leaves_the_colour_key(self, mode):
        """dash.sthlp: legend(off) removes the legend from any graph; a
        colorvar() key is not the legend, and stays."""
        fig, _ = _render(mode, [plot_for("scatter", {"colorvar": "foreign",
                                                     "colordiscrete": "1"}),
                                plot_for("lfit")], {"legend": "off"})
        keys = [m for m in fig.legend
                if str(m.name or "") == dr._COLORVAR_LEGEND_NAME]
        plots = [m for m in fig.legend if m not in keys]
        assert keys and all(k.visible for k in keys)
        assert plots and not any(p.visible for p in plots)

    @pytest.mark.parametrize("mode", _MODES)
    def test_connected_colours_its_markers_and_not_its_line(self, mode):
        fig, _ = _render(mode, [plot_for("connected", {"colorvar": "price"})])
        kinds = {type(r.glyph).__name__: _colour_mapped_one(r)
                 for r in _glyphs(fig)}
        assert kinds == {"Line": False, "Scatter": True}, kinds


class TestAStringColorvar:
    """twoway wants a numeric colorvar(): a string one is "found where
    numeric variable expected", r(7) (test_help_claims_7.cscript HC7-06).
    dash takes a string variable too, and draws one colour per distinct
    value with a key entry each -- in both modes."""

    def test_one_colour_per_value(self):
        import test_twoway_option_parity as tw
        r, doc, _, _ = tw._both([plot_for("scatter", {"colorvar": "make"})])
        for fig in tw._figures(r, doc):
            assert _colour_mapped(fig) == {"field": True, "bar": False,
                                           "key": True}
            key = [m for m in fig.right if isinstance(m, Legend)
                   and str(m.name or "") == dr._COLORVAR_LEGEND_NAME][0]
            assert len(key.items) == tw._DF["make"].nunique()

    def test_a_repeated_value_is_one_level(self, monkeypatch):
        """The string path took every OBSERVATION for a level: a variable
        holding D and F five times each gave the mapper ten factors and the
        key ten entries, D five times over.  One level per distinct value,
        and an empty string -- Stata's missing string -- drawn in
        colormissing() under "(missing)", as a missing number is."""
        import test_twoway_option_parity as tw
        df = tw._DF.copy()
        df["make"] = ["D", "F", "D", "F", "D", "F", "D", "F", "", "F"]
        monkeypatch.setattr(tw, "_DF", df)
        r, doc, _, _ = tw._both([plot_for("scatter", {
            "colorvar": "make", "colormissing": "red"})])
        for fig in tw._figures(r, doc):
            key = [m for m in fig.right if isinstance(m, Legend)
                   and str(m.name or "") == dr._COLORVAR_LEGEND_NAME][0]
            labels = [str(getattr(i.label, "value", i.label))
                      for i in key.items]
            assert labels == ["D", "F", "(missing)"], labels
            mapper = [r_.glyph.fill_color for r_ in _glyphs(fig)
                      if type(r_.glyph).__name__ == "Scatter"][0]
            mapper = (mapper.get("transform") if isinstance(mapper, dict)
                      else mapper.transform)
            # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
            assert list(mapper.factors) == ["D", "F"]
            assert str(mapper.nan_color).lower() == "#ff0000"


def _colour_mapped_one(r):
    for attr in ("fill_color", "line_color"):
        v = getattr(r.glyph, attr, None)
        if (isinstance(v, dict) and v.get("transform") is not None) or \
                getattr(v, "transform", None) is not None:
            return True
    return False


# ===========================================================================
# 5. legend(): quoted text is text, and twoway's keywords only
# ===========================================================================

_TWO = [plot_for("scatter"), plot_for("lfit")]


def _legend_state(fig):
    lg = [x for x in fig.legend
          if str(x.name or "") != dr._COLORVAR_LEGEND_NAME][0]
    side = [s for s in ("above", "below", "left", "right", "center")
            if lg in getattr(fig, s)]
    return {"visible": lg.visible, "location": str(lg.location),
            "side": side}


class TestLegendReadsItsSuboptionsNotItsLabels:
    """_dash_apply_legend searched the whole legend() text, quoted labels
    included: legend(label(1 "Turned off")) hid the legend, label(1 "on")
    forced one onto a one-key graph, and label(1 "left"), label(2 "pos(3)")
    and label(1 "ring(0)") each moved it."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("label", ['label(1 "Turned off")',
                                       'label(1 "left")',
                                       'label(2 "pos(3)")',
                                       'label(1 "ring(0)")',
                                       'label(2 "order(2)")',
                                       'label(1 "cols(3)")'])
    def test_a_label_does_not_move_or_hide_the_legend(self, mode, label):
        base, _ = _render(mode, _TWO)
        fig, _ = _render(mode, _TWO, {"legend": label})
        assert _legend_state(fig) == _legend_state(base), (
            f"legend({label}) changed the legend ({mode})")
        assert len(fig.legend[0].items) == len(base.legend[0].items)
        assert fig.legend[0].ncols == base.legend[0].ncols

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_label_reading_on_does_not_force_a_legend(self, mode):
        fig, _ = _render(mode, [plot_for("scatter")],
                         {"legend": 'label(1 "on")'})
        assert not _legend_state(fig)["visible"], (
            "a one-key graph drew a legend because a label read 'on'")

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_real_suboptions_still_work_beside_a_label(self, mode):
        fig, _ = _render(mode, _TWO,
                         {"legend": 'position(3) label(1 "Cars") off'})
        st = _legend_state(fig)
        assert st["side"] == ["right"] and not st["visible"], st
        assert str(fig.legend[0].items[0].label.value) == "Cars"
        shown, _ = _render(mode, [plot_for("scatter")],
                           {"legend": 'on label(1 "Cars")'})
        assert _legend_state(shown)["visible"]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("kw", ["top", "bottom", "left", "right"])
    def test_a_bare_direction_word_is_not_a_placement(self, mode, kw):
        """twoway refuses legend(top) ("option top not allowed", r(198)), and
        so does dash.ado (test_help_claims_7.cscript HC7-01).  A spec that
        carries one anyway is named, not placed: it used to put the legend
        INSIDE the plot, where twoway places nothing."""
        base, _ = _render(mode, _TWO)
        fig, caught = _render(mode, _TWO, {"legend": kw})
        assert _legend_state(fig) == _legend_state(base), (
            f"legend({kw}) moved the legend ({mode})")
        assert any("legend() sub-option" in w and kw in w for w in caught), (
            caught)


# ===========================================================================
# 6. Marker and Transparency Options
# ===========================================================================

#: The plot types whose markers jitter() moves in dash -- the markers only;
#: connected and rconnected keep their lines where the data are, as twoway
#: does.  Flipped (WP-31 C8a): rscatter, rcapsym, pcscatter and pccapsym,
#: whose markers twoway jitters (colorvar_types_truth.json jitter), are
#: jittered too; dash.ado named jitter() there.
_JITTER_TYPES = {"scatter", "connected", "rconnected", "dot", "dropline",
                 "scatteri", "rscatter", "rcapsym", "pcscatter", "pccapsym",
                 # WP-31 B1: rpcap's and rpspike's y3 markers, which
                 # twoway jitters (rangept_truth.json jitter.rpcap).
                 "rpcap", "rpspike"}
#: The plot types that draw markers, and so take msangle() and malpha().
_MARKER_TYPES = {"scatter", "connected", "rconnected", "dot", "dropline",
                 "scatteri", "rscatter", "rcapsym", "pcscatter", "pccapsym",
                 "rpcap", "rpspike"}


def _coords(fig, only=None):
    out = []
    for r in _glyphs(fig):
        name = type(r.glyph).__name__
        if only is not None and name != only:
            continue
        row = [name]
        for f in _X_FIELDS + _Y_FIELDS:
            fld = _field(r.glyph, f)
            if fld and fld in r.data_source.data:
                row.append((f, tuple(round(float(v), 6)
                                     for v in r.data_source.data[fld])))
        out.append(tuple(row))
    return out


class TestJitter:

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_the_types_jitter_moves(self, mode, ptype):
        base, _ = _render(mode, [plot_for(ptype)])
        moved, _ = _render(mode, [plot_for(ptype, {"jitter": "20",
                                                   "jitterseed": "7"})])
        assert (_coords(base) != _coords(moved)) == (ptype in _JITTER_TYPES)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", ["connected", "rconnected"])
    def test_the_line_stays_where_the_data_are(self, mode, ptype):
        base, _ = _render(mode, [plot_for(ptype)])
        moved, _ = _render(mode, [plot_for(ptype, {"jitter": "20",
                                                   "jitterseed": "7"})])
        assert _coords(base, "Line") == _coords(moved, "Line")
        assert _coords(base, "Scatter") != _coords(moved, "Scatter")


class TestMsangle:

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_the_types_msangle_turns(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"msangle": "45"})])
        angles = {round(float(r.glyph.angle), 9) for r in _glyphs(fig)
                  if type(r.glyph).__name__ == "Scatter" and not _is_cap(r)}
        if ptype in _MARKER_TYPES:
            assert angles == {round(math.radians(45), 9)}, angles
        else:
            assert not angles or angles == {0.0}, angles

    def test_a_positive_bokeh_marker_angle_turns_counter_clockwise(self):
        """msangle(45) is Bokeh angle +pi/4, which BokehJS draws
        counter-clockwise: AngleSpec.materialize negates the value before
        the canvas's clockwise rotate().  twoway turns the marker the same
        way (its SVG writes rotate(-45)); dash.sthlp said clockwise."""
        import bokeh
        js = os.path.join(os.path.dirname(bokeh.__file__), "server",
                          "static", "js", "bokeh.js")
        if not os.path.exists(js):
            pytest.skip("the BokehJS bundle is not installed beside bokeh")
        with open(js, encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r"class AngleSpec extends NumberUnitsSpec \{(.*?)\n"
                      r"    \}\n", src, re.S)
        assert m, "BokehJS's AngleSpec moved; re-measure the direction"
        assert re.search(r"materialize\(value\) \{\s*const coeff = -",
                         m.group(1)), (
            "BokehJS no longer negates an angle: msangle() would turn "
            "clockwise, against twoway and against dash.sthlp")


def _alphas(fig, markers):
    return [(type(r.glyph).__name__,
             round(float(getattr(r.glyph, "fill_alpha", -1)), 6),
             round(float(getattr(r.glyph, "line_alpha", -1)), 6))
            for r in _glyphs(fig)
            if (type(r.glyph).__name__ == "Scatter"
                and not _is_cap(r)) == markers]


class TestAlphaOptions:
    """malpha() is the markers' opacity and nothing else's."""

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_malpha_is_the_markers_opacity(self, mode, ptype):
        base, _ = _render(mode, [plot_for(ptype)])
        fig, _ = _render(mode, [plot_for(ptype, {"malpha": "30"})])
        marks = _alphas(fig, True)
        if ptype in _MARKER_TYPES:
            assert marks and all(fa == 0.3 and la == 0.3
                                 for _, fa, la in marks), marks
        assert _alphas(fig, False) == _alphas(base, False)


# ===========================================================================
# 7. color(), marker() and hover()
# ===========================================================================

def _colours(fig):
    out = {}
    for r in _glyphs(fig):
        g = r.glyph
        out.setdefault(type(g).__name__, set()).update(
            str(getattr(g, a)).lower() for a in ("fill_color", "line_color")
            if hasattr(g, a) and not str(getattr(g, a)).startswith("{")
            and not (a == "fill_color" and _is_cap(r)))
    return out


class TestColorColoursTheWholeLayer:
    """twoway's color() sets a layer's fill and line colours alike: red
    markers, red lines, a red band on rarea and rbar and a red confidence
    band on lfitci (SVG, 23sep2026).  dash left a range area and a range
    bar's fill at the scheme's colour and every confidence band grey."""

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(
        ["rarea", "rbar", "area", "bar", "histogram"]))
    def test_the_fill_is_the_colour(self, mode, ptype):
        """The fill is color()'s colour at the layer's intensity: twoway's
        rbar, color(red) fills #FF3333 (p#bar or p#area at inten80); a
        histogram is at full intensity until section 24 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        fig, _ = _render(mode, [plot_for(ptype, {"color": "red"})])
        fills = [str(r.glyph.fill_color).lower() for r in _glyphs(fig)
                 if hasattr(r.glyph, "fill_color")]
        want = "#ff0000" if ptype == "histogram" else "#ff3333"
        assert fills and set(fills) == {want}, (ptype, fills)

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(
        ["lfitci", "qfitci", "lpolyci", "fpfitci"]))
    def test_the_confidence_band_is_the_colour(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"color": "red"})])
        got = _colours(fig)
        assert got.get("VArea") == {"#ff0000"}, got
        assert got.get("Line") == {"#ff0000"}, got

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(
        sorted(_MARKER_TYPES)))
    def test_markers_and_lines_alike(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"color": "red"})])
        got = _colours(fig)
        assert got and all(v == {"#ff0000"} for v in got.values()), got

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_specific_colour_option_wins(self, mode):
        fig, _ = _render(mode, [plot_for("rbar", {"color": "red",
                                                  "fcolor": "navy"})])
        # fcolor()'s navy at rbar's intensity, inten80 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        assert {str(r.glyph.fill_color).lower() for r in _glyphs(fig)} == {
            "#486c8c"}


class TestMarkerIsMsymbol:
    """marker() is dash's own spelling of msymbol(); twoway refuses it
    (test_help_claims_7.cscript HC7-03)."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", sorted(_MARKER_TYPES))
    def test_marker_sets_the_symbol(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype, {"marker": "D"})])
        marks = {str(r.glyph.marker) for r in _glyphs(fig)
                 if type(r.glyph).__name__ == "Scatter" and not _is_cap(r)}
        assert marks == {"diamond"}, marks

    @pytest.mark.parametrize("mode", _MODES)
    def test_msymbol_wins_over_marker(self, mode):
        fig, _ = _render(mode, [plot_for("scatter", {"marker": "D",
                                                     "msymbol": "S"})])
        marks = {str(r.glyph.marker) for r in _glyphs(fig)
                 if type(r.glyph).__name__ == "Scatter"}
        assert marks == {"square"}, marks


#: The plot types whose tooltip carries a variable hover() names: the ones
#: whose marks are observations, as dash.sthlp lists them.  Every other
#: type is computed or immediate, and a note names it (test_mode_parity.py
#: TestHoverReachesEveryLayerOrIsReported).
_HOVER_TYPES = {"scatter", "connected", "line", "tsline", "area", "dot",
                "dropline", "bar", "spike", "rarea", "rbar", "rspike",
                "rcap", "rcapsym", "rline", "tsrline", "rconnected",
                "rscatter", "pcspike", "pcarrow", "pcbarrow", "pcscatter",
                "pccapsym", "rpcap", "rpspike"}


def _hover_rows(fig):
    rows = set()
    for t in fig.tools:
        if isinstance(t, HoverTool) and isinstance(t.tooltips, list):
            rows.update(label for label, _ in t.tooltips)
    return rows


class TestHover:

    @pytest.mark.parametrize("ptype,mode", _types_by_mode(_TYPES))
    def test_the_types_whose_tooltip_shows_the_variable(self, mode, ptype):
        fig, _ = _render(mode, [plot_for(ptype)], {"hover": "rep"})
        assert ("rep" in _hover_rows(fig)) == (ptype in _HOVER_TYPES), (
            _hover_rows(fig))


# ===========================================================================
# 8. xtick() and ytick(): ticks without labels, beside the labels
# ===========================================================================

def _primary(fig, which):
    axes = fig.xaxis if which == "x" else fig.yaxis
    attr = "x_range_name" if which == "x" else "y_range_name"
    return [a for a in axes if getattr(a, attr) == "default"][0]


def _tick_args(axis):
    t = axis.ticker
    assert type(t).__name__ == "CustomJSTicker", (
        f"the axis ticker is {type(t).__name__}; xtick()/ytick() were not "
        f"drawn as ticks without labels")
    return t.args


class TestTicksWithoutLabels:
    """dash.sthlp: xtick() and ytick() are "tick positions without labels".
    GAPS.md F4 found them labelled when alone and dropped beside xlabel(),
    and TR-23.1's "fixed in WP-14/WP-15" did not hold on 23sep2026: xtick()
    alone still replaced the axis's labels with labelled ticks at its
    positions, and beside xlabel() it was not read at all."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("which", ["x", "y"])
    def test_alone_they_keep_the_default_labels(self, mode, which):
        opt, pos = (("xtick", "2500 3500") if which == "x"
                    else ("ytick", "18 27"))
        base, _ = _render(mode, [plot_for("scatter")])
        fig, _ = _render(mode, [plot_for("scatter")], {opt: pos})
        args = _tick_args(_primary(fig, which))
        assert args["extra"] == [float(v) for v in pos.split()]
        # The labelled ticks are the axis's own, as without the option.
        assert type(args["base"]).__name__ == type(
            _primary(base, which).ticker).__name__

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("which", ["x", "y"])
    def test_beside_a_label_option_both_are_drawn(self, mode, which):
        go = ({"xlabel": "2000 4000", "xtick": "3000"} if which == "x"
              else {"ylabel": "15 25", "ytick": "20"})
        fig, _ = _render(mode, [plot_for("scatter")], go)
        args = _tick_args(_primary(fig, which))
        assert type(args["base"]).__name__ == "FixedTicker"
        assert [float(v) for v in args["base"].ticks] == (
            [2000.0, 4000.0] if which == "x" else [15.0, 25.0])
        assert args["extra"] == ([3000.0] if which == "x" else [20.0])

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_tick_only_positions_look_like_major_ticks(self, mode):
        fig, _ = _render(mode, [plot_for("scatter")], {"xtick": "2500"})
        ax = _primary(fig, "x")
        assert (ax.minor_tick_in, ax.minor_tick_out,
                ax.minor_tick_line_color, ax.minor_tick_line_width) == (
            ax.major_tick_in, ax.major_tick_out, ax.major_tick_line_color,
            ax.major_tick_line_width)

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_rule_forms(self, mode):
        # #4 marks where twoway puts #4 over the drawn weights, 1800 to
        # 4080: `_natscale 1800 4080 4' is 2000(500)4000 (measured
        # 24sep2026; BUGS.md "ylabel(#N) and xlabel(#N) ticks fall where
        # Bokeh puts them").
        fig, _ = _render(mode, [plot_for("scatter")], {"xtick": "#4"})
        args = _tick_args(_primary(fig, "x"))
        assert "every" not in args
        assert args["extra"] == [2000.0, 2500.0, 3000.0, 3500.0, 4000.0]
        fig, _ = _render(mode, [plot_for("scatter")],
                         {"xtick": "2000(500)3000"})
        assert _tick_args(_primary(fig, "x"))["extra"] == [2000.0, 2500.0,
                                                           3000.0]
        fig, _ = _render(mode, [plot_for("scatter")], {"xtick": "minmax"})
        w = tp._DF["weight"]
        assert _tick_args(_primary(fig, "x"))["extra"] == [
            float(w.min()), float(w.max())]
        fig, _ = _render(mode, [plot_for("scatter")], {"xtick": "none"})
        assert type(_primary(fig, "x").ticker).__name__ != "CustomJSTicker"

    @pytest.mark.parametrize("mode", _MODES)
    def test_grid_draws_gridlines_at_the_ticks(self, mode):
        fig, _ = _render(mode, [plot_for("scatter")], {"ytick": "20, grid"})
        # One y grid on the figure's own range in both renders (measured
        # 24sep2026, both modes); an all() over none held with the grid
        # gone or moved to another range.
        own = [g for g in fig.ygrid if g.y_range_name == "default"]
        assert len(own) == 1, [g.y_range_name for g in fig.ygrid]
        assert all(g.minor_grid_line_color is not None for g in fig.ygrid
                   if g.y_range_name == "default")
        plain, _ = _render(mode, [plot_for("scatter")], {"ytick": "20"})
        own = [g for g in plain.ygrid if g.y_range_name == "default"]
        assert len(own) == 1, [g.y_range_name for g in plain.ygrid]
        assert all(g.minor_grid_line_color is None for g in plain.ygrid
                   if g.y_range_name == "default")

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_label_suboption_on_a_tick_option_is_named(self, mode):
        _, caught = _render(mode, [plot_for("scatter")],
                            {"xtick": "2500, labsize(large)"})
        assert any("xtick() sub-option" in w and "labsize(large)" in w
                   for w in caught), caught

    def test_the_tick_code_carries_no_data(self):
        """The CustomJS code is constant text; the positions travel in args
        as numbers, so nothing a user writes reaches the code."""
        for code in (dr._DASH_TICK_MAJOR_JS, dr._DASH_TICK_EXTRA_JS,
                     dr._DASH_TICK_EVERY_JS):
            assert re.fullmatch(r"[A-Za-z0-9_ .(),;=>&<\[\]]+", code), code


# ===========================================================================
# 9. The second axis is the second axis's
# ===========================================================================

class TestTheSecondAxisIsItsOwn:
    """fig.xaxis and fig.yaxis splat over every axis on a side, the
    xaxis(2)/yaxis(2) one included; the primary axis options reached it,
    and a yaxis(2) layer's labels and arrowheads stayed on the left axis."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_ylabel_labels_the_left_axis_only(self, mode):
        fig, _ = _render(mode, _Y2, {"ylabel": "15 20 25 30"})
        left = _primary(fig, "y")
        right = _axis2(fig, "y2")
        assert [float(v) for v in left.ticker.ticks] == [15.0, 20.0, 25.0,
                                                         30.0]
        # WP-30 P1.3a: "not a FixedTicker" was wrong because the right-hand
        # axis now carries its own default (natscale) FixedTicker; ylabel()
        # must still not reach it.
        assert dr._DASH_DEFAULT_TAG in (right.ticker.tags or []), (
            f"ylabel() set the right-hand axis's ticks too ({mode})")

    @pytest.mark.parametrize("mode", _MODES)
    def test_xlabel_labels_the_bottom_axis_only(self, mode):
        fig, _ = _render(mode, _X2, {"xlabel": "2000 3000"})
        top = _axis2(fig, "x2")
        # WP-30 P1.3a: the top axis carries its own default ticker.
        assert dr._DASH_DEFAULT_TAG in (top.ticker.tags or []), (
            f"xlabel() set the top axis's ticks too ({mode})")

    @pytest.mark.parametrize("mode", _MODES)
    def test_xtick_and_ytick_tick_the_primary_axes_only(self, mode):
        fig, _ = _render(mode, _X2, {"xtick": "3000"})
        assert type(_axis2(fig, "x2").ticker).__name__ != "CustomJSTicker"
        assert type(_primary(fig, "x").ticker).__name__ == "CustomJSTicker"
        fig, _ = _render(mode, _Y2, {"ytick": "20"})
        assert type(_axis2(fig, "y2").ticker).__name__ != "CustomJSTicker"
        assert type(_primary(fig, "y").ticker).__name__ == "CustomJSTicker"

    @pytest.mark.parametrize("mode", _MODES)
    def test_xtitle_styles_the_bottom_title_only(self, mode):
        fig, _ = _render(mode, _X2, {"xtitle": "W, color(red)"})
        assert str(_primary(fig, "x").axis_label_text_color) == "#ff0000"
        assert str(_axis2(fig, "x2").axis_label_text_color) != "#ff0000", (
            f"xtitle()'s colour reached the top axis's title ({mode})")

    @pytest.mark.parametrize("mode", _MODES)
    def test_marker_labels_go_on_the_second_axis(self, mode):
        from bokeh.models import LabelSet
        fig, _ = _render(mode, [plot_for("line"),
                                plot_for("scatter", {"yaxis": "2",
                                                     "mlabel": "rep"},
                                         yvar="price")])
        sets = [m for m in fig.center if isinstance(m, LabelSet)]
        assert sets and all(s.y_range_name == "y2" for s in sets), (
            [s.y_range_name for s in sets])

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("which,plots", [
        ("y", _Y2), ("x", _X2),
        ("y", [plot_for("scatter"),
               plot_for("scatter", {"yaxis": "2"}, yvar="price")])])
    def test_the_first_axis_is_scaled_to_its_own_layers(self, mode, which,
                                                         plots):
        """The left axis spans the layers on the left, not the right-hand
        layer too.  Its DataRange1d read every renderer on the figure --
        BokehJS unites the bounds of all the renderers a DataRange1d is
        given, whatever range they draw on -- so (line mpg weight) (line
        price weight, yaxis(2)) drew the left axis from 0 to 11,000 and mpg
        flat along the bottom, in both modes (seen in a browser,
        23sep2026)."""
        fig, _ = _render(mode, plots)
        rng = fig.y_range if which == "y" else fig.x_range
        attr = "y_range_name" if which == "y" else "x_range_name"
        # WP-30 P1.3a: a renderer list was wrong because the axis is now a
        # Range1d over the hull of the layers on its own range (and ticks).
        own = dr._dash_layer_extent(fig.renderers, attr, "default")
        lo, hi = dr._dash_range_hull(rng)
        ax = _primary(fig, which)
        t = list(getattr(ax.ticker, "ticks", None) or [])
        assert (lo, hi) == pytest.approx((min([own[0]] + t),
                                          max([own[1]] + t))), (
            f"the {which} range reads the second axis's layer ({mode})")

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_figure_without_a_second_axis_keeps_its_range(self, mode):
        """No second axis, no change: a line and its fit still range over
        every renderer (an empty list is Bokeh's "all of them")."""
        plain, _ = _render(mode, [plot_for("line"), plot_for("lfit")])
        # WP-30 P1.3a: an empty renderer list was wrong because the axes
        # are now Range1d over every layer, the fit included.
        for rng, attr in ((plain.y_range, "y_range_name"),
                          (plain.x_range, "x_range_name")):
            ext = dr._dash_layer_extent(plain.renderers, attr, "default")
            lo, hi = dr._dash_range_hull(rng)
            assert lo <= ext[0] + 1e-9 and hi >= ext[1] - 1e-9

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_legend_stays_on_the_figure(self, mode):
        """The figure's legend is made by whichever layer draws first; a
        first layer on yaxis(2) must not take it to the second axis."""
        fig, _ = _render(mode, [plot_for("scatter", {"yaxis": "2",
                                                     "mlabel": "rep"},
                                         yvar="price"), plot_for("line")],
                         {"legend": "ring(0) pos(3)"})
        # One legend, keying both layers (measured 24sep2026, both modes):
        # an all() over no legend held with the legend gone from the
        # figure, the very thing this test's name says cannot happen.
        assert len(fig.legend) == 1, len(fig.legend)
        assert len(fig.legend[0].items) == 2, fig.legend[0].items
        assert all(lg.y_range_name == "default" for lg in fig.legend)

    @pytest.mark.parametrize("mode", _MODES)
    def test_arrowheads_go_on_the_second_axis(self, mode):
        # WP-31 C1: the head is a glyph renderer the script draws in its
        # own range's scale (an Arrow annotation before).
        fig, _ = _render(mode, [plot_for("line"),
                                plot_for("pcarrow", {"yaxis": "2"})])
        heads = [r for r in fig.renderers if "dash-arrowhead" in (r.tags or [])]
        assert heads and all(h.y_range_name == "y2" for h in heads)

    @pytest.mark.parametrize("mode", _MODES)
    def test_yscale2_log_reverse_and_range(self, mode):
        fig, _ = _render(mode, _Y2, {"yscale2": "log"})
        assert isinstance(_axis2(fig, "y2"), LogAxis)
        rng = fig.extra_y_ranges["y2"]
        assert 0 < rng.start < float(tp._DF["price"].min())
        fig, _ = _render(mode, _Y2, {"yscale2": "reverse"})
        rng = fig.extra_y_ranges["y2"]
        assert rng.start > rng.end, "yscale2(reverse) did not reverse"
        fig, _ = _render(mode, _Y2, {"yscale2": "range(0 20000)"})
        rng = fig.extra_y_ranges["y2"]
        # WP-28 B2: range() widens to 0 and 20000, padded 5% a side (this
        # pinned exactly (0, 20000)).
        assert dr._dash_range_hull(rng) == pytest.approx((0.0, 20000.0))

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_unhonoured_yscale2_suboption_is_named(self, mode):
        # Flipped (WP-30 P1.18a): noline is drawn; outergap() is not.
        _, caught = _render(mode, _Y2, {"yscale2": "outergap(1)"})
        assert any("yscale2() sub-option" in w and "outergap(1)" in w
                   for w in caught), caught


# ===========================================================================
# 10. Figure proportions, colour notation, line options, palettes
# ===========================================================================

class TestTheHeightBand:
    """dash.sthlp, Figure proportions: "The ratio is honoured within a
    height band"; the band is the figure's min_height and max_height, which
    BokehJS holds while the aspect ratio yields outside it."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("go", [{"xsize": "10", "ysize": "2"},
                                    {"aspectratio": "1"}, {}])
    def test_every_proportioned_figure_carries_the_band(self, mode, go):
        fig, _ = _render(mode, [plot_for("scatter")], go)
        assert fig.aspect_ratio is not None
        assert (fig.min_height, fig.max_height) == (
            dr._MIN_FIGURE_HEIGHT, dr._MAX_FIGURE_HEIGHT)


class TestColourAlphaNotation:
    """mcolor(red%50) and mcolor(red) malpha(50) are the same thing."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_two_spellings_draw_the_same_marker(self, mode):
        def marker(opts):
            fig, _ = _render(mode, [plot_for("scatter", opts)])
            g = [r.glyph for r in _glyphs(fig)
                 if type(r.glyph).__name__ == "Scatter"][0]
            return (str(g.fill_color), str(g.line_color),
                    round(float(g.fill_alpha), 6),
                    round(float(g.line_alpha), 6))
        a = marker({"mcolor": "red%50"})
        b = marker({"mcolor": "red", "malpha": "50"})
        assert a == b == ("#ff0000", "#ff0000", 0.5, 0.5), (a, b)


class TestAnUnknownLineStyleIsNamedWithoutALine:
    """An unknown lcolor() or lwidth() name is still reported on a plot with
    no line, as twoway notes it there."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt,val", [("lcolor", "notacolour"),
                                         ("lwidth", "notawidth")])
    def test_the_note(self, mode, opt, val):
        _, caught = _render(mode, [plot_for("scatter", {opt: val})])
        assert any(val in w and opt in w for w in caught), caught


class TestColourPalettes:
    """dash.sthlp: colpalette() is viridis, magma, inferno, plasma,
    cividis, turbo, greys, blues or reds -- each Bokeh's 256-colour palette
    of that name; without it the key is twoway's colour rule (WP-31 C8b)."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("name", ["", "viridis", "magma", "inferno",
                                      "plasma", "cividis", "turbo", "greys",
                                      "blues", "reds"])
    def test_the_palette(self, mode, name):
        from bokeh import palettes
        opts = {"colorvar": "price"}
        if name:
            opts["colpalette"] = name
        fig, _ = _render(mode, [plot_for("scatter", opts)])
        bars = [m for m in fig.right if isinstance(m, ColorBar)]
        assert bars, "no colour bar"
        # Flipped (WP-31 C8b): viridis with no colpalette() was wrong
        # because twoway draws the key in its colour rule, hue from blue to
        # red under s2color (colorvar_options_truth.json D01); colpalette()
        # stays dash's own.
        want = (getattr(palettes, name.capitalize() + "256") if name else
                dr._dash_colorrule_palette("hue", "#0000ff", "#ff0000", 256))
        assert list(bars[0].color_mapper.palette) == list(want)


# ===========================================================================
# 11. The helpers this work added, one by one (CLAUDE.md rule 4)
# ===========================================================================

class TestTheNewHelpers:

    @pytest.mark.parametrize("raw,want", [
        ('"255 0 0"', "255 0 0"), ('`"255 0 0"\'', "255 0 0"),
        ("navy", "navy"), ('"255 0 0', '"255 0 0'), ('""', ""),
        ('  "#1a476f"  ', "#1a476f"), ('"a" "b"', 'a" "b'),
    ])
    def test_dash_unquoted(self, raw, want):
        assert dr._dash_unquoted(raw) == want

    def test_the_region_readers_unquote(self):
        # Flipped (WP-30 P1.20a): _extract_region_color/_lcolor were wrong
        # because the region reader is _dash_region_spec; an RGB triplet's
        # quotes still come off.
        base = {"fill": "#ffffff", "fill_alpha": 1.0, "line": "#ffffff",
                "line_alpha": 1.0, "line_width": 0.768, "line_dash": []}
        s, _ = dr._dash_region_spec('lwidth(2) color("0 0 255")',
                                    "plotregion", base)
        assert s["fill"] == "#0000ff"
        s, _ = dr._dash_region_spec('lcolor("1 2 3")', "plotregion", base)
        assert (s["line"], s["fill"]) == ("#010203", "#ffffff")

    def test_dash_legend_parts(self):
        words, calls = dr._dash_legend_parts(
            'OFF pos(6) label(1 "on top") order(2 1)')
        # Names are twoway's (WP-30 P1.19): capitals are unread, and each
        # call is (full name, argument, name as typed).
        assert words == set()
        assert calls == [("position", "6", "pos"),
                         ("label", '1 "on top"', "label"),
                         ("order", "2 1", "order")]
        assert dr._dash_legend_parts("") == (set(), [])

    def test_dash_legend_arg(self):
        calls = [("pos", "x"), ("position", "12"), ("pos", "3")]
        assert dr._dash_legend_arg(calls, ("order",)) is None
        assert dr._dash_legend_arg(calls, ("position", "pos")) == "x"
        m = dr._dash_legend_arg(calls, ("position", "pos"), r"(\d+)")
        assert m.group(1) == "12"

    def test_dash_primary_axes_keeps_the_list_type(self):
        from bokeh.plotting import figure as _f
        from bokeh.models import LinearAxis, Range1d
        fig = _f()
        fig.extra_y_ranges["y2"] = Range1d(0, 1)
        fig.add_layout(LinearAxis(y_range_name="y2"), "right")
        second = [a for a in fig.yaxis if a.y_range_name == "y2"][0]
        before = second.axis_label
        prim = dr._dash_primary_axes(fig.yaxis, "y_range_name")
        assert type(prim) is type(fig.yaxis) and len(prim) == 1
        assert prim[0].y_range_name == "default"
        prim.axis_label = "left only"          # the splat sets every member
        assert prim[0].axis_label == "left only"
        assert second.axis_label == before

    def test_dash_secondary_values(self):
        from bokeh.plotting import figure as _f
        from bokeh.models import (BooleanFilter, CDSView, ColumnDataSource,
                                  Range1d)
        fig = _f()
        fig.extra_y_ranges["y2"] = Range1d(0, 1)
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [10.0, 20.0, 90.0]})
        r = fig.scatter("x", "y", source=src, y_range_name="y2",
                        view=CDSView(filter=BooleanFilter([True, True,
                                                           False])))
        bars = fig.vbar(x="x", top="y", bottom=0, width=0.5,
                        source=ColumnDataSource({"x": [1.0], "y": [5.0]}),
                        y_range_name="y2")
        cols, every = dr._dash_secondary_values(fig, "y_range_name", "y2")
        assert sorted(cols) == [5.0, 10.0, 20.0]      # 90 is outside the view
        assert sorted(every) == [0.0, 5.0, 10.0, 20.0]  # the bar's base
        assert r and bars


# ===========================================================================
# 12. Adversarial (CLAUDE.md rule 18): the readers this work changed
# ===========================================================================

class TestAdversarialLegendAxesRegions:
    """Bypass, injection and exhaustion against the three readers WP-23
    rewrote: legend()'s sub-options, the second axes' and xtick()'s rules,
    and the region colours.  Each case runs both render modes."""

    # ---- legend() ----------------------------------------------------------

    def test_a_direction_word_in_any_spelling_is_not_a_placement(self):
        """Bypass: legend(top) is refused by dash.ado; no other spelling of
        it -- a capital, quotes, empty or full parentheses -- places the
        legend inside the plot either."""
        for mode in _MODES:
            base = _legend_state(_render(mode, _TWO)[0])
            for lg in ("Top", '"top"', "top()", "top(1)", "RIGHT"):
                st = _legend_state(_render(mode, _TWO, {"legend": lg})[0])
                assert st == base, (mode, lg, st, base)

    def test_label_text_is_a_label_and_never_read(self):
        """Injection: sub-option words and markup inside a quoted label are
        the label's text -- carried raw, as a DOM text node draws it --
        and move, hide or restyle nothing."""
        text = 'off pos(3) ring(0) cols(9) <b>x</b> $$\\href{a}$$'
        for mode in _MODES:
            base = _render(mode, _TWO)[0]
            fig = _render(mode, _TWO, {"legend": 'label(1 "%s")' % text})[0]
            assert _legend_state(fig) == _legend_state(base), mode
            assert fig.legend[0].ncols == base.legend[0].ncols
            # Flipped (WP-30 P1.11a): twoway draws a TeX pair as typed, so
            # the key carries the text with each delimiter broken by U+2060.
            from bokeh.embed.util import contains_tex_string
            lab = fig.legend[0].items[0].label.value
            assert lab.replace(dr._DASH_WORD_JOINER, "") == text
            assert not contains_tex_string(lab)

    def test_a_ten_thousand_word_legend_is_read_in_bounded_time(self):
        """Exhaustion: the sub-option reader is linear."""
        import time
        lg = "on " * 10000 + 'label(1 "x")'
        for mode in _MODES:
            t0 = time.perf_counter()
            fig, _ = _render(mode, [plot_for("scatter")], {"legend": lg})
            assert time.perf_counter() - t0 < 30, mode
            assert _legend_state(fig)["visible"]

    # ---- ylabel2()/xlabel2() and xtick() -------------------------------------

    def test_a_huge_increment_on_a_second_axis_or_a_tick_is_bounded(self):
        """Exhaustion: 0(0.000001)1000000 asks for 10**12 ticks.  The shared
        parser counts before it builds, so the axis keeps its default ticks
        and a warning says why, in both modes, quickly."""
        import time
        rule = "0(0.000001)1000000"
        for mode in _MODES:
            t0 = time.perf_counter()
            fig, caught = _render(mode, _Y2, {"ylabel2": rule, "xtick": rule})
            assert time.perf_counter() - t0 < 30, mode
            # WP-30 P1.3a: the default ticks are now a tagged FixedTicker.
            assert dr._DASH_DEFAULT_TAG in (_axis2(fig, "y2").ticker.tags
                                            or [])
            assert type(_primary(fig, "x").ticker).__name__ != "CustomJSTicker"
            assert sum("more than 2,000 ticks" in w for w in caught) >= 1
            # One note each: ylabel2() and xtick() are read apart and each
            # names its own (measured 24sep2026 -- one alone gives one, the
            # two give two, in both modes; `caught' keeps repeats).  At
            # least one passed a tick that kept its default in silence.
            assert sum("more than 2,000 ticks" in w for w in caught) == 2, (
                mode, caught)

    def test_axis_label_text_is_data_never_code(self):
        """Injection: a value label on the second axis travels in the
        formatter's args, as JSON, and the code is constant; the saved page
        carries no live markup from it."""
        hostile = '</script><script>alert(1)</script>'
        for mode in _MODES:
            fig, _ = _render(mode, _Y2,
                             {"ylabel2": '5000 "%s" 10000 "ok"' % hostile})
            fmt = _axis2(fig, "y2").formatter
            assert hostile not in fmt.code
            assert hostile in str(fmt.args["labels"])
        spec = tp._spec(_Y2, None, {"ylabel2": '5000 "%s"' % hostile})
        _, _, page = tp._standalone_page(spec)
        assert hostile not in page

    def test_tick_positions_are_numbers_only(self):
        """Bypass and injection through xtick(): a word among the positions
        is named, never carried, and the tick code stays constant."""
        for mode in _MODES:
            fig, caught = _render(mode, [plot_for("scatter")],
                                  {"xtick": "2500 abc 3500 alert(1)"})
            t = _primary(fig, "x").ticker
            assert t.args["extra"] == [2500.0, 3500.0]
            assert t.minor_code == dr._DASH_TICK_EXTRA_JS
            assert any("xtick() sub-option" in w and "abc" in w
                       for w in caught), caught

    # ---- plotregion()/graphregion() colours -----------------------------------

    def test_a_hostile_colour_is_refused_not_passed_through(self):
        """Injection: a colour that is CSS with a payload is no colour; it
        is named and drawn black, as twoway draws an unknown colour, never
        set raw (Flipped, WP-30 P1.13a: the scheme's colour was kept)."""
        payload = 'color("red; background:url(javascript:alert(1))")'
        for mode in _MODES:
            fig, caught = _render(mode, [plot_for("scatter")],
                                  {"plotregion": payload,
                                   "graphregion": payload})
            assert fig.background_fill_color == "#000000"
            assert fig.border_fill_color == "#000000"
            assert any("javascript" in w for w in caught), caught

    def test_quotes_that_are_not_a_pair_are_not_stripped(self):
        """Bypass: compound quotes are a pair and are read; a quote with no
        partner is not, and the colour is named, not guessed."""
        for mode in _MODES:
            fig, _ = _render(mode, [plot_for("scatter")],
                             {"plotregion": 'color(`"255 0 0"\')'})
            assert str(fig.background_fill_color).lower() == "#ff0000"
            fig, caught = _render(mode, [plot_for("scatter")],
                                  {"plotregion": 'color("255 0 0)'})
            # Flipped (WP-30 P1.13a): an unknown colour is black; the
            # scheme's colour was kept.
            assert fig.background_fill_color == "#000000"
            assert caught
            # Any warning passed `assert caught'.  The note that names the
            # colour is knowable (measured 24sep2026, both modes, the only
            # warning this render raises).
            assert any('plotregion(color("255 0 0)) is not a recognised '
                       'colour' in w for w in caught), caught

    def test_a_hundred_thousand_character_colour_is_named_quickly(self):
        """Exhaustion: an enormous colour name is judged and named in
        bounded time, and the render survives."""
        import time
        for mode in _MODES:
            t0 = time.perf_counter()
            fig, caught = _render(mode, [plot_for("scatter")],
                                  {"plotregion": "color(%s)" % ("a" * 100000)})
            assert time.perf_counter() - t0 < 30, mode
            assert caught
            # Named means this note, not any warning (measured 24sep2026,
            # both modes: the only one, 161 characters -- the name shown
            # cut short, never all 100,000 of it).
            notes = [w for w in caught
                     if "plotregion(color(aaaa" in w
                     and "is not a recognised colour" in w]
            assert len(notes) == 1, caught
            assert len(notes[0]) < 1000, len(notes[0])


class TestTheServedHalvesAreRepresentative:
    """Guards the pruning (WP-30 E): every served representative is a real
    type or row, and every pruned sweep still serves at least one."""

    def test_the_representatives_exist(self):
        assert set(_SERVED_TYPES) < set(_TYPES) and len(_SERVED_TYPES) == 6
        rows = {f"{o}({v})" for o, v, _, _ in _REGION}
        assert set(_REGION_SERVED) < rows and len(_REGION_SERVED) == 6

    @pytest.mark.parametrize("types", [
        _TYPES, ["rarea", "rbar", "area", "bar", "histogram"],
        ["lfitci", "qfitci", "lpolyci", "fpfitci"], sorted(_MARKER_TYPES)],
        ids=["all", "fill", "band", "markers"])
    def test_every_pruned_sweep_still_serves(self, types):
        assert [p for p in _types_by_mode(types) if p.values[1] == "served"]
