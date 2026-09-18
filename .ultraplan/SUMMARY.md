# UltraPlan Summary — `dash` as a true drop-in replacement for `twoway`

## What we're building

Not a new feature. A closing of the distance between what `dash` says it does and what it
does. `dash` already turns `twoway` syntax into interactive HTML dashboards; its abstract
promises *"just replace twoway with dash and you can be on your way."* This plan makes that
sentence true.

Three things change. Every `twoway` command that works in Stata will work in `dash` instead
of stopping the do-file. Every option `dash` accepts will either take effect or say out loud
that it cannot. And the values that decide how a chart looks and what it computes will come
from the user's command, their data and their Stata scheme, rather than from literals in the
source.

## The five findings that justify the effort

1. **`net install` is broken.** `dash.pkg` omits `schemes/`, and the code that should recover
   from a missing scheme raises the same error a second time, uncaught. Installed the
   advertised way, **every `dash` command ends in a Python traceback**. Reproduced by staging
   exactly the six declared files. It works on the author's machine only because the
   development tree has the directory.
2. **`bokeh serve` serves an empty document.** The generated app binds its document inside
   `if __name__ == '__main__':`, and Bokeh runs app scripts under a synthetic module name, so
   the guard is always false. `docs_json` is literally `{}`; `/health` is 404. 448 server
   tests pass because every one of them calls `make_document` directly.
3. **37 of 59 ordinary `twoway` commands abort.** Including `xsize()`, `sort`, `bin()`,
   `level()`, `percent`, and the everyday abbreviations `mlab()`, `msym()`, `xlab()`,
   `mcol()`. The help states that unknown options produce no error. They produce `r(198)`.
4. **Work disappears silently.** `dash scatter mpg price weight` draws one series where
   `twoway` draws two. `layout(bs)` combined with `by()` deletes the faceted graph from the
   dashboard entirely — the abstract's headline feature and core `twoway` syntax, and using
   both loses one.
5. **The numbers are not Stata's numbers.** A histogram is always 10 bars; Stata gives 8 for
   `auto`/`mpg` and 33 for `nlsw88`/`wage`. Every confidence band is 95% with no `level()`.
   Every `twoway function` is drawn over x ∈ [0,1]. And `stcolor` — the default scheme since
   Stata 18, and the active scheme on this machine — renders **every series black**.

## Scale

**118 distinct defect classes. 211 hardcoded values, 73 of them HIGH. 16 sections, 89 tasks,
6 batches.** Every finding is cited to `file:line`; the ones marked *measured* were
reproduced by running the software against live StataNow 19.5.

## The four decisions that shaped the plan

1. **Schemes are translated, not parsed.** `dash` keeps its own `schemes/` directory; the set
   widens to the fourteen most-used StataCorp schemes, the translations deepen until they
   faithfully reproduce the Stata aesthetic, and `scheme()` is restricted to that set with a
   clear error rather than a silent fallback.
2. **Defaults change to match Stata.** Matching `twoway` is the definition of correct. Every
   altered default gets a changelog entry and a migration note.
3. **Server mode: fix the root bug, then unify.** The generated app currently implements 38
   behaviours 107 times and has already drifted visibly.
4. **Unsupported options are accepted and reported together** — one note per command listing
   every unsupported option it used. Never an abort, never silence.

## Risk areas

- **[red] S15 — unification.** Collapsing 107 implementations in a 10,455-line file, in the
  half with the thinnest coverage. Sequenced last so it can be deferred; S14 alone makes
  server mode work.
- **[red] S11 — scheme consumption.** Changes the appearance of every chart the package has
  ever produced, and a wrong colour is the hardest thing to notice.
- **[red] S08 — dates and formats.** Touches `_load_data` and `_make_figure`, which every
  code path depends on.
- **[red] S05 / S06 — the syntax gate.** Changes what every command accepts, and reshapes the
  spec for a very common input.
- **[yellow] The environment.** `statsmodels` is broken here; Stata's Python and the test
  suite's Python are different interpreters; Stata must be forced to its arm64 slice
  (`arch -arm64`) for `dash build` to run at all.

## Structure

```
Batch 1  S01 Baseline/tests || S02 Packaging || S03 Scheme translation    <- parallel
Batch 2  S04 -> S05 -> S06        (dash.ado / dash_parse.mata)
Batch 3  S07 -> S08 -> S09 -> S10 (dash_render.py)
Batch 4  S11 -> S12 -> S13        (dash_render.py)
Batch 5  S14 -> S15               (server)
Batch 6  S16                      (docs, conformance, security, release)
```

Only batch 1 is genuinely parallel — the rest share two files. The one real logical gate is
**S05 blocking batches 3 and 4**: an option Stata's `syntax` rejects can never reach the
renderer.

## Four places you can stop

Each leaves the package better and self-consistent:

| Stop after | What the user gets |
|---|---|
| **Batch 1** | The package **installs and works** at all, and the test suite can fail honestly. The minimum defensible release. |
| **Batch 2** | Pasted `twoway` syntax **runs**. No aborts, no dropped series. |
| **Batch 3** | The **numbers and proportions** match Stata. |
| **Batch 4** | It **looks** like Stata, and the interactive layer is correct. |

## The cross-cutting deliverable

A **conformance suite** — a corpus of real `twoway` commands run through `dash`, asserting no
`r(198)`, no dropped series, no dropped graph, and agreement with Stata's own computed values
for the statistical layers. Grown from S05 onward, formalised in S16. It is the artifact that
*proves* the drop-in claim instead of asserting it, and it is what stops all 118 findings
coming back.

## Relationship to the conference plan

`/Users/billy/Desktop/Programs/JavaScript/stataConference2026/.ultraplan/` contains a
completed plan for the 2026 talk whose sections 02-09 fix `dash` defects. This plan is a
**superset** of that work: it adopts the date support, silent-failure and server sections by
reference and adds the three dimensions a demo did not need — systematic `twoway` surface
parity, the hardcoding inventory as a first-class deliverable, and the scheme pipeline.

Its `DASH_AUDIT.md` remains a useful reference, with two corrections this round established:
`by()` + `link()` is **not** forbidden by the code (only by the stale help), and `timeout()`'s
units were already fixed.

## How to execute

1. Share the `.ultraplan/` folder with any AI coding tool.
2. Say: "Read `.ultraplan/sections/index.md` and execute section 1."
3. S01, S02 and S03 can run in parallel. Everything after is sequential.
4. After each section: "Execute section [next]."

Every section is test-first (project rule 8), commits to a feature branch (rule 6), and runs
the full suite against the S01 baseline before committing (rule 5).

## How to update

Run `/ultraplan update` and describe what changed — only affected sections are regenerated.
