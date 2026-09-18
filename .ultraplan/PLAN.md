# Technical Plan — `dash` as a true drop-in replacement for `twoway`

## Architecture: unchanged, and deliberately so

The v2.0 decisions stay. Mata splits segments only. **Stata's `syntax` parses every option.**
JSON is assembled in Stata by string concatenation and escaped through `_dash_json_str`.
`jsonio` carries the data and is not modified. Python builds Bokeh models.

Three architectural changes are in scope, and only three:

1. **The abbreviation table is deleted.** `dash.ado` currently declares every option in
   lowercase — which disables Stata's own abbreviation — and simulates abbreviation with a
   fixed exact-match table in Mata (`dash_parse.mata:179-253`). Capitalising the minimum
   abbreviation in the `syntax` declarations, the way every StataCorp command does, fixes
   ~25 broken abbreviations and removes 5 silent mis-mappings in one change, and deletes
   ~80 lines of Mata.
2. **A `formats` map is added to the master JSON.** `jsonio` has no option that emits Stata
   display formats — verified in its source and by `javap` on the shipped jar. `dash.ado`
   collects `local f : format <var>` itself and carries the map. This is the only way dates
   and numeric formats can reach Python.
3. **Server mode stops being a second implementation.** 107 implementations currently cover
   38 behaviours. The generated app will call into shared functions instead of re-deriving
   them in generated string literals.

## Tech stack

StataNow 19.5 (forced to its arm64 slice on this machine) · `jsonio`, unmodified ·
Python 3.14.5 · Bokeh 3.9.0 · pandas 3.0.1 · numpy 2.4.3 · scipy 1.17.1 · statsmodels
(currently broken here — S01 fixes the guard, not the install) · Bootstrap, inlined.

## The four decisions that bind this plan

1. **Schemes are translated, not parsed from Stata.** `dash` keeps its own `schemes/`
   directory. The translated set widens to the StataCorp schemes users actually have set, the
   translations deepen until they faithfully reproduce the Stata aesthetic, and `scheme()` is
   **restricted** to the translated set with a clear error naming the supported names — never
   a silent fallback to black or to `s2color`.
2. **Defaults change to match Stata.** Matching `twoway` is the definition of correct. Every
   altered default gets a changelog entry and a migration note.
3. **Server mode: fix the root bug, then unify.**
4. **Unsupported options are accepted and reported together** — one note per command listing
   every unsupported option that command used. Never an abort, never silence.

## Section index

See `sections/index.md`. **16 sections, 89 tasks, 6 batches.**

## Dependency graph

```
Batch 1  (parallel — no shared files)
  S01 Baseline, environment, test integrity
  S02 Packaging: make net install work
  S03 Scheme translation: author the .scheme files

Batch 2  (sequential — all edit dash.ado / dash_parse.mata)
  S04 Abbreviations via Stata syntax
   -> S05 Open the option surface + unsupported-option reporting
   -> S06 Varlist and plot-spec correctness

Batch 3  (sequential — all edit dash_render.py)
  S07 Statistical defaults from the data and c(level)
   -> S08 Display formats, dates and labels
   -> S09 Axes, legend, titles, reference lines
   -> S10 Figure geometry and layout sizing

Batch 4  (sequential — all edit dash_render.py)
  S11 Scheme consumption and fidelity
   -> S12 Layout, tabs and faceting correctness
   -> S13 Linking, filters and KPI correctness

Batch 5  (sequential — server)
  S14 Server mode: root fix and option pass-through
   -> S15 Server/standalone unification

Batch 6
  S16 Help reconciliation, conformance suite, security and release
```

## A note on parallelism, stated honestly

Only batch 1 is genuinely parallel. S01 touches `test/`, S02 touches `dash.pkg` and one
`except` clause, S03 touches `schemes/` — three disjoint file sets.

Everything after that is sequential, not because the work is logically dependent but because
**S04-S06 all edit `dash.ado` and `dash_parse.mata`, and S07-S15 all edit `dash_render.py`.**
Running them concurrently produces conflicting edits to two files. Do not be tempted to
parallelise S07-S10 — they are independent in intent, not in file.

There is one real logical dependency worth naming: **S05 gates batches 3 and 4.** An option
that Stata's `syntax` rejects can never reach the renderer, so there is no point implementing
`bin()` in `map_histogram` before `bin()` is accepted.

## Working rules for every section

1. **Test first.** Project rule 8: every defect gets a regression test that **fails before
   the fix and passes after**. Demonstrate the failure before writing the fix. A task is not
   done until the failure output has been read and confirmed to be the right failure.
2. **One commit per fix**, on a single feature branch off `main`, single-issue style, message
   in the imperative, **no mention of AI tooling** (rule 7). Never commit to `main` (rule 6).
   The merge command is reported at the end, not run.
3. **Full suite after every section**, compared against the S01 baseline (rule 5). The suite
   must be green before any commit.
4. **Every behaviour change to existing output is recorded** in a running `CHANGELOG` section,
   with the before and after values.
5. **Verify end to end through Stata**, not just through pytest. Structural assertions on
   generated HTML are necessary but not sufficient for anything the user looks at.

## Environment contract (established in S01, assumed thereafter)

```stata
clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
dash clear
```

`adopath ++` prepends; `+` appends and lets an installed copy in `PLUS/d/` shadow the
development tree. `dash.ado`'s Mata-load block runs once at file-load time, so set the path
**before** the first `dash` call or `discard` afterwards.

```bash
arch -arm64 /usr/local/bin/stata-mp -b do <file>.do     # required on this machine
```

Launched without `arch -arm64`, Stata runs its x86_64 slice and fails to load the arm64
`libpython3.13.dylib` with r(7100). Stata's `python_exec` is `/opt/anaconda3/bin/python3`
(3.13.9); the pytest suite runs `/opt/homebrew/bin/python3.14`. **These are different
interpreters with different library versions.** S01 pins and verifies both.

## Measured baseline

```
python3 -m pytest test/ -q   ->   1,480 passed, 14 failed
```

All 14 are `lowess` tests failing on an unguarded `statsmodels` import
(`dash_render.py:2547`). The suite is RED, which project rule 5 forbids committing over.
S01 fixes the guard and re-establishes green.

## Review notes

_(populated by Phase 4)_

---

# Review Notes

**Review date:** 2026-09-18

## Self-review results
- Issues found: **9**
- Auto-fixed: **7**
- Escalated to the user: **4** (answered before the plan was written — see PLAN's
  "four decisions that bind this plan")
- Flagged and accepted: **2**

## Category results

| # | Category | Result |
|---|---|---|
| 1 | Completeness | **WARN** — 6 research findings had no owning section. All 6 auto-fixed. |
| 2 | Consistency | **WARN** — the task total in `index.md` and `PLAN.md` disagreed with the section files. Auto-fixed (84 → 89). |
| 3 | Feasibility | **WARN** — S15 is disproportionately large. Flagged, not fixed; see below. |
| 4 | Security | pass — S13-05, S14-05 and S16-04 cover every input surface, and S16-04 explicitly re-enumerates the surface *after* the plan's changes rather than reusing the current list. |
| 5 | Scalability | pass — the one growth risk (per-row identifiers on every source, S13-03) is called out with a size constraint in the task itself. |
| 6 | Edge cases | pass — minimum-N guards, all-missing columns, Stata's date range exceeding pandas', degenerate ranges and sentinel collisions are all carried into named tasks. |
| 7 | User experience | pass — the accept-and-report note, the migration section, and three separate "look at it in a browser" verification steps (S08-06, S10-04, S11-06, S12-05). |
| 8 | Cost & complexity | **WARN** — 89 tasks is a large plan. Flagged; the batching makes it stoppable at several points. |

## The six completeness gaps, and where they went

Each was a finding in `RESEARCH.md` with no task claiming it:

| Finding | Now owned by |
|---|---|
| Dashboard title/subtitle **double HTML-escaped** in the Bootstrap path (`:7518-7519` vs `:6551`, `:6555`) | S09-07 |
| Graph and axis titles `html.escape`d but drawn as **canvas text** (`:5638`, `:5610-5611`) | S09-07 |
| `hover()` read at `:6063` and `:4940` but **absent from `dash.ado`** | S09-07 |
| Secondary-axis range computed from the **unfiltered** frame (`:5729`, `:5764`) | S09-07 |
| `mlabel()` on `line` plots uses the **unsorted** source (`:2014`, `:2030`) | S09-07 |
| `dash build` has **no `nobrowser`**, and no `_rc` check after any of six `shell` calls | S14-04 |

## Two things flagged rather than fixed

**S15 (server/standalone unification) is the largest single item in the plan** — collapsing
107 implementations of 38 behaviours in a 10,455-line file, in the half with the thinnest
test coverage. It is sequenced last among the code sections precisely so it can be deferred:
S14 alone makes server mode work and honour its options. If the effort has to be cut, cutting
S15 leaves a working package with a known maintenance burden, whereas cutting anything earlier
leaves a broken one. The cost of deferring is that every future parity fix must be written
twice.

**89 tasks is a lot.** It is not padded — it is the number of distinct defects the audit found
— but the batch structure gives four natural stopping points, each leaving the package in a
better and self-consistent state:

| Stop after | What the user gets |
|---|---|
| Batch 1 (S01-S03) | The package **installs and works** at all, and the test suite can fail honestly. This is the minimum defensible release. |
| Batch 2 (S04-S06) | Pasted `twoway` syntax **runs**. No aborts, no silently dropped series. The drop-in claim becomes true at the syntax level. |
| Batch 3 (S07-S10) | The **numbers and proportions** match Stata. |
| Batch 4 (S11-S13) | It **looks** like Stata, and the interactive layer is correct. |
| Batch 5-6 | Server mode works and everything is documented and proved. |

## Refinement questions asked and answered
Four decisions were put to the user before the plan was written. All four are recorded in
`RESEARCH.md` §10 and bind the sections: scheme strategy (translate the widely-used StataCorp
schemes and restrict `scheme()` to that set), breaking changes (match Stata), server mode
(fix the root bug then unify), and unsupported options (accept, never abort, and report them
together in one note per command).

## Sections modified during review
`section-09-axes-legend-titles.md` (new task 09-07, five register rows, five test stubs);
`section-14-server-root-fix.md` (task 14-04 extended, two test stubs);
`sections/index.md` and `PLAN.md` (task counts corrected).
