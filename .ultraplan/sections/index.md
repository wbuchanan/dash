# Section Index -- WP-31: close the GAPS3 drop-in gaps

> Architect pass, 10oct2026, on branch `s3-bugs` at `6370ca4` (= `main` 1a78bb9 plus the heatmap removal and GAPS3.md). Source: `GAPS3.md` section 4 (rows A1..K6), section 5 (partially finished work) and section 6 (register corrections), narrowed by the maintainer's decisions in `.ultraplan/DISCOVERY.md` (Q1-Q40) and `.ultraplan/RESEARCH.md` (C1-C4). Section files are `section-NN-<slug>.md`, written to `BRIEF.md`'s layout. Where a section file disagrees with this index, this index wins.

## Overview

- **Total sections:** 61: S01 tracking foundation, S02-S60 (59 fix sections), S61 closeout. "Sn" means section n.
- **GAPS3 rows in scope:** every row of GAPS3 4.A-4.G, 4.J, 4.K (less K5), 4.H (H1-H7 as narrowed below), 4.I (I2-I7; I1 the platform package is out), section 5's half-finished code, section 6's register corrections, plus one new requirement, the per-graph data table (DISCOVERY Q35, Q38-Q40). The manifest yields 110 entries (rows, with a split row counted once per part; A3 counted per DECISIONS A12), tracked as 110 BUGS.md entries that S01 opens; S01's Appendix A is the binding list.
- **Out of scope (PRD §7):** I1 the platform package; K5 the module split; a LICENSE; sunflower/matamatrix drawing (refused by name instead); contour exact beyond the cap; legend text-before-symbol; scheme-file colour spaces beyond RGB/RGBA.
- **Parallel batches:** 22, numbered 0-21. Batch 0 is S01 alone; batches 1-20 hold two or three sections; batch 21 is the closeout alone. Every dependency lies in an earlier batch. At most one JavaScript (`_FILTER_JS`) editor, one `_generate_app_source` editor, one `_make_figure_body` editor and one `_dash_option_rules` editor per batch (R12).
- **Order (DISCOVERY Q6):** silent drops (S1) first, then values twoway accepts, then named-not-drawn options, then fidelity, then the dashboard extensions, then documents and tests. The JavaScript estimator ports run one per batch from batch 3 so the offline page gains refits steadily without two sections editing the saved filter script at once.
- **Commit units:** one commit per GAPS3 row (BRIEF), so a section with two rows lands as two commits; plus the plan commit (S00), S01's commit and S61's steps.
- **Risk:** 11 red, 36 yellow, 14 green (table below). **Effort:** 12 S, 41 M, 8 L. **Tasks:** 249 across the 61 section files (manifest column = planned; the files are binding).
- **Full-suite runs planned:** one per batch end (22) plus one per section worktree before the merger lands it is NOT required (DISCOVERY Q19); `make cert` at every batch end; `make gate` at S61.

## Decision record (binding; from DISCOVERY.md and RESEARCH.md)

| Id | Decision | Source |
|---|---|---|
| M1 | Scope: all twoway-facing rows, docs, tests, packaging basics, accessibility (K6) and the dashboard extensions (H2); the platform package stays deferred; no module split. | Q1, Q2, Q29 |
| M2 | Done = every in-scope row closed with a BUGS.md entry and a pinning test; full pytest, `make cert`, `make gate` green at closeout; each batch end runs the full suite and `make cert`. | Q3, Q19 |
| M3 | contour/contourline: Python+JavaScript reimplementation of twoway's interpolation (kernel sqrt(x²+y²) with a linear trend; Shepard 1/d²), twoway's grid rule (unique x × unique y), exact up to a cap of 1,000 unique points with live refit in both modes; above the cap a bounded 100×100 grid in Python, the stale cue on the saved page and a note. Exempt from timing tests. Truth = `twoway__contour_gen ..., gen()` output. | Q4, C1, C2 |
| M4 | sunflower and matamatrix() are refused by name with advice and listed in the help. | Q5 |
| M5 | Refuse like twoway: options on types that do not take them (measured per option × type pair from the parse-class table), the plot-type abbreviation superset, misplaced date literals; twoway's rc and words, measured by a committed extract script, never guessed. Every newly refused form gets a CHANGELOG "Changed behaviour" line. | Q15, Q17, Q28, Q36 |
| M6 | Tests that pin today's picture are flipped with the reason, never deleted. | Q16 |
| M7 | Scheme files: RGB and Stata's RGBA syntax only. | Q17 |
| M8 | Where the saved page cannot match the served app, a visible cue names what is frozen; never a silent difference. | Q18 |
| M9 | A section runs only its own and directly covering tests plus the cscript it changed; no full suite inside a section. | Q19 |
| M10 | New computed layers (not contour): under 2 s for 100,000 rows in Python, with a timing test in test_estimator_cost.py. | Q20, C2 |
| M11 | No security guard weakened; new HTML/JS through the nonce/hash paths; test_csp.py and test_serve_token.py green. | Q21 |
| M12 | Residuals: an open BUGS.md entry, a GAPS3 Tracked line, a hand-back note. | Q22 |
| M13 | One `test/test_wp31_truth.cscript` with a block per section; a pytest file per item; S01 is the tracking foundation (GAPS3 Tracked reader, BUGS entries, CHANGELOG markers). | Q23, Q24 |
| M14 | New drawing code lands in the shared glyph layer and helpers the server copies by name; never in the template alone. | Q25 |
| M15 | Drawing an option removes it from the pending list, the help's Unsupported section and TWOWAY_COVERAGE_AUDIT.md in the same commit. | Q26 |
| M16 | All eleven estimators are ported to JavaScript (lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline), each pinned to its Python twin; WP-29 M3 is retired type by type. | Q27 |
| M17 | Fidelity: match twoway's scheme-driven layout where Bokeh can express it; otherwise document with a measured example. | Q30 |
| M18 | No LICENSE; version stays 0.1.0 with a new date at closeout; GitHub distribution now (README with the `net install` line; dash.pkg Author/KW lines). | Q31-Q33 |
| M19 | Accessibility: keyboard-reachable widgets, ARIA labels on every filter, KPI card, tab and figure (host `html_attributes`), contrast checks for the shipped schemes, verified with axe-core through the DevTools harness. | Q34 |
| M20 | Dashboard extensions: per-graph data table (`table()` option; folded, toggle; drawn rows and plotted + hover() variables in Stata display formats and value labels; virtual scroll, sortable, row cap with note; both modes), KPI weights and kurtosis/semean/range, multi-select dropdown, "(missing)" option, slider direction, reset button, several link groups, brush-as-filter, print stylesheet, PNG/SVG export with KPI cards, title, filters and tabs. | Q35, Q38-Q40 |
| M21 | Minor-tick labels: a second LabelSet along the axis at the minor positions in the scheme's minor-label size. | Q37 |
| M22 | No new Python dependency. | Q11, C3 |
| M23 | Tracking moves to GAPS3.md; GAPS2.md and DROPIN-REMAINING.md are read-only. | Q14 |
| M24 | Stata truth comes from committed `scripts/extract_*_truth.do` scripts run on this machine. | Q12 |
| M25 | Both twins for new computed work, one shared fixture, a parity entry. | Q13 |

### Architect decisions (this pass)

| Id | Decision | Why |
|---|---|---|
| A1 | **Grouping.** 59 fix sections, each 1-4 tasks and at most three GAPS3 rows, so a batch of two or three lands in one session (Q9). Rows with an L effort are split: B4 contour into S23 (interpolation, grid, truth), S26 (drawing, options, colour key, cap) and S29 (the JS twin); C8 colorvar into S15 (coverage, jitter) and S17 (the option remainder); C10 into S05 (bounds that are a rules-table edit), S06 (values needing new parsing) and S09 (axes 3-9); F1 into seven JS sections S10, S13, S16, S19, S22, S25, S28; E9/E10 into S42 and S44. | Q9: many small batches. |
| A2 | **Batch rules.** At most three sections per batch; no two sections of a batch edit the same function; one editor per batch for each hot function in the owner table; every dependency in an earlier batch; a red section sits with lighter partners; the JS sections (one per batch) own `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind` and `test_saved_stale_cue.py` for their batch. | Q8, Q9; WP-30 A139. |
| A3 | **Case ids** are `U<NN>-<k>` (prefix `U` is unused in test/ at 6370ca4); a section's cscript cases carry its own prefix whether they sit in the truth script or an area script. | Unique across worktrees. |
| A4 | **Entry ids** are GAPS3 row ids (`C1`, `D4`...), with `a`/`b` for a row split across sections (C8a S15, C8b S17; C10a S05, C10b S06, C10c S09; B4a S23, B4b S26, B4c S29; B5a S03, B5b S18; F1a..F1g the JS sections S10, S13, S16, S19, S22, S25, S28; E9 S42, E10 S44). The data table is `H2t`; the other H2 parts are `H2f` (filters), `H2k` (KPI), `H2l` (links/brush), `H2x` (export/print). CHANGELOG markers are `<!-- WP-31 <id> -->`; commit subjects end `(WP-31 <id>)`. | One id per entry across BUGS.md, GAPS3 Tracked lines, markers and subjects. |
| A5 | **The truth script** `test/test_wp31_truth.cscript` is created and registered by S01 as runner block `// 70.`; the hygiene pins move 68→69; the shard table is regenerated by scripts/cert_shards.py in S01. | WP-30 A142. |
| A6 | **Register corrections** (GAPS3 §6) are applied by S01 as data edits to GAPS2.md Tracked lines and DROPIN-REMAINING.md rows ("Written closed"/"narrowed" annotations), because the tracking tests read them; after S01 those two files are read-only (M23). | Q14. |
| A7 | **Served copy lists.** A section adding a module-level helper or constant appends to the copy tuples after the anchor its Notes name; the anchor table is in R2 below; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` is the guard. | M14. |
| A8 | **Contour cap** is a module constant `_DASH_CONTOUR_EXACT_MAX = 1000` (unique (x,y) points) read by both twins; above it the Python side evaluates on a 100×100 grid over the data's range and tags the layer frozen on the saved page; the note text is fixed in S26. | M3. |
| A9 | **JS prelude.** S10 generalises the `_FILTER_JS` aggregate prelude to read `ac.xvar`, `ac.yvar`, `ac.wvar` jointly (today one `ac.varname`) and adds `dash_fit_grid`, `dash_wls` (normal equations via a small Gaussian elimination with partial pivoting) and `dash_t_ppf` (the incomplete-beta inversion ported from `_t_ppf`); every later JS section builds on them. | M16. |
| A10 | **Applicability column.** S04 adds a `types` column to `_dash_option_rules`' plot tokens (`opt=kind,...@type|type` already exists for value bounds; S04 adds a parallel `applies` table `opt@type|type|...` generated from research/stata-ground-truth.md §1.2-1.3) and a check in `_dash_validate_opts` before the rule loop that refuses with the measured text; the measured text per pair comes from `scripts/extract_applicability_truth.do` into `test/fixtures/applicability_truth.json`. | M5. |

## Section manifest

| # | Slug | GAPS3 rows | Batch | Depends on | Blocks | Risk | Effort | Tasks |
|---|---|---|---|---|---|---|---|---|
| 01 | tracking-foundation | §6, §9 (new) | 0 | -- | all | green | M | 9 |
| 02 | arrowheads | C1 (B27 arrow part) | 1 | 01 | -- | yellow | M | 4 |
| 03 | rbar-msize-dot-recast | C2, B5a (base/recast parts) | 1 | 01 | 18 | green | S | 3 |
| 04 | option-applicability | C3 (A12; BUGS kernel() entry) | 1 | 01 | 05, 06 | yellow | M | 4 |
| 05 | value-bounds | C10a (range(varname), range(# .), bwidth(0), lowess bwidth≥1→.8, n(1), per-type level bounds) | 2 | 04 | -- | green | S | 3 |
| 06 | parsed-values | C10b (degree 4-7 with ROT constants, several vars in one mlabel() element, scatteri 2/2, yaxis(1 2)), C18, F4 | 2 | 04, 05 | 09 | yellow | M | 5 |
| 07 | weights-operators-hover-dates | A5, A6, A7, A8 | 2 | 01 | -- | yellow | M | 5 |
| 08 | abbreviations-prefix-mlalign | A1, A2, A3, A4 | 3 | 01 | -- | green | S | 5 |
| 09 | axes-three-to-nine | C10c (axes 3-9) | 3 | 01, 06 | 35 | red | L | 4 |
| 10 | js-prelude-lfit-qfit | F1a | 3 | 01 | 13, 16, 19, 22, 25, 28, 29 | red | M | 4 |
| 11 | fit-options | C4 | 4 | 04 | -- | yellow | M | 4 |
| 12 | distribution-area-odds | C5 | 4 | 04 | -- | yellow | M | 4 |
| 13 | js-lfitci-qfitci | F1b | 5 | 10 | 28 | yellow | M | 3 |
| 14 | cmissing-connect-recast | C6, C7 | 5 | 01 | -- | yellow | M | 3 |
| 15 | colorvar-coverage | C8a (every type; jitter on the four range types) | 5 | 01 | 17 | yellow | M | 4 |
| 16 | js-lowess | F1c | 4 | 10 | -- | yellow | M | 3 |
| 17 | colorvar-options | C8b (colorformissing alias, colorlist, coloruseplegend, colorstart/end/rule/fillonly/keysrange, clegend/plegend/pcycle) | 6 | 15 | -- | yellow | M | 4 |
| 18 | dot-rows | B5b (dot rows, d-options) | 6 | 03 | -- | yellow | M | 4 |
| 19 | js-lpoly | F1d | 6 | 10 | 22 | red | M | 3 |
| 20 | weighted-markers | C9 | 7 | 01 | -- | yellow | S | 3 |
| 21 | rpcap-rpspike-refusals | B1, B2, B3 | 7 | 01 | 57 | yellow | M | 4 |
| 22 | js-lpolyci | F1e | 7 | 19 | -- | red | M | 3 |
| 23 | contour-interpolation | B4a (TPS/Shepard numpy, grid rule, cap, truth extractor) | 8 | 01 | 26, 29 | red | L | 4 |
| 24 | minor-ticks-labels | D1 | 8 | 01 | 33 | yellow | M | 4 |
| 25 | js-mband-mspline | F1f | 8 | 10 | -- | yellow | M | 3 |
| 26 | contour-drawing | B4b (type registration, options, colour rules, colour key, both modes) | 9 | 23 | 29, 57 | red | L | 4 |
| 27 | edge-titles | D2 | 9 | 01 | -- | yellow | M | 3 |
| 28 | js-fpfit-fpfitci | F1g | 9 | 13 | -- | red | M | 3 |
| 29 | js-contour | B4c (marching squares, isobands, refit within the cap) | 10 | 26, 10 | -- | red | L | 4 |
| 30 | textbox-placement-added-text | D3, D13 | 10 | 01 | -- | yellow | M | 4 |
| 31 | legend-geometry | D4, C13 | 10 | 01 | -- | yellow | M | 4 |
| 32 | sizing-scale-aspect | D5, E11 | 11 | 01 | -- | yellow | M | 4 |
| 33 | axis-suboptions-look | D6, D7, E6 | 11 | 24 | -- | yellow | M | 4 |
| 34 | varlabel-marker-label-options | D8, C17, E3, C14, C15 | 11 | 01 | -- | green | S | 4 |
| 35 | second-axis-moves | D9 | 12 | 09 | -- | yellow | M | 3 |
| 36 | by-remainder | D10 | 12 | 01 | -- | yellow | M | 4 |
| 37 | region-remainder | D11 | 12 | 01 | -- | yellow | M | 3 |
| 38 | reference-lines-frame | D12 | 13 | 01 | -- | yellow | S | 3 |
| 39 | tabs-layout-legend-edges | D14, D16 | 13 | 31 | -- | green | S | 3 |
| 40 | symbols-line-patterns | E1, E2, E12 | 13 | 01 | 44 | yellow | M | 4 |
| 41 | colour-width-outline-edges | E4, E5, E7, E8, E13 | 14 | 01 | -- | green | S | 4 |
| 42 | smcl-inline-runs | E9 | 14 | 01 | -- | yellow | M | 3 |
| 43 | data-missing-locale | G1, G2, G3, G4, G5 | 14 | 01 | -- | yellow | M | 4 |
| 44 | style-file-resolver | E10 | 15 | 40 | -- | red | L | 4 |
| 45 | date-ticks-natscale | D15 | 15 | 01 | -- | red | L | 3 |
| 46 | estimator-edges | C11, C12, C16, G6, G7, F5 | 15 | 01 | -- | yellow | M | 4 |
| 47 | function-fallback-fixtures | F2, F3 | 16 | 01 | -- | yellow | M | 3 |
| 48 | data-table | H2t (new) | 16 | 01 | 53, 54 | yellow | L | 4 |
| 49 | filter-widgets | H2f (E13; multi-select, "(missing)", slider direction, reset) | 16 | 01 | 54 | yellow | M | 4 |
| 50 | kpi-weights-stats | H2k (E7) | 17 | 01 | -- | green | M | 3 |
| 51 | link-groups-brush | H2l (E5, E9: several link groups, brush-as-filter, brush on bars/histograms, concurrent brushes intersected) | 17 | 01, 48 | 52, 60 | red | L | 4 |
| 52 | saved-page-errors-throttle | H1 (E11, E12), S14's and S20's after-move residuals (A23) | 17 | 10, 14, 20, 49 | 53, 54 | yellow | M | 5 |
| 53 | export-print | H2x (E10, J7: composite PNG/SVG, print stylesheet) | 18 | 48 | -- | yellow | M | 4 |
| 54 | accessibility | K6 | 18 | 48, 49 | -- | yellow | M | 4 |
| 55 | served-hygiene | H3, H4, H7 | 18 | 01 | -- | green | S | 4 |
| 56 | help-reconciliation | J1, J2 | 19 | 02-55 | -- | yellow | M | 6 |
| 57 | examples | J3 | 19 | 21, 26 | -- | green | S | 3 |
| 58 | register-drift | J4, J5, J6 | 19 | 01 | -- | green | S | 7 |
| 59 | readme-package-versions | I2, I3, I4, I5, I7 | 20 | 01 | -- | green | S | 8 |
| 60 | test-harness-fixtures | K2, K3, K4, H6, I6 | 20 | 10, 51 | -- | yellow | M | 8 |
| 61 | closeout | -- | 21 | all | -- | green | M | 7 |

Row coverage check: A1-A8 (S08: A1 A2 A3 A4; S07: A5 A6 A7 A8), B1-B5 (S21, S23/26/29, S18, S03), C1-C18 (S02, S03, S04, S11, S12, S14, S14, S15/17, S20, S05/06/09, S46, S46, S31, S34, S34, S46, S34, S06), D1-D16 (S24, S27, S30, S31, S32, S33, S33, S34, S35, S36, S37, S38, S30, S39, S45, S39), E1-E13 (S40, S40, S34, S41, S41, S33, S41, S41, S42, S44, S32, S40-? E12 is a NEW item; E13 S41/S55), F1-F5 (S10..S28, S47, S47, S06, S46), G1-G7 (S43, S43, S43, S43, S43, S46, S46), H1-H7 (S52, S48-S53, S55, S55, design residuals noted in S55, S60, S55), I2-I7 (S59, S59, S59, S59, S60, S59), J1-J6 (S56, S56, S57, S58, S58, S58), K1-K6 (flips inside each fix section; S60; S60; S60; out; S54). E12 (case folding of symbol/pattern names, `_INTENSITY` max) joins S40; E13 (dead `_SIZE_MAP`, duplicate constants, histogram opacity test) joins S41. H5 (served-key and private-file design residuals) stays documented, no section (GAPS3 says design residuals).

## Batch execution order

Each batch: (k.0) record the base sha; (k.1) cut one worktree per section (`git worktree add <path>/wp31-s<NN> -b wp31-s<NN> s3-bugs`); (k.2) run the sections in parallel, at most three, each in its own Stata slot; (k.3) merge in the order given with `patch -p1` from each worktree's diff (project memory: never cd into a worktree to merge; remove worktrees after); (k.3b) rewrite every `commit pending` Tracked line of the batch to the landed sha in one tracking commit (DECISIONS A11); (k.4) run the full pytest suite once and `make cert` once on `s3-bugs`; (k.5) if red, fix on `s3-bugs` and rerun the failed tests; (k.6) re-index GitNexus (`gitnexus analyze --index-only --max-file-size 8192`).

| Batch | Sections (merge order) | Hot-function owners |
|---|---|---|
| 0 | 01 | all (alone) |
| 1 | 04, 02, 03 | rules table: 04; GlyphMapper pc mappers: 02; map_rbar/map_dot: 03 |
| 2 | 05, 07, then 06 | rules table and dash.ado:2998/:3147-3163, dash.sthlp:944/:996: 05 lands, then 06 is cut (A32); 07 runs in parallel with both; dash.ado parsers: 07 |
| 3 | 10, 08, 09 | `_FILTER_JS`: 10; Mata abbreviation table and the `_make_figure_body`/`_dash_figure_for` empty-list guards (R1-22): 08; `_dash_add_secondary_axes`: 09 |
| 4 | 16, 11, 12 | `_FILTER_JS`: 16 (and S12's gap/area/boundary refit keys, A22); fit mappers: 11; histogram/kdensity/function/area/bar mappers: 12 |
| 5 | 13, 14, 15 | `_FILTER_JS` and `map_lfitci`/`map_qfitci`: 13; `_dash_connect_opt`/`_dash_recast_opt`: 14 (merged before 15); `_apply_colorvar`/`_dash_fold_typed`: 15 |
| 6 | 19, 17, 18 | `_FILTER_JS`: 19; colorvar option readers: 17; map_dot: 18 |
| 7 | 22, 20, 21 | `_FILTER_JS`: 22; map_scatter size path: 20; plot-type registration: 21 |
| 8 | 25, 23, 24 | `_FILTER_JS`: 25; new module `_dash_contour_*` helpers: 23; axis ticker/LabelSet: 24 |
| 9 | 28, 26, 27 | `_FILTER_JS`: 28; map_contour + registration: 26; title placement: 27 |
| 10 | 29, 30, 31 | `_FILTER_JS`: 29; `_dash_textbox`/`_dash_textbox_place`/added text: 30; legend builders: 31 |
| 11 | 32, 33, 34 | `_dash_option_rules`, `_make_figure_body`, `_generate_app_source`, `_dash_layout_cell`, figure sizing: 32 (S33's lwidth bound and S34's lalign/mlalign tokens ride S32's rules edit, A15); axis label/scale appliers and the R11 finishers: 33; dash.ado syntax + mlabel readers + `_apply_mlabel_opts`: 34 |
| 12 | 35, 36, 37 | secondary axes + `_dash_refinish_axes` + JS axis finish (R11): 35; by() grammar/appliers, `_FILTER_JS`, `_build_filter_widgets`, `_make_figure_body`, `_generate_app_source`: 36; region appliers (reads `_dash_plot_margin(mult=)` S36 adds): 37 |
| 13 | 38, 39, 40 | reference lines (one Arrow path, `_DASH_AXIS_ZOOM_JS` statement, A17): 38; tabs/layout checks + legend label edges + `_generate_app_source`: 39; symbol/pattern translators: 40 |
| 14 | 41, 42, 43 | colour/width translators + outlines + `_generate_app_source` (three deleted `_SIZE_MAP` lines): 41; graph-text parser, `_dash_gt_head`, test_graph_text.py, the graph-text help paragraph: 42; loader/export/missing, `_DASH_FILTER_MASK_JS`/`_DASH_FMT_JS`, `_build_filter_widgets`, `_dash_graph_text_style`: 43 (new tests in its own file) |
| 15 | 44, 45, 46 | style tables/resolver: 44; date ticks, `_DASH_AXIS_FINISH_JS` (R11), `_make_figure_body`/`_generate_app_source` stamps: 45; lpoly/function/stale-kind edges, its own `_FILTER_JS` substitution: 46 (S45 and S46 add to `_dash_plot` on disjoint lines; merge 45 then 46) |
| 16 | 47, 48, 49 | function fallback + fixtures: 47; `_dash_layout_cell` + DataTable: 48; FilterBuilder: 49 |
| 17 | 50, 51, 52 | KPI statistics (`dash_apply_kpis` inside `_FILTER_JS`, template `_compute_kpi`): 50; link/brush machinery (`_dash_link_names`, `_BRUSH_JS`, template link block): 51; `_FILTER_JS` wrapper at the :31459 assembly, slider throttle, `_build_filter_widgets`, the `document_ready` `_hooks` list, the bin-members twin: 52 -- an R12 exception with recorded disjoint hunks, merge order 50→51→52 (A28) |
| 18 | 53, 54, 55 | export/print JS + composite: 53; `html_attributes`/ARIA + axe harness: 54; served template env/health/bundle: 55 |
| 19 | 56, 57, 58 | dash.sthlp: 56; examples/: 57; the tracking documents: 58 |
| 20 | 59, 60 | README/dash.pkg/version pins: 59; test harness/scripts/CI: 60 |
| 21 | 61 | closeout, main checkout |

## Merge rules (R1-R13; from WP-30, with WP-31 ids)

- **R1 cscripts.** Only S01 creates or registers a cscript (`test_wp31_truth.cscript`, runner block `// 70.`, pins 68→69). Every other section appends a block above the marker line in section order and adds area-script cases under its `U<NN>` prefix.
- **R2 served copy lists.** New module-level helpers/constants are appended to the copy tuples at the anchor the section names; a section never reorders the tuples. Anchors: constants after `_DASH_STALE_STATUS_HTML` (:46584-46784 region); functions after `_dash_reference_lines` (:47223); statistical helpers after `_natural_cubic_spline` (:47446-47503). `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` guards misspellings.
- **R3 help paragraphs.** Each section edits only the dash.sthlp paragraphs it owns (named in its Notes) and the Unsupported-list lines for the options it draws; S56 owns everything else in dash.sthlp and lands in batch 19.
- **R4 CHANGELOG.** Markers placed by S01 are replaced in place by their row's closing task; nothing else is added.
- **R5 BUGS.md and GAPS3 Tracked.** Entries are closed in place (Resolution rewritten, `- [x]`); Tracked lines rewritten in place; the tracking test's open set shrinks by the id.
- **R6 dash.ado, dash_setup.ado, dash_parse.mata.** `_dash_require_mata`'s `_needed` list is data: append in alphabetical place; `version 19` in every new program; the seven graph key lists change together.
- **R7 fixtures.** `_meta` complete; never hand-patched; `git add -f`.
- **R8 parity corpus.** Append CORPUS/MOVE_CORPUS entries; `ALLOWED` is never edited.
- **R9 pinned tests.** Flipped in place with a `Flipped:` commit line; never deleted.
- **R10 combined pins and counts.** test_unsupported_report_is_true.py's declared counts, test_cscript_hygiene.py's script counts and similar pins move with a `# old -> new: <id> <why>` comment.
- **R11 axis finishers.** `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS` have one editor per batch (S24 batch 8, S33 batch 11, S35 batch 12, S45 batch 15).
- **R12 one editor per batch** of `_FILTER_JS`, `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, `_dash_option_rules`, the four `_apply_*` appliers and `_dash_layout_cell` (owner table above).
- **R13 GitNexus.** Re-index after each batch lands.

## Verification gates

- **G1 section hand-back:** the section's regression tests red at base and green after; its cscript cases pass under the console binary; no `Flipped:` without a reason; BUGS entry closed; GAPS3 Tracked line rewritten; CHANGELOG marker replaced; help/Unsupported list/TWOWAY_COVERAGE_AUDIT.md updated in the same commit; no tooling names in messages.
- **G2 batch end:** full pytest green; `make cert` 69 of 69 scripts passed, no SKIP; test_tracking_documents.py green (open set = the ids of later sections only).
- **G3 closeout (S61):** full pytest, `make cert`, `make gate` green; no open BUGS.md entry at S1/S2; GAPS3 §9 has no "Open" line; help Unsupported list == pending blocks; examples cover every drawn type; axe-core reports 0 violations on the example pages; dates bumped; ROADMAP WP-31 marked DONE with measurements.

## Phase 4 decisions

See `.ultraplan/review/DECISIONS.md` (D1-D8 maintainer, A11-A34 architect); a decision there wins over any section text.

## Residuals (expected, to be filed by S61 if unclosed)

Legend text-before-symbol (M17); contour above the cap; the platform package (I1); the module split (K5); served-key and private-file design residuals (H5); anything a section files under M12.
