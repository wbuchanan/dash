"""A recast histogram or kdensity is recounted after a saved move (WP-31 C16).

The bars and the curve are recounted by the saved page's own script after a
filter move (``_FILTER_JS``'s histogram and kdensity branches); recast to a
yx type, they were drawn by ``GlyphMapper._dash_draw_xy_as`` on a fresh
source the script never saw, so the build's points stayed after the move
(with the stale cue, or with none under kdensity's range()).  The recast
layer now carries the un-recast layer's config plus ``recast_cols``, the
role of each of its source's columns, and the script writes the recounted
midpoints and heights (the grid and the density) into it.

Measured at the base (deviation from D-46e): the un-recast histogram and
kdensity do NOT escape the cue -- their bins and grid are the build's, so
both carry "(bins unfiltered)" / "(grid unfiltered)" after a move; the
recast layer keeps exactly that cue (``test_cue_as_the_unrecast_layer``).
"""
import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_mode_parity import _spec  # noqa: E402
from test_saved_filter_layers import _MOVES, _move, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

#: The recast targets whose source is the computed points' (dot draws its
#: dots on the axis rows and keeps the cue).
_TARGETS = ("scatter", "line", "connected", "area", "bar", "spike",
            "dropline")
#: kdensity over range() is recounted with no cue; without it the grid is
#: the build's.
_TYPES = {"histogram": {}, "kdensity": {"range": "10 45"}}


def _pair(ptype, target, move=_MOVES[0], extra=None):
    """A page with the un-recast layer in g1 and the recast one in g2."""
    o = dict(_TYPES[ptype], **(extra or {}))
    spec = _spec(None, {"filter": move[1]}, graphs=[
        ("g1", [plot_for(ptype, dict(o))]),
        ("g2", [plot_for(ptype, dict(o, recast=target))])])
    return _render(spec)


def _plain_points(r, ptype):
    """The un-recast layer's (x, y): bar midpoints and heights, or the
    curve."""
    for g in drawn_renderers(r.figures["g1"]):
        d = g.data_source.data
        if ptype == "histogram" and "top" in d:
            # The bars drawn now (WP-31 H6: a default grid is binned again
            # after a move, so the build's bin_edges are no longer them).
            lo = np.asarray(d["left"], dtype=float)
            hi = np.asarray(d["right"], dtype=float)
            return (lo + hi) / 2.0, np.asarray(d["top"], dtype=float)
        if ptype == "kdensity" and hasattr(g, "_dash_agg_config"):
            return (np.asarray(d["x"], dtype=float),
                    np.asarray(d["y"], dtype=float))
    raise AssertionError("no un-recast layer")


def _recast_renderers(r):
    # Flipped (WP-34 PIC-1): an area's outline ring is drawn from its
    # fill's source by its own script; the fill is the recounted renderer.
    return [g for g in drawn_renderers(r.figures["g2"])
            if not dr._dash_is_swatch(g)
            and "dash_area_outline" not in (getattr(g, "tags", None) or ())]


@pytest.mark.parametrize("ptype", sorted(_TYPES))
class TestRecastRefit:

    @pytest.mark.parametrize("target", _TARGETS)
    def test_tagged(self, ptype, target):
        r = _pair(ptype, target)
        rends = _recast_renderers(r)
        assert rends
        for g in rends:
            cfg = getattr(g, "_dash_agg_config", None)
            assert cfg is not None, (ptype, target, type(g.glyph).__name__)
            assert cfg["type"] == ptype
            assert g._dash_agg_source is g.data_source
            # Flipped (WP-31 H2l): a recast histogram's target carries
            # each bar's rows (__dash_bin_rows), which the refit does not
            # write and so drops at a move (the bars select nothing after
            # one, as the bars themselves do); every other column is one.
            assert set(cfg["recast_cols"]) == set(g.data_source.data) - {
                "__dash_bin_rows"}

    @requires_node
    @pytest.mark.parametrize("target", _TARGETS)
    def test_js_equals_python(self, ptype, target):
        r = _pair(ptype, target)
        _move(r, _MOVES[0][2])
        px, py = _plain_points(r, ptype)
        for g in _recast_renderers(r):
            d = g.data_source.data
            cols = g._dash_agg_config["recast_cols"]
            for k, role in cols.items():
                got = np.asarray(d[k], dtype=float)
                if role == "x":
                    np.testing.assert_allclose(got, px, rtol=1e-12)
                elif role == "y":
                    np.testing.assert_allclose(got, py, rtol=1e-12)
                elif role == "index":
                    assert list(got) == list(range(len(px)))
                else:
                    # a base: the axis finish moves it with the axis
                    assert len(got) == len(px)

    def test_cue_as_the_unrecast_layer(self, ptype):
        r = _pair(ptype, "line")
        plain = [t for t, _ in r.frozen_layer_registry.get("g1", [])]
        recast = [t for t, _ in r.frozen_layer_registry.get("g2", [])]
        assert [t["kind"] for t in recast] == [t["kind"] for t in plain]

    def test_dot_keeps_the_cue(self, ptype):
        # dot draws its dots on the axis rows, which the script does not
        # rebuild for a computed layer: no recount, the build's cue kind.
        r = _pair(ptype, "dot")
        assert not any(hasattr(g, "_dash_agg_config")
                       for g in _recast_renderers(r))


@requires_node
def test_turned_histogram_line_follows_the_move():
    r = _pair("histogram", "line", extra={"horizontal": "horizontal"})
    _move(r, _MOVES[0][2])
    px, py = _plain_points(r, "histogram")
    [g] = _recast_renderers(r)
    cols = g._dash_agg_config["recast_cols"]
    d = g.data_source.data
    xs = [k for k, v in cols.items() if v == "x"]
    ys = [k for k, v in cols.items() if v == "y"]
    assert xs and ys
    for k in xs:
        np.testing.assert_allclose(np.asarray(d[k], float), px)
    for k in ys:
        np.testing.assert_allclose(np.asarray(d[k], float), py)
