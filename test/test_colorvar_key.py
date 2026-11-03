"""
test_colorvar_key.py -- dash draws the colour key twoway draws (WP-42
section 42-03).

CV-8a (D68): under by() a contour's colour key is a by() colour key.
twoway draws no key under ``by(date)`` and one key beside the panels
under ``by(date, clegend(on))`` (sysuse surface, ``contour temperature
latitude longitude, levels(10)``; graph export SVG, 02nov2026: by(date)
has no key text right of the panels; by(date, clegend(on)) one key at the
right ticked 4.81 to 17.69, titled "Sea surface temperature (Deg. C)";
by(date, clegend(on pos(6))) the same key below the panels).  dash kept
every panel's ContourColorBar: ``_dash_by_keys`` collected only
``ColorBar``, of which ``ContourColorBar`` is not a subclass.
test_wp42_truth.cscript block S03 CV-8a measures it live.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tbk  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json  # noqa: E402

_MODES = ("saved", "served")


def _surface():
    """A two-date surface: z = x + y on a 6 x 6 grid, each date its own
    offset (sysuse surface's shape, small)."""
    xs, ys = np.meshgrid(np.arange(6.0), np.arange(6.0))
    rows = []
    for d, off in ((1.0, 0.0), (2.0, 3.0)):
        for x, y in zip(xs.ravel(), ys.ravel()):
            rows.append({"date": d, "lon": x, "lat": y, "temp": x + y + off})
    return pd.DataFrame(rows)


def _contour_bars(model):
    sides = ("left", "right", "above", "below", "center")
    return [m for s in sides for m in getattr(model, s)
            if type(m).__name__ in ("ColorBar", "ContourColorBar")
            and getattr(m, "name", None) != "dash_by_label_box"]


def _by_build(mode, by):
    spec = tp._spec([{"type": "contour", "zvar": "temp", "yvar": "lat",
                      "xvar": "lon", "options": {"levels": "10"}}],
                    None, {"by": by, "name": "g1"})
    data = make_data_json(_surface(),
                          variable_labels={"temp": "Temperature"})
    roots, _notes, _owner = tbk._build(mode, spec, data)
    (grid,) = tbk._grids(roots).values()
    return grid


@pytest.mark.parametrize("mode", _MODES)
class TestTheByContourKey:
    """CV-8a: a by() contour draws twoway's one key."""

    def test_no_key_under_by(self, mode):
        """by(date): no panel keeps a key and no key cell is drawn."""
        grid = _by_build(mode, "date")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        assert tbk._cell(grid, "dash_by_clegend") is None

    def test_one_key_under_clegend_on(self, mode):
        """by(date, clegend(on)): one key at the right of the panels,
        none on a panel, titled with z's label."""
        grid = _by_build(mode, "date, clegend(on)")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        cell = tbk._cell(grid, "dash_by_clegend")
        assert cell is not None
        assert tbk._cell_side(grid, cell) == "right"
        # Flipped (WP-42 CV-3): dash's colour key was a ContourColorBar;
        # twoway draws swatches beside a z axis (CV-3): panel 1's key
        # cell, titled with z's label.
        assert "dash_key_cell" in (cell[0].tags or [])
        assert cell[0]._dash_key_title.text == "Temperature"

    def test_one_key_below_under_pos6(self, mode):
        """by(date, clegend(on pos(6))): the one key below the panels."""
        grid = _by_build(mode, "date, clegend(on pos(6))")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        cell = tbk._cell(grid, "dash_by_clegend")
        assert cell is not None
        assert tbk._cell_side(grid, cell) == "below"
        # Flipped (WP-42 CV-3): the key cell (see above).
        assert "dash_key_cell" in (cell[0].tags or [])


# ---------------------------------------------------------------------------
# twoway's axis-style colour key, as measured (test/fixtures/
# colorvar_key_truth.json, scripts/extract_colorvar_key_truth.do): what the
# key cell of CV-3 is drawn to.
# ---------------------------------------------------------------------------

import json  # noqa: E402

_KEY_FIXTURE = os.path.join(_HERE, "fixtures", "colorvar_key_truth.json")

#: The swatch each plot type keys its levels with (S_<type>): a marker
#: (circle), a rect, a line, a marker on a line, or no key at all.
_SWATCH_KIND = {
    "scatter": "marker", "connected": "marker+line", "line": "line",
    "area": "none", "bar": "rect", "spike": "rect", "dropline": "marker",
    "dot": "marker", "rarea": "none", "rbar": "rect", "rspike": "rect",
    "rcap": "marker", "rcapsym": "marker", "rscatter": "marker",
    "rline": "line", "rconnected": "marker+line", "pcspike": "rect",
    "pccapsym": "marker", "pcarrow": "rect", "pcbarrow": "rect",
    "pcscatter": "marker",
}


def _key_truth():
    with open(_KEY_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _key_texts(rec):
    """twoway's unrotated key texts right of the plot region, top first."""
    r = rec["plot"]["right"]
    return [t["text"] for t in sorted(rec["texts"], key=lambda t: t["y"])
            if t["x"] > r + 1 and not t["rotate"]]


def _swatch_kind(rec):
    k = rec["key"]
    filled = [c for c in k.get("circles", []) if c.get("fill") != "none"]
    lines = [h for h in k.get("hlines", []) if h.get("stroke") != "#000000"]
    if filled and lines:
        return "marker+line"
    if filled:
        return "marker"
    if k.get("rects"):
        return "rect"
    return "line" if lines else "none"


class TestTwowaysKey:
    """The measured key: highest level at the top, labelled at the z axis'
    ticks, no missing entry, the title up the right of the labels."""

    def test_discrete_key_is_an_axis(self):
        t = _key_truth()
        assert _key_texts(t["K1"]) == ["5", "4", "3", "2", "1"]
        assert _key_texts(t["K2"]) == ["1", ".8", ".6", ".4", ".2", "0"]
        assert _key_texts(t["K7"])[0] == "Foreign"
        assert _key_texts(t["K3"]) == ["3.66667", "2.33333"]
        assert _key_texts(t["K4"]) == ["4", "2"]
        assert _key_texts(t["K_cont"]) == ["15,000", "10,000", "5,000", "0"]
        for pid in ("K1", "K8", "E_allmiss"):
            assert not any("missing" in x["text"] or x["text"] == "rest"
                           for x in t[pid]["texts"])
        (title,) = [x for x in t["K1"]["texts"] if x["rotate"]
                    and x["x"] > t["K1"]["plot"]["right"]]
        assert title["rotate"] == -90.0
        assert title["text"] == "Repair record 1978"

    def test_swatch_kind(self):
        t = _key_truth()
        got = {p[2:]: _swatch_kind(r) for p, r in t.items()
               if p.startswith("S_")}
        assert got == _SWATCH_KIND


# ---------------------------------------------------------------------------
# LT-22: contourline keys its levels in the plot legend under colorlines,
# as twoway does (CL_cl: one key a line, highest first, labelled 8000 ...
# 7700 in the line's colour, at the right; CL_clp: plegend(position(6))
# below), and plain contourline draws no legend and prints nothing (CL_ctl).
# ---------------------------------------------------------------------------

import test_contour_gen as _cg  # noqa: E402
import test_contour_outlines as _co  # noqa: E402

_CMODES = ("std", "srv")


def _level_legends(fig):
    return [m for s in ("right", "left", "above", "below", "center")
            for m in getattr(fig, s)
            if type(m).__name__ == "Legend" and m.items
            and m.visible is not False]


def _label(it):
    v = getattr(it.label, "value", None)
    return str(it.label if v is None else v)


@pytest.mark.parametrize("mode", _CMODES)
class TestContourlineLegend:

    def test_the_fixture(self, mode):
        t = _key_truth()
        assert _key_texts(t["CL_cl"]) == ["8000", "7900", "7800", "7700"]
        assert not [r for r in t["CL_ctl"]["regions"][1:]]
        assert len(t["CL_clp"]["regions"]) == 2

    def test_colorlines_keys_its_levels(self, mode):
        """contourline z y x, colorlines: one legend at the right keying
        each cut, highest first, in its line's colour, no note."""
        plot = _cg._plot("contourline", {"colorlines": "colorlines"})
        fig, msgs = _co._draw(mode, plot, _co._scatter_df())
        [cr] = _cg._crs(fig)
        lev = [float(v) for v in cr.line_renderer.data_source.data["levels"]]
        cols = list(cr.line_renderer.data_source.data["line_color"])
        (lg,) = _level_legends(fig)
        assert lg in list(fig.right)
        # Centred on the plot region (CL_cl's box about its centre).
        assert lg.location == "center"
        want = [dr._dash_fmt_text(v, "%9.0g") for v in reversed(lev)]
        assert [_label(it) for it in lg.items] == want
        got = [it.renderers[0].glyph.line_color for it in lg.items]
        assert got == list(reversed(cols))
        assert not [m for m in msgs if "contourline" in str(m)]

    def test_plegend_places_it(self, mode):
        """plegend(position(6)) puts the level legend below."""
        plot = _cg._plot("contourline", {"colorlines": "colorlines"})
        spec = tp._spec([plot], None, {"plegend": "position(6)"})
        figs, _m = _cg._figs_msgs(mode, spec, _co._scatter_df())
        (lg,) = _level_legends(figs[0])
        assert lg in list(figs[0].below)

    def test_plain_contourline_draws_no_legend_and_no_note(self, mode):
        plot = _cg._plot("contourline")
        fig, msgs = _co._draw(mode, plot, _co._scatter_df())
        assert not _level_legends(fig)
        assert not [m for m in msgs if "contourline" in str(m)]


# ---------------------------------------------------------------------------
# CV-3: every colour key is twoway's axis-style key (colorvar_key_truth.json
# K*, S_*, E_allmiss): a key cell of swatches in the plot type's key kind,
# highest level at the top, a z axis with its axis line ticked at natscale
# (a discrete key) or the cuts (a binned or stepped key), the title up the
# axis side, no missing entry, no frame.
# ---------------------------------------------------------------------------

import math  # noqa: E402

import test_colorvar_truth as _tct  # noqa: E402
import colour_bins as cb  # noqa: E402
from test_mode_parity import plot_for  # noqa: E402

#: The probes' plot options (colorvar_key_truth.json "command").
_KEY_OPTS = {
    "K1": {"colorvar": "rep78", "colordiscrete": "colordiscrete"},
    "K2": {"colorvar": "foreign", "colordiscrete": "colordiscrete"},
    "K3": {"colorvar": "rep78", "colorlevels": "3"},
    "K4": {"colorvar": "rep78", "colorcuts": "2 4"},
    "K8": {"colorvar": "rep78", "colordiscrete": "colordiscrete",
           "colorcuts": "3 4", "colorotherlabel": '"rest"'},
    "K_cont": {"colorvar": "price"},
}


def _key_cells(root):
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    return [m for m in refs if "dash_key_cell" in (m.tags or [])
            and type(m).__name__ == "Plot"]


def _render_root(spec, mode):
    return _tct._render(spec, mode)


def _figure_keys(root):
    """The colour key models drawn on a figure: a Legend named as the
    colour key, a ColorBar (a by() label box excepted)."""
    from bokeh.models import ColorBar, Legend, Plot
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    out = []
    for f in refs:
        if not isinstance(f, Plot) or "dash_key_cell" in (f.tags or []):
            continue
        for side in ("left", "right", "above", "below", "center"):
            for m in getattr(f, side):
                if isinstance(m, ColorBar) and m.name != "dash_by_label_box":
                    out.append(m)
                elif isinstance(m, Legend) \
                        and m.name == dr._COLORVAR_LEGEND_NAME:
                    out.append(m)
    return out


def _cell_state(cell):
    """(swatch kinds, swatches top first as (value, colour), label texts
    top first, axis bounds, axis title)."""
    ax = cell._dash_key_axis
    rs = [r for r in cell.renderers if r.name == "dash_key_swatch"]
    kinds = sorted(r.glyph.marker for r in rs)
    d = rs[0].data_source.data if rs else cell._dash_keycell["src"].data
    sw = sorted(zip(d["y"], d["c"]), key=lambda t: -t[0])
    ovr = dict(ax.major_label_overrides or {})
    texts = [ovr[k] for k in sorted(ovr, key=float, reverse=True)]
    tl = getattr(cell, "_dash_key_title", None)
    return kinds, sw, texts, tuple(ax.bounds), (tl.text if tl else None)


def _hex(c):
    c = str(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _truth_swatches(rec):
    """twoway's filled swatches top first as (value, fill): the axis line
    runs lo .. hi from its y1 (bottom) to its y2 (top)."""
    k = rec["key"]
    fills = [(c["cy"], c["fill"]) for c in k.get("circles", [])
             if c.get("fill") not in (None, "none")]
    fills += [(r["cy"], r["fill"]) for r in k.get("rects", [])
              if r.get("fill") not in (None, "none")]
    return sorted(fills)


@pytest.fixture
def _auto(monkeypatch):
    monkeypatch.setattr(tp, "_DF", _tct._auto_frame())


@pytest.mark.usefixtures("_auto")
class TestTheAxisKey:
    """CV-3: the key cell's swatches top to bottom, their colours and
    positions, the axis's labels and its line, no missing entry, no
    Legend or ColorBar on the figure (twoway's K probes)."""

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", sorted(_KEY_OPTS))
    def test_probe(self, pid, mode):
        rec = _key_truth()[pid]
        root = _render_root(tp._spec([plot_for("scatter", _KEY_OPTS[pid],
                                               yvar="mpg", xvar="weight")]),
                            mode)
        assert not _figure_keys(root)
        (cell,) = _key_cells(root)
        kinds, sw, texts, bounds, title = _cell_state(cell)
        assert kinds == ["circle"]
        assert texts == _key_texts(rec)
        assert not [t for t in texts if "missing" in t or t == "rest"]
        want = _truth_swatches(rec)
        assert len(sw) == len(want)
        # twoway's axis line runs from the bottom end to the top end.
        (vl,) = rec["key"]["vlines"]
        lo, hi = bounds
        for (v, col), (cy, fill) in zip(sw, want):
            tv = lo + (vl["y1"] - cy) / (vl["y1"] - vl["y2"]) * (hi - lo)
            assert abs(v - tv) <= 0.01 * (hi - lo), (pid, sw, want)
            assert max(abs(a - b) for a, b in zip(_hex(col), _hex(fill))) \
                <= 2, (pid, col, fill)
        assert cell._dash_key_title.angle == pytest.approx(math.pi / 2)
        assert title
        assert cell._dash_key_axis.axis_line_color is not None
        assert cell.outline_line_color is None

    @pytest.mark.parametrize("ptype", sorted(_SWATCH_KIND))
    def test_swatch_kind_table(self, ptype):
        """dash's swatch table is twoway's (S_<type>)."""
        assert dr._DASH_KEY_SWATCH_KIND[ptype] == _SWATCH_KIND[ptype]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype,want", [
        ("bar", ["square"]), ("line", ["dash"]),
        ("connected", ["circle", "dash"]), ("spike", ["square"])])
    def test_swatch_kind(self, ptype, want, mode):
        opts = dict(_KEY_OPTS["K1"])
        if ptype in ("line", "connected", "spike"):
            opts["sort"] = "sort"
        root = _render_root(tp._spec([plot_for(ptype, opts, yvar="mpg",
                                               xvar="weight")]), mode)
        (cell,) = _key_cells(root)
        assert _cell_state(cell)[0] == want

    @pytest.mark.parametrize("mode", _MODES)
    def test_all_missing_draws_the_title_alone(self, mode, monkeypatch):
        """E_allmiss: an all-missing colorvar() draws the axis line and the
        title, no swatch and no tick."""
        df = _tct._auto_frame()
        df["zmiss"] = np.nan
        monkeypatch.setattr(tp, "_DF", df)
        rec = _key_truth()["E_allmiss"]
        assert not _key_texts(rec)
        root = _render_root(tp._spec([plot_for(
            "scatter", {"colorvar": "zmiss"}, yvar="mpg", xvar="weight")]),
            mode)
        assert not _figure_keys(root)
        (cell,) = _key_cells(root)
        _kinds, sw, texts, _b, title = _cell_state(cell)
        assert sw == [] and texts == []
        assert title

    @pytest.mark.parametrize("mode", _MODES)
    def test_two_layers_ring0_one_key(self, mode):
        """One key a graph (CV-6): a later layer's key inside the plot
        replaces an earlier layer's key cell."""
        spec = tp._spec([
            plot_for("scatter", {"colorvar": "rep78",
                                 "colordiscrete": "colordiscrete"},
                     yvar="mpg", xvar="weight"),
            plot_for("scatter", {"colorvar": "foreign",
                                 "colordiscrete": "colordiscrete",
                                 "colorallowmultiple": "colorallowmultiple"},
                     yvar="price", xvar="weight")],
            None, {"clegend": "ring(0)"})
        root = _render_root(spec, mode)
        # Flipped (WP-42 CV-3, D-42-03.b): the ring(0) key was the old
        # Legend inside the plot; twoway draws its axis-style key there:
        # one key cell, the last layer's (foreign: 0 .. 1), no Legend or
        # ColorBar.
        (cell,) = _key_cells(root)
        assert not _figure_keys(root)
        assert cell._dash_key_ring0 == "right"
        assert cb.axis_key_texts(cell)[0] == "1"


def _layout_of(mode, plots, go=None):
    spec = tp._spec(plots, None, go or {})
    return _render_root(spec, mode)


def _figs_and_cells(root):
    from bokeh.models import Plot
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    figs = [m for m in refs if isinstance(m, Plot)
            and "dash_key_cell" not in (m.tags or []) and m.renderers]
    return figs, _key_cells(root)


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
class TestClegendTitle:
    """LT-12 (colorvar_key_truth.json P_ti, P_tbx on K1; C_ti, C_cbx on a
    contour draw alike): clegend(title("Z")) draws Z above the key, centred
    on the key's box, at 1.1 times the labels' size, the axis line's top
    down by the title's band and the z title kept; title(, box) fills and
    outlines that band.  dash replaced the z title with the raw text
    ('"Z", box' with its quotes)."""

    def _texts(self, cell):
        return {r.data_source.data["text"][0]: r
                for r in cell._dash_key_texts}

    @pytest.mark.parametrize("pid", ("P_ti", "P_tbx"))
    def test_the_title_above_the_key(self, mode, pid):
        rec = _key_truth()[pid]
        fig, cell, mpx, warns = _p_build(mode, pid)
        assert not [w for w in warns if "clegend" in w], warns
        # The z title kept: the one the key draws without clegend().
        _f, base, _m, _w = _p_build(mode, "K1")
        assert cell._dash_key_title.text == base._dash_key_title.text
        texts = self._texts(cell)
        assert set(texts) == {"Z"}
        z = texts["Z"]
        assert z.level == "overlay" and z.glyph.text_align == "center"
        lab = dr.OptionTranslator.css_to_pt(
            cell._dash_key_axis.major_label_text_font_size)
        assert dr.OptionTranslator.css_to_pt(z.glyph.text_font_size) == \
            pytest.approx(1.1 * lab, rel=0.01)
        it, ib = cell._dash_keycell["inset"]
        want_t, want_b = _line_fracs(rec)
        assert abs(it - want_t) <= 0.012 and abs(ib - want_b) <= 0.012
        lo, hi = cell._dash_key_axis.bounds
        assert z.data_source.data["y"][0] > hi
        # Centred on the key's box: twoway's Z x from the plot region's
        # edge, in the cell's px.
        (tw,) = [t for t in rec["texts"] if t["text"] == "Z"]
        s = mpx / 2880.0
        to_frame = fig.min_border_right + (cell.min_border_left or 0)
        assert z.data_source.data["x"][0] + to_frame == pytest.approx(
            (tw["x"] - rec["plot"]["right"]) * s, abs=1.0)

    def test_box(self, mode):
        rec = _key_truth()["P_tbx"]
        fig, cell, mpx, warns = _p_build(mode, "P_tbx")
        [box] = [r for r in cell.renderers if r.name == "dash_key_title_box"]
        assert box.level == "overlay"
        assert box.glyph.fill_color == "#d9e6eb"
        assert box.glyph.line_color == "#000000"
        fill = [r for r in rec["key"]["rects"] if r["fill"] == "#d9e6eb"][0]
        d = box.data_source.data
        s = mpx / 2880.0
        assert d["right"][0] - d["left"][0] == pytest.approx(
            fill["w"] * s, abs=1.0)
        z = self._texts(cell)["Z"].data_source.data["x"][0]
        assert (d["left"][0] + d["right"][0]) / 2.0 == pytest.approx(z)
        # The band from the line's ordinary top to its new one.
        lo, hi = cell._dash_key_axis.bounds
        assert d["bottom"][0] == pytest.approx(hi, rel=1e-6) or \
            d["bottom"][0] > hi
        assert d["top"][0] > d["bottom"][0]

    @pytest.mark.parametrize("pid", ("P_tbx2",))
    def test_a_wide_title_s_box_is_capped(self, mode, pid):
        # twoway's box is 408 wide for "Price in dollars" and "WWW" alike
        # (measured 03nov2026): its widest, centred on the key's box.  The
        # build estimates the width (Chrome measures it, the browser test
        # pins "WWW" and "iii").
        rec = _key_truth()[pid]
        fig, cell, mpx, warns = _p_build(mode, pid)
        [box] = [r for r in cell.renderers if r.name == "dash_key_title_box"]
        fill = [r for r in rec["key"]["rects"] if r["fill"] == "#d9e6eb"][0]
        d = box.data_source.data
        assert d["right"][0] - d["left"][0] == pytest.approx(
            fill["w"] * mpx / 2880.0, abs=1.0)
        assert cell._dash_key_px["box"][4] == pytest.approx(
            fill["w"] * mpx / 2880.0, abs=1.0)

    def test_no_box_without_box(self, mode):
        fig, cell, mpx, warns = _p_build(mode, "P_ti")
        assert not [r for r in cell.renderers
                    if r.name == "dash_key_title_box"]


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
class TestColorkeysreverse:
    """Measured 03nov2026 (s2color, SVG): twoway scatter mpg weight,
    colorvar(rep78) colordiscrete colorkeysreverse draws K1's key with its
    colours reversed -- #0000ff at 5's place .. #ffcc00 at 1's -- its labels
    where they are and the markers unchanged; colorvar(price)
    colorkeysreverse draws price's key as without it (C8e).  The key cell
    went silent on it (WP-42 CV-3)."""

    def _cell(self, mode, opts):
        root = _render_root(tp._spec([plot_for("scatter", opts, yvar="mpg",
                                               xvar="weight")]), mode)
        (cell,) = _key_cells(root)
        kc = cell._dash_keycell
        return (list(kc["src"].data["c"]), list(kc["src"].data["y"]),
                dict(kc["axis"].major_label_overrides or {}))

    def test_a_discrete_key_reverses_its_colours(self, mode):
        base = dict(_KEY_OPTS["K1"])
        c0, y0, l0 = self._cell(mode, base)
        c1, y1, l1 = self._cell(mode, dict(base,
                                           colorkeysreverse="colorkeysreverse"))
        assert c1 == list(reversed(c0)) and c1 != c0
        assert (y1, l1) == (y0, l0)

    def test_a_continuous_key_is_unchanged(self, mode):
        base = {"colorvar": "price"}
        assert self._cell(mode, dict(
            base, colorkeysreverse="colorkeysreverse")) == \
            self._cell(mode, base)


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
class TestTheLayoutIsUnchanged:
    """CV-3: a graph with no colour key lays out as before; a key cell
    sits beside its figure inside the graph region, at a width known at
    build, and takes scale() and the xsize()/ysize() box as the key
    did."""

    def test_no_key(self, mode):
        root = _layout_of(mode, [plot_for("scatter", yvar="mpg",
                                          xvar="weight")])
        refs = root.references() if hasattr(root, "references") else [
            m for r in root.roots for m in r.references()]
        assert not [m for m in refs if "dash_key_row" in (m.tags or [])]
        assert not _key_cells(root)

    def test_the_cell_has_a_width(self, mode):
        root = _layout_of(mode, [plot_for("scatter", {"colorvar": "price"},
                                          yvar="mpg", xvar="weight")])
        (cell,) = _key_cells(root)
        assert isinstance(cell.width, int)
        assert cell.width == dr._dash_key_cell_extent(cell,
                                                      cell._dash_key_band)
        refs = root.references() if hasattr(root, "references") else [
            m for r in root.roots for m in r.references()]
        (row,) = [m for m in refs if "dash_key_row" in (m.tags or [])]
        assert row.children[1] is cell
        # Inside the graph region box (GW-6), as twoway draws its key.
        (reg,) = [m for m in refs if "dash_graph_region" in (m.tags or [])]
        assert row in list(reg.children)

    def test_xsize_box_holds_the_key(self, mode):
        root = _layout_of(mode, [plot_for("scatter", {"colorvar": "price"},
                                          yvar="mpg", xvar="weight")],
                          {"xsize": "6", "ysize": "4", "aspectratio": "1"})
        (fig,), (cell,) = _figs_and_cells(root)
        assert fig.width + cell.width == 576
        assert fig.height == 384 and cell.height == 384
        assert abs(fig.frame_width - fig.frame_height) <= 1

    def test_scale_reaches_the_key(self, mode):
        def px(go):
            root = _layout_of(mode, [plot_for(
                "scatter", {"colorvar": "price"}, yvar="mpg",
                xvar="weight")], go)
            (cell,) = _key_cells(root)
            return dr.OptionTranslator.css_to_pt(
                cell._dash_key_axis.major_label_text_font_size)
        assert px({"scale": "1.5"}) == pytest.approx(1.5 * px({}), rel=0.01)


def _cell_record(models):
    """Every key cell's (labels, swatches) among *models*, sorted."""
    out = []
    for m in models:
        if "dash_key_cell" not in (getattr(m, "tags", None) or []) \
                or type(m).__name__ != "Plot":
            continue
        _k, sw, texts, bounds, _t = _cell_state(m)
        out.append((texts, [(round(v, 6), str(c)) for v, c in sw],
                    tuple(round(b, 6) for b in bounds)))
    return sorted(out, key=repr)


#: WP-42 CV-15: zlabel()'s list and valuelabel and zscale(reverse) on a
#: discrete key after a move, the twins against a fresh build.
_EXTRA_MOVES = {
    "CV-15 colordiscrete zlabel() zscale(reverse), range": tp._move_case(
        "CV-15 colordiscrete zlabel() zscale(reverse), range", tp._MOVES[1],
        [plot_for("scatter", {"colorvar": "rep",
                              "colordiscrete": "colordiscrete"})],
        {"zlabel": "1 2 4, valuelabel", "zscale": "reverse"}),
}


@pytest.mark.parametrize("name", [
    "scatter colordiscrete, range to 4500-11385",
    "scatter colorlevels(4), rep dropdown to 3",
    "scatter colorcuts(), rep dropdown to 3",
    "scatter colorvar stepped price, rep dropdown to 3",
    "line colorvar levels (D-15f), rep dropdown to 3",
    "CV-15 colordiscrete zlabel() zscale(reverse), range"],
    ids=["levels", "bins", "cuts", "stepmap", "steps", "zlabel"])
class TestTheKeyAfterAMove:
    """CV-3 (D-42-03.d): after a filter move the key cell's labels and
    swatches equal a fresh build over the kept rows, served (the Python
    twin) and saved (the page's script under node)."""

    def test_twins_agree(self, name):
        import json as _json
        import js_runner
        if name in _EXTRA_MOVES:
            case = _EXTRA_MOVES[name]
        else:
            case = [c for c in tp.MOVE_CORPUS if c.values[0] == name][0]
        _name, spec, action, oracle = case.values
        q = _json.loads(_json.dumps(spec))
        q["build_options"]["filter"] = ""
        for g in q["graphs"]:
            g["if_expr"] = oracle
        r0, _ = tp._standalone(q)
        want = _cell_record(r0._last_layout_root.references())
        before, _ = tp._standalone(spec)
        assert want and want != _cell_record(
            before._last_layout_root.references())
        doc, _ = tp._served(spec)
        kind, label = action
        w = [x for x in tp._widgets_of(doc) if type(x).__name__ == kind][0]
        tp._fire(w, tp._move_widget_value(w, kind, label))
        assert _cell_record([m for root in doc.roots
                             for m in root.references()]) == want
        r, _ = tp._standalone(spec)
        w, cb = [(w, cb) for w, cb in zip(r.filter_widgets,
                                          r.filter_callbacks)
                 if type(w).__name__ == kind][0]
        session = js_runner.JsSession(r.filter_callbacks)
        session.set(w, tp._move_widget_value(w, kind, label))
        session.run(cb)
        assert _cell_record(r._last_layout_root.references()) == want


#: Every plot's canvas and frame in page px, its tags and its axes' boxes.
_FRAMES_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const plots = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.canvas_view) {
      const c = v.canvas_view.el.getBoundingClientRect();
      const f = v.frame.bbox;
      const parts = [];
      for (const [m, rv] of (v.renderer_views || [])) {
        if (!m.visible || !rv.bbox || !String(m.type).endsWith('Axis')) continue;
        const b = rv.bbox;
        parts.push([m.axis_label || '', b.x0, b.y0, b.x1, b.y1]);
      }
      plots.push({tags: v.model.tags || [], canvas: [c.left, c.top, c.width,
                  c.height], frame: [c.left + f.left, c.top + f.top,
                  c.left + f.right, c.top + f.bottom], parts});
    }
    for (const k of (v.child_views || [])) visit(k);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, plots}),
                     '*');
}, 3500));
</script>
"""


def _keyed_page(mode, tmp):
    import warnings as _w
    import test_sizing as ts
    spec = tbk._spec([tbk._graph("g1", [tbk._p("scatter", colorvar="weight")],
                                 {}, title=False)], scheme="stcolor")
    sp = os.path.join(tmp, "s.json")
    dp = os.path.join(tmp, "d.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(tbk.tg._data(), fh)
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        if mode == "saved":
            return dr.DashRenderer(sp, dp).render()
        from bokeh.document import Document
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        ap = os.path.join(tmp, "a.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = ts.load_app(ap, "_cvk_app_%s" % mode, draw=False)
        doc = Document()
        mod.make_document(doc)
        return file_html(doc, INLINE, "served")


@pytest.mark.release
@pytest.mark.parametrize("mode", _MODES)
class TestTheKeyCellInChrome:
    """CV-3 in Chrome: the key cell's z axis spans its figure's plot region
    (the frames' tops and bottoms within 2 px) at 600, 1000 and 1400 px;
    the figure and the cell together keep the graph's shape (the figure's
    height the graph's at the figure's ratio) and the key's labels and
    title lie inside the cell's canvas."""

    def test_alignment(self, mode, tmp_path):
        import responsive_probe
        html = _keyed_page(mode, str(tmp_path))
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _FRAMES_JS)
        try:
            rec = responsive_probe.measure_many(html, (600, 1000, 1400))
        finally:
            mp.undo()
        ratios = []
        for w, r in rec.items():
            cells = [p for p in r["plots"] if "dash_key_cell" in p["tags"]]
            figs = [p for p in r["plots"] if "dash_key_cell" not in p["tags"]]
            assert len(cells) == 1 and len(figs) == 1, (w, r)
            c, f = cells[0], figs[0]
            assert abs(c["frame"][1] - f["frame"][1]) <= 2, (w, c, f)
            assert abs(c["frame"][3] - f["frame"][3]) <= 2, (w, c, f)
            # Side by side, the cell at the figure's right.
            assert abs(c["canvas"][0] - (f["canvas"][0] + f["canvas"][2])) \
                <= 2, (w, c, f)
            cw, ch = c["canvas"][2:]
            for q in c["parts"]:
                assert q[1] >= -0.5 and q[3] <= cw + 0.5, (w, q, c)
                assert q[2] >= -0.5 and q[4] <= ch + 0.5, (w, q, c)
            ratios.append((f["canvas"][2] + cw) / f["canvas"][3])
        assert max(ratios) - min(ratios) <= 0.02, ratios

    def test_title_reads_upward(self, mode):
        """Measured 03nov2026 (headless Chrome): a right axis's title at
        pi/2 reads upward; the key cell's title is set so."""
        assert dr._DASH_KEY_TITLE_UP == pytest.approx(math.pi / 2)


class TestTheKeyCellHelpers:
    """CV-3: the key cell's module helpers, each on its own."""

    def test_range(self):
        lo, hi = dr._dash_key_range(1.0, 5.0)
        f = dr._DASH_KEY_AXIS_INSET
        # The axis's ends sit twoway's inset (K1: 135.3 of 2388.33) in.
        assert (1.0 - lo) / (hi - lo) == pytest.approx(f)
        assert dr._dash_key_range(None, 1) == (0.0, 1.0)
        assert dr._dash_key_range(2, 2) == dr._dash_key_range(1.5, 2.5)
        a, b = dr._dash_key_range(10, 1000, log=True)
        assert math.log10(10) - math.log10(a) == pytest.approx(
            math.log10(b) - math.log10(1000))
        assert dr._dash_key_range(-1, 10, log=True) == (1.0, 10.0)

    def test_ends(self):
        # K_cont: from its 0 tick to the maximum.
        assert dr._dash_key_ends(3291, 15906, [0, 5000, 15000]) == (
            0.0, 15906.0)
        assert dr._dash_key_ends(None, None, []) == (None, None)

    def test_bin_centres(self):
        assert dr._dash_key_bin_centres(3291, 15906, [5000, 10000, 15000],
                                        [0]) == [2500.0, 7500.0, 12500.0,
                                                 15453.0]
        assert dr._dash_key_bin_centres(1, 100, [10], log=True) == [
            pytest.approx(math.sqrt(10)), pytest.approx(math.sqrt(1000))]
        assert dr._dash_key_bin_centres(None, None, []) == []

    def test_a_level_no_value_reaches_is_not_drawn(self):
        # Measured 03nov2026 (twoway line y x, colorvar(z)): z of 1,000 ..
        # 2,300 cut at 1,000 .. 2,500 draws four swatches, #0000ff ..
        # #ffff00, the level above 2,500 none; z of 1 .. 10,000 under
        # zscale(log) cut at 2,000 .. 10,000 five of six, the level above
        # 10,000 none.  Its centre is NaN and _dash_key_cell_data drops it
        # with its colour.
        c = dr._dash_key_bin_centres(1000, 2300, [1000, 1500, 2000, 2500])
        assert c[:4] == [1000.0, 1250.0, 1750.0, 2250.0] and math.isnan(c[4])
        c = dr._dash_key_bin_centres(1, 10000, [2000, 4000, 6000, 8000,
                                                10000], log=True)
        assert len(c) == 6 and math.isnan(c[5]) and \
            not any(math.isnan(v) for v in c[:5])
        d = dr._dash_key_cell_data(c, ["a", "b", "c", "d", "e", "f"], True,
                                   12.0)
        assert d["c"] == ["a", "b", "c", "d", "e"] and len(d["y"]) == 5
        # Below the smallest value too.
        c = dr._dash_key_bin_centres(5, 9, [2, 4, 6, 8])
        assert math.isnan(c[0]) and math.isnan(c[1]) and c[2] == 5.0

    def test_the_js_twin_leaves_out_the_same_levels(self):
        import re as _re
        from js_runner import run_js
        js = dr._DASH_CVAR_RELEVEL_JS
        fns = []
        for name in ("dash_key_ends", "dash_key_bin_centres",
                     "dash_key_cell_data"):
            m = _re.search(r"\nfunction %s\(.*?\n\}\n" % name, js, _re.S)
            assert m, name
            fns.append(m.group(0))
        cases = [(1000, 2300, [1000, 1500, 2000, 2500], False),
                 (1, 10000, [2000, 4000, 6000, 8000, 10000], True),
                 (5, 9, [2, 4, 6, 8], False)]
        script = "".join(fns) + (
            "const out = [];\n"
            "for (const [lo, hi, cuts, log] of %s) {\n"
            "  const c = dash_key_bin_centres(lo, hi, cuts, [], log);\n"
            "  const d = dash_key_cell_data(c, ['a','b','c','d','e','f'],"
            " true, 12, null, null);\n"
            "  out.push([c.map((v) => Number.isNaN(v) ? null : v), d.c]);\n"
            "}\nconsole.log(JSON.stringify(out));\n"
            % json.dumps([list(c) for c in cases]))
        got = run_js(script)
        for (lo, hi, cuts, log), (jc, jd) in zip(cases, got):
            pc = dr._dash_key_bin_centres(lo, hi, cuts, log=log)
            assert [None if v != v else pytest.approx(v) for v in pc] == jc
            assert dr._dash_key_cell_data(pc, list("abcdef"), True,
                                          12.0)["c"] == jd

    def test_levels_layout(self):
        lo, hi, cs, pos, ovr = dr._dash_key_levels_layout(
            ["1", "2", "5"], {"1": 1.0, "2": 2.0, "5": 5.0}, True, "%8.0gc")
        assert (lo, hi, cs) == (1.0, 5.0, [1.0, 2.0, 5.0])
        assert pos == [1.0, 2.0, 3.0, 4.0, 5.0]
        lo, hi, cs, pos, ovr = dr._dash_key_levels_layout(["a", "b"], {},
                                                          False, None)
        assert cs == pos == [1.0, 2.0] and ovr == {1.0: "a", 2.0: "b"}
        assert dr._dash_key_levels_layout([], {}, True, None)[2] == []

    def test_bins_layout(self):
        lo, hi, cs, pos, ovr = dr._dash_key_bins_layout(
            [1.0, 3.0, 5.0, float("nan")], [2.0, 4.0], False, "%8.0gc")
        assert (lo, hi, cs, pos) == (1.0, 5.0, [1.5, 3.0, 4.5], [2.0, 4.0])
        assert dr._dash_key_bins_layout([1.0, 5.0], [3.0, 4.0], True,
                                        None)[2] == [3.0, 4.0]
        assert dr._dash_key_bins_layout([float("nan")], [2.0], False,
                                        None)[2:] == ([], [], {})

    def test_zlabel(self):
        """WP-42 CV-15: zlabel() and zscale() as the key cell reads them;
        a list relabels the key, valuelabel writes the value labels."""
        z = dr._dash_key_zlabel({"zlabel": "1 3 5", "zscale": "reverse"})
        assert z["mode"] == "explicit" and z["ticks"] == [1.0, 3.0, 5.0]
        assert z["reverse"] is True
        z = dr._dash_key_zlabel({"zlabel": ", valuelabel"},
                                {"0": "Domestic", "1": "Foreign"})
        lay = dr._dash_key_levels_layout(["0", "1"], {"0": 0.0, "1": 1.0},
                                         True, "%8.0gc", "period", z)
        assert lay[4][0.0] == "Domestic" and lay[4][1.0] == "Foreign"
        assert lay[4][0.2] == ".2"
        assert dr._dash_key_zlabel({})["reverse"] is False

    def _cell(self, **kw):
        spec = {"kind": "marker", "side": "right", "lo": 1.0, "hi": 5.0,
                "centres": [1.0, 5.0], "colours": ["#0000ff", "#ffcc00"],
                "ticks": [1.0, 5.0], "labels": {1.0: "1", 5.0: "5"},
                "title": "Z", "chrome": {}, "width_px": 24,
                "length_px": 300}
        spec.update(kw)
        return dr._dash_key_cell(spec)

    def test_cell_and_its_data(self):
        c = self._cell()
        assert "dash_key_cell" in c.tags and c.toolbar_location is None
        assert c._dash_key_axis.bounds == (1.0, 5.0)
        assert c._dash_key_title.angle == pytest.approx(math.pi / 2)
        d = dr._dash_key_cell_data([1.0, 2.0], ["a", "b"], True, 12.0,
                                   [(0, 1), (1, 2)], 24)
        assert d["x"] == [12.0, 12.0] and d["b"] == [0.0, 1.0]
        assert d["t"] == [1.0, 2.0] and d["r"] == [24.0, 24.0]
        band = self._cell(kind="band", bands=[(1.0, 3.0), (3.0, 5.0)],
                          centres=[2.0, 4.0])
        assert [type(r.glyph).__name__ for r in band.renderers] == ["Quad"]
        assert type(self._cell(log=True)._dash_key_axis).__name__ \
            == "LogAxis"

    def test_extent(self):
        c = self._cell()
        w = dr._dash_key_cell_extent(c, 24)
        assert w > 24 and c.width == w
        c2 = self._cell(title="")
        assert dr._dash_key_cell_extent(c2, 24) < w

    def test_update(self):
        c = self._cell()
        kc = c._dash_keycell
        dr._dash_cvar_keycell_update(kc, 2.0, 4.0, [2.0, 3.0, 4.0],
                                     ["a", "b", "c"], [2.0, 4.0],
                                     {2.0: "2", 4.0: "4"})
        assert list(kc["src"].data["y"]) == [2.0, 3.0, 4.0]
        assert c._dash_key_axis.bounds == (2.0, 4.0)
        assert list(kc["ticker"].ticks) == [2.0, 4.0]
        assert kc["range"].start < 2.0 < 4.0 < kc["range"].end
        dr._dash_cvar_keycell_update(None, 0, 1, [], [], [], {})

    def test_reside(self):
        c = self._cell()
        rec = c._dash_keycell
        assert dr._dash_key_cell_reside(c, "right") is c
        n = dr._dash_key_cell_reside(c, "left")
        assert n._dash_keycell is rec and n._dash_key_side == "left"
        assert rec["axis"] is n._dash_key_axis

    def test_scale_entries_and_shape(self):
        c = self._cell()
        ents = dr._dash_key_scale_entries(c)
        # Both borders (WP-42 CV-15: the swatches' side holds altaxis's
        # band and region()'s room).
        assert [e[1] for e in ents] == ["width", "min_border_right",
                                        "min_border_left"]
        from bokeh.plotting import figure
        f = figure(sizing_mode="stretch_width", aspect_ratio=2.0)
        fw = dr._dash_key_hold_shape(f, c, 720.0)
        # The figure's nominal width less the cell's; the graph's height.
        assert fw == 720.0 - c.width and f.height == 360
        assert dr._dash_key_hold_shape(f, c, 720.0) == fw

    def test_the_level_and_bin_relevels(self):
        c = self._cell()
        plan = {"keycell": dict(c._dash_keycell, pos={"1": 1.0, "3": 3.0},
                                numeric=True, fmt="%8.0gc", dp="period")}
        plan["keycell"]["src"] = c._dash_keycell["src"]
        dr._dash_cvar_keycell_levels(plan, ["1", "3"], ["#a", "#b"])
        assert list(c._dash_keycell["src"].data["y"]) == [1.0, 3.0]
        plan = {"keycell": c._dash_keycell, "discrete": False,
                "fmt": "%8.0gc"}
        dr._dash_cvar_keycell_bins(plan, [1.0, 5.0], [3.0], ["#a", "#b"])
        assert list(c._dash_keycell["src"].data["y"]) == [2.0, 4.0]

    def test_the_step_relevel(self):
        c = self._cell()
        ax = c._dash_key_axis
        ax.ticker.ticks = [0.0, 5000.0]
        ax.major_label_overrides = {0.0: "0", 5000.0: "5,000"}
        plan = {"keycell": c._dash_keycell, "cbar": ax, "zrange": None}
        dr._dash_cvar_keycell_steps(plan, 3000.0, 6000.0, [5000.0],
                                    ["#a", "#b"])
        assert list(c._dash_keycell["src"].data["y"]) == [2500.0, 5500.0]
        assert ax.bounds == (0.0, 6000.0)

    def test_the_contour_helpers(self):
        from bokeh.plotting import figure
        f = figure()
        cr = f.contour(x=[[0, 1], [0, 1]], y=[[0, 0], [1, 1]],
                       z=[[0, 1], [1, 2]], levels=[0, 1, 2],
                       fill_color=["#ff0000", "#0000ff"])
        assert dr._dash_contour_band_colours(cr, 3) == [
            "#ff0000", "#0000ff", "#0000ff"]
        c = self._cell()
        assert dr._dash_contour_key_state(c._dash_keycell) == (
            [1.0, 5.0], {1.0: "1", 5.0: "5"})
        assert dr._dash_contour_key_state(None) == ([], {})


@pytest.mark.parametrize("mode", _MODES)
class TestIlegendsKeys:
    """by(, ilegends): twoway draws each panel's own colour key (measured
    03nov2026: ``scatter mpg weight, colorvar(price) by(foreign,
    ilegends)`` exports two keys titled Price; by(foreign) none)."""

    def test_each_panel_draws_its_key(self, mode):
        spec = tbk._spec([tbk._graph("g1", [tbk._p("scatter",
                                                   colorvar="headroom")],
                                     {"by": "foreign, ilegends"})])
        roots, _n, _o = tbk._build(mode, spec)
        grids = [m for r in roots for m in r.references()
                 if type(m).__name__ == "GridPlot"
                 and any(type(c[0]).__name__ == "Row" for c in m.children)]
        (grid,) = grids
        rows = [c[0] for c in grid.children
                if type(c[0]).__name__ == "Row"]
        assert len(rows) == 2
        for r in rows:
            f, cell = r.children
            assert type(f).__name__ == "figure"
            assert "dash_key_cell" in (cell.tags or [])
        assert tbk._cell(grid, "dash_by_clegend") is None


@pytest.mark.parametrize("mode", _MODES)
def test_an_upright_key_below_runs_twoways_length(mode):
    """clegend(position(6)): the key below the plot is upright, its axis
    line G01's share of the graph's height (421.6 of 2880)."""
    root = _layout_of(mode, [plot_for("scatter", {"colorvar": "price"},
                                      yvar="mpg", xvar="weight")],
                      {"clegend": "position(6)"})
    (cell,) = _key_cells(root)
    figs, _c = _figs_and_cells(root)
    gh = float(figs[0]._dash_nominal_px[1])
    frame = cell.height - cell.min_border_top - cell.min_border_bottom
    line = frame * (1 - 2 * dr._DASH_KEY_AXIS_INSET)
    assert abs(line - 421.6 / 2880 * gh) <= 1.5, (line, gh)
    assert cell._dash_key_place == "below" and cell._dash_key_side == "right"


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
def test_save_as_svg_exports_the_key_with_its_figure(mode):
    """The figure's Save as SVG action exports its graph with the key
    cell beside it (the key row), not the figure alone."""
    root = _layout_of(mode, [plot_for("scatter", {"colorvar": "price"},
                                      yvar="mpg", xvar="weight")])
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    acts = [m for m in refs if type(m).__name__ == "CustomAction"
            and "dash_svg_save" in (m.tags or [])]
    rows = [m for m in refs if "dash_key_row" in (m.tags or [])]
    assert len(rows) == 1
    grids = [a.callback.args.get("grid") for a in acts]
    assert any(g is rows[0] or (g is not None and rows[0] in [
        x for x in g.references()]) for g in grids), grids


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
class TestTheKeyAsTwowayDrawsIt:
    """The whole-image pair (scatter mpg weight, colorvar(rep78)
    colordiscrete at 1100 px against twoway's export): the key's title,
    its swatches and its place, from colorvar_key_truth.json K1."""

    def _parts(self, mode):
        root = _layout_of(mode, [plot_for(
            "scatter", _KEY_OPTS["K1"], yvar="mpg", xvar="weight")])
        (fig,), (cell,) = _figs_and_cells(root)
        return fig, cell

    def test_the_title_is_upright_black_and_centred(self, mode):
        """twoway: upright (the axis title's style), black, centred on the
        axis's length."""
        fig, cell = self._parts(mode)
        tl = cell._dash_key_title
        assert tl.text and tl.angle == pytest.approx(math.pi / 2)
        assert tl.text_font_style == "normal"
        assert tl.text_align == "center" and tl.text_baseline == "middle"
        assert tl.text_color == fig.yaxis[0].axis_label_text_color
        assert tl.text_font_size == fig.yaxis[0].axis_label_text_font_size
        lo, hi = cell._dash_key_axis.bounds
        assert tl.y == pytest.approx((lo + hi) / 2.0)

    def test_the_swatch_is_the_layers_marker(self, mode):
        """twoway keys a level in the plot's marker (K1: the key's circles
        are its markers' size)."""
        fig, cell = self._parts(mode)
        sizes = {r.glyph.size for r in fig.renderers
                 if type(r.glyph).__name__ == "Scatter"
                 and isinstance(r.glyph.size, (int, float))
                 and r.glyph.size > 0}
        (sw,) = [r for r in cell.renderers if r.name == "dash_key_swatch"]
        assert sw.glyph.size in sizes

    def test_the_key_sits_at_twoways_place(self, mode):
        """K1 (of the graph's 2880-unit smaller side): plot region to the
        swatches 220.9, the axis to the title 227.09, the title to the
        key's edge 145.33 (the graph margin apart)."""
        t = _key_truth()["K1"]
        k = t["key"]
        side = min(t["canvas"]["w"], t["canvas"]["h"])
        sw = [c["cx"] for c in k["circles"]][0]
        ax = k["vlines"][0]["x1"]
        (title,) = [x for x in t["texts"] if x["rotate"]
                    and x["x"] > t["plot"]["right"]]
        assert dr._DASH_KEY_GAP_PLOT == pytest.approx(
            (sw - t["plot"]["right"]) / side)
        # The title's letters' middle (its SVG x is its baseline).
        assert dr._DASH_KEY_GAP_TITLE == pytest.approx(
            (title["x"] - dr._DASH_KEY_TITLE_INK * title["size"] - ax)
            / side)
        fig, cell = self._parts(mode)
        nom = fig._dash_nominal_px
        mpx = min(nom) / (dr.OptionTranslator.size_ref_of(fig) / 4.0)
        band = cell._dash_key_band
        assert fig.min_border_right == round(
            dr._DASH_KEY_GAP_PLOT * mpx - band / 2.0)
        assert cell._dash_key_title.x == pytest.approx(
            band + dr._DASH_KEY_GAP_TITLE * mpx)
        assert cell.width >= band + math.ceil(
            (dr._DASH_KEY_GAP_TITLE + dr._DASH_KEY_GAP_END) * mpx)


# ---------------------------------------------------------------------------
# CV-15: zlabel() and zscale() drawn on the key cell (colorvar_key_truth.json
# C24: zlabel(1 3 5) relabels the discrete key 5 3 1; C26: zscale(reverse)
# puts 1 at the top, its colour with it; K7: zlabel(, valuelabel) writes
# Foreign and Domestic at the ends), with no note.
# ---------------------------------------------------------------------------

_Z_OPTS = {
    "C24": ({"colorvar": "rep78", "colordiscrete": "colordiscrete"},
            {"zlabel": "1 3 5"}),
    "C26": ({"colorvar": "rep78", "colordiscrete": "colordiscrete"},
            {"zscale": "reverse"}),
    "K7": ({"colorvar": "foreign", "colordiscrete": "colordiscrete"},
           {"zlabel": ", valuelabel"}),
}


@pytest.mark.usefixtures("_auto")
class TestZOptionsOnTheKey:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", sorted(_Z_OPTS))
    def test_probe(self, pid, mode):
        rec = _key_truth()[pid]
        opts, go = _Z_OPTS[pid]
        spec = tp._spec([plot_for("scatter", opts, yvar="mpg",
                                  xvar="weight")], None, go)
        if mode == "saved":
            r, warns = tp._standalone(spec)
            root = r._last_layout_root
        else:
            root, warns = tp._served(spec)
        (cell,) = _key_cells(root)
        ovr = dict(cell._dash_key_axis.major_label_overrides or {})
        rng = cell._dash_keycell["range"]
        rev = rng.start > rng.end
        # Top first: on a reversed axis the lowest value is at the top.
        texts = [ovr[k] for k in sorted(ovr, key=float, reverse=not rev)]
        assert texts == _key_texts(rec), (pid, texts)
        if pid == "C26":
            # 1 at the top, in level 1's colour (#0000ff).
            d = cell._dash_keycell["src"].data
            low = min(zip(d["y"], d["c"]))
            assert rev and low[0] == 1.0 and low[1].lower() == "#0000ff"
        assert not [w for w in warns if "zlabel" in w or "zscale" in w], \
            warns


import contextlib  # noqa: E402
import warnings as _warnings  # noqa: E402


@contextlib.contextmanager
def _no_warn():
    out = []
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        yield out
    out.extend(str(w.message) for w in caught)


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("scheme,pid", [("s2color", "K1"),
                                        ("stcolor", "K1_stcolor")])
def test_the_key_gaps_follow_the_scheme(mode, scheme, pid):
    """K1 under s2color and stcolor (colorvar_key_truth.json K1,
    K1_stcolor): the plot region to the swatches and the axis to the
    title, as shares of the graph's smaller side, are twoway's under each
    scheme (stcolor's title sits further out by its larger axis title
    gap, tiny against s2color's minuscule)."""
    t = _key_truth()[pid]
    side = min(t["canvas"]["w"], t["canvas"]["h"])
    k = t["key"]
    sw = [c["cx"] for c in k["circles"] if c.get("fill") not in
          (None, "none")][0]
    ax = k["vlines"][0]["x1"]
    (title,) = [x for x in t["texts"] if x["rotate"]
                and x["x"] > t["plot"]["right"]]
    root = _layout_of(mode, [plot_for("scatter", _KEY_OPTS["K1"],
                                      yvar="mpg", xvar="weight")])
    spec = tp._spec([plot_for("scatter", _KEY_OPTS["K1"], yvar="mpg",
                              xvar="weight")], {"scheme": scheme}, {})
    root = _render_root(spec, mode)
    (fig,), (cell,) = _figs_and_cells(root)
    mpx = min(fig._dash_nominal_px) / (
        dr.OptionTranslator.size_ref_of(fig) / 4.0)
    band = cell._dash_key_band
    assert abs(fig.min_border_right + band / 2.0
               - (sw - t["plot"]["right"]) / side * mpx) <= 1.0
    mid = title["x"] - dr._DASH_KEY_TITLE_INK * title["size"]
    assert abs(cell._dash_key_title.x - band
               - (mid - ax) / side * mpx) <= 0.6



#: The ring(0) pairs (colorvar_key_truth.json P_bp_1, P_bp_7): twoway draws
#: the key inside the plot region where the outside key's texts are, at
#: the graph region's right (pos 1) or its swatches K1's gap from the plot
#: region's left (pos 7, bplacement(sw)).
@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("pos,place", [("1", "right"), ("7", "left")])
def test_a_ring0_key_is_a_key_cell_over_the_plot(mode, pos, place):
    t = _key_truth()
    # pos(1): the key's texts at K1's x; pos(7): its swatches from the
    # plot region's left by K1's gap (labels 757.1 = 390.8 + 220.9 +
    # 145.41, K1's swatch-to-label 3546.68 - 3401.27).
    k1 = [x["x"] for x in t["K1"]["texts"] if x["text"] == "1"
          and x["x"] > t["K1"]["plot"]["right"]][0]
    p1 = [x["x"] for x in t["P_bp_1"]["texts"] if x["text"] == "1"
          and x["y"] > 2000 and x["x"] > 3000][0]
    p7 = [x["x"] for x in t["P_bp_7"]["texts"] if x["text"] == "1"
          and x["y"] > 2000 and x["x"] < 1000][0]
    assert p1 == k1
    assert p7 - t["P_bp_7"]["plot"]["left"] == pytest.approx(
        k1 - t["K1"]["plot"]["right"], abs=0.1)
    go = {"clegend": "ring(0) position(%s)%s" % (
        pos, " bplacement(sw)" if pos == "7" else "")}
    root = _layout_of(mode, [plot_for("scatter", _KEY_OPTS["K1"],
                                      yvar="mpg", xvar="weight")], go)
    (fig,), (cell,) = _figs_and_cells(root)
    assert not _figure_keys(root)
    assert cell._dash_key_ring0 == place
    st = dict(cell.styles or {})
    assert st.get("position") == "absolute"
    assert st.get("pointer-events") == "none"
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    (row,) = [m for m in refs if "dash_key_row" in (m.tags or [])]
    # Over the figure: after it, the figure keeping its whole width.
    assert list(row.children) == [fig, cell]
    assert fig.min_border_right != getattr(fig, "_dash_key_border", "x")


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
def test_the_save_button_writes_the_key_too(mode):
    """The page's save button (the grid's one SaveTool, D67) exports the
    grid, the key row in it (measured 03nov2026 in headless Chrome: the
    grid's PNG export holds the key's swatches, axis and title).  A graph
    embedded as a cell of its own (_dash_name_save on its graph region
    box) swaps its figure's SaveTool, which writes the figure alone, for a
    PNG action of the key row."""
    from bokeh.models import CustomAction, GridPlot, SaveTool
    root = _layout_of(mode, [plot_for("scatter", {"colorvar": "price"},
                                      yvar="mpg", xvar="weight")])
    refs = root.references() if hasattr(root, "references") else [
        m for r in root.roots for m in r.references()]
    (row,) = [m for m in refs if "dash_key_row" in (m.tags or [])]
    grids = [m for m in refs if isinstance(m, GridPlot)
             and row in m.references()]
    assert grids
    saves = [t for g in grids for t in g.toolbar.tools
             if isinstance(t, SaveTool)]
    assert saves
    (reg,) = [m for m in refs if "dash_graph_region" in (m.tags or [])
              and list(getattr(m, "children", []) or []) == [row]]
    dr._dash_name_save(reg, "g1")
    fig = row.children[0]
    assert not [t for t in fig.toolbar.tools if isinstance(t, SaveTool)]
    (png,) = [t for t in fig.toolbar.tools if isinstance(t, CustomAction)
              and "dash_key_png" in (t.tags or [])]
    assert png.callback.args["grid"] is row
    assert png.callback.code == dr._DASH_KEY_PNG_SAVE_JS


# ---------------------------------------------------------------------------
# CV-15: clegend()'s altaxis, region(), bmargin(), bplacement(), subtitle(),
# note() and caption() drawn on the key cell (colorvar_key_truth.json P_*),
# nothing named.
# ---------------------------------------------------------------------------

_P_OPTS = {
    "P_alt": "altaxis",
    "P_reg": "region(fcolor(gs14) lcolor(red))",
    "P_bm": "bmargin(large)",
    "P_bm_m": "bmargin(medium)",
    "P_bm_v": "bmargin(vlarge)",
    "P_sub": 'subtitle("S") note("N") caption("C")',
    "P_bp_7": "ring(0) position(7) bplacement(sw)",
    "P_bp_7c": "ring(0) position(7)",
    "P_bp_n": "bplacement(north)",
    "P_bp_s": "bplacement(south)",
    "K1": "",
    "P_ti": 'title("Z")',
    "P_tbx": 'title("Z", box)',
    "P_tbx2": 'title("Price in dollars", box)',
    "P_tbx3": 'title("WWW", box)',
    "P_tbx4": 'title("iii", box)',
}


def _p_build(mode, pid):
    spec = tp._spec([plot_for("scatter", _KEY_OPTS["K1"], yvar="mpg",
                              xvar="weight")], {"scheme": "s2color"},
                    {"clegend": _P_OPTS[pid]})
    if mode == "saved":
        r, warns = tp._standalone(spec)
        root = r._last_layout_root
    else:
        root, warns = tp._served(spec)
    (fig,), (cell,) = _figs_and_cells(root)
    mpx = min(fig._dash_nominal_px) / (
        dr.OptionTranslator.size_ref_of(fig) / 4.0)
    return fig, cell, mpx, warns


def _line_fracs(rec):
    """twoway's axis line ends as shares of the plot region from its top
    and its foot."""
    pl = rec["plot"]
    v = rec["key"]["vlines"][0]
    h = pl["bottom"] - pl["top"]
    return ((min(v["y1"], v["y2"]) - pl["top"]) / h,
            (pl["bottom"] - max(v["y1"], v["y2"])) / h)


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", _MODES)
class TestClegendSuboptions:

    def test_altaxis(self, mode):
        rec = _key_truth()["P_alt"]
        fig, cell, mpx, warns = _p_build(mode, "P_alt")
        assert not [w for w in warns if "clegend" in w], warns
        # The axis before the swatches, its labels and title with it.
        assert cell._dash_key_side == "left"
        ax = rec["key"]["vlines"][0]["x1"]
        assert abs(fig.min_border_right + cell.min_border_left
                   - (ax - rec["plot"]["right"]) / 2880.0 * mpx) <= 1.0
        (title,) = [t for t in rec["texts"] if t["rotate"]
                    and t["x"] > rec["plot"]["right"]]
        mid = title["x"] - dr._DASH_KEY_TITLE_INK * title["size"]
        assert cell._dash_key_title.x == pytest.approx(
            -(ax - mid) / 2880.0 * mpx, abs=0.6)
        sw = rec["key"]["circles"][0]["cx"]
        assert cell._dash_keycell["mid"] == pytest.approx(
            cell._dash_key_band / 2.0)
        assert sw - ax == pytest.approx(85.51, abs=0.1)

    def test_region(self, mode):
        rec = _key_truth()["P_reg"]
        box = rec["regions"][1]
        assert box["fill"] == "#e0e0e0"
        fig, cell, mpx, warns = _p_build(mode, "P_reg")
        assert not [w for w in warns if "clegend" in w], warns
        reg = cell._dash_key_region
        assert reg["fill"].lower() == "#e0e0e0"
        assert reg["line"].lower() == "#ff0000"
        ins = (box["left"] - rec["plot"]["right"]) / 2880.0 * mpx
        assert reg["inset"] == pytest.approx(ins, abs=0.1)
        assert fig.min_border_right == round(ins)

    @pytest.mark.parametrize("pid", ("P_bm_m", "P_bm", "P_bm_v"))
    def test_bmargin(self, mode, pid):
        # Three sizes (medium, large, vlarge): twoway's line ends, its
        # axis and its swatches move with the margin, linearly.
        rec = _key_truth()[pid]
        fig, cell, mpx, warns = _p_build(mode, pid)
        assert not [w for w in warns if "clegend" in w], warns
        it, ib = cell._dash_keycell["inset"]
        want_t, want_b = _line_fracs(rec)
        assert abs(it - want_t) <= 0.012 and abs(ib - want_b) <= 0.012, (
            it, ib, want_t, want_b)
        s = mpx / 2880.0
        ax = rec["key"]["vlines"][0]["x1"]
        cx = rec["key"]["circles"][0]["cx"]
        band = cell._dash_key_band
        # The plot region to the axis line (the axis at the band's end).
        assert fig.min_border_right + (cell.min_border_left or 0) + band \
            == pytest.approx((ax - rec["plot"]["right"]) * s, abs=1.0)
        # Flipped (WP-42 CV-15): the swatches moved away from the axis;
        # twoway moves them toward it, across it at vlarge (P_bm_v).
        assert band - cell._dash_keycell["mid"] == pytest.approx(
            (ax - cx) * s, abs=1.0)
        # Drawn whole where they cross the axis: over the frame.
        (sw,) = [r for r in cell.renderers
                 if r.data_source is cell._dash_keycell["src"]]
        assert sw.level == "overlay"

    def test_subtitle_note_caption(self, mode):
        rec = _key_truth()["P_sub"]
        fig, cell, mpx, warns = _p_build(mode, "P_sub")
        assert not [w for w in warns if "clegend" in w], warns
        # Flipped (WP-42 CV-15): Labels in the cell's foot panel, which
        # raised its frame's foot 13 px above the plot region's; Text
        # glyphs over the frame, the cell's panels left to its axis.
        texts = {r.data_source.data["text"][0]: r
                 for r in cell._dash_key_texts}
        assert set(texts) == {"S", "N", "C"}
        assert all(r in cell.renderers and r.level == "overlay"
                   for r in texts.values())
        assert not cell.below and not cell.above
        assert texts["S"].glyph.text_align == "center"
        it, ib = cell._dash_keycell["inset"]
        want_t, want_b = _line_fracs(rec)
        assert abs(it - want_t) <= 0.012 and abs(ib - want_b) <= 0.012
        rng = cell._dash_keycell["range"]
        # S above the line, N then C below it.
        lo, hi = cell._dash_key_axis.bounds
        y = {k: r.data_source.data["y"][0] for k, r in texts.items()}
        assert y["S"] > hi and y["N"] < lo
        assert y["C"] < y["N"]

    @pytest.mark.parametrize("pid,base", (("P_bp_7", "P_bp_7c"),
                                          ("P_bp_n", "K1"),
                                          ("P_bp_s", "K1")))
    def test_bplacement_is_silent(self, mode, pid, base):
        # twoway draws the same key with bplacement() as without it, at
        # ring(0) and beside the plot (P_bp_7 against P_bp_7c; P_bp_n and
        # P_bp_s against K1): every text where its control's is.
        tw = _key_truth()
        assert [(t["text"], t["x"], t["y"]) for t in tw[pid]["texts"]] == \
            [(t["text"], t["x"], t["y"]) for t in tw[base]["texts"]]
        assert tw[pid]["key"] == tw[base]["key"]
        fig, cell, mpx, warns = _p_build(mode, pid)
        assert not [w for w in warns if "clegend" in w], warns
        fig0, cell0, _m, _w = _p_build(mode, base)
        for a, b in ((fig, fig0), (cell, cell0)):
            assert (a.width, a.min_border_right, a.min_border_left) == \
                (b.width, b.min_border_right, b.min_border_left)
        assert cell._dash_keycell["mid"] == cell0._dash_keycell["mid"]
        assert getattr(cell, "_dash_key_ring0", None) == \
            getattr(cell0, "_dash_key_ring0", None)
