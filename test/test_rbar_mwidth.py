"""
test_rbar_mwidth.py -- rbar's mwidth draws each bar as wide as a marker of
its msize(), in screen units, as twoway's rbarm view does (WP-31 C2).

The defect (measured at 4e2bd90): ``dash rbar yl yh x, mwidth msize(large)``
drew one x unit per bar and never read msize(); mwidth was undeclared (the
generic note named it) and ``rbar ..., msize(large)`` without mwidth sat in
the spec unread with no note.

twoway (StataNow 19.5, scripts/extract_rbar_dot_truth.do, fixture
test/fixtures/rbar_dot_truth.json): with mwidth each bar's width over
min(W, H) * 100 is its marker.size.val (1.53 medium by default), whatever
the x spacing; msize() without mwidth draws exactly the plain rbar.
"""
import json
import os
import sys

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure as bk_figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as tsfl  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "rbar_dot_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
_MW = {"mwidth": "mwidth"}


def _rect(figs):
    [r] = bg._glyphs(figs, "Rect")
    return r


def _field(v):
    return v if isinstance(v, str) else getattr(v, "field", None)


def _rbar_mw(mode, tmp_path, case="s1", **o):
    figs, notes = bg._figs(mode, tmp_path,
                           bg._spec([bg._bar("rbar", **dict(_MW, **o))]),
                           bg._frame(bg._X[case]))
    return _rect(figs), notes


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta_is_stamped(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]
        assert all(_T["_meta"][k] for k in _T["_meta"])

    def test_twoways_width_is_its_msize(self):
        for k in ("mwidth", "mwidth_small", "mwidth_large", "mwidth_vlarge",
                  "mwidth_2", "spacing"):
            v = _T["rbar"][k]
            assert v["ratio"] == pytest.approx(v["marker_size_val"],
                                               rel=0.01), k
        # The same width at both x spacings (weight and turn).
        assert _T["rbar"]["spacing"]["width_px"] == pytest.approx(
            _T["rbar"]["mwidth"]["width_px"], rel=1e-3)
        # msize() without mwidth draws the plain rbar.
        assert _T["rbar"]["msize_only"]["width_px"] == pytest.approx(
            _T["rbar"]["plain"]["width_px"], rel=1e-3)


# ---------------------------------------------------------------------------
# mwidth
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestMwidth:

    def test_the_width_is_the_marker_size(self, mode, tmp_path):
        r, _ = _rbar_mw(mode, tmp_path)
        assert r.glyph.width_units == "screen"
        assert r.glyph.height_units == "data"
        assert bg._width_value(r) == pytest.approx(
            bg._scatter_size(mode, tmp_path))
        assert _field(r.glyph.y) == "__dash_rbar_mid"
        assert _field(r.glyph.height) == "__dash_rbar_h"

    def test_the_vertical_extent_is_y1_y2(self, mode, tmp_path):
        r, _ = _rbar_mw(mode, tmp_path)
        d = r.data_source.data
        assert list(d["__dash_rbar_mid"]) == pytest.approx(
            [(a + b) / 2.0 for a, b in zip(bg._LO, bg._HI)])
        assert list(d["__dash_rbar_h"]) == pytest.approx(
            [abs(b - a) for a, b in zip(bg._LO, bg._HI)])

    @pytest.mark.parametrize("m", ["small", "large", "vlarge", "2"])
    def test_msize_scales_the_width(self, mode, tmp_path, m):
        r, notes = _rbar_mw(mode, tmp_path, msize=m)
        assert bg._width_value(r) == pytest.approx(
            bg._scatter_size(mode, tmp_path, m))
        assert not [n for n in notes if "msize" in n or "mwidth" in n], notes

    def test_the_width_does_not_follow_the_spacing(self, mode, tmp_path):
        a, _ = _rbar_mw(mode, tmp_path, "s1")
        b, _ = _rbar_mw(mode, tmp_path, "s5")
        assert bg._width_value(a) == bg._width_value(b)

    def test_barwidth_with_mwidth(self, mode, tmp_path):
        """twoway reads barwidth() beside mwidth as the marker size
        (barwidth(.3) draws marker.size.val .3, barwidth(3) 3)."""
        assert _T["rbar"]["mwidth_barwidth_rule"] == "marker size"
        for bw in (".3", "3"):
            r, notes = _rbar_mw(mode, tmp_path, barwidth=bw)
            assert bg._width_value(r) == pytest.approx(
                bg._scatter_size(mode, tmp_path, bw)), bw
        assert not [n for n in notes if "barwidth" in n], notes

    def test_the_tag(self, mode, tmp_path):
        r, _ = _rbar_mw(mode, tmp_path)
        assert "dash_rbar_mwidth" in (r.tags or [])


class TestAnEmptyLayer:

    def test_an_empty_layer(self):
        gm = bg._gm()
        rs = gm.map_rbar(bk_figure(), ColumnDataSource(
            {"x": [], "lo": [], "hi": []}), "lo", "hi", "x", dict(_MW))
        [r] = rs
        assert type(r.glyph).__name__ == "Rect"
        assert r.glyph.width_units == "screen"
        d = r.data_source.data
        assert len(d["__dash_rbar_mid"]) == 0
        assert len(d["__dash_rbar_h"]) == 0
        assert bg._width_value(r) == pytest.approx(
            gm.scheme.default_marker_size(0))


class TestTheWidthHoldsAcrossAMove:

    def test_saved(self):
        spec = tp._spec([plot_for("rbar", dict(_MW, msize="large"))],
                        {"filter": bg._DROPDOWN})
        r = tsfl._render(spec)
        [rect] = bg._glyphs(r.figures.values(), "Rect")
        before = bg._width_value(rect)
        tsfl._move(r, tsfl._MOVES[0][2])
        assert bg._width_value(rect) == before
        d = rect.data_source.data
        assert len(d["__dash_rbar_mid"]) == len(d["__dash_rbar_h"])

    def test_served(self):
        spec = tp._spec([plot_for("rbar", dict(_MW, msize="large"))],
                        {"filter": bg._DROPDOWN})
        r = tsfl._render(tp._spec([plot_for("rbar", dict(_MW,
                                                         msize="large"))]))
        [rect] = bg._glyphs(r.figures.values(), "Rect")
        want = bg._width_value(rect)
        figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
        widths = [g["coords"].get("width") for f in figs
                  for g in f["glyphs"] if g["type"] == "Rect"]
        # The profile rounds a value (_num).
        assert len(widths) == 1 and widths[0][0] == "value", widths
        assert widths[0][1] == pytest.approx(want, abs=1e-4), widths


# ---------------------------------------------------------------------------
# Without mwidth
# ---------------------------------------------------------------------------

class TestWithoutMwidth:

    def test_nothing_changes(self):
        """The VBar is the one drawn at 4e2bd90 (snapshot taken there)."""
        gm = bg._gm()
        for o, lw, fill in (({}, 0.768, "#486c8c"),
                            ({"msize": "large", "lwidth": "thick",
                              "bfcolor": "red"}, 3.072, "#ff3333")):
            src = ColumnDataSource({"x": [1., 2, 3], "lo": [1., 2, 1],
                                    "hi": [4., 5, 3]})
            [r] = gm.map_rbar(bk_figure(), src, "lo", "hi", "x", o)
            g = r.glyph
            assert type(g).__name__ == "VBar", o
            assert (_field(g.x), _field(g.bottom), _field(g.top)) == \
                ("x", "lo", "hi")
            assert bg._width_value(r) == 1.0
            # Flipped (WP-31 E8): the outline was Bokeh's default at alpha
            # 0; twoway outlines each bar in color p# (fixture ol.rbar).
            assert g.line_color == "#1a476f" and g.line_alpha == 1.0
            assert g.line_width == pytest.approx(lw)
            assert g.fill_color == fill
            assert "dash_rbar_mwidth" not in (r.tags or [])

    @pytest.mark.parametrize("mode", _MODES)
    def test_msize_is_named(self, mode, tmp_path):
        """dash.ado names msize() on rbar without mwidth (_dash_fold_typed);
        the renderer adds no second note."""
        figs, notes = bg._figs(mode, tmp_path,
                               bg._spec([bg._bar("rbar", msize="large")]),
                               bg._frame(bg._X["s1"]))
        assert bg._glyphs(figs, "VBar") and not bg._glyphs(figs, "Rect")
        assert not [n for n in notes if "msize" in n], notes


# ---------------------------------------------------------------------------
# The axis hull reads the Rect's rows
# ---------------------------------------------------------------------------

class TestTheExtent:

    def test_the_y_extent_is_y1_y2_and_x_the_centres(self):
        gm = bg._gm()
        src = ColumnDataSource({"x": [1., 2, 3], "lo": [1., 2, 1],
                                "hi": [4., 5, 3]})
        rs = gm.map_rbar(bk_figure(), src, "lo", "hi", "x", dict(_MW))
        lo, hi = dr._dash_layer_extent(rs, "y_range_name", "default")
        assert (lo, hi) == pytest.approx((1.0, 5.0))
        assert dr._dash_layer_extent(rs, "x_range_name", "default") == \
            pytest.approx((1.0, 3.0))

    @pytest.mark.parametrize("mode", _MODES)
    def test_both_modes_range_over_y1_y2(self, mode, tmp_path):
        """The Rect names its centre; the axis still spans y1..y2 (the
        renderer's _dash_hull_fields), as the VBar's does."""
        spec = tp._spec([plot_for("rbar", dict(_MW))])
        figs, _ = bg._figs(mode, tmp_path, spec, tp._DF)
        [f] = figs
        assert f.y_range.start <= float(tp._DF["mpg"].min())
        assert f.y_range.end >= float(tp._DF["price"].max())

    def test_the_saved_plan_reads_y1_y2(self):
        """The saved page's re-finish reads the same two columns."""
        r = tsfl._render(tp._spec([plot_for("rbar", dict(_MW))],
                                  {"filter": bg._DROPDOWN}))
        plan, _models = dr._dash_axis_plan(r.figures, {})
        plan = json.loads(plan) if isinstance(plan, str) else plan
        ys = [L["fields"] for g in plan for p in g.get("panels", [g])
              for a in p["axes"] if a["letter"] == "y"
              for L in a["layers"]]
        assert any({"mpg", "price"} <= set(f) for f in ys), ys

    def test_horizontal_turns_the_rect(self):
        gm = bg._gm()
        src = ColumnDataSource({"x": [1., 2, 3], "lo": [1., 2, 1],
                                "hi": [4., 5, 3]})
        rs = gm.map_rbar(bk_figure(), src, "lo", "hi", "x", dict(_MW))
        dr._dash_transpose_layer(None, rs, [], "rbar")
        [r] = rs
        assert type(r.glyph).__name__ == "Rect"
        assert r.glyph.height_units == "screen"
        assert r.glyph.width_units == "data"
        assert _field(r.glyph.x) == "__dash_rbar_mid"
        assert r._dash_hull_fields == {"x": ("lo", "hi")}
        assert dr._dash_layer_extent(rs, "x_range_name", "default") == \
            pytest.approx((1.0, 5.0))


class TestOnADateAxis:
    """rbar mwidth on a %td y axis, upright and horizontal: the Rect's
    centre and height are in the axis's own units (epoch milliseconds),
    so centre -/+ height/2 is y1..y2 and the axis spans it."""

    _LO = [15000.0, 15010.0, 15020.0]
    _HI = [15005.0, 15030.0, 15021.0]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("hz", [False, True])
    def test_the_bar_spans_y1_y2(self, mode, hz, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"x": [1.0, 2, 3], "lo": self._LO,
                           "hi": self._HI, "y": [1.0, 2, 3]})
        o = dict(_MW, **({"horizontal": "horizontal"} if hz else {}))
        figs, _ = bg._figs(mode, tmp_path,
                           bg._spec([bg._bar("rbar", **o)],
                                    formats={"lo": "%td", "hi": "%td"}),
                           df)
        [f] = figs
        r = _rect(figs)
        g = r.glyph
        centre, size = ("x", "width") if hz else ("y", "height")
        d = r.data_source.data
        mid = np.asarray(d[_field(getattr(g, centre))], dtype=float)
        h = np.asarray(d[_field(getattr(g, size))], dtype=float)
        ms = lambda v: dr._STATA_EPOCH_UNIX_MS + np.asarray(v) * bg._DAY
        assert list(mid - h / 2) == pytest.approx(list(ms(self._LO)))
        assert list(mid + h / 2) == pytest.approx(list(ms(self._HI)))
        # The other dimension is the marker's screen width.
        other = "height" if hz else "width"
        assert getattr(g, other + "_units") == "screen"
        rng = f.x_range if hz else f.y_range
        assert rng.start <= ms(min(self._LO)) and \
            rng.end >= ms(max(self._HI))
        axis = (f.xaxis if hz else f.yaxis)[0]
        assert type(axis).__name__ == "DatetimeAxis"
