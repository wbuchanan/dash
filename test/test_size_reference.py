"""
test_size_reference.py -- the size reference follows xsize()/ysize()
(WP-31 E11, section 32; DECISIONS D29).

Before: absolute sizes (#pt, #in, #cm and the schemes' #-pt sizes) were
converted at the scheme's graphsize, the smaller side, whatever xsize()
and ysize() said.  twoway's relative sizes are relative to the smaller
side of the graph as drawn (test/fixtures/sizing_truth.json ref_def,
ref_84, ref_48, ref_88: title(size(5)) is 144 SVG units on a 5.5 x 4,
8 x 4 or 4 x 8 inch graph and 288 on 8 x 8), so an absolute size is a
smaller share of a larger graph.  dash draws a relative size at 2.88 pt
per unit on a figure the browser sizes, so it converts an absolute size
at min(xsize, ysize) of each figure, the scheme's side standing in for
one not given; scale() multiplies afterwards and leaves the reference.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from test_sizing import _MODES, _figure, _pt  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "sizing_truth.json")


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _title_pt(f):
    return _pt(f.title.text_font_size)


class TestReference:
    def test_twoway_scales_relative_sizes_with_the_smaller_side(self):
        d = _truth()
        for k in ("ref_def", "ref_84", "ref_48", "ref_88"):
            c = d[k]["canvas"]
            # 10 SVG units a point; the title's share of the smaller side.
            assert d[k]["title_size"] / min(c["w"], c["h"]) \
                == pytest.approx(0.05, abs=.001), k

    def test_the_reference(self):
        f = dr._dash_ref_in
        assert f({}, 5.5, 4.0) is None
        assert f({"xsize": "8", "ysize": "8"}, 5.5, 4.0) == 8.0
        assert f({"xsize": "8", "ysize": "4"}, 5.5, 4.0) == 4.0
        assert f({"ysize": "8"}, 5.5, 4.0) == 5.5
        assert f({"xsize": "x"}, 5.5, 4.0) is None
        assert f({"xsize": "-2", "ysize": "6"}, 5.5, 4.0) == 5.5

    @pytest.mark.parametrize("mode", _MODES)
    def test_sizes_follow_the_reference(self, mode, tmp_path):
        a = _figure(mode, tmp_path, {"title": '"T", size(14pt)'})
        b = _figure(mode, tmp_path, {"title": '"T", size(14pt)',
                                     "xsize": "8", "ysize": "8"})
        r = _figure(mode, tmp_path, {"title": '"T", size(5)',
                                     "xsize": "8", "ysize": "8"})
        assert dr.OptionTranslator.size_ref_of(a) == 4.0
        assert dr.OptionTranslator.size_ref_of(b) == 8.0
        assert _title_pt(b) == pytest.approx(_title_pt(a) / 2, abs=.01)
        # A relative size is the same share of every figure.
        assert _title_pt(r) == pytest.approx(14.4, abs=.01)

    @pytest.mark.parametrize("mode", _MODES)
    def test_scale_leaves_the_reference(self, mode, tmp_path):
        a = _figure(mode, tmp_path, {"title": '"T", size(14pt)',
                                     "xsize": "8", "ysize": "8"})
        b = _figure(mode, tmp_path, {"title": '"T", size(14pt)',
                                     "xsize": "8", "ysize": "8",
                                     "scale": "2"})
        assert dr.OptionTranslator.size_ref_of(b) == 8.0
        assert _title_pt(b) == pytest.approx(2 * _title_pt(a), abs=.01)

    def test_the_scheme_is_never_changed(self, tmp_path):
        """The figure's reference is a copy of the scheme's, made once per
        reference; the build's scheme keeps its own."""
        s = dr.SchemeParser.resolve_or_fallback("s2color", "test")
        cache = {}
        c8 = dr._dash_scheme_at_ref(s, 8.0, cache)
        assert c8 is not s and c8.size_ref_in == 8.0 and s.size_ref_in == 4.0
        assert dr._dash_scheme_at_ref(s, 8.0, cache) is c8
        assert dr._dash_scheme_at_ref(s, None, cache) is s
        assert dr._dash_scheme_at_ref(s, 4.0, cache) is s
