"""test_legend_title_style.py -- legend(title()) and legend(subtitle()) are
drawn as twoway draws them (WP-43 section 43-01: LT-1, LT-15).

LT-1: twoway draws the legend's title and subtitle in the scheme's
``textboxstyle leg_title`` / ``leg_subtitle`` text boxes (heading and
subheading under s2color; stcolor's leg_title is legend_title, heading's
size in black), not in the key text's size and colour.

Ground truth: test/fixtures/legend_title_truth.json, written by
scripts/extract_legend_title_truth.do from twoway's SVG export (SVG px,
720 per inch).  ``style_<scheme>`` holds T's and S's size and fill and the
key text's size for ``legend(title("T") subtitle("S"))``.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_legend_geometry as G  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "legend_title_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "scheme_truth.json"),
          encoding="utf-8") as _fh:
    SCHEMES = {k: v for k, v in json.load(_fh).items() if k != "_meta"}

STYLE_SCHEMES = ("stcolor", "s2color", "s1mono", "economist", "meta")
EDGES = ("t1", "t2", "b1", "b2", "l1", "l2", "r1", "r2")


def _legend(mode, opt, scheme="s2color"):
    """``(legend, messages)`` of the two-scatter graph with legend(*opt*)."""
    fig, caught = G._build(mode, G.TWO, opt, scheme=scheme)
    return G._legend(fig), caught


def _pt(size):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(pt|px)\s*", str(size))
    assert m, size
    v = float(m.group(1))
    return v if m.group(2) == "pt" else v * 0.75


class TestTheFixture:

    def test_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_title_truth.do"
        keys = (["style_" + s for s in STYLE_SCHEMES]
                + ["control", "title_box", "title_box_margin", "title_just",
                   "title_tstyle", "sub_style", "sub_under", "block_box",
                   "scale_block"]
                + ["title_pos_%d" % k for k in (0, 3, 5, 6, 9, 12)])
        for k in keys:
            assert TRUTH[k]["rc"] == 0, k
        for e in EDGES:
            assert TRUTH["edge_" + e]["rc"] == 198, e
            assert TRUTH["edge_" + e]["first_line"] == (
                "option %stitle() not allowed" % e)


class TestSchemeStyles:

    @pytest.mark.parametrize("scheme", sorted(SCHEMES))
    def test_each_scheme(self, scheme):
        sc = dr.SchemeParser(scheme)
        truth = SCHEMES[scheme]
        for box, dflt in (("title", "heading"), ("subtitle", "subheading"),
                          ("note", "small_body"), ("caption", "body")):
            want = truth.get("textboxstyle_leg_" + box) or dflt
            assert sc.legend_text_styles[box] == want, (scheme, box)
        assert sc._legend_text_style("bogus_box", "body") == "body"


class TestTitleStyle:

    @pytest.mark.parametrize("scheme", STYLE_SCHEMES)
    @pytest.mark.parametrize("mode", MODES)
    def test_scheme_style(self, mode, scheme):
        rec = TRUTH["style_" + scheme]
        lg, _ = _legend(mode, 'title("T")', scheme)
        sc = dr.SchemeParser(scheme)
        size, colour = sc.textbox_style(sc.legend_text_styles["title"])
        assert lg.title == "T"
        assert lg.title_text_font_size == size
        assert str(lg.title_text_color).lower() == str(colour).lower()
        assert str(lg.title_text_color).lower() == rec["T"]["fill"]
        want = rec["T"]["size"] / rec["key_size"]
        got = _pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
        assert abs(got / want - 1) < 0.02, (got, want)

    @pytest.mark.parametrize("scheme", STYLE_SCHEMES)
    @pytest.mark.parametrize("mode", MODES)
    def test_subtitle_alone(self, mode, scheme):
        rec = TRUTH["style_" + scheme]
        lg, msgs = _legend(mode, 'subtitle("S")', scheme)
        assert lg.title == "S"
        assert str(lg.title_text_color).lower() == rec["S"]["fill"]
        want = rec["S"]["size"] / rec["key_size"]
        got = _pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
        assert abs(got / want - 1) < 0.02, (got, want)
        assert not [m for m in msgs if "subtitle" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_tstyle(self, mode):
        rec = TRUTH["title_tstyle"]
        lg, msgs = _legend(mode, 'title("T", tstyle(body))')
        assert abs(_pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
                   - rec["T"]["size"] / rec["key_size"]) < 0.02
        assert str(lg.title_text_color).lower() == rec["T"]["fill"]
        assert not [m for m in msgs if "tstyle" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_tstyle_unknown_noted(self, mode):
        _lg, msgs = _legend(mode, 'title("T", tstyle(bogus))')
        hits = [m for m in msgs if "named style bogus not found in class "
                "textboxstyle, default attributes used" in m]
        assert len(hits) == 1, msgs
