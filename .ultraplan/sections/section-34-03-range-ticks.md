# Section 34-03: range() beyond the data: ticks over the data only

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: AX-1 · Risk: yellow · Batch: 34.2 · Depends on: 34-01 · Blocks: 34-07 · Tasks: 3, 1 commit · Case-id prefix: Q3403

## Overview

**What is wrong today.** On an axis with no label rule, twoway's `range()` widens only the scale; the ticks stay natscale over the data. The audit (AX-1, probes R1-R3 and C63, twoway's `.Graph.yaxis1.major.dlg_tickpos` beside dash's saved-page FixedTicker) measured: `scatter mpg weight, yscale(range(0))` -- twoway labels 10 20 30 40, dash 0 10 20 30 40; `yscale(range(100))` -- twoway 10 20 30 40, dash 20(20)100; `xscale(range(0 6000))` and `xscale(range(1000 6100))` -- twoway 2000(1000)5000, dash 0 2000 4000 6000 and 1000(1000)6000. test/fixtures/axis_truth.json's `b2_range_0`, `b2_range_100` and `b2_range_three` (twoway SVGs) all draw 10..40. Only an explicit `#N` (`ylabel(#5) yscale(range(100))` gives 20(20)100, R4) and a by() graph (`b2_by_range0` 0..40, R5) widen the ticks over range(); a default date axis is already special-cased and matches. The cause is the join in `_dash_finish_count_ticks` (dash_render.py:47750-47767): range() values join the tick range unless the axis is a default date axis; the saved twin is `dash_axis_compute`'s `const sc = tsd ? [] : a.scale.filter(...)` (:43437-43441). The help says range() "widens the ticks" (dash.sthlp:4529, HR-10's range part). `yscale(range(0))` is a very common idiom.

**After this section**, in both modes, at build, after a served refit and after a saved move: on a default numeric or log axis (no label rule) of a graph without by(), the ticks are placed over the data alone and range() widens only the axis's span (the hull). An explicit `#N` and every by() graph keep the widened ticks, as twoway draws them. Date axes are unchanged.

**Why one section.** One item; batch 34.2's one editor of `_dash_finish_count_ticks` and `_DASH_AXIS_FINISH_JS` (R11) and of `_make_figure_body` and the served `_generate_app_source_body` (R12, one line each).

**Test order and commit rule.** 34-03-01 measures the probes, writes the regression tests (Python, node, cscript), runs them red, saves `<scratch>/34-03-01-failure.txt`, no commit. 34-03-02 makes the Python and JS change. 34-03-03 flips the pins, corrects the help, closes AX-1 and commits `(WP-34 AX-1)`.

### Section decisions

- **D-34-03.a. "Default" is the ticker's default tag.** The rule applies to an entry whose placeholder is `_dash_default_ticker`'s (`e["default"]`, `_DASH_DEFAULT_TAG`, :47188; the plan's `a.dflt`, :46635). An axis with `#N` (any label rule) keeps the join. An axis whose label option holds sub-options and no rule (`ylabel(, angle(0))`) is a default axis for twoway (it ticks it over the data); probe R11 measures it and TR-34-03.1a makes dash agree (REVIEW R2-46).
- **D-34-03.b. by() is read from the graph, not the panel.** A figure gets `fig._dash_by_graph` (True when its graph has `by()`), stamped beside `fig._dash_numticks` in both modes; the plan carries it per axis as `byg`. Under by() the join stays for every panel, rescaled or not (twoway's b2_by_range0; a rescaled panel's own range() values are already emptied by `_dash_scale_values`' rescale rule, :56795-56796).
- **D-34-03.c. The hull keeps range().** Python's `_dash_axis_hull` reads `_dash_scale_values` (:47444-47449) and the plan's `explicit` includes `scale` (:46479), so range() still sets the span in both modes; only the tick input changes.

## Risk: [yellow] -- every default axis with range() changes its ticks in both modes and after moves

**Why.** The join is shared by numeric, log and second axes and by the by() common ticks (which read `tick_lo`/`tick_hi`).

**Risk factors.** 1. by() must keep widening (the common ticks read the finish's `tick_lo`). 2. Secondary axes read `_dash_scale_values2`. 3. Tests pinning dash's widened ticks. 4. Bars: `bar_range0` (test_bar_range_geometry.py) skips its ticks and scale today.

**Mitigation.** Probe rows for y, x, y2, log, bar, lfit, by() and #N; the by() and #N rows are guards that must stay green; the flipped pins carry reasons.

## Dependencies

- **Depends on:** 34-01 (edits `_dash_axis_plan` and the finish JS in batch 34.1; re-read both).
- **Blocks:** 34-07 (its date-axis work reads the same finish).
- **Parallel batch:** 34.2 with 34-06 and 34-08. **Can run with them:** 34-06 edits the plot-number counters and the legend counter; 34-08 edits `_dash_expand_numlist`. Neither edits the finish, the plan, `_make_figure_body` or the served builder.

## Evidence

### Code at 090d928 (re-read before editing)

```python
47750     for e in counted:
47751         lo, hi = e["lo"], e["hi"]
47752         extra = (list(scale_vals.get(e["letter"], []))
47753                  if e["name"] == "default"
47754                  else list(scale_vals2.get(e["name"], [])))
47755         if e["kind"] == "log":
47756             extra = [v for v in extra if v > 0]
47757         if e.get("default") and _dash_ts_kind(e["kind"]):
 ...
47763             extra = []
47764         if extra:
47765             lo = min(extra + ([lo] if lo is not None else []))
47766             hi = max(extra + ([hi] if hi is not None else []))
47767         e["tick_lo"], e["tick_hi"] = lo, hi
```
Saved twin, inside `dash_axis_compute` (:43422):
```js
const tsd = a.dflt && typeof a.kind === "string" && (...DASH_TS_UNITS...);
const sc = tsd ? [] : a.scale.filter((v) => a.kind !== "log" || v > 0);
```
`fig._dash_numticks = _dash_by_numticks(self.scheme, graph_opts)` (saved, `_make_figure_body` :63474) and `"        fig._dash_numticks = _dash_by_numticks(_dash_cur_scheme(), go)",` (served literal :70342). The plan entry dict is built at `_dash_axis_plan` :46622-46653 (`"dflt"`, `"scale"` ...).

### twoway's truth

axis_truth.json (scripts/extract_axis_truth.do :334-353, group b2_extent; twoway SVG texts): `b2_range_0`, `b2_range_100`, `b2_range_20_30`, `b2_range_dot_60`, `b2_range_60_dot`, `b2_range_unsorted`, `b2_range_three` all label y 10 20 30 40; `b2_hash5_range100` labels 20(20)100; `b2_by_range0` 0(10)40; `b2_log_range`, `b2_lfit_range0`, `b2_bar_xrange0`, `b2_rev_range`, `b2_td_range` are further rows. The audit's x probes: range(0 6000) and range(1000 6100) on weight label 2000(1000)5000. R8 `yscale(log range(5))` already matches (10 20 30 40).

### Tests pinning today's behaviour (flip, never delete)

- test/test_bar_range_geometry.py:653-656 `_DB_TICKS_ELSEWHERE = {"bar_range0"}` (read :695, which also skips the scale) -- becomes `set()`.
- Any test asserting the widened default ticks (find them in 34-03-02's runs of test/test_axis_extents.py, test/test_axis_options.py, test/test_graph_options.py, test/test_by_scales.py, test/test_mode_parity.py, test/test_join_order.py, test/test_server.py -- the files that name `range(0)` or a b2_range row).

## User stories

- US-34-03.1 As a Stata user with an existing twoway command, I want `yscale(range(0))` to start my axis at 0 and keep the labels 10 20 30 40, so that it reads as in twoway.
- US-34-03.2 As that user, I want `ylabel(#5) yscale(range(100))` and by() graphs to keep the widened ticks twoway draws.

## Business requirements

- BR-34-03.1 On a default numeric or log axis of a graph without by(), range() widens the axis but not its ticks, in both modes, at build and after a move.
- BR-34-03.2 With `#N`, or in a by() graph, the ticks are placed over the data and range() together, as today.
- BR-34-03.3 Date axes, second axes and bars follow the same rule as their kind does today plus BR-34-03.1.

## Technical requirements

- TR-34-03.1 `_dash_finish_count_ticks` (:47757): the condition becomes `if e.get("default") and (_dash_ts_kind(e["kind"]) or not getattr(fig, "_dash_by_graph", False)):` with the comment `# WP-34 AX-1: a default axis is ticked over its data alone; range() widens only its scale (axis_truth b2_range_*: yscale(range(0)) labels 10(10)40 over 0-41); under #N or by() the range joins the ticks (b2_hash5_range100, b2_by_range0).` The body (`extra = []`) is unchanged.
- TR-34-03.1a Sub-options without a rule (R11, D-34-03.a): 34-03-01 records in <scratch>/34-03/anchors.txt the `default` flag of R11's y entry (`_dash_count_axes(fig)` on the R11 page, both modes). If it is True, nothing more is needed. If it is False, the code that replaced the default placeholder for that option (the R11 page shows which; `_dash_parse_axis_spec`'s caller is the first place to read) keeps `_dash_default_ticker(n)`'s placeholder when the option's rule part -- its text before the first comma -- is blank, so `e["default"]` and the plan's `dflt` are True for R11 and TR-34-03.1 applies; a test in TestAgainstStata pins R11 either way.
- TR-34-03.2 Stamp: in `_make_figure_body`, after `fig._dash_numticks = ...` (:63474) add `fig._dash_by_graph = bool(str((graph_opts or {}).get("by", "") or "").strip())`; in `ServerAppBuilder._generate_app_source_body`, after the literal line `"        fig._dash_numticks = _dash_by_numticks(_dash_cur_scheme(), go)",` (:70342) add `"        fig._dash_by_graph = bool(str((go or {}).get('by', '') or '').strip())",`. A Python attribute; never serialised.
- TR-34-03.3 `_dash_axis_plan`: the axis entry dict (:46622ff) gains `"byg": bool(getattr(f, "_dash_by_graph", False))`.
- TR-34-03.4 `_DASH_AXIS_FINISH_JS`, `dash_axis_compute`: `const sc = (tsd || (a.dflt && !a.byg)) ? [] : a.scale.filter((v) => a.kind !== "log" || v > 0);` with a one-line comment naming WP-34 AX-1.
- TR-34-03.5 No new function or constant: no copy-list or function_test_map.py entry.
- TR-34-03.6 Stata truth: create `scripts/extract_range_ticks_truth.do` (header, root, `_meta` and git-stamp pattern of scripts/extract_ts_operator_truth.do:1-90; the axis reader is scripts/extract_date_axes_truth.do's `_dt_axis` (:90-106) copied as `_rt_axis`). Probes on `sysuse auto`: R1 `scatter mpg weight, yscale(range(0))`; R2 `..., yscale(range(100))`; R3 `..., xscale(range(0 6000))`; R4 `..., xscale(range(1000 6100))`; R5 `..., ylabel(#5) yscale(range(100))`; R6 `..., by(foreign) yscale(range(0))`; R7 `..., yscale(log range(5))`; R8 `bar mpg weight, yscale(range(0))`; R9 `(scatter mpg weight) (lfit mpg weight), yscale(range(0))`; R10 `(scatter mpg weight) (scatter price weight, yaxis(2)), yscale(range(0) axis(2))`; R11 `scatter mpg weight, ylabel(, angle(0)) yscale(range(0))` (REVIEW R2-46). Per probe and axis (x1, y1, y2; each panel under by() through `.Graph.graphs[k]`): `major.dlg_tickpos` list, `major.min/max/delta`, the scale's `curmin/curmax`. Output `test/fixtures/range_ticks_truth.json` `{"_meta": {...}, "probes": {"R1": {"cmd": ..., "axes": {"y1": {"ticks": [...], "cur": [lo, hi]}, ...}}}}`; `git add -f`.

## Boundaries

- Do not touch `_dash_common_count_ticks`, `_dash_place_count_ticks` or `_dash_stata_*` (34-09's), `_dash_by_numticks` (34-02's) or the histogram tick input (34-01's).
- Date-axis behaviour is unchanged (34-07 owns the date-axis end rows).
- PRD §7; R14.

## Stata truth

`scripts/extract_range_ticks_truth.do` -> `test/fixtures/range_ticks_truth.json` (TR-34-03.6), run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_range_ticks_truth.do`. Truth block, inserted directly above the first block whose `S<MM>` is higher than S03 (BRIEF "Block order"; at the batch-34.2 base that is S04, which 34-04 landed in batch 34.1), not above the marker (REVIEW R2-20); it uses S01's helpers `_q34_drawn`/`_q34_has`, defined above S01:

```
* ==== S03 AX-1: range() widens the axis, not its default ticks ====
local only : env WP34_ONLY
if inlist("`only'", "", "S03") & `: list posof "S03" in w34_run' {
    display as text "S03 start " c(current_date) " " c(current_time)
    ...
    display as text "S03 end " c(current_date) " " c(current_time)
}
* ==== end S03 ====
```
- Q3403-1: for R1, R2, R3, R4 and R11 twoway's ticks (`_q34_drawn`) equal the saved page's FixedTicker (`_q34_has`).
- Q3403-2: R5 (#5) and R6 (by()) keep the widened ticks, equal to twoway's.

## TDD test stubs

Regression tests (red at the base):
- Test: every range_ticks_truth probe's ticks and scale match twoway on every axis and panel -- test/test_range_ticks.py::TestAgainstStata::test_probes[saved|served] (red on R1-R4, R8-R11; guards R5-R7)
- Test: every axis_truth b2_extent row with a numeric y axis labels the same numbers dash ticks (`svg_truth.label_value` over its `all_text_elements` at the y-axis x position, as test/test_bar_range_geometry.py reads them) -- ::TestTheAxisTruthRows::test_b2_rows[saved|served]
- Test: after a saved move (node, the plan through test/js_runner.py) and a served refit, R1's ticks stay over the kept data and the span keeps 0 -- ::TestAfterAMove::test_saved[...], ::test_served
- Test: `fig._dash_by_graph` is set in both modes and the plan's `byg` follows it -- ::TestTheStamp::test_both_modes
cscript: Q3403-1, Q3403-2.
Pinned test to flip: test/test_bar_range_geometry.py `_DB_TICKS_ELSEWHERE`.
Parity: append `_case("yscale range 0 default ticks", [_sc()], go={"yscale": "range(0)"})` to `CORPUS` and one `_move_case("yscale range 0 after a move", <an existing range-slider move>, [_sc()], go={"yscale": "range(0)"})` to `MOVE_CORPUS`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Ticks over the data, span with range() | pytest TestAgainstStata | range_ticks_truth.json | yes |
| axis_truth b2 rows | pytest | axis_truth.json | yes |
| After a move | node + pytest | -- | yes |
| #N and by() keep widening | pytest guards + Q3403-2 | same | yes |
| Live twoway vs dash | cscript Q3403-1/2 | -- | saved |
| Parity | CORPUS, MOVE_CORPUS | -- | yes |

AC-34-03.1 `yscale(range(0))` labels 10 20 30 40 over 0-41 in both modes; AC-34-03.2 #N and by() unchanged; AC-34-03.3 after a move the rule holds; AC-34-03.4 one green commit.

## Tasks

**Commit boundary.** 34-03-01 to 34-03-03 form one commit, subject `Tick a default axis over its data when range() widens it (WP-34 AX-1)`, made by 34-03-03 on branch `wp34-s03` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s03`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-03-03 for AX-1) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-03/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-03 <scratch>/34-03/run_test_wp33_truth.do` and read `<scratch>/34-03/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-03/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-03-01">
  <name>Measure range probes and write failing tests</name>
  <files>scripts/extract_range_ticks_truth.do, test/test_range_ticks.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_finish_count_ticks, dash_axis_compute, _dash_axis_plan's entry dict and the two _dash_numticks lines at the batch-34.2 base (34-01 changed the plan and the finish JS); run `node .gitnexus/run.cjs impact "_dash_finish_count_ticks" --direction upstream --repo .` and write callers and anchors to <scratch>/34-03/anchors.txt. Create the extractor per TR-34-03.6, run it, `git add -f test/fixtures/range_ticks_truth.json`; record R11's `default` flag in anchors.txt (TR-34-03.1a). Create test/test_range_ticks.py with the TDD stubs (pages through test/test_default_axes.py's _spec/_figs; the node move through test/js_runner.py as test/test_default_axes.py's move tests do). Insert the S03 block where the Stata truth section says (above S04). Run `python3 -m pytest test/test_range_ticks.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-03/01.log`, run the S03 block with WP34_ONLY=S03, save the failures to <scratch>/34-03-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/range_ticks_truth.json'))['probes'];print(p['R1']['axes']['y1']['ticks'],p['R5']['axes']['y1']['ticks'],p['R11']['axes']['y1']['ticks']==p['R1']['axes']['y1']['ticks'])"` prints `[10.0, 20.0, 30.0, 40.0] [20.0, 40.0, 60.0, 80.0, 100.0] True` (if R11 prints False, the fixture wins: record twoway's R11 ticks in the handback and pin them); `grep -c FAILED <scratch>/34-03/01.log` is at least 4; `test -s <scratch>/34-03-01-failure.txt`.]]></verify>
  <done>twoway's range() ticks for eleven probes were recorded and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-03-02">
  <name>Tick default axes over their data</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-34-03.1 (the finish's condition), TR-34-03.1a if anchors.txt records R11's `default` as False, TR-34-03.2 (the two stamp lines, saved and served), TR-34-03.3 (byg in the plan) and TR-34-03.4 (the JS condition). Run test/test_range_ticks.py, test/test_default_axes.py, test/test_by_scales.py, test/test_axis_extents.py, test/test_axis_options.py, test/test_graph_options.py, test/test_bar_range_geometry.py, test/test_join_order.py, test/test_second_axis*.py, test/test_natscale_js.py and test/test_mode_parity.py -k "range or yscale or xscale"; list in <scratch>/34-03/flips.txt every failure that asserts dash's widened default ticks (the old picture); any other failure is a regression to fix in the code.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_range_ticks.py -q -n0 -p no:cacheprovider` ends with 0 failed; `grep -c "a.dflt && !a.byg" dash_render.py` prints 1; `grep -c "_dash_by_graph" dash_render.py` is at least 4.]]></verify>
  <done>A default axis is ticked over its data with range() in its span, in both modes and after moves, and #N and by() keep their widened ticks.</done>
</task>

<task type="auto" id="34-03-03">
  <name>Flip pins, correct the help, close AX-1</name>
  <files>test/test_bar_range_geometry.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
Flip `_DB_TICKS_ELSEWHERE` to `set()` with `# Flipped (WP-34 AX-1): twoway ticks bar_range0 over its data (10(1)14 over 0-14), dash now does.` and each node in <scratch>/34-03/flips.txt with the reason "range() widens only the scale on a default axis (WP-34 AX-1)". Append the parity entries to test/test_mode_parity.py. Help (HR-10, range part): in dash.sthlp:4529 replace ", a {cmd:range()} that widens the ticks" with "" and add, as a separate sentence after that paragraph's sentence about the margin: "On an axis with no rule, {cmd:range()} widens the axis but not its ticks, as in {cmd:twoway}: {cmd:yscale(range(0))} on {cmd:mpg} labels 10 20 30 40 over an axis from 0; with {cmd:#}{it:N}, or in a {cmd:by()} graph, the ticks are placed over the data and the range together." Add test/test_range_ticks.py::TestTheHelp::test_the_range_sentence (the `_between(_help(), ...)` pattern). Append `[WP-34 AX-1: corrected -- range() widens a default axis, not its ticks]` to the Axes row of TWOWAY_COVERAGE_AUDIT.md (:140). Close the BUGS.md entry 33-01 registered for AX-1 (closed form: _dash_finish_count_ticks and dash_axis_compute leave range() out of a default axis's tick range outside by(), fig._dash_by_graph in both modes, plan byg; pinned by test/test_range_ticks.py::TestAgainstStata::test_probes and Q3403-1; fixture range_ticks_truth.json); rewrite `- **AX-1 Tracked:**` to the Closed form with `commit pending`; delete AX-1's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- yscale(range(0)) and other range() values beyond the data no longer widen a default axis's ticks (scatter mpg weight, yscale(range(0)): 0(10)40 -> 10(10)40) (WP-34, AX-1)` under `### Fixed in WP-34`. Run the Closing steps for AX-1 (Tasks; BRIEF steps (1)-(3)): (1) delete AX-1's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py AX-1`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-03) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_range_ticks.py, test/test_bar_range_geometry.py, the flipped nodes, test/test_mode_parity.py -k "range", test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py and the S03 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_range_ticks.py test/test_bar_range_geometry.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3403-[12] PASS" <scratch>/34-03/run_test_wp34_truth.log` prints 2; `awk -F'\t' '$1 == "AX-1"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py AX-1` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-03/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 AX-1)`.]]></verify>
  <done>range() widens a default axis without widening its ticks in both modes, the help says so, and AX-1 is closed in one commit.</done>
</task>

## Section completion criteria

- range_ticks_truth and the axis_truth b2 rows match in both modes; #N and by() guards green; the bar pin flipped; the help sentence corrected and pinned; tracking documents; one green commit.

## Notes

- **R11/R12:** 34-03 is batch 34.2's one editor of `_dash_finish_count_ticks`, `_DASH_AXIS_FINISH_JS`, `_make_figure_body` and `ServerAppBuilder._generate_app_source_body`.
- **Help (R3, HR-10):** this section owns the range() clause of dash.sthlp:4529 and the one new sentence; 34-01's histogram sentence (batch 34.1) is beside it and 34-09 rewrites the paragraph's model sentence in batch 34.4.
- **Trap:** `e.get("default")` is True for a default axis only; check that the axis entries of a `#N` axis carry `default` False (they do at 090d928: `_DASH_DEFAULT_TAG` is only on `_dash_default_ticker`'s placeholder, :47186-47187).
- **Trap:** a log axis's range() values at or below 0 are already dropped (:47755-47756, inside the finish loop :47750-47767); keep that line.
- **Commit body line forms:** `Regression: test/test_range_ticks.py::TestAgainstStata::test_probes -- failed at <base sha> with <text>`; `Flipped: test/test_bar_range_geometry.py::<class>::<test> -- bar_range0's ticks were skipped, which was wrong because twoway ticks its data only`; `Fixture: test/fixtures/range_ticks_truth.json (scripts/extract_range_ticks_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: AX-1 Tracked`.
- Merge rules touched: R1, R3, R7, R8, R9, R11, R12.
