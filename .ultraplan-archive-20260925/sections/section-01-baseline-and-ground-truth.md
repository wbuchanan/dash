# Section 01: Baseline and ground truth

## Overview

This section builds no product behaviour. It builds the two instruments every other section
of the phase measures itself against, and it lands before any of them.

The first is `.ultraplan/BASELINE.md` — today's verbatim pass / fail / skip counts for both
suites, at today's HEAD, in today's environment. The phase's own definition of done says
"both suites are green against the baseline measured at the start of the phase", and the
only number currently in circulation is the audit's `3,498 passed / 37 skipped` taken at
`ca5fe35`. `test/conftest.py:52` and `test/test_varlist_expansion.py:224` already cite this
document by name, and it is deleted from the working tree right now. Re-measure it, do not
inherit it (DISCOVERY Q12).

The second is `test/fixtures/stat_truth_qualifier.json` plus the raw rows it describes —
Stata's own `regress` doubles for every qualified subsample the phase asserts on, produced
by a committed probe script, not typed in by hand. Without it, BR-01.2's 1e-6 relative
assertion has nothing to assert against, and test bodies across sections 02-09 would each
hard-code a literal nobody can re-derive.

Two traps are encoded on purpose. `auto.dta` ships domestic-first, so `in 1/20` holds zero
foreign cars and `regress ... if foreign==1 in 1/20` is `r(2000)`; intersection tests must
use `in 1/60`. And sersets store `float`, so a coefficient recovered from a graph agrees
with `regress` only to ~1e-8 — the fixture carries the doubles and says so.

**TDD convention for this section: each task writes its own failing test first** and
confirms it fails for the right reason before producing what makes it pass.

## Risk: [green] — no product code is touched, but every later section's assertions inherit whatever this one gets wrong

## Dependencies
- Depends on: none
- Blocks: section-02, section-03, section-04, section-05, section-06, section-07, section-08, section-09, section-10
- Parallel batch: 1

## Evidence

### Why a measured baseline, and why it is not optional

`phases/PHASE-01-per-plot-qualifiers-on-computed-layers.md:1058-1063` sets the gate:

> - Full pytest suite green. The audit's HEAD baseline is **3,498 passed / 37
>   skipped**; this phase adds tests and must not subtract passes.
> - Full certification suite: **25/25 cscripts**, run with `arch -arm64` from
>   `test/` — and a skip is not a pass.

DISCOVERY Q12 answers "what baseline should the plan assume?" with *re-measure it as task
01*, and records the consequence: "every later claim is measured against a number taken
today, not the audit's `ca5fe35` figure (3,498 passed / 37 skipped / 25 cscripts). The
archived plan did this and it surfaced a stale-environment problem; repeating it is cheap
insurance."

The document is not inert. `test/conftest.py:57-70` pins the environment and warns on drift:

```python
_BASELINE_ENV = {
    "python": "3.14",       # major.minor only — patch drift is not interesting
    "bokeh": "3.9",
    "pandas": "3.0",
    "numpy": "2.4",
    "scipy": "1.17",
}
```

and `pinned_environment` (`test/conftest.py:73`) tells the developer to "See
.ultraplan/BASELINE.md" — a document that, measured today, `git status` reports as
` D .ultraplan/BASELINE.md`. The pointer is live and the target is gone.

`test/conftest.py:42-52` also records the fact that makes a single number insufficient:

```
#   pytest        /opt/homebrew/bin/python3.14
#   Stata's       /opt/anaconda3/bin/python3   (set python_exec)
#
# A green pytest run therefore does NOT prove the Stata path works
```

So both suites are measured, separately, and both go in the document.

### The ground-truth numbers (RESEARCH.md §3.1, full precision)

Measured on StataNow 19.5 MP (arm64), `sysuse auto` (N=74; foreign==1: 22, foreign==0: 52).

| quantity | `if foreign==1` | full sample |
|---|---|---|
| N | **22** | **74** |
| slope `_b[weight]` | **-.010425957587798849** | **-.0060086868119993289** |
| intercept `_b[_cons]` | **48.918297231743246** | **39.440283530717977** |
| slope, `%21x` | `-1.55a3456f3dfbfX-007` | `-1.89c9095975231X-008` |
| intercept, `%21x` | `+1.8758ac3812c1bX+005` | `+1.3b85b35f2b358X+005` |
| se(slope) | .0024941691063949203 | .00051787817670857252 |
| r2 | .46628963289838132 | .65153125290875114 |
| x-range of the drawn segment | **[1760, 3420]** | [1760, 4840] |

Companions, same source:

- `foreign==0` — N=52, slope `-.0059750835105182119`
- `in 1/60` — N=60, slope `-.0056974654861187985`
- `foreign==1 & weight>2500` — N=6, slope `-.0093656523981433745`
- `foreign==1 in 1/60` — N=8, slope `-.0096564106174751828`

### Trap (a) — `in 1/20` is not a usable intersection

RESEARCH.md §3.1 carries this verbatim warning:

> ⚠️ **Trap for the test author.** `auto.dta` ships sorted domestic-first, so foreign cars
> start at observation 53. So `in 1/20` contains **zero** foreign cars and
> `regress mpg weight if foreign==1 in 1/20` is `r(2000)`. Use `in 1/60` (N=8) for any
> intersection test.

The fixture therefore records `foreign1_in_1_20` as a return code, not a coefficient, so a
later section that reaches for it finds the reason instead of an empty result.

It follows that the row order of the exported data matters. RESEARCH.md §3.2 point 4:

> **`in` is absolute dataset observation numbers, never re-indexed into an outer
> subsample**, and it is sort-order dependent. The decisive case: if `in 1/60` were
> re-indexed within the 22 command-level rows it would select all 22 and give -.01042; it
> gives -.00965 instead.

### Trap (b) — sersets are float; assert against the `regress` doubles

RESEARCH.md §3, method caveat:

> Sersets store `float`, so coefficients recovered *from a graph* agree with `regress`
> doubles only to ~1e-8 relative. That is a storage artifact of the graph object, not of
> Stata's estimation. **Test assertions must use the `regress` doubles below, not
> serset-recovered values.**

RESEARCH.md §3.2 gives the serset-recovered figures beside the doubles, and the gap is
visible in the digits: `-.0060086866` vs `-.0060086868119993289`; `-.0104259571` vs
`-.010425957587798849`; `-.0093656528` vs `-.0093656523981433745`; `-.0096564116` vs
`-.0096564106174751828`. The fixture carries both, and names which one an assertion reads.

DISCOVERY Q4 fixes the tolerance at ~1e-6 relative and records why that is safe: "The
unqualified fit (slope -.00600869) fails by a factor of 1.7, so the bound is far from the
decision boundary."

### Per-layer semantics the fixture must be able to express (RESEARCH.md §3.2)

| command | layer 1 serset | `lfit` slope | equals `regress` on |
|---|---|---|---|
| `(scatter) (lfit)` | 74 obs | -.0060086866 | full sample |
| **`(scatter) (lfit … if foreign==1)`** | **74 obs** | **-.0104259571** | `if foreign==1` |
| `(scatter) (lfit) if foreign==1` | 22 obs | -.0104259571 | `if foreign==1` |
| `(scatter … if foreign==0) (lfit … if foreign==1)` | 52 obs | -.0104259571 | each its own |
| `(scatter) (lfit … if weight>2500) if foreign==1` | 22 obs | -.0093656528 | the **intersection**, N=6 |
| `(scatter) (lfit … if foreign==1) in 1/60` | 60 obs | -.0096564116 | intersection, N=8 |
| `(scatter) (lfit … in 1/60) if foreign==1` | 22 obs | -.0096564116 | intersection, N=8 |

The last two rows are identical, so **order does not matter** — the fixture stores both
keys so a later test can assert that rather than assume it.

### `by()` panels (RESEARCH.md §3.6) — an expansion of the brief, justified

The brief enumerates the whole-sample and companion subsamples. RESEARCH.md §3.6 measured
the same family of `regress` doubles per `by()` panel, and section 06 and section 08 assert
on exactly those numbers:

| panel | scatter | lfit | recovered slope | `regress … if rep78==k & foreign==1` |
|---|---|---|---|---|
| 1 | 2 obs (all panel rows) | **0 obs** | — | N=0 |
| 2 | 8 obs | **0 obs** | — | N=0 |
| 3 | 30 obs | 3 pts | -.015476189 | N=3, **-.0154761904761905** |
| 4 | 18 obs | 3 pts | -.005500296 | N=9, **-.0055002961792872** |
| 5 | 11 obs | 3 pts | -.019698354 | N=9, **-.0196983546617916** |

They are `regress` doubles on a qualified subsample, produced by the same probe, so they go
in the same fixture. This is recorded as a deliberate expansion of the brief's enumeration,
not a contradiction of it.

### What is deliberately NOT in this fixture

RESEARCH.md §3.3's degenerate-subset return-code table (`lfit`/`lfitci`/`lpoly`/`lpolyci`/
`kdensity` → rc 2001 and the whole graph aborts; `qfit`/`fpfit` → rc 0 and nothing drawn) is
a measurement of return codes, not of coefficients, and RESEARCH.md §4.4 records that dash
**does not reproduce it** — "keep the uniform graceful policy and document the divergence."
Encoding it here would invite a later section to assert Stata's behaviour as the target.
Section 07 owns it and probes it for itself.

### Supersessions that do not reach this section

RESEARCH.md §4 supersedes three discovery decisions — Q3 (connected topology: per-layer NaN
column, not a private source), item 8 marker labels (`figure.text`, not a masked `LabelSet`),
and item 8 colour range (`LinearColorMapper` with `domain=[(renderer, col)]`). **None of
them changes a ground-truth number**, so the fixture is unaffected. It is named here only so
nobody adds a "private source" or "LabelSet" key to the fixture on the strength of the older
decision text.

### The mechanical hazards this section has to get right

1. **`.git/info/exclude` silently drops the fixture.** The file carries `*.json` and `*.csv`
   under "Common ASCII dataset extensions". `test/test_fixtures_are_committed.py` exists
   because this has already happened: "174 tests do not run on a clone, and the suite still
   exits 0, because each of them skips politely when its fixture is missing." Both new
   fixture files must be added with `git add -f`.

2. **`test/fixtures/data/auto.csv` must not be extended.** It holds two columns
   (`mpg,weight`, 74 rows) and `test/test_statistical_truth.py:57` loads every file in that
   directory as `df = pd.read_csv(path).dropna()`. Adding a `rep78` column — which has five
   missing values in `auto.dta` — would silently drop five rows from the frame every existing
   `stat_truth.json` assertion is checked against. The qualifier data goes in a new file.

3. **`test/conftest.py:107`'s `auto_df` is synthetic.** It is `np.random.seed(42)` over
   `randint` ranges, not `auto.dta`. It cannot be used for a ground-truth assertion, and the
   fixture must carry real rows.

### The trap that governs every test this fixture will be read by

Existing coverage is scatter-only and **structurally cannot catch this class of bug**.
`test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans` and returns the full row count when the filter is
`AllIndices` or absent — which is exactly the state a *computed* layer is in, no matter what
it drew. **Assertions on computed layers must compare the layer's own source values against
an independently computed subsample**, never a view's booleans. That is the entire reason
this fixture carries `row_ids` per entry: so a later test can build the subsample itself.

## TDD test stubs

- Test: **`.ultraplan/BASELINE.md` is present and tracked by git.** Fails today — the file is
  deleted from the working tree. In `test/test_baseline_is_current.py` (new).
- Test: **the environment table in `BASELINE.md` equals `conftest._BASELINE_ENV` key for
  key.** In `test/test_baseline_is_current.py`. *Mutation that must kill it:* change `bokeh`
  to `3.8` in the document's table; the test must fail naming `bokeh`.
- Test: **the SHA `BASELINE.md` records is a commit that exists in this repository.** In
  `test/test_baseline_is_current.py`. *Mutation:* replace the SHA with 40 zeros; the test
  must fail.
- Test: **`test/fixtures/stat_truth_qualifier.json` and
  `test/fixtures/data/auto_qualifier.csv` exist.** Fails before the probe runs. In
  `test/test_qualifier_truth_fixture.py` (new). This module carries **no `skipif`** — a skip
  is not a pass, and a fixture-existence test that skips when the fixture is missing certifies
  nothing.
- Test: **every fixture file is tracked by git.** Already exists —
  `test/test_fixtures_are_committed.py::test_every_fixture_is_tracked_by_git` parametrises
  over the directory, so it fails for the two new paths until they are `git add -f`ed. Use
  that failure as the task's red state rather than writing a new one.
- Test: **each `regress` entry is reproduced by an independent numpy OLS over the entry's own
  `row_ids`, at rtol 1e-12.** In `test/test_qualifier_truth_fixture.py`. *Mutation:* truncate
  `regress.foreign1.b_weight` to `-0.0104259`; the `foreign1` case must fail.
- Test: **`in 1/20` contains no foreign car, and the fixture records `r(2000)` for it rather
  than a coefficient.** In `test/test_qualifier_truth_fixture.py`. *Mutation:* re-export the
  CSV sorted by `foreign`; the test must fail, because the whole trap is sort-order dependent.
- Test: **serset-recovered slopes agree with the `regress` doubles to better than 1e-7 and
  worse than 1e-12**, i.e. the serset really was read and really is float-limited. In
  `test/test_qualifier_truth_fixture.py`. *Mutation:* copy `regress.*.b_weight` into
  `serset.*.slope`; the lower bound must fail.
- Test: **the qualified and unqualified slopes differ by a factor of ~1.73, so the 1e-6
  tolerance is nowhere near the decision boundary** (DISCOVERY Q4). In
  `test/test_qualifier_truth_fixture.py`.
- Test: **`foreign1_in_1_60` and `in_1_60_foreign1` are identical in N, both coefficients and
  `row_ids`** (RESEARCH.md §3.2 point 3). In `test/test_qualifier_truth_fixture.py`.
- Test: **the three non-empty `by(rep78)` panels are reproduced by numpy OLS; the two empty
  ones record N 0 and carry no coefficients.** In `test/test_qualifier_truth_fixture.py`.

## Tasks

<task type="auto" id="01-01">
  <name>Re-measure both suites and restore .ultraplan/BASELINE.md</name>
  <files>test/test_baseline_is_current.py, .ultraplan/BASELINE.md</files>
  <action>
    Write the failing test first.

    1. Create `test/test_baseline_is_current.py`. It must contain no `skipif` of any kind.
       Module docstring: this document is cited by `test/conftest.py:52` and
       `test/test_varlist_expansion.py:224`, and DISCOVERY Q12 requires it to be re-measured
       at the start of the phase rather than inherited from the audit. Three tests:

       - `test_baseline_document_exists_and_is_tracked()` — assert
         `os.path.exists(<repo>/.ultraplan/BASELINE.md)`, then run
         `git -C <repo> ls-files --error-unmatch .ultraplan/BASELINE.md` with
         `subprocess.run(..., capture_output=True, text=True)` and assert `returncode == 0`.
         Resolve `<repo>` as `os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))`,
         the same way `test/test_fixtures_are_committed.py` does.
       - `test_baseline_environment_table_matches_conftest()` — `from conftest import
         _BASELINE_ENV` (add `sys.path.insert(0, _HERE)` first, as the other test modules do),
         parse the document's `## 3. Environment` markdown table into `{name: version}` by
         splitting each body row on `|` and taking the first two non-empty cells, then assert
         the parsed dict contains every key of `_BASELINE_ENV` with an equal value. Assert
         first that the parsed dict is non-empty, so a table that fails to parse cannot pass
         vacuously.
       - `test_baseline_records_a_commit_that_exists()` — read the line beginning
         `**Git SHA (HEAD):**`, extract the 40-hex token, and assert
         `git -C <repo> cat-file -e <sha>^{commit}` returns 0. Do not assert it equals current
         HEAD; later commits in this phase would break that.

    2. Run `/opt/homebrew/bin/python3.14 -m pytest test/test_baseline_is_current.py -q` and
       confirm **3 failed** — the document is deleted from the working tree, so the first test
       fails on `os.path.exists` and the other two on the missing file. Read the output and
       confirm that is the reason.

    3. Measure the pytest suite, verbatim:
       `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/ -q --no-header 2>&1 | tail -60`
       Keep the full `short test summary info` block and the headline line. Record the wall
       time. If the run is dominated by the `serve` marker, also record
       `-m 'not serve'` as a second, clearly-labelled measurement — never as a substitute.

    4. Measure the certification suite, verbatim:
       `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash/test && arch -arm64 /usr/local/bin/stata-mp -b do run_all_cscripts.do`
       then read `test/run_all_cscripts.log` and extract every `[ PASS]` / `[ FAIL]` /
       `[ SKIP]` line and the `Results: ... passed, ... failed, ... skipped (of ... total)`
       line. The runner already sets `global dash_nobrowser 1`, so nothing opens a browser;
       do not remove it. `arch -arm64` is mandatory — the runner's own header records that a
       long run was observed launching the x86_64 slice, after which every Python-dependent
       script fails on `incompatible architecture`.

    5. Write `.ultraplan/BASELINE.md` with these sections, all output pasted verbatim:
       - Header: date, repository path, branch (`feature/batch4-interactive-layer`),
         `**Git SHA (HEAD):**` on its own line, working-tree state, and the plan task id
         `01-01`.
       - `## 1. Python unit test suite (pytest)` — the command, the headline line, a
         passed/failed/skipped/warnings/errors/wall-time table, and the complete list of
         failing test ids if there are any.
       - `## 2. Stata certification suite` — the command, all 25 script result lines, and the
         `Results:` line. Name every SKIP and give its reason. State plainly that a skip is
         not a pass.
       - `## 3. Environment` — a markdown table whose first two columns are the package name
         and the version, with rows for `python`, `bokeh`, `pandas`, `numpy`, `scipy`, taken
         from the interpreter that ran step 3. Below it, record both interpreters by path:
         pytest `/opt/homebrew/bin/python3.14` and Stata's `/opt/anaconda3/bin/python3`, and
         restate `test/conftest.py:42-52`'s point that a green pytest run does not prove the
         Stata path works.
       - `## 4. Divergence from the audit figure` — the audit recorded 3,498 passed /
         37 skipped / 25 cscripts at `ca5fe35`. Record today's numbers beside it and explain
         any difference. Do not adopt a difference silently; if a test that passed at the
         audit now fails, say so and name it. Nothing in the rest of this phase may cite the
         audit figure once this file exists.

    6. Re-run the guard test; expect 3 passed.

    Do not touch any other file. No product code changes in this task.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_baseline_is_current.py -q` prints `3 passed`.
    `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash ls-files --error-unmatch .ultraplan/BASELINE.md` exits 0 and echoes the path.
    Mutation check: change `3.9` to `3.8` in the document's `## 3. Environment` table, re-run the
    same pytest command, and confirm it prints `1 failed` naming `bokeh`; then restore the value
    and confirm `git diff --stat .ultraplan/BASELINE.md` reports no change.
  </verify>
  <done>
    `.ultraplan/BASELINE.md` exists, is tracked, and carries today's verbatim counts for both
    suites plus the environment table, at a commit that exists in the repository.
    `test/test_baseline_is_current.py` is green and was demonstrated to fail before the
    document existed. Every later section compares against this file, not against `ca5fe35`.
  </done>
</task>

<task type="auto" id="01-02">
  <name>Write the Stata qualifier-truth probe and the guard test that fails without its output</name>
  <files>test/test_qualifier_truth_fixture.py, scripts/extract_qualifier_truth.do</files>
  <action>
    Write the failing test first.

    1. Create `test/test_qualifier_truth_fixture.py`. **No `skipif` anywhere in the module** —
       state that in the docstring, with the reason: the certification convention on this
       project is that a skip is not a pass, and `test/test_fixtures_are_committed.py`
       documents what a politely-skipping fixture test costs (174 tests that do not run on a
       clone while the suite still exits 0). Also put the `_visible_count` trap in the module
       docstring: `test/test_varlist_expansion.py:101` returns the full row count for any
       renderer whose filter is absent or `AllIndices`, which is every computed layer, so
       sections 02-09 read this fixture's `row_ids` and rebuild the subsample themselves
       rather than asking a view what it drew.

       Define `_HERE`, `_FIXTURE = test/fixtures/stat_truth_qualifier.json`,
       `_CSV = test/fixtures/data/auto_qualifier.csv`, and one test:
       `test_the_qualifier_fixture_exists()` asserting both paths exist, with an assertion
       message naming `scripts/extract_qualifier_truth.do` as the way to produce them.

    2. Run `/opt/homebrew/bin/python3.14 -m pytest test/test_qualifier_truth_fixture.py -q`
       and confirm it prints `1 failed`, not `1 skipped`, and that the failure names the
       missing fixture.

    3. Create `scripts/extract_qualifier_truth.do`, modelled on `scripts/extract_stat_truth.do`
       (1,485 lines) — same shape, a fraction of the size. Copy its proven mechanics rather
       than inventing new ones:

       - A `*!` header giving the purpose, both output paths, and the exact run command,
         including the scratch directory, because batch mode writes its `.log` to the process
         working directory (`extract_stat_truth.do:8-14`).
       - `clear all`, `set graphics off`, `set more off`, `global dash_nobrowser 1`.
       - `global ZQ_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"`,
         `global ZQ_OUT "${ZQ_REPO}/test/fixtures/stat_truth_qualifier.json"`,
         `global ZQ_CSV "${ZQ_REPO}/test/fixtures/data/auto_qualifier.csv"`, scratch under
         `c(tmpdir)`, and a record file.
       - The record-file helpers `zq_s` / `zq_n` / `zq_a` copied from
         `extract_stat_truth.do:79-99`: field separator `@@@`, numerics written with
         `string(z, "%20.17g")` so doubles round-trip, missing written as `null`.
       - Two constraints from that file's header that are not optional: a loop header must not
         contain `${...}` (copy globals into locals first, `extract_stat_truth.do:57-59`), and
         the trailing `python:` block must never call `SFIToolkit.stata()` (:51-55).

    4. Body of the probe:

       - `sysuse auto, clear`, then `gen long obs = _n` **before anything else**. Never issue
         `sort`. `auto.dta` ships domestic-first and RESEARCH.md §3.2 point 4 establishes that
         `in` is absolute and sort-order dependent; re-sorting silently destroys trap (a).
       - `export delimited make mpg weight price foreign rep78 length obs using "${ZQ_CSV}", replace nolabel`
         — `nolabel` is required or `foreign` exports as `Domestic`/`Foreign` instead of 0/1.
         `rep78`'s five missing values export as empty fields; that is correct and the Python
         loader must not `dropna()` them away.
       - A program `zq_reg` taking `key()`, optional `ifx()` and `inx()`. It runs
         `capture regress mpg weight `ifx' `inx''` and records, under section `regress`, key
         `key`: `cmd` (the command string verbatim), `qualifier_if`, `qualifier_in`, `rc`
         (`_rc`), and — only when `_rc==0` and `e(N)>0` — `N` (`e(N)`), `b_weight`
         (`_b[weight]`), `b_cons` (`_b[_cons]`), `b_weight_hex` and `b_cons_hex` (the same two
         written with `%21x`), `se_weight` (`_se[weight]`), `r2` (`e(r2)`), `x_min` / `x_max`
         (`summarize weight if e(sample)`, `r(min)` / `r(max)`), and `row_ids` — the `obs`
         values of the estimation sample, `;`-joined, recorded with `zq_a`.

       - Call it for these keys, exactly:

         | key | qualifier |
         |---|---|
         | `full` | (none) |
         | `foreign1` | `if foreign==1` |
         | `foreign0` | `if foreign==0` |
         | `in_1_60` | `in 1/60` |
         | `foreign1_weight2500` | `if foreign==1 & weight>2500` |
         | `foreign1_in_1_60` | `if foreign==1` + `in 1/60` |
         | `in_1_60_foreign1` | `in 1/60` + `if foreign==1` (arguments in the other order) |
         | `foreign1_in_1_20` | `if foreign==1` + `in 1/20` — **expected `rc` 2000** |
         | `rep78_1_foreign1` … `rep78_5_foreign1` | `if rep78==k & foreign==1` |

       - A serset cross-check block, using a `zq_serset` program copied in shape from
         `extract_stat_truth.do:145-187` (drop all graphs and sersets first, `graph use`,
         `serset set #`, `serset use, clear`, rename inside the same program because
         `__00000N` names are dropped when the program ends). For `full`, `foreign1`,
         `foreign1_weight2500` and `foreign1_in_1_60`: draw
         `twoway (scatter mpg weight) (lfit mpg weight <qualifier>)`, `graph save` in live
         format to the scratch directory, load the `lfit` serset, regress its points on each
         other, and record under section `serset`: `slope`, `intercept`, `n_points`, and
         `reldiff_slope` = `abs(slope - <regress b_weight>)/abs(<regress b_weight>)`.

       - A `by()` block: `twoway (scatter mpg weight) (lfit mpg weight if foreign==1), by(rep78)`
         is not needed to obtain the numbers — the panel coefficients are the `rep78_k_foreign1`
         regressions above. Record under section `by_panel` only the panel membership counts
         (`count if rep78==k`) so a later section can assert the scatter keeps all its panel
         rows while the fit uses the intersection.

    5. Trailing `python:` block: read the record file, split on `@@@`, coerce `null` to `None`
       and `row_ids`/array fields to lists, and assemble:

       ```
       {"_meta": {...}, "data": {...}, "regress": {...}, "serset": {...}, "by_panel": {...}}
       ```

       `_meta` carries `generated_by`, `run_date`, `stata_version` / `stata_edition`,
       `dataset: "auto"`, a `precision` note, `counts`, and two blocks that later sections
       read directly:

       - `"tolerance": {"assert_against": "regress_double", "rtol": 1e-6,
         "serset_float_agreement": 1e-8}` — DISCOVERY Q4's stated tolerance, in the fixture so
         it is written once and cited, not re-typed per test body.
       - `"self_checks": {"foreign_in_1_20_is_empty": <bool>,
         "max_serset_vs_regress_reldiff": <float>,
         "qualified_vs_unqualified_slope_ratio": <float>}`.

       `data` carries `{"file": "test/fixtures/data/auto_qualifier.csv", "n": 74,
       "columns": [...], "sha256": <hexdigest of the CSV>}`. Write with
       `json.dump(doc, fh, indent=2, sort_keys=True)` and a trailing newline, matching
       `extract_stat_truth.do`'s final block. Print `WROTE <path>` and every `_meta.counts`
       and `_meta.self_checks` entry so the run can be read from the log.

    6. Do not run the probe in this task and do not hand-write the JSON. Review the script,
       commit it with the still-red guard test, and stop.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_qualifier_truth_fixture.py -q` prints `1 failed` (not `1 skipped`), and the failure message names `scripts/extract_qualifier_truth.do`.
    `grep -c 'skipif' test/test_qualifier_truth_fixture.py` prints `0`.
    `grep -c 'SFIToolkit.stata' scripts/extract_qualifier_truth.do` prints `0`.
    `git status --porcelain` lists exactly the two files this task creates.
  </verify>
  <done>
    `scripts/extract_qualifier_truth.do` is committed and reviewed but has not been run.
    `test/test_qualifier_truth_fixture.py` fails for the right reason — the fixture it needs
    does not exist yet — and cannot ever pass by skipping.
  </done>
</task>

<task type="auto" id="01-03">
  <name>Run the probe and commit the fixture and its data with git add -f</name>
  <files>test/fixtures/stat_truth_qualifier.json, test/fixtures/data/auto_qualifier.csv</files>
  <action>
    1. Run the probe from a scratch directory, forcing the arm64 slice:

       ```
       mkdir -p /tmp/dash-qualifier && cd /tmp/dash-qualifier && \
       arch -arm64 /usr/local/bin/stata-mp -b do \
         /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_qualifier_truth.do
       ```

       Read `/tmp/dash-qualifier/extract_qualifier_truth.log` end to end. Confirm the `WROTE`
       line and every printed `counts` / `self_checks` value.

    2. Confirm the run reproduces RESEARCH.md §3.1 to the digit. These are the acceptance
       numbers; a mismatch means the run went wrong, not that the research was wrong:

       | key | N | `b_weight` | `b_cons` |
       |---|---:|---|---|
       | `full` | 74 | -.0060086868119993289 | 39.440283530717977 |
       | `foreign1` | 22 | -.010425957587798849 | 48.918297231743246 |
       | `foreign0` | 52 | -.0059750835105182119 | — |
       | `in_1_60` | 60 | -.0056974654861187985 | — |
       | `foreign1_weight2500` | 6 | -.0093656523981433745 | — |
       | `foreign1_in_1_60` | 8 | -.0096564106174751828 | — |
       | `in_1_60_foreign1` | 8 | -.0096564106174751828 | — |
       | `rep78_3_foreign1` | 3 | -.0154761904761905 | — |
       | `rep78_4_foreign1` | 9 | -.0055002961792872 | — |
       | `rep78_5_foreign1` | 9 | -.0196983546617916 | — |

       Also confirm `foreign1.x_min` is 1760 and `foreign1.x_max` is 3420, and that
       `full.x_max` is 4840 (RESEARCH.md §3.1's x-range row).

       **Nothing in this fixture may be typed by hand.** If a number disagrees, stop, report
       the disagreement with both values, and fix the probe — never the output.

    3. Confirm trap (a): `regress.foreign1_in_1_20` has `rc` 2000, has no `b_weight` key, and
       `_meta.self_checks.foreign_in_1_20_is_empty` is `true`.

    4. Confirm trap (b): `_meta.tolerance.rtol` is `1e-06`,
       `_meta.tolerance.assert_against` is `"regress_double"`, and
       `_meta.self_checks.max_serset_vs_regress_reldiff` is strictly greater than 0 and less
       than 1e-7. A value of exactly 0 means the serset was not actually read and the
       cross-check certified nothing.

    5. Confirm the CSV: 75 lines (header plus 74 rows); the `foreign` column holds `0`/`1`,
       not `Domestic`/`Foreign`; `rep78` has exactly 5 empty fields; the first data row is the
       AMC Concord; and rows 1-52 all have `foreign` 0, i.e. the domestic-first shipping order
       was preserved. That order is what makes trap (a) true.

    6. **Do not modify `test/fixtures/data/auto.csv`.** `test/test_statistical_truth.py:57`
       loads every file in `test/fixtures/data/` with `pd.read_csv(path).dropna()`; adding a
       `rep78` column to `auto.csv` would silently drop the five rows with missing `rep78`
       from the frame that every existing `stat_truth.json` assertion is checked against.

    7. Stage both files with `-f`:

       ```
       git add -f test/fixtures/stat_truth_qualifier.json test/fixtures/data/auto_qualifier.csv
       ```

       The `-f` is mandatory: `.git/info/exclude` carries `*.json` and `*.csv` under "Common
       ASCII dataset extensions". `test/test_fixtures_are_committed.py` exists because seven
       earlier fixtures needed `git add -f` and two did not get it.

    8. Commit on `feature/batch4-interactive-layer`. Never on `main` (project rule 6). No
       AI or vendor references in the message (rule 7). Report the merge command; do not run
       it.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_qualifier_truth_fixture.py test/test_fixtures_are_committed.py -q` prints `... passed` with 0 failed — the two new paths now satisfy `test_every_fixture_is_tracked_by_git`, which failed for them before the `git add -f`.
    `/opt/homebrew/bin/python3.14 -c "import json;d=json.load(open('test/fixtures/stat_truth_qualifier.json'));r=d['regress']['foreign1'];print(repr(r['b_weight']),repr(r['b_cons']),r['N'])"` prints `-0.010425957587798849 48.918297231743246 22`.
    `/opt/homebrew/bin/python3.14 -c "import json;d=json.load(open('test/fixtures/stat_truth_qualifier.json'));print(d['regress']['foreign1_in_1_20']['rc'], 'b_weight' in d['regress']['foreign1_in_1_20'])"` prints `2000 False`.
    `awk -F, 'NR>1 && NR<=53 && $6!=0' test/fixtures/data/auto_qualifier.csv | wc -l` prints `0` (adjust the field index to the exported column order).
  </verify>
  <done>
    Both fixture files were produced by a Stata run, match RESEARCH.md §3.1 digit for digit,
    encode both traps, and are tracked by git rather than existing only on this machine.
    `test/fixtures/data/auto.csv` is untouched.
  </done>
</task>

<task type="auto" id="01-04">
  <name>Prove the fixture against an independent recomputation, and pin both traps</name>
  <files>test/test_qualifier_truth_fixture.py</files>
  <action>
    Extend `test/test_qualifier_truth_fixture.py`. Keep the no-`skipif` rule. Add a module-level
    loader that reads the JSON once and reads the CSV with
    `pd.read_csv(_CSV)` and **no `dropna()`** — the five missing `rep78` values are data, and
    dropping them silently would change the `by()` panel row counts.

    Add an OLS helper that does not call into `dash_render`: given float64 arrays `x` and `y`,
    solve the two-parameter normal equations (or `numpy.polyfit(x, y, 1)`) and return
    `(slope, intercept)`. The point of this file is that it agrees with Stata **without**
    going through the code under test.

    Then add these tests.

    1. `test_every_regress_entry_is_reproduced_by_numpy_ols` — `pytest.mark.parametrize` over
       every key in `regress` that carries `b_weight`. Select the CSV rows whose `obs` value is
       in the entry's `row_ids`, assert `len(rows) == entry["N"]`, fit, and assert
       `math.isclose(slope, entry["b_weight"], rel_tol=1e-12)` and the same for the intercept.
       Include a `test_the_parametrisation_is_not_empty` guard asserting at least 9 keys were
       collected — a parametrisation over an empty list passes and proves nothing.

    2. `test_in_1_20_contains_no_foreign_car` — assert
       `df.sort_values("obs").head(20)["foreign"].sum() == 0`, and assert the fixture's
       `foreign1_in_1_20` entry has `rc == 2000` and no `b_weight`. Docstring: `auto.dta`
       ships domestic-first, foreign cars start at observation 53, so any intersection test in
       sections 02-09 uses `in 1/60` (N=8, slope -.0096564106174751828) and never `in 1/20`.

    3. `test_serset_values_are_float_limited_and_are_not_what_we_assert_on` — assert
       `0 < _meta["self_checks"]["max_serset_vs_regress_reldiff"] < 1e-7`, assert at least one
       `serset` entry's `reldiff_slope` exceeds 1e-12, and assert
       `_meta["tolerance"]["assert_against"] == "regress_double"`. Docstring: later sections
       read `regress.<key>.b_weight`; nothing reads `serset.<key>.slope` except this test.

    4. `test_the_tolerance_is_far_from_the_decision_boundary` — compute
       `abs(full.b_weight - foreign1.b_weight) / abs(foreign1.b_weight)`, assert it exceeds
       `0.4`, and assert `_meta["tolerance"]["rtol"] == 1e-6`. Docstring: DISCOVERY Q4 — the
       unqualified fit is wrong by a factor of about 1.73, so a 1e-6 relative bound cannot be
       satisfied by the wrong answer.

    5. `test_qualifier_order_does_not_matter` — assert `foreign1_in_1_60` and
       `in_1_60_foreign1` have equal `N`, equal `b_weight`, equal `b_cons` and equal `row_ids`
       (RESEARCH.md §3.2 point 3).

    6. `test_by_panel_entries_match_their_own_regression` — for `rep78_3_foreign1`,
       `rep78_4_foreign1`, `rep78_5_foreign1`, re-fit from the CSV as in test 1; for
       `rep78_1_foreign1` and `rep78_2_foreign1`, assert `N` is 0 (or `rc` is non-zero) and no
       coefficients are recorded. Assert the `by_panel` membership counts are 2, 8, 30, 18, 11
       for panels 1-5, which is what a later section's scatter must keep (RESEARCH.md §3.6).

    Then demonstrate the mutations, one at a time, restoring the fixture after each:

    - Truncate `regress.foreign1.b_weight` to `-0.0104259`; test 1's `foreign1` case must fail.
    - Copy `regress.full.b_weight` over `serset.full.slope`; test 3's lower bound must fail.
    - Reverse the CSV's row order; test 2 must fail.

    Record the three mutation results in the commit message. Restore the fixture and confirm
    `git diff --stat` is empty before committing.
  </action>
  <verify>
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/test_qualifier_truth_fixture.py -q` prints `N passed` with 0 failed and 0 skipped, where N is at least 15 (the existence test, the non-empty guard, five behaviour tests, and one parametrised case per `regress` key carrying coefficients).
    Mutation proof: `/opt/homebrew/bin/python3.14 -c "import json,io;p='test/fixtures/stat_truth_qualifier.json';d=json.load(open(p));d['regress']['foreign1']['b_weight']=-0.0104259;json.dump(d,open(p,'w'),indent=2,sort_keys=True)"` then the same pytest command prints `1 failed` naming `foreign1`; `git checkout -- test/fixtures/stat_truth_qualifier.json` then `git diff --stat` prints nothing and the suite is green again.
    `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && /opt/homebrew/bin/python3.14 -m pytest test/ -q --no-header 2>&1 | tail -3` shows the count from `.ultraplan/BASELINE.md` plus this section's new tests, with no new failures.
  </verify>
  <done>
    The fixture is self-validating: every coefficient in it is reproduced from the committed
    rows by an OLS that never touches `dash_render.py`, so a later section reading it is
    reading a number two independent computations agree on. Both traps are pinned by tests
    that were each shown to die under a named mutation. Sections 02-10 can now assert against
    `regress.<key>.b_weight` and rebuild any subsample from `row_ids` — which is the only
    form of assertion that works on a computed layer, because
    `test/test_varlist_expansion.py:101`'s `_visible_count` reports such a layer as fully
    visible no matter what it drew.
  </done>
</task>
