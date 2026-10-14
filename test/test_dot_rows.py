"""
test_dot_rows.py -- twoway dot's rows of dots, dotextend(), ndots() and the
d-options (WP-31 B5b; GAPS3 B5's rows-and-options half, section 18).

The defect (measured at 8dde8ee): ``dash dot mpg weight`` drew map_scatter's
markers and nothing else; dotextend() and ndots() were not declared, the
d-options fell to the generic note and dstyle()/dlstyle() were named.

twoway (StataNow 19.5, scripts/extract_dot_truth.do, fixture
test/fixtures/dot_truth.json): for every observation a row of dots, drawn
before the marker, from the axis's base (0 when the scale holds it, else the
end nearer 0) down to the scale's curmin and up to its curmax -- or to the
value under dotextend(no) -- in steps of (curmax - curmin) / (ndots - 1),
ndots 75, as Stata's forvalues steps them (the step added to the last dot,
so round-off may leave the end out: 74 distinct dots over 14..22, 75 over
14..50).  Vertical rows at each x (bar_drop_to x); horizontal ones under
horizontal.  The dots are markerstyle dots (a vtiny black circle, outline
linestyle dotmark, thin and black; white under s1rcolor) and only the
d-options restyle them: color(), mcolor(), msymbol(), pstyle() and mstyle()
leave them black, and so does colorvar() (D09, D23-D26).  ndots() takes any
number and refuses anything else; dotextend() takes anything, lowercase no,
n, off and false meaning no; both are refused on types other than dot,
area, bar, spike and dropline; baroffset() on dot moves nothing (D28, D29);
dlalign() moves the outline (D30), which Bokeh cannot do, so it is named.
"""
import json
import os
import re
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure as bk_figure

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
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "dot_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
#: auto in 1/5: the rows the fixture's graphs draw.
_AUTO5 = pd.DataFrame({"mpg": [22.0, 17.0, 22.0, 20.0, 15.0],
                       "weight": [2930.0, 3350.0, 2640.0, 3250.0, 4080.0]})
#: The SVG's y of curmin and curmax on the fixture's canvas (D17: ndots(2)
#: draws exactly the two ends).
_PX_LO, _PX_HI = 2425.82, 164.22


def _px(v, lo, hi):
    return _PX_LO - (v - lo) * (_PX_LO - _PX_HI) / (hi - lo)


def _fig(mode, tmp_path, o=None, df=None, scheme=None, plot=None):
    p = plot or {"type": "dot", "yvar": "mpg", "xvar": "weight",
                 "options": dict(o or {})}
    bo = {"scheme": scheme} if scheme else None
    figs, notes = bg._figs(mode, tmp_path, bg._spec([p], bo=bo),
                           _AUTO5 if df is None else df)
    return figs[0], notes


def _is_dots(r):
    return "dash_dots" in (getattr(r, "tags", None) or ())


def _dots(f):
    [r] = [r for r in f.renderers if _is_dots(r)]
    return r


def _marker(f):
    [r] = [r for r in f.renderers if not _is_dots(r)
           and not dr._dash_is_swatch(r)
           and type(getattr(r, "glyph", None)).__name__ == "Scatter"]
    return r


def _runs(r):
    """{the observation's position: its dots along the row, sorted}."""
    d = r.data_source.data
    out: dict = {}
    for x, y in zip(d["x"], d["y"]):
        out.setdefault(float(x), []).append(float(y))
    return {k: sorted(v) for k, v in out.items()}


def _fixture_counts(key):
    """The fixture's dots per run, in the order of the runs' screen
    position (which is the order of weight)."""
    runs = _T[key]["dot_runs"]
    return [len(runs[k]) for k in sorted(runs, key=float)]


def _dots_by_weight(f):
    rr = _runs(_dots(f))
    return [len(rr[w]) for w in sorted(rr)]


class TestTheFixture:

    def test_twoways_class_values(self):
        assert _T["D01"]["num_dots"] == 75
        assert _T["D01"]["dots_extend"] == "1"
        assert _T["D02"]["dots_extend"] == "0"
        assert _T["D03"]["num_dots"] == 10
        assert _T["D01"]["bar_drop_to"] == "x" and _T["D01"]["along"] == "y"
        assert _T["D06"]["bar_drop_to"] == "y" and _T["D06"]["along"] == "x"
        assert _T["D01"]["yscale"] == [14.0, 22.0]

    def test_the_refusals_and_spellings(self):
        p = _T["probes"]
        assert (p["D11d"]["rc"], p["D11d"]["message"]) == (
            198, "option ndots() not allowed")
        assert (p["D11g"]["rc"], p["D11g"]["message"]) == (
            198, "option ndots() incorrectly specified")
        assert (p["D11l"]["rc"], p["D11l"]["message"]) == (
            198, "option dotextend() not allowed")
        no = {k for k in ("D05", "D05b", "D05c", "D05d", "D05e", "D05f",
                          "D05g", "D05h", "D05i", "D05j")
              if p[k]["class"][1] == "0"}
        assert no == {"D05d", "D05i", "D05j"}       # n, off, false
        for k in ("D11", "D11b", "D11e", "D11f", "D11h", "D11i", "D11j",
                  "D11n", "D11o", "D11p", "D11q", "D11r", "D11s", "D11t"):
            assert p[k]["rc"] == 0, k


class TestShape:

    def test_map_dot_returns_dots_then_marker(self):
        gm = bg._gm()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [14.0, 22.0]})
        f = bk_figure()
        rs = gm.map_dot(f, src, "y", "x", {})
        assert len(rs) == 2 and _is_dots(rs[0]) and not _is_dots(rs[1])
        assert f.renderers.index(rs[0]) < f.renderers.index(rs[1])
        # Filled at once over the layer's own values, 14..22.
        assert set(_runs(rs[0])) == {1.0, 2.0}

    @pytest.mark.parametrize("mode", _MODES)
    def test_two_renderers(self, mode, tmp_path):
        f, notes = _fig(mode, tmp_path)
        d, m = _dots(f), _marker(f)
        assert f.renderers.index(d) < f.renderers.index(m)
        assert type(d.glyph).__name__ == "Scatter"
        assert not [n for n in notes if "dot" in n.lower()], notes

    @pytest.mark.parametrize("mode", _MODES)
    def test_order_and_tags(self, mode, tmp_path):
        """No key, no tooltip, no part of the axis hull."""
        f, _ = _fig(mode, tmp_path)
        d = _dots(f)
        for lg in f.legend:
            for it in lg.items:
                assert d not in it.renderers
        for t in f.tools:
            if isinstance(t, HoverTool):
                assert d not in (t.renderers if isinstance(t.renderers, list)
                                 else [])
        assert dr._dash_layer_extent([d], "y_range_name", "default") is None


class TestGeometry:

    @pytest.mark.parametrize("key", ["D01", "D03", "D10", "D17"])
    def test_positions_match_twoway(self, key):
        """Every run of the fixture's graph, dot for dot, within 0.25 px (Stata's SVG rounds
        each point to its device grid)."""
        t = _T[key]
        lo, hi = t["yscale"]
        pos, rows, nd = dr.GlyphMapper._dot_positions(
            lo, hi, _AUTO5["mpg"].to_numpy(), True, t["num_dots"])
        assert nd == t["num_dots"]
        for i in range(len(_AUTO5)):
            mine = sorted(_px(v, lo, hi) for v in pos[rows == i])
            for run in t["dot_runs"].values():
                assert len(run) == len(mine), (key, run, mine)
                assert np.allclose(sorted(run), sorted(mine), atol=0.25)

    @pytest.mark.parametrize("key", ["D02", "D22"])
    def test_to_the_value(self, key):
        t = _T[key]
        lo, hi = t["yscale"]
        order = np.argsort(_AUTO5["weight"].to_numpy())
        pos, rows, _ = dr.GlyphMapper._dot_positions(
            lo, hi, _AUTO5["mpg"].to_numpy(), False, t["num_dots"])
        runs = [t["dot_runs"][k] for k in sorted(t["dot_runs"], key=float)]
        for i, run in zip(order, runs):
            mine = sorted(_px(v, lo, hi) for v in pos[rows == i])
            assert np.allclose(sorted(run), mine, atol=0.25), (key, i)

    @pytest.mark.parametrize("lo,hi,base", [(14, 22, 14), (-5, 10, 0),
                                            (-20, -3, -3)])
    def test_base_rule(self, lo, hi, base):
        pos, rows, _ = dr.GlyphMapper._dot_positions(lo, hi, [lo, hi], True)
        for i in (0, 1):
            run = pos[rows == i]
            assert run[0] == base
            assert run.min() >= lo - 1e-9 and run.max() <= hi + 1e-9

    @pytest.mark.parametrize("key,nd", [("D04", 1), ("D04b", 0),
                                        ("D04c", 2.5), ("D04d", -3),
                                        ("D04e", 20000), ("D11v", 1000)])
    def test_odd_ndots(self, key, nd):
        """twoway's dots under each ndots(): two circles a dot and ten for
        the five markers."""
        want = (_T["probes"][key]["n_circles"] - 10) // 2
        pos, _, _ = dr.GlyphMapper._dot_positions(
            14, 22, _AUTO5["mpg"].to_numpy(), True, nd)
        assert len(pos) == want, (key, len(pos), want)

    def test_a_missing_value_draws_no_row(self):
        pos, rows, _ = dr.GlyphMapper._dot_positions(
            0, 1, [0.5, np.nan], False)
        assert set(rows.tolist()) == {0}

    def test_the_cap(self):
        vals = np.full(100_000, 0.5)
        pos, _, nd = dr.GlyphMapper._dot_positions(0, 1, vals, True, 75,
                                                   limit=2_000_000)
        assert len(pos) <= 2_000_000 and 2 <= nd < 75
        assert dr._DASH_DOTS_MAX == 2_000_000

    @pytest.mark.parametrize("mode", _MODES)
    def test_scale_from_the_axis(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path)
        assert dr._dash_axis_scale(f, "y") == tuple(_T["D01"]["yscale"])
        assert _dots_by_weight(f) == _fixture_counts("D01")
        lo, hi = _T["D01"]["yscale"]
        for run in _runs(_dots(f)).values():
            assert np.allclose(sorted(_px(v, lo, hi) for v in run),
                               _T["D01"]["dot_runs"]["750.17"], atol=0.25)

    @pytest.mark.parametrize("mode", _MODES)
    def test_extend_no(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path, {"dotextend": "no"})
        assert _dots_by_weight(f) == _fixture_counts("D02")

    @pytest.mark.parametrize("mode", _MODES)
    def test_ndots(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path, {"ndots": "10"})
        assert _dots_by_weight(f) == _fixture_counts("D03")
        f, _ = _fig(mode, tmp_path, {"ndots": "10", "dotextend": "no"})
        assert _dots_by_weight(f) == _fixture_counts("D22")

    @pytest.mark.parametrize("mode", _MODES)
    def test_horizontal(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path, {"horizontal": "horizontal",
                                     "dotextend": "no"})
        d = _dots(f)
        assert dr._dash_spec_field(d.glyph.x) == "y"     # rows along x
        assert dr._dash_axis_scale(f, "x") == tuple(_T["D16"]["xscale"])
        # D16's runs are keyed by their y, which runs down the screen
        # as weight runs up.
        assert _dots_by_weight(f) == _fixture_counts("D16")[::-1]


class TestStyle:

    @pytest.mark.parametrize("mode", _MODES)
    def test_scheme_defaults(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path)
        g = _dots(f).glyph
        assert g.marker == "circle"
        assert g.size == 1.0          # vtiny, 0.384 px, drawn at 1 px
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("thin"))
        assert (str(g.fill_color).lower(), str(g.line_color).lower()) == (
            "#000000", "#000000")
        f, _ = _fig(mode, tmp_path, scheme="s1rcolor")
        assert str(_dots(f).glyph.line_color).lower() == \
            _T["D18"]["dot_stroke"][0]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("opt,val,attr,want", [
        ("dcolor", "red", "fill_color", "#ff0000"),
        ("dcolor", "red", "line_color", "#ff0000"),
        ("dfcolor", "red", "fill_color", "#ff0000"),
        ("dfcolor", "red", "line_color", "#000000"),
        ("dlcolor", "blue", "line_color", "#0000ff"),
        ("dsymbol", "square", "marker", "square"),
    ])
    def test_d_option(self, mode, tmp_path, opt, val, attr, want):
        """D14, D15, D07."""
        f, notes = _fig(mode, tmp_path, {opt: val})
        assert str(getattr(_dots(f).glyph, attr)).lower() == want
        assert not [n for n in notes if opt in n], notes

    @pytest.mark.parametrize("mode", _MODES)
    def test_d_sizes(self, mode, tmp_path):
        """dsize(medium) is the marker's medium (D12); dlwidth(thick)."""
        f, _ = _fig(mode, tmp_path, {"dsize": "medium", "dlwidth": "thick"})
        g = _dots(f).glyph
        assert g.size == pytest.approx(_marker(f).glyph.size)
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("thick"))

    @pytest.mark.parametrize("mode", _MODES)
    def test_dstyle(self, mode, tmp_path):
        """dstyle(p3): p3's marker, p3's colour and size (D08)."""
        f, _ = _fig(mode, tmp_path, {"dstyle": "p3"})
        g = _dots(f).glyph
        assert str(g.fill_color).lower() == "#55752f"
        assert _T["D08"]["dot_stroke"] == ["#1a476f", "#55752f"]
        assert g.size == pytest.approx(_marker(f).glyph.size)
        f, _ = _fig(mode, tmp_path, {"dlstyle": "p3"})
        assert str(_dots(f).glyph.line_color).lower() == "#55752f"

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("o", [{"color": "red"}, {"mcolor": "red"},
                                   {"pstyle": "p3"}, {"mstyle": "p3"}],
                             ids=["color", "mcolor", "pstyle", "mstyle"])
    def test_no_marker_option_reaches_the_dots(self, mode, tmp_path, o):
        """D23-D26: the dots stay black."""
        f, _ = _fig(mode, tmp_path, o)
        g = _dots(f).glyph
        assert (str(g.fill_color).lower(), str(g.line_color).lower()) == (
            "#000000", "#000000")

    def test_unknown_names_are_noted_as_d_options(self, tmp_path):
        f, notes = _fig("saved", tmp_path, {"dsize": "bogus",
                                            "dcolor": "bogus"})
        g = _dots(f).glyph
        assert g.size == 1.0 and str(g.fill_color).lower() == "#000000"
        assert any("dsize(bogus)" in n for n in notes), notes
        assert any("dcolor(bogus)" in n for n in notes), notes
        assert not [n for n in notes if "msize(" in n or "mcolor(" in n]


class TestColorvar:

    @pytest.mark.parametrize("mode", _MODES)
    def test_dots_take_the_mapping(self, mode, tmp_path):
        """twoway colours the markers, not the dots (D09): the dots keep
        their style; the marker is coloured as S15 colours it."""
        df = _AUTO5.assign(rep=[3.0, 3.0, 4.0, 3.0, 4.0])
        f, _ = _fig(mode, tmp_path, {"colorvar": "rep",
                                     "colordiscrete": "colordiscrete"},
                    df=df)
        g = _dots(f).glyph
        assert str(g.fill_color).lower() == "#000000"
        assert _T["D09"]["dot_stroke"] == ["#000000"]
        assert not isinstance(_marker(f).glyph.fill_color, str)


class TestBrushIgnoresDots:

    @pytest.mark.parametrize("mode", _MODES)
    def test(self, mode, tmp_path):
        """The dots carry no data column a card reads, and no served
        frame label, so no brush reaches them; they are no part of the
        axis hull."""
        f, _ = _fig(mode, tmp_path)
        d = _dots(f)
        assert set(d.data_source.data) <= {"x", "y", dr._ROW_ID_COLUMN}
        assert "index" not in d.data_source.data
        assert dr._dash_secondary_values(f, "y_range_name",
                                         "default") is not None


def _move_spec():
    return tp._spec([plot_for("dot")], {"filter": sf._MOVES[0][1]})


def _dots_after(mode):
    label, _f, action, oracle = sf._MOVES[0]
    after = hm._moved(_move_spec(), action, mode)
    kept = hm._kept(_move_spec(), oracle, mode)
    return ([dict(_dots(f).data_source.data) for f in after],
            [dict(_dots(f).data_source.data) for f in kept])


class TestAfterAServedMove:

    def test_span_follows_axis(self):
        """The served re-finish (_dash_refinish_axes ->
        _dash_finish_count_ticks -> _dash_finish_auto_bases) rebuilds the
        rows over the kept rows' axis: what the kept rows' own build
        draws."""
        after, kept = _dots_after("served")
        for a, k in zip(after, kept):
            assert np.allclose(a["y"], k["y"]) and list(a["x"]) == list(
                k["x"])


class TestAfterASavedMove:

    @requires_node
    @pytest.mark.xfail(strict=True, reason=(
        "WP-31 B5b residual: the saved page keeps each kept observation's "
        "row where the build drew it; rebuilding it over the re-finished "
        "axis is the saved page's JavaScript (S22's slot)"))
    def test_measured(self):
        after, kept = _dots_after("saved")
        for a, k in zip(after, kept):
            assert len(a["y"]) == len(k["y"])
            assert np.allclose(a["y"], k["y"])

    @requires_node
    def test_the_kept_rows_keep_their_dots(self):
        """What the saved page does draw: the kept observations' rows, no
        other's (the dots carry the row identity the callback keeps)."""
        after, kept = _dots_after("saved")
        for a, k in zip(after, kept):
            assert set(a["x"]) == set(k["x"])


class TestTheServedCopy:

    def test_constant(self, tmp_path):
        import test_served_linked_views as tlv
        sp, dp = tlv._write_inputs(tmp_path, _move_spec())
        app = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        assert re.search(r"^_DASH_DOTS_MAX = 2000000$", src, re.M)
        assert "def _dot_positions" in src and "def dots_style" in src


class TestTheAdoText:

    _NINE = ("dotextend", "ndots", "dsymbol", "dcolor", "dfcolor", "dsize",
             "dlcolor", "dlwidth", "dlalign")

    def test_declared(self):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        for decl in ("DOTEXtend(string)", "NDOTs(string)",
                     "Dsymbol(string asis)", "DColor(string asis)",
                     "DFColor(string asis)", "DSIZe(string asis)",
                     "DLColor(string asis)", "DLWidth(string asis)",
                     "DLAlign(string asis)"):
            assert ado.count(decl) == 1, decl
        for o in self._NINE:
            assert re.search(r"sreturn local %s\s+: copy local %s" % (o, o),
                             ado), o
        assert "dotextend ndots dsymbol dcolor dfcolor dsize dlcolor " \
               "dlwidth dlalign ///" in ado
        pend = re.findall(r"local _dash_pending `\"`_dash_pending' (\w+)\"'",
                          ado)
        assert "dlalign" in pend
        assert "dstyle" not in pend and "dlstyle" not in pend
        assert "ndots@area|bar|spike|dropline|dot" in ado
        # p() drops the d-options, as twoway's p(p3) dcolor(red) draws
        # black dots (D27).
        assert "`_dash_p_drops' dsymbol dcolor dfcolor dsize dlcolor " \
               "dlwidth\"" in ado
        assert _T["D27"]["dot_stroke"] == ["#000000"]
        assert 'display as error "option ndots() incorrectly specified"' \
            in ado


class TestJitter:
    """twoway's jitter() moves dot's markers and leaves its rows of dots on
    the data: under jitter(5) jitterseed(1) the runs keep D01's screen x
    and every marker leaves its run (dot_truth.json D31).  dash drew the
    rows through the jittered marker columns (measured at c377e9b)."""

    def test_the_fixture(self):
        runs = sorted(float(k) for k in _T["D31"]["dot_runs"])
        assert runs == sorted(float(k) for k in _T["D01"]["dot_runs"])
        off = {tuple(c) for c in _T["D31"]["marker_centres"]
               if min(abs(c[0] - r) for r in runs) > 0.2}
        assert len(off) == 5

    @pytest.mark.parametrize("mode", _MODES)
    def test_rows_stay_on_the_data(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path, {"jitter": "5", "jitterseed": "1"})
        assert set(_runs(_dots(f))) == set(_AUTO5["weight"])
        m = _marker(f)
        xs = m.data_source.data[dr._dash_spec_field(m.glyph.x)]
        assert not set(float(v) for v in xs) & set(_AUTO5["weight"])

    @pytest.mark.parametrize("mode", _MODES)
    def test_horizontal_rows_stay_on_the_data(self, mode, tmp_path):
        f, _ = _fig(mode, tmp_path, {"jitter": "5", "jitterseed": "1",
                                     "horizontal": "horizontal"})
        assert set(_runs(_dots(f))) == set(_AUTO5["weight"])
        lo, hi = dr._dash_axis_scale(f, "x")
        for run in _runs(_dots(f)).values():
            assert min(run) >= lo - 1e-9 and max(run) <= hi + 1e-9
