"""test_noted_drawn.py -- options twoway draws that dash named (WP-32).

BUGS.md "Options twoway draws that dash still names: sort on marker types,
mstyle()/mlstyle() on arrows, baroffset() on rbar, mwidth on histogram"
and the entries split from it.  Each was measured 19oct2026 in StataNow
19.5 by graph export SVG (test/fixtures/noted_option_truth.json and the
probes the entries name); each test draws the option in both modes, the
saved page and the served app, and holds dash's geometry to twoway's.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = tsr.MODES


def _renderers(plots, mode, scheme="stcolor"):
    if isinstance(plots, dict):
        plots = [plots]
    d = tsr._draw(tp._spec(list(plots), {"scheme": scheme}, {}), mode)
    return ([r for f in d.figures for r in f.renderers
             if isinstance(r, GlyphRenderer)],
            [m for m in d.warnings if m.startswith("dash")])


def _vbar(plots, mode):
    rs, notes = _renderers(plots, mode)
    [r] = [r for r in rs if type(r.glyph).__name__ == "VBar"][:1]
    return r, notes


def _col(r, field):
    spec = getattr(r.glyph, field)
    name = spec if isinstance(spec, str) else getattr(spec, "field", spec)
    if isinstance(spec, dict):
        name = spec.get("field")
    return np.asarray(r.data_source.data[name], dtype=float)


@pytest.mark.parametrize("mode", MODES)
class TestRbarBaroffset:
    """twoway moves rbar's bars by baroffset() bar widths exactly as it
    moves bar's (measured 19oct2026: for baroffset(1), (-1), (.5) and (5)
    every rbar rect's x equals bar's, against each one's baroffset(0)),
    which map_bar draws (WP-31 C5)."""

    @pytest.mark.parametrize("off", ["1", "-1", ".5", "5"])
    def test_rbar_moves_as_bar_moves(self, mode, off):
        rb, _ = _vbar(plot_for("rbar", {"baroffset": off}), mode)
        r0, _ = _vbar(plot_for("rbar"), mode)
        xs = _col(r0, "x")
        got = _col(rb, "x")
        assert np.allclose(got, xs + float(off) * 1.0, equal_nan=True)

    def test_rbar_baroffset_is_not_named(self, mode):
        _, notes = _vbar(plot_for("rbar", {"baroffset": "1"}), mode)
        assert not [n for n in notes if "baroffset" in n]


def _width(r):
    """(value, units) of a glyph's width spec."""
    w = r.glyph.width
    v = getattr(w, "value", w)
    if isinstance(w, dict):
        v = w.get("value", w.get("field"))
    f = getattr(w, "field", None) or (v if isinstance(v, str) else None)
    if f:
        col = list(r.data_source.data[f])
        assert len(set(col)) <= 1, col
        v = col[0]
    units = getattr(w, "units", None) or getattr(r.glyph, "width_units",
                                                  None)
    if isinstance(w, dict):
        units = w.get("units", units)
    return float(v), units


@pytest.mark.parametrize("mode", MODES)
class TestHistogramMwidth:
    """twoway's histogram with mwidth draws each bar as wide as a marker
    whose size is barwidth() -- the bin width by default -- centred on the
    bin's start (measured 19oct2026: mpg's eight bins of 3.625 drawn
    117.45 of the SVG's 3240, 3.625%, the first centred at the first
    bar's left edge; barwidth(1) 32.4, 1%; msize() changes nothing)."""

    def _bars(self, mode, extra=None):
        o = {"mwidth": "mwidth"}
        o.update(extra or {})
        rs, notes = _renderers(plot_for("histogram", o), mode)
        return rs, notes

    def test_each_bar_is_a_marker_wide_at_the_bin_start(self, mode):
        rs, _ = self._bars(mode)
        q0 = [r for r in _renderers(plot_for("histogram"), mode)[0]
              if type(r.glyph).__name__ == "Quad"][0]
        [vb] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        assert not [r for r in rs if type(r.glyph).__name__ == "Quad"]
        assert np.allclose(_col(vb, "x"), _col(q0, "left"))
        assert np.allclose(_col(vb, "top"), _col(q0, "top"))
        w, units = _width(vb)
        assert units == "screen"
        assert w > 0

    def test_barwidth_is_the_marker_size(self, mode):
        rs, _ = self._bars(mode)
        [a] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        rs1, _ = self._bars(mode, {"barwidth": "1"})
        [b] = [r for r in rs1 if type(r.glyph).__name__ == "VBar"]
        bin_w = float(np.diff(_col(a, "x"))[0])
        assert _width(a)[0] == pytest.approx(bin_w * _width(b)[0], rel=1e-6)

    def test_msize_changes_nothing(self, mode):
        rs, _ = self._bars(mode)
        rs2, _ = self._bars(mode, {"msize": "vlarge"})
        [a] = [r for r in rs if type(r.glyph).__name__ == "VBar"]
        [b] = [r for r in rs2 if type(r.glyph).__name__ == "VBar"]
        assert _width(a) == _width(b)
