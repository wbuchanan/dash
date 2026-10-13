"""scatteri's p/q coordinate (WP-31 C18).

GAPS3 C18: dash's immediate-values reader (``_dash_imm_number``,
dash_parse.mata) refused ``scatteri 2/2 1`` as "invalid point" where
twoway draws a point at (1, 1): its numlist reads ``2/2`` as a range of
one value, then evaluates it as a division.  Measured in
test/fixtures/parsed_values_truth.json (scripts/extract_parsed_values_truth.do):
``2/2 1`` and ``-1/-1 1`` draw (1, 1), ``0/0 1`` a missing y, ``2/2 1/1``
(1, 1); ``1/2 1`` is "invalid point, 1 1/2" r(198); ``1 2 (1/1)`` a clock
position of 1.  The Stata run is test_parser.cscript U06-05.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_FIX = os.path.join(_HERE, "fixtures", "parsed_values_truth.json")


def _mata():
    with open(_MATA, encoding="utf-8") as fh:
        return fh.read()


def _function(src, name):
    m = re.search(r"\n[^\n]*\b" + name + r"\(", src)
    start = m.start()
    end = src.index("\n}\n", start)
    return src[start:end]


class TestDivision:
    def test_twoways_readings(self):
        with open(_FIX, encoding="utf-8") as fh:
            s = json.load(fh)["scatteri"]
        assert s["2/2 1"]["rows"] == [[1.0, 1.0]]
        assert s["-1/-1 1"]["rows"] == [[1.0, 1.0]]
        assert s["0/0 1"]["rows"] == [[None, 1.0]]
        assert s["2/2 1/1"]["rows"] == [[1.0, 1.0]]
        assert (s["1/2 1"]["rc"], s["1/2 1"]["message"]) == \
            (198, "invalid point, 1 1/2")

    def test_the_branch_exists(self):
        body = _function(_mata(), "_dash_imm_number")
        assert 'strpos(t, "/")' in body
        assert "_dash_imm_decimal(a) & _dash_imm_decimal(b)" in body
        assert 'strtoreal(a) == 0 ? "null" : "1"' in body

    def test_the_comment(self):
        src = _mata()
        assert "2/2 is a numlist range twoway takes" not in src
        assert "p/q with p == q draws 1" in src


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_the_point_draws_at_one(mode):
    """What dash.ado writes for ``scatteri 2/2 1`` -- values [[1, 1]] --
    draws one marker at (1, 1) (guard)."""
    from bokeh.models import GlyphRenderer
    spec = tp._spec([plot_for("scatteri", values=[[1.0, 1.0]])])
    if mode == "saved":
        r, _w = tp._standalone(spec)
        models = list(r._last_layout_root.references())
    else:
        doc, _w = tp._served(spec)
        models = [m for root in doc.roots for m in root.references()]
    pts = []
    for m in models:
        if isinstance(m, GlyphRenderer) and hasattr(m.glyph, "x") \
                and isinstance(getattr(m.glyph, "x", None), str):
            d = m.data_source.data
            pts += list(zip(d[m.glyph.y], d[m.glyph.x]))
    assert [(float(a), float(b)) for a, b in pts] == [(1.0, 1.0)]
