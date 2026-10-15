"""WP-31 D7: the axis-scale look is drawn as twoway draws it (section 33).

dash named outergap(), noextend, extend, fextend, fill and lstyle() of
xscale()/yscale() in a note, read two yscale(alt) copies as one, drew the
axis title Bokeh's 5 px from its labels where the scheme says gsize
axis_title_gap, and named zlabel()/zscale() look words on a graph with no
colour key.  twoway's answers are in test/fixtures/axis_look_truth.json
(scripts/extract_axis_look_truth.do; SVG units are 10 per point):

* outergap(5) widens the border on the axis's side by 124 units: the size
  (14.4 pt) less twoway's 2 pt default (sc_outergap_5, sc_xoutergap_5).
* noextend draws the axis line from the first tick to the last
  (sc_noextend); extend, fextend and fill draw the plain graph.
* lstyle(grid) draws the line in the grid's colour and width
  (sc_lstyle_grid).
* yscale(alt) yscale(alt) draws the plain graph: each copy toggles the side
  (sc_alt2); yscale(alt alt) in one copy is r(198) "option alt not
  allowed" (sc_alt2one).
* zlabel(, labsize(small)) and zscale(alt) on a scatter print nothing
  (z_zlabel, z_zscale).

While iterating: ``python3 -m pytest test/test_axis_scale_look.py -q``.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_axis_look_options as tal  # noqa: E402
import test_default_axes as tda  # noqa: E402

_MODES = ("saved", "served")
_T = tal._T
T = dr.OptionTranslator
_figs = tal._figs


def _pr(key):
    return _T[key]["plotregion"]


def _noted(msgs):
    return [m for m in msgs if "not implemented" in m]


class TestTheFixture:
    def test_keys(self):
        for k in ("sc_outergap_5", "sc_xoutergap_5", "sc_noextend",
                  "sc_extend", "sc_fextend", "sc_fill", "sc_lstyle_grid",
                  "sc_alt1", "sc_alt2", "sc_alt2one", "z_zlabel",
                  "z_zscale"):
            assert k in _T, k
        assert _T["sc_alt2one"]["rc"] == 198
        assert _T["sc_alt2one"]["log"] == ["option alt not allowed"]


class TestOutergap:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("letter", ["x", "y"])
    def test_each(self, mode, letter):
        if letter == "y":
            moved = _pr("sc_outergap_5")["left"] - _pr("plain")["left"]
            prop = "min_border_left"
        else:
            moved = _pr("plain")["bottom"] - _pr("sc_xoutergap_5")["bottom"]
            prop = "min_border_bottom"
        assert moved == pytest.approx(124.0, abs=0.1)
        f0, _m = _figs(mode, {})
        f1, msgs = _figs(mode, {letter + "scale": "outergap(5)"})
        base = getattr(f0, prop)
        base = f0.min_border if base is None else base
        assert getattr(f1, prop) - base == round(moved / 10 * T.PX_PER_PT)
        assert not _noted(msgs), msgs

    def test_not_under_by(self):
        fig = tal.tb  # noqa: F841  (the by() figures are built below)
        from bokeh.plotting import figure
        f = figure()
        ax = f.yaxis[0]
        b = f.min_border_left
        dr._dash_apply_scale_look(f, ax, dr._dash_scale_look("outergap(5)"),
                                  "yscale", by_graph=True)
        assert f.min_border_left == b


class TestExtend:
    @pytest.mark.parametrize("mode", _MODES)
    def test_noextend(self, mode):
        a = _T["sc_noextend"]["vlines"][0]
        tick_ys = sorted(h["y1"] for h in _T["plain"]["hlines"]
                         if h["stroke"] == "#000000"
                         and abs(h["x2"] - h["x1"]) < 100)
        assert (min(a["y1"], a["y2"]), max(a["y1"], a["y2"])) == \
            (tick_ys[0], tick_ys[-1])
        f, msgs = _figs(mode, {"yscale": "noextend"})
        ax = tal._axis(f, "y")
        ticks = [float(t) for t in tda._ticks(f, "y")]
        assert tuple(ax.bounds) == (min(ticks), max(ticks)) == (10.0, 40.0)
        assert not _noted(msgs), msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_extend_words(self, mode):
        for key in ("sc_extend", "sc_fextend", "sc_fill"):
            assert _T[key]["vlines"] == _T["plain"]["vlines"], key
        for w in ("extend", "fextend", "noextend extend", "fill",
                  "nofill"):
            f, msgs = _figs(mode, {"yscale": w})
            assert tal._axis(f, "y").bounds == "auto", w
            assert not _noted(msgs), (w, msgs)

    def test_noextend_on_a_log_axis(self):
        f, _m = _figs("saved", {"xscale": "log noextend"})
        ax = tal._axis(f, "x")
        ticks = [float(t) for t in tda._ticks(f, "x")]
        assert tuple(ax.bounds) == (min(ticks), max(ticks))

    def test_js_equals_python(self):
        src = (dr._DASH_AXIS_FINISH_JS + """
const ax = {bounds: "auto"}, tk = {ticks: [10, 20, 30, 40, 55]};
const models = [ax, tk];
dash_axis_bounds({noext: 0, noext_ticks: 1}, models, 8, 42);
const ax2 = {bounds: [1, 2]};
dash_axis_bounds({noext: 0, noext_ticks: 1}, [ax2, {ticks: []}], 8, 42);
console.log(JSON.stringify([ax.bounds, ax2.bounds]));
""")
        assert js_runner.run_js(src) == [[10, 40], "auto"]


class TestLstyle:
    @pytest.mark.parametrize("mode", _MODES)
    def test_grid(self, mode):
        a = _T["sc_lstyle_grid"]["vlines"][0]
        assert (a["stroke"], a["width"]) == ("#eaf2f3", 8.64)
        f, msgs = _figs(mode, {"yscale": "lstyle(grid)"})
        ax = tal._axis(f, "y")
        assert ax.axis_line_color == "#eaf2f3"
        assert ax.axis_line_width == pytest.approx(8.64 / 10 * T.PX_PER_PT)
        assert not _noted(msgs), msgs

    @pytest.mark.parametrize("mode", _MODES)
    def test_lcolor_wins(self, mode):
        f, _m = _figs(mode, {"yscale": "lstyle(grid) lcolor(red)"})
        assert tal._axis(f, "y").axis_line_color == "#ff0000"


class TestAltParity:
    def test_one(self):
        assert _T["sc_alt1"]["texts"][0]["x"] > _pr("sc_alt1")["right"]
        assert dr._dash_scale_look("alt")["alternate"] is True

    def test_two(self):
        # Two copies draw the plain graph; dash.ado's merge drops the pair
        # (Mata _dash_rep_alt; test_wp31_truth.cscript U33-06).
        strip = ("texts", "vlines", "hlines")
        assert all(_T["sc_alt2"][k] == _T["plain"][k] for k in strip)


class TestTitleGap:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("scheme", ["s2color", "s1mono"])
    def test_default(self, mode, scheme):
        s = dr.SchemeParser(scheme)
        assert s.axis_title_gap_px == pytest.approx(1.0 * T.PX_PER_PT,
                                                    abs=0.01)
        spec = tda._spec(tal._SC, {}, scheme=scheme, formats=tal._FORMATS)
        f = tda._figs(mode, spec)[0]
        for letter in ("x", "y"):
            assert tal._axis(f, letter).axis_label_standoff == round(
                s.axis_title_gap_px)

    def test_the_scheme_files_carry_it(self):
        with open(os.path.join(_HERE, "..", "dash-s2color.scheme"),
                  encoding="utf-8") as fh:
            assert any(ln.split()[:2] == ["gsize", "axis_title_gap"]
                       for ln in fh)


class TestZLook:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt,val", [("zlabel", ", labsize(small)"),
                                         ("zscale", "alt")])
    def test_each(self, mode, opt, val):
        assert _T["z_" + opt]["rc"] == 0 and _T["z_" + opt]["log"] == []
        _f, msgs = _figs(mode, {opt: val})
        assert not [m for m in msgs if opt in m], msgs


class TestSilentWhenHonoured:
    def test_the_set(self):
        assert {"outergap", "noextend", "extend", "nofextend", "fextend",
                "lstyle", "fillspace", "nofillspace"} <= \
            dr._DASH_SCALE_LOOK_SUBOPTS
