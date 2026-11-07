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


def _figs(mode, plots, go=None):
    """The first panel of the page *plots* and graph options *go* draw
    over auto (with ``z = mpg - 25``), and the notes it printed."""
    spec = tda._spec(plots, go or {}, formats=_FORMATS)
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
