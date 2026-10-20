# Section Index -- WP-33..WP-50: close the drop-in audit of 19oct2026

> Architect pass, 20oct2026, on `s3-bugs` at `090d928` (= `main`). Sources: `review/DROPIN-AUDIT-19oct2026.md` (17 packages, 224 printed items), the maintainer's rulings D40/D41 (in the audit's decisions section), `DISCOVERY.md` (Q1-Q58, amendments A1-A3), `RESEARCH.md` (conflicts C1-C5) and the three reports in `research/`. Section files are `section-NN-MM-<slug>.md`, written to `BRIEF.md`. **Where a section file disagrees with this index, this index wins; `review/DECISIONS.md` (Phase 4) wins over both.**

## Overview

- **Work packages:** 17 -- WP-33..WP-38, WP-40..WP-50 (WP-39 removed by A3; its number stays unused). Run in this order: 33, 34, 35, 36, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50. One WP is closed (WE steps, below) before the next starts.
- **Sections:** 91, numbered `NN-MM` (WP, section). **Batches:** 56, numbered `NN.b` inside each WP (`b` from 1). At most three sections per batch; at most one section per batch edits the saved page's JavaScript (`_FILTER_JS`, `_DASH_AXIS_FINISH_JS`, `_DASH_CVAR_RELEVEL_JS` -- column JS); every dependency lies in an earlier batch of the same WP.
- **Items:** 224 printed; 3 withdrawn (plat:PT-3 by Q48, basic:PT-7 by Q50, plot:PT-10 by A2); **221 live items**, each keyed by its lead id and assigned to exactly one section (Appendix A, the binding list 33-01 copies into GAPS4.md and BUGS.md).
- **Risk:** 15 red, 60 yellow, 16 green.
- **Commit unit:** one commit per item (lead id); a section with several items commits once per item, in its listed order. Sections with no item (33-01..33-09, 48-04, WP-50) commit once per task group they name.
- **Gates:** each batch ends with `make test-all` (pytest whole suite + parity + `make cert`), as WP-31/32 did; each WP ends with the WE steps; the final WE (WP-50) re-runs the corpus and regenerates the gallery (Q3).

## Decision record (binding)

### Maintainer rulings (summarised; full text in the cited file)

| Id | Ruling | Source |
|---|---|---|
| M1 | heatmap and sunflower are not twoway plot types; matamatrix() does not exist in Stata. Never listed as gaps, plot types, tests or audit targets. Contour's own `heatmap` option stays in scope. | D40, A2 |
| M2 | Never reference differences between Stata editions; plat:PT-3 is withdrawn and no text may mention it. | Q48 |
| M3 | Scope: all 17 packages; each item fixed, or documented where its ruling says so. One WP per package (WP-33..49 in the D40 order); WP-39 removed, its items moved (A3); WP-50 suite speed. | Q1, Q2, Q5, A3, Q29 |
| M4 | Done: every item Closed/Documented/Withdrawn with a BUGS entry and a pinning test; `make test-all` green per WP; the corpus re-run and gallery regenerated at the final closeout with maintainer sign-off. | Q3, Q6, Q12 |
| M5 | P13 corpus: help files + g.pdf [G-2]/[G-3] + `examples/` + the audit's probes; datasets in a git-ignored cache; twoway SVG beside a dash SVG (BokehJS export) at each example's own twoway size; geometry verdicts (Same/Close/Differs) with a known-differences ledger plus an image score; ~12 curated pairs in the README as captioned pairs; one dash-built gallery page with tabs by plot type embedding each twoway SVG beside its live graph, committed under `docs/gallery/` with no size cap; `make corpus`/`make gallery`; a ~20-example cert guard; no paths or names in outputs; dev/test-only tools allowed, none expected. | Q9, Q13-Q20, Q30, Q36, Q53-Q58, C2, C4 |
| M6 | P1: resolve all ten items; never a 0 px plot; time-series operators verified allowed in twoway before any L./D. work (research measured 121 probes, all agreeing) and twoway's answer matched where it refuses; the zero label is `0`; Stata's ticks at build; the after-move natscale misses stay open. | D41, Q28 |
| M7 | P11: accept what twoway accepts, refuse what it refuses, with its rc and words. P4's remaining items move here. Capitalised plot-type spellings are refused (lower case only). The dash-only words are ruled per word in Phase 4 from the measurements. | D40, Q4, Q7, Q8, A3 |
| M8 | P2: no pre-check of Python -- when c(python_exec) is empty dash and dash_setup run the normal `python:` path and surface Stata's own failure with dash's advice; the harness follows the same rule; no `python query` probe. WebGL: dashed lines keep the figure on canvas; the switch counts drawn rows. Function points of named graphs kept off the macro. Documented only: the tested platform (macOS arm64, StataNow 19.5, console), Chrome as the tested browser, the lock's coverage, the dependencies (listed in the help, nothing else), the large-data timings, the Stata 19 floor. | D40, C5, Q31, Q33-Q35, Q46, Q47, Q49, A1 |
| M9 | P12: one Stata-side zero-observation check, run after the qualifiers are applied and before Python, copying twoway's measured answer per type and case (twoway draws an empty graph for 34 of 40 types); where it refuses, twoway's words first and a second line naming the plot's number and type. Contour from `twoway__contour_gen` when the data is a full grid or interp(none); scattered data above 1,000 points keeps the subsample and its note. lpolyci zero df: correct the help. | D40, Q21, Q22, C1, Q26, C3, Q27 |
| M10 | P3: resolved by help documentation only (a dashboard is not a Stata graph, every listed rc and message difference). P5: every cap documented (Differences entry + Resource limits); the cell cap counts only the selected rows when nothing needs every row; every other cap kept. | D40, Q44, Q45 |
| M11 | P6-P10: fix every item -- Bokeh can draw all of them (shipped models + CustomJS + composites; no custom TypeScript models); the three composite residuals (mixed SMCL runs, dates past the browser's range, custom key cells without click-to-hide) are documented under Differences. | D40, Q23, Q24, research B §4.8 |
| M12 | P14-P17: resolve; RH-8 documented (dash keeps its clean transpose); jitter unchanged and undocumented; dash's extra refusal lines and Supported list kept (P16 corrects help sentences that say otherwise). | Q25, Q43, Q50 |
| M13 | Process: worktree agents under `../dash-wt/_tools/agent-rules.md`, merged by cherry-pick with `picks.sh`; three Stata slots; 2-3 sections per batch of 1-4 tasks; committed `scripts/extract_*_truth.do` truth (never hand-typed); saved JS + served Python twins with one fixture and a parity entry; pinned tests flipped with the reason, never deleted; a failing test first; the pending list, help Unsupported and TWOWAY_COVERAGE_AUDIT.md updated in the same commit; a per-WP truth cscript; documented items pinned by a help-claim test plus a probe where measurable; help notes = a one-line Differences entry linking to the topic section. | Q10, Q11, Q37-Q42 |
| M14 | Release: version stays 0.1.0 (dates move); the README keeps its drop-in claim; P16 fixes false sentences as their WPs land. | Q51, Q52 |

### Architect decisions (this pass)

| Id | Decision |
|---|---|
| PD-1 | **Register.** `GAPS4.md` at the repository root: a header naming the audit, D40/D41 and this index; one `## WP-NN` section per WP (in run order) with a table `| ID | Item | Sev | Section | Kind | Evidence | Fix |`, one row per Appendix A item keyed by its lead id (other ids in the Item cell); no rows for the three withdrawn items (the header says only that three audit items were withdrawn by rulings Q48, Q50 and A2 and are not registered); a `## Tracking` section with one `- **<id> Tracked:** <form>` line per row. 33-01 writes it from Appendix A and the audit text. |
| PD-2 | **Severity map** for the release guard: P1 items S1; P2-P13 items S2; P14-P17 items S3. Every open S1/S2 title is in the new `GAPS4_OPEN` allowance. |
| PD-3 | **Tracked forms** (exact): `Open (WP-NN section NN-MM).` · `Closed in WP-NN, BUGS.md "<title>", commit <sha|pending>.` · `Documented in WP-NN, BUGS.md "<title>", commit <sha|pending>.` · `Partly closed in WP-NN (section NN-MM, commit <sha|pending>): <closed>; open: <rest> (BUGS.md "<residual title>").` The merger rewrites `pending` to the landed sha in one tracking commit per batch (step k.3b). |
| PD-4 | **BUGS.md forms** (exact): open `  - Resolution: Not fixed because WP-NN section NN-MM has not landed. Graded S<n> (WP-NN): <why>.`; closed `  - Resolution: Fixed <ddmonyyyy> (WP-NN, <id>). <what changed, where, both modes>. Pinned by <node>[, <cscript case>][; fixture <file>]. Closes GAPS4 <id> (WP-NN, <id>).`; documented `  - Resolution: Documented <ddmonyyyy> (WP-NN, <id>). <help file:section where it is stated>. Pinned by <help-claim node>[, <probe>]. Closes GAPS4 <id> (WP-NN, <id>).`. Titles unique, no `"`. Entries appended at the end of BUGS.md in Appendix A order. |
| PD-5 | **Case ids** are `Q<NN><MM>-<k>` (e.g. `Q3402-1` for section 34-02); never the audit-id shape `XX-n`, which the tracking test's `_CASE_ID` would read as a test name. |
| PD-6 | **Truth scripts.** One `test/test_wpNN_truth.cscript` per WP that compares with Stata: WP 33, 34, 35, 36, 37, 40, 41, 42, 43, 44, 45, 46, 47, 49. None for WP-38, WP-48 and WP-50 (their probes join the existing area cscripts). Each is created and registered at its WP's start (step W0) from the template 33-01 adds (`test/templates/wp_truth_template.cscript`) -- except `test_wp33_truth.cscript`, which 33-01 itself creates and registers from that template (WP-33's W0.2 is therefore skipped); 33-01 replaces WP-31's hygiene reader with one parametrised `_wp_blocks(src, wp)` over every `test_wp(3[3-9]|4[0-9])_truth.cscript`. Block header `* ==== S<MM> <lead-id>: <what> ====`, gate `local only : env WP<NN>_ONLY`. |
| PD-7 | **CHANGELOG.** W0 adds `### Fixed in WP-NN` under the 0.1.0 release; each item's closing commit appends one line ending `(WP-NN, <id>)` there, or under `### Changed behaviour (may need your do-files changed)` when the item refuses something dash accepted or accepts something it refused. No markers. `unionmerge.py` merges CHANGELOG hunks. |
| PD-8 | **The audit's 22 false help/README sentences** (audit :855-880) are not rows. Appendix B maps each to its owning section, which corrects it in the item's commit; 48-04 verifies all 22 with one help-claim test each and corrects any still false. |
| PD-9 | **natscale entry.** 34-09 re-scopes the one open BUGS entry (BUGS.md:4139-4143) and the ROADMAP "exact at build" sentence (ROADMAP.md:5153) to the after-move misses only; plot:PT-13 ends `Partly closed` with that entry as its residual (D41: the after-move misses stay open). |
| PD-10 | **sunflower and matamatrix() code (M1).** 35-09 makes both refusals generic -- `sunflower` gets the same "is not a twoway plot type" refusal as any other word, `matamatrix()` the same refusal as any option dash does not take -- removes `_dash_undrawn_plottype`'s and `_dash_matamatrix_typed`'s by-name paths, flips their pins, and removes both names from dash.sthlp (:737-745, :995-997). One commit `(WP-35 A2)`; no GAPS4 row. |
| PD-11 | **plot:PT-7 scope.** The first line of every refusal is twoway's words naming the option as typed; dash's second and later lines and the Supported list stay (Q43). |
| PD-12 | **Gallery feature (C4).** 33-06 adds a registered image panel: `dash image using <file.svg>, name(<n>) [caption(<text>) alt(<text>)]`; the SVG is read at build, size-bounded, sanitised (no script, event handler, foreignObject or external reference), and drawn as `<img src="data:image/svg+xml;base64,...">` inside a Bokeh `Div` (CSP `img-src data:` already allowed); caption and alt escaped; placed by `layout()`/`tabs()` like a KPI; both modes; its own cap `$dash_max_images` (default 100, ceiling 1,000), documented in Resource limits. 33-07 adds `frame(<name>)` on graph registration: the graph's data is exported from that Stata frame at build; graphs in different frames may not share a `link()` or brush (refused r(198)); a filter applies to the graphs whose frame holds its variable. With no `frame()`, behaviour is unchanged. |
| PD-13 | **Gallery files.** README block between `<!-- dash-gallery:start -->` and `<!-- dash-gallery:end -->`, written only by `make gallery` from `scripts/corpus/readme_examples.txt` (about 12 example ids); pairs as two `<img>` side by side with the command and verdict as the caption beneath; SVGs at `docs/gallery/svg/<id>-twoway.svg` and `<id>-dash.svg` (normalised: duplicate text strokes and random clip ids rewritten deterministically); the gallery page `docs/gallery/index.html` (a `!docs/gallery/*.html` rule in `.gitignore`); the corpus data (`docs/gallery/corpus.json`: id, source, command, rc pair, verdict, differences). The first gallery (33-14) states its date and dash commit; WP-50's WE regenerates it. |
| PD-14 | **Verdicts.** Same = rc pair equal and every geometry check within tolerance and image score at or above T_same; Close = only ledger-listed or within-tolerance differences and image score at or above T_close; Differs = anything else. 33-05 calibrates T_same/T_close and the tolerances on a committed calibration set and records them in `test/fixtures/corpus_verdict_rules.json`; the ledger `test/fixtures/corpus_ledger.json` keys each known difference by GAPS4 id, so a fix that lands removes its ledger rows. |
| PD-15 | **Zero-observation check (M9).** One program `_dash_zero_obs_check` (dash.ado), called right after `_dash_qual_gen` on the one-line route (dash.ado:11778) and in `_dash_prepare_spec` (:13207, build and serve), reading the per-type/per-case table from `test/fixtures/zero_obs_truth.json` (written by `scripts/extract_zero_obs_truth.do`, research S §3's 400 probes) as a Mata rule table in dash_parse.mata; the existing per-type refusals in `_dash_process_segment` stay and must agree with it. |
| PD-16 | **The ts-operator precondition (D41).** 34-07's task 01 runs `scripts/extract_ts_operator_truth.do` extended with the 22 new probes of research S §4 and commits the regenerated fixture before any operator work; if any probe's twoway answer differs from the fixture of 18oct2026, the section stops at its checkpoint. |
| PD-17 | **WP-33's first gallery is a baseline.** It is generated before WP-34..49 land, so many verdicts are Differs; the README block says so in one sentence with the date. by() and multi-figure examples are exported at dash's default size until 34-04/45-04 make xsize()/ysize() exact; the harness records which pairs are size-matched. |
| PD-18 | **Per-word rulings (Q8)** are asked in Phase 4 and recorded in `review/DECISIONS.md`; 35-07 (and CV-14 in 42-05) implement them. |

## Work packages

| WP | Title | Sections | Batches | Live items | Truth script |
|---|---|---|---|---|---|
| WP-33 | Verification corpus and README gallery (P13) | 14 | 7 | 9 | test_wp33_truth.cscript |
| WP-34 | Default drawing of common graphs (P1) | 9 | 4 | 11 | test_wp34_truth.cscript |
| WP-35 | Accepted syntax and refusals (P11, with P4's remaining items) | 9 | 4 | 27 | test_wp35_truth.cscript |
| WP-36 | Python discovery and environment (P2) | 4 | 2 | 10 | test_wp36_truth.cscript |
| WP-37 | Statistical and computed layers (P12) | 5 | 3 | 8 | test_wp37_truth.cscript |
| WP-38 | Stata graph integration, documented (P3) | 2 | 1 | 12 | none |
| WP-40 | Resource limits (P5) | 2 | 2 | 10 | test_wp40_truth.cscript |
| WP-41 | by() fidelity (P6) | 6 | 4 | 20 | test_wp41_truth.cscript |
| WP-42 | Colour variables (P7) | 5 | 4 | 17 | test_wp42_truth.cscript |
| WP-43 | Legend, titles and added text (P8) | 7 | 6 | 25 | test_wp43_truth.cscript |
| WP-44 | Axes (P9) | 5 | 3 | 20 | test_wp44_truth.cscript |
| WP-45 | Schemes, styles and figure geometry (P10) | 5 | 3 | 14 | test_wp45_truth.cscript |
| WP-46 | recast() and horizontal (P14) | 2 | 2 | 6 | test_wp46_truth.cscript |
| WP-47 | Plot-option fidelity (P15) | 6 | 4 | 18 | test_wp47_truth.cscript |
| WP-48 | Help, README and tracker accuracy (P16) | 4 | 3 | 9 | none |
| WP-49 | Messages and notes (P17) | 2 | 1 | 5 | test_wp49_truth.cscript |
| WP-50 | Test-suite speed | 4 | 3 | 0 | none |

## Section manifest

| Section | Slug | Name | Items (lead ids) | Batch | Depends on | Risk | JS | Owns (hot functions / files) |
|---|---|---|---|---|---|---|---|---|
| 33-01 | tracking-foundation | GAPS4 register, 221 BUGS entries, tracking and truth-script readers | -- | 33.1 | none | yellow |  | BUGS.md, GAPS4.md, test_tracking_documents.py, test_cscript_hygiene.py (alone) |
| 33-02 | corpus-extractor | Corpus extractor and dataset cache | -- | 33.2 | 33-01 | yellow |  | scripts/corpus/ (new) |
| 33-06 | image-panel | dash image panel (registered SVG item) | -- | 33.2 | 33-01 | red |  | _dash_kpi family, master JSON, _dash_layout_cell, kpi_divs |
| 33-10 | value-abbrev-truth | value_truth probe-by-probe and abbreviation bindings | TR-11, syn:SD-20 | 33.2 | 33-01 | yellow |  | test_option_validation.py, extract_abbrev_truth.do |
| 33-03 | twoway-runner | twoway runner: SVG at each example's size | -- | 33.3 | 33-02 | yellow |  | scripts/corpus/ |
| 33-07 | graph-frames | Registered graphs read their own frame | -- | 33.3 | 33-06 | red |  | _dash_register_graph, _dash_prepare_spec, _dash_write_data, _dash_build |
| 33-11 | strict-run-scale-truth | Strict run passes; scale() frame geometry truth | TR-23, GW-11 | 33.3 | 33-01 | yellow |  | test_graph_text.py TestBounds, _dash_apply_scale (read only) |
| 33-04 | dash-runner-svg | dash runner: saved page, SVG and view dump | -- | 33.4 | 33-03 | yellow |  | scripts/corpus/, test/range_probe.py (read) |
| 33-12 | by-type-truth | Per-type by() truth and by() title positions | BY-23, BY-24 | 33.4 | 33-01 | yellow |  | scripts/extract_by_types_truth.do (new), extract_by_text_truth.do |
| 33-13 | estimator-colorvar-truth | Estimator combinations and colorvar key truth | stat:PT-23, CV-16 | 33.4 | 33-01 | yellow |  | extract_stat_truth.do, extract_colorvar_truth.do |
| 33-05 | verdict-engine | Verdict engine: geometry, image score, ledger | -- | 33.5 | 33-03, 33-04 | red |  | scripts/corpus/verdict.py (new) |
| 33-08 | gallery-readme | Gallery page, README block, make targets, privacy scan | -- | 33.6 | 33-05, 33-06, 33-07 | yellow |  | Makefile, README.md block, docs/gallery/, .gitignore |
| 33-09 | cert-guard | Twenty-example certification guard | -- | 33.6 | 33-05 | yellow |  | test_wp33_truth.cscript block, corpus_guard_truth.json |
| 33-14 | corpus-first-run | First corpus run, sign-off, gallery commit | TR-2 | 33.7 | 33-08, 33-09 | yellow |  | docs/gallery/, README.md (alone) |
| 34-01 | histogram-bin-axis | Histogram bin axis ticked over the midpoints | AX-4 | 34.1 | none | yellow | yes | _dash_layer_extent, _dash_axis_plan, dash_axis_extent, _DASH_STATA_TICK_SKIP, _FILTER_JS histogram branch |
| 34-04 | fixed-frame-size | aspectratio() with xsize()/ysize(): exact frame, never 0 px | VF-3 | 34.1 | none | yellow |  | _dash_frame_sizes, _dash_apply_frame_aspect |
| 34-05 | area-outline | Default area outline and key | PIC-1 | 34.1 | none | green |  | map_area |
| 34-03 | range-ticks | range() beyond the data: ticks over the data only | AX-1 | 34.2 | 34-01 | yellow | yes | _dash_finish_count_ticks scale join, _DASH_AXIS_FINISH_JS scale filter |
| 34-06 | ci-nofit-index | ci types with nofit count one plot | PIC-3 | 34.2 | none | green |  | _dash_plot_style_indices, _dash_apply_legend counter, _dash_legend_keys |
| 34-08 | zero-label | a(b)c rules write the zero label as 0 | DG-3 | 34.2 | none | green |  | _dash_expand_numlist |
| 34-07 | date-axis-end-rows | Date axis with a missing y at an end row (ts-operator probe first) | TR-4 | 34.3 | 34-03 | yellow | yes | dash.ado _dash_stata_ticks_gen summaries, dash_axis_extent rows |
| 34-02 | by-ticks-shared-title | by(): x ticks at #4 and the shared y title painted | AX-2, VF-2 | 34.3 | 34-01 | yellow |  | _dash_by_numticks, _dash_by_text_cell, _dash_by_cell |
| 34-09 | stata-ticks-at-build | Stata's own ticks at build; natscale entry re-scoped | AX-3, plot:PT-13 | 34.4 | 34-02, 34-07 | red | yes | _dash_stata_tick_requests, _dash_stata_ticks_gen, colour-key tick calls |
| 35-01 | repeated-options | Repeated options taken rightmost | MS-1 | 35.1 | none | yellow |  | _dash_label_split, _dash_contour_split |
| 35-02 | p-numbered-options | p1() .. p20() mapped onto their plots | syn:SD-3 | 35.1 | none | yellow |  | _dash_tw_takes_tab p rows, gen_twoway_takes_table.py |
| 35-09 | command-grammar | Plot-type case, empty graph, group forms; generic sunflower/matamatrix refusals | plot:PT-3, plot:PT-4, syn:SD-1, syn:SD-13 | 35.1 | none | yellow |  | _dash_expand_plottype, _dash_split_groups, _dash_split_segs, _make_figure_body empty branch |
| 35-03 | stat-option-acceptance | Statistical-type options twoway accepts | stat:PT-7, syn:SD-5, stat:PT-13, stat:PT-6, stat:PT-9, syn:SD-7 | 35.2 | 35-01 | yellow |  | dash.ado option declarations, _dash_fn_points, _dash_recast_opt |
| 35-06 | graph-option-refusals | Graph-option refusals in twoway's words | basic:PT-8, GW-2, GW-3, GW-4, sil:SD-8, syn:SD-8 | 35.2 | none | yellow |  | _dash_parse_graph_opts, _dash_validate_value var kind |
| 35-04 | stat-option-refusals | Statistical-type refusals twoway makes | stat:PT-1, stat:PT-2, stat:PT-5, stat:PT-8, stat:PT-14 | 35.3 | 35-03 | yellow |  | _dash_validate_opts, _dash_option_rules flags, _dash_contour_check, _dash_fold_bw |
| 35-05 | value-codes-bounds | Value refusals with twoway's codes; dash's own bounds lifted | basic:PT-9, basic:PT-13 | 35.3 | 35-06 | yellow |  | _dash_option_rules values, _dash_validate_value |
| 35-07 | dash-only-words | Dash-only words per the maintainer's per-word rulings | DT-15 | 35.4 | 35-04, 35-05 | yellow |  | option declarations of the ruled words |
| 35-08 | working-columns | Working columns that never clash with user variables | DT-19 | 35.4 | none | yellow |  | _dash_qual_gen, _dash_maxvar_room |
| 36-01 | python-discovery | Use the Python Stata finds or the user sets | plat:PT-1 | 36.1 | none | red |  | _dash_require_python, dash_setup.ado, dash_setup_lib._linked, harness gates |
| 36-02 | webgl-backend | WebGL: dashed lines on canvas, switch on drawn rows | DG-14 | 36.1 | none | yellow |  | _make_figure_body backend, served backend lines |
| 36-03 | function-points-strl | Function points of named graphs kept off the macro | plat:PT-4 | 36.1 | none | yellow |  | _dash_register_graph function points, _dash_fn_spec_tail |
| 36-04 | environment-docs | Environment documented: platform, Chrome, lock, dependencies, timings | plat:PT-5, plat:PT-2, plat:PT-11, plat:PT-12, plat:PT-6, plat:PT-16, plat:PT-14 | 36.2 | 36-01 | green |  | dash.sthlp Dependencies/Description, dash_setup.sthlp, README.md |
| 37-01 | zero-obs-check | One zero-observation check copying twoway per case | DG-1 | 37.1 | none | red |  | _dash_zero_obs_check (new), map_contour empty branch |
| 37-04 | lfit-transformed-x | lfit/lfitci on xlog/xtransform() | stat:PT-12 | 37.1 | none | yellow | yes | _dash_fit_points, JS fit twins |
| 37-05 | statistical-docs | lpolyci zero df, numeric limits and ties documented | stat:PT-16, DT-26, stat:PT-21 | 37.1 | none | green |  | dash.sthlp statistical paragraphs |
| 37-02 | rarea-gaps-contour-key | rarea outlines break at gaps; contour key without a surface | DG-5, DG-8 | 37.2 | 37-01 | yellow | yes | map_rarea bound lines, dash_fill_vertices, map_contour key |
| 37-03 | contour-stata-grid | Contour from twoway__contour_gen for gridded data or interp(none) | TR-13 | 37.3 | 37-02 | red |  | _dash_contour_check site, map_contour surface |
| 38-01 | graph-integration-help | Help: a dashboard is not a Stata graph | syn:SD-17, GW-12, ECO-1, ECO-4, ECO-15, ECO-7 | 38.1 | none | green |  | dash.sthlp new {marker graphintegration} section |
| 38-02 | registry-message-help | Help: name(), saving(), nodraw, play(), dash clear rc differences | GW-13, GW-14, GW-15, GW-16, GW-9, ECO-5 | 38.1 | none | green |  | dash.sthlp Differences item 2 sub-points |
| 40-01 | selected-row-count | The cell cap counts only the selected rows | plat:PT-7 | 40.1 | none | red |  | _dash_cell_cap, _dash_write_data, _dash_embedded_cells |
| 40-02 | caps-docs | Every cap documented under Differences and Resource limits | plat:PT-8, plat:PT-9, plat:PT-10, stat:PT-15, sil:SD-1, AX-16, sil:SD-11, sil:SD-12, sil:SD-13 | 40.2 | 40-01 | green |  | dash.sthlp Resource limits and Differences |
| 41-01 | by-contour-cuts | Contour under by(): one shared z axis | BY-28 | 41.1 | none | yellow | yes | _dash_share_by_scales z, dash_contour_cuts |
| 41-03 | by-scale-range-weights | by(): scale(), per-panel range(varname), zero-weight panels | BY-2, BY-27, sil:SD-7 | 41.1 | none | yellow |  | _dash_scale_factor, _dash_fold_range, by() weight gate |
| 41-06 | by-panel-labels | by() panel-label sub-options and raw values | BY-10, BY-16 | 41.1 | none | yellow |  | by() panel label row |
| 41-02 | by-chrome-titles | by(): ring(0) chrome, edge titles, legend position notes, unfiled residuals | BY-1, BY-12, BY-7, TR-19 | 41.2 | 41-06 | yellow |  | _dash_by_chrome, _dash_text_annotations by skip |
| 41-04 | by-holes-keys | by(): at() holes, legloc/plegend, coloruseplegend, hole legend scale | BY-3, BY-13, BY-14, PIC-13 | 41.3 | 41-02 | yellow |  | _dash_by_keys, _dash_by_side |
| 41-05 | by-styles-layout | by(): compact, shrink, total, layout regions, equal panels, overhangs | BY-4, BY-5, BY-6, BY-18, VF-6, GW-5 | 41.4 | 41-04 | red |  | _DASH_BYSTYLE_EXPAND, _dash_by_spacing, by() grid, _dash_overhangs |
| 42-01 | colorvar-stepped-default | Unbinned numeric colorvar binned at the z ticks; key width from the scheme | CV-8, sil:SD-4 | 42.1 | none | yellow | yes | _apply_colorvar continuous branch, _colorvar_stepped_mapper, _DASH_CVAR_RELEVEL_JS |
| 42-02 | colorvar-line-parts-swatches | colorfillonly line parts, two colorvar layers, pstyle swatch | CV-1, CV-6, CV-7 | 42.2 | 42-01 | yellow |  | _colorvar_paint, _colorvar_line_parts, colorvar key per layer |
| 42-05 | colorvar-cuts-refusals | colordiscrete levels, colorvar refusals, malformed keys, documented acceptances | CV-2, CV-9, CV-10, CV-14 | 42.2 | 42-01 | yellow | yes | _dash_colorvar_cuts, dash_cvar_relevel_bins, colorvar rules |
| 42-03 | colorvar-axis-key | twoway's axis-style colour key | CV-3, CV-15, LT-12, AX-12, LT-22 | 42.3 | 42-02, 42-05 | red |  | _apply_colorvar discrete key, _DASH_CLEGEND_SUBOPTS, z tick family |
| 42-04 | colorvar-plegend-interplay | coloruseplegend key, legend() isolation, colorkeysreverse | CV-4, CV-5, CV-11 | 42.4 | 42-03 | yellow |  | coloruseplegend key, _dash_apply_legend cv_legends |
| 43-01 | legend-titles | Legend title and subtitle styles; edge titles refused | LT-1, LT-15, LT-13 | 43.1 | none | yellow |  | _dash_apply_legend title block, _DASH_LEGEND_SUBOPT_TABLE |
| 43-06 | added-text | text(): alignment() and the box options | LT-11, LT-20 | 43.1 | none | yellow |  | _dash_at_canon, _dash_added_text |
| 43-02 | legend-placement | Legend ring(0) bplacement, holes, all/draw/nodraw | LT-4, LT-17, LT-5 | 43.2 | 43-01 | yellow |  | _dash_move_legend, legend merge loop, holes |
| 43-05 | title-boxes | Title boxes: fill, ring, placement at ring(0), sub-options, edge titles, quotes | LT-8, LT-9, LT-14, LT-16, LT-18, LT-19, LT-24 | 43.3 | 43-02 | yellow |  | _dash_textbox_style, _dash_textbox_position, _dash_edge_titles |
| 43-03 | legend-box-layout | Legend box and layout sub-options, bexpand, margins | LT-2, LT-3, LT-6, LT-7, LT-10 | 43.4 | 43-05 | yellow |  | _dash_legend_box, _DASH_LEGEND_SUBOPTS, _dash_legend_margin_px |
| 43-04 | legend-keys | Legend keys: size, shapes, merging, horizontal names | LT-21, PIC-11, MS-10, RH-13 | 43.5 | 43-03 | red |  | _dash_legend_keys, _dash_legend_key, key composites |
| 43-07 | smcl-runs | Partial SMCL markup drawn as styled runs | ST-14 | 43.6 | 43-04 | red |  | text drawing of titles, labels and keys (alone) |
| 44-01 | axis-titles | Axis titles: orientation, right-axis reading, two lines, the ... rule | AX-13, PIC-12, MS-13, MS-11 | 44.1 | none | yellow |  | _dash_style_axis_titles, _dash_axis_default_titles, _dash_rep_merge axis titles |
| 44-04 | date-axes | Date axes: numbers where twoway labels numbers, %tC, dates with blanks | AX-18, DG-6, DG-4 | 44.1 | none | yellow | yes | date axis choice, _dash_tc_from_tC, _dash_tdate_value |
| 44-05 | axis-misc | Lone second-axis gridlines; non-numbers in label lists refused | MS-12, DG-9 | 44.1 | none | green |  | _dash_lone_second_axes, _dash_axlabel_refusal |
| 44-02 | tick-label-options | Label and tick sub-options: custom, grid styles, style words | AX-5, AX-6, AX-8, AX-14, AX-15 | 44.2 | 44-01 | yellow |  | _DASH_AXLABEL_HONOURED, tick gridlines |
| 44-03 | axis-scales | Scales: off fill, transforms, contradictions, log edges, empty minmax | AX-7, AX-9, AX-10, AX-11, MS-14, DG-13 | 44.3 | 44-02 | red | yes | _dash_scale_spec, _dash_scale_look, log ticks, _DASH_AXIS_FINISH_JS |
| 45-01 | economist-fixes | economist: note painted; p#other and p#area widths | PIC-4, PIC-7 | 45.1 | none | yellow |  | _dash_text_annotations in-band branch, p_other_band_styles, map_rarea widths |
| 45-02 | style-word-readers | Style-word readers per class | ST-1 | 45.1 | none | yellow |  | _dash_at_place, _dash_at_orient, clock/ring regexes, _dash_connect_canon |
| 45-05 | colour-font-edges | Colour intensity edge, blank stylelist words, plain-text font face | ST-22, GW-10 | 45.1 | none | yellow |  | colour grammar, _dash_graph_set_fonts |
| 45-03 | style-files-schemes | Style files, shipped-name order, scheme directives, unknown scheme() | ST-7, ST-15, ST-10, ST-17, ST-16 | 45.2 | 45-02 | yellow |  | _STYLE_FILE_CLASSES, _resolve_path, _scheme_name_ok |
| 45-04 | figure-geometry | Figure proportions, size units, graph-region outline and margin, inner box | VF-4, GW-1, GW-6, ST-21 | 45.3 | 45-03 | red | yes | _make_figure_body sizing, _dash_graph_margin, _DASH_GRAPH_MARGIN_JS, _dash_inner_box |
| 46-01 | recast-orientation | recast(): horizontal judged as twoway judges it | RH-1, RH-9, RH-11 | 46.1 | none | yellow |  | _dash_hz_check, _dash_recast_opt orientation, y2xtype table |
| 46-02 | recast-bounds-histogram | recast(): second bound kept; histogram recast style; RH-8 documented | RH-3, RH-5, RH-8 | 46.2 | 46-01 | yellow | yes | _dash_draw_range_as, map_histogram recast, _dash_tag_eval_extent |
| 47-01 | pc-immediate-labels | headlabel and immediate-type labels | basic:PT-1, MS-7 | 47.1 | none | yellow |  | map_pcscatter, map_pccapsym, map_pcarrowi, map_pci_literal, map_scatteri |
| 47-03 | outline-alignment | Outline, marker and dot alignment | basic:PT-4, basic:PT-6, basic:PT-5 | 47.1 | none | yellow |  | outline width/alignment code, mlalign, dot outline |
| 47-02 | varlabels-formats | varlabel and varformat reach every type; mlabel(t*); emptied-layer names | MS-2, MS-3, MS-5, basic:PT-3, DG-7 | 47.2 | 47-01 | yellow |  | _dash_layer_series, _dash_mlabel_list, _dash_axis_default_titles |
| 47-06 | markers-dots-bins | Marker shapes, empty bins, dot rows, zero weights, dot floor, documented differences | PIC-2, PIC-9, PIC-10, DG-12, PIC-16, basic:PT-15 | 47.2 | 47-03 | yellow | yes | symbol map, map_histogram empty bins, _dot_positions, _FILTER_JS rebin |
| 47-04 | older-spellings | Older spellings folded onto the options dash draws | basic:PT-10 | 47.3 | 47-02 | green |  | _dash_tw_silent_tab, option folds |
| 47-05 | noted-options-drawn | Noted options twoway draws, drawn | basic:PT-11 | 47.4 | 47-04 | red |  | each option's mapper (listed in the section) |
| 48-01 | stale-help-paragraphs | Stale help paragraphs rewritten and pinned | LT-27, plot:PT-5, basic:PT-16, GW-22 | 48.1 | none | green |  | dash.sthlp paragraphs named in the section |
| 48-03 | tracker-accuracy | Tracker accuracy: dash_setup help, CHANGELOG, coverage audit, GAPS3, DROPIN | DT-29 | 48.1 | none | green |  | dash_setup.sthlp, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md, GAPS3.md, DROPIN-REMAINING.md |
| 48-02 | help-claims-conformance | Unsupported list from twoway's declarations; recast claims; ecosystem paragraph | syn:SD-15, RH-15, ECO-16, DT-28 | 48.2 | 48-01 | green |  | test_help_conformance.py, dash.sthlp Unsupported |
| 48-04 | false-sentence-sweep | The audit's false-sentence checklist (HR-1..HR-22) | -- | 48.3 | 48-02, 48-03 | green |  | dash.sthlp, README.md, dash.pkg (alone) |
| 49-01 | refusal-first-line | Refusal first lines in twoway's words, typed spelling | plot:PT-7, plot:PT-6 | 49.1 | none | yellow |  | _dash_refuse_unknown, _dash_refuse_foreign, _dash_refuse_repeat first line |
| 49-02 | notes-silence | Silence where twoway is silent; notes in twoway's words; library messages | basic:PT-12, LT-25, plot:PT-11 | 49.1 | none | yellow |  | _dash_silent_drop, note sites, _dash_require_mata load |
| 50-01 | suite-profile | Profile the gate and name the bottlenecks | -- | 50.1 | none | green |  | none (measurement) |
| 50-02 | cert-consolidation | Certification: fewer loads, consolidated truth scripts, balanced shards | -- | 50.2 | 50-01 | yellow |  | run_all_cscripts.do, cert_shards.py, test_wp*_truth.cscript |
| 50-03 | pytest-levers | pytest: the untaken levers | -- | 50.2 | 50-01 | yellow |  | conftest.py, slow test files |
| 50-04 | suite-verify | make test at most 5 minutes, recorded | -- | 50.3 | 50-02, 50-03 | green |  | ROADMAP.md, handoff/TEST-PERFORMANCE.md |

Blocks: the inverse of Depends on; the closeout steps WE of each WP depend on every section of that WP.

## Batch execution order

Each batch: **(k.0)** record the base sha on `s3-bugs`; **(k.1)** cut one worktree per section, `git worktree add ../dash-wt/wpNN-sMM -b wpNN-sMM s3-bugs`; **(k.2)** run the sections in parallel, at most three, each holding one Stata slot (`scripts/stata_slot.sh`); **(k.3)** land them in the listed order with `../dash-wt/_tools/picks.sh` (cherry-pick; comment hunks keep both sides, value hunks keep ours and are marked REDERIVE; BUGS/CHANGELOG/GAPS4 union-merged), then the line-loss Counter check after every conflicted pick; **(k.3b)** rewrite every `commit pending` Tracked line of the batch to the landed sha in one tracking commit; **(k.4)** `make test-all` once (prefix `FULL_SUITE_RERUN=1` for a third launch in a session); **(k.5)** if red, fix on `s3-bugs` (fixture/pin drift: update the fixture; regression: fix the code) and rerun only the failed tests; **(k.6)** re-index GitNexus (`gitnexus analyze --force --index-only --max-file-size 8192`); **(k.7)** remove the worktrees.

| Batch | Sections (merge order) |
|---|---|
| 33.1 | 33-01 |
| 33.2 | 33-02, 33-06, 33-10 |
| 33.3 | 33-03, 33-07, 33-11 |
| 33.4 | 33-04, 33-12, 33-13 |
| 33.5 | 33-05 |
| 33.6 | 33-08, 33-09 |
| 33.7 | 33-14 |
| 34.1 | 34-01, 34-04, 34-05 |
| 34.2 | 34-03, 34-06, 34-08 |
| 34.3 | 34-07, 34-02 |
| 34.4 | 34-09 |
| 35.1 | 35-01, 35-02, 35-09 |
| 35.2 | 35-03, 35-06 |
| 35.3 | 35-04, 35-05 |
| 35.4 | 35-07, 35-08 |
| 36.1 | 36-01, 36-02, 36-03 |
| 36.2 | 36-04 |
| 37.1 | 37-01, 37-04, 37-05 |
| 37.2 | 37-02 |
| 37.3 | 37-03 |
| 38.1 | 38-01, 38-02 |
| 40.1 | 40-01 |
| 40.2 | 40-02 |
| 41.1 | 41-01, 41-03, 41-06 |
| 41.2 | 41-02 |
| 41.3 | 41-04 |
| 41.4 | 41-05 |
| 42.1 | 42-01 |
| 42.2 | 42-02, 42-05 |
| 42.3 | 42-03 |
| 42.4 | 42-04 |
| 43.1 | 43-01, 43-06 |
| 43.2 | 43-02 |
| 43.3 | 43-05 |
| 43.4 | 43-03 |
| 43.5 | 43-04 |
| 43.6 | 43-07 |
| 44.1 | 44-01, 44-04, 44-05 |
| 44.2 | 44-02 |
| 44.3 | 44-03 |
| 45.1 | 45-01, 45-02, 45-05 |
| 45.2 | 45-03 |
| 45.3 | 45-04 |
| 46.1 | 46-01 |
| 46.2 | 46-02 |
| 47.1 | 47-01, 47-03 |
| 47.2 | 47-02, 47-06 |
| 47.3 | 47-04 |
| 47.4 | 47-05 |
| 48.1 | 48-01, 48-03 |
| 48.2 | 48-02 |
| 48.3 | 48-04 |
| 49.1 | 49-01, 49-02 |
| 50.1 | 50-01 |
| 50.2 | 50-02, 50-03 |
| 50.3 | 50-04 |

## WP start (W0) and WP end (WE) steps -- run by the orchestrator in the main checkout

**W0 (before the WP's first batch):** (W0.1) `git checkout s3-bugs && git merge --ff-only main` if main moved; (W0.2) for a WP with a truth script other than WP-33 (33-01 creates WP-33's), `sed 's/@@WP@@/NN/g' test/templates/wp_truth_template.cscript > test/test_wpNN_truth.cscript`, add its runner block after the last `test_wp*_truth` block in `test/run_all_cscripts.do` and its shard row `test_wpNN_truth.cscript 1.0 0 * * *`, move the three count pins by one with a `# old -> new: test_wpNN_truth.cscript (WP-NN W0)` comment (test_cscript_hygiene.py glob count and Python-skip count, test_cert_shards.py), run `python3 scripts/cert_shards.py check`, `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_shards.py test/test_cert_verdict.py -q` and the new script once through `scripts/stata_slot.sh` (expect `part 1/1 has no block to run` or the scaffold PASS); (W0.3) add `### Fixed in WP-NN` to CHANGELOG.md (PD-7); (W0.4) commit `Add the WP-NN truth script and changelog heading (WP-NN W0)`.

**WE (after the WP's last batch):** (WE.1) confirm every registered Appendix A row of the WP is Closed, Documented or Partly and no `pending` remains; (WE.2) append `"WP-NN"` to `GAPS4_CLOSED_WPS` in test/test_tracking_documents.py and add the WP's closeout-sha constant after the commit (two-step: commit WE.3, then a follow-up commit records its sha); (WE.3) add `## WP-NN · <title> — DONE` to ROADMAP.md (user story, business requirements citing M-ids, `**Entries.**` line `<n> WP-NN entries; <c> closed, <d> documented, <p> partly closed; BUGS.md holds <k> open entries.`, residuals with their BUGS titles, the gate line with date, pytest counts and cert 'N of N passed'); (WE.4) `make test-all` and record it; (WE.5) commit `Close WP-NN (WP-NN WE)`; give the maintainer `git checkout main && git merge s3-bugs`; (WE.6) re-index GitNexus. **Final WE (WP-50) adds:** (WE.7) `make corpus && make gallery`, a maintainer checkpoint on the regenerated gallery, commit `Regenerate the corpus gallery (WP-50 WE)`; (WE.8) move the dates (0.1.0 stays, M14).

## Merge rules (R1-R14)

- **R1 cscripts.** Only W0 creates or registers a WP truth script. A section appends one block per item above `* ==== append new blocks above this line ====` in section order and puts refusal/message cases in the existing area cscript for its area under its own `Q<NN><MM>-<k>` ids.
- **R2 served copy lists.** A new module-level helper or constant in dash_render.py is appended to the served copy tuples at the anchor the section names (constants, functions and statistical-helper tuples; re-read the anchors -- they drift); never reorder; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` guards it.
- **R3 help paragraphs.** A section edits only the dash.sthlp paragraphs its Notes name, the Unsupported-list lines for options it draws, its own one-line Differences entries and the topic notes they link to; 48-04 owns the rest.
- **R4 CHANGELOG** per PD-7; union-merged.
- **R5 BUGS.md and GAPS4.md** are edited in place only (Resolution rewritten, `- [x]`, Tracked line rewritten); the closing commit deletes its id's line from `GAPS4_OPEN`.
- **R6 ado/Mata.** `version 19` in every new program; `_dash_require_mata`'s `_needed` list and the dash_parse.mata header index updated for a new Mata function; test/program_coverage_map.py for a new program; test/function_test_map.py for a new dash_render.py function.
- **R7 fixtures.** Written by a committed `scripts/extract_*_truth.do`; `_meta` complete (`stata_version`, `born_date`, `dash_commit`, `extracted`, `source`); never hand-patched; `git add -f`; named by a test.
- **R8 parity corpus.** Append `CORPUS`/move entries in test/test_mode_parity.py for every twin; `ALLOWED` is never edited.
- **R9 pinned tests** are flipped in place with a `Flipped:` commit-body line; never deleted.
- **R10 counts and pins** move with a `# old -> new: <id> <why>` comment.
- **R11 axis finishers.** `_dash_refinish_axes`, `_dash_finish_count_ticks` and `_DASH_AXIS_FINISH_JS` have one editor per batch (the JS column marks it where it is the saved twin).
- **R12 one editor per batch** of `_FILTER_JS`, `_DASH_AXIS_FINISH_JS`, `_DASH_CVAR_RELEVEL_JS`, `ServerAppBuilder._generate_app_source_body`, `_make_figure_body`, `_dash_option_rules`, `_dash_apply_legend`, `GlyphMapper._apply_colorvar`, `_dash_layout_cell` and `_dash_process_segment`'s per-type check block. The Owns column names each section's; a section that finds it needs another section's hot function in the same batch stops and reports it (the orchestrator moves one of them to the next batch).
- **R13 GitNexus** re-indexed after each batch lands and before each commit's detect-changes check.
- **R14 banned topics.** No section, test, help sentence or commit message lists heatmap or sunflower as a twoway plot type, mentions matamatrix() except to remove it (PD-10), references Stata editions, or adds a browser other than Chrome.

## Verification gates

- **G1 section hand-back:** every regression test red at base (saved failure text) and green after; its cscript cases pass under the console binary; flips carry reasons; BUGS entry closed and GAPS4 Tracked line rewritten per item; help/Unsupported list/TWOWAY_COVERAGE_AUDIT.md/CHANGELOG updated in the item's commit; commit messages free of tooling or vendor names (grep `claude|anthropic` before and after).
- **G2 batch end:** `make test-all` green (pytest whole suite, parity, cert N of N passed with no SKIP); test_tracking_documents.py green with the open set = later sections' ids only.
- **G3 WP end (WE):** every row of the WP closed; the WP's closeout test green; ROADMAP section with measurements.
- **G4 final (WP-50 WE):** gallery regenerated and signed off; `make test` at most 5 minutes or the measured bottleneck recorded (PRD §8); no open S1/S2 entry outside the natscale residual.

## Appendix A -- every audit item, binding for 33-01

Kind: **Fix** (closed by code), **Document** (closed by a help note; M10, M8, M12), **Partly** (fix + residual), **Withdrawn** (not registered in GAPS4.md or BUGS.md; no text kept). Sev per PD-2.

### WP-33 · Verification corpus and README gallery (P13)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| TR-2 | -- | No picture comparison over a broad corpus (109 gr_example commands run here only once, by hand) | S2 | 33-14 | Fix |
| TR-11 | -- | value_truth.json (311 twoway answers) is never compared with dash probe by probe | S2 | 33-10 | Fix |
| TR-23 | -- | No green strict batch-end run is recorded on HEAD; TestBounds (4 runs) always skips, so DASH_STRICT=1 cannot pass | S2 | 33-11 | Fix |
| BY-23 | BY-31 | Per-type by() drawing is pinned against twoway only for function (default range) and lpoly | S2 | 33-12 | Fix |
| stat:PT-23 | -- | Estimator combinations with no truth (all matched when measured): lfitci [pw], lpoly degree >=4, weighted kdensity boundary, combined lowess flags, histogram discrete [fw] ... | S2 | 33-13 | Fix |
| CV-16 | -- | colorvar fixtures never compare key texts, order or frames; non-scatter options and interactions are unmeasured; disc_levels_price_4 passes vacuously | S2 | 33-13 | Fix |
| syn:SD-20 | -- | About 89 options' abbreviation bindings are unmeasured; abbrev_truth wrongly says twoway has no bgcolor() | S2 | 33-10 | Fix |
| GW-11 | -- | scale() frame geometry is never compared with truth; the help wrongly says gaps are not scaled | S2 | 33-11 | Fix |
| BY-24 | -- | by() title/note/caption under position() has truth only for caption pos(5) | S2 | 33-12 | Fix |

### WP-34 · Default drawing of common graphs (P1)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| AX-4 | VF-1, DG-2 | The histogram bin axis is ticked over the bar edges; twoway ticks it over the first and last bin midpoints | S1 | 34-01 | Fix |
| AX-2 | TR-3, BY-26 | by() panels tick x1 at the scheme's #5; twoway's by() styles set xlabels(#4) ylabels(#4) | S1 | 34-02 | Fix |
| AX-1 | -- | xscale/yscale(range()) beyond the data widens the default ticks; twoway ticks only the data | S1 | 34-03 | Fix |
| VF-2 | TR-24 | A by() graph's shared y title is never painted (its cell canvas is 1 px tall) | S1 | 34-02 | Fix |
| VF-3 | ST-12 | aspectratio() with xsize()/ysize(): the fixed frame is ignored by BokehJS (aspectratio(2) xsize(8) ysize(4) draws a 0 px plot), and a Bokeh E-1023 ERROR line is printed | S1 | 34-04 | Fix |
| PIC-1 | RH-14 | A default area plot (and its legend key) has no outline in any scheme | S1 | 34-05 | Fix |
| PIC-3 | -- | A ci type with nofit still uses two plot numbers, so every later layer takes the wrong p# style | S1 | 34-06 | Fix |
| TR-4 | -- | A date axis loses Stata's ticks when the layer's first or last row has a missing y (every L./D. operator, any series with a missing end) | S1 | 34-07 | Fix |
| DG-3 | -- | a(b)c label and tick rules that cross zero print floating-point residue ('5.551e-17') as the zero label | S1 | 34-08 | Fix |
| AX-3 | TR-5, TR-12, DT-27, VF-10, CV-13 | Axes drawn at build from dash's natscale model, not Stata's: the by() count 4, mtick/mlabel #N, fit/kdensity/function/immediate ranges, the qfitci//scatter overlay, and the colour key's levels | S1 | 34-09 | Fix |
| plot:PT-13 | AX-20, syn:SD-21, VF-9, BY-25, sil:SD-16 | Open entry: the natscale model misses 3 of 264 axes after a filter move or without embedded ticks | S2 | 34-09 | Partly |

### WP-35 · Accepted syntax and refusals (P11, with P4's remaining items)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| MS-1 | stat:PT-3 | Repeated options twoway takes rightmost are refused r(198): yvarlabel, xvarlabel, mlabprefix, mlabsuffix, lalign, mlabstyle (and yvarl) given twice, and repeated contour levels(), ccuts(), ccolors(), clabels(), format(), scolor/ecolor/crule/interp, clwidths/clpatterns | S2 | 35-01 | Fix |
| syn:SD-3 | -- | p1()..p20(): p3()-p19() are refused, and p1(), p2() and p20() are noted and not drawn | S2 | 35-02 | Fix |
| stat:PT-7 | syn:SD-6 | lowess m (twoway's documented minimum of mean) is refused | S2 | 35-03 | Fix |
| syn:SD-5 | -- | bwi() is refused on lowess, kdensity, lpoly and lpolyci | S2 | 35-03 | Fix |
| stat:PT-1 | TR-7 | histogram accepts bins()+width() and two of density/fraction/frequency/percent; twoway refuses | S2 | 35-04 | Fix |
| stat:PT-2 | -- | density, fraction, frequency and percent are accepted on every type; twoway takes them only on histogram | S2 | 35-04 | Fix |
| stat:PT-5 | -- | contour levels() 501-1000 and 500+ ccuts() are accepted where twoway refuses at draw time; the help says twoway takes any integer | S2 | 35-04 | Fix |
| stat:PT-13 | -- | contour abbreviations twoway documents (int(), i(), colorl, clp(), clw()) are refused or bound to other options | S2 | 35-03 | Fix |
| stat:PT-6 | -- | function subchar() is not honoured: subchar(t) fails r(111), and subchar(1t) is accepted with a note | S2 | 35-03 | Fix |
| stat:PT-8 | -- | lowess 'noweight weight' is accepted (twoway refuses), and bare weight is named although nothing changes | S2 | 35-04 | Fix |
| stat:PT-9 | -- | Edge values twoway takes are refused: mspline bands(-1), fpfitci n(0), lfit n(-1) | S2 | 35-03 | Fix |
| stat:PT-14 | DT-13 | bw() is accepted with a note on scatter/line/lfit and read as barwidth() on the bar family; twoway refuses it off the bandwidth types | S2 | 35-04 | Fix |
| basic:PT-8 | syn:SD-10 | Two omit* options are accepted with a note; twoway refuses 'option omitanymissomitallmiss not allowed' | S2 | 35-06 | Fix |
| basic:PT-9 | TR-9, stat:PT-10 | Value refusals use r(198) where twoway uses another code: base(abc) 4026, bin() 125/121/126, width() 125/121, start() 121, mlabel(make..) 101, rbar barwidth(.) 199, mlabangle(1e308) 111 | S2 | 35-05 | Fix |
| basic:PT-13 | DT-17, DT-18, TR-17 | Values twoway draws are refused by dash's bounds: jitter(-3/150/abc), jitterseed(-1), barwidth(0/-1), aspectratio(-1), lwidth(-1) on scatter, msangle(400) on line, msize(1e400); lwidth(*40000) noted where twoway refuses | S2 | 35-05 | Fix |
| DT-15 | DT-16, syn:SD-18 | Accepted where twoway refuses: kernel(GAUSSIAN), xsize(()), an empty-colorvar if, and about 35 dash-only words (ytitle2(), xlabel2(), mlg(), marker(), malpha(), jseed(), plotbgcolor(), hover(), table ...) | S2 | 35-07 | Fix per the Q8 per-word ruling |
| syn:SD-7 | -- | ty() on lfitci/qfitci/fpfitci/lpolyci is refused; twoway refuses only the full word type | S2 | 35-03 | Fix |
| syn:SD-8 | -- | Factor-variable notation in by()/colorvar(c.) gives r(111) where twoway gives r(101); mlabel(45) gives r(111) where twoway gives r(198) | S2 | 35-06 | Fix |
| GW-2 | -- | aspectratio() with xoverhangs/yoverhangs is accepted; twoway refuses r(198) | S2 | 35-06 | Fix |
| GW-3 | -- | maxaxes() is never checked: maxaxes(x)/(2.5) accepted, maxaxes(1) with yaxis(2) drawn | S2 | 35-06 | Fix |
| GW-4 | -- | fxsiz()/fysiz() (twoway's abbreviations) are noted and not applied | S2 | 35-06 | Fix |
| sil:SD-8 | -- | title() with notitling is accepted with a note; twoway fails r(4018) | S2 | 35-06 | Fix |
| DT-19 | -- | Variables named __dash* give r(110); dash's working columns can give r(900) at c(maxvar) | S2 | 35-08 | Fix |
| plot:PT-3 | basic:PT-14, DT-14 | Plot-type names are read in any case (SC, Hist, Contour) where twoway refuses capitalised abbreviations | S2 | 35-09 | Fix |
| plot:PT-4 | syn:SD-2 | The empty graph is drawn with two black axes and takes axis options twoway refuses ('xlabels() not allowed, xaxis1 does not exist') | S2 | 35-09 | Fix |
| syn:SD-1 | -- | A bare plot after a parenthesised group, '(scatter ..) line ..', is refused; twoway draws it | S2 | 35-09 | Fix |
| syn:SD-13 | -- | A // inside one group with no graph options, '(scatter .. // line ..)', is refused; twoway draws both | S2 | 35-09 | Fix |

### WP-36 · Python discovery and environment (P2)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| plat:PT-1 | -- | dash and dash_setup refuse a Python that Stata found by itself (python_exec never set), and the remedy loops back to the same refusal | S2 | 36-01 | Fix |
| plat:PT-5 | TR-20, ECO-17 | Windows, Linux, Intel macOS and GUI Stata have never run dash; the opener and os.name branches are simulated only; the runners are POSIX sh | S2 | 36-04 | Document |
| plat:PT-3 | -- | (withdrawn; not registered, no text kept) | -- | -- | Withdrawn (Q48) |
| plat:PT-4 | -- | Named graphs with function layers are capped by c(macrolen); BE's fixed 264,392 refuses two n(10000) layers, and the advice 'set maxvar' is impossible on BE | S2 | 36-03 | Fix |
| plat:PT-2 | -- | The version floor is Stata 19 (r(9)); twoway runs on Stata 8 and later | S2 | 36-04 | Document |
| plat:PT-11 | ECO-17 | Python 3.11+ with bokeh 3.8-3.9, numpy and pandas is required; no conda guidance; dash_setup reports an old numpy/pandas as unmet and does not upgrade it | S2 | 36-04 | Document |
| plat:PT-12 | -- | The hash-pinned lock covers Python 3.11-3.14 on five platform tags: Python 3.15 and Windows ARM64 (tzdata) fail, and there is no offline wheelhouse route | S2 | 36-04 | Document |
| plat:PT-6 | -- | saving() with ~ on Windows: dash expands only '~/' from HOME and treats '~\' as relative | S2 | 36-04 | Document |
| plat:PT-16 | -- | 'Works offline in any modern browser' is verified on Chrome only (Firefox once by hand, Safari never); bokeh 3.10+ unverified | S2 | 36-04 | Document |
| plat:PT-14 | -- | Large data: about 6-8 s and 1.4 GB of Stata RSS per million rows; page columns are JSON number lists, about twice the base64 size | S2 | 36-04 | Document |
| DG-14 | -- | WebGL above 10,000 dataset rows: thick dashed lines draw speckled; the switch counts the dataset's rows, not the graph's | S2 | 36-02 | Fix |

### WP-37 · Statistical and computed layers (P12)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| DG-1 | -- | contour over zero observations crashes with a Python traceback, r(7102) | S2 | 37-01 | Fix |
| DG-5 | -- | rarea with cmissing(n) draws its bound outlines across the gaps | S2 | 37-02 | Fix |
| TR-13 | stat:PT-19, sil:SD-19 | contour above 1,000 distinct points fits a seeded subsample on a 100x100 grid (every sandstone help example); a repeated node keeps the smallest z; a different polygon cutter | S2 | 37-03 | Fix |
| DG-8 | -- | A contour with no surface (two observations) draws no colour key | S2 | 37-02 | Fix |
| stat:PT-12 | -- | xlog/xtransform() on lfit/lfitci are noted and the straight line drawn; twoway fits the transformed x | S2 | 37-04 | Fix |
| stat:PT-16 | -- | lpolyci at zero-df grid points: dash pinches to zero width where twoway draws a huge band that rescales y; the help calls it round-off | S2 | 37-05 | Document |
| DT-26 | -- | Documented numeric limits: lpoly bandwidth about 1% off at degree 6-7, degree above 7 differs (484.23 vs 400.94), exact-polynomial cases, fpfit date-time model choice, ndots thinning above 2,000,000 | S2 | 37-05 | Document |
| stat:PT-21 | BY-30, DG-16 | Tied sort keys keep data order; twoway's order among ties is unstable (lowess drawn path, sort with by(), cmissing breaks) | S2 | 37-05 | Document |

### WP-38 · Stata graph integration, documented (P3)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| syn:SD-17 | ECO-3 | name() registers the graph instead of drawing it, and saving() beside name() writes nothing; a do-file that names every graph produces no output | S2 | 38-01 | Document |
| GW-12 | ECO-2, plat:PT-13, TR-16 | A dashboard is not a Stata graph: graph export/save/display/combine, putdocx, putpdf, putexcel, dyndoc and markdown cannot use it; graph export writes a stale graph or r(601) | S2 | 38-01 | Document |
| ECO-1 | -- | A registered graph draws the data in memory at dash build, not at registration: preserve/collapse + name() + restore draws the restored data with no note; tempvar and frame graphs fail with r(111) | S2 | 38-01 | Document |
| ECO-4 | -- | graph combine has no full counterpart: dash build refuses xcommon, ycommon, cols(), holes(), colfirst, iscale(), imargin(), note(), caption() and xsize(), and the help never maps combine to layout() | S2 | 38-01 | Document |
| GW-13 | ECO-6, ECO-12 | name(): at most 22 characters and no '__'; a duplicate name gives r(198) in dash's words where twoway gives r(110) 'graph X already exists' | S2 | 38-02 | Document |
| GW-14 | ECO-13 | saving() onto an existing file gives r(198) where twoway gives r(602); twoway's '(file x.gph not found)' note is missing | S2 | 38-02 | Document |
| GW-15 | -- | nodraw with saving(, asis) writes the page where twoway gives r(601) | S2 | 38-02 | Document |
| GW-16 | ECO-14 | play() refuses a readable recording (r(198)); there is no Graph Editor | S2 | 38-02 | Document |
| GW-9 | -- | name(g, rep) or another bad sub-option gives a garbled 'invalid graph name g??rep' where twoway says 'option rep not allowed' | S2 | 38-02 | Document |
| ECO-5 | -- | 'dash clear g2' clears the whole registry (no syntax check); there is no dir/describe/drop for registered items | S2 | 38-02 | Document |
| ECO-15 | -- | Each one-line command opens a new browser page; only the newest five previews are kept; saving() opens none | S2 | 38-01 | Document |
| ECO-7 | -- | dash leaves internal s() macros (s(_recast_type), s(g_saving), s(g_name)); twoway clears s() | S2 | 38-01 | Document |

### WP-39 (removed; P4's items moved to WP-35, plot:PT-10 withdrawn)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| plot:PT-10 | -- | (withdrawn; not registered, no text kept) | -- | -- | Withdrawn (A2) |

### WP-40 · Resource limits (P5)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| plat:PT-8 | syn:SD-16, sil:SD-22 | r(134) above 5M embedded cells (hard ceiling 20M, about 10M obs for one y and one x), 100 plots, 10,000 reflines and 1,000 added texts | S2 | 40-02 | Document |
| plat:PT-7 | DG-15 | The cell cap counts _N whatever if/in select (the qualifier adds a column), so 'in 1/100' on 3M obs is refused although the page embeds only the selected rows | S2 | 40-01 | Fix |
| plat:PT-9 | -- | The plot limit is per graph, not twoway's 100 variables per plot: dash takes y1-y100 x (twoway r(103)) and refuses (y1-y60 x)(y61-y120 x), which twoway draws | S2 | 40-02 | Document |
| plat:PT-10 | BY-22 | by() draws the first 100 groups (ceiling 1,000), with a note | S2 | 40-02 | Document |
| stat:PT-15 | DT-17 | n() above 10,000 and bin() above 1,000 are refused; lpoly degree() above 30 is fitted at a lower degree | S2 | 40-02 | Document |
| sil:SD-1 | -- | histogram width() or discrete needing more than 1,000 bins (empty ones counted) is rebinned: width() is dropped, and discrete is squeezed into 1,000 bars | S2 | 40-02 | Document |
| AX-16 | sil:SD-10 | An axis option asking for more than 2,000 ticks keeps the default ticks; #N above 2,000 is clamped silently | S2 | 40-02 | Document |
| sil:SD-11 | -- | msize() above 1,000 units is drawn at the default with 'not a recognised size'; the help says any number | S2 | 40-02 | Document |
| sil:SD-12 | -- | fpfit/fpfitci above 20,000 distinct x is evaluated on a linspace grid, silently | S2 | 40-02 | Document |
| sil:SD-13 | -- | text() whose globals expand past 4,000 characters is refused r(198) | S2 | 40-02 | Document |

### WP-41 · by() fidelity (P6)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| BY-28 | -- | contour/contourline under by() cuts each panel at its own z ticks; twoway uses one shared z axis, so the same colour means a different z per panel | S2 | 41-01 | Fix |
| BY-1 | -- | by()'s note(), caption() and subtitle() with ring(0) are dropped silently ('Graphs by' vanishes too) | S2 | 41-02 | Fix |
| BY-2 | BY-29, BY-11 | A scale() written outside by() scales every panel, where twoway ignores it on a by() graph; by(, scale()), which twoway applies, is named and ignored | S2 | 41-03 | Fix |
| BY-27 | -- | function range(varname) under by() spans the whole data in every panel; twoway uses each panel's own range (kdensity range(varname) likely the same, unprobed) | S2 | 41-03 | Fix |
| BY-3 | -- | An at() hole for a legend or colour key that is not drawn is not reserved in the grid | S2 | 41-04 | Fix |
| BY-4 | sil:SD-2 | compact: beside an explicit style() it is drawn compact (twoway lets style() win), and its black plot-region and label-box outlines are not drawn | S2 | 41-05 | Fix |
| BY-5 | -- | aspectratio() with by(, shrink) is accepted; twoway refuses it ('options aspect() and shrink may not be combined') | S2 | 41-05 | Fix |
| BY-6 | -- | by(, total) with no variables gives r(198) in dash's words; twoway gives r(100) 'varlist required in by()' | S2 | 41-05 | Fix |
| BY-12 | -- | by(, l1title() b1title() t1title() ...) are named and ignored; in twoway l1title/b1title replace the shared axis titles | S2 | 41-02 | Fix |
| BY-13 | -- | by(, legloc() clegloc() plegend() plegloc()) are named and ignored | S2 | 41-04 | Fix |
| BY-14 | -- | coloruseplegend under by(): plegend(on) draws nothing, and clegend(on) draws a discrete Legend with '(missing)' where twoway draws a colour-bar key | S2 | 41-04 | Fix |
| BY-10 | -- | Panel-label sub-options twoway draws are named: justification(), nobexpand, lwidth()/lpattern(), span, alignment(), linegap(), bmargin(), placement(), orientation() | S2 | 41-06 | Fix |
| BY-16 | BY-17 | by() panel labels: a date variable is written as dates (twoway writes 14610); a value label holding double quotes stays one line | S2 | 41-06 | Fix |
| BY-18 | BY-19, BY-20, BY-21 | Documented by() layout differences: style(combine) on by()'s grid; clock 3/9 labels and titles below instead of beside; aspectratio() shapes each panel figure, not its plot region; a smaller graph margin insets nothing | S2 | 41-05 | Fix |
| VF-6 | -- | by() panels in the first column have narrower plot regions (y labels inside their canvas), so pixels per unit differ across a row | S2 | 41-05 | Fix |
| GW-5 | -- | xoverhangs/yoverhangs move panel borders under by() (twoway ignores them there) and use every label, not only the end labels, raising both sides equally | S2 | 41-05 | Fix |
| sil:SD-7 | -- | A weighted layer under by() with a panel whose weights are all zero is drawn; twoway stops with r(198) | S2 | 41-03 | Fix |
| PIC-13 | -- | A legend in a by() at() hole keeps full-size text; twoway scales it (0.85x) | S2 | 41-04 | Fix |
| BY-7 | BY-15 | by(, legend(pos(abc))) gives no note and the wrong side; by(, bgcolor()) is named although nothing visible changes under stcolor | S2 | 41-02 | Fix |
| TR-19 | -- | Residuals in closed by()/span entries are filed nowhere: 'panel row taller than its panels (unfiled)', by(clegend(pos(6))) keeps panel proportions | S2 | 41-02 | Fix |

### WP-42 · Colour variables (P7)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| CV-8 | DT-22, sil:SD-20 | An unbinned numeric colorvar() on 17 non-line types is a 256-step gradient with a ColorBar; twoway bins at the z ticks with a stepped key (mono schemes start near white) | S2 | 42-01 | Fix |
| CV-1 | -- | colorfillonly strips the level colour from every line part (line, connected, spike, dropline, rcapsym, pc shafts and heads) | S2 | 42-02 | Fix |
| CV-3 | -- | The discrete/binned clegend differs: ascending top to bottom, value labels and interval texts instead of a z axis, an extra '(missing)'/otherlabel entry, circles for every type, a frame | S2 | 42-03 | Fix |
| CV-4 | -- | The coloruseplegend key: ascending order, '(missing)' for 'Other', an extra title, value labels; legend() sub-options and colorkeysrange applied | S2 | 42-04 | Fix |
| CV-2 | -- | colordiscrete with colorlevels(k) makes k-1 cuts at range/k; twoway makes k cuts at range/(k+1) | S2 | 42-05 | Fix |
| CV-5 | -- | legend(size()) and legend(rows()/cols()) restyle the colour key; twoway's key ignores them | S2 | 42-04 | Fix |
| CV-6 | -- | Two colorvar layers: dash draws a key per layer and no plot legend; twoway draws the last layer's key plus a plot legend | S2 | 42-02 | Fix |
| CV-7 | -- | A colorvar layer's plot-legend swatch takes row 0's level colour, not its pstyle colour | S2 | 42-02 | Fix |
| CV-11 | CV-12 | colorkeysreverse reverses entries and labels (twoway reverses colours only); colorlevels() over one value prints nonsense intervals | S2 | 42-04 | Fix |
| CV-9 | syn:SD-9 | colorvar refusals differ in rc or words: colorcuts(abc) r(198) vs r(121); colorvar(a b) r(198) vs r(101); colorvar(pri*) accepted vs r(198); colorlevels(abc) and nosuch in dash's words | S2 | 42-05 | Fix |
| CV-10 | LT-14 | Malformed clegend(bogus), plegend(bogus), zlabel(bogus) and zscale(bogus) are drawn with a note (garbled 'using not drawn') where twoway refuses r(198) | S2 | 42-05 | Fix |
| CV-14 | -- | Documented acceptances: string colorvar, colpalette()/colornlevels()/colormissing(), cv()/colv(), an empty layer drawing no key, '(missing)' for all-missing | S2 | 42-05 | Fix or Document per the Q8 per-word ruling |
| CV-15 | LT-23 | On a discrete key, zlabel() and zscale() are named and not drawn; clegend() altaxis, region(), bplacement(), bmargin(), subtitle(), note() and caption() are named as 'not a recognised sub-option' | S2 | 42-03 | Fix |
| LT-12 | -- | clegend(title()) replaces the z title and prints the raw option text when it has sub-options ('"Z", box') | S2 | 42-03 | Fix |
| AX-12 | syn:SD-4 | The z tick family: zlabels/zticks/zmlabels/zmticks are refused (twoway takes them); ztick(), zmlabel() and zmtick() are noted and not drawn, and are absent from the Unsupported list | S2 | 42-03 | Fix |
| sil:SD-4 | sil:SD-14 | The colour bar is a fixed 12 px (twoway uses the scheme's clegend_width, about 23 px); the scheme contour keys (outline, colorlines, reversekey, levels) are never read | S2 | 42-01 | Fix |
| LT-22 | -- | contourline with colorlines draws no level legend; plain contourline gets a needless note; the contour key title sits above with no axis line | S2 | 42-03 | Fix |

### WP-43 · Legend, titles and added text (P8)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| LT-1 | -- | legend(title()/subtitle()) are drawn at key-text size and colour, not the scheme's leg_title/leg_subtitle styles | S2 | 43-01 | Fix |
| LT-4 | ST-1 (bplacement part) | legend(ring(0) bplacement()) ignores bplacement; bplacement abbreviations (nor, nea, t, top) are not read | S2 | 43-02 | Fix |
| LT-2 | -- | legend(nobox) removes the region box; in twoway nobox is the key-text textbox option and changes nothing | S2 | 43-03 | Fix |
| LT-3 | -- | Key-text textbox options are not drawn: box (silent), bcolor(), fcolor(), justification(), alignment(), margin(), linegap(), tstyle() | S2 | 43-03 | Fix |
| LT-5 | -- | legend(all), draw and nodraw are named: whether a legend appears, and how keys merge, differ | S2 | 43-02 | Fix |
| LT-6 | -- | Legend layout sub-options named: style(), width(), height(), xoffset(), yoffset(), showindex, region(style()/lstyle()/lalign()) | S2 | 43-03 | Fix |
| LT-7 | -- | bexpand on legend() and on title/subtitle/note/caption is taken silently where twoway widens the box | S2 | 43-03 | Fix |
| LT-8 | -- | A title box under stcolor is filled #d9e6eb (the added-text fill), not textbox white with a 6.48 line | S2 | 43-05 | Fix |
| LT-9 | -- | A fractional ring() (7.5, 4.5) or ring(100) is dropped silently | S2 | 43-05 | Fix |
| LT-10 | -- | Numeric marginstyle forms (# # # #, l=#, l+#) are refused for textbox margins; legend region margin collapses four sides to the largest | S2 | 43-03 | Fix |
| LT-11 | -- | text(..., alignment()) is noted and not drawn, though the help, CHANGELOG and WP-32 say it is drawn | S2 | 43-06 | Fix |
| LT-13 | -- | legend(t1title() ... b2title()) is accepted and named where twoway refuses r(198) | S2 | 43-01 | Fix |
| LT-14 | -- | title(..., ring(x)) is accepted silently where twoway prints notes and refuses r(198) | S2 | 43-05 | Fix |
| LT-15 | -- | legend title()/subtitle() sub-options (position(), box ...) are dropped silently; subtitle size()/color() are ignored | S2 | 43-01 | Fix |
| LT-16 | ST-8 | title/subtitle/note/caption placement() at ring(0) is drawn as a Label anchor (n lifts the box out of the plot) and long names, clocks and synonyms are ignored | S2 | 43-05 | Fix |
| LT-17 | -- | legend(holes()) with cols(1) inserts a full blank row | S2 | 43-02 | Fix |
| LT-18 | ST-18 | Title box sub-options named: orientation(), width(), height(), angle(), lstyle(), bl*, lalign(), style(); clocks 2-4/8-10 drawn above or below (style() and lalign() missing from the help list) | S2 | 43-05 | Fix |
| LT-19 | -- | Edge titles draw no box, justification(), margin() or tstyle() | S2 | 43-05 | Fix |
| LT-20 | GW-21 | text() draws no width(), height(), linegap(), bexpand, bmargin(), lstyle(), lpattern(), lalign(); a `=exp' global is drawn literally | S2 | 43-06 | Fix |
| LT-21 | VF-8, PIC-14 | Legend keys: marker at 0.4 of the box, not the marker's size; textfirst, stacked, symplacement() and the legend's own note()/caption() not drawn; at 384 px an economist 3-column legend clips its labels (undocumented) | S2 | 43-04 | Fix |
| PIC-11 | -- | Legend key shapes of rcap, rcapsym, pccapsym, dropline, pcarrow, pcbarrow and rarea are wrong | S2 | 43-04 | Fix |
| MS-10 | -- | Keys are merged when two different pstyles look alike (s1mono line v6/v14, v12/v15) | S2 | 43-04 | Fix |
| ST-14 | TR-14, DG-17, PIC-18 | Partial SMCL markup ({bf:}, {it:}, {sup:} on letters, fonts) in titles, labels and keys is drawn in one plain style | S2 | 43-07 | Fix |
| LT-24 | -- | title("'90s") is drawn where twoway gives r(100) | S2 | 43-05 | Fix |
| RH-13 | -- | A horizontal kdensity (and function) is keyed by its name; twoway keys it by the grid variable 'x' | S2 | 43-04 | Fix |

### WP-44 · Axes (P9)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| AX-13 | ST-13 | Axis title textbox sub-options other than size/color are named: orientation() (Bokeh axis_label_orientation never set), justification(), placement(), box, margin() ... | S2 | 44-01 | Fix |
| AX-5 | -- | custom on xlabel()/ylabel() is ignored: its styles reach every label and the grid; custom with no list is accepted (twoway r(198)) | S2 | 44-02 | Fix |
| AX-6 | -- | Gridlines of xtick()/xmtick() are drawn in the minor style (dotted); twoway uses the major gridstyle | S2 | 44-02 | Fix |
| AX-7 | -- | yscale(off fill) is drawn as off; twoway keeps the axis's space | S2 | 44-03 | Fix |
| AX-8 | -- | Label sub-options twoway draws are named: labelminlen(), noshowlabels/showlabels, nopgmgrid/pgmgrid, style(); showlabels nolabels hides labels | S2 | 44-02 | Fix |
| AX-9 | sil:SD-5 | xscale/yscale atanh, logit, log1m and style() are named and drawn linear | S2 | 44-03 | Fix |
| AX-10 | -- | Contradictory transforms in one copy (log nolog, atanh log) are accepted; twoway refuses r(198) | S2 | 44-03 | Fix |
| AX-11 | -- | A log axis over data with non-positive values is ticked over positive values only (twoway's whole drawing is degenerate there) | S2 | 44-03 | Fix |
| AX-14 | -- | tstyle(), labstyle(), gstyle(), tlstyle(), glstyle() and nogextend are named | S2 | 44-02 | Fix |
| AX-15 | AX-17, AX-19 | Documented: xtick and xmtick share one tick length; out-of-range reflines are clipped from the margin; string/hex formats drawn %9.0g, dates past the browser range, margin fixed at build | S2 | 44-02 | Fix |
| AX-18 | stat:PT-20, VF-12 | A date axis is kept where twoway labels Stata numbers (first layer lfit/qfit/ci/kdensity/lpoly/function/immediates); xscale(log) on a date axis is drawn linear | S2 | 44-04 | Fix |
| MS-14 | -- | xscale(range()) on a log axis adds a tick at the range end | S2 | 44-03 | Fix |
| MS-12 | -- | A graph whose only plot is on yaxis(2) is drawn with y gridlines; twoway draws none | S2 | 44-05 | Fix |
| MS-11 | RH-17 | twoway's '<first title>...' x title (different x across y-axis groups, or upright plus turned layers) is not drawn | S2 | 44-01 | Fix |
| MS-13 | -- | ytitle(A) ytitle(B, suffix) is joined on one line; twoway draws two lines for axis titles | S2 | 44-01 | Fix |
| PIC-12 | -- | A right-hand y title reads top to bottom; twoway's reads upward (every economist graph, any yaxis(2)) | S2 | 44-01 | Fix |
| DG-6 | -- | %tC ticks are placed and labelled in leap-second-corrected time (22 s off in 2001) | S2 | 44-04 | Fix |
| DG-4 | -- | Parenthesised dates holding blanks ((1 jan 2001)) are refused in tlabel(), tline() and tscale(range()) | S2 | 44-04 | Fix |
| DG-9 | TR-8 | A non-number in a label list (.a, a bare word) is noted and drawn; twoway refuses 'invalid label specifier' | S2 | 44-05 | Fix |
| DG-13 | DG-11 | ylabel(minmax) on an empty scale draws Bokeh's default ticks; data spanning about ±8e307 give an OverflowError traceback (twoway gives r(199)) | S2 | 44-03 | Fix |

### WP-45 · Schemes, styles and figure geometry (P10)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| PIC-4 | -- | economist: a graph's note() is never painted (the Label targets a Title Node BokehJS does not resolve) | S2 | 45-01 | Fix |
| PIC-7 | PIC-8 | economist widths: range, spike, dropline and pc lines at 1.2 (linewidth p) where twoway uses pother 0.8; the rarea outline at 0.8 centred where twoway uses parea 0.2 inside | S2 | 45-01 | Fix |
| ST-1 | ST-2, ST-3, ST-4, ST-5, ST-6, ST-11 | Style-word abbreviations and names twoway reads are not read: compass2dir (nor, N, rig ...), tb_orientstyle (hor, vertic), clockdir names (top, bottom, left ...: title position(bottom) drawn above), gridringstyle (inside/outside; title ring(in) accepted where twoway refuses), anglestyle (v, rv, rh), connectstyle (st, up, no drawn direct); twoway-worded notes are invented for them, and justification(l)'s note is missing | S2 | 45-02 | Fix |
| ST-7 | -- | Leaf style files on the ado-path (linepattern, linewidth, symbolsize, gsize, intensity, anglestyle, margin) are not read | S2 | 45-03 | Fix |
| ST-15 | GW-18 | color-*.style and textboxstyle-*.style files are not read (mcolor(mine) draws black) | S2 | 45-03 | Fix |
| ST-17 | GW-18 | Scheme directives read but not drawn: clockdir p/p#, title textboxstyle, legend_col_gap, title clocks 2-4/8-10; a scheme name must not be a path; files over 1 MB or linked out are skipped | S2 | 45-03 | Fix |
| ST-10 | -- | A shipped-name scheme placed before BASE (adopath ++) is ignored; dash always uses its own translation | S2 | 45-03 | Fix |
| ST-16 | GW-17 | An unknown scheme() is refused r(198) where twoway notes and draws s2color | S2 | 45-03 | Fix |
| GW-6 | VF-7 | The graph-region outline is not stroked by default, and the scheme's graph margin (3.5 units) is not drawn (Bokeh's 5 px min_border is used) | S2 | 45-04 | Fix |
| ST-21 | GW-19 | graphregion's inner box and region lalign() are named; ifcolor() fills the whole border; the plot margin is a share of the whole graph | S2 | 45-04 | Fix |
| VF-4 | GW-20, sil:SD-21, VF-5, VF-11 | Figure proportions: a lone graph fills the page width within a 160-560 px height band (2.14:1 at 1200 px where twoway is 1.667:1; xsize()/ysize()/aspectratio() alone change nothing); relative sizes are a fixed 2.88 pt (0.889x twoway under stcolor); fxsize()/fysize() shrink the cell | S2 | 45-04 | Fix |
| GW-1 | -- | xsize()/ysize() with units (10cm, 3in, 200pt) are ignored with a note that leaks 'None' | S2 | 45-04 | Fix |
| ST-22 | -- | Colour edges: navy*52 intensity rule, blank stylelist element refused in dash's words | S2 | 45-05 | Fix |
| GW-10 | -- | graph set window/svg fontface for plain text is not read (only stSans/stSerif/stMono tags) | S2 | 45-05 | Fix |

### WP-46 · recast() and horizontal (P14)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| RH-1 | RH-2 | A range source recast to line/scatter/connected refuses horizontal/vertical (twoway turns it); recast to bar/area/spike/dropline/dot with horizontal is turned by dash where twoway draws it upright | S3 | 46-01 | Fix |
| RH-3 | RH-4 | A range source or ciplot() drawn as a yx type leaves the second bound out of the axis, the default title and the key | S3 | 46-02 | Fix |
| RH-5 | RH-6, RH-7 | histogram recast(): drawn in the target's style (twoway keeps the histogram style), bars one unit wide (twoway uses the bin width), and 0 left out of the height axis | S3 | 46-02 | Fix |
| RH-8 | -- | histogram/rbar with recast() plus horizontal: twoway draws a broken swapped serset; dash draws a clean transpose | S3 | 46-02 | Document |
| RH-9 | RH-10, RH-12 | Orientation flags judged differently: dot with a non-bar recast takes h/v (twoway refuses); scatteri recast to bar-like refuses h/v (twoway turns it); recast(b)/(ba) takes h/v and draws p1bar (twoway refuses and draws p1) | S3 | 46-01 | Fix |
| RH-11 | -- | Abbreviated yx names on y2xtype sources (sc, li, co, b) are read as full names; twoway notes them and draws rspike | S3 | 46-01 | Fix |

### WP-47 · Plot-option fidelity (P15)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| basic:PT-1 | basic:PT-2, MS-6 | headlabel is ignored on pcscatter/pccapsym with mlabel() and on pcarrowi labels: labels stay at the first point | S3 | 47-01 | Fix |
| MS-7 | MS-8, MS-9 | Immediate-type labels: pci labels dropped under recast() with a false note; scatteri labels vanish under recast(); mlabel(nosuch) on scatteri is refused r(111) | S3 | 47-01 | Fix |
| MS-2 | TR-6 | yvarlabel()/xvarlabel() are ignored on scatteri, pci, pcarrowi, function, kdensity and histogram | S3 | 47-02 | Fix |
| MS-3 | MS-4 | yvarlabel("") gives the key 'scatter' and no title (twoway uses the variable name); yvarlabel relabels a variable in every plot in twoway, per layer in dash | S3 | 47-02 | Fix |
| MS-5 | -- | xvarformat()/yvarformat() do not reach marker labels of the plotted variable | S3 | 47-02 | Fix |
| basic:PT-3 | -- | mlabel(t*) naming several variables draws labels; twoway draws none | S3 | 47-02 | Fix |
| basic:PT-4 | sil:SD-3, PIC-15 | Outline alignment: twoway strokes bars, histogram bins, areas and rbar inside and honours lalign(); dash centres every stroke and calls lalign() 'the same picture'; rcap caps butt-ended, not round | S3 | 47-03 | Fix |
| basic:PT-6 | -- | mlalign(center) and inside draw one picture; the default marker is probably twoway's center picture | S3 | 47-03 | Fix |
| basic:PT-5 | -- | dlalign(center/outside) changes dot size in twoway; dash drops it silently (tw_silent built from one default value) | S3 | 47-03 | Fix |
| basic:PT-7 | -- | (withdrawn; not registered, no text kept) | -- | -- | Withdrawn (Q50) |
| basic:PT-10 | syn:SD-11, sil:SD-17, ST-20, DT-20 | Spellings twoway draws as other options are only noted: symbol(), msymangle(), mlabels(), bcolor(), bfintensity(), blwidth(), blpattern(), afcolor(), afintensity(), bsymbol(), bmsize() on arrows (= barbsize) | S3 | 47-04 | Fix |
| basic:PT-11 | TR-18, DT-20, sil:SD-17, ST-20 | Noted options twoway draws: back markers (bm*), alalign/blalign, mlabalignment, mlabjustification, bartype(spanning), dropto(), numkeys(), omitanymiss on multi-y, dlpattern(), xtransform, onepanel etc. | S3 | 47-05 | Fix |
| PIC-2 | PIC-5, PIC-6, ST-19, ST-9 | Marker shapes: diamonds 2/3 as wide; V/v closed triangles (help says open chevron); + filled fat cross; arrow symbols without shaft; msymbol(invisible) draws nothing (twoway notes and draws the default) | S3 | 47-06 | Fix |
| PIC-9 | -- | Empty histogram bins draw an outline segment along the base | S3 | 47-06 | Fix |
| PIC-10 | -- | dot draws no row for an observation whose y is missing (dotextend yes); twoway draws the full row | S3 | 47-06 | Fix |
| DG-12 | -- | Markers with missing or zero weight are invisible; twoway still draws a dot | S3 | 47-06 | Fix |
| PIC-16 | PIC-17 | Dot-plot dots floored to 1 px before the outline (0.46 vs 0.30 rs); dot patterns rounded to whole pixels | S3 | 47-06 | Fix |
| DG-7 | -- | Titles and keys of emptied or unfittable layers differ ('Fitted values' vs 'mpg', histogram x 'x') | S3 | 47-02 | Fix |
| basic:PT-15 | DT-23, DT-24, sil:SD-23 | Other documented drawing and text differences: rarea closing edges, half-missing pc rows, pcarrow mlabangle, date mlabel value labels, pci notes, side-clock titles, key marker size, fxsize, globals with =exp, browser date range, missing scheme keys | S3 | 47-06 | Fix |

### WP-48 · Help, README and tracker accuracy (P16)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| LT-27 | GW-24, syn:SD-14, ECO-10, DT-05, TR-21, sil:SD-15 | The 'typo is reported as ignored ... titel(x) appears in the note' paragraph is stale; the paragraph before it (xreverse, xcommon, lockaspect ... reach the note) is stale too | S3 | 48-01 | Fix |
| plot:PT-5 | ECO-9, DT-06 | 'graph is a prefix before twoway' / 'unrecognised plot type graph' is stale | S3 | 48-01 | Fix |
| basic:PT-16 | DT-07, DT-08, DT-09, DT-10, DT-11, DT-12, stat:PT-18, BY-9 | Stale passages: :332 and :3472-3475 headlabel/mangle 'named'; :3611 recast on dot; :3676 degree() >7 refused; :3977-3985 fpfit bwidth accepted; :4084 acolor named; :1239 mlabel(t*) refused; :240-246 shadowed x/y; :3635 merged keys; :3179 rescale note; :3290 subtitle box; :4782/:6573/:6597 lalign/dlalign/'every type'; TWOWAY_COVERAGE_AUDIT:71/81/84; _dot_style docstring; test_lpoly_degree.py:16 | S3 | 48-01 | Fix |
| GW-22 | GW-23 | Units paragraph says xsize/ysize do not change the size reference (they do); pcycle()/clegend() 'named in the note' when drawn | S3 | 48-01 | Fix |
| syn:SD-15 | -- | The Unsupported list is not checked against the tw_takes table, so p#(), ztick/zmlabel/zmtick are missing | S3 | 48-02 | Fix |
| RH-15 | -- | Horizontal/recast help claims ('as twoway draws it', 'judged after recast()', 'one x unit wide') are contradicted or undocumented differences | S3 | 48-02 | Fix |
| DT-29 | DT-30, TR-22 | dash_setup help contradicts itself on versions/ceilings; 0.1.0 CHANGELOG lists reversed behaviour; TWOWAY_COVERAGE_AUDIT rows stale; GAPS3 H5/I1/K1/K5 lack Tracked lines; DROPIN P2.34/P2.64 unmapped; rejected_options.json narratives | S3 | 48-03 | Fix |
| ECO-16 | ECO-8 | Help and README understate ecosystem losses (graph display/use/replay, putpdf, putexcel, markdown, iframe note unlinked); no recipes for commands that draw through twoway (histogram, marginsplot, sts graph) | S3 | 48-02 | Fix |
| DT-28 | syn:SD-19 | Reviewed and needing no change: HTML output is the package's premise; a zero-weight graph refused under nodraw matches the drawn twoway | S3 | 48-02 | Document |

### WP-49 · Messages and notes (P17)

| Lead id | Other ids | Item | Sev | Section | Kind |
|---|---|---|---|---|---|
| plot:PT-7 | GW-8, ECO-11, sil:SD-9, syn:SD-12, TR-10 | Refusals add a second line ('twoway does not take this option here', the after-comma hint, 'takes this option once') and a six-line Supported list; value refusals use dash's words; the full option name is printed instead of the typed spelling (bands() for ba()) | S3 | 49-01 | Fix |
| basic:PT-12 | stat:PT-11, stat:PT-8, AX-21, LT-26, BY-8, BY-15, GW-23 | Notes for options twoway draws the same picture with: afcolor on scatter, clalign, dlpattern on dot, bmsize on scatter, bargap, omitallmiss, onepanel, xlog on qfit, back/noback, heatlabel, zvarformat, nolog, noreverse, ring(), labelkeepleadingzero, legend nostack/angle/orientation, text angle/bexpand ('bexpand()' with parentheses), by() spacers/subtitle width | S3 | 49-02 | Fix |
| LT-25 | ST-11, basic:PT-17, BY-7, BY-8, GW-7 | Named-style notes: invented twoway-worded notes where twoway prints none; missing notes for clockdir 13 and justification(bogus); 'not a recognised size; using medium' instead of the gsize note; iscale(abc) note printed twice; xsize() bounds and graphsize notes in dash's words with 'None' | S3 | 49-02 | Fix |
| plot:PT-6 | plot:PT-8, DG-10 | Different words, same rc: tsline/tsrline without tsset; a weight glued to the type ('scatter[aw=price]'); a date tline() on a %tb axis | S3 | 49-01 | Fix |
| plot:PT-11 | stat:PT-22 | '_dash_dp_format() already exists' and '(11721 lines skipped)' are printed after discard and, in long sessions, mid-session | S3 | 49-02 | Fix |

## Appendix B -- the audit's false sentences (PD-8)

| HR | Sentence (audit :855-880) | Corrected by |
|---|---|---|
| HR-1 | dash.sthlp:156-157, :181-182 'accepts the same syntax as twoway' | 48-04 |
| HR-2 | dash.sthlp:185-187 and README.md:15-16 caveats: name() registers, no graph memory/export (help only); tested platform | 38-01 (help), 36-04 (platform, help and README) |
| HR-3 | README.md:6-8, dash.pkg:7-9 'Most twoway options are honoured; the rest are accepted and named in a note' | 48-04 |
| HR-4 | README.md:59 'every difference from twoway' | 48-04 |
| HR-5 | dash.sthlp:737-745, :995-997 sunflower named as a twoway plot type (and matamatrix()) | 35-09 (PD-10) |
| HR-6 | dash.sthlp:6459-6465 'a command copy-pasted from a do-file always runs' | 48-04 |
| HR-7 | dash.sthlp:286-289 'where dash differs, this file says so' | 48-04 |
| HR-8 | dash.sthlp:164-166 empty graph 'with axes' | 35-09 |
| HR-9 | dash.sthlp:172-174 'works offline in any modern browser' | 36-04 |
| HR-10 | dash.sthlp:4528-4529 (Stata's ticks at build; range() widens ticks), BUGS.md:4139-4143, ROADMAP.md:5153 'exact at build' | 34-03 (range), 34-09 (build) |
| HR-11 | dash.sthlp:4679 by() 'one fewer on y' | 34-02 |
| HR-12 | dash.sthlp:5670-5679, :5653-5655 aspectratio()/xsize() 'exactly as twoway does' | 34-04, 45-04 |
| HR-13 | dash.sthlp:4760-4763 yvarlabel/xvarlabel reach every title and key | 47-02 |
| HR-14 | dash.sthlp:3472-3475, :332 headlabel/mangle; :4782-4786 lalign; :6573-6577 dlalign; :6597-6600 'every plot type' | 47-01, 47-03, 48-01 |
| HR-15 | dash.sthlp:6041 area outline; :6069 V/v chevron; :6202-6205 economist note | 34-05, 47-06, 45-01 |
| HR-16 | dash.sthlp:372-386 horizontal; :596-598 levels(); :5359-5361 placement(); :4567-4568 custom; :4867 tick grid; :4617 fill | 48-02, 35-04, 43-05, 44-02, 44-02, 44-03 |
| HR-17 | dash.sthlp Differences item 5 and ~:1036 refusals 'as twoway refuses them', 'naming the option given' | 49-01 |
| HR-18 | dash.sthlp:3013-3016 the cap counts what the page embeds | 40-01 |
| HR-19 | dash.sthlp:5434, :5494 colordiscrete; :1177-1178 msize; :3990-3995 discrete one bar per value; :4192-4194 zero weight; :5687-5690 gaps not scaled | 42-05, 40-02, 40-02, 47-06, 33-11 |
| HR-20 | dash_setup.sthlp:41-43 and 'Python is required but is not available to Stata' | 36-01 |
| HR-21 | Differences should list resource limits, recast+horizontal quirks (the histogram tick rule and continuous colorvar are fixed; jitter and the Python requirement are not added, Q50, Q49) | 40-02, 46-02; checked by 48-04 |
| HR-22 | dash.sthlp:737-742 sunflower (D40) | 35-09 |

