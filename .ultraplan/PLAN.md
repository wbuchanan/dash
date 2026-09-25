# UltraPlan: WP-28 — close 22 GAPS2 gaps · Master Technical Plan

> Generated: 2026-09-25
> Phase: 6/6 - OUTPUT (complete: reviewed in Phase 4, fixed, validated in Phase 5; see `VALIDATE.md` and `SUMMARY.md`)
> Sections: 19 | Tasks: 205 | Parallel batches: 4
> For plain-English requirements see `PRD.md`; for decisions `DISCOVERY.md`; for measurements `RESEARCH.md` and `research/`.

---

## Project overview

### Summary

`dash` accepts `twoway` syntax and renders an interactive HTML dashboard through two renderers in `dash_render.py`: `DashRenderer` writes a saved offline page whose interactivity is embedded JavaScript, and `ServerAppBuilder` emits a `bokeh serve` app whose interactivity is Python. This package closes 22 gaps from the 25 September 2026 audit (`GAPS2.md`) at commit `91d97be`: 15 where the page silently draws different numbers, text, colours or rows from twoway, and 7 where a documented capability fails visibly. Every fix lands as a failing regression test, then the fix, then a closed BUGS.md entry, in one commit per gap on `s3-bugs`; truth comes from Stata itself through measured fixtures; the exit is the WP-27 release gate with no open S1 or S2 defect.

### Goals

1. Every S1 gap in scope produces the numbers, text and rows twoway produces, proven by a Stata-measured fixture or SVG comparison and asserted in both renderers.
2. Every refusal is loud and uses Stata's code (r(109), r(110), r(198), r(134)); every honoured option is silent.
3. The package leaves the guards green throughout: the full pytest suite under both interpreters, the certification suite, the tracking tests, and finally the release gate from an installed package.

### Constraints

- Scope is fixed at 22 gaps (PRD §4); C4/E4 and the residuals in PRD §7 are out.
- Branch `s3-bugs`; no commit to `main`; the merge command is reported.
- Stata only through `scripts/stata_slot.sh <scratch-dir> <file>.do` (`sections/index.md` step 0: three `mkdir` slots, `STATATMP=<scratch-dir>/tmp/`, the console binary of CLAUDE.md rule 10), which keeps concurrent Stata sessions at three; a single cscript goes through the two-line driver of step 0; `make cert` and `make gate` run only in S19.
- pytest: changed files while iterating; the full suite once before a commit; never a second full run while one executes.
- Declared floor: Python 3.13, Bokeh 3.8, pandas 2.3, numpy 2.3 (the `stata` baseline in `test/conftest.py`).
- The served app is assembled by copying named functions and constants (`dash_render.py` 24326-24428, 24466-24687): every new helper joins those lists, after the anchor entry `sections/index.md` R2's table names for its section, and `test/function_test_map.py`.
- One new certification script only, `test/test_gaps2_truth.cscript` (S02; runner block `// 67.`; pins 66/48); every later Stata-truth comparison is a `GAPS2_ONLY`-gated block appended to it, and refusal, message and setup checks join the existing script for their area (review D11). The suite's wall time may grow by about five minutes at most, measured against the pre-batch-1 run of step 0b (Q28).
- Commits: one per gap `(GAPS2 <ID>)`, one per shared component S01-S04 and one per S19 step `(WP-28 Snn)`; a section commits on its worktree branch `wp28-s<NN>` and the merger lands the commit on `s3-bugs`; no test-only commit; the failing tests' output at 91d97be opens each fix commit's body (Q24).

---

## Architecture overview

```
 Stata ────────────────────────────────────────────────────────────────────────
   dash.ado / dash_parse.mata        S07 __dash prefix, Unicode names     S08 numeric varlists, cell cap
   ├─ parse twoway syntax            S13 axis(#) routing (Mata, pre-merge)  S14 numlist expansion
   ├─ validate options               S16 colorlevels/colorvarminmax/z*     S04 %x/%H refusal
   ├─ export data.json  ──────────►  S04 storageTypes, formats             S09 serve: rc, /health, floor
   └─ spec.json
 Python (dash_render.py) ──────────────────────────────────────────────────────
   loaders (both renderers)          S04 storage types, %g formats kept
   OptionTranslator / textbox        S13 abbreviation table, "" titles, title2 textboxes
   axis spec                         S14 tokenizer, valuelabel → major_label_overrides
   GlyphMapper                       S05 histogram floor/clamp · S16 colorvar levels · S14 __dash_hover_*
   SchemeParser                      S06 third-token grammar, quoted RGB/%opacity
   legend                            S15 keys by Stata plot number, label-only rows
   finish (after layers)             S18 hull extents (data ∪ ticks ∪ range), Range1d
   hover / widgets / KPI / CSV       S11 cards · S12 widgets, tooltips, date axes, mlabels, CSV  ← S04 _dash_fmt
   filter callbacks                  S17 per-target masks, numeric Select values
   served template                   S10 viewport, dimming, range views, bs CSS
 JavaScript twins (strings in dash_render.py) ─────────────────────────────────
   _DASH_FMT_JS (S04) · _DASH_FILTER_MASK_JS / _FILTER_JS (S17, S05 recount) · ROW_ID (S07)
 Tests ─────────────────────────────────────────────────────────────────────────
   S02 scripts/svg_truth.py + test/cert_svg.do + test/test_gaps2_truth.cscript (the one new cscript)   S03 test/js_runner.py (JsSession, mask_parity)
   scripts/extract_*_truth.do → test/fixtures/*_truth.json (git add -f)
 Tracking ──────────────────────────────────────────────────────────────────────
   S01 ROADMAP WP-28, test_tracking_documents.py (GAPS2), test_packaging.py   S19 CHANGELOG, GAPS2 Tracked, gate
```

### Architecture notes

- **One rule, two twins.** Where the saved page recomputes in the browser (formats, filter masks, histogram recount), the Python original and the JS string are pinned against each other under node and against the Stata fixture.
- **Truth is measured once.** A Stata extract script writes a fixture; pytest and cscripts consume it; live cscripts compare a `graph export .svg` through `test/cert_svg.do` where GAPS2 asks for it.
- **Order of operations inside a figure differs between renderers** (research A §0.2). Fixes that depend on ordering (B7 styling of the second axis, B2's hull) are placed inside shared functions that run at the same point in both, or they add the missing step to the template.

---

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Command | Stata ado + Mata (`dash.ado`, `dash_parse.mata`, `dash_setup.ado`) | parse, validate, export, launch |
| Renderer | Python 3.13+ (`dash_render.py`), numpy 2.3+, pandas 2.3+ | build figures, pages, served app |
| Plotting | Bokeh 3.8+ (BokehJS in the page) | figures, widgets, legend, colour bar |
| Page logic | embedded JavaScript strings | filters, KPI cards, CSV, recount, formats |
| Tests | pytest (`-n auto`), node v24 for JS, headless Chrome (optional), Stata cscripts | unit, parity, end-to-end, certification |
| Tracking | BUGS.md, ROADMAP.md, CHANGELOG.md, GAPS2.md, dash.sthlp | guards read by `test_tracking_documents.py` |

### Key libraries

| Library | Version (floor / dev) | Notes |
|---|---|---|
| bokeh | 3.8.0 / 3.9.0 | `Select` numeric values ≥ 3.4; label-only `LegendItem`; pandas optional from 3.9 |
| pandas | 2.3.3 / 3.0.1 | declared by dash itself |
| numpy | 2.3.5 / 2.4.3 | |
| node | 24.13.1 | JS twin tests; skipped if absent (red under `DASH_STRICT`) |

---

## Section index

| # | Section | Gaps | Risk | Batch | Depends on | Blocks |
|---|---|---|---|---|---|---|
| 01 | Tracking foundation | all | green | 1 | none | 19 |
| 02 | Stata truth helper | truth for B1, B2, B3, B5, B6, B7, D1, G16, X2 | yellow | 1 | none | 13, 14, 15, 16, 18 |
| 03 | Stateful node runner | tests for C2, E2, E3, X1 | green | 1 | none | 04, 05, 12, 17 |
| 04 | Display-format writer core | E1, E3, G6 (foundation) | red | 2 | 03 | 11, 12 |
| 05 | Histogram edge rule | C2 | yellow | 2 | 03 | 19 |
| 06 | Scheme quoted values | D1 | green | 1 | none | 19 |
| 07 | Reserved and Unicode names | G1, G5 | yellow | 1 | none | 14, 17, 19 |
| 08 | Numeric varlists and the data limit | G2, G3 | yellow | 1 | none | 19 |
| 09 | Serve launcher and version floor | F1, K2 | red | 1 | none | 19 |
| 10 | Saved/served presentation parity | E14 | yellow | 1 | none | 19 |
| 11 | KPI cards | E1 (+E3, G6 on cards) | yellow | 3 | 04, 17 | 19 |
| 12 | Widgets, tooltips, date axes, marker labels, CSV | E3, G6 | red | 3 | 03, 04, 14, 16, 17 | 19 |
| 13 | Textbox grammar | B3, B6, B7 | yellow | 2 | 02 | 15, 19 |
| 14 | Axis labels and value labels | B1, G16 | red | 2 | 02, 07 | 12, 18 |
| 15 | Legend order and labels | B5 | yellow | 3 | 02, 13 | 19 |
| 16 | colorvar explicit forms | X2 | yellow | 2 | 02 | 12, 19 |
| 17 | Filters: exclude() and dropdowns | E2, X1 | red | 2 | 03, 07 | 11, 12, 19 |
| 18 | Axis scale extents | B2 | red | 3 | 02, 14 | 19 |
| 19 | Closeout | all | green | 4 | all | none |

Section files: `sections/section-NN-<slug>.md`; the manifest with task counts is `sections/index.md`.

---

## Dependency graph

```
Batch 1: 01  02  03  06  07  08  09  10
             │   │       │
Batch 2:     │   ├─► 04  │          (03)
             │   ├─► 05  │          (03)
             ├───┼─► 13  │          (02)
             ├───┼─► 14 ◄┤          (02, 07)
             ├───┼─► 16  │          (02)
             │   └─► 17 ◄┘          (03, 07)
Batch 3:     11 (04, 17)   12 (03, 04, 14, 16, 17)   15 (02, 13)   18 (02, 14)
Batch 4: 19 ◄── all
```

### Dependency notes (revised in review, D4)

- S02 is a hard dependency for every section whose truth is twoway's drawing (13, 14, 16, and through 13, 15; 18); their fixtures use `scripts/svg_truth.py`.
- S03 is a hard dependency for S04 and S05 (their node tests import `run_js` / `run_filter_js_block` from `test/js_runner.py`, whose predecessors S03 deletes), for S17 (chained moves) and S12 (period-slider masks under node).
- S07 is a hard dependency for S14 (its Unicode-aware name check) and S17 (the `ROW_ID` fill).
- S04 is a hard dependency for S11 and S12: they call `_dash_fmt` and prepend `_DASH_FMT_JS`.
- S17 precedes S11 (per-group `dash_apply_kpis` call) and S12 (dropdown values before labels); S16 precedes S12 (colour-key label site); S14 precedes S12 (hover signatures) and S18 (the tokenizer); S13 precedes S15 (`extract_text_truth.do`).
- Batch 1 sections touch disjoint regions of `dash_render.py` and `dash.ado`; shared files follow the merge rules R1-R6 in `sections/index.md`; Stata runs go through `scripts/stata_slot.sh` (three slots).

---

## Parallel batch groups

### Batch 1: foundation and independent leaves
Sections 01, 02, 03, 06, 07, 08, 09, 10. Execute together.

### Batch 2: consumers of S02, S03 and S07
Sections 04, 05, 13, 14, 16, 17. Execute together after batch 1.

### Batch 3: consumers of batch 2
Sections 11, 12, 15, 18. Execute together after batch 2.

### Batch 4: closeout
Section 19, after every other section has merged and the full suites are green.

---

## Execution order

0. In the main checkout on `s3-bugs`, before any worktree exists: (0a) create `scripts/stata_slot.sh` (the `mkdir`-slot text in `sections/index.md` step 0, which supersedes review D6's `flock` wording) and commit it alone, mode 755, as `… (WP-28 S00)`; (0b) record the certification suite's "before" wall time with `{ date +%s; make cert; date +%s; } > <scratch>/cert-baseline.log 2>&1` (review D11; S19 compares against it); (0c) give each section agent its section file, `sections/BRIEF.md`, `DISCOVERY.md`, `RESEARCH.md`, `review/DECISIONS.md`, `sections/index.md` and the research report it cites.
1. Create one worktree per Batch 1 section from `s3-bugs` (`git worktree add <path>/wp28-s<NN> -b wp28-s<NN> s3-bugs`); each agent works in its worktree only and its closing task commits there, on `wp28-s<NN>`, after one green full run in the worktree.
2. Land the batch in its merge order (review D4, contract C3): batch 1 `S01, S03, S02, S06, S07, S08, S09, S10`; batch 2 `S04, S05, S13, S17, S16, S14`; batch 3 `S18, S15, S11, S12`. For each commit of each section, oldest first: `git -C <worktree> format-patch -1 --stdout <sha> | patch -p1` (never `cd` into the worktree; rejected hunks applied by hand under `sections/index.md` R1-R6, copy-list entries after the anchors in R2's table), `git add` the patch's files, `git commit -F <the section's recorded message>` (subject `(GAPS2 <ID>)` or `(WP-28 Snn)`; the failing-test output at 91d97be in the body; no AI references). After the last section of the batch, run the full suite once (`python3 -m pytest test/ -q`), the registry tests of R2 and the batch's certification blocks and scripts through the step-0 driver; a red result is fixed in the owning section (a fresh worktree from `s3-bugs`, a commit with the gap's id, landed the same way) and the suite rerun once. Remove the worktrees.
3. Repeat for Batch 2 and Batch 3, creating each batch's worktrees from `s3-bugs` after the previous batch has landed; then S19 in the main checkout, committing per step.
4. S19 reconciles the CHANGELOG (zero `<!-- WP-28 ` markers; every line `(WP-28, <ID>)` in its place), has the residual list approved, writes GAPS2.md's Tracked lines, marks WP-28 DONE, appends the WP-28 invariants to `AGENTS.md` (review D14), regenerates the demo pages without committing them (none is tracked; Q25 corrected), dates the release, runs `make test`, `make test-dev`, `make cert` (timed against `<scratch>/cert-baseline.log`; a growth over about five minutes is folded before the gate) and `make gate` once each, verifies BUGS.md and ROADMAP.md, and reports the merge command without running it.

---

## Risk summary

### Risk distribution

- **Green:** 4 sections (01, 03, 06, 19)
- **Yellow:** 9 sections (02, 05, 07, 08, 10, 11, 13, 15, 16)
- **Red:** 6 sections (04, 09, 12, 14, 17, 18)

### High-risk sections

| Section | Risk summary | Mitigation |
|---|---|---|
| 04 Display-format writer core | `%w.0g` has no documented algorithm; two twins to keep identical; loaders start carrying %g formats, which flips pinned tests | ~200-value Stata fixture pins both twins; every pinned test is flipped in the same commit with its reason |
| 12 Widgets, tooltips, axes, labels, CSV | nine sites in both renderers; period sliders change the mask's column conversion; tooltip field pattern is a security guard | one site per task; `mask_parity` under node; the `_PLACEHOLDER` pattern widened deliberately with the format carried in `args` |
| 17 Filters | the callback architecture changes in both modes; snapshot coercion touches marker labels and `dcount` | one documented mask rule pinned by `mask_parity`; chained-move tests through `JsSession`; Stata-counted truth |
| 18 Axis scale extents | the hull interacts with count ticks, log/date axes, by() common scale and the saved-only renderers block | the hull lives in the one post-layer function both modes run; 20 SVG-fitted cases; a parity profile field for range renderers |
| 09 Serve launcher and version floor | child-process plumbing with a live /health poll; three refusal sites plus the embedded port; tests that require clamping are inverted | reader threads, `_FakeProc` gains `returncode`; a held-socket pytest and cscript; every clamp site parametrised |
| 14 Axis labels and value labels | a new tokenizer, numlist expansion in ado with a Python bound, and a hover column that must survive filter moves in both twins | ado never refuses; Python keeps `_MAX_AXIS_TICKS`; SVG fixture per numlist form; the hover column is built like the marker-label column |

### Medium-risk sections

| Section | Risk summary | Mitigation |
|---|---|---|
| 02 | consolidating seven private SVG helpers | reuse without changing their tests' results; smoke fixture |
| 05 | the recount's JS and the served mapper path | property test summing to N in Python, served path and node |
| 07 | renaming internal columns across both twins | a guard test that no internal literal lacks the prefix |
| 08 | per-graph accounting in Mata; a 6M-row cscript | a lowered-limit knob in tests; served keeps the full cap |
| 10 | per-child CSS on a Bokeh GridBox | stylesheet on children or a resize handler; residual if neither |
| 11 | date branch first in the KPI formatter; JS card escaping | Stata's own `kpi_display` as truth; escape in the rebuild |
| 13 | `axis(2)` routing before the Mata repeat merge | Python-side rewrite as fallback |
| 15 | key numbering with CI layers | `_dash_plot_style_indices` as the numbering source |
| 16 | declaring z options touches seven graph-key lists | one task per list group; parity corpus cases |

---

## File map

| Directory / file | Sections |
|---|---|
| `dash.ado` | 04 (fmt refusal, storage types), 07, 08, 09, 13 (axis routing), 14 (numlist), 16 (options) |
| `dash_parse.mata` | 07 (name check), 08 (per-graph accounting), 13 (repeat merge), 16 (categories, tables) |
| `dash_setup.ado`, `dash_setup.sthlp`, `dash.pkg` | 09 |
| `dash_render.py` | 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18 |
| `dash.sthlp`, `CHANGELOG.md`, `BUGS.md` | every gap section; 19 |
| `ROADMAP.md`, `GAPS2.md` | 01, 19 |
| `AGENTS.md` | 19 (the "Invariants introduced by WP-28" section, review D14) |
| `scripts/svg_truth.py`, `test/cert_svg.do` | 02 (18 rewires `extract_axis_truth.do` onto it) |
| `scripts/stata_slot.sh` | orchestrator, before batch 1 (index.md step 0a, committed as WP-28 S00) |
| `scripts/extract_format_truth.do`, `extract_text_truth.do`, `extract_colorvar_truth.do`, `extract_axis_truth.do` (extended), `extract_stat_truth.do` (extended), `extract_filter_truth.do`, `extract_svg_truth_smoke.do`; `scripts/gen_string_varlists_cscript.py` | 04, 13/15, 16, 14/18, 05, 17, 02; 08 |
| `test/test_gaps2_truth.cscript` (the one new certification script) | 02 creates and registers it (runner block `// 67.`); 05, 11, 13, 14, 15, 16, 17, 18 append `GAPS2_ONLY`-gated blocks in section order |
| `scripts/regen_dashboards.py`, `regen_comprehensive.py`, `regen_bootstrap_examples.py` (run, not edited; their `.html` output is untracked) | 19 |
| `test/fixtures/*_truth.json` | as above (`git add -f`) |
| `test/js_runner.py` | 03 |
| `test/test_tracking_documents.py`, `test/test_packaging.py` | 01 |
| `test/function_test_map.py`, `test/program_coverage_map.py` | every section adding a function or program |
| `test/test_*.py`; the existing `test/test_*.cscript` files (blocks or cases added per contract C7); `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` (02 only) | every section; 02 |

---

## Review notes

Phase 4 (2026-09-25). Three parallel reviewers read every plan file against the repository at `91d97be`:

| Report | Scope | Findings |
|---|---|---|
| `review/consistency.md` | naming, contracts, dependencies, shared files | 36 (7 critical, 13 major, 16 minor) |
| `review/feasibility.md` | task schema, order, scope, verification, risk, UX, simplification, checkpoints | 51 (6 critical, 12 major, 32 minor, 1 compliant) |
| `review/requirements-security.md` | GAPS2 plan-step coverage, decision compliance, security, edge cases | 24 (1 critical, 6 major, 17 minor) |

**111 findings** in all. `review/DECISIONS.md` D1-D10 resolved the contested points; refinement questions Q24-Q31 (DISCOVERY.md) added D11-D14. The fixer pass then rewrote every section file to them.

### What was fixed

- **Commits versus tasks (D1).** Every test-only commit removed; one commit per gap, one per shared component; failing output recorded at 91d97be and quoted as the CHANGELOG old value (Q24).
- **CHANGELOG markers (D2)** placed per list; every closing task replaces its own marker(s) with lines ending `(WP-28, <ID>)`.
- **BUGS.md Resolution form (D3)** made one form everywhere: `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). … Pinned by …`, appended at the end of the file.
- **Batches and dependencies (D4)** recut: S04/S05 after S03; S14 after S07; S15 after S13; S11/S12 into batch 3; merge orders fixed inside each batch; the shared-function contracts (hover, axis spec, `_apply_colorvar`, the KPI marker, the node-runner names, the copy-list anchors) written identically into every section that touches them.
- **Merge rules R1-R6 (D5)**, **the Stata slot wrapper (D6)**, **the XML schema (D7)**: CDATA everywhere it is needed (and the five files the mechanical pass had corrupted repaired), 3-8-word names, ≤ 3 files, the twenty oversized tasks split, ids renumbered.
- **Checkpoints (D8)**: S14's checkpoint removed; a Chrome approval added to S10; a residual-approval checkpoint added to S19; S18's kept last.
- **Risk (D9)**: S09 and S14 red; distribution 4 green, 9 yellow, 6 red.
- **Specific corrections (D10)** and the security and edge-case minors, each as a TDD stub in its section.
- **One certification script (D11)**, **fixture provenance stamps (D12)**, **third-party schemes out (D13)**, **AGENTS.md invariants (D14)**.

### Corrections found by the cross-check before the fixer pass (2026-09-25, resumed session)

- **D2 had been misread** in the resumed session's first brief: the markers belong in the release's existing top-level lists (`### Results that change` under a new bold group `**WP-28 (GAPS2 audit, 25sep2026)**`, `### Changed behaviour…`, `### Requirements`) plus a new `### Fixed in WP-28` heading for F1, G3, G5 and E14's served items; every WP-28 line ends `(WP-28, <ID>)`.
- **A single certification script cannot be handed to the slot wrapper**: the runner changes into `test/` first, so each section runs its script through a two-line driver do-file in its scratch directory.
- **The `%tm` probe's ticks** are 492(3)501 (sp500 is 2001), texts `2001m1 2001m4 2001m7 2001m10`.
- **A third hygiene pin exists** (`with_probes == 13`, :315); S02 states whether the new script changes it.
- **Commits happen on the worktree branch** (`s3-bugs` cannot be checked out in a second worktree); the merger lands each commit on `s3-bugs` in the batch's merge order.
- **`_MUST_WARN` entries** are edited by the section whose gap silences them (S12, S14, S18), every key kept; index.md R6 rewritten.
- **Step 0 gains 0a and 0b**: the slot wrapper is committed before any worktree is created, and a `make cert` baseline is timed for D11's comparison.

### Orchestrator rulings made in the fixer pass (not covered by a DECISIONS item)

- D6's `flock` wording is superseded by `sections/index.md` step 0's `mkdir` slot wrapper (noted under D6).
- Under D11, G2's generated cases (DISCOVERY Q16) live as a generated block inside `test/test_adversarial.cscript`; `scripts/gen_string_varlists_cscript.py` rewrites only that block.
- S06's optional d3colors SVG comparison task is deleted rather than moved: D13 excludes third-party scheme files.
- The hygiene pins after WP-28 are 66 (`_CSCRIPTS`) and 48 (`names`), set by S02 alone.
- Refinement Q25 is applied as "regenerate the demo pages, do not commit them": no `.html` is tracked (`.gitignore`, `git ls-files`), and a root `.html` would fail `test_packaging.py`'s allowlist.
- Every section keeps its "Review amendments" block, with its closing sentence changed to say the text below conforms.

### Mechanical validation

A read-only validator (task XML, ids, names, files, `<done>`, headings, the amendments block, naming drift, Stata-run rules, the truth-script blocks, checkpoint positions, cross-references, manifest agreement) ran before and after the pass: **207 errors and 43 warnings before; 0 errors and 14 warnings after**, the warnings being line ranges that look like task ids (`mpg 12-41`, `scale.class:19-27`). Tasks went from 160 to **205** (49 names shortened, 18 `(new)` annotations removed, 7 hidden fourth files split out, the 20 oversized tasks split, S14's checkpoint removed, the S10 Chrome checkpoint and the S19 residual checkpoint added, S06's optional d3colors task deleted). The full table is `VALIDATE.md` §9.

### Sections modified

All nineteen section files, `sections/BRIEF.md`, `sections/index.md`, this file, `PRD.md` §7, and one note in `review/DECISIONS.md`.
