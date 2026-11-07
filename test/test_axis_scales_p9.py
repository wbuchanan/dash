"""
test_axis_scales_p9.py
WP-44 section 44-03: the xscale()/yscale() items of audit package 9 --
off fill (AX-7), the transform words twoway's graph fails on and scale
style() (AX-9), log axes over non-positive data (AX-11), range() on a
log axis (MS-14), minmax on an empty scale and spans that overflow
(DG-13).  The refusals (AX-9's transform words, AX-10's contradictory
transforms in one copy, DG-13's overflow) are Stata-side and are pinned
in test/test_option_validation.cscript (Q4403-2, Q4403-6, Q4403-12).

The truth is test/fixtures/axis_scale_truth.json
(scripts/extract_axis_scale_truth.do, StataNow 19.5, stcolor): each
key's rc and error line, and for a drawn graph its plot region, x and y
labels, grid rows and columns and the lines on the region's edges.

Run with:  pytest test/test_axis_scales_p9.py -q -n0
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402
from conftest import make_data_json, render_models  # noqa: E402
from test_display_format_sites import js_texts  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "axis_scale_truth.json"),
          encoding="utf-8") as _fh:
    _G = json.load(_fh)["graphs"]
_FORMATS = {"weight": "%8.0gc", "mpg": "%8.0g", "z": "%9.0g"}


def _write(spec):
    tag = next(tb._SEQ)
    sp = os.path.join(tb._TMP, "as_spec_%d.json" % tag)
    dp = os.path.join(tb._TMP, "as_data_%d.json" % tag)
    df = tb._frame("auto")
    df = df.assign(z=df["mpg"] - 25.0)
    d = tb._truth()["data"]
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, d["auto_value_labels"],
                                 d["auto_value_label_names"], tb._LABELS), fh)
    return tag, sp, dp


#: Stata's own style files, on the ado-path dash.ado passes (scheme_dirs).
_BASE = "/Applications/StataNow/ado/base"
_needs_base = pytest.mark.skipif(
    not os.path.isdir(os.path.join(_BASE, "style")),
    reason="Stata's style files are not here")


def _figs(mode, plots, go=None, scheme="", base=False):
    """The first panel of the page *plots* and graph options *go* draw
    over auto (with ``z = mpg - 25``), and the notes it printed; under
    *scheme*, with Stata's style files on the ado-path when *base*."""
    spec = tda._spec(plots, go or {}, scheme=scheme, formats=_FORMATS)
    if base:
        spec["build_options"]["scheme_dirs"] = [_BASE]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tag, sp, dp = _write(spec)
        if mode == "saved":
            r = render_models(dr.DashRenderer(sp, dp))
            figs = tb._panels(list(r.figures.values()))
        else:
            from bokeh.document import Document
            ap = os.path.join(tb._TMP, "as_app_%d.py" % tag)
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = tb.load_app(ap, "_as_app_%d" % tag, draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = tb._panels(tb._figs_of(doc.roots))
    return figs[0], [str(x.message) for x in w]


def _labels(key, letter):
    """twoway's axis labels of a fixture row, the axis title left out."""
    t = list(_G[key][letter])
    return [s for s in t if not s[:1].isalpha()]


def _drawn(f, letter):
    """The texts the page writes for the axis's ticks."""
    ax = tda._axis(f, letter)
    ticks = tda._ticks(f, letter)
    ov = {float(k): v for k, v in dict(ax.major_label_overrides or {}).items()}
    if not ticks:
        return []
    texts = js_texts(ax.formatter, ticks, "tick") if not all(
        float(t) in ov for t in ticks) else [None] * len(ticks)
    return [ov.get(float(t), s) for t, s in zip(ticks, texts)]


# ---------------------------------------------------------------------------
# AX-7: off fill keeps the axis's space
# ---------------------------------------------------------------------------

_CLEAR = "#00000000"


@pytest.mark.parametrize("mode", _MODES)
class TestOffFill:
    @pytest.mark.parametrize("letter", ["y", "x"])
    def test_space_kept(self, mode, letter):
        """xscale(off fill)/yscale(off fill) keep the axis's space, as
        twoway's plot region keeps the plain graph's edge (ax7_off_fill,
        ax7_x_off_fill), and nothing of the axis paints: the axis stays
        laid out with no line, ticks, labels or title."""
        pre = "" if letter == "y" else "x_"
        edge = "left" if letter == "y" else "bottom"
        plain = _G["ax7_plain"]["plotregion"][edge]
        assert _G["ax7_%soff_fill" % pre]["plotregion"][edge] == plain
        assert _G["ax7_%soff" % pre]["plotregion"][edge] != plain
        assert _G["ax7_%soff_fill" % pre][letter] == []
        f, msgs = _figs(mode, [P("scatter", "mpg", "weight")],
                        {letter + "scale": "off fill"})
        ax = tda._axis(f, letter)
        assert ax.visible is True
        assert ax.axis_line_color is None
        assert ax.major_tick_line_color is None
        assert ax.minor_tick_line_color is None
        assert ax.major_label_text_color == _CLEAR
        assert ax.axis_label_text_color == _CLEAR
        assert ax.major_tick_out > 0
        assert not [m for m in msgs if "fill" in m], msgs

    def test_off_alone_unchanged(self, mode):
        """off without fill still hides the axis and takes its space."""
        f, _m = _figs(mode, [P("scatter", "mpg", "weight")],
                      {"yscale": "off"})
        assert tda._axis(f, "y").visible is False

    def test_fill_alone_is_the_plain_axis(self, mode):
        """fill without off draws the plain axis (ax7_fill)."""
        assert _G["ax7_fill"]["y"] == _G["ax7_plain"]["y"]
        f, _m = _figs(mode, [P("scatter", "mpg", "weight")],
                      {"yscale": "fill"})
        ax = tda._axis(f, "y")
        assert ax.visible is True
        assert ax.major_label_text_color != _CLEAR

    def test_later_label_colours_stay_clear(self, mode):
        """A label or title colour given elsewhere does not paint an off
        fill axis."""
        f, _m = _figs(mode, [P("scatter", "mpg", "weight")],
                      {"yscale": "off fill", "ylabel": ", labcolor(red)",
                       "ytitle": "Mileage, color(blue)"})
        ax = tda._axis(f, "y")
        assert ax.major_label_text_color == _CLEAR
        assert ax.axis_label_text_color == _CLEAR


def test_scale_look_reads_fill():
    """_dash_scale_look's ``fill``: the last of fillspace/nofillspace in
    the copy, any abbreviation."""
    assert dr._dash_scale_look("off fill")["fill"] is True
    assert dr._dash_scale_look("off fillspace")["fill"] is True
    assert dr._dash_scale_look("off fill nofill")["fill"] is False
    assert dr._dash_scale_look("off")["fill"] is False


# ---------------------------------------------------------------------------
# AX-9 (ruling D75): the transform words; scale style()
# ---------------------------------------------------------------------------

def _grid_on(f, dim):
    from bokeh.models import Grid
    gs = [g for g in list(f.renderers) + list(f.center)
          if isinstance(g, Grid) and g.dimension == dim]
    return any(g.visible and g.grid_line_color is not None for g in gs)


@pytest.mark.parametrize("mode", _MODES)
class TestTransformWords:
    @pytest.mark.parametrize("word", ["noatanh", "nologit", "nolog1m"])
    def test_no_forms_silent(self, mode, word):
        """A no form alone draws the plain graph in twoway (ax9_noatanh,
        ax9_nolog1m_x) and is taken with no note; the axis is the plain
        one."""
        assert _G["ax9_noatanh"]["y"] == _G["ax7_plain"]["y"]
        f0, _m = _figs(mode, [P("scatter", "mpg", "weight")])
        f, msgs = _figs(mode, [P("scatter", "mpg", "weight")],
                        {"yscale": word})
        assert not [m for m in msgs if word in m], msgs
        assert tda._ticks(f, "y") == tda._ticks(f0, "y")
        assert type(tda._axis(f, "y")).__name__ == "LinearAxis"


def test_the_help_sentence():
    """The xscale()/yscale() paragraph says log is the only transform and
    that atanh, logit and log1m are refused as twoway's graph refuses
    them (ruling D75)."""
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8") as fh:
        h = " ".join(fh.read().split())
    assert ("{cmd:log} is the only transform a scale takes: {cmd:atanh}, "
            "{cmd:logit} and {cmd:log1m}") in h
    assert "{cmd:unrecognized command}, {cmd:r(199)}" in h


def _sfigs(mode, go):
    """_figs under stcolor (the fixture's scheme) with Stata's files."""
    return _figs(mode, [P("scatter", "mpg", "weight")], go,
                 scheme="stcolor", base=True)


@_needs_base
@pytest.mark.parametrize("mode", _MODES)
class TestScaleStyle:
    def test_vertical_nogrid(self, mode):
        """yscale(style(vertical_nogrid)) draws no y grid and keeps the x
        grid, as twoway draws it (ax9_style_nogrid: no grid row, the
        plain graph's columns), with no note."""
        assert _G["ax9_style_nogrid"]["hgrid"] == 0
        assert _G["ax9_style_nogrid"]["vgrid"] == _G["ax7_plain"]["vgrid"]
        assert _G["ax7_plain"]["hgrid"] > 0
        f, msgs = _sfigs(mode, {"yscale": "style(vertical_nogrid)"})
        assert not _grid_on(f, 1)
        assert _grid_on(f, 0)
        assert not [m for m in msgs if "style" in m], msgs

    def test_horizontal_noline(self, mode):
        """xscale(style(horizontal_noline)) draws no x axis line and, as
        its file names a grid key no scheme declares, no x grid, with
        twoway's note for the key (ax9_style_noline)."""
        row = _G["ax9_style_noline"]
        assert row["bottom_line"] == [] and row["vgrid"] == 0
        assert any("draw_major__nl_hgrid not found in scheme" in n
                   for n in row["notes"])
        f, msgs = _sfigs(mode, {"xscale": "style(horizontal_noline)"})
        assert tda._axis(f, "x").axis_line_color is None
        assert not _grid_on(f, 0)
        assert _grid_on(f, 1)
        assert [m for m in msgs
                if "yesno draw_major__nl_hgrid not found in scheme" in m]

    def test_unknown_notes(self, mode):
        """An unknown name is twoway's named-style note (ax9_style_bogus)
        and the plain axis."""
        assert any("bogus_style not found in class axisstyle" in n
                   for n in _G["ax9_style_bogus"]["notes"])
        f, msgs = _sfigs(mode, {"yscale": "style(bogus_style)"})
        assert [m for m in msgs
                if "bogus_style not found in class axisstyle" in m], msgs
        assert _grid_on(f, 1)

    def test_explicit_wins(self, mode):
        """An explicit label sub-option after the style's wins:
        ylabel(, grid) beside yscale(style(vertical_nogrid)) draws the
        grid."""
        f, _m = _sfigs(mode, {"yscale": "style(vertical_nogrid)",
                              "ylabel": ", grid"})
        assert _grid_on(f, 1)


@_needs_base
def test_scale_style_expand():
    """_dash_scale_style_expand: the value less its style(), the style's
    scale tokens first; the label tokens apart; None with no style()."""
    sp = dr.SchemeParser("stcolor", ado_dirs=(_BASE,))
    v, lab = dr._dash_scale_style_expand(
        "style(horizontal_noline) log", sp, "x", note=False)
    assert v == "noline log" and lab == ["nogrid"]
    v, lab = dr._dash_scale_style_expand("sty(vertical_nogrid)", sp, "y")
    assert v == "" and lab == ["nogrid"]
    assert dr._dash_scale_style_expand("log", sp, "y") is None


def test_label_tokens_first():
    """_dash_label_tokens_first puts the tokens before the explicit
    sub-options and keeps the rule."""
    assert dr._dash_label_tokens_first("", ["nogrid"]) == ", nogrid"
    assert dr._dash_label_tokens_first(
        "#5, labsize(small)", ["nogrid"]) == "#5, nogrid labsize(small)"
    assert dr._dash_label_tokens_first('10 "a, b" 20', ["grid"]) == \
        '10 "a, b" 20, grid'


# ---------------------------------------------------------------------------
# AX-10: two transform words in one copy (Stata side: Q4403-6)
# ---------------------------------------------------------------------------

def test_the_exclusive_sentence():
    """The help states twoway's refusal of two transform words in one copy
    and the merge across copies (ax10_*: yscale(log nolog) "only one of
    options nolog or log is allowed", yscale(log) yscale(nolog) drawn)."""
    assert _G["ax10_log_nolog"]["error"] == \
        "only one of options nolog or log is allowed"
    assert _G["ax10_across"]["rc"] == 0
    assert _G["ax10_log_log"]["error"] == \
        "only one of options log or log1m is allowed"
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8") as fh:
        h = " ".join(fh.read().split())
    assert ("Two transform words in one copy ({cmd:yscale(log nolog)}, "
            "{cmd:yscale(atanh log)}, and {cmd:yscale(log log)}") in h
    assert ("{cmd:twoway}'s \"only one of options ... is allowed\"; across "
            "copies the last counts") in h


# ---------------------------------------------------------------------------
# AX-11: a log axis over non-positive data
# ---------------------------------------------------------------------------

def _ticks_of(key, letter="y"):
    """twoway's tick values of a fixture row (its labels as numbers)."""
    return [float(s.replace(",", "")) for s in _labels(key, letter)]


def _moved(mode, plots, go, filt, kind, value):
    """The first panel after a filter move, on the page _figs builds."""
    spec = tda._spec(plots, go or {}, filt=filt, formats=_FORMATS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tag, sp, dp = _write(spec)
        if mode == "saved":
            r = render_models(dr.DashRenderer(sp, dp))
            return tda._move_saved(r, kind, value)[0]
        from bokeh.document import Document
        ap = os.path.join(tb._TMP, "as_app_%d.py" % tag)
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = tb.load_app(ap, "_as_app_%d" % tag, draw=False)
        doc = Document()
        mod.make_document(doc)
        return tda._move_served(doc, kind, value)[0]


@pytest.mark.parametrize("mode", _MODES)
class TestLogTicks:
    def test_nonpositive(self, mode):
        """A log axis over values at or below 0 is ticked as twoway ticks
        it: natscale over every finite value, the ticks at or below 0 left
        out -- gen z = mpg - 25, scatter z weight, yscale(log) labels 10
        20 (ax11_c20), where dash ticked the positive values alone (5 10
        15).  Under ylabel(#5) twoway also writes a 0 label off its scale
        (ax11_with_n: 0 10 20); a log axis cannot place 0, so dash draws
        10 20 (the degenerate picture is documented, ruling A-5)."""
        assert _ticks_of("ax11_c20") == [10.0, 20.0]
        assert _ticks_of("ax11_with_n") == [0.0, 10.0, 20.0]
        f, _m = _figs(mode, [P("scatter", "z", "weight")], {"yscale": "log"})
        assert tda._ticks(f, "y") == [10.0, 20.0]
        f, _m = _figs(mode, [P("scatter", "z", "weight")],
                      {"yscale": "log", "ylabel": "#5"})
        assert tda._ticks(f, "y") == [v for v in _ticks_of("ax11_with_n")
                                      if v > 0]

    def test_positive_data_unchanged(self, mode):
        """A log axis over positive values keeps twoway's ticks
        (ax11_positive: 10 20 30 40) and its hull keeps positive values."""
        f, _m = _figs(mode, [P("scatter", "mpg", "weight")],
                      {"yscale": "log"})
        assert tda._ticks(f, "y") == _ticks_of("ax11_positive")
        f, _m = _figs(mode, [P("scatter", "z", "weight")], {"yscale": "log"})
        rng = f.y_range
        assert min(rng.start, rng.end) > 0

    def test_after_a_move(self, mode):
        """After a filter move the log axis is ticked again over every
        finite value the rows kept draw (the saved page's dash_axis_finish
        under node, the served app's refinish)."""
        f = _moved(mode, [P("scatter", "z", "weight")], {"yscale": "log"},
                   "foreign, type(dropdown)", "Select", "Domestic")
        df = tb._frame("auto")
        z = (df["mpg"] - 25.0)[df["foreign"] == 0]
        want = dr._dash_axis_count_ticks(float(z.min()), float(z.max()), 5,
                                         "log")
        # Over -13 to 9: 5 10; over the positive values alone, 2 4 6 8.
        assert want == [5.0, 10.0]
        pos = z[z > 0]
        assert dr._dash_axis_count_ticks(float(pos.min()), float(pos.max()),
                                         5, "log") != want
        assert tda._ticks(f, "y") == want


def test_the_log_rule_sentence():
    """The log rule paragraph says ticks are over every finite value and
    that twoway's degenerate picture is not copied, with its Differences
    line (ruling A-5)."""
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8") as fh:
        h = " ".join(fh.read().split())
    assert ("a log axis is ticked over every finite value its layers draw, "
            "as {cmd:twoway} ticks it, and the ticks at or below 0 are "
            "left out") in h
    assert ("{help dash##log_nonpositive:item 20} under Differences from "
            "twoway") in h
    assert "{marker log_nonpositive}" in h


# ---------------------------------------------------------------------------
# MS-14: range() on a log axis
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestLogRange:
    @pytest.mark.parametrize("key, letter, plots, go", [
        ("ms14_b04", "x", [P("scatter", "mpg", "weight")],
         {"xscale": "range(1000) log"}),
        ("ms14_b2", "y", [P("scatter", "weight", "mpg")],
         {"yscale": "log range(1000 20000)"}),
        ("ms14_with_n", "y", [P("scatter", "weight", "mpg")],
         {"yscale": "log range(1000 20000)", "ylabel": "#5"}),
    ])
    def test_no_end_tick(self, mode, key, letter, plots, go):
        """range() on a log axis adds no tick at the range's end: B04
        (xscale(range(1000)) xscale(log)) and b2 are ticked 2,000-5,000
        over the data, as twoway ticks them; under ylabel(#5) the range
        joins the ticks (0 5,000 ... 20,000 in twoway, whose 0 a log axis
        cannot place)."""
        f, _m = _figs(mode, plots, go)
        want = [v for v in _ticks_of(key, letter) if v > 0]
        assert tda._ticks(f, letter) == want
