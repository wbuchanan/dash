# Section 33-14: First corpus run and sign-off

> Part of: WP-33 (Verification corpus and README gallery) · Items: TR-2 · Risk: yellow · Batch: 33.7 · Depends on: 33-08, 33-09 · Blocks: WP-33 WE · Tasks: 5, 1 commit · Case-id prefix: Q3314 (none used)

## Overview

**What is wrong today.** TR-2 (audit :672-674, appendix :2518-2524): "No picture comparison over a broad corpus (109 gr_example commands run here only once, by hand)". "`git grep gr_example` finds nothing. test/fixtures/twoway_corpus.do (299 probes) checks only return codes ... conformance_corpus.txt (75 lines) checks only that each command registers. test_mode_parity.py compares the saved page with the served app, so dash against dash." The auditor's one-off run "found ... real differences no test catches (TR-3 to TR-6, TR-14, TR-15)". The fix asked for: "Commit a corpus harness ... every gr_example (and the manual's examples) ... compare tick values and labels, titles, legend keys, glyph counts and extents, and colours, with a known-differences ledger."

**After this section.** WP-33's harness (33-02..33-05, wired by 33-08's `make corpus`) has run once over the whole corpus -- help files, g.pdf [G-2]/[G-3], `examples/` and the audit's probes, one example per combination of plot types and option names (P4-2: about 425 of 636 distinct commands, every dropped duplicate listed with the example it maps to). Each example has its verdict and its differences -- glyph colours among them, judged within the calibrated RGB tolerance (DECISIONS A-25) -- each explained by a ledger row where one exists. The run's counts are committed as `test/fixtures/corpus_baseline.json` (written by 33-08's `scripts/corpus/summary.py`), with its date and dash commit, after the maintainer approved them (Q12). TR-2 closes, pinned by that record's test and by 33-09's certification guard (Q3309-1). By maintainer decision P4-8 this section builds **no gallery page and no README block**: those are built and committed only at WP-50's closeout (WE.7), with the maintainer's sign-off (PD-13, PD-17).

**Why its own section.** It runs the whole pipeline once, holds every Stata slot for hours and needs the maintainer's approval.

**Test order and commit rule.** Task 01 writes TR-2's test red and saves `<scratch>/33-14-01-failure.txt`; task 02 runs `make corpus`; task 03 writes the baseline record; task 04 is the maintainer's checkpoint; task 05 closes TR-2 and commits once: `Run the corpus comparison once and record its baseline (WP-33 TR-2)`.

### Section decisions (binding on the executor)

- **D-33-14.a What runs.** `make corpus` with the default `CORPUS_DIR` (`$TMPDIR/dash_corpus`), on the tree batch 33.6 left, after batch 33.6's gate has finished, with no other Stata job and no full suite running (both want every Stata slot). `make gallery` is not run (P4-8).
- **D-33-14.b The baseline record.** `python3 scripts/corpus/summary.py --run "$CORPUS_DIR" --out test/fixtures/corpus_baseline.json` (D-33-08.o, TR-33-08.2): the counts per verdict and per plot type, the duplicates removed, the examples twoway or dash refused (kept as data, P4-10), the ledger ids with the number of differences each explains, and the checks outside tolerance that no ledger row explains, under `_meta` (`stata_version`, `born_date`, `extracted`, `dash_commit` = the tree `make corpus` ran on, `source` = `scripts/corpus/summary.py`). GENERATORS row `"corpus_baseline.json": "scripts/corpus/summary.py"`; 33-08's Makefile `truth:` line already names the generator (`test_make_truth_lists_every_generator`). `git add -f` (`.git/info/exclude:58`).
- **D-33-14.c Pins.** TR-2's certification case is 33-09's Q3309-1 (twenty corpus examples in every gate); its pytest pins are `test/test_corpus_baseline.py` (TR-33-14.1) and `test/test_corpus_guard.py`. No truth block is added (BRIEF "Block order": a harness item adds none).
- **D-33-14.d What the checkpoint shows.** The counts (examples, duplicates removed, Same, Close, Differs, skipped, refused by twoway, refused by dash); the counts per plot type; each ledger id with the number of differences it explains; each unexplained check with its count; the twenty Differs examples with the most checks outside tolerance (id, command, `summary`); every skipped example with its reason, and each `skip: dataset <name> not cached` line the run printed (one per dataset missing from the offline cache, 33-03's D-33-03.f; none is expected after 33-02's fetch, which fetches only the datasets the cache lacks, A-26); the record's privacy grep (`grep -cE '/(Users|private|var|tmp|home)/|<user name>' test/fixtures/corpus_baseline.json` prints 0). It says in plain words what approval does: it records these counts as WP-33's starting point and closes the "no picture comparison" item; it publishes nothing and changes no README text (the gallery comes at the final closeout).
- **D-33-14.e The ledger is not edited here.** A difference no ledger row explains stays counted as unexplained, so the baseline is honest. If the maintainer names a systematic difference and the open GAPS4 item that explains it, the row is added by a follow-up on 33-05's files (D-33-05.e's form, D-33-05.i's regeneration), `verdict.py --run "$CORPUS_DIR"` and `summary.py` are rerun, and the checkpoint is asked again.
- **D-33-14.f No gallery, no README (P4-8).** No file under docs/ is written, README.md and scripts/corpus/readme_examples.txt are unchanged; the README ids are chosen at WE.7 with `gallery.py --suggest-ids` (D-33-08.k).

## Risk: [yellow] -- a long run over hundreds of examples and a sign-off

**Risk factors.** (1) The run takes hours and holds every Stata slot. (2) Disk: twoway and dash SVGs, pages and logs for about 425 examples. (3) A stage fails partway. (4) A path or name leaking into the record. (5) The counts read as a claim about dash before the WP-34..49 fixes.

**Mitigation.** (1) D-33-14.a; `make corpus` uses the slots through stata_slot.sh as `make truth` does. (2) `df -h` before (the memory note: the suite once filled the disk); the run folder is outside the repository and removed after the commit. (3) Each stage writes its own files; make stops at the failing stage's line, which reruns alone. (4) The record holds counts and ids only; D-33-14.d's grep; test_fixtures_are_committed.py's `_ABSOLUTE` guard. (5) Nothing is published: the counts live in a test fixture, the BUGS entry and the commit body.

## Dependencies

- **Depends on: 33-08** (`make corpus`, summary.py) and **33-09** (the guard), and through them 33-02..33-07 and 33-15.
- **Blocks:** WP-33's WE (WE.1 needs TR-2 closed).
- **Parallel batch 33.7:** none (alone).

## Evidence

- 33-08's `make corpus` (TR-33-08.3: extract, fetch, twoway, dash, verdict, summary into `CORPUS_DIR`) and `scripts/corpus/summary.py` (TR-33-08.2: `summarise`, `write_fixture`, `main --run [--out]`).
- 33-09's `test/fixtures/corpus_guard_truth.json` and block `S09 tool: corpus guard` (Q3309-1).
- 33-05's `test/fixtures/corpus_ledger.json` (known differences keyed by GAPS4 id, PD-14) and `corpus_verdict_rules.json`; verdicts.jsonl's row keys (33-05's Published interface).
- Corpus size [S §1d]: help 198 distinct + g.pdf 305 + examples/ 120 graph lines + the audit's probes, about 620 before de-duplication; about 425 after (P4-2; 33-02's AC-33-02.3 band 350-500); 18 shipped datasets and 3 webuse (lifeexp2, lbw, nhanes2l) cached by 33-02.
- test/test_fixtures_are_committed.py: `GENERATORS` (:257, sorted), `META_KEYS` (:402-403), `test_every_fixture_is_named_by_a_test`, `test_make_truth_lists_every_generator` (:501-515).

## User stories

- **US-33-14.1** As the maintainer, I want the whole corpus compared once and its counts recorded with their date and dash commit, so that later WPs and the final gallery can be measured against them.
- **US-33-14.2** As the maintainer, I want to approve the baseline before it is recorded, so that nothing I have not seen becomes the record (Q12).

## Business requirements

- **BR-33-14.1** The whole de-duplicated corpus has been compared once, and its counts are committed with the date and dash commit.
- **BR-33-14.2** The maintainer approved the counts before the commit.
- **BR-33-14.3** The committed record holds no path, user or machine name.
- **BR-33-14.4** Nothing is published in this section: no gallery page, no README change.

## Technical requirements

- **TR-33-14.1 (test)** Create `test/test_corpus_baseline.py` (reads committed files only; no Stata, no Chrome): `TestTheBaseline::test_meta_and_counts` (the five `META_KEYS` with `source == "scripts/corpus/summary.py"`; `examples` at least 1 (whether the count is plausible is judged at 33-14-04's checkpoint and by 33-02's AC-33-02.3, which reports a kept count outside 350-500 rather than forcing it, so the pin never fails on an accepted count); `sum(verdicts.values()) == examples`; for each plot type its `examples` equals the sum of its four verdict counts, and the plot types' `examples` sum to the total; `duplicates` at least 1; `gallery` at most `examples - refused.twoway`), `::test_every_ledger_id_is_a_gaps4_id` (every key of `ledger` is a lead id of a `- **<id> Tracked:**` line of GAPS4.md).
- **TR-33-14.2 (run)** `df -h "${TMPDIR:-/tmp}"` shows at least 20 GB free; `make corpus` to completion (D-33-14.a).
- **TR-33-14.3 (record)** D-33-14.b's command, GENERATORS row and `git add -f`.
- **TR-33-14.4 (closure)** BUGS.md TR-2 entry (title `GAPS4_OPEN["TR-2"]` in test/test_tracking_documents.py), PD-4's closed form: `Fixed <ddmonyyyy> (WP-33, TR-2). make corpus compares <n> twoway examples -- one per combination of plot types and option names, <d> duplicates removed -- from the help files, g.pdf [G-2]/[G-3], examples/ and the audit's probes with dash: ticks and labels, titles, keys, glyph counts, glyph extents, marker shapes and glyph colours (within an RGB tolerance the calibration records, test/fixtures/corpus_verdict_rules.json) are judged, an image score can move a pair from Same to Close, and differences are explained by a known-differences ledger keyed by GAPS4 id (test/fixtures/corpus_ledger.json); the first run, <ddmonyyyy> at <sha7>, is recorded in test/fixtures/corpus_baseline.json (<same> Same, <close> Close, <differs> Differs, <skipped> skipped); twenty of the examples run in every certification gate; the gallery pages and README pairs are built at WP-50's closeout (P4-8). Pinned by test/test_corpus_baseline.py::TestTheBaseline, test/test_corpus_guard.py, test/test_wp33_truth.cscript Q3309-1; fixture test/fixtures/corpus_baseline.json. Closes GAPS4 TR-2 (WP-33, TR-2).`; flip `- [ ]` to `- [x]`; GAPS4.md's TR-2 Tracked line `Closed in WP-33, BUGS.md "<title>", commit pending.`; delete the `"TR-2"` line from `GAPS4_OPEN`; CHANGELOG under `### Fixed in WP-33`: `- make corpus compares about <n> twoway examples with dash, and twenty of them run in every certification gate (WP-33, TR-2)`.
- **TR-33-14.5 Maps.** None (no dash code, no corpus function).

## Boundaries

- No change to the harness, dash, the guard or the ledger here: a harness defect found in the run is reported at the checkpoint and fixed by a follow-up on the owning section's branch, then the run repeats (D-33-14.e for the ledger).
- No file under docs/, no README.md change, no readme_examples.txt change (P4-8, D-33-14.f).
- The agent opens no browser and sets no persistent preference.

## Stata truth

The run is the measurement (twoway drawn fresh for every example by 33-03's runner through `scripts/stata_slot.sh`; dash by 33-04's). Its record is `test/fixtures/corpus_baseline.json`, written by `scripts/corpus/summary.py` from the run folder (`_meta` complete; `git add -f`). No live cscript case of its own (D-33-14.c).

## TDD test stubs

- Test: `test/test_corpus_baseline.py::TestTheBaseline::test_meta_and_counts` -- red at the base (no fixture).
- Test: `test/test_corpus_baseline.py::TestTheBaseline::test_every_ledger_id_is_a_gaps4_id` -- red at the base.
- Existing: `test/test_wp33_truth.cscript` Q3309-1 and `test/test_corpus_guard.py` (33-09).
- No cscript case; no flips; no parity entries.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| the baseline is whole and consistent | pytest TestTheBaseline | corpus_baseline.json | -- |
| the record names only GAPS4 ids | pytest | corpus_baseline.json, GAPS4.md | -- |
| fixture guard (meta, generator, no path) | pytest test_fixtures_are_committed.py | corpus_baseline.json | -- |
| corpus subset each gate | cscript Q3309-1 (33-09) | corpus_guard_truth.json | saved page |

- **AC-33-14.1** The maintainer approved in chat (task 04).
- **AC-33-14.2** TestTheBaseline and test_fixtures_are_committed.py pass on the committed tree.
- **AC-33-14.3** One commit ending `(WP-33 TR-2)`; GAPS4 TR-2 Closed with `commit pending`; `git show --stat HEAD` names no file under docs/ and not README.md.

## Tasks

**Commit boundary.** One commit by 33-14-05: `Run the corpus comparison once and record its baseline (WP-33 TR-2)`. Branch `wp33-s14` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s14`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (33-14-05 for TR-2) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/s14/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/s14 <scratch>/s14/run_test_wp33_truth.do` and read `<scratch>/s14/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s14/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). TR-2 is the harness item: no ledger or `*_KNOWN` row is keyed to it, so steps (1) and (2) are expected to delete nothing (D-33-14.e still adds no ledger row here), and this section changes no code, so step (3) is expected to report no change; any change it does report is named in the hand-back as well. Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="33-14-01">
  <name>Write TR-2's baseline test red</name>
  <files>test/test_corpus_baseline.py</files>
  <action><![CDATA[In worktree $WT (wp33-s14) create test/test_corpus_baseline.py (TR-33-14.1). Run `python3 -m pytest test/test_corpus_baseline.py -q -n0 -p no:cacheprovider > <scratch>/s14/01.log 2>&1` and save the failures to <scratch>/33-14-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "FAILED\|ERROR" <scratch>/s14/01.log` is at least 2; `test -s <scratch>/33-14-01-failure.txt`.]]></verify>
  <done>TR-2's baseline test existed and failed for want of a recorded run.</done>
</task>

<task type="auto" id="33-14-02">
  <name>Run the whole corpus once</name>
  <files>none</files>
  <action><![CDATA[Confirm no other Stata job or full suite is running (`ls /tmp/dash-stata-slot-*.d` empty; no `/tmp/dash-full-suite-*.lock` held). `df -h "${TMPDIR:-/tmp}"` shows at least 20 GB free, else stop and report. Run `make corpus > <scratch>/s14/corpus.log 2>&1` in the background and read its log as it goes (never relaunch it to check on it); on a stage failure rerun that stage's command alone (the recipe's line make printed) and continue with the next. Do not run `make gallery` (P4-8).]]></action>
  <verify><![CDATA[`tail -2 <scratch>/s14/corpus.log` holds the `corpus: <n> examples (<d> duplicates removed): ...` line and `make corpus: results in`; `test -s "${TMPDIR:-/tmp}/dash_corpus/verdicts.jsonl"` succeeds; `git status --short docs README.md` prints nothing.]]></verify>
  <done>The whole de-duplicated corpus was compared once and every example had its verdict row.</done>
</task>

<task type="auto" id="33-14-03">
  <name>Record the baseline from the run</name>
  <files>test/fixtures/corpus_baseline.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Run D-33-14.b's command, add the GENERATORS row (a dict entry in alphabetical position; no function edited) and `git add -f test/fixtures/corpus_baseline.json`. Run `python3 -m pytest test/test_corpus_baseline.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` and D-33-14.d's privacy grep. Prepare D-33-14.d's tables from the run folder with a short scratch Python snippet (verdicts.jsonl, twoway.jsonl, dash.jsonl).]]></action>
  <verify><![CDATA[Both pytest files pass; the privacy grep prints 0; `python3 -c "import json;d=json.load(open('test/fixtures/corpus_baseline.json'));print(d['examples'], d['verdicts'])"` prints the run's counts.]]></verify>
  <done>The run's counts were recorded as a fixture with complete _meta and no path or name.</done>
</task>

<task type="checkpoint" id="33-14-04">
  <name>Get the maintainer's approval of the baseline</name>
  <files>none</files>
  <action><![CDATA[Present D-33-14.d's summary in chat, then ask in these words: "This is the first time every twoway example in the corpus has been drawn by twoway and by dash and compared. The numbers above become WP-33's starting point; approving them records them in a test file and closes the audit item that said no such comparison existed. Nothing is published and the README does not change: the picture gallery is built at the final closeout. Do you approve recording these numbers? Answer yes, or name the examples or differences to look at again." A harness defect the maintainer names stops the section (Boundaries); a systematic difference with a named open item follows D-33-14.e.]]></action>
  <verify><![CDATA[The maintainer wrote an approval in chat for this run (date and commit as presented); the answer is quoted in the hand-back.]]></verify>
  <done>The maintainer approved the first corpus run's counts as WP-33's baseline.</done>
</task>

<task type="auto" id="33-14-05">
  <name>Close TR-2 and commit</name>
  <files>none</files>
  <action><![CDATA[Apply TR-33-14.4 (BUGS, GAPS4 Tracked line, `GAPS4_OPEN`, CHANGELOG) and run `python3 -m pytest test/test_corpus_baseline.py test/test_fixtures_are_committed.py test/test_tracking_documents.py test/test_corpus_guard.py -q -p no:cacheprovider`. No function is edited (the GAPS4_OPEN dict loses a line), so no impact run is needed. Run the Closing steps for TR-2 (Tasks; BRIEF steps (1)-(3)): (1) delete TR-2's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py TR-2`, delete every row it prints (none expected) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/s14) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main). Run `node .gitnexus/run.cjs detect-changes --scope all --repo .`. Stage by path: `git add test/test_corpus_baseline.py test/test_fixtures_are_committed.py test/test_tracking_documents.py BUGS.md GAPS4.md CHANGELOG.md` and `git add -f test/fixtures/corpus_baseline.json` (and, only if a closing step changed them, scripts/corpus/ledger.tsv, the edited `*_KNOWN` file and `git add -f` test/fixtures/corpus_ledger.json and test/fixtures/corpus_guard_truth.json); confirm `git merge-base --is-ancestor s3-bugs HEAD`; commit on wp33-s14; body: the run's date and dash commit, the counts, the approval date, `Regression: test/test_corpus_baseline.py::TestTheBaseline::test_meta_and_counts -- failed at <base> with FileNotFoundError`, `Fixture: test/fixtures/corpus_baseline.json (scripts/corpus/summary.py)`, `BUGS.md: "<title>" (closed)`, `GAPS4: TR-2 Tracked`; grep the message for claude|anthropic before and after. Remove the run folder (`rm -rf "${TMPDIR:-/tmp}/dash_corpus"`) after the commit.]]></action>
  <verify><![CDATA[The pytest run passes; `awk -F'\t' '$1 == "TR-2"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py TR-2` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/s14/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-33 TR-2)`; `git show --stat HEAD | grep -c "docs/\|README.md"` prints 0; the claude|anthropic grep prints 0.]]></verify>
  <done>The first corpus run was recorded as WP-33's baseline and TR-2 was closed.</done>
</task>

## Section completion criteria

- The maintainer's approval in chat; one commit on wp33-s14 holding the baseline record, its test and the tracking edits; TestTheBaseline, test_fixtures_are_committed.py and test_tracking_documents.py green; TR-2 Closed with `commit pending`; no gallery output and no README change; the run folder removed.

## Notes

- **Order in the batch.** Batch 33.7 holds only this section; run it after batch 33.6's gate has finished (the corpus and the gate both want every Stata slot).
- **For WE.7 (WP-50).** The final closeout reruns `make corpus`, builds the gallery with `make gallery` (33-08) and can read this record beside the new run's summary line to show what WP-34..49 changed; this section's record is not regenerated then (it stays the WP-33 baseline).
- **Merge rules:** R5 (BUGS/GAPS4 in place), R7 (fixture from its generator, `git add -f`), R14 (33-02's filter keeps only the plot types dash draws).
- **Appendix B:** HR-4 (README "every difference from twoway") is 48-04's; this section edits no README prose.
- **Help paragraphs owned:** none.
