# Test suite performance: where the time goes and how to reach 5 minutes

## 0. WP-50 result (13nov2026)

Measured by WP-50's batch-end runs (50-01 before, 50-04 after; full profile in
.ultraplan/handoff/wp50-profile.txt).

| | Before (50-01) | After (50-04) |
|---|---|---|
| `make test` wall (Stata's Python, 8 workers) | 1,056.4 s (34,833 tests, 3 failed) | 306.1 s (24,385 passed); 284.6 s (24,397 passed) after the collection fix |
| `make test` test-seconds | 8,138.9 | 2,160.8 |
| `make test` longest item | 149.1 s (test_contour_gen malformed_object[std]) | 14.5 s (test_test_integrity, group test-integrity-suite 14.7 s) |
| `make test` collection (session start to first test) | 22.2 s | 21.0 s |
| `make test-all` pytest wall (python3.14, batch tier) | 627.5 s (46,075 tests; WP-49 gate, c3bb39e) | 583.2 s (46,322 passed) |
| `make test-all` pytest test-seconds | 4,737.5 | 4,366.1 |
| `make test-all` cert wall | 703 s (3 sessions; 694.9 / 697.9 / 582.2 s summed) | 238 s (8 sessions; 182.9-234.4 s summed each) |
| cert script runs per session | 35 / 42 / 34 | 9 / 11 / 8 / 8 / 12 / 8 / 8 / 17 |
| dash loads per session (echoed load lines) | 30 / 38 / 32 | 8 / 9 / 8 / 6 / 9 / 7 / 7 / 16 |
| WP truth scripts | 15 split in every session | all template-made ones whole; wp30/wp31 split (release tier) |
| `make test-all` whole | 1,343 s | 835 s |

Levers taken:
- **Speed branch, merged first (ruled 13nov2026):** `Cut the batch-end suite's cost: Bokeh defaults once per class, eight balanced cert sessions` (eacb68f2), `Add cert_shards.py rebalance and place the table again after WP-47's blocks` (96784d1e), `Parse a dash command in about half the time: walk only the options it set` (c1cd1c41), `Bring the speed branch up to WP-48 and WP-49 (WP-50)` (f11d6c86). Cert 703 s on 3 sessions -> 238 s on 8.
- **50-03:** `Run numpy's BLAS on one thread per test worker (WP-50 50-03)` (887c2c1d): Stata's Python runs numpy on OpenBLAS, and 8 workers x 12 threads oversubscribed the cores; the four contour files went from 175 s to 12.3 s wall, and the three time-bound failures pass. `Share one render per type and mode across sweep methods (WP-50 50-03)` (e1144cb0). `Move the ruled tests out of make test into the batch tier (WP-50 50-03)` (8a9d5ae8): 52 files, 1,958 test-seconds at the WP-49 gate, run at every batch end.
- **50-02:** `Load dash with run in the certification scripts (WP-50 50-02)` (845b818c); `Run short WP truth scripts in one session and balance parts on measured seconds (WP-50 50-02)` (2a3203a7): every template-made truth script runs whole (SPLIT_MIN 228 s), about 36 s summed saved.

Levers not taken: splits (no item over 60 s once BLAS ran on one thread); the render cache F (77 of 704 help_claims renders repeat, at most 11%, under its 25% rule); pruning (WP-50 deletes no test).

make test: 285 s wall (24,397 passed), at or under the five-minute target (CLAUDE.md rule 11, PRD §8), with the 52 files ruled at 50-01-04 moved to the batch tier and, applied at sign-off (377bb3be, 13nov2026), the batch tier's files left uncollected; before that fix it was 306 s.

Applied at sign-off (13nov2026, 377bb3be): the bottleneck's fix -- a run that leaves the batch tier out does not collect its files.  One timed make test: 306.1 s -> 284.6 s wall, 24,397 passed; collection 21.0 -> 16.1 s; test-seconds 2,160.8 -> 2,052.5; busiest worker 272.8 -> 257.3 s.

**Bottleneck record (D-50-04.b), as written before the fix was applied:**
- Bottleneck: the start of the run, not the tests.  The workers are busy
  268.5-272.8 s (imbalance 4.3 s; longest group 14.7 s), and 21.0 s pass
  from the session's start to its first test (collection: every worker
  collects all 46,322 items of the tree, then the tier hook deselects the
  21,937 batch-tier ones -- test_mode_parity.py and the 52 ruled files).
- Fix proposed (newly found): in a run that does not keep the batch tier,
  skip collecting the batch-tier files (a pytest_ignore_collect hook in
  test/conftest.py reading the file list test_test_tiers.py already pins as
  _RULED_BATCH_FILES, plus test_mode_parity.py), so make test never imports
  them.
- Estimated saving: about 10 s (basis: collection time scales with the items
  collected; the batch tier is 21,937 / 46,322 = 47% of them; 21.0 s x 0.47
  = 9.9 s), which would bring make test to about 296 s.
- Cost: no coverage moves (the files still run at every batch end); the risk
  is the file list drifting from the files' marks, guarded by a test that
  every ignored file carries the batch mark and every marked file is
  ignored.  A second lever, -n 10 workers (07oct2026: -n 8 -> 10 took 94 ->
  89 s, -5%), would save about 15 s but breaks the 8-worker budget
  (scripts/run_all_tests.sh, the memory rule): a maintainer ruling.

## History (07-10oct2026)

The analysis below is the one WP-30..WP-32 worked from, kept as it was.

Measured 07oct2026 on `wp30-p1`, from the following:
- **pytest:** the batch-2 full run with `DASH_SUITE_TIMING` (commit a0978fa): 24,815 tests, 6 workers, 867 s wall.
- **cscripts:** the timed certification run with timer 100 and `DASH_CERT_PROFILE` (commit ba34eef): 67 scripts, one Stata session, 914 s wall.
- **pruning analysis:** targeted pytest probes and cProfile runs (scratchpad `test-pruning-report.md`).

Target: the whole suite, pytest plus cscripts, in 5 minutes or less on at most 8 parallel workers, with no major coverage gap.

## 1. Where the time goes today

**Total today:** 5,038 pytest test-seconds plus 904 cscript seconds = **5,942 worker-seconds**.

At 8 workers the 5-minute budget is about 8 × 300 × 0.85 ≈ **2,040 worker-seconds**. The 0.85 factor is the measured scaling efficiency: -n 6/8/10/12 took 111/94/89/88 s.

The suite must therefore lose about two thirds of its work. Most of that is repeated work, not coverage.

### pytest (5,038 s over 6 workers; the workers are balanced at about 840 s each)

| Where | Test-s | Why |
|---|---|---|
| test_mode_parity.py | 1,245 (25%) | Each of 4,023 tests re-renders its dashboard in both modes. Its `xdist_group` marks never take effect (bug below). |
| The served half of every render pair | about 85% of each pair | For each spec, `ServerAppBuilder` regenerates a 26,000-line app, re-running `inspect.getsource` on 411 helpers (0.166 s). The test then compiles that app (0.14 s). The saved render takes 0.045 s. |
| help_claims_1-8 | 790 | Each claim renders full pages, mostly 40-plot-type sweeps in both modes. |
| server*, served_* and facets files | about 450 | The same served-app cost. |
| Chrome tests | 89 + 85 + 52 + others | csp_browser, responsive_layout, by_scales_chrome (one 100-panel test takes 43 s), stale_cue_browser. |
| Subprocess sweeps | 135 | `TestNoLayerNeedsScipyOrStatsmodels`: 4 tests × 34 s, each repeating the same subprocess sweep. |
| suite_lock, dataset_size_warning | about 45 | Nested pytest runs and large files. |

**Bug found:** in `test/conftest.py`, `pytest_collection_modifyitems` runs after xdist's own hook, so the parity groups are ignored. Every one of the 11 comparisons per parity entry re-renders.

### cscripts (904 s serial; timer 100 per script, wall clock as a cross-check)

| Script | s | Top programs (self time, profiler) |
|---|---|---|
| test_qualifier_in_stata | 126 | `_qs_by_case` 42, `_dash_do_render` 41 |
| test_wp29_truth | 124 | `_dash_do_render` 79 |
| test_twoway_option_parity | 102 | twoway itself (Graph, style and class programs) about 60, render 19 |
| test_help_claims_4 | 62 | `_dash_serve` 61.5: HC4-19 waits out a real `dash serve, timeout(1)` |
| test_parser | 52 | twoway Graph 7, render 7 |
| test_help_claims_6 | 45 | `setscheme` 8 and other twoway scheme programs |
| test_help_examples | 44 | `_dash_do_render` 43 |
| The other 60 scripts | 349 | Mostly `_dash_do_render` |

Profile totals across all scripts (775 s attributed):
- **dash programs:** 505 s.
  - `_dash_do_render`: 340 s over 1,079 builds, about 0.315 s each.
  - `_dash_serve`: 66 s.
- **Stata's own graph and class system:** 204 s (`Graph`, `setstyle`, `style`, `editstyle`, `remake_as_copy`, `new`, `set` and so on). That is twoway being drawn fresh as the truth for comparison.
- **Script helper programs:** 66 s.

**Product bottleneck found:** `_dash_do_render` runs `runpy.run_path("dash_render.py")` for every build. That recompiles the 38,150-line module each time, 0.224 s per compile (measured). Of the 340 s of render time, about 240 s is recompiling the same file. Every user's `dash` build pays the same 0.22 s.

## 2. Plan to reach 5 minutes

Every step below keeps coverage, apart from the pruning in E, which only removes duplicates. Savings are worker-seconds. They come from the measurements above, or are marked "est." where they are estimates.

### A. Fix repeated work in pytest (no coverage change)

| # | Change | Saves |
|---|---|---|
| A1 | Make the conftest grouping hook run first (`@pytest.hookimpl(tryfirst=True)`), so each parity entry renders once per worker. This is a bug, so it gets a regression test. | about 440 (measured: 446 → 138 s for the class) |
| A2 | `ServerAppBuilder` caches each helper's source; a product change that also speeds up `dash build, server`. | about 500 (measured: build 0.166 → 0.057 s) |
| A3 | Test helper: compile each generated app once per template and reuse the code object. Done through an explicit loader in conftest, not an import patch. | about 850 (measured with A2: −54% on parity, −27% on a 12-file mix) |
| A4 | Cache each move/saved render in TestAFilterMoveAgrees; per-plot-type classes share one render; classes with shared fixtures stay on one worker. | about 310 (est.) |

Subtotal: 5,038 → about **2,940**.

### B. Fix repeated work in the cscripts (no coverage change)

| # | Change | Saves |
|---|---|---|
| B1 | **Product:** `_dash_do_render` compiles `dash_render.py` once per Stata session and reuses the module from `sys.modules`, which survives `clear all`. It recompiles only when the file changes. This also makes every user's `dash` build about 0.22 s faster. | about 240 |
| B2 | twoway's own truth (the Graph and scheme programs in twoway_option_parity, parser and help_claims_6) is read from committed fixtures, re-measured only by the release run and by the extractor scripts. | about 150 |
| B3 | HC4-19 tests `dash serve, timeout()` with a 1-second internal deadline instead of waiting about 60 s; the test keeps its meaning. | about 60 |

Subtotal: 904 → about **450**.

### C. Run the cscripts in parallel

Split `run_all_cscripts.do` into 2 to 4 Stata sessions, each with its own STATATMP. The scripts that serve on fixed ports 5006/5097-5099 go in one session. 450 s of work then finishes in about 115-225 s of wall time, while those sessions share the 8 workers with pytest.

### D. Release-only tier (still run, at release, closeout and `make gate`, not in the 5-minute run)

Move these to a `release` marker or cert tier, about 340 pytest-seconds plus about 60 cscript-seconds:
- the Chrome browser tests;
- the 100-panel stress test;
- the subprocess sweeps without scipy or statsmodels;
- the nested-pytest suite_lock tests;
- the large-file warning tests;
- the multi-Python floor legs.

Coverage is unchanged; these tests run every release, not every batch.

### E. Pruning (duplicated coverage only; about 230 test-s after A, about 610 before)

- **Cut the served half of these 40-type sweeps to 6 representative types;** the saved half keeps all 40, and the served app runs the same drawing code (copy lists):
  - help_claims_7 TestAlphaOptions, TestMsangle and TestHover;
  - marker_label_parity::test_the_line_options_leave_every_marker_alone;
  - server_facets::TestEveryTypeFacetsTheSameWayInBothModes.
- **Your decision (pinned by BUGS.md regression entries):** TestJitter, TestWhereColorvarIsDrawn, TestRegionColours and TestColorColoursTheWholeLayer. The same reduction applies, and each bug is still pinned by its saved-mode half. Keep TestTheSecondAxisFitsTheLayer whole: its pin names all 40 types.
- **Not pruned:** the 259-entry parity corpus, the 38-type defect classes in server_layer_defects, label_sinks (XSS), and the served token and lifecycle tests (security).

## 3. Projection for the default run (≤ 8 workers)

| | Worker-s now | After A-E |
|---|---|---|
| pytest | 5,038 | about 2,370 (A, D, E) |
| cscripts | 904 | about 390 (B, D) |
| **Total** | **5,942** | **about 2,760** |

At 8 workers and 0.85 efficiency, 2,760 worker-seconds is about **6.8 minutes**. Steps A-E alone do not reach 5 minutes.

The remaining gap of about 720 worker-seconds needs one more step, again without a coverage gap:

- **F. One saved and one served render per distinct spec per worker.** A spec-hash render cache in conftest, used by the renders in the help_claims and served files. Those files re-render identical specs across classes: for example, the same 40-type sweep spec appears in help_claims_7 and in two other files.
- **Estimate:** 25-35% of the remaining render cost, about 600-800 worker-seconds.
- **Status:** an estimate. I measure it after A and B, before relying on it.

With F, the projection is about **5.0-5.3 minutes**. Two levers close the remainder without dropping coverage, though either may reduce what each test covers:
- **The pinned prunes in E**, about 380 test-seconds more.
- **Running each cert session alongside pytest** (pytest on 6 workers plus 2 Stata sessions, 8 in all), instead of one after the other.

**Honest bottom line:** on this machine, 5 minutes on at most 8 workers is reachable only with A, B, C and D plus F, and with E including your call on the pinned prunes. Each step is measured as it lands. If F comes in below estimate, the remaining choice is between more served-mode pruning and moving more tests to the release tier. I will bring that choice to you, not make it silently.

## 4. Suggested order (each step: related tests, then one timing run at its end)

1. A1, the conftest grouping bug, with a regression test.
2. B1, the renderer compiled once per session. This is a product speedup, so it gets a unit test and a cscript case.
3. A2 and A3, the served-app build cache and compile-once loader.
4. B3, then B2, the HC4-19 deadline and the twoway fixtures.
5. C, the parallel cert sessions, and D, the release tier: a `release` marker, plus `make test` and `make gate` wiring.
6. A4, the move-render and fixture-sharing caches, then F, the spec-hash render cache, measured.
7. E, the safe prunes, then the pinned prunes if you approve.
8. One full timing run of both suites at ≤ 8 workers, reported against the 5-minute target.
