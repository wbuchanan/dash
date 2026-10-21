# Section 50-03: pytest: the untaken levers

> Part of: WP-50 (Test-suite speed, Q29; CLAUDE.md rule 11) · Items: none · Risk: yellow · Batch: 50.2 · Depends on: 50-01 · Blocks: 50-04 · Tasks: 5, up to 4 commits · Case-id prefix: Q5003

## Overview

**What is wrong today.** `make test` -- the PRD §8 target, "at most 5 minutes" -- is pytest under Stata's Python with the release and batch tiers left out. Its last whole-suite measurements were 459 s (WP-30, 09oct2026, ROADMAP.md:5089) and 898 s for WP-31's suite (ROADMAP.md:5123); WP-32's gate pytest (with the batch tier) took 1,562 s; WP-33..WP-49 add the tests of 221 items. The structural levers of the 07-10oct2026 analyses are in place ([C] §7.2: tryfirst xdist grouping, tiers, `render_models`, the compile-once app loader, the ServerAppBuilder source cache, the per-process temp folder). What is left ([C] §7.3) is: "Split each long served probe into per-case tests so loadgroup can spread them" -- with `--dist loadgroup` "a long single test sets the wall floor whatever the worker count" (test_size_units.py `TestStataRatios` label offsets and sizes 212 s and 192 s, each one test looping over every probe through `_every_probe`; test_bare_intensity.py 93 s; test_by_text.py's three served probes 66-67 s; test_added_text.py 62 s; test_intensity_blend.py 59 s; test_by_axes_keys.py 40 s); F, "a spec-hash render cache per worker for identical specs across help_claims and served files (estimate 600-800 worker-s at the time)"; S5, one render per (type, mode) shared across the methods of per-type sweep classes; and tiering, which needs the maintainer's answer and gets it up front at 50-01-04 with the projection in hand (REVIEW-5 R5-9). Served-half de-parametrisation (TEST-PERFORMANCE.md E, TEST-PRUNING-ANALYSIS.md P1-P5) is not taken: a served parameter runs the served app's code path, and WP-50 never deletes a test to save time (REVIEW-5 R5-36).

**After this section.** The levers 50-01-03 lists in wp50-profile.txt are applied to the files 50-01's profile named: no test longer than the measured target floor (D-50-03.a) runs as one item; identical renders are built once per worker where the cache is measured to pay; per-type sweeps share renders across their methods; every assertion is kept (a guard counts the assertions' cases before and after). Tier moves are applied only as the maintainer answered at 50-01-04, file or class by file or class, and every moved test still runs (in the batch tier of `make test-all` unless the ruling names the release tier); no test is deleted and no served parameter is merged into its saved twin.

**Why these, why here.** They are the only pytest levers left that keep coverage; they change test files and conftest.py only, so they run beside 50-02 (cert files) in batch 50.2.

**Test order and commit rule.** 50-03-01 freezes the case counts and writes their guard (no commit); 50-03-02..04 each apply one lever group and commit it (`(WP-50 50-03)`), running only the files they change, 50-03-03 writing its cache tests red first; 50-03-05 applies the tier moves the maintainer answered for at 50-01-04, if any, and commits. The guard goes in the first commit made. No timing run of the whole suite (memory rule); a lever's effect is read from 50-01's per-test seconds before, and from 50-04's batch-end profile after.

### Section decisions

- **D-50-03.a — The floor.** With W = 8 workers (pyproject.toml:9) the wall cannot fall below the larger of (test-seconds / W) and the longest single item or xdist group. The 300 s target at 0.85 efficiency allows about 2,040 test-seconds in all; one item over 60 s already takes a fifth of a worker's budget. So: split every item or group over 150 s first, then every one over 60 s, in the order 50-01's profile lists them.
- **D-50-03.b — Splitting keeps the assertions.** A test that loops over probes (`_every_probe`) becomes `@pytest.mark.parametrize("pid", <the same id list>)` calling the same per-probe function; the old "listed together on failure" message is replaced by pytest's per-parameter report. A shared expensive fixture is made `scope="module"` (or class) and the parameters grouped with `xdist_group` only when the fixture costs more than the parallelism saves (measure from the profile's setup seconds).
- **D-50-03.c — The render cache (F).** `conftest.cached_render(spec, mode)`: keyed by `hashlib.sha256(json.dumps(spec, sort_keys=True))` and mode, per process; it returns a *new* renderer state each call by re-loading the cached Bokeh document from its JSON (`Document.from_json`, both bokeh 3.8 and 3.9) for tests that only read models; a test that mutates the document (grep for `.data =`, `.change.emit`, `apply_json_patch` in it) does not use the cache. Taken only if one targeted measurement -- `python3 -m pytest <the three files the profile names as the largest render repeaters> -q -n0 --durations=0` before and after, a targeted run, not a full suite -- shows at least 25% less time on those files; else not taken, and recorded.
- **D-50-03.d — Shared sweeps (S5).** In a class whose methods each render the same (type, mode) set (server_layer_defects `TestEveryFigureCarriesTheSameHover`, `TestTheLegendSaysTheSameThing`, `TestALayerThatDrewNothing...`; server_facets `TestEveryTypeFacetsTheSameWayInBothModes`; saved_filter_layers `TestEveryLayerFollowsAMove`; and any WP-33..49 class 50-01's profile shows), one class-scoped cache of the render per (type, mode) serves every method; the class gets `xdist_group` so it renders once per worker.
- **D-50-03.e — Tier moves only as ruled; no merges.** A file or class leaves `make test` only if 50-01-04's ruling names it, and then moves to the batch tier (`pytestmark = pytest.mark.batch`, run by `make test-all` at every batch end) unless the ruling names the release tier; its tests are unchanged and still run. No served parameter is merged into its saved twin and no test is deleted: a served parameter exercises the served app's code path, which its saved twin does not, so it is not a duplicate (REVIEW-5 R5-36; WP-50 never deletes a test to save time). Pinned BUGS.md classes (TestJitter, TestWhereColorvarIsDrawn, TestRegionColours, TestColorColoursTheWholeLayer, TestTheSecondAxisFitsTheLayer) are moved only if the ruling names them.

## Risk: [yellow] -- test-only changes that could hide a lost assertion

**Why.** Splitting and caching move work between tests; a mistake could drop a probe or let one test see another's mutation. **Risk factors.** 1. A probe list shortened by accident. 2. A cached document mutated by a test. 3. xdist groups that make one worker the floor again. 4. Bokeh 3.8 vs 3.9 `Document.from_json` differences. **Mitigation.** 1. TR-50-03.1's case counter, red first. 2. D-50-03.c's mutation rule plus a test that two consecutive `cached_render` calls return documents with different ids. 3. Read 50-01's per-group seconds; split groups over 60 s. 4. Run the changed files under /opt/anaconda3/bin/python3 (bokeh 3.8, pytest 8.4) as well as python3.

## Dependencies

- **Depends on:** 50-01 (the profile and the levers 50-01-03 lists; none of them is put to approval, and this section takes the pytest ones).
- **Blocks:** 50-04.
- **Parallel batch 50.2** with 50-02 (cert files only). 50-03 owns test/conftest.py and the slow test files the profile names; it edits no cscript, no runner and no product code.

## Evidence

- pyproject.toml:9 `addopts = "-n 8 --dist loadgroup"`; test/conftest.py: tiers :220-300 (`_covers_whole_suite`, `pytest_collection_modifyitems` tryfirst, parity grouping `xdist_group("parity:<name>")`), session lock :127-213, per-process temp folder :34-80, `render_models` :562-573, `load_app` :576-588, the compile-once loader :363-470; test/suite_timing.py.
- test/test_size_units.py `TestStataRatios` :1034-1060: `test_sizes(mode)` and `test_label_offsets(mode)` each call `_every_probe(_SIZE_IDS|_OFFSET_IDS, ..., mode, tmp_path)`.
- The other named files: test/test_bare_intensity.py, test/test_by_text.py, test/test_added_text.py, test/test_intensity_blend.py, test/test_by_axes_keys.py (re-read each for the looping test; 50-01's profile is authoritative).
- Guards that must stay green: test/test_xdist_groups.py, test/test_test_tiers.py, test/test_suite_lock.py, test/test_test_integrity.py (its rules on test classes and collection), test/test_function_test_map.py (every function keeps a named test: a split test keeps its name with a parameter).
- .ultraplan/handoff/TEST-PERFORMANCE.md §2 (A4, E, F) and TEST-PRUNING-ANALYSIS.md §2-§4 (S2, S5, P1-P5, tiering).

## User stories

- US-50-03.1 As the maintainer, I want `make test` to finish within five minutes so that I run the suite as often as the rules ask.
- US-50-03.2 As a coding agent, I want slow tests split per case so that a failure names the probe and the workers stay busy.

## Business requirements

- BR-50-03.1 Every assertion case that ran before runs after (counted).
- BR-50-03.2 No single pytest item or xdist group in `make test` runs longer than the floor D-50-03.a sets, by 50-04's measurement.
- BR-50-03.3 No test is deleted or merged away; a tier move applies only to a file or class 50-01-04's ruling names, and its tests still run in the tier it moves to.

## Technical requirements

- TR-50-03.1 New test/test_suite_cases_kept.py: for each file this section changes, the number of probe/parameter cases its tests run (counted from the id lists and parametrize arguments by importing the module and reading its id lists, not by running it) equals the number frozen at the base in the module constant `FROZEN = {"<test file>": {"<test name>": <count>, ...}, ...}  # frozen at <base sha> (WP-50 50-03-01)`, written by 50-03-01. No fixture file: a JSON fixture would need a committed generator script, a `_meta` stamp and a GENERATORS entry in test/test_fixtures_are_committed.py (R7), which a hand-frozen count has not.
- TR-50-03.2 Splits per D-50-03.b in each file the profile lists over the floor; function_test_map.py names that point at a renamed test are updated (the test name stays where possible: keep `test_sizes` as the parametrised name).
- TR-50-03.3 `cached_render` in conftest.py per D-50-03.c, with test/test_conftest_cache.py (two calls give distinct documents with equal JSON; a spec differing in one option misses the cache), written red in 50-03-03 and committed only with `cached_render`; used only by the read-only tests of the files the measurement names. If F is not taken, test_conftest_cache.py is deleted uncommitted with the code (REVIEW-5 R5-35).
- TR-50-03.4 Shared sweep caches per D-50-03.d as class-scoped fixtures in those files.
- TR-50-03.5 Tier moves per D-50-03.e; test_test_tiers.py's tier lists (if they list files) move with `# old -> new: WP-50 50-03 <file> to the <batch|release> tier (ruled <date> at 50-01-04)`.

## Boundaries

- No product code; no cscript or runner (50-02); no change to `addopts`, the tiers' rules or the session lock unless 50-01-04 ruled it.
- No test deleted, no served parameter merged into its saved twin (D-50-03.e).
- No full-suite run inside the section; the targeted measurement of D-50-03.c is the only timing run, on three files.

## Stata truth

None.

## TDD test stubs

- Test: the frozen case counts equal the live counts for every changed file -- `test/test_suite_cases_kept.py::TestCasesKept::test_counts[file]` (green at the base by construction: `FROZEN` is read from the base; a lever that drops a case turns it red).
- Test: `cached_render` returns distinct documents with equal JSON -- `test/test_conftest_cache.py::TestCachedRender::test_fresh_document_each_call` (red: no function), `::test_a_different_spec_misses` (red).
- Test: each split test still reaches every probe id -- `test/test_size_units.py::TestStataRatios::test_sizes[mode-pid]` (the parametrised form; its collection count equals the id list length times modes).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| cases kept | test_suite_cases_kept.py | `FROZEN` (module constant, frozen at the base) | n/a |
| render cache | test_conftest_cache.py; targeted durations run | -- | yes |
| changed files | their own tests under both Pythons | -- | yes |
| speed | 50-04's batch-end profile | 50-01's profile | n/a |

- AC-50-03.1 Every changed file passes under bokeh 3.8 and 3.9; the case counter is green.
- AC-50-03.2 Each lever not taken is recorded with its reason in its commit body or in wp50-profile.txt.

## Tasks

**Commit boundary.** One commit per lever group taken, each `<what> (WP-50 50-03)`: splits (50-03-02), render cache (50-03-03, with test_conftest_cache.py), shared sweeps (50-03-04), ruled tier moves (50-03-05). 50-03-01 commits nothing of its own: its guard goes in the first of those commits that is made, never alone (no test-only commit). Branch `wp50-s03`.

<task type="auto" id="50-03-01">
  <name>Freeze case counts and write the guard</name>
  <files>test/test_suite_cases_kept.py</files>
  <action><![CDATA[From the lever list 50-01-03 wrote in .ultraplan/handoff/wp50-profile.txt and the maintainer's answers at 50-01-04, name the files this section changes (the splits, the cache users, the sweep classes, any tier move answered for). Create test/test_suite_cases_kept.py with the module constant `FROZEN = {...}  # frozen at <base sha> (WP-50 50-03-01)` (per file: each test's case count = len(id list) x len(modes) or the parametrize product, computed by importing the module at the base) and `TestCasesKept::test_counts[file]` (TR-50-03.1). No fixture file and no edit of test/test_fixtures_are_committed.py. Run `python3 -m pytest test/test_suite_cases_kept.py -q -n0`. Do not commit (the first lever commit carries it).]]></action>
  <verify><![CDATA[test_suite_cases_kept.py passes at the base (the counts equal the frozen ones) -- the guard is green before the change and must stay green after; `git status --short test/fixtures/` lists nothing this task wrote.]]></verify>
  <done>The case counts of every file to change are frozen in the guard's module constant, which the levers must keep green.</done>
</task>

<task type="auto" id="50-03-02">
  <name>Split the long single tests</name>
  <files>test/test_size_units.py, test/test_by_text.py, test/test_bare_intensity.py</files>
  <action><![CDATA[Apply TR-50-03.2 to every file 50-01-03's lever list names over the floor (the three named here and any others; list them in the commit body). Keep each per-probe function's body; replace each loop with `@pytest.mark.parametrize("pid", <ids>)`. Run each changed file and test_suite_cases_kept.py, test_function_test_map.py, test_test_integrity.py, test_xdist_groups.py under python3 and /opt/anaconda3/bin/python3 with `-q -n0`. Commit `Split the long single tests per probe so the workers share them (WP-50 50-03)` with 50-03-01's guard (if no test is over the floor, nothing is split, nothing is committed here, and the guard goes in the next commit made) (Notes: before each commit).]]></action>
  <verify><![CDATA[pytest 0 failed under both Pythons for the changed files and the guards; `python3 -m pytest test/test_size_units.py --collect-only -q | grep -c TestStataRatios` prints the id lists' total times the modes.]]></verify>
  <done>Every test the profile showed above the floor runs as per-probe items with every probe kept.</done>
</task>

<task type="auto" id="50-03-03">
  <name>Add the measured render cache</name>
  <files>test/conftest.py, test/test_conftest_cache.py</files>
  <action><![CDATA[First create test/test_conftest_cache.py (TestCachedRender stubs) and run it red: `python3 -m pytest test/test_conftest_cache.py -q -n0 > <scratch>/50-03-03-failure.txt; true`. Then implement `cached_render` (TR-50-03.3, D-50-03.c). Measure the three files the profile names as the largest render repeaters with `python3 -m pytest <files> -q -n0 --durations=0` before switching them to it and after (a targeted run of three files, not the suite); record both totals in <scratch>/50-03-03-measure.txt. If the saving is under 25%, revert the users and delete `cached_render` and test/test_conftest_cache.py uncommitted (keep no unused code; nothing of F is committed) and record "F not taken: <before> s -> <after> s" in wp50-profile.txt; else run the users and test_conftest_cache.py under both Pythons and commit `Build identical read-only renders once per worker (WP-50 50-03)` with test_conftest_cache.py, `cached_render` and its users, plus 50-03-01's guard if no commit carried it yet (Notes: before each commit).]]></action>
  <verify><![CDATA[<scratch>/50-03-03-failure.txt shows the cache tests failing; <scratch>/50-03-03-measure.txt holds both totals; either a commit ending `(WP-50 50-03)` holds test_conftest_cache.py with pytest 0 failed, or wp50-profile.txt records the lever as not taken and `git status --short test/test_conftest_cache.py` prints nothing.]]></verify>
  <done>The render cache is in use where it saves at least a quarter of the time, or its measured failure to pay is recorded.</done>
</task>

<task type="auto" id="50-03-04">
  <name>Share renders across sweep methods</name>
  <files>test/test_server_layer_defects.py, test/test_server_facets.py, test/test_saved_filter_layers.py</files>
  <action><![CDATA[Apply TR-50-03.4 (D-50-03.d) to the named classes and any the profile adds; keep every method's assertions. Run each changed file, test_suite_cases_kept.py and test_xdist_groups.py under both Pythons (`-q -n0`; also once with `-n 4` on the changed files to see the groups spread). Commit `Share one render per type and mode across sweep methods (WP-50 50-03)`, with 50-03-01's guard if no commit carried it yet (Notes: before each commit).]]></action>
  <verify><![CDATA[pytest 0 failed for the changed files and guards under both Pythons.]]></verify>
  <done>Per-type sweep classes render each type and mode once per worker with every assertion kept.</done>
</task>

<task type="auto" id="50-03-05">
  <name>Apply the ruled tier moves</name>
  <files>test/test_test_tiers.py, test/conftest.py</files>
  <action><![CDATA[Apply TR-50-03.5 for each file or class the maintainer's answer at 50-01-04 names (none, if it named none: then this task changes nothing and commits nothing): add `pytestmark = pytest.mark.batch` to the file (or the marker to the class) -- `pytest.mark.release` only where the ruling says release -- and move test_test_tiers.py's lists with their comments. No test is deleted and no parameter merged. Run each moved file with `DASH_TEST_TIER=batch` (or `release`), test_test_tiers.py and test_suite_cases_kept.py (its frozen counts for a moved file are unchanged -- the tests still exist), under both Pythons. Commit `Move the ruled tests out of make test into the batch tier (WP-50 50-03)` if anything changed, with 50-03-01's guard if no commit carried it yet (Notes: before each commit).]]></action>
  <verify><![CDATA[pytest 0 failed; for each moved file `python3 -m pytest <file> -m batch --collect-only -q` (or `-m release`) collects the same count as before the move; `git diff <base> --stat -- test/` deletes no test function (`git diff <base> -- test/ | grep -c "^-    def test_"` equals the number of tests renamed by a split, each with its parametrised replacement).]]></verify>
  <done>Only the tier moves the maintainer ruled at 50-01-04 are applied, and every test still exists and runs in its tier.</done>
</task>

## Section completion criteria

- Guards green; every changed file green under both Pythons; each lever taken is committed, each not taken recorded with its measured reason.
- No test deleted; the frozen case counts hold.

## Notes

- **Memory rules:** no duplicate tests (one test per behaviour; a served parameter is not a duplicate of its saved twin), never delete a test to save time, verify only with directly-covering tests, no per-item timing runs (D-50-03.c's three-file run is the one targeted measurement), no full suite inside a batch.
- **Stata's Python:** `make test` runs pytest 8.4 and bokeh 3.8 (memory); keep to their APIs (`Document.from_json` exists in both; parametrize ids as strings).
- **Merge rules touched:** R7 none (the frozen counts are a module constant, no fixture); R10, R14.
- **Before each commit (CLAUDE.md rule 4; REVIEW-5 R5-39):** `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp50-s03 pull --ff-only . main` (BRIEF "Pull form": inside a worktree, with `$WT` the absolute worktree path; CLAUDE.md rule 4; expect `Already up to date.` at the batch base); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch. WP-50 closes no GAPS4 item, so BRIEF's corpus-ledger, known-differences and guard steps (1)-(3) have no lead id and are not taken. Then run the tests named in the task, `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back), grep the message for `claude|anthropic`, commit, and grep again.
- **Commit-body lines:** each lever's files, and the per-file seconds before (from 50-01's profile) beside the change.
