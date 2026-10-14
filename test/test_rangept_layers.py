"""
test_rangept_layers.py -- twoway rpcap and rpspike (WP-31 B1, section 21).

The defect (measured at d887f0d): ``dash rpcap lo hi turn weight`` and
``dash rpspike ...`` were refused by name, r(198), "a twoway plot type
dash does not draw", although twoway draws both (Stata 19,
``twoway_rpcap_parse.class`` inherits ``twoway_y3xview_parse``).

twoway (StataNow 19.5, scripts/extract_rangept_truth.do, fixture
test/fixtures/rangept_truth.json): four variables y1 y2 y3 x
(``y3xview_parse``: one is "too few variables specified", two, three or
five "you must specify four variables with twoway rpcap", r(102) below and
r(103) above); a spike from (x, y1) to (x, y2), at both ends a cap as wide
as the marker (rpcap only; ``yxview_rpcap_draw.ado``: ``sz =
.style.marker.size.gmval``), and the layer's marker at (x, y3); msize()
sizes caps and marker together; the y axis ranges over the three y
variables (``y3xview_g.ranges``); its title is ``L(y1)/L(y2)/L(y3)`` unless
the three labels are equal (``dimtitle``); one legend key; ``horizontal``
turns the layer; a weight sizes the y3 markers.

dash draws the layer as map_rcap (or map_rspike) and map_scatter on the
same rows (GlyphMapper.map_rpcap / map_rpspike), in both modes.
"""
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402
from js_runner import requires_node  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "rangept_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
_TURN = [40.0, 40.0, 35.0, 40.0, 43.0, 43.0, 34.0, 42.0, 43.0, 42.0]
_DF = pd.DataFrame({
    "lo": [t - 5 for t in _TURN],
    "hi": [t + 5 for t in _TURN],
    "turn": _TURN,
    "weight": [2930.0, 3350.0, 2640.0, 3250.0, 4080.0, 3670.0, 2230.0,
               3280.0, 3880.0, 3400.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 7827.0, 5788.0, 4453.0,
              5189.0, 10372.0, 4082.0],
})


def _plot(ptype, opts=None):
    return {"type": ptype, "yvar1": "lo", "yvar2": "hi", "yvar": "turn",
            "xvar": "weight", "options": dict(opts or {})}


def _fig(mode, tmp_path, ptype="rpcap", opts=None, plots=None, bo=None):
    figs, _notes = bg._figs(mode, tmp_path,
                            bg._spec(plots or [_plot(ptype, opts)], bo=bo),
                            _DF)
    return figs[0]


def _drawn(f):
    return [r for f_r in [f] for r in f_r.renderers
            if getattr(r, "glyph", None) is not None
            and not dr._dash_is_swatch(r)]


def _segments(f):
    return [r for r in _drawn(f) if type(r.glyph).__name__ == "Segment"]


def _caps(f):
    return [r for r in _drawn(f) if type(r.glyph).__name__ == "Scatter"
            and "dash_cap" in (r.tags or [])]


def _markers(f):
    return [r for r in _drawn(f) if type(r.glyph).__name__ == "Scatter"
            and "dash_cap" not in (r.tags or [])]


def _field(spec):
    return spec if isinstance(spec, str) else getattr(spec, "field", None)


class TestTheFixture:

    def test_meta_and_keys(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]
        assert _T["_meta"]["source"] == "scripts/extract_rangept_truth.do"
        for k in ("rpcap", "rpcap_msize", "rpcap_hz", "rpcap_weight",
                  "rpspike", "rpspike_hz", "rpspike_weight",
                  "rcap_scatter", "rpcap_colorvar", "rpspike_colorvar"):
            assert k in _T["draw"], k
        for t in ("rpcap", "rpspike"):
            for n in range(1, 6):
                assert "counts.%s_%d" % (t, n) in _T["probes"]
        for k in ("abbrev.rpca", "abbrev.rpspik", "abbrev.sunflow",
                  "draw.sunflower", "barwidth.rpcap", "advice.matamatrix",
                  "matamatrix.defined", "matamatrix.upper"):
            assert k in _T["probes"], k
        assert set(_T["title"]) >= {"differs", "same"}
        assert _T["advice"]["sunflower"] and _T["advice"]["matamatrix"]

    def test_twoways_values(self):
        d = _T["draw"]
        assert d["rpcap"]["roles"] == {"yvar": "lo", "y2var": "hi",
                                       "y3var": "turn", "xvar": "weight",
                                       "wvar": ""}
        assert d["rpcap"]["legend_keys"] == 1
        assert d["rpcap_hz"]["bar_drop_to"] == "y"
        assert d["rpcap_msize"]["marker_size_gmval"] > \
            d["rpcap"]["marker_size_gmval"]
        # The y range over the three: the same axis as rcap lo hi plus
        # scatter turn on the same x.
        assert d["rpcap"]["yaxis_major"] == d["rcap_scatter"]["yaxis_major"]
        assert _T["title"] == {"differs": "Low/High/Turn", "same": "Turn",
                               "same_hz": "Turn"}
        p = _T["probes"]
        for t in ("rpcap", "rpspike"):
            assert (p["counts.%s_1" % t]["rc"],
                    p["counts.%s_1" % t]["message"]) == (
                102, "too few variables specified")
            for n, rc in ((2, 102), (3, 102), (5, 103)):
                q = p["counts.%s_%d" % (t, n)]
                assert (q["rc"], q["message"]) == (
                    rc, "you must specify four variables with twoway %s" % t)
            assert p["counts.%s_4" % t]["rc"] == 0
        assert p["abbrev.rpca"]["rc"] == 198
        assert p["abbrev.rpspik"]["rc"] == 198


class TestRpcapDraws:

    @pytest.mark.parametrize("mode", _MODES)
    def test_spike_caps_and_marker(self, mode, tmp_path):
        f = _fig(mode, tmp_path)
        [seg] = _segments(f)
        assert len(_caps(f)) == 2
        [mk] = _markers(f)
        assert _field(seg.glyph.y0) == "lo" and _field(seg.glyph.y1) == "hi"
        assert _field(mk.glyph.y) == "turn"
        assert _field(mk.glyph.x) == "weight"
        assert len(mk.data_source.data["turn"]) == len(_DF)


class TestRpspikeDraws:

    @pytest.mark.parametrize("mode", _MODES)
    def test_spike_and_marker(self, mode, tmp_path):
        f = _fig(mode, tmp_path, "rpspike")
        [seg] = _segments(f)
        assert not _caps(f)
        [mk] = _markers(f)
        assert _field(seg.glyph.y0) == "lo" and _field(mk.glyph.y) == "turn"


class TestCapWidthIsMarkerSize:

    @pytest.mark.parametrize("mode", _MODES)
    def test_default_and_msize(self, mode, tmp_path):
        f = _fig(mode, tmp_path)
        f2 = _fig(mode, tmp_path, opts={"msize": "large"})
        sizes = []
        for g in (f, f2):
            [mk] = _markers(g)
            for c in _caps(g):
                assert float(c.glyph.size) == pytest.approx(
                    float(mk.glyph.size))
            sizes.append(float(mk.glyph.size))
        assert sizes[1] > sizes[0]


class TestTheReaders:

    @pytest.mark.parametrize("mode", _MODES)
    def test_axis_names_and_range(self, mode, tmp_path):
        p = _plot("rpcap")
        assert dr._dash_layer_axis_names(p, "yvar") == (
            1, ["lo", "hi", "turn"])
        assert dr._dash_layer_axis_names(p, "xvar") == (1, ["weight"])
        assert dr._dash_axis_vars([p]) == ("weight", "lo")
        # The marker reaches beyond the range: y3 = 60 above every hi.
        df = _DF.copy()
        df.loc[0, "turn"] = 60.0
        figs, _ = bg._figs(mode, tmp_path, bg._spec([p]), df)
        f = figs[0]
        assert f.y_range.end >= 60.0
        assert f.y_range.start <= float(df["lo"].min())

    def test_series_label(self):
        p = _plot("rpcap")
        assert dr._dash_layer_series(p, {"lo": "Low", "hi": "High",
                                         "turn": "Turn"}) == [
            ("Low/High/Turn", "weight")]
        assert dr._dash_layer_series(p, {"lo": "Turn", "hi": "Turn",
                                         "turn": "Turn"}) == [
            ("Turn", "weight")]
        # No labels: the names (fixture: "lo/hi/Turn circle (ft.)").
        assert dr._dash_layer_series(p, {})[0][0] == "lo/hi/turn"

    def test_hover_vars(self):
        assert dr._dash_hover_layer_vars(_plot("rpcap")) == [
            "weight", "lo", "hi", "turn"]

    def test_tick_format_reads_y1(self):
        fmt = dr._dash_layer_tick_format(
            _plot("rpcap"), "y", {"lo": "%9.1f", "turn": "%9.3f"}, {})
        assert fmt == ("%9.1f", False)


class TestHorizontal:

    @pytest.mark.parametrize("mode", _MODES)
    def test_turned(self, mode, tmp_path):
        f = _fig(mode, tmp_path, opts={"horizontal": "horizontal"})
        [seg] = _segments(f)
        [mk] = _markers(f)
        assert _field(seg.glyph.x0) == "lo" and _field(seg.glyph.x1) == "hi"
        assert _field(seg.glyph.y0) == "weight"
        assert _field(mk.glyph.x) == "turn" and _field(mk.glyph.y) == "weight"
        assert all(c.glyph.angle != 0 for c in _caps(f))

    def test_registered(self):
        for t in ("rpcap", "rpspike"):
            assert t in dr._DASH_HORIZONTAL_TYPES
            assert t in dr._DASH_VERTICAL_TYPES


class TestLegendKey:

    @pytest.mark.parametrize("mode", _MODES)
    def test_one_key_two_renderers(self, mode, tmp_path):
        """With a second layer the legend shows: the rpcap layer is one
        item holding its spike, caps and marker."""
        sc = {"type": "scatter", "yvar": "price", "xvar": "weight",
              "options": {}}
        f = _fig(mode, tmp_path, plots=[_plot("rpcap"), sc])
        [leg] = f.legend
        assert len(leg.items) == 2
        kinds = sorted(type(r.glyph).__name__
                       for r in leg.items[0].renderers)
        assert "Segment" in kinds and kinds.count("Scatter") == 3, kinds


def _move_spec(ptype):
    return tp._spec([_plot(ptype)], {"filter": sf._MOVES[0][1]})


def _layer_rows(figs):
    """The rows each drawn renderer of the first figure holds."""
    out = []
    for r in _drawn(figs[0]):
        d = r.data_source.data
        col = "weight" if "weight" in d else sorted(d)[0]
        out.append((type(r.glyph).__name__, len(d[col])))
    return sorted(out)


class TestMoves:

    @pytest.mark.parametrize("ptype", ["rpcap", "rpspike"])
    @pytest.mark.parametrize("mode", [
        pytest.param("saved", marks=requires_node), "served"])
    def test_rows_follow_the_filter(self, mode, ptype):
        _label, _f, action, oracle = sf._MOVES[0]
        after = hm._moved(_move_spec(ptype), action, mode, df=_DF)
        kept = hm._kept(_move_spec(ptype), oracle, mode, df=_DF)
        n_kept = int((_DF["foreign"] == 1).sum())
        got = _layer_rows(after)
        assert got == _layer_rows(kept)
        assert got and all(n == n_kept for _k, n in got), got


class TestServedCarries:

    def test_constant_copied(self, tmp_path):
        assert dr._DASH_RANGEPT_TYPES == frozenset({"rpcap", "rpspike"})
        sp, dp = bg._write(tmp_path, bg._spec([_plot("rpcap")]), _DF)
        app = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        assert re.search(r"^_DASH_RANGEPT_TYPES = ", src, re.M)


class TestWeightMeasured:

    def test_twoway_sizes_the_markers_and_so_does_dash(self):
        """twoway sizes rpcap's and rpspike's y3 markers by an aweight,
        fweight or pweight (fixture draw.rpcap_weight: 114 radii where the
        unweighted graph draws 2) and refuses an iweight, r(101); the
        weight text is read as its other yxview views read it
        (wexp.*: [aw=price-price] r(101), [aw=(price)] r(198)), no
        weight above zero stops it, r(198) (wzero.*), and labelled or
        point markers keep their size (wmlabel.*, wpoint.*).  Flipped
        (WP-31 B1, after section 20's weighted markers landed): dash
        named the weight and drew every marker at one size."""
        for t in ("rpcap", "rpspike"):
            assert _T["draw"][t + "_weight"]["radii_vary_with_weight"]
        p = _T["probes"]
        assert p["fw.rpcap"]["rc"] == 0 and p["pw.rpcap"]["rc"] == 0
        assert (p["iw.rpcap"]["rc"], p["iw.rpcap"]["message"]) == (
            101, "iweights not allowed")
        assert (p["wexp.rpcap_minus"]["rc"],
                p["wexp.rpcap_minus"]["message"]) == (101, "- not allowed")
        assert (p["wexp.rpcap_paren"]["rc"],
                p["wexp.rpcap_paren"]["message"]) == (198, "( invalid name")
        assert p["wzero.rpcap"]["rc"] == p["wzero.rpspike"]["rc"] == 198
        assert p["wmlabel.rpcap"]["n_radii"] == p["plain.rpcap"]["n_radii"]
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        m = re.search(r'local _wt_markers "([^"]*)"', ado)
        for t in ("rpcap", "rpspike"):
            assert t in m.group(1).split(), t
            assert dr._DASH_WEIGHT_ACCEPTS[t] == ("aw", "fw", "pw")
            assert t in dr.GlyphMapper._WEIGHTED_MARKER_TYPES

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_marker_is_sized_and_the_caps_are_not(self, mode, tmp_path):
        f = _fig(mode, tmp_path, opts={"weight": "aweight", "wexp": "price"})
        [mk] = _markers(f)
        assert isinstance(mk.glyph.size, str)
        sizes = np.asarray(mk.data_source.data[mk.glyph.size], dtype=float)
        assert len(set(np.round(sizes, 9))) > 1
        for c in _caps(f):
            assert not isinstance(c.glyph.size, str)
