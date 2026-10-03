# Section 01: Tracking foundation

> Part of: WP-29 · P0: all 20, tracked as 21 BUGS.md entries (P0.1-P0.20, with P0.12 split into P0.12a and P0.12b), opened here and closed by sections 02-14 · Risk: green · Batch: 1 (lands first) · Depends on: none (after step 0) · Blocks: 02-15 · Tasks: 8, 1 commit (S01)

## Review amendments

> Batch **1** · Depends on **none (after step 0)** · Blocks **02-15** · Risk **green** · Commits: one, `(WP-29 S01)`, made by task 01-08

**Ratified 01oct2026 (applied in this file at plan time).** The maintainer's answers (index.md "Decisions for maintainer ratification") changed text this section writes, and nothing else:
- **Appendix D (ROADMAP.md).** BR-29.6, BR-29.11 and AC-29.6 now carry PLAN.md §7 S01 item 1's amended text in place, so PLAN.md's override and this appendix agree. BR-29.7 names the kept date axis as a documented divergence (answer 1). BR-29.9 adds that both modes number the rows they send by rank, the served `index` included (answer 4). BR-29.10 adds that the app never runs without a token (answer 3). BR-29.11 and AC-29.6 say that a location that is not private proceeds with one note, and that only the anti-hijack guards refuse, with r(7102) (answer 2); no r(603) refusal remains. Round 2 (01oct2026): BR-29.10 and AC-29.6 add that the key is never printed except when no link file can be written anywhere, when the link is printed once after a warning and the server keeps serving (answer A); BR-29.11 and AC-29.6 add that dash starts its served app only from the bytes it wrote and verified, never by path (answer B). Appendix D is now 218 lines, so ROADMAP.md is 4808 lines after S01 (task 01-05's verify and Evidence "The documents after S01").
- **Appendix A (BUGS.md).** The Suggested fix of P0.11, P0.12a, P0.12b and P0.14 is reworded to match (P0.12a and P0.12b again for round 2: the once-printed link, answer A; the launch from the verified bytes, answer B). Titles, grades, Resolutions and line counts are unchanged (each field is one line). WP-29 opens exactly these 21 entries; S14 opens no further S3 entry.
- **Appendix C (CHANGELOG.md).** Unchanged: S01 writes only the 26 markers; each section writes its own lines.

**Ratified 01oct2026 (round 2; applied in this file at plan time).** The maintainer answered "Print the URL once" (A), "Launch from open file" (B) and "Commit them" (C) (index.md "Decisions for maintainer ratification", round 2). Round 1 stays in force. What changed here:
- **Appendix D (ROADMAP.md).** BR-29.10 and AC-29.6 add that the key is never printed except when no link file can be written in any folder dash tries; then one warning line and the link are printed once and the server keeps serving (A; section-13 K-9). BR-29.11 and AC-29.6 add that dash starts its served app only from the bytes it wrote, read through a descriptor it opened and verified, never by path (B; section-08 R-9). PLAN.md §7 S01 item 1 carries the same text. Appendix D is 218 lines and ROADMAP.md 4808 after S01 (measured on a scratch copy: the readers still give `{'done': False, 'gaps': {}}`, `{'done': False, 'gaps2': {}}` and 76).
- **Appendix A (BUGS.md).** The Suggested fix of P0.12a and P0.12b adds the same two points, each still one line, so BUGS.md stays 2850 lines.
- **Boundaries.** `.ultraplan/wp29/` is committed by step 0a (C), before this section's worktree is cut; S01 still never stages or edits a plan file.
- **Appendix C (CHANGELOG.md).** Unchanged.

There was no research report or design review for this section (the WP-29 research list for S01 is empty). It is derived from `index.md` (decisions A3, A4, A5, A6, A10, the "Deltas from BRIEF.md" table, merge rules R1 and R3, and the manifest) and `PLAN.md` §7 "S01". Every file it writes was prototyped on a copy of the tree at `7421d3d` and run (see Evidence, "Prototype"). That run led to five refinements of `PLAN.md` §7. They are binding here:

- **R-01 (more tests).** `TestWp29Tracking` has six tests, not four. The two extra tests are:
  - `test_each_p0_sits_in_its_changelog_lists`, which checks each P0's marker or closing line against the list `index.md` "P0 coverage" assigns it;
  - `test_the_wp29_problem_readers`, the unit tests of the four problem helpers (CLAUDE.md rule 3).

  `test/test_cscript_hygiene.py` also gains `TestTheWp29TruthScript` (three tests). This guards the truth script that 13 sections append to in parallel.
- **R-02 (blank lines between markers and entries).** The 21 BUGS.md entries and the 26 CHANGELOG markers are separated by one blank line each. The reason: when a neighbouring section has already changed the adjacent line, `patch -p1` can still apply a hunk at fuzz 2 if the line next to it is blank. If entries or markers touch, the hunk is rejected (Notes, "Merging").
- **R-03 (the scaffold fails when nothing ran).** The truth script exits 9 when no case ran. A `WP29_ONLY` that names no block is otherwise a silent green. This was measured: `WP29_ONLY=S99` printed `ALL CHECKS PASSED` before the guard was added.
- **R-04 (a fresh private work directory).** The truth script makes a fresh work directory from a `tempfile` name and fails if it cannot. It never reuses a fixed `c(tmpdir)` name, which another account could plant on a shared `/tmp` (rule 1).
- **R-05 (S01 lands before 02-09 are cut).** The manifest says 02-09 depend on 01, but `index.md` step 1 cuts all nine batch-1 worktrees from the step-0a tree. A section cut before S01 lands has no entry to close, no `WP29_OPEN` key to delete and no marker to replace, so its gate G5 cannot pass. S01 therefore runs alone first (it changes no shipped file). The merger lands it on `wp29-p0`, and only then are the worktrees for 02-09 cut. `<scratch>/batch-1-base.txt` is re-recorded at that point. S01's own "failed at" sha is the step-0c sha.

## Overview

WP-29 closes the 20 P0 items of the drop-in re-audit (`.ultraplan/handoff/DROPIN-REMAINING.md` §3 "### P0", lines 35-62, verified at `357c368`). Today, nothing in the repository records them:
- BUGS.md has no entry for any of them;
- CHANGELOG.md has no place for their lines;
- ROADMAP.md stops at WP-28;
- the certification suite has no script for the Stata-truth blocks the sections will add.

Two guards stand in the way of simply writing the entries:
- **The release guard.** `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2` (`test/test_tracking_documents.py:503-510`) turns the suite red on any open S1 or S2 entry. Measured on the prototype: the 21 entries open 21 such failures.
- **The hygiene pins.** `test/test_cscript_hygiene.py` counts the cscripts (66, at :295) and the scripts that gate on Python (48, at :313). A new script breaks both pins until they move.

After this section:
- **BUGS.md** carries 21 open, graded entries in the WP-29 form.
- **The allowance.** `WP29_OPEN` in `test/test_tracking_documents.py` exempts exactly those 21 titles from the release guard. `TestWp29Tracking` makes every later section close its entry, delete its key and replace its markers in the same commit. A stale or forged allowance fails the suite.
- **CHANGELOG.md** holds 26 `<!-- WP-29 P0.n -->` markers in the five lists of the current release.
- **ROADMAP.md** opens WP-29. It is not DONE, and its `**GAPS2 closed:**` field is filled at closeout.
- **The truth script.** `test/test_wp29_truth.cscript` exists with a smoke block S01 (`W29-01`). It is registered as runner block `// 68.`, and its block layout is guarded.

This section also writes down, once, the forms every later section copies (TR-01.10):
- the in-place closure of an entry;
- the replacement of a marker;
- a truth block;
- the commit message.

**Test order and commit rule (CLAUDE.md rules 4 and 7).**
1. Task 01-01 writes the section's tests against the unmodified tree (the step-0c sha, in the worktree `wp29-s01`). It saves their failure text to `<scratch>/01-S01-failure.txt` and does not commit. On the prototype, 11 tests failed.
2. Tasks 01-02 to 01-07 turn the tests green.
3. Task 01-08 runs the full suite once and makes the section's one commit, subject `Open the WP-29 P0 entries, markers and truth script (WP-29 S01)`. Its body opens with the saved failure text.

No shipped file changes.

## Risk: [green] — two test modules extended, one new certification script, three documents appended to; no shipped file changes

- **Why green.** No renderer, ado, Mata or help text moves. Every existing assertion passes unchanged except two count pins (66→67 and 48→49), which move because a script is added. The release guard keeps its exact behaviour for every entry outside `WP29_OPEN`.
- **Risk factors.**
  1. The allowance weakens the release guard.
  2. Thirteen sections edit BUGS.md, CHANGELOG.md, `WP29_OPEN` and the truth script from parallel worktrees, so `patch -p1` may reject hunks.
  3. ROADMAP.md's readers end a package at any `# `/`## ` line and split on the literal `## Traceability matrix` (`_wp_sections`, `test_tracking_documents.py:628-642`; `_matrix_gaps`, :537-541).
  4. `test/test_version_floor.py:91-95` reads `### Requirements` up to the next `### `, so a marker or heading placed wrongly moves that range.
  5. GitNexus does not index this repository today (Evidence, "GitNexus").
- **Mitigation.**
  1. The exemption applies only to a title that `WP29_OPEN` names. `_wp29_open_problems` also requires that entry to be open and to read `Not fixed because WP-29 section NN has not landed. Graded S1|S2 (WP-29): …`. An S1 entry from any other package still fails the guard, and S15 empties the allowance.
  2. Blank-line separation (R-02); in-place edits only; `TestTheWp29TruthScript` checks block order; the merge notes below.
  3. A hazard check in 01-05 (no `# `/`## ` line, no `Gaps closed`). The readers' outputs were measured unchanged.
  4. `test_version_floor.py` was run on the prototype: green.
  5. Task 01-02 indexes the main checkout first.

## Dependencies

- **Depends on:** step 0 of `index.md`. That is 0a (the `TWOWAY_COVERAGE_AUDIT.md` commit with `_ROOT_ALSO`) and 0c (the base sha). Nothing else.
- **Blocks:** every other section (02-15). Each fix section:
  - closes the entry S01 opens;
  - deletes the key S01 adds;
  - replaces the marker(s) S01 places;
  - appends its truth block above the marker S01 writes.
  S15 empties the allowance and fills ROADMAP.
- **Parallel batch:** 1, but it must land BEFORE the other batch-1 worktrees are cut (R-05). It touches no file of 02-09 except the shared tracking files, which they edit only after it.
- **Why:** each fix section's gate G5 (`test_tracking_documents.py` green, with its entry closed, its key gone and its markers replaced) can only pass on a tree that holds S01's entries, keys and markers.

## Evidence

All line numbers are at `7421d3d` (HEAD of `wp29-p0` at plan time; `git log --oneline -1` → `7421d3d Record what remains for dash to be a drop-in twoway replacement`).

### The release guard and the BUGS.md readers (`test/test_tracking_documents.py`, 1226 lines)

```python
 481 class TestNoOpenEntryBlocksARelease:
 492     _GRADE = re.compile(r"\bGraded (S[1-3]) \(WP-\d{2}\): \S")
 494     def test_every_open_entry_is_graded_once(self, bugs):        # exactly one Graded per open entry
 503     def test_no_open_entry_is_s1_or_s2(self, bugs):
 504         entries, _p = bugs
 505         bad = ["line %d: %s %s" % (e["line"], g, e["title"][:90])
 506                for e in entries if not e["closed"]
 507                for g in self._GRADE.findall(e["fields"].get("Resolution", ""))
 508                if g in ("S1", "S2")]
 509         assert not bad, ("open S1/S2 BUGS.md entries block the release:\n"
 510                          + "\n".join(bad))
```

- **`TestEveryOpenEntrySaysWhyItIsOpen`** (:458-478) requires an open entry's Resolution to match `\b(not fixed|still open|stays open|remains open)\b` and to contain `because`.
- **`_ENTRY` / `_FIELD`** (:103, :106) read `- [ ] Title: …` and the four fields `File Names and Line Numbers`, `Description`, `Suggested fix`, `Resolution`. A field stores its whole line, `  - Resolution: …` included (`_parse_bugs`, :110-156).
- **`_references`** (:300-330) treats three kinds of name in an entry as references that must exist:
  - every `test_*.py|cscript|do` name (`_FILE_REF`, :290);
  - every `test_x.py::Class[::test]` node (`_NODE_REF`, :292);
  - every `Test[A-Z]\w+` word (`_CLASS_REF`, :293).

  Only these three can be "dangling". A `_CASE_ID`-shaped token (:212) is only ever "found" or ignored. That is why `WP-29`, `AUDIT-08` and `REM-08-05-C3b` in a Description are inert. An open entry here names no test file, node or `Test…` word.
- **The precedent for an allowance** is `WP23_OPEN_UNTIL_INTEGRATION = frozenset()` (:65). It is checked by `test_the_allowances_are_still_needed` (:890-911) so it cannot outlive its reason.
- **BUGS.md at 7421d3d.** It has 2724 lines and 455 entries: 451 closed and 4 open (2523, 2559, 2595 and 2601, each graded `S3 (WP-27)`). It ends with one newline (`tail -c 1 BUGS.md | xxd` → `0a`). The WP-28 entries from 2640 on are not blank-separated; the older ones are.

### The CHANGELOG lists, and the one test that reads them

`grep -n '^## \|^### ' CHANGELOG.md` (621 lines) gives:

```
3:## 0.1.0, 30sep2026 (release candidate)
10:### Results that change          (last item ends 236 "  (follow-up to GAPS2 X2)", blank 237)
238:### Security                    (last item ends 272 "  CSV injection. (WP-21)", blank 273)
274:### New
315:### Fixed
376:### Changed behaviour (may need your do-files changed)   (last item ends 437 "... (WP-28, G2)", blank 438)
439:### Removed
448:### Requirements                (last item ends 464 "... (WP-28, K2)", blank 465)
466:### Fixed in WP-28
516:### Fixed after WP-27 (the S3 batch, 24sep2026)
561:### Fixed in WP-27
```

- **The release.** There is only one `## ` release heading. The WP-28 group line `**WP-28 (GAPS2 audit, 25sep2026)**` sits at 142, in `### Results that change`. Its items are consecutive `- ` lines.
- **The one test that reads a CHANGELOG list** is `test/test_version_floor.py:91-95`:

  ```python
  changelog = _flat(_read("CHANGELOG.md"))
  rq_start = changelog.index("### Requirements")
  rq_end = changelog.index("### ", rq_start + 10)
  ```

  After S01, the next `### ` after Requirements is `### Fixed in WP-29`. The P0.19 marker sits inside the range, and the floor text is unchanged. The test was run on the prototype: green.
- **No existing test reads `<!-- `** in CHANGELOG.md. `grep -rn '<!--' test/*.py` finds only `test_string_value_export.py`, on page HTML.

### ROADMAP.md and its readers

- **Structure.** `grep -n '^## \|^# ' ROADMAP.md` gives `4243:## WP-28 · Close the GAPS2 audit's 22 gaps — DONE`, then `4448:## Traceability matrix`, and `grep -n '^---$'` gives 4446. WP-29 goes between the `---` at 4446 (with its blank line, 4447) and 4448, as WP-28 went before it.
- **The readers.**
  - `_wp_sections` (:628-642) splits on `^## WP-\d{2} ` and ends a section at `^# ` or `^## (?!WP-)`.
  - `_parse_roadmap` (:645-659) reads `**Gaps closed:**`.
  - `_parse_roadmap_gaps2` (:721-741) reads `**GAPS2 closed:**`, whose items must match `^(?:and\s+)?([A-NX]\d{0,2})`.

  So the field text `(filled at closeout)` yields no ids (measured below), and the GAPS2 checks pass vacuously until S15 fills it.
- **Who reads ROADMAP.** No test other than `test_tracking_documents.py` reads ROADMAP.md's content (`grep -rn '_read(.ROADMAP\|"ROADMAP\.md")' test/*.py` hits only `test_packaging.py:429`'s allowlist).

### The runner, the hygiene pins and WP-28's frame

- **Block 67** of `test/run_all_cscripts.do` (1766 lines) occupies 1715-1741. Line 1741 is its closing `}`, 1742 is blank, and 1743-1745 are the `// Summary` banner:

  ```
  1716 // 67. test_gaps2_truth.cscript (WP-28: the one certification script for
  1721 display as text "[ RUN ] test_gaps2_truth.cscript"
  1724     do "test_gaps2_truth.cscript"
  1730 if `rc' == 222 {
  1741 }
  ```

- **`scripts/cert_verdict.py:21`** registers a script by `^\s*do "(?:[^"]*/)?([^"/]+\.cscript)"\s*$`. `test/test_cert_verdict.py::TestTheRegisteredScripts::test_the_real_runner_registers_every_script_in_test` requires the runner's list to equal the `.cscript` files on disk.
- **`test/test_cscript_hygiene.py`** (870 lines):
  - `assert len(_CSCRIPTS) == 66` at :295, with its comment at :284-294;
  - `assert len(names) == 48` at :313, with its comment at :309-312 (the scripts whose text matches `SKIP[^"\n]*\bPython\b`);
  - `assert len(with_probes) == 13` at :322. S01 does not touch this one; it is S09's (index R1).

  The per-script tests a new script must pass are `test_no_script_probes_python_by_executing_it`, `test_no_unsafe_expansion`, `test_the_runner_calls_it`, `test_no_build_runs_with_the_browser_allowed` and `test_a_script_that_needs_python_says_so_through_the_setting`. The new script must also use no `capture python:` import probe.
- **`test/test_gaps2_truth.cscript`** (1624 lines) is the frame copied:
  - the header comment;
  - `cscript "GAPS2 truth: twoway comparisons" adodir ".."` (26);
  - the `c(python_exec)` gate (31-34);
  - `do "cert_helpers.do"`, then `quietly do "cert_svg.do"`, `qui do "../dash_parse.mata"`, `qui do "../dash.ado"` and `global dash_nobrowser 1` (36-40);
  - `_gt_expect`/`_gt_done` (49-71);
  - blocks gated by `local only : env GAPS2_ONLY` / `if inlist("`only'", "", "S02") {`;
  - the marker `* ==== append new blocks above this line ====` (1601);
  - the summary, which exits 9 (1603-1624).

  WP-28's scaffold test is `test/test_svg_truth.py::TestScriptHygiene::test_the_truth_script_has_the_block_scaffolding` (:378-395).
- **`test/cert_svg.do:195`.** `cert_svg_texts` writes its list to `` `file'.texts.jsonl `` beside the SVG. The prototype's first run left `w29s01.svg.texts.jsonl` behind until the block erased `r(list)` too.
- **Prefixes are free.** `grep -rn 'W29-\|WP29_ONLY\|WP29_OPEN\|test_wp29_truth' test/ scripts/ Makefile` finds nothing, so the prefix `W29` and every new name are unused.

### GitNexus

`gitnexus_impact({target: "test_no_open_entry_is_s1_or_s2", direction: "upstream", repo: "dash"})` answered `Repository "dash" not found. Available: TYME, PhotoShootPlannerPro`. `gitnexus_list_repos()` lists only those two. There is no `.gitnexus/` in the main checkout. The maintainer's uncommitted `.gitignore` edit adds `.gitnexus` (`git diff .gitignore`: `+.gitnexus`); a worktree cut from `wp29-p0` does not have that line. So:
- task 01-02 runs `gitnexus analyze` in the MAIN checkout, never the worktree;
- no step stages `.gitnexus/`.

### Twoway truth behind one entry (P0.4), measured

The do-file `adopath ++ "<repo>/"`, then `cd "<repo>/test"`, then `quietly do "cert_svg.do"` ran `twoway scatter mpg weight, ytitle(, size(large))` and read the SVG. It was run through `scripts/stata_slot.sh` in StataNow 19.5 and printed:

```
P04 ytitle(, size(large)) keeps Mileage (mpg): found=1 count=1
```

So twoway keeps the default title when a title sub-option has no text, as the P0.4 entry says. The other entries quote DROPIN-REMAINING.md's text and its source ids; those claims were measured by the re-audit at `357c368` and are re-measured by each fix section (R7).

### Prototype of this section (scratch copy of `7421d3d`, 30sep2026)

`git archive 7421d3d | tar -x` into a scratch directory. The exact texts in Appendices A-G were applied there and run. The skip below is `test_a_closing_commit_exists` ("not a git working tree"), which does not skip in a real checkout.

- **Before S01, on the real tree.**

  ```
  $ python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_version_floor.py -q -n0 -p no:cacheprovider
  421 passed in 3.94s
  $ python3 -m pytest test/test_tracking_documents.py --collect-only -q -n0 -p no:cacheprovider   →  34 tests collected
  $ python3 -m pytest test/test_cscript_hygiene.py --collect-only -q -n0 -p no:cacheprovider     →  359 tests collected
  ```

- **Red first: the test classes only, no helpers, documents unchanged** (task 01-01's state).

  ```
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_every_allowed_title_is_an_open_entry
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_an_open_p0_keeps_its_marker
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_a_closed_p0_has_no_marker_and_a_resolution
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_each_p0_sits_in_its_changelog_lists
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_the_marker_reader
  FAILED test/test_tracking_documents.py::TestWp29Tracking::test_the_wp29_problem_readers
  FAILED test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script
  FAILED test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read
  FAILED test/test_cscript_hygiene.py::TestTheWp29TruthScript::test_the_scaffold_is_in_order
  FAILED test/test_cscript_hygiene.py::TestTheWp29TruthScript::test_every_block_is_gated_closed_and_in_section_order
  FAILED test/test_cscript_hygiene.py::TestTheWp29TruthScript::test_the_block_reader
  11 failed, 412 passed, 1 skipped
  ```

  The reasons, as `E` lines:
  - `NameError: name '_wp29_open_problems' is not defined` (×2);
  - `NameError` on `_wp29_marker_problems`, `_wp29_closure_problems`, `WP29_LISTS`, `_wp29_markers`, `_WP29_TRUTH`, `_wp29_blocks` and `_W29_MARK`;
  - `assert 66 == 67`;
  - `assert 48 == 49`.
- **Helpers in, documents unchanged** (task 01-02's state): 3 failed. Each failure's first line:
  - `P0.1: 0 BUGS.md entries are titled "line, connected, …"`;
  - `P0.1 is open and CHANGELOG.md holds no marker for it`;
  - `CHANGELOG.md has no single '### Fixed in WP-29' list`.
- **Why the allowance is needed** (a probe on the prototype's BUGS.md): open S1/S2 entries without the allowance: 21, starting `(2726, 'S1')`; with it: 0. The first new entry sits at line 2726.
- **Everything in.**

  ```
  $ python3 -m pytest test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_tracking_documents.py test/test_version_floor.py test/test_svg_truth.py test/test_test_integrity.py -q -n0 -p no:cacheprovider
  534 passed, 1 skipped
  ```

  The new collected counts are `test_tracking_documents.py` 40 (was 34) and `test_cscript_hygiene.py` 367 (was 359; the new class's 3 tests plus 5 per-script tests for the new script).
- **The documents after S01.**
  - BUGS.md: 2850 lines (+126), 476 entries, 451 closed, 25 open, 0 parse problems.
  - CHANGELOG.md: 682 lines (+61). `grep -c '<!-- WP-29 '` gives 26, per list: Results 13, Security 5, Changed behaviour 4, Requirements 1, Fixed in WP-29 3.
  - ROADMAP.md: 4808 lines (+218). The prototype measured 4766 (+176) with the pre-amendment Appendix D; Appendix D as amended 01oct2026 (PLAN.md §7 S01 item 1 and the ratified answers of both rounds) is 218 lines, 4590 + 218 = 4808. The amended bullets add no heading, `Gaps closed`, `> **DONE` line or Markdown link, so the readers give the same:
    - `_parse_roadmap(r)['WP-29']` → `{'done': False, 'gaps': {}}`;
    - `_parse_roadmap_gaps2(r)['WP-29']` → `{'done': False, 'gaps2': {}}`;
    - `len(_matrix_gaps(r))` → 76, the same as at `7421d3d`.

  `awk '/^## WP-29 /,/^## Traceability matrix/'` finds `Gaps closed` 0 times, and its only `^# |^## ` lines are the two headings.
- **The truth script in StataNow 19.5**, through `scripts/stata_slot.sh <scratch> run_test_wp29_truth.do`.
  - With `WP29_ONLY` unset: `W29-01 PASS: a twoway SVG was written and read (10 texts); dash is loaded`, then `test_wp29_truth: ALL CHECKS PASSED`, with no `r(` error. The block ran from `S01 start 22:27:12` to `S01 end 22:27:13`. `ls -A <scratch>/tmp` was empty afterwards (no work directory or file was left).
  - With `WP29_ONLY=S99`: `test_wp29_truth: no case ran (WP29_ONLY=S99)` and `r(9);`. Before R-03, the same run printed `ALL CHECKS PASSED`.

### Existing tests that pin today's behaviour

None asserts wrong behaviour, so no test is flipped. Three existing assertions change, each with its reason:
- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script`: 66 → 67, the new script;
- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read`: 48 → 49, the new script's `SKIP: Python not available.` gate;
- `test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2` skips exactly the titles `WP29_OPEN` lists.

## User stories

- **US-01.1** As the maintainer, I want every P0 item open in BUGS.md from WP-29's first commit, graded and saying which section closes it, so that the tracking documents tell the truth about what is not yet fixed.
- **US-01.2** As the release manager, I want the release guard to keep refusing every open S1/S2 entry except WP-29's own, and those only while they are open in the WP-29 form, so that the allowance cannot hide a defect.
- **US-01.3** As the developer or agent of a fix section, I want one fixed edit to close my entry (the box, the Resolution line, my `WP29_OPEN` key and my markers), checked by a test, so that I cannot half-close it.
- **US-01.4** As the developer or agent of a fix section, I want one truth script with a gated block per section, runnable alone by `WP29_ONLY=S<NN>`, so that I can measure my section against Stata without running the others'.
- **US-01.5** As the maintainer, I want WP-29 in ROADMAP.md with its requirements, acceptance criteria and P0 traceability before the first fix lands, so that its closure is measured against a written list.

## Business requirements

- **BR-01.1** BUGS.md holds one open entry per P0 entry (21). Each has:
  - the five fields;
  - a title with no `"` that no other entry has;
  - a Resolution that says it is open, why, and which section closes it;
  - exactly one grade, `S1` or `S2` `(WP-29)`;
  - no reference to a test that does not exist.
- **BR-01.2** The full suite is green at S01's commit and at every later WP-29 commit. The release guard's verdict on every entry outside the 21 is unchanged.
- **BR-01.3** Each of these fails a test:
  - an allowance for an entry that is closed, missing or not in the WP-29 open form;
  - an open P0 with no marker;
  - a closed P0 with a marker or without `(WP-29, <id>)` in a closed Resolution;
  - a marker or closing line outside the lists its P0 belongs to;
  - a marker naming no P0.
- **BR-01.4** CHANGELOG.md's current release carries 26 markers in five lists, as `index.md` "P0 coverage" assigns them. One list is the new `### Fixed in WP-29` heading, placed directly above `### Fixed in WP-28`.
- **BR-01.5** ROADMAP.md holds WP-29, not DONE, before the traceability matrix. Its readers' answers for every other package, and the matrix, are unchanged.
- **BR-01.6** The truth script:
  - runs under the certification runner;
  - skips with r(222) only when Stata has no Python;
  - runs one section's block alone under `WP29_ONLY`;
  - fails when no case ran;
  - leaves no file behind.
- **BR-01.7** The forms later sections follow — closing an entry, replacing a marker, appending a truth block, the commit message — are written down once, here (TR-01.10).
- **BR-01.8** No shipped file changes, and nothing outside the seven files of this section is staged.

## Technical requirements

- **TR-01.1 BUGS.md.**
  - **Placement.** Append Appendix A at the end of BUGS.md: one blank line after line 2724, then the 21 entries in P0 order, each separated from the next by one blank line. The file ends with one newline.
  - **Field form.** The five fields are one line each. Field names are exactly as `_FIELD` reads them.
  - **Resolution form.** `Not fixed because WP-29 section NN has not landed. Graded S<n> (WP-29): <why>.` NN is the section in `index.md` "P0 coverage". S1 for all but P0.14 and P0.19 (S2).
  - **Descriptions.** Each quotes the DROPIN-REMAINING.md P0 text and its source ids. P0.10's two pinned cases are not named, so the entry carries no case id (PLAN.md §7.3).
  - **Anchors.** The File Names field gives anchors at `7421d3d`.
- **TR-01.2 The allowance and the readers** (`test/test_tracking_documents.py`, Appendix B).
  - **Placement.** A new banner block appended at the end of the file (after `test_the_traceability_matrix_heading_appears_once`, :1218-1226).
  - **Constants.**
    - `WP29_OPEN`: 21 keys, `"P0.1"` … `"P0.20"` with `"P0.12a"`, `"P0.12b"`, one per line in P0 order, each value the exact title.
    - `WP29_LISTS`: the CHANGELOG lists per id, from `index.md` "P0 coverage". Permanent.
    - `WP29_ALL = tuple(WP29_LISTS)`.
  - **Regexes.** `_WP29_MARKER = <!-- WP-29 (P0\.\d{1,2}[ab]?) -->` and `_WP29_OPEN_FORM`.
  - **Helpers:**
    - `_wp29_markers(text)`;
    - `_changelog_lists(text)` (the newest release's `### ` lists);
    - `_changelog_list(lists, name)` (an exact heading, or one that starts with the name and ` (`; None unless exactly one heading matches);
    - `_wp29_open_problems(open_map, entries)`;
    - `_wp29_marker_problems(open_ids, markers)`;
    - `_wp29_closure_problems(open_ids, markers, entries)`;
    - `_wp29_list_problems(lists_map, changelog)`.

    Each returns a list of problem strings. A document test asserts the list is empty. The unit tests run the helpers on inline text in both directions.
- **TR-01.3 The release guard.** In `test_no_open_entry_is_s1_or_s2` (:503-510), add `allowed = set(WP29_OPEN.values())` and the condition `and e["title"] not in allowed` (Appendix B part 4). Nothing else in `TestNoOpenEntryBlocksARelease` changes. Extend the module docstring with item 8 (Appendix B part 5).
- **TR-01.4 `TestWp29Tracking`** (Appendix B part 3), six tests:
  - `test_every_allowed_title_is_an_open_entry`;
  - `test_an_open_p0_keeps_its_marker`;
  - `test_a_closed_p0_has_no_marker_and_a_resolution`;
  - `test_each_p0_sits_in_its_changelog_lists`;
  - `test_the_marker_reader`;
  - `test_the_wp29_problem_readers`.

  The substring `(WP-29, P0.1)` is not read inside `(WP-29, P0.12a)` or `(WP-29, P0.10)`, and the unit test pins that.
- **TR-01.5 CHANGELOG.md** (Appendix C), five insertions, made bottom-up so the anchors hold:
  1. Above 466: the `### Fixed in WP-29` heading, its sentence and 3 markers.
  2. After 464: 1 marker, at the end of `### Requirements`.
  3. After 437: 4 markers, at the end of `### Changed behaviour`.
  4. After 272: 5 markers, at the end of `### Security`.
  5. After 236: the group line `**WP-29 (drop-in P0, 30sep2026)**` and 13 markers, at the end of `### Results that change`.

  Markers are separated by blank lines (R-02). No WP-29 line is written here; lines are the closing commits'.
- **TR-01.6 ROADMAP.md** (Appendix D). Insert WP-29 after line 4447 (the blank line after the `---` at 4446) and before `## Traceability matrix` (4448). It ends with `---` and a blank line.
  - **Heading:** `## WP-29 · Close the drop-in P0 gaps`, with no `— DONE`.
  - **Header line:** `**GAPS2 closed:** (filled at closeout) · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28`.
  - **Body:** the user story, BR-29.1-16 (PLAN.md §6), TR-29.1-4 (pointing at `.ultraplan/wp29/`), AC-29.1-12 (PLAN.md §9 E1-E12), a test plan, and a `#### P0 traceability` table of 21 rows.
  - **Forbidden inside WP-29:** any line beginning `# ` or `## ` except its own heading; the strings `Gaps closed` and `## Traceability matrix`; any Markdown link to a file named `PLAN.md` or `TODO.md` (`test_nothing_links_them`, :973). Paths go in backticks only.
- **TR-01.7 The truth script** `test/test_wp29_truth.cscript` (Appendix E). It is the WP-28 frame with:
  - its own gate `if `"`c(python_exec)'"' == "" { … exit 222 }` (so it carries the `SKIP: Python not available.` line the hygiene pin counts);
  - `_w29_expect`/`_w29_done`, which count closed cases in `$w29_ncase`;
  - a fresh work directory from `tempfile w29_base` (`mkdir` failure → exit 9; removed by `capture rmdir` in the summary);
  - block S01 (case `W29-01`): `cert_svg_export` and `cert_svg_texts` on `twoway scatter mpg weight`, and `_dash_serve` defined. Every file it writes is erased (`r(file)` and `r(list)`);
  - the marker;
  - a summary that exits 9 when `$w29_ncase == 0` or a case failed.

  No `capture python:` import probe (the import-probe pin stays 13).
- **TR-01.8 Runner.** Insert Appendix F after line 1741 (block 67's closing `}`): block `// 68.`, the form of block 67, naming `test_wp29_truth.cscript`.
- **TR-01.9 Hygiene** (`test/test_cscript_hygiene.py`, Appendix G):
  - the pin 66 → 67 (:295) and the pin 48 → 49 (:313), with their comments;
  - appended at the end of the file:
    - a banner;
    - `_WP29_TRUTH`, `_W29_OPEN`, `_W29_CLOSE`, `_W29_MARK`;
    - `_wp29_blocks(src)`, which returns `(blocks, problems)`. The problems are: a marker not there exactly once; a block not closed by its own end line; a block not gated by its own section; a block below the marker; a block out of section order (non-decreasing, so one section may own two blocks);
    - `TestTheWp29TruthScript` with `test_the_scaffold_is_in_order`, `test_every_block_is_gated_closed_and_in_section_order` and `test_the_block_reader`.
- **TR-01.10 The forms every fix section follows.** These are the binding WP-29 forms of BRIEF's D1-D3, per `index.md` "Deltas".
  1. **Closing an entry, in place, in the fix commit.**
     - On the entry's title line, change `- [ ] Title:` to `- [x] Title:`, keeping the title.
     - Replace the whole Resolution line with `  - Resolution: Fixed <ddmonyyyy> (WP-29, P0.<n>). <what changed, where, both renderers>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-29): <what and why>.]`
     - Delete the entry's `WP29_OPEN` key line in the same commit.
     - Exactly one P0 id per parenthesis: never `(WP-29, P0.12b, P0.14)`.
     - Name only tests that exist in that commit.
  2. **Replacing a marker.**
     - Each `<!-- WP-29 P0.<n> -->` is replaced in place by one `- …` item ending `(WP-29, P0.<n>)`, one id per item.
     - A Results item names the command, the old value (from the saved failure text) and the new value.
     - Nothing is added anywhere else.
     - P0.13 (two commits): the F2 commit may replace either of its two markers and keeps the entry open and its key. The F4 commit replaces the other, closes the entry and deletes the key. `TestWp29Tracking` accepts both orders.
  3. **A truth block.** It goes into `test/test_wp29_truth.cscript` above the marker, after the last block whose section number is not greater than the section's own, in this form:

     ```
     * ==== S<NN> P0.<n>: <what> ====
     local only : env WP29_ONLY
     if inlist("`only'", "", "S<NN>") {
         display as text "S<NN> start `c(current_time)'"
         ... cases: _w29_expect <ID> "(<cond>)" "<msg>" ... _w29_done <ID> "<what passed>"
         ... erase every file the block wrote, under `w29_work'
         display as text "S<NN> end `c(current_time)'"
     }
     * ==== end S<NN> ====
     ```

     - Case ids use the manifest prefix (JO, UL, ET, FX, DU, KD, HX, QF, CQV, PF, LC, PEP, AX, BSC, LW, LB, SCU, EW, TOK, ER).
     - The header comment's block list gains one line.
  4. **The commit message.**
     - **Subject:** a sentence ending `(WP-29 P0.<n>)`, or the variants of `index.md` A10.
     - **Body:** it opens with the saved failure text. Then the measured defect, then what changed and where. Then one line each:
       - `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`;
       - `Flipped: <node> -- <old expectation> was wrong because <why>`;
       - `Fixture: test/fixtures/<name>.json (scripts/<extract>.do)`;
       - `BUGS.md: "<title>" (closed)`.
     - No reference to any AI tool or vendor, and no co-author trailer (CLAUDE.md rule 6 overrides any harness default). Grep the message for `claude|anthropic` before and after committing.
- **TR-01.11 Security (rule 1).**
  - The readers use anchored regular expressions on repository text. They run no subprocess, no `eval` and no `shell=True`.
  - The truth script interpolates no file content into a macro.
  - It writes only under a work directory it has just created and that did not exist before.
  - It echoes no user text.
  - The allowance is closed-world. Only titles in `WP29_OPEN` are exempt, only while each matches `_WP29_OPEN_FORM`, and S15 empties it.

## Boundaries

- Do not change any shipped file: `dash.ado`, `dash_parse.mata`, `dash_render.py`, `dash.sthlp`, `dash_setup.*`, `dash.pkg`, `stata.toc`, the schemes.
- Do not stage the following:
  - `CLAUDE.md` or `.gitignore` (the maintainer's uncommitted edits);
  - `.ultraplan/` (the plan: step 0a commits `.ultraplan/wp29/` on `wp29-p0` before any worktree is cut, round 2 answer C; no section commit stages a plan file);
  - `.gitnexus/`;
  - `TWOWAY_COVERAGE_AUDIT.md` (step 0a's);
  - any scratch file or `*.html`.
- Do not edit:
  - GAPS2.md, GAPS.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md or AGENTS.md (A5: S15 only);
  - `test/test_gaps2_truth.cscript` (S06 only flips AL-19) or `test/test_svg_truth.py`;
  - the import-probe pin (:322, S09's);
  - `test/test_packaging.py` (step 0a's).
- Do not:
  - mark WP-29 DONE;
  - fill `**GAPS2 closed:**`;
  - write `**Gaps closed:**`;
  - write any CHANGELOG line other than markers, the group line and the `### Fixed in WP-29` sentence.
- Do not close, reword or regrade any existing BUGS.md entry. Do not rename or delete any test.
- Do not run `make cert`, `make gate` or a second full suite (rule 11). Do not run Stata other than through `scripts/stata_slot.sh`.

## Stata truth

- **What this section adds.** No fixture and no extract script. The section adds the truth script itself and one smoke block:
  - block `S01`, case `W29-01`;
  - `twoway scatter mpg weight` on `sysuse auto`, exported to SVG by `cert_svg_export` and read by `cert_svg_texts`;
  - pass condition: `r(rc) == 0`, the file exists, `r(n) > 0` (measured: 10), and `_dash_serve` is defined.
- **The driver** (index.md "The cscript driver", with the do-file opening `adopath ++` per this package's Stata rule). `<W>` is the worktree root:

  ```sh
  W=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s01
  printf 'adopath ++ "%s/"\ncd "%s/test"\ndo "%s/test/%s"\n' "$W" "$W" "$W" test_wp29_truth.cscript > <scratch>/run_test_wp29_truth.do
  cd "$W" && dash_nobrowser=1 scripts/stata_slot.sh <scratch> <scratch>/run_test_wp29_truth.do      # log: <scratch>/run_test_wp29_truth.log
  ```

- **Measured runtime.** About 1 s for block S01 (`S01 start 22:27:12`, `S01 end 22:27:13`). S15 times blocks from these lines.

## TDD test stubs

Every stub was run on the prototype; the "fails at base" text is what was measured there.

**Regression tests.** They are written first by 01-01 and fail at the step-0c sha.

- Test: `test/test_tracking_documents.py::TestWp29Tracking::test_every_allowed_title_is_an_open_entry` — `_wp29_open_problems(WP29_OPEN, entries) == []`. Fails at base with `NameError: name '_wp29_open_problems' is not defined`. With the helpers but no entries, it fails with `P0.1: 0 BUGS.md entries are titled …`.
- Test: `…::TestWp29Tracking::test_an_open_p0_keeps_its_marker` — every open id has a marker, and every marker names a WP-29 id. Fails with `NameError` (`_wp29_marker_problems`), then with `P0.1 is open and CHANGELOG.md holds no marker for it`.
- Test: `…::TestWp29Tracking::test_a_closed_p0_has_no_marker_and_a_resolution` — a closed id has no marker, and a closed entry's Resolution holds `(WP-29, <id>)`. Fails with `NameError` (`_wp29_closure_problems`). It is vacuous on the documents while all 21 are open; its inline cases live in `test_the_wp29_problem_readers`.
- Test: `…::TestWp29Tracking::test_each_p0_sits_in_its_changelog_lists` — `WP29_ALL == tuple(WP29_LISTS)` and has length 21; each list holds the id's marker or a line ending `(WP-29, <id>)`; no marker sits elsewhere. Fails with `NameError` (`WP29_LISTS`), then with `CHANGELOG.md has no single '### Fixed in WP-29' list`.
- Test: `…::TestWp29Tracking::test_the_marker_reader` — `_wp29_markers` and `_changelog_lists`/`_changelog_list` on inline text: repeats kept, a WP-28 marker and a malformed one not read, only the newest release read, the `(may need …)` heading suffix matched, a missing list giving `None`. Fails with `NameError` (`_wp29_markers`).
- Test: `…::TestWp29Tracking::test_the_wp29_problem_readers` — the four problem helpers on inline entries and text, each problem kind reported and the good case clean, including that `(WP-29, P0.1)` is not read inside `(WP-29, P0.12a)` or `(WP-29, P0.10)`. Fails with `NameError` (`_wp29_open_problems`).
- Test: `test/test_cscript_hygiene.py::TestTheWp29TruthScript::test_the_scaffold_is_in_order` — `cscript "WP-29 truth`, `SKIP: Python not available.`, `do "cert_helpers.do"`, `do "cert_svg.do"`, `* ==== S01 `, `local only : env WP29_ONLY`, `* ==== end S01 ====`, the marker and `test_wp29_truth: ALL CHECKS PASSED` all appear, in that order, and there is no `capture python:`. Fails with `NameError: name '_WP29_TRUTH' is not defined`.
- Test: `…::TestTheWp29TruthScript::test_every_block_is_gated_closed_and_in_section_order` — `_wp29_blocks(script)` reports no problem and the first block is S01. Fails with `NameError` (`_wp29_blocks`).
- Test: `…::TestTheWp29TruthScript::test_the_block_reader` — a good two-block text gives `[("S01", 2, 6), ("S10", 7, 11)]` with no problem. Six mutations are each reported: not gated, never closed, not closed before, section order, marker appears 0 times, below the marker. Fails with `NameError` (`_W29_MARK`).

**Pin moves.** They fail at base once the pins move, and pass when the script exists.
- Test: `…::TestTheChecksReachEveryScript::test_the_glob_finds_every_script` — 67. Fails with `assert 66 == 67`.
- Test: `…::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read` — 49. Fails with `assert 48 == 49`.

**Guards already green that S01 must keep green** (listed so the executor runs them):
- `test_tracking_documents.py`: every pre-existing test, notably `TestNoOpenEntryBlocksARelease`, `TestEveryOpenEntrySaysWhyItIsOpen`, `TestEveryBugsEntryIsWellFormed`, `TestEveryClosedEntryNamesATestThatExists`, `TestGaps2AndRoadmapAgree` and `TestTodoAndPlanAreRetired`;
- `test/test_cert_verdict.py::TestTheRegisteredScripts::test_the_real_runner_registers_every_script_in_test`;
- `test/test_version_floor.py`;
- `test/test_svg_truth.py`;
- `test/test_test_integrity.py` (the new tests assert, catch nothing and return early nowhere).

Pinned tests to flip: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| 21 open entries in the WP-29 form, allowance exact | pytest `TestWp29Tracking::test_every_allowed_title_is_an_open_entry` | BUGS.md | n/a |
| Release guard exempts only `WP29_OPEN`'s titles | pytest `TestNoOpenEntryBlocksARelease` (3 tests) + the inline cases of `test_the_wp29_problem_readers` | BUGS.md, inline | n/a |
| Markers: present while open, gone when closed, in their lists only | pytest `test_an_open_p0_keeps_its_marker`, `test_a_closed_p0_has_no_marker_and_a_resolution`, `test_each_p0_sits_in_its_changelog_lists` | CHANGELOG.md | n/a |
| Readers and problem helpers, both directions | pytest `test_the_marker_reader`, `test_the_wp29_problem_readers` | inline | n/a |
| ROADMAP readers unchanged; WP-29 open; matrix 76 | pytest `test_tracking_documents.py` (all) + the 01-05 hazard greps | ROADMAP.md | n/a |
| Requirements range still holds the floor | pytest `test/test_version_floor.py` | CHANGELOG.md | n/a |
| Truth-script layout, gating, order, marker | pytest `TestTheWp29TruthScript` (3) | the script, inline | n/a |
| New script obeys every per-script rule and is registered | pytest `test_cscript_hygiene.py` (all), `test_cert_verdict.py` | the script, runner | n/a |
| Scaffold runs in Stata; gating; "no case ran" | cscript through the driver: `W29-01 PASS` with `WP29_ONLY` unset; `no case ran` and `r(9)` with `WP29_ONLY=S99` | auto | n/a (Stata only) |
| Nothing else broke | `python3 -m pytest test/ -q` once (01-08) | — | — |

**Acceptance criteria.**

- **AC-01.1 BUGS.md.**
  - `grep -c '^- \[ \] Title:' BUGS.md` prints 25 (4 + 21).
  - `wc -l < BUGS.md` prints 2850.
  - `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes 40 tests (34 + 6) with none skipped.
- **AC-01.2 Release guard.**
  - On the S01 tree, `test_no_open_entry_is_s1_or_s2` passes.
  - Removing one title from `WP29_OPEN` makes both it and `test_every_allowed_title_is_an_open_entry` fail.
  - Closing one entry without deleting its key makes `test_every_allowed_title_is_an_open_entry` fail ("is closed; delete its WP29_OPEN key").

  Checked by hand in 01-02's verify, then reverted.
- **AC-01.3 CHANGELOG.md.**
  - `grep -c '<!-- WP-29 ' CHANGELOG.md` prints 26.
  - Per list: Results 13, Security 5, Changed behaviour 4, Requirements 1, Fixed in WP-29 3.
  - `grep -c '^### Fixed in WP-29$'` prints 1, and so does `grep -c '^\*\*WP-29 (drop-in P0, 30sep2026)\*\*$'`.
- **AC-01.4 ROADMAP.md.**
  - `grep -c '^## WP-29 ' ROADMAP.md` prints 1, and `grep -c '## Traceability matrix'` prints 1.
  - WP-29 is not DONE, its GAPS2 field yields `{}`, and its `#### P0 traceability` table has 21 rows.
- **AC-01.5 Truth script.**
  - `test/test_wp29_truth.cscript` is registered as block 68.
  - The driver run prints `W29-01 PASS` and `test_wp29_truth: ALL CHECKS PASSED`, with no `r(` error and nothing left in `<scratch>/tmp`.
  - `WP29_ONLY=S99` ends `r(9)` with `no case ran`.
  - `test_cscript_hygiene.py` passes 367 tests.
- **AC-01.6 The commit.**
  - The full suite is green once, in the worktree.
  - One commit is made on `wp29-s01`. Its subject ends `(WP-29 S01)`, and it holds exactly the seven files of this section.
  - Its message matches no `claude|anthropic`.
  - The merger lands it on `wp29-p0` before the worktrees of 02-09 are cut.

## Tasks

Commit boundary: **one commit (S01)**, holding 01-01 to 01-07, made by 01-08 on branch `wp29-s01` in the worktree `<W>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s01`. The worktree is created by `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash worktree add <W> -b wp29-s01 wp29-p0` after step 0a.
- **`<scratch>`** is the orchestrator's session scratch directory for this section (for example `<session scratchpad>/wp29/s01-run`, created with `mkdir -p`).
- **`<base>`** is `cat <scratch-of-step-0>/batch-1-base.txt` (the step-0c sha).
- **Shell.** Every shell command below starts with `cd <W> &&` because the agent's cwd resets between calls.
- **No commit before 01-08.** A red tree is never committed (rule 4). No Stata runs except 01-07's driver run. No AI references anywhere.

<task type="auto" id="01-01">
  <name>Write the failing tracking and hygiene tests</name>
  <files>test/test_tracking_documents.py, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
In `<W>/test/test_tracking_documents.py`, append Appendix B part 3 (`class TestWp29Tracking` with its six tests, verbatim) at the end of the file, after `test_the_traceability_matrix_heading_appears_once` (:1218-1226), preceded by two blank lines. Do NOT add the constants or helpers yet.
In `<W>/test/test_cscript_hygiene.py`, make Appendix G part 1's two pin edits (:284-295 and :309-313), and append Appendix G part 2's class `TestTheWp29TruthScript` only (not its banner, constants or `_wp29_blocks`) at the end of the file (after :870), preceded by two blank lines.
Run `cd <W> && python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider 2>&1 | grep -E '^(FAILED|E   )|passed|failed' > <scratch>/01-S01-failure.txt`. Prefix that file with the line `S01 tests at <base>:`.
Do not commit. This text opens the section's commit body (TR-01.10.4).
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/01-S01-failure.txt` reads `11 failed, 413 passed` (the run collects 40 + 362 + 22 = 424 tests; measured on the prototype as `11 failed, 412 passed, 1 skipped`, the skip being `test_a_closing_commit_exists`, which runs in a git checkout). The FAILED lines are exactly the 11 nodes listed in Evidence "Prototype / Red first". `grep -c NameError <scratch>/01-S01-failure.txt` is at least 9, and the file holds `assert 66 == 67` and `assert 48 == 49`. `cd <W> && git status --porcelain` shows only ` M test/test_cscript_hygiene.py` and ` M test/test_tracking_documents.py`; `git log -1 --format=%h` equals `<base>` abbreviated.]]></verify>
  <done>The eleven new or moved tests existed and failed for their recorded reasons on the unmodified tree, every other test in the three files passed, the failure text was saved, and nothing was committed.</done>
</task>

<task type="auto" id="01-02">
  <name>Add the WP-29 readers and the allowance</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
**GitNexus first** (CLAUDE.md).
1. Call `gitnexus_list_repos()`. If no repo named `dash` with path `/Users/billy/Desktop/Programs/StataPrograms/d/dash` is listed (at plan time it was not), run `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && gitnexus analyze` in the MAIN checkout, never in `<W>`. The main checkout's uncommitted `.gitignore` ignores `.gitnexus`; nothing it writes is ever staged.
2. Call `gitnexus_impact({target: "test_no_open_entry_is_s1_or_s2", direction: "upstream", repo: "dash", includeTests: true, file_path: "test/test_tracking_documents.py"})` and record the risk and direct callers in `<scratch>/01-impact.txt`. The expected result is LOW with no caller other than pytest collection. Report HIGH or CRITICAL to the maintainer before editing.

**Then, in `<W>/test/test_tracking_documents.py`:**
1. Insert Appendix B parts 1-2 (the banner, `WP29_OPEN`, `WP29_LISTS`, `WP29_ALL`, `_WP29_MARKER`, `_WP29_OPEN_FORM` and the seven helpers) directly above `class TestWp29Tracking`.
2. Replace the first three lines of `test_no_open_entry_is_s1_or_s2`'s body (:504-506) with Appendix B part 4.
3. Insert Appendix B part 5 (docstring item 8) after the docstring line `line is listed by its package.` (:36).
4. Run the file.

Hand-check AC-01.2 in a throwaway edit, reverted before the next task:
- delete the `"P0.1"` line from `WP29_OPEN` → `test_no_open_entry_is_s1_or_s2` fails naming line 2726 once 01-03 is done;
- before 01-03, the test to watch is `test_every_allowed_title_is_an_open_entry`.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `3 failed, 37 passed`. The three failures are exactly `test_every_allowed_title_is_an_open_entry` (first E line `P0.1: 0 BUGS.md entries are titled "line, connected, ...`), `test_an_open_p0_keeps_its_marker` (`P0.1 is open and CHANGELOG.md holds no marker for it`) and `test_each_p0_sits_in_its_changelog_lists` (`CHANGELOG.md has no single '### Fixed in WP-29' list`). `test_the_marker_reader`, `test_the_wp29_problem_readers`, `test_a_closed_p0_has_no_marker_and_a_resolution` and all three `TestNoOpenEntryBlocksARelease` tests pass. `<scratch>/01-impact.txt` exists.]]></verify>
  <done>The allowance, the permanent id-to-list map and the seven helpers existed, the release guard skipped exactly the allowed titles, the reader unit tests passed, and only the three document checks still failed, for want of entries and markers.</done>
</task>

<task type="auto" id="01-03">
  <name>Open the 21 P0 entries in BUGS.md</name>
  <files>BUGS.md</files>
  <action><![CDATA[
Append Appendix A to `<W>/BUGS.md`, byte for byte (the 21 entries, P0 order):
- after the current last line (2724, the colorlevels entry's Resolution), add one empty line;
- then the 21 entries, with one empty line between consecutive entries;
- the file ends with a single newline.

Write it with a here-document or Python, not by retyping. Check before saving:
- no title holds `"`;
- no entry names a `test_*` file, a `file::node` or a `Test...` word;
- each field is one line beginning with two spaces and `- `.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '^- \[ \] Title:' BUGS.md` prints 25; `wc -l < BUGS.md` prints 2850; `tail -c 1 BUGS.md | xxd -p` prints `0a` and `tail -c 2 BUGS.md | xxd -p` is not `0a0a`; `grep -n '^- \[ \] Title: line, connected' BUGS.md` prints `2726:...`. `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `2 failed, 38 passed`; the two are `test_an_open_p0_keeps_its_marker` and `test_each_p0_sits_in_its_changelog_lists`. `TestEveryBugsEntryIsWellFormed`, `TestEveryClosedEntryNamesATestThatExists`, `TestEveryOpenEntrySaysWhyItIsOpen` and `TestNoOpenEntryBlocksARelease` pass.]]></verify>
  <done>BUGS.md held the 21 WP-29 entries, open, graded, well formed and exempt from the release guard only through the allowance.</done>
</task>

<task type="auto" id="01-04">
  <name>Place the 26 CHANGELOG markers</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[
In `<W>/CHANGELOG.md`, make Appendix C's five insertions bottom-up, so the line numbers hold:
1. C.5 directly above line 466 (`### Fixed in WP-28`).
2. C.4 after line 464.
3. C.3 after line 437.
4. C.2 after line 272.
5. C.1 after line 236.

Before inserting, assert the anchor lines' text:
- 236 `  (follow-up to GAPS2 X2)`, 238 `### Security`;
- 272 `  CSV injection. (WP-21)`, 274 `### New`;
- 437 ends `(WP-28, G2)`, 439 `### Removed`;
- 464 ends `(WP-28, K2)`, 466 `### Fixed in WP-28`.

Stop and report if any differs. Write no WP-29 line other than the group line, the heading and its sentence.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '<!-- WP-29 ' CHANGELOG.md` prints 26. The per-list counts each pipe the range into `grep -c '<!-- WP-29 '`:
- `awk '/^### Results that change/,/^### Security/' CHANGELOG.md` → 13
- `awk '/^### Security/,/^### New/' CHANGELOG.md` → 5
- `awk '/^### Changed behaviour/,/^### Removed/' CHANGELOG.md` → 4
- `awk '/^### Requirements/,/^### Fixed in WP-29/' CHANGELOG.md` → 1
- `awk '/^### Fixed in WP-29/,/^### Fixed in WP-28/' CHANGELOG.md` → 3

`grep -c '^### Fixed in WP-29$' CHANGELOG.md` prints 1, `grep -c '^\*\*WP-29 (drop-in P0, 30sep2026)\*\*$' CHANGELOG.md` prints 1, and `wc -l < CHANGELOG.md` prints 682. `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed (40 tracking tests passing).]]></verify>
  <done>CHANGELOG.md held one marker per P0 list cell, 26 in all, in the five lists of the current release, and every tracking test passed.</done>
</task>

<task type="auto" id="01-05">
  <name>Open WP-29 in ROADMAP.md</name>
  <files>ROADMAP.md</files>
  <action><![CDATA[
1. Assert the anchors: line 4446 of `<W>/ROADMAP.md` is `---`, 4447 is empty and 4448 is `## Traceability matrix`.
2. Insert Appendix D's text (from `## WP-29 · Close the drop-in P0 gaps` through its closing `---` and the empty line after it) between 4447 and 4448, so `## Traceability matrix` follows it directly.
3. Check the hazards before saving:
   - inside WP-29 no line begins `# ` or `## ` other than its heading;
   - neither `Gaps closed` nor `## Traceability matrix` occurs in the inserted text;
   - the heading has no `— DONE`;
   - no Markdown link names `PLAN.md` or `TODO.md`.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '^## WP-29 ' ROADMAP.md` prints 1, `grep -c '## Traceability matrix' ROADMAP.md` prints 1, and `wc -l < ROADMAP.md` prints 4808 (4590 at `7421d3d` plus Appendix D's 218 lines as amended 01oct2026, rounds 1 and 2).

Hazard checks on `awk '/^## WP-29 /,/^## Traceability matrix/' ROADMAP.md`:
- piped into `grep -c 'Gaps closed'` → 0;
- piped into `grep -c '^| P0\.'` → 21;
- piped into `grep -c '^# \|^## '` → 2.

`python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; r=open('ROADMAP.md').read(); print(t._parse_roadmap(r)['WP-29'], t._parse_roadmap_gaps2(r)['WP-29'], len(t._matrix_gaps(r)))"` prints `{'done': False, 'gaps': {}} {'done': False, 'gaps2': {}} 76`. `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `40 passed`.]]></verify>
  <done>ROADMAP.md held WP-29 open, before the traceability matrix, with its requirements, criteria and 21-row P0 table, and every reader returned what it returned before for every other package.</done>
</task>

<task type="auto" id="01-06">
  <name>Create the truth-script scaffold and its reader</name>
  <files>test/test_wp29_truth.cscript, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
Create `<W>/test/test_wp29_truth.cscript` with Appendix E's text, verbatim:
- the header;
- the gate;
- the helpers;
- the fresh work directory;
- block S01 (W29-01);
- the marker;
- the summary with the no-case guard.

In `<W>/test/test_cscript_hygiene.py`, insert Appendix G part 2's banner, constants (`_WP29_TRUTH`, `_W29_OPEN`, `_W29_CLOSE`, `_W29_MARK`) and `_wp29_blocks` directly above `class TestTheWp29TruthScript`. Run the two hygiene-related files.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `1 failed, 366 passed`. The one failure is `TestEveryCscriptIsWiredIntoTheRunner::test_the_runner_calls_it[test_wp29_truth.cscript]` ("exists but run_all_cscripts.do never runs it"), which 01-07 fixes. `TestTheWp29TruthScript` (3) and both moved pins pass. `python3 -m pytest test/test_cert_verdict.py -q -n0 -p no:cacheprovider` fails only `test_the_real_runner_registers_every_script_in_test`. `grep -c 'capture python' test/test_wp29_truth.cscript` prints 0.]]></verify>
  <done>The truth script existed in WP-28's frame with a gated, closed S01 block above its marker, and every hygiene rule held except registration in the runner.</done>
</task>

<task type="auto" id="01-07">
  <name>Register block 68 and run it</name>
  <files>test/run_all_cscripts.do</files>
  <action><![CDATA[
1. In `<W>/test/run_all_cscripts.do`, assert line 1741 is `}` and lines 1743-1744 are the `// ----` / `// Summary` banner.
2. Insert Appendix F after line 1741, so the result is block 67, one empty line, block 68, one empty line, `// Summary`.
3. Run the hygiene and verdict files.
4. Run the scaffold in Stata through the driver of "Stata truth" twice:
   - once with `WP29_ONLY` unset;
   - once with `WP29_ONLY=S99` into a second scratch directory `<scratch>/s99`, with the driver copied there.

Each run goes through `scripts/stata_slot.sh` only, never the GUI or a bare stata-mp. If the first run SKIPs (r(222)), `c(python_exec)` was dropped from `~/.stata19/console/stata19.rc`, and a skip is not a pass: restore the link and rerun.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_cscript_hygiene.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed (367 hygiene tests passing). `grep -c 'do "test_wp29_truth.cscript"' test/run_all_cscripts.do` prints 1.

In `<scratch>/run_test_wp29_truth.log`:
- `grep -c '^W29-01 PASS'` prints 1;
- `grep -c '^  test_wp29_truth: ALL CHECKS PASSED'` prints 1;
- `grep -c '^r([0-9]*);'` prints 0.

`ls -A <scratch>/tmp` prints nothing.

In `<scratch>/s99/run_test_wp29_truth.log`:
- `grep -c 'no case ran (WP29_ONLY=S99)'` prints at least 1;
- `grep -c '^r(9);'` prints at least 1;
- `grep -c '^W29-01 PASS'` prints 0.]]></verify>
  <done>The runner ran the new script as block 68, the scaffold passed W29-01 in StataNow, ran one block alone under WP29_ONLY, failed when a gate named no block, and left no file behind.</done>
</task>

<task type="auto" id="01-08">
  <name>Run the gates and commit S01</name>
  <files>none</files>
  <action><![CDATA[
**1. Merge main.** Run `cd <W> && git merge --no-edit main` (rule 4; expected `Already up to date.`; if main moved, stop and report to the orchestrator).

**2. The changed files.** Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_version_floor.py test/test_svg_truth.py test/test_test_integrity.py -q -n0 -p no:cacheprovider`.

**3. The full suite, once.** Run `python3 -m pytest test/ -q > <scratch>/01-full.log 2>&1` in the background and read the log when it exits. Never launch a second run to check on it. If it is refused with "a full test-suite run is already in progress", another section holds `/tmp/dash-full-suite-<uid>.lock`: wait for it (Monitor until `lsof /tmp/dash-full-suite-$(id -u).lock` is empty), then launch once.

**4. Stage the seven paths by name, never `-A`:**
- `git add BUGS.md CHANGELOG.md ROADMAP.md test/test_tracking_documents.py test/test_cscript_hygiene.py test/run_all_cscripts.do test/test_wp29_truth.cscript`.
- `git diff --cached --name-only` must list exactly those seven.
- `git status --porcelain` may also show `?? .gitnexus/` or nothing else unstaged.

**5. Scope (G6).** Run `gitnexus_detect_changes({scope: "compare", base_ref: "<base>", repo: "dash"})` if the index can see this tree. If the tool reads only the main checkout, record that and rely on the name-only check. The merger repeats `gitnexus_detect_changes({scope: "staged"})` in the main checkout before landing.

**6. Commit message.** Write it to `<scratch>/01-commit-msg.txt` from the template in Notes, opening with `<scratch>/01-S01-failure.txt`. Run `grep -Eic 'claude|anthropic' <scratch>/01-commit-msg.txt` (expect 0).

**7. Commit and hand off.** Run `git commit -F <scratch>/01-commit-msg.txt`, then `git log -1 --format=%B | grep -Eic 'claude|anthropic'` (expect 0). Record the sha in `<scratch>/01-sha.txt` for the merger. The merger lands it on `wp29-p0` first in batch 1 (`format-patch -1 | patch -p1`, `git add` the seven paths, `git commit -F` the same message), then re-records `batch-1-base.txt` and cuts the worktrees of 02-09 (R-05).
  ]]></action>
  <verify><![CDATA[The targeted run reports 0 failed. `tail -1 <scratch>/01-full.log` reports 0 failed and 0 errors. `cd <W> && git log -1 --format=%s` ends `(WP-29 S01)`. `git show --stat --format= HEAD | tail -1` reports 7 files changed. `git show --name-only --format= HEAD | sort` lists exactly BUGS.md, CHANGELOG.md, ROADMAP.md, test/run_all_cscripts.do, test/test_cscript_hygiene.py, test/test_tracking_documents.py, test/test_wp29_truth.cscript. `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0. `git log -1 --format=%b | head -1` prints `S01 tests at <base>:` (the body opens with the saved failure text). `git status --porcelain -- BUGS.md CHANGELOG.md ROADMAP.md test` is empty.]]></verify>
  <done>One green commit on wp29-s01 held the entries, the allowance and its tests, the markers, WP-29 in ROADMAP, the truth script, its runner block and its hygiene guard, with a message free of AI references, ready for the merger to land first.</done>
</task>

## Section completion criteria

- One commit on `wp29-s01`, subject ending `(WP-29 S01)`, made after one green full run. It holds exactly the seven files. No test-only commit exists, and no message names an AI tool or vendor.
- BUGS.md holds 21 open WP-29 entries (Appendix A). `WP29_OPEN` holds their 21 titles. `WP29_LISTS`/`WP29_ALL` are permanent. `TestWp29Tracking` (6) and the release-guard exemption are in place. `test_tracking_documents.py` passes 40 tests.
- CHANGELOG.md holds the 26 markers (13 + 5 + 4 + 1 + 3), the WP-29 group line and the `### Fixed in WP-29` heading.
- ROADMAP.md holds WP-29, open, before the matrix. The readers are unchanged for every other package.
- `test/test_wp29_truth.cscript` is registered as block 68 and passes `W29-01` in StataNow. `TestTheWp29TruthScript` (3) passes. The pins read 67 and 49. `test_cscript_hygiene.py` passes 367 tests.
- The forms of TR-01.10 are recorded for sections 02-15.
- The merger landed the commit on `wp29-p0` before the worktrees of 02-09 were cut.

## Notes

- **Merging (R1, R3).**
  - **BUGS.md.** Each later section changes, in place, only its entry's title-line box and its Resolution line.
  - **CHANGELOG.md.** Each later section changes, in place, only its own marker line(s).
  - **`test_tracking_documents.py`.** Each later section deletes only its own `WP29_OPEN` line.
  - **Why the blank lines.** With entries and markers blank-separated (R-02), a hunk whose neighbour was already rewritten by another section still applies with `patch`'s default fuzz. The innermost context line is the blank one.
  - **`WP29_OPEN`.** The keys are one per line, so two adjacent deletions conflict only in context. The merger applies both by hand and keeps every other key.
  - **Never resolve by dropping a line.**
- **Truth blocks under parallel merges.** In a worktree, a section's block goes directly above the marker (only S01's block is there). When the merger lands sections in merge order (S09, S03, S02, …), a lower-numbered section's block can land below a higher-numbered one. `TestTheWp29TruthScript::test_every_block_is_gated_closed_and_in_section_order` then fails at G8. The merger moves the block up to its section-number place; that is the fix, never reordering the check. A section with two P0s may own two blocks, e.g. S10's P0.5 then P0.2.
- **P0.12b and P0.14** close in one commit, `(WP-29 P0.12b, P0.14)`, as two entries, two Resolutions, two key deletions and two marker replacements. Each carries its own `(WP-29, P0.12b)` / `(WP-29, P0.14)`.
- **P0.13** has two commits. The F2 commit replaces one of its markers and leaves the entry open with its key. The F4 commit replaces the other, closes the entry and deletes the key. The tests accept either marker first.
- **A closed entry keeps its title.** S15 quotes it in GAPS2 Tracked lines, and the title holds no `"`.
- **`_CASE_ID` and source ids.**
  - A source id such as `AUDIT-08`, `REM-08-05-C3b` or `WP-29` matches `_CASE_ID`, but a case id is only ever "found" or ignored, never dangling (test_tracking_documents.py:325-328). Source ids in a Description are therefore safe.
  - A `test_*.py`/`.cscript` name or `Test…` word that does not exist is not safe: `test_no_entry_names_a_test_that_does_not_exist` fails.
- **`.gitnexus/`.** The worktree's `.gitignore` (committed text) does not ignore `.gitnexus`. Never run `gitnexus analyze` in `<W>`, and never stage with `-A`/`.`. Not measured: whether files under `.gitnexus/` in the main checkout trip `test_nothing_links_them` (it walks every directory except `.git`, `.claude`, `__pycache__`, `.pytest_cache`, `node_modules`). If a full run there fails on a `.gitnexus/` path, stop and report it to the maintainer rather than editing the walker in this section.
- **Python linkage.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, after which the script SKIPs (r(222)). A SKIP is not a pass. `scripts/stata_slot.sh` caps sessions at three.
- **Commit message template** (01-08; TR-01.10.4):

  ```
  Open the WP-29 P0 entries, markers and truth script (WP-29 S01)

  <the contents of <scratch>/01-S01-failure.txt>

  WP-29 closes the 20 P0 items of the drop-in re-audit of 357c368
  (.ultraplan/handoff/DROPIN-REMAINING.md section 3). This opens them:
  21 BUGS.md entries (P0.12 as P0.12a and P0.12b), open and graded S1 (19)
  and S2 (2) in the form "Not fixed because WP-29 section NN has not
  landed"; the WP29_OPEN allowance, which alone exempts those titles from
  the release guard while each stays in that form; WP29_LISTS, the
  CHANGELOG lists each P0 belongs in, with 26 markers placed in the five
  lists of the 0.1.0 release and a new "Fixed in WP-29" heading; WP-29 in
  ROADMAP.md, open; and test/test_wp29_truth.cscript, the package's one
  truth script, registered as runner block 68, with a guard on its block
  layout.

  Regression: test/test_tracking_documents.py::TestWp29Tracking -- failed at <base> with NameError: name '_wp29_open_problems' is not defined
  Regression: test/test_cscript_hygiene.py::TestTheWp29TruthScript -- failed at <base> with NameError: name '_WP29_TRUTH' is not defined
  Regression: test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script -- failed at <base> with assert 66 == 67
  Regression: test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read -- failed at <base> with assert 48 == 49
  Changed: test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2 -- skips exactly the titles WP29_OPEN lists; TestWp29Tracking holds each to the WP-29 open form
  Truth: test/test_wp29_truth.cscript W29-01 PASS (StataNow 19.5, WP29_ONLY unset)
  ```

- **Notes for the closeout (A5; S15 reads this).**
  - **S15.1.** Confirm `WP29_OPEN` is empty, replace it with `WP29_OPEN = {}`, and add `test_no_wp29_entry_remains_open` to `TestWp29Tracking`. It asserts that `WP29_OPEN == {}`, and that every id in `WP29_ALL` has a closed entry whose Resolution holds `(WP-29, <id>)` (that is, `_wp29_closure_problems(set(), set(_wp29_markers(changelog)), entries) == []`).
  - **Keep** `WP29_LISTS` and `WP29_ALL`. Once every P0 is closed, `test_each_p0_sits_in_its_changelog_lists` permanently checks that each WP-29 line stays in its list.
  - **S15.3.**
    - Replace `**GAPS2 closed:** (filled at closeout)` with the fully closed ids. They must be GAPS2 `### <ID>.` headings, so the parenthetical must go entirely.
    - Head the section `— DONE`.
    - Optionally add a commit column to `#### P0 traceability`.
  - **Formatting only.** When the last marker of a list is gone, S15 may remove the blank lines between consecutive WP-29 items of that list (R-02 left them for merging), without rewording any line.

## Appendix A: the 21 BUGS.md entries (TR-01.1; verbatim, one blank line between entries)

~~~~text
- [ ] Title: line, connected, area, rline, rarea and rconnected are joined in x order, never in the data's order as twoway joins them, and sort(varlist) is ignored
  - File Names and Line Numbers: dash_render.py at 7421d3d: GlyphMapper.map_line (7852; sort_values(xvar) at 7906), called by map_connected (7981) and map_rconnected (10949, 10952); GlyphMapper.map_area (7988; argsort at 8028); GlyphMapper._masked_order (8630; argsort at 8638), called by map_rarea (10591) and map_rline (10880); dash.sthlp: the Connection order paragraph (3229)
  - Description: DROPIN-REMAINING.md P0.1, verified at 357c368: line, connected, area, rline, rarea and rconnected always sort by x, so `twoway line y x` without `sort` draws a different picture, with no note; tests pin the x order. twoway joins these types in the data's order and `sort` gives x order (line.sthlp). Sources: GAPS2-A1-a, AUDIT-08, REM-§2-S06-sort, REM-S06-b, GAPS2-A4-o, GAPS2-B12-e, AUDIT-10, GAPS2-G15-b, GAPS2-A1-c.
  - Suggested fix: WP-29 section 02 (line join order): join every connecting type in the data's order unless sort or sort(varlist) is given, honour sort(varlist) with ties kept in the data's order, in both modes and after a filter move (maintainer decision M1).
  - Resolution: Not fixed because WP-29 section 02 has not landed. Graded S1 (WP-29): silently wrong output in common use; twoway line y x without sort draws another path, and nothing says so.

- [ ] Title: by() panels are drawn on independent scales by default, and by(, yrescale) is named and ignored
  - File Names and Line Numbers: dash_render.py at 7421d3d: DashRenderer._expand_by_groups (25660), DashRenderer._make_figure_body (25920; each panel's ranges are limited to its own layers at 26331), _dash_common_count_ticks (20758, the only shared-range path, for #N ticks), ServerAppBuilder._plan_by_groups (29209)
  - Description: DROPIN-REMAINING.md P0.2, verified at 357c368: a plain `by(foreign)` autoranges each panel separately; axes are shared only when ticks or a range are given explicitly. `by(, yrescale)` is named in the note and ignored. twoway draws by() panels on one common scale unless yrescale or xrescale is given. Sources: GAPS2-B4-a, GAPS2-B4-b.
  - Suggested fix: WP-29 section 10 (axis(#) routing and by() shared scales): share one range per axis across every panel, the Total panel included, unless yrescale, xrescale or rescale is given, in both modes and after a filter move.
  - Resolution: Not fixed because WP-29 section 10 has not landed. Graded S1 (WP-29): silently wrong output; panels that look comparable are drawn on different scales.

- [ ] Title: An unlabelled variable gets a blank axis title, a legend key named after the plot type and a blank tooltip label, where twoway uses the variable name
  - File Names and Line Numbers: dash_render.py at 7421d3d: _dash_axis_labels (18702), _dash_legend_key (23579), GlyphMapper._hover_tool (6193); test/conftest.py: make_data_json (425), which labels every variable and so hides the defect
  - Description: DROPIN-REMAINING.md P0.3, verified at 357c368: unlabelled variables get blank axis titles, legend keys named after the plot type, and blank tooltip labels; twoway uses the variable name. The test data helper gives every variable a label, which hides this. Sources: REM-08-05-C3b, REM-08-05-C3a, REM-08-05-M3.
  - Suggested fix: WP-29 section 03 (default and empty titles): use the variable's name wherever its label is empty, in axis titles, legend keys and tooltips, in both modes, and stop the test data helper labelling every variable.
  - Resolution: Not fixed because WP-29 section 03 has not landed. Graded S1 (WP-29): silently wrong text in common use; most variables in real data have no label.

- [ ] Title: A title sub-option with no text, such as ytitle(, size(large)), deletes the default axis title
  - File Names and Line Numbers: dash_render.py at 7421d3d: _TEXTBOX_SUBOPT_RE (2751), _textbox_split_point (2790), _dash_axis_labels (18702)
  - Description: DROPIN-REMAINING.md P0.4, verified at 357c368: `xtitle(, size())` or `ytitle(, color())` with no text deletes the default title. For example, `ytitle(, size(large))` removes the y title in both modes. twoway keeps the default title and restyles it. Sources: CRIT-01.
  - Suggested fix: WP-29 section 03 (default and empty titles): a title sub-option with no text restyles the default title; only a typed empty string removes it.
  - Resolution: Not fixed because WP-29 section 03 has not landed. Graded S1 (WP-29): a documented option deletes the title it was asked to restyle, with no note.

- [ ] Title: axis(2) on ylabel(), yscale(), yline() and xtick() is applied to the first axis
  - File Names and Line Numbers: dash_parse.mata at 7421d3d: _dash_route_axis2 (4893, routes only the title options); dash_render.py at 7421d3d: _dash_add_secondary_axes (20076), _dash_apply_scale_ranges (22749)
  - Description: DROPIN-REMAINING.md P0.5, verified at 357c368: `axis(2)` on `ylabel`/`yscale`/`yline`/`xtick` is applied to axis 1. `yscale(log axis(2))` logs the primary axis, and the note names only `axis(2)`. `ytitle(, axis(2))` is already routed correctly. Sources: REM-09-02-AXIS-N, GAPS2-B15-a, AUDIT-27, GAPS2-B22-c.
  - Suggested fix: WP-29 section 10 (axis(#) routing and by() shared scales): route axis(#) on every axis option to the axis it names, and refuse an axis number no layer uses with twoway's return code and message.
  - Resolution: Not fixed because WP-29 section 10 has not landed. Graded S1 (WP-29): an option is drawn on the wrong axis; yscale(log axis(2)) logs the primary axis.

- [ ] Title: function evaluates ^ from the right and accepts pi and e, which twoway refuses
  - File Names and Line Numbers: dash_render.py at 7421d3d: GlyphMapper.map_function (12431; _SAFE_FUNCS at 12477), _dash_function_args (24792); dash.ado at 7421d3d: _dash_fn_refuse (5457)
  - Description: DROPIN-REMAINING.md P0.6, verified at 357c368: `function` evaluates `^` right to left and accepts `pi` and `e`. `2^3^x` at x=2 draws 512 where Stata gives 64. `pi*x` draws, where `twoway` refuses it r(111). Sources: GAPS2-A6-d, GAPS2-C5-g, GAPS2-A6-c.
  - Suggested fix: WP-29 section 04 (function evaluated by Stata): take the points from Stata's own twoway__function_gen at registration, so the curve and the refusals are Stata's, with the RNG state as twoway leaves it.
  - Resolution: Not fixed because WP-29 section 04 has not landed. Graded S1 (WP-29): wrong numbers drawn (512 for 64), and commands twoway refuses are drawn.

- [ ] Title: The lpoly and lpolyci default bandwidth ignores kernel() and degree() and misses Stata's rule of thumb
  - File Names and Line Numbers: dash_render.py at 7421d3d: _LPOLY_ROT_C (229), GlyphMapper._default_lpoly_bwidth (9247), GlyphMapper.map_lpoly (9437), GlyphMapper.map_lpolyci (9525)
  - Description: DROPIN-REMAINING.md P0.7, verified at 357c368: the lpoly/lpolyci default bandwidth ignores `kernel()` and `degree()` (10-90% too small, e.g. biweight degree 2: 63.8 vs 302.5). Even the Epanechnikov degree 0/1 default is off by -22% to +14%, and 185 vs 77 on a 7-observation sample. Sources: GAPS2-A9-a, GAPS2-A9-b, GAPS2-C1, GAPS2-C13, AUDIT-24, GAPS2-C12-e.
  - Suggested fix: WP-29 section 11 (lpoly port): port Stata's per-kernel, per-degree rule-of-thumb bandwidth to Python, pinned to Stata's r(bwidth) in both modes and in served recomputes (maintainer decision M2).
  - Resolution: Not fixed because WP-29 section 11 has not landed. Graded S1 (WP-29): a smooth drawn with the wrong bandwidth, silently.

- [ ] Title: Computed layers on a date variable run in epoch milliseconds, so densities are per ms, width(), start() and bwidth() are read as ms, and lpoly draws nothing
  - File Names and Line Numbers: dash_render.py at 7421d3d: _stata_dates_to_datetime (326, the loader's conversion to epoch ms), GlyphMapper.map_histogram (10112), GlyphMapper.map_kdensity (10426), GlyphMapper.map_lpoly (9437), GlyphMapper.map_lpolyci (9525)
  - Description: DROPIN-REMAINING.md P0.8, verified at 357c368: computed layers on a date variable run in milliseconds. histogram/kdensity densities are per ms, and `width()`, `start()` and `bwidth()` are read as ms. lpoly/lpolyci draw nothing. histogram/kdensity put the date axis on Y. Sources: REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12.
  - Suggested fix: WP-29 section 05 (date computations in Stata units): compute histograms, densities and smooths of a date in its Stata units and draw them on the date axis, in both modes.
  - Resolution: Not fixed because WP-29 section 05 has not landed. Graded S1 (WP-29): wrong numbers on every computed layer of a date, and an empty smooth.

- [ ] Title: The lpolyci band is a bootstrap percentile band, not Stata's analytic band, and pwidth() and var() are ignored
  - File Names and Line Numbers: dash_render.py at 7421d3d: GlyphMapper._bootstrap_ci (6510), GlyphMapper.map_lpolyci (9525)
  - Description: DROPIN-REMAINING.md P0.9, verified at 357c368: the lpolyci band is a bootstrap percentile band, not Stata's analytic band. Band width is 0.51-1.33 times Stata's, and edges are off by up to 2.25 mpg. `pwidth()` and `var()` are ignored. It costs about 100 times lpoly. Sources: AUDIT-23, GAPS2-A10-a, GAPS2-C7-a, GAPS2-C7-b, GAPS2-A10-b, GAPS2-C7-c, GAPS2-C7-e.
  - Suggested fix: WP-29 section 11 (lpoly port): port lpolyci's analytic band with pwidth() and var() to Python, pinned to Stata's band, and remove the bootstrap (maintainer decision M2).
  - Resolution: Not fixed because WP-29 section 11 has not landed. Graded S1 (WP-29): a confidence band drawn 0.51 to 1.33 times Stata's width, silently.

- [ ] Title: A variable named only in hover() is never exported, so its tooltip field is empty in both modes
  - File Names and Line Numbers: dash.ado at 7421d3d: the export's variable list (5981, mata _dash_extract_vars), _dash_cell_cap (2830-2861); dash_parse.mata at 7421d3d: _dash_extract_vars (2148)
  - Description: DROPIN-REMAINING.md P0.10, verified at 357c368: a variable named only in `hover()` is never exported. Both routes and both modes drop it silently, with rc 0 and no note. Two existing certification cases pin the defect and must change (WP-29 section 06 names them). Sources: REM-09-07-HOVER-EXPORT, GAPS2-G16-res, REM-09-07-HOVER-TEST.
  - Suggested fix: WP-29 section 06 (hover() variables exported): export every hover() variable a layer can show and count it against the data limits, in both modes, refusing a name that is not a variable before any command text is built.
  - Resolution: Not fixed because WP-29 section 06 has not landed. Graded S1 (WP-29): a variable the user named is dropped in silence.

- [ ] Title: The saved page embeds every row of each drawn variable, including rows that if and in exclude
  - File Names and Line Numbers: dash_render.py at 7421d3d: DashRenderer._make_figure_body (25920); dash.ado at 7421d3d: _dash_write_data (4308)
  - Description: DROPIN-REMAINING.md P0.11, verified at 357c368: the saved page embeds rows that `if`/`in` exclude. Every row of each drawn variable is in the HTML source, and the help does not disclose it. Sources: GAPS2-I2-a, GAPS2-I2-b.
  - Suggested fix: WP-29 section 14 (embed only the rows a consumer reads): embed a cell only when a layer, a recomputed KPI card, a filter or the csv export reads that variable on that observation, number the rows both modes send by rank so no row number reveals an excluded observation (the served index included, ratified 01oct2026), and say so in the help.
  - Resolution: Not fixed because WP-29 section 14 has not landed. Graded S1 (WP-29): data the user excluded is published in the page source, undisclosed.

- [ ] Title: The served app has no credential, so any local account can open a session and read the data
  - File Names and Line Numbers: dash_render.py at 7421d3d: ServerAppBuilder (28242; the emitted make_document at 29994), main (31888), _dash_launch_app (31944)
  - Description: DROPIN-REMAINING.md P0.12, verified at 357c368: the served app has no credential. Any local account can open a session and read the data. The help's "only this machine" wording understates this. Sources: GAPS2-I3-a, GAPS2-I3-c, AUDIT-87.
  - Suggested fix: WP-29 section 13 (served-app token): require a per-launch secret token before any session, page, autoload, metadata or row reaches a client, compare it in constant time, have Stata open the tokenized 127.0.0.1 URL, and never run without a token: an app started without one makes its own and writes its link to a private file, and only if no folder takes that file prints the link once, after a warning, and keeps serving (maintainer decision M4, ratified 01oct2026; round 2, answer A).
  - Resolution: Not fixed because WP-29 section 13 has not landed. Graded S1 (WP-29): any account on the machine can read the dataset while dash serve runs.

- [ ] Title: The served app, spec and data files are written with the default umask, readable by other accounts where the temp directory is shared
  - File Names and Line Numbers: dash_render.py at 7421d3d: main (31888; open(output_path, "w") at 31940); dash.ado at 7421d3d: _dash_serve (7588; tempfiles at 7598 and 7652), _dash_write_data (4308)
  - Description: DROPIN-REMAINING.md P0.12, verified at 357c368: the app and the spec/data JSON are written 0644; on macOS the per-user 0700 temp directory mitigates this, and the shared-/tmp case on Linux is unmeasured. Sources: GAPS2-I3-b, GAPS2-I3-c, AUDIT-87.
  - Suggested fix: WP-29 section 08 (private files and serve lifecycle): write the app, spec and data files 0600, never through a symlink or into a FIFO, inside a 0700 per-user directory; where a location cannot be kept private, proceed and print one note naming it rather than refuse; start the served app only from the bytes dash wrote, read through a descriptor it opened and verified, never by path (maintainer decision M4, ratified 01oct2026; round 2, answer B).
  - Resolution: Not fixed because WP-29 section 08 has not landed. Graded S1 (WP-29): other accounts can read the dataset from disk where the temp directory is shared.

- [ ] Title: The served app outlives a killed Stata, its files survive a crash, and Break cannot stop dash serve
  - File Names and Line Numbers: dash_render.py at 7421d3d: _dash_launch_app (31944; Popen at 31999, KeyboardInterrupt at 32079, proc.wait() at 32083); dash.ado at 7421d3d: _dash_serve (7588; the Ctrl+C message at 7661); dash.sthlp: Ctrl+C at 97, 752, 777, 1423 and 1719
  - Description: DROPIN-REMAINING.md P0.13, verified at 357c368: killing Stata leaves the server running, holding its port and the data. Temp files survive a crash. Break in GUI Stata cannot stop `dash serve`: sfi `pollstd` is never called. The messages tell GUI users to press Ctrl+C. Sources: GAPS2-F2a, GAPS2-F2b, GAPS2-F4, GAPS2-H2a, GAPS2-F9c, GAPS2-H2b.
  - Suggested fix: WP-29 section 08 (private files and serve lifecycle): stop the app within a grace period when its parent Stata dies, delete its data files once it serves, poll Break while dash serve blocks so it ends with r(1), and name Break in the messages.
  - Resolution: Not fixed because WP-29 section 08 has not landed. Graded S1 (WP-29): the data stays served and on disk after Stata dies, and the GUI has no working way to stop dash serve.

- [ ] Title: One-line preview pages are never deleted and are written 0644, each a copy of the graph's data
  - File Names and Line Numbers: dash.ado at 7421d3d: the one-line form's preview path (5956-5957, tempfile saving_path_tmp plus .html, a name Stata never erases)
  - Description: DROPIN-REMAINING.md P0.14, verified at 357c368: one-line preview pages are never deleted and are 0644. 39 orphans of about 1.2 MB each were observed. Nothing prunes them and nothing documents them. Sources: GAPS2-X3-a, GAPS2-X3-b, GAPS2-X3-c.
  - Suggested fix: WP-29 section 08 (private files and serve lifecycle): write previews 0600 under unique names in a 0700 folder of the per-user root, keep at most five per session, and remove them with dash clear and once their session is dead (section 08 R-6, ratified 01oct2026).
  - Resolution: Not fixed because WP-29 section 08 has not landed. Graded S2 (WP-29): copies of the data are left on disk; not S1 because the command names each preview's path when it writes it.

- [ ] Title: After a filter move the saved page registers a layer's own if rows, not their intersection with its panel or graph qualifier
  - File Names and Line Numbers: dash_render.py at 7421d3d: DashRenderer._make_figure_body (25920, the per-plot view block), DashRenderer._register_view_filter (25538), DashRenderer._row_ids_for (25604), _FILTER_JS (15812; the view rebuild at 15966)
  - Description: DROPIN-REMAINING.md P0.15, verified at 357c368: after a filter move, the saved page registers per-plot rows rather than the intersection. In a linked `by()` graph, or a linked graph with its own graph-level qualifier, a layer with its own `if` then draws rows outside its panel. The served app is correct. Sources: REM-06-06-C7.
  - Suggested fix: WP-29 section 07 (saved filter rows and colorvar domain): register the intersection of the layer's rows with its panel or graph qualifier, so every move keeps the layer inside it.
  - Resolution: Not fixed because WP-29 section 07 has not landed. Graded S1 (WP-29): rows outside a panel are drawn in it after the first move, silently.

- [ ] Title: The colorvar() colour range ignores a per-plot if on the saved page and a linked graph's qualifier in both modes
  - File Names and Line Numbers: dash_render.py at 7421d3d: GlyphMapper._apply_colorvar (6916), _dash_colorvar_bins (5828)
  - Description: DROPIN-REMAINING.md P0.16, verified at 357c368: the `colorvar()` range ignores qualifiers. On the saved page it spans every row under a per-plot `if`. In both modes it ignores a linked graph's graph-level qualifier. Which colour key `twoway` draws under `by()` is not yet measured. Sources: REM-06-06-C8b, REM-06-06-C8b-link.
  - Suggested fix: WP-29 section 07 (saved filter rows and colorvar domain): take the colorvar domain, levels and bins from the rows the layer draws, in both modes, for numeric, string and date colorvars.
  - Resolution: Not fixed because WP-29 section 07 has not landed. Graded S1 (WP-29): colours mean other values than the rows drawn, silently.

- [ ] Title: Fits, smooths and densities on the saved page stay fitted to all rows after a filter move, with no cue
  - File Names and Line Numbers: dash_render.py at 7421d3d: _FILTER_JS (15812); the _dash_agg_config tags that only histogram (10197) and kdensity (10538) carry; dash.sthlp: the sentence that the saved page does not redraw a fitted line (1404)
  - Description: DROPIN-REMAINING.md P0.17, verified at 357c368: saved-page fits go stale after a filter move, with no cue. Filtered points sit under a fit computed on all rows. Sources: GAPS2-C4, GAPS2-E4a, GAPS2-E4c, AUDIT-38.
  - Suggested fix: WP-29 section 12 (stale cue and served redraw widths): show a visible stale cue on a frozen computed layer after a move that removes a row of its estimation sample, cleared when the move is undone; the served app keeps refitting, and no estimator is ported to JavaScript (maintainer decision M3).
  - Resolution: Not fixed because WP-29 section 12 has not landed. Graded S1 (WP-29): a fit that no longer matches the points shown, with no cue.

- [ ] Title: The served redraw keeps build-time bar and rbar widths and an emptied layer's style after a filter move
  - File Names and Line Numbers: dash_render.py at 7421d3d: ServerAppBuilder's emitted _dash_redraw_for (30264) and _on_filter_change (31049); GlyphMapper.map_bar (8086), GlyphMapper.map_rbar (10623)
  - Description: DROPIN-REMAINING.md P0.18, verified at 357c368: the served redraw keeps build-time bar/rbar widths. After a move, bar widths stay 56 where the qualified saved draw gives 168. An emptied lowess panel keeps its style. bar and rbar are not in the moved-layer tests. Sources: REM-15-03-C15.
  - Suggested fix: WP-29 section 12 (stale cue and served redraw widths): recompute bar and rbar widths, and an emptied layer's style, in the served redraw as the saved build does.
  - Resolution: Not fixed because WP-29 section 12 has not landed. Graded S1 (WP-29): served bars are drawn at the wrong width after a move, silently.

- [ ] Title: dash_setup fails on PEP 668 externally managed Pythons, and the commands it prints fail too
  - File Names and Line Numbers: dash_setup.ado at 7421d3d: the pip install and --user retry (172-190), the printed fallback (197), _dash_pip_command (404; the single-quoted command at 407)
  - Description: DROPIN-REMAINING.md P0.19, verified at 357c368: `dash_setup` fails on externally-managed Pythons (PEP 668, e.g. Homebrew). There is no detection and no `venv()` option. The manual fallback names a bare, unquoted `python`, and the single-quoted hint breaks in cmd.exe. The `--user` site is not added to the path, there is no ensurepip hint, and the help gives no guidance. Sources: GAPS2-H7a, GAPS2-H7b, GAPS2-H7c, GAPS2-H7d, GAPS2-H7e, GAPS2-H7f, GAPS2-H7g.
  - Suggested fix: WP-29 section 09 (dash_setup on PEP 668 Pythons): detect an externally managed Python before any pip process starts, offer venv(path), and print commands that run as printed in cmd.exe and POSIX shells.
  - Resolution: Not fixed because WP-29 section 09 has not landed. Graded S2 (WP-29): installation fails visibly on common Pythons, and the fixes it prints fail too.

- [ ] Title: KPI sd, var, iqr, cv and sum of a date variable are computed in epoch milliseconds
  - File Names and Line Numbers: dash_render.py at 7421d3d: DashRenderer._kpi_statistic (25250), _dash_kpi_date_valued (23437), _FILTER_JS's dash_apply_kpis (16076)
  - Description: DROPIN-REMAINING.md P0.20, verified at 357c368: KPI `sd`, `var`, `iqr`, `cv` and `sum` of a date are computed in epoch ms. `sd` is 86,400,000 times Stata's value on a %td variable. Sources: GAPS2-E1-residual.
  - Suggested fix: WP-29 section 05 (date computations in Stata units): compute KPI sd, var, iqr, cv and sum of a date in its Stata units, in both modes and after every move.
  - Resolution: Not fixed because WP-29 section 05 has not landed. Graded S1 (WP-29): wrong numbers on a KPI card, 86,400,000 times Stata's.
~~~~

## Appendix B: `test/test_tracking_documents.py` (TR-01.2-TR-01.4)

**Parts 1-2** go directly above part 3's class (task 01-02). They are the banner, the allowance, the map, the regexes and the helpers. Part 3 is appended at the end of the file (task 01-01). Each `WP29_OPEN` value is exactly the Appendix A title; a value is one line however long, because index R3 deletes keys by line.

~~~~python


# ===========================================================================
# WP-29's P0 entries (item 8 of the module docstring)
# ===========================================================================

#: WP-29 (.ultraplan/wp29/index.md, decision A4): the BUGS.md entries the
#: tracking foundation (S01) opened, one per P0 entry, by id, with their
#: exact titles.  Each stays open, graded S1 or S2, until the section that
#: fixes it lands; that section closes the entry in place and deletes its key
#: here in the same commit.  test_no_open_entry_is_s1_or_s2 skips exactly
#: these titles, and TestWp29Tracking fails on a key whose entry is missing,
#: closed or not in the WP-29 open form, so the allowance cannot outlive its
#: reason.  The closeout (S15) leaves it {}.
WP29_OPEN = {
    "P0.1": "line, connected, area, rline, rarea and rconnected are joined in x order, never in the data's order as twoway joins them, and sort(varlist) is ignored",
    "P0.2": "by() panels are drawn on independent scales by default, and by(, yrescale) is named and ignored",
    "P0.3": "An unlabelled variable gets a blank axis title, a legend key named after the plot type and a blank tooltip label, where twoway uses the variable name",
    "P0.4": "A title sub-option with no text, such as ytitle(, size(large)), deletes the default axis title",
    "P0.5": "axis(2) on ylabel(), yscale(), yline() and xtick() is applied to the first axis",
    "P0.6": "function evaluates ^ from the right and accepts pi and e, which twoway refuses",
    "P0.7": "The lpoly and lpolyci default bandwidth ignores kernel() and degree() and misses Stata's rule of thumb",
    "P0.8": "Computed layers on a date variable run in epoch milliseconds, so densities are per ms, width(), start() and bwidth() are read as ms, and lpoly draws nothing",
    "P0.9": "The lpolyci band is a bootstrap percentile band, not Stata's analytic band, and pwidth() and var() are ignored",
    "P0.10": "A variable named only in hover() is never exported, so its tooltip field is empty in both modes",
    "P0.11": "The saved page embeds every row of each drawn variable, including rows that if and in exclude",
    "P0.12a": "The served app has no credential, so any local account can open a session and read the data",
    "P0.12b": "The served app, spec and data files are written with the default umask, readable by other accounts where the temp directory is shared",
    "P0.13": "The served app outlives a killed Stata, its files survive a crash, and Break cannot stop dash serve",
    "P0.14": "One-line preview pages are never deleted and are written 0644, each a copy of the graph's data",
    "P0.15": "After a filter move the saved page registers a layer's own if rows, not their intersection with its panel or graph qualifier",
    "P0.16": "The colorvar() colour range ignores a per-plot if on the saved page and a linked graph's qualifier in both modes",
    "P0.17": "Fits, smooths and densities on the saved page stay fitted to all rows after a filter move, with no cue",
    "P0.18": "The served redraw keeps build-time bar and rbar widths and an emptied layer's style after a filter move",
    "P0.19": "dash_setup fails on PEP 668 externally managed Pythons, and the commands it prints fail too",
    "P0.20": "KPI sd, var, iqr, cv and sum of a date variable are computed in epoch milliseconds",
}

#: Every WP-29 P0 entry, permanently, and the CHANGELOG.md lists of the
#: current release its line belongs in (index.md "P0 coverage").  S01 put
#: one ``<!-- WP-29 <id> -->`` marker in each; the closing commit replaces
#: each marker in place with a line ending ``(WP-29, <id>)``.
WP29_LISTS = {
    "P0.1": ("Results that change", "Changed behaviour"),
    "P0.2": ("Results that change",),
    "P0.3": ("Results that change",),
    "P0.4": ("Results that change",),
    "P0.5": ("Results that change", "Changed behaviour"),
    "P0.6": ("Results that change", "Changed behaviour"),
    "P0.7": ("Results that change",),
    "P0.8": ("Results that change",),
    "P0.9": ("Results that change",),
    "P0.10": ("Fixed in WP-29",),
    "P0.11": ("Security",),
    "P0.12a": ("Security", "Changed behaviour"),
    "P0.12b": ("Security",),
    "P0.13": ("Security", "Fixed in WP-29"),
    "P0.14": ("Security",),
    "P0.15": ("Results that change",),
    "P0.16": ("Results that change",),
    "P0.17": ("Fixed in WP-29",),
    "P0.18": ("Results that change",),
    "P0.19": ("Requirements",),
    "P0.20": ("Results that change",),
}

#: The 21 ids, in P0 order.
WP29_ALL = tuple(WP29_LISTS)

_WP29_MARKER = re.compile(r"<!-- WP-29 (P0\.\d{1,2}[ab]?) -->")
_WP29_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-29 section \d{2} has not landed\."
    r" Graded S[12] \(WP-29\): \S")


def _wp29_markers(text):
    """The ids of every ``<!-- WP-29 <id> -->`` marker in *text*, in order,
    repeats kept."""
    return _WP29_MARKER.findall(text)


def _changelog_lists(text):
    """{heading: body} for every ``### `` list of the newest release (the
    first ``## `` section) of a CHANGELOG.md text.  The heading is the text
    after ``### ``; the body runs to the next ``### `` or ``## `` line."""
    releases = re.split(r"^## ", text, flags=re.M)
    if len(releases) < 2:
        return {}
    parts = re.split(r"^### (.+)$", releases[1], flags=re.M)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts), 2)}


def _changelog_list(lists, name):
    """The body of the list *name* names: the heading equal to it, or that
    starts with it and a parenthesis ("Changed behaviour (may need ...)");
    None unless exactly one heading matches."""
    hits = [b for h, b in lists.items()
            if h == name or h.startswith(name + " (")]
    return hits[0] if len(hits) == 1 else None


def _wp29_open_problems(open_map, entries):
    """What is wrong with the allowance *open_map* ({id: title}) against the
    BUGS.md *entries*: an id WP-29 lacks, a title with a double quote or
    shared by two ids, a title no entry or two entries carry, an entry that
    is closed (the allowance is stale), or one not in the WP-29 open form."""
    bad = []
    unknown = sorted(set(open_map) - set(WP29_ALL))
    if unknown:
        bad.append("ids WP-29 does not have: %s" % unknown)
    titles = list(open_map.values())
    if len(set(titles)) != len(titles):
        bad.append("two ids share one title")
    for pid, title in open_map.items():
        if '"' in title:
            bad.append("%s: the title holds a double quote" % pid)
        match = [e for e in entries if e["title"] == title]
        if len(match) != 1:
            bad.append("%s: %d BUGS.md entries are titled %r"
                       % (pid, len(match), title))
            continue
        e = match[0]
        if e["closed"]:
            bad.append("%s: %r is closed; delete its WP29_OPEN key"
                       % (pid, title))
        elif not _WP29_OPEN_FORM.match(e["fields"].get("Resolution", "")):
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-29 "
                       "section NN has not landed. Graded S1|S2 (WP-29): ...'"
                       % (pid, title))
    return bad


def _wp29_marker_problems(open_ids, markers):
    """A marker naming no WP-29 id, and an open id with no marker left."""
    bad = ["a marker names %s, which WP-29 does not have" % m
           for m in sorted(set(markers) - set(WP29_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP29_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp29_closure_problems(open_ids, markers, entries):
    """A closed id (in WP29_ALL, not open) whose marker is still in the
    CHANGELOG, or whose (WP-29, <id>) no closed entry's Resolution holds."""
    bad = []
    for pid in WP29_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-29, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp29_list_problems(lists_map, changelog):
    """Each id's marker or its (WP-29, <id>) line must sit in every list
    *lists_map* names for it, and its marker nowhere else."""
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-29 %s -->" % pid, "(WP-29, %s)" % pid
        for n in wanted:
            body = bodies.get(n)
            if body is not None and mark not in body and line not in body:
                bad.append("%s: '### %s' holds neither its marker nor a line "
                           "ending %s" % (pid, n, line))
        for h, body in lists.items():
            if mark in body and not any(
                    h == n or h.startswith(n + " (") for n in wanted):
                bad.append("%s: its marker sits under '### %s'" % (pid, h))
    return bad
~~~~

**Part 3** is appended at the end of the file by 01-01. It is preceded by two blank lines.

~~~~python
class TestWp29Tracking:
    """WP-29's 21 P0 entries (index.md A4): open in BUGS.md with a marker in
    each CHANGELOG list they belong to until their section lands, then
    closed with no marker left and a Resolution naming (WP-29, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        bad = _wp29_open_problems(WP29_OPEN, entries)
        assert not bad, "\n".join(bad)

    def test_an_open_p0_keeps_its_marker(self):
        bad = _wp29_marker_problems(
            set(WP29_OPEN), _wp29_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_p0_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp29_closure_problems(
            set(WP29_OPEN), set(_wp29_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_p0_sits_in_its_changelog_lists(self):
        assert WP29_ALL == tuple(WP29_LISTS) and len(WP29_ALL) == 21
        bad = _wp29_list_problems(WP29_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("# Changelog\n\n## 1.0, 01jan2027\n\nintro\n\n"
                "### Results that change\n\n- a line. (WP-29, P0.2)\n"
                "<!-- WP-29 P0.1 -->\n\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-29 P0.1 -->\n<!-- WP-29 P0.12a -->\n\n"
                "### Fixed in WP-29\n\n<!-- WP-29 P0.13 -->\n\n"
                "## 0.9, 01jan2026\n\n### Results that change\n\n"
                "<!-- WP-29 P0.99 -->\n")
        assert _wp29_markers(text) == ["P0.1", "P0.1", "P0.12a", "P0.13",
                                       "P0.99"]
        assert _wp29_markers("<!-- WP-28 B1 --> <!-- WP-29 P0.1-->") == []
        lists = _changelog_lists(text)
        assert list(lists) == [
            "Results that change",
            "Changed behaviour (may need your do-files changed)",
            "Fixed in WP-29"]
        assert "P0.99" not in "".join(lists.values())
        assert _changelog_list(lists, "Changed behaviour").startswith(
            "\n\n<!-- WP-29 P0.1 -->")
        assert _changelog_list(lists, "Security") is None
        assert _changelog_lists("no release heading") == {}

    def test_the_wp29_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-29 section 02 has not landed. "
                     "Graded S1 (WP-29): wrong path.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01oct2026 (WP-29, P0.2). Done.")]
        assert _wp29_open_problems({"P0.1": "T1"}, good) == []
        for open_map, entries, says in (
                ({"P0.1": "T2"}, good, "is closed"),
                ({"P0.1": "T9"}, good, "0 BUGS.md entries"),
                ({"P0.1": "T1"}, good + [entry("T1", False, open_form)],
                 "2 BUGS.md entries"),
                ({"P0.1": "T1"},
                 [entry("T1", False, "Not fixed because x. Graded S3 "
                        "(WP-27): y.")], "not 'Not fixed because WP-29"),
                ({"P0.99": "T1"}, good, "does not have"),
                ({"P0.1": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote"),
                ({"P0.1": "T1", "P0.3": "T1"}, good, "share one title")):
            bad = _wp29_open_problems(open_map, entries)
            assert any(says in b for b in bad), (says, bad)

        assert _wp29_marker_problems({"P0.1"}, ["P0.1"]) == []
        assert _wp29_marker_problems({"P0.1"}, []) == [
            "P0.1 is open and CHANGELOG.md holds no marker for it"]
        assert _wp29_marker_problems(set(), ["P0.12"]) == [
            "a marker names P0.12, which WP-29 does not have"]

        others = set(WP29_ALL) - {"P0.2"}
        assert _wp29_closure_problems(others, others, good) == []
        assert _wp29_closure_problems(others, others | {"P0.2"}, good) == [
            "P0.2 is closed and CHANGELOG.md still holds its marker"]
        assert _wp29_closure_problems(others, others, good[:1]) == [
            "P0.2 is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-29, P0.2)"]
        # (WP-29, P0.1) is not read inside (WP-29, P0.12a) or (WP-29, P0.10)
        near = [entry("T3", True, "Fixed (WP-29, P0.12a). (WP-29, P0.10).")]
        assert _wp29_closure_problems(set(WP29_ALL) - {"P0.1"}, set(),
                                      near) == [
            "P0.1 is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-29, P0.1)"]

        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-29 P0.1 -->\n"
               "### Changed behaviour (may need your do-files changed)\n\n"
               "- a line. (WP-29, P0.1)\n### Security\n\n"
               "<!-- WP-29 P0.11 -->\n")
        rules = {"P0.1": ("Results that change", "Changed behaviour"),
                 "P0.11": ("Security",)}
        assert _wp29_list_problems(rules, log) == []
        assert _wp29_list_problems(
            {"P0.1": ("Results that change", "Changed behaviour"),
             "P0.11": ("Results that change",)}, log) == [
            "P0.11: '### Results that change' holds neither its marker nor "
            "a line ending (WP-29, P0.11)",
            "P0.11: its marker sits under '### Security'"]
        assert _wp29_list_problems({"P0.10": ("Fixed in WP-29",)}, log) == [
            "CHANGELOG.md has no single '### Fixed in WP-29' list"]
~~~~

**Part 4.** Task 01-02 replaces lines 504-506 of `test_no_open_entry_is_s1_or_s2` with these lines. Lines 507-510 are unchanged.

~~~~python
        entries, _p = bugs
        # WP-29's P0 entries stay open, S1 or S2, until their sections land
        # (WP29_OPEN); TestWp29Tracking holds each one to its WP-29 form.
        allowed = set(WP29_OPEN.values())
        bad = ["line %d: %s %s" % (e["line"], g, e["title"][:90])
               for e in entries if not e["closed"]
               and e["title"] not in allowed
~~~~

**Part 5.** Task 01-02 inserts the module docstring's item 8 after line 36 (`line is listed by its package.`):

~~~~text
8. WP-29's P0 entries (.ultraplan/wp29/index.md A4) are open in BUGS.md
   in the form "Not fixed because WP-29 section NN has not landed. Graded
   S1|S2 (WP-29): ..." and listed in WP29_OPEN, which alone exempts them
   from the release guard, with a "<!-- WP-29 <id> -->" marker in each
   CHANGELOG list WP29_LISTS names, until their section lands; then the
   key is gone, no marker is left, each of those lists holds a line ending
   "(WP-29, <id>)", and a closed entry's Resolution holds "(WP-29, <id>)".
~~~~

## Appendix C: CHANGELOG.md insertions (TR-01.5; insert C.5 first, C.1 last)

Each block below is inserted as shown, and its first line is the empty line.

**C.1, after line 236 (end of `### Results that change`):** 13 markers.

~~~~text

**WP-29 (drop-in P0, 30sep2026)**

<!-- WP-29 P0.1 -->

<!-- WP-29 P0.2 -->

<!-- WP-29 P0.3 -->

<!-- WP-29 P0.4 -->

<!-- WP-29 P0.5 -->

<!-- WP-29 P0.6 -->

<!-- WP-29 P0.7 -->

<!-- WP-29 P0.8 -->

<!-- WP-29 P0.9 -->

<!-- WP-29 P0.15 -->

<!-- WP-29 P0.16 -->

<!-- WP-29 P0.18 -->

<!-- WP-29 P0.20 -->
~~~~

**C.2, after line 272 (end of `### Security`):** 5 markers.

~~~~text

<!-- WP-29 P0.11 -->

<!-- WP-29 P0.12a -->

<!-- WP-29 P0.12b -->

<!-- WP-29 P0.13 -->

<!-- WP-29 P0.14 -->
~~~~

**C.3, after line 437 (end of `### Changed behaviour (may need your do-files changed)`):** 4 markers.

~~~~text

<!-- WP-29 P0.1 -->

<!-- WP-29 P0.5 -->

<!-- WP-29 P0.6 -->

<!-- WP-29 P0.12a -->
~~~~

**C.4, after line 464 (end of `### Requirements`):** 1 marker.

~~~~text

<!-- WP-29 P0.19 -->
~~~~

**C.5, directly above line 466 (`### Fixed in WP-28`):** the heading, its sentence and 3 markers. The block ends with an empty line, so `### Fixed in WP-28` follows a blank line.

~~~~text
### Fixed in WP-29

Failures the drop-in re-audit of 30sep2026 ranked P0 that WP-29 fixed
without changing a drawn result; the results that changed are the WP-29
group under Results that change, and the security, behaviour and
requirement changes sit in their own lists.

<!-- WP-29 P0.10 -->

<!-- WP-29 P0.13 -->

<!-- WP-29 P0.17 -->

~~~~

## Appendix D: WP-29 in ROADMAP.md (TR-01.6; insert between line 4447 and line 4448)

~~~~markdown
## WP-29 · Close the drop-in P0 gaps

**GAPS2 closed:** (filled at closeout) · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28

> **User story.** As the Stata user pasting twoway syntax, I want dash to
> draw what twoway draws -- joins, scales, titles, axes, functions,
> smooths, bands and dates -- with nothing I named dropped; as the
> dashboard publisher, I want the page and the served app to carry only
> the rows a reader may see, to admit only me, and to stop with my Stata
> session; as the installer, I want dash_setup to work on an externally
> managed Python; as the maintainer, I want each of the 20 P0 items of the
> drop-in re-audit (`.ultraplan/handoff/DROPIN-REMAINING.md` section 3, P0,
> verified at 357c368) closed by a regression test that failed before its
> fix.

### Business requirements

- **BR-29.1** Join order: data order by default, x order under `sort`,
  varlist order under `sort(varlist)` (the rightmost copy wins), time
  order for the ts types, ties stable; in both modes and after a move; an
  invalid `sort()` name is refused with twoway's message and r(198) (P0.1).
- **BR-29.2** by() axes: one shared scale per axis by default (x, y, y2,
  x2, the Total panel included), the union of the drawn data after any
  move; the rescale forms and their abbreviations give per-panel scales; a
  `range()` twoway ignores on a rescaled axis is named once, at build
  time, in both modes (P0.2).
- **BR-29.3** Text: a variable's label when it is non-empty, else its
  name; a title sub-option with no text keeps the default text; a typed
  `""` empties the title; wherever a title, key or tooltip names a
  variable (P0.3, P0.4).
- **BR-29.4** axis(#): every routed option draws on the axis it names; an
  axis number no layer uses is refused with twoway's rc and message;
  axis-number parsing follows twoway's integer bounds; nothing is dropped
  unnamed (P0.5).
- **BR-29.5** function: the points are Stata's own
  (`twoway__function_gen`), written to round-trip exactly (`%24.17g`); an
  expression Stata refuses is refused with Stata's rc, before graph-level
  options are checked; the RNG state matches twoway's (P0.6).
- **BR-29.6** lpoly: the default bandwidth equals Stata's `r(bwidth)`
  within 1e-7 relative on exact rows (degree 0/1, x centred within three
  half-ranges of 0) and within 5e-5 relative on noisy rows (degree 2/3,
  or an offset x such as years, dates or `weight+20000`), where Stata's
  own float64 arithmetic varies; a missing or zero `r(bwidth)` draws y=0
  on every grid point, as twoway does; the lpolyci band at a given
  `bwidth()` and `pwidth()` or `var()` equals Stata's `lpoly, ci` band
  within 1e-8 times max(1,|y|), and at the default bandwidths within the
  bandwidth's tier; for every kernel, degrees 0-3 (the only degrees dash
  draws; the degree 4-7 constants are unit-tested, not drawn),
  `pwidth()`, `var()`, weights and the small-x scales where Stata drops
  pivots, in served recomputes too, with the option checks in twoway's
  order; the divergences D1-D9 that section 11 measures are documented
  and pinned (P0.7, P0.9).
- **BR-29.7** Dates: computed layers and KPI statistics run in Stata units
  and draw on the date axis; out-of-range bins or points are dropped and
  named in one note, alike in both modes; no non-finite number reaches page
  JSON; when every layer is computed and the first is lfit, qfit, lfitci,
  qfitci, kdensity, lpoly or lpolyci over a date, dash keeps its date axis
  where twoway labels numbers, a documented divergence (P0.8, P0.20).
- **BR-29.8** hover(): every named variable is exported, and counted
  against the data limits, when some layer can show it; a name that is not
  a variable is refused before any Stata command text is built (P0.10).
- **BR-29.9** Embedding: the saved page holds a cell only when a layer, a
  recomputed KPI card, a filter or the csv export reads that variable on
  that observation; Stata-computed results still use the whole data; both
  modes number the rows they send 0..m-1 in data order (the saved page's
  row ids and the served sources' `index`), so no row number reveals an
  excluded observation; the help discloses the rule (P0.11).
- **BR-29.10** Served access: without the per-launch token no session,
  page, autoload, metadata or row reaches a client, under `dash serve`,
  `python app.py` and `bokeh serve app.py`; the app never runs without a
  token: started with none, it makes its own, writes its link to a 0600
  file and prints only that file's path; the key is never printed, except
  when no link file can be written in any folder dash tries: then one
  warning line and the link alone are printed once, to the output of
  whoever started the server, which keeps serving; `/health` and BokehJS
  static files stay open; tokens are compared in constant time (P0.12a).
- **BR-29.11** Private files: every temporary copy of the data lives in a
  per-user directory dash makes 0700, and every file is created 0600; a
  location that cannot be kept private (a `c(tmpdir)` other accounts can
  change, a disk that keeps no permissions, a `dash-<uid>` that is not the
  user's own folder) is never refused: dash proceeds, leaves a planted
  `dash-<uid>` alone for a 0700 fallback, and prints one note naming the
  location; as an anti-hijack guard, not for privacy, no write goes
  through a symbolic link, into a FIFO or device, or over a hard-linked or
  another account's file, and no replaced app file is started, each ending
  r(7102); dash starts its served app only from the bytes it wrote, read
  through a descriptor it opened and verified, never by path, so an app
  file swapped in after that check never runs; one-line preview pages are
  private and bounded (unique names, 0600 in a 0700 folder; a session
  keeps its newest five; `dash clear` removes the session's pages except
  one a browser was asked to open in the last 60 s; another session's
  pages are removed only once that session is dead or the page is more
  than 24 h old; all sessions together keep at most 25); a server app the
  user names is written 0600 into the folder the user names, which is
  never refused or re-moded, and pages the user names keep twoway's umask
  semantics (P0.12b, P0.14).
- **BR-29.12** Lifecycle: the served app stops within the grace period
  after its parent Stata dies; no data file stays on disk while it serves;
  Break stops `dash serve` from every front end and ends it with r(1); the
  messages name Break, not Ctrl+C, in the GUI (P0.13).
- **BR-29.13** Saved filters: a linked or by() layer's view stays inside
  its panel or graph qualifier after any move; a colorvar's domain, levels
  and bins come from the layer's drawn rows, in both modes, for numeric,
  string and date colorvars (P0.15, P0.16).
- **BR-29.14** Stale and redraw: after a move that removed a row of a
  frozen layer's estimation sample the layer shows a visible cue, cleared
  when the move is undone; the served app recomputes bar and rbar widths
  and an emptied layer's style as the saved build does (P0.17, P0.18).
- **BR-29.15** Setup: on a PEP 668 Python `dash_setup` starts no pip
  process, names the reason and the `venv()` route, never suggests
  `--break-system-packages` and ends r(198); `venv(path)` creates,
  installs into and verifies a private environment and prints how to link
  Stata to it; printed commands run as printed in cmd.exe and POSIX
  shells (P0.19).
- **BR-29.16** Every P0 BUGS.md entry is closed with a Resolution naming
  tests that exist, every CHANGELOG marker is replaced, and the GAPS2 ids
  this package lists are closed with commits that exist.

### Technical requirements

- **TR-29.1** The plan is `.ultraplan/wp29/`: `PLAN.md` (context, goals,
  risks, exit gates) and `index.md` (the 15 sections, the four batches and
  their merge order, merge rules R1-R8, the cscript driver and gates
  G0-G11); each section file carries its own TR-NN.k and test plan.
- **TR-29.2** Tracking (section 01): 21 BUGS.md entries opened in the
  WP-29 form, the `WP29_OPEN` allowance and `TestWp29Tracking` in
  `test/test_tracking_documents.py`, 26 CHANGELOG markers in five lists,
  and the one truth script `test/test_wp29_truth.cscript` (runner block
  68, gated by `WP29_ONLY=S<NN>`).
- **TR-29.3** One commit per P0 entry (P0.13 two), subject ending
  `(WP-29 P0.<n>)`, each on a tree that was never red, its body opening
  with the failing tests' saved output.
- **TR-29.4** Both renderers every time: a helper the served app needs is
  added to the served copy lists and named in `test/function_test_map.py`;
  `test/test_mode_parity.py` gains each section's corpus cases and its
  `ALLOWED` set is unchanged.

### Acceptance criteria

- **AC-29.1** The 21 BUGS.md entries section 01 opened are closed; each
  Resolution holds `(WP-29, P0.<n>)` and names tests that exist;
  `WP29_OPEN` is empty.
- **AC-29.2** Each P0 entry's fix commit body opens with its saved failure
  text, with a `Regression:` line per regression test.
- **AC-29.3** `test/test_wp29_truth.cscript` runs every section block with
  every case PASS and no SKIP on a machine with Python; its fixtures carry
  the `_meta` stamp and are committed.
- **AC-29.4** `test/test_mode_parity.py` is green with every section's
  corpus cases, and `ALLOWED` is unchanged.
- **AC-29.5** Both served-name guards are green, the `__main__` block
  included.
- **AC-29.6** The security tests are green: no session, page or data
  without the token, and an app started without one makes its own and
  prints only its link file's path, or, when no link file can be written
  anywhere, prints the link once after a warning line and keeps serving;
  0600 files in a 0700 root wherever the disk keeps permissions; a
  location that is not private proceeds with one note, never an error; a
  link, FIFO or device, hard-linked or foreign file at a target, or a
  replaced app, refused r(7102); an app path swapped after the launch's
  check runs nothing but the verified bytes; every preview page 0600 in a
  0700 folder, at most five per session and 25 in all, removed by `dash
  clear` (except a page a browser was asked to open in the last 60 s) and
  once its session is dead; the app exits within the grace period after
  its parent dies; Break ends `dash serve` with r(1); no non-finite number
  in page JSON; no saved-page cell outside BR-29.9, and no served `index`
  value that is an original observation number.
- **AC-29.7** CHANGELOG.md holds no WP-29 marker; every WP-29 line ends
  `(WP-29, P0.<n>)`, and each Results line names the command, the old
  value and the new.
- **AC-29.8** WP-29 is headed DONE here; each id its `GAPS2 closed` field
  lists has a GAPS2.md Tracked line `Closed in WP-29, ...` naming a commit
  that exists; `test/test_tracking_documents.py` is green.
- **AC-29.9** `make test`, `make test-dev`, `make cert` and `make gate`
  are green once each on `wp29-p0`, and the cert wall time is reported
  against the baseline recorded before batch 1.
- **AC-29.10** No WP-29 commit message names an AI tool or vendor, and no
  WP-29 commit holds `CLAUDE.md` or `.gitignore`.
- **AC-29.11** Each commit's change detection showed only its section's
  symbols, and every HIGH or CRITICAL impact was reported before its edit.
- **AC-29.12** The merge into `main` is reported, not run, and the
  worktrees are removed.

### Test plan

`test/test_tracking_documents.py::TestWp29Tracking` checks the entries,
the allowance and the CHANGELOG markers at every commit; each section's
regression tests, truth block and parity corpus cases are listed in its
section file; the closeout runs the full suites, the certification suite
and the release gate once each.

#### P0 traceability

| P0 | Entry (BUGS.md) | Grade | Section |
|---|---|---|---|
| P0.1 | line types joined in x order; sort(varlist) ignored | S1 | 02 |
| P0.2 | by() panels independently scaled | S1 | 10 |
| P0.3 | unlabelled variables: blank titles, type-named keys, blank tooltips | S1 | 03 |
| P0.4 | a title sub-option with no text deletes the title | S1 | 03 |
| P0.5 | axis(2) on ylabel/yscale/yline/xtick applied to axis 1 | S1 | 10 |
| P0.6 | function: ^ right-associative, pi and e accepted | S1 | 04 |
| P0.7 | lpoly/lpolyci default bandwidth wrong | S1 | 11 |
| P0.8 | computed layers on a date run in ms | S1 | 05 |
| P0.9 | lpolyci band a bootstrap, not Stata's | S1 | 11 |
| P0.10 | hover()-only variable never exported | S1 | 06 |
| P0.11 | saved page embeds rows if/in exclude | S1 | 14 |
| P0.12a | served app has no credential | S1 | 13 |
| P0.12b | served app files readable by other accounts | S1 | 08 |
| P0.13 | served app outlives Stata; Break cannot stop serve | S1 | 08 |
| P0.14 | one-line preview pages never deleted, 0644 | S2 | 08 |
| P0.15 | saved filter registers per-plot rows, not the intersection | S1 | 07 |
| P0.16 | colorvar range ignores qualifiers | S1 | 07 |
| P0.17 | saved fits stale after a filter move, no cue | S1 | 12 |
| P0.18 | served redraw keeps build-time bar widths | S1 | 12 |
| P0.19 | dash_setup fails on PEP 668 Pythons | S2 | 09 |
| P0.20 | KPI sd/var/iqr/cv/sum of a date in ms | S1 | 05 |

---

~~~~

## Appendix E: `test/test_wp29_truth.cscript` (TR-01.7; the whole file)

~~~~stata
*! test_wp29_truth.cscript
*! WP-29's ONE new certification script (.ultraplan/wp29/index.md, A3):
*! every comparison with twoway's drawing or with Stata's own values that
*! WP-29's sections need lives here, one block per section, in section
*! order, so the certification suite grows by one script.  Refusal,
*! message and return-code checks join the EXISTING script for their area
*! instead (index.md rule R1); this script never gains one of those.
*!
*! Blocks, in section order (extended by each section that lands one):
*!   S01  scaffold smoke: the helpers load and a twoway SVG is read (W29-01)
*!
*! Usage: via run_all_cscripts.do (registered as its block 68).  One
*! block alone: set WP29_ONLY=S<NN> in the environment of the driver run
*! (index.md "The cscript driver").  Each block prints "S<NN> start" and
*! "S<NN> end" with the time, so the closeout can time it.

cscript "WP-29 truth: twoway comparisons" adodir ".."

clear all
set more off

if `"`c(python_exec)'"' == "" {
    display as error "SKIP: Python not available."
    exit 222
}

do "cert_helpers.do"
quietly do "cert_svg.do"
qui do "../dash_parse.mata"
qui do "../dash.ado"
global dash_nobrowser 1

// ----------------------------------------------------------------
// Tally helpers -- test_gaps2_truth.cscript's _gt_expect/_gt_done,
// renamed _w29_ for this script.
// ----------------------------------------------------------------
global w29_nfail    = 0
global w29_faillist ""
global w29_bad      = 0
global w29_ncase    = 0

capture program drop _w29_expect
program define _w29_expect
    version 16.0
    args id cond msg
    if !(`cond') {
        display as error `"`id' FAIL: `macval(msg)'"'
        global w29_bad = 1
    }
end

capture program drop _w29_done
program define _w29_done
    version 16.0
    args id msg
    if ${w29_bad} {
        global w29_nfail    = ${w29_nfail} + 1
        global w29_faillist "${w29_faillist} `id'"
    }
    else display as text `"`id' PASS: `macval(msg)'"'
    global w29_bad   = 0
    global w29_ncase = ${w29_ncase} + 1
end

// A fresh directory for this run's files, never one that already exists:
// a fixed name in a shared temp directory could be planted by another
// account (rule 1), so a name Stata has not handed out before is made and
// the run fails if it cannot be.
tempfile w29_base
local w29_work "`w29_base'_w29"
capture mkdir "`w29_work'"
if _rc {
    display as error "test_wp29_truth: cannot create the work directory `w29_work' (rc `=_rc')"
    exit 9
}

* ==== S01 scaffold: the helpers load and a twoway SVG is read ====
local only : env WP29_ONLY
if inlist("`only'", "", "S01") {
    display as text "S01 start `c(current_time)'"

    // ------------------------------------------------------------
    // W29-01: cert_svg_export and cert_svg_texts on one twoway scatter,
    // and dash's own programs are loaded from this tree.
    // ------------------------------------------------------------
    sysuse auto, clear
    quietly twoway scatter mpg weight, name(w29s01, replace)
    cert_svg_export, name(w29s01) file("`w29_work'/w29s01.svg")
    local s01_rc   = r(rc)
    local s01_file "`r(file)'"
    _w29_expect W29-01 "(`s01_rc' == 0)" "cert_svg_export rc `s01_rc'"
    capture confirm file "`s01_file'"
    _w29_expect W29-01 "(_rc == 0)" "r(file) `s01_file' does not exist"
    cert_svg_texts, file("`s01_file'")
    local s01_n    = r(n)
    local s01_list "`r(list)'"
    _w29_expect W29-01 "(`s01_n' > 0)" "cert_svg_texts found no text elements"
    capture program list _dash_serve
    _w29_expect W29-01 "(_rc == 0)" "dash.ado's _dash_serve is not loaded"
    _w29_done W29-01 "a twoway SVG was written and read (`s01_n' texts); dash is loaded"

    capture erase "`s01_file'"
    capture erase "`s01_list'"
    capture graph drop w29s01
    display as text "S01 end `c(current_time)'"
}
* ==== end S01 ====

* ==== append new blocks above this line ====

// ----------------------------------------------------------------
// Summary (test_gaps2_truth.cscript's shape)
// ----------------------------------------------------------------
capture graph drop _all
capture dash clear
capture rmdir "`w29_work'"
local nfail    = ${w29_nfail}
local faillist "${w29_faillist}"
local ncase    = ${w29_ncase}
local only : env WP29_ONLY
macro drop w29_nfail w29_faillist w29_bad w29_ncase
display as text ""
display as text "============================================================"
if `ncase' == 0 {
    // A WP29_ONLY that names no block ran nothing: that is not a pass.
    display as error "  test_wp29_truth: no case ran (WP29_ONLY=`only')"
    display as text "============================================================"
    exit 9
}
else if `nfail' == 0 {
    display as text "  test_wp29_truth: ALL CHECKS PASSED"
    display as text "============================================================"
}
else {
    display as error "  test_wp29_truth: `nfail' CHECK(S) FAILED"
    display as error "  failing:`faillist'"
    display as text "============================================================"
    exit 9
}
~~~~

## Appendix F: runner block 68 (TR-01.8; inserted after line 1741 of `test/run_all_cscripts.do`)

The first line is the empty line separating it from block 67.

~~~~stata

// ----------------------------------------------------------------
// 68. test_wp29_truth.cscript (WP-29: the one certification script for
// every twoway/Stata-value comparison the drop-in P0 package needs; one
// block per section, appended above its own "append new blocks above
// this line" marker -- .ultraplan/wp29/index.md A3)
// ----------------------------------------------------------------
display as text "[ RUN ] test_wp29_truth.cscript"
cd "`testdir'"
capture noisily {
    do "test_wp29_truth.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp29_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp29_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp29_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
~~~~

## Appendix G: `test/test_cscript_hygiene.py` (TR-01.9)

**Part 1, the two pins** (task 01-01), as a diff against `7421d3d`:

~~~~diff
@@ -289,10 +289,11 @@ class TestTheChecksReachEveryScript:
         # it (24sep2026); plus WP-28's test_gaps2_truth, the one script the
         # package adds (review D11): every twoway/Stata-value comparison of
         # the GAPS2 fix package lives in this one script, one block per
-        # section, so 66 now.  An empty
+        # section, so 66; plus WP-29's test_wp29_truth, the one script that
+        # package adds (.ultraplan/wp29/index.md A3), so 67 now.  An empty
         # glob would leave every per-script test above with no parameters,
         # and pytest reports that as a skip, not a failure.
-        assert len(_CSCRIPTS) == 66, (
+        assert len(_CSCRIPTS) == 67, (
             f"{len(_CSCRIPTS)} .cscript files found in {_HERE}"
         )
@@ -309,8 +310,9 @@ class TestTheChecksReachEveryScript:
         # runs no Python.  And WP-27's test_qualifier_in_stata and
         # test_string_values.  WP-28's test_gaps2_truth gates on
         # c(python_exec) itself (its own line, not cert_svg.do's, which
-        # loads after it and would otherwise be the only carrier), so 48.
-        assert len(names) == 48, f"{len(names)}: {sorted(names)}"
+        # loads after it and would otherwise be the only carrier), so 48;
+        # WP-29's test_wp29_truth gates the same way, so 49.
+        assert len(names) == 49, f"{len(names)}: {sorted(names)}"
~~~~

**Part 2, appended at the end of the file.** Task 01-01 adds only `class TestTheWp29TruthScript` (from `class` down). Task 01-06 inserts the banner, the four names and `_wp29_blocks` above it.

~~~~python


# ---------------------------------------------------------------------------
# WP-29's truth script: one block per section, gated, closed, in order
# ---------------------------------------------------------------------------
# test/test_wp29_truth.cscript is WP-29's one new certification script
# (.ultraplan/wp29/index.md A3, merge rule R1).  The fix sections append
# blocks to it from parallel worktrees: a block that is not gated cannot be
# run alone (WP29_ONLY=S<NN>), one that is not closed swallows the next,
# and one below the marker runs after the summary has judged the run.

_WP29_TRUTH = os.path.join(_HERE, "test_wp29_truth.cscript")
_W29_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W29_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W29_MARK = "* ==== append new blocks above this line ===="


def _wp29_blocks(src):
    """``(blocks, problems)`` for the truth script's text.  A block is
    ``(section, header line, end line)``; a problem names a marker line that
    is not there exactly once, or a block that is not closed by its own end
    line, not gated by its own section, below the marker, or out of section
    order."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W29_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W29_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, cur = [], None
    for n, ln in enumerate(lines, 1):
        o, c = _W29_OPEN.match(ln.rstrip()), _W29_CLOSE.match(ln.rstrip())
        if o:
            if cur:
                bad.append("%s (line %d) is not closed before line %d"
                           % (cur[0], cur[1], n))
            cur = (o.group(1), n)
        elif c:
            if cur is None or c.group(1) != cur[0]:
                bad.append("line %d closes %s, which is not the open block"
                           % (n, c.group(1)))
            else:
                blocks.append((cur[0], cur[1], n))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur)
    for k, (sec, first, last) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1] if ln.strip()]
        if code[:2] != ["local only : env WP29_ONLY",
                        'if inlist("`only\'", "", "%s") {' % sec]:
            bad.append("%s (line %d) is not gated by WP29_ONLY=%s"
                       % (sec, first, sec))
        if last > mark:
            bad.append("%s (line %d) is below the marker" % (sec, first))
        if k and sec < blocks[k - 1][0]:
            bad.append("%s (line %d) follows %s: blocks go in section order"
                       % (sec, first, blocks[k - 1][0]))
    return blocks, bad


class TestTheWp29TruthScript:
    """The scaffold section 01 writes, and every block a later section
    appends to it."""

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP29_TRUTH)
        order = ['cscript "WP-29 truth', "SKIP: Python not available.",
                 'do "cert_helpers.do"', 'do "cert_svg.do"', "* ==== S01 ",
                 "local only : env WP29_ONLY", "* ==== end S01 ====",
                 _W29_MARK, "test_wp29_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_closed_and_in_section_order(self):
        blocks, bad = _wp29_blocks(_read(_WP29_TRUTH))
        assert not bad, "\n".join(bad)
        assert blocks and blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        good = ('cscript "x"\n'
                "* ==== S01 scaffold ====\nlocal only : env WP29_ONLY\n"
                'if inlist("`only\'", "", "S01") {\n}\n'
                "* ==== end S01 ====\n"
                "* ==== S10 P0.5: axis(2) ====\nlocal only : env WP29_ONLY\n"
                'if inlist("`only\'", "", "S10") {\n}\n'
                "* ==== end S10 ====\n" + _W29_MARK + "\nexit 9\n")
        blocks, bad = _wp29_blocks(good)
        assert bad == [], bad
        assert blocks == [("S01", 2, 6), ("S10", 7, 11)], blocks
        moved = good.replace(_W29_MARK + "\n", "")
        for text, says in (
                (good.replace('"S10") {', '"S01") {'), "not gated"),
                (good.replace("* ==== end S10 ====\n", ""), "never closed"),
                (good.replace("* ==== end S01 ====\n", ""),
                 "not closed before"),
                (good.replace("S10", "S00"), "section order"),
                (moved, "appears 0 times"),
                (moved.replace('cscript "x"\n',
                               'cscript "x"\n' + _W29_MARK + "\n"),
                 "below the marker")):
            _blocks, bad = _wp29_blocks(text)
            assert any(says in b for b in bad), (says, bad)
~~~~
