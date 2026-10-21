# Section 46-01: recast(): horizontal judged as twoway judges it

> Part of: WP-46 (recast() and horizontal, P14) · Items: RH-1, RH-9, RH-11 · Risk: yellow · Batch: 46.1 · Depends on: none · Blocks: 46-02 · Tasks: 6, 3 commits · Case-id prefix: Q4601

## Overview

**What is wrong today.**
- **RH-1 (with RH-2).** "A range source recast to line/scatter/connected refuses horizontal/vertical (twoway turns it); recast to bar/area/spike/dropline/dot with horizontal is turned by dash where twoway draws it upright." twoway: `rarea lo hi x, recast(line) horizontal` rc 0, turned; `rcap lo hi x, recast(scatter) vertical` rc 0; `tsrline lo hi, recast(line) horizontal` rc 0; `rarea lo hi x, recast(connected) horizontal` rc 0 (V2). `rspike lo hi x, recast(bar) horizontal` and `rarea ..., recast(area) horizontal` rc 0 "bar_drop_to x ... horizontal has no effect"; spike and dropline the same (V3, V4). dash refuses the first group "option horizontal not allowed", r(198) (`_dash_process_segment` sets ptype to the yx target, dash.ado:6659, before `_dash_hz_check` :6665, and line/scatter/connected are in neither `_hz_htypes` nor `_hz_vtypes`, :2940-2941) and turns the second (`_dash_is_horizontal` dash_render.py:45741-45756 turns any bar or area target).
- **RH-9 (with RH-10, RH-12).** "dot with a non-bar recast takes h/v (twoway refuses); scatteri recast to bar-like refuses h/v (twoway turns it); recast(b)/(ba) takes h/v and draws p1bar (twoway refuses and draws p1)". `dot y x, recast(line) horizontal` -> twoway r(198) "option horizontal not allowed", dash rc 0 (the dot branch exits `_dash_recast_opt` before the target is read, dash.ado:3258-3261); `scatteri 1 1 2 2 3 1, recast(bar) horizontal` -> twoway rc 0 turned, dash r(198) (`_hz_derived` :2942 and `_DASH_DERIVED_ORIENT_TYPES` :45710-45713 omit scatteri, which `_dash_recast_opt`'s `_derived` :3272 holds); `scatter y x, recast(b) horizontal` -> twoway r(198) and `recast(b)` draws "bars with an outline 9.72 SVG units wide, where recast(bar) gives 6.48 (style p1, not p1bar)"; `recast(ba) horizontal` r(198) (V7). dash canonicalises `b` to `bar` before judging (dash.ado:3291-3300).
- **RH-11.** "Abbreviated yx names on y2xtype sources (sc, li, co, b) are read as full names; twoway notes them and draws rspike." `rline lo hi x, recast(sc)` and `histogram mpg, recast(li)` print "named style sc|li not found in class y2xtype..." and draw rspike (y2xtype.class `_unabbrev`: RSCatter RLIne RCOnnected only). dash.ado:3288 gives y2xtype the yxtype minimums (`scatter:2 line:2 connected:2 bar:1 ...`); the ciplot canon (dash.ado:10548) already uses `scatter:7 line:4 connected:9 bar:3`.

**After this section.** horizontal/vertical on a recast layer are accepted and refused exactly where twoway accepts and refuses them, judged on the typed recast word; a range source recast to line/scatter/connected is turned by horizontal, one recast to bar/area/spike/dropline/dot is drawn upright; scatteri recast to a bar-like type is turned; an abbreviated bar or area recast draws the generic p# style; abbreviated yx names on a y2xtype source print twoway's two notes and draw rspike.

**Why together.** All three are `_dash_recast_opt`'s name reading and `_dash_hz_check`'s judgement (the Owns column), plus the renderer's `_dash_is_horizontal` turn rule they feed. 46-02 builds on the corrected kinds.

**Test order and commit rule.** Per item: 46-01-01 measures every item into the two existing fixtures and writes RH-1's failing tests (no commit); 46-01-02 fixes RH-1 and commits `(WP-46 RH-1)`; 46-01-03/04 RH-9; 46-01-05/06 RH-11. No full suite inside the section.

### Section decisions

- **D-46-01.a -- range2yx takes both flags.** `_dash_hz_check` accepts horizontal and vertical whenever `kind == "range2yx"` (twoway_y2xview_parse.class:51-65 reads them for every y2x source); "may not combine" still applies.
- **D-46-01.b -- the turn rule.** `_dash_is_horizontal(plot)`: a plot with `recast_from` in the range types (`_DASH_RANGE_RECAST_SOURCES = ("rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter", "tsrline")`, new constant) is turned only when its type (the yx target) is `line`, `scatter` or `connected`; a bar/area/spike/dropline/dot target is drawn upright (twoway_y2xview_parse.class:119 resets bar_drop_to to x).
- **D-46-01.c -- the typed word.** `_dash_recast_opt` returns `s(_recast_typed)` = the word as typed. `_dash_hz_check` gets it as a fifth argument: for kind base, ts or derived, a target in `bar area spike dropline dot` takes h/v only when the typed word equals the full name (BarOrBarDerived compares the typed string, twoway_yxview_parse.class:324, :456); for ptype dot, the judgement is on the typed word: h/v allowed only for `bar area dot dropline spike` typed in full (kind `dotrecast`, set by the dot branch before `_dash_recast_named`), the dot graph drawn unchanged.
- **D-46-01.d -- the generic style.** A yx recast whose typed word is an abbreviation of `bar` or `area` carries the plot option `typesfx` = `generic`; the renderer then draws the bar or area in the generic `p<k>` style (outline width, colour, fill) instead of `p<k>bar`/`p<k>area` (twoway_yxview_parse.class:1041-1045, :1326-1335). Other abbreviated targets draw the same picture in twoway (recast(li) = recast(line) under stcolor, measured) and keep today's style.
- **D-46-01.e -- y2xtype spellings.** `_dash_recast_opt`'s y2xtype list becomes `"\`_sp_rng' scatter:7 line:4 connected:9 bar:3 area:4 spike:5 dropline:8 dot:3"` -- the ciplot canon's minimums, which are the full names.

## Risk: [yellow] -- acceptance and orientation of recast layers

**Why.** `_dash_hz_check` and `_dash_is_horizontal` decide every recast layer's acceptance and turn; `_dash_is_horizontal` has six callers in both modes (axis titles, roles, legends, the transposer).

**Risk factors.** 1. `test/test_horizontal.py::TestTheTypeSets::test_sets_equal_twoways` (:126-162) pins `_hz_htypes`/`_hz_vtypes` (28/26) and `_hz_derived == _DASH_DERIVED_ORIENT_TYPES`: adding scatteri changes both sets together. 2. A range target drawn turned needs both bounds on the turned axis -- 46-02's RH-3 adds the second bound; until then the turned line spans its first bound only (the test of this section checks orientation, not extent). 3. dash.ado's dot path must keep drawing the dot graph unchanged.

**Mitigation.** Every acceptance case runs twoway live beside dash in `_hz_case` (test_option_validation.cscript :1396-1437); orientation is pinned by the existing `horizontal_truth.json draw.*` reading pattern (b1/x axis titles and label ranges).

## Dependencies

- **Depends on:** none (WP-46 W0 done).
- **Blocks:** 46-02.
- **Parallel batch:** 46.1 alone.

## Evidence

- dash.ado `_dash_hz_check` :2937-2971 (`args ptype target kind S`; sets :2940-2942; derived rule :2956, :2960; refusal :2962-2965; "may not combine" :2967-2970). Header comment :2922-2923 still says "24 types ... 22" (stale; correct it to 28/26 in RH-1's commit).
- `_dash_recast_opt` :3226-3343 (contract :3217-3224; dot exit :3258-3261; `_rc_v` :3263; class lists :3264-3281; spellings :3283-3290; match loop :3294-3300; unknown-name notes and fallbacks :3306-3314; derived :3323-3330; base/ts/range2yx :3331-3342).
- `_dash_process_segment` :6655-6688 (`_ptype_typed` :6598; ptype from target :6659; `yvar1` for range2yx :6660; `_dash_hz_check` call :6663-6665); spec `recast_from` :7107-7110, :7149, :7156.
- ciplot canon dash.ado:10544-10553.
- dash_render.py `_DASH_HORIZONTAL_TYPES` :45696-45701, `_DASH_VERTICAL_TYPES` :45702-45707, `_DASH_DERIVED_ORIENT_TYPES` :45710-45713, `_dash_is_horizontal` :45741-45756 (callers :1816, :39830, :41861, :45764, :58973, :63908), `_dash_transpose_layer` :45769.
- twoway: twoway_y2xview_parse.class:51-65, :119; twoway_yxview_parse.class:319-324, :456-476, :1041-1045, :1326-1335; twoway_dot_parse.class:18-19; y2xtype.class / yxtype.class `_unabbrev`.
- Fixtures: test/fixtures/horizontal_truth.json (`accept` 40 types, `draw` 33, `recast` 18 rows; scripts/extract_horizontal_truth.do, `_hz_probe kind id cmd` :84-98, recast rows :144-160); test/fixtures/recast_truth.json (71 probes; scripts/extract_recast_truth.do, `_rc_probe id cmd` :75-91; W-sc-b `equal_to ''`).
- Pinned tests: test/test_horizontal.py `TestTheTypeSets::test_sets_equal_twoways` (:126-162; stays green with scatteri added to both derived sets) and `TestTheRoleRule::test_is_horizontal_and_role_letter` (:167-187; add range2yx cases, none flips); test/test_option_validation.cscript HZ-01..HZ-17 (:1438-1460; stay green: HZ-06 `bar mpg weight, recast(scatter) horizontal` is base kind, still refused); test/test_recast.py `TestTheFixture::test_meta_and_classes` (:249-263) green; any test asserting `rline ..., recast(sc)` draws a scatter: `grep -rn "recast(sc)\|recast(li)\|recast(co)" test/` -- flip to rspike with the notes.

## User stories

- US-46-01.1 As the Stata user with an existing twoway command, I want `rarea lo hi x, recast(line) horizontal` accepted and turned, and `rspike lo hi x, recast(bar) horizontal` drawn upright, as twoway does.
- US-46-01.2 As the Stata user, I want horizontal on dot, scatteri and abbreviated recast names accepted or refused as twoway accepts or refuses it, with its words.
- US-46-01.3 As the Stata user, I want `rline lo hi x, recast(sc)` to print twoway's notes and draw what twoway draws.

## Business requirements

- BR-46-01.1 For every measured recast/orientation command, dash's rc and first error line equal twoway's.
- BR-46-01.2 A range source recast to line/scatter/connected with horizontal is drawn turned; one recast to bar/area/spike/dropline/dot with horizontal is drawn upright.
- BR-46-01.3 scatteri recast to a bar-like type with horizontal is drawn turned.
- BR-46-01.4 recast(b) and recast(ba) draw the generic plot style (twoway's p1 outline).
- BR-46-01.5 sc, li, co and b on a y2xtype source print twoway's two notes and draw rspike.

## Technical requirements

- TR-46-01.1 `_dash_hz_check`: args become `ptype target kind S typed`; inside the loop, before `if !\`_hz_ok'`: `if "\`kind'" == "range2yx" local _hz_ok 1`; for `inlist("\`kind'", "base", "ts", "derived")` with `\`: list target in _hz_bar'` (`local _hz_bar bar area spike dropline dot`) and `"\`typed'" != "\`target'"`: `local _hz_ok 0` (abbreviated: BarOrBarDerived fails -- for kind base this overrides the ptype membership, since ptype is the target); `if "\`kind'" == "dotrecast" local _hz_ok = \`: list typed in _hz_bar'`. `_hz_derived` gains `scatteri` (after `histogram`). The header comment's counts become 28 and 26.
- TR-46-01.2 `_dash_recast_opt`: `sreturn local _recast_typed "\`_rc_v'"` right after :3263; the dot branch (:3258) becomes: compute `_rc_v` first (move :3263 above it), then `sreturn local _recast_target "\`_rc_v'"`, `sreturn local _recast_kind dotrecast`, then `_dash_recast_named \`_rc_word'` and `exit`. Line :3288 per D-46-01.e.
- TR-46-01.3 `_dash_process_segment`: `local _rc_typed "\`s(_recast_typed)'"` after :6658; the call :6665 passes `"\`_rc_typed'"` as the fifth argument. Kind `dotrecast` joins no other `_rc_kind` test (re-read :6659-6688: `inlist(... "base", "range2yx", "ts")` and the `derived` tests do not match it; the dot graph is drawn unchanged).
- TR-46-01.4 dash.ado: after the `_dash_hz_check` call (:6665), when `_rc_kind` is base or ts, the target is `bar` or `area` and `"\`_rc_typed'" != "\`_rc_target'"`, run `_dash_recast_s typesfx "generic"` (the setter :6685 and :6688 use), and add `typesfx` to the option-name list after `range_var` (:5429) so the plot's options JSON carries `"typesfx":"generic"`.
- TR-46-01.5 dash_render.py: new constant `_DASH_RANGE_RECAST_SOURCES` beside `_DASH_DERIVED_ORIENT_TYPES` (:45710); `_DASH_DERIVED_ORIENT_TYPES` gains `"scatteri"`; `_dash_is_horizontal` after the options check: `rf = str(plot.get("recast_from", "") or "").lower(); if rf in _DASH_RANGE_RECAST_SOURCES: return ptype in ("line", "scatter", "connected")`. Copy list (R2): `"_DASH_RANGE_RECAST_SOURCES",` on the constants tuple after `"_DASH_DERIVED_ORIENT_TYPES",` (grep it; if that name is not on the tuple, after `"_DASH_HORIZONTAL_TYPES",`).
- TR-46-01.6 Generic style (D-46-01.d): `GlyphMapper.map_bar` and `map_area` read their scheme chain through the type suffix (grep the `p%dbar` / `p%darea` style names in `SchemeParser` and the mappers' style lookup, re-read before editing); when `options.get("typesfx") == "generic"` the lookup uses the plain `p<k>` style (outline width, line colour, fill) instead of `p<k>bar`/`p<k>area`. GlyphMapper and SchemeParser are copied whole: no copy-list entry.
- TR-46-01.7 Help (R3): dash.sthlp :372-386 -- "judged after {cmd:recast()}" replaced by "judged on the word {cmd:recast()} names, as {cmd:twoway} judges it: a range type recast to {cmd:line}, {cmd:scatter} or {cmd:connected} takes both and is turned; recast to {cmd:bar}, {cmd:area}, {cmd:spike}, {cmd:dropline} or {cmd:dot} it takes them and is drawn upright; an abbreviation of {cmd:bar} or {cmd:area} takes neither and draws the plain plot style; on {cmd:dot} only a recast to {cmd:bar}, {cmd:area}, {cmd:dot}, {cmd:dropline} or {cmd:spike} takes them"; the orientation paragraph's type list gains rpcap, rpspike, contour and contourline (the 28-type set). :3608-3611 (recast spellings) gains "a range source or {cmd:histogram} takes the yx names in full only, as {cmd:twoway}'s y2xtype does". Appendix B HR-16's :372-386 sentence is 48-02's to verify; this section makes it true.

## Boundaries

- Do not edit `_dash_draw_range_as`, `map_histogram`'s recast branches or `_dash_tag_eval_extent` (46-02's). The second bound of a turned range layer (RH-3) is 46-02's.
- RH-13 (horizontal kdensity key) is 43-04's; RH-14 (area outline) closed by 34-05.
- No change to h/v on types that are not recast (HZ-01..17 green).

## Stata truth

Extend `scripts/extract_horizontal_truth.do` (R7) with `_hz_probe recast` rows (data as the script's: x 1..5, y, lo, hi; auto rows where named), each `nodraw` for rc and a drawn SVG row for orientation (`_hz_probe draw` reads the b1/l1 titles and the x/y label ranges as `draw.*` does):

| id | cmd |
|---|---|
| RH1-01 | `twoway rarea lo hi x, recast(line) horizontal` (+ draw) |
| RH1-02 | `twoway rcap lo hi x, recast(scatter) vertical` |
| RH1-03 | `twoway rarea lo hi x, recast(connected) horizontal` (+ draw) |
| RH1-04 | `twoway rspike lo hi x, recast(bar) horizontal` (+ draw) |
| RH1-05 | `twoway rarea lo hi x, recast(area) horizontal` (+ draw) |
| RH1-06 | `twoway rspike lo hi x, recast(spike) horizontal`; RH1-07 `rcap lo hi x, recast(dropline) horizontal`; RH1-08 `rbar lo hi x, recast(dot) horizontal` |
| RH1-09 | `twoway rarea lo hi x, recast(line) horizontal vertical` |
| RH9-01 | `twoway dot y x, recast(line) horizontal`; RH9-02 `dot y x, recast(scatter) vertical`; RH9-03 `dot y x, recast(bar) horizontal`; RH9-04 `dot y x, recast(b) horizontal` |
| RH9-05 | `twoway scatteri 1 1 2 2 3 1, recast(bar) horizontal` (+ draw); RH9-06 `scatteri ..., recast(area) vertical` |
| RH9-07 | `twoway scatter y x, recast(b) horizontal`; RH9-08 `recast(ba) horizontal`; RH9-09 `recast(bar) horizontal` |

and `scripts/extract_recast_truth.do` (R7) `_rc_probe` rows: RH11-01 `twoway rline y y2 x, recast(sc)`, RH11-02 `histogram mpg, recast(li)`, RH11-03 `rline y y2 x, recast(co)`, RH11-04 `rbar y y2 x, recast(b)`, RH11-05 `tsrline` form if the script's data are tsset (else skip and say so in the commit body); RH9-10 `twoway scatter y x, recast(b)` and RH9-11 `recast(bar)` with the bar outline stroke-width read from the SVG. Regenerate both fixtures through `scripts/stata_slot.sh`; `git add -f`.

Truth blocks in `test/test_wp46_truth.cscript` (created by W0), one per item (BRIEF, Certification scripts), above `* ==== append new blocks above this line ====` (46-01 is WP-46's first section, so nothing lies below its blocks; 46-02's S02 blocks follow them): `* ==== S01 RH-1: recast range layers take horizontal ====`, `* ==== S01 RH-9: horizontal judged on the typed recast word ====`, `* ==== S01 RH-11: yx names on a y2xtype source read in full ====`, each gated `local only : env WP46_ONLY` / `if inlist("\`only'", "", "S01") & \`: list posof "S01" in w46_run' {` with its `S01 start`/`S01 end` display lines, and `S01` added to the script's run list `w46_run` (as 46-02-01 adds `S02`). Each block runs its item's drawn probe live under twoway beside dash, as the `draw.*` rows read it: helper program `_q4601_draw <k> <command>` (defined once, in the RH-1 block) sets up the extract script's data (copy the set-up lines of scripts/extract_horizontal_truth.do -- x 1..5, y, lo, hi -- or, for RH11-01, of scripts/extract_recast_truth.do), runs `capture noisily twoway <command>` and `cert_svg_export, name(...) file(...)`, reads twoway's b1 and l1 titles with `cert_svg_has_text` and its x and y label ranges with `cert_svg_extent, axis(x)` / `axis(y)` (test/cert_svg.do; save r() at once, every program there clobbers it), then runs `capture dash <command> name(zq4601<k>)` and `_dash_serve_spec, specpath() datapath()`; a top-level `python:` helper `_q4601_check` (modelled on test_wp31_truth.cscript's `_u33_docs`, which builds both modes) returns each mode's drawn x and y axis titles and Range1d ends. Cases: Q4601-23 (S01 RH-1, probe RH1-01 `rarea lo hi x, recast(line) horizontal`): rc 0 on both sides; in both modes dash's y title equals twoway's l1 title (Xvar's) and twoway's x label range overlaps dash's x range, so the bound lies on the horizontal axis as twoway turns it -- the full two-bound extent and the second bound's title are RH-3's, compared in 46-02's S02 RH-3 block (Risk factor 2); Q4601-24 (S01 RH-9, probe RH9-05 `scatteri 1 1 2 2 3 1, recast(bar) horizontal`): rc 0 on both sides; in both modes twoway's x and y label ranges lie inside dash's x and y ranges (the turned bars); Q4601-25 (S01 RH-11, probe RH11-01 `rline y y2 x, recast(sc)`): rc 0 on both sides; in both modes dash's b1 and l1 titles equal twoway's and twoway's y label range lies inside dash's y range (the rspike spans both bounds). The acceptance, refusal and note cases stay in the area scripts (Q4601-1..22).

## TDD test stubs

In test/test_horizontal.py (`_MODES`):
- RH-1: `TestRangeRecastOrientation::test_line_targets_turned[mode-RH1-01|RH1-03]` (x title = the bound's, y = Xvar, as the fixture's draw row; red), `::test_bar_targets_upright[mode-RH1-04|RH1-05]` (no HBar/HArea; red), `::test_is_horizontal_rule` (unit; red).
- RH-9: `TestDerivedOrientation::test_scatteri_bar_turned[mode]` (RH9-05; red), `TestGenericStyle::test_recast_b_outline[mode]` (bar outline width = the generic p1 line width, fixture RH9-10 vs RH9-11 ratio 1.5 within 0.01; red).
- RH-11: `test/test_recast.py::TestY2xSpellings::test_abbreviations_fall_back[mode-RH11-01..04]` (drawn as rspike: a Segment renderer, no Scatter/Line; red).

cscript cases (test/test_option_validation.cscript, after HZ-17, each `_hz_case Q4601-<k> "<cmd without twoway>"` so twoway and dash run live): Q4601-1..9 RH1-01..09; Q4601-10..18 RH9-01..09; (test/test_twoway_option_parity.cscript, the recast area) Q4601-19..22 RH11-01..04 comparing dash's two note lines with twoway's; (test/test_wp46_truth.cscript, the S01 blocks of Stata truth, the drawn picture live beside twoway) Q4601-23 RH1-01, Q4601-24 RH9-05, Q4601-25 RH11-01.

Pinned tests to flip: the `recast(sc|li|co)` grep of Evidence (expected: test_recast_range_pc.py or test_wp30_truth.cscript RC rows naming a scatter/line drawn from an abbreviation on a range source; flip each to rspike with the notes).

Parity (R8): `_case("rarea recast(line) horizontal", ...)`, `_case("rspike recast(bar) horizontal", ...)`, `_case("scatteri recast(bar) horizontal", ...)` beside the existing horizontal entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| acceptance and words | `_hz_case` Q4601-1..18 (live twoway) | horizontal_truth recast rows | n/a |
| orientation drawn | pytest TestRangeRecastOrientation, TestDerivedOrientation | draw rows | yes |
| generic style | pytest TestGenericStyle | recast_truth RH9-10/11 | yes |
| y2xtype spellings | pytest TestY2xSpellings; Q4601-19..22 | recast_truth RH11-* | yes |
| drawn picture beside twoway | test_wp46_truth.cscript S01 blocks Q4601-23..25 (live twoway, cert_svg.do) | live twoway | yes |

- AC-46-01.1 Every red stub red at its base and green after; failure texts saved.
- AC-46-01.2 Q4601-1..25 PASS; HZ-01..17 still PASS.
- AC-46-01.3 test_horizontal.py, test_recast.py, test_recast_range_pc.py, test_mode_parity.py green.
- AC-46-01.4 RH-1, RH-9, RH-11 Tracked lines Closed.

## Tasks

**Commit boundary.** 46-01-01/02 -> `Take horizontal on a recast range layer as twoway does: turn line targets, keep bar targets upright (WP-46 RH-1)`; 46-01-03/04 -> `Judge horizontal on the typed recast word, for dot, scatteri and abbreviations (WP-46 RH-9)`; 46-01-05/06 -> `Read yx names on a y2xtype source in full, as twoway does (WP-46 RH-11)`. Branch `wp46-s01`.

<task type="auto" id="46-01-01">
  <name>Measure recast orientation, write RH-1 tests</name>
  <files>scripts/extract_horizontal_truth.do, scripts/extract_recast_truth.do, test/test_horizontal.py</files>
  <action><![CDATA[Add the probes of "Stata truth" to both extract scripts (old rows unchanged), run both through `scripts/stata_slot.sh`, `git add -f test/fixtures/horizontal_truth.json test/fixtures/recast_truth.json`. Add the RH-1 stubs to test/test_horizontal.py and cases Q4601-1..9 after HZ-17 in test/test_option_validation.cscript. Append the block `* ==== S01 RH-1: recast range layers take horizontal ====` with `_q4601_draw`, `_q4601_check` and case Q4601-23 above the append marker of test/test_wp46_truth.cscript, and add `S01` to its run list `w46_run` (Stata truth). Run `python3 -m pytest test/test_horizontal.py::TestRangeRecastOrientation -q -n0 -rf > <scratch>/46-01-01-failure.txt 2>&1; true`, test_option_validation.cscript through a two-line driver and test_wp46_truth.cscript with WP46_ONLY=S01, appending their Q4601 FAIL lines. Do not commit.]]></action>
  <verify><![CDATA[`python3 -c "import json;r=json.load(open('test/fixtures/horizontal_truth.json'))['recast'];print(r['RH1-01']['rc'], r['RH1-04']['rc'], r['RH9-01']['rc'], r['RH9-05']['rc'], r['RH9-07']['rc'])"` prints `0 0 198 0 198`; `grep -c FAILED <scratch>/46-01-01-failure.txt` is at least 4; `grep -c "Q4601-[1-3] FAIL" <scratch>/46-01-01-failure.txt` prints 3; the file holds `Q4601-23 FAIL` (dash refuses the probe r(198)).]]></verify>
  <done>twoway's recast orientation answers were recorded and RH-1's tests were shown failing.</done>
</task>

<task type="auto" id="46-01-02">
  <name>Accept range2yx flags, commit RH-1</name>
  <files>dash.ado, dash_render.py, dash.sthlp</files>
  <action><![CDATA[Apply TR-46-01.1's range2yx line and comment fix, TR-46-01.5's constant and turn rule, and TR-46-01.7's range sentence. Run `python3 -m pytest test/test_horizontal.py test/test_recast.py test/test_recast_range_pc.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_cscript_hygiene.py -q -n0`, test_option_validation.cscript (Q4601-1..9 and HZ-01..17 PASS) and test_wp46_truth.cscript with WP46_ONLY=S01 (Q4601-23 PASS). Append the three parity entries of TDD stubs (Parity) to `CORPUS` in test/test_mode_parity.py. Close RH-1 (BUGS, Tracked, GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG under `### Changed behaviour (may need your do-files changed)`: "a range type recast to line, scatter or connected takes horizontal and vertical and is turned, and one recast to bar, area, spike, dropline or dot is drawn upright, as twoway does; rarea lo hi x, recast(line) horizontal was refused r(198) (WP-46, RH-1)"; TWOWAY_COVERAGE_AUDIT.md: grep `recast` and `horizontal`, the matching row gains "[WP-46 RH-1: corrected -- a recast range layer takes horizontal as twoway does]"). Before the commit take BRIEF's closing steps (1)-(3) for RH-1 (Notes "Before every commit" gives each command in full): (1) delete RH-1's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-1 (documented)` or `RH-1 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-1` and delete every row it prints from its `*_KNOWN` table -- a difference RH-1's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-1. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; test_option_validation.cscript prints its success line; the S01 block log shows `Q4601-23 PASS`; `git log -1 --format=%s` ends `(WP-46 RH-1)`.]]></verify>
  <done>Range recast orientation follows twoway in both modes and RH-1 is closed.</done>
</task>

<task type="auto" id="46-01-03">
  <name>Write the typed-word tests</name>
  <files>test/test_horizontal.py, test/test_option_validation.cscript</files>
  <action><![CDATA[Add TestDerivedOrientation and TestGenericStyle stubs and cases Q4601-10..18, and append the block `* ==== S01 RH-9: horizontal judged on the typed recast word ====` with case Q4601-24 above the append marker of test/test_wp46_truth.cscript, after the S01 RH-1 block. Run them into `<scratch>/46-01-03-failure.txt` (pytest and both cscripts' FAIL lines; the truth script with WP46_ONLY=S01). Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/46-01-03-failure.txt` is at least 2; the Q4601-10, -11, -13, -14, -16, -17 FAIL lines are present (dot non-bar, recast(b), scatteri), and `Q4601-24 FAIL` (dash refuses the scatteri probe r(198)).]]></verify>
  <done>RH-9's regression tests were shown failing on the base.</done>
</task>

<task type="auto" id="46-01-04">
  <name>Judge the typed word, commit RH-9</name>
  <files>dash.ado, dash_render.py, dash.sthlp</files>
  <action><![CDATA[Apply TR-46-01.1 (typed argument, dotrecast, `_hz_derived` scatteri), TR-46-01.2 (typed return, dot branch), TR-46-01.3, TR-46-01.4, TR-46-01.5 (`_DASH_DERIVED_ORIENT_TYPES` scatteri), TR-46-01.6 and TR-46-01.7's dot/abbreviation sentences. Run `python3 -m pytest test/test_horizontal.py test/test_recast.py test/test_dot_base_recast.py test/test_glyphs.py -k "bar or recast" -q -n0` and test_option_validation.cscript, test_parser.cscript and test_wp46_truth.cscript (WP46_ONLY=S01: Q4601-23 and Q4601-24 PASS) once each. Close RH-9 (BUGS, Tracked, GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG under Changed behaviour: "horizontal and vertical are judged on the recast word as twoway judges them: dot with a non-bar recast and an abbreviated recast(b) are refused, scatteri recast to a bar-like type is accepted and turned (WP-46, RH-9)"; TWOWAY_COVERAGE_AUDIT.md's recast/horizontal row gains "[WP-46 RH-9: corrected -- horizontal judged on the typed recast word]"). Before the commit take BRIEF's closing steps (1)-(3) for RH-9 (Notes "Before every commit" gives each command in full): (1) delete RH-9's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-9 (documented)` or `RH-9 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-9` and delete every row it prints from its `*_KNOWN` table -- a difference RH-9's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-9. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; test_option_validation.cscript and test_parser.cscript print their success lines; the S01 log shows `Q4601-24 PASS`; `git log -1 --format=%s` ends `(WP-46 RH-9)`.]]></verify>
  <done>Orientation flags follow the typed recast word and RH-9 is closed.</done>
</task>

<task type="auto" id="46-01-05">
  <name>Write the y2xtype spelling tests</name>
  <files>test/test_recast.py, test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[Add `TestY2xSpellings` and cases Q4601-19..22 (the recast area of test_twoway_option_parity.cscript; re-read its RC case form), and append the block `* ==== S01 RH-11: yx names on a y2xtype source read in full ====` with case Q4601-25 above the append marker of test/test_wp46_truth.cscript, after the S01 RH-9 block. Run them into `<scratch>/46-01-05-failure.txt` (the truth script with WP46_ONLY=S01); list the grep's pins in `<scratch>/46-01-flips.txt`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/46-01-05-failure.txt` is at least 4 and the Q4601-19..22 FAIL lines and `Q4601-25 FAIL` (dash draws a scatter, so its titles or y range differ from twoway's rspike) are present.]]></verify>
  <done>RH-11's regression tests were shown failing on the base.</done>
</task>

<task type="auto" id="46-01-06">
  <name>Read yx names in full, commit RH-11</name>
  <files>dash.ado, dash.sthlp</files>
  <action><![CDATA[Apply TR-46-01.2's line :3288 change and TR-46-01.7's spelling sentence. Flip the pins of `<scratch>/46-01-flips.txt` in place, in the files that list names (Evidence's grep; expected test/test_recast_range_pc.py or test/test_wp30_truth.cscript). Run `python3 -m pytest test/test_recast.py test/test_recast_range_pc.py test/test_histogram*.py -k recast -q -n0` and test_twoway_option_parity.cscript and test_wp46_truth.cscript (WP46_ONLY=S01: Q4601-23..25 PASS) once each. Close RH-11 (BUGS, Tracked, GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG under Fixed: "sc, li, co and b on a range type or histogram print twoway's two notes and draw rspike, as twoway does; they drew a scatter, line, connected or bar (WP-46, RH-11)"; TWOWAY_COVERAGE_AUDIT.md's recast row gains "[WP-46 RH-11: corrected -- yx names on a y2xtype source read in full]"). Before the commit take BRIEF's closing steps (1)-(3) for RH-11 (Notes "Before every commit" gives each command in full): (1) delete RH-11's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `RH-11 (documented)` or `RH-11 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py RH-11` and delete every row it prints from its `*_KNOWN` table -- a difference RH-11's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with RH-11. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; test_twoway_option_parity.cscript prints its success line with Q4601-19..22 PASS; the S01 log shows `Q4601-25 PASS` and no FAIL line; `git log -1 --format=%s` ends `(WP-46 RH-11)`.]]></verify>
  <done>y2xtype sources read yx names as twoway reads them and RH-11 is closed.</done>
</task>

## Section completion criteria

- Three commits, failing tests first; Q4601-1..25 PASS (Q4601-23..25 in the three S01 blocks of test_wp46_truth.cscript); HZ-01..17 PASS; no test deleted.
- `_DASH_RANGE_RECAST_SOURCES` on the served copy tuple; `_hz_derived == _DASH_DERIVED_ORIENT_TYPES` still (test_sets_equal_twoways green).

## Notes

- **Help paragraphs owned (R3):** dash.sthlp :372-386 (Orientation), :3608-3611 (recast spellings). HR-16's :372-386 is verified by 48-02.
- **Merge rules:** R1 (three S01 blocks above the append marker, plus the area-script cases), R2, R3, R5, R7, R8, R9.
- **Trap:** `_dash_hz_check`'s callers: grep `_dash_hz_check ` in dash.ado; every call gains the fifth argument ("" where no recast).
- **Trap:** `_rc_v` must be computed before the dot branch, and the dot branch must still call `_dash_recast_named` so `recast()` on dot stays taken (dash.sthlp:6598 vs :3611-3612 contradiction is 48-01's).
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp46-s01`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_horizontal.py::TestRangeRecastOrientation::test_line_targets_turned[saved-RH1-01] -- failed at <base> with <text>` (per item); `Fixture: test/fixtures/horizontal_truth.json (scripts/extract_horizontal_truth.do)`, `Fixture: test/fixtures/recast_truth.json (scripts/extract_recast_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: <id> Tracked`.
