"""recast() of a histogram to a range type and of pci/pcarrowi to a pc type,
drawn as twoway draws them (WP-31 C7).

The defect, measured at the C6 commit (StataNow 19.5): dash.ado named
``recast()`` in its note for ``histogram mpg, recast(rarea)`` (and every
range target), for an unknown name on histogram, and for any recast() on
pci and pcarrowi, and drew the layer as typed -- bars, a pcspike, arrows.

twoway's own answers are test/fixtures/area_cmissing_truth.json (scripts/
extract_area_cmissing_truth.do; auto with mpg missing in 10/12):

* histogram is a y2xtype source: recast(rarea) draws the bins as an rarea
  over (bin centre, 0, height) (H01, ``.plot1.type`` rarea); rbar draws
  bars as wide as the histogram's own, gap() and baroffset() honoured
  (H03, H04, H09); rspike, rcap, rcapsym, rscatter, rline and rconnected
  stand at the centres, gap() and baroffset() not read (H05, H06, H10,
  H07, H08, H11, H12); an unknown name prints twoway's two notes and draws
  rspike, y2xtype's default (H02);
* pci and pcarrowi are yxyxtype: recast(pcarrow), (pcscatter), (pccapsym),
  (pcspike) draw the type named (P01, P02, P04, P05); an unknown name
  prints the two notes and draws pcspike (P03).
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402

_REPO = os.path.join(_HERE, "..")
with open(os.path.join(_HERE, "fixtures", "area_cmissing_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json"),
          encoding="utf-8") as _fh:
    _AUTO = json.load(_fh)["datasets"]["auto"]

_MODES = ("saved", "served")
_RANGE = ("rarea", "rbar", "rspike", "rcap", "rcapsym", "rscatter", "rline",
          "rconnected")


def _auto():
    df = pd.DataFrame({"mpg": _AUTO["mpg"], "weight": _AUTO["weight"]},
                      dtype=float)
    df.loc[9:11, "mpg"] = np.nan
    return df


def _figs(mode, plots, df=None):
    figs, _ = bg._figs(mode, tempfile.mkdtemp(), bg._spec(plots),
                       _auto() if df is None else df)
    return figs


def _hist(**o):
    return {"type": "histogram", "var": "mpg", "options": o}


def _types(fig):
    return [type(r.glyph).__name__ for r in fig.renderers
            if getattr(r, "glyph", None) is not None]


def _col(r, name):
    g = r.glyph
    v = getattr(g, name)
    f = v if isinstance(v, str) else getattr(v, "field", None)
    return dr._dash_float_values(r.data_source.data[f])


def _bins():
    """twoway's bins of H01: (centre, height), from the rarea polygon's
    upper edge (the path's first half after its move-to repeat)."""
    pts = _T["H01"]["paths"][0]["pts"]
    m = (len(pts) - 2) // 2
    return [tuple(p) for p in pts[1:1 + m]]


# ===========================================================================
# histogram
# ===========================================================================

@pytest.mark.parametrize("mode", _MODES)
class TestHistogramRangeRecast:

    def test_rarea(self, mode):
        """histogram mpg, recast(rarea): one VArea over the bin centres
        from 0 to each bin's height, twoway's (H01)."""
        fig = _figs(mode, [_hist(recast="rarea")])[0]
        [r] = [r for r in fig.renderers
               if type(r.glyph).__name__ == "VArea"]
        x, lo, hi = _col(r, "x"), _col(r, "y1"), _col(r, "y2")
        want = _bins()
        assert len(x) == len(want)
        for i, (cx, h) in enumerate(want):
            assert abs(x[i] - cx) < 1e-3 and abs(hi[i] - h) < 1e-4, (
                i, x[i], hi[i], cx, h)
        assert np.all(lo == 0.0)
        assert "Quad" not in _types(fig)

    @pytest.mark.parametrize("target", _RANGE)
    def test_each_target(self, mode, target):
        """Each range target draws what its own mapper draws, at the bin
        centres (no Quad)."""
        fig = _figs(mode, [_hist(recast=target)])[0]
        t = _types(fig)
        assert "Quad" not in t, t
        assert t, target

    @pytest.mark.parametrize("pid,o", [
        ("H03", {}), ("H04", {"gap": "50"}),
        ("H09", {"gap": "50", "baroffset": "1"})])
    def test_rbar_is_the_histograms_bar(self, mode, pid, o):
        """recast(rbar): bars as wide as the histogram's own (gap()) and
        moved by baroffset(), twoway's rectangles."""
        fig = _figs(mode, [_hist(recast="rbar", **o)])[0]
        [r] = [r for r in fig.renderers if type(r.glyph).__name__ == "VBar"]
        x = _col(r, "x")
        w = r.glyph.width
        w = float(getattr(w, "value", w))
        bars = [q for q in _T[pid]["rects"] if q[4] not in ("#ffffff",
                                                             "none")]
        assert len(bars) == len(x)
        for i, q in enumerate(bars):
            assert abs((x[i] - w / 2) - q[0]) < 2e-3, (i, x[i], w, q)
            assert abs((x[i] + w / 2) - q[1]) < 2e-3, (i, x[i], w, q)

    def test_spike_ignores_gap(self, mode):
        """recast(rspike) gap(50) baroffset(1): the spikes stand at the
        centres, as twoway's (H05)."""
        fig = _figs(mode, [_hist(recast="rspike", gap="50",
                                 baroffset="1")])[0]
        [r] = [r for r in fig.renderers
               if type(r.glyph).__name__ == "Segment"]
        x0 = _col(r, "x0")
        want = [s[0] for s in _T["H05"]["segs"]]
        assert len(x0) == len(want)
        assert np.allclose(sorted(x0), sorted(want), atol=1e-3)


class TestUnknownName:

    def test_histogram_notes_and_rspike(self):
        """twoway's answer to recast(bogus) on histogram: its two notes and
        rspike (H02); dash.ado writes rspike after the same notes, so the
        spec's recast is rspike and spikes are drawn."""
        assert _T["H02"]["type"] == "rspike"
        assert len(_T["H02"]["lines"]) == 2
        for mode in _MODES:
            fig = _figs(mode, [_hist(recast="rspike")])[0]
            assert "Segment" in _types(fig) and "Quad" not in _types(fig)
        ado = _read("dash.ado")
        body = ado[ado.index("program define _dash_recast_opt"):]
        body = body[:body.index("\nend\n")]
        # No histogram special case: the class's fallback is taken.
        assert 'if "`ptype\'" == "histogram" {' not in body


# ===========================================================================
# pci and pcarrowi
# ===========================================================================

def _pc_types(mode, target):
    """What the pc type *target* draws on one segment given as variables."""
    df = pd.DataFrame({"a": [20.0], "b": [2000.0], "c": [30.0],
                       "d": [4000.0]})
    plot = {"type": target, "y1var": "a", "x1var": "b", "y2var": "c",
            "x2var": "d", "options": {}}
    return _types(_figs(mode, [plot], df)[0])


@pytest.mark.parametrize("mode", _MODES)
class TestPciRecast:

    def test_pcarrow(self, mode):
        """pci 20 2000 30 4000, recast(pcarrow) draws pcarrow's glyphs
        (P01: .plot1.type pcarrow)."""
        assert _T["P01"]["type"] == "pcarrow"
        plot = {"type": "pci", "values": [[20.0, 2000.0, 30.0, 4000.0]],
                "options": {"recast": "pcarrow"}}
        got = _types(_figs(mode, [plot])[0])
        assert got == _pc_types(mode, "pcarrow"), got

    def test_pcarrowi(self, mode):
        """pcarrowi ..., recast(pcscatter) draws pcscatter's glyphs (P02)."""
        assert _T["P02"]["type"] == "pcscatter"
        plot = {"type": "pcarrowi", "values": [[20.0, 2000.0, 30.0, 4000.0]],
                "options": {"recast": "pcscatter"}}
        got = _types(_figs(mode, [plot])[0])
        assert got == _pc_types(mode, "pcscatter"), got

    def test_each_target(self, mode):
        for target in ("pcspike", "pccapsym", "pcbarrow"):
            for lit in ("pci", "pcarrowi"):
                plot = {"type": lit,
                        "values": [[20.0, 2000.0, 30.0, 4000.0]],
                        "options": {"recast": target}}
                got = _types(_figs(mode, [plot])[0])
                assert got == _pc_types(mode, target), (lit, target, got)


# ===========================================================================
# dash.ado
# ===========================================================================

def _read(name):
    with open(os.path.join(_REPO, name), encoding="utf-8") as fh:
        return fh.read()


class TestTheAdoText:

    def test_literal_kind(self):
        """_dash_recast_opt reads pci and pcarrowi's recast() in yxyxtype
        and writes the target with kind literal; a range target on
        histogram is written as a derived target, never named."""
        ado = _read("dash.ado")
        body = ado[ado.index("program define _dash_recast_opt"):]
        body = body[:body.index("\nend\n")]
        assert "sreturn local _recast_kind literal" in body
        assert ("else if `: list ptype in _rc_lit' local _rc_class "
                "yxyxtype") in body
        # The only remaining caller of _dash_recast_named is dot (S03).
        assert body.count("_dash_recast_named") == 1
        seg = ado[ado.index("_dash_recast_opt \"`ptype'\""):]
        seg = seg[:seg.index("// function's range() as typed")]
        assert '"`_rc_kind\'" == "literal"' in seg
