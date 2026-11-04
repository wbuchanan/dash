"""
test_added_text_box.py -- text()'s alignment() typed through dash, its box
and line options, and a global's =exp in a graph's text (WP-43 section
43-06, LT-11 and LT-20).

The defects: dash.ado named ``text(..., alignment())`` in a note and never
handed it to the drawing (LT-11), though the renderer could draw it; and
text()'s width(), height(), linegap(), lstyle(), lpattern() and lalign()
(and their bl forms) were named and not drawn, and a global holding
```=1+1'`` was drawn as written where twoway draws 2 (LT-20).

twoway's rule: test/fixtures/added_text_box_truth.json, written by
scripts/extract_added_text_box_truth.do (stcolor, auto, ``twoway scatter
mpg weight, text(30 3000 "Peak" "two", <opts>)``).
"""
import json
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_added_text as tat  # noqa: E402

MODES = ("saved", "served")

with open(os.path.join(_HERE, "fixtures", "added_text_box_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
P = TRUTH["probes"]


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program(src, head, end):
    """The text of one ado program or Mata function: from *head* to the
    first *end* after it."""
    a = src.index(head)
    return src[a:src.index(end, a)]


def _block(text, opts, mode, caught=None):
    """The Labels one text(30 3000 "Peak" "two", <opts>) record draws."""
    spec = tat._spec([tat._at(30, 3000, ["Peak", "two"], opts)])
    return [lab for f in tat._figs(spec, mode, None, caught)
            for lab in tat._labels(f)]


def _size_px(lab):
    return tat._pt(lab.text_font_size) * dr.OptionTranslator.PX_PER_PT


class TestTheFixture:

    def test_meta(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m[k], k
        assert m["source"] == "scripts/extract_added_text_box_truth.do"
        assert m["viewbox"] == [5400.0, 3240.0]

    def test_alignment_spellings(self):
        """twoway draws only the four full words; an abbreviation is
        named (class vertical_text) and drawn as bottom is drawn."""
        eq = TRUTH["_meta"]["al_equal"]
        assert {k: v for k, v in eq.items() if v} == {
            w: w for w in ("top", "middle", "bottom", "baseline")}
        for ab in ("t", "to", "mid", "bot", "base"):
            assert P["al_" + ab]["notes"] == [
                "(note:  named style %s not found in class vertical_text, "
                "default attributes used)" % ab]
            assert [t["y_px"] for t in P["al_" + ab]["texts"]] == \
                [t["y_px"] for t in P["al_bottom"]["texts"]]

    def test_alignment_shifts(self):
        """top and bottom raise the block 0.15 of its size above middle,
        baseline lowers it 0.15 (_DASH_ADDED_TEXT_VSHIFT)."""
        mid = P["al_middle"]["texts"][0]
        for w, k in dr._DASH_ADDED_TEXT_VSHIFT.items():
            got = P["al_" + w]["texts"][0]
            assert (mid["y_px"] - got["y_px"]) / mid["size"] == \
                pytest.approx(k, abs=0.003), w


class TestAlignmentRoute:

    def test_ado_and_mata(self):
        """alignment() leaves dash.ado's noted list and _dash_at_canon
        writes it for the drawing."""
        ado = _program(_read("dash.ado"), "program define _dash_at_opts",
                       "\nend")
        noted = ado[ado.index("local _nt \"\""):]
        noted = noted[:noted.index("{")]
        assert "alignment" not in noted.split()
        canon = _program(_read("dash_parse.mata"),
                         "string scalar _dash_at_canon()", "\n}")
        assert '" alignment("' in canon

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_name_is_drawn_as_bottom(self, mode):
        """An alignment twoway does not know is named in its words and
        drawn where bottom is drawn (al_t, al_bot: the fixture)."""
        caught = []
        (lab,) = _block("", "alignment(bot)", mode, caught)
        want = dr._DASH_ADDED_TEXT_VSHIFT["bottom"] * _size_px(lab)
        assert lab.y_offset == pytest.approx(want, abs=0.01)
        hits = [w for w in caught if "named style bot not found in class "
                "vertical_text, default attributes used" in w]
        assert len(hits) == 1, caught
