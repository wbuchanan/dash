# Section 58: Register drift

> Part of: WP-31 · GAPS3 rows: J4, J5, J6 · Risk: green · Batch: 19 · Depends on: 01 · Blocks: -- · Tasks: 7, 3 commits · Case-id prefix: U58

## Overview

**What is wrong today.** GAPS3 J4 (stale tracking text): GAPS.md:42-76 ("Eight gaps stand between this tree and the product dash.sthlp describes: 1. Every computed layer ignores its row filter ... 8. There is no image or data export") lists eight closed gaps as current; ROADMAP.md:4194 says "19 remain open, all S3" where BUGS.md has 3 open entries at `6370ca4` (112 after S01); 62 closed BUGS.md entries (`- [x]`) have a Resolution that starts `Not fixed` (measured: 62 of 65 `Resolution: Not fixed` lines sit under `- [x]` headers, e.g. :909-913, :915-919, :951-955); DROPIN P3.10 (`.ultraplan/handoff/DROPIN-REMAINING.md:434`) says "dash_render.py is one 32k-line module" and GAPS2 K10 (GAPS2.md:1878, :1881) "27.7k lines ... 27,715 lines" where the file is 52,280 lines; TWOWAY_COVERAGE_AUDIT.md:169 lists `horizontal`, `vertical`, `pstyle`, `lstyle`, `mstyle`, `mlstyle`, `recast`, `text`, `mlabvposition`, `mlabtextstyle`, `cmissing`, `connect` among the "tracked known-inert names" (all drawn now; bracketed WP-30 notes follow the list) and :95 describes lpolyci as "Local polynomial plus bootstrap percentile band" in its body with a correction appended in brackets; GAPS2 anchors A8, B27, A2 point at old line numbers; test/test_geometry_visual.md:6 and :20 (a procedure for a `/tmp/dash-visual` run with `<repo>`); test/test_scheme_fidelity.py:996 "all 20 translated schemes" (26 shipped); docstrings describing removed xfails in test_scheme_consumption.py:1108-1113 ("five were strict xfails ... until the S3 batch fixed them"), test_scheme_visual_truth.py:66-74 ("were pinned here as strict xfails until the S3 batch fixed them"), test_mode_parity.py:2341 ("were a hand-made strict xfail until WP-27"), test_filters.py:1612-1622 (a browser measurement of the line-plot filter bug, fixed); test_glyphs.py:1352 a "Missing unit tests" header over tests that exist; dangling references to `.ultraplan/BASELINE.md` (test_varlist_expansion.py:240), `.ultraplan/CHANGELOG.md` (REMAINING.md:1262, :1405, :1921; BUGS.md:245; test_varlist_expansion.py:252-291), `.ultraplan/phases/PHASE-12` (GAPS2.md:1146), `examples/plot_types_tour.do` (GAPS2.md:1772; S57 writes it), `scripts/extract_format_locale_truth.do` (GAPS2.md:1728). GAPS3 J5 (served-app text): the emitted header line `'# Launch with: bokeh serve <this_file.py>'` (dash_render.py:47961); `ServerAppBuilder` docstring :46424-46444 ("Can be launched with ``bokeh serve <app.py>`` or executed directly", "true dynamic recomputation of aggregated plots (histogram, lfit, qfit, kdensity, lowess)"); dead `title_safe = html.escape(title_raw)` at :47868; `_SIZE_MAP` emitted into the app at :48084 (`"_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),)`). GAPS3 J6: REMAINING.md (its §"89 tasks" table :353-365 with 68 PARTIAL) and `phases/` (32 files) are superseded by ROADMAP.md and DROPIN-REMAINING.md but carry no notice; ROADMAP.md's `## WP-01 · Parser integrity` ... `## WP-11 · Server facets` (:84-1102) lack the ` — DONE` suffix `_wp_sections` (test_tracking_documents.py:684-698) reads, although each carries a `> **DONE` blockquote (so `done` is already True through the second clause).

**After this section** every sentence J4 names says what is true at the batch-19 base or is marked historical with a date; the 62 closed entries whose Resolution begins "Not fixed" are reconciled (each gains a leading `Fixed <ddmonyyyy> (<closer>). ` clause taken from the commit or entry that closed it, or is reopened if nothing did); `test_tracking_documents.py` gains count checks (`TestTheCountsAreTrue`: ROADMAP's open-entry count sentence, GAPS.md's "Eight gaps" summary marked historical, the renderer line count in GAPS2/DROPIN annotated); the served app's header line, docstring, dead assignment and `_SIZE_MAP` emission are fixed (J5); REMAINING.md and phases/PHASE-00-INDEX.md open with a historical notice and ROADMAP's WP-01..WP-11 headings carry ` — DONE` (J6).

**Why one section.** Three S3 rows that are all text reconciliation over the tracking documents and the served template's prose; one commit each.

**Test order and commit rule.** Three cycles, three commits `(WP-31 J4)`, `(WP-31 J5)`, `(WP-31 J6)`; each cycle's first task writes the failing tests and saves `<scratch>/58-0k-failure.txt`, never commits.

### Section decisions

- **D-58.a GAPS2.md stays read-only (M23, A6).** J4's "GAPS2 anchors A8, B27, A2 point at old line numbers" and the three dangling GAPS2 references (:1146, :1728, :1772) are NOT edited by S58; the J4 Resolution records them as "left as written: GAPS2.md is read-only after WP-31 S01 (M23); its anchors are at 1a78bb9-era line numbers and GAPS3.md carries the current ones". DROPIN-REMAINING.md:434 likewise (S01 narrowed what GAPS3 §6 listed; P3.10 was not in §6) -- recorded, not edited (ratification item 1).
- **D-58.b Closed "Not fixed" entries (DECISIONS D7: rewritten in place; an entry whose closing commit cannot be found is reopened as S3).** For each of the 62, find the closer: the entry's own later sentences ("**Closed by WP-19**", "Reconciled 23sep2026 (WP-23)", a commit sha) or `git log -S"<title's first 40 chars>" --format=%h -- BUGS.md`. Rewrite the Resolution's first clause to `Fixed <ddmonyyyy> (<WP-nn or sha>), recorded below; the first text of this Resolution is the historical "Not fixed" note. Not fixed ...` (the rest of the line kept verbatim). An entry with no closer found is reopened (`- [ ]`) with `Graded S3 (WP-31): <why>` and a new Tracked-free BUGS entry is not needed (it is the same entry); list them in the J4 Resolution as a residual (M12). The reader `TestEveryClosedEntryNamesATestThatExists` must stay green: a closed entry must still name a test; where the historical text names none, the reconciled clause adds `Pinned by <the test the closer's commit added>` found with `git show --stat <sha>`.
- **D-58.c ROADMAP:4194.** The sentence is WP-27's AC record; it becomes "19 remained open, all S3, at WP-27's closeout (3 at 6370ca4; see BUGS.md)". `TestTheCountsAreTrue::test_the_roadmap_open_count_is_dated` asserts the sentence holds "remained" and a sha.
- **D-58.d GAPS.md:42-76.** Insert after :42 (`## Executive summary`; :44 is the first paragraph, REVIEW-4 R4-30) the line `*Historical (21sep2026): the eight gaps below were closed by WP-01 to WP-21; see each gap's heading for its closer and ROADMAP.md.*`; nothing else in GAPS.md changes (its headings carry the statuses the tracking test reads).
- **D-58.e Test docstrings.** Each named docstring is rewritten to past tense with the date of the fix ("Two cases, measured 24sep2026, were pinned as strict xfails until the S3 batch (24sep2026) fixed them; they are plain assertions now"); `test_glyphs.py:1352`'s header becomes `# Unit tests added for the mappers that had none (WP-09)`; `test_scheme_fidelity.py:996` "all 20" → "all 26"; `test_geometry_visual.md:6, :20` keep the procedure but name `scripts/stata_batch.sh` (already) and replace `/tmp/dash-visual` with `<scratch>/dash-visual` and the `<repo>` placeholder sentence "replace <repo> with the checkout's absolute path"; `test_varlist_expansion.py:240` → "recorded in test/conftest.py's _BASELINES (python 3.14, bokeh 3.9; the .ultraplan/BASELINE.md it once cited is gone)", :252-291 `.ultraplan/CHANGELOG.md` → `CHANGELOG.md`; BUGS.md:245 `.ultraplan/CHANGELOG.md` → `CHANGELOG.md (then .ultraplan/CHANGELOG.md)`.
- **D-58.f J5.** The header line becomes `'# Launch with: python <this_file.py>  (or: dash serve, which runs it for you)'`; the docstring's "Can be launched with ``bokeh serve <app.py>``" → "Is run by ``dash serve`` through ``python <app.py>`` (``bokeh serve <app.py>`` also works)"; "(histogram, lfit, qfit, kdensity, lowess)" → "(every computed layer)"; `title_safe` at :47868 deleted if `grep -c title_safe dash_render.py` is 1 (only the assignment); `_SIZE_MAP` emission: S41 (E13) deletes `_SIZE_MAP` itself in batch 14, so at the batch-19 base :48084 is already gone -- 58-04 asserts `grep -c '_SIZE_MAP' dash_render.py` → 0 and records "already removed by S41 (E13)" in the J5 Resolution; if it is not gone, stop and report (S41 did not land as planned).
- **D-58.g J6.** REMAINING.md gains, after its first heading line, `> **Historical (10oct2026).** Superseded by ROADMAP.md (WP-12 to WP-30) and .ultraplan/handoff/DROPIN-REMAINING.md; the PARTIAL markers below are the state of 20sep2026 and are not maintained.`; `phases/PHASE-00-INDEX.md` the same notice naming phases/; the 31 phase files are not edited (one notice in the index suffices; ratification item 2: delete phases/ instead?). ROADMAP.md :84, :168, :277, :346, :417, :552, :655, :745, :866, :930, :1102 gain ` — DONE` (the em dash U+2014 with spaces, as :1220 `## WP-12 · The parity guard earns its name — DONE`).

## Risk: [green] -- documents, docstrings and two prose lines of the served template

**Risk factors.** 1. A BUGS.md Resolution rewrite breaks `_parse_bugs` (four fields) or `TestEveryClosedEntryNamesATestThatExists`. 2. The ROADMAP heading edit changes what `_parse_roadmap` reads for WP-01..WP-11 (`done` already True; the suffix adds nothing but must not break the `## WP-nn ` split). 3. Editing the served template's header line changes the generated app's text: `test_server_build_options.py` or a parity test may pin it.

**Mitigation.** 1. 58-01's tests include running the whole tracking file after each edit. 2. `test_the_roadmap_reader` (:701) pins `_parse_roadmap`; run it. 3. `grep -rn "Launch with" test/` before editing; flip any pin in place (R9).

## Dependencies

- **Depends on:** 01 (the entries and Tracked lines); J5's `_SIZE_MAP` leg depends on S41 (batch 14) having landed.
- **Blocks:** nothing. **Parallel batch 19** with S56 (dash.sthlp) and S57 (examples/): S58 edits neither; S58 is batch 19's only editor of `dash_render.py` (prose lines only) and of the tracking documents other than the three sections' own entries.

## Evidence

- BUGS.md closed entries with `Not fixed` Resolutions: 62 (probe: for each `- [x] Title:` header, the next `  - Resolution:` line starting `Not fixed`); examples :913 "Not fixed. Found while measuring WP-10's hover parity...", :919 "Not fixed beyond the four types named...", :955 "Not fixed. Still open, measured 23sep2026 at 4ede074 (WP-23)...".
- ROADMAP.md:4190-4194 (WP-27's AC text): "... Every open entry now carries "Graded S<n> (WP-27): <why>", and test/test_tracking_documents.py::TestNoOpenEntryBlocksARelease fails on an open S1 or S2: 19 remain open, all S3."
- GAPS.md:42-76: `## Executive summary` at :42 (:44 is the first paragraph); "Eight gaps stand between this tree and the product `dash.sthlp` describes:" :46-47; items 1-8.
- TWOWAY_COVERAGE_AUDIT.md:169: the backticked list `acolor`, `alcolor`, ... `yoverhangs` followed by `[WP-30 P1.9b, commit a5e3757: horizontal drawn] [WP-30 P1.14b, commit 38bbb05: named styles drawn; dstyle, dlstyle, bmlinestyle stay named] [WP-30 P1.10, commit 56b3597: text and ttext drawn] [WP-30 P1.8a, commit fa52891: connect and cmissing drawn]`; :95 the lpolyci row "Local polynomial plus bootstrap percentile band; ..." with `[WP-29 P0.9, commit e32be3a: corrected -- the band is Stata's analytic band ...]`.
- test_tracking_documents.py:684-698 `_wp_sections`: `done = head.rstrip().endswith("— DONE") or re.search(r"^> \*\*DONE\b", section, re.M) is not None`.
- dash_render.py:47961 `'# Launch with: bokeh serve <this_file.py>',`; :46424-46444 the ServerAppBuilder docstring; :47868 `        title_safe = html.escape(title_raw)`; :48084 `"_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),),` (S41 removes `_SIZE_MAP`, :6992-7007, in batch 14).
- REMAINING.md:351-366 the DONE/PARTIAL/NOT DONE table; `ls phases | wc -l` → 32; ROADMAP.md headings :84 `## WP-01 · Parser integrity` through :1102 `## WP-11 · Server facets` without the suffix; :1220 `## WP-12 · The parity guard earns its name — DONE` with it.
- Existing tests that pin today's text: `test_tracking_documents.py::TestGapsAndRoadmapAgree`, `::test_the_roadmap_reader` (:701 region), `TestEveryClosedEntryNamesATestThatExists` (:386) -- all must stay green; any test quoting `Launch with: bokeh serve` (`grep -rln "Launch with" test/`), flipped in place.

## User stories

- **US-58.1** As the maintainer, I want every tracking document to state the current state or say it is historical, so an audit does not re-verify closed work.
- **US-58.2** As a user who opens the generated server app, I want its header to tell me how dash runs it.

## Business requirements

- **BR-58.1** No closed BUGS.md entry's Resolution begins with "Not fixed"; each begins with its closer, or the entry is open.
- **BR-58.2** GAPS.md's summary, ROADMAP's open-entry sentence, TWOWAY_COVERAGE_AUDIT.md's inert list and lpolyci row, and the named docstrings are true or dated historical; every dangling path names a file that exists or says it is gone.
- **BR-58.3** The served app's header, docstring and dead code say what the app does; nothing it does changes.
- **BR-58.4** REMAINING.md and phases/ carry a historical notice; WP-01..WP-11 headings read ` — DONE`.

## Technical requirements

- **TR-58.1 `test/test_tracking_documents.py`** gains `class TestTheCountsAreTrue` (appended after TestWp31Tracking): `test_no_closed_entry_begins_not_fixed` (for each closed entry, `not Resolution.startswith("  - Resolution: Not fixed")`); `test_the_roadmap_open_count_is_dated` (D-58.c regex `19 remained open, all S3, at WP-27's closeout \(3 at [0-9a-f]{7}`); `test_gaps_summary_is_marked_historical` (`*Historical (21sep2026)` within 3 lines after `## Executive summary`); `test_the_audit_inert_list_names_no_drawn_option` (the TWOWAY_COVERAGE_AUDIT.md:169 list minus the pending blocks' names, read with test_help_conformance's `_pending` logic copied as `_pending_names()`, is empty); `test_no_test_file_cites_a_gone_path` (`.ultraplan/BASELINE.md`, `.ultraplan/CHANGELOG.md`, `.ultraplan/phases/` absent from test/*.py, BUGS.md, REMAINING.md:1262/:1405/:1921 excepted by `_USER_RECORDS`); `test_remaining_and_phases_are_marked_historical`; `test_wp01_to_wp11_headings_say_done` (`_wp_sections`: every head of WP-01..WP-11 `endswith("— DONE")`). Module docstring item 11 describing the class.
- **TR-58.2 BUGS.md** per D-58.b (62 entries; a generated list of (line, title, closer) in `<scratch>/s58/58-closers.txt` first, reviewed before editing).
- **TR-58.3** GAPS.md D-58.d; ROADMAP.md:4194 D-58.c; TWOWAY_COVERAGE_AUDIT.md:169: remove the drawn names from the backticked list (keep the bracketed notes, add `[WP-31 J4: list reduced to the names still pending at <sha>]`) and :95: the lpolyci row's body becomes "Local polynomial plus Stata's analytic band; ..." keeping the bracketed note; the docstrings of D-58.e.
- **TR-58.4 dash_render.py (J5)** per D-58.f: :47961, :46424-46444, :47868; the served copy lists are untouched (no helper changes); `_generate_app_source` is edited for one string literal (R12: S58 is batch 19's only editor).
- **TR-58.5 J6** per D-58.g.
- **TR-58.6 Security.** Text only; the header line is a Python comment inside the generated file, written by the template's string list, never from user text.

## Boundaries

- Not edited: GAPS2.md, DROPIN-REMAINING.md (M23; D-58.a), GAPS3.md other than S58's three Tracked lines, dash.sthlp (S56), examples/ (S57), any test's assertions (only docstrings and comments), WP-29/WP-30 tracking constants, the 31 phase files' bodies.
- `dash_render.py`: only the three prose/dead-code sites of D-58.f; no behaviour change (the app's text output other than its header comment is byte-identical; 58-05 proves it with a before/after diff of a generated app).

## Stata truth

None. No cscript case (nothing Stata-facing changes); no block in test_wp31_truth.cscript. Case prefix U58 is reserved and unused.

## TDD test stubs

Regression (58-01, J4; red at the batch-19 base): `test/test_tracking_documents.py::TestTheCountsAreTrue::test_no_closed_entry_begins_not_fixed` (62 lines listed), `::test_the_roadmap_open_count_is_dated`, `::test_gaps_summary_is_marked_historical`, `::test_the_audit_inert_list_names_no_drawn_option`, `::test_no_test_file_cites_a_gone_path`.
Regression (58-04, J5): `test/test_server_build_options.py::TestTheAppHeader::test_it_names_how_dash_runs_it` (new; the generated source holds `# Launch with: python` and not `bokeh serve <this_file.py>`), `::test_no_dead_title_safe` (`grep`-equivalent over dash_render.py source: `title_safe` absent), `::test_no_size_map_is_emitted` (guard, green if S41 landed).
Regression (58-06, J6): `TestTheCountsAreTrue::test_remaining_and_phases_are_marked_historical`, `::test_wp01_to_wp11_headings_say_done`.
Guards: `test_the_roadmap_reader`, `TestGapsAndRoadmapAgree`, `TestEveryClosedEntryNamesATestThatExists`, `TestEveryBugsEntryIsWellFormed`. Pinned tests to flip: any node quoting `Launch with: bokeh serve` (found by grep). Parity corpus: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| 62 Resolutions reconciled; counts and summaries true | pytest `TestTheCountsAreTrue` (7) | the documents | n/a |
| Readers unchanged | pytest `test_tracking_documents.py` whole | -- | n/a |
| App header, docstring, dead code | pytest `test_server_build_options.py::TestTheAppHeader` (3) | generated app | served |
| App behaviour unchanged | diff of `python3 -c` generated app before/after, header line excepted | spec/data of one scatter | served |

AC-58.1 `python3 -c "..."` probe of D-58.b prints 0 closed-Not-fixed entries. AC-58.2 `grep -c 'Launch with: bokeh serve' dash_render.py` → 0. AC-58.3 `grep -c '^## WP-\(0[1-9]\|1[01]\) .* — DONE$' ROADMAP.md` → 11. AC-58.4 `python3 -m pytest test/test_tracking_documents.py test/test_server_build_options.py -q -p no:cacheprovider` 0 failed.

## Tasks

**Commit boundary.** 58-01..58-03 → `Reconcile the tracking documents and stale docstrings with the tree (WP-31 J4)`; 58-04..58-05 → `Say how the served app is run and drop its dead text (WP-31 J5)`; 58-06..58-07 → `Mark REMAINING.md and phases historical and suffix the DONE headings (WP-31 J6)`. Bodies per BRIEF; `BUGS.md: "<title>" (closed)` and `GAPS3: <row> Tracked` in each closing commit; Every Tracked line is written with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha; no amend). Worktree `<W>` = `.../dash-wt/wp31-s58`.

<task type="auto" id="58-01">
  <name>Write failing count tests, list closers</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[Append `class TestTheCountsAreTrue` per TR-58.1 (the five J4 tests now; the two J6 tests are added in 58-06) and docstring item 11. Write <scratch>/s58/58-closers.txt: one line per closed entry whose Resolution starts `Not fixed`: `<line> | <title> | <closer: the WP-nn, date or sha found in the Resolution's later sentences, else the first sha of git log -S"<title[:40]>" --format=%h -- BUGS.md, else NONE>`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -rf > <scratch>/s58/58-01.log 2>&1`; write <scratch>/58-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s58/58-01.log` prints 5 (the five J4 nodes) and every other node passed; `wc -l < <scratch>/s58/58-closers.txt` prints 62; `grep -c ' | NONE$' <scratch>/s58/58-closers.txt` is recorded in the failure file.]]></verify>
  <done>The count tests existed and failed on the unmodified documents, and every closed Not-fixed entry had its closer looked up.</done>
</task>

<task type="auto" id="58-02">
  <name>Reconcile BUGS.md, GAPS.md, ROADMAP and the audit</name>
  <files>BUGS.md, GAPS.md, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[Apply D-58.b to each line of 58-closers.txt (a NONE row is reopened: `- [x]` → `- [ ]`, Resolution prefixed `Not fixed: reopened 10oct2026 (WP-31 J4): no closing commit or test was found. Graded S3 (WP-31): <one phrase from its title>. ` and the row listed for the J4 Resolution's residual). Apply D-58.d to GAPS.md, D-58.c to ROADMAP.md:4194 (ROADMAP.md is a fourth file: edit it here and list it in the commit), and TR-58.3's two TWOWAY_COVERAGE_AUDIT.md edits. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` after each file.]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k "not test_no_test_file_cites_a_gone_path"` reports 0 failed (TestEveryClosedEntryNamesATestThatExists and TestNoOpenEntryBlocksARelease included); `grep -c '^- \[ \] Title:' BUGS.md` equals 112 plus the NONE count.]]></verify>
  <done>Every closed entry opened with its closer, the summaries were dated, and the audit's inert list named only pending options.</done>
</task>

<task type="auto" id="58-03">
  <name>Fix the docstrings, close J4 and commit</name>
  <files>test/test_varlist_expansion.py, test/test_scheme_consumption.py, test/test_scheme_visual_truth.py</files>
  <action><![CDATA[Apply D-58.e to the eight files it names (test_varlist_expansion.py, test_scheme_consumption.py, test_scheme_visual_truth.py, test_mode_parity.py, test_filters.py, test_glyphs.py, test_scheme_fidelity.py, test_geometry_visual.md; and BUGS.md:245) -- comments and docstrings only; `git diff --stat` must show no assertion line changed (review the diff). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` (all green) and `python3 -m pytest test/test_varlist_expansion.py test/test_glyphs.py test/test_scheme_fidelity.py -q -p no:cacheprovider` (green: nothing but text changed). Close the J4 entry (closed form; `Pinned by test/test_tracking_documents.py::TestTheCountsAreTrue::test_no_closed_entry_begins_not_fixed, ::test_the_roadmap_open_count_is_dated, ::test_gaps_summary_is_marked_historical, ::test_the_audit_inert_list_names_no_drawn_option, ::test_no_test_file_cites_a_gone_path. Residual, deferred (WP-31): GAPS2.md's A8, B27 and A2 anchors and its three dangling references, and DROPIN P3.10's line count, are left as written (M23: both files are read-only after S01) (GAPS3 J4 Tracked)[; reopened entries: <titles>]`); the J4 Tracked line takes the Partly form if entries were reopened, else Closed; delete the `"J4": "` WP31_OPEN line; replace `<!-- WP-31 J4 -->` under `### Fixed in WP-31` with `- The tracking documents say what is true: 62 closed BUGS.md entries that began "Not fixed" open with their closer, GAPS.md's summary and ROADMAP's open count are dated, TWOWAY_COVERAGE_AUDIT.md's inert list names only pending options, and eight stale test docstrings are rewritten. (WP-31, J4)`. The J4 Tracked line ends `commit pending` (A11). Stage by name; commit.]]></action>
  <verify><![CDATA[`git diff HEAD~1 --stat` after the commit lists BUGS.md, GAPS.md, ROADMAP.md, TWOWAY_COVERAGE_AUDIT.md, CHANGELOG.md, GAPS3.md, test/test_tracking_documents.py and the eight docstring files; `grep -c '^    "J4": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` 0 failed; `git log -1 --format=%s` ends `(WP-31 J4)`.]]></verify>
  <done>J4 was closed in one commit with the documents and docstrings reconciled and the read-only registers recorded as a residual.</done>
</task>

<task type="auto" id="58-04">
  <name>Write the failing app-header tests</name>
  <files>test/test_server_build_options.py</files>
  <action><![CDATA[Assert `grep -c '_SIZE_MAP' dash_render.py` prints 0 (S41 landed); otherwise stop and report. `grep -rln "Launch with" test/` and note the files. Append `class TestTheAppHeader` to test/test_server_build_options.py with the three tests of "TDD test stubs" (generate an app from a one-scatter spec with ServerAppBuilder as the file's existing tests do; assert the source holds `# Launch with: python` and not `bokeh serve <this_file.py>`; assert `title_safe` is absent from dash_render.py's text; assert `_SIZE_MAP =` is absent from the generated source). Generate one app to <scratch>/s58/app-before.py for 58-05's diff. Run the class; write <scratch>/58-04-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[Two of the three tests fail (`test_it_names_how_dash_runs_it`, `test_no_dead_title_safe`) and `test_no_size_map_is_emitted` passes; `test -s <scratch>/s58/app-before.py`.]]></verify>
  <done>The header, dead-code and emission tests existed, two failing on the unmodified renderer.</done>
</task>

<task type="auto" id="58-05">
  <name>Fix the served prose, close J5 and commit</name>
  <files>dash_render.py, BUGS.md, GAPS3.md</files>
  <action><![CDATA[Apply D-58.f to dash_render.py:47961, :46424-46444 and :47868 (delete the `title_safe` line only if `grep -c title_safe dash_render.py` prints 1; else report). Generate the same app to <scratch>/s58/app-after.py and `diff <scratch>/s58/app-before.py <scratch>/s58/app-after.py`: exactly the header line differs. Run `python3 -m pytest test/test_server_build_options.py test/test_server_serves.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -p no:cacheprovider` and flip any pin of the old header in place (`Flipped (WP-31 J5)`). Close the J5 entry (`Pinned by test/test_server_build_options.py::TestTheAppHeader::test_it_names_how_dash_runs_it, ::test_no_dead_title_safe, ::test_no_size_map_is_emitted`; "_SIZE_MAP emission already removed by S41 (WP-31 E13)"), delete the `"J5": "` key, replace `<!-- WP-31 J5 -->` under `### Fixed in WP-31` with `- The server app dash build, server writes opens with how dash runs it (python <file>, or dash serve), its class docstring no longer names bokeh serve as the way or five layer types as the recomputed ones, and a dead escaped title is gone. (WP-31, J5)`; rewrite the J5 Tracked line to the Closed form with `commit pending` (A11); commit (CHANGELOG.md, the tracking test and the test file are further files of the commit).]]></action>
  <verify><![CDATA[`diff <scratch>/s58/app-before.py <scratch>/s58/app-after.py | grep -c '^[<>]'` prints 2; `grep -c 'Launch with: bokeh serve' dash_render.py` prints 0; the pytest runs report 0 failed; `grep -c '^    "J5": "' test/test_tracking_documents.py` prints 0; `git log -1 --format=%s` ends `(WP-31 J5)`.]]></verify>
  <done>The served app's prose said what it does, its behaviour was proven unchanged, and J5 was closed in one commit.</done>
</task>

<task type="auto" id="58-06">
  <name>Write the failing historical-notice tests</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[Add `test_remaining_and_phases_are_marked_historical` (REMAINING.md and phases/PHASE-00-INDEX.md each hold `> **Historical (10oct2026).**` within their first 5 lines) and `test_wp01_to_wp11_headings_say_done` (TR-58.1) to TestTheCountsAreTrue. Run them; write <scratch>/58-06-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[Both fail; `test_the_roadmap_reader` passes.]]></verify>
  <done>The two J6 tests existed and failed on the unmodified documents.</done>
</task>

<task type="auto" id="58-07">
  <name>Mark the documents historical, close J6 and commit</name>
  <files>REMAINING.md, phases/PHASE-00-INDEX.md, ROADMAP.md</files>
  <action><![CDATA[Apply D-58.g: the two notices and the eleven ` — DONE` suffixes (:84, :168, :277, :346, :417, :552, :655, :745, :866, :930, :1102; the dash is U+2014 with a space on each side, copied from :1220). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Close the J6 entry (`Pinned by test/test_tracking_documents.py::TestTheCountsAreTrue::test_remaining_and_phases_are_marked_historical, ::test_wp01_to_wp11_headings_say_done`), delete the `"J6": "` key, replace `<!-- WP-31 J6 -->` under `### Fixed in WP-31` with `- REMAINING.md and phases/ carry a historical notice naming ROADMAP.md and DROPIN-REMAINING.md as their successors, and ROADMAP.md's WP-01 to WP-11 headings carry the DONE suffix the tracking test reads. (WP-31, J6)`; rewrite the J6 Tracked line to the Closed form with `commit pending` (A11); commit.]]></action>
  <verify><![CDATA[`grep -c '^## WP-\(0[1-9]\|1[01]\) .* — DONE$' ROADMAP.md` prints 11; `head -5 REMAINING.md | grep -c 'Historical (10oct2026)'` prints 1; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 J6)`; `git log -3 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The superseded documents said so, the DONE headings read as the test reads them, and J6 was closed in one commit.</done>
</task>

## Section completion criteria

- Three commits on `wp31-s58` ending `(WP-31 J4)`, `(WP-31 J5)`, `(WP-31 J6)`; no test-only commit.
- `TestTheCountsAreTrue` (7) green; `TestTheAppHeader` (3) green; the whole tracking file green; the generated app differs from before only in its header line.
- J4, J5, J6 closed (J4 Partly if entries were reopened), keys deleted, markers replaced.

## Notes

- **M23 / D-58.a:** never edit GAPS2.md or DROPIN-REMAINING.md here; record what J4 asked for in them as a residual sentence.
- **R9:** a test that pins `Launch with: bokeh serve` is flipped, not deleted.
- **R12:** `_generate_app_source` is edited for one string literal; S56 and S57 do not touch dash_render.py.
- **Trap:** `_parse_bugs` needs the four fields in order with two-space indents; a rewritten Resolution must stay one logical line (continuations indented four spaces).
- **Trap:** the em dash in the DONE suffix is U+2014; an ASCII hyphen fails `_wp_sections`' `endswith("— DONE")`.
- **Decisions for maintainer ratification:** (1) D-58.a (GAPS2/DROPIN anchors left as written); (2) D-58.g (notice in phases/PHASE-00-INDEX.md rather than deleting phases/). **Decided:** D-58.b -- closed "Not fixed" preambles rewritten in place and entries with no closer reopened as S3 (DECISIONS D7).
- **Tracked lines (A11):** the three closing tasks write `commit pending`; no amend anywhere. **A14:** no truth block. **Files (A13):** `<files>` lists primary files; the tracking documents and flipped tests are implied.
