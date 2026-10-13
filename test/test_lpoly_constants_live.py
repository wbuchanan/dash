"""The lpoly rule-of-thumb constants for degree 4-7 are live (WP-31 F4).

GAPS3 F4: ``_LPOLY_ROT_CONSTANTS`` held the Fan-Gijbels constants for
pe = 5 and 7 (degree 4-7) while ``degree=int,0,3`` refused every degree
that reads them, and its comment called them dormant.  C10b bounded
degree() at 7 (test_lpoly_degree.py); here every row of the table is
shown read by the bandwidth rule at a degree the rule table accepts, and
the comment says so.
"""
import os
import re
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402

_SRC = os.path.join(_HERE, "..", "dash_render.py")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_AUTO = os.path.join(_HERE, "fixtures", "data", "auto.csv")


def _comment():
    """The comment block directly above the table."""
    with open(_SRC, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    at = lines.index("_LPOLY_ROT_CONSTANTS = {")
    out = []
    for ln in reversed(lines[:at]):
        if not ln.startswith("#"):
            break
        out.append(ln)
    return " ".join(reversed(out))


def _degree_bound():
    with open(_ADO, encoding="utf-8") as fh:
        m = re.search(r"\bdegree=int,(\d+),(\d+)\b", fh.read())
    return int(m.group(1)), int(m.group(2))


class _Reads(dict):
    """The table, counting each key ``get`` reads."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.reads = {}

    def get(self, key, default=None):
        self.reads[key] = self.reads.get(key, 0) + 1
        return super().get(key, default)


class TestTheComment:
    def test_constants_are_live(self):
        text = _comment()
        assert "dormant" not in text
        assert "live" in text and "degree 4-7" in text

    def test_every_row_is_reachable(self, monkeypatch):
        d = pd.read_csv(_AUTO)
        x = d["weight"].to_numpy(float)
        y = d["mpg"].to_numpy(float)
        table = _Reads(dr._LPOLY_ROT_CONSTANTS)
        monkeypatch.setattr(dr, "_LPOLY_ROT_CONSTANTS", table)
        lo, hi = _degree_bound()
        for kernel, pe in sorted(dr._LPOLY_ROT_CONSTANTS):
            degree = pe - 1
            assert lo <= degree <= hi, (kernel, pe, "beyond degree()'s rule")
            h = dr.GlyphMapper._default_lpoly_bwidth(x, y, None, degree,
                                                     kernel)
            assert h == h and h > 0, (kernel, pe, h)
        assert sorted(table.reads) == sorted(dr._LPOLY_ROT_CONSTANTS)
        assert set(table.reads.values()) == {1}
