"""test_noted_options_drawn.py -- options twoway draws that dash only noted
(WP-47 basic:PT-11, section 47-05).

dash accepted back markers (bmsymbol() .. bmlalign()), mlabalignment(),
mlabjustification() and contour's zvarlabel(), named each in its note
"(note: dash: ignoring unsupported option(s): ...)" and drew the default.
twoway draws each (measured 10nov2026, StataNow 19.5, graph export SVG:
test/fixtures/noted_option_truth.json, which says where twoway's picture
differs, and test/fixtures/noted_drawn_truth.json, its geometry).  Each
test draws the option in both modes, the saved page and the served app.
alalign() and blalign(), which dash.ado folds onto lalign(), are checked by
test/test_wp47_truth.cscript Q4705.
"""
from __future__ import annotations

import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer, HoverTool, LabelSet, Legend

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = tsr.MODES
_FX = os.path.join(_HERE, "fixtures")


def _fixture(name):
    with open(os.path.join(_FX, name), encoding="utf-8") as fh:
        return json.load(fh)


DRAWN = _fixture("noted_drawn_truth.json")["probes"]
NOTED = _fixture("noted_option_truth.json")["probes"]


def _draw(plots, mode, scheme="stcolor"):
    if isinstance(plots, dict):
        plots = [plots]
    d = tsr._draw(tp._spec(list(plots), {"scheme": scheme}, {}), mode)
    return d, [m for m in d.warnings if m.startswith("dash")]


def _renderers(d):
    return [r for f in d.figures for r in f.renderers
            if isinstance(r, GlyphRenderer)]


def _back(d):
    return [r for r in _renderers(d)
            if "dash_backmarker" in (r.tags or [])]


def _circles(key, fill=None):
    """The circles of probe *key* as (fill, stroke, width, ring diameter):
    a filled circle then its stroked ring, per marker, in drawing order."""
    out = []
    for e in DRAWN[key]["elements"]:
        if e["kind"] == "circle":
            out.append(e)
    return out


#: The types twoway draws back markers on (noted_option_truth.json
#: bmsymbol(T): a different picture on each), drawn through dash's mappers.
_BACK_TYPES = ["scatter", "connected", "dot", "dropline", "rcapsym",
               "rconnected", "rscatter", "rpcap", "rpspike", "pcscatter",
               "pccapsym", "scatteri"]


class TestTheFixtures:
    """The classification 47-05-01 drew is the fixtures' (a re-extraction
    that moved it fails here first)."""

    def test_twoway_draws_back_markers_on_the_marker_types(self):
        rows = NOTED["bmsymbol(T)"]
        diff = {t for t, r in rows.items()
                if r["twoway_rc"] == 0 and r["twoway_draws"] is True}
        assert set(_BACK_TYPES) <= diff
        assert diff - set(_BACK_TYPES) <= {"contour"}

    def test_label_layout_differs_only_with_labels(self):
        for opt in ("mlabalignment(top)", "mlabjustification(right)"):
            diff = {t for t, r in NOTED[opt].items()
                    if r["twoway_draws"] is True}
            assert diff <= {"contour"}
            ctx = NOTED[opt + "+mlabel"]
            assert ctx["scatter"]["twoway_draws"] is True

    def test_back_options_alone_draw_the_same(self):
        for opt in ("bmcolor(red)", "bmsize(large)", "bmlwidth(thick)",
                    "bmlalign(outside)", "bmlpattern(dash)"):
            rows = NOTED[opt]
            assert rows["scatter"]["twoway_draws"] is False, opt


@pytest.mark.parametrize("mode", MODES)
class TestBackMarkers:

    @pytest.mark.parametrize("ptype", _BACK_TYPES)
    def test_drawn_under_the_marker(self, mode, ptype):
        """bmsymbol(T): a triangle drawn just before each marker renderer,
        over its source and view, as twoway draws the back symbol first
        (BM02); no note."""
        d, notes = _draw(plot_for(ptype, {"bmsymbol": "T"}), mode)
        backs = _back(d)
        assert backs, ptype
        assert not notes
        for f in d.figures:
            rs = list(f.renderers)
            for b in [r for r in rs if r in backs]:
                front = b._dash_backmarker_of
                assert rs.index(front) > rs.index(b)
                assert front.data_source is b.data_source
                assert b.glyph.marker == "triangle"
                assert front.glyph.x == b.glyph.x
                assert front.glyph.y == b.glyph.y

    def test_default_style(self, mode):
        """bmsymbol(O) alone: a white back marker outlined in the
        background's colour at twoway's smallest ring (BM01): stcolor's
        white, s2color's #eaf2f3 (BM16), its outline the background
        linestyle's width."""
        for scheme, line in (("stcolor", "#ffffff"), ("s2color", "#eaf2f3")):
            d, _ = _draw(plot_for("scatter", {"bmsymbol": "O"}), mode, scheme)
            [b] = _back(d)
            assert b.glyph.fill_color == "#ffffff"
            assert b.glyph.line_color == line
            assert b.glyph._dash_stroke_nominal[0] == 0.0
            # Drawn as msize(0) is: twoway's smallest ring.
            d0, _ = _draw(plot_for("scatter", {"msize": "0"}), mode, scheme)
            [m] = [r for r in _renderers(d0)
                   if type(r.glyph).__name__ == "Scatter"]
            assert b.glyph.size == pytest.approx(m.glyph.size)
        e = _circles("BM01")
        assert e[0]["fill"] == "#ffffff" and e[1]["stroke"] == "#ffffff"
        e = _circles("BM16")
        assert e[1]["stroke"] == "#eaf2f3"

    def test_size_as_msize(self, mode):
        """bmsize(large): the back ring as large as msize(large)'s ring
        (BM04 against BM09: 78.64 SVG units each)."""
        assert _circles("BM04")[1]["extent"] == pytest.approx(
            _circles("BM09")[7]["extent"])
        d, _ = _draw(plot_for("scatter", {"bmsymbol": "O",
                                          "bmsize": "large"}), mode)
        [b] = _back(d)
        d2, _ = _draw(plot_for("scatter", {"msize": "large"}), mode)
        [m] = [r for r in _renderers(d2) if type(r.glyph).__name__ == "Scatter"]
        assert b.glyph._dash_stroke_nominal[0] == pytest.approx(
            m.glyph._dash_stroke_nominal[0])

    def test_colour_is_the_fill(self, mode):
        """bmcolor(red) fills the back marker and leaves its outline (BM03:
        a red fill, the white ring)."""
        e = _circles("BM03")
        assert e[0]["fill"] == "#ff0000" and e[1]["stroke"] == "#ffffff"
        d, _ = _draw(plot_for("scatter", {"bmsymbol": "O",
                                          "bmcolor": "red"}), mode)
        [b] = _back(d)
        assert b.glyph.fill_color.lower() in ("#ff0000", "red")
        assert b.glyph.line_color == "#ffffff"

    def test_outline(self, mode):
        """bmlcolor(red) bmlwidth(thick) bmlalign(outside): the back
        outline red and thick, drawn outside (BM07: the ring S + 2w)."""
        e = _circles("BM07")
        w = e[1]["stroke_width"]
        assert e[1]["extent"] == pytest.approx(
            _circles("BM05")[1]["extent"] + 2 * w, abs=0.05)
        d, _ = _draw(plot_for("scatter", {
            "bmsymbol": "O", "bmlcolor": "red", "bmlwidth": "thick",
            "bmlalign": "outside"}), mode)
        [b] = _back(d)
        lw = b.glyph.line_width
        assert lw == pytest.approx(dr.OptionTranslator.translate_lwidth(
            "thick"))
        # Bokeh strokes centred: drawn at S + 2w, outer edge S + 3w.
        assert b.glyph.size == pytest.approx(
            b.glyph._dash_stroke_nominal[0] + 2 * lw)

    def test_hollow(self, mode):
        """bmsymbol(Oh): the ring alone (BM10)."""
        assert all(e["fill"] in (None, "none") or e["stroke"]
                   for e in _circles("BM10")[:3])
        d, _ = _draw(plot_for("scatter", {"bmsymbol": "Oh"}), mode)
        [b] = _back(d)
        assert b.glyph.fill_alpha == 0.0

    @pytest.mark.parametrize("case", ["mlabel", "weight", "colorvar",
                                      "none"])
    def test_not_drawn(self, mode, case):
        """twoway draws no back marker for labelled points (BM11), weighted
        ones (BM12) or under colorvar() (BM13), and none for bmsymbol(none)."""
        o = {"bmsymbol": "O"}
        extra = {}
        if case == "mlabel":
            o["mlabel"] = "foreign"
        elif case == "colorvar":
            o["colorvar"] = "price"
        elif case == "none":
            o["bmsymbol"] = "none"
        else:
            o.update({"weight": "aweight", "wexp": "price"})
        d, _ = _draw(plot_for("scatter", o, **extra), mode)
        assert not _back(d)
        key = {"mlabel": "BM11", "weight": "BM12", "colorvar": "BM13"}.get(
            case)
        if key:
            assert all(e["fill"] != "#ffffff" for e in _circles(key))

    def test_not_in_hover_or_legend(self, mode):
        d, _ = _draw([plot_for("scatter", {"bmsymbol": "O"}),
                      plot_for("scatter", {})], mode)
        backs = _back(d)
        assert backs
        for f in d.figures:
            for t in f.tools:
                if isinstance(t, HoverTool) and t.renderers not in (
                        None, "auto"):
                    assert not set(map(id, t.renderers)) & set(
                        map(id, backs))
            for lg in f.select(type=Legend):
                for it in lg.items:
                    assert not set(map(id, it.renderers)) & set(
                        map(id, backs))


def _labels(d):
    return [m for f in d.figures for m in f.center
            if isinstance(m, LabelSet)]


def _em(key):
    """twoway's baseline below the marker centre, in ems of the label
    size, for probe *key* (position 3: the anchor is level with the
    point)."""
    r = DRAWN[key]
    c = [e for e in r["elements"] if e["kind"] == "circle"][0]["center"][1]
    t = [t for t in r["texts"] if t["text"].startswith("AMC Concord")][0]
    return (t["y"] - c) / 89.94


@pytest.mark.parametrize("mode", MODES)
class TestLabelLayout:

    @pytest.mark.parametrize("v,key", [("top", "ML01"), ("bottom", "ML02"),
                                       ("baseline", "ML04")])
    def test_alignment(self, mode, v, key):
        """mlabalignment(): the label's baseline as far below its anchor,
        in ems, as twoway draws it (ML01, ML02, ML04)."""
        d, notes = _draw(plot_for("scatter", {"mlabel": "foreign",
                                              "mlabalignment": v}), mode)
        [ls] = _labels(d)
        px = dr.OptionTranslator.css_to_pt(ls.text_font_size) \
            * dr.OptionTranslator.PX_PER_PT
        assert ls.text_baseline == "alphabetic"
        assert -ls.y_offset / px == pytest.approx(_em(key), abs=0.01)
        assert not notes

    def test_middle_is_the_default(self, mode):
        """mlabalignment(middle) draws the default (ML03 equals ML00)."""
        assert _em("ML03") == pytest.approx(_em("ML00"))
        d, _ = _draw(plot_for("scatter", {"mlabel": "foreign",
                                          "mlabalignment": "middle"}), mode)
        d0, _ = _draw(plot_for("scatter", {"mlabel": "foreign"}), mode)
        [a], [b] = _labels(d), _labels(d0)
        assert (a.text_baseline, a.y_offset) == (b.text_baseline, b.y_offset)

    @pytest.mark.parametrize("v,anchor", [("right", "end"),
                                          ("center", "middle"),
                                          ("left", "start")])
    def test_justification(self, mode, v, anchor):
        """mlabjustification(): the side of the anchor twoway puts the text
        on (ML05-ML07)."""
        key = {"right": "ML05", "center": "ML07", "left": "ML06"}[v]
        assert {t["anchor"] for t in DRAWN[key]["texts"]
                if t["text"].startswith("AMC")} == {anchor}
        d, notes = _draw(plot_for("scatter", {"mlabel": "foreign",
                                              "mlabjustification": v}), mode)
        [ls] = _labels(d)
        assert ls.text_align == {"end": "right", "middle": "center",
                                 "start": "left"}[anchor]
        assert not notes

    @pytest.mark.parametrize("opt,cls,key", [
        ("mlabalignment", "vertical_text", "ML10"),
        ("mlabjustification", "horizontal", "ML11")])
    def test_unknown_word_noted(self, mode, opt, cls, key):
        """A word twoway does not know: its note, the default drawn."""
        assert any(cls in ln for ln in DRAWN[key]["printed"])
        d, notes = _draw(plot_for("scatter", {"mlabel": "foreign",
                                              opt: "nosuch"}), mode)
        assert any("named style nosuch not found in class " + cls in n
                   for n in notes)


@pytest.mark.parametrize("mode", MODES)
class TestContour:

    def _title(self, mode, opts):
        import colour_bins
        d, notes = _draw({"type": "contour", "zvar": "price", "yvar": "mpg",
                          "xvar": "weight", "options": opts}, mode)
        titles = [cb.title for f in d.figures
                  for cb in colour_bins.key_views(f)]
        return titles, notes

    def test_zvarlabel(self, mode):
        """zvarlabel(Z) titles contour's key Z (ZV01, ZV00's gz)."""
        assert "Z" in [t["text"] for t in DRAWN["ZV01"]["texts"]]
        titles, notes = self._title(mode, {"zvarlabel": "Z"})
        assert titles == ["Z"]
        assert not notes
        titles, _ = self._title(mode, {"zvarlabel": '"Z b"'})
        assert titles == ["Z b"]

    def test_first_word_unquoted(self, mode):
        """zvarlabel(A b): twoway titles the key A (ZV04)."""
        texts = [t["text"] for t in DRAWN["ZV04"]["texts"]]
        assert "A" in texts and "A b" not in texts
        titles, _ = self._title(mode, {"zvarlabel": "A b"})
        assert titles == ["A"]


class TestTheHelpers:

    @pytest.mark.parametrize("raw,want", [
        ("", None), ("Z", "Z"), ('"Z b"', "Z b"), ("A b", "A"),
        ('`"x y"\'', "x y")])
    def test_zvarlabel(self, raw, want):
        assert dr._dash_zvarlabel({"zvarlabel": raw} if raw else {}) == want

    def test_back_marker_style(self):
        st = dr.SchemeParser("s2color").back_marker_style()
        assert st == {"fill": "#ffffff", "line": "#eaf2f3",
                      "line_width": dr.OptionTranslator.translate_lwidth(
                          "thin")}


# ---------------------------------------------------------------------------
# Rows 4-7 and the routed words (the section's second pass)
# ---------------------------------------------------------------------------

#: auto's first ten rows: weight, mpg (sysuse auto).
_W10 = [2930, 3350, 2640, 3250, 4080, 3670, 2230, 3280, 3880, 3400]
_M10 = [22, 17, 22, 20, 15, 18, 26, 20, 16, 19]


def _bars(key):
    return [e for e in DRAWN[key]["elements"] if e["kind"] == "rect"
            and e["fill"] not in (None, "none")]


def _px_of(key, xs):
    """twoway's x scale of probe *key*'s default bars (one per row, centred
    on its x), fitted to the rows' xs: px = a * x + b."""
    import numpy as np
    c = [(e["x0"] + e["x1"]) / 2.0 for e in _bars(key)]
    a, b = np.polyfit(np.asarray(xs, float), np.asarray(c, float), 1)
    return lambda x: a * x + b


class TestBarSpan:

    def test_spanning_is_twoways(self):
        """BT01: each drawn bar runs from its row's x to the next row's x,
        in the rows' order; _dash_bar_span gives the same edges, and none
        for the last row."""
        import numpy as np
        px = _px_of("BT00", _W10[:5])
        got = sorted((round(e["x0"]), round(e["x1"])) for e in _bars("BT01"))
        c, w = dr._dash_bar_span(_W10[:5], _M10[:5], "spanning")
        want = sorted((round(px(ci - wi / 2)), round(px(ci + wi / 2)))
                      for ci, wi in zip(c, w) if np.isfinite(wi))
        assert len(got) == len(want)
        for g, h in zip(got, want):
            assert g == pytest.approx(h, abs=3)
        assert np.isnan(w[-1])

    def test_edge_cases(self):
        """BT03 one bar and BT04 one distinct x draw nothing; BT05 a missing
        x ends the bar before it and draws none of its own (rows 3 and 4)."""
        import numpy as np
        assert _bars("BT03") == [] and _bars("BT04") == []
        c, w = dr._dash_bar_span([2930.0], [22.0], "spanning")
        assert np.isnan(w).all()
        c, w = dr._dash_bar_span([1.0] * 10, _M10, "spanning")
        assert (w[np.isfinite(w)] == 0).all()
        xs = list(map(float, _W10))
        xs[3] = float("nan")
        c, w = dr._dash_bar_span(xs, _M10, "spanning")
        assert np.isnan(w[2]) and np.isnan(w[3]) and np.isnan(w[9])
        # Row 5 (mpg 15, the axis floor) draws a bar of no height in
        # twoway's SVG, which writes none: six rects for seven widths.
        assert int(np.isfinite(w).sum()) == len(_bars("BT05")) + 1

    def test_obs(self):
        """BT13: bartype(obs) bars are (max - min) / (n - 1) wide."""
        px = _px_of("BT00", _W10[:5])
        ws = {round(e["x1"] - e["x0"]) for e in _bars("BT13")}
        c, w = dr._dash_bar_span(_W10[:5], _M10[:5], "obs")
        assert ws == {round(px(w[0]) - px(0))}

    def test_fixed_and_notes(self):
        """bartype(fixed) draws the default (BT02); an unknown word twoway's
        two notes (BT07, BT15)."""
        assert _bars("BT02") == _bars("BT00")
        assert "yxbartype_g" in DRAWN["BT07"]["printed"][0]
        assert "yxbartype_g" in DRAWN["BT15"]["printed"][0]

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("bt", ["spanning", "obs"])
    def test_drawn(self, mode, bt):
        import numpy as np
        d, notes = _draw(plot_for("bar", {"bartype": bt}), mode)
        [r] = [r for r in _renderers(d) if type(r.glyph).__name__ == "VBar"]
        assert r.glyph.width == dr.GlyphMapper._BAR_W or getattr(
            r.glyph.width, "field", None) == dr.GlyphMapper._BAR_W
        src = r.data_source
        assert src._dash_join["kind"] == "span"
        assert np.isfinite(np.asarray(src.data[dr.GlyphMapper._BAR_W],
                                      float)).any()


def _span_js(nd, spec, keep):
    from js_runner import run_js
    js = dr._FILTER_JS
    i = js.index("function dash_bar_span(")
    j = js.index("function dash_join_rebuild(", i)
    return run_js(js[i:j] + "\nconst nd = " + json.dumps(nd) + ";\n"
                  "dash_bar_span(nd, " + json.dumps(spec) + ", 'rid', new Set("
                  + json.dumps(sorted(keep)) + "));\n"
                  "console.log(JSON.stringify(nd));\n")


class TestBarSpanTwin:
    """The saved page's move (dash_bar_span) and _dash_bar_span agree."""

    @pytest.mark.parametrize("mode", ["spanning", "obs"])
    @pytest.mark.parametrize("keep", [range(10), [0, 1, 2, 5, 6, 9],
                                      [4], []])
    def test_node_and_python_agree(self, mode, keep):
        import numpy as np
        xs = [float(v) for v in _W10]
        xs[3] = None
        ys = [float(v) for v in _M10]
        spec = {"kind": "span", "mode": mode, "c": "c", "w": "w",
                "ids": list(range(10)), "xs": xs, "ys": ys}
        kept = sorted(keep)
        nd = {"rid": [i for i in kept if xs[i] is not None]}
        out = _span_js(nd, spec, kept)
        px = [xs[i] if xs[i] is not None else float("nan") for i in kept]
        c, w = dr._dash_bar_span(px, [ys[i] for i in kept], mode)
        want = {i: (c[k], w[k]) for k, i in enumerate(kept)}
        for r, cj, wj in zip(out["rid"], out["c"], out["w"]):
            cp, wp = want[r]
            assert (cj is None and not np.isfinite(wp)) or \
                wj == pytest.approx(wp)


@pytest.mark.parametrize("mode", MODES)
class TestNumkeys:

    def _items(self, d):
        return [it for f in d.figures for lg in f.select(type=Legend)
                for it in lg.items]

    def test_three_keys_and_the_next(self, mode):
        """numkeys(3) then a second plot: four keys, the first three the
        first plot's (NK01: Mileage x3, Turn)."""
        texts = [t["text"] for t in DRAWN["NK01"]["texts"]]
        assert texts.count("Mileage (mpg)") == 3
        d, notes = _draw([plot_for("scatter", {"numkeys": "3"}),
                          plot_for("scatter", {})], mode)
        items = self._items(d)
        assert len(items) == 4
        assert items[0].renderers == items[1].renderers == items[2].renderers

    def test_none(self, mode):
        """numkeys(0): the plot gives no key; one key left draws no legend
        (NK03)."""
        assert "Mileage (mpg)" not in [t["text"] for t in DRAWN["NK03"]["texts"]]
        d, _ = _draw([plot_for("scatter", {"numkeys": "0"}),
                      plot_for("scatter", {})], mode)
        assert not any(lg.visible for f in d.figures
                       for lg in f.select(type=Legend) if lg.items)

    def test_helper(self, mode):
        for raw, k in (("", 1), ("3", 3), ("0", 0), ("abc", 1), ("-1", 1)):
            assert dr._dash_numkeys({"options": {"numkeys": raw}}) == k


@pytest.mark.parametrize("mode", MODES)
class TestRouted:

    def test_below(self, mode):
        """below on lfitci: the fit line drawn before the band (BL00, BL01)."""
        kinds = lambda k: [e["fill"] in (None, "none") and e["stroke"] != "#e0e0e0"
                           for e in DRAWN[k]["elements"] if e["kind"] == "path"]
        assert kinds("BL01")[0] and not kinds("BL00")[0]
        for ptype in ("lfitci", "qfitci", "lpolyci", "fpfitci"):
            d, notes = _draw(plot_for(ptype, {"below": "below"}), mode)
            names = [type(r.glyph).__name__ for r in _renderers(d)]
            assert names.index("Line") < min(
                names.index(n) for n in names if n in ("VArea", "Band",
                                                        "Patch")), ptype

    def test_noback(self, mode):
        """noback on mspline/mband: the y's own label, not "Median spline"
        (NB00, NB01, NB02)."""
        texts = lambda k: [t["text"] for t in DRAWN[k]["texts"]]
        assert "Median spline" in texts("NB00")
        assert "Mileage (mpg)" in texts("NB01")
        assert "Mileage (mpg)" in texts("NB02")
        for ptype in ("mspline", "mband"):
            plot = plot_for(ptype, {"noback": "noback"})
            ser = dr._dash_layer_series(plot, {"mpg": "Mileage (mpg)"})
            assert ser[0][0] == "Mileage (mpg)", ptype
            ser = dr._dash_layer_series(plot_for(ptype, {}),
                                        {"mpg": "Mileage (mpg)"})
            assert ser[0][0] in ("Median spline", "Median bands")

    def test_kdensity_omitanymiss(self, mode):
        """omitanymiss on kdensity: the grid's first min(n, _N) points
        (KD00 300, KD01 74, KD02 n(50) 50, KD04 n(500) 74)."""
        n = lambda k: [len(e.get("points", [])) for e in
                       DRAWN[k]["elements"] if e["kind"] == "path"][0]
        assert (n("KD00"), n("KD01"), n("KD02"), n("KD04")) == (300, 74, 50,
                                                                74)
        assert dr._dash_kde_omit_keep({"omit": "omitanymiss"}, 300, 74) == 74
        assert dr._dash_kde_omit_keep({"omit": "omitanymiss"}, 50, 74) is None
        assert dr._dash_kde_omit_keep({}, 300, 74) is None
        d, _ = _draw(plot_for("kdensity", {"omit": "omitanymiss",
                                           "omit_n": "74"}), mode)
        d0, _ = _draw(plot_for("kdensity", {}), mode)
        [a] = [r for r in _renderers(d) if type(r.glyph).__name__ == "Line"]
        [b] = [r for r in _renderers(d0) if type(r.glyph).__name__ == "Line"]
        # dash.ado writes the data's _N as omit_n.
        assert len(b.data_source.data["x"]) == 300
        assert len(a.data_source.data["x"]) == 74

    def test_dot_back_marker_over_the_rows(self, mode):
        """twoway draws dot's rows, then the back markers, then the markers."""
        d, _ = _draw(plot_for("dot", {"bmsymbol": "O"}), mode)
        tags = [tuple(r.tags or ()) for r in _renderers(d)]
        i = next(k for k, t in enumerate(tags) if "dash_dots" in t)
        j = next(k for k, t in enumerate(tags) if "dash_backmarker" in t)
        assert i < j < len(tags) - 1


@pytest.mark.parametrize("mode", MODES)
class TestLabelLayoutRows:

    def test_vposition(self, mode):
        """Under mlabvposition() each row's label is aligned and justified
        as a scalar one (MV00-MV02: top moves every row's baseline 0.3485
        em lower; right ends every row's text)."""
        y = lambda k: [t["y"] for t in DRAWN[k]["texts"]
                       if t["text"].startswith("AMC")]
        assert [b - a for a, b in zip(y("MV00"), y("MV01"))] \
            == pytest.approx([31.4, 62.8, 31.4], abs=0.2)
        assert {t["anchor"] for t in DRAWN["MV02"]["texts"]
                if t["text"].startswith("AMC")} == {"end"}
        p = plot_for("scatter", {"mlabel": "foreign", "mlabvposition": "foreign",
                                 "mlabalignment": "top",
                                 "mlabjustification": "right"})
        d, _ = _draw(p, mode)
        [ls] = _labels(d)
        assert ls.text_align == "right"
        assert ls.text_baseline == "alphabetic"
        assert getattr(ls.y_offset, "field", "").endswith("_al_top")


class TestAbbreviations:
    """Each folded word's minimum (noted_drawn_truth.json AB_<word>_<L>):
    every spelling from it up draws the full name's picture, the one
    below does not."""

    MINIMUM = {"alalign": "ala", "blalign": "bla", "bmsymbol": "bms",
               "bmcolor": "bmc", "bmsize": "bmsi", "bmlcolor": "bmlc",
               "bmlwidth": "bmlw", "bmlalign": "bmla", "bmlpattern": "bmlp",
               "mlabalignment": "mlabalign", "mlabjustification": "mlabjust",
               "zvarlabel": "zvarl", "bartype": "bart", "dropto": "drop",
               "numkeys": "numkey", "omitanymiss": "omitanym",
               "noback": "noback", "below": "below"}

    @pytest.mark.parametrize("word", sorted(MINIMUM))
    def test_minimum(self, word):
        m = len(self.MINIMUM[word])
        for L in range(m, len(word) + 1):
            assert DRAWN["AB_%s_%d" % (word, L)]["same_as_full"], (word, L)
        if m > 1:
            assert not DRAWN["AB_%s_%d" % (word, m - 1)]["same_as_full"]

    @pytest.mark.parametrize("word", sorted(MINIMUM))
    def test_the_fold_reads_the_minimum(self, word):
        src = open(os.path.join(_HERE, "..", "dash.ado"),
                   encoding="utf-8").read()
        i = src.index("program define _dash_fold_drawn")
        assert "%s:%s:" % (word, self.MINIMUM[word]) in src[i:i + 2000]

    @pytest.mark.parametrize("word", sorted(MINIMUM))
    def test_dash_answers_each_spelling_as_twoway(self, word):
        """dash's rc for every spelling of the word, the shorter ones that
        bind to another option or none included, is twoway's."""
        for L in range(1, len(word) + 1):
            r = DRAWN["AB_%s_%d" % (word, L)]
            assert r["dash_rc"] == r["rc"], (word, L, r["dash_rc"], r["rc"])
