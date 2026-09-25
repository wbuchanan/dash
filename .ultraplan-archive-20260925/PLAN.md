# Technical Plan — Phase 01: per-plot qualifiers on computed layers

**Target:** `dash` · branch `feature/batch4-interactive-layer` · base `187a786`
**Scope:** the 10 work items of `phases/PHASE-01-per-plot-qualifiers-on-computed-layers.md`,
plus 10 additions approved in discovery, minus 3 decisions superseded by research.
**Shape:** 10 sections · 51 tasks · 5 batches.

---

## Architecture overview

### Where the defect lives

`dash` renders a dashboard from a master spec JSON that `dash.ado` builds. Each graph owns one
shared `ColumnDataSource`; each plot layer draws from it. A per-plot qualifier arrives as
`if_expr` / `in_expr` on the plot dict and is turned, at `dash_render.py:9951-9998`, into a
`CDSView` + `BooleanFilter` over that shared source.

That mechanism restricts **which rows of the shared source a glyph draws**. It is correct for
marker and bar glyphs and it is structurally invisible to anything else:

```
                         spec JSON  (if_expr per plot — dash.ado:1240,1244)
                              │
                   _make_figure_body :9951-9998
                              │
                     _mask  :9979   ← facet_mask AND qualifier_mask
                              │
                  CDSView(BooleanFilter(_mask))
                              │
        ┌─────────────────────┼──────────────────────────────┐
        │                     │                              │
   marker/bar glyph      Line / Patch                 computed layer
   ✅ honoured           ❌ E-1024, draws              ❌ builds its OWN source
                            nothing or partial            from the unfiltered frame
```

### The three mechanisms this plan installs

| layer kind | mechanism | why |
|---|---|---|
| marker, bar, segment, **VArea** | keep `CDSView` + `BooleanFilter` | measured correct in Bokeh 3.9 |
| computed (14 types) | **`row_mask=` kwarg**, ANDed into the NaN mask the mapper already builds | the layer must be *recomputed* on the subset; filtering its output is meaningless |
| connected (`Line`, `Patch`) | **per-layer NaN column on the shared source** | a `CDSView` on a Line draws correctly only for a contiguous prefix; a private source draws across the gap and leaves `link()` |

Two auxiliary mechanisms, both replacing a superseded answer:

- **Marker labels** move from `LabelSet` (which has no `view` property at all) to
  `figure.text(..., view=...)`, a real filterable `GlyphRenderer`.
- **Colour range** moves to `LinearColorMapper(palette=...)` with
  `domain=[(renderer, column)]` — the only construct measured to follow a `CDSView`.

### Three identity spaces, and where they meet

This is the part that makes item 7, item 9 and item 10 subtle. Three row-identity spaces
coexist:

1. **`self.df` ordinal position** — what `_row_ids_for` (:8574) returns and what
   `__dash_row__` (:591) carries.
2. **Source position** — what a `BooleanFilter.booleans` array indexes.
3. **Kept-row position after a filter callback** — what the JS rebuild at :7169 produces.

The JS rebuild is a *total replacement* computed from `member_ids`, so whatever is registered
at render time is the only thing that survives a widget move. Register the qualifier's rows
alone and the facet restriction is silently discarded (item 7). Register against the shared
source while the glyph draws from a jittered copy and the mask lands on the wrong rows
(item 9). Give the browser-side aggregate recompute no row list at all and it recomputes from
the widget selection only (item 10).

---

## Tech stack

Unchanged by this phase — no new dependency is introduced.

| layer | technology | relevant version facts |
|---|---|---|
| Stata side | ado + Mata | `syntax`, `sreturn`; `dash.ado:1496` promotes a qualifier when `n_segs == 1` |
| Renderer | Python 3.14 | `dash_render.py`, 16,264 lines, two renderers |
| Plotting | **Bokeh 3.9.0** | `ConnectedXYGlyph` has exactly two subclasses (`Line`, `Patch`); `LabelSet` has no `view`; `linear_cmap` cannot auto-range |
| Data | pandas 3.0.1 / numpy 2.4.3 | `df.query(engine="python")` after AST validation |
| Tests | pytest (82 modules) + 25 `.cscript` | Stata invoked as `arch -arm64 /usr/local/bin/stata-mp -b do` |

---

## Dependency graph

```
                         ┌──────────────────────────┐
                         │ S01 Baseline & ground    │  batch 1
                         │     truth        [green] │
                         └────────────┬─────────────┘
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
   │ S02 Mask mechanism │  │ S04 NaN column     │  │ S08 Qualifier      │  batch 2
   │  12 mappers [yel]  │  │  connected  [red]  │  │  scoping    [yel]  │
   └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘
      ┌──────┼──────┬───────────┐    │                       │
      ▼      ▼      ▼           │    │                       │
  ┌───────┐┌──────┐┌─────────┐  │    │                       │
  │S03    ││S05   ││S07      │  │    │                       │  batch 3
  │hist & ││labels││degenerate│ │    │                       │
  │kdens  ││&     ││& warnings│ │    │                       │
  │[yel]  ││colour││  [yel]   │ │    │                       │
  └───┬───┘└──┬───┘└────┬─────┘ │    │                       │
      │       │         │       │    │                       │
      └───┬───┴─────────┼───────┴────┘                       │
          ▼             │                                    │
   ┌────────────────┐   │   ┌────────────────────┐           │
   │ S06 Survival   │   │   │ S09 Server         │           │  batch 4
   │ under          │   │   │  divergence [green]│           │
   │ interaction    │   │   │  (failing test)    │           │
   │        [red]   │   │   └─────────┬──────────┘           │
   └────────┬───────┘   │             │                      │
            └───────────┴─────────────┴──────────────────────┘
                                      ▼
                        ┌──────────────────────────┐
                        │ S10 Docs, changelog,     │  batch 5
                        │     release      [green] │
                        └──────────────────────────┘
```

### Why the order is what it is

- **S01 first, always.** Project rule 5 and discovery Q12: no claim in this plan rests on a
  figure taken from the audit rather than from today. It also produces the ground-truth
  fixture every later assertion reads.
- **S02 is the mechanism everything reuses.** S03 is the same idea applied to the two mappers
  where `_extract_finite` breaks positional correspondence; S05 and S07 both need a mask to
  exist before they can mask anything.
- **S04 and S08 are genuinely independent of S02.** S04 installs a different mechanism
  (NaN columns) for a disjoint set of layer types; S08 touches only `dash.ado` /
  `dash_parse.mata`. All three can run in parallel.
- **S06 is last of the code sections** because it is the "wrong after the first interaction"
  work and it needs every first-paint mechanism to exist before it can keep them true.
- **S09 is deliberately a test, not an implementation** (discovery Q2). It is placed after
  S02/S03 because the parity case needs the standalone behaviour to compare against.
- **S10 closes out** and cannot be written until the semantics it documents are settled.

---

## Batch execution order

| batch | sections | parallel? | rationale |
|---|---|---|---|
| 1 | S01 | — | foundation; blocks everything |
| 2 | S02, S04, S08 | ✅ yes | disjoint mechanisms and files |
| 3 | S03, S05, S07 | ✅ yes | all consume S02's mask, none touches another's symbols |
| 4 | S06, S09 | ✅ yes | S06 is renderer-side, S09 is test-side |
| 5 | S10 | — | documents what the others decided |

Batches 2-4 are parallel in *intent*. All of S02-S07 edit `dash_render.py`, so an executor
running them concurrently must either use separate worktrees or serialise the merges.
S08 (Stata side) and S09 (test side) are the only ones with genuinely disjoint file sets.

---

## Sections

See `.ultraplan/sections/index.md` for the manifest and `section-NN-*.md` for each unit.

| # | Section | Risk | Tasks | Discharges |
|---|---|---|---:|---|
| 01 | Baseline and ground truth | green | 4 | additions Q4, Q12 |
| 02 | The mask mechanism — twelve computed mappers | yellow | 7 | items 1, 3 |
| 03 | `histogram` and `kdensity` — the two exceptions | yellow | 5 | item 1 (part) |
| 04 | Connected-topology layers — the NaN column | red | 6 | item 4 |
| 05 | Marker labels and colour range | yellow | 5 | item 8 |
| 06 | Survival under interaction | red | 7 | items 7, 9, 10 |
| 07 | Degenerate subsets, inline layers, warnings | yellow | 5 | additions Q6, Q8 |
| 08 | Qualifier scoping — bar syntax and `by()` | yellow | 4 | additions S1, S2 |
| 09 | Server-mode divergence — the parity test | green | 3 | items 2, 5, 6 (test only) |
| 10 | Documentation, changelog and release | green | 5 | additions Q9, Q10, Q13, Q14 |

---

## Constraints that bind every section

1. **Test first** (rule 8). The regression test fails before the fix and passes after. Read
   the failure and confirm it is the *right* failure. For any test at risk of certifying
   nothing, state the mutation that must make it die.
2. **Assertions on computed layers compare values, not views.** The existing helper
   `_visible_count` (`test/test_varlist_expansion.py:101`) reads
   `renderer.view.filter.booleans` and reports a computed layer as fully visible regardless.
   Compare the layer's own source data against an independently computed subsample.
3. **Assert against Stata's `regress` doubles, not serset floats.** A graph's serset stores
   `float`, so coefficients recovered from a rendered graph agree only to ~1e-8. The fixture
   carries doubles; the tolerance is 1e-6 relative.
4. **Never lose the layer.** The existing contract at :9993-9998 — warn and draw rather than
   raise — is preserved everywhere. But "drawn unfiltered" must become a visible warning
   about a real impossibility, not the silent default.
5. **One commit per work item**, on the feature branch, never on `main` (rule 6), no AI
   references in the message (rule 7). Report the merge command; do not run it.

---

## Definition of done for the phase

- `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` renders a fit implying slope
  `-.010425957587798849` and intercept `48.918297231743246` to 1e-6 relative, while the
  scatter still draws 74 points.
- All 14 computed types produce data equal to the same computation on the qualified subsample.
- A qualified `line` layer draws the correct gapped topology and the document carries no
  E-1024 validation error.
- Every assertion above still holds after a filter move, a brush, a `link()` and inside a
  `by()` panel.
- Each of the 10 items has a regression test proven to fail before its fix.
- One end-to-end `.cscript` proves the headline case through real Stata.
- Both suites green against the S01 baseline.
- The server parity test is red, marked, and attributed to Phases 5-8.

---

## Review Notes

*(populated by Phase 4 REVIEW)*
