# dash test suites: runtime, structural speedups, pruning, tiering (07oct2026, branch wp30-p1)

Read-only analysis. No repo file was edited. Measurements were taken with targeted pytest runs only: single files or explicit file lists, at -n 4/6/8/10/12. Prototype plugins live in `scratchpad/wp30x/prune/` (`grpfix.py`, `memo.py`, `ccache.py`, `costprobe.py`, `hashprobe.py`), and the raw outputs sit beside them. No Stata was run. Cert figures come from the 06oct baseline log (`/var/folders/.../dash_cert.CKMopw/run_all_cscripts.log`, 943 s, 67 scripts) and the mtimes of its `tmp/` files.

Units. A "u" is one test-second as measured by the b2 full run at `-n 6` (5,038 u for 24,815 tests, 867 s wall). Capacity was measured on a 6-file mix (3,958 tests, 622 u at -n 6):

| workers | wall | user CPU | u per wall-second |
|---|---|---|---|
| 6 | 111.3 s | 650 s | 5.6 |
| 8 | 93.6 s | 723 s | 6.65 |
| 10 | 89.3 s | 835 s | 7.0 |
| 12 | 88.1 s | 935 s | 7.07 |

The machine has 8 P-cores and 4 E-cores, and throughput levels off at about 8 workers. Going from -n 6 to -n 12 buys only about 20% wall time. **5 minutes of wall time is about 2,120 u at -n 12.** This is the budget that both suites have to fit into.

---

## 1. Where the time goes

### 1.1 pytest (b2 run: 5,038 u, 867 s wall at -n 6; the queue script forced -n 6, while pyproject's default is -n auto)

| file | u | tests | why |
|---|---|---|---|
| test_mode_parity.py | 1,245 | 4,023 | Each corpus entry is rendered saved and served. **Its render-once design is broken (bug, §2 S1)**, so each of the 11 comparisons re-renders. TestAFilterMoveAgrees re-renders on every test by design (§2 S2). |
| test_help_claims_7.py | 267 | 913 | 40-type × {saved, served} sweeps; served is about 88% of the cost (TestJitter, TestWhereColorvarIsDrawn, TestTheSecondAxisFitsTheLayer, TestAlphaOptions, TestMsangle, TestHover). |
| test_help_claims_8.py | 224 | 310 | TestNoLayerNeedsScipyOrStatsmodels: 4 tests × 33.7 s. Its class fixtures run once per worker (xdist splits the class), so a 33 s subprocess runs 4 times instead of 2. TestAnUnsupportedOptionIsInertWhenServed: 72 served renders. |
| test_server.py | 145 | 468 | About 180 served app builds + compiles (it loads its own dash_render copy). |
| test_server_layer_defects.py | 142 | 395 | 313 served builds. Classes with 2–3 methods × 40 types each render both modes per method. |
| test_marker_label_parity.py | 93 | 146 | 195 served builds; two loop tests at about 11 s (30 served renders each). |
| test_saved_filter_layers.py | 90 | 382 | 618 saved renders and 297 node subprocesses (JS filter runs); two methods per case redo the same render and node run. |
| test_label_sinks.py | 90 | 960 | TestTextSinks: served about 0.95 s/test (security sinks). |
| test_csp_browser.py | 90 | 24 | Headless Chrome with real serve. |
| test_responsive_layout.py | 85 | 63 | Headless Chrome. |
| test_server_facets.py | 80 | 158 | 2 methods × 40 types, both modes each. |
| test_by_scales_chrome.py | 52 | 6 | test_hundred_panels_settle alone takes 43 s (Chrome, 100 panels). |
| other 198 files | about 2,435 | | Mostly served+saved render pairs. Subprocess-heavy files are inflated about 5× by load: test_runner_portability takes 41 u in the full run and 8 s alone. |

**Cost of one render pair** (warm, uncontended, cProfile and timers):

| step | time |
|---|---|
| saved `DashRenderer.render` | 0.045 s |
| served `ServerAppBuilder.build` | 0.166 s; 66% of it is `inspect.getsource` over 411 helper functions plus the whole module, every build |
| `compile` of the generated app | 0.14 s; the app is 26,259 lines / 1.4 MB |
| exec + make_document | about 0.05 s |

**The served side is about 85% of a pair.** The generated app is identical across specs except for its literal constant lines. The costprobe over 10 heavy files (1,365 u) found served build 360 u + compile 288 u = 47%, and saved render 12%.

Phases in the b2 run: call 4,767 s, setup 263 s (class- and module-scoped fixtures repeated per worker), teardown 8 s. Note that b2 had 74 failing tests (test_unsupported_report_is_true and others), so those files' timings are approximate.

### 1.2 Cert (06oct baseline: 943 s serial, 67 scripts; test_wp30_truth.cscript added since, about 20 s estimated)

The runner runs scripts serially in one Stata session. The estimates come from inner-log timestamps and tmp-file mtimes. They are ±10 s.

| rank | script(s) | est. s | driver |
|---|---|---|---|
| 1 | test_qualifier_in_stata (+ mata_library_guard, same window) | about 125 (138 together) | 115 renders: per case, immediate page + named route saved + served build/compile |
| 2 | test_wp29_truth | about 131 | 197 renders, 36 twoway, 104 python blocks |
| 3 | test_twoway_option_parity | about 110 | twoway oracle per type × option (inner logs 15:51:25–15:53:10) |
| 4 | test_help_claims_4 | about 70 | **HC4-19: a real `dash serve, timeout(1)` that blocks 61.6 s by design** (timeout is in minutes) |
| 5 | scripts 1–8 (tokenizer, parser, e2e_*, ado_loads, mata_autoload) | about 65 | parser 25 builds, 110 dash commands |
| 6 | scripts 9–20 (adversarial, e2e_serve, … examples_run, serve_options) | about 85 | adversarial 62 renders; examples_run 141 dash commands |
| 7 | test_help_examples | about 45 | 36 builds (every help example) |
| 8 | test_help_claims_6 | about 45 | twoway oracle: about 60 `.gph`/`.dta` pairs |
| 9 | test_json_escaping | about 28 | 63 renders, 91 python blocks |
| 10 | test_qualifier_literals | about 27 | 35 renders |
| 11 | test_gaps2_truth (+ci_band_options) | about 30 | 37 renders, 18 twoway |
| 12 | test_string_values | about 21 | 34 renders |
| 13 | test_program_coverage | about 15 | 37 renders |
| 14 | remaining 35 scripts | about 150 | 0–20 renders each, plus a 16,000-line `do` of dash_parse.mata/dash.ado per script (122 loads; 29 MB log) |

Cert/pytest overlap is small. The help_claims_N, twoway_option_parity and qualifier pairs are deliberately split: Stata's half in the cscript, the renderer half in pytest. Real overlap exists only where a cscript renders the served mode in-process: qualifier_in_stata `_qs_modes`, json_escaping JSE-16, and wp29 (23 served references). That costs about 20–30 s.

---

## 2. Structural speedups (no coverage lost)

| id | change | measured / estimated saving | risk |
|---|---|---|---|
| **S1** | **Bug fix:** in `test/conftest.py`, `pytest_collection_modifyitems` must be `@pytest.hookimpl(tryfirst=True)`. xdist's worker hook (remote.py:236) runs first and reads `xdist_group` before conftest adds it, so no parity item gets its `@parity:<name>` suffix. Every comparison re-renders the entry: 0.42 s each instead of 0.42 s once per 11. | Verified with `-p grpfix` (nodeids gain `@parity:`). TestTheTwoModesAgree: 446 → 138 u-equivalent (-n 4). The file drops about 25%, **about −440 u**. | Nil. Needs a regression test under rule 7, e.g. assert the hook is tryfirst, or that an xdist run's parity nodeids carry `@parity:`. |
| **S2** | TestAFilterMoveAgrees: cache `_served_after_move` and `_saved_with_qualifier` results (plain data) per entry name, so its 4 methods share 1 served move, 1 saved render and the `move-before` pair (the group already keeps them on one worker once S1 lands). | After S1+S3+S6 the class is 180 of 282 test-s at -n 8. About −60% of that, **about −150 u**. | Low. The assertions are unchanged. Firing mutates the doc, so cache the profiles, not the doc. |
| **S3** | Product: memoize `inspect.getsource` in `ServerAppBuilder` (dash_render.py 33879/33884/33969/34039/34059), keyed by object identity. Run gitnexus impact first. | build 0.166 → 0.057 s/app. Four served-heavy files (1,612 tests): 590 → 449 s CPU (−24%), all pass. **Suite about −500 u.** It also speeds `dash serve` and the cert's served builds (about −15–20 s). | Low. Ids of module-level functions are stable, and a monkeypatched function has a new id. |
| **S6** | Harness: compile each generated app once per template. Lift literal constant lines (147 per app) out, cache the code object by template hash, and exec it with the constants injected. The prototype (`prune/ccache.py`) patches `SourceLoader.source_to_code`. For the repo, make it an explicit `load_app(path)` helper in conftest, not an import-system patch. | With S3: served-heavy files 590 → 264 s CPU (−55%, wall 76 → 35 s); parity (after S1) 673 → 311 s CPU (−54%, wall 87 → 41 s); a 12-file mix (4,781 tests) 864 → 628 s (−27%). Every test passed. **Suite about −850 u on top of S3 (S3+S6 ≈ −1,350 u).** | Medium. Tests no longer compile the exact file text (equal by `literal_eval`). Keep one un-cached compile of a real app per run, as test_server::test_generated_file_compiles already does. Exclude the security tests that inspect the generated file. Line numbers are preserved. |
| **S4** | Put every class with a class-scoped fixture, and every module with a module-scoped fixture, in an `xdist_group` (same tryfirst hook). 73 such fixtures in 44 files. | help_claims_8 TestNoLayerNeedsScipyOrStatsmodels 135 → 67 u; test_test_integrity (5 × 6 s module fixture) about −20; test_function_test_map about −5; part of the 263 s setup phase. **About −100 u.** | Low. It creates a 67 s single-worker chunk, which is acceptable. |
| **S5** | Share one render per (type, mode) across the methods of per-type sweep classes: server_layer_defects TestEveryFigureCarriesTheSameHover (3 methods), TestTheLegendSaysTheSameThing, TestALayerThatDrewNothing…; server_facets TestEveryTypeFacetsTheSameWayInBothModes (2 methods); saved_filter_layers TestEveryLayerFollowsAMove (2 methods share render + node run). | Before S3/S6 about −130 u; after them **about −60 u**. | Low. The pinned assertions are unchanged. |
| **S7** | Worker count: run at -n 8–12 (pyproject already says auto; `full_suite_queue.sh` forces 6). | Wall −16% (n8) to −21% (n12) at the same work. | None. |
| **C1** | Cert: shard `run_all_cscripts.do` into 4 Stata sessions, each with its own `STATATMP=<dir>/` and `DASH_PYTHON_EXEC` set per session (guards against the stata19.rc python_exec loss seen with ~16 sessions). **Keep every script that launches `dash serve` on a fixed port in one shard:** 5006/5097/5098/5099 in bug_regressions, env_guards, help_claims_4, serve_browser, serve_launch, serve_options, e2e_serve, wp29. | 965 s → about 240 s (LPT, 4 shards); about 170 s with 6 shards (wp29_truth's 131 s is the floor). | Medium: ports, license seats and the rc file. Keep it to ≤4 shards. |
| **C2** | Cert: record twoway oracles (twoway_option_parity, help_claims_6 `.gph`, the twoway parts of wp29/gaps2/help_claims_1) as committed fixtures, the way `value_truth.json` already is. Re-measure them in the release tier and on a Stata version change. | **About −120–150 s CPU.** | Medium: a stale oracle between releases. |
| **C3** | Cert: load dash_parse.mata/dash.ado with `run` (no echo) instead of `do`. 122 loads echo 16,000 lines each, which is most of the 29 MB log. | Unmeasured; estimated −20–60 s. | Low, but a few scripts grep their own log. |

Totals for pytest after S1–S7: about 5,038 → 2,700 u (±20%; extrapolated from the three measured file groups).

---

## 3. Pruning list (ranked by seconds saved per unit of coverage lost; the post-S3/S6 saving is in brackets)

| # | target | action | saves u (post-structural) | coverage given up | still covered by |
|---|---|---|---|---|---|
| P1 | help_claims_7 TestAlphaOptions::test_malpha_is_the_markers_opacity (40 served), TestMsangle::test_the_types_msangle_turns (41 served), TestHover::test_the_types_whose_tooltip_shows_the_variable (40 served); **no BUGS.md pin** | Keep saved for all 40 types. Cut served to a 6-type family set (scatter, line, rarea, bar, lfitci, pcarrow). | 62 (28) | Served check of malpha, msangle and hover for 34 types | Saved half for every type. The served app runs the same `getsource`-copied GlyphMapper. test_mode_parity's corpus has every dispatched type (TestTheCorpusIsComplete) comparing glyph style/tools. TestHoverReachesEveryLayerOrIsReported runs all types × both modes. |
| P2 | help_claims_7 TestJitter, TestWhereColorvarIsDrawn (2 methods), TestTheSecondAxisFitsTheLayer (2 methods), TestRegionColours, TestColorColoursTheWholeLayer; **each pinned in BUGS.md** ("certified by …"; the bugs were per-type, in both modes, not served-only) | Same de-parametrization: served cut to 6 types, saved kept on all 40. **This needs your call:** under the rule, the saved half is the "equivalent cheaper test" only because the served app copies the same code. TestTheSecondAxisFitsTheLayer's pin says "(40 types)", so keep that one whole unless you accept that argument. | 134 (60); 97 (44) without TestTheSecondAxisFitsTheLayer | Served per-type confirmation for 34 types | The same as P1, plus HC7-02/03/04 in the cscript. |
| P3 | test_marker_label_parity::test_the_line_options_leave_every_marker_alone (36 params, both modes; unpinned) | Halve to one representative per line option family. | 32 (14) | Some line-option × type combinations | Saved-mode per-type marker tests and test_twoway_option_parity.py. |
| P4 | server_facets TestEveryTypeFacetsTheSameWayInBothModes (95 tests; unpinned) | Do S5 first. If more is needed, cut to a 10-type subset. | 38 (17) | by() parity for 30 types | The parity corpus has 23 by() entries; TestByPanelsShareInBothModes. |
| P5 | Other mode-parametrized `[served]` halves (2,471 served-param tests in total): date_units 129, scheme_resolution 75, axis2_suboptions 67, function_expr 61, scheme_linewidth 58, help_claims_6 55, help_claims_8 56, lpolyci_band 51, axis_extents 47 | Review each: where a test is a per-type/per-value sweep and the claim is not served-specific, keep served on a subset. | about 250 (about 110) | Served cross-product beyond the parity corpus | Saved halves and the parity corpus. |
| — | test_mode_parity corpus (259 entries) | **Do not prune.** Purposeful entries; after S1/S2/S3/S6 the file costs about 170 test-s at -n 8 (from about 1,380). | — | — | — |
| — | Pinned per-type parity classes in server_layer_defects (TestEveryFigureCarriesTheSameHover, TestTheLegendSaysTheSameThing, TestALayerThatDrewNothingSaysSoInBothModes, TestMlabelIsDrawnExactlyAsTheSavedDashboardDrawsIt: each pinned "all 38 types, both modes") | **Keep.** Use S5 only. | — | — | — |
| — | label_sinks (security sinks, both modes); serve token/lifecycle/launcher tests (security, 15 pins, mostly wall-time waits) | **Keep in the default suite.** | — | — | — |

The P1–P5 total is about 610 u before the structural changes, **about 230 u after them** (≈ 270 if P2 includes TestTheSecondAxisFitsTheLayer). No function loses its last unit test. All of these trims remove only `[served]` parameters of sweeps whose functions keep both a saved test and a served test on a representative subset.

---

## 4. Tiering (a release/closeout tier, e.g. `-m slow` with an `addopts` exclusion, plus a `make test-release`)

| move to the release tier | u (b2) | notes |
|---|---|---|
| test_csp_browser.py (Chrome + real serve) | 90 | Keep test_csp.py (header/meta/nonce checks, 21 u) in the default suite. 1 pin; the pinned bug is also asserted at the header level. |
| test_responsive_layout.py, the Chrome classes (TestPagesFitInChrome, TestServedDocumentsFitInChrome, TestTheServedBsGridReflowsAsTheSavedOne) | about 80 | Keep TestTheProbe/find_chrome unit tests. 3 pins: in the default suite only the markup half then guards them. |
| test_by_scales_chrome.py (incl. 43 s test_hundred_panels_settle) | 52 | test_by_scales.py stays (both modes, no browser). 1 pin. |
| test_stale_cue_browser.py | 5 | test_saved_stale_cue.py stays. |
| help_claims_8 TestNoLayerNeedsScipyOrStatsmodels (2 subprocess sweeps) | 67 after S4 (135 before) | Keep test_no_source_line_imports_either (the AST check, cheap) in the default suite. |
| test_suite_lock.py (nested pytest runs) | 29 | Tooling only. |
| test_dataset_size_warning.py | 17.5 | Builds large datasets. |
| test_adversarial_matrix::TestTheMatrixIsComplete::test_every_pytest_entry_is_collected | 8 | Nested collect-only run. |
| Cert HC4-19..21 (a real `dash serve` blocking 61.6 s) | 62 cert-s | Move to the release cert. HC4-16..18 (stub serve) stay. |
| Cert twoway oracle re-measurement (pairs with C2) | about 150 cert-s | |
| **pytest total** | **about 340 u** | The release tier then runs these, plus `make test-floor` (multi-Python) and C2's re-measurement. |

`make check` currently runs pytest twice (test under Stata's Python, test-dev under Homebrew 3.14) and then the cert. Running the test-dev leg only in the release tier halves make check's pytest cost. Doing so gives up the dev-stack drift detection that `_BASELINES` exists for, so keep it at release.

---

## 5. Projection (u → wall at -n 12 = u / 7.07; ±20%)

| step | pytest u | pytest wall |
|---|---|---|
| today (b2, -n 6) | 5,038 | 867 s measured (about 713 s at -n 12) |
| + S1, S3, S6 | about 3,030 | about 430 s |
| + S2, S4, S5 | about 2,700 | about 385 s |
| + P1–P5 | about 2,470 | about 350 s |
| + tier (§4) | **about 2,130** | **about 300 s (5.0 min), at the limit** |

| cert | wall |
|---|---|
| today | 943 s (+ about 20 s for wp30_truth) |
| C1 (4 shards) | about 240 s |
| + C2 + HC4-19 tier + S3 | about 180–190 s (6 shards: about 150 s; floor wp29_truth 131 s) |

**Honest verdict.** pytest alone can reach about 5 minutes, but only with every structural change (S6, the harness compile cache, is the biggest single one), the served de-parametrization and the browser/stress tier. **pytest plus cert in 5 minutes on this machine is not reachable.**

- Run sequentially, it comes to about 300 + 185 ≈ 8 min.
- Run concurrently, the combined CPU is about 2,130 + about 800 cert-u ≈ 2,930 u against a 2,120 u budget, about 7 min, because throughput levels off at about 8 cores.

Reaching 5 minutes total would mean giving up one of these named kinds of coverage:

1. **The cert in the default loop** (Stata-side certification: the ado parser, Stata-evaluated qualifiers, twoway oracles, help examples run in Stata). It would run at release or closeout only, which is the WP-30 practice today, or on a second machine. This is the recommended option.
2. **Roughly all served-mode coverage beyond the parity corpus** (about 2,471 `[served]` parameters, about −500 u more) plus every real-serve subprocess test. Even that leaves pytest at about 3.8 min and still does not fit a 3–4 min cert.

Order of work by value: S1 (trivial, a real bug) → S3 → S6 → S2 → S7 → S4/S5 → C1 → tier → P1/P3/P4 → P2/P5 (with your decision) → C2.
