# Section 47-04: Older spellings folded onto the options dash draws

> Part of: WP-47 (Plot-option fidelity, P15) · Items: basic:PT-10 · Risk: green · Batch: 47.3 · Depends on: 47-02, 47-01, 47-03, 47-06 · Blocks: 47-05 · Tasks: 3, 1 commit · Case-id prefix: Q4704

## Overview

**What is wrong today.** basic:PT-10 (with syn:SD-11, sil:SD-17, ST-20, DT-20): "Spellings twoway draws as other options are only noted: symbol(), msymangle(), mlabels(), bcolor(), bfintensity(), blwidth(), blpattern(), afcolor(), afintensity(), bsymbol(), bmsize() on arrows (= barbsize)". twoway's own parser maps each onto an option dash already draws (twoway_yxview_parse.class, read at /Applications/StataNow/ado/base/t/): `Symbol` -> `marker(symbol(X))` as `Msymbol` does; `MSYMANgle` -> `marker(symangle(X))` as `MSAngle`; `MLabels(string)` is the declared full name of mlabel() itself (:141, :186); `BColor` -> `area(shadestyle(color(X)) linestyle(color(X)))` as `AColor`; `BFIntensity`/`AFIntensity` -> `area(shadestyle(intensity(X)))`; `AFColor` -> `area(shadestyle(color(X)))` (= the fill colour); `BLWidth` -> `area(linestyle(width(X)))`; `BLPattern` -> `area(linestyle(pattern(X)))`; `BSymbol` -> `marker(backsymbol(X))` as `BMSymbol`; `BMSIze` -> `marker(backsize(X))`, "the same target as barbsize: the pcarrow SVGs with bmsize(2) and barbsize(2) are identical". dash names every one in its "ignoring unsupported option(s)" note and draws the default (help dash.sthlp:6497-6524 'Older spellings', 'Area, bar and line edge styles', 'Back markers').

**After this section.** Each alias is read as the option twoway factors it onto, with twoway's abbreviation and twoway's precedence against that option, on every plot type, in both modes; the note no longer names any of them. `bsymbol()` becomes `bmsymbol()` (drawn by 47-05); `bmsize()` is `barbsize()` on pcarrow, pcbarrow and pcarrowi, and the back-marker size elsewhere (47-05).

**Why alone.** One small declaration-and-fold change in dash.ado and the generated tables; 47-05 then draws the targets that are still undrawn (back markers).

**Test order and commit rule.** 47-04-01 measures the precedence and abbreviations and writes the failing tests (no commit); 47-04-02 folds (no commit); 47-04-03 regenerates the catch-all fixture's dependants, corrects the help list and commits `(WP-47 basic:PT-10)`.

### Section decisions

- **D-47-04.a — Fold, never draw twice.** Each alias is translated to its target before validation, in `_dash_parse_plot_opts`'s fold step (the place acolor()/alcolor() are folded today; re-read `_dash_fold_cl`/`_dash_fold_bw` :2067-2260 for the pattern): `symbol` -> `msymbol`, `msymangle` -> `msangle`, `mlabels` -> `mlabel`, `bcolor` -> `acolor` (fill and outline), `afcolor` -> `fcolor`, `afintensity` and `bfintensity` -> `fintensity`, `blwidth` -> `alwidth`, `blpattern` -> `alpattern`, `bsymbol` -> `bmsymbol`, and `bmsize` -> `barbsize` on `pcarrow pcbarrow pcarrowi` only. The target's value rules then refuse what twoway refuses, in the target's words (the measured first line decides whether the alias's own name is printed; PD-11).
- **D-47-04.b — Precedence is measured.** twoway factors the options in the class's declaration order (`Msymbol` before `Symbol`, `AColor` before `AFColor` before `BColor` before `BFColor`), so a later-factored alias may win whatever the typed order. 47-04-01 measures every pair both ways (`msymbol(O) symbol(T)` and `symbol(T) msymbol(O)`; `color(red) bcolor(blue)`; `fcolor(red) afcolor(blue)`; `bfcolor(red) bcolor(blue)`; `msangle(10) msymangle(45)`; `mlabel(make) mlabels(foreign)`; `barbsize(1) bmsize(3)` on pcarrow); the fold implements the measured winner per pair, independent of order where twoway is.
- **D-47-04.c — Abbreviations are twoway's.** The minimum abbreviation of each alias is the class's capitals (`Symbol` = `s` unless Stata's parse binds `s` to another declared option first -- measured, `MSYMANgle` = `msyman`, `MLabels` = `ml`, `BColor` = `bc`, `BFIntensity` = `bfi`, `BLWidth` = `blw`, `BLPattern` = `blp`, `AFColor` = `afc`, `AFIntensity` = `afi`, `BSymbol` = `bs`, `BMSIze` = `bmsi`); where a short form collides with an option dash declares (`s` with `sort`; `ml` with `mlabel`), the binding twoway measures wins: read `test/fixtures/abbrev_truth.json` (`abbrev_resolution`) and, for any alias not in it, the 47-04-01 probes (`scatter mpg weight, s(Oh)`, `sy(Oh)`, `msyman(45)`, `bc(red)` on bar, `bfi(30)`, `blw(thick)`, `blp(dash)`, `afc(red)`, `afi(30)`, `bs(O)`, `bmsi(2)` on pcarrow).
- **D-47-04.d — Tables are regenerated.** `scripts/extract_catchall_options_truth.do` is re-run (the folded names leave the catch-all), `scripts/gen_twoway_takes_table.py` regenerates the generated blocks (`tw_silent`, `_dash_rep_und_tab` rows if generated -- re-read the generator's targets), never by hand. Before regenerating, `dlalign` is removed from the generator's `SILENT` tuple (scripts/gen_twoway_takes_table.py, the `SILENT = (...)` list): 47-03 took dlalign() off dash's pending list in batch 47.1 (`SILENT` names the pending options), so its row has filtered nothing since and is dropped here, where the silent table is owned (REVIEW-5 R5-4). The generator keeps 47-01's rules (TR-47-01.9): a `<name>+<context>` probe key counts as a probe of `<name>`, and a type a probe set does not hold keeps the other probes' verdict, so the regeneration and `--check` raise no KeyError on the `headlabel+mlabel` set, which holds the pc and immediate types only.

## Risk: [green] -- declarations and folds only, measured first

**Why.** No renderer change: each target is drawn today. **Risk factors.** 1. Abbreviation collisions (`s`, `ml`, `bc`). 2. The Unsupported count pin and help-conformance both ways. 3. 47-02 changed the mlabel reader (`_dash_mlabel_list`); `mlabels()` must reach it unchanged. **Mitigation.** 1. D-47-04.c with test_abbreviations.py rows. 2. Move the pins with `# old -> new` comments. 3. A regression test runs `mlabel(t*)` and `mlabels(t*)` side by side.

## Dependencies

- **Depends on:** 47-02 (mlabel reader) and 47-06 (msymbol table rewritten there; `symbol()` folds onto it), both in batch 47.2; 47-03 (batch 47.1: dlalign() off the pending list, D-47-04.d); 47-01 (batch 47.1: the generator's context-key and missing-type rules). The header names all four, as the index's manifest row does (REVIEW-5 R5-37); every one of them lies in an earlier batch, so the batch order already holds.
- **Blocks:** 47-05 (draws back markers, the targets of `bsymbol()`/`bmsize()` off the arrows).
- **Batch 47.3** alone.

## Evidence

Anchors at `090d928`; re-read (47-01..47-06 moved lines).

- twoway: `/Applications/StataNow/ado/base/t/twoway_yxview_parse.class` :141 and :186 (`MLabels`), the marker block (`Msymbol`, `Symbol`, `MSYMANgle`, `MSAngle`, `BARBSize`, `BMSymbol`, `BSymbol`, `BMSIze`) and the area/bar blocks (`AColor`, `AFColor`, `AFIntensity`, `BColor`, `BFColor`, `BFIntensity`, `BLWidth`, `BLPattern`) -- quoted in this section's Overview; re-read the line numbers at execution.
- dash.ado: `_dash_parse_plot_opts` :1203 (declarations :1246-1290; `MLabel(string asis)` :1248); the fold programs `_dash_fold_bw` :2067, `_dash_fold_cl` :2176, `_dash_fold_mlab` :2218, `_dash_fold_typed` :2740; the arrow types `arrow_types "pcarrow pcbarrow pcarrowi"` :2785.
- dash_parse.mata: `_dash_rep_und_tab` :7658 (undeclared twoway options); `_dash_tw_silent_tab` :8234 (generated).
- Fixtures: `test/fixtures/catchall_options_truth.json` (`options` holds afcolor, afintensity, bcolor, bfintensity, blpattern, blwidth, bmsize, bsymbol, mlabels, msymangle, symbol), `abbrev_truth.json` (holds `symbol` and `bcolor`).
- Help: dash.sthlp :6497-6524 ('Area, bar and line edge styles', 'Back markers', 'Older spellings').
- Pinned tests: test/test_help_conformance.py `assert len(_unsupported_section()) == 59` (:807; re-read the current count) and `TestTheUnsupportedSectionIsTrue` (:1182-1212); test/test_unsupported_report_is_true.py declared/pending counts (comments `# 196 -> 199` style, :932); test/test_abbreviations.py; test_twoway_option_parity.cscript catch-all rows (grep `symbol(` and `bcolor(`).

## User stories

- US-47-04.1 As a Stata user with an old do-file, I want `symbol(Oh)`, `msymangle(45)` and `mlabels(make)` drawn as twoway draws them.
- US-47-04.2 As a Stata user, I want `bcolor()`, `bfintensity()`, `blwidth()`, `blpattern()`, `afcolor()` and `afintensity()` to style my bars and areas.
- US-47-04.3 As a Stata user, I want `bmsize()` on an arrow to size its head as `barbsize()` does.

## Business requirements

- BR-47-04.1 Each alias draws the picture its target draws, on every type, both modes; the pair precedence equals twoway's measured precedence.
- BR-47-04.2 No alias is named in a note; a bad value is refused as twoway refuses it.
- BR-47-04.3 Every abbreviation of an alias binds as twoway binds it.
- BR-47-04.4 The help's Unsupported list no longer lists the aliases (except `bsymbol()`/`bmsize()` as back-marker spellings until 47-05 draws them).

## Technical requirements

- TR-47-04.1 dash.ado declarations in `_dash_parse_plot_opts` (after the declaration of each target; spellings per D-47-04.c), each `(string asis)` as its target is; sreturn lines beside the targets'; the fold per D-47-04.a/b in a new program `_dash_fold_alias, sclass` called first in the fold chain (before `_dash_fold_bw`; re-read the chain's call site), `version 19`, which writes the winning value to the target's `s()` and empties the alias's `s()`. program_coverage_map.py row for `_dash_fold_alias` (R6). Comment header names this section and the class lines.
- TR-47-04.2 The pending/catch-all path: after the fold the aliases never reach `_pending` or the catch-all note (the catch-all reads leftover options; folded ones are consumed).
- TR-47-04.3 No Python change; the targets are drawn. Both modes follow.
- TR-47-04.4 Regenerate per D-47-04.d; `git add -f` the regenerated fixtures.

## Boundaries

- Do not draw back markers (47-05) or touch alignment (47-03; `alalign()`/`blalign()`/`clalign()` stay for 47-05).
- Do not edit renderer code, `_dash_option_rules` values (only add the aliases where a rule must name them), or any JS.

## Stata truth

New `scripts/extract_alias_truth.do` -> `test/fixtures/alias_truth.json` (`_meta`; extract_noted_option_truth.do skeleton): for each alias A with target T on the type of its catch-all probe (scatter, bar, area, pcarrow): P1 `<type> ..., A(<v>)` vs `<type> ..., T(<v>)` SVG equality (normalised ids, the `draws()` reader of extract_noted_option_truth.do); P2/P3 the pair both orders (D-47-04.b) -- which value is drawn; P4 the alias's abbreviations (D-47-04.c) -- rc, first line, and which picture; P5 a bad value (`symbol(bogus)`, `bcolor(bogus)`, `bmsize(abc)` on pcarrow) -- rc and lines. Run through `scripts/stata_slot.sh`; `git add -f`; register in test_fixtures_are_committed.py. Then re-run `scripts/extract_catchall_options_truth.do` and `scripts/extract_abbrev_truth.do` if its probe list gains the aliases (add them to it).

## TDD test stubs

New `test/test_older_spellings.py`:
- `TestTheFold::test_alias_draws_its_target[mode-alias]` -- the render of `A(v)` equals the render of `T(v)` (glyph properties compared through test_mode_parity's `_figure_profile`) (red).
- `TestTheFold::test_precedence[pair-order]` from alias_truth P2/P3 (red).
- `TestTheFold::test_not_named[alias]` -- no "ignoring unsupported option(s)" note names it (red).
- `TestTheFold::test_mlabels_reaches_the_pattern_rule` -- `mlabels(t*)` and `mlabel(t*)` draw the same (red).
- `TestTheDeclarations::test_spellings_bind_as_twoways[alias-abbrev]` (red).
cscript (test/test_wp47_truth.cscript block `* ==== S04 basic:PT-10: older spellings ====`; refusals in test/test_option_validation.cscript):
- Q4704-1 `dash scatter mpg weight, symbol(Oh)` rc 0, no note; the marker hollow.
- Q4704-2 `dash bar mpg weight, bcolor(red) blwidth(thick)` rc 0, no note.
- Q4704-3 `dash pcarrow mpg weight trunk turn, bmsize(3)` equals `barbsize(3)` (head size).
- Q4704-4 (test_option_validation.cscript) the bad values of P5: rc and first line equal the fixture's.
Pinned flips: test_help_conformance.py count and lists; test_unsupported_report_is_true.py counts; test_twoway_option_parity.cscript rows asserting the note for these names.
Parity: `_case("older spellings symbol bcolor afcolor", ...)`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| fold equals target | TestTheFold; Q4704-1..3 | alias_truth P1 | yes |
| precedence | test_precedence | P2/P3 | yes |
| abbreviations | TestTheDeclarations; test_abbreviations.py | P4, abbrev_truth | n/a |
| refusals | Q4704-4 | P5 | n/a |
| help list | test_help_conformance.py | catchall_options_truth | n/a |

- AC-47-04.1 stubs red at the base, green after; Q4704-1..4 PASS; help-conformance green both ways.

## Tasks

**Commit boundary.** 47-04-01..47-04-03 form one commit, made by 47-04-03, subject `Fold twoway's older spellings onto the options they stand for (WP-47 basic:PT-10)`. Branch `wp47-s04`.

<task type="auto" id="47-04-01">
  <name>Measure aliases and write failing tests</name>
  <files>scripts/extract_alias_truth.do, test/test_older_spellings.py, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_alias_truth.do with P1-P5 for the eleven aliases as "Stata truth" lists; run it through `scripts/stata_slot.sh <scratch> <file>` with DASH_REPO=<worktree>; `git add -f test/fixtures/alias_truth.json`; register it in test/test_fixtures_are_committed.py. Create test/test_older_spellings.py with every stub, reading alias_truth.json. Run `python3 -m pytest test/test_older_spellings.py -q -n0 > <scratch>/47-04-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/47-04-01-failure.txt` prints at least 11; `python3 -c "import json;d=json.load(open('test/fixtures/alias_truth.json'));print(d['symbol']['P1']['same_as_target'])"` prints `True`.]]></verify>
  <done>twoway's reading of each older spelling -- picture, precedence, abbreviations and refusals -- is committed and the fold tests fail against the base.</done>
</task>

<task type="auto" id="47-04-02">
  <name>Fold the aliases onto their targets</name>
  <files>dash.ado, test/test_wp47_truth.cscript, test/test_option_validation.cscript</files>
  <action><![CDATA[Apply TR-47-04.1 and TR-47-04.2 with the measured precedence and abbreviations, with `_dash_fold_alias`'s row in test/program_coverage_map.py. Insert the S04 block (Q4704-1..3) directly above the first `* ==== S06 ` header of test/test_wp47_truth.cscript (47-06's blocks landed in batch 47.2; BRIEF block order) and Q4704-4 to test/test_option_validation.cscript; run both through two-line drivers with `scripts/stata_slot.sh` (`WP47_ONLY=S04`) and test/test_twoway_option_parity.cscript once (flip its rows that assert these names in the note with `// Flipped (WP-47 basic:PT-10)`). Run `python3 -m pytest test/test_older_spellings.py test/test_program_coverage_map.py test/test_mlabel_patterns.py -q -n0` and, after appending the TDD stubs' parity entry `_case("older spellings symbol bcolor afcolor", ...)` to `CORPUS` in test/test_mode_parity.py, parity `-k "older spellings"`. Do not commit (47-04-03 commits).]]></action>
  <verify><![CDATA[pytest 0 failed; logs show Q4704-1..4 PASS and test_twoway_option_parity.cscript's success line.]]></verify>
  <done>Every older spelling is folded onto its target with twoway's precedence and abbreviations, and the section's cscript cases pass.</done>
</task>

<task type="auto" id="47-04-03">
  <name>Regenerate tables, close basic:PT-10</name>
  <files>scripts/gen_twoway_takes_table.py, scripts/extract_abbrev_truth.do, dash.sthlp</files>
  <action><![CDATA[Re-run scripts/extract_catchall_options_truth.do (unedited) and scripts/extract_abbrev_truth.do (with the aliases added to its probe list) through `scripts/stata_slot.sh`; remove `"dlalign"` from `SILENT` in scripts/gen_twoway_takes_table.py (D-47-04.d); `python3 scripts/gen_twoway_takes_table.py` (it rewrites the generated blocks of dash_parse.mata); `git add -f test/fixtures/catchall_options_truth.json test/fixtures/abbrev_truth.json`; the regenerated tw_silent block loses the `dlalign` row and no other row changes except those the folded aliases move (record each moved row in the commit body). dash.sthlp: delete the 'Older spellings' entry (:6514-6518), remove bcolor(), bfintensity(), blpattern(), blwidth(), afcolor(), afintensity() from 'Area, bar and line edge styles' (keep alalign(), blalign(), clalign() -- 47-05's), and in 'Back markers' write "{opt bsymbol()} is {cmd:twoway}'s other spelling of {opt bmsymbol()}, and {opt bmsize()} on {cmd:pcarrow}, {cmd:pcbarrow} and {cmd:pcarrowi} is {cmd:barbsize()}, which dash draws". Add to the marker options synopt list one line: "{cmd:symbol()}, {cmd:msymangle()} and {cmd:mlabels()} are {cmd:twoway}'s older spellings of {cmd:msymbol()}, {cmd:msangle()} and {cmd:mlabel()}, and are read as them; so are {cmd:bcolor()}, {cmd:afcolor()}, {cmd:afintensity()}, {cmd:bfintensity()}, {cmd:blwidth()} and {cmd:blpattern()} for the area and bar options they stand for." Move the Unsupported count pin in test/test_help_conformance.py with `# old -> new: basic:PT-10 the older spellings are read` and the counts in test/test_unsupported_report_is_true.py the same way. Run `python3 -m pytest test/test_help_conformance.py test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_unknown_options.py test/test_older_spellings.py -q -n0`. Close basic:PT-10's BUGS entry (Resolution names syn:SD-11, sil:SD-17, ST-20, DT-20's alias half), Tracked line, GAPS4_OPEN (test/test_tracking_documents.py) line, CHANGELOG under `### Fixed in WP-47`, the item's TWOWAY_COVERAGE_AUDIT.md cells (grep each alias: `symbol(`, `msymangle`, `mlabels`, `bcolor`, `bfintensity`, `blwidth`, `blpattern`, `afcolor`, `afintensity`, `bsymbol`, `bmsize`; rewrite each stale cell to `drawn (WP-47 basic:PT-10)` or `read as <target> (WP-47 basic:PT-10)`). Before the commit take BRIEF's closing steps (1)-(3) for basic:PT-10 (Notes "Before every commit" gives each command in full): (1) delete basic:PT-10's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `basic:PT-10 (documented)` or `basic:PT-10 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py basic:PT-10` and delete every row it prints from its `*_KNOWN` table -- a difference basic:PT-10's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with basic:PT-10. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[pytest 0 failed; `grep -c "Older spellings" dash.sthlp` prints 0; `grep -c '("dlalign"' dash_parse.mata` prints 0; `python3 scripts/gen_twoway_takes_table.py --check` exits 0; `git log -1 --format=%s` ends `(WP-47 basic:PT-10)`.]]></verify>
  <done>The catch-all fixture, the generated tables and the help agree with the folds, and basic:PT-10 is closed in one commit.</done>
</task>

## Section completion criteria

- Stubs green; Q4704-1..4 PASS; the regenerated fixtures and tables committed; pins moved with comments; program_coverage_map.py row.
- Help: the Unsupported entries and the marker-options line; BUGS, GAPS4 Tracked line, CHANGELOG in the one commit.

## Notes

- **Help paragraphs this section owns (R3):** dash.sthlp 'Older spellings', the alias part of 'Area, bar and line edge styles' and 'Back markers' (:6497-6524), one marker-options line.
- **Merge rules touched:** R1, R3, R5, R6, R7, R9, R10, R14.
- **Block order (BRIEF):** S04 goes directly above the first S06 block (47-06 landed in 47.2), never above the marker; `python3 -m pytest test/test_cscript_hygiene.py -k wp47 -q -n0` checks the order.
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp47-s04`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Trap:** `MLabels` is the declared full name, so `mlabel` is itself an abbreviation of it in twoway; declare `mlabels` so that `mlabel`/`ml` keep binding to dash's mlabel and `mlabels` folds onto it -- do not rename dash's `MLabel` declaration (s(mlabel) is read in many places).
- **Commit-body lines:** `Regression: test/test_older_spellings.py::TestTheFold::test_alias_draws_its_target -- failed at <base> with <text>`; `Fixture: test/fixtures/alias_truth.json (scripts/extract_alias_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: basic:PT-10 Tracked`.
