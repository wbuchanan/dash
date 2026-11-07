"""
test_tick_label_options_p9.py
WP-44 section 44-02: the label and tick sub-options -- custom (AX-5), the
gridlines of the tick options (AX-6), the label words (AX-8), the style
names and nogextend (AX-14) and the documented tick parts (AX-15).

The truth is test/fixtures/tick_style_truth.json
(scripts/extract_tick_style_truth.do; SVG units, 10 per point):

* ``ax5_add_custom_lab`` -- ``ylabel(25 "x", add custom labcolor(red)
  labsize(large))`` draws "x" red and large and 10 20 30 40 black at the
  axis's size; without custom (``ax5_add_plain``) every label is red.
  ``ax5_add_custom_grid`` -- a custom option's ``glcolor()`` changes no
  gridline (twoway's tickset logs no grid edit on a custom option,
  _gs_parse_and_log_tickset.ado).  ``ax5_custom_full`` -- with no add the
  custom list is the axis's labels and all four are red.  ``custom`` with
  no value list -- an empty list, an a(b)c rule, #N, minmax or none --
  and a label or tick edit is refused r(198) ``tick_styles[-1] invalid
  name``; with no edit, or only grid edits or format(), it is drawn.

Run with:  pytest test/test_tick_label_options_p9.py -q -n0
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "tick_style_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)
_SC = [P("scatter", "mpg", "weight")]
_FORMATS = {"weight": "%8.0gc", "mpg": "%8.0g"}


def _figs(mode, go, plots=None, scheme=""):
    """The first figure and every warning the build printed."""
    from conftest import render_models
    spec = tda._spec(plots or _SC, go, scheme=scheme, formats=_FORMATS)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        if mode == "saved":
            _tag, sp, dp = tda._write(spec, "auto")
            r = render_models(dr.DashRenderer(sp, dp))
            figs = tb._panels(list(r.figures.values()))
        else:
            figs = tda._figs(mode, spec)
    return figs[0], [str(x.message) for x in w]


def _ylabel_fills(row):
    """{label text: fill} of the y axis labels of a fixture row (the texts
    left of the plot region, the axis title excepted)."""
    left = row["plotregion"]["left"]
    return {t["text"]: t["fill"] for t in row["texts"]
            if t["x"] is not None and t["x"] < left
            and t["rotate"] is None}


def _grid_strokes(row, kind="hlines"):
    return sorted({ln["stroke"] for ln in row.get(kind, [])
                   if ln.get("stroke") not in (None, "#000000")})


class TestTheFixture:
    def test_meta(self):
        m = _T["_meta"]
        assert m["source"] == "scripts/extract_tick_style_truth.do"
        assert m["stata_version"] and m["dash_commit"]


@pytest.mark.parametrize("mode", _MODES)
class TestCustom:
    """AX-5: a custom option styles its own ticks only, and its grid
    edits change nothing."""

    def test_add_custom_lab(self, mode):
        fills = _ylabel_fills(_T["ax5_add_custom_lab"])
        assert fills.pop("x") == "#ff0000"
        assert set(fills.values()) == {"#000000"}, fills
        assert set(_ylabel_fills(_T["ax5_add_plain"]).values()) == \
            {"#ff0000"}
        plain, _m = _figs(mode, {})
        f, msgs = _figs(mode, {"ylabel": '25 "x", add custom '
                                         'labcolor(red) labsize(large)'})
        ax, ax0 = tda._axis(f, "y"), tda._axis(plain, "y")
        # Ruling D73: Bokeh draws one label look per axis, so dash draws
        # the custom option's edits on every label of the axis (twoway
        # styles the custom tick alone), documented and not named.
        assert ax.major_label_text_color == "#ff0000"
        assert ax.major_label_text_font_size != \
            ax0.major_label_text_font_size
        # The custom value is drawn with its text.
        assert ax.major_label_overrides.get(25.0) == "x"
        assert 25.0 in list(getattr(ax, "_dash_extra_ticks", []))
        noted = [m for m in msgs if "not implemented" in m]
        assert not [m for m in noted if "labcolor" in m
                    or "labsize" in m], msgs

    def test_grid_edit_ignored(self, mode):
        assert _grid_strokes(_T["ax5_add_custom_grid"]) == \
            _grid_strokes(_T["plain_stcolor"]) == ["#f0f0f0"]
        assert _grid_strokes(_T["ax5_empty_grid"]) == ["#f0f0f0"]
        plain, _m = _figs(mode, {})
        for go in ({"ylabel": "25, add custom labcolor(red) grid "
                              "glcolor(red)"},
                   {"ylabel": ", custom grid glcolor(red)"}):
            f, msgs = _figs(mode, go)
            assert [g.grid_line_color for g in f.ygrid] == \
                [g.grid_line_color for g in plain.ygrid], go
            assert not [m for m in msgs if "glcolor" in m], msgs

    def test_full_list_styled(self, mode):
        assert set(_ylabel_fills(_T["ax5_custom_full"]).values()) == \
            {"#ff0000"}
        f, msgs = _figs(mode, {"ylabel": "10 20 30 40, custom "
                                         "labcolor(red)"})
        assert tda._axis(f, "y").major_label_text_color == "#ff0000"
        assert not [m for m in msgs if "not implemented" in m], msgs


class TestCustomRefusalTruth:
    """The forms twoway refuses (Q4402-2 runs them through dash)."""

    def test_rows(self):
        refused = sorted(k for k in _T if k.startswith("ax5_")
                         and _T[k]["rc"])
        assert refused == sorted([
            "ax5_count_custom", "ax5_empty_angle", "ax5_empty_custom",
            "ax5_empty_nolabels", "ax5_empty_tlcolor", "ax5_minmax_custom",
            "ax5_none_custom", "ax5_rule_custom", "ax5_xlabel_empty",
            "ax5_ytick_empty"])
        for k in refused:
            assert _T[k]["rc"] == 198
            assert _T[k]["log"] == ["tick_styles[-1] invalid name"], k
        for k in ("ax5_empty_plain", "ax5_empty_grid", "ax5_empty_format"):
            assert _T[k]["rc"] == 0, k


def _vgrid_looks(row):
    """{(stroke, width, dasharray)} of a fixture row's non-black vertical
    lines: twoway's x gridlines."""
    return {(ln["stroke"], ln["width"], ln["dasharray"])
            for ln in row["vlines"] if ln["stroke"] not in (None, "#000000")}


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("scheme", ("stcolor", "s2color"))
class TestTickGrid:
    """AX-6: the gridlines of xtick() and xmtick() are drawn in the major
    gridstyle (every shipped scheme: ``gridstyle minor major``)."""

    @pytest.mark.parametrize("option", ("xtick", "xmtick"))
    def test_major_style(self, mode, scheme, option):
        assert _vgrid_looks(_T["ax6_%s_%s" % (option, scheme)]) == \
            _vgrid_looks(_T["ax6_xlabel_%s" % scheme])
        s = dr.SchemeParser(scheme)
        f, _m = _figs(mode, {option: "2500 3500, grid"}, scheme=scheme)
        gs = [g for g in f.xgrid if g.minor_grid_line_color is not None]
        assert gs, option
        for g in gs:
            assert g.minor_grid_line_color == s.grid_color
            assert g.minor_grid_line_width == s.grid_line_width
            assert list(g.minor_grid_line_dash) == \
                list(s.major_grid_dash or [])
        assert s.minor_tickset_gridstyle == "major"


def _shows_labels(ax):
    return ax.major_label_text_font_size != "0px"


def _drawn_grid(f, letter):
    return any(g.grid_line_color is not None
               for g in (f.xgrid if letter == "x" else f.ygrid))


@pytest.mark.parametrize("mode", _MODES)
class TestLabelWords:
    """AX-8: showlabels/noshowlabels are labels/nolabels, pgmgrid/nopgmgrid
    turn the grid on and off below grid/nogrid, and labelminlen() widens
    a y axis's label column, as twoway draws them, with no note."""

    def test_each(self, mode):
        # twoway: the positive label word wins within one copy, and
        # grid/nogrid are applied after pgmgrid/nopgmgrid (its tickset
        # code order, the later edit winning).
        assert not _ylabel_fills(_T["ax8_noshowlabels"])
        for k in ("ax8_showlabels", "ax8_order_a", "ax8_order_b",
                  "ax8_order_c", "ax8_order_d"):
            assert _ylabel_fills(_T[k]), k
        assert not _grid_strokes(_T["ax8_nopgmgrid"])
        assert not _grid_strokes(_T["ax8_pgmgrid"])
        assert _grid_strokes(_T["ax8_grid_nopgmgrid"])
        cases = (
            ({"ylabel": ", noshowlabels"}, False, True),
            ({"ylabel": ", showlabels"}, True, True),
            ({"ylabel": ", showlabels nolabels"}, True, True),
            ({"ylabel": ", nolabels showlabels"}, True, True),
            ({"ylabel": ", labels noshowlabels"}, True, True),
            ({"ylabel": ", noshowlabels labels"}, True, True),
            ({"ylabel": ", nopgmgrid"}, True, False),
            ({"ylabel": ", nogrid pgmgrid"}, True, False),
            ({"ylabel": ", grid nopgmgrid"}, True, True),
        )
        for go, labels, grid in cases:
            f, msgs = _figs(mode, go)
            assert _shows_labels(tda._axis(f, "y")) is labels, go
            assert _drawn_grid(f, "y") is grid, go
            assert not [m for m in msgs if "not implemented" in m], (go, msgs)
        f0, _m = _figs(mode, {})
        f, msgs = _figs(mode, {"xlabel": ", pgmgrid"})
        assert not _drawn_grid(f0, "x") and _drawn_grid(f, "x")

    def test_minlen(self, mode):
        from bokeh.models import CustomJSTickFormatter
        # twoway widens the y label column to ten characters' room
        # (510 units: 0.567 of the 112.56-unit font a character) and
        # changes no x label.
        y0 = _T["plain_stcolor"]["plotregion"]["left"]
        y1 = _T["ax8_minlen_y"]["plotregion"]["left"]
        assert (y1 - y0) / 8 / 112.56 == pytest.approx(0.567, abs=0.005)
        assert _T["ax8_minlen_x"]["plotregion"] == \
            _T["plain_stcolor"]["plotregion"]
        f, msgs = _figs(mode, {"ylabel": ", labelminlen(10)",
                               "xlabel": ", labelminlen(10)"})
        fy = tda._axis(f, "y").formatter
        assert isinstance(fy, CustomJSTickFormatter)
        assert fy.code == dr._DASH_LABEL_MINLEN_JS
        assert fy.args["n"] == 10 and fy.args["side"] == "start"
        fx = tda._axis(f, "x").formatter
        assert not (isinstance(fx, CustomJSTickFormatter)
                    and fx.code == dr._DASH_LABEL_MINLEN_JS)
        assert not [m for m in msgs if "not implemented" in m], msgs


class TestLabelMinlenJS:
    def test_minlen_pads(self):
        import js_runner
        src = (
            "const base = {doFormat: (ticks, opts) => "
            "ticks.map((t) => String(t))};\n"
            "const f = new Function('tick', 'index', 'ticks', 'base', 'n', "
            "'side', " + json.dumps(dr._DASH_LABEL_MINLEN_JS) + ");\n"
            "const ticks = [10, 2000, 123456789012];\n"
            "const a = ticks.map((t, i) => f(t, i, ticks, base, 6, 'start'));\n"
            "const b = ticks.map((t, i) => f(t, i, ticks, base, 6, 'end'));\n"
            "console.log(JSON.stringify([a, b]));\n")
        fs = chr(0x2007)
        assert js_runner.run_js(src) == [
            [fs * 4 + "10", fs * 2 + "2000", "123456789012"],
            ["10" + fs * 4, "2000" + fs * 2, "123456789012"]]


# ---------------------------------------------------------------------------
# AX-14: the style names and nogextend (and AX-8's style())
# ---------------------------------------------------------------------------

#: Stata's own style files, on the ado-path dash.ado passes (scheme_dirs).
_BASE = "/Applications/StataNow/ado/base"
_needs_base = pytest.mark.skipif(
    not os.path.isdir(os.path.join(_BASE, "style")),
    reason="Stata's style files are not here")


def _sfigs(mode, go):
    """The first figure and notes, under stcolor (the fixture's scheme)
    with Stata's style files on the ado-path, as dash.ado passes them."""
    orig = tda._spec

    def spec(*a, **k):
        s = orig(*a, **k)
        s["build_options"]["scheme_dirs"] = [_BASE]
        return s
    tda._spec = spec
    try:
        return _figs(mode, go, scheme="stcolor")
    finally:
        tda._spec = orig


def _grid_looks(row):
    """{(stroke, width)} of a fixture row's y gridlines (not the black
    axis and tick lines, unless every line is black)."""
    pr = row["plotregion"]
    ls = [ln for ln in row["hlines"] if ln["x2"] > pr["left"] + 100
          and ln["y1"] < pr["bottom"] - 1]
    return {(ln["stroke"], ln["width"]) for ln in ls}


def _note_of(row):
    """twoway's note as dash words it."""
    (line,) = row["log"]
    return "dash: " + " ".join(line.strip("()").split()).replace(
        "note: ", "", 1)


@_needs_base
@pytest.mark.parametrize("mode", _MODES)
class TestStyleNames:
    """tstyle(), labstyle(), gstyle(), tlstyle(), glstyle() and style()
    draw what their style files say (tick_style_truth.json ``ax14_*``,
    ``ax8_style_*``), with no note."""

    def test_each(self, mode):
        T0 = _T["plain_stcolor"]
        plain, _m = _sfigs(mode, {})
        ay0 = tda._axis(plain, "y")
        # major_notick: no tick, the labels half a tick nearer (twoway's
        # notickgap tiny for tickgap half_tiny: the region moves 22.6 of
        # the 45.1-unit tick).
        tick_len = T0["plotregion"]["left"] - min(
            min(ln["x1"], ln["x2"]) for ln in T0["hlines"])
        for key, go in (("ax14_tstyle_notick", "tstyle(major_notick)"),
                        ("ax8_style_notick", "style(major_vert_notick)")):
            shift = T0["plotregion"]["left"] - _T[key]["plotregion"]["left"]
            assert shift / tick_len == pytest.approx(0.5, abs=0.02), key
            f, msgs = _sfigs(mode, {"ylabel": ", " + go})
            ay = tda._axis(f, "y")
            assert ay.major_tick_out == 0 and ay.major_tick_in == 0, go
            d0 = ay0.major_tick_out + ay0.major_label_standoff
            d1 = ay.major_tick_out + ay.major_label_standoff
            assert (d0 - d1) / ay0.major_tick_out == \
                pytest.approx(0.5, abs=0.15), go
            assert not [m for m in msgs if "dash:" in m], (go, msgs)
        # major_nolabel: no labels.
        for key, go in (("ax14_tstyle_nolabel", "tstyle(major_nolabel)"),
                        ("ax8_style_nolabel", "style(major_vert_nolabel)")):
            assert not _ylabel_fills(_T[key]), key
            f, msgs = _sfigs(mode, {"ylabel": ", " + go})
            assert not _shows_labels(tda._axis(f, "y")), go
            assert not [m for m in msgs if "dash:" in m], (go, msgs)

    def test_grid_and_line_styles(self, mode):
        plain, _m = _sfigs(mode, {"ylabel": ", grid"})
        g0 = plain.ygrid[0]
        w0 = _grid_looks(_T["plain_stcolor"])
        ((_c0, wd0),) = w0
        # gstyle(dot): black dots at two thirds of the grid's width.
        ((c, wd),) = _grid_looks(_T["ax14_gstyle_dot"])
        f, msgs = _sfigs(mode, {"ylabel": ", grid gstyle(dot)"})
        g = f.ygrid[0]
        assert (c, g.grid_line_color) == ("#000000", "#000000")
        assert g.grid_line_width / g0.grid_line_width == \
            pytest.approx(wd / wd0, abs=0.01)
        assert list(g.grid_line_dash), g.grid_line_dash
        assert not [m for m in msgs if "dash:" in m], msgs
        # glstyle(refline): black, the grid's width.
        ((c, wd),) = _grid_looks(_T["ax14_glstyle_refline"])
        f, msgs = _sfigs(mode, {"ylabel": ", grid glstyle(refline)"})
        g = f.ygrid[0]
        assert (c, g.grid_line_color) == ("#000000", "#000000")
        assert g.grid_line_width == pytest.approx(g0.grid_line_width) \
            and wd == wd0
        assert not [m for m in msgs if "dash:" in m], msgs
        # tlstyle(foreground): the default tick look.
        t0, t1 = ({(ln["stroke"], ln["width"]) for ln in _T[k]["hlines"]
                   if min(ln["x1"], ln["x2"]) < _T[k]["plotregion"]["left"]
                   - 1} for k in ("plain_stcolor",
                                  "ax14_tlstyle_foreground"))
        assert t0 == t1
        f, msgs = _sfigs(mode, {"ylabel": ", tlstyle(foreground)"})
        ay, ay0 = tda._axis(f, "y"), tda._axis(plain, "y")
        assert (ay.major_tick_line_color, ay.major_tick_line_width) == \
            (ay0.major_tick_line_color, ay0.major_tick_line_width)
        assert not [m for m in msgs if "dash:" in m], msgs

    def test_labstyle(self, mode):
        plain, _m = _sfigs(mode, {})
        s0 = float(tda._axis(plain, "y").major_label_text_font_size[:-2])
        for key, name in (("ax14_labstyle_heading", "heading"),
                          ("ax14_labstyle_small_body", "small_body")):
            row = _T[key]
            labs = [t for t in row["texts"] if t["rotate"] is None
                    and t["x"] < row["plotregion"]["left"]]
            assert {t["anchor"] for t in labs} == {"middle"}
            ratio = labs[0]["size"] / 112.56
            f, msgs = _sfigs(mode, {"ylabel": ", labstyle(%s)" % name})
            ay = tda._axis(f, "y")
            s1 = float(ay.major_label_text_font_size[:-2])
            assert s1 / s0 == pytest.approx(ratio, abs=0.03), name
            assert ay.major_label_text_align == "center", name
            assert not [m for m in msgs if "dash:" in m], (name, msgs)

    def test_unknown_name_notes(self, mode):
        for key, go in (("ax14_tstyle_bogus", "tstyle(bogus)"),
                        ("ax8_style_bogus", "style(bogus)")):
            assert _T[key]["rc"] == 0
            assert _T[key]["plotregion"] == _T["plain_stcolor"]["plotregion"]
            f, msgs = _sfigs(mode, {"ylabel": ", " + go})
            assert _note_of(_T[key]) in msgs, (go, msgs)
            assert not [m for m in msgs if "not implemented" in m], msgs
            assert _shows_labels(tda._axis(f, "y"))


@pytest.mark.parametrize("mode", _MODES)
class TestNogextend:
    """nogextend ends the y gridlines at the x axis's scale: twoway draws
    them from the x data minimum (1760) to the last x tick (5000)."""

    def test_bounds(self, mode):
        row = _T["ax14_grid_nogextend"]
        lines = [ln for ln in row["hlines"] if ln["stroke"] == "#f0f0f0"]
        ticks = {t["raw"]: t["x"] for t in row["texts"]
                 if t["raw"] in ("2,000", "5,000")}
        k = 3000.0 / (ticks["5,000"] - ticks["2,000"])
        lo = 2000 + (min(ln["x1"] for ln in lines) - ticks["2,000"]) * k
        hi = 2000 + (max(ln["x2"] for ln in lines) - ticks["2,000"]) * k
        assert (lo, hi) == (pytest.approx(1760, abs=2),
                            pytest.approx(5000, abs=2))
        f, msgs = _figs(mode, {"ylabel": ", grid nogextend"})
        assert [tuple(g.cross_bounds) for g in f.ygrid] == \
            [(pytest.approx(1760), pytest.approx(5000))]
        assert not [m for m in msgs if "nogextend" in m], msgs
        f, _m = _figs(mode, {"ylabel": ", grid"})
        assert [g.cross_bounds for g in f.ygrid] == ["auto"]

    def test_js_twin(self, mode):
        import js_runner
        if mode == "served":
            # The served app re-finishes in Python (test_bounds).
            f, _m = _figs(mode, {"ylabel": ", grid nogextend"})
            assert dr._dash_nogextend_grids(f, "x") == list(f.ygrid)
            return
        src = (dr._DASH_AXIS_FINISH_JS + """
const g = {cross_bounds: "auto"};
dash_grid_nogextend({nogx: [0]}, [g], 1500, 4800);
const h = {cross_bounds: "auto"};
dash_grid_nogextend({}, [h], 1500, 4800);
console.log(JSON.stringify([g.cross_bounds, h.cross_bounds]));
""")
        assert js_runner.run_js(src) == [[1500, 4800], "auto"]


@_needs_base
class TestAxisStyleTokens:
    """SchemeParser.axis_style_tokens and the text expansion: only what a
    style name changes from the axis's default tickset, from Stata's
    files (StataNow 19.5's ado/base/style)."""

    def _sp(self, scheme="stcolor"):
        return dr.SchemeParser(scheme, ado_dirs=(_BASE,))

    def test_the_readers(self):
        sp = self._sp()
        rows = sp._axis_rows("tickstyle", "major_notick")
        assert rows["show_ticks"] == ("literal", "no")
        assert rows["textgap"] == ("scheme", "notickgap")
        assert sp._axis_rows("tickstyle", "bogus") is None
        # s2color's gsize notickgap tiny, read from Stata's own scheme.
        assert sp._axis_leaf("gsize", "notickgap") == "tiny"
        assert sp._axis_val(rows, "textgap", "gsize") == "tiny"
        assert sp._axis_val(rows, "show_ticks", "yesno") == "no"
        # A style hop: the file of that name.
        assert sp._axis_val({"x": ("scheme", "major_nolabel")}, "x",
                            "tickstyle", hop=True) == "major_nolabel"

    def test_each_class(self):
        sp = self._sp()
        assert sp._axis_tick_tokens("major_notick", "default") == \
            ["noticks", "labgap(tiny)"]
        assert sp._axis_tick_tokens("minor", "default") == \
            ["tlength(half_tiny)"]
        assert sp._axis_grid_tokens("dot", "major") == \
            ["glwidth(thin)", "glcolor(#000000)", "glpattern(dot)"]
        assert sp._axis_line_tokens("foreground", "tick", "tl") == []
        assert sp._axis_line_tokens("bogus", "tick", "tl") is None
        assert sp._axis_text_tokens("heading", "tick_label") == \
            ["labsize(large)", "labjustification(center)"]
        assert sp._axis_text_tokens("bogus", "tick_label") is None
        assert sp.axis_style_tokens("style", "major_vert_nolabel") == \
            ["nolabels"]
        assert sp.axis_style_tokens("style", "major_vert_default") == []
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._DASH_NOTED.discard(("named-style", "textstyle", "zq1"))
            assert sp.axis_style_tokens("labstyle", "zq1") == []
            assert sp.axis_style_tokens("tlstyle", "zq1",
                                        note=False) == []
        assert [str(x.message) for x in w] == [
            "dash: named style zq1 not found in class textstyle, default "
            "attributes used"]

    def test_the_text(self):
        sp = self._sp()
        assert dr._dash_axis_style_text(", tstyle(major_notick) noticks",
                                        sp) == \
            ", noticks labgap(tiny) tstyle(major_notick) noticks"
        # The minimum abbreviations, gs() and gls(); a tick option takes
        # no label edit.
        assert dr._dash_axis_style_text("10 20, gs(dot)", sp) == \
            "10 20, glwidth(thin) glcolor(#000000) glpattern(dot) gs(dot)"
        assert dr._dash_axis_style_text(", tsty(major_notick)", sp,
                                        tick=True) == \
            ", noticks tsty(major_notick)"
        assert dr._dash_axis_style_text(", grid", sp) == ", grid"
        go = {"ylabel": ", grid", "name": "g"}
        assert dr._dash_axis_styles_expand(go, sp) is go
        go2 = {"ylabel": ", tstyle(major_nolabel)",
               "axisn": {"y3": {"label": ", style(major_vert_notick)"}}}
        got = dr._dash_axis_styles_expand(go2, sp)
        assert got is not go2 and go2["ylabel"] == ", tstyle(major_nolabel)"
        assert got["ylabel"] == ", nolabels tstyle(major_nolabel)"
        assert got["axisn"]["y3"]["label"] == \
            ", noticks labgap(tiny) style(major_vert_notick)"


# ---------------------------------------------------------------------------
# AX-15: the hexadecimal, IEEE-byte and string axis formats
# ---------------------------------------------------------------------------

#: The fixture's ax15_fmtl_* lists (scripts/extract_tick_style_truth.do):
#: ``twoway scatteri 0 0 1 1, ylabel(<list>, format(<f>))``, written in
#: the list's order.
_LX = [0, 0.1, -0.5, 10, 33.3333333, 65536, 1e-310, 1e20, -2.5e-8]
_LS = [0, 0.1, -0.5, 10, 33.3333333, 1234567.891, 1234567890, -123456789,
       0.000012345, 123456789012]
_FMT_LISTS = (("x21", "%21x", _LX), ("xl", "%-21x", _LX),
              ("h16", "%16H", _LX), ("h8", "%8H", _LX),
              ("l16", "%16L", _LX), ("l8", "%8L", _LX),
              ("hl", "%-16H", _LX), ("s", "%12s", _LS), ("sl", "%-5s", _LS))
#: ``scatter mpg weight, ylabel(, format(<f>))``: its labels 10 20 30 40.
_FMT_AXES = (("ax15_fmt_x", "%21x"), ("ax15_fmt_hexhi", "%16H"),
             ("ax15_fmt_s", "%12s"))


def _ylabel_texts(row):
    """The y axis label texts of a fixture row, in the order written."""
    left = row["plotregion"]["left"]
    return [t["text"] for t in row["texts"]
            if t["x"] is not None and t["x"] < left and t["rotate"] is None]


class TestFormats:

    def test_the_writer(self):
        for key, fmt, vals in _FMT_LISTS:
            want = _ylabel_texts(_T["ax15_fmtl_" + key])
            assert [dr._dash_fmt_text(v, fmt) for v in vals] == want, fmt
        # twoway refuses the other widths (r(198) "invalid format, %10x"),
        # which the writer does not claim.
        for key, fmt in (("bad10x", "%10x"), ("bad12h", "%12H")):
            row = _T["ax15_fmtl_" + key]
            assert row["rc"] == 198
            assert row["log"] == ["invalid format, " + fmt]
            assert not dr._dash_fmt_dump_writes(fmt)

    def test_the_js_twin(self):
        import js_runner
        cases = [[fmt, vals] for _k, fmt, vals in _FMT_LISTS]
        got = js_runner.run_js(
            dr._DASH_FMT_JS + "\nconst c = %s;\n"
            "process.stdout.write(JSON.stringify(c.map((x) => x[1].map("
            "(v) => dash_fmt_text(v, x[0])))));" % json.dumps(cases))
        assert got == [_ylabel_texts(_T["ax15_fmtl_" + k])
                       for k, _f, _v in _FMT_LISTS]

    @pytest.mark.parametrize("mode", _MODES)
    def test_axis(self, mode):
        for key, fmt in _FMT_AXES:
            row = _T[key]
            f, msgs = _figs(mode, {"ylabel": ", format(%s)" % fmt})
            fm = tda._axis(f, "y").formatter
            assert fm.args["fmt"] == fmt, (key, fm.args)
            got = [dr._dash_fmt_text(v, fm.args["fmt"])
                   for v in (10, 20, 30, 40)]
            assert got == _ylabel_texts(row), key
            assert not [m for m in msgs if "format(" in m], msgs


# ---------------------------------------------------------------------------
# AX-15: xtick() and xmtick() at their own lengths
# ---------------------------------------------------------------------------

_TICK_STUBS_JS = r"""
function build(d) {
    if (d && d.kind === "fixed")
        return {ticks: d.ticks, get_ticks() {
            return {major: d.ticks.slice(), minor: []}; }};
    if (d && d.kind === "cjs") {
        const args = {};
        for (const k of Object.keys(d.args)) args[k] = build(d.args[k]);
        const o = {args: args};
        o.get_ticks = (s, e, r, c) => {
            const cb = {start: s, end: e, range: r, cross_loc: c};
            const names = Object.keys(args), vals = names.map((n) => args[n]);
            const maj = new Function("cb_data", ...names, d.major)(cb, ...vals);
            const mn = new Function("cb_data", ...names, d.minor)(
                Object.assign({major_ticks: maj}, cb), ...vals);
            return {major: maj, minor: mn};
        };
        return o;
    }
    if (d && d.kind === "text")
        return {doFormat: (ts) => ts.map((t) => String(t))};
    return d;
}
"""


def _stub(m):
    """A model as the node stubs above build it: FixedTicker and
    CustomJSTicker by their ticks and code, a formatter as String()."""
    from bokeh.models import CustomJSTicker, FixedTicker, TickFormatter
    if isinstance(m, FixedTicker):
        return {"kind": "fixed", "ticks": [float(v) for v in m.ticks]}
    if isinstance(m, CustomJSTicker):
        return {"kind": "cjs", "major": m.major_code, "minor": m.minor_code,
                "args": {k: _stub(v) for k, v in dict(m.args).items()}}
    if isinstance(m, TickFormatter):
        return {"kind": "text"}
    return m


def _drawn_ticks(f, letter):
    """``(majors, minors, labels)`` the axis draws over its range: its
    ticker's code and its formatter's code run under node (labels: the
    position's text, "" where none is written)."""
    import js_runner
    ax = tda._axis(f, letter)
    rng = f.x_range if letter == "x" else f.y_range
    fm = ax.formatter
    fdesc = {"code": getattr(fm, "code", ""),
             "args": {k: _stub(v) for k, v in dict(
                 getattr(fm, "args", None) or {}).items()}}
    src = (_TICK_STUBS_JS
           + "const t = build(%s); const fd = %s;\n"
             "const r = t.get_ticks(%r, %r, null, null);\n"
             "const lo = Math.min(%r, %r), hi = Math.max(%r, %r);\n"
             "const maj = r.major.filter((v) => v >= lo && v <= hi);\n"
             "const names = Object.keys(fd.args);\n"
             "const vals = names.map((n) => build(fd.args[n]));\n"
             "let labs = maj.map(String);\n"
             "if (fd.code) { const fn = new Function('tick', 'index', "
             "'ticks', ...names, fd.code).bind({});\n"
             "  labs = maj.map((v, i) => String(fn(v, i, maj, ...vals))); }\n"
             "console.log(JSON.stringify([maj, r.minor, labs]));\n") % (
        json.dumps(_stub(ax.ticker)), json.dumps(fdesc),
        rng.start, rng.end, rng.start, rng.end, rng.start, rng.end)
    return js_runner.run_js(src)


def _tw_tick_lengths(row, letter, values):
    """twoway's tick length at each of *values* (sorted along the axis
    against the ticks it draws outside the plot region)."""
    pr = row["plotregion"]
    if letter == "x":
        ts = sorted((ln["x1"], abs(ln["y2"] - ln["y1"]))
                    for ln in row["vlines"]
                    if min(ln["y1"], ln["y2"]) >= pr["bottom"] - 1)
    else:
        ts = sorted(((ln["y1"], abs(ln["x2"] - ln["x1"]))
                     for ln in row["hlines"]
                     if max(ln["x1"], ln["x2"]) <= pr["left"] + 1),
                    reverse=True)
    assert len(ts) == len(values), ts
    return dict(zip(sorted(values), [round(n, 2) for _p, n in ts]))


class TestTickLengths:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("letter,only,minor", [
        ("x", [2500.0, 4500.0], [3500.0]), ("y", [15.0, 25.0], [35.0])])
    def test_two_lengths(self, mode, letter, only, minor):
        row = _T["ax15_ticklens_" + letter]
        labels = ([2000.0, 3000.0, 4000.0, 5000.0] if letter == "x"
                  else [10.0, 20.0, 30.0, 40.0])
        tw = _tw_tick_lengths(row, letter, labels + only + minor)
        long_ = tw[labels[0]]
        # twoway: the xtick() positions as long as a labelled tick, the
        # xmtick() one half as long, and only the label positions written.
        assert all(tw[v] == long_ for v in labels + only)
        assert all(abs(tw[v] / long_ - 0.5) < 0.02 for v in minor)
        assert len(_ylabel_texts(row)) == 4
        go = {letter + "tick": " ".join("%g" % v for v in only),
              letter + "mtick": " ".join("%g" % v for v in minor)}
        f, _msgs = _figs(mode, go)
        ax = tda._axis(f, letter)
        maj, mnr, labs = _drawn_ticks(f, letter)
        assert sorted(maj) == sorted(labels + only)
        assert sorted(mnr) == minor
        written = sorted(v for v, s in zip(maj, labs) if s)
        assert written == labels
        sp = dr.SchemeParser("stcolor")
        assert ax.major_tick_out == int(round(sp.tick_length_px))
        assert ax.minor_tick_out == int(round(sp.minortick_length_px))
        assert sp.minortick_length_px / sp.tick_length_px == \
            pytest.approx(tw[minor[0]] / long_, abs=0.02)
        # The gridlines stay at the labels: twoway draws none at the tick
        # positions (no grid sub-option).
        pr = row["plotregion"]
        if letter == "x":
            gl = {round(ln["x1"]) for ln in row["vlines"]
                  if ln["stroke"] not in (None, "#000000")
                  and max(ln["y1"], ln["y2"]) < pr["bottom"] - 1}
        else:
            gl = {round(ln["y1"]) for ln in row["hlines"]
                  if ln["stroke"] not in (None, "#000000")
                  and min(ln["x1"], ln["x2"]) > pr["left"] + 1}
        assert len(gl) == len(labels)
        import js_runner
        from bokeh.models import Grid
        g = [m for m in f.renderers + f.center if isinstance(m, Grid)
             and m.dimension == (0 if letter == "x" else 1)]
        rng = f.x_range if letter == "x" else f.y_range
        for m in g:
            if m.ticker is None:
                continue
            gmaj = js_runner.run_js(
                _TICK_STUBS_JS + "console.log(JSON.stringify(build(%s)"
                ".get_ticks(%r, %r, null, null).major));"
                % (json.dumps(_stub(m.ticker)), rng.start, rng.end))
            lo, hi = sorted((rng.start, rng.end))
            assert sorted(v for v in gmaj if lo <= v <= hi) == labels


class TestDocumentedDifferences:
    """Rulings D73 and D74: AX-5's add-custom look and AX-15's margin
    reference lines and resize margin are Differences from twoway items
    17-19, each led to from the paragraph that draws it."""

    _ITEMS = (
        ("add_custom", "17", "custom with add styles every label of the "
                             "axis."),
        ("margin_reflines", "18", "Reference lines outside the axis's "
                                  "range are not drawn."),
        ("resize_margin", "19", "The plot-region margin is fixed when the "
                                "page is built."))

    def test_items(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        diff = text[text.index("{title:Differences from twoway}"):
                    # Item 21 since WP-44 44-03 added item 20.
                    text.index("{phang2}21.  {ul:Resource limits.}")]
        for marker, num, head in self._ITEMS:
            item = "{marker %s}{...}\n{phang2}%s.  {ul:%s}" % (
                marker, num, head)
            assert item in diff, marker
            # Led to from outside the Differences list.
            rest = text.replace(diff, "")
            assert "{help dash##%s:item %s}" % (marker, num) in rest, marker
