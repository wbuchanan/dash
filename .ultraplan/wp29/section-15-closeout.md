# Section 15: Closeout

> Part of: WP-29 · P0: all 20, tracked as 21 BUGS.md entries (P0.1-P0.20, P0.12 as P0.12a and P0.12b), opened by section 01 and closed by sections 02-14; recorded, reconciled and proven here · Risk: green · Batch: 4 (main checkout on `wp29-p0`, alone) · Depends on: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14 · Blocks: none · Tasks: 17, five or six commits (S15.1, S15.2, S15.3, S15.4, S15.6 only if the release date must move, S15.7)

## Review amendments (derivation and binding refinements)

> Batch **4** · Depends on **01-14** · Blocks **none** · Risk **green** · Commits: one per closeout step, subjects ending `(WP-29 S15.<k>)` (index.md A10); a defect found here is fixed under its owner's id `(WP-29 P0.<n>)`, never under S15's.

There was no research report and no design review for this section (the research list handed to it is empty). It is derived from `index.md` (A4, A5, A10, the "Deltas from BRIEF.md" table, R1-R8, gates G5-G11), `PLAN.md` §7 "S15" and §9 E1-E12, section 01's "Notes for the closeout" and Appendices A-D, the "Notes for the closeout" of the section files written at plan time (02, 03, 05, 06, 07, 08, 10), and WP-28's closeout (`.ultraplan/sections/section-19-closeout.md` and its commits `e520a48`, `157400c`, `1f53868`, `4508bfe`). Every claim below was measured at `7421d3d` (Evidence). The measurements led to twelve refinements of `PLAN.md` §7 S15. They are binding here:

- **R15-1 (Closed lines and DONE land together).** S15.2 commits only the GAPS2 lines that are *not* `Closed in WP-29` (partly closed, WP-28 residual notes, C4), the `(WP-29, <gid>)` appends in BUGS.md and the REMAINING/AUDIT/DROPIN/GAPS.md marks. The `Closed in WP-29, …` Tracked lines are written in S15.3's commit, together with `— DONE` and the `**GAPS2 closed:**` ids. Reason: `TestGaps2AndRoadmapAgree::test_every_closed_gaps2_entry_is_listed_by_its_package` (test_tracking_documents.py:1099) fails on a `Closed in WP-29` line while WP-29 is not DONE, and `test_every_gaps2_id_a_done_package_lists_is_closed_by_it` (:1063) fails the other way. WP-28 hit the same pair and landed both in one commit (`e520a48`, body: "either one alone fails the tracking tests").
- **R15-2 (one commit per Tracked line).** `_GAPS2_CLOSED` (:676-677) reads `commit ([0-9a-f]{7,40})\b`, so a Tracked line names exactly one commit after `commit `. S08's note form `commits <F2 sha>, <F4 sha>` would match neither Closed nor Deferred. A second commit is commentary after the first: `…, commit <sha1>; with BUGS.md "<title2>", commit <sha2>; was: …`.
- **R15-3 (WP-28's closed ids keep their prefix).** E1, G1, G3 and G16 already read `Closed in WP-28, …` and are listed by WP-28's `**GAPS2 closed:**`. Rewriting them to `Closed in WP-29` breaks `test_every_gaps2_id_a_done_package_lists_is_closed_by_it` for WP-28. Their WP-29 part is written inside their residual clause, and they are never listed in WP-29's field.
- **R15-4 (duplicates have no heading).** A10, C1, C5, C10, C13, E4, G15 and H2 are "same gap as" pointers (GAPS2.md Appendix, :2025-2060) with no `### ` heading, so `test_every_gaps2_id_a_package_declares_has_a_heading` (:1041) refuses them in the field. Their primary id's line (C7, A9, A6, A13, A9, C4, B12, F4) carries them.
- **R15-5 (GAPS.md body only).** No GAPS.md heading gains `CLOSED by WP-29`: WP-29 has no `**Gaps closed:**` field, so `TestGapsAndRoadmapAgree::test_a_closing_work_package_is_done_and_lists_the_gap` (:827) would fail. Each correction is a body paragraph opening `**Since WP-29 (P0.<n>, commit <sha>).**`, which `_RESOLVED_BODY` (:531) does not read as a closure.
- **R15-6 (AGENTS.md placement).** AGENTS.md ends with a generated code-intelligence block (`<!-- gitnexus:start -->` at :39 to `<!-- gitnexus:end -->` at :81, committed at the maintainer's request in `157400c`). The WP-29 invariants go between the WP-28 invariants (:23-37) and that block. A tool refresh of the block (`npx gitnexus analyze` rewrites it) is set aside before the edit and restored after the commit.
- **R15-7 (the release date moves only if the gate demands it).** The version stays `0.1.0` and the CHANGELOG heading keeps its text (PLAN.md §3). The seven date lines and the heading's date move only when the newest commit touching a shipped file is dated after `20260930` (the gate's rule, `scripts/run_release_gate.sh:18-31`, `scripts/release_verdict.py:213-215`). WP-28 re-dated the same way (`1f53868`, `4508bfe`).
- **R15-8 (PLAN.md is not edited; superseded 01oct2026).** PLAN.md is part of the plan, which step 0a commits on `wp29-p0` (round 2, answer C), and is not in this section's files. It no longer needs a report entry or a ROADMAP rewording: R-6 and the maintainer's answers of both rounds were ratified on 01oct2026 at plan time, PLAN.md BR-29.7, BR-29.9, BR-29.10, BR-29.11 and E6 were amended then (BR-29.10, BR-29.11 and E6 again for round 2: the once-printed link, answer A; the launch from the verified bytes, answer B), and section 01's Appendix D writes those texts into ROADMAP.md (PLAN.md §7 S01 item 1 and S15.3). S15 applies no D.10 rewording and names no superseded PLAN.md sentence; it only checks that ROADMAP's copies read as PLAN.md §7 S01 item 1 (15-10).
- **R15-9 (rule 4 per commit).** Each S15 commit is preceded by `git merge --no-edit main` (expect `Already up to date.`) and one full run, `python3 -m pytest test/ -q`. The hook allows two free launches per session (`MAX_FREE_LAUNCHES = 2`, `.claude/hooks/guard-full-suite.sh`), so the third and later launches are prefixed `FULL_SUITE_RERUN=1`. S15.6's full runs are `make test` and `make test-dev`, which the hook does not count.
- **R15-10 (new residuals go to the task list).** Items the sections hand on to "file" (S07's two-colorvar refusal, by() key, empty and all-missing colorvar layers; S10's six; S05's and S02's residuals) are appended to `.ultraplan/handoff/DROPIN-REMAINING.md` after the checkpoint (15-06), not opened as BUGS.md entries: an open S1 or S2 entry blocks the release, and grading a new defect is the maintainer's call. The checkpoint may instead name entries to open.
- **R15-11 (what cannot be re-measured is attested, not claimed).** E11 (`gitnexus_detect_changes()` before every section commit) leaves no trace in git. S15 runs it before its own commits and reports the sections' G6 records as the sections reported them, marked "not re-verified".
- **R15-12 (logs outlive the session).** The session scratch does not survive the session (index.md "Deltas"). S15 copies every log it quotes to `.ultraplan/handoff/wp29-<name>.log`, which `.git/info/exclude:130` (`*.log`) ignores, as WP-28's logs sit beside them (`.ultraplan/handoff/cert-baseline.log`, `make-cert.log`, `make-gate.log`).

The section text below conforms to these refinements.

## Overview

When sections 01 to 14 have landed on `wp29-p0`, every P0 entry has a fix commit, a closed BUGS.md entry and its CHANGELOG lines, but nothing yet says so in one place and nothing has measured the whole:
- `WP29_OPEN` in `test/test_tracking_documents.py` is an empty multi-line dict that nothing stops a later commit from refilling;
- ROADMAP.md's WP-29 is open, its `**GAPS2 closed:**` field still reads `(filled at closeout)`;
- the GAPS2.md entries the P0 sources cite still read `- **Tracked:** new.` or their audit text;
- REMAINING.md, TWOWAY_COVERAGE_AUDIT.md and DROPIN-REMAINING.md still describe the defects as open, and GAPS.md L10 still says "`dash` has no auth model";
- AGENTS.md holds no WP-29 invariant;
- the release has not been run as a whole: `make test`, `make test-dev`, `make cert` and `make gate` were never run on the merged tree, and the cert suite's growth against step 0b's baseline is unknown.

After this section:
- `WP29_OPEN = {}`, and a new test keeps every P0 entry closed with no marker left (S15.1);
- every source id of the 20 P0 items is marked in its document as closed or partly closed by a named commit, after the maintainer approved the classification (S15.2, S15.3);
- WP-29 is headed `— DONE`, lists the GAPS2 ids it fully closed, and carries a measured `### Done, measured` block (S15.3, S15.7);
- AGENTS.md carries "Invariants introduced by WP-29", each with a guarding test that collects (S15.4);
- the two help files were checked for contradictions between the sections' sentences (S15.5);
- the four release targets each passed once on the final tree, and the cert wall time is reported against the baseline (S15.6);
- the merge command `git checkout main && git merge --no-ff wp29-p0` is reported and not run (S15.7, rule 5).

**Test order and commit rule (CLAUDE.md rules 4 and 7).** This section fixes no P0, so it writes no regression test of a defect. Its one new test (`test_no_wp29_entry_remains_open`) is a guard that passes on a correct tree; its failing-first proof is a recorded mutation (a key put back, an entry reopened, a marker re-added), quoted in S15.1's commit body as `Regression:` lines. S15.3's commit carries the same kind of proof for the GAPS2 guard (a reverted Tracked line), as WP-28's `e520a48` did. A defect any run finds belongs to the section that owns it (Boundaries) and is fixed under that section's rules with its own failing test first.

## Risk: [green] — documents, one test, and four suite runs; no shipped behaviour changes

- **Why green.** No renderer, ado or Mata logic changes. The only shipped-file edits are the version-date lines (if R15-7 requires them), which `test/test_pkg_metadata.py` and `test/test_help_claims_1.py` hold equal.
- **Risk factors.**
  1. A Tracked line, field or heading written in a form the tracking readers misread (R15-1 to R15-5).
  2. A cert SKIP that is really Stata having lost `python_exec` read as a pass.
  3. The gate's Distribution-Date rule failing on an undated package.
  4. The full-suite hook or the conftest lock refusing a run, or a second run started while one executes.
  5. AGENTS.md's generated block overwritten or committed by accident (R15-6).
  6. A section's notes or residuals lost because a section file is read only partly.
  7. Classifying a GAPS2 id FULLY closed when part of its Gap text is still open.
- **Mitigation.**
  1. Every form is given verbatim in Appendix D and checked by the readers' own functions (`_parse_gaps2`, `_parse_roadmap_gaps2`) before commit; the GAPS2 guard is proven to bite (15-10).
  2. `python_exec` is read before `make test` and `make cert` and again after any SKIP (15-01, 15-15); a SKIP is never a pass.
  3. 15-13/15-14 compute the gate's own `newest` date and re-date before the gate.
  4. Every full run is started once, in the background, and read from its log; `FULL_SUITE_RERUN=1` from the third pytest launch (R15-9).
  5. 15-11 checks that `git diff AGENTS.md` before the edit lies wholly inside the generated block and restores it after the commit.
  6. 15-05 extracts every section's "Notes for the closeout" into one file, and 15-06's checkpoint shows the maintainer the full ledger.
  7. FULL requires every bullet of the entry's **Gap** text to be answered by a WP-29 commit's test; anything else is PARTLY, and the maintainer approves the list (15-06).

## Dependencies

- **Depends on:** sections 01 to 14 merged into `wp29-p0` by `patch -p1`, batches 1-3 each green at G8, worktrees removed (index.md "How to execute" step 3). Also step 0b's certification baseline `{ date +%s; make cert; date +%s; }`, written to `<scratch0>/wp29-cert-baseline.log` (index.md step 0b).
- **Blocks:** none. Parallel batch: 4, alone, in the main checkout `/Users/billy/Desktop/Programs/StataPrograms/d/dash` on `wp29-p0` (no worktree).
- **Why:** the closure proof reads the merged commits and BUGS.md titles on `wp29-p0`; the suites must run on the merged tree; and A5 makes S15 the only editor of the cross-package tracking documents.

## Evidence

All line numbers are at `7421d3d` (`git log --oneline -1` → `7421d3d Record what remains for dash to be a drop-in twoway replacement`). Step 0a commits `TWOWAY_COVERAGE_AUDIT.md` unchanged, so its line numbers hold. Other documents move as sections land; every task locates by text, not by number.

### The readers S15 writes for (`test/test_tracking_documents.py`, 1226 lines at 7421d3d)

```python
 674 _GAPS2_HEADING = re.compile(r"^### (?P<id>[A-NX]\d{1,2})\. (?P<title>\S.*)$")
 675 _GAPS2_TRACKED = re.compile(r"^- \*\*Tracked:\*\* (?P<text>\S.*)$")
 676 _GAPS2_CLOSED = re.compile(
 677     r'^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b')
 678 _GAPS2_DEFERRED = re.compile(r"^Deferred \((WP-\d{2})\): \S")
```

- `_parse_gaps2` (:681-718) reads the first `- **Tracked:**` line after each `### <ID>.` heading; text after the point where `_GAPS2_CLOSED` stops matching is commentary.
- `_parse_roadmap_gaps2` (:721-741) reads `^\*\*GAPS2 closed:\*\* (.+?)(?: · |$)` and keeps items matching `^(?:and\s+)?([A-NX]\d{0,2})(?![A-Za-z0-9-])`, so `(filled at closeout)` and `none` yield no id.
- `_wp_sections` (:628-642): a package is DONE when its heading ends `— DONE`; a section ends at `^# ` or `^## (?!WP-)`.
- The four GAPS2 agreement tests (:1041, :1063, :1099, :1139) and the deferral test (:1186). `test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit` (:1139-1184) requires the named title's entry to be closed, its Resolution to hold `(WP-29, <gid>)`, and `git cat-file -e <sha>^{commit}` to succeed.
- GAPS.md readers: `_status` (:556), `_classify` (:574) read `CLOSED by` only in a heading; `_RESOLVED_BODY` (:531) flags a body line opening `**RESOLVED`, `**CORRECTED, then CLOSED`, `**Closed`, `**CLOSED`, `**Finished by` or `**<word> closed by` under a heading that does not say `CLOSED by`.
- `_MD_LINK` (:935) flags a Markdown link to `PLAN.md`/`TODO.md` in any `.md` the walk reaches. The walk skips `REMAINING.md`, `phases/` and every root directory starting `.ultraplan` (`_USER_RECORDS`, :88), but reads `AGENTS.md`, `ROADMAP.md`, `GAPS.md`, `GAPS2.md` and `TWOWAY_COVERAGE_AUDIT.md`.
- Section 01 (its Appendix B) adds `WP29_OPEN`, `WP29_LISTS`, `WP29_ALL`, `_WP29_MARKER`, `_WP29_OPEN_FORM`, `_wp29_markers`, `_changelog_lists`, `_changelog_list`, `_wp29_open_problems`, `_wp29_marker_problems`, `_wp29_closure_problems`, `_wp29_list_problems` and `TestWp29Tracking` (six tests). Its "Notes for the closeout" ask S15 to set `WP29_OPEN = {}`, add `test_no_wp29_entry_remains_open`, keep `WP29_LISTS`/`WP29_ALL`, replace the GAPS2 field's parenthetical entirely, and optionally add a commit column to `#### P0 traceability`.

### The documents at 7421d3d

- **GAPS2.md** (2064 lines). The headings and Tracked lines the P0 sources name (`grep -n "^### <ID>\. "`, then the first `- **Tracked:**` after it):

  | Id | Heading | Tracked | Tracked text (start) |
  |---|---|---|---|
  | A1 | 111 | 120 | `GAPS.md E1 (sort(varlist) deferred); BUGS.md:2441-2443 …` |
  | A4 | 175 | 196 | `GAPS.md E1 (connect, cmissing, recast, sort, …` |
  | A6 | 215 | 228 | `new (the empty-layer note is documented at dash.sthlp:327-328).` |
  | A9 | 246 | 259 | `GAPS.md A4 (the rule of thumb "stays as it was"); …` |
  | A13 | 291 | 306 | `new.` |
  | B4 | 418 | 423 | `new.` |
  | B12 | 476 | 488 | `GAPS.md E1 (deferred).` |
  | B15 | 505 | 513 | `dash.sthlp:2392-2399 (documented limit); REMAINING.md:2459 …` |
  | B16 | 516 | 525 | `GAPS.md E3 (named remainder); dash.sthlp:1676-1679.` |
  | B22 | 595 | 604 | `GAPS.md E3 (named remainder).` |
  | C4 | 743 | 755 | `Deferred (WP-28): out of scope by decision (DISCOVERY Q3), with its duplicate E4; …; was: new. …` |
  | C7 | 760 | 770 | `GAPS.md A4; ROADMAP.md WP-18 follow-up; BUGS.md:1237 …` |
  | C12 | 781 | 797 | `new.` |
  | E1 | 1102 | 1111 | `Closed in WP-28, BUGS.md "KPI fmt() accepts …", commit ef92806; residual deferred (WP-28): a spread of a date variable is computed in milliseconds (outside E1, E3 and G6); was: new` |
  | F2 | 1317 | 1322 | `new` |
  | F4 | 1333 | 1338 | `new` |
  | F9 | 1353 | 1363 | `new` |
  | G1 | 1393 | 1398 | `Closed in WP-28, … ; residual deferred (WP-28): … shadowed by the derived field in hover() and mlabel(); was: new` |
  | G3 | 1409 | 1414 | `Closed in WP-28, BUGS.md "The data limit counts exported values, …", commit 4e23bc0; residual deferred (WP-28): …` |
  | G16 | 1487 | 1492 | `Closed in WP-28, BUGS.md "Value labels are never drawn …", commit 429d679; residual deferred (WP-28): on the one-line route a hover()-only variable is not exported …; an x or y variable not named in hover() keeps its number in the tooltip; was: new (documented difference 6)` |
  | H7 | 1545 | 1550 | `new.` |
  | I2 | 1618 | 1638 | `new.` |
  | I3 | 1641 | 1656 | `GAPS.md L10 records "no auth model" as the design. …` |
  | X3 | 1962 | 1973 | `new` |

  `grep -c 'Tracked:\*\* Closed in WP-28' GAPS2.md` → 22; the only `Deferred` line is C4's (:755).
- **ROADMAP.md.** WP-28 (`## WP-28 · Close the GAPS2 audit's 22 gaps — DONE`) has `### Done, measured (30sep2026)` with one bullet per group, the run numbers, `575 s before WP-28 and 699 s after`, the gate `12 of 12 examples and 20 of 20 scheme pages`, and `- **Merge.** \`git checkout main && git merge s3-bugs\` -- reported, not run.` Section 01 inserts WP-29 directly above `## Traceability matrix` with the header `**GAPS2 closed:** (filled at closeout) · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28`, BR-29.1-16, TR-29.1-4, AC-29.1-12 and a `#### P0 traceability` table of 21 rows (`| P0 | Entry (BUGS.md) | Grade | Section |`). Its BR-29.11 says "one-line preview pages are deleted when the command ends"; its AC-29.6 says "no preview page survives the command".
- **AGENTS.md** (81 lines): rules 1-21, `## Invariants introduced by WP-28` at :23 (seven bold-led paragraphs, :25-37), then the generated block :39-81. `git log -1 --format=%h -S'gitnexus:start' -- AGENTS.md` → `157400c`.
- **GAPS.md** L10 (:2417-2435), heading `### L10. Auth bypass — not a gap — standing note (WP-20)`, body: "`dash` has no auth model, and `test_security_surface.py:95` establishes that the help does not claim one." E1 (:906), body :950-959: "… since the S3 batch a bare sort on the connected types is taken without a note; sort(varlist) is still named."
- **TWOWAY_COVERAGE_AUDIT.md** (214 lines, "Audit date: 27 September 2026", untracked until step 0a). The rows P0 fixes falsify (`grep -n 'x order\|x-sorted\|sort(varlist)\|pwidth\|bootstrap\|common scales\|axis(2)\|recomput\|authentication' TWOWAY_COVERAGE_AUDIT.md`): summary items :24, :25, :27, :29; legend :44, :45; rows `line` :60, `connected` :61, `area` :62, `rarea` :70, `rline` :76, `rconnected` :77, `lpoly` :92, `lpolyci` :93, `Layer axes` :116, `Secondary axes` :137, `Facets` :142 (claims "common scales", lists `yrescale` as ignored), `Connection behavior` :144, `Standalone build` :161, `Server build/serve` :162, the qualification bullet :173, the envelope paragraph :183. The file carries no `AUDIT-nn` ids: DROPIN numbered its rows itself, so rows are found by text.
- **REMAINING.md** (3062 lines; last changed by `de1e2dd`). DROPIN's `REM-<sec>-C<n>[<x>]` ids are the n-th `- **[` item of Appendix C's `### <sec>` list, and `REM-<sec>-M<n>` ids are taken here as the n-th item of Appendix B's list. Checked: Appendix C 06-06 item 7 (:1848) is "Register the INTERSECTED row set for a per-plot view", which is P0.15's REM-06-06-C7; 08-05 item 3 (:2142) is "Hover rows are labelled with the EMPTY STRING", P0.3's REM-08-05-C3. One id is NOT resolved by that rule: REM-08-05-M3 would be Appendix B 08-05 item 3 (:1064, the date-cardinality warning), which is not P0.3's subject; 15-05 searches for it and records it as "not located" if it finds nothing.
- **DROPIN-REMAINING.md.** §3 P0 items at :37-62 (item 13 spans :49-55, its sources on :55); §4 decisions on P0.1 (:337), P0.7 (:338), P0.9 (:339), P0.17 (:340), P0.12 (:346); P1 runs to item 35, P2 to 29, P3 to 12. P1.15 (:105), P1.16 (:113), P1.22 (:131, `function` evaluates only 10 functions, the broad part of GAPS2 A6) and P1.23 (:134) are the items sections hand notes to.
- **BUGS.md** (2724 lines): 451 closed, 4 open (2523, 2559, 2595, 2601), each graded `S3 (WP-27)`. Section 01 appends the 21 WP-29 entries in the open form; each fix section closes its own in place with `  - Resolution: Fixed <ddmonyyyy> (WP-29, P0.<n>). … Pinned by test/… .`.
- **CHANGELOG.md.** Line 3 `## 0.1.0, 30sep2026 (release candidate)`; line 5 ends "`adoupdate` compares the Distribution-Date, now 20260930)". Section 01 places 26 markers: Results 13, Security 5, Changed behaviour 4, Requirements 1, `### Fixed in WP-29` 3, separated by blank lines (its R-02, for merging).
- **The dated lines.** `dash.ado:29`, `dash_setup.ado:16`, `dash_parse.mata:254` read `*! Version: 0.1.0  30sep2026`; `dash.sthlp:2` and `dash_setup.sthlp:2` read `{* *! version 0.1.0  30sep2026}{...}`; `dash.pkg:24-25` read `d Version: 0.1.0  30sep2026` and `d Distribution-Date: 20260930`.

### Measured for this section (30sep2026)

- **Stata's Python, through the slot wrapper.** A three-line do-file (`adopath ++ "<repo>/"`, ``display "PYEXEC=[`c(python_exec)']"``, `display` of `c(stata_version)` and `c(born_date)`) run as `dash_nobrowser=1 scripts/stata_slot.sh <scratch>/pyexec <scratch>/pyexec/pyexec_check.do` printed `rc=0`, `PYEXEC=[/opt/anaconda3/bin/python3]`, `STATAVER=[19.5] BORN=[12 Aug 2026]`.
- **The pickaxe finds the closing commit.** For WP-28's B1, `git log --format='%h %s' -S"- [x] Title: Axis-label rules misread quoted numeric text, multi-line labels and numlist forms" -- BUGS.md` printed exactly `9cd93e8 Read axis-label options by Stata's own numlist and label grammar (GAPS2 B1)`, the commit GAPS2.md:393's Tracked line names. Section 01 opens each WP-29 entry as `- [ ] Title:` and the fix turns it into `- [x] Title:`, so `-S"- [x] Title: <title>"` over `7421d3d..HEAD` names exactly the closing commit. Appendix A.1 uses this.
- **Inventory script, dry run at 7421d3d** (Appendix A.1, `python3 wp29_inventory.py <repo> 7421d3d <scratch>`): `PROBLEM WP29_OPEN still holds ['(absent)']`, 21 lines `PROBLEM P0.<n>: 0 closed entries open their Resolution with 'Fixed <date> (WP-29, P0.<n>).'`, then `ids mapped: 0 of 21; residual clauses: 0; problems: 22`. Its subject pattern was checked on seven sample subjects: `P0.1` matches `(WP-29 P0.1)` only, not `P0.10` or `P0.12b`; `P0.14` and `P0.12b` both match `(WP-29 P0.12b, P0.14)`; `P0.13` matches both `(WP-29 P0.13 F2)` and `(WP-29 P0.13 F4)`; `P0.12` matches nothing.
- **Gates script, dry run** (Appendix A.2, empty map): `commits checked: 0; Flipped: lines: 0 (0 pytest nodes); test defs at base: 5640, now: 5640; problems: 0`, exit 0. (5729 `def test_` lines in 193 test `.py` files at 7421d3d, 5640 distinct file::name pairs.) Its `ALLOWED` comparison alone printed `ALLOWED unchanged: True` at 7421d3d.
- **Block timer, on WP-28's certification log** (Appendix A.3 on `.ultraplan/handoff/run_all_cscripts.log` with `test_gaps2_truth.cscript`): `blocks: 9; total: 21 s; unclosed: none`, exit 0; `grep -c '^\* ==== S[0-9][0-9] ' test/test_gaps2_truth.cscript` → 9.
- **The closeout test, exactly as Appendix B writes it**, executed against section 01's Appendix B helpers (taken from that section file) with 21 synthetic closed entries and a stubbed `_read`: clean → `PASS`; a key put back → `FAIL: WP29_OPEN is {} after WP-29's closeout; it holds ['P0.1']`; P0.1's entry reopened in the WP-29 open form → `FAIL: P0.1 is closed and no closed BUGS.md entry's Resolution holds (WP-29, P0.1)`; a `<!-- WP-29 P0.7 -->` marker added → `FAIL: markers left in CHANGELOG.md: ['P0.7']`. The three appendix scripts were diffed against the files run above: identical.
- **GitNexus.** `gitnexus_list_repos()` lists `TYME` and `PhotoShootPlannerPro`, not `dash`. Section 01 task 01-02 runs `npx gitnexus analyze` in the main checkout; by batch 4 the index may exist and be stale.
- **The hook.** `.claude/hooks/guard-full-suite.sh`: `MAX_FREE_LAUNCHES = 2`, `OVERRIDE = "FULL_SUITE_RERUN=1"`; it matches only `pytest …` not narrowed to a file/node/`-k`/`--lf`/`--collect-only`, and a Stata `do … run_all_cscripts.do`; `make test` and `make cert` are not matched (the conftest lock still serialises pytest).
- **Logs.** `git check-ignore -v .ultraplan/handoff/wp29-x.log` → `.git/info/exclude:130:*.log`. WP-28's `cert-baseline.log` reads `1790348209` … `65 of 65 registered scripts passed` … `1790348784` (575 s); its `make-cert.log` reads `66 of 66 registered scripts passed`, `exit=0`, 641 s; its `make-gate.log` reads `12 of 12 examples and 20 of 20 scheme pages clean`, `exit=0`.
- **Help phrases at 7421d3d** (`grep -c -F`; dash.sthlp / dash_setup.sthlp): `Ctrl+C` 5/0 (:97, :752, :777, :1423, :1719); `only this machine` 1/0 (:1465); `single-user` 1/0 (:1496); `Connection order` 1/0 (:3229, "always joins … in the order of x"); `bootstrap` 1/0 (:2181); `approximat` 1/1 (dash.sthlp:2066 is lpoly's default bandwidth; dash_setup.sthlp:47 is version comparison, not WP-29's); `does not redraw` 1/0 (:1404); `shadowed` 1/0 (:183, G1's residual); `milliseconds` 2/0 (:2495, :2514); `token` 0/0; `Break` 0/0; `venv` 0/0; `externally` 0/0; `pwidth` 1/0 (:1910, "named in the note"); `localhost` 2/0.
- **Final pass lines of the eight help-claims scripts at 7421d3d** (as printed, matched whole-line): hc1 `  test_help_claims_1: ALL CHECKS PASSED`; hc2 `test_help_claims_2: ALL CHECKS PASSED`; hc3 `test_help_claims_3.cscript: ALL CHECKS PASSED`; hc4 `All help-claims-4 tests PASSED.`; hc5 `All help-claims-5 certification tests PASSED.`; hc6 `  test_help_claims_6: ALL CHECKS PASSED`; hc7 `  test_help_claims_7: ALL CHECKS PASSED`; hc8 `ALL TESTS PASSED`. Sections 02 and 08 edit hc8 and hc4; 15-12 re-reads each script's last pass string before matching.

### What the sections hand to the closeout (their "Notes for the closeout", plan time)

Sections 04, 09, 11, 12, 13 and 14 were not written when this section was; 15-05 reads every section file's notes on the merged tree. The notes already written say:
- **S02 (P0.1):** ROADMAP line "Join order matches twoway (data order; sort; sort(varlist) by a Stata rank; ts types in time order; per-bound range rows); sort() checked as twoway checks it"; GAPS2 A1-a, A1-c, A4-o, B12-e, G15-b fully closed only where the Gap text is join order or sort(varlist), partly where it names connect()/cmissing() or the rarea one-bound polygon; AUDIT-08, AUDIT-10, REM-§2-S06-sort, REM-S06-b closed; GAPS.md E1's "sort is inert" true only off the six joining types and tsline/tsrline; AGENTS invariant "join order" (`GlyphMapper._join_order`, rank columns `__dashs<k>`, `test_join_order.py`, JO-01); residuals O1 (rarea one bound missing), stable vs random ties, O6 marker paint order, M5 sort named on seven computed types, connect() (P1), `sort() sort()` all empty unpinned.
- **S03 (P0.3, P0.4):** REM-08-05-C3b, C3a, M3 closed by P0.3; CRIT-01 by P0.4; GAPS2 A13/C10 partly closed (histogram and kdensity keys; open: fit, lowess, lpoly, mband keys, pc and immediate keys, no y title when layers differ, `y1/y2` range titles); DROPIN P1.16 and P1.15 notes; AGENTS invariant "every text naming a variable goes through `_dash_var_label` …" (`test_unlabelled_variables.py`, `test_conftest_helpers.py`).
- **S05 (P0.8, P0.20):** GAPS2 E1's residual closed by P0.20; REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12 closed by P0.8; AGENTS invariant "Stata units" (`test/test_date_units.py`); documented divergence (ratified 01oct2026: a first lfit/qfit/lfitci/qfitci/kdensity/lpoly/lpolyci over a date keeps dash's date axis where twoway labels numbers; a lone kdensity's range() points before 01jan0100 are dropped); residuals (`xlabel(minmax)` on a mixed numeric axis whose first layer's variable is a date, `barwidth()` on a date axis (GAPS2 A3), function/scatteri/pci/pcarrowi on a date axis (P1.23), histogram and fit tooltips in ms (P1.23), fractional period values floored, `horizontal` (P1.9)).
- **S06 (P0.10):** G16's hover-only residual closed (FULLY vs PARTLY against its second residual is S15's call); G3's Tracked line amended with the counting rule; DROPIN P0.10 annotated; dash.sthlp:183 / G1's shadowing sentence to be re-measured at S15.5; AGENTS invariant on hover export (`test_embedded_cells.py::TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`).
- **S07 (P0.15, P0.16):** REMAINING 06-06 "Register the INTERSECTED row set" and "re-check `_apply_colorvar`" done; DROPIN P0.15/P0.16 annotated; new residual items (two colorvar layers refused by twoway r(198), by() key presence, empty colorvar layer r(3001), all-missing layer key); AGENTS invariants (`TestTheRegisteredRowsAreTheViewsOwn`; `TestTheKeyIsDrawnFromTheLayersRows`, `TestTheColourFieldName`).
- **S08 (P0.12b, P0.14, P0.13):** X3 and F2 Closed; F4 closed by the F4 commit, H2 points to F4; I3 partly closed until S13; F9 stays open with bullet c closed; AUDIT-87's file half closed; ROADMAP field X3, F2, F4 (I3 after S13); ROADMAP/PLAN BR-29.11 and E6 already carry R-6 and R-8 (ratified 01oct2026: no privacy refusal, one note per command naming a location that is not private, anti-hijack refusals r(7102), r(603) only for an OS failure to create a folder); residual: in a shared non-sticky `c(tmpdir)`, the spec and data read by path, and denial of the launch (R-8, TR-08.21; the app-substitution window is closed by R-9, round 2); a `.py` run by hand is opened by name and imports from its folder (documented); the launch from the open file is unmeasured on Linux and Windows; F2's erase of `app.py` still waits for `/health` and the banner although the child no longer reads the file; and a disk that keeps no permissions keeping `dash serve`'s copies until the command ends; AGENTS invariants (private root and 0600 writer `TestTheDataFileIsPrivate`, parent watch `TestTheServerDiesWithItsLauncher`, Break ends `dash serve` with r(1) LC-03, and the app starts only from the verified bytes (`TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`)).
- **S10 (P0.5, P0.2):** B4 closed; B15-a closed, B15 partly (axes 3-9, `yaxis(1 2)`); B16's rescale part closed; B22-c closed; REMAINING.md:2451-2466 closed; AUDIT :142 corrected ("common scales" was false before P0.2; drop yrescale from "ignored"), AUDIT-27 closed; ROADMAP: the 100-panel settle time from the P0.2 commit body; six new residuals; AGENTS invariant "by() sharing is decided by `_dash_share_by_scales` …; served notes are decided at build time (`ServerAppBuilder._plan_graph_notes`)".
- **S13 (P0.12a), as ratified 01oct2026 (answer 3):** the app never runs without a token; started by hand with none, it makes its own, writes its link to a 0600 `link.html` in a 0700 folder and prints only the path (section 13 K-1..K-9); when no link file can be written anywhere it prints the link once after a warning and keeps serving (round 2, answer A). Its Notes for the closeout carry eight residuals, among them: the once-printed link in the starter's output and log (K-9); under `bokeh serve` the first session is refused while the key is made; plain `bokeh serve` needs `--allow-websocket-origin 127.0.0.1:<port>` for the 127.0.0.1 link; a SIGKILL leaves the link folder behind. GAPS.md L10's D.8 correction says the app never runs without its key. 15-05 reads the full list on the merged tree.
- **S14 (P0.11), as ratified 01oct2026 (answer 4):** the served `index` carries the saved page's dense ranks in every served source (TR-14.18), so it is NOT a residual and S14 opens no BUGS.md entry; AC-15.1's 4 open entries stand. Residuals: SD5's three follow-ups (rows read only by computed layers, `$dash_max_cells` counting planned rows, the served `.py` holding every row); and a residual candidate measured at `7421d3d`: the served brush reads a line copy's position as a label (not reachable by box or lasso select on a line; not browser-measured).

## User stories

- **US-15.1** As the maintainer, I want one measured record that WP-29 is done — the 21 entries closed test-first, the suites, the certification suite and the gate green on the merged tree, no open S1/S2 — so that the release can be judged from the documents alone.
- **US-15.2** As the next auditor, I want every source id of the 20 P0 items marked in its document with the commit that closed it, or with what is still open, so that nothing WP-29 fixed is re-reported and nothing it left is lost.
- **US-15.3** As the maintainer, I want to approve which GAPS2 gaps WP-29 fully closed and which residuals it hands on before they are written into the audit, so that the audit never claims more than was done.
- **US-15.4** As the next agent working on dash, I want the invariants WP-29 introduced in AGENTS.md, each with its guarding test, so that I neither break them nor rediscover them.
- **US-15.5** As a Stata user reading the help, I want the help files to say one thing about each behaviour WP-29 changed, so that two sections' sentences never contradict each other.
- **US-15.6** As the maintainer, I want the merge command reported and not run, so that `main` moves only by my hand (CLAUDE.md rule 5).

## Business requirements

- **BR-15.1** Every P0 entry stays closed: the allowance is empty, no CHANGELOG marker remains, each of the 21 ids has one closed entry whose Resolution holds `(WP-29, <id>)` and names tests that exist, and a test fails if any of this is undone.
- **BR-15.2** The CHANGELOG records each P0 once in each list `WP29_LISTS` names (26 lines), every line ending `(WP-29, P0.<n>)`, every Results line naming the command, the old value and the new.
- **BR-15.3** Each GAPS2 id a P0 source names is marked Closed in WP-29 (only when every bullet of its Gap is answered), partly closed (naming what is open), or annotated where WP-28 already closed it; each mark names a commit that exists; the audit text is otherwise unchanged, its old Tracked text kept after `was:`.
- **BR-15.4** REMAINING.md, TWOWAY_COVERAGE_AUDIT.md and DROPIN-REMAINING.md carry a tag on every row a P0 source names, stating closed or partly closed and the commit; DROPIN's §4 decisions record what WP-29 decided; the residuals the sections hand on are filed where the maintainer approved.
- **BR-15.5** No GAPS.md sentence is left false by WP-29 (L10's "no auth model", E1's sort remark), and no GAPS.md heading claims a closure WP-29 cannot list.
- **BR-15.6** WP-29 is DONE in ROADMAP.md with the GAPS2 ids it fully closed, a commit per P0 in its traceability table, and a measured block quoting the four runs, the cert wall time before and after, the residuals and the merge command.
- **BR-15.7** AGENTS.md carries "Invariants introduced by WP-29", one paragraph per invariant, each naming a test that collects.
- **BR-15.8** The help files hold no stale claim about a WP-29 behaviour and no contradiction between sections' sentences; any found is fixed by its owner, test first.
- **BR-15.9** `make test`, `make test-dev`, `make cert` and `make gate` each pass once on the final tree, strict, with no skip; the package date agrees with the gate's rule.
- **BR-15.10** The tree is clean of WP-29's work (only the maintainer's own uncommitted planning files and generated blocks remain), every WP-29 commit is on `wp29-p0`, none names an AI tool or vendor or holds `CLAUDE.md`/`.gitignore`, and the merge command is reported, not run.

## Technical requirements

- **TR-15.1 Inventory (15-01, 15-02).** Write Appendix A.1-A.3 to `<scratch>` and run A.1 then A.2 on `wp29-p0`. A.1 writes `<scratch>/wp29-map.tsv` (id, closing sha, every sha whose subject names the id, title, BUGS.md line) and `<scratch>/wp29-residuals.txt` (every `Residual, deferred (WP-29): …` clause), and requires: `WP29_OPEN == {}`; one closed entry per id whose Resolution opens `Fixed <ddmonyyyy> (WP-29, <id>).`; no `"` in a title; at least one found and no dangling test reference (`_references`); exactly one closing commit (pickaxe) that also names the id in its subject; no `<!-- WP-29 ` marker. A.2 checks E2 (a `Regression:` line in the TR-01.10.4 form and an opening failure text in every named commit), E3 (`_meta` stamp on every added or changed fixture JSON), E4 (`ALLOWED` unchanged), E10 (messages and `CLAUDE.md`/`.gitignore`) and K3 (no test file deleted; every base test function present or named by a `Flipped:` line), and writes `<scratch>/wp29-flipped-nodes.txt`.
- **TR-15.2 The closeout test (15-03).** In `test/test_tracking_documents.py`: replace the multi-line empty `WP29_OPEN = {…}` with `WP29_OPEN = {}` and its comment (Appendix B part 1); add `test_no_wp29_entry_remains_open` to `TestWp29Tracking` (Appendix B part 2); extend the module docstring's item 8 (Appendix B part 3). Prove the test bites by three mutations, each reverted (Appendix B part 4).
- **TR-15.3 CHANGELOG (15-04).** Check the 26 WP-29 lines in their lists (awk ranges in 15-04), the 13 Results lines' command/old/new, and remove the blank line between two consecutive WP-29 items of one list (formatting only; section 01's R-02 left them for merging). Move or complete a line, never reword its fact; a missing old value is taken from the closing commit's body.
- **TR-15.4 Ledger (15-05).** Build `<scratch>/wp29-sources.tsv` from Appendix C, one row per source id: P0, source id, document, anchor found on the merged tree, verdict (closed / partly / annotate / not located), commit(s), the text to write (Appendix D forms). Build `<scratch>/wp29-closeout-notes.md` by concatenating, for each `.ultraplan/wp29/section-*.md`, the text from its "Notes for the closeout" heading or bullet to the next `## ` or `### ` heading. Build `<scratch>/wp29-invariants.tsv` (name, sentence, guarding nodes). A GAPS2 id is FULL only when every bullet of its **Gap** text is answered by a WP-29 commit's test (Appendix C gives the plan-time expectation).
- **TR-15.5 GAPS2 and BUGS.md, partly closed (15-07).** Write the partly-closed and annotate lines (Appendix D.2-D.4) and append ` Closes GAPS2 <ID> (WP-29, <ID>).` to the Resolution of the entry that will be named for each FULL id (Appendix D.6). Each Tracked line stays one physical line.
- **TR-15.6 REMAINING, AUDIT, DROPIN, GAPS.md (15-08, 15-09).** Tags and paragraphs of Appendix D.5, D.7, D.8; the AUDIT gains one dated line under "Audit date"; DROPIN's new items continue the numbering of the list the checkpoint chose. Commit S15.2.
- **TR-15.7 DONE (15-10).** Write the FULL Tracked lines (D.1), the heading `— DONE`, the field (D.9), the commit column (no D.10 rewording: R-6 was ratified 01oct2026 and S01 wrote the final text) and the `### Done, measured (<ddmonyyyy>)` skeleton (Appendix E) with `<to be measured in 15-17>` placeholders. Prove the guard bites on a reverted Tracked line. Check with the readers' own functions. Commit S15.3.
- **TR-15.8 AGENTS.md (15-11).** Insert `## Invariants introduced by WP-29` and one paragraph per row of `<scratch>/wp29-invariants.tsv` between the last WP-28 paragraph and `<!-- gitnexus:start -->` (R15-6). Every named node collects. No Markdown link. Commit `AGENTS.md` alone, S15.4.
- **TR-15.9 Help consistency (15-12).** Run the eight `test_help_claims_*.py` files and the eight `test_help_claims_*.cscript` through the driver; check the stale-phrase table of 15-12; route any contradiction to its owner (Boundaries). No S15 commit.
- **TR-15.10 Date (15-13, 15-14).** Compute `newest` exactly as `scripts/run_release_gate.sh:18-31` does. If `newest` > `20260930`, set the six `Version` lines and `dash.pkg`'s two lines to today, run the metadata tests, then `make test` and `make test-dev`, and commit S15.6. Otherwise run `make test` and `make test-dev` with no commit.
- **TR-15.11 Certification and gate (15-15, 15-16).** `python_exec` read first; `{ date +%s; make cert; echo "exit=$?"; date +%s; }` and `make gate; echo "exit=$?"` in the background, one at a time; 67 of 67 scripts, no SKIP; per-block times of `test_wp29_truth.cscript` from Appendix A.3; growth against step 0b's baseline reported.
- **TR-15.12 Record and report (15-17).** Fill the Done block, date CHANGELOG lines 3 and 5 if 15-14 re-dated, run the final checks, commit S15.7, report in the order of 15-17 with the merge command and the words "not run".
- **TR-15.13 Security (rule 1).** Nothing reaches a page. The scripts of Appendix A read the repository and git through `subprocess.run([...])` with argument lists (no `shell=True`), `ast.parse` (never `eval`), and `json.load`; they write only under `<scratch>`. Every Stata run is the console binary in batch: `make cert`/`make gate`/`make test` through their own runners, every one-off do-file and cscript through `scripts/stata_slot.sh`; never the GUI. No secret is written to a log: the served token (S13) never appears in a document S15 edits — the Done block names token tests, never a token.

## Boundaries

- **Do not fix a P0 here.** A red test, a failed cert script, a gate problem, a help contradiction or a missing BUGS.md/CHANGELOG fact is a defect of the section that owns it. Fix it in the main checkout on `wp29-p0` under that section's rules: `gitnexus_impact` on each symbol first; the failing test written and run first, its output saved to `<scratch>/15-fix-<P0>-failure.txt`; the fix; the full suite once; a commit whose subject ends `(WP-29 P0.<n>)` and whose body opens with that failure text and a `Regression:` line. Then return to the step that found it. Never weaken or delete a test, never read a skip as a pass.
- **Do not reword** a section's CHANGELOG fact, BUGS.md entry, help sentence or test assertion; only placement, completeness, the formatting of R-02's blank lines, the `(WP-29, <gid>)` appends and the release date are this section's.
- **GAPS2.md:** only Tracked lines change, each keeping its old text after `was:`; nothing is written before the maintainer approved the ledger (15-06). Never list A10, C1, C5, C10, C13, E4, G15, H2 or an id already Closed in WP-28 in WP-29's field (R15-3, R15-4).
- **GAPS.md:** body paragraphs only (R15-5); no heading changes.
- **ROADMAP.md:** only WP-29's section changes; WP-01..WP-28 and `## Traceability matrix` are untouched; no line inside WP-29 starts `# ` or `## ` other than its heading; neither `Gaps closed` nor `## Traceability matrix` is written.
- **Files S15 never stages:** `CLAUDE.md`, `.gitignore`, `.gitnexus/`, anything under `.ultraplan/` except `.ultraplan/handoff/DROPIN-REMAINING.md`, `*.html`, `*.log`, scratch files, and AGENTS.md's generated block refresh (R15-6). Stage by name, never `git add -A` or `git add .`.
- **Do not** run `git checkout main`, `git merge` other than `git merge --no-edit main` (which must print `Already up to date.`), `git push`, `git rebase`, `make hooks`, or `git commit --amend` on a landed commit; never commit to `main` (rule 5); never rewrite history to repair an E2 exception (report it).
- **Do not** add a `.cscript`, edit `test/run_all_cscripts.do` or the hygiene pins (section 01 alone did), touch the served copy lists or `test/function_test_map.py`, or edit `ALLOWED`/`_MUST_WARN` in `test/test_mode_parity.py`.
- **Do not** start a second full run while one executes, or relaunch one to check on it (rule 11): read its log.
- **Do not** edit `.ultraplan/wp29/PLAN.md` (R15-8) or write the invariants into `CLAUDE.md`.

## Stata truth

None added. This section runs Stata only:
- through `make test` (which reads `c(python_exec)` with `scripts/stata_python_exec.sh`), `make cert` (`scripts/run_cert_suite.sh`) and `make gate` (`scripts/run_release_gate.sh`), each of which runs the console binary of CLAUDE.md rule 10 in batch from a `mktemp -d` directory with its own `STATATMP`, one at a time (batch 4 runs alone, so no slot is contended);
- through `scripts/stata_slot.sh <scratch> <file>.do` with `dash_nobrowser=1` for: the `python_exec` check and, if needed, its restore (15-01, 15-15); the eight help-claims cscripts through the two-line driver (15-12); one block of `test/test_wp29_truth.cscript` with `WP29_ONLY=S<NN>` if a block must be rerun.

No fixture is written; nothing needs `git add -f`.

## TDD test stubs

**The one new test** (written by 15-03; a guard, passing on a correct tree):
- Test: `test/test_tracking_documents.py::TestWp29Tracking::test_no_wp29_entry_remains_open` — `WP29_OPEN == {}`; no `<!-- WP-29 ` marker in CHANGELOG.md; `_wp29_closure_problems(set(), set(markers), entries) == []`; no open entry whose Resolution matches `_WP29_OPEN_FORM`. Its failing-first proof is three reverted mutations (Appendix B part 4), each recorded in `<scratch>/15-03-mutations.txt` and quoted in S15.1's body:
  - `"P0.1": "<title>"` put back into `WP29_OPEN` → fails with `WP29_OPEN is {} after WP-29's closeout; it holds ['P0.1']` (and `test_every_allowed_title_is_an_open_entry` fails with `P0.1: … is closed; delete its WP29_OPEN key`);
  - P0.1's entry set back to `- [ ]` with its section-01 open Resolution → fails with `P0.1 is closed and no closed BUGS.md entry's Resolution holds (WP-29, P0.1)` and `… is open in the WP-29 form`;
  - `<!-- WP-29 P0.7 -->` re-added under `### Results that change` → fails with `markers left in CHANGELOG.md: ['P0.7']`.

**Documentary failing-first proof** (15-10): with WP-29 DONE and one FULL id's Tracked line temporarily reverted to its `was:` text, `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it` fails with `WP-29 is DONE and lists <ID>, whose Tracked line does not say Closed in WP-29`; restored, it passes.

**Tests that become non-vacuous for WP-29 at DONE** (section 01's and WP-28's, unchanged): `TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it`, `::test_every_closed_gaps2_entry_is_listed_by_its_package`, `::test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`, `::test_every_gaps2_id_a_package_declares_has_a_heading`; `TestWp29Tracking::test_a_closed_p0_has_no_marker_and_a_resolution` and `::test_each_p0_sits_in_its_changelog_lists` (all 21 closed).

**Pinned tests to flip:** none. **Flips that must already exist:** every node `<scratch>/wp29-flipped-nodes.txt` lists (from the commits' `Flipped:` lines) must collect (15-02).

## Test plan

| What | How | Fixture / input | Both modes? |
|---|---|---|---|
| 21 entries closed, one closing commit each, tests named exist, no marker | Appendix A.1 (15-01) | BUGS.md, CHANGELOG.md, git | n/a |
| E2, E3, E4, E10, K3 | Appendix A.2 (15-02); `pytest --collect-only` over the flipped nodes | git, fixtures, `test_mode_parity.py` | n/a |
| The allowance stays empty; entries stay closed | `TestWp29Tracking::test_no_wp29_entry_remains_open` + three mutations (15-03) | BUGS.md, CHANGELOG.md | n/a |
| 26 CHANGELOG lines in their lists | `TestWp29Tracking` (all) + awk range counts (15-04) | CHANGELOG.md | n/a |
| Classification approved before writing | checkpoint 15-06 | `<scratch>/wp29-sources.tsv` | n/a |
| Tracked lines parse as intended | `_parse_gaps2` / `_parse_roadmap_gaps2` one-liners (15-07, 15-10); `TestGaps2AndRoadmapAgree` (all) | GAPS2.md, ROADMAP.md, BUGS.md, git | n/a |
| GAPS.md stays well formed | `TestEveryGapHasAStatus`, `TestGapsAndRoadmapAgree` (15-09) | GAPS.md | n/a |
| Invariants name tests that exist | `pytest --collect-only -q <nodes>` (15-11); `TestTodoAndPlanAreRetired` | AGENTS.md | n/a |
| Help files consistent | the eight `test_help_claims_*.py`; the eight `test_help_claims_*.cscript` through the driver; the stale-phrase table (15-12) | dash.sthlp, dash_setup.sthlp | yes (the scripts build saved and served pages) |
| Dates agree with the gate's rule | `test_pkg_metadata.py`, `test_help_claims_1.py::TestTheHeader`, the `newest` computation (15-13, 15-14) | seven date lines | n/a |
| Full suite, strict, no skip, both interpreters | `make test`, `make test-dev` (15-14) | whole suite | yes: the parity corpus runs inside |
| Certification suite, no skip; block times; growth | `make cert` timed; Appendix A.3 (15-15) | 67 registered scripts | yes |
| Release gate from an installed package | `make gate` (15-16) | `examples/`, the scheme files | yes (examples include server mode) |
| Clean tree, merge reported | `git status --porcelain` with the filter of AC-15.11 (15-17) | git | n/a |

**Acceptance criteria.**

- **AC-15.1 (E1)** `python3 <scratch>/wp29_inventory.py <R> 7421d3d <scratch>` prints `ids mapped: 21 of 21; residual clauses: <r>; problems: 0` and exits 0; `grep -c '^- \[ \] Title:' BUGS.md` prints 4 (the S3 entries open at 7421d3d; WP-29 opens no other entry, S14's served-index residual having been struck on 01oct2026) and `TestNoOpenEntryBlocksARelease` passes; `WP29_OPEN = {}` is one line.
- **AC-15.2 (E2, E3, E4, E10)** `python3 <scratch>/wp29_gates.py <R> 7421d3d <scratch>/wp29-map.tsv <scratch>` prints `problems: 0`, or every PROBLEM line it prints is an E2 exception listed in the S15.7 report (E2 cannot be repaired without rewriting history).
- **AC-15.3** `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes with no skip after each of S15.1-S15.4; the three mutation records and the reverted-line record exist.
- **AC-15.4 (E7)** `grep -c '<!-- WP-29 ' CHANGELOG.md` prints 0; `grep -cE '\(WP-29, P0\.[0-9]{1,2}[ab]?\)$' CHANGELOG.md` prints 26; per list (awk ranges of 15-04) 13, 5, 4, 1 and 3.
- **AC-15.5** 15-10's reader check prints `True True <ids> {'done': True, 'gaps': {}} 76`, where `<ids>` are exactly the FULL ids approved at 15-06; 15-07's check printed `partly` equal to the approved PARTLY list; E1, G1, G3 and G16 still start `Closed in WP-28,`.
- **AC-15.6 (E8)** `grep -c '^## WP-29 .* — DONE$' ROADMAP.md` prints 1; `grep -c '## Traceability matrix' ROADMAP.md` prints 1; `awk '/^## WP-29 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'Gaps closed'` prints 0.
- **AC-15.7** `grep -c '^## Invariants introduced by WP-29$' AGENTS.md` prints 1, the heading's line number is below the last WP-28 paragraph and above `<!-- gitnexus:start -->`, the paragraph count equals the rows of `<scratch>/wp29-invariants.tsv`, every node it names collects.
- **AC-15.8** The eight help-claims pytest files pass; each help-claims cscript log holds its pass line; every stale phrase of 15-12 meets its expectation or was fixed by its owner.
- **AC-15.9 (E9)** `make test` and `make test-dev` logs each end with a pass count, `0 failed` or no `failed`, no `skipped`, no strict-mode refusal; `make cert` says `67 of 67 registered scripts passed`, `verdict: PASS`, `exit=0`, `[ SKIP]` count 0 in its log; `make gate` says `verdict: PASS`, `exit=0`; the cert wall time and growth are recorded.
- **AC-15.10 (E3, E4, E5, E6)** inside 15-14's and 15-15's runs: `test_wp29_truth.cscript` printed `test_wp29_truth: ALL CHECKS PASSED` with every block's end line; `test_mode_parity.py`, both served-name guards and the security tests named in Appendix E pass.
- **AC-15.11 (E10, E12)** `git status --porcelain | grep -v -E '^(\?\?|.M|M.) (CLAUDE\.md|\.gitignore|\.gitnexus/|phases/|scripts/__pycache__/)|^\?\? \.ultraplan/|^ M AGENTS\.md$'` prints nothing (and ` M AGENTS.md` only when its diff lies inside the generated block), so only untracked (`??`) `.ultraplan/` paths pass; `git status --porcelain .ultraplan/wp29` prints nothing (the plan is tracked since step 0a: a ` M .ultraplan/wp29/…` or `?? .ultraplan/wp29/…` line is an uncommitted plan amendment, reported to the orchestrator to commit alone on `wp29-p0` as index.md's "Plan files" delta says; S15 never stages it); `git worktree list` shows one line; the report states `git checkout main && git merge --no-ff wp29-p0` and that it was not run.
- **AC-15.12 (E11)** `gitnexus_detect_changes()` was run before each S15 commit and its result recorded in `<scratch>/15-detect-<k>.txt`; the report lists the sections' G6 records as "attested by the sections, not re-verified".

## Tasks

Commit boundary: **one commit per step**, made by 15-04 (S15.1), 15-09 (S15.2), 15-10 (S15.3), 15-11 (S15.4), 15-14 (S15.6, only if 15-13 found the date must move) and 15-17 (S15.7); subjects end `(WP-29 S15.<k>)` (Appendix F). S15.5 commits nothing of its own; a defect it routes is committed under its owner's `(WP-29 P0.<n>)`.
- **`<R>`** is `/Users/billy/Desktop/Programs/StataPrograms/d/dash` (the main checkout, on `wp29-p0`). Every shell command starts `cd <R> &&` because the cwd resets between calls.
- **`<scratch>`** is the orchestrator's session scratch directory for this section (for example `<session scratchpad>/wp29/s15-run`), created with `mkdir -p`; **`<scratch0>`** is step 0's.
- **`<base>`** is `7421d3d`.
- **Before every commit:** `git merge --no-edit main` (must print `Already up to date.`; if main moved, stop and report), `gitnexus_detect_changes()` recorded in `<scratch>/15-detect-<k>.txt`, one full run `python3 -m pytest test/ -q > <scratch>/15-full-<k>.log 2>&1` in the background (prefixed `FULL_SUITE_RERUN=1` from the third launch of the session), read on exit, then stage by name, write the message to a file, `grep -Eic 'claude|anthropic'` it (expect 0), `git commit -F`, and grep the committed message again (expect 0). No co-author trailer (CLAUDE.md rule 6 overrides any harness default).
- **Every long run** (`python3 -m pytest test/ -q`, `make test`, `make test-dev`, `make cert`, `make gate`) is started once with the Bash tool's background mode and output redirected, waited on, then read from its log; copy each quoted log to `.ultraplan/handoff/wp29-<name>.log` (R15-12).

<task type="auto" id="15-01">
  <name>Inventory the merged branch and its entries</name>
  <files>none</files>
  <action><![CDATA[
1. `cd <R> && git rev-parse --abbrev-ref HEAD` must print `wp29-p0`; `git worktree list` must show one line (the main checkout); `git log --oneline <base>..HEAD` is saved to `<scratch>/wp29-log.txt` and `git rev-parse main` to `<scratch>/15-main-sha.txt`. If a worktree remains, stop and ask the orchestrator to remove it.
2. `git status --porcelain` may list only ` M CLAUDE.md`, ` M .gitignore`, `?? .gitnexus/`, untracked `?? .ultraplan/…` paths (never a modified tracked one), `phases/`, `scripts/__pycache__/`, and ` M AGENTS.md` whose `git diff AGENTS.md` lies wholly between `<!-- gitnexus:start -->` and `<!-- gitnexus:end -->`. `git status --porcelain .ultraplan/wp29` must print nothing: the plan is tracked since step 0a, so a ` M .ultraplan/wp29/…` or `?? .ultraplan/wp29/…` line is an uncommitted plan amendment; report it to the orchestrator, which commits it alone on `wp29-p0` (index.md "Plan files" delta) before S15 goes on; S15 never stages it. Anything else: stop and report.
3. Write Appendix A.1, A.2 and A.3 verbatim to `<scratch>/wp29_inventory.py`, `<scratch>/wp29_gates.py` and `<scratch>/wp29_block_times.py` (a Python writer or a quoted here-document; never retype). Run `python3 <scratch>/wp29_inventory.py <R> <base> <scratch> > <scratch>/15-01-inventory.txt; echo "exit=$?" >> <scratch>/15-01-inventory.txt`.
4. Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0 -p no:cacheprovider` and append its last line to the same file.
5. Python check: write `<scratch>/pyexec/pyexec_check.do` holding `adopath ++ "<R>/"` and ``display "PYEXEC=[`c(python_exec)']"``; run `cd <R> && dash_nobrowser=1 scripts/stata_slot.sh <scratch>/pyexec <scratch>/pyexec/pyexec_check.do`; `grep '^PYEXEC=' <scratch>/pyexec/pyexec_check.log` must print `PYEXEC=[/opt/anaconda3/bin/python3]`. If it prints `PYEXEC=[]`, write `<scratch>/pyexec/pyexec_fix.do` holding `set python_exec /opt/anaconda3/bin/python3, permanently`, run it the same way, and check again.
6. Baseline: look for `<scratch0>/wp29-cert-baseline.log`, then `<R>/.ultraplan/handoff/wp29-cert-baseline.log`. Its first and last lines must be epoch seconds and it must hold `registered scripts passed`. Copy it to `<R>/.ultraplan/handoff/wp29-cert-baseline.log` if it is not there. If neither exists, record `baseline not measured` in `<scratch>/15-01-inventory.txt` for 15-15 (do not check out an old tree to measure it).
7. GitNexus: `gitnexus_list_repos()`; if `dash` is absent or stale, run `cd <R> && npx gitnexus analyze` (main checkout only), then repeat step 2's AGENTS.md check. If any problem line was printed in step 3, the owning section (the id's section in index.md "P0 coverage") fixes it under Boundaries before 15-02. No commit.
  ]]></action>
  <verify><![CDATA[`tail -2 <scratch>/15-01-inventory.txt` shows `ids mapped: 21 of 21; residual clauses: <r>; problems: 0` then `exit=0`, and the pytest line reports 0 failed; `wc -l < <scratch>/wp29-map.tsv` prints 21; `wc -l < <scratch>/wp29-residuals.txt` equals `<r>`; `grep -c '^PYEXEC=\[/opt/anaconda3/bin/python3\]' <scratch>/pyexec/pyexec_check.log` prints 1; `git worktree list | wc -l` prints 1.]]></verify>
  <done>Every P0 id had one closed entry naming existing tests and one closing commit that names it, the allowance and the markers were gone, the residual clauses were collected, Stata's Python was confirmed, and the cert baseline was located or recorded as missing.</done>
</task>

<task type="auto" id="15-02">
  <name>Check the package gates E2 to E10</name>
  <files>none</files>
  <action><![CDATA[
Run `cd <R> && python3 <scratch>/wp29_gates.py <R> <base> <scratch>/wp29-map.tsv <scratch> > <scratch>/15-02-gates.txt; echo "exit=$?" >> <scratch>/15-02-gates.txt`. Then, if `<scratch>/wp29-flipped-nodes.txt` is not empty, run `python3 -m pytest --collect-only -q -n0 -p no:cacheprovider $(cat <scratch>/wp29-flipped-nodes.txt) > <scratch>/15-02-collect.txt 2>&1` and require no `ERROR` and no `not found`. Count `git log --format=%B <base>..HEAD | grep -c '^Flipped: '` and `git diff --stat <base>..HEAD -- test/fixtures | tail -1` into `<scratch>/15-02-gates.txt` for the Done block. A PROBLEM line of kind E3, E4, E10 or K3 is a defect: the owning section fixes it under Boundaries (an E10 match in a landed commit is reported to the maintainer at once, since only a history rewrite, which the maintainer must decide, can remove it). A PROBLEM of kind E2 is recorded as an exception for the S15.7 report; history is not rewritten. No commit.
  ]]></action>
  <verify><![CDATA[`tail -2 <scratch>/15-02-gates.txt` shows `problems: 0` (or only `E2:` PROBLEM lines, each copied to `<scratch>/15-e2-exceptions.txt`) and the `exit=` line; `grep -c 'ERROR\|not found' <scratch>/15-02-collect.txt` prints 0 when that file exists; the Flipped count and the fixtures stat line are in `<scratch>/15-02-gates.txt`.]]></verify>
  <done>The fix commits carried their failure text and Regression lines (or each exception was recorded), every changed fixture carried its provenance stamp, the parity allowance was unchanged, no message or commit held a forbidden name or file, no base test vanished unflipped, and every flipped node collected.</done>
</task>

<task type="auto" id="15-03">
  <name>Add the closeout test and empty the allowance</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
1. GitNexus (CLAUDE.md): `gitnexus_impact({target: "TestWp29Tracking", direction: "upstream", repo: "dash"})` and `gitnexus_impact({target: "WP29_OPEN", direction: "upstream", repo: "dash"})`; record risk and callers in `<scratch>/15-03-impact.txt` (expected LOW: test-module names read only by this module's tests). Report HIGH or CRITICAL to the maintainer before editing.
2. In `<R>/test/test_tracking_documents.py`: replace the whole `WP29_OPEN = {` … `}` assignment (empty after the sections deleted their keys) and the comment block above it with Appendix B part 1; append Appendix B part 2 (the method) as the last method of `class TestWp29Tracking`, after `test_the_wp29_problem_readers`; insert Appendix B part 3 into the module docstring directly after item 8's last line.
3. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` (all pass).
4. The three mutations of Appendix B part 4, one at a time, each followed by `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k "Wp29Tracking" 2>&1 | grep -E '^(FAILED|E   )' >> <scratch>/15-03-mutations.txt` with a header line `== mutation <k>: <what>` before each, then reverted (`git checkout -- BUGS.md CHANGELOG.md`; the test file's mutation by re-editing). After the last, `git status --porcelain -- BUGS.md CHANGELOG.md` must be empty. No commit (15-04 commits).
  ]]></action>
  <verify><![CDATA[`grep -c '^WP29_OPEN = {}$' test/test_tracking_documents.py` prints 1; `python3 -m pytest "test/test_tracking_documents.py::TestWp29Tracking::test_no_wp29_entry_remains_open" -q -n0 -p no:cacheprovider` passes; `grep -c '^== mutation ' <scratch>/15-03-mutations.txt` prints 3 and the file holds `WP29_OPEN is {} after WP-29's closeout`, `no closed BUGS.md entry's Resolution holds (WP-29, P0.1)` and `markers left in CHANGELOG.md`; `git status --porcelain -- BUGS.md CHANGELOG.md` is empty.]]></verify>
  <done>The allowance was a one-line empty dict, a guard test held every P0 entry closed with no marker left, and three recorded mutations showed it failing for each way the closure could be undone.</done>
</task>

<task type="auto" id="15-04">
  <name>Reconcile the CHANGELOG and commit S15.1</name>
  <files>CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
1. In `<R>/CHANGELOG.md`, check the 26 WP-29 lines: each list holds the ids `WP29_LISTS` assigns (Results: P0.1-P0.9, P0.15, P0.16, P0.18, P0.20; Security: P0.11, P0.12a, P0.12b, P0.13, P0.14; Changed behaviour: P0.1, P0.5, P0.6, P0.12a; Requirements: P0.19; Fixed in WP-29: P0.10, P0.13, P0.17), each line ends `(WP-29, P0.<n>)`, and each of the 13 Results lines names the command, the value dash drew before (it must match the failure text that opens the closing commit's body: `git log -1 --format=%b <sha from wp29-map.tsv>`) and the value it now draws. Complete a missing value from that body; move a misplaced line; never reword a fact.
2. Formatting only: where two WP-29 items of one list are separated by a blank line (section 01's R-02), remove that blank line, so each list's WP-29 items are consecutive as WP-28's are; keep the blank line before the next `### ` heading and around the `**WP-29 (drop-in P0, 30sep2026)**` group line.
3. Run `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider`.
4. The pre-commit routine of the Tasks preamble (merge, detect_changes to `<scratch>/15-detect-1.txt`, full run to `<scratch>/15-full-1.log`). Stage exactly `CHANGELOG.md test/test_tracking_documents.py`; commit with Appendix F's S15.1 message, its body quoting `<scratch>/15-03-mutations.txt` as three `Regression:` lines.
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-29 ' CHANGELOG.md` prints 0; `grep -cE '\(WP-29, P0\.[0-9]{1,2}[ab]?\)$' CHANGELOG.md` prints 26; piping each range into `grep -cE '\(WP-29, P0\.[0-9]{1,2}[ab]?\)$'`: `awk '/^### Results that change/,/^### Security/' CHANGELOG.md` → 13, `awk '/^### Security/,/^### New/' CHANGELOG.md` → 5, `awk '/^### Changed behaviour/,/^### Removed/' CHANGELOG.md` → 4, `awk '/^### Requirements/,/^### Fixed in WP-29/' CHANGELOG.md` → 1, `awk '/^### Fixed in WP-29/,/^### Fixed in WP-28/' CHANGELOG.md` → 3; `tail -1 <scratch>/15-full-1.log` reports 0 failed; `git log -1 --format=%s` ends `(WP-29 S15.1)`; `git show --name-only --format= HEAD | sort` lists exactly `CHANGELOG.md` and `test/test_tracking_documents.py`; `git log -1 --format=%B | grep -c '^Regression: '` prints 3; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The CHANGELOG held each P0 once in each of its lists with its before and after values and no marker, the allowance was closed for good behind a guard test, and S15.1 was committed on a green tree.</done>
</task>

<task type="auto" id="15-05">
  <name>Build the source ledger and edit drafts</name>
  <files>none</files>
  <action><![CDATA[
1. `<scratch>/wp29-closeout-notes.md`: for each `<R>/.ultraplan/wp29/section-NN-*.md` (01-14), append `## <file>` and the text from its "Notes for the closeout" heading or bullet up to the next heading of the same or higher level (read the whole file first; sections 04, 09, 11, 12, 13 and 14 were written after this plan). Also append each section's closed BUGS.md entry Resolution (`Residual, deferred (WP-29): …` clauses are already in `<scratch>/wp29-residuals.txt`).
2. `<scratch>/wp29-sources.tsv`: one row per row of Appendix C, columns `P0, source id, document, anchor on the merged tree, verdict, commit(s), text to write`. Find each anchor by its text (`grep -n`), not by Appendix C's 7421d3d number. Decide each GAPS2 heading's verdict by Appendix C's rule: FULL only when every bullet of its **Gap** text is answered by a test in the commits of `<scratch>/wp29-map.tsv` (name the test per bullet in a seventh column), PARTLY otherwise (name what is open), ANNOTATE for ids already `Closed in WP-28`. Where a section's notes and Appendix C disagree, the notes (written with the code in hand) win; write the disagreement into the row.
3. Draft every text to write, in the exact forms of Appendix D, into `<scratch>/wp29-tracking-edits.md`, grouped by file (GAPS2.md Tracked lines with their full old text after `was:`; BUGS.md appends; REMAINING.md tags; AUDIT tags and the dated line; DROPIN P0 annotations, §4 decision annotations, notes on P1/P2 items, and new items; GAPS.md paragraphs; ROADMAP field, column and rewording; the C4 line in both forms of D.4).
4. `<scratch>/wp29-invariants.tsv`: Appendix D.11's eight mandatory invariants plus every "AGENTS.md invariant" bullet in `<scratch>/wp29-closeout-notes.md`, a bullet restating one of the eight merged into it; columns `name, sentence, guarding nodes`; check each node with `python3 -m pytest --collect-only -q -n0 -p no:cacheprovider <node>`.
5. `<scratch>/wp29-residual-filings.md`: every residual the notes hand on "to file", with the DROPIN list proposed for it (P1 if common twoway usage, P2 otherwise) and its measured text. No commit.
  ]]></action>
  <verify><![CDATA[`awk -F'\t' 'NF<6' <scratch>/wp29-sources.tsv | wc -l` prints 0; every source id of the 21 entries' Descriptions appears in column 2 (`for id in $(grep -o 'Sources: [^.]*' BUGS.md | tr ',' '\n' | sed 's/Sources: //;s/ //g'); do grep -qF "$id" <scratch>/wp29-sources.tsv || echo MISSING $id; done` prints nothing); every FULL row names a test per Gap bullet; `<scratch>/wp29-invariants.tsv` has at least 8 rows and every node collected.]]></verify>
  <done>Every source id of every P0 had a located anchor (or was recorded as not located), a verdict with its evidence, and its exact text drafted; the invariants and the residual filings were listed, ready for approval.</done>
</task>

<task type="checkpoint" id="15-06">
  <name>Approve the classification and the filings</name>
  <files>none</files>
  <action><![CDATA[
Present to the maintainer, in one message, before any tracking document is edited:
1. The GAPS2 classification: the FULL ids (with, per Gap bullet, the test that answers it), the PARTLY ids (with what is open), the ANNOTATE ids (E1, G1, G3, G16 as applicable), and the ids Appendix C expected FULL that 15-05 found PARTLY, or the reverse.
2. C4's line, in both forms of Appendix D.4, with the recommendation (partly closed: the cue is done, the redraw stays out by decision M3).
3. Every residual of `<scratch>/wp29-residuals.txt` and `<scratch>/wp29-residual-filings.md`, with the DROPIN list proposed for each, and the question whether any should instead be a BUGS.md entry (R15-10).
4. Nothing about ROADMAP's requirements: R-6 and the 01oct2026 answers were ratified at plan time and S01 wrote BR-29.6/7/9/10/11 and AC-29.6 in their final form (R15-8). Instead, list the divergences and residuals the ratification introduced (S05's kept date axis; S08's inputs read by path in a shared non-sticky `c(tmpdir)`, its launch from the open file unmeasured on Linux and Windows, and a `.py` run by hand opened by name; S13's `bokeh serve` first-session refusal, websocket-origin flag and K-9's once-printed link) with the DROPIN list proposed for each residual, as in item 3.
5. The REM ids not located (expected: REM-08-05-M3).
6. The count of invariants for AGENTS.md.
Ask for a yes, or for the changes wanted; a residual sent back to its section is fixed there under Boundaries before 15-07.
  ]]></action>
  <verify><![CDATA[The maintainer approved the classification, C4's form, the residual filings, the rewording and the invariant list as shown, or named the changes, which were applied to the drafts in `<scratch>`; nothing was written to a tracking document.]]></verify>
  <done>The maintainer approved what WP-29 would claim it closed, what it would hand on and where, before any of it was written.</done>
</task>

<task type="auto" id="15-07">
  <name>Mark partly closed GAPS2 gaps and entries</name>
  <files>GAPS2.md, BUGS.md</files>
  <action><![CDATA[
1. In `<R>/GAPS2.md`, from the approved drafts, rewrite the `- **Tracked:**` line of every PARTLY id (Appendix D.2), of C4 (the approved form of D.4), and of every ANNOTATE id (D.3: insert the WP-29 clause inside the residual it closes, before `; was:`; the `Closed in WP-28, … commit <sha>` prefix is untouched). Locate each with `grep -n '^### <ID>\. ' GAPS2.md` and the first `- **Tracked:**` after it. One physical line per Tracked line; nothing else in GAPS2.md changes. Do NOT write any `Closed in WP-29` line here (R15-1).
2. In `<R>/BUGS.md`, for each FULL id, append ` Closes GAPS2 <ID> (WP-29, <ID>).` to the end of the Resolution line of the entry its D.1 line will name (Appendix D.6); for I3, the P0.12a entry; for F2 and F4, the P0.13 entry. Change nothing else in any entry.
3. Check with the readers: `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; g,d=t._parse_gaps2(open('GAPS2.md',encoding='utf-8').read()); print('dupes',d); print('closed_wp29',sorted(k for k,v in g.items() if v['closed'] and v['closed'][0]=='WP-29')); print('closed_wp28',sum(1 for v in g.values() if v['closed'] and v['closed'][0]=='WP-28')); print('deferred',sorted(k for k,v in g.items() if v['deferred'])); print('partly',sorted(k for k,v in g.items() if (v['tracked'] or '').startswith('Partly closed in WP-29 (')))"` and `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. No commit (15-09 commits).
  ]]></action>
  <verify><![CDATA[The one-liner prints `dupes []`, `closed_wp29 []`, `closed_wp28 22`, `deferred` as approved for C4 (`['C4']` or `[]`), and `partly` equal to the approved PARTLY list (C4 included when its partly form was approved); `git diff --stat -- GAPS2.md` shows as many insertions as deletions, equal to the number of lines rewritten; `grep -o '(WP-29, [A-NX][0-9]\{1,2\})' BUGS.md | sort -u | wc -l` equals the number of FULL ids (F2 and F4 share P0.13's line, so count matches, not lines); the tracking tests pass.]]></verify>
  <done>Every partly closed gap said what WP-29 closed and what stays open, WP-28's residuals that WP-29 closed said so inside their own lines, and each entry about to be named for a fully closed gap carried that gap's id, with every reader still green.</done>
</task>

<task type="auto" id="15-08">
  <name>Tag the audit, backlog and task list</name>
  <files>REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, .ultraplan/handoff/DROPIN-REMAINING.md</files>
  <action><![CDATA[
From the approved drafts (Appendix D.5, D.7):
1. `<R>/REMAINING.md`: append the tag to the last line of each REM item `<scratch>/wp29-sources.tsv` locates (a bullet's last wrapped line; a table row's last cell, before its final `|`).
2. `<R>/TWOWAY_COVERAGE_AUDIT.md`: add the dated line of D.5 directly under the `Audit date:` line (as its own paragraph), and the tag (with its correction text) on every row and summary item the ledger lists; change no other text.
3. `<R>/.ultraplan/handoff/DROPIN-REMAINING.md`: append the D.7 annotation to the last line of each P0 item 1-20 (item 13's on its `Effort M. Sources:` line; item 12 names both P0.12a and P0.12b); annotate the §4 decision bullets on P0.1, P0.7, P0.9, P0.17 and P0.12; add the approved notes to P1/P2 items (P1.15, P1.16, P1.22, P1.23 and any the notes name); append the approved new items at the end of their lists, numbered on from the list's last number.
4. Check: no line of the three files starts with `**RESOLVED` or `**Closed` because of an edit; `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0 -p no:cacheprovider` passes (the link walk reads TWOWAY_COVERAGE_AUDIT.md). No commit (15-09 commits).
  ]]></action>
  <verify><![CDATA[`grep -c '\[WP-29 P0\.' REMAINING.md` equals the REMAINING rows of `<scratch>/wp29-sources.tsv` whose verdict is not `not located`; `grep -c '\[WP-29 P0\.' TWOWAY_COVERAGE_AUDIT.md` equals the AUDIT rows; `grep -c 'Closed in WP-29: BUGS.md' .ultraplan/handoff/DROPIN-REMAINING.md` prints 20 (one per P0 item; item 12 names two entries); `grep -c 'Decided for WP-29' .ultraplan/handoff/DROPIN-REMAINING.md` prints 5; `git diff --numstat -- REMAINING.md TWOWAY_COVERAGE_AUDIT.md .ultraplan/handoff/DROPIN-REMAINING.md` shows only the approved lines; the two pytest files pass.]]></verify>
  <done>Every REMAINING, audit and task-list row a P0 named said what WP-29 closed and by which commit, the task list recorded the decisions WP-29 took and carried the residuals the maintainer approved, and the audit's own text stood as written beside the tags.</done>
</task>

<task type="auto" id="15-09">
  <name>Correct GAPS.md and commit S15.2</name>
  <files>GAPS.md</files>
  <action><![CDATA[
1. In `<R>/GAPS.md`, append the approved D.8 paragraphs: L10's after its last body paragraph (before the `---` that follows it), E1's after its body paragraph ending "sort(varlist) is still named.", and any other the ledger lists. Headings are not edited (R15-5).
2. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` (`TestEveryGapHasAStatus` and `TestGapsAndRoadmapAgree` must pass).
3. The pre-commit routine (`<scratch>/15-detect-2.txt`, `<scratch>/15-full-2.log`). Stage exactly `GAPS2.md BUGS.md REMAINING.md TWOWAY_COVERAGE_AUDIT.md .ultraplan/handoff/DROPIN-REMAINING.md GAPS.md`; commit with Appendix F's S15.2 message.
  ]]></action>
  <verify><![CDATA[`grep -c '^\*\*Since WP-29 (P0\.' GAPS.md` equals the paragraphs approved; `git diff HEAD~1 -- GAPS.md | grep '^[-+]#'` prints nothing (no heading changed); `tail -1 <scratch>/15-full-2.log` reports 0 failed; `git log -1 --format=%s` ends `(WP-29 S15.2)`; `git show --name-only --format= HEAD | sort` lists exactly the six staged paths; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>GAPS.md no longer said the served app had no credential or that sort(varlist) was unhonoured on the joining types, and the partly closed gaps, WP-28 residual notes, entry appends and row tags were committed as S15.2 on a green tree.</done>
</task>

<task type="auto" id="15-10">
  <name>Close the GAPS2 gaps and mark WP-29 done</name>
  <files>GAPS2.md, ROADMAP.md</files>
  <action><![CDATA[
1. `<R>/GAPS2.md`: write the approved D.1 line for every FULL id (title from `<scratch>/wp29-map.tsv` column 4, commit from column 2; F2 takes the P0.13 F2 commit, F4 the F4 commit; I3 names the P0.12a entry and commit with the P0.12b entry and commit as `; with …`), each one physical line ending `; was: <old text>`.
2. `<R>/ROADMAP.md`, inside WP-29 only: append ` — DONE` (U+2014) to `## WP-29 · Close the drop-in P0 gaps`; replace `(filled at closeout)` in the header line with the D.9 field; add the `Commit` column to `#### P0 traceability` (header, rule and 21 rows; P0.13 `F2 <sha>, F4 <sha>`); apply no D.10 (R15-8); insert Appendix E's block after the traceability table and before WP-29's closing `---`, with `<to be measured in 15-17>` where Appendix E says.
3. Prove the guard bites: temporarily replace one FULL id's Tracked line with its `was:` text (uncommitted), run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k Gaps2 2>&1 | grep -E '^(FAILED|E   )' > <scratch>/15-10-guard.txt`, restore the line by re-editing (not `git checkout`, which would drop step 1).
4. Check: `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; r=open('ROADMAP.md',encoding='utf-8').read(); g,_=t._parse_gaps2(open('GAPS2.md',encoding='utf-8').read()); w=t._parse_roadmap_gaps2(r)['WP-29']; c=sorted(k for k,v in g.items() if v['closed'] and v['closed'][0]=='WP-29'); print(w['done'], sorted(w['gaps2'])==c, c, t._parse_roadmap(r)['WP-29'], len(t._matrix_gaps(r)))"` and `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
5. The pre-commit routine (`<scratch>/15-detect-3.txt`, `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/15-full-3.log 2>&1`). Stage exactly `GAPS2.md ROADMAP.md`; commit with Appendix F's S15.3 message, its body opening with the guard's recorded failure as a `Regression:` line.
  ]]></action>
  <verify><![CDATA[The check prints `True True <the approved FULL ids> {'done': True, 'gaps': {}} 76`; `grep -c '^## WP-29 .* — DONE$' ROADMAP.md` prints 1; `grep -c '## Traceability matrix' ROADMAP.md` prints 1; `awk '/^## WP-29 /,/^## Traceability matrix/' ROADMAP.md` piped into `grep -c 'Gaps closed'` prints 0 and into `grep -c '^# \|^## '` prints 2; `<scratch>/15-10-guard.txt` holds `WP-29 is DONE and lists`; `git status --porcelain -- GAPS2.md ROADMAP.md` is empty after the commit; `git log -1 --format=%B | grep -c '^Regression: '` prints 1; `tail -1 <scratch>/15-full-3.log` reports 0 failed; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>WP-29 was headed DONE with the GAPS2 gaps it fully closed, each named by a Tracked line, an entry and a commit that exist, a commit per P0 in its table and a measured block awaiting its numbers; the guard was seen to fail on a stale line and pass on the real ones; S15.3 was committed.</done>
</task>

<task type="auto" id="15-11">
  <name>Record the WP-29 invariants in AGENTS.md</name>
  <files>AGENTS.md</files>
  <action><![CDATA[
1. If `git diff --quiet -- AGENTS.md` fails, check that every changed line lies between `<!-- gitnexus:start -->` and `<!-- gitnexus:end -->` (else stop and report), copy the working file to `<scratch>/AGENTS.working.md`, and run `git checkout -- AGENTS.md` (R15-6).
2. Insert, after the last WP-28 invariant paragraph (the one starting `**The fixture \`_meta\` stamp.**`) and its blank line, and before `<!-- gitnexus:start -->`: the heading `## Invariants introduced by WP-29`, a blank line, then one paragraph per row of the approved `<scratch>/wp29-invariants.tsv` in the D.11 form, each followed by a blank line. No Markdown link (no `](`), no AI reference, no `PLAN.md`/`TODO.md` link.
3. Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0 -p no:cacheprovider`, then `python3 -m pytest --collect-only -q -n0 -p no:cacheprovider <every test/…py::… node the new section names>` (each collects at least one test, no error).
4. The pre-commit routine (`<scratch>/15-detect-4.txt`, `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/15-full-4.log 2>&1`). Stage `AGENTS.md` alone; commit with Appendix F's S15.4 message.
5. If step 1 saved `<scratch>/AGENTS.working.md`, put its generated block (from `<!-- gitnexus:start -->` to `<!-- gitnexus:end -->`) back in place of the committed block, so the tool's refresh stays uncommitted as before; `git diff AGENTS.md` must then show changes inside the block only.
  ]]></action>
  <verify><![CDATA[`grep -n '^## Invariants introduced by WP-2[89]$\|^<!-- gitnexus:start -->' AGENTS.md` prints WP-28's heading, then WP-29's, then the marker, in that order; `awk '/^## Invariants introduced by WP-29$/,/^<!-- gitnexus:start -->/' AGENTS.md | grep -c '^\*\*'` equals the rows of `<scratch>/wp29-invariants.tsv`; the same range piped into `grep -c '](\|<PLAN\.md\|<TODO\.md'` prints 0; the collect run reports no error; `git show --name-only --format= HEAD` lists only `AGENTS.md`; `git log -1 --format=%s` ends `(WP-29 S15.4)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>AGENTS.md carried the invariants WP-29 introduced, each with a guarding test that collects, placed before the generated block, committed alone, with the tool's own refresh left as it was.</done>
</task>

<task type="auto" id="15-12">
  <name>Check the help files for consistency</name>
  <files>none</files>
  <action><![CDATA[
1. `python3 -m pytest test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_help_claims_6.py test/test_help_claims_7.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider > <scratch>/15-12-hc.log 2>&1`.
2. For each `test/test_help_claims_<k>.cscript` (k = 1..8), one after another: `printf 'adopath ++ "%s/"\ncd "%s/test"\ndo "%s/test/%s"\n' "<R>" "<R>" "<R>" test_help_claims_<k>.cscript > <scratch>/hc<k>/run_hc<k>.do` (after `mkdir -p <scratch>/hc<k>`), then `cd <R> && dash_nobrowser=1 scripts/stata_slot.sh <scratch>/hc<k> <scratch>/hc<k>/run_hc<k>.do`. Take the script's final pass string from `grep -n 'PASSED' test/test_help_claims_<k>.cscript | tail -1` and require `grep -cxF '<that string as displayed>' <scratch>/hc<k>/run_hc<k>.log` ≥ 1 (Evidence lists the strings at 7421d3d). A run that ends `r(222);` is the python_exec drop: restore it (15-01 step 5) and rerun; a skip is not a pass.
3. The stale-phrase table: for each row, `grep -n -F '<phrase>' dash.sthlp dash_setup.sthlp`, read each hit's whole paragraph, and record pass or the contradiction in `<scratch>/15-12-phrases.txt`:
   - `Ctrl+C` (5 at 7421d3d): every remaining hit's sentence also names Break (P0.13, S08);
   - `only this machine`, `single-user`, `localhost`: no sentence says loopback alone keeps others out; tokenized URLs use 127.0.0.1 (P0.12a, S13);
   - `Connection order` paragraph: data order unless `sort`/`sort(varlist)`; no "always … in the order of x" (P0.1, S02);
   - `bootstrap`: 0 hits about lpolyci (P0.9, S11); `pwidth`: no longer "named in the note" (P0.9);
   - `approximat` in dash.sthlp's lpoly Default bandwidth paragraph: gone (P0.7, S11);
   - `does not redraw`: the sentence names the stale cue (P0.17, S12);
   - `milliseconds`: no hit says a computed layer or KPI of a date runs in ms (P0.8, P0.20, S05);
   - `shadowed` (:183, G1): if a test on the merged tree pins `hover(top)`/`hover(y)` as not shadowed (`grep -rn 'hover(top)\|hover(y)\|"hover": *"top"' test/`), the sentence is false and is routed to S06's P0.10; if no test pins it, record "unmeasured by WP-29" for the report and change nothing;
   - dash_setup.sthlp: `venv` ≥ 1 and `externally` or `PEP 668` ≥ 1; `--break-system-packages` 0 in both files (P0.19, S09);
   - dash.sthlp's embedding paragraph discloses that the page holds only rows a layer, a recomputed KPI, a filter or csv reads (P0.11, S14); the preview paragraph matches R-6 (P0.14, S08);
   - `r(603)`, `not private`, `refus`: no sentence says dash refuses a location or folder because it is not private; the private-files paragraph says such a location proceeds with one note and names the anti-hijack refusals (r(7102)) as anti-hijack (P0.12b, S08 R-8, ratified 01oct2026);
   - `DASH_SERVE_TOKEN`, `bokeh serve`: no sentence says the app refuses to start or fails closed without the variable; the help says an app started without a key makes its own and prints its link file's path, says that when no link file can be written anywhere the link is printed once after a warning and the server keeps serving, and names `--allow-websocket-origin` for plain `bokeh serve`; no sentence says the key is never printed without that exception, or that a link that cannot be written stops the server (P0.12a, S13 K-1..K-9, round 2 answer A);
   - `hands the text to Python`, `imports modules from the folder`: the needles S08's round-2 test pins (`test_it_says_dash_serve_runs_the_text_it_checked`: the first in the tempfiles section of TR-08.11, the second in the "Running the generated .py file independently" passage); the help says `dash serve` runs only the app text it wrote and checked, and that a `.py` run by hand with `python` or `bokeh serve` is opened by its name and imports from its folder (P0.12b, S08 R-9 and TR-08.11, round 2 answer B);
   - `date axis`: the divergence sentence for a first lfit/qfit/lfitci/qfitci/kdensity/lpoly/lpolyci over a date is present, and no sentence says dash labels such an axis with numbers (P0.8, S05 D05-1 struck).
4. Read the two help files' paragraphs each section changed (from `git diff <base>..HEAD -- dash.sthlp dash_setup.sthlp`) for two sentences that disagree. A failure or contradiction is routed under Boundaries to the section whose P0 the sentence describes (test first, in that P0's `test_help_claims_<k>.py`), committed `(WP-29 P0.<n>)`; then rerun steps 1-3 for the touched file. No S15 commit.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/15-12-hc.log` reports 0 failed and no skipped; each of the eight `<scratch>/hc<k>/run_hc<k>.log` holds its pass line; `grep -c 'CONTRADICTION\|FAIL' <scratch>/15-12-phrases.txt` prints 0, or each listed item has a landed `(WP-29 P0.<n>)` fix commit named beside it.]]></verify>
  <done>The help files said one thing about each behaviour WP-29 changed, every help-claims test passed in both suites, and any stale or contradicting sentence was fixed by its owner, test first.</done>
</task>

<task type="auto" id="15-13">
  <name>Decide the release date and date sources</name>
  <files>dash.ado, dash_setup.ado, dash_parse.mata</files>
  <action><![CDATA[
1. Compute the gate's date exactly as `scripts/run_release_gate.sh:18-31` does: `shipped="$(sed -n 's/^f  *\([^ ]*\) *$/\1/p' dash.pkg)"`; if `git status --porcelain -- dash.pkg stata.toc $shipped` is non-empty, `newest=$(date +%Y%m%d)`, else `newest=$(git log -1 --format=%cd --date=format:%Y%m%d -- dash.pkg stata.toc $shipped)`. Record it in `<scratch>/15-13-date.txt`.
2. If `newest` ≤ `20260930`: record "no re-dating needed" and skip the rest of this task and the dating part of 15-14 (R15-7).
3. Else set `*! Version: 0.1.0  <ddmonyyyy>` for today (lower-case month, as `30sep2026`) in `dash.ado:29`, `dash_setup.ado:16` and the line `grep -n '\*! Version:' dash_parse.mata` reports. Version stays 0.1.0. Do not run the metadata tests between this task and 15-14 (they hold all seven lines equal); if the two tasks straddle midnight, redo this one. No commit.
  ]]></action>
  <verify><![CDATA[`cat <scratch>/15-13-date.txt` holds an 8-digit date and the decision; when re-dating, `grep -n '^\*! Version: 0.1.0  ' dash.ado dash_setup.ado dash_parse.mata` prints three lines with today's `ddmonyyyy` and `git status --porcelain` lists those three files as modified (and nothing else beyond AC-15.11's filter).]]></verify>
  <done>The release date was decided by the gate's own rule, and, where it had to move, the three shipped sources carried today's date awaiting the package and help lines.</done>
</task>

<task type="auto" id="15-14">
  <name>Date the package and run both pytest targets</name>
  <files>dash.pkg, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
1. If 15-13 re-dated: set `{* *! version 0.1.0  <ddmonyyyy>}{...}` in `dash.sthlp:2` and `dash_setup.sthlp:2`, `d Version: 0.1.0  <ddmonyyyy>` and `d Distribution-Date: <yyyymmdd>` in `dash.pkg` (24, 25), for the same day; run `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q -n0 -p no:cacheprovider`.
2. `git merge --no-edit main` (expect `Already up to date.`). Read Stata's Python: `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh` must print `/opt/anaconda3/bin/python3`.
3. `make test > <scratch>/wp29-make-test.log 2>&1; echo "exit=$?" >> <scratch>/wp29-make-test.log` in the background; when it has exited, read its tail. Then `make test-dev` to `<scratch>/wp29-make-test-dev.log` the same way. Never start the second while the first runs. A red or skipped test belongs to its section (Boundaries); after its fix, rerun only that file, then the make target that failed.
4. Copy both logs to `<R>/.ultraplan/handoff/`.
5. If 15-13 re-dated: `gitnexus_detect_changes()` to `<scratch>/15-detect-6.txt`; stage exactly the six dated files; commit with Appendix F's S15.6 message, quoting both logs' last lines and interpreter versions.
  ]]></action>
  <verify><![CDATA[`tail -2 <scratch>/wp29-make-test.log` and `tail -2 <scratch>/wp29-make-test-dev.log` each show a pass count with no `failed` and no `skipped` and `exit=0`, and each log's first line names its interpreter (`pytest under Stata's Python: /opt/anaconda3/bin/python3`, `pytest under the development interpreter: python3`); when re-dated, `grep -n 'Distribution-Date' dash.pkg` shows today, `git show --stat --format= HEAD | tail -1` reports 6 files changed, `git log -1 --format=%s` ends `(WP-29 S15.6)`, and `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The package carried one date in all seven lines that the gate accepts, and the full suite passed strict with no skip under Stata's Python and under the development interpreter on that tree.</done>
</task>

<task type="auto" id="15-15">
  <name>Run the certification suite and time it</name>
  <files>none</files>
  <action><![CDATA[
1. Read `python_exec` (15-01 step 5); restore it if empty.
2. `{ date +%s; make cert; echo "exit=$?"; date +%s; } > <scratch>/wp29-make-cert.log 2>&1` in the background; no other Stata runs meanwhile; read the log on exit. It must say `certification suite: 67 of 67 registered scripts passed`, `verdict: PASS`, `exit=0`; the wall time is the last line minus the first.
3. From the line `certification log: <path>`: `grep -c '^\[ PASS\]' <path>` is 67, `grep -c '^\[ SKIP\]\|^\[ FAIL\]' <path>` is 0. If any script SKIPped, read `python_exec` again before believing it; restore and rerun (`FULL_SUITE_RERUN=1` if the hook asks).
4. `python3 <scratch>/wp29_block_times.py <path> > <scratch>/wp29-block-times.txt` (exit 0); its block count equals `grep -o '^\* ==== S[0-9][0-9] ' test/test_wp29_truth.cscript | sort -u | wc -l`; the region of `test_wp29_truth.cscript` holds `test_wp29_truth: ALL CHECKS PASSED` and no `SKIP: Python not available.` output line.
5. Growth: wall time minus the baseline's (`<R>/.ultraplan/handoff/wp29-cert-baseline.log`, last line minus first). If the baseline was not measured, record the after time alone. If the growth exceeds 300 s, list the five slowest blocks with their owning sections for the report and the Done block, and ask the maintainer whether to fold them (a fold changes tests, so it is done by the owning section, never here).
6. A FAIL belongs to its section (Boundaries); after its fix, rerun that one script through the driver (`WP29_ONLY=S<NN>` for one block), then this task. Copy the cert log and `<path>` to `<R>/.ultraplan/handoff/wp29-make-cert.log` and `wp29-run_all_cscripts.log`. No commit.
  ]]></action>
  <verify><![CDATA[`grep -E 'registered scripts passed|verdict|exit=' <scratch>/wp29-make-cert.log` shows `67 of 67`, `verdict: PASS`, `exit=0`; `head -1` and `tail -1` of the log are epoch seconds; the certification log exists with 67 `[ PASS]` and 0 `[ SKIP]`/`[ FAIL]`; `tail -1 <scratch>/wp29-block-times.txt` shows `unclosed: none` and the block count matches the script's.]]></verify>
  <done>The certification suite passed every registered script with no skip on a Stata whose Python was verified, the WP-29 truth script passed every block, and the wall time, its growth over the pre-WP-29 baseline and the per-block times were recorded.</done>
</task>

<task type="auto" id="15-16">
  <name>Run the release gate from an installed package</name>
  <files>none</files>
  <action><![CDATA[
Run `make gate > <scratch>/wp29-make-gate.log 2>&1; echo "exit=$?" >> <scratch>/wp29-make-gate.log` in the background and wait for it to exit: it copies what `dash.pkg` ships to a scratch source, net-installs it into a scratch PLUS, runs every `examples/*.do` and one page per shipped scheme from the install, checks adoupdate, and judges the log with `scripts/release_verdict.py`. Read the log: `verdict: PASS`, `exit=0`, no problem line. A `Distribution-Date … is older than the newest change to a shipped file` problem means a shipped file changed after 15-14: redo 15-13 and 15-14, then this task. An example printing an undeclared diagnostic, a scheme page falling back or an install failing belongs to the section whose change caused it (Boundaries); after its fix rerun this task, and 15-15 too if a shipped file changed. Copy the log to `<R>/.ultraplan/handoff/wp29-make-gate.log`. No commit.
  ]]></action>
  <verify><![CDATA[`tail -4 <scratch>/wp29-make-gate.log` shows `release gate: <e> of <e> examples and <p> of <p> scheme pages clean`, `verdict: PASS`, `release gate log: <path>` naming a file that exists, and `exit=0`.]]></verify>
  <done>The release gate passed from a net-installed copy of exactly what dash.pkg ships: every example and every scheme page clean, adoupdate as expected, the Distribution-Date current.</done>
</task>

<task type="auto" id="15-17">
  <name>Record the measurements and report the merge</name>
  <files>ROADMAP.md, CHANGELOG.md</files>
  <action><![CDATA[
1. In WP-29's `### Done, measured` block of `<R>/ROADMAP.md`, replace every `<to be measured in 15-17>` with the numbers from the logs (Appendix E names each source), set the heading's date to today, and keep every line free of a leading `# `/`## ` and of the text `Gaps closed`.
2. If 15-14 re-dated: set `CHANGELOG.md:3` to `## 0.1.0, <ddmonyyyy> (release candidate)` and the `now <yyyymmdd>` on line 5 to the Distribution-Date.
3. Final checks: `python3 <scratch>/wp29_inventory.py <R> <base> <scratch>` (problems 0); `python3 -m pytest test/test_tracking_documents.py test/test_pkg_metadata.py test/test_packaging.py -q -n0 -p no:cacheprovider`; AC-15.11's `git status` filter; `git worktree list`.
4. The pre-commit routine (`<scratch>/15-detect-7.txt`, `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/15-full-7.log 2>&1`). Stage exactly `ROADMAP.md` and, if changed, `CHANGELOG.md`; commit with Appendix F's S15.7 message.
5. Report, in this order: the four make verdicts with log paths; the cert wall times and growth; the slowest blocks; the open-entry count and grades; the 21 closed entries with their commits; the GAPS2 FULL and PARTLY ids with what is open; the residuals filed and where; the E2 exceptions (if any) and the sections' G6 records as "attested by the sections, not re-verified" (R15-11); the PLAN.md sentences R15-8 leaves superseded (BR-29.11, E6) and the platforms not measured (Windows, Linux, Stata before 19); the `wp29-s<NN>` branches still present (`git branch --list 'wp29-s*'`, left for the maintainer); and the merge command `git checkout main && git merge --no-ff wp29-p0`, with the words "reported, not run". Do not run it.
  ]]></action>
  <verify><![CDATA[`grep -c 'to be measured' ROADMAP.md` prints 0; `awk '/^## WP-29 /,/^## Traceability matrix/' ROADMAP.md` piped into `grep -c 'git checkout main && git merge --no-ff wp29-p0'` prints 1 and into `grep -c 'wall time'` prints at least 1; the targeted pytest run passes with no skip; AC-15.11's filtered `git status --porcelain` prints nothing; `git log -1 --format=%s` ends `(WP-29 S15.7)`; `git log --format=%B <base>..HEAD | grep -Eic 'claude|anthropic'` prints 0; `git rev-parse --abbrev-ref HEAD` prints `wp29-p0` and `git rev-parse main` prints the sha saved in `<scratch>/15-main-sha.txt` (main did not move).]]></verify>
  <done>WP-29's measured block quoted the four green runs by number and log, the cert wall times and growth, the closures and the residuals; every WP-29 commit was on wp29-p0 with a clean message; and the merge command had been reported and not run.</done>
</task>

## Section completion criteria

- Five or six commits on `wp29-p0` (15-04, 15-09, 15-10, 15-11, 15-14 if re-dated, 15-17), each subject ending `(WP-29 S15.<k>)`, each made after one green full run, none naming an AI tool or vendor, none holding `CLAUDE.md`, `.gitignore`, `.gitnexus/` or a plan file; `git checkout main && git merge --no-ff wp29-p0` reported, not run.
- The maintainer approved the classification, C4's form, the residual filings, the rewording and the invariants (15-06) before 15-07 wrote any of it.
- `WP29_OPEN = {}` behind `test_no_wp29_entry_remains_open`, with three recorded mutations; 21 closed entries naming existing tests; 0 markers; 26 WP-29 CHANGELOG lines in their lists.
- GAPS2: every FULL id `Closed in WP-29, …` and listed by WP-29's field; every PARTLY id `Partly closed in WP-29 (…); open: …`; E1/G1/G3/G16 still `Closed in WP-28` with their WP-29 clauses; `TestGaps2AndRoadmapAgree` green with WP-29 DONE.
- REMAINING, AUDIT and DROPIN rows tagged; GAPS.md L10 and E1 corrected in body paragraphs.
- AGENTS.md's WP-29 invariants above the generated block, every named node collecting.
- `make test`, `make test-dev`, `make cert` (67 of 67) and `make gate` each green once on the final tree, logs copied to `.ultraplan/handoff/wp29-*.log`, wall time and growth recorded.

## Notes

- **Order matters twice.** (1) R15-1: the `Closed in WP-29` lines and `— DONE` are one commit; S15.2 writes only what both tests already accept. (2) The date rule: 15-14 commits the date before 15-16; any later commit to a shipped file (a routed fix) on a later day makes the gate fail until 15-13/15-14 are redone.
- **Where a red test belongs.** Find the owner from the test file, the cscript case prefix (JO, UL, ET, FX, DU, KD, HX, QF, CQV, PF, LC, PEP, AX, BSC, LW, LB, SCU, EW, TOK, ER; W29 is section 01's) or the `test_wp29_truth.cscript` block header `* ==== S<NN> P0.<n>: … ====`. Fix under Boundaries. If the fix changes an entry's title, the GAPS2 line naming it changes in the same commit (the guard fails otherwise).
- **A SKIP in 0-1 s is the `python_exec` drop**, not a pass. Many concurrent console sessions can rewrite `~/.stata19/console/stata19.rc` without its Python lines; restore with `set python_exec /opt/anaconda3/bin/python3, permanently` from a do-file run through `scripts/stata_slot.sh` (never the GUI; `.claude/hooks/block-stata-gui.sh` blocks it anyway).
- **`make` and the hook.** `make test`/`make cert` are not counted by the launch hook; the conftest lock still refuses a second whole-suite pytest (`a full test-suite run is already in progress`). Start each target in the background, wait for its exit, read its log; never poll by relaunching.
- **The cert baseline** is step 0b's; it should be copied to `.ultraplan/handoff/wp29-cert-baseline.log` (ignored) when it is taken, since the session scratch does not survive. WP-28's numbers (575 s at 65 scripts, 699 s at 66 in ROADMAP WP-28's block) are context, not WP-29's baseline.
- **E1, G16 and the other WP-28 ids.** A WP-29 commit may close a WP-28 residual completely (E1's KPI spreads by P0.20) or partly (G16's hover-only export by P0.10, while "an x or y variable not named in hover() keeps its number in the tooltip" stays open). The `Closed in WP-28, …` prefix never changes (R15-3).
- **C4.** It is `Deferred (WP-28)` today. Its Gap names both the missing redraw and the missing cue; M3 decided the cue only. The recommended form (D.4 a) makes it partly closed; the alternative (D.4 b) keeps the WP-28 deferral with the WP-29 clause inside it. Either passes the readers; the maintainer chooses at 15-06.
- **Demo pages.** WP-28's closeout regenerated nine untracked demo pages; PLAN.md §7 gives WP-29 no such step, so this section does not. The maintainer can run `python3 scripts/regen_dashboards.py`, `scripts/regen_comprehensive.py` and `scripts/regen_bootstrap_examples.py` from the root; the pages stay untracked (`.gitignore` holds `*.html`).
- **Shared files and the merge rules.** R1: no script, runner block or hygiene pin changes here. R2: no copy list or map. R3: CHANGELOG lines are only placed, completed or de-blanked; BUGS.md entries only gain the `(WP-29, <gid>)` sentence; `test_tracking_documents.py` gains the closeout test. R5: no fixture. R6: `ALLOWED` and `_MUST_WARN` untouched (E4 checks it). R8: `gitnexus_impact` before 15-03's edits and `gitnexus_detect_changes()` before every commit. Nothing is landed with `patch -p1` here: batch 4 runs on the branch.
- **Commit-body line forms** (section 01 TR-01.10.4): `Regression: test/<file>.py::<Class>::<test> -- failed on <mutation> with <text>` for this section's proofs; a routed fix uses `-- failed at <sha> with <text>`, `Flipped: …`, `BUGS.md: "<title>"` as its owner's section prescribes.

## Appendix A: closeout scripts (written to `<scratch>` verbatim by 15-01)

### A.1 `wp29_inventory.py`

~~~~python
"""WP-29 closeout inventory (S15 task 15-01).  Read-only on the repository.

Usage:  python3 wp29_inventory.py <repo> <base-sha> <out-dir>
Writes <out-dir>/wp29-map.tsv (one row per P0 id) and
<out-dir>/wp29-residuals.txt, prints one PROBLEM line per defect and
exits 1 if there is any."""
import os
import re
import subprocess
import sys

repo, base, out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(repo, "test"))
import test_tracking_documents as t  # noqa: E402

IDS = ("P0.1 P0.2 P0.3 P0.4 P0.5 P0.6 P0.7 P0.8 P0.9 P0.10 P0.11 P0.12a "
       "P0.12b P0.13 P0.14 P0.15 P0.16 P0.17 P0.18 P0.19 P0.20").split()
WP29_ALL = getattr(t, "WP29_ALL", tuple(IDS))
problems = []
if tuple(WP29_ALL) != tuple(IDS):
    problems.append("WP29_ALL is %r" % (WP29_ALL,))
if getattr(t, "WP29_OPEN", None) not in ({},):
    problems.append("WP29_OPEN still holds %s"
                    % sorted(getattr(t, "WP29_OPEN", {"(absent)": 1})))


def git(*args):
    r = subprocess.run(["git", "-C", repo] + list(args),
                       capture_output=True, text=True)
    return r.stdout


entries, parse_problems = t._parse_bugs(t._read("BUGS.md"))
problems += ["BUGS.md parse: %s" % p for p in parse_problems]
files = t._test_files()
py = {f: t._python_names(os.path.join(t._HERE, f))
      for f in files if f.endswith(".py")}
cases = set()
for f in files:
    if f.endswith((".cscript", ".do")):
        with open(os.path.join(t._HERE, f), encoding="utf-8",
                  errors="replace") as fh:
            cases |= t._displayed_cases(fh.read())
on_disk = {"files": files, "py": py, "cases": cases,
           "classes": set().union(*(set(c) for c, _f in py.values()))}

subjects = [ln.split("\t", 1) for ln in
            git("log", "--format=%h\t%s", base + "..HEAD").splitlines()]
fixed = re.compile(r"^  - Resolution: Fixed \d{2}[a-z]{3}\d{4} "
                   r"\(WP-29, (P0\.\d{1,2}[ab]?)\)\. \S")
rows, residuals = [], []
for pid in IDS:
    tag = "(WP-29, %s)" % pid
    mine = [e for e in entries if e["closed"]
            and fixed.match(e["fields"].get("Resolution", ""))
            and fixed.match(e["fields"]["Resolution"]).group(1) == pid]
    if len(mine) != 1:
        problems.append("%s: %d closed entries open their Resolution with "
                        "'Fixed <date> %s.'" % (pid, len(mine), tag))
        continue
    e = mine[0]
    if '"' in e["title"]:
        problems.append("%s: the title holds a double quote" % pid)
    found, dangling = t._references(e["text"], on_disk)
    if not found or dangling:
        problems.append("%s: tests found %s, dangling %s"
                        % (pid, found, dangling))
    closing = git("log", "--format=%h", "-S- [x] Title: " + e["title"],
                  base + "..HEAD", "--", "BUGS.md").split()
    if len(closing) != 1:
        problems.append("%s: %d commits close the entry: %s"
                        % (pid, len(closing), closing))
    pat = re.compile(r"\(WP-29 (?:P0\.\S+, )*%s(?:,? [^)]*)?\)$"
                     % re.escape(pid))
    named = [h for h, s in subjects if pat.search(s)]
    if not named:
        problems.append("%s: no commit subject ends (WP-29 %s)" % (pid, pid))
    if closing and closing[0] not in named:
        problems.append("%s: the closing commit %s does not name %s in its "
                        "subject" % (pid, closing[0], pid))
    rows.append("\t".join([pid, (closing or ["?"])[0], ",".join(named),
                           e["title"], str(e["line"])]))
    m = re.search(r"Residual, deferred \(WP-29\): (.*)$",
                  e["fields"]["Resolution"])
    if m:
        residuals.append("\t".join([pid, e["title"], m.group(1)]))
markers = re.findall(r"<!-- WP-29 [^>]*-->", t._read("CHANGELOG.md"))
if markers:
    problems.append("CHANGELOG.md still holds %d WP-29 marker(s): %s"
                    % (len(markers), markers))
with open(os.path.join(out, "wp29-map.tsv"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(rows) + ("\n" if rows else ""))
with open(os.path.join(out, "wp29-residuals.txt"), "w",
          encoding="utf-8") as fh:
    fh.write("\n".join(residuals) + ("\n" if residuals else ""))
for p in problems:
    print("PROBLEM", p)
print("ids mapped: %d of %d; residual clauses: %d; problems: %d"
      % (len(rows), len(IDS), len(residuals), len(problems)))
sys.exit(1 if problems else 0)
~~~~

### A.2 `wp29_gates.py`

~~~~python
"""WP-29 closeout: package-level gates E2, E3 (fixtures), E4, E10 and K3
(S15 task 15-02).  Read-only on the repository.

Usage:  python3 wp29_gates.py <repo> <base-sha> <map.tsv> <out-dir>
Prints one PROBLEM line per failed check, writes <out-dir>/wp29-flipped-
nodes.txt (the pytest nodes the Flipped: lines name) and exits 1 on any
problem."""
import ast
import json
import os
import re
import subprocess
import sys

repo, base, map_tsv, out = sys.argv[1:5]


def git(*args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True).stdout


problems = []
rows = [ln.split("\t") for ln in open(map_tsv, encoding="utf-8")
        if ln.strip()]
# E2: each closing commit (and every commit whose subject names a P0 id)
# carries a Regression: line in the TR-01.10.4 form, after its failure text.
reg = re.compile(r"^Regression: test/\S+ -- failed (?:at [0-9a-f]{7,40}|on "
                 r"[^\n]+?) with \S", re.M)
shas = set()
for pid, closing, named, _title, _line in rows:
    shas.add(closing)
    shas.update(s for s in named.split(",") if s)
for sha in sorted(shas):
    body = git("log", "-1", "--format=%b", sha)
    if not reg.search(body):
        problems.append("E2: %s %s has no 'Regression: test/... -- failed "
                        "at <sha> with <text>' line"
                        % (sha, git("log", "-1", "--format=%s", sha).strip()))
    first = body.strip().split("\n\n", 1)[0] if body.strip() else ""
    if not re.search(r"fail|error|assert", first, re.I):
        problems.append("E2: %s's body does not open with its saved "
                        "failure text" % sha)
# E3: every fixture WP-29 added or changed carries the D12 _meta stamp.
for ln in git("diff", "--name-status", base + "..HEAD", "--",
              "test/fixtures").splitlines():
    status, path = ln.split("\t", 1)
    if status[0] in "AM" and path.endswith(".json"):
        try:
            meta = json.load(open(os.path.join(repo, path),
                                  encoding="utf-8")).get("_meta", {})
        except (ValueError, AttributeError) as exc:
            problems.append("E3: %s does not load: %s" % (path, exc))
            continue
        miss = [k for k in ("stata_version", "born_date", "dash_commit",
                            "extracted") if k not in meta]
        if miss:
            problems.append("E3: %s's _meta lacks %s" % (path, miss))


# E4: test_mode_parity.ALLOWED is the value it had at the base.
def allowed(src):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and \
                getattr(n.targets[0], "id", "") == "ALLOWED":
            return ast.dump(n.value)


if allowed(git("show", base + ":test/test_mode_parity.py")) != allowed(
        open(os.path.join(repo, "test/test_mode_parity.py"),
             encoding="utf-8").read()):
    problems.append("E4: test_mode_parity.ALLOWED changed since " + base)
# E10: no message names an AI tool or vendor; CLAUDE.md and .gitignore are
# in no WP-29 commit.
msgs = git("log", "--format=%H%n%B", base + "..HEAD")
if re.search(r"claude|anthropic", msgs, re.I):
    problems.append("E10: a commit message since %s matches "
                    "claude|anthropic" % base)
touched = set(git("log", "--name-only", "--format=", base + "..HEAD")
              .split())
for f in ("CLAUDE.md", ".gitignore"):
    if f in touched:
        problems.append("E10: %s is in a WP-29 commit" % f)
# K3: no test file deleted; every test function at the base still exists
# or is named by a Flipped: line (a renamed flip).
deleted = git("diff", "--diff-filter=D", "--name-only", base + "..HEAD",
              "--", "test").split()
if deleted:
    problems.append("K3: test files deleted: %s" % deleted)
defs = re.compile(r"^(test/[^:]+\.py):\d+:\s*def (test_\w+)", re.M)


def names(rev):
    args = ["grep", "-n", "-E", r"^[[:space:]]*def test_[A-Za-z0-9_]+"]
    args += [rev] if rev else []
    txt = git(*(args + ["--", "test/*.py"]))
    if rev:
        txt = re.sub(r"^%s:" % re.escape(rev), "", txt, flags=re.M)
    return set(defs.findall(txt))


flipped_text = "\n".join(ln for ln in msgs.splitlines()
                         if ln.startswith("Flipped: "))
gone = sorted("%s::%s" % fn for fn in names(base) - names(None)
              if fn[1] not in flipped_text)
if gone:
    problems.append("K3: %d base tests are gone and no Flipped: line names "
                    "them: %s" % (len(gone), gone[:20]))
nodes = sorted(set(re.findall(r"^Flipped: (test/test_\w+\.py::[\w:]+)",
                              flipped_text, re.M)))
with open(os.path.join(out, "wp29-flipped-nodes.txt"), "w") as fh:
    fh.write("\n".join(nodes) + ("\n" if nodes else ""))
for p in problems:
    print("PROBLEM", p)
print("commits checked: %d; Flipped: lines: %d (%d pytest nodes); "
      "test defs at base: %d, now: %d; problems: %d"
      % (len(shas), flipped_text.count("Flipped: "), len(nodes),
         len(names(base)), len(names(None)), len(problems)))
sys.exit(1 if problems else 0)
~~~~

### A.3 `wp29_block_times.py`

~~~~python
"""Per-block wall times of one truth script inside a certification log.

Usage:  python3 wp29_block_times.py <run_all_cscripts.log> [script]
script defaults to test_wp29_truth.cscript.  Prints one line per block,
"S<NN> <seconds>", slowest first, then the block count and the total; exits
1 if a block has a start and no end, or the script's region is absent."""
import re
import sys

log = open(sys.argv[1], encoding="utf-8", errors="replace").read()
script = sys.argv[2] if len(sys.argv) > 2 else "test_wp29_truth.cscript"
m = re.search(r"^\[ RUN \] %s$(.*?)^\[ (?:PASS|FAIL|SKIP)\] %s"
              % (re.escape(script), re.escape(script)), log, re.M | re.S)
if not m:
    sys.exit("no region for %s in %s" % (script, sys.argv[1]))
start, times, bad = {}, {}, []
for blk, kind, hh, mm, ss in re.findall(
        r"^(S\d{2}) (start|end) (\d{2}):(\d{2}):(\d{2})\s*$", m.group(1), re.M):
    sec = int(hh) * 3600 + int(mm) * 60 + int(ss)
    if kind == "start":
        start[blk] = sec
    elif blk in start:
        times[blk] = times.get(blk, 0) + (sec - start.pop(blk)) % 86400
for blk in start:
    bad.append(blk)
for blk, sec in sorted(times.items(), key=lambda kv: -kv[1]):
    print(blk, sec)
print("blocks: %d; total: %d s; unclosed: %s" % (len(times),
      sum(times.values()), bad or "none"))
sys.exit(1 if bad else 0)
~~~~

## Appendix B: `test/test_tracking_documents.py` (task 15-03)

**Part 1** replaces the whole `WP29_OPEN = {` … `}` assignment and the `#:` comment above it:

~~~~python
#: WP-29 (.ultraplan/wp29/index.md, decision A4): the BUGS.md entries the
#: tracking foundation (S01) opened, one per P0 entry, while they were open.
#: Each fix section closed its entry in place and deleted its key here; the
#: closeout (S15.1) left the allowance empty, and
#: TestWp29Tracking::test_no_wp29_entry_remains_open keeps it so.
WP29_OPEN = {}
~~~~

**Part 2** is the last method of `class TestWp29Tracking`:

~~~~python
    def test_no_wp29_entry_remains_open(self, bugs):
        # WP-29's closeout (S15.1): every P0 entry is closed, the allowance
        # is empty and no marker is left, so the release guard exempts
        # nothing and each id's (WP-29, <id>) sits in a closed entry.
        # Reopening an entry, putting a key back or re-adding a marker
        # fails here.
        entries, _p = bugs
        assert WP29_OPEN == {}, (
            "WP29_OPEN is {} after WP-29's closeout; it holds %s"
            % sorted(WP29_OPEN))
        markers = _wp29_markers(_read("CHANGELOG.md"))
        assert not markers, (
            "markers left in CHANGELOG.md: %s" % markers)
        bad = _wp29_closure_problems(set(), set(markers), entries)
        bad += ["%r is open in the WP-29 form" % e["title"]
                for e in entries if not e["closed"]
                and _WP29_OPEN_FORM.match(e["fields"].get("Resolution", ""))]
        assert not bad, "\n".join(bad)
~~~~

**Part 3** is appended to item 8 of the module docstring (after its last line):

~~~~text
   WP-29's closeout left WP29_OPEN empty; test_no_wp29_entry_remains_open
   keeps every P0 entry closed with no marker left.
~~~~

**Part 4, the three mutations** (each made, run, recorded and reverted in turn by 15-03):

1. Put `"P0.1": "<P0.1's title from wp29-map.tsv>",` back inside `WP29_OPEN = {}` (as `WP29_OPEN = {"P0.1": "…"}`). Expected E lines include `WP29_OPEN is {} after WP-29's closeout; it holds ['P0.1']`. Revert by re-editing to `WP29_OPEN = {}`.
2. In BUGS.md, change P0.1's title line `- [x] Title:` to `- [ ] Title:` and its Resolution line to section 01's open form (`  - Resolution: Not fixed because WP-29 section 02 has not landed. Graded S1 (WP-29): silently wrong output in common use; twoway line y x without sort draws another path, and nothing says so.`). Expected: `P0.1 is closed and no closed BUGS.md entry's Resolution holds (WP-29, P0.1)` and `… is open in the WP-29 form`. Revert with `git checkout -- BUGS.md`.
3. In CHANGELOG.md, add a line `<!-- WP-29 P0.7 -->` under `### Results that change`. Expected: `markers left in CHANGELOG.md: ['P0.7']` (and `test_a_closed_p0_has_no_marker_and_a_resolution` fails with `P0.7 is closed and CHANGELOG.md still holds its marker`). Revert with `git checkout -- CHANGELOG.md` (this runs before 15-04 edits CHANGELOG.md).

## Appendix C: the provisional source-id ledger (anchors at 7421d3d; 15-05 re-finds each by text)

Verdict rule: **FULL** only when every bullet of the GAPS2 entry's **Gap** text is answered by a test in the P0's commits; **PARTLY** otherwise; **ANNOTATE** for ids already `Closed in WP-28`. "Expect" is the plan-time expectation from the section notes and the Gap text; 15-05 decides on the merged tree.

| P0 | Source id(s) | Document and anchor | Expect | Notes |
|---|---|---|---|---|
| P0.1 | GAPS2-A1-a, GAPS2-A1-c | GAPS2 A1 (:111, Tracked :120) | FULL | S02: data order, sort, sort(varlist), ts types in time order, help paragraph; residual O1 (rarea one bound missing) is not in A1's Gap text |
| P0.1 | GAPS2-A4-o | GAPS2 A4 (:175, :196) | PARTLY | open: the other type-specific options A4 lists |
| P0.1 | GAPS2-B12-e, GAPS2-G15-b | GAPS2 B12 (:476, :488) | PARTLY | open: horizontal/vertical, recast(), connect(), cmissing(n) |
| P0.1 | AUDIT-08, AUDIT-10 | AUDIT :24, :25, :60, :61, :62, :70, :76, :77, :144, :173 | tag | "Always x-sorted" / "sort(varlist) ignored" corrected in the tag |
| P0.1 | REM-§2-S06-sort | REMAINING.md:124-126 | closed | |
| P0.1 | REM-S06-b | REMAINING.md:305 (Status row 06) | partly | open: `horizontal`, `vertical`, positional plot options |
| P0.2 | GAPS2-B4-a, GAPS2-B4-b | GAPS2 B4 (:418, :423) | FULL | S10 |
| P0.2 | (S10 note) | GAPS2 B16 (:516, :525) | PARTLY | rescale part closed; rows/holes/titles/legend/i*axes open |
| P0.2 | (S10 note) | AUDIT :142 | tag | "common scales" was false before P0.2; yrescale no longer ignored |
| P0.3 | REM-08-05-C3b, REM-08-05-C3a | REMAINING.md:2142-2156 (Appendix C 08-05 item 3) | closed | |
| P0.3 | REM-08-05-M3 | not located at 7421d3d (Appendix B 08-05 item 3, :1064, is the date-cardinality warning) | not located | 15-05 searches; else reported |
| P0.3 | (S03 note) | GAPS2 A13 (:291, :306), with C10 | PARTLY | histogram/kdensity keys closed; fit, lowess, lpoly, mband, pc and immediate keys, mixed-layer y title, `y1/y2` range titles open |
| P0.4 | CRIT-01 | DROPIN P0.4 only (critic pass) | closed | no REMAINING/GAPS2 row |
| P0.5 | REM-09-02-AXIS-N | REMAINING.md:2447-2466 (Appendix C 09-02 items 14 and 15; S10 cites :2451-2466; GAPS2 B15's Tracked cites :2459) | partly | the `axis(#)` misrouting and silent pass-through closed; the other dropped scale and label sub-options stay |
| P0.5 | GAPS2-B15-a | GAPS2 B15 (:505, :513) | PARTLY | open: axes 3-9, `yaxis(1 2)` |
| P0.5 | GAPS2-B22-c | GAPS2 B22 (:595, :604) | PARTLY | `axis(2)` closed; numlists, abbreviations, `lstyle`/`style`/`noextend` open unless S10 closed them |
| P0.5 | AUDIT-27 | AUDIT :116, :137 | tag | |
| P0.6 | GAPS2-A6-c, GAPS2-A6-d, GAPS2-C5-g | GAPS2 A6 (:215, :228), with C5 | FULL if S04 draws every Stata expression through `twoway__function_gen` and handles plan step 3 (`range(varname)`, `droplines()`, `horizontal`); else PARTLY | DROPIN P1.22 is A6's broad part: annotate it closed if FULL |
| P0.7 | GAPS2-A9-a, GAPS2-A9-b, GAPS2-C1, GAPS2-C13 | GAPS2 A9 (:246, :259), with C1, C13 | FULL | M2 port pinned to `r(bwidth)` within 1e-9 in both modes and served recomputes |
| P0.7 | GAPS2-C12-e | GAPS2 C12 (:781, :797) | PARTLY | only the lpoly default-bandwidth bullet, unless S11 measured every C12 bullet |
| P0.7 | AUDIT-24 | AUDIT :92 | tag | |
| P0.8 | REM-08-05-C6d, REM-08-05-C6c | REMAINING.md:2180-2194 (Appendix C 08-05 item 6) | closed or partly | per S05 |
| P0.8 | REM-08-04-C2 | REMAINING.md:1954 | per S05 | |
| P0.8 | REM-08-04-C3a | REMAINING.md:1965 | per S05 | |
| P0.8 | REM-08-04-C12 | REMAINING.md:2075 | per S05 | |
| P0.9 | GAPS2-C7-a, -b, -c, -e, GAPS2-A10-a, -b | GAPS2 C7 (:760, :770), with A10 | FULL if the bootstrap is gone, `pwidth()`/`var()` are honoured, the band equals Stata's in served recomputes and `level()` is checked as the plan says; else PARTLY | |
| P0.9 | AUDIT-23 | AUDIT :27, :93 | tag | |
| P0.10 | REM-09-07-HOVER-EXPORT | REMAINING.md:1217 (Appendix B 09-07 item 2) | closed | |
| P0.10 | REM-09-07-HOVER-TEST | REMAINING.md:2546 (Appendix C 09-07 item 5) | closed | |
| P0.10 | GAPS2-G16-res | GAPS2 G16 (:1487, :1492) | ANNOTATE | the hover-only residual closed; "an x or y variable not named in hover() keeps its number" stays |
| P0.10 | (S06 note) | GAPS2 G3 (:1409, :1414) | ANNOTATE | the counting rule |
| P0.11 | GAPS2-I2-a, GAPS2-I2-b | GAPS2 I2 (:1618, :1638) | FULL | S14 |
| P0.11 | (I2 plan step 4) | AUDIT :161, :183 | tag | |
| P0.12a, P0.12b | GAPS2-I3-a, -b, -c | GAPS2 I3 (:1641, :1656) | FULL (after both) | Tracked names P0.12a's entry and commit, with P0.12b's after `; with` |
| P0.12a, P0.12b | AUDIT-87 | AUDIT :162, :183 | tag | |
| P0.12a | (decision M4) | GAPS.md L10 (:2417-2435) | paragraph | D.8 |
| P0.13 | GAPS2-F2a, GAPS2-F2b | GAPS2 F2 (:1317, :1322) | FULL | commit = the `(WP-29 P0.13 F2)` commit |
| P0.13 | GAPS2-F4, GAPS2-H2a, GAPS2-H2b | GAPS2 F4 (:1333, :1338), with H2 | FULL | commit = the F4 commit |
| P0.13 | GAPS2-F9c | GAPS2 F9 (:1353, :1363) | PARTLY | bullet c closed; a, b, d, e open |
| P0.14 | GAPS2-X3-a, -b, -c | GAPS2 X3 (:1962, :1973) | FULL | with S08's R-6 bounded retention |
| P0.15 | REM-06-06-C7 | REMAINING.md:1848-1862 | closed | |
| P0.16 | REM-06-06-C8b, REM-06-06-C8b-link | REMAINING.md:1863-1878 (C8's `_apply_colorvar` clause) | partly | C8's LabelSet masking is a different defect |
| P0.17 | GAPS2-C4, GAPS2-E4a, GAPS2-E4c | GAPS2 C4 (:743, :755), with E4 | D.4 (a) or (b) | maintainer's choice |
| P0.17 | AUDIT-38 | AUDIT :29, :44, :45, :161 | tag | the cue on the saved page |
| P0.18 | REM-15-03-C15 | REMAINING.md:3020 (Appendix C 15-03 item 15) | partly | only the bar/rbar width and emptied-layer style |
| P0.19 | GAPS2-H7a … GAPS2-H7g | GAPS2 H7 (:1545, :1550) | FULL if S09 covers detection, `venv()`, quoted printed commands with `c(python_exec)`, the `--user` site and the ensurepip hint; else PARTLY | |
| P0.20 | GAPS2-E1-residual | GAPS2 E1 (:1102, :1111) | ANNOTATE | the KPI-spread residual closed |
| all | DROPIN §3 P0 items 1-20 | DROPIN :37-62 | D.7 | |
| P0.1, P0.7, P0.9, P0.17, P0.12 | DROPIN §4 decisions | DROPIN :337, :338, :339, :340, :346 | D.7 | M1, M2, M2, M3, M4 |

## Appendix D: the exact edit forms

- **D.1 GAPS2, fully closed** (one physical line):
  `- **Tracked:** Closed in WP-29, BUGS.md "<title>", commit <sha>[; with BUGS.md "<title2>", commit <sha2>][; residual deferred (WP-29): <clause>]; was: <the whole old Tracked text>`
- **D.2 GAPS2, partly closed:**
  `- **Tracked:** Partly closed in WP-29 (P0.<n>, commit <sha>[; P0.<m>, commit <sha>]): <what WP-29 closed, in the Gap text's own words>; open: <what remains>; was: <the whole old Tracked text>`
- **D.3 GAPS2, WP-28's closed ids:** inside the residual clause the commit closes, before `; was:` (or at the residual's end), insert ` -- closed in WP-29 (P0.<n>, commit <sha>)`; for a residual only partly closed, ` -- the part <what> closed in WP-29 (P0.<n>, commit <sha>)`. G3's counting rule is added the same way: ` -- WP-29 (P0.10, commit <sha>): hover()'s own variables count only where a layer can show them or csv is given; the graph itself is still treated as touched`. The `Closed in WP-28, …, commit <sha>` prefix is never changed.
- **D.4 C4:** (a) recommended: `- **Tracked:** Partly closed in WP-29 (P0.17, commit <sha>): a frozen fit, smooth or density on the saved page shows a visible stale cue after a move that removed a row of its estimation sample, cleared when the move is undone; open by decision (WP-29 M3, DISCOVERY Q3): the saved page does not re-estimate them, and nothing is ported to _FILTER_JS; was: <the whole old Tracked text>`. (b) alternative: keep `Deferred (WP-28): out of scope by decision (DISCOVERY Q3), with its duplicate E4; nothing is ported to _FILTER_JS on its account` and insert `; the stale cue was added in WP-29 (P0.17, commit <sha>)` before `; was:`.
- **D.5 REMAINING.md and TWOWAY_COVERAGE_AUDIT.md tags** (appended to an item's last line, or a table row's last cell before its final `|`): ` [WP-29 P0.<n>, commit <sha>: closed]` · ` [WP-29 P0.<n>, commit <sha>: partly closed; open: <what>]` · on an AUDIT row whose claim became false: ` [WP-29 P0.<n>, commit <sha>: corrected -- <the true statement>]`. The AUDIT's dated line, directly under `Audit date: 27 September 2026`: `Rows tagged [WP-29 P0.n, commit …] were marked at WP-29's closeout (<ddmonyyyy>): the tag says what changed; the untagged text is the audit as written.`
- **D.6 BUGS.md append** (at the end of the Resolution line of the entry D.1 names): ` Closes GAPS2 <ID> (WP-29, <ID>).` one sentence per FULL id.
- **D.7 DROPIN-REMAINING.md:** a P0 item: ` [Closed in WP-29: BUGS.md "<title>", commit <sha>[, also <sha>…]; residuals: <the new item numbers, or none>]` (item 12: `BUGS.md "<P0.12a title>", commit <sha>; BUGS.md "<P0.12b title>", commit <sha>`; item 13: `commits <F2 sha> (F2), <F4 sha> (F4)` inside the bracket is commentary, not a GAPS2 line, so two shas are allowed here). A §4 decision: ` [Decided for WP-29: <M1|M2|M4|M3>, <the decision as index.md's decision record states it>; commit <sha>]`. A note on a P1/P2 item: ` [WP-29 note (S<NN>): <text>]`. A new item: `<n>. **<title>.** <measured text>. Effort <S|M|L>. Sources: WP-29-S<NN> (<what>)[, BUGS.md "<title>" residual].`
- **D.8 GAPS.md paragraphs** (a new paragraph, never a heading): `**Since WP-29 (P0.<n>, commit <sha>).** <the correction>.` L10's correction: "The served app now requires a per-launch secret token: without it no session, page, autoload, metadata or row reaches a client, `/health` and BokehJS's static files stay open, and the token is compared in constant time. The app never runs without its token: started without one, it makes its own and writes its link to a file only the user can read; only when no such file can be written anywhere does it print the link, once, after a warning, to the output of whoever started it. The sentence above that dash has no auth model no longer describes the served app. dash still has no accounts, administrators or administrative component, so rule 19 still does not apply; the adversarial reading of "auth bypass" above now also covers getting a session without the token. Guarded by <S13's tests, by node>." E1's correction: "`sort` and `sort(varlist)` are honoured on line, connected, area, rline, rarea and rconnected, which otherwise join in the data's order as twoway does; tsline and tsrline join in time order. The remark above that sort(varlist) is still named holds only for the other plot types." Both are checked against the merged code's behaviour (S13's and S02's tests) before they are written.
- **D.9 ROADMAP field:** `**GAPS2 closed:** <FULL ids, comma-separated, in GAPS2 order> · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28`; if no id is FULL, `**GAPS2 closed:** none · …`.
- **D.10 ROADMAP rewording: NOT APPLIED (R-6 ratified 01oct2026; section 01's Appendix D already carries the final BR-29.11 and AC-29.6, R15-8).** Kept for the record, the old form was: in BR-29.11 replace "one-line preview pages are deleted when the command ends" with "every one-line preview page is private and bounded (five per session), removed by `dash clear` and with its session"; in AC-29.6 replace "no preview page survives the command" with "every preview page is private and bounded (five per session), and is removed by `dash clear` and with its session".
- **D.11 AGENTS.md paragraph** (the WP-28 paragraphs' form): a bold lead `**<Invariant name>.**`, one to three sentences saying what must stay true and where it lives, then `Guarded by` and the test node(s) in backticks, `test/<file>.py::<Class>[::<test>]`, optionally followed by `test/<script>.cscript <CASE-ID>`. The eight mandatory invariants (PLAN.md §7 S15.4): (1) join order (`GlyphMapper._join_order` is the only place a joining layer's rows are ordered; rank columns `__dashs<k>` are made in Stata); (2) Stata units for computed layers and KPI statistics of a date; (3) the private 0700 root and the 0600 writer (a location that is not private is noted, never refused; the anti-hijack guards refuse with r(7102)), and the launch from the verified bytes (dash starts its served app only from the bytes it read through a descriptor it opened and verified, never by path; round 2, answer B); (4) the per-launch token, never missing (a hand-started app makes its own), never printed except K-9's once-only warned fallback when no link file can be written (round 2, answer A), and `127.0.0.1` URLs; (5) the parent watch; (6) embed rows (a cell is embedded only when a layer, a recomputed KPI, a filter or csv reads it; both modes number the rows they send by rank, the served `index` included); (7) the `lpvar` key (never `var`, which `_dash_extract_vars` reads as a variable); (8) build-time served notes (a note the served app must print is decided at build time, `ServerAppBuilder._plan_graph_notes`/`_plan_by_groups`). Plus every section bullet (S03 variable labels, S06 hover export, S07 view ids and colour key, S08 Break, S10 by() sharing, and the bullets of 04, 09, 11, 12, 13, 14).

## Appendix E: the `### Done, measured` block (written by 15-10, numbers filled by 15-17)

~~~~markdown
### Done, measured (<to be measured in 15-17>)

- **P0 entries.** The 21 BUGS.md entries section 01 opened are closed,
  each test first, by a commit whose subject names it (P0.13 by two, F2
  then F4); each Resolution reads (WP-29, P0.<n>) and names tests that
  exist. WP29_OPEN is {} and test_no_wp29_entry_remains_open keeps it so.
  No CHANGELOG marker is left; the 26 WP-29 lines sit in the lists
  WP29_LISTS names.
- **Per P0.** <one line per P0, from its section's closeout note and its
  commit: "P0.1 (<sha>): …" -- 21 lines, P0.2 with the 100-panel settle
  time from its commit body>
- **GAPS2.** Closed: <FULL ids>. Partly closed, each Tracked line saying
  what is open: <PARTLY ids>. WP-28 residuals closed or narrowed: <E1
  (P0.20), G16 (P0.10), G3 (P0.10)>. C4: <the approved form>.
- **Residuals.** <count> deferred clauses, as BUGS.md records them and the
  maintainer approved; filed in DROPIN-REMAINING.md as <item numbers>.
- **Fixtures.** <from git diff --stat 7421d3d..HEAD -- test/fixtures>.
- **Tests flipped.** <n> pinned expectations, each named with its reason
  in its fix commit's Flipped: line; every pytest node named collects.
- **Security (AC-29.6).** <the token (self-made key included), once-printed link (K-9), private-file, not-private-location note, anti-hijack r(7102),
  launch-from-the-open-file, preview, parent-watch, Break, non-finite-JSON and embed-row tests, by class>, all
  green in both runs below.
- **Runs (<date>, on the final tree).** make test, under Stata's Python
  (<path>, <version>): <n> passed, <x> xfailed, 0 skipped. make test-dev
  (<interpreter>, <version>): <n> passed, <x> xfailed, 0 skipped. make
  cert: 67 of 67 scripts, 0 skipped; wall time <b> s before WP-29 (step
  0b) and <a> s after, a growth of about <g> minutes; the <k> blocks of
  test_wp29_truth.cscript took <t> s, the slowest <S..> (<s> s). make
  gate: <e> of <e> examples and <p> of <p> scheme pages clean from a
  net-installed copy. No S1 or S2 entry is open.
- **Not measured.** Windows, Linux and Stata before 19 (the package's
  non-goals): the commands dash_setup prints were tested in the sandbox
  for cmd.exe and POSIX shells only. <any E2 exception, by commit>.
- **AGENTS.md** carries "Invariants introduced by WP-29", <n> paragraphs,
  each with its guarding test.
- **Merge.** `git checkout main && git merge --no-ff wp29-p0` -- reported,
  not run.
~~~~

Every `<…>` is replaced by 15-17 (the heading's by today's `ddmonyyyy`); 15-10 writes the block with `<to be measured in 15-17>` in place of each run number, wall time and date, and the GAPS2, residual and per-P0 lines already filled.

## Appendix F: commit messages (no AI reference, no co-author trailer)

~~~~text
Close the WP-29 allowance and keep every P0 entry closed (WP-29 S15.1)

Regression: test/test_tracking_documents.py::TestWp29Tracking::test_no_wp29_entry_remains_open -- failed on a key put back into WP29_OPEN with <E line>
Regression: test/test_tracking_documents.py::TestWp29Tracking::test_no_wp29_entry_remains_open -- failed on P0.1's entry reopened with <E line>
Regression: test/test_tracking_documents.py::TestWp29Tracking::test_no_wp29_entry_remains_open -- failed on a re-added P0.7 marker with <E line>

All 21 WP-29 entries are closed and every key was deleted by its section,
so WP29_OPEN becomes the one-line {} and the new test holds it there with
every marker gone. The CHANGELOG's 26 WP-29 lines are checked in their
lists, completed where a value was missing, and the blank lines left
between them for merging are removed.
~~~~

~~~~text
Mark what WP-29 closed in the audits and the task list (WP-29 S15.2)

GAPS2.md: <PARTLY ids> partly closed, naming what stays open; <ANNOTATE
ids>: WP-28's residuals that WP-29 closed say so; C4 <form>. BUGS.md: the
entries about to be named for <FULL ids> carry (WP-29, <ID>).
REMAINING.md, TWOWAY_COVERAGE_AUDIT.md and DROPIN-REMAINING.md: every row
a P0 source names is tagged with its commit; the decisions and the
approved residuals are recorded. GAPS.md: L10 and E1 corrected in body
paragraphs. The Closed lines land with the DONE heading in the next
commit, since either alone fails the tracking tests.
~~~~

~~~~text
Mark WP-29 done and name the entry and commit that closed each GAPS2 gap (WP-29 S15.3)

Regression: test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it -- failed on a reverted Tracked line with "<text from 15-10-guard.txt>"

<FULL ids> are closed; the P0 table gains a commit per entry; the
measured block follows in a later commit.
~~~~

~~~~text
Record the invariants WP-29 introduced, each with its guarding test (WP-29 S15.4)
~~~~

~~~~text
Date the 0.1.0 release candidate for WP-29 (WP-29 S15.6)

make test (Stata's Python, <path> <version>): <last line>.
make test-dev (<interpreter> <version>): <last line>.
~~~~

~~~~text
Record WP-29's release measurements (WP-29 S15.7)
~~~~
