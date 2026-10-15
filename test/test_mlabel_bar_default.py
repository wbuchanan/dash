"""
test_mlabel_bar_default.py -- a bar's marker labels default to 12 o'clock,
as twoway draws them (WP-31 C15).

The defect (measured at 0742dba): ``dash bar mpg weight, mlabel(make)``
put the labels at 3 o'clock, the applier's default for every type.

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json bardefault.*): the first plot's
label position is 12 on bar and rbar (labelstyle p#bar, ``clockdir pbar
12``) and 3 on scatter.  rbar draws no labels at all (its SVG holds no
"AMC" text), as dash draws none, so bar alone moves.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from test_varlabel_options import T, MODES, figs, sc  # noqa: E402
from test_msangle_mlabstyle import _labelsets  # noqa: E402


def _anchor(fs):
    [ls] = _labelsets(fs)
    return ls.text_align, ls.text_baseline


def _clock(n):
    return dr.GlyphMapper._MLABEL_CLOCK[n][2]


class TestBarDefault:

    def test_the_fixture(self):
        b = T["bardefault"]
        assert [b[k]["label_position"] for k in ("bar", "rbar", "scatter")] \
            == ["12", "12", "3"]
        assert not [t for t in b["rbar"]["texts"] if "AMC" in t["text"]]

    @pytest.mark.parametrize("mode", MODES)
    def test_bar_and_rbar_are_12(self, mode, tmp_path):
        fs, _ = figs(mode, tmp_path, [{"type": "bar", "yvar": "mpg",
                                       "xvar": "weight",
                                       "options": {"mlabel": "make"}}])
        assert _anchor(fs) == _clock(12)
        # mlabposition() still wins.
        fs, _ = figs(mode, tmp_path, [{"type": "bar", "yvar": "mpg",
                                       "xvar": "weight",
                                       "options": {"mlabel": "make",
                                                   "mlabposition": "3"}}])
        assert _anchor(fs) == _clock(3)
        # rbar draws no labels, as twoway.
        fs, _ = figs(mode, tmp_path, [{"type": "rbar", "yvar1": "lo",
                                       "yvar2": "hi", "xvar": "weight",
                                       "options": {"mlabel": "make"}}])
        assert _labelsets(fs) == []

    @pytest.mark.parametrize("mode", MODES)
    def test_scatter_stays_3(self, mode, tmp_path):
        fs, _ = figs(mode, tmp_path, [sc(mlabel="make")])
        assert _anchor(fs) == _clock(3)
