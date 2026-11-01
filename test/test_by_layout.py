"""by()'s layout drawn as twoway lays it out (WP-41 section 41-05).

The truth is test/fixtures/by_layout_truth.json
(scripts/extract_by_layout_truth.do): per probe Y01-Y21, twoway's rc,
first error line, SVG canvas, rects and texts.  Measured:

- BY-4: ``by(foreign, total style(default) compact)`` and ``total
  compact style(default)`` export the same rects as ``by(foreign,
  total)`` (style() wins over compact); compact draws each plot region
  and each label box with the foreground line (#000000).
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_remainder as tr  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_layout_truth.json")
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


def _built(mode, go, plots=None, scheme="stcolor"):
    """``(grid, roots, notes)`` of one by() graph."""
    spec = tk._spec([tk._graph("g", plots or tk._ONE, go)], scheme=scheme)
    roots, notes, _o = tk._build(mode, spec, data=tr._data())
    grids = list(tk._grids(roots).values())
    return (grids[0] if grids else None), roots, notes


def _label_boxes(roots):
    from bokeh.models import ColorBar
    return [m for r in roots for m in r.references()
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box"]


def _geometry(grid):
    """What compact changes: the grid's spacing and each panel's drawn
    axes and borders."""
    return (tuple(grid.spacing),
            [(tk._axis_drawn(p, "x"), tk._axis_drawn(p, "y"),
              p.min_border_left, p.min_border_right, p.min_border_top,
              p.min_border_bottom) for p in tk._panels(grid)])


class TestTheFixture:
    def test_meta(self):
        assert sorted(_truth()["_meta"]) == ["born_date", "dash_commit",
                                             "extracted", "source",
                                             "stata_version"]

    def test_style_wins_in_twoway(self):
        p = _truth()["probes"]
        assert p["Y02"]["rects"] == p["Y01"]["rects"]
        assert p["Y03"]["rects"] == p["Y01"]["rects"]


class TestTheCompactWord:
    @pytest.mark.parametrize("tok,want", [
        ("compact", True), ("com", True), ("compa", True), ("co", False),
        ("compacts", False), ("Compact", False), ("", False)])
    def test_spellings(self, tok, want):
        """The grammar's minimum is com (_DASH_BY_GRAMMAR)."""
        assert dr._dash_by_is_compact(tok) is want

    @pytest.mark.parametrize("subs,want", [
        ("total style(default) compact", "total style(default)"),
        ("total comp style(default)", "total style(default)"),
        ("compact style(econ)", None),
        ("total compact", "total compact"),
        ("style(compact) compact", "compact compact")])
    def test_routed(self, subs, want):
        spec = tk._spec([tk._graph("g", tk._ONE, {"by": "foreign, " + subs})])
        go = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]
        rest = go["by"].partition(",")[2].strip()
        if want is None:
            assert "compact" not in rest and "plotregion" in go
        else:
            assert rest == want


@pytest.mark.parametrize("mode", _MODES)
class TestCompact:
    @pytest.mark.parametrize("pid", ["Y02", "Y03"])
    def test_style_wins(self, mode, pid):
        """compact beside style(default) is drawn as style(default)."""
        base, _r, _n = _built(mode, {"by": "foreign, total"})
        subs = {"Y02": "total style(default) compact",
                "Y03": "total compact style(default)"}[pid]
        got, _r, _n = _built(mode, {"by": "foreign, " + subs})
        assert _geometry(got) == _geometry(base)

    def test_compact_outlines(self, mode):
        """Y04 (s2color): every plot region and label box outline is the
        foreground line (#000000); the plot region keeps its width."""
        fg = dr.SchemeParser("s2color").style_bundle(
            "line", "foreground")["line"]
        assert fg == "#000000" and {
            r["stroke"] for r in _probe("Y04")["rects"]
            if r["fill"] == "none" and r["sw"] == 4.9 and r["x"] > 300} == {fg}
        grid, roots, _n = _built(mode, {"by": "foreign, compact"},
                                 scheme="s2color")
        plain, _r, _n = _built(mode, {"by": "foreign"}, scheme="s2color")
        panels = tk._panels(grid)
        assert {str(p.outline_line_color).lower() for p in panels} == {fg}
        assert [p.outline_line_width for p in panels] == [
            p.outline_line_width for p in tk._panels(plain)]
        assert {str(b.bar_line_color).lower()
                for b in _label_boxes(roots)} == {fg}

    def test_bystyle_compact_fixture(self, mode):
        """by_remainder_truth.json bystyle_compact: style(compact) draws
        the black plot region and label box outlines."""
        probe = tr._probe("bystyle_compact")
        assert {r["stroke"] for r in probe["rects"]
                if r["fill"] == "none" and r["x"] > 200} == {"#000000"}
        grid, roots, _n = _built(mode, {"by": "rep78, style(compact)"},
                                 plots=tk._TWO, scheme="s2color")
        assert {str(p.outline_line_color).lower()
                for p in tk._panels(grid)} == {"#000000"}
        assert {str(b.bar_line_color).lower()
                for b in _label_boxes(roots)} == {"#000000"}
