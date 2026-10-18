# Phase index — finishing the ultraplan

> **Historical (10oct2026).** The phase files in phases/ are superseded by ROADMAP.md (WP-12 to WP-30) and .ultraplan/handoff/DROPIN-REMAINING.md; their PARTIAL markers and definitions of done are the state of 20sep2026 (ca5fe35) and are not maintained.

This directory breaks the remaining work in [`../REMAINING.md`](../REMAINING.md)
into **31 sequentially numbered phases**, each scoped to one to three epics. Every
phase document is self-contained: it carries the evidence for its own work, user
stories with acceptance criteria, numbered business and technical requirements, the
full work-item list, and a test plan.

`REMAINING.md` is the source of record and is unchanged — nothing was moved out of it,
only copied. Where a phase document and `REMAINING.md` disagree, `REMAINING.md` wins.

## What is in here

**249 work items** — 168 functional (a user-visible
behaviour gap) and 81 deliverable (a test, cscript, help
sentence or changelog entry the plan asked for). Effort mix:
151 small, 81 medium,
17 large.

The items come from three places in `REMAINING.md`, all of them preserved:

| source | what it is | items |
|---|---|---:|
| Main body (§1–§7, the 17 overturned claims, the section status table) | the five blockers and the cross-cutting gaps | 52 |
| Appendix B | the itemised backlog for the eight tasks reviewed in detail | 76 |
| Appendix C | what the adversarial pass added, less the one refuted item | 121 |

One item from Appendix B was refuted and is deliberately absent: the adversarial
canvas-text test already exists. The `graphsize_x`/`graphsize_y` refutation narrowed a
surviving item rather than removing it. Both are recorded in Appendix C.

## The phases

| # | Phase | Items | Func | Deliv | S/M/L | Depends on |
|---:|---|---:|---:|---:|:---:|---|
| 01 | [Per-plot qualifiers on computed layers](PHASE-01-per-plot-qualifiers-on-computed-layers.md) | 10 | 10 | 0 | 2/8/0 | — |
| 02 | [Per-plot qualifiers — edge cases, server and KPI percentiles](PHASE-02-per-plot-qualifiers-edge-cases-server-and-kpi-percentiles.md) | 7 | 5 | 2 | 4/3/0 | 01 |
| 03 | [Packaged install and scheme reachability](PHASE-03-packaged-install-and-scheme-reachability.md) | 5 | 1 | 4 | 4/1/0 | — |
| 04 | [Security, resource limits and honest declarations](PHASE-04-security-resource-limits-and-honest-declarations.md) | 9 | 6 | 3 | 6/3/0 | — |
| 05 | [Server unification I — the glyph dispatch](PHASE-05-server-unification-i-the-glyph-dispatch.md) | 5 | 5 | 0 | 2/1/2 | — |
| 06 | [Server unification II — facet expansion and loop unification](PHASE-06-server-unification-ii-facet-expansion-and-loop-unification.md) | 12 | 10 | 2 | 8/4/0 | 05 |
| 07 | [Server unification II(b) — the twenty plot types that draw nothing](PHASE-07-server-unification-iib-the-twenty-plot-types-that-draw-not.md) | 6 | 5 | 1 | 4/1/1 | 05, 06 |
| 08 | [Server unification III — the parity guard](PHASE-08-server-unification-iii-the-parity-guard.md) | 9 | 3 | 6 | 6/3/0 | 05, 06, 07 |
| 09 | [Dates I — the standalone loader and primary axes](PHASE-09-dates-i-the-standalone-loader-and-primary-axes.md) | 14 | 8 | 6 | 8/4/2 | — |
| 10 | [Dates II — secondary axes, tick lists and the server renderer](PHASE-10-dates-ii-secondary-axes-tick-lists-and-the-server-renderer.md) | 8 | 7 | 1 | 5/3/0 | 05–08 |
| 11 | [Formats I(a) — hover and tooltips](PHASE-11-formats-ia-hover-and-tooltips.md) | 5 | 4 | 1 | 5/0/0 | 09 |
| 12 | [Formats I(b) — date filter widgets and cardinality](PHASE-12-formats-ib-date-filter-widgets-and-cardinality.md) | 14 | 9 | 5 | 9/3/2 | 09 |
| 13 | [Formats II — KPIs, facets, marker labels and the server renderer](PHASE-13-formats-ii-kpis-facets-marker-labels-and-the-server-render.md) | 6 | 2 | 4 | 3/3/0 | 09–12, 05–08 |
| 14 | [Axis grammar I — numlist rules and sub-options](PHASE-14-axis-grammar-i-numlist-rules-and-sub-options.md) | 6 | 5 | 1 | 2/4/0 | — |
| 15 | [Axis grammar II — scales, minmax and dates](PHASE-15-axis-grammar-ii-scales-minmax-and-dates.md) | 9 | 8 | 1 | 6/2/1 | 14 |
| 16 | [Axis grammar III — the server port](PHASE-16-axis-grammar-iii-the-server-port.md) | 9 | 6 | 3 | 5/4/0 | 05–08, 14, 15 |
| 17 | [The option surface — declaring and serializing the 69](PHASE-17-the-option-surface-declaring-and-serializing-the-69.md) | 6 | 6 | 0 | 3/2/1 | — |
| 18 | [The option surface — abbreviations, generator and reporting](PHASE-18-the-option-surface-abbreviations-generator-and-reporting.md) | 15 | 6 | 9 | 8/7/0 | 17 |
| 19 | [S07 statistical options](PHASE-19-s07-statistical-options.md) | 4 | 3 | 1 | 1/2/1 | 17, 18 |
| 20 | [S09 axis and text options](PHASE-20-s09-axis-and-text-options.md) | 3 | 3 | 0 | 1/0/2 | 17, 18 |
| 21 | [S09 style options](PHASE-21-s09-style-options.md) | 5 | 5 | 0 | 0/2/3 | 17, 18 |
| 22 | [Geometry, sizing and layout](PHASE-22-geometry-sizing-and-layout.md) | 4 | 3 | 1 | 1/3/0 | 17, 18 |
| 23 | [Scheme consumption I(a) — text sizing and typography](PHASE-23-scheme-consumption-ia-text-sizing-and-typography.md) | 8 | 7 | 1 | 7/1/0 | — |
| 24 | [Scheme consumption I(b) — subtitle, caption and the size stubs](PHASE-24-scheme-consumption-ib-subtitle-caption-and-the-size-stubs.md) | 9 | 8 | 1 | 6/3/0 | 23 |
| 25 | [Scheme consumption II — legend, colour mapping and CSS delivery](PHASE-25-scheme-consumption-ii-legend-colour-mapping-and-css-delive.md) | 15 | 9 | 6 | 10/4/1 | 23, 24 |
| 26 | [Text fidelity I — canvas escaping](PHASE-26-text-fidelity-i-canvas-escaping.md) | 11 | 10 | 1 | 11/0/0 | — |
| 27 | [Text fidelity II — hover() and the secondary axis](PHASE-27-text-fidelity-ii-hover-and-the-secondary-axis.md) | 12 | 8 | 4 | 5/6/1 | 26, 05–08 |
| 28 | [Varlist, server-fix and parser leftovers](PHASE-28-varlist-server-fix-and-parser-leftovers.md) | 8 | 6 | 2 | 6/2/0 | — |
| 29 | [Test debt and scheme ground truth](PHASE-29-test-debt-and-scheme-ground-truth.md) | 2 | 0 | 2 | 1/1/0 | — |
| 30 | [Documentation and help reconciliation](PHASE-30-documentation-and-help-reconciliation.md) | 9 | 0 | 9 | 9/0/0 | all feature phases |
| 31 | [Release gates and closeout](PHASE-31-release-gates-and-closeout.md) | 4 | 0 | 4 | 3/1/0 | all |

## Suggested execution order

The ordering is not arbitrary. Two facts from the audit drive it: wrong numbers
outrank everything else, and **six of the eight tasks reviewed in detail are done in
`DashRenderer` and absent from `ServerAppBuilder`**. Phase 05 is the lever — once a
plot type delegates to the shared `GlyphMapper`, it inherits the standalone behaviour
instead of needing its own copy of every later fix. Running the server-dependent
phases before it means doing that work twice.

### Wave 1 — Correctness and security first

- **Phase 01 — Per-plot qualifiers on computed layers** (10 items)
- **Phase 02 — Per-plot qualifiers — edge cases, server and KPI percentiles** (7 items)
- **Phase 03 — Packaged install and scheme reachability** (5 items)
- **Phase 04 — Security, resource limits and honest declarations** (9 items)

### Wave 2 — The server-unification lever

- **Phase 05 — Server unification I — the glyph dispatch** (5 items)
- **Phase 06 — Server unification II — facet expansion and loop unification** (12 items)
- **Phase 07 — Server unification II(b) — the twenty plot types that draw nothing** (6 items)
- **Phase 08 — Server unification III — the parity guard** (9 items)

### Wave 3 — Dates and display formats

- **Phase 09 — Dates I — the standalone loader and primary axes** (14 items)
- **Phase 10 — Dates II — secondary axes, tick lists and the server renderer** (8 items)
- **Phase 11 — Formats I(a) — hover and tooltips** (5 items)
- **Phase 12 — Formats I(b) — date filter widgets and cardinality** (14 items)
- **Phase 13 — Formats II — KPIs, facets, marker labels and the server renderer** (6 items)

### Wave 4 — The axis grammar

- **Phase 14 — Axis grammar I — numlist rules and sub-options** (6 items)
- **Phase 15 — Axis grammar II — scales, minmax and dates** (9 items)
- **Phase 16 — Axis grammar III — the server port** (9 items)

### Wave 5 — The option surface

- **Phase 17 — The option surface — declaring and serializing the 69** (6 items)
- **Phase 18 — The option surface — abbreviations, generator and reporting** (15 items)
- **Phase 19 — S07 statistical options** (4 items)
- **Phase 20 — S09 axis and text options** (3 items)
- **Phase 21 — S09 style options** (5 items)
- **Phase 22 — Geometry, sizing and layout** (4 items)

### Wave 6 — Scheme fidelity and text

- **Phase 23 — Scheme consumption I(a) — text sizing and typography** (8 items)
- **Phase 24 — Scheme consumption I(b) — subtitle, caption and the size stubs** (9 items)
- **Phase 25 — Scheme consumption II — legend, colour mapping and CSS delivery** (15 items)
- **Phase 26 — Text fidelity I — canvas escaping** (11 items)
- **Phase 27 — Text fidelity II — hover() and the secondary axis** (12 items)

### Wave 7 — Leftovers, docs and release

- **Phase 28 — Varlist, server-fix and parser leftovers** (8 items)
- **Phase 29 — Test debt and scheme ground truth** (2 items)
- **Phase 30 — Documentation and help reconciliation** (9 items)
- **Phase 31 — Release gates and closeout** (4 items)

## How to read a phase document

Each one follows the same skeleton, set by the project's planning rule (CLAUDE.md
rule 21): Purpose · At a glance · Why this phase exists · Epics · User stories ·
Business requirements · Technical requirements · Work items · Test plan · Definition
of done · Risks and sequencing notes.

Two project rules shape every test plan in here:

- **Rule 8** — a bug fix needs a regression test that fails *before* the fix and passes
  after. Each phase names the failing test to write first.
- **Rule 4** — every function needs a unit test, and the application needs end-to-end
  coverage. Each phase names the actual test files and, for the tests most at risk of
  certifying nothing, the mutation that must make them die.

The second matters more than usual here: this repository has a documented history of
tests that passed against broken implementations. Ten such tests were found and fixed
during the plan, and the adversarial pass found more. A test that has not been shown to
fail has not been shown to work.

## Gates that close the programme

Phase 31 holds the six gates from ultraplan task 16-07: full pytest · full
certification suite with honest skip counts · the conformance corpus (zero `r(198)`,
zero dropped series, zero dropped graphs) · the parity corpus · a clean `net install`
that runs every example · the adversarial suite. At the time of the audit the first
four passed and the fifth failed on the packaging defect that Phase 03 fixes.

