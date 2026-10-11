# Section 01: Tracking foundation

> Part of: WP-30 · Items: none of its own; it opens the 56 entries (P1.1a-P1.35) that S02-S57 close (index.md "P1 coverage") · Risk: green · Batch: 0 (alone; merge order [1]) · Depends on: none (after step 0) · Blocks: 02-58 · Tasks: 8, 1 commit (`(WP-30 S01)`) · Case prefix: TF

## Review amendments

- Checked against manifest.json: Appendix A has exactly one row per section S02-S57, each id = manifest item+part, each name verbatim; Appendix B has 56 entries in that order, each Suggested fix and open Resolution naming its own section; `WP30_LISTS` rows equal index.md "P1 coverage" (34/5/7/23/4/10) and the grades 9/38/9. No change needed.
- `_wp30_list_problems` now also fails a `(WP-30, <id>)` line under a list its row does not name (BR-01.3 required it; the code checked only markers), with a unit assertion in `test_the_wp30_problem_readers`; checked by executing the readers and both reader tests against HEAD's `test_tracking_documents.py` (pass). No count or prototype figure moves.
- TR-01.10.1 now gives the key-deletion check (`grep -c '^    "<id>": "'` → 0). The bare `grep -c '"<id>"'` → 0 that 31 sections' closing verify lines use prints 2 or more after a correct close (permanent `WP30_LISTS`/`WP30_SECTION` rows; measured 3 while open); cross-file fixes recorded in review-notes/g01.md.
- P-1 turned into a marked Maintainer question with a recommendation; index.md step 0a needs it named (cross-file, g01.md).
- Spot-checked at HEAD: test_tracking_documents.py:512-516 and :45 and its last line, hygiene pins :294/:313/:322, BUGS.md 2850 lines, CHANGELOG.md 824, run_all_cscripts.do :1767/:1769/:1772, function_test_map.py :800/:894-895, program_coverage_map.py :298/:338/:608, `_glyph_layer_lines` at dash_render.py:32834, Appendix B anchors of P1.1a: all hold.
- Rejected: none.
- (cross-file pass) Appendix A row P1.17a: `WP30_LISTS` "Results that change" -> "Results that change; Changed behaviour" (S14's rcap/rcapsym refusal, g03). Counts follow: 84 markers, Changed behaviour 24 (Overview, BR-01.4, TR-01.5, AC-01.3, task 01-04, completion criteria, commit body, Appendix D table), CHANGELOG 1001 lines and `### Fixed in WP-30` at :803 (derived; the prototype line keeps its measured 83/999/:801 and says so). index.md "P1 coverage" and A147 need the same change (not this file).
- (cross-file pass) S58.2 GAPS2 table: "D12, D16, D17: P1.2a" -> "D12, D17: P1.2a; D16: P1.2a, P1.3a" (D16-a, the minor ticks, closes with S21 under register P1.2.7; S15 Notes).
- (cross-file pass) TR-01.10 item 4: a case whose code under test reads only the working directory may write a uniquely named file there, checked absent first and erased in the same case (S07 SX-05/SX-08, g02).

The review pass applied both lenses.
- Row 4 (ratification 06oct2026): S33's name is now "Marker-label and colour-key chrome; unread directives retained (P1.4 part b)" (Appendix A row and the P1.4b entry's Suggested fix, verbatim with manifest.json); the fix keeps every user-scheme directive in the parsed scheme and prints no note. The P1.4b title and its open-form Resolution are unchanged (they describe the defect as found; S33 closes the third clause by disposition).
- Row 27 (ratification 06oct2026): P2.49 is not filed (S08 fixes the brushed-copy bug), so the S58.1 note now expects 3 open BUGS.md entries after WP-30 (2559, 2595, 2601), not 4. No S01 entry, `WP30_OPEN` key or marker changes: S08's entry is still P1.12a.
- P-1 answered (ratification 06oct2026, row 29): the file stays and `_ROOT_ALSO` names it; the Maintainer question in Notes records the answer. Boundaries are unchanged (S01 does not edit `test/test_packaging.py`).

## Overview

WP-30 closes the 35 P1 items of `.ultraplan/handoff/DROPIN-REMAINING.md` ("### P1", lines 64-170), split into 56 entries, one per fix section (index.md A138, A140). At `c96facd` nothing in the repository records them: BUGS.md has no entry for any of them, CHANGELOG.md has no place for their lines, the certification suite has no script for the twoway comparisons the sections will add, the two coverage maps have no place for the sections' keys, and nothing checks that the served app's copy lists name only functions that exist. Two guards stand in the way of simply writing the entries:

- **The release guard.** `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2` (`test/test_tracking_documents.py:512-523`) turns the suite red on any open S1 or S2 entry outside `WP29_OPEN` (now `{}`). Measured on the prototype: removing one WP-30 key makes it fail on that entry (Evidence, "Prototype").
- **The hygiene pins.** `test/test_cscript_hygiene.py` counts the cscripts (67, :294) and the scripts that gate on Python (49, :313). A new script breaks both until they move.

After this section:
- **BUGS.md** carries the 56 entries open, graded S1 (9), S2 (38) or S3 (9), each naming its section, with the DROPIN text and its source ids (Appendix B).
- **`test/test_tracking_documents.py`** holds `WP30_OPEN` (56 keys), the permanent `WP30_LISTS`, `WP30_SECTION` and `WP30_ALL`, the readers, `TestWp30Tracking` (six tests), and a release guard that exempts exactly the titles `WP29_OPEN` and `WP30_OPEN` list.
- **CHANGELOG.md** holds 84 `<!-- WP-30 <id> -->` markers in six lists of the release `## 0.1.0, 02oct2026 (release candidate)`: Results that change 34 (under a `**WP-30 (drop-in P1, 03oct2026)**` group), Security 5, New 7, Changed behaviour 24, Requirements 4, and a new `### Fixed in WP-30` 10 (index.md A147, R4).
- **`test/test_wp30_truth.cscript`** exists with S01's smoke block (case TF-01) and one gated, timed stub block for each of S02-S57 in section order, registered as runner block `// 69.`, guarded by `TestTheWp30TruthScript`; the pins read 68 and 50.
- **The maps** carry one comment anchor per section (A148): 56 at the end of `FUNCTIONS`, 3 at the end of `SETUP_FUNCTIONS`, 56 each at the ends of `COVERAGE["dash.ado"]` and `COVERAGE["dash_parse.mata"]`, 4 at the end of `COVERAGE["dash_setup.ado"]`.
- **`TestTheServedAppCarriesEveryName::test_every_listed_name_exists`** (A149) holds every name in `_glyph_layer_lines`' two copy lists to a definition in `dash_render.py`.

It also writes down, once, the forms every later section follows (TR-01.10). No shipped file changes, and ROADMAP.md and the other tracking documents are not touched (A145): WP-30's ROADMAP entry is written by S58.

**Test order and commit rule (CLAUDE.md rules 4 and 7).** Task 01-01 writes the section's tests against the unmodified worktree (the `batch-0-base.txt` commit), saves their failure text to `<scratch>/s01/01-S01-failure.txt` and commits nothing; on the prototype 11 tests failed and the one guard test passed. Tasks 01-02 to 01-07 turn them green. Task 01-08 runs the full suite once through the queue and makes the section's one commit, `Open the WP-30 P1 entries, markers and truth script (WP-30 S01)`, whose body opens with the saved failure text.

## Risk: [green] — four test modules extended, one certification script added, two documents appended to; no shipped file changes

- **Why green.** No renderer, ado, Mata, scheme or help text moves. Every existing assertion passes unchanged except two count pins (67→68, 49→50), which move because a script is added, and the release guard, whose verdict on every entry outside the two allowances is unchanged.
- **Risk factors.**
  1. The allowance weakens the release guard.
  2. Fifty-six sections in 20 batches edit BUGS.md, CHANGELOG.md, `WP30_OPEN`, the truth script and the maps from parallel worktrees.
  3. `test/test_version_floor.py:91-95` reads `### Requirements` up to the next `### `, which becomes `### Fixed in WP-30`.
  4. **The suite is red at `c96facd`, before S01** (Evidence, "Baseline"): `test/test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` fails on the tracked root file `PhilSchummSuggestion.md` (added by 76e32d7). Step 0a's G0 and S01's own full run cannot be green until that is resolved, and S01 must not resolve it (Boundaries).
  5. A stub block has no case, so `WP30_ONLY=S<NN>` on a stub ends "no case ran" and r(9).
- **Mitigation.**
  1. Closed-world allowance: only titles `WP30_OPEN` names are exempt, only while each entry is open in the WP-30 form naming the section `WP30_SECTION` gives; a stale, closed or misnamed key fails `TestWp30Tracking`; S58.1 empties it.
  2. Entries, markers and stub blocks are separated by blank lines, keys and anchors sit one per line, and every later section edits only its own lines (Notes, "Merging"); `TestTheWp30TruthScript` checks block order, gating and timing.
  3. `test_version_floor.py` was run on the prototype: green.
  4. Precondition P-1 (Dependencies) and the open question in Notes.
  5. Measured and documented in the script's header; a section fills its stub before running it alone.

## Dependencies

- **Depends on:** step 0 of index.md "How to execute": 0g (the queue script), 0a (the plan commit, `(WP-30 S00)`), 0d (`<scratch>/batch-0-base.txt`). S01 may run before 0f (the ratified record) is answered (A151): no ratification row changes its form.
- **Precondition P-1:** a green full run needs `test_the_package_root_holds_only_what_ships_and_the_repositorys_own` green, which it is not at `c96facd`. The maintainer resolves it in a commit of their own before step 0a (moving the file out of the package root, or naming it in `_ROOT_ALSO`), so that the base S01's worktree is cut from is green. If it is not, task 01-08 stops before committing and reports.
- **Blocks:** every fix section (02-57) closes the entry S01 opens, deletes the key S01 adds, replaces the marker(s) S01 places and fills the stub S01 writes; S58 empties the allowance and removes empty map anchors.
- **Parallel batch:** none; batch 0 is S01 alone, and batch 1 is cut from the commit after S01 lands (`batch-1-base.txt`, index.md step 1).

## Evidence

All anchors were re-read at `c96facd` on branch `wp30-p1` (`git log --oneline -1` → `c96facd Merge branch 'wp29-p0'`; `git status --porcelain` → `?? .ultraplan/wp30/`).

### Baseline: the targeted files at `c96facd`

```
$ python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_version_floor.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_packaging.py test/test_test_integrity.py -q -n0 -p no:cacheprovider
FAILED test/test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own
1 failed, 549 passed in 16.87s
E  AssertionError: the package root holds files that neither ship nor belong to the repository's documents or configuration; move them to scripts/ or examples/: PhilSchummSuggestion.md
$ git ls-files PhilSchummSuggestion.md; git log --oneline -1 -- PhilSchummSuggestion.md
PhilSchummSuggestion.md
76e32d7 Made sure to include Phil's suggestion for how to build on Dash ...
$ python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -n0 -p no:cacheprovider
1 passed
```

Collected counts at `c96facd`: `test_tracking_documents.py` 41, `test_cscript_hygiene.py` 367, `test_statistical_helpers.py` 147.

### BUGS.md and the release guard

- **BUGS.md** has 2850 lines and 476 entries: 472 closed and 4 open (2523, 2559, 2595, 2601, each `Graded S3 (WP-27)`). It ends with one newline (`tail -c 2 BUGS.md | xxd -p` → `2e0a`). `_ENTRY`/`_FIELD` (:112-118) read `- [ ] Title:` and the four one-line fields.
- **`_references`** (:309-339) fails an entry that names a `test_*.py|cscript|do` file, a `file::Class` node or a `Test[A-Z]…` word that does not exist. A `_CASE_ID`-shaped token (`WP-30`, `REM-08-04-C7`, `GAPS2-D8-a`) is only ever found or ignored. So an open entry names no test, and source ids are safe (Appendix B was checked by script: no such reference, no `"` in a title, no `PLAN.md`).
- **The release guard** (`test/test_tracking_documents.py:512-523`):

  ```python
      def test_no_open_entry_is_s1_or_s2(self, bugs):
          entries, _p = bugs
          # WP-29's P0 entries stay open, S1 or S2, until their sections land
          # (WP29_OPEN); TestWp29Tracking holds each one to its WP-29 form.
          allowed = set(WP29_OPEN.values())
          bad = ["line %d: %s %s" % (e["line"], g, e["title"][:90])
                 for e in entries if not e["closed"]
                 and e["title"] not in allowed
  ```

- **WP-29's block** (:1240-1525), which this section mirrors and does not edit: `WP29_OPEN = {}` (:1251), `WP29_LISTS` (:1257), `_WP29_OPEN_FORM` (:1285-1287), the readers `_wp29_markers`, `_changelog_lists`, `_changelog_list`, `_wp29_open_problems`, `_wp29_marker_problems`, `_wp29_closure_problems`, `_wp29_list_problems` (:1290-1395), `TestWp29Tracking` (:1398-1525). `_changelog_lists` and `_changelog_list` are generic and are reused, not copied. The module docstring's last item is 8 (:37-45).

### CHANGELOG.md (824 lines) and the one test that reads a list

`grep -n '^## \|^### \|^\*\*WP-' CHANGELOG.md`: `3:## 0.1.0, 02oct2026 (release candidate)`, `10:### Results that change`, `142:**WP-28 …**`, `238:**WP-29 (drop-in P0, 30sep2026)**`, `315:### Security`, `411:### New`, `452:### Fixed`, `513:### Changed behaviour (may need your do-files changed)`, `598:### Removed`, `607:### Requirements`, `653:### Fixed in WP-29`. The last items of the lists S01 extends end at 313 `(WP-29, P0.20)`, 409 `(WP-29, P0.14)`, 450 `(WP-23).`, 596 `(WP-29, P0.12a)` and 651 `(WP-29, P0.19)`, each followed by a blank line; `grep -c '<!--' CHANGELOG.md` → 0. `test/test_version_floor.py:91-95` reads `### Requirements` to the next `### `; no other test reads a CHANGELOG list.

### The runner, the pins and WP-29's script

- `test/run_all_cscripts.do` (1794 lines): block 68 is :1743-1769 (`// 68. test_wp29_truth.cscript …` at :1744, `[ FAIL] test_wp29_truth.cscript` at :1767, closing `}` at :1769), then a blank line and the `// Summary` banner (:1771-1773). `scripts/cert_verdict.py` registers a script by its `do "<name>.cscript"` line, and `test_cert_verdict.py::TestTheRegisteredScripts::test_the_real_runner_registers_every_script_in_test` requires the runner's list to equal the files on disk.
- `test/test_cscript_hygiene.py` (975 lines): `assert len(_CSCRIPTS) == 67` (:294, comment :281-293), `assert len(names) == 49` (:313, comment :307-312), `assert len(with_probes) == 13` (:322; S01 adds no `capture python:` probe, so it stays). `TestTheWp29TruthScript` and `_wp29_blocks` are :874-975.
- `test/test_wp29_truth.cscript` (4846 lines) is the frame: header, `cscript … adodir ".."`, the `c(python_exec)` gate printing `SKIP: Python not available.` and `exit 222`, `do "cert_helpers.do"`, `quietly do "cert_svg.do"`, `qui do "../dash_parse.mata"`, `qui do "../dash.ado"`, `_w29_expect`/`_w29_done`, a fresh work directory from `tempfile`, block S01 (W29-01), the marker, and a summary that exits 9 when no case ran.
- **Names are free:** `grep -rln 'WP30_ONLY\|test_wp30_truth\|WP30_OPEN\|_wp30_\|W30_' test scripts Makefile` → nothing; `grep -E -c '(^|[^A-Za-z0-9_])TF-[0-9]' test/*.cscript test/*.py test/*.do` → 0 in every file.

### The maps

- `test/function_test_map.py` (895 lines): `FUNCTIONS` ends on :800 with its closing brace on the entry's line (`'main': '…test_main_raises_on_serve_mode'}`); `SETUP_FUNCTIONS` is :869-895 (`"version_tuple": …` at :894, `}` at :895). `test_function_test_map.py` imports the dicts and reads no map text, so comments inside them are inert.
- `test/program_coverage_map.py` (610 lines): `COVERAGE["dash.ado"]` closes at :298 (`    },`, then `    "dash_setup.ado": {`), `COVERAGE["dash_setup.ado"]` at :338, `COVERAGE["dash_parse.mata"]` at :608 (then `}` at :609).

### The served copy lists (A149)

`ServerAppBuilder._glyph_layer_lines` (def `dash_render.py:32834`) copies constants and functions by name and skips a name the module lacks (:32884-32897, :33077-33093):

```python
        for _name in ("_TEXTBOX_SUBOPTS", "_TEXTBOX_SUBOPT_RE",
                      ...
            _val = getattr(_mod, _name, None)
            if _val is None:
                continue
        ...
        for _fn_name in ("_parse_textbox_opt", "_textbox_split_point",
                         ...
            _fn = getattr(_mod, _fn_name, None)
            if _fn is None:
                continue
```

Measured with `ast` over `inspect.getsource(dr.ServerAppBuilder._glyph_layer_lines)`: the only string-tuple loops are `_name` (145 names, 145 distinct, 0 undefined) and `_fn_name` (312, 312, 0). `_shared_stat_lines`' loops (`_fn` 41, `_sm` 5) iterate objects, not names, so a misspelling there fails at import and needs no test.

### Source ids matched by content (the manifest's three cases)

- **P1.23** cites REM-08-04-C7, C7b, C3b, C3c, C4, B2b, B7a, B4 and REM-08-05-M1, C7c, C10, M2. Only two have a literal anchor: WP-29's note at REMAINING.md:1979 names `REM-08-04-C3b, C3c; DROPIN P1.23` inside the 08-04 section (`grep -n 'REM-08-0[45]' REMAINING.md GAPS2.md GAPS.md TWOWAY_COVERAGE_AUDIT.md` finds nothing else). REMAINING.md:1935-2110 ("08-04 — Convert in the loader and give date figures a datetime axis") holds the date-position bullets (`_figure_date_kind`'s keys :1965-1979, the axis partition :1980-1990, reference lines :1991-1999, the axis-spec date branch :2000-2014, scatteri/pci :2015-2022); :2111-2290 ("08-05 — Format dates and numbers everywhere they are displayed") holds the text bullets (colorvar :2195-2208, fallback hover :2231-2241). Every REM-08-04 bullet concerns where a date is placed and every REM-08-05 bullet the text it is shown as, so no id moves: the eight REM-08-04 ids go to P1.23a (S35) and the four REM-08-05 ids to P1.23b (S17), as the manifest's scopes of S35 and S17 say. (REM-08-04-C6a and C6b are P1.5's, S18.)
- **P1.15** cites GAPS2-B16-a..e, but GAPS2.md's B16 (:516-528) has no lettered parts. Its Gap list and its Plan points 1-4 give the five letters, read in either order (DROPIN's "rows, holes, colfirst, title, note, legend(), i* axes and compact", or the Plan's): **a** rows()/holes()/colfirst (Plan 1) → P1.15b (S48); **b** title/subtitle/note/caption inside by() (Plan 2) → P1.15a (S28); **c** the i*/noi* axes and noedgelabel (Plan 3) and **d** legend() inside by() (Plan 4) → P1.15c (S53); **e** compact, iscale() and imargin() (the Closable line's approximations) → P1.15b (S48). Both readings give the same allocation, which is the manifest's (S28, S48 and S53 scopes).
- **P1.11** cites GAPS2-D3-a..e; GAPS2.md's D3 (:866) has no lettered parts. DROPIN's order gives a `{bf:}`, b `{it:}`, c `{sup:}`, d `{&beta}`/`{c #}`, e the `$$…$$` TeX pair: D3-e → P1.11a (S09, the TeX half, with J5), D3-a..d → P1.11b (S29, the SMCL half, with J2 and B13), as the manifest's S09 and S29 scopes say.
- **Every other split item** takes its ids from the manifest's "Closes" clause of each part's section, checked by script against DROPIN's source list (each DROPIN id lands in at least one entry; an id two parts share is listed in both with the part in parentheses, e.g. GAPS2-D2-a in P1.12a and P1.12b).

### GitNexus (CLI, at `c96facd`)

- `gitnexus impact test_no_open_entry_is_s1_or_s2 -d upstream -r dash` → `"risk": "UNKNOWN"`, `impactedCount: 0`, riskNote "No callers resolved". Confirmed by text search: `grep -rn 'test_no_open_entry_is_s1_or_s2\|WP29_OPEN\b' --include=*.py .` finds only `test/test_tracking_documents.py` (pytest collects it; nothing calls it).
- `gitnexus impact TestTheServedAppCarriesEveryName -d upstream -r dash` → `UNKNOWN`, 0 impacted (a test class; confirmed by grep: defined once, in `test/test_statistical_helpers.py:1296`).
- `gitnexus impact _glyph_layer_lines -d upstream -r dash` → `HIGH` (4 impacted, 1 direct). S01 only reads its source from a test and does not edit it; no warning applies to this section, and the HIGH is why A149's guard exists.
- The other edited symbols are test helpers new in this section (no callers) and Stata/Markdown text (not indexed).

### Prototype (scratch copy of `c96facd`, 03oct2026)

`git archive HEAD | tar -x` into a scratch directory; `s01_apply.py` (Appendix D) applied each step from this file's appendices, then the files were run. Not a git tree, so `test_a_closing_commit_exists` and the packaging root test skip there; in the worktree they run.

- **Red first** (steps `tests` only, documents unchanged): `11 failed, 429 passed, 1 skipped` over `test_tracking_documents.py`, `test_cscript_hygiene.py`, `test_cert_verdict.py` and `TestTheServedAppCarriesEveryName`. The failures: the six `TestWp30Tracking` tests (`NameError` on `_wp30_open_problems` ×2, `WP30_LISTS`, `_wp30_marker_problems`, `_wp30_closure_problems`, `_wp30_markers`), the three `TestTheWp30TruthScript` tests (`NameError` on `_WP30_TRUTH`, `_wp30_blocks`, `_W30_MARK`), `assert 67 == 68` and `assert 49 == 50`. The guard `test_every_listed_name_exists` passed.
- **Readers in** (step `readers`): `test_tracking_documents.py` `3 failed, 43 passed, 1 skipped`: `test_every_allowed_title_is_an_open_entry` (`P1.1a: 0 BUGS.md entries are titled 'A style list over several y variables, …'`), `test_an_open_p1_keeps_its_marker`, `test_each_p1_sits_in_its_changelog_lists`.
- **Entries in** (step `bugs`): `2 failed, 44 passed, 1 skipped`; BUGS.md 3186 lines, 60 open entries, the first new one at :2852.
- **Markers in** (step `changelog`): `test_tracking_documents.py` and `test_version_floor.py` `52 passed, 1 skipped`; CHANGELOG.md 999 lines, 83 markers, per list 34/5/7/23/4/10, `**WP-30 (drop-in P1, 03oct2026)**` at :315, `### Fixed in WP-30` at :801 (measured before P1.17a gained Changed behaviour; with its second marker and blank line the expected values are 1001 lines, 84 markers, 34/5/7/24/4/10, :315 and :803).
- **Everything in:** task 01-08's step-2 file set (eleven files) → `804 passed, 60 skipped`, 0 failed; `test_file_headers.py test_no_orphans.py test_measure_stata_coverage.py` also pass. Every step was applied from this file by `s01_apply.py` on a second fresh copy and gave the per-task results the tasks' verify lines quote (the counts there are for a git checkout, one more pass each); re-running a step stops with `step … already applied`. Collected: 47, 375 and 148. Sizes: `test_tracking_documents.py` 1952, `test_cscript_hygiene.py` 1117, `test_statistical_helpers.py` 1382, `test_wp30_truth.cscript` 593, `run_all_cscripts.do` 1823, `function_test_map.py` 955 (59 anchors), `program_coverage_map.py` 726 (116 anchors).
- **AC-01.2 by hand:** deleting the `"P1.5"` key made `test_no_open_entry_is_s1_or_s2` fail (`line 2900: S1 Default tick labels ignore the variable's display format, …`) and `test_a_closed_p1_has_no_marker_and_a_resolution` fail (`P1.5 is closed and CHANGELOG.md still holds its marker`); restoring it gave `46 passed, 1 skipped`.
- **The truth script in StataNow 19.5** (through `scripts/stata_slot.sh`, driver as in "Stata truth", the generated script byte-identical to the one step `truth` writes):
  - `WP30_ONLY` unset: `TF-01 PASS: a twoway SVG was written and read (10 texts); dash is loaded`, 57 `S<NN> start` and 57 `S<NN> end` lines (`S01 start  3 Oct 2026 16:55:27` … `S57 end  3 Oct 2026 16:55:27`), `test_wp30_truth: ALL CHECKS PASSED`, no `r(` error, `<scratch>/tmp` empty.
  - `WP30_ONLY=S02` (a stub): `S02 start`/`S02 end`, then `test_wp30_truth: no case ran (WP30_ONLY=S02)` and `r(9);`.
  - `WP30_ONLY=S99`: `no case ran (WP30_ONLY=S99)` and `r(9);`.

### Existing tests that pin today's behaviour

None asserts wrong behaviour, so nothing is flipped. Three assertions change, each with its reason:
- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script`: 67 → 68, the new script;
- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read`: 49 → 50, its `SKIP: Python not available.` gate;
- `test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2`: skips the titles of `WP29_OPEN` and `WP30_OPEN`.

## User stories

- **US-01.1** As the maintainer, I want every P1 item open in BUGS.md from WP-30's first fix onwards, graded, with its DROPIN text and source ids and the section that closes it, so that the tracking documents tell the truth about what is not yet fixed.
- **US-01.2** As the release manager, I want the release guard to keep refusing every open S1/S2 entry except WP-30's own, and those only while each is open in the WP-30 form, so that the allowance cannot hide a defect.
- **US-01.3** As the developer or agent of a fix section, I want one fixed edit to close my entry (the box, the Resolution line, my `WP30_OPEN` key, my markers), checked by a test, so that I cannot half-close it.
- **US-01.4** As the developer or agent of a fix section, I want my own gated, timed block in one truth script, runnable alone by `WP30_ONLY=S<NN>`, and my own anchors in the maps, so that I measure against Stata and register my functions without touching another section's lines.
- **US-01.5** As a dashboard publisher, I want a misspelt name in the served app's copy lists to fail the suite, not my served page.

## Business requirements

- **BR-01.1** BUGS.md holds one open entry per WP-30 entry (56), each with the five one-line fields, a title with no `"` that no other entry has, the DROPIN text with its source ids, a Suggested fix naming its section, and a Resolution that says it is open, why and which section closes it, graded once S1, S2 or S3 `(WP-30)`; none names a test.
- **BR-01.2** The full suite is green at S01's commit (given P-1), and the release guard's verdict on every entry outside the two allowances is unchanged.
- **BR-01.3** Each of these fails a test: an allowance key whose entry is missing, duplicated, closed, not in the WP-30 open form or naming another section; an open entry with no marker; a closed entry with a marker or without `(WP-30, <id>)` in a closed Resolution; a marker or closing line outside its lists; a marker naming no WP-30 id.
- **BR-01.4** CHANGELOG.md's current release carries 84 markers in six lists, as index.md "P1 coverage" assigns them; `### Fixed in WP-30` is new and sits directly above `### Fixed in WP-29`.
- **BR-01.5** The truth script runs under the certification runner, skips with r(222) only when Stata has no Python, runs one block alone under `WP30_ONLY`, fails when no case ran, times every block, and leaves no file behind; every one of S01-S57 owns at least one block, in section order.
- **BR-01.6** Each fix section has its own anchor in each map place A148 names, so parallel sections add keys in distinct hunks.
- **BR-01.7** Every name in the served app's two copy lists is defined in `dash_render.py`, once.
- **BR-01.8** The forms later sections follow are written down once, here (TR-01.10). No shipped file changes, and nothing outside this section's nine files is staged.

## Technical requirements

Both modes: S01 draws nothing and changes no page, so no saved/served pair, filter move, JS twin or copy-list entry applies. Its one served-app check is the A149 guard, which reads `_glyph_layer_lines`' source and edits nothing. It adds no function to `function_test_map.py` or program to `program_coverage_map.py`: only anchors.

- **TR-01.1 BUGS.md.** Append Appendix B at the end: one blank line after :2850, then the 56 entries in entry order, one blank line between entries; the file ends with one newline. File Names give anchors at `c96facd`. Each Description starts `DROPIN-REMAINING.md:<line> P1.<n>[, the <part> part], re-verified at c96facd:`, quotes the item text for its part and ends `Sources: <ids>`. Each Suggested fix is `WP-30 section NN (<section name without its parenthesis>): <one sentence>.` Each Resolution is `Not fixed because WP-30 section NN has not landed. Graded S<n> (WP-30): <why>.` Grades (S01's, by the WP-27 scale in `TestNoOpenEntryBlocksARelease`'s docstring): S1 where a number, position or text is wrong with no note, or an option the user gave is dropped without one (P1.5, P1.16, P1.17a, P1.17b, P1.18b, P1.20a, P1.20b, P1.23a, P1.23b); S3 for default-look fidelity, the points-free fallback, the missing vector export and the runners (P1.2a, P1.2b, P1.3a, P1.3b, P1.4a, P1.4b, P1.22, P1.28b, P1.34); S2 for the other 38 (a twoway form refused, named and not drawn, or failing visibly).
- **TR-01.2 Constants and readers** (`test/test_tracking_documents.py`, block `tracking-readers`, above `class TestWp30Tracking`): a banner; `WP30_OPEN` (56 keys, entry id to the Appendix B title, one per line, in entry order); `WP30_LISTS` (id to its lists, Appendix A; permanent); `WP30_SECTION` (id to its closing section; permanent); `WP30_ALL = tuple(WP30_LISTS)`; `_WP30_MARKER = <!-- WP-30 (P1\.\d{1,2}[abc]?) -->`; `_WP30_OPEN_FORM`, A144's form with the section captured; `_wp30_markers`, `_wp30_open_problems` (also checks the Resolution's section against `WP30_SECTION`), `_wp30_marker_problems`, `_wp30_closure_problems`, `_wp30_list_problems`. `_changelog_lists`/`_changelog_list` are WP-29's, reused. The constants are built by `s01_apply.py readers` from Appendices A and B, never retyped.
- **TR-01.3 The release guard.** In `test_no_open_entry_is_s1_or_s2` the allowance becomes `set(WP29_OPEN.values()) | set(WP30_OPEN.values())`, with its comment; nothing else in `TestNoOpenEntryBlocksARelease` changes. The module docstring gains item 9 (block `docstring-item-9`).
- **TR-01.4 `TestWp30Tracking`** (block `tracking-class`, appended at the end of the file): `test_every_allowed_title_is_an_open_entry`, `test_an_open_p1_keeps_its_marker`, `test_a_closed_p1_has_no_marker_and_a_resolution`, `test_each_p1_sits_in_its_changelog_lists` (also `WP30_SECTION` covers `WP30_ALL` and names 02-57 once each), `test_the_marker_reader`, `test_the_wp30_problem_readers` (both directions of every helper, including that `(WP-30, P1.1a)` is not read inside `(WP-30, P1.11a)` or `(WP-30, P1.1b)`).
- **TR-01.5 CHANGELOG.md** (the manifest's five lists plus `### New`, A147; step `changelog`, bottom-up so the anchors hold): above :653 the block `fixed-in-wp30` and 10 markers; after :651 4; after :596 24; after :450 7; after :409 5; after :313 the group line `**WP-30 (drop-in P1, 03oct2026)**` and 34. Markers are `<!-- WP-30 <id> -->`, in entry order within each list, one blank line between consecutive ones. No WP-30 line is written; lines are the closing commits'.
- **TR-01.6 The truth script** `test/test_wp30_truth.cscript` (step `truth`): block `truth-head` (header; `cscript "WP-30 truth: twoway comparisons" adodir ".."`; the `c(python_exec)` gate; `cert_helpers.do`, `cert_svg.do`, `dash_parse.mata`, `dash.ado`; `global dash_nobrowser 1`; `_w30_expect`/`_w30_done` declaring `version 19`; a fresh work directory from `tempfile w30_base` or exit 9; block S01 with case TF-01), then one stub per section S02-S57 in section order, each

  ```stata
  * ==== S<NN> P1.<n>[abc]: <section name without its trailing parenthesis> ====
  local only : env WP30_ONLY
  if inlist("`only'", "", "S<NN>") {
      display as text "S<NN> start " c(current_date) " " c(current_time)
      display as text "S<NN> end " c(current_date) " " c(current_time)
  }
  * ==== end S<NN> ====
  ```

  with a blank line before each, then block `truth-tail` (the marker `* ==== append new blocks above this line ====` and the summary that exits 9 when `$w30_ncase == 0` or a case failed). No `capture python:` probe.
- **TR-01.7 Runner and hygiene.** Runner block `// 69.` (block `runner-69`, block 68's form) after :1769 and one blank line. The pins 67 → 68 (:294) and 49 → 50 (:313) with their comments. Block `hygiene-reader` (`_WP30_TRUTH`, `_W30_OPEN`, `_W30_CLOSE`, `_W30_MARK`, `_W30_HEAD`, `_wp30_blocks`) and block `hygiene-class` (`TestTheWp30TruthScript`: `test_the_scaffold_is_in_order`, `test_every_block_is_gated_timed_closed_and_in_section_order`, `test_the_block_reader`). `_wp30_blocks` reports a marker not there once, a block not closed by its own end line, a header with no entry id (`P1.<n>[abc]: ` or S01's `scaffold: `), a block not gated by its own section, a block whose first statement after the gate is not its start line or whose last before `}` is not its end line (comment lines ignored), a block below the marker, a block out of section order (non-decreasing, so a section may own two), and a section whose blocks name two entries.
- **TR-01.8 Map anchors** (step `anchors`, A148): `# WP-30 S<NN> (<id>): <manifest section name>`, in section order: after `FUNCTIONS`' last entry (its closing brace moved to its own line; indent 1) all 56; before `SETUP_FUNCTIONS`' `}` (indent 4) S05, S25, S41; before the `    },` closing `COVERAGE["dash.ado"]` (:298) and `COVERAGE["dash_parse.mata"]` (:608) all 56 (indent 8); before the one closing `COVERAGE["dash_setup.ado"]` (:338) S03, S05, S25, S41 (indent 8).
- **TR-01.9 The copy-list guard** (block `served-names`, appended inside `TestTheServedAppCarriesEveryName`): `test_every_listed_name_exists` walks `_glyph_layer_lines`' source with `ast`, collects every `for <name> in (<string constants>)` loop, requires exactly the loops `_name` and `_fn_name` with at least 140 and 300 names, every name defined in `dash_render`, and none listed twice.
- **TR-01.10 The forms every fix section follows** (binding; index.md "Deltas", A141, A156, R1-R5):
  1. **Closing an entry, in place, in the closing commit.** `- [ ] Title:` becomes `- [x] Title:` (title kept); the whole Resolution line becomes `  - Resolution: Fixed <ddmonyyyy> (WP-30, <id>). <what changed, where, both modes>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-30): <what and why>.]`; one id per parenthesis; only tests that exist in that commit are named; the entry's own `WP30_OPEN` key line is deleted in the same commit. Its File Names, Description and Suggested fix are left as written. **The key-deletion check** is `grep -c '^    "<id>": "' test/test_tracking_documents.py` → 0 (1 while open; only `WP30_OPEN`'s rows are `"<id>": "<title>",` at indent 4). A bare `grep -c '"<id>"'` is not that check: `WP30_LISTS` and `WP30_SECTION` keep a `"<id>":` row for good (A144), and `TestWp30Tracking`'s unit tests quote P1.1a, P1.1b, P1.2a, P1.19 and P1.29, so it prints at least 2 after a correct close.
  2. **Replacing markers.** Each of the entry's `<!-- WP-30 <id> -->` lines is replaced in place by one or more `- …` items ending `(WP-30, <id>)`, one id per item; a Results line names the command, the old value (from the saved failure text) and the new; nothing is added elsewhere. A section that needs another list edits its own `WP30_LISTS` row and its own marker in the same commit (R4).
  3. **Two-commit sections** (S05, S19, S37, S41, S42, S51, S56; A156): the first commit leaves the entry, its key and every marker in place; the second closes all three and its lines cover both halves; both subjects end `(WP-30 P1.<n>[abc])` and say which half each is (A141).
  4. **Filling a stub.** Cases go between the section's own start and end lines, which stay the first and last statements of its block (`TestTheWp30TruthScript` checks it), and print `<CASE-ID> PASS: …` through `_w30_expect`/`_w30_done`; case ids use the section's prefix (index.md manifest table); files are written only under `` `w30_work' `` (a case whose code under test reads only the working directory may write a uniquely named file there, checked absent with `capture confirm new file` first and erased in the same case; S07 SX-05/SX-08) and erased before the end line; helper programs go directly above the section's own header (they declare `version 19`); a second block goes directly below the section's own end line, with the same `S<NN>` and entry id; no section writes in another's block, moves the marker or edits the header, the S01 block or the summary. A block run alone (`WP30_ONLY=S<NN>`) must print its PASS lines and `ALL CHECKS PASSED`.
  5. **Map keys** go under the section's own anchor, alphabetical by key; Mata functions also get their `_needed` entry (X.5/A137). No section edits another's anchor or entries.
  6. **Copy lists** are append-only at the R2 anchors; `test_every_listed_name_exists` (G4) must stay green.
  7. **The commit message.** Subject ends `(WP-30 P1.<n>[abc])` (A141). The body opens with the saved failure text, then the measured defect, then what changed and where, then one line each: `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>`, `Fixture: test/fixtures/<name>.json (scripts/<extract>)`, `BUGS.md: "<title>" (closed)` (in the closing commit only; a two-commit section's first commit has none). No tool or vendor is named and no co-author trailer is added (CLAUDE.md rule 6; G7).
- **TR-01.11 Security (rule 1).** The readers are anchored regular expressions over repository text; the A149 guard parses source with `ast` and runs none of it; nothing runs a subprocess, `eval` or `shell=True`. `s01_apply.py` reads only the section file and the files it edits, asserts every anchor before writing, refuses to run a step twice, and uses no shell or network. The truth script interpolates no file content into a macro, echoes no user text, and writes only under a work directory it has just created. The allowance is closed-world (only `WP30_OPEN`'s titles, only in the open form naming their own section) and S58.1 empties it. The markers are HTML comments in a document that is not shipped.

## Boundaries

- **No shipped file:** `dash.ado`, `dash_parse.mata`, `dash_render.py`, `dash_setup.ado`, `dash_setup_lib.py`, `dash.sthlp`, `dash_setup.sthlp`, `dash.pkg`, `stata.toc` and the scheme files are not edited.
- **Not staged:** `CLAUDE.md`, `.gitignore`, `AGENTS.md` (the maintainer's, E7), `.ultraplan/` (step 0a's; G6), `.gitnexus/`, `PhilSchummSuggestion.md`, any scratch file or `*.html`.
- **Not edited:** ROADMAP.md, GAPS.md, GAPS2.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md, AGENTS.md, `test/fixtures/rejected_options.json` (S58's, A145); `test/test_packaging.py` and its `_ROOT_ALSO` (P-1 is the maintainer's); WP-29's constants, readers, `TestWp29Tracking`, `_wp29_blocks`, `TestTheWp29TruthScript` and `test/test_wp29_truth.cscript` (mirrored, not edited); the import-probe pin (:322; S05, S25 and S41 own it); `test/test_mode_parity.py`, `test/test_unsupported_report_is_true.py` and every other pin of R10.
- **Not done:** no existing BUGS.md entry is closed, reworded or regraded; no test is renamed or deleted; no CHANGELOG line other than the group line and the `### Fixed in WP-30` heading and introduction is written; no `make cert`, `make gate`, `run_all_cscripts.do` or second full run (rule 11, index.md "Full-suite runs" rule 3); Stata runs only through `scripts/stata_slot.sh`.
- **Later sections own** every entry's closure, every marker's replacement, every stub's cases and every map key; batch 1 (S02, S03) is cut only after this section lands.

## Stata truth

- **What this section adds:** no fixture and no extractor (so no `_meta` stamp). It adds the truth script and its smoke case **TF-01**: `twoway scatter mpg weight` on `sysuse auto`, exported by `cert_svg_export` to `` `w30_work'/w30s01.svg `` and read by `cert_svg_texts`; it passes when `r(rc) == 0`, the file exists, `r(n) > 0` (measured 10) and `_dash_serve` is defined; it erases `r(file)` and `r(list)` and drops the graph. The 56 stubs print only their start and end lines.
- **The driver** (index.md "The cscript driver", with the do-file lines this package's Stata rule asks for). `<W>` is the worktree root:

  ```sh
  W=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s01; X=<scratch>/s01
  mkdir -p "$X/s99"
  printf 'adopath ++ "%s/"\nglobal dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/test_wp30_truth.cscript"\n' "$W" "$W" "$W" > "$X/run_test_wp30_truth.do"
  cp "$X/run_test_wp30_truth.do" "$X/s99/"
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$X" "$X/run_test_wp30_truth.do"                  # log: $X/run_test_wp30_truth.log
  WP30_ONLY=S99 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$X/s99" "$X/s99/run_test_wp30_truth.do"
  ```

- **Measured:** the whole script ran in about one second (`S01 start` to `S57 end` at 16:55:27); S58.7 times blocks from the `S<NN> start/end` lines, which carry the date and the time.

## TDD test stubs

**Regression tests**, written first by 01-01; each fails at the base for the reason measured on the prototype:
- Test: `test/test_tracking_documents.py::TestWp30Tracking::test_every_allowed_title_is_an_open_entry` — `_wp30_open_problems(WP30_OPEN, entries) == []`. Fails with `NameError: name '_wp30_open_problems' is not defined`; with the readers but no entries, `P1.1a: 0 BUGS.md entries are titled …`.
- Test: `…::TestWp30Tracking::test_an_open_p1_keeps_its_marker` — every open id has a marker and every marker names a WP-30 id. `NameError` (`_wp30_marker_problems`), then `P1.1a is open and CHANGELOG.md holds no marker for it`.
- Test: `…::TestWp30Tracking::test_a_closed_p1_has_no_marker_and_a_resolution` — `NameError` (`_wp30_closure_problems`); vacuous while all 56 are open.
- Test: `…::TestWp30Tracking::test_each_p1_sits_in_its_changelog_lists` — `NameError` (`WP30_LISTS`), then `CHANGELOG.md has no single '### Fixed in WP-30' list`.
- Test: `…::TestWp30Tracking::test_the_marker_reader` — `NameError` (`_wp30_markers`).
- Test: `…::TestWp30Tracking::test_the_wp30_problem_readers` — `NameError` (`_wp30_open_problems`).
- Test: `test/test_cscript_hygiene.py::TestTheWp30TruthScript::test_the_scaffold_is_in_order` — `NameError: name '_WP30_TRUTH' is not defined`.
- Test: `…::TestTheWp30TruthScript::test_every_block_is_gated_timed_closed_and_in_section_order` — `NameError` (`_wp30_blocks`).
- Test: `…::TestTheWp30TruthScript::test_the_block_reader` — `NameError` (`_W30_MARK`).
- Test: `…::TestTheChecksReachEveryScript::test_the_glob_finds_every_script` — `assert 67 == 68`.
- Test: `…::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read` — `assert 49 == 50`.

**Guard test** (green at the base, listed apart): `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName::test_every_listed_name_exists`.

**Guards already green that S01 keeps green:** every other test of `test_tracking_documents.py` (notably `TestNoOpenEntryBlocksARelease`, `TestEveryOpenEntrySaysWhyItIsOpen`, `TestEveryBugsEntryIsWellFormed`, `TestEveryClosedEntryNamesATestThatExists`, `TestWp29Tracking`), `test_cert_verdict.py`, `test_version_floor.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_fixtures_are_committed.py`, `test_test_integrity.py`, `test_svg_truth.py`. Pinned tests to flip: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| 56 open entries in the WP-30 form, each naming its section; allowance exact | pytest `TestWp30Tracking::test_every_allowed_title_is_an_open_entry` | BUGS.md | n/a (no page) |
| Release guard exempts only the two allowances | pytest `TestNoOpenEntryBlocksARelease` (3) and the AC-01.2 hand check | BUGS.md | n/a |
| Markers present while open, gone when closed, in their lists only | pytest `test_an_open_p1_keeps_its_marker`, `test_a_closed_p1_has_no_marker_and_a_resolution`, `test_each_p1_sits_in_its_changelog_lists` | CHANGELOG.md | n/a |
| Readers, both directions | pytest `test_the_marker_reader`, `test_the_wp30_problem_readers` | inline | n/a |
| The Requirements range still holds the floor | pytest `test/test_version_floor.py` | CHANGELOG.md | n/a |
| Truth-script layout: gated, timed, closed, ordered, every section present | pytest `TestTheWp30TruthScript` (3) | the script, inline | n/a |
| The script obeys every per-script rule and is registered | pytest `test_cscript_hygiene.py`, `test_cert_verdict.py` | the script, the runner | n/a |
| Scaffold runs in Stata; gating; "no case ran" | the driver: TF-01 PASS and 57 timed blocks with `WP30_ONLY` unset; r(9) with `WP30_ONLY=S99` | auto | n/a (Stata) |
| Map anchors inert; maps complete | pytest `test_function_test_map.py`, `test_program_coverage_map.py` | the maps | n/a |
| Copy-list names exist, once | pytest `test_every_listed_name_exists` | `dash_render.py` | served (the guard) |
| Nothing else broke | one full run through the queue (01-08) | — | — |

**Acceptance criteria.**
- **AC-01.1 BUGS.md.** `grep -c '^- \[ \] Title:' BUGS.md` → 60; `wc -l < BUGS.md` → 3186; `grep -n '^- \[ \] Title: A style list' BUGS.md` → `2852:…`; `grep -c 'Not fixed because WP-30 section' BUGS.md` → 56.
- **AC-01.2 The allowance.** `test_no_open_entry_is_s1_or_s2` passes; deleting one S1 or S2 key (e.g. `"P1.5"`) makes it and `test_a_closed_p1_has_no_marker_and_a_resolution` fail; closing an entry without deleting its key makes `test_every_allowed_title_is_an_open_entry` fail (`is closed; delete its WP30_OPEN key`; unit-tested).
- **AC-01.3 CHANGELOG.md.** `grep -c '<!-- WP-30 ' CHANGELOG.md` → 84; per list (awk ranges in task 01-04) 34, 5, 7, 24, 4, 10; `grep -c '^### Fixed in WP-30$'` → 1; `grep -c '^\*\*WP-30 (drop-in P1, 03oct2026)\*\*$'` → 1; `wc -l` → 1001.
- **AC-01.4 Truth script.** 593 lines; registered once as block 69 (`grep -c 'do "test_wp30_truth.cscript"' test/run_all_cscripts.do` → 1, runner 1823 lines); the driver run prints `TF-01 PASS`, 57 `S<NN> start` and 57 `S<NN> end` lines and `test_wp30_truth: ALL CHECKS PASSED`, no `r(` error, nothing in `<scratch>/s01/tmp`; `WP30_ONLY=S99` ends `r(9)` with `no case ran`.
- **AC-01.5 Counts.** `test_tracking_documents.py` collects 47, `test_cscript_hygiene.py` 375, `test_statistical_helpers.py` 148; `grep -c '# WP-30 S' test/function_test_map.py test/program_coverage_map.py` → 59 and 116.
- **AC-01.6 The commit.** One green full run through the queue in the worktree; one commit on `wp30-s01` whose subject ends `(WP-30 S01)`, holding exactly the nine files of Tasks; `grep -Eic 'claude|anthropic'` → 0 on the message before and after.

## Tasks

Commit boundary: **one commit, `(WP-30 S01)`**, holding 01-01 to 01-07, made by 01-08 on `wp30-s01` in the worktree `<W>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s01`, cut by the orchestrator (index.md step 0.1) from `<base>` = the sha in `<scratch>/batch-0-base.txt`. `<scratch>` is the orchestrator's WP-30 scratch directory; S01 works in `<scratch>/s01/` (`mkdir -p`). `<SF>` is this file at its main-checkout path, `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/wp30/section-01-tracking-foundation.md`. Every command starts with `cd <W> &&` (the shell's cwd resets). `A=<scratch>/s01/s01_apply.py`. No commit before 01-08; no Stata except 01-06's driver runs.

<task type="auto" id="01-01">
  <name>Write the failing tracking and hygiene tests</name>
  <files>test/test_tracking_documents.py, test/test_cscript_hygiene.py, test/test_statistical_helpers.py</files>
  <action><![CDATA[
Check `git -C <W> rev-parse HEAD` equals `<base>` and `git -C <W> branch --show-current` prints `wp30-s01`. Write Appendix D's block `s01-apply` to `<scratch>/s01/s01_apply.py`, byte for byte, never retyped: `python3 -c "import re,sys; t=open(sys.argv[1]).read(); m=re.search(r'^~~~~python s01-apply\n(.*?)\n~~~~$', t, re.M|re.S); open(sys.argv[2],'w').write(m.group(1)+'\n')" <SF> <scratch>/s01/s01_apply.py`. Run `cd <W> && python3 $A <SF> tests`: it appends block `tracking-class` to `test/test_tracking_documents.py`, moves the two pins of `test/test_cscript_hygiene.py` (:294, :313) with their comments and appends block `hygiene-class` there, and appends block `served-names` inside `TestTheServedAppCarriesEveryName`. Then run `cd <W> && python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -n0 -p no:cacheprovider 2>&1 | grep -E '^(FAILED|E   )|passed|failed' > <scratch>/s01/01-S01-failure.txt` and put the line `S01 tests at <base>:` first in that file. Commit nothing.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/s01/01-S01-failure.txt` reads `11 failed, 430 passed` (the prototype, outside git, gave `11 failed, 429 passed, 1 skipped`). The FAILED lines are exactly the 11 regression nodes of "TDD test stubs"; `grep -c NameError` on the file is at least 9 and it holds `assert 67 == 68` and `assert 49 == 50`; `test_every_listed_name_exists` is not among them. `git -C <W> status --porcelain` shows only ` M` for the three files.]]></verify>
  <done>The eleven new or moved tests existed and failed for their recorded reasons, the guard passed, the failure text was saved, and nothing was committed.</done>
</task>

<task type="auto" id="01-02">
  <name>Add the WP-30 constants, readers and allowance</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> readers`. It builds `WP30_OPEN` (titles from Appendix B), `WP30_LISTS` and `WP30_SECTION` (Appendix A), puts them into block `tracking-readers` in place of its three `@@…@@` lines, inserts the block directly above `class TestWp30Tracking` with two blank lines on each side, replaces the release guard's comment and allowance in `test_no_open_entry_is_s1_or_s2` (:514-516) with the union of `WP29_OPEN` and `WP30_OPEN`, and inserts block `docstring-item-9` after the docstring line `   keeps every P0 entry closed with no marker left.` (:45). Then run the file.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `3 failed, 44 passed`; the three are `test_every_allowed_title_is_an_open_entry` (first E line `P1.1a: 0 BUGS.md entries are titled 'A style list over several y variables, ...`), `test_an_open_p1_keeps_its_marker` and `test_each_p1_sits_in_its_changelog_lists`; all three `TestNoOpenEntryBlocksARelease` tests pass. `grep -c '^    "P1\.' test/test_tracking_documents.py` prints 168 (56 keys in each of the three maps).]]></verify>
  <done>The allowance, the two permanent maps and the readers existed, the release guard skipped exactly the two allowances' titles, the reader unit tests passed, and only the three document checks still failed.</done>
</task>

<task type="auto" id="01-03">
  <name>Open the 56 entries in BUGS.md</name>
  <files>BUGS.md</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> bugs`: it asserts BUGS.md ends `.\n` with no blank last line and appends one blank line, Appendix B's 56 entries exactly as written (one blank line between entries) and a final newline. Do not retype an entry; if Appendix B must change, change it in the plan through the orchestrator (G6), never in the worktree only.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '^- \[ \] Title:' BUGS.md` prints 60; `wc -l < BUGS.md` prints 3186; `tail -c 2 BUGS.md | xxd -p` prints `2e0a`; `grep -n '^- \[ \] Title: A style list' BUGS.md | cut -d: -f1` prints 2852. `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `2 failed, 45 passed` (`test_an_open_p1_keeps_its_marker`, `test_each_p1_sits_in_its_changelog_lists`); `TestEveryBugsEntryIsWellFormed`, `TestEveryClosedEntryNamesATestThatExists`, `TestEveryOpenEntrySaysWhyItIsOpen` and `TestNoOpenEntryBlocksARelease` pass.]]></verify>
  <done>BUGS.md held the 56 WP-30 entries, open, graded, well formed, each naming its section, and exempt from the release guard only through the allowance.</done>
</task>

<task type="auto" id="01-04">
  <name>Place the 84 CHANGELOG markers</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> changelog`. It asserts the anchors (313 ends `(WP-29, P0.20)`, 315 `### Security`, 409 `(WP-29, P0.14)`, 411 `### New`, 450 `(WP-23).`, 452 `### Fixed`, 596 `(WP-29, P0.12a)`, 598 `### Removed`, 607 `### Requirements`, 651 `(WP-29, P0.19)`, 653 `### Fixed in WP-29`; 314, 410, 451, 597, 652 blank) and inserts bottom-up: above 653 block `fixed-in-wp30` and the Fixed in WP-30 markers; after 651, 596, 450 and 409 a blank line and the markers of Requirements, Changed behaviour, New and Security; after 313 a blank line, `**WP-30 (drop-in P1, 03oct2026)**`, a blank line and the Results that change markers. Each list's markers are in entry order with one blank line between them. If an assertion fails, stop and report: the base is not `c96facd`'s CHANGELOG.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '<!-- WP-30 ' CHANGELOG.md` prints 84 and `wc -l < CHANGELOG.md` prints 1001. Piping each range into `grep -c '<!-- WP-30 '`: `awk '/^### Results that change/,/^### Security/'` 34; `awk '/^### Security/,/^### New/'` 5; `awk '/^### New/,/^### Fixed$/'` 7; `awk '/^### Changed behaviour/,/^### Removed/'` 24; `awk '/^### Requirements/,/^### Fixed in WP-30/'` 4; `awk '/^### Fixed in WP-30/,/^### Fixed in WP-29/'` 10. `grep -c '^### Fixed in WP-30$' CHANGELOG.md` and `grep -c '^\*\*WP-30 (drop-in P1, 03oct2026)\*\*$' CHANGELOG.md` print 1. `python3 -m pytest test/test_tracking_documents.py test/test_version_floor.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `53 passed`.]]></verify>
  <done>CHANGELOG.md held 84 markers in the six lists of the current release, and every tracking and floor test passed.</done>
</task>

<task type="auto" id="01-05">
  <name>Create the truth script and its reader</name>
  <files>test/test_wp30_truth.cscript, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> truth`. It creates `test/test_wp30_truth.cscript` from block `truth-head`, the 56 stubs (TR-01.6; S02-S57 in section order, header text from Appendix A's last column without its trailing parenthesis) and block `truth-tail`, and inserts block `hygiene-reader` directly above `class TestTheWp30TruthScript`. Then run the hygiene and verdict files. Do not register the script yet.
  ]]></action>
  <verify><![CDATA[`cd <W> && wc -l < test/test_wp30_truth.cscript` prints 593; `grep -c '^\* ==== S[0-9][0-9] ' test/test_wp30_truth.cscript` prints 57; `grep -c 'capture python' test/test_wp30_truth.cscript` prints 0. `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `1 failed, 374 passed`, the failure being `TestEveryCscriptIsWiredIntoTheRunner::test_the_runner_calls_it[test_wp30_truth.cscript]`; `python3 -m pytest test/test_cert_verdict.py -q -n0 -p no:cacheprovider` fails only `test_the_real_runner_registers_every_script_in_test`.]]></verify>
  <done>The truth script existed in WP-29's frame with S01's block and 56 gated, timed stubs above its marker, and every hygiene rule held except its registration.</done>
</task>

<task type="auto" id="01-06">
  <name>Register block 69 and run the script</name>
  <files>test/run_all_cscripts.do</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> runner`: it asserts :1769 is block 68's closing `}` (with `[ FAIL] test_wp29_truth.cscript` at :1767, a blank :1770 and `// Summary` at :1772) and inserts a blank line and block `runner-69` after :1769. Run the hygiene and verdict files. Then run the script in StataNow through the two driver runs of "Stata truth" (`WP30_ONLY` unset into `<scratch>/s01`, `WP30_ONLY=S99` into `<scratch>/s01/s99`), only through `scripts/stata_slot.sh`. If the first run SKIPs (r(222)), `python_exec` was dropped from `~/.stata19/console/stata19.rc`: a skip is not a pass; restore the link and rerun.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_cscript_hygiene.py test/test_cert_verdict.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `397 passed`; `grep -c 'do "test_wp30_truth.cscript"' test/run_all_cscripts.do` prints 1 and `wc -l < test/run_all_cscripts.do` 1823. In `<scratch>/s01/run_test_wp30_truth.log`: `grep -c '^TF-01 PASS'` 1, `grep -c '^S[0-9][0-9] start '` 57, `grep -c '^S[0-9][0-9] end '` 57, `grep -c '^  test_wp30_truth: ALL CHECKS PASSED'` 1, `grep -c '^r([0-9]*);'` 0; `ls -A <scratch>/s01/tmp` prints nothing. In `<scratch>/s01/s99/run_test_wp30_truth.log`: `grep -c 'no case ran (WP30_ONLY=S99)'` at least 1, `grep -c '^r(9);'` at least 1, `grep -c '^TF-01 PASS'` 0.]]></verify>
  <done>The runner ran the script as block 69; TF-01 passed in StataNow, all 57 blocks printed their start and end lines, a gate naming no block failed with r(9), and no file was left behind.</done>
</task>

<task type="auto" id="01-07">
  <name>Place the map anchors</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
Run `cd <W> && python3 $A <SF> anchors`. It asserts the anchors (`FUNCTIONS`' `'main'` line ending `'}` at :800; `SETUP_FUNCTIONS`' `}` at :895 after `"version_tuple"`; the `    },` lines at :298, :338 and :608 of `program_coverage_map.py`, each followed by the next key or `}`), then places the TR-01.8 anchors in section order, bottom-up within each file. Run both map tests.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -c '# WP-30 S' test/function_test_map.py` prints 59 and `grep -c '# WP-30 S' test/program_coverage_map.py` prints 116; `wc -l` gives 955 and 726. `grep -n '^ # WP-30 S02 ' test/function_test_map.py` prints `801: # WP-30 S02 (P1.34): Portable runners (P1.34 under M4)`. `python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports `31 passed`.]]></verify>
  <done>Each fix section had its own anchor in each map place A148 names, and both map tests passed unchanged.</done>
</task>

<task type="auto" id="01-08">
  <name>Run the gates and commit S01</name>
  <files>none</files>
  <action><![CDATA[
1. `cd <W> && git merge --no-edit main` must print `Already up to date.` (E9); otherwise stop and report.
2. Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_cert_verdict.py test/test_version_floor.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_statistical_helpers.py test/test_packaging.py test/test_test_integrity.py test/test_fixtures_are_committed.py test/test_svg_truth.py -q -n0 -p no:cacheprovider`. If the only failure is `test_the_package_root_holds_only_what_ships_and_the_repositorys_own` (P-1 unresolved), stop and report to the orchestrator without committing.
3. One full run through the queue, launched in the background and waited for: `<scratch>/full_suite_queue.sh <W> <scratch>/s01/01-full-1.log`; read the log's `exit=` line, never relaunch to check (E1); a known flaky test gets one isolated re-run (E6).
4. Stage the nine paths by name, never `-A`: `git add BUGS.md CHANGELOG.md test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_statistical_helpers.py test/run_all_cscripts.do test/function_test_map.py test/program_coverage_map.py test/test_wp30_truth.cscript`; `git diff --cached --name-only` lists exactly those nine (G6).
5. Write `<scratch>/s01/01-commit-msg.txt` from the template in Notes, opening with `<scratch>/s01/01-S01-failure.txt`; `grep -Eic 'claude|anthropic'` on it prints 0 (G7).
6. `git -C <W> branch --show-current` prints `wp30-s01`; `git commit -F <scratch>/s01/01-commit-msg.txt`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; record the sha in `<scratch>/s01/01-sha.txt` for the merger, who lands it on `wp30-p1` (index.md landing routine) before batch 1 is cut.
  ]]></action>
  <verify><![CDATA[Step 2 reports 0 failed. The log ends `exit=0` with 0 failed and 0 errors. `cd <W> && git log -1 --format=%s` ends `(WP-30 S01)`; `git show --name-only --format= HEAD | sort` lists exactly BUGS.md, CHANGELOG.md, test/function_test_map.py, test/program_coverage_map.py, test/run_all_cscripts.do, test/test_cscript_hygiene.py, test/test_statistical_helpers.py, test/test_tracking_documents.py, test/test_wp30_truth.cscript; `git log -1 --format=%b | head -1` prints `S01 tests at <base>:`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git status --porcelain -- BUGS.md CHANGELOG.md test` is empty.]]></verify>
  <done>One green commit on wp30-s01 held the entries, the allowance and its tests, the markers, the truth script with its runner block and guard, the map anchors and the copy-list guard, with a message free of tool names, ready to land first.</done>
</task>

## Section completion criteria

- One commit on `wp30-s01`, subject ending `(WP-30 S01)`, made after one green full run through the queue; exactly the nine files; no test-only commit; G7 prints 0.
- BUGS.md holds the 56 WP-30 entries open in the WP-30 form; `WP30_OPEN` holds their titles; `WP30_LISTS`, `WP30_SECTION` and `WP30_ALL` are permanent; `TestWp30Tracking` (6) and the release-guard union are in place; `test_tracking_documents.py` collects 47 and passes.
- CHANGELOG.md holds 84 markers (34 + 5 + 7 + 24 + 4 + 10), the WP-30 group line and `### Fixed in WP-30`.
- `test/test_wp30_truth.cscript` is registered as block 69, passes TF-01 in StataNow and times all 57 blocks; `TestTheWp30TruthScript` (3) passes; the pins read 68 and 50; `test_cscript_hygiene.py` collects 375 and passes.
- The maps hold 59 and 116 anchors; `test_every_listed_name_exists` passes.
- The forms of TR-01.10 are recorded for S02-S57; the merger landed the commit before batch 1 was cut.

## Notes

- **Merging (R1, R4, R5, R2).** Every later section changes, in place, only: its entry's box and Resolution line (BUGS.md); its own marker lines (CHANGELOG.md); its own `WP30_OPEN` line; the lines inside its own stub (or directly above its header or below its end line); the lines under its own anchors. Entries, markers and stubs are separated by blank lines, so a hunk whose neighbour was already rewritten still applies three-way; adjacent `WP30_OPEN` deletions conflict in context only and the merger applies both by hand. Never resolve a conflict by dropping a line.
- **Block order under merges.** Stubs are in section order from the start, so blocks land in place. A conflict in a stub region is resolved by keeping each section's lines inside its own block; `TestTheWp30TruthScript` fails at G8 if a block moved or lost its gate or timing lines.
- **A block run alone.** `WP30_ONLY=S<NN>` on a stub ends `no case ran` and r(9), by design: a section runs its block alone only after it has written a case.
- **`_CASE_ID` and source ids.** Source ids (`REM-§2-S09-text`, `GAPS2-D8-a`, `AUDIT-64`) are inert in BUGS.md; a `test_*` file name, `file::node` or `Test…` word that does not exist is not (`test_no_entry_names_a_test_that_does_not_exist`), so an open entry names none; a closing Resolution names only tests that exist.
- **Grades.** S01's grades are informational for the release (all 56 close in WP-30). A section that finds its entry misgraded corrects the grade only in its closing Resolution's text, never in an open entry.
- **Python linkage.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, after which the script SKIPs (r(222)); `scripts/stata_slot.sh` caps sessions at three.
- **Maintainer question (P-1).** `PhilSchummSuggestion.md` is tracked in the package root (76e32d7), and `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` is red at `c96facd`, so G0 (step 0a) and every section's full run fail until the maintainer moves the file or adds it to `_ROOT_ALSO`. S01 does neither. **Recommendation:** the maintainer moves it with `git mv PhilSchummSuggestion.md .ultraplan/handoff/` in a commit of their own on `wp30-p1` before step 0a (a design note, not a shipped or configuration file, and `.ultraplan` is skipped by the directory walks), rather than widening `_ROOT_ALSO`, which would let a stray note ship next to the package. **Answered 06oct2026 (ratification row 29):** "Ignore the file in the packaging root test": `PhilSchummSuggestion.md` is named in `_ROOT_ALSO` (a one-line change by the maintainer, uncommitted at plan time), committed on `wp30-p1` after one green full run and before step 0a (index step 0a.4). S01 still edits neither the file nor `_ROOT_ALSO`.
- **Commit message template** (01-08):

  ```
  Open the WP-30 P1 entries, markers and truth script (WP-30 S01)

  <the contents of <scratch>/s01/01-S01-failure.txt>

  WP-30 closes the 35 P1 items of the drop-in re-audit
  (.ultraplan/handoff/DROPIN-REMAINING.md section 3, "P1"), split into 56
  entries, one per fix section (S02-S57). This opens them: 56 BUGS.md
  entries, open and graded S1 (9), S2 (38) and S3 (9) in the form "Not
  fixed because WP-30 section NN has not landed"; the WP30_OPEN allowance,
  which with WP29_OPEN alone exempts open S1/S2 entries from the release
  guard while each stays in that form; WP30_LISTS and WP30_SECTION, the
  CHANGELOG lists each entry belongs in and the section that closes it,
  with 84 markers in six lists of the 0.1.0 release and a new "Fixed in
  WP-30" heading; test/test_wp30_truth.cscript, the package's one truth
  script, with a scaffold block and one gated, timed block per fix
  section, registered as runner block 69 and guarded by
  TestTheWp30TruthScript; one comment anchor per section in the two
  coverage maps; and a guard that every name the served app's copy lists
  name is defined in dash_render.py.

  Regression: test/test_tracking_documents.py::TestWp30Tracking -- failed at <base> with NameError: name '_wp30_open_problems' is not defined
  Regression: test/test_cscript_hygiene.py::TestTheWp30TruthScript -- failed at <base> with NameError: name '_WP30_TRUTH' is not defined
  Regression: test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script -- failed at <base> with assert 67 == 68
  Regression: test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_every_script_that_skips_for_python_is_read -- failed at <base> with assert 49 == 50
  Guard: test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName::test_every_listed_name_exists -- green at <base> (145 constants and 312 functions, each defined, none listed twice)
  Changed: test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2 -- skips exactly the titles WP29_OPEN and WP30_OPEN list
  Truth: test/test_wp30_truth.cscript TF-01 PASS (StataNow 19.5, WP30_ONLY unset; 57 blocks timed)
  ```

  No co-author or tool trailer is added (CLAUDE.md rule 6 overrides any harness default).
- **Notes for the closeout (A145; S58 reads this).**
  - **S58.1.** Confirm `WP30_OPEN` is empty; replace it with `WP30_OPEN = {}` under a comment like WP-29's (:1246-1250); add `TestWp30Tracking::test_no_wp30_entry_remains_open`, a copy of `test_no_wp29_entry_remains_open` (:1508-1525) with WP-30 names (`WP30_OPEN == {}`, no marker left, `_wp30_closure_problems(set(), set(markers), entries) == []`, no entry left in `_WP30_OPEN_FORM`). Keep `WP30_LISTS`, `WP30_SECTION` and `WP30_ALL`: `test_each_p1_sits_in_its_changelog_lists` then keeps each WP-30 line in its list for good. Delete the map anchors left with no key under them (A148), and nothing else in the maps. BUGS.md then holds 3 open entries (2559, 2595 and 2601); P2.49 is not filed, because S08 fixes the brushed-copy bug (ratification row 27, 06oct2026; A146).
  - **S58.2 (GAPS2 Tracked lines).** A GAPS2 id is Closed only when every entry that carries it is closed. The headings and their entries, from Appendix B's Sources: A3: P1.17a, P1.17b; A4: P1.6, P1.8a, P1.8b, P1.24; A6: P1.22; A13: P1.16; B11: P1.14a, P1.14b; B12: P1.8a, P1.8b, P1.9a, P1.9b; B14: P1.6; B16: P1.15a, P1.15b, P1.15c; B17: P1.19; B18: P1.20a, P1.20b; B20: P1.10; B21: P1.18a, P1.18b, P1.19; B22: P1.19, P1.21a, P1.21b; B23: P1.18a; B25: P1.2a, P1.3a, P1.3b; B26: P1.15c; B27: P1.24; B31: P1.15a, P1.15c; D2: P1.12a, P1.12b; D3: P1.11a, P1.11b; D5: P1.4a; D7: P1.13a, P1.13b; D8: P1.1a, P1.1b; D9: P1.18a; D10: P1.4b; D11: P1.2b; D12, D17: P1.2a; D16: P1.2a, P1.3a (D16-a, the minor ticks, closes with S21's commit under register P1.2.7, though Appendix B cites it under P1.2a only); D18, D19: P1.4a; E10: P1.28a, P1.28b; F3: P1.31a, P1.31b; F5: P1.26b; G4: P1.7; G10: P1.5; G14: P1.31a; H4: P1.30, P1.33; H6: P1.32; I12: P1.29; I14: P1.27, P1.29; J7: P1.28a; J8, K3: P1.35; K1: P1.34; K5: P1.30; X4: P1.26a; X5: P1.25a, P1.25b. Thirteen cited ids have no `### ` heading of their own (A7, B8, B9, B13, B29, C5, C10, D6, G15, I4, I7, J2, J5: "same gap as …; see there" or "also reported as …"); they are tracked through the heading that carries them. GAPS2-E10c, H-intro-platforms and H-intro-gui stay open, in the deferred platform package (M4, M8).
  - **S58.2 (REMAINING.md and DROPIN).** The REM-08-04 ids P1.23 cites close with P1.23a and the REM-08-05 ids with P1.23b (Evidence, "Source ids matched by content"); REM-08-04-C6a/C6b close with P1.5. DROPIN-REMAINING.md's P1 rows each name their entries and commits; P1.22 is recorded closed by WP-29 P0.6 and P1.22's note (M12).
  - **S58.2 (ROADMAP header).** `**Severity:**` from S01's grades: S1 (9), S2 (38), S3 (9).
  - **S58.4.** When a list's last marker is gone, the blank lines between consecutive WP-30 items may be removed (formatting only, no rewording). `grep -c '<!-- WP-30' CHANGELOG.md` must print 0.
  - **S58.7.** Per-block times come from `S<NN> start <date> <time>` / `S<NN> end <date> <time>` in the certification log.


## Appendix A: the 56 entries (TR-01.1; read by `s01_apply.py`)

One row per entry, in entry order (A140). `S` is the closing section, `Grade` the grade its open Resolution carries, the lists are its `WP30_LISTS` row (index.md "P1 coverage"), and the last column is the manifest's section name, verbatim: the map anchors use it whole, and the truth-script stub header drops its trailing parenthesis.

| Entry | S | Grade | `WP30_LISTS` (in order) | Section name (manifest; stub header drops the trailing parenthesis) |
|---|---|---|---|---|
| P1.1a | 11 | S2 | Results that change; Changed behaviour | Stylelists of style options across an expanded varlist (P1.1 part a) |
| P1.1b | 20 | S2 | Changed behaviour; Fixed in WP-30 | Per-series value lists (P1.1 part b) |
| P1.2a | 15 | S3 | Results that change | Scheme chrome: titles, ticks, grid, economist axes (P1.2 part a, M1) |
| P1.2b | 16 | S3 | Results that change | Intensity as an opaque blend (P1.2 part b, M1) |
| P1.3a | 21 | S3 | Results that change | natscale ticker and twoway margin on non-date axes (P1.3 part a, M1) |
| P1.3b | 44 | S3 | Results that change | tsnatscale on %td-%ty default axes (P1.3 part b, M1) |
| P1.4a | 24 | S3 | Results that change | Scheme opacity, histogram style and symbols reach every layer (P1.4 part a) |
| P1.4b | 33 | S3 | Results that change | Marker-label and colour-key chrome; unread directives retained (P1.4 part b) |
| P1.5 | 18 | S1 | Results that change; Changed behaviour | Axis format fallbacks (P1.5) |
| P1.6 | 51 | S2 | New; Changed behaviour | tsline time-axis options (P1.6) |
| P1.7 | 42 | S2 | New; Changed behaviour | Time-series operators in plot varlists (P1.7) |
| P1.8a | 40 | S2 | Results that change; Changed behaviour | connect() and cmissing() (P1.8 part a) |
| P1.8b | 45 | S2 | Results that change; Changed behaviour | recast() (P1.8 part b) |
| P1.9a | 49 | S2 | Results that change; Changed behaviour | horizontal drawn (P1.9 part a, M5) |
| P1.9b | 55 | S2 | Fixed in WP-30 | horizontal after a filter move (P1.9 part b) |
| P1.10 | 56 | S2 | New; Changed behaviour | text() and ttext() annotations (P1.10) |
| P1.11a | 09 | S2 | Security; Results that change | TeX delimiters inert on every canvas sink (P1.11 part a) |
| P1.11b | 29 | S2 | Results that change | SMCL in graph text (P1.11 part b) |
| P1.12a | 08 | S2 | Results that change; Changed behaviour | Stata size units for markers, text and gaps (P1.12 part a, M1) |
| P1.12b | 13 | S2 | Results that change; Changed behaviour | Stata line-width ladder (P1.12 part b, M1) |
| P1.13a | 30 | S2 | Results that change; Changed behaviour | Stata colour grammar (P1.13 part a) |
| P1.13b | 43 | S2 | Results that change | Default colour and opacity at every colour site (P1.13 part b) |
| P1.14a | 32 | S2 | Results that change | Named styles p1-p15 (P1.14 part a) |
| P1.14b | 36 | S2 | Results that change | Other style names (P1.14 part b) |
| P1.15a | 28 | S2 | Results that change | by() panel labels and overall text (P1.15 part a) |
| P1.15b | 48 | S2 | Results that change; Changed behaviour | by() grid and size (P1.15 part b) |
| P1.15c | 53 | S2 | Results that change | Shared axes and keys under by() (P1.15 part c) |
| P1.16 | 19 | S1 | Results that change | Legend keys and default axis titles (P1.16) |
| P1.17a | 14 | S1 | Results that change; Changed behaviour | Bar widths and range caps (P1.17 part a) |
| P1.17b | 27 | S1 | Results that change | twoway's default base and axis extent (P1.17 part b) |
| P1.18a | 31 | S2 | Results that change; Changed behaviour | Axis look sub-options (P1.18 part a, M5/M6) |
| P1.18b | 52 | S1 | Results that change | The add sub-option (P1.18 part b) |
| P1.19 | 10 | S2 | Changed behaviour; Fixed in WP-30 | Sub-option abbreviations (P1.19) |
| P1.20a | 38 | S1 | Results that change; Changed behaviour | plotregion()/graphregion() styling (P1.20 part a) |
| P1.20b | 47 | S1 | Results that change | Plot-region margin and inner box (P1.20 part b) |
| P1.21a | 39 | S2 | Results that change; Changed behaviour | xline/yline positions, refusals and lstyle (P1.21 part a) |
| P1.21b | 50 | S2 | Results that change | xline/yline extend, noextend and style() (P1.21 part b) |
| P1.22 | 26 | S3 | Fixed in WP-30 | function: closed by disposition (P1.22 under M12) |
| P1.23a | 35 | S1 | Results that change | Date positions on every axis (P1.23 part a) |
| P1.23b | 17 | S1 | Results that change | Date and format text in keys and tooltips (P1.23 part b) |
| P1.24 | 37 | S2 | Fixed in WP-30; Changed behaviour | mlabvposition() and mlabtextstyle() (P1.24) |
| P1.25a | 07 | S2 | New | Ship the six StataCorp schemes (P1.25 part a) |
| P1.25b | 34 | S2 | Results that change; Security | Stata's scheme lookup along the ado-path (P1.25 part b, M7) |
| P1.26a | 06 | S2 | Changed behaviour; Fixed in WP-30 | One note channel (P1.26 part a) |
| P1.26b | 23 | S2 | Changed behaviour; Fixed in WP-30 | Served notes reach Stata (P1.26 part b, M6) |
| P1.27 | 12 | S2 | Changed behaviour; Fixed in WP-30 | Drop-in command form and saving() grammar (P1.27, M5/M11) |
| P1.28a | 22 | S2 | New; Changed behaviour | r(filename) and the stale-graph note (P1.28 part a, M8) |
| P1.28b | 54 | S3 | New | Client-side Save as SVG (P1.28 part b, M8) |
| P1.29 | 04 | S2 | Security | CSP without 'unsafe-inline'; safe Windows opener (P1.29, M11) |
| P1.30 | 41 | S2 | Requirements; Security | Verified bokeh window; internals fail closed (P1.30, M9/M10) |
| P1.31a | 46 | S2 | New; Security | Served session capacity and memory (P1.31 part a) |
| P1.31b | 57 | S2 | Fixed in WP-30 | Served recompute off the event loop (P1.31 part b) |
| P1.32 | 25 | S2 | Requirements | Render-time dependency guards (P1.32) |
| P1.33 | 05 | S2 | Requirements | Measured Python floor (P1.33, M3/M10) |
| P1.34 | 02 | S3 | Fixed in WP-30 | Portable runners (P1.34 under M4) |
| P1.35 | 03 | S2 | Requirements; Changed behaviour | Stata 19 floor declared and enforced (P1.35 under M2) |

## Appendix B: the 56 BUGS.md entries (TR-01.1; verbatim, appended in this order, one blank line between entries)

~~~~text bugs-entries
- [ ] Title: A style list over several y variables, such as mcolor(red blue), is given whole to every series and refused, where twoway gives each series its own element
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_plot_opts (897; MColor(string) at 925 drops the quotes), _dash_plot_opts_to_json (3131), _dash_process_segment (3454; one options JSON for every series in its assembly block, about 4330-4370); dash_render.py at c96facd: GlyphMapper._apply_marker_opts (8622), GlyphMapper._apply_line_opts (8540)
  - Description: DROPIN-REMAINING.md:66 P1.1, the style-option part, re-verified at c96facd: `scatter mpg turn weight, mcolor(red blue) msymbol(O T)` gives every y the whole list. The renderer then refuses "red blue" and draws scheme defaults, with a misleading note. The same holds for line style lists, the `.`/`=` shorthands, and a single-y list (where `twoway` uses the first element). Also measured: a lone value or a short list styles every series where twoway styles only the leading ones, quoted elements lose their quotes, and `mcolor(red .. blue)` is accepted where twoway refuses it r(198). Sources: REM-S06-c, GAPS2-D8-a, GAPS2-D8-b, GAPS2-D8-c, GAPS2-D8-d, GAPS2-D8-e (the style options).
  - Suggested fix: WP-30 section 11 (Stylelists of style options across an expanded varlist): split each style option's list across the expanded series as twoway does, with the `.`, `=`, `..` and `...` shorthands, quoted elements kept whole and the first element on single-y types, refusing a misplaced `..` with twoway's code and words.
  - Resolution: Not fixed because WP-30 section 11 has not landed. Graded S2 (WP-30): a common multi-y do-file draws every series in the scheme's defaults, under a note that blames the colour.

- [ ] Title: Per-series value lists such as mlabel(make rep78), jitter(2 3), base(10 20) and barwidth(1 2) are refused r(198), where twoway applies them series by series
  - File Names and Line Numbers: dash.ado at c96facd: _dash_option_rules (2025; the per-option list rules, about 2032-2042), _dash_validate_value (2125), _dash_fold_mlab (1691)
  - Description: DROPIN-REMAINING.md:66 P1.1, the per-series value-list part (research sub-claim h), re-verified at c96facd: `mlabel(make rep78)` is refused r(198) (mlabel() must name one variable), and `jitter(2 3)`, `base(10 20)` and `barwidth(1 2)` are refused r(198), where twoway accepts each and applies it by series: series 1 labelled by make and series 2 by rep78, bottoms at 10 and 20. Sources: REM-S06-c, GAPS2-D8 (the per-series value lists).
  - Suggested fix: WP-30 section 20 (Per-series value lists): read mlabel(varlist), jitter(), base(), barwidth() and mlabposition() positionally per series after the shorthands resolve, refusing what twoway refuses in its words.
  - Resolution: Not fixed because WP-30 section 20 has not landed. Graded S2 (WP-30): twoway's per-series forms are refused.

- [ ] Title: The default chrome differs from every scheme: a bold left-aligned title, italic axis titles, Bokeh's minor ticks and tick geometry, and the schemes' tick angles, grid patterns, tick colours and economist axes missing
  - File Names and Line Numbers: dash_render.py at c96facd: SchemeParser.apply_to_figure (7376), SchemeParser.apply_to_axis (7429), _dash_figure_title (25905), _dash_style_axis_titles (25929), _dash_text_annotations (25969), _dash_add_secondary_axes (23034); scripts/extract_scheme_truth.py
  - Description: DROPIN-REMAINING.md:67-76 P1.2, the chrome part, re-verified at c96facd: the title is bold and left-aligned (Stata centres it and does not bold it); axis titles are italic; subtitle, note and caption sit at x=0; Bokeh minor ticks are drawn and tick geometry is Bokeh's; s2color's vertical y tick labels are missing, as is stcolor's dashed grid; s1rcolor's ticks are invisible (black on black), and economist's y axis is wrong. Sources: GAPS2-D17-a, GAPS2-D17-b, GAPS2-D17-c, GAPS2-D17-d, REM-11-04-A1-ALIGN, GAPS2-B29, GAPS2-D16-a, GAPS2-D16-c, GAPS2-D16-d, GAPS2-D12-a, GAPS2-D12-b, GAPS2-D12-c, GAPS2-B25-c.
  - Suggested fix: WP-30 section 15 (Scheme chrome: titles, ticks, grid, economist axes): draw each scheme's title, axis-title, tick, grid and axis chrome from the scheme's own keys in Stata units, in both modes (maintainer decision M1).
  - Resolution: Not fixed because WP-30 section 15 has not landed. Graded S3 (WP-30): fidelity: every graph's chrome differs from its scheme's, and no value is misread.

- [ ] Title: Markers are drawn at alpha 0.8, and fintensity() and the schemes' bar and area intensities are applied as transparency, where Stata blends them opaquely
  - File Names and Line Numbers: dash_render.py at c96facd: SchemeParser.default_alpha (7222), SchemeParser._intensity (6577), GlyphMapper._scheme_alpha (9727), GlyphMapper._blend_intensity (8293), GlyphMapper._apply_fill_opts (8807), GlyphMapper._ci_band_style (8307)
  - Description: DROPIN-REMAINING.md:67-76 P1.2, the opacity part, re-verified at c96facd: markers are drawn at alpha 0.8, and `fintensity()` is applied as alpha; so are the schemes' p#bar and p#area intensities. Sources: GAPS2-D11-a, GAPS2-D11-b.
  - Suggested fix: WP-30 section 16 (Intensity as an opaque blend): draw markers opaque unless an opacity is asked for, and blend every intensity into an opaque colour, in both modes (maintainer decision M1).
  - Resolution: Not fixed because WP-30 section 16 has not landed. Graded S3 (WP-30): fidelity: colours are paler and see-through where Stata's are solid, and no value is misread.

- [ ] Title: Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ticks and plot-region margin, and fit lines are left out of the axis range
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_count_ticker (22176), _dash_padded_range (23489), _dash_finish_count_ticks (23732), _dash_keep_primary_ranges (23316), _dash_limit_ranges_to_primary (23913), _dash_share_by_scales (23845), _FILTER_JS (18562)
  - Description: DROPIN-REMAINING.md:77 P1.3, the non-date part, re-verified at c96facd: every default axis gets BasicTicker and 10% padding (5% a side), where twoway uses natscale ticks over the hull of the data and its ticks plus a plot-region margin. twoway's (by) common scale includes fit lines and dash's does not (WP-29 S10 note), and after a filter move the default axes follow Bokeh's autorange. Sources: GAPS2-B25-a (numeric, log and %tc axes), GAPS2-B25-b.
  - Suggested fix: WP-30 section 21 (natscale ticker and twoway margin on non-date axes): draw default numeric, log and %tc axes with natscale ticks over every drawn layer plus twoway's plot-region margin, re-finished after every filter move in both modes (maintainer decision M1).
  - Resolution: Not fixed because WP-30 section 21 has not landed. Graded S3 (WP-30): fidelity: tick positions and padding differ, and every value is drawn where it belongs.

- [ ] Title: Default %td to %ty date axes keep Bokeh's DatetimeTicker, not twoway's tsnatscale ticks
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_tsnatscale_ticks (22491), _dash_count_ticker (22176), _FILTER_JS (18562); BUGS.md:2523 (the open WP-27 entry on the fitted model)
  - Description: DROPIN-REMAINING.md:77 P1.3, the date part, re-verified at c96facd: every default %td, %tw, %tm, %tq, %th and %ty axis gets Bokeh's DatetimeTicker, where twoway draws tsnatscale ticks; dash's fitted tsnatscale model serves only #N ticks today. Sources: GAPS2-B25-a (date axes).
  - Suggested fix: WP-30 section 44 (tsnatscale on %td-%ty default axes): draw default date axes with the fitted tsnatscale model at build and after every filter move in both modes, through a JavaScript port pinned to the model's 12,000 measured answers (maintainer decision M1).
  - Resolution: Not fixed because WP-30 section 44 has not landed. Graded S3 (WP-30): fidelity: tick positions differ, and every value is drawn where it belongs.

- [ ] Title: The scheme's opacity, histogram colour, intensity and width, and its hollow and sm symbols do not reach fits, spikes, ranges, immediates, histograms or rarea
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper._scheme_alpha (9727), GlyphMapper._histogram_quads (12423), GlyphMapper.map_rarea (12933), GlyphMapper._empty_fit_line (10823), GlyphMapper._apply_marker_opts (8622), SchemeParser._symbol (6797), OptionTranslator.translate_msymbol (5516)
  - Description: DROPIN-REMAINING.md:78-87 P1.4, the layer part, re-verified at c96facd: sttrans opacity is missing on fits, spikes, ranges, immediates and bands; histograms ignore the scheme's histogram colour, intensity and line width (and the empty histogram key colour, the WP-29 S12 residual); hollow and sm* p# symbols are drawn filled and full size; rarea is drawn at alpha 0.5. Also measured: the p# symbol cycle does not reach scatteri, rscatter, pcscatter, dropline or rcapsym; markers read p#mark where twoway reads p#markfill and p#markline; msymbol(Oh) with malpha() refills a hollow marker. Sources: GAPS2-D18-a, GAPS2-D18-b, GAPS2-D18-c, GAPS2-D18-d, AUDIT-76, GAPS2-D19-a, GAPS2-D19-b, GAPS2-D5-g, GAPS2-D5-h, REM-11-04-B13-RAREA.
  - Suggested fix: WP-30 section 24 (Scheme opacity, histogram style and symbols reach every layer): carry the scheme's opacity, histogram keys and symbol traits to every layer type at construction, in both modes.
  - Resolution: Not fixed because WP-30 section 24 has not landed. Graded S3 (WP-30): fidelity: layers are drawn in another opacity, style or symbol than their scheme's.

- [ ] Title: Marker-label size and colour are fixed, the colour key has no scheme chrome, and unread user-scheme directives are ignored silently
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper._apply_mlabel_opts (9302), GlyphMapper._apply_colorvar (8887), SchemeParser._parse_lines (6318), SchemeParser._include (6389)
  - Description: DROPIN-REMAINING.md:78-87 P1.4, the chrome part, re-verified at c96facd: marker-label size and colour are fixed at 10px #444444 (9px in the served app); the ColorBar has no chrome; unconsumed user-scheme directives are ignored silently. Sources: REM-11-04-B1, REM-S11-e2, REM-11-04-C11, GAPS2-D10-a, GAPS2-D10-b.
  - Suggested fix: WP-30 section 33 (Marker-label and colour-key chrome; unread directives retained): take marker-label and colour-key chrome from the scheme in Stata units, in both modes, and keep every user-scheme directive in the parsed scheme for later versions, with no note (ratification row 4).
  - Resolution: Not fixed because WP-30 section 33 has not landed. Graded S3 (WP-30): fidelity: label and key chrome differ from the scheme's, and a user scheme's unread keys pass unmentioned.

- [ ] Title: Default tick labels ignore the variable's display format, xlabel(, format(%td)) is ignored silently, and a numeric format() on a date axis writes epoch milliseconds
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_apply_axis_options (22997), _dash_apply_axis_spec (22714), _dash_finish_secondary_axes (23172), _dash_fmt (21063), DashRenderer._make_figure_body (30203); dash.sthlp: the log example under Axis and Display Options
  - Description: DROPIN-REMAINING.md:88-95 P1.5, re-verified at c96facd: default ticks ignore the variable's display format (weight %9.0fc gives 2000, not 2,000); %g/%gc formats are never used as the fallback; `xlabel(, format(%td…))` is silently ignored; a numeric `format()` on a date axis writes epoch ms; the help's log example promises commas that dash does not write. Sources: REM-09-02-FMT-a, REM-09-02-FMT-b, GAPS2-G10-a, GAPS2-G10-b, REM-09-02-DATE-FORMAT, REM-08-04-C6b, GAPS2-B8-b, REM-08-04-C6a, GAPS2-G10-c.
  - Suggested fix: WP-30 section 18 (Axis format fallbacks): write default ticks in twoway's axis format, honour format() on date and numeric axes, and refuse the format() forms twoway refuses, in both modes and after a filter move.
  - Resolution: Not fixed because WP-30 section 18 has not landed. Graded S1 (WP-30): silently wrong text: tick labels in epoch milliseconds, and a format() the user gave dropped without a note.

- [ ] Title: The tsline time-axis options tlabel, ttick, tmlabel, tmtick, ttitle, tscale and tline are undeclared and only named in the note
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_graph_opts (682), _dash_parse_plot_opts (897), _dash_axis_expand (2537); dash_parse.mata at c96facd: _dash_route_axis2 (5486)
  - Description: DROPIN-REMAINING.md:96 P1.6, re-verified at c96facd: `tlabel`, `ttick`, `tmlabel`, `tmtick`, `ttitle`, `tscale` and `tline` are undeclared and only named in the note. They need folding onto the x equivalents, with date-literal expansion. Sources: REM-§2-S09-tlabel, REM-§2-S09-ttick, REM-§2-S09-tline, REM-§2-S09-ttitle, REM-S09-73-tsaxis-a, REM-S09-73-tsaxis-b, REM-05-04-S09-a, REM-05-04-S09-b, GAPS2-A4-q, GAPS2-B14-a, GAPS2-B14-b, GAPS2-B14-c, REM-15-03-E5.
  - Suggested fix: WP-30 section 51 (tsline time-axis options): declare the t* options for every twoway graph and fold them onto x axis 1 with Stata-unit date literals, refusing date literals where twoway's x axis is numeric.
  - Resolution: Not fixed because WP-30 section 51 has not landed. Graded S2 (WP-30): accepted twoway options are named and not drawn.

- [ ] Title: Time-series operators in plot varlists, such as line D.close date and lfit y L.x, are refused r(101)
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_varpart_std (1310), _dash_parse_varpart_any (1444), _dash_process_segment (3454); dash_render.py at c96facd: _dash_take_qual_columns (27657), DashRenderer._load_data (29266)
  - Description: DROPIN-REMAINING.md:97 P1.7, re-verified at c96facd: time-series operators in plot varlists are refused r(101). This covers `line D.close date`, `tsline D.gdp` and `lfit y L.x`, and the help does not document it. Sources: GAPS2-G4-a, GAPS2-G4-b, GAPS2-G4-c.
  - Suggested fix: WP-30 section 42 (Time-series operators in plot varlists): accept the L., F., D. and S. operators wherever twoway does, materialised under tsset and labelled as twoway labels them, refusing what twoway refuses in its words.
  - Resolution: Not fixed because WP-30 section 42 has not landed. Graded S2 (WP-30): a common time-series form is refused.

- [ ] Title: connect() and cmissing() are not honoured: scatter y x, c(l) draws no line, stairsteps and connect(L) cannot be drawn, and cmissing(n) never breaks a line
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_scatter (9744), GlyphMapper.map_line (9880), GlyphMapper.map_connected (9991), GlyphMapper.map_tsline (14468), _FILTER_JS (18562); dash.ado at c96facd: _dash_parse_plot_opts (897)
  - Description: DROPIN-REMAINING.md:98 P1.8, the connect() and cmissing() part, re-verified at c96facd: `scatter y x, c(l)` draws no line, stairsteps and `connect(L)` panel lines are impossible, and missing values are always bridged. (WP-29 note: P0.1 made the six joining types join in the data's order; connect() on scatter and cmissing() stay here.) Sources: REM-§2-S06-connect, REM-S05-04-connect, GAPS2-A4-l, GAPS2-A4-m, GAPS2-B12-c, GAPS2-B12-d, GAPS2-G15-a, AUDIT-09, AUDIT-11.
  - Suggested fix: WP-30 section 40 (connect() and cmissing()): draw every connect() style and cmissing(n) breaks on scatter, the line family and the fits as twoway draws them, in both modes and after a filter move.
  - Resolution: Not fixed because WP-30 section 40 has not landed. Graded S2 (WP-30): accepted twoway options are named and not drawn.

- [ ] Title: recast() is not honoured, and recast() on lfitci, qfitci, lpolyci and fpfitci is accepted where twoway refuses it
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_plot_opts (897), _dash_fold_bw (1545), _dash_fold_typed (1749); dash_render.py at c96facd: _dash_glyph_dispatch (28501)
  - Description: DROPIN-REMAINING.md:98 P1.8, the recast() part, re-verified at c96facd: `recast()` is not honoured. Also measured: dash accepts recast() on the ci types, which twoway refuses, and the spellings recastas() and type() are not declared. Sources: GAPS2-A4-n, GAPS2-B12-b, AUDIT-12 (with AUDIT-09, AUDIT-11 and GAPS2-G15-a, shared with connect()).
  - Suggested fix: WP-30 section 45 (recast()): draw a recast layer as its new type with twoway's fallbacks, and refuse recast() on the ci types with twoway's code and words.
  - Resolution: Not fixed because WP-30 section 45 has not landed. Graded S2 (WP-30): an accepted twoway option is named and not drawn.

- [ ] Title: horizontal is not drawn on any plot type, and vertical is named as unsupported
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_bar (10122), GlyphMapper.map_rcap (13153), GlyphMapper.map_dropline (13398), _dash_axis_labels (21665), _dash_figure_date_kind (788), _compute_secondary_range (7684)
  - Description: DROPIN-REMAINING.md:99 P1.9, the drawing part, re-verified at c96facd: `horizontal` is not drawn on any type; it is common on bar, rcap, rspike and dropline. It is named in the note, `vertical` (twoway's default) is named as unsupported, and the help says every plot is drawn upright. (WP-29 note: horizontal on function and on computed layers on a date axis stays here.) Sources: REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15 (the drawing).
  - Suggested fix: WP-30 section 49 (horizontal drawn): draw horizontal on every type twoway turns, with the axes and titles swapped, and refuse it where twoway refuses it, in both modes.
  - Resolution: Not fixed because WP-30 section 49 has not landed. Graded S2 (WP-30): an accepted twoway option is named and not drawn.

- [ ] Title: The filter-move redraws of both modes write vertical geometry only, so a horizontal layer cannot keep its orientation after a move
  - File Names and Line Numbers: dash_render.py at c96facd: _FILTER_JS (18562), _dash_copy_redraw_geometry (24941), _dash_build_hover (27118), ServerAppBuilder._generate_app_source (33915; the generated _dash_redraw_for at 35039)
  - Description: DROPIN-REMAINING.md:99 P1.9, the after-a-move part, re-verified at c96facd: `horizontal` is not drawn on any type, and the saved page's redraw and the served app's geometry copy write widths and vertical tooltip fields only, so a turned bar or range would be redrawn upright after a filter move. Sources: REM-§2-S06-horizontal, REM-S06-a, GAPS2-A7, GAPS2-B12-a, AUDIT-15 (after a move).
  - Suggested fix: WP-30 section 55 (horizontal after a filter move): keep a turned layer's geometry, tooltip and reference lines after saved and served filter moves, through a fixed branch that never reads a property name from page data.
  - Resolution: Not fixed because WP-30 section 55 has not landed. Graded S2 (WP-30): an accepted twoway option would be lost at the first filter move.

- [ ] Title: text() and ttext() annotations are not drawn
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_graph_opts (682; TEXT(string asis) at 726), _dash_parse_plot_opts (897; 971); dash_parse.mata at c96facd: _dash_rep_merge (5715); dash_render.py at c96facd: _dash_text_annotations (25969), DashRenderer._make_figure_body (30203)
  - Description: DROPIN-REMAINING.md:100 P1.10, re-verified at c96facd: `text()` and `ttext()` annotations are not drawn. Sources: REM-§2-S09-text, REM-S09-73-text, GAPS2-B20-a, AUDIT-13, REM-§2-S09-ttext, GAPS2-B20-b.
  - Suggested fix: WP-30 section 56 (text() and ttext() annotations): parse and draw text() and ttext() where twoway puts them, with size, colour, box and orientation, on every by() panel and after a move, refusing malformed points as twoway does.
  - Resolution: Not fixed because WP-30 section 56 has not landed. Graded S2 (WP-30): accepted twoway options are named and not drawn.

- [ ] Title: TeX delimiters in titles, labels and keys are typeset as mathematics through MathJax where twoway draws them as typed, and the saved page carries the TeX engine
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_inert_tex (24012), DashRenderer._build_sources_and_figures (31389), ServerAppBuilder._generate_app_source (33915)
  - Description: DROPIN-REMAINING.md:101 P1.11, the TeX part, re-verified at c96facd: `$$…$$` in a title triggers MathJax, which grows the page from 1.3 MB to 3.1 MB; `_dash_inert_tex` breaks the delimiters only in widget titles, so user text in canvas titles, labels, ticks and keys reaches MathJax's TeX parser. Sources: GAPS2-D3-e (the TeX delimiters), GAPS2-J5.
  - Suggested fix: WP-30 section 09 (TeX delimiters inert on every canvas sink): make TeX delimiters inert on every canvas text sink in one document pass in both modes, so TeX pairs are drawn as typed and the saved page no longer ships MathJax.
  - Resolution: Not fixed because WP-30 section 09 has not landed. Graded S2 (WP-30): typed text is drawn as mathematics, and user text reaches a TeX parser.

- [ ] Title: SMCL in graph text, such as {bf:}, {it:}, {sup:}, {&beta} and {c #}, is drawn literally
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_inert_tex (24012), GlyphMapper._apply_mlabel_opts (9302), GlyphMapper._mlabel_column_kind (9607); dash.sthlp (no paragraph on graph text)
  - Description: DROPIN-REMAINING.md:101 P1.11, the SMCL part, re-verified at c96facd: `{bf:}`, `{it:}`, `{sup:}`, `{&beta}` and `{c #}` are drawn literally, as are the font tags `{stSerif:}` and `{fontface}`, in both modes, and the help does not document graph-text markup. Sources: GAPS2-D3-a, GAPS2-D3-b, GAPS2-D3-c, GAPS2-D3-d, GAPS2-J2, GAPS2-B13.
  - Suggested fix: WP-30 section 29 (SMCL in graph text): translate Stata's graph-text grammar to Unicode and whole-string style at every canvas sink and in marker labels with a linear-time scanner, noting once what cannot be drawn, in both modes.
  - Resolution: Not fixed because WP-30 section 29 has not landed. Graded S2 (WP-30): the markup is drawn as visible braces.

- [ ] Title: Marker, text and gap sizes are read as pixels on a private ladder, and #pt, *# and vhuge are refused, where twoway reads Stata's relative size units
  - File Names and Line Numbers: dash_render.py at c96facd: OptionTranslator (5098; its size translators), _textbox_size (4819), GlyphMapper._apply_marker_opts (8622), GlyphMapper._apply_mlabel_opts (9302; mlabgap); dash.ado at c96facd: _dash_validate_value (2125), _dash_option_rules (2025); CHANGELOG.md:521-522 (the msize(abc) note)
  - Description: DROPIN-REMAINING.md:102 P1.12, the marker, text and gap part, re-verified at c96facd: numbers are read as pixels and keywords use a private pixel ladder: `msize(medium)` gives 11px against a default of 8. `#pt`, `*#` and `vhuge` are refused, and `mlabgap` is read as px. Also measured: text size(large) is smaller than the scheme's default, and an explicit msize or mcolor does not reach the nonselection and muted glyphs. Sources: GAPS2-D2-a, GAPS2-D2-b, GAPS2-D2-d, GAPS2-D2-e (marker, text and gap sizes), GAPS2-B9.
  - Suggested fix: WP-30 section 08 (Stata size units for markers, text and gaps): read every marker, text and gap size in Stata's relative units with #pt, *# and the full keyword ladder, in both modes (maintainer decision M1).
  - Resolution: Not fixed because WP-30 section 08 has not landed. Graded S2 (WP-30): twoway's size forms are refused, and every size keyword is drawn at another size.

- [ ] Title: Line widths use a private ladder without vvvthin or none and read numbers as pixels, and negative widths twoway refuses are accepted
  - File Names and Line Numbers: dash_render.py at c96facd: OptionTranslator._LWIDTH_MAP (5324), GlyphMapper._apply_line_opts (8540), SchemeParser._lwidth (6625), _extract_region_lwidth (5065), _dash_refline_draw (26327); dash.ado at c96facd: _dash_validate_value (2125)
  - Description: DROPIN-REMAINING.md:102 P1.12, the line-width part, re-verified at c96facd: numbers are read as pixels (`lwidth(.3)` is 0.3px) and keywords use a private ladder whose ratios are not Stata's; `vvvthin` is missing, as is `none`; `#pt` and `*#` are refused; negative unit and multiplier forms are accepted where twoway refuses them. Sources: GAPS2-D2-c, GAPS2-D2-a, GAPS2-D2-b, GAPS2-D2-e (line widths).
  - Suggested fix: WP-30 section 13 (Stata line-width ladder): replace the private width map with Stata's lwidth ladder in Stata units at every line site, refusing the forms twoway refuses (maintainer decisions M1 and M5).
  - Resolution: Not fixed because WP-30 section 13 has not landed. Graded S2 (WP-30): twoway's width forms are refused, and every width keyword is drawn at another width.

- [ ] Title: Stata colour forms such as navy*.5, CMYK, HSV, bg and fg are refused, and an unknown colour is drawn in the scheme's default where twoway draws it black with a note
  - File Names and Line Numbers: dash_render.py at c96facd: OptionTranslator.parse_color_alpha (5379), OptionTranslator.translate_mcolor (5445), SchemeParser._color (6466); scripts/extract_scheme_truth.py
  - Description: DROPIN-REMAINING.md:103 P1.13, the grammar part, re-verified at c96facd: `navy*.5`, CMYK, HSV and bg/fg are refused. An unreadable scheme colour falls back to #000000 (twoway does the same for some keys). Also measured: an unknown option colour is drawn in the scheme's default where twoway draws it black with a note, colour names are lower-cased where twoway is case-sensitive, and dash accepts forms twoway refuses. Sources: GAPS2-D7-a, GAPS2-D7-c, GAPS2-D7-d, GAPS2-D7-e.
  - Suggested fix: WP-30 section 30 (Stata colour grammar): read Stata's whole colour grammar in options and scheme files through one reader, drawing an unknown colour black with twoway's note and refusing what twoway refuses (maintainer decision M5).
  - Resolution: Not fixed because WP-30 section 30 has not landed. Graded S2 (WP-30): twoway's colour forms are refused.

- [ ] Title: A bare *# or %# colour, such as mcolor(*.5), is refused or loses the site's default colour, where twoway adjusts that default
  - File Names and Line Numbers: dash_render.py at c96facd: OptionTranslator.translate_mcolor (5445), _textbox_color (4839), _resolve_kpi_color (17054), _dash_graph_color (15407), _dash_refline_draw (26327)
  - Description: DROPIN-REMAINING.md:103 P1.13, the default-colour part, re-verified at c96facd: `*.5` (the default colour at an adjusted intensity) is refused, and a bare %# does not keep the site's default colour, at every colour site: markers, lines, fills, bands, marker labels, text, axes, regions, the KPI and reference lines. Sources: GAPS2-D7-b.
  - Suggested fix: WP-30 section 43 (Default colour and opacity at every colour site): give a bare *# and %# the site's own default colour at every colour site, composed with the intensity blend and the named style, in both modes.
  - Resolution: Not fixed because WP-30 section 43 has not landed. Graded S2 (WP-30): a twoway colour form is refused.

- [ ] Title: pstyle() works only on the four CI fits, and lstyle, mstyle, mlstyle, astyle, alstyle, bstyle and their siblings are not read
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_plot_opts (897), _dash_plot_opts_to_json (3131); dash_render.py at c96facd: _dash_plot_style_indices (26709), GlyphMapper._ci_band_style (8307), SchemeParser (5646)
  - Description: DROPIN-REMAINING.md:104 P1.14, the p1-p15 part, re-verified at c96facd: `pstyle()` works only on the four CI fits. `lstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle` and `dstyle` are not read; nor are twoway's `p()` spelling, `blstyle()` and `clstyle()`. Sources: REM-§2-S09-lstyle, REM-§2-S09-mstyle, REM-§2-S09-areastyle, REM-S09-73-namedstyles, REM-05-04-S09-g, GAPS2-B11-a, GAPS2-B11-b, GAPS2-D6, AUDIT-29, AUDIT-30 (the p# names).
  - Suggested fix: WP-30 section 32 (Named styles p1-p15): apply pstyle and the other named-style options with p1-p15 on every type in both modes, in twoway's order, with explicit options winning.
  - Resolution: Not fixed because WP-30 section 32 has not landed. Graded S2 (WP-30): accepted twoway options are named and not drawn.

- [ ] Title: Style names other than p1-p15, such as ci, histogram, refline and p1bar, are not read by pstyle() and the other style options
  - File Names and Line Numbers: dash_render.py at c96facd: SchemeParser (5646), OptionTranslator (5098); scripts/extract_scheme_truth.py
  - Description: DROPIN-REMAINING.md:104 P1.14, the other-names part, re-verified at c96facd: the named-style options read no Stata style name outside p1-p15 (ci, ci2, histogram, foreground, background, grid, refline, none, and the p#line, p#bar, p#area and p#mark suffixes), an unknown name is not noted as twoway notes it, and `dstyle()` is not declared. Sources: GAPS2-B11-c, GAPS2-D6, AUDIT-30 (the other names).
  - Suggested fix: WP-30 section 36 (Other style names): read every Stata named-style name the shipped style files define through the style bundle, noting an unknown name as twoway does.
  - Resolution: Not fixed because WP-30 section 36 has not landed. Graded S2 (WP-30): accepted twoway style names are named and not drawn.

- [ ] Title: by() panel labels are appended to the graph title, there is no Graphs by note, composite and missing panels are titled differently, and by(, title()) is ignored
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_facet_label (20107), DashRenderer._facet_label (30049), _dash_by_groups (3436), DashRenderer._build_sources_and_figures (31389), ServerAppBuilder._generate_app_source (33915)
  - Description: DROPIN-REMAINING.md:105-112 P1.15, the panel-text part, re-verified at c96facd: panel labels are appended to the graph title, and there is no "Graphs by" note; composite and missing panels are titled differently from twoway; `title`, `subtitle`, `note` and `caption` inside `by()` are named in the note and ignored. Also measured: a string by() variable's empty group is drawn as an untitled panel where twoway leaves it out. Sources: GAPS2-B16-b (title, subtitle, note and caption inside by()), GAPS2-B31-a, GAPS2-B31-b, GAPS2-B31-d.
  - Suggested fix: WP-30 section 28 (by() panel labels and overall text): title each panel apart from the graph title, draw by()'s own title, note and caption once over the array with the Graphs by note, and title composite and missing panels as twoway does, in both modes.
  - Resolution: Not fixed because WP-30 section 28 has not landed. Graded S2 (WP-30): accepted by() sub-options are named and not drawn, and panel titles differ.

- [ ] Title: by() rows, holes, colfirst, compact, iscale and imargin are named and ignored, bad by() arguments are accepted, and faceted graphs miss the automatic layout
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_parse_by (19941), _dash_by_groups (3436), _dash_reflow (24465), _dash_auto_bs_layout (25115)
  - Description: DROPIN-REMAINING.md:105-112 P1.15, the grid and size part, re-verified at c96facd: `rows`, `holes`, `colfirst` and `compact` (with `iscale` and `imargin`) are named in the note and ignored; facet aspect ratios miss the automatic layout. (WP-29 note: `YRESCALE` and two `style()` are accepted where twoway refuses them.) Sources: GAPS2-B16-a (rows, holes and colfirst), GAPS2-B16-e (compact, iscale and imargin), REM-10-03.
  - Suggested fix: WP-30 section 48 (by() grid and size): lay out by() panels with rows(), cols(), holes() and colfirst, size the array and its spacing in Stata units, and refuse bad by() arguments with twoway's codes and words.
  - Resolution: Not fixed because WP-30 section 48 has not landed. Graded S2 (WP-30): accepted by() sub-options are named and not drawn.

- [ ] Title: Under by() every panel draws a legend and repeats both axes, and by(, legend()) and the i* axis options are named and ignored
  - File Names and Line Numbers: dash_render.py at c96facd: DashRenderer._build_sources_and_figures (31389), _dash_reflow (24465), _dash_share_by_scales (23845), _dash_apply_legend (21400), GlyphMapper._apply_colorvar (8887)
  - Description: DROPIN-REMAINING.md:105-112 P1.15, the axes and legend part, re-verified at c96facd: every panel draws a legend and repeats both axes; `legend()` and the `i*` axes inside `by()` are named in the note and ignored. (WP-29 notes: dash draws an explicit axis-2 title on every panel where twoway draws none, and a colour key on every panel where twoway draws one only under by(, clegend(on)).) Sources: GAPS2-B16-c (the i*/noi* axes and noedgelabel), GAPS2-B16-d (legend() inside by()), GAPS2-B26-d, GAPS2-B31-c, AUDIT-71, AUDIT-72.
  - Suggested fix: WP-30 section 53 (Shared axes and keys under by()): show outer axes and edge labels only, one legend and at most one colour key, honouring the i* options and by(, legend()), in both modes.
  - Resolution: Not fixed because WP-30 section 53 has not landed. Graded S2 (WP-30): accepted by() sub-options are named and not drawn.

- [ ] Title: Legend keys and default axis titles do not follow twoway: fits are keyed Fitted values, pc and immediate types by their type name, the y title follows the first layer, and range types get none
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_legend_key (26925), _dash_legend_keys (26960), _dash_axis_labels (21665), _dash_add_secondary_axes (23034), GlyphMapper.map_scatteri (13627); dash.ado at c96facd: _dash_process_segment (3454; the function branch's y name)
  - Description: DROPIN-REMAINING.md:113-120 P1.16, re-verified at c96facd: lowess, lpoly, mband, mspline and function are all keyed "Fitted values"; the pc family and scatteri/pci are keyed by the type name; the y title comes from the first layer even when the layers' labels differ; range types get no y title. (WP-29 P0.3 closed the histogram and kdensity keys; dash draws no default title on yaxis(2) where twoway titles it by its layers' variables.) Sources: GAPS2-A13-a, GAPS2-A13-b, GAPS2-A13-c, GAPS2-A13-d, GAPS2-A13-e, GAPS2-A13-f, GAPS2-C10-a, GAPS2-C10-b, GAPS2-C10-c, GAPS2-C10-d.
  - Suggested fix: WP-30 section 19 (Legend keys and default axis titles): key every layer and choose default axis titles by twoway's text and its first-equals-last rule, including range types and yaxis(2), in both modes.
  - Resolution: Not fixed because WP-30 section 19 has not landed. Graded S1 (WP-30): silently misleading text: an axis titled for one variable while its layers show others.

- [ ] Title: bar and rbar default to 0.8 of the smallest x gap, rbar ignores barwidth() without a note, rcap caps ignore msize(), and rcapsym draws caps twoway does not
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_bar (10122), GlyphMapper.map_rbar (13005), GlyphMapper.map_rcap (13153), GlyphMapper.map_rcapsym (13512), GlyphMapper._tag_spacing (10293), _dash_copy_redraw_geometry (24941)
  - Description: DROPIN-REMAINING.md:121-128 P1.17, the width and cap part, re-verified at c96facd: bar and rbar default to 0.8× the smallest x gap, not 1 x-unit; rbar ignores `barwidth()` with no note; rcap cap width ignores `msize()`, and rcapsym draws caps twoway does not. (WP-29 notes: barwidth() on a date axis is read in ms; P0.18 fixed the served redraw widths only.) Sources: GAPS2-A3-a, GAPS2-A3-b, GAPS2-A3-d, GAPS2-A3-e, AUDIT-44.
  - Suggested fix: WP-30 section 14 (Bar widths and range caps): draw bars one x-unit wide, honour rbar barwidth(), size rcap caps from msize() and draw rcapsym without caps, unchanged by filter moves in both modes.
  - Resolution: Not fixed because WP-30 section 14 has not landed. Graded S1 (WP-30): a user's rbar barwidth() is dropped without a note.

- [ ] Title: bar, area, spike and dropline draw from 0 rather than twoway's default base, and a 0 outside the data extends the axis to it
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_bar (10122), GlyphMapper.map_area (10029), GlyphMapper.map_spike (10311), GlyphMapper.map_dropline (13398), _dash_finish_count_ticks (23732), _dash_units_to_axis (569)
  - Description: DROPIN-REMAINING.md:121-128 P1.17, the base part, re-verified at c96facd: bar's base is 0, not twoway's rule; when 0 is outside the data, area, bar, spike and dropline draw from 0 and extend the axis to it. On a date axis that default base is 01jan1970, not 01jan1960 (the default-base half of P1.23's base bullet). Sources: GAPS2-A3-c, GAPS2-A3-f, AUDIT-42.
  - Suggested fix: WP-30 section 27 (twoway's default base and axis extent): draw bar, area, spike and dropline from twoway's default base clamped into the finished scale, keeping a default base out of the axis range, in both modes and after every move.
  - Resolution: Not fixed because WP-30 section 27 has not landed. Graded S1 (WP-30): silently different bars: every length is drawn from another base, and the axis is stretched to 0.

- [ ] Title: The axis look sub-options nolabels, noticks, off, noline, line colour, width and pattern, alt, titlegap, labcolor, tlength and tposition are not honoured, and anglestyle names are dropped silently
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_parse_axis_spec (22602), _parse_axis_angle (4998), _DASH_ANGLESTYLES (4953), _dash_apply_tick_option (22882), _dash_apply_axis_spec (22714)
  - Description: DROPIN-REMAINING.md:129 P1.18, the look part, re-verified at c96facd: `nolabels`, `noticks`, `xscale(off)`, `noline`, axis line colour, width and pattern, `alt` and `titlegap` are not honoured; `angle(rvertical)`, `angle(stacked)` and other anglestyle names are dropped silently; `labcolor`, `tlength` and `tposition` are not honoured. Also measured: `angle(Vertical)` and `angle(400)` are accepted, and sub-options are read from label text. Sources: GAPS2-B21-c, REM-09-02-NOLABELS-NOTICKS, REM-09-02-SCALE-OFF, REM-09-02-SCALE-LINE, REM-09-02-SCALE-TITLEGAP, GAPS2-B23-b, GAPS2-B23-c, GAPS2-B23-d, GAPS2-B23-e, GAPS2-B23-f, REM-09-02-LABEL-ANGLE, GAPS2-D9-a, REM-09-02-LABEL-LABCOLOR, REM-09-02-LABEL-TICKGEOM, GAPS2-B21-e, AUDIT-28.
  - Suggested fix: WP-30 section 31 (Axis look sub-options): honour each axis look sub-option and every anglestyle name on both axes in both modes, refusing what twoway refuses and staying silent under by() where twoway is (maintainer decisions M5 and M6).
  - Resolution: Not fixed because WP-30 section 31 has not landed. Graded S2 (WP-30): accepted axis sub-options are named and not drawn.

- [ ] Title: The add sub-option replaces the default ticks instead of adding to them, and an axis(2) add is named and not drawn
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_apply_tick_option (22882), _dash_count_ticker (22176); dash.ado at c96facd: _dash_axis_expand (2537); dash_parse.mata at c96facd: _dash_rep_merge (5715)
  - Description: DROPIN-REMAINING.md:129 P1.18, the add part, re-verified at c96facd: `add` is not honoured; it replaces the default ticks instead of adding to them. (WP-29 note: add on an axis(2)-routed label is named, not drawn.) Also measured: a repeated add is lost in the Mata merge, and dash.ado expands an a(b)c rule before the renderer, losing what add needs. Sources: REM-09-02-LABEL-ADD, GAPS2-B21-f.
  - Suggested fix: WP-30 section 52 (The add sub-option): add a rule's ticks to the default ticks, keep them through every re-finish after a move, and draw an axis(2) add, in both modes.
  - Resolution: Not fixed because WP-30 section 52 has not landed. Graded S1 (WP-30): silently wrong ticks: the axis loses its default labels.

- [ ] Title: Sub-option abbreviations such as legend(c(2) posi(6)), ylabel(, labs(small)) and xline(5, lc(red)) are not recognised
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_legend_parts (21252), _dash_apply_legend (21400), _dash_parse_axis_spec (22602), _dash_refline_instances (26268), _TEXTBOX_SUBOPTS (4639), _dash_apply_z_options (26106)
  - Description: DROPIN-REMAINING.md:130 P1.19, re-verified at c96facd: sub-option abbreviations are not recognised. This covers legend `c()`, `r()`, `lab()` and `posi()`; axis `labs()`, `glc()` and similar; and xline's `lc()`, `lp()` and `lw()`. Sources: GAPS2-B17-a, GAPS2-B21-d, REM-09-02-LABSIZE-ABBREV, GAPS2-B22-b.
  - Suggested fix: WP-30 section 10 (Sub-option abbreviations): read legend, axis, reference-line and textbox sub-options by twoway's abbreviations through shared tables in both modes, refusing a capitalised sub-option as twoway does (maintainer decision M5).
  - Resolution: Not fixed because WP-30 section 10 has not landed. Graded S2 (WP-30): twoway's abbreviations are not read.

- [ ] Title: plotregion() and graphregion() styling sub-options such as style(none), lcolor(), lwidth(), fc() and lc() are dropped with no note
  - File Names and Line Numbers: dash_render.py at c96facd: _extract_region_color (5048), _extract_region_lcolor (5058), _extract_region_lwidth (5065), _dash_graph_color (15407); dash.sthlp:2717-2721 (Region Styling Options)
  - Description: DROPIN-REMAINING.md:131 P1.20, the styling part, re-verified at c96facd: `style(none)`, graphregion `lcolor`/`lwidth`, the `i*` options and the abbreviations `fc()`/`lc()` have no effect, and nothing is reported. Also measured: color() sets only the fill where twoway sets fill and outline, colour none paints black, %NN opacity, lpattern() and lstyle(none) are dropped, and repeated copies are not merged. Sources: GAPS2-B18-b, GAPS2-B18-c, GAPS2-B18-d, GAPS2-B18-e, GAPS2-B18-f, AUDIT-66 (styling).
  - Suggested fix: WP-30 section 38 (plotregion()/graphregion() styling): read every region sub-option and its abbreviations, draw what twoway draws with twoway's bgcolor() semantics and name the rest in one note, refusing what twoway refuses, in both modes.
  - Resolution: Not fixed because WP-30 section 38 has not landed. Graded S1 (WP-30): options the user gave are dropped without a note.

- [ ] Title: plotregion(margin()) and graphregion(margin()) have no effect and no note, and the plot region's inner box is not drawn
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_padded_range (23489), _dash_apply_scale_ranges (26051); scripts/extract_scheme_truth.py
  - Description: DROPIN-REMAINING.md:131 P1.20, the margin part, re-verified at c96facd: `margin()` has no effect, and nothing is reported, in plotregion() and graphregion() alike. Sources: GAPS2-B18-a, AUDIT-66 (margins).
  - Suggested fix: WP-30 section 47 (Plot-region margin and inner box): honour plotregion(margin()) through twoway's plot-region margin and draw the inner box, naming graphregion margins, in both modes and after every move.
  - Resolution: Not fixed because WP-30 section 47 has not landed. Graded S1 (WP-30): an option the user gave is dropped without a note.

- [ ] Title: xline() and yline() numlists such as xline(2000(500)3000) draw nothing, and lstyle() and lalign() are only named
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_reference_lines (26224), _dash_refline_instances (26268), _dash_refline_draw (26327); dash.ado at c96facd: _dash_parse_graph_opts (682)
  - Description: DROPIN-REMAINING.md:132 P1.21, the positions and lstyle part, re-verified at c96facd: numlists such as `xline(2000(500)3000)` draw nothing (the note names them); `lstyle` and `lalign` are only named. Also measured: dash accepts positions twoway refuses, keeps duplicate lines, and adds lines one at a time. Sources: GAPS2-B22-a, GAPS2-B22-d (lstyle), AUDIT-64.
  - Suggested fix: WP-30 section 39 (xline/yline positions, refusals and lstyle): expand numlist positions, refuse in twoway's order what twoway refuses, and draw lstyle() through the style bundle, in both modes.
  - Resolution: Not fixed because WP-30 section 39 has not landed. Graded S2 (WP-30): accepted twoway positions are named and not drawn.

- [ ] Title: xline() and yline() noextend, extend and style() are only named, so every line spans the whole frame
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_refline_draw (26327), _dash_reference_lines (26224); scripts/extract_scheme_truth.py
  - Description: DROPIN-REMAINING.md:132 P1.21, the extent part, re-verified at c96facd: `noextend` is only named, as is `style()`, so every line spans the frame where twoway insets it by the plot-region margin. Sources: GAPS2-B22-e, GAPS2-B22-d (style()).
  - Suggested fix: WP-30 section 50 (xline/yline extend, noextend and style()): draw extend, noextend and style() with the scheme's extend keys over the axis hull, re-finished after every move in both modes.
  - Resolution: Not fixed because WP-30 section 50 has not landed. Graded S2 (WP-30): accepted sub-options are named and not drawn.

- [ ] Title: The points-free function fallback knows ten functions and draws any other in silence
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper.map_function (14854), _stata_fn_eval (28877), _dash_note_empty_layer (28349); dash.sthlp:413-418
  - Description: DROPIN-REMAINING.md:133 P1.22, re-verified at c96facd: `function` evaluates only 10 functions; `normalden`, `normal`, `ln`, `_pi`, `c(pi)`, comparisons, `cond`, `min`, `max`, `round`, `int`, `scalar()` and `_b[]` all draw nothing. (WP-29 note: P0.6 evaluates every function layer of a Stata-built spec with Stata's own generator, which closes these sources there; the points-free fallback still knows ten functions.) Sources: GAPS2-A6-a, GAPS2-A6-b, GAPS2-C5-a, GAPS2-C5-b, GAPS2-C5-c, GAPS2-C5-d, GAPS2-C5-e, GAPS2-C5-f, AUDIT-53.
  - Suggested fix: WP-30 section 26 (function: closed by disposition): keep the ten-function fallback and give any other function it meets one note naming the function and the remedy, in both modes (maintainer decision M12).
  - Resolution: Not fixed because WP-30 section 26 has not landed. Graded S3 (WP-30): only a spec built outside Stata reaches the fallback, and it draws nothing in silence.

- [ ] Title: Dates on range, pc, immediate and second axes are drawn at raw or millisecond positions, and a date layer beside a numeric one is drawn in epoch milliseconds
  - File Names and Line Numbers: dash_render.py at c96facd: _dash_figure_date_kind (788), _dash_axis_vars (821), _dash_axis_date_kind (841), GlyphMapper._on_axis (10646), GlyphMapper.map_scatteri (13627), GlyphMapper.map_function (14854), _dash_secondary_values (23117), _dash_count_axes (23345)
  - Description: DROPIN-REMAINING.md:134-144 P1.23, the positions part, re-verified at c96facd: scatteri/pci/pcarrowi coordinates and `function range()` are drawn at raw SIF values (1970); range and pc plots with date y get no date axis; a layer on `yaxis(2)`/`xaxis(2)` turns the primary date axis numeric, and the secondary date axis shows epoch ms; a date layer beside a numeric layer on one axis is drawn at epoch ms with no warning (and xlabel(minmax) there reads epoch ms, WP-29 S04/S05 note); base 0 is 1970, not 1960. Sources, matched by content to REMAINING.md:1935-2110 (section 08-04): REM-08-04-C7, REM-08-04-C7b, REM-08-04-C3b, REM-08-04-C3c, REM-08-04-C4, REM-08-04-B2b, REM-08-04-B7a, REM-08-04-B4.
  - Suggested fix: WP-30 section 35 (Date positions on every axis): place every date in Stata units on the axis it is drawn on, primary or secondary, for range, pc and immediate types and mixed axes, in both modes and after a filter move.
  - Resolution: Not fixed because WP-30 section 35 has not landed. Graded S1 (WP-30): silently wrong positions: dates drawn near 1970 or in milliseconds.

- [ ] Title: A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, and the histogram tooltip always says Count
  - File Names and Line Numbers: dash_render.py at c96facd: GlyphMapper._apply_colorvar (8887), _dash_colorvar_cuts (7724), _dash_colorvar_bins (7768), _dash_apply_z_options (26106), _dash_build_hover (27118), GlyphMapper.map_histogram (12451)
  - Description: DROPIN-REMAINING.md:134-144 P1.23, the text part, re-verified at c96facd: a date `colorvar` key shows ms (colorcuts() on a date are read as ms too); fallback tooltips ignore formats; the histogram tooltip always says "Count". Sources, matched by content to REMAINING.md:2111-2290 (section 08-05): REM-08-05-M1, REM-08-05-C7c, REM-08-05-C10, REM-08-05-M2.
  - Suggested fix: WP-30 section 17 (Date and format text in keys and tooltips): read a date colour key, its ticks and cuts in Stata units, show fallback tooltips in the variable's display format, and name the histogram's measure, in both modes and after a filter move.
  - Resolution: Not fixed because WP-30 section 17 has not landed. Graded S1 (WP-30): silently wrong numbers in keys and tooltips.

- [ ] Title: mlabvposition(varname) and mlabtextstyle() are declared and pending but never serialised or drawn
  - File Names and Line Numbers: dash.ado at c96facd: _dash_parse_plot_opts (897; MLABVposition at 957, the pending entry at 1079), _dash_plot_opts_to_json (3131); dash_parse.mata at c96facd: _dash_extract_vars (2229); dash_render.py at c96facd: GlyphMapper._apply_mlabel_opts (9302)
  - Description: DROPIN-REMAINING.md:145 P1.24, re-verified at c96facd: `mlabvposition(varname)` is not drawn. It and `mlabtextstyle` are declared and pending but never serialised, and no test checks that declared options reach the spec. Sources: REM-§2-S09-mlabvpos, REM-S09-73-mlabpos, REM-05-04-S09-r, GAPS2-A4-p, GAPS2-B27-c, AUDIT-33, REM-05-04-B6.
  - Suggested fix: WP-30 section 37 (mlabvposition() and mlabtextstyle()): serialise and draw mlabvposition(varname) per row and mlabtextstyle() from the scheme's textbox styles, refusing what twoway refuses, in both modes and after filter moves.
  - Resolution: Not fixed because WP-30 section 37 has not landed. Graded S2 (WP-30): accepted twoway options are named and not drawn.

- [ ] Title: Six StataCorp schemes, among them meta and stcolor_mv, are refused r(198) where twoway draws them
  - File Names and Line Numbers: dash.ado at c96facd: _dash_shipped_schemes (1967); dash_render.py at c96facd: SchemeParser._BUILTIN_NAMES (5704); scripts/extract_scheme_truth.py; dash.pkg
  - Description: DROPIN-REMAINING.md:146 P1.25, the shipped-schemes part, re-verified at c96facd: six StataCorp schemes, including meta and stcolor_mv, are refused r(198) where twoway draws them, and an inherited `c(scheme)` naming one of them is drawn as s2color. Sources: GAPS2-X5-c (the six-scheme part; the refusal has no source id of its own).
  - Suggested fix: WP-30 section 07 (Ship the six StataCorp schemes): ship meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv, transcribed from Stata 19.5 as the other twenty are.
  - Resolution: Not fixed because WP-30 section 07 has not landed. Graded S2 (WP-30): schemes twoway draws are refused.

- [ ] Title: scheme(NAME) is looked for in two places only, never along Stata's ado-path or under Stata's scheme-NAME.scheme file name, and its refusal does not list the valid names
  - File Names and Line Numbers: dash.ado at c96facd: _dash_validate_value (2125; the scheme check), _dash_shipped_schemes (1967); dash_render.py at c96facd: SchemeParser.resolve_or_fallback (5844), SchemeParser._include (6389), SchemeParser._parse_file (6198)
  - Description: DROPIN-REMAINING.md:146 P1.25, the lookup part, re-verified at c96facd: `scheme(NAME)` never tries Stata's own `scheme-NAME.scheme` file name. An inherited `c(scheme)` that Stata found is drawn as s2color. `#include` has the same limits. The error message does not list the valid names. Also measured: a working-directory file overrides a StataCorp name, the reverse of twoway, and the help's remedy fails. Sources: REM-§3-f, GAPS2-X5-a, GAPS2-X5-c, GAPS2-X5-d, REM-§3-e.
  - Suggested fix: WP-30 section 34 (Stata's scheme lookup along the ado-path): resolve scheme(NAME), an inherited c(scheme) and #include along Stata's whole ado-path under both file names, with name, containment, regular-file and size guards, parsing scheme files as data and never running them (maintainer decision M7).
  - Resolution: Not fixed because WP-30 section 34 has not landed. Graded S2 (WP-30): schemes Stata finds are refused or drawn as s2color.

- [ ] Title: Notes print as raw Python warnings with internal paths, a warnings filter of ignore hides them, and one of error turns a note into r(7102)
  - File Names and Line Numbers: dash_render.py at c96facd: main (36823), _dash_warn_once (15363); dash.ado at c96facd: _dash_process_segment (3454), _dash_report_ignored (4951), _dash_render_immediate (6432), _dash_build (8072); dash_parse.mata at c96facd: _dash_say (676)
  - Description: DROPIN-REMAINING.md:147-153 P1.26, the channel part, re-verified at c96facd: notes print as raw UserWarnings with internal paths; a session `warnings` filter of "ignore" silences them; one of "error" turns a note into r(7102). Also measured: dash.ado's own notes are hidden by quietly while the renderer's survive it. Sources: GAPS2-X4-a, GAPS2-X4-b, GAPS2-X4-c, GAPS2-X4-d, GAPS2-I-sum-logging.
  - Suggested fix: WP-30 section 06 (One note channel): print every note through one SMCL-escaped channel in twoway's (note: ...) form, unaffected by the session's warnings filters, shown under quietly and hidden by capture as twoway's notes are.
  - Resolution: Not fixed because WP-30 section 06 has not landed. Graded S2 (WP-30): notes fail visibly: raw warnings, hidden notes and a note turned into an error.

- [ ] Title: dash build, server and dash serve report no option or empty-layer notes, and the served child's stderr never reaches Stata
  - File Names and Line Numbers: dash_render.py at c96facd: ServerAppBuilder._generate_app_source (33915), _dash_launch_app (37206), _dash_note_empty_layer (28349), DashRenderer._make_figure_body (30203)
  - Description: DROPIN-REMAINING.md:147-153 P1.26, the served part, re-verified at c96facd: `dash build, server` reports no option or empty-layer notes; the served child's stderr never reaches Stata. (WP-29 note: the served app prints no empty-layer note where the saved page notes "drew nothing"; under maintainer decision M6 a layer whose own if/in keeps no row is silent in both modes, as in twoway.) Sources: GAPS2-F5a, GAPS2-F5b, GAPS2-F5c (closed at c96facd).
  - Suggested fix: WP-30 section 23 (Served notes reach Stata): run a trial render at build for dash build, server, relay the served child's notes redacted and bounded, and keep an empty own-if layer silent in both modes (maintainer decision M6).
  - Resolution: Not fixed because WP-30 section 23 has not landed. Graded S2 (WP-30): the served route drops the notes the saved route prints.

- [ ] Title: The drop-in command form fails: a twoway prefix is refused, saving(name, asis) writes a file named after the whole argument, dash build, saving(f, replace) is refused, and batch mode opens a browser
  - File Names and Line Numbers: dash.ado at c96facd: dash (84), _dash_browser_wanted (5696), _dash_dashboard_browser (5739), _dash_open_page (5781), _dash_build (8072); dash_render.py at c96facd: _validate_output_path (36678)
  - Description: DROPIN-REMAINING.md:154-161 P1.27, re-verified at c96facd: `set graphics off` and batch mode still open a browser; a `twoway`/`tw`/`graph twoway` prefix is refused; `saving(n, asis)` writes a file literally named "n, asis.html"; `dash build, saving(f, replace)` is refused; `..` and `&` in a saving path are refused where twoway accepts them. Sources: CRIT-04, CRIT-02, CRIT-03, CRIT-09, GAPS2-I14-a, GAPS2-I14-b.
  - Suggested fix: WP-30 section 12 (Drop-in command form and saving() grammar): accept the twoway prefixes and one saving() grammar on every route, open no browser in batch mode or under set graphics off, and accept the path characters twoway accepts while keeping the sink checks (maintainer decisions M5 and M11).
  - Resolution: Not fixed because WP-30 section 12 has not landed. Graded S2 (WP-30): twoway's command forms are refused or misread.

- [ ] Title: dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph
  - File Names and Line Numbers: dash.ado at c96facd: dash (84; not rclass), _dash_render_immediate (6432), _dash_build (8072)
  - Description: DROPIN-REMAINING.md:162 P1.28, the Stata part, re-verified at c96facd: `graph export` after dash fails r(601), or silently exports a stale earlier graph. There is no `r(filename)`. Also measured: saving(x.png) silently writes x.png.html. Sources: GAPS2-J7-a, GAPS2-J7-c, GAPS2-J7-b (documented); GAPS2-E10c (a scripted export) waits for the deferred platform package (maintainer decision M8).
  - Suggested fix: WP-30 section 22 (r(filename) and the stale-graph note): make dash rclass with r(filename), note once when graph export would write an older Stata graph, and document what graph export can and cannot do after dash (maintainer decision M8).
  - Resolution: Not fixed because WP-30 section 22 has not landed. Graded S2 (WP-30): a twoway companion fails or exports the wrong graph.

- [ ] Title: Neither mode offers a vector export: the toolbar saves only a PNG at the screen's resolution
  - File Names and Line Numbers: dash_render.py at c96facd: _DASH_FIGURE_TOOLS (24418), _dash_save_filename (24431), _dash_name_save (24445)
  - Description: DROPIN-REMAINING.md:162 P1.28, the SVG part, re-verified at c96facd: there is no SVG backend; figures are canvas or webgl only, and the only image is the toolbar's PNG at device-pixel resolution. Sources: GAPS2-E10b.
  - Suggested fix: WP-30 section 54 (Client-side Save as SVG): add one Save as SVG toolbar action to every dashboard in both modes, running under the page's hashed or nonced policy (maintainer decision M8).
  - Resolution: Not fixed because WP-30 section 54 has not landed. Graded S3 (WP-30): a missing export format; the PNG save works.

- [ ] Title: Both content security policies allow inline scripts, and percent and exclamation signs in a saving path reach the Windows shell
  - File Names and Line Numbers: dash_render.py at c96facd: _DASH_CSP_SERVED (3699), _dash_csp_meta (3722), _dash_served_template (3756), _render_bootstrap_html (30857); dash.ado at c96facd: _dash_open_page (5781)
  - Description: DROPIN-REMAINING.md:163 P1.29, re-verified at c96facd: both CSPs keep `unsafe-inline`; they need hashes or a nonce, plus a browser test. `%` and `!` in saving paths reach Windows `start` via cmd.exe; whether they expand there is unmeasured on Windows. The help does not state saving()'s character rule. Sources: GAPS2-I12-a, GAPS2-I12-b, GAPS2-I12-c, GAPS2-I14-c, GAPS2-I14-d.
  - Suggested fix: WP-30 section 04 (CSP without 'unsafe-inline'; safe Windows opener): hash every inline script of the saved page and nonce the served one, prove the policy in a browser in both modes, and open no path holding a cmd metacharacter on Windows (maintainer decision M11).
  - Resolution: Not fixed because WP-30 section 04 has not landed. Graded S2 (WP-30): an injected inline script is not blocked by the policy, and user path text reaches cmd.exe.

- [ ] Title: The bokeh dependency has no ceiling or run-time version check, and the Bokeh internals dash's security relies on are not checked
  - File Names and Line Numbers: dash_setup.ado at c96facd: dash_setup (19; its package list at 285); dash_render.py at c96facd: _dash_strict_match_host (3836), _dash_served_template (3756)
  - Description: DROPIN-REMAINING.md:164 P1.30, re-verified at c96facd: there is no bokeh ceiling and no run-time `bokeh.__version__` check. The text-sink XSS safety is verified only on 3.8 and 3.9. The setup gate never reports "outside the verified range". dash also depends on Bokeh internals (`match_host`, `templates.FILE`). (WP-29 note: dash_setup does no hash-pinned installs.) Sources: GAPS2-H4b, GAPS2-H4c, GAPS2-H4d, GAPS2-H4e, GAPS2-I7-a, GAPS2-I7-b, GAPS2-K5-a, GAPS2-K5-b, GAPS2-K5-c.
  - Suggested fix: WP-30 section 41 (Verified bokeh window; internals fail closed): install and check bokeh inside one verified window, note above it and refuse below it at run time, and refuse to serve when the Bokeh internals dash relies on change (maintainer decisions M9 and M10).
  - Resolution: Not fixed because WP-30 section 41 has not landed. Graded S2 (WP-30): an unverified Bokeh release is installed and run with no word.

- [ ] Title: The served app has no session cap or idle lifetime and decodes the whole dataset again for every session
  - File Names and Line Numbers: dash_render.py at c96facd: main (36823; its argparse flags), ServerAppBuilder._generate_app_source (33915), _dash_launch_app (37206); dash.ado at c96facd: _dash_serve (8369)
  - Description: DROPIN-REMAINING.md:165 P1.31, the capacity part, re-verified at c96facd: there is no concurrent-session cap and no unused-session lifetime. Each session re-decodes the whole dataset. Sources: GAPS2-F3a, GAPS2-F3b, GAPS2-F3c, GAPS2-I4-a, GAPS2-I4-b, GAPS2-G14-d.
  - Suggested fix: WP-30 section 46 (Served session capacity and memory): decode the data once per process, cap concurrent sessions with a busy page and close idle sessions, set from dash serve and dash build, server.
  - Resolution: Not fixed because WP-30 section 46 has not landed. Graded S2 (WP-30): a served app can be exhausted by open sessions.

- [ ] Title: One reader's filter-move recompute blocks the served event loop for every other reader
  - File Names and Line Numbers: dash_render.py at c96facd: ServerAppBuilder._generate_app_source (33915; the generated _dash_redraw_for at 35039 and _on_filter_change at 35854), _dash_event_throttle (24330)
  - Description: DROPIN-REMAINING.md:165 P1.31, the recompute part, re-verified at c96facd: one event loop is blocked by recomputes: lowess takes 27.7 s at N=100k (lpolyci's 8.7 s was closed by WP-29 P0.9). Sources: GAPS2-F3d, GAPS2-C-intro-served-cost.
  - Suggested fix: WP-30 section 57 (Served recompute off the event loop): run filter-move recomputes on a worker thread, apply results on the next tick and drop stale ones, after a thread-safety audit of the final served move path.
  - Resolution: Not fixed because WP-30 section 57 has not landed. Graded S2 (WP-30): one slow recompute freezes every session.

- [ ] Title: A missing numpy, pandas or bokeh or an old Python fails with a bare ModuleNotFoundError or SyntaxError, and dash_setup's first Python call is uncaptured
  - File Names and Line Numbers: dash_render.py at c96facd: the import block (82-118); dash.ado at c96facd: _dash_require_python (206), _dash_do_render (402), _dash_xm_load (4576); dash_setup.ado at c96facd: dash_setup (19; its first python: call at 92)
  - Description: DROPIN-REMAINING.md:166 P1.32, re-verified at c96facd: a missing numpy, pandas or bokeh gives a bare ModuleNotFoundError. An old Python gives a SyntaxError. `dash_setup`'s first Python call is uncaptured. Sources: GAPS2-H6a, GAPS2-H6b, GAPS2-H6c, GAPS2-H6d.
  - Suggested fix: WP-30 section 25 (Render-time dependency guards): guard the renderer's imports and the generated app's header with one message naming dash_setup, check the packages from Stata before rendering, and capture dash_setup's first Python call.
  - Resolution: Not fixed because WP-30 section 25 has not landed. Graded S2 (WP-30): a missing dependency fails with an internal error.

- [ ] Title: The Python floor of 3.13 turns away 3.11 and 3.12 users, and dash_setup reports failure although dash may render
  - File Names and Line Numbers: dash_setup.ado at c96facd: _dash_pymin (489), _dash_setup_summary (672); dash.ado at c96facd: _dash_require_python (206); dash.pkg (Requires)
  - Description: DROPIN-REMAINING.md:167 P1.33, re-verified at c96facd: the Python floor of 3.13 excludes 3.11/3.12 users. Setup reports failure although dash may still render. Sources: GAPS2-H4g.
  - Suggested fix: WP-30 section 05 (Measured Python floor): run both test suites under Python 3.11 and 3.12 in scratch environments and lower the declared floor to the lowest version that passes (maintainer decisions M3 and M10).
  - Resolution: Not fixed because WP-30 section 05 has not landed. Graded S2 (WP-30): a supported Python is turned away.

- [ ] Title: The certification runners hard-code arch -arm64 and the maintainer's paths, so they run on no other machine
  - File Names and Line Numbers: scripts/stata_slot.sh:10, scripts/run_cert_suite.sh:17, scripts/run_release_gate.sh:34 and 42, scripts/stata_python_exec.sh:17, test/run_all_cscripts.do:4-6, scripts/regen_option_surface.py:17, scripts/wire_option_reporting.py:9, and the extractors under scripts/ that repeat them
  - Description: DROPIN-REMAINING.md:168 P1.34, re-verified at c96facd: Windows, Linux, Intel Mac and GUI Stata are untested. `arch -arm64` and the maintainer's path are hard-coded in the runners. Whether anything actually breaks is unclear. Under maintainer decision M4 WP-30 makes the runners portable only, and measuring other platforms moves to a later package. Sources: GAPS2-K1-a, GAPS2-K1-b; GAPS2-H-intro-platforms and GAPS2-H-intro-gui (deferred).
  - Suggested fix: WP-30 section 02 (Portable runners): give every runner and extractor one Stata-invocation rule with no hard-coded architecture prefix or maintainer path, choosing the prefix from the binary itself (maintainer decision M4).
  - Resolution: Not fixed because WP-30 section 02 has not landed. Graded S3 (WP-30): test runners only; no user's output changes.

- [ ] Title: dash declares Stata 16.0, but only StataNow 19.5 has ever run it or made its truth fixtures
  - File Names and Line Numbers: dash.ado at c96facd: dash (84-85) and the other version 16.0 statements (79 in the file); dash_setup.ado at c96facd: its 12 version 16.0 statements, _dash_pymin (489); dash.pkg; scripts/wire_option_reporting.py
  - Description: DROPIN-REMAINING.md:169 P1.35, re-verified at c96facd: `version 16.0` is declared, but only StataNow 19.5 is ever run. Every truth fixture is also 19.5-only. Sources: GAPS2-H-intro-stataver, GAPS2-J8-e, GAPS2-K3-d.
  - Suggested fix: WP-30 section 03 (Stata 19 floor declared and enforced): declare version 19 in every program and refuse an older Stata with one clear message (maintainer decision M2).
  - Resolution: Not fixed because WP-30 section 03 has not landed. Graded S2 (WP-30): a Stata 16 to 18.5 user meets an unmeasured failure instead of a clear refusal.
~~~~

## Appendix C: code and text blocks (read by `s01_apply.py` by name)

**`tracking-readers`** (01-02; inserted above `class TestWp30Tracking`, the three `@@...@@` lines replaced by the constants `s01_apply.py` builds from Appendices A and B).

~~~~python tracking-readers
# ===========================================================================
# WP-30's P1 entries (item 9 of the module docstring)
# ===========================================================================

#: WP-30 (.ultraplan/wp30/index.md, decision A144): the BUGS.md entries the
#: tracking foundation (S01) opened, one per fix section (S02-S57), by id,
#: with their exact titles, one key per line in entry order.  Each stays open
#: until its section lands; that section's closing commit closes the entry in
#: place and deletes its own key line here.  test_no_open_entry_is_s1_or_s2
#: skips exactly these titles (and WP29_OPEN's), and TestWp30Tracking fails
#: on a key whose entry is missing, closed or not in the WP-30 open form, so
#: the allowance cannot outlive its reason.  The closeout (S58.1) leaves it {}.
@@WP30_OPEN@@

#: Every WP-30 entry, permanently, and the CHANGELOG.md lists of the current
#: release its line belongs in (index.md "P1 coverage").  S01 put one
#: ``<!-- WP-30 <id> -->`` marker in each; the closing commit replaces each
#: marker in place with a line ending ``(WP-30, <id>)``.  A section that
#: needs another list edits its own row and its own markers in the same
#: commit (index.md R4).
@@WP30_LISTS@@

#: The section that closes each entry (index.md "Section manifest"); an open
#: entry's Resolution names it.  Permanent.
@@WP30_SECTION@@

#: The 56 ids, in entry order.
WP30_ALL = tuple(WP30_LISTS)

_WP30_MARKER = re.compile(r"<!-- WP-30 (P1\.\d{1,2}[abc]?) -->")
_WP30_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-30 section (\d{2}) has not landed\."
    r" Graded S[1-3] \(WP-30\): \S")


def _wp30_markers(text):
    """The ids of every ``<!-- WP-30 <id> -->`` marker in *text*, in order,
    repeats kept."""
    return _WP30_MARKER.findall(text)


def _wp30_open_problems(open_map, entries):
    """What is wrong with the allowance *open_map* ({id: title}) against the
    BUGS.md *entries*: an id WP-30 lacks, a title with a double quote or
    shared by two ids, a title no entry or two entries carry, an entry that
    is closed (the allowance is stale), one not in the WP-30 open form, or
    one whose Resolution names another section than WP30_SECTION's."""
    bad = []
    unknown = sorted(set(open_map) - set(WP30_ALL))
    if unknown:
        bad.append("ids WP-30 does not have: %s" % unknown)
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
            bad.append("%s: %r is closed; delete its WP30_OPEN key"
                       % (pid, title))
            continue
        form = _WP30_OPEN_FORM.match(e["fields"].get("Resolution", ""))
        if not form:
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-30 "
                       "section NN has not landed. Graded S1|S2|S3 (WP-30): "
                       "...'" % (pid, title))
        elif int(form.group(1)) != WP30_SECTION.get(pid):
            bad.append("%s: its Resolution names section %s, not %s"
                       % (pid, form.group(1), WP30_SECTION.get(pid)))
    return bad


def _wp30_marker_problems(open_ids, markers):
    """A marker naming no WP-30 id, and an open id with no marker left."""
    bad = ["a marker names %s, which WP-30 does not have" % m
           for m in sorted(set(markers) - set(WP30_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP30_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp30_closure_problems(open_ids, markers, entries):
    """A closed id (in WP30_ALL, not open) whose marker is still in the
    CHANGELOG, or whose (WP-30, <id>) no closed entry's Resolution holds."""
    bad = []
    for pid in WP30_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-30, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp30_list_problems(lists_map, changelog):
    """Each id's marker or its (WP-30, <id>) line must sit in every list
    *lists_map* names for it, and neither its marker nor such a line
    anywhere else (a section that needs another list widens its own row
    first, index.md R4)."""
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-30 %s -->" % pid, "(WP-30, %s)" % pid
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
~~~~

**`tracking-class`** (01-01; appended at the end of `test/test_tracking_documents.py`).

~~~~python tracking-class
class TestWp30Tracking:
    """WP-30's 56 P1 entries (index.md A144): open in BUGS.md, naming their
    section, with a marker in each CHANGELOG list they belong to until their
    section lands, then closed with no marker left and a Resolution naming
    (WP-30, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        bad = _wp30_open_problems(WP30_OPEN, entries)
        assert not bad, "\n".join(bad)

    def test_an_open_p1_keeps_its_marker(self):
        bad = _wp30_marker_problems(
            set(WP30_OPEN), _wp30_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_p1_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp30_closure_problems(
            set(WP30_OPEN), set(_wp30_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_p1_sits_in_its_changelog_lists(self):
        assert WP30_ALL == tuple(WP30_LISTS) and len(WP30_ALL) == 56
        assert tuple(WP30_SECTION) == WP30_ALL
        assert sorted(WP30_SECTION.values()) == list(range(2, 58))
        bad = _wp30_list_problems(WP30_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("# Changelog\n\n## 1.0, 01jan2027\n\nintro\n\n"
                "### Results that change\n\n- a line. (WP-30, P1.2a)\n"
                "<!-- WP-30 P1.1a -->\n\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-30 P1.1a -->\n<!-- WP-30 P1.15c -->\n\n"
                "### Fixed in WP-30\n\n<!-- WP-30 P1.19 -->\n\n"
                "## 0.9, 01jan2026\n\n### Results that change\n\n"
                "<!-- WP-30 P1.99 -->\n")
        assert _wp30_markers(text) == ["P1.1a", "P1.1a", "P1.15c", "P1.19",
                                       "P1.99"]
        assert _wp30_markers("<!-- WP-29 P0.1 --> <!-- WP-30 P1.1a-->"
                             " <!-- WP-30 P1.1d -->") == []
        lists = _changelog_lists(text)
        assert list(lists) == [
            "Results that change",
            "Changed behaviour (may need your do-files changed)",
            "Fixed in WP-30"]
        assert "P1.99" not in "".join(lists.values())
        assert _changelog_list(lists, "Changed behaviour").startswith(
            "\n\n<!-- WP-30 P1.1a -->")
        assert _changelog_list(lists, "Security") is None

    def test_the_wp30_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-30 section 11 has not landed. "
                     "Graded S2 (WP-30): wrong style.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01nov2026 (WP-30, P1.2a). Done.")]
        assert _wp30_open_problems({"P1.1a": "T1"}, good) == []
        for open_map, entries, says in (
                ({"P1.1a": "T2"}, good, "is closed"),
                ({"P1.1a": "T9"}, good, "0 BUGS.md entries"),
                ({"P1.1a": "T1"}, good + [entry("T1", False, open_form)],
                 "2 BUGS.md entries"),
                ({"P1.1a": "T1"},
                 [entry("T1", False, "Not fixed because x. Graded S3 "
                        "(WP-27): y.")], "not 'Not fixed because WP-30"),
                ({"P1.1a": "T1"},
                 [entry("T1", False, open_form.replace("11", "12"))],
                 "names section 12, not 11"),
                ({"P1.99": "T1"}, good, "does not have"),
                ({"P1.1a": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote"),
                ({"P1.1a": "T1", "P1.1b": "T1"}, good, "share one title")):
            bad = _wp30_open_problems(open_map, entries)
            assert any(says in b for b in bad), (says, bad)

        assert _wp30_marker_problems({"P1.1a"}, ["P1.1a"]) == []
        assert _wp30_marker_problems({"P1.1a"}, []) == [
            "P1.1a is open and CHANGELOG.md holds no marker for it"]
        assert _wp30_marker_problems(set(), ["P1.1"]) == [
            "a marker names P1.1, which WP-30 does not have"]

        others = set(WP30_ALL) - {"P1.2a"}
        assert _wp30_closure_problems(others, others, good) == []
        assert _wp30_closure_problems(others, others | {"P1.2a"}, good) == [
            "P1.2a is closed and CHANGELOG.md still holds its marker"]
        assert _wp30_closure_problems(others, others, good[:1]) == [
            "P1.2a is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-30, P1.2a)"]
        # (WP-30, P1.1a) is not read inside (WP-30, P1.11a) or (WP-30, P1.1b)
        near = [entry("T3", True, "Fixed (WP-30, P1.11a). (WP-30, P1.1b).")]
        assert _wp30_closure_problems(set(WP30_ALL) - {"P1.1a"}, set(),
                                      near) == [
            "P1.1a is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-30, P1.1a)"]

        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-30 P1.1a -->\n"
               "### Changed behaviour (may need your do-files changed)\n\n"
               "- a line. (WP-30, P1.1a)\n### Security\n\n"
               "<!-- WP-30 P1.29 -->\n")
        rules = {"P1.1a": ("Results that change", "Changed behaviour"),
                 "P1.29": ("Security",)}
        assert _wp30_list_problems(rules, log) == []
        assert _wp30_list_problems(
            {"P1.1a": ("Results that change", "Changed behaviour"),
             "P1.29": ("Results that change",)}, log) == [
            "P1.29: '### Results that change' holds neither its marker nor "
            "a line ending (WP-30, P1.29)",
            "P1.29: its marker sits under '### Security'"]
        # a closing line in a list its row does not name (R4 not followed)
        assert _wp30_list_problems(rules, log + "- x. (WP-30, P1.1a)\n") == [
            "P1.1a: a line ending (WP-30, P1.1a) sits under '### Security'"]
        assert _wp30_list_problems({"P1.19": ("Fixed in WP-30",)}, log) == [
            "CHANGELOG.md has no single '### Fixed in WP-30' list"]
~~~~

**`docstring-item-9`** (01-02; after the module docstring's line `   keeps every P0 entry closed with no marker left.`, :45).

~~~~text docstring-item-9
9. WP-30's P1 entries (.ultraplan/wp30/index.md A144) are open in BUGS.md
   in the form "Not fixed because WP-30 section NN has not landed. Graded
   S1|S2|S3 (WP-30): ...", NN being the section WP30_SECTION names, and
   listed in WP30_OPEN, which alone (with WP29_OPEN) exempts them from the
   release guard, with a "<!-- WP-30 <id> -->" marker in each CHANGELOG
   list WP30_LISTS names, until their section lands; then the key is gone,
   no marker is left, each of those lists holds a line ending
   "(WP-30, <id>)", and a closed entry's Resolution holds "(WP-30, <id>)".
~~~~

**`fixed-in-wp30`** (01-04; the heading and introduction of the new list).

~~~~text fixed-in-wp30
### Fixed in WP-30

Failures the drop-in re-audit of 30sep2026 ranked P1 that WP-30 fixed
without changing a drawn result; the results that changed are the WP-30
group under Results that change, and the security, behaviour, new and
requirement changes sit in their own lists.
~~~~

**`hygiene-reader`** (01-05; inserted above `class TestTheWp30TruthScript`).

~~~~python hygiene-reader
# ---------------------------------------------------------------------------
# WP-30's truth script: one block per section, gated, timed, closed, in order
# ---------------------------------------------------------------------------
# test/test_wp30_truth.cscript is WP-30's one new certification script
# (.ultraplan/wp30/index.md A142, merge rule R1).  Section 01 writes a stub
# block for every fix section (S02-S57) and each fills its own from a
# parallel worktree: a block that is not gated cannot be run alone
# (WP30_ONLY=S<NN>), one that is not closed swallows the next, one below the
# marker runs after the summary has judged the run, and one that does not
# print its start and end lines first and last cannot be timed (S58.7).

_WP30_TRUTH = os.path.join(_HERE, "test_wp30_truth.cscript")
_W30_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W30_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W30_MARK = "* ==== append new blocks above this line ===="
_W30_HEAD = re.compile(r"^(scaffold|P1\.\d{1,2}[abc]?): \S")


def _wp30_blocks(src):
    """``(blocks, problems)`` for the truth script's text.  A block is
    ``(section, header line, end line)``; a problem names a marker line that
    is not there exactly once, a block that is not closed by its own end
    line, not headed by an entry id, not gated by its own section, not timed
    by its own start and end lines, below the marker or out of section
    order, or a section whose blocks name two entries."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W30_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W30_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, heads, cur = [], {}, None
    for n, ln in enumerate(lines, 1):
        o, c = _W30_OPEN.match(ln.rstrip()), _W30_CLOSE.match(ln.rstrip())
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
                head = _W30_HEAD.match(cur[2])
                if not head:
                    bad.append("%s (line %d) names no entry ('P1.<n>: <what>')"
                               % (cur[0], cur[1]))
                else:
                    heads.setdefault(cur[0], set()).add(head.group(1))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur[:2])
    for k, (sec, first, last) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1]
                if ln.strip() and not ln.strip().startswith(("//", "*"))]
        if code[:2] != ["local only : env WP30_ONLY",
                        'if inlist("`only\'", "", "%s") {' % sec]:
            bad.append("%s (line %d) is not gated by WP30_ONLY=%s"
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
    for sec, ids in sorted(heads.items()):
        if len(ids) > 1:
            bad.append("%s's blocks name %d entries: %s"
                       % (sec, len(ids), sorted(ids)))
    return blocks, bad
~~~~

**`hygiene-class`** (01-01; appended at the end of `test/test_cscript_hygiene.py`).

~~~~python hygiene-class
class TestTheWp30TruthScript:
    """The scaffold section 01 writes, and every block a later section
    fills or adds."""

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP30_TRUTH)
        order = ['cscript "WP-30 truth', "SKIP: Python not available.",
                 'do "cert_helpers.do"', 'do "cert_svg.do"', "* ==== S01 ",
                 "local only : env WP30_ONLY", "* ==== end S01 ====",
                 "* ==== S02 ", "* ==== end S57 ====", _W30_MARK,
                 "test_wp30_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_timed_closed_and_in_section_order(self):
        blocks, bad = _wp30_blocks(_read(_WP30_TRUTH))
        assert not bad, "\n".join(bad)
        assert sorted({b[0] for b in blocks}) == [
            "S%02d" % n for n in range(1, 58)], blocks
        assert blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        def block(sec, head, body=""):
            return ("* ==== %s %s ====\nlocal only : env WP30_ONLY\n"
                    'if inlist("`only\'", "", "%s") {\n'
                    '    display as text "%s start " c(current_date) " " '
                    "c(current_time)\n%s"
                    '    display as text "%s end " c(current_date) " " '
                    "c(current_time)\n}\n* ==== end %s ====\n"
                    % (sec, head, sec, sec, body, sec, sec))
        good = ('cscript "x"\n' + block("S01", "scaffold: smoke",
                                        "    // a case\n")
                + "\n" + block("S10", "P1.19: abbreviations")
                + _W30_MARK + "\nexit 9\n")
        blocks, bad = _wp30_blocks(good)
        assert bad == [], bad
        assert blocks == [("S01", 2, 9), ("S10", 11, 17)], blocks
        moved = good.replace(_W30_MARK + "\n", "")
        second = block("S10", "P1.20a: more")
        for text, says in (
                (good.replace('"S10") {', '"S01") {'), "not gated"),
                (good.replace("* ==== end S10 ====\n", ""), "never closed"),
                (good.replace("* ==== end S01 ====\n", ""),
                 "not closed before"),
                (good.replace("S10", "S00"), "section order"),
                (moved, "appears 0 times"),
                (moved.replace('cscript "x"\n',
                               'cscript "x"\n' + _W30_MARK + "\n"),
                 "below the marker"),
                (good.replace('"S10 end "', '"S10 stop "'),
                 "does not print its start line first"),
                (good.replace("S10 P1.19: abbreviations", "S10 abbreviations"),
                 "names no entry"),
                (good.replace(_W30_MARK, second + _W30_MARK),
                 "blocks name 2 entries")):
            _blocks, bad = _wp30_blocks(text)
            assert any(says in b for b in bad), (says, bad)
~~~~

**`served-names`** (01-01; appended at the end of `test/test_statistical_helpers.py`, inside `TestTheServedAppCarriesEveryName`).

~~~~python served-names
    def test_every_listed_name_exists(self):
        # WP-30 A149: _glyph_layer_lines copies each listed constant and
        # function through getattr(_mod, _name, None) and SKIPS a name
        # dash_render.py does not define, so a misspelt, renamed or deleted
        # entry fails only on the served page.  Every name in both copy
        # lists must be defined, and listed once.
        import ast
        import inspect
        import textwrap
        tree = ast.parse(textwrap.dedent(
            inspect.getsource(dr.ServerAppBuilder._glyph_layer_lines)))
        lists = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.For)
                    and isinstance(node.target, ast.Name)
                    and isinstance(node.iter, ast.Tuple)
                    and all(isinstance(e, ast.Constant)
                            and isinstance(e.value, str)
                            for e in node.iter.elts)):
                lists.setdefault(node.target.id, []).extend(
                    e.value for e in node.iter.elts)
        # The constants (_name) and the functions (_fn_name): 145 and 312
        # at c96facd.  A walk that finds nothing must not pass as a check.
        assert sorted(lists) == ["_fn_name", "_name"], sorted(lists)
        assert len(lists["_name"]) >= 140, len(lists["_name"])
        assert len(lists["_fn_name"]) >= 300, len(lists["_fn_name"])
        for kind, names in sorted(lists.items()):
            missing = sorted(n for n in set(names) if not hasattr(dr, n))
            assert not missing, (kind, missing)
            twice = sorted(n for n in set(names) if names.count(n) > 1)
            assert not twice, (kind, twice)
~~~~

**`truth-head`** (01-05; the script up to S01's end line; the 56 stubs follow, generated from Appendix A).

~~~~stata truth-head
*! test_wp30_truth.cscript
*! WP-30's ONE new certification script (.ultraplan/wp30/index.md A142):
*! every comparison with twoway's drawing or with Stata's own values that
*! WP-30's sections need lives here, one block per section, in section
*! order, so the certification suite grows by one script.  Refusal,
*! message and return-code checks join the EXISTING script for their area
*! instead (index.md merge rule R1); this script never gains one of those.
*!
*! S01 is the scaffold smoke (TF-01).  S02-S57 each own the block their
*! header names, a stub until that section fills it with its own cases
*! (its case-id prefix: index.md "Section manifest").  A section writes
*! only inside its own block, its helper programs directly above its own
*! header, and a second block of its own directly below its own end line.
*!
*! Usage: via run_all_cscripts.do (registered as its block 69).  One
*! block alone: set WP30_ONLY=S<NN> in the environment of the driver run
*! (index.md "The cscript driver"); a block with no case yet then ends
*! "no case ran" and r(9).  Each block prints "S<NN> start" and
*! "S<NN> end" with the date and time, so the closeout can time it.

cscript "WP-30 truth: twoway comparisons" adodir ".."

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
// Tally helpers -- test_wp29_truth.cscript's _w29_expect/_w29_done,
// renamed _w30_ for this script.  A case is any number of
// _w30_expect lines closed by one _w30_done.
// ----------------------------------------------------------------
global w30_nfail    = 0
global w30_faillist ""
global w30_bad      = 0
global w30_ncase    = 0

capture program drop _w30_expect
program define _w30_expect
    version 19
    args id cond msg
    if !(`cond') {
        display as error `"`id' FAIL: `macval(msg)'"'
        global w30_bad = 1
    }
end

capture program drop _w30_done
program define _w30_done
    version 19
    args id msg
    if ${w30_bad} {
        global w30_nfail    = ${w30_nfail} + 1
        global w30_faillist "${w30_faillist} `id'"
    }
    else display as text `"`id' PASS: `macval(msg)'"'
    global w30_bad   = 0
    global w30_ncase = ${w30_ncase} + 1
end

// A fresh directory for this run's files, never one that already exists:
// a fixed name in a shared temp directory could be planted by another
// account (rule 1), so a name Stata has not handed out before is made and
// the run fails if it cannot be.  Every block writes only under it.
tempfile w30_base
local w30_work "`w30_base'_w30"
capture mkdir "`w30_work'"
if _rc {
    display as error "test_wp30_truth: cannot create the work directory `w30_work' (rc `=_rc')"
    exit 9
}

* ==== S01 scaffold: the helpers load and a twoway SVG is read ====
local only : env WP30_ONLY
if inlist("`only'", "", "S01") {
    display as text "S01 start " c(current_date) " " c(current_time)

    // ------------------------------------------------------------
    // TF-01: cert_svg_export and cert_svg_texts on one twoway scatter,
    // and dash's own programs are loaded from this tree.
    // ------------------------------------------------------------
    sysuse auto, clear
    quietly twoway scatter mpg weight, name(w30s01, replace)
    cert_svg_export, name(w30s01) file("`w30_work'/w30s01.svg")
    local s01_rc   = r(rc)
    local s01_file "`r(file)'"
    _w30_expect TF-01 "(`s01_rc' == 0)" "cert_svg_export rc `s01_rc'"
    capture confirm file "`s01_file'"
    _w30_expect TF-01 "(_rc == 0)" "r(file) `s01_file' does not exist"
    cert_svg_texts, file("`s01_file'")
    local s01_n    = r(n)
    local s01_list "`r(list)'"
    _w30_expect TF-01 "(`s01_n' > 0)" "cert_svg_texts found no text elements"
    capture program list _dash_serve
    _w30_expect TF-01 "(_rc == 0)" "dash.ado's _dash_serve is not loaded"
    _w30_done TF-01 "a twoway SVG was written and read (`s01_n' texts); dash is loaded"

    capture erase "`s01_file'"
    capture erase "`s01_list'"
    capture graph drop w30s01
    display as text "S01 end " c(current_date) " " c(current_time)
}
* ==== end S01 ====
~~~~

**`truth-tail`** (01-05; after the last stub and one blank line).

~~~~stata truth-tail
* ==== append new blocks above this line ====

// ----------------------------------------------------------------
// Summary (test_wp29_truth.cscript's shape)
// ----------------------------------------------------------------
capture graph drop _all
capture dash clear
capture rmdir "`w30_work'"
local nfail    = ${w30_nfail}
local faillist "${w30_faillist}"
local ncase    = ${w30_ncase}
local only : env WP30_ONLY
macro drop w30_nfail w30_faillist w30_bad w30_ncase
display as text ""
display as text "============================================================"
if `ncase' == 0 {
    // A WP30_ONLY that names no block, or only a stub, ran nothing:
    // that is not a pass.
    display as error "  test_wp30_truth: no case ran (WP30_ONLY=`only')"
    display as text "============================================================"
    exit 9
}
else if `nfail' == 0 {
    display as text "  test_wp30_truth: ALL CHECKS PASSED"
    display as text "============================================================"
}
else {
    display as error "  test_wp30_truth: `nfail' CHECK(S) FAILED"
    display as error "  failing:`faillist'"
    display as text "============================================================"
    exit 9
}
~~~~

**`runner-69`** (01-06; after `test/run_all_cscripts.do`:1769, block 68's closing `}`, and one blank line).

~~~~stata runner-69
// ----------------------------------------------------------------
// 69. test_wp30_truth.cscript (WP-30: the one certification script for
// every twoway/Stata-value comparison the drop-in P1 package needs; one
// block per section, S01's scaffold and one block for each of S02-S57,
// above its "append new blocks above this line" marker --
// .ultraplan/wp30/index.md A142)
// ----------------------------------------------------------------
display as text "[ RUN ] test_wp30_truth.cscript"
cd "`testdir'"
capture noisily {
    do "test_wp30_truth.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp30_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp30_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp30_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
~~~~

## Appendix D: `s01_apply.py` (written to `<scratch>/s01/s01_apply.py` by task 01-01)

~~~~python s01-apply
"""s01_apply.py <section-01 file> <step>: apply one step of WP-30 S01.

Run from the root of the S01 worktree.  It reads only the section file (its
Appendix A table, its Appendix B entries and its named ~~~~ blocks) and the
files the step edits; it asserts every anchor before writing and refuses a
step already applied.  No shell, no network.  Steps, in task order:
  tests      01-01  TestWp30Tracking, TestTheWp30TruthScript, the two pins,
                    test_every_listed_name_exists
  readers    01-02  the WP-30 constants and readers, the release allowance,
                    docstring item 9
  bugs       01-03  the 56 entries appended to BUGS.md
  changelog  01-04  the 84 markers, the WP-30 group line, Fixed in WP-30
  truth      01-05  test/test_wp30_truth.cscript; the block reader
  runner     01-06  runner block 69
  anchors    01-07  the map anchors
"""
import os
import re
import sys

_ROW = re.compile(r"^\| (P1\.\d{1,2}[abc]?) \| (\d{2}) \| S([1-3]) \| "
                  r"([^|]+) \| ([^|]+) \|$")


def rd(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def wr(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class Plan:
    def __init__(self, path):
        self.text = rd(path)
        self.rows = [m.groups() for m in map(_ROW.match,
                                             self.text.splitlines()) if m]
        self.entries = self.block("bugs-entries")
        self.titles = re.findall(r"^- \[ \] Title: (.+)$", self.entries, re.M)
        assert len(self.rows) == 56 and len(self.titles) == 56, (
            len(self.rows), len(self.titles))
        self.by_section = sorted(self.rows, key=lambda r: r[1])

    def block(self, name):
        """The text of the fenced block ``~~~~<lang> <name>``, without its
        leading and trailing blank lines."""
        hit = re.search(r"^~~~~\w+ %s\n(.*?)\n~~~~$" % re.escape(name),
                        self.text, re.M | re.S)
        assert hit, "no block " + name
        return hit.group(1).strip("\n")

    def lists(self, row):
        return [n.strip() for n in row[3].split(";")]

    def constants(self):
        opn = ["WP30_OPEN = {"] + ['    "%s": "%s",' % (r[0], t) for r, t
                                  in zip(self.rows, self.titles)] + ["}"]
        lst = ["WP30_LISTS = {"]
        for r in self.rows:
            names = ['"%s"' % n for n in self.lists(r)]
            tup = names[0] + "," if len(names) == 1 else ", ".join(names)
            lst.append('    "%s": (%s),' % (r[0], tup))
        sec = (["WP30_SECTION = {"] + ['    "%s": %d,' % (r[0], int(r[1]))
                                       for r in self.rows] + ["}"])
        return "\n".join(opn), "\n".join(lst + ["}"]), "\n".join(sec)

    def markers(self, name):
        ids = [r[0] for r in self.rows if name in self.lists(r)]
        out = []
        for i in ids:
            out += ["<!-- WP-30 %s -->" % i, ""]
        return out[:-1]

    def stubs(self):
        out = []
        for r in self.by_section:
            nn = r[1]
            head = re.sub(r" \(P1\.[^()]*\)$", "", r[4].strip())
            out += ["", "* ==== S%s %s: %s ====" % (nn, r[0], head),
                    "local only : env WP30_ONLY",
                    'if inlist("`only\'", "", "S%s") {' % nn,
                    '    display as text "S%s start " c(current_date) " " '
                    "c(current_time)" % nn,
                    '    display as text "S%s end " c(current_date) " " '
                    "c(current_time)" % nn,
                    "}", "* ==== end S%s ====" % nn]
        return out

    def anchors(self, indent, only=()):
        return ["%s# WP-30 S%s (%s): %s" % (" " * indent, r[1], r[0],
                                            r[4].strip())
                for r in self.by_section if not only or r[1] in only]


def once(text, old, new, what):
    assert text.count(old) == 1, "%s: anchor found %d times" % (
        what, text.count(old))
    return text.replace(old, new)


TRACK = "test/test_tracking_documents.py"
HYG = "test/test_cscript_hygiene.py"
STAT = "test/test_statistical_helpers.py"


def step_tests(p):
    t = rd(TRACK)
    assert "class TestWp30Tracking" not in t, "step tests already applied"
    assert t.endswith('        assert not bad, "\\n".join(bad)\n')
    wr(TRACK, t + "\n\n" + p.block("tracking-class") + "\n")
    t = rd(HYG)
    t = once(t, "        # package adds (.ultraplan/wp29/index.md A3), so 67 now."
             "  An empty\n",
             "        # package adds (.ultraplan/wp29/index.md A3), so 67; "
             "plus WP-30's\n"
             "        # test_wp30_truth, the one script that package adds\n"
             "        # (.ultraplan/wp30/index.md A142), so 68 now.  An empty\n",
             "pin 67 comment")
    t = once(t, "assert len(_CSCRIPTS) == 67,", "assert len(_CSCRIPTS) == 68,",
             "pin 67")
    t = once(t, "        # WP-29's test_wp29_truth gates the same way, so 49.\n"
             "        assert len(names) == 49,",
             "        # WP-29's test_wp29_truth gates the same way, so 49; "
             "WP-30's\n"
             "        # test_wp30_truth gates the same way, so 50.\n"
             "        assert len(names) == 50,", "pin 49")
    wr(HYG, t + "\n\n" + p.block("hygiene-class") + "\n")
    t = rd(STAT)
    assert t.endswith("        assert not sorted(wanted - defined), "
                      "sorted(wanted - defined)\n")
    wr(STAT, t + "\n" + p.block("served-names") + "\n")


def step_readers(p):
    t = rd(TRACK)
    assert "WP30_OPEN = {" not in t, "step readers already applied"
    opn, lst, sec = p.constants()
    readers = (p.block("tracking-readers").replace("@@WP30_OPEN@@", opn)
               .replace("@@WP30_LISTS@@", lst)
               .replace("@@WP30_SECTION@@", sec))
    assert "@@" not in readers
    t = once(t, "\n\n\nclass TestWp30Tracking:",
             "\n\n\n" + readers + "\n\n\nclass TestWp30Tracking:", "class")
    t = once(t, "        # WP-29's P0 entries stay open, S1 or S2, until their "
             "sections land\n"
             "        # (WP29_OPEN); TestWp29Tracking holds each one to its "
             "WP-29 form.\n"
             "        allowed = set(WP29_OPEN.values())\n",
             "        # WP-29's P0 entries stayed open, S1 or S2, until their "
             "sections\n"
             "        # landed (WP29_OPEN, empty since its closeout); WP-30's "
             "P1 entries\n"
             "        # do the same until theirs land (WP30_OPEN), and "
             "TestWp30Tracking\n"
             "        # holds each one to its WP-30 form.\n"
             "        allowed = set(WP29_OPEN.values()) | "
             "set(WP30_OPEN.values())\n", "release guard")
    item = ("   keeps every P0 entry closed with no marker left.\n")
    t = once(t, item, item + p.block("docstring-item-9") + "\n", "docstring")
    wr(TRACK, t)


def step_bugs(p):
    t = rd("BUGS.md")
    assert "WP-30 section" not in t, "step bugs already applied"
    assert t.endswith(".\n") and not t.endswith("\n\n")
    wr("BUGS.md", t + "\n" + p.entries + "\n")


def step_changelog(p):
    L = rd("CHANGELOG.md").split("\n")
    assert not any("WP-30" in x for x in L), "step changelog already applied"
    want = {313: "(WP-29, P0.20)", 315: "### Security",
            409: "(WP-29, P0.14)", 411: "### New", 450: "(WP-23).",
            452: "### Fixed", 596: "(WP-29, P0.12a)", 598: "### Removed",
            607: "### Requirements", 651: "(WP-29, P0.19)",
            653: "### Fixed in WP-29"}
    for n, end in want.items():
        assert L[n - 1].endswith(end), (n, L[n - 1])
    for n in (314, 410, 451, 597, 652):
        assert L[n - 1] == "", n
    fixed = (p.block("fixed-in-wp30").split("\n") + [""]
             + p.markers("Fixed in WP-30") + [""])
    # bottom-up, so every line number above still holds
    L[652:652] = fixed
    L[651:651] = [""] + p.markers("Requirements")
    L[596:596] = [""] + p.markers("Changed behaviour")
    L[450:450] = [""] + p.markers("New")
    L[409:409] = [""] + p.markers("Security")
    L[313:313] = (["", "**WP-30 (drop-in P1, 03oct2026)**", ""]
                  + p.markers("Results that change"))
    wr("CHANGELOG.md", "\n".join(L))


def step_truth(p):
    path = "test/test_wp30_truth.cscript"
    assert not os.path.exists(path), "step truth already applied"
    wr(path, "\n".join([p.block("truth-head")] + p.stubs()
                       + ["", p.block("truth-tail")]) + "\n")
    t = rd(HYG)
    assert "_WP30_TRUTH = " not in t, "the block reader is already there"
    wr(HYG, once(t, "\n\n\nclass TestTheWp30TruthScript:",
                 "\n\n\n" + p.block("hygiene-reader")
                 + "\n\n\nclass TestTheWp30TruthScript:", "hygiene class"))


def step_runner(p):
    path = "test/run_all_cscripts.do"
    L = rd(path).split("\n")
    assert not any("test_wp30_truth" in x for x in L), "runner already done"
    assert L[1768] == "}" and L[1769] == "" and L[1771] == "// Summary", (
        L[1766:1772])
    assert "[ FAIL] test_wp29_truth.cscript" in L[1766], L[1766]
    L[1769:1769] = [""] + p.block("runner-69").split("\n")
    wr(path, "\n".join(L))


def step_anchors(p):
    path = "test/function_test_map.py"
    L = rd(path).split("\n")
    assert not any("# WP-30 S" in x for x in L), "anchors already placed"
    assert L[799].startswith(" 'main': ") and L[799].endswith("'}"), L[799]
    assert L[894] == "}" and L[893].startswith('    "version_tuple": ')
    L[894:894] = p.anchors(4, ("05", "25", "41"))      # SETUP_FUNCTIONS
    L[799:800] = [L[799][:-1] + ","] + p.anchors(1) + ["}"]  # FUNCTIONS
    wr(path, "\n".join(L))
    path = "test/program_coverage_map.py"
    L = rd(path).split("\n")
    for n, key in ((298, '"dash_setup.ado": {'), (338, '"dash_parse.mata": {'),
                   (608, "}")):
        assert L[n - 1] == "    }," and L[n].strip() == key, (n, L[n - 1:n + 1])
    L[607:607] = p.anchors(8)                          # dash_parse.mata
    L[337:337] = p.anchors(8, ("03", "05", "25", "41"))  # dash_setup.ado
    L[297:297] = p.anchors(8)                          # dash.ado
    wr(path, "\n".join(L))


STEPS = {"tests": step_tests, "readers": step_readers, "bugs": step_bugs,
         "changelog": step_changelog, "truth": step_truth,
         "runner": step_runner, "anchors": step_anchors}

if __name__ == "__main__":
    STEPS[sys.argv[2]](Plan(sys.argv[1]))
    print("applied", sys.argv[2])
~~~~
