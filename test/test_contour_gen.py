"""
test_contour_gen.py -- contour and contourline over a full grid, or with
interp(none), draw twoway's own polygons (WP-37 section 37-03, TR-13 with
stat:PT-19 and sil:SD-19).

The defect (measured at 80d59b8): every sandstone help example -- 6,400
points on an 80 x 80 grid -- printed "contour draws an approximate
surface" and drew dash's fit of a seeded 1,000-point subsample on a
100 x 100 grid, where twoway runs twoway__contour_gen on the plot's rows
and draws its polygons (5,668 for the default cuts 7700 7800 7900 8000).
dash.ado now runs the generator at export, in a frame, and writes its rows
as the layer's ``contour_gen`` object (per by() panel under by()); both
renderers draw them.  After a filter move that leaves rows out both modes
draw dash's own fit of the kept rows with the stale cue (DECISIONS A-26).

Fixture: test/fixtures/contour_gen_truth.json
(scripts/extract_contour_gen_truth.do).  test_wp37_truth.cscript S03
(Q3703-1..6) checks the Stata side live.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_contour_js as cj  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from js_runner import requires_node  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "contour_gen_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("std", "srv")
_N = [0]


def _obj(key, n=None, lines=None):
    """A contour_gen object built from the fixture's rows of *key*."""
    d = _T[key]
    rows = d["rows"]
    out = {"cuts": list(d["cuts"]), "line": d["line"],
           "x": [r[0] for r in rows], "y": [r[1] for r in rows],
           "z": [r[2] for r in rows], "levels": [r[3] for r in rows],
           "n": d["n"] if n is None else n}
    if lines is not None:
        lo = _obj(lines)
        out["lines"] = {k: lo[k] for k in ("x", "y", "z", "levels")}
    return out


def _grid_df(side=40):
    """The fixture's grid: x = mod(_n-1, side), y = floor((_n-1)/side),
    z = sin(x/6) + cos(y/7)."""
    i = np.arange(side * side)
    df = pd.DataFrame({"x": (i % side).astype(float),
                       "y": (i // side).astype(float)})
    df["z"] = np.sin(df["x"] / 6) + np.cos(df["y"] / 7)
    df["half"] = (df["y"] >= side / 2).astype(float)
    return df


def _plot(ptype, opts=None):
    return {"type": ptype, "zvar": "z", "yvar": "y", "xvar": "x",
            "options": dict(opts or {})}


def _figs(mode, spec, df):
    """The figures *spec* draws over *df* in *mode*."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "std":
            return jo._saved_figs(jo._saved(spec, df))
        return jo._served_figs(jo._served(spec, df))


def _figs_msgs(mode, spec, df):
    """The figures and every warning the build raised."""
    dr._DASH_NOTED.clear()
    if mode == "std":
        r, msgs, _html = jo._saved(spec, df, page=True)
        return jo._saved_figs(r), msgs
    doc, msgs = jo._served(spec, df, msgs=True)
    return jo._served_figs(doc), msgs


def _crs(fig, tag="dash_contour"):
    return [r for r in fig.renderers
            if type(r).__name__ == "ContourRenderer" and tag in (r.tags or [])]


def _runs(obj):
    """[(level, nvertices)] per run of the object's rows."""
    out, cur, lev = [], 0, None
    for x, y, z, lv in zip(obj["x"], obj["y"], obj["z"], obj["levels"]):
        if x is None and y is None and z is None:
            if cur:
                out.append((lev, cur))
            cur, lev = 0, None
            continue
        if lev is None:
            lev = lv
        cur += 1
    if cur:
        out.append((lev, cur))
    return out


def _band_of(lower, fl):
    return min(range(len(fl) - 1), key=lambda b: abs(fl[b] - lower))


def _items_per_band(cr):
    """Polygons per band of a drawn fill source, by its lower level."""
    d = cr.fill_renderer.data_source.data
    fl = list(cr.levels)
    out = [0] * (len(fl) - 1)
    for xs, lo in zip(d["xs"], d["lower_levels"]):
        out[_band_of(float(lo), fl)] += len(xs)
    return out


def _lines(data):
    """NaN-separated runs per item of a line source."""
    out = []
    for xs in data["xs"]:
        a = np.asarray(xs, float)
        runs, inrun = 0, False
        for v in a:
            if np.isnan(v):
                inrun = False
            elif not inrun:
                runs += 1
                inrun = True
        out.append(runs)
    return out


class TestTheFixture:

    def test_meta_and_generator_ran(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]
        assert _T["_meta"]["source"] == "scripts/extract_contour_gen_truth.do"
        probes = [k for k in _T if k not in ("_meta", "sandstone.outlines",
                                             "sandstone.by")]
        assert len(probes) == 11
        for k in probes:
            assert _T[k]["gen_rc"] == 0, k
            assert _T[k]["levels_nondecreasing"] in (0, 1), k
            assert _T[k]["cuts_equal_dash"] in (0, 1), k
        for k in ("grid40", "grid40.line"):
            assert len(_T[k]["rows"]) == _T[k]["row_count"] > 0
        assert _T["sandstone.default"]["cuts"] == [7700, 7800, 7900, 8000]
        assert _T["sandstone.default"]["row_count"] == 32689
        assert _T["sandstone.default.line"]["lines_per_cut"] == [2, 2, 10, 9]
        o = _T["sandstone.outlines"]
        assert o["outlines_are_cut_lines"] in (0, 1)
        assert isinstance(o["edge_segments"], int)
        b = _T["sandstone.by"]
        assert len(b["panels"]) == 2 and b["first_panel_rule"] in (0, 1)
        for p in b["panels"]:
            assert p["polys_per_band"] == p["gen_polys_per_band"]
            assert p["n"] == 3200


@pytest.mark.parametrize("mode", _MODES)
class TestTheRenderer:

    def test_a_grid_object_is_drawn(self, mode):
        """The 40 x 40 grid's object draws exactly its polygons per band,
        one fill item per band: BokehJS's colour key paints from the fill
        items and throws ("Inconsistent number of filled contour levels")
        unless there is one per band (measured in headless Chrome)."""
        spec = tp._spec([_plot("contour", {"contour_gen": _obj("grid40")})])
        [fig] = _figs(mode, spec, _grid_df())
        [cr] = _crs(fig)
        assert _items_per_band(cr) == _T["grid40"]["polys_per_band"]
        d = cr.fill_renderer.data_source.data
        assert len(d["xs"]) == len(d["fill_color"]) == len(cr.levels) - 1

    def test_no_cap_note_with_a_grid(self, mode):
        """A 50 x 50 grid (2,500 distinct points, above the cap) carrying
        an object draws it with no approximation note."""
        df = _grid_df(50)
        spec = tp._spec([_plot("contour", {"contour_gen": _obj(
            "grid40", n=2500)})])
        figs, msgs = _figs_msgs(mode, spec, df)
        assert not [m for m in msgs if "approximate surface" in m]
        [cr] = _crs(figs[0])
        assert _items_per_band(cr) == _T["grid40"]["polys_per_band"]

    def test_contourline_object(self, mode):
        spec = tp._spec([_plot("contourline",
                               {"contour_gen": _obj("grid40.line")})])
        [fig] = _figs(mode, spec, _grid_df())
        [cr] = _crs(fig)
        d = cr.line_renderer.data_source.data
        assert [float(v) for v in d["levels"]] == _T["grid40.line"]["cuts"]
        assert _lines(d) == _T["grid40.line"]["lines_per_cut"]
        xs = [np.asarray(r[0], float) if r[0] is not None else np.nan
              for r in _T["grid40.line"]["rows"]]
        drawn = np.concatenate([np.asarray(a, float) for a in d["xs"]])
        assert np.isfinite(drawn).sum() == np.isfinite(
            np.asarray(xs, float)).sum()
        assert sorted(drawn[np.isfinite(drawn)].tolist()) == sorted(
            v for v in np.asarray(xs, float).tolist() if v == v)

    @pytest.mark.parametrize("opt", [{"outlines": "outlines"},
                                     {"alpattern": "dash"},
                                     {"sort": "sort"}],
                             ids=["outlines", "alpattern", "sort"])
    def test_boundary_lines_come_from_the_grid(self, mode, opt):
        cg = _obj("grid40", lines="grid40.line")
        spec = tp._spec([_plot("contour", dict(opt, contour_gen=cg))])
        [fig] = _figs(mode, spec, _grid_df())
        [lr] = _crs(fig, "dash_contour_lines")
        d = lr.line_renderer.data_source.data
        xs, _ys = dr._dash_contour_gen_lines(cg["lines"], 3)
        assert len(d["xs"]) == 3
        for a, b in zip(d["xs"], xs):
            np.testing.assert_array_equal(np.asarray(a, float), b)
        assert _lines(d) == _T["grid40.line"]["lines_per_cut"]
        med = float(dr.OptionTranslator.translate_lwidth("medium"))
        if "outlines" in opt:
            assert list(d["line_color"]) == ["#000000"] * 3
            assert [float(w) for w in d["line_width"]] == [2 * med] * 3
        else:
            assert [float(w) for w in d["line_width"]] == [
                med * dr._DASH_CONTOUR_HAIRLINE] * 3
            assert all(list(p) for p in d["line_dash"])

    def test_horizontal_swaps(self, mode):
        spec = tp._spec([_plot("contour", {"contour_gen": _obj("grid40"),
                                           "horizontal": "horizontal"})])
        [fig] = _figs(mode, spec, _grid_df())
        [cr] = _crs(fig)
        d = cr.fill_renderer.data_source.data
        first = _T["grid40"]["rows"][0]
        # The first ring's first vertex, turned: (y, x), first in its
        # band's item.
        b = int(first[3]) - 1
        assert float(d["xs"][b][0][0][0]) == first[1]
        assert float(d["ys"][b][0][0][0]) == first[0]

    def test_no_note_when_cuts_differ(self, mode):
        """Cuts unlike dash's own rule draw silently, banded and keyed at
        the object's cuts."""
        cg = _obj("grid40")
        cg["cuts"] = [-1.0, 0.0, 1.0]
        spec = tp._spec([_plot("contour", {"contour_gen": cg,
                                           "levels": "7"})])
        [fig], msgs = _figs_msgs(mode, spec, _grid_df())
        assert not [m for m in msgs if "contour" in m], msgs
        [cr] = _crs(fig)
        assert [float(v) for v in cr.levels[1:-1]] == [-1.0, 0.0, 1.0]
        bars = [m for side in (fig.right, fig.left, fig.above, fig.below,
                               fig.center) for m in side
                if type(m).__name__ == "ContourColorBar"]
        assert [float(t) for t in bars[0].ticker.ticks] == [-1.0, 0.0, 1.0]

    def test_levels_out_of_order_go_to_their_bands(self, mode):
        """Runs of levels 2, 1, 3 (the generator's runs are never in level
        order, contour_gen_truth.json): each goes to its band's item, the
        items in band order with the bands' bounds and colours."""
        cg = {"cuts": [0.5, 1.5], "line": 0, "n": 1600,
              "x": [0, 1, 1, None, 2, 3, 3, None, 4, 5, 5],
              "y": [0, 0, 1, None, 0, 0, 1, None, 0, 0, 1],
              "z": [1, 1, 1, None, 0, 0, 0, None, 2, 2, 2],
              "levels": [2, 2, 2, None, 1, 1, 1, None, 3, 3, 3]}
        spec = tp._spec([_plot("contour", {"contour_gen": cg})])
        [fig] = _figs(mode, spec, _grid_df())
        [cr] = _crs(fig)
        d = cr.fill_renderer.data_source.data
        fl = list(cr.levels)
        assert [_band_of(float(v), fl) for v in d["lower_levels"]] == [0, 1, 2]
        assert [float(p[0][0][0]) for p in d["xs"]] == [2.0, 0.0, 4.0]
        assert len(d["fill_color"]) == 3

    def test_a_malformed_object_falls_back(self, mode):
        """One note, dash's own fit; also a filled object with no lines on
        an outlines layer."""
        for opts in ({"contour_gen": {"cuts": "x", "n": 1600}},
                     {"contour_gen": _obj("grid40"), "outlines": "outlines"}):
            spec = tp._spec([_plot("contour", opts)])
            [fig], msgs = _figs_msgs(mode, spec, _grid_df())
            notes = [m for m in msgs if "cannot be read" in m]
            assert len(notes) == 1, notes
            [cr] = _crs(fig)
            assert len(cr.fill_renderer.data_source.data["xs"]) == len(
                cr.levels) - 1
        assert dr._dash_contour_gen_of({}) is None

    def test_each_panel_takes_its_own_grid(self, mode):
        df = _grid_df()
        df["g"] = df["half"]
        a, b = _obj("grid40", n=800), _obj("grid40.line", n=800)
        b = dict(_obj("grid40", n=800), cuts=[0.0], x=[0, 1, 1, None],
                 y=[0, 0, 1, None], z=[0, 0, 0, None],
                 levels=[1, 1, 1, None])
        spec = tp._spec([_plot("contour", {"contour_gen": {"panels": [
            {"key": [0], "grid": a}, {"key": [1], "grid": b}]}})],
            graph_options={"by": "g"})
        figs = [f for f in _figs(mode, spec, df) if _crs(f)]
        assert len(figs) == 2
        n0 = sum(_items_per_band(_crs(figs[0])[0]))
        n1 = sum(_items_per_band(_crs(figs[1])[0]))
        assert (n0, n1) == (sum(_T["grid40"]["polys_per_band"]), 1)

    def test_the_total_panel_takes_total(self, mode):
        df = _grid_df()
        df["g"] = df["half"]
        t = dict(_obj("grid40", n=1600))
        one = dict(_obj("grid40", n=800), cuts=[0.0], x=[0, 1, 1, None],
                   y=[0, 0, 1, None], z=[0, 0, 0, None],
                   levels=[1, 1, 1, None])
        spec = tp._spec([_plot("contour", {"contour_gen": {"panels": [
            {"key": [0], "grid": one}, {"key": [1], "grid": one}],
            "total": t}})], graph_options={"by": "g, total"})
        figs = [f for f in _figs(mode, spec, df) if _crs(f)]
        assert len(figs) == 3
        ns = sorted(sum(_items_per_band(_crs(f)[0])) for f in figs)
        assert ns == [1, 1, sum(_T["grid40"]["polys_per_band"])]

    def test_a_panel_with_no_grid_is_fitted(self, mode):
        df = _grid_df()
        df["g"] = df["half"]
        one = dict(_obj("grid40", n=800), cuts=[0.0], x=[0, 1, 1, None],
                   y=[0, 0, 1, None], z=[0, 0, 0, None],
                   levels=[1, 1, 1, None])
        spec = tp._spec([_plot("contour", {"contour_gen": {"panels": [
            {"key": [0], "grid": one}]}})], graph_options={"by": "g"})
        figs, msgs = _figs_msgs(mode, spec, df)
        figs = [f for f in figs if _crs(f)]
        assert not [m for m in msgs if "cannot be read" in m]
        [c1] = _crs(figs[1])
        # dash's own fit: one item per band
        assert len(c1.fill_renderer.data_source.data["xs"]) == len(
            c1.levels) - 1
        assert not getattr(c1, "_dash_points_frozen", False)


class TestTheHandOver:

    def test_the_layer_is_handed_to_the_js_fit(self):
        spec = tp._spec([_plot("contour", {"contour_gen": _obj("grid40")})],
                        {"filter": "half, type(dropdown)"})
        r = jo._saved(spec, _grid_df())
        [fig] = jo._saved_figs(r)
        [cr] = _crs(fig)
        cfg = cr._dash_agg_config
        assert cfg["stata_n"] == 1600 and cfg["capped"] is False
        assert len(cfg["extra"]["fill_color"]) == len(cr.levels) - 1
        assert cr._dash_points_frozen is True
        assert cr._dash_points_stale is False
        [(tag, _rends)] = [e for g in r.frozen_layer_registry.values()
                           for e in g]
        assert tag["kind"] == "fit"

    def test_served_move_refits(self):
        """Served: a move keeping half the rows draws dash's own fit and
        the cue; a move back draws the object's polygons, no cue."""
        spec = tp._spec([_plot("contour", {"contour_gen": _obj("grid40")})],
                        {"filter": "half, type(dropdown)"})
        doc = jo._served(spec, _grid_df())
        [w] = [x for x in tp._widgets_of(doc) if type(x).__name__ == "Select"]
        first = w.value
        one = [v for v, lab in w.options if lab == "1"][0]
        tp._fire(w, one)
        [fig] = jo._served_figs(doc)
        [cr] = _crs(fig)
        fitted = len(cr.fill_renderer.data_source.data["xs"])
        assert fitted == len(cr.levels) - 1
        cues = [m for m in doc.models if type(m).__name__ == "Title"
                and m.text == dr._DASH_STALE_CUE_TEXT]
        assert [c.visible for c in cues] == [True]
        tp._fire(w, first)
        [fig] = jo._served_figs(doc)
        [cr] = _crs(fig)
        assert _items_per_band(cr) == _T["grid40"]["polys_per_band"]
        cues = [m for m in doc.models if type(m).__name__ == "Title"
                and m.text == dr._DASH_STALE_CUE_TEXT]
        assert cues and not any(c.visible for c in cues)


def _page(ptype, side=20, n=None, opts=None):
    df = _grid_df(side)
    key = "grid40" if ptype == "contour" else "grid40.line"
    cg = _obj(key, n=side * side if n is None else n)
    o = dict(opts or {})
    if o.get("outlines"):
        cg["lines"] = {k: _obj("grid40.line")[k]
                       for k in ("x", "y", "z", "levels")}
    o["contour_gen"] = cg
    spec = tp._spec([_plot(ptype, o)], {"filter": "half, type(dropdown)"})
    return spec, df


def _select(r):
    [w] = [x for x in r.filter_widgets if type(x).__name__ == "Select"]
    return w


def _arg_path(args, w):
    for k, v in args.items():
        if v is w:
            return k
        if isinstance(v, (list, tuple)):
            for i, x in enumerate(v):
                if x is w:
                    return "%s[%d]" % (k, i)
    raise AssertionError("the widget is not in the callback's args")


def _move_and_back(r, label):
    """Move the dropdown to *label*, then back to every row, in ONE run of
    the page's own script, as a browser keeps the page's state between
    two moves."""
    w = _select(r)
    first = w.value
    raw = [v for v, lab in w.options if lab == label][0]
    cb = r.filter_callbacks[r.filter_widgets.index(w)]
    path = _arg_path(cb.args, w)
    w.value = raw
    code = ("{\n" + cb.code + "\n}\n" + path + ".value = "
            + json.dumps(first) + ";\n{\n" + cb.code + "\n}\n")
    sf._run(code, cb.args)
    w.value = first


def _fill(r, part="fill", tag="dash_contour"):
    [fig] = jo._saved_figs(r)
    [cr] = _crs(fig, tag)
    return (cr.fill_renderer if part == "fill"
            else cr.line_renderer).data_source.data


def _cue_on(r):
    st = r.filter_callbacks[0].args.get("stale_status")
    return st is not None and st.visible is True


def _same_data(a, b):
    assert sorted(a) == sorted(b)
    for k in a:
        assert json.dumps(_plain(a[k])) == json.dumps(_plain(b[k])), k


def _plain(v):
    if isinstance(v, np.ndarray):
        return [_plain(x) for x in v.tolist()]
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
        return v
    v = float(v)
    return None if v != v else v


@requires_node
class TestTheSavedPage:

    @pytest.mark.parametrize("ptype", ["contour", "contourline"])
    def test_a_move_refits_and_marks(self, ptype):
        spec, df = _page(ptype)
        r, after = hm._saved_moved(spec, ("Select", "1"), df)
        kept = hm._kept(spec, "half == 1", "saved", df=df)
        part = "fill" if ptype == "contour" else "line"
        a, b = cj._layer_data(after, part), cj._layer_data(kept, part)
        if part == "fill":
            assert len(a["xs"]) == len(b["xs"])
            sub = df.query("half == 1")
            X, Y = cj._grid(sub["x"], sub["y"])
            agree = (cj._raster(a["xs"], a["ys"], X, Y)
                     == cj._raster(b["xs"], b["ys"], X, Y)).mean()
            assert agree >= 0.999, agree
        else:
            assert list(a["levels"]) == list(b["levels"])
        assert _cue_on(r)

    @pytest.mark.parametrize("part", ["bands", "outlines"])
    def test_a_move_back_draws_the_polygons(self, part):
        opts = {"outlines": "outlines"} if part == "outlines" else {}
        spec, df = _page("contour", opts=opts)
        r = jo._saved(spec, df, labels=True)
        built = {k: list(v) for k, v in _fill(r).items()}
        lines = ({k: list(v) for k, v in
                  _fill(r, "line", "dash_contour_lines").items()}
                 if part == "outlines" else None)
        bar = r.figures and [m for f in jo._saved_figs(r)
                             for side in (f.right, f.left, f.above, f.below,
                                          f.center) for m in side
                             if type(m).__name__ == "ContourColorBar"][0]
        lv, tk = list(bar.levels), list(bar.ticker.ticks)
        _move_and_back(r, "1")
        _same_data(_fill(r), built)
        if lines is not None:
            _same_data(_fill(r, "line", "dash_contour_lines"), lines)
        assert list(bar.levels) == lv and list(bar.ticker.ticks) == tk
        assert not _cue_on(r)

    def test_above_the_cap_the_polygons_stay_marked(self):
        spec, df = _page("contour", side=50, n=2500)
        r = jo._saved(spec, df, labels=True)
        built = {k: list(v) for k, v in _fill(r).items()}
        assert sum(len(i) for i in built["xs"]) == sum(
            _T["grid40"]["polys_per_band"])
        [(tag, _rends)] = [e for g in r.frozen_layer_registry.values()
                           for e in g]
        assert tag["kind"] == "fit"
        sf._move(r, ("Select", "1"))
        _same_data(_fill(r), built)
        assert _cue_on(r)


class TestTheChannel:

    def test_attach_puts_the_grid_in_options(self):
        g = _obj("grid40")
        spec = tp._spec([_plot("contour"), _plot("contourline"),
                         {"type": "scatter", "yvar": "y", "xvar": "x",
                          "options": {}}])
        spec["contour_grids"] = {"g1": {"1": g, "2": {"panels": [],
                                                      "total": g},
                                        "3": g, "9": g, "x": g}}
        out = dr._dash_attach_function_points(spec)
        assert "contour_grids" not in out
        plots = out["graphs"][0]["plots"]
        assert plots[0]["options"]["contour_gen"] is g
        assert plots[1]["options"]["contour_gen"]["total"] is g
        assert "contour_gen" not in plots[2]["options"]
        assert "contour_gen" not in spec["graphs"][0]["plots"][0]["options"]

    def test_the_spec_tail_writes_it(self):
        with open(os.path.join(_HERE, "..", "dash_parse.mata"),
                  encoding="utf-8") as fh:
            src = fh.read()
        at = src.index("void _dash_fn_spec_tail(")
        body = src[at:src.index("\n}\n", at)]
        for word in ("contour_grids", "panels", "grid", "total"):
            assert word in body, word
        assert "void _dash_cg_take(" in src and "void _dash_cg_reset(" in src
