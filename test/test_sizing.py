"""
test_sizing.py -- scale(), fxsize()/fysize(), aspectratio(#, placement())
and xoverhangs/yoverhangs (WP-31 D5, section 32).

Before: the five options were named "not implemented" and drawn as if
absent, and aspectratio(1, placement(e)) was refused "not a positive
number".  twoway's measured behaviour is in test/fixtures/sizing_truth.json
(scripts/extract_sizing_truth.do):

* scale(1.5) draws every text, marker radius and stroke 1.5 x (scale_15);
  scale(0) draws, scale(-1) is "gm_linewidth must be between 0.000 and
  1.0e+04" r(198), scale(x) a note, drawn at 1.
* fxsize()/fysize() take any number (0 and 150 draw); a word is "option
  fxsize() incorrectly specified" r(198).  Alone, twoway keeps the graph's
  size and draws the plot region in # percent of 4 inches, centred; dash
  shrinks the figure's cell (documented).
* aspectratio(1) makes the plot region square (ar_1); with xsize(8)
  ysize(4) it stays square, centred, and placement(e)/(w)/(n)/(s) push it
  to that edge (ar_place_*, ar_vplace_*).  An unknown placement() is a
  note; aspectratio(1, foo) is "option foo not allowed" r(198).
* xoverhangs narrows the plot region so a long end label fits (overhang_x0
  against overhang_x1); yoverhangs moved nothing on the probe measured.

Every expectation is twoway's measured value or the rule it implies.
"""
import itertools
import json
import os
import re
import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_MODES = ("saved", "served")
_FIX = os.path.join(_HERE, "fixtures", "sizing_truth.json")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_SEQ = itertools.count()
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0],
})


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _spec(plots, go):
    g = {"name": "g1", "title": '"T"'}
    g.update(go or {})
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": "s2color", "session_scheme": "", "title": "",
         "subtitle": "", "registry": "g1", "tabs": "",
         "filter_position": "top", "csv": "0", "level": "95",
         "formats": {}, "limits": {}}
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "build_options": b}


def _sc(**o):
    return {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": o}


def _figure(mode, wd, go=None, plots=None):
    """The one figure g1 draws in *mode*, after the page's layout ran."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fcls
    tag = next(_SEQ)
    wd = Path(wd)
    sp, dp = wd / ("s%d.json" % tag), wd / ("d%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots or [_sc()], go)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(str(sp), str(dp))
            r.render()
            figs = list(r.figures.values())
        else:
            ap = str(wd / ("a%d.py" % tag))
            dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
            mod = load_app(ap, "_sz_app_%d" % tag)
            from bokeh.io import curdoc
            curdoc().clear()
            doc = Document()
            mod.make_document(doc)
            figs = [m for root in doc.roots for m in root.references()
                    if isinstance(m, _fcls)]
    assert len(figs) == 1, figs
    return figs[0]


def _pt(css):
    m = re.fullmatch(r"([0-9.]+)(pt|px)", str(css))
    return float(m.group(1)) * (1.0 if m.group(2) == "pt" else 0.75)


def _sizes(fig):
    """Every scaled size of *fig*: {(class, n, prop): value}."""
    out = {}
    count = {}
    for m in sorted(fig.references(), key=lambda x: (type(x).__name__,
                                                     str(getattr(x, "name", "")))):
        t = type(m).__name__
        props = {
            "LinearAxis": ("major_label_text_font_size",
                           "axis_label_text_font_size", "major_tick_out",
                           "axis_line_width"),
            "Grid": ("grid_line_width",),
            "Title": ("text_font_size",),
            "Scatter": ("size", "line_width"),
        }.get(t)
        if not props:
            continue
        k = count[t] = count.get(t, 0) + 1
        for p in props:
            v = getattr(m, p, None)
            if isinstance(v, str) and re.fullmatch(r"[0-9.]+(pt|px)", v):
                out[(t, k, p)] = _pt(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out[(t, k, p)] = float(v)
    return out


class TestTheFixture:
    def test_it_is_stamped_and_complete(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        for k in ("scale_15", "scale_bad_neg", "fxsize_50", "fysize_50",
                  "ar_1", "ar_sizes", "ar_place_e", "aspect_bad_sub",
                  "aspect_bad_place", "overhang_x0", "overhang_x1",
                  "ref_def", "ref_84", "ref_88", "lw_20000"):
            assert k in d, k

    def test_twoway_scales_every_size(self):
        d = _truth()
        b, s = d["base"], d["scale_15"]
        assert s["title_size"] / b["title_size"] == pytest.approx(1.5, abs=.01)
        assert s["xlabel_size"] / b["xlabel_size"] == pytest.approx(1.5, abs=.01)
        assert s["marker_r"] / b["marker_r"] == pytest.approx(1.5, abs=.01)
        assert [w / v for w, v in zip(s["line_widths"], b["line_widths"])] \
            == pytest.approx([1.5, 1.5], abs=.01)

    def test_twoway_squares_the_plot_region(self):
        d = _truth()
        for k in ("ar_1", "ar_sizes"):
            p = d[k]["plot"]
            assert (p["bottom"] - p["top"]) / (p["right"] - p["left"]) \
                == pytest.approx(1.0, abs=.01), k


class TestScale:
    @pytest.mark.parametrize("mode", _MODES)
    def test_every_size_scales(self, mode, tmp_path):
        a = _sizes(_figure(mode, tmp_path))
        f = _figure(mode, tmp_path, {"scale": "1.5"})
        b = _sizes(f)
        assert a and set(a) == set(b)
        for k in a:
            assert b[k] == pytest.approx(a[k] * 1.5, abs=0.51), k
        assert f._dash_scale == 1.5

    @pytest.mark.parametrize("mode", _MODES)
    def test_one_is_identity(self, mode, tmp_path):
        a = _sizes(_figure(mode, tmp_path))
        f = _figure(mode, tmp_path, {"scale": "1"})
        assert _sizes(f) == a
        assert getattr(f, "_dash_scaled", None) is None

    def test_idempotent(self):
        from bokeh.plotting import figure
        f = figure(title="T")
        f.scatter([1], [2], size=6)
        dr._dash_apply_scale(f, 2.0)
        once = _sizes(f)
        dr._dash_apply_scale(f, 2.0)
        assert _sizes(f) == once
        assert f._dash_scaled == 2.0

    def test_the_factor(self):
        for raw, want in (("1.5", 1.5), ("0", 0.0), ("", None), ("1", None),
                          ("x", None), ("-1", None), ("inf", None)):
            assert dr._dash_scale_factor({"scale": raw}) == want, raw


class TestScaleHoldsAcrossAMove:
    def test_weighted_size_columns(self):
        from bokeh.models import ColumnDataSource
        s = ColumnDataSource({"x": [1, 2], "__dash_wsize": [2.0, 4.0]})
        dr._dash_scale_columns([s, s], 1.5)
        assert s.data["__dash_wsize"] == [3.0, 6.0]
        assert s.data["x"] == [1, 2]

    def test_the_served_redraw_scales_them(self):
        src = dr.ServerAppBuilder.__dict__
        text = open(dr.__file__, encoding="utf-8").read()
        assert "_dash_scale_columns(_out, _dash_scale_factor(_go))" in text
        assert src  # the builder is the class the line belongs to


class TestScaleBounds:
    def test_the_rules(self):
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        assert "scale=mult  fxsize=optnum  fysize=optnum" in ado

    def test_twoways_refusals_recorded(self):
        d = _truth()
        assert d["scale_bad_neg"]["rc"] == 198
        assert d["scale_bad_0"]["rc"] == 0
        assert d["scale_bad_x"]["rc"] == 0
        assert d["fx_bad_x"]["lines"] == ["option fxsize() incorrectly specified"]
        assert d["fx_bad_150"]["rc"] == 0 and d["fy_bad_0"]["rc"] == 0


_SF_FIX = os.path.join(_HERE, "fixtures", "scale_frame_truth.json")
_SF_KEY = re.compile(r"[AB]:(top|left|bottom|right):(slope|intercept|linear)")


class TestScaleFrameTruth:
    """WP-33 GW-11: twoway's plot region under scale(0.5..2)
    (scale_frame_truth.json, scripts/extract_scale_frame_truth.do) and
    the hygiene of the known-differences tables test/test_scale_frame.py
    reads (default tier, D-33-11.h)."""

    def test_twoway_scales_the_gaps(self):
        """Every side but the right moves linearly with the factor (the
        title, label and key gaps scale; only the region's margins stay);
        a side twoway itself draws non-linearly is listed, with its
        owner, in SCALE_FRAME_TWOWAY_KNOWN (D43)."""
        import scale_frame_known as sfk
        from known_differences import known_problems
        with open(_SF_FIX, encoding="utf-8") as fh:
            d = json.load(fh)
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert len([k for k in d if ":" in k]) == 10
        res = {}
        for c in ("A", "B"):
            rules = d["rules"][c]
            assert rules["right"]["slope"] == 0
            for side in ("top", "left", "bottom"):
                r = rules[side]
                assert abs(r["slope"]) > 10, (c, side, r)
                res["%s:%s:linear" % (c, side)] = (
                    None if r["max_residual"] < 1 else
                    "twoway's largest residual %s" % r["max_residual"])
        assert known_problems(res, sfk.SCALE_FRAME_TWOWAY_KNOWN,
                              "scale_frame_twoway") == []

    def test_every_known_difference_is_open(self):
        import scale_frame_known as sfk
        from known_differences import dead_rows
        for name, known in (("scale_frame", sfk.SCALE_FRAME_KNOWN),
                            ("scale_frame_twoway",
                             sfk.SCALE_FRAME_TWOWAY_KNOWN)):
            assert dead_rows(known, name) == []
            assert [k for k in known if not _SF_KEY.fullmatch(k)] == []
        assert not set(sfk.SCALE_FRAME_DELIBERATE) & set(
            sfk.SCALE_FRAME_KNOWN)


class TestScaleHelp:
    def test_the_sentence_says_the_gaps_scale(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        i = text.index("{phang2}{opt scale(#)}")
        para = " ".join(text[i:text.index("{p_end}", i)].split())
        assert "gaps between boxes are not scaled" not in para
        assert "the gaps around titles, labels, keys and added text" in para
        assert "only the graph region's margins stay as they are" in para


class TestFxFy:
    @pytest.mark.parametrize("mode", _MODES)
    def test_fysize(self, mode, tmp_path):
        a = _figure(mode, tmp_path)
        b = _figure(mode, tmp_path, {"fysize": "50"})
        # Flipped (WP-45 VF-11): the figure was drawn half as tall; the figure was held in a 160-560 px band at 2.88 pt a unit; twoway
        # draws its graph's shape at 0.72 pt per inch of its smaller side
        # (VF-4, DECISIONS A-1):
        # twoway keeps the graph and draws the plot 192 px tall, centred.
        assert b.aspect_ratio == pytest.approx(a.aspect_ratio)
        h = b._dash_nominal_px[1]
        assert b.min_border_top - b._dash_frame_est["above"] == \
            pytest.approx((h - 192) / 2, abs=1)

    @pytest.mark.parametrize("mode", _MODES)
    def test_fxsize(self, mode, tmp_path):
        f = _figure(mode, tmp_path, {"fxsize": "50"})
        # Flipped (WP-45 VF-11): the cell was held to 50% of its width; the figure was held in a 160-560 px band at 2.88 pt a unit; twoway
        # draws its graph's shape at 0.72 pt per inch of its smaller side
        # (VF-4, DECISIONS A-1):
        # twoway keeps the graph and draws the plot 192 px wide, centred.
        assert f.styles.get("max-width") is None
        w = f._dash_nominal_px[0]
        assert f.min_border_left - f._dash_frame_est["left"] == \
            pytest.approx((w - 192) / 2, abs=1)

    def test_out_of_range_changes_nothing(self):
        from bokeh.plotting import figure
        for v in ("0", "-5", "100", "150", "x"):
            f = figure(aspect_ratio=2.0, max_height=560)
            dr._dash_fxy_size(f, {"fysize": v, "fxsize": v})
            assert f.aspect_ratio == 2.0 and f.max_height == 560
            assert "max-width" not in (f.styles or {})


class TestAspect:
    @pytest.mark.parametrize("mode", _MODES)
    def test_alone_keeps_figure_ratio(self, mode, tmp_path):
        f = _figure(mode, tmp_path, {"aspectratio": "1"})
        # Flipped (WP-45 VF-4): aspectratio(1) alone made the figure square;
        # the figure was held in a 160-560 px band at 2.88 pt a unit; twoway
        # draws its graph's shape at 0.72 pt per inch of its smaller side
        # (VF-4, DECISIONS A-1): the figure keeps the scheme's shape and its plot region is
        # square inside it (kept at every drawn size by the follow).
        assert f.aspect_ratio == pytest.approx(5.5 / 4.0)
        assert f.frame_width is None and f.frame_height is None
        w, h = f._dash_nominal_px
        assert w - f.min_border_left - f.min_border_right == pytest.approx(
            h - f.min_border_top - f.min_border_bottom, abs=1)

    @pytest.mark.parametrize("mode", _MODES)
    def test_survives_sizes(self, mode, tmp_path):
        f = _figure(mode, tmp_path, {"aspectratio": "1", "xsize": "8",
                                     "ysize": "4"})
        # Flipped (WP-34 VF-3): aspect_ratio 2 was the leftover that
        # collapsed the frame; the box is the figure's width and height now.
        assert f.aspect_ratio is None
        assert (f.width, f.height) == f._dash_frame_box
        assert f.min_height is None and f.max_height is None
        assert f.sizing_mode == "fixed"
        assert f.frame_width == f.frame_height
        w, h = f._dash_frame_box
        assert (w, h) == (768, 384)
        assert f.min_border_top + f.frame_height + f.min_border_bottom \
            == pytest.approx(h, abs=1)
        assert f.min_border_left + f.frame_width + f.min_border_right \
            == pytest.approx(w, abs=1)
        assert not f.js_property_callbacks

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("place", ["c", "e", "w", "n", "s", "ne", "sw"])
    def test_placement_borders(self, mode, place, tmp_path):
        ar = "1" if place not in ("n", "s") else "0.25"
        f = _figure(mode, tmp_path, {"aspectratio": ar, "aspectplacement":
                                     place, "xsize": "8" if ar == "1" else "4",
                                     "ysize": "4"})
        b = f._dash_frame_est
        left = f.min_border_left - b["left"]
        right = f.min_border_right - b["right"]
        top = f.min_border_top - b["above"]
        bottom = f.min_border_bottom - b["below"]
        if "e" in place:
            assert left > 0 and right == pytest.approx(0, abs=1)
        elif "w" in place:
            assert right > 0 and left == pytest.approx(0, abs=1)
        else:
            assert left == pytest.approx(right, abs=1)
        if place == "n":
            assert bottom > 0 and top == pytest.approx(0, abs=1)
        elif place == "s":
            assert top > 0 and bottom == pytest.approx(0, abs=1)

    def test_placement_is_measured(self):
        d = _truth()
        e, w, c = (d["ar_place_" + k]["plot"] for k in ("e", "w", "c"))
        assert e["right"] > c["right"] > w["right"]
        assert d["aspect_bad_sub"]["lines"] == ["option foo not allowed"]
        assert d["aspect_bad_place"]["rc"] == 0

    def test_the_borders_count_the_title(self):
        """D55: a figure's own title is counted on its side, as its lines
        at 1.3 x the font's px plus its standoff; an empty title is not."""
        from bokeh.plotting import figure
        f = figure(title="T\nU")
        f.title.text_font_size = "14pt"
        b = dr._dash_frame_borders(f)
        assert b["above"] == pytest.approx(2 * 1.3 * 14 * 4 / 3
                                           + f.title.standoff)
        assert dr._dash_frame_borders(figure())["above"] == 5
        g = figure(title="T", title_location="left")
        assert dr._dash_frame_borders(g)["left"] > 5
        assert dr._dash_frame_borders(g)["above"] == 5

    def test_the_frame_rule(self):
        from bokeh.plotting import figure
        f = figure()
        b = dr._dash_frame_borders(f)
        dr._dash_frame_sizes(f, 0.5, "c", 600, 600)
        assert f.frame_height == round(f.frame_width * 0.5)
        assert f.frame_width == round(600 - b["left"] - b["right"])


#: aspectratio() with xsize()/ysize(): the three probes measured in [B]
#: §4.6 (WP-34 VF-3).  Every box is under the page's height bound, so the
#: expectations compare with ``_dash_frame_box``, never with a bound.
_FIXED = (
    {"aspectratio": "2", "xsize": "8", "ysize": "4"},
    {"aspectratio": "1", "xsize": "8"},
    {"aspectratio": ".5", "xsize": "6", "ysize": "3"},
)
_FIXED_IDS = ("ar2_8x4", "ar1_8", "ar05_6x3")

#: The same box with a title, and a title and subtitle (D55), and the room
#: above the frame headless Chrome gave them: title 14pt 31 px (bokeh 3.9;
#: 33 under 3.8), a subtitle 11pt 26 px (28) under it.
_FIXED_TITLED = (
    {"aspectratio": "2", "xsize": "8", "ysize": "4", "title": '"T"'},
    {"aspectratio": "2", "xsize": "8", "ysize": "4", "title": '"T"',
     "subtitle": '"S"'},
)
_FIXED_TITLED_IDS = ("ar2_title", "ar2_title_subtitle")
_TITLE_ROOM = {"ar2_title": 33, "ar2_title_subtitle": 61}


def _fixed_build(mode, wd, go):
    """``(figure, models, log lines)`` of *go* in *mode*: every model of
    the page's roots and every record Bokeh logged while the page was
    built -- the saved page's ``render()``, or the served document's
    creation and validation (what the server runs before it sends it)."""
    import logging
    from bokeh.plotting import figure as _fcls
    seen = []

    class _H(logging.Handler):
        def emit(self, record):
            seen.append(record.getMessage())

    log = logging.getLogger("bokeh")
    h = _H(level=logging.DEBUG)
    log.addHandler(h)
    try:
        tag = next(_SEQ)
        wd = Path(wd)
        sp, dp = wd / ("s%d.json" % tag), wd / ("d%d.json" % tag)
        sp.write_text(json.dumps(_spec([_sc()], go)), encoding="utf-8")
        dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                r = dr.DashRenderer(str(sp), str(dp))
                r.render()
                roots = [r._last_layout_root]
            else:
                from bokeh.document import Document
                ap = str(wd / ("a%d.py" % tag))
                dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
                mod = load_app(ap, "_sz_fixed_%d" % tag)
                doc = Document()
                mod.make_document(doc)
                doc.validate()
                roots = list(doc.roots)
    finally:
        log.removeHandler(h)
    models = set()
    for root in roots:
        models |= set(root.references())
    figs = [m for m in models if isinstance(m, _fcls)]
    assert len(figs) == 1, figs
    return figs[0], models, seen


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("go", _FIXED, ids=_FIXED_IDS)
class TestFixedFrame:
    """aspectratio() with xsize()/ysize() (WP-34 VF-3): the figure is the
    box, its height bounds and own ratio are cleared, and its frame has
    ratio # -- before, BokehJS sized the host 600 x 560 from Bokeh's
    default height against max_height and aspectratio(2) xsize(8) ysize(4)
    drew a 0 px frame, and every build printed E-1023."""

    def test_box_and_ratio(self, mode, go, tmp_path):
        f, _m, _l = _fixed_build(mode, tmp_path, go)
        ar = float(go["aspectratio"])
        assert f.sizing_mode == "fixed"
        assert (f.width, f.height) == f._dash_frame_box
        assert isinstance(f.width, int) and isinstance(f.height, int)
        assert f.min_height is None and f.max_height is None
        assert f.aspect_ratio is None
        assert f.frame_width > 0 and f.frame_height > 0
        assert f.frame_height / f.frame_width == pytest.approx(ar, rel=0.01)
        w, h = f._dash_frame_box
        assert f.min_border_left + f.frame_width + f.min_border_right \
            == pytest.approx(w, abs=1)
        assert f.min_border_top + f.frame_height + f.min_border_bottom \
            == pytest.approx(h, abs=1)

    def test_no_validation_message(self, mode, go, tmp_path):
        from bokeh.core.validation import check_integrity
        _f, models, logged = _fixed_build(mode, tmp_path, go)
        issues = check_integrity(models)
        codes = sorted("W-%d %s" % (w.code, w.name) for w in issues.warning) \
            + sorted("E-%d %s" % (e.code, e.name) for e in issues.error)
        assert codes == [], codes
        assert [m for m in logged if "E-10" in m or "W-10" in m] == [], logged


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("go,room", [(g, _TITLE_ROOM[i]) for g, i in
                                     zip(_FIXED_TITLED, _FIXED_TITLED_IDS)],
                         ids=_FIXED_TITLED_IDS)
class TestFixedFrameTitles:
    """D55: the figure's own title, and a subtitle under it, take room
    above the frame; the estimate counts them, so BokehJS draws the frame
    at its size and ratio instead of squeezing it (title("T") drew 168x308,
    ratio 1.83, for aspectratio(2) xsize(8) ysize(4))."""

    def test_the_room_above_holds_them(self, mode, go, room, tmp_path):
        f, _m, _l = _fixed_build(mode, tmp_path, go)
        assert f._dash_frame_est["above"] >= room
        assert f.min_border_top >= room
        assert f.frame_height / f.frame_width == pytest.approx(2.0, rel=0.01)
        assert f.min_border_top + f.frame_height + f.min_border_bottom \
            == pytest.approx(f.height, abs=1)


class TestFixedFrameHelp:
    def test_the_size_sentence(self):
        from test_help_claims_1 import _between, _help
        para = " ".join(_between(_help(), "{phang2}{opt aspectratio(#)}",
                                 "{p_end}").split())
        # D55: the residual is stated (titles estimated up to 4 px high
        # each line, measured in Chrome), no longer "a few pixels" either way.
        assert ("The figure is drawn at that size; the room the axes and "
                "titles take is estimated, up to 4 pixels high for each "
                "line of a title, so the plot region, always of ratio "
                "{it:#}, can be that much smaller than the largest that "
                "fits.") in para
        assert "differ from the largest fit by a few pixels" not in para
        assert ("Such a figure keeps its size in a cell narrower than it, "
                "which then scrolls sideways.") in para
        assert "the figure's size can differ from {cmd:xsize()}" not in para
        # Flipped (WP-45 VF-4): the height bound was 45-04's to remove;
        # the figure was held in a 160-560 px band at 2.88 pt a unit; twoway
        # draws its graph's shape at 0.72 pt per inch of its smaller side
        # (VF-4, DECISIONS A-1).
        assert "held to the page's height bound" not in para


class TestOverhangs:
    @pytest.mark.parametrize("mode", _MODES)
    def test_per_fixture(self, mode, tmp_path):
        d = _truth()
        p0, p1 = d["overhang_x0"]["plot"], d["overhang_x1"]["plot"]
        assert p1["left"] > p0["left"] and p1["right"] < p0["right"]
        a = _figure(mode, tmp_path)
        f = _figure(mode, tmp_path, {"xoverhangs": "xoverhangs",
                                     "xlabel": '1800 "a very long first label" 4000'})
        assert (f.min_border_right or 0) > (a.min_border_right or 5)
        assert (f.min_border_left or 0) > (a.min_border_left or 5)

    def test_never_lowers(self):
        from bokeh.plotting import figure
        f = figure(min_border_left=300, min_border_right=300)
        dr._dash_overhangs(f, {"xoverhangs": "xoverhangs"})
        assert f.min_border_left == 300 and f.min_border_right == 300


class TestSilentWhenHonoured:
    @pytest.mark.parametrize("option", ["scale", "fxsize", "fysize",
                                        "xoverhangs", "yoverhangs"])
    def test_no_pending_line(self, option):
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        assert "_dash_pending' %s\"" % option not in ado

    def test_placement_reaches_the_spec(self):
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        assert "program define _dash_aspect_split\n" in ado
        assert ado.count("aspectplacement xoverhangs yoverhangs nodraw") == 7
