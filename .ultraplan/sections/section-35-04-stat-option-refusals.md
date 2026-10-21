# Section 35-04: Statistical-type refusals twoway makes

> Part of: WP-35 (Accepted syntax and refusals) · Items: stat:PT-1 (TR-7), stat:PT-2, stat:PT-5, stat:PT-8, stat:PT-14 (DT-13) · Risk: yellow · Batch: 35.3 · Depends on: 35-03 · Blocks: 35-07 · Tasks: 6, 5 commits · Case-id prefix: Q3504

## Overview

**What is wrong today.** dash accepts five things twoway refuses (audit package 11; appendix type-options-stat PT-1, PT-2, PT-5, PT-8, PT-14; tracking-tests TR-7; docs-claims DT-13):
- **stat:PT-1/TR-7** histogram with `bins()` and `width()`, or two of density/fraction/frequency/percent: twoway__histogram_gen.ado:27-51 refuses "options bins() and width() may not be combined" and "options `type' may not be combined" (words in the order density fraction frequency percent), r(198); dash draws one of them (dash.ado:4788-4848 checks only discrete with bins()).
- **stat:PT-2** density, fraction, frequency, percent on every type: twoway refuses "option frequency not allowed", r(198), off histogram; dash's flag rules (dash.ado:3772-3774) do not list them.
- **stat:PT-5** contour `levels()` 501-1000 and 500+ cuts from `ccuts()`: drawn, twoway refuses "contour level must be between 0 and 500", r(198) (499 cuts draw, 500 refuse; under nodraw rc 0); dash.ado:2660-2665 bounds at 1000 with its own sentence, and dash.sthlp:596-598 says twoway takes any integer (HR-16, levels()).
- **stat:PT-8** lowess `noweight weight`: twoway "option noweight not allowed", r(198); dash rc 0 and names `weight`, which twoway draws as without it (twoway_lowess_parse.class:37-47).
- **stat:PT-14/DT-13** `bw()` off the bandwidth types: twoway "option bw() not allowed", r(198), on scatter, line, lfit, fpfit, bar, rbar, histogram, dot, spike; dash folds it to barwidth() on the bar family and notes it elsewhere (`_dash_fold_bw` dash.ado:2125-2145; dash.sthlp:3653-3658).

**The maintainer's rulings.** P4-7 (20oct2026): "Unless the options are specific to functionality that only dash provides, the syntax should mirror twoway syntax as close as possible" -- `bw()` read as `barwidth()` on bar/rbar/histogram/dot/spike is refused with twoway's words. P4-9: when dash refuses a synonym it used to accept, the first line is twoway's refusal and a second line names the twoway spelling; for `bw()` on the bar family that line is `use barwidth()`.

**After this section.** Each is refused with twoway's rc and first line, or (bare lowess `weight`) taken silently; `bw()` on the bar family adds P4-9's second line. One section: every fix sits in the statistical-option checks 35-03 left (`_dash_validate_opts`, the flags local, `_dash_contour_check`, `_dash_fold_bw`).

**Test order and commit rule.** 35-04-01 runs GitNexus impact on the functions the section edits, measures twoway (one extract script holding every item's keys) and writes the FIRST item's failing tests only (stat:PT-1), saves `<scratch>/35-04-01-failure.txt` (BRIEF "Failing test first"; the stat:PT-1 commit's body cites it) and does not commit. 35-04-02 fixes and closes stat:PT-1 (commit 1, which also carries the extractor and the fixture). Each later task, 35-04-03 .. 35-04-06, is one item's whole cycle in the manifest's order (stat:PT-2, stat:PT-5, stat:PT-8, stat:PT-14): it first appends that item's own pytest class and its own cscript cases, runs them on the tree before its fix and saves `<scratch>/35-04-<id>-failure.txt` (`:` written `-`), then fixes, closes and commits. So no commit holds a later item's red test (REVIEW R2-7; CLAUDE.md rule 4).

### Section decisions

- **D-35-04.a twoway's order.** Inside `_dash_validate_opts` the histogram checks run as twoway__histogram_gen runs them: discrete+bins() (existing), then bins()+width(), then the scale words. Value errors of bins()/width() (35-05) precede them in twoway's `syntax`; dash keeps its rule loop's order, and the mixed case (a bad value AND a forbidden pair) is not certified -- noted in Notes.
- **D-35-04.b Drawn bounds.** The contour bound is the drawn one (500 levels, 499 cuts), because a dashboard always draws.
- **D-35-04.c bare weight on lowess** is removed from the note list silently (`_dash_tw_silent_tab` cannot express a pair rule, so the fold does it); `weight` beside `noweight` is refused.
- **D-35-04.d bw() per P4-7/P4-9.** Off the bandwidth types `bw()` prints twoway's `option bw() not allowed` and exits 198; on bar, rbar, histogram, dot and spike, where dash read it as `barwidth()`, a second line `      use barwidth()` follows (P4-9, the indentation of dash's later lines); on every other type (where dash only named it in the note, so it was not a synonym) the first line stands alone.
- **D-35-04.e One truth block per item** with a truth-block case: `S04 stat:PT-5` (Q3504-3) and `S04 stat:PT-8` (Q3504-4); the refusal cases Q3504-1, -2, -5 go in test_option_validation.cscript (R1; PD-6).

## Risk: [yellow] -- refusing forms dash accepted (changed behaviour)

**Risk factors.** 1. Existing do-files using `bw()` as barwidth() on the bar family break (documented superset today). 2. contour_truth.json `refuse.levelsbig` was measured under nodraw. 3. 35-05 (same batch) also edits `_dash_option_rules` (the `plot` tokens) and `_dash_validate_opts` (a block after its rule loop); this section edits only the `flags` local and the `_dbin` area -- an R12 overlap the index assigns by part (35.3 note). 4. `_dash_validate_opts` and `_dash_option_rules` run for every plot (high fan-in).

**Mitigation.** 1. CHANGELOG `### Changed behaviour` lines naming the replacement (`barwidth()`), and P4-9's second line at the refusal. 2. The contour extractor's probe is drawn and the fixture regenerated with a diff limited to that key. 3. Disjoint lines; merge 35-04 first (index order), then 35-05 re-reads. 4. 35-04-01 runs GitNexus impact on each edited function; the handback names any HIGH, CRITICAL or UNKNOWN risk.

## Dependencies

- **Depends on:** 35-03 (the fold `_dash_fold_stat_words` and the generator's HANDLED set exist).
- **Blocks:** 35-07 (rows 38 and 42 of its table are ruled here).
- **Parallel batch 35.3:** with 35-05 (value codes and bounds: `_dash_option_rules` `plot` tokens, `_dash_validate_value`, a block at the end of `_dash_validate_opts`).

## Evidence

Anchors at `090d928` (re-read; 35-03 moved some by a few lines): `_dash_validate_opts` :4774, flags loop :4796-4809, `_dbin` :4842-4846; `_dash_option_rules` flags local :3772-3774 (`discrete@histogram  stdp|stdf|stdr@lfitci|qfitci|fpfitci  mean|noweight|adjust|logit@lowess`); `_dash_contour_check` :2603, levels bound :2660-2665, ccuts numlist :2638-2645; `_dash_fold_bw` :2067, `bandwidth_types` :2125, `bar_types` :2126, fold :2135-2142; s() names `density` `fraction` `frequency` `percent` (dash.ado:1594-1598). Help: :596-598 (levels), :3653-3658 (bw()), the Unsupported lowess `weight` line (grep `weight` near :6552). Fixtures: value_truth.json `histogram_freqpct_1` (rc 198, "options frequency percent may not be combined"); contour_truth.json `refuse.levelsbig` (scripts/extract_contour_truth.do:358, nodraw); alias_spelling_truth.json `bw` `barwidth_*`. TWOWAY_COVERAGE_AUDIT.md rows: lowess :93, histogram :98, contour :101, Fill/bar styling :117 (names `barwidth()`).

**Pins to flip (grep in each item's own cycle into `<scratch>/35-04-flips-<id>.txt`):** stat:PT-1 -- `histogram ..., density fraction` drawn; stat:PT-5 -- `levels(1000)` accepted or the "between 0 and 1000" sentence; stat:PT-8 -- `weight` named on lowess (test_unsupported_report_is_true.py LIVE lists; dash.sthlp Unsupported pin in test_help_conformance.py:807, `== 59` at `090d928`: 35-03's stat:PT-6 and 35-06's GW-3 each remove one entry in batch 35.2, so the count at the 35.3 base is expected to be 57 -- re-read it -- and moves to 56 with `# 57 -> 56: WP-35 stat:PT-8 lowess weight taken` if the line goes); stat:PT-14 -- tests asserting `bw()` read as barwidth() on bar/rbar/histogram/dot/spike (grep `bw(` in test/*.py and test/*.cscript) and any test reading alias_spelling_truth.json's `bw` key as dash's binding.

## User stories

- **US-35-04.1** As a Stata user, I want `histogram mpg, bin(10) width(2)` and `histogram mpg, density fraction` refused with twoway's message, so a mistake is caught as in twoway.
- **US-35-04.2** As that user, I want `scatter mpg weight, frequency`, `contour ..., levels(600)`, `lowess mpg weight, noweight weight` and `bar mpg rep78, bw(.5)` refused in twoway's words.
- **US-35-04.3** As that user, I want `lowess mpg weight, weight` drawn silently, as twoway draws it.
- **US-35-04.4** As a user whose do-file wrote `bw()` for a bar width, I want the refusal to tell me to write `barwidth()`.

## Business requirements

- **BR-35-04.1** Every probe the fixture records as refused is refused by dash with the same rc and first line; every probe it records as rc 0 is drawn as twoway draws it, with no note.
- **BR-35-04.2** levels() 0-500 and up to 499 cuts draw; dash's own 1,000 sentence is gone; the help states twoway's bound.
- **BR-35-04.3** `bw()` on bar, rbar, histogram, dot and spike is refused with twoway's first line and a second line naming `barwidth()` (P4-9).

## Technical requirements

- **TR-35-04.1 stat:PT-1.** After the `_dbin` block in `_dash_validate_opts`: `mata: st_local("_dbw", strofreal(st_global("s(bin)") != "" & st_global("s(width)") != ""))`; `if `_dbw' & "`ptype'" == "histogram" { display as error "options bins() and width() may not be combined"; exit 198 }`; then `local _htype ""`, `foreach f in density fraction frequency percent { if `"`s(`f')'"' != "" local _htype "`_htype' `f'" }`, `if `: word count `_htype'' > 1 { local _htype : list retokenize _htype; display as error "options `_htype' may not be combined"; exit 198 }`.
- **TR-35-04.2 stat:PT-2.** Flags local: append `density|fraction|frequency|percent@histogram` (one token) after `discrete@histogram`. The existing loop prints `option <f> not allowed`.
- **TR-35-04.3 stat:PT-5.** `_dash_contour_check`: replace the `> 1000` branch by `if `_zl' > 500 { display as error "contour level must be between 0 and 500"; exit 198 }` (the literal from the fixture key `contour.levels_501`); after the ccuts numlist: `if `: word count `r(numlist)'' >= 500` -> the same line, exit 198 (fixture `contour.ccuts_500`). scripts/extract_contour_truth.do:358: remove `nodraw` from that probe; regenerate `test/fixtures/contour_truth.json` through its script; `git diff --stat` must show only that file, and a `python3 -c` comparison must show only `refuse.levelsbig` and `_meta` changed (else stop and report it to the orchestrator in the handback).
- **TR-35-04.4 stat:PT-8.** In `_dash_fold_stat_words` (35-03's program): on lowess, a bare token `weight` in s(_unknown) is removed; when `s(noweight)` is also set the fold records it (`c_local _fsw_nowt 1`) and prints nothing (else the removal is silent). The refusal is given on a new line directly after 35-03's subchar() refusal lines, which follow the fold's second call after the `_dash_refuse_asp` line in `_dash_process_segment` (re-read at the batch base; the second call sets the record again after `_dash_refuse_unknown`'s re-parse), so an unknown word typed earlier is named first, as twoway names it (WP-32 order, 35-03's D-35-03.c): `if "`_fsw_nowt'" == "1" { display as error "option noweight not allowed"; exit 198 }` (fixture `lowess.noweight_weight`), with `local _fsw_nowt ""` set beside 35-03's `local _fsw_subc ""` before the fold call. Generator: add `weight` to `HANDLED` if a tw_takes or tw_silent row carries it on lowess; regenerate; `--check`. Remove the Unsupported line's `weight` (R3).
- **TR-35-04.5 stat:PT-14 (P4-7, P4-9).** `_dash_fold_bw`: delete the `bar_types` branch's fold to `s(barwidth)` and the else branch's move to `s(_unknown)`; for every type not in `bandwidth_types`: `display as error "option bw() not allowed"` (fixture `bw.<type>`); then, only when the type is in the kept list `bar_types` ("bar rbar histogram dot spike"), `display as error "      use barwidth()"` (P4-9); exit 198. Help :3653-3658 rewritten: "{opt bw()} is {opt bwidth()} on {cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci} and {cmd:kdensity}; elsewhere it is refused, as {cmd:twoway} refuses it ({opt barwidth()} sets a bar's width)."
- **TR-35-04.6 Both modes.** Refusals happen in Stata before any spec; nothing to render. The one acceptance (bare lowess `weight`) registers the same spec as no `weight` (Q3504-4), which both renderers read, so no parity entry is needed (REVIEW R2-6).

## Boundaries

The `plot` rule tokens, `_dash_validate_value` and the end-of-loop block of `_dash_validate_opts` (35-05); the dash-only words (35-07); `_dash_fold_stat_words`'s 35-03 branches (only the `weight` branch is added); renderers.

## Stata truth

**New extractor** `scripts/extract_stat_refusal_truth.do` -> `test/fixtures/stat_refusal_truth.json` (model: extract_noted_option_truth.do; twoway, drawn, `sysuse auto` / `sysuse sandstone`; rc and first line). It holds every item's keys and is created once, in 35-04-01:

| Key | Command |
|---|---|
| `hist.bins_width` | `histogram mpg, bin(10) width(2)` |
| `hist.<a>_<b>` | `histogram mpg, density fraction`; `fraction percent`; `frequency density`; `percent frequency`; `density fraction frequency` |
| `flag.<type>.<f>` | `<type> ... , <f>` for f in density fraction frequency percent, type in scatter, line, lfit, kdensity, function (`function y=x`), bar |
| `contour.levels_500`, `levels_501`, `levels_1000` | `contour depth northing easting, levels(N)` drawn |
| `contour.ccuts_499`, `ccuts_500` | `ccuts()` of 499 / 500 values spanning depth's range (built with `numlist`) |
| `lowess.weight`, `lowess.noweight_weight` | `lowess mpg weight, weight`; `noweight weight`; plus the serset equality of `weight` with none |
| `bw.<type>` | `bw(2)` on scatter, line, lfit, fpfit, bar (`bar mpg rep78`), rbar, histogram, dot, spike |

**Cases.** Refusal cases go in test_option_validation.cscript (R1: "refusal ... cases go in the existing cscript for their area"), after its last case and before `// Summary`, with header lines in its `*!` list, each with `_u46_rc` plus `_ov_said` for the line: **Q3504-1** (stat:PT-1) the histogram pairs, dash rc/line = fixture; **Q3504-2** (stat:PT-2) the flag grid; **Q3504-5** (stat:PT-14) the bw() grid -- the first line equals the fixture's on every type, and the second line is `use barwidth()` on bar, rbar, histogram, dot and spike and absent elsewhere. Truth blocks in `test/test_wp35_truth.cscript`, gated `WP35_ONLY=S04`, the first inserted directly above the first block whose S<MM> is higher than S04 (S06 landed in batch 35.2), the second directly below it (BRIEF Block order; REVIEW R2-20): `* ==== S04 stat:PT-5: contour levels bounded at twoway's 500 ====` -- **Q3504-3** contour bounds (500 and 499 cuts register; 501/1000/500 cuts refused); `* ==== S04 stat:PT-8: lowess weight taken silently, noweight weight refused ====` -- **Q3504-4** lowess weight silent (no `ignoring` line; spec equals the no-weight spec) and the pair refused.

## TDD test stubs

Each item's tests are written in that item's own cycle (Test order and commit rule), in test/test_stat_refusals.py and its cscript cases:
- stat:PT-1 (35-04-01): `test/test_stat_refusals.py::TestTheFixture::test_readings` (guard, green once the fixture exists); `::TestTheHistogramPairs::test_checks_in_twoways_order` (red: the bins()+width() line follows the `_dbin` check in `_dash_validate_opts`); cscript Q3504-1 (red).
- stat:PT-2 (35-04-03): `::TestTheFlags::test_scale_words_are_histograms` (red: the flags local has no `density|fraction|frequency|percent@histogram` token); cscript Q3504-2 (red).
- stat:PT-5 (35-04-04): `::TestTheContourBound::test_500_and_499` (red: `_dash_contour_check` holds the 1000 bound); cscript Q3504-3 (red).
- stat:PT-8 (35-04-05): cscript Q3504-4 (red) and the flipped LIVE-list pin.
- stat:PT-14 (35-04-06): `::TestTheBw::test_no_barwidth_fold` (red: `_dash_fold_bw` still writes `s(barwidth)`); `::TestTheBw::test_the_hint_names_barwidth` (red: the refusal's second line `use barwidth()` is printed only for `bar_types`); cscript Q3504-5 (red).

Flips per each item's grep. Parity corpus (R8): none -- these are Stata-side refusals before any spec, and the lowess `weight` acceptance registers the no-weight spec (Q3504-4), which both renderers read (REVIEW R2-6).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| refusals | Q3504-1, -2, -5 (option validation cscript), Q3504-3 (S04 stat:PT-5) | stat_refusal_truth.json | n/a |
| bw() hint line | Q3504-5, pytest TestTheBw | stat_refusal_truth.json | n/a |
| silent weight | Q3504-4 (S04 stat:PT-8) | stat_refusal_truth.json | spec shared |
| code shape | pytest test_stat_refusals.py | -- | n/a |

**Acceptance criteria.** **AC-35-04.1** `WP35_ONLY=S04` and test_option_validation.cscript print Q3504-1..5 PASS and `ALL CHECKS PASSED`. **AC-35-04.2** `python3 -m pytest test/test_stat_refusals.py test/test_help_conformance.py test/test_unsupported_report_is_true.py -q -n0` 0 failed. **AC-35-04.3** the regenerated contour_truth.json differs only in `refuse.levelsbig` and `_meta`.

## Tasks

**Commit boundary.** Five commits on `wp35-s04` (`$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp35-s04`), one per item, made by its closing task: 35-04-01..02 `Refuse histogram's exclusive options in twoway's words (WP-35 stat:PT-1)`; 35-04-03 `Refuse histogram's scale words on other types (WP-35 stat:PT-2)`; 35-04-04 `Bound contour levels at twoway's drawn 500 (WP-35 stat:PT-5)`; 35-04-05 `Refuse lowess noweight with weight; take weight silently (WP-35 stat:PT-8)`; 35-04-06 `Refuse bw() off the bandwidth types (WP-35 stat:PT-14)`. Bodies per BRIEF, each with its own `Regression:` lines (its own pytest node and Q3504 case, with the text of its own failure file: `<scratch>/35-04-01-failure.txt` for stat:PT-1, `<scratch>/35-04-<id>-failure.txt` for each later item), `Flipped:` lines, the line `Ledger: <n> rows of <id> removed; known differences: <m> rows removed` and its GitNexus risk from `<scratch>/35-04/anchors.txt`; the first carries `Fixture: test/fixtures/stat_refusal_truth.json (scripts/extract_stat_refusal_truth.do)`, stat:PT-5's also `Fixture: test/fixtures/contour_truth.json (scripts/extract_contour_truth.do)`. Each commit carries its CHANGELOG line under `### Changed behaviour (may need your do-files changed)` (P4-7: every newly refused form; the exact text is in its task), its TWOWAY_COVERAGE_AUDIT.md tag, BUGS/GAPS4 closure and `GAPS4_OPEN` deletion, and stages only its own item's tests, cases and code. "Close" means: BUGS.md Resolution in PD-4's closed form and `- [x]`; GAPS4.md Tracked line `Closed in WP-35, BUGS.md "<title>", commit pending.`; the id's line deleted from `GAPS4_OPEN` in test/test_tracking_documents.py; `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q -n0` 0 failed.

"Clear `<id>`" below means BRIEF's closing steps (1)-(3) ("The corpus ledger and the known-differences tables"; D-33-05.i, D-33-10.a/b/h, D-33-09.c), run in `$WT` for the item's lead id `<id>` before staging; every item here closes `Closed` and so should have no `(documented)` or `(residual)` row (one would be dead once its item closes: hand it back instead of keeping or deleting it); D-33-10.b keys `stat:PT-1`, `-2`, `-5`, `-8` and `-14` rows in these tables, value_truth.json's `histogram_freqpct_1` under stat:PT-1 among them, and steps (1) and (2) take the plain rows of the item's other ids too (TR-7 for stat:PT-1, DT-13 for stat:PT-14): (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do` and read `<scratch>/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). After step (2), also run `WP33_ONLY=S10` of test_wp33_truth.cscript through the same driver: a row keyed to another id that S10 reports as now agreeing (known_problems rule 2: this fix fixed it) is deleted too and named in the body; a deleted row whose difference S10 still reports (rule 1) means the fix is incomplete -- fix the code, never put the row back. Then pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main). Each closing task's verify includes `test/test_corpus_ledger.py` 0 failed, `python3 test/known_differences.py <id>` printing no `<file>:<line>` row with its hygiene command 0 failed, `Q3309-1 PASS` in `<scratch>/run_test_wp33_truth.log`, and `WP33_ONLY=S10` printing `Q3310-1 PASS` and `Q3310-2 PASS`. Every commit task, after staging, runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) into `<scratch>/35-04/detect-<id>.txt`, writes the message to a file, checks `grep -Eic 'claude|anthropic'` prints 0, commits with `git commit -F` and re-runs the grep on `git log -1 --format=%B`.

<task type="auto" id="35-04-01">
  <name>Measure the refusals; write stat:PT-1's failing tests</name>
  <files>scripts/extract_stat_refusal_truth.do, test/fixtures/stat_refusal_truth.json, test/test_stat_refusals.py</files>
  <action><![CDATA[
    Check the branch `wp35-s04` holds 35-03's six commits. From `$WT` run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for `_dash_validate_opts`, `_dash_option_rules`, `_dash_contour_check`, `_dash_fold_bw`, `_dash_fold_stat_words`, `_dash_process_segment` (the noweight refusal line), `rows` (scripts/gen_twoway_takes_table.py) and `_dash_tw_takes_tab` (the generator's HANDLED set may gain `weight`), writing callers, processes and risk to `<scratch>/35-04/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the handback; UNKNOWN confirmed with `grep -n`). Create and run the extractor; `git add -f`. Create test/test_stat_refusals.py with stat:PT-1's two nodes only and Q3504-1 in test/test_option_validation.cscript (after its last case, before `// Summary`, with its `*!` header line). Run pytest and that cscript through the two-line driver; save the FAIL lines to `<scratch>/35-04-01-failure.txt`; grep stat:PT-1's pins into `<scratch>/35-04-flips-stat-PT-1.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[Fixture: `hist.bins_width.rc` 198, `contour.levels_501.rc` 198, `contour.levels_500.rc` 0, `bw.bar.rc` 198; pytest 1 failed 1 passed; Q3504-1 FAIL; `test -s <scratch>/35-04-01-failure.txt` and `test -s <scratch>/35-04/anchors.txt`.]]></verify>
  <done>twoway's refusals for all five items were recorded drawn, and stat:PT-1's tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="35-04-02">
  <name>Fix and close stat:PT-1</name>
  <files>dash.ado, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    TR-35-04.1; the histogram help paragraph (grep `options discrete and bins()` in dash.sthlp) gains the two refusals; flip the pins listed. TWOWAY_COVERAGE_AUDIT.md histogram row (:98): append `[WP-35 stat:PT-1: corrected -- bin() with width(), and two of density, fraction, frequency and percent, refused in twoway's words]`. CHANGELOG: `- histogram with bin() and width(), or with two of density, fraction, frequency and percent, is refused, r(198), in twoway's words ("options bins() and width() may not be combined", "options density fraction may not be combined"); dash drew one of them. (WP-35, stat:PT-1)`. Run Q3504-1 and test_stat_refusals.py. Close; Clear stat:PT-1 (steps (1)-(3): stat:PT-1's plain ledger rows, `python3 test/known_differences.py stat:PT-1` and its hygiene command, the S09 guard; then `WP33_ONLY=S10`; value_truth.json's `histogram_freqpct_1` row of VALUE_KNOWN goes with it); pull (`git -C $WT pull --ff-only . main`); stage the extractor, the fixture, the pytest file, Q3504-1 and the fix; detect-changes; commit (the body cites `<scratch>/35-04-01-failure.txt`).
  ]]></action>
  <verify><![CDATA[Q3504-1 PASS; pytest 0 failed; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py stat:PT-1` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; `grep -c '"histogram_freqpct_1"' test/value_truth_known.py` prints 0; `git log -1 --format=%s` ends `(WP-35 stat:PT-1)`; `grep -c "(WP-35, stat:PT-1)" CHANGELOG.md` prints 1.]]></verify>
  <done>histogram's exclusive options were refused in twoway's words, closed in their own commit.</done>
</task>

<task type="auto" id="35-04-03">
  <name>Test, fix and close stat:PT-2</name>
  <files>dash.ado, test/test_stat_refusals.py, dash.sthlp</files>
  <action><![CDATA[
    Append `TestTheFlags::test_scale_words_are_histograms` and Q3504-2 (test/test_option_validation.cscript, after Q3504-1); run both before the fix and save to `<scratch>/35-04-stat-PT-2-failure.txt`; grep the pins. Then TR-35-04.2; the flags help sentence (grep `switch that belongs to one plot type`) lists density, fraction, frequency and percent as histogram's; flip. TWOWAY_COVERAGE_AUDIT.md histogram row (:98): append `[WP-35 stat:PT-2: corrected -- density, fraction, frequency and percent refused off histogram]`. CHANGELOG: `- density, fraction, frequency and percent are refused off histogram, r(198), "option frequency not allowed", as twoway refuses them; dash accepted them. (WP-35, stat:PT-2)`. Run Q3504-2 and test_stat_refusals.py. Close; Clear stat:PT-2 (steps (1)-(3): stat:PT-2's plain ledger rows, `python3 test/known_differences.py stat:PT-2` and its hygiene command, the S09 guard; then `WP33_ONLY=S10`); pull (`git -C $WT pull --ff-only . main`); stage; detect-changes; commit.
  ]]></action>
  <verify><![CDATA[Before the fix: 1 failed and Q3504-2 FAIL, saved. After: Q3504-1, Q3504-2 PASS; pytest 0 failed; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py stat:PT-2` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-35 stat:PT-2)`.]]></verify>
  <done>histogram's scale words were refused elsewhere in twoway's words, closed in their own commit.</done>
</task>

<task type="auto" id="35-04-04">
  <name>Test, fix and close stat:PT-5</name>
  <files>dash.ado, scripts/extract_contour_truth.do, test/fixtures/contour_truth.json</files>
  <action><![CDATA[
    Append `TestTheContourBound::test_500_and_499` to test/test_stat_refusals.py and the `S04 stat:PT-5` block (Q3504-3) to test/test_wp35_truth.cscript at the place "Stata truth" names; run both before the fix and save to `<scratch>/35-04-stat-PT-5-failure.txt`; grep the pins. Then TR-35-04.3 (bound, ccuts count, the extractor's probe drawn, the fixture regenerated and diffed); rewrite dash.sthlp:596-598 to "{opt levels()} above 500, and more than 499 values in {opt ccuts()}, are refused, as {cmd:twoway} refuses them when it draws ({cmd:contour level must be between 0 and 500})" (HR-16's levels() sentence); flip. TWOWAY_COVERAGE_AUDIT.md contour row (:101): append `[WP-35 stat:PT-5: corrected -- levels() above 500 and 500 or more ccuts() refused, as twoway refuses them when it draws]`. CHANGELOG: `- contour levels() above 500 and ccuts() with 500 or more values are refused, r(198), "contour level must be between 0 and 500", as twoway refuses them when it draws; dash drew up to 1,000. (WP-35, stat:PT-5)`. Run Q3504-3 and test_stat_refusals.py. Close; Clear stat:PT-5 (steps (1)-(3): stat:PT-5's plain ledger rows, `python3 test/known_differences.py stat:PT-5` and its hygiene command, the S09 guard; then `WP33_ONLY=S10`); pull (`git -C $WT pull --ff-only . main`); stage; detect-changes; commit.
  ]]></action>
  <verify><![CDATA[Before the fix: 1 failed and Q3504-3 FAIL, saved. After: Q3504-3 PASS; `grep -c "between 0 and 1000" dash.ado dash.sthlp` prints 0 for each; the fixture diff check of TR-35-04.3 passes; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py stat:PT-5` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-35 stat:PT-5)`.]]></verify>
  <done>contour's drawn bound was twoway's, closed in its own commit.</done>
</task>

<task type="auto" id="35-04-05">
  <name>Test, fix and close stat:PT-8</name>
  <files>dash.ado, scripts/gen_twoway_takes_table.py, dash.sthlp</files>
  <action><![CDATA[
    Add the `S04 stat:PT-8` block (Q3504-4) to test/test_wp35_truth.cscript directly below the S04 stat:PT-5 block and flip the LIVE-list pin of test/test_unsupported_report_is_true.py that names lowess `weight`; run both before the fix and save to `<scratch>/35-04-stat-PT-8-failure.txt`. Then TR-35-04.4 (the `weight` branch's record and its refusal line after `_dash_refuse_asp`, the generator and its regenerated `_dash_tw_takes_tab` in dash_parse.mata, the Unsupported line). If the Unsupported line goes, move test/test_help_conformance.py's pin (:807) from the count at the 35.3 base (expected 57: 35-03's stat:PT-6 and 35-06's GW-3 each took one entry in batch 35.2; re-read it) to 56 with `# 57 -> 56: WP-35 stat:PT-8 lowess weight taken` (R10; another base count n is written `# n -> n-1`). TWOWAY_COVERAGE_AUDIT.md lowess row (:93): append `[WP-35 stat:PT-8: corrected -- weight taken silently; noweight with weight refused]`. CHANGELOG: `- lowess noweight with weight is refused, r(198), "option noweight not allowed", as twoway refuses it; lowess weight alone is drawn with no note, as twoway draws it (dash named it in the note). (WP-35, stat:PT-8)`. Run Q3504-4, test_unsupported_report_is_true.py, test_help_conformance.py, `gen_twoway_takes_table.py --check`. Close; Clear stat:PT-8 (steps (1)-(3): stat:PT-8's plain ledger rows, `python3 test/known_differences.py stat:PT-8` and its hygiene command, the S09 guard; then `WP33_ONLY=S10`); pull (`git -C $WT pull --ff-only . main`); stage; detect-changes; commit.
  ]]></action>
  <verify><![CDATA[Before the fix: Q3504-4 FAIL, saved. After: Q3504-4 PASS; the pytest files 0 failed; `--check` exits 0; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py stat:PT-8` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-35 stat:PT-8)`.]]></verify>
  <done>lowess's weight pair was twoway's, closed in its own commit.</done>
</task>

<task type="auto" id="35-04-06">
  <name>Test, fix and close stat:PT-14</name>
  <files>dash.ado, test/test_stat_refusals.py, dash.sthlp</files>
  <action><![CDATA[
    Append `TestTheBw::test_no_barwidth_fold`, `TestTheBw::test_the_hint_names_barwidth` and Q3504-5 (test/test_option_validation.cscript, after Q3504-2); run both before the fix and save to `<scratch>/35-04-stat-PT-14-failure.txt`; grep the pins. Then TR-35-04.5 (D-35-04.d: twoway's line, and `      use barwidth()` on bar_types only); flip each pin with a `Flipped:` line: "bw() read as barwidth() was wrong because twoway refuses bw() off the bandwidth types (P4-7)". TWOWAY_COVERAGE_AUDIT.md Fill/bar styling row (:117): append `[WP-35 stat:PT-14: corrected -- bw() is not barwidth(); it is refused off the bandwidth types, as twoway refuses it]`. CHANGELOG: `- bw() off lowess, lpoly, lpolyci and kdensity is refused, r(198), "option bw() not allowed", as twoway refuses it; on bar, rbar, histogram, dot and spike dash read it as barwidth() (the refusal's second line now says "use barwidth()"), and elsewhere named it in the note. (WP-35, stat:PT-14)`. Run Q3504-5, `WP35_ONLY=S04`, test_option_validation.cscript, test_stat_refusals.py. Close; Clear stat:PT-14 (steps (1)-(3): stat:PT-14's plain ledger rows, `python3 test/known_differences.py stat:PT-14` and its hygiene command, the S09 guard; then `WP33_ONLY=S10`); pull (`git -C $WT pull --ff-only . main`); stage; detect-changes; commit.
  ]]></action>
  <verify><![CDATA[Before the fix: 2 failed and Q3504-5 FAIL, saved. After: Q3504-1..5 PASS; `grep -c 'barwidth : copy local bw' dash.ado` prints 0; pytest 0 failed; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py stat:PT-14` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; `git -C $WT log --format=%s s3-bugs..HEAD | grep -c '(WP-35 '` prints 5 (the branch's commits since its batch base: this section's five, and no earlier batch's).]]></verify>
  <done>bw() was refused off the bandwidth types as twoway refuses it, with the barwidth() hint where dash had read it so, and the section's five commits were ready, each green.</done>
</task>

## Section completion criteria

Five commits, each holding only its own item's tests and each green; S04's two blocks and the option-validation cases green; two fixtures (one new, one regenerated) committed and named by tests; each item's plain rows gone from ledger.tsv and from every `*_KNOWN` table (`python3 test/known_differences.py <id>` prints none; any key a ruling kept in its table's deliberate dict), the S09 guard at `Q3309-1 PASS`, with test_corpus_ledger.py and `WP33_ONLY=S10` green; help :596-598 and :3653-3658 true; TWOWAY_COVERAGE_AUDIT.md tagged per item; P4-7's CHANGELOG lines present; GitNexus impact and detect-changes recorded.

## Notes

- **Mixed errors.** twoway's `syntax` validates bins()/width() values before the pair checks; dash's rule loop runs after `_dash_validate_opts`'s pair checks. `histogram mpg, bin(0) width(2)` may give the pair line in dash and r(125) in twoway; not certified here (35-05 owns value codes). Recorded in the BUGS Resolution as a known order difference only if Q3504-1's extra probe shows it.
- **HR-16 (levels())** is corrected here (Appendix B).
- **Rows 38 and 42 of 35-07's table** (bw()) are ruled and implemented here (P4-7); 35-07 does not touch `_dash_fold_bw`.
- **Help paragraphs owned (R3):** :596-598, :3653-3658, the histogram refusal paragraph, the switch paragraph, the lowess weight Unsupported line.
- **R12:** batch 35.3 has two editors of `_dash_option_rules` (this section's flags local, 35-05's plot tokens) and of `_dash_validate_opts` (this section's `_dbin` area, 35-05's block after the rule loop) -- the index's 35.3 note; the hunks are disjoint; merge 35-04 first.
- **Merge rules:** R1, R5, R7, R9, R10 (the Unsupported count, read at the 35.3 base), R12, R13 (GitNexus). No R8 entry (no twin).
- **Functions edited** (for the index's Owns cell): `_dash_validate_opts` (`_dbin` area), `_dash_option_rules` (flags local), `_dash_contour_check`, `_dash_fold_bw`, `_dash_fold_stat_words` (weight branch), `_dash_process_segment` (the noweight refusal line beside 35-03's subchar() lines, after `_dash_refuse_asp`; 35-05 edits the program elsewhere in batch 35.3, after the `_dash_validate_opts` call), scripts/extract_contour_truth.do, scripts/gen_twoway_takes_table.py `rows()` and the generated `_dash_tw_takes_tab`.
- **Refusal order (WP-32).** The noweight refusal is given after `_dash_refuse_unknown`, as 35-03 gives subchar()'s, so `lowess mpg weight, bogus noweight weight` names `bogus` first, as twoway does.
