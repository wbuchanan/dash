# Section 01: Tracking foundation

> Part of: WP-31 · GAPS3 rows: §6 (register corrections), §9 (new: Tracking) · Risk: green · Batch: 0 · Depends on: -- · Blocks: all · Tasks: 9, 1 commit · Case-id prefix: U01

## Overview

**What is wrong today.** GAPS3.md (411 lines at `6370ca4`) is a register of tables: every row of sections 4.A-4.K is a `| <id> | <gap> | <sev> | <register> | <evidence> | <task> |` line and nothing in the repository tracks a row's state. `test/test_tracking_documents.py` reads GAPS2.md's `### <id>. <title>` headings and `- **Tracked:**` lines (`_GAPS2_HEADING`, `_GAPS2_TRACKED`, :731-734) and WP-30's `WP30_OPEN`/`WP30_LISTS`/`WP30_SECTION` maps (:1580-1710), but knows nothing of GAPS3. BUGS.md ends at :3197 with three open entries (:2559, :2595, :2601, all S3) and none for the 110 WP-31 entries the manifest derives from GAPS3's rows. CHANGELOG.md's 0.1.0 release has the lists `### Results that change` (:10), `### Changed behaviour (may need your do-files changed)` (:609), `### Requirements` (:744) and `### Fixed in WP-30` (:800), and no `<!-- WP-31 ... -->` marker. The certification suite has 68 scripts (`test_cscript_hygiene.py:299`, `test_cert_shards.py:45`), the last registered as runner block `// 69.` (`test/run_all_cscripts.do:3077-3121`); there is no `test/test_wp31_truth.cscript`. GAPS3 §6 names register text that no longer matches the code: GAPS2 C14 is still `- **Tracked:** new.` (GAPS2.md:807) though `b06b662` closed it; DROPIN P3.1 (`.ultraplan/handoff/DROPIN-REMAINING.md:380`) asks to retire a script `44f8ab0` retired; P2.1, P2.12, P2.14, P2.25, P2.29, P2.48 and P3.9 describe more than is open. (GAPS3 §6 also lists GAPS2 G4 as "closed now, mark closed"; its Tracked line at GAPS2.md:1422 already reads `Closed in WP-30, ... commit acd868f`, so no edit is needed there.)

**After this section** every WP-31 entry is open in BUGS.md in the WP-31 form, graded, naming the section that closes it; GAPS3.md has a `## 9. Tracking` section with one `- **<id> Tracked:** Open (WP-31 section NN).` line per entry; `test_tracking_documents.py` reads those lines and the entries through `WP31_OPEN`, `WP31_LISTS`, `WP31_SECTION` and `TestWp31Tracking`, and the release guard exempts exactly the open WP-31 titles; CHANGELOG.md carries one `<!-- WP-31 <id> -->` marker per entry in each list the entry belongs to, under a new `### Fixed in WP-31` heading where no existing list fits; `test/test_wp31_truth.cscript` exists with S01's smoke block TF-01, is registered as runner block `// 70.`, has one row in the shard table, and is guarded by `TestTheWp31TruthScript`; the pins read 69 and 51; and the GAPS3 §6 corrections are applied to GAPS2.md and DROPIN-REMAINING.md as data edits, after which both are read-only (M23, A6).

**Why one section.** Every later section closes its entry, rewrites its Tracked line, replaces its markers and appends its truth block in place; those forms must exist before batch 1 is cut (M13, Q24), and only one section may create or register a cscript (R1) or edit GAPS2.md and DROPIN-REMAINING.md (A6).

**Test order and commit rule (rule 7, BRIEF).** One cycle, one commit `(WP-31 S01)`: 01-01 writes the failing tracking and hygiene tests, runs them against the unmodified tree and saves `<scratch>/01-01-failure.txt`, never committing; 01-02 to 01-08 turn them green; 01-09 runs the section's tests and the truth script through the slot, and commits. No full suite inside the section (M9); the merger runs it at batch end.

### Section decisions (binding on the executor)

- **D-01.a Entry ids.** One entry per manifest row id (A4): 110 entries (DECISIONS A12: A3, the abbreviation-truth fixture, is S08's entry). B5 is split, like C8 and C10, into `B5a` (S03: `base()` on dot read, `recast()` on dot noted or honoured) and `B5b` (S18: dot rows, the d-options), the ids the manifest already uses (index.md rows 03 and 18). E12 joins S40 and E13 joins S41, as the index's coverage check says. H5 and K1 have no entry (the index: design residuals; flips inside each fix section).
- **D-01.b Section name in an entry** is the manifest slug with each hyphen read as a space (`option-applicability` → `option applicability`), so an executor builds it mechanically.
- **D-01.c Grades** are GAPS3's Sev column: S1 for C1, C2, C3; S3 where the row says S3; S2 otherwise. A row graded "S2 (by decision)" or "S2 (recast part S1 unverified)" is S2 in every part.
- **D-01.d CHANGELOG lists.** Each entry's lists are in Appendix A's `Lists` column: `RC` = Results that change, `CB` = Changed behaviour (may need your do-files changed), `RQ` = Requirements, `FX` = Fixed in WP-31. Every entry has at least one list. The H2 parts go to `FX` (ratification item 3: the release also has a `### New` list the BRIEF does not name).
- **D-01.e The truth script carries no stubs.** Unlike WP-30, S01 writes only its own S01 block; each later section appends its blocks above the marker, one block per row it measures (R1), so `_wp31_blocks` requires one row id per header and non-decreasing section order, and does not require every section to own a block.
- **D-01.f Empty shard parts pass.** The script reads `DASH_CERT_SHARD` (so cert_shards.py marks it `*`) and balances its blocks longest first, every unlisted block counting 1 s (WP-30 counted 0). When `w31_N > 1`, `WP31_ONLY` is unset and part k has no block, the script prints `test_wp31_truth: part k/N has no block to run` and exits 0; with one part or `WP31_ONLY` set, no case run is still r(9). The `w31_secs` table holds `S01 1` until S61 writes the measured seconds.
- **D-01.g Shard table by hand.** `scripts/cert_shards.py write` needs a timed log naming every script, which no run has for the new script, so 01-07 adds the one row `test_wp31_truth.cscript  1.0 0  * * *` by hand; a `*` row adds its share to every shard before the others are placed, so no other assignment changes and `python3 scripts/cert_shards.py check` exits 0.
- **D-01.h GAPS3 reader forms** are exactly the BRIEF's three Tracked forms plus a row reader over the tables (`_GAPS3_ROW`), so a Tracked line naming an id no table row carries fails.

## Risk: [green] -- tests, documents and one certification scaffold; no shipped file changes

**Why.** Nothing drawn changes; the risk is a mistyped form that every later section then copies.

**Risk factors.** 1. A title with a `"` or shared by two entries breaks the reader. 2. A marker in the wrong list is caught only by `_wp31_list_problems`. 3. An unbalanced shard table or a split script with empty parts fails `make cert` at batch 1's end. 4. The GAPS2/DROPIN edits are read by `TestNoResidualNamesAClosedRow` and `_parse_gaps2`.

**Mitigation.** 1. `_wp31_open_problems` and `test_the_wp31_problem_readers` (unit-tested both directions). 2. The list check runs in 01-01's regression tests. 3. D-01.f and D-01.g; 01-08 runs the script through the slot with `DASH_CERT_SHARD` unset and `=3/3`. 4. The appended text keeps every regex the readers use (01-05 runs `test_tracking_documents.py` after the edits).

## Dependencies

- **Depends on:** nothing; batch 0, alone.
- **Blocks:** every section (S02-S61): the entry, Tracked line, marker, truth script and pins they rewrite in place exist only after S01 lands on `s3-bugs`.
- **Parallel batch:** 0; can run with nothing.

## Evidence

Anchors at `6370ca4`.

- **GAPS2 reader**, `test/test_tracking_documents.py:731-775`: `_GAPS2_HEADING`, `_GAPS2_TRACKED = ^- \*\*Tracked:\*\* (?P<text>\S.*)$`, `_GAPS2_CLOSED = ^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b`, `_GAPS2_DEFERRED`; `_parse_gaps2` returns `({id: {...}}, dupes)`; `_git(*args)` at :811 runs `git -C _ROOT`.
- **WP-30 machinery**, :1580-1870: `WP30_OPEN = {}`, `WP30_LISTS`, `WP30_SECTION`, `WP30_ALL`, `_WP30_MARKER = <!-- WP-30 (P1\.\d{1,2}[abc]?) -->`, `_WP30_OPEN_FORM`, `_wp30_markers`, `_wp30_open_problems`, `_wp30_marker_problems`, `_wp30_closure_problems`, `_wp30_list_problems`, `TestWp30Tracking` (7 tests, the last `test_no_wp30_entry_remains_open` at :1934). `_changelog_lists`/`_changelog_list` at :1339/:1350 are shared. The file ends at :1953.
- **Release guard**, :551-560: `allowed = set(WP29_OPEN.values()) | set(WP30_OPEN.values())` with the comment at :553-556. Module docstring items 1-9 at :1-59.
- **DROPIN reader**, :500-528: rows `^(\d+)\. (.*)$` under `### P2:`; a row holding `Written closed` or `[Closed in` is closed.
- **BUGS.md** 3197 lines, ends `SP-17.\n` (`tail -c 2 | xxd -p` → `2e0a`); open entries at :2559, :2595, :2601; `_parse_bugs` (:129) requires the four fields in order.
- **CHANGELOG.md** 991 lines: `### Results that change` :10 (last item :376, blank :377, `### Security` :378); `### Changed behaviour (may need your do-files changed)` :609 (last item ends :733, blank :734, `### Removed` :735); `### Requirements` :744 (last item :798, blank :799, `### Fixed in WP-30` :800).
- **Runner**, `test/run_all_cscripts.do` 3147 lines: shard table :75-156 (`local _cert_shards ///` :87, last row :155 `    test_wp30_truth.cscript             316.9 0  * * *`, `// ---- shards: end ----` :156); block `// 69.` :3077-3121 (its closing `}` at :3121, blank :3122, `// ----` :3123, `// Summary` :3124).
- **Pins:** `test_cscript_hygiene.py:299` `assert len(_CSCRIPTS) == 68`, :319 `assert len(names) == 50`, :328 `assert len(with_probes) == 13` (unchanged: no captured python import probe); `test_cert_shards.py:45` `assert len(names) == len(set(names)) == 68`. Hygiene reader for WP-30: `_WP30_TRUTH`..`_W30_HEAD` :1080-1084, `_wp30_blocks` :1087-1145, `TestTheWp30TruthScript` :1148-1215.
- **`scripts/cert_shards.py`**: `_SPLITS` matches `local <name> : env[ironment] DASH_CERT_SHARD`; `check()` applies `wp30_check` to the WP-30 script only; `assign()` shares a `*` script's seconds over all shards first.
- **`test/test_wp30_truth.cscript`** :1-200: header; `cscript "WP-30 truth: twoway comparisons" adodir ".."`; timer; `c(python_exec)` SKIP exit 222; `do "cert_helpers.do"`, `quietly do "cert_svg.do"`, `qui do "../dash_parse.mata"`, `qui do "../dash.ado"`, `global dash_nobrowser 1`; `_w30_expect`/`_w30_done`; work directory from `tempfile w30_base`; the parts section :99-189 (`w30_secs`, `_w30_part` Mata); S01 block :191-221; summary from :12352.
- **GAPS3 §6 targets:** GAPS2.md:807 `- **Tracked:** new.` (C14, closed by `b06b662`, BUGS.md:2650 "A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above"); GAPS2.md:1566 (H10) `- **Tracked:** new.`; DROPIN-REMAINING.md:173 (P2.1), :202-209 (P2.12), :211-218 (P2.14), :246 (P2.25), :262 (P2.29), :288 (P2.48), :380 (P3.1), :433 (P3.9).
- **Existing tests that pin today's state** (flipped by moving the count, never deleted): `test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script` (68), `::test_every_script_that_skips_for_python_is_read` (50), `test_cert_shards.py::TestTheRealTable::test_every_registered_script_has_one_row` (68).

## User stories

- **US-01.1** As the maintainer, I want every WP-31 entry open in BUGS.md, graded, naming its section, with a GAPS3 Tracked line, so the tracking documents state what is not yet fixed.
- **US-01.2** As the release manager, I want the release guard to exempt an S1/S2 entry only while it is open in the WP-31 form, so the allowance cannot hide a defect.
- **US-01.3** As a fix section's agent, I want one fixed edit (box, Resolution, Tracked line, `WP31_OPEN` key, markers) checked by a test, so I cannot half-close my entry.
- **US-01.4** As a fix section's agent, I want one truth script with a gated, timed block form, runnable alone with `WP31_ONLY=S<NN>`, so I measure against Stata without touching another section's lines.

## Business requirements

- **BR-01.1** BUGS.md holds one open entry per Appendix A row (110), in the BRIEF's open form, each title quote-free and unique.
- **BR-01.2** GAPS3.md §9 holds exactly one Tracked line per entry, each `Open (WP-31 section NN)` with NN = the entry's section.
- **BR-01.3** A stale allowance key, a missing or duplicated title, an entry not in the open form or naming another section, an open entry with no marker, a closed entry with a marker or without `(WP-31, <id>)`, a marker outside its list, a Tracked line out of step with BUGS.md: each fails a named test.
- **BR-01.4** CHANGELOG.md carries one marker per (entry, list) pair of Appendix A; `### Fixed in WP-31` sits directly above `### Fixed in WP-30`.
- **BR-01.5** The truth script runs under the runner as block 70, SKIPs r(222) only without Python, runs alone under `WP31_ONLY`, fails r(9) when no case ran in a single-part run, passes an empty part under a split run, and leaves no file behind.
- **BR-01.6** The GAPS3 §6 corrections are in GAPS2.md and DROPIN-REMAINING.md, and every tracking test stays green.
- **BR-01.7** No shipped file changes.

## Technical requirements

Both modes: S01 draws nothing; no copy list, JS or parity entry applies. No function is added to `function_test_map.py` or `program_coverage_map.py`.

- **TR-01.1 BUGS.md.** Append, after :3197 and one blank line, one entry per Appendix A row in Appendix A's order, one blank line between entries, the file ending with one newline:
  ```
  - [ ] Title: <Appendix A Title>
    - File Names and Line Numbers: <GAPS3 row's Evidence column, verbatim>
    - Description: GAPS3.md <row id>, re-verified at 6370ca4: <GAPS3 row's Gap column, verbatim; for a split row, the part Appendix A names in parentheses after the title, then "; the whole row reads: " and the Gap column>
    - Suggested fix: WP-31 section NN (<section name, D-01.b>): <Appendix A Suggested fix>
    - Resolution: Not fixed because WP-31 section NN has not landed. Graded S<n> (WP-31): <Appendix A Why>.
  ```
  `<row id>` in the Description is the GAPS3 table id (`B5`, not `B5a`). Backticks in the Gap column are kept; a `"` in the Gap column is kept in the Description (only the Title is quote-free). Build the entries with the script of TR-01.9 (`python3 <scratch>/s01/s01_entries.py bugs`), never by hand.
- **TR-01.2 GAPS3.md §9.** Append after :411 (one blank line, then):
  ```
  ## 9. Tracking

  One line per WP-31 entry (.ultraplan/sections/index.md, A4), rewritten in place by the entry's closing commit; test/test_tracking_documents.py::TestWp31Tracking reads exactly these forms:
  `Open (WP-31 section NN).`, `Closed in WP-31, BUGS.md "<title>", commit <sha>.`, or
  `Partly closed in WP-31 (section NN, commit <sha>): <what is closed>; open: <what remains> (BUGS.md "<residual title>").`
  A closing commit writes `commit pending`; the merger's step k.3b replaces it with the landed sha on s3-bugs (DECISIONS A11).

  - **A1 Tracked:** Open (WP-31 section 08).
  ...
  ```
  then the 110 lines of Appendix B in id order.
- **TR-01.3 Readers** (`test/test_tracking_documents.py`, appended after :1953 with two blank lines before; Appendix C block `tracking-wp31`): `WP31_OPEN` (110 keys, id to title, one per line, Appendix A order), `WP31_LISTS` (id to a tuple of list names, from the `Lists` column: `RC`→`"Results that change"`, `CB`→`"Changed behaviour"`, `RQ`→`"Requirements"`, `FX`→`"Fixed in WP-31"`), `WP31_SECTION` (id to int), `WP31_ALL = tuple(WP31_LISTS)`, the regexes `_WP31_ID = r"[A-K]\d{1,2}[a-gkltx]?"`, `_WP31_MARKER`, `_WP31_OPEN_FORM`, `_GAPS3_ROW`, `_GAPS3_TRACKED`, `_GAPS3_OPEN`, `_GAPS3_CLOSED`, `_GAPS3_PARTLY`, the functions `_wp31_markers`, `_wp31_open_problems`, `_wp31_marker_problems`, `_wp31_closure_problems`, `_wp31_list_problems` (each a copy of its WP-30 twin with `30`→`31`, `P1 entries`→`entries`, and `WP31_SECTION`), `_parse_gaps3(text)` and `_gaps3_problems(tracked, open_ids, entries)`, and `class TestWp31Tracking` with `test_every_allowed_title_is_an_open_entry`, `test_an_open_entry_keeps_its_marker`, `test_a_closed_entry_has_no_marker_and_a_resolution`, `test_each_entry_sits_in_its_changelog_lists` (also `len(WP31_ALL) == 110`, `tuple(WP31_SECTION) == WP31_ALL`, `set(WP31_SECTION.values()) == set(range(2, 61))`), `test_the_marker_reader`, `test_the_wp31_problem_readers`, `test_every_entry_has_one_gaps3_tracked_line`, `test_the_gaps3_readers`.
- **TR-01.4 Release guard.** :557 becomes `allowed = (set(WP29_OPEN.values()) | set(WP30_OPEN.values()) | set(WP31_OPEN.values()))`; the comment at :553-556 gains `, and WP-31's entries do the same (WP31_OPEN; TestWp31Tracking)`. Module docstring: item 10 after :59 (Appendix C `docstring-item-10`).
- **TR-01.5 CHANGELOG.md** (bottom-up so the anchors hold): above :800 insert Appendix C `fixed-in-wp31` and the `FX` markers; after :798 a blank line and the `RQ` markers (none in Appendix A; insert nothing); after :733 a blank line and the `CB` markers; after :376 a blank line, the group line `**WP-31 (drop-in GAPS3, 10oct2026)**`, a blank line and the `RC` markers. Markers are `<!-- WP-31 <id> -->`, Appendix A order within a list, one blank line between consecutive markers.
- **TR-01.6 The truth script** `test/test_wp31_truth.cscript`: copy `test/test_wp30_truth.cscript` lines 1-221 (header through `* ==== end S01 ====`) and lines 12352-12385 (from the blank line before `* ==== append new blocks above this line ====` to the end), then apply, in order: `sed -e 's/wp30/wp31/g' -e 's/WP30/WP31/g' -e 's/WP-30/WP-31/g' -e 's/w30_/w31_/g' -e 's/_w30_/_w31_/g'`; replace the header comment lines 1-28 with Appendix C `truth-header`; replace the `w30_secs` table (:112-118 of the original, now `w31_secs`) with the two lines `local w31_secs ///` / `    S01 1`; in the Mata `_w31_part` change `sec = J(rows(ids), 1, 0)` to `sec = J(rows(ids), 1, 1)` (D-01.f); in the S01 block change the header to `* ==== S01 scaffold: the helpers load and a twoway SVG is read ====` (unchanged text), case id `TF-01` to `U01-1` (four `_w31_expect` lines, one `_w31_done`), `w30s01` to `w31s01` (three places); in the summary, directly after `if \`ncase' == 0 {`, insert Appendix C `empty-part` as the first statement inside that brace. The `.ultraplan/wp30/index.md A142` citation in the header becomes `.ultraplan/sections/index.md A5`.
- **TR-01.7 Runner, pins, shard table.** Runner: after :3121 insert a blank line and block `// 70.` = lines 3077-3121 with `sed -e 's/69\./70./' -e 's/wp30/wp31/g' -e 's/WP-30: the one certification script for/WP-31: the one certification script for/' -e 's#.ultraplan/wp30/index.md A142#.ultraplan/sections/index.md A5#' -e "s/S01's scaffold and one block for each of S02-S57,/S01's scaffold and the blocks S02-S60 append,/"`. Shard table: :155 gains ` ///` at its end and a new :156 `    test_wp31_truth.cscript               1.0 0  * * *` (same column widths as :155). Pins: `test_cscript_hygiene.py:299` `68`→`69` with the comment line `# ... so 68 now.` extended `; plus WP-31's test_wp31_truth (.ultraplan/sections/index.md A5), so 69.`; :319 `50`→`51` with `; WP-31's test_wp31_truth gates the same way, so 51.`; `test_cert_shards.py:45` `68`→`69` with a trailing comment `# 68 -> 69: test_wp31_truth.cscript (WP-31 S01)`. Hygiene reader: Appendix C `hygiene-wp31` inserted after :1215 (the end of `TestTheWp30TruthScript`).
- **TR-01.8 Register corrections (A6)**, exact edits, Appendix D.
- **TR-01.9 Generator** `<scratch>/s01/s01_entries.py` (Appendix E): reads this file's Appendix A table and GAPS3.md's tables, and prints, by sub-command, `bugs` (the 110 entries), `tracking` (the §9 lines), `readers` (the three dict literals), `markers <list>` (the marker lines of one list). It uses `re` and `sys` only, no shell, no network, no `eval`.
- **TR-01.10 Security (rule 1).** Readers are anchored regexes over repository text; nothing runs user text; the generator writes nothing (its output is redirected by the task); the truth script writes only under a directory it creates.

## Boundaries

- No shipped file (`dash.ado`, `dash_parse.mata`, `dash_render.py`, `dash_setup.*`, `dash.sthlp`, `dash.pkg`, `stata.toc`, scheme files).
- Not edited: ROADMAP.md, GAPS.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, `test/function_test_map.py`, `test/program_coverage_map.py`, `test/test_mode_parity.py`, WP-29's and WP-30's constants and classes (mirrored, not changed), the import-probe pin (:328), `scripts/cert_shards.py`.
- GAPS2.md and DROPIN-REMAINING.md: only the lines Appendix D names; after S01 both are read-only (M23).
- No existing BUGS.md entry is closed, reworded or regraded. No test is renamed or deleted. No `make cert`, `make gate` or full suite.

## Stata truth

None added. The truth script's one case **U01-1** is the WP-30 TF-01 smoke renamed: `sysuse auto`, `twoway scatter mpg weight, name(w31s01, replace)`, `cert_svg_export` to `` `w31_work'/w31s01.svg ``, `cert_svg_texts` (`r(n) > 0`), `_dash_serve` loaded. Driver (BRIEF "Running one cscript"), `<W>` the worktree:
```sh
X=<scratch>/s01; mkdir -p "$X/only" "$X/shard3"
printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/test_wp31_truth.cscript"\n' "<W>" "<W>" > "$X/run_test_wp31_truth.do"
cp "$X/run_test_wp31_truth.do" "$X/only/"; cp "$X/run_test_wp31_truth.do" "$X/shard3/"
scripts/stata_slot.sh "$X" "$X/run_test_wp31_truth.do"
WP31_ONLY=S99 scripts/stata_slot.sh "$X/only" "$X/only/run_test_wp31_truth.do"
DASH_CERT_SHARD=3/3 scripts/stata_slot.sh "$X/shard3" "$X/shard3/run_test_wp31_truth.do"
```

## TDD test stubs

Regression tests (01-01; red at `6370ca4`):
- Test: `test/test_tracking_documents.py::TestWp31Tracking::test_every_allowed_title_is_an_open_entry` -- `NameError: name '_wp31_open_problems' is not defined`, then `A1: 0 BUGS.md entries are titled ...`.
- Test: `...::TestWp31Tracking::test_an_open_entry_keeps_its_marker` -- NameError, then `A1 is open and CHANGELOG.md holds no marker for it`.
- Test: `...::TestWp31Tracking::test_a_closed_entry_has_no_marker_and_a_resolution` -- NameError; vacuous once all are open.
- Test: `...::TestWp31Tracking::test_each_entry_sits_in_its_changelog_lists` -- NameError, then `CHANGELOG.md has no single '### Fixed in WP-31' list`.
- Test: `...::TestWp31Tracking::test_the_marker_reader`, `::test_the_wp31_problem_readers`, `::test_the_gaps3_readers` -- NameError.
- Test: `...::TestWp31Tracking::test_every_entry_has_one_gaps3_tracked_line` -- NameError, then `A1: GAPS3.md has 0 Tracked lines`.
- Test: `test/test_cscript_hygiene.py::TestTheWp31TruthScript::test_the_scaffold_is_in_order`, `::test_every_block_is_gated_timed_closed_and_in_section_order`, `::test_the_block_reader` -- `NameError: name '_WP31_TRUTH' is not defined`.
- Test: `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script` -- `assert 68 == 69`; `::test_every_script_that_skips_for_python_is_read` -- `assert 50 == 51`.
- Test: `test/test_cert_shards.py::TestTheRealTable::test_every_registered_script_has_one_row` -- `assert 68 == 69`.

cscript case: `test/test_wp31_truth.cscript U01-1` (green once the script exists). Pinned tests to flip: the three count pins above (moved, R10). Parity corpus: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| 110 open entries in form, titles unique, sections right | pytest `TestWp31Tracking::test_every_allowed_title_is_an_open_entry` | BUGS.md | n/a |
| Release guard exempts the three allowances only | pytest `TestNoOpenEntryBlocksARelease` | BUGS.md | n/a |
| Markers present/absent/in place | pytest `test_an_open_entry_keeps_its_marker`, `test_a_closed_entry_has_no_marker_and_a_resolution`, `test_each_entry_sits_in_its_changelog_lists` | CHANGELOG.md | n/a |
| GAPS3 Tracked lines agree with BUGS.md | pytest `test_every_entry_has_one_gaps3_tracked_line` | GAPS3.md | n/a |
| Readers both directions | pytest `test_the_marker_reader`, `test_the_wp31_problem_readers`, `test_the_gaps3_readers` | inline | n/a |
| Truth script layout, registration, pins | pytest `TestTheWp31TruthScript`, `test_cscript_hygiene.py`, `test_cert_verdict.py`, `test_cert_shards.py`; `python3 scripts/cert_shards.py check` | the script, the runner | n/a |
| Script runs; gate; empty part | the three driver runs of "Stata truth" | auto | Stata |
| Register edits keep readers green | pytest `test_tracking_documents.py` | GAPS2.md, DROPIN | n/a |

Acceptance criteria: **AC-01.1** `grep -c '^- \[ \] Title:' BUGS.md` → 113; `grep -c 'Not fixed because WP-31 section' BUGS.md` → 110. **AC-01.2** `grep -c '^- \*\*[A-K][0-9]*[a-z]* Tracked:\*\* Open (WP-31 section [0-9][0-9])\.$' GAPS3.md` → 110. **AC-01.3** `grep -c '<!-- WP-31 ' CHANGELOG.md` equals the number of (entry, list) pairs of Appendix A (the generator prints it: `python3 <scratch>/s01/s01_entries.py count`); `grep -c '^### Fixed in WP-31$' CHANGELOG.md` → 1. **AC-01.4** `grep -c 'do "test_wp31_truth.cscript"' test/run_all_cscripts.do` → 1; `python3 scripts/cert_shards.py check` exits 0; the driver prints `U01-1 PASS` and `test_wp31_truth: ALL CHECKS PASSED`; `WP31_ONLY=S99` ends r(9); `DASH_CERT_SHARD=3/3` prints `part 3/3 has no block to run` and no `r(`. **AC-01.5** `grep -Eic 'claude|anthropic'` on the commit message → 0.

## Tasks

**Commit boundary.** Tasks 01-01 to 01-08 form the one S01 commit, subject `Open the WP-31 entries, Tracked lines, markers and truth script (WP-31 S01)`, made by 01-09 on `wp31-s01` in `<W>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s01` (cut by the orchestrator from `s3-bugs` at `6370ca4`). The body opens with `<scratch>/01-01-failure.txt`, then what changed and where, then one `Regression:` line per red node of "TDD test stubs" (`-- failed at 6370ca4 with <text>`), one `Flipped:` line per moved count pin (`-- 68 was right before test_wp31_truth.cscript existed`), `Truth: test/test_wp31_truth.cscript U01-1 PASS`. No `Fixture:`, no `BUGS.md: ... (closed)` line (S01 closes nothing), no `GAPS3:` line. Every command runs as `cd <W> && ...`. `<SF>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/sections/section-01-tracking-foundation.md`.

<task type="auto" id="01-01">
  <name>Write the failing tracking and hygiene tests</name>
  <files>test/test_tracking_documents.py, test/test_cscript_hygiene.py, test/test_cert_shards.py</files>
  <action><![CDATA[Check `git -C <W> rev-parse HEAD` prints 6370ca4's full sha and `git -C <W> branch --show-current` prints wp31-s01; `mkdir -p <scratch>/s01`. Extract Appendix E to `<scratch>/s01/s01_entries.py` with `python3 -c "import re,sys; t=open(sys.argv[1]).read(); m=re.search(r'^~~~~python s01-entries\n(.*?)\n~~~~$', t, re.M|re.S); open(sys.argv[2],'w').write(m.group(1)+'\n')" <SF> <scratch>/s01/s01_entries.py`. Append Appendix C block `tracking-wp31` to test/test_tracking_documents.py after its last line (:1953) with two blank lines before it, replacing its three `@@WP31_OPEN@@`, `@@WP31_LISTS@@`, `@@WP31_SECTION@@` lines by the output of `python3 <scratch>/s01/s01_entries.py readers <SF>`. Insert Appendix C block `hygiene-wp31` into test/test_cscript_hygiene.py after :1215 (the last line of TestTheWp30TruthScript) with two blank lines before it; change :299 `== 68` to `== 69` and :319 `== 50` to `== 51`, extending their comments as TR-01.7 says. In test/test_cert_shards.py:45 change `== 68` to `== 69` and append the TR-01.7 comment. Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_shards.py -q -n0 -p no:cacheprovider -rf 2>&1 | grep -E '^(FAILED|E   )|passed|failed' > <scratch>/01-01-failure.txt` and put the line `S01 tests at 6370ca4:` first. Do not commit.]]></action>
  <verify><![CDATA[`grep -c '^FAILED' <scratch>/01-01-failure.txt` prints 14: the eight TestWp31Tracking nodes, the three TestTheWp31TruthScript nodes, test_the_glob_finds_every_script, test_every_script_that_skips_for_python_is_read and test_every_registered_script_has_one_row; the file holds `assert 68 == 69` twice and `assert 50 == 51` once; `grep -c '^    "' test/test_tracking_documents.py` grew by 330 (110 keys in each of three maps). `git -C <W> status --porcelain` shows only ` M` for the three files.]]></verify>
  <done>The fourteen new or moved tests existed and failed for their recorded reasons, and nothing was committed.</done>
</task>

<task type="auto" id="01-02">
  <name>Widen the release guard and the docstring</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[In test_no_open_entry_is_s1_or_s2 (:551) replace the statement at :557 `allowed = set(WP29_OPEN.values()) | set(WP30_OPEN.values())` by `allowed = (set(WP29_OPEN.values()) | set(WP30_OPEN.values()) | set(WP31_OPEN.values()))` and extend the comment ending at :556 with the sentence `WP-31's entries do the same until theirs land (WP31_OPEN; TestWp31Tracking).` Insert Appendix C block `docstring-item-10` after :59 (the docstring line `   keeps every P1 entry closed with no marker left.`). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[The run reports exactly these failures: test_every_allowed_title_is_an_open_entry, test_an_open_entry_keeps_its_marker, test_each_entry_sits_in_its_changelog_lists, test_every_entry_has_one_gaps3_tracked_line; TestNoOpenEntryBlocksARelease's three tests pass; `grep -c 'WP31_OPEN.values()' test/test_tracking_documents.py` prints 1; `grep -c '^10. WP-31' test/test_tracking_documents.py` prints 1.]]></verify>
  <done>The release guard exempted exactly the three allowances' titles, the reader unit tests passed, and only the four document checks still failed.</done>
</task>

<task type="auto" id="01-03">
  <name>Open the entries and the Tracked lines</name>
  <files>BUGS.md, GAPS3.md</files>
  <action><![CDATA[Check `tail -c 2 BUGS.md | xxd -p` prints 2e0a and `wc -l < BUGS.md` prints 3197. Run `python3 <scratch>/s01/s01_entries.py bugs <SF> >> BUGS.md` (the script prints one blank line, then the 110 entries of TR-01.1 in Appendix A order, one blank line between entries, a final newline). Check `tail -3 GAPS3.md` ends with the line `still contain the word from earlier runs; they are regenerated by \`make cert\`.`; run `python3 <scratch>/s01/s01_entries.py tracking <SF> >> GAPS3.md` (prints one blank line, the TR-01.2 heading and introduction, one blank line, the 110 lines of Appendix B). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`grep -c '^- \[ \] Title:' BUGS.md` prints 113; `grep -c 'Not fixed because WP-31 section' BUGS.md` prints 110; `grep -c '^- \*\*[A-K][0-9]*[a-z]* Tracked:\*\* Open (WP-31 section [0-9][0-9])\.$' GAPS3.md` prints 110; `grep -c '^## 9. Tracking$' GAPS3.md` prints 1; the pytest run fails only test_an_open_entry_keeps_its_marker and test_each_entry_sits_in_its_changelog_lists, and TestEveryBugsEntryIsWellFormed, TestEveryOpenEntrySaysWhyItIsOpen, TestNoOpenEntryBlocksARelease pass.]]></verify>
  <done>BUGS.md held the 110 WP-31 entries open, graded and well formed, and GAPS3.md tracked each as Open at its section.</done>
</task>

<task type="auto" id="01-04">
  <name>Place the CHANGELOG markers</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[Assert the anchors: :376 ends `(WP-30, P1.25b)`, :377 blank, :378 `### Security`; :733 ends `(WP-30, P1.35)`, :734 blank, :735 `### Removed`; :798 ends `(WP-30, P1.35)`, :799 blank, :800 `### Fixed in WP-30`. If any fails, stop and report (the base is not 6370ca4's CHANGELOG). Edit bottom-up: (1) above :800 insert Appendix C block `fixed-in-wp31`, one blank line, the output of `python3 <scratch>/s01/s01_entries.py markers FX <SF>`, one blank line; (2) after :733 insert one blank line and the output of `... markers CB <SF>`; (3) after :376 insert one blank line, the line `**WP-31 (drop-in GAPS3, 10oct2026)**`, one blank line and the output of `... markers RC <SF>`. Appendix A has no RQ entry, so nothing goes after :798. Run `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-31 ' CHANGELOG.md` equals `python3 <scratch>/s01/s01_entries.py count <SF>`; `awk '/^### Results that change/,/^### Security/' CHANGELOG.md | grep -c '<!-- WP-31 '` equals the RC count the script prints, likewise CB between `### Changed behaviour` and `### Removed`, and FX between `### Fixed in WP-31` and `### Fixed in WP-30`; `grep -c '^### Fixed in WP-31$' CHANGELOG.md` prints 1; the pytest run reports 0 failed.]]></verify>
  <done>CHANGELOG.md held one WP-31 marker per entry and list, under the group line and the new Fixed in WP-31 heading, and every tracking and floor test passed.</done>
</task>

<task type="auto" id="01-05">
  <name>Apply the register corrections</name>
  <files>GAPS2.md, .ultraplan/handoff/DROPIN-REMAINING.md</files>
  <action><![CDATA[Make exactly the edits of Appendix D, each after asserting the line's current text as Appendix D quotes it (stop and report on a mismatch). Then run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`sed -n 807p GAPS2.md` starts `- **Tracked:** Closed in WP-28, BUGS.md "A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above", commit b06b662`; `grep -c 'Written closed' .ultraplan/handoff/DROPIN-REMAINING.md` grew by 1; `grep -c 'Narrowed 10oct2026 (GAPS3 §6)' .ultraplan/handoff/DROPIN-REMAINING.md` prints 7; `grep -c ' GAPS3: ' GAPS2.md` prints 36; the pytest run reports 0 failed.]]></verify>
  <done>GAPS2.md and DROPIN-REMAINING.md said what the code does, pointed their open rows at GAPS3, and the tracking tests stayed green.</done>
</task>

<task type="auto" id="01-06">
  <name>Create the truth script</name>
  <files>test/test_wp31_truth.cscript</files>
  <action><![CDATA[Build the file as TR-01.6 says: `sed -n '1,221p;12352,12385p' test/test_wp30_truth.cscript | sed -e 's/wp30/wp31/g' -e 's/WP30/WP31/g' -e 's/WP-30/WP-31/g' -e 's/w30_/w31_/g' > test/test_wp31_truth.cscript`; replace lines 1-28 (the `*!` header) by Appendix C `truth-header`; replace the `local w31_secs ///` block (seven lines) by `local w31_secs ///` and `    S01 1`; change `sec = J(rows(ids), 1, 0)` to `sec = J(rows(ids), 1, 1)`; in the S01 block replace `TF-01` by `U01-1` (five places) and `w30s01` by `w31s01` (three); insert Appendix C `empty-part` as the first statement after `if \`ncase' == 0 {` in the summary. Check `grep -c 'w30\|WP30\|WP-30\|TF-01' test/test_wp31_truth.cscript` prints 0 and `grep -c 'capture python' test/test_wp31_truth.cscript` prints 0. Run `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`grep -c '^\* ==== S01 scaffold: ' test/test_wp31_truth.cscript` prints 1; `grep -c '^\* ==== append new blocks above this line ====$'` prints 1; `grep -c 'has no block to run'` prints 1; the hygiene run fails only `TestEveryCscriptIsWiredIntoTheRunner::test_the_runner_calls_it[test_wp31_truth.cscript]` and TestTheWp31TruthScript passes; test_cert_verdict.py fails only `test_the_real_runner_registers_every_script_in_test`.]]></verify>
  <done>The truth script existed in WP-30's frame with S01's U01-1 block, its parts machinery and the empty-part rule, and every hygiene rule held except its registration.</done>
</task>

<task type="auto" id="01-07">
  <name>Register block 70 and the shard row</name>
  <files>test/run_all_cscripts.do</files>
  <action><![CDATA[Assert :3121 is `}` (block 69's close), :3122 blank, :3124 `// Summary`. Insert after :3121 one blank line and the block `sed -n '3077,3121p' test/run_all_cscripts.do | sed -e 's/69\./70./' -e 's/wp30/wp31/g' -e 's/WP-30:/WP-31:/' -e 's#.ultraplan/wp30/index.md A142#.ultraplan/sections/index.md A5#' -e "s/S01's scaffold and one block for each of S02-S57,/S01's scaffold and the blocks S02-S60 append,/"` (generate it to <scratch>/s01/block70.do first, then insert). In the shard table append ` ///` to :155 and insert after it `    test_wp31_truth.cscript               1.0 0  * * *` (the name padded to the same width as :155's). Run `python3 scripts/cert_shards.py check` and `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_cert_shards.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`grep -c 'do "test_wp31_truth.cscript"' test/run_all_cscripts.do` prints 1; `grep -c '^// 70\. test_wp31_truth' test/run_all_cscripts.do` prints 1; `python3 scripts/cert_shards.py check` prints nothing and exits 0; `python3 scripts/cert_shards.py show` prints the same N=2,3,4 loads as at the base plus 0.5, 0.3 and 0.25 s; the pytest run reports 0 failed.]]></verify>
  <done>The runner ran the WP-31 script as block 70 in every shard, the shard table balanced unchanged, and the hygiene, verdict and shard tests passed.</done>
</task>

<task type="auto" id="01-08">
  <name>Run the script in Stata three ways</name>
  <files>none</files>
  <action><![CDATA[Run the three driver runs of "Stata truth" through scripts/stata_slot.sh only (never the GUI, never a bare -b do). If the first run SKIPs (r(222)), python_exec was dropped from ~/.stata19/console/stata19.rc: a skip is not a pass; restore the link and rerun.]]></action>
  <verify><![CDATA[In <scratch>/s01/run_test_wp31_truth.log: `grep -c '^U01-1 PASS'` 1, `grep -c '^S01 start '` 1, `grep -c '^S01 end '` 1, `grep -c 'test_wp31_truth: ALL CHECKS PASSED'` 1, `grep -c '^r([0-9]*);'` 0; `ls -A <scratch>/s01/tmp` prints nothing. In <scratch>/s01/only/run_test_wp31_truth.log: `grep -c 'no case ran'` at least 1 and `grep -c '^r(9);'` at least 1. In <scratch>/s01/shard3/run_test_wp31_truth.log: `grep -c 'part 3/3 has no block to run'` 1 and `grep -c '^r([0-9]*);'` 0.]]></verify>
  <done>U01-1 passed in StataNow, a gate naming no block failed with r(9), and an empty shard part ended cleanly.</done>
</task>

<task type="auto" id="01-09">
  <name>Run the section tests and commit S01</name>
  <files>none</files>
  <action><![CDATA[Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_cert_shards.py test/test_version_floor.py test/test_packaging.py test/test_test_integrity.py test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider`. Stage by name: `git add BUGS.md GAPS3.md GAPS2.md CHANGELOG.md .ultraplan/handoff/DROPIN-REMAINING.md test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_shards.py test/run_all_cscripts.do test/test_wp31_truth.cscript`; `git diff --cached --name-only` lists exactly those ten. Write <scratch>/s01/01-commit-msg.txt per the Commit boundary paragraph, opening with <scratch>/01-01-failure.txt; `grep -Eic 'claude|anthropic'` on it prints 0; `git commit -F <scratch>/s01/01-commit-msg.txt`; record the sha in <scratch>/s01/01-sha.txt for the merger.]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 S01)`; `git show --name-only --format= HEAD | wc -l` prints 10; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git log -1 --format=%b | head -1` prints `S01 tests at 6370ca4:`.]]></verify>
  <done>One green commit on wp31-s01 held the entries, Tracked lines, readers, markers, register corrections, truth script and runner block, with a message free of tool names.</done>
</task>

## Section completion criteria

- One commit on `wp31-s01` ending `(WP-31 S01)`, exactly ten files, no test-only commit, no tool names.
- BUGS.md: 110 WP-31 entries open; GAPS3.md §9: 110 Open lines; `WP31_OPEN` has 110 keys; `TestWp31Tracking` (8) green; release guard widened.
- CHANGELOG.md: markers per Appendix A, group line, `### Fixed in WP-31`.
- `test/test_wp31_truth.cscript` registered as block 70, one `*` shard row, U01-1 PASS, empty-part rule proven; pins 69 and 51; `TestTheWp31TruthScript` (3) green; `cert_shards.py check` exits 0.
- GAPS2.md and DROPIN-REMAINING.md corrected per Appendix D.

## Notes

- **Forms later sections follow** (binding; R1, R4, R5): close an entry by flipping `- [ ]` to `- [x]` and rewriting only its Resolution line in the BRIEF's closed form; delete its own `WP31_OPEN` line (check: `grep -c '^    "<id>": "' test/test_tracking_documents.py` → 0; `WP31_LISTS` and `WP31_SECTION` rows are `"<id>": (` and `"<id>": <int>,` and stay); rewrite its GAPS3 §9 line to the Closed or Partly form with `commit pending` in the sha position (a Partly line names an open BUGS.md entry whose title is the residual's); the merger's step k.3b rewrites every `pending` of the batch to the landed sha on `s3-bugs` in one tracking commit, so no section ever runs `git commit --amend` (DECISIONS A11; G2 forbids `pending` after k.3b and S61.3 fails on any); replace each `<!-- WP-31 <id> -->` in place with lines ending `(WP-31, <id>)`; append truth blocks above the marker, one block per GAPS3 row (A14; a section's task 01 appends only its first row's block), as `* ==== S<NN> <id>: <what> ====` with `local only : env WP31_ONLY` / `if inlist("\`only'", "", "S<NN>") & \`: list posof "S<NN>" in w31_run' {` / `display as text "S<NN> start " c(current_date) " " c(current_time)` as the first code line / `display as text "S<NN> end " c(current_date) " " c(current_time)` as the last before `}` (the exact forms `_wp31_blocks` requires) / `* ==== end S<NN> ====`, helpers above the header, case ids `U<NN>-<k>`, `_w31_expect`/`_w31_done`, files only under `` `w31_work' ``. A section does not edit `w31_secs` (S61 writes it from the closeout log).
- **Merging (R1, R4, R5).** Entries, Tracked lines, markers and blocks are separated by blank lines, so hunks apply three-way; adjacent `WP31_OPEN` deletions conflict in context only; the merger applies both by hand, never dropping a line.
- **Python linkage.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; `stata_slot.sh` caps sessions at three.
- **For S61:** empty `WP31_OPEN` to `{}`, add `test_no_wp31_entry_remains_open` (copy of :1934-1953 with WP-31 names), write `w31_secs` from the closeout cert log's `S<NN> start/end` lines, and file residuals per M12.
- **Decisions for maintainer ratification:** (1) the H2 parts under Fixed in WP-31 rather than `### New` (D-01.d); (2) the empty-part exit 0 (D-01.f); (3) the hand-added shard row (D-01.g). (The former items on `B5a`/`B5b` and on the entry count are moot: the index uses the ids and the count is 110 with A3, REVIEW-1 R1-14, R1-01.)

## Appendix A: the 110 entries (TR-01.1; read by `s01_entries.py`)

Columns: Id · S (closing section) · Grade · Lists (RC, CB, RQ, FX) · Title (quote-free, unique) · Suggested fix (the sentence after `WP-31 section NN (<name>): `). The Description's Gap text and the File Names come from GAPS3.md's row `<id without suffix>`; the part a split entry covers is the parenthesis after its title (the generator writes it before the Gap text).

| Id | S | Grade | Lists | Title | Suggested fix |
|---|---|---|---|---|---|
| C1 | 02 | S1 | RC | pcarrow, pcbarrow and pcarrowi heads ignore msize(), mcolor(), mfcolor(), mlcolor() and mlwidth() in silence, pcbarrow heads fill black, mangle(), barbsize() and headlabel are undeclared, and a row missing its second point is dropped | size and colour the heads from the marker options and the scheme, fill pcbarrow heads with the line colour, declare mangle(), barbsize() and headlabel, keep a one-point row as a marker, and rewrite P4-18 and P4-20. |
| C2 | 03 | S1 | RC | rbar msize() is written and silently unread where twoway uses it as the bar width with mwidth | read msize() with mwidth on rbar, or name both in the note. |
| B5a | 03 | S2 | RC | base() on dot is written to the spec and never read, and recast() on dot is dropped with no note (the base and recast parts) | read base() on dot and note or honour recast() on dot after measuring twoway dot, recast(line). |
| C3 | 04 | S1 | CB | Options twoway refuses on a type (kernel() n() level() bwidth() bands() range() base()) are written to every spec and dropped in silence | add a per-type applicability column to _dash_option_rules and refuse each inapplicable option with twoway's measured words. |
| C10a | 05 | S2 | FX | range(varname), range(# .), bwidth(0), lowess bwidth() above 1, n(1) and per-type level() bounds are refused where twoway accepts them (the bounds that are a rules-table edit) | relax each rule to twoway's bound and cscript each against twoway's rc. |
| C10b | 06 | S2 | FX | degree() above 3, several variables in one mlabel() element, scatteri 2/2 and yaxis(1 2) are refused where twoway accepts them (the values needing new parsing) | accept degree 4-7 with the ROT constants, several variables in one mlabel() element, the scatteri division and yaxis(1 2). |
| C18 | 06 | S3 | FX | scatteri refuses a 2/2 numlist element where twoway divides | evaluate the division in the immediate forms. |
| F4 | 06 | S3 | FX | _LPOLY_ROT_CONSTANTS holds degree 4-7 rows that are unreachable under the degree 0-3 rule | accept degree 4-7 with C10b. |
| A5 | 07 | S2 | FX | Weight expressions such as [aw=price+1] and [aw=L.x] are refused where twoway takes an expression | evaluate the expression into a __dash column at registration and pin the values against summarize [aw=]. |
| A6 | 07 | S3 | FX CB | Option varlists with time-series operators (mlabel(L.make), colorvar(L.mpg), by(L.foreign)) are refused r(198) where twoway draws or refuses with another code | route option varlists through _dash_tsop_gen where twoway draws and copy twoway's rc where it refuses. |
| A7 | 07 | S3 | RC | hover() written inside a layer's parentheses and again after the comma keeps only the rightmost list | merge the two lists and pin the tooltip. |
| A8 | 07 | S3 | CB | Date literals in y options such as ylabel(2000m1) are accepted where twoway refuses r(198) | extend the date-literal refusal loop to the y options. |
| A1 | 08 | S3 | FX | dash twoway with nothing after it is refused r(198) where twoway draws an empty graph | draw an empty figure with axes only for the bare prefix and pin it with a cscript. |
| A2 | 08 | S3 | CB | Plot-type abbreviations are a superset of twoway's eight and the help lists only twoway's | refuse the extra abbreviations with twoway's not-a-twoway-plot-type r(198) and pin with test_parser.cscript. |
| A3 | 08 | S3 | FX | Option-abbreviation minimums have no live pin and test/fixtures/abbrev_truth.json is a pre-fix record whose stale counts test_abbreviations.py asserts | regenerate the fixture after A2 and pin every option minimum live both ways. |
| A4 | 08 | S2 | CB | mla() binds to mlabel() where twoway's mla is mlalign(), so mla(center) is refused as a bad variable | declare MLAlign() so the longer minimum wins and cscript both spellings. |
| C10c | 09 | S2 | FX | Axes 3 to 9 are refused where twoway draws them (the axes part) | draw axes 3-9 with Bokeh extra ranges in both modes and cscript against twoway. |
| F1a | 10 | S2 | RC | The saved page does not refit lfit and qfit after a filter move (the JS prelude and the lfit and qfit twins) | generalise the _FILTER_JS prelude to xvar, yvar and wvar, add dash_fit_grid, dash_wls and dash_t_ppf, and refit lfit and qfit pinned to their Python twins. |
| C4 | 11 | S2 | RC | Fit options atobs, estcmd(), estopts(), predopts(), ciplot(), fitplot() and nofit are named and not drawn | honour nofit, ciplot() and fitplot(), run estcmd(), estopts() and predopts() through Stata at build time, and read atobs as a grid rule. |
| C5 | 12 | S2 | RC | kdensity area() and boundary, histogram gap(), function droplines() and base(), area nodropbase and bar baroffset() are named and not drawn | draw each with its direct Bokeh form in both modes. |
| F1b | 13 | S2 | RC | The saved page does not refit lfitci and qfitci after a filter move (the lfitci and qfitci twins) | port the lfitci and qfitci bands to JavaScript on the S10 prelude, pinned to their Python twins. |
| C6 | 14 | S2 | RC | cmissing(n) on area, rarea and estimator-generated missing points and connect() other than direct on rarea are named and not drawn | split the patch or band at missing points as twoway does. |
| C7 | 14 | S3 | RC | recast() of a histogram to a range type or an unknown name and recast() on pci and pcarrowi are named where twoway draws them | extend _dash_recast_opt to those forms. |
| C8a | 15 | S2 | RC | colorvar() is drawn on four plot types only and jitter() is named on rscatter, rcapsym, pcscatter and pccapsym (the coverage and jitter parts) | route every glyph through _apply_colorvar and jitter the four range types. |
| F1c | 16 | S2 | RC | The saved page does not refit lowess after a filter move (the lowess twin) | port lowess to JavaScript, pinned to its Python twin. |
| C8b | 17 | S2 | RC | colorlist() and coloruseplegend are pending, colorstart(), colorend(), colorformissing(), colorfillonly, colorkeysrange, colorrule(), clegend(), plegend() and pcycle() are undeclared, and dash's colormissing() is not Stata's colorformissing() spelling (the option remainder) | alias colorformissing(), declare and draw the remaining colorvar options. |
| B5b | 18 | S2 | RC | dot is drawn as a plain scatter with no dot rows, and dotextend(), ndots() and the d-options are undeclared or pending (the dot rows and d-options) | draw twoway's dot rows and declare and draw the d-options in both modes. |
| F1d | 19 | S2 | RC | The saved page does not refit lpoly after a filter move (the lpoly twin) | port lpoly with its rule-of-thumb bandwidth to JavaScript, pinned to its Python twin. |
| C9 | 20 | S2 | RC | Weighted scatter markers are not sized by [aw] | scale marker area by weight as twoway does and pin against twoway's .gph marker sizes. |
| B1 | 21 | S2 | FX | rpcap and rpspike are refused by name | parse the four-variable family, draw map_rcap or map_rspike plus the point marker in both modes, and cscript against the .gph serset. |
| B2 | 21 | S2 | FX | sunflower falls to the generic unrecognised-plot-type message and is absent from the help's Not-drawn list | refuse sunflower by name with advice and list it in the help. |
| B3 | 21 | S2 | FX | matamatrix() is read as a varlist and refused r(101) or r(111) | refuse matamatrix() by name with advice and list it in the help. |
| F1e | 22 | S2 | RC | The saved page does not refit lpolyci after a filter move (the lpolyci twin) | port the lpolyci analytic band to JavaScript on S19's lpoly, pinned to its Python twin. |
| B4a | 23 | S2 | FX | contour and contourline are refused by name (the interpolation, grid rule, cap and truth extractor) | implement twoway's thin-plate and Shepard interpolation in numpy with the unique-x by unique-y grid, the 1,000-point cap and an extract script of twoway__contour_gen truth. |
| D1 | 24 | S2 | RC | xmtick, ymtick, xmlabel, ymlabel, tmtick and tmlabel and their *2 forms are pending and never read | draw minor ticks as Bokeh minor ticks and minor labels as a second LabelSet along the axis. |
| F1f | 25 | S2 | RC | The saved page does not refit mband and mspline after a filter move (the mband and mspline twins) | port mband and mspline to JavaScript, pinned to their Python twins. |
| B4b | 26 | S2 | FX | contour and contourline are refused by name (the type registration, options, colour rules, colour key and both modes) | register the two types, draw with Bokeh contour fills and lines from S23's grid with the colour options and key, and tag the layer frozen above the cap. |
| D2 | 27 | S2 | RC CB | t1title to r2title are pending and title2 and subtitle2 are named where twoway refuses them | draw the eight edge titles on each side and refuse title2() and subtitle2() with twoway's r(198). |
| F1g | 28 | S2 | RC | The saved page does not refit fpfit and fpfitci after a filter move (the fpfit and fpfitci twins) | port fpfit's power search and fpfitci's band to JavaScript, pinned to their Python twins. |
| B4c | 29 | S2 | FX | contour and contourline are refused by name (the JavaScript twin) | port marching squares and isobands to the saved page so contours refit within the cap. |
| D3 | 30 | S2 | RC | Textbox sub-options on titles are named and _dash_textbox_place is wired to scheme clocks only | wire user position() and ring() through _dash_textbox_place and draw box, margin and justification. |
| D13 | 30 | S3 | RC | Added text ignores tstyle() and the textbox sub-options and does not expand a global macro in a drawn label | route tstyle() through SchemeParser.textbox_style and expand globals at registration. |
| D4 | 31 | S2 | RC | Legend geometry sub-options are named, corner clocks are centred, pos(0) and ring(0) land at Bokeh's top_right, label(#) with no text is dropped, and identical keys are not merged | implement the geometry sub-options on the Bokeh Legend with a clock table, a blank key for label(#) and merged identical keys. |
| C13 | 31 | S3 | RC | A histogram-only graph draws a legend where twoway draws none | exempt histogram-only graphs from the legend. |
| D5 | 32 | S2 | RC | scale(), fxsize(), fysize() and the overhangs are never read, and aspectratio() shapes the figure, loses to xsize/ysize and refuses placement() | apply scale() to every size, honour fxsize and fysize in the grid, compute the plot-region ratio from the frame and accept placement(). |
| E11 | 32 | S2 | RC | Sizes are relative to a 4-inch reference and scale() is pending | scale every size with D5. |
| D6 | 33 | S2 | RC CB | Axis label and tick style sub-options are named, ##5 is read as #5, and label forms twoway refuses are drawn | draw the stylable sub-options, apply the ##N minor rule and refuse twoway's refusals. |
| D7 | 33 | S3 | RC | Axis-scale look options fill, outergap(), extend, fextend and lstyle are named and two yscale(alt) do not toggle back | draw extend, fextend and outergap() and toggle alt. |
| E6 | 33 | S3 | RC | Line-width *# multiplies before the 0.3 pt floor and tlwidth() and glwidth() are named not drawn | apply the floor after the multiply and draw tick and grid widths. |
| D8 | 34 | S2 | RC | yvarlabel() and xvarlabel() are undeclared, noted and absent from the help | declare them and use them as axis title and legend key text. |
| C17 | 34 | S3 | RC | mlabprefix(), mlabsuffix() and plot-level lalign() are undeclared and headlabel is accepted on types twoway may not take it on | declare and draw prefix and suffix, declare lalign() and measure headlabel's type set. |
| E3 | 34 | S2 | RC | msangle(anglestyle name) is drawn at 0 degrees and mlalign(), mwidth and mlabstyle() are undeclared | use _dash_anglestyle_degrees for msangle and declare the three options. |
| C14 | 34 | S3 | CB | rscatter y y2 x, mlabel(y) draws where twoway refuses r(102) | count mlabel variables toward the range check. |
| C15 | 34 | S3 | RC | Bar marker labels default to 3 o'clock where twoway's bar default is 12 | give each type its default clock. |
| D9 | 35 | S2 | RC | The y2 and x2 range is built once and never follows a filter move, the first-used axis is not drawn left or bottom, and horizontal with yaxis(2) titles no x axis | recompute the extra ranges in the move callback in both modes and apply the first-used side rule. |
| D10 | 36 | S3 | RC | by() sub-options of its stage-3 grammar are named, overall legend placement and interaction differ, panel margins ignore iscale(), and panels emptied by a filter stay drawn | apply the stage-3 grammar rows and hide emptied panels after a move. |
| D11 | 37 | S3 | RC | graphregion margins are inexact, the intensity and shade options are named, several marginstyle forms are not parsed, and s1color's unfilled plot region is filled white | parse every marginstyle form, draw intensity and shade and honour shadestyle plotregion none. |
| D12 | 38 | S3 | RC | An out-of-range xline() or yline() is clipped to the frame where twoway draws it outside | draw reference lines with a Segment in screen units beyond the frame. |
| D14 | 39 | S3 | CB FX | tabs() drops unregistered names silently, the served layout() overwrites a cell silently, and there is no per-tab layout() | name unknown tab members, refuse same-cell collisions in Mata and add per-tab layout. |
| D16 | 39 | S3 | CB FX | legend(po(9) top) names top first, title(T, prefix suffix) prints no ignored line, and values nested in legend(region()) are unchecked | match twoway's order and message. |
| E1 | 40 | S2 | RC CB | Marker symbols arrow, arrowf, A, a and pipe are refused, pipe is horizontal, point is 8 px, V is filled, shorthands are full size and non-Stata names are accepted | add the arrow marker, vertical pipe, 1 px point, hollow V and small shorthands, and refuse the non-Stata names. |
| E2 | 40 | S2 | RC | Line-pattern formula strings are refused, named pattern geometry differs from Stata's and mlpattern() is pending | parse the formula grammar into dash arrays scaled by width, copy the style files' ratios and draw mlpattern(). |
| E12 | 40 | S3 | CB | translate_msymbol and translate_lpattern lower-case names where Stata style names are case-sensitive | measure twoway and match its case rule. |
| E4 | 41 | S3 | CB | Glued = stylelist forms and a parenthesised element reach the renderer as one unknown element | tokenise = inside elements and refuse the parenthesised form. |
| E5 | 41 | S3 | RC CB | A comma colour inside a structured sub-option is drawn black where twoway refuses r(198) | read comma RGB in every context and refuse where twoway does. |
| E7 | 41 | S3 | RC | A pstyle(p#) CI band under a scheme intensity above full is clamped to full | pass clamp=False on the band reader. |
| E8 | 41 | S3 | RC | rarea and rbar outlines are not stroked where twoway strokes them from the scheme | stroke from the scheme's area line style. |
| E13 | 41 | S3 | FX | _SIZE_MAP and _GSIZE_NUMERIC_PT_PER_UNIT are dead but kept and serialised, and histogram scheme opacity is unverified | drop the dead map and constant and verify histogram opacity with a test. |
| E9 | 42 | S3 | RC | Inline SMCL style runs and raised text with no Unicode form are drawn in the text's own style, and hline, space, dup, cmd, hi, ccl, center and links are drawn as typed | split a text into runs drawn as several Label objects, or document the limit with a measured example. |
| G1 | 43 | S2 | RC | Extended missing .a to .z are merged into one null in by(, missing) panels, marker labels, filters and tooltips | carry the missing code through export and the label writer. |
| G2 | 43 | S3 | RC | set dp comma is never read, %tC is converted without leap seconds and graph set font faces are not read | read c(dp), embed Stata's leap-second table and read graph set. |
| G3 | 43 | S3 | FX | Working columns are generated in the user's data, user variables named x, y, top, count or density are shadowed in hover() and mlabel(), numbers are embedded as JSON text and the cell count counts every exported row | reserve derived names by prefix, use binary arrays and count planned rows. |
| G4 | 43 | S3 | FX | Carried hover, mlabel and row-id columns are upcast to object and handed to Bokeh as Python lists | keep numeric carried columns as arrays. |
| G5 | 43 | S3 | FX | One format-writer model is emitted per distinct tick format and per tooltip kind | share one writer per page. |
| E10 | 44 | S3 | RC | User and third-party style files are not read, 57 Stata style names draw default attributes with a note, and a scheme cannot redefine a linestyle or areastyle | add a general resolver over the 161 style files and the scheme's own class directives. |
| D15 | 45 | S3 | RC | Date #N ticks agree with _tsnatscale on 52 to 98 percent of ranges, xtick(#N) and xlabel(minmax) are held after a move, and the margin is a build-time fraction | fit more measured ranges or embed Stata's ticks and re-place after a move. |
| C11 | 46 | S3 | RC | lpoly edge cases: tiny gaussian weights counted toward the two-observation rule, round-off cases, pwidth(0) and pwidth(+800) rc differences, and an empty line under a five-row if | measure twoway, then match or document. |
| C12 | 46 | S3 | RC | function under by() is evaluated once where twoway evaluates once per panel, and a malformed y form is echoed as typed | evaluate per panel. |
| C16 | 46 | S3 | FX | A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted | tag the recast renderer for the recount. |
| G6 | 46 | S3 | RC | Fractional %t values are floored on load and join-order edge cases differ | measure twoway and match. |
| G7 | 46 | S3 | RC CB | %d and %tb axis formats are drawn %9.0g with a note and xvarformat(bogus) is noted where twoway refuses | write business dates and copy twoway's error. |
| F5 | 46 | S3 | FX | The map_qfitci docstring, the module header and the _dash_fold_typed comment describe code that no longer exists | fix the three comments. |
| F2 | 47 | S3 | RC | The function points-free fallback evaluates ten math names only | extend the fallback to comparisons, cond(), n-ary min and max, round, int, ln, normal, normalden, c(pi) and missing codes. |
| F3 | 47 | S3 | FX | Stata ground truth is missing for weighted qfitci and fpfitci bands, stdf and stdr under fw, the six kernels on lpolyci, pattern lengths and on-edge values | extract and pin each. |
| H2t | 48 | S3 | FX | No per-graph data table shows the rows a graph draws (the data table) | add a folded, toggled per-graph DataTable of the drawn rows in Stata display formats and value labels, virtual scrolling, sortable, row-capped, in both modes. |
| H2f | 49 | S3 | FX | Filters lack a multi-select dropdown, a (missing) option, a slider direction and a reset button (the filter widgets) | add the four widgets in both modes. |
| H2k | 50 | S3 | FX | KPI cards take no weights and lack kurtosis, semean and range (the KPI statistics) | add weights and the three statistics in both modes. |
| H2l | 51 | S3 | FX | One link group only, brush cannot act as a filter, a brush on bars or histograms drives nothing and concurrent brushes are not intersected (the link groups and brush) | add several link groups, brush-as-filter, bin and bar selection to rows, and intersected brushes in both modes. |
| H1 | 52 | S3 | FX | Saved-page JavaScript errors fail silently and saved sliders fire on every drag step | add an error banner through the nonce path and value_throttled on the saved page. |
| H2x | 53 | S3 | FX | No print stylesheet, and PNG and SVG export omit KPI cards, title, filters and the tab strip (the export and print parts) | add a print stylesheet and a composite PNG and SVG export. |
| K6 | 54 | S3 | FX | One aria-live region, no alt text and English-only interface | add keyboard-reachable widgets, ARIA labels on every filter, KPI card, tab and figure, and contrast checks, verified with axe-core. |
| H3 | 55 | S3 | FX | The served make_document builds on the event loop, catch_warnings can swap filters, a brush made during a move is cleared, and the bundle ships bokeh-mathjax | build off-loop and drop the mathjax component from the served resources. |
| H4 | 55 | S3 | CB | BOKEH_RESOURCES=cdn blanks the served page silently, BOKEH_MINIFIED and BOKEH_DEV change the saved page silently, /health reports only ok, and the browser-launch return code is never read | reject or report each variable, deepen /health and read _op_rc. |
| H7 | 55 | S3 | FX | Four unprefixed Mata functions are dropped by name on repair, sys.argv is overwritten and not restored, and three names are left in __main__ | prefix the functions, save and restore argv and delete the names. |
| J1 | 56 | S3 | FX | The help says every supplied option is named in the note and its Unsupported section omits every name that reaches the generic note | generate the list from the pending blocks, _dash_rep_und_tab and the catch-all probes, and pin both ways. |
| J2 | 56 | S3 | FX | Help inconsistencies in the syntax line, the period-slider sentence, legend(ring(0)), msangle, the Not-drawn count, dot, the refusal-log claim and missing paragraphs | fix each sentence with its test. |
| J3 | 57 | S3 | FX | Ten plot types, dash serve, weights and csv appear in no example, the feature_tour header is stale and no coverage test exists | add a plot-types tour and a serve example and a coverage test. |
| J4 | 58 | S3 | FX | Stale tracking text in GAPS.md, ROADMAP.md, BUGS.md, DROPIN, TWOWAY_COVERAGE_AUDIT.md and several test docstrings | one reconciliation pass and tracking-document count checks. |
| J5 | 58 | S3 | FX | The served app's header says Launch with bokeh serve, ServerAppBuilder docstrings are stale, title_safe is dead and _SIZE_MAP is emitted | fix each. |
| J6 | 58 | S3 | FX | REMAINING.md and phases/ are superseded but in the tree with PARTIAL markers, and ROADMAP WP-01 to WP-11 headings lack the DONE suffix | mark the two documents historical and add the suffixes. |
| I2 | 59 | S3 | FX | No README, dash.pkg has no Author or KW lines, no net install instruction in the help, the Author section is titled Also see, and the Jump To list is short | write the README, the pkg lines, the install line and the help fixes. |
| I3 | 59 | S3 | FX | A failed dash_setup leaves installed packages in place and does not say what it installed, the served child is sys.executable, Unmet lists warnings beside a failure, and a dash_setup_lib.py in the working directory is found first | record installs, offer the uninstall line, and fix the four reporting and path defects. |
| I4 | 59 | S3 | FX | _dash_dep_versions() is printed nowhere but through Stata, so a hand-run renderer or app is silent, and Python below 3.7 dies at the parser | print the note from the renderer's and the app's main and accept the SyntaxError. |
| I5 | 59 | S3 | FX | Version headers disagree (dash_render.py 1.0.0 25mar2026, dash.ado and dash_parse.mata v2.0) and the pin reads only the Version lines | renumber every header and extend the pin to every file and header. |
| I7 | 59 | S3 | FX | The renderer bytecode is still cached under PLUS/py and ado uninstall leaves __pycache__ behind | wrap the renderer load in the dont_write_bytecode guard and pin with test_installed_layout.py. |
| K2 | 60 | S3 | FX | Stata end-to-end gaps: served layer-output assertions, computed layers on %t variables served, the serve start line, a served build from an installed tree, per-type by() parity, an inspect.getsource fallback | add each. |
| K3 | 60 | S3 | FX | Sixteen truth fixtures have no committed generator, nine carry absolute paths, there is no make truth and no metadata guard | add generators, a target and a guard. |
| K4 | 60 | S3 | FX | The server fixture leaks a process when __enter__ fails, no AST count of the app's dispatch, hand-written scheme-key enumeration, no CSS-guard served arm, two strict xfails | fix the leak and add the guards. |
| H6 | 60 | S3 | FX | The parity guard compares only glyphs, labels, arrowheads and KPI cards after a move and its oracle is the saved renderer, not the saved page's JS | extend the move profile and add a saved-JS move oracle. |
| I6 | 60 | S3 | FX | No secret scan, CI, ruff, pyflakes or bandit, the hooks CLAUDE.md relies on are git-ignored, and *.log is excluded only locally | add a CI workflow, a lint target and a secrets test, and track or document the hooks. |

`Why` (the Graded clause) is, by grade: S1 `a value the user gave is dropped or drawn wrong with no note`; S2 `a twoway form is refused, named and not drawn, or fails visibly`; S3 `fidelity, hygiene, coverage or documentation drift`.

## Appendix B: the 110 Tracked lines (TR-01.2; id order)

`- **<id> Tracked:** Open (WP-31 section NN).` for: A1 08, A2 08, A3 08, A4 08, A5 07, A6 07, A7 07, A8 07, B1 21, B2 21, B3 21, B4a 23, B4b 26, B4c 29, B5a 03, B5b 18, C1 02, C2 03, C3 04, C4 11, C5 12, C6 14, C7 14, C8a 15, C8b 17, C9 20, C10a 05, C10b 06, C10c 09, C11 46, C12 46, C13 31, C14 34, C15 34, C16 46, C17 34, C18 06, D1 24, D2 27, D3 30, D4 31, D5 32, D6 33, D7 33, D8 34, D9 35, D10 36, D11 37, D12 38, D13 30, D14 39, D15 45, D16 39, E1 40, E2 40, E3 34, E4 41, E5 41, E6 33, E7 41, E8 41, E9 42, E10 44, E11 32, E12 40, E13 41, F1a 10, F1b 13, F1c 16, F1d 19, F1e 22, F1f 25, F1g 28, F2 47, F3 47, F4 06, F5 46, G1 43, G2 43, G3 43, G4 43, G5 43, G6 46, G7 46, H1 52, H2f 49, H2k 50, H2l 51, H2t 48, H2x 53, H3 55, H4 55, H6 60, H7 55, I2 59, I3 59, I4 59, I5 59, I6 60, I7 59, J1 56, J2 56, J3 57, J4 58, J5 58, J6 58, K2 60, K3 60, K4 60, K6 54. (The generator prints them; A3 is S08's entry per the manifest row 08 and DECISIONS A12.)

## Appendix C: code and text blocks

**`tracking-wp31`** (01-01; appended to test/test_tracking_documents.py):

~~~~python tracking-wp31
# ===========================================================================
# WP-31's entries (item 10 of the module docstring)
# ===========================================================================

#: WP-31 (.ultraplan/sections/index.md A4): the BUGS.md entries S01 opened,
#: one per manifest row id, by id, with their exact titles, one key per line
#: in Appendix A order.  A section's closing commit closes the entry in place
#: and deletes its own key line.  S61 leaves it {}.
@@WP31_OPEN@@

#: Every WP-31 entry, permanently, and the CHANGELOG.md lists of the current
#: release its line belongs in (section-01 Appendix A).
@@WP31_LISTS@@

#: The section that closes each entry (index.md "Section manifest").
@@WP31_SECTION@@

WP31_ALL = tuple(WP31_LISTS)

_WP31_ID = r"[A-K]\d{1,2}[a-gkltx]?"
_WP31_MARKER = re.compile(r"<!-- WP-31 (%s) -->" % _WP31_ID)
_WP31_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-31 section (\d{2}) has not landed\."
    r" Graded S[1-3] \(WP-31\): \S")
_GAPS3_ROW = re.compile(r"^\| (?P<id>[A-K]\d{1,2}) \| (?P<gap>.+?) \| (?P<sev>S[1-3][^|]*)\| ")
_GAPS3_TRACKED = re.compile(r"^- \*\*(?P<id>%s) Tracked:\*\* (?P<text>\S.*)$" % _WP31_ID)
_GAPS3_OPEN = re.compile(r"^Open \(WP-31 section (\d{2})\)\.$")
#: A closing commit writes "commit pending"; the merger's step k.3b rewrites
#: it to the landed sha on s3-bugs (DECISIONS A11), so the reader accepts
#: both and the batch-end gate (G2) and S61.3 forbid "pending".
_GAPS3_CLOSED = re.compile(
    r'^Closed in WP-31, BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40}|pending)\.$')
_GAPS3_PARTLY = re.compile(
    r'^Partly closed in WP-31 \(section (\d{2}), commit ([0-9a-f]{7,40}|pending)\): '
    r'(\S.*); open: (\S.*) \(BUGS\.md "([^"]+)"\)\.$')


def _wp31_markers(text):
    return _WP31_MARKER.findall(text)


def _wp31_open_problems(open_map, entries):
    """As _wp30_open_problems, for WP-31 (WP31_ALL, _WP31_OPEN_FORM,
    WP31_SECTION)."""
    bad = []
    unknown = sorted(set(open_map) - set(WP31_ALL))
    if unknown:
        bad.append("ids WP-31 does not have: %s" % unknown)
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
            bad.append("%s: %r is closed; delete its WP31_OPEN key"
                       % (pid, title))
            continue
        form = _WP31_OPEN_FORM.match(e["fields"].get("Resolution", ""))
        if not form:
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-31 "
                       "section NN has not landed. Graded S1|S2|S3 (WP-31): "
                       "...'" % (pid, title))
        elif int(form.group(1)) != WP31_SECTION.get(pid):
            bad.append("%s: its Resolution names section %s, not %s"
                       % (pid, form.group(1), WP31_SECTION.get(pid)))
    return bad


def _wp31_marker_problems(open_ids, markers):
    bad = ["a marker names %s, which WP-31 does not have" % m
           for m in sorted(set(markers) - set(WP31_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP31_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp31_closure_problems(open_ids, markers, entries):
    bad = []
    for pid in WP31_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-31, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp31_list_problems(lists_map, changelog):
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-31 %s -->" % pid, "(WP-31, %s)" % pid
        for n in wanted:
            body = bodies.get(n)
            if body is not None and mark not in body and line not in body:
                bad.append("%s: '### %s' holds neither its marker nor a line "
                           "ending %s" % (pid, n, line))
        for h, body in lists.items():
            if any(h == n or h.startswith(n + " (") for n in wanted):
                continue
            if mark in body:
                bad.append("%s: its marker sits under '### %s'" % (pid, h))
            if line in body:
                bad.append("%s: a line ending %s sits under '### %s'"
                           % (pid, line, h))
    return bad


def _parse_gaps3(text):
    """(rows, tracked, dupes): rows {table id: gap text}, tracked
    {entry id: text of its Tracked line}, dupes the entry ids with two
    Tracked lines.  Only GAPS3.md's table rows and its section 9 lines are
    read."""
    rows, tracked, dupes = {}, {}, []
    for ln in text.split("\n"):
        m = _GAPS3_ROW.match(ln)
        if m:
            rows[m.group("id")] = m.group("gap")
        t = _GAPS3_TRACKED.match(ln)
        if t:
            if t.group("id") in tracked:
                dupes.append(t.group("id"))
            tracked[t.group("id")] = t.group("text")
    return rows, tracked, dupes


def _gaps3_problems(rows, tracked, dupes, open_ids, entries, sha_exists):
    """Every WP-31 id has one Tracked line whose table row exists; an Open
    line names the id's section and the id is open; a Closed line names a
    closed entry's title and a commit that exists (or "pending", before the
    merger's step k.3b), and the id is not open; a Partly line names an
    existing commit (or "pending") and an open residual entry."""
    bad = ["%s has two Tracked lines" % d for d in dupes]
    bad += ["a Tracked line names %s, which WP-31 does not have" % t
            for t in sorted(set(tracked) - set(WP31_ALL))]
    for pid in WP31_ALL:
        if pid not in tracked:
            bad.append("%s: GAPS3.md has 0 Tracked lines" % pid)
            continue
        if re.sub(r"[a-z]$", "", pid) not in rows:
            bad.append("%s: GAPS3.md has no table row for it" % pid)
        text = tracked[pid]
        o, c, p = (_GAPS3_OPEN.match(text), _GAPS3_CLOSED.match(text),
                   _GAPS3_PARTLY.match(text))
        if o:
            if int(o.group(1)) != WP31_SECTION[pid]:
                bad.append("%s: Open names section %s, not %s"
                           % (pid, o.group(1), WP31_SECTION[pid]))
            if pid not in open_ids:
                bad.append("%s: Tracked Open but its entry is closed" % pid)
        elif c:
            title, sha = c.group(1), c.group(2)
            if pid in open_ids:
                bad.append("%s: Tracked Closed but its entry is open" % pid)
            if not [e for e in entries if e["closed"] and e["title"] == title]:
                bad.append("%s: no closed BUGS.md entry is titled %r"
                           % (pid, title))
            if sha != "pending" and not sha_exists(sha):
                bad.append("%s: commit %s does not exist" % (pid, sha))
        elif p:
            if p.group(2) != "pending" and not sha_exists(p.group(2)):
                bad.append("%s: commit %s does not exist" % (pid, p.group(2)))
            if not [e for e in entries if not e["closed"]
                    and e["title"] == p.group(5)]:
                bad.append("%s: no open BUGS.md entry is titled %r"
                           % (pid, p.group(5)))
        else:
            bad.append("%s: Tracked line %r is in none of the three forms"
                       % (pid, text))
    return bad


def _sha_exists(sha):
    return _git("cat-file", "-e", sha + "^{commit}").returncode == 0


class TestWp31Tracking:
    """WP-31's entries (index.md A4; section-01): open in BUGS.md naming
    their section, tracked Open in GAPS3.md section 9, with a marker in each
    CHANGELOG list they belong to, until their section lands; then closed,
    tracked Closed or Partly, with no marker left and a Resolution naming
    (WP-31, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        assert not _wp31_open_problems(WP31_OPEN, entries), "\n".join(
            _wp31_open_problems(WP31_OPEN, entries))

    def test_an_open_entry_keeps_its_marker(self):
        bad = _wp31_marker_problems(set(WP31_OPEN),
                                    _wp31_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_entry_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp31_closure_problems(
            set(WP31_OPEN), set(_wp31_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_entry_sits_in_its_changelog_lists(self):
        assert WP31_ALL == tuple(WP31_LISTS) and len(WP31_ALL) == 110
        assert tuple(WP31_SECTION) == WP31_ALL
        assert set(WP31_SECTION.values()) == set(range(2, 61))
        bad = _wp31_list_problems(WP31_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_every_entry_has_one_gaps3_tracked_line(self, bugs):
        entries, _p = bugs
        rows, tracked, dupes = _parse_gaps3(_read("GAPS3.md"))
        bad = _gaps3_problems(rows, tracked, dupes, set(WP31_OPEN), entries,
                              _sha_exists)
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("### Results that change\n\n<!-- WP-31 C1 -->\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-31 C10a --><!-- WP-31 H2t -->\n"
                "### Fixed in WP-31\n\n<!-- WP-31 F1g -->\n")
        assert _wp31_markers(text) == ["C1", "C10a", "H2t", "F1g"]
        assert _wp31_markers("<!-- WP-30 P1.1a --> <!-- WP-31 C1-->") == []
        assert _wp31_markers("<!-- WP-31 B5a --><!-- WP-31 B5b -->") == [
            "B5a", "B5b"]

    def test_the_wp31_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-31 section 02 has not landed. "
                     "Graded S1 (WP-31): dropped.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01nov2026 (WP-31, C2). Done.")]
        assert _wp31_open_problems({"C1": "T1"}, good) == []
        for open_map, entries, says in (
                ({"C1": "T2"}, good, "is closed"),
                ({"C1": "T9"}, good, "0 BUGS.md entries"),
                ({"C1": "T1"}, [entry("T1", False, open_form.replace(
                    "02", "03"))], "names section 03, not 2"),
                ({"Z9": "T1"}, good, "does not have"),
                ({"C1": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote")):
            assert any(says in b for b in _wp31_open_problems(
                open_map, entries)), (says, open_map)
        assert _wp31_marker_problems({"C1"}, []) == [
            "C1 is open and CHANGELOG.md holds no marker for it"]
        others = set(WP31_ALL) - {"C2"}
        assert _wp31_closure_problems(others, others, good) == []
        assert _wp31_closure_problems(others, others, good[:1]) == [
            "C2 is closed and no closed BUGS.md entry's Resolution holds "
            "(WP-31, C2)"]
        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-31 C1 -->\n"
               "### Fixed in WP-31\n\n- x. (WP-31, J1)\n")
        assert _wp31_list_problems({"C1": ("Results that change",),
                                    "J1": ("Fixed in WP-31",)}, log) == []
        assert _wp31_list_problems({"J1": ("Results that change",)}, log) == [
            "J1: '### Results that change' holds neither its marker nor a "
            "line ending (WP-31, J1)",
            "J1: a line ending (WP-31, J1) sits under '### Fixed in WP-31'"]

    def test_the_gaps3_readers(self):
        text = ("| ID | Gap | Sev | Register | Evidence | Task |\n"
                "|---|---|---|---|---|---|\n"
                "| C1 | heads are fixed | S1 | P2.8 | r.py:1 | fix |\n"
                "| C8 | colorvar on 4 types | S2 | P2.10 | d.ado:2 | route |\n"
                "## 9. Tracking\n\n- **C1 Tracked:** Open (WP-31 section 02).\n"
                '- **C8a Tracked:** Closed in WP-31, BUGS.md "T2", commit '
                "0123abc.\n- **C8b Tracked:** Partly closed in WP-31 (section "
                '17, commit 0123abc): aliases; open: pcycle (BUGS.md "R1").\n')
        rows, tracked, dupes = _parse_gaps3(text)
        assert rows == {"C1": "heads are fixed", "C8": "colorvar on 4 types"}
        assert sorted(tracked) == ["C1", "C8a", "C8b"] and dupes == []
        entries = [{"title": "T2", "closed": True, "fields": {}},
                   {"title": "R1", "closed": False, "fields": {}}]
        tracked_all = {pid: "Open (WP-31 section %02d)." % WP31_SECTION[pid]
                       for pid in WP31_ALL}
        tracked_all.update(tracked)
        bad = _gaps3_problems(rows, tracked_all, dupes,
                              set(WP31_ALL) - {"C8a"}, entries,
                              lambda s: s == "0123abc")
        assert bad == [], bad
        bad = _gaps3_problems(rows, tracked_all, dupes, set(WP31_ALL),
                              entries, lambda s: False)
        assert "C8a: Tracked Closed but its entry is open" in bad
        assert "C8a: commit 0123abc does not exist" in bad
        assert "C8b: commit 0123abc does not exist" in bad
        rows2 = dict(rows)
        rows2.pop("C1")
        assert "C1: GAPS3.md has no table row for it" in _gaps3_problems(
            rows2, tracked_all, dupes, set(WP31_ALL), entries, lambda s: True)
        assert "C1: GAPS3.md has 0 Tracked lines" in _gaps3_problems(
            rows, {}, [], set(WP31_ALL), entries, lambda s: True)
        # "commit pending" (DECISIONS A11) passes without a sha check.
        pend = dict(tracked_all)
        pend["C8a"] = 'Closed in WP-31, BUGS.md "T2", commit pending.'
        pend["C8b"] = ("Partly closed in WP-31 (section 17, commit pending): "
                       'aliases; open: pcycle (BUGS.md "R1").')
        assert _gaps3_problems(rows, pend, dupes, set(WP31_ALL) - {"C8a"},
                               entries, lambda s: False) == []
        # Split-row ids (B5a/B5b, C10a..c, F1a..g, H2f/k/l/t/x) parse.
        for pid in ("B5a", "B5b", "C10c", "F1g", "H2t"):
            m = _GAPS3_TRACKED.match(
                "- **%s Tracked:** Open (WP-31 section 03)." % pid)
            assert m and m.group("id") == pid, pid
~~~~

**`docstring-item-10`** (01-02; after :59):

~~~~text docstring-item-10
10. WP-31's entries (.ultraplan/sections/index.md A4) are open in BUGS.md
   in the form "Not fixed because WP-31 section NN has not landed. Graded
   S1|S2|S3 (WP-31): ...", NN being the section WP31_SECTION names, listed
   in WP31_OPEN, which with WP29_OPEN and WP30_OPEN exempts them from the
   release guard, tracked "Open (WP-31 section NN)." in GAPS3.md section 9,
   with a "<!-- WP-31 <id> -->" marker in each CHANGELOG list WP31_LISTS
   names, until their section lands; then the key is gone, the Tracked
   line reads Closed or Partly closed, no marker is left, each list holds a
   line ending "(WP-31, <id>)", and a closed Resolution holds it too.
~~~~

**`fixed-in-wp31`** (01-04; above :800):

~~~~text fixed-in-wp31
### Fixed in WP-31

Gaps the drop-in audit of 10oct2026 (GAPS3.md) recorded that WP-31 fixed
without changing a drawn result; the results that changed are the WP-31
group under Results that change, and the newly refused forms sit under
Changed behaviour.
~~~~

**`truth-header`** (01-06; replaces lines 1-28 of the copied script):

~~~~text truth-header
*! test_wp31_truth.cscript
*! WP-31's ONE new certification script (.ultraplan/sections/index.md A5):
*! every comparison with twoway's drawing or with Stata's own values that
*! WP-31's sections need lives here, one block per GAPS3 row, appended
*! above the "append new blocks above this line" marker in section order,
*! so the certification suite grows by one script.  Refusal, message and
*! return-code checks join the EXISTING script for their area (merge rule
*! R1); this script never gains one of those.
*!
*! S01 is the scaffold smoke (U01-1).  A section appends its blocks
*! `* ==== S<NN> <row>: <what> ====` ... `* ==== end S<NN> ====`, its
*! helper programs directly above its first header, and writes only inside
*! its own blocks.  Case ids are U<NN>-<k>.
*!
*! Usage: via run_all_cscripts.do (registered as its block 70).  One
*! block alone: WP31_ONLY=S<NN> in the driver's environment; a section with
*! no block then ends "no case ran" and r(9).  Each block prints "S<NN>
*! start" and "S<NN> end" with the date and time, so S61 can time it.  The
*! suite runs it in every session; DASH_CERT_SHARD=k/N runs part k of N of
*! the blocks (the "parts" section below); a part with no block ends 0.
~~~~

**`empty-part`** (01-06; first statement inside the summary's `if \`ncase' == 0 {`):

~~~~text empty-part
    if `w31_N' > 1 & `"`macval(only)'"' == "" & "`w31_run'" == "" {
        display as text "test_wp31_truth: part `w31_k'/`w31_N' has no block to run"
        display as text "============================================================"
        exit 0
    }
~~~~

(`w31_k`, `w31_N` and `w31_run` are the parts section's locals, which are still in scope in the summary; `only` is the summary's own local.)

**`hygiene-wp31`** (01-01; after test_cscript_hygiene.py:1215):

~~~~python hygiene-wp31
# ---------------------------------------------------------------------------
# WP-31's truth script: S01's scaffold and the blocks sections append
# ---------------------------------------------------------------------------

_WP31_TRUTH = os.path.join(_HERE, "test_wp31_truth.cscript")
_W31_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W31_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W31_MARK = "* ==== append new blocks above this line ===="
_W31_HEAD = re.compile(r"^(scaffold|[A-K]\d{1,2}[a-gkltx]?): \S")


def _wp31_blocks(src):
    """As _wp30_blocks, with WP31_ONLY and w31_run, a header naming one
    GAPS3 row id (a section may own several blocks, one per row), and
    section order non-decreasing."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W31_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W31_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, cur = [], None
    for n, ln in enumerate(lines, 1):
        o, c = _W31_OPEN.match(ln.rstrip()), _W31_CLOSE.match(ln.rstrip())
        if o:
            if cur:
                bad.append("%s (line %d) is not closed before line %d"
                           % (cur[0], cur[1], n))
            cur = (o.group(1), n, o.group(2))
        elif c:
            if cur is None or c.group(1) != cur[0]:
                bad.append("line %d closes %s, which is not the open block"
                           % (n, c.group(1)))
            else:
                blocks.append((cur[0], cur[1], n))
                if not _W31_HEAD.match(cur[2]):
                    bad.append("%s (line %d) names no GAPS3 row ('<id>: "
                               "<what>')" % (cur[0], cur[1]))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur[:2])
    for k, (sec, first, last) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1]
                if ln.strip() and not ln.strip().startswith(("//", "*"))]
        if code[:2] != ["local only : env WP31_ONLY",
                        'if inlist("`only\'", "", "%s") & `: list posof '
                        '"%s" in w31_run\' {' % (sec, sec)]:
            bad.append("%s (line %d) is not gated by WP31_ONLY=%s"
                       % (sec, first, sec))
        timed = ['display as text "%s %s " c(current_date) " " '
                 'c(current_time)' % (sec, w) for w in ("start", "end")]
        if code[2:3] != timed[:1] or code[-2:] != [timed[1], "}"]:
            bad.append("%s (line %d) does not print its start line first and "
                       "its end line last" % (sec, first))
        if last > mark:
            bad.append("%s (line %d) is below the marker" % (sec, first))
        if k and sec < blocks[k - 1][0]:
            bad.append("%s (line %d) follows %s: blocks go in section order"
                       % (sec, first, blocks[k - 1][0]))
    return blocks, bad


class TestTheWp31TruthScript:

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP31_TRUTH)
        order = ['cscript "WP-31 truth', "SKIP: Python not available.",
                 'do "cert_helpers.do"', 'do "cert_svg.do"',
                 "// ---- parts: begin", "local w31_sh : environment "
                 "DASH_CERT_SHARD", "// ---- parts: end", "* ==== S01 ",
                 "local only : env WP31_ONLY", "* ==== end S01 ====",
                 _W31_MARK, "has no block to run",
                 "test_wp31_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_timed_closed_and_in_section_order(self):
        blocks, bad = _wp31_blocks(_read(_WP31_TRUTH))
        assert not bad, "\n".join(bad)
        assert blocks and blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        def block(sec, head, body=""):
            return ("* ==== %s %s ====\nlocal only : env WP31_ONLY\n"
                    'if inlist("`only\'", "", "%s") & `: list posof "%s" '
                    'in w31_run\' {\n'
                    '    display as text "%s start " c(current_date) " " '
                    "c(current_time)\n%s"
                    '    display as text "%s end " c(current_date) " " '
                    "c(current_time)\n}\n* ==== end %s ====\n"
                    % (sec, head, sec, sec, sec, body, sec, sec))
        good = ('cscript "x"\n' + block("S01", "scaffold: smoke", "    // a\n")
                + "\n" + block("S14", "C6: cmissing") + "\n"
                + block("S14", "C7: recast") + _W31_MARK + "\nexit 9\n")
        blocks, bad = _wp31_blocks(good)
        assert bad == [], bad
        assert [b[0] for b in blocks] == ["S01", "S14", "S14"], blocks
        for text, says in (
                (good.replace('"S14") &', '"S01") &'), "not gated"),
                (good.replace("* ==== end S14 ====\n", "", 1), "not closed"),
                (good.replace("C7: recast", "nothing"), "names no GAPS3 row"),
                (good.replace("S14", "S00"), "section order"),
                (good.replace(_W31_MARK + "\n", ""), "appears 0 times")):
            assert any(says in b for b in _wp31_blocks(text)[1]), (says,)
~~~~

## Appendix D: register corrections (TR-01.8; 01-05)

Each edit asserts the quoted current text first.

1. GAPS2.md:807, currently `- **Tracked:** new.` (under `### C14.` at :802) → `- **Tracked:** Closed in WP-28, BUGS.md "A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above", commit b06b662; GAPS3 §6: the histogram edge rule is pinned by test/test_histogram_edge_rule.py; was: new`.
2. GAPS2.md:1566, currently `- **Tracked:** new.` (under `### H10.` at :1561) → `- **Tracked:** new; half closed (GAPS3 §6): the dash_setup_lib load is guarded (dash.ado:6296-6299, dash_setup.ado:1080-1083, PYTHONDONTWRITEBYTECODE in dash_setup_lib.py:43), the renderer load at dash.ado:6118-6133 is not. GAPS3: I7.`
3. GAPS2.md, the `- **Tracked:**` line under each of these headings gains the suffix ` GAPS3: <rows>.` (one space, then the text; appended after the line's last character): A2 `C1`; A5 `B1, B2, B3, B4`; A8 `C8`; A11 `(BUGS.md:2559, kept by WP-30 M6)`; A12 `C3`; A14 `B5`; A15 `C10`; B10 `D1`; B19 `D2`; B24 `D15`; B28 `D2`; B30 `D5`; B33 `D5`; D4 `E2`; D14 `D5, E11`; E5 `H1, H2l`; E6 `D9`; E7 `H2k`; E9 `H2l`; E11 `H1`; E12 `H1`; E13 `H2f`; E15 `D14`; G7 `G2`; G12 `G1`; G17 `A5`; G18 `C9`; H8 `I3`; I1 `H4`; I9 `I6`; J1 `G2`; J10 `J3`; K4 `H4`; K10 `K5 (out of scope, PRD §7)`; K11 `J4`; X7 `H7`. (36 lines; C14 and H10 are items 1-2.)
4. DROPIN-REMAINING.md:380 (`1. **Retire or fix \`scripts/regen_option_surface.py\`.** ...` under `### P3:`) gains the suffix ` [Written closed: retired by a hard sys.exit (scripts/regen_option_surface.py:17), commit 44f8ab0 (WP-30 P1.34).]`.
5. DROPIN-REMAINING.md, each of these rows gains the suffix ` [Narrowed 10oct2026 (GAPS3 §6): <text>]` at the end of its last line: :173 P2.1 `unknown layout() names are refused now (dash_parse.mata:1650-1668); only the served same-cell collision and tabs() stay silent (GAPS3 D14)`; :209 P2.12 (the `Effort M. Sources:` line) `lwidth(none) and mlabtextstyle are closed; the rest is GAPS3 E2, E3`; :218 P2.14 (the row's last line) `msize(1e400) and per-series mlabel(make rep78) are closed; one element naming several variables remains (GAPS3 C10)`; :246 P2.25 `a brushed histogram is drawn at full intensity, not dimmed (dash.sthlp:4418); drives nothing stands (GAPS3 H1)`; :262 P2.29 `dash.pkg states Requires: Stata 19 or later and a version; the .pyc leg is GAPS3 I7; README, Author, KW and rollback remain (GAPS3 I2, I3)`; :288 P2.48 `the saved page ships no mathjax (three tests assert it); the served bundle still does (GAPS3 H3)`; :433 P3.9 `dev dependencies are declared in test/requirements-*.txt; CI, lint, bandit and secrets remain (GAPS3 I6)`.

## Appendix E: `s01_entries.py` (TR-01.9; 01-01)

~~~~python s01-entries
"""S01's entry generator: reads section-01's Appendix A and GAPS3.md's
tables; prints by sub-command.  Usage:
  python3 s01_entries.py bugs|tracking|readers|count <section file>
  python3 s01_entries.py markers RC|CB|RQ|FX <section file>
Nothing is written; the task redirects the output."""
import os
import re
import sys

LISTS = {"RC": "Results that change", "CB": "Changed behaviour",
         "RQ": "Requirements", "FX": "Fixed in WP-31"}
WHY = {"S1": "a value the user gave is dropped or drawn wrong with no note",
       "S2": "a twoway form is refused, named and not drawn, or fails visibly",
       "S3": "fidelity, hygiene, coverage or documentation drift"}
SLUG = re.compile(r"^\| (\d{2}) \| ([a-z][a-z0-9-]*) \|")
ROW = re.compile(r"^\| ([A-K]\d{1,2}[a-gkltx]?) \| (\d{2}) \| (S[1-3]) \| "
                 r"([A-Z ]+) \| (.+?) \| (.+?) \|$")
G3 = re.compile(r"^\| ([A-K]\d{1,2}) \| (.+?) \| (S[1-3][^|]*)\| ([^|]*)\| "
                r"([^|]*)\| ([^|]*)\|$")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def appendix_a(text):
    sect = text.split("## Appendix A", 1)[1].split("## Appendix B", 1)[0]
    rows = []
    for ln in sect.split("\n"):
        m = ROW.match(ln)
        if m:
            rows.append(dict(id=m.group(1), sec=int(m.group(2)),
                             grade=m.group(3), lists=m.group(4).split(),
                             title=m.group(5), fix=m.group(6)))
    assert len(rows) == 110, len(rows)
    return rows


def names(root):
    idx = read(os.path.join(root, ".ultraplan", "sections", "index.md"))
    # Only the manifest table: the batch table's rows (`| 21 | 61 |`) would
    # otherwise match a digits-only slug (REVIEW-1 R1-08).
    idx = idx.split("## Section manifest", 1)[1]
    idx = idx.split("## Batch execution order", 1)[0]
    out = {}
    for ln in idx.split("\n"):
        m = SLUG.match(ln)
        if m:
            out[int(m.group(1))] = m.group(2).replace("-", " ")
    assert len(out) == 61, len(out)
    return out


def gaps3(root):
    out = {}
    for ln in read(os.path.join(root, "GAPS3.md")).split("\n"):
        m = G3.match(ln)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(5).strip())
    return out


def part(title):
    m = re.search(r" \((the [^()]+)\)$", title)
    return m.group(1) if m else ""


def main(argv):
    cmd, sf = argv[1], argv[-1]
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(sf))))
    rows, nm, g3 = appendix_a(read(sf)), names(root), gaps3(root)
    if cmd == "bugs":
        out = [""]
        for r in rows:
            gap, evid = g3[re.sub(r"[a-z]$", "", r["id"])]
            p = part(r["title"])
            desc = ("%s; the whole row reads: %s" % (p, gap)) if p else gap
            out += ["- [ ] Title: %s" % r["title"],
                    "  - File Names and Line Numbers: %s" % evid,
                    "  - Description: GAPS3.md %s, re-verified at 6370ca4: %s"
                    % (re.sub(r"[a-z]$", "", r["id"]), desc),
                    "  - Suggested fix: WP-31 section %02d (%s): %s"
                    % (r["sec"], nm[r["sec"]], r["fix"]),
                    "  - Resolution: Not fixed because WP-31 section %02d has "
                    "not landed. Graded %s (WP-31): %s."
                    % (r["sec"], r["grade"], WHY[r["grade"]]), ""]
        print("\n".join(out[:-1]))
    elif cmd == "tracking":
        key = lambda r: (r["id"][0], int(re.sub(r"\D", "", r["id"])),
                         re.sub(r"^[A-K]\d+", "", r["id"]))
        out = ["", "## 9. Tracking", "",
               "One line per WP-31 entry (.ultraplan/sections/index.md, A4), "
               "rewritten in place by the entry's closing commit; "
               "test/test_tracking_documents.py::TestWp31Tracking reads "
               "exactly these forms:",
               "`Open (WP-31 section NN).`, `Closed in WP-31, BUGS.md "
               "\"<title>\", commit <sha>.`, or",
               "`Partly closed in WP-31 (section NN, commit <sha>): <what is "
               "closed>; open: <what remains> (BUGS.md \"<residual "
               "title>\").`",
               "A closing commit writes `commit pending`; the merger's step "
               "k.3b replaces it with the landed sha on s3-bugs (DECISIONS "
               "A11).", ""]
        out += ["- **%s Tracked:** Open (WP-31 section %02d)." % (r["id"], r["sec"])
                for r in sorted(rows, key=key)]
        print("\n".join(out))
    elif cmd == "readers":
        print("WP31_OPEN = {")
        for r in rows:
            print('    "%s": "%s",' % (r["id"], r["title"]))
        print("}\n\nWP31_LISTS = {")
        for r in rows:
            print('    "%s": (%s,),' % (r["id"], ", ".join(
                '"%s"' % LISTS[k] for k in r["lists"])))
        print("}\n\nWP31_SECTION = {")
        for r in rows:
            print('    "%s": %d,' % (r["id"], r["sec"]))
        print("}")
    elif cmd == "markers":
        want = argv[2]
        print("\n\n".join("<!-- WP-31 %s -->" % r["id"]
                          for r in rows if want in r["lists"]))
    elif cmd == "count":
        print(sum(len(r["lists"]) for r in rows))
        for k in LISTS:
            print(k, sum(1 for r in rows if k in r["lists"]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
~~~~
