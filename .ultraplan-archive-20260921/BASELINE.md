# dash — Measured Baseline (pre-change reference)

**Date recorded:** 2026-09-18
**Repository:** `/Users/billy/Desktop/Programs/StataPrograms/d/dash`
**Branch:** `feature/batch1-foundation`
**Git SHA (HEAD):** `3948ce8fd2ca62dc1a5027772035d98935291db9`
**Working tree at time of measurement:** clean except untracked `.ultraplan/` and `AGENTS.md`
**Plan task:** 01-01 (Section 01 — Baseline, environment and test-suite integrity)

This document is the fixed reference every later section compares against. Nothing in the
repository was modified to produce it. All command output below is verbatim.

---

## 1. Python unit test suite (pytest)

Command:

```
cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/ -q --no-header 2>&1 | tail -40
```

### Headline result

```
14 failed, 1480 passed, 10 warnings in 33.24s
```

| Metric | Value |
|---|---|
| Passed | 1480 |
| Failed | 14 |
| Warnings | 10 |
| Errors | 0 |
| Wall time | 33.24s |

### Full list of failing test ids (verbatim `short test summary info`)

```
=========================== short test summary info ============================
FAILED test/test_glyphs.py::TestEdgeCasesEmptyData::test_lowess_fewer_than_2_points_returns_renderer
FAILED test/test_glyphs.py::TestEdgeCasesEmptyData::test_lowess_all_nan_returns_renderer
FAILED test/test_glyphs.py::TestMapLowess::test_lowess_returns_renderer - Mod...
FAILED test/test_glyphs.py::TestMapLowess::test_lowess_line_glyph - ModuleNot...
FAILED test/test_glyphs.py::TestMapLowess::test_lowess_lcolor_applied - Modul...
FAILED test/test_glyphs.py::TestMapLowess::test_lowess_source_sorted_by_x - M...
FAILED test/test_glyphs.py::TestLegendLabelCoverage::test_lowess_legend - Mod...
FAILED test/test_glyphs.py::TestLowessConstantX::test_constant_x_returns_renderer
FAILED test/test_glyphs.py::TestLowessConstantX::test_constant_x_produces_empty_line
FAILED test/test_glyphs.py::TestLowessConstantX::test_normal_x_still_works - ...
FAILED test/test_html_output.py::TestLowessHtmlOutput::test_lowess_html_contains_line_glyph
FAILED test/test_html_output.py::TestColorRenderingAllPlotTypes::test_lowess_lcolor_in_html
FAILED test/test_pipeline_integration.py::TestLowessBasicFunctionality::test_lowess_produces_smooth_line
FAILED test/test_pipeline_integration.py::TestEdgeCaseData::test_ec04_constant_x_lowess_no_crash
14 failed, 1480 passed, 10 warnings in 33.24s
```

The 14 failing ids as clean identifiers:

1. `test/test_glyphs.py::TestEdgeCasesEmptyData::test_lowess_fewer_than_2_points_returns_renderer`
2. `test/test_glyphs.py::TestEdgeCasesEmptyData::test_lowess_all_nan_returns_renderer`
3. `test/test_glyphs.py::TestMapLowess::test_lowess_returns_renderer`
4. `test/test_glyphs.py::TestMapLowess::test_lowess_line_glyph`
5. `test/test_glyphs.py::TestMapLowess::test_lowess_lcolor_applied`
6. `test/test_glyphs.py::TestMapLowess::test_lowess_source_sorted_by_x`
7. `test/test_glyphs.py::TestLegendLabelCoverage::test_lowess_legend`
8. `test/test_glyphs.py::TestLowessConstantX::test_constant_x_returns_renderer`
9. `test/test_glyphs.py::TestLowessConstantX::test_constant_x_produces_empty_line`
10. `test/test_glyphs.py::TestLowessConstantX::test_normal_x_still_works`
11. `test/test_html_output.py::TestLowessHtmlOutput::test_lowess_html_contains_line_glyph`
12. `test/test_html_output.py::TestColorRenderingAllPlotTypes::test_lowess_lcolor_in_html`
13. `test/test_pipeline_integration.py::TestLowessBasicFunctionality::test_lowess_produces_smooth_line`
14. `test/test_pipeline_integration.py::TestEdgeCaseData::test_ec04_constant_x_lowess_no_crash`

**All 14 failures are lowess-related and all share one root cause:** `statsmodels` cannot be
imported under `/opt/homebrew/bin/python3.14` because its `packaging` dependency is missing.
This is a pre-existing environment fact, NOT a defect in `dash`. Representative traceback tail:

```
                try:
                    self.figures[name] = self._make_figure(
                        g, src, facet_view=_qual_view
                    )
                except Exception as exc:
>                   raise RuntimeError(
                        f"dash_render: failed to build figure '{name}': {exc}"
                    ) from exc
E                   RuntimeError: dash_render: failed to build figure 'g1': No module named 'packaging'

dash_render.py:7697: RuntimeError
```

### Warnings captured in the same run (verbatim)

```
=============================== warnings summary ===============================
test/test_phase5.py::TestPerGraphIfFilter::test_if_expr_invalid_no_crash
test/test_phase5.py::TestPerGraphIfFilter::test_if_expr_injection_blocked
test/test_phase5.py::TestPerGraphIfFilter::test_if_expr_getattr_blocked
test/test_phase5.py::TestPerGraphIfFilter::test_if_expr_setattr_blocked
test/test_phase5.py::TestIfExprRceHardening::test_at_poc_payload_blocked_end_to_end
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/../dash_render.py:6937: UserWarning: dash: if_expr filter skipped — invalid syntax (<unknown>, line 1)
    filtered_df = self._apply_graph_filter(g)

test/test_pipeline_integration.py::TestEdgeCaseData::test_ec01_empty_dataframe_scatter_no_crash
test/test_pipeline_integration.py::TestEdgeCaseData::test_ec01_empty_dataframe_lfit_no_crash
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/../dash_render.py:5970: UserWarning: dash: variable(s) ['mpg', 'weight'] not found in data source; skipping glyph. Check that all plot variables exist in the dataset.
    self._add_glyph(fig, source, ptype, pyvar, pxvar, popts,

test/test_pipeline_integration.py::TestEdgeCaseData::test_ec01_empty_dataframe_histogram_no_crash
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/../dash_render.py:5947: UserWarning: dash: variable(s) ['mpg'] not found in data source; skipping glyph. Check that all plot variables exist in the dataset.
    self._add_glyph(fig, source, ptype, pyvar, pxvar, popts,

test/test_pipeline_integration.py::TestEdgeCaseData::test_ec04_constant_x_lfit_no_crash
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/../dash_render.py:2320: RankWarning: Polyfit may be poorly conditioned
    coeffs = np.polyfit(x, y, 1)  # [slope, intercept]

test/test_server.py::TestServerSliderStringFallback::test_make_document_with_slider_on_string_does_not_raise
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_server.py:7570: UserWarning: dash: filter 'group' type 'slider' requires numeric data; skipping widget (use type(dropdown) for string columns).
    mod.make_document(doc)
```

---

## 2. Stata certification suite (.cscript)

Command:

```
cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && arch -arm64 /usr/local/bin/stata-mp -b do test/run_all_cscripts.do
```

Log file produced: `/Users/billy/Desktop/Programs/StataPrograms/d/dash/run_all_cscripts.log`
(the do-file `cd`s to the repo root, so the log lands there, not in `test/`).
Shell exit status of the Stata invocation: `0` — **but Stata batch mode exits 0 even on error,
so the exit status carries no information; the log is the only evidence.**

### Run header (verbatim)

```
============================================================
  dash certification script runner
  18 Sep 2026 14:44:44
============================================================
```

### Per-script result lines (verbatim, in runner order)

```
[ PASS] test_tokenizer.cscript
[ PASS] test_parser.cscript
[ PASS] test_jsonio.cscript
[ PASS] test_e2e_single.cscript
[ PASS] test_e2e_multi.cscript
[ PASS] test_e2e_filters.cscript
[ PASS] test_e2e_kpi.cscript
[ PASS] test_ado_loads.cscript
[ PASS] test_mata_autoload.cscript
```

No `[ FAIL]` line was emitted. No `SKIP:` line appears anywhere in the log, which means the
dependency guards described in section 4 did **not** fire on this machine — `jsonio` and Python
were both available, so these 9 scripts did execute their assertions on this run.

### Summary block (verbatim)

```
============================================================
  Results: 9 passed, 0 failed, 0 skipped  (of 9 total)
============================================================
ALL TESTS PASSED
```

### `.cscript` files on disk vs. files the runner invokes — CONFIRMED

`ls test/*.cscript` — **11 files on disk:**

```
test_ado_loads.cscript
test_adversarial.cscript
test_e2e_filters.cscript
test_e2e_kpi.cscript
test_e2e_multi.cscript
test_e2e_serve.cscript
test_e2e_single.cscript
test_jsonio.cscript
test_mata_autoload.cscript
test_parser.cscript
test_tokenizer.cscript
```

The runner `test/run_all_cscripts.do` contains exactly **9** numbered invocation blocks:

| # | Script invoked by runner | Working dir the runner uses |
|---|---|---|
| 1 | `test_tokenizer.cscript` | `test/` |
| 2 | `test_parser.cscript` | `test/` |
| 3 | `test_jsonio.cscript` | `test/` |
| 4 | `test_e2e_single.cscript` | `test/` |
| 5 | `test_e2e_multi.cscript` | `test/` |
| 6 | `test_e2e_filters.cscript` | `test/` |
| 7 | `test_e2e_kpi.cscript` | `test/` |
| 8 | `test_ado_loads.cscript` | `test/` |
| 9 | `test_mata_autoload.cscript` | repo root (needs `findfile` to see `dash_parse.mata` via `.`) |

**Orphans — on disk but never invoked by the runner (2):**

- `test/test_adversarial.cscript`
- `test/test_e2e_serve.cscript`

11 on disk, 9 invoked, 2 orphaned. This confirms the prior finding exactly.

### State of `run_all_cscripts.log` in git

```
$ git ls-files run_all_cscripts.log
(no output)
$ git ls-files --error-unmatch run_all_cscripts.log
error: pathspec 'run_all_cscripts.log' did not match any file(s) known to git
Did you forget to 'git add'?
rc=1
```

**The log is NOT tracked in git**, and no `.log` file anywhere in the repo is
(`git ls-files '*.log'` returns nothing).

It is also absent from `git status` because it is ignored — but not by the repo's `.gitignore`,
whose entire contents are:

```
__pycache__/*
test/__pycache__
test/__pycache__/*
.claude/
*.html
```

The ignore comes from `.git/info/exclude`, a large boilerplate exclude list that is **not under
version control and therefore not shared with any clone**:

```
$ git check-ignore -v run_all_cscripts.log basic_scatter.log test_adversarial.log
.git/info/exclude:130:*.log	run_all_cscripts.log
.git/info/exclude:130:*.log	basic_scatter.log
.git/info/exclude:130:*.log	test_adversarial.log
```

That same `.git/info/exclude` also ignores `*.json`, `*.csv`, `*.txt`, `*.dta` and `*.xml`
repo-wide. On a fresh clone none of those ignores exist, so Stata `.log` files and any JSON
fixtures would show up as untracked noise there. There is also a global excludes file at
`/Users/billy/.git_template/info/exclude`.

`git ls-files` is therefore the only reliable check for these files, and it proves this log is
not under version control. No `git checkout -- run_all_cscripts.log` was needed or possible.

A pre-existing copy of this log dated `Apr 24 04:04` (10743 bytes) was present before the run.
It was backed up to `/tmp/dash-wf/run_all_cscripts.log.orig`, the suite overwrote it, and the
original was restored byte-for-byte afterwards. `git status --porcelain` after restoration:

```
?? .ultraplan/
?? AGENTS.md
```

— identical to the pre-run state. The working tree is clean.

---

## 3. Environment

### Python interpreters

There are **two different Python interpreters** in play and they do not share libraries.

| | `/opt/homebrew/bin/python3.14` (pytest runs here) | `/opt/anaconda3/bin/python3` (Stata's `python_exec`) |
|---|---|---|
| Python | **3.14.5** | **3.13.9** |
| bokeh | 3.9.0 | 3.8.0 |
| pandas | 3.0.1 | 2.3.3 |
| numpy | 2.4.3 | 2.3.5 |
| scipy | 1.17.1 | 1.16.3 |
| statsmodels | **BROKEN** (see below) | 0.14.5 |

**This divergence is itself a baseline fact:** the Python unit tests exercise bokeh 3.9.0 /
pandas 3.0.1, while anything `dash.ado` actually runs inside Stata exercises bokeh 3.8.0 /
pandas 2.3.3. A pytest pass does not prove the same code path works under Stata, and vice versa.

#### statsmodels under the homebrew interpreter — BROKEN (verbatim)

```
$ /opt/homebrew/bin/python3.14 -c "import statsmodels.api"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import statsmodels.api
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/__init__.py", line 1, in <module>
    from statsmodels.compat.patsy import monkey_patch_cat_dtype
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/compat/__init__.py", line 1, in <module>
    from statsmodels.tools._test_runner import PytestTester
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/tools/__init__.py", line 1, in <module>
    from .tools import add_constant, categorical
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/tools/tools.py", line 8, in <module>
    from statsmodels.tools.data import _is_using_pandas
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/tools/data.py", line 4, in <module>
    from statsmodels.compat.numpy import NP_LT_2
  File "/opt/homebrew/lib/python3.14/site-packages/statsmodels/compat/numpy.py", line 42, in <module>
    from packaging.version import Version, parse
ModuleNotFoundError: No module named 'packaging'
```

This single missing transitive dependency (`packaging`) is the sole cause of all 14 pytest
failures in section 1. It is a pre-existing environment condition, not a `dash` defect.
statsmodels imports fine (0.14.5) under the anaconda interpreter Stata actually uses.

### Stata

| Property | Value |
|---|---|
| Banner | `StataNow 19.5` — `MP—Parallel Edition` |
| `c(stata_version)` | `19.5` |
| `c(version)` | `19.5` |
| `c(edition_real)` | `MP` |
| `c(flavor)` | `IC` *(see note)* |
| `c(scheme)` | **`stcolor`** |
| `c(level)` | **`95`** |
| `c(machine_type)` | `Mac (Apple Silicon)` |
| `c(os)` | `Unix` |
| `c(maxvar)` | `5000` |
| `c(processors)` | `12` |
| License | Single-user 12-core, expiring 14 Apr 2027 (serial redacted) |
| `set python_exec` | `/opt/anaconda3/bin/python3` |
| Python library path | `/opt/anaconda3/lib/libpython3.13.dylib` |
| Python `initialized` | `no` (until first `python:` block) |

*Note on `c(flavor)`:* the banner and `c(edition_real)` both say **MP**, but `c(flavor)` returns
`IC` and `c(maxvar)` is 5000. Recorded verbatim as observed. Any later code that branches on
`c(flavor)` must not assume it reports `MP` on this machine.

`profile.do` in use: `/Users/billy/Documents/Stata/profile.do` (runs on every batch start).

### How Stata must be invoked

```
arch -arm64 /usr/local/bin/stata-mp -b do /abs/path/to/file.do
```

The `arch -arm64` prefix is **mandatory**. `/usr/local/bin/stata-mp` is a universal binary;
without `arch -arm64` macOS selects the x86_64 slice, which cannot load the arm64
`libpython3.13.dylib` and dies with **`r(7100)`**. Since `dash` calls Python from inside Stata,
every `dash` invocation under the wrong slice fails at the first `python:` block.

Every do-file used against this repo needs this header:

```stata
clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
```

The adopath as the certification runner establishes it (verbatim from the run log):

```
  [1]              "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"
  [2]              "/Users/billy/Desktop/Programs/Java/StataJSON/"
  [3]  (BASE)      "/Applications/StataNow/ado/base/"
  [4]  (SITE)      "/Applications/StataNow/ado/site/"
  [5]              "."
  [6]  (PERSONAL)  "/Users/billy/Library/Application Support/Stata/ado/personal/"
  [7]  (PLUS)      "/Users/billy/Library/Application Support/Stata/ado/plus/"
  [8]  (OLDPLACE)  "~/ado/"
```

### Git

| Property | Value |
|---|---|
| `git rev-parse HEAD` | `3948ce8fd2ca62dc1a5027772035d98935291db9` |
| Branch | `feature/batch1-foundation` |
| Main branch | `main` |
| `git status --porcelain` | `?? .ultraplan/` and `?? AGENTS.md` only |

---

## 4. Dependency guards: why "ALL TESTS PASSED" can be worthless

### Count of `exit 0` guards per `.cscript`

```
$ for f in test/*.cscript; do echo -n "$f: "; grep -c 'exit 0' "$f"; done
test/test_ado_loads.cscript: 0
test/test_adversarial.cscript: 3
test/test_e2e_filters.cscript: 2
test/test_e2e_kpi.cscript: 2
test/test_e2e_multi.cscript: 2
test/test_e2e_serve.cscript: 3
test/test_e2e_single.cscript: 2
test/test_jsonio.cscript: 1
test/test_mata_autoload.cscript: 0
test/test_parser.cscript: 0
test/test_tokenizer.cscript: 0
```

**Total `exit 0` guards across all 11 `.cscript` files: 15.**
Of those, **9** are in the 9 scripts the runner actually invokes
(`test_e2e_filters` 2, `test_e2e_kpi` 2, `test_e2e_multi` 2, `test_e2e_single` 2,
`test_jsonio` 1) and **6** are in the two orphaned scripts
(`test_adversarial` 3, `test_e2e_serve` 3).

Exact guard locations:

```
$ grep -n 'exit 0' test/*.cscript
test/test_e2e_filters.cscript:19:    exit 0
test/test_e2e_filters.cscript:29:    exit 0
test/test_adversarial.cscript:21:    exit 0
test/test_adversarial.cscript:31:    exit 0
test/test_adversarial.cscript:41:    exit 0
test/test_e2e_kpi.cscript:19:    exit 0
test/test_e2e_kpi.cscript:29:    exit 0
test/test_e2e_multi.cscript:19:    exit 0
test/test_e2e_multi.cscript:29:    exit 0
test/test_e2e_serve.cscript:20:    exit 0
test/test_e2e_serve.cscript:30:    exit 0
test/test_e2e_serve.cscript:41:    exit 0
test/test_e2e_single.cscript:19:    exit 0
test/test_e2e_single.cscript:29:    exit 0
test/test_jsonio.cscript:15:    exit 0
```

### The defect in the scoring scheme

A guard looks like this (`test/test_e2e_single.cscript`, lines 14-30):

```stata
capture which jsonio
if _rc != 0 {
    display as error "SKIP: jsonio not installed. Run dash_setup first."
    exit 0
}

capture {
    python:
pass
    end
}
if _rc != 0 {
    display as error "SKIP: Python not available."
    exit 0
}
```

The runner scores each script purely on the return code:

```stata
capture {
    do "test_e2e_single.cscript"
}
local rc = _rc
if `rc' == 0 {
    display as text "[ PASS] test_e2e_single.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_single.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
```

`exit 0` is a *successful* exit. A skipped script therefore returns rc==0 and is counted as
`[ PASS]`, and `n_skip` — which the summary line prints — is initialised to 0 and **never
incremented anywhere in the runner**. Consequences:

1. On a machine without `jsonio` or without Python, `test_e2e_single`, `test_e2e_multi`,
   `test_e2e_filters`, `test_e2e_kpi` and `test_jsonio` all bail out before asserting anything,
   all return 0, and the runner prints **`Results: 9 passed, 0 failed, 0 skipped` / `ALL TESTS
   PASSED`** having verified essentially nothing beyond the tokenizer, parser, and two loader
   tests.
2. The "0 skipped" figure in the summary is structurally incapable of being non-zero — it is
   not evidence that nothing was skipped.
3. The only way to tell a real pass from a silent skip today is to grep the log for `SKIP:`.
   On **this** run no `SKIP:` line was present, so the 9 passes above are genuine.

### Baseline integrity assessment

| Concern | Status at baseline |
|---|---|
| pytest failures | 14, all lowess, all from the missing `packaging` module — environmental |
| cscript failures | 0 real failures; all 9 invoked scripts genuinely executed on this run |
| cscript orphans | 2 (`test_adversarial.cscript`, `test_e2e_serve.cscript`) — never run by CI or the runner |
| skip-as-pass hazard | 15 `exit 0` guards; runner has no skip accounting; `n_skip` is dead |
| interpreter divergence | pytest and Stata use different Pythons with different library versions |

---

*End of baseline. Recorded 2026-09-18 against commit `3948ce8` on `feature/batch1-foundation`.
No source file was modified to produce this document.*

---

# Addendum — defects surfaced while executing S01 (2026-09-18)

Recorded per plan task 01-05: *"If either fails, that is a finding, not a blocker for this
task — record the failure in BASELINE.md and note which later section owns it."*

## F1. The certification suite's green was partly false [CONFIRMED]

`test/run_all_cscripts.do` reported **"Results: 9 passed, 0 failed, 0 skipped / ALL TESTS
PASSED"**. That was not accurate. Two independent defects produced it.

**F1a — the dependency guards swallowed the code after them.** Eight guards used the form

```stata
capture {
    python:
pass
    end
}
```

An **indented `end` is not recognised as the Python block terminator**, so Stata kept feeding
subsequent do-file lines into Python instead of executing them as Stata commands. Proven by
a differential test:

| pattern | result |
|---|---|
| `capture { python: \n pass \n␣␣␣␣end \n }` | the *next* `display` never executed at all |
| `capture { python: \n import bokeh \n␣␣␣␣end \n }` | `r(7102)` |
| `capture python: import bokeh` (one line) | `r(0)` — works |

This is the same defect already documented at `dash.ado:137-141` for `python:`/`end` blocks
inside `program define`. Whatever followed each guard — including assertions — was consumed.

**F1b — the runner could not report a skip.** `n_skip` was initialised and never incremented,
and the 15 dependency guards used `exit 0`, which the runner scored as PASS. A machine with
no `jsonio` and no Python printed `ALL TESTS PASSED` having asserted nothing.

**Fixed in S01:** guards converted to the single-line form; `exit 0` → `exit 111` in all 15
skip guards; the runner classifies `111` as SKIP, increments `n_skip`, and now **hard-errors
when every script skips**. The two orphaned scripts (`test_adversarial.cscript`,
`test_e2e_serve.cscript`) are now invoked.

## F2. Five end-to-end scripts fail once their assertions actually run [OWNER: S16-03]

With F1a fixed, the assertions that were being swallowed now execute — and five scripts fail:

| script | rc |
|---|---|
| `test_e2e_multi.cscript` | 132 |
| `test_e2e_filters.cscript` | 133 |
| `test_e2e_kpi.cscript` | 132 |
| `test_adversarial.cscript` | 132 |
| `test_e2e_serve.cscript` | 132 |

**These are pre-existing defects, not regressions.** Evidence: the `_json_escape() already
exists` Mata error appears **twice in the pre-change log** while it still printed ALL TESTS
PASSED.

**Root cause, diagnosed by solo run.** The scripts assert on dashboard content by reading the
generated HTML line-by-line into a Stata local:

```stata
file read `fh' ln
if strpos(`"`ln'"', "Avg MPG") > 0 ...
```

Two failure modes, both fatal and both inherent to the approach:
1. `r(132) too few quotes` — HTML is full of `"`, so the macro reference breaks.
2. Wrapping in `macval()` fixes that, and then hits **`r(130) expression too long`** — a
   Bokeh standalone file embeds its model JSON on single lines megabytes long, far past
   Stata's expression limit.

So the line-scan mechanism cannot work against Bokeh output at all, and no patch to it will
help. The assertions must be performed **Python-side** (read the file in Python, set a Stata
local via `sfi`). That is a rewrite of the e2e assertion harness, which **S16-03 owns**
("widen the end-to-end coverage… give the parse-only scripts a render step").

Deliberately **not** fixed in S01: doing it here would be scope creep into S16 and would mean
rewriting ~15 assertion blocks across 7 scripts.

## F3. `test_e2e_single.cscript` skips for a real reason [OWNER: S16-03]

It now reports SKIP rather than a false PASS. Its dependency guard genuinely fires. Worth
confirming which one during S16-03.

## F4. `dash` cannot open a browser on macOS [OWNER: S14-04]

A solo cscript run emitted:

```
/bin/bash: xdg-open: command not found
```

`xdg-open` is Linux. On macOS the command is `open`. Commit `2470b8a` fixed the *Windows*
browser path; the macOS path still falls through to `xdg-open`. Combined with the audit
finding that **no `_rc` is checked after any of the six `shell` calls**, a user on macOS gets
no browser and no error. S14-04 already owns the browser/`nobrowser` work.

## F5. `.git/info/exclude` hides fixture files [ADVISORY]

Line 58 is `*.json`, so `test/fixtures/scheme_truth.json` is invisible to `git add` on this
machine and required `git add -f`. The same file also excludes `*.csv`, `*.txt`, `*.dta` and
`*.xml` repo-wide. `.git/info/exclude` is **not version-controlled**, so these files would be
ordinary untracked files on any other clone — a real hazard for a package that passes JSON
between Stata and Python.

## F6. `net install` subdirectory semantics — NOT empirically verified [OPEN]

Plan task 02-02 called for confirming empirically whether Stata's `net install` preserves a
`f schemes/x.scheme` subdirectory or flattens the file into the install root. **That probe
was not run.** The agent that attempted it in the first run of this batch destroyed the
session's filesystem access, and re-running it mid-batch was judged not worth the risk.

Documentary evidence was sought instead and is inconclusive: Stata ships no `.pkg` files of
its own to use as examples (0 found under `/Applications/Stata/ado`), and `net.sthlp` does
not describe the `f`/`F` directive semantics — that lives in the Programming Reference
Manual, not the online help.

**This does not leave the package at risk.** The implementation resolves schemes from BOTH
`<install dir>/schemes/` and `<install dir>/` (`SchemeParser._SCHEME_SEARCH_DIRS`), and
`test_packaging.py` is parametrized over both layouts — `flat` and `as-declared` — and passes
for both. The package therefore works whichever choice Stata makes; the open question is
documentary only.

To close it later, run a real local `net install` into a temp target **from a shell whose
working directory is outside the staging tree**, and record which layout results.

## F7. `_COLOR_MAP` disagrees with Stata for 52 of 68 shared colour names [OWNER: S09]

Found while translating the schemes, and larger than the scheme work itself.
`OptionTranslator._COLOR_MAP` is dash's Stata-colour-name table, used for **every**
user-supplied colour — `mcolor()`, `lcolor()`, `fcolor()` and the rest. Compared against
Stata's own `color-<name>.style` files:

| | count |
|---|---|
| Stata named colours available | 92 |
| dash `_COLOR_MAP` entries (before this batch) | 73 |
| names present in both | 68 |
| **of which DISAGREE with Stata** | **52** |
| Stata names dash lacked | 24 |

Representative disagreements (dash -> Stata):

| name | dash | Stata | note |
|---|---|---|---|
| `green` | `#00ff00` | `#008000` | dash uses CSS lime |
| `edkblue` | `#00008b` | `#3e647d` | dash uses CSS darkblue |
| `gs1`…`gs15` | all 15 wrong | | dash's `gs10`-`gs15` are near-white; Stata's are mid-greys (`gs6` = `#606060`, dash had `#999999`) |
| `ltbluishgray` | `#d9e8f0` | `#eaf2f3` | s2color's background |
| `cranberry` | `#a00000` | `#c10534` | |
| `lavender` | `#c4b8d5` | `#938dd2` | |

**Consequence:** `dash scatter y x, mcolor(green)` renders a different colour from
`twoway scatter y x, mcolor(green)`. This is a plain drop-in-replacement failure affecting
every named colour a user types.

**Not fixed in this batch, deliberately.** Correcting 52 values changes the colour of
essentially every existing output and will move many tests that assert specific hex. That
deserves its own focused commit with a migration note, and it belongs with **S09**, which
already owns "style options reach the property they name". Batch 1's remit was scheme
translation.

**What WAS done here, and why it is safe:** the 24 missing names were added — including the
`stc1`-`stc15` cycle that the Stata 18+ default scheme uses, whose absence was the root cause
of stcolor rendering every series black. Additions cannot change existing output. No existing
entry was altered.

The 14 translated scheme files are **immune** to this bug: they carry resolved `#rrggbb` hex
rather than colour names, precisely so `_color()` cannot fall back.

## F8. Landmine tests corrected [RESOLVED]

Four tests asserted dash's old approximations rather than Stata's values, and so failed once
the schemes became faithful. Each new value was verified against
`/Applications/Stata/ado/base/` before the assertion was changed — not against dash's own
output, which would have been circular.

| test | asserted | Stata's value | derivation |
|---|---|---|---|
| `test_explicit_scheme_loaded` | sj p1 `#000000` | `#606060` | sj `#include`s s2mono; `color p1 gs6` -> `"96 96 96"` |
| `test_economist_inherits_from_s2color` | economist p1 `#1a476f` | `#3e647d` | economist `#include`s s2color then overrides: `color p1 edkblue` -> `"62 100 125"` |
| `test_economist_fill_alpha_is_0_9` | `0.9` | `0.8` | economist declares no `intensity`; inherits s2color `intensity p inten80` |
| `TestThemeKey.S2COLOR_BG` | `#d9e8f0` | `#eaf2f3` | `color background ltbluishgray` -> `"234 242 243"` (see F7) |

One test marked `xfail` pending S11 now passes and the marker was removed: adding all 14
names to `_BUILTIN_NAMES` makes the rejection message name the supported set.

## F9. Defects the scheme translations exposed in the translators [RESOLVED]

Faithful schemes use vocabulary dash could not express, and unlike `_color()` these raised
rather than degrading:

- **`translate_lpattern` knew 8 of Stata's 17 line patterns.** `vshortdash` — used by the
  st* family — raised straight out of `SchemeParser.__init__`. Added the 8 missing patterns.
- **`translate_msymbol` lacked `smdiamond` and `smtriangle`**, which all six mono schemes
  cycle through, so a faithful mono translation could not be parsed at all. Added those plus
  `smdiamond_hollow`, `smtriangle_hollow`, `smsquare_hollow`, `smplus`, `v`, `smv`, `lgx`.
- **`_lpattern()` raised where `_color()` swallowed.** Both now degrade *with a warning*.
  `_color()` warns only when a key is present-but-unresolvable; an absent key is ordinary
  scheme inheritance and stays silent.

---

# Addendum — batch 2 (2026-09-18)

## F10. The abbreviation table mis-routed EIGHT options, not five [RESOLVED]

Return codes alone are not enough to measure this: twoway *accepts* `xl()`, `t()` and `l()`
but resolves them to `xlabel()`, `t1title()` and `l1title()`. `scripts/extract_abbrev_truth.do`
therefore confirms each accepted prefix with a **resolution oracle** — it saves the probe to a
live-format `.gph`, normalises the per-run ids, and compares byte-for-byte against the full
option name.

| abbreviation | dash bound it to | twoway binds it to |
|---|---|---|
| `xl` | xline | **xlabel** |
| `yl` | yline | **ylabel** |
| `m` | marker (not a twoway option at all) | **msymbol** |
| `mlc` | mlabcolor | **mlcolor** |
| `mls` | mlabsize | **mlstyle** |
| `mlp` | mlabposition | **mlpattern** |
| `mlw` | mlabwidth | **mlwidth** |

`mlg` was *not* a mis-map: dash sent it to mlabgap, and twoway rejects `mlg` outright
(mlabgap's real minimum is `mlabg`). Twenty further abbreviations in dash's table are
rejected by twoway entirely.

## F11. Stata cannot express every abbreviation through capitalisation [WORKED AROUND]

`syntax` derives the minimum from the **leading run of capitals**, and a digit ends that run —
so `T1title` yields a minimum of `t1`, and no capitalisation of `t1title` yields `t`. twoway
nevertheless accepts `t()`, `b()`, `l()` and `r()`. Eleven further dash short forms
(`xla2`, `xsc2`, `xti2`, `yla2`, `ysc2`, `yti2`, `pbgc`, `bw`, `mlg`, `cv`, `colv`) are
**aliases rather than prefixes** and are equally inexpressible. All fifteen are declared as
their own options and folded onto the real local after `syntax`.

## F12. The saving() path validator rejected every Windows Program Files path [RESOLVED]

`_dash_validate_path` rejected `(` and `)` as shell metacharacters. Every `shell` call site
quotes the path (`shell open "``saving_path'"`), and inside double quotes those characters
are literal — so the rejection bought nothing and broke every path under
`C:\Program Files (x86)\`.

**A real hole was found next to it:** the double quote itself was **not** rejected, and that
character *would* terminate the quoted argument. Parentheses are now allowed and `"` is
rejected.

## F13. The skip sentinel collided with a real Stata return code [RESOLVED]

Batch 1 used `exit 111` to mark a skipped certification script. `r(111)` is Stata's own code
for the un-`tsset` case — which batch 2 then adopted for `dash tsline` to match twoway
exactly (verified: `twoway tsline mpg` on un-tsset data returns r(111), and rc=0 once tsset).
A genuine tsline failure would have been scored as a SKIP. The sentinel moved to **222**,
which is not a Stata return code.

## F14. The certification runner's quiet capture broke output-dependent checks [RESOLVED]

Scripts ran under bare `capture {...}`, which suppresses everything they display. Batch 1
already found this hid the `SKIP:` messages. It also breaks any check that verifies **dash's
own output** — the new unsupported-option note cannot be asserted if the note is suppressed,
which made `test_option_surface.cscript` pass standalone and fail inside the runner. The
runner now uses `capture noisily`.

Separately, a script that dies mid-scan leaks its `file open` handle, and `clear all` does not
close file handles; the runner now issues `capture file close _all` between scripts.

## F15. e2e_single joins the known e2e failures [OWNER: S16-03]

It previously reported SKIP. With the sentinel moved off 111 its guards no longer mask the
run, and it fails with `r(111) "Security not found"` — a line of generated HTML being parsed
as a Stata command. That is the **same** line-by-line HTML scan defect as F2, so the
certification suite now shows **6** e2e failures rather than 5. Nothing regressed; one more
instance of a known defect became visible.

## Batch 2 result

| suite | before | after |
|---|---|---|
| `test_abbreviations.cscript` | 371 checks failing | **all pass** |
| `test_option_surface.cscript` | 143 of 299 corpus commands abort | **all 299 run** |
| `test_varlist_expansion.cscript` | 13 checks failing | **all pass** |
| pytest | 1,610 passed / 5 failed | **1,615 passed / 0 failed** |
| certification runner | 5 passed / 5 failed / 1 skipped (of 11) | **8 passed / 6 failed / 0 skipped (of 14)** |
