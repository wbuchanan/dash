# Section 55: horizontal after a filter move (P1.9 part b)

> Part of: WP-30 · Items: P1.9b (entry `P1.9b`; REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15, after a move) · Risk: yellow · Batch: 19 (merge order S54, S55, S56) · Depends on: 49 · Blocks: 57 · Tasks: 7, 1 commit · Case prefix: HM

## Review amendments

- Fixed (blocker): TR-55.1 read "S49's mark" on a turned renderer, but S49 sets none. TR-49.4 rebuilds the glyphs in place and keeps `tags`. Turned-ness is now derived from the `layers` argument both hover call sites already pass (:30702, :35487): `_dash_is_horizontal(plot)` plus a glyph class in `_DASH_TRANSPOSE`, so an unmapped class S49 leaves upright stays upright. The tests, 55-01, Risk, Dependencies and Notes now use S49's real names. A new guard covers the unmapped class.
- Fixed (major): `test_no_callback_carries_a_property_name` banned arg strings equal to `x`, `y`, `top`, `left` and similar. S21's plan legitimately holds those as column names and axis letters, so the test would have failed for the wrong reason. It is now `test_no_callback_can_reach_a_glyph`: no callback arg is a `Glyph` or `GlyphRenderer`. HM-03, TR-55.6, BR-55.5, the Resolution and the G9 line now match.
- Fixed (major): TR-55.2 and 55-04 could edit S21's `_dash_axis_plan`, a finisher-chain symbol (A153, R11). S49 lists it as not its own for this reason, and S49's `test_the_saved_plan_carries_bar_heights` with its Stop rule already guarantees HBar heights in batch 17. 55-04 is now a guard check that stops and reports, and S55 edits only `_dash_build_hover`. This resolves the S55 open question.
- Fixed (major): the after-move guarantee covered P1.9's 12 types, but S49 turns 24 (`_DASH_HORIZONTAL_TYPES`) and the manifest scope says "Transposed layers". `_TURNED` and BR-55.1 now cover all 24, and `plot_for` builds every one of them.
- Fixed (minor): `_profile` holds no ranges, so the saved guard now uses `_profile_full` plus Range1d ends and ticks. `TestTheRoleMap` is limited to the classes the fallback reads. The truth helpers now use the reviewed `python:` form. HM-03 is marked as a guard. 55-02 and 55-05 check for SKIP and `ALL CHECKS PASSED`. 55-06 tolerates S14's D-14b fallback.
- Checked at `c96facd`: `_dash_build_hover` 27118, `_drawn_field` 27331, `_bins` 27360-27373, `_segment`/`_band` 27396-27412, the fallback loop 27414-27425, and both call sites passing `layers`. The `function_test_map` keys nested functions (`_dash_build_hover.<locals>._cols_of`). Batch 19: S54 and S56 do not edit `_dash_build_hover`.
- Rejected: restoring the manifest's `_FILTER_JS` height branch and `_dash_copy_redraw_geometry`. IR-13 and S14's D-14b cancel them, and the manifest note and the R2 row are stale (g09.md).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:99 (P1.9) reads "`horizontal` is not drawn on any type". S49 (P1.9a, batch 17) draws it: one transposition helper in both build loops turns every glyph of the 24 types twoway turns (VBar→HBar, VArea→HArea, Quad's sides, Segment/Line/Scatter/LabelSet/Arrow x↔y), and swaps axis variables, titles, date kinds and y2. This section's entry (S01's Appendix B) is the half that happens after a filter move: "the saved page's redraw and the served app's geometry copy write widths and vertical tooltip fields only, so a turned bar or range would be redrawn upright after a filter move".

Two of the three redraw paths that sentence names no longer exist. S14 (P1.17a, batch 5) deleted the saved page's spacing writer (`_FILTER_JS`, dash_render.py:18737-18753 and :18769-18778, the only line that wrote a glyph property, `_g.width = _w` at :18777), its `_build_filter_widgets` JSON and `_dash_copy_redraw_geometry` (:24941-24957, served), because widths no longer depend on the kept rows (register P1.17.3, A61; S14 D-14b). IR-13 binds it: "P1.17.3's cancellation of P1.9's step 5 stands." So the manifest's "the `_FILTER_JS` redraw writes height … through a fixed branch" and "the served `_dash_copy_redraw_geometry` uses height" are void: a turned bar's `height` is a build-time constant that no move touches, in either mode.

What is still wrong at the batch-19 base is the tooltip. `_dash_build_hover` builds the fallback tooltip of a computed or generic layer by reading the glyph's own property names (`_drawn_field(rd.glyph, "x", …)`, `"y"`, `"y0"`/`"x0"`, `"y1"`/`"y2"`), and gives a histogram's bins `mode="vline"` (dash_render.py:27360-27373). On a turned layer those names point at the other axis's column: a turned kdensity's first row names the density as the variable, a turned area (HArea has `y`, `x1`, `x2`, no `x`/`y1`/`y2`) gets no fallback tooltip at all, a turned rcap's ends are listed in the wrong roles, and a turned histogram's tooltip fires by horizontal position across bins stacked vertically. The saved and served pages share the builder (copied by name, :33171; called at :30692 and in the template at :35476), so both modes are wrong the same way, before and after every move. 55-01 measures each at the base and saves the text.

**After this section**, in both modes, before and after every saved and served filter move:
- a turned layer's tooltip has the rows, labels and order of the same layer drawn upright, and a turned histogram's bins answer along the horizontal line (`mode="hline"`);
- turned layers of all 24 types S49 turns (`_DASH_HORIZONTAL_TYPES`) keep their glyph class, bindings and constant widths/heights, by() panels keep their shared transposed scales, `yaxis(2)` keeps the turned layer's x variable on the right axis, and a mixed-orientation graph on a date axis keeps its date axis, each equal to the page S49 builds from the kept rows (parity, pinned by tests that were guards at the base);
- nothing in either page reads a glyph property name from page data (G9).

**Test order and commit rule (rule 7).** One cycle on `wp30-s55`: 55-01 and 55-02 write the regression and guard tests and the parity cases and run them against the unmodified batch-19 base, saving `$S/55-P1.9b-failure.txt` (no commit); 55-03 to 55-06 fix and verify; 55-07 closes the entry, deletes its `WP30_OPEN` key, replaces its one marker and makes the commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — the tooltip builder is shared by every figure of both modes, and the after-move guarantees rest on three earlier sections' code

**Why.**
- `_dash_build_hover` is LOW in the index (research p1-09 §6) but copied verbatim into the served app, which the index cannot see; treat it as MEDIUM. It decides every tooltip of every figure.
- The after-move behaviour is S14's (no geometry writer), S21's (`_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`, `_dash_axis_plan`) and S49's (the transposition). This section must prove them together without editing them.
- The batch-19.0 list in index.md names `_build_filter_widgets` (CRITICAL) for S55; under IR-13 this section does not edit it, and it edits only `_dash_build_hover` (Notes; the index fix is in review-notes g09.md).

**Risk factors.**
1. Reading the turned glyph through a role map could change the upright tooltip if the map were applied to a renderer S49 did not turn.
2. S49 sets no mark on a turned renderer: TR-49.4 rebuilds the glyph models in place and keeps `name` and `tags` as they are, and an unmapped class stays upright with a note. Whether a renderer is turned must be derived, not read from a tag.
3. S21's saved re-finish reads a per-figure plan built in Python (`_dash_axis_plan`, TR-21.10, `bars: centre/size`); if that plan listed VBars only, a turned bar's end halves would fall outside the axis after a saved move, while the served Python hull (`_dash_axis_hull`, which already reads "an HBar's y plus or minus half its height", dash_render.py:23578-23582, :23618-23623) keeps them.
4. A hostile spec could name a data column `height` or `width`; nothing may treat it as a property.

**Mitigation.**
1. The role map applies only to a renderer of a layer `_dash_is_horizontal` (S49's TR-49.2) accepts whose glyph class is a key of `_DASH_TRANSPOSE` (S49's TR-49.1), read from the `layers` argument both call sites already pass (`[(plot_spec, [renderer, ...]), ...]`: saved `layers=locals().get("_plot_renderers", [])`, :30702; served `layers=_plot_rends`, :35487). A renderer in no layer is upright. `TestUprightIsUntouched` compares every CORPUS figure's tooltips with the base's, byte for byte.
2. S49 copy-lists `_dash_is_horizontal` (TR-49.8) and its constants reach the app through `_supply_missing_constants`, so the served copy of `_dash_build_hover` resolves both names; `TestTheRoleMap` asserts the role map agrees with `_DASH_TRANSPOSE` on every class the fallback reads.
3. S49's `TestTheHullSeesTransposedGlyphs::test_the_saved_plan_carries_bar_heights` (batch 17) already holds the plan to HBar heights, and S49 stops if it is red (its Stop rule; R11). `TestAfterASavedMove::test_turned_bars_keep_their_ends_on_the_axis` is a guard here; if it is red at `batch-19-base`, this section stops and reports (55-04). It never edits `_dash_axis_plan`, a finisher-chain symbol (A153, R11, S49 "Not edited").
4. `TestNoPropertyNameFromPageData` pins that no saved callback can reach a glyph or renderer model (so no callback can write a glyph property) and that a column named `height` changes no glyph property after a move.

## Dependencies

- **Depends on: 49** (batch 17): `_dash_is_horizontal(plot)` (TR-49.2), the transposition helper `_dash_transpose_layer` (TR-49.4, which rebuilds glyphs in place on the same renderer and sets no mark), its per-class map `_DASH_TRANSPOSE` (TR-49.1: glyph class name → (new class name, pairs to swap)) and `_DASH_HORIZONTAL_TYPES` (the 24 types), swatches and keys skipped, `_DASH_X_COORDS` gaining `"x2"` (HArea), `_dash_axis_vars`/`_dash_figure_date_kind`/`_dash_axis_labels`/`_compute_secondary_range` swapped, rcap caps rotated (`dash_cap`), and `test/fixtures/horizontal_truth.json` with S49's `test/test_horizontal.py`.
- Landed before and read here (not edited): S14 (no geometry writer in either mode), S17 (the fallback tooltip's measure row), S21 (served `_dash_refinish_axes` from `_on_filter_change`; saved `_DASH_AXIS_FINISH_JS` at the end of `_FILTER_JS`, its plan from `_dash_axis_plan`), S35 (date kinds per axis), S45 (recast-resolved types), S48/S53 (by() grids and shared axes), S01 (entry `P1.9b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.9b -->` under `### Fixed in WP-30`, the S55 stub `* ==== S55 P1.9b: horizontal after a filter move ====`, the map anchor `# WP-30 S55 (P1.9b): horizontal after a filter move (P1.9 part b)`).
- **Blocks: 57.** S57 (batch 20) audits the final served move path for thread safety; this section adds nothing to it.
- **Parallel batch: 19**, merge order S54, S55, S56. **Can run with** S54 (`_dash_name_save`, toolbar) and S56 (`_make_figure_body`, `_generate_app_source`, SchemeParser, dash.ado): neither edits `_dash_build_hover`, and this section edits none of theirs. S54 and S56 also extend `test/test_mode_parity.py` (S54 its harness, S56 CORPUS cases); all append (R8).

## Evidence

Anchors at `c96facd`; S14, S17, S21, S35 and S49 move them, so the executor re-finds each by symbol at `batch-19-base`.

### E1. The fallback tooltip reads glyph property names (dash_render.py, `_dash_build_hover`, 27118-27426)

```python
27331         def _drawn_field(glyph, prop, data):
27334             v = getattr(glyph, prop, None)
27335             v = v.get("field") if isinstance(v, dict) else getattr(v, "field", v)
...
27360         def _bins(rd, data):
...
27370             return ([(_bin_label, f"@{{left}}{{{_p}}} to @{{right}}{{{_p}}}"),
27373                      ("Count", "@{top}")], "vline")
27375         def _point_or_line(rd, data):
27376             fx = _drawn_field(rd.glyph, "x", data)
27377             fy = _drawn_field(rd.glyph, "y", data)
...
27396         def _segment(rd, data):
27397             ends = [(_drawn_field(rd.glyph, p, data), role) for p, role in
27398                     (("y0", "y1"), ("x0", "x1"), ("y1", "y2"), ("x1", "x2"))]
...
27404         def _band(rd, data):
27405             fx = _drawn_field(rd.glyph, "x", data)
27406             f1 = _drawn_field(rd.glyph, "y1", data)
27407             f2 = _drawn_field(rd.glyph, "y2", data)
...
27414         for _shape in (_bins, _point_or_line, _range, _segment, _band):
...
27424                 fig.add_tools(HoverTool(tooltips=_fb_fields,
27425                                         renderers=[_rd], mode=_fb_mode))
```

The comprehensive tool (`_fields_for`, from :27227) names data columns (`@{varname}`), not glyph properties, so it is orientation-proof already; only the fallback (used when no renderer carries the layer's variables: histogram, kdensity, function, the fits, pc literals, rcapsym) reads the glyph. The builder is one function in both modes: saved call :30692, served (generated) :35476, copied by name (:33171). S17 replaces `("Count", …)` by the measure's name (Density, Frequency, …); this section keeps S17's rows and changes only the mode.

### E2. What a turned glyph names (research p1-09 §3 M5, `proto.py`; S49's map)

| Upright | Turned | Upright role → turned property |
|---|---|---|
| VBar | HBar | x→y, top→right, bottom→left, width→height |
| VArea | HArea | x→y, y1→x1, y2→x2 |
| Quad | Quad | left→bottom, right→top, bottom→left, top→right |
| Segment, Line, Scatter, LabelSet, Arrow | same class | x↔y, x0↔y0, x1↔y1 |

Every row is the restriction of one involution on names: `x↔y, x0↔y0, x1↔y1, x2↔y2, left↔bottom, right↔top, width↔height`. So a role read through it on a turned glyph returns the upright column.

### E3. No geometry is written after a move (S14 D-14b; this file's base)

At `c96facd`, `_FILTER_JS` (18562) wrote one glyph property, the spacing writer (:18777 `for (const _g of (_dspacing_glyphs[_di] || [])) { _g.width = _w; }`), and the served app copied `width` through `_dash_copy_redraw_geometry` (:24941; called at :36042). S14 deleted both with their JSON and args (S14 AC-14.7: `grep -c "_tag_spacing\|dash_spacing\|derived_spacing\|_dash_copy_redraw_geometry" dash_render.py` prints 0). What a move still writes, in both modes, is data: the saved derived-copy loop (`_dsrcs[_di].data = _nd;`) and CDSView filters; the served `_live.data = _dash_keep_jitter(dict(_new.data), …)` (:36030-36031). Column names are the same upright or turned (S49 transposes bindings, never data), so the turned bindings read the moved data correctly. The saved histogram recount and kdensity grid write the `top`/`left`/`right` and `x`/`y` columns the turned Quad and Line bind (research p1-09 §4 step 5: "need no change, and tests prove that").

### E4. The axes after a move (S21; read only)

Served: `_dash_refinish_axes(figures, facet_map)` from `_on_filter_change` re-hulls through `_dash_layer_extent` over `_DASH_X_COORDS`/`_DASH_Y_COORDS` (S49 adds `"x2"`) and `_dash_axis_hull`'s HBar half-heights (:23618-23623 at `c96facd`: `glyph_name, centre, size = (("VBar", "x", "width") if letter == "x" else ("HBar", "y", "height"))`). Saved: `_DASH_AXIS_FINISH_JS` at the end of `_FILTER_JS` reads the per-axis plan of `_dash_axis_plan` (TR-21.10: `layers[].fields`, `bars: [{"src", "filt", "centre", "size"}]`), built at page build after S49's transposition. The plan holds field names only (S21's `TestThePlanCarriesNoUserText`).

### E5. Truth (research p1-09 §3 M2, M4; critic 8; S49's fixture)

twoway's horizontal is an exact transpose of the upright drawing (M2: `c2_h: rect x[10.0..30.0] y[1.5..2.5]`, `c11_h` caps perpendicular); `yaxis(2)` is physical (the turned layer's x on the right axis); a date variable's axis follows the layer to y; `(scatter y d) (bar y d, horizontal)` keeps x as dates and y numeric, the reverse order the opposite. twoway has no filter, so after a move the truth is "the page dash builds from the kept rows", which S49's tests compare with twoway.

### E6. Tests that pin today's behaviour

None pins a turned tooltip (S49 is the first to draw one). 55-01 re-measures `grep -rn "vline" test/*.py` and S49's `test/test_horizontal.py` for an assertion of `vline` or of upright roles on a turned layer; each found is flipped in 55-03 with its reason.

### E7. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`)

| Symbol | Risk | Action |
|---|---|---|
| `_dash_build_hover` | LOW (copied into the served app: treat as MEDIUM) | warn; one nested function added, four inner readers routed through it, one mode |
| `_build_filter_widgets`, `_FILTER_JS`, `_generate_app_source`, `_make_figure_body`, `_dash_axis_plan` (S21's finisher chain) | CRITICAL / UNKNOWN / HIGH / CRITICAL / new | **not edited** |

## User stories

- **US-55.1** As a twoway user, I want a turned bar, range, area, histogram or density to stay turned, with the same bars, axes and panels, after I move a filter, in the saved page and the served app, so `horizontal` is as reliable as the upright drawing.
- **US-55.2** As a dashboard viewer, I want the tooltip of a turned layer to name its variables in the same roles and order as the upright layer, and a turned histogram's tooltip to answer along the row I point at, so I read the right numbers.
- **US-55.3** As a maintainer, I want no page script to take a property name from page data, so a hostile column name cannot change a glyph.

## Business requirements

- **BR-55.1** For each of the 24 types S49 turns (`_DASH_HORIZONTAL_TYPES`: area, bar, spike, dropline, dot, histogram, kdensity, rarea, rbar, rspike, rcap, rcapsym, rline, rconnected, rscatter, the five pc types, pci, pcarrowi, function, tsrline) drawn with `horizontal`, a saved or served filter move leaves the layer turned, and the page after the move equals the page built from the kept rows (glyphs, bindings, widths and heights, axes, ticks, titles, legends).
- **BR-55.2** A turned layer's tooltip has the same rows (labels and fields) in the same order as the same layer drawn upright, in both modes, before and after a move; a turned histogram's tooltip answers along a horizontal line.
- **BR-55.3** Under `by()`, every panel keeps its turned layers and the shared scales cover them after a move; with `yaxis(2)`, the turned layer's x variable stays on the right axis and its range follows the kept rows; a graph mixing an upright and a turned layer on a date variable keeps the date axis twoway gives it.
- **BR-55.4** Upright layers' tooltips and pages are unchanged.
- **BR-55.5** No page script can write a glyph property after a move: no filter callback holds a glyph or renderer model, and a data column named `width`, `height` or `__proto__` changes no glyph property.

## Technical requirements

- **TR-55.1 `_dash_build_hover`** (in place; both modes through the copy list; warn).
  - Add a nested function directly before `_drawn_field`:

    ```python
    def _role_prop(rd, prop):
        """The property of *rd*'s glyph that draws the upright role *prop*:
        the role itself, or its mirror when S49 turned the layer."""
    ```

    It returns `prop` unless `id(rd)` is in `_turned`, and then the mirror from the literal involution of E2 (`{"x": "y", "y": "x", "x0": "y0", "y0": "x0", "x1": "y1", "y1": "x1", "x2": "y2", "y2": "x2", "left": "bottom", "bottom": "left", "right": "top", "top": "right", "width": "height", "height": "width"}`), or `prop` itself when absent from it.
  - `_turned` is a set built once, directly before `_role_prop`: `{id(r) for _lp, _lr in (layers or []) if _dash_is_horizontal(_lp) for r in _lr if isinstance(r, GlyphRenderer) and type(r.glyph).__name__ in _DASH_TRANSPOSE}`. S49 sets no mark (TR-49.4 keeps `tags`), so turned-ness is derived from the layer spec S49 itself reads, and an unmapped class, which S49 leaves upright, is upright here too. A renderer in no layer (a hand-built call without `layers`) is upright. `GlyphRenderer` is imported locally if `_dash_build_hover` does not already import it.
  - `_point_or_line`, `_segment` and `_band` call `_drawn_field(rd.glyph, _role_prop(rd, <role>), data)` for each of their roles; their row labels, order and fallbacks are unchanged.
  - `_bins` returns `"hline"` instead of `"vline"` when `id(rd) in _turned`; its rows are unchanged (S17's measure row kept). The comment above it gains: "A turned histogram's bins run along y; hline fires anywhere within a bin's y-range (WP-30 P1.9b)."
  - `_range` reads data columns, not glyph properties, and is unchanged.
  - No other line of `_dash_build_hover` changes; the comprehensive tool is untouched.
- **TR-55.2 The saved re-finish of a turned bar** (a guard; 55-04). `TestAfterASavedMove::test_turned_bars_keep_their_ends_on_the_axis` is expected to pass at `batch-19-base`, because S49's `TestTheHullSeesTransposedGlyphs::test_the_saved_plan_carries_bar_heights` held S21's plan to HBar heights in batch 17 (S49 Stop rule). If it is red, this section stops and reports the failure text to the orchestrator. It edits none of `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS` or `_dash_refinish_axes`: they are the finisher chain (A153, R11), batch 19 has no finisher editor, and S49 lists `_dash_axis_plan` as not its own to edit for the same reason.
- **TR-55.3 Both modes.** Saved and served share `_dash_build_hover`; the served copy needs no new name (R2 row S55: `_dash_build_hover` in place, 33171). Nested functions travel with it. `_generate_app_source` is not edited.
- **TR-55.4 JS twins: none.** No JavaScript changes. The saved page's after-move path (the derived-copy loop and S21's finisher) is tested under node; the served path through `_served_after_move`.
- **TR-55.5 Registries.** `test/function_test_map.py`, under S55's anchor: `'_dash_build_hover.<locals>._role_prop': 'test/test_horizontal_moves.py::TestTheTooltipFollowsTheTurn::test_a_turned_density_names_its_rows_as_upright'` (the map keys nested functions by qualified name, as `_dash_build_hover.<locals>._cols_of` already is). No program, no Mata function, no copy-list change.
- **TR-55.6 Security (rule 1; G9: "no property name read from JSON").** Threat: page data steering a glyph property (the deleted spacing writer took glyph objects and a width from callback args). Closed by S14's deletion and pinned here: every filter callback's code is one of the module's constant codes (`_FILTER_JS` with S21's finisher appended, and the slider and range variants), and no callback arg, followed through lists, dicts and S21's `models`, is a `Glyph` or a `GlyphRenderer`, so no callback can reach a glyph to write a property. Field names in args are expected (S21's plan holds column names such as `x`, `top` and `left`, and axis letters), so the test does not ban strings. The role map is a Python literal applied at build; a data column named `height`, `width`, `top` or `__proto__` on a turned bar leaves `glyph.height` and `glyph.width` at their build values after saved and served moves. The tooltip fields stay `@{name}` of names `_dash_is_stata_name` admitted (unchanged).
- **TR-55.7 Help: none.** S49 owns the orientation paragraph (Plot types, R3); the one sentence about moves and tooltips is a closeout note for it (Notes). This section edits no help.

## Boundaries

- **Batch partners.** S54: `_dash_name_save`, the SVG constants, `test_toolbar.py`, `test_export_svg.py`, `test_csp_browser.py`, the toolbar help. S56: `_make_figure_body`, `_generate_app_source`, `_dash_added_text`, SchemeParser, the extractor and scheme files, dash.ado, Mata. S55 edits none of them.
- **Earlier sections, read only:** S14's removal (nothing re-added: no glyph property is written by any move), S21's finishers and plan, S49's `_dash_is_horizontal`, helper, map and fixture, S17's tooltip rows, S35's date kinds.
- **Cancelled by IR-13 and S14 D-14b, not done here:** a `_FILTER_JS` height branch, a `_build_filter_widgets` JSON property name, `_dash_copy_redraw_geometry` (deleted).
- **Not this section's:** default axis titles with several mixed layers (S19's rule), cap angles (S14/S49), horizontal's refusals (S49), recast (S45), the served worker (S57).
- **Never:** `_FILTER_JS`, `_build_filter_widgets`, `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes`, `_dash_axis_plan`, `_generate_app_source`, `_make_figure_body`, S49's transposition helper and constants.

## Stata truth

No new fixture: twoway has no filter, and the drawing truth is S49's `test/fixtures/horizontal_truth.json`. One truth block, S01's S55 stub of `test/test_wp30_truth.cscript`, between its start and end lines (helpers directly above its header: Python functions `_hm_*` in one `python:` block, called through one-line `python:` statements and returning through `sfi.Macro.setLocal`; any Stata program there declares `version 19`):

- **HM-01:** `sysuse auto, clear`; `dash histogram mpg, horizontal saving("`w30_work'/hm1.html", replace)`: the page's HoverTool on the Quad renderer has `mode` `hline`; with no `horizontal`, `vline`.
- **HM-02:** `dash kdensity mpg, horizontal saving(…)`: the fallback tooltip's first row's field is the density curve's grid column (the upright first row's), not the density.
- **HM-03 (guard):** `dash bar mpg weight, horizontal filter(foreign) saving(…)`: the glyph is HBar, and no `CustomJS` object's `args` subtree in the page's document JSON references the HBar's id or any `GlyphRenderer` (read with `_br_saved`'s two encodings, test_bug_regressions.cscript:159-180).

## TDD test stubs

### Regression and guard tests, new `test/test_horizontal_moves.py` (55-01)

Module docstring: the entry's text, E1-E5, IR-13. Imports: `dash_render as dr`; from `test_mode_parity`: `_render_pair`, `_spec`, `_served_after_move`, `_tools`, `_axes`, `_annotations`; from `test_saved_filter_layers`: `_render`, `_move`, `_profile_full`, `_saved_of_rows`, `_MOVES`; from `test_server_layer_defects`: `plot_for`; `js_runner.requires_node`. `_H = {"horizontal": "horizontal"}`; `_TURNED = dr._DASH_HORIZONTAL_TYPES` (S49's 24) for the after-move guards; `_FALLBACK_CLASSES = ("VBar", "HBar", "VArea", "HArea", "Quad", "Segment", "Line", "Scatter")`. Every drawing class is parametrized `mode in ("saved", "served")`. "Red" marks a regression expected to fail at the base; the rest are guards and are listed as such in the failure file.

- Test: for every class of `_FALLBACK_CLASSES` (the ones the fallback reads) present in `dr._DASH_TRANSPOSE`, each swapped pair is a pair of the E2 involution, and every turned class it names is a key too — `TestTheRoleMap::test_it_agrees_with_the_transposition` (guard; S49's other pairs, `xs`/`ys`, `x_start`/`y_start`, `dimension`, are not read by the fallback)
- Test (both modes): `kdensity mpg, horizontal`: the fallback tooltip equals the upright one (labels, fields, order); its first field is the grid column — `TestTheTooltipFollowsTheTurn::test_a_turned_density_names_its_rows_as_upright[mode]` (red)
- Test (both modes): `function y=x^2, range(0 2) horizontal` likewise — `::test_a_turned_function_names_its_rows_as_upright[mode]` (red)
- Test (both modes): `area mpg weight, horizontal` alone with `hover()` off: an HArea renderer gets the band tooltip, rows as upright — `::test_a_turned_area_still_has_a_tooltip[mode]` (red: no tooltip)
- Test (both modes): `rcap headroom trunk weight, horizontal` and `pci 1 2 3 4, horizontal`: segment rows in twoway's y1 x1 y2 x2 order with the upright fields — `::test_turned_segments_keep_their_roles[mode]` (red)
- Test (both modes): `histogram mpg, horizontal`: mode `hline`; rows equal the upright tooltip's — `::test_a_turned_histogram_answers_along_its_bins[mode]` (red: `vline`)
- Test: a hand-built figure whose Line binds `x="y", y="x"` (an upright layer drawn from oddly named columns), passed with `layers=None` and again in a layer without `horizontal`, keeps today's rows: the first row reads `glyph.x`'s column; the same for a Quad's `vline` — `TestUprightIsUntouched::test_a_renderer_of_no_turned_layer_reads_its_own_properties` (guard)
- Test: a `horizontal` layer whose renderer's glyph class is not in `_DASH_TRANSPOSE` (a stand-in class S49 leaves upright) keeps its upright rows — `TestUprightIsUntouched::test_an_unmapped_class_stays_upright` (guard)
- Guard (unchanged files, run as they are): `test/test_server_layer_defects.py::TestTheHoverBuilder`, `test/test_function_audit.py` (the tooltip classes `TestARangeReadsAsARange`, `TestABandAloneStillGetsATooltip`, `TestTooltipPrecisionFollowsTheSpread`) and `test/test_mode_parity.py`: every upright tooltip as before.
- Test (node, saved): for each type of `_TURNED` and each `_MOVES` move: the page after the move equals `_saved_of_rows` of the kept rows by `test_saved_filter_layers._profile_full` (glyph class, bindings, widths/heights, annotations) plus each figure's Range1d `start`/`end` and ticker ticks after S21's re-finish; every turned glyph keeps its turned class and bindings — `TestAfterASavedMove::test_a_turned_layer_stays_turned[<type>-<move>]` (guard)
- Test (node, saved): `bar mpg weight, horizontal` with a dropdown: after the move the y range covers every kept bar's `y ± height/2` and equals the served re-finish's — `TestAfterASavedMove::test_turned_bars_keep_their_ends_on_the_axis` (guard or red; TR-55.2)
- Test (served): for each type of `_TURNED`: `_served_after_move` equals a fresh served build on the kept rows (glyphs, bindings, `_axes`, `_annotations`, `_tools`) — `TestAfterAServedMove::test_a_turned_layer_stays_turned[<type>]` (guard)
- Test (both modes): after a move, the tooltips of a turned histogram, kdensity and area equal their pre-move tooltips — `TestAfterAServedMove::test_the_tooltip_survives_a_move[<type>-saved|served]` (red: the base tooltip is the wrong one)
- Test (both modes): `bar mpg weight, horizontal by(foreign)`: after a move every panel keeps its HBar, the shared y range covers the half-heights and the x range the kept values; saved equals served — `TestByAndSecondAxis::test_by_panels_after_a_move[mode]` (guard)
- Test (both modes): `(scatter mpg weight) (bar mpg weight, horizontal yaxis(2))` after a move: the right axis's range covers the kept rows' weights and keeps its title; the left axis's the kept mpg — `TestByAndSecondAxis::test_yaxis2_after_a_move[mode]` (guard)
- Test (both modes): a %td `d` with `(scatter y d) (bar y d, horizontal)` and the reverse order (critic 8): after a move the date axis is the one S49's fixture names, before and after — `TestByAndSecondAxis::test_mixed_orientation_on_a_date_after_a_move[order-mode]` (guard)
- Test (both modes): a turned bar whose source holds columns named `width`, `height`, `top` and `__proto__`: after a saved (node) and a served move, `glyph.height` and `glyph.width` keep their build values and the page is the kept rows' — `TestNoPropertyNameFromPageData::test_a_column_named_like_a_property_changes_nothing[mode]` (guard)
- Test: every filter callback in the saved page of `bar …, horizontal filter(foreign)` (dropdown, slider and range) has code equal to one of the module's constant codes, and no arg, followed through lists, dicts and S21's `models`, is a `bokeh.models.glyph.Glyph` or a `GlyphRenderer` — `TestNoPropertyNameFromPageData::test_no_callback_can_reach_a_glyph` (guard)
- Test (cscript): HM-01..HM-03 in `test/test_wp30_truth.cscript`.

### Shared harness and corpora (appended; 55-02)

- `test/test_mode_parity.py` CORPUS: `_case("Turned layers (WP-30 P1.9b)", [plot_for("histogram", _H), plot_for("kdensity", _H)])`, `_case("Turned ranges and areas (WP-30 P1.9b)", [plot_for("rcap", _H), plot_for("area", _H)])`, `_case("Turned bar on axis 2 (WP-30 P1.9b)", [_sc(), plot_for("bar", {**_H, "yaxis": "2"})])`; `ALLOWED` and `_MUST_WARN` untouched.
- `test/test_saved_filter_layers.py` `_CORPUS`: `_case("a turned bar, dropdown", _MOVES[0], [plot_for("bar", _H)])`, `_case("a turned histogram, range slider", _MOVES[1], [plot_for("histogram", _H)])`.

### Pinned tests to flip

None known (E6). Any assertion found by 55-01's grep that a turned layer's tooltip is `vline` or carries upright-property roles is flipped in 55-03 with `Flipped: <node> -- <old> was wrong because a turned layer's tooltip names its variables in the upright roles and a turned histogram answers along y`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Role map | pytest `TestTheRoleMap` | S49's map | n/a |
| Tooltips | pytest `TestTheTooltipFollowsTheTurn`, `TestUprightIsUntouched`; cscript HM-01, HM-02 | auto | yes |
| Saved moves | pytest `TestAfterASavedMove` (node); `test_saved_filter_layers.py` corpus | `_DF`, auto | saved |
| Served moves | pytest `TestAfterAServedMove` | `_DF`, auto | served |
| by(), yaxis(2), dates | pytest `TestByAndSecondAxis` | auto, a %td frame | yes |
| Security | pytest `TestNoPropertyNameFromPageData`; cscript HM-03 | hostile column names | yes |
| Parity | `test_mode_parity.py` with three cases | CORPUS | yes |
| Registries, tracking | `test_function_test_map.py`, `test_tracking_documents.py`, `test_cscript_hygiene.py` | — | n/a |

**Acceptance criteria.**
- **AC-55.1** (BR-55.1) `TestAfterASavedMove` and `TestAfterAServedMove::test_a_turned_layer_stays_turned` pass for all 24 types, node tests not skipped.
- **AC-55.2** (BR-55.2) `TestTheTooltipFollowsTheTurn` and `test_the_tooltip_survives_a_move` pass in both modes; HM-01 and HM-02 PASS.
- **AC-55.3** (BR-55.3) `TestByAndSecondAxis` passes in both modes.
- **AC-55.4** (BR-55.4) `TestUprightIsUntouched` passes; `test_mode_parity.py` passes with the new cases and untouched `ALLOWED`/`_MUST_WARN`.
- **AC-55.5** (BR-55.5) `TestNoPropertyNameFromPageData` and HM-03 pass.
- **AC-55.6** The full suite through the queue reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 55-01 to 55-07 form the one commit, made by 55-07 on `wp30-s55` with the subject `Keep turned layers' tooltips and geometry through filter moves in both modes (WP-30 P1.9b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s55`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; a cscript runs through the driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "test_wp30_truth.cscript" > "$S/run_test_wp30_truth.do"`, then `WP30_ONLY=S55 "$SLOT" "$S" "$S/run_test_wp30_truth.do"`). Each task appends the files it changed to `$S/55-files.txt`.

<task type="auto" id="55-01">
  <name>Write the move and tooltip tests</name>
  <files>test/test_horizontal_moves.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-19-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s55`; stop otherwise. Check S49's names exist on this tree (`grep -nE "^def _dash_is_horizontal|^_DASH_TRANSPOSE|^_DASH_HORIZONTAL_TYPES|^def _dash_transpose_layer" "$WT/dash_render.py"` prints 4 lines, and `grep -n '"_dash_is_horizontal"' "$WT/dash_render.py"` finds the copy-list entry); stop and report if not. Create `test/test_horizontal_moves.py` with every stub of "Regression and guard tests". Run `python3 -m pytest test/test_horizontal_moves.py -q -n 6 -p no:cacheprovider -rf > "$S/55-new.log" 2>&1`. Also run `grep -rn "vline" "$WT"/test/*.py` and S49's `test/test_horizontal.py` for E6's pins and write what is found to `$S/55-pins.txt`. Write `$S/55-P1.9b-failure.txt`: the base sha, one line per failing node with its first error line (the measured base tooltips of the red cases), then "Guards (pass at the base)" with every guard node. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/55-new.log"` is at least 16 (the red cases in both modes); `grep -c "SKIPPED" "$S/55-new.log"` prints 0; `grep -c "Guards (pass at the base)" "$S/55-P1.9b-failure.txt"` prints 1; `git -C "$WT" diff --name-only -- dash_render.py` prints nothing.]]></verify>
  <done>Every tooltip regression was shown failing and every after-move guard shown passing on the unmodified tree, with the text saved.</done>
</task>

<task type="auto" id="55-02">
  <name>Add parity cases and truth cases</name>
  <files>test/test_mode_parity.py, test/test_saved_filter_layers.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append the three `CORPUS` cases of "Shared harness and corpora" to `test/test_mode_parity.py` before `CORPUS`'s closing bracket, after any earlier section's cases, and the two `_CORPUS` cases to `test/test_saved_filter_layers.py` after its last case (R8). Put HM-01..HM-03 between S01's `S55 start` and `S55 end` lines of `test/test_wp30_truth.cscript`, printing `HM-nn PASS: …` through `_w30_expect`/`_w30_done`, files only under the work directory and erased before the end line, the `_hm_*` helper block directly above the S55 header (form of "Stata truth"). Run `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "P1.9b"`, `test/test_saved_filter_layers.py -k turned`, and the block through the driver. Append the failing parity nodes and `HM-nn FAIL` lines to `$S/55-P1.9b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "HM-0[12] FAIL" "$S/run_test_wp30_truth.log"` prints 2; `grep -c "HM-03 PASS" "$S/run_test_wp30_truth.log"` prints 1; the log has no `SKIP`; `python3 -m pytest "$WT/test/test_saved_filter_layers.py" -q -n 6 -p no:cacheprovider -k turned` reports 0 failed (guards).]]></verify>
  <done>The parity cases and the Stata-route cases were in place, the tooltip ones shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="55-03">
  <name>Read turned glyphs in upright roles</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_build_hover` is copied into the served app and decides every tooltip. Apply TR-55.1 exactly: the `_turned` set and the nested `_role_prop` before `_drawn_field`, the role reads in `_point_or_line`, `_segment` and `_band`, and `"hline"` in `_bins` for a marked renderer, with the comment. Edit no other line of the function. Add TR-55.5's `FUNCTIONS` entry under S55's anchor. Flip each pin listed in `$S/55-pins.txt` in place with its `Flipped:` line written to `$S/55-flips.txt`; delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "$WT/test/test_horizontal_moves.py" -q -n 6 -p no:cacheprovider -k "Tooltip or Upright or RoleMap"` reports 0 failed; `python3 -m pytest "$WT/test/test_server_layer_defects.py" "$WT/test/test_function_audit.py" "$WT/test/test_function_test_map.py" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Turned layers' tooltips named their variables in the upright roles and a turned histogram answered along y, in both modes, with upright tooltips unchanged.</done>
</task>

<task type="auto" id="55-04">
  <name>Confirm the saved bar plan guard</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest "$WT/test/test_horizontal_moves.py::TestAfterASavedMove::test_turned_bars_keep_their_ends_on_the_axis" -q -n0 -p no:cacheprovider` and write its last line to `$S/55-plan.txt`. If it fails, stop and report the failure text to the orchestrator (TR-55.2): the fix belongs to a finisher editor (A153, R11), not to this section. Edit nothing.
  ]]></action>
  <verify><![CDATA[`cat "$S/55-plan.txt"` reports 1 passed; `python3 -m pytest "$WT/test/test_natscale_js.py" "$WT/test/test_saved_filter_layers.py" -q -n 6 -p no:cacheprovider` reports 0 failed; `git -C "$WT" diff --name-only -- dash_render.py` shows only the file 55-03 edited.]]></verify>
  <done>A turned bar's end halves stayed on the axis after a saved move through S21's plan as S49 left it, with nothing edited.</done>
</task>

<task type="auto" id="55-05">
  <name>Run every move and parity test</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_horizontal_moves.py`, `test_horizontal.py` (S49's), `test_mode_parity.py`, `test_saved_filter_layers.py`, `test_served_filter_move.py`, `test_saved_stale_cue.py`, `test_by_scales_chrome.py`, `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_cscript_hygiene.py` with `-n 6` (Chrome and node files as their modules require), and the S55 block through the driver. Record each command's last line in `$S/55-local.txt`. A failure is fixed in the task that owns its file before going on.
  ]]></action>
  <verify><![CDATA[Every line of `$S/55-local.txt` reports 0 failed and no skip; `grep -cE "HM-0[1-3] PASS" "$S/run_test_wp30_truth.log"` prints 3; `grep -c "ALL CHECKS PASSED" "$S/run_test_wp30_truth.log"` prints 1; the log has no `SKIP`.]]></verify>
  <done>Every test of the section and of the move paths it relies on passed on the worktree.</done>
</task>

<task type="auto" id="55-06">
  <name>Check scope against the manifest</name>
  <files>none</files>
  <action><![CDATA[
    Confirm the cancelled work stayed cancelled: `git -C "$WT" diff "$(cat "$S/batch-19-base.txt")" -- dash_render.py` touches only `_dash_build_hover`; `grep -c "dash_spacing\|derived_spacing" "$WT/dash_render.py"` prints 0, and `grep -c "_dash_copy_redraw_geometry" "$WT/dash_render.py"` prints 0 (or, only if the maintainer took S14's D-14b fallback at 5.0, the function is the documented no-op `return None`). Write the result, with the IR-13 and S14 D-14b citations, to `$S/55-scope.txt` for the commit body and the merger's 19.0 record (`_build_filter_widgets` was not edited).
  ]]></action>
  <verify><![CDATA[`cat "$S/55-scope.txt"` lists one edited symbol and the 0 count.]]></verify>
  <done>The edit was confined to the tooltip builder, with the cancelled redraw work recorded as cancelled.</done>
</task>

<task type="auto" id="55-07">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.9b"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.9b"` key line of `WP30_OPEN`. Replace the `<!-- WP-30 P1.9b -->` marker under `### Fixed in WP-30` in place with "Notes: CHANGELOG line", quoting the base tooltips from `$S/55-P1.9b-failure.txt`. Run `test_tracking_documents.py` with `-n0`. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/55-full.log"` in the background, read when `exit=` appears, never relaunched (E6). Stage exactly the files in `$S/55-files.txt` plus these three; check `git -C "$WT" diff --cached --name-only` equals that list (G6). Write `$S/55-message.txt` per "Notes: commit message", check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/55-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.9b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.9b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.9b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.9b was closed naming existing tests, its marker carried the measured change, and one green commit on wp30-s55 was ready for the merger.</done>
</task>

## Section completion criteria

- In both modes, before and after saved and served filter moves, the 24 turned types stay turned and equal the page built from the kept rows, including by() panels, `yaxis(2)` and a mixed-orientation date graph.
- A turned layer's tooltip has the upright layer's rows and order; a turned histogram's tooltip is `hline`; upright tooltips are unchanged.
- No page script takes a glyph property name from page data, and a column named like a property changes nothing.
- `_dash_build_hover.<locals>._role_prop` is mapped; the edit is confined to `_dash_build_hover`.
- One green commit `(WP-30 P1.9b)` exists on `wp30-s55`; it closes the entry, deletes its key and replaces its marker.

## Notes

- **The manifest's redraw work is cancelled, not forgotten.** The manifest scope ("the `_FILTER_JS` redraw writes height … through a fixed branch; the served `_dash_copy_redraw_geometry` uses height") and the notes ("Edits `_dash_copy_redraw_geometry`, … the `_FILTER_JS` branch and `_build_filter_widgets`") predate S14's D-14b. IR-13 ("P1.17.3's cancellation of P1.9's step 5 stands") binds. The security intent (critic 7: "the property name is asserted in Python and branched in JS") is met more strongly: no property is written by any move, and `TestNoPropertyNameFromPageData` pins it. For the orchestrator at 19.0: `_build_filter_widgets` (listed as S55's expected CRITICAL) is not edited by this section, nor is `_dash_axis_plan`; S55's one edited symbol is `_dash_build_hover` (LOW in the index; copied into the served app, treated as MEDIUM).
- **S49's names.** `_dash_is_horizontal`, `_DASH_TRANSPOSE` and `_DASH_HORIZONTAL_TYPES` are S49's (TR-49.1, TR-49.2), checked by 55-01. No mark is needed: both call sites already pass `layers`, and S49 rebuilds glyphs on the same renderer objects, so the renderer ids in `layers` are the turned renderers.
- **Hover after a move.** Hover tools are built once per document in both modes and never rebuilt by a move; a served move replaces data wholesale, so the fields keep resolving. The tests still check after a move, since S21's re-finish and S57's worker touch the same documents.
- **Merge rules for the shared files.**
  - R1: S55's own truth block only.
  - R2: no copy-list change (`_dash_build_hover` in place, 33171); one map key under S55's anchor.
  - R4/R5: the one `P1.9b` marker under `### Fixed in WP-30`, the entry and its key.
  - R8: three CORPUS cases and two saved-move cases appended; S54's harness change and S56's cases sit beside them, all kept by the merger.
  - R9: only the pins 55-01 finds. R10: no count pin moves. R11/R12: no finisher and no one-editor symbol is edited.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_dash_build_hover` only, plus test symbols of the staged files.
- **Commit message.** Subject as in "Commit boundary". Body, in order: `$S/55-P1.9b-failure.txt`; the measured defect (the base tooltips of a turned kdensity, area, rcap and histogram, both modes); what changed (TR-55.1) and what did not (the contents of `$S/55-scope.txt`, citing IR-13 and S14 D-14b); the threat closed (G9): "no filter callback can reach a glyph, so no page data can steer a glyph property; pinned with hostile column names"; one `Regression: test/test_horizontal_moves.py::<Class>::<test> -- failed at <base sha> with <text>` per red node and `Regression: test/test_wp30_truth.cscript HM-01 -- failed at <base sha> with <text>`; the `Flipped:` lines of `$S/55-flips.txt`, if any; `BUGS.md: "<WP30_OPEN["P1.9b"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.9b). A turned layer keeps its orientation after saved and served filter moves: the width-writing redraw paths this entry names were removed by WP-30 P1.17a, so bar widths and heights are build-time constants in both modes, and the after-move pages of the 24 types drawn with horizontal equal the pages built from the kept rows, by() panels, yaxis(2) and a mixed-orientation date axis included; the shared tooltip builder (dash_render.py _dash_build_hover, copied into the served app) now reads a glyph that WP-30 P1.9a turned (a horizontal layer's mapped class) through the mirror of each upright role, so turned densities, functions, areas and segments name their rows as upright, and a turned histogram's tooltip answers along y (hline). No filter callback can reach a glyph or renderer, so no page script writes a glyph property after a move. Pinned by test/test_horizontal_moves.py::TestTheTooltipFollowsTheTurn::test_a_turned_histogram_answers_along_its_bins, test/test_horizontal_moves.py::TestAfterASavedMove::test_a_turned_layer_stays_turned, test/test_horizontal_moves.py::TestAfterAServedMove::test_a_turned_layer_stays_turned, test/test_horizontal_moves.py::TestByAndSecondAxis::test_yaxis2_after_a_move, test/test_horizontal_moves.py::TestNoPropertyNameFromPageData::test_no_callback_can_reach_a_glyph, test/test_wp30_truth.cscript HM-01.
  ```
- **CHANGELOG line** (replaces the marker in place, under `### Fixed in WP-30`):

  ```
  - A layer drawn with `horizontal` keeps its tooltips right in both modes, before and after filter moves: `dash histogram mpg, horizontal` answered along x (`vline`) across bins stacked along y, and now answers along y (`hline`); a turned kdensity, function, area or rcap named its tooltip rows in the other axis's roles (a turned area had none), and now names them as the upright layer does. Turned layers, by() panels, `yaxis(2)` and a mixed-orientation date axis stay as drawn after any move. (WP-30, P1.9b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md A7** (:100, :230) and **B12** (:476-486): `- **Tracked:** Closed in WP-30, BUGS.md "<P1.9a title>", "<P1.9b title>", commits <S49 sha>, <sha>` once both entries are closed; B12-b stays with P1.8b's (S45) line.
  - **REMAINING.md** :124-126, :305 (REM-§2-S06-horizontal, REM-S06-a) and **TWOWAY_COVERAGE_AUDIT.md** :24, :63, :97, :115, :169 (AUDIT-15): horizontal drawn and kept through moves (S49, S55).
  - **DROPIN-REMAINING.md:99** (P1.9): "Closed by <S49 sha>, <sha> (WP-30 S49, S55)."
  - **test/fixtures/rejected_options.json:1130-1200**: `horizontal`'s disposition "implement-S06" and stale `dash_rc` 198 (critic 10).
  - **Help sentence for S49's paragraph** (S49 owns it; not edited here): "A turned layer keeps its orientation, axes and tooltips after filter moves, in both modes." If S49's paragraph already says so, nothing is needed.
  - **AGENTS.md invariant:** "no filter move writes a glyph property in either mode and no filter callback holds a glyph; a turned layer differs from the upright one only in its glyph bindings, and the tooltip builder reads them through `_role_prop`, deciding turned-ness from `layers` and `_dash_is_horizontal`."
