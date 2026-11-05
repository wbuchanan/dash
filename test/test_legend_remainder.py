"""The legend sub-options section 31 left named (WP-31 D4b, section 39).

Measured (test/fixtures/legend_remainder_truth.json, s2color, two keys in
one row): colgap() is the gap between the legend's columns -- colgap(0)
moves the second key 140 SVG units (4.8611 units, the scheme's
``legend_col_gap`` large) left, colgap(bogus) draws medium with a note;
legend(subtitle()) is drawn centred above the keys, under the title.

Drawn: colgap() is the Bokeh legend's spacing when its keys are in one
row (when they are in one column, rowgap() is, as before; a grid of both
has one Bokeh spacing, the row gap); subtitle() is a line of the legend's
title.  stacked, symplacement() and the legend's own note() and caption()
were named here (M17) and are drawn since WP-43 LT-21
(test_legend_keys.py); note() and caption() beside the legend's title()
stay named.
"""
import json
import os
import sys

import pytest
from bokeh.models import Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
import test_tabs_layout_edges as T

_FIXTURE = os.path.join(_HERE, "fixtures", "legend_remainder_truth.json")
_TRUTH = json.load(open(_FIXTURE))
MODES = ("saved", "served")


def _two(legend):
    sp = T._spec(["g1"])
    g = sp["graphs"][0]
    if legend:
        g["graph_options"]["legend"] = legend
    g["plots"].append({"type": "scatter", "yvar": "weight", "xvar": "mpg",
                       "options": {}})
    return sp


def _legend(mode, legend):
    roots, msgs = T._root(mode, _two(legend))
    lgs = [lg for r in roots for lg in r.select({"type": Legend})]
    return lgs[0], msgs


def _px(units):
    O = dr.OptionTranslator
    return int(round(units * O.PT_PER_RS * O.PX_PER_PT))


class TestTheFixture:
    def test_meta(self):
        m = _TRUTH["_meta"]
        assert {"born_date", "dash_commit", "extracted", "source",
                "stata_version"} <= set(m)
        assert m["source"] == "scripts/extract_legend_remainder_truth.do"

    def test_colgap_is_the_column_gap(self):
        base, zero = _TRUTH["base"], _TRUTH["colgap_zero"]
        assert base["col_gap"] == 4.8611 and zero["col_gap"] == 0
        def gap(r):
            return r["key_texts"][1]["x"] - r["key_texts"][0]["x"]
        dx = gap(base) - gap(zero)
        assert abs(dx - 4.8611 * 28.8) < 2, dx
        # rows are untouched
        assert base["key_texts"][0]["y"] == zero["key_texts"][0]["y"]


class TestColgap:
    @pytest.mark.parametrize("mode", MODES)
    def test_default_row_takes_the_column_gap(self, mode):
        lg, _ = _legend(mode, "")
        assert lg.spacing == _px(4.8611), lg.spacing

    @pytest.mark.parametrize("mode", MODES)
    def test_colgap_zero(self, mode):
        lg, msgs = _legend(mode, "colgap(0)")
        assert lg.spacing == 0
        assert not [m for m in msgs if "colgap" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_one_column_keeps_the_row_gap(self, mode):
        lg, _ = _legend(mode, "cols(1) colgap(0)")
        assert lg.spacing == _px(1.3888), lg.spacing

    def test_bogus_is_noted(self):
        assert _TRUTH["colgap_bogus"]["log"] == [
            "(note:  named style bogus not found in class gsize, default "
            "attributes used)"]
        lg, msgs = _legend("saved", "colgap(bogus)")
        assert lg.spacing == _px(3.8194)
        assert any("colgap(bogus)" in m for m in msgs), msgs


class TestSubtitle:
    @pytest.mark.parametrize("mode", MODES)
    def test_alone(self, mode):
        assert "Sub" in [t["text"] for t in _TRUTH["lsubtitle"]["texts"]]
        lg, msgs = _legend(mode, 'subtitle("Sub")')
        assert lg.title == "Sub"
        # Flipped: was drawn at the key text's size; twoway's
        # leg_title/leg_subtitle text boxes (WP-43 LT-1): subheading.
        sc = dr.SchemeParser("s2color")
        assert lg.title_text_font_size == sc.textbox_style("subheading")[0]
        assert not [m for m in msgs if "subtitle" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_under_the_title(self, mode):
        ys = {t["text"]: t["y"] for t in _TRUTH["lall"]["texts"]}
        assert ys["Ttl"] < ys["Sub"]
        lg, _ = _legend(mode, 'title("Ttl") subtitle("Sub")')
        assert lg.title == "Ttl\nSub"


class TestStillNamed:
    """M17: no Bokeh Legend property draws these; each stays in the note."""

    # Flipped: stacked is drawn as twoway draws it (WP-43 LT-21,
    # test_legend_keys.py::TestKeyOrder).
    # Flipped (WP-43 LT-21): symplacement() is drawn (test_legend_keys.py::TestSymplacement).
    # Flipped (WP-43 LT-21): the legend's note() and caption() are drawn (test_legend_keys.py::TestNoteAndCaption); beside its title() they stay named.
    @pytest.mark.parametrize("opt", ['note("Nt")', 'caption("Cap")'])
    def test_named(self, opt):
        _, msgs = _legend("saved", 'title("T") ' + opt)
        word = opt.split("(")[0]
        assert any("legend()" in m and word in m for m in msgs), msgs

    def test_measured(self):
        assert (_TRUTH["stacked"]["key_marks"][0]["cy"]
                < _TRUTH["stacked"]["key_texts"][0]["y"] - 100)
        assert (_TRUTH["symp_n"]["key_marks"][0]["cy"]
                < _TRUTH["base"]["key_marks"][0]["cy"])
        nt = [t for t in _TRUTH["lnote"]["texts"] if t["text"] == "Nt"][0]
        assert nt["y"] > _TRUTH["lnote"]["key_texts"][0]["y"]
