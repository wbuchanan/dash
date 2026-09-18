# Section 01: Baseline, environment and test-suite integrity

## Overview
Nothing in this plan can be trusted until the test suite can fail honestly. It currently
cannot. The pytest suite is RED (14 failures from an unguarded `statsmodels` import), the
Stata certification runner prints "ALL TESTS PASSED" on a machine where nothing was asserted,
the two richest certification scripts are not in the runner, and the Python that runs pytest
is a different interpreter from the Python that Stata uses.

This section makes the suite tell the truth, then records the baseline everything else is
measured against.

## User story
> As the developer, when I run the test suite I need a pass to mean the code works and a
> failure to name the thing that broke — so that after every subsequent section I can tell a
> regression from an unrelated environment problem.

## Business requirements
- BR-01.1 The suite must be green before any section commits (project rule 5).
- BR-01.2 A skipped test must be reported as skipped, never counted as a pass (rule 2).
- BR-01.3 Dependencies must be verified before use, not declared in a manifest (rule 15).

## Technical requirements
- TR-01.1 `map_lowess` must degrade with a named, actionable message when `statsmodels` is
  unavailable, not raise `ModuleNotFoundError` out of the render.
- TR-01.2 `run_all_cscripts.do` must increment `n_skip` and report it, and must include every
  `.cscript` in `test/`.
- TR-01.3 Both interpreters must be identified, version-pinned in a recorded fixture, and
  their Bokeh/pandas/numpy/scipy versions compared.

## Risk: [yellow] — low technical difficulty, but every later measurement depends on getting this exactly right.

## Dependencies
- Depends on: none
- Blocks: every other section
- Parallel batch: 1 (with S02 and S03 — disjoint file sets)

## TDD test stubs
- Test: with `statsmodels` importable, `map_lowess` returns a populated renderer.
- Test: with `statsmodels` unimportable (monkeypatched), `map_lowess` emits a `UserWarning`
  naming `statsmodels` and returns an empty renderer rather than raising.
- Test: the cscript runner's skip counter increments when a dependency guard fires.
- Test: the runner's final summary reports a non-zero skip count when scripts were skipped.
- Test: every `.cscript` file in `test/` appears in `run_all_cscripts.do`.
- Test: a fixture records both interpreters' versions and fails if either drifts.

## Tasks

<task type="auto" id="01-01">
  <name>Record the measured baseline before touching anything</name>
  <files>.ultraplan/BASELINE.md</files>
  <action>
    Run the pytest suite and capture the exact counts and the full list of failing test ids.
    Run the certification suite under `arch -arm64 /usr/local/bin/stata-mp` and capture its
    output verbatim.

    Record both in `.ultraplan/BASELINE.md`, along with: the two Python interpreter paths and
    versions, the versions of bokeh, pandas, numpy, scipy and statsmodels under each, the
    Stata version and flavour, `c(scheme)`, `c(level)`, and the current git SHA.

    Do not fix anything in this task. The point is a fixed, dated reference that every later
    section compares against.
  </action>
  <verify>BASELINE.md exists and contains both suites' verbatim output plus the environment table.</verify>
  <done>A dated, complete baseline exists and is committed.</done>
</task>

<task type="auto" id="01-02">
  <name>Write the failing tests for the statsmodels guard</name>
  <files>test/test_dependency_guards.py</files>
  <action>
    Write tests before the fix (rule 8).

    Test one: with `statsmodels` available, `map_lowess` behaves as it does today.
    Test two: monkeypatch the import so `statsmodels.nonparametric.smoothers_lowess` raises
    `ModuleNotFoundError`, call `map_lowess`, and assert it emits a `UserWarning` whose text
    names `statsmodels` and suggests `dash_setup`, and returns a renderer with an empty data
    source — the same degradation shape already used for the slider dtype guard at
    `dash_render.py:7203`.

    Run them. Test two must fail with `ModuleNotFoundError` escaping, which is the current
    behaviour and the right failure.
  </action>
  <verify>Test two fails with an escaping ModuleNotFoundError; test one passes.</verify>
  <done>The failure has been read and confirmed to be the right failure.</done>
</task>

<task type="auto" id="01-03">
  <name>Guard the statsmodels import and audit every other lazy import</name>
  <files>dash_render.py</files>
  <action>
    Wrap the `statsmodels` import at `dash_render.py:2547` so a failure warns and degrades
    instead of raising.

    Then audit every other lazy import in the file and apply the same treatment where a
    missing library would abort a render: `scipy.stats` at `:2404` (lfitci/qfitci),
    `scipy.stats.gaussian_kde` at `:3055` (kdensity), `scipy.interpolate.PchipInterpolator`
    at `:4001` (mspline). Each should name the missing package and the plot type it disables.

    Note but do NOT fix here: the generated server app imports `statsmodels` and `scipy` at
    module scope (`:7882`), so a missing library breaks the whole app regardless of plot
    type. That belongs to S14.

    Also correct `dash_setup.ado` and `dash.pkg`, which both declare `statsmodels` a hard
    dependency. It is required only by `lowess`. Make the declaration honest.
  </action>
  <verify>All tests from 01-02 pass; the full pytest suite is green.</verify>
  <done>No missing optional dependency can abort a standalone render, and the dependency declarations match reality.</done>
</task>

<task type="auto" id="01-04">
  <name>Make the certification runner incapable of a false pass</name>
  <files>test/run_all_cscripts.do</files>
  <action>
    Three defects, all in `test/run_all_cscripts.do`.

    First: the 15 dependency guards `exit 0`, which the runner scores as PASS. Change the
    guards to signal a distinct skip condition, and have the runner classify it as a skip.

    Second: `n_skip` (around line 36) is never incremented, so the summary (around line 216)
    always prints "0 skipped". Increment it, and make the summary line report passes,
    failures and skips separately.

    Third — and this is the one that matters — make the runner **fail loudly** if the number
    of skips equals the number of scripts. A machine with no `jsonio` and no Python currently
    prints ALL TESTS PASSED having asserted nothing. That must become a hard error.

    Write the test for this before the change: assert that a run in which every script skips
    does not report success.
  </action>
  <verify>A forced all-skip run reports a non-zero skip count and does not print ALL TESTS PASSED.</verify>
  <done>The runner cannot report success without having asserted something.</done>
</task>

<task type="auto" id="01-05">
  <name>Adopt the two orphaned certification scripts</name>
  <files>test/run_all_cscripts.do, test/test_adversarial.cscript, test/test_e2e_serve.cscript</files>
  <action>
    `test_adversarial.cscript` and `test_e2e_serve.cscript` are the two richest scripts in the
    suite and neither is in the runner. Add both.

    Run them first, on their own, and record what they actually do. If either fails, that is
    a finding, not a blocker for this task — record the failure in BASELINE.md and, if it is
    a genuine defect, note which later section owns it. `test_e2e_serve.cscript` in particular
    is expected to surface the server-mode defects that S14 fixes; mark it xfail with a
    comment naming S14 rather than deleting or weakening it.

    Also note in BASELINE.md that only 4 of 11 cscripts currently reach Python end to end —
    `test_parser.cscript`'s single `dash` call passes `name()`, which routes to
    `_dash_register_graph` and never renders. S16 owns widening that.
  </action>
  <verify>Both scripts run under the runner; their results are recorded; any xfail names its owning section.</verify>
  <done>No certification script is orphaned, and the reason for every xfail is written down.</done>
</task>

<task type="auto" id="01-06">
  <name>Pin both interpreters and commit the baseline</name>
  <files>test/conftest.py, .ultraplan/BASELINE.md</files>
  <action>
    The pytest suite runs `/opt/homebrew/bin/python3.14`; Stata's `python_exec` is
    `/opt/anaconda3/bin/python3` (3.13.9). They are different interpreters with different
    library versions, so the Python unit tests and the Stata certification scripts are not
    exercising the same code.

    Add a session fixture that records the running interpreter and the versions of bokeh,
    pandas, numpy and scipy, and compares them against the values recorded in BASELINE.md.
    On a mismatch, emit a clear warning naming both — not a failure, because a developer may
    legitimately be on a different machine, but never silence.

    Add a short section to BASELINE.md documenting the `arch -arm64` requirement and why:
    launched without it, Stata runs its x86_64 slice and fails to load the arm64
    `libpython3.13.dylib` with r(7100).

    Run the full suite. It must be green. Commit.
  </action>
  <verify>Full pytest suite green; certification suite runs and reports honest counts; BASELINE.md committed.</verify>
  <done>The suite tells the truth, and there is a fixed reference to measure every later section against.</done>
</task>
