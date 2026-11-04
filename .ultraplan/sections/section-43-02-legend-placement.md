# Section 43-02: Legend ring(0) bplacement, holes, all/draw/nodraw

> Part of: WP-43 (Legend, titles and added text) · Items: LT-4, LT-17, LT-5 · Risk: red · Batch: 43.2 · Depends on: 43-01 · Blocks: 43-05 · Tasks: 7, 3 commits · Case-id prefix: Q4302

> **D69 (04nov2026) supersedes this section's use of the overlay dispatcher.** D-43-01.c / R4-7 are withdrawn: there is no `_DASH_OVERLAY_JS`, `_dash_overlay_item`, `_dash_overlay` or `_dash_overlay_move`, because Bokeh clips a `fig.center` annotation to the plot frame. Every task below that registers a dispatcher kind or overlay is re-planned at its start: measure, then draw by native model properties, CSS on the model, an annotation only where its target lies inside the plot frame, or bring a documented difference for a ruling. Add no shared layout callback. See .ultraplan/review/DECISIONS.md D69.

## Overview

**What is wrong today.** LT-4 with the bplacement part of ST-1 (audit :361-363; appendix LT-4, ST-1): "legend(ring(0) bplacement()) ignores bplacement; bplacement abbreviations (nor, nea, t, top) are not read". twoway puts `legend(ring(0) bplacement(nw))` at the plot region's top-left and `legend(ring(0) pos(1) bplacement(sw))` at its bottom-left, and `ring(0) bplacement(ne)` equals `ring(0) position(1)`; dash's ring-0 branch (dash_render.py:39628-39630) passes only `_DASH_CLOCK_INSIDE[clock]` and the lookup (:39612) is `_DASH_BPLACEMENT_LOCATION.get(_bp.strip().lower())`, exact keys only, so `nor`, `nea`, `t` and `top` (which twoway draws as `n`, `ne`, `n`, `n`) are noted and dropped. LT-17 (audit :400-402): "legend(holes()) with cols(1) inserts a full blank row": twoway's `legend_g.class` PlaceKeyTextAdjRow (:312-357) advances the column index for a hole, so `holes(1) cols(1)` makes the box 45 units taller (367.20 -> 412.26) and moves the keys 22.45 units -- one row gap, not a 157-unit key row; dash inserts a full empty `LegendItem` (:39497-39512). LT-5 (audit :370-372): "legend(all), draw and nodraw are named": twoway's `all` keys every view (no merge: two `pstyle(p1)` scatters get two keys and a legend), `draw` is `on` and `nodraw` is `off` (`_fr_legend_parse_and_log.ado:328-334`); dash merges, hides on `draw` and draws on `nodraw`, each named.

**After this section** a ring(0)/position(0) legend is placed at the plot region's compass point that `bplacement()` names; every legend `bplacement()` is read through one port of twoway's compass reader (`compass2dir.class` `_unabbrev`); a hole in a one-column or one-row legend adds one row gap where twoway adds it -- after a filter move with its stale suffix on the drawn text (R4-9), under `scale()` (R4-4) and in by()'s legend with click-to-hide (R4-8); `legend(all)` keys every plot with no merge, `draw` is `on` and `nodraw` is `off`; nothing is printed for them.

**Why together.** All three are `_dash_apply_legend`'s placement, merge loop and holes, which this section owns in batch 43.2.

**Test order and commit rule (BRIEF).** LT-4 (43-02-01 red; 43-02-02 fix and commit `(WP-43 LT-4)`), LT-17 (43-02-03 red and spike; 43-02-04 checkpoint only if the spike fails; 43-02-05 fix and commit `(WP-43 LT-17)`), LT-5 (43-02-06 red; 43-02-07 fix and commit `(WP-43 LT-5)`).

### Section decisions (binding on the executor)

- **D-43-02.a The compass reader.** New `_dash_compass_dir(text) -> str | None`, a port of `compass2dir.class` `_unabbrev` (base/c/compass2dir.class:95-175): with `t = str(text).strip()`, (1) option-abbreviation matching, lower case only, of `north` (min `n`), `south` (`s`), `east` (`e`), `west` (`w`), `nwest` (`nw`), `neast` (`ne`), `swest` (`sw`), `seast` (`se`), `center` (`c`), `top` (`t`), `bottom` (`b`), `left` (`l`), `right` (`r`) -- `t` matches a name when `len(t) >= len(min)` and `name.startswith(t)`; top/bottom/left/right map to north/south/west/east; (2) only when no name matched and `len(t) <= 2`: the capitals `N S E W NE NW SE SW` to their names and `T B R L` to north/south/east/west; (3) only when no name matched and `len(t) <= 2` and `t` is a number 0-12: `center neast neast east seast seast south swest swest west nwest nwest north`[int(t)]; else None. `_DASH_BPLACEMENT_LOCATION` already maps every full name; each `_DASH_BPLACEMENT_LOCATION.get(` site (grep; :39612 and any by() legend site) reads `_DASH_BPLACEMENT_LOCATION.get(_dash_compass_dir(x) or "")`. An unknown value keeps today's note (its wording is 49-02's, LT-25). (45-02 later routes this function through its style-word table, R4-2; it keeps this signature and these full names.)
- **D-43-02.b ring(0) with bplacement.** In step 4 of `_dash_apply_legend`: when the legend is inside (`ring == 0`, or `position(0)`) and `_bploc` is not None, `_dash_move_legend(fig, legend, "center", _bploc)`; without `bplacement()` the clock's inside location as today. Measured truth (`legend_place_truth.json` `r0_bp_<x>`) decides `position(0) bplacement()` (expected: bplacement wins).
- **D-43-02.c Holes in a one-column or one-row grid.** A hole in a grid of more than one column and more than one row stays an empty `LegendItem` (twoway's cell is a full cell; fixture `holes_2col` confirms). In a grid of one column (or one row, measured `holes_1row`) the hole is a gap of one `legend_row_gap` (one `legend_col_gap` for a row), drawn as a composite by `_dash_legend_hole_runs(fig, legend, hole_at, chrome)`:
  - *the spacer*: the Legend itself keeps its box, place, ring, span, title and padding; its `items` become renderer-less stand-ins `LegendItem(label=<the original's label>, renderers=[])`, one per key and none for a hole, drawn with `label_text_alpha = 0`; its `spacing` becomes `rowgap + (round(h * rowgap / (n - 1)) if n > 1 else 0)` (n keys, h holes inside the list; with one key there is no inside place, so no division; a hole before the first key adds `rowgap` to `title_standoff`, one after the last adds `rowgap` to the padding's bottom side -- `legend(on holes(1) cols(1))` on a one-key legend therefore adds `rowgap` to `title_standoff` only), so it reserves twoway's size; the Python attributes `legend._dash_hole_at = hole_at` and `legend._dash_real_items = <the original items>` record the composite for by();
  - *the runs*: `k + 1` borderless, transparent Legends, one per run of keys between holes (`border_line_color=None`, `background_fill_color=None`, the spacer's label and glyph props copied through the `_dash_by_legend_cell` prop list, `click_policy` the spacer's), in `fig.center`, tagged `["dash_legend_run", "<i>"]`, `visible=False` until placed. Each run holds the ORIGINAL `LegendItem` instances of its keys -- a slice of the original list, never copies -- so the stale cue, which finds legend items by their renderers (`_stale_cue_args`, dash_render.py:65964-66045) and writes their labels, puts its suffix on the drawn text with no JS edit in either mode (R4-9);
  - *the placement*: one dispatcher item (43-01, D-43-01.c) `_dash_overlay_item(fig, "legend_runs", runs, legend, {"holes": hole_at, "axis": "col" or "row"}, px={"gap": rowgap, "pad": [l, r, t, b]}, watch=[[it, "label"] for it in originals])`, whose handler this section adds to `_DASH_OVERLAY_JS`: it reads the spacer's laid-out box and each stand-in's DOM row (its height), sets each run's numeric `location` (run top = spacer top + pad top + rows before x (row height + gap) + holes before x gap; run left = spacer left + pad left; mirrored for a row), copies each original item's current label into its stand-in (a stale suffix then widens the spacer too), and sets the runs `visible = true`, writing only what differs. No separate layout CustomJS is added (R4-7). The `px` numbers scale with `scale()` through 43-01's post-pass (R4-4).
  This holds only if 43-02-03's spike shows that a `fig.center` Legend at a numeric location outside the frame is drawn in both Bokeh versions, in Chrome and in the SVG export, and that a renderer-less stand-in reserves its row; otherwise checkpoint 43-02-04.
- **D-43-02.d all/draw/nodraw.** `all` in `_words`: the C13 merge (`_kept`/`_folded` loop, :39385-39431) is skipped. `draw` is read as `on` and `nodraw` as `off` everywhere `_words` is read (step 8, :39770-39777: `forced_on = bool({"on", "draw"} & _words)`, `turned_off = bool({"off", "nodraw"} & _words) and not forced_on`), so on/draw win over off/nodraw in either order, as the parse file's order makes them. `_DASH_LEGEND_SUBOPTS` (:53797) gains `"all", "draw", "nodraw"`; `styleonly` stays out (49-02, LT-26).
- **D-43-02.e by()'s legend (R4-8).** by() builds its overall legend in a cell from panel 1's legend items (`_dash_by_keys`, :55691-; `_dash_by_legend_cell`, :55644-55690), after every panel's `_dash_apply_legend`. In `_dash_by_keys`: `series_legends(fig)` also skips Legends tagged `dash_legend_run`; `items = list(getattr(first[0], "_dash_real_items", None) or first[0].items)`, so the cell is built from the real keys (clones plus panel matches, `click_policy="hide"`). In `_dash_by_legend_cell`, after 43-01's `_dash_overlay_move` call: when `getattr(legend, "_dash_hole_at", None)` is set, `_dash_legend_hole_runs(cell, leg, legend._dash_hole_at, None)` rebuilds the composite on the cell's legend, its runs holding the cell's items and its `px` copied from panel 1's `legend_runs` item (already scaled by panel 1's post-pass; the cell has none), so a click on a key in a run hides that series in every panel. Panel 1's own runs stay on panel 1 and stay hidden with their hidden spacer (D-43-01.c step 3); 43-01 moves only kind `overlay`, so they are not moved.

## Risk: [red] -- inside legends move, merged keys split under all, a hole composite in both modes and in by()

**Why.** Placement and the merge loop run for every legend in both modes; the hole composite is new, reaches the stale cue and by()'s click-to-hide.

**Risk factors.** 1. Pins on `bplacement` outside the plot (test_legend_geometry.py::TestClockTable::test_bplacement, guard). 2. `_dash_legend_keys`/merge pins (test_legend_histogram_only.py:110-179). 3. by() legends read `bplacement` and holes too. 4. The run Legends must not be double-counted by later passes (`fig.legend` lists every Legend: the colour-key skip, `_dash_finish_graph_text` and step 8's `plot_legends` must treat the spacer as the one plot legend and the runs as its drawing). 5. The stale cue must reach the drawn text.

**Mitigation.** 1. The guard stays green. 2. `all` only skips the merge when given; test_legend_histogram_only.py runs in each commit task. 3. A by() Chrome case with click-to-hide. 4. Each run Legend is tagged `["dash_legend_run", "<n>"]`; tests count them and assert the runs hold the original items. 5. A MOVE_CORPUS case and a Chrome stale-suffix test, both modes.

## Dependencies

- **Depends on: 43-01** (the dispatcher `_DASH_OVERLAY_JS`, `_dash_overlay_item`, `_dash_overlay_move`, the scale post-pass and the chrome dict keys it added; the title block must be in place before the spacer reads the box).
- **Blocks: 43-05** (it reuses `_dash_compass_dir` for title `placement()`).
- **Parallel batch: 43.2**, alone.

## Evidence

### Placement today (dash_render.py `_dash_apply_legend`, re-read: step 4 starts :39590)

```python
39609    _bp = _dash_legend_arg(_calls, ("bplacement",))
39612        _bploc = _DASH_BPLACEMENT_LOCATION.get(_bp.strip().lower())
39624    if legend is not None and (m_pos or m_ring or _sclock is not None):
39625        if m_pos and clock == 0:
39626            _dash_move_legend(fig, legend, "center", "center")
39627        elif ring == 0:
39628            _dash_move_legend(fig, legend, "center",
39629                              _DASH_CLOCK_INSIDE.get(clock, "bottom_center"))
```
Holes (:39495-39512) insert `LegendItem(label={"value": ""}, renderers=[])` at each position. The merge loop (:39385-39431) folds keys by `_dash_key_signature` unless a style option is given. Step 8 (:39770-39777) reads `on`/`off` only. `_DASH_LEGEND_SUBOPTS` (:53797-53803) has no `all`, `draw`, `nodraw`. The stale cue collects every Legend of a figure's center and sides and the items whose renderers include a frozen layer's (`_stale_cue_args`, :65977-66010). `_dash_by_keys` takes `first[0].items` from `series_legends(figs[0])` (:55740-55744, :55757-55758) and hands them to `_dash_by_legend_cell` (:55821-55823).

### twoway

`legend_options.sthlp:723-724` ("When ring(0) is specified, bplacement() further specifies where in the plot region the legend is placed"); `_fr_legend_parse_and_log.ado:226-234` (`all` sets `.legend._all`), `:328-334` (`nodraw`/`off` -> force_nodraw; `draw`/`on` -> force_draw, applied after); `legend_g.class` `rebuild` (:161-240: `all` adds every view's key; draw_view = `(ct > 1 & !force_nodraw) | force_draw`), PlaceKeyTextAdjRow (:312-357); compass2dir.class `_unabbrev` (:95-175).

### Fixtures on disk

`legend_geometry_truth.json` (`bplacement`: pos(6) bplacement(w) outside only; `holes`, `holes_big`: cols(2)/default), `added_text_truth.json` `_meta.compass` (text() spellings). This section adds `legend_place_truth.json`.

### Tests that pin today's behaviour (flip, never delete)

- test/test_legend_geometry.py::TestClockTable::test_bplacement (:302-306): stays (outside).
- test/test_legend_geometry.py::TestHolesAndGrid::test_holes (:330-338): two columns -- stays; a one-column node is new.
- test/test_legend_histogram_only.py merge guards (:110-179): stay; `all` cases are new.
- Any test asserting `legend(draw)` hides or `nodraw` shows a legend, or that `all`/`draw`/`nodraw` are named (grep `"nodraw"\|"draw"\|all)` in test/test_legend*.py and test/test_subopt_abbrev.py) flips.

## User stories

- US-43-02.1 As the Stata user with an existing twoway command, I want `legend(ring(0) bplacement(nw))` in the plot region's top-left, and `bplacement(nor)` read as `n`, as twoway does.
- US-43-02.2 As the same user, I want `legend(holes(1) cols(1))` to leave twoway's small gap, not a blank row, and its keys to show the stale mark after I move a filter and to hide their plots when I click them in a by() graph.
- US-43-02.3 As the same user, I want `legend(all)`, `legend(draw)` and `legend(nodraw)` to decide the keys and whether a legend shows exactly as twoway does.

## Business requirements

- BR-43-02.1 An inside legend with `bplacement()` sits at that compass point of the plot region; every spelling twoway reads for a compass direction is read.
- BR-43-02.2 A hole in a one-column or one-row legend is one row (column) gap; in a larger grid a full cell; the gap scales with `scale()`, a stale suffix shows on the drawn key text, and by()'s legend still hides a series on a click.
- BR-43-02.3 `all` keys every plot, `draw` forces a legend, `nodraw` removes it, and nothing is printed for them.

## Technical requirements

- TR-43-02.1 `_dash_compass_dir` (D-43-02.a) after `_DASH_BPLACEMENT_LOCATION` (:38491-38501); copy list (R2): `"_dash_compass_dir",` after `"_dash_legend_arg",` in the functions tuple (:67496); function_test_map.py `"_dash_compass_dir": "test/test_legend_place.py::TestCompassReader::test_each_spelling"`.
- TR-43-02.2 Step 4 per D-43-02.b; the bplacement note path unchanged.
- TR-43-02.3 Holes per D-43-02.c: `_dash_legend_hole_runs(fig, legend, hole_at, chrome)` after `_dash_legend_title_block` (43-01); the `legend_runs` handler added to `_DASH_OVERLAY_JS`'s kind table (no new constant, no new CustomJS); copy list `"_dash_legend_hole_runs",` after 43-01's `"_dash_overlay_move",`; function_test_map `"_dash_legend_hole_runs": "test/test_legend_place.py::TestHolesOneColumn::test_runs"`.
- TR-43-02.4 all/draw/nodraw per D-43-02.d.
- TR-43-02.5 by() per D-43-02.e: `_dash_by_keys`' `series_legends` filter and `items` line, and the `_dash_legend_hole_runs` call in `_dash_by_legend_cell` after 43-01's `_dash_overlay_move` call.
- TR-43-02.6 Served: shared code; no template edit (the served app runs `_dash_apply_legend` and `_dash_by_keys` by name).
- TR-43-02.7 test/test_overlay_budget.py `_PAGE_ROWS` gains a `legend(holes(1) cols(1))` three-key row.

## Boundaries

- Not touched: `_dash_legend_box` (43-01, 43-03), `_dash_legend_keys`/`_dash_key_signature`'s rule (43-04 owns MS-10's merge key; this section only skips the merge under `all`), the textbox placement (43-05), `_dash_at_place` in Mata (45-02, ST-1's text() part), `styleonly`/`nodrawview` (49-02), `_FILTER_JS` (the runs hold the original items, so the stale cue needs no edit), the dispatcher's own code beyond the `legend_runs` handler.
- Owns in 43.2 (for the manifest): `_dash_apply_legend` (step 4, merge, holes, step 8; R12), `_dash_compass_dir`*, `_dash_legend_hole_runs`*, the `legend_runs` handler of `_DASH_OVERLAY_JS`, `_DASH_LEGEND_SUBOPTS`, `_dash_by_keys` (`series_legends`, `items`), `_dash_by_legend_cell` (the runs call).

## Stata truth

Script `scripts/extract_legend_place_truth.do` (new) -> `test/fixtures/legend_place_truth.json`. Base `twoway (scatter mpg weight) (scatter price weight) (scatter turn weight)`; SVG read with `scripts/svg_chrome.py` (legend box rect) and `scripts/svg_text_runs.py` (key texts):

| key | legend() | recorded |
|---|---|---|
| r0_bp_<x> for nw sw ne c | `ring(0) bplacement(<x>)` | box rect relative to the plot region |
| r0_pos1_bp_sw, pos0_bp_nw | `ring(0) pos(1) bplacement(sw)`, `pos(0) bplacement(nw)` | box rect |
| bp_<s> for nor nea t top N NE R 3 12 rig bot | `pos(6) bplacement(<s>)` and `ring(0) bplacement(<s>)` | rect; equal-to-canonical flag; note text |
| holes_1col_<k> for k 1 2 4 | `holes(<k>) cols(1)` | box height, every key text y |
| holes_1col_1key | `twoway (scatter mpg weight), legend(on holes(1) cols(1))` (one key) | box height, key text y |
| holes_1col_scale | `holes(1) cols(1)` with `scale(1.5)` | box height, key text y |
| holes_1row | `holes(2) rows(1)` | box width, key x |
| holes_2col | `holes(2) cols(2)` | key positions |
| all_p1 | two `pstyle(p1)` scatters, `legend(all)` | key count, legend drawn |
| draw_1, nodraw_2, on_nodraw, off_draw, all_nodraw | one-key `draw`; two-key `nodraw`; `on nodraw`; `off draw`; `all nodraw` | legend drawn? key count |

`_meta` per R7; `git add -f`; test/test_legend_place.py::TestTheFixture names it.

## TDD test stubs

### Regression tests (red at the 43-01 tree), `test/test_legend_place.py` (new)

LT-4: `TestCompassReader::test_each_spelling[spelling]` (every `bp_<s>` spelling's canonical name; red: absent), `TestInsideBplacement::test_ring0[mode-x]` (location per `r0_bp_<x>`; red), `::test_ring0_pos1_sw[mode]` (bottom_left; red), `::test_abbreviation_outside[mode-s]` (`pos(6) bplacement(nor)` -> top_center, no note; red), `::test_by_legend[mode]` (by()'s overall legend reads the same; red if by() has its own lookup).

LT-17: `TestHolesOneColumn::test_spacer_spacing[mode-k]` (stand-in items with no renderers, no hole item, spacer `spacing` per D-43-02.c, for k 1, 2, 4 and the one-key case `holes_1col_1key` -- `spacing == rowgap`, `title_standoff` grown by `rowgap`, no ZeroDivisionError; red), `::test_runs[mode-k]` (k + 1 run Legends tagged `dash_legend_run`, each run's items the original instances -- `run.items[j] is originals[i]` -- and one `legend_runs` dispatcher item; red), `::test_in_chrome[mode]` (Chrome: key text y gaps against `holes_1col_<k>` scaled to px, within 1 px; box height grows by one row gap; red), `::test_stale_suffix_shows[mode]` (Chrome: `(scatter) (lfit) (scatter)` with `holes(1) cols(1)` and a dropdown move that drops rows of the fit's sample: the lfit key's drawn text ends with the stale suffix; saved: the page's filter, served: `_dash_points_stale_follow`; red), `::test_by_cell[mode]` (Chrome: `by(rep78)` with `legend(holes(1) cols(1))`: the runs are in the cell at the composite's places, and clicking a key hides its series in every panel through the `_CLICK_JS` harness of test/test_by_remainder_browser.py; red), `::test_scale[mode]` (`scale(1.5)`: the item's `gap` and `pad` x1.5 and the Chrome gap within 1 px of `holes_1col_scale`; red), `TestHolesTwoColumns::test_full_cell[mode]` (guard).

LT-5: `TestAllDrawNodraw::test_all_keeps_every_key[mode]` (two p1 scatters -> two items, legend visible; red), `::test_draw_is_on[mode]` (one key -> visible; red), `::test_nodraw_is_off[mode]` (two keys -> hidden; red), `::test_on_beats_nodraw[mode]`, `::test_draw_beats_off[mode]` (red), `::test_silent[mode-word]` (no note; red).

### Cases in cscripts

test_wp43_truth.cscript (block order, BRIEF: batch 43.1 landed S01 and S06 first, so every S02 block is inserted directly above the line `* ==== S06 LT-11:`, never above the append marker; each later S02 block goes above that same line, so S02's blocks keep their order) block `* ==== S02 LT-4: ring(0) bplacement ====`: Q4302-1 (each `r0_bp_<x>` and `bp_<s>` against the saved page's Legend location), block `S02 LT-17`: Q4302-2 (`holes_1col_1` box height and key gaps from the page through Chrome, the cert_svg.do page reader extended only if needed), block `S02 LT-5`: Q4302-3 (each `all/draw/nodraw` probe: legend drawn and key count equal to twoway's, live `capture noisily twoway ...` beside `dash`).

### Parity corpus (R8)

`_case("legend(ring(0) bplacement(nw)) (WP-43 LT-4)", [_sc(), plot_for("scatter", yvar="price")], go={"legend": "ring(0) bplacement(nw)"})`, `_case("legend(holes(1) cols(1)) (WP-43 LT-17)", [_sc(), plot_for("scatter", yvar="price"), plot_for("scatter", yvar="rep")], go={"legend": "holes(1) cols(1)"})`, `_case("legend(all) two p1 scatters (WP-43 LT-5)", ...)`; one `MOVE_CORPUS` `_move_case("legend(holes(1) cols(1)) with an lfit after a dropdown move (WP-43 LT-17)", _MOVES[0], ...)` whose layers include an lfit, so both modes' stale suffix is compared.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Compass reader | pytest | legend_place_truth.json | n/a |
| ring(0) bplacement | pytest + Q4302-1 | legend_place_truth.json | yes |
| Holes one column/row, scale() | pytest + Chrome + Q4302-2 | legend_place_truth.json | yes |
| Holes after a move (stale suffix) | Chrome + MOVE_CORPUS | -- | yes |
| Holes in by(), click-to-hide | Chrome | -- | yes |
| Dispatcher budget | test_overlay_budget.py | -- | yes |
| all/draw/nodraw | pytest + Q4302-3 | legend_place_truth.json | yes |

Acceptance: AC-43-02.1 red stubs green; AC-43-02.2 Q4302-1..3 PASS; AC-43-02.3 test_legend_geometry.py, test_legend_histogram_only.py, test_legend_order.py, test_by_grid.py, test_by_remainder.py, test_by_remainder_browser.py, test_overlay_budget.py green; AC-43-02.4 three green commits.

## Tasks

**Commit boundary.** 43-02-01..02 LT-4 `(WP-43 LT-4)`; 43-02-03..05 LT-17 `(WP-43 LT-17)`; 43-02-06..07 LT-5 `(WP-43 LT-5)`. Branch `wp43-s02`. `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp43-s02` (BRIEF "Pull form"): every path and command below runs in it. Every closing task (43-02-02, 43-02-05, 43-02-07) takes **the three closing steps** after its tracking edits and before its commit, in this order, whether the item closes `Closed` or `Documented` (BRIEF "The corpus ledger and the known-differences tables" (1)-(3); D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c; A-10): **(1) the ledger step** -- delete every row of `scripts/corpus/ledger.tsv` whose `gaps4_id` is the item's plain lead id (`LT-4`, `LT-17`, `LT-5`), keep every `<id> (documented)` and `<id> (residual)` row, run `python3 scripts/corpus/ledger.py` (no `--run`: the fixture's `_meta` is kept), `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py test/test_tracking_documents.py -q -n0` in the task's verify; **(2) the known-differences step** -- run `python3 test/known_differences.py <lead id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints (a `*_KNOWN` row whose value is exactly the lead id; `(documented)` and `(residual)` rows are not printed and stay), except that a difference the item's ruling keeps moves into that table's deliberate dict -- the companion dict 33-10 names for it: `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN` (`SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py, `BY_POSITION_DELIBERATE` in test/test_by_text.py, `BY_TYPES_DELIBERATE` in test/test_by_types.py, `STAT_COMBOS_DELIBERATE` in test/test_statistical_truth.py, `COLORVAR_DELIBERATE` in test/test_colorvar_truth.py) -- written `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (none is expected here: every item closes `Closed` and no ruling keeps a difference of LT-4, LT-17 or LT-5; a row the executor would keep without a ruling id is reported to the orchestrator, not moved); then run the hygiene command it prints (`python3 -m pytest <the files defining test_every_known_difference_is_open> -q -n0 -k every_known_difference_is_open`) in the task's verify; **(3) the guard step** -- run block S09 of test/test_wp33_truth.cscript alone (`WP33_ONLY=S09`, BRIEF's two-line driver with `<repo>` = `$WT`); if 33-09's guard check Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script (`DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`), `git add -f` it, rerun S09 to its `Q3309-1 PASS` and commit it with the item (body line `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`). Before each commit: `cd $WT && git pull --ff-only . main` (BRIEF "Pull form"; CLAUDE.md rule 4; a no-op when the batch base already contains main -- if it refuses, stop and report to the orchestrator, never make a merge commit), the tests the change touches, and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (re-run it while it reports `partial` or `truncated`; R13, R4-14). Before editing a function, `node .gitnexus/run.cjs impact "<function>" --direction upstream --repo .`; report a HIGH or CRITICAL risk in the hand-back.

<task type="auto" id="43-02-01">
  <name>Measure placement truth; write LT-4 tests</name>
  <files>scripts/extract_legend_place_truth.do, test/test_legend_place.py, test/test_wp43_truth.cscript</files>
  <action><![CDATA[ Create scripts/extract_legend_place_truth.do with the Stata truth table (R7), run it via scripts/stata_slot.sh, `git add -f test/fixtures/legend_place_truth.json`. Create test/test_legend_place.py with TestTheFixture, TestCompassReader and TestInsideBplacement; insert block S02 LT-4 (Q4302-1) directly above the line `* ==== S06 LT-11:` of test/test_wp43_truth.cscript (block order, BRIEF). Run red on the 43-01 tree; save to <scratch>/43-02-01-failure.txt. Do not commit. ]]></action>
  <verify><![CDATA[ python3 -m pytest test/test_legend_place.py -q -n0 -> TestTheFixture passes; TestCompassReader and TestInsideBplacement fail; python3 -m pytest test/test_cscript_hygiene.py -q -n0 -> pass (blocks in section order: S01, S02, S06) ]]></verify>
  <done>LT-4's failure is recorded.</done>
</task>

<task type="auto" id="43-02-02">
  <name>Read bplacement as twoway; commit LT-4</name>
  <files>dash_render.py, dash.sthlp</files>
  <action><![CDATA[ Implement D-43-02.a/b and TR-43-02.1/2. Help (R3): the legend paragraph's "{cmd:bplacement()} its place along its side" (dash.sthlp :4473-4474) becomes "its place along its side, or, inside the plot region ({cmd:ring(0)}), the plot region's compass point it names; every spelling {cmd:twoway} reads for a compass direction ({cmd:nor}, {cmd:NE}, {cmd:top}, a clock number) is read". CHANGELOG, TWOWAY_COVERAGE_AUDIT.md :143 `[WP-43 LT-4: corrected -- ring(0) bplacement() and twoway's compass spellings]`, BUGS.md, GAPS4.md, `GAPS4_OPEN` (test/test_tracking_documents.py), then the three closing steps for `LT-4` (Commit boundary): (1) delete the plain `LT-4` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py LT-4`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it. Run block S02 alone, `cd $WT && git pull --ff-only . main`, `node .gitnexus/run.cjs detect-changes --scope all --repo .`, commit `Place an inside legend by bplacement() and read twoway's compass spellings (WP-43 LT-4)`. ]]></action>
  <verify><![CDATA[ WP43_ONLY=S02: "Q4302-1 PASS"; python3 -m pytest test/test_legend_place.py test/test_legend_geometry.py test/test_by_grid.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; python3 test/known_differences.py LT-4 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS" ]]></verify>
  <done>LT-4 is closed in one green commit.</done>
</task>

<task type="auto" id="43-02-03">
  <name>Spike the hole composite; write LT-17 tests</name>
  <files>test/test_legend_place.py, test/test_wp43_truth.cscript, test/test_overlay_budget.py</files>
  <action><![CDATA[ In a scratch script (not committed), under /opt/anaconda3/bin/python3 (bokeh 3.8) and python3 (3.9), build a figure with a right-panel spacer Legend of renderer-less stand-ins and two borderless Legends in `fig.center` at numeric locations outside the frame, each holding original LegendItems; load it in Chrome with RangeProbe and export SVG (`Bokeh.index.find_one(model).export("svg")`); record whether both run Legends are drawn in the canvas and in the SVG and whether each stand-in reserves its row. Add TestHolesOneColumn and TestHolesTwoColumns, block S02 LT-17 (Q4302-2, inserted directly above the line `* ==== S06 LT-11:`, after S02 LT-4) and the TR-43-02.7 budget row; run red; save to <scratch>/43-02-03-failure.txt. Do not commit. ]]></action>
  <verify><![CDATA[ the spike's printed result: "drawn canvas 3.8 yes/no, 3.9 yes/no; svg 3.8 yes/no, 3.9 yes/no; stand-in row 3.8 yes/no, 3.9 yes/no"; python3 -m pytest test/test_legend_place.py -k Holes -q -n0 -> new one-column nodes fail; python3 -m pytest test/test_cscript_hygiene.py -q -n0 -> pass ]]></verify>
  <done>The composite's feasibility is measured and LT-17's tests fail.</done>
</task>

<task type="checkpoint" id="43-02-04">
  <name>Escalate if the hole composite fails</name>
  <files>none</files>
  <action><![CDATA[ Only if 43-02-03 printed any "no": stop and report to the orchestrator that D-43-02.c cannot draw a one-column hole on this Bokeh, with the spike's result, and ask whether LT-17 moves to 43-04 (the key cell) or another composite is approved. If every result was "yes", this checkpoint passes with no question. ]]></action>
  <verify><![CDATA[ either every spike result is yes, or the maintainer's answer is recorded by the orchestrator ]]></verify>
  <done>The hole composite is approved by measurement or re-routed by the maintainer.</done>
</task>

<task type="auto" id="43-02-05">
  <name>Draw one-column holes; commit LT-17</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[ Implement D-43-02.c, D-43-02.e and TR-43-02.3/5 (`_dash_legend_hole_runs`, the `legend_runs` handler in `_DASH_OVERLAY_JS`, the by() lines in `_dash_by_keys` and `_dash_by_legend_cell`, copy list, function_test_map). The runs hold the original LegendItem instances; the spacer holds renderer-less stand-ins with `label_text_alpha = 0`; the runs copy the spacer's `click_policy`. Add the parity and move cases. Help (R3): the legend paragraph's holes sentence (dash.sthlp :4469-4470, "{cmd:holes(2)} leaves the second place blank") gains "; in a one-column or one-row legend a hole is a row's or a column's gap, as {cmd:twoway} draws it". CHANGELOG, TWOWAY_COVERAGE_AUDIT.md :143 `[WP-43 LT-17: corrected -- a hole in a one-column legend is a row gap]`, tracking (BUGS.md, GAPS4.md, `GAPS4_OPEN` in test/test_tracking_documents.py), then the three closing steps for `LT-17` (Commit boundary): (1) delete the plain `LT-17` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py LT-17`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it. `cd $WT && git pull --ff-only . main`, `node .gitnexus/run.cjs detect-changes --scope all --repo .`, commit `Draw a hole in a one-column legend as a row gap (WP-43 LT-17)` with the spike's result in the body. ]]></action>
  <verify><![CDATA[ WP43_ONLY=S02: Q4302-1, Q4302-2 PASS; python3 -m pytest test/test_legend_place.py test/test_legend_geometry.py test/test_label_sinks.py test/test_by_remainder.py test/test_by_remainder_browser.py test/test_overlay_budget.py test/test_mode_parity.py -k "legend or WP-43 or by or Budget" -q -n0 -> pass; python3 -m pytest test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; python3 test/known_differences.py LT-17 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS" ]]></verify>
  <done>LT-17 is closed in one green commit.</done>
</task>

<task type="auto" id="43-02-06">
  <name>Write the LT-5 regression tests</name>
  <files>test/test_legend_place.py, test/test_wp43_truth.cscript</files>
  <action><![CDATA[ Add TestAllDrawNodraw and block S02 LT-5 (Q4302-3, live twoway beside dash for each `all/draw/nodraw` probe; inserted directly above the line `* ==== S06 LT-11:`, after S02 LT-17); run red on the LT-17 tree; save to <scratch>/43-02-06-failure.txt. Do not commit. ]]></action>
  <verify><![CDATA[ python3 -m pytest test/test_legend_place.py::TestAllDrawNodraw -q -n0 -> every node fails; python3 -m pytest test/test_cscript_hygiene.py -q -n0 -> pass ]]></verify>
  <done>LT-5's tests fail for the measured reason.</done>
</task>

<task type="auto" id="43-02-07">
  <name>Honour all, draw, nodraw; commit LT-5</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[ Implement D-43-02.d (merge skipped under `all`; draw/nodraw read as on/off; the three words in `_DASH_LEGEND_SUBOPTS`); flip the pins found by the grep in Evidence with `Flipped:` reasons. Add the parity case. Help: the legend paragraph (after the order()/label() sentences, dash.sthlp :4440-4447) gains "{cmd:all} keys every plot, so two plots that look alike keep two keys; {cmd:draw} is {cmd:on} and {cmd:nodraw} is {cmd:off}, as in {cmd:twoway}". CHANGELOG, TWOWAY_COVERAGE_AUDIT.md :143 `[WP-43 LT-5: corrected -- all, draw and nodraw honoured]`, tracking (BUGS.md, GAPS4.md, `GAPS4_OPEN` in test/test_tracking_documents.py), then the three closing steps for `LT-5` (Commit boundary): (1) delete the plain `LT-5` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py LT-5`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it. `cd $WT && git pull --ff-only . main`, `node .gitnexus/run.cjs detect-changes --scope all --repo .`, commit `Honour legend(all), draw and nodraw as twoway does (WP-43 LT-5)`. ]]></action>
  <verify><![CDATA[ WP43_ONLY=S02: Q4302-1..3 PASS; python3 -m pytest test/test_legend_place.py test/test_legend_histogram_only.py test/test_legend_order.py test/test_subopt_abbrev.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; python3 test/known_differences.py LT-5 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS" ]]></verify>
  <done>LT-5 is closed in one green commit.</done>
</task>

## Section completion criteria

Three green commits on `wp43-s02`; Q4302-1..3 PASS; the spike recorded in the LT-17 commit body; one dispatcher callback per figure (no new layout CustomJS); the stale suffix and by() click-to-hide shown in Chrome in both modes; tracking per item; the three closing steps taken in each closing commit (no plain `LT-4`, `LT-17` or `LT-5` row left in scripts/corpus/ledger.tsv, corpus_ledger.json regenerated, test_corpus_ledger.py green; `python3 test/known_differences.py <id>` printing no row for any of the three ids and every table's `test_every_known_difference_is_open` green; S09's Q3309-1 PASS, the guard fixture regenerated and committed with the item whenever Q3309-1 reported a change); the S02 blocks above `* ==== S06 LT-11:` (test_cscript_hygiene.py green); detect-changes run before each commit; no tooling names.

## Notes

- Traps: `_dash_compass_dir` must not lower-case (twoway's `NOR` is unknown); a clock number is read only when the text is at most two characters (`3.0` is unknown). The run Legends are extra `fig.legend` entries: `cv_legends` filtering, step 8's `plot_legends` visibility, `_dash_by_keys`' `series_legends` and the stale cue must treat the spacer as the one plot legend and the runs as its drawing (tests count both). Each original LegendItem sits in exactly one run, never in two Legends. The runs copy the spacer's `click_policy` (Bokeh's default `none` on an ordinary legend, `hide` in by()'s cell).
- Help paragraphs owned (R3): the legend paragraph's bplacement, holes and the new all/draw/nodraw sentences (dash.sthlp :4440-4475).
- Merge rules: R1, R2, R4, R5, R7, R8, R9, R12 (`_dash_apply_legend` alone in 43.2), R13.
- Commit-body lines: `Regression: test/test_legend_place.py::TestInsideBplacement::test_ring0 -- failed at <base sha> with <text>`; `Fixture: test/fixtures/legend_place_truth.json (scripts/extract_legend_place_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (every commit; plus `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` when Q3309-1 reported a change).
