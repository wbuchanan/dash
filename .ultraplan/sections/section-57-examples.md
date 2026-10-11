# Section 57: Examples

> Part of: WP-31 · GAPS3 rows: J3 · Risk: green · Batch: 19 · Depends on: 21, 26 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U57

## Overview

**What is wrong today.** GAPS3 J3: "10 of 40 plot types unused (bar, scatteri, pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline, fpfit); no example uses `dash serve`, weights or `csv`; feature_tour.do's header names serve/pci it does not contain and says 'thirty-eight plot types'; test_examples_run.cscript:13-16 claims the examples exercise every plot type; no coverage test." Measured at `6370ca4`: `examples/` holds 12 do-files; `grep -ohE '\((scatter|line|bar|...)' examples/*.do` finds no `bar`, `scatteri`, `pci`, `pcarrowi`, `pccapsym`, `pcbarrow`, `pcscatter`, `tsline`, `tsrline` or `fpfit`; `grep -c 'dash serve\|\[aw\|\[fw\|, csv\|csv ' examples/*.do` is 0 for every file; `examples/feature_tour.do:9-14` reads "Ten of dash's thirty-eight plot types appeared in no example at all -- which is how `pci' and `pcscatter' came to draw an empty plot region" and names `dash serve` at :12; `test/test_examples_run.cscript:13-16` reads "between them the do-files (eleven then, twelve on 24sep2026) exercise every plot type, KPIs, filters, ..."; the script asserts `nfiles == 12` (:62) and runs each file (:66-81). GAPS2 J10 (GAPS2.md:1772) planned `examples/plot_types_tour.do` and it was never written.

**After this section** `examples/plot_types_tour.do` draws every plot type dash draws at the batch-19 base (the 40 of `6370ca4` plus rpcap, rpspike, contour and contourline from S21 and S26), a weighted layer and `dash build, csv`; `examples/serve_dashboard.do` registers a dashboard and runs `dash build, saving(app.py) server replace` (writing the app without launching it, so the example runs under certification) and shows the `dash serve` line in a comment; feature_tour.do's header states what it holds; test_examples_run.cscript's header and its file count say what is true; and `test/test_examples_cover.py` pins that every drawn plot type, `dash serve` or `dash build, server`, a weight and `csv` appear in some example.

**Why one section.** One row, one commit; batch 19 so that S21's rpcap/rpspike and S26's contour exist to be drawn.

**Test order and commit rule.** One cycle, one commit `(WP-31 J3)`: 57-01 writes `test_examples_cover.py` red and saves `<scratch>/57-01-failure.txt`; 57-02 writes the examples and headers; 57-03 certifies, closes and commits.

### Section decisions

- **D-57.a Drawn types come from the code, not a list.** `test_examples_cover.py` reads the plot-type names from `dash.ado`'s `"Supported: ..."` text (dash.ado:4903-4906 at `6370ca4`; the lines following `"Supported: scatter line connected area bar spike " _n ///`) so S21's and S26's additions are required automatically; `_dash_undrawn_plottype`'s names (dash_parse.mata:1802) are excluded.
- **D-57.b `dash serve` is not run by an example.** Certification runs every example (`test_examples_run.cscript`); a serving example would block. `serve_dashboard.do` runs `dash build, saving(serve_dashboard_app.py) server replace nobrowser` and comments the `dash serve, port(5006)` line; the coverage test accepts either `dash serve` or `dash build, ... server` as the "serve" use.
- **D-57.c The file count pin moves 12 → 14** (`test_examples_run.cscript:62`) with a comment `// 12 -> 14: plot_types_tour.do, serve_dashboard.do (WP-31 J3)`.
- **D-57.d The tsline/tsrline example** uses `sysuse sp500` after `tsset date`, as GAPS2 J10 planned; the weighted layer is `scatter mpg weight [aw=price]` on auto (C9 lands in batch 7, so the markers are sized).

## Risk: [green] -- two new do-files and one new test; nothing shipped changes

**Risk factors.** 1. A plot type whose drawing fails under `$dash_nobrowser` (contour above the cap, a type needing `tsset`) breaks `test_examples_run.cscript`. 2. The Supported text's shape changes by batch 19.

**Mitigation.** 1. 57-03 runs test_examples_run.cscript through the driver; contour uses a 50-point grid. 2. `test_examples_cover.py::test_the_supported_list_was_found` asserts at least 40 names.

## Dependencies

- **Depends on:** 21 (rpcap, rpspike, sunflower/matamatrix refusals), 26 (contour/contourline drawn). Both land by batch 9.
- **Blocks:** nothing; S61's G3 "examples cover every drawn type" reads `test_examples_cover.py`.
- **Parallel batch 19** with S56 (dash.sthlp) and S58 (tracking documents); S57 edits neither.

## Evidence

- `ls examples/`: basic_scatter.do, bootstrap_equal_cols.do, bootstrap_kpi_hero.do, bootstrap_responsive.do, bootstrap_stacked.do, comprehensive_demo.do, feature_tour.do, full_dashboard.do, geometry_responsive.do, kelly22ex_categorical.do, multi_graph_dashboard.do, sp500_dates.do (12).
- Types used (grep of `(<type>` and `dash <type>` across examples/): scatter 88, histogram 12, lfit 6, line 6, kdensity 3, lfitci 3, qfitci 2, lpolyci 2, fpfitci 2, qfit, pcarrow, mspline, mband, lpoly, lowess, spike, rspike, rscatter, rline, rconnected, rcapsym, rcap, rbar, rarea, pcspike, function, dropline, dot, connected, area 1 each. Absent: bar, scatteri, pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline, fpfit.
- `examples/feature_tour.do:1-20`: header; :9-12 "Ten of dash's thirty-eight plot types appeared in no example at all -- which is how `pci' and `pcscatter' came to draw an empty plot region without anyone noticing."; :20 `*! Version: 1.0.0  20sep2026`.
- `test/test_examples_run.cscript:13-16`: "examples/ is exactly that corpus -- between them the do-files (eleven then, twelve on 24sep2026) exercise every plot type, KPIs, filters, linking, tabs, faceting, both layouts, dates and the Bootstrap grid -- and nothing ran them."; :57-62 the count comment and `assert \`nfiles' == 12`; :64-81 the loop (`capture noisily do "\`exdir'/\`f'"`).
- `dash.ado:4903`: `"Supported: scatter line connected area bar spike " _n ///` (continues over several lines; the refusal message for an unknown plot type).
- `dash_parse.mata:1802`: `string scalar _dash_undrawn_plottype(string scalar name)` (the by-name refusals; four at `6370ca4`, six after S21).
- Existing tests that pin today's state: `test_examples_run.cscript:62` (`nfiles == 12`), moved (R10). `test_help_examples.cscript` reads the help's examples, not `examples/` (unaffected).

## User stories

- **US-57.1** As a Stata user learning dash, I want an example that draws every plot type, so I can copy the one I need.
- **US-57.2** As a Stata user, I want an example of `dash serve`, weights and `csv`, so the dashboard features have a worked case.

## Business requirements

- **BR-57.1** Every plot type dash draws appears in at least one file under `examples/`, pinned by a test that reads the drawn types from the code.
- **BR-57.2** `dash serve` (or `dash build, server`), a weight and `csv` each appear in at least one example.
- **BR-57.3** Every example runs clean under certification; the headers of feature_tour.do and test_examples_run.cscript are true.

## Technical requirements

- **TR-57.1 `examples/plot_types_tour.do`**: header (`*! plot_types_tour.do`, purpose, `Usage: do examples/plot_types_tour.do (run from the dash/ directory)`, `Produces: plot_types_tour.html`, `*! Version: 0.1.0  <ddmonyyyy>`); `sysuse auto, clear`, `dash clear`, `global dash_nobrowser 1` is NOT set (the cscript sets it); one `dash <type> ..., name(ptNN)` per drawn type on auto (bar: `dash bar mpg foreign`; scatteri: `dash scatteri 20 2000 30 4000`; pci: `dash pci 20 2000 30 4000`; pcarrowi: `dash pcarrowi 20 2000 30 4000`; pccapsym/pcbarrow/pcscatter: `dash <type> mpg weight price turn`; fpfit: `dash fpfit mpg weight`; rpcap/rpspike: `dash <type> price mpg turn weight` (y1 y2 y3 x per S21); contour/contourline: `dash <type> price mpg weight in 1/50`; the other 30 as feature_tour.do writes them), then `preserve`, `sysuse sp500, clear`, `tsset date`, `dash tsline close, name(pt_tsline)`, `dash tsrline high low, name(pt_tsrline)`, `restore`; a weighted layer `dash scatter mpg weight [aw=price], name(pt_weighted)`; `dash build, saving(plot_types_tour.html) csv replace`.
- **TR-57.2 `examples/serve_dashboard.do`**: header as above; `sysuse auto, clear`; two graphs and a KPI; `dash build, saving(serve_dashboard_app.py) server replace`; a comment block `// To serve it: dash serve, port(5006)` and `// or: python serve_dashboard_app.py` with the help's launch sentence.
- **TR-57.3 feature_tour.do header**: :9-12 become "Ten of dash's forty plot types appeared in no example at all before examples/plot_types_tour.do, which now draws every type; this file keeps the options tour." and :12's `dash serve` mention becomes "`dash serve' is shown in examples/serve_dashboard.do". `*! Version` line → `0.1.0  <ddmonyyyy>`.
- **TR-57.4 test_examples_run.cscript**: :13-16 → "examples/ is exactly that corpus -- between them the do-files (twelve on 24sep2026, fourteen since WP-31 J3) exercise every plot type (test/test_examples_cover.py pins it), KPIs, filters, linking, tabs, faceting, both layouts, dates, weights, csv and the Bootstrap grid -- and nothing ran them."; :62 `assert \`nfiles' == 14` with D-57.c's comment; EX-00's text unchanged.
- **TR-57.5 `test/test_examples_cover.py`** (new): `_drawn_types()` reads dash.ado's `Supported:` text (regex `"Supported: (.*?)"` over the joined continuation lines, split on whitespace) minus `_undrawn()` (names in `_dash_undrawn_plottype`'s `inlist(name, ...)` or `if (name == "...")` lines, read from dash_parse.mata); `_examples_text()` joins `examples/*.do`; `TestEveryDrawnTypeHasAnExample::test_each_type[<type>]` (parametrised) asserts `re.search(r"\bdash (?:twoway )?\(?%s\b|\(%s\b" % (t, t), text)`; `TestTheFeaturesHaveExamples::test_serve`, `::test_weight` (`\[(?:aw|fw|pw|iw)=`), `::test_csv` (`\bcsv\b` in a `dash build` line); `TestTheParsersFoundSomething::test_the_supported_list_was_found` (at least 40 names), `::test_the_undrawn_list_was_found` (at least 4). Add the new functions to `test/function_test_map.py`? No: test helpers are not mapped (only dash_render functions are).
- **TR-57.6 Security (rule 1).** The examples write only into the working directory with `replace`; no `shell`; no network; the server example does not launch.

## Boundaries

- Not edited: dash.sthlp (S56's), dash.ado, dash_parse.mata, dash_render.py, the other ten examples' bodies (only feature_tour.do's header), `test_help_examples.cscript`, `test_examples_run.cscript`'s loop.
- No `dash serve` is run anywhere under certification.

## Stata truth

None (nothing is compared with twoway). The certification of the examples is `test/test_examples_run.cscript`, run through the driver: `printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/test_examples_run.cscript"\n' "<W>" "<W>" > <scratch>/s57/run_test_examples_run.do; scripts/stata_slot.sh <scratch>/s57 <scratch>/s57/run_test_examples_run.do`. No block in test_wp31_truth.cscript.

## TDD test stubs

Regression (57-01; red at the batch-19 base):
- Test: `test/test_examples_cover.py::TestEveryDrawnTypeHasAnExample::test_each_type[bar]` (and `[scatteri]`, `[pci]`, `[pcarrowi]`, `[pccapsym]`, `[pcbarrow]`, `[pcscatter]`, `[tsline]`, `[tsrline]`, `[fpfit]`, `[rpcap]`, `[rpspike]`, `[contour]`, `[contourline]`) -- `AssertionError: no example draws bar`.
- Test: `...::TestTheFeaturesHaveExamples::test_serve`, `::test_weight`, `::test_csv` -- AssertionError.
- Test: `...::TestTheHeadersAreTrue::test_feature_tour_header` (asserts `thirty-eight` absent and `plot_types_tour.do` present) and `::test_examples_run_header` (asserts `fourteen` present) -- AssertionError.
Guards (green at base): `test_the_supported_list_was_found`, `test_the_undrawn_list_was_found`, `test_each_type[scatter]` and the other 29 types already used.
cscript: `test_examples_run.cscript` EX-00 (count 14) and EX-01; pin flipped: `:62` 12 → 14 (R10). Parity corpus: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Every drawn type in an example | pytest `TestEveryDrawnTypeHasAnExample` (parametrised over the code's list) | examples/*.do | n/a |
| serve, weight, csv in an example | pytest `TestTheFeaturesHaveExamples` (3) | examples/*.do | n/a |
| Headers true | pytest `TestTheHeadersAreTrue` (2) | -- | n/a |
| Every example runs clean, 14 files | cscript test_examples_run.cscript EX-00, EX-01 | auto, sp500 | saved page (and one server file) |

AC-57.1 `ls examples/*.do | wc -l` → 14. AC-57.2 `python3 -m pytest test/test_examples_cover.py -q -p no:cacheprovider` 0 failed. AC-57.3 driver log holds `EX-00 PASS: 14 example do-files found`, `EX-01 PASS`, `ALL CHECKS PASSED`. AC-57.4 `grep -c 'thirty-eight' examples/feature_tour.do` → 0.

## Tasks

**Commit boundary.** 57-01..57-03 form the one J3 commit, subject `Add a plot-types tour and a serve example, with a coverage test (WP-31 J3)`, made by 57-03 on `wp31-s57` in `<W>` = `.../dash-wt/wp31-s57`. Body: `<scratch>/57-01-failure.txt`; the defect (ten types, serve, weights, csv absent; two stale headers); the change; `Regression:` lines for the red nodes; `Flipped: test/test_examples_run.cscript:62 -- 12 was right before the two examples existed`; `BUGS.md: "<J3 title>" (closed)`; `GAPS3: J3 Tracked`.

<task type="auto" id="57-01">
  <name>Write the failing coverage test</name>
  <files>test/test_examples_cover.py</files>
  <action><![CDATA[Create test/test_examples_cover.py per TR-57.5 (module docstring: GAPS3 J3's text and the grep that measured the absences). Run `python3 -m pytest test/test_examples_cover.py -q -n0 -p no:cacheprovider -rf > <scratch>/s57/57-01.log 2>&1` and write <scratch>/57-01-failure.txt (base sha, each FAILED node, the guards that passed). Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s57/57-01.log` is at least 17 (14 types, serve, weight, csv) plus the two header tests; `grep -c 'test_each_type\[scatter\]' <scratch>/s57/57-01.log` prints 0 (it passed); `test -s <scratch>/57-01-failure.txt`.]]></verify>
  <done>The coverage test existed and failed on the unmodified examples for every absent type and feature.</done>
</task>

<task type="auto" id="57-02">
  <name>Write the two examples and fix the headers</name>
  <files>examples/plot_types_tour.do, examples/serve_dashboard.do, examples/feature_tour.do</files>
  <action><![CDATA[Create examples/plot_types_tour.do (TR-57.1) and examples/serve_dashboard.do (TR-57.2); edit examples/feature_tour.do's header (TR-57.3) and nothing below its header. Run `python3 -m pytest test/test_examples_cover.py -q -n0 -p no:cacheprovider` until only the two header tests of test_examples_run.cscript's header remain red (TestTheHeadersAreTrue::test_examples_run_header). Then run each new example alone through the slot: `printf 'global dash_nobrowser 1\ncd "%s"\ndo "%s/examples/plot_types_tour.do"\n' "<W>" "<W>" > <scratch>/s57/run_tour.do; scripts/stata_slot.sh <scratch>/s57 <scratch>/s57/run_tour.do` (likewise serve_dashboard.do); a non-zero rc stops the task (fix the example, never the renderer).]]></action>
  <verify><![CDATA[Both example logs end without `r(`; `ls <W>/plot_types_tour.html <W>/serve_dashboard_app.py` lists both (delete them afterwards: `rm <W>/plot_types_tour.html <W>/plot_types_tour.csv <W>/serve_dashboard_app.py`); `python3 -m pytest test/test_examples_cover.py -q -n0 -p no:cacheprovider` fails only test_examples_run_header.]]></verify>
  <done>Every drawn type, a weight, csv and the server build had an example that ran clean, and feature_tour.do's header was true.</done>
</task>

<task type="auto" id="57-03">
  <name>Fix the cscript header, certify, close J3</name>
  <files>test/test_examples_run.cscript, BUGS.md, GAPS3.md</files>
  <action><![CDATA[Edit test/test_examples_run.cscript :13-16 and :62 per TR-57.4 and D-57.c. Run it through the driver (Stata truth) and `python3 -m pytest test/test_examples_cover.py test/test_cscript_hygiene.py -q -p no:cacheprovider`. Close the J3 entry (closed form; `Pinned by test/test_examples_cover.py::TestEveryDrawnTypeHasAnExample::test_each_type, test/test_examples_cover.py::TestTheFeaturesHaveExamples::test_serve, test/test_examples_run.cscript EX-00, EX-01`); delete the `"J3": "` WP31_OPEN line in test/test_tracking_documents.py; replace `<!-- WP-31 J3 -->` under `### Fixed in WP-31` in CHANGELOG.md with `- examples/plot_types_tour.do draws every plot type dash draws, a weighted layer and a csv build, and examples/serve_dashboard.do writes a server app; test/test_examples_cover.py pins that every drawn type has an example. (WP-31, J3)`; rewrite the J3 Tracked line to the Closed form after the commit with its sha and `git commit --amend --no-edit` once. Stage by name (the two documents, CHANGELOG.md, the tracking test, the three examples, the two tests); commit per the Commit boundary.]]></action>
  <verify><![CDATA[Driver log: `EX-00 PASS: 14 example do-files found`, `EX-01 PASS`, `ALL CHECKS PASSED`; pytest 0 failed; `grep -c '^    "J3": "' test/test_tracking_documents.py` prints 0; `grep -c '<!-- WP-31 J3 -->' CHANGELOG.md` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` 0 failed; `git log -1 --format=%s` ends `(WP-31 J3)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Fourteen examples ran clean under certification, the coverage test pinned them, and J3 was closed in one commit.</done>
</task>

## Section completion criteria

- One commit on `wp31-s57` ending `(WP-31 J3)`; `examples/` holds 14 files; `test_examples_cover.py` green; EX-00/EX-01 PASS with 14; J3 closed, Tracked Closed, marker replaced, key deleted.

## Notes

- **R10:** the count pin at test_examples_run.cscript:62 moves with the comment of D-57.c.
- **R1:** no new cscript.
- **Trap:** the examples run with `global dash_nobrowser 1` set by the cscript, not by the example; a browser launch in an example would open a window per run (memory: no browser spam).
- **Trap:** sp500 needs `tsset date` before tsline; `preserve`/`restore` keeps auto for the later layers; `dash clear` between graphs is not needed (names differ).
- **Trap:** contour on the whole of auto (74 rows, unique x × unique y) is fine under the cap; keep `in 1/50` so the example is quick.
- **For S61:** G3 "examples cover every drawn type" is `python3 -m pytest test/test_examples_cover.py -q`.
