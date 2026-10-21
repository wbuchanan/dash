# Section 47-01: headlabel and immediate-type labels

> Part of: WP-47 (Plot-option fidelity, P15) · Items: basic:PT-1, MS-7 · Risk: yellow · Batch: 47.1 · Depends on: none · Blocks: 47-02, 47-04 · Tasks: 5, 2 commits · Case-id prefix: Q4701

## Overview

**What is wrong today.** Two label defects on the paired-coordinate and immediate types (audit package 15, appendix "type-options-basic" PT-1/PT-2 and "series-lists-merges" MS-6..MS-9):

- **basic:PT-1 (with basic:PT-2, MS-6).** `headlabel` is ignored on `pcscatter` and `pccapsym` with `mlabel()`, and on `pcarrowi`'s immediate labels: "labels stay at the first point". twoway moves every label to the second point (y2, x2): measured, "'AMC Concord' moves from (3952,718) to (678,2559)" on pcscatter, and `pcarrowi 20 2000 30 4000 "A", headlabel` moves 'A' "from (641,2727) to (5263,216)". dash draws them at (x1, y1) with no note: `map_pcscatter` fills `__dash_mlabel_x/y` from x1/y1 only, `map_pccapsym` passes `x1var, y1var`, `map_pcarrowi` always passes x1/y1 to `_immediate_labels`. Only `map_pcarrow` and `map_pcbarrow` read `headlabel`. The silence comes from `_dash_tw_silent_tab`'s `headlabel` row, generated from `extract_noted_option_truth.do`, "whose base command for pc types has no mlabel()". The help is false in two places (Appendix B HR-14): dash.sthlp:3472-3475 says headlabel moves pcarrowi's labels and that dash names it on pcscatter/pccapsym, and :332 says headlabel, mangle() and barbsize() are named in the note on the other plot types, where dash refuses headlabel off the pc types, rpcap and rpspike (as twoway does) and takes the other two in silence.
- **MS-7 (with MS-8, MS-9).** Immediate-type labels: `pci ... "A" ..., recast(pccapsym|pcarrow|pcscatter)` draws no labels and prints the false note "pci draws no labels, as twoway pci draws none" (twoway draws them at the first points under those recasts); `scatteri 20 3000 "A" 25 4000 "B", recast(connected|dropline)` draws no labels because `map_scatteri` returns from the recast branch before `_immediate_labels` (twoway draws A and B; recast(line) draws none); `scatteri 20 3000, mlabel(nosuch)` is refused r(111) "dash: mlabel(): variable nosuch not found" where twoway draws (rc 0).

**After this section.** headlabel moves the labels to (x2, y2) on pcscatter, pccapsym and pcarrowi, in both modes and after a filter move; it is taken in silence wherever twoway draws nothing different. pci labels are drawn under a recast() to a type that has marker labels and the false note is gone; scatteri labels are drawn after a recast() whose target has marker labels; mlabel() on scatteri, pci and pcarrowi is not checked against the dataset. The help paragraph is rewritten to the measured behaviour.

**Why together.** Both items live in the same five mappers (`map_pcscatter`, `map_pccapsym`, `map_pcarrowi`, `map_pci_literal`, `map_scatteri`) and the one label applier `_immediate_labels`; 47-02 (batch 47.2) edits label text in the same layers and so follows this section.

**Test order and commit rule.** 47-01-01 measures twoway and writes basic:PT-1's failing tests (no commit). 47-01-02 fixes basic:PT-1 and commits `(WP-47 basic:PT-1)`. 47-01-03 writes MS-7's failing tests (saved failure, no commit), 47-01-04 fixes and commits `(WP-47 MS-7)`. 47-01-05 checks the regenerated silent table against the measurement (no maintainer approval: D-47-01.b, the measurement decides). No full suite inside the section.

### Section decisions

- **D-47-01.a — headlabel with no mlabel() stays silent.** twoway draws nothing different for `headlabel` on pcscatter/pccapsym without `mlabel()` (the current fixture row) and on pcspike/pci/rpcap/rpspike (verifier: "P28/P29 normalised diff 0"). After the fix headlabel is drawn where twoway draws it and silent elsewhere; it is never named. The `_hl_named` loop (dash.ado:2865-2871) therefore drops `headlabel` from the named list for pcscatter and pccapsym (they draw it) and keeps `mangle barbsize` in the loop as today: the generated `mangle` and `barbsize` rows of `_dash_tw_silent_tab` (dash_parse.mata:8245, :8253) cover every non-arrow type, so `_dash_silent_drop` takes both in silence there, as twoway draws nothing different with them.
- **D-47-01.b — the silent table is regenerated, never hand-edited; this section is batch 47.1's only editor of it.** `extract_noted_option_truth.do` gains `headlabel` probes WITH `mlabel()` on the pc types (and with labels on pcarrowi/pci), stored under the key `headlabel+mlabel`; `scripts/gen_twoway_takes_table.py`'s `silent_rows` folds a `<name>+<context>` key into `<name>`'s row (`name = opt.split("(", 1)[0].split("+", 1)[0]`), so an option is silent on a type only when every probe set of that name that holds the type draws twoway's plain picture there (the generator already intersects the probes of one name, e.g. `sort` and `sort(price)`); a type a probe set does not hold keeps the other probes' verdict, because the `headlabel+mlabel` set holds the pc and immediate types only and `silent_rows` would otherwise raise KeyError on `scatter` (REVIEW-5 R5-14). Without the fold the new key is a pseudo-option outside `SILENT` and the headlabel row never moves. The generator then regenerates the `tw_silent` block between its BEGIN/END markers. Where the regenerated row and the drawn behaviour disagree the measurement wins and the deviation is recorded in the commit body. In batch 47.1 this section alone edits `scripts/extract_noted_option_truth.do`, `test/fixtures/noted_option_truth.json`, `scripts/gen_twoway_takes_table.py` and the generated `tw_silent` block (REVIEW-5 R5-4); 47-03, beside it, makes dlalign() silent by taking it off dash's pending list instead and touches none of them.
- **D-47-01.c — pci under recast().** Labels are passed to `_immediate_labels` at (x1, y1) when the recast target is `pccapsym`, `pcarrow`, `pcbarrow` or `pcscatter` (the pc types that draw marker labels), at (x2, y2) when `headlabel` is also given and the target is one of those four; never for `pcspike` (plain pci = immediate pcspike draws none). The dash.ado note at :6229-6231 is deleted outright: with recast it is false, and for plain pci twoway is silent (index rule "silent when honoured" -- the picture now matches twoway's).
- **D-47-01.d — scatteri under recast().** The labels are drawn after `_dash_draw_xy_as` when the recast target is one of `scatter connected dropline dot bar spike` -- the yxview types twoway draws marker labels on -- measured per target in 47-01-01 (probe list below); a target twoway draws none on (`line`, `area`, measured) draws none. The measured list wins.
- **D-47-01.e — mlabel() on the immediate types.** `scatteri`, `pci` and `pcarrowi` join `_dash_fold_mlab`'s unread list (`mlab_unread`, dash.ado:2227) only for the dataset check: the value is still validated for `..`/`...`/`=` exactly as twoway refuses them there (measured in 47-01-01: `scatteri 1 1, mlabel(..)`, `mlabel(=)`); what twoway draws for `mlabel(make)` on scatteri (G05 "matches") stays as today.

## Risk: [yellow] -- five mappers shared by both modes, and a generated silence table

**Why.** The mappers are copied whole into the served app (GlyphMapper), so one change reaches both modes; but the pcscatter labels ride the markers' own source with NaN second-point positions, and a filter move refreshes them through that source.

**Risk factors.** 1. pcscatter's label columns (`__dash_mlabel_x/y`) are built once and masked by row id on a move; swapping x1 for x2 must keep the NaN half. 2. `_dash_tw_silent_tab` is generated: a hand edit is overwritten by the next `make truth`. 3. test_mode_parity's `pcarrowi headlabel with labels` entry compares modes only; it does not catch a wrong position. 4. scatteri recast to `dropline`/`connected` draws through `_dash_draw_xy_as`, whose renderer source columns are `x`/`y`; labels must use the literal arrays, not the renderer's source.

**Mitigation.** 1. Regression tests read the label columns after a saved filter move (node `run_filter_js_block`) and a served move. 2. D-47-01.b. 3. New regression tests compare positions with the measured SVG coordinates mapped to data units. 4. The labels take `x_vals`/`y_vals` already computed in `map_scatteri`.

## Dependencies

- **Depends on:** none inside WP-47 (35-01 repeated options, 43-04 legend keys and 46-01/46-02 recast orientation landed in earlier WPs).
- **Blocks:** 47-02 (label text on the same layers) and 47-04 (batch 47.3, which regenerates the tables with this section's generator rules: the context-key fold and the missing-type rule of TR-47-01.9; index manifest).
- **Parallel batch 47.1** with 47-03. 47-03 edits outline/stroke code (`_apply_line_opts` lalign block, `_apply_marker_opts` mlalign block, the bar/area/rbar/rarea/rcap mappers, `_dot_style`, dash.ado's dlalign pending line); 47-01 edits only the five label mappers, `_dash_fold_mlab`, the `_hl_named` loop, the pci note and -- alone in the batch -- the noted-option extract, its fixture, the generator and the `tw_silent` block (D-47-01.b). No shared hot function (R12); neither edits saved-page JavaScript.

## Evidence

Anchors at `090d928`; re-read before editing.

### Mappers (dash_render.py)

- `map_pcscatter` :24940. Labels at the first point only, :25019-25041:
  ```
  # The label goes at the FIRST point only -- twoway: "By default, the
  # labels are placed at ... the point defined by y1var and x1var"
  ...
      _pc_cols[_DASH_MLABEL_X] = np.concatenate(
          [_dash_float_values(clean[x1var]), _nan])
      _pc_cols[_DASH_MLABEL_Y] = np.concatenate(
          [_dash_float_values(clean[y1var]), _nan])
  ```
  `_apply_mlabel_opts(fig, pc_source, options, _DASH_MLABEL_X, _DASH_MLABEL_Y, ...)` :25075-25079.
- `map_pccapsym` :25573; `self._apply_mlabel_opts(fig, seg_src, options, x1var, y1var, ...)` :25692-25693.
- `map_pcarrow` :25357 and `map_pcbarrow` :25469 are the model: `_at_head = bool(str(options.get("headlabel", "") or "").strip())` then `x2var if _at_head else x1var` (:25461-25466, :25565-25570).
- `map_pcarrowi` :25834; labels at the tail, :25877-25885 (`[x1[i] if drawn[i] else nan ...]`, `"x1", "y1"`). Docstring :25844-25848 says "Each label is drawn at its arrow's tail".
- `map_pci_literal` :24873; `_labels` read and dropped; recast through `_pc_recast` :24921-24924; docstring :24900-24903 "No label is drawn".
- `map_scatteri` :24655; recast returns at :24764-24767 before the labels at :24795-24799.
- `_immediate_labels` :25766 (the one applier; takes `xcol`, `ycol`).

### dash.ado

- `_dash_fold_mlab` :2218; `local mlab_unread "histogram function"` :2227 (the r(111) for scatteri comes from the generic value rules that run when the type is not in this list: `_dash_mlabel_list` :4604 -> `_dash_validate_value ... "var"`).
- `_hl_named "mangle barbsize headlabel"` :2865, loop :2866-2871 (`arrow_types "pcarrow pcbarrow pcarrowi"` :2785).
- pci note :6225-6231 (`if "\`ptype'" == "pci" & \`_pci_nlab' > 0 { mata: _dash_note("dash: pci draws no labels, ...") }`).

### dash_parse.mata

- `_dash_tw_silent_tab` :8234, generated block :8238-8260; the `headlabel` row :8250 `"rpcap rpspike pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi"`. `_dash_silent_drop` :8264.

### twoway's rule

`twoway_pcscatter.sthlp`/`twoway_pccapsym.sthlp` (`gr_headlabopt`): headlabel "specifies that labels be drawn at the (y2var,x2var) point"; `twoway_pci.sthlp` points to pccapsym's marker options under recast; `twoway_scatteri.sthlp`: the labels are `mlabel()` of the point list.

### Measured truth (audit)

basic:PT-1 probes P26/P27 (pcscatter/pccapsym), P30 (pcarrowi); MS-6 C08/E24 (pcarrowi, recast(pcbarrow)); MS-7 C07/C13/E15; MS-8 C05/C06/E18; MS-9 C15/E16 (all in the audit's scratch, not committed). This section commits its own truth (Stata truth below).

### Fixtures on disk

`test/fixtures/noted_option_truth.json` (probes `headlabel` without mlabel), `arrowhead_truth.json` (headlabel on pcarrow/pcbarrow), `varlabel_mlabel_truth.json`.

### Pinned tests (flip, never delete)

- `test/test_parser.cscript:1108-1112` (P1A-65c) asserts the pci note `dash: pci draws no labels, ...` -- flipped in 47-01-04 to assert the note is absent (`r(found) == 0`), same case id.
- `test/test_pccapsym_pcarrowi.py` module docstring :12 and `TestMapPcarrowi` (:214) tests that place labels at x1/y1 -- re-read; any asserting the tail under `headlabel` is flipped.
- `test/test_unknown_options.py:112` and :146 read the `headlabel` row of the silent table (`assert "pcspike" in rows["headlabel"].split()` stays true; re-run after regeneration).
- `test/test_marker_label_parity.py:35` docstring table ("pcarrow pcbarrow (headlabel: at (y2, x2)) the other three none") -- update the table text in the fix commit.

## User stories

- US-47-01.1 As a Stata user with an existing twoway command, I want `pcscatter ..., mlabel(make) headlabel` to label the second points so that my paired plot reads as twoway's.
- US-47-01.2 As a Stata user, I want `pcarrowi ... "A", headlabel` to put A at the arrow's head so that annotated arrows point where I drew them.
- US-47-01.3 As a Stata user, I want the labels of `pci` and `scatteri` drawn after `recast()` as twoway draws them so that changing the drawing type does not lose my text.
- US-47-01.4 As a Stata user, I want `scatteri ..., mlabel(nosuch)` to draw as twoway does so that a pasted command is not refused.

## Business requirements

- BR-47-01.1 With `headlabel`, the marker labels of pcscatter, pccapsym and pcarrowi sit at (x2, y2), in the saved page, the served app and after a filter move.
- BR-47-01.2 headlabel never produces a note on any type twoway takes it on.
- BR-47-01.3 pci labels appear under recast() to pccapsym, pcarrow, pcbarrow and pcscatter, at the first point (or the second under headlabel); no "pci draws no labels" note is printed in any case.
- BR-47-01.4 scatteri labels appear after recast() exactly for the targets twoway labels (the measured list).
- BR-47-01.5 mlabel() of a name that is not a variable is accepted on scatteri, pci and pcarrowi, drawing what twoway draws.

## Technical requirements

- TR-47-01.1 `map_pcscatter`: compute `_at_head = bool(str(options.get("headlabel", "") or "").strip())` before :25026; fill `_DASH_MLABEL_X/_Y` from `clean[x2var]`/`clean[y2var]` when `_at_head`, else x1/y1 as today; the NaN half and the value columns are unchanged. Update the comment block :25019-25025 to cite twoway_pcscatter.sthlp's headlabel and the measured move.
- TR-47-01.2 `map_pccapsym`: same `_at_head`; `self._apply_mlabel_opts(fig, seg_src, options, x2var if _at_head else x1var, y2var if _at_head else y1var, ...)`. Confirm `seg_src` carries the x2/y2 columns under those names (it is the segment source built from the four variables); if it carries them under other names, use those names.
- TR-47-01.3 `map_pcarrowi`: `_at_head` as above; label positions `x2[i]`/`y2[i]` and column names `"x2", "y2"` when `_at_head`; docstring sentence rewritten: "Each label is drawn at its arrow's tail, (x1, y1), or at its head, (x2, y2), under headlabel, as twoway places it."
- TR-47-01.4 `map_pci_literal`: keep `_clocks` filtered with `_keep` (today only `_labels` is); after `_draw(...)`, when `options.get("recast")` is one of `("pccapsym", "pcarrow", "pcbarrow", "pcscatter")` and `any(_labels)`, call `self._immediate_labels(fig, xs, ys, _labels, _clocks, options, "pci", "x1", "y1", radius_px=self._mlabel_radius_px(options, self.scheme.default_marker_size(color_idx)), color_idx=color_idx)` with xs/ys the tail (or head under headlabel), NaN where the segment is not drawn -- the exact pattern of `map_pcarrowi` :25876-25885. Rewrite the docstring's "No label is drawn" sentence. The return value is unchanged (`_draw(...)`'s result).
- TR-47-01.5 `map_scatteri`: in the recast branch (:24764-24767) keep the renderer `rr = self._dash_draw_xy_as(...)`; then, when `any(_labels)` and `options["recast"]` is in the module constant `_DASH_SCATTERI_LABEL_RECASTS` (new, a `frozenset` of the targets 47-01-01 measured as labelled; expected `{"scatter", "connected", "dropline"}` plus whichever of `dot bar spike` twoway labels), call `self._immediate_labels(fig, x_vals.tolist(), y_vals.tolist(), _labels, _clocks, options, "scatteri", radius_px=..., color_idx=color_idx)` and return `[rr]`. R2: append `"_DASH_SCATTERI_LABEL_RECASTS"` to the served constants copy tuple after the last `_DASH_*` constant name present at the section's base (re-read the tuple near dash_render.py:67000 where `"_DASH_MLABEL_VALUES", "_DASH_MLABEL_X"` sit; append, never reorder).
- TR-47-01.6 dash.ado: (a) `_dash_fold_mlab` :2227: a new `local mlab_imm "scatteri pci pcarrowi"`; for those types run the same `..`/`...`/`=` loop as `mlab_unread` (with `=` refused as twoway refuses it there, measured), then `exit` keeping `s(mlabel)` as typed (no dataset check). (b) :2865 loop: when `ptype` is `pcscatter` or `pccapsym`, `headlabel` is skipped (`if "\`o'" == "headlabel" & inlist("\`ptype'", "pcscatter", "pccapsym") continue`), with a comment `// WP-47 basic:PT-1: headlabel is drawn on pcscatter and pccapsym (map_pcscatter, map_pccapsym)`. (c) delete the pci note block :6225-6231 (comment and `if` block) and write in its place `// WP-47 MS-7: pci's labels are drawn under recast() to a labelled pc type (map_pci_literal) and, like twoway pci, not otherwise; nothing is printed.`
- TR-47-01.7 No new program or function: no program_coverage_map.py / function_test_map.py rows; the new constant needs the copy-list entry only.
- TR-47-01.8 Saved page: the label sources are static columns masked by row id on a move (no `_FILTER_JS` change). 47-01-01 proves it with a node run of the pcscatter label source after a move; if the saved JS rebuilds `__dash_mlabel_x` from x1, STOP and report (47-01 is not a JS section; R12).
- TR-47-01.9 `scripts/gen_twoway_takes_table.py` `silent_rows` (:118): `name = opt.split("(", 1)[0].split("+", 1)[0]`, and the per-probe set becomes `same = {t for t in types if t not in rows or (rows[t]["twoway_rc"] == 0 and rows[t]["twoway_draws"] is False)}` -- a type a probe set does not hold keeps the other probes' verdict (D-47-01.b); every plain probe holds all forty-four types, so a type enters a row only through a probe that measured it. `refused_rows` and `rows` are unchanged (a context key never names a declared option, so `refused_rows` never reads it). The module docstring's tw_silent paragraph gains: "A probe key `<name>+<context>` (a second base command, e.g. `headlabel+mlabel`) counts as a probe of `<name>`; a type such a probe does not hold keeps the other probes' verdict." test/test_unknown_options.py `TestTheSilentTableIsTheNotedFixture::test_each_row_is_where_twoway_draws_the_same` derives the name the same way (so the context probes are checked too) and reads each type with `by.get(t)`, skipping a type the probe does not hold (`if by.get(t) is None: continue`) before its two asserts. The `--check` path calls the same `silent_rows`, so it raises nothing either.

## Boundaries

- Do not touch `_apply_mlabel_opts`, label text, value labels or formats (47-02), outline or stroke code (47-03), the legend key shapes (43-04), recast orientation (46-01).
- Do not edit `_FILTER_JS`, `_DASH_AXIS_FINISH_JS` (no JS in 47-01).
- Do not hand-edit the `tw_silent` block; regenerate it (D-47-01.b).
- The pci trailing-values notes (dash.ado :6219-6224) are 47-06's (basic:PT-15); leave them.

## Stata truth

Extend `scripts/extract_noted_option_truth.do` (the WP-32 generator; R7):
- In the per-type base commands (:93-107) nothing changes; add a second probe set after the `probes` loop, `local probes_lab`, run only on the pc and immediate types with labels in the base: pcscatter/pccapsym/pcspike/pcarrow/pcbarrow `"<t> mpg weight trunk turn in 1/5, mlabel(make)"`, pcarrowi/pci `"<t> 20 2000 30 4000 \"A\" 25 3000 35 4000 (9) \"B\","`, rpcap/rpspike `"<t> yl yh mpg weight in 1/5, mlabel(make)"`; each with `headlabel` (o vs b SVG as the script already does). Store under `probes["headlabel+mlabel"]` with the same row shape (the generator folds the key into `headlabel`'s row, TR-47-01.9). This section is the only one in batch 47.1 that re-runs this script and regenerates the table (D-47-01.b).
- New `scripts/extract_immediate_label_truth.do` -> `test/fixtures/immediate_label_truth.json` (skeleton: extract_noted_option_truth.do's header, root check, `git rev-parse` through `shell` into a file, `_meta`). Probes (sysuse auto; each `capture noisily twoway ...`, rc, first error line, and from the SVG through `scripts/svg_truth.py` `svg_texts` every text element with its x/y; and a data-unit mapping from `fit_axis_mapping`):
  - H01 `pcscatter mpg weight trunk turn in 1/5, mlabel(make)`; H02 = H01 + `headlabel`; H03/H04 the same on pccapsym; H05 `pcarrowi 20 2000 30 4000 "A" 25 3000 35 4000 (9) "B"`; H06 = H05 + `headlabel`; H07 = H05 + `recast(pcbarrow) headlabel`.
  - R01-R04 `pci 20 2000 30 4000 "A" 25 3000 35 4000 (9) "B", recast(<t>)` for t in pccapsym pcarrow pcbarrow pcscatter; R05 = R01 + `headlabel`; R06 plain pci (no labels drawn).
  - S01-S08 `scatteri 20 3000 "A" 25 4000 "B", recast(<t>)` for t in scatter line connected area bar spike dropline dot.
  - M01 `scatteri 20 3000, mlabel(nosuch)`; M02 `scatteri 20 3000 "A" 25 4000 "B", mlabel(nosuch)`; M03 `pci 20 2000 30 4000, mlabel(nosuch)`; M04 `pcarrowi 20 2000 30 4000, mlabel(nosuch)`; M05 `scatteri 20 3000, mlabel(..)`; M06 `scatteri 20 3000, mlabel(=)`; M07 `scatteri 20 3000, mlabel(make)`.
- Run: `DASH_REPO=<wt> sh <wt>/scripts/stata_slot.sh <scratch> <wt>/scripts/extract_immediate_label_truth.do`, then the same for extract_noted_option_truth.do; `python3 scripts/gen_twoway_takes_table.py` (re-read its usage line) regenerates the `tw_silent` block. `git add -f` both fixtures; add `immediate_label_truth.json` to test/test_fixtures_are_committed.py's named list.

## TDD test stubs

New `test/test_pc_immediate_labels.py` (both modes through the existing `_render`/`render_models` helpers of test/test_pccapsym_pcarrowi.py; `_MODES = ("saved", "served")`):
- Test: pcscatter headlabel labels at (x2, y2) -- `TestHeadlabel::test_pcscatter_labels_the_second_point[mode]` (red).
- Test: pccapsym headlabel -- `TestHeadlabel::test_pccapsym_labels_the_second_point[mode]` (red).
- Test: pcarrowi headlabel at the head, and with recast(pcbarrow) -- `TestHeadlabel::test_pcarrowi_labels_the_head[mode]`, `::test_pcarrowi_recast_pcbarrow[mode]` (red).
- Test: label positions equal H02/H04/H06's SVG positions mapped to data units within 1% of the axis span -- `TestHeadlabel::test_positions_match_twoway[case]` (red).
- Test: after a saved filter move (node, `js_runner.run_filter_js_block`) the pcscatter label columns stay at x2/y2 for the kept rows -- `TestHeadlabel::test_saved_move_keeps_the_head` (red).
- Test: no note names headlabel on any pc type -- `TestHeadlabel::test_silent[ptype]` (red on pcscatter/pccapsym only if the regenerated table drops them; else green -- keep it as the guard).
- Test: pci recast labels -- `TestImmediateRecast::test_pci_labels_under_recast[mode-target]` (red), `::test_pci_plain_draws_none[mode]` (green guard).
- Test: scatteri recast labels for each measured-labelled target, none for line/area -- `TestImmediateRecast::test_scatteri_labels_under_recast[mode-target]` (red for connected/dropline).
- Test: the dash.ado text has no `pci draws no labels` note -- `TestImmediateRecast::test_no_pci_note` (red).
- Test: `_DASH_SCATTERI_LABEL_RECASTS` equals the fixture's labelled targets and is on the served copy tuple -- `TestImmediateRecast::test_the_constant` (red).
- Test: a context probe folds into its option -- `test/test_unknown_options.py::TestTheSilentTableIsTheNotedFixture::test_a_context_probe_folds_into_its_option`: `gen.silent_rows` on a synthetic fixture (`types` = scatter, pcspike, pcscatter; a `headlabel` probe holding all three, refused on scatter and drawing the same on pcspike and pcscatter; a `headlabel+mlabel` probe holding pcspike and pcscatter only, the same on pcspike and different on pcscatter) raises nothing, gives a headlabel row of exactly `pcspike` (pcscatter leaves; scatter, which the context probe does not hold, keeps the plain probe's verdict, refused, so no row), and no row named `headlabel+mlabel` (red at the base, which keeps pcscatter; a name fold without the missing-type rule raises KeyError on scatter instead).
- Test: the arrow options' closing sentence (dash.sthlp:332) is true -- `TestTheHelp::test_the_arrow_options_sentence`: `_between(_help(), "{opt headlabel} puts the marker labels", "A range type takes")` (the `_between` pattern of test/test_help_claims_1.py) holds "taken in silence, as {cmd:twoway} takes it", "refused, as {cmd:twoway} refuses it" and "{cmd:mangle()} and {cmd:barbsize()} off the arrow types are taken in silence", and not "named in the note" (red at the base).

cscript cases (block `* ==== S01 basic:PT-1: headlabel on pcscatter, pccapsym, pcarrowi ====` and `* ==== S01 MS-7: immediate labels under recast() ====` in test/test_wp47_truth.cscript; refusal/acceptance cases in test/test_option_validation.cscript):
- Q4701-1 `dash pcscatter mpg weight trunk turn in 1/5, mlabel(make) headlabel name(q1)`: rc 0, no note naming headlabel (log read with `cert_file_has`, `r(found) == 0`).
- Q4701-2 the same on pcarrowi with labels: rc 0, silent.
- Q4701-3 `dash pci 20 2000 30 4000 "A", recast(pccapsym) name(q3)`: rc 0, no `pci draws no labels` line.
- Q4701-4 (test_option_validation.cscript) `dash scatteri 20 3000, mlabel(nosuch)`: rc equal to the fixture's M01 twoway rc (0); `mlabel(..)` and `mlabel(=)` rc and first line equal M05/M06's.

Pinned tests to flip: test_parser.cscript P1A-65c (note present -> absent); test_pccapsym_pcarrowi.py tail-under-headlabel assertions if any; test_marker_label_parity.py docstring table.

Parity (R8): append to `CORPUS` in test/test_mode_parity.py `_case("pcscatter mlabel headlabel", [...])`, `_case("pccapsym mlabel headlabel", [...])`, `_case("pci labels recast(pccapsym)", [...])`, `_case("scatteri labels recast(connected)", [...])` built like the existing `pcarrowi headlabel with labels` entry (:2547 area; re-read).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| headlabel positions | pytest TestHeadlabel; Q4701-1/2 | immediate_label_truth H01-H07 | yes |
| headlabel after a move | node run_filter_js_block; served move | -- | yes |
| silence | pytest test_silent; cscript log reads | noted_option_truth headlabel+mlabel | yes |
| pci/scatteri recast labels | pytest TestImmediateRecast; Q4701-3 | R01-R06, S01-S08 | yes |
| mlabel(nosuch) on immediates | Q4701-4 | M01-M07 | n/a |
| parity | test_mode_parity CORPUS | -- | yes |
| the arrow options' sentence (:332) | pytest TestTheHelp | -- | n/a |

- AC-47-01.1 Every red stub above was red at the section's base (saved failure text) and is green after.
- AC-47-01.2 Q4701-1..4 PASS under the console binary.
- AC-47-01.3 dash.sthlp's "Where labels are drawn" paragraph matches the measured rule; HR-14's :3472-3475 and :332 (its headlabel and its mangle/barbsize clauses) are true.
- AC-47-01.4 GAPS4 basic:PT-1 and MS-7 Tracked lines read `Closed in WP-47, BUGS.md "<title>", commit pending.`

## Tasks

**Commit boundary.** 47-01-01 and 47-01-02 form basic:PT-1's commit, subject `Draw headlabel on pcscatter, pccapsym and pcarrowi (WP-47 basic:PT-1)`. 47-01-03 and 47-01-04 form MS-7's commit, subject `Draw immediate labels under recast() and take mlabel() unchecked on immediates (WP-47 MS-7)`. 47-01-05 commits nothing (a check). Branch `wp47-s01`.

<task type="auto" id="47-01-01">
  <name>Measure twoway and write headlabel tests</name>
  <files>scripts/extract_immediate_label_truth.do, scripts/extract_noted_option_truth.do, test/test_pc_immediate_labels.py</files>
  <action><![CDATA[Create scripts/extract_immediate_label_truth.do with probes H01-H07, R01-R06, S01-S08, M01-M07 exactly as "Stata truth" lists, on extract_noted_option_truth.do's skeleton (root check, `shell git rev-parse HEAD` into a file read by the python block, `_meta` with stata_version, born_date, dash_commit, extracted, source; texts read with scripts/svg_truth.py `svg_texts` and positions converted with `fit_axis_mapping`). Extend extract_noted_option_truth.do with the `headlabel+mlabel` probe set (after the `probes` loop, before the graph-level block). Write the fold test of TR-47-01.9 in test/test_unknown_options.py and run it before any generator edit: `python3 -m pytest "test/test_unknown_options.py::TestTheSilentTableIsTheNotedFixture::test_a_context_probe_folds_into_its_option" -q -n0 > <scratch>/47-01-01-failure.txt; true` (red); then apply TR-47-01.9's fold to scripts/gen_twoway_takes_table.py (part of basic:PT-1's commit). Run both through `scripts/stata_slot.sh <scratch> <file>` with DASH_REPO=<worktree>, then `python3 scripts/gen_twoway_takes_table.py` (it rewrites the tw_silent block of dash_parse.mata) and `git add -f test/fixtures/immediate_label_truth.json test/fixtures/noted_option_truth.json`; add immediate_label_truth.json to test/test_fixtures_are_committed.py. Create test/test_pc_immediate_labels.py with every TestHeadlabel stub and the TestTheHelp stub. Run `python3 -m pytest test/test_pc_immediate_labels.py::TestHeadlabel test/test_pc_immediate_labels.py::TestTheHelp -q -n0 >> <scratch>/47-01-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/47-01-01-failure.txt` prints at least 7; `python3 -c "import json;d=json.load(open('test/fixtures/immediate_label_truth.json'));print(d['H02']['twoway_rc'], len(d['H02']['texts']))"` prints `0` and a count above 0; `git diff --stat` shows dash_parse.mata changed only inside the tw_silent BEGIN/END block.]]></verify>
  <done>twoway's headlabel and immediate-label truth is committed as a fixture and the headlabel tests fail against the base.</done>
</task>

<task type="auto" id="47-01-02">
  <name>Draw headlabel and close basic:PT-1</name>
  <files>dash_render.py, dash.ado, dash.sthlp</files>
  <action><![CDATA[Apply TR-47-01.1, TR-47-01.2, TR-47-01.3 and TR-47-01.6(b). dash.sthlp: rewrite the sentence at :3472-3475 ("headlabel moves those labels ... on pcscatter and pccapsym dash names it in the note and draws the labels at the first point.") to "{cmd:headlabel} moves those labels to the second point, the head, on {cmd:pcscatter}, {cmd:pccapsym}, {cmd:pcarrow}, {cmd:pcbarrow} and {cmd:pcarrowi}, as {cmd:twoway} does; on {cmd:pcspike}, {cmd:pci}, {cmd:rpcap} and {cmd:rpspike}, which draw no labels, it changes nothing, and is taken in silence." and the pcarrowi sentence at :659 ("at its arrow's tail for pcarrowi") to "at its arrow's tail for {cmd:pcarrowi}, or at its head under {cmd:headlabel}". dash.sthlp:332 ("On the other plot types these three options are named in the note.", after the arrow options' `{opt headlabel}` entry at :328-329): rewrite the whole sentence to "{cmd:headlabel} also moves the labels of {cmd:pcscatter}, {cmd:pccapsym} and {cmd:pcarrowi}; on {cmd:pcspike}, {cmd:pci}, {cmd:rpcap} and {cmd:rpspike} it is taken in silence, as {cmd:twoway} takes it, and on every other type it is refused, as {cmd:twoway} refuses it. {cmd:mangle()} and {cmd:barbsize()} off the arrow types are taken in silence, as {cmd:twoway} draws nothing different with them." (Appendix B HR-14 gives :332 to this section; both clauses are true at the base's code: headlabel off the pc types, rpcap and rpspike is refused before the `_hl_named` loop through `_dash_tw_refuses_tab`'s headlabel row, as dash.ado:2861-2864's comment says, and the `mangle`/`barbsize` rows of `_dash_tw_silent_tab` silence both off the arrow types). Remove `{cmd:pccapsym}, {cmd:pcscatter},` from the `headlabel on ...` clause of the `{ul:Not drawn.}` paragraph (find it with `grep -n "{cmd:headlabel} on {cmd:pcspike}" dash.sthlp`, :6596 at 090d928; the clause runs :6596-6597) -- they draw it now; keep the rest of that clause. TWOWAY_COVERAGE_AUDIT.md :71/:81/:84 (re-read): rewrite only the headlabel clause of each cell and keep the rest of the cell as it stands (the jitter clause is M12's and stays; "a missing second point drops the whole observation" is 47-06's PT-15 case 2) -- :81 (pccapsym) and :84 (pcscatter) "`headlabel` and jitter unavailable" becomes "`headlabel` drawn (WP-47 basic:PT-1); jitter unavailable"; :71 (pcarrowi) "optional tail labels/clock positions" becomes "optional tail labels/clock positions (at the head under `headlabel`, WP-47 basic:PT-1)". Flip pinned tests per Evidence (test/test_pccapsym_pcarrowi.py's tail-under-headlabel assertions, if any, and the docstring table of test/test_marker_label_parity.py). Append the Q4701-1/2 block to test/test_wp47_truth.cscript above the marker and run it with `WP47_ONLY=S01`. Run `python3 -m pytest test/test_pc_immediate_labels.py::TestHeadlabel test/test_pc_immediate_labels.py::TestTheHelp test/test_pccapsym_pcarrowi.py test/test_arrowheads.py test/test_unknown_options.py test/test_help_conformance.py test/test_marker_label_parity.py -q -n0` then append the two headlabel entries of TDD stubs (Parity) to `CORPUS` in test/test_mode_parity.py and run them (`python3 -m pytest test/test_mode_parity.py -k "headlabel" -q -n0`). Before closing, `git diff <base> -- dash_parse.mata` must show, inside the tw_silent block, only the `headlabel` row changed (else STOP and report, D-47-01.b; 47-01-05 records the rows). Close the BUGS.md entry for basic:PT-1 (PD-4 closed form), rewrite its GAPS4 Tracked line (PD-3 Closed form, commit pending), delete `basic:PT-1` from GAPS4_OPEN in test/test_tracking_documents.py, add the CHANGELOG line under `### Fixed in WP-47` ending `(WP-47, basic:PT-1)`, write the commit body in BRIEF's line forms (Notes). Before the commit take BRIEF's closing steps (1)-(3) for basic:PT-1 (Notes "Before every commit" gives each command in full): (1) delete basic:PT-1's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `basic:PT-1 (documented)` or `basic:PT-1 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py basic:PT-1` and delete every row it prints from its `*_KNOWN` table -- a difference basic:PT-1's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with basic:PT-1. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest prints 0 failed; the Stata log shows `Q4701-1 PASS` and `Q4701-2 PASS`; `git log -1 --format=%s` ends `(WP-47 basic:PT-1)`; `grep -c "basic:PT-1 Tracked:\*\* Closed in WP-47" GAPS4.md` prints 1.]]></verify>
  <done>headlabel moves the labels to the second point on pcscatter, pccapsym and pcarrowi in both modes, silently, and basic:PT-1 is closed in one commit.</done>
</task>

<task type="auto" id="47-01-03">
  <name>Write the immediate-label recast tests</name>
  <files>test/test_pc_immediate_labels.py, test/test_option_validation.cscript</files>
  <action><![CDATA[Add the TestImmediateRecast stubs to test/test_pc_immediate_labels.py, reading the expected labelled targets from immediate_label_truth.json (R01-R05 twoway texts holding "A"/"B"; S01-S08 the same). Add case Q4701-4 to test/test_option_validation.cscript under its own id (after the last OV-/Q-case block of the mlabel area; re-read). Run `python3 -m pytest test/test_pc_immediate_labels.py::TestImmediateRecast -q -n0 > <scratch>/47-01-03-failure.txt; true` and the cscript case through a two-line driver with `scripts/stata_slot.sh`, appending its failing lines to the same file. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/47-01-03-failure.txt` prints at least 4; the Q4701-4 line in the file shows `FAIL` (dash rc 111 against twoway's 0).]]></verify>
  <done>The recast-label and mlabel-on-immediates regression tests fail against the base with the failure text saved.</done>
</task>

<task type="auto" id="47-01-04">
  <name>Draw immediate labels and close MS-7</name>
  <files>dash_render.py, dash.ado, dash.sthlp</files>
  <action><![CDATA[Apply TR-47-01.4, TR-47-01.5 (constant `_DASH_SCATTERI_LABEL_RECASTS` placed beside `_DASH_LITERAL_TYPES`, its value the fixture's labelled S-targets, and its copy-list entry), TR-47-01.6(a) and TR-47-01.6(c). dash.sthlp: replace ":659-661" ("{cmd:pci} draws no labels, as {cmd:twoway pci} draws none, and says so;") with "{cmd:pci} draws its labels only under {cmd:recast()} to {cmd:pccapsym}, {cmd:pcarrow}, {cmd:pcbarrow} or {cmd:pcscatter}, at the first point (the second under {cmd:headlabel}), as {cmd:twoway} does;" and add after the scatteri label sentence "Under {cmd:recast()} the labels are drawn when the type named draws marker labels ({it:list the measured targets}), as {cmd:twoway} draws them; {cmd:mlabel()} on {cmd:scatteri}, {cmd:pci} and {cmd:pcarrowi} is not looked up in the data, as {cmd:twoway} does not look it up." Flip test/test_parser.cscript P1A-65c to `r(found) == 0` with a `// Flipped (WP-47 MS-7): the note was false under recast() and twoway is silent` comment. Append the Q4701-3 block (S01's MS-7 block) to test/test_wp47_truth.cscript above the marker and run `WP47_ONLY=S01`; run test_option_validation.cscript and test_parser.cscript once each; run `python3 -m pytest test/test_glyphs.py -k "pci or scatteri" -q -n0`, then `python3 -m pytest test/test_pc_immediate_labels.py test/test_paired_coordinate_plots.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName -q -n0` (two commands: `-k` applies to every path of a command), and, after appending the two MS-7 entries of TDD stubs (Parity) to `CORPUS` in test/test_mode_parity.py, `python3 -m pytest test/test_mode_parity.py -k "recast" -q -n0`. Close MS-7's BUGS entry, Tracked line, GAPS4_OPEN (test/test_tracking_documents.py) line and CHANGELOG line (under `### Changed behaviour (may need your do-files changed)` for the mlabel(nosuch) acceptance, naming `scatteri 20 3000, mlabel(nosuch)`: was r(111), now drawn), the item's TWOWAY_COVERAGE_AUDIT.md cells (grep `scatteri`, `pci`, `recast`). Before the commit take BRIEF's closing steps (1)-(3) for MS-7 (Notes "Before every commit" gives each command in full): (1) delete MS-7's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `MS-7 (documented)` or `MS-7 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py MS-7` and delete every row it prints from its `*_KNOWN` table -- a difference MS-7's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with MS-7. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; the logs show `Q4701-3 PASS`, `Q4701-4 PASS`, test_parser.cscript and test_option_validation.cscript `ALL CHECKS PASSED` (or their success line); `git log -1 --format=%s` ends `(WP-47 MS-7)`; `grep -c "pci draws no labels" dash.ado dash.sthlp` prints 0 for both.]]></verify>
  <done>pci and scatteri labels are drawn under recast() as twoway draws them, mlabel() on immediates is not checked against the data, and MS-7 is closed in one commit.</done>
</task>

<task type="auto" id="47-01-05">
  <name>Check the regenerated silent table rows</name>
  <files>none</files>
  <action><![CDATA[Diff the tw_silent block (dash_parse.mata `BEGIN tw_silent` .. `END tw_silent`) between the section's base and the branch: `git diff <base> -- dash_parse.mata`. Expected: the `headlabel` row loses exactly the types where the `headlabel+mlabel` probes draw differently (pcscatter, pccapsym and pcarrowi by the audit's measurement, and pcarrow and pcbarrow, whose labels headlabel already moves; the fixture decides; scatter and the other types the context probes do not hold keep their plain-probe verdict) and no other row moves. Write the diff, the H02/H04/H06 twoway label positions against dash's and the measured scatteri recast list to <scratch>/47-01-05-rows.txt and put them in the hand-back. Run `python3 scripts/gen_twoway_takes_table.py --check`. If any other row moved, STOP and report it with its fixture rows (a re-measured row means the plain picture changed between runs): do not hand-edit the block. No maintainer approval is asked: the rows follow the measurement (D-47-01.b).]]></action>
  <verify><![CDATA[`python3 scripts/gen_twoway_takes_table.py --check` exits 0; <scratch>/47-01-05-rows.txt shows only the headlabel row changed, or the section stopped and reported the other rows.]]></verify>
  <done>The regenerated silence rows were checked against the measurement and reported in the hand-back.</done>
</task>

## Section completion criteria

- Every stub green; Q4701-1..4 PASS; P1A-65c flipped with its reason; no test deleted.
- `_DASH_SCATTERI_LABEL_RECASTS` on the served copy tuple; the tw_silent block regenerated, not hand-edited.
- Help (:332, :3472-3475, :659-661, the Not drawn clause), TWOWAY_COVERAGE_AUDIT.md (the headlabel clauses only), BUGS.md, GAPS4 (two Tracked lines), CHANGELOG in the two item commits.

## Notes

- **Help paragraphs this section owns (R3):** dash.sthlp :3468-3480 ("Where labels are drawn"), :652-663 (immediate labels), :332 (the whole sentence, its headlabel and its mangle/barbsize clauses; 47-01-02), the `headlabel` clause of `{ul:Not drawn.}` (:6596-6597). Appendix B HR-14's :3472-3475 and :332 are corrected here: :332 is 47-01's whole sentence (Appendix B HR-14); 48-01 verifies it.
- **Merge rules touched:** R1 (truth block, Q4701 ids), R2 (one constant), R3, R5, R7 (two fixtures), R8 (four corpus entries), R9 (P1A-65c), R14.
- **Trap:** `map_pci_literal` filters `_labels` by `_keep` but not `_clocks`; filter both before calling `_immediate_labels` or the clocks shift.
- **Trap:** pcscatter's `_DASH_MLABEL_X/_Y` half of NaN must stay the SECOND half (the second-point markers), whichever point is labelled.
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp47-s01`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_pc_immediate_labels.py::TestHeadlabel::test_pcscatter_labels_the_second_point -- failed at <base> with <text>`; `Flipped: test/test_parser.cscript P1A-65c -- the pci note was expected; it was wrong because twoway draws pci labels under recast() and is silent otherwise`; `Fixture: test/fixtures/immediate_label_truth.json (scripts/extract_immediate_label_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: basic:PT-1 Tracked`.
