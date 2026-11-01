"""by()'s layout drawn as twoway lays it out (WP-41 section 41-05).

The truth is test/fixtures/by_layout_truth.json
(scripts/extract_by_layout_truth.do): per probe Y01-Y21, twoway's rc,
first error line, SVG canvas, rects and texts.  Measured:

- BY-4: ``by(foreign, total style(default) compact)`` and ``total
  compact style(default)`` export the same rects as ``by(foreign,
  total)`` (style() wins over compact); compact draws each plot region
  and each label box with the foreground line (#000000).
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_remainder as tr  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_layout_truth.json")
_MODES = ("saved", "served")
_T = None


def _truth():
    global _T
    if _T is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _T = json.load(fh)
    return _T


def _probe(pid):
    return _truth()["probes"][pid]


def _built(mode, go, plots=None, scheme="stcolor"):
    """``(grid, roots, notes)`` of one by() graph."""
    spec = tk._spec([tk._graph("g", plots or tk._ONE, go)], scheme=scheme)
    roots, notes, _o = tk._build(mode, spec, data=tr._data())
    grids = list(tk._grids(roots).values())
    return (grids[0] if grids else None), roots, notes


def _label_boxes(roots):
    from bokeh.models import ColorBar
    return [m for r in roots for m in r.references()
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box"]


def _geometry(grid):
    """What compact changes: the grid's spacing and each panel's drawn
    axes and borders."""
    return (tuple(grid.spacing),
            [(tk._axis_drawn(p, "x"), tk._axis_drawn(p, "y"),
              p.min_border_left, p.min_border_right, p.min_border_top,
              p.min_border_bottom) for p in tk._panels(grid)])


class TestTheFixture:
    def test_meta(self):
        assert sorted(_truth()["_meta"]) == ["born_date", "dash_commit",
                                             "extracted", "source",
                                             "stata_version"]

    def test_style_wins_in_twoway(self):
        p = _truth()["probes"]
        assert p["Y02"]["rects"] == p["Y01"]["rects"]
        assert p["Y03"]["rects"] == p["Y01"]["rects"]


class TestTheCompactWord:
    @pytest.mark.parametrize("tok,want", [
        ("compact", True), ("com", True), ("compa", True), ("co", False),
        ("compacts", False), ("Compact", False), ("", False)])
    def test_spellings(self, tok, want):
        """The grammar's minimum is com (_DASH_BY_GRAMMAR)."""
        assert dr._dash_by_is_compact(tok) is want

    @pytest.mark.parametrize("subs,want", [
        ("total style(default) compact", "total style(default)"),
        ("total comp style(default)", "total style(default)"),
        ("compact style(econ)", None),
        ("total compact", "total compact"),
        ("style(compact) compact", "compact compact")])
    def test_routed(self, subs, want):
        spec = tk._spec([tk._graph("g", tk._ONE, {"by": "foreign, " + subs})])
        go = dr._dash_bystyle_route(spec)["graphs"][0]["graph_options"]
        rest = go["by"].partition(",")[2].strip()
        if want is None:
            assert "compact" not in rest and "plotregion" in go
        else:
            assert rest == want


@pytest.mark.parametrize("mode", _MODES)
class TestCompact:
    @pytest.mark.parametrize("pid", ["Y02", "Y03"])
    def test_style_wins(self, mode, pid):
        """compact beside style(default) is drawn as style(default)."""
        base, _r, _n = _built(mode, {"by": "foreign, total"})
        subs = {"Y02": "total style(default) compact",
                "Y03": "total compact style(default)"}[pid]
        got, _r, _n = _built(mode, {"by": "foreign, " + subs})
        assert _geometry(got) == _geometry(base)

    def test_compact_outlines(self, mode):
        """Y04 (s2color): every plot region and label box outline is the
        foreground line (#000000); the plot region keeps its width."""
        fg = dr.SchemeParser("s2color").style_bundle(
            "line", "foreground")["line"]
        assert fg == "#000000" and {
            r["stroke"] for r in _probe("Y04")["rects"]
            if r["fill"] == "none" and r["sw"] == 4.9 and r["x"] > 300} == {fg}
        grid, roots, _n = _built(mode, {"by": "foreign, compact"},
                                 scheme="s2color")
        plain, _r, _n = _built(mode, {"by": "foreign"}, scheme="s2color")
        panels = tk._panels(grid)
        assert {str(p.outline_line_color).lower() for p in panels} == {fg}
        assert [p.outline_line_width for p in panels] == [
            p.outline_line_width for p in tk._panels(plain)]
        assert {str(b.bar_line_color).lower()
                for b in _label_boxes(roots)} == {fg}

    def test_bystyle_compact_fixture(self, mode):
        """by_remainder_truth.json bystyle_compact: style(compact) draws
        the black plot region and label box outlines."""
        probe = tr._probe("bystyle_compact")
        assert {r["stroke"] for r in probe["rects"]
                if r["fill"] == "none" and r["x"] > 200} == {"#000000"}
        grid, roots, _n = _built(mode, {"by": "rep78, style(compact)"},
                                 plots=tk._TWO, scheme="s2color")
        assert {str(p.outline_line_color).lower()
                for p in tk._panels(grid)} == {"#000000"}
        assert {str(b.bar_line_color).lower()
                for b in _label_boxes(roots)} == {"#000000"}


# ---------------------------------------------------------------------------
# Headless Chrome: each figure's box, frame and label-box strip (page px)
# and the by() grid's box, at load (both modes' pages, as
# test_by_axes_keys_browser.py draws them).
# ---------------------------------------------------------------------------
_LAYOUT_JS = r"""
<script>
function rect(el){const r=el.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom];}
function state() {
  const figs = [];
  let grid = null;
  const visit = (v, gb) => {
    if (!v) return;
    if (v.model && v.model.type === 'GridBox') gb = v;
    if (v.frame && v.renderer_views && v.canvas_view) {
      const cr = v.canvas_view.el.getBoundingClientRect();
      const f = v.frame.bbox;
      const strips = [], titles = [];
      for (const [m, rv] of v.renderer_views) {
        if (!m.visible) continue;
        if (m.type === 'ColorBar' && m.name === 'dash_by_label_box' && rv.bbox) {
          const b = rv.bbox;
          strips.push({orient: m.orientation,
                       box: [cr.left + b.x0, cr.top + b.y0, cr.left + b.x1, cr.top + b.y1]});
        }
        if (m.type === 'Title' && m.text) {
          rv.compute_geometry();
          const r = rv._rect; if (!r) continue;
          const a = r.angle || 0, ca = Math.cos(a), sa = Math.sin(a);
          const xs = [], ys = [];
          for (const lx of [-r.anchor.x * r.width, (1 - r.anchor.x) * r.width])
            for (const ly of [-r.anchor.y * r.height, (1 - r.anchor.y) * r.height]) {
              xs.push(r.sx + lx * ca - ly * sa + cr.left);
              ys.push(r.sy + lx * sa + ly * ca + cr.top);
            }
          titles.push({text: m.text, box: [Math.min(...xs), Math.min(...ys),
                                           Math.max(...xs), Math.max(...ys)]});
        }
      }
      const axes = [];
      for (const [m, rv] of v.renderer_views) {
        if (!m.visible || !(m.type || '').endsWith('Axis') || !rv.bbox) continue;
        const b = rv.bbox;
        if (!(b.width > 0)) continue;
        axes.push([cr.left + b.x0, cr.top + b.y0, cr.left + b.x1, cr.top + b.y1]);
      }
      let gp = v.parent;
      while (gp != null && !(gp.model != null && gp.model.type === 'GridPlot')) gp = gp.parent;
      figs.push({name: v.model.name || '', el: rect(v.el),
                 gridplot: gp ? rect(gp.el) : null,
                 frame: [cr.left + f.x0, cr.top + f.y0, cr.left + f.x1, cr.top + f.y1],
                 strips, titles, axes,
                 ol: v.model.outline_line_width,
                 alw: ((v.model.left || []).concat(v.model.below || []).find(
                   (a) => (a.type || '').endsWith('Axis')) || {}).axis_line_width,
                 grid: gb ? rect(gb.el) : null});
    }
    for (const c of (v.child_views || [])) visit(c, gb);
  };
  for (const v of Object.values(Bokeh.index)) visit(v, null);
  return figs;
}
addEventListener('load', () => setTimeout(() => {
  parent.postMessage('DASHPROBE' + JSON.stringify(
    {W: innerWidth, wide: state()}), '*');
}, 3000));
</script>
"""


def _measure(mode, go, plots=None, widths=(1400,), scheme="stcolor"):
    """``{width: [figure records]}`` of one by() graph in Chrome."""
    import test_by_axes_keys_browser as kb
    spec = tk._spec([tk._graph("g1", plots or tk._ONE, go, title=False)],
                    scheme=scheme)
    got = kb._measure(mode, spec, _LAYOUT_JS, widths)
    return {w: got[w]["wide"] for w in widths}


def _panels_of(figs):
    """The panel records (unnamed figures)."""
    return [f for f in figs if not f["name"]]


# ---------------------------------------------------------------------------
# BY-18: style(combine)'s regions, labels and titles beside the panels,
# aspectratio()'s plot regions and a smaller graph margin.
# Measured (by_layout_truth.json, stcolor 5400 x 3240, 1 unit = 32.4):
# Y10 draws combine's array 2.2 units in from the graph (71.21) and each
# panel's graph region 1.76 units outside its plot region on the side no
# axis takes (57.04); Y11/Y12 a strip 33.07 units wide (the label box's
# two margins, 138.38 less the 105.13 font) as tall as the plot region,
# the label horizontal at its middle; Y13 the title T right of the
# panels, centred on their plot regions; Y14 square plot regions
# (2196.62 x 2196.62); Y15 margin(small) and Y16 margin(zero) an array
# 2.3 and 3.5 units larger on every side.
# ---------------------------------------------------------------------------
_U = 32.4


def _combine_figs(mode, width=1400):
    return _panels_of(_measure(mode, {"by": "rep78, style(combine)"},
                               tk._TWO, (width,))[width])


@pytest.mark.parametrize("mode", _MODES)
class TestCombine:
    def test_fixture(self, mode):
        rects = _probe("Y10")["rects"]
        assert abs(rects[3]["x"] / _U - dr._DASH_BY_COMBINE_INSET_RS) < 0.01
        right = 5400 - 57.04
        assert abs(57.04 / _U - dr._DASH_BY_COMBINE_PANEL_MARGIN_RS) < 0.01
        assert right > 0

    @pytest.mark.release
    def test_regions(self, mode):
        """The array is inset by combine's 2.2 units plus a panel's own
        1.76 (a share of the cell's width, units of its short side; the
        grid's padding on every side), and neighbouring panels are two
        panel margins apart."""
        g0, _r, _n = _built(mode, {"by": "rep78, style(combine)"},
                            plots=tk._TWO)
        pct = (dr._DASH_BY_COMBINE_INSET_RS
               + dr._DASH_BY_COMBINE_PANEL_MARGIN_RS) * 0.6
        assert g0.styles["padding"] == " ".join(["%.4g%%" % pct] * 4)
        figs = _combine_figs(mode)
        g = figs[0]["gridplot"]
        W = g[2] - g[0]
        share = 4.5 / 7.5
        want = (dr._DASH_BY_COMBINE_INSET_RS
                + dr._DASH_BY_COMBINE_PANEL_MARGIN_RS) * share / 100.0 * W
        left = min(f["el"][0] for f in figs) - g[0]
        assert abs(left - want) <= 2, (left, want)
        unit = dr.OptionTranslator.PT_PER_RS * dr.OptionTranslator.PX_PER_PT
        gap = sorted(f["el"][0] for f in figs if abs(f["el"][1] - figs[0]["el"][1]) < 1)
        row = [f for f in figs if abs(f["el"][1] - figs[0]["el"][1]) < 1]
        row.sort(key=lambda f: f["el"][0])
        got = row[1]["el"][0] - row[0]["el"][2]
        assert abs(got - 2 * dr._DASH_BY_COMBINE_PANEL_MARGIN_RS * unit) <= 2, (
            got, gap)

    def test_no_note(self, mode):
        _g, _r, notes = _built(mode, {"by": "rep78, style(combine)"},
                               plots=tk._TWO)
        assert [n for n in notes if "style(combine)" in n] == []


def _strip(fig):
    from bokeh.models import ColorBar
    for side in ("left", "right", "above", "below"):
        for m in getattr(fig, side):
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box":
                return side, m
    return None, None


@pytest.mark.parametrize("mode", _MODES)
class TestBeside:
    @pytest.mark.parametrize("pid,where", [("Y11", "right"), ("Y12", "left")])
    def test_labels_beside(self, mode, pid, where):
        """A vertical one-colour strip on the panel's right (3 o'clock)
        or left (9), as wide as the box's two margins (Y11: 33.07 of the
        box's 138.38 against its 105.13 font), the label centred on it."""
        clock = {"Y11": 3, "Y12": 9}[pid]
        grid, _r, _n = _built(mode, {"by": "foreign",
                                     "subtitle": ", position(%d)" % clock})
        plain, _r, _n = _built(mode, {"by": "foreign"})
        _s0, top = _strip(tk._panels(plain)[0])
        font = float(str(top.major_label_text_font_size).rstrip("px"))
        for p in tk._panels(grid):
            side, box = _strip(p)
            assert side == where and box.orientation == "vertical"
            assert abs(box.width - (top.height - font)) <= 1, (box.width,
                                                               top.height)
            assert list(box.ticker.ticks) == [0.5]
            assert box.major_label_text_align == "center"

    def test_title_beside(self, mode):
        for pos, name, where in (("3", "dash_by_rtext", "right"),
                                 ("9", "dash_by_ltext", "left")):
            grid, _r, _n = _built(mode, {
                "by": 'foreign, title("T", position(%s))' % pos})
            cell = tk._cell(grid, name)
            assert cell is not None, name
            assert tk._cell_side(grid, cell) == where
            assert int(cell[3]) == 1
            axis = (cell[0].right if where == "right" else cell[0].left)[0]
            assert list(axis.major_label_overrides.values()) == ["T"]
            # A renderer, so the build logs no W-1000 for the cell.
            assert [m.name for m in cell[0].center
                    if type(m).__name__ == "Span"] == ["dash_by_anchor"]
            assert tk._cell(grid, "dash_by_head") is None or not str(
                tk._cell(grid, "dash_by_head")[0].title.text or "")

    @pytest.mark.release
    def test_title_centred_on_the_plot_regions(self, mode):
        figs = _measure(mode, {"by": 'foreign, title("T", position(3))'})[1400]
        panels = _panels_of(figs)
        (cell,) = [f for f in figs if f["name"] == "dash_by_rtext"]
        (ax,) = cell["axes"]
        mid = (panels[0]["frame"][1] + panels[0]["frame"][3]) / 2.0
        assert ax[0] >= max(p["el"][2] for p in panels) - 1
        assert abs((ax[1] + ax[3]) / 2.0 - mid) <= 2, (ax, mid)
        # The text's column is as wide as the text, not a panel's share
        # (twoway's panels narrow by 71.6 of 2196.6 units for T: Y13
        # against Y11d); the two panels keep most of the width.
        W = panels[0]["grid"][2] - panels[0]["grid"][0]
        assert sum(p["el"][2] - p["el"][0] for p in panels) > 0.8 * W


@pytest.mark.parametrize("mode", _MODES)
class TestFrameAspect:
    def test_the_hook(self, mode):
        grid, _r, _n = _built(mode, {"by": "foreign", "aspectratio": "1"})
        p = tk._panels(grid)[0]
        cbs = [c for c in p.js_property_callbacks.get("change:inner_width", [])
               if c.code == dr._DASH_BY_FIT_JS]
        assert len(cbs) == 1 and cbs[0].args["frame_ar"] == 1.0


#: The default tier keeps one Chrome case per item, saved at 1000 px
#: (REVIEW R3-39); the rest are release.
_SQUARE_CASES = [pytest.param(m, w, marks=() if (m, w) == ("saved", 1000)
                              else pytest.mark.release)
                 for m in _MODES for w in (1400, 1000, 760)]


class TestFrameAspectInChrome:
    @pytest.mark.parametrize("mode,width", _SQUARE_CASES)
    def test_plot_regions_square(self, mode, width):
        """Y14: twoway's plot regions are square at aspectratio(1)."""
        a = _probe("Y14")["rects"][3]
        assert a["w"] == a["h"]
        figs = _panels_of(_measure(mode, {"by": "foreign",
                                          "aspectratio": "1"},
                                   widths=(width,))[width])
        assert len(figs) == 2
        for f in figs:
            fr = f["frame"]
            assert abs((fr[2] - fr[0]) - (fr[3] - fr[1])) <= 1, fr


@pytest.mark.release
@pytest.mark.parametrize("mode", _MODES)
class TestSmallMargin:
    @pytest.mark.parametrize("pid,margin,units", [
        ("Y15", "small", 2.3), ("Y16", "zero", 3.5)])
    def test_array_grows(self, mode, pid, margin, units):
        """The array is larger on every side by the scheme's graph margin
        (3.5) less the one given (small 1.2, zero 0)."""
        base = _probe("Y11d")["rects"][3]
        got = _probe(pid)["rects"][3]
        assert abs((base["x"] - got["x"]) / _U - units) < 0.02
        plain = _panels_of(_measure(mode, {"by": "foreign"})[1400])
        small = _panels_of(_measure(mode, {
            "by": "foreign, graphregion(margin(%s))" % margin})[1400])
        W = plain[0]["grid"][2] - plain[0]["grid"][0]
        want = units * 0.6 / 100.0 * W
        dl = min(f["frame"][0] for f in plain) - min(f["frame"][0] for f in small)
        dr_ = max(f["frame"][2] for f in small) - max(f["frame"][2] for f in plain)
        dt = min(f["frame"][1] for f in plain) - min(f["frame"][1] for f in small)
        # Flipped (DECISIONS D66, the maintainer's ruling of 01nov2026):
        # 2 px at the 96-px size; the graph is one picture, its axes'
        # room scales with the drawn width, and the tolerance with it.
        k = W / 720.0 * 4.5 / 4.0
        for d in (dl, dr_, dt):
            # 2.5 px at the 96-px size (margin(zero): 24.4 of 29.4 px).
            assert abs(d - want) <= 2.5 * k, (dl, dr_, dt, want)


# ---------------------------------------------------------------------------
# VF-6: every panel in a row has the same plot-region width.  Measured
# (by_layout_truth.json Y17, scatter price weight, ylabel(, format(%15.2fc))
# by(rep78)): twoway's plot regions are equally wide in every column, the
# shared y labels outside the first column's region.
# ---------------------------------------------------------------------------
# The test data hold no price, so mpg stands in: the formatted labels
# ("40.00") still widen the first column's left side.
_Y17 = ([tk._p("scatter")],
        {"by": "rep78", "ylabel": ", format(%15.2fc)"})

_EQUAL_CASES = [pytest.param(m, w, marks=() if (m, w) == ("saved", 1000)
                             else pytest.mark.release)
                for m in _MODES for w in (1400, 1000, 760)]


def _rows_of(panels):
    rows = {}
    for f in panels:
        rows.setdefault(round(f["frame"][1]), []).append(f)
    return list(rows.values())


class TestEqualPanels:
    def test_fixture(self):
        ws = sorted({r["w"] for r in _probe("Y17")["rects"][3:]
                     if r["fill"] == "#ffffff" and r["h"] > 500})
        assert ws and max(ws) - min(ws) < 1, ws

    @pytest.mark.parametrize("mode,width", _EQUAL_CASES)
    def test_frames_equal_across_a_row(self, mode, width):
        plots, go = _Y17
        figs = _panels_of(_measure(mode, go, plots, (width,))[width])
        assert len(figs) == 5
        for row in _rows_of(figs):
            w = [f["frame"][2] - f["frame"][0] for f in row]
            assert max(w) - min(w) <= 1, w

    @pytest.mark.parametrize("mode", _MODES)
    def test_axis_cells(self, mode):
        """One dash_by_yaxis_<r> cell per panel row, on the row's shared
        y range, left of the panels; no panel draws its own y axis."""
        plots, go = _Y17
        grid, _r, _n = _built(mode, go, plots)
        panels = tk._panels(grid)
        cells = [tk._cell(grid, "dash_by_yaxis_%d" % r) for r in (0, 1)]
        assert all(c is not None for c in cells), cells
        for r, c in enumerate(cells):
            assert tk._cell_side(grid, c) == "left"
            row = [p for p in panels if tk._axis_drawn(p, "x") is not None]
            assert c[0].y_range is panels[3 * r].y_range
            (ax,) = c[0].left
            assert ax.formatter is not None
        assert not any(a.visible for p in panels for a in p.yaxis)

    @pytest.mark.release
    @pytest.mark.parametrize("mode", _MODES)
    def test_stacked_view_restores(self, mode):
        """Stacked (400 px), each panel shows its own y axis again and the
        axis cells hide."""
        plots, go = _Y17
        figs = _measure(mode, go, plots, (400,))[400]
        panels = _panels_of(figs)
        assert all(f["axes"] for f in panels)
        assert not [f for f in figs if f["name"].startswith("dash_by_yaxis")
                    and f["el"][2] - f["el"][0] > 0]
# GW-5: xoverhangs.  Measured (by_layout_truth.json): Y18 (by(foreign)
# xoverhangs) exports Y19's rects (twoway ignores overhangs under by());
# sizing_truth.json overhang_x0/x1 a long first label moving the left edge
# in by 138 units and the right by 80 of 3,960.
# ---------------------------------------------------------------------------
_LONG = '2000 "a very long label" 5000'


def _figures(mode, go):
    """Every plot figure of one graph (its panels under by())."""
    spec = tk._spec([tk._graph("g1", tk._ONE, go, title=False)])
    roots, _n, _o = tk._build(mode, spec, data=tr._data())
    return [m for r in roots for m in r.references()
            if type(m).__name__ == "figure"]


@pytest.mark.parametrize("mode", _MODES)
class TestOverhangs:
    def test_ignored_under_by(self, mode):
        p = _truth()["probes"]
        assert p["Y18"]["rects"] == p["Y19"]["rects"]
        a = _figures(mode, {"by": "foreign", "xlabel": _LONG,
                            "xoverhangs": "xoverhangs"})
        b = _figures(mode, {"by": "foreign", "xlabel": _LONG})
        sides = ("min_border_left", "min_border_right", "min_border_top",
                 "min_border_bottom")
        assert [[getattr(f, s) for s in sides] for f in a] == \
            [[getattr(f, s) for s in sides] for f in b]

    def test_end_labels_per_side(self, mode):
        """Each side follows its own end label: the long first label
        raises the left, the one-letter last label leaves the right."""
        (f,) = _figures(mode, {"xlabel": '2000 "a very long label" 3000 "b" '
                                         '5000 "c"',
                               "xoverhangs": "xoverhangs"})
        (g,) = _figures(mode, {"xlabel": '2000 "a very long label" 3000 "b" '
                                         '5000 "c"'})
        assert (f.min_border_left or 0) > (g.min_border_left or 5)
        assert (f.min_border_right or 5) == (g.min_border_right or 5) or \
            (f.min_border_right or 0) < (f.min_border_left or 0) / 4


@pytest.mark.parametrize("mode", _MODES)
class TestTheOuterYAxisSize:
    """The row's outer y axis cell (WP-41 VF-6) draws its tick labels at
    the panels' size: by()'s multiplier (0.85 for two panels) applies to
    it as to the panels, as twoway draws one size for every tick label
    (figure_geometry_truth.json G_by_stcolor: 9.57 pt, x and y alike)."""

    def test_the_tick_labels_match_the_panels(self, mode):
        grid, _r, _n = _built(mode, {"by": "foreign"})
        panels = tk._panels(grid)
        cells = [c[0] for c in grid.children
                 if str(getattr(c[0], "name", "") or "").startswith(
                     "dash_by_yaxis_")]
        assert cells
        want = panels[0].xaxis[0].major_label_text_font_size
        for cell in cells:
            assert cell.left[0].major_label_text_font_size == want


@pytest.mark.parametrize("mode", _MODES)
class TestCompactPanels:
    """WP-41 41-05 pair 1: by(foreign, compact) under s2color.  Measured
    (figure_geometry_truth.json P1, 3960 x 2880): the plot regions touch
    (353.80 .. 2106.47, 2106.47 .. 3859.02) and each is outlined at the
    axis lines' width (stroke-width 4.90 for both, 1.73 px at 1400)."""

    def test_the_panels_touch_and_are_outlined_as_the_axes(self, mode):
        figs = _panels_of(_measure(mode, {"by": "foreign, compact"},
                                   scheme="s2color")[1400])
        assert len(figs) == 2
        a, b = sorted(figs, key=lambda f: f["frame"][0])
        assert abs(b["frame"][0] - a["frame"][2]) <= 1, (a, b)
        k = 1400.0 / 3960.0
        for f in figs:
            assert f["ol"] == pytest.approx(4.90 * k, abs=0.1), f
            assert f["alw"] == pytest.approx(4.90 * k, abs=0.1), f
