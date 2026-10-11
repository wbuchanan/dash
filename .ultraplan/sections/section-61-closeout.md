# Section 61: Closeout

> Part of: WP-31 · GAPS3 rows: -- (closeout) · Risk: green · Batch: 21 · Depends on: all · Blocks: -- · Tasks: 7, 6 commits · Case-id prefix: U61

## Overview

**What is true when batch 20 has landed.** Every fix section has closed its entries in BUGS.md, rewritten its GAPS3 §9 Tracked lines, replaced its CHANGELOG markers and appended its truth blocks; `WP31_OPEN` should be empty except for residual entries sections filed under M12 (which are new entries, not WP-31 ids). The shipped files still carry the date `09oct2026` (dash.ado:29, dash_setup.ado:17, dash_parse.mata:529, dash.pkg:26-27 `d Version: 0.1.0  09oct2026` / `d Distribution-Date: 20261009`, dash.sthlp:2 and dash_setup.sthlp:2 `{* *! version 0.1.0  09oct2026}`, and after S59 I5 dash_render.py:60 `Version: 0.1.0  09oct2026`); CHANGELOG.md:3 reads `## 0.1.0, 09oct2026 (release candidate)`; ROADMAP.md has no `## WP-31` section; `test/test_wp31_truth.cscript`'s `w31_secs` still reads `S01 1`; the full suite and `make cert` ran at each batch end but `make gate` not since WP-30.

**After this section** (G3): the date in every shipped file and dash.pkg's Distribution-Date is the closeout date and `test_pkg_metadata.py` pins them equal; CHANGELOG's release line carries the date and `(release candidate)` is dropped or kept per ratification; GAPS3 §9 has no `Open` line; `WP31_OPEN` is `{}` and `test_no_wp31_entry_remains_open` guards it; ROADMAP.md has `## WP-31 · Close the GAPS3 drop-in gaps — DONE` with measurements; the full pytest suite, `make cert` (70 of 70 scripts, no SKIP) and `make gate` are green; GitNexus is re-indexed; every residual is filed per M12 (an open BUGS.md entry graded S3, a GAPS3 Tracked line in the Partly form, a hand-back note).

**Why one section.** The closeout touches every shipped file's date and the tracking constants, which no fix section may do (BRIEF: dates are S61's).

**Test order and commit rule.** S61 is the exception to one-commit-per-row: one commit per step `(WP-31 S61.k)`, k = 1..6, each after its own tests; the full suite, `make cert` and `make gate` run in S61.5 before S61.6 commits. No test-only commit. Steps run on `s3-bugs` in the main checkout (index "Batch 21: closeout, main checkout"), never on `main` (CLAUDE.md rule 5): the merge command is reported at the end.

### Section decisions

- **D-61.a Closeout date** is the day S61.1 runs, written `ddmonyyyy` (lower-case month, as `09oct2026`) and `yyyymmdd` for Distribution-Date. `(release candidate)` on CHANGELOG.md:3 is kept (ratification item 1: the maintainer decides whether 0.1.0 ships at S61 or after the platform package).
- **D-61.b A residual sections could not close** (an `Open` Tracked line left, or an open WP-31 entry) is not fixed in S61: S61.3 converts it to the M12 form (the entry stays open graded S3 `(WP-31)` with `Not fixed: deferred at WP-31's closeout because <why>`, the Tracked line becomes `Partly closed in WP-31 (section NN, commit <sha of the section's last commit>): <what landed>; open: <what remains> (BUGS.md "<title>").`, the `WP31_OPEN` key is deleted and the entry's Resolution leaves the WP-31 open form) and lists it in the hand-back. An `Open` line whose section never landed is reported to the maintainer and stops S61.3 (a batch was not merged).
- **D-61.c `w31_secs`** is written from the closeout cert log: for each `S<NN> start <date> <time>` / `S<NN> end` pair, the seconds per section summed over its blocks, rounded up to a whole second, minimum 1; written as `S01 1 S02 4 ...` in the WP-30 layout (ten tokens a line, `///` continuations). `python3 scripts/cert_shards.py check` must still exit 0 (the wp31 row's seconds in the shard table are also replaced by the script's measured total through `cert_shards.py write <log>` on the closeout cert log, which now times every script).
- **D-61.d ROADMAP WP-31 section** follows WP-30's shape (ROADMAP.md:4763ff): heading with ` — DONE`, a `**GAPS3 closed:** <ids> · **Severity:** S1 (3), S2 (n), S3 (m) · **Effort:** XL · **Depends on:** WP-30` line (the GAPS3 field is new and read by no test; `_parse_roadmap_gaps2` ignores it), the user-story sentence, `### Business requirements` summarising index.md M1-M25, `### Measurements` (the closeout cert wall time per shard, the full-suite time and test count, `make gate` result, axe-core violations on the example pages = 0 from S54's harness, contour exact-cap timing from S23), `### Residuals` (D-61.b list, the index's expected residuals: legend text-before-symbol, contour above the cap, the platform package I1, the module split K5, H5, hash pinning (S59)).

## Risk: [green] -- dates, documents, constants and three gate runs; no drawing changes

**Risk factors.** 1. The gate runs take the longest (full suite ~7 min, `make cert` ~12 min on 3 sessions, `make gate` a `net install` plus every example and scheme). 2. A date bump touches six shipped files at once; a test pins the date string `09oct2026` somewhere (`grep -rn 09oct2026 test/`). 3. GitNexus index (R13).

**Mitigation.** 1. One run each, launched in the background, logs read, never relaunched to check (CLAUDE.md rule 11); `FULL_SUITE_RERUN=1` only if a second full run is needed after a fix. 2. S61.1's test first: `test_pkg_metadata.py::test_every_file_declares_the_same_version` already compares the six; the new assertion compares all seven plus Distribution-Date; the grep finds date pins to flip. 3. `gitnexus analyze --index-only --max-file-size 8192` (CLI, memory note).

## Dependencies

- **Depends on:** every section (S01-S60) landed on `s3-bugs`, each batch's full suite and `make cert` green (G2).
- **Blocks:** nothing; it is last.

## Evidence

- Version/date lines: dash.ado:29 `*! Version: 0.1.0  09oct2026`; dash_setup.ado:17; dash_parse.mata:529; dash.pkg:26 `d Version: 0.1.0  09oct2026`, :27 `d Distribution-Date: 20261009`; dash.sthlp:2 and dash_setup.sthlp:2 `{* *! version 0.1.0  09oct2026}{...}`; dash_render.py:60 (after S59: `Version: 0.1.0  09oct2026`). `test/test_pkg_metadata.py:48-57` `VERSION_SOURCES` (regexes capturing version and date); S59 adds `dash_render.py` and `HEADER_SOURCES`.
- CHANGELOG.md:3 `## 0.1.0, 09oct2026 (release candidate)`; :5 "... `adoupdate` compares the Distribution-Date, now 20261009)".
- test_tracking_documents.py: `WP30_OPEN = {}` at :1580 with its comment; `test_no_wp30_entry_remains_open` :1934-1953 (the model for WP-31's); S01's `WP31_OPEN`, `TestWp31Tracking`, `_gaps3_problems`.
- ROADMAP.md:4763 `## WP-30 · Close the drop-in P1 gaps — DONE`; :4765 the `**GAPS2 closed:** ... · **Severity:** S1 (9), S2 (38), S3 (9) · **Effort:** XL · **Depends on:** WP-29` line; `_wp_sections` reads `— DONE`.
- Makefile: `test-all` :71 (pytest + parity, then cert), `cert` :84, `gate` :87 (`sh scripts/run_release_gate.sh`), `release` :90; CLAUDE.md rule 11 (full suite once, `-n auto`, session lock; `FULL_SUITE_RERUN=1` for a third launch).
- test_wp31_truth.cscript (after S01): `local w31_secs ///` / `    S01 1`; `scripts/cert_shards.py write <log> [<source>]` rewrites the shard table from a run's `[ TIME]` lines (every script must be timed: the closeout `make cert` log is such a run, with the shards' logs concatenated).
- GitNexus: memory `feedback_gitnexus_upkeep.md`: `gitnexus analyze --index-only --max-file-size 8192` after each landing.

## User stories

- **US-61.1** As the release manager, I want every shipped file to carry one date and `adoupdate` to see it, so users get the update.
- **US-61.2** As the maintainer, I want proof that nothing WP-31 opened is still open, and a list of what was deferred.

## Business requirements

- **BR-61.1** One date in seven shipped files and dash.pkg's Distribution-Date, pinned.
- **BR-61.2** No `Open` Tracked line, no open WP-31 entry in the open form, `WP31_OPEN == {}`, no marker left.
- **BR-61.3** ROADMAP.md records WP-31 DONE with measurements and residuals.
- **BR-61.4** Full pytest, `make cert` and `make gate` green on `s3-bugs`; GitNexus re-indexed.

## Technical requirements

- **TR-61.1 (S61.1)** `test/test_pkg_metadata.py`: `test_the_distribution_date_is_the_version_date` (parse `d Distribution-Date: (\d{8})` and the `d Version:` date `ddmonyyyy` → `yyyymmdd` through `datetime.strptime(d, "%d%b%Y")`; assert equal) and `test_the_date_is_not_older_than_the_changelog_release` (CHANGELOG.md:3's date equals the files' date). Then the edits: the seven `0.1.0  09oct2026` lines → `0.1.0  <date>`, dash.pkg:27 `20261009` → `<yyyymmdd>`, CHANGELOG.md:3 and :5.
- **TR-61.2 (S61.2)** CHANGELOG.md: the release line (TR-61.1) and `grep -c '<!-- WP-31' CHANGELOG.md` → 0 (any marker left is a section that did not close: stop and report); when a list's last marker is gone, blank lines between consecutive WP-31 items may be removed (formatting only).
- **TR-61.3 (S61.3)** `test_tracking_documents.py`: `WP31_OPEN = {}` under a comment like WP-30's (:1580-1588); add `TestWp31Tracking::test_no_wp31_entry_remains_open` (copy :1934-1953 with `WP31`/`_wp31_`/`_WP31_OPEN_FORM`), and `test_no_gaps3_line_is_open` (`_parse_gaps3`: no Tracked text matches `_GAPS3_OPEN`); D-61.b conversions; module docstring item 10's last sentence `WP-31's closeout left WP31_OPEN empty; test_no_wp31_entry_remains_open keeps every entry closed with no marker left.`
- **TR-61.4 (S61.4)** ROADMAP.md WP-31 section (D-61.d) appended after the WP-30 section's last line; `w31_secs` (D-61.c) and the shard table via `cert_shards.py write <scratch>/s61/cert.log "the closeout certification run of <date>, three sessions"`.
- **TR-61.5 (S61.5)** Gates: `python3 -m pytest test/ -q > <scratch>/s61/full.log 2>&1` (background; read the log), `make cert > <scratch>/s61/cert.log 2>&1` (background), `make gate > <scratch>/s61/gate.log 2>&1` (background, after cert); a red result is fixed on `s3-bugs` with a regression test (rule 7) and only the failed tests rerun (`--lf`); `scripts/cert_verdict.py` judges the cert logs; `gitnexus analyze --index-only --max-file-size 8192`.
- **TR-61.6 (S61.6)** Hand-back: `<scratch>/s61/handback.md` listing the residuals (D-61.b, D-61.d), the measurements, the merge command `git checkout main && git merge --ff-only s3-bugs` (reported, not run: rule 5), and the ratification items of every section file's Notes still open.
- **TR-61.7 Security.** No shipped behaviour changes; dates only.

## Boundaries

- No fix is made in S61 except to turn a red gate green (with its regression test); no new drawing, no help text beyond the date, no GAPS2.md or DROPIN edit (M23).
- Never commit to `main` (rule 5); never launch a second full run while one is executing; never relaunch to check (rule 11).

## Stata truth

None added. The closeout `make cert` run is the measurement source for `w31_secs` and the shard table (D-61.c). `make cert` and `make gate` are launched here and only here (BRIEF: never inside a section).

## TDD test stubs

- Test: `test/test_pkg_metadata.py::test_the_distribution_date_is_the_version_date` -- green at base (20261009 == 09oct2026) and after; guard.
- Test: `test/test_pkg_metadata.py::test_the_date_is_not_older_than_the_changelog_release` -- red after the files are bumped and before CHANGELOG.md:3 is (S61.1 bumps both in one task; the test is red between the two edits, proven by running it after the first).
- Test: `test/test_tracking_documents.py::TestWp31Tracking::test_no_wp31_entry_remains_open` -- red at the batch-21 base while `WP31_OPEN` is not `{}` (even if empty of real keys, the constant literal differs) or a marker remains; green after S61.3.
- Test: `...::test_no_gaps3_line_is_open` -- red while any `Open (WP-31 section NN).` line remains.
- Guards: the whole suite (S61.5), `make cert` 70/70, `make gate`.
No cscript case (U61 unused); no parity entry.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Dates agree across eight places | pytest `test_pkg_metadata.py` (2 new + existing) | -- | n/a |
| Nothing WP-31 left open | pytest `test_no_wp31_entry_remains_open`, `test_no_gaps3_line_is_open`, `TestNoOpenEntryBlocksARelease` | BUGS.md, GAPS3.md, CHANGELOG.md | n/a |
| ROADMAP WP-31 DONE | pytest `test_tracking_documents.py` (`_wp_sections` reads it) | ROADMAP.md | n/a |
| Everything | full pytest, `make cert`, `make gate` | -- | both |

AC-61.1 `grep -c '<date>' dash.ado dash_setup.ado dash_parse.mata dash.pkg dash.sthlp dash_setup.sthlp dash_render.py` → 1 each; `grep -c 'Distribution-Date: <yyyymmdd>' dash.pkg` → 1. AC-61.2 `grep -c 'Tracked:\*\* Open' GAPS3.md` → 0; `grep -c '<!-- WP-31' CHANGELOG.md` → 0; `grep -c '^WP31_OPEN = {}$' test/test_tracking_documents.py` → 1. AC-61.3 `grep -c '^## WP-31 .* — DONE$' ROADMAP.md` → 1. AC-61.4 full.log ends with 0 failed; cert.log: `scripts/cert_verdict.py` prints OK with 70 passed, 0 skipped; gate.log ends with the gate's pass line (`scripts/run_release_gate.sh`'s last line: read it at run time).

## Tasks

**Commit boundary.** One commit per step, subjects: S61.1 `Date every shipped file and the distribution date <date> (WP-31 S61.1)`; S61.2 `Date the 0.1.0 release line and tidy the WP-31 lists (WP-31 S61.2)`; S61.3 `Close WP-31's tracking: no entry, Tracked line or marker left open (WP-31 S61.3)`; S61.4 `Record WP-31 as done with its measurements and time its truth blocks (WP-31 S61.4)`; S61.5 commits only if a gate fix was needed: `Fix <what> found by the WP-31 closeout gates (WP-31 S61.5)`; S61.6 `Hand back WP-31 (WP-31 S61.6)` (the hand-back note is written to `.ultraplan/handoff/WP31-HANDBACK.md`, a user record). Every command runs in the main checkout on `s3-bugs`; `D=$(date +%d%b%Y | tr A-Z a-z)`, `N=$(date +%Y%m%d)`.

<task type="auto" id="61-01">
  <name>Bump every date and pin the distribution date</name>
  <files>test/test_pkg_metadata.py, dash.pkg, CHANGELOG.md</files>
  <action><![CDATA[`git -C <repo> branch --show-current` prints s3-bugs; `git status --porcelain` is empty. Add TR-61.1's two tests to test/test_pkg_metadata.py and run the file (both green at the base). Then `sed -i '' -e "s/0\.1\.0  09oct2026/0.1.0  $D/" dash.ado dash_setup.ado dash_parse.mata dash.pkg dash.sthlp dash_setup.sthlp dash_render.py` and `sed -i '' -e "s/^d Distribution-Date: 20261009$/d Distribution-Date: $N/" dash.pkg`; run `python3 -m pytest test/test_pkg_metadata.py -q -n0 -p no:cacheprovider` and record that `test_the_date_is_not_older_than_the_changelog_release` is red in <scratch>/61-01-failure.txt; then `sed -i '' -e "3s/09oct2026/$D/" -e "5s/20261009/$N/" CHANGELOG.md`; rerun (green). `grep -rn 09oct2026 test/` -- flip any pin of the old date in place with `Flipped (WP-31 S61.1)`. Stage the seven shipped files, CHANGELOG.md, test/test_pkg_metadata.py and any flipped test; commit.]]></action>
  <verify><![CDATA[`grep -c "$D" dash.ado dash_setup.ado dash_parse.mata dash.pkg dash.sthlp dash_setup.sthlp dash_render.py` prints 1 for each; `grep -c "Distribution-Date: $N" dash.pkg` prints 1; `sed -n 3p CHANGELOG.md` holds `$D`; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 S61.1)`.]]></verify>
  <done>Every shipped file, dash.pkg's Distribution-Date and the CHANGELOG release line carried the closeout date, pinned equal.</done>
</task>

<task type="auto" id="61-02">
  <name>Check the CHANGELOG lists are closed</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[`grep -n '<!-- WP-31' CHANGELOG.md`: if any marker remains, stop and report its id and section (the section did not close; the merger must land it first). Otherwise remove blank lines between consecutive WP-31 items within a list only (no rewording), and confirm `### Fixed in WP-31` sits directly above `### Fixed in WP-30`. Run `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider`; commit if the file changed.]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-31' CHANGELOG.md` prints 0; the pytest run reports 0 failed; `grep -c '^### Fixed in WP-31$' CHANGELOG.md` prints 1.]]></verify>
  <done>The CHANGELOG held WP-31's lines with no marker left.</done>
</task>

<task type="auto" id="61-03">
  <name>Empty the allowance and guard it</name>
  <files>test/test_tracking_documents.py, BUGS.md, GAPS3.md</files>
  <action><![CDATA[Write `test_no_wp31_entry_remains_open` and `test_no_gaps3_line_is_open` (TR-61.3) first and run them: record the red output in <scratch>/61-03-failure.txt (`WP31_OPEN` not `{}`, or Open lines listed). For each remaining `WP31_OPEN` key or `Open` Tracked line apply D-61.b (or stop if the section never landed). Replace the `WP31_OPEN = {` ... `}` literal by `WP31_OPEN = {}` under its comment extended with `S61 left it {} (10oct2026 closeout).`; update docstring item 10's last sentence. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; commit.]]></action>
  <verify><![CDATA[`grep -c '^WP31_OPEN = {}$' test/test_tracking_documents.py` prints 1; `grep -c 'Tracked:\*\* Open' GAPS3.md` prints 0; `grep -c 'Not fixed because WP-31 section' BUGS.md` prints 0; the pytest run reports 0 failed, TestNoOpenEntryBlocksARelease included; `git log -1 --format=%s` ends `(WP-31 S61.3)`.]]></verify>
  <done>No WP-31 entry, Tracked line or marker was left open; the residuals were in the M12 form and the guard test kept it so.</done>
</task>

<task type="auto" id="61-04">
  <name>Run the three gates</name>
  <files>none</files>
  <action><![CDATA[Launch in the background and wait, reading each log once it ends (never relaunch to check): (1) `python3 -m pytest test/ -q > <scratch>/s61/full.log 2>&1`; (2) after (1), `make cert > <scratch>/s61/cert.log 2>&1`; (3) after (2), `make gate > <scratch>/s61/gate.log 2>&1`. Judge (2) with `python3 scripts/cert_verdict.py <the shard logs the run wrote, per scripts/run_cert_suite.sh>`. If any is red: diagnose, write the regression test, fix on s3-bugs, rerun only the failed tests (`python3 -m pytest --lf -q`, or the one cscript through the driver), commit as S61.5's subject, and rerun the whole gate that was red once (`FULL_SUITE_RERUN=1` for a third full launch). Then `gitnexus analyze --index-only --max-file-size 8192`.]]></action>
  <verify><![CDATA[`tail -1 <scratch>/s61/full.log` reports 0 failed and 0 errors; cert_verdict prints 70 passed, 0 skipped, 0 failed; the gate log ends with scripts/run_release_gate.sh's pass line and no `FAIL`; `gitnexus` printed its index summary.]]></verify>
  <done>The full suite, the 70-script certification run and the release gate were green on s3-bugs, and the index was current.</done>
</task>

<task type="auto" id="61-05">
  <name>Record WP-31 done and time the truth blocks</name>
  <files>ROADMAP.md, test/test_wp31_truth.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[Append the WP-31 section to ROADMAP.md after WP-30's last line per D-61.d, with the measurements read from <scratch>/s61/full.log (tests, time), the cert shard logs (`[SHARD]` and wall times), gate.log, S54's axe-core report and S23's timing test output. Write `w31_secs` from the cert logs' `S<NN> start/end` lines (D-61.c) into test/test_wp31_truth.cscript's parts section (replacing `    S01 1`), and regenerate the shard table: `cat <the shard logs> > <scratch>/s61/cert-all.log; python3 scripts/cert_shards.py write <scratch>/s61/cert-all.log "the closeout certification run of $D, three sessions"`. Run `python3 scripts/cert_shards.py check` and `python3 -m pytest test/test_tracking_documents.py test/test_cert_shards.py test/test_cscript_hygiene.py -q -p no:cacheprovider`; commit.]]></action>
  <verify><![CDATA[`grep -c '^## WP-31 .* — DONE$' ROADMAP.md` prints 1; `python3 scripts/cert_shards.py check` exits 0; `grep -c 'S01 ' test/test_wp31_truth.cscript` is at least 2 (the secs table and the block); the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 S61.4)`.]]></verify>
  <done>ROADMAP.md recorded WP-31 as done with its measurements, and the truth script's parts and the shard table carried the measured seconds.</done>
</task>

<task type="checkpoint" id="61-06">
  <name>Approve the residual list and the release line</name>
  <files>none</files>
  <action><![CDATA[Show the maintainer: the residuals (D-61.b conversions and D-61.d's list) with each open BUGS.md title; whether CHANGELOG.md:3 keeps `(release candidate)` (D-61.a); the open ratification items collected from every section file's Notes. Wait for the answers; apply a "drop (release candidate)" answer to CHANGELOG.md:3 and commit it under S61.2's subject with `--amend` only if S61.2's commit is HEAD~2 or nearer and unpushed; otherwise a new commit `(WP-31 S61.2)`.]]></action>
  <verify><![CDATA[The maintainer's answers are recorded in <scratch>/s61/handback.md under "Ratified".]]></verify>
  <done>The maintainer ratified the residual list and the release line.</done>
</task>

<task type="auto" id="61-07">
  <name>Write the hand-back and report the merge command</name>
  <files>.ultraplan/handoff/WP31-HANDBACK.md</files>
  <action><![CDATA[Create .ultraplan/handoff/WP31-HANDBACK.md (TR-61.6): what landed (109 entries by section, the five S61 commits), the measurements, the residuals with their BUGS.md titles and GAPS3 Tracked lines, the ratified decisions, and the merge command `git checkout main && git merge --ff-only s3-bugs` (not run). Commit it with subject `Hand back WP-31 (WP-31 S61.6)`; `git log -6 --format=%B | grep -Eic 'claude|anthropic'` prints 0. Print the merge command as the last line of the hand-back report.]]></action>
  <verify><![CDATA[`test -s .ultraplan/handoff/WP31-HANDBACK.md`; `git log -1 --format=%s` ends `(WP-31 S61.6)`; `git branch --show-current` prints s3-bugs; `git status --porcelain` is empty.]]></verify>
  <done>WP-31 was handed back with its residuals, measurements and the merge command, on s3-bugs and not on main.</done>
</task>

## Section completion criteria

- Five or six commits on `s3-bugs` ending `(WP-31 S61.k)`; none on `main`.
- Dates equal in eight places and pinned; `WP31_OPEN == {}`; no `Open` Tracked line; no marker; ROADMAP WP-31 DONE; `w31_secs` and the shard table measured.
- Full pytest 0 failed; `make cert` 70 of 70, no SKIP; `make gate` green; GitNexus re-indexed; hand-back written with the merge command.

## Notes

- **Rule 5:** never `git checkout main` to commit; report `git checkout main && git merge --ff-only s3-bugs`.
- **Rule 11:** one full run; read its log; `FULL_SUITE_RERUN=1` only for a third launch after a fix.
- **R13:** GitNexus after the gates.
- **Memory:** a skip is not a pass: `make cert` with any `[ SKIP]` is red; restore `python_exec` in `~/.stata19/console/stata19.rc` if the sessions dropped it.
- **Trap:** `sed -i ''` is BSD sed's in-place form (macOS); the `{* *! version ...}` lines in the two sthlp files match the same `0.1.0  09oct2026` pattern.
- **Trap:** `cert_shards.py write` needs every registered script timed in the log; concatenate every shard's log first.
- **Decisions for maintainer ratification:** (1) keep or drop `(release candidate)` (D-61.a); (2) the residual conversions (D-61.b); (3) the ROADMAP `**GAPS3 closed:**` field has no reader (D-61.d) -- add one, or accept it as text.
