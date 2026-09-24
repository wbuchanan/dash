"""test_geometry.py — S10: figure geometry and layout sizing.

Measured: no generated dashboard contained a figure ``width``, ``height``,
``frame_width`` or ``aspect_ratio`` — 67 Figure objects across 10 dashboards,
every one emitted with ``sizing_mode="stretch_width"`` and Bokeh's default
height. There was no way, by option, by scheme or by data, for a user to
influence plot proportions.

Ground truth is ``test/fixtures/geometry_truth.json``, measured in Stata:

  * ``xsize()``/``ysize()`` are **inches** — triple-confirmed via the EPS
    bounding box (``xsize(6)`` → 432pt = 6in), the ``.gph`` header, and a PNG
    export.
  * They are **independent**: ``xsize(9)`` alone under ``stcolor`` gives
    4.5 × 9.
  * **Stata's ``aspectratio()`` is height/width. Bokeh's ``aspect_ratio`` is
    width/height.** dash passed the value straight through, inverting every
    request. Measured on a 600×600 export: ``aspectratio(0.25)`` gives a plot
    region 542×152, i.e. h/w = 0.28.
  * ``aspectratio()`` constrains the **plot region** only; it does not change
    the graph size.
"""
import json
import math
import os
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer, SchemeParser

from conftest import make_spec, make_data_json

_FIXTURE = os.path.join(_HERE, "fixtures", "geometry_truth.json")


@pytest.fixture(scope="module")
def truth():
    if not os.path.exists(_FIXTURE):
        pytest.skip("geometry_truth.json is missing")
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _df(n=20):
    return pd.DataFrame({
        "mpg": np.linspace(12, 41, n),
        "weight": np.linspace(1760, 4840, n),
        "price": np.linspace(3291, 15906, n),
    })


class _FakeFig:
    """Minimal stand-in carrying only the property the layout reads."""

    def __init__(self, ratio):
        self.aspect_ratio = ratio


_SCATTER = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}]


def _render(gopts=None, build=None, plots=None, n_graphs=1):
    plots = plots or _SCATTER
    spec = make_spec(plots)
    if gopts:
        spec["graphs"][0]["graph_options"].update(gopts)
    for i in range(1, n_graphs):
        g = {"plots": plots,
             "graph_options": dict({"name": f"g{i + 1}"}, **(gopts or {})),
             "if_expr": "", "in_expr": ""}
        spec["graphs"].append(g)
    if n_graphs > 1:
        spec["build_options"]["registry"] = " ".join(
            f"g{i + 1}" for i in range(n_graphs))
    if build:
        spec["build_options"].update(build)
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df()), f)
    dr = DashRenderer(sp, dp, op)
    html_text = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr, html_text


def _ratio(fig):
    """The figure's width/height ratio, however it is expressed."""
    if fig.aspect_ratio:
        return float(fig.aspect_ratio)
    if fig.width and fig.height:
        return float(fig.width) / float(fig.height)
    if fig.frame_width and fig.frame_height:
        return float(fig.frame_width) / float(fig.frame_height)
    return None


# ======================================================================
# xsize() / ysize()
# ======================================================================

class TestExplicitSize:

    def test_xsize_and_ysize_set_the_ratio(self, truth):
        dr, _ = _render({"xsize": "6", "ysize": "4"})
        fig = dr.figures["g1"]
        assert _ratio(fig) == pytest.approx(1.5), (
            f"xsize(6) ysize(4) should be 1.5 wide-to-tall, got {_ratio(fig)}"
        )

    @pytest.mark.parametrize("xs,ys,want", [
        ("6", "4", 1.5), ("10", "2", 5.0), ("4", "8", 0.5),
    ])
    def test_measured_fixture_cases(self, xs, ys, want):
        dr, _ = _render({"xsize": xs, "ysize": ys})
        assert _ratio(dr.figures["g1"]) == pytest.approx(want)

    def test_xsize_alone_keeps_the_scheme_ysize(self, truth):
        """Measured: xsize(9) alone under stcolor gives 4.5 x 9."""
        dr, _ = _render({"xsize": "9"}, build={"scheme": "stcolor"})
        fig = dr.figures["g1"]
        assert _ratio(fig) == pytest.approx(9.0 / 4.5, rel=1e-6)

    def test_ysize_alone_keeps_the_scheme_xsize(self):
        dr, _ = _render({"ysize": "9"}, build={"scheme": "stcolor"})
        assert _ratio(dr.figures["g1"]) == pytest.approx(7.5 / 9.0, rel=1e-6)

    @pytest.mark.parametrize("bad", ["0", "-3", "notanumber", ""])
    def test_an_unusable_size_is_reported_not_applied(self, bad):
        """Stata returns r(198) for xsize(0) and xsize(-3)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr, _ = _render({"xsize": bad, "ysize": "4"})
        fig = dr.figures["g1"]
        assert fig is not None
        if bad != "":
            assert any("xsize" in str(w.message) for w in caught), (
                f"xsize({bad}) was accepted silently"
            )


# ======================================================================
# The scheme's graphsize
# ======================================================================

class TestSchemeGraphsize:

    def test_with_no_option_the_ratio_comes_from_the_scheme(self, truth):
        dr, _ = _render(build={"scheme": "stcolor"})
        assert _ratio(dr.figures["g1"]) == pytest.approx(7.5 / 4.5, rel=1e-6)

    @pytest.mark.parametrize("scheme,want", [
        ("stcolor", 7.5 / 4.5),
        ("s2color", 5.5 / 4.0),
        ("economist", 1.0),
        ("sj", 3.575 / 2.6),
    ])
    def test_every_translated_scheme_carries_its_own_size(self, truth, scheme,
                                                          want):
        sp = SchemeParser(scheme)
        if not (sp.graphsize_x and sp.graphsize_y):
            # A failure, not a skip: this test says the scheme carries its
            # own size, and each of the four does (measured 24sep2026 --
            # stcolor 7.5 x 4.5, s2color 5.5 x 4, economist 2.2 x 2.2, sj
            # 3.575 x 2.6).  A skip here passed a scheme that lost it.
            pytest.fail(f"{scheme} records no graphsize")
        dr, _ = _render(build={"scheme": scheme})
        assert _ratio(dr.figures["g1"]) == pytest.approx(want, rel=1e-3)

    def test_two_schemes_with_different_sizes_differ(self):
        a, _ = _render(build={"scheme": "stcolor"})
        b, _ = _render(build={"scheme": "economist"})
        assert _ratio(a.figures["g1"]) != pytest.approx(
            _ratio(b.figures["g1"]))

    def test_the_scheme_values_match_stata(self, truth):
        """SchemeParser must agree with Stata's own defaults."""
        compared, sizeless = [], []
        for name, rec in truth["scheme_defaults"].items():
            sp = SchemeParser(name)
            if sp.graphsize_x is None:
                sizeless.append(name)
                continue
            assert sp.graphsize_x == pytest.approx(rec["xsize"]), name
            assert sp.graphsize_y == pytest.approx(rec["ysize"]), name
            compared.append(name)
        # The `continue' passed a scheme that lost its size, and every one
        # of them at once.  Measured 24sep2026: the fixture records Stata's
        # size for 14 schemes and dash carries a size for all 14.
        assert not sizeless and len(compared) == 14, (compared, sizeless)


# ======================================================================
# aspectratio() — inverted
# ======================================================================

class TestAspectRatio:

    def test_stata_aspectratio_is_height_over_width(self, truth):
        """Stata's aspectratio = h/w; Bokeh's aspect_ratio = w/h.

        dash passed the value straight through, so every request came out
        upside down: aspectratio(0.5) asked for a SHORT WIDE plot region and
        dash drew a TALL NARROW one.
        """
        assert "height / width" in truth["semantics"]["aspectratio"]
        dr, _ = _render({"aspectratio": "0.5"})
        fig = dr.figures["g1"]
        assert _ratio(fig) == pytest.approx(2.0), (
            f"aspectratio(0.5) means half as tall as wide, i.e. a Bokeh "
            f"aspect_ratio of 2.0; got {_ratio(fig)}"
        )

    @pytest.mark.parametrize("stata_ar,bokeh_ratio", [
        ("0.25", 4.0), ("1", 1.0), ("2", 0.5), ("4", 0.25),
    ])
    def test_the_reciprocal_is_taken(self, stata_ar, bokeh_ratio):
        dr, _ = _render({"aspectratio": stata_ar})
        assert _ratio(dr.figures["g1"]) == pytest.approx(bokeh_ratio)

    def test_aspectratio_beats_the_scheme(self):
        dr, _ = _render({"aspectratio": "1"}, build={"scheme": "stcolor"})
        assert _ratio(dr.figures["g1"]) == pytest.approx(1.0)

    def test_explicit_sizes_beat_aspectratio(self):
        """A documented precedence, so the two cannot silently fight."""
        dr, _ = _render({"xsize": "6", "ysize": "4", "aspectratio": "3"})
        assert _ratio(dr.figures["g1"]) == pytest.approx(1.5)

    @pytest.mark.parametrize("bad", ["0", "-1", "abc"])
    def test_an_unusable_aspectratio_is_reported(self, bad):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr, _ = _render({"aspectratio": bad})
        assert dr.figures["g1"] is not None
        assert any("aspectratio" in str(w.message) for w in caught)


# ======================================================================
# Responsiveness must survive
# ======================================================================

class TestResponsiveness:
    """BR-10.3: the abstract's headline claim."""

    def test_a_sized_figure_is_still_responsive(self):
        dr, _ = _render({"xsize": "6", "ysize": "4"})
        fig = dr.figures["g1"]
        assert fig.sizing_mode in (
            "stretch_width", "scale_width", "stretch_both", "scale_both"), (
            f"a sized figure became fixed: sizing_mode={fig.sizing_mode!r}"
        )

    def test_proportions_are_carried_as_a_RATIO_not_as_pixels(self):
        """Converting inches to fixed pixels would break BR-10.3.

        Bokeh gives every figure a default width and height of 600, which
        sizing_mode overrides; what matters is that dash expresses the
        request as aspect_ratio rather than pinning inch-derived pixels.
        """
        dr, _ = _render({"xsize": "6", "ysize": "4"})
        fig = dr.figures["g1"]
        assert fig.aspect_ratio is not None, (
            "xsize()/ysize() did not become an aspect ratio"
        )
        assert fig.width in (None, 600), (
            f"the width was pinned to {fig.width}px from the inch size"
        )

    def test_an_unsized_figure_is_unchanged_in_kind(self):
        dr, _ = _render()
        assert dr.figures["g1"].sizing_mode == "stretch_width"


# ======================================================================
# Layout
# ======================================================================

class TestBootstrapLayout:

    @staticmethod
    def _emitted(text):
        """Classes on the emitted grid DIVs, not the stylesheet definitions.

        The stylesheet defines every db-col-* class, so a bare substring
        search matches whether or not anything uses them.
        """
        import re
        out = []
        for m in re.finditer(r'class="(db-col-12[^"]*)"', text):
            out.append(m.group(1))
        return out

    def test_an_lg_breakpoint_is_emitted(self):
        """The .db-col-lg-* CSS already existed; nothing emitted it."""
        _, html_text = _render(build={"layout": "bs"}, n_graphs=3)
        cls = self._emitted(html_text)
        assert cls, "no Bootstrap grid cells were emitted"
        assert any("db-col-lg-" in c for c in cls), (
            f"the grid emits only an md breakpoint, so a wide display is "
            f"never used: {cls[:3]}"
        )

    def test_the_md_breakpoint_is_still_emitted(self):
        _, html_text = _render(build={"layout": "bs"}, n_graphs=3)
        cls = self._emitted(html_text)
        assert any("db-col-md-" in c for c in cls), cls[:3]

    def test_a_narrow_cell_doubles_up_at_the_medium_breakpoint(self):
        """A tablet is not a wide display: four columns at 1440 are cramped
        at 768."""
        import re
        _, html_text = _render(
            build={"layout": "bs: g1=3 g2=3 g3=3 g4=3"}, n_graphs=4)
        checked = 0
        for c in self._emitted(html_text):
            md = re.search(r"db-col-md-(\d+)", c)
            lg = re.search(r"db-col-lg-(\d+)", c)
            if md and lg and int(lg.group(1)) <= 4:
                assert int(md.group(1)) > int(lg.group(1)), c
                checked += 1
        # The four cells are narrow ones (measured 24sep2026: md-6 lg-3
        # each); a cell that lost its md or lg class was never asked.
        assert checked == 4, (checked, self._emitted(html_text))

    def test_a_graph_cell_takes_its_height_from_the_figure(self):
        """Every cell used to get the same height regardless of its span.

        The fix is NOT a min-height on graph cells: with an aspect ratio the
        figure already determines its own height, and forcing a floor leaves
        dead space -- measured at 217px under a 10x2in panel in a full-width
        cell. A graph cell therefore carries no height class at all, and the
        proportions come from the figure.
        """
        import re
        _, html_text = _render({"xsize": "10", "ysize": "2"},
                               build={"layout": "bs"}, n_graphs=1)
        graph_cells = [c for c in self._emitted(html_text)
                       if "db-cell-h-" in c]
        assert not graph_cells, (
            f"a graph cell was given a fixed height: {graph_cells}"
        )

    def test_a_kpi_cell_height_follows_its_span(self):
        """A KPI card has no intrinsic height, so it still needs one."""
        import re
        spec_kpis = [{"name": f"k{i}", "stat": "mean", "var": "mpg",
                      "title": f"K{i}", "fmt": "%9.1f"} for i in range(1, 5)]
        import tempfile
        spec = make_spec(_SCATTER)
        spec["kpis"] = spec_kpis
        spec["build_options"]["layout"] = "bs"
        spec["build_options"]["registry"] = "k1 k2 k3 k4 g1"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        html_text = DashRenderer(sp, dp, op).render()
        for pth in (sp, dp, op):
            try:
                os.unlink(pth)
            except OSError:
                pass
        kpi_cells = [c for c in self._emitted(html_text) if "db-cell-h-" in c]
        assert kpi_cells, "KPI cells carry no height class"
        assert all("db-cell-h-sm" in c for c in kpi_cells), kpi_cells
        # One card of four with a height passed the two checks above.
        # Measured 24sep2026: each of the four KPI cells carries it, and
        # the graph's cell (the fifth) none.
        assert len(kpi_cells) == 4, self._emitted(html_text)

    def test_a_wide_panel_gets_its_own_row(self):
        """And does not push every other graph onto a row of its own."""
        rows = DashRenderer._auto_bs_layout(
            ["wide", "a", "b"], [],
            figures={"wide": _FakeFig(5.0), "a": _FakeFig(1.0),
                     "b": _FakeFig(1.0)})
        spans = [[sp for _, sp in r] for r in rows]
        assert [12] in spans, f"the wide panel did not get a full row: {spans}"
        assert any(len(r) == 2 for r in rows), (
            f"the square panels were not packed together: {spans}"
        )


class TestGrid:

    @pytest.mark.parametrize("n,rows,cols", [
        (1, 1, 1), (4, 2, 2), (9, 3, 3),
    ])
    def test_a_square_grid_for_square_figures(self, n, rows, cols):
        dr, _ = _render({"aspectratio": "1"}, n_graphs=n)
        got = dr._compute_grid(n, "auto")
        assert got == (rows, cols), got

    def test_wide_figures_get_fewer_columns(self):
        """A dashboard of wide figures wants fewer columns than square ones."""
        square, _ = _render({"aspectratio": "1"}, n_graphs=4)
        wide, _ = _render({"xsize": "10", "ysize": "2"}, n_graphs=4)
        s_rows, s_cols = square._compute_grid(4, "auto")
        w_rows, w_cols = wide._compute_grid(4, "auto")
        assert w_cols < s_cols, (
            f"wide figures got {w_cols} columns, square ones {s_cols}"
        )

    def test_an_explicit_layout_still_wins(self):
        dr, _ = _render({"xsize": "10", "ysize": "2"}, n_graphs=4)
        assert dr._compute_grid(4, "1 4") == (1, 4)

    def test_the_kpi_row_maximum_is_a_named_constant(self):
        """4 per row is a design choice, not a derivable quantity."""
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        assert "_MAX_KPIS_PER_ROW" in src, (
            "the KPI-per-row limit is still a bare literal"
        )


# ======================================================================
# The responsive claim itself
# ======================================================================

class TestViewportMeta:
    """Found by opening a dashboard at 375px in a real browser.

    The emulated viewport reported ``window.innerWidth == 980``: with no
    ``<meta name="viewport">`` a mobile browser lays the page out at its
    980px default and then zooms the whole thing out to fit. Every
    breakpoint below 980 is therefore unreachable on a phone, and the text
    is unreadably small -- which is the specific claim the conference
    abstract makes.
    """

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_the_document_declares_a_viewport(self, layout):
        _, html_text = _render(build={"layout": layout})
        assert 'name="viewport"' in html_text, (
            f"{layout}: no viewport meta tag, so a phone renders the "
            f"dashboard at 980px and zooms out"
        )
        assert "width=device-width" in html_text

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_it_is_declared_exactly_once(self, layout):
        _, html_text = _render(build={"layout": layout})
        assert html_text.count('name="viewport"') == 1

    def test_the_csp_meta_is_still_present(self):
        """The viewport tag must not displace the security header."""
        _, html_text = _render(build={"layout": "bs"})
        assert "Content-Security-Policy" in html_text
