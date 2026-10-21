# Section 50-01: Profile the gate and name the bottlenecks

> Part of: WP-50 (Test-suite speed, Q29; CLAUDE.md rule 11) · Items: none · Risk: green · Batch: 50.1 · Depends on: none (WP-49's WE closed) · Blocks: 50-02, 50-03 · Tasks: 4, 1 commit · Case-id prefix: Q5001

## Overview

**What is wrong today.** CLAUDE.md rule 11: "The entire test suite should be capable of executing in less than five minutes." PRD §8 makes the WP-50 target concrete: "`make test` runs in at most 5 minutes, or the plan records the measured bottleneck and its fix." The last measurements are far above it and older than WP-33..WP-49 ([C] §7.1): the WP-32 gate of 19oct2026 ran `make test-all`'s pytest half (38,224 passed, with the batch tier) in **1,562 s**, and the whole gate took "about 40 minutes wall" (ROADMAP.md:5155); WP-31's whole-suite pytest (without the batch tier, 8 workers) took 898 s (ROADMAP.md:5123); `make cert` 804 s over three sessions, its 69 scripts summing 2,127 s with test_wp30_truth (566.6 s) and test_wp31_truth (456.4 s) 48% of it (test/run_all_cscripts.do:76-157). WP-33..WP-49 add about 221 items' regression tests and fourteen per-WP truth scripts (PD-6: WP 33, 34, 35, 36, 37, 40, 41, 42, 43, 44, 45, 46, 47, 49), each a `* * *` shard row that loads dash_parse.mata and dash.ado in all three sessions ([C] §2.4.6). Nothing has measured the suite since.

**After this section.** One measured profile of the suite as WP-49 left it: `make test` (the target, Stata's Python, bokeh 3.8) and `make test-all` (the gate) with per-test, per-file and per-worker seconds (`DASH_SUITE_TIMING`, test/suite_timing.py), the cert's per-script seconds (`[ TIME]` lines) and per-block seconds of every WP truth script (the `S<MM> start/end` lines), the fixed cost per cert script, the pytest critical path (the longest single test or xdist group), and collection time. A report script turns the logs into one table, with a projection of `make test` after the coverage-keeping levers. The ranked bottlenecks and the coverage-keeping levers that address them (splits, the render cache under its 25% rule, shared sweeps, `run` loads, whole-run truth scripts, the shard rewrite) are listed in wp50-profile.txt by 50-01-03, and 50-02 and 50-03 work from that list: they are technical means that keep every test, so nobody is asked to approve them. The maintainer is asked two plain questions only, with the projection in hand (50-01-04): whether named files move from `make test` to the batch-end run if five minutes cannot be reached otherwise, and whether the Stata certification scripts stay out of `make test`.

**Why a section of its own.** The memory rule ("Full suite only at batch end ... timing rides on the batch-end run") forbids timing runs inside a batch; batch 50.1's own end-of-batch run is the measurement, and both 50.2 sections need its numbers first.

**Test order and commit rule.** 50-01-01 writes `scripts/suite_profile.py` and its unit tests and commits them `(WP-50 50-01)`; 50-01-02 is the orchestrator's batch-end run with the timing switches on (no code); 50-01-03 runs the report on those logs; 50-01-04 is the checkpoint. No other commit.

### Section decisions

- **D-50-01.a — What is measured, once.** At batch 50.1's step k.4 the orchestrator runs, one after the other (never two at once; CLAUDE.md rule 10): (1) `DASH_SUITE_TIMING=<scratch>/timing-make-test.json make test` -- the PRD's target, under Stata's Python; (2) `DASH_SUITE_TIMING=<scratch>/timing-test-all.json make test-all` -- the gate (pytest with the batch tier, then cert), which is k.4's normal run. The second is the session's second full launch, the guard hook's limit; no third run. `DASH_CERT_PROFILE` is NOT set (Stata's profiler adds its own cost to every script; per-script and per-block seconds come from the `[ TIME]` and `S<MM> start/end` lines the runner and the truth scripts already print).
- **D-50-01.b — The report.** `scripts/suite_profile.py report <timing.json> [<timing.json>] --cert <run_all_cscripts.log>... [--estimate <seconds>]...` prints: pytest wall, the sum of test-seconds, worker imbalance (busiest minus least busy), the 30 slowest files and tests, the longest xdist group (the wall floor under `--dist loadgroup`), setup vs call vs teardown totals, collection seconds; cert wall per session, each script's seconds, each WP truth script's blocks over 20 s, and the fixed cost per script (script seconds minus the sum of its block seconds); and the target line `make test: <s> s against 300 s`; with one or more `--estimate` values, also D-50-01.d's projection line from the first timing file's test-seconds. Pure stdlib; it reads only the files it is given.
- **D-50-01.c — Collection time.** Measured separately inside the report from the timing file's first-test start minus the session start if test/suite_timing.py records it; if it does not, 50-01-01 adds the session start time to its JSON (`"session_start"`, `"first_test_start"`) -- a test-tooling change with a unit test.
- **D-50-01.d — The projection (REVIEW-5 R5-9).** The coverage-keeping levers cannot be assumed to reach 300 s: WP-31's whole-suite pytest was about 6,000 test-seconds on 8 workers (898 s), WP-32's gate pytest 1,562 s (ROADMAP.md:5155), and WP-33..49 add the tests of 221 items, while 300 s at 0.85 efficiency allows about 2,040 test-seconds (D-50-03.a). 50-01-03 therefore writes one projection line, `projection: (<make test test-seconds> - <estimated savings of the levers that keep every test in make test>) / (8 x 0.85) = <s> s against 300 s`, each estimate with its basis (the profile's seconds of the tests a lever touches, and TEST-PERFORMANCE.md §3's estimate for F), so the maintainer sees before any change whether the target needs the answer to 50-01-04's first question. 50-02's certification levers do not count towards it: `make test` runs no cscript.

## Risk: [green] -- measurement only

**Why.** No product code changes; one test-tooling script, possibly two fields in the timing report. **Risk factors.** 1. A red gate (a regression from WP-49) would make the timing unrepresentative. 2. Running both suites back to back on one machine. **Mitigation.** 1. k.5 fixes come first; the measurement is taken from the green run (or a re-run with `FULL_SUITE_RERUN=1`, the guard's deliberate override, noted in the report). 2. `df -h` before (the temp-leak memory: 15-20 GB per run was once leaked; the per-process folder fixed it).

## Dependencies

- **Depends on:** WP-49 closed (WE done), so the profile is of the full WP-33..49 suite.
- **Blocks:** 50-02 (cert levers), 50-03 (pytest levers).
- **Batch 50.1** alone.

## Evidence

- `pyproject.toml:9` `addopts = "-n 8 --dist loadgroup"` (CLAUDE.md rule 10's `-n auto` is stale; the file says 8, measured 07oct2026 "-n 6/8/10/12 took 111/94/89/88 s").
- `Makefile:44-50` `make test` (Stata's Python via `scripts/stata_python_exec.sh`, `DASH_STRICT=1 DASH_BASELINE=stata`, release and batch tiers deselected by test/conftest.py:220-300); `:80-81` `make test-all` -> scripts/run_all_tests.sh (pytest `-n 8` with `DASH_TEST_TIER=batch`, then `scripts/run_cert_suite.sh` with 3 sessions; logs in `$TMPDIR/dash_all_tests.XXXXXX/{pytest.log,cert.log}`).
- test/suite_timing.py (`DASH_SUITE_TIMING`, per-test setup/call/teardown, per-file, per-worker; registered at conftest.py:116-118).
- test/run_all_cscripts.do: shard table :75-158 (69 rows, seconds of 18oct2026), `[ TIME] <script> timer=..s wall=..s` per script; scripts/cert_shards.py (`seconds_from_log` :218, `wp30_seconds` :160) already reads them.
- Handoff analyses (07-10oct2026): .ultraplan/handoff/TEST-PERFORMANCE.md §1-§4 and TEST-PRUNING-ANALYSIS.md §1-§5 (levers S1-S7, C1-C3, P1-P5, tiering; "pytest plus cert in 5 minutes on this machine is not reachable"); [C] §7.2 levers already in place (do not re-propose): xdist loadgroup with tryfirst grouping, release/batch tiers, `render_models`, the compile-once app loader, the ServerAppBuilder source cache, `_dash_do_render` compiling once per session, twoway oracles from fixtures, sharded cert with self-splitting truth scripts, the per-process temp folder, the session lock.

## User stories

- US-50-01.1 As the maintainer, I want one measured profile of the suite as it stands after WP-49 so that the speed work targets the real bottlenecks.
- US-50-01.2 As a coding agent, I want the bottlenecks named with seconds so that 50-02 and 50-03 know what to change.

## Business requirements

- BR-50-01.1 `make test`'s wall time and its slowest files, tests and xdist groups are recorded from one run.
- BR-50-01.2 The gate's pytest and cert walls, each cert script's seconds, each WP truth script's slow blocks and the per-script fixed cost are recorded from one run.
- BR-50-01.3 The ranked bottleneck list and the coverage-keeping levers for it are recorded before any speed change; the maintainer answers, with the projection in hand, whether named files leave `make test` for the batch-end run and whether certification stays out of `make test`.

## Technical requirements

- TR-50-01.1 New `scripts/suite_profile.py` (stdlib only; `report` subcommand per D-50-01.b; `main(argv)` returns 0/2; reads only named files; no shell). New `test/test_suite_profile.py` with synthetic timing JSON and a synthetic cert log fragment (two scripts, one truth script with three blocks) asserting each printed figure.
- TR-50-01.2 If needed (D-50-01.c), test/suite_timing.py's `summarise` adds `session_start` and `first_test_start` (epoch seconds) to its JSON; a test in test/test_suite_timing.py (create if absent; grep for an existing test of suite_timing first).
- TR-50-01.3 The report's output and the four log paths are saved to `.ultraplan/handoff/wp50-profile.txt` (committed in 50-04's commit, not here) and its table pasted into the checkpoint.

## Boundaries

- No change to test selection, workers, tiers, cscripts or product code (50-02, 50-03).
- No extra full run beyond D-50-01.a's two; no `DASH_CERT_PROFILE`.

## Stata truth

None (no twoway comparison; the cert run is the measurement).

## TDD test stubs

- Test: the report prints pytest wall and test-seconds from a synthetic timing file -- `test/test_suite_profile.py::TestReport::test_pytest_totals` (red: no script).
- Test: the slowest-group line names the xdist group with the largest summed call time -- `::test_longest_group` (red).
- Test: cert script seconds, slow blocks and fixed cost from a synthetic log -- `::test_cert_tables` (red).
- Test: the target line reads `make test: <s> s against 300 s` -- `::test_target_line` (red).
- Test: given lever estimates, the projection line reads `projection: (<t> - <e>) / (8 x 0.85) = <s> s against 300 s` with the arithmetic right -- `::test_projection_line` (red; the report takes `--estimate <seconds>` once per lever, so 50-01-03 can print it).
- Test (if TR-50-01.2): `test/test_suite_timing.py::TestSummary::test_session_start_recorded` (red).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| report arithmetic | pytest test_suite_profile.py | synthetic in-test data | n/a |
| the profile itself | batch-end runs (D-50-01.a) | the four logs | n/a |

- AC-50-01.1 test_suite_profile.py green; the report runs on the real logs without error.
- AC-50-01.2 The checkpoint shows `make test`'s wall against 300 s, the projection and the ranked list with its levers, and records the maintainer's two answers.

## Tasks

**Commit boundary.** 50-01-01 commits `Add a suite profile report for the speed work (WP-50 50-01)` on `wp50-s01`. 50-01-02..04 commit nothing (the report text is committed by 50-04).

<task type="auto" id="50-01-01">
  <name>Write the suite profile report</name>
  <files>scripts/suite_profile.py, test/test_suite_profile.py, test/suite_timing.py</files>
  <action><![CDATA[Create test/test_suite_profile.py with the stubs and run it (`python3 -m pytest test/test_suite_profile.py -q -n0 > <scratch>/50-01-01-failure.txt; true`); create scripts/suite_profile.py per TR-50-01.1 and D-50-01.b, parsing the cert log's `[ TIME] <script> timer=<t>s wall=<w>s` lines and the truth scripts' `S<MM> start <date> <time>` / `S<MM> end <date> <time>` lines (seconds = end - start; a script's fixed cost = its timer seconds minus its blocks' sum). Apply TR-50-01.2 only if suite_timing.py's JSON lacks a session start. Register the new test file in test/function_test_map.py if that map covers scripts/ (grep it for `scripts/`). Run `python3 -m pytest test/test_suite_profile.py test/test_function_test_map.py -q -n0`; commit.]]></action>
  <verify><![CDATA[The failure file shows the stubs failing; pytest then 0 failed; `python3 scripts/suite_profile.py report` with no files exits 2 with a usage line.]]></verify>
  <done>A stdlib report turns a pytest timing file and the cert logs into the bottleneck table, under unit test.</done>
</task>

<task type="auto" id="50-01-02">
  <name>Run the timed batch-end suites</name>
  <files>none</files>
  <action><![CDATA[Orchestrator, at batch 50.1's step k.4, in the main checkout after 50-01-01 landed: `df -h /` (record free space); `DASH_SUITE_TIMING=<scratch>/timing-make-test.json make test > <scratch>/make-test.log 2>&1`; then `DASH_SUITE_TIMING=<scratch>/timing-test-all.json make test-all > <scratch>/make-test-all.log 2>&1` (run_all_tests.sh prints its log folder; copy its `pytest.log`, `cert.log` and the cert working folder's `s1`..`s3/run_all_cscripts.log` into <scratch>/). Never start the second before the first returns. If either is red, fix per k.5 and rerun only the failed tests; the timing stands unless a fix changes a slow file, in which case rerun that suite once with `FULL_SUITE_RERUN=1` and say so.]]></action>
  <verify><![CDATA[Both timing JSON files exist and parse (`python3 -c "import json;json.load(open('<scratch>/timing-make-test.json'))"`); make-test.log ends with a pytest summary line; make-test-all.log ends with run_all_tests.sh's `whole suite: <s> s wall` line.]]></verify>
  <done>`make test` and `make test-all` ran once each at batch end with per-test timing, and their logs are kept.</done>
</task>

<task type="auto" id="50-01-03">
  <name>Write the bottleneck profile</name>
  <files>none</files>
  <action><![CDATA[Run `python3 scripts/suite_profile.py report <scratch>/timing-make-test.json <scratch>/timing-test-all.json --cert <scratch>/s1/run_all_cscripts.log <scratch>/s2/run_all_cscripts.log <scratch>/s3/run_all_cscripts.log > <scratch>/wp50-profile.txt` and copy it to .ultraplan/handoff/wp50-profile.txt (uncommitted). Add a ranked list at its end, under `Levers (50-02, 50-03)`: each bottleneck with its seconds and the coverage-keeping lever that addresses it -- the list 50-02 and 50-03 work from, recorded and not put to approval -- drawing only on levers not yet taken ([C] §7.3; TEST-PERFORMANCE.md §2 A4/E/F; TEST-PRUNING-ANALYSIS.md S2, S5, C3, the concurrency option) and on anything new the profile shows (a WP-33..49 file over 60 test-seconds; a truth script whose fixed cost exceeds its blocks; a single test over 60 s). Then add D-50-01.d's projection line, and, if the projection is above 300 s, the tier candidates: the test files (or classes) with the most test-seconds in `make test` that would still run in `make test-all`'s batch tier or the release tier if moved, each with the seconds it frees, until the projection reaches 300 s or the list ends. Served/saved parameter merges are not candidates (D-50-03.e: a served parameter runs the served app's code, and WP-50 never deletes a test to save time).]]></action>
  <verify><![CDATA[.ultraplan/handoff/wp50-profile.txt holds the line `make test: <s> s against 300 s`, the `projection:` line with the basis of each estimate, at least five ranked bottlenecks with seconds, and, when the projection is above 300 s, the tier candidates with their seconds.]]></verify>
  <done>The suite's bottlenecks after WP-49 are written down with measured seconds and the lever for each.</done>
</task>

<task type="checkpoint" id="50-01-04">
  <name>Ask the two scope questions</name>
  <files>none</files>
  <action><![CDATA[Show wp50-profile.txt's totals, the ranked list with its levers, the projection line and the tier candidates; the levers are listed, not put to approval (they keep every test). Ask the maintainer only these two questions, in these words, with the numbers filled in: (1) "make test is projected at <s> s. To reach five minutes, these files (<file: seconds each>) would run only at batch end (make test-all) instead of in make test; no test is deleted. Move them, or keep make test as it is and record the bottleneck?" -- asked only when the projection is above 300 s; otherwise say the projection meets the target and skip it. (2) "Keep the Stata certification scripts out of make test, as today?" Merging a served parameter into its saved twin is not offered (D-50-03.e).]]></action>
  <verify><![CDATA[The maintainer answers (1) (when asked) and (2); the answers, with any moved files named one by one, are appended to wp50-profile.txt under `Answered <date>`.]]></verify>
  <done>The maintainer answered whether files leave make test for the batch-end run and whether certification stays out of make test, before any speed change.</done>
</task>

## Section completion criteria

- scripts/suite_profile.py and test/test_suite_profile.py committed; the two batch-end runs done once each; wp50-profile.txt written with the ranked lever list and the maintainer's two answers.

## Notes

- **The five-minute target is `make test`** (PRD §8), not `make test-all`; the gate's time is reported beside it because CLAUDE.md rule 11 names "the entire test suite" and the handoff analysis found pytest plus cert in five minutes unreachable on this machine; 50-01-04 asks the maintainer, with the projection in hand, whether named files move to the batch-end run (REVIEW-5 R5-9), so 50-03 applies an answer given up front.
- **No test is deleted to save time (WP-50).** A tier move keeps every test (it runs in the batch or release tier); no served parameter is merged into its saved twin.
- **Before each commit (CLAUDE.md rule 4; REVIEW-5 R5-39):** `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp50-s01 pull --ff-only . main` (BRIEF "Pull form": inside a worktree, with `$WT` the absolute worktree path; CLAUDE.md rule 4; expect `Already up to date.` at the batch base); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch. WP-50 closes no GAPS4 item, so BRIEF's corpus-ledger, known-differences and guard steps (1)-(3) have no lead id and are not taken. Then run the tests named in the task, `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back), grep the message for `claude|anthropic`, commit, and grep again.
- **Full-suite rules:** two launches only (the guard hook refuses a third without `FULL_SUITE_RERUN=1`); never two at once (the conftest lock refuses a concurrent full run); never launch a run to check on another -- read its log.
- **Merge rules touched:** none of R1-R14 beyond R14 (commit messages).
- **Commit-body line:** `Adds scripts/suite_profile.py (stdlib) and its tests; no test selection changes.`
