# Traceability Matrix -- dash WP-33..WP-50

> Generated 2026-10-21 by UltraPlan Phase 5. Sources: `DISCOVERY.md` (Q1-Q58, A1-A3), `RESEARCH.md` (C1-C5), the audit's D40/D41, `review/DECISIONS.md` (P4-1..P4-10, P5-1..P5-3, A-1..A-28). Requirements were extracted by three tracers and every Missing/Partial row plus a one-in-six sample of Covered rows was checked adversarially (1 of 43 sampled Covered rows was downgraded, the gallery load target, resolved by P5-3).

## Summary

- Requirements traced: 292 (from Q1-Q58, A1-A3, C1-C5, D40/D41, P4-*, A-*).
- Covered: 269; Superseded by a later ruling: 23; Partial: 0; Missing: 0; Excluded by choice: 0.
- Audit items: 221 live items, each assigned to exactly one section and closed by a named closing task or commit boundary (table below); 3 withdrawn items are not registered (Q48, Q50, A2).
- Tasks: 509 across 92 sections; every task traces to an audit item, a ruling or the harness/tracking infrastructure they imply (scope-creep log below).

## Requirement-to-Task Mapping

| # | Requirement | Source | PRD | Plan sections | Task ids | Status | Note |
|---|---|---|---|---|---|---|---|
| REQ-B-01 | Measure twoway's zero-observation answer per plot type and per case (one empty plot among several, all plots empty, graph-wide if/in, by() with empty panels) before building the check | Q21 (C1) | §4 (WP-37) | 37-01 | 37-01-01 | Covered | Research [S] §3 ran 400 probes. 37-01-01 re-measures them with scripts/extract_zero_obs_truth.do (cases a, b1, b2, c, d, f, e1, e2; the g and g2 sets were removed by P5-2) into the committed fixture zero_obs_truth.json, and stops at a checkpoint if any type differs from [S] §3. |
| REQ-B-02 | One Stata-side zero-observation check copies twoway's measured answer for each type and case | Q21, C1, D40 P12 | §4 (WP-37) | 37-01 | 37-01-02, 37-01-03 | Covered | The Mata rule table _dash_zero_obs_rule is called by _dash_zero_obs_check (PD-15, M9). Cert case Q3701-1 proves the table equals the fixture. |
| REQ-B-03 | The help documents any remaining difference; C1 says no note is needed where dash matches | Q21, C1 | §5 | 37-01 | 37-01-04 | Covered | TR-37-01.7 adds sentences to dash.sthlp :340-355 and :505-524. They cover the build-time re-check, the plot line, empty contours and by() with literal types. No Differences entry is needed because dash matches twoway in every case. |
| REQ-B-04 | The zero-observation refusal is r(2000) "no observations" | Q22 | none | 37-01 | none | Superseded | Superseded by C1 (and M9). dash refuses with twoway's own rc and words per type: lpoly/lpolyci r(2000) "no observations"; fpfit/fpfitci, mband/mspline and an all-empty by() r(198). See REQ-B-47..51. |
| REQ-B-05 | Where dash refuses for want of observations, twoway's words come first, then a second line naming the plot's number and type | Q22, C1 (kept as M9), A-12 | none (index M9); §5 says only 'same errors, same return codes' | 37-01 | 37-01-02, 37-01-04 | Covered | _dash_zo_line (D-37-01.b, TR-37-01.4) prints the line on registration and export refusals. by() refusals name every plot (A-12). 37-01-04 flips the P1A pins. A stale note in 37-01 says 'RESEARCH C1 says superseded', but RESEARCH C1 now keeps Q22. The section follows M9 either way. |
| REQ-B-06 | P6-P10 items Bokeh cannot draw are documented under the help's Differences with a measured example, and the note stays | Q23, M11, A-5, A-15 | §4 (WP-41..45: document the three residuals), §5 | 43-04, 43-07, 44-02 | 43-04-04, 43-07-06, 44-02-08, 44-02-09 | Covered | Covered after A-26 (each residual has a measured example command: 43-04, 43-07) |
| REQ-B-07 | 'Supported by Bokeh' means built from shipped glyphs, annotations, tickers and CustomJS, composites included; on that definition every P6-P10 item is drawn | Q24, M11, D40 P6-P10 | §4 (WP-41..45) | 41-01..41-06, 42-01..42-05, 43-01..43-07, 44-01..44-05, 45-01..45-05 | index rule M11; 43-04-02, 43-07-02 (spikes proving the shipped-model + CustomJS route) | Covered | Research B found 0 of 97 items unsupported. The spike checkpoints escalate to the maintainer only if the shipped-model route fails. |
| REQ-B-08 | Exclusion: custom TypeScript extension models do not count and are not used | Q24 | §7 (no custom compiled Bokeh extensions) | none | none (exclusion; index M11) | Covered | A grep of all 92 section files and BRIEF finds no TypeScript or __implementation__ model. M11 and PRD §7 state the exclusion. |
| REQ-B-09 | RH-8: keep dash's clean transpose for histogram/rbar with recast() and horizontal | Q25, M12 | §4 (WP-46), §7 | 46-02 | 46-02-05 | Covered | Boundaries forbid any drawing change. 46-02-05 adds test_dash_draws_the_transpose as a guard of today's behaviour. PRD §7: twoway's broken picture is not copied. |
| REQ-B-10 | RH-8: list twoway's broken picture under Differences with a measured example | Q25 | §4 (WP-46) | 46-02 | 46-02-05, 46-02-06 | Covered | D-46-02.g / TR-46-02.9 add a Differences line and a Recast topic note with measured ranges (histogram recast(bar) horizontal x -5.47..5.53; rbar recast(rcap)). The item closes Documented, pinned by TestRecastHorizontalDifference and Q4602-3. |
| REQ-B-11 | Run twoway__contour_gen at registration so every contour's first drawing (above 1,000 points) is twoway's grid | Q26 | §4 (WP-37) | 37-03 | none | Superseded | Superseded by C3 (only on a full grid or with interp(none)) and M9 (run at export, not at registration; D-37-03.a). |
| REQ-B-12 | After a filter move dash refits a Stata-grid contour with its own fit and shows the stale cue | Q26 | none | 37-03 | 37-03-01, 37-03-03, 37-03-04 | Covered | Covered after A-26 (37-03: the saved page refits with the JS twin and shows the cue) |
| REQ-B-13 | lpolyci at zero-df grid points: correct the help to describe the difference accurately; Stata's compiled round-off is not reproduced | Q27, M9 | §4 (WP-37), §7 | 37-05 | 37-05-01, 37-05-02 | Covered | stat:PT-16 is documented with measured values (-50.75..74.75) and a Differences entry. D-37-05.a copies no arithmetic. |
| REQ-B-14 | P1 item 8: probe ts operators in twoway first; where twoway refuses a form dash accepts, refuse with twoway's rc and words; do operator work only where twoway draws | Q28, D41, M6, PD-16 | §4 (WP-34) | 34-07 | 34-07-01, 34-07-02, 34-07-03, 34-07-05 | Covered | 121 probes are re-measured and committed before any code changes. The 34-07-02 checkpoint stops for a ruling if anything differs. Research found dash's refusals already equal twoway's. |
| REQ-B-15 | Test-suite speed work is a separate WP-50, run after the package WPs | Q29, M3 | §1, §4 (WP-50) | 50-01, 50-02, 50-03, 50-04 | 50-01-01..50-04-04 | Covered | The index run order puts WP-50 last. 50-01 depends on WP-49's WE having closed. |
| REQ-B-16 | Quality: bring the ~40-minute gate toward CLAUDE.md's 5-minute target; make test at most 5 minutes, or the measured bottleneck recorded | Q29 (CLAUDE.md rule 11) | §4 (WP-50), §8, §10 risk 1 | 50-01, 50-02, 50-03, 50-04 | 50-01-02, 50-01-03, 50-02-02, 50-02-03, 50-03-02..50-03-05, 50-04-01..50-04-04; index G4 | Covered | The work profiles the suite, cuts cert load and pytest cost, re-measures, and records a verdict for maintainer sign-off. A-3 rules out consolidating truth scripts. |
| REQ-B-17 | Corpus comparison has its own make targets (make corpus / make gallery), run at the final closeout and on demand | Q30, M5, P4-8 | §8 (corpus re-run at the final closeout) | 33-08, 33-14 | 33-08-03, 33-14-02; index WE.7 | Covered | 33-08-03 adds both targets without running them. 33-14-02 runs make corpus once as the baseline. WE.7 runs make corpus && make gallery, the only gallery build (P4-8). |
| REQ-B-18 | A pinned subset of about 20 examples runs in the cert tier as a regression guard | Q30, M5 | §4 (WP-33), §8 | 33-09 | 33-09-01, 33-09-02, 33-09-03, 33-09-04 | Covered | Block S09 of test_wp33_truth.cscript runs in make cert and checks against corpus_guard_truth.json from extract_corpus_guard_truth.do. Each later closing task re-runs S09. |
| REQ-B-19 | Exclusion: large data keeps JSON number columns (no binary columns or bound) | Q31, M8 | §7 (JSON data columns kept) | none | none (exclusion; index M8) | Covered | No section changes the column encoding. D-33-01.h's Fix column says plat:PT-14 keeps JSON. |
| REQ-B-20 | State the measured large-data timings and memory per million rows in the help | Q31 | §4 (WP-36) | 36-04 | 36-04-04 | Covered | plat:PT-14 is documented in Resource limits with a Differences entry. The figures are re-measured at the batch-36.2 base rather than taken from the audit's 6-8 s / 1.4 GB, because 35-08 changed the export since. |
| REQ-B-21 | Add Firefox and WebKit runs of the CSP, browser and accessibility tests in the release tier through a dev-only driver | Q32 | none | none | none | Superseded | Superseded by A1 (no Firefox or WebKit runs). |
| REQ-B-22 | Exclusion: no browser other than Chrome is tested or added | A1 (over Q32), M8, R14 | §6, §7 | none | none (exclusion; index rule R14) | Covered | R14 bans adding any non-Chrome browser. No section adds a Firefox, WebKit or Playwright driver. |
| REQ-B-23 | The help states dash is tested in Chrome and that problems in other browsers are not dash's to solve (resolves plat:PT-16) | A1 | §4 (WP-36), §6 | 36-04 | 36-04-04 | Covered | D-36-04.c gives the wording. It replaces 'any modern browser' and 'any browser' in dash.sthlp, README and dash.pkg, pinned by TestTheBrowser. plat:PT-16 closes Documented. |
| REQ-B-24 | dash_setup's help states the Pythons and platform tags the lock covers, and that Python 3.15 and Windows ARM64 are not covered | Q33, M8 | §4 (WP-36), §7 | 36-04 | 36-04-03 | Covered | plat:PT-12 is documented. TestTheLock checks that the sentence names 3.11-3.14, the five tags, 3.15 and ARM64 and matches dash_requirements.txt. Cert case S04 reads the lock header. |
| REQ-B-25 | Exclusion: lock coverage is documented only (no lock regeneration, no warning, no win_arm64 or offline wheelhouse work) | Q33 | §7 (lock coverage kept, documented) | none | none (exclusion; index M8) | Covered | No section edits dash_requirements.txt or the setup code for coverage. D-36-04 makes no code change. |
| REQ-B-26 | WebGL: a figure with dashed or dotted lines stays on the canvas backend | Q34, M8 | §4 (WP-36) | 36-02 | 36-02-01, 36-02-02 | Covered | _dash_dashes_on_canvas applies to Line, MultiLine and Step glyphs with a non-empty line_dash, in both modes (D-36-02.b). |
| REQ-B-27 | The WebGL switch counts the rows the graph draws, not the dataset's rows | Q34, M8 | §4 (WP-36) | 36-02 | 36-02-01, 36-02-02 | Covered | _dash_drawn_rows is used in the saved page; len(g_df) in the served app (D-36-02.a). |
| REQ-B-28 | A WebGL-vs-canvas pixel check pins the fix | Q34 | none | 36-02 | 36-02-01, 36-02-03 | Covered | A release-tier test_webgl_backend_browser.py runs with SwiftShader WebGL on (D-36-02.c), plus a parity entry for DG-14. |
| REQ-B-29 | Keep named graphs' function points off the macro (a strL scalar or a file) | Q35, M8, A-7 | §4 (WP-36) | 36-03 | 36-03-01, 36-03-02 | Covered | A-7 chooses a private 0600 file per graph under dash's temp folder (survives clear all). The c(macrolen) refusal is removed. |
| REQ-B-30 | Fix the function-points message and the help, with no edition referenced | Q35 (restated after Q48), M2, R14 | §4 (WP-36), §7 | 36-03 | 36-03-02, 36-03-03 | Covered | The r(134) refusal and its 'set maxvar' advice are removed. TR-36-03.6 rewrites dash.sthlp :3713-3716, :884 and :1509-1511. No edition text is added. |
| REQ-B-31 | No absolute paths, user names or machine names in the gallery page or SVGs; test_no_secrets.py covers docs/gallery/ | Q36, M5 | §8 | 33-02, 33-08 | 33-02-02, 33-08-01, 33-08-04; index WE.7 | Covered | D-33-02.d keeps only relative paths. The D-33-08.l scan covers paths, user, host, git user, Stata banner and e-mail, with base64 payloads decoded. It runs on the 33-08-04 smoke build and is shown at the WE.7 checkpoint. |
| REQ-B-32 | The gallery uses Stata's example data only | Q36 | §6 (help files, g.pdf and the 21 datasets) | 33-02 | 33-02-02, 33-02-03 | Covered | Holds by construction. Setups are sysuse/webuse only: g.pdf stata-press uses are rewritten, examples/ use sysuse, and audit probes default to sysuse auto. The 3 webuse sets are cached. No test asserts it directly. |
| REQ-B-33 | A new GAPS4.md lists every audit item by id under its package, each with a Tracked: line read by test_tracking_documents.py | Q37, PD-1, PD-3 | §4 (WP-33), §8 | 33-01 | 33-01-01, 33-01-02 | Covered | 221 live rows keyed by lead id, other ids in the Item cell, one ## WP-NN section per WP. The 3 withdrawn items (Q48, Q50, A2) are not registered. TestGaps4Tracking covers it. |
| REQ-B-34 | One BUGS.md entry per item, closed in place | Q37, PD-4 | §8 | 33-01 (and every closing section) | 33-01-02; index rule R5 | Covered | 33-01-02 opens 221 entries in PD-4's open form. Every closing task rewrites only Resolution and the checkbox (R5). |
| REQ-B-35 | One truth cscript per WP (test_wpNN_truth.cscript), a block per section, selected by WPnn_ONLY | Q38, A-3, PD-6 | §10 risk 1 | 33-01 | 33-01-03, 33-01-04; index W0.2, rule R1 | Covered | A-3 keeps one script per WP. PD-6 narrows Q38: no script for WP-38, WP-48 or WP-50 (no Stata comparison), and WP-39 is removed. The template and wp33 script come from 33-01; the rest are created at W0.2. PRD §10 says 'first section', but the index's W0 wins. |
| REQ-B-36 | Truth comes from committed scripts/extract_*_truth.do, never hand-typed | Q39, M13 | §6 | all item sections | index rule R7 | Covered | R7 requires a committed extract script, complete _meta, no hand patching, git add -f. Each section names its script (e.g. 37-01-01, 37-03-01, 34-07-01). |
| REQ-B-37 | Saved-page JS and served Python twins share one fixture and a parity entry | Q39, M13 | §8 (saved and served modes agree) | all JS = yes sections | index rules R8, R2, R12 | Covered | BRIEF pins each JS twin through js_runner.py plus a CORPUS/MOVE parity entry. ALLOWED is never edited. |
| REQ-B-38 | Tests that pin today's picture are flipped with the reason, never deleted | Q39, M13 | §8, §10 risk 4 | all item sections | index rule R9; G1 | Covered | Each flip carries a Flipped: commit-body line (BRIEF). |
| REQ-B-39 | A failing test first | Q39, M13 | §8 (every regression test red before its fix) | all item sections | index gate G1; each section's NN-MM-01 task | Covered | BRIEF 'Failing test first': task -01 saves the failure text and makes no commit. |
| REQ-B-40 | The pending list, the help's Unsupported section and TWOWAY_COVERAGE_AUDIT.md are updated in the same commit | Q39, M13 | none | all item sections | index M13, rule R3, gate G1 | Covered | BRIEF puts the help/Unsupported/coverage-audit edits in the item's one commit. test_help_conformance pins the Unsupported list to the pending blocks. |
| REQ-B-41 | New help Differences notes are a one-line entry in 'Differences from twoway' linking to the full note in its topic section | Q40, M13 | §5 | e.g. 36-04, 37-05, 43-04, 43-07, 44-02, 46-02 | index rule R3; e.g. 36-04-02, 37-05-02, 46-02-06, 44-02-09 | Covered | R3 and BRIEF's help-text rule. The pattern is applied in D-36-04.b, D-37-05.b, D-46-02.g and D-44-02.h. |
| REQ-B-42 | The tracking foundation is built once in 33-01: GAPS4.md for all packages, every BUGS entry opened, test_tracking_documents.py taught | Q41 | §4 (WP-33) | 33-01 | 33-01-01, 33-01-02 | Covered | Rows are generated once by a scratch script (D-33-01.a) and include P4's items moved by A3. GAPS4_OPEN/WP/SECTION and the release-guard allowance are added. |
| REQ-B-43 | Each WP's closeout proves its own rows closed | Q41, Q6 | §8 | 33-01 | 33-01-01; index WE.1, WE.2 | Covered | WE.1 checks every row is Closed/Documented/Partly with no pending sha. WE.2 appends to GAPS4_CLOSED_WPS, which TestGaps4Tracking's closeout tests read. |
| REQ-B-44 | A documented item's BUGS entry closes 'Documented' with a test that reads the help sentence | Q42, M13, PD-4 | §8 | 33-01; 36-04, 37-05, 38-01, 38-02, 40-02, 43-04, 43-07, 44-02, 46-02 | 33-01-01 (Documented-form reader); e.g. 36-04-01..36-04-04, 37-05-01..37-05-03, 46-02-05, 46-02-06 | Covered | PD-3/PD-4 define the Documented forms. The reader rejects a Documented line whose Resolution does not begin 'Documented'. |
| REQ-B-45 | Where measurable, a probe shows dash does what the help sentence says | Q42, M13 | none | e.g. 36-04, 46-02, 37-05 | e.g. 36-04-03 (S04 probes), 46-02-05 (Q4602-3), 37-05-02 | Covered | Examples: D-36-04.d's probes (r(9) floor, ~ rule, lock line) and RH-8's transpose probe. |
| REQ-B-46 | The single check runs after the qualifiers are applied (_dash_qual_gen) and before Python/_dash_do_render, on the one-line route and on build/serve | C1, PD-15, M9 | §4 (WP-37) | 37-01 | 37-01-02 | Covered | D-37-01.c places it after the qual/sort/tsop/weight generators and before _dash_write_data. This includes 35-08's working frame and 33-07's multi-frame stack. Wiring is pinned by TestTheCheckIsWired. |
| REQ-B-47 | Draw the empty graph wherever twoway draws (34 of 40 types; literal types ignore if 0) | C1 | §4 (WP-37) | 37-01 | 37-01-01, 37-01-02 | Covered | The rule returns '0' (draw) for every other type and case, and literal types take no per-plot case. Q3701-1/2 check this against the fixture. |
| REQ-B-48 | lpoly/lpolyci with no observations: refuse r(2000) 'no observations' | C1 | §4 (WP-37) | 37-01 | 37-01-02 | Covered | Applies to the nodata, none and allmissing cases. |
| REQ-B-49 | fpfit/fpfitci with no observations: refuse r(198) 'observation numbers out of range' after twoway's fracpoly note | C1 | §4 (WP-37) | 37-01 | 37-01-02 | Covered | The rule table returns the note line, then the error line (TR-37-01.2). |
| REQ-B-50 | mband/mspline (without bands()) with no observations: refuse r(198) 'bands must be between 1 and 200' | C1 | §4 (WP-37) | 37-01 | 37-01-02 | Covered | With bands() given, they draw. |
| REQ-B-51 | A by() graph with every panel empty: refuse r(198) 'nothing to graph' for every type, function/scatteri/pci/pcarrowi included | C1 | §4 (WP-37) | 37-01 | 37-01-02, 37-01-03 | Covered | byempty is checked at export, and 37-01-03 removes the literal-type skip from the by() block (TR-37-01.5). Q3701-5 covers the several-plots line. |
| REQ-B-52 | Fix contour's zero-observation crash (DG-1, r(7102)) | C1 | §4 (WP-37) | 37-01 | 37-01-03, 37-01-04 | Covered | map_contour draws an empty layer and a titled, empty ColorBar in both modes (_contour_key_empty), with a parity entry. DG-1 closes in 37-01-04. |
| REQ-B-53 | Each corpus example is rendered at the size twoway draws it: its scheme's default (7.5x4.5 in under stcolor) or its own xsize()/ysize() | C2 (supersedes Q57's 5.5x4), A-1 | §5 | 33-03, 33-04, 34-04, 45-04 | 33-03-02, 33-03-03, 33-04-03, 33-04-04, 34-04-02, 45-04-02 | Covered | The twoway runner records each SVG's inches, and the dash runner exports at W,H = inches x 96. by()/multi-figure pages are letterboxed until A-1's fixes (34-04, 45-04) land, which happens before the WE.7 gallery (PD-17, D-33-08.n). |
| REQ-B-54 | Call twoway__contour_gen only when the data is a full grid or interp(none) is given | C3, M9 | §4 (WP-37) | 37-03 | 37-03-01, 37-03-02, 37-03-03 | Covered | Runs at export in a temporary frame, per by() panel, with an exact grid test and the D-37-03.f gate. Both renderers draw Stata's polygons and cuts. |
| REQ-B-55 | Exclusion/quality: scattered data above 1,000 points keeps the seeded subsample and its note, and the help says so | C3, M9 | §4 (WP-37), §10 risk 6 | 37-03 | 37-03-03, 37-03-04 | Covered | BR-37-03.3 keeps today's fit on scattered data. The TR-37-03.6 help text states the subsample, the note, and interp(none)'s cost. |
| REQ-B-56 | Add a dash image panel: a registered SVG item placed by tabs()/layout() like a KPI, in both modes | C4, PD-12, A-17, A-18 | §4 (WP-33), §3 | 33-06 | 33-06-01, 33-06-02, 33-06-03, 33-06-04, 33-06-05 | Covered | Syntax: dash image using <file.svg>, name() caption() alt() link(<page>.html). Count cap $dash_max_images, no byte bound (A-18). Q3306-8 places one in tabs(). |
| REQ-B-57 | Registered graphs keep their own frame, so one dash build draws several datasets | C4, A-17, P4-4 | §4 (WP-33) | 33-07 | 33-07-01, 33-07-02, 33-07-03, 33-07-04, 33-07-05 | Covered | A-17 uses Stata's own frame f: prefix (no frame() option). P4-4 extends frames to ts operators, sort() and weights. Single-frame builds are unchanged. |
| REQ-B-58 | The gallery is a genuine dash build | C4, P4-1, P4-8 | §4 (WP-33), §5 | 33-08 | 33-08-02, 33-08-04; index WE.7 | Covered | gallery.py writes one page.do per plot type, each ending in dash build, plus a dash-built index page (P4-1 replaces Q16's single page). The smoke build runs in scratch. The real gallery is built only at WE.7 (P4-8). |
| REQ-B-59 | Quality: help, tests and security rules apply to the new gallery features | C4 | §10 risk 2 | 33-06, 33-07 | 33-06-01, 33-06-02, 33-06-03, 33-06-04, 33-07-04 | Covered | SVGs are sanitised (no script, event handler, foreignObject, DOCTYPE or external reference). Caption and alt are html.escape'd, link() is whitelisted, and the image is a data: URI under the unchanged CSP. Release-tier CSP browser test; help sections for both features. |
| REQ-B-60 | With c(python_exec) empty, dash and dash_setup skip their refusal and run the normal python: path, so Stata picks its Python | C5, M8, D40 P2 | §4 (WP-36), §6 | 36-01 | 36-01-01, 36-01-02 | Covered | _dash_require_python stays as an empty hook (A-8). A release-tier fresh-HOME pytest goes through one stata_slot. |
| REQ-B-61 | Stata's own failure is surfaced, followed by dash's advice | C5, M8 | §4 (WP-36) | 36-01 | 36-01-02 | Covered | Uses capture noisily python: and _dash_python_failed, exiting with Stata's rc (D-36-01.b). |
| REQ-B-62 | The harness (truth-cscript gates, cert_svg.do, scripts/stata_python_exec.sh) follows the same no-pre-check rule | C5, M8 | none | 36-01 | 36-01-03, 36-01-04 | Covered | Removes 50 cscript skip gates, cert_svg's gate and 65 extract-script gates, and rewrites stata_python_exec.sh. 36-01-04 flips the hygiene pins. |
| REQ-B-63 | Exclusion: no python query probe | C5, M8 | none (index M8) | 36-01 | none (exclusion; index M8) | Covered | D-36-01 keeps the hygiene guard that forbids python query and adds no other probe. D-33-01.h's Fix column says plat:PT-1 uses no python query. |
| REQ-C-01 | Keep dash's extra refusal lines (second/later lines, hint lines) and the Supported list; only the first line becomes twoway's | DISCOVERY Q43 (index PD-11, M12) | §7 (kept: dash's extra refusal lines); §4 WP-46..49 | 49-01 | 49-01-01, 49-01-03 (Q4901-4/5 guards); index rule PD-11 | Covered | 49-01 Boundaries forbid removing any second line or the Supported list; Q4901-4/5 check they stay byte-identical. |
| REQ-C-02 | Correct any help sentence that says refusals print only twoway's line | DISCOVERY Q43 | §4 WP-46..49; §9 | 49-01, 48-04 | 49-01-03 (D-49-01.d, TestHR17) | Covered | Q43 gives this to P16 (WP-48), but the plan does it in WP-49 (P17) as HR-17. 48-04 D-48-04.c hands HR-17 to 49-01. |
| REQ-C-03 | Keep every cap that is not on observations (plots, reflines, added texts, n(), bin(), lpoly degree, 1,000-bin rebin, 2,000-tick clamp, msize, fpfit grid, text length) | DISCOVERY Q44 | §7 (every count cap kept) | 33-15, 40-02 | 33-15-01..04 (D-33-15.b, BR-33-15.3); 40-02-02..04 (documentation only) | Covered | 33-15 leaves every count cap unchanged. 40-02 changes no code and does not edit _DASH_STATA_ORACLE_MAX. |
| REQ-C-04 | Document each cap in the help: a one-line Differences entry plus the full note under Resource limits | DISCOVERY Q44 (M10) | §4 WP-40; §7 | 40-02 | 40-02-01, 40-02-02, 40-02-03, 40-02-04 | Covered | One Differences item, 'Resource limits', with one sub-point per cap, plus a new Fixed limits paragraph. |
| REQ-C-05 | Keep the page-size (bytes) cap like every other cap (Q44 'keep every cap') | DISCOVERY Q44 | §7 | 33-15 | 33-15-02, 33-15-03 (cap removed) | Superseded | Superseded by P4-3: the $dash_max_bytes and $dash_max_cells caps are removed in batch 33.1. |
| REQ-C-06 | Document the observation caps (D40 P5) | DISCOVERY Q45 | §4 WP-40 | 33-15, 40-02 | 33-15-03 (help paragraph 'No size limit.'); 40-02-02 (plat:PT-8 no-size-limit sub-point, plat:PT-10 by() groups) | Covered | The cell cap is gone (P4-3), so the help says there is no size limit and documents the by() group cap. |
| REQ-C-07 | The observation cap counts only the rows if/in selects | DISCOVERY Q45 | §4 WP-40 | 40-01 | -- | Superseded | Superseded by P4-3 (index M10): no cap is left to count against, so the selected-row work stays only as a size measure. |
| REQ-C-08 | Export only the rows the graphs select when no filter, link() or csv needs every row | DISCOVERY Q45 (with A-12) | §4 WP-40 | 40-01 | 40-01-01, 40-01-02, 40-01-03, 40-01-04 | Covered | KPI, brush() and served builds also keep the full export (A-12). n_obs keeps the lpoly grid exact. |
| REQ-C-09 | Keep the Stata 19 version floor (no change to the floor) | DISCOVERY Q46 | §7 (Stata 19 floor kept) | 36-04 | 36-04-02 (r(9) kept; no code change) | Covered | 36-04 Boundaries: no code change. Q3604-1 probes the r(9) floor. |
| REQ-C-10 | README and help state the drop-in claim is for Stata 19 and later | DISCOVERY Q46 | §7; §4 WP-36 | 36-04 | 36-04-01, 36-04-02 (TR-36-04.2) | Covered | Adds a Dependencies sentence, '(on Stata 19 and later)' at README.md:15, and a Differences entry. |
| REQ-C-11 | README and help state the tested platform (macOS arm64, StataNow 19.5, console) and that other platforms have not been run | DISCOVERY Q47 | §7; §4 WP-36 | 36-04 | 36-04-01, 36-04-02 (plat:PT-5 with TR-20, ECO-17) | Covered | Covers the runners and the opener. dash.pkg and dash_setup.sthlp are updated too. |
| REQ-C-12 | Platforms are documented only: no code changes | DISCOVERY Q47 | §7 (no platform ports) | 36-04 | 36-04 Boundaries (no change to dash.ado, mata, renderer, setup) | Covered | Exclusion stated in PRD §7 and in 36-04 Boundaries/M8. |
| REQ-C-13 | The ~ expansion item (plat:PT-6) is resolved by documentation | DISCOVERY Q47 | §4 WP-36 | 36-04 | 36-04-03 (Q3604-2 tilde probe) | Covered | The rule is stated where saving() paths are documented. No Differences entry (D-36-04.b). |
| REQ-C-14 | Do nothing about Stata editions; plat:PT-3 withdrawn and not registered | DISCOVERY Q48 | §7 (no work on editions, ever) | 33-01 | 33-01-02 (WITHDRAWN rows skipped); index Appendix A | Covered | The GAPS4 header says only that three items were withdrawn (Q48, Q50, A2). |
| REQ-C-15 | Never reference edition differences again in plan text, tests or help changes | DISCOVERY Q48 (restated by A-2) | §7 | 36-04, 36-03 | index rule R14; index M2; 36-04-01..04 (D-36-04.a) | Covered | Editions appear only in the ban rules (M2, R14, BRIEF, A-2). No section adds edition text. |
| REQ-C-16 | List the dependencies in the help file and do nothing else | DISCOVERY Q49 | §4 WP-36; §9 | 36-04 | 36-04-03 (plat:PT-11, TR-36-04.3) | Covered | No Differences entry, no conda guidance and no venv default (D-36-04.b, Boundaries). |
| REQ-C-17 | Keep jitter's noise unchanged and undocumented; basic:PT-7, DT-25, TR-15, sil:SD-6 withdrawn | DISCOVERY Q50 | §7 (jitter's noise, not documented); §4 | 33-01, 48-04 | 33-01-02 (basic:PT-7 not registered); index M12, Appendix A; 48-04 Boundaries (no jitter text) | Covered | The plan has no jitter-noise work. 35-05 lifts only jitter() value bounds (basic:PT-13), not the noise. |
| REQ-C-18 | Version stays 0.1.0; only the date moves | DISCOVERY Q51 | §7; §9 | index | index WE.8; index M14 | Covered | WE.8 moves the dates at the final closeout. |
| REQ-C-19 | Keep the README's drop-in claim while the work lands | DISCOVERY Q52 | §7; §9 | 48-04, 36-04 | 48-04-03 (claim kept); index M14 | Covered | 48-04 Boundaries: do not remove the README's drop-in claim. 36-04-02 scopes it to Stata 19+. |
| REQ-C-20 | P16 fixes each specific false sentence as its owning WP lands | DISCOVERY Q52 | §9 | 48-04 and Appendix B owners | index rule PD-8 / Appendix B; 48-04-01..05 | Covered | Each owning section fixes its HR sentence in the item's commit. 48-04 verifies all 22, HR-17 by 49-01. |
| REQ-C-21 | No gallery size cap; commit what the corpus produces | DISCOVERY Q53 | §9 | 33-08 | 33-08-02 (D-33-08.m: prints sizes, exits 0); index WE.7 | Covered | A warning only above 95 MB (GitHub's limit). WE.7's checkpoint decides. |
| REQ-C-22 | About 12 curated README examples spanning the plot types and common options | DISCOVERY Q54 | §5; §4 WP-33 | 33-08 | 33-08-02 (readme_candidates, 12 groups; readme_examples.txt); index WE.7 (ids chosen) | Covered | TestTheCommittedGallery requires 10-14 ids once the gallery exists. |
| REQ-C-23 | README links to the full gallery page | DISCOVERY Q54 | §5 | 33-08 | 33-08-02 (readme_block link to docs/gallery/index.html) | Covered | --pages-url is supported for the maintainer's later GitHub Pages step. |
| REQ-C-24 | README layout: side-by-side pairs (twoway SVG left, dash SVG right), command as caption beneath, plus its verdict | DISCOVERY Q55 | §5 | 33-08 | 33-08-01 (TestReadmeBlock), 33-08-02 (readme_block); index WE.7 | Covered | D-33-08.j: two <img>, then <code>cmd</code>, then <b>verdict</b>[: summary]. |
| REQ-C-25 | Verdict scale is Same / Close / Differs | DISCOVERY Q56 | §5 | 33-05 | 33-05-01, 33-05-02 (verdict()) | Covered | The rule follows A-4 (D-33-05.a). |
| REQ-C-26 | Close and Differs list the measured differences in one line | DISCOVERY Q56 | §5 | 33-05, 33-08 | 33-05-02 (summary(), max 200 chars); 33-08-02 (captions) | Covered | Each difference is tagged with its explaining GAPS4 id when one exists. |
| REQ-C-27 | Render the dash graph at a fixed size in twoway's default 5.5 x 4 in shape | DISCOVERY Q57 | §5 | 33-03, 33-04 | 33-03-02, 33-04-02..04 (each example's own size) | Superseded | Superseded by RESEARCH C2 (stcolor's default is 7.5 x 4.5): each pair is drawn at the size twoway draws that example. |
| REQ-C-28 | Each pair lines up and the gallery page uses the same size | DISCOVERY Q57 (as C2 resolved it) | §5 | 33-04, 33-08, 34-04, 45-04 | 33-04-03 (export at twoway's W x H, size_matched); 33-08-02 (D-33-08.n); 45-04-02 before WE.7 | Covered | No xsize()/ysize() is added. A-1 makes the graph keep twoway's shape and fill its cell beside the image panel. |
| REQ-C-29 | One gallery page organised by dash tabs by plot type | DISCOVERY Q58 (and Q16) | §5 (still says one page with tabs) | 33-08 | -- | Superseded | Superseded by P4-1 (one page per plot type plus an index page). PRD §5 was not updated and still describes tabs. |
| REQ-C-30 | Each gallery example shows its command, twoway's SVG, the live dash graph and the verdict | DISCOVERY Q58 | §5 | 33-08 | 33-08-02 (D-33-08.c, .e), 33-08-04 (smoke build); index WE.7 | Covered | A row falls back to dash's static SVG only when its dataset is missing, the frame limit is reached or a frame clash occurs. |
| REQ-C-31 | No Firefox or WebKit runs (supersedes Q32) | DISCOVERY A1 | §6; §7 (no browsers other than Chrome) | all | index rule R14; BRIEF | Covered | Exclusion stated. Q32 (in another category) is Superseded by A1. No section adds a browser. |
| REQ-C-32 | Help states dash is tested in Chrome and problems in other browsers are not dash's to solve; this resolves plat:PT-16 | DISCOVERY A1 | §6 | 36-04 | 36-04-01, 36-04-04 (D-36-04.c, TR-36-04.6) | Covered | plat:PT-16 closes Documented. The README and dash.pkg are updated too. |
| REQ-C-33 | Do not draw matamatrix() (it does not exist in Stata) | DISCOVERY A2 | §7 | 35-09 | 35-09-03 (by-name code removed; generic refusal) | Covered | PD-10: _dash_matamatrix_typed is removed and the varlist form gets the generic unknown-token refusal. |
| REQ-C-34 | plot:PT-10 withdrawn; no plan, test or audit lists it | DISCOVERY A2 | §7 | 33-01, 35-09 | 33-01-02 (not registered); index Appendix A; index rule R14; 35-09-03 (D-35-09.e) | Covered | Appendix A names the id only as withdrawn. Tests keep the word only as input in flipped pins (A-9). |
| REQ-C-35 | Help stops naming matamatrix() (P16) | DISCOVERY A2 | §4 WP-46..49 | 35-09, 48-04 | 35-09-03 (dash.sthlp :737-745, :995-997); 48-04-01 (TestHR05and22 verifies) | Covered | A2 names P16, but the plan does it in WP-35 (PD-10/HR-5). WP-48's 48-04 only verifies it. |
| REQ-C-36 | WP-39 removed; number 39 stays unused; other WP numbers keep the Q5 mapping | DISCOVERY A3 | §1; §4 | index | index Overview, M3, Appendix A (WP-39 removed) | Covered | Seventeen WPs; WP-39 holds only the withdrawn plot:PT-10. |
| REQ-C-37 | Capitalised plot-type names (Q7) move to WP-35 | DISCOVERY A3 | §4 WP-35 | 35-09 | 35-09-01, 35-09-02 (plot:PT-3) | Covered | Lower case only; capitals are refused as twoway refuses them. |
| REQ-C-38 | The empty graph's axes and options move to WP-35 | DISCOVERY A3 | §4 WP-35 | 35-09 | 35-09-04 (plot:PT-4) | Covered | Drawn with no axes; its axis options are refused in twoway's words; HR-8 corrected. |
| REQ-C-39 | '(scatter ..) line ..' moves to WP-35 (accepted) | DISCOVERY A3 | §4 WP-35 | 35-09 | 35-09-05 (syn:SD-1) | Covered |  |
| REQ-C-40 | An option-less \|\| inside one group moves to WP-35 (accepted) | DISCOVERY A3 | §4 WP-35 | 35-09 | 35-09-06 (syn:SD-13) | Covered |  |
| REQ-C-41 | The dash.sthlp:737-742 sunflower sentence goes to WP-48 (P16) | DISCOVERY A3 | §4 WP-46..49 | 35-09, 48-04 | 35-09-03 (HR-22, PD-10); 48-04-01 (TestHR05and22) | Covered | The fix moved earlier, to WP-35's PD-10 commit (A-9). WP-48 only verifies it. This departs from A3's WP-48 placement but does what A3 requires. |
| REQ-C-42 | Gallery is one dash page per plot type plus a dash-built index page linking them (supersedes Q16/Q58) | DECISIONS P4-1 | §4 WP-33 | 33-08, 33-06 | 33-08-01, 33-08-02 (pages, write_page, write_index), 33-08-04; 33-06-02..04 (link()); index WE.7 | Covered | PRD §5 still describes one tabbed page; index PD-13 and 33-08 follow P4-1. |
| REQ-C-43 | Each gallery page loads quickly (quality) | DECISIONS P4-1 | §4 WP-33 | 33-08 | 33-08-02 (per-type split; D-33-08.m size lines), 33-08-04 (page MB recorded) | Covered | Achieved by the per-type split and de-duplication (P4-2). There is no load-time test; size is reported per page. |
| REQ-C-44 | Corpus keeps one example per combination of plot types and option names (~425 of 636); option values do not make a new example | DECISIONS P4-2 | §4 WP-33 | 33-02 | 33-02-01 (TestDedup), 33-02-02 (dedupe, signature), 33-02-03 (count reported) | Covered | Option spellings are expanded to full names; weights do not count. The kept count is reported, not forced (AC-33-02.3). |
| REQ-C-45 | Extractor records every dropped duplicate and the example it maps to | DECISIONS P4-2 | §4 WP-33 | 33-02, 33-08 | 33-02-02, 33-02-03 (extract_duplicates.tsv); 33-08-02 (corpus.json duplicates) | Covered |  |
| REQ-C-46 | Remove the embedded-cell cap ($dash_max_cells) and the page-size cap ($dash_max_bytes) in both modes, in batch 33.1, in new section 33-15 | DECISIONS P4-3 | §4 WP-33; §7 | 33-15 | 33-15-01, 33-15-02, 33-15-03, 33-15-04 | Covered | Index manifest/batch 33.1 hold 33-15. PLAN.md's section overview is stale: it omits 33-15 and says 91 sections. |
| REQ-C-47 | Count caps (graphs, plots, by groups, tabs, filters, reflines, added text, table rows, images) stay and are documented | DECISIONS P4-3 (Q44) | §7 | 33-15, 33-06, 40-02 | 33-15-01..04 (BR-33-15.3); 33-06-02, 33-06-04 (images row); 40-02-02 | Covered |  |
| REQ-C-48 | Multi-frame builds support time-series operators, sort() and weight expressions; no example is limited to a static pair for that reason | DECISIONS P4-4 | §4 WP-33 | 33-07, 33-08 | 33-07-01, 33-07-03 (D-33-07.g); 33-08-01 (test_ts_operators_sort_and_weights_stay_live) | Covered |  |
| REQ-C-49 | LT-24: option text with an unbalanced quote is refused with twoway's measured rc and words (r(100)/r(109)/r(198) by form), overriding the keep-as-typed rule | DECISIONS P4-5 | §5 (general only) | 43-05 | 43-05-01 (quote_truth.json), 43-05-08 (Q4305-12; JSE-42..49 flipped) | Covered | Not named in the PRD. |
| REQ-C-50 | Quotes inside if qualifiers and compound-quoted text keep today's handling | DECISIONS P4-5 | -- | 43-05 | 43-05-08 (Q4305-13) | Covered | The qualifier and compound JSE cases are left unflipped. |
| REQ-C-51 | text() =exp globals are evaluated by a whitelisted Mata evaluator (arithmetic and Stata functions on scalars only; no variables, commands, macro or file access) | DECISIONS P4-6 | -- | 43-06 | 43-06-03 (TestEvaluatorIsSafe), 43-06-05 | Covered | The same evaluator covers the graph text options (P4-7). A filewrite probe confirms nothing is written. |
| REQ-C-52 | Help documents exactly what is whitelisted | DECISIONS P4-6 | -- | 43-06 | 43-06-06 (TestHelp::test_whitelist_sentence) | Covered | The test checks the help's function list against the wl assignment. |
| REQ-C-53 | Anything outside the whitelist is drawn literally with a note | DECISIONS P4-6 | -- | 43-06 | 43-06-05 (_at_expnote, one note per graph) | Covered | LT-20 closes Documented (A-5). |
| REQ-C-54 | Syntax mirrors twoway as closely as possible unless the option is dash-only functionality | DECISIONS P4-7 | §4 WP-35; §5 | 35-07, 33-06, 33-07 | 35-07-01, 35-07-02, 35-07-03; 33-07-02 (no frame() option) | Covered | PRD §4 still says the words are 'decided per word' (before the ruling). |
| REQ-C-55 | Refuse the 25 second-axis forms (ytitle2() .. ttitle2()) with twoway's words | DECISIONS P4-7 | §4 WP-35 | 35-07 | 35-07-01, 35-07-02 | Covered |  |
| REQ-C-56 | Refuse malpha()/lalpha()/falpha(), marker(), jseed(), mlg(), plotbgcolor(), pbgc() with twoway's words | DECISIONS P4-7 | §4 WP-35 | 35-07 | 35-07-01, 35-07-02 | Covered |  |
| REQ-C-57 | Refuse cv(), colv(), colornlevels(), colormissing(), colpalette() with twoway's words | DECISIONS P4-7 | §4 WP-35/42 | 35-07, 42-05 | 35-07-02 (refusal); 42-05-07, 42-05-08 (pins, CV-14) | Covered |  |
| REQ-C-58 | Refuse bw() where dash read it as barwidth() (bar/rbar/histogram/dot/spike) | DECISIONS P4-7 | §4 WP-35 | 35-04 | 35-04-06 (stat:PT-14) | Covered |  |
| REQ-C-59 | Keep hover() and table (and dash's own subcommands' options) as dash-only, listed in one help paragraph | DECISIONS P4-7 | §4 WP-35 | 35-07 | 35-07-03 ({marker dashonly}; deliberate dicts) | Covered | Their known differences move to *_DELIBERATE under P4-7. |
| REQ-C-60 | Non-word forms: kernel() is case-sensitive; xsize(()) is refused | DECISIONS P4-7 | §4 WP-35 | 35-07 | 35-07-02 (V1, V2), 35-07-03 (CHANGELOG) | Covered |  |
| REQ-C-61 | A string colorvar() is refused r(7) | DECISIONS P4-7 | §4 WP-35/42 | 35-07, 42-05 | 35-07-02 (V3); 42-05-04 (confirm numeric variable); 42-05-08 (pinned) | Covered |  |
| REQ-C-62 | A colorvar() layer whose if keeps no observation is answered as twoway answers when it draws | DECISIONS P4-7 | §4 WP-42 | 42-05 | 42-05-07, 42-05-08 (_dash_zero_obs_cvrule) | Covered | Recorded in 35-07 as V4 and delivered by 42-05 after 37-01's check. |
| REQ-C-63 | Each newly refused form gets a CHANGELOG 'Changed behaviour' line | DECISIONS P4-7 | -- | 35-07, 35-04, 42-05 | 35-07-03 (one line per REFUSE entry), 35-04-06, 42-05-08 | Covered | 35-07-03's verify counts 41 lines tagged (WP-35, DT-15). |
| REQ-C-64 | WP-33 builds the harness, runs the corpus comparison (verdicts, ledger) and closes TR-2 | DECISIONS P4-8 | §4 WP-33 | 33-02..33-05, 33-08, 33-14 | 33-14-01, 33-14-02, 33-14-03, 33-14-04, 33-14-05 | Covered | The baseline goes to test/fixtures/corpus_baseline.json with maintainer approval. |
| REQ-C-65 | WP-33 writes no gallery page and no README block | DECISIONS P4-8 | §4 WP-33 | 33-08, 33-14 | 33-08-04, 33-08-05 (D-33-08.p, nothing under docs/ or README.md); 33-14-05 (D-33-14.f) | Covered |  |
| REQ-C-66 | Gallery pages and the README block are built and committed only at the final closeout (WP-50 WE.7) with maintainer sign-off | DECISIONS P4-8 | §4 WP-33; §8 | index | index WE.7 | Covered | WE.7: make corpus && make gallery, maintainer checkpoint, commit. |
| REQ-C-67 | Refusing a synonym dash used to accept prints twoway's refusal first and a second line naming the twoway spelling | DECISIONS P4-9 | -- | 35-07, 35-04, 42-05, 49-01 | 35-07-02 (D-35-07.b); 35-04-06 ('use barwidth()'); 42-05-07, 42-05-08; 49-01-01 (Q4901-5 keeps them) | Covered |  |
| REQ-C-68 | Refused examples (twoway refuses, or dash refuses as a documented difference) stay in corpus.json with both answers | DECISIONS P4-10 | -- | 33-05, 33-08 | 33-05-02 (gallery(), D-33-05.h); 33-08-02 (corpus_json) | Covered |  |
| REQ-C-69 | Gallery pages show only examples twoway draws | DECISIONS P4-10 | -- | 33-05, 33-08 | 33-05-02; 33-08-01 (TestPages), 33-08-02 (pages()) | Covered |  |
| REQ-C-70 | Every graph, by() included, keeps twoway's shape (xsize/ysize ratio or the scheme's graph size); width fills its cell | DECISIONS A-1 | §4 WP-41..45 | 45-04 | 45-04-01, 45-04-02 (VF-4) | Covered |  |
| REQ-C-71 | Remove the 160-560 px height band | DECISIONS A-1 | -- | 45-04 | 45-04-02 | Covered |  |
| REQ-C-72 | Explicit xsize()/ysize() give the exact size, with 34-04's fix as the base | DECISIONS A-1 | §4 WP-34 | 34-04, 45-04 | 34-04-01, 34-04-02, 34-04-03; 45-04-02 | Covered |  |
| REQ-C-73 | Relative sizes scale with the scheme's graph size (1.125x under stcolor) | DECISIONS A-1 | -- | 45-04 | 45-04-01, 45-04-02 (D-45-04.b) | Covered |  |
| REQ-C-74 | Sizing pins flip with reasons (never deleted) | DECISIONS A-1 | §8 | 45-04 | 45-04-02 (AC-45-04.5) | Covered |  |
| REQ-C-75 | Existing edition sentences in dash.pkg, README.md, dash.sthlp, dash_setup.sthlp and CHANGELOG.md stay verbatim; new sentences go beside them | DECISIONS A-2 | §7 | 36-04 | 36-04-02, 36-04-03, 36-04-04 (D-36-04.a) | Covered |  |
| REQ-C-76 | test_every_stata_declaration_agrees is not flipped | DECISIONS A-2 | -- | 36-04 | 36-04-02..04 (run as a guard after every edit; AC-36-04.2) | Covered |  |
| REQ-C-77 | 50-02 keeps one truth script per WP (no consolidation); it cuts per-session load cost and rebalances shards instead | DECISIONS A-3 (keeps Q38) | §10 risk 1; §4 WP-50 | 50-02 | 50-02-02, 50-02-03 (D-50-02.a) | Covered | Scripts load with `run` instead of `do`, and only long scripts split, on measured block seconds. |
| REQ-C-78 | Verdicts: geometry decides Differs; the image score can only move a geometry-clean pair from Same to Close | DECISIONS A-4 | -- | 33-05 | 33-05-01 (TestVerdict::test_every_branch), 33-05-02 | Covered |  |
| REQ-C-79 | No calibration stop rule; T_close/T_same are recorded, not gating | DECISIONS A-4 | -- | 33-05 | 33-05-04 (thresholds never raises), 33-05-05 (shown for information) | Covered | T_same is still used for the Same-to-Close step. T_close is recorded only. |
| REQ-C-80 | Residuals documented by a ruling close Documented (no open S1/S2 entry) | DECISIONS A-5 | §4 WP-41..45 | 43-04, 43-06, 43-07, 44-02 | 43-04-04 (LT-21), 43-06-06 (LT-20), 43-07-06 (ST-14), 44-02-09 (AX-15) | Covered |  |
| REQ-C-81 | AX-13's boxed right-hand axis title takes the overlay route (no residual) | DECISIONS A-5 | -- | 44-01 | 44-01-01, 44-01-02 (D-44-01.c) | Covered |  |
| REQ-C-82 | AX-11's degenerate twoway picture for non-positive data on a log axis is documented, as RH-8 is | DECISIONS A-5 | -- | 44-03 | 44-03-06, 44-03-07 (D-44-03.e) | Covered | Closes Documented with its (documented) ledger rows kept. |
| REQ-C-83 | 34-05 draws the full area outline twoway draws (measured), not only the top | DECISIONS A-6 | §2; §4 WP-34 | 34-05 | 34-05-01, 34-05-02, 34-05-03, 34-05-04 | Covered | One ring: top, base and closing edges, on the key too. |
| REQ-C-84 | Function points go to a private file under dash's temp folder keyed by graph name (survives clear all) | DECISIONS A-7 | §4 WP-36 | 36-03 | 36-03-01, 36-03-02, 36-03-03 (TestClearAll) | Covered |  |
| REQ-C-85 | The fresh-HOME test is a release-tier pytest that starts Stata through stata_slot.sh with a temporary HOME (one slot; no nested fourth session) | DECISIONS A-8 | §4 WP-36 | 36-01 | 36-01-01, 36-01-04 (D-36-01.e) | Covered |  |
| REQ-C-86 | _dash_require_python stays as an empty documented hook | DECISIONS A-8 | §4 WP-36 | 36-01 | 36-01-02 (D-36-01.a) | Covered |  |
| REQ-C-87 | sunflower/matamatrix() pins are flipped in place to assert the generic refusals (the word appears only as test input) | DECISIONS A-9 | §7 | 35-09 | 35-09-03 | Covered |  |
| REQ-C-88 | CHANGELOG and TWOWAY_COVERAGE_AUDIT lines naming them as twoway features are corrected by 35-09 | DECISIONS A-9 | -- | 35-09 | 35-09-03 (grep checks 0 matamatrix, 0 sunflower in TWOWAY_COVERAGE_AUDIT) | Covered |  |
| REQ-C-89 | Ledger rows of documented or residual items stay after their item closes | DECISIONS A-10 | -- | 33-05, 33-10 | 33-05-01, 33-05-02 (ledger live rule, D-33-05.e); 33-10 D-33-10.a; the closing steps of each closing task | Covered |  |
| REQ-C-90 | GAPS4's Fix column states the ruled resolution, never a remedy a ruling rejected | DECISIONS A-10 | -- | 33-01 | 33-01-01, 33-01-02 (FIX_OVERRIDE, 63 rows; D-33-01.h) | Covered |  |
| REQ-C-91 | Chrome scale/position comparisons stay in the release tier; the 230 accepted probes are not rendered in cert | DECISIONS A-10 | -- | 33-10, 33-11, 33-12 | 33-10-01..03 (registration only); 33-11-03, 33-11-06 (D-33-11.h); 33-12-04..06 | Covered |  |
| REQ-C-92 | GitHub Pages stays the maintainer's later step | DECISIONS A-10 | §6; §9 | 33-08 | 33-08-02 (README link text; --pages-url optional) | Covered | Exclusion stated; no plan step enables Pages. |
| REQ-C-93 | 42-05 moves to its own batch 42.3 so 42-02 alone edits _apply_colorvar in 42.2; 42-03 and 42-04 follow | DECISIONS A-11 | -- | 42-02..42-05 | index batch order (42.2-42.5); section headers | Covered | PLAN.md's section overview still lists the old batches (42-05 in 42.2). The index and sections follow A-11. |
| REQ-C-94 | lfit xlog/xtransform() under by() fits per panel, as twoway does | DECISIONS A-12 | §4 WP-37 | 37-04 | 37-04-02, 37-04-03 (Q3704-5, Q3704-7) | Covered |  |
| REQ-C-95 | qfit/qfitci/fpfitci xlog/xtransform() are measured and accepted or refused as twoway does | DECISIONS A-12 | -- | 37-04 | 37-04-01, 37-04-02 (Q3704-4) | Covered | Measured: qfit, qfitci and fpfitci take the options and draw without them; fpfit refuses. |
| REQ-C-96 | A by() 'nothing to graph' refusal's second line names the plots | DECISIONS A-12 | -- | 37-01 | 37-01-01, 37-01-02 (TR-37-01.4) | Covered |  |
| REQ-C-97 | TR-19 closes with no CHANGELOG line | DECISIONS A-12 | -- | 41-02 | 41-02-08 (D-41-02.e) | Covered |  |
| REQ-C-98 | CV-14 closes Closed with the kept and refused words both named | DECISIONS A-12 | -- | 42-05 | 42-05-08 | Covered |  |
| REQ-C-99 | 40-01's extra full-row cases (KPI, brush(), served) stay | DECISIONS A-12 | -- | 40-01 | 40-01-01 (Q4001-3), 40-01-03 (D-40-01.a) | Covered |  |
| REQ-C-100 | Right edge titles (r1title/r2title) read upward as in twoway, added to 43-05 under LT-19 | DECISIONS A-13 | -- | 43-05, 41-02 | 43-05-07 (D-43-05.h); 41-02-05 (hand-back for by() cells) | Covered |  |
| REQ-C-101 | Q11's 1-4 tasks counts per item; a multi-item section may hold more tasks; no split for count alone | DECISIONS A-14 | -- | all (e.g. 44-03, 43-05) | BRIEF 'Task counts' rule (e.g. 44-03-01..13) | Covered |  |
| REQ-C-102 | WP-44 residuals documented by a ruling close Documented with a Documented Tracked line; documented ledger rows stay | DECISIONS A-15 | -- | 44-02, 44-03 | 44-02-09 (AX-15, D-44-02.i), 44-03-07 (AX-11, AC-44-03.4) | Covered | A-15 names 44-01 and 44-03. The second residual, AX-15, sits in 44-02. 44-01's items close Closed. |
| REQ-C-103 | 34-09's TR-5 checkpoint offers only 'match twoway's range rule' (no documentation option) | DECISIONS A-16 | §4 WP-34 | 34-09 | 34-09-02 (checkpoint), 34-09-03 (match) | Covered |  |
| REQ-C-104 | Colour-key ticks follow Stata's at build in both modes (the served app gets the same Stata rows as the saved page) | DECISIONS A-16 | §4 WP-34 | 34-09 | 34-09-04, 34-09-05 (Q3409-9) | Covered |  |
| REQ-C-105 | frame() is Stata's own prefix: 33-07 records the frame a named graph is registered in; dash takes no frame() option | DECISIONS A-17 | §4 WP-33 | 33-07 | 33-07-01, 33-07-02 (Q3307-2: frame() refused), 33-07-03 | Covered |  |
| REQ-C-106 | The image panel gains link(<page>.html) (a dash-only option) so the gallery index links its pages | DECISIONS A-17 | §4 WP-33 | 33-06, 33-08 | 33-06-01, 33-06-02, 33-06-03, 33-06-04; 33-08-02 (write_index) | Covered | link() accepts only ^[A-Za-z0-9_-]+\.html$. |
| REQ-C-107 | No per-image byte bound: 33-06 drops _DASH_IMAGE_MAX_BYTES | DECISIONS A-18 | §7 | 33-06, 40-02 | 33-06-01 (help test: no byte figure), 33-06-03 (no size constant); 40-02-01 (grep guard) | Covered |  |
| REQ-C-108 | $dash_max_images count cap stays and is documented | DECISIONS A-18 | §7 | 33-06, 40-02 | 33-06-02 (limit table), 33-06-04 (Resource limits row); 40-02-02 | Covered |  |
| REQ-C-109 | 34-09's 256-call build-time tick bound stays (not a size cap) and 40-02 documents it | DECISIONS A-18 | §7 | 34-09, 40-02 | 34-09-04 (_DASH_STATA_ORACLE_MAX = 256); 40-02-02 (silent list), 40-02-03 (Fixed limits, AX-16) | Covered |  |
| REQ-C-110 | At build every colour-key tick call uses Stata's rows in both modes | DECISIONS A-19 | §4 WP-34 | 34-09 | 34-09-05 (TR-34-09.9 table keyword) | Covered |  |
| REQ-C-111 | _dash_cvar_ticks (served filter-move relevel) stays on the natscale model; after-move misses stay open (D41) | DECISIONS A-19 | §4 WP-34; §7 | 34-09 | 34-09-05 (left untouched, grep verify), 34-09-08 (natscale entry re-scoped, Partly) | Covered |  |
| REQ-C-112 | Found while planning: the in-place export reads e(sample) after _estimates hold. The fix and its regression test ride DT-19's commit with a 'Found while planning' line and a CHANGELOG 'Fixed' line; no new GAPS4 row | DECISIONS A-20 | -- | 35-08 | 35-08-01 (Q3508-2/3), 35-08-04, 35-08-05 | Covered | 35-08 Notes add that the orchestrator may give it its own id instead, a minor loosening of A-20's 'no new GAPS4 row'. |
| REQ-C-113 | 41-02 owns the by() key clockdir notes (pos(13) included) | DECISIONS A-21 | -- | 41-02 | 41-02-06, 41-02-07 (D-41-02.c, Q4102-3) | Covered |  |
| REQ-C-114 | 49-02 owns every other named-style note | DECISIONS A-21 | -- | 49-02 | 49-02-04, 49-02-05 (LT-25) | Covered | 49-02 verifies earlier closures (by(, bgcolor()) of 41-02) and does not redo them. |
| REQ-A-01 | The plan covers all 17 audit packages | Q1 (with A3) | §1, §4 | index Overview, M3, Appendix A; WP-33..WP-38, WP-40..WP-49 | 33-01-02 | Covered | 33-01-02 registers every live item of all packages from Appendix A. P4 has no WP of its own after A3; its items sit in WP-35 (35-09), and plot:PT-10 is withdrawn (A2). |
| REQ-A-02 | Every deduplicated audit item is planned, including items D40 left without a ruling | Q1; D40 preamble ('no ruling' items stay open for planning) | §1, §8 | index Appendix A; 33-01 | 33-01-01, 33-01-02 | Covered | 221 live rows (224 printed, 3 withdrawn by Q48, Q50 and A2). gen_gaps4 (N-1) refuses to run unless the 221 Appendix A rows equal the 221 audit bullets. |
| REQ-A-03 | Each item is fixed, or documented where its ruling says documentation resolves it | Q1 | §1, §8 | index Appendix A (Kind column), every item section | 33-01-02 (Kind and FIX_OVERRIDE per row); each item's closing task (e.g. 34-01-04, 36-04-02, 38-01-02); index WE.1 | Covered | plot:PT-13 ends Partly (D41, PD-9, 34-09-08). PRD §8 lists only Closed, Documented and Withdrawn, so it does not mention Partly. |
| REQ-A-04 | Seventeen work packages, one per audit package | Q2 | §1 | index Overview, Work packages | none | Superseded | A3 removed WP-39, leaving 16 package WPs (33-38 and 40-49). WP-50 (Q29) is added for suite speed. |
| REQ-A-05 | Each WP has its own register | Q2 (refined by Q37, Q41) | §4 (WP-33), §8 | 33-01 (GAPS4.md, PD-1); index WE.2 | 33-01-02; index WE.2 | Covered | Implemented as one shared GAPS4.md with a separate '## WP-NN' table per WP. Each closeout appends its WP to GAPS4_CLOSED_WPS. |
| REQ-A-06 | Each WP has its own closeout | Q2 | §8 | index W0/WE steps | index WE.1-WE.6 (per WP) | Covered | No WP starts before the previous one has closed. |
| REQ-A-07 | Done means every item is closed with a BUGS entry and a pinning test, or documented with a test that reads its help sentence | Q3 (Q42) | §8 | 33-01; every item section; index PD-4, R5, G1 | 33-01-02 (opens 221 entries); each item's closing task; index WE.1 | Covered | Entries use PD-4's closed and documented forms. Documented items are pinned by help-claim tests. |
| REQ-A-08 | Done means make test-all is green | Q3 | §8 | index Verification gates G2/G3 | index batch step k.4; index WE.4 | Covered | Run at the end of every batch and at every WP closeout. |
| REQ-A-09 | The P13 corpus is re-run and the README gallery built at the final closeout | Q3 | §4 (WP-33), §8 | 33-08 (tooling); index final WE | 33-08-01..33-08-05; index WE.7 | Covered | WE.7 runs make corpus and make gallery, the first and only gallery build, then the maintainer checkpoint, then the commit. |
| REQ-A-10 | Timing: the README gallery is generated in WP-33 and regenerated at the final closeout | Q3, Q6 | §4 (WP-33) | 33-08 (D-33-08.p), 33-14 (D-33-14.f); index WE.7 | 33-08-04 (smoke build in scratch, docs/README untouched); 33-14-02, 33-14-05 | Superseded | P4-8: WP-33 builds no gallery page and no README block. The only build is at WP-50 WE.7. |
| REQ-A-11 | Draw matamatrix() plots | Q4 | §7 | 35-09 (PD-10, A-9) | 35-09-03 | Superseded | A2: matamatrix() does not exist in Stata, and plot:PT-10 is withdrawn. 35-09-03 removes the by-name path and the help mentions (R14). |
| REQ-A-12 | Accept a bare plot after a parenthesised group: (scatter ..) line .. | Q4 (P4 under P11) | §4 (WP-35) | 35-09 (syn:SD-1) | 35-09-05 | Covered | Q3509-6/7, with a help sentence and a CHANGELOG line. |
| REQ-A-13 | Accept an option-less \|\| inside one group | Q4 (P4 under P11) | §4 (WP-35) | 35-09 (syn:SD-13) | 35-09-06 | Covered | A \|\| piece that holds options is refused in twoway's words. |
| REQ-A-14 | Draw the empty graph with no axes and refuse its axis options as twoway does | Q4 (P4 under P11) | §4 (WP-35) | 35-09 (plot:PT-4) | 35-09-04 | Covered | Q3509-4/5. HR-8 help rewrite; both modes are covered by a parity entry. |
| REQ-A-15 | WPs are numbered WP-33..WP-49 in the D40 order with the stated package mapping | Q5 | §1, §4 | index Work packages table, Overview run order | none (plan structure) | Covered | The mapping matches for every WP (33=P13, 34=P1, 35=P11, 36=P2, 37=P12, 38=P3, 40=P5 ... 49=P17). |
| REQ-A-16 | WP-39 = P4 (P4's remaining items in a WP of their own) | Q5, Q4 | §1, §4 | 35-09 | 35-09-01..35-09-06 | Superseded | A3 removed WP-39 and left its number unused. Its items moved to WP-35. A3 sent the sunflower sentence to WP-48, but PD-10 later moved it to 35-09. |
| REQ-A-17 | All WPs are planned inside this .ultraplan/ | Q5 | none | sections/index.md, sections/* | none (plan structure) | Covered | All 92 section files are in .ultraplan/sections. |
| REQ-A-18 | Sections are numbered per WP (33-01, ...) | Q5 | none | index Section manifest | none (plan structure) | Covered | Sections are NN-MM and tasks NN-MM-KK. |
| REQ-A-19 | WP closeout: the WP's items are closed in BUGS and the register, with pins | Q6 | §8 | index WE | index WE.1, WE.2 | Covered | WE.1 checks that every row is Closed, Documented or Partly and that no 'pending' remains. |
| REQ-A-20 | WP closeout: make test-all is green | Q6 | §8 | index WE | index WE.4 | Covered |  |
| REQ-A-21 | WP closeout: a ROADMAP line | Q6 | §8 | index WE | index WE.3 | Covered | WE.3 writes a full '## WP-NN ... DONE' section. |
| REQ-A-22 | The corpus re-run and the gallery refresh happen only at the final WP's closeout | Q6 | §8 | index WE (WE.7 final only); 33-14 | index WE.7 | Covered | No per-WP closeout runs the corpus. 33-14's single run in WP-33 is the baseline that P4-8 allows. |
| REQ-A-23 | Refuse every capitalised plot-type spelling: lower case only, whatever the file system | Q7 | §4 (WP-35) | 35-09 (plot:PT-3) | 35-09-01, 35-09-02 | Covered | The refusal is r(198) '<word> is not a twoway plot type'. HC1-08 and test_help_claims_1 pins are flipped. |
| REQ-A-24 | Note the capitalised-name refusal under Differences | Q7 | §5 | 35-09 | 35-09-02 | Covered | A Differences line links to Plot types. |
| REQ-A-25 | Measure first: research lists each dash-only word with twoway's answer | Q8 | §4 (WP-35) | RESEARCH §3 P11 ([C §6], [S §5]); 35-07 | 35-07-01 | Covered | 35-07-01 commits extract_dash_only_truth.do and its fixture. A fixture row that differs from the research table stops the task. |
| REQ-A-26 | The maintainer decides each dash-only word in Phase 4, and the plan carries out each decision | Q8 | §4 (WP-35) | DECISIONS P4-7, P4-9; index PD-18; 35-07; 42-05 (CV-14); 35-04 (bw()) | 35-07-01..35-07-03; 42-05-07, 42-05-08; 35-04-06 | Covered | 38 synonyms are refused with a hint line naming twoway's spelling. hover() and table are kept. |
| REQ-A-27 | The README gallery serves Stata users evaluating dash who paste a twoway command and want the same picture | Q9 | §3, §5 | 33-08; index WE.7 | 33-08-02 (readme_block, readme_candidates); index WE.7 | Covered | Each caption shows the twoway command. Candidates are help-file examples spread over 12 groups. |
| REQ-A-28 | Gallery captions use Stata terms and show no internals | Q9 | §3 | 33-05 (summary), 33-08 (captions) | 33-05-02, 33-08-02 | Covered | Covered after A-24 (Stata terms in captions; ids only in corpus.json) |
| REQ-A-29 | Sections are run by worktree agents under ../dash-wt/_tools/agent-rules.md | Q10 | §3 | index M13, Batch execution order | index batch steps k.1, k.2 | Covered | PLAN's file map has agent-rules.md re-issued for WP-33 onward. |
| REQ-A-30 | Work is merged by cherry-pick with picks.sh | Q10 | §10 (risk 3) | index k.3, R1-R14; 33-01 | 33-01-05 (picks.sh edits handed back); index batch step k.3 | Covered |  |
| REQ-A-31 | Three Stata slots | Q10 | none | index k.2; 33-03 (jobs=3) | index batch step k.2 | Covered | Each section holds one slot through scripts/stata_slot.sh. |
| REQ-A-32 | The orchestrator runs the gates | Q10 | §8 | index k.4, W0/WE, G2/G3 | index batch step k.4; index WE.4 | Covered |  |
| REQ-A-33 | 2-3 sections per batch | Q11 | none | index M13, Batch execution order | index batch table | Covered | Covered as ruled by A-22 (single-section batches where dependencies or R11/R12 force them) |
| REQ-A-34 | 1-4 tasks per section | Q11 | none | all | e.g. 41-05-01..41-05-12, 44-03-01..44-03-13 | Superseded | A-14: the count is per item, so multi-item sections hold more tasks. |
| REQ-A-35 | Up to three sections run in parallel | Q11 | none | index Overview, k.2 | index batch step k.2 | Covered |  |
| REQ-A-36 | The harness assigns verdicts automatically | Q12 | §4 (WP-33) | 33-05; 33-08 (make corpus) | 33-05-02, 33-05-03, 33-08-03 | Covered | Beyond this, the maintainer also confirms the calibration labels (33-05-05) and the baseline counts (33-14-04). |
| REQ-A-37 | The maintainer signs off on the generated gallery once per refresh, before it is committed | Q12 | §8 | index final WE | index WE.7 | Covered | WE.7 holds a maintainer checkpoint before the commit. |
| REQ-A-38 | The corpus includes every example in the twoway help files (about 128 plus the gr_example2 named ones) | Q13 | §4 (WP-33) | 33-02 | 33-02-01, 33-02-02, 33-02-03 | Covered | Covered by help_links, ado_programs (gr_example2, tsline_ex) and split_setup. 198 distinct examples were measured. |
| REQ-A-39 | The corpus includes every twoway example in g.pdf's [G-2] graph twoway and [G-3] option entries | Q13 | §4 (WP-33) | 33-02 | 33-02-02, 33-02-03 | Covered | gpdf_commands reads all of g.pdf (a superset), filtered to the types dash draws. pdftotext is a dev tool; when it is missing the g.pdf source is skipped with a message. |
| REQ-A-40 | The corpus includes the repository's examples/ folder | Q13 | §4 (WP-33) | 33-02 | 33-02-02 | Covered | example_commands builds each twoway twin with the dash-only words removed. |
| REQ-A-41 | The corpus includes the audit's probe commands | Q13 | §4 (WP-33) | 33-02 | 33-02-02 (--freeze-audit into audit_probes.txt) | Covered | Covered after A-26 (hand-curated prose probes in audit_probes.txt) |
| REQ-A-42 | Every extracted example is run in the corpus | Q13 | §4 (WP-33) | 33-02 (dedupe) | 33-02-02, 33-02-03 | Superseded | P4-2 keeps one example per combination of plot types and option names (about 425 of 636). Dropped duplicates are listed in extract_duplicates.tsv. |
| REQ-A-43 | webuse datasets are downloaded once into a git-ignored local cache | Q14 | §6 | 33-02 (datasets.py, scripts/corpus/.gitignore); 33-08 (make corpus) | 33-02-02, 33-02-03 | Covered | Covered after A-26 (fetch skips cached datasets) |
| REQ-A-44 | An offline run uses the cache and names any missing dataset | Q14 | §6 | 33-02 (rewrite_setup); 33-03; 33-08 | 33-02-02, 33-03-02, 33-08-02 | Covered | Covered after A-26 (missing dataset named once) |
| REQ-A-45 | twoway's picture is an SVG | Q15 | §5, §6 | 33-03 | 33-03-01, 33-03-02, 33-03-03 | Covered | graph export as(svg) at each example's own size (C2). |
| REQ-A-46 | twoway's SVG is embedded in the dash HTML output | Q15 | §5 | 33-06 (image panel); 33-08 (page.do); index WE.7 | 33-06-01..33-06-05, 33-08-02, 33-08-04; index WE.7 | Covered | The SVG is sanitised and embedded as a data: URI <img> inside a Bokeh Div. |
| REQ-A-47 | One gallery page holds all examples | Q16 (Q58) | §4 (WP-33), §5 | 33-08 (pages, write_index); 33-06 link() | 33-08-02, 33-08-04 | Superseded | P4-1: one dash page per plot type plus a dash-built index page (A-17 link()). PRD §5 still says 'one page built by dash, with tabs by plot type', which is out of date. |
| REQ-A-48 | The gallery page is built with dash itself | Q16 | §4, §5 | 33-06, 33-07, 33-08; index WE.7 | 33-06-01..33-06-05, 33-07-01..33-07-05, 33-08-02, 33-08-04; index WE.7 | Covered | Each page is one dash build using image panels, with frames for each dataset (C4, P4-4). |
| REQ-A-49 | Each example's twoway SVG is shown beside its live dash graph | Q16 (Q58) | §5 | 33-08 | 33-08-02, 33-08-04 | Covered | Covered after A-23 (static only for a dataset missing from the cache) |
| REQ-A-50 | Every example appears on the gallery page | Q16 | §4 (WP-33) | 33-05 (gallery flag), 33-08 | 33-05-02, 33-08-02 | Superseded | P4-10 shows only examples twoway draws; refused examples stay as data in corpus.json. P4-2 removes duplicates. |
| REQ-A-51 | The README shows the dash graph as a static SVG exported by Bokeh | Q17 | §5 | 33-04 (export, normalise_svg); 33-08 (README block); index WE.7 | 33-04-03, 33-04-04, 33-08-02; index WE.7 | Covered | Uses BokehJS export('svg') over DevTools, not output_backend='svg'. The output is normalised and deterministic. |
| REQ-A-52 | Both README columns are vector | Q17 | §5 | 33-04 | 33-04-03 | Covered | Covered after A-26 (README admits only fully vector pairs) |
| REQ-A-53 | Verdicts are geometry first: ticks, labels, titles, keys | Q18 | §4 (WP-33) | 33-05 | 33-05-02 | Covered | Checks: x_ticks, y_ticks, x_labels, y_labels, axis_titles, titles, legend (D-33-05.b). |
| REQ-A-54 | Verdicts check glyph counts and extents | Q18 | §4 (WP-33) | 33-04 (DUMP_JS), 33-05 | 33-04-03, 33-05-02 | Covered | Checks: glyphs, glyph_extents, marker_shape. A by() graph is compared on its first panel only. |
| REQ-A-55 | Verdicts compare colours | Q18 | §4 (WP-33) | 33-05 | 33-05-02 | Covered | Covered after A-25 (colours judged within a recorded tolerance) |
| REQ-A-56 | twoway's SVG is compared against dash's Bokeh model | Q18 | §4 (WP-33) | 33-04, 33-05 | 33-04-03, 33-05-02 | Covered | twoway_geometry (stdlib SVG readers) against dash_geometry (BokehJS view dump). |
| REQ-A-57 | A known-differences ledger | Q18 | §10 (risk 5) | 33-05; every closing commit (D-33-05.i) | 33-05-02, 33-05-04 | Covered | ledger.tsv compiles to corpus_ledger.json, keyed by GAPS4 id, and must stay live against GAPS4 states (A-10). |
| REQ-A-58 | An image-similarity score as a secondary signal | Q18 | §4 (WP-33) | 33-05 | 33-05-03 | Covered | SSIM in numpy+scipy. Under A-4 it can only move a geometry-clean pair from Same to Close. |
| REQ-A-59 | New developer-only dependencies are allowed in the dev/test tier only | Q19 | §6 | PLAN Tech stack; 33-02 (D-33-02.e); 33-05 (TR-33-05.6) | 33-02-02, 33-05-03 | Covered | None is planned. pdftotext is an existing dev tool; scikit-image appears only in a release-tier parity test that is skipped when absent. |
| REQ-A-60 | Nothing new for dash users or in dash_requirements.txt | Q19 | §6, §9 | all (exclusion) | none | Covered | No section edits dash_requirements.txt or adds a user dependency (TR-33-05.6). |
| REQ-A-61 | The gallery is committed in the repository under docs/gallery/ | Q20 | §6, §9 | 33-08 (.gitignore negations, TestTheCommittedGallery); index WE.7 | 33-08-01, 33-08-03; index WE.7 | Covered |  |
| REQ-A-62 | Enabling GitHub Pages is a separate maintainer step | Q20 | §6, §9 | DECISIONS A-10; 33-08 (D-33-08.j) | 33-08-02 (README link wording) | Covered | The exclusion is stated and the plan contains no Pages work. |
| REQ-A-63 | heatmap and sunflower are not twoway plot types: never listed as plot types, gaps, tests or audit targets | D40 (decisions bullet 1; P4) | §7 | index M1, R14, Appendix A; 33-01 | 33-01-01, 33-01-02 (BANNED check, AC-33-01.5); index rule R14 | Covered | P4's heatmap and sunflower items are withdrawn and have no GAPS4 rows. |
| REQ-A-64 | Contour's own heatmap option stays in scope | D40 | none | index M1; 33-01 (N-1 BANNED regex exempts 'heatmap option') | 33-01-02; index rule M1 | Covered |  |
| REQ-A-65 | dash.sthlp:737-742 stops calling sunflower a twoway plot type | D40 (P4 help follow-on) | §4 (WP-46..49 line) | 35-09 (PD-10; HR-5, HR-22); 48-04 | 35-09-03, 48-04-01 | Covered | A3 routed this to WP-48, but PD-10 and Appendix B do it in 35-09; 48-04 verifies it with TestHR05and22. PRD §4 still places it under P16. |
| REQ-A-66 | sunflower is refused like any word that is not a twoway plot type | D40 (P4) | §7 | 35-09 (TR-35-09.2, A-9) | 35-09-03 | Covered | Pinned by TestGeneric::test_no_by_name_refusal and Q3509-3. |
| REQ-A-67 | No programming yet: implementation waits for a later planning process | D40 | none | this plan (DISCOVERY) | none | Superseded | Superseded by DISCOVERY Q1-Q3: this plan is the later planning process that authorises the work. |
| REQ-A-68 | Planning order: P13 first, then 1, 11, 2, 12, 3, 4, 5, 6-10, 14-17 | D40 | §1, §4 | index Overview run order, Batch execution order; PLAN Execution strategy | index WE (each WP closed before the next) | Covered | Order: 33, 34, 35, 36, 37, 38, 40-49, 50. P4's items run in WP-35 (A3). |
| REQ-A-69 | P1: resolve every item that can be resolved (all ten) | D41 (P1) | §2, §4 (WP-34) | 34-01..34-09 | 34-01-01..34-09-08 | Covered | 11 GAPS4 rows. plot:PT-13 ends Partly by ruling. |
| REQ-A-70 | P1(1): the histogram bin axis is ticked over the first and last bin midpoints | D41 (P1 item 1) | §4 | 34-01 (AX-4) | 34-01-01, 34-01-02, 34-01-03, 34-01-04 | Covered | Both modes, including the _FILTER_JS twin. |
| REQ-A-71 | P1(2): by() panels tick x1 at #4 as well as y | D41 (P1 item 2) | §4 | 34-02 (AX-2) | 34-02-01, 34-02-02 | Covered |  |
| REQ-A-72 | P1(3): range() beyond the data puts ticks over the data only | D41 (P1 item 3) | §4 | 34-03 (AX-1) | 34-03-01, 34-03-02, 34-03-03 | Covered |  |
| REQ-A-73 | P1(4): by()'s shared y title is painted | D41 (P1 item 4) | §4 | 34-02 (VF-2) | 34-02-03, 34-02-04, 34-02-05 | Covered | Pinned by a Chrome pixel test. |
| REQ-A-74 | P1(5): aspectratio() with xsize()/ysize() draws the frame at that ratio and size, with no Bokeh validation error | D41 (P1 item 5) | §4 | 34-04 (VF-3); 45-04 (A-1) | 34-04-01, 34-04-02, 34-04-03 | Covered | check_integrity and the log are checked for E-1023/E-10/W-10 (TR-34-04.3, Q3404-2). |
| REQ-A-75 | Never draw a 0 px plot | D41 (P1) | §4 | 34-04; 45-04 | 34-04-01, 34-04-02, 34-04-03 | Covered | BR-34-04.2 and TestFixedFrameInChrome at 1400 and 375 px. |
| REQ-A-76 | P1(6): the default area plot and its key are outlined as twoway outlines them | D41 (P1 item 6) | §4 | 34-05 (PIC-1) | 34-05-01, 34-05-02, 34-05-03, 34-05-04 | Covered | The full outline ring (A-6). |
| REQ-A-77 | P1(7): a ci type with nofit counts one plot number | D41 (P1 item 7) | §4 | 34-06 (PIC-3) | 34-06-01, 34-06-02, 34-06-03 | Covered |  |
| REQ-A-78 | P1(8): confirm by a direct twoway probe that time-series operators are allowed, before any L./D. work | D41 (P1 item 8) | §4 | 34-07 (PD-16) | 34-07-01, 34-07-02 (checkpoint), 34-07-03 | Covered | Regenerates the operator truth with 22 new probes. Any difference stops the section until the maintainer rules. |
| REQ-A-79 | P1(8): fix the missing-end-row date axis, for the operator part and for a plain y | D41 (P1 item 8) | §4 | 34-07 (TR-4) | 34-07-04, 34-07-05, 34-07-06 | Covered | Per-series complete-case tokens. |
| REQ-A-80 | P1(9): an a(b)c rule crossing zero labels zero as 0, never 5.551e-17 | D41 (P1 item 9) | §4 | 34-08 (DG-3) | 34-08-01, 34-08-02, 34-08-03 | Covered |  |
| REQ-A-81 | P1(10): axes at build use Stata's own ticks wherever Stata can be asked at export | D41 (P1 item 10) | §4 | 34-09 (AX-3) | 34-09-01..34-09-07 | Covered | A-16/A-19 apply in both modes. |
| REQ-A-82 | The natscale misses after a filter move stay open | D41 (P1 item 10) | §4, §7 | 34-09 (PD-9) | 34-09-08 | Covered | plot:PT-13 ends Partly, with the natscale entry re-scoped as its residual. |
| REQ-A-83 | P2: dash and dash_setup use the Python Stata finds or the user sets, never refuse a Python Stata accepts, and never insist on their own discovery | D40 (P2) | §4 (WP-36), §6 | 36-01 (plat:PT-1; C5, M8, A-8) | 36-01-01, 36-01-02, 36-01-03, 36-01-04 | Covered | No pre-check and no python query probe. The harness follows the same rule. |
| REQ-A-84 | P2: the other items (platforms, floor, lock, ~, large data, WebGL) have no D40 ruling and stay open for planning | D40 (P2) | §4 (WP-36), §7 | 36-02, 36-03, 36-04 | 36-02-01..36-02-03, 36-03-01..36-03-03, 36-04-01..36-04-04 | Covered | Later rulings decided them: Q31, Q33, Q34, Q35, Q46, Q47, Q49, A1. |
| REQ-A-85 | P3: resolved by help documentation only (a dashboard is not a Stata graph) | D40 (P3) | §4 (WP-38), §7 | 38-01, 38-02 | 38-01-01..38-01-04, 38-02-01..38-02-04 | Covered | No code changes. PRD §7 excludes graph memory, export, .gph, play() and the Graph Editor. |
| REQ-A-86 | P3 help: name() registers a graph; there is no graph in memory; graph export/save/use/display/combine, putdocx/putpdf/putexcel, dyndoc and markdown cannot use it | D40 (P3) | §4 | 38-01 (syn:SD-17, GW-12, ECO-4) | 38-01-01, 38-01-02, 38-01-03 | Covered | TR-38-01.3 lists every one of these commands. ECO-4 maps graph combine to layout(). |
| REQ-A-87 | P3 help: each registry rc and message difference (name() length and '__', duplicate name, saving() onto an existing file, nodraw with saving(,asis), play(), name(g, rep), dash clear g2) | D40 (P3) | §4 | 38-02 (GW-13, GW-14, GW-15, GW-16, GW-9, ECO-5) | 38-02-01, 38-02-02, 38-02-03, 38-02-04 | Covered |  |
| REQ-A-88 | P3 help: browser previews and leftover s() macros | D40 (P3) | §4 | 38-01 (ECO-15, ECO-7) | 38-01-04 | Covered |  |
| REQ-A-89 | P3 help: the data is evaluated at build time | D40 (P3) | §4 | 38-01 (ECO-1) | 38-01-03 | Covered | Names the frame f: prefix (33-07). |
| REQ-A-90 | P4 audit correction: internal and undocumented class names (rbarm, rbspike, ksm, patch, normgen, ipoint, meta_*, y*xview) are withdrawn | D40 (P4) | §7 | index Appendix A (no rows) | none | Covered | The exclusion is stated in PRD §7 and no work is planned. |
| REQ-A-91 | P4 audit correction: adopath-defined types are withdrawn | D40 (P4) | none | index Appendix A (no rows); 33-02 (D-33-02.b filter) | none | Covered | Covered (PRD section 7 and index M1 state the exclusion) |
| REQ-A-92 | P4's remaining items (empty graph's axes and options, bare plot after a group, \|\| inside one group) are carried under P11 (compatible with twoway) | D40 (P4) | §4 (WP-35) | 35-09 | 35-09-04, 35-09-05, 35-09-06 | Covered | These are the same requirements as REQ-A-12..14. |
| REQ-A-93 | P4's capitalised type names are made compatible with twoway (accepted where twoway accepts them) | D40 (P4 under P11) | §4 (WP-35) | 35-09 (plot:PT-3) | 35-09-01, 35-09-02 | Superseded | Q7 (M7) refuses all capitals, including those twoway takes on a case-insensitive file system, and documents this under Differences. |
| REQ-A-94 | P5: every observation cap is documented in the help, under Differences from twoway and under Resource limits | D40 (P5) | §4 (WP-40), §7 | 40-02; 33-15 (help) | 40-02-01..40-02-04, 33-15-03 | Covered | plat:PT-8, plat:PT-10 and sil:SD-12 are documented in both places. |
| REQ-A-95 | P5: document the embedded-cell cap (5M, 20M ceiling) | D40 (P5) | §4 (WP-33), §7 | 33-15; 40-02 | 33-15-01..33-15-04, 40-02-02 | Superseded | P4-3 removed the cap (and the page-bytes cap). The help states that there is no size cap. |
| REQ-A-96 | P5: document that the cap counts _N whatever if/in selects | D40 (P5) | §4 (WP-40) | 40-01 (plat:PT-7) | 40-01-01..40-01-04 | Superseded | P4-3 left no cap to count against. Q45's fix stays as a size measure: only the selected rows are exported and nothing is refused. |
| REQ-A-97 | P5: document by()'s group limit | D40 (P5) | §4 (WP-40) | 40-02 (plat:PT-10) | 40-02-02 | Covered |  |
| REQ-A-98 | P5: caps not on observations (plots, reflines, added texts, n(), bin(), lpoly degree, rebinning, tick clamp, msize, fpfit grid, text length) have no D40 ruling | D40 (P5) | §7 | 40-02 | 40-02-02, 40-02-03, 40-02-04 | Covered | Decided by Q44: all are documented and every count cap is kept. |
| REQ-A-99 | P6-P10: resolve every item Bokeh can draw | D40 (P6-P10) | §4 (WP-41..45), §7 | 41-01..41-06, 42-01..42-05, 43-01..43-07, 44-01..44-05, 45-01..45-05 | 41-01-01..41-06-05, 42-01-01..42-05-08, 43-01-01..43-07-06, 44-01-01..44-05-05, 45-01-01..45-05-04 | Covered | Q24 defines 'supported by Bokeh' as shipped models, CustomJS and composites. Research found no item unsupported (M11). |
| REQ-A-100 | P6-P10: items Bokeh cannot draw are documented under Differences | D40 (P6-P10 planning proposal) | §4 | 43-04, 43-07, 44-02 | 43-04-04, 43-07-06, 44-02-09 | Covered | Confirmed by Q23 and M11. Three composite residuals are documented: the key cell (LT-21), partial SMCL in marker labels and tooltips (ST-14), and dates past the browser's range (AX-15). |
| REQ-A-101 | P11: accept what twoway accepts and refuse what it refuses, with its rc and words | D40 (P11) | §4 (WP-35) | 35-01..35-09 | 35-01-01..35-01-03, 35-02-01..35-02-04, 35-03-01..35-03-07, 35-04-01..35-04-06, 35-05-01..35-05-03, 35-06-01..35-06-07, 35-07-01..35-07-03, 35-08-01..35-08-05, 35-09-01..35-09-06 | Covered |  |
| REQ-A-102 | P12: one Stata-side zero-observation check in one function, after each plot's and the graph's if/in and before Python, for every plot type | D40 (P12) | §4 (WP-37) | 37-01 (DG-1, PD-15) | 37-01-01, 37-01-02, 37-01-03, 37-01-04 | Covered | _dash_zero_obs_check runs on every route before _dash_write_data. |
| REQ-A-103 | P12: refuse zero observations with an error, and note in the help where twoway draws instead | D40 (P12) | §4 (WP-37) | 37-01 | 37-01-02, 37-01-03, 37-01-04 | Superseded | C1, M9 and Q21 copy twoway per case: dash draws the empty graph where twoway draws and refuses with twoway's rc and words (plus a plot-naming line, Q22) where twoway refuses. No difference is left to note. |
| REQ-A-104 | P12: fix the contour crash on zero observations | D40 (P12) | §4 (WP-37) | 37-01 | 37-01-03 | Covered | Draws an empty contour and its titled key in both modes. |
| REQ-A-105 | P12's other items (rarea cmissing, contour subsample, contour with no surface, lfit xlog/xtransform, lpolyci zero df, numeric limits, ties) have no D40 ruling | D40 (P12) | §4 (WP-37), §7, §10 | 37-02, 37-03, 37-04, 37-05 | 37-02-01..37-02-03, 37-03-01..37-03-04, 37-04-01..37-04-04, 37-05-01..37-05-03 | Covered | Decided by Q26/C3, Q27 and the plan. |
| REQ-A-106 | P13 is the top priority and is planned first | D40 (P13) | §1, §4 | WP-33 (batch 33.1 first); 33-10..33-13 | 33-01-01 onward; 33-10-01..33-13-06 | Covered | P13's other coverage items (TR-11, TR-23, BY-23, BY-24, stat:PT-23, CV-16, syn:SD-20, GW-11) are closed by 33-10..33-13. |
| REQ-A-107 | P13: a broad corpus of twoway examples (help files, g.pdf) is run under both twoway and dash and compared | D40 (P13) | §4 (WP-33) | 33-02, 33-03, 33-04, 33-05, 33-14; index WE.7 | 33-02-01..33-02-03, 33-03-01..33-03-03, 33-04-01..33-04-04, 33-05-01..33-05-05, 33-14-01..33-14-05; index WE.7 | Covered | De-duplicated per P4-2. |
| REQ-A-108 | P13: the output (command, twoway picture, dash picture, verdict) can be injected into README.md as a gallery that shows dash's flexibility | D40 (P13) | §4, §5, §9 | 33-08; index WE.7 | 33-08-01..33-08-05; index WE.7 | Covered | readme_block and replace_block write between markers. readme_candidates spans 12 groups. |
| REQ-A-109 | P14: resolve (fix all) | D40 (P14) | §4 (WP-46) | 46-01, 46-02 | 46-01-01..46-01-06, 46-02-01..46-02-04 | Covered |  |
| REQ-A-110 | P14: fix RH-8 (histogram/rbar recast plus horizontal) | D40 (P14) | §4, §7 | 46-02 | 46-02-05, 46-02-06 | Superseded | Q25 (M12) keeps dash's clean transpose and documents twoway's picture. |
| REQ-A-111 | P15: resolve (fix all) | D40 (P15) | §4 (WP-47) | 47-01..47-06 | 47-01-01..47-06-08 | Covered |  |
| REQ-A-112 | P15: fix the jitter() items | D40 (P15) | §7 | none | none | Superseded | Q50 keeps jitter's noise, undocumented. basic:PT-7 and its findings are withdrawn. |
| REQ-A-113 | P16: resolve (fix all) | D40 (P16) | §4 (WP-48), §9 | 48-01, 48-02, 48-03, 48-04 | 48-01-01..48-04-06 | Covered | Includes the HR-1..HR-22 sweep. |
| REQ-A-114 | P17: resolve (fix all) | D40 (P17) | §4 (WP-49) | 49-01, 49-02 | 49-01-01..49-02-08 | Covered |  |
| REQ-A-115 | P17: remove dash's extra refusal lines and Supported list (plot:PT-7) | D40 (P17) | §7 | 49-01 (PD-11) | 49-01-01, 49-01-02, 49-01-03 | Superseded | Q43 (M12, PD-11) gives every refusal twoway's words as its first line and keeps dash's extra lines and the Supported list. |

## Audit Item-to-Task Mapping

| Lead id | Section | Tasks naming it | Closing task(s) |
|---|---|---|---|
| TR-11 | 33-10 | 33-10-01, 33-10-03, 33-10-04 | 33-10-03 |
| syn:SD-20 | 33-10 | 33-10-04, 33-10-06 | 33-10-06 |
| TR-23 | 33-11 | 33-11-02 | 33-11-02 |
| GW-11 | 33-11 | 33-11-03, 33-11-04, 33-11-06 | 33-11-06 |
| BY-23 | 33-12 | 33-12-01, 33-12-02, 33-12-03 | 33-12-03 |
| BY-24 | 33-12 | 33-12-04, 33-12-05, 33-12-06 | 33-12-06 |
| stat:PT-23 | 33-13 | 33-13-01, 33-13-03 | 33-13-03 |
| CV-16 | 33-13 | 33-13-04, 33-13-05, 33-13-06 | 33-13-06 |
| TR-2 | 33-14 | 33-14-01, 33-14-05 | 33-14-05 |
| AX-4 | 34-01 | 34-01-04 | 34-01-04 |
| VF-3 | 34-04 | 34-04-03 | 34-04-03 |
| PIC-1 | 34-05 | 34-05-04 | 34-05-04 |
| AX-1 | 34-03 | 34-03-03 | 34-03-03 |
| PIC-3 | 34-06 | 34-06-03 | 34-06-03 |
| DG-3 | 34-08 | 34-08-03 | 34-08-03 |
| TR-4 | 34-07 | 34-07-03, 34-07-06 | 34-07-03, 34-07-06 |
| AX-2 | 34-02 | 34-02-01, 34-02-02, 34-02-05 | 34-02-02 |
| VF-2 | 34-02 | 34-02-03, 34-02-05 | 34-02-05 |
| AX-3 | 34-09 | 34-09-01, 34-09-05, 34-09-06, 34-09-07, 34-09-08 | 34-09-05, 34-09-06, 34-09-07 |
| plot:PT-13 | 34-09 | 34-09-08 | 34-09-08 |
| MS-1 | 35-01 | 35-01-03 | 35-01-03 |
| syn:SD-3 | 35-02 | 35-02-03, 35-02-04 | 35-02-04 |
| plot:PT-3 | 35-09 | 35-09-01, 35-09-02, 35-09-04 | 35-09-02 |
| plot:PT-4 | 35-09 | 35-09-04, 35-09-05 | 35-09-04 |
| syn:SD-1 | 35-09 | 35-09-05, 35-09-06 | 35-09-05 |
| syn:SD-13 | 35-09 | 35-09-06 | 35-09-06 |
| stat:PT-7 | 35-03 | 35-03-01, 35-03-02, 35-03-03 | 35-03-02 |
| syn:SD-5 | 35-03 | 35-03-03, 35-03-04 | 35-03-03 |
| stat:PT-13 | 35-03 | 35-03-04, 35-03-05 | 35-03-04 |
| stat:PT-6 | 35-03 | 35-03-05, 35-03-06 | 35-03-05 |
| stat:PT-9 | 35-03 | 35-03-06, 35-03-07 | 35-03-06 |
| syn:SD-7 | 35-03 | 35-03-07 | 35-03-07 |
| basic:PT-8 | 35-06 | 35-06-01, 35-06-02 | 35-06-02 |
| GW-2 | 35-06 | 35-06-03 | 35-06-03 |
| GW-3 | 35-06 | 35-06-04 | 35-06-04 |
| GW-4 | 35-06 | 35-06-05 | 35-06-05 |
| sil:SD-8 | 35-06 | 35-06-06 | 35-06-06 |
| syn:SD-8 | 35-06 | 35-06-07 | 35-06-07 |
| stat:PT-1 | 35-04 | 35-04-01, 35-04-02, 35-04-06 | 35-04-02 |
| stat:PT-2 | 35-04 | 35-04-03 | 35-04-03 |
| stat:PT-5 | 35-04 | 35-04-04, 35-04-05 | 35-04-04 |
| stat:PT-8 | 35-04 | 35-04-05 | 35-04-05 |
| stat:PT-14 | 35-04 | 35-04-06 | 35-04-06 |
| basic:PT-9 | 35-05 | 35-05-01, 35-05-02, 35-05-03 | 35-05-02 |
| basic:PT-13 | 35-05 | 35-05-01, 35-05-03 | 35-05-03 |
| DT-15 | 35-07 | 35-07-01, 35-07-03 | 35-07-03 |
| DT-19 | 35-08 | 35-08-03, 35-08-05 | 35-08-05 |
| plat:PT-1 | 36-01 | 36-01-01, 36-01-04 | 36-01-04 |
| DG-14 | 36-02 | 36-02-03 | 36-02-03 |
| plat:PT-4 | 36-03 | 36-03-03 | 36-03-03 |
| plat:PT-5 | 36-04 | 36-04-01, 36-04-02 | commit boundary of the section |
| plat:PT-2 | 36-04 | 36-04-02 | commit boundary of the section |
| plat:PT-11 | 36-04 | 36-04-03 | commit boundary of the section |
| plat:PT-12 | 36-04 | 36-04-03 | commit boundary of the section |
| plat:PT-6 | 36-04 | 36-04-03 | commit boundary of the section |
| plat:PT-16 | 36-04 | 36-04-04 | commit boundary of the section |
| plat:PT-14 | 36-04 | 36-04-04 | commit boundary of the section |
| DG-1 | 37-01 | 37-01-03, 37-01-04 | 37-01-04 |
| stat:PT-12 | 37-04 | 37-04-03, 37-04-04 | 37-04-04 |
| stat:PT-16 | 37-05 | 37-05-02, 37-05-03 | commit boundary of the section |
| DT-26 | 37-05 | 37-05-02, 37-05-03 | commit boundary of the section |
| stat:PT-21 | 37-05 | 37-05-03 | commit boundary of the section |
| DG-5 | 37-02 | 37-02-01, 37-02-02, 37-02-03 | 37-02-02 |
| DG-8 | 37-02 | 37-02-03 | 37-02-03 |
| TR-13 | 37-03 | 37-03-03, 37-03-04 | 37-03-04 |
| syn:SD-17 | 38-01 | 38-01-02 | commit boundary of the section |
| GW-12 | 38-01 | 38-01-02 | commit boundary of the section |
| ECO-1 | 38-01 | 38-01-03, 38-01-04 | commit boundary of the section |
| ECO-4 | 38-01 | 38-01-03 | commit boundary of the section |
| ECO-15 | 38-01 | 38-01-04 | commit boundary of the section |
| ECO-7 | 38-01 | 38-01-04 | commit boundary of the section |
| GW-13 | 38-02 | 38-02-02 | commit boundary of the section |
| GW-14 | 38-02 | 38-02-02 | commit boundary of the section |
| GW-15 | 38-02 | 38-02-03 | commit boundary of the section |
| GW-16 | 38-02 | 38-02-03 | commit boundary of the section |
| GW-9 | 38-02 | 38-02-03 | commit boundary of the section |
| ECO-5 | 38-02 | 38-02-04 | commit boundary of the section |
| plat:PT-7 | 40-01 | 40-01-04 | 40-01-04 |
| plat:PT-8 | 40-02 | 40-02-02 | commit boundary of the section |
| plat:PT-9 | 40-02 | 40-02-02 | commit boundary of the section |
| plat:PT-10 | 40-02 | 40-02-02 | commit boundary of the section |
| stat:PT-15 | 40-02 | 40-02-03 | commit boundary of the section |
| sil:SD-1 | 40-02 | 40-02-03, 40-02-04 | commit boundary of the section |
| AX-16 | 40-02 | 40-02-03 | commit boundary of the section |
| sil:SD-11 | 40-02 | 40-02-04 | commit boundary of the section |
| sil:SD-12 | 40-02 | 40-02-04 | commit boundary of the section |
| sil:SD-13 | 40-02 | 40-02-04 | commit boundary of the section |
| BY-28 | 41-01 | 41-01-04 | 41-01-04 |
| BY-2 | 41-03 | 41-03-02, 41-03-03, 41-03-04, 41-03-05 | 41-03-03 |
| BY-27 | 41-03 | 41-03-04, 41-03-05 | 41-03-05 |
| sil:SD-7 | 41-03 | 41-03-07 | 41-03-07 |
| BY-10 | 41-06 | 41-06-01, 41-06-02, 41-06-05 | 41-06-02 |
| BY-16 | 41-06 | 41-06-03, 41-06-04, 41-06-05 | 41-06-04 |
| BY-1 | 41-02 | 41-02-02, 41-02-03, 41-02-04, 41-02-05, 41-02-06 | 41-02-03 |
| BY-12 | 41-02 | 41-02-04, 41-02-05, 41-02-06 | 41-02-05 |
| BY-7 | 41-02 | 41-02-06, 41-02-07 | 41-02-07 |
| TR-19 | 41-02 | 41-02-08 | 41-02-08 |
| BY-3 | 41-04 | 41-04-02, 41-04-03, 41-04-04 | 41-04-03 |
| BY-13 | 41-04 | 41-04-04, 41-04-05, 41-04-06 | 41-04-05 |
| BY-14 | 41-04 | 41-04-06, 41-04-07 | 41-04-07 |
| PIC-13 | 41-04 | 41-04-08 | 41-04-08 |
| BY-4 | 41-05 | 41-05-01, 41-05-02, 41-05-07, 41-05-12 | 41-05-02 |
| BY-5 | 41-05 | 41-05-03, 41-05-04 | 41-05-04 |
| BY-6 | 41-05 | 41-05-05, 41-05-06 | 41-05-05, 41-05-06 |
| BY-18 | 41-05 | 41-05-07, 41-05-08, 41-05-12 | 41-05-08 |
| VF-6 | 41-05 | 41-05-09, 41-05-10, 41-05-12 | 41-05-10 |
| GW-5 | 41-05 | 41-05-11 | 41-05-11 |
| CV-8 | 42-01 | 42-01-01, 42-01-02, 42-01-03, 42-01-04 | 42-01-02 |
| sil:SD-4 | 42-01 | 42-01-04 | 42-01-04 |
| CV-1 | 42-02 | 42-02-01, 42-02-02, 42-02-03 | 42-02-02 |
| CV-6 | 42-02 | 42-02-01, 42-02-04, 42-02-05 | 42-02-04 |
| CV-7 | 42-02 | 42-02-01, 42-02-06 | 42-02-06 |
| CV-2 | 42-05 | 42-05-01, 42-05-02, 42-05-05 | 42-05-02 |
| CV-9 | 42-05 | 42-05-04, 42-05-05, 42-05-08 | 42-05-04 |
| CV-10 | 42-05 | 42-05-05, 42-05-06, 42-05-07 | 42-05-06 |
| CV-14 | 42-05 | 42-05-07, 42-05-08 | 42-05-08 |
| CV-3 | 42-03 | 42-03-01, 42-03-02, 42-03-03, 42-03-04 | 42-03-02 |
| CV-15 | 42-03 | 42-03-01, 42-03-03, 42-03-04, 42-03-05, 42-03-06 | 42-03-04 |
| LT-12 | 42-03 | 42-03-01, 42-03-05, 42-03-06, 42-03-07, 42-03-08 | 42-03-06 |
| AX-12 | 42-03 | 42-03-01, 42-03-07, 42-03-08, 42-03-09, 42-03-10 | 42-03-08 |
| LT-22 | 42-03 | 42-03-01, 42-03-09, 42-03-10 | 42-03-10 |
| CV-4 | 42-04 | 42-04-01, 42-04-02, 42-04-03, 42-04-04 | 42-04-02 |
| CV-5 | 42-04 | 42-04-03, 42-04-04, 42-04-05, 42-04-06 | 42-04-04 |
| CV-11 | 42-04 | 42-04-05, 42-04-06 | 42-04-06 |
| LT-1 | 43-01 | 43-01-01, 43-01-03, 43-01-04, 43-01-06, 43-01-07 | 43-01-03 |
| LT-15 | 43-01 | 43-01-04, 43-01-06 | 43-01-06 |
| LT-13 | 43-01 | 43-01-07 | 43-01-07 |
| LT-11 | 43-06 | 43-06-01, 43-06-02, 43-06-03 | 43-06-02 |
| LT-20 | 43-06 | 43-06-03, 43-06-06 | 43-06-06 |
| LT-4 | 43-02 | 43-02-01, 43-02-02, 43-02-03 | 43-02-02 |
| LT-17 | 43-02 | 43-02-03, 43-02-04, 43-02-05, 43-02-06 | 43-02-05 |
| LT-5 | 43-02 | 43-02-06, 43-02-07 | 43-02-07 |
| LT-8 | 43-05 | 43-05-01, 43-05-02, 43-05-03 | 43-05-02 |
| LT-9 | 43-05 | 43-05-03, 43-05-05 | 43-05-03 |
| LT-14 | 43-05 | 43-05-04 | 43-05-04 |
| LT-16 | 43-05 | 43-05-05, 43-05-06 | 43-05-05 |
| LT-18 | 43-05 | 43-05-06, 43-05-07 | 43-05-06 |
| LT-19 | 43-05 | 43-05-07 | 43-05-07 |
| LT-24 | 43-05 | 43-05-08 | 43-05-08 |
| LT-2 | 43-03 | 43-03-01, 43-03-02, 43-03-04 | 43-03-02 |
| LT-3 | 43-03 | 43-03-03, 43-03-04, 43-03-05 | 43-03-04 |
| LT-6 | 43-03 | 43-03-05, 43-03-06 | 43-03-05 |
| LT-7 | 43-03 | 43-03-06, 43-03-07 | 43-03-06 |
| LT-10 | 43-03 | 43-03-07 | 43-03-07 |
| LT-21 | 43-04 | 43-04-01, 43-04-03, 43-04-04, 43-04-05, 43-04-06 | 43-04-03, 43-04-04 |
| PIC-11 | 43-04 | 43-04-05, 43-04-06 | 43-04-05 |
| MS-10 | 43-04 | 43-04-06, 43-04-07 | 43-04-06 |
| RH-13 | 43-04 | 43-04-07 | 43-04-07 |
| ST-14 | 43-07 | 43-07-01, 43-07-06 | 43-07-06 |
| AX-13 | 44-01 | 44-01-01, 44-01-02 | 44-01-02 |
| PIC-12 | 44-01 | 44-01-03, 44-01-04 | 44-01-04 |
| MS-13 | 44-01 | 44-01-05, 44-01-06 | 44-01-06 |
| MS-11 | 44-01 | 44-01-07, 44-01-08 | 44-01-08 |
| AX-18 | 44-04 | 44-04-01, 44-04-02 | 44-04-02 |
| DG-6 | 44-04 | 44-04-03, 44-04-04 | 44-04-04 |
| DG-4 | 44-04 | 44-04-05, 44-04-06 | 44-04-06 |
| MS-12 | 44-05 | 44-05-01, 44-05-02 | 44-05-02 |
| DG-9 | 44-05 | 44-05-03, 44-05-04 | 44-05-04 |
| AX-5 | 44-02 | 44-02-01, 44-02-02, 44-02-03 | 44-02-02 |
| AX-6 | 44-02 | 44-02-03, 44-02-04 | 44-02-03 |
| AX-8 | 44-02 | 44-02-04, 44-02-05, 44-02-06 | 44-02-05 |
| AX-14 | 44-02 | 44-02-06, 44-02-07, 44-02-08 | 44-02-07 |
| AX-15 | 44-02 | 44-02-08, 44-02-09 | 44-02-09 |
| AX-7 | 44-03 | 44-03-01, 44-03-02, 44-03-03 | 44-03-02 |
| AX-9 | 44-03 | 44-03-03, 44-03-04, 44-03-06 | 44-03-04 |
| AX-10 | 44-03 | 44-03-05 | 44-03-05 |
| AX-11 | 44-03 | 44-03-06, 44-03-07, 44-03-08 | 44-03-07 |
| MS-14 | 44-03 | 44-03-08, 44-03-09 | 44-03-08 |
| DG-13 | 44-03 | 44-03-09, 44-03-10 | 44-03-10 |
| PIC-4 | 45-01 | 45-01-01, 45-01-02, 45-01-03 | 45-01-02 |
| PIC-7 | 45-01 | 45-01-04 | 45-01-04 |
| ST-1 | 45-02 | 45-02-01, 45-02-03 | 45-02-03 |
| ST-22 | 45-05 | 45-05-01, 45-05-02, 45-05-03 | 45-05-02 |
| GW-10 | 45-05 | 45-05-03, 45-05-04 | 45-05-04 |
| ST-7 | 45-03 | 45-03-01, 45-03-02, 45-03-03, 45-03-04 | 45-03-02 |
| ST-15 | 45-03 | 45-03-03, 45-03-04, 45-03-05, 45-03-06 | 45-03-04 |
| ST-10 | 45-03 | 45-03-05, 45-03-06, 45-03-07, 45-03-08 | 45-03-06 |
| ST-17 | 45-03 | 45-03-07, 45-03-08, 45-03-09, 45-03-10 | 45-03-08 |
| ST-16 | 45-03 | 45-03-09, 45-03-10 | 45-03-10 |
| VF-4 | 45-04 | 45-04-01, 45-04-02, 45-04-03, 45-04-04, 45-04-06 | 45-04-02 |
| GW-1 | 45-04 | 45-04-03, 45-04-04, 45-04-05, 45-04-06, 45-04-08 | 45-04-04 |
| GW-6 | 45-04 | 45-04-05, 45-04-06, 45-04-07, 45-04-08 | 45-04-06 |
| ST-21 | 45-04 | 45-04-07, 45-04-08 | 45-04-08 |
| RH-1 | 46-01 | 46-01-01, 46-01-02, 46-01-03, 46-01-05, 46-01-06 | 46-01-02 |
| RH-9 | 46-01 | 46-01-03, 46-01-04, 46-01-05 | 46-01-04 |
| RH-11 | 46-01 | 46-01-05, 46-01-06 | 46-01-06 |
| RH-3 | 46-02 | 46-02-01, 46-02-02 | 46-02-02 |
| RH-5 | 46-02 | 46-02-03, 46-02-04 | 46-02-04 |
| RH-8 | 46-02 | 46-02-05, 46-02-06 | 46-02-06 |
| basic:PT-1 | 47-01 | 47-01-01, 47-01-02 | 47-01-02 |
| MS-7 | 47-01 | 47-01-04 | 47-01-04 |
| basic:PT-4 | 47-03 | 47-03-03, 47-03-04, 47-03-05 | 47-03-04 |
| basic:PT-6 | 47-03 | 47-03-05 | 47-03-05 |
| basic:PT-5 | 47-03 | 47-03-06, 47-03-07 | 47-03-07 |
| MS-2 | 47-02 | 47-02-01, 47-02-02 | 47-02-02 |
| MS-3 | 47-02 | 47-02-03 | 47-02-03 |
| MS-5 | 47-02 | 47-02-04 | 47-02-04 |
| basic:PT-3 | 47-02 | 47-02-05 | 47-02-05 |
| DG-7 | 47-02 | 47-02-06 | 47-02-06 |
| PIC-2 | 47-06 | 47-06-02 | 47-06-02 |
| PIC-9 | 47-06 | 47-06-03 | 47-06-03 |
| PIC-10 | 47-06 | 47-06-04 | 47-06-04 |
| DG-12 | 47-06 | 47-06-05 | 47-06-05 |
| PIC-16 | 47-06 | 47-06-06 | 47-06-06 |
| basic:PT-15 | 47-06 | 47-06-07, 47-06-08 | 47-06-08 |
| basic:PT-10 | 47-04 | 47-04-02, 47-04-03 | 47-04-02, 47-04-03 |
| basic:PT-11 | 47-05 | 47-05-04 | 47-05-04 |
| LT-27 | 48-01 | 48-01-01, 48-01-02 | 48-01-02 |
| plot:PT-5 | 48-01 | 48-01-03 | 48-01-03 |
| basic:PT-16 | 48-01 | 48-01-04, 48-01-05, 48-01-06 | 48-01-06 |
| GW-22 | 48-01 | 48-01-07, 48-01-08 | 48-01-08 |
| DT-29 | 48-03 | 48-03-04 | 48-03-04 |
| syn:SD-15 | 48-02 | 48-02-02 | 48-02-02 |
| RH-15 | 48-02 | 48-02-03, 48-02-04 | 48-02-04 |
| ECO-16 | 48-02 | 48-02-05, 48-02-06 | 48-02-06 |
| DT-28 | 48-02 | 48-02-07 | 48-02-07 |
| plot:PT-7 | 49-01 | 49-01-01, 49-01-02, 49-01-03 | 49-01-03 |
| plot:PT-6 | 49-01 | 49-01-04, 49-01-05 | 49-01-05 |
| basic:PT-12 | 49-02 | 49-02-01, 49-02-03 | 49-02-03 |
| LT-25 | 49-02 | 49-02-04, 49-02-05 | 49-02-05 |
| plot:PT-11 | 49-02 | 49-02-06 | 49-02-06 |

## Gap Resolution Log

| # | Gap type | Description | Resolution | Date |
|---|---|---|---|---|
| 1 | Partial requirement | REQ-B-06: P6-P10 items Bokeh cannot draw are documented under the help's Differences with a measured example, and the note stays | Covered after A-26 (each residual has a measured example command: 43-04, 43-07) | 2026-10-21 |
| 2 | Partial requirement | REQ-B-12: After a filter move dash refits a Stata-grid contour with its own fit and shows the stale cue | Covered after A-26 (37-03: the saved page refits with the JS twin and shows the cue) | 2026-10-21 |
| 3 | Partial requirement | REQ-A-28: Gallery captions use Stata terms and show no internals | Covered after A-24 (Stata terms in captions; ids only in corpus.json) | 2026-10-21 |
| 4 | Partial requirement | REQ-A-33: 2-3 sections per batch | Covered as ruled by A-22 (single-section batches where dependencies or R11/R12 force them) | 2026-10-21 |
| 5 | Partial requirement | REQ-A-41: The corpus includes the audit's probe commands | Covered after A-26 (hand-curated prose probes in audit_probes.txt) | 2026-10-21 |
| 6 | Partial requirement | REQ-A-43: webuse datasets are downloaded once into a git-ignored local cache | Covered after A-26 (fetch skips cached datasets) | 2026-10-21 |
| 7 | Partial requirement | REQ-A-44: An offline run uses the cache and names any missing dataset | Covered after A-26 (missing dataset named once) | 2026-10-21 |
| 8 | Partial requirement | REQ-A-49: Each example's twoway SVG is shown beside its live dash graph | Covered after A-23 (static only for a dataset missing from the cache) | 2026-10-21 |
| 9 | Partial requirement | REQ-A-52: Both README columns are vector | Covered after A-26 (README admits only fully vector pairs) | 2026-10-21 |
| 10 | Partial requirement | REQ-A-55: Verdicts compare colours | Covered after A-25 (colours judged within a recorded tolerance) | 2026-10-21 |
| 11 | Partial requirement | REQ-A-91: P4 audit correction: adopath-defined types are withdrawn | Covered (PRD section 7 and index M1 state the exclusion) | 2026-10-21 |

## Scope-Creep Log

| # | Task(s) | What it adds | Resolution | Date |
|---|---|---|---|---|
| 1 | 37-04-02 and 37-04-03 (also Q3704-7 in 37-04-01 and the second CHANGELOG line in 37-04-04) | Under by(), every fit dash computes in Stata with estopts(), predopts() or estcmd() (lfit, qfit, lfitci, qfitci, fpfit, fpfitci) is fitted once per panel. Today one whole-sample fit is drawn in every panel. The change brings its own user st | Kept (P5-1) | 2026-10-21 |
| 2 | 43-06-05 (the evaluator wiring) and 43-06-06 (help, Differences line, CHANGELOG, flip of test_wp31_truth U42-05) | The whitelisted Mata =exp evaluator for globals is applied to every graph text option, not just text()/ttext(). That covers title, subtitle, note, caption, axis/edge/legend titles, tick labels, by() texts and axes 3-9 (through _dash_axisn_j | Kept (P5-1) | 2026-10-21 |
| 3 | 34-09-04 (with 34-09-06's export counts; documented by 40-02-04's AX-16 'Fixed limits' sentence, D-40-02.f) | A build-time Stata tick oracle (sfi calls during render) with a new hard bound, _DASH_STATA_ORACLE_MAX = 256 calls per build. Past the bound, ticks fall silently to the model, which is a new silent count cap. Also an always-on served pre-pa | Kept: core of D41 item 10 | 2026-10-21 |
| 4 | 35-08-02 and 35-08-04 (D-35-08.b/c), closed in 35-08-05 | A byte copy, <R>esample, is made before _estimates hold so that a qualifier or weight naming e(sample) keeps the estimation sample. This holds on the in-place path, on the temporary-frame path and in every frame of a multi-frame build. It h | Kept (P5-1) | 2026-10-21 |
| 5 | 43-05-07 (D-43-05.h) | r1title() and r2title() are drawn reading upward, through an alpha-0 spacer plus an overlay Label. This extends to by()'s dash_by_r1title and dash_by_r2title cells, which 41-02 hands off. | Kept (P5-1) | 2026-10-21 |
| 6 | 47-06-01 and 47-06-02 (D-47-06.g) | Times 20,000 custom-marker diamonds drawn on canvas against WebGL circles, and adds a Resource-limits help sentence if the draw takes more than 2 s. | Kept (P5-1) | 2026-10-21 |
| 7 | 50-04-04 (D-50-04.c) | Proposes corrected wording for CLAUDE.md rule 10 (the -n 8 --dist loadgroup default and the measured duration) and possibly rule 11, for the maintainer to apply. | Kept (P5-1) | 2026-10-21 |
| 8 | 33-05-02 (D-33-05.b; calibrated in 33-05-04, confirmed at 33-05-05) | marker_shape and frame_aspect geometry checks in the verdict engine, plus a 30-row calibration set of dash commands mutated on purpose, which the maintainer confirms. | Kept (P5-1) | 2026-10-21 |
| 9 | 37-01-01 and 37-01-02 (D-37-01.a, cases g and g2) | Two probe sets beyond research [S] section 3's 400 probes: an empty dataset (_N == 0) and by() on an empty dataset. They can add rule rows such as histogram r(198) on no data and a 'bynodata' case. | Removed (P5-2) | 2026-10-21 |

## Superseded Requirements

- REQ-B-04 (Q22): The zero-observation refusal is r(2000) "no observations" -- Superseded by C1 (and M9). dash refuses with twoway's own rc and words per type: lpoly/lpolyci r(2000) "no observations"; fpfit/fpfitci, mband/mspline and an all-empty by() r(198). See REQ-B-47..51.
- REQ-B-11 (Q26): Run twoway__contour_gen at registration so every contour's first drawing (above 1,000 points) is twoway's grid -- Superseded by C3 (only on a full grid or with interp(none)) and M9 (run at export, not at registration; D-37-03.a).
- REQ-B-21 (Q32): Add Firefox and WebKit runs of the CSP, browser and accessibility tests in the release tier through a dev-only driver -- Superseded by A1 (no Firefox or WebKit runs).
- REQ-C-05 (DISCOVERY Q44): Keep the page-size (bytes) cap like every other cap (Q44 'keep every cap') -- Superseded by P4-3: the $dash_max_bytes and $dash_max_cells caps are removed in batch 33.1.
- REQ-C-07 (DISCOVERY Q45): The observation cap counts only the rows if/in selects -- Superseded by P4-3 (index M10): no cap is left to count against, so the selected-row work stays only as a size measure.
- REQ-C-27 (DISCOVERY Q57): Render the dash graph at a fixed size in twoway's default 5.5 x 4 in shape -- Superseded by RESEARCH C2 (stcolor's default is 7.5 x 4.5): each pair is drawn at the size twoway draws that example.
- REQ-C-29 (DISCOVERY Q58 (and Q16)): One gallery page organised by dash tabs by plot type -- Superseded by P4-1 (one page per plot type plus an index page). PRD §5 was not updated and still describes tabs.
- REQ-A-04 (Q2): Seventeen work packages, one per audit package -- A3 removed WP-39, leaving 16 package WPs (33-38 and 40-49). WP-50 (Q29) is added for suite speed.
- REQ-A-10 (Q3, Q6): Timing: the README gallery is generated in WP-33 and regenerated at the final closeout -- P4-8: WP-33 builds no gallery page and no README block. The only build is at WP-50 WE.7.
- REQ-A-11 (Q4): Draw matamatrix() plots -- A2: matamatrix() does not exist in Stata, and plot:PT-10 is withdrawn. 35-09-03 removes the by-name path and the help mentions (R14).
- REQ-A-16 (Q5, Q4): WP-39 = P4 (P4's remaining items in a WP of their own) -- A3 removed WP-39 and left its number unused. Its items moved to WP-35. A3 sent the sunflower sentence to WP-48, but PD-10 later moved it to 35-09.
- REQ-A-34 (Q11): 1-4 tasks per section -- A-14: the count is per item, so multi-item sections hold more tasks.
- REQ-A-42 (Q13): Every extracted example is run in the corpus -- P4-2 keeps one example per combination of plot types and option names (about 425 of 636). Dropped duplicates are listed in extract_duplicates.tsv.
- REQ-A-47 (Q16 (Q58)): One gallery page holds all examples -- P4-1: one dash page per plot type plus a dash-built index page (A-17 link()). PRD §5 still says 'one page built by dash, with tabs by plot type', which is out of date.
- REQ-A-50 (Q16): Every example appears on the gallery page -- P4-10 shows only examples twoway draws; refused examples stay as data in corpus.json. P4-2 removes duplicates.
- REQ-A-67 (D40): No programming yet: implementation waits for a later planning process -- Superseded by DISCOVERY Q1-Q3: this plan is the later planning process that authorises the work.
- REQ-A-93 (D40 (P4 under P11)): P4's capitalised type names are made compatible with twoway (accepted where twoway accepts them) -- Q7 (M7) refuses all capitals, including those twoway takes on a case-insensitive file system, and documents this under Differences.
- REQ-A-95 (D40 (P5)): P5: document the embedded-cell cap (5M, 20M ceiling) -- P4-3 removed the cap (and the page-bytes cap). The help states that there is no size cap.
- REQ-A-96 (D40 (P5)): P5: document that the cap counts _N whatever if/in selects -- P4-3 left no cap to count against. Q45's fix stays as a size measure: only the selected rows are exported and nothing is refused.
- REQ-A-103 (D40 (P12)): P12: refuse zero observations with an error, and note in the help where twoway draws instead -- C1, M9 and Q21 copy twoway per case: dash draws the empty graph where twoway draws and refuses with twoway's rc and words (plus a plot-naming line, Q22) where twoway refuses. No difference is left to note.
- REQ-A-110 (D40 (P14)): P14: fix RH-8 (histogram/rbar recast plus horizontal) -- Q25 (M12) keeps dash's clean transpose and documents twoway's picture.
- REQ-A-112 (D40 (P15)): P15: fix the jitter() items -- Q50 keeps jitter's noise, undocumented. basic:PT-7 and its findings are withdrawn.
- REQ-A-115 (D40 (P17)): P17: remove dash's extra refusal lines and Supported list (plot:PT-7) -- Q43 (M12, PD-11) gives every refusal twoway's words as its first line and keeps dash's extra lines and the Supported list.
