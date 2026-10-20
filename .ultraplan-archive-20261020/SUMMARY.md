# UltraPlan Summary — WP-31: close the GAPS3 drop-in gaps

## What we're building

Not a feature. The closing of every measured difference between what `dash` draws and what
`twoway` draws. `dash` accepts `twoway` syntax and renders an interactive HTML dashboard through
two renderers in `dash_render.py`: the saved offline page (JavaScript callbacks) and the
`bokeh serve` app (Python callbacks). The 10 October 2026 audit (`GAPS3.md`, at `1a78bb9` plus
the heatmap removal `6370ca4`) found 98 rows across eleven tables where dash still drops,
mis-draws, mis-parses, mis-documents or under-tests twoway behaviour, plus half-finished code
(pending blocks, unwired helpers, xfails) and register drift. WP-31 closes every in-scope row:
94 of the 98 (I1 the platform package and K5 the module split are deferred by the maintainer;
H5 is a documented design residual; K1 is the set of pinned tests each fix section flips),
tracked as 110 BUGS.md entries once split rows are counted per part.

The four undrawn plot types are all feasible in Bokeh and all in scope: `rpcap` and `rpspike`
(S21, batch 7), `contour` and `contourline` (S23 interpolation, S26 drawing, S29 the
JavaScript twin; batches 8-10) with Stata's thin-plate-spline and Shepard interpolation
reimplemented in numpy and JavaScript, exact up to 1,000 points and a seeded subsample above
(D4).

## The findings that justify the effort

1. **Options are accepted and dropped in silence** on types that twoway refuses them for, or
   are named "not drawn" at every call (GAPS3 4.C/4.D/4.E: 47 rows). Sections S02-S09 and
   S30-S46 make every accepted option drawn and every refused option refused with twoway's
   words and return codes.
2. **Four twoway plot types are refused by name** (4.B: B1-B4). S21, S23, S26, S29 draw them.
3. **The saved page cannot refit eleven estimators after a filter move** (F1); it shows a stale
   cue instead. S10-S29 port one estimator per batch to JavaScript, exact to the Python twin.
4. **Parsed values are narrower than twoway's**: degree 4-7, `yaxis(1 2)`, axes 3-9, weight
   expressions, `mla()` bound to the wrong option (4.A, C10, C18, F4). S05-S09.
5. **Layout and geometry differ**: arrowheads, dot rows, legend geometry, minor-tick labels,
   textbox placement, sizing/aspect, by() and region remainders, reference lines beyond the
   frame, tabs/layout checks (4.D). S24, S27, S30-S39.
6. **Data handling**: missing codes, locale, coded-variable text, date ticks, style-file
   resolution, estimator edges (4.G, D15, E10, F5). S43-S47.
7. **The dashboard extensions the maintainer asked for**: a per-graph data table, filter
   widgets, KPI weights, link groups and brush-as-filter, export/print, accessibility (4.H,
   Q35, Q38-Q40). S48-S55.
8. **Documents, examples, registers, packaging and the test harness drift from the tree**
   (4.I, 4.J, 4.K). S56-S60; S61 closes out.

None of these warns. Every row was reproduced on the tree at `6370ca4`.

## Scale

**110 entries · 61 sections · 249 tasks · 116 commits · 22 batches (0-21), 2-3 sections each.**
Risk: 11 red, 36 yellow, 14 green. Effort: 12 S, 41 M, 8 L. Four reviews and five deep passes
(`review/REVIEW-1..4`, `REVIEW-3b..3e`) raised 201 finding rows (7 critical, 70 major, 118
minor); eight maintainer decisions (D1-D8) and twenty-four architect rulings (A11-A34) in
`review/DECISIONS.md` settled them, and three fixer passes rewrote the section files to them.

## The decisions that shaped the plan

1. **Many small batches** (the maintainer's preference): 22 batches of at most three sections,
   each with one owner per hot function (`_FILTER_JS`, the rules table, `_make_figure_body`,
   `_generate_app_source`), so merges with `patch -p1` never collide.
2. **Measure first** (Q17): every section's first task is a committed `scripts/extract_*_truth.do`
   that writes a stamped fixture; no number in a test is planned from another section (A33).
3. **One commit per GAPS3 row, never a red tree** (Q3, BRIEF): the failing regression test is
   written first against the unmodified tree, its failure text saved, and committed together
   with the fix, the flipped pins, the fixture, the closed BUGS.md entry, the GAPS3 Tracked line
   (`commit pending`, rewritten to the landed sha by the merger's step k.3b, A11) and the
   CHANGELOG line.
4. **Custom arrowheads** (D1), **mlabel's minimum is `mlab`** (D2), **estopts layers stay
   frozen** (D3), **contour subsample above the cap** (D4), **tabs() unknown names refused
   r(198)** (D5), **one data table under a by() grid** (D6), **BUGS preambles rewritten** (D7),
   **the release label dropped at closeout** (D8).
5. **No new dependency** (Q11/C3): the interpolation is numpy and plain JavaScript.
6. **Scheme files hold RGB and Stata's RGBA forms only** (Q17); no LICENSE (Q31); version stays
   0.1.0 and only the date moves (Q33); no module split (Q29); no platform package (Q2).

## Risk areas

- **[red] S09 axes 3-9, S32 sizing/scale/aspect** — shared axis and figure-sizing surface across
  both renderers; S32 owns the batch-11 rules edit (A15) and sizes the frame in Python (A16).
- **[red] S10, S19, S22, S28, S29 JavaScript estimators and contour** — twins must agree with
  Python to the parity corpus's tolerance; one `_FILTER_JS` owner per batch (R12).
- **[red] S23, S26 contour** — Stata's kernel (`sqrt(x²+y²)` with a linear trend, not r²log r) and
  the unique(x)×unique(y) grid were measured, not assumed; the 1,000-point cap is exempt from
  the timing test (C2).
- **[red] S44 style-file resolver, S45 date ticks** — file-system and locale edges; rows are
  embedded at registration so a host without the style files still renders (A24).
- **[red] S51 link groups and brush** — several groups, brush-as-filter, concurrent brushes
  intersected, rewriting S48's table view; lands last-but-one in batch 17 (50→51→52, A28).

## Structure

- `.ultraplan/sections/index.md` — the manifest (61 rows), decision record M1-M25, the batch
  order with hot-function owners, merge rules R1-R13, gates G1-G3; it wins over any section.
- `.ultraplan/sections/BRIEF.md` — the writing and execution contract (XML schema, verbatim
  commit, BUGS, Tracked and CHANGELOG forms).
- `.ultraplan/sections/section-NN-<slug>.md` — 61 files, each with evidence at `6370ca4`, user
  stories, business and technical requirements, boundaries, Stata truth, TDD stubs, test plan,
  XML tasks and notes.
- `.ultraplan/review/` — REVIEW-1..4, the deep passes, DECISIONS.md.
- `.ultraplan/VALIDATE.md` — the traceability matrix (Q1-Q40, C1-C4, D1-D8, every GAPS3 row).

## Places you can stop

| Stop after | What the user gets |
|---|---|
| **Batch 3** | Every option is drawn or refused as twoway does (S02-S09): arrowheads, dot base/recast, option applicability, value bounds, parsed values, weights/operators, abbreviations, axes 3-9; the saved page refits lfit/qfit. |
| **Batch 10** | rpcap, rpspike, contour and contourline draw; all eleven estimators and contour refit on the saved page; distribution, colorvar, connect/recast, weighted markers, minor-tick labels and title placement match twoway. |
| **Batch 15** | Legend, textbox, sizing, axis, second-axis, by(), region, reference-line, tabs/layout, symbol, colour, graph-text, data, style-file, date-tick and estimator-edge rows closed. |
| **Batch 18** | The dashboard extensions: function fallback, data table, filter widgets, KPI weights, link groups/brush, saved-page errors and throttle, export/print, accessibility, served hygiene. |
| **Batch 21** | The release: help, examples, registers, README/package, test harness; S61 dates the files, drops the release label, runs the suite, `make cert`, `make gate` and axe, and reports the merge command. |

## How to execute

1. Say: "Read `.ultraplan/sections/index.md` and execute batch 0" (S01 alone), then batch 1 and
   on — one agent per section in its own worktree `wp31-s<NN>`, each given its section file,
   `sections/BRIEF.md`, `DISCOVERY.md`, `RESEARCH.md`, `review/DECISIONS.md` and the research
   report it cites.
2. Merge each finished section with `patch -p1` from its worktree's diff in the batch's merge
   order; run the changed tests; after the batch, the full suite once and `make cert`; rewrite
   the batch's `commit pending` Tracked lines to the landed shas (step k.3b); re-index GitNexus.
3. Repeat through batch 20, then S61 (batch 21), which runs the gates and reports
   `git checkout main && git merge --ff-only s3-bugs` without running it.

## How to update

`/ultraplan update` edits the plan in place: index.md is the manifest of record; a changed
section keeps its number and slug; a new GAPS3 row gets a new entry in S01's Appendix A and a
section in the latest batch that can hold it.
