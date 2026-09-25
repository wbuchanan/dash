# Review decisions (Phase 4, 2026-09-25)

Three review reports sit beside this file: `consistency.md` (36 findings), `requirements-security.md` (24), `feasibility.md` (51). This file records how each contested point is resolved so five fixer agents apply one rule. Where a report's proposed edit conflicts with a decision here, the decision wins; otherwise apply the report's edit as written.

## D1. Commits versus tasks (fixes consistency #4, requirements F-01, feasibility critical 1)

Tasks are work steps. Commits are **one per gap** (DISCOVERY Q18, PRD §9), or one per shared component for S01-S04. **A red tree is never committed** (CLAUDE.md rule 4): the failing regression tests are written first (rule 7), run against the unmodified tree, and their failure is recorded in the fix commit's message, but they are committed together with the fix that turns them green. Sections with several gaps (S07, S08, S09, S13, S14, S17) therefore have as many fix commits as gaps; S09 has two (F1, K2), S10 one (E14), S01 one, S02 one, S03 one, S04 one.

Edit everywhere: `BRIEF.md` ("each task = one commit" → this rule); every section's Overview "Test order" paragraph, every task whose `<verify>`/`<done>` says the failing tests are committed alone, and every "Section completion criteria" line about commits.

## D2. CHANGELOG convention (fixes consistency #1, requirements F-04, feasibility critical 6)

S01 task 01-03 places one marker `<!-- WP-28 <ID> -->` per gap **in the list where that gap's entry belongs**, not all under one heading: `### Results that change` for B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, E3, E14 (bar move), G6, G16, X1, X2; `### Changed behaviour (may need your do-files changed)` for G1 (r(110)) and G2 (r(109)); `### Requirements` for K2; `### Fixed in WP-28` for F1, G3, G5 and E14's other four items (E14 has two markers: 23 markers in all). Each gap's closing task **replaces its marker(s)** with the entry text (command, old value, new value for a changed result). S19 19-01 verifies `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0.

## D3. BUGS.md Resolution field (fixes consistency #2, requirements F-03)

The field name stays exactly `- Resolution:` (the parser `_FIELD` in `test/test_tracking_documents.py:98-101` must keep matching; fixer A verifies this against the regex and adjusts if the regex tolerates a parenthetical). The WP and gap id go in the text: `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.` A residual adds `Residual, deferred (WP-28): <what and why>.` at the end. Entries are **appended at the end of BUGS.md** (the file has no headings; S05's mid-file insertion is wrong).

## D4. Batches and dependencies (fixes consistency #5-#9, feasibility critical 2-3)

```
Batch 1: 01 02 03 06 07 08 09 10
Batch 2: 04 (03)   05 (03)   13 (02)   14 (02, 07)   16 (02)   17 (03, 07)
Batch 3: 11 (04, 17)   12 (03, 04, 14, 16, 17)   15 (02, 13)   18 (02, 14)
Batch 4: 19 (all)
```
Reasons: S04 and S05 use `test/js_runner.py` (S03 deletes `_NODE`/`_run_filter_js_block` from their old homes); S14 uses S07's Unicode name check (not `_DASH_VARNAME_RE`); S17 renames nothing but relies on S07's `ROW_ID` fill; S15 adds probes to S13's `scripts/extract_text_truth.do` and regenerates `text_truth.json`; S12 builds on S14's `_dash_build_hover`/`_dash_hover_row` signatures, S16's colorvar key labels and S17's `_dash_filter_widget` values; S11 changes `dash_apply_kpis` after S17's per-group call (S11 must keep the brush slice marker `dash_apply_kpis(new_data,` at dash_render.py:14650/23485 working, or update the slice in the same task); S18 consumes S14's tokenizer. Update every section header, `index.md` (manifest, batches, graph, gap coverage) and `PLAN.md` (index, graph, batch groups, execution order, risk distribution).

## D5. Merge rules within a batch (fixes consistency shared-file table)

Add to `index.md` "How to execute" and `BRIEF.md`:
- **R1 cscripts.** Each section registers its cscript(s) in `test/run_all_cscripts.do` as the LAST block and bumps `test/test_cscript_hygiene.py`'s count pins by its own delta; the merger renumbers blocks and sets the pins to the final count after the batch. S13 and S15 must register theirs (they did not).
- **R2 copy lists and maps.** Each section appends its own names to the served copy lists (dash_render.py 24326-24428, 24466-24687), `test/function_test_map.py` and `test/program_coverage_map.py`; the merger resolves the append conflicts textually.
- **R3 dash.sthlp, CHANGELOG.md, BUGS.md.** Each section edits only the paragraphs GAPS2 cites for its gaps, replaces only its own CHANGELOG markers, and appends its own BUGS.md entries; S12 edits dash.sthlp 1109-1128 after S17 (batch order enforces it).
- **R4 dash.ado graph-key lists.** Only S16 adds graph keys (z options) in its batch; S14 adds none (its numlist expansion uses `_dash_option_rules`).
- **R5 fixtures.** A regenerated fixture is never patched by hand; the section that last touches an extract script regenerates the JSON once (S15 for `text_truth.json`, S18 for `axis_truth.json`, S05 for `stat_truth.json`'s histogram records, S17 for its filter records).
- **R6 parity corpus.** Sections append `CORPUS` cases; only S10 edits `ALLOWED`; only S18 edits `MUST_WARN`.

## D6. Stata concurrency (feasibility "no mechanism")

`index.md` "How to execute" gains step 0: the orchestrator creates `scripts/stata_slot.sh` before batch 1 — a wrapper that acquires one of three `flock` slots (`/tmp/dash-stata-slot-{1,2,3}.lock`, non-blocking retry loop) and then runs `cd "$1" && STATATMP="$1/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do "$2"`. Every section's Stata invocation is written as `scripts/stata_slot.sh <scratch-dir> <file>.do`. S02 task 02-07's `make cert` moves to S19 (a full cert run is never launched inside a section).

> Orchestrator note (2026-09-25, fixer pass): the wrapper is implemented with three atomic `mkdir` slot directories as written in `sections/index.md` step 0, which supersedes the `flock` wording above; sections only call `scripts/stata_slot.sh`.

## D7. XML task schema (feasibility schema violations)

- Any `<action>`, `<verify>` or `<done>` containing `&`, `<` or `>` (shell `&&`, `2>&1`, `<scratch>` placeholders) is wrapped in `<![CDATA[ … ]]>`; text stays readable, never entity-escaped.
- `<name>` is 3-8 words and starts with a verb.
- `<files>` lists paths only, comma-separated, at most 3; the "(new)" suffix moves into the action ("create …"); the seven tasks with a hidden fourth file (02-04, 07-06, 12-04, 12-05, 14-05, 17-04, 17-07) are split as feasibility.md proposes. 19-05's six version files stay (justified).
- `<done>` is one past-tense sentence.
- The 20 oversized tasks named in feasibility.md are split using its XML; ids are renumbered sequentially within the section afterwards, and every cross-reference to a renumbered id (in the same file, in `index.md`, in `PLAN.md`) is updated.

## D8. Checkpoints

Remove 14-12 (S19 runs the suites; the labels are pinned by tests). Keep 18-12. Add a `type="checkpoint"` task at the end of S10 (the one deliberate picture change: the bs filter bar) and one in S19 immediately before the task that marks the residuals deferred in GAPS2.md (approve the deferred list).

## D9. Risk ratings

S09 → red (child-process plumbing, three refusal sites, twelve tasks, inverted tests). S14 → red (tokenizer plus ado numlist expansion plus hover column across both twins). Update the header line, `index.md` and `PLAN.md` (risk distribution becomes 4 green, 9 yellow, 6 red).

## D10. Specific corrections

- S05 imports `run_filter_js_block` from `test/js_runner.py` (S03), not `_NODE`/`_run_filter_js_block` from `test_statistical_helpers.py`.
- S14 uses S07's Unicode-aware check by S07's final name (read S07 §Technical requirements), never `_DASH_VARNAME_RE`; S14's boundary claim of "no overlap" with S12/S17 is replaced by the D4 ordering.
- S14's probe table gains the E3 `%tm` axis-label probe (`twoway line … , xlabel(, format(%tm))` on a %tm variable, recording the tick label texts) that S12 consumes; S12's hand-off note points at that probe id.
- S13 reads `size` from `svg_texts`, not `font_size`; S13's B6 BUGS.md title contains no `"`: use `An empty xtitle() or ytitle() does not remove the axis title`.
- S13 and S15 register `test_textbox_grammar.cscript` and `test_legend_order.cscript` (R1).
- S08 runs the full pytest suite once, at the end (CLAUDE.md rule 11), not four times.
- 04-04's verify arithmetic is recomputed (feasibility critical 4: 14977.0, not 15341.0) — fixer B re-derives and states the derivation in the verify.
- 16-03/16-04 drop the phantom "rebuild the Mata library" step (no `.mlib` exists; dash_parse.mata is `run` from dash.ado).
- S18 rewires `scripts/extract_axis_truth.do`'s private SVG code onto `scripts/svg_truth.py` when it regenerates `axis_truth.json` (S02 deferred this to S18).
- Security minors: S04 adds a unit test for `dash_html_escape` (and its Python twin); S06 bounds the scheme file name in warnings (basename, ≤ 80 characters); S09 bounds forwarded child stdout (last 20 lines, ≤ 4 KB) and stderr likewise; S14 states that a numeric run holding `` ` `` or `$` never reaches `numlist` (it is treated as text and named).
- Edge-case minors from requirements-security.md §4 become TDD stubs in the named sections (NaN precondition in `_histogram_counts`; period sliders on empty and single-value columns; `valuelabel` under by() panels; `label(0)`; `%tC` tooltip keeps its time; compound-quoted `ytitle2`; width-1 formats; `numlist` 1,600-element cap vs the 2,000 bound).
- D1 residual (CMYK/hsv/`*#` colour forms) is added to PRD §7 and S19's deferred list (requirements F-11).

## What fixers must NOT do

Do not change any decision in `DISCOVERY.md`; do not add or remove gaps; do not alter the fixed public names of S02, S03, S04, S07, S14; do not edit files outside your assignment.

## D11. Certification-suite budget (refinement Q28: cap the growth at about five minutes)

New cert work is consolidated so the whole certification suite grows by at most about five minutes of wall time. Rule: **only comparisons with twoway's drawing or Stata's own values get new cscript code, and all of it goes into ONE new script, `test/test_gaps2_truth.cscript`** (registered once, by S02, which also puts its helper smoke checks there; every later section appends a block to it — merge rule R1 applies to the block order, not to new files). Refusal, message, return-code and setup checks join the existing script for their area: F1 → `test_serve_launch.cscript` (stub-renderer style); K2 → `test_setup_honesty.cscript` and `test_setup_python_gate.cscript`; G1 and G5 → `test_qualifier_in_stata.cscript` (QS-06) and `test_statistical_options.cscript`; G2 → `test_adversarial.cscript`; G3 → `test_adversarial.cscript` with the lowered-limit knob (no 6M-row build); C2's page-sum check and the X1/E2 row counts → `test_e2e_filters.cscript` unless they compare with twoway, in which case they are blocks in `test_gaps2_truth.cscript`; E14 has no cscript (pytest and Chrome). Sections that had planned their own new cscript (`test_cert_svg.cscript`, `test_textbox_grammar.cscript`, `test_legend_order.cscript`, the S05/S06/S07/S08/S09/S16/S17 scripts) rewrite those tasks accordingly. S19 measures the cert suite's wall time before and after the package (the runner log's start and end lines) and records it in WP-28's "Done, measured" block; if the growth exceeds five minutes, the slowest blocks are folded before the gate.

## D12. Fixture provenance stamp (refinement Q31)

Every new or regenerated Stata-measured fixture carries in `_meta`: `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (the `git rev-parse HEAD` at extraction, written by the extract script's python block from a value the do-file passes in), and `extracted` (date). A test reads the keys exist; nothing compares them. Applies to S02, S04, S05, S13, S14, S15, S16, S17, S18.

## D13. Third-party scheme files are out of scope (refinement Q30)

The maintainer excluded every third-party scheme file. S06 drops the PLUS sweep (the env-gated task), the copied `scheme-d3colors.scheme` fixture and the "127 of 129" claims. D1's tests pin quoted values with a scheme file the test writes itself (a copy of a shipped scheme with `color background "255 0 0"`, `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, an unclosed quote, a `label "…"` line and a tab-separated line). GAPS2 D1 plan step 4's third-party parts are marked excluded by decision in S19's GAPS2 Tracked line and in PRD §7.

## D14. Invariants for future agents (refinement Q29)

S19 appends an "Invariants introduced by WP-28" section to `AGENTS.md` (not CLAUDE.md): the `__dash` column prefix and its guard test; the served copy lists and `TestTheServedAppCarriesEveryName`; the Python/JavaScript twins (`_dash_fmt`/`dash_fmt`, the filter mask, the histogram recount) and their node parity tests; `scripts/stata_slot.sh`; the CHANGELOG marker convention; the BUGS.md Resolution form; the fixture `_meta` stamp. One paragraph each, naming the guarding test.
