"""
test_by_contour_cuts.py -- contour and contourline under by(): every panel
cut at the first panel's cuts (WP-41 BY-28, section 41-01).

The defect (the audit, BY-28): ``contour price mpg weight, by(rep78,
total)`` drew 4, 5, 3, 3, 4 and 3 levels -- each panel cut at the z ticks
of its own rows (``GlyphMapper.map_contour`` read the panel's own z range),
so one colour meant a different z range in each panel.

twoway (scripts/extract_by_contour_truth.do, fixture
test/fixtures/by_contour_truth.json, each panel's
``.G.graphs[i].plotregion1.plot1.lastcuts`` after ``graph export``) reads
one z axis: every panel, the Total panel too, is cut at the first panel's
cuts -- those of the first panel drawn alone -- not at the union of the
panels.  dash now carries the first panel's z range to every panel
(``_dash_by_contour_zranges``, ``_dash_by_zrange_spec``), in both modes,
and after a filter move re-cuts every panel at the first panel that keeps
rows (``dash_contour_zfirst`` on the saved page, ``_dash_by_first_zranges``
in the served app).  A gridded layer's panels keep Stata's own polygons
and cuts (WP-37 TR-13); a panel of such a layer that dash fits takes the
same cuts (``_dash_by_contour_gen_cuts``).
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
import test_contour_gen as cgt  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_contour_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")

#: auto's rows the probes draw, with nf = 1 - foreign.
_AUTO = pd.DataFrame({k: [np.nan if v is None else v for v in col]
                      for k, col in _T["rows"].items()})
_AUTO["nf"] = 1.0 - _AUTO["foreign"]

#: Each probe as dash is given it: (type, options, by(), graph if).
_PROBES = {
    "C01": ("contour", {}, "foreign", ""),
    "C02": ("contour", {}, "nf", ""),
    "C03": ("contour", {}, "rep78, total", ""),
    "C04": ("contourline", {}, "nf", ""),
    "C05": ("contour", {"levels": "4"}, "nf", ""),
    "C06": ("contour", {"ccuts": "5000 9000"}, "nf", ""),
    "C07": ("contour", {}, "nf, total", ""),
    "C08": ("contour", {}, "nf, rescale", ""),
    "C09": ("contour", {}, "nf, clegend(on)", ""),
    "C10": ("contour", {}, "rep78", "rep78 > 2"),
}


def _plot(ptype="contour", opts=None):
    return {"type": ptype, "zvar": "price", "yvar": "mpg", "xvar": "weight",
            "options": dict(opts or {})}


def _figs(mode, spec, df=None):
    df = _AUTO if df is None else df
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            return jo._saved_figs(jo._saved(spec, df))
        return jo._served_figs(jo._served(spec, df))


def _panel_cuts(figs, ptype):
    """Each drawn panel's inner cuts, read from its contour layer's drawn
    source (the served redraw and the saved refit write it): a filled
    layer's band floors past the first, a line layer's levels."""
    out = []
    for f in figs:
        crs = [r for r in f.renderers
               if type(r).__name__ == "ContourRenderer"
               and "dash_contour" in (r.tags or [])]
        if not crs:
            continue
        if ptype == "contourline":
            d = crs[0].line_renderer.data_source.data
            out.append([float(v) for v in d["levels"]])
        else:
            d = crs[0].fill_renderer.data_source.data
            out.append([float(v) for v in list(d["lower_levels"])[1:]])
    return out


def _probe_spec(pid, extra_bo=None):
    ptype, opts, by, gif = _PROBES[pid]
    return tp._spec([_plot(ptype, opts)], extra_bo,
                    graph_options={"by": by}, if_expr=gif)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_first_panel_rule(self):
        """Guard: twoway cut every panel at its first panel's cuts, which
        are those of the first panel drawn alone."""
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]
        assert sorted(_T["probes"]) == sorted(_PROBES)
        for pid, p in _T["probes"].items():
            assert p["rc"] == 0, pid
            assert p["panels"] == len(p["cuts"]) >= 2, pid
            for c in p["cuts"]:
                assert c == p["cuts"][0], pid
            assert p["first_alone"] == p["cuts"][0], pid
        assert _T["probes"]["C03"]["panels"] == 6
        assert _T["probes"]["C07"]["panels"] == 3


# ---------------------------------------------------------------------------
# The panels' cuts
# ---------------------------------------------------------------------------

class TestByContourCuts:

    @pytest.mark.parametrize("pid", sorted(_PROBES))
    @pytest.mark.parametrize("mode", _MODES)
    def test_panels_share_the_first_panels_cuts(self, mode, pid):
        want = _T["probes"][pid]
        got = _panel_cuts(_figs(mode, _probe_spec(pid)), _PROBES[pid][0])
        assert len(got) == want["panels"], got
        for c in got:
            assert c == pytest.approx(want["cuts"][0], rel=1e-9, abs=1e-9), \
                (pid, got)


# ---------------------------------------------------------------------------
# The rule's helpers
# ---------------------------------------------------------------------------

class TestTheRule:

    def test_zrange_of(self):
        plot = _plot()
        rows = pd.DataFrame({"weight": [1.0, np.nan, 3.0, 4.0],
                             "mpg": [1.0, 2.0, 3.0, np.nan],
                             "price": [5.0, -100.0, 7.0, 900.0]})
        # a row with x or y missing is left out
        assert dr._dash_contour_zrange_of(rows, plot) == [5.0, 7.0]
        # no row with x, y and z
        assert dr._dash_contour_zrange_of(rows.iloc[[1, 3]], plot) is None
        assert dr._dash_contour_zrange_of(rows.iloc[0:0], plot) is None
        # a column the frame lacks, or no plot
        assert dr._dash_contour_zrange_of(rows, dict(plot, zvar="q")) is None
        assert dr._dash_contour_zrange_of(rows, None) is None
        # a %td z, held in epoch ms, read in its Stata days
        day = 86_400_000.0
        epoch = float(dr._STATA_EPOCH_UNIX_MS)
        dz = rows.assign(price=[epoch + 10 * day, 0.0, epoch + 20 * day,
                                epoch])
        assert dr._dash_contour_zrange_of(dz, plot, {"price": "td"}) \
            == pytest.approx([10.0, 20.0])

    def test_zranges_read_the_qualifier(self):
        frame = pd.DataFrame({"weight": [1.0, 2.0, 3.0, 4.0],
                              "mpg": [1.0, 2.0, 3.0, 4.0],
                              "price": [10.0, 20.0, 30.0, 40.0],
                              "q": [0.0, 1.0, 1.0, 0.0]})
        gdf = frame.iloc[0:3]
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {}},
                 dict(_plot(), if_expr="q == 1"),
                 _plot("contourline")]
        got = dr._dash_by_contour_zranges(gdf, frame, plots)
        assert got == {1: [20.0, 30.0], 2: [10.0, 30.0]}
        # a plot whose qualifier keeps no row is left out
        plots[1] = dict(_plot(), if_expr="q == 5")
        assert dr._dash_by_contour_zranges(gdf, frame, plots) == {
            2: [10.0, 30.0]}

    def test_spec(self):
        g = {"plots": [{"type": "scatter", "options": {"a": 1}},
                       _plot()], "name": "g1"}
        assert dr._dash_by_zrange_spec(g, {}, 0, "g1") is g
        out = dr._dash_by_zrange_spec(g, {1: [1.0, 2.0]}, 2, "g1",
                                      {0: [5.0]})
        assert out is not g and out["plots"][0] is g["plots"][0]
        o1 = out["plots"][1]["options"]
        assert o1 == {"_dash_by_zrange": [1.0, 2.0],
                      "_dash_by_zshare": "g1|1", "_dash_by_zpanel": 2}
        assert g["plots"][1]["options"] == {}
        out = dr._dash_by_zrange_spec(g, {1: [1.0, 2.0]}, 0, "g1",
                                      {1: [3.0, 4.0]})
        assert out["plots"][1]["options"]["_dash_by_zcuts"] == [3.0, 4.0]

    def test_gen_cuts(self):
        def gen(obj):
            return _plot("contour", {"contour_gen": obj})
        grid = {"cuts": [2.0, 1.0]}
        plots = [
            gen({"panels": [{"key": [0], "grid": {"cuts": []}},
                            {"key": [1], "grid": grid}]}),
            gen({"panels": [], "total": {"cuts": [7.0]}}),
            gen({"cuts": [1.0]}),
            {"type": "scatter", "options": {"contour_gen": {
                "panels": [{"grid": grid}]}}},
            gen({"panels": [{"grid": {"cuts": [1.0, True]}}]}),
            gen({"panels": [{"grid": {"cuts": [float("nan")]}}]}),
            gen({"panels": "x"}),
            _plot(),
        ]
        assert dr._dash_by_contour_gen_cuts(plots) == {0: [1.0, 2.0],
                                                       1: [7.0]}
        assert dr._dash_by_contour_gen_cuts(None) == {}

    def test_first_zranges(self):
        """The served move's rule: per zshare, the lowest zpanel with a
        kept range; an agg with no zshare is not asked."""
        def agg(share, panel, r):
            def redraw(frame, zrange=None):
                return []
            redraw.zrange = lambda frame: r
            return {"zshare": share, "zpanel": panel, "redraw": redraw}
        asked = []
        aggs = {"a": agg("g|0", 1, [1.0, 2.0]), "b": agg("g|0", 0, None),
                "c": agg("g|0", 2, [5.0, 6.0]), "d": agg("h|1", 3, [7.0, 8.0]),
                "e": agg(None, 0, [0.0, 0.0])}
        got = dr._dash_by_first_zranges(
            aggs, lambda k: asked.append(k) or k)
        assert got == {"g|0": [1.0, 2.0], "h|1": [7.0, 8.0]}
        assert "e" not in asked
        assert dr._dash_by_first_zranges({}, lambda k: k) == {}

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_by_unchanged(self, mode):
        """Guard: a contour with no by() is cut at its own range and its
        page config carries no zshare."""
        spec = tp._spec([_plot()])
        [f] = [f for f in _figs(mode, spec) if _panel_cuts([f], "contour")]
        z = _AUTO.dropna(subset=["price", "mpg", "weight"])["price"]
        cuts, _t = dr._dash_contour_cuts({}, float(z.min()), float(z.max()))
        assert _panel_cuts([f], "contour")[0] == pytest.approx(cuts)
        if mode == "saved":
            [cr] = [r for r in f.renderers
                    if type(r).__name__ == "ContourRenderer"]
            assert cr._dash_contour_config.get("zshare") is None


# ---------------------------------------------------------------------------
# A gridded layer (WP-37 TR-13)
# ---------------------------------------------------------------------------

class TestGridPanels:

    @pytest.mark.parametrize("mode", _MODES)
    def test_gridded_panels_keep_statas_cuts(self, mode):
        """Panel 0 drawn from its contour_gen object at the object's cuts;
        panel 1, with no object, fitted by dash and cut at the same cuts."""
        df = cgt._grid_df()
        df["g"] = df["half"]
        # The object's cuts moved off the grid's own -1, 0, 1 (which dash's
        # rule also gives every half of the grid), so a panel cut at its
        # own range is told apart from one cut at Stata's cuts.
        obj = dict(cgt._obj("grid40", n=800), cuts=[-1.5, 0.0, 1.5])
        spec = tp._spec([cgt._plot("contour", {"contour_gen": {"panels": [
            {"key": [0], "grid": obj}]}})], graph_options={"by": "g"})
        figs = [f for f in _figs(mode, spec, df) if cgt._crs(f)]
        assert len(figs) == 2
        want = [float(c) for c in obj["cuts"]]
        for f in figs:
            assert _panel_cuts([f], "contour")[0] == pytest.approx(want)
        # the second panel is dash's own fit: one item per band
        [c1] = cgt._crs(figs[1])
        assert len(c1.fill_renderer.data_source.data["xs"]) == len(
            c1.levels) - 1


# ---------------------------------------------------------------------------
# The saved page's twins
# ---------------------------------------------------------------------------

def _twin_js(code):
    return run_js(js_runner.fit_helpers_js()
                  + "\nconst out = (v) => process.stdout.write("
                  "JSON.stringify(v));\n" + code)


@requires_node
class TestTwins:

    @pytest.mark.parametrize("kind", ["numeric", "td"])
    def test_zfirst_equals_python(self, kind):
        rng = np.random.default_rng(7)
        n = 30
        z = np.round(rng.uniform(100, 900, n), 0)
        if kind == "td":
            z = float(dr._STATA_EPOCH_UNIX_MS) + z * 86_400_000.0
        x = rng.uniform(0, 1, n)
        x[3] = np.nan
        y = rng.uniform(0, 1, n)
        rid = list(range(n))
        frame = pd.DataFrame({"weight": x, "mpg": y, "price": z})
        dk = "td" if kind == "td" else None
        want = {}
        cfgs = []
        # panel 1 is listed first: the lowest zpanel decides
        for zp, ids in ((1, rid[15:]), (0, rid[:15]), (0, [])):
            share = "g1|0" if ids else "g2|0"
            cfgs.append({"type": "contour", "xvar": "weight",
                         "yvar": "mpg", "zvar": "price", "use": [],
                         "zdatekind": dk, "member_ids": ids,
                         "zshare": share, "zpanel": zp})
        want["g1|0"] = dr._dash_contour_zrange_of(
            frame.iloc[rid[:15]], _plot(), {"price": "td"} if dk else None)
        data = {"weight": [None if not np.isfinite(v) else v for v in x],
                "mpg": list(y), "price": list(z), dr._ROW_ID_COLUMN: rid}
        got = _twin_js(
            "const DATA = JSON.parse(%s);\n"
            "function dash_data_for(u) { return DATA; }\n"
            "DATA.weight = DATA.weight.map(v => v === null ? NaN : v);\n"
            "out(dash_contour_zfirst(JSON.parse(%s)));"
            % (json.dumps(json.dumps(data)), json.dumps(json.dumps(cfgs))))
        assert sorted(got) == ["g1|0"]
        assert got["g1|0"] == pytest.approx(want["g1|0"], rel=1e-12)

    def test_stata_units_is_the_branchs(self):
        js = dr._FILTER_JS
        assert "const _su = dash_stata_units;" in js
        ms = [float(dr._STATA_EPOCH_UNIX_MS) + d * 86_400_000.0
              for d in (0.0, 1.5, 15000.0, -200.0)]
        got = _twin_js("out(dash_stata_units(%s, 'td'));" % json.dumps(ms))
        assert got == pytest.approx(
            list(dr._dash_date_units(np.asarray(ms), "td")), rel=1e-12)


# ---------------------------------------------------------------------------
# After a filter move
# ---------------------------------------------------------------------------

#: A range filter on rep78 moved to keep rep78 of 4 and 5.
_MOVE_FILTER = "rep78, type(range)"
_MOVE = ("RangeSlider", (4.0, 5.0))


@pytest.mark.parametrize("mode", _MODES)
class TestAfterAMove:

    def test_both_modes_share(self, mode):
        spec = tp._spec([_plot()], {"filter": _MOVE_FILTER},
                        graph_options={"by": "nf"})
        if mode == "saved":
            js_runner.node()
            _r, after = hm._saved_moved(spec, _MOVE, _AUTO)
        else:
            _d, after = hm._served_moved(spec, _MOVE, _AUTO)
        got = _panel_cuts(after, "contour")
        first = _AUTO[(_AUTO["nf"] == 0) & (_AUTO["rep78"] >= 4)].dropna(
            subset=["price", "mpg", "weight"])["price"]
        want, _t = dr._dash_contour_cuts({}, float(first.min()),
                                         float(first.max()))
        assert len(got) == 2
        for c in got:
            assert c == pytest.approx(want, rel=1e-9), got
