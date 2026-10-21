# Section 42-04: coloruseplegend key, legend() isolation, colorkeysreverse

> Part of: WP-42 (Colour variables, audit package 7) · Items: CV-4, CV-5, CV-11 (CV-12) · Risk: yellow · Batch: 42.5 · Depends on: 42-03 · Blocks: WP-42 WE · Tasks: 6, 3 commits · Case-id prefix: Q4204

## Overview

**What is wrong today.**

- **CV-4.** The coloruseplegend key: twoway draws "a framed box (white fill, black frame). Levels run top to bottom as 5 4 3 2 1 Other, and there is no title (K5, D13, T2, T6, X1). Missing values are 'Other' (colorotherlabel overrides it). Texts are string(cut, variable format), not value labels: foreign gives '1','0' (K6). legend(rows(1)), legend(size(huge)) and legend(off) leave it unchanged (M4, Q3, M3). Under colorkeysrange it keeps marker swatches (C28)." dash: the clegend's Legend -- ascending, '(missing)' (`_other_label or "(missing)"`, dash_render.py:16605-16606), titled with the variable label (`title=var_display`, :16698), value labels, nrows=1 under legend(rows(1)), 20pt under legend(size(huge)), Quads under colorkeysrange (`_swatch`, :16581-16589).
- **CV-5.** legend(size()) and legend(rows()/cols()) restyle the colour key: `_dash_apply_legend` applies rows()/cols() to `cv_legends` (:39703-39713) and size() to every `fig.legend` (:39715-39735). twoway's keys keep 99.99 SVG units and stay vertical (Q0-Q3, P12, M4).
- **CV-11 (CV-12).** colorkeysreverse on a discrete key: twoway reverses only the swatch colours ("The labels stay at 1 (bottom) to 5 (top) and the swatch colours flip, so level 1's #0000ff sits beside '5'"; R1, D12); dash reverses the entries with their labels (`legend_items.reverse()` :16598-16599). colorlevels() over one value: twoway's cuts all equal the value (diff 0; key '3','3', markers #0000ff); dash widens to lo + 1 (`edge_hi = ... lo_v + 1.0`, :14228) and labels '3–3.33333', '3.33333–3.66667', '3.66667–3'.

**After this section.** The coloruseplegend key is twoway's plot-legend box, descending with "Other", untitled, numbers in the variable's display format, marker swatches, untouched by legend(); legend()'s size and grid steps leave every colour key alone; colorkeysreverse reverses the key's colours only; a one-value colorvar cuts at zero width and keys as twoway. Both modes, before and after a move.

**Why one section.** All three are the colour key's interplay with the plot legend and its order, after 42-03 made the clegend an axis key and left the Legend only under coloruseplegend.

**Test order and commit rule.** Three items, three commits, in manifest order (CV-4, CV-5, CV-11); each a tests task (no commit) then a fix-and-commit task.

### Section decisions

- **D-42-04.a coloruseplegend's Legend.** Items in descending level order, then the gray item labelled `colorotherlabel()` or `Other`; `title` None; label text `_dash_fmt_text(level, <the colour variable's display format>)` (its Stata format from `self.var_formats` -- grep the renderer's per-variable format map) unless `zlabel(, valuelabel)`; `border_line_color` black, `background_fill_color` white (or the scheme's legend box colours if the fixture shows them under stcolor); swatches always the layer's marker (colorkeysrange ignored there, C28).
- **D-42-04.b legend() isolation.** `_dash_apply_legend` excludes `cv_legends` (and key cells, which are not Legends) from the rows()/cols() step and the size() step; legend(off) already leaves them (M3 matches).
- **D-42-04.c colorkeysreverse.** On the axis key (42-03's cell) the swatch colours are reversed against the levels; labels, positions and the plotted colours unchanged. Under coloruseplegend it changes nothing (twoway's plot legend keeps its order, D13r). Relevel: the plan's `rev` flag reverses the colours the key cell takes (`_dash_cvar_keycell_update`, both twins).
- **D-42-04.d Zero-width cuts.** `_dash_colorvar_cuts` with `levels` and `hi_v == lo_v`: `diff = 0`, cuts `[lo_v] * (cnt - 1)` kept as a list with repeats (no `set()`), as twoway's `forvalues` writes them; minmax adds `lo_v` twice. The binning (`searchsorted`) is unchanged by repeats; the key labels every cut, so '3','3'. The JS twin's levels rule does the same.

## Risk: [yellow] -- key order and legend() rules change; one more twin edit

**Why.** CV-4 reverses the order users see; CV-5 changes what legend() touches; CV-12 changes the cut helper both twins share.

**Risk factors.** 1. Tests pin ascending coloruseplegend entries and "(missing)". 2. The legend size step is shared with the plot legend. 3. Repeats in the cut list may break code that assumes strictly increasing cuts (the stepped mapper's step computation).

**Mitigation.** 1. The flip list from 42-04-01's base run. 2. A test that the plot legend still takes legend(size(huge)). 3. Repeats only on the colorlevels path with a one-value domain; the stepped path never sees them (its cuts come from ticks); a test covers interval labels with repeats.

## Dependencies

- **Depends on:** 42-03 (the axis key; the Legend left only for coloruseplegend; `_dash_cvar_keycell_update`).
- **Blocks:** WP-42's WE.
- **Parallel batch 42.5:** alone (DECISIONS A-11); editor of `_dash_apply_legend`, `_apply_colorvar`, `_DASH_CVAR_RELEVEL_JS` this batch (R12; the manifest marks it JS = yes for CV-12's twin and colorkeysreverse's relevel). Builds on 42-05 (batch 42.3: `_dash_colorvar_cuts`' `cnt` form and its JS twin) and 42-03 (batch 42.4: the key cell).

## Evidence

- coloruseplegend path: `_apply_colorvar` :16591-16607 (items, order, missing item), :16698 (title), :16711-16725 (plegend placement through `_dash_clegend_opts(_pleg)`) -- re-read after 42-03, which moved the non-plegend key to the cell.
- `_dash_apply_legend` :39310; `cv_legends` :39359-39361; rows/cols :39703-39713; size :39715-39735.
- `_dash_colorvar_cuts` :14227-14230 (after 42-05: the `cnt` form); JS `dash_cvar_relevel_bins` levels rule :44144-44147.
- twoway: the audit's K5, K6, M3, M4, Q0-Q3, P12, C28, R1, D12, D13r, I5, I3; committed: colorvar_options_truth.json D12 (reversed colours), D13/D13r (coloruseplegend order), D05p (plegend 'rest').
- Pins (flip, never delete): test/test_colorvar_options.py::TestKeys::test_reverse (pins label reversal; :343), ::TestOtherlabel::test_label (:364), ::TestPlegend::test_off (:401, stays), the coloruseplegend tests near :498 (grep `coloruseplegend` in test/test_colorvar_options.py); test/test_colorvar_legend.py::TestTheSchemeChromeIsStillApplied::test_an_explicit_legend_size_still_wins (:179-185: asserts legend size reaches the colour key -- flips for CV-5); test/test_colorkeysreverse_bar.py::TestTheMeasurement (:43-71, stays as truth); test/test_function_audit.py TestColorLevelsPutEachPointInItsLabelledBin (CV-12 labels).

## User stories

- US-42-04.1 As a Stata user, I want `colordiscrete coloruseplegend` keyed 5 4 3 2 1 Other in a framed plot legend, as twoway draws it.
- US-42-04.2 As a Stata user, I want legend(size(huge)) and legend(rows(1)) to restyle only the plot legend.
- US-42-04.3 As a Stata user, I want colorkeysreverse to flip the key's colours, not its labels, and a one-value colorvar keyed as twoway keys it.

## Business requirements

- BR-42-04.1 The coloruseplegend key's order, texts, title, frame and swatches match twoway's probes.
- BR-42-04.2 legend()'s size and grid sub-options never change a colour key.
- BR-42-04.3 colorkeysreverse reverses the key's colours only; colorlevels() over one value draws twoway's key and colours.
- BR-42-04.4 All of it holds after a filter move, saved and served.

## Technical requirements

- TR-42-04.1 `_apply_colorvar` coloruseplegend branch: D-42-04.a (order, "Other", title None, labels, frame, marker swatch). The `_dash_cvar` plan's `items`/`miss` order follows (descending), so `_dash_cvar_relevel` (:52272-52370) and the JS `dash_cvar_relevel` keep it: add `"desc": True` to the plan and reverse the kept items there when set (both twins).
- TR-42-04.2 `_dash_apply_legend`: rows()/cols() loop (:39703-39713) iterates `plot_legends` only; size() step (:39715-39735) skips `lg in cv_legends`.
- TR-42-04.3 colorkeysreverse on the key cell: the cell spec's level colours reversed (`spec["levels"]` colours in reverse order against the same levels) when `_keys_rev and not _use_plegend`; the plan's `rev` reverses the colours in `_dash_cvar_keycell_update` (Python) and `dash_cvar_keycell_update` (JS). The old `legend_items.reverse()` lines (:16598-16599, :16617-16618, :16648-16649) are removed.
- TR-42-04.4 `_dash_colorvar_cuts`: D-42-04.d; `_dash_colorvar_bins`' interval labels with repeated cuts: labels per cut as twoway's z axis labels (the binned key labels the cuts, 42-03); the JS levels rule: `if (hi === lo) { for (i = 1; i < cnt; i++) eff.push(lo); }` and skip the `Set` de-duplication in that case.
- TR-42-04.5 function_test_map.py: existing entries; no new function unless the executor extracts one (then a row and a copy-list entry after `"_dash_cvar_relevel_steps", "_dash_cvar_kept",`, dash_render.py:67715).

## Boundaries

- Not the key cell's form (42-03), the cut rule under colordiscrete (42-05), by() keys (41-04). Help paragraphs owned (R3): dash.sthlp:5463-5466 (colorotherlabel, coloruseplegend synopts), :5518-5523 (colorkeysreverse), :5624 ("A colorvar() key is not the legend: it stays" -- extended with legend()'s size and grid).

## Stata truth

New `scripts/extract_colorvar_plegend_truth.do` writing `test/fixtures/colorvar_plegend_truth.json` (skeleton extract_colorvar_options_truth.do; plot-legend texts, swatch kinds, frame and fill colours, text sizes from the SVG):
- `K5` `scatter mpg weight, colorvar(rep78) colordiscrete coloruseplegend`; `K6` `colorvar(foreign) colordiscrete coloruseplegend`; `X1` K5 + `colorotherlabel("rest")`; `C28` K5 + `colorkeysrange`; `M3` K5 + `legend(off)`; `M4` K5 + `legend(rows(1))`; `Q0` `colorvar(price)` with an lfit layer; `Q1` Q0 + `legend(size(huge))`; `Q3` K5 + lfit + `legend(size(huge))`; `P12` Q0 + `legend(rows(1))`; `ST` K5 under `scheme(stcolor)` (frame and fill).
- `R1` `colorvar(rep78) colordiscrete colorkeysreverse` (key labels with positions, swatch colours top to bottom, marker colours); `D13r` K5 + colorkeysreverse.
- `I5` `scatter mpg weight if rep78==3, colorvar(rep78) colorlevels(3)`; `I5m` + colorvarminmax; `I3` `if rep78==3, colorvar(rep78) colordiscrete colorlevels(2)`.
- `_meta` (R7); `git add -f`; register.

Cscript blocks: `S04 CV-4` (Q4204-1), `S04 CV-5` (Q4204-2), `S04 CV-11` (Q4204-3) in test/test_wp42_truth.cscript, using `_q4204_reg` (copied from `_u17_reg`).

## TDD test stubs

New `test/test_colorvar_plegend.py`:
- Test: K5, K6, X1, C28, ST: plot-legend items top to bottom, texts, no title, frame/fill, swatch kind -- `TestThePlegendKey::test_probe[probe-mode]` (red).
- Test: M3, M4, Q3: legend()'s options leave the key's text size and rows -- `TestLegendLeavesTheKey::test_probe[probe-mode]` (red for M4, Q3); the plot legend still takes size(huge) -- `::test_the_plot_legend_takes_it` (guard).
- Test: P12/Q1 on the clegend key cell: unchanged -- `TestLegendLeavesTheKey::test_cell[probe-mode]` (guard after 42-03).
- Test: R1: labels 1..5 bottom to top, colours reversed against them, markers as K1; D13r unchanged -- `TestReverse::test_probe[probe-mode]` (red).
- Test: I5, I5m, I3: key texts and marker colours -- `TestOneValue::test_probe[probe-mode]` (red); `_dash_colorvar_cuts` on a one-value domain with levels 3 gives `[3.0, 3.0]` -- `TestOneValue::test_cut_helper` (red).
- Test: after a move the coloruseplegend order stays descending and the reversed colours stay reversed, saved (node) and served -- `TestAfterAMove::test_twins_agree[probe]` (red).
- Pinned flips: Evidence list.
- Parity (R8): CORPUS entries `_case("colorvar coloruseplegend", ...)`, `_case("colorvar colorkeysreverse", ...)` after the colorvar entries (test/test_mode_parity.py:1738-1770).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| coloruseplegend key | pytest TestThePlegendKey; Q4204-1 | colorvar_plegend_truth K5 K6 X1 C28 ST | yes |
| legend() isolation | TestLegendLeavesTheKey; Q4204-2 | M3 M4 Q0-Q3 P12 | yes |
| reverse, one value | TestReverse, TestOneValue; Q4204-3 | R1 D13r I5 I5m I3 | yes |
| move twins | TestAfterAMove (node + served); parity | -- | yes |

AC-42-04.1 stubs red at base and green after; AC-42-04.2 Q4204-1..3 PASS; AC-42-04.3 dash.sthlp:5518-5523 states twoway's rule; AC-42-04.4 after each item's commit no plain row of its lead id is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py <id>` prints none), and test/test_corpus_ledger.py and every `test_every_known_difference_is_open` pass.

## Tasks

**Commit boundary.** 01+02 `Draw the coloruseplegend key as twoway does (WP-42 CV-4)`; 03+04 `Keep legend()'s size and grid off the colour key (WP-42 CV-5)`; 05+06 `Reverse a colour key's colours only; key one value at zero width (WP-42 CV-11)`; on `wp42-s04` in the worktree `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp42-s04` (BRIEF "Pull form": every command below runs in `$WT`, and a command that names the worktree names it `$WT`, this absolute path, never a `<wt>` placeholder or a relative path). Every S04 block goes directly above the first `* ==== S05 ` header of test/test_wp42_truth.cscript (42-05's blocks landed in batch 42.3, before this section; BRIEF "Block order"), after any S03 block; each closing task runs `python3 -m pytest "test/test_cscript_hygiene.py::TestTheWpTruthScripts" -q -n0` (33-01's block reader over every WP truth script: at least one passed and 0 failed; "no tests collected" is a failure). Before editing a function, run `node .gitnexus/run.cjs impact <symbol> --direction upstream --repo .` and report a HIGH, CRITICAL or UNKNOWN risk in the hand-back. Before each commit: `git -C $WT pull --ff-only . main` (BRIEF "Pull form", CLAUDE.md rule 4: pulls local main into the worktree branch; it is a no-op, `Already up to date.`, when the batch base already contains main; if it fails, stop and report to the orchestrator without committing -- a section branch never takes a merge commit), then `git -C $WT merge-base --is-ancestor main HEAD` (exit 0; otherwise stop and report), then `node .gitnexus/run.cjs detect-changes --scope all --repo .` from `$WT` (re-run a `partial` or `truncated` result), and grep the message for claude|anthropic before and after.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", its steps (1)-(3), which every closing task takes whether its item is Fix, Document or Partly -- every item of this section is a Fix item; D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c). Each closing task (42-04-02 for `CV-4`, 42-04-04 for `CV-5`, 42-04-06 for `CV-11`) takes them in `$WT` after its tracking edits and before the pull, for its item's lead id `<id>`: (1) **the ledger** -- delete every plain row of `scripts/corpus/ledger.tsv` (first column exactly `<id>`; CV-12's rows are keyed `CV-11`), keeping every `<id> (documented)` and `<id> (residual)` row (A-10: a Document item keeps its `<id> (documented)` rows); rerun `python3 scripts/corpus/ledger.py` (33-05; no `--run`, so the fixture's `_meta` is kept), stage scripts/corpus/ledger.tsv and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0`; (2) **the known-differences tables** -- run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints (WP-42's rows sit in `COLORVAR_KNOWN`, test/test_colorvar_truth.py, D-33-13.f: CV-4's coloruseplegend key, CV-5's legend() restyling, CV-11's colorkeysreverse and one-value levels; a row of any other `*_KNOWN` table it names goes the same way); a difference the item's ruling keeps is not deleted but moved into that table's deliberate dict, the companion dict 33-10 names for that table -- `DELIBERATE` (test/value_truth_known.py) for `VALUE_KNOWN`, `ABBREV_DELIBERATE` (test/test_abbreviations.py) for `ABBREV_KNOWN`, `COLORVAR_DELIBERATE` (test/test_colorvar_truth.py) for `COLORVAR_KNOWN`, and `<NAME>_DELIBERATE` beside any other `<NAME>_KNOWN` table (33-11..33-13, e.g. `SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py), as `"<key>": "<ruling id>: <what is kept>"`, where the ruling id is a DECISIONS or index id (P4-n, A-n, Q-n, M-n), never a section decision's id, and no key stays in both dicts (D-33-10.a rule 4); no item here has a ruling that keeps one; then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`); (3) **the guard** -- run block S09 of `$WT/test/test_wp33_truth.cscript` alone (33-09's case Q3309-1): write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/run_test_wp33_truth.do` (BRIEF "Running one cscript") and run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`. If Q3309-1 reports any change for a guard example -- an improved verdict, `<example id> improved from <old verdict> (<old checks>) to <new verdict> (<new checks>): ...`, or a changed field, `<example id>: <field> was <old> now <new>` (D-33-09.c; `<example id>` is an id of scripts/corpus/guard_examples.txt, never the item's GAPS4 id) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script, `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_corpus_guard_truth.do`, `git add -f` it, and run the S09 block again: the item is committed, with the regenerated fixture, only when that rerun's log shows `Q3309-1 PASS`. The commit body gains `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and, when regenerated, `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`.

<task type="auto" id="42-04-01">
  <name>Measure the plot-legend key; failing tests</name>
  <files>scripts/extract_colorvar_plegend_truth.do, test/test_colorvar_plegend.py, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_colorvar_plegend_truth.do with every probe of "Stata truth"; run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_colorvar_plegend_truth.do`; `git add -f test/fixtures/colorvar_plegend_truth.json`; register it in test/test_fixtures_are_committed.py. Create test/test_colorvar_plegend.py with CV-4's class only, TestThePlegendKey (TestLegendLeavesTheKey, TestReverse, TestOneValue and TestAfterAMove are added by 42-04-03 and 42-04-05: BRIEF "Failing test first", so this item's commit carries no later item's stub). Run `python3 -m pytest test/test_colorvar_plegend.py -q -n0 -k PlegendKey > <scratch>/42-04-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/42-04-01-failure.txt` prints at least 5; the fixture's K5 legend texts are "5" "4" "3" "2" "1" "Other".]]></verify>
  <done>twoway's plot-legend key, legend() interplay, reverse and one-value keys are measured; the CV-4 tests fail at the base.</done>
</task>

<task type="auto" id="42-04-02">
  <name>Draw the coloruseplegend key and commit</name>
  <files>dash_render.py, test/test_wp42_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Run `impact` on `_apply_colorvar` and `_dash_cvar_relevel` (Commit boundary). Apply TR-42-04.1 (re-read the coloruseplegend branch after 42-03; the display-format map: grep `var_formats` or `display_formats` in dash_render.py). Flip the coloruseplegend pins of Evidence with the reason "the plot-legend key was the clegend's ascending, titled Legend; twoway draws 5 4 3 2 1 Other, untitled, in the variable's format (CV-4)". dash.sthlp:5465-5466 coloruseplegend synopt: "the keys in the plot legend, highest first and then Other, untitled, numbers in the variable's display format, as in twoway". Write block S04 CV-4 (Q4204-1) directly above the first `* ==== S05 ` header of test/test_wp42_truth.cscript (42-05's blocks landed in batch 42.3, before this section; BRIEF "Block order"), after any S03 block; run it with WP42_ONLY=S04. Add the CV-4 parity entry `_case("colorvar coloruseplegend", ...)` (TDD test stubs) to test/test_mode_parity.py's `CORPUS`. Close CV-4 (BUGS, GAPS4, GAPS4_OPEN; CHANGELOG `### Fixed in WP-42` (a drawing change, PD-7): `coloruseplegend keys 5 4 3 2 1 Other with no title (was ascending with (missing) and the variable's label) (WP-42, CV-4)`; TWOWAY_COVERAGE_AUDIT.md Color mapping row (:120) gains `[WP-42 CV-4: corrected -- the coloruseplegend key as twoway draws it]`). Run `python3 -m pytest test/test_colorvar_plegend.py test/test_colorvar_options.py test/test_colorvar_legend.py test/test_tracking_documents.py -q -n0` and `python3 -m pytest "test/test_cscript_hygiene.py::TestTheWpTruthScripts" -q -n0`; take Closing steps (1)-(3) for `CV-4`: (1) delete its plain rows of scripts/corpus/ledger.tsv, rerun `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py CV-4`, delete the rows it prints from test/test_colorvar_truth.py's `COLORVAR_KNOWN` or whichever `*_KNOWN` table file it names, and run the hygiene command it prints; (3) run block S09 of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json, `git add -f` it and rerun S09 until its log shows `Q3309-1 PASS`; then the pull, the merge-base check and detect-changes (Commit boundary); commit; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; "Q4204-1 PASS"; `awk -F'\t' '$1 == "CV-4"' scripts/corpus/ledger.tsv` prints nothing and `python3 test/known_differences.py CV-4` prints no `<file>:<line>` row; test/test_corpus_ledger.py and the hygiene command pass; the last S09 driver log (the rerun's, after a regeneration) shows `Q3309-1 PASS`; `git log -1 --format=%s` ends "(WP-42 CV-4)".]]></verify>
  <done>The coloruseplegend key is twoway's, both modes, committed.</done>
</task>

<task type="auto" id="42-04-03">
  <name>Write failing legend isolation tests</name>
  <files>test/test_colorvar_plegend.py</files>
  <action><![CDATA[Add TestLegendLeavesTheKey (the stubs of TDD test stubs) to test/test_colorvar_plegend.py; run `python3 -m pytest test/test_colorvar_plegend.py -q -n0 -k LegendLeaves > <scratch>/42-04-03-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/42-04-03-failure.txt` prints at least 2.]]></verify>
  <done>The CV-5 tests fail at the CV-4 commit.</done>
</task>

<task type="auto" id="42-04-04">
  <name>Keep legend() off the colour keys</name>
  <files>dash_render.py, test/test_wp42_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Run `impact` on `_dash_apply_legend` (Commit boundary). Apply TR-42-04.2 (re-read :39700-39740). Flip test/test_colorvar_legend.py::TestTheSchemeChromeIsStillApplied::test_an_explicit_legend_size_still_wins to assert the colour key keeps its size (reason: "twoway's legend(size()) leaves the colour key at its own size (CV-5)"). dash.sthlp:5624: "A colorvar() key is not the legend: legend()'s size(), rows() and cols() leave it, as in twoway." Write block S04 CV-5 (Q4204-2) after the S04 CV-4 block (above the first S05 header), run it. Close CV-5 (BUGS, GAPS4, GAPS4_OPEN; CHANGELOG Fixed: `legend(size()) and legend(rows()/cols()) no longer restyle the colour key (WP-42, CV-5)`; TWOWAY_COVERAGE_AUDIT.md Legends row (:143) gains `[WP-42 CV-5: corrected -- legend() size and grid leave the colour key]`). Run `python3 -m pytest test/test_colorvar_plegend.py test/test_colorvar_legend.py test/test_legend_geometry.py test/test_legend_remainder.py test/test_tracking_documents.py -q -n0` and `python3 -m pytest "test/test_cscript_hygiene.py::TestTheWpTruthScripts" -q -n0`; take Closing steps (1)-(3) for `CV-5`: (1) delete its plain rows of scripts/corpus/ledger.tsv, rerun `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py CV-5`, delete the rows it prints from test/test_colorvar_truth.py's `COLORVAR_KNOWN` or whichever `*_KNOWN` table file it names, and run the hygiene command it prints; (3) run block S09 of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json, `git add -f` it and rerun S09 until its log shows `Q3309-1 PASS`; then the pull, the merge-base check and detect-changes (Commit boundary); commit; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; "Q4204-2 PASS"; `awk -F'\t' '$1 == "CV-5"' scripts/corpus/ledger.tsv` prints nothing and `python3 test/known_differences.py CV-5` prints no `<file>:<line>` row; test/test_corpus_ledger.py and the hygiene command pass; the last S09 driver log (the rerun's, after a regeneration) shows `Q3309-1 PASS`; `git log -1 --format=%s` ends "(WP-42 CV-5)".]]></verify>
  <done>legend()'s size and grid steps leave every colour key, committed.</done>
</task>

<task type="auto" id="42-04-05">
  <name>Write failing reverse and one-value tests</name>
  <files>test/test_colorvar_plegend.py</files>
  <action><![CDATA[Add TestReverse, TestOneValue and TestAfterAMove (the stubs of TDD test stubs) to test/test_colorvar_plegend.py; run `python3 -m pytest test/test_colorvar_plegend.py -q -n0 -k "Reverse or OneValue or AfterAMove" > <scratch>/42-04-05-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/42-04-05-failure.txt` prints at least 4.]]></verify>
  <done>The CV-11/CV-12 tests fail at the CV-5 commit.</done>
</task>

<task type="auto" id="42-04-06">
  <name>Reverse colours only; zero-width cuts</name>
  <files>dash_render.py, test/test_wp42_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Run `impact` on `_dash_colorvar_cuts`, `_dash_colorvar_bins` and `_dash_cvar_keycell_update` (Commit boundary). Apply TR-42-04.3 and TR-42-04.4 in both twins (re-read :14200-14245 after 42-05, `_dash_cvar_keycell_update` and `dash_cvar_keycell_update` from 42-03, the JS levels rule). Flip test/test_colorvar_options.py::TestKeys::test_reverse (reason: "dash reversed the entries and their labels; twoway reverses the key's colours only (CV-11)") and the one-value label pins in test/test_function_audit.py (reason CV-12). dash.sthlp:5518-5523: "colorkeysreverse reverses the colours of a colordiscrete key against its levels, as twoway draws it; the plotted colours and the plot legend under coloruseplegend are unchanged". Write block S04 CV-11 (Q4204-3) after the S04 CV-5 block (above the first S05 header), run it. Add the CV-11 parity entry `_case("colorvar colorkeysreverse", ...)` (TDD test stubs) to test/test_mode_parity.py's `CORPUS`. Close CV-11 with CV-12 in its Item (BUGS, GAPS4, GAPS4_OPEN; CHANGELOG `### Fixed in WP-42` (a drawing change, PD-7): `colorkeysreverse reverses the key's colours, not its labels; colorlevels() over one value keys 3 3 as twoway (WP-42, CV-11)`; TWOWAY_COVERAGE_AUDIT.md Color mapping row (:120) gains `[WP-42 CV-11: corrected -- colorkeysreverse reverses colours only; one-value colorlevels()]`). Run `python3 -m pytest test/test_colorvar_plegend.py test/test_colorvar_options.py test/test_colorvar_forms.py test/test_function_audit.py test/test_colorkeysreverse_bar.py test/test_tracking_documents.py -q -n0`, `python3 -m pytest test/test_mode_parity.py -q -n0 -k colorvar` and `python3 -m pytest "test/test_cscript_hygiene.py::TestTheWpTruthScripts" -q -n0`; take Closing steps (1)-(3) for `CV-11`: (1) delete its plain rows of scripts/corpus/ledger.tsv (CV-12's rows are keyed `CV-11`), rerun `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py CV-11`, delete the rows it prints from test/test_colorvar_truth.py's `COLORVAR_KNOWN` or whichever `*_KNOWN` table file it names, and run the hygiene command it prints; (3) run block S09 of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json, `git add -f` it and rerun S09 until its log shows `Q3309-1 PASS`; then the pull, the merge-base check and detect-changes (Commit boundary); commit; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; "Q4204-3 PASS"; `awk -F'\t' '$1 == "CV-11"' scripts/corpus/ledger.tsv` prints nothing and `python3 test/known_differences.py CV-11` prints no `<file>:<line>` row; test/test_corpus_ledger.py and the hygiene command pass; the last S09 driver log (the rerun's, after a regeneration) shows `Q3309-1 PASS`; `git log -1 --format=%s` ends "(WP-42 CV-11)".]]></verify>
  <done>colorkeysreverse and one-value keys follow twoway, both modes, committed.</done>
</task>

## Section completion criteria

- Three commits on `wp42-s04`; Q4204-1..3 PASS; stubs green; parity entries added.
- CV-4, CV-5, CV-11 tracked per PD-3 with `commit pending`; GAPS4_OPEN lines deleted; WP-42's rows all closed for WE.
- The closing steps taken in each commit: no plain CV-4, CV-5 or CV-11 row left in scripts/corpus/ledger.tsv or a `*_KNOWN` table, corpus_ledger.json regenerated and staged, S09 run, and test/fixtures/corpus_guard_truth.json regenerated and staged whenever Q3309-1 reported a change for a guard example, the rerun PASS.

## Notes

- **Batch and JS (DECISIONS A-11):** CV-12's cut helper twin and colorkeysreverse's relevel edit `_DASH_CVAR_RELEVEL_JS`; the manifest marks 42-04 JS = yes and it is alone in batch 42.5, so R12 holds. Its S04 blocks land after 42-05's S05 blocks (42.3), hence the insertion rule of the Commit boundary.
- **Trap:** a reversed key must not reverse `mapper.palette` (that would recolour the markers); only the cell's swatch colours.
- **Trap:** the variable's display format may be a date format: write the level through `_dash_fmt_text` with that format, as twoway's `string(cut, fmt)`.
- **Help paragraphs owned (R3):** dash.sthlp:5463-5466, :5518-5523, :5624.
- **Merge rules:** R1 (blocks above the first S05 header), R2, R7, R8, R9, R12 (`_dash_apply_legend`, `_apply_colorvar`, `_DASH_CVAR_RELEVEL_JS`: this section is batch 42.5's only editor), R13.
- **Functions this section edits (for the manifest's Owns cell):** `GlyphMapper._apply_colorvar` coloruseplegend branch (R12), `_dash_apply_legend` rows()/cols() and size() steps (R12), `_DASH_CVAR_RELEVEL_JS` (`dash_cvar_relevel`, `dash_cvar_relevel_bins` levels rule, `dash_cvar_keycell_update`; R12), `_dash_cvar_relevel`, `_dash_cvar_keycell_update`, `_dash_colorvar_cuts`, `_dash_colorvar_bins`.
- **Commit body lines:** `Regression: test/test_colorvar_plegend.py::TestThePlegendKey::test_probe[K5-saved] -- failed at <base> with <text>`; `Flipped: test/test_colorvar_options.py::TestKeys::test_reverse -- reversed labels were wrong because twoway reverses the key's colours only`; `Fixture: test/fixtures/colorvar_plegend_truth.json (scripts/extract_colorvar_plegend_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (every commit; the guard fixture's line when S09 made it regenerate); `BUGS.md: "<title>" (closed)`; `GAPS4: CV-4 Tracked` (and CV-5, CV-11).
