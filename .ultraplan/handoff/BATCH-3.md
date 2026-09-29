# WP-28 batch 3 — hand-off checklist for the Mac (sections 18, 15, 11, 12)

> Written 29sep2026 after an attempt to execute batch 3 in a Linux cloud container. Nothing of
> batch 3 was changed there: the container has no Stata (sections 15 and 18 read fixtures only
> Stata can measure; sections 11, 15 and 18 have certification blocks that run only in Stata),
> and its full pytest suite is not green for environment reasons unrelated to WP-28 (28 failures
> at `e197c42`: the help-link and help-parser checks that need Stata's help files, the Mata
> header check, a bokeh-version pin, the lowess speed bound, date-range conversion at Stata's
> extreme dates, the strict-mode baseline reader), so CLAUDE.md rule 4 could not be met there.
> Batch 3 is therefore run on the Mac, where batches 1 and 2 were run. The section files are the
> specifications; this file only orders the steps and names what each Stata run must show.

## Preconditions

- Main checkout `/Users/billy/Desktop/Programs/StataPrograms/d/dash` on `s3-bugs` at
  `9872104` or later; batches 1 and 2 landed (36 WP-28 commits; `scripts/stata_slot.sh`,
  `test/js_runner.py`, `test/test_gaps2_truth.cscript`, `scripts/svg_truth.py`, `test/cert_svg.do`,
  `scripts/extract_text_truth.do` with its `* ---- section 15: legend probes ----` region, and the
  `e3_tm_axis_lab` probe in `test/fixtures/axis_truth.json` are on the tree).
- Step 0b's `<scratch>/cert-baseline.log` exists (run it first if not: `{ date +%s; make cert;
  date +%s; } > <scratch>/cert-baseline.log 2>&1`).
- `scripts/stata_python_exec.sh` prints `/opt/anaconda3/bin/python3`.
- One worktree per section, from `s3-bugs`: `git worktree add <path>/wp28-s<NN> -b wp28-s<NN> s3-bugs`
  for 18, 15, 11 and 12. A section's agent works only in its worktree; `<repo>` in every command
  below is that worktree; `<scratch>` is `/tmp/dash-s<NN>` (create it, with `tmp/` inside).

## Mechanics every section uses

- **A single cscript run** (BRIEF.md "Running one cscript"):
  `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_gaps2_truth.cscript" > <scratch>/run_test_gaps2_truth.do`
  then `GAPS2_ONLY=S<NN> scripts/stata_slot.sh <scratch> <scratch>/run_test_gaps2_truth.do`;
  the log is `<scratch>/run_test_gaps2_truth.log`. `grep -c '^r([0-9]*);' <log>` must print 0.
- **An extract script** (it sets its own directories): `scripts/stata_slot.sh <scratch> <repo>/scripts/<script>.do`.
- **A regenerated fixture** is never hand-edited; every pre-existing probe must be identical
  outside `_meta` (the one-liners below), then `git add -f test/fixtures/<name>.json`.
- **Commits**: one per gap on the worktree branch, subject ending `(GAPS2 <ID>)`, body per
  section-01 TR-01.9 (the recorded failing output first, then `Regression:` / `Flipped:` /
  `Fixture:` / `BUGS.md:` lines), no AI reference; the full pytest suite once in the worktree
  before each commit (`python3 -m pytest test/ -q`); never a red tree.

## Section 18 — B2, axis scale extents (15 tasks, one commit `(GAPS2 B2)`)

1. 18-01 writes `test/test_axis_extents.py` and runs it on the unmodified tree; the failure text
   goes to `<scratch>/18-01-failure.txt` (the CHANGELOG's old values, Q24). 18-02 registers the
   `b2_extent` probes and the `.Graph` reads in `scripts/extract_axis_truth.do` (S14 already
   added the provenance capture; keep it, do not duplicate it).
2. **18-03 (Stata).** Rewire the script's `python:` block onto `scripts/svg_truth.py` (delete the
   private `parse_svg`/`axis_facts`), then run once:
   `scripts/stata_slot.sh /tmp/dash-s18 <repo>/scripts/extract_axis_truth.do`
   and read the `probe <id> rc=` lines of `/tmp/dash-s18/extract_axis_truth.log`. Before adding
   the fixture, the probe-by-probe check must print `[] []`:
   `python3 -c "import json,subprocess;o=json.loads(subprocess.run(['git','show','HEAD:test/fixtures/axis_truth.json'],capture_output=True,text=True,check=True).stdout);n=json.load(open('test/fixtures/axis_truth.json'));bad=[k for k in o['probes'] if n['probes'].get(k)!=o['probes'][k]];lost=[k for k in o['_meta'] if k not in n['_meta']];print(bad,lost)"`
   If an old probe differs, the rewiring is wrong (fix the reader's internals, never S02's public
   names) and the script is re-run. Then the verify one-liner of 18-03 prints the verdict, `True
   True`, an extent past 100, the four provenance keys and the unchanged scheme;
   `grep -c 'def parse_svg\|def axis_facts' scripts/extract_axis_truth.do` prints 0.
3. 18-04 to 18-12: the Python work (range() as values, norescale, the hull helpers, the hull
   after the layers, by() panels, the second axes, the shared primary-renderers limit, the
   flips), each verified by its task's pytest lines.
4. **18-13 (Stata).** Append the `* ==== S18 B2: axis scale extents ====` block (AE-01..AE-06)
   above `* ==== append new blocks above this line ====`, after every lower-numbered section's
   block, and run it alone through the driver with `GAPS2_ONLY=S18`. Expected:
   `grep -c 'AE-0[1-6] PASS' /tmp/dash-s18/run_test_gaps2_truth.log` prints 6, ` FAIL` and
   ` SKIP` counts print 0, `S18 start` and `S18 end` present; `test/run_all_cscripts.do` and
   `test/test_cscript_hygiene.py` untouched.
5. 18-14 closes B2 (BUGS.md appended, dash.sthlp 2333-2335 and 2431-2432, the `<!-- WP-28 B2 -->`
   marker replaced in the `**WP-28 (GAPS2 audit, 25sep2026)**` group of `### Results that change`),
   runs the full suite once, and makes the one commit. 18-15 is the maintainer's checkpoint:
   approve the extents and the `.Graph` verdict the fixture recorded.

## Section 15 — B5, legend order and labels (9 tasks, one commit `(GAPS2 B5)`)

1. 15-01 writes `test/test_legend_order.py`; on the unmodified tree the headline failure shows
   `['mpg', 'Fitted values', 'price']` where `['Group 2', 'Three']` was expected; save it to
   `/tmp/dash-s15/15-01-failure.txt`.
2. **15-02 (Stata).** Append the `* ==== S15 B5: legend order and labels ====` block (LO-01..LO-08)
   and run it alone with `GAPS2_ONLY=S15` against the unmodified tree; expected pre-fix:
   `LO-01 FAIL` on the default texts `mpg` / `Fitted values` / `price` and `LO-04 FAIL` on
   `lastlabel` being named; append those lines to the failure file. Do not commit.
3. 15-03 and 15-04 extend the seven pinned test files as specified.
4. **15-05 (Stata).** Add the 44 `zp` registrations in the `* ---- section 15: legend probes ----`
   region of `scripts/extract_text_truth.do` and the `keys_in_drawn_order` records for group
   `legend` in its python block, then run once:
   `scripts/stata_slot.sh /tmp/dash-s15 <repo>/scripts/extract_text_truth.do`
   Expected: every legend probe measured with rc 0; the section-13 `title` records unchanged:
   `python3 -c "import json,subprocess;o=json.loads(subprocess.run(['git','show','HEAD:test/fixtures/text_truth.json'],capture_output=True,text=True,check=True).stdout)['probes'];n=json.load(open('test/fixtures/text_truth.json'))['probes'];bad=[k for k in o if n.get(k)!=o[k]];print(bad)"`
   prints `[]`; the `_meta` keys `stata_version`, `born_date`, `dash_commit`, `extracted` present;
   `p['l_order_text']['keys_in_drawn_order']` is `['Group 2', 'Three']`, `l_dash_text` gives
   `['mpg', 'Note', 'Fitted values']`, `l_lastlabel_pos` one of `['Fitted values', 'L']` /
   `['L', 'mpg']` (record which: 15-07 follows it), `l_ci_order_last` `['price', 'mpg']` (or the
   variable labels twoway draws). `git add -f test/fixtures/text_truth.json`.
5. 15-06 and 15-07: the parser, the key list and the rewritten `_dash_apply_legend` steps.
6. **15-08 (Stata).** The one-line Mata change in `_dash_rep_subkey` and the coverage-map entry;
   rerun the S15 block (`GAPS2_ONLY=S15`) and `test_twoway_option_parity.cscript` through its own
   driver. Expected: `LO-08 PASS` and every other LO case PASS; TP-14 still PASS.
7. 15-09 closes B5 (entry appended, dash.sthlp 2290-2293 and 2307-2312, the `<!-- WP-28 B5 -->`
   marker replaced), runs the full suite once, then the S15 block, and makes the one commit.

## Section 11 — E1, KPI cards (7 tasks, one commit `(GAPS2 E1)`)

1. 11-01 writes the failing card tests (`test/test_kpi_format.py`, `test/test_help_claims_4.py`);
   on the unmodified tree `fmt(%10.0g)` of 6165.2567 reads `6e+03`; save the output to
   `/tmp/dash-s11/11-01-failure.txt`.
2. 11-02 to 11-05: the writer at first paint, the JS twin after a move (keeping the
   `dash_apply_kpis(new_data,` marker section 17 left), the flips.
3. **11-06 (Stata).** Append the `* ==== S11 E1: KPI card text ====` block (KF-01..KF-05; the
   expected strings come from Stata's own `display` at run time) and add the coverage-map
   reference; run it alone with `GAPS2_ONLY=S11`. Expected: `grep -c "KF-0[1-5] PASS"
   /tmp/dash-s11/run_test_gaps2_truth.log` prints 5, ` FAIL` prints 0.
4. 11-07 closes E1 (entry appended, dash.sthlp 1242-1250 and 1259-1261, the `<!-- WP-28 E1 -->`
   marker replaced), runs the full suite once, then the S11 block, and makes the one commit.

## Section 12 — E3 and G6, widgets, tooltips, date axes, marker labels, CSV (15 tasks, one commit `(GAPS2 E3, G6)`)

No Stata run. 12-01 and 12-02 write the failing tests (`test/test_display_format_sites.py`,
`test/test_label_sinks.py`); `TestDateAxis::test_ticks_read_as_stata_in_both_modes` reads the
`e3_tm_axis_lab` probe section 14 recorded and fails, never skips, if it is absent. 12-03 to
12-10 are the sites; 12-11 to 12-14 the flips; 12-15 closes E3 and G6 (two entries appended,
dash.sthlp 1783-1784, 2361, 2441-2461 and 862-866; 1109-1138 is section 17's and is only
verified; both markers replaced), runs the full suite once and makes the one commit whose subject
ends `(GAPS2 E3, G6)`. Section 12 lands after section 18 (it appends `fmt_cache` to
`_dash_apply_axis_spec` last).

## Landing the batch (index.md step 1)

In the merge order **S18, S15, S11, S12**, for each commit of each section, oldest first, from
the main checkout on `s3-bugs`: `git -C <worktree> format-patch -1 --stdout <sha> | patch -p1`
(never `cd` into the worktree; a rejected hunk is applied by hand under rules R1-R6), `git add`
the files the patch names, `git commit -F <the section's recorded message>`. After the last
section: the full suite once (`python3 -m pytest test/ -q`), the registry tests of R2
(`test_cscript_hygiene.py`, `test_function_test_map.py`, `test_program_coverage_map.py`,
`test_statistical_helpers.py::TestTheServedAppCarriesEveryName`,
`test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_no_orphans.py`,
`test_mode_parity.py`), and the four batch-3 blocks of `test_gaps2_truth.cscript` through the
driver (one run without `GAPS2_ONLY` covers them all). The batch is complete only when that run
is green; a red result belongs to the section that owns the test. Remove the worktrees. Then
section 19 (index.md batch 4).

## What the container run established

- At `e197c42`, under Python 3.13.12 / bokeh 3.8.2 / pandas 2.3.3 / numpy 2.3.5 on Linux
  (the suite's "stata" baseline versions): 28 failed, 19,551 passed, 122 skipped in 18 minutes;
  all 28 are the environment failures named at the top, none in WP-28's tests.
- No batch-3 file was changed there; nothing needs reconciling.
