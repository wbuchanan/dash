# Section 48-03: Tracker accuracy: dash_setup help, CHANGELOG, coverage audit, GAPS3, DROPIN

> Part of: WP-48 (Help, README and tracker accuracy, audit package 16) · Items: DT-29 · Risk: green · Batch: 48.1 · Depends on: none (WP-34..47 landed) · Blocks: 48-04 · Tasks: 5, 1 commit · Case-id prefix: Q4803

## Overview

**What is wrong today.** DT-29 (DT-30, TR-22): "dash_setup help contradicts itself on versions/ceilings; 0.1.0 CHANGELOG lists reversed behaviour; TWOWAY_COVERAGE_AUDIT rows stale; GAPS3 H5/I1/K1/K5 lack Tracked lines; DROPIN P2.34/P2.64 unmapped; rejected_options.json narratives" (audit :813). In detail (appendix :2501-2507, :2645):

- **dash_setup.sthlp.** :124-126 says `venv()` installs "packaging, bokeh, numpy and pandas at their minimums", while :88-96 says every install, the venv() one included, uses the hash-pinned lock at the newest tested versions (dash_setup_lib.py `lock_install`, :1085-1093; dash_requirements.txt). :208-213 says numpy and pandas have ceilings (`numpy>=2.3,<2.5`, `pandas>=2.3,<3.1`) and that only bokeh's is reported, while dash.sthlp:6716-6718 says "Only bokeh has a ceiling".
- **CHANGELOG.md 0.1.0** lists behaviour later work in the same release reversed: :589-591 (contour, contourline, rpcap, rpspike "refused by name"; all drawn), :706 (`yaxis(3)` r(198); axes 1-9 are taken), :712 (`[aw=price+1]` r(198); expressions are taken), :622 (tmlabel()/tmtick() "named until drawn"; drawn), :838 (mlalign() "named until it is drawn"; center and inside silent), :928 and :936 (WP-32 entries "filed as open"; closed).
- **TWOWAY_COVERAGE_AUDIT.md** keeps open text later work closed: :17-18 (the summary's "Unknown option names are normally accepted and reported as ignored"; titel() is refused), :31, :46, :47, :158, :165 ("saved page does not recompute": WP-29 F1a-g closed it), :66-67 ("Upright only": horizontal drawn), :145 ("fxsize(), fysize(), and scale() ignored": drawn, sizing_truth.json), :146 ("shrink ... bystyles stay named": WP-31 D10b/c), :218 (stale counts).
- **GAPS3.md** rows H5, I1, K1 and K5 have no `Tracked:` line in its §9 (143 lines; ROADMAP.md:5141 calls H5, I1 and K5 "expected by the index").
- **DROPIN-REMAINING.md** P2.34 (colorvar refusals and key text) and P2.64 (value-list refusals in dash's words or codes) are open rows mapped to nothing; the file is read by test_tracking_documents.py's `TestNoResidualNamesAClosedRow` (:523-551).
- **test/fixtures/rejected_options.json**'s narrative fields (`purpose`, `root_cause`, `summary`) describe the 18oct2026 state ("Counter-example set for the dash.sthlp:668-673 claim that "No error is produced for unknown options ...""); the fixture is written by scripts/extract_rejected_options.do.

**After this section**, each tracking document says what is true at the WP-48 base, every annotation names where an item is tracked now, the fixture's narrative is regenerated from its script, and every tracking test stays green.

**Why one section.** One item, six tracker files, one owner (index Owns: dash_setup.sthlp, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md, GAPS3.md, DROPIN-REMAINING.md). It runs beside 48-01 in batch 48.1; the only shared file is TWOWAY_COVERAGE_AUDIT.md, whose headlabel rows (:71, :81, :84 at `090d928`) are 48-01's (basic:PT-16); this section edits every other stale row.

**Test order and commit rule.** One commit `(WP-48 DT-29)`. 48-03-01 writes every pin (tests reading the corrected statements) and runs them on the base, saves the failure text, no commit; 48-03-02 and 48-03-03 edit the trackers, two each, running their readers; 48-03-04 regenerates the fixture, closes the item and commits once; 48-03-05 checks. (Four tasks for the one item, BRIEF's task-count norm.)

### Section decisions (binding on the executor)

- **D-48-03.a dash_setup.sthlp states the lock.** :124-126's sentence becomes "installs packaging, bokeh, numpy and pandas from the hash-pinned lock (see {help dash_setup##lock:The hash-pinned lock}) into it"; :208-213 stays the authority for ceilings; dash.sthlp:6716-6718's "Only bokeh has a ceiling" becomes "bokeh, numpy and pandas have ceilings (see help dash_setup); only bokeh's is reported". 36-04 (WP-36) rewrote dash_setup.sthlp's lock-coverage and dependency paragraphs: re-read them; change only the two contradictions.
- **D-48-03.b The CHANGELOG keeps its history, annotated.** Each reversed 0.1.0 line keeps its text and gains, at its end before any `<!-- ... -->` marker, ` (Superseded in 0.1.0: <what dash does now>, <WP that changed it>.)` -- one sentence, no line numbers. Marker comments and the `### Fixed in WP-NN` lists are untouched (test_tracking_documents.py reads WP-31's markers and lists; PD-7). The lines are found by phrase (`refused by name`, `yaxis(3)`, `aw=price+1`, `named until`, `filed as open`). The phrase `refused by name` also matches CHANGELOG.md:1009-1010 at `090d928`: those two lines are 35-09's, corrected under A-9 (WP-35) -- skip them whatever they read at the WP-48 base; only the contour/rpcap/rpspike line (:589-591) is annotated here.
- **D-48-03.c TWOWAY_COVERAGE_AUDIT.md: tag, never delete.** Each stale row or sentence gets a bracketed tag in the file's existing style (`[WP-29 P0.17, commit b242b99: partly closed; open: ...]` at :31 is the precedent): `[Closed in WP-NN, BUGS.md "<title>", commit <sha>]` when the open part is closed, with the open words struck by rewriting them to the current behaviour; :17-18's summary sentence is rewritten (unknown options are refused as twoway refuses them; noted options are the Unsupported list); :218's counts get `[Counts of <date>; superseded]`. TWOWAY_COVERAGE_AUDIT.md:15, :105 and :106 at `090d928` are 35-09's (A-9): never tag or annotate them, and never add a tag naming what they named.
- **D-48-03.d GAPS3 Tracked lines only in forms the reader accepts.** For each of H5, I1, K1, K5: find where it is tracked now (`grep -n "<row words>" BUGS.md GAPS4.md ROADMAP.md`). Add `- **<id> Tracked:** <form>` to GAPS3.md §9 only when one of `_gaps3_problems`'s forms is true: `Closed in WP-3[12], BUGS.md "<closed title>", commit <sha>.` or `Partly closed in WP-31 (section NN, commit <sha>): <closed>; open: <rest> (BUGS.md "<open residual title>").` with an existing open entry. When no accepted form is true (an "expected" residual with no BUGS entry, such as K5's module split), add no Tracked line; instead append to the §9 intro paragraph (`## 9. Tracking`, GAPS3.md:413-418) one sentence: "H5, I1, K1 and K5 are residuals the WP-31 index expected; where each is tracked now: <id>: <GAPS4 id or BUGS title or 'not tracked: <why>'>." and run test_tracking_documents.py to confirm prose there is not parsed.
- **D-48-03.e DROPIN rows are mapped, not closed.** P2.34 and P2.64 each gain, at the end of the row, `[Mapped to GAPS4 <id> (<state>), <id> (<state>)]` with the GAPS4 rows whose Item text names each sub-claim (expected: P2.34 -> CV-14 and CV-2/CV-9 as the Item cells say; P2.64 -> basic:PT-9, syn:SD-8, and the mlabposition(13) note's row, LT-25 or ST-3 -- the executor greps GAPS4.md's Item cells for `base(abc)`, `barwidth(.)`, `mlabel(make..)`, `mlabel(L.`, `mlabposition`). The literal text `[Closed in` is used only if every mapped row is Closed, so `TestNoResidualNamesAClosedRow` keeps reading the row as open while any part is open.
- **D-48-03.f rejected_options.json: change the script, regenerate.** The narrative string literals in scripts/extract_rejected_options.do (`purpose`, `root_cause`, `summary`; grep them) are replaced by one current sentence each without help line numbers; the fixture is regenerated twice through `scripts/stata_slot.sh`. If the remeasured probes differ from the committed ones (dash's behaviour moved since 18oct2026), every reader (test_taxis_options.py, test_recast.py, test_option_surface.cscript, test_fixtures_are_committed.py) is run: a reader that fails because it pinned the old measurement is a fixture-drift pin, updated with a `Flipped:` line naming the WP that changed the behaviour (CLAUDE.md rule 2); a reader failing for another reason stops the task for the maintainer.

## Risk: [green] -- documentation and one regenerated fixture

**Why.** No product code; risk is to the tracking tests that parse these files.

**Risk factors.** (1) test_tracking_documents.py parses GAPS3.md, BUGS.md, CHANGELOG.md markers and DROPIN-REMAINING.md. (2) The regenerated rejected_options.json feeds two pytest files and a cscript. (3) TWOWAY_COVERAGE_AUDIT.md is also edited by 48-01 (headlabel rows).

**Mitigation.** (1) After each file, run `python3 -m pytest test/test_tracking_documents.py -q -n0`. (2) D-48-03.f's reader rule. (3) Disjoint rows; merge order 48-01 then 48-03; this section never edits a line containing `headlabel`.

## Dependencies

- **Depends on:** none in WP-48; WP-34..47 landed (their closures are what the annotations name).
- **Blocks: 48-04** (batch 48.3), whose HR checklist reads dash_setup.sthlp (HR-20, 36-01's) and the README.
- **Parallel batch 48.1** with 48-01 (TWOWAY_COVERAGE_AUDIT.md rows split as above).

## Evidence

Quoted in the Overview with anchors at `090d928`: dash_setup.sthlp:88-96, :122-127, :206-213; dash.sthlp:6716-6718; CHANGELOG.md:589-591, :622, :706, :712, :838, :928, :936; TWOWAY_COVERAGE_AUDIT.md:17-18, :31, :46-47, :66-67, :145-146, :158, :165, :218; GAPS3.md:242 (H5), :258 (I1), :281 (K1), :285 (K5), §9 :413-418; DROPIN-REMAINING.md P2 rows 34 and 64 (`### P2:` list); test/test_tracking_documents.py:523-551 (`TestNoResidualNamesAClosedRow`), `_gaps3_problems` (:2419-2462); scripts/extract_rejected_options.do.

### Tests that pin today's behaviour

- test/test_tracking_documents.py (GAPS3 forms, DROPIN reader, CHANGELOG markers) -- must stay green, nothing flipped.
- Readers of rejected_options.json (D-48-03.f).
- dash_setup help readers: `grep -rn "at their minimums\|Only bokeh has a ceiling" test/` -- flip with reasons.

## User stories

- **US-48-03.1** As a Stata user installing dash, I want dash_setup's help to say one thing about which versions it installs.
- **US-48-03.2** As the maintainer, I want the CHANGELOG, coverage audit and registers to say where each item stands, so the trackers can be trusted.

## Business requirements

- **BR-48-03.1** dash_setup.sthlp and dash.sthlp agree on what venv() installs and which packages have ceilings.
- **BR-48-03.2** Every reversed 0.1.0 CHANGELOG line carries its superseding sentence.
- **BR-48-03.3** No TWOWAY_COVERAGE_AUDIT.md row states an open defect that is closed.
- **BR-48-03.4** H5, I1, K1, K5 and P2.34, P2.64 each say where they are tracked now.
- **BR-48-03.5** rejected_options.json's narrative is current and written by its script.
- **BR-48-03.6** Every tracking test stays green.

## Technical requirements

- **TR-48-03.1** New test file `test/test_tracker_accuracy_p16.py` with: `TestSetupHelp::test_venv_uses_the_lock`, `::test_ceilings_agree`; `TestChangelog::test_reversed_lines_are_annotated` (each phrase of D-48-03.b is followed on its line or the next by "Superseded in 0.1.0"); `TestCoverageAudit::test_no_stale_open_text` (the stale phrases of the Overview are absent or tagged `[Closed in`); `TestRegisters::test_gaps3_rows_say_where` (each of H5, I1, K1, K5 has a Tracked line or is named in the §9 sentence); `TestRegisters::test_dropin_rows_are_mapped` (rows 34 and 64 carry `[Mapped to GAPS4`); `TestRejectedNarrative::test_no_help_line_numbers` (no `dash.sthlp:` in the narrative fields) and `::test_written_by_its_script` (the fixture's narrative equals the script's literals).
- **TR-48-03.2** The edits of D-48-03.a-f; the regenerated fixture `git add -f`.
- **TR-48-03.3** BUGS: DT-29's entry closed naming DT-30 and TR-22 and the test file; GAPS4 Closed, commit pending; GAPS4_OPEN line deleted. No CHANGELOG `### Fixed in WP-48` line beyond one: "The tracking documents and dash_setup's help agree with the code (WP-48, DT-29)".

## Boundaries

- Do not edit dash.sthlp beyond :6716-6718; do not edit the README or dash.pkg (48-04); do not touch TWOWAY_COVERAGE_AUDIT.md lines containing `headlabel` (48-01); do not add a new Tracked form or change test_tracking_documents.py's readers.
- Never delete a CHANGELOG line, a GAPS3 row or a DROPIN row.
- **35-09's lines (A-9, REVIEW-5 R5-11).** CHANGELOG.md:1009-1010 and TWOWAY_COVERAGE_AUDIT.md:15, :105, :106 (anchors at `090d928`) are corrected by 35-09 in WP-35; this section never annotates, tags or rewrites them, and its tests do not read them.
- **The existing Stata-version sentences stay byte-identical** (A-2, M2, REVIEW-5 R5-26): CHANGELOG.md:919 (inside the 0.1.0 list this section annotates), dash_setup.sthlp:155-157 (the `{phang2}Stata 19 or later; tested on StataNow 19.5 ...` sentence, its three lines, beside the two sentences of D-48-03.a), dash.sthlp:6700-6703 (in the Dependencies list beside :6716-6718), GAPS3.md:258 (I1's row; the §9 sentence of D-48-03.d does not touch it), README.md:32-33 and dash.pkg:17-18 (the `d Requires: Stata 19 or later; tested on StataNow 19.5 ...` line and the `d` line after it) (anchors at `090d928`; re-read by phrase, `grep -n "tested on StataNow 19.5"` in each file, GAPS3.md:258 by its `| I1 |` row). No sentence about Stata versions is added, and no test reads or asserts those lines.

## Stata truth

The regenerated `rejected_options.json` (scripts/extract_rejected_options.do, D-48-03.f). Nothing else; no truth script (PD-6).

## TDD test stubs

- Test: venv uses the lock -- test_tracker_accuracy_p16.py::TestSetupHelp::test_venv_uses_the_lock (fails at base: "at their minimums").
- Test: ceilings agree -- ::TestSetupHelp::test_ceilings_agree (fails at base).
- Test: reversed CHANGELOG lines annotated -- ::TestChangelog::test_reversed_lines_are_annotated (fails).
- Test: coverage audit current -- ::TestCoverageAudit::test_no_stale_open_text (fails).
- Test: registers say where -- ::TestRegisters::test_gaps3_rows_say_where, ::test_dropin_rows_are_mapped (fail).
- Test: fixture narrative -- ::TestRejectedNarrative::test_no_help_line_numbers (fails), ::test_written_by_its_script.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| setup help, CHANGELOG, audit, registers | pytest test_tracker_accuracy_p16.py | the files themselves | n/a |
| tracking machinery unchanged | pytest test_tracking_documents.py | GAPS3.md, BUGS.md, DROPIN-REMAINING.md | n/a |
| fixture narrative and readers | pytest readers; test_option_surface.cscript | rejected_options.json (regenerated) | n/a |

Acceptance criteria:
- **AC-48-03.1** test_tracker_accuracy_p16.py passes; every test in it failed at the WP-48 base.
- **AC-48-03.2** test_tracking_documents.py, test_fixtures_are_committed.py and the rejected_options readers pass.

## Tasks

**Commit boundary.** One commit `Bring the tracking documents and setup help up to date (WP-48 DT-29)` made by 48-03-04; 48-03-01..03 are steps (no commit); 48-03-05 checks.

```xml
<task type="auto" id="48-03-01">
  <name>Write the tracker-accuracy pins</name>
  <files>test/test_tracker_accuracy_p16.py</files>
  <action><![CDATA[Create test/test_tracker_accuracy_p16.py with every test of TR-48-03.1 (plain file reads; no import from other test modules; no test reads the lines the Boundaries keep byte-identical or 35-09's lines). Run it on the base; save to <scratch>/48-03-01-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_tracker_accuracy_p16.py -q -n0 -> every test fails except TestRejectedNarrative::test_written_by_its_script; failure file exists]]></verify>
  <done>The pins exist and fail on the stale trackers.</done>
</task>

<task type="auto" id="48-03-02">
  <name>Reconcile setup help; annotate CHANGELOG lines</name>
  <files>dash_setup.sthlp, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[Apply D-48-03.a (re-read 36-04's paragraphs first; change only the two contradictions, leaving dash_setup.sthlp:155-157 and dash.sthlp:6700-6703 byte-identical). Flip readers found by grep -rn "at their minimums\|Only bokeh has a ceiling" test/ (the files that read dash_setup.sthlp: grep -ln "dash_setup.sthlp" test/*.py). Then apply D-48-03.b to each reversed 0.1.0 line found by phrase, skipping CHANGELOG.md:1009-1010 (35-09's, A-9) and leaving CHANGELOG.md:919, the markers and the Fixed lists as they are. Run TestSetupHelp, TestChangelog, the dash_setup.sthlp readers found by the grep, test_help_claims_*.py and test_tracking_documents.py.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_tracker_accuracy_p16.py::TestSetupHelp test/test_tracker_accuracy_p16.py::TestChangelog test/test_tracking_documents.py test/test_help_claims_8.py test/test_packaging.py -q -n0 -> pass; git diff -U0 CHANGELOG.md dash_setup.sthlp dash.sthlp shows no hunk at the A-2 lines -- CHANGELOG.md:919, dash_setup.sthlp:155-157 and dash.sthlp:6700-6703, each located first by phrase with grep -n "tested on StataNow 19.5" (the line it prints and the lines of that sentence after it)]]></verify>
  <done>The two help files agree on versions and ceilings, and every reversed 0.1.0 line names what superseded it.</done>
</task>

<task type="auto" id="48-03-03">
  <name>Tag audit rows; map GAPS3 and DROPIN</name>
  <files>TWOWAY_COVERAGE_AUDIT.md, GAPS3.md, .ultraplan/handoff/DROPIN-REMAINING.md</files>
  <action><![CDATA[Apply D-48-03.c to :17-18, :31, :46, :47, :66-67, :145, :146, :158, :165, :218 (found by phrase), with the BUGS titles and shas of the closures (git log -S and BUGS.md); do not touch any line holding "headlabel" (48-01) or 35-09's :15, :105, :106. Then apply D-48-03.d and D-48-03.e. After each file run python3 -m pytest test/test_tracking_documents.py -q -n0; if a Tracked line you added is refused by _gaps3_problems, remove it and use the §9 sentence instead. Run TestCoverageAudit and TestRegisters.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_tracker_accuracy_p16.py::TestCoverageAudit test/test_tracker_accuracy_p16.py::TestRegisters test/test_tracking_documents.py -q -n0 -> pass]]></verify>
  <done>No coverage-audit row states a closed defect as open, and H5, I1, K1, K5, P2.34 and P2.64 each say where they are tracked, within the readers' forms.</done>
</task>

<task type="auto" id="48-03-04">
  <name>Regenerate the fixture narrative; commit</name>
  <files>scripts/extract_rejected_options.do, test/fixtures/rejected_options.json</files>
  <action><![CDATA[Apply D-48-03.f: edit the narrative literals, regenerate twice through scripts/stata_slot.sh with DASH_REPO, git add -f, run every reader and handle drift by the rule. Close DT-29 (TR-48-03.3: BUGS closed form, GAPS4 Closed with commit pending, GAPS4_OPEN (test/test_tracking_documents.py) line deleted, the one CHANGELOG line). Before the commit take BRIEF's closing steps (1)-(3) for DT-29 (Notes "Before every commit" gives each command in full): (1) delete DT-29's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `DT-29 (documented)` or `DT-29 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py DT-29` and delete every row it prints from its `*_KNOWN` table -- a difference DT-29's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with DT-29. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep). Run test_tracker_accuracy_p16.py, test_tracking_documents.py, test_fixtures_are_committed.py, test_taxis_options.py, test_recast.py, test_corpus_ledger.py and test_option_surface.cscript through stata_slot.sh; commit everything from 48-03-02..04 as one commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_tracker_accuracy_p16.py test/test_tracking_documents.py test/test_fixtures_are_committed.py test/test_taxis_options.py test/test_recast.py test/test_corpus_ledger.py -q -n0 -> pass; test_option_surface.cscript -> ALL CHECKS PASSED; subject ends "(WP-48 DT-29)"; grep -ci 'claude\|anthropic' on the message -> 0]]></verify>
  <done>Every tracker and the fixture narrative are current, and DT-29 is committed.</done>
</task>

<task type="auto" id="48-03-05">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run test_tracker_accuracy_p16.py, test_tracking_documents.py, test_fixtures_are_committed.py, test_help_conformance.py and test_help_claims_*.py once more on the committed tree.]]></action>
  <verify><![CDATA[all pass]]></verify>
  <done>The section's commit is green on its own.</done>
</task>
```

## Section completion criteria

- One commit `(WP-48 DT-29)` with the six trackers corrected, the fixture regenerated by its script, the pins green and every tracking test green.

## Notes

- **Traps.** (1) `TestNoResidualNamesAClosedRow` treats a row containing `[Closed in` or `Written closed` as closed: never write those words into P2.34/P2.64 while a mapped part is open. (2) GAPS3.md's §9 Tracked lines are parsed line by line: a sentence in the intro is not, but a sentence starting `- **H5 Tracked:**` is. (3) CHANGELOG lines may carry `<!-- WP-31 <id> -->`: put the annotation before it. (4) Keep `rejected_options.json`'s keys and schema_version.
- **Files this section owns (R3, index):** dash_setup.sthlp's two sentences, dash.sthlp:6716-6718, CHANGELOG.md 0.1.0 lines (not :919, A-2; not :1009-1010, 35-09's), TWOWAY_COVERAGE_AUDIT.md (all but the headlabel rows, 48-01's, and :15, :105, :106, 35-09's), GAPS3.md §9, DROPIN-REMAINING.md rows 34 and 64, scripts/extract_rejected_options.do and its fixture.
- **Merge rules touched:** R3, R4 (CHANGELOG annotated, union merge), R5, R7 (regenerated fixture), R9 (drift pins only), R14 (35-09's lines are not touched).
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp48-s03`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_tracker_accuracy_p16.py::TestSetupHelp::test_venv_uses_the_lock -- failed at <base sha> with <text>`; `Fixture: test/fixtures/rejected_options.json (scripts/extract_rejected_options.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: DT-29 Tracked`.
