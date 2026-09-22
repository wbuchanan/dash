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
        dr.render()
    finally:
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass
    return dr


def _glyph_renderers(fig):
    """Return the figure's glyph renderers in draw order."""
    return [r for r in fig.renderers if getattr(r, "glyph", None) is not None]


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
    # Unknown filter type — compute it the way Bokeh would, if possible.
    try:
        return int(len(filt.compute_indices(renderer.data_source)))
    except Exception:  # pragma: no cover - defensive
        return n_rows


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
# environment recorded in .ultraplan/BASELINE.md (python 3.14, bokeh 3.9).
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
#               documented behaviour change; see .ultraplan/CHANGELOG.md.
#   8cfdca74... S10.  Every figure now carries an aspect ratio.  There was
#               previously no way at all -- option, scheme or data -- to
#               influence a figure's proportions: all 67 Figure objects
#               across 10 generated dashboards had no width, height,
#               frame_width or aspect_ratio.  With none given the ratio now
#               comes from the active scheme's graphsize, so every dashboard
#               changes.  Also intended; see .ultraplan/CHANGELOG.md.  The
#               same commit adds the viewport meta tag (without it a phone
#               laid the page out at 980px and zoomed out) and the
#               min/max height band the ratio is honoured within.
#   49647a0c  S12/S13.  Every ColumnDataSource now carries a row-identity
#               column so the filter callback can mask by identity instead
#               of by position, and single-series figures pick up the
#               scheme-driven changes from the same batch.  Intended; see
#               .ultraplan/CHANGELOG.md....
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
#               Intended; see .ultraplan/CHANGELOG.md.
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
#               Intended; see .ultraplan/CHANGELOG.md.
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
_SINGLE_Y_BASELINE_SHA256 = (
    "2bf51dc0452f30c142bc91fad12a77ea48c09747f4eb77ad703d33176da19645"
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
