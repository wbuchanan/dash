"""
test_by_scale_range_weights.py -- three per-panel rules of a by() graph
(WP-41 section 41-03).

BY-2: a scale() written beside by() scaled every panel, where twoway
ignores it on a by() graph, and by(, scale(#)), which twoway applies to the
whole by() graph, was named as ignored.  BY-27: function and kdensity
range(varname) under by() spanned the whole data in every panel, where
twoway spans each panel's own rows.  The truth is
test/fixtures/by_scale_range_truth.json
(scripts/extract_by_scale_range_truth.do); sil:SD-7's zero-weight panels
are a Stata-side refusal, compared with twoway in
test/test_option_validation.cscript (Q4103-4..9).
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_grid as tbg  # noqa: E402
from by_panel_probe import by_grid, is_chrome, panel_label_title  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_scale_range_truth.json")
_MODES = ("saved", "served")
_T = None


def _truth():
    global _T
    if _T is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _T = json.load(fh)
    return _T


def _probe(pid):
    return _truth()["probes"][pid]


def _pt(v):
    return dr.OptionTranslator.css_to_pt(v)


def _ratio(a, b, text):
    """twoway's size ratio of *text* between probes *a* and *b* (the
    first SVG text reading *text* in each)."""
    sa = next(t["size"] for t in _probe(a)["texts"] if t["text"] == text)
    sb = next(t["size"] for t in _probe(b)["texts"] if t["text"] == text)
    return sa / sb


def _sizes(mode, go, plots=None):
    """``{"tick", "marker", "label", "chrome": {text: pt}, "legend"}`` of
    the by() graph *go* drawn in *mode*: panel 1's x tick-label size, its
    first marker's size, its panel label's size, every text of the cells
    beside the panels (head, foot, axis titles, legend) and the overall
    legend's label size; plus the build's notes."""
    from bokeh.models import Label, Legend, Title
    spec = tbg._many([go], scheme="stcolor")
    if plots is not None:
        spec["graphs"][0]["plots"] = plots
    roots, notes = tbg._build(mode, spec)
    grid = tbg._grids(roots)[0]

    class _R:
        def references(self_inner):
            return [grid]
    panels, _, _ = by_grid(_R())
    fig = panels[0][2]
    out = {"tick": _pt(fig.xaxis[0].major_label_text_font_size),
           "marker": next(float(r.glyph.size) for r in fig.renderers
                          if isinstance(getattr(r.glyph, "size", None),
                                        (int, float))),
           "label": _pt(panel_label_title(fig).text_font_size),
           "chrome": {}, "legend": None, "notes": notes}
    own = set()
    for _r, _c, f in panels:
        own |= {id(m) for m in f.references()}
    for child in grid.children:
        cell = child[0]
        if not is_chrome(cell):
            continue
        for m in cell.references():
            if id(m) in own:
                continue
            if isinstance(m, (Title, Label)) and str(m.text or ""):
                out["chrome"].setdefault(str(m.text), _pt(m.text_font_size))
            elif isinstance(m, Legend) and m.items:
                out["legend"] = _pt(m.label_text_font_size)
    return out


_S05_PLOTS = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
               "options": {}},
              {"type": "lfit", "yvar": "mpg", "xvar": "weight",
               "options": {}}]


class TestByScale:
    @pytest.mark.parametrize("mode", _MODES)
    def test_outer_scale_changes_nothing(self, mode):
        # twoway: every text and the marker of S02 equal S01's.
        s01, s02 = _probe("S01"), _probe("S02")
        assert [t["size"] for t in s02["texts"]] == \
            [t["size"] for t in s01["texts"]]
        assert s02["marker_r"] == s01["marker_r"]
        base = _sizes(mode, {"by": "foreign"})
        got = _sizes(mode, {"by": "foreign", "scale": "1.5"})
        for k in ("tick", "marker", "label", "chrome"):
            assert got[k] == base[k], (k, base[k], got[k])

    @pytest.mark.parametrize("mode", _MODES)
    def test_by_scale_scales_everything(self, mode):
        want = _ratio("S05", "S06", "T")
        assert abs(want - 1.5) < 0.01
        for text in ("10", "Domestic", "Graphs by Car origin",
                     "Weight (lbs.)"):
            assert abs(_ratio("S05", "S06", text) - want) < 0.01, text
        base = _sizes(mode, {"by": 'foreign, title("T")', "legend": "on"},
                      _S05_PLOTS)
        got = _sizes(mode, {"by": 'foreign, scale(1.5) title("T")',
                            "legend": "on"}, _S05_PLOTS)
        for k in ("tick", "marker", "label", "legend"):
            assert base[k], k
            assert abs(got[k] / base[k] - 1.5) < 0.01, (k, base[k], got[k])
        for text in ("T", "Graphs by Car origin", "Weight (lbs.)"):
            assert abs(got["chrome"][text] / base["chrome"][text] - 1.5) \
                < 0.01, (text, base["chrome"], got["chrome"])

    @pytest.mark.parametrize("mode", _MODES)
    def test_by_scale_with_iscale1(self, mode):
        assert abs(_ratio("S04", "S07", "10") - 1.5) < 0.01
        assert abs(_probe("S04")["marker_r"] / _probe("S07")["marker_r"]
                   - 1.5) < 0.01
        base = _sizes(mode, {"by": "foreign, iscale(1)"})
        got = _sizes(mode, {"by": "foreign, scale(1.5) iscale(1)"})
        for k in ("tick", "marker", "label"):
            assert abs(got[k] / base[k] - 1.5) < 0.01, (k, base[k], got[k])

    def test_no_note_for_a_number(self):
        got = _sizes("saved", {"by": "foreign, scale(1.5)"})
        assert not [n for n in got["notes"] if "not implemented" in n], \
            got["notes"]

    def test_a_word_is_still_named(self):
        got = _sizes("saved", {"by": "foreign, scale(big)"})
        assert [n for n in got["notes"] if "not implemented" in n
                and "scale(big)" in n], got["notes"]
        base = _sizes("saved", {"by": "foreign"})
        assert got["tick"] == base["tick"]

    def test_scale_mult(self):
        f = dr._dash_by_scale_mult
        assert f("foreign, scale(1.5)") == 1.5
        assert f("foreign, iscale(1) scale(2)") == 2.0
        assert f("foreign, sc(1.5)") == 1.0     # not twoway's spelling
        for raw in ("foreign", "", None, "foreign, scale(big)",
                    "foreign, scale(-1)", "foreign, scale(0)",
                    "foreign, scale(1e999)", "foreign, scale()", 5):
            assert f(raw) == 1.0, raw

    def test_scale_arg(self):
        f = dr._dash_by_scale_arg
        assert f("1.5") == 1.5
        assert f(" 2 ") == 2.0
        assert f("1") == 1.0
        assert f(".5e1") == 5.0
        for raw in ("", None, "big", "-1", "0", "1e999", "1 2", "x" * 99):
            assert f(raw) is None, raw
