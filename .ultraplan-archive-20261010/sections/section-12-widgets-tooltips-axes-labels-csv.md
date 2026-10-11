# Section 12: Widgets, tooltips, date axes, marker labels, CSV

> Part of: WP-28 · Gaps: E3, G6 · Risk: red · Batch: 3 · Depends on: 03, 04, 14, 16, 17 · Blocks: 19 · Tasks: 15, 1 commit (E3, G6)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **3** · Depends on **03, 04, 14, 16, 17** · Blocks **19** · Risk **red** · Commits: ONE commit closing E3 and G6 together (one code path closes both), subject ending `(GAPS2 E3, G6)`; two BUGS.md entries; two CHANGELOG markers replaced, both in `Results that change`

- D4: builds on S14's `_dash_build_hover`/`_dash_hover_row` signatures (value labels), S16's colour-key label site (`_dash_colorvar_bins`) and S17's dropdown VALUES and `groups`; all three are on the tree when this section starts (batch 2); S17 owns dash.sthlp 1109-1138 and this section only verifies the sentence it wrote there.
- D10: the E3 `%tm` axis-label truth is the probe pair `e3_tm_axis` / `e3_tm_axis_lab` in S14's `axis_truth.json` (group `b1_label`; ticks 492 495 498 501, texts `2001m1 2001m4 2001m7 2001m10`); this section consumes it by those ids and fails, never skips, when they are absent.
- Q26: dropdown labels are deduplicated by display text — two values with one display text become ONE entry (S17's `groups` mechanism; this section forms the groups by label), and the mask matches every value of the group, in both modes.
- Stubs: period sliders on empty and single-value columns; a `%tC` tooltip keeps its time; 12345.67 under `%10.0g`; two values with one label.
- D7: split 12-01 (now 12-01, 12-02) and the old 12-06 (now 12-07, 12-08, 12-09); the old 12-04/12-05 hidden fourth files moved into the flip tasks 12-11, 12-13, 12-14.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

Every place a value becomes page text outside a KPI card ignores the variable's Stata
display format. GAPS2 E3 measured it: "a %td dropdown lists `2001-12-31 00:00:00`, and a
%9.0fc dropdown lists `3799`. … date sliders show `%d %b %Y` and step span/100 days for
every kind, so %tm/%tq/%ty sliders stop mid-period. A numeric RangeSlider shows `0[.]00`.
Tooltips use `{%F}` for every kind except tc, so %tC loses its time. … Date axes use one
DatetimeTickFormatter per kind, so a %tm axis reads `Jan 2000` where twoway shows
`2000m1`." GAPS2 G6 adds: "A float 0.1 shows as 0.10000000149011612 in marker labels and
dropdowns. Tooltips use BokehJS's basic formatter, so 12345.67 becomes 1.235e+4", and
`mlabformat(%9.3g)` is named and not applied. Report B §1.3 lists the fourteen sites;
section 11 took the three card rows; this section takes the other eleven: dropdown
labels, slider labels, tooltips, date-axis ticks, numeric axis `format()`, marker labels
and `mlabformat()`, by() panel titles, the CSV, and the colorvar key's number labels.

After this section each of those sites writes its text through section 04's writer with
the variable's full display format — `%8.0gc` on a dropdown, `2001m1` on a %tm axis tick,
`09jan2002` in a tooltip, `%tdCCYY-NN-DD` honoured wherever the variable's picture is —
in the saved page (JavaScript, through `CustomJSTickFormatter` and `CustomJSHover`
carrying the format in `args`) and in the served app (the same functions, copied). The
five period kinds (%tw %tm %tq %th %ty) get a numeric slider over Stata's period number
with step 1, and both masks convert the column the same way. Two dropdown values that
share one display text become one entry that selects both (Q26). A float-stored variable
writes its float32 digits in the CSV. Dates in the CSV stay ISO 8601 as dash.sthlp:862-866
documents (§Notes).

One code path closes both gaps (the writer at every site), so E3 and G6 share ONE commit
whose subject names both, `… (GAPS2 E3, G6)`, and BUGS.md gets two closed entries.

**Test order (CLAUDE.md rule 7) and commit rule (D1): tasks 12-01 and 12-02 write every
regression test for this section**, run them against the tree as batch 2 leaves it and save
the failure texts to `<scratch>/12-01-failure.txt` and `<scratch>/12-02-failure.txt` --
they do not commit (a red tree is never committed, rule 4); 12-03 to 12-10 turn the sites
green one at a time; 12-11 to 12-14 flip the pinned tests; 12-15 closes E3 and G6 and
makes the section's ONE commit, whose body opens with the saved failure texts (Q24; S01
TR-01.9). The failing tests land in that commit, never alone.

## Risk: [red] — eleven sites in two renderers, three of them rewritten by sections 14, 16 and 17 in batch 2, and five widget/mask changes that alter which rows a filter keeps

**Why.** Each site has a saved and a served entry point; the widget change alters the
value space a slider works in (period numbers instead of milliseconds), which the masks,
the exclusion rule and the CSV button all read.

**Risk factors.** (1) `_dash_filter_widget`, `_DASH_FILTER_MASK_JS` and
`_dash_frame_filter_mask` were rewritten by section 17 (dropdown values, `numeric`,
`groups`, per-target `use`) in batch 2; this section edits the slider/range branches and
the label closure of the merged text. (2) `_apply_colorvar` was rewritten by section 16
(`_dash_colorvar_bins`) and its labelset lookup by section 14 (`_dash_value_labels_for`);
this section's colorvar edit is four expressions in the merged text. (3) A
`CustomJSTickFormatter`/`CustomJSHover` per axis, slider and field would embed the
writer many times per page. (4) Bokeh models cannot be shared across served sessions.
(5) A tooltip field with `{custom}` fails `test_label_sinks.py`'s field pattern.

**Mitigation.** (1) and (2) This section runs in batch 3 on the merged batch-2 tree; every
edit is named by symbol and by the merged signature (TR-12.2, TR-12.4, TR-12.5, TR-12.9),
never by a 91d97be line inside a rewritten region. (3) One formatter model per distinct
`(format, kind, storage)` triple, cached per document. (4) The cache is a dict created
inside `make_document`. (5) The pattern is widened deliberately and a test asserts every
`{custom}` field has a formatter whose `args` carry the format.

## Dependencies

- Depends on: section 04 (the writer, `_DASH_FMT_JS`, `dash_stata_value_of`,
  `self.formats`/`_FORMATS`, `storage_types`/`_storage_types`, `format_truth.json`);
  section 03 (`test/js_runner.py`: `JsSession` for the one-move card/graph case,
  `mask_parity(df, filter_specs, widget_values)` for the period-slider and grouped-label
  mask cases, `run_js` for the node checks); section 14 (`_dash_hover_row(…, text_col=None)`
  and `_dash_build_hover(…, layers=None, value_labels=None, value_label_names=None)`,
  `_dash_apply_axis_spec(…, value_labels=None)`, `_dash_value_labels_for`, the
  `e3_tm_axis`/`e3_tm_axis_lab` probes of `axis_truth.json`); section 16
  (`_dash_colorvar_bins(col_vals, cuts, discrete, label_of)` and `label_of`'s fallback);
  section 17 (dropdown option values -- `rv` is a float for a numeric column and exact
  text otherwise -- the spec keys `numeric` and `groups`, the served `_dash_groups` map,
  the per-target `use` args, and the mask rule that keeps a row whose number equals any
  member of the selected group).
- Blocks: section 19.
- Parallel batch: 3. Can run with: 11, 15, 18. Merge order inside batch 3: S18, S15, S11,
  S12 -- this section merges LAST; S18's `_dash_apply_axis_spec` hunks (the `norescale`
  and hull hooks) are disjoint from this section's `format()` branch, and S11 edits no
  function this section touches.
- Why: this section's tasks run in batch 3 on the merged batch-2 tree, so every "if
  section 17's/16's diff has landed" of the earlier draft is unconditional: the merged
  signatures below are what the executor finds.

## Evidence

Anchors are at `91d97be`; sections 14, 16 and 17 (batch 2) rewrote the hover, colorvar and
widget regions, so the signatures this section finds on the tree are the ones stated in
TR-12.2, TR-12.4, TR-12.5 and TR-12.9; locate every site by symbol.

### Dropdown labels — `_dash_filter_widget`, dash_render.py:17593-17618

```python
17595        date_text = ({_dash_option_value(d): str(d)
17596                      for d in series.dropna().unique()}
17597                     if is_date else {})
17598
17599        def _label(rv):
17600            if rv in date_text:
17601                return date_text[rv]
17602            if rv in vlabels:
17603                return vlabels[rv]
...
17609            return rv
```

`str(d)` of a Timestamp is `2001-12-31 00:00:00`; a number without a value label is its
option text (`0.10000000149011612`, `5e-05`). The option **value** (`rv`) is section 17's:
after batch 2 it is a float for a numeric column and the exact text otherwise (S17
TR-17.2), a numeric entry's value is its group's first value, the saved spec entry carries
`"groups": [[value, member, ...], ...]` and the served widget a `_dash_groups = {value:
(members,)}` map, and both masks keep a row whose number equals any member of the selected
group -- the pandas mask is `_dash_dropdown_mask(column, value, groups=None)` and the JS rule is
`members.includes(Number(col[i]))` (S17 ships groups of one and `mask_parity`'s
`test_two_values_sharing_a_label_select_both`). The signature (:17547-17548) takes `date_kind` only; both
callers (saved `_build_filter_widgets`; served :26703-26706) pass no format.

### Slider labels and steps — :17637-17663

```python
17641    if is_date and _is_clock_kind(date_kind):
17643        step = _clock_slider_step_ms(vmin, vmax)
17644        w = (DatetimeRangeSlider(title=title, start=vmin, end=vmax,
17645                                 value=(vmin, vmax), step=step)
...
17649    elif is_date:
17650        step = _date_slider_step_days(vmin, vmax)
17651        w = (DateRangeSlider(title=title, start=vmin, end=vmax,
...
17658        step = _whole_number_step(arr, vmax - vmin)
17659        w = (RangeSlider(title=title, start=vmin, end=vmax,
```

Bokeh's defaults label them `0[.]00`, `%d %b %Y`, `DatetimeTickFormatter()` (:17648).
`RangeSlider.format` and `DateRangeSlider.format` accept a `CustomJSTickFormatter`;
BokehJS calls `format.compute(value)` with `ticks=[value]`, `index=0` (report W §1e).
The existing branch (:17627-17638) returns a disabled widget for an empty column and
widens `vmin == vmax` by one; the period branch must keep both behaviours (F-20). The
masks: `_dash_frame_filter_mask` range/slider branches (:13989-14008) compare
`_dash_float_values(df[wvar])` (epoch ms for a date) with the widget's value; the JS twin
(:14141-14160) compares `col[i]` with `w.value`. The filter spec JSON (:23707-23714)
carries `varname`, `type`, `sentinel` (and, after section 17, `numeric` and `groups`);
the served callback reads widgets' `_dash_var`, `_dash_exclude` (:26719-26720).

### Tooltips — `_dash_hover_row`, :19795-19808

```python
19802    if date_kind:
19803        spec = (f"@{{{col}}}{{%F %T}}" if date_kind == "tc"
19804                else f"@{{{col}}}{{%F}}")
19805        return (label, spec), f"@{{{col}}}"
19806    pattern = _stata_numeric_pattern(numeric_fmt) if numeric_fmt else None
19807    spec = f"@{{{col}}}{{{pattern}}}" if pattern else f"@{{{col}}}"
```

`_dash_build_hover` (:19839, saved call :22348, served :26451) builds the one HoverTool
with `formatters={"@{col}": "datetime"}` for date fields; a `CustomJSHover` in
`formatters` with a `@{col}{custom}` field receives `value` (epoch ms for a date column),
`format` and its `args` (W §1d). After section 14 (batch 2) `_dash_hover_row` carries
`text_col=None` (a value-labelled `hover()` variable's derived column `__dash_hover_<var>`,
tested first and never formatted) and `_dash_build_hover` carries `layers=None,
value_labels=None, value_label_names=None`. The fallback for computed columns is
`_tooltip_precision` (:260, used at :20026-20051) — not a variable, stays.
`test_label_sinks.py:855-857` pins the fields:

```python
_PLACEHOLDER = r"@\{[^\W\d]\w*\}(?:\{[0-9.,%FT ]+\})?"
```

### Date-axis ticks — saved :22029-22034, served :26198-26200

```python
22031        for _axis, _kind in ((fig.xaxis, _x_date), (fig.yaxis, _y_date)):
22032            if _kind:
22033                _axis.formatter = _datetime_formatter_for(_kind)
```

`_datetime_formatter_for` (:335-356) is one `DatetimeTickFormatter` per kind. A
`CustomJSTickFormatter` on a datetime axis receives `tick` as epoch milliseconds (W §1c);
`_dash_apply_axis_spec` already uses one with `args` for `xlabel(1 "text")` overrides
(:16786-16796) and sets `NumeralTickFormatter` for an explicit `format()` when
`_stata_numeric_pattern` gives a pattern (:16800-16810) — `%f` only. Section 14 gave
`_dash_apply_axis_spec` its `value_labels=None` keyword and section 18 (merged before this
section in batch 3) its `norescale`/hull hooks; neither touches the `format()` branch.

### Marker labels — `GlyphMapper._apply_mlabel_opts`, :6732-6765; `_mlabformat_column`, :6904-6971

```python
6754                elif _kind:
6755                    rendered = self._mlabel_date_texts(raw, _miss, _kind)
6756                elif _numfmt:
6757                    rendered = ["." if m else
6758                                _format_stata_numeric(v, _numfmt).strip()
6759                                for v, m in zip(raw, _miss)]
6760                else:
6761                    rendered = ["." if m else v
6762                                for v, m in zip(raw, _miss)]
```

Section 04 routed `_format_stata_numeric` through the writer, so the `_numfmt` branch
already writes Stata's text; the date branch uses `_mlabel_date_texts` (:6879-6902) and
`_format_date_value_standalone`'s fixed pictures; a variable with no format draws the raw
number (`0.10000000149011612` for a float). `_mlabformat_column` gates on
`_parse_stata_numeric_fmt` (:6950-6956) and names `%g`: "mlabformat(%9.3g) is not a
display format dash reproduces" (`test_mode_parity.py:1444`). Value-labelled variables
keep `_mlabel_number_text`'s `%18.0g` rule (:7033), measured from twoway — unchanged.
Section 07 renamed the derived columns `__dash_mlabel_*` (batch 1).

### by() panel titles — `_dash_facet_label`, :15549-15615

```python
15599        _kind = date_vars.get(var)
15600        if _kind and date_formatter is not None:
15601            parts.append(date_formatter(val, _kind))
```

with `_dash_stata_date_text(value, kind)` (:15618-15645) in both modes (saved :21754
`_format_date_value`; served :26547-26550). `numeric_formats` is "accepted and not read".
Section 14 replaced its labelset lookup (15601-15607) with `_dash_value_labels_for`.

### CSV — `_DASH_CSV_JS`, :14012-14076; `_dash_csv_meta`, :13880; `_dash_csv_payload`, :13920

```js
14017 function dash_csv_number(v) {
14018     return Object.is(v, -0) ? "0" : String(v);
14019 }
```

Both modes write the file in the browser from JSON numbers (`_dash_csv_payload` sends
floats), so `String(v)` of a float-stored 0.1 is `0.10000000149011612`. `dash_csv_date`
writes ISO 8601 — the documented contract (dash.sthlp:862-866: "a date is written in ISO
8601 … a number is written as the shortest decimal that reads back as the same number").
`test_export.py::TestTheCsvFormatter::test_a_number_is_javascripts_shortest_spelling`
(:166-171) pins `1e-7`, `123456789012`, `1e+21`. Section 14 replaced `_dash_csv_meta`'s
labelset lookup (13909-13912) with `_dash_value_labels_for`.

### colorvar key labels — `_apply_colorvar`, :6407-6420 and :6467-6488 at 91d97be

```python
6418            return vlabels.get(key, f"{v:g}")
...
6467                        if lo_b is None:
6468                            labels.append(f"≤{hi_b:g}")
```

Python's `:g` (six significant digits). Section 16 (batch 2) rewrote 6459-6498 into
`_dash_colorvar_bins(col_vals, cuts, discrete, label_of)`, so on the tree the number text
lives in `label_of`'s `f"{v:g}"` fallback and the three interval labels (`≤c1`, `c1–c2`,
`>ck`) inside `_dash_colorvar_bins`; those four expressions are this section's edit.

### Stata's rules

Report D §8b (dates, default pictures, codes) and §8a (numeric) as section 04 cites them;
the writer is section 04's and the truth is `format_truth.json`. For the period kinds
Stata's slider analogue is the period number itself (`%tm` 480 is 2000m1; the fixture's
`date_formats` rows give each number's text). twoway labels a date axis in the variable's
format (GAPS2 G10; dash.sthlp:2361 "On a date axis a number is a date in the variable's
own units"); its drawn tick text for a `%tm` variable is recorded by section 14's probes
`e3_tm_axis` (`twoway line close m` on sp500's `m = mofd(date)`, `format m %tm`) and
`e3_tm_axis_lab` (the same with `xlabel(492(3)501, format(%tm))`, ticks 492 495 498 501,
texts `2001m1 2001m4 2001m7 2001m10`) in group `b1_label` of `test/fixtures/axis_truth.json`.

### Tests that pin today's behaviour (flip, never delete)

- Dropdown: `test/test_saved_filter_layers.py::TestADateDropdown::test_the_option_labels_still_read_as_dates`
  (:1212-1216, `"2001-12-31 00:00:00"`) → `31dec2001`.
- Sliders: `test/test_filter_slider_step.py::…::test_the_step_is_a_whole_number_of_days[tw|tm|tq|th]`
  (:180-196, asserts `DateRangeSlider`) and `::test_a_long_monthly_series_is_not_stepped_one_day_at_a_time`
  (:198-215, `%tm` → `DateRangeSlider`, step 36 days) → a `RangeSlider` over period
  numbers with step 1; the `td` case stays. `test/test_filter_widget_data.py`
  `_SAVED_DATE_TYPE` (:109) stays (its variable is `%td`) and gains a `%tm` row.
  `test/test_dates.py:556-582, 715-728` and `test/test_date_range.py:520-535` use `%td`
  → stay.
- Tooltips: `test/test_date_range.py:609` (`("date", "@{date}{%F}")`),
  `test/test_served_dates.py:129, 229`, `test/test_help_claims_4.py:1706` → `@{date}{custom}`
  with a `CustomJSHover` whose `args["fmt"] == "%td"`; `test/test_label_sinks.py:855-857`
  `_PLACEHOLDER` → widened; `test/test_server_layer_defects.py::TestTheHoverBuilder`
  (:1187-1200) calls the row helper by keyword → updated to the merged signature (12-11).
- Date axis: `test/test_dates.py::TestDatetimeAxis::test_a_date_x_variable_gets_a_datetime_axis`
  (named by `function_test_map.py` for `_datetime_formatter_for`) → asserts a
  `CustomJSTickFormatter` whose node output for a tick equals the fixture text.
- Numeric axis: `test/test_axis_options.py::…::test_format_suboption_reaches_the_tick_labels`
  and `::test_format_with_explicit_ticks_together` (:176-190, `NumeralTickFormatter`,
  `","` in `fmt.format`) → `CustomJSTickFormatter` with `args["fmt"] == "%9.0fc"` and node
  output `4,099` for 4099; `test/test_help_claims_7.py:255-262` reads `fmt.format` when
  `NumeralTickFormatter` else the type name → reads `args["fmt"]` (12-13);
  `test/test_adversarial_matrix.py::…::test_an_axis_format_with_a_billion_decimals_is_bounded`
  (:1678-1687) stays (the bound now lives in `_dash_fmt_parse`; the warning still fires).
- Marker labels: `test/test_date_range.py:476-478` `_LABELS` and :790-860 (`"02 Jan 2001"`,
  `"31 Dec 9999"`, `"28 Nov 2001"`) → `02jan2001`, `31dec9999`, `28nov2001`;
  `test/test_help_claims_5.py::TestADateVariablesLabels` (:1110-1130, `"03 Jan 2000"`,
  and `test_mlabformat_is_named_and_the_dates_kept_in_both_modes` keeps its note — a
  numeric `mlabformat` on a date variable stays named, §Boundaries);
  `test/test_twoway_option_parity.py::test_mlabformat_on_a_date_variable_is_named_and_the_dates_kept`
  (:619-635, `"16 Jan 2020"`) → `16jan2020`;
  `test/test_twoway_option_parity.py::test_a_format_dash_does_not_reproduce_is_named[%9.3g]`
  (:592-602) → `%9.3g` is honoured (drop it from the parametrisation and add a positive
  case; `abc`, `%td`, `%12s` stay named); `test/test_mode_parity.py::_MUST_WARN` entry
  "a format mlabformat() cannot reproduce" (:1444) → this section (the one whose gap
  silences it) changes its CORPUS case's format to `%12s` and the expected message to
  `dash: mlabformat(%12s) is not a display format dash reproduces`; the key is kept
  (`test_mode_parity.py:1608-1611` requires every key to name a corpus case).
- Facet titles: `test/test_help_claims_5.py:519-522` (`"01 Jan 2000"` both modes),
  `::TestTheFacetLabelHelper::test_a_date_goes_through_the_formatter` (:565-573),
  `::TestTheStataDateText::test_each` (:580-591) → `01jan2000`, `2000m1`, `2000`,
  `01jan2000 00:00:00`; `test/test_date_range.py:582, 652` (`"02 Jan 2001"`, `"31 Dec
  9999"`) → `02jan2001`, `31dec9999`; `test/test_served_dates.py::…::test_a_by_graph_over_dates`
  (:207) likewise.
- Dates test: `test/test_date_range.py::…::test_the_date_formatter` (:944-961) and
  `::test_the_date_formatter_writes_a_number_past_the_range_as_itself` pin
  `_format_date_value_standalone` → rewritten against `_dash_stata_date_text(value,
  fmt)` for each of `%td`, `%tc`, `%tC`, `%tw`, `%tm`, `%tq`, `%th`, `%ty` with Stata's
  text from `format_truth.json`'s `date_formats` rows and `.` for missing;
  `test/test_help_claims_5.py::TestTheStataDateText` likewise.
- CSV: `test/test_export.py::TestTheCsvFormatter::test_a_number_is_javascripts_shortest_spelling`
  (:166-171) → `dash_csv_number(v, storage)` with the same double cases plus float cases;
  `::test_csv_meta` (:548) → the meta gains `storage`.
- Colorvar: `test/test_colorvar_legend.py` assertions on `:g` labels, if any (grep
  `labels` there) → the variable's format; section 16 (batch 2, on the tree) already
  re-pinned its own key labels, so only the number text changes here.
- `test/test_dates.py::TestNumericDisplayFormats::test_a_bokeh_tick_pattern_is_produced`
  (:480) and `::test_a_format_dash_does_not_reproduce_returns_none` (:488) and
  `test/test_adversarial_matrix.py::TestNumericFormatBounds::test_the_formats_stata_accepts_still_parse`
  (:1675) pin `_stata_numeric_pattern`/`_parse_stata_numeric_fmt` → rewritten against
  `_dash_fmt_parse`/`_dash_fmt_kind` when those two are retired (task 12-09; flipped in
  12-13).

## User stories

- **US-12.1** As a dashboard viewer, I want a dropdown over a `%td` variable to list
  `31dec2001` and one over auto's price to list `4,099`, so the widget reads as the data
  does in Stata.
- **US-12.2** As a dashboard viewer, I want a `%tm` range slider to step one month at a
  time and read `2000m1 .. 2019m12`, so I never stop mid-period.
- **US-12.3** As a dashboard viewer, I want a tooltip over a `%tc` or `%tC` variable to
  show its time and one over `%8.0gc` price to show `4,099`, in both modes.
- **US-12.4** As a Stata user, I want a `%tm` axis to read `2001m1` where twoway does, and
  `xlabel(, format(%9.0fc))` to draw `4,099`, in both modes.
- **US-12.5** As a Stata user, I want marker labels, `mlabformat(%9.3g)` and by() panel
  titles of a date variable written as Stata writes them, and a float-stored 0.1 labelled
  `.1`, not `0.10000000149011612`.
- **US-12.6** As a dashboard viewer downloading the CSV, I want a float-stored variable
  written with its float32 digits (`0.1`), so the file reads as Stata's data does.
- **US-12.7** As a dashboard viewer, I want a dropdown over a variable whose format shows
  two values as one text (`1.2` and `1.4` under `%9.0f`) to list that text once and select
  both rows, so the widget never lists two identical labels.

## Business requirements

- **BR-12.1** A dropdown's option labels are the variable's value labels where they exist,
  else Stata's `display` text for the variable's format; the option values are unchanged;
  values that share one display text are listed once, as one entry that selects every row
  carrying any of them, in both modes (the format decides the grouping, Q26).
- **BR-12.2** A slider or range slider's labels are Stata's `display` text for the
  variable's format; a `%tw/%tm/%tq/%th/%ty` slider moves over Stata's period numbers in
  steps of 1 and keeps exactly the rows whose period number is within its bounds; a
  `%td`/`%tc`/`%tC` slider is unchanged in behaviour and labelled in the variable's format;
  an all-missing period column gives the disabled widget and a single value the widened
  one, as today's branches do.
- **BR-12.3** A tooltip row for a variable shows Stata's `display` text for its format (a
  `%tC` variable keeps its time; 12345.67 under `%10.0g` reads `12345.67`); computed
  columns keep their spread-based precision.
- **BR-12.4** A date axis's tick labels are Stata's `display` text for the variable's
  format at each tick, as twoway draws them (`2001m1 2001m4 2001m7 2001m10` on the sp500
  probe); an explicit `format()` on a numeric axis is honoured for every writable format.
- **BR-12.5** Marker labels of a variable without value labels are Stata's `display` text
  for its format (a date in its picture, a float without expansion); `mlabformat()` is
  honoured for every writable format; a missing value is `.`.
- **BR-12.6** A by() panel of a date variable is titled with Stata's `display` text for
  the variable's format.
- **BR-12.7** The CSV writes a float-stored number as the shortest decimal that reads back
  as the same float32; a double is unchanged; dates stay ISO 8601.
- **BR-12.8** The colorvar key's number labels use the variable's display format.
- **BR-12.9** All of the above hold identically in the saved page and the served app, and
  the saved page's text after a filter move equals its text before.
- **BR-12.10** Every changed text is listed in CHANGELOG "Results that change".

## Technical requirements

- **TR-12.1 Formatter models, cached.** Two module-level functions, added to the function
  copy list (24466-24687) immediately after `"_dash_hover_row"` (24539) and to
  `function_test_map.py`: `_dash_fmt_tick_formatter(fmt, kind, storage, cache)` returning a
  `CustomJSTickFormatter(code=_DASH_FMT_JS + "\nreturn dash_fmt_text(kind ?
  dash_stata_value_of(tick, kind) : tick, fmt, storage);", args={"fmt": fmt or "%9.0g",
  "kind": kind or "", "storage": storage or ""})` and `_dash_fmt_hover(fmt, kind,
  storage, cache)` returning the same as a `CustomJSHover` over `value`. `cache` is a
  dict keyed by `(fmt, kind, storage)`; the saved renderer holds `self._fmt_models = {}`
  per render, the served template creates `_fmt_cache = {}` inside `make_document` (a
  Bokeh model belongs to one document). The format is always in `args`, never in `code`.
- **TR-12.2 Dropdown labels and groups.** `_dash_filter_widget(ftype, varname, column,
  title, value_labels=None, date_kind="", max_options=None, fmt="", storage="")` (the
  new keywords appended after section 17's): `_label(rv)` returns `vlabels[rv]` when
  present, else for a date `_dash_fmt_text(_dash_stata_value_of(ms, date_kind), fmt)`,
  else `_dash_fmt_text(float(rv), fmt or "%9.0g", storage)` when `rv` is a number, else
  `rv`. `rv` is section 17's option value: a float for a numeric column and exact text
  otherwise (S17 TR-17.2), never a string to parse. Groups (Q26): section 17 owns the
  mechanism (a numeric entry's value is its group's first value; the saved spec entry
  carries `"groups": [[value, member, ...], ...]`, the served widget `_dash_groups =
  {value: (members,)}`, and both masks -- `_dash_dropdown_mask(column, value, groups=None)`
  and the JS rule `members.includes(Number(col[i]))` -- keep a row whose number equals any
  member of the selected group, NaN never); this section forms the groups by label: the distinct values
  are labelled with `_label`, values sharing one label form one group listed once (in
  ascending order of the first member), the entry's value is the first member and its
  label the shared text, no suffixes. A value-labelled variable groups by its labels the
  same way (two codes with one label form one group). Both callers pass
  `fmt=formats.get(var, "")` (saved `self.formats`, served `_FORMATS`) and
  `storage=storage_types.get(var, "")`. The option value's form is untouched (section 17).
- **TR-12.3 Sliders.** Numeric and `%td`/clock sliders keep their widget classes and
  steps and gain `format=_dash_fmt_tick_formatter(fmt, kind, storage, cache)`. Period
  kinds (`date_kind in ("tw", "tm", "tq", "th", "ty")`): `RangeSlider`/`Slider` whose
  `vmin`/`vmax` come from the existing `arr` (`_dash_finite_column`) converted through the
  new `_dash_period_values(column, unit)` (vectorised `_dash_stata_value_of`, NaN for
  missing), so an all-missing column still yields the disabled widget and a single value
  the `+1` widening of the existing branch (F-20); `value` the same, `step=1`, the
  formatter as above with `kind=""` (the value is already a period number),
  `w._dash_is_date = True`, `w._dash_unit = date_kind`. The saved filter spec (:23707-23714;
  after section 17 it also carries `numeric` and `groups`) gains `"unit": getattr(_w,
  "_dash_unit", "")`; `_dash_frame_filter_mask`'s range and slider branches convert `col`
  with `_dash_period_values` when `getattr(w, "_dash_unit", "")`; `_DASH_FILTER_MASK_JS`'s
  range and slider branches read `spec.unit` and compare `dash_stata_value_of(col[i],
  spec.unit)` (null → the row is dropped, as a missing value is today). The dropdown
  branches of both masks are section 17's and are not touched. `_date_slider_step_days`
  keeps serving `td`. `_at_full_extent` works unchanged on period numbers.
- **TR-12.4 Tooltips, the merged signatures.** Today `_dash_hover_row(col, label,
  date_kind="", numeric_fmt="")`. Stage one (section 14, batch 2, on the tree): `text_col=None`
  appended, and `_dash_build_hover` gains `layers=None, value_labels=None,
  value_label_names=None`. Stage two (this section): replace `date_kind`/`numeric_fmt`
  with `fmt="", kind="", storage="", cache=None`, keeping `text_col=None` last, and append
  `formats=None, storage_types=None, fmt_cache=None` to `_dash_build_hover`. Final forms:
  `_dash_hover_row(col, label, fmt="", kind="", storage="", cache=None, text_col=None)`
  returns `((label, f"@{{{text_col}}}"), None)` when `text_col` is given (tested first,
  never formatted), else `((label, f"@{{{col}}}{{custom}}"), (f"@{{{col}}}",
  _dash_fmt_hover(fmt, kind, storage, cache)))` for a variable with a writable format or a
  date kind, else `((label, f"@{{{col}}}"), None)`;
  `_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars,
  numeric_formats, univar, layers=None, value_labels=None, value_label_names=None,
  formats=None, storage_types=None, fmt_cache=None)`: section 14's value-label column pass
  (`__dash_hover_<var>`) runs before `_fields_for`, then this section's formatter pass
  builds `formatters` from the returned pairs; `_fields_for` keeps checking names with
  `_dash_is_stata_name` (section 07) and its text-column rule; both call sites (saved
  :22348, served :26451) pass all six keywords. The served app's import list
  (:25236-25262) gains `CustomJSHover` and `CustomJSTickFormatter`. `test_label_sinks.py`
  `_PLACEHOLDER` becomes `r"@\{[^\W\d]\w*\}(?:\{(?:[0-9.,%FT ]+|custom)\})?"` and a new
  test asserts every `{custom}` field maps to a `CustomJSHover` whose `args["fmt"]` is a
  string and whose `code` does not contain that string.
- **TR-12.5 Axes, the merged signature.** `_dash_date_axis_formatter(fmt, storage, cache)`
  = `_dash_fmt_tick_formatter(fmt, _stata_date_kind(fmt), storage, cache)`; the saved
  site (:22029-22034) and the served site (:26198-26200) call it with the axis variable's
  full format (`self.formats[var]` / `_FORMATS[var]`; the variable is the one whose kind
  set `_x_date`/`_y_date`). `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None,
  fmt_fallback="", grid_color=None, value_labels=None, fmt_cache=None)`: section 14 added
  `value_labels` (batch 2) and section 18 the `norescale`/hull hooks (batch 3, merged
  before this section); this section adds `fmt_cache=None` and edits only the `format()`
  branch (:16800-16810 at 91d97be): when `_dash_fmt_kind(fmt) in ("f", "g", "e")` set
  `_dash_fmt_tick_formatter(fmt, "", "", fmt_cache)`; a date `format()` on a numeric axis
  keeps today's behaviour; an unwritable explicit format keeps the warning. The cache
  reaches it through a `fmt_cache=None` keyword appended last to `_dash_apply_axis_options`
  and `_dash_finish_secondary_axes` (after section 14's `value_labels`,
  `value_label_names`), passed from the four call sites (saved 22115/22307
  `self._fmt_models`; served 26266/26399 `_fmt_cache`). `_datetime_formatter_for` is
  deleted; `_stata_numeric_pattern` is deleted once no caller remains. The explicit-label
  formatter at :16786-16796 is section 14's; the two formatters are not merged and no
  shared code string is exposed (nothing in WP-28 would consume it).
- **TR-12.6 Marker labels.** In `_apply_mlabel_opts` the date branch becomes
  `["." if m else _dash_fmt_text(_dash_stata_value_of(v, _kind), _fmt) …]` with `_fmt =
  self.formats.get(var)` — the mapper holds `date_vars` (kind) and `numeric_formats`; add
  `mapper.formats` (full map) through `_dash_attach_labels(formats=None)` (appended after
  section 04's `storage_types=`) so the picture is available; the numeric branch uses
  `_dash_fmt_text(v, _numfmt, self.storage_types.get(var))`; the no-format branch uses
  `_dash_fmt_text(v, "%9.0g", storage)` (Stata's default for a variable with no format is
  its type's default: `%9.0g` float, `%10.0g` double, `%8.0g` int/byte, `%12.0g` long — a
  variable always carries a format from `st_varformat`, so this branch is reached only by
  hand-edited specs; use `%9.0g`). `_mlabformat_column` gates on `_dash_fmt_kind(fmt) in
  ("f", "g", "e")` and writes with `_dash_fmt_text`; a date variable keeps its note for a
  numeric `mlabformat` (§Boundaries). `_mlabel_date_texts` is deleted. The derived columns
  are `__dash_mlabel_*` (section 07).
- **TR-12.7 Facet titles.** `_dash_stata_date_text(value, fmt)` takes the full format
  (kind from `_stata_date_kind(fmt)`) and writes `_dash_fmt_text(_dash_stata_value_of(ms,
  kind), fmt)`; `_dash_facet_label` gains `formats=None` (appended after section 14's
  value-label keywords) and calls `date_formatter(val, formats.get(var) or "%" + _kind)`;
  both callers pass the full map; `DashRenderer._format_date_value` and
  `_format_date_value_standalone` are deleted.
- **TR-12.8 CSV.** `_dash_csv_meta` gains `"storage": {var: type}` from a new
  `storage_types` argument (both callers: :23855, :27090); `dash_csv_cell` passes
  `storage[j]` to `dash_csv_number(v, storage)`, which returns `dash_float32_text(v)`
  when `storage === "float"`, else today's `String(v)` with the `-0` rule. Dates stay
  `dash_csv_date`. `_DASH_FMT_JS` is already in both CSV scripts (section 04).
- **TR-12.9 Colorvar labels.** Inside `_dash_colorvar_bins(col_vals, cuts, discrete,
  label_of)` (section 16 TR-16.3) `label_of`'s `f"{v:g}"` fallback and the three interval
  labels use `_dash_fmt_text(v, self.formats.get(varname, "%9.0g"),
  self.storage_types.get(varname))`. Nothing else in `_apply_colorvar` or
  `_dash_colorvar_bins` (cuts, levels, gray rule, section 14's `_dash_value_labels_for`
  lookup, section 17's string path) changes.
- **TR-12.10 Both renderers.** New module functions in the function copy list after
  `"_dash_hover_row"` (24539): `_dash_fmt_tick_formatter`, `_dash_fmt_hover`,
  `_dash_date_axis_formatter`, `_dash_period_values`; `_dash_hover_row`,
  `_dash_build_hover`, `_dash_filter_widget`, `_dash_facet_label`,
  `_dash_stata_date_text`, `_dash_csv_meta` are already copied; the served template's
  call sites listed above change; `function_test_map.py` gains the four new names and
  loses `_datetime_formatter_for`, `_format_date_value_standalone`,
  `_stata_numeric_pattern`, `_parse_stata_numeric_fmt`, `_format_stata_numeric` (once its
  last caller moves), `DashRenderer._format_date_value`, `GlyphMapper._mlabel_date_texts`.
- **TR-12.11 Security.** Formats reach BokehJS only as `args` values; option labels are
  text nodes (the comment at :17611-17616), slider titles and axis ticks are canvas or
  `textContent`, `LabelSet` text is canvas, tooltip values are inserted as text by
  BokehJS, the CSV cell is quoted and guarded as today, the facet title reaches a KPI
  card that escapes it. No new HTML sink is created.
- **TR-12.12 Documents.** dash.sthlp :1783-1784, :2361, :2441-2461 and :862-866 are this
  section's; :1109-1138 is section 17's (batch 2, its task 17-06), which wrote this section's sentence into
  it ("A listed value is written in the variable's display format, or its value label;
  values that share one display text are one entry that selects them all; and a %tw, %tm,
  %tq, %th or %ty variable's range slider moves over Stata's period numbers in steps of
  one", the wording of section 17's TR-17.15 and task 17-06); 12-15 verifies that wording
  and never rewrites the paragraph.
  CHANGELOG: the markers `<!-- WP-28 E3 -->` and `<!-- WP-28 G6 -->` sit in the `**WP-28
  (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change`
  list (S01, D2); 12-15 replaces each with its line ending `(WP-28, E3)` / `(WP-28, G6)`.
  BUGS.md: two closed entries appended at the end with `- Resolution: Fixed <ddmonyyyy>
  (WP-28, E3). …` and `… (WP-28, G6). …`.

## Boundaries

- Not the KPI card (section 11); not `_dash_option_value`, `_dash_dropdown_values`, the
  dropdown branches of either mask, the `groups` mechanism or the exclusion rule (section
  17); not `_apply_colorvar`'s cut logic, levels or gray rule (section 16); not tick
  *placement* on date or numeric axes (`_dash_tsnatscale_ticks`, section 14/18) nor the
  default axis format for a variable with no `format()` (GAPS2 G10, out of scope); not
  the explicit `xlabel(1 "text")` formatter (section 14); not `_dash_apply_axis_spec`'s
  `norescale`/hull hooks (section 18).
- A numeric `mlabformat()` on a date variable stays named and the dates kept, as
  documented at dash.sthlp:1783 and pinned by `test_help_claims_5.py:1121`: twoway's
  behaviour there was not measured and is not in E3/G6.
- Dates in the CSV stay ISO 8601 and doubles keep JavaScript's shortest spelling
  (dash.sthlp:862-866 is a documented, re-importable contract; E3 names no CSV site);
  only the float-storage digits change (G6).
- `%tC` is written on `%tc`'s epoch (G7 out of scope); extended missing values are `.`
  (G12).
- Silent when honoured (Q22): `mlabformat(%9.3g)` and every format now written print
  nothing; the only notes left are the existing ones for unwritable formats.
- BUGS.md entries for E3 and G6 land closed in task 12-15's commit.
- No Stata run, no cscript, no extract script in this section (D11: the one twoway truth
  E3 needs is section 14's probe).

## Stata truth

No Stata run in this section. Every text this section writes is a `display` output
already pinned by section 04's `format_truth.json` (`numeric_formats`, `date_formats`) and
by `date_truth.json`; the tests assert the site's text equals `_dash_fmt_text` of the
value under the variable's format, and `_dash_fmt_text` is held to Stata by section 04.
The one twoway-drawn truth E3's plan names — the axis label text of a `%tm` variable — is
recorded by section 14 (batch 2) in `test/fixtures/axis_truth.json` as the probe pair
`e3_tm_axis` / `e3_tm_axis_lab` (group `b1_label`; `sysuse sp500`, `m = mofd(date)`,
`format m %tm`, `twoway line close m` bare and with `xlabel(492(3)501, format(%tm))`;
ticks 492 495 498 501; texts `2001m1 2001m4 2001m7 2001m10`).
`TestDateAxis::test_ticks_read_as_stata_in_both_modes` reads
`truth['probes']['e3_tm_axis_lab']` and calls `pytest.fail("section 14 must land first:
axis_truth.json has no e3_tm_axis_lab probe")` when it is absent; it never skips.

## TDD test stubs

All in **`test/test_display_format_sites.py`** (new, tasks 12-01 and 12-02) unless noted;
both-mode helpers from `test/test_mode_parity.py` (`_standalone`, `_served`, `_spec`); the
node runner `from js_runner import run_js, JsSession, mask_parity` (section 03); auto from
`test/fixtures/data/auto.csv` with `when` (`%td`), `whenm` (`%tm`, 2000m1..2000m3), `whenq`
(`%tq`), `whenc` (`%tc`), `whenC` (`%tC`, the same milliseconds as `whenc`; section 04
writes `%tC` on `%tc`'s epoch) and `f` (a float32-rounded `price/7`, storage `float`).
Each stub names its pre-fix failure; 12-01 and 12-02 record every failure text (Q24).

- Test: `TestDropdown::test_labels_are_statas_text_in_both_modes` — dropdowns over
  `price` (`%8.0gc` → `4,099`), `when` (`%td` → `02jan2000`), `whenm` (`%tm` → `2000m1`),
  `f` (float → `.1`-style digits, `%9.0g`); values unchanged (compare to
  `_dash_option_value`). Pre-fix: `4099`, `2000-01-02 00:00:00`.
- Test: `TestDropdown::test_a_value_label_still_wins` — `foreign` with labels.
- Test: `TestDropdown::test_two_values_with_one_formatted_label_select_both` — a float
  column holding 0.1 (float32) and a double column holding 0.1000000015 under `%9.0g`
  list one entry `.1`; `%9.0f` on a column holding 1.2 and 1.4 lists one entry `1` whose
  spec `groups` entry holds both members (saved) and whose `_dash_groups` holds both
  (served); selecting it keeps both rows in both modes (`mask_parity` for the two masks,
  `_served` for the app). Pre-fix: two entries with one label (or Bokeh's duplicate-label
  error).
- Test: `TestSliders::test_numeric_and_td_sliders_carry_a_stata_formatter` — the
  `RangeSlider`/`DateRangeSlider` `format` is a `CustomJSTickFormatter` with
  `args["fmt"]` the variable's format; under node `format.code` on `value=4099` → `4,099`
  and on the `%td` slider's start (ms) → `02jan2000`. Pre-fix: `format == "0[.]00"`.
- Test: `TestSliders::test_period_kinds_are_numeric_sliders_over_period_numbers` —
  `whenm` range: `RangeSlider`, `start == 480`, `end == 482`, `step == 1`, formatter
  gives `2000m1`; `whenq`, `%th`, `%ty`, `%tw` likewise; `w._dash_unit` set; the saved
  filter spec holds `unit`. Pre-fix: `DateRangeSlider`.
- Test: `TestSliders::test_a_period_column_with_one_value_or_none` — an all-missing
  `%tm` column gives the disabled widget the existing branch gives; a column with one
  period gives `end == start + 1` (the `+1` widening) and its mask keeps the row (F-20).
- Test: `TestSliders::test_the_masks_agree_on_a_period_slider_in_both_modes` —
  `whenm` range set to `(481, 481)`: `mask_parity(df, filter_specs, widget_values)`
  reports the pandas mask (`_dash_frame_filter_mask`) equal to the node mask, both equal
  to the rows whose month is February; a missing `whenm` row is dropped once moved and
  kept at full extent.
- Test: `TestSliders::test_a_period_move_reaches_a_card_and_a_graph` — after the move
  (`JsSession`, one move) the graph source holds the February rows and a `count(price)`
  card reads their count, saved (node) and served.
- Test: `TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` — the
  HoverTool of a `scatter price when` figure has `("price", "@{price}{custom}")`,
  `("when", "@{when}{custom}")`, `formatters["@{price}"]` a `CustomJSHover` with
  `args["fmt"] == "%8.0gc"`, `"@{when}"` with `"%td"`, `code` not containing `%8.0gc`;
  under node the hover code on 4099 → `4,099`, on `when`'s ms → `02jan2000`, on 12345.67
  under `%10.0g` → `12345.67` (F-23); a `%tc` variable and the `%tC` variable `whenC`
  keep their time (`02jan2000 00:00:00`-style text, F-19); both modes. Pre-fix:
  `@{when}{%F}`, `1.235e+4`.
- Test: `TestTooltips::test_one_formatter_model_per_format_triple` — three figures over
  `price` and `when`: the document holds exactly two `CustomJSHover` models (+ the
  computed-column ones, which are not `CustomJSHover`).
- Test: `TestTooltips::test_a_value_labelled_hover_variable_is_not_formatted` —
  `hover(foreign)` with value labels: the row is section 14's `@{__dash_hover_foreign}`
  with no `{custom}` and no formatter (the `text_col` branch runs first).
- Test: `TestTooltips::test_the_label_sink_pattern_admits_custom_only_with_a_formatter`
  (in `test/test_label_sinks.py`): every `{custom}` field has a formatter; no other
  `{…}` form appears but the numeric/date ones.
- Test: `TestDateAxis::test_ticks_read_as_stata_in_both_modes` — `line price when`:
  `fig.xaxis[0].formatter` is a `CustomJSTickFormatter` with `args["fmt"] == "%td"`, and
  its code under node on the ms of 02jan2000 → `02jan2000`; `%tm` → `2000m1`; `%tc` with
  a time; `%tdCCYY-NN-DD` honoured; `%ty` → `2000`; and, from `axis_truth.json`'s
  `e3_tm_axis_lab` probe, `_dash_fmt_text(v, "%tm")` and the node twin at v in {492, 495,
  498, 501} equal `2001m1 2001m4 2001m7 2001m10`, each present in the probe's `texts` and
  absent from `e3_tm_axis.texts` (the companion without `xlabel()`); `pytest.fail`, never
  skip, when the probe is absent. Pre-fix: `DatetimeTickFormatter`.
- Test: `TestNumericAxis::test_format_suboption_is_written_by_the_formatter` —
  `ylabel(, format(%9.0fc))` → `CustomJSTickFormatter`, node on 4099 → `4,099`;
  `format(%9.2e)` → `4.10e+03`; `format(%9.3g)` → `4.10e+03`; `format(%12s)` still warns
  and leaves the formatter default; `%9.999999999f` bounded and warned.
- Test: `TestMarkerLabels::test_a_date_a_float_and_a_g_variable_in_both_modes` —
  `mlabel(when)` → `02jan2000…`; `mlabel(f)` on the float column → `_dash_fmt_text(v,
  "%9.0g")`, never a 17-digit expansion; `mlabel(price)` → `4,099`; a missing → `.`.
- Test: `TestMarkerLabels::test_mlabformat_g_is_honoured_and_silent` — `mlabformat(%9.3g)`
  → labels `4.10e+03`, no warning in either mode; `mlabformat(%td)` on `price` → dates
  (Stata's `display %td 4099`); `mlabformat(%12s)` still named.
- Test: `TestFacetTitles::test_a_date_panel_is_titled_as_stata_in_both_modes` —
  `by(when)` → `02jan2000`, `by(whenm)` → `2000m1`, a custom picture honoured;
  `_dash_stata_date_text(14610.0, "%td") == "01jan2000"`, `(nan, "%td") == "."`.
- Test: `TestCsv::test_a_float_variable_writes_its_float32_digits` — meta with
  `storage {"f": "float"}`: node `dash_csv_text` writes `0.1` for the float-stored value
  whose double is `0.10000000149011612`; a double column is unchanged (`1e-7`,
  `123456789012`); dates still ISO; both the saved and served CSV scripts. Pre-fix:
  `0.10000000149011612`.
- Test: `TestColorvarLabels::test_number_labels_use_the_variables_format` —
  `colorvar(price)` with `colorcuts(4000 6000)`: cut labels hold `4,000` and `6,000`;
  a discrete unlabelled value uses `%8.0gc`.
- Test: `TestRetired::test_the_old_formatters_are_gone` — `dash_render` has no
  `_datetime_formatter_for`, `_format_date_value_standalone`, `_stata_numeric_pattern`,
  `_parse_stata_numeric_fmt`, `_format_stata_numeric`; `GlyphMapper` no
  `_mlabel_date_texts`; `DashRenderer` no `_format_date_value`.
- Test: `TestParity::test_the_saved_text_after_a_move_equals_before` — a `mpg` slider
  at its minimum: dropdown labels, slider formatter output, marker labels (LabelSet
  column) and a card are unchanged, under node.

**Mutation table**:

| break this | test that must die |
|---|---|
| put the format into `CustomJSHover.code` instead of `args` | `TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` (`code` check) |
| convert the column in the pandas mask but not in the JS mask | `TestSliders::test_the_masks_agree_on_a_period_slider_in_both_modes` |
| build a new formatter model per figure | `TestTooltips::test_one_formatter_model_per_format_triple` |
| pass the date kind instead of the full format to `_dash_stata_date_text` | `TestFacetTitles` (custom picture) |
| `dash_csv_number` ignores `storage` | `TestCsv::test_a_float_variable_writes_its_float32_digits` |
| keep `%9.3g` in `_mlabformat_column`'s refusal | `TestMarkerLabels::test_mlabformat_g_is_honoured_and_silent` |
| list a value per entry instead of a group per label | `TestDropdown::test_two_values_with_one_formatted_label_select_both` |
| format a `text_col` row | `TestTooltips::test_a_value_labelled_hover_variable_is_not_formatted` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Dropdown labels; groups by label | pytest (+ `mask_parity`) | format_truth.json (via `_dash_fmt_text`) | yes |
| Slider formatters; period sliders; empty/single columns; masks agree | pytest + node (`mask_parity`, `JsSession`) | none | yes |
| Tooltips: fields, formatters, args, node output, `%tC`, one model per triple | pytest + node | none | yes |
| Date-axis ticks against twoway's `%tm` texts; numeric `format()` | pytest + node | `axis_truth.json` `e3_tm_axis_lab` (S14); format_truth.json | yes |
| Marker labels, `mlabformat` | pytest | none | yes |
| by() titles | pytest | none | yes |
| CSV float32 | pytest + node | none | yes (both scripts) |
| Colorvar labels | pytest | none | yes |
| Label-sink pattern | pytest | none | yes |
| Text unchanged across a move | pytest + node | none | saved |
| Retired names | pytest | none | n/a |

Acceptance criteria:

- **AC-12.1** `python3 -m pytest test/test_display_format_sites.py -q` passes with no
  skips under both interpreters.
- **AC-12.2** Every pinned test in §Evidence is flipped, none deleted, each named in the
  commit body's `Flipped:` lines with old and new text.
- **AC-12.3** The full pytest suite is green; `TestTheServedAppCarriesEveryName` and
  `TestTheServedAppDefinesEveryNameItReads` pass; `test_mode_parity.py` CORPUS profiles
  are equal between modes and every `_MUST_WARN` key still names a corpus case.
- **AC-12.4** BUGS.md carries E3 and G6 closed (`- Resolution: Fixed <ddmonyyyy> (WP-28,
  E3). …` and `… (WP-28, G6). …`) naming their tests; dash.sthlp :1783-1784, :2361,
  :2441-2461 and the CSV paragraph are updated and :1109-1138 holds section 17's sentence;
  the `<!-- WP-28 E3 -->` and `<!-- WP-28 G6 -->` markers are replaced by lines ending
  `(WP-28, E3)` and `(WP-28, G6)` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group of
  `### Results that change`.

## Tasks

Commit boundary: **one commit (E3 and G6 together)** holding 12-01 to 12-15, subject
ending `(GAPS2 E3, G6)` -- one code path (the writer at every site) closes both gaps, so
they are not separable into green commits -- made by 12-15 on the worktree branch
`wp28-s12` after the section's one full pytest run in the worktree (CLAUDE.md rules 4 and
11); the merger lands it on `s3-bugs` with the same message (index.md step 1). The body
opens with `<scratch>/12-01-failure.txt` and `<scratch>/12-02-failure.txt` (Q24) and
carries S01 TR-01.9's `Regression:` / `Flipped:` / `BUGS.md:` lines (two `BUGS.md:` lines).
No Stata run in this section. No AI references anywhere.

<task type="auto" id="12-01">
  <name>Write the failing widget and tooltip tests</name>
  <files>test/test_display_format_sites.py, test/test_label_sinks.py</files>
  <action><![CDATA[
    Create `test/test_display_format_sites.py` with the helpers "TDD test stubs" name (import `_standalone`, `_served`, `_spec` from `test_mode_parity`; `from js_runner import run_js, JsSession, mask_parity`; build the auto frame with `when`, `whenm`, `whenq`, `whenc`, `whenC`, `f`; a `truth()` fixture that loads `test/fixtures/axis_truth.json` and `pytest.fail`s, never skips, when a probe is missing), the module docstring stating GAPS2 E3's and G6's measured symptoms, and the classes `TestDropdown`, `TestSliders` and `TestTooltips` with exactly the stub names. In `test/test_label_sinks.py` add `TestTooltips::test_the_label_sink_pattern_admits_custom_only_with_a_formatter` (it fails now because no `{custom}` field exists — write it to assert at least one such field per figure over a variable with a format, so it is not vacuous). Do not touch dash_render.py. Run both files against the tree as batch 2 left it. Do not commit: save the failure output (`2000-01-02 00:00:00`, `4099`, two entries sharing one label, `DateRangeSlider`, `0[.]00`, `@{when}{%F}`, `1.235e+4`) to `<scratch>/12-01-failure.txt`; it opens the commit's body and its values are the CHANGELOG's old values (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q 2>&1 | tail -5` reports 0 passed, no collection error, failures with the old text rather than exceptions where a site exists today; `<scratch>/12-01-failure.txt` exists.]]></verify>
  <done>The widget and tooltip regression tests existed and failed for their recorded reasons, with nothing committed.</done>
</task>

<task type="auto" id="12-02">
  <name>Write the failing axis, label and CSV tests</name>
  <files>test/test_display_format_sites.py</files>
  <action><![CDATA[
    Add to `test/test_display_format_sites.py` the classes `TestDateAxis` (reading `truth()['probes']['e3_tm_axis_lab']` and `['e3_tm_axis']` as the stub says, `pytest.fail` when absent), `TestNumericAxis`, `TestMarkerLabels`, `TestFacetTitles`, `TestCsv`, `TestColorvarLabels`, `TestRetired` and `TestParity` with exactly the stub names; skip node cases only when node is absent and assert in a module test that the node tests ran. Do not touch dash_render.py. Run the file against the same tree. Do not commit: save the failure output (`DatetimeTickFormatter`, `NumeralTickFormatter`, `03 Jan 2000`-style pictures, `0.10000000149011612`, the `mlabformat(%9.3g)` note, `01 Jan 2000` panel titles) to `<scratch>/12-02-failure.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q 2>&1 | tail -5` reports 0 passed and no collection error; `python3 -m pytest test/test_display_format_sites.py -q -k TestDateAxis 2>&1 | grep -c "e3_tm_axis_lab"` is 0 (the probe exists: section 14 landed in batch 2) and the case fails on `DatetimeTickFormatter`; `<scratch>/12-02-failure.txt` exists.]]></verify>
  <done>The axis, label, CSV and parity regression tests existed and failed for their recorded reasons, with nothing committed.</done>
</task>

<task type="auto" id="12-03">
  <name>Format dropdown and slider labels</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_fmt_tick_formatter`, `_dash_fmt_hover` (TR-12.1) beside the section 04 writer functions and to the function copy list immediately after `"_dash_hover_row"` (24539). Extend `_dash_filter_widget` with `fmt=""`, `storage=""`, `fmt_cache=None` after section 17's keywords (TR-12.2, TR-12.3 for the non-period branches: every `RangeSlider`, `Slider`, `DateRangeSlider`, `DateSlider` and `DatetimeRangeSlider` gets `format=_dash_fmt_tick_formatter(...)`, kind `""` for a numeric column and the date kind for a date one). Form the dropdown groups by label as TR-12.2 says, on section 17's mechanism: label every distinct value with `_label`, put values sharing one label into one `groups` entry (first member first), list each group once with its first member as the value and the shared text as the label; set the served widget's `_dash_groups` the same way. Pass the new arguments from the saved `_build_filter_widgets` (`self.formats`, `self.storage_types`, `self._fmt_models`) and from the served call (:26703-26706 at 91d97be: `_FORMATS`, `_storage_types`, `_fmt_cache`, created at the top of `make_document`). Add the served imports `CustomJSHover`, `CustomJSTickFormatter` (:25236-25262). Do not touch the period-kind branch, the dropdown option values, the dropdown branches of the masks or the masks' group rule (section 17). Map the two new functions to `TestTooltips::test_one_formatter_model_per_format_triple` and `TestSliders::test_numeric_and_td_sliders_carry_a_stata_formatter`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k "TestDropdown or numeric_and_td_sliders"` passes, `test_two_values_with_one_formatted_label_select_both` included; `python3 -m pytest test/test_filter_widget_data.py test/test_saved_filter_layers.py test/test_dropdown_values.py test/test_js_runner.py -q` shows only the `2001-12-31 00:00:00` pin failing (flipped in 12-14).]]></verify>
  <done>Dropdown labels and every slider label read as Stata's display text in both modes, from one cached formatter model per format, and values sharing one text became one entry that selects them all.</done>
</task>

<task type="auto" id="12-04">
  <name>Move period kinds onto numeric sliders</name>
  <files>dash_render.py, test/test_filter_slider_step.py</files>
  <action><![CDATA[
    Implement TR-12.3's period branch in `_dash_filter_widget` (after the clock branch, before the `elif is_date` `td` branch), deriving `vmin`/`vmax` from the existing `arr` through the new helper `_dash_period_values(column, unit)` so the empty-column and single-value paths of the existing branch still run; the `unit` field in the saved filter spec (:23707-23714 at 91d97be, beside section 17's `numeric` and `groups`); the conversion in `_dash_frame_filter_mask`'s range and slider branches (leave section 17's dropdown branch alone) and in `_DASH_FILTER_MASK_JS`'s slider and range branches (likewise). Add `_dash_period_values` to the function copy list after `_dash_fmt_hover` and to the test map (`TestSliders::test_a_period_column_with_one_value_or_none`). Flip `test_filter_slider_step.py` (:180-215): the `tw/tm/tq/th` cases assert a `RangeSlider` with `step == 1` and `start/end` the period numbers; the `td` case stays and the monthly-series test's span assertion moves to the period domain (`2010m1..2019m12` is 119 periods, step 1). Record the flips in `<scratch>/12-flips.txt` as `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k TestSliders` passes (pandas and node masks agree on one move; the empty and single-value columns behave; a card and a graph follow); `python3 -m pytest test/test_filter_slider_step.py test/test_export.py test/test_filter_exclude.py test/test_filter_exclusion_sets.py -q` passes.]]></verify>
  <done>A %tw/%tm/%tq/%th/%ty filter became a step-1 slider over Stata's period numbers, labelled in the variable's format, and both masks kept exactly the rows in its bounds.</done>
</task>

<task type="auto" id="12-05">
  <name>Format tooltips through CustomJSHover</name>
  <files>dash_render.py, test/test_label_sinks.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply stage two of TR-12.4 to the tree's stage-one signatures: in `_dash_hover_row` replace `date_kind`/`numeric_fmt` with `fmt="", kind="", storage="", cache=None`, keeping section 14's `text_col=None` last and its branch first; append `formats=None, storage_types=None, fmt_cache=None` to `_dash_build_hover`, build the `formatters` dict from the returned pairs after section 14's value-label column pass and leave the `_tooltip_precision` fallback for computed columns untouched. Pass `formats`, `storage_types` and the cache from the saved call (:22348) and the served call (:26451), so both call sites pass all six keywords. Widen `_PLACEHOLDER` in `test/test_label_sinks.py` deliberately (comment: `{custom}` is admitted only with a `CustomJSHover` whose args carry the format). Update the test map for `_dash_hover_row` and `_dash_build_hover` to this section's tests. `test_server_layer_defects.py::TestTheHoverBuilder` (calls by keyword) is flipped in 12-11, not here.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k TestTooltips` and `python3 -m pytest test/test_label_sinks.py test/test_value_labels_drawn.py -k Hover -q` pass (section 14's value-label rows still carry no formatter); `python3 -m pytest test/test_date_range.py test/test_served_dates.py test/test_help_claims_4.py test/test_server_layer_defects.py -q -k "hover or tooltip or HoverBuilder"` shows only the `@{date}{%F}` pins and `TestTheHoverBuilder` failing (flipped in 12-11 and 12-14).]]></verify>
  <done>Every tooltip row for a variable was written by the format writer in both modes, the format travelled in args, a value-labelled row stayed unformatted, and the label-sink test admitted `{custom}` only with a formatter.</done>
</task>

<task type="auto" id="12-06">
  <name>Write axis ticks through the formatter</name>
  <files>dash_render.py, test/function_test_map.py, test/test_axis_options.py</files>
  <action><![CDATA[
    Add `_dash_date_axis_formatter(fmt, storage, cache)` (TR-12.5), use it at the saved site (:22029-22034) and the served site (:26198-26200) with the axis variable's full format, add `fmt_cache=None` last to `_dash_apply_axis_spec`, `_dash_apply_axis_options` and `_dash_finish_secondary_axes` (after section 14's keywords; section 18's hooks are already on the tree and are not touched), thread it from the four call sites, and change only the `format()` branch of `_dash_apply_axis_spec` to set `_dash_fmt_tick_formatter(fmt, "", "", fmt_cache)` for every f/g/e `format()`. Delete `_datetime_formatter_for`; delete `_stata_numeric_pattern` if this was its last caller (grep), else leave it for 12-09. Flip `test_axis_options.py` (:176-190) to assert a `CustomJSTickFormatter` with `args["fmt"]` and node output `4,099` (record the flip in `<scratch>/12-flips.txt`). Keep the explicit-label formatter (:16786-16796) untouched (section 14). Map `_dash_date_axis_formatter` to `TestDateAxis::test_ticks_read_as_stata_in_both_modes`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k "TestDateAxis or TestNumericAxis"` passes, the `e3_tm_axis_lab` comparison included; `python3 -m pytest test/test_axis_options.py test/test_axis_extents.py test/test_axis_label_grammar.py test/test_adversarial_matrix.py -q` passes; `python3 -m pytest test/test_dates.py test/test_help_claims_7.py -q` shows only the `DatetimeTickFormatter` and `fmt.format` pins failing (flipped in 12-13).]]></verify>
  <done>Date-axis ticks and explicit numeric formats became Stata's text in both modes, twoway's `%tm` texts included, and the fixed per-kind formatter was gone.</done>
</task>

<task type="auto" id="12-07">
  <name>Format marker labels and mlabformat</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Implement TR-12.6: add `formats=None` to `_dash_attach_labels` (after section 04's `storage_types=`) and pass the full map from both callers (saved and served) so the mapper holds `self.formats`; rewrite the date, numeric and no-format branches of `_apply_mlabel_opts` on `_dash_fmt_text`; make `_mlabformat_column` gate on `_dash_fmt_kind(fmt) in ("f", "g", "e")` and write with `_dash_fmt_text`, keeping the note for a numeric `mlabformat` on a date variable; delete `GlyphMapper._mlabel_date_texts` and its test-map entry. The derived columns keep section 07's `__dash_mlabel_*` names.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k TestMarkerLabels` passes; `python3 -m pytest test/test_marker_label_parity.py test/test_function_test_map.py -q` passes; `python3 -m pytest test/test_help_claims_5.py test/test_twoway_option_parity.py -q -k "mlab or Labels"` shows only the fixed-picture and `%9.3g` pins failing (flipped in 12-12).]]></verify>
  <done>Marker labels and `mlabformat()` became Stata's text for every writable format in both modes, and the fixed-picture date helper of the mapper was gone.</done>
</task>

<task type="auto" id="12-08">
  <name>Format facet titles and retire date helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Implement TR-12.7: `_dash_stata_date_text(value, fmt)` takes the full format and writes through `_dash_fmt_text(_dash_stata_value_of(ms, kind), fmt)`; `_dash_facet_label` gains `formats=None` after section 14's keywords and calls `date_formatter(val, formats.get(var) or "%" + _kind)`; both callers (saved :21754, served :26547-26550 at 91d97be) pass the full map. Delete `DashRenderer._format_date_value` and `_format_date_value_standalone` (section 11's callers moved in batch 3 before this section; grep for any remaining caller first) and their test-map entries; map `_dash_stata_date_text` to `TestFacetTitles::test_a_date_panel_is_titled_as_stata_in_both_modes`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k "TestFacetTitles"` passes; `grep -c "_format_date_value_standalone\|def _format_date_value" dash_render.py` prints 0; `python3 -m pytest test/test_function_test_map.py test/test_facets.py -q` passes.]]></verify>
  <done>by() panel titles became Stata's text for the variable's full picture in both modes, and the two fixed-picture date helpers were gone.</done>
</task>

<task type="auto" id="12-09">
  <name>Format colorvar labels and retire numeric helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Implement TR-12.9 inside section 16's `_dash_colorvar_bins(col_vals, cuts, discrete, label_of)`: `label_of`'s `f"{v:g}"` fallback and the three interval labels use `_dash_fmt_text(v, self.formats.get(varname, "%9.0g"), self.storage_types.get(varname))`; touch nothing else in `_apply_colorvar` (section 14's `_dash_value_labels_for` lookup and section 17's string path stay as they are). Delete `_parse_stata_numeric_fmt`, `_stata_numeric_pattern` and `_format_stata_numeric` once `grep` shows no caller in dash_render.py; leave their tests to 12-13. Make the test map current (additions and removals).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k "TestColorvarLabels or TestRetired"` passes; `python3 -m pytest test/test_colorvar_legend.py test/test_colorvar_forms.py test/test_function_test_map.py test/test_statistical_helpers.py -q -k "colorvar or map or CarriesEveryName"` passes (substitute section 16's test file name if it differs).]]></verify>
  <done>Colorvar number labels became the variable's display text in both modes and the `%f`-only numeric helpers were gone.</done>
</task>

<task type="auto" id="12-10">
  <name>Write float32 digits in the CSV</name>
  <files>dash_render.py, test/test_export.py</files>
  <action><![CDATA[
    Implement TR-12.8: `_dash_csv_meta(columns, formats, string_flags, value_labels, value_label_names, filename=…, storage_types=None)` adds `"storage"` (its labelset lookup is section 14's `_dash_value_labels_for`; keep it); both callers (:23855 saved, :27090 served at 91d97be) pass the storage map; in `_DASH_CSV_JS`, `dash_csv_number(v, storage)` and `dash_csv_cell(v, is_text, kind, labels, storage)` thread it, and `dash_csv_text` reads `meta.storage`. Flip `test_export.py::TestTheCsvFormatter::test_a_number_is_javascripts_shortest_spelling` to the new signature (same double cases) and `::TestTheHelpers::test_csv_meta` to the new key; add float cases; record the flips in `<scratch>/12-flips.txt`. Dates are untouched.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q -k TestCsv` and `python3 -m pytest test/test_export.py -q` pass.]]></verify>
  <done>The CSV wrote a float-stored variable as its float32 digits in both modes and everything else as before.</done>
</task>

<task type="auto" id="12-11">
  <name>Flip the pinned tooltip and date-range tests</name>
  <files>test/test_date_range.py, test/test_served_dates.py, test/test_server_layer_defects.py</files>
  <action><![CDATA[
    Flip with a comment naming E3/G6 and this section: `test_date_range.py` :476-478 `_LABELS`, :582, :609, :652, :790-860 and `test_the_date_formatter` (:944-961, rewritten against `_dash_stata_date_text(value, fmt)` for each of `%td`, `%tc`, `%tC`, `%tw`, `%tm`, `%tq`, `%th`, `%ty` with Stata's text from `format_truth.json`'s `date_formats` rows and `.` for missing); `test_served_dates.py` :129, :207, :229; `test_server_layer_defects.py::TestTheHoverBuilder` (:1187-1200): call `_dash_hover_row` and `_dash_build_hover` by the final keywords of TR-12.4 (`fmt=`, `kind=`, `storage=`, `cache=`, `text_col=`; `formats=`, `storage_types=`, `fmt_cache=`) and expect `@{col}{custom}` rows with a `CustomJSHover`. Record each old/new text as a `Flipped:` line in `<scratch>/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_range.py test/test_served_dates.py test/test_server_layer_defects.py -q` passes.]]></verify>
  <done>The date-range, served-dates and hover-builder tests pinned Stata's text and the merged signatures; none was deleted.</done>
</task>

<task type="auto" id="12-12">
  <name>Flip the pinned facet, marker-label and parity tests</name>
  <files>test/test_help_claims_5.py, test/test_mode_parity.py, test/test_twoway_option_parity.py</files>
  <action><![CDATA[
    Flip: `test_help_claims_5.py` :519-522, :565-573, :580-600 (`TestTheStataDateText` takes formats), :1110-1130 (dates as `03jan2000`; the `mlabformat(%9.2f)` note on a date variable stays); `test_mode_parity.py`: change the CORPUS case behind the `_MUST_WARN` key "a format mlabformat() cannot reproduce" from `%9.3g` to `%12s` and its expected message (:1444) to `dash: mlabformat(%12s) is not a display format dash reproduces` — the key is kept (:1608-1611 requires it to name a corpus case) and this section is the one whose gap silences it (rule R6 as index.md states it after the review); re-profile any CORPUS entry whose recorded text changed; edit neither `ALLOWED` nor any other `_MUST_WARN` entry; `test_twoway_option_parity.py::test_mlabformat_on_a_date_variable_is_named_and_the_dates_kept` (`16jan2020`) and `::test_a_format_dash_does_not_reproduce_is_named` (drop `%9.3g` from the parametrisation and add `test_mlabformat_g_is_honoured_in_both_modes`). Record each old/new text in `<scratch>/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_5.py test/test_mode_parity.py test/test_twoway_option_parity.py -q` passes, `test_mode_parity.py`'s `_MUST_WARN` key test included.]]></verify>
  <done>The facet, marker-label and parity tests pinned Stata's text and the honoured `%g`, the `mlabformat` warning entry still fired on `%12s`, and none was deleted.</done>
</task>

<task type="auto" id="12-13">
  <name>Flip the helper and axis-format pins</name>
  <files>test/test_dates.py, test/test_adversarial_matrix.py, test/test_help_claims_7.py</files>
  <action><![CDATA[
    Rewrite `test_dates.py::TestNumericDisplayFormats` against `_dash_fmt_text` and `_dash_fmt_kind` (the 56 f/fc cases through `_dash_fmt_text`; the tick-pattern test becomes a `_dash_fmt_tick_formatter` args test; the "does not reproduce" test becomes `_dash_fmt_kind` None/x/H cases) and `TestDatetimeAxis`'s formatter assertion (a `CustomJSTickFormatter` whose node output for a tick equals the fixture text); `test_adversarial_matrix.py::TestNumericFormatBounds` against `_dash_fmt_parse` (same bounds and timing); `test_help_claims_7.py:255-262`: the profile reads `args["fmt"]` of a `CustomJSTickFormatter` instead of `fmt.format`. Record each old/new text in `<scratch>/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dates.py test/test_adversarial_matrix.py test/test_help_claims_7.py -q` passes.]]></verify>
  <done>The numeric-format helper pins, the datetime-axis pin and the help-claims-7 axis profile pinned the writer and the formatter's args; none was deleted.</done>
</task>

<task type="auto" id="12-14">
  <name>Flip the dropdown and hover-field pins</name>
  <files>test/test_saved_filter_layers.py, test/test_help_claims_4.py</files>
  <action><![CDATA[
    Flip `test_saved_filter_layers.py::TestADateDropdown::test_the_option_labels_still_read_as_dates` (:1212-1216) to `31dec2001` and `test_help_claims_4.py:1706` to `@{date}{custom}` with a `CustomJSHover` whose `args["fmt"] == "%td"`, each with a comment naming E3 and this section. Run `python3 -m pytest test/test_saved_filter_layers.py test/test_help_claims_4.py test/test_kpi_format.py -q` (changed files only; section 11's card tests must still pass on this tree). Record both flips in `<scratch>/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_filter_layers.py test/test_help_claims_4.py test/test_kpi_format.py -q 2>&1 | tail -3` reports no failures.]]></verify>
  <done>The date-dropdown label pin and the help-claims-4 hover-field pin pinned Stata's text and the `{custom}` field, and section 11's card tests still passed.</done>
</task>

<task type="auto" id="12-15">
  <name>Close E3 and G6 in the documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md (S01 TR-01.8; never mid-file) two closed entries with the fields in order: `- [x] Title: Dates and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the variable's Stata display format` with `- Resolution: Fixed <ddmonyyyy> (WP-28, E3). Dropdown labels, slider labels and steps (period kinds as step-1 sliders over Stata's period numbers), tooltips (CustomJSHover with the format in args), date-axis ticks and explicit numeric format() are written by _dash_fmt_text / dash_fmt_text under the variable's display format in _dash_filter_widget, _dash_hover_row, _dash_build_hover, _dash_date_axis_formatter and _dash_apply_axis_spec, in both renderers; the KPI card sites are section 11's E1 entry. Pinned by test/test_display_format_sites.py::TestDropdown::test_labels_are_statas_text_in_both_modes, ::TestSliders::test_period_kinds_are_numeric_sliders_over_period_numbers, ::TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format, ::TestDateAxis::test_ticks_read_as_stata_in_both_modes, test/test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved; fixture test/fixtures/axis_truth.json (probe e3_tm_axis_lab, section 14).` and `- [x] Title: %g formats (Stata's default) and float storage are not reproduced, so values show full double expansions` with `- Resolution: Fixed <ddmonyyyy> (WP-28, G6). Marker labels, mlabformat(), by() titles, colorvar number labels and the CSV write %w.dg text and float32 digits through _dash_fmt_text / dash_fmt_text and dash_float32_text in _apply_mlabel_opts, _mlabformat_column, _dash_facet_label, _dash_colorvar_bins and _DASH_CSV_JS, in both renderers. Pinned by test/test_display_format_sites.py::TestMarkerLabels::test_a_date_a_float_and_a_g_variable_in_both_modes, ::TestCsv::test_a_float_variable_writes_its_float32_digits, test/test_display_format_writer.py::TestPythonWriter::test_every_numeric_display_matches_stata_exactly.` -- neither title holds `"`. Rewrite dash.sthlp :1783-1784 (marker labels "in its display format" without the qualifier; `mlabformat()` takes any numeric display format), :2361 (date-axis ticks in the variable's format), :2441-2461 (tooltips in the variable's format), :862-866 (a float-stored number is written with its float32 digits); read :1109-1138 as section 17's task 17-06 left it and confirm it holds the sentence of TR-12.12 -- if it does not, stop and report to the merger (section 17 owns that paragraph; do not rewrite it). Grep `test/test_help_claims_*.py` and `test/test_help_claims_*.cscript` for the changed sentences and update any pin. In `CHANGELOG.md` replace, in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01 placed the markers there, D2), the marker `<!-- WP-28 E3 -->` with ONE line ending `(WP-28, E3)` quoting the recorded old values from `<scratch>/12-01-failure.txt` and `12-02-failure.txt`: a `%td` dropdown `2001-12-31 00:00:00` → `31dec2001`; a `%9.0fc` dropdown `3799` → `3,799`; a `%tm` slider stepping days → months; a `%tC` tooltip's time dropped → kept; a `%tm` axis `Jan 2000` → `2000m1`; two values with one display text listed twice → once; and the marker `<!-- WP-28 G6 -->` with ONE line ending `(WP-28, G6)`: a float 0.1 marker label and dropdown `0.10000000149011612` → `.1`; a tooltip `1.235e+4` → `12345.67`; `mlabformat(%9.3g)` named → applied; the CSV's float digits. Write nothing under any other heading. Run the section's one full pytest run in the worktree (`python3 -m pytest test/ -q`; a pin it exposes that no flip task listed is flipped in the flip task owning that file before continuing); grep the three files and the message for `claude|anthropic`; commit the whole section on the worktree branch `wp28-s12` as ONE commit, subject ending `(GAPS2 E3, G6)`, body opening with the two saved failure texts and carrying the `Regression:` / `Flipped:` (from `<scratch>/12-flips.txt`) / `BUGS.md: "<title>" (closed)` lines, one per entry (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes (both entries parse, name existing tests, no open S1/S2 entry); `grep -c '<!-- WP-28 E3 -->\|<!-- WP-28 G6 -->' CHANGELOG.md` prints 0, `grep -c '(WP-28, E3)' CHANGELOG.md BUGS.md` prints 2 and `grep -c '(WP-28, G6)' CHANGELOG.md BUGS.md` prints 2; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 E3, G6)'` prints 1.]]></verify>
  <done>E3 and G6 were closed in BUGS.md naming their tests, the help described each site's format rule, both CHANGELOG markers were replaced by lines with the recorded old values, and one green commit on `wp28-s12` carried the section.</done>
</task>

## Section completion criteria

- Every site in report B §1.3 rows 4-14 writes Stata's display text through the section
  04 writer in both modes; the period kinds filter over Stata's period numbers with both
  masks agreeing; dropdown values sharing one display text are one entry that selects
  them all; formatter models are cached per document.
- `_datetime_formatter_for`, `_format_date_value_standalone`, `_stata_numeric_pattern`,
  `_parse_stata_numeric_fmt`, `_format_stata_numeric`, `_mlabel_date_texts` and
  `_format_date_value` are gone and the test map is current; the four new functions sit
  in the copy list after `"_dash_hover_row"`.
- One commit on `wp28-s12`, subject ending `(GAPS2 E3, G6)`, holding the failing tests,
  the fix, the flips and the two closed BUGS.md entries; no test-only commit exists (D1).
- The full pytest suite is green with no skips; every flipped test is recorded as a
  `Flipped:` line; the label-sink pattern admits `{custom}` only with a formatter carrying
  the format in args; every `_MUST_WARN` key still names a corpus case.
- BUGS.md carries E3 and G6 closed in the D3 form; dash.sthlp is updated and :1109-1138
  holds section 17's sentence; both CHANGELOG markers are replaced by lines ending
  `(WP-28, E3)` and `(WP-28, G6)`.

## Notes

- **Batch 3 on the merged batch-2 tree.** Sections 14, 16 and 17 have merged when this
  section starts, so every edit here is made to the merged text: `_dash_filter_widget`,
  `_dash_frame_filter_mask`, `_DASH_FILTER_MASK_JS`, `_build_filter_widgets` and the
  `filter_specs_json` dict as section 17 left them (values, `numeric`, `groups`, `use`)
  and section 14 (lookups); `_apply_colorvar`/`_dash_colorvar_bins` as section 16 left
  them; `_dash_hover_row`/`_dash_build_hover`/`_dash_apply_axis_spec`/`_dash_facet_label`/
  `_dash_csv_meta` as section 14 left them. Merge order inside batch 3 is S18, S15, S11,
  S12: this section's diff is applied last (rule R2); S18's `_dash_apply_axis_spec` hunks
  are disjoint from the `format()` branch.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression:
  test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>` (the run was made on the
  post-batch-2 tree; the symptom is 91d97be's), `Flipped: <node>
  -- <old expectation> was wrong because <why>` (one per flip), `BUGS.md: "<title>"
  (closed)` (one per entry); no `Fixture:` line (this section regenerates none).
- **Shared registries (rules R1-R6).** R1: no cscript here. R2: the four new functions go
  after `"_dash_hover_row"` in the served function tuple and in alphabetical place in
  `function_test_map.py`; the merger resolves append conflicts. R3: BUGS.md is appended
  at the end, only the E3 and G6 markers are replaced in CHANGELOG, dash.sthlp
  :1109-1138 belongs to section 17 (verify only). R5: `axis_truth.json` is read, never
  regenerated here. R6: `CORPUS` entries are re-profiled and the one `_MUST_WARN` entry
  this section's gap silences (`mlabformat`) is changed with its key kept; `ALLOWED` is
  never edited.
- **Why the CSV keeps ISO dates and shortest doubles.** PRD §4 lists the CSV among the
  sites; dash.sthlp:862-866 documents a re-importable file with ISO dates and shortest
  round-trip numbers, and GAPS2 E3 names no CSV site; G6's CSV symptom is the float
  expansion. This section therefore changes only the float-storage digits. If the
  maintainer wants display-format text in the CSV (Stata's `export delimited, datafmt`),
  that is a documented behaviour change for a later package, not a gap closure.
- **Ticks are placed elsewhere.** The formatter only writes text for the positions
  Bokeh's ticker (or `_dash_tsnatscale_ticks`, section 14/18) chooses; on a `%tm` axis a
  tick at a mid-month position floors to the month. twoway's `%tm` axis-label truth (E3
  plan step 4) is section 14's probe pair `e3_tm_axis`/`e3_tm_axis_lab`, read by
  `TestDateAxis`; nothing is handed over in a commit message.
- **Section 14's explicit-label formatter.** `xlabel(1 "text")` sets a
  `CustomJSTickFormatter` at :16786-16796 whose fallback is `String(tick)`; it is section
  14's and is not merged with this section's formatter; no shared code string is exposed
  (no section consumes one).
- **`args` strings.** The existing override formatter passes `json.dumps(labels)` as an
  `args` string; a bare string in `args` is accepted (AnyRef). Never put the format in
  `code`.
- **Models per document.** A `CustomJSTickFormatter` shared by several axes/sliders in
  one document is fine; sharing across served sessions is not. The cache lives per
  render/`make_document`.
- **Period sliders and exclusion.** `_dash_excluded` and the per-target masks (section
  17/E2) read widget values through `_dash_frame_filter_mask`; the unit conversion lives
  inside that function, so E2's per-target masks inherit it.
- **Groups by label.** Section 17's masks select by group membership, so this section
  never compares display text in a mask: it only decides which values share an entry.
  Two values with one label but different value labels cannot occur (the label set wins
  before formatting).
- **`_whole_number_step` stays** for numeric columns; period sliders bypass it with
  `step=1`.
- **Tooltip fallback.** Computed columns (`top`, `left`, fit `y`) keep
  `_tooltip_precision`; only variables get `{custom}`; a value-labelled `hover()` variable
  keeps section 14's text column, unformatted.
- **Line numbers** are 91d97be's, shifted by batch 2 (sections 04, 14, 16, 17) and by
  section 11 and 18 in batch 3; symbols are authoritative.
- **Stata sessions.** None in this section (no cscript, no extract script).
