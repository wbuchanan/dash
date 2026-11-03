"""A colour list of quoted RGB colours is read colour by colour (WP-42 CV-17).

colorlist() and contour's ccolors() were split into words, so
``colorlist("68 1 84" "70 50 126" ...)`` became the words ``"68``, ``1``,
``84"``, ...: none a colour, every level black, and the note 'named style
"68 not found in class color'.  twoway reads each quoted colour whole
(test/fixtures/colorlist_truth.json, scripts/extract_colorlist_truth.do):

* L8, the corpus example ex-feature_tour-eaf70b99: the eight listed colours,
  #440154 ... #fde725, on the markers and the key;
* LM, ``colorlist("255 0 0" green "0 0 255")`` under colordiscrete: the
  first three levels red, green (#008000) and blue;
* C3, contour ``ccolors("255 0 0" "0 255 0" "0 0 255")``: the bands red,
  lime and blue.
"""
import json
import os
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tbk  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_colorvar_key import _surface  # noqa: E402

_MODES = ("saved", "served")
_FIX = os.path.join(_HERE, "fixtures", "colorlist_truth.json")
#: Everything an exported graph fills that is not a level colour: the
#: graph and plot regions, the marker outlines and text.
_CHROME = {"#000000", "#ffffff", "#eaf2f3"}
_L8 = ('"68 1 84" "70 50 126" "54 92 141" "39 127 142" "31 161 135" '
       '"74 193 109" "160 218 57" "253 231 37"')


def _auto():
    """The parity suite's frame (mpg, weight, price, rep78, ...)."""
    return make_data_json(tp._DF, tp._VALUE_LABELS, tp._LABEL_NAMES)


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)["probes"]


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb.split())


def _key_colours(roots):
    cells = [m for r in roots for m in r.references()
             if "dash_key_cell" in (getattr(m, "tags", None) or [])]
    assert len(cells) == 1, cells
    return [str(c).lower() for c in cells[0]._dash_keycell["src"].data["c"]]


def _marker_palette(roots):
    for r in roots:
        for m in r.references():
            if type(m).__name__ != "GlyphRenderer":
                continue
            fc = getattr(m.glyph, "fill_color", None)
            tr = getattr(fc, "transform", None)
            pal = getattr(tr, "palette", None)
            if pal:
                return [str(c).lower() for c in pal]
    return None


class TestTheFixture:

    def test_l8_draws_the_eight_listed_colours(self):
        rec = _truth()["L8"]
        assert rec["rc"] == 0 and not rec["lines"]
        drawn = set(rec["style_fills"]) - _CHROME
        assert drawn == {_hex(t.strip('"')) for t in
                         dr._dash_by_tokens(_L8, top_quotes=True)}

    def test_lm_and_c3(self):
        p = _truth()
        assert {"#ff0000", "#008000", "#0000ff"} <= set(p["LM"]["fills"])
        assert set(p["C3"]["style_fills"]) - _CHROME == {
            "#ff0000", "#00ff00", "#0000ff"}


class TestTheTokens:

    def test_a_quoted_colour_is_one_word(self):
        assert dr._dash_by_tokens('"68 1 84" red `"0 0 255"\'',
                                  top_quotes=True) == [
            '"68 1 84"', "red", '`"0 0 255"\'']

    def test_the_default_is_unchanged(self):
        # by(), legend() and the other option lists keep their reading.
        assert dr._dash_by_tokens('"a b" title("c d")') == [
            '"a', 'b"', 'title("c d")']


@pytest.mark.parametrize("mode", _MODES)
class TestColorlist:

    def test_the_corpus_example(self, mode):
        spec = tp._spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                          "options": {"colorvar": "price",
                                      "colorlevels": "8",
                                      "colorlist": _L8}}])
        roots, notes, _o = tbk._build(mode, spec, _auto())
        want = [_hex(t.strip('"'))
                for t in dr._dash_by_tokens(_L8, top_quotes=True)]
        assert set(want) == set(_truth()["L8"]["style_fills"]) - _CHROME
        assert _key_colours(roots) == want
        assert _marker_palette(roots)[:8] == want
        assert not [n for n in notes if "class color" in n], notes

    def test_named_and_quoted(self, mode):
        spec = tp._spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                          "options": {"colorvar": "rep78",
                                      "colordiscrete": "yes",
                                      "colorlist":
                                          '"255 0 0" green "0 0 255"'}}])
        roots, notes, _o = tbk._build(mode, spec)
        assert _key_colours(roots)[:3] == ["#ff0000", "#008000", "#0000ff"]
        assert not [n for n in notes if "class color" in n], notes


@pytest.mark.parametrize("mode", _MODES)
def test_ccolors(mode):
    spec = tp._spec([{"type": "contour", "zvar": "temp", "yvar": "lat",
                      "xvar": "lon",
                      "options": {"levels": "3",
                                  "ccolors": '"255 0 0" "0 255 0" "0 0 255"'}}])
    roots, notes, _o = tbk._build(mode, spec, make_data_json(_surface()))
    assert _key_colours(roots)[:3] == ["#ff0000", "#00ff00", "#0000ff"]
    assert not [n for n in notes if "class color" in n], notes


def test_the_contour_helper():
    tr = dr.OptionTranslator(dr.SchemeParser("s2color"))
    got = dr._dash_contour_colours(
        {"ccolors": '"255 0 0" lime "0 0 255"'}, 3, dr.SchemeParser("s2color"),
        parse=lambda t: tr.parse_color_alpha(t, "ccolors")[0])
    assert [c.lower() for c in got] == ["#ff0000", "#00ff00", "#0000ff"]
