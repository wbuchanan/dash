# Section Index

## Overview
- Total sections: **16**
- Total tasks: **89**
- Batches: **6** (only batch 1 is genuinely parallel — see the note below)

## Batch execution order

### Batch 1 — parallel (three disjoint file sets)
- S01: Baseline, environment and test-suite integrity — `test/` [yellow]
- S02: Packaging — make `net install` work — `dash.pkg`, one `except` clause [green]
- S03: Scheme translation — author the translated `.scheme` files — `schemes/` [yellow]

### Batch 2 — sequential (all edit `dash.ado` / `dash_parse.mata`)
- S04: Abbreviations via Stata's own `syntax` [yellow]
- S05: Open the option surface + unsupported-option reporting [red]
- S06: Varlist and plot-spec correctness [red]

### Batch 3 — sequential (all edit `dash_render.py`)
- S07: Statistical defaults from the data and `c(level)` [yellow]
- S08: Display formats, dates and labels [red]
- S09: Axes, legend, titles and reference lines [yellow]
- S10: Figure geometry and layout sizing [yellow]

### Batch 4 — sequential (all edit `dash_render.py`)
- S11: Scheme consumption and fidelity [red]
- S12: Layout, tabs and faceting correctness [yellow]
- S13: Linking, filters and KPI correctness [yellow]

### Batch 5 — sequential (server)
- S14: Server mode — root fix and option pass-through [red]
- S15: Server/standalone unification [red]

### Batch 6
- S16: Help reconciliation, conformance suite, security and release [yellow]

## Section manifest

| # | Section | Risk | Batch | Depends on | Blocks | Tasks |
|---|---|---|---|---|---|---|
| 01 | Baseline, environment, test integrity | yellow | 1 | none | all | 6 |
| 02 | Packaging: `net install` | green | 1 | none | 16 | 4 |
| 03 | Scheme translation | yellow | 1 | none | 11 | 5 |
| 04 | Abbreviations via Stata `syntax` | yellow | 2 | 01 | 05 | 5 |
| 05 | Open the option surface | red | 2 | 04 | 06-13 | 6 |
| 06 | Varlist and plot-spec correctness | red | 2 | 05 | 07 | 7 |
| 07 | Statistical defaults from data | yellow | 3 | 06 | 08 | 6 |
| 08 | Display formats, dates, labels | red | 3 | 07 | 09 | 6 |
| 09 | Axes, legend, titles, reference lines | yellow | 3 | 08 | 10 | 7 |
| 10 | Figure geometry and layout sizing | yellow | 3 | 09 | 11 | 4 |
| 11 | Scheme consumption and fidelity | red | 4 | 03, 10 | 12 | 6 |
| 12 | Layout, tabs, faceting correctness | yellow | 4 | 11 | 13 | 5 |
| 13 | Linking, filters, KPI correctness | yellow | 4 | 12 | 14 | 6 |
| 14 | Server: root fix + option pass-through | red | 5 | 13 | 15 | 5 |
| 15 | Server/standalone unification | red | 5 | 14 | 16 | 4 |
| 16 | Help, conformance, security, release | yellow | 6 | 15 | none | 7 |

## Why almost nothing is parallel

S04-S06 all edit `dash.ado` and `dash_parse.mata`. S07-S15 all edit `dash_render.py`
(10,455 lines). Running any of them concurrently produces conflicting edits to the same
file. They are independent in **intent**, not in **file**. Only batch 1 has disjoint file
sets.

The one genuine logical gate: **S05 blocks batches 3 and 4.** An option that Stata's
`syntax` rejects can never reach the renderer, so implementing `bin()` inside
`map_histogram` before `bin()` is accepted accomplishes nothing.

## Two rules that apply to every section

1. **Test first** (project rule 8). The regression test must fail before the fix and pass
   after. Read the failure output and confirm it is the right failure before writing code.
2. **One commit per fix**, on a feature branch off `main`, no AI-tooling references
   (rule 7), never on `main` (rule 6). Report the merge command; do not run it.

## Cross-cutting deliverable

A **conformance suite** (built in S16, but grown incrementally from S05 onward): a corpus of
real `twoway` commands run through `dash`, asserting (a) no `r(198)`, (b) no silently dropped
series, (c) no silently dropped graph, and (d) for the statistical layers, agreement with
Stata's own computed values. This is the artifact that proves the drop-in claim rather than
asserting it.
