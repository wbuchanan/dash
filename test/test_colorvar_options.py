"""WP-31 section 17 (GAPS3 C8b): twoway's colorvar options, colorvar(i.var),
and the graph options clegend(), plegend() and pcycle().

What twoway draws is measured, not modelled, by
scripts/extract_colorvar_options_truth.do into
test/fixtures/colorvar_options_truth.json (StataNow 19.5):

* ``probes[D*]``: ``twoway scatter mpg weight, colorvar(...) <options>``
  -- the key's swatch fills in document order (the colour key draws the
  highest level first), their opacities, the swatch kind (a marker, or a
  bar under colorkeysrange), the key's texts and the plotted markers'
  outline colours.  twoway colours k levels from k + 1 steps of the rule
  under colordiscrete (D01, D01f: 2 levels are hue 240 and 120), and k
  bins from k steps (D02a-c); hue and chue interpolate the hue at full
  saturation and value (chue always upward round the wheel), linear and
  revlinear the RGB, intensity scales colorend() by step/steps; phue is
  the scheme's p1, p2, ...; a *# intensity and a %# opacity apply to every
  level.  colorlist() shorter than the levels repeats its last colour
  (D03).
* ``schemes[<s>]``: each scheme dash ships -- the rule's two ends
  (colorlevels(2)) and the five discrete levels; the mono schemes and
  economist use the intensity rule.
* ``probes[R*]``, ``probes[P*]``: refusals, rc and text.

Every test that draws runs in both modes: the saved page (DashRenderer)
and the served app (ServerAppBuilder); both run the same GlyphMapper.
"""
from __future__ import annotations

import itertools
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColorBar, Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from test_server_layer_defects import (_figures_of, make_spec,  # noqa: E402
                                       plot_for)

_FIX = os.path.join(_HERE, "fixtures", "colorvar_options_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
PROBES = TRUTH["probes"]
MODES = ["saved", "served"]

_DF = pd.DataFrame({
    "mpg":     [30.0, 28.0, 25.0, 23.0, 22.0, 21.0, 19.0, 17.0, 16.0, 14.0],
    "trunk":   [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
    "turn":    [31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0],
    "weight":  [1800.0, 2010.0, 2200.0, 2650.0, 2930.0, 3000.0, 3100.0,
                3350.0, 3600.0, 4080.0],
    "price":   [4816.0, 10372.0, 3799.0, 11385.0, 4099.0, 5788.0, 4453.0,
                4749.0, 4082.0, 5189.0],
    "foreign": [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
    "rep78":   [4.0, 5.0, 3.0, 2.0, 1.0, 3.0, 4.0, 5.0, 2.0, 3.0],
})

_SEQ = itertools.count()
_CACHE: dict = {}


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return tmp_path_factory.mktemp("cvo")


def _figs(tmp, mode, plots, go=None):
    """The figures of a one-graph spec of *plots*, in *mode*, and the
    warnings the build gave."""
    key = (mode, json.dumps([plots, go], sort_keys=True))
    if key in _CACHE:
        return _CACHE[key]
    spec = make_spec(plots, graph_options=go)
    tag = next(_SEQ)
    sp = tmp / f"cvo_spec_{tag}.json"
    dp = tmp / f"cvo_data_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            figs = list(r.figures.values())
        else:
            ap = tmp / f"cvo_app_{tag}.py"
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
            mod = load_app(str(ap), f"_cvo_{tag}", draw=False)
            doc = Document()
            mod.make_document(doc)
            figs = _figures_of(doc)
    _CACHE[key] = (figs, [str(w.message) for w in caught])
    return _CACHE[key]


def _fig(tmp, mode, opts, go=None, ptype="scatter"):
    (figs, _w) = _figs(tmp, mode, [plot_for(ptype, opts)], go)
    [f] = figs
    return f


def _keys(fig, kind=None):
    out = []
    for side in (fig.right, fig.left, fig.above, fig.below, fig.center):
        for m in side:
            if isinstance(m, ColorBar) or (
                    isinstance(m, Legend)
                    and m.name == dr._COLORVAR_LEGEND_NAME):
                if kind is None or isinstance(m, kind):
                    out.append(m)
    return out


def _side_of(fig, model):
    for side in ("right", "left", "above", "below", "center"):
        if model in list(getattr(fig, side)):
            return side
    return None


def _main(fig):
    """The layer's own glyph renderer (never a key swatch)."""
    rs = [r for r in fig.renderers
          if not str(getattr(r, "name", "") or "").startswith(
              dr._DASH_SWATCH_PREFIX)
          and getattr(r, "glyph", None) is not None]
    return rs[0]


def _mapper(fig):
    return _main(fig).glyph.fill_color.transform


def _items(fig):
    [leg] = _keys(fig, Legend)
    return [(str(getattr(it.label, "value", it.label)), it.renderers[0])
            for it in leg.items]


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _close(got, want):
    """Colour lists equal to within 1/255 a channel (D-17a)."""
    return len(got) == len(want) and all(
        abs(a - b) <= 1 for g, w in zip(got, want)
        for a, b in zip(_rgb(g), _rgb(w)))


def _ascending(probe):
    """The probe's level colours, lowest level first: the colour key
    draws the highest first."""
    return list(reversed(PROBES[probe]["key"]["fills"]))


_HEX = {"blue": "#0000ff", "red": "#ff0000", "navy": "#1a476f",
        "white": "#ffffff", "green": "#008000", "gs8": "#808080"}
_S2P = dr.SchemeParser("s2color").p_colors
#: probe: (rule, start, end, steps, intensity) -- the rule as the probe's
#: command gives it, the steps twoway divides it into.
_PALETTES = {
    "D01": ("hue", "blue", "red", 6, None),
    "D01f": ("hue", "blue", "red", 3, None),
    "D02a": ("hue", "blue", "red", 3, None),
    "D02b": ("hue", "blue", "red", 8, None),
    "D02c": ("hue", "blue", "red", 4, None),
    "D04": ("linear", "white", "navy", 6, None),
    "D04b": ("linear", "blue", "navy", 6, None),
    "D04c": ("linear", "red", "blue", 4, None),
    "D04d": ("revlinear", "white", "navy", 6, None),
    "D06": ("intensity", "blue", "navy", 6, None),
    "D06b": ("intensity", "blue", "red", 4, None),
    "D07": ("phue", "blue", "red", 6, None),
    "D07b": ("phue", "blue", "red", 6, 0.5),
    "D08": ("chue", "blue", "red", 6, None),
    "D08b": ("chue", "red", "blue", 6, None),
    "D08c": ("chue", "blue", "blue", 6, None),
    "D08d": ("hue", "green", "blue", 6, None),
    "D08e": ("hue", "gs8", "navy", 6, None),
    "D08f": ("hue", "blue", "blue", 6, None),
    "D09": ("hue", "blue", "red", 6, 1.5),
    "D09b": ("hue", "blue", "red", 6, 0.5),
    "D09c": ("linear", "white", "navy", 6, None),
}


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta(self):
        m = TRUTH["_meta"]
        assert sorted(m) == ["born_date", "dash_commit", "extracted",
                             "source", "stata_version"]
        assert m["source"] == "scripts/extract_colorvar_options_truth.do"

    def test_every_dash_scheme_is_measured(self):
        assert sorted(TRUTH["schemes"]) == sorted(
            dr.SchemeParser._BUILTIN_NAMES)


# ---------------------------------------------------------------------------
# The helpers
# ---------------------------------------------------------------------------

class TestColorruleParse:

    def test_forms(self):
        p = dr._dash_colorrule_parse
        assert p("") == (None, None, None)
        assert p("hue") == ("hue", None, None)
        assert p("linear %40 *2") == ("linear", 40.0, 2.0)
        assert p("hue *0.5") == ("hue", None, 0.5)
        assert p("*1.5 %50") == (None, 50.0, 1.5)
        # twoway ignores an intensity it cannot read (R02c rc 0) ...
        assert PROBES["R02c"]["rc"] == 0
        assert p("hue %50 *x") == ("hue", None, None)
        # ... and refuses an opacity it cannot read beside one it can.
        with pytest.raises(ValueError, match="invalid colorrule"):
            p("hue *2 %x")


class TestColorrulePalette:

    @pytest.mark.parametrize("probe", sorted(_PALETTES))
    def test_matches_twoway(self, probe):
        rule, s, e, n, it = _PALETTES[probe]
        want = _ascending(probe)
        got = dr._dash_colorrule_palette(rule, _HEX[s], _HEX[e], n,
                                         intensity=it, scheme_p=_S2P)
        assert _close(got[:len(want)], want), (got, want)

    @pytest.mark.parametrize("scheme", sorted(TRUTH["schemes"]))
    def test_each_schemes_default(self, scheme):
        rule, s, e = dr._dash_colorrule_default(dr.SchemeParser(scheme))
        p = dr.SchemeParser(scheme).p_colors
        two = list(reversed(TRUTH["schemes"][scheme]["S2"]["key"]["fills"]))
        five = list(reversed(TRUTH["schemes"][scheme]["S5"]["key"]["fills"]))
        assert _close(dr._dash_colorrule_palette(rule, s, e, 2,
                                                 scheme_p=p), two)
        assert _close(dr._dash_colorrule_palette(rule, s, e, 6,
                                                 scheme_p=p)[:5], five)


# ---------------------------------------------------------------------------
# The level colours drawn
# ---------------------------------------------------------------------------

_CV = {"colorvar": "rep78", "colordiscrete": "colordiscrete"}


class TestDefault:

    @pytest.mark.parametrize("mode", MODES)
    def test_discrete_levels_in_twoways_hue(self, tmp, mode):
        m = _mapper(_fig(tmp, mode, _CV))
        assert _close(list(m.palette), _ascending("D01")), m.palette

    @pytest.mark.parametrize("mode", MODES)
    def test_bins_in_twoways_hue(self, tmp, mode):
        m = _mapper(_fig(tmp, mode, {"colorvar": "rep78",
                                     "colorlevels": "3"}))
        assert _close(list(m.palette), _ascending("D02a")), m.palette

    @pytest.mark.parametrize("mode", MODES)
    def test_rule_start_end(self, tmp, mode):
        m = _mapper(_fig(tmp, mode, dict(
            _CV, colorrule="linear", colorstart="white", colorend="navy")))
        assert _close(list(m.palette), _ascending("D04")), m.palette

    @pytest.mark.parametrize("mode", MODES)
    def test_opacity_and_intensity(self, tmp, mode):
        f = _fig(tmp, mode, dict(_CV, colorrule="hue %50 *1.5"))
        assert _close(list(_mapper(f).palette), _ascending("D09"))
        assert PROBES["D09"]["key"]["opacities"] == [0.5] * 5
        assert _main(f).glyph.fill_alpha == 0.5

    @pytest.mark.parametrize("mode", MODES)
    def test_a_colour_bar_takes_the_rule(self, tmp, mode):
        f = _fig(tmp, mode, {"colorvar": "price"})
        [cb] = _keys(f, ColorBar)
        pal = list(cb.color_mapper.palette)
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8); one step of the rule a level, n cuts
        # n + 1 levels, from the rule's start to its end.
        cuts = [t for t in cb.ticker.ticks if t >= min(_DF["price"])]
        assert len(pal) == len(cuts) + 1
        assert _close([pal[0], pal[-1]], ["#0000ff", "#ff0000"]), pal[:2]


class TestColorlist:

    @pytest.mark.parametrize("mode", MODES)
    def test_in_order(self, tmp, mode):
        m = _mapper(_fig(tmp, mode, dict(
            _CV, colorlist="red blue green orange navy")))
        assert _close(list(m.palette), _ascending("D03b")), m.palette

    @pytest.mark.parametrize("mode", MODES)
    def test_short_list(self, tmp, mode):
        m = _mapper(_fig(tmp, mode, dict(_CV, colorlist="red blue")))
        assert _close(list(m.palette), _ascending("D03")), m.palette


class TestFillonly:

    @pytest.mark.parametrize("mode", MODES)
    def test_outline_kept(self, tmp, mode):
        g = _main(_fig(tmp, mode, dict(_CV, colorfillonly="colorfillonly"))
                  ).glyph
        assert getattr(g.fill_color, "transform", None) is not None
        assert PROBES["D10"]["outline_strokes"] == ["#1a476f"]
        assert str(g.line_color).lower() == "#1a476f"


class TestKeys:

    @pytest.mark.parametrize("mode", MODES)
    def test_range(self, tmp, mode):
        f = _fig(tmp, mode, {"colorvar": "rep78", "colorlevels": "4",
                             "colorkeysrange": "colorkeysrange"})
        assert PROBES["D11"]["key"]["swatch"] == "bar"
        assert PROBES["D11"]["key"]["texts"] == \
            PROBES["D11b"]["key"]["texts"]
        kinds = {type(r.glyph).__name__ for _l, r in _items(f)}
        assert kinds == {"Quad"}, kinds
        plain = _fig(tmp, mode, {"colorvar": "rep78", "colorlevels": "4"})
        assert [lab for lab, _r in _items(f)] == \
            [lab for lab, _r in _items(plain)]

    @pytest.mark.parametrize("mode", MODES)
    def test_reverse(self, tmp, mode):
        plain = [lab for lab, _r in _items(_fig(tmp, mode, _CV))]
        rev = [lab for lab, _r in _items(_fig(tmp, mode, dict(
            _CV, colorkeysreverse="colorkeysreverse")))]
        assert rev == list(reversed(plain)), (plain, rev)
        assert _ascending("D12") == list(reversed(_ascending("D01")))

    def test_reverse_on_colorbar_named(self, tmp):
        # Flipped (WP-31 C8e): "named on a colour bar" was wrong because
        # twoway draws a key that is not discrete the same with
        # colorkeysreverse as without it (D14r == D14), and so does dash,
        # in silence (test_colorkeysreverse_bar.py).
        (_f, w) = _figs(tmp, "saved", [plot_for("scatter", {
            "colorvar": "price", "colorkeysreverse": "colorkeysreverse"})])
        assert not any("colorkeysreverse" in x for x in w), w
        assert PROBES["D14r"]["key"] == PROBES["D14"]["key"]


class TestOtherlabel:

    @pytest.mark.parametrize("mode", MODES)
    def test_label(self, tmp, mode):
        f = _fig(tmp, mode, dict(_CV, colorcuts="3 4",
                                 colorotherlabel="rest"))
        labs = [lab for lab, _r in _items(f)]
        assert labs[-1] == "rest", labs
        assert PROBES["D05p"]["key"]["texts"][-1] == "rest"


# ---------------------------------------------------------------------------
# clegend(), plegend(), pcycle()
# ---------------------------------------------------------------------------

class TestClegend:

    @pytest.mark.parametrize("mode", MODES)
    def test_position_width(self, tmp, mode):
        f = _fig(tmp, mode, {"colorvar": "price"},
                 go={"clegend": 'position(6) width(5) title("Z")'})
        [cb] = _keys(f, ColorBar)
        assert _side_of(f, cb) == "below"
        assert cb.title == "Z"
        # twoway keeps the key upright below the plot (G01: its swatches
        # stacked at one x), width() its thickness.
        xs = {round(x) for x, _y in PROBES["G01"]["key"]["text_pos"][:5]}
        assert len(xs) == 1, xs
        assert cb.width == round(5 * 2.88 * 96 / 72)

    @pytest.mark.parametrize("mode", MODES)
    def test_off(self, tmp, mode):
        assert PROBES["G03"]["key"]["fills"] == []
        f = _fig(tmp, mode, {"colorvar": "price"}, go={"clegend": "off"})
        assert _keys(f) == []


class TestPlegend:

    @pytest.mark.parametrize("mode", MODES)
    def test_off(self, tmp, mode):
        assert PROBES["G02"]["key"]["fills"] == []
        f = _fig(tmp, mode, dict(_CV, coloruseplegend="coloruseplegend"),
                 go={"plegend": "off"})
        assert _keys(f) == []


class TestPcycle:

    @pytest.mark.parametrize("mode", MODES)
    def test_recycles(self, tmp, mode):
        s = PROBES["P01"]["series_fills"]
        assert sorted(s.values()) == [75, 149]     # series 3 is p1
        plots = [dict(plot_for("scatter"), yvar=y)
                 for y in ("mpg", "trunk", "turn")]
        (figs, _w) = _figs(tmp, mode, plots, go={"pcycle": "2"})
        [f] = figs
        cols = [str(r.glyph.fill_color).lower() for r in f.renderers
                if type(r.glyph).__name__ == "Scatter"]
        assert cols[:3] == ["#1a476f", "#90353b", "#1a476f"], cols

    def test_helper(self):
        assert dr._dash_pcycle({"pcycle": "2"}) == 2
        assert dr._dash_pcycle({}) is None
        assert dr._dash_pcycle({"pcycle": "40"}) == 15
        assert dr._dash_plot_style_indices(
            [{"type": "scatter"}] * 3, 2) == [0, 1, 0]


class TestClegendOpts:

    def test_forms(self):
        o = dr._dash_clegend_opts('pos(6) ring(1) width(5) height(20) '
                                  'title("Z") altaxis')
        assert o["position"] == 6 and o["ring"] == 1
        assert o["width"] == "5" and o["height"] == "20"
        assert o["title"] == "Z" and o["off"] is False
        assert o["other"] == ["altaxis"]
        assert dr._dash_clegend_opts("off")["off"] is True


class TestTheServedCopy:

    def test_names(self):
        src = open(os.path.join(_HERE, "..", "dash_render.py"),
                   encoding="utf-8").read()
        for name in ("_dash_colorrule_parse", "_dash_colorrule_palette",
                     "_dash_colorrule_default", "_dash_clegend_opts",
                     "_dash_pcycle"):
            assert f'"{name}"' in src, name


# ---------------------------------------------------------------------------
# dash.ado
# ---------------------------------------------------------------------------

def _ado():
    with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


class TestTheAdoText:

    def test_declared(self):
        txt = _ado()
        # As twoway_yxview_parse.class:185-201 declares them.
        for decl in ("COLORSTart(string)", "COLOREnd(string)",
                     "COLORRule(string)", "COLORFILLONLY",
                     "COLORFORMISSing(string)", "COLORKEYSRANge",
                     "COLORKEYSREVerse", "COLORALLOWMULTIPLE",
                     "COLOROTHERLABel(string)",
                     "CLEGend(string asis)", "PLEGend(string asis)",
                     "PCYCle(string)"):
            assert decl in txt, decl
        # Both parsers declare the three graph options.
        assert txt.count("CLEGend(string asis)") == 2
        assert "local colormissing : copy local colorformissing" in txt
        assert "_dash_pending' colorlist" not in txt
        assert "_dash_pending' coloruseplegend" not in txt

    def test_refusals_in_twoways_words(self):
        txt = _ado()
        assert PROBES["R01"]["lines"] == [
            "you must specify option colordiscrete with option "
            "coloruseplegend"]
        assert PROBES["R03"]["lines"] == [
            "multiple contour, patch, or colorvar plots not allowed"]
        for p in ("R01", "R03"):
            assert PROBES[p]["lines"][0] in txt, p
        assert "invalid colorrule specification" in txt
        assert "option seriesid() not allowed" in txt

    def test_ivar(self):
        txt = _ado()
        assert 'anyof(("i.", "I."), substr(strtrim(st_local("colorvar")), '\
            '1, 2))' in txt
        assert PROBES["D13"]["rc"] == 0
        assert PROBES["D13"]["key"]["texts"][-1] == "Other"

    def test_companions_dropped_on_silent_types(self):
        txt = _ado()
        body = txt[txt.index("program define _dash_cv_drop"):]
        body = body[:body.index("\nend\n")]
        words = set(re.findall(r'local cv_opts "([^"]*)"', body)[0].split())
        for line in re.findall(r'local cv_opts "`cv_opts\' ([^"]*)"', body):
            words |= set(line.split())
        for o in ("colorstart", "colorend", "colorrule", "colorfillonly",
                  "colorkeysrange", "colorkeysreverse", "colorallowmultiple",
                  "colorotherlabel", "colorlist", "coloruseplegend"):
            assert o in words, o
        assert "foreach o of local cv_opts" in body
