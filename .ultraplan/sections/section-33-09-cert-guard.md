# Section 33-09: Twenty-example certification guard

> Part of: WP-33 (Verification corpus and README gallery) · Items: none (harness; TR-2 closes in 33-14) · Risk: yellow · Batch: 33.6 · Depends on: 33-05 (and 33-02..33-04 through it) · Blocks: 33-14 · Tasks: 4, 1 commit · Case-id prefix: Q3309

## Overview

**What is wrong today.** Nothing in the certification tier compares a twoway picture with dash's over real examples: the audit's TR-2 evidence is that "twoway_corpus.do and conformance_corpus check rc only; test_mode_parity compares dash with dash". WP-33 builds the full corpus (`make corpus`, about 425 examples once duplicates are removed, P4-2), but that run is long, Stata- and Chrome-bound and runs only at 33-14 and at WP-50's closeout (Q30). Between those, a regression in a common picture would pass every gate.

**After this section.** About twenty corpus examples, one per common plot type and option family, run in `make cert` (so in every `make test-all` gate) as block `S09 tool: corpus guard` of `test/test_wp33_truth.cscript`. twoway is drawn fresh by 33-03's own do-file text and dash by 33-04's, both run inside the certification session under one generated wrapper that leaves the session as it found it; 33-04's `export_pages` takes dash's SVG and view dump at twoway's size; 33-05's `judge` gives each verdict row. The rows must equal the committed fixture `test/fixtures/corpus_guard_truth.json`, which the committed `scripts/extract_corpus_guard_truth.do` writes and which also holds each example's frozen record, so the block needs no extraction. A fix that changes a guard example regenerates the fixture in its own commit, as it removes its ledger rows (PD-14, D-33-05.i).

**Why a separate section.** It depends only on the harness modules (33-02..33-05) and is independent of the gallery tooling (33-08), which runs beside it in batch 33.6.

**Test order and commit rule.** Task 01 writes the unit tests and the cscript block red and saves `<scratch>/33-09-01-failure.txt`; tasks 02-03 add the guard module, the list, the extract script and the fixture; task 04 runs the block green twice and commits once: `Add the twenty-example corpus guard to the certification suite (WP-33 33-09)` (D-33-01.g's subject form for a section with no item).

### Section decisions (binding on the executor)

- **D-33-09.a Interfaces used** (the Published interfaces of 33-02..33-05; use these names exactly -- a landed module that differs is that section's defect: stop and report it). 33-02 (TR-33-02.7, D-33-02.g): the examples.jsonl record keys; `extract.extract(stata_dir, repo, out, pdftotext=None)` (writes `<out>/examples.jsonl`); `datasets.cache_dir()`; the import convention -- insert the **repository root** into `sys.path` and import `from scripts.corpus import ...` (R1-10). 33-03 (TR-33-03.4): `twoway_run.do_text(examples, out_dir, cache) -> str`, `twoway_run.parse_log(text) -> dict`, `twoway_run.records(examples, parsed, svg_dir, run_dir) -> list[dict]`. 33-04 (Published interface): `dash_run.do_text(examples, out_dir, cache, repo) -> str`, `dash_run.records(examples, parsed, html_dir, run_dir, twoway_rows) -> list[dict]`, `dash_run.export_pages(pages, sizes, out_dir, probe=None) -> {id: {"svg", "view", "size_matched", "js_errors", "w", "h"} | {"error"}}`, `dash_run.CorpusProbe(path, chrome=None, timeout=60, ready=None)`. 33-05 (Published interface): `verdict.judge(example, tw, da, run_dir, rules, ledger, states, probe=None) -> dict` (the verdicts.jsonl row: `verdict`, `checks`, `summary`, `ledger`, `ssim`, `size_matched`, `rc_twoway`, `rc_dash`, `first_twoway`, `first_dash`, ...), `verdict.load_ledger(path)`, `ledger.gaps4_states()`; `rules` the parsed `test/fixtures/corpus_verdict_rules.json` (`T_same` a number or null). This section writes no do-file text, log parser, exporter or comparison of its own (R1-28, R1-30): it wraps 33-03's and 33-04's do-file texts and calls the rest.
- **D-33-09.b The guard list** `scripts/corpus/guard_examples.txt` (committed; one `<id>  # <plottype>: <first 60 characters of cmd>` per line, about 20), chosen once by this rule: for each of scatter, line, connected, area, bar, spike, dropline, dot, lfit, qfitci, lfitci, lpoly, lowess, kdensity, histogram, function, rarea, rcap, pcarrow, contour, tsline, and one `by()` example and one `colorvar()` example, the help-file example (`source == "help"`, a kept id of the de-duplicated examples.jsonl, P4-2) with the smallest id whose `setup` lines are only `sysuse`, `use`, `generate`, `replace`, `label`, `tsset` or `sort`, whose datasets are all shipped (none from `webuse`), whose twoway rc is 0, and -- when the rules' `T_same` is a number -- whose recorded SSIM is at least 0.01 from `T_same` (A-4: the image score can move only Same to Close, and T_close decides nothing, so only T_same can make a verdict flap); a type with no such example is skipped and named in the commit body. The list file is the selection's record; it is edited only by a later section that drops an example (with the reason in its commit body).
- **D-33-09.c Equality, not a ratchet.** The block fails when, for any listed id, the live row differs from the fixture's in `rc_twoway`, `first_twoway`, `rc_dash`, `verdict`, `checks` or `summary` (33-05's Notes: "33-09 compares verdict, checks and summary"). `first_dash`, `ssim`, `size_matched` and `ledger` are recorded and not compared (these four and the six compared fields are exactly the ten keys `measure` returns, TR-33-09.1; 33-05's `colours` is not recorded). An improvement also fails -- the verdict moves up (Differs, Close, Same) or, with the same verdict, `checks` becomes a proper subset -- with `<id> improved from <old verdict> (<old checks>) to <new verdict> (<new checks>): delete the fixed item's rows from scripts/corpus/ledger.tsv, run python3 scripts/corpus/ledger.py (D-33-05.i), and regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do in the fixing commit`; any other change prints `<id>: <field> was <old> now <new>: if the commit under test changed it, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do in that commit (a worse verdict is a regression: fix the code)`, so either message names the script, and BRIEF's ledger bullet step (3) regenerates the fixture on any change Q3309-1 reports for a guard example. So the fixture and the ledger move with the fix that moved them; a batch gate that finds one does so in step k.5 (fixture drift: update the fixture).
- **D-33-09.d Session hygiene.** `guard.guard_do` writes 33-03's and 33-04's do-file texts for the guard's examples and a wrapper `guard.do` (exact text in Notes) that saves `c(scheme)`, `c(linesize)`, `$S_ADO` and `$dash_nobrowser`, `preserve`s the data, runs each runner's do-file under its own named text log (`s09tw`, `s09da`; opened after the session's banner, so no licence text is read), and restores all of it (`set scheme <saved>`, never `permanently`), with `capture graph drop _all`, `capture serset clear` and `dash clear` at the end. 33-03's do-file text clears the data before each example and 33-04's adds `adopath ++` and `global dash_nobrowser 1`; the wrapper undoes both.
- **D-33-09.e Sizes.** Each dash page is exported at twoway's size, W = round(width_in x 96) and H = round(height_in x 96) from the twoway row (D-33-04.b), through `export_pages`; a by() or multi-figure page is letterboxed and `size_matched` false (D-33-04.c) until 34-04/45-04 land (PD-17); the fixture records `size_matched` per id.
- **D-33-09.f No Chrome is a failure.** The block calls `responsive_probe.find_chrome()` first; when it is None the case fails (`Q3309-1 FAIL: headless Chrome not found; the guard cannot run`); it never prints a SKIP (a skip is not a pass; cert_verdict.py fails on SKIP too).
- **D-33-09.g The examples live in the fixture.** Each listed id's examples.jsonl record is frozen in the fixture (`examples[<id>]["record"]`); the block writes `<run>/examples.jsonl` from those records, so certification reads no help file or g.pdf and runs exactly the frozen commands. The extract script freezes them once: when test/fixtures/corpus_guard_truth.json exists it takes each listed id's record from `examples[<id>]["record"]`, and it runs 33-02's extractor (once, into a temporary folder) only for the ids the fixture lacks -- every id at the first generation, none at a later regeneration. A regeneration therefore never re-extracts: 33-02's de-duplication signatures depend on dash.ado's option table (D-33-02.f `option_table`), which WP-35 edits, so a fresh extraction could drop a listed id as a duplicate of another, and `records_from_run` would then refuse it in a later fix's commit.
- **D-33-09.h Seconds (R1-5, D-33-01.i).** The block prints `S09 start` and `S09 end` with the date and time (BRIEF's block form); the section reports the measured seconds in its hand-back. The frame's seconds table `local w33_secs` is rewritten only by the WE step that D-33-01.i proposes, never here.

## Risk: [yellow] -- a certification block that drives Chrome through four harness modules

**Risk factors.** (1) A Published interface differs when this section lands. (2) Cert time (about 20 x (twoway export + dash save + Chrome export + raster)). (3) Verdict flapping. (4) Examples changing the session (scheme, data, graphs, adopath). (5) Stata's Python lacks a module the harness imports.

**Mitigation.** (1) D-33-09.a's stop rule; task 01 reads the landed modules first. (2) One Chrome for the exports and one for the rasters; the measured seconds go to the hand-back (D-33-09.h). (3) D-33-09.b's SSIM margin and D-33-09.c's equality on recorded fields only; task 04 runs the block twice. (4) D-33-09.d's wrapper. (5) The harness is standard library plus numpy and scipy ([B] §2.2); task 02 runs the unit tests under `/opt/anaconda3/bin/python3` (Stata's) as well.

## Dependencies

- **Depends on: 33-05** (judge, rules, ledger), and through it 33-02 (extractor, cache, the nested `.gitignore`), 33-03 (twoway do-file text and log reader), 33-04 (dash do-file text, records, exporter, probe), 33-01 (the truth script, its block reader and D-33-01.e's `tool:` head).
- **Blocks: 33-14** (the first corpus run closes TR-2 with the guard in place as its certification case).
- **Parallel batch 33.6:** with 33-08 (Makefile, docs/gallery tooling, .gitignore, test_no_secrets.py). Disjoint: this section adds `scripts/corpus/guard.py`, `scripts/corpus/guard_examples.txt`, `scripts/extract_corpus_guard_truth.do`, the fixture, `test/test_corpus_guard.py`, one row in test/test_fixtures_are_committed.py and one block.

## Evidence

- test/test_wp33_truth.cscript (33-01): frame from the template; block heads `scaffold:`, `<GAPS4 id>:` or `tool:` (D-33-01.e, `_W_HEAD`); tally helpers `_w33_expect <id> <cond> <msg>` / `_w33_done <id> <msg>`, `w33_work`, `w33_run`, `WP33_ONLY`; frame pinned by `test_cscript_hygiene.py::TestTheWpTruthScripts::test_every_script_keeps_the_templates_head_and_tail` (the seconds statement excepted, D-33-01.i). By batch 33.6 the script holds S00, S10 (two blocks, batch 33.2), S11 (33.3), S12 and S13 (two each, 33.4), each section's helpers directly above its first header.
- Top-level `python:` blocks in a cscript with `__main__`-qualified calls: test/cert_svg.do:44-58; the U20/U46 helpers of test_wp31_truth.cscript (:4207ff, :12968ff).
- Chrome: `test/responsive_probe.py::find_chrome` (:124-134), `chrome_argv` (:165-190).
- Fixtures: test/test_fixtures_are_committed.py `GENERATORS` (:257), `_ABSOLUTE` (:414), `TestEveryFixtureHasMeta` (:449); `.git/info/exclude:58` ignores `*.json` (fixtures are `git add -f`'d) and `:52` `*.txt` (R1-9).
- The truth gate: every truth script skips with r(222) when `c(python_exec)` is empty (WP-36 changes that rule; this block follows whatever the frame does).

## User stories

- **US-33-09.1** As the maintainer, I want twenty common twoway examples compared with dash in every certification run, so that a regression in a picture fails the gate the day it is made.
- **US-33-09.2** As a coding agent of a later WP, I want a fix that improves an example to tell me which ledger rows to delete and which fixture to regenerate, so that the record moves with my commit.

## Business requirements

- **BR-33-09.1** Every gate compares about twenty examples' twoway and dash pictures with the recorded verdicts, checks and summaries, and fails on any change.
- **BR-33-09.2** The recorded verdicts and the examples' commands come from a committed script, never from hand edits.
- **BR-33-09.3** The guard leaves the Stata session's scheme, line size, ado-path, data and graphs as it found them and never runs without Chrome.

## Technical requirements

- **TR-33-09.1 (module)** Create `scripts/corpus/guard.py` (D-33-02.g's opening lines; `from scripts.corpus import twoway_run, dash_run, verdict, datasets` and `from scripts.corpus import ledger as corpus_ledger`), public functions, one unit test each:
  - `read_list(path=<repo>/scripts/corpus/guard_examples.txt) -> list[str]` (ids; comments after `#` and blank lines ignored).
  - `candidates(examples, shipped) -> list[dict]`: the records that meet D-33-09.b's source, setup-word and shipped-dataset conditions (`shipped` = `datasets.shipped(<c(sysdir_stata)>)`; a record qualifies when every name of its `datasets` key is in it).
  - `select(run_dir, rules) -> tuple[list[str], list[str]]`: D-33-09.b over `<run_dir>`'s examples.jsonl, twoway.jsonl and verdicts.jsonl: the chosen ids (one per type, smallest id first) and the types skipped.
  - `records_from_run(run_dir, ids, fixture=None) -> dict[str, dict]`: for each id, `fixture["examples"][id]["record"]` when the parsed fixture holds that id (D-33-09.g), else its record in `<run_dir>/examples.jsonl` (read only when some id needs it; `run_dir` may be None when the fixture holds every id); `ValueError` naming every id found in neither.
  - `write_examples(records, run_dir) -> str`: writes `<run_dir>/examples.jsonl` (sorted by id, one JSON object per line) and returns its path.
  - `guard_do(examples, run_dir, cache, repo) -> str`: writes `<run_dir>/tw/guard_tw.do` = `twoway_run.do_text(examples, "<run_dir>/tw/svg", cache)`, `<run_dir>/dash/guard_dash.do` = `dash_run.do_text(examples, "<run_dir>/dash", cache, repo)` and `<run_dir>/guard.do` (Notes' text), creating the folders; returns guard.do's path.
  - `measure(run_dir, examples, rules_path, ledger_path, gaps4_path=None) -> dict[str, dict]`: `twoway_run.parse_log` of `<run_dir>/tw/guard.log` and `<run_dir>/dash/guard.log`; `tw = twoway_run.records(examples, parsed_tw, "<run_dir>/tw/svg", run_dir)`; `da = dash_run.records(examples, parsed_da, "<run_dir>/dash", run_dir, tw)`; `dash_run.export_pages({id: "<run_dir>/<html>"}, {id: (round(width_in*96), round(height_in*96))}, "<run_dir>/dash")` for each dash row with rc 0 and an `html`; each result folded into its dash row (`svg` = `dash/<id>.svg`, `view` = `dash/<id>.view.json`, `size_matched`, `js_errors`, `w`, `h`, or `export_error`); writes `<run_dir>/raster.html` (`<!doctype html><meta charset="utf-8"><title>raster</title>`, 33-05's blank page); opens one `dash_run.CorpusProbe("<run_dir>/raster.html", ready="document.readyState === 'complete'")` and calls `verdict.judge(example, tw_row, da_row, run_dir, rules, verdict.load_ledger(ledger_path), corpus_ledger.gaps4_states(gaps4_path), probe)` for each example in id order; returns `{id: {"rc_twoway", "first_twoway", "rc_dash", "first_dash", "verdict", "checks", "summary", "ledger", "ssim", "size_matched"}}` taken from each judge row.
  - `compare(want, got) -> list[str]`: D-33-09.c, one message per id, sorted by id; a listed id missing from `got` is a message too.
  - `main(argv)`: `--select <run>` prints the chosen lines (D-33-09.b's form, `<id>  # <plottype>: <first 60 characters of cmd>`, in id order) and then one line `skipped: <type> <type> ...` (`skipped: none` when every type has an example); no other mode (the block and the extract script call the functions).
  No absolute path is written into any returned row or the fixture (Q36): records keep 33-02's relative `file`, the runners replace the cache and run folders in first lines (TR-33-03.3).
- **TR-33-09.2 (list)** Create `scripts/corpus/guard_examples.txt` by D-33-09.b, with the header line `# WP-33 33-09: the certification guard's examples (D-33-09.b); about twenty, one per common type`. Staged with `git add -f` (R1-9: `.git/info/exclude:52` ignores `*.txt`; 33-02's nested `.gitignore` re-includes it and `test_corpus_functions.py::TestTheCorpusFilesAreTracked` checks that; `-f` stages it either way).
- **TR-33-09.3 (extract)** Create `scripts/extract_corpus_guard_truth.do` with the root guards of scripts/extract_by_text_truth.do (re-read it: DASH_REPO checks, `adopath ++`, `set graphics off`, `global dash_nobrowser 1`, `version 19`). A first `python:` block inserts the repository root; reads `fixture = json.load(...)` of `<repo>/test/fixtures/corpus_guard_truth.json` when that file exists (else `fixture = None`); takes `ids = guard.read_list()` and `need = [i for i in ids if fixture is None or i not in fixture["examples"]]`; only when `need` is not empty runs `extract.extract(<c(sysdir_stata)>, <repo>, "<tmp>/x")` (the guard's ids are help-file examples, so whether g.pdf is read changes nothing); then `recs = guard.records_from_run("<tmp>/x" if need else None, ids, fixture)` (D-33-09.g: a listed id's frozen record is reused), `guard.write_examples(recs, "<tmp>/g")` and `guard.guard_do(<recs in id order>, "<tmp>/g", datasets.cache_dir(), <repo>)`, and sets the local `gdo`; then `do "\`gdo'"`; `shell git -C "<repo>" rev-parse HEAD > "<tmp>/head.txt"`, read into a local with `file read`; a second `python:` block runs `guard.measure("<tmp>/g", ...)` with the committed rules and ledger and writes `test/fixtures/corpus_guard_truth.json` = `{"_meta": {"stata_version", "born_date", "dash_commit" (the local, read through `Macro.getLocal`), "extracted", "source": "scripts/extract_corpus_guard_truth.do", "rules": "test/fixtures/corpus_verdict_rules.json", "ledger": "test/fixtures/corpus_ledger.json"}, "examples": {<id>: {"record": recs[id], <measure's row>}}}` (sorted keys, 2-space indent; a backtick written `\x60`; no `shell=True`). GENERATORS row `"corpus_guard_truth.json": "scripts/extract_corpus_guard_truth.do"`, in alphabetical position.
- **TR-33-09.4 (block)** Insert directly below the line `* ==== end S00 ====` and the blank line after it -- that is, above S10's helpers and its first header, `* ==== S10 TR-11: value_truth probe by probe ====`, the first block with a higher `S<MM>` (BRIEF "Block order"; R1-29) -- the python helpers and then the block. Helpers (one top-level `python:` block, as WP-31's): `_w33s09_prepare(fixture, run, repo)` (writes `<run>/examples.jsonl` from the fixture's records with `guard.write_examples`, calls `guard.guard_do(..., datasets.cache_dir(), repo)`, sets the local `gdo`, and sets the global `w33_s09_chrome` to 1 or 0 from `responsive_probe.find_chrome()`); `_w33s09_judge(fixture, run)` (`guard.measure` with the fixture's `_meta.rules` and `_meta.ledger`, `guard.compare` against the fixture's rows, globals `w33_s09_n` (problem count) and `w33_s09_bad` (the first 10 messages joined by `"; "`, at most 2,000 characters), and `shutil.rmtree(run, ignore_errors=True)` in a `finally`). Each helper inserts the repository root (`os.path.abspath("..")`, the cscript's parent, as `adodir ".."` gives it) and `<repo>/test` at `sys.path[0]` and removes them after. The block: `* ==== S09 tool: corpus guard ====` / `local only : env WP33_ONLY` / `` if inlist("`only'", "", "S09") & `: list posof "S09" in w33_run' { `` / `display as text "S09 start " c(current_date) " " c(current_time)` / `local run "\`w33_work'/s09"` / `python: __import__("__main__")._w33s09_prepare(...)` / when `${w33_s09_chrome}` is 0, `_w33_expect Q3309-1 "(0)" "headless Chrome not found; the guard cannot run"`; else `do "\`gdo'"`, `python: __import__("__main__")._w33s09_judge(...)` and `_w33_expect Q3309-1 "(\${w33_s09_n} == 0)" "\${w33_s09_bad}"` / `_w33_done Q3309-1 "the guard's examples draw the recorded twoway and dash pictures and verdicts"` / `macro drop w33_s09_*` / `dash clear` / `display as text "S09 end " c(current_date) " " c(current_time)` / `}` / `* ==== end S09 ====`.
- **TR-33-09.5 (tests)** Create `test/test_corpus_guard.py` (temporary folders; none runs Stata or Chrome): `TestReadList::test_ignores_comments_and_blanks`; `TestCandidates::test_help_shipped_setup_words_only`; `TestSelect::test_one_per_type_smallest_id_away_from_t_same` (an example 0.005 from T_same is passed over; with `T_same` null no SSIM condition applies; a type with no candidate is returned as skipped); `TestRecordsFromRun::test_a_missing_id_is_refused`, `::test_reuses_the_fixtures_records` (a fixture whose record for id `a` differs from the run's record for `a`: the fixture's is returned; id `b`, only in the run, comes from the run; with `run_dir` None and every id in the fixture no file is read); `TestWriteExamples::test_sorted_jsonl`; `TestGuardDo::test_wraps_the_runners_do_files` (guard_tw.do equals `twoway_run.do_text(...)` and guard_dash.do equals `dash_run.do_text(...)` for the same arguments; guard.do saves and restores `c(scheme)`, `c(linesize)`, `$S_ADO` and `$dash_nobrowser`, `preserve`s and `restore`s, opens and closes the two named logs, holds no `permanently`), `::test_no_absolute_path_but_the_run_folder_and_repo`; `TestMeasure::test_rows_from_canned_logs` (two canned logs, `dash_run.export_pages`, `dash_run.CorpusProbe` and `verdict.judge` monkeypatched to stubs: the dash row passed to judge carries `svg == "dash/<id>.svg"` and the export's `size_matched`; a failed export gives `export_error`; the returned row has exactly the ten keys); `TestCompare::test_equal_rows_pass`, `::test_a_worse_verdict_fails`, `::test_an_improvement_fails_and_names_the_ledger_and_the_script`, `::test_a_new_check_fails`, `::test_a_changed_rc_fails` (the message is `<id>: rc_dash was <old> now <new>: ...` and names scripts/extract_corpus_guard_truth.do); `TestMain::test_select_prints_the_lines_and_the_skipped_types` (`guard.main(["--select", <a fake run folder>])` over a tmp run of examples.jsonl, twoway.jsonl and verdicts.jsonl holding a scatter and a line candidate and no contour one; `capsys` shows the two `<id>  # <plottype>: ...` lines in id order and `skipped: ` naming `contour` among the types with no candidate); `TestTheList::test_about_twenty_distinct_types` (18 to 24 ids, at least 15 distinct plot types, every id a key of the fixture's `examples`); `TestTheFixture::test_meta_and_rows` (the seven meta keys; every row's `record` has 33-02's keys and `id` equal to its key; `verdict` in Same, Close, Differs; every `ledger` id an id of GAPS4.md).

## Boundaries

- No do-file text, log parsing, export, normalisation or scoring logic here (D-33-09.a): 33-03's and 33-04's texts and readers and 33-05's `judge` decide. No edit of scripts/corpus/ files other than the two new ones.
- No change to the truth script's frame (33-01's head-and-tail pin), the Makefile, README, docs/ or .gitignore (33-08's).
- No `set ..., permanently`, no `graph set`; no browser other than Chrome (R14).

## Stata truth

`scripts/extract_corpus_guard_truth.do` (new) extracts the guard's examples, runs them in twoway and dash and records the verdict rows: `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`; `git add -f test/fixtures/corpus_guard_truth.json`. Live case Q3309-1 (block `S09 tool: corpus guard`).

## TDD test stubs

- Test: `test/test_corpus_guard.py::TestReadList::test_ignores_comments_and_blanks` and the other tests of TR-33-09.5 (17 tests) -- red at the base: `scripts/corpus/guard.py` missing.
- cscript: `Q3309-1` -- red at the base (no module, no fixture).
- Pinned tests to flip: none. Parity entries: none.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| guard module functions | pytest test_corpus_guard.py | tmp files, canned logs | -- |
| list and fixture shape | pytest | corpus_guard_truth.json | -- |
| twenty examples, twoway vs dash | cscript Q3309-1 (cert tier, Chrome) | corpus_guard_truth.json | saved page (the corpus's mode) |

- **AC-33-09.1** `python3 -m pytest test/test_corpus_guard.py -q` passes under the development Python and under `/opt/anaconda3/bin/python3`.
- **AC-33-09.2** The S09 block prints `Q3309-1 PASS` through the driver twice in a row; the block's seconds (from its start and end lines) are reported.
- **AC-33-09.3** One commit ending `(WP-33 33-09)`.

## Tasks

**Commit boundary.** One commit by 33-09-04: `Add the twenty-example corpus guard to the certification suite (WP-33 33-09)`. Branch `wp33-s09` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s09`; every command runs from `$WT`. This section closes no GAPS4 item, so BRIEF's ledger and known-differences steps ("The corpus ledger and the known-differences tables") have nothing to delete here; its commit task pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main) before it commits.

<task type="auto" id="33-09-01">
  <name>Write the guard's tests and block red</name>
  <files>test/test_corpus_guard.py, test/test_wp33_truth.cscript</files>
  <action><![CDATA[In worktree $WT (wp33-s09), first read the landed scripts/corpus/ modules of 33-02..33-05 and check every name and signature of D-33-09.a against them; a difference stops the section (report it). Create test/test_corpus_guard.py (TR-33-09.5) and insert the S09 helpers and block of TR-33-09.4 directly below `* ==== end S00 ====` and its blank line (above S10's helpers). Run `python3 -m pytest test/test_corpus_guard.py -q -n0 -p no:cacheprovider > <scratch>/s09/01.log 2>&1` and the block with `WP33_ONLY=S09` through BRIEF's two-line driver; save both failures to <scratch>/33-09-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "ERROR\|FAILED" <scratch>/s09/01.log` is at least 1; the driver log holds `Q3309-1` FAIL text; `python3 -m pytest test/test_cscript_hygiene.py -k "TestTheWpTruthScripts" -q -p no:cacheprovider` passes (the block's head, gate and order are well formed).]]></verify>
  <done>The guard's unit tests and certification block existed and failed for want of the module and fixture.</done>
</task>

<task type="auto" id="33-09-02">
  <name>Write the guard module and list</name>
  <files>scripts/corpus/guard.py, scripts/corpus/guard_examples.txt</files>
  <action><![CDATA[Create scripts/corpus/guard.py (TR-33-09.1) on 33-02..33-05's landed functions. Choose the list by D-33-09.b on a candidate run: `python3 scripts/corpus/extract.py --out <scratch>/s09/run`; rewrite its examples.jsonl to the records `guard.candidates(<its records>, datasets.shipped(<Stata's folder>))` keeps; run `twoway_run.py --run`, `dash_run.py --run` and `verdict.py --run` on `<scratch>/s09/run`; then `python3 scripts/corpus/guard.py --select <scratch>/s09/run > <scratch>/s09/list.txt` and write scripts/corpus/guard_examples.txt from its id lines with TR-33-09.2's header (its last line, `skipped: ...`, goes to the commit body, not the list). Run `python3 -m pytest test/test_corpus_guard.py -q -n0 -p no:cacheprovider -k "not TestTheList and not TestTheFixture"` and the same under `/opt/anaconda3/bin/python3 -m pytest ... -p no:randomly`.]]></action>
  <verify><![CDATA[Both runs pass; `grep -vc "^#\|^$" scripts/corpus/guard_examples.txt` prints a number from 18 to 24.]]></verify>
  <done>The guard module and its example list existed and their unit tests passed in both Pythons.</done>
</task>

<task type="auto" id="33-09-03">
  <name>Record the expected verdicts</name>
  <files>scripts/extract_corpus_guard_truth.do, test/fixtures/corpus_guard_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_corpus_guard_truth.do (TR-33-09.3) and its GENERATORS row (a dict entry, no function edited); run it through the slot; `git add -f test/fixtures/corpus_guard_truth.json`. Read the fixture: every listed id has a row with its record, no string matches `^/(Users|private|var|tmp|home|Applications)/`. Run `python3 -m pytest test/test_corpus_guard.py test/test_fixtures_are_committed.py -q -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/corpus_guard_truth.json'));print(len(d['examples']), sorted(d['_meta']))"` prints the list's length and the seven meta keys; both pytest files pass.]]></verify>
  <done>The guard's examples and expected verdicts were committed truth from the committed script.</done>
</task>

<task type="auto" id="33-09-04">
  <name>Run the guard green and commit</name>
  <files>none</files>
  <action><![CDATA[Run the S09 block with `WP33_ONLY=S09` (Q3309-1 PASS); then run it a second time to show it does not flap (both PASS); note its seconds from the `S09 start`/`S09 end` lines. Run `python3 -m pytest test/test_corpus_guard.py test/test_cscript_hygiene.py test/test_fixtures_are_committed.py test/test_corpus_functions.py -q -p no:cacheprovider`. No existing function is edited (the GENERATORS dict gains a row), so no impact run is needed. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main). Run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (new files, the dict and the cscript only). Stage by path: `git add scripts/corpus/guard.py scripts/extract_corpus_guard_truth.do test/test_corpus_guard.py test/test_fixtures_are_committed.py test/test_wp33_truth.cscript`, `git add -f scripts/corpus/guard_examples.txt test/fixtures/corpus_guard_truth.json` (R1-9, R7); confirm `git merge-base --is-ancestor s3-bugs HEAD`; commit on wp33-s09 with the body: what the guard runs, the list's types and any type D-33-09.b skipped, `Regression: test/test_corpus_guard.py::TestCompare::test_a_worse_verdict_fails -- failed at <base> with ModuleNotFoundError: No module named 'scripts.corpus.guard'`, `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`, `Seconds: S09 <n>`; grep the message for claude|anthropic before and after.]]></action>
  <verify><![CDATA[The two driver logs both show `Q3309-1 PASS`; the pytest run passes; `git log -1 --format=%s` ends `(WP-33 33-09)`; `git ls-files scripts/corpus/guard_examples.txt test/fixtures/corpus_guard_truth.json` prints both paths; the claude|anthropic grep prints 0.]]></verify>
  <done>The certification suite ran about twenty corpus examples against their recorded verdicts, and the guard was committed.</done>
</task>

## Section completion criteria

- One commit on wp33-s09; Q3309-1 PASS twice in a row; test_corpus_guard.py green in both Pythons; the fixture committed with complete `_meta`, the frozen records and no absolute path; the frame of test_wp33_truth.cscript unchanged; S09 placed above S10 (blocks in section order); the block's seconds in the hand-back.

## Notes

- **guard.do** (D-33-09.d; written by `guard.guard_do`, `<run>` its run folder):

````stata
* guard.do -- written by scripts/corpus/guard.py (WP-33 33-09); leaves the session as it found it
local _g_scheme "`c(scheme)'"
local _g_ls = c(linesize)
local _g_ado `"$S_ADO"'
local _g_nb `"$dash_nobrowser"'
preserve
capture log close s09tw
log using "<run>/tw/guard.log", text replace name(s09tw)
capture noisily do "<run>/tw/guard_tw.do"
local _g_rc1 = _rc
log close s09tw
capture graph drop _all
capture log close s09da
log using "<run>/dash/guard.log", text replace name(s09da)
capture noisily do "<run>/dash/guard_dash.do"
local _g_rc2 = _rc
log close s09da
restore
set scheme `_g_scheme'
set linesize `_g_ls'
global S_ADO `"`_g_ado'"'
global dash_nobrowser `"`_g_nb'"'
capture graph drop _all
capture serset clear
dash clear
display "GUARD-DONE `_g_rc1' `_g_rc2'"
````

- **For later WPs (WP-34..49).** Every item's closing task runs BRIEF's three closing steps ("The corpus ledger and the known-differences tables"): (1) delete the item's plain rows of `scripts/corpus/ledger.tsv` and run `python3 scripts/corpus/ledger.py` (D-33-05.i); (2) run `python3 test/known_differences.py <lead id>`, delete every row it prints (a kept difference moves to its table's deliberate dict) and run the hygiene command it prints (D-33-10.h); (3) run this block (`WP33_ONLY=S09`) and, when Q3309-1 reports any change for a guard example -- `<id> improved from ...` or `<id>: <field> was <old> now <new>` -- regenerate this fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` in that item's commit, run the block again until it prints `Q3309-1 PASS`, and `git add -f` the fixture (the regeneration keeps each listed id's frozen record and re-measures only the verdict rows, D-33-09.g); never hand-edit the fixture (R7). Both messages say so. A later section reads the fixture's `examples[<id>]["ledger"]` to see whether a guard example carries its id (35-07 does).
- **Privacy (Q36).** Stata's batch log starts with the licence banner (the licensee's name and serial number): the guard reads only its two named logs, opened after the banner, through 33-03's `parse_log`, and nothing from a log reaches the fixture but rc and first lines (with the cache and run folders replaced, TR-33-03.3).
- **Merge rules:** R1 (one `tool:` block, in section order), R7, R10 (no count pin moves: no new cscript), R14.
- **Help paragraphs owned:** none.
- **Commit body line forms:** `Regression: test/test_corpus_guard.py::TestCompare::test_a_worse_verdict_fails -- failed at <base> with ModuleNotFoundError`; `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`; `Seconds: S09 <n> (two runs: <a>, <b>)`.
