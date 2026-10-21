# Section 34-01: Histogram bin axis ticked over the midpoints

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: AX-4 (VF-1, DG-2) · Risk: yellow · Batch: 34.1 · Depends on: none · Blocks: 34-03, 34-02 · Tasks: 4, 1 commit · Case-id prefix: Q3401

## Overview

**What is wrong today.** Every default histogram's bin axis is ticked over the bars' edges. The audit (AX-4, VF-1, DG-2) measured `histogram mpg` on auto: twoway draws x ticks 15(5)40 over a scale running 12-41, because its scale min and max are the first and last bin midpoints (test/fixtures/default_axes_truth.json P08: `min 13.8125, max 39.1875`, `major [15, 5, 40]`, `cur [12, 41]`). dash draws 10(10)40 over 9.58-41.42, leaving an empty band left of the first bar. The same holds for `histogram price` (dash adds a 0 tick), `price, width(2000)` (dash 0-20000 where twoway draws 5000(5000)15000), `rep78, discrete` (dash 0 2 4 6 where twoway draws 1(1)5), `weight, frequency` (dash 2000(1000)5000 where twoway draws 2000(500)4500), `length, percent` (dash 140(20)240 where twoway draws 140(20)220), a constant 5 (dash 5(.2)6 where twoway draws 4.5 6.5) and `mpg, horizontal` on y. The cause: `map_histogram` draws a `Quad` whose `left`/`right` fields are both in `_DASH_X_COORDS`, and `_dash_layer_extent` reads every coordinate field as tick input; `histogram` is in `_DASH_STATA_TICK_SKIP`, so the model runs over the edges. The only tracking is the test exclusion `_NOT_DEFAULT = {("P08", "x")}` (test/test_default_axes.py:233).

**After this section**, in both modes, at build, after a served refit and after a saved-page rebin: a histogram's bin axis takes its tick input from the first and last bin midpoints of the bin grid (not from the drawn bar edges, so `gap()` and `baroffset()` do not move the ticks, as measured), while the bars' edges stay in the axis's hull, so the axis still spans every bar. Turned (`horizontal`) histograms do the same on y. The ticks are still the natscale model's at build (the midpoint range is not a variable range, so `histogram` stays in `_DASH_STATA_TICK_SKIP`); 34-09 later asks Stata over the same midpoint range. Over midpoints the model gives twoway's answer in every probe the audit ran.

**Why one section.** One item, one owner of `_dash_layer_extent`, `_dash_axis_plan`, `dash_axis_extent`/`dash_axis_hull` and the `_FILTER_JS` histogram branch in batch 34.1 (R11/R12: this section is batch 34.1's one editor of `_FILTER_JS` and `_DASH_AXIS_FINISH_JS`).

**Test order and commit rule.** 34-01-01 measures the new rows, writes every regression test and the cscript block, runs them on the unmodified tree, saves `<scratch>/34-01-01-failure.txt` and does not commit. 34-01-02 makes the Python tick input; 34-01-03 makes the saved-page twin; 34-01-04 flips the pins, edits the help and the tracking documents and makes the one commit `(WP-34 AX-4)`.

### Section decisions

- **D-34-01.a. The tick input is a column, not a formula.** `map_histogram` writes `__dash_mid` (the bin centres of the kept bars, from the grid's axis edges) into the bars' source and stamps the Quad renderer `_dash_tick_fields = {"x": ("__dash_mid",)}`. Every tick-input reader (`_dash_layer_extent` with role `"data"`, `_dash_axis_plan`'s layer `fields`) reads those columns instead of the glyph's coordinate fields on that letter; the hull readers keep reading `left`/`right`. Measured 20oct2026 (this plan's probe): `histogram mpg, gap(50) baroffset(1)` keeps x major 15(5)40 while its scale runs 11.09-41.91, so the drawn bars are no tick input.
- **D-34-01.b. Stata is not asked here.** `histogram` stays in `_DASH_STATA_TICK_SKIP` (dash_render.py:41811-41812): the export summarizes variables, and a midpoint range is no variable's range. 34-09's build-time oracle covers it.
- **D-34-01.c. Scope.** The Quad branch only. The `mwidth` branch (`fig.vbar`, x = the bin start) and the `recast()` branches (which already draw the midpoints as `x`) are unchanged.

## Risk: [yellow] -- the tick reader and the hull reader split for one glyph, in Python and in the saved page's JavaScript

**Why.** A field read as tick input but not as hull, or the reverse, either clips the bars or leaves the old ticks; the saved rebin replaces `src.data` wholesale, so a column it forgets disappears after the first move.

**Risk factors.** 1. `_dash_transpose_layer` must turn `_dash_tick_fields` with the glyph (horizontal). 2. The saved rebin (`_FILTER_JS` ~:34600-34650) builds `src.data = {top, left, right}` in two places (the empty branch and the counted branch). 3. Date-kind histograms draw edges through `_on_axis` (axis units): the midpoints must be computed from the same axis edges. 4. by() panels share the x letter through `_dash_common_count_ticks`, which reads `tick_lo`/`tick_hi` from the finish.

**Mitigation.** A unit test per reader; a horizontal row; a node test of the rebin; a by() row (twoway's B5 agreed with dash at the base, so it is a guard); the parity corpus entries.

## Dependencies

- **Depends on:** none (WP-34 W0 has created `test/test_wp34_truth.cscript` and `### Fixed in WP-34`).
- **Blocks:** 34-03 (edits the finish's scale join and the same JS function family next batch), 34-02 (by() ticks read the same extent).
- **Parallel batch:** 34.1 with 34-04 and 34-05. **Can run with them:** 34-04 edits `_dash_frame_sizes` only; 34-05 edits `map_area`, one SchemeParser method, one rule in `_dash_auto_base_props`, one call in `_dash_finish_auto_bases`, the key rules of `_dash_legend_keys`, one `continue` in `GlyphMapper._tag_recast` and one filter clause of `_dash_build_hover`, and adds its own ring script (a `CustomJS`, not a hot literal); `map_histogram`'s recast branch keeps calling `_tag_recast` as it does (:22263), and neither section edits that call. None of them edits `_dash_layer_extent`, `_dash_axis_plan`, `_dash_transpose_layer`, `_DASH_AXIS_FINISH_JS` or `_FILTER_JS`. `_dash_layer_extent` and `_dash_axis_plan` call `_dash_auto_base_props`: keep that call where it is, so 34-05's rule (an area's outline ring is no tick input) reaches both readers after the merge.

## Evidence

### Code at 090d928 (re-read before editing; anchors drift)

`map_histogram` (dash_render.py:22094) builds the bars' source at :22188-22192:

```python
        hist_source = ColumnDataSource({
            "top":   tops[i0:i1],
            "left":  _hl,
            "right": _hr,
        })
```
`axis_edges` (:22165) are the grid's edges in axis units; `_hl`/`_hr` are the drawn bar edges after `gap()`/`baroffset()` (:22185-22187). The Quad is drawn by `_histogram_quads` (:22033, `fig.quad(top="top", bottom=0, left="left", right="right")` :22067-22072). The recount config's `bin_edges` is `axis_edges[i0:i1 + 1]` (`_hist_agg_config` :22294, :22303).

`_DASH_X_COORDS = ("x", "x0", "x1", "x2", "left", "right")` (:45690). `_dash_layer_extent(renderers, range_attr, name, kind=None, role="data")` (:46078) loops `for attr in fields:` over every coordinate field of the glyph (:46131-46158) and is the tick input of `_dash_count_axes` (:47180). The hull reads `_dash_secondary_values` (:45875; its field loop :45908-45929), which this section does not change. `_dash_transpose_layer` (:45769) turns `_dash_hull_fields` at :45842-45845:

```python
        hf = getattr(r, "_dash_hull_fields", None)
        if hf:
            r._dash_hull_fields = {("y" if k == "x" else "x"): v
                                   for k, v in hf.items()}
```

`_dash_axis_plan` (:46382) writes each layer as `{"src", "filt", "fk", "fields", "consts", "bfields", "bconsts", "units"}` (:46616-46620), `fields` from the glyph's coordinate attributes (:46571-46590). The saved twin `dash_axis_extent(a, models, base)` (:43118) reads `L.fields`; `dash_axis_hull(a, ticks, lo, hi, models, bases)` (:43148) joins `lo`/`hi`, the placed ticks, `a.held`, `a.explicit` and `a.bars`. The saved rebin is the `ac.type === 'histogram'` branch of `_FILTER_JS` (:34551-34650): `src.data = { top: ..., left: _hl, right: _mw ? _hl.slice() : _hr }` at :34605-34609 (no rows) and :34646-34650 (counted).

### twoway's rule

twoway__histogram_gen.ado generates the bin midpoints as the serset's x, and the scale's `min`/`max` are that variable's (default_axes_truth.json P08). Measured 20oct2026 with the plan's probe: `histogram mpg` x major 15 40 delta 5, curmin 12, curmax 41; `histogram mpg, horizontal` y major 15 40 delta 5; `histogram mpg, gap(50) baroffset(1)` x major 15 40 delta 5, curmin 11.09375, curmax 41.90625. The audit's probes (AX-4 appendix, VF-1, DG-2): price 5,000-15,000; price bin(8) and width(2000) 5000(5000)15000; rep78 discrete 1(1)5; weight frequency 2000(500)4500; length percent 140(20)220; constant 5: 4.5 6.5 (natscale's lo==hi rule over the one midpoint 5.5); width(5) start(10) 10(10)40; by() rows agree.

### Fixtures on disk

test/fixtures/default_axes_truth.json (scripts/extract_default_axes_truth.do; rows `P|`, `S|` per probe, `_ns_rec <id> <scheme> <data> <svg> "<cmd>"` at :117-136; datasets `_ns_data` :67-78). P08 is the only histogram row.

### Tests pinning today's behaviour (flip, never delete)

- test/test_default_axes.py:230-233 `_NOT_DEFAULT = {("P08", "x")}`, read at :242 -- becomes `set()` with a `Flipped:` comment.
- test/test_stata_ticks.py::TestTheRangeRule::test_histogram_axis_has_no_key (:225) -- stays green (D-34-01.b); not a flip.
- Any test asserting dash's edge-based histogram x ticks: run `grep -ln "histogram" test/test_*axis*.py test/test_hist*.py test/test_default_axes.py test/test_by_scales.py` and the files 34-01-04 runs; a failure that asserts 10(10)40-style edge ticks is flipped with the reason "twoway ticks the bin midpoints (P08)".

## User stories

- US-34-01.1 As a Stata user with an existing twoway command, I want `dash histogram mpg` to label 15 20 25 30 35 40 with the first bar at the axis's left edge, so that it looks like my twoway histogram.
- US-34-01.2 As that user, I want a discrete, binned, frequency, percent and turned histogram ticked as twoway ticks it.
- US-34-01.3 As a dashboard author, I want a filtered histogram's axis to keep following its bins after a move.

## Business requirements

- BR-34-01.1 A histogram's bin axis is ticked over its first and last bin midpoints and spans every bar, at build, in both modes.
- BR-34-01.2 After a filter move the bin axis is ticked over the kept grid's midpoints, in both modes.
- BR-34-01.3 `gap()` and `baroffset()` do not change the ticks; they change only the span.
- BR-34-01.4 A turned histogram follows the same rule on its y axis.
- BR-34-01.5 Every other layer type's ticks are unchanged.

## Technical requirements

- TR-34-01.1 `GlyphMapper.map_histogram` (Quad branch only, after `hist_source` is built, :22188-22192): add the column `"__dash_mid": [(float(axis_edges[k]) + float(axis_edges[k + 1])) / 2.0 for k in range(i0, i1)]` to `hist_source.data`, and after `r = _tag(self._histogram_quads(...))` (:22275) set `r._dash_tick_fields = {"x": ("__dash_mid",)}` when `mwidth_px` is None. The empty branches get no column.
- TR-34-01.2 `_dash_layer_extent` (:46078): before the field loop, `tick = (getattr(r, "_dash_tick_fields", None) or {}).get(range_attr[0]) if role == "data" else None`; when `tick` is set, the loop runs over `tick` instead of `fields`, reading each name as a data column (same `rows` selection, same `_dash_float_values`, same log filter), and the glyph's coordinate fields are not read for that renderer. `role == "base"` is unchanged.
- TR-34-01.3 `_dash_transpose_layer` (:45769): after the `_dash_hull_fields` turn (:45842-45845), turn `_dash_tick_fields` the same way: `tf = getattr(r, "_dash_tick_fields", None)`; `if tf: r._dash_tick_fields = {("y" if k == "x" else "x"): v for k, v in tf.items()}`.
- TR-34-01.4 `_dash_axis_plan` (:46382), per renderer and letter: `tick = (getattr(r, "_dash_tick_fields", None) or {}).get(letter)`; when set, `lf` holds `tick`'s names that are in `src.data`, and the glyph's coordinate fields that were read (`left`, `right` or, turned, `bottom`, `top`) go into a new list `hf`; the layer dict gains `"hfields": hf` (always present, `[]` when empty). No other key changes.
- TR-34-01.5 `_DASH_AXIS_FINISH_JS`, `dash_axis_hull` (:43148): after the `a.held` loop, for each `L` of `a.layers` with `L.hfields && L.hfields.length`, read each field's column over `dash_axis_rows(L, models, n)` exactly as `dash_axis_extent` reads `L.fields` (units through `dash_axis_unit_of(L.units, fld)`), pushing each finite value (positive on a log axis) into `vals`. `dash_axis_extent` is unchanged (it already reads `L.fields`).
- TR-34-01.6 `_FILTER_JS` histogram branch: before either `src.data = {...}` assignment, `const _hmid = (src.data && src.data.__dash_mid !== undefined);` and in both assignments, when `_hmid` and not `_mw`, add `__dash_mid: mids` with `const mids = []; for (let k = 0; k < n_bins; k++) mids.push((edges[k] + edges[k + 1]) / 2);` (`edges` = `ac.bin_edges`, axis units, the same numbers Python used).
- TR-34-01.7 Served mode: no literal changes. The served redraw copies `_new.data` onto the live source (dash_render.py:71363-71364), so `__dash_mid` arrives with each redraw; `_dash_refinish_axes` reads it through `_dash_layer_extent`. No new module-level helper, so no copy-list entry (R2); no new function, so no function_test_map.py row.
- TR-34-01.8 Stata truth: scripts/extract_default_axes_truth.do gains `_ns_data` dataset `c5` (`sysuse auto, clear` then `quietly generate c = 5`) and rows after the P08 line (:139): `H01 stcolor auto 0 histogram price`, `H02 ... histogram price, bin(8)`, `H03 ... histogram price, width(2000)`, `H04 ... histogram rep78, discrete`, `H05 ... histogram weight, frequency`, `H06 ... histogram length, percent`, `H07 ... histogram mpg, horizontal`, `H08 c5 ... histogram c`, `H09 ... histogram mpg, gap(50) baroffset(1)`, `H10 ... histogram mpg, by(foreign)`, each as `_ns_rec Hnn stcolor <data> 0 \`"\`T' histogram ...,"'`. test/test_default_axes.py `_PROBES` gains the ten rows with the same layers (`P("histogram", "price", bin="8")` and so on; H08 reads a frame with `c = 5` (`_frame` gains `elif which == "c5": df = df.assign(c=[5.0] * len(df))`; the auto frame from by_scales_truth.json's `data.auto` already holds foreign, length, mpg, price, rep78, turn and weight); H10 `{"by": "foreign"}`).

## Boundaries

- Do not touch `_DASH_STATA_TICK_SKIP` (no WP-34 section changes it; D-34-01.b), `_dash_stata_tick_requests` (34-07's and 34-09's) or dash.ado (34-07's: `_dash_axis_ticks_stata`, TR-34-07.4).
- Do not touch `_dash_finish_count_ticks`' scale join (34-03, next batch) or `_dash_by_numticks` (34-02).
- Do not touch the `mwidth` and `recast()` branches (D-34-01.c), kdensity or function layers.
- PRD §7: no new dependency; R14 banned topics.

## Stata truth

Extend `scripts/extract_default_axes_truth.do` per TR-34-01.8; run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_default_axes_truth.do`; the `_meta` stamp is the script's own (`stata_version`, `born_date`, `dash_commit`, `extracted`, `source`); `git add -f test/fixtures/default_axes_truth.json`. Expected rows: H01 x major 5000(5000)15000; H02, H03 the same; H04 1(1)5; H05 2000(500)4500; H06 140(20)220; H07 y 15(5)40; H08 4.5 6.5; H09 15(5)40 with cur 11.09375-41.90625; H10 every panel 15(5)40 or twoway's own (a guard). If any row differs from these numbers, the fixture wins; record the difference in the handback.

Truth block in test/test_wp34_truth.cscript, inserted directly above the first block whose `S<MM>` is higher than S01 (BRIEF "Block order"), or above `* ==== append new blocks above this line ====` if there is none (at the batch-34.1 base there is none). Above the block, outside any gate, define once for every WP-34 block: the program `_q34_drawn <graph> <axis>` (WP-31's `_u45_drawn`, test_wp31_truth.cscript:12445-12458, renamed; sets global `q34_t` to the axis's `major.dlg_tickpos` list) and the python helper `_q34_has(page, kind, want)` (WP-31's `_u45_has`, :12425-12443, renamed; sets global `q34_bad`).

```
* ==== S01 AX-4: histogram bin axis over the midpoints ====
local only : env WP34_ONLY
if inlist("`only'", "", "S01") & `: list posof "S01" in w34_run' {
    display as text "S01 start " c(current_date) " " c(current_time)
    ... Q3401-1, Q3401-2, Q3401-3 ...
    display as text "S01 end " c(current_date) " " c(current_time)
}
* ==== end S01 ====
```
- Q3401-1: for `histogram mpg`, `price, width(2000)`, `rep78, discrete`, `mpg, horizontal` (y): twoway's ticks (`_q34_drawn .Graph x1` or `y1`) equal `dash histogram ..., saving(<dir>/hNN.html, replace)`'s FixedTicker (`_q34_has`).
- Q3401-2: `histogram mpg, gap(50) baroffset(1)`: same equality (the bars are no tick input).
- Q3401-3: `histogram mpg if foreign` (a qualifier's rows): same equality.

## TDD test stubs

Regression tests (red at the base):
- Test: `_dash_layer_extent` over a histogram Quad renderer returns the first and last midpoints on x, and over the same renderer with role "base" returns None -- test/test_histogram_bin_axis.py::TestTheTickInput::test_extent_reads_the_midpoints
- Test: the axis hull still spans the bar edges (`_dash_hull_entries` x lo/hi equal the first left and last right edge, plus margin) -- ::TestTheTickInput::test_hull_keeps_the_edges[saved|served]
- Test: `_dash_transpose_layer` turns `_dash_tick_fields` -- ::TestTheTickInput::test_transpose_turns_the_tick_fields
- Test: the plan's histogram layer has `fields == ["__dash_mid"]` and `hfields == ["left", "right"]` -- ::TestThePlan::test_plan_fields
- Test: every new default_axes_truth row matches in each mode -- test/test_default_axes.py::TestStataTruth::test_probes[saved|served] (red through H01-H09)
- Test: after a saved range move on `mpg` the rebinned source carries `__dash_mid` equal to the kept grid's centres and the axis ticks equal `_dash_axis_count_ticks(first_mid, last_mid, 5)` (node, test/js_runner.py) -- ::TestAfterAMove::test_saved_rebin
- Test: the served refit after the same move ticks the same values -- ::TestAfterAMove::test_served_refit
cscript: Q3401-1, Q3401-2, Q3401-3.
Pinned tests to flip: test/test_default_axes.py `_NOT_DEFAULT` (:233) to `set()`.
Parity: append to `CORPUS` in test/test_mode_parity.py `_case("histogram gap baroffset", [plot_for("histogram", {"gap": "50", "baroffset": "1"})])` and `_case("histogram horizontal ticks", [plot_for("histogram", {"horizontal": "horizontal"})])`; append to `MOVE_CORPUS` one `_move_case("histogram mid ticks after a range move", <the file's existing range-slider move on the y variable>, [plot_for("histogram")])` (copy the move tuple an existing histogram `_move_case` uses; `ALLOWED` is never edited, R8).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tick input over midpoints | pytest unit | -- | n/a |
| Every histogram row vs twoway | pytest TestStataTruth::test_probes | default_axes_truth.json H01-H10 | yes |
| Hull keeps the edges | pytest | P08, H09 | yes |
| Saved rebin carries the midpoints | node via test/js_runner.py | -- | saved |
| Served refit | pytest | -- | served |
| Live twoway vs dash | cscript Q3401-1..3 | -- | saved |
| Parity | test_mode_parity.py CORPUS/MOVE_CORPUS | -- | yes |

AC-34-01.1 `histogram mpg` draws 15(5)40 over 12-41 in both modes; AC-34-01.2 H01-H10 match twoway; AC-34-01.3 the ticks follow a move in both modes; AC-34-01.4 `gap()`/`baroffset()` leave the ticks; AC-34-01.5 one green commit with P08 back in the comparison.

## Tasks

**Commit boundary.** 34-01-01 to 34-01-04 form the one commit, subject `Tick the histogram's bin axis over its first and last bin midpoints (WP-34 AX-4)`, made by 34-01-04 on branch `wp34-s01` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s01` (BRIEF "Pull form": every command below that names `$WT` uses this absolute path).

<task type="auto" id="34-01-01">
  <name>Measure histogram rows and write failing tests</name>
  <files>scripts/extract_default_axes_truth.do, test/test_histogram_bin_axis.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read map_histogram, _dash_layer_extent, _dash_transpose_layer, _dash_axis_plan, dash_axis_hull and the _FILTER_JS histogram branch at the batch base and write their anchors to <scratch>/34-01/anchors.txt. Apply TR-34-01.8 to scripts/extract_default_axes_truth.do and test/test_default_axes.py's _PROBES (ten rows H01-H10), run the extractor through scripts/stata_slot.sh (the Stata truth section's command) and `git add -f test/fixtures/default_axes_truth.json`. Create test/test_histogram_bin_axis.py with the TDD stubs above (build pages with test/test_default_axes.py's _spec/_figs helpers, import them; node via js_runner as test/test_default_axes.py does). Insert the S01 block with Q3401-1..3 where the Stata truth section says, and the shared helpers _q34_drawn/_q34_has directly above it (outside any gate). Run `python3 -m pytest test/test_histogram_bin_axis.py test/test_default_axes.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-01/01.log`, run the cscript through the two-line driver with WP34_ONLY=S01, and write both outputs' failure lines to <scratch>/34-01-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/default_axes_truth.json'))['probes'];print(p['H01']['x']['major'],p['H04']['x']['major'],p['H08']['x']['major'])"` prints `[5000.0, 5000.0, 15000.0] [1.0, 1.0, 5.0]` and H08's two-tick form; `grep -c FAILED <scratch>/34-01/01.log` is at least 6; `grep -c "Q3401-[123] FAIL" <scratch>/34-01/run_test_wp34_truth.log` is at least 2; `test -s <scratch>/34-01-01-failure.txt`.]]></verify>
  <done>Twoway's histogram ticks for ten new probes were recorded and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-01-02">
  <name>Read the midpoints as the tick input</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-34-01.1 (the __dash_mid column and r._dash_tick_fields in map_histogram's Quad branch), TR-34-01.2 (_dash_layer_extent reads _dash_tick_fields on role "data"), TR-34-01.3 (_dash_transpose_layer turns it) and TR-34-01.4 (_dash_axis_plan writes fields from the tick columns and the new hfields list). Run test/test_histogram_bin_axis.py::TestTheTickInput and ::TestThePlan, test/test_default_axes.py, test/test_histogram*.py and test/test_horizontal*.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_histogram_bin_axis.py -k "TickInput or ThePlan" test/test_default_axes.py -q -n0 -p no:cacheprovider` ends with 0 failed except TestAfterAMove nodes (deselected); `grep -c "_dash_tick_fields" dash_render.py` is at least 5.]]></verify>
  <done>At build and in the served refit a histogram's bin axis is ticked over its midpoints and spans its bar edges.</done>
</task>

<task type="auto" id="34-01-03">
  <name>Carry the midpoints through the saved page</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action><![CDATA[
Apply TR-34-01.5 (dash_axis_hull reads L.hfields) and TR-34-01.6 (both src.data assignments of the _FILTER_JS histogram branch write __dash_mid from ac.bin_edges when the source had it and mwidth is off). Append the three parity entries named under TDD test stubs. Run test/test_histogram_bin_axis.py whole, test/test_mode_parity.py -k "histogram", test/test_saved_filter_layers.py -k histogram, test/test_csp.py and test/test_natscale_js.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_histogram_bin_axis.py test/test_mode_parity.py -k "histogram" test/test_csp.py -q -n0 -p no:cacheprovider` ends with 0 failed.]]></verify>
  <done>After a saved move the rebinned histogram keeps its midpoint column and both modes tick the same values.</done>
</task>

<task type="auto" id="34-01-04">
  <name>Flip pins, document, close AX-4</name>
  <files>test/test_default_axes.py, dash.sthlp, scripts/corpus/ledger.tsv</files>
  <action><![CDATA[
Flip `_NOT_DEFAULT` (test/test_default_axes.py:233) to `set()` with the comment `# Flipped (WP-34 AX-4): twoway's histogram is ticked over its bin midpoints, P08 is compared now.` and flip any other edge-tick pin the runs below expose with the same reason. Help: after the sentence ending "takes the model at once." (dash.sthlp:4529) add `A {cmd:histogram}'s bin axis is ticked over its first and last bin midpoints, as {cmd:twoway} ticks it, and spans the bars' edges: {cmd:histogram mpg} labels 15 20 25 30 35 40.` Append `[WP-34 AX-4: corrected -- the bin axis ticked over the bin midpoints]` to the histogram row of TWOWAY_COVERAGE_AUDIT.md (:98). Close the BUGS.md entry 33-01 registered for AX-4 (the one whose Resolution reads "WP-34 section 34-01 has not landed") with PD-4's closed form naming map_histogram, _dash_layer_extent, _dash_axis_plan, dash_axis_hull and the _FILTER_JS rebin, both modes, pinned by test/test_histogram_bin_axis.py::TestAfterAMove::test_saved_rebin and Q3401-1, fixture default_axes_truth.json; flip `- [ ]` to `- [x]`; rewrite `- **AX-4 Tracked:**` in GAPS4.md to `Closed in WP-34, BUGS.md "<title>", commit pending.`; delete AX-4's line from GAPS4_OPEN in test/test_tracking_documents.py; add `- A histogram's bin axis is ticked over its first and last bin midpoints, as twoway ticks it (histogram mpg: 10(10)40 -> 15(5)40) (WP-34, AX-4)` under `### Fixed in WP-34` in CHANGELOG.md. Before the commit, BRIEF's "The corpus ledger and the known-differences tables" steps, in order: (1) delete AX-4's plain rows of scripts/corpus/ledger.tsv (first column exactly `AX-4`; keep any `AX-4 (documented)` or `AX-4 (residual)` row), rerun `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest test/test_corpus_ledger.py -q -n0`; (2) run `python3 test/known_differences.py AX-4` (33-10, D-33-10.h) and delete every row it prints (from test/value_truth_known.py, test/test_abbreviations.py or the other table file it names; AX-4's ruling keeps no difference, so no key moves into a deliberate dict -- `DELIBERATE` in test/value_truth_known.py, `ABBREV_DELIBERATE` in test/test_abbreviations.py, or the `<NAME>_DELIBERATE` beside a 33-11..33-13 table), then run the hygiene command it prints; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through the two-line driver); if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-01 $WT/scripts/extract_corpus_guard_truth.do`, `git add -f test/fixtures/corpus_guard_truth.json`, add the body line `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` and commit it with this item (rerun the S09 block: `Q3309-1 PASS`). Run the section's files: test/test_histogram_bin_axis.py, test/test_default_axes.py, test/test_stata_ticks.py, test/test_by_scales.py, test/test_mode_parity.py -k histogram, test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py, and the S01 block. Before committing, run `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s01 pull --ff-only . main` (BRIEF "Pull form": a no-op when the batch base already contains main; CLAUDE.md rule 4). Run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is re-run), then commit with the body lines of BRIEF (Regression, Flipped, Fixture, BUGS.md, GAPS4); grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_histogram_bin_axis.py test/test_default_axes.py test/test_stata_ticks.py test/test_by_scales.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3401-[123] PASS" <scratch>/34-01/run_test_wp34_truth.log` prints 3; `git log -1 --format=%s` ends `(WP-34 AX-4)`; `grep -c "AX-4 Tracked:\*\* Closed in WP-34" GAPS4.md` prints 1; `awk -F'\t' '$1 == "AX-4"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py AX-4` prints no row; the S09 guard block (rerun after any regeneration) prints `Q3309-1 PASS`; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>The histogram bin axis matches twoway in both modes and after moves, P08 is compared, and AX-4 is closed in one commit.</done>
</task>

## Section completion criteria

- Ten new default_axes_truth rows and P08 match in both modes; the hull spans every bar; moves keep the midpoint rule in both modes.
- One green commit `(WP-34 AX-4)`; BUGS entry closed, GAPS4 Tracked line `commit pending`, GAPS4_OPEN line removed, CHANGELOG line, coverage-audit tag, help sentence.
- No change to `_DASH_STATA_TICK_SKIP`, dash.ado or the finish's scale join.

## Notes

- **GitNexus (CLAUDE.md):** before editing `map_histogram`, `_dash_layer_extent`, `_dash_transpose_layer` and `_dash_axis_plan`, run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` and write the callers and risk into `<scratch>/34-01/anchors.txt`; a HIGH or CRITICAL risk (or UNKNOWN, confirmed by a text search) is named in the handback.
- **R11/R12:** 34-01 is batch 34.1's one editor of `_FILTER_JS` and `_DASH_AXIS_FINISH_JS` and of `_dash_axis_plan`; 34-04 and 34-05 must not touch them.
- **Help (R3):** this section owns only the sentence it adds after dash.sthlp:4529. 34-03 edits the same paragraph's range() clause next batch and 34-09 rewrites its model sentence in batch 34.4: insert the new sentence as a separate sentence so their edits apply cleanly.
- **Trap:** the plan's `hfields` key must be present on every layer dict (an empty list), or `dash_axis_hull` reads `undefined.length`.
- **Trap:** `_dash_layer_extent` must still read `_dash_eval_values` and `_dash_hull_fields` for the renderer (they follow the field loop) -- only the coordinate loop is replaced.
- **Commit body line forms:** `Regression: test/test_histogram_bin_axis.py::TestTheTickInput::test_extent_reads_the_midpoints -- failed at <base sha> with <text>`; `Flipped: test/test_default_axes.py::TestStataTruth::test_probes -- _NOT_DEFAULT left P08 x out, which was wrong because twoway ticks the bin midpoints`; `Fixture: test/fixtures/default_axes_truth.json (scripts/extract_default_axes_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: AX-4 Tracked`.
- **Manifest (REVIEW R2-25):** the index's Owns cell (index.md, row 34-01) names exactly what this section edits: `GlyphMapper.map_histogram`'s Quad branch (`__dash_mid` and `_dash_tick_fields`, TR-34-01.1), `_dash_layer_extent` (TR-34-01.2), `_dash_transpose_layer` (TR-34-01.3), `_dash_axis_plan` (TR-34-01.4), `_DASH_AXIS_FINISH_JS`'s `dash_axis_hull` (TR-34-01.5), `_FILTER_JS`'s histogram branch (TR-34-01.6), scripts/extract_default_axes_truth.do and test/test_default_axes.py (TR-34-01.8). It names neither `dash_axis_extent` (unchanged: it already reads `L.fields`) nor `_DASH_STATA_TICK_SKIP` (unchanged, D-34-01.b).
- Merge rules touched: R1, R2 (none needed), R7, R8, R9, R11, R12.
