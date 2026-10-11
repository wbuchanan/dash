# Section 36: The by() remainder

> Part of: WP-31 · GAPS3 rows: D10 · Risk: yellow · Batch: 12 · Depends on: 01 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U36

## Overview

**What is wrong today.** GAPS3 D10 (GAPS3.md:160): "`by()`: overall `graphregion()/plotregion()` and `regions` named; `legend(ring(0))` drawn beside the array; overall legend not clickable; `by_alternate_*` axes; panel margin uses f(panels) not `iscale()`; `subtitleformat()`, shrink options, other bystyles named; panel-label box restyling (`subtitle(, fcolor() lcolor() nobox)`) named; a one-panel `by()` with an empty value label drawn without chrome; panels emptied by a filter stay drawn." Evidence dash_render.py:26095-26135 (`_DASH_BY_GRAMMAR`, whose stage-3 rows `graphregion plotregion r1title..b2title note caption subtitle title spacers bgcolor` are parsed and, GAPS3 §5 says, "never applied") and :38451 (`_dash_warn_once(... "by(, legend(ring(0))) is drawn beside the panels.")`). The register rows are P2.69 (one-panel empty label), P2.77 (overall regions), P2.81 (layout edges: f(panels), subtitleformat, shrink), P2.84 (legend ring(0), clickable, by_alternate), P2.89 (label box restyling) and P2.24 (emptied panels stay drawn).

Measured at `6370ca4` (this file's probes, read from the code; re-measured by 36-01):
- `by(foreign, graphregion(fcolor(red)))`: `_dash_by_axes_options` (:37798) and `_dash_by_layout_options` (:38408) read stages 1 and 2 only; the stage-3 token is in the by() grammar (:26127) so it is not refused, and `_dash_parse_by` names it in the warning "by() sub-option(s) not implemented and ignored".
- `by(foreign, legend(ring(0)))`: `_dash_by_keys` (:38108) returns `ring0=True`; `_dash_by_side` (:38422-38460) places the legend cell beside the array and warns.
- The overall legend cell (`_dash_by_legend_cell`, :38074) builds a `Legend` with `click_policy` left at Bokeh's `"none"`, and its items reference the first panel's renderers only.
- `_dash_plot_margin(scheme, graph_opts, panels=1)` (:29168) receives the number of panels; twoway's margin multiplier is `f(k)` with `k = ceil(sqrt(full_n))` times `iscale()` (`_dash_by_panel_scale`, :26528-26560), which only sizes text and markers today.
- `_dash_by_label_box` (:38225) fills from `textboxstyle subtitle` and outlines in `bylabel_outline`; the by()'s `subtitle(, fcolor() lcolor() nobox)` words are read by `_dash_by_text_options` for the text only.
- `_dash_facet_label` (:26812) returns "" for a value whose label is "", and `_dash_by_label_box` returns None for an empty text ("A panel with no label, or an empty one, gets no box", :38246); with one panel the renderers draw no "Graphs by" note either.
- After a filter move that empties a panel, the saved page's `_FILTER_JS` row copy leaves an empty source and the figure drawn; the served `_dash_redraw_for` (:49267) redraws an empty layer; neither hides the panel.

**After this section**, both renderers: `by(, graphregion() plotregion())` restyle the array (every panel's border and frame as twoway's overall regions, measured); `by(, legend(ring(0)))` puts the legend in an empty cell of the array when one exists, else at the compass position over the array's own cell (D-36.b); the overall legend's items reference the matching renderer of every panel and `click_policy="hide"` toggles a series in all panels; `by_alternate_xaxes/yaxes` (the scheme's yesno stubs, measured) alternate the outer axes' sides by column/row; the panel plot-region margin takes the `f(k) x iscale()` multiplier; `subtitleformat()` restyles every panel label; the shrink words follow the measurement; `subtitle(, fcolor() lcolor() nobox)` restyle the label box; a one-panel by() with an empty label keeps its chrome (an empty label box and the Graphs-by note, as measured); a panel a filter empties is hidden after the move and shown again when rows return, saved and served. Options drawn print nothing (Q36).

**Test order and commit rule (rule 7, M6).** One row, one commit `(WP-31 D10)`. 36-01 writes the extractor, the fixture, `test/test_by_remainder.py` and the U36 cases, runs them red, saves `<scratch>/36-01-failure.txt`, never commits. 36-02 draws the regions, legend and axes; 36-03 the margin, label box, subtitleformat, shrink, one-panel chrome and the emptied-panel hiding; 36-04 flips, help, BUGS, GAPS3, CHANGELOG, the one commit.

### Section decisions (this file; binding on the executor)

- **D-36.a Overall regions are per panel.** Bokeh has no model for the whole gridplot's background other than each figure's `border_fill_color`. `by(, graphregion(...))` is drawn on every panel's border (and the head/foot/legend cells' figures) exactly as `_dash_apply_regions` draws `graphregion()` on a plain figure; `by(, plotregion(...))` on every panel's frame. The by() copy wins over an outer `graphregion()`/`plotregion()` copy when both are given (twoway's by() regions replace the graph's; measured `regions.both`). If the fixture shows twoway drawing the by() plotregion as the array's region (one box around all panels, not each frame), `plotregion()` inside by() is drawn on the panels' borders too and the difference is documented (M17).
- **D-36.b `legend(ring(0))` goes into the array.** With a hole or an unfilled trailing cell, the legend cell takes the empty cell nearest the clock's compass position (`_dash_by_positions`' `extra["drawn"]` lists the cells; `legend_at` already names a cell for `at(#)`). Without an empty cell, the legend is placed inside the panel at the compass position (the panel whose cell is nearest the compass corner), as `_dash_apply_legend` places `ring(0)` on a plain figure, with its items referencing every panel's renderers (D-36.c). The warning at :38451 is removed.
- **D-36.c One legend, every panel.** `_dash_by_legend_cell`'s items get `renderers=[panel_k.renderers[i] for every panel k]` for series *i* (matched by the renderer tag the mapper stamps, `_dash_series_index`, or by position when all panels draw the same layers), and `click_policy="hide"`. Verified in headless Chrome in 36-02 (`test_csp_browser.py`'s harness): a click hides the series in every panel. If BokehJS rejects renderers of another plot (a console error in the harness), the fallback is `click_policy="hide"` on the first panel's renderers plus a `CustomJS` on each first-panel renderer's `visible` change that copies `visible` to the matching renderer of every other panel (`_DASH_BY_LEGEND_SYNC_JS`, constant text; the renderers travel in `args`).
- **D-36.d Alternate axes are the scheme's.** `SchemeParser.by_flags` gains `alt_xaxes`/`alt_yaxes` from the stubs the executor finds by `grep -n "by_alt" /Applications/StataNow/ado/base/s/scheme-s2color.scheme` (names recorded in the fixture `_meta.by_alt_stubs`). When set, `_dash_by_outer_axes` (:37929) puts the outer y axis of odd-numbered rows on the right and the outer x axis of odd-numbered columns on top, as the fixture's panel SVGs show. No stub, or `no`: nothing changes.
- **D-36.e The margin multiplier is `f(k) x iscale`.** `_dash_plot_margin(scheme, graph_opts, panels=1)` gains `mult=None`; the by() builders pass `_dash_by_panel_scale(full_n, by_raw)` as *mult* and the margin fraction is `scheme margin twoway x mult`, the fixture `margin.<n>` deciding whether twoway scales the margin by the multiplier (expected yes: bygraph_g.class scales every view).
- **D-36.f `subtitleformat()` is the panel label's textbox.** Its argument is read by `_dash_textbox` as a textbox option list and applied to every panel's `dash_by_label` Title and label box (size, colour, box fill/outline, justification), after by()'s `subtitle()` words, the later copy winning.
- **D-36.g Shrink words follow the fixture.** `shrink`/`noshrink`, `ishrink`/`noishrink`, `overallshrink`/`nooverallshrink` are measured (marker size, label font, title font, three panel counts). The rule written into `_dash_by_panel_scale` is the one the fixture shows (expected: `noishrink` holds the panel multiplier at 1 for the panels' contents; `nooverallshrink` holds the overall titles at 1; `noshrink` both). A word whose measured effect is nil is honoured silently.
- **D-36.h An empty label is still a label.** `_dash_by_label_box` draws the box for `title.text == ""` when the figure is a by() panel (`fig._dash_by_panel` is stamped by the builders); the Graphs-by note and the outer titles follow `by_vars`, never the label text. The one-panel case is a by() graph with one panel, not the "no faceting" sentinel (`_DASH_UNSAFE_BY` empties the varlist only for injection patterns).
- **D-36.i Emptied panels are hidden, both modes.** Saved: `_FILTER_JS` gains, after the row copy of every derived source, `dash_panels_visibility(panel_sources, panel_figs)`: a figure whose every own source has zero kept rows gets `visible = false`, else `true`; the figures and their sources travel in the callback `args` (`_build_filter_widgets` passes `by_panels_json` as index pairs, no user text). Served: `_dash_refinish_axes`'s caller in `_on_filter_change` sets `fig.visible` by the same rule through `_dash_panel_visibility(figures, facet_map)` (a new module function, copied). S36 is batch 12's one editor of `_FILTER_JS` and `_build_filter_widgets` (R12; no JS estimator section sits in batch 12). The gridplot keeps the hidden panel's cell (Bokeh leaves a blank), which is the documented behaviour. The stale-cue code is untouched.

## Risk: [yellow] -- every by() dashboard changes look in two places, and the saved filter script gains a block

**Why.** The legend, regions, axes, margin and label box run on every by() graph in both modes; the emptied-panel rule edits `_FILTER_JS` and `_build_filter_widgets`, which every saved page with a filter shares.

**Risk factors.**
1. Cross-plot legend items (D-36.c) are a BokehJS behaviour, not a documented API.
2. Hiding a figure inside a `gridplot` changes the grid's row heights in some Bokeh layouts; a hidden panel's toolbar entry stays.
3. Pinned tests: test_by_grid.py `TestNamedNoMore`, test_by_scales.py, test_by_chrome*.py, test_by_side*.py, test_help_claims_* nodes that assert the ring(0) warning, the named stage-3 words, the margin fraction and the empty-label behaviour.
4. The fixture must distinguish the by() regions from the outer ones; twoway's own words for a by() region refusal are unknown until measured.
5. Batch partners: S35 edits `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS` (R11); S36 calls `_dash_refinish_axes` from the served move path and must not edit it -- `_dash_panel_visibility` is called beside it, in the template's `_on_filter_change` block (`_generate_app_source`: S36 is batch 12's editor; S35's and S37's Boundaries say they do not edit the template).
6. S37 edits `_dash_apply_regions` and `_dash_region_spec`; S36 calls them with by()'s arguments and edits neither.

**Mitigation.**
1. 36-02 verifies in headless Chrome and falls back to the `visible`-sync CustomJS (D-36.c); `TestLegend::test_click_hides_every_panel` runs the fallback's JS under node when the direct route is not taken.
2. `test_a_hidden_panel_keeps_its_cell` pins the gridplot's children count; the help documents the blank cell.
3. Every pin is flipped in place in the commit (TDD stubs, "Flips").
4. The fixture records each region's fill from the SVG rect sizes (the array box versus each panel box).
5. The served call is added at the template line directly after the emitted `_dash_refinish_axes(...)` call; the Python function is new.
6. S36 passes by()'s stage-3 arguments as `graph_opts` copies to `_dash_apply_regions` unchanged.

## Dependencies

- **Depends on: 01** (tracking foundation: the BUGS.md entry, the Tracked line, the truth script and the markers).
- **Blocks:** none.
- **Parallel batch: 12**, merge order 35, 36, 37. **Can run with S35 and S37:** S35 edits secondary axes, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`; S37 edits `_dash_region_spec`, `_dash_apply_regions`, `_dash_margin_sides`, `_dash_plot_margin`'s margin reading. S36 edits the by() grammar appliers (`_dash_by_axes_options`, `_dash_by_keys`, `_dash_by_side`, `_dash_by_legend_cell`, `_dash_by_outer_axes`, `_dash_by_label_box`, `_dash_by_panel_scale`, `_dash_facet_label`'s callers), `_FILTER_JS`, `_build_filter_widgets` and the template's move block, and passes `mult` into `_dash_plot_margin` through a new keyword S37 does not touch (S37 is told in its Notes to keep the signature `mult=None`).

## Evidence

All anchors at `6370ca4`; re-read before editing.

### The grammar and the appliers

`_DASH_BY_GRAMMAR` (:26096-26135): stage-3 rows `graphregion plotregion r1title r2title l1title l2title t1title t2title b1title b2title note caption subtitle title spacers bgcolor`. `_dash_parse_by`'s docstring (:26240-26260) lists what is drawn: "cols(), total, missing, the rescale words, rows(), holes(), colfirst, compact, style(compact), iscale() and imargin() ... title(), subtitle(), note() and caption(), and ... the i*/noi* axis and title words, edgelabel, individual, ilegends, legend() and clegend()". Everything else is named once.

`_dash_by_side` (:38422-38490):

```python
38446    keys = _dash_by_keys(figs, opts, scheme)
38447    mark = ("by_legend_ring0", str(key))
38448    if keys.get("ring0") and (seen is None or mark not in seen):
38451        _dash_warn_once(mark, "dash: graph %r: by(, legend(ring(0))) is "
38452                        "drawn beside the panels." % str(key))
38453    gopts = _dash_by_layout_options(go)
38454    _cells, _r, _c2, extra = _dash_by_positions(
38455        len(figs), gopts, legend_at=keys["legend_at"],
38456        clegend_at=keys["clegend_at"])
38457    cells, nr, nc = extra["drawn"]
```

`_dash_by_legend_cell(scheme, name, side, legend, items, tag)` (:38074) builds the cell; `_dash_by_keys` (:38108) returns `{"legend", "legend_side", "legend_at", "clegend", ..., "ring0"}`. `_dash_by_outer_axes(figs, positions, opts)` (:37929) hides inner axes (`ax.visible = False`, :37963) by the `outer_*` flags. `_DASH_BY_FLAG_DEFAULTS` (:26070-26079) holds `edgelabel outer_xaxes outer_yaxes outer_xtitles outer_ytitles indiv_* indiv_as_whole`; no alternate key.

### The multiplier and the margin

`_dash_by_panel_scale(full_n, by_raw)` (:26528-26560): `k = ceil(sqrt(full_n))`, `f = 1 - (k-1)/k * b1`, `f -= (b2 - b1) (k - k1)/k` for `k > k1`, `_DASH_BY_GMETRIC = (3.0, 0.3, 1.0)` (:28991); `iscale(#)` replaces, `iscale(*#)` multiplies. `_dash_by_scale_panel(fig, m)` (:26626) applies it to text, markers, lines. `_dash_plot_margin(scheme, graph_opts, panels=1)` (:29168) computes the margin fraction as "r x min(W, H) ... r the scheme's `margin twoway` (2.2%) edited by each `plotregion(margin())` copy" and reads *panels* for the by() case.

### The label box and the empty label

`_dash_by_label_box(fig, scheme, mult=1.0)` (:38225-38310): a one-colour `ColorBar` named `dash_by_label_box` whose tick label is the panel label; "s2color #D9E6EB on #D9E6EB, s1color #E5DAA5 outlined black" (:38235-38236); `if title is None or not str(title.text or ""): return None` (:38258). `_dash_facet_label` (:26812): the value's label when it has one, else the number; "" is kept as "".

### The emptied panel

`_dash_by_panel_dropped` (:4392) decides at build time which panels twoway leaves out; nothing decides after a move. `_FILTER_JS` (constant at :24612) copies rows into every derived source; the served template's `_on_filter_change` redraws through `_dash_redraw_for` (:49267) and re-finishes through `_dash_refinish_axes` (:32271).

### Stata rules (research/stata-ground-truth.md §7, §9-§11)

- §11: by() stubs present in dash's scheme: `clockdir by_legend_position 6`, `gridringstyle by_legend_ring 3`, `yesno by_*`, `margin by_indiv`; absent: `bygraphstyle default`, `special by_slope1 .3 / by_knot1 3 / by_slope2 1`, `textboxstyle subtitle subheading` for panel labels.
- §7: `ring(0)` -> "on plotregion1" with `box_alignment = compass2style(position)`; clock to compass: 1-2 NE, 3 E, 4-5 SE, 6 S, 7-8 SW, 9 W, 10-11 NW, 12 N, 0 centre.
- §10: `fcolor` -> fillcolor, `lcolor` the box line, `nobox` no border (`_fr_tbstyle_parse_and_log.ado`).
- bygraph_g.class (read by the executor at `/Applications/StataNow/ado/base/b/bygraph_g.class`): `RunGraph` draws each panel's subtitle as a textbox with `subtitleformat` applied; `set_shrink` reads `shrink/ishrink/overallshrink`; the regions are the graph's `graphregion`/`plotregion` styles.

### Fixtures on disk

`test/fixtures/by_grid_truth.json` (`sizes`, `cells`, `indiv_margin`), `by_chrome_truth.json` (`label_box`), `by_scales_truth.json`, `by_text_truth.json`. S36 adds `by_remainder_truth.json`.

### Tests that pin today's behaviour (flip in place, never delete)

- test/test_by_grid.py::TestNamedNoMore -- nodes asserting the stage-3 words or `subtitleformat()`/`shrink` are named.
- test/test_by_scales.py::TestTheNoteReachesTheUser -- nodes asserting the ring(0) note.
- test_by_side*.py / test_by_chrome*.py (the files `grep -l "drawn beside the panels\|dash_by_label_box\|_dash_plot_margin" test/*.py` lists) -- nodes asserting the beside placement, the first-panel-only legend items, `click_policy == "none"`, the empty-label no-box rule and `panels=` in the margin.
- test/test_by_scales.py:426 strict xfail stays (D-36.j below); not flipped by S36.
- test_help_claims_*.py nodes reading dash.sthlp:2675-2676 ("drawn beside the panels and a note says so. The overall legend is not clickable") and :2744-2745.

The exact red list is measured by 36-01 and written to `<scratch>/36-flips.txt`.

- **D-36.j (ruling)** test/test_by_scales.py:426 (`style(rescale) noyrescale` x tick count) is a tick-count model in `_dash_finish_count_ticks`, owned in batch 12 by S35 (R11) and later by S45; S36 does not resolve it. The xfail stays strict; the hand-back note names it for S45/S61.

## User stories

- **US-36.1** As a Stata user, I want `by(foreign, graphregion(fcolor(gs15)) plotregion(lcolor(black)))` to restyle the array so that the dashboard matches my graph.
- **US-36.2** As a Stata user, I want `by(foreign, legend(ring(0) pos(5)))` to put the legend inside the array where twoway puts it, and clicking a key to hide that series in every panel.
- **US-36.3** As a Stata user with many panels, I want the panel margins, label boxes, `subtitleformat()` and the shrink words drawn as twoway draws them.
- **US-36.4** As a Stata user whose value label is "", I want the one-panel by() graph to keep its panel chrome as twoway keeps it.
- **US-36.5** As a dashboard user moving a filter, I want a panel left with no rows to disappear rather than sit empty, in the saved page and the served app.

## Business requirements

- **BR-36.1** by()'s `graphregion()` and `plotregion()` are drawn on the array in both modes; nothing is printed for them.
- **BR-36.2** `legend(ring(0))` inside by() is drawn inside the array (an empty cell or over a panel) with no note; the overall legend toggles a series in every panel on click.
- **BR-36.3** The outer axes alternate sides when the scheme says so.
- **BR-36.4** Each panel's plot-region margin equals twoway's for 2, 4 and 10 panels and under `iscale()`.
- **BR-36.5** `subtitleformat()` and `subtitle(, fcolor() lcolor() nobox)` restyle every panel label and its box; the shrink words behave as measured.
- **BR-36.6** A one-panel by() with an empty value label draws the label box and the Graphs-by note as twoway does (measured).
- **BR-36.7** A panel with no kept rows after a filter move is hidden, and shown again when rows return, saved and served.

## Technical requirements

- **TR-36.1** `_dash_by_region_options(by_raw)` (new, after `_dash_by_layout_options` :38408): `{"graphregion": <merged stage-3 arguments>, "plotregion": ..., "given": bool}` through `_dash_by_word`; the panel builders call `_dash_apply_regions(fig, {**graph_opts, **by_regions}, scheme, seen, key)` for every panel and chrome cell (D-36.a). Copy list: after `"_dash_by_layout_options",` in the functions tuple.
- **TR-36.2** `_dash_by_keys` returns `legend_cell` for ring(0): the nearest empty cell to the compass of `legend_position` (default the scheme's `clockdir by_legend_position`), else None; `_dash_by_side` places the legend cell there, or inside the compass panel through `_dash_apply_legend`'s ring(0) path (D-36.b); the `_dash_warn_once` at :38447-38452 is deleted; `_dash_parse_by`'s docstring gains `graphregion() plotregion() subtitleformat() the shrink words`.
- **TR-36.3** `_dash_by_legend_cell` builds items over every panel (D-36.c) and sets `click_policy="hide"`; constant `_DASH_BY_LEGEND_SYNC_JS` only on the fallback path (copy list after `"_DASH_TICK_EVERY_JS",`).
- **TR-36.4** `SchemeParser.by_flags` reads the alternate stubs (D-36.d); `_DASH_BY_FLAG_DEFAULTS` gains `"alt_xaxes": False, "alt_yaxes": False`; `_dash_by_outer_axes` moves the outer axes by row/column parity when set (`fig.left`/`fig.right`, `fig.below`/`fig.above` list reassignment as `_dash_axis_alternate` does, :30895-30908).
- **TR-36.5** `_dash_plot_margin(scheme, graph_opts, panels=1, mult=None)`: when *mult* is given the per-side fraction is `r x mult` (D-36.e); the by() builders (saved `_make_figure_body`'s by() branch and the template's panel builder) pass `mult=_dash_by_panel_scale(full_n, by_raw)`. The saved `_make_figure_body` edit is one keyword in one call (S36 is batch 12's `_make_figure_body` editor; S35 and S37 do not edit it).
- **TR-36.6** `_dash_by_text_options` reads `subtitleformat()` (stage 2, :26126) and the `subtitle()` textbox words `fcolor lcolor nobox` (through `_DASH_TBSTYLE_ROWS`); `_dash_by_label_box(fig, scheme, mult=1.0, box=None)` takes `box = {"fill", "line", "nobox", "text"}` and draws it (D-36.f): `nobox` -> return None and `title.visible = True`; `fcolor` -> the `LinearColorMapper` palette's one colour; `lcolor` -> `bar_line_color`.
- **TR-36.7** `_dash_by_panel_scale` reads the shrink words per the fixture (D-36.g); `_dash_by_chrome`'s overall titles take the `overallshrink` rule.
- **TR-36.8** `_dash_by_label_box` draws an empty label's box when `getattr(fig, "_dash_by_panel", False)` (D-36.h); the builders stamp `fig._dash_by_panel = True` on every panel; the one-panel route never takes the no-faceting sentinel on an empty label (`_dash_parse_by`'s varlist decides).
- **TR-36.9** D-36.i: `_FILTER_JS` gains `function dash_panels_visibility(pairs, sources, figs)` between `dash_kernel` and the "// agg_sources is a Bokeh model list" comment, called after the derived-source copy loop; `_build_filter_widgets` passes `by_panels=[(fig_index, [source_indices])]` through the callback `args` (`by_panel_figs`, `by_panel_sources` as model lists and `by_panels_json` as index pairs, no names); the three `FilterBuilder.build_*` gain the default args `"by_panel_figs": [], "by_panel_sources": [], "by_panels_json": "[]"` beside their existing defaults. Served: `_dash_panel_visibility(figures, facet_map)` (new, after `_dash_refinish_axes` :32300; copy list after `"_dash_refinish_axes",`) sets `visible` from each panel's own sources' row counts; `_generate_app_source` emits `_dash_panel_visibility(figures, facet_map)` directly after the emitted `_dash_refinish_axes(` call. `js_runner.run_filter_js_block`'s helper slice carries the new function by position.
- **TR-36.10** Help (R3): "Faceting with by()" :2670-2682 (ring(0) and clickable sentences) and :2740-2750 (the implemented list and the subtitleformat/shrink sentence) rewritten; a new sentence under "Filters" (:1680-1792) and "Server Mode" (:1927-2308) on hidden emptied panels; TWOWAY_COVERAGE_AUDIT.md row "Facets" (:143) gains the drawn words.
- **TR-36.11** `test/function_test_map.py` entries for `_dash_by_region_options`, `_dash_panel_visibility`, `dash_panels_visibility` (as `app:` or JS twin per the map's convention for `_FILTER_JS` helpers), `_dash_by_label_box.<locals>` if new locals appear; parity `CORPUS` entries `"by graphregion plotregion"`, `"by legend ring(0) hole"`, `"by subtitleformat nobox"`; `MOVE_CORPUS` `"by panel emptied by a dropdown"` (R8).

### Code and verbatim texts (copy, do not paraphrase)

**`_dash_by_region_options(by_raw)`** (after `_dash_by_layout_options`):

```python
def _dash_by_region_options(by_raw):
    """by()'s own graphregion()/plotregion() copies (WP-31 D10, D-36.a):
    ``{"graphregion": str, "plotregion": str, "given": bool}``, each the
    arguments of every copy joined ", " (the renderer's merged-copy form)."""
    out = {"graphregion": "", "plotregion": "", "given": False}
    try:
        text = by_raw if isinstance(by_raw, str) else str(by_raw or "")
    except Exception:  # noqa: BLE001
        return out
    _, comma, subs = text.partition(",")
    if not comma:
        return out
    parts = {"graphregion": [], "plotregion": []}
    for tok in _dash_by_tokens(subs.strip()):
        row, _typed, paren, arg = _dash_by_word(tok)
        if row in parts and paren:
            parts[row].append(arg)
    for k, v in parts.items():
        if v:
            out[k] = ", ".join(v)
            out["given"] = True
    return out
```

The panel builder (saved and served) then does `_reg = _dash_by_region_options(go.get("by", "")); _opts = dict(go); for k in ("graphregion", "plotregion"): if _reg[k]: _opts[k] = _reg[k]; _dash_apply_regions(fig, _opts, scheme, seen, key)`.

**`_dash_panel_visibility(figures, facet_map)`** (after `_dash_refinish_axes`):

```python
def _dash_panel_visibility(figures, facet_map):
    """Hide a by() panel whose every own source kept no row after a served
    move, show it when rows return (WP-31 D10, D-36.i).  Idempotent."""
    figs = dict(figures or {})
    for _g, items in (facet_map or {}).items():
        for item in items or ():
            fk = item[0] if isinstance(item, (list, tuple)) else item
            f = figs.get(fk)
            if f is None or not getattr(f, "_dash_by_panel", False):
                continue
            srcs = [r.data_source for r in f.renderers
                    if getattr(r, "data_source", None) is not None]
            if not srcs:
                continue
            rows = 0
            for s in srcs:
                d = getattr(s, "data", None) or {}
                rows += max((len(v) for v in d.values()), default=0)
            f.visible = rows > 0
```

**`dash_panels_visibility`** (in `_FILTER_JS`, before the agg_sources comment; `pairs` is `JSON.parse(by_panels_json)`, a list of `[fig_index, [source_indices]]`):

```js
function dash_panels_visibility(pairs, sources, figs) {
    for (const p of pairs) {
        const f = figs[p[0]];
        if (!f) continue;
        let rows = 0;
        for (const si of p[1]) {
            const s = sources[si];
            if (!s || !s.data) continue;
            for (const k of Object.keys(s.data)) { rows = Math.max(rows, (s.data[k] || []).length); }
        }
        const vis = rows > 0;
        if (f.visible !== vis) f.visible = vis;
    }
}
```

Call site, after the derived-source copy loop: `if (typeof by_panels_json !== "undefined" && by_panels_json) dash_panels_visibility(JSON.parse(by_panels_json), by_panel_sources, by_panel_figs);`.

**Help sentences** (Faceting with by(), replacing :2675-2676 and :2744-2746):

`{cmd:by(, legend(ring(0)))} draws the legend inside the array: in an empty cell when the grid has one, else over the panel at the legend's clock position.  Clicking a key of the overall legend hides that series in every panel.  {cmd:by(, graphregion())} and {cmd:by(, plotregion())} restyle the array, {cmd:subtitleformat()} restyles every panel label, {cmd:subtitle(, fcolor() lcolor() nobox)} restyle the label box, and the shrink words ({cmd:shrink}, {cmd:ishrink}, {cmd:overallshrink} and their {cmd:no} forms) size the panels as {cmd:twoway} does.  A one-panel {cmd:by()} whose value label is empty keeps its label box and the Graphs-by note.`

Filters and Server Mode (one sentence each): `A {cmd:by()} panel left with no rows by a filter is hidden, its cell left blank, and shown again when rows return.`

**BUGS.md Resolution (D10):** `  - Resolution: Fixed <ddmonyyyy> (WP-31, D10). _dash_by_region_options hands by()'s graphregion()/plotregion() to _dash_apply_regions on every panel; _dash_by_keys and _dash_by_side place legend(ring(0)) inside the array; _dash_by_legend_cell spans every panel's renderers with click_policy hide; _dash_by_outer_axes alternates the outer axes when the scheme's by_alternate stubs say so; _dash_plot_margin takes the f(k) x iscale() multiplier; _dash_by_label_box draws subtitleformat(), fcolor(), lcolor(), nobox and an empty label's box; _dash_by_panel_scale reads the shrink words; dash_panels_visibility (saved) and _dash_panel_visibility (served) hide a panel a filter empties; in both renderers. Pinned by test/test_by_remainder.py::TestLegend::test_items_span_panels, test/test_by_remainder.py::TestMargin::test_count, test/test_by_remainder.py::TestEmptiedPanels::test_saved_hidden, test/test_wp31_truth.cscript U36-02; fixture test/fixtures/by_remainder_truth.json. Residual, deferred (WP-31): the x tick count under style(rescale) noyrescale (test/test_by_scales.py:426) is the axis finishers' model (sections 35, 45) (GAPS3 D10 Tracked). Closes GAPS3 D10 (WP-31, D10).`

**CHANGELOG Results line (D10):** `- by() draws its remainder. dash scatter mpg weight, by(foreign, legend(ring(0))) drew the legend beside the array with a note, now inside it; the overall legend was not clickable, now a click hides the series in every panel; by(foreign, graphregion(fcolor(red))) was named and ignored, now drawn; a panel's plot-region margin used the panel count, now twoway's f(k) x iscale() (<old fraction> -> <new> for four panels); subtitleformat(), the shrink words and subtitle(, fcolor() lcolor() nobox) are drawn; a one-panel by() with an empty value label drew no label box, now twoway's chrome; a panel a filter empties is hidden in both modes. (WP-31, D10)`

**The Chrome check of 36-02** writes `<scratch>/s36/legend-click.txt` as one line, `cross_plot_items: ok` or `cross_plot_items: error <first console line>`; the fallback is taken on `error`.

### Both-mode call sites (grep first; anchors drift)

| Change | Saved renderer (`DashRenderer`) | Served app (`ServerAppBuilder` template) | Finder |
|---|---|---|---|
| by() regions on every panel | the by() branch of `_make_figure_body` where `_dash_apply_regions(` is called per panel (:43782 comment "plotregion(), graphregion(), bgcolor() and plotbgcolor(): one") | the emitted line :49465 (`"        # plotregion(), graphregion(), bgcolor(), plotbgcolor(): the"`) and its call two lines below | `grep -n "_dash_apply_regions(" dash_render.py` |
| legend cell placement | `_dash_by_side` (module function, shared by copy) | the same function, copied | `grep -n '"_dash_by_side",' dash_render.py` |
| margin multiplier | `_dash_plot_margin(` call in `_make_figure_body`'s by() branch | the emitted `_dash_plot_margin(` line | `grep -n "_dash_plot_margin(" dash_render.py` |
| label box words | `_dash_by_label_box(` call in `_dash_by_chrome_figures` (:37776) | the same function, copied | `grep -n "_dash_by_label_box(" dash_render.py` |
| panel stamp `_dash_by_panel` | both builders, directly after the figure is made | the emitted figure line | `grep -n "_dash_hull_axes = " dash_render.py` (the stamp goes beside the hull stamp) |
| emptied panels | `_FILTER_JS` + `_build_filter_widgets` args | `_dash_panel_visibility(figures, facet_map)` emitted after `_dash_refinish_axes(` | `grep -n "_dash_refinish_axes(" dash_render.py` |

Every module-level name the served app needs is in the functions tuple (:46822-47270) by the anchors TR-36.1 and TR-36.9 give; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` fails on a missing one, and `test_mode_parity.py`'s `CORPUS` entries fail on a drawing difference.

### Measured red list procedure (36-01)

Apply the fix on a scratch copy of the worktree (`cp -r $WT <scratch>/s36/sim`) only far enough to change the warning text, the legend `click_policy`, the margin keyword and the label-box rule; run `python3 -m pytest test/test_by_grid.py test/test_by_scales.py test/test_by_chrome*.py test/test_by_side*.py test/test_help_claims_*.py -q -n0 -p no:cacheprovider -rf` there; copy the failing node ids into `<scratch>/36-flips.txt` with the one-line reason each; delete the scratch copy. The real flips happen in 36-04 on `$WT`.

## Boundaries

- Not `_dash_refinish_axes`, `_dash_finish_count_ticks`, `_DASH_AXIS_FINISH_JS` (S35, R11); not the by() tick-count model (D-36.j).
- Not `_dash_region_spec`, `_dash_apply_regions`'s body, `_dash_margin_sides`, the margin grammar (S37): S36 passes arguments only.
- Not the legend's own geometry options (S31, batch 10 landed; S36 reads `_dash_apply_legend` unchanged).
- Not `_dash_stale_kind` or the stale cue; not the estimator JS; not `_dash_option_rules`.
- No refusal added: the by() grammar's refusals landed in WP-30 P1.15b.

## Stata truth

**New extractor** `scripts/extract_by_remainder_truth.do` (path-free form of scripts/extract_by_grid_truth.do :1-45), run as `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s36/x $WT/scripts/extract_by_remainder_truth.do`, writing `test/fixtures/by_remainder_truth.json` (`git add -f`; `_meta` with the five keys plus `by_alt_stubs`). twoway only; `sysuse auto`; `set scheme s2color` unless named; `rep78` recoded to 2, 4 and 10 groups for the panel counts.

| Key | twoway command (`scatter mpg weight, by(<g>, ...)`) | Recorded |
|---|---|---|
| `regions.graph_red`, `regions.plot_blue`, `regions.both`, `regions.outer_vs_by` | `by(foreign, graphregion(fcolor(red)))`; `by(foreign, plotregion(fcolor(blue)))`; both; `graphregion(fcolor(green)) by(foreign, graphregion(fcolor(red)))` | SVG rect fills and their boxes: the canvas rect, the array rect, each panel's frame rect |
| `legend.ring0_hole`, `legend.ring0_full`, `legend.ring0_pos5` | `by(rep78, legend(ring(0)))` with 5 panels (one empty cell); `by(foreign, legend(ring(0)))`; `by(rep78, legend(ring(0) pos(5)))` | the legend box's centre relative to the array and the panel frames; which cell holds it |
| `alt.stubs`, `alt.yes` | the stub lines; a scheme copy with the alternate stubs set yes, `by(rep78)` | sides of the outer axes per row/column |
| `margin.<2,4,10>`, `margin.iscale_half` | `by(g2)`, `by(g4)`, `by(g10)`, `by(g4, iscale(.5))` | each panel's plot-region inset in px over min(W, H) of the panel; `.Graph.style.indiv_margin` |
| `subtitleformat.size_large_color_red`, `subtitle.fcolor_lcolor`, `subtitle.nobox` | `by(foreign, subtitleformat(size(large) color(red)))`; `by(foreign, subtitle(, fcolor(yellow) lcolor(blue)))`; `by(foreign, subtitle(, nobox))` | label font size and fill, box fill and stroke, box present |
| `shrink.<word>.<2,10>` for `noshrink noishrink nooverallshrink shrink ishrink overallshrink` | `by(g2, <word>)`, `by(g10, <word>)` | marker radius, label font px, title font px, each over the plain graph's |
| `one_panel.empty_label` | `label define e 1 ""`, `label values one e`, `by(one)` | label box present (rect at the panel's top), its height; the Graphs-by note text |
| `refusals.regions_comma` | `capture noisily twoway scatter mpg weight, by(foreign, graphregion(fcolor(red), x))` | rc, first error line (documentation; dash's WP-30 grammar refusal already covers nested commas) |

**Truth block** (R1): `test/test_wp31_truth.cscript`, header `* ==== S36 D10: The by() remainder ====`, helpers `_ub_*` above it, cases ending `_w31_done U36-0k "<what>"`:
- **U36-01** `dash scatter mpg weight, by(foreign, graphregion(fcolor(red)) plotregion(fcolor(blue)))`: every panel's `border_fill_color` is `#ff0000` and `background_fill_color` `#0000ff` (or the fixture's array rule), saved and served; the log holds no `sub-option(s) not implemented`.
- **U36-02** `by(rep78, legend(ring(0)))` (five panels): the legend sits in the empty cell the fixture names; `click_policy == "hide"`; each item references as many renderers as panels; no `drawn beside the panels` in the log.
- **U36-03** `by(g4, iscale(.5))`: each panel's margin fraction equals `margin.iscale_half` within 1e-3 (both modes).
- **U36-04** `by(foreign, subtitleformat(size(large) color(red)) subtitle(, fcolor(yellow) lcolor(blue)))`: the label box colours and the label font equal the fixture's; `subtitle(, nobox)` leaves no `dash_by_label_box`.
- **U36-05** `by(one)` with the empty label: one panel, a `dash_by_label_box` present, the Graphs-by note present, both modes.
- **U36-06** `dash scatter mpg weight, by(foreign) filter(rep78)` on the parity frame: after the served Select moves to a value no Foreign row has (the generated app, the callback fired as UL-08 fires it), the Foreign panel's `visible` is False and back to True on the reset value.

## TDD test stubs

### Regression tests, `test/test_by_remainder.py` (red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, spec)` as test_by_grid.py's `_draw`; `_panels(figs)`; node moves through test_saved_filter_layers `_render`/`_move`; served moves through test_mode_parity `_served_after_move`; the fixture read once.
- Test: the fixture has six `_meta` keys and every table key -- `TestTheFixture::test_meta`, `::test_keys` (guard after 36-01).
- Test: by()'s graphregion/plotregion restyle every panel; the by() copy wins over the outer copy; no warning -- `TestRegions::test_each_panel[mode]`, `::test_by_copy_wins[mode]`, `::test_silent[mode]` (red: named).
- Test: ring(0) with a hole places the legend cell in the fixture's cell; without a hole inside the compass panel; the warning is gone -- `TestLegend::test_hole[mode]`, `::test_full_grid[mode]`, `::test_no_warning[mode]` (red).
- Test: the legend's items reference every panel's renderer and `click_policy == "hide"`; hiding through the harness (or the fallback JS under node) hides all -- `::test_items_span_panels[mode]`, `::test_click_hides_every_panel` (red).
- Test: with the alternate stubs set, outer y axes alternate right by row and x axes top by column; unset nothing moves -- `TestAlternateAxes::test_alternate[mode]`, `::test_default_unchanged[mode]` (red).
- Test: the panel margin fraction is `r x f(k) x iscale` for 2, 4, 10 panels and `iscale(.5)` -- `TestMargin::test_count[mode-n]`, `::test_iscale[mode]` (red: f(panels)).
- Test: `subtitleformat()` sets the label size and colour; `subtitle(, fcolor() lcolor())` the box colours; `nobox` removes the box and shows the Title -- `TestLabelBox::test_subtitleformat[mode]`, `::test_box_colours[mode]`, `::test_nobox[mode]` (red).
- Test: each shrink word follows the fixture for 2 and 10 panels -- `TestShrink::test_word[mode-word-n]` (red or guard per word).
- Test: a one-panel by() with an empty label draws the box and the note -- `TestOnePanel::test_chrome[mode]` (red).
- Test: a saved move emptying a panel sets `visible` false and a reverting move true; the served twin the same; the gridplot keeps the cell -- `TestEmptiedPanels::test_saved_hidden`, `::test_saved_restored`, `::test_served_hidden`, `::test_served_restored`, `::test_a_hidden_panel_keeps_its_cell` (red).
- Test: `_FILTER_JS` holds `dash_panels_visibility` between `dash_kernel` and the agg_sources comment; the three builders carry the defaults; the template emits `_dash_panel_visibility` -- `TestTheWiring::test_js_position`, `::test_builder_defaults`, `::test_template_call` (red).

### Cases in cscripts
- `test_wp31_truth.cscript` U36-01..U36-06 (red at base).

### Flips (in place, each with a `Flipped:` line; red at base after the flip)
From `<scratch>/36-flips.txt`; docstrings gain "twoway draws by()'s regions, legend(ring(0)) inside the array, a clickable overall legend, the f(k) x iscale margin, subtitleformat() and the label box words, and an empty label's chrome (WP-31 D10)" or "an emptied panel is hidden after a move (WP-31 D10)".

### Parity corpus (R8; guards at base)
TR-36.11's entries under `# WP-31 D10: the by() remainder`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| by() regions | pytest `TestRegions`; U36-01 | `regions.*` | yes |
| legend ring(0), clickable | pytest `TestLegend` (Chrome harness or node fallback); U36-02 | `legend.*` | yes |
| alternate axes | pytest `TestAlternateAxes` | `alt.*` | yes |
| margin multiplier | pytest `TestMargin`; U36-03 | `margin.*` | yes |
| label box, subtitleformat, shrink | pytest `TestLabelBox`, `TestShrink`; U36-04 | `subtitleformat.* subtitle.* shrink.*` | yes |
| one-panel empty label | pytest `TestOnePanel`; U36-05 | `one_panel.*` | yes |
| emptied panels after a move | pytest `TestEmptiedPanels` (node + served); U36-06; `MOVE_CORPUS` | -- | yes |
| wiring | pytest `TestTheWiring`; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` | -- | yes |

**Acceptance criteria**
- **AC-36.1** Every panel's border/frame colours equal the fixture's under by()'s regions in both modes, silently.
- **AC-36.2** ring(0) lands in the fixture's cell or panel; items span every panel; `click_policy == "hide"`; the beside-the-array warning no longer exists in dash_render.py (`grep -c "drawn beside the panels" dash_render.py` prints 0).
- **AC-36.3** The margin fraction equals `r x f(k) x iscale` within 1e-3 for 2, 4, 10 panels.
- **AC-36.4** The label box, `subtitleformat()`, `nobox` and the shrink words match the fixture.
- **AC-36.5** The one-panel empty-label graph draws the box and the note in both modes.
- **AC-36.6** A panel with zero kept rows is `visible == False` after a saved move (node) and a served move, and `True` after a reverting move.
- **AC-36.7** `WP31_ONLY=S36` prints U36-01..U36-06 PASS, no SKIP; one green commit `(WP-31 D10)`.

## Tasks

**Commit boundary.** Tasks 36-01 to 36-04 form the one D10 commit, subject `Draw by()'s regions, legend, axes, margins and label box, and hide emptied panels (WP-31 D10)`, made by 36-04 on `wp31-s36` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s36` after the section's tests and the truth block ran green. Body: `<scratch>/36-01-failure.txt`, the measured defect, the change in both renderers, then `Regression:` lines, `Flipped:` lines from `<scratch>/36-flips.txt`, `Fixture: test/fixtures/by_remainder_truth.json (scripts/extract_by_remainder_truth.do)`, `BUGS.md: "<title>" (closed)`, `GAPS3: D10 Tracked`.

<task type="auto" id="36-01">
  <name>Measure twoway and write the failing tests</name>
  <files>scripts/extract_by_remainder_truth.do, test/fixtures/by_remainder_truth.json, test/test_by_remainder.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-12-base.txt` and the branch is `wp31-s36`; `mkdir -p <scratch>/s36/x`. Create scripts/extract_by_remainder_truth.do by the "Stata truth" table (head copied from scripts/extract_by_grid_truth.do :1-45; the alternate-stub scheme copy written to the work directory), run it through the slot, `git add -f test/fixtures/by_remainder_truth.json`, and record the branch values (regions rule, legend cells, shrink effects, alt stub names, one-panel chrome) in `<scratch>/s36/measured.txt`. Create test/test_by_remainder.py with exactly the classes of "TDD test stubs", branching tests reading the fixture. Append the U36 block to test/test_wp31_truth.cscript above `* ==== append new blocks above this line ====`. Run `python3 -m pytest test/test_by_remainder.py -q -n0 -p no:cacheprovider -rf > <scratch>/s36/36-01.log 2>&1` and the truth block through the driver with `WP31_ONLY=S36`; write `<scratch>/36-01-failure.txt` (base sha, each failing node and FAIL case with its reason, the guards that passed). List the pinned nodes a simulated fix turns red into `<scratch>/36-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/by_remainder_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'by_alt_stubs', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c FAILED <scratch>/s36/36-01.log` is at least 25 and no FAILED line names `TestTheFixture`; `grep -c "U36-0[1-6] FAIL" <scratch>/s36/run_test_wp31_truth.log` prints 6; `grep -c SKIP <scratch>/s36/run_test_wp31_truth.log` prints 0; `test -s <scratch>/36-01-failure.txt`.]]></verify>
  <done>twoway's by() regions, legend placement, axes, margins, label boxes, shrink words and empty-label chrome were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="36-02">
  <name>Draw the by() regions, legend and axes</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In dash_render.py: add `_dash_by_region_options` after `_dash_by_layout_options` (:38408) and call `_dash_apply_regions` with by()'s copies in the saved by() panel builder and the template's panel builder (TR-36.1; the by() copy replaces the outer one in the dict passed); `_dash_by_keys` (:38108) computes `legend_cell` (D-36.b) and `_dash_by_side` (:38422) places the cell there or inside the compass panel, deleting the `_dash_warn_once` at :38447-38452; `_dash_by_legend_cell` (:38074) builds items over every panel and sets `click_policy="hide"` (D-36.c), with `_DASH_BY_LEGEND_SYNC_JS` and the `visible` CustomJS only if the Chrome check below fails; `SchemeParser.by_flags` and `_DASH_BY_FLAG_DEFAULTS` (:26070) gain the alternate flags and `_dash_by_outer_axes` (:37929) moves the outer axes by parity (D-36.d). Copy-list entries: `"_dash_by_region_options",` after `"_dash_by_layout_options",`; the JS constant after `"_DASH_TICK_EVERY_JS",` if used. Build `dash scatter mpg weight, by(rep78, legend(ring(0)))` as a saved page under `<scratch>/s36/legend.html`, open it through test_csp_browser.py's DevTools harness, click the first legend key and read every panel's first renderer `visible`; record the result in `<scratch>/s36/legend-click.txt` and take the fallback if any console error names the renderer. Add function_test_map entries. Run `python3 -m pytest test/test_by_remainder.py -q -n0 -p no:cacheprovider -k "Regions or Legend or AlternateAxes or Fixture"`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "drawn beside the panels" dash_render.py` prints 0; `grep -c "click_policy=\"hide\"" <(sed -n 38074,38110p dash_render.py)` prints at least 1; `test -s <scratch>/s36/legend-click.txt`.]]></verify>
  <done>by()'s regions were drawn on every panel, the ring(0) legend moved into the array with items spanning every panel and a hide click policy, and the outer axes alternated when the scheme said so.</done>
</task>

<task type="auto" id="36-03">
  <name>Draw margins, labels and hide emptied panels</name>
  <files>dash_render.py, test/js_runner.py, test/function_test_map.py</files>
  <action><![CDATA[
    In dash_render.py: `_dash_plot_margin(scheme, graph_opts, panels=1, mult=None)` (:29168; D-36.e) and the two by() builders passing `mult=_dash_by_panel_scale(full_n, by_raw)` (the saved call is in `_make_figure_body`'s by() branch, one keyword; the served call in the template's panel builder lines, one keyword); `_dash_by_text_options` reads `subtitleformat()` and `subtitle()`'s `fcolor lcolor nobox`, `_dash_by_label_box(fig, scheme, mult=1.0, box=None)` draws them (TR-36.6) and draws an empty label's box for a stamped panel (D-36.h; the builders stamp `fig._dash_by_panel = True`); `_dash_by_panel_scale` (:26528) reads the shrink words per the fixture (D-36.g). D-36.i: in `_FILTER_JS` add `function dash_panels_visibility(pairs, sources, figs)` directly before the `// agg_sources is a Bokeh model list` comment and its call after the derived-source copy loop; the three `FilterBuilder.build_*` gain `"by_panel_figs": [], "by_panel_sources": [], "by_panels_json": "[]"` defaults beside their existing default args; `_build_filter_widgets` fills them from the facet map (indices only); add `_dash_panel_visibility(figures, facet_map)` after `_dash_refinish_axes` (:32300), its copy-list entry after `"_dash_refinish_axes",`, and the emitted call in `_generate_app_source` on the line after the emitted `_dash_refinish_axes(` call. Check test/js_runner.py's helper slice still ends at the agg_sources comment (no edit expected; if the slice is bounded by a function name, extend it to the new function). Add function_test_map entries. Run `python3 -m pytest test/test_by_remainder.py test/test_saved_filter_layers.py test/test_statistical_helpers.py -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `python3 -c "import dash_render as d; i=d._FILTER_JS.index('function dash_kernel'); j=d._FILTER_JS.index('// agg_sources is a Bokeh model list'); print(i < d._FILTER_JS.index('function dash_panels_visibility') < j)"` prints True; `grep -c "_dash_panel_visibility(figures, facet_map)" dash_render.py` is at least 2 (the module call site and the emitted line).]]></verify>
  <done>Panel margins took twoway's multiplier, panel labels and boxes took subtitleformat() and the subtitle() box words, the empty label kept its chrome, the shrink words followed the measurement, and panels emptied by a move were hidden in both renderers.</done>
</task>

<task type="auto" id="36-04">
  <name>Flip pins, update help and commit D10</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
    Flip every node of `<scratch>/36-flips.txt` in place with the reason (R9); append TR-36.11's parity entries to test/test_mode_parity.py under `# WP-31 D10: the by() remainder`. Help (R3): rewrite dash.sthlp :2670-2682 (ring(0) inside the array; the overall legend toggles a series in every panel on click), :2740-2750 (graphregion(), plotregion(), subtitleformat(), the shrink words and the subtitle() box words join the implemented list; "Any other sub-option ... is accepted, named in a warning, and ignored" keeps only what remains), and one sentence each under Filters and Server Mode: "A by() panel left with no rows by a filter is hidden, its cell left blank, and shown again when rows return." TWOWAY_COVERAGE_AUDIT.md :143 gains the drawn words. Close the D10 BUGS.md entry (Resolution per BRIEF naming `_dash_by_region_options`, `_dash_by_keys`, `_dash_by_side`, `_dash_by_legend_cell`, `_dash_by_outer_axes`, `_dash_plot_margin`'s `mult`, `_dash_by_label_box`, `_dash_by_panel_scale`, `dash_panels_visibility`, `_dash_panel_visibility`, both renderers; `Residual, deferred (WP-31): the style(rescale) noyrescale tick count (test/test_by_scales.py:426) is the finishers' model (sections 35, 45) (GAPS3 D10 Tracked)`), rewrite the D10 Tracked line ("Partly closed ... open: the style(rescale) noyrescale tick count (BUGS.md ...)" only if S01 opened a residual entry for it; else "Closed" and the residual named in the hand-back), replace the `<!-- WP-31 D10 -->` markers (Results: `by(foreign, legend(ring(0)))` drew the legend beside the array with a note, now inside it; `by(g4, iscale(.5))` margin old fraction -> new; Changed behaviour: none, unless the fixture made a word refused). Run `python3 -m pytest test/test_by_remainder.py test/test_by_grid.py test/test_by_scales.py test/test_mode_parity.py test/test_help_conformance.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` plus every file `<scratch>/36-flips.txt` names, and the truth block through the driver. Stage dash_render.py dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md scripts/extract_by_remainder_truth.do test/test_by_remainder.py test/test_wp31_truth.cscript test/test_mode_parity.py test/function_test_map.py test/js_runner.py (if edited) and the flipped files; `git add -f test/fixtures/by_remainder_truth.json`; commit; grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed (the :426 xfail stays XFAIL, not XPASS); the driver log shows `U36-01 PASS` through `U36-06 PASS` and no SKIP; `git log -1 --format=%s` ends `(WP-31 D10)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D10 -->' CHANGELOG.md` prints 0; `grep -c "drawn beside the panels" dash.sthlp` prints 0.]]></verify>
  <done>D10 was closed in BUGS.md naming tests that exist, its Tracked line rewritten, its markers replaced, the help described by()'s drawn remainder and the hidden emptied panels, and one green commit on wp31-s36 was ready for the merger.</done>
</task>

## Section completion criteria

- by()'s regions, ring(0) legend, clickable overall legend, alternate axes, `f(k) x iscale` margins, `subtitleformat()`, the label box words, the shrink words and the empty-label chrome are drawn in both modes as the fixture says, silently.
- Emptied panels are hidden after a move and shown when rows return, saved (node) and served.
- `by_remainder_truth.json` stamped and named; U36-01..U36-06 PASS; every flip recorded; test_by_scales.py:426 untouched and named in the hand-back.
- One green commit `(WP-31 D10)`; BUGS.md entry closed; Tracked line rewritten; markers replaced; help, audit, maps and corpus updated.

## Notes

- **R12 in batch 12.** S36 is the batch's one editor of `_FILTER_JS`, `_build_filter_widgets`, `_make_figure_body` (one keyword) and `_generate_app_source` (one emitted line and the panel builder's keyword); S35 and S37 must edit none of them (their Boundaries say so). `_dash_refinish_axes` is S35's: S36 adds a sibling call, never a line inside it.
- **The JS helper's position** decides whether `js_runner.run_filter_js_block` carries it; the verify line of 36-03 pins it.
- **Hidden panels and gridplot.** `gridplot` keeps the child; `visible=False` leaves a blank cell. Do not remove the child (the saved page cannot re-add it).
- **Legend over panels.** On the fallback path the `visible` CustomJS is per first-panel renderer; it must not recurse (guard: set only when different).
- **python_exec hazard** (project memory) after each cscript run; a SKIP is not a pass.
- **Shared files.** R1: the U36 block only; R2: `_dash_by_region_options` after `_dash_by_layout_options`, `_dash_panel_visibility` after `_dash_refinish_axes`, the JS constant after `_DASH_TICK_EVERY_JS` only if used; R3: Faceting with by(), one sentence each in Filters and Server Mode; R4: markers replaced; R5: one entry, one Tracked line; R7: one extractor; R8: corpus appended; R9: flips in place; R10: none; R11: untouched.
- **Commit-body line forms** are BRIEF's; `failed at` is `batch-12-base.txt`'s sha.
- **For S37 (batch 12).** `_dash_plot_margin` gains `mult=None` here; S37's margin edits keep the signature.
- **For S45 and S61.** test/test_by_scales.py:426 stays a strict xfail: the panel tick count under `style(rescale) noyrescale` is a finisher model (`special by_slope1/by_knot1/by_slope2`, stata-ground-truth.md §11), to be measured with S45's date-tick work or filed by S61 under M12.
- **Decisions for maintainer ratification.** D-36.a (regions per panel, by() copy wins), D-36.b (ring(0) into an empty cell, else inside the compass panel), D-36.c (cross-panel legend items with a sync fallback), D-36.i (hidden panels keep their blank cell), D-36.j (:426 not resolved here).
