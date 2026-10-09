# Section 58: Closeout

> Part of: WP-30 · Entries: all 56 (P1.1a-P1.35, opened by S01, closed by S02-S57), plus the extra entries P1.5.7 and P1.25.6 (closed; P2.49 is not filed, ratification row 27); recorded, reconciled, filed and proven here · Risk: green · Batch: 21 (main checkout on `wp30-p1`, alone) · Depends on: 01-57 · Blocks: none · Tasks: 21, five or six commits (S58.1, S58.2, S58.3, S58.4, S58.6 only if the release date must move, S58.7; S58.5 commits nothing)

## Review amendments (derivation and binding refinements)

> Batch **21** · Depends on **01-57** · Blocks **none** · Risk **green** · Commits: one per closeout step, subjects ending `(WP-30 S58.<k>)` (A141); a defect found here is fixed under its owner's entry id `(WP-30 P1.<n>[abc])`, never under S58's.

There is no research note for this section. It is derived from `index.md` (A141-A148, A156, "Deltas from BRIEF.md", E1-E12, IR-2/3/4/8/9/16, "How to execute" step 3, G10, G11), `PLAN.md` §6 BR-30.40, §7 "S58" and §9 E1-E15, `manifest.json` (section 58's scope and notes; the 22 residuals), `decisions.md` (M1-M12), `decision-register.md` (P2.42-P2.57, the scope changes of P2.11-P2.14, P3.2, P3.7, P3.9, P3.11), the "Notes for the closeout" of all 57 section files (Appendix C lists each and where it is consumed), the review notes `review-notes/g01.md`-`g09.md`, `open-questions.md`, and WP-29's closeout (`.ultraplan/wp29/section-15-closeout.md`; commits `03fbda0`, `97b201c`, `114f354`). Every claim marked "measured" was measured at `c96facd` on 06oct2026. The measurements led to these binding refinements of PLAN.md §7 S58:

- **R58-1 (Closed lines and DONE land together).** ROADMAP.md has no WP-30 section until S58.2 writes it, and `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_closed_gaps2_entry_is_listed_by_its_package` (:1112) fails on any `Closed in WP-30` Tracked line whose package is absent, not DONE or not listing the id (`"%s names %s, which ROADMAP.md lacks"`). So every GAPS2 Tracked line, the WP-30 entry headed `— DONE` and its `**GAPS2 closed:**` field are one commit, S58.2 (WP-29's R15-1, `e520a48`).
- **R58-2 (one commit after `commit `).** `_GAPS2_CLOSED` (:689-690) reads `^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b`. The notes' forms `commits <sha1>, <sha2>` (S19, S29, S42, S51, S56), `Closed in WP-30 (P1.4b), BUGS.md …` (S33) and `"<t1>" (commit <s1>) and "<t2>" (commit <s2>)` (S04) match nothing and are normalised to Appendix D.1: the entry that completed the closure first, every other carrying entry after it as `; with BUGS.md "<title>", commit <sha>`.
- **R58-3 (the Resolution token is the heading id).** The reader (:1152-1197) requires `"(%s, %s)" % (wp, gid)`, i.e. `(WP-30, I14)`, in the named entry's Resolution. The notes' sub-id tokens (`(WP-30, GAPS2-I14-a)`, `(WP-30, GAPS2-X5-c)`, `(WP-30, GAPS2-B17-a)`) are never written; each closing entry that carries a FULL id gains exactly ` Closes GAPS2 <ID> (WP-30, <ID>).` at the end of its Resolution (WP-29's D.6).
- **R58-4 (pointer ids have no heading).** A7, B8, B9, B13, B29, C5, C10, D6, G15, I4, I7, J2 and J5 are "same gap as" paragraphs (measured: GAPS2.md:230, 455, 457, 490, 676, 757, 776, 915, 1484, 1658, 1660, 1735, 1739), so `test_every_gaps2_id_a_package_declares_has_a_heading` (:1054) refuses them in the field. The Tracked lines the notes propose for B9 (S08), J5 (S09), I4 (S46) and A7 (S55) are written as commentary in their primaries' lines: B12 (A7, G15), E3 (B8), D2 (B9), D3 (B13, J2, J5), D17 (B29), A6 (C5), A13 (C10), B11 (D6), F3 (I4), H4 (I7).
- **R58-5 (earlier closures keep their prefix).** A6 (`Closed in WP-29`, :228), E3 and K2 (`Closed in WP-28`) are ANNOTATE ids: WP-30's part is inserted before `; was:` and they are never listed in WP-30's field (WP-29's R15-3).
- **R58-6 (group intros have no Tracked line).** The H intro (platforms, GUI, the Stata version; S02, S03), the I summary (:1590; S06, S23) and the C intro (:711; S57) are paragraphs, not headings. Their closures are recorded on the DROPIN rows and in the Done block; GAPS2.md changes nowhere but Tracked lines.
- **R58-7 (earlier text is tagged, not rewritten).** GAPS.md corrections are body paragraphs opening `**Since WP-30 (P1.<n>, commit <sha>).**` (no heading gains `CLOSED by`; WP-29's R15-5). A correction to an earlier ROADMAP package (S03 :4750, S06 :452, S09 :3039/:3063-3066, S11 PHASE-28, S13 :2048-2050, S14 :4554/:4660/:4703, S16 :2051, S25 WP-07, S38 :1527, S40 :1567; numbers at `c96facd`, found by text) is a tag `[WP-30 P1.<n>, commit <sha>: <correction>]` appended to the end of the line or bullet it corrects, the old text kept; no `**Gaps closed:**`, `**GAPS2 closed:**`, heading or Done-block number of an earlier package changes.
- **R58-8 (BUGS.md gains one sentence only).** The only BUGS.md edit is R58-3's sentence. Residual clauses of earlier entries that WP-30 closed (BUGS.md:2742, :2748, :2754 by P1.16; :2771 by P1.23a; :504 acted on by P1.17a) are recorded on the DROPIN rows that filed them (P2.30-P2.41) and in the Done block, never in those entries.
- **R58-9 (no plan file is edited).** `.ultraplan/wp30/` is committed (step 0a) and no S58 commit stages it (G6). What the notes ask of PLAN.md (S04's G11 divergence, S05's K15 outcome) goes into the Done block.
- **R58-10 (P2 numbering).** Measured: DROPIN's P2 list ends at item 41 (WP-29's P2.30-P2.41); the register reserves P2.42-P2.57 (P2.49 withdrawn by ratification row 27: S08 fixes it, so its row is written closed, keeping the register's numbers); `grep -on 'P2\.[5-9][0-9]' .ultraplan/wp30/section-*.md` finds no number above 57. S58.3 writes P2.42-P2.57 with the register's text and the new rows from P2.58 in Appendix B's order; the checkpoint (58-07) fixes the final numbers, consecutive, after striking rows a landed section closed.
- **R58-11 (the date precedes the gate).** `scripts/run_release_gate.sh` compares the Distribution-Date with the newest commit touching a shipped file, so S58.6's date commit is made inside the gate step, before `make cert` and `make gate`; CHANGELOG.md's lines 3 and 5 move in S58.7, as WP-29 did (`97b201c`, `114f354`).
- **R58-12 (logs outlive the session).** Every log quoted is copied to `.ultraplan/handoff/wp30-<name>.log`, ignored by `.git/info/exclude`'s `*.log`.
- **R58-13 (attested, not claimed).** The sections' G1/G6/E14 records (impact at each base, detect-changes at each landing) leave no trace in git; S58 re-runs what it can (its own detect-changes, the compare against `main`) and reports the rest as "attested by the sections, not re-verified".
- **R58-14 (help terminology is not reworded here).** S06 lets the closeout reword "named in a warning" (dash.sthlp 1312-1313, 2123, 2919, 2962, 2967, 3023 at `c96facd`), but three test lines pin the phrase (measured: `grep -rn 'named in a warning' test/*.py test/*.cscript | wc -l` → 3) and seven sections own the paragraphs (R3). It is filed as a P3.3 note, with `test/cert_helpers.do:101-110`.

The section text below conforms to these refinements.
- Ratification 06oct2026 applied (ratification 06oct2026): row 25 (no floor-Python gate leg): TR-58.8, 58-18's action, verify and done and the S05 owner row lose the floor leg and the floor venv; `make gate` runs plain.
- Row 27 (ratification 06oct2026): P2.49 is not filed (S08 fixes the brushed-copy bug under P1.12a): the header, Evidence, BR-58.1, 58-19's report, the completion criteria and the 58-03 script now expect 3 open BUGS.md entries and no open entry naming P2.49; Appendix B's P2.49 row is written closed in D.7's form, keeping the register's numbering; the owner rows of S08, S16 and S32 lose P2.49.
- Row 36 (ratification 06oct2026): the by() panel label's filled box is S53's; row 69 keeps only the one-panel case, and the consumed-notes line says so.
- Row 32 (ratification 06oct2026): row 60 loses the blank-quoted-element residual (S11 now refuses a used whitespace-only element r(198)).
- Rows 4, 8, 12, 22 (ratification 06oct2026): GAPS2 D10 stays FULL, D10-b closed by disposition (directives kept in the parsed scheme, not noted); the report's documented divergences drop dropped control codes and dropped off-range date literals (both now mirror twoway); the measurements verify reads RSS growth ≤ 80 MB.
- Row 44 checked (ratification 06oct2026): R58-14 (leave "named in a warning", file a P3.3 note) agrees with section-06's Help terminology note, now reworded to the same reading.

## Overview

When S57 has landed, every P1 entry has its fix commit(s), a closed BUGS.md entry and its CHANGELOG lines, but nothing says so in one place and nothing has measured the whole: `WP30_OPEN` is an empty dict nothing pins; the map anchors of A148 may sit empty; ROADMAP.md has no WP-30 section; GAPS2.md, GAPS.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md and DROPIN-REMAINING.md still describe the P1 gaps as open; the 22 manifest residuals, the register's P2.42-P2.57 and some 30 residuals the sections measured are filed nowhere; AGENTS.md holds no WP-30 invariant; and `make test`, `make test-dev`, `make cert` (68 scripts) and `make gate` were never run on the merged tree.

After this section: `WP30_OPEN = {}` behind `TestWp30Tracking::test_no_wp30_entry_remains_open` (S58.1); every GAPS2 id a P1 source names is Closed, Partly closed or annotated by a named commit, WP-30 is DONE in ROADMAP with its requirements, traceability and the deferred platform package, the P1 rows of DROPIN carry their commits, and AGENTS.md carries "Invariants introduced by WP-30" (S58.2, after the maintainer approved the ledger at 58-07); every residual is a numbered DROPIN row or a note on an existing one, the audit is tagged and the stale `rejected_options.json` rows are measured again (S58.3); the CHANGELOG holds each entry in its lists with no marker (S58.4); the four release targets pass once each through the queue, with the release dated if the gate requires it (S58.5, S58.6); the release measurements are recorded and the merge command `git checkout main && git merge --no-ff wp30-p1` is reported, not run (S58.7).

**Test order and commit rule (CLAUDE.md rules 4 and 7).** This section fixes no P1, so it writes no regression test of a defect. Its one new test is a guard that passes on a correct tree; its failing-first proof is three recorded mutations (58-03), quoted as `Regression:` lines in S58.1's body. S58.2's body carries the same proof for the GAPS2 guard (a reverted Tracked line). A red result any run finds belongs to the section that owns the test and is fixed under that entry's id, test first (Boundaries).

## Risk: [green] — documents, one guard test, four release runs; no shipped behaviour changes

- **Why green.** No renderer, ado or Mata logic changes. Shipped-file edits are the date lines (S58.6), two stale comments and, only if nothing calls it, the dead `_dash_graph_color` (S58.1).
- **Risk factors.** (1) A Tracked line, field or token in a form the readers misread (R58-1 to R58-5). (2) A cert SKIP that is Stata having lost `python_exec`, read as a pass. (3) The gate's Distribution-Date rule failing. (4) A second full run started while one runs. (5) A section's notes or a residual lost. (6) An id classified FULL while part of its Gap is open. (7) AGENTS.md holding the maintainer's uncommitted edits (E7).
- **Mitigation.** (1) Appendix D gives every form verbatim; 58-10 checks with the readers' own `_parse_gaps2`/`_parse_roadmap_gaps2`, and the guard is proven to bite. (2) `python_exec` read before `make test` and `make cert` and after any SKIP. (3) R58-11; 58-15 computes the gate's own `newest`. (4) Every full run goes through the queue once and is read from its log (E1). (5) 58-06 extracts every section's notes and every `Residual, deferred (WP-30)` clause; Appendix C is checked row by row. (6) FULL needs a test per bullet of the **Gap** text; the maintainer approves the list (58-07). (7) 58-11 checks `git diff --quiet -- AGENTS.md` first and hands the text over instead if it fails.

## Dependencies

- **Depends on:** S01-S57 landed on `wp30-p1` by the landing routine, batches 0-20 green at G8, `batch-21-base.txt` recorded, every worktree removed. Also step 0b's baseline `<scratch>/wp30-cert-baseline.log` (queue cert mode: first and last lines are epoch seconds) and the queue script `<scratch>/full_suite_queue.sh` (step 0g).
- **Blocks:** none. Batch 21, alone, in `/Users/billy/Desktop/Programs/StataPrograms/d/dash` on `wp30-p1` (no worktree).
- **Why:** the closure proof reads the landed commits; the suites must run on the merged tree; A145 makes S58 the only editor of the tracking documents.

## Evidence

Line numbers are at `c96facd`; sections move them, so every task locates by text.

- **Readers** (`test/test_tracking_documents.py`, measured): `_GAPS2_HEADING`/`_GAPS2_TRACKED`/`_GAPS2_CLOSED`/`_GAPS2_DEFERRED` at :687-691; the four agreement tests at :1054, :1076, :1112, :1152 and the deferral test at :1199; WP-29's block at :1240-1525 (`WP29_OPEN = {}` at :1251 under a five-line comment; `test_no_wp29_entry_remains_open` at :1508-1525, the model for 58-03). S01 adds `WP30_OPEN`, `WP30_LISTS`, `WP30_SECTION`, `WP30_ALL`, `_WP30_MARKER`, `_WP30_OPEN_FORM`, `_wp30_markers`, `_wp30_open_problems`, `_wp30_marker_problems`, `_wp30_closure_problems`, `_wp30_list_problems` and `TestWp30Tracking`; its notes ask S58.1 to keep `WP30_LISTS`, `WP30_SECTION` and `WP30_ALL` for good.
- **GAPS2.md state of the ids S01's table lists** (measured with `_parse_gaps2`): `Partly closed in WP-29` — A4, A13, B12, B16, B22; `Closed in WP-29` — A6; `Closed in WP-28` — E3, K2; every other id (A3, B11, B14, B17, B18, B20, B21, B23, B25, B26, B27, B31, D2, D3, D5, D7-D12, D16-D19, E10, F3, F5, G4, G10, G14, H4, H6, I12, I14, J7, J8, K1, K3, K5, X4, X5) holds its audit text. A11 (BUGS.md:2559) stays open; C8 has no heading.
- **ROADMAP.md** (4905 lines): `## WP-29 · Close the drop-in P0 gaps — DONE` at :4448 (header, user story, BR/TR/AC, `#### P0 traceability` with a Commit column, `### Done, measured (02oct2026)`), `## Traceability matrix` at :4763 (once). WP-30's section is inserted directly above it.
- **DROPIN-REMAINING.md** (364 lines): P1 items 1-35 at :66-170 (by text), P2 items 1-41 at :171-276 (WP-29's 30-41 closing it), P3 1-12, §4 at :345 with six decisions WP-30 answers (79 options; Third-party schemes Q30 → M7; Refuse vs note → M5; Drew nothing → M6; Size units → M1; graph export → M8; Support floor → M2, M3, M9). WP-29's closed form: `[Closed in WP-29: BUGS.md "<title>", commit <sha>; residuals: P2.40]`.
- **Tag forms in use** (measured): REMAINING.md `[WP-29 P0.1, commit b0d170d: partly closed; open: …]`; TWOWAY_COVERAGE_AUDIT.md `[WP-29 P0.7, commit 758cf59: corrected -- …]` with a dated line at :4; GAPS.md `**Since WP-29 (P0.7, commit 758cf59; …).**` (:258, :963).
- **AGENTS.md:** WP-28 invariants at :23, WP-29 at :39, the generated block `<!-- gitnexus:start -->` :81 to `<!-- gitnexus:end -->` :124; clean at `c96facd`.
- **BUGS.md:** 2850 lines, 4 open entries (:2523, :2559, :2595, :2601). After WP-30: :2523 closed by S44 (in place, by disposition), so 3 open (:2559, :2595, :2601). P2.49 is not opened: S08 fixes the brushed-copy bug (ratification row 27, 06oct2026).
- **Release date:** CHANGELOG.md:3 `## 0.1.0, 02oct2026 (release candidate)`, :5 "now 20261002"; `dash.pkg:24-25` `0.1.0  02oct2026`, `20261002`.
- **`test/fixtures/rejected_options.json`** (5768 lines; task 05-01's record, no generator and no `_meta`) is read by `test/test_option_surface.cscript` O2-03/O2-04 (the `accept-and-report` disposition and `summary.by_disposition`), so S58.3 keeps the summary equal to the rows.
- **WP-29's numbers** (ROADMAP :4859-4878): `make cert` 67 of 67, 1,178 s before and **907 s** after; 10 truth blocks 97 s; `make gate` 12 of 12 examples and 20 of 20 scheme pages.
- **S09's page sizes at `c96facd`:** a saved page with `$$…$$` text 3,087,832 bytes (ships `bokeh-mathjax`), the same page in plain words 1,301,750 bytes.
- **S01's grades:** S1 (9), S2 (38), S3 (9).

## User stories

- **US-58.1** As the maintainer, I want one measured record that WP-30 is done — 56 entries closed test first, the suites, the 68-script certification and the gate green on the merged tree, no open S1/S2 — so that the release can be judged from the documents.
- **US-58.2** As the next auditor, I want every GAPS2, REM, AUDIT and DROPIN id a P1 source names marked with the commit that closed it, or with what is open, so that nothing is re-reported and nothing is lost.
- **US-58.3** As the maintainer, I want to approve what WP-30 claims it closed and every residual it hands on before they are written.
- **US-58.4** As the next agent, I want WP-30's invariants in AGENTS.md, each with its guarding test.
- **US-58.5** As the maintainer, I want the merge command reported and not run (rule 5).

## Business requirements

- **BR-58.1** Every WP-30 entry stays closed: the allowance is empty, no marker remains, each of the 56 ids has one closed entry whose Resolution holds `(WP-30, <id>)` and names tests that exist, and a test fails if any of this is undone. BUGS.md holds exactly 3 open entries (:2559, :2595, :2601 at `c96facd`), none S1 or S2.
- **BR-58.2** Each GAPS2 id is Closed in WP-30 only when every bullet of its Gap is answered by a WP-30 test, else Partly closed (naming what is open) or annotated (earlier closures); each names commits that exist; old Tracked text is kept after `was:`.
- **BR-58.3** REMAINING, GAPS.md, TWOWAY_COVERAGE_AUDIT and DROPIN carry a tag on every row a P1 source names; DROPIN's §4 records what WP-30 decided.
- **BR-58.4** Every residual (the 22 manifest items as amended by IR-2/3/4/9, P2.42-P2.57, every section note's residual, every `Residual, deferred (WP-30)` clause) is a DROPIN row, a note on an existing row, the platform package, or a documented difference, as approved.
- **BR-58.5** ROADMAP's WP-30 is DONE with its GAPS2 ids, BR-30.1-40, AC-30.1-15, a commit per entry, the deferred platform package and a measured block.
- **BR-58.6** The CHANGELOG holds each WP-30 line once in each list `WP30_LISTS` names, ending `(WP-30, <id>)`, no marker left.
- **BR-58.7** `make test`, `make test-dev`, `make cert` and `make gate` each pass once, strict, no skip, through the queue; the package date agrees with the gate's rule.
- **BR-58.8** No WP-30 commit message, BUGS/CHANGELOG/help line names a tool or vendor; no commit holds `CLAUDE.md`, `.gitignore`, a plan file or (outside E7) AGENTS.md; every worktree and `wp30-s<NN>` branch is gone; the merge is reported, not run.

## Technical requirements

- **TR-58.1 Inventory (58-01, 58-02).** Appendix A.1 to `<S>/wp30_inventory.py`, run read-only; it writes `<S>/wp30-map.tsv` (id, closing sha, every sha whose subject ends `(WP-30 <id>)`, title) and `<S>/wp30-residuals.txt`, and fails on any problem. 58-02 checks E2/E3/E4/E13 with git and grep.
- **TR-58.2 Closeout test (58-03).** `WP30_OPEN = {}` under WP-29's comment form; `TestWp30Tracking::test_no_wp30_entry_remains_open` (58-03's text); three reverted mutations.
- **TR-58.3 Registries and dead names (58-04, 58-05).** Remove the A148 anchor comments with no key below them; remove `_dash_graph_color`, its `_shared_stat_lines` entry and map entry only if nothing calls or names it; correct the two stale comments; commit S58.1.
- **TR-58.4 Ledger (58-06) and approval (58-07).** Notes, residual clauses, GAPS2 verdicts (Appendix E), REM/AUDIT/DROPIN rows, invariants and filings drafted in `<S>`; nothing written to a tracking document before the maintainer approves.
- **TR-58.5 Tracking documents (58-08 to 58-11).** ROADMAP's WP-30 entry (Appendix D.4), GAPS2 Tracked lines (D.1-D.3), BUGS appends (R58-3), REMAINING/GAPS.md/DROPIN P1 tags (D.5-D.7), AGENTS.md (D.8); one commit S58.2 with the guard proof.
- **TR-58.6 Residuals and audit (58-12, 58-13).** DROPIN rows P2.42-P2.57 and P2.58 onward (Appendix B), notes on existing rows, AUDIT tags, `rejected_options.json` rows re-measured; commit S58.3.
- **TR-58.7 CHANGELOG (58-14).** Check every WP-30 line in its lists, consolidate the superseded Requirements lines (S05), remove blank lines between consecutive WP-30 items; commit S58.4.
- **TR-58.8 Release (58-15 to 58-18).** Date by the gate's rule (S58.6); `make test`, `make test-dev`, `make cert`, `make gate` in that order through the queue; block times. No floor-Python gate leg (ratification row 25, 06oct2026: S05 measured the floor once).
- **TR-58.9 Measurements and report (58-19 to 58-21).** Page sizes and render times on `c96facd` and HEAD, served memory and latency, the compare against `main`, the path guard and version pin, message checks, re-index; commit S58.7; report.
- **TR-58.10 Security (rule 1).** Nothing reaches a page. The scripts read git through `subprocess.run([...])` argument lists (no `shell=True`), JSON through `json.load`, never `eval`; they write only under `<S>`. Stata runs only through the `make` targets, the queue and `scripts/stata_slot.sh`; never the GUI. No served key or token is written to a document; the Done block names tests, never secrets.

## Boundaries

- **Do not fix a P1 here.** A red test, failed cert script, gate problem or missing BUGS/CHANGELOG fact belongs to the owning section: in the main checkout on `wp30-p1`, `gitnexus impact` on each symbol, the failing test first (output to `<S>/58-fix-<entry>-failure.txt`), the fix, one full run through the queue, a commit `(WP-30 P1.<n>[abc])` whose body opens with the failure text and a `Regression:` line; then resume. Never weaken, delete or deselect a test; a skip is not a pass.
- **Do not reword** a section's CHANGELOG fact, BUGS entry, help sentence or assertion; S58 places, completes and de-blanks CHANGELOG lines, appends R58-3's sentence and dates the release.
- **GAPS2.md:** only Tracked lines (R58-1 to R58-6). **GAPS.md:** body paragraphs only. **ROADMAP.md:** WP-30's section plus R58-7 tags; `## Traceability matrix` stays once; no line in WP-30 starts `# ` or `## ` but its heading; no `Gaps closed` text; no Markdown link to `PLAN.md`/`TODO.md`.
- **Never staged:** `CLAUDE.md`, `.gitignore`, `.gitnexus/`, `.ultraplan/` except `.ultraplan/handoff/DROPIN-REMAINING.md`, `*.html`, `*.log`, scratch files, AGENTS.md's generated block. Stage by name, never `git add -A`/`.`.
- **Do not** run `git checkout main`, `git merge` other than `git merge --no-edit main` (must print `Already up to date.`), `git push`, `git rebase`, `git commit --amend` on a landed commit, or a history rewrite; never commit to `main`.
- **Do not** add or register a cscript, move a hygiene pin, edit `ALLOWED`/`_MUST_WARN`, patch a generated fixture or scheme file by hand, or start a second full run (rule 11).

## Stata truth

None added. Stata runs only through the queue's `test`, `test-dev`, `cert` and `gate` modes and through `scripts/stata_slot.sh <dir> <file>.do` for: the `python_exec` check (58-01), the `rejected_options.json` probe (58-13), the render-time do-file (58-19), and a single cscript rerun through the driver if a fix needs one. Each non-cscript do-file opens `adopath ++ "<tree>/"` then `global dash_nobrowser 1` (E5). No fixture is written; nothing needs `git add -f`.

## TDD test stubs

- Test: `test/test_tracking_documents.py::TestWp30Tracking::test_no_wp30_entry_remains_open` — guard; failing-first proof by three mutations (58-03): a key put back → `WP30_OPEN is {} after WP-30's closeout; it holds ['P1.1a']`; P1.1a's entry reopened in S01's open form → `_wp30_closure_problems`' message naming P1.1a, and `… is open in the WP-30 form`; `<!-- WP-30 P1.29 -->` re-added under `### Security` → `markers left in CHANGELOG.md: ['P1.29']`.
- Documentary proof (58-10): one FULL id's Tracked line reverted to its `was:` text fails `TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it`; restored, it passes.
- Non-vacuous at DONE (unchanged): the four `TestGaps2AndRoadmapAgree` tests, `TestWp30Tracking::test_a_closed_p1_has_no_marker_and_a_resolution`, `::test_each_p1_sits_in_its_changelog_lists`, `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2`.
- Pinned tests to flip: none. Every node named by a `Flipped:` line in `c96facd..HEAD` must collect (58-02).

## Test plan

| What | How | Input | Both modes? |
|---|---|---|---|
| 56 entries closed, closing commits, extra entries, no marker | Appendix A.1 (58-01) | BUGS.md, CHANGELOG.md, git | n/a |
| E2, E3, E4, E13 | git/grep checks; `pytest --collect-only` on flipped nodes (58-02) | git, fixtures | n/a |
| Allowance empty, entries stay closed | the guard + three mutations (58-03) | BUGS.md, CHANGELOG.md | n/a |
| Registries consistent after anchor and dead-name removal | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` (58-04, 58-05) | maps, copy lists | served names |
| Classification approved first | checkpoint 58-07 | `<S>/wp30-ledger.tsv` | n/a |
| Tracked lines parse as intended | readers' one-liners; `TestGaps2AndRoadmapAgree` (58-09, 58-10) | GAPS2.md, ROADMAP.md, BUGS.md | n/a |
| Documents well formed | `test_tracking_documents.py`, `test_packaging.py` after each document task | all tracking docs | n/a |
| Invariants name tests that collect | `pytest --collect-only` (58-11) | AGENTS.md | n/a |
| Fixture summary equals its rows | 58-13's check; `test_option_surface.cscript` through the driver | rejected_options.json | n/a |
| CHANGELOG lists | `TestWp30Tracking`; per-list counts from `WP30_LISTS` (58-14) | CHANGELOG.md | n/a |
| Full suite strict, both interpreters | `make test`, `make test-dev` (58-16) | whole suite | yes (parity corpus) |
| Certification, 68 scripts, block times | `make cert` timed; Appendix A.2 (58-17) | `test/run_all_cscripts.do` | yes |
| Release gate from an install | `make gate` (58-18) | `examples/`, 26 scheme pages | yes |
| Release measurements | 58-19 | two trees | yes |

**Acceptance criteria.**
- **AC-58.1** `python3 <S>/wp30_inventory.py <R> <base> <S>` prints `ids mapped: 56 of 56; extra closed: 2; open: 4; residual clauses: <r>; problems: 0`, exit 0; `grep -c '^- \[ \] Title:' BUGS.md` prints 4.
- **AC-58.2** 58-02 prints no problem line (or only E2 exceptions, listed in the report; history is not rewritten).
- **AC-58.3** `grep -c '^WP30_OPEN = {}$' test/test_tracking_documents.py` prints 1; the mutation record holds three blocks; `test_tracking_documents.py` passes after each commit.
- **AC-58.4** `grep -c '<!-- WP-30' CHANGELOG.md` prints 0; per list, the count of lines ending `(WP-30, <id>)` equals the ids `WP30_LISTS` assigns to it (Results that change is 35 after S20's widening, Changed behaviour 24 after S14's; the script counts, it does not assume).
- **AC-58.5** 58-10's reader check prints `True True <approved FULL ids> … 76`; A6, E3 and K2 keep their prefixes; no pointer id is in the field.
- **AC-58.6** `grep -c '^## WP-30 .* — DONE$' ROADMAP.md` 1; `grep -c '## Traceability matrix' ROADMAP.md` 1; `awk '/^## WP-30 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'Gaps closed'` 0.
- **AC-58.7** `grep -c '\[Closed in WP-30' .ultraplan/handoff/DROPIN-REMAINING.md` prints 35; `grep -c 'Decided for WP-30' …` prints 6; the P2 list runs 1 to its approved last number with no gap.
- **AC-58.8** AGENTS.md: WP-28, WP-29 and WP-30 invariant headings in order above `<!-- gitnexus:start -->`; one paragraph per approved invariant; every node collects (or the text was handed to the maintainer under E7).
- **AC-58.9** The four make logs: pass counts with `0 failed`, no `skipped`, `exit=0`; `make cert` says `68 of 68 registered scripts passed`, `verdict: PASS`; `make gate` says `verdict: PASS`; wall times recorded.
- **AC-58.10** `git log --format=%B main..wp30-p1 | grep -Eic 'claude|anthropic'` 0; the same on the added lines of BUGS.md, CHANGELOG.md, dash.sthlp and dash_setup.sthlp; `git worktree list | wc -l` 1; `git branch --list 'wp30-s*'` empty; `git rev-parse main` unchanged; the report states the merge command and "not run".

## Tasks

Commit boundary: one commit per step — 58-05 (S58.1), 58-11 (S58.2), 58-13 (S58.3), 58-14 (S58.4), 58-16 (S58.6, only if 58-15 finds the date must move) and 58-21 (S58.7); subjects end `(WP-30 S58.<k>)` (Appendix F). S58.5 (58-15 to 58-18) commits nothing but S58.6.
- `<R>` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash` (on `wp30-p1`); every command starts `cd <R> &&`. `<S>` is `<scratch>/s58` (`mkdir -p`); `<Q>` is `<scratch>/full_suite_queue.sh`; `<base>` is `c96facd`.
- **Before every commit** (index step 3, E3, E7, E9, E10): `git branch --show-current` prints `wp30-p1`; `git merge --no-edit main` prints `Already up to date.` (else stop and report); `sh <Q> <R> <S>/58-full-<k>.log` launched once in the background and read on its `exit=` line (0 failed; E6 for the flaky four); `gitnexus detect-changes --scope all --repo dash > <S>/58-detect-<k>.txt` (re-run if `partial` or `truncated`); stage by name; `git diff --cached --name-only` holds only the task's files; the message written to `<S>/msg-<k>.txt`, `grep -Eic 'claude|anthropic'` → 0, `git commit -F`, the same grep on `git log -1 --format=%B` → 0. No co-author trailer (rule 6). After the commit, `gitnexus analyze --index-only --max-file-size 8192` and `gitnexus status` (indexed commit = HEAD).

<task type="auto" id="58-01">
  <name>Inventory the merged branch and its entries</name>
  <files>none</files>
  <action><![CDATA[
1. `git branch --show-current` → `wp30-p1`; `git worktree list` one line; `git branch --list 'wp30-s*'` empty (else ask the orchestrator to remove them); `git rev-parse main > <S>/58-main-sha.txt`; `git log --oneline <base>..HEAD > <S>/wp30-log.txt`.
2. `git status --porcelain` may list only ` M CLAUDE.md`, ` M .gitignore`, ` M AGENTS.md` (the maintainer's, E7), `scripts/__pycache__/`, `phases/`, and nothing under `.ultraplan/wp30` (`git status --porcelain .ultraplan/wp30` empty: an amendment is the orchestrator's to commit alone first). Record whether AGENTS.md is modified.
3. Write Appendix A.1 and A.2 verbatim (a quoted here-document) to `<S>/wp30_inventory.py` and `<S>/wp30_block_times.py`; run `python3 <S>/wp30_inventory.py <R> <base> <S> > <S>/58-01-inventory.txt; echo "exit=$?" >> <S>/58-01-inventory.txt`.
4. `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0 -p no:cacheprovider`, last line appended to the same file.
5. Python check: `<S>/py/pyexec.do` holding `adopath ++ "<R>/"`, `global dash_nobrowser 1`, ``display "PYEXEC=[`c(python_exec)']"``; `scripts/stata_slot.sh <S>/py <S>/py/pyexec.do`; `grep '^PYEXEC=' <S>/py/pyexec.log` must name the maintainer's interpreter (`/opt/anaconda3/bin/python3`); if empty, restore it with `set python_exec /opt/anaconda3/bin/python3, permanently` through the wrapper and check again.
6. Baseline: `<scratch>/wp30-cert-baseline.log` must start and end with epoch seconds and hold `registered scripts passed`; copy it to `<R>/.ultraplan/handoff/wp30-cert-baseline.log`. If missing, record `baseline not measured` (never check out an old tree to measure it).
7. `gitnexus status`: indexed commit equals `git rev-parse --short HEAD`, else re-index. Any PROBLEM line is fixed by its owner (Boundaries) before 58-02. No commit.
  ]]></action>
  <verify><![CDATA[`tail -2 <S>/58-01-inventory.txt` shows `ids mapped: 56 of 56; extra closed: 2; open: 4; residual clauses: <r>; problems: 0` and `exit=0`; the pytest line has 0 failed; `wc -l < <S>/wp30-map.tsv` prints 56; `grep -c '^PYEXEC=\[/' <S>/py/pyexec.log` prints 1; `git worktree list | wc -l` prints 1.]]></verify>
  <done>Every entry had one closed record naming existing tests and a closing commit naming it, the extra entries and the four open ones were as planned, residual clauses were collected, Stata's Python was confirmed, and the baseline was located.</done>
</task>

<task type="auto" id="58-02">
  <name>Check the package gates E2 to E13</name>
  <files>none</files>
  <action><![CDATA[
Into `<S>/58-02-gates.txt`, for every sha of `<S>/wp30-map.tsv` column 3: (E2) `git log -1 --format=%B <sha> | grep -c '^Regression: '` ≥ 1 for each closing commit and each first commit of a two-commit section, else an `E2:` line; (E3) for every fixture JSON added or changed in `<base>..HEAD` (`git diff --name-only --diff-filter=AM <base>..HEAD -- 'test/fixtures/*.json'`), `python3 -c` with `json.load` requires `_meta` with `stata_version`, `born_date`, `dash_commit`, `extracted` (`rejected_options.json` excepted: no `_meta` at `<base>` and edited only by S58.3); (E4) `git diff <base>..HEAD -- test/test_mode_parity.py | grep -E '^[-+].*ALLOWED'` empty; (E13) `git log --format=%B <base>..HEAD | grep -Eic 'claude|anthropic'` 0 and `git log --name-only --format= <base>..HEAD | grep -cE '^(CLAUDE\.md|\.gitignore)$'` 0, AGENTS.md absent; (K3) no test file deleted (`git diff --diff-filter=D --name-only <base>..HEAD -- test/` empty); flipped nodes: `git log --format=%B <base>..HEAD | sed -n 's/^Flipped: \(test\/[^ ]*\) .*/\1/p' | sort -u > <S>/wp30-flipped.txt`, then `python3 -m pytest --collect-only -q -n0 -p no:cacheprovider $(cat <S>/wp30-flipped.txt)` with no `ERROR`/`not found`. Count `Flipped:` lines and `git diff --stat <base>..HEAD -- test/fixtures | tail -1` for the Done block. An E3/E4/E13/K3 problem is its owner's defect (an E13 hit in a landed commit is reported to the maintainer at once). E2 problems are recorded as exceptions. No commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^PROBLEM' <S>/58-02-gates.txt` prints 0, or every PROBLEM line starts `E2:` and is copied to `<S>/58-e2-exceptions.txt`; the collect run reports no error; the Flipped count and fixture stat line are in the file.]]></verify>
  <done>Fix commits carried their failure text and Regression lines or were recorded as exceptions, every changed truth fixture carried its stamp, the parity allowance was unchanged, no message or commit held a forbidden name or file, and every flipped node collected.</done>
</task>

<task type="auto" id="58-03">
  <name>Add the closeout guard and empty the allowance</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
1. `gitnexus impact TestWp30Tracking -d upstream -r dash` and `gitnexus impact WP30_OPEN -d upstream -r dash` to `<S>/58-03-impact.txt` (expected LOW; UNKNOWN confirmed by `grep -rn 'WP30_OPEN' test/`; HIGH/CRITICAL reported to the maintainer before editing).
2. Replace the `WP30_OPEN = {` … `}` assignment and its comment with WP-29's form: five `#:` lines (S01 opened one entry per fix section; each fix section closed its entry and deleted its key; the closeout (S58.1) left the allowance empty; `TestWp30Tracking::test_no_wp30_entry_remains_open` keeps it so) and `WP30_OPEN = {}`.
3. Append as the last method of `TestWp30Tracking` a copy of `test_no_wp29_entry_remains_open` (:1508-1525) with WP-30 names: comment "WP-30's closeout (S58.1)"; `assert WP30_OPEN == {}` with `"WP30_OPEN is {} after WP-30's closeout; it holds %s" % sorted(WP30_OPEN)`; `markers = _wp30_markers(_read("CHANGELOG.md"))`, `assert not markers, "markers left in CHANGELOG.md: %s" % markers`; `bad = _wp30_closure_problems(set(), set(markers), entries)` plus `"%r is open in the WP-30 form" % e["title"]` for every open entry whose Resolution matches `_WP30_OPEN_FORM`; `assert not bad`. Extend the module docstring's WP-30 item with one sentence naming the guard.
4. Run the file (`-q -n0 -p no:cacheprovider`). Then three mutations, one at a time, each followed by `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k Wp30Tracking 2>&1 | grep -E '^(FAILED|E   )' >> <S>/58-03-mutations.txt` under a header `== mutation <k>: <what>`, then reverted: (1) `"P1.1a": "<its title>"` put back; (2) P1.1a's entry set to `- [ ]` with S01's open Resolution; (3) `<!-- WP-30 P1.29 -->` re-added under `### Security`. Revert BUGS.md/CHANGELOG.md with `git checkout -- BUGS.md CHANGELOG.md` and the test file by re-editing. No commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^WP30_OPEN = {}$' test/test_tracking_documents.py` prints 1; `python3 -m pytest "test/test_tracking_documents.py::TestWp30Tracking::test_no_wp30_entry_remains_open" -q -n0 -p no:cacheprovider` passes; `grep -c '^== mutation ' <S>/58-03-mutations.txt` prints 3 and the file holds `it holds ['P1.1a']`, `P1.1a` with `WP-30` from the closure reader, and `markers left in CHANGELOG.md`; `git status --porcelain -- BUGS.md CHANGELOG.md` is empty.]]></verify>
  <done>The allowance was a one-line empty dict, a guard held every entry closed with no marker left, and three recorded mutations showed it failing for each way the closure could be undone.</done>
</task>

<task type="auto" id="58-04">
  <name>Remove the map anchors left empty</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
For each `# WP-30 S<NN> (P1.<n>[abc]): <name>` comment of A148 in `test/function_test_map.py` (`FUNCTIONS`, `SETUP_FUNCTIONS`) and `test/program_coverage_map.py` (`COVERAGE["dash.ado"]`, `["dash_parse.mata"]`, `["dash_setup.ado"]`): if the next non-blank line is another WP-30 anchor or the dict's closing brace, delete the anchor line; otherwise keep it. Delete nothing else. Record each deleted anchor in `<S>/58-04-anchors.txt`. Run `python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider`. No commit (58-05 commits).
  ]]></action>
  <verify><![CDATA[`git diff -U0 -- test/function_test_map.py test/program_coverage_map.py | grep '^[-+][^-+]' | grep -vc '^-    # WP-30 S[0-9][0-9] '` prints 0 (only anchor lines removed); the count of `-` lines equals `wc -l < <S>/58-04-anchors.txt`; both test files pass.]]></verify>
  <done>Every anchor left with no key below it was gone and every key stayed, with both registry tests green.</done>
</task>

<task type="auto" id="58-05">
  <name>Drop dead names and commit S58.1</name>
  <files>dash_render.py, dash.ado, test/function_test_map.py</files>
  <action><![CDATA[
1. `gitnexus impact _dash_graph_color -d upstream -r dash` and `gitnexus impact _shared_stat_lines -d upstream -r dash` to `<S>/58-05-impact.txt`; report HIGH/CRITICAL before editing (g07). `grep -n '_dash_graph_color' dash_render.py test/*.py`: if any hit other than its `def`, its `_shared_stat_lines` tuple entry, its `function_test_map.py` entry and comments names it (a call, or a call inside the generated template text), keep it and record a P3.3 note for 58-06; else delete the function, its tuple entry and its map entry.
2. The served template comment S19 names ("lowess, scatteri and pci pass no label", by text): if it is a Python `#` comment outside emitted text, correct it to say scatteri passes a label; if it is inside the emitted template string, leave it and record a P3.3 note (`_generate_app_source` is not edited for a comment).
3. dash.ado's comment "bare numlist has NO element cap" (S39, by text): correct it to "a bare numlist is capped by Stata (r(123) above its element limit on 19.5)". Comment only.
4. `python3 -m pytest test/test_statistical_helpers.py test/test_function_test_map.py test/test_resource_limits.py test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
5. Pre-commit routine (k=1). Stage exactly `test/test_tracking_documents.py`, the two maps and whichever of `dash_render.py`, `dash.ado` changed; commit with Appendix F's S58.1 message, its body quoting `<S>/58-03-mutations.txt` as three `Regression:` lines and listing the removed anchors and names.
  ]]></action>
  <verify><![CDATA[`tail -1 <S>/58-full-1.log` holds `exit=0` with 0 failed; `git log -1 --format=%s` ends `(WP-30 S58.1)`; `git log -1 --format=%B | grep -c '^Regression: '` prints 3; `git show --name-only --format= HEAD` lists only the staged paths named; `<S>/58-detect-1.txt` names only `WP30_OPEN`, `TestWp30Tracking`, the map dicts and (if removed) `_dash_graph_color`/`_shared_stat_lines`.]]></verify>
  <done>The allowance was closed for good behind a guard, the registries held no empty anchor, dead names and two stale comments were gone or filed, and S58.1 was committed on a green tree.</done>
</task>

<task type="auto" id="58-06">
  <name>Build the ledger and every draft</name>
  <files>none</files>
  <action><![CDATA[
1. `<S>/wp30-notes.md`: for each `<R>/.ultraplan/wp30/section-NN-*.md` (01-57), `## <file>` and the text from its "Notes for the closeout" bullet or heading to the next item of the same or higher level; also each section's "Residuals" bullets. Check every row of Appendix C against it.
2. `<S>/wp30-ledger.tsv`, one row per source id (columns: entry, source id, document, anchor found by text on HEAD, verdict closed/partly/annotate/not located, commit(s), text to write, evidence test per Gap bullet). GAPS2 verdicts start from Appendix E and are decided by the FULL rule (every bullet of the **Gap** text answered by a test of a commit in `<S>/wp30-map.tsv`); where a section's note and Appendix E differ, the note wins and the row says so. REM ids from the entries' Descriptions (`grep -o 'REM-[^ ,.;]*' BUGS.md` within WP-30 entries) and the notes' anchors; AUDIT rows by content.
3. `<S>/wp30-edits.md`: every text to write, by file, in Appendix D's forms (GAPS2 lines with full old text after `was:`; BUGS appends; ROADMAP entry incl. the traceability table from `wp30-map.tsv`; R58-7 tags; REMAINING/AUDIT tags and the AUDIT dated line; DROPIN P1 tags, six §4 decisions; GAPS.md paragraphs).
4. `<S>/wp30-filings.md`: Appendix B rows with each row's measured text from the notes and the BUGS residual clauses (`<S>/wp30-residuals.txt`); a clause matching no row gets a new row; a row a landed section closed (P2.62's S32 condition, P2.63's horizontal-histogram tooltip, P2.85's clipping, P2.88's 3.10 ceiling) is struck with its evidence. Proposed final numbers from P2.58.
5. `<S>/wp30-invariants.tsv`: the 39 "AGENTS.md invariant" bullets of Appendix C (two notes on `_dash_finish_graph_text`, S09 and S29, merged), columns name, sentence, guarding nodes (from the note or the section's `Regression:` lines); each node checked with `pytest --collect-only`.
6. `<S>/wp30-maintainer.md`: struck ratification rows (from `<scratch>/wp30-ratified.txt`) and what each changed; S02's two items for the maintainer (rule 10's text and the hook message still name `arch -arm64`; the full-suite hook misses a wrapper launch); the S12, S22, S45 readings if still unanswered. No commit.
  ]]></action>
  <verify><![CDATA[`awk -F'\t' 'NF<7' <S>/wp30-ledger.tsv | wc -l` prints 0; every GAPS2 id of Appendix E and every source id in the 56 entries' Descriptions appears in column 2 (a loop over `grep -o` of BUGS.md prints no `MISSING`); every FULL row names a test per Gap bullet; each Appendix C row has a ledger, filing or invariant row; every invariant node collected.]]></verify>
  <done>Every source id had a located anchor and a verdict with evidence, every residual had a proposed row, every invariant a guarding test, and every text was drafted for approval.</done>
</task>

<task type="checkpoint" id="58-07">
  <name>Approve the classification and the filings</name>
  <files>none</files>
  <action><![CDATA[
Present to the maintainer in one message, before any tracking document is edited: (1) the GAPS2 classification — FULL ids with the test per Gap bullet, PARTLY ids with what is open, ANNOTATE ids (A6, E3, K2), and every difference from Appendix E; (2) the residual filings of `<S>/wp30-filings.md` with their final numbers (P2.42-P2.57 register rows, then P2.58 onward), the notes on existing rows, the platform-package items and the documented differences, and whether any should instead be a BUGS.md entry (an open S1/S2 would block the release); (3) the invariant count for AGENTS.md, or, if AGENTS.md has uncommitted edits (E7), that the text will be handed over instead; (4) the platform package's place (a `###` subsection of WP-30, recommended, or its own future package heading); (5) `<S>/wp30-maintainer.md`. Ask for a yes or the changes wanted; apply changes to the drafts only.
  ]]></action>
  <verify><![CDATA[The maintainer approved items 1-5 as shown or named changes, which were applied to the drafts in `<S>`; `git status --porcelain` shows no tracking document modified.]]></verify>
  <done>The maintainer approved what WP-30 would claim it closed and what it would hand on, and where, before any of it was written.</done>
</task>

<task type="auto" id="58-08">
  <name>Write the WP-30 ROADMAP entry</name>
  <files>ROADMAP.md</files>
  <action><![CDATA[
Insert Appendix D.4's section directly above `## Traceability matrix`, from the approved drafts: heading `## WP-30 · Close the drop-in P1 gaps — DONE` (U+2014), the header line, the user story, BR-30.1-BR-30.40 from PLAN.md §6 with the `[Rn]` tags removed and each struck row's amendment applied, one TR line pointing at `.ultraplan/wp30/index.md` (plain text, no link), AC-30.1-AC-30.15 from PLAN.md §9, `#### P1 traceability` (56 rows from `<S>/wp30-map.tsv`: entry, short title, grade, section, commit(s); a two-commit section `<sha1>, <sha2>`), `### Deferred: the platform package (P1.34.6)` (Appendix D.4's list), `### Scope changes of existing items`, and `### Done, measured (<to be dated in 58-21>)` with `<to be measured in 58-21>` placeholders (Appendix D.4), ending with `---`. Then append the approved R58-7 tags to the earlier packages' lines. Check: `grep -c '^## Traceability matrix' ROADMAP.md` 1; `awk '/^## WP-30 /,/^## Traceability matrix/' ROADMAP.md | grep -c '^# \|^## '` 2; no `](` in the section. No commit (58-11).
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; w=t._parse_roadmap_gaps2(open('ROADMAP.md',encoding='utf-8').read())['WP-30']; print(w['done'], sorted(w['gaps2']))"` prints `True` and the approved FULL ids; the section holds 56 traceability rows (`awk '/^#### P1 traceability/,/^### Deferred/' ROADMAP.md | grep -c '^| P1\.'` prints 56).]]></verify>
  <done>WP-30 stood in ROADMAP headed DONE with its approved GAPS2 ids, its requirements and criteria, a commit per entry, the platform package and a measured block awaiting its numbers, and earlier packages carried tags, not rewrites.</done>
</task>

<task type="auto" id="58-09">
  <name>Write GAPS2 Tracked lines and appends</name>
  <files>GAPS2.md, BUGS.md</files>
  <action><![CDATA[
1. GAPS2.md: for every approved id, rewrite the first `- **Tracked:**` line after `### <ID>. ` (found by `grep -n`) in Appendix D.1 (FULL), D.2 (PARTLY) or D.3 (ANNOTATE) form, one physical line, ending `; was: <old text>` (an id already `Partly closed in WP-29` keeps WP-29's clause as commentary and its original `was:` tail). Pointer ids are carried in their primaries' commentary (R58-4); nothing else in GAPS2.md changes.
2. BUGS.md: append ` Closes GAPS2 <ID> (WP-30, <ID>).` to the end of the Resolution line of every closed entry that carries a FULL id (R58-3), the named entry first. Change nothing else.
3. Check: `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; g,d=t._parse_gaps2(open('GAPS2.md',encoding='utf-8').read()); print('dupes',d); print('wp30',sorted(k for k,v in g.items() if v['closed'] and v['closed'][0]=='WP-30')); print('partly',sorted(k for k,v in g.items() if (v['tracked'] or '').startswith('Partly closed in WP-30 (')))"`. No commit.
  ]]></action>
  <verify><![CDATA[The one-liner prints `dupes []`, `wp30` equal to the approved FULL ids and `partly` equal to the approved PARTLY ids; A6 still starts `Closed in WP-29,` and E3, K2 `Closed in WP-28,`; `git diff --numstat -- GAPS2.md` shows equal insertions and deletions, one per id written; `grep -o '(WP-30, [A-NX][0-9]\{1,2\})' BUGS.md | sort -u | wc -l` equals the FULL count.]]></verify>
  <done>Every GAPS2 id a P1 source names said, in a form the readers parse, what WP-30 closed, by which entry and commit, and what stays open.</done>
</task>

<task type="auto" id="58-10">
  <name>Tag REMAINING, GAPS and DROPIN rows</name>
  <files>REMAINING.md, GAPS.md, .ultraplan/handoff/DROPIN-REMAINING.md</files>
  <action><![CDATA[
1. REMAINING.md: append the D.5 tag to the last line of each REM item the ledger locates (a bullet's last wrapped line; a table row's last cell before its final `|`).
2. GAPS.md: the approved D.6 paragraphs after the body paragraph each corrects (S04 I3 and E7; S37 F3/E1; S38 E3), before the next `---` or heading; no heading edited.
3. DROPIN-REMAINING.md: the D.7 tag at the end of each P1 item 1-35 (its last line, after any WP-29 note); the six `[Decided for WP-30: …]` annotations on §4's bullets (Appendix D.7); the 79-options bullet gains a WP-30 note naming what WP-30 drew.
4. Prove the GAPS2 guard bites (with 58-08 and 58-09 in place): temporarily replace one FULL id's Tracked line by its `was:` text, `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k Gaps2 2>&1 | grep -E '^(FAILED|E   )' > <S>/58-10-guard.txt`, restore the line by re-editing. Then `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; r=open('ROADMAP.md',encoding='utf-8').read(); g,_=t._parse_gaps2(open('GAPS2.md',encoding='utf-8').read()); w=t._parse_roadmap_gaps2(r)['WP-30']; c=sorted(k for k,v in g.items() if v['closed'] and v['closed'][0]=='WP-30'); print(w['done'], sorted(w['gaps2'])==c, c, len(t._matrix_gaps(r)))"` and the full tracking file. No commit.
  ]]></action>
  <verify><![CDATA[`grep -c '\[WP-30 P1\.' REMAINING.md` equals the ledger's located REMAINING rows; `grep -c '^\*\*Since WP-30 (P1\.' GAPS.md` equals the approved paragraphs; `grep -c '\[Closed in WP-30' .ultraplan/handoff/DROPIN-REMAINING.md` prints 35 and `grep -c 'Decided for WP-30' …` prints 6; `<S>/58-10-guard.txt` holds `WP-30 is DONE and lists`; the reader check prints `True True <ids> 76`; `test_tracking_documents.py` and `test_packaging.py` pass.]]></verify>
  <done>Every REMAINING, GAPS.md and DROPIN row a P1 source names said what WP-30 closed and by which commit, the task list recorded WP-30's decisions, and the guard was seen to fail on a stale Tracked line and pass on the real ones.</done>
</task>

<task type="auto" id="58-11">
  <name>Record WP-30 invariants and commit S58.2</name>
  <files>AGENTS.md</files>
  <action><![CDATA[
1. If `git diff --quiet -- AGENTS.md` fails (E7), do not edit it: write the approved section to `<S>/AGENTS-wp30.md`, name it in the report, and leave AGENTS.md out of the commit. Otherwise insert, after the last WP-29 invariant paragraph and its blank line and before `<!-- gitnexus:start -->`, `## Invariants introduced by WP-30`, a blank line, and one D.8 paragraph per approved row of `<S>/wp30-invariants.tsv`, each followed by a blank line; no `](`, no tool name.
2. `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0 -p no:cacheprovider` and `--collect-only` on every node the paragraphs name.
3. Pre-commit routine (k=2). Stage exactly `ROADMAP.md GAPS2.md BUGS.md REMAINING.md GAPS.md .ultraplan/handoff/DROPIN-REMAINING.md` and `AGENTS.md` if edited; commit with Appendix F's S58.2 message, its body opening with `<S>/58-10-guard.txt` as one `Regression:` line.
  ]]></action>
  <verify><![CDATA[`grep -n '^## Invariants introduced by WP-\(28\|29\|30\)$\|^<!-- gitnexus:start -->' AGENTS.md` prints the three headings then the marker (or AGENTS.md is unchanged and `<S>/AGENTS-wp30.md` exists); the collect run has no error; `tail -1 <S>/58-full-2.log` has `exit=0`; `git log -1 --format=%s` ends `(WP-30 S58.2)`; `git log -1 --format=%B | grep -c '^Regression: '` prints 1; `git status --porcelain -- ROADMAP.md GAPS2.md BUGS.md REMAINING.md GAPS.md` is empty.]]></verify>
  <done>The GAPS2 closures, WP-30's DONE entry, the entry appends, the row tags and the invariants were committed together as S58.2 on a green tree.</done>
</task>

<task type="auto" id="58-12">
  <name>File the residual rows in DROPIN</name>
  <files>.ultraplan/handoff/DROPIN-REMAINING.md</files>
  <action><![CDATA[
Append to §3's P2 list, after item 41 and before `### P3`, the approved rows in Appendix B's order, numbered consecutively from 42 in DROPIN's item form (`<n>. **<title>.** <measured text>. Effort <S|M|L>. Sources: <WP-30 register P1.x.y | WP-30-S<NN> (P1.<n> residuals)>, BUGS.md "<title>" residual where one exists.`). Then add the approved notes to existing items, each as `[WP-30 note (S<NN>): …]` at the item's last line (Appendix B part 2), and the scope changes: P2.11's sm* sizes, P2.12's `lwidth(none)` and P2.13's graphsize reference marked closed by WP-30 with their commits; P3.2 loses `xvarformat()`/`yvarformat()`; P3.7 loses its extractor-path part (IR-8); P3.9, P3.11 gain their work. No commit (58-13).
  ]]></action>
  <verify><![CDATA[`awk '/^### P2:/,/^### P3:/' .ultraplan/handoff/DROPIN-REMAINING.md | grep -oE '^[0-9]+\. ' | tr -d '. ' | awk 'NR!=$1{bad=1} END{print bad?"GAP":"OK", NR}'` prints `OK <last approved number>`; `grep -c 'WP-30 note (S' .ultraplan/handoff/DROPIN-REMAINING.md` equals the approved notes.]]></verify>
  <done>Every residual WP-30 hands on was a numbered P2 row or a note on the item that owns it, and the scope changes the register made were recorded.</done>
</task>

<task type="auto" id="58-13">
  <name>Tag the audit and commit S58.3</name>
  <files>TWOWAY_COVERAGE_AUDIT.md, test/fixtures/rejected_options.json, test/fixtures/twoway_corpus.do</files>
  <action><![CDATA[
1. TWOWAY_COVERAGE_AUDIT.md: under WP-29's dated line add `Rows tagged [WP-30 P1.n, commit …] were marked at WP-30's closeout (<ddmonyyyy>): …` and the approved tags (Appendix C's AUDIT column: AUDIT-09/11/12/13/15/28/29/30/33/42/44/53/64/66/71/72/74/76, :24, :26, :63-66, :72-75, :97, :99, :112-116, :136-146, :169, :173 by content, "20" → "26 shipped translations" as a tag).
2. `rejected_options.json`: write `<S>/rej/probe.do` (`adopath ++ "<R>/"`, `global dash_nobrowser 1`, `sysuse auto, clear`) running every `dash_command` of `rejected_options` and `probes` under `capture noisily` and writing id and `_rc` to `<S>/rej/rc.csv`; run it with `scripts/stata_slot.sh <S>/rej <S>/rej/probe.do`. For each row whose measured rc differs from its `dash_rc`, set `dash_rc` (and each probe's) to the measured value and its `disposition` to `honoured-WP-30-<entry>` when the rc is 0; recompute `summary.by_disposition` and `summary.dash_failures` from the rows. Edit with a script that `json.load`s and rewrites only those values in place (text substitution at each row's span), so untouched rows stay byte-identical. Run `test_option_surface.cscript` through the driver.
3. `twoway_corpus.do`: the expectation comments S38 (:294-296, :559) and S56 (:214-215) name, by text, rewritten to the measured rc; commands unchanged.
4. Pre-commit routine (k=3). Stage `TWOWAY_COVERAGE_AUDIT.md`, `.ultraplan/handoff/DROPIN-REMAINING.md` and the two fixtures; commit with Appendix F's S58.3 message (body: rows filed, rows struck with reasons, rejected_options rows changed with old and new rc).
  ]]></action>
  <verify><![CDATA[`grep -c '\[WP-30 P1\.' TWOWAY_COVERAGE_AUDIT.md` equals the ledger's AUDIT rows; `python3 -c "import json,collections as c; d=json.load(open('test/fixtures/rejected_options.json')); print(dict(c.Counter(r['disposition'] for r in d['rejected_options']))==d['summary']['by_disposition'])"` prints True; the O2 cases print PASS in `<S>/run_test_option_surface.log`; `tail -1 <S>/58-full-3.log` has `exit=0`; `git log -1 --format=%s` ends `(WP-30 S58.3)`.]]></verify>
  <done>The audit carried WP-30's tags beside its own text, the rejected-options record said what dash does now as measured, and S58.3 was committed.</done>
</task>

<task type="auto" id="58-14">
  <name>Consolidate the CHANGELOG and commit S58.4</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[
1. For each id of `WP30_LISTS`, check one line ending `(WP-30, <id>)` in each list it names; each Results line names the command, the old value and the new (the old value matches the closing commit body's failure text, `git log -1 --format=%b <sha>`); complete a missing value from that body; move a misplaced line; never reword a fact.
2. Requirements: consolidate the older lines S05 supersedes (by text, "Python 3.13 or later … Was 3.8" and "The declared minimums are the tested ones -- Python 3.13, …") with S05's line, keeping one line per requirement: Stata 19 (P1.35), the measured Python floor (P1.33), the bokeh window (P1.30), the dependency guards (P1.32).
3. Formatting only: remove blank lines between consecutive WP-30 items of one list; keep blank lines around headings and the `**WP-30 (drop-in P1, 03oct2026)**` group line.
4. `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider`. Pre-commit routine (k=4). Stage `CHANGELOG.md`; commit with Appendix F's S58.4 message.
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-30' CHANGELOG.md` prints 0; `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; print(t._wp30_list_problems(t.WP30_LISTS, t._read('CHANGELOG.md')))"` prints `[]`; `grep -cE '\(WP-30, P1\.[0-9]{1,2}[abc]?\)$' CHANGELOG.md` equals the sum of the lengths of `WP30_LISTS`' values; `TestWp30Tracking` passes; `git log -1 --format=%s` ends `(WP-30 S58.4)`.]]></verify>
  <done>The CHANGELOG held each WP-30 change once in each list it belongs to, with before and after values, one line per requirement and no marker, committed as S58.4.</done>
</task>

<task type="auto" id="58-15">
  <name>Decide the release date and sources</name>
  <files>dash.ado, dash_setup.ado, dash_parse.mata</files>
  <action><![CDATA[
Compute `newest` exactly as `scripts/run_release_gate.sh` does (shipped files from `dash.pkg`'s `f` lines; today if any is uncommitted, else `git log -1 --format=%cd --date=format:%Y%m%d -- dash.pkg stata.toc $shipped`) into `<S>/58-15-date.txt`. If `newest` ≤ the Distribution-Date (`20261002` at `c96facd`), record "no re-dating" and skip the dating parts of 58-16. Else set `*! Version: 0.1.0  <ddmonyyyy>` (today, lower-case month) in the three files (`grep -n '\*! Version:'`); the version stays 0.1.0. If 58-15 and 58-16 straddle midnight, redo this task. No commit.
  ]]></action>
  <verify><![CDATA[`<S>/58-15-date.txt` holds an 8-digit date and the decision; when re-dating, `grep -n '^\*! Version: 0.1.0  ' dash.ado dash_setup.ado dash_parse.mata` prints three lines with today's date.]]></verify>
  <done>The release date was decided by the gate's own rule and, where it had to move, the shipped sources carried today's date.</done>
</task>

<task type="auto" id="58-16">
  <name>Date the package and run pytest targets</name>
  <files>dash.pkg, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
1. If re-dating: `{* *! version 0.1.0  <ddmonyyyy>}{...}` in line 2 of both help files; `d Version: 0.1.0  <ddmonyyyy>` and `d Distribution-Date: <yyyymmdd>` in `dash.pkg`; `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q -n0 -p no:cacheprovider`.
2. `git merge --no-edit main` (`Already up to date.`); `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh` names the maintainer's interpreter.
3. `sh <Q> <R> <S>/wp30-make-test.log test` in the background, read on exit; then `sh <Q> <R> <S>/wp30-make-test-dev.log test-dev`. Never two at once; a red test is its owner's (Boundaries), then rerun that file and the target.
4. Copy both logs to `<R>/.ultraplan/handoff/`. If re-dating: `gitnexus detect-changes --scope all --repo dash > <S>/58-detect-6.txt`; stage the six dated files; commit with Appendix F's S58.6 message quoting both logs' last lines and interpreters.
  ]]></action>
  <verify><![CDATA[Each make log shows a pass count, no `failed`, no `skipped`, `exit=0`, and names its interpreter; when re-dated, `grep 'Distribution-Date' dash.pkg` shows today, `git show --stat --format= HEAD | tail -1` reports 6 files, `git log -1 --format=%s` ends `(WP-30 S58.6)`, the message grep prints 0.]]></verify>
  <done>The package carried one date the gate accepts, and the full suite passed strict with no skip under Stata's Python and the development interpreter.</done>
</task>

<task type="auto" id="58-17">
  <name>Run the certification suite and time it</name>
  <files>none</files>
  <action><![CDATA[
1. `python_exec` read again (58-01 step 5).
2. `sh <Q> <R> <S>/wp30-make-cert.log cert` in the background (the queue writes epoch seconds first and last); read on exit: `certification suite: 68 of 68 registered scripts passed`, `verdict: PASS`, `exit=0`.
3. From `certification log: <path>`: 68 `[ PASS]`, 0 `[ SKIP]`/`[ FAIL]`; a SKIP means re-reading `python_exec`, restoring and rerunning once through the queue.
4. `python3 <S>/wp30_block_times.py <path> > <S>/wp30-block-times.txt`: 57 blocks (S01's scaffold and S02-S57, each printing `S<NN> start`/`end` with date and time; a section's second block is summed with its first), `unclosed: none`; the `test_wp30_truth` region holds `test_wp30_truth: ALL CHECKS PASSED` and no `SKIP: Python` line.
5. Wall time = last line minus first; change against `wp30-cert-baseline.log` and against WP-29's 907 s (67 scripts). If the change over the baseline exceeds 300 s, list the five slowest blocks with their sections and ask the maintainer whether to fold any (done by the owner, never here).
6. A FAIL is its owner's; after the fix, rerun that script through the driver (`WP30_ONLY=S<NN>` for one block), then this task. Copy the logs to `.ultraplan/handoff/wp30-make-cert.log` and `wp30-run_all_cscripts.log`. No commit.
  ]]></action>
  <verify><![CDATA[`grep -E 'registered scripts passed|verdict|exit=' <S>/wp30-make-cert.log` shows `68 of 68`, `verdict: PASS`, `exit=0`; first and last lines are epoch seconds; the certification log has 68 `[ PASS]`; `tail -1 <S>/wp30-block-times.txt` shows `blocks: 57; … unclosed: none`.]]></verify>
  <done>The certification suite passed all 68 scripts with no skip, the WP-30 truth script passed every block, and the wall time, its change against the baseline and WP-29's 907 s, and the per-block times were recorded.</done>
</task>

<task type="auto" id="58-18">
  <name>Run the release gate from an install</name>
  <files>none</files>
  <action><![CDATA[
`sh <Q> <R> <S>/wp30-make-gate.log gate` (no floor-Python leg: ratification row 25, 06oct2026). Read on exit: `verdict: PASS`, `exit=0`, no problem line; `~/.stata19/console/stata19.rc` still names the maintainer's `python_exec` (E12). A Distribution-Date problem means a shipped file changed after 58-16: redo 58-15/58-16, then this task. Any other problem is its owner's. Copy the log to `.ultraplan/handoff/wp30-make-gate.log`. No commit.
  ]]></action>
  <verify><![CDATA[`tail -4 <S>/wp30-make-gate.log` shows `release gate: <e> of <e> examples and 26 of 26 scheme pages clean` , `verdict: PASS` and `exit=0`.]]></verify>
  <done>The release gate passed from a net-installed copy of what dash.pkg ships: every example and all 26 scheme pages clean, the date current.</done>
</task>

<task type="auto" id="58-19">
  <name>Measure page sizes, renders and serving</name>
  <files>none</files>
  <action><![CDATA[
1. `git worktree add --detach <S>/tree-base <base>` (a separate directory; the main checkout is not switched).
2. `<S>/m/measure.do` taking the tree as argument 1: `adopath ++ "`1'/"`, `global dash_nobrowser 1`, `sysuse auto, clear`; `timer` around (a) `dash scatter mpg weight, title("$$x^2$$") saving(<S>/m/<tag>-tex.html, replace)`, (b) the same with `title("x squared")`, (c) `dash scatter mpg weight, by(rep78) saving(…)`, (d) 100k rows (`set obs 100000`, seeded `rnormal()`) `dash scatter y x || lowess y x, saving(…)`; `timer list` and each file's size via `file open … read` length or `checksum`. Run it through `scripts/stata_slot.sh` once with `<S>/tree-base` (tag base) and once with `<R>` (tag head).
3. `grep -c 'bokeh-mathjax' <S>/m/*-tex.html` per tree.
4. Served: `python3 -m pytest test/test_served_resources.py -q -n0 -p no:cacheprovider -k TestPerSessionMemory -s > <S>/58-rss.log 2>&1` and `python3 -m pytest test/test_served_worker.py -q -n0 -p no:cacheprovider -k TestTheLoopAnswersDuringARecompute -s > <S>/58-latency.log 2>&1` (no full run in progress); record the printed mean RSS growth and worst `/health` latency.
5. `git worktree remove <S>/tree-base`. Write the table to `<S>/wp30-measurements.txt`.
  ]]></action>
  <verify><![CDATA[`<S>/wp30-measurements.txt` holds, for base and head: the two page sizes and the mathjax count, the four timer values; head's TeX page ships no `bokeh-mathjax` and is within 2,000 bytes of its plain page (BR-09.2); the RSS growth (≤ 80 MB, ratification row 22) and the latency (≤ 1.0 s) as printed; `git worktree list | wc -l` prints 1.]]></verify>
  <done>Page sizes with and without TeX text, render times on the pre-WP-30 and final trees, and served memory and latency under the session cap were measured and recorded.</done>
</task>

<task type="auto" id="58-20">
  <name>Run the final guards and compare</name>
  <files>none</files>
  <action><![CDATA[
1. `python3 -m pytest test/test_runner_portability.py test/test_version_floor.py test/test_tracking_documents.py test/test_pkg_metadata.py -q -n0 -p no:cacheprovider` (S02's path guard, S03's pin); `grep -c 'version 16.0' dash.ado dash_setup.ado` prints 0 and 0.
2. `gitnexus detect-changes --scope compare --base-ref main --repo dash > <S>/wp30-detect-compare.txt` (re-run if partial or truncated); record its changed-symbol and process counts.
3. E13: `git log --format=%B main..wp30-p1 | grep -Eic 'claude|anthropic'` 0; `git diff main..wp30-p1 -- BUGS.md CHANGELOG.md dash.sthlp dash_setup.sthlp | grep '^+' | grep -Eic 'claude|anthropic'` 0.
4. `python3 <S>/wp30_inventory.py <R> <base> <S>` (problems 0). No commit.
  ]]></action>
  <verify><![CDATA[The pytest run passes with no skip; both greps print 0; the compare file exists and is not partial; the inventory prints `problems: 0`.]]></verify>
  <done>The path guard, the version pin, the message checks and the inventory held on the final tree, and the change against main was recorded.</done>
</task>

<task type="auto" id="58-21">
  <name>Record measurements and report the merge</name>
  <files>ROADMAP.md, CHANGELOG.md</files>
  <action><![CDATA[
1. In WP-30's `### Done, measured` block replace every placeholder from the logs (Appendix D.4 names each source), date the heading today.
2. If 58-16 re-dated: CHANGELOG.md line 3 `## 0.1.0, <ddmonyyyy> (release candidate)` and line 5's `now <yyyymmdd>`.
3. Pre-commit routine (k=7). Stage `ROADMAP.md` and, if changed, `CHANGELOG.md`; commit with Appendix F's S58.7 message. Re-index.
4. Report, in order: the four make verdicts and log paths; cert wall time vs baseline and vs 907 s; slowest blocks; the measurements table; open entries (3) and grades; the 56 entries with commits; FULL and PARTLY GAPS2 ids with what is open; residual rows filed (numbers) and notes; struck ratification rows; documented divergences (tsnatscale floors, plot-margin tolerance, date panel titles, CSP level 1 blank page, date literals past the browser's dates left out with a note; control codes and literals outside 0100-9999 now mirror twoway, ratification rows 8 and 12); unmeasured platforms (Linux, Windows, Intel Mac, GUI Stata under M4; Stata below 19 under M2); E2 exceptions and the sections' records "attested, not re-verified"; S02's two items for the maintainer; AGENTS text handed over if E7 applied; and `git checkout main && git merge --no-ff wp30-p1` — reported, not run.
  ]]></action>
  <verify><![CDATA[`grep -c 'to be measured\|to be dated' ROADMAP.md` prints 0; `awk '/^## WP-30 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'git checkout main && git merge --no-ff wp30-p1'` prints 1; `git log -1 --format=%s` ends `(WP-30 S58.7)`; `git log --format=%B <base>..HEAD | grep -Eic 'claude|anthropic'` prints 0; `git rev-parse main` equals `<S>/58-main-sha.txt`; `git branch --show-current` prints `wp30-p1`.]]></verify>
  <done>WP-30's measured block quoted the four green runs, the timings and the closures; every WP-30 commit was on wp30-p1 with a clean message; and the merge command was reported, not run.</done>
</task>

## Section completion criteria

- Five or six commits on `wp30-p1` (58-05, 58-11, 58-13, 58-14, 58-16 if re-dated, 58-21), each after one green full run through the queue, none naming a tool or vendor, none staging `CLAUDE.md`, `.gitignore`, `.gitnexus/` or a plan file.
- The maintainer approved the classification, filings, invariants and platform-package placement (58-07) before 58-08 wrote any of it.
- `WP30_OPEN = {}` behind the guard; 56 closed entries; 3 open; 0 markers.
- GAPS2, REMAINING, GAPS.md, AUDIT and DROPIN tagged; P2 rows 42 to the approved last number; WP-30 DONE in ROADMAP; AGENTS.md (or the handed-over text) carries the invariants.
- `make test`, `make test-dev`, `make cert` (68 of 68) and `make gate` green once each; logs in `.ultraplan/handoff/wp30-*.log`; measurements recorded; merge reported, not run.

## Notes

- **Order matters twice.** R58-1: every Tracked line and `— DONE` land in S58.2. R58-11: the date commit precedes `make cert` and `make gate`; a routed fix to a shipped file on a later day means redoing 58-15/58-16.
- **Where a red test belongs.** By the test file, the case prefix (manifest table: RR, SF, CSP, PYF, NC, SX, SU, TX, SA, SL, CF, LN, BG, LK, OB, DK, AF, KT, PS, NS, GE, SK, RG, FN, DB, BP, GT, CG, AXL, NP, MK, SP, DA, OS, MV, RS, XP, CM, BK, TSO, BI, TN, RC, MS, RM, BYG, HZ, XE, TA, AD, BYA, SVA, HM, AT, WK; TF is S01's) or the truth block header `* ==== S<NN> P1.<n>…`. If a fix changes an entry title, the GAPS2 line naming it changes in the same commit.
- **A SKIP in 0-1 s is the `python_exec` drop.** Restore through a do-file run by `scripts/stata_slot.sh`, never the GUI.
- **Shared files.** R1: no script, runner block or pin. R2: only S58.1's removals, with the registry tests. R4/R5: CHANGELOG placed and de-blanked; BUGS only R58-3's sentence. R7: no generated fixture touched; `rejected_options.json` is a hand record, re-measured. R8: `ALLOWED`/`_MUST_WARN` untouched. R13: detect-changes before every commit, re-index after.
- **Demo pages** are not regenerated (`*.html` ignored); the maintainer can run `scripts/regen_dashboards.py`.

## Appendix A: closeout scripts (written verbatim by 58-01)

### A.1 `wp30_inventory.py`

~~~~python
"""WP-30 closeout inventory (S58, 58-01).  Read-only on the repository.
Usage: python3 wp30_inventory.py <repo> <base-sha> <out-dir>"""
import os, re, subprocess, sys
repo, base, out = sys.argv[1:4]
sys.path.insert(0, os.path.join(repo, "test"))
import test_tracking_documents as t  # noqa: E402

def git(*a):
    return subprocess.run(["git", "-C", repo] + list(a),
                          capture_output=True, text=True).stdout

problems = []
if getattr(t, "WP30_OPEN", None) != {}:
    problems.append("WP30_OPEN still holds %s" % sorted(getattr(t, "WP30_OPEN", {"(absent)": 1})))
ids = list(t.WP30_ALL)
if len(ids) != 56:
    problems.append("WP30_ALL has %d ids" % len(ids))
entries, pp = t._parse_bugs(t._read("BUGS.md"))
problems += ["BUGS.md parse: %s" % p for p in pp]
subjects = [ln.split("\t", 1) for ln in git("log", "--format=%h\t%s", base + "..HEAD").splitlines()]
two = {"P1.33", "P1.16", "P1.24", "P1.30", "P1.7", "P1.6", "P1.10"}
rows, residuals = [], []
for i in ids:
    fx = re.compile(r"^Fixed \d{2}[a-z]{3}\d{4} \(WP-30, %s\)\. \S" % re.escape(i))
    hit = [e for e in entries if e["closed"] and fx.match(e["fields"].get("Resolution", ""))]
    if len(hit) != 1:
        problems.append("%s: %d closed entries open their Resolution with Fixed <date> (WP-30, %s)." % (i, len(hit), i))
        continue
    title = hit[0]["title"]
    if '"' in title:
        problems.append("%s: title holds a double quote" % i)
    close = git("log", "--format=%h", "-S- [x] Title: " + title, base + "..HEAD", "--", "BUGS.md").split()
    named = [h for h, s in subjects if s.endswith("(WP-30 %s)" % i)]
    if len(close) != 1 or close[0] not in named:
        problems.append("%s: closing commit %s not among its subjects %s" % (i, close, named))
    if len(named) < (2 if i in two else 1):
        problems.append("%s: %d commits name it" % (i, len(named)))
    rows.append("\t".join([i, close[0] if close else "", ",".join(named), title]))
    res = hit[0]["fields"]["Resolution"]
    residuals += ["%s\t%s" % (i, r.strip()) for r in re.findall(
        r"Residual, deferred \(WP-30\): (.*?)(?=Residual, deferred|$)", res, re.S)]
extra = 0
for i in ("P1.5", "P1.25b"):
    r = [x for x in rows if x.startswith(i + "\t")]
    if r and r[0].split("\t")[1]:
        n = git("show", r[0].split("\t")[1], "--", "BUGS.md").count("\n+- [x] Title:")
        extra += 1 if n >= 2 else 0
if extra != 2:
    problems.append("extra closed entries P1.5.7/P1.25.6 found: %d of 2" % extra)
opened = [e for e in entries if not e["closed"]]
p249 = [e for e in opened if "P2.49" in e["title"] + e["fields"].get("Resolution", "")]
if len(opened) != 3 or p249:
    problems.append("open entries: %d (want 3); open entries naming P2.49 (want 0): %d"
                    % (len(opened), len(p249)))
problems += ["%r is open in the WP-30 form" % e["title"] for e in opened
             if t._WP30_OPEN_FORM.match(e["fields"].get("Resolution", ""))]
marks = t._wp30_markers(t._read("CHANGELOG.md"))
if marks:
    problems.append("markers left: %s" % marks)
open(os.path.join(out, "wp30-map.tsv"), "w").write("\n".join(rows) + "\n")
open(os.path.join(out, "wp30-residuals.txt"), "w").write("\n".join(residuals) + "\n")
for p in problems:
    print("PROBLEM", p)
print("ids mapped: %d of 56; extra closed: %d; open: %d; residual clauses: %d; problems: %d"
      % (len(rows), extra, len(opened), len(residuals), len(problems)))
sys.exit(1 if problems else 0)
~~~~

### A.2 `wp30_block_times.py`

~~~~python
"""Per-block times of test_wp30_truth.cscript from a certification log (58-17)."""
import re, sys
from datetime import datetime
pat = re.compile(r"^S(\d\d) (start|end)\s+(\d{1,2} [A-Z][a-z]{2} \d{4}) (\d\d:\d\d:\d\d)\s*$")
open_, total, per = {}, 0, {}
for ln in open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = pat.match(ln.strip("\n"))
    if not m:
        continue
    sec, kind = m.group(1), m.group(2)
    ts = datetime.strptime(m.group(3) + " " + m.group(4), "%d %b %Y %H:%M:%S")
    if kind == "start":
        open_[sec] = ts
    elif sec in open_:
        d = int((ts - open_.pop(sec)).total_seconds())
        per[sec] = per.get(sec, 0) + d
        total += d
for sec, d in sorted(per.items(), key=lambda x: -x[1]):
    print("S%s\t%d s" % (sec, d))
print("blocks: %d; total: %d s; unclosed: %s" % (len(per), total, ",".join(sorted(open_)) or "none"))
sys.exit(1 if open_ else 0)
~~~~

## Appendix B: residual filings (proposed; numbers fixed at 58-07)

**Part 1, new DROPIN P2 rows.** P2.42-P2.57 are the register's rows, written with its text and source ids (manifest item 8's stairstep-hover part is struck by IR-3 and filed nowhere): 42 cmissing(n) on area/rarea and connect()/c(J) on rarea noted (P1.8.3; S40's cases); 43 cmissing(n) at estimator-generated missing points (P1.8.7); 44 recast() from histogram to range types (P1.8.7); 45 one format-writer model per distinct tick format, ~33 KB each (P1.5.3; S17's fallback tooltips add the same cost); 46 an empty trailing `|| , options` refused (P1.10.6); 47 SMCL beyond graph_text's documented tags drawn as typed (P1.11.2); 48 the served bundle ships bokeh-mathjax, 1.79 MB per session, unused by dash text (P1.11.6); 49 nonselection/muted glyphs keep creation values (P1.12.6), written closed in D.7's form, `[Closed in WP-30: BUGS.md "<S08's P1.12a title>", commit <S08's sha>]`, because S08 fixes it (ratification row 27; no BUGS.md entry of its own); 50-52 key merging, histogram-only legends, first-used axis side (P1.16.2, manifest item 16); 53 exact graphregion(margin()) outer margin and the graphregion i* options named, not drawn (P1.20.2; IR-2 strikes the bgcolor half); 54 an out-of-range xline/yline clipped (P1.21.7); 55 user and third-party `*.style` files (textboxstyle, color) not read (P1.24.3, P1.25.7); 56 `dash twoway` alone refused (P1.27.8); 57 a served session's make_document runs on the event loop, 1.6-4.6 s at 100-200k rows (P1.31.11; with S57's 100k measurement). New rows from 58:

| # | Row (source) |
|---|---|
| 58 | twoway macro-expands `$name` in a variable or value label it draws; dash draws the stored text (S09) |
| 59 | Legend and title sub-option edges: `title("T", prefix suffix)`'s printed line; `legend(label(1))` blanks key 1; values nested in `legend(region())`/`legend(title())` unchecked; `legend(po(9) top)` names `top` (S10 R-S10-1..4) |
| 60 | Stylelist element edges: an unknown `msymbol()` element draws the p# symbol (twoway: circle); glued `=` forms and `(red)` elements reach the renderer as one unknown element; a misplaced `..` echo's blank count (S11) |
| 61 | Line-width edges: the draw-time 10,000-unit bound (D-13b); `*#` on a sub-0.3 pt default (D-13e); `tlwidth()`/`glwidth()` on axes and the colour key named, not drawn (D-13f) (S13) |
| 62 | pstyle(p#) confidence bands under a scheme whose `intensity p#bar` is above full (D-16e) — struck if S32 closed it (S16) |
| 63 | Axis-format edges: `%d`/`%tb…` axis formats drawn `%9.0g` with a note (twoway writes dates); `xvarformat(bogus)` noted and `%9.0g` (twoway: `bogus not found`, no labels); a horizontal histogram's tooltip names its bins on x — that part struck if S49/S55 closed it (S18, S17 c) |
| 64 | Value-list refusals in dash's words or codes: lowess/kdensity `bwidth()`/`level()`/`degree()` lists; `base(abc)` r(198) vs r(4026); rbar `barwidth(.)` r(198) vs r(199); `mlabel(make..)` vs r(101); `mlabel(L.mpg)` vs r(111); `mlabposition(13)`'s note (S20) |
| 65 | natscale residuals: `xtick(#N)`/`xlabel(minmax)` held after a move (twoway re-places under `if`); the margin a build-time fraction, up to ~0.8% of the width off on resize (ratified A6); a user scheme's `special by_knot1/by_slope*` and `gsize *margin` unread; an axis with no finite value keeps Bokeh's autorange after a move (S21) |
| 66 | rarea's and rbar's outlines, which twoway strokes, are not drawn (S24) |
| 67 | The hand-run version note and the pre-3.7 SyntaxError (low) (S25) |
| 68 | Extend the points-free function fallback (research option B: comparisons, `!`, `cond`, n-ary min/max, round, int, ln, normal, normalden, c(pi), missing codes; 1e-12 in the normal tails) (S26; manifest item 22) |
| 69 | by() panel labels: a one-panel by() whose only value label is empty drawn without chrome (S28, S53). The filled label box is not a residual: S53 draws it (Q-28.1, ratification row 36) |
| 70 | Exact inline style runs and raised super/subscripts through a TeX route (S29; manifest item 11) |
| 71 | Colour edges: a user scheme's hex `color background/foreground` resolving `bg`/`fg`; a comma colour inside a structured sub-option (`title(…, color("1,2,3"))`, region, `xline(…, lcolor())`, `ylabel(, labcolor("255,0,0"))`) noted and drawn black where twoway refuses r(198); navy*52's clamp and the `color foreground bg` cycle; `mcolor("red",blue)` one unknown colour (S30 1-4, S31 R-S31-5) |
| 72 | Axis-look edges: two `yscale(alt)` toggle back in twoway; `gsize axis_title_gap` unread; `zlabel()`/`zscale()` look words named; `xtick()`'s labcolor/labels/nolabels named; `mlabangle()`'s h/v/rh/rv unmeasured; `fill`, `outergap()`, `extend`/`noextend`/`fextend` named (S31 R-S31-1,2,3,4,6,7) |
| 73 | scheme.class's `c(adoarchive)` branch unmeasured (S34) |
| 74 | The 57 Stata-known style names outside S36's table drawn in default attributes (D-36c), and the general 161-file style resolver; any label-colour difference under `pstyle(ci)`/histogram (S36; manifest item 14) |
| 75 | A range layer whose `mlabel()` names its own plotted variable: twoway r(102), dash draws (S37) |
| 76 | Region `intensity()`, `iintensity()`, `shadestyle()`, `ishadestyle()`, `marginonly` named, not drawn (S38, Q-38.1) |
| 77 | by()'s overall regions: `by(, graphregion() plotregion())` and `by(…, regions)` (S38, IR-9; manifest item 15) |
| 78 | Option variables with operators: `mlabel(L.make)` (twoway r(111)), `colorvar(L.mpg)`/`by(L.foreign)` (r(101)); dash r(198) (S42) |
| 79 | `recast()` on pci and pcarrowi; the note name twoway prints for a multi-word `recast()` value (S45) |
| 80 | twoway's drawing of `margin(L+10)`, `margin(1 2 3)`, `margin(1 2 3 4 5)` (S47) |
| 81 | by() layout edges: a panel's plot-region margin uses f(panels), not f(full_n)/`iscale()`; per-row label offsets not scaled; the second `iscale()` note not copied (S48) |
| 82 | A one-end-extended reference line (asymmetric user scheme) does not follow zoom-out past the last re-finish (S50) |
| 83 | Date literals in y-options (`ylabel(2000m1)`) accepted; twoway r(198) (S51) |
| 84 | by() legend and axes: `legend(ring(0))` inside the array; a clickable overall legend; `by_alternate_*` axes (S53) |
| 85 | `tstyle()` on added text through `SchemeParser.textbox_style`; Bokeh's clipping of an off-frame Label — struck if G8 did not find it (S56) |
| 86 | Served worker: library-internal `catch_warnings` blocks (pandas, numpy) can still swap `warnings.filters` for one block (Python 3.14's `-X context_aware_warnings` removes it); a free-threaded interpreter recomputes inline; a brush made while a move waits is cleared when it is drawn (S57) |
| 87 | CSP: script-src keeps `'unsafe-eval'`, style-src `'unsafe-inline'`; the launcher's header cannot carry the nonce (blocked on Bokeh; manifest item 29) |
| 88 | Hash-pinned installs (WP-29 OQ7); the `<3.11` ceiling unless S41 verified 3.10 (manifest item 30) |
| 89 | by() panel-label box: `subtitle(, fcolor() lcolor() nobox)` restyles twoway's box but stays named in dash (S53, ratification row 36) |

**Part 2, notes on existing items** (`[WP-30 note (S<NN>): …]`): P2.2 (`tmlabel()`/`tmtick()` minor ticks, item 6; D16-b); P2.4 (D17-e, item 2; `_dash_textbox_place` is the clock table `title(, position())` will reuse, S15; `subtitle(, ring(0) pos())`, S28); P2.5 (D16-e; B17's open legend parts, S10); P2.7 (`droplines()`, `nodropbase`, S26/S27); P2.8 (`bmlinestyle()`, arrowheads by `mstyle()`, S32/S36); P2.9 (`dstyle()`/`dlstyle()`, S36, item 14); P2.10 (the colour key's title up its right side and its label-side axis line, S33); P2.11 (sm* sizes closed by P1.4a for scheme and `msymbol()`, IR-4; `x`/`smx`, `v`/`smv` geometry; the lower-case shorthands stay, item 4); P2.12 (`lwidth(none)` closed by P1.12b; `mlabtextstyle` closed by P1.24; area/rarea outlines and a series style's label role stay; `mlabstyle()`, item 24); P2.13 (graphsize reference closed by P1.12a; `xsize()`/`ysize()` closed or kept per S08's Q1); P2.14 (`fintensity(1e400)`, S16; `[aw=L.x]` reusing `_dash_tsop_gen`, S42, item 7; an `mlabel()` element naming several variables, per-element jitter/barwidth bounds, `jitterseed(1 2)`, S20; `barwidth(0)`/`(-1)`, S14; `range(varname)`, S26); P2.18 (`.a`-`.z` panels, S28); P2.19 (S44's commit is its baseline; item 3); P2.20 (B21's open items; all-layer `minmax`, item 23, S35; the axis line style, S31; REM-09-02-SUBOPT-IN-LABEL closed by P1.19; the `angle(Vertical)` bullet struck); P2.21 (the sweep, item 1; D-13c; `barwidth()` on non-bar types, S14; S17 (a), (b); `xvar()`/`xva()`, S18; scalar `base()` on rbar/histogram and `barwidth()` on rspike, S20; `pst()`/`ps()`/`as()`, S32; `base()` on dot/function, S27); P2.22 (`{stSans}`/`{stSerif}`/`{stMono}` map to fixed families, S29); P2.26 and P2.38 (S23's relay is their route); P2.28 (a temporary-frame move runs `_dash_tsop_gen` first, S42); P2.31 (by() per-panel evaluation of `function` stays, S26); P2.30-P2.41 (the WP-29 residuals WP-30 closed, R58-8: P1.16 for BUGS.md:2742/:2748/:2754, P1.23a for :2771, P1.17a for the bar-width notes, P1.15c for the axis-2-title and clegend notes); P2.40 (its failure ends in one line naming `dash_setup`, S25); P2.41 (`.tolist()` and the index lists stay, S46); P3.2 (loses `xvarformat()`/`yvarformat()`); P3.3 (S08's dead `_SIZE_MAP` and `_GSIZE_PT`'s `third_tiny`/`ehuge`; `svg_truth.py`'s polygon docstring, S24; R58-14's "named in a warning" and `cert_helpers.do:101-110`; 58-05's kept names, if any); P3.4 (J7-d's iframe sentence, S22); P3.7 (loses the extractor-path part, IR-8, keeping the `W29_REPO` convention; `abbrev_truth.json`'s `mls`, S32; `value_truth.json` connect/recast rows and `regen_option_surface.py:102`, S40/S45; K3's generator parts, S03); P3.9 (the two requirements files and the bokeh window comment exist, S05/S41; the next bokeh minor needs S41's re-verification leg before the ceiling rises; K5-d, IR-16); P3.11 (the beforeprint layout, item 28/S22; the SVG has the PNG's omissions, S54; E10a).

**Part 3, the platform package and documented differences.** Platform package (ROADMAP, D.4): items 34, 35, 28 (a Chrome-driven `dash export`, PNG size, GAPS2-E10c), 33 (Python 3.10 and older); S02's critic list; S04's cmd.exe `%`/`!` measurement, `os.startfile` opener and Firefox/Safari CSP runs; S05's Windows 3.11 patch-level caveat (CVE-2024-4030); S12's `c(mode)`/`c(graphics)` under `/e`, `/b` and GUI, and the `To launch:` line; S25's processor hint off Apple Silicon; S34's path and case rules; S41, S44, S46, S54, S57's Linux/Windows/Intel and other-browser runs; every section's "Stata 14-18.5 not run (M2)". Documented differences (Done block): zyx2rule drawn as stcolor (item 25, S07); twoway's split of quoted value labels into lines (item 15); date literals and bases past the browser's dates (|ms| > 8.64e15) left out with a note (item 23, S35; those outside 0100-9999 are drawn, ratification row 12); S12's three error-code differences; S34's `scheme(NAME.scheme)`, cwd-only `dash-` names, refused paths, unfollowed links.

## Appendix C: section notes consumed

| S | Notes go to (task) | Filed |
|---|---|---|
| 01 | WP30_OPEN, guard, anchors (58-03/04); GAPS2 table (E); Severity; CHANGELOG de-blank (58-14); block times (58-17) | — |
| 02 | K1 FULL; H intro (R58-6); P1.34 row; platform package; maintainer items; REMAINING regen rows; invariant | P3.7 |
| 03 | J8, K3 PARTLY; H intro; ROADMAP :4750 tag; P1.35 row; platform item 35; invariant; BUGS :1287 left as written | — |
| 04 | I12 FULL; I14 with S12; GAPS.md I3, E7; P1.29 row; platform; CSP L1 divergence | P2.87 |
| 05 | H4 (with S41), K2 annotate; P1.33 row and §4 Support floor; P3.9; platform; CHANGELOG Requirements (58-14); invariant; K15 to Done | platform 33 |
| 06 | X4 FULL; I summary (R58-6); P1.26 part a; ROADMAP :452 tag; help wording (R58-14) | P3.3 |
| 07 | X5 with S34; AUDIT :144; P1.25 part a; zyx2rule documented; invariant | — |
| 08 | D2 (B9 inside); P1.12 (brushed copies included, ratification row 27); P2.13; AUDIT :112-114, :136, :140; invariant | P3.3 |
| 09 | D3 (J5 inside); ROADMAP :3039 tags; P1.11; invariant (merged with S29) | P2.48, P2.58 |
| 10 | B17, B21, B22; REM LABSIZE; P1.19; P2.20 | P2.59 |
| 11 | D8 with S20; REMAINING row 06; PHASE-28 tag; P1.1; AUDIT stylelists | P2.60 |
| 12 | I14-a/b; P1.27 row (CRIT-02..09); documented differences; platform; invariant | P2.56 |
| 13 | D2; ROADMAP :2048-2050 tag; P1.12; P2.12; AUDIT; invariant | P2.61, P2.21 |
| 14 | A3 with S27; AUDIT :72-75; P1.17; ROADMAP :4554/:4660/:4703 tags; invariant | P2.21, P2.14 |
| 15 | D12, D17, D16 (+P1.3a), B25-c; P1.2 part a; S24 hand-off (checked) | P2.4 |
| 16 | D11; ROADMAP :2051 tag; AUDIT :112, :115, :116; P1.2 part b | P2.14, P2.62 |
| 17 | REM-08-05; P1.23 text part; AUDIT colour key | P2.45, P2.21, P2.63 |
| 18 | G10; E3 annotate (B8); REM FMT, DATE-FORMAT; P1.5 row; AUDIT :137; rejected_options (58-13); invariant | P2.45, P2.63, P3.2 |
| 19 | A13 (C10 inside); P1.16; template comment (58-05); invariant | P2.50-52, P2.30-41 |
| 20 | D8; REMAINING row 06; P1.1; AUDIT stylelists | P2.14, P2.21, P2.64 |
| 21 | B25 with S44; P1.3 part a; AUDIT default axes | P2.65 |
| 22 | J7; E10 with S54; P1.28 part a; AUDIT `saving()`, Stored results; platform; P3.11 | P3.4, P3.11 |
| 23 | F5; I summary; P1.26 part b; A11/C8 stays open | P2.26, P2.38 |
| 24 | D18, D19, D5 PARTLY; AUDIT :112; REM :1381; P1.4 part a | P2.11, P2.66, P3.3 |
| 25 | H6; WP-07 tag; P1.32; invariant; platform hint | P2.40, P2.67 |
| 26 | A6 annotate (C5 inside); P1.22 disposition row; AUDIT :99; invariant | P2.68, P2.7, P2.14, P2.31 |
| 27 | A3; AUDIT :63-66, :115; P1.17; invariant | P2.7, P2.21 |
| 28 | B16, B31; AUDIT :143; P1.15; invariant | P2.4, P2.18, P2.69 |
| 29 | D3 (B13, J2 inside); P1.11; AUDIT graph text; invariant | P2.47, P2.48, P2.22, P2.70 |
| 30 | D7 with S43; P1.13 | P2.71 |
| 31 | B23, D9, B21; REM NOLABELS etc.; AUDIT :137; P1.18 | P2.71, P2.72, P2.20 |
| 32 | B11 with S36 (D6 inside); REM style lists; AUDIT-29/30; P1.14; rejected_options | P2.8, P2.12, P2.21, P3.7 |
| 33 | D10; REM 11-04, row 11; P1.4 | P2.10 |
| 34 | X5; REM §3 e, f; AUDIT :144 (AUDIT-74); P1.25 and §4 Q30; platform; invariant | P2.55, P2.73 |
| 35 | REM 08-04 tags; P1.23 positions; divergences; invariant | P2.20 |
| 36 | B11; REM style lists; AUDIT-30; P1.14; rejected_options | P2.8, P2.9, P2.12, P2.74 |
| 37 | A4, B27 PARTLY; REM :139/:454/:810-881; AUDIT :113; GAPS.md F3/E1; P1.24; rejected_options; invariant | P2.12, P2.75 |
| 38 | B18 with S47; AUDIT :141; GAPS.md E3; ROADMAP :1527 tag; P1.20; rejected_options, corpus; invariant | P2.53, P2.76, P2.77 |
| 39 | B22; AUDIT :139; dash.ado comment (58-05); P1.21; invariant | — |
| 40 | A4, B12 (G15 inside); REM connect; AUDIT-09/11; ROADMAP :1567 tag; P1.8; invariant | P2.42, P2.43, P3.7 |
| 41 | H4 (I7 inside), K5, K2 annotate; P1.30; invariant; platform | P3.9, P2.88 |
| 42 | G4; P1.7; invariant; platform | P2.14, P2.28, P2.78 |
| 43 | D7; P1.13; invariant | — |
| 44 | B25; P1.3; invariant; platform | P2.19 |
| 45 | A4, B12; AUDIT-09/11/12; rejected_options; invariant | P2.44, P2.79, P3.7 |
| 46 | F3 (I4 inside), G14; invariant; platform | P2.41, P2.57 |
| 47 | B18; AUDIT :141; invariant | P2.53, P2.80 |
| 48 | B16; REM :396; P1.15; invariant | P2.81 |
| 49 | B12 (A7 inside); REM :124-126, :305; AUDIT-15; P1.9; rejected_options; invariant | — |
| 50 | B22; AUDIT :139; P1.21; invariant | P2.82 |
| 51 | A4, B14; REM t-options; P1.6; rejected_options; invariant | P2.83 |
| 52 | B21; REM LABEL-ADD; P1.18; invariant | — |
| 53 | B16, B26, B31; AUDIT-71/72; P1.15; invariant | P2.69, P2.84 |
| 54 | E10 PARTLY, J7; P1.28; invariant; platform | P3.11 |
| 55 | B12 (A7); REM :124-126; AUDIT-15; P1.9; rejected_options; invariant | — |
| 56 | B20; REM text rows; AUDIT-13; P1.10; rejected_options, corpus; invariant | P2.85 |
| 57 | F3; C intro (R58-6); P1.31 recompute part; invariant; platform | P2.57, P2.86 |

Review notes also consumed: g06 (region intensity row, P2.76; no origin-matcher row: Q-41.1 resolved in S41), g07 (`_dash_graph_color`, 58-05), g08 and open-questions (Q-28.1, answered "Add to S53" by ratification row 36, so P2.69 keeps only the one-panel case), g02 (S08 Q1 → P2.13 note), g04 (Results 35), g03 (D16 + P1.3a).

## Appendix D: forms

- **D.1 FULL:** `- **Tracked:** Closed in WP-30, BUGS.md "<completing entry title>", commit <sha>[; with BUGS.md "<title>", commit <sha>]…[; <pointer ids carried>; <stale Gap anchor, now file:line>][; WP-29 (P0.<n>, commit <sha>) closed <part>]; was: <old text>`.
- **D.2 PARTLY:** `- **Tracked:** Partly closed in WP-30 (P1.<n>, commit <sha>[; P1.<m>, commit <sha>]): <what closed>; open: <what, with its P2/P3 row>; was: <old text>`.
- **D.3 ANNOTATE:** insert `; WP-30 (P1.<n>, commit <sha>): <what>` before `; was:`, the `Closed in WP-2x, …` prefix untouched.
- **D.4 ROADMAP WP-30:** header `**GAPS2 closed:** <FULL ids, comma-separated> · **Severity:** S1 (9), S2 (38), S3 (9) · **Effort:** XL · **Depends on:** WP-29`; then the user story, `### Business requirements`, `### Technical requirements`, `### Acceptance criteria`, `#### P1 traceability` (`| P1 | Entry (BUGS.md) | Grade | Section | Commit |`, rows `| P1.1a | … |`), `### Deferred: the platform package (P1.34.6)` (Appendix B part 3), `### Scope changes of existing items` (P2.11-P2.14, P3.2, P3.7, P3.9, P3.11), `### Done, measured (<date>)` with bullets: Entries; Per entry (one clause each); GAPS2 (FULL, PARTLY, annotated); Residuals (P2.42-P2.<last>, notes, platform package); Documented differences (the six ratified ones and Appendix B part 3); Python floor outcome (K15) and bokeh window; Fixtures (58-02 stat); Tests flipped (count); Security (G9 tests by name); Runs (make test, make test-dev with counts and interpreters; make cert 68 of 68, wall time vs `wp30-cert-baseline.log` and vs WP-29's 907 s, the slowest blocks; make gate counts); Measurements (58-19 table); Compare against main (58-20); Not measured (M2, M4); AGENTS.md; `- **Merge.** \`git checkout main && git merge --no-ff wp30-p1\` -- reported, not run.` Earlier-package tags: `[WP-30 P1.<n>, commit <sha>: <correction>]`.
- **D.5 REMAINING/AUDIT tag:** `[WP-30 P1.<n>, commit <sha>: closed]` or `…: partly closed; open: <what>` or `…: corrected -- <text>`.
- **D.6 GAPS.md:** `**Since WP-30 (P1.<n>, commit <sha>).** <correction>` as its own paragraph.
- **D.7 DROPIN:** P1 item: `[Closed in WP-30: BUGS.md "<title>", commit <sha>[; BUGS.md "<title>", commit <sha>]; residuals: <P2/P3 ids or none>]`; P1.22 `[Closed in WP-30 by disposition (M12): WP-29 P0.6, commit 96aa267; BUGS.md "<title>", commit <sha>; residuals: P2.14, P2.7, P2.31, P2.68]`; P1.34/P1.35 add `under M4`/`under M2` and `measurement: the platform package`. §4: `[Decided for WP-30: M<k>, <answer>; <entries and commits>]` on Third-party schemes (M7), Refuse vs note (M5), Drew nothing (M6), Size units (M1), graph export (M8), Support floor (M2, M3, M9).
- **D.8 AGENTS.md:** `**<Name>.** <sentence>. Guarded by \`test/<file>.py::<Class>[::<test>]\`[, <case id>].`

## Appendix E: GAPS2 classification at plan time (58-06 decides)

- **FULL expected:** A3 (P1.17a, P1.17b), A13 (P1.16), B14 (P1.6), B16 (P1.15a/b/c), B18 (P1.20a/b), B20 (P1.10), B22 (P1.19, P1.21a/b; c by WP-29 P0.5), B23 (P1.18a), B25 (P1.2a, P1.3a, P1.3b), B31 (P1.15a, P1.15c), D2, D3, D7, D8, D9, D10, D11, D12, D18, D19, F3, F5, G4, G10, H6, I12, I14, K1, X4, X5.
- **PARTLY expected:** A4 (WP-29's open list less recast/connect/mlabvposition/t-options), B17 (legend parts, P2.5), B21 (P2.20), B27 (headlabel, pc* first-point labels, extended missing, value-labelled dates), D5 (P2.11), D16 (D16-b P2.2, D16-e P2.5), D17 (D17-e P2.4), E10 (E10a P3.11, E10c platform), G14 (G14-a..c, P2.28), J8 (author, README, licence, Jump To), K3 (generators, P3.7), K5 (K5-d, P3.9).
- **Judged at the ledger:** B11 (`mlpattern`, `colorlist`, `coloruseplegend` in its heading), B12 (`vertical`), B26 (parts other than d), H4 (H4a, H4f), J7 (J7-d to P3.4).
- **ANNOTATE:** A6 (WP-29), E3, K2 (WP-28). **Open, untouched:** A11 (BUGS.md:2559).

## Appendix F: commit messages (subject; body lines)

- **S58.1** `Keep every WP-30 entry closed and drop the empty map anchors (WP-30 S58.1)`; three `Regression: test/test_tracking_documents.py::TestWp30Tracking::test_no_wp30_entry_remains_open -- failed on <mutation> with <text>`; the anchors and names removed.
- **S58.2** `Mark what WP-30 closed in GAPS2, the backlog and the roadmap (WP-30 S58.2)`; one `Regression:` line from `<S>/58-10-guard.txt`; FULL/PARTLY/annotated ids; "the Closed lines and DONE land together: either alone fails the tracking tests".
- **S58.3** `File WP-30's residuals and tag the coverage audit (WP-30 S58.3)`; rows filed and struck; rejected_options rows with old and new rc.
- **S58.4** `Consolidate the WP-30 CHANGELOG lines (WP-30 S58.4)`; per-list counts.
- **S58.6** `Date the 0.1.0 release candidate for WP-30 (WP-30 S58.6)`; both make logs' last lines and interpreters.
- **S58.7** `Record WP-30's release measurements (WP-30 S58.7)`; the four verdicts, the cert time against the baseline and 907 s, the measurements.
