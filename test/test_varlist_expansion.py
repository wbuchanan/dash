"""
test_varlist_expansion.py
Renderer-side tests for varlist expansion and plot-spec correctness.

Plan task 06-01 (batch 2).  This file is the Python half of a pair; the Stata
half is ``test/test_varlist_expansion.cscript``.  The split follows where each
defect lives:

  * the cscript drives the real ``dash`` command and measures what the user
    sees (colour census of the generated HTML, return codes, spec JSON);
  * this file pins the contracts ``dash_render.py`` must honour once
    ``dash.ado`` starts emitting correct specs.

Most tests here are FAILING tests written before the fix, per project rule 8.
Two are regression guards that pass today and must keep passing; they are
labelled as such in their docstrings so nobody mistakes a green result for
proof that a defect was fixed.

Run with:  pytest test/test_varlist_expansion.py -v
"""
import hashlib
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
# conftest.py holds the shared spec/data builders; add the test directory
# itself to sys.path so it imports as a plain module regardless of the
# directory pytest was invoked from.
sys.path.insert(0, _HERE)

from bokeh.models import AllIndices, BooleanFilter, IndexFilter, LabelSet
from bokeh.plotting import figure

from dash_render import DashRenderer, GlyphMapper, OptionTranslator, SchemeParser

from conftest import make_data_json, make_spec


# ============================================================
# Helpers
# ============================================================

from conftest import render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402


def _render(plots, df, *, graph_if="", graph_in=""):
    """Render *plots* against *df* and return the DashRenderer.

    The spec shape matches what ``dash.ado`` emits for a single named graph.
    """
    spec = make_spec(plots)
    spec["graphs"][0]["if_expr"] = graph_if
    spec["graphs"][0]["in_expr"] = graph_in
    data = make_data_json(df)

    paths = [tempfile.mkstemp(suffix=s)[1] for s in (".json", ".json", ".html")]
    spec_path, data_path, out_path = paths
    try:
        with open(spec_path, "w") as fh:
            json.dump(spec, fh)
        with open(data_path, "w") as fh:
            json.dump(data, fh)
        dr = DashRenderer(spec_path, data_path, out_path)
        render_models(dr)
    finally:
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass
    return dr


def _glyph_renderers(fig):
    """Return the figure's glyph renderers in draw order."""
    return [r for r in drawn_renderers(fig) if getattr(r, "glyph", None) is not None]


def _series_colors(fig):
    """Return the distinct series colours drawn on *fig*, in draw order.

    Reads the colour off each glyph rather than off the HTML so the assertion
    does not depend on how Bokeh happens to serialise the document.  The
    cscript performs the same census against the generated HTML.
    """
    seen = []
    for r in _glyph_renderers(fig):
        g = r.glyph
        for attr in ("fill_color", "line_color"):
            val = getattr(g, attr, None)
            if isinstance(val, str) and val.startswith("#") and val not in seen:
                seen.append(val)
    return seen


def _visible_count(renderer):
    """Number of rows *renderer* actually draws, honouring any CDSView filter."""
    n_rows = max(
        (len(v) for v in renderer.data_source.data.values()), default=0
    )
    view = getattr(renderer, "view", None)
    filt = getattr(view, "filter", None)
    if filt is None or isinstance(filt, AllIndices):
        return n_rows
    if isinstance(filt, IndexFilter):
        return len(filt.indices or [])
    if isinstance(filt, BooleanFilter):
        return int(sum(1 for b in (filt.booleans or []) if b))
    # Unknown filter type — compute it the way Bokeh would.  A failure here
    # used to `return n_rows', i.e. report every row as visible, which is
    # exactly the expected count for the unqualified layers this helper
    # also measures (~372, ~393): a filter whose indices could not be
    # computed would then pass those assertions silently.  A count that
    # cannot be determined must fail, not default to "all of them".
    try:
        return int(len(filt.compute_indices(renderer.data_source)))
    except Exception as exc:  # pragma: no cover - defensive
        raise AssertionError(
            f"_visible_count cannot measure a {type(filt).__name__}: {exc}"
        ) from exc


def _all_label_sets(fig):
    """Every LabelSet annotation attached to *fig*, wherever it was added."""
    out = []
    for panel in (fig.center, fig.above, fig.below, fig.left, fig.right):
        out.extend(a for a in panel if isinstance(a, LabelSet))
    return out


# Bokeh mints a fresh "pNNNN" id for every model and a fresh document UUID on
# every render.  Nothing else about the page is random, so normalising those
# two token families makes two renders byte-comparable.
_BOKEH_ID_RE = re.compile(r"\b[pP]\d{3,7}\b")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_DOC_VERSION_RE = re.compile(r'("UUID":\{"version":")[^"]*(")')
_DOC_JSON_RE = re.compile(
    r'<script type="application/json"[^>]*>(.*?)</script>', re.S
)


def normalise_bokeh_html(html: str) -> str:
    """Return the page's Bokeh document JSON with per-run ids normalised away.

    The bundled BokehJS blob is excluded deliberately: it is a copy of the
    installed library, so including it would turn this guard into a Bokeh
    version check instead of a check on what dash generates.
    """
    match = _DOC_JSON_RE.search(html)
    if match is None:
        raise AssertionError(
            "no Bokeh document JSON found in the generated HTML"
        )
    doc = match.group(1)
    doc = _BOKEH_ID_RE.sub("ID", doc)
    doc = _UUID_RE.sub("UUID", doc)
    # The document records the Bokeh version that wrote it, and that is
    # the only difference between this page under bokeh 3.8.0 (the version
    # Stata's Python ships) and 3.9.0 (the development interpreter's):
    # measured 24sep2026, WP-25, when the suite first ran under both.
    doc = _DOC_VERSION_RE.sub(r"\1VERSION\2", doc)
    return doc.strip()


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def wide_df():
    """Ten rows with five numeric columns — four y's against one x."""
    n = 10
    return pd.DataFrame({
        "mpg":     np.linspace(15.0, 35.0, n),
        "price":   np.linspace(4000.0, 12000.0, n),
        "length":  np.linspace(142.0, 233.0, n),
        "displ":   np.linspace(80.0, 425.0, n),
        "weight":  np.linspace(2000.0, 4000.0, n),
        "foreign": np.array([0.0, 1.0] * (n // 2)),
    })


def _scatter(yvar, xvar, if_expr="", in_expr=""):
    return {"type": "scatter", "yvar": yvar, "xvar": xvar,
            "options": {}, "if_expr": if_expr, "in_expr": in_expr}


# ============================================================
# V2P-01 — N y-variables must draw N distinctly coloured series
# ============================================================
# STATUS: passes today.  This is the renderer-side contract that the cscript's
# headline colour census measures end to end.  dash.ado currently collapses
# `scatter mpg price weight` to a single plot spec, so the renderer never gets
# the chance to draw the second series; once the parser is fixed this test
# pins the behaviour it must produce.

@pytest.mark.parametrize("n_series", [1, 2, 3, 4])
def test_n_plots_draw_n_distinct_series_colours(wide_df, n_series):
    """Each plot spec gets its own scheme colour, p1..pN, in order."""
    yvars = ["mpg", "price", "length", "displ"][:n_series]
    plots = [_scatter(y, "weight") for y in yvars]

    dr = _render(plots, wide_df)
    fig = dr.figures["g1"]

    colors = _series_colors(fig)
    assert len(colors) == n_series, (
        f"{n_series} plot specs produced {len(colors)} distinct series "
        f"colours: {colors}"
    )

    # Derive the expected palette from the ACTIVE scheme rather than
    # hardcoding hex values: batch 1 replaced the scheme files.
    scheme = SchemeParser("s2color")
    expected = [scheme.default_color(i, "scatter") for i in range(n_series)]
    assert colors == expected


# ============================================================
# V2P-02 — REGRESSION GUARD: single-y output is unchanged
# ============================================================
# STATUS: passes today, by design.  A guard cannot fail before the change it
# guards against; its job is to hold the line across the varlist work.
#
# The baseline below was captured from the PRE-FIX code base.  If the varlist
# change alters a one-y-variable dashboard in any way at all, this fails.

# sha256 of normalise_bokeh_html(<single-y scatter render>), under the pinned
# environment recorded in test/conftest.py's _BASELINES (python 3.14, bokeh 3.9;
# the .ultraplan/BASELINE.md it once cited is gone).
# Re-baseline ONLY on a deliberate, reviewed change: run this test, read the
# reported digest, and say in the commit message what changed and why.
#
# History:
#   70d9475b... captured 2026-09-18 against the pre-varlist tree.
#   264474fd... S09.  A single-series scatter no longer draws a legend.
#               Measured over 55 probes: twoway draws a legend if and only if
#               the graph has two or more keys, and only legend(on) forces
#               one onto a one-key plot.  dash passed legend_label=<yvar>
#               from every glyph, so every single-series graph carried a
#               legend twoway would not draw.  This is the intended,
#               documented behaviour change; see CHANGELOG.md.
#   8cfdca74... S10.  Every figure now carries an aspect ratio.  There was
#               previously no way at all -- option, scheme or data -- to
#               influence a figure's proportions: all 67 Figure objects
#               across 10 generated dashboards had no width, height,
#               frame_width or aspect_ratio.  With none given the ratio now
#               comes from the active scheme's graphsize, so every dashboard
#               changes.  Also intended; see CHANGELOG.md.  The
#               same commit adds the viewport meta tag (without it a phone
#               laid the page out at 980px and zoomed out) and the
#               min/max height band the ratio is honoured within.
#   49647a0c  S12/S13.  Every ColumnDataSource now carries a row-identity
#               column so the filter callback can mask by identity instead
#               of by position, and single-series figures pick up the
#               scheme-driven changes from the same batch.  Intended; see
#               CHANGELOG.md....
#   f929e3d3  S11.  The renderer now CONSUMES the translated schemes instead
#               of only parsing them.  A marker's symbol comes from the
#               scheme's symbol cycle and its size from `symbolsize p'
#               (previously a literal 8px for every scheme); a scatter's
#               alpha from `intensity p', a bar's from `intensity bar' and
#               an area's from `intensity area' (previously 0.7/0.8/0.5); a
#               line's width from `linewidth p' and its dash from
#               `linepattern p#lineplot'; the minor grid from `color
#               minor_grid'; the legend's background, border and label size
#               from the scheme.  _GSIZE_PT was also corrected against
#               Stata's own style/gsize-*.style files, which disagreed with
#               six of its fourteen entries.  Every dashboard changes.
#               Intended; see CHANGELOG.md.
#   98d50ff6  The scheme now decides WHICH grids are drawn, not just their
#               colour.  The two grid-visibility flags were parsed and never
#               read, and Bokeh draws both grids by default, so dash drew a
#               grid Stata does not draw in 10 of the 14 shipped schemes --
#               both grids under s1color, s1mono, s1rcolor and stmono1, which
#               draw none.  The y-axis flag was also read from
#               `draw_major_grid', which is dead at scheme level and `no' in
#               every scheme; Stata's key is `draw_major_vgrid' and is `yes'
#               for ten of them.  s2color, the baseline's scheme, therefore
#               loses its vertical grid lines and keeps its horizontal ones.
#               Intended; see CHANGELOG.md.
#   2bf51dc0  WP-10.  A figure carried TWO HoverTools with identical
#               tooltips: the mapper adds one for a scatter and the figure
#               builder added a comprehensive one, which cleared the
#               mapper's only when hover() was given.  Both renderers now
#               build the figure's hover in one place and clear first.  The
#               whole normalised difference from 98d50ff6 is the removal of
#               one HoverTool object and its id from the figure's tools
#               list -- diffed token by token against HEAD before
#               re-baselining, 38 chunks, all of them that one object.
#               Intended.
#   5e1c3a24  WP-16.  The scheme reaches the page: the figure title takes
#               `color heading' and `gsize heading' (was Bokeh's #444444 at
#               13px), the minor grid is None on both axes (was #505050),
#               the legend sits below the plot, centred, in the scheme's
#               columns (was top_right inside), and the axis text takes the
#               scheme's colours.  Not diffed token by token; each of those
#               changes is pinned off the models by
#               test_scheme_rendered_output.py for all 14 schemes in both
#               modes.  Intended.
#   20a7cb46  WP-21.  Every figure carries box zoom, undo, redo and save
#               beside its pan, wheel zoom, box select, lasso select and
#               reset, and the grid's one save button writes dashboard.png.
#               Diffed token by token against HEAD (4f6a314, which gives
#               5e1c3a24) before re-baselining: four chunks, all insertions
#               -- the grid toolbar's BoxZoomTool with its default overlay,
#               its UndoTool and RedoTool, its merged SaveTool with filename
#               "dashboard", and the figure's own four new tools.  Intended.
#   6f400f84  WP-25.  The document's Bokeh version is normalised away: it
#               was the only difference between this page under bokeh 3.8.0
#               (Stata's Python) and 3.9.0 (the development interpreter),
#               so the test failed under the interpreter Stata ships for no
#               change of dash's.  Diffed before re-baselining: the
#               normalised text is 20a7cb46's with "version":"3.9.0" read
#               as "version":"VERSION", and is identical under both
#               interpreters.  Intended.
#   3e545d0f  WP-27's phone-width reflow (`_dash_reflow') gives every
#               gridplot() grid equal shrinkable columns.  Diffed before
#               re-baselining, against HEAD's renderer: the one difference
#               is the GridPlot's "cols":null, now "cols":"minmax(0, 1fr)";
#               the Bokeh document is otherwise identical.  Intended.
#   5ad925f7  S3 batch: the plot region's border is the scheme's own line
#               (s2color: `color plotregion_line' white, `linewidth
#               plotregion' thin), where it was `color axisline' black
#               under every scheme; Stata's s2color draws it white on
#               white (test/fixtures/scheme_visual/truth.json).  Diffed
#               token by token against HEAD's renderer and HEAD's
#               schemes/s2color.scheme before re-baselining: one chunk,
#               "outline_line_color":"#000000" now "#ffffff" and an
#               inserted "outline_line_width":0.8.  Intended.
#   fd0db4f6  S3 batch: marker outlines follow linewidth p#mark -> pmark ->
#               p# -> p.  Diffed against HEAD's renderer and schemes: the
#               border chunk above and, on each of the scatter's three
#               glyphs, an inserted "line_width":1.5 (s2color's linewidth
#               p); nothing else.  Intended.
#   1ca5b296  WP-31 D4: the legend takes the scheme's key geometry
#               (glyph_width/height, label_standoff, spacing, padding,
#               margin), its grid (ncols/nrows) and its panel location
#               from twoway's clock table.  Intended.
#   ed770acf  WP-31 D6/D7: the finish code's dash_axis_bounds (noextend);
#               finish JS text only.  Intended.
#   efd46918  WP-31 D7: the axis title gap is the scheme's axis_title_gap
#               (1 px, Bokeh's 5 before).  Intended.
#   8dcef2d3  WP-31 D1c: the finish code reads a typed list as no ##N
#               rule; finish JS text only.  Intended.
#   8dd889d5  WP-31 D12: the zoom code ends with the reference lines'
#               dash_refline_extent statement; zoom JS text only.  Intended.
#   9e9dd72a  WP-31 E2 (merged on D12): the minor grid's dot pattern is Stata's .1 .7 rs
#               ([1, 3] px; [2, 4] before).  Intended.
#   18488fea  WP-31 G1/G2: the filter mask's code letters and every formatter's
#               dp arg ("period" here).  Intended.
#   39ab38bb  WP-31 D15: the finish code reads Stata's own ticks
#               (dash_stata_pick) and re-places xtick(#N); finish JS text
#               only.  Intended.
#   f9b003a1  WP-31 D15 follow-up: a shared by() letter's xtick(#N) in the
#               finish code; finish JS text only.  Intended.
_SINGLE_Y_BASELINE_SHA256 = (
    "c01991f0ef5c8d747f8a0c67a8586ea835d62939c98a2d9708f850f0eec1ee25"  # fe81e3ff -> c01991f0 (WP-44 AX-15: the Stata writer's dash_fmt_dump in _DASH_FMT_JS, the %21x/%16H/%8H/%16L/%8L/%#s axis formats; writer JS text only: the old _DASH_FMT_JS spliced into the new tree gives fe81e3ff; the same under both Pythons); 6a976759 -> fe81e3ff (WP-44 AX-14: the finish code's dash_grid_nogextend; finish JS text only; the same under both Pythons); cd5a71bb -> 6a976759 (WP-44 DG-6: the finish code's leap-second pair and its %tC tick branch; finish JS text only; the same under both Pythons); a5d23259 -> cd5a71bb (WP-44 AX-18: the finish and zoom code ticks a log axis of dates on their calendar, dash_axis_ticks_of; finish JS text only; the same under both Pythons); 355484e2 -> a5d23259 (WP-43 LT-10: the width scale's pair kind takes a legend's four-sided padding; width-scale JS text only; the same under both Pythons); 155db72d -> 355484e2 (WP-43 LT-6: the width scale writes its factor as --dash-k on each plot; width-scale JS text only; the same under both Pythons); e804d647 -> 155db72d (BUGS.md "A graph's canvas ended before its own x axis, x title and colour key labels": the graph region box a column of its own round the figure and the width-scale and span JS's graph box; the same under both Pythons); 7f4b4bfa -> e804d647 (WP-41 41-05, the width scale's by() grid spacing pair and its --dash-by-k length (width-scale JS text only); the same under both Pythons); 53c6cd58 -> 7f4b4bfa (WP-41 41-05: the plot region's outline in the width scale's table; the same under both Pythons); 699fcbf5 -> 53c6cd58 (WP-45 GW-6: the figure's graph-region box in its styles and the span hook's graph box; the same under both Pythons); 8c92e39b -> 699fcbf5 (WP-45 VF-4 with DECISIONS D66/D67 (the graph drawn as one picture, its width-scale callback on every figure; one toolbar per page, laid over it); the same under both Pythons); ad3f4117 -> 8c92e39b (WP-45 VF-4 in WP-41 41-05: the figure loses its 160-560 px height band, as twoway draws its graph's shape at any size, DECISIONS A-1; the same under both Pythons); 37127dab -> ad3f4117 (WP-34 AX-1: the axis plan's byg key and the finish code's default-axis condition; plan key and finish JS text only; the same under both Pythons); 93a4ea73 -> 37127dab (WP-34 AX-4: the axis plan's hfields and the histogram midpoint/span code; the same under both Pythons); a4f442b5 -> 93a4ea73 (WP-32 merge); 634f532a -> 12cea7d0 (P1.12b line widths) -> 150011f2 (P1.2a scheme chrome, merged batch 5) -> 4b4e77b5 -> 68b474a5 (P1.5 axis formats on P1.2b, merged batch 6) -> b11518da (P1.3a) -> 369c5e1a (merged batch 7) -> e8872e93 (merged batch 9) -> b7398dd3 (P1.23a) -> 33cae67d (P1.3b: the filter callback carries the date model's JS port) -> fd92af37 (batch-15 gate: a default date axis's ticks leave out range()) -> c1e8c7e1 (P1.20b: the axis plan carries margin pairs and box indexes, the finish code pads per side and moves the inner box) -> 533ab561 (P1.21b: the finish code carries dash_refline_extent; finish JS text only) -> 0ee9beb4 (merged batch 18) -> 9e48e06e (P1.28b) -> c1988a74 (P1.17b: the date model's JS port puts %td weekly steps on %tw week starts; finish JS text only) -> a64278d1 (WP-31 D1: the minor-tick finish code; finish JS text only) -> 1ca5b296 (WP-31 D4: legend geometry) -> ed770acf (WP-31 D6/D7: dash_axis_bounds; finish JS text only) -> efd46918 (WP-31 D7: the scheme's axis_title_gap) -> 8dcef2d3 (WP-31 D1c: typed lists; finish JS text only) -> 3e39e6d9 (WP-31 B5c: the axis plan's dots and dash_fill_dots) -> aa3312e2 (WP-31 D1b: dash_minor_place re-places a minor-label pool; finish JS text only) -> 8dd889d5 (WP-31 D12: the zoom code's dash_refline_extent statement; zoom JS text only) -> 039a825b (WP-31 E2: the minor grid's dot is .1 .7 rs, [1, 3] px; merged on D12) -> 9e9dd72a -> 18488fea (WP-31 G1/G2: the filter mask's code letters and every formatter's dp arg) -> 39ab38bb (WP-31 D15: dash_stata_pick and xtick(#N) re-placed; finish JS text only) -> f9b003a1 (WP-31 D15 follow-up: shared by() xtick(#N); finish JS text only) -> 48e429ca (merged batch 15: D15's Stata ticks, G7's %tb writer, C11's degree note) -> 95c8ec49 (WP-31 H2x: the grid's composite export actions and the print hook and stylesheet; the same under both Pythons) -> 4e76eb3b (merged batch 18: H2x's composite actions and K6's html_attributes) -> 414d94dd (batch-18 gate: the composite code's entity table keyed by name; composite JS text only) -> ed6ea533 (WP-31 K6 follow-up: a figure with a toolbar is role=group, not img; the same under both Pythons) -> a4f442b5 (WP-32 D-31.a: the legend key box is symxsize() by symysize(), 50 x 13; the same under both Pythons)
    # 533ab561 -> 0ee9beb4: P1.18b's axis plan key (xnr) and finish code.
    # 0ee9beb4 -> 9e48e06e: P1.28b's Save as SVG action on the grid's
    # toolbar.
    # 369c5e1a -> e8872e93: P1.17b's axis plan key (autobase) and finish code.
    # e8872e93 -> b7398dd3: P1.23a's code text only (the plan's "units"
    # key, the date-units JS in the finish code, dash_stata_number_of in
    # the formatter); diffed against the base, nothing else differs.
    # b11518da -> 369c5e1a: re-derived on the merged batch-7 tree (P1.16
    # keys and titles, P1.1b lists, P1.3a's min/max without spreads).
    # 68b474a5 -> b11518da: P1.3a default axes take natscale ticks and
    # twoway's margin (FixedTicker placeholders, Range1d over the hull, the
    # axis plan and zoom callback in the page).
    # 150011f2 -> 4b4e77b5: P1.2b markers drawn opaque (alpha 0.8 -> 1.0)
)


def _single_y_html():
    df = pd.DataFrame({
        "mpg":    np.linspace(15.0, 35.0, 10),
        "weight": np.linspace(2000.0, 4000.0, 10),
    })
    spec = make_spec([_scatter("mpg", "weight")])
    data = make_data_json(df)
    paths = [tempfile.mkstemp(suffix=s)[1] for s in (".json", ".json", ".html")]
    spec_path, data_path, out_path = paths
    try:
        with open(spec_path, "w") as fh:
            json.dump(spec, fh)
        with open(data_path, "w") as fh:
            json.dump(data, fh)
        return DashRenderer(spec_path, data_path, out_path).render()
    finally:
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass


def test_normalisation_makes_two_runs_of_one_command_comparable():
    """The comparison method itself: two renders differ only by Bokeh ids."""
    a, b = _single_y_html(), _single_y_html()
    assert a != b, (
        "two renders were byte-identical, so this guard is not actually "
        "exercising the id normalisation it claims to"
    )
    assert normalise_bokeh_html(a) == normalise_bokeh_html(b)


def test_the_bokeh_version_is_normalised_away():
    """The same document written by two Bokeh versions normalises alike, so
    the baseline is a check on what dash generates under either (WP-25)."""
    page = _single_y_html()
    m = re.search(r'"version":"([^"]+)"', page)
    assert m, "the page records no Bokeh version"
    other = page.replace('"version":"%s"' % m.group(1),
                         '"version":"%s.1"' % m.group(1), 1)
    assert other != page
    assert normalise_bokeh_html(other) == normalise_bokeh_html(page)


def test_single_y_output_matches_prefix_baseline():
    """A one-y-variable dashboard is unchanged apart from per-run ids."""
    normalised = normalise_bokeh_html(_single_y_html())
    digest = hashlib.sha256(normalised.encode("utf-8")).hexdigest()
    assert digest == _SINGLE_Y_BASELINE_SHA256, (
        "single-y dashboard output changed.\n"
        f"  baseline: {_SINGLE_Y_BASELINE_SHA256}\n"
        f"  actual:   {digest}\n"
        "If the change was intended, re-baseline the constant in this file "
        "and say why in the commit message."
    )


# ============================================================
# V2P-03 — a per-plot if qualifier binds to that plot only
# ============================================================
# STATUS: FAILS today.  dash_render.py's _apply_graph_filter() reads only the
# GRAPH-level "if_expr"; no code path reads a plot's own "if_expr", so a
# qualifier written on one layer of an overlay is silently ignored.

def test_second_plot_if_expr_filters_only_the_second_plot(wide_df):
    """`(scatter mpg weight) (scatter mpg weight if foreign)`."""
    plots = [
        _scatter("mpg", "weight"),
        _scatter("mpg", "weight", if_expr="foreign==1"),
    ]
    dr = _render(plots, wide_df)
    renderers = _glyph_renderers(dr.figures["g1"])
    assert len(renderers) == 2

    n_foreign = int((wide_df["foreign"] == 1).sum())
    assert _visible_count(renderers[0]) == len(wide_df), (
        "the unqualified first layer lost rows"
    )
    assert _visible_count(renderers[1]) == n_foreign, (
        "the second layer's `if foreign` qualifier was not applied to it; "
        f"it draws {_visible_count(renderers[1])} rows, expected {n_foreign}"
    )


def test_first_plot_if_expr_does_not_leak_onto_later_plots(wide_df):
    """The mirrored command: the qualifier must not apply to every layer."""
    plots = [
        _scatter("mpg", "weight", if_expr="foreign==1"),
        _scatter("mpg", "weight"),
    ]
    dr = _render(plots, wide_df)
    renderers = _glyph_renderers(dr.figures["g1"])
    assert len(renderers) == 2

    n_foreign = int((wide_df["foreign"] == 1).sum())
    assert _visible_count(renderers[0]) == n_foreign
    assert _visible_count(renderers[1]) == len(wide_df), (
        "the first layer's qualifier leaked onto the unqualified second layer"
    )


# ============================================================
# V2P-04 — scatteri marker labels belong to their own point
# ============================================================
# STATUS: FAILS today.  map_scatteri() reads pair[0]/pair[1] as floats and has
# no label handling at all, so `scatteri 20 3000 "A" 30 4000 "B"` loses both
# labels even once dash.ado stops shearing the pairing.
#
# WIRE FORMAT ASSUMED: a labelled point arrives as [y, x, label].  If the fix
# chooses a different representation, update the spec built here — the
# assertions (two points at the right coordinates, each carrying its own
# label) are the part that must not change.

def test_scatteri_labels_attach_to_their_own_points():
    mapper = GlyphMapper(OptionTranslator(), SchemeParser("s2color"))
    fig = figure()

    renderers = mapper.map_scatteri(fig, [[20, 3000, "A"], [30, 4000, "B"]], {})

    source = renderers[0].data_source
    assert list(source.data["x"]) == [3000.0, 4000.0]
    assert list(source.data["y"]) == [20.0, 30.0]

    label_sets = _all_label_sets(fig)
    assert label_sets, (
        "scatteri drew the points but no marker labels; 'A' and 'B' were "
        "dropped"
    )
    labels = list(label_sets[0].source.data[label_sets[0].text])
    assert labels == ["A", "B"]


def test_scatteri_rejects_a_sheared_values_array():
    """The shape dash.ado emits today must not be accepted silently.

    `[[20,3000],["A",30],[4000,"B"]]` is what the blind two-at-a-time pairing
    produces.  Whatever the fix, a coordinate that is not a number must raise
    an error that names the plot type, not a bare float() ValueError from
    numpy internals.
    """
    mapper = GlyphMapper(OptionTranslator(), SchemeParser("s2color"))
    fig = figure()

    with pytest.raises(Exception) as excinfo:
        mapper.map_scatteri(fig, [[20, 3000], ["A", 30], [4000, "B"]], {})

    assert "scatteri" in str(excinfo.value).lower(), (
        "a malformed scatteri values array produced an unhelpful error: "
        f"{excinfo.value!r}"
    )


# ============================================================
# V2P-05 — tsline without an x variable must name tsset
# ============================================================
# STATUS: FAILS today.  dash has no notion of tsset; `dash tsline close`
# leaves xvar empty and map_line() dies on `source.data[""]`, surfacing to the
# user as r(7102) wrapping a KeyError with an empty key.

def test_tsline_without_x_variable_reports_tsset():
    df = pd.DataFrame({
        "close": np.linspace(10.0, 20.0, 10),
        "qtr":   np.arange(10.0),
    })
    plots = [{"type": "tsline", "yvar": "close", "xvar": "",
              "options": {}, "if_expr": "", "in_expr": ""}]

    with pytest.raises(Exception) as excinfo:
        _render(plots, df)

    message = str(excinfo.value)
    assert "tsset" in message.lower(), (
        "a tsline plot with no time variable failed with an error that does "
        f"not tell the user to tsset the data: {message!r}"
    )


def test_tsline_uses_the_supplied_time_variable():
    """Once dash.ado resolves the tsset time variable, tsline must plot it.

    STATUS: passes today — the renderer is fine when it is handed an xvar.
    Recorded so the tsset work has a positive case to render against.
    """
    df = pd.DataFrame({
        "close": np.linspace(10.0, 20.0, 10),
        "qtr":   np.arange(10.0),
    })
    plots = [{"type": "tsline", "yvar": "close", "xvar": "qtr",
              "options": {}, "if_expr": "", "in_expr": ""}]

    dr = _render(plots, df)
    renderers = _glyph_renderers(dr.figures["g1"])
    assert len(renderers) == 1
