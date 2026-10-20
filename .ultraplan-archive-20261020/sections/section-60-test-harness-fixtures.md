# Section 60: Test harness, fixtures, parity profile, lint and CI

> Part of: WP-31 · GAPS3 rows: K2, K3, K4, H6, I6 · Risk: yellow · Batch: 20 · Depends on: 10, 51 · Blocks: -- · Tasks: 8, 5 commits · Case-id prefix: U60

## Overview

**What is wrong today.** Five S3 rows about the suite itself. GAPS3 K3 (GAPS3.md:283): "16 fixtures with no committed generator; 9 carry absolute paths; no `make truth`; no metadata guard". Measured at `6370ca4` (probe over test/fixtures/*.json against scripts/): the fixtures with no `scripts/` generator naming them are ci_plot_index_truth.json, fp_edge_truth.json, geometry_truth.json, kpi_pctile_truth.json, kpi_truth.json, linewidth_chain_truth.json, marker_linewidth_truth.json, mband_band_edges.json, natscale_axes_truth.json, natscale_truth.json, qualified_stat_truth.json, rejected_options.json (12 files) plus the two helper-written ones whose generator is a `.py` without a Stata source (ci_band_style_truth.json and scheme_truth.json via scripts/extract_scheme_truth.py, color_truth.json via extract_color_truth.py -- generated, so not counted) and the directories test/fixtures/data and test/fixtures/scheme_visual (16 with GAPS3's count including help_examples.txt and conformance_corpus.txt); absolute paths (`/Users/`, `/private/tmp`, `/var/folders`) appear in abbrev_truth.json, date_truth.json, geometry_truth.json, rejected_options.json, qualified_stat_truth.json and ts_operator_truth.json (6 files at this commit; GAPS3 counted 9 at an earlier one). GAPS3 K4 (:284): the `_Served` fixture leaks a process when `__enter__` fails (test/test_server_serves.py:123-142: the `raise AssertionError("bokeh serve never answered")` at :142 and the early-exit raise at :133 both leave `self.proc` running). GAPS3 K2 (:282): six Stata end-to-end gaps. GAPS3 H6 (:243): the move profile compares glyphs, labels, arrowheads and KPI cards only (test_mode_parity.py:3247-3298) although `_figure_profile` (:911) records `axes` and `chrome`; the oracle is the saved renderer re-run with an `if` (:2802), never the saved page's JS; no slider-on-yaxis(2) entry. GAPS3 I6 (:264): no CI workflow, no lint target, no secrets scan; `*.log` excluded only in `.git/info/exclude:130`; `.claude/hooks/*` git-ignored.

**After this section** every fixture has a committed generator (an extract `.do` or a documented `.py`) and `make truth` runs them all; a guard test refuses a fixture without a complete `_meta` or with an absolute path; the `_Served` fixture terminates its process on every failure path; the six K2 gaps are cscript cases in the truth script; the parity move profile compares axes, ranges, legend items and chrome after a move, has a slider-on-`yaxis(2)` entry and a saved-JS move oracle (the page's own `_FILTER_JS` run under node) beside the renderer re-run; `make lint` runs ruff with a committed baseline; a secrets test scans the tree; a GitHub Actions workflow runs `make test-dev` and `make lint` on `ubuntu-latest` (a comment in it names macOS as the certified platform); `.gitignore` carries `*.log`; the hooks are documented (not tracked: they hold machine paths).

**Why one section.** All five are suite infrastructure with no twoway content; S60 depends on S10 (the JS prelude the saved-JS oracle runs) and S51 (brush entries in the move corpus).

**Test order and commit rule.** Five cycles, five commits in row order K4 (the leak first, it protects every later run), K3, K2, H6, I6; each row's failing tests written on the tree the previous commit leaves.

### Section decisions (binding on the executor)

- **D-60a. Generators.** One extract script per Stata-sourced fixture: `scripts/extract_ci_plot_index_truth.do`, `extract_fp_edge_truth.do`, `extract_geometry_truth.do`, `extract_kpi_pctile_truth.do`, `extract_kpi_truth.do`, `extract_linewidth_chain_truth.do`, `extract_marker_linewidth_truth.do`, `extract_mband_band_edges.do`, `extract_natscale_axes_truth.do`, `extract_natscale_truth.do`, `extract_qualified_stat_truth.do`, `extract_rejected_options.do`. Each REPRODUCES the committed fixture's keys (read the fixture and its reading test to learn the probes: e.g. kpi_truth.json's `kpi_stats.all/foreign1` are `summarize mpg, detail` r() values on `sysuse auto` whole and `if foreign`; kpi_pctile_truth.json's scopes are `_pctile`; natscale_*.json are `.Graph` axis ranges of `twoway ... , xscale(natscale)`; rejected_options.json is `capture twoway ...` rc/text pairs; geometry_truth.json holds `.plotregion1` sizes; mband_band_edges.json is `twoway mband, bands(#)`'s `_mbandgen` output). A regenerated fixture replaces the committed one; a value difference is a finding (reported in the commit body), and the test that reads it decides. help_examples.txt and conformance_corpus.txt are text corpora written by hand: a header line `# hand-written corpus; no generator (S60 D-60a)` is added and the guard exempts files whose first line says so. test/fixtures/data (datasets) and scheme_visual (SVG renders from scripts/svg_truth.py) are exempt by directory.
- **D-60b. `_meta` and path guard.** `test/test_fixtures_are_committed.py` gains `class TestEveryFixtureHasMeta` (REVIEW-4 R4-29: that file already pins fixture <-> test and `.do` <-> test naming at :213 and :232, so the new checks join it as classes reusing its `_fixture_files()` list; no `test_fixture_meta.py`): every `test/fixtures/*.json` (not under data/ or scheme_visual/) has a `_meta` object with keys `stata_version`, `born_date`, `dash_commit`, `extracted`, `source` (older fixtures with `generated_by`/`run_date` are migrated by regeneration -- the new generators write the five keys), and no string anywhere in the file matches `^/(Users|private|var|tmp|home)/` or `^[A-Z]:\\`. The six absolute-path fixtures are regenerated with paths relative to the repo (`_meta.source = "scripts/extract_x_truth.do"`; a probe's path field is written as its basename).
- **D-60c. `make truth`.** Target: `truth:` runs every `scripts/extract_*_truth.do` and `scripts/extract_*.do` through `scripts/stata_slot.sh` sequentially (one slot; the python_exec hazard forbids concurrency) with `DASH_REPO=$(CURDIR)`, then the three `.py` generators; prints each fixture's path; `make truth-check` runs `test/test_fixtures_are_committed.py` (which now holds the `_meta`/path/generator guard, R4-29). Never part of `make test`.
- **D-60d. The leak.** `_Served.__enter__`: wrap the wait loop in `try: ... except BaseException: self.__exit__(None, None, None); raise` (the pattern `_CspProbe.__enter__` uses, test_csp_browser.py:213-216); the same in `_Launched.__enter__` (:183ff).
- **D-60e. K2's six cases** are cscript cases in the truth block S60 (`U60-1..U60-6`): (1) served layer output -- `_dash_serve_spec` then a `python:` block importing the generated app and asserting a histogram layer's served source has the bins the saved page has; (2) computed layers on `%t` variables served (an lfit on a `%td` x in the served document equals the saved one's x range); (3) the serve start line in the log (`dash serve ..., dryrun` prints `dash: serving ... http://localhost:<port>/...`? -- read `_dash_serve`'s display lines and pin the one it prints; a dryrun prints the command it would run); (4) a served build from an installed tree (`net install` into a tempdir adopath as scripts/run_release_gate.sh does, then `dash build, server`); (5) per-type `by()` parity: for each drawn type in `_pt_univar + scatter line bar` build `by(foreign)` saved and served and compare panel counts and glyph counts through a `python:` block; (6) the `inspect.getsource` fallback: delete the `.py` source's cached `__file__` (run the renderer from a `.pyc`-only copy in a tempdir) and assert `dash build` still writes the served app (the copy lists read source text; the fallback the row names must exist -- if it does not, this case documents the refusal text instead, and the row's BUGS entry stays partly open).
- **D-60f. H6's profile and oracle.** `TestMovesAgree` gains `test_same_axes_after_the_move` (`_axes(fig)`: ranges start/end, tickers, formatters, axis labels, visible), `test_same_chrome_after_the_move` (`_chrome(fig)`: title, legend items' labels and visibility, background, border), both over the existing `_diff`; a new `_MOVES` entry `("slider on yaxis(2) to 4500", "price, type(slider)", ("Slider", 4500.0), "price >= 4500")` used by `_move_case("line yaxis(2), slider to 4500", ..., [plot_for("scatter"), plot_for("line", {"yaxis": "2"})])` so the second axis's range after a move is compared (GAPS3 D9 was fixed by S35, batch 12); and a second oracle, `_saved_js_after_move(spec, move)`: render the saved page, run its `_FILTER_JS` under node through `test/js_runner.py` with the widget set to the move's value, and return the figures' profiles read from the mutated sources (glyph coordinates only -- the JS writes sources, not axes), compared with `_served_after_move` in `test_saved_js_agrees_with_served_after_the_move`. Brush entries: `_BRUSH_MOVES` with S51's `brush_state` (one box selection on g1, intersected with a dropdown move) -- one entry, saved-JS vs served.
- **D-60g. Lint and secrets.** `make lint` = `$(PYTHON) -m ruff check dash_render.py dash_setup_lib.py test scripts --config ruff.toml`; `ruff.toml` selects `E,F,W,B` and lists the 51 findings' rules as a committed `# baseline` through `--add-noqa`-free `per-file-ignores`? No: fix the 51 (most are unused imports/variables, `E741`, bare `except`) where mechanical, and `# noqa: <code>  # <why>` the rest in place (the "baseline" is the noqa comments, greppable). ruff is NOT a runtime dependency: `make lint` prints how to install it when `python3 -m ruff` is missing and exits 2. Secrets: `test/test_no_secrets.py` scans every tracked text file for `AKIA[0-9A-Z]{16}`, `-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----`, `ghp_[A-Za-z0-9]{36}`, `xox[baprs]-`, `DASH_SERVE_TOKEN=[A-Za-z0-9_-]{20,}` outside test/ fixtures that define TEST_TOKEN, and the user's email outside .git; the allow-list is the test's own patterns file.
- **D-60h. CI.** `.github/workflows/test.yml`: `on: [push, pull_request]`; one job `ubuntu-latest`, Python 3.11 (the floor, WP-30 P1.33; REVIEW-4 R4-28: the job runs no Stata, and macOS runners cost ten times Linux minutes -- a comment in the workflow names macOS as the certified platform), `pip install -r requirements-dev.txt` (the file the repo has; else `pip install bokeh==3.8.* numpy pandas pytest pytest-xdist`), then `make test-dev PYTHON=python` and `make lint`. No Stata step (`make test` and `make cert` need the console binary; the workflow says so in a comment). Hooks: `.claude/hooks/*.sh` stay untracked; `CLAUDE.md`'s rules 10-11 already name them; S60 adds `docs/HOOKS.md`? NO (no new docs unless asked) -- a four-line note in README's Development section (S59 owns README: hand the line to S59 via the hand-back; S60 writes nothing to README). `.gitignore` gains `*.log` (moved from .git/info/exclude:130).

## Risk: [yellow] -- regenerating fixtures may change pinned values; the saved-JS oracle runs the whole filter script under node

**Risk factors.** (1) A regenerated fixture differs from the committed one (Stata version drift since it was written) and flips a passing test; (2) the saved-JS oracle needs every estimator helper S10-S29 landed (batches 3-10) -- S60 is batch 20, so they have; (3) ruff fixes touching dash_render.py could alter behaviour; (4) a CI run without Stata cannot run `make test` (Stata's Python) -- only `make test-dev`.

**Mitigation.** (1) D-60a: a difference is reported, the reading test decides, never a hand edit (R7); (2) `js_runner.run_filter_js_block` already slices helpers; (3) only `F401/F841/E741/E722` fixes and `noqa` comments; `make test-dev` after; (4) stated in the workflow.

## Dependencies

- **Depends on: 10** (JS prelude for the node oracle), **51** (brush state for the brush entry). **Blocks: none.**
- **Parallel batch: 20** with S59 (README/dash.pkg/version pins). S60 edits Makefile, .gitignore, .github/, ruff.toml, scripts/extract_*.do (new), test/test_server_serves.py, test/test_mode_parity.py, test/test_wp31_truth.cscript, new test files; S59 edits README.md, dash.pkg, dash_setup version pins. Disjoint.

## Evidence

### The leak

```python
123    def __enter__(self):
124        self.proc = subprocess.Popen(
...
131        deadline = time.time() + 60
132        while time.time() < deadline:
133            if self.proc.poll() is not None:
134                out = self.proc.stdout.read() if self.proc.stdout else ""
135                raise AssertionError(
136                    f"bokeh serve exited early:\n{out[:3000]}")
137            try:
138                self.get(self.ready_path)
139                return self
140            except Exception:
141                time.sleep(0.4)
142        raise AssertionError("bokeh serve never answered")
```

(:133-136 raises with a dead process, no leak; :142 raises with a LIVE process -- the leak; `__exit__` :144-151 would terminate it.)

### The move profile

```python
911 def _figure_profile(fig):
912     return {"glyphs": _glyph_profile(fig), "annotations": _annotations(fig),
913             "tools": _tools(fig), "axes": _axes(fig), "chrome": _chrome(fig)}
```

`TestMovesAgree` (:3240-3298): `test_same_glyphs_after_the_move`, `test_same_labels_after_the_move`, `test_same_arrowheads_after_the_move` (also cards), `test_the_move_changed_something`. `_saved_with_qualifier` (:2802); `_served_after_move` (:2756); `_MOVES` (:2819-2826).

### Fixtures and generators

scripts/ holds 63 `extract_*_truth.do` files; the exemplar is scripts/extract_default_base_truth.do (`DASH_REPO` guards :21-43, mata/ado load :45-48, `shell git rev-parse HEAD`, the `_meta` python block :181-183). test/test_fixtures_are_committed.py requires every fixture to be named by a test and every `.do` by another script or test (:213, :232).

### Makefile and hooks

Makefile targets (:38-93): check, test, test-dev, test-release, test-batch, test-all, test-floor, cert, gate, release, hooks. scripts/git-hooks/pre-push runs `make check`. `.github/` does not exist. `python3 -m ruff` is not installed on this machine (verified: "No module named ruff").

### Existing tests that pin today's behaviour

- test/test_fixtures_are_committed.py -- every new `.do` must be named by a test (the `GENERATORS` table added to this same file names them all, R4-29).
- test/test_mode_parity.py `ALLOWED` -- untouched (R8); the new oracle's differences must be real or the entry fails.
- test/test_cscript_hygiene.py counts -- the truth block adds cases, not scripts (R1).

## User stories

- **US-60.1** As a maintainer I want `make truth` to regenerate every fixture so that a new Stata release is re-measured in one command.
- **US-60.2** As a maintainer I want a failing server fixture to leave no process behind.
- **US-60.3** As a maintainer I want the parity guard to compare axes, legends and the second axis after a move, and the saved page's own script against the served app.
- **US-60.4** As a contributor I want `make lint`, a secrets check and CI on push.

## Business requirements

- **BR-60.1** Every committed fixture names its generator and carries complete `_meta`; none holds an absolute path.
- **BR-60.2** No test leaves a `bokeh serve` running after a failure.
- **BR-60.3** The six K2 gaps are certified in Stata.
- **BR-60.4** After a move, both modes agree on axes, ranges, legend and chrome; the saved page's script agrees with the served app on glyphs; a `yaxis(2)` layer's range is compared.
- **BR-60.5** `make lint` is clean; the tree holds no secret; CI runs `make test-dev` and `make lint` on a Linux runner.

## Technical requirements

- **TR-60.1 (K4)** D-60d in `_Served.__enter__` and `_Launched.__enter__`; `test/test_server_fixture.py::TestNoLeak::test_a_never_ready_server_is_terminated` (a `_Served` on a port nothing listens on with `ready_path` to a 404 and a 2 s deadline through a `deadline` parameter added to `__init__`; assert `proc.poll() is not None` after the `AssertionError`).
- **TR-60.2 (K3)** D-60a's twelve scripts; D-60b's guard; D-60c's targets; regenerate the six absolute-path fixtures; `git add -f` each regenerated fixture.
- **TR-60.3 (K2)** D-60e's six cases in the truth block `* ==== S60 K2: end-to-end gaps ====`; program_coverage_map entries for the programs they reach (`_dash_serve_spec`, `_dash_serve`).
- **TR-60.4 (H6)** D-60f: `_axes`/`_chrome` comparisons, the `_MOVES` entry and corpus case, `_saved_js_after_move` (uses `test/js_runner.py`'s `run_filter_js` over the page's `_FILTER_JS` with the widget value set; collects `all_graph_sources` after the run and rebuilds `_glyph_profile`-shaped dicts from the sources' columns the glyphs reference), `test_saved_js_agrees_with_served_after_the_move`, the brush entry.
- **TR-60.5 (I6)** D-60g, D-60h; Makefile `lint:` and `truth:`/`truth-check:`; `.PHONY` updated; `make help` lines; `.gitignore` `*.log`; `.github/workflows/test.yml`.
- **TR-60.6 Maps.** function_test_map: `app:` entries unchanged; new test-only helpers in test/ need none. program_coverage_map: K2's cases.

## Boundaries

- No change to dash_render.py except ruff `F401/F841/E741/E722` fixes and `noqa` comments (no behaviour change; `make test-dev` proves it).
- No README edit (S59); hand the hooks note to S59.
- No new cscript (R1); no change to `ALLOWED` (R8); no fixture edited by hand (R7).
- No Stata in CI.

## Stata truth

Twelve generators (D-60a) regenerate existing fixtures; `make truth` runs them. The truth block S60 holds U60-1..U60-6 (K2) measured live.

## TDD test stubs

K4 (red at 6370ca4): `test/test_server_fixture.py::TestNoLeak::test_a_never_ready_server_is_terminated`, `::test_an_early_exit_is_still_reported`.
K3 (red after K4's commit): `test/test_fixtures_are_committed.py::TestEveryFixtureHasMeta::test_every_fixture_has_meta[rel]`, `::test_no_absolute_path[rel]`, `::test_every_fixture_names_a_generator[rel]` (table `GENERATORS = {fixture: script}` plus the hand-written exemptions), `::test_make_truth_lists_every_generator` (no new file, R4-29) (parses the Makefile target's loop against `scripts/extract_*.do`).
K2 (cscript): U60-1..U60-6.
H6 (red after K2's commit): `test_mode_parity.py::TestMovesAgree::test_same_axes_after_the_move`, `::test_same_chrome_after_the_move`, `::test_saved_js_agrees_with_served_after_the_move`, the `yaxis(2)` entry, the brush entry; `test/test_parity_oracles.py::TestTheJsOracle::test_it_reads_the_mutated_sources` (unit test of the helper on one spec).
I6 (red after H6's commit): `test/test_no_secrets.py::test_no_pattern_matches`, `::test_the_patterns_catch_a_planted_sample` (a string built at run time, never committed); `test/test_repo_hygiene.py::test_gitignore_excludes_logs`, `::test_the_workflow_runs_test_dev_and_lint`, `::test_make_lint_target_exists`, `::test_ruff_findings_are_zero_or_skip` (runs ruff when installed; skips with a reason otherwise, red under DASH_STRICT=1 only when ruff is installed and dirty).

Flips: none expected; a regenerated fixture that changes a value flips the reading test with the reason in that commit (K3).

Parity entries: the `yaxis(2)` move case and the brush case (H6); CORPUS unchanged.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| leak | pytest | none | served |
| generators, meta, paths | pytest + `make truth` (by hand, once) | all | -- |
| K2 gaps | cscript U60-1..6 | none | both |
| profile extension, JS oracle | pytest batch tier | none | both |
| lint, secrets, CI, gitignore | pytest + make | none | -- |

**AC-60.1** every stub green; **AC-60.2** `make truth` regenerates every fixture with the five `_meta` keys and no absolute path; **AC-60.3** `make lint` clean (or skip with the install hint); **AC-60.4** five commits with subjects ending `(WP-31 K4)`, `(WP-31 K3)`, `(WP-31 K2)`, `(WP-31 H6)`, `(WP-31 I6)`.

## Tasks

**Commit boundary.** 60-01 = K4 commit `Terminate the test server when the fixture fails to start (WP-31 K4)`; 60-02..60-06 = K3 commit `Give every truth fixture a committed generator, complete metadata and relative paths; add make truth (WP-31 K3)` (REVIEW-4 R4-27: one task per three generators, the guard and Makefile first; made by 60-06); 60-07 = K2 commit `Certify the served layer output, dates served, the serve start line, an installed-tree build, by() parity and the source fallback (WP-31 K2)` and H6 commit `Compare axes, chrome and the second axis after a move, and the saved page's script against the served app (WP-31 H6)`; 60-08 = I6 commit `Add make lint, a secrets test, a CI workflow and the log ignore rule (WP-31 I6)`.

<task type="auto" id="60-01">
  <name>Fix the server fixture leak and commit K4</name>
  <files>test/test_server_fixture.py, test/test_server_serves.py, BUGS.md</files>
  <action><![CDATA[Create test/test_server_fixture.py (K4 stubs), run it on the unmodified tree, save <scratch>/60-01-failure.txt. Apply D-60d to _Served.__enter__ (:123-142) and _Launched.__enter__ (:183ff) with a `deadline` keyword (default 60). Run test/test_server_fixture.py and test/test_server_serves.py. Close BUGS.md "Harness: server fixture leak" (the K4 entry; the other K4 clauses -- AST count of the app's dispatch, scheme-key enumeration, CSS-guard served arm, tracking counts, strict xfails -- stay in a new open residual entry "Harness guards" graded S3), rewrite the GAPS3 K4 Tracked line to the Partly form with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha), replace the <!-- WP-31 K4 --> marker under "### Fixed in WP-31". Commit on wp31-s60.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_server_fixture.py test/test_server_serves.py -q passes; pgrep -f "bokeh serve" prints nothing after the run; git log -1 --format=%s ends "(WP-31 K4)"]]></verify>
  <done>A failing server fixture leaves no process; K4's leak clause is closed and committed.</done>
</task>

<task type="auto" id="60-02">
  <name>Write the fixture guard and make truth</name>
  <files>test/test_fixtures_are_committed.py, Makefile</files>
  <action><![CDATA[Add to test/test_fixtures_are_committed.py the class `TestEveryFixtureHasMeta` of D-60b (REVIEW-4 R4-29: no new test_fixture_meta.py; the class reuses the file's `_fixture_files()` list and `_do_files()`), with the module-level `GENERATORS = {fixture: script}` table naming D-60a's twelve scripts and the hand-written exemptions; run `python3 -m pytest test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider -k "TestEveryFixtureHasMeta" > <scratch>/s60/60-02.log 2>&1` on the unmodified tree and write <scratch>/60-02-failure.txt (red: no `_meta` on the old fixtures, absolute paths in the six named files, no generator for the twelve). Add `truth:` and `truth-check:` to the Makefile per D-60c (sequential `scripts/stata_slot.sh` runs over `scripts/extract_*.do` with `DASH_REPO=$(CURDIR)`, then the three `.py` generators; `truth-check` runs `python3 -m pytest test/test_fixtures_are_committed.py -q`), with `make help` lines and `.PHONY` entries. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s60/60-02.log` is at least 12; `grep -c '^truth:' Makefile` prints 1 and `grep -c '^truth-check:' Makefile` prints 1; `test -s <scratch>/60-02-failure.txt`.]]></verify>
  <done>The fixture guard existed in the file that already pins fixtures, failed on the unmodified fixtures, and make truth was defined.</done>
</task>

<task type="auto" id="60-03">
  <name>Write the first three generators</name>
  <files>scripts/extract_ci_plot_index_truth.do, scripts/extract_fp_edge_truth.do, scripts/extract_geometry_truth.do</files>
  <action><![CDATA[Create the three scripts on the exemplar's form (scripts/extract_default_base_truth.do: DASH_REPO guards :21-43, mata/ado load :45-48, `shell git rev-parse HEAD` into a local, the `_meta` python block :181-183 writing the five keys through Macro.getLocal), each reproducing its fixture's keys as D-60a says (read the fixture and the test that reads it first; geometry_truth.json's probe paths are written as basenames so no absolute path remains). Run each through `DASH_REPO=<W> scripts/stata_slot.sh <scratch>/s60 <W>/scripts/<script>` one at a time, `git add -f` the three regenerated fixtures, and for any value change run the reading test and record the change in <scratch>/s60/60-changes.txt for the K3 commit body.]]></action>
  <verify><![CDATA[`python3 -c "import json;[print(sorted(json.load(open('test/fixtures/'+f))['_meta'])) for f in ('ci_plot_index_truth.json','fp_edge_truth.json','geometry_truth.json')]"` prints the five keys three times; `grep -c '/Users/\|/private/tmp\|/var/folders' test/fixtures/geometry_truth.json` prints 0.]]></verify>
  <done>Three fixtures were regenerated by committed scripts with complete metadata and no absolute path.</done>
</task>

<task type="auto" id="60-04">
  <name>Write the next three generators</name>
  <files>scripts/extract_kpi_pctile_truth.do, scripts/extract_kpi_truth.do, scripts/extract_linewidth_chain_truth.do</files>
  <action><![CDATA[Create the three scripts as 60-03 did (kpi_truth.json's `kpi_stats.all/foreign1` from `summarize mpg, detail` on `sysuse auto` whole and `if foreign`, plus its `moment_definitions`; kpi_pctile_truth.json's scopes from `_pctile`; linewidth_chain_truth.json's values from the `.Graph` class as its reading test expects). Run each through the slot one at a time, `git add -f` the regenerated fixtures, record any value change in <scratch>/s60/60-changes.txt.]]></action>
  <verify><![CDATA[`python3 -c "import json;[print(sorted(json.load(open('test/fixtures/'+f))['_meta'])) for f in ('kpi_pctile_truth.json','kpi_truth.json','linewidth_chain_truth.json')]"` prints the five keys three times; `python3 -m pytest test/test_kpi_values.py -q -p no:cacheprovider` passes (or the change is in 60-changes.txt with the reading test's verdict).]]></verify>
  <done>Three more fixtures had committed generators and complete metadata.</done>
</task>

<task type="auto" id="60-05">
  <name>Write three more generators</name>
  <files>scripts/extract_marker_linewidth_truth.do, scripts/extract_mband_band_edges.do, scripts/extract_natscale_axes_truth.do</files>
  <action><![CDATA[Create the three scripts as 60-03 did (mband_band_edges.json from `twoway mband, bands(#)`'s `_mbandgen` output; natscale_axes_truth.json from the `.Graph` axis ranges of `twoway ..., xscale(natscale)`; marker_linewidth_truth.json from the `.Graph` marker line widths its reading test names). Run each through the slot one at a time, `git add -f` the regenerated fixtures, record any value change in <scratch>/s60/60-changes.txt.]]></action>
  <verify><![CDATA[`python3 -c "import json;[print(sorted(json.load(open('test/fixtures/'+f))['_meta'])) for f in ('marker_linewidth_truth.json','mband_band_edges.json','natscale_axes_truth.json')]"` prints the five keys three times.]]></verify>
  <done>Nine of the twelve fixtures had committed generators and complete metadata.</done>
</task>

<task type="auto" id="60-06">
  <name>Write the last three generators and commit K3</name>
  <files>scripts/extract_natscale_truth.do, scripts/extract_qualified_stat_truth.do, scripts/extract_rejected_options.do</files>
  <action><![CDATA[Create the last three scripts as 60-03 did (rejected_options.json as `capture twoway ...` rc/text pairs with the probe's path field written as a basename; qualified_stat_truth.json and natscale_truth.json per their reading tests), run each through the slot, `git add -f` the regenerated fixtures. Add the header line `# hand-written corpus; no generator (S60 D-60a)` to test/fixtures/help_examples.txt and test/fixtures/conformance_corpus.txt (two further files, named here). Run `make truth-check` (test/test_fixtures_are_committed.py whole, green) and `python3 -m pytest $(grep -l "qualified_stat_truth\|rejected_options\|natscale_truth" test/test_*.py) -q -p no:cacheprovider`; any value change is in <scratch>/s60/60-changes.txt with the reading test's verdict. Close BUGS.md "Truth fixtures without generators", rewrite the GAPS3 K3 Tracked line to the Closed form with `commit pending` (DECISIONS A11; the Partly form, also ending `commit pending`, if the scheme_visual histogram render clause is left: say so), replace the <!-- WP-31 K3 --> marker. Commit on wp31-s60 with one `Fixture:` line per regenerated fixture and the 60-changes.txt findings in the body.]]></action>
  <verify><![CDATA[`ls scripts/extract_*.do | wc -l` prints 75 or more; `python3 -m pytest test/test_fixtures_are_committed.py -q` passes; `grep -rl "/Users/\|/private/tmp\|/var/folders" test/fixtures/*.json | wc -l` prints 0; `git log -1 --format=%s` ends "(WP-31 K3)".]]></verify>
  <done>Every fixture had a generator, complete metadata and relative paths, make truth regenerated them, and K3 was committed.</done>
</task>


<task type="auto" id="60-07">
  <name>Certify the K2 gaps and extend the parity profile; commit K2 then H6</name>
  <files>test/test_wp31_truth.cscript, test/test_mode_parity.py, test/test_parity_oracles.py</files>
  <action><![CDATA[K2 cycle: append the S60 K2 block (U60-1..U60-6 per D-60e) above the marker line; run it red through scripts/stata_slot.sh (the cases fail or are refused at base: record which), fix nothing in dash (these are tests of existing behaviour; a case that FAILS because dash is wrong is reported and left red with `_w31_expect` noting the GAPS3 row, never skipped), add program_coverage_map entries, close BUGS.md "Stata end-to-end gaps", rewrite the GAPS3 K2 Tracked line to the Closed (or Partly) form with `commit pending` (A11), replace the marker, commit (WP-31 K2). H6 cycle: create test/test_parity_oracles.py and add D-60f's tests, _MOVES entry, corpus cases and _saved_js_after_move to test_mode_parity.py; run DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "after_the_move or yaxis or brush" and test/test_parity_oracles.py; a real divergence found is reported and the entry left red with its GAPS3 row named (never added to ALLOWED). Close BUGS.md "Parity guard limits", rewrite the GAPS3 H6 Tracked line to the Closed form with `commit pending` (A11), replace the marker, commit (WP-31 H6).]]></action>
  <verify><![CDATA[The cscript log shows U60-1..U60-6 with PASS or the documented FAIL lines; DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "after_the_move" -q passes or names the divergence; git log --format=%s -2 prints the H6 then the K2 subject]]></verify>
  <done>The six end-to-end gaps are certified and the move profile compares axes, chrome, the second axis and the saved page's own script.</done>
</task>

<task type="auto" id="60-08">
  <name>Add lint, secrets, CI and the log rule; commit I6</name>
  <files>Makefile, .github/workflows/test.yml, test/test_no_secrets.py</files>
  <action><![CDATA[Create test/test_no_secrets.py and test/test_repo_hygiene.py (I6 stubs), run them red, save <scratch>/60-04-failure.txt. Add `lint:` per D-60g (ruff.toml with select E,F,W,B; the install hint when ruff is absent), fix dash_render.py's F401/F841/E741/E722 findings or `# noqa` them with a reason (run `python3 -m pip install --user ruff` ONLY if the maintainer has allowed installs; otherwise write the config and the noqa comments from a `python3 -m pyflakes` pass and report that ruff was not run), create .github/workflows/test.yml per D-60h, move `*.log` from .git/info/exclude into .gitignore, update `make help` and .PHONY. Run test/test_no_secrets.py, test/test_repo_hygiene.py, test/test_makefile*.py if present, and `make test-dev PYTEST_ARGS="test/test_csp.py test/test_render*.py -q"` to prove the lint edits changed no behaviour. Close BUGS.md "No CI, lint or secrets scan", rewrite the GAPS3 I6 Tracked line to the Closed form with `commit pending` (A11), replace the <!-- WP-31 I6 --> marker (Requirements list). Commit on wp31-s60; in the hand-back, give S59 the README line about .claude/hooks.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_no_secrets.py test/test_repo_hygiene.py -q passes; grep -c '^\*\.log$' .gitignore prints 1; test -f .github/workflows/test.yml; git log -1 --format=%s ends "(WP-31 I6)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0]]></verify>
  <done>Lint, secrets and CI are in place and committed.</done>
</task>

## Section completion criteria

- Five commits in order K4, K3, K2, H6, I6; `make truth` regenerates every fixture; the meta/path guard is green; no leaked server; U60-1..6 certified or documented red with their rows; the parity move profile compares axes/chrome/yaxis(2) and runs the saved-JS oracle; `make lint`, the secrets test and the workflow exist.

## Notes

- **python_exec hazard.** `make truth` runs 75+ Stata scripts: sequentially, one slot, with `STATATMP=<dir>/` and `global dash_nobrowser 1` in each driver (project memory). Never in parallel.
- **R7.** Regenerated fixtures are never edited by hand; `git add -f` each (`.git/info/exclude:58 *.json`).
- **R1/R8/R10.** No new cscript; `ALLOWED` untouched; test_cscript_hygiene.py counts unchanged (cases, not scripts).
- **Security.** The secrets test's planted sample is built at run time from fragments so the repository never holds a matching string; the CI workflow needs no secret (no Stata, no token).
- **Commit body forms:** `Regression: test/test_server_fixture.py::TestNoLeak::test_a_never_ready_server_is_terminated -- failed at 6370ca4 with AssertionError: proc still running`; `Fixture: test/fixtures/<name>.json (scripts/extract_<name>.do)` one per regenerated fixture; `BUGS.md: "<title>" (closed)`; `GAPS3: <row> Tracked`.
- **Decisions for ratification:** the twelve generator names and the hand-written-corpus exemption (D-60a); the `_meta` key set enforced on old fixtures by regeneration (D-60b); K2 case (6)'s fallback-or-document rule (D-60e); the noqa baseline and a Linux CI without Stata (D-60g, D-60h; R4-28); K4's other clauses as a residual (60-01).
- **Tracked lines (A11):** every closing task (60-01, 60-06, 60-07 twice, 60-08) writes `commit pending`; no amend anywhere. **A14:** one truth block (K2's, appended by 60-07); 60-01 appends none. **Files (A13):** `<files>` lists primary files; the tracking documents, the regenerated fixtures (`git add -f`) and flipped tests are implied.
