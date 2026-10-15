"""
test_contour_layers.py -- twoway contour and contourline drawn (WP-31 B4b,
section 26).

The defect (measured at 0dd33ea): ``dash contour mpg weight length`` and
``dash contourline ...`` were refused by name, r(198), "a twoway plot
type dash does not draw", and no plot type reached S23's surface
(``_dash_contour_surface``).

twoway (StataNow 19.5, scripts/extract_contour_truth.do's ZD_ block,
fixture test/fixtures/contour_truth.json keys draw, line, abbrev, refuse,
scheme): three variables z y x; the cuts are ccuts() (sorted), else
levels(#)'s # - 1 equal steps over the z range (minmax adds both ends;
levels(0) and levels(1) give none), else the z axis's ticks -- zlabel(#5)
by default, the first and last dropped under a rule -- and zmax when none
is left; #cuts + 1 bands coloured by zyx2style's rules between scolor()
and ecolor() (the scheme's contour_begin/contour_end) or by ccolors(); a
colour key over the z axis ticked at its ticks; contourline's lines black
and thin unless colorlines or ccolors() colour them; a second contour (or
a second contourline) refused.

dash draws both with Bokeh's contour renderer over S23's surface
(GlyphMapper.map_contour / map_contourline), in both modes; the saved page
keeps the layer frozen and marked (grid unfiltered) until section 29.
"""
import json
import os
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
from conftest import render_models  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "contour_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
_ROWS = _T["cases"]["auto"]["rows"]
#: auto's 74 rows: z = mpg, y = weight, x = length.
_AUTO = pd.DataFrame({"mpg": _ROWS["z"], "weight": _ROWS["y"],
                      "length": _ROWS["x"]})
_ZMIN, _ZMAX = float(_AUTO["mpg"].min()), float(_AUTO["mpg"].max())


def _plot(ptype="contour", opts=None, z="mpg", y="weight", x="length"):
    return {"type": ptype, "zvar": z, "yvar": y, "xvar": x,
            "options": dict(opts or {})}


def _figs(mode, tmp_path, plots, go=None, df=None):
    spec = tp._spec(plots, {"formats": {}}, graph_options=go)
    return bg._figs(mode, tmp_path, spec, _AUTO if df is None else df)


def _contours(fig):
    return [r for r in fig.renderers if type(r).__name__ == "ContourRenderer"]


def _bars(fig):
    return [m for side in (fig.right, fig.left, fig.above, fig.below,
                           fig.center)
            for m in side if type(m).__name__ == "ContourColorBar"]


def _hex(c):
    c = str(c).lower()
    if c.startswith("#") and len(c) == 7:
        return c
    raise AssertionError(c)


def _close_rgb(a, b, tol=1):
    a, b = _hex(a), _hex(b)
    return all(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) <= tol
               for i in (1, 3, 5))


#: The fixture's draw probes: (options, graph options) dash is given.
_CUT_PROBES = {
    "default": ({}, {}),
    "ccuts": ({"ccuts": "15 20 25 30"}, {}),
    "ccuts_unsorted": ({"ccuts": "30 15 25 20"}, {}),
    "levels5": ({"levels": "5"}, {}),
    "levels5_minmax": ({"levels": "5", "minmax": "minmax"}, {}),
    "levels1": ({"levels": "1"}, {}),
    "levels2": ({"levels": "2"}, {}),
    "minmax_alone": ({"minmax": "minmax"}, {}),
    "zlabel5": ({}, {"zlabel": "#5"}),
    "zlabel_list": ({}, {"zlabel": "15(5)35"}),
    "zlabel_plain": ({}, {"zlabel": "15 20 25 30 35"}),
    "zlabel_minmax": ({}, {"zlabel": "minmax"}),
}

_COLOUR_PROBES = {
    "default": {},
    "crule_linear": {"crule": "linear", "scolor": "navy", "ecolor": "gold"},
    "crule_revlinear": {"crule": "revlinear", "scolor": "navy",
                        "ecolor": "gold"},
    "crule_intensity": {"crule": "intensity", "scolor": "navy",
                        "ecolor": "gold"},
    "crule_hue": {"crule": "hue", "scolor": "navy", "ecolor": "gold"},
    "crule_chue": {"crule": "chue", "scolor": "navy", "ecolor": "gold"},
    "crule_phue": {"crule": "phue", "scolor": "navy", "ecolor": "gold"},
    "crule_hue_default": {"crule": "hue"},
    "crule_linear_default": {"crule": "linear"},
    "crule_intensity_default": {"crule": "intensity"},
    "chue_default": {"crule": "chue"},
    "scolor_only": {"scolor": "green"},
    "ccolors": {"ccolors": "red blue green"},
    "ccuts": {"ccuts": "15 20 25 30"},
    "levels5_minmax": {"levels": "5", "minmax": "minmax"},
}


def _scheme(name="s2color"):
    return dr.SchemeParser(name) if name != "s2color" else dr.SchemeParser()


def _parse(t):
    return dr.OptionTranslator(scheme_of=lambda: dr.SchemeParser()) \
        .parse_color_alpha(t, "ccolors")[0]


class TestTheFixture:

    def test_meta_and_keys(self):
        assert _T["_meta"]["source"] == "scripts/extract_contour_truth.do"
        assert {"draw", "line", "abbrev", "refuse", "scheme", "cases",
                "grid"} <= set(_T)
        for k in list(_CUT_PROBES) + list(_COLOUR_PROBES):
            assert _T["draw"][k]["rc"] == 0, k
        r = _T["refuse"]
        assert (r["ccuts_levels"]["rc"], r["ccuts_levels"]["lines"]) == (
            198, ["option ccuts() cannot be combined with option levels()"])
        assert (r["two_contours"]["rc"], r["two_contours"]["lines"]) == (
            198, ["multiple contour, heatmap, or patch plots not allowed"])
        assert (r["two_lines"]["rc"], r["two_lines"]["lines"]) == (
            198, ["multiple contourline plots not allowed"])
        assert r["contour_and_line"]["rc"] == 0
        assert r["counts_2"]["lines"] == ["contour requires 3 variables: "
                                          "mpg weight"]
        assert r["weight"]["lines"] == ["weights not allowed"]


class TestContourDraws:

    @pytest.mark.parametrize("mode", _MODES)
    def test_renderer_levels_and_colours(self, mode, tmp_path):
        figs, _n = _figs(mode, tmp_path, [_plot()])
        [cr] = _contours(figs[0])
        d = _T["draw"]["default"]
        assert [float(v) for v in cr.levels[1:-1]] == pytest.approx(d["cuts"])
        # The key's ends: twoway's z axis, 10 to 41 on auto.
        [cb] = _bars(figs[0])
        assert float(cb.levels[0]) == pytest.approx(10.0)
        assert float(cb.levels[-1]) == pytest.approx(_ZMAX, abs=1e-6)
        assert [float(v) for v in cb.levels[1:-1]] == pytest.approx(
            d["cuts"])
        fills = list(cr.fill_renderer.data_source.data["fill_color"])
        lows = list(cr.fill_renderer.data_source.data["lower_levels"])
        want = dict(zip([float(v) for v in cr.levels[:-1]], d["rgb"]))
        assert fills and all(_close_rgb(f, want[float(lo)])
                             for f, lo in zip(fills, lows))
        # No outline: twoway's gm_linewidth .001.
        assert not cr.line_renderer.data_source.data.get("xs")


class TestContourlineDraws:

    @pytest.mark.parametrize("mode", _MODES)
    def test_lines_only(self, mode, tmp_path):
        figs, notes = _figs(mode, tmp_path, [_plot("contourline")])
        [cr] = _contours(figs[0])
        assert not cr.fill_renderer.data_source.data.get("xs")
        assert [float(v) for v in cr.levels] == pytest.approx(
            _T["line"]["default"]["cuts"])
        assert len(cr.line_renderer.data_source.data["xs"]) == 2
        assert not _bars(figs[0])
        assert any("contourline" in n and "not drawn" in n for n in notes)


class TestCuts:

    @pytest.mark.parametrize("probe", sorted(_CUT_PROBES))
    def test_each_rule(self, probe):
        opts, zopts = _CUT_PROBES[probe]
        d = _T["draw"][probe]
        cuts, ticks = dr._dash_contour_cuts(opts, _ZMIN, _ZMAX, zopts)
        assert cuts == pytest.approx(d["cuts"], rel=1e-9)
        assert ticks == pytest.approx(d["ticks"], rel=1e-9)


class TestColours:

    @pytest.mark.parametrize("probe", sorted(_COLOUR_PROBES))
    def test_each_rule(self, probe):
        d = _T["draw"][probe]
        got = dr._dash_contour_colours(_COLOUR_PROBES[probe], d["levels"],
                                       _scheme(), parse=_parse)
        assert len(got) == len(d["rgb"])
        assert all(_close_rgb(a, b) for a, b in zip(got, d["rgb"])), (
            got, d["rgb"])

    @pytest.mark.parametrize("scheme", ["s1mono", "economist"])
    def test_each_schemes_default(self, scheme):
        d = _T["scheme"][scheme]
        got = dr._dash_contour_colours({}, d["levels"], _scheme(scheme),
                                       parse=_parse)
        assert all(_close_rgb(a, b) for a, b in zip(got, d["rgb"])), (
            got, d["rgb"])


#: contourline's lines, read from twoway's exported SVG: (options, colour
#: per line, width name per line).
_LINE_PROBES = {
    "default": ({}, ["#000000"] * 2, ["thin"] * 2),
    "clwidths_vthick": ({"clwidths": "vthick vthick"}, ["#000000"] * 2,
                        ["thin"] * 2),
    "clpatterns_dash": ({"clpatterns": "dash dash"}, ["#000000"] * 2,
                        ["thin"] * 2),
    "ccolors": ({"ccolors": "red blue"}, ["#ff0000", "#0000ff"],
                ["medium"] * 2),
    "colorlines": ({"colorlines": "colorlines"}, ["#0000ff", "#00ff00"],
                   ["medium"] * 2),
    "colorlines_clwidths": ({"colorlines": "colorlines",
                             "clwidths": "vthick thin"},
                            ["#0000ff", "#00ff00"], ["vthick", "thin"]),
}
#: twoway's SVG stroke widths of the three width names (720 units an inch).
_SVG_WIDTH = {"thin": "5.76", "medium": "8.64", "vthick": "40.32"}


class TestLines:

    @pytest.mark.parametrize("probe", sorted(_LINE_PROBES))
    def test_each_probe(self, probe):
        opts, colours, widths = _LINE_PROBES[probe]
        strokes = _T["line"][probe]["plot_strokes"]
        for c, w in zip(colours, widths):
            assert "%s %s" % (c, _SVG_WIDTH[w]) in strokes, (probe, strokes)
        rgb = _T["line"][probe]["rgb"]
        if opts.get("ccolors"):
            rgb = dr._dash_contour_colours(opts, 3, _scheme(), parse=_parse)
        got = dr._dash_contour_line_style(opts, rgb, 2)
        assert got == (colours, widths)


class TestTheKey:

    @pytest.mark.parametrize("mode", _MODES)
    def test_placement(self, mode, tmp_path):
        figs, _n = _figs(mode, tmp_path, [_plot()])
        [cb] = _bars(figs[0])
        assert cb in figs[0].right
        assert list(cb.ticker.ticks) == pytest.approx(
            _T["draw"]["default"]["ticks"])
        assert cb.title == "mpg"
        figs, _n = _figs(mode, tmp_path, [_plot()],
                         go={"clegend": "off"})
        assert not _bars(figs[0])
        figs, _n = _figs(mode, tmp_path, [_plot()],
                         go={"clegend": "position(9)"})
        [cb] = _bars(figs[0])
        assert cb in figs[0].left

    def test_reversekey_changes_nothing(self):
        # Measured: twoway's contour key is the same with reversekey.
        assert _T["draw"]["reversekey"]["key_fills"] == \
            _T["draw"]["default"]["key_fills"]


def _poly_bounds(cr):
    xs = cr.fill_renderer.data_source.data["xs"]
    ys = cr.fill_renderer.data_source.data["ys"]
    allx = [v for p in xs for poly in p for ring in poly for v in ring]
    ally = [v for p in ys for poly in p for ring in poly for v in ring]
    return (min(allx), max(allx)), (min(ally), max(ally))


class TestHorizontal:

    @pytest.mark.parametrize("mode", _MODES)
    def test_swapped(self, mode, tmp_path):
        figs, _n = _figs(mode, tmp_path,
                         [_plot(opts={"horizontal": "horizontal"})])
        [cr] = _contours(figs[0])
        (x0, x1), (y0, y1) = _poly_bounds(cr)
        assert (x0, x1) == pytest.approx((_AUTO["weight"].min(),
                                          _AUTO["weight"].max()))
        assert (y0, y1) == pytest.approx((_AUTO["length"].min(),
                                          _AUTO["length"].max()))

    def test_registered(self):
        assert {"contour", "contourline"} <= set(dr._DASH_HORIZONTAL_TYPES)
        assert {"contour", "contourline"} <= set(dr._DASH_VERTICAL_TYPES)
        assert _T["draw"]["hz"]["xrange"] == [1760.0, 5000.0]


class TestInterp:

    @pytest.mark.parametrize("mode", _MODES)
    def test_each(self, mode, tmp_path):
        out = {}
        for w in ("thinplatespline", "shepard", "none", "bogus"):
            figs, _n = _figs(mode, tmp_path, [_plot(opts={"interp": w})])
            [cr] = _contours(figs[0])
            out[w] = cr._dash_contour_config["interp"] if hasattr(
                cr, "_dash_contour_config") else None
        assert out == {"thinplatespline": "thinplatespline",
                       "shepard": "shepard", "none": "none",
                       "bogus": "none"}


def _move_spec(ptype="contour"):
    return tp._spec([_plot(ptype, z="price", y="mpg", x="weight")],
                    {"filter": sf._MOVES[0][1]})


def _levels_drawn(figs):
    [cr] = _contours(figs[0])
    d = cr.fill_renderer.data_source.data
    return (sorted(set(float(v) for v in d["lower_levels"])),
            len(d["xs"]))


class TestMoves:

    def test_served_refits(self):
        _label, _f, action, oracle = sf._MOVES[0]
        after = hm._moved(_move_spec(), action, "served", df=tp._DF)
        kept = hm._kept(_move_spec(), oracle, "served", df=tp._DF)
        assert _levels_drawn(after) == _levels_drawn(kept)

    def test_saved_is_marked(self, tmp_path):
        sp, dp = bg._write(tmp_path, _move_spec(), tp._DF)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path), "o.html"))
            render_models(r)
        reg = r.frozen_layer_registry
        [(tag, rends)] = [e for g in reg.values() for e in g]
        assert tag["kind"] == "grid" and tag["type"] == "contour"
        assert tag["vars"] == ["price", "mpg", "weight"]
        assert any(type(x).__name__ == "GlyphRenderer"
                   and type(x.glyph).__name__ == "MultiPolygons"
                   for x in rends)
        assert dr._DASH_STALE_SUFFIX["grid"] == " (grid unfiltered)"


def _many(n=1001):
    rng = np.random.default_rng(7)
    return pd.DataFrame({"z": rng.normal(size=n), "y": rng.uniform(size=n),
                         "x": rng.uniform(size=n)})


class TestTheCap:

    @pytest.mark.parametrize("mode", _MODES)
    def test_note_and_frozen(self, mode, tmp_path):
        figs, notes = _figs(mode, tmp_path, [_plot(z="z", y="y", x="x")],
                            df=_many())
        [cr] = _contours(figs[0])
        assert cr._dash_contour_capped is True
        cap = [n for n in notes if "approximate surface" in n]
        assert len(cap) == 1 and "1001 distinct points" in cap[0] \
            and "100 x 100" in cap[0] and "subsample of 1000" in cap[0]


class TestBrushedCopies:

    def test_no_glyph_is_skipped(self):
        from bokeh.plotting import figure
        f = figure()
        f.contour(x=[0, 1], y=[0, 1], z=[[0, 1], [1, 2]], levels=[0.5],
                  line_color="black")
        dr.GlyphMapper._sync_brushed_copies(f, ())


def _even_odd(px, py, X, Y):
    """The points (X, Y) inside the ring (px, py), by the even-odd rule."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    inside = np.zeros(X.shape, bool)
    j = len(px) - 1
    for i in range(len(px)):
        xi, yi, xj, yj = px[i], py[i], px[j], py[j]
        cross = (yi > Y) != (yj > Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = (xj - xi) * (Y - yi) / (yj - yi) + xi
        inside ^= cross & (X < xc)
        j = i
    return inside


def _twoway_raster(rows, X, Y):
    """Each point's band in twoway's filled rows.  twoway paints pieces in
    order -- the top band over the whole region, then each lower band's
    region over it (measured: manual5's first piece is the whole square)
    -- a piece ending at a missing row or where the level changes."""
    lab = np.zeros(X.shape, int)
    px, py, lev = [], [], None
    for x, y, lv in list(zip(rows["x"], rows["y"], rows["lev"])) + [
            (None, None, None)]:
        if px and (x is None or int(lv) != lev):
            lab[_even_odd(px, py, X, Y)] = lev
            px, py = [], []
        if x is None:
            continue
        px.append(x)
        py.append(y)
        lev = int(lv)
    return lab


def _dash_raster(cr, X, Y):
    """Each point's band in dash's fill polygons (outer ring and holes)."""
    d = cr.fill_renderer.data_source.data
    levels = [float(v) for v in cr.levels]
    lab = np.zeros(X.shape, int)
    for xs, ys, lo in zip(d["xs"], d["ys"], d["lower_levels"]):
        k = levels.index(float(lo)) + 1
        for pxs, pys in zip(xs, ys):
            m = np.zeros(X.shape, bool)
            for rx, ry in zip(pxs, pys):
                m ^= _even_odd(rx, ry, X, Y)
            lab[m] = k
    return lab


class TestAgainstTheFixture:

    @pytest.mark.parametrize("interp", ["thinplatespline", "shepard"])
    @pytest.mark.parametrize("case", ["auto", "synthetic"])
    def test_level_sets(self, case, interp, tmp_path):
        """A 200 x 200 raster of the grid's hull: each cell's band in
        twoway's filled polygons and in dash's agrees on 98% of cells or
        more (the polygons are cut by different algorithms; the level
        sets are the same).  auto's thin-plate spline, whose system's
        condition is 2.5e17 (S23), agrees on 97.6% (measured 15oct2026:
        the grid's nodes match twoway's to 1e-7, and a bilinear, either
        triangulated or dash's cut of the cells all agree with twoway's
        polygons on 97.2-97.5%), so it is held to 97%."""
        c = _T["cases"][case]
        rows = c["rows"]
        df = pd.DataFrame({"z": rows["z"], "y": rows["y"], "x": rows["x"]})
        cuts = " ".join(repr(float(v)) for v in c[interp]["cuts"])
        figs, _n = _figs("saved", tmp_path,
                         [_plot(z="z", y="y", x="x",
                                opts={"ccuts": cuts, "interp": interp})],
                         df=df)
        [cr] = _contours(figs[0])
        g = _T["grid"][case]
        xs = np.linspace(min(g["x"]), max(g["x"]), 201)
        ys = np.linspace(min(g["y"]), max(g["y"]), 201)
        X, Y = np.meshgrid((xs[:-1] + xs[1:]) / 2, (ys[:-1] + ys[1:]) / 2)
        a = _twoway_raster(c[interp]["filled"], X, Y)
        b = _dash_raster(cr, X, Y)
        floor = 0.97 if (case, interp) == ("auto", "thinplatespline") \
            else 0.98
        assert (a == b).mean() >= floor, (a == b).mean()


class TestDuplicateZ:

    def test_smallest_z_is_kept(self):
        # S23's measured rule, documented by S26 (DECISIONS D20): dash
        # keeps the smallest z at a repeated (x, y) under every interp();
        # twoway does so under interp(none) and picks by sort seed under
        # the other two (dupseed).
        rows = _T["cases"]["manual5"]["rows"]
        for w in ("thinplatespline", "shepard", "none"):
            s = dr._dash_contour_surface(rows["x"], rows["y"], rows["z"], w)
            assert s["gz"][1, 1] == 4.0, w
        assert set(_T["dupseed"]["none"]["order1"]) == {4.0}
        assert set(_T["dupseed"]["thinplatespline"]["order1"]) <= {4.0, 5.0}


class TestTheReaders:

    def test_each(self):
        p = _plot()
        assert dr._dash_hover_layer_vars(p) == ["length", "weight", "mpg"]
        assert dr._dash_layer_axis_names(p, "xvar")[1] == ["length"]
        assert dr._dash_layer_axis_names(p, "yvar")[1] == ["weight"]
        hz = _plot(opts={"horizontal": "horizontal"})
        assert dr._dash_layer_axis_names(hz, "xvar")[1] == ["weight"]
        keys = dr._dash_legend_keys([(p, ["r"]), (_plot("scatter"), ["s"])])
        assert keys == [(2, keys[0][1], ["s"])]
        assert "zvar" in dr._DASH_PLOT_VAR_KEYS
        assert dr._dash_stale_kind("contour", {}) == "grid"
        # Drawn from the layer's rows, which the page embeds: no
        # computed-only type (the embedded-cells count and hover read it).
        assert not dr._DASH_CONTOUR_TYPES & dr._DASH_COMPUTED_ONLY_TYPES


class TestServedCarries:

    def test_names(self, tmp_path):
        sp, dp = bg._write(tmp_path, tp._spec([_plot()]), _AUTO)
        app = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        for name in ("_dash_contour_zticks", "_dash_contour_cuts",
                     "_dash_contour_colours", "_dash_contour_line_style",
                     "_dash_contour_fill_levels",
                     "_dash_is_horizontal_opts"):
            assert "def %s(" % name in src, name
        for name in ("_DASH_CONTOUR_TYPES", "_DASH_CONTOUR_CAP_NOTE"):
            assert "\n%s = " % name in src, name
