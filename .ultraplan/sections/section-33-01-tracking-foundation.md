# Section 33-01: GAPS4 register, 221 BUGS entries, tracking and truth-script readers

> Part of: WP-33 (Verification corpus and README gallery) · Items: none (closes no item) · Risk: yellow · Batch: 33.1 (with 33-15; merged first) · Depends on: none · Blocks: every other section of WP-33..WP-49 · Tasks: 5, 2 commits · Case-id prefix: Q3300 (the scaffold) / Q3301

## Overview

Today the drop-in audit of 19oct2026 is tracked nowhere: "Most are untracked: BUGS.md has one open entry (natscale)" (audit, Verdict). WP-31's register GAPS3.md is closed, and `test/test_tracking_documents.py` knows only the WP-29..WP-31 forms; `test/test_cscript_hygiene.py` reads only `test_wp30_truth.cscript` and `test_wp31_truth.cscript`, each with its own copy of the block reader.

After this section: `GAPS4.md` (repository root) holds one row and one `Tracked:` line for each of the 221 live items of index Appendix A (PD-1); BUGS.md holds 221 new open entries in PD-4's open form, graded per PD-2; `test_tracking_documents.py` holds `GAPS4_OPEN` / `GAPS4_WP` / `GAPS4_SECTION` and `TestGaps4Tracking`, and its release guard exempts the open GAPS4 titles; `test_cscript_hygiene.py` has one parametrised reader `_wp_blocks(src, wp)` (WP-31's reader becomes a wrapper of it); `test/templates/wp_truth_template.cscript` exists, and `test/test_wp33_truth.cscript`, made from it, is registered in the runner (block 71) and the shard table, with the three count pins moved. Every later section closes its item against these readers.

These pieces share one section because each later section's closing commit needs all of them at once (its BUGS entry, its GAPS4 line, its open-allowance key, its truth block), and because they are written once by tools, not by hand.

**Test order and commit rule.** Task 33-01-01 writes the GAPS4 tests and runs them red against the unmodified tree (GAPS4.md is missing), saving `<scratch>/33-01-01-failure.txt`; task 33-01-02 writes the register and commits group 1. Task 33-01-03 writes the truth-script tests and moves the pins, red (no template, no wp33 script), saving `<scratch>/33-01-03-failure.txt`; task 33-01-04 makes them green and commits group 2. Task 33-01-05 is the hand-back checkpoint. No test-only commit exists; no full suite runs inside this section.

### Section decisions

- **D-33-01.a (generator).** GAPS4.md, the BUGS entries and the three constants are written by a **one-off scratch script** (`<scratch>/gen_gaps4.py`, listing N-1), whose output is committed; the script is not committed. Why: every later closing commit edits GAPS4.md and BUGS.md in place (R5), so a committed regenerator would clobber them, and its inputs live under `.ultraplan/`, which is archived when the plan ends. The permanent record is GAPS4.md plus `GAPS4_WP`/`GAPS4_SECTION`.
- **D-33-01.b (titles and texts).** The BUGS title and the GAPS4 Item text are the audit bullet's title (audit lines 41-845), not Appendix A's Item cell. Why: the audit bullet is the source text; Appendix A is the binding id/section/kind list (a dry run of N-1 against index.md as revised in Phase 4 matches all 221 ids, their other ids and their sections). Three audit titles hold `"` and are replaced by the fixed titles in N-1 (`TITLE_OVERRIDE`: LT-12, LT-24, MS-3). In GAPS4.md table cells, `|` is written `\|`. The Evidence cell is the bullet's `Evidence:` line verbatim; the Fix cell follows D-33-01.h.
- **D-33-01.c (BUGS entry fields).** File Names and Line Numbers = the audit Evidence; Description = `Drop-in audit of 19oct2026 (.ultraplan/review/DROPIN-AUDIT-19oct2026.md at commit f81cd31), package <p> (<grade>): ids <ids>; <status>. Registered as GAPS4 <id> (WP-NN, section NN-MM, <Kind>).` (the commit keeps the citation readable after `.ultraplan/` is archived when the plan ends: `git show f81cd31:.ultraplan/review/DROPIN-AUDIT-19oct2026.md`); Suggested fix = the Fix of D-33-01.h; Resolution = `Not fixed because WP-NN section NN-MM has not landed. Graded S<n> (WP-NN): drop-in audit package <p>, <grade>.` (PD-4; `<grade>` is the package heading's blocker/major/minor/cosmetic). Sev is Appendix A's Sev column.
- **D-33-01.d (scaffold id).** Every WP truth script's scaffold block is `S00` with case `Q<NN>00-1`, so it never collides with section NN-01's own `S01` blocks and `Q<NN>01-k` cases (PD-5).
- **D-33-01.e (block heads).** A block head in a WP-33..49 script is `scaffold: <what>`, `<GAPS4 lead id>: <what>` or `tool: <what>` (a harness section with no item, e.g. 33-09); a GAPS4 id in a head must belong to that WP and section.
- **D-33-01.f (no empty parametrise).** The per-WP closeout and counts tests loop over `GAPS4_CLOSED_WPS` / `GAPS4_CLOSEOUT` inside one test each, never `@pytest.mark.parametrize` over an empty tuple (pytest reports that as a skip, and a strict run treats a skip as red, conftest.py:196-208).
- **D-33-01.g (commit subjects).** `(WP-33 33-01)` at the end of both subjects; the same `(WP-33 33-MM)` form is used by 33-02..33-09 and 33-15 (sections with no item).
- **D-33-01.h (the Fix column states the ruling; DECISIONS A-10).** GAPS4's Fix cell and the BUGS Suggested fix are the audit's `Fix:` line, except where a ruling resolved the item otherwise: then they hold the ruled resolution from N-1's `FIX_OVERRIDE` (63 rows): every Kind Document or Partly row (34); the two per-word rows DT-15 and CV-14 (P4-7); plat:PT-7 (P4-3, A-12); LT-24 (P4-5); AX-11, AX-13 and AX-15 (A-5); the ten Fix rows whose audit remedy a ruling rejected -- plat:PT-1 (M8, A-8: no `python query` probe), plat:PT-4 (A-7: a private file, not a scalar), TR-13 and DG-1 (M9), plot:PT-3 and syn:SD-13 (M7), plot:PT-7 (M12, PD-11: dash's extra lines stay), VF-4 (A-1: the height band goes), TR-2 (M5, P4-8, A-25: colours judged within a recorded tolerance, the gallery built last), TR-23 (R9: a pinned test is never deleted); and the twelve rows whose audit Fix offered naming or documenting as an alternative to drawing, which M11 (BY-1, AX-9, AX-12, LT-3, LT-6, LT-7, LT-15, LT-18, ST-16) and M12 (basic:PT-4, basic:PT-6, basic:PT-11) rule out, kept to the audit's fix half. N-1 refuses a non-Fix row with no override and an override naming an unregistered id. So plat:PT-16 reads "Documented only (M8): the help states that Chrome is the browser dash is tested in", never the audit's suggestion to add other browsers; plat:PT-14 keeps JSON (Q31); GW-12 adds no export command (PRD §7); plat:PT-2 keeps the Stata 19 floor (Q46); plat:PT-1 states M8's rule (no `python query` probe), never the audit's fallback to one.
- **D-33-01.i (the seconds table may change).** `local w<NN>_secs ...` is the one statement of a WP script's frame that a later commit edits (the measured seconds of its blocks, so the shards split by real cost). `_head_and_tail` (N-5) leaves it out of the frame comparison; the hand-back (33-01-05) asks the orchestrator to add the WE step that rewrites it from the WE.4 cert log's `S<MM> start`/`S<MM> end` lines.

## Risk: [yellow] -- two documents and two test files every later section edits

**Why.** A wrong form here makes all 221 later closing commits fight the reader. **Risk factors.** (1) The release guard fails on 221 open S1/S2 entries unless the allowance is wired. (2) `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` fails on a new root file. (3) `test_no_entry_names_a_test_that_does_not_exist` would fail if an audit Evidence named a missing test (measured: 0 of 221 do). (4) An empty parametrised test skips. **Mitigation.** N-1 validates the inputs and refuses on any mismatch; N-2 was run against the generated documents in a scratch simulation (0 problems from every reader; release-guard wiring in TR-33-01.4); the template was built and run once under Stata (`Q3300-1 PASS`, `test_wp33_truth: ALL CHECKS PASSED`, 20oct2026).

## Dependencies

- **Depends on:** none.
- **Blocks:** every section of WP-33..WP-49: each closes its row against GAPS4.md/BUGS.md and appends its block to its WP's truth script.
- **Parallel batch 33.1:** 33-15 (the size caps removed, P4-3) -- disjoint files: this section owns BUGS.md, GAPS4.md, test_tracking_documents.py, test_cscript_hygiene.py, test_packaging.py, test_cert_shards.py, run_all_cscripts.do and test/templates/ alone; 33-15 edits dash.ado, dash_parse.mata, dash_render.py, dash.sthlp, CHANGELOG.md and the cap pins and touches none of these. Merge this section first.

## Evidence

- **Audit structure (measured 20oct2026 at 090d928).** Work packages lines 41-845: 221 bullets `- **<title>** [<ids>; <status>]` each followed by `  - Evidence: ...` and `  - Fix: ...`; the 221 lead ids equal Appendix A's 221 live lead ids and every bullet's other ids equal Appendix A's Other ids. No live text names a withdrawn item, a word the rulings bar (M1) or a gone path. Package headings `### <p>. <title> (<grade>, effort <e>)` (lines 43, 81, ..., 823).
- **BUGS.md** (4,479 lines, 748 entries, one open: the natscale entry at :4139-4143). The parser `_ENTRY` test_tracking_documents.py:145, fields `_FIELDS` :146-147 (File Names and Line Numbers, Description, Suggested fix, Resolution), `_parse_bugs` :152-198. Entries end the file separated by one blank line.
- **Readers the new entries meet.** `TestEveryOpenEntrySaysWhyItIsOpen` :500-520 (`not fixed` + `because`); `TestNoOpenEntryBlocksARelease` :554-601, `_GRADE` :565, the allowance at :583-584:

```python
        allowed = (set(WP29_OPEN.values()) | set(WP30_OPEN.values())
                   | set(WP31_OPEN.values()))
```

  `_references` :342-372 (dangling test names), `_CASE_ID` :254-255 (an audit id like `AX-4` has the case-id shape; harmless unless a cscript displays `AX-4 PASS`, which PD-5 prevents).
- **WP-31's machinery to copy:** `_WP31_OPEN_FORM` :2293-2295, `_GAPS3_*` :2296-2310, `_wp31_open_problems` :2322-2348, `_wp31_closure_problems` :2359-2372, `_parse_gaps3` :2401-2416, `_gaps3_problems` :2419-2462, `_sha_exists` :2465, `TestWp31Tracking` :2469-2645, closeout counts `_WP31_CLOSEOUT` :2696 and `TestTheCountsAreTrue::test_the_wp31_closeout_counts_are_computed` (:2735 class, :2781-2799 test; it is not in `TestWp31Tracking`). Docstring items 10-11 end at :78.
- **test_packaging.py:430-437** `_ROOT_ALSO` lists the root documents (`"GAPS3.md"` at :433); GAPS4.md must join it.
- **test_cscript_hygiene.py:** `_CSCRIPTS = sorted(glob(... "*.cscript"))` :33 (not recursive, so `test/templates/` is outside it); `test_the_glob_finds_every_script` :283-302 asserts 69 at :300; `test_every_script_that_skips_for_python_is_read` :304-321 asserts 51 at :321; WP-31 reader `_WP31_TRUTH`..`_wp31_blocks` :1218-1275; `TestTheWp31TruthScript` :1278-1321.
- **test/test_cert_shards.py:45** `assert len(names) == len(set(names)) == 69  # 68 -> 69: test_wp31_truth.cscript (WP-31 S01)`.
- **test/run_all_cscripts.do:** shard table `// ---- shards: begin` :75 .. `:158`, last rows :156-157 (`test_wp30_truth.cscript 566.6 0  * * * ///`, `test_wp31_truth.cscript 456.4 0  * * *` with no continuation); block 70 :3125-3170; Summary :3172.
- **test/test_wp31_truth.cscript** frame: header :1-20, cscript :22, Python gate :36-39, loads :41-45, tally helpers :47-77, work dir :80-90, parts :92-182 (seconds table :105-111), S01 :184-214, marker :14433, summary :14435-14469.
- **Tools outside the repo:** `../dash-wt/_tools/picks.sh:11` names only `test/test_wp31_truth.cscript`; `:15` lists `BUGS.md|CHANGELOG.md|GAPS3.md|TWOWAY_COVERAGE_AUDIT.md`. `blockorder.py`'s header regex `^\* ==== S\d\d ` already reads `S00`..`S99`.

## User stories

- US-33-01.1 As the maintainer and the coding agents, I want every audit item registered with its section, grade and evidence so that each later section knows exactly which row it closes and the release guard knows what is still open.
- US-33-01.2 As a coding agent of a later section, I want one truth-script template and one block reader so that my WP's script is made by `sed` and checked the same way as every other.

## Business requirements

- BR-33-01.1 Every one of the 221 live items appears exactly once in GAPS4.md (one row, one Tracked line `Open (WP-NN section NN-MM).`) and once in BUGS.md as an open entry naming its WP and section.
- BR-33-01.2 No register text names a withdrawn item or a word ruling M1 bars, and no Fix states a remedy a ruling rejected (A-10).
- BR-33-01.3 The release guard still fails on any open S1/S2 entry that is not a registered, unlanded GAPS4 item.
- BR-33-01.4 A WP truth script made from the template runs and passes its scaffold under the console binary.

## Technical requirements

- TR-33-01.1 `GAPS4.md` and the 221 BUGS.md entries are written by N-1 (`--write`), byte for byte, with D-33-01.h's `FIX_OVERRIDE`; nothing is hand-edited afterwards in this section.
- TR-33-01.2 test_tracking_documents.py: docstring item 12 inserted after line 78 (text in N-3); the three constants pasted from `<scratch>/gen/gaps4_constants.py` and the code of N-2 appended at the end of the file (after :2849), followed by `class TestGaps4Tracking` (N-3).
- TR-33-01.3 The release guard at :583-584 becomes `allowed = (set(WP29_OPEN.values()) | set(WP30_OPEN.values()) | set(WP31_OPEN.values()) | set(GAPS4_OPEN.values()))`, with the comment above it extended by the sentence `GAPS4's entries do the same until their sections land (GAPS4_OPEN; TestGaps4Tracking).` `GAPS4_OPEN` is defined at module level below the class; Python resolves it at call time, so the order is safe.
- TR-33-01.4 test_packaging.py `_ROOT_ALSO`: add `"GAPS4.md",` after `"GAPS3.md",` on line 433 (keep the frozenset's other lines).
- TR-33-01.5 test_cscript_hygiene.py: replace `_wp31_blocks` (:1227-1275) by the code of N-4 (the general `_wp_blocks` plus the thin `_wp31_blocks` wrapper, which keeps every message `TestTheWp31TruthScript::test_the_block_reader` expects); append `class TestTheWpTruthScripts` (N-5) at the end of the file.
- TR-33-01.6 `test/templates/wp_truth_template.cscript` is written by `<scratch>/make_template.py` (N-6) from test_wp31_truth.cscript; `test/test_wp33_truth.cscript` = `sed 's/@@WP@@/33/g'` of it.
- TR-33-01.7 run_all_cscripts.do: line 157 gains ` ///` and a new row follows it: `    test_wp33_truth.cscript               1.0 0  * * *`; block 71 (N-7) is inserted after block 70's closing `}` (:3170) and before the Summary comment (:3172). `python3 scripts/cert_shards.py check` exits 0.
- TR-33-01.8 Pins (R10): test_cscript_hygiene.py:300 `69` -> `70` with `# 69 -> 70: test_wp33_truth.cscript (WP-33 33-01)` appended to the comment above; :321 `51` -> `52` with `# 51 -> 52: test_wp33_truth gates on c(python_exec) (WP-33 33-01)`; test_cert_shards.py:45 `69` -> `70  # 69 -> 70: test_wp33_truth.cscript (WP-33 33-01)`.
- TR-33-01.9 No dash.ado, dash_parse.mata or dash_render.py change; no function_test_map/program_coverage_map entry is needed (test helpers only).

## Boundaries

Do not touch: GAPS3.md, CHANGELOG.md (W0.3 is the orchestrator's; 33-15 adds its own line), ROADMAP.md, dash.sthlp, any shipped file, every file 33-15 edits (its batch-mate), the natscale entry (BUGS.md:4139-4143; PD-9 gives it to 34-09), `WP29_OPEN`/`WP30_OPEN`/`WP31_OPEN`, `TestTheWp30TruthScript`, `../dash-wt/_tools/*` (reported in 33-01-05 instead). Follow R14 (banned topics) in every line written.

## Stata truth

None (no extract script, no fixture). One run of the new `test_wp33_truth.cscript` through `scripts/stata_slot.sh` (task 33-01-04) proves the template.

## TDD test stubs

- Test: the register holds the 221 items in 16 WPs, none withdrawn -- test/test_tracking_documents.py::TestGaps4Tracking::test_the_register_holds_every_item (red at base: GAPS4.md missing)
- Test: every GAPS4_OPEN title is one open entry in the open form -- ::TestGaps4Tracking::test_every_allowed_title_is_an_open_entry (red at base)
- Test: every item has one row and one Tracked line consistent with BUGS.md -- ::TestGaps4Tracking::test_every_item_has_one_tracked_line (red at base)
- Test: a closed id has a closed entry naming (WP-NN, id) -- ::TestGaps4Tracking::test_a_closed_entry_names_its_closure
- Test: closed WPs stay closed -- ::TestGaps4Tracking::test_every_closed_wp_is_closed
- Test: closeout counts recomputed -- ::TestGaps4Tracking::test_the_gaps4_closeout_counts_are_computed
- Test: the readers find what is wrong -- ::TestGaps4Tracking::test_the_gaps4_readers, ::test_the_gaps4_problem_readers, ::test_the_count_reader
- Test: template and wp33 script exist -- test/test_cscript_hygiene.py::TestTheWpTruthScripts::test_the_template_and_the_wp33_script_exist (red at base)
- Test: scaffold order per script -- ::TestTheWpTruthScripts::test_the_scaffold_is_in_order[test_wp33_truth.cscript]
- Test: blocks gated, timed, ordered, S00 first -- ::TestTheWpTruthScripts::test_every_block_is_gated_timed_closed_and_in_section_order[...]
- Test: a GAPS4 head belongs to its WP and section -- ::TestTheWpTruthScripts::test_each_block_names_a_row_of_its_own_section[...]
- Test: the template makes a clean script, and every script starts and ends as the template -- ::TestTheWpTruthScripts::test_the_template_makes_a_clean_script, ::test_every_script_keeps_the_templates_head_and_tail[...]
- Test: the general reader -- ::TestTheWpTruthScripts::test_the_block_reader
- Test: the seconds table may change, nothing else of the frame -- ::TestTheWpTruthScripts::test_the_seconds_table_may_change
- Cert case: Q3300-1 (S00 scaffold of test_wp33_truth.cscript).
- Pins moved (red at base after the move): test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script, ::test_every_script_that_skips_for_python_is_read; test_cert_shards.py::TestTheRealTable::test_every_registered_script_has_one_row.
- Parity corpus: none (no twin).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| GAPS4 register and BUGS forms | pytest test_tracking_documents.py | GAPS4.md, BUGS.md | n/a |
| Package root list | pytest test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own | git ls-files | n/a |
| Template, reader, pins | pytest test_cscript_hygiene.py test_cert_shards.py test_cert_verdict.py | the scripts | n/a |
| Shard table | `python3 scripts/cert_shards.py check` | run_all_cscripts.do | n/a |
| Scaffold runs | cscript via scripts/stata_slot.sh | none | n/a |

- AC-33-01.1 `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q -n0` passes, and `grep -c '^- \*\*.* Tracked:\*\* Open (WP-' GAPS4.md` prints 221.
- AC-33-01.2 `grep -c 'Registered as GAPS4 ' BUGS.md` prints 221; `grep -cE '^- \[ \] Title:' BUGS.md` prints 222.
- AC-33-01.3 `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_shards.py test/test_cert_verdict.py -q -n0` passes; `python3 scripts/cert_shards.py check` exits 0.
- AC-33-01.4 The wp33 run's log holds `Q3300-1 PASS` and `test_wp33_truth: ALL CHECKS PASSED`.
- AC-33-01.5 `grep -nE 'plat:PT-3|basic:PT-7|plot:PT-10|sunflower' GAPS4.md` prints nothing, and `grep -c 'Documented only' GAPS4.md` prints 32 (the Document rows' rulings).

## Tasks

**Commit boundary.** Group 1 = tasks 33-01-01 and 33-01-02, one commit by 33-01-02: `Register the drop-in audit's 221 items in GAPS4.md and BUGS.md (WP-33 33-01)`. Group 2 = tasks 33-01-03 and 33-01-04, one commit by 33-01-04: `Add the per-WP truth-script template, the WP-33 truth script and one block reader (WP-33 33-01)`. Task 33-01-05 commits nothing. Both commits are made on branch `wp33-s01` in the worktree `$WT` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s01`; every command below runs with `$WT` as its working directory, and `$WT` in a command is that absolute path. The section closes no item and the corpus ledger, the known-differences tables and the guard do not exist yet (33-05, 33-10, 33-09), so BRIEF's three ledger steps do not apply to its commits. Before each commit: inside the worktree `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is re-run); grep the message for `claude|anthropic` before and after. No Co-Authored-By trailer (agent-rules.md).

```xml
<task type="auto" id="33-01-01">
  <name>Write the GAPS4 tests red</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[ Write N-1 to <scratch>/gen_gaps4.py and run `python3 <scratch>/gen_gaps4.py --repo $WT --out <scratch>/gen` (dry run; it must print "gen_gaps4: 221 rows, 221 entries, 16 WPs; dry run"). In test/test_tracking_documents.py insert docstring item 12 (N-3, after line 78), then append at the end of the file: the comment and the three dicts from <scratch>/gen/gaps4_constants.py (GAPS4_OPEN, GAPS4_WP, GAPS4_SECTION, one key per line, in that order), then the code of N-2, then class TestGaps4Tracking (N-3). Before editing `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2`, run `node .gitnexus/run.cjs impact "test_no_open_entry_is_s1_or_s2" --direction upstream --repo .` and report its risk in the hand-back (a test method: UNKNOWN or LOW is expected; confirm with `grep -rn test_no_open_entry_is_s1_or_s2 test/`). Wire the release guard (TR-33-01.3). Do not create GAPS4.md or touch BUGS.md yet. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_tracking_documents.py -q -n0 -k "Gaps4 or release" 2>&1 | tee <scratch>/33-01-01-failure.txt | tail -5` shows failures in test_the_register_holds_every_item, test_every_allowed_title_is_an_open_entry and test_every_item_has_one_tracked_line (FileNotFoundError on GAPS4.md, or "0 BUGS.md entries are titled"), and the three reader tests pass. Nothing is committed. ]]></verify>
  <done>The GAPS4 tests exist and fail at the base for the missing register; the failure text is saved.</done>
</task>

<task type="auto" id="33-01-02">
  <name>Write GAPS4.md and the 221 entries</name>
  <files>GAPS4.md, BUGS.md, test/test_packaging.py</files>
  <action><![CDATA[ Run `python3 <scratch>/gen_gaps4.py --repo $WT --out <scratch>/gen --write` once (it refuses if GAPS4.md exists). Add `"GAPS4.md",` after `"GAPS3.md",` in test/test_packaging.py's _ROOT_ALSO (:433). Run the verify; then the commit boundary's pull and detect-changes, `git -C $WT add GAPS4.md BUGS.md test/test_tracking_documents.py test/test_packaging.py` and commit group 1 with the subject in the commit boundary and a body holding the saved failure text's summary line, `Regression: test/test_tracking_documents.py::TestGaps4Tracking::test_the_register_holds_every_item -- failed at 090d928 with FileNotFoundError: GAPS4.md` (use the base sha and text you saved) and the line `GAPS4: 221 rows registered Open`. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py test/test_no_secrets.py -q -n0` passes; `grep -c 'Registered as GAPS4 ' BUGS.md` prints 221; `grep -c 'Tracked:\*\* Open (WP-' GAPS4.md` prints 221; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0. ]]></verify>
  <done>GAPS4.md and the 221 open BUGS.md entries are committed and every tracking reader passes.</done>
</task>

<task type="auto" id="33-01-03">
  <name>Write the truth-script reader tests red</name>
  <files>test/test_cscript_hygiene.py, test/test_cert_shards.py</files>
  <action><![CDATA[ Run `node .gitnexus/run.cjs impact "_wp31_blocks" --direction upstream --repo .` first and report its callers and risk (expected: TestTheWp31TruthScript only). In test/test_cscript_hygiene.py replace `def _wp31_blocks(src):` .. its `return blocks, bad` (:1227-1275) by N-4, keeping `_WP31_TRUTH`, `_W31_OPEN`, `_W31_CLOSE`, `_W31_MARK`, `_W31_HEAD` above it; append class TestTheWpTruthScripts (N-5) at the end of the file. Move the three pins of TR-33-01.8 now, so they fail until the script exists. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_shards.py -q -n0 2>&1 | tee <scratch>/33-01-03-failure.txt | tail -8` shows exactly these failing: TestTheWpTruthScripts::test_the_template_and_the_wp33_script_exist, test_the_template_makes_a_clean_script, test_the_glob_finds_every_script (69 != 70), test_every_script_that_skips_for_python_is_read (51), test_every_registered_script_has_one_row (69); TestTheWp31TruthScript passes unchanged. Nothing is committed. ]]></verify>
  <done>The general reader replaces WP-31's copy, its tests and the moved pins fail for the missing script, and the failure text is saved.</done>
</task>

<task type="auto" id="33-01-04">
  <name>Create the template and register wp33</name>
  <files>test/templates/wp_truth_template.cscript, test/test_wp33_truth.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[ Write N-6 to <scratch>/make_template.py; `mkdir -p $WT/test/templates && python3 <scratch>/make_template.py $WT $WT/test/templates/wp_truth_template.cscript` (prints "template: 246 lines, 113 placeholders"; a changed WP-31 frame makes it stop at an assert -- then report, do not patch). Create `sed 's/@@WP@@/33/g' $WT/test/templates/wp_truth_template.cscript > $WT/test/test_wp33_truth.cscript`. Edit test/run_all_cscripts.do per TR-33-01.7 (shard row; block 71 = N-7). Run the script once: write <scratch>/run_wp33.do with the four lines `cd "$WT/test"`, `adopath ++ "$WT/"`, `global dash_nobrowser 1`, `do "$WT/test/test_wp33_truth.cscript"` and run `sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_wp33.do`. Then the commit boundary's pull and detect-changes, and commit group 2 (`git -C $WT add test/templates/wp_truth_template.cscript test/test_wp33_truth.cscript test/run_all_cscripts.do test/test_cscript_hygiene.py test/test_cert_shards.py`), body with the saved failure lines as `Regression:` lines and `Flipped:` lines for the three pins (`69 was wrong because test_wp33_truth.cscript is registered`). ]]></action>
  <verify><![CDATA[ `python3 scripts/cert_shards.py check` exits 0; `python3 -m pytest test/test_cscript_hygiene.py test/test_cert_shards.py test/test_cert_verdict.py -q -n0` passes; `grep -E 'Q3300-1 PASS|test_wp33_truth: ALL CHECKS PASSED' <scratch>/run_wp33.log` prints both lines; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0. ]]></verify>
  <done>The template, the WP-33 truth script, its runner block, shard row and moved pins are committed and the scaffold passes under Stata.</done>
</task>

<task type="checkpoint" id="33-01-05">
  <name>Hand back the tool edits</name>
  <files>none</files>
  <action><![CDATA[ Report to the orchestrator, in the hand-back, the two edits to ../dash-wt/_tools/picks.sh (outside the repository; not made here): line 11's case pattern becomes `test/test_wp3[3-9]_truth.cscript|test/test_wp4[0-9]_truth.cscript|test/test_wp31_truth.cscript)` with the same action (addmerge.py ours-first then blockorder.py); line 15's pattern becomes `BUGS.md|CHANGELOG.md|GAPS3.md|GAPS4.md|TWOWAY_COVERAGE_AUDIT.md)`. blockorder.py needs no change (its `^\* ==== S\d\d ` header regex reads S00). Report one proposed WE step for the index owner (D-33-01.i): "WE.2a: rewrite `local w<NN>_secs` in test/test_wp<NN>_truth.cscript from the WE.4 cert log's `S<MM> start`/`S<MM> end` lines (rounded up, at least 1), so the next WP's shards split by measured cost; the head-and-tail check ignores that statement". Also report the two group shas, the counts 221/221/70/52 and the 63 FIX_OVERRIDE ids. ]]></action>
  <verify><![CDATA[ The hand-back names both picks.sh lines, the WE.2a proposal, both shas, and that blockorder.py is unchanged. ]]></verify>
  <done>The orchestrator has what it needs to teach the merge tools GAPS4.md and the new truth scripts.</done>
</task>
```

## Section completion criteria

AC-33-01.1..5 hold; two commits on `wp33-s01`, subjects ending `(WP-33 33-01)`, no tooling names; `git status` clean apart from untracked scratch; the hand-back holds the picks.sh edits.

## Notes

- **Traps.** (0) A FIX_OVERRIDE text is the ruling, in the ruling's words; never write a remedy a ruling rejected (A-10). (1) Do not hand-edit GAPS4.md or the entries; rerunning N-1 `--write` refuses once GAPS4.md exists -- to redo, `git checkout BUGS.md && rm GAPS4.md`. (2) Paste the constants exactly as generated: one key per line, Appendix A order (later commits delete single lines; `addmerge.py drop` merges deletions). (3) Never write a cscript case id of the audit shape (`AX-4`); WP truth cases are `Q<NN><MM>-<k>` (PD-5). (4) The template run must start in `$WT/test` (the script reads its own blocks from the cwd and `do`es `../dash.ado`). (5) Under a strict run a skipped test is red: do not parametrise over an empty tuple (D-33-01.f).
- **Merge rules touched:** R1 (W0 for later WPs uses this template), R5, R10, R14.
- **Batch-mate 33-15.** It removes the size caps in the same batch and edits none of this section's files; plat:PT-7's and plat:PT-8's FIX_OVERRIDE rows already state P4-3's outcome, so neither section waits for the other. W0.2 for WP-34..49: `sed 's/@@WP@@/NN/g' test/templates/wp_truth_template.cscript > test/test_wpNN_truth.cscript`, then block 7x, the shard row and the three pins as here.
- **Commit body line forms:** `Regression: <node> -- failed at <base sha> with <text>`; `Flipped: <node> -- <old> was wrong because <why>`; `GAPS4: 221 rows registered Open`.
- **For 36-01:** the template carries WP-31's Python gate (`c(python_exec)` empty -> SKIP r(222)); when 36-01 changes the harness rule (M8, C5) it must change the template and every test_wpNN_truth.cscript made from it.

### N-1 `<scratch>/gen_gaps4.py` (write verbatim)

```python
"""gen_gaps4.py -- one-off writer of GAPS4.md, the 221 open BUGS.md entries
and the GAPS4_* constants (section 33-01).  Not committed: its output is.

    python3 gen_gaps4.py --repo <repo> --out <dir>           # dry run
    python3 gen_gaps4.py --repo <repo> --out <dir> --write   # into <repo>
"""
import argparse
import os
import re
import subprocess
import sys
import time

AUDIT = ".ultraplan/review/DROPIN-AUDIT-19oct2026.md"
INDEX = ".ultraplan/sections/index.md"
ID = r"(?:(?:plot|basic|stat|plat|syn|sil):)?[A-Z]{2,3}-\d{1,2}"
WITHDRAWN = ("plat:PT-3", "basic:PT-7", "plot:PT-10")
TITLE_OVERRIDE = {
    "LT-12": "clegend(title()) replaces the z title and prints the raw "
             "option text, quotes included, when it has sub-options",
    "LT-24": "title() whose text is an apostrophe and 90s inside double "
             "quotes is drawn where twoway gives r(100)",
    "MS-3": "yvarlabel() with an empty string gives the key 'scatter' and "
            "no title (twoway uses the variable name); yvarlabel relabels "
            "a variable in every plot in twoway, per layer in dash",
}
GONE = (".ultraplan/BASELINE.md", ".ultraplan/CHANGELOG.md", ".ultraplan/phases/")
# The audit's Fix line is its suggestion; where a ruling resolved the item
# otherwise (every Document or Partly row, the per-word rulings, P4-3,
# P4-5, A-5, a Fix row whose remedy a ruling rejected, and a P6-P10 or
# P14-P17 row whose Fix offered naming or documenting instead of drawing,
# M11/M12), the register states the ruling instead (DECISIONS A-10).
FIX_OVERRIDE = {
    "plot:PT-13": "Partly closed by ruling (D41, PD-9): Stata's own ticks "
                  "at build (34-09); the natscale misses after a filter move "
                  "stay open as the re-scoped natscale entry.",
    "DT-15": "Per the maintainer's per-word ruling (P4-7): the 25 "
             "second-axis forms (ytitle2() ... ttitle2()), malpha(), "
             "lalpha(), falpha(), marker(), jseed(), mlg(), plotbgcolor(), "
             "pbgc() and bw() read as barwidth() are refused with twoway's "
             "words and a second line naming twoway's spelling (P4-9); "
             "kernel() is read case-sensitively and xsize(()) is refused as "
             "twoway refuses them; a colorvar() layer whose if keeps no "
             "observation is answered as twoway answers it; hover() and "
             "table stay, listed as dash-only options in one help paragraph.",
    "plat:PT-5": "Documented only (Q47, M8): README and help state the "
                 "tested platform (macOS arm64, StataNow 19.5, console); no "
                 "code changes.",
    "plat:PT-2": "Documented only (Q46, M8): the Stata 19 floor stays; "
                 "README and help state that the drop-in claim is for "
                 "Stata 19 and later.",
    "plat:PT-11": "Documented only (Q49, M8): the help lists the "
                  "dependencies, and nothing else changes.",
    "plat:PT-12": "Documented only (Q33, M8): dash_setup's help states the "
                  "Pythons and platform tags the lock covers, and that "
                  "Python 3.15 and Windows ARM64 are not covered.",
    "plat:PT-6": "Documented only (Q47, M8): the tested-platform statement "
                 "covers it; saving()'s ~ expansion is not changed.",
    "plat:PT-16": "Documented only (M8): the help states that Chrome is "
                  "the browser dash is tested in.",
    "plat:PT-14": "Documented only (Q31, M8): page columns stay JSON number "
                  "lists; the help states the measured timings and memory "
                  "(about 6-8 s and 1.4 GB of Stata memory per million "
                  "rows).",
    "stat:PT-16": "Documented only (Q27, M9): the help describes the "
                  "zero-df difference accurately; Stata's compiled "
                  "round-off is not copied.",
    "DT-26": "Documented only (37-05): the help states each measured "
             "numeric limit (lpoly at degree 6-7 and above 7, the "
             "exact-polynomial cases, fpfit's date-time model choice, ndots "
             "thinning above 2,000,000).",
    "stat:PT-21": "Documented only (37-05): the help states that tied sort "
                  "keys keep data order, where twoway's order among ties is "
                  "unstable.",
    "syn:SD-17": "Documented only (M10): the help states that name() "
                 "registers the graph instead of drawing it and that "
                 "saving() beside name() writes nothing.",
    "GW-12": "Documented only (M10): the help states that a dashboard is "
             "not a Stata graph and names what cannot use it; no export "
             "command is added (PRD section 7).",
    "ECO-1": "Documented only (M10): the help states that a registered "
             "graph draws its frame's data as it is at dash build, not as "
             "it was at registration, and that a graph registered under "
             "frame f: (frame f: dash ..., name(), section 33-07) draws "
             "frame f, as twoway draws from the current frame.",
    "ECO-4": "Documented only (M10): the help maps graph combine's "
             "options onto layout() and names those dash build refuses.",
    "GW-13": "Documented only (M10): the help states name()'s limits (22 "
             "characters, no '__') and the rc and words a duplicate name "
             "gives.",
    "GW-14": "Documented only (M10): the help states the rc and words "
             "saving() onto an existing file gives.",
    "GW-15": "Documented only (M10): the help states that nodraw with "
             "saving(, asis) writes the page.",
    "GW-16": "Documented only (M10): the help states that play() is "
             "refused and that there is no Graph Editor.",
    "GW-9": "Documented only (M10): the help states the message a bad "
            "name() sub-option gives.",
    "ECO-5": "Documented only (M10): the help states that dash clear "
             "clears the whole registry and that there is no dir, describe "
             "or drop for registered items.",
    "ECO-15": "Documented only (M10): the help states that each one-line "
              "command opens a new browser page, that the newest five "
              "previews are kept, and that saving() opens none.",
    "ECO-7": "Documented only (M10): the help states which s() macros dash "
             "leaves.",
    "plat:PT-7": "Export only the rows some graph draws when no filter(), "
                 "link(), brush(), csv or KPI card needs every row and the "
                 "page is not served (Q45, A-12); with the embedded-cell cap "
                 "removed (P4-3, section 33-15) this keeps pages and data "
                 "files small and refuses nothing.",
    "plat:PT-8": "Documented (M10, Q44, P4-3): the embedded-cell cap is "
                 "removed (section 33-15), so a dashboard has no size cap "
                 "and the help says so; the count caps (100 plots, 10,000 "
                 "reference lines, 1,000 added texts) stay and are "
                 "documented under Resource limits and Differences.",
    "plat:PT-9": "Documented only (M10, Q44): the per-graph plot limit "
                 "stays and is documented under Resource limits and "
                 "Differences.",
    "plat:PT-10": "Documented only (M10, Q44): by()'s group limit stays and "
                  "is documented under Resource limits and Differences.",
    "stat:PT-15": "Documented only (M10, Q44): the n(), bin() and degree() "
                  "bounds stay and are documented under Resource limits and "
                  "Differences.",
    "sil:SD-1": "Documented only (M10, Q44): the 1,000-bin bound and its "
                "rebinning stay and are documented under Resource limits "
                "and Differences.",
    "AX-16": "Documented only (M10, Q44): the 2,000-tick bound stays and "
             "is documented under Resource limits and Differences.",
    "sil:SD-11": "Documented only (M10, Q44): the 1,000-unit msize() bound "
                 "stays; the help and the note's wording are corrected.",
    "sil:SD-12": "Documented only (M10, Q44): the 20,000-point fpfit grid "
                 "stays and is documented under Resource limits and "
                 "Differences.",
    "sil:SD-13": "Documented only (M10, Q44): the 4,000-character bound on "
                 "text() after its globals expand stays and is documented "
                 "under Resource limits and Differences.",
    "CV-14": "Per the maintainer's per-word ruling (P4-7): a string "
             "colorvar() is refused r(7), and colpalette(), colornlevels(), "
             "colormissing(), cv() and colv() are refused with twoway's "
             "words and a second line naming twoway's spelling (P4-9); an "
             "empty colorvar() layer and an all-missing colorvar() are "
             "answered as twoway answers them; the entry closes naming the "
             "kept and the refused words (A-12).",
    "RH-8": "Documented only (Q25, M12): dash keeps its clean transpose; "
            "twoway's broken picture is listed under Differences with a "
            "measured example.",
    "DT-28": "Documented only (48-02): reviewed and needing no change; the "
             "help says so.",
    "LT-24": "Refuse option text with an unbalanced quote with twoway's "
             "measured rc and words (r(100), r(109) or r(198) by form); "
             "quotes inside if qualifiers and compound-quoted text keep "
             "today's handling (P4-5).",
    "AX-11": "Natscale over all finite values, then drop those at or below "
             "zero; twoway's degenerate picture for non-positive data on a "
             "log axis is documented under Differences, as RH-8 is (A-5).",
    "AX-13": "Draw orientation(), margins and justification; the boxed "
             "right-hand axis title takes the overlay route, with no "
             "residual (A-5).",
    "AX-15": "Per M11 (section 44-02): draw each part as twoway draws it "
             "with Bokeh's shipped models and CustomJS, no custom glyph "
             "model; the dates past the browser's range and the reference "
             "line off the canvas stay documented differences, and the "
             "item closes Documented (A-5).",
    "plat:PT-1": "Per M8 (C5): no pre-check of Python and no python query "
                 "probe; when c(python_exec) is empty, dash and dash_setup "
                 "run the normal python: path and show Stata's own failure "
                 "with dash's advice; the fresh-HOME test is a release-tier "
                 "pytest through scripts/stata_slot.sh (A-8).",
    "plot:PT-7": "Per Q43/M12 (PD-11): the first line of every refusal is "
                 "twoway's words naming the option as typed; dash's second "
                 "and later lines and the Supported list stay.",
    "TR-13": "Per M9: contour comes from twoway__contour_gen, run at "
             "export, when the data is a full grid or interp(none); "
             "scattered data above 1,000 points keeps the subsample and "
             "its note.",
    "plat:PT-4": "Per A-7: the function points of a named graph go to a "
                 "private file under dash's temp folder, keyed by graph "
                 "name; fix the message and the help.",
    "VF-4": "Per A-1: every graph keeps twoway's shape (the "
            "xsize()/ysize() ratio, else the scheme's graph size), the "
            "width fills its cell, the 160-560 px band is removed, and "
            "relative sizes scale with the scheme's graph size.",
    "plot:PT-3": "Per M7: plot-type names are read in lower case only; "
                 "capitalised spellings are refused as twoway refuses them.",
    "syn:SD-13": "Per M7: accept the option-less form, as twoway draws it.",
    "TR-2": "Per M5, P4-8 and A-25: make corpus judges every corpus "
            "example by geometry and glyph colours (within a recorded RGB "
            "tolerance), with an image score and a known-differences "
            "ledger; a ~20-example guard runs in cert; the gallery is "
            "built only at the final closeout.",
    "TR-23": "Convert TestBounds so it runs (R9: pinned tests are never "
             "deleted); run make test-all once and record it.",
    "DG-1": "Per M9 (PD-15): one Stata-side zero-observation check copies "
            "twoway's measured answer per type and case.",
    "BY-1": "Draw them inside the panel array at their clock; add truth "
            "probes (M11: every P6-P10 item is drawn, none only named).",
    "AX-9": "Draw the transforms (M11: every P6-P10 item is drawn).",
    "AX-12": "Accept the plurals; draw the ticks and labels on the key "
             "(M11: every P6-P10 item is drawn).",
    "LT-3": "Draw them (M11: every P6-P10 item is drawn, none only named).",
    "LT-6": "Implement them on the Legend (M11: every P6-P10 item is "
            "drawn).",
    "LT-7": "Draw the expanded box (M11: every P6-P10 item is drawn).",
    "LT-15": "Apply them (M11: every P6-P10 item is drawn, none only "
             "named).",
    "LT-18": "Draw them (M11: every P6-P10 item is drawn).",
    "ST-16": "Note and draw s2color, as twoway does (M11: every P6-P10 "
             "item is fixed).",
    "basic:PT-4": "Inset or outset closed shapes by half the width; round "
                  "cap ends (M12: resolved by drawing).",
    "basic:PT-6": "Measure diameters; compensate size (M12: resolved by "
                  "drawing).",
    "basic:PT-11": "Draw them (M12: resolved by drawing).",
}
# Words ruling M1 bars from every register text, checked after the
# overrides (R14).  Contour's own heatmap option stays in scope.
BANNED = re.compile(r"sunflower|\bheatmap\b(?!\s+option)", re.I)
AUDIT_AT = "f81cd31"


def die(msg):
    sys.exit("gen_gaps4: " + msg)


def appendix(index_text):
    lines = index_text.split("\n")
    s = lines.index("## Appendix A -- every audit item, binding for 33-01")
    e = lines.index("## Appendix B -- the audit's false sentences (PD-8)")
    rows, heads, wp = [], {}, None
    for ln in lines[s:e]:
        m = re.match(r"^### (WP-\d\d) · (.+)$", ln)
        if m:
            wp = m.group(1)
            heads[wp] = m.group(2)
            continue
        m = re.match(r"^\| (\S+) \| (.+?) \| (.+) \| (S[1-3]|--) \| (\S+) \| (.+) \|$", ln)
        if m and m.group(1) != "Lead id":
            lead, other, _item, sev, sec, kind = m.groups()
            if kind.startswith("Withdrawn"):
                if lead not in WITHDRAWN:
                    die("unexpected withdrawn row " + lead)
                continue
            if not re.match(r"^\d\d-\d\d$", sec) or sec[:2] != wp[3:]:
                die("%s: section %s is not in %s" % (lead, sec, wp))
            rows.append(dict(wp=wp, lead=lead, other=other, sev=sev,
                             sec=sec, kind=kind))
    return rows, heads


def bullets(audit_text):
    lines = audit_text.split("\n")
    end = next(i for i, l in enumerate(lines)
               if l.startswith("## Help and README wording"))
    out, pkg, grade = {}, None, None
    for i in range(end):
        m = re.match(r"^### (\d+)\. .+ \((blocker|major|minor|cosmetic), effort \w+\)$", lines[i])
        if m:
            pkg, grade = int(m.group(1)), m.group(2)
            continue
        m = re.match(r"^- \*\*(.+?)\*\* \[(.+?)\]$", lines[i])
        if not m:
            continue
        head, _sep, status = m.group(2).partition("; ")
        ids = head.split(", ")
        ev = fx = None
        j = i + 1
        while j < end and lines[j].startswith("  - "):
            if lines[j].startswith("  - Evidence: "):
                ev = lines[j][len("  - Evidence: "):]
            elif lines[j].startswith("  - Fix: "):
                fx = lines[j][len("  - Fix: "):]
            j += 1
        if ids[0] in out:
            die("lead id %s twice in the audit" % ids[0])
        if not (ev and fx):
            die("%s: no Evidence or Fix line" % ids[0])
        out[ids[0]] = dict(title=m.group(1), ids=ids, status=status,
                           ev=ev, fx=fx, pkg=pkg, grade=grade)
    return out


def cell(s):
    return s.replace("|", "\\|")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    read = lambda p: open(os.path.join(a.repo, p), encoding="utf-8").read()
    rows, heads = appendix(read(INDEX))
    bul = bullets(read(AUDIT))
    if len(rows) != 221 or len(bul) != 221:
        die("%d Appendix A rows and %d audit bullets, not 221 and 221"
            % (len(rows), len(bul)))
    bugs = read("BUGS.md")
    old_titles = set(re.findall(r"^- \[[ x]\] Title: (.+)$", bugs, re.M))
    titles = {}
    for r in rows:
        b = bul.get(r["lead"])
        if b is None:
            die("no audit bullet for " + r["lead"])
        other = [] if r["other"] == "--" else [x.strip() for x in r["other"].split(", ")]
        if other != b["ids"][1:]:
            die("%s: other ids %s against the audit's %s" % (r["lead"], other, b["ids"][1:]))
        if not re.match("^%s$" % ID, r["lead"]):
            die("lead id %r is outside the id grammar" % r["lead"])
        t = TITLE_OVERRIDE.get(r["lead"], b["title"])
        if '"' in t:
            die("%s: title holds a double quote" % r["lead"])
        if t in old_titles or t in titles.values():
            die("%s: title is not unique" % r["lead"])
        titles[r["lead"]] = t
        if r["kind"] != "Fix" and r["lead"] not in FIX_OVERRIDE:
            die("%s: Kind %s needs a FIX_OVERRIDE" % (r["lead"], r["kind"]))
        fx = FIX_OVERRIDE.get(r["lead"], b["fx"])
        text = " ".join((t, b["ev"], fx, b["status"]))
        if BANNED.search(text) or any(g in text for g in GONE):
            die("%s: banned word or gone path in its text" % r["lead"])
        r.update(b=b, title=t, fx=fx)
    unknown = sorted(set(FIX_OVERRIDE) - {r["lead"] for r in rows})
    if unknown:
        die("FIX_OVERRIDE names ids that are not registered: %s" % unknown)
    # The day and the commit the register is written on (the worktree's
    # base), never typed: the section runs on whatever base s3-bugs has.
    when = time.strftime("%d%b%Y").lower()
    head = subprocess.run(["git", "-C", a.repo, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    if not re.match(r"^[0-9a-f]{7,40}$", head):
        die("git rev-parse --short HEAD gave %r in %s" % (head, a.repo))
    g = ["# GAPS4 -- the drop-in audit of 19oct2026, registered", "",
         "*Every live item of `.ultraplan/review/DROPIN-AUDIT-19oct2026.md` "
         "as committed at `%s` (audited at `7dced3a`), under the maintainer's "
         "rulings D40 and D41, "
         "registered for the WP-33..WP-49 plan (`.ultraplan/sections/index.md`, "
         "Appendix A). Written %s at `%s` by section 33-01. Three "
         "audit items were withdrawn by rulings Q48, Q50 and A2 and are not "
         "registered.*" % (AUDIT_AT, when, head), "",
         "One row per item, keyed by its first id (the lead id); the item's "
         "other ids follow its text. Sev: S1 for audit package 1, S2 for "
         "packages 2-13, S3 for packages 14-17 (index PD-2). Section: the plan "
         "section that resolves the item. Kind: Fix, Document, Partly, or the "
         "per-word ruling form. Evidence is the audit's; Fix is the audit's "
         "suggestion, or the ruling that resolved the item where one did "
         "(every Document and Partly row, and each Fix row whose suggestion "
         "a ruling replaced).", ""]
    for wp in heads:
        mine = [r for r in rows if r["wp"] == wp]
        if not mine:
            continue
        g += ["## %s · %s" % (wp, heads[wp]), "",
              "| ID | Item | Sev | Section | Kind | Evidence | Fix |",
              "|---|---|---|---|---|---|---|"]
        for r in mine:
            item = r["title"] + (" (also %s)" % ", ".join(r["b"]["ids"][1:])
                                 if len(r["b"]["ids"]) > 1 else "")
            g.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                r["lead"], cell(item), r["sev"], r["sec"], r["kind"],
                cell(r["b"]["ev"]), cell(r["fx"])))
        g.append("")
    g += ["## Tracking", "",
          "One line per row, rewritten in place by the item's closing commit; "
          "test/test_tracking_documents.py::TestGaps4Tracking reads exactly "
          "these forms: `Open (WP-NN section NN-MM).`, `Closed in WP-NN, "
          "BUGS.md \"<title>\", commit <sha>.`, `Documented in WP-NN, BUGS.md "
          "\"<title>\", commit <sha>.`, or `Partly closed in WP-NN (section "
          "NN-MM, commit <sha>): <what is closed>; open: <what remains> "
          "(BUGS.md \"<residual title>\").` A closing commit writes `commit "
          "pending`; the merger's step k.3b replaces it with the landed sha.", ""]
    g += ["- **%s Tracked:** Open (%s section %s)." % (r["lead"], r["wp"], r["sec"])
          for r in rows]
    gaps4 = "\n".join(g) + "\n"
    ents = []
    for r in rows:
        b = r["b"]
        ents.append("\n".join((
            "- [ ] Title: " + r["title"],
            "  - File Names and Line Numbers: " + b["ev"],
            "  - Description: Drop-in audit of 19oct2026 "
            "(.ultraplan/review/DROPIN-AUDIT-19oct2026.md at commit %s), "
            "package %d (%s): "
            "ids %s; %s. Registered as GAPS4 %s (%s, section %s, %s)."
            % (AUDIT_AT, b["pkg"], b["grade"], ", ".join(b["ids"]), b["status"],
               r["lead"], r["wp"], r["sec"], r["kind"]),
            "  - Suggested fix: " + r["fx"],
            "  - Resolution: Not fixed because %s section %s has not landed. "
            "Graded %s (%s): drop-in audit package %d, %s."
            % (r["wp"], r["sec"], r["sev"], r["wp"], b["pkg"], b["grade"]))))
    append = "\n" + "\n\n".join(ents) + "\n"
    if not bugs.endswith("\n"):
        die("BUGS.md does not end with a newline")
    q = repr
    c = ["GAPS4_OPEN = {"] + ["    %s: %s," % (q(r["lead"]), q(r["title"])) for r in rows] + ["}", ""]
    c += ["GAPS4_WP = {"] + ["    %s: %s," % (q(r["lead"]), q(r["wp"])) for r in rows] + ["}", ""]
    c += ["GAPS4_SECTION = {"] + ["    %s: %s," % (q(r["lead"]), q(r["sec"])) for r in rows] + ["}", ""]
    os.makedirs(a.out, exist_ok=True)
    for name, text in (("GAPS4.md", gaps4), ("bugs_append.md", append),
                       ("gaps4_constants.py", "\n".join(c))):
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    if a.write:
        if os.path.exists(os.path.join(a.repo, "GAPS4.md")):
            die("GAPS4.md exists already; this writer runs once")
        with open(os.path.join(a.repo, "GAPS4.md"), "w", encoding="utf-8") as fh:
            fh.write(gaps4)
        with open(os.path.join(a.repo, "BUGS.md"), "a", encoding="utf-8") as fh:
            fh.write(append)
    print("gen_gaps4: %d rows, %d entries, %d WPs%s" % (
        len(rows), len(ents), len({r["wp"] for r in rows}),
        "; written" if a.write else "; dry run"))


if __name__ == "__main__":
    main()
```

Measured on f81cd31 (index.md as revised in Phase 4) in a scratch dry run of this exact text, 20oct2026: `gen_gaps4: 221 rows, 221 entries, 16 WPs; dry run`; GAPS4.md 532 lines, its header naming the run's date and `f81cd31`; BUGS.md gains 1,326 lines (969 entries, 222 open); 63 FIX_OVERRIDE rows (D-33-01.h's list); 32 Fix cells begin `Documented only`; the BANNED check (M1's words) passes over every text after the overrides.

### N-2 code appended to test/test_tracking_documents.py (after the three dicts)

```python
GAPS4_ALL = tuple(GAPS4_WP)

#: The WPs whose closeout (step WE.2) has run, in run order; each WE
#: appends its own (TestGaps4Tracking::test_every_closed_wp_is_closed).
GAPS4_CLOSED_WPS = ()

#: WP -> the commit that recorded its closeout counts (WE.2's follow-up
#: commit); test_the_gaps4_closeout_counts_are_computed recomputes them.
GAPS4_CLOSEOUT = {}

_GAPS4_WPS = ("WP-33", "WP-34", "WP-35", "WP-36", "WP-37", "WP-38",
              "WP-40", "WP-41", "WP-42", "WP-43", "WP-44", "WP-45",
              "WP-46", "WP-47", "WP-48", "WP-49")
_GAPS4_WITHDRAWN = ("plat:PT-3", "basic:PT-7", "plot:PT-10")
_GAPS4_ID = r"(?:(?:plot|basic|stat|plat|syn|sil):)?[A-Z]{2,3}-\d{1,2}"
_GAPS4_KINDS = ("Fix", "Document", "Partly", "Fix per the Q8 per-word ruling",
                "Fix or Document per the Q8 per-word ruling")
_GAPS4_ROW = re.compile(
    r"^\| (?P<id>%s) \| (?P<item>.+?) \| (?P<sev>S[1-3]) \| "
    r"(?P<sec>\d{2}-\d{2}) \| (?P<kind>%s) \| "
    % (_GAPS4_ID, "|".join(re.escape(k) for k in _GAPS4_KINDS)))
_GAPS4_TRACKED = re.compile(
    r"^- \*\*(?P<id>%s) Tracked:\*\* (?P<text>\S.*)$" % _GAPS4_ID)
_GAPS4_OPEN = re.compile(r"^Open \((WP-\d{2}) section (\d{2}-\d{2})\)\.$")
_GAPS4_CLOSED = re.compile(
    r'^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40}|pending)\.$')
_GAPS4_DOCUMENTED = re.compile(
    r'^Documented in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40}|pending)\.$')
_GAPS4_PARTLY = re.compile(
    r"^Partly closed in (WP-\d{2}) \(section (\d{2}-\d{2}), commit "
    r'([0-9a-f]{7,40}|pending)\): (\S.*); open: (\S.*) \(BUGS\.md "([^"]+)"\)\.$')
_GAPS4_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because (WP-\d{2}) section (\d{2}-\d{2}) "
    r"has not landed\. Graded (S[1-3]) \((WP-\d{2})\): \S")
_GAPS4_ENTRIES_LINE = re.compile(
    r"^- \*\*Entries\.\*\* (?P<all>\d+) (?P<wp>WP-\d{2}) entries; "
    r"(?P<closed>\d+) closed, (?P<documented>\d+) documented, "
    r"(?P<partly>\d+) partly closed; BUGS\.md holds (?P<open>\d+) open "
    r"entries\.$", re.M)


def _parse_gaps4(text):
    """(rows, tracked, dupes): rows {id: {"sev", "sec", "kind"}}, tracked
    {id: Tracked text}, dupes the ids with two rows or two Tracked lines."""
    rows, tracked, dupes = {}, {}, []
    for ln in text.split("\n"):
        m = _GAPS4_ROW.match(ln)
        if m:
            if m.group("id") in rows:
                dupes.append(m.group("id"))
            rows[m.group("id")] = {"sev": m.group("sev"),
                                   "sec": m.group("sec"),
                                   "kind": m.group("kind")}
        t = _GAPS4_TRACKED.match(ln)
        if t:
            if t.group("id") in tracked:
                dupes.append(t.group("id"))
            tracked[t.group("id")] = t.group("text")
    return rows, tracked, dupes


def _gaps4_open_problems(open_map, entries, rows):
    """Each GAPS4_OPEN title is one open entry in the open form naming the
    id's WP and section, graded with its row's Sev."""
    unknown = sorted(set(open_map) - set(GAPS4_ALL))
    bad = ["ids GAPS4 does not have: %s" % unknown] if unknown else []
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
            bad.append("%s: %r is closed; delete its GAPS4_OPEN key"
                       % (pid, title))
            continue
        m = _GAPS4_OPEN_FORM.match(e["fields"].get("Resolution", ""))
        want = (GAPS4_WP.get(pid), GAPS4_SECTION.get(pid),
                (rows.get(pid) or {}).get("sev"), GAPS4_WP.get(pid))
        if not m:
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-NN "
                       "section NN-MM has not landed. Graded S<n> (WP-NN): "
                       "...'" % (pid, title))
        elif m.groups() != want:
            bad.append("%s: its Resolution names %s, not %s"
                       % (pid, m.groups(), want))
    return bad


def _gaps4_closure_problems(open_ids, entries):
    """Every id no longer open has a closed entry naming (WP-NN, <id>)."""
    bad = []
    for pid in GAPS4_ALL:
        if pid in open_ids:
            continue
        tag = "(%s, %s)" % (GAPS4_WP[pid], pid)
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _gaps4_problems(rows, tracked, dupes, open_ids, entries, sha_exists):
    """Every id has one row in its own section and one Tracked line in one
    of PD-3's four forms, consistent with BUGS.md."""
    bad = ["%s has two Tracked lines or two rows" % d for d in dupes]
    bad += ["GAPS4.md names %s, which GAPS4 does not have" % t
            for t in sorted((set(tracked) | set(rows)) - set(GAPS4_ALL))]
    for pid in GAPS4_ALL:
        wp, sec = GAPS4_WP[pid], GAPS4_SECTION[pid]
        if pid not in rows:
            bad.append("%s: GAPS4.md has no table row for it" % pid)
        elif rows[pid]["sec"] != sec:
            bad.append("%s: its row names section %s, not %s"
                       % (pid, rows[pid]["sec"], sec))
        if pid not in tracked:
            bad.append("%s: GAPS4.md has 0 Tracked lines" % pid)
            continue
        text = tracked[pid]
        o, c = _GAPS4_OPEN.match(text), _GAPS4_CLOSED.match(text)
        d, p = _GAPS4_DOCUMENTED.match(text), _GAPS4_PARTLY.match(text)
        if o:
            if o.groups() != (wp, sec):
                bad.append("%s: Open names %s section %s, not %s section %s"
                           % ((pid,) + o.groups() + (wp, sec)))
            if pid not in open_ids:
                bad.append("%s: Tracked Open but its entry is closed" % pid)
        elif c or d:
            m, form = (c, "Closed") if c else (d, "Documented")
            if m.group(1) != wp:
                bad.append("%s: %s names %s, not %s" % (pid, form, m.group(1), wp))
            if pid in open_ids:
                bad.append("%s: Tracked %s but its entry is open" % (pid, form))
            hits = [e for e in entries if e["closed"] and e["title"] == m.group(2)]
            if not hits:
                bad.append("%s: no closed BUGS.md entry is titled %r"
                           % (pid, m.group(2)))
            elif d and not any(e["fields"].get("Resolution", "").startswith(
                    "  - Resolution: Documented ") for e in hits):
                bad.append("%s: Tracked Documented but %r's Resolution does "
                           "not begin 'Documented'" % (pid, m.group(2)))
            if m.group(3) != "pending" and not sha_exists(m.group(3)):
                bad.append("%s: commit %s does not exist" % (pid, m.group(3)))
        elif p:
            if p.group(1) != wp or p.group(2) != sec:
                bad.append("%s: Partly names %s section %s, not %s section %s"
                           % (pid, p.group(1), p.group(2), wp, sec))
            if pid in open_ids:
                bad.append("%s: Tracked Partly but its entry is open" % pid)
            if p.group(3) != "pending" and not sha_exists(p.group(3)):
                bad.append("%s: commit %s does not exist" % (pid, p.group(3)))
            if not [e for e in entries if not e["closed"]
                    and e["title"] == p.group(6)]:
                bad.append("%s: no open BUGS.md entry is titled %r"
                           % (pid, p.group(6)))
        else:
            bad.append("%s: Tracked line %r is in none of the four forms"
                       % (pid, text))
    return bad


def _gaps4_closeout_counts(wp, bugs_text, gaps4_text):
    """The counts a WP's ROADMAP.md "Entries." line states, computed from
    BUGS.md and GAPS4.md as they were at its closeout commit."""
    entries, _p = _parse_bugs(bugs_text)
    _rows, tracked, _d = _parse_gaps4(gaps4_text)
    lines = [tracked.get(pid, "") for pid in GAPS4_ALL if GAPS4_WP[pid] == wp]
    return {"all": len(lines), "wp": wp,
            "closed": sum(1 for t in lines if t.startswith("Closed in ")),
            "documented": sum(1 for t in lines if t.startswith("Documented in ")),
            "partly": sum(1 for t in lines if t.startswith("Partly closed in ")),
            "open": sum(1 for e in entries if not e["closed"])}


def _roadmap_gaps4_counts(roadmap, wp):
    """The counts ROADMAP.md's "Entries." line for *wp* states, or {}."""
    for m in _GAPS4_ENTRIES_LINE.finditer(roadmap):
        if m.group("wp") == wp:
            return {k: (v if k == "wp" else int(v))
                    for k, v in m.groupdict().items()}
    return {}
```

### N-3 docstring item 12 and class TestGaps4Tracking

Docstring item 12 (insert after line 78, before the blank line that ends the list): `12. The drop-in audit's items (GAPS4.md, .ultraplan/sections/index.md PD-1..PD-4) are open in BUGS.md in the form "Not fixed because WP-NN section NN-MM has not landed. Graded S<n> (WP-NN): ...", listed in GAPS4_OPEN, which exempts them from the release guard, and tracked "Open (WP-NN section NN-MM)." in GAPS4.md's Tracking section, until their section lands; then the key is gone, the Tracked line reads Closed, Documented or Partly closed, and a closed Resolution holds "(WP-NN, <id>)". Each WP's closeout appends it to GAPS4_CLOSED_WPS and records its counts (GAPS4_CLOSEOUT).`

`class TestGaps4Tracking:` (docstring: one line naming PD-1..PD-4) with these methods, each body exactly as described:

1. `test_the_register_holds_every_item(self)`: `rows, tracked, dupes = _parse_gaps4(_read("GAPS4.md"))`; assert `len(GAPS4_ALL) == 221` (comment `# index.md Appendix A: 224 printed, 3 withdrawn`), `tuple(GAPS4_SECTION) == GAPS4_ALL` and `set(GAPS4_OPEN) <= set(GAPS4_ALL)` (GAPS4_OPEN shrinks as items close; never compare it with GAPS4_ALL for equality); `set(GAPS4_WP.values()) == set(_GAPS4_WPS)`; every id matches `^%s$ % _GAPS4_ID`; every section matches `^\d{2}-\d{2}$` and `GAPS4_SECTION[pid][:2] == GAPS4_WP[pid][3:]`; `set(rows) == set(GAPS4_ALL)` and `not dupes`; for each `w` in `_GAPS4_WITHDRAWN`: `w not in GAPS4_WP` and `not re.search(r"(?<![\w:])%s(?!\d)" % re.escape(w), _read("GAPS4.md"))`.
2. `test_every_allowed_title_is_an_open_entry(self, bugs)`: `entries, _p = bugs`; `rows, _t, _d = _parse_gaps4(_read("GAPS4.md"))`; `bad = _gaps4_open_problems(GAPS4_OPEN, entries, rows)`; `assert not bad, "\n".join(bad)`.
3. `test_a_closed_entry_names_its_closure(self, bugs)`: `assert not _gaps4_closure_problems(set(GAPS4_OPEN), bugs[0])` (message joined).
4. `test_every_item_has_one_tracked_line(self, bugs)`: `rows, tracked, dupes = _parse_gaps4(_read("GAPS4.md"))`; `bad = _gaps4_problems(rows, tracked, dupes, set(GAPS4_OPEN), bugs[0], _sha_exists)`; assert not bad.
5. `test_every_closed_wp_is_closed(self, bugs)`: `_r, tracked, _d = _parse_gaps4(_read("GAPS4.md"))`; for `wp in GAPS4_CLOSED_WPS`: `bad += [pid for pid in GAPS4_OPEN if GAPS4_WP[pid] == wp]`; `bad += ["%s: %s" % (pid, t) for pid, t in tracked.items() if GAPS4_WP.get(pid) == wp and (_GAPS4_OPEN.match(t) or "commit pending" in t)]`; `bad += [e["title"] for e in bugs[0] if not e["closed"] and e["fields"].get("Resolution", "").startswith("  - Resolution: Not fixed because %s section" % wp)]`; assert not bad. (Passes trivially while the tuple is empty; D-33-01.f.)
6. `test_the_gaps4_closeout_counts_are_computed(self)`: for `wp, sha in GAPS4_CLOSEOUT.items()`: `stated = _roadmap_gaps4_counts(_git("show", sha + ":ROADMAP.md").stdout, wp)`; `got = _gaps4_closeout_counts(wp, _git("show", sha + ":BUGS.md").stdout, _git("show", sha + ":GAPS4.md").stdout)`; assert `stated == got`, (wp, stated, got). Use the module's existing `_git` helper (:836).
7. `test_the_gaps4_readers(self)`: a synthetic GAPS4 text with one table row `| AX-4 | t \| u | S1 | 34-01 | Fix | e | f |`, one `| plat:PT-1 | x | S2 | 36-01 | Fix | e | f |` and Tracked lines `- **AX-4 Tracked:** Open (WP-34 section 34-01).`, `- **plat:PT-1 Tracked:** Closed in WP-36, BUGS.md "T2", commit 0123abc.`; assert `_parse_gaps4` returns rows for both ids with sec 34-01/36-01, both tracked texts, no dupes; then, as `test_the_gaps3_readers` does (:2567-2614), fill `tracked_all = {pid: "Open (%s section %s)." % (GAPS4_WP[pid], GAPS4_SECTION[pid]) for pid in GAPS4_ALL}` and `rows_all = {pid: {"sev": "S2", "sec": GAPS4_SECTION[pid], "kind": "Fix"} for pid in GAPS4_ALL}`, override plat:PT-1 with the Closed line and entries `[{"title": "T2", "closed": True, "fields": {}}, {"title": "R1", "closed": False, "fields": {}}]`, and assert: `_gaps4_problems(rows_all, tracked_all, [], set(GAPS4_ALL) - {"plat:PT-1"}, entries, lambda s: s == "0123abc") == []`; with `open_ids = set(GAPS4_ALL)` and `lambda s: False` the result holds `"plat:PT-1: Tracked Closed but its entry is open"` and `"plat:PT-1: commit 0123abc does not exist"`; a Partly line `Partly closed in WP-36 (section 36-01, commit pending): x; open: y (BUGS.md "R1").` passes with plat:PT-1 not open; a Documented line naming T2 whose Resolution is `  - Resolution: Fixed ...` reports `Resolution does not begin 'Documented'`; `Open (WP-35 section 36-01).` reports `Open names WP-35 section 36-01, not WP-36 section 36-01`; dropping AX-4's row reports `AX-4: GAPS4.md has no table row for it`.
8. `test_the_gaps4_problem_readers(self)`: as `test_the_wp31_problem_readers` (:2532-2566): `open_form = "Not fixed because WP-34 section 34-01 has not landed. Graded S1 (WP-34): drop-in audit package 1, blocker."`; `entry(title, closed, res)` builds `{"title", "closed", "fields": {"Resolution": "  - Resolution: " + res}}`; `rows = {"AX-4": {"sev": "S1", "sec": "34-01", "kind": "Fix"}}`; `_gaps4_open_problems({"AX-4": "T1"}, [entry("T1", False, open_form)], rows) == []`; then each of: title of a closed entry -> "is closed"; missing title -> "0 BUGS.md entries"; `open_form.replace("34-01", "34-02")` -> "its Resolution names"; `{"ZZ-9": "T1"}` -> "does not have"; a title with `"` -> "double quote"; and `_gaps4_closure_problems(set(GAPS4_ALL) - {"AX-4"}, [entry("T2", True, "Fixed 01nov2026 (WP-34, AX-4). Done.")]) == []`, while with no such entry it returns `["AX-4 is closed and no closed BUGS.md entry's Resolution holds (WP-34, AX-4)"]`.
9. `test_the_count_reader(self)`: `line = "- **Entries.** 11 WP-34 entries; 9 closed, 0 documented, 1 partly closed; BUGS.md holds 12 open entries."`; assert `_roadmap_gaps4_counts("x\n" + line + "\n", "WP-34") == {"all": 11, "wp": "WP-34", "closed": 9, "documented": 0, "partly": 1, "open": 12}` and `_roadmap_gaps4_counts(line, "WP-35") == {}`.

### N-4 replaces `_wp31_blocks` in test/test_cscript_hygiene.py (:1227-1275)

```python
_W_MARK = "* ==== append new blocks above this line ===="
_W_GAPS4_ID = r"(?:(?:plot|basic|stat|plat|syn|sil):)?[A-Z]{2,3}-\d{1,2}"
_W_HEAD = re.compile(r"^(scaffold|tool|%s): \S" % _W_GAPS4_ID)


def _wp_blocks(src, wp, head=_W_HEAD, row="GAPS4 row"):
    """(blocks, bad) of WP-<wp>'s truth script: one marker; each block
    `* ==== S<MM> <head> ====` .. `* ==== end S<MM> ====` above it, gated by
    WP<wp>_ONLY and w<wp>_run, printing its start line first and its end
    line last, in non-decreasing section order.  blocks are (S<MM>, first
    line, last line, header text)."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W_MARK, len(marks)))
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
                blocks.append((cur[0], cur[1], n, cur[2]))
                if not head.match(cur[2]):
                    bad.append("%s (line %d) names no %s ('<id>: <what>')"
                               % (cur[0], cur[1], row))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur[:2])
    for k, (sec, first, last, _h) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1]
                if ln.strip() and not ln.strip().startswith(("//", "*"))]
        if code[:2] != ["local only : env WP%s_ONLY" % wp,
                        'if inlist("`only\'", "", "%s") & `: list posof '
                        '"%s" in w%s_run\' {' % (sec, sec, wp)]:
            bad.append("%s (line %d) is not gated by WP%s_ONLY=%s"
                       % (sec, first, wp, sec))
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


def _wp31_blocks(src):
    """WP-31's reader: _wp_blocks with its GAPS3 head; blocks as
    (S<NN>, first line, last line)."""
    blocks, bad = _wp_blocks(src, "31", head=_W31_HEAD, row="GAPS3 row")
    return [b[:3] for b in blocks], bad
```

Measured in scratch: on test_wp31_truth.cscript the wrapper returns exactly what the old reader returned (110 blocks, no problem), and `TestTheWp31TruthScript::test_the_block_reader` passes against it. `_W31_MARK` stays (the WP-31 class reads it).

### N-5 class TestTheWpTruthScripts (append at the end of test_cscript_hygiene.py)

Module constants above it: `_WP_TEMPLATE = os.path.join(_HERE, "templates", "wp_truth_template.cscript")`; `_WP_TRUTHS = sorted(p for p in glob.glob(os.path.join(_HERE, "test_wp*_truth.cscript")) if re.search(r"test_wp(3[3-9]|4[0-9])_truth\.cscript$", p))`; `def _wp_of(path): return re.search(r"test_wp(\d{2})_truth\.cscript$", path).group(1)`; `_SECS = re.compile(r"^local w\d\d_secs[^\n]*(?:\n    [^\n]*)*\n", re.M)` (the seconds statement and its `///` continuation lines, D-33-01.i); `def _head_and_tail(text): i = text.index("* ==== end S00 ====\n") + len("* ==== end S00 ====\n"); j = text.index(_W_MARK); return _SECS.sub("", text[:i], count=1), text[j:]`. Import the register inside the one test that needs it: `sys.path.insert(0, _HERE); import test_tracking_documents as T` (add `import sys` at the top of the file if absent).

Methods: (1) `test_the_template_and_the_wp33_script_exist`: `os.path.isfile(_WP_TEMPLATE)` and `"test_wp33_truth.cscript" in [os.path.basename(p) for p in _WP_TRUTHS]`. (2) `@pytest.mark.parametrize("path", _WP_TRUTHS, ids=os.path.basename)` `test_the_scaffold_is_in_order(path)`: wp = `_wp_of(path)`; order `['cscript "WP-%s truth' % wp, "SKIP: Python not available.", 'do "cert_helpers.do"', 'do "cert_svg.do"', "// ---- parts: begin", "local w%s_sh : environment DASH_CERT_SHARD" % wp, "// ---- parts: end", "* ==== S00 ", "local only : env WP%s_ONLY" % wp, "* ==== end S00 ====", _W_MARK, "has no block to run", "test_wp%s_truth: ALL CHECKS PASSED" % wp]`; positions found and sorted (as :1280-1292); `"capture python:" not in text`. (3) parametrised `test_every_block_is_gated_timed_closed_and_in_section_order(path)`: `blocks, bad = _wp_blocks(_read(path), _wp_of(path))`; `not bad`; `blocks[0][0] == "S00"` and `blocks[0][3].startswith("scaffold: ")`. (4) parametrised `test_each_block_names_a_row_of_its_own_section(path)`: for each block whose head starts with a GAPS4 id (`re.match(r"^(%s): " % _W_GAPS4_ID, h)`), assert `T.GAPS4_WP[id] == "WP-" + wp` and `T.GAPS4_SECTION[id] == "%s-%s" % (wp, sec[1:])`. (5) `test_the_template_makes_a_clean_script`: `t = _read(_WP_TEMPLATE)`; `t.count("@@WP@@") >= 100`; none of `"WP-31", "w31", "U01-1", "GAPS3"` in t; `blocks, bad = _wp_blocks(t.replace("@@WP@@", "47"), "47")`; `bad == []` and `[b[0] for b in blocks] == ["S00"]`. (6) parametrised `test_every_script_keeps_the_templates_head_and_tail(path)`: `_head_and_tail(_read(path)) == _head_and_tail(_read(_WP_TEMPLATE).replace("@@WP@@", _wp_of(path)))` (sections append only between the S00 block and the marker, and W0 must not edit the frame). (7) `test_the_block_reader`: build blocks with the helper of :1301-1310 renamed for `WP47_ONLY`/`w47_run`; `good = 'cscript "x"\n' + block("S00", "scaffold: smoke") + block("S02", "AX-4: ticks") + block("S02", "plat:PT-1: python") + block("S09", "tool: guard") + _W_MARK + "\n"`; `_wp_blocks(good, "47")` gives no problem and sections `["S00", "S02", "S02", "S09"]`; and each of: gate changed to `"S00") &` -> "not gated"; `"AX-4: ticks"` -> `"nothing"` -> "names no GAPS4 row"; a `"S02"` -> `"S01"` swap after S09 -> "section order"; marker removed -> "appears 0 times"; `WP47_ONLY` read with wp `"48"` -> "not gated". (8) `test_the_seconds_table_may_change`: `t = _read(_WP_TEMPLATE).replace("@@WP@@", "47")`; `u = t.replace("local w47_secs S00 1\n", "local w47_secs ///\n    S00 1 S09 150 ///\n    S10 300\n")`; assert `u != t` and `_head_and_tail(u) == _head_and_tail(t)`; and a change anywhere else in the head (`u2 = t.replace("SKIP: Python not available.", "SKIP: x.")`) gives `_head_and_tail(u2) != _head_and_tail(t)`; `len(_SECS.findall(t)) == 1`.

### N-6 `<scratch>/make_template.py` (write verbatim)

```python
"""make_template.py <repo> <out>: write test/templates/wp_truth_template.cscript
from test_wp31_truth.cscript's frame (section 33-01)."""
import re
import sys

repo, out = sys.argv[1], sys.argv[2]
src = open(repo + "/test/test_wp31_truth.cscript", encoding="utf-8").read().split("\n")
mark = "* ==== append new blocks above this line ===="
i_mark = src.index(mark)
i_end = src.index("* ==== end S01 ====")
assert src[i_end + 1] == "" and src[0] == "*! test_wp31_truth.cscript", "frame moved"
text = "\n".join(src[:i_end + 2] + src[i_mark:])
for a, b in (("WP-31", "WP-@@WP@@"), ("WP31", "WP@@WP@@"), ("wp31", "wp@@WP@@"),
             ("w31", "w@@WP@@"), ("U01-1", "Q@@WP@@00-1"), ("S01", "S00")):
    text = text.replace(a, b)
head_end = text.index('cscript "WP-@@WP@@ truth')
HEADER = """*! test_wp@@WP@@_truth.cscript
*! WP-@@WP@@'s ONE certification script (.ultraplan/sections/index.md PD-6):
*! every comparison with twoway's drawing or with Stata's own values that
*! WP-@@WP@@'s sections need lives here, one block per GAPS4 row (or per
*! harness tool), appended above the "append new blocks above this line"
*! marker in section order.  Refusal, message and return-code checks join
*! the EXISTING script for their area (merge rule R1).
*!
*! Made from test/templates/wp_truth_template.cscript (@@WP@@ -> the WP's
*! number).  S00 is the scaffold smoke (Q@@WP@@00-1).  A section appends
*! `* ==== S<MM> <lead id>: <what> ====` ... `* ==== end S<MM> ====` (or
*! `S<MM> tool: <what>` for a section with no item), its helper programs
*! directly above its first header, and writes only inside its own
*! blocks.  Case ids are Q@@WP@@<MM>-<k> (PD-5).
*!
*! Usage: via run_all_cscripts.do.  One block alone: WP@@WP@@_ONLY=S<MM> in
*! the driver's environment.  Each block prints "S<MM> start" and "S<MM>
*! end" with the date and time.  The suite runs it in every session;
*! DASH_CERT_SHARD=k/N runs part k of N of the blocks; a part with no
*! block ends 0.

"""
text = HEADER + text[head_end:]
secs = re.compile(r"// Seconds: each block's start/end lines[^\n]*\n(?://[^\n]*\n)*"
                  r"local w@@WP@@_secs ///\n(?:    [^\n]*///\n)*    [^\n]*\n")
assert len(secs.findall(text)) == 1, "seconds table moved"
text = secs.sub("// Seconds: each block's start/end lines in the WP's last measured\n"
                "// certification run, rounded up, at least 1; a block not listed\n"
                "// counts 1 s.\n"
                "local w@@WP@@_secs S00 1\n", text)
for left in ("WP-31", "w31", "U01", "GAPS3", "S61"):
    assert left not in text, left
open(out, "w", encoding="utf-8").write(text)
print("template: %d lines, %d placeholders" % (text.count("\n"), text.count("@@WP@@")))
```

Measured 20oct2026: 246 lines, 113 placeholders; `sed 's/@@WP@@/33/g'` of it, run from a copy of test/ through `scripts/stata_slot.sh`, printed `test_wp33_truth: part 1/1 runs 1 blocks: S00`, `Q3300-1 PASS: a twoway SVG was written and read (10 texts); dash is loaded` and `test_wp33_truth: ALL CHECKS PASSED`.

### N-7 runner block 71 (insert after block 70's `}` at :3170)

Copy block 70 (:3125-3170) verbatim, replacing every `test_wp31_truth.cscript` with `test_wp33_truth.cscript` and the comment's first six lines with:

```
// 71. test_wp33_truth.cscript (WP-33: the one certification script for
// every twoway/Stata-value comparison WP-33's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
```
