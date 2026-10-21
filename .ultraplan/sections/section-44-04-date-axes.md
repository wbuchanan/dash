# Section 44-04: Date axes: numbers where twoway labels numbers, %tC, dates with blanks

> Part of: WP-44 (Axes, audit package 9) · Items: AX-18, DG-6, DG-4 · Risk: yellow · Batch: 44.1 · Depends on: none (WP-34 landed) · Blocks: none · Tasks: 7, 3 commits · Case-id prefix: Q4404

## Overview

**What is wrong today.**

- **AX-18 (stat:PT-20, VF-12).** "A date axis is kept where twoway labels Stata numbers (first layer lfit/qfit/ci/kdensity/lpoly/function/immediates); xscale(log) on a date axis is drawn linear" (audit :470). `_dash_figure_date_kind` (dash_render.py:1559-1599) returns the date kind whenever every layer on the axis draws one date kind, and its docstring records the first-plot rule as "a documented divergence, ratified 01oct2026"; twoway labels `kdensity date` (sp500) 15000(100)15400 and `lfit close date, range(14900 15400)` 14900(100)15400 (appendix :1298-1303, D06, K5). For `xscale(log)` the saved figure warns "xscale(log) is meaningless for the date variable ...; drawing a date axis instead" and drops the log (:63443-63456; served template :70318-70330); twoway draws a log scale with date labels (dash.sthlp:4723-4731). Both are documented today as differences (dash.sthlp:4815-4820).
- **DG-6.** "%tC ticks are placed and labelled in leap-second-corrected time (22 s off in 2001)" (audit :488). dash converts %tC values to %tc milliseconds with `_dash_tc_from_tC` (:685-700) but places Stata's tick numbers (asked over the raw %tC values at export) on the converted axis unchanged, so `scatter mpg tC` labels `01jan2001 20:26:40` where twoway labels `20:26:18` (T05 against T04; %tc matches).
- **DG-4.** "Parenthesised dates holding blanks ((1 jan 2001)) are refused in tlabel(), tline() and tscale(range())" (audit :491). `_dash_tdate_value`'s gate (dash_parse.mata:9310) excludes the blank and `_dash_tdate_lines` splits with `tokens(seg)` (:9512), which does not bind parentheses; `_dash_tdate_range` does the same (:9566). twoway draws `tlabel((1 jan 2001) (1 jul 2001))`, `tline((15 jun 2001))`, `tscale(range((1 dec 2000) (31 jan 2002)))` (DT04, DT05, DT09, DT20; datelist.sthlp binds dates with spaces in parentheses).

**After this section**, in both modes and after a filter move: an axis whose first layer is one of twoway's eleven number-labelling types is a numeric axis labelled as twoway labels it; `xscale(log)`/`yscale(log)` on a date variable draws a log scale in the variable's units with date labels; %tC axes are ticked and labelled exactly as twoway's; parenthesised dates with blanks are read wherever a date literal is read.

**Why one section.** The three are the date-axis decision and the date readers (`_dash_figure_date_kind`, `_dash_tc_from_tC`'s tick use, `_dash_tdate_*`), which the index gives 44-04; it is batch 44.1's JS section (the %tC conversion after a move is in `_DASH_AXIS_FINISH_JS`).

**Test order and commit rule.** Three commits `(WP-44 AX-18)`, `(WP-44 DG-6)`, `(WP-44 DG-4)`. 44-04-01 writes the extract script (all three items) and only AX-18's failing tests and block; saved failure; no commit. Each later item: failing tests saved, then fix + flips + tracking in one commit.

### Section decisions (binding on the executor)

- **D-44-04.a twoway's first-plot rule, from its measurement.** `_dash_figure_date_kind` gains: let `first` be the first plot in plot order whose layer counts on this axis (the same `on` list it builds, :1588-1590, but kept in order with the plot type); when `first["type"]` is in `_DASH_NUMBER_FIRST_TYPES = frozenset({"lfit", "qfit", "lfitci", "qfitci", "kdensity", "lpoly", "lpolyci", "scatteri", "pci", "pcarrowi", "function"})` (the fixture's `ax18.first_<type>` probes confirm each member; a type the fixture shows keeping dates is removed from the set before coding), return None. Because scatteri, pci, pcarrowi and function name no variable and are skipped by `_dash_layer_axis_names` today, the order walk reads `plots` directly (type and its `yaxis`/`xaxis`/`horizontal` options through `_dash_axis_numbers` and `_dash_is_horizontal`). A None axis is then labelled in the format the fixture's labels show (expected the variable's numbers in `%9.0g`-style text, e.g. `15000`; the axis-format rule of dash.sthlp:4700-4712 decides which variable's format applies, and a `%t` format there is NOT a date writer: the fixture decides; if twoway writes `15,000`, follow it).
- **D-44-04.b A log date axis is a numeric log axis with date labels.** When the axis has a date kind and `xscale(log)`/`yscale(log)` (or the axis-2 forms), the figure is made as for a numeric log axis (no `x_axis_type="datetime"`, the date columns kept in Stata units: the conversion to epoch milliseconds the date kind triggers is skipped for that axis), and the axis's label format is the variable's date format, through exactly the path `xlabel(, format(%td))` on a numeric axis takes today (dash.sthlp:4733-4737: "format(%td) on a numeric axis writes its numbers as dates"); the warning text is removed in both modes. Ticks: the log rule over Stata units, as the fixture's `ax18.log_*` labels show (twoway asks `_natscale` over the logged values of a log axis; 34-09's export already requests Stata's ticks for log axes -- re-read `_dash_stata_tick_requests`, :41815). After a move the finisher re-ticks the numeric log axis as any log axis; nothing date-specific runs.
- **D-44-04.c %tC ticks are converted, labels follow.** In the one tick funnel 34-09 made, `_dash_axis_count_ticks(lo, hi, n, kind=None, table=None)` (dash_render.py:41612 at `090d928`; it maps tc/tC to Stata units through `_STATA_EPOCH_UNIX_MS` before `_dash_stata_or_model`), and in `dash_axis_finish`, an axis of kind `"tC"` maps every tick value `t` (a raw %tC number, as Stata's `_tsnatscale`/`_natscale` return it over the raw column) to `_dash_tc_from_tC([t])[0]` before the epoch-millisecond conversion that places it; the %tc label writer then writes `%tC(t)` because `%tc(cofC(t)) == %tC(t)`. After a move, the model ticks a %tC axis over the RAW values: the finisher converts the kept rows' extent back with new `dash_tC_from_tc(ms)` (the inverse: add one second per leap second at or before the instant, the same 27-entry table) before natscale, then forward with `dash_tc_from_tC(v)`. Both JS functions are defined in `_DASH_AXIS_FINISH_JS` itself, in its own code right after its `_DASH_DATE_UNITS_JS + _DASH_TSNATSCALE_JS` prefix (:43010) -- NOT in `_DASH_DATE_UNITS_JS`, which is also concatenated into every date `CustomJSTransform`'s `func` and `v_func` (:2035-2036), so a function there would ride on every date column's transform (REVIEW-4 R4-29) -- with the leap table written into the code as constant numbers (no user text) and pinned equal to `_STATA_LEAP_SECONDS_TC_MS` (:675) by a test.
- **D-44-04.d Dates bound in parentheses.** New Mata `string rowvector _dash_tdate_toks(string scalar seg)`: splits `seg` at blanks outside parentheses (a depth counter; a quote has no meaning here), so `(1 jan 2001)` is one token; it replaces `tokens(seg)` in `_dash_tdate_lines` (:9512) and `tokens(...)` in `_dash_tdate_range` (:9566), and is used by the tlabel/ttick reader that calls `_dash_tdate_tok` (:9439; re-read its tokenizer). `_dash_tdate_value` (:9291): when `t` starts with `(` and ends with the matching `)`, the inner text is read with the blank added to the gate (`ok + " "`), at most 40 bytes inside, then `date(inner, "DMY")` (and the other units' functions) as today; a comma inside stays refused (DT06: twoway refuses `(july 1, 2001)`, dash already matches). `ttext()`'s position reader (:11539) inherits the rule. A parenthesised date on a numeric (non-date) axis is refused as today.

## Risk: [yellow] -- the date-axis decision is read by every figure, and the finisher's date prefix by every saved page with a date axis

**Why.** Changing `_dash_figure_date_kind` changes the axis type of every graph whose first layer is a fit or an immediate type on a date variable; the date-unit JS prefix is shared by the finisher.

**Risk factors.**
1. Tests and examples that draw `lfit close date` or `function` over a date axis pin a DatetimeAxis.
2. Skipping the millisecond conversion for a log date axis must reach every column of that axis (both bounds of a range plot, pc coordinates), or points land at Stata units on one layer and ms on another.
3. The leap-second inverse at a leap second itself (an instant inside the 61st second) must round-trip as Stata's `Cofc()`/`cofC()` do (fixture `leap.inside`, data_locale_truth.json).
4. The parenthesis-binding tokenizer must not change any token without parentheses (every taxis_truth.json probe).
5. Batch partners 44-01 (axis titles, late helper) and 44-05 (`_dash_lone_second_axes`, `_dash_axlabel_refusal`) do not touch these functions, except `_dash_add_secondary_axes`, which 44-01 also edits (a different hunk).

**Mitigation.**
1. 44-04-02 greps `test/` for `DatetimeAxis` beside `lfit|qfit|kdensity|lpoly|function|scatteri|pci` on date data and flips each with a `Flipped:` line; examples/ do-files are checked by `test_examples_run.cscript` at the batch gate.
2. The skip is taken where the axis kind is decided (one kind per axis, `_dash_mark_date_axes`), so every layer on that axis follows it; `TestLogDate::test_every_layer_in_units` covers rarea and pcspike.
3. `TestTcTicks::test_inverse_round_trip` runs every `leap.*` entry through both directions in Python and node.
4. `TestParenDates::test_old_probes_unchanged` reruns taxis_truth.json's probes through the cscript case Q4404-6.
5. 44-04 is batch 44.1's only editor of `_make_figure_body` and of the served template `_generate_app_source_body` (R12): 44-01 and 44-05 wire their helpers through `_dash_apply_axis_options` instead.

## Dependencies

- **Depends on:** none in WP-44. 34-07 (TR-4, date axes with missing end rows) and 34-09 (Stata's ticks at build) landed in WP-34 and are this section's base for `_dash_stata_ticks_gen` and the date summaries; re-read both.
- **Blocks:** none.
- **Parallel batch 44.1** with 44-01 and 44-05; merge order 44-01, 44-04, 44-05. 44-04 is the batch's only JS editor (`_DASH_AXIS_FINISH_JS`, after its date prefix).

## Evidence

Anchors at `090d928`; re-read at the WP-44 base.

```python
1588     on = [names for a, names in layers if a == axis_no]
1589     if not on and axis_no == 1:
1590         on = [names for _a, names in layers]
...
1596     if not kinds or len(kinds) > 1 or None in kinds:
1597         return None
1598     return kinds.pop()
```

```python
63443         if _x_date and _xs_log:
63444             warnings.warn(
63445                 f"dash: xscale(log) is meaningless for the date variable "
...
63449             _xs_log = False
```

```python
685 def _dash_tc_from_tC(values):
...
694     shifted = table + 1000.0 * np.arange(1, len(table) + 1)
696         k = np.searchsorted(shifted, v, side="right")
697     out = v - 1000.0 * k
```

```
9310     ok = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.+-*/@=_"
...
9512         t   = tokens(seg)
```

Help: dash.sthlp:4706-4707 (%tC "converted with Stata's own leap-second table, so timestamps are exact"), :4723-4731 (log scales on date axes), :4815-4820 (computed layers of a date; first layer scatteri/pci/pcarrowi/function). Fixtures on disk: stata_ticks_truth.json (a `TC` probe for %tc, none for %tC), taxis_truth.json (`c55`, `lit_*`; no blank inside parentheses), data_locale_truth.json `leap.*`.

### Tests that pin today's behaviour (flip, never delete)

- `grep -rn "meaningless for the date" test/` -- every test that expects the log-date warning (flip: no warning, a log axis).
- `grep -rn "Difference from twoway" test/test_help_claims_*.py | grep -i "date\|15000"` -- the help-claim pins of :4815-4820 (flip to the new sentences).
- Tests drawing a fit or immediate type first on a date variable and asserting a DatetimeAxis (found by the grep in Mitigation 1).
- Tests asserting `tline((1 jan 2001))` is refused: `grep -rn "invalid line argument\|invalid label specifier" test/*.py test/*.cscript | grep "("`.

## User stories

- **US-44-04.1** As a Stata user, I want `dash kdensity date` to label the axis 15000 to 15400 as twoway does, so the two graphs read the same.
- **US-44-04.2** As a Stata user, I want `xscale(log)` on a date axis to draw a log scale with date labels.
- **US-44-04.3** As a Stata user with %tC timestamps, I want the tick labels twoway writes, to the second.
- **US-44-04.4** As a Stata user, I want `tlabel((1 jan 2001) (1 jul 2001))` accepted, as twoway accepts it.

## Business requirements

- **BR-44-04.1** For each type the fixture marks, a first layer of that type on a date variable gives a numeric axis whose labels equal twoway's.
- **BR-44-04.2** A log date axis draws a log scale in the variable's units with the fixture's date labels; no warning.
- **BR-44-04.3** %tC tick positions and labels equal twoway's, before and after a move.
- **BR-44-04.4** Every DG-4 form twoway draws is drawn at the same dates; forms twoway refuses stay refused with its words.
- **BR-44-04.5** Saved page and served app agree.

## Technical requirements

- **TR-44-04.1** `_DASH_NUMBER_FIRST_TYPES` (module constant before `_dash_figure_date_kind`); the order walk in `_dash_figure_date_kind` (D-44-04.a); the served copy of the function travels by name (`_dash_figure_date_kind` is already copy-listed; add the constant after `"_STATA_LEAP_SECONDS_TC_MS",` at :67155).
- **TR-44-04.2** Log date axes (D-44-04.b): in `_make_figure_body` (:63443-63456) and the served template (:70318-70330) replace the warn-and-drop blocks with `_x_date, _x_logdate = _dash_log_date(_x_date, _xs_log)` (new module function returning `(None, kind)` when both are set, else `(kind, None)`); `_dash_mark_date_axes` and the column conversion skip an axis whose `_logdate` is set; the axis formatter is `_dash_date_axis_formatter`'s numeric-axis date path (the one `format(%td)` on a numeric axis uses; grep `format(%td)` handling in `_dash_apply_axis_spec`). Axis 2: the same in `_dash_add_secondary_axes` (:45636-45646, where it warns for `{n}scale2(log)`); 44-01 edits the same function in this batch (its title stamp before `fig.add_layout(ax, side)`, :45680) -- two hunks of one non-R12 function, named in both hand-backs (REVIEW-4 R4-22).
- **TR-44-04.3** %tC (D-44-04.c): Python in `_dash_axis_count_ticks` (for kind `"tC"`: the lo/hi it hands to `_dash_stata_or_model` are raw %tC -- the converted ms plus the leap seconds, `dash_tC_from_tc`'s Python twin `_dash_tC_from_tc` added beside `_dash_tc_from_tC` -- and every returned tick goes back through `_dash_tc_from_tC` before the ms conversion); JS `dash_tc_from_tC(v)` and `dash_tC_from_tc(ms)` defined in `_DASH_AXIS_FINISH_JS`'s own code after its prefix (D-44-04.c; `_DASH_DATE_UNITS_JS` is unchanged) and their use in `dash_axis_finish`'s natscale step for kind `"tC"`; a test pins the JS table to `_STATA_LEAP_SECONDS_TC_MS`, and `TestTcTicks::test_not_in_the_transforms` asserts `"dash_tC_from_tc"` is absent from `_DASH_DATE_UNITS_JS`.
- **TR-44-04.4** Mata (D-44-04.d): `_dash_tdate_toks` before `_dash_tdate_tok` (dash_parse.mata :9328), header index line beside `_dash_tdate_tok`'s (:658), `_needed` entry, program_coverage_map.py row naming `test_wp44_truth.cscript:Q4404-6`; the three call-site changes; `_dash_tdate_value`'s parenthesis branch.
- **TR-44-04.5** function_test_map.py rows: `_dash_log_date` -> `test/test_date_axes_p9.py::TestLogDate`; `_dash_tC_from_tc` -> `test/test_date_axes_p9.py::TestTcTicks` (copy-listed after `"_dash_tc_from_tC",`, :67808); `_dash_figure_date_kind` gains `test/test_date_axes_p9.py::TestNumberFirst`.
- **TR-44-04.6** Parity (R8) `CORPUS` under `# WP-44 44-04`: `"kdensity date numbers"`, `"lfit first on date numbers"`, `"function first on date numbers"`, `"xscale log on date"`, `"tC ticks"`; `MOVE_CORPUS`: `"tC ticks, dropdown"`, `"xscale log on date, dropdown"`.
- **TR-44-04.7** Help (R3): rewrite :4723-4731 (log date axes drawn), :4815-4820 (the two "Difference from twoway" sentences of the computed-layers and dates-on-every-axis paragraphs become twoway's rule; the browser-range residual sentence stays), :4706-4707 (%tC ticks and labels as twoway's); the datelist sentence of the tlabel/tline/tscale paragraphs gains the parenthesised form with an example; their Differences lines are removed. TWOWAY_COVERAGE_AUDIT.md's date-axis row.

## Boundaries

- Do not edit 34-07's end-row summaries or 34-09's `_dash_stata_tick_requests`/`_dash_stata_ticks_gen` beyond reading their output; do not edit the transform code (44-03, later batch), axis titles (44-01), the lone-axis rewrite (44-05).
- The browser-range residual (dates past years -271821/275760) stays (M11).
- 49-01 owns DG-10 (`tline()` on a %tb axis, words); this section must not change that message.

## Stata truth

New `scripts/extract_date_axis_rule_truth.do` -> `test/fixtures/date_axis_rule_truth.json` (frame of `scripts/extract_axis_look_truth.do`; per key rc, log lines, SVG tick texts and positions, `.Graph.plotregion1.xscale` min/max). Keys:
- `ax18.first_<type>`: `sysuse sp500`, for each of `lfit qfit lfitci qfitci kdensity lpoly lpolyci fpfit fpfitci lowess mspline mband histogram`: `twoway (<type> close date) (scatter close date)` (kdensity/histogram: `(<type> date) (scatter close date)`), and `(scatteri 1300 15400) (scatter close date)`, `(pci 1300 15200 1400 15300) (scatter close date)`, `(pcarrowi 1300 15200 1400 15300) (scatter close date)`, `(function y = 1300, range(15000 15400)) (scatter close date)`; `scatter_first` = `(scatter close date) (lfit close date)`; `y2_first` = `(scatter close date) (lfit open date, xaxis(2))`; `hz` = `kdensity date, horizontal`.
- `ax18.log_<k>`: `line close date, xscale(log)`; `scatter date close, yscale(log)`; `line close date, xscale(log) xlabel(#4)`; the same under %tm (`gen m = mofd(date)`, `format m %tm`).
- `dg6.*`: `T04` (%tc) and `T05` (%tC) of the audit (`clear`, `set obs 30`, `gen double t = tc(01jan2001 00:00:00) + (_n - 1) * 86400000`, `gen double tC = Cofc(t)`, `format t %tc`, `format tC %tC`, `gen y = _n`; `scatter y t` and `scatter y tC`), plus `tC_2016` around the 2016 leap second.
- `dg4.*`: `DT04` `tlabel((1 jan 2001) (1 jul 2001))`, `DT05` `tlabel(01jan2001 (1 jul 2001))`, `DT09` `tline((15 jun 2001))`, `DT20` `tscale(range((1 dec 2000) (31 jan 2002)))`, `DT06` `tlabel((july 1, 2001))` (refused), `ttext` `ttext(1300 (15 jun 2001) "x")`, on `sysuse sp500`'s `line close date`.

Run twice through `scripts/stata_slot.sh` with DASH_REPO; `git add -f`. Truth blocks in test_wp44_truth.cscript: `* ==== S04 AX-18: numbers and log on date axes ====`, `S04 DG-6`, `S04 DG-4`, gate `WP44_ONLY`/`"S04"`, helper `_q4404_reg` (as 44-01's).

## TDD test stubs

New file `test/test_date_axes_p9.py`:
- Test: number-first types give a numeric axis with twoway's labels -- ::TestNumberFirst::test_each_type[saved|served] (fails at base: DatetimeAxis); ::test_scatter_first_keeps_dates; ::test_second_axis.
- Test: log date axis -- ::TestLogDate::test_log_with_date_labels[saved|served] (fails at base: warning, linear); ::test_every_layer_in_units; ::test_move (node or parity move).
- Test: %tC ticks -- ::TestTcTicks::test_labels_equal_twoway[saved|served] (fails at base: 22 s off); ::test_inverse_round_trip (Python and node over data_locale_truth leap.*); ::test_js_table_equals_python; ::test_not_in_the_transforms.
- Test: parenthesised dates -- cscript Q4404-5 (DT04, DT05, DT09, DT20, ttext drawn; DT06 refused with twoway's line); ::TestParenDates::test_drawn_positions[saved|served] (the spec dash writes for DT04 holds 01jan2001 and 01jul2001 day numbers); Q4404-6 (taxis_truth probes unchanged).
- cscript cases: Q4404-1 (kdensity date labels 15000..), Q4404-2 (lfit first), Q4404-3 (log date), Q4404-4 (%tC labels), Q4404-5, Q4404-6.
- Flips: Evidence list. Parity: TR-44-04.6.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| first-plot rule | pytest TestNumberFirst; Q4404-1/2 | date_axis_rule_truth.json ax18.first_* | yes |
| log date axes | pytest TestLogDate; Q4404-3 | ax18.log_* | yes, and a move |
| %tC ticks | pytest TestTcTicks; node; Q4404-4 | dg6.*, data_locale_truth.json leap.* | yes, and a move |
| parenthesised dates | Q4404-5/6; pytest TestParenDates | dg4.*, taxis_truth.json | Stata side + spec |
| parity | test_mode_parity.py | -- | yes |

Acceptance criteria:
- **AC-44-04.1** Every `ax18.first_*` probe's x labels equal twoway's text in both modes; `scatter_first` keeps the date axis.
- **AC-44-04.2** Every `ax18.log_*` probe draws a LogAxis whose labels equal twoway's date texts; no warning.
- **AC-44-04.3** `dg6.T05` labels equal twoway's to the second, before and after a move; `T04` unchanged.
- **AC-44-04.4** `dg4` forms draw at twoway's dates; DT06 refused with twoway's line; every taxis_truth probe unchanged.

## Tasks

**Commit boundary.** AX-18: 44-04-01 (no commit) + 44-04-02 (commit `Label date axes with numbers or a log scale as twoway does (WP-44 AX-18)`). DG-6: 44-04-03 (no commit) + 44-04-04 (commit `Place %tC ticks in twoway's raw units (WP-44 DG-6)`). DG-4: 44-04-05 (no commit) + 44-04-06 (commit `Read parenthesised dates with blanks (WP-44 DG-4)`). 44-04-07 is the section check. Branch `wp44-s04`; `$WT` and the closing steps every closing task takes before its commit are in Notes ("Before every commit").

```xml
<task type="auto" id="44-04-01">
  <name>Measure date axes; write AX-18 failing tests</name>
  <files>scripts/extract_date_axis_rule_truth.do, test/test_date_axes_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_date_axis_rule_truth.do with every key of "Stata truth", run it twice through scripts/stata_slot.sh with DASH_REPO set, git add -f test/fixtures/date_axis_rule_truth.json (staged). From the fixture, write the final member list of _DASH_NUMBER_FIRST_TYPES into <scratch>/44-04-types.txt (a type whose first-layer probe keeps date labels is dropped). Create test/test_date_axes_p9.py with TestNumberFirst and TestLogDate and append "* ==== S04 AX-18: numbers and log on date axes ====" (Q4404-1..3). Run on the unmodified tree; save to <scratch>/44-04-01-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_date_axes_p9.py -q -n0 -> TestNumberFirst::test_each_type and TestLogDate::test_log_with_date_labels fail; Q4404-1..3 FAIL; both scratch files exist]]></verify>
  <done>The date-axis fixture exists and AX-18's tests fail on the unmodified tree.</done>
</task>

<task type="auto" id="44-04-02">
  <name>Apply twoway's date-axis rules</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[Implement D-44-04.a with the member list from <scratch>/44-04-types.txt and D-44-04.b (TR-44-04.1, .2): the constant, the order walk, _dash_log_date in both modes and on axis 2, the skipped conversion and the numeric-axis date formatter; remove the three warn-and-drop blocks (saved, served template, axis 2). Flip the pins found by the Evidence greps. Rewrite dash.sthlp:4723-4731 and the two :4815-4820 difference sentences (keep the browser-range one); update _dash_figure_date_kind's docstring (no "ratified divergence"). Parity entries in test/test_mode_parity.py. Close AX-18 (BUGS names stat:PT-20 and VF-12; GAPS4 Closed, commit pending; delete AX-18's GAPS4_OPEN line in test/test_tracking_documents.py; CHANGELOG under "### Fixed in WP-44"; TWOWAY_COVERAGE_AUDIT.md's date-axis row gains "[WP-44 AX-18: corrected -- numbers where twoway labels numbers; log date axes drawn]"); take the three closing steps for `AX-18` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `AX-18` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py AX-18`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run the AX-18 tests, test_tracking_documents.py, test_dates.py, test_date_axis_ticks.py, test_date_axis_residuals.py, test_date_units.py, test_axisn_dates.py, test_computed_layer_rows.py, the test_help_claims_*.py files that read :4723-4731 or :4815-4820, the block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_date_axes_p9.py test/test_dates.py test/test_date_axis_ticks.py test/test_date_axis_residuals.py test/test_axisn_dates.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; "Q4404-1 PASS" .. "Q4404-3 PASS"; python3 test/known_differences.py AX-18 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 AX-18)"]]></verify>
  <done>Date axes follow twoway's first-plot and log rules in both modes and AX-18 is committed.</done>
</task>

<task type="auto" id="44-04-03">
  <name>Write DG-6 failing tests</name>
  <files>test/test_date_axes_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Write TestTcTicks (test_labels_equal_twoway; test_inverse_round_trip over data_locale_truth.json leap.* in Python with a local inverse defined in the test from the table, and in node through js_runner on the JS functions dash_tc_from_tC and dash_tC_from_tc, which fail now as absent; test_js_table_equals_python) and append "* ==== S04 DG-6: %tC ticks in raw units ====" (Q4404-4). Run; save to <scratch>/44-04-03-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_date_axes_p9.py::TestTcTicks -q -n0 -> test_labels_equal_twoway fails ("20:26:40" != "20:26:18"); node tests fail (function absent); Q4404-4 FAIL]]></verify>
  <done>DG-6's regression tests fail before the fix and are saved.</done>
</task>

<task type="auto" id="44-04-04">
  <name>Convert %tC ticks before placing</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[Implement D-44-04.c (TR-44-04.3) in the Python tick placement and in _DASH_AXIS_FINISH_JS (the two functions after its date prefix; its natscale step). Add the help sentence at :4706-4707 (ticks placed and written as twoway's, leap seconds included). Parity "tC ticks" and its MOVE entry in test/test_mode_parity.py. Close DG-6 (BUGS closed form naming TestTcTicks and Q4404-4; GAPS4 Closed, commit pending; delete DG-6's GAPS4_OPEN line in test/test_tracking_documents.py; CHANGELOG Fixed; TWOWAY_COVERAGE_AUDIT.md's date-axis row gains "[WP-44 DG-6: corrected -- %tC ticks placed and labelled as twoway's]"); take the three closing steps for `DG-6` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `DG-6` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py DG-6`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run TestTcTicks, test_tracking_documents.py, test_stata_ticks.py, test_date_format_edges.py, the data-locale tests (grep -l leap test/*.py), test_mode_parity.py -k "tC" (batch tier, targeted), the block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_date_axes_p9.py::TestTcTicks test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; "Q4404-4 PASS"; python3 test/known_differences.py DG-6 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 DG-6)"]]></verify>
  <done>%tC axes are ticked and labelled as twoway's in both modes and after a move, and DG-6 is committed.</done>
</task>

<task type="auto" id="44-04-05">
  <name>Write DG-4 failing tests</name>
  <files>test/test_date_axes_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Write TestParenDates and append "* ==== S04 DG-4: parenthesised dates with blanks ====" with Q4404-5 (each dg4 form: twoway's rc and, when rc 0, dash rc 0 and the registered spec's t positions equal twoway's dates; DT06 refused with twoway's line) and Q4404-6 (every taxis_truth.json probe gives its recorded rc and positions). Run; save to <scratch>/44-04-05-failure.txt.]]></action>
  <verify><![CDATA[WP44_ONLY=S04 -> Q4404-5 FAIL lines for DT04, DT05, DT09, DT20 and ttext (refused r(198)/r(121)); Q4404-6 PASS; failure file exists]]></verify>
  <done>DG-4's regression cases fail before the fix and the old probes are pinned.</done>
</task>

<task type="auto" id="44-04-06">
  <name>Bind parentheses in date lists</name>
  <files>dash_parse.mata, dash.ado, dash.sthlp</files>
  <action><![CDATA[Implement D-44-04.d (TR-44-04.4): _dash_tdate_toks, the three call sites, the parenthesis branch of _dash_tdate_value; header index, _needed entry and the test/program_coverage_map.py row. Flip the refusal pins the Evidence grep finds. Add the parenthesised example to the datelist sentences of the tlabel/tline/tscale help in dash.sthlp. CHANGELOG under "### Changed behaviour (may need your do-files changed)" (a refused form is now accepted). Close DG-4 (BUGS closed form naming TestParenDates and Q4404-5; GAPS4 Closed, commit pending; delete DG-4's GAPS4_OPEN line in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's date-axis row gains "[WP-44 DG-4: corrected -- parenthesised dates with blanks read in tlabel(), tline() and tscale()]"); take the three closing steps for `DG-4` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `DG-4` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py DG-4`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run the block, test_parser.cscript and test_option_validation.cscript through stata_slot.sh, test_program_coverage_map.py, test_cscript_hygiene.py, test_tracking_documents.py, TestParenDates; commit.]]></action>
  <verify><![CDATA[WP44_ONLY=S04 -> "Q4404-5 PASS", "Q4404-6 PASS"; both area cscripts -> ALL CHECKS PASSED; python3 -m pytest test/test_date_axes_p9.py::TestParenDates test/test_program_coverage_map.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; python3 test/known_differences.py DG-4 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 DG-4)"]]></verify>
  <done>Parenthesised dates with blanks are read in every date list and DG-4 is committed.</done>
</task>

<task type="auto" id="44-04-07">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run the section's tests, the S04 blocks, test_mode_parity.py -k "44-04", test_help_conformance.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_tracking_documents.py and test_examples_run.cscript through stata_slot.sh (examples draw date axes); grep the three commit messages for claude|anthropic. Write <scratch>/44-04-handback.txt naming the lines a merger may conflict on: _dash_add_secondary_axes (44-01 stamps its title options there).]]></action>
  <verify><![CDATA[all pass; grep count 0]]></verify>
  <done>The three commits are green together.</done>
</task>
```

## Section completion criteria

- Three commits `(WP-44 AX-18)`, `(WP-44 DG-6)`, `(WP-44 DG-4)` with failure texts, flips, tracking edits and the three closing steps (Notes: plain rows of scripts/corpus/ledger.tsv removed, corpus_ledger.json regenerated; `python3 test/known_differences.py <id>` printing no row and every table's `test_every_known_difference_is_open` green; S09's Q3309-1 PASS, the guard fixture regenerated and committed with the item whenever Q3309-1 reported a change); `date_axis_rule_truth.json` committed and named.
- Q4404-1..6 pass; parity and move entries agree.

## Notes

- **Traps.** (1) The first-plot walk must use plot ORDER, not the set of names: `(scatter close date) (lfit close date)` keeps dates. (2) Under `horizontal` a kdensity's variable is on y; the walk reads the axis through `_dash_is_horizontal` exactly as `_dash_layer_axis_names` does. (3) For a log date axis the hover still writes dates: the hover formatter reads the variable's format, not the axis kind -- check `_dash_hover_text_column` is unchanged. (4) `dash_tC_from_tc` must add a leap second only once the instant is reached (`>=` on the shifted table), mirroring `searchsorted(..., side="right")`. (5) `_dash_tdate_toks` must keep `td(1jan2001)`-style pseudo-functions as one token (its parentheses bind too) and must not merge two dates separated by a blank outside parentheses.
- **Help paragraphs this section owns (R3):** dash.sthlp:4700-4712's %tC sentence, :4723-4731, :4800-4820's two difference sentences, the datelist sentences of tlabel/tline/tscale.
- **Merge rules touched:** R1, R2, R3, R5, R6 (one Mata function), R8, R9, R11/R12 (`_DASH_AXIS_FINISH_JS`, its own code after the date prefix: batch 44.1's only JS section; batch 44.1's only editor of `_make_figure_body` and the served template).
- **Owns beyond the manifest's cell (for the orchestrator; REVIEW-4 R4-21/R4-22):** `_make_figure_body` and `ServerAppBuilder._generate_app_source_body` (the log-date blocks; the cell already names this section their sole 44.1 editor), `_dash_add_secondary_axes` (axis-2 log warning; 44-01 edits another hunk), `_dash_axis_count_ticks`, `_dash_mark_date_axes`, `_DASH_AXIS_FINISH_JS`.
- **Before every commit (BRIEF; CLAUDE.md rules 4 and 6; R13).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp44-s04` (BRIEF "Pull form"): every path and command below runs in it. Every closing task (44-04-02, 44-04-04, 44-04-06) takes **the three closing steps** after its tracking edits and before its commit, in this order, whether the item closes `Closed` or `Documented` (BRIEF "The corpus ledger and the known-differences tables" (1)-(3); D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c; A-10): **(1) the ledger step** -- delete every row of `scripts/corpus/ledger.tsv` whose `gaps4_id` is the item's plain lead id (`AX-18`, `DG-6`, `DG-4`), keep every `<id> (documented)` and `<id> (residual)` row, run `python3 scripts/corpus/ledger.py` (no `--run`: the fixture's `_meta` is kept), `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py test/test_tracking_documents.py -q -n0` in the task's verify; **(2) the known-differences step** -- run `python3 test/known_differences.py <lead id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints (a `*_KNOWN` row whose value is exactly the lead id; `(documented)` and `(residual)` rows are not printed and stay), except that a difference the item's ruling keeps moves into that table's deliberate dict -- the companion dict 33-10 names for it: `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN` (`SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py, `BY_POSITION_DELIBERATE` in test/test_by_text.py, `BY_TYPES_DELIBERATE` in test/test_by_types.py, `STAT_COMBOS_DELIBERATE` in test/test_statistical_truth.py, `COLORVAR_DELIBERATE` in test/test_colorvar_truth.py) -- written `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (none is expected here: every item closes `Closed` and no ruling keeps a difference of AX-18, DG-6 or DG-4; a row the executor would keep without a ruling id is reported to the orchestrator, not moved); then run the hygiene command it prints (`python3 -m pytest <the files defining test_every_known_difference_is_open> -q -n0 -k every_known_difference_is_open`) in the task's verify; **(3) the guard step** -- run block S09 of test/test_wp33_truth.cscript alone (`WP33_ONLY=S09`, BRIEF's two-line driver with `<repo>` = `$WT`); if 33-09's guard check Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script (`DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`), `git add -f` it, rerun S09 to its `Q3309-1 PASS` and commit it with the item (body line `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`). Then, before the commit: (4) `cd $WT && git pull --ff-only . main` (BRIEF "Pull form"; CLAUDE.md rule 4; a no-op when the batch base already contains main -- if it refuses because main moved, stop and report to the orchestrator, never make a merge commit). (5) Run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is re-run) and report HIGH/CRITICAL or UNKNOWN risk in the hand-back. (6) Grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_date_axes_p9.py::TestNumberFirst::test_each_type -- failed at <base sha> with <text>`; `Flipped: <node> -- a date axis there was wrong because twoway labels the axis with the variable's numbers`; `Fixture: test/fixtures/date_axis_rule_truth.json (scripts/extract_date_axis_rule_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (every commit; plus `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` when Q3309-1 reported a change); `BUGS.md: "<title>" (closed)`; `GAPS4: AX-18 Tracked`.
