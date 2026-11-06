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
        # The other labels keep the axis's look, as twoway draws them.
        assert ax.major_label_text_color == ax0.major_label_text_color
        assert ax.major_label_text_font_size == \
            ax0.major_label_text_font_size
        # The custom value is drawn with its text.
        assert ax.major_label_overrides.get(25.0) == "x"
        assert 25.0 in list(getattr(ax, "_dash_extra_ticks", []))
        # Its own look is not drawn on that tick alone, so it is named.
        noted = [m for m in msgs if "not implemented" in m]
        assert any("labcolor(red)" in m and "labsize(large)" in m
                   for m in noted), msgs

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
