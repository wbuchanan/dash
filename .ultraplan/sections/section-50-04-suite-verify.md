# Section 50-04: make test at most 5 minutes, recorded

> Part of: WP-50 (Test-suite speed, Q29; CLAUDE.md rule 11) · Items: none · Risk: green · Batch: 50.3 · Depends on: 50-02, 50-03 · Blocks: WP-50 WE (the final closeout) · Tasks: 4, 1 commit · Case-id prefix: Q5004

## Overview

**What is wrong today.** Nothing records whether the speed work reached its target. PRD §8: "WP-50: `make test` runs in at most 5 minutes, or the plan records the measured bottleneck and its fix"; gate G4: "`make test` at most 5 minutes or the measured bottleneck recorded (PRD §8)". The last recorded figures are 50-01's profile (`.ultraplan/handoff/wp50-profile.txt`) before 50-02 and 50-03; the handoff report `.ultraplan/handoff/TEST-PERFORMANCE.md` still describes the 07oct2026 suite ("5,038 s over 6 workers"), and ROADMAP.md's last gate line says "The suite now takes about 40 minutes wall, past CLAUDE.md's five-minute target" (:5155).

**After this section.** One batch-end measurement of `make test` and `make test-all` after 50-02 and 50-03 landed, compared with 50-01's; the result written into ROADMAP.md (the WP-50 entry's measurements) and a rewritten TEST-PERFORMANCE.md (§1 the new numbers, the levers taken with their measured savings, the levers not taken and why, the history kept below); and either `make test: <s> s, at or under 300 s` or the measured bottleneck with its proposed fix, its estimated saving and what it would cost.

**Why a section.** The measurement must ride on the batch-end run (memory rule), so it is its own batch, 50.3, after both 50.2 sections.

**Test order and commit rule.** 50-04-01 is the timed batch-end run (orchestrator, no code); 50-04-02 runs the report; 50-04-03 writes the documents and commits `(WP-50 50-04)`; 50-04-04 is the maintainer's sign-off. No test is added or changed except the documents' pins (none expected).

### Section decisions

- **D-50-04.a — The runs.** Exactly as 50-01's D-50-01.a: at batch 50.3's step k.4, `DASH_SUITE_TIMING=<scratch>/timing-make-test-after.json make test`, then `DASH_SUITE_TIMING=<scratch>/timing-test-all-after.json make test-all`, one after the other; the second run is k.4's gate. No third run.
- **D-50-04.b — Pass or record.** If `make test`'s wall is at most 300 s, the result line is `make test: <s> s wall (<n> passed), at or under the five-minute target (CLAUDE.md rule 11, PRD §8)`. Otherwise the record names: the bottleneck (the item, group, file or phase with its seconds from the after-profile), the fix proposed for it (one of: a lever from TEST-PERFORMANCE.md/TEST-PRUNING-ANALYSIS.md not taken, a newly found one, or a ruling the maintainer must make such as cert scope or tiering), its estimated saving in seconds with the basis of the estimate, and its cost (coverage moved, risk). No fix is applied in this section.
- **D-50-04.c — CLAUDE.md is not edited.** Rule 10 says "`pyproject.toml` makes it parallel (`-n auto`) ... finishes in about two minutes", which the file (`-n 8 --dist loadgroup`) and the measurements contradict; 50-04-04 proposes corrected sentences to the maintainer, who edits CLAUDE.md if they agree.

## Risk: [green] -- documents only

**Why.** Two runs and two documents. **Risk factors.** 1. A red gate. 2. Numbers from different interpreters compared as one. **Mitigation.** 1. k.5 fixes first; the timing is read from the green run, a rerun noted. 2. `make test` (Stata's Python) is compared with 50-01's `make test`, `make test-all` with 50-01's `make test-all`, never across.

## Dependencies

- **Depends on:** 50-02, 50-03 (landed in batch 50.2).
- **Blocks:** WP-50's WE (WE.3 adds `## WP-50 · Test-suite speed — DONE` to ROADMAP.md with this section's numbers; WE.7 regenerates the corpus gallery).
- **Batch 50.3** alone.

## Evidence

- PRD §8 (the target sentence); index gate G4; CLAUDE.md rules 2, 10, 11.
- ROADMAP.md:5089 (WP-30's `make test` 459 s), :5123 (WP-31 898 s), :5154-5155 (WP-32 gates 995 s and 1,562 s pytest; "about 40 minutes wall").
- .ultraplan/handoff/TEST-PERFORMANCE.md (135 lines: §1 where the time goes, §2 plan A-F, §3 projection, §4 order) and TEST-PRUNING-ANALYSIS.md (158 lines); .ultraplan/handoff/wp50-profile.txt (50-01, with the lever list, the maintainer's two answers and the levers 50-02/50-03 recorded as taken or not).
- scripts/suite_profile.py (50-01) prints both profiles' tables.

## User stories

- US-50-04.1 As the maintainer, I want the suite's time after the speed work measured and written down so that I know whether rule 11 holds and, if not, what to do next.

## Business requirements

- BR-50-04.1 `make test`'s wall time after WP-50 is recorded beside 50-01's, from one batch-end run.
- BR-50-04.2 Either the five-minute target is met, or the bottleneck and its fix are recorded with seconds (PRD §8).
- BR-50-04.3 TEST-PERFORMANCE.md describes the suite as it is, with the history kept.

## Technical requirements

- TR-50-04.1 `python3 scripts/suite_profile.py report <after timing files> --cert <after logs>` and the same for 50-01's files; a before/after table (pytest wall, test-seconds, longest item/group, cert wall per session, the WP truth scripts' seconds and the number of dash loads per session, A-3) written to `.ultraplan/handoff/wp50-profile.txt` under `After (<date>)`.
- TR-50-04.2 TEST-PERFORMANCE.md: a new §0 "WP-50 result (<date>)" at the top with the table, the levers taken (50-02, 50-03 commits by subject) and their measured savings, the levers not taken with reasons, and the D-50-04.b line; the old sections kept under "History (07-10oct2026)".
- TR-50-04.3 ROADMAP.md: the measurements block for WP-50 (the WE.3 entry's gate line takes these numbers; this section writes the paragraph `**Suite speed.** make test <before> s -> <after> s (<workers> workers, Stata's Python); make test-all pytest <b> s -> <a> s, cert <b> s -> <a> s wall. <D-50-04.b line>.` under the WP-50 heading if WE.3 has not yet added it, else into it).

## Boundaries

- No code, test or configuration change; no CLAUDE.md edit (D-50-04.c); no new lever applied.
- No run beyond D-50-04.a's two.

## Stata truth

None.

## TDD test stubs

None: the section adds no function. The documents are read by no test today; if test_tracking_documents.py reads ROADMAP.md's WP sections (the WE closeout tests), the paragraph's form follows the WE.3 form so those tests stay green -- run `python3 -m pytest test/test_tracking_documents.py -q -n0` after writing it.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| the measurement | batch-end runs (D-50-04.a) | -- | n/a |
| the documents | test_tracking_documents.py (if it reads them) | -- | n/a |

- AC-50-04.1 wp50-profile.txt has Before and After tables; TEST-PERFORMANCE.md §0 and ROADMAP.md carry the D-50-04.b line.
- AC-50-04.2 The maintainer signed the result off (50-04-04).

## Tasks

**Commit boundary.** 50-04-03 commits `Record the suite's time after the speed work (WP-50 50-04)` on `wp50-s04` (wp50-profile.txt, TEST-PERFORMANCE.md, ROADMAP.md). 50-04-01, -02, -04 commit nothing.

<task type="auto" id="50-04-01">
  <name>Run the timed batch-end suites</name>
  <files>none</files>
  <action><![CDATA[Orchestrator, at batch 50.3's step k.4, in the main checkout after 50-02 and 50-03 landed: `df -h /`; `DASH_SUITE_TIMING=<scratch>/timing-make-test-after.json make test > <scratch>/make-test-after.log 2>&1`; then `DASH_SUITE_TIMING=<scratch>/timing-test-all-after.json make test-all > <scratch>/make-test-all-after.log 2>&1`, copying the cert sessions' run_all_cscripts.log files into <scratch>/after-s1..s3/. Never two at once; a red run is fixed per k.5 and only the failed tests rerun; a rerun of a suite needs `FULL_SUITE_RERUN=1` and is noted.]]></action>
  <verify><![CDATA[Both timing files parse as JSON; both logs end with their summary lines (pytest's, and run_all_tests.sh's `whole suite: <s> s wall`).]]></verify>
  <done>`make test` and `make test-all` ran once each after the speed work, with per-test timing kept.</done>
</task>

<task type="auto" id="50-04-02">
  <name>Compare the profiles before and after</name>
  <files>none</files>
  <action><![CDATA[Apply TR-50-04.1. Decide D-50-04.b: compute `make test`'s wall from make-test-after.log (pytest's own `in <s>s` figure); if over 300 s, read the after-profile's critical path and slowest phase and write the bottleneck record (item or phase, seconds, proposed fix, estimated saving and its basis, cost) into wp50-profile.txt.]]></action>
  <verify><![CDATA[wp50-profile.txt holds the After table and either the at-or-under line or a bottleneck record with all four parts.]]></verify>
  <done>The before/after comparison and the pass-or-bottleneck verdict are written down.</done>
</task>

<task type="auto" id="50-04-03">
  <name>Write the documents and commit</name>
  <files>.ultraplan/handoff/TEST-PERFORMANCE.md, ROADMAP.md, .ultraplan/handoff/wp50-profile.txt</files>
  <action><![CDATA[Apply TR-50-04.2 and TR-50-04.3. Run `python3 -m pytest test/test_tracking_documents.py -q -n0`. Commit the three files (stage each by path; `git add -f` wp50-profile.txt if .gitignore matches it); grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[pytest 0 failed; `git log -1 --format=%s` ends `(WP-50 50-04)`; `grep -c "make test:" .ultraplan/handoff/TEST-PERFORMANCE.md` prints at least 1.]]></verify>
  <done>The suite's measured time after WP-50, and the verdict against five minutes, are recorded in the handoff report and ROADMAP.md.</done>
</task>

<task type="checkpoint" id="50-04-04">
  <name>Sign off the suite-speed result</name>
  <files>none</files>
  <action><![CDATA[Present the before/after table and the D-50-04.b line. If the target was missed, present the bottleneck record and ask whether to open a follow-up (a BUGS.md entry or a new WP) for its fix. Propose corrected sentences for CLAUDE.md rule 10 (the `-n 8 --dist loadgroup` default and the measured duration) and, if the maintainer's scope ruling at 50-01-04 changed it, rule 11 (what "the entire test suite" covers); the maintainer edits CLAUDE.md if they agree.]]></action>
  <verify><![CDATA[The maintainer signs off, and answers on the follow-up and the CLAUDE.md sentences.]]></verify>
  <done>The maintainer signed off the measured suite time and decided the follow-up and the CLAUDE.md wording.</done>
</task>

## Section completion criteria

- Two batch-end runs; wp50-profile.txt Before/After; TEST-PERFORMANCE.md §0; ROADMAP.md paragraph; the maintainer's sign-off.

## Notes

- **Batch order (index k.3/k.4):** Batch 50.3 inverts k.3/k.4 by design: 50-04-01 is k.4 (nothing has landed before it). 50-04-03's commit touches only ROADMAP.md, TEST-PERFORMANCE.md and wp50-profile.txt. It is landed with picks.sh after k.4 and checked with `python3 -m pytest test/test_tracking_documents.py -q -n0` only, with no further full launch.
- **Not a gate by itself:** G4 is met when `make test` is at most 300 s or the bottleneck record exists (PRD §8); a missed target does not block WP-50's closeout, the record does.
- **Merge rules touched:** R14 (commit message) only.
- **What the numbers mean (REVIEW-5 R5-9).** 50-02's levers cut `make test-all`'s cert half only; `make test` moves only by 50-03's levers and the tier moves the maintainer ruled at 50-01-04. Compare the after-profile with 50-01's projection line and say in the D-50-04.b line which ruling applied (tier moves made, or the bottleneck outcome accepted).
- **Before the commit (CLAUDE.md rule 4; REVIEW-5 R5-39):** `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp50-s04 pull --ff-only . main` (BRIEF "Pull form": inside a worktree, with `$WT` the absolute worktree path; CLAUDE.md rule 4; expect `Already up to date.` at the batch base); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch. WP-50 closes no GAPS4 item, so BRIEF's corpus-ledger, known-differences and guard steps (1)-(3) have no lead id and are not taken. Then run `python3 -m pytest test/test_tracking_documents.py -q -n0`, `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back), grep the message for `claude|anthropic`, commit, and grep again.
- **Commit-body lines:** the before and after `make test` walls, the verdict line.
