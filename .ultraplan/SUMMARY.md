# UltraPlan Summary: dash -- close the drop-in audit of 19oct2026 (WP-33..WP-50)

> One-page cheat sheet | Generated: 2026-10-21. Details: `PRD.md`, `PLAN.md`, `sections/index.md` (binding manifest and procedures), `review/DECISIONS.md` (binding rulings), `VALIDATE.md`.

## What We're Building

Every shortcoming the drop-in audit of 19 October 2026 found is closed, so a Stata user can type `dash` where they would type `twoway` and get twoway's picture, numbers and refusals. Sixteen work packages follow the audit's packages in the maintainer's order (WP-39 removed), then WP-50 speeds up the test suite. The first package builds the twoway-vs-dash comparison of about 425 examples; the gallery built from it (one dash page per plot type and about 12 pairs in the README) is generated last.

## Key Features

- WP-33: GAPS4 register and 221 BUGS entries; size caps removed (33-15); corpus harness, verdicts, ledger; dash image panel and frame-aware builds; a 20-example cert guard; P13's truth items.
- WP-34: the ten default-drawing items (histogram axis, by() ticks and title, range(), aspectratio/xsize, area outline, ci nofit, date end rows, zero label 0, Stata's ticks at build).
- WP-35: twoway's accepts and refusals, with its rc and words; 38 dash-only synonyms refused with a hint naming twoway's spelling; P4's grammar items.
- WP-36: whichever Python Stata finds; WebGL fixes; function points off the macro; environment documented (Chrome, macOS arm64).
- WP-37: one zero-observation check copying twoway per case; contour from Stata's grid; rarea gaps; lfit transforms.
- WP-38/40: a dashboard is not a Stata graph (help); every cap documented, only the drawn rows exported.
- WP-41..45: by(), colorvar, legend/titles/text, axes, schemes/geometry drawn as twoway draws them; three residuals documented.
- WP-46..49: recast()/horizontal, option fidelity, help/README/tracker accuracy, messages.
- WP-50: the test suite toward five minutes; final closeout builds the gallery with your sign-off.

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Parser and export | Stata 19 ado/Mata (`dash.ado`, `dash_parse.mata`) | unchanged; twoway's grammar in Stata |
| Renderer | Python 3.11+, Bokeh 3.8/3.9, numpy, pandas | unchanged; no new user dependency |
| Truth | StataNow 19.5 console on this machine, committed `scripts/extract_*_truth.do` | measured, never hand-typed |
| Harness | headless Chrome over DevTools, node, stdlib SVG readers, numpy+scipy SSIM | existing tools; no new dependency |

## Risk Areas

- [Red] 33-06 dash image panel (registered SVG item)
- [Red] 33-07 Registered graphs keep the frame they were registered in (Stata's frame f: prefix)
- [Red] 33-05 Verdict engine: geometry, image score, ledger
- [Red] 34-09 Stata's own ticks at build; natscale entry re-scoped
- [Red] 36-01 Use the Python Stata finds or the user sets
- [Red] 37-01 One zero-observation check copying twoway per case
- [Red] 37-03 Contour from twoway__contour_gen for gridded data or interp(none)
- [Red] 40-01 Export only the rows the graphs draw (a size measure; nothing refused)
- [Red] 41-05 by(): compact, shrink, total, layout regions, equal panels, overhangs
- [Red] 42-03 twoway's axis-style colour key
- [Red] 43-01 Legend title and subtitle styles; edge titles refused
- [Red] 43-02 Legend ring(0) bplacement, holes, all/draw/nodraw
- [Red] 43-04 Legend keys: size, shapes, merging, horizontal names
- [Red] 43-07 Partial SMCL markup drawn as styled runs
- [Red] 44-03 Scales: off fill, transform words refused, contradictions, log edges, empty minmax
- [Red] 45-04 Figure proportions, size units, graph-region outline and margin, inner box
- [Red] 47-03 Outline, marker and dot alignment
- [Red] 47-05 Noted options twoway draws, drawn
- [Yellow] 58 further sections (index manifest); the main cross-cutting risks are gate time (~40 min per batch end, 57 batches) and many flipped pins.

## Plan Structure

- **Sections:** 92 across 17 WPs (33-38, 40-50)
- **Total tasks:** 509
- **Parallel batches:** 57 (at most three sections each, at most one saved-page JavaScript editor each)
- **Live audit items:** 221, each closed by one section (Appendix A of the index)
- **Rulings:** D40/D41, Q1-Q58, A1-A3, C1-C5, P4-1..P4-10, P5-1..P5-3, A-1..A-28

## How to Execute This Plan

1. On `s3-bugs`, start a WP with the index's W0 steps (truth-script scaffold, CHANGELOG heading).
2. Run its batches in order: for each batch, cut one worktree per section, hand each agent `sections/BRIEF.md`, `sections/index.md`, `review/DECISIONS.md` and its section file, merge with `../dash-wt/_tools/picks.sh`, rewrite pending shas, run `make test-all` once, re-index GitNexus.
3. Close the WP with the index's WE steps (closeout test, ROADMAP section, `make test-all`), then give `git checkout main && git merge s3-bugs`.
4. Start with WP-33 batch 33.1: sections 33-01 (tracking foundation) and 33-15 (size caps removed).
5. The final WE (WP-50) runs `make corpus && make gallery`, asks for your sign-off, and commits the gallery.

## How to Update This Plan

Run `/ultraplan update`, describe what changed; only affected sections are regenerated. A new ruling goes into `review/DECISIONS.md`, which wins over the index and the sections.

## Files in This Plan

| File | What |
|---|---|
| `PRD.md` | approved requirements, plain English |
| `PLAN.md` | technical plan and Review Notes |
| `RESEARCH.md` | research findings and conflict resolutions |
| `research/` | three measured reports (codebase, Stata truth, Bokeh) |
| `DISCOVERY.md` | 58 answers and amendments |
| `VALIDATE.md` | traceability matrix |
| `review/DROPIN-AUDIT-19oct2026.md` | the audit (with D40/D41) |
| `review/REVIEW-1..5.md` | plan reviews |
| `review/DECISIONS.md` | binding Phase 4/5 rulings |
| `sections/index.md` | manifest, procedures, Appendix A/B |
| `sections/BRIEF.md` | writing and execution standard |
| `sections/section-*.md` | 92 executable sections |
| `STATE.md` | session state |
| `handoff/` | run logs and the DROPIN register (read by tests) |
