# Section 49: horizontal drawn (P1.9 part a, M5)

> Part of: WP-30 · Items: P1.9a (entry `P1.9a`; REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15, the WP-29 S04/S05 horizontal notes) · Risk: yellow · Batch: 17 (merge order S48, S49, S50) · Depends on: 14, 18, 19, 21, 24, 35, 45 · Blocks: 55 · Tasks: 13, 1 commit · Case prefix: HZ

## Review amendments

- Fixed (major, executability): `TestUprightIsUntouched` pinned 40 page digests recorded at the batch-17 base, a combined pin R10 does not list; S54 (toolbar), S55 and S56 change every page and would each have had to re-derive 40 digests. The guard now compares, in the same run, the normalised page without the flag with the page built with `vertical` and with the transposition patched to raise (Risk mitigation 5, BR-49.6, the stub, 49-01).
- Fixed (minor): 49-08 ran `test_keys_and_titles.py`, which no section creates; S19's file is `test_series_labels.py`.
- Fixed (minor): TR-49.7 reads the flags from `s()` after S45's sclass `_dash_recast_opt`; 49-03 now confirms S45's program keeps `s()` (no `sreturn clear`, as dash.ado:1536 says of the other helpers) and stops otherwise.
- Checked at HEAD: dash.ado:953 (`HORizontal VERTical`), :1069 and :1112 (pending lines), :1207-1208, :3153; dash_render.py:797 (the docstring), 23112 (`_DASH_X_COORDS`), 23946 (`_dash_assign_axis_ranges`), 30611 and 30649 (saved layer loop), 35009 (served), copy-list `"_dash_add_pc_glyph", "_dash_note_no_second_y",` 33132; Mata `_dash_rep_scan`'s closing brace 4624; `test_option_validation.cscript`'s final line 914.
- Checked: the refusal rule of TR-49.7 reproduces every E4 row (typed order first, then the conflict; derived types refused only when type and target both refuse); M5 (twoway's words, r(198)) and M6 (`vertical` silent) hold; both build loops call the one helper; no user text reaches a property name (TR-49.11).
- Checked (batch 17): S49 alone edits `_make_figure_body` and `_generate_app_source` (R12); S48 (`_dash_validate_value`'s by() branch, by() layout functions) and S50 (refline functions, `SchemeParser._init_properties`, finishers) share no function with it; the copy-list anchors (33132, 33200, 33383) are distinct; shared `_needed`, Mata header-index and CORPUS lines conflict in context only.
- Cross-file (notes file): index 17.0's expected list omits S49's `_generate_app_source` (HIGH) and `_glyph_layer_lines` (HIGH).
- Rejected: splitting 49-01 so the fixture is listed in `<files>` (the extractor writes it; BRIEF allows three paths and the commit task stages it with `git add -f`).
- The review pass applied both lenses.

**Binding readings applied in this file** (M1, M5, M6; register P1.9.1-P1.9.4, P1.17.5, X.1, X.5; index A138, IR-13, A148, A149, R1-R12):
- **P1.9.1 (M5).** `horizontal vertical` together, on a type that takes both, is refused r(198) `may not combine options horizontal and vertical`.
- **P1.9.2 (M5).** `horizontal` or `vertical` on a type twoway refuses it for is refused r(198) `option horizontal not allowed` / `option vertical not allowed`, judged after S45's `recast()` (IR-13: here, after S45). This file measures the rule exactly (E4): a base or range type is judged on its recast target; a derived type (fits, smoothers, kdensity, function, histogram) is refused only when both it and its recast target refuse the flag.
- **P1.9.3 / A26 and IR-13.** The default axis titles swap through S19's helper: each layer's contribution is read through its orientation, and S19's first-equals-last rule then applies unchanged; this reproduces all eight measured mixed cases (E3). `_dash_axis_labels` is edited only for the univariate first-layer defaults it still owns.
- **P1.9.4 / A27.** P1.5 (S18), P1.17a (S14), P1.23a (S35), P1.16 (S19) and P1.8b (S45) have landed; S49 adds the swap to their helpers: S18's tick-format helper, S14's `dash_cap` markers, S35's axis decisions and `_axis_kind`, S19's title helper.
- **P1.17.5.** Every renderer tagged `dash_cap` is rotated by π/2, so rcap caps stay perpendicular to the spine.
- **M6.** `vertical` on a type that takes it is accepted silently; neither flag is named in the "ignoring unsupported option(s)" note any more.
- **Manifest note.** After-move parity (hover fields, `hline`, the moved-geometry and parity-corpus move tests) is S55's (batch 19). This section's tests are at build, in both modes.
- **R12.** S49 is batch 17's only editor of `_make_figure_body` and `_generate_app_source`; it edits no applier, no finisher (R11; S50 is batch 17's finisher editor), `_build_filter_widgets`, `_FILTER_JS` or `_dash_build_hover` (S55's).

**Section decisions.**
- **D-49a. One transposition after the mapper.** A layer is drawn exactly as today, then `_dash_transpose_layer` rebuilds each of its glyphs (five slots) under a fixed property map and swaps its annotations' data coordinates. Column names and data do not change, so every move path that writes columns keeps working. It runs after S21's `_dash_tag_hull_roles` (its `_dash_auto_base` stamps are re-mapped by the same map) and before `_dash_assign_axis_ranges`, which keeps `yaxis(2)`/`xaxis(2)` physical, as twoway does (E3).
- **D-49b. One role rule.** `_dash_role_letter(plot, letter)` answers which data role a physical axis letter shows: the other letter for a horizontal layer, the same otherwise. Every reader of a layer's axis variables calls it once.
- **D-49c. Where the refusal runs.** A new dash.ado program `_dash_hz_check`, called in `_dash_process_segment` directly after S45's recast step, reads the resolved type, the recast target and the typed order of the two flags (a Mata scan of the segment's option text), in E4's order.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:99 (P1.9): "`horizontal` is not drawn on any type. It is common on bar, rcap, rspike and dropline." WP-29 S04/S05 left `horizontal` on `function` and on computed layers on a date axis here. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-09.md` M3, critic c1-c3):

```
dash bar mpg weight, horizontal              -> dash: ignoring unsupported option(s): horizontal()  rc=0
dash bar mpg weight, vertical                -> dash: ignoring unsupported option(s): vertical()    rc=0
dash bar mpg weight, horizontal vertical     -> both named, rc=0      (twoway: r(198) may not combine options horizontal and vertical)
dash function y=x^2, range(0 2) horizontal   -> named, drawn upright
bar H saved: VBar{'x': 'weight', 'top': 'mpg', 'bottom': 0, 'width': 56.0} (same as upright); rcap, histogram, area, rbar likewise; served identical
```

dash_render.py reads `horizontal` nowhere (the docstring at :797 is the only hit); dash.ado declares `HORizontal VERTical` (:953), puts both on the pending list (:1069, :1112) and serialises them (:3153); dash.sthlp:3687-3690 says "dash draws every plot upright".

**After this section**, in the saved page and the served app:
- `horizontal` draws the exact transpose of the upright layer on the 24 types twoway turns (area, bar, spike, dropline, dot, histogram, kdensity, rarea, rbar, rspike, rcap, rcapsym, rline, rconnected, rscatter, pcspike, pcarrow, pcbarrow, pcscatter, pccapsym, pci, pcarrowi, function, tsrline), with the scheme's alpha kept, rcap caps perpendicular, marker-label offsets physical, colour-key swatches untouched;
- axis variables, default titles, date kinds, tick formats and second-axis ranges follow the layer's orientation; `yaxis(2)` stays physical; a mixed-orientation graph with a date variable labels each axis as twoway does;
- the refusals of E4 are dash's, in twoway's words; `vertical` is accepted silently; neither flag is named.

**Why one section.** One transposition and one role rule, consumed by the axis helpers of five landed sections, with the refusal that must read S45's recast type (research §8 split 9a; IR-13). S55 owns interaction parity.

**Test order and commit rule (rule 7).** One cycle on `wp30-s49`: 49-01 and 49-02 write the fixture and every regression test against the unmodified batch-17 base and save `$S/49-P1.9a-failure.txt` (no commit); 49-03 to 49-12 fix, flip and document; 49-13 closes the entry and commits.

## Risk: [yellow] — the CRITICAL figure body, a HIGH template and title helper, and seven landed sections' helpers read through a new role rule

**Why.**
- `DashRenderer._make_figure_body` CRITICAL (4 impacted); `ServerAppBuilder._generate_app_source` HIGH (5); `_dash_axis_labels` HIGH (4: `_build_sources_and_figures`, `_dash_add_secondary_axes`, `_make_figure_body`); `_glyph_layer_lines` HIGH (4) (research §6).
- LOW but copied into the served app by name (treat as MEDIUM): `_dash_figure_date_kind` (3), `_dash_axis_vars` (3), `_compute_secondary_range` (3), S35's `_dash_layer_axis_names`, S19's `_dash_axis_default_titles`, S18's `_dash_axis_tick_formats` (impact at 17.0; new since `c96facd`).
- `GlyphMapper._axis_kind` (S35's method; travels with the class); `map_*` UNKNOWN (dispatch dict, grep). `_DASH_X_COORDS` UNKNOWN (constant; grep: `_dash_secondary_values`, the hull readers, S21's `_dash_layer_extent` and plan).
- dash.ado `_dash_process_segment`, `_dash_parse_plot_opts` and the new program: UNKNOWN (not indexed).

**Risk factors.**
1. A glyph class the map does not know would stay upright in silence.
2. Property-name stamps (`_dash_auto_base`) and S21's plan readers may assume VBar/Segment orientation.
3. A reader of axis variables that is missed keeps the upright role (one axis titled or formatted wrongly).
4. Swatches and keys inside the layer's slice would be moved.
5. Upright output must not change by a byte.
6. The refusal must read S45's resolved type and the typed order.

**Mitigation.**
1. `_DASH_TRANSPOSE` covers every class the 24 types emit (research M5 inventory, re-run at the base by `TestEveryTurnedTypeIsMapped`); an unmapped class draws upright with one note, and the test fails.
2. The map re-maps `_dash_auto_base`; `TestTheHullSeesTransposedGlyphs` checks the Python hull, S27's clamp and S21's saved plan for an HBar and an HArea at build. If the plan or the clamp cannot read them, S49 stops and reports: those are finisher changes (R11).
3. `_dash_role_letter` is the one rule; `TestTheAxesFollowTheLayer` covers titles, tick formats, date kinds and y2 for every type against the fixture.
4. Swatches (`_dash_is_swatch`), `Legend` and `ColorBar` are skipped, as `_dash_assign_axis_ranges` skips them (:23960-23963); `dot …, colorvar() horizontal` is tested.
5. `TestUprightIsUntouched` builds every type without the flag and compares its normalised saved page (`normalise_bokeh_html`, as `test_varlist_expansion.py`'s digest test does) with the same type built with `vertical` and with the page built while `_dash_transpose_layer` is patched to raise: equal pages, and the patch never fires. No digest is pinned, so later sections that change every page (S54's toolbar) move no S49 pin.
6. HZ-01..HZ-14 compare rc and first line with live twoway for E4's rows, orders and recast cases.

## Dependencies

- **Depends on: 14, 18, 19, 21, 24, 35, 45.**
  - S14 (batch 5): one-x-unit bar widths (`_bar_extent`, `__dash_bar_*` columns on period axes), rcap caps as `marker="dash"` Scatters tagged `dash_cap`, and no spacing machinery (so a turned bar's height needs no move-time writer).
  - S18 (batch 6): `_dash_axis_tick_formats` per axis.
  - S19 (batch 7): `_dash_axis_default_titles` (first-equals-last per axis) and the yaxis(2) own-layer titles in `_dash_add_secondary_axes`.
  - S21 (batch 7): `_dash_tag_hull_roles` (its `_dash_auto_base` stamps), `_dash_layer_extent`, the hull and plan readers over `_DASH_X_COORDS`/`_DASH_Y_COORDS`.
  - S24 (batch 8): construction-site alphas, which the rebuilt glyph keeps.
  - S35 (batch 12): `_dash_figure_date_kind(…, axis_no)`, `_dash_layer_axis_names`, `_dash_axis_vars(plots, axis_no)`, `GlyphMapper._axis_kind`/`_unit_kind`, the mixed-axis transform and its letter map; its note for S49 (section-35 Notes: "swap the x/y keys of `_dash_layer_axis_names`, the letter in `_axis_kind`/`_unit_kind` callers, and the pass's letter map, in one place each").
  - S45 (batch 16): `_dash_recast_opt` (base and range types rewritten to the target; derived types keep their type and carry the canonical target) and the draw-as helper.
  - S01: entry `P1.9a`, its key, the markers `<!-- WP-30 P1.9a -->` (Results that change; Changed behaviour), the stub `* ==== S49 P1.9a: horizontal drawn ====`, the anchors `# WP-30 S49 (P1.9a): horizontal drawn (P1.9 part a, M5)`.
- **Blocks: 55** (hover, `hline`, the move-path parity and the move corpus).
- **Parallel batch: 17**, merge order S48, S49, S50. **Can run with** S48 (by() layout, dash.ado's by() validation) and S50 (reference lines, finishers, scheme keys): no shared function.

## Evidence

Anchors at `c96facd`; re-find each by symbol at `batch-17-base` (batches 5-16 moved most).

### E1. The flags reach the spec and nothing reads them

dash.ado:953 `HORizontal VERTical`; :1069 `if `: length local horizontal' local _dash_pending …`; :1112 the same for `vertical`; :1207-1208 `sreturn local horizontal/vertical`; :3153 the JSON key list. `_dash_fold_typed` (1749; one caller, `_dash_process_segment` :4134) never touches them.

### E2. The layer loops (dash_render.py)

Saved, `_make_figure_body`:
```python
30611            _layer_renderers = list(fig.renderers[_r_before:])
...
30649            _dash_assign_axis_ranges(fig, _layer_renderers, popts,
30650                                     list(fig.center[_c_before:]))
```
Served, the template's layer block (generated text):
```python
35009            "        _dash_assign_axis_ranges(fig, fig.renderers[_before:], opts,",
35010            "                                 list(fig.center[_before_c:]))",
```
`_dash_assign_axis_ranges` (23946) skips `Legend`/`ColorBar` among the annotations. The served redraw draws on a throwaway figure and returns sources only (35083-35092). `_DASH_X_COORDS = ("x", "x0", "x1", "left", "right")` (23112) lacks HArea's `x2`. `_dash_axis_hull` already reads "an HBar's y ± height/2" (23580, 23620-23621; critic). `_dash_axis_vars` (821) and `_dash_figure_date_kind` (788) read a univariate `var` on x only (docstring: "`horizontal` is not read here yet, P1.9"). `_dash_axis_labels` (21665) takes the first layer's `xvar`/`yvar` or the univariate defaults. `_compute_secondary_range` (7684) reads `var_key` ("yvar" for y2) of the layers on axis 2.

### E2b. The refusal precedent (dash.ado `_dash_option_rules` 2090-2105, `_dash_validate_opts` 2598-2611)

dash already refuses type-specific flags by table (`discrete@histogram`, `stdp|stdf|stdr@lfitci|qfitci|fpfitci`, `mean|noweight|adjust|logit@lowess`):

```stata
    foreach tok of local _dash_rules_flags {
        ...
        if `: list ptype in types' continue
        foreach f of local names {
            if `"`s(`f')'"' != "" {
                display as error "option `f' not allowed"
                exit 198
```

That loop judges `ptype` only and in declaration order. `horizontal`/`vertical` need the recast target, the derived-type rule and the typed order (E4), so they get their own program (D-49c) instead of two rows in the table; the wording is the table's.

### E3. twoway's drawing (research M2, M4, critic 8)

All 24 types draw the exact transpose of the upright drawing, swapping data roles and default titles (pc family, pci/pcarrowi, function and tsrline included). Geometry: `bar` rect x[1.5..2.5] y[10..30] → x[10..30] y[1.5..2.5]; `dropline` (2,10)-(2,30) → (10,2)-(30,2); `rcap` cap (0.974..1.026, 14.0) → (14.0, 0.961..1.039). Date: `(bar y d, horizontal)` puts the dates on y titled "Day"; a date histogram horizontal has y 08jan2020..22apr2020 and x "Density". `yaxis(2)` is physical: `(scatter y x) (bar y x, horizontal yaxis(2))` puts the bar's x on the right axis. Marker labels keep their physical clock (dropline 3 o'clock both ways). Titles: `(scatter y x)(bar y x, horizontal)` none; `(scatter)(bar h)(scatter)` y "Yvar", x "Xvar"; `(bar h)(bar h)` y "Xvar", x "Yvar"; `(rcap lo hi x, h)(scatter x y)` y "Xvar", no x. Mixed with a date d (%td): `(scatter y d) (bar y d, horizontal)` x dates, y numeric; reversed order: y dates, x numeric; no titles; legend "Yvar" twice. t* options stay physical (`tsrline …, horizontal tlabel(2 4)` labels the horizontal axis).

### E4. twoway's refusals (this pass, `p49.do`, `p49b.do`, `p49c.do`, StataNow 19.5, `nodraw`)

```
scatter|lfit|lowess|scatteri|tsline …, horizontal       r(198) option horizontal not allowed
kdensity mpg, vertical / function …, vertical           r(198) option vertical not allowed
kdensity mpg, horizontal vertical (either order)        r(198) option vertical not allowed
scatter mpg weight, horizontal vertical                 r(198) option horizontal not allowed
scatter mpg weight, vertical horizontal                 r(198) option vertical not allowed      (typed order)
bar mpg weight, vertical horizontal / hor vert          r(198) may not combine options horizontal and vertical
rcap mpg price weight, recast(rscatter) horizontal vertical   r(198) may not combine …
bar …, recast(scatter) horizontal / recast(lfit) horizontal   r(198) option horizontal not allowed
scatter …, recast(bar) horizontal; line …, recast(area) horizontal   rc 0
area …, recast(line) vertical                           r(198) option vertical not allowed
kdensity …, recast(area) vertical; function …, recast(area) vertical; lfit …, recast(bar) horizontal;
  lowess …, recast(bar) horizontal; histogram …, recast(scatter) horizontal; kdensity …, recast(line) horizontal;
  histogram …, recast(line) vertical                    rc 0
lfit …, recast(scatter) horizontal; lowess …, recast(line) horizontal   r(198) option horizontal not allowed
kdensity …, recast(line) vertical; function …, recast(line) vertical    r(198) option vertical not allowed
bar mpg weight, HORIZONTAL                              r(198) option HORIZONTAL not allowed     (dash's unknown-option path; P2.21)
```
Research M1: `horizontal` rc 0 on the 24 types above, r(198) on scatter, line, connected, lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline, scatteri, tsline; `vertical` the same 24 less kdensity and function. The rule: a refusing type names its first refused flag in typed order, before the conflict check; a derived type is refused only when its own type and its recast target both refuse the flag.

### E5. Tests that pin today's behaviour (re-measured by 49-10/49-11)

- `test/test_help_claims_8.py::…::test_bars_are_drawn_vertically_at_the_x_values[horizontal]` (:1339-1342) and `::test_a_spike_is_drawn_upright_even_with_horizontal` (:1371-1380).
- `test/test_unsupported_report_is_true.py` PLOT_VALUES rows `"horizontal": ("horizontal", "", "bar")` (:111) and `"vertical": ("vertical", "", "bar")` (:150); the pending count (:240, as S45 left it); the declared count (:607) re-measured.
- `test/test_help_conformance.py` `test_the_ignored_list_was_found` / `test_the_unsupported_section_was_found` counts; `test/test_help_claims_8.py`'s Unsupported equality pin and `TestTheUnsupportedProseIsTrue`.
- `test/test_help_claims_8.cscript` HC8-02/HC8-03 and `test/test_twoway_option_parity.cscript` TP-06/TP-13a rows naming `horizontal`/`vertical` (grep at the base); HC8-03's twoway side stays.
- Not flips: `test/fixtures/rejected_options.json:1130-1200` (S58, A145).

## User stories

- **US-49.1** As a twoway user, I want `twoway bar mpg rep, horizontal`, `rcap lo hi x, horizontal` and `dropline y x, horizontal` drawn sideways, with the axes, titles and date labels swapped, in the saved page and the served app.
- **US-49.2** As a twoway user, I want `horizontal` on histogram, kdensity and function, and on range and pc plots, drawn as twoway draws them.
- **US-49.3** As a twoway user, I want `horizontal vertical`, or `horizontal` on a scatter, refused in twoway's words, judged after `recast()`.
- **US-49.4** As a dashboard publisher, I want dashboards without `horizontal` to stay exactly as they are.

## Business requirements

- **BR-49.1** On the 24 types, `horizontal` draws the transpose of the upright layer: every coordinate swapped, bar widths become heights, areas fill toward the x axis, rcap caps perpendicular, pc arrows turned; the scheme's alpha and every explicit style kept; colour-key swatches, legends and colour bars unmoved.
- **BR-49.2** Marker-label offsets and angles stay physical; `yaxis(2)`/`xaxis(2)` are physical (a horizontal layer's x role on `yaxis(2)` is on the right axis).
- **BR-49.3** Axis variables, tick formats, date kinds and default titles are read per physical axis through each layer's orientation; titles then follow twoway's first-equals-last rule (E3's eight cases); univariate defaults swap (histogram horizontal: y the variable, x "Density").
- **BR-49.4** Refused as twoway, r(198), in E4's order: a refused flag on its type (judged on the recast target, or for a derived type on both) as `option horizontal not allowed` / `option vertical not allowed`, the first refused flag in typed order; then both flags together `may not combine options horizontal and vertical`.
- **BR-49.5** `vertical` on a type that takes it is accepted and draws the upright layer, silently; neither flag is named in any note; graph-level `horizontal` stays refused as today.
- **BR-49.6** Without `horizontal`, no layer is transposed and every page is what it would be without S49's transposition (the normalised page equals the one built with the transposition disabled, and the one built with `vertical`).

## Technical requirements

- **TR-49.1 Constants** (dash_render.py, directly after `_DASH_X_COORDS`, 23112): `_DASH_HORIZONTAL_TYPES` and `_DASH_VERTICAL_TYPES` (tuples, E4's 24 and 22); `_DASH_DERIVED_ORIENT_TYPES` (lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline, kdensity, function, histogram); `_DASH_TRANSPOSE`, a dict of tuples: glyph class name → (new class name, pairs to swap), covering at least `VBar→HBar` (x↔y, top↔right, bottom↔left, width↔height), `HBar→VBar` (the inverse), `VArea→HArea` (x↔y, y1↔x1, y2↔x2), `HArea→VArea`, `Quad` (left↔bottom, right↔top), `Segment` (x0↔y0, x1↔y1), `Scatter`, `Line`, `Circle`, `Step` (x↔y), `Patch`/`Patches`/`MultiLine` (xs↔ys) and every class 49-01's inventory finds; annotations `LabelSet`/`Label` (x↔y; offsets, angle, align and baseline unchanged), `Arrow` (x_start↔y_start, x_end↔y_end), `Span` (`dimension` width↔height). `_DASH_X_COORDS` gains `"x2"` (and `_DASH_Y_COORDS` nothing).

  | Upright class (types, research M5) | Turned class | Pairs swapped | Kept as they are |
  |---|---|---|---|
  | VBar (bar, rbar) | HBar | x↔y, top↔right, bottom↔left, width↔height | fill/line style, alpha, `__dash_bar_*` field specs |
  | VArea (area, rarea) | HArea | x↔y, y1↔x1, y2↔x2 | fill style, alpha |
  | Quad (histogram) | Quad | left↔bottom, right↔top | the recount's columns `left`, `right`, `top` |
  | Segment (spike, rspike, rcap, pcspike, pci, dropline, rcapsym, pccapsym, pcarrow, pcbarrow, pcarrowi) | Segment | x0↔y0, x1↔y1 | line style |
  | Scatter (dot, rscatter, pcscatter, dropline/rcapsym/pccapsym markers, rcap caps) | Scatter | x↔y; `dash_cap` angle + π/2 | marker, size, style |
  | Line (kdensity, rline, function, tsrline, rconnected) | Line | x↔y | line style, S40's pre-expanded stair vertices |
  | LabelSet (bar, dropline, rcapsym, dot, rscatter, rconnected, pcscatter) | LabelSet | x↔y | `x_offset`, `y_offset`, `angle`, `text_align`, `text_baseline`, S37's per-row fields |
  | Arrow (pcarrow, pcbarrow, pcarrowi heads) | Arrow | x_start↔y_start, x_end↔y_end | heads, style |
- **TR-49.2 `_dash_is_horizontal(plot) -> bool`**: `options.horizontal` non-blank and either the layer's type or the canonical recast target S45 writes into its options is in `_DASH_HORIZONTAL_TYPES` (this covers E4's accepted derived cases: `kdensity …, recast(line) horizontal` by its own type, `lfit …, recast(bar) horizontal` by its target). A hand-built spec with `horizontal` on a type and target that both refuse it draws upright, silently (dash.ado refuses it first).
- **TR-49.3 `_dash_role_letter(plot, letter) -> str`**: `"y"` for `"x"` and `"x"` for `"y"` when `_dash_is_horizontal(plot)`, else `letter`; any other letter unchanged.
- **TR-49.4 `_dash_transpose_layer(fig, renderers, annotations) -> None`**: for each `GlyphRenderer` that is not a swatch (`_dash_is_swatch`), rebuild `glyph`, `selection_glyph`, `nonselection_glyph`, `hover_glyph`, `muted_glyph` (each that is a model, not `"auto"`/None) as `cls(**swapped(properties_with_values(include_defaults=False)))`, keeping `name`, `tags` and field specs (with any `transform`) as they are; a renderer tagged `dash_cap` adds π/2 to `angle`; re-map `_dash_auto_base` names (and any other S21/S27 property-name stamp found at the base) through the pairs; for each annotation that is not `Legend`/`ColorBar`, swap its pairs in place. An unmapped class leaves the renderer upright and emits one note through S06's channel, `(note: horizontal: <type> is drawn upright; dash cannot turn a <class>)`. Pure Bokeh model edits, no data access.
- **TR-49.5 Both loops.** Saved: in `_make_figure_body` (CRITICAL: warn), after S21's `_dash_tag_hull_roles(...)` call and before `_dash_assign_axis_ranges(...)` (30649): `if _dash_is_horizontal(plot): _dash_transpose_layer(fig, _layer_renderers, list(fig.center[_c_before:]))`. Served: in `_generate_app_source` (HIGH: warn), the same two generated lines directly before `"        _dash_assign_axis_ranges(fig, fig.renderers[_before:], opts,"`, with `fig.renderers[_before:]` and `fig.center[_before_c:]`.
- **TR-49.6 The role rule in the readers** (one place each; S35's note):
  - S35's `_dash_layer_axis_names(plot, key)`: the names read for physical key `key` are those of role `_dash_role_letter(plot, key[0])`; the axis number stays the physical option (`yaxis` for "yvar"). A univariate horizontal layer contributes its `var` on "yvar" only.
  - `_dash_axis_vars(plots, axis_no)` (S35's form): per physical letter, the first non-literal layer's role-letter variable.
  - `_dash_figure_date_kind`: through `_dash_layer_axis_names` (no own change if S35 routes it there; otherwise the same swap).
  - `GlyphMapper._axis_kind(self, fig, axis, options)` (S35's): `axis = _dash_role_letter({"type": …, "options": options}, axis)` first, so a mapper's role letter reaches the physical axis (and its `yaxis(2)`/`xaxis(2)`); `_unit_kind` and `_on_axis` follow. S35's mixed-axis pass's letter map: the same call.
  - S19's `_dash_axis_default_titles`: each layer's x and y contributions read through `_dash_role_letter`; the rule unchanged. `_dash_axis_labels` (HIGH: warn): its univariate first-layer defaults swap when that layer is horizontal (if S19 moved them into its helper, the swap goes there and `_dash_axis_labels` is not edited). S19's y2/x2 own-layer titles in `_dash_add_secondary_axes`: the same per-layer read.
  - S18's `_dash_axis_tick_formats`: the format of the physical axis's first-layer variable through `_dash_role_letter`.
  - `_compute_secondary_range`: for a horizontal plot on `axis_key`, read the opposite role's variable.
- **TR-49.7 dash.ado.** Delete the two pending lines (:1069, :1112) and reword their comment. New program `_dash_hz_check` (`version 19`, after `_dash_fold_typed`'s `end`): `args ptype target S` (resolved type, S45's canonical recast target or empty, a string scalar holding the segment's option text). It reads the typed order of the two flags through new Mata `_dash_hz_order(string scalar scname)` (part 5, directly after `_dash_rep_scan`'s closing brace, 4624 at c96facd, so its hunk stays apart from S48's functions after `_dash_rep_value`: `_dash_rep_toks`/`_dash_rep_optname` with the minimums `hor` and `vert`; sets `_hz_order` to `horizontal vertical`, `vertical horizontal`, one word or empty). For each flag in that order that `s()` holds: accepted if `ptype` takes it, or `target` takes it and `ptype` is in the derived list (E4); otherwise `display as error "option <flag> not allowed"`, `exit 198`. Then, both held: `may not combine options horizontal and vertical`, r(198). Called in `_dash_process_segment` directly after S45's recast call and before `_dash_fold_bw`, with the segment text in a tempname scalar (read through `st_local`, never expanded). The flags are `s(horizontal)`/`s(vertical)` from `_dash_parse_plot_opts`, which survive the sclass helpers called after it (dash.ado:1536); 49-03 confirms by grep that S45's `_dash_recast_opt` has no `sreturn clear` and stops and reports if it has. Type lists are dash.ado locals equal to TR-49.1's tuples (a test parses both).
- **TR-49.8 Copy list (R2 row S49).** Functions tuple, new lines directly after `"_dash_add_pc_glyph", "_dash_note_no_second_y",` (33132): `# horizontal (WP-30 P1.9a).` and `"_dash_is_horizontal", "_dash_role_letter", "_dash_transpose_layer",`. The constants (tuples and dicts of tuples) reach the app through `_supply_missing_constants`.
- **TR-49.9 Registries.** `test/function_test_map.py` under S49's anchor: `_dash_is_horizontal`, `_dash_role_letter`, `_dash_transpose_layer` (no nested functions). `test/program_coverage_map.py`: `_dash_hz_check` (dash.ado anchor), `_dash_hz_order` (Mata anchor); `_needed` gains `_dash_hz_order`; the Mata header index one entry.
- **TR-49.10 Help** (R3: "Plot types" and the Unsupported section). "Plot types": a paragraph "Orientation" naming the 24 types, `vertical` as the default, the refusals, `yaxis(2)` and labels physical, histogram/kdensity titles swapped. Unsupported: the "Orientation, bar labels and positions" entry (:3687-3690) becomes "Bar labels and positions" (blabel, at()).
- **TR-49.11 Security (rule 1).** The property map is a constant; nothing reads a property name from user input or JSON; the transposition writes only model properties; dash.ado reads the segment text by value; messages are constant text. No new HTML or JS sink.

## Boundaries

- **Not edited:** `_dash_build_hover`, `_FILTER_JS`, `_build_filter_widgets`, `_dash_copy_redraw_geometry` (S55); the finishers and `_dash_axis_plan` (R11, S50); the appliers (R12); every `map_*` (the transposition is after them); `_dash_assign_axis_ranges`; `_apply_mlabel_opts` (offsets stay physical, S37's BR-37.8).
- **Batch partners:** S48 (by() layout, `_dash_validate_value`'s by() branch); S50 (reference lines, scheme keys, finishers).
- **Residuals:** none new; `horizontal` on `dot` keeps dot's geometry (P2.9).

## Stata truth

New `scripts/extract_horizontal_truth.do` in S02's form, run through the slot with `DASH_REPO="$WT"`; writes `test/fixtures/horizontal_truth.json` (`git add -f`, D12 `_meta`). Data: research t2's (x 1..5, y {10,30,20,50,40}, lo/hi, labelled), `sysuse auto`, a `%td` variable d. Records:
- `accept`: for each of the 40 dash types, rc and first error line of `horizontal`, `vertical`, both orders (E4's model);
- `recast`: every E4 recast row and `kdensity mpg, recast(line) horizontal vertical`;
- `draw`: for the 24 types, upright and horizontal tick-label sets, axis titles (rotated/flat), and for bar, dropline and rcap the mapped geometry (`scripts/svg_truth.py`);
- `dates`, `y2`, `labels`, `titles`, `mixed`: E3's cases, including both mixed orders and `histogram d, horizontal`.

Case ids. HZ-01 `scatter mpg weight, horizontal`; HZ-02 `kdensity mpg, vertical`; HZ-03 `scatter mpg weight, vertical horizontal`; HZ-04 `kdensity mpg, horizontal vertical`; HZ-05 `bar mpg weight, vertical horizontal`; HZ-06 `bar mpg weight, recast(scatter) horizontal`; HZ-07 `kdensity mpg, recast(area) vertical` (rc 0); HZ-08 `lfit mpg weight, recast(bar) horizontal` (rc 0); HZ-09 `lfit mpg weight, recast(scatter) horizontal`; HZ-10 `histogram mpg, recast(line) vertical` (rc 0); HZ-11 `scatter mpg weight, recast(bar) horizontal` (rc 0); HZ-12 `area mpg weight, recast(line) vertical`; HZ-13 `rcap mpg price weight, recast(rscatter) horizontal vertical`; HZ-14 `tsline mpg, horizontal` (after `tsset t`). Drawn: HZ-20 bar, HZ-21 rcap, HZ-22 histogram, HZ-23 kdensity, HZ-24 function, HZ-25 bar on a `%td` x, HZ-26 `(scatter y d) (bar y d, horizontal)`, HZ-27 the reverse order, HZ-28 `(scatter y x) (bar y x, horizontal yaxis(2))`.

Truth cases: HZ-01..HZ-14 in `test/test_option_validation.cscript` (area script, R1: one run at its end, before `display as text "  test_option_validation: ALL CHECKS PASSED"`), each comparing live twoway's rc and first error line with dash's for E4's rows; HZ-20..HZ-28 in S49's block of `test/test_wp30_truth.cscript`, each building a dash page for one drawn case and comparing its axis labels and glyph orientation with twoway's SVG in the same run.

## TDD test stubs

New `test/test_horizontal.py` (helpers `_T` (lazy fixture), `_both(spec)` through `test_mode_parity._standalone/_served`, `_glyphs(fig)`). Red at the base unless marked guard.

- Test: `TestTheTypeSets::test_sets_equal_twoways` — `_DASH_HORIZONTAL_TYPES`, `_DASH_VERTICAL_TYPES` equal the fixture's accept sets and dash.ado's lists. Red: NameError.
- Test: `TestEveryTurnedTypeIsMapped::test_type[<24>]` — every glyph and annotation class the upright layer emits is in `_DASH_TRANSPOSE`. Red.
- Test: `TestHorizontalIsTheTranspose::test_type[<24>-saved|served]` — each renderer's horizontal glyph equals the upright one under the map in all five slots; no VBar/VArea remains. Red: unchanged.
- Test: `TestCapsArePerpendicular::test_rcap[saved|served]` — `dash_cap` renderers have `angle == π/2`. Red.
- Test: `TestAlphaAndStyleAreKept::test_bar_and_rarea[saved|served]` — fill/line alpha, colour, width equal the upright layer's under stcolor and sttrans. Red.
- Test: `TestSwatchesAreSkipped::test_dot_colorvar[saved|served]` — swatch renderers and the colour key are unchanged. Red.
- Test: `TestTheAxesFollowTheLayer::test_titles[<24>-saved|served]`, `::test_mixed_titles[<E3 case>]`, `::test_tick_formats[bar_fc]` (a `%9.0fc` y on a horizontal bar formats the x axis) against the fixture. Red.
- Test: `TestADateLayerTurnsItsAxis::test_case[bar_td|rcap_td|histogram_td-saved|served]` — the y axis is the date axis. Red.
- Test: `TestMixedOrientationWithADate::test_order[scatter_first|bar_first-saved|served]` — E3's axis kinds and labels. Red.
- Test: `TestSecondAxisIsPhysical::test_bar_on_y2[saved|served]` — the horizontal bar's renderers are on `y2`, y2's range spans the bar's x values, y2's default title is the x variable's. Red.
- Test: `TestMarkerLabelsStayPhysical::test_dropline_and_bar[saved|served]` — LabelSet x/y fields swapped, offsets and alignment unchanged. Red.
- Test: `TestByPanels::test_bar_by_foreign[saved|served]` — every panel turned; the shared y range spans the HBar half-heights. Red.
- Test: `TestTheHullSeesTransposedGlyphs::test_python_hull[bar|area]`, `::test_the_saved_plan_carries_bar_heights`, `::test_a_default_base_turns_with_the_bar` (the x axis takes S27's clamp, the y axis none). Red (or a stop: Risk 2).
- Test: `TestTheRefusalRule::test_scan_order` — `_dash_hz_order` on `vert hor`, `horizontal`, `hor(1)`, text with quotes and backticks. Red.
- Test: `TestNotNamed::test_no_note[bar-horizontal|bar-vertical|kdensity-horizontal]` — no "ignoring unsupported" line. Red.
- Test: `TestAnUnmappedGlyphIsNoted::test_a_fake_class` — a layer holding an unknown glyph class draws upright with the one note. Red.
- Guard: `TestUprightIsUntouched::test_every_type[<40>]` — without the flag, the normalised saved page (`normalise_bokeh_html`) equals the page built with `vertical` and the page built under `monkeypatch.setattr(dr, "_dash_transpose_layer", <a function that raises>, raising=False)`, which never raises. Green at the base and after.
- Shared: `test/test_mode_parity.py` CORPUS `_case("horizontal bar, rcap, histogram and pcarrow (WP-30 P1.9a)", [plot_for("bar", {"horizontal": "horizontal"}), plot_for("rcap", {"horizontal": "horizontal"})])` and `_case("horizontal histogram on a date (WP-30 P1.9a)", …)`; `ALLOWED`/`_MUST_WARN` untouched.
- cscript: HZ-01..HZ-14, HZ-20..HZ-28.

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| `_DASH_TRANSPOSE["VBar"]` keeps `width` | `TestHorizontalIsTheTranspose::test_type[bar-saved]` |
| the served loop omits the call | `TestHorizontalIsTheTranspose::test_type[bar-served]` |
| no `dash_cap` rotation | `TestCapsArePerpendicular::test_rcap[saved]` |
| swatches transposed | `TestSwatchesAreSkipped::test_dot_colorvar[saved]` |
| `_dash_role_letter` ignores univariate layers | `TestADateLayerTurnsItsAxis::test_case[histogram_td-saved]` |
| `_axis_kind` keeps the role letter | `TestSecondAxisIsPhysical::test_bar_on_y2[served]` |
| `_dash_hz_check` judges `ptype` only | HZ-07 (`kdensity …, recast(area) vertical`, rc 0) |
| typed order ignored | HZ-03 (`scatter …, vertical horizontal`) |
| the transposition runs without the flag | `TestUprightIsUntouched::test_every_type[bar]` |

### Pinned tests to flip (R9)

E5's list, each with `Flipped (WP-30 P1.9a): <old> was wrong because twoway draws/refuses it (horizontal_truth.json <case>)`: `[horizontal]` asserts HBar at the y values; the spike test asserts `y0 == y1` (horizontal segments); `horizontal` moves to `LIVE_VALUES` (bar: the page differs); `vertical` leaves `PLOT_VALUES` for the silent-accept table if the file has one, else for `test_horizontal.py::TestNotNamed`, with a "Left the parametrisation" line; the pending, declared and help counts re-measured (R10 comment form).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Type sets, scan | `TestTheTypeSets`, `TestTheRefusalRule` | accept | n/a |
| Refusals | cscript HZ-01..HZ-14 vs live twoway | E4 | n/a |
| Transpose, caps, alpha, swatches | `TestHorizontalIsTheTranspose`, `TestCapsArePerpendicular`, `TestAlphaAndStyleAreKept`, `TestSwatchesAreSkipped` | draw | yes |
| Axes, titles, dates, y2, labels | `TestTheAxesFollowTheLayer` … `TestMarkerLabelsStayPhysical`; HZ-20..HZ-28 | draw, dates, mixed, y2 | yes |
| Hull and plan | `TestTheHullSeesTransposedGlyphs`, `TestByPanels` | — | yes |
| Upright identity | `TestUprightIsUntouched` | base digests | saved |
| Parity | CORPUS cases | — | yes |
| Registries, served names | maps, G4 guards | — | served |

**Acceptance criteria.**
- **AC-49.1** (BR-49.1, BR-49.2) every type's transpose test passes in both modes; caps perpendicular; alpha kept; swatches unmoved.
- **AC-49.2** (BR-49.3) titles, formats, date kinds and y2 equal the fixture for every probe; HZ-20..HZ-28 PASS.
- **AC-49.3** (BR-49.4, BR-49.5) HZ-01..HZ-14 PASS; no note names either flag.
- **AC-49.4** (BR-49.6) `TestUprightIsUntouched` passes for all 40 types.
- **AC-49.5** flips recorded, none deleted; the full run green; G7 0 twice.

## Tasks

**Commit boundary.** Tasks 49-01 to 49-13 form the one commit of entry `P1.9a`, made by 49-13 on `wp30-s49` with the subject `Draw horizontal on every type twoway turns and refuse it where twoway does (WP-30 P1.9a)`. `$S`, `$SLOT` as in section 48; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s49`. Cscripts through the driver with `WP30_ONLY=S49`. Confirm `$S/batch-17-impact.txt` records the approval before the first edit of `_make_figure_body`, `_generate_app_source`, `_dash_axis_labels` and `_glyph_layer_lines`.

<task type="auto" id="49-01">
  <name>Write the orientation fixture and tests</name>
  <files>scripts/extract_horizontal_truth.do, test/test_horizontal.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-17-base.txt"` and the branch is `wp30-s49`; stop otherwise. Create the extractor as "Stata truth" describes and run it through the slot. Run a scratch inventory of every glyph and annotation class the 24 upright types emit (both modes) into `$S/49-inventory.txt`. Create every stub of "TDD test stubs", naming new symbols so they fail with AttributeError now; append the two CORPUS cases. Run `python3 -m pytest test/test_horizontal.py -q -n 6 -p no:cacheprovider -rf > "$S/49-new.log" 2>&1`. Write `$S/49-P1.9a-failure.txt` (base sha, failing nodes, then the guards). Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/horizontal_truth.json')); a=d['accept']; print(sum(v['horizontal']['rc']==0 for v in a.values()), a['scatter']['horizontal']['line'])"` prints `24 option horizontal not allowed`; `grep -c FAILED "$S/49-new.log"` is at least 40; the log's summary line reports at least 40 passed (the `TestUprightIsUntouched` guards, listed as guards in the failure text).]]></verify>
  <done>The twoway orientation fixture, the upright digests and the class inventory existed, and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="49-02">
  <name>Write the refusal and truth cases</name>
  <files>test/test_option_validation.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add HZ-01..HZ-14 to the end of `test/test_option_validation.cscript` (one run headed `// HZ: horizontal and vertical refused as twoway refuses them (WP-30 P1.9a)`, before its final PASSED display), each comparing live twoway's rc and first error line with dash's for one E4 row (both orders, the recast rows, the derived rows). Put the `_s49_*` helpers above S01's S49 header and HZ-20..HZ-28 inside S49's block of `test/test_wp30_truth.cscript`. Run both through the driver on the unmodified tree; append the FAIL lines to `$S/49-P1.9a-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "HZ-(0[1-9]|1[0-4]) FAIL" "$S/run_test_option_validation.log"` is at least 9 (the rc-0 rows pass as guards); `grep -cE "HZ-2[0-8] FAIL" "$S/run_test_wp30_truth.log"` is at least 8.]]></verify>
  <done>The refusal and drawing comparisons were in their scripts and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="49-03">
  <name>Refuse the flags in Stata</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Make TR-49.7: delete the pending lines (:1069, :1112 at c96facd) and reword the comment; add `_dash_hz_order` in part 5 of dash_parse.mata directly after `_dash_rep_scan` (TR-49.7) with its header-index entry and `_needed` entry; add `_dash_hz_check` after `_dash_fold_typed`'s `end` with the type lists; call it in `_dash_process_segment` directly after S45's recast call (re-find it: `grep -n "_dash_recast_opt" dash.ado`) and before `_dash_fold_bw`, as a block. Edit no other program. Map both under S49's anchors.
  ]]></action>
  <verify><![CDATA[`test_option_validation.cscript` through the driver prints `HZ-01 PASS` to `HZ-14 PASS` and `test_option_validation: ALL CHECKS PASSED`; `python3 -m pytest test/test_horizontal.py -q -n0 -p no:cacheprovider -k "TestTheRefusalRule or TestTheTypeSets"` passes; `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_file_headers.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash refused horizontal and vertical where and as twoway refuses them, judged after recast(), and stopped naming them.</done>
</task>

<task type="auto" id="49-04">
  <name>Add the constants and role rule</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add TR-49.1's constants after `_DASH_X_COORDS` (with `"x2"` appended to it and a comment naming HArea), filling `_DASH_TRANSPOSE` with every class of `$S/49-inventory.txt`, and TR-49.2/TR-49.3's `_dash_is_horizontal` and `_dash_role_letter` after them. Map both under S49's anchor. Run every test file naming `_DASH_X_COORDS` or `_dash_layer_extent` (grep) with `-n 6`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_horizontal.py -q -n0 -p no:cacheprovider -k "TestEveryTurnedTypeIsMapped"` passes; the grep'd files report 0 failed.]]></verify>
  <done>The type sets, the property map and the one role rule existed, and the hull readers knew HArea's x2.</done>
</task>

<task type="auto" id="49-05">
  <name>Write the transposition helper</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_transpose_layer` after `_dash_role_letter` (TR-49.4), with a docstring citing E3 and D-49a; re-find S21's and S27's property-name stamps at the base (`grep -n "_dash_auto_base" dash_render.py`) and re-map each through the pairs. Use S06's note helper by name for the unmapped case. Map it under S49's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_horizontal.py -q -n0 -p no:cacheprovider -k "AnUnmappedGlyph"` passes.]]></verify>
  <done>One helper turned a layer's glyphs and annotations by a fixed map, rotating caps and keeping styles, stamps and swatches right.</done>
</task>

<task type="auto" id="49-06">
  <name>Turn layers in both build loops</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_make_figure_body` is CRITICAL and `_generate_app_source` and `_glyph_layer_lines` HIGH. Make TR-49.5 (saved and served) and TR-49.8 (copy list). Touch no other line of either method. Run test_glyphs.py, test_bar_range_geometry.py, test_range_plots.py, test_pccapsym_pcarrowi.py, test_mode_parity.py and the G4 guards with `-n 6`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_horizontal.py -q -n 6 -p no:cacheprovider -k "Transpose or Caps or Alpha or Swatches or UprightIsUntouched"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Both modes drew every horizontal layer turned and every upright page unchanged.</done>
</task>

<task type="auto" id="49-07">
  <name>Read axis variables through orientation</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-49.6's date and variable readers: S35's `_dash_layer_axis_names`, `_dash_axis_vars`, `_dash_figure_date_kind` (only if S35 does not route it through `_dash_layer_axis_names`), `GlyphMapper._axis_kind` and S35's pass letter map, and `_compute_secondary_range`, one `_dash_role_letter` call each. Update the docstring at :797 that says horizontal is not read.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_horizontal.py -q -n 6 -p no:cacheprovider -k "DateLayer or MixedOrientation or SecondAxis or ByPanels or Hull"` passes (or 49-07 stops per Risk 2 and reports); `python3 -m pytest test/test_date_axis_residuals.py test/test_dual_axis.py test/test_default_axes.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Date kinds, axis variables, unit conversions and second-axis ranges followed each layer's orientation in both modes.</done>
</task>

<task type="auto" id="49-08">
  <name>Swap titles and tick formats</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_dash_axis_labels` is HIGH. Make TR-49.6's title and format readers: S19's `_dash_axis_default_titles` and its y2/x2 own-layer read, the univariate defaults (in `_dash_axis_labels` or S19's helper, wherever they live at the base), and S18's `_dash_axis_tick_formats`, one role-letter read each. Change no rule.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_horizontal.py -q -n 6 -p no:cacheprovider -k "AxesFollowTheLayer or MarkerLabels"` passes; `python3 -m pytest test/test_series_labels.py test/test_axis_format_fallback.py -q -n 6 -p no:cacheprovider` reports 0 failed (S19's and S18's files; use their names at the base).]]></verify>
  <done>Default titles and tick formats followed orientation, reproducing twoway's eight measured title cases.</done>
</task>

<task type="auto" id="49-09">
  <name>Fill the truth block and parity</name>
  <files>test/test_wp30_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    Run the S49 truth block through the driver; correct only the test-side reading of a case if it misread a passing page, never an expectation from the fixture. Extend `test/test_mode_parity.py`'s `_annotations`/glyph profile to HBar, HArea and the Arrow/LabelSet swapped fields if it does not profile them, so the CORPUS cases compare turned glyphs.
  ]]></action>
  <verify><![CDATA[`grep -cE "HZ-2[0-8] PASS" "$S/run_test_wp30_truth.log"` prints 9; `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The truth block and the parity corpus confirmed both modes against twoway.</done>
</task>

<task type="auto" id="49-10">
  <name>Flip the drawing pins</name>
  <files>test/test_help_claims_8.py, test/test_unsupported_report_is_true.py, test/test_help_conformance.py</files>
  <action><![CDATA[
    Re-measure E5's pytest pins and flip them in place with the reasons of "Pinned tests to flip", moving the two rows, and writing each count with `# <old> -> <new>: P1.9a horizontal drawn, vertical silent` (R10). Write `Flipped:` and "Left the parametrisation" lines to `$S/49-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_unsupported_report_is_true.py test/test_help_conformance.py -q -n 6 -p no:cacheprovider` reports 0 failed except the Unsupported-prose checks 49-12 fixes.]]></verify>
  <done>Every pytest pin of upright drawing or of the named flags asserted the turned drawing, with reasons.</done>
</task>

<task type="auto" id="49-11">
  <name>Flip the script pins</name>
  <files>test/test_help_claims_8.cscript, test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[
    Re-measure: in HC8-02 and TP-06/TP-13a, move `horizontal` to the honoured rows (rc equal to twoway's, not named) and `vertical` to the silent rows, with comment counts; leave HC8-03's twoway side. Append the `Flipped:` lines to `$S/49-flips.txt`.
  ]]></action>
  <verify><![CDATA[Both scripts through the driver end with their ALL CHECKS PASSED line.]]></verify>
  <done>The scripts asserted horizontal drawn and vertical silent.</done>
</task>

<task type="auto" id="49-12">
  <name>Document orientation in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Make TR-49.10 in "Plot types" and the Unsupported section, found by text. Lines at most 79 characters; no tool or vendor name; keep other sections' sentences.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py test/test_help_plot_types.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "draws every plot upright" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help documented horizontal on its 24 types, the refusals, and that labels and second axes stay physical.</done>
</task>

<task type="auto" id="49-13">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Title `WP30_OPEN["P1.9a"]` ("horizontal is not drawn on any plot type, and vertical is named as unsupported"): close in place with "Notes: BUGS.md Resolution"; delete only its `WP30_OPEN` line; replace both `<!-- WP-30 P1.9a -->` markers with "Notes: CHANGELOG lines". Run test_tracking_documents.py, test_horizontal.py, the maps, test_fixtures_are_committed.py, test_cscript_hygiene.py and both scripts. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/49-full-1.log"`, read on `exit=`. Stage exactly the files of `$S/49-files.txt` plus these three, `git add -f test/fixtures/horizontal_truth.json`; G6, G7, branch check, commit, G7.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/49-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.9a -->' "$WT/CHANGELOG.md"` prints 0; `python3 -c "import sys; sys.path.insert(0, '$WT/test'); import test_tracking_documents as t; print('P1.9a' in t.WP30_OPEN)"` prints `False`; the subject ends `(WP-30 P1.9a)`; G7 prints 0.]]></verify>
  <done>Entry P1.9a was closed naming existing tests, its markers replaced, and one green commit on wp30-s49 was ready for the merger.</done>
</task>

## Section completion criteria

- The 24 types draw turned in both modes, at build, with caps, alpha, labels, swatches, `yaxis(2)`, dates, titles and formats as twoway's; upright pages unchanged.
- E4's refusals reproduced in twoway's words and order, judged after `recast()`; `vertical` silent; neither flag named.
- Helpers mapped and copied; fixture committed; flips recorded; one green commit `(WP-30 P1.9a)`.

## Notes

- **Stop rule (Risk 2).** If `TestTheHullSeesTransposedGlyphs::test_the_saved_plan_carries_bar_heights` or `::test_a_default_base_turns_with_the_bar` is red after 49-07 because S21's `_dash_axis_plan` or S27's `_dash_finish_auto_bases` hard-codes the upright letter, S49 stops and reports: the fix belongs to the batch's finisher editor (R11), and the orchestrator decides (an amendment to S50 or S52).
- **S45's names.** The recast step, its canonical target local and the draw-as helper are re-read at the base; use S45's names.
- **python_exec hazard.** Check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Shared lines with S48 (conflicts in context only; the merger keeps both).** dash.ado's `local _needed` statement (237) gains S48's two names and S49's one; dash_parse.mata's header index gains entries from both; `test/test_mode_parity.py` gains CORPUS cases from all three sections, and S49 and S50 may each add a branch to `_annotations` (S49 HBar/HArea, S50 Arrow): keep every branch.
- **Merge rules.** R1: HZ-01..HZ-14 at the end of `test_option_validation.cscript`; S49's truth block. R2: S49's anchor after `"_dash_add_pc_glyph", "_dash_note_no_second_y",`. R3: "Plot types" and the Unsupported entry. R4/R5: the two `P1.9a` markers, the entry, the key. R6: one program after `_dash_fold_typed`, `version 19`, one Mata function. R7: one fixture and extractor. R8: two CORPUS cases. R9: E5. R10: the pending, declared and help counts, re-measured. R12: S49 is batch 17's `_make_figure_body` and `_generate_app_source` editor.
- **Landing (merger).** detect-changes names `_dash_is_horizontal`, `_dash_role_letter`, `_dash_transpose_layer`, `DashRenderer._make_figure_body`, `ServerAppBuilder._generate_app_source`, `_glyph_layer_lines`, `_dash_layer_axis_names`, `_dash_axis_vars`, `GlyphMapper._axis_kind`, `_compute_secondary_range`, `_dash_axis_default_titles` and/or `_dash_axis_labels`, `_dash_axis_tick_formats` and test symbols.
- **Commit message.** Body: `$S/49-P1.9a-failure.txt`; Overview's measured block; TR-49.1-TR-49.11 in both modes; `Regression: test/test_horizontal.py::<Class>::<test> -- failed at <base sha> with <text>` per node (`test/test_option_validation.cscript HZ-01`, `test/test_wp30_truth.cscript HZ-20`); the `Flipped:` lines; `Fixture: test/fixtures/horizontal_truth.json (scripts/extract_horizontal_truth.do)`; `BUGS.md: "horizontal is not drawn on any plot type, and vertical is named as unsupported" (closed)`.
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.9a). horizontal draws the exact transpose of the upright layer on the 24 types twoway turns (area, bar, spike, dropline, dot, histogram, kdensity, rarea, rbar, rspike, rcap, rcapsym, rline, rconnected, rscatter, the pc family, pci, pcarrowi, function and tsrline) through one helper in both build loops (_dash_transpose_layer with _DASH_TRANSPOSE, called from DashRenderer._make_figure_body and the served layer loop), rcap caps perpendicular, alpha and styles kept, swatches unmoved, marker-label offsets and yaxis(2) physical; axis variables, date kinds, tick formats, default titles and second-axis ranges are read through each layer's orientation (_dash_role_letter in _dash_layer_axis_names, _dash_axis_vars, GlyphMapper._axis_kind, _dash_axis_default_titles, _dash_axis_tick_formats, _compute_secondary_range); dash.ado refuses horizontal and vertical where twoway does, judged after recast() (_dash_hz_check with Mata _dash_hz_order), refuses both together, accepts vertical silently and names neither. Pinned by test/test_horizontal.py::TestHorizontalIsTheTranspose::test_type, test/test_horizontal.py::TestTheAxesFollowTheLayer::test_titles, test/test_horizontal.py::TestMixedOrientationWithADate::test_order, test/test_horizontal.py::TestUprightIsUntouched::test_every_type, test/test_option_validation.cscript HZ-01, test/test_wp30_truth.cscript HZ-20; fixture test/fixtures/horizontal_truth.json. Residual, deferred (WP-30): hover rows, the hover line and the move-time parity of turned layers are P1.9b (section 55); dot's own geometry is P2.9.
  ```
- **CHANGELOG lines:**

  ```
  ### Results that change
  - `horizontal` is drawn on bar, rbar, spike, rspike, rcap, rcapsym, dropline, dot, area, rarea, histogram, kdensity, function, rline, rconnected, rscatter, tsrline, the pc types, pci and pcarrowi, as twoway draws it: `dash bar mpg rep78, horizontal` drew upright bars and named the option, and now draws bars along the y axis with the axes, default titles, date labels and second axes swapped, rcap caps across the spine and marker labels where twoway puts them; `vertical` is no longer named. (WP-30, P1.9a)

  ### Changed behaviour (may need your do-files changed)
  - `horizontal` and `vertical` are refused where twoway refuses them, in its words (both were accepted with a note): `horizontal vertical` together (`may not combine options horizontal and vertical`, r(198)); `horizontal` on scatter, line, connected, the fits and smoothers, scatteri and tsline, and `vertical` on those and on kdensity and function (`option horizontal not allowed`, r(198)), judged after `recast()` as twoway judges it. (WP-30, P1.9a)
  ```
- **Notes for the closeout (S58; A145).** GAPS2.md A7/B12 (:100, :230, :476-486): the drawing part closed by `<sha>`, B12-a partly open until S55; REMAINING.md:124-126 and :305; TWOWAY_COVERAGE_AUDIT.md:24, :63, :97, :115, :169 (AUDIT-15); WP-29 section-04/section-05 notes on horizontal; DROPIN-REMAINING.md:99; `test/fixtures/rejected_options.json:1130-1200` (stale `dash_rc` 198 for horizontal). AGENTS.md invariant: "a horizontal layer is drawn upright by its mapper and turned once by `_dash_transpose_layer`; every axis-variable reader goes through `_dash_role_letter`." Unverified: Stata 14-18.5 (M2).
