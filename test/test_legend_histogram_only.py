"""test_legend_histogram_only.py -- a histogram-only graph draws no legend,
as twoway draws none (WP-31 C13, GAPS3 C13).

GAPS3 C13: ``dash histogram mpg || histogram price`` drew a two-key
legend; twoway draws none.

Measured first (test/fixtures/legend_geometry_truth.json, written by
scripts/extract_legend_geometry_truth.do): the cause is not the plot type.
twoway's legend_g draws two keys whose text and style are the same as ONE
key, and a graph of one key draws no legend:

* hist_only: two histograms, both keyed "Density" in the one histogram
  colour -- one key, no legend (draw_view 0).
* hist_color: the same pair with color(red) on the second -- two keys, a
  legend.  So a "histogram-only" rule would be wrong.
* merge_pstyle: two scatters of mpg with pstyle(p1) -- one key, no legend;
  merge_style: the same with mcolor(red) on one -- two keys.
* merge_on / merge_order / merge_lab1_on / merge_lab2_on / merge_order2:
  the merged key is plot 1's: legend(on) draws it once, order(2 1) draws
  it once, label(1 "A") renames it, label(2 "B") changes nothing and
  order(2) draws no key -- the folded number is no key.
* hist_on: legend(on) still draws the one-key legend.
* merge_text, merge_override, merge_default_value, merge_mlabel,
  hist_scales: the rule is the plots' look, not their text -- two plots of
  one type that look the same, neither given a style option of its own
  (even one equal to the default, msize(medium)), are one key whose text
  is their distinct texts joined by "/" ("Mileage (mpg)/Price",
  "Frequency/Percent"); mlabel() is not a style option.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "legend_geometry_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

HIST2 = [plot_for("histogram"), plot_for("histogram", var="price")]


def _p1(**o):
    o = dict(o, pstyle="p1")
    return plot_for("scatter", o, yvar="mpg", xvar="weight")


def _legend(mode, plots, legend=""):
    from bokeh.models import Legend
    go = {"legend": legend} if legend else {}
    figs, _ = tp._figures_in(mode, tp._spec(plots, {"scheme": "s2color"},
                                            go))
    assert len(figs) == 1
    lgs = [m for m in figs[0].select({"type": Legend})
           if str(m.name or "") != dr._COLORVAR_LEGEND_NAME]
    assert len(lgs) == 1
    return lgs[0]


def _text(it):
    lab = it.label
    return lab.get("value") if isinstance(lab, dict) else getattr(
        lab, "value", lab)


@pytest.mark.parametrize("mode", MODES)
class TestHistogramOnly:

    def test_no_legend(self, mode):
        assert TRUTH["hist_only"]["drawn"] == 0
        assert _legend(mode, HIST2).visible is False

    def test_on_forces(self, mode):
        assert TRUTH["hist_on"]["drawn"] == 1
        assert _legend(mode, HIST2, "on").visible is True

    def test_mixed_draws(self, mode):
        assert TRUTH["hist_mixed"]["drawn"] == 1
        plots = [plot_for("histogram"),
                 plot_for("scatter", yvar="mpg", xvar="mpg")]
        assert _legend(mode, plots).visible is True

    def test_two_scales_are_one_key(self, mode):
        """histogram mpg, freq || histogram mpg, percent: one key,
        "Frequency/Percent", so no legend (hist_scales)."""
        assert TRUTH["hist_scales"]["drawn"] == 0
        plots = [plot_for("histogram", {"frequency": "frequency"}),
                 plot_for("histogram", {"percent": "percent"})]
        assert _legend(mode, plots).visible is False

    def test_two_colours_draw(self, mode):
        assert TRUTH["hist_color"]["keys"] == 2
        plots = [plot_for("histogram"),
                 plot_for("histogram", {"color": "red"}, var="price")]
        assert _legend(mode, plots).visible is True


@pytest.mark.parametrize("mode", MODES)
class TestMerge:

    def test_same_text_and_style_is_one_key(self, mode):
        assert TRUTH["merge_pstyle"]["keys"] == 1
        assert TRUTH["merge_on"]["keys"] == 1
        assert _legend(mode, [_p1(), _p1()]).visible is False
        lg = _legend(mode, [_p1(), _p1()], "on")
        assert lg.visible is True
        assert len(lg.items) == 1
        assert len(lg.items[0].renderers) == 2
        assert list(lg.items[0].tags) == ["dash_key_numbers", "1", "2"]

    def test_texts_join_with_a_slash(self, mode):
        assert TRUTH["merge_text"]["label_1"] == "Mileage (mpg)/Price"
        lg = _legend(mode, [_p1(), plot_for("scatter", {"pstyle": "p1"},
                                            yvar="price", xvar="weight")],
                     "on")
        assert [_text(i) for i in lg.items] == ["mpg/price"]

    def test_a_style_option_keeps_a_key_apart(self, mode):
        """An explicit style option keeps the key apart even when the two
        look the same (merge_override, merge_default_value); mlabel() does
        not (merge_mlabel)."""
        assert TRUTH["merge_override"]["keys"] == 2
        assert TRUTH["merge_default_value"]["keys"] == 2
        assert TRUTH["merge_mlabel"]["keys"] == 1
        two = _legend(mode, [_p1(mcolor="red"), _p1(mcolor="red")])
        assert (two.visible, len(two.items)) == (True, 2)
        one = _legend(mode, [_p1(mlabel="make"), _p1(mlabel="make")])
        assert one.visible is False

    def test_different_style_keeps_two(self, mode):
        assert TRUTH["merge_style"]["keys"] == 2
        lg = _legend(mode, [_p1(), _p1(mcolor="red")])
        assert lg.visible is True
        assert len(lg.items) == 2


@pytest.mark.parametrize("mode", MODES)
class TestMergeKeepsNumbers:

    def test_order_and_label(self, mode):
        assert [t["text"] for t in TRUTH["merge_order"]["key_texts"]] == [
            "Mileage (mpg)"]
        assert [t["text"] for t in TRUTH["merge_lab1_on"]["key_texts"]] == [
            "A"]
        assert [t["text"] for t in TRUTH["merge_lab2_on"]["key_texts"]] == [
            "Mileage (mpg)"]
        assert not TRUTH["merge_order2"].get("key_texts")
        two = [_p1(), _p1()]
        assert [_text(i) for i in _legend(mode, two, "on order(2 1)").items
                ] == ["mpg"]
        assert [_text(i) for i in _legend(mode, two, 'on label(1 "A")').items
                ] == ["A"]
        assert [_text(i) for i in _legend(mode, two, 'on label(2 "B")').items
                ] == ["mpg"]
        assert [_text(i) for i in _legend(mode, two, "on order(2)").items
                ] == []


class TestKeySignature:

    def test_equal_glyphs_sign_alike(self):
        from bokeh.models import ColumnDataSource, GlyphRenderer, Scatter
        src = ColumnDataSource({"x": [1], "y": [2]})

        def r(**kw):
            return GlyphRenderer(data_source=src,
                                 glyph=Scatter(x="x", y="y", **kw))
        a = dr._dash_key_signature([r(fill_color="red", size=6)])
        b = dr._dash_key_signature([r(fill_color="red", size=6)])
        c = dr._dash_key_signature([r(fill_color="blue", size=6)])
        assert a == b != c
