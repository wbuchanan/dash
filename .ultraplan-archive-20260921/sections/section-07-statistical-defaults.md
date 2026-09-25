# Section 07: Statistical defaults from the data and `c(level)`

## Overview
`dash` computes different numbers from Stata. Not differently-styled versions of the same
numbers — different numbers, from fixed constants where Stata derives from the data.

The clearest case, measured on two real datasets:

| dataset / variable | N | Stata `histogram` | `dash histogram` |
|---|---|---|---|
| `auto` / `mpg` | 74 | **bin=8**, start=12, width=3.625 | 10 bins |
| `nlsw88` / `wage` | 2,246 | **bin=33**, start=1.0050, width=1.2043 | 10 bins |

`dash_render.py:3001` is `n_bins = min(int(options.get("bin", 10)), _MAX_BINS)`. Until S05,
`bin()` was rejected by Stata's `syntax`, so the literal `10` was not merely a default — it
was **unreachable**, and could not be overridden at all.

**Decision taken:** defaults change to match Stata. Every change is recorded with before and
after values.

## User story
> As a Stata user, `dash histogram wage` gives me the histogram `histogram wage` gives me,
> and `level(90)` gives me a 90% band.

## Business requirements
- BR-07.1 Every statistical default matches Stata's documented rule for the same command.
- BR-07.2 Every Stata option controlling those computations is honoured.
- BR-07.3 `c(level)` is the default confidence level.
- BR-07.4 A value computed at render time and recomputed in JavaScript under filtering must
  use the **same** rule, so the picture does not jump.

## Technical requirements — the register

| Line | Today | Required | Stata's lever |
|---|---|---|---|
| `:3001` | 10 bins always | `k = min(sqrt(N), 10*ln(N)/ln(10))`, rounded | `bin()` `width()` `start()` |
| `:3003` | raw **counts** | **density** by default | `percent` `frequency` `density` `fraction` |
| `:1343-1344`, `:2441`, `:8101`, `:8123` | 95% fixed in four places | `level()`, defaulting to `c(level)` | `level()` |
| `:3066`, `:2611` | Gaussian kernel | **epanechnikov** for `kdensity` and `lpoly` | `kernel()` |
| `:3068` | scipy Scott's rule; `bwidth` **ignored** though reachable | honour `bwidth()` | `bwidth()` |
| `:4617` vs `:3068` | filter JS uses **Silverman**, render uses **Scott's** | one rule in both | — |
| `:2667`, `:2604` | `bwidth` as a **fraction of x-range**, clamped `[0.01,1.0]` | **absolute bandwidth in data units** | `bwidth()` |
| `:5951`, `:4121` | `function` over x ∈ [0,1] | `range()`, defaulting to the x-axis range | `range()` |
| `:5952` | `n_pts = 200` | **300** | `n()` |
| `:2880-2883`, `:2941-2944` | `fpfit` truncated to the 1st-99th percentile; 200 pts vs 150 in `fpfitci` | full estimation range, one grid size | — |
| `:4085` | `mband` invents `clip(ceil(n/5), 2, 20)` equal-**width** bands | `bands()`, cross-medians | `bands()` |
| `:2582` | `_compute_lpoly_fit` `bwidth=0.5` | rule-of-thumb from the data | — |
| `:1303` vs `:2513` | `n_boot` 200 vs 500, docstrings contradict; `seed=42` fixed | consistent, and seedable | `jseed()`-style |
| `:2560` | **unguarded** `float(options.get("bwidth","0.8"))` — crashes the render on non-numeric | validated with a clear message | — |
| `:2843`, `:2898` | `fpfit`/`fpfitci` never read `bwidth` or `degree`, contradicting `dash.sthlp:559-560` | honour or report | — |

Also here, carried from S06: **`map_function` must translate Stata's `^` to Python's `**`.**
`x^2` currently parses as `BitXor`, passes the AST validator at `:4175-4181`, then raises
`TypeError` on float arrays and draws a silent empty red line (`:4241-4243`).

## Risk: [yellow] — individually small changes, but they alter output everyone has already seen, so the CHANGELOG discipline matters more here than the code.

## Dependencies
- Depends on: S06 (the options must be accepted first — S05 — and the spec shape settled)
- Blocks: S08
- Parallel batch: 3

## TDD test stubs
- Test: `dash histogram mpg` produces 8 bins; `dash histogram wage` on nlsw88 produces 33 —
  values taken from Stata, recorded as fixtures with the command that produced them.
- Test: `bin(20)`, `width(2)` and `start(10)` each override correctly.
- Test: the default y-axis is density; `percent`, `frequency` and `fraction` each change it.
- Test: `lfitci` with no `level()` uses `c(level)`; `level(90)` widens the band; the four
  hardcoded sites all move together.
- Test: `kdensity` default kernel is epanechnikov; `kernel(gaussian)` changes it.
- Test: `kdensity ..., bwidth(2)` produces a visibly different curve from the default.
- Test: the initial KDE and the filtered-JS KDE agree when no rows are removed. This is the
  test for the Scott-vs-Silverman jump and it must compare values, not just run.
- Test: `lpoly ..., bwidth(5)` on `weight` uses an absolute bandwidth of 5, not the whole
  x-range.
- Test: `function y=x^2, range(0 10) n(400)` spans 0-10 with 400 points.
- Test: `function y=x^2` renders a parabola, not an empty line.
- Test: `fpfit` and `fpfitci` use the same grid size and the same x-range.
- Test: `lowess ..., bwidth(notanumber)` produces a clear error, not a crashed render.

## Tasks

<task type="auto" id="07-01">
  <name>Extract statistical ground truth from Stata</name>
  <files>test/fixtures/stat_truth.json, scripts/extract_stat_truth.do</files>
  <action>
    For each statistical layer, run Stata's own command on at least three datasets of
    different sizes and record the results: `histogram` bin/start/width; `kdensity` default
    kernel, bandwidth and grid; `lpoly` bandwidth and degree; `lowess` bwidth; `lfitci` and
    `qfitci` band endpoints at levels 90, 95 and 99; `fpfit` powers and fitted values.

    Record the exact command beside each value so a reviewer can re-derive it. The histogram
    row already has two verified entries — auto/mpg (8, 12, 3.625) and nlsw88/wage
    (33, 1.0049518, 1.2042921) — use those as the format.

    Where Stata's rule is documented, record the rule too, not just the output, so the
    implementation can be checked against the formula rather than curve-fitted to three
    samples.
  </action>
  <verify>The fixture covers every layer in the register, on at least three datasets, with commands recorded.</verify>
  <done>Stata's own answers are captured as the specification.</done>
</task>

<task type="auto" id="07-02">
  <name>Write the failing statistical tests</name>
  <files>test/test_statistical_defaults.py</files>
  <action>
    Drive every test from `stat_truth.json`. Assert on computed values — bin edges, band
    endpoints, curve values at sampled points — not on the presence of a glyph.

    Include the two tests that catch the self-inconsistencies, because they are invisible to
    any single-path test: initial-KDE vs filtered-JS-KDE agreement on an unfiltered dataset,
    and `fpfit` vs `fpfitci` grid and range agreement.

    Run. Confirm each failure is a value mismatch against Stata, and record the actual-vs-
    expected pairs — they become the CHANGELOG entries.
  </action>
  <verify>Every failure is a value mismatch with Stata, with both values recorded.</verify>
  <done>A failing, value-asserting test exists for every row of the register.</done>
</task>

<task type="auto" id="07-03">
  <name>Histogram: data-driven bins and selectable y-axis</name>
  <files>dash_render.py</files>
  <action>
    Implement Stata's bin rule at `:3001` and honour `bin()`, `width()` and `start()` with
    Stata's precedence — `width()` and `start()` together determine the grid; `bin()` sets a
    count. Keep the `_MAX_BINS` guard against resource exhaustion, but apply it after the
    rule, and warn when it clamps rather than clamping silently.

    Implement the y-axis family at `:3003`: density by default, with `percent`, `frequency`
    and `fraction` selectable.

    The JS recompute path (`:4563-4589`) reuses `ac.bin_edges` verbatim, so filtering changes
    bar heights but never bar boundaries. With `start()`/`width()` now explicit that is
    defensible and should be **documented** rather than changed — a moving grid under a
    filter is worse. But the y-axis scaling must recompute consistently: a density histogram
    under a filter must renormalise. Add that to the JS.
  </action>
  <verify>Bin counts match Stata on all fixture datasets; each y-axis mode is correct; a filtered density histogram renormalises.</verify>
  <done>`dash histogram` reproduces `histogram` and responds to every Stata option for it.</done>
</task>

<task type="auto" id="07-04">
  <name>Confidence level from level() and c(level)</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    `dash.ado` must read `c(level)` and serialize it, so Python has the session default
    without guessing. `level()` from S05 overrides it per plot.

    Replace the four hardcoded sites — `:1343-1344` (bootstrap percentiles), `:2441`
    (`t.ppf(0.975)`), and the server duplicates `:8101` and `:8123` — with one helper taking
    the level. Four sites is exactly how they drifted; one helper is the fix.

    Validate the level in Stata: a value outside (0,100) is an error there, where the user can
    see it, not a Python exception.

    Note: the server duplicates are fixed here for value-correctness, but S15 removes the
    duplication itself.
  </action>
  <verify>Band endpoints match Stata at 90, 95 and 99; `set level 90` changes the default; all four sites move together.</verify>
  <done>Confidence level is a user input with Stata's default, in one place.</done>
</task>

<task type="auto" id="07-05">
  <name>Kernels, bandwidths, and the Scott/Silverman inconsistency</name>
  <files>dash_render.py</files>
  <action>
    Default kernel becomes epanechnikov for `kdensity` (`:3066`) and `lpoly` (`:2611`), with
    `kernel()` honoured.

    `map_kdensity` (`:3068`) must honour `bwidth()`. It is currently ignored even though the
    option is reachable — a silent drop, not an unreachable default.

    Fix the `lpoly` bandwidth semantics (`:2667`, `:2604`): Stata's `bwidth()` is an absolute
    bandwidth in data units, not a fraction of the x-range clamped to `[0.01,1.0]`. Today
    `bwidth(5)` on `weight` clamps to the entire x-range — the opposite of the request. When
    no `bwidth()` is given, compute Stata's rule-of-thumb from the data rather than using the
    fixed 0.5 at `:2582`.

    Make the filter-callback KDE (`:4617`) use the same bandwidth rule as the initial render
    (`:3068`). Today one is Silverman and the other Scott's, so touching any filter makes the
    curve jump even when no rows are removed. The code comment at `:3080-3081` already admits
    this. Whichever rule is chosen, both paths must use it, and the test from 07-02 enforces
    that.

    Guard `:2560`'s `float(options.get("bwidth","0.8"))`, which has no try/except and crashes
    the whole render on a non-numeric value.
  </action>
  <verify>Kernels and bandwidths match Stata; the KDE does not move when an inert filter is touched; a bad bwidth errors clearly.</verify>
  <done>Smoothing parameters come from the user and the data, consistently across render and filter.</done>
</task>

<task type="auto" id="07-06">
  <name>function, fpfit, mband — domains, grids and operators; then commit</name>
  <files>dash_render.py, .ultraplan/CHANGELOG.md</files>
  <action>
    `map_function`: honour `range()` (`:5951`, `:4121`), defaulting to the x-axis range rather
    than [0,1]; honour `n()` with Stata's default of **300**, not 200 (`:5952`). Remove the
    dead reads at `:5953` and `:5960`. Translate Stata's `^` to Python's `**` before
    evaluation — `x^2` currently parses as `BitXor`, passes the AST validator, raises
    `TypeError` on float arrays and draws a silent empty line. Keep the AST whitelist intact;
    this is a translation step before validation, not a loosening of it.

    `fpfit`/`fpfitci`: use the full estimation range rather than the 1st-99th percentile
    (`:2880-2883`), and one grid size rather than 200 vs 150 (`:2941-2944`). Honour or report
    `bwidth()` and `degree()`, which `dash.sthlp:559-560` documents and the code ignores.

    `mband`: implement `bands()` with Stata's cross-median semantics, replacing the invented
    `clip(ceil(n/5), 2, 20)` equal-width bands at `:4085`.

    Reconcile `n_boot` (200 at `:1303` vs 500 at `:2513`, with contradicting docstrings) and
    make the seed settable rather than fixed at 42 (`:1304`).

    Write every changed default into `.ultraplan/CHANGELOG.md` with before and after values
    and the datasets that demonstrate the change. Regenerate the `examples/` dashboards and
    record which changed and how. Run all suites against the S01 baseline. Commit as
    single-issue commits.
  </action>
  <verify>All 07-02 tests pass; the CHANGELOG lists every altered default with before/after values; suites green.</verify>
  <done>Every statistical value comes from the data, the user's options, or `c(level)` — and every change is written down.</done>
</task>
