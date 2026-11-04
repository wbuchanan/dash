"""test_legend_box.py -- the legend's box and its key texts' text boxes,
as twoway draws them (WP-43 section 43-03: LT-2, LT-3, LT-6, LT-7,
LT-10).

LT-2: twoway's ``legend(nobox)`` and ``legend(box)`` are the key texts'
textbox options (legend_options.sthlp): nobox leaves the legend as the
default draws it, box frames each key's text; neither touches the region
box, which only the scheme and region() draw.

Ground truth: test/fixtures/legend_box_truth.json, written by
scripts/extract_legend_box_truth.do from twoway's SVG export (SVG user
units, 720 per inch; three scatters; s2color unless the row says).
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_legend_geometry as G  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "legend_box_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The key texts of the fixture's three scatters.
KEYS = ("Mileage (mpg)", "Price", "Turn circle (ft.)")


def _rects(key):
    """The fixture row *key*'s rects smaller than the canvas, as
    ``(x0, y0, x1, y1, style)``."""
    row = TRUTH[key]
    return [(r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"], r["style"])
            for r in row["rects"] if r["w"] < row["viewbox"][2] - 1]


def _key_frames(key):
    """The rects of row *key* that hold one key text's anchor and no
    other: twoway's frame round each key text (fill and line)."""
    texts = [t for t in TRUTH[key]["texts"] if t["text"] in KEYS]
    out = []
    for r in _rects(key):
        # A line is drawn inside the fill: up to half its width in.
        inside = [t for t in texts if r[0] - 15 <= t["x"] <= r[2] + 1
                  and r[1] <= t["y"] <= r[3] + 1]
        if len(inside) == 1:
            out.append(r)
    return out


def _legend_region(key):
    """The legend's region box (fill and line) of row *key*: the rects
    holding every key text."""
    texts = [t for t in TRUTH[key]["texts"] if t["text"] in KEYS]
    return [r for r in _rects(key)
            if all(r[0] <= t["x"] <= r[2] and r[1] <= t["y"] <= r[3]
                   for t in texts)]


class TestTheFixture:

    def test_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "base", "units"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_box_truth.do"
        for k, row in TRUTH.items():
            if k != "_meta":
                assert row["rc"] == 0, (k, row["lines"])

    def test_nobox_is_the_default(self):
        """nobox draws the default; box and box nobox frame each key text
        and leave the region box (s2color and stcolor)."""
        for sfx in ("", "_st"):
            ctl = TRUTH["ctl" + sfx]
            assert TRUTH["nobox" + sfx]["rects"] == ctl["rects"]
            assert TRUTH["nobox" + sfx]["texts"] == ctl["texts"]
            assert _legend_region("box" + sfx) == _legend_region("ctl" + sfx)
            assert len(_key_frames("box" + sfx)) == 2 * len(KEYS)
        assert _key_frames("box_nobox") == _key_frames("box")


@pytest.mark.parametrize("mode", MODES)
class TestNobox:

    @pytest.mark.parametrize("scheme", ["s2color", "stcolor"])
    def test_changes_nothing(self, mode, scheme):
        """legend(nobox) and legend(box): the region box's line and fill
        are the default's (legend_box_truth.json nobox, box)."""
        _f, ref, _ = G._fig_legend(mode, G.THREE, "", scheme=scheme)
        for opt in ("nobox", "box"):
            _f, lg, caught = G._fig_legend(mode, G.THREE, opt,
                                           scheme=scheme)
            assert lg.border_line_color == ref.border_line_color, opt
            assert lg.background_fill_color == ref.background_fill_color, \
                opt
            assert lg.padding == ref.padding, opt
            assert not [w for w in caught if opt in w], caught
