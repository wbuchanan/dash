# Section Index — Phase 01: per-plot qualifiers on computed layers

## Overview

- **Total sections:** 10
- **Total tasks:** 51
- **Parallel batches:** 5
- **Scope:** the 10 work items of `phases/PHASE-01-*.md`, plus 4 additions approved in
  discovery and 3 decisions superseded by research.

## Batch execution order

### Batch 1 — foundation (must land first)
- **S01** Baseline and ground truth — `test/fixtures/`, `.ultraplan/BASELINE.md` **[green]**

### Batch 2 — parallel (three disjoint areas)
- **S02** The mask mechanism — twelve computed mappers — `dash_render.py` **[yellow]**
- **S04** Connected-topology layers — the NaN column — `dash_render.py` **[red]**
- **S08** Qualifier scoping — bar syntax and `by()` panels — `dash.ado`, `dash_parse.mata` **[yellow]**

### Batch 3 — parallel (all depend on S02's mechanism)
- **S03** `histogram` and `kdensity` — the two exceptions **[yellow]**
- **S05** Marker labels and colour range **[yellow]**
- **S07** Degenerate subsets, inline layers, and the warning surface **[yellow]**

### Batch 4 — parallel (depend on batches 2-3)
- **S06** Survival under interaction **[red]**
- **S09** Server-mode divergence — the failing parity test **[green]**

### Batch 5 — close-out
- **S10** Documentation, changelog and release **[green]**

## Section manifest

| # | Section | Risk | Batch | Depends on | Blocks | Tasks | Work items |
|---|---|---|---|---|---|---:|---|
| 01 | Baseline and ground truth | green | 1 | none | all | 4 | (addition) |
| 02 | The mask mechanism — twelve computed mappers | yellow | 2 | 01 | 03, 05, 06, 07, 09 | 7 | 1, 3 |
| 03 | `histogram` and `kdensity` | yellow | 3 | 01, 02 | 06 | 5 | 1 (part) |
| 04 | Connected-topology layers — the NaN column | red | 2 | 01 | 06 | 6 | 4 |
| 05 | Marker labels and colour range | yellow | 3 | 01, 02 | 06 | 5 | 8 |
| 06 | Survival under interaction | red | 4 | 02, 03, 04, 05 | 10 | 7 | 7, 9, 10 |
| 07 | Degenerate subsets, inline layers, warnings | yellow | 3 | 01, 02 | 10 | 5 | (additions) |
| 08 | Qualifier scoping — bar syntax and `by()` | yellow | 2 | 01 | 10 | 4 | (additions) |
| 09 | Server-mode divergence — the parity test | green | 4 | 02, 03 | 10 | 3 | 2, 5, 6 |
| 10 | Documentation, changelog and release | green | 5 | all | none | 5 | (additions) |

## Work-item coverage

Every one of the phase document's ten items maps to at least one section:

| item | title | section(s) |
|---|---|---|
| 1 | Make every computed glyph honour the per-plot view | **02**, 03 |
| 2 | Teach the generated `bokeh serve` app | **09** (test only — implementation deferred) |
| 3 | Fix computed layers under `link()` | **02** |
| 4 | Decide what a qualifier means for connected-topology glyphs | **04** |
| 5 | Correct the scope of the server-mode fix | **09** (test only) |
| 6 | The server-mode fix has three more paths | **09** (test only) |
| 7 | Register the INTERSECTED row set | **06** |
| 8 | Mask the `mlabel` `LabelSet` and the colour range | **05** |
| 9 | Make the per-plot view and the glyph's source agree | **06** |
| 10 | Give the browser-side aggregate recompute a row restriction | **06** |

## Additions beyond the ten items

Each was approved in discovery and is flagged for VALIDATE as a deliberate
task-beyond-requirement, not scope creep:

| addition | section | why |
|---|---|---|
| Re-measure the baseline before touching code | 01 | Q12 — no claim rests on a figure from the audit |
| Ground-truth fixture from Stata's own `regress` | 01 | Q4 — the 1e-6 assertion needs doubles, not serset floats |
| Uniform graceful policy for degenerate subsets | 07 | Q8 — Stata's own behaviour is inconsistent and undocumented |
| Validate-then-warn for `scatteri`/`pci`/`function` | 07 | Q6 refined by research §3.4 |
| Bar-syntax `||` scoping probe | 08 | S1 — Stata binds a trailing `if` to the last plot |
| `by()` panel survival | 08 | S2 — Stata deletes the panel; dash keeps it |
| Graph-level qualifier in the agg recompute | 06 | Q7 — same code path, would knowingly ship a defect |
| `dash.sthlp` per-plot-qualifier documentation | 10 | Q13 — discharges one Phase 30 item |
| CHANGELOG entry with before/after values | 10 | Q9 — users have seen the old numbers |
| Performance measurement on the largest example | 10 | Q14 — measure, do not cap |

## Decisions superseded by research

Recorded so no one implements the earlier answer:

| was | now | why | section |
|---|---|---|---|
| Private pre-filtered source for connected glyphs | **Per-layer NaN column on the shared source** | The private source draws straight across the gap, and loses `link()` and callback reach | 04 |
| Mask the `LabelSet` | **Replace with a filterable `text` glyph** | `LabelSet` has no `view` property in Bokeh 3.9 | 05 |
| (unspecified) colour range | **`LinearColorMapper` with `domain=[(renderer, col)]`** | Auto-ranging ignores the view; `linear_cmap` cannot auto-range at all | 05 |

## Two rules that apply to every section

1. **Test first** (project rule 8). The regression test must fail before the fix and pass
   after. Read the failure and confirm it is the *right* failure before writing code. For any
   test at risk of certifying nothing, state the mutation that must make it die.
2. **One commit per work item** (rules 6 and 7), on `feature/batch4-interactive-layer`, never
   on `main`, no AI references in the message. Report the merge command; do not run it.

## The trap that governs every test in this plan

Existing coverage is **scatter-only and structurally cannot catch this class of bug**.
`test/test_varlist_expansion.py:101`'s `_visible_count` helper reads
`renderer.view.filter.booleans` — which reports a *computed* layer as fully visible no matter
what it drew. **Assertions on computed layers must compare the layer's own source values
against an independently computed subsample**, never a view's booleans.
