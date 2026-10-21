# Section 33-03: twoway runner -- SVG at each example's own size

> Part of: WP-33 (Verification corpus and README gallery) · Items: none (TR-2 closes in 33-14) · Risk: yellow · Batch: 33.3 · Depends on: 33-02 · Blocks: 33-04, 33-05, 33-09 · Tasks: 3, 1 commit · Case-id prefix: Q3303 (none used)

## Overview

The corpus has commands (33-02) but no truth: nothing runs twoway over them, so "No picture comparison over a broad corpus (109 gr_example commands run here only once, by hand)" (audit TR-2). twoway's own picture is available in console batch: `graph export x.svg` "works in batch, rc 0", is "byte-identical" across sessions, and records the graph's size in inches on its root element [S §2].

After this section, `python3 scripts/corpus/twoway_run.py --run <run>` reads `<run>/examples.jsonl`, writes do-files that run every example under twoway in chunks, runs them through `scripts/stata_slot.sh` (up to three at once), and writes `<run>/twoway.jsonl` -- per example its return code, the first line twoway printed, the SVG path and the size twoway drew it at -- plus `<run>/twoway/<id>.svg`. The size is each example's own (C2): its scheme's default (7.5 x 4.5 in under stcolor) or its own `xsize()`/`ysize()`. 33-04 renders dash at that size; 33-05 compares.

**Test order and commit rule.** Task 33-03-01 writes the unit tests red (module missing) and saves `<scratch>/33-03-01-failure.txt`; 33-03-02 writes the module green; 33-03-03 runs it on a 12-example sample through Stata, checks the results and commits once: `Add the corpus twoway runner (WP-33 33-03)`.

### Section decisions

- **D-33-03.a (markers and the first line).** Each example runs between `display "##BEGIN <id>"` and `display "##RC <id> " _rc`, with `capture noisily` around the command (the [S] harness, "Shared probe harness"). The first message line is the first non-blank log line after the `##SETUP <id> <rc>` line and before the `##RC <id>` line that is not an echo (`^\. `, `^> ` or a numbered continuation `^\s*\d+\. `) and not a `##` marker. Starting after `##SETUP` matters: the setup's own output sits between `##BEGIN` and `##SETUP` -- a live probe of this do-file shape (REVIEW-1 R1-11) printed `(1978 automobile data)` there, before `option nosuch not allowed`, and the old rule took it as every refusal's first line. `set linesize 255` at the top of each do-file keeps messages on one line.
- **D-33-03.b (size).** Size = the exported SVG's root `width`/`height` in inches (`<svg width="7.500in" height="4.500in" ...>`); a `width="1000px"` form (from `graph export ..., width()`) is never produced because the runner never passes `width()`.
- **D-33-03.c (state between examples).** Before each example: `clear`, `graph drop _all`, `discard` is not used (it reloads dash's programs in the dash runner and is slow); the setup lines run under `capture noisily`, their rc written as `##SETUP <id> <rc>`; a nonzero setup rc skips the command (`rc` null, `skip: "setup rc <n>"`).
- **D-33-03.d (chunks, timeouts and dead chunks).** 25 examples per do-file, except that each `contour` or `contourline` example is a chunk of its own (scattered-data contour grows about as n^4, [S §6], so one slow example must not take 24 siblings with it); each chunk in its own folder `<run>/tw/c<k>/` (its own STATATMP through stata_slot.sh); `--jobs 3` chunks at once. A chunk killed after `--timeout` seconds (default 1800) marks its unreported examples `skip: "timeout"` and prints `corpus: chunk <k> timed out; if no stata-mp process is left, remove a stale /tmp/dash-stata-slot-<n>.d` (stata_slot.sh's lock). A chunk whose Stata ends without a timeout before every example printed `##RC` (a crash, an r(9xx) outside `capture`) marks each such example `skip: "chunk ended early (rc <n>)"`, `<n>` the slot script's exit status. The runner never starts Stata itself.
- **D-33-03.e (no preference changes).** The do-files set no scheme, no `graph set`, nothing `permanently` (BRIEF); the scheme is the session default (stcolor here, [S] header).
- **D-33-03.f (a dataset missing from the cache; DECISIONS A-26, D-33-02.c).** Before chunking, `run()` passes each example's setup through `datasets.rewrite_setup(setup, datasets.cache_dir())`; an example whose `missing` list is not empty is put in no chunk (no Stata line runs for it) and gets the row `rc` None, `first_line` None, `setup_rc` None, `export_rc` None, `svg` None, `skip: "dataset <name> not cached"` (`<name>` the first name of its `missing` list, which `rewrite_setup` gives in setup order). The run prints `skip: dataset <name> not cached` exactly once per missing dataset, in name order, whatever number of examples lack it, before the counts line: an example that lacks two datasets is counted under both, so a dataset that is only ever an example's second missing one is named too (A-26). The counts' `skipped` includes these examples.

## Risk: [yellow] -- long Stata runs driven from Python

**Why.** 600 examples take minutes per chunk; a stuck example could hold a slot. **Risk factors.** Log parsing (echo lines, wrapped lines), size parsing, setup failures, the slot lock after a kill. **Mitigation.** Unit tests on inline log and SVG text; the timeout path names the manual recovery; task 33-03-03 runs a 12-example sample covering every source and one failing command.

## Dependencies

- **Depends on:** 33-02 (`examples.jsonl`, `datasets.rewrite_setup` and `datasets.cache_dir`, whose `missing` list D-33-03.f reads).
- **Blocks:** 33-04 (dash renders at the sizes recorded here), 33-05.
- **Parallel batch 33.3:** 33-07, 33-11 -- disjoint files.

## Evidence

- [S §2]: `graph export x.svg` in batch, message `file x.svg saved as SVG format`; default 7.5 x 4.5 in (`<svg width="7.500in" height="4.500in" viewBox="0 0 5400 3240">`, 720 units per inch); `xsize(8) ysize(4)` gives `8.000in x 4.000in`; deterministic (cmp across sessions); `<desc>Stata Graph - <name></desc>` holds the graph name, no path or time.
- `test/cert_svg.do:157-183` `cert_svg_export, name() file()` uses `graph export ..., as(svg) replace` -- the same call this runner writes.
- `scripts/stata_slot.sh:1-17`: `stata_slot.sh <dir> <file.do>` runs from `<dir>` with `STATATMP=<dir>/tmp/`, holding one of three `/tmp/dash-stata-slot-<n>.d` locks; the log is `<dir>/<file>.log`.
- [S §6]: `twoway__contour_gen` on scattered data grows about as n^4 (1,000 points unfinished after 12 min) -- the reason for D-33-03.d's timeout; every gridded sandstone example takes 0.2 s.

## User stories

- US-33-03.1 As the maintainer, I want twoway's own SVG, return code and message for every corpus example so that each dash picture is judged against Stata's.

## Business requirements

- BR-33-03.1 Every example in `examples.jsonl` ends with a twoway record: an rc and first line, or a skip reason.
- BR-33-03.2 Each SVG is twoway's picture at the size twoway drew that example.
- BR-33-03.3 The run changes no Stata preference and leaves no Stata slot held.
- BR-33-03.4 An example whose dataset is not in the offline cache is skipped with a reason naming the dataset, and each missing dataset is named once in the run's output (A-26).

## Technical requirements

- TR-33-03.1 Create `scripts/corpus/twoway_run.py` with these public functions (one unit test each):
  - `do_text(examples, out_dir, cache) -> str`: the do-file for one chunk: `version 19`, `set more off`, `set linesize 255`, `display "##VERSION " c(stata_version)`, then per example, in this order: `display "##BEGIN <id>"`; `clear`; `capture graph drop _all`; the setup lines (after `datasets.rewrite_setup`) inside one `capture noisily {` ... `}` block; `display "##SETUP <id> " _rc`; `if _rc == 0 {`; `capture noisily <cmd>`; `display "##RC <id> " _rc`; `if _rc == 0 capture noisily graph export "<out_dir>/<id>.svg", as(svg) replace`; `display "##EXPORT <id> " _rc`; `}`. An example with no setup line still gets the empty block (so `##SETUP <id> 0` is always printed).
  - `parse_log(text) -> dict[str, dict]`: id -> `{"setup_rc", "rc", "first_line", "export_rc"}` from the markers, plus the key `"_version"` -> the `##VERSION` value (e.g. `"19.5"`; 33-05 stamps it into its fixtures' `_meta`), with D-33-03.a's first-line rule (strip trailing blanks; None when no line).
  - `svg_size(path) -> tuple[float, float] | None`: inches from the root `<svg>` `width`/`height` (`in` suffix; `px` divided by 96; None if neither).
  - `chunks(examples, size=25) -> list[list[dict]]` (D-33-03.d: a `contour`/`contourline` example alone in its chunk; the others in id order, `size` at most).
  - `missing_datasets(examples, cache) -> dict[str, list[str]]`: D-33-03.f's split, without running Stata: each missing dataset name -> the ids (sorted) of every example whose `rewrite_setup` `missing` list holds it (an id lacking two datasets is under both keys); an example with nothing missing is in no list. Its keys, in name order, are the run's `skip:` lines.
  - `skip_rows(examples, cache) -> list[dict]`: the twoway.jsonl rows of D-33-03.f, in id order, for every example whose `rewrite_setup` `missing` list is not empty (TR-33-03.4's keys; `skip: "dataset <name> not cached"`, `<name>` that list's first name).
  - `records(examples, parsed, svg_dir, run_dir) -> list[dict]`: the twoway.jsonl rows of one parsed log without running Stata -- for each example, its `parse_log` entry (or the D-33-03.d skip when it has none), the SVG `<svg_dir>/<id>.svg` moved to `<run_dir>/twoway/<id>.svg` when `export_rc` is 0, its `svg_size`, and TR-33-03.3's path replacement. `run()` calls it per chunk; 33-09 calls it on a log it made in its own Stata session.
  - `run(run_dir, jobs=3, timeout=1800, only=None) -> dict`: reads `<run_dir>/examples.jsonl` (`only` = a set of ids), sets aside every example `missing_datasets(examples, datasets.cache_dir())` names, printing D-33-03.f's one `skip: dataset <name> not cached` line per key of that map, in name order, and adding `skip_rows(examples, datasets.cache_dir())` to the output (when no example is left, no chunk folder is made and no Stata session starts), then writes `<run_dir>/tw/c<k>/twoway.do`, runs `sh <repo>/scripts/stata_slot.sh <run_dir>/tw/c<k> <run_dir>/tw/c<k>/twoway.do` with `subprocess.Popen(..., start_new_session=True)` at most `jobs` at once, kills a chunk's process group (`os.killpg(p.pid, signal.SIGTERM)`) after `timeout`, parses each `twoway.log`, turns each into rows with `records` (which moves each SVG to `<run_dir>/twoway/<id>.svg`), writes `<run_dir>/stata_version.txt` (the first chunk's `_version`), and writes `<run_dir>/twoway.jsonl` (sorted by id; keys `id, rc, first_line, setup_rc, export_rc, svg, width_in, height_in, skip`; `svg` relative to `<run_dir>`); returns counts `{"rc0", "refused", "skipped"}`.
  - `main(argv)`: `--run <dir>` (required), `--jobs`, `--timeout`, `--only <id,id,...>`; prints the counts.
- TR-33-03.2 SVG files are written by `graph export` into `<run_dir>/tw/c<k>/svg/` and moved; their content is not edited (normalisation for the gallery is 33-04's `normalise_svg`, applied by 33-08 when it copies files to docs/).
- TR-33-03.3 The records hold no absolute path (Q36): `svg` is relative; `first_line` is Stata's text, which for a refused `use` could hold the cache path -- `records()` replaces the cache directory (`datasets.cache_dir()`) and the run directory in `first_line` by `<cache>` and `<run>`.
- TR-33-03.4 (Published interface; 33-04, 33-05, 33-09 rely on it). `twoway_run.SLOT_CMD` (list); `do_text(examples, out_dir, cache) -> str` (the markers `##VERSION`, `##BEGIN <id>`, `##SETUP <id> <rc>`, `##RC <id> <rc>`, `##EXPORT <id> <rc>`, each on its own line); `parse_log(text) -> dict` (D-33-03.a; key `"_version"`); `records(examples, parsed, svg_dir, run_dir) -> list[dict]`; `chunks`; `svg_size`; `missing_datasets(examples, cache) -> dict`; `skip_rows(examples, cache) -> list[dict]` (33-04's runner calls both); `run(run_dir, jobs=3, timeout=1800, only=None) -> dict`. A missing dataset's examples carry `skip: "dataset <name> not cached"` (D-33-03.f), which 33-05's `judge` reads like any other skip; 33-04's runner sets the same examples aside by the same two functions (D-33-04.g). Files: `<run>/twoway.jsonl` rows `{id, rc, first_line, setup_rc, export_rc, svg, width_in, height_in, skip}` (`svg` relative to the run folder or None; `rc` None when skipped), `<run>/twoway/<id>.svg` (as Stata wrote it), `<run>/stata_version.txt`. CLI `python3 scripts/corpus/twoway_run.py --run <run> [--jobs N] [--timeout S] [--only id,id]`. The module follows 33-02's import convention (D-33-02.g).

## Boundaries

Do not touch any shipped file, the Makefile (33-08), test_wp33_truth.cscript (33-09 adds the guard block), 33-07's `_dash_register_graph`/`_dash_prepare_spec`/`_dash_write_data`/`_dash_build`, 33-11's test_graph_text.py.

## Stata truth

No fixture. Task 33-03-03 runs `python3 scripts/corpus/twoway_run.py --run <scratch>/c1 --only <12 ids>` (one chunk, one Stata session through stata_slot.sh) on the extract of 33-02's verification run.

## TDD test stubs

- Test: the do-file text, markers, setup block and export line -- test/test_corpus_twoway.py::TestDoText::test_markers_setup_and_export (asserts the exact lines for a two-example chunk, one with `webuse lbw` rewritten to the cache)
- Test: the log parser on an inline batch log with echoes, a wrapped echo (`> `), a numbered echo (`  2. `), a refused command (`option foo() not allowed` / `r(198);`) and a setup failure -- ::TestParseLog::test_rc_first_line_and_setup
- Test: setup output is never the first line -- ::TestParseLog::test_setup_output_is_not_the_message (a canned log with `(1978 automobile data)` between `##BEGIN a` and `##SETUP a 0`, then `option nosuch not allowed` before `##RC a 198`: `first_line == "option nosuch not allowed"`)
- Test: SVG sizes in inches and pixels -- ::TestSvgSize::test_inches_and_pixels (uses test/fixtures/svg_truth_smoke.svg, whose root says 7.500in x 4.500in, plus an inline px root)
- Test: chunking -- ::TestChunks::test_sizes (51 examples, one of them a contour: chunks of 25, 25 and the contour alone, or the contour alone and 25, 25 by id order)
- Test: a dataset missing from the cache -- ::TestMissingDatasets::test_one_line_per_dataset (a tmp cache holding `lifeexp2.dta` only; examples a and b set up with `webuse lbw, clear`, c with `webuse nhanes2l, clear`, d with `webuse lifeexp2, clear`, e with `sysuse auto, clear`, f with `webuse lbw, clear` then `webuse nlswork, clear`: `missing_datasets` gives `{"lbw": ["a", "b", "f"], "nhanes2l": ["c"], "nlswork": ["f"]}`; `skip_rows` gives four rows with `rc` None and `skip == "dataset lbw not cached"` (a, b, f: f's first missing name) or `"dataset nhanes2l not cached"` (c)), ::test_run_names_each_missing_dataset_once (`run()` with the fake slot command of TestRun on those six examples: captured stdout holds `skip: dataset lbw not cached`, `skip: dataset nhanes2l not cached` and `skip: dataset nlswork not cached` once each, in that order (nlswork is only ever a second missing dataset), the do-files written hold no line for a, b, c or f, and twoway.jsonl holds all six rows)
- Test: rows from a parsed log -- ::TestRecords::test_rows_from_a_parsed_log (a tmp svg_dir holding `a.svg` from test/fixtures/svg_truth_smoke.svg: the row has `svg == "twoway/a.svg"`, 7.5 x 4.5 in, and the file moved)
- Test: run() with a fake slot script (monkeypatch the command to `sh -c` writing a canned log) records rc, size and skips, and replaces paths -- ::TestRun::test_records_from_a_canned_log
- Test: timeout marks unreported examples -- ::TestRun::test_a_timeout_marks_the_rest (fake command `sleep 5`, timeout 1)
- Test: a chunk that dies marks its unreported examples -- ::TestRun::test_a_dead_chunk_marks_the_rest (a fake command that writes a log holding `##RC` for the first of three examples and exits 3: the other two get `skip: "chunk ended early (rc 3)"`)
- Function coverage stays green: test/test_corpus_functions.py
- Cert cases: none. Pins: none. Parity: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Do-file and parser | pytest test_corpus_twoway.py | inline text, svg_truth_smoke.svg | n/a |
| Live sample | twoway_run.py --only 12 ids via stata_slot.sh | 33-02's extract | n/a |

- AC-33-03.1 `python3 -m pytest test/test_corpus_twoway.py test/test_corpus_functions.py -q -n0` passes.
- AC-33-03.2 On the 12-example sample (4 help, 4 g.pdf, 2 examples/, 1 audit, plus `twoway scatter mpg weight, nosuch` added by hand to the `--only` run's examples.jsonl copy, its setup `sysuse auto, clear`): 11 records with rc 0, an SVG and a size (at least one 7.5 x 4.5, and one with its own `xsize()` if the sample holds one), and the hand-added one with rc 198 and first line `option nosuch not allowed` (not `(1978 automobile data)`).
- AC-33-03.3 After the run, `ls /tmp/dash-stata-slot-*.d` lists no slot this run left (compare with before).
- AC-33-03.4 A run folder `<scratch>/c3m` whose examples.jsonl holds every example of `<scratch>/c1` whose setup reads `webuse lbw` (one or more), run with `DASH_CORPUS_CACHE` pointed at an empty scratch folder, prints `skip: dataset lbw not cached` exactly once, creates no `<scratch>/c3m/tw/` folder (no Stata session: every example was set aside), and writes every one of their rows with `skip == "dataset lbw not cached"` (A-26).

## Tasks

**Commit boundary.** Tasks 33-03-01..03 form one commit by 33-03-03: `Add the corpus twoway runner (WP-33 33-03)`. Branch `wp33-s03` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s03`; every command runs from `$WT`. This section closes no GAPS4 item, so BRIEF's ledger and known-differences steps ("The corpus ledger and the known-differences tables") have nothing to delete here; its commit task pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main) before it commits.

```xml
<task type="auto" id="33-03-01">
  <name>Write the twoway runner tests red</name>
  <files>test/test_corpus_twoway.py</files>
  <action><![CDATA[ Create test/test_corpus_twoway.py with the stubs under TDD (class and test names exactly), importing `from scripts.corpus import twoway_run` after `sys.path.insert(0, <repo>)`. The canned log is an inline string in the shape of a console batch log: `. display "##BEGIN a"`, `##BEGIN a`, `. capture noisily {`, `. sysuse auto, clear`, `(1978 automobile data)`, `. }`, `. display "##SETUP a " _rc`, `##SETUP a 0`, `. if _rc == 0 {`, `. capture noisily twoway scatter mpg weight, nosuch`, `option nosuch not allowed`, `. display "##RC a " _rc`, `##RC a 198`. ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_corpus_twoway.py -q -n0 2>&1 | tee <scratch>/33-03-01-failure.txt | tail -3` shows every test erroring on the missing module. Nothing committed. ]]></verify>
  <done>The runner's rules have failing tests and the failure text is saved.</done>
</task>

<task type="auto" id="33-03-02">
  <name>Write the twoway runner module</name>
  <files>scripts/corpus/twoway_run.py</files>
  <action><![CDATA[ Create scripts/corpus/twoway_run.py with exactly the functions of TR-33-03.1 and the rules D-33-03.a..e. The slot script path is `os.path.join(repo, "scripts", "stata_slot.sh")` where repo is two levels above the module; tests replace it through a module constant `SLOT_CMD` (a list, default `["sh", <that path>]`). ]]></action>
  <verify><![CDATA[ `python3 -m pytest test/test_corpus_twoway.py test/test_corpus_functions.py -q -n0` passes. ]]></verify>
  <done>The twoway runner exists and its unit tests pass.</done>
</task>

<task type="auto" id="33-03-03">
  <name>Run a live sample and commit</name>
  <files>none</files>
  <action><![CDATA[ In <scratch>/c1 (33-02's verification run, or a fresh `python3 scripts/corpus/extract.py --out <scratch>/c1`), pick the 12 ids of AC-33-03.2 into a copy `<scratch>/c3/examples.jsonl` (append the hand-made refused example with id `test-nosuch-00000000`), record `ls /tmp/dash-stata-slot-*.d`, run `python3 scripts/corpus/twoway_run.py --run <scratch>/c3`, and check AC-33-03.2 and AC-33-03.3. Then copy every example of <scratch>/c1 whose setup reads `webuse lbw` into `<scratch>/c3m/examples.jsonl` and run `DASH_CORPUS_CACHE=<scratch>/empty_cache python3 scripts/corpus/twoway_run.py --run <scratch>/c3m` (`mkdir -p <scratch>/empty_cache` first) to check AC-33-03.4. Then `git add scripts/corpus/twoway_run.py test/test_corpus_twoway.py`, pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), confirm `git merge-base --is-ancestor s3-bugs HEAD`, run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (new files only), and commit (body: the failure summary, `Regression:` lines, and the sample's counts). ]]></action>
  <verify><![CDATA[ AC-33-03.2, AC-33-03.3 and AC-33-03.4 hold; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0. ]]></verify>
  <done>The twoway runner is committed and has drawn a live sample with twoway's own sizes and messages.</done>
</task>
```

## Section completion criteria

AC-33-03.1..4; one commit ending `(WP-33 33-03)`; the hand-back gives the sample's 12 ids, their sizes and rc, and the missing-dataset run's printed line.

## Notes

- **Traps.** (1) Echoed commands in a batch log start `. `; continuation echoes start `> `; loop and program bodies echo as `  2. `; never take those as the message, and never read before the `##SETUP` line. (2) `capture noisily` keeps `_rc`; read it on the very next line (`display ... _rc`). (3) Do not add `name()` or `width()` to the command (it changes what twoway draws and the SVG's units). (4) The examples' `xsize()`/`ysize()` stay in the command: that is "each example's own size". (5) Never `set scheme ..., permanently` or `graph set`. (6) A missing dataset is found from `rewrite_setup`'s `missing` list before any do-file is written (D-33-03.f): never let a `use` of an absent cache file reach Stata and read its r(601) as the example's answer.
- **Merge rules touched:** R14. **Help paragraphs owned:** none.
- **Commit-body line forms:** `Regression: test/test_corpus_twoway.py::<Class>::<test> -- failed at <sha> with ModuleNotFoundError`; `Sample: 12 examples, <n> rc 0, <n> refused, sizes <list>`; `Offline: skip: dataset lbw not cached, printed once for <n> examples`.
