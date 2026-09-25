# Section 12: Widgets, tooltips, date axes, marker labels, CSV

> Part of: WP-28 · Gaps: E3, G6 · Risk: red · Batch: 3 · Depends on: 03, 04, 14, 16, 17 · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **3** · Depends on **03, 04, 14, 16, 17** · Blocks **19** · Risk **red** · Commits: two commits: E3 and G6 → CHANGELOG `Results that change`

- D4: builds on S14's `_dash_build_hover`/`_dash_hover_row` signatures (value labels), S16's colour-key label site and S17's dropdown VALUES; edits dash.sthlp 1109-1128 after S17.
- D10: the E3 `%tm` axis-label truth is a probe in S14's table (S14 records it; this section consumes it by its probe id).
- Q26: dropdown labels are deduplicated by display text — two values with one display text become ONE entry, and the mask (S17's rule) matches every value whose display text equals the entry's, in both modes.
- Stubs: period sliders on empty and single-value columns; a `%tC` tooltip keeps its time.
- D7: split 12-01, 12-04, 12-05, 12-06.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

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
the variable's full display format — `%8.0gc` on a dropdown, `2000m1` on a %tm axis tick,
`09jan2002` in a tooltip, `%tdCCYY-NN-DD` honoured wherever the variable's picture is —
in the saved page (JavaScript, through `CustomJSTickFormatter` and `CustomJSHover`
carrying the format in `args`) and in the served app (the same functions, copied). The
five period kinds (%tw %tm %tq %th %ty) get a numeric slider over Stata's period number
with step 1, and both masks convert the column the same way. A float-stored variable
writes its float32 digits in the CSV. Dates in the CSV stay ISO 8601 as dash.sthlp:862-866
documents (§Notes).

**Test order (CLAUDE.md rule 7): task 12-01 writes every failing test for this section**
and records the failure; 12-02 through 12-07 turn the sites green one at a time; 12-08 to
12-10 flip the pinned tests; 12-11 closes E3 and G6.

## Risk: [red] — eleven sites in two renderers, two of them shared with sections 16 and 17 in the same batch, and five widget/mask changes that alter which rows a filter keeps

**Why.** Each site has a saved and a served entry point; the widget change alters the
value space a slider works in (period numbers instead of milliseconds), which the masks,
the exclusion rule and the CSV button all read.

**Risk factors.** (1) `_dash_filter_widget`, `_DASH_FILTER_MASK_JS` and
`_dash_frame_filter_mask` are also edited by section 17 (dropdown branches) in this
batch. (2) `_apply_colorvar` is rewritten by section 16 in this batch. (3) A
`CustomJSTickFormatter`/`CustomJSHover` per axis, slider and field would embed the
writer many times per page. (4) Bokeh models cannot be shared across served sessions.
(5) A tooltip field with `{custom}` fails `test_label_sinks.py`'s field pattern.

**Mitigation.** (1) This section edits only the slider/range branches and the label
sites of those three functions, named by line in the tasks, so `patch -p1` merges; S17's
diff lands first when both are ready. (2) The colorvar edit is two label expressions
(`_vlookup`'s fallback and the cut labels); it is the last code task and rebases on
S16's diff. (3) One formatter model per distinct `(format, kind, storage)` triple,
cached per document. (4) The cache is a dict created inside `make_document`. (5) The
pattern is widened deliberately and a test asserts every `{custom}` field has a
formatter whose `args` carry the format.

## Dependencies

- Depends on: section 04 (the writer, `_DASH_FMT_JS`, `dash_stata_value_of`,
  `self.formats`/`_FORMATS`, `storage_types`, `format_truth.json`); section 03 (the
  stateful node runner, for the period-slider mask parity test; a single move suffices).
- Blocks: section 19.
- Parallel batch: 2, with S11, S13, S14, S15, S16, S17. Merge order inside the batch:
  S17 and S16 before this section's tasks 12-03 and 12-06 respectively (§Notes).

## Evidence

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
option text (`0.10000000149011612`, `5e-05`). The option **value** (`rv`) is section 17's.
The signature (:17547-17548) takes `date_kind` only; both callers (saved
`_build_filter_widgets`; served :26703-26706) pass no format.

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
The masks: `_dash_frame_filter_mask` range/slider branches (:13989-14008) compare
`_dash_float_values(df[wvar])` (epoch ms for a date) with the widget's value; the JS twin
(:14141-14160) compares `col[i]` with `w.value`. The filter spec JSON (:23707-23714)
carries `varname`, `type`, `sentinel`; the served callback reads widgets' `_dash_var`,
`_dash_exclude` (:26719-26720).

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
`format` and its `args` (W §1d). The fallback for computed columns is
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
`_stata_numeric_pattern` gives a pattern (:16800-16810) — `%f` only.

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

### by() panel titles — `_dash_facet_label`, :15549-15615

```python
15599        _kind = date_vars.get(var)
15600        if _kind and date_formatter is not None:
15601            parts.append(date_formatter(val, _kind))
```

with `_dash_stata_date_text(value, kind)` (:15618-15645) in both modes (saved :21754
`_format_date_value`; served :26547-26550). `numeric_formats` is "accepted and not read".

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
(:166-171) pins `1e-7`, `123456789012`, `1e+21`.

### colorvar key labels — `_apply_colorvar`, :6407-6420 and :6467-6488

```python
6418            return vlabels.get(key, f"{v:g}")
...
6467                        if lo_b is None:
6468                            labels.append(f"≤{hi_b:g}")
```

Python's `:g` (six significant digits); section 16 rewrites the surrounding logic.

### Stata's rules

Report D §8b (dates, default pictures, codes) and §8a (numeric) as section 04 cites them;
the writer is section 04's and the truth is `format_truth.json`. For the period kinds
Stata's slider analogue is the period number itself (`%tm` 480 is 2000m1; the fixture's
`date_formats` rows give each number's text). twoway labels a date axis in the variable's
format (GAPS2 G10; dash.sthlp:2361 "On a date axis a number is a date in the variable's
own units").

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
  (:1187-1200) reads the row helper's signature → updated.
- Date axis: `test/test_dates.py::TestDatetimeAxis::test_a_date_x_variable_gets_a_datetime_axis`
  (named by `function_test_map.py` for `_datetime_formatter_for`) → asserts a
  `CustomJSTickFormatter` whose node output for a tick equals the fixture text.
- Numeric axis: `test/test_axis_options.py::…::test_format_suboption_reaches_the_tick_labels`
  and `::test_format_with_explicit_ticks_together` (:176-190, `NumeralTickFormatter`,
  `","` in `fmt.format`) → `CustomJSTickFormatter` with `args["fmt"] == "%9.0fc"` and node
  output `4,099` for 4099; `test/test_help_claims_7.py:255-262` reads `fmt.format` when
  `NumeralTickFormatter` else the type name → reads `args["fmt"]`;
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
  case; `abc`, `%td`, `%12s` stay named); `test/test_mode_parity.py::_MUST_WARN`
  "a format mlabformat() cannot reproduce" (:1444) → the CORPUS entry's format becomes
  `%12s` so it still warns, or the entry is removed with its CORPUS case.
- Facet titles: `test/test_help_claims_5.py:519-522` (`"01 Jan 2000"` both modes),
  `::TestTheFacetLabelHelper::test_a_date_goes_through_the_formatter` (:565-573),
  `::TestTheStataDateText::test_each` (:580-591) → `01jan2000`, `2000m1`, `2000`,
  `01jan2000 00:00:00`; `test/test_date_range.py:582, 652` (`"02 Jan 2001"`, `"31 Dec
  9999"`) → `02jan2001`, `31dec9999`; `test/test_served_dates.py::…::test_a_by_graph_over_dates`
  (:207) likewise.
- Dates test: `test/test_date_range.py::…::test_the_date_formatter` (:944-961) and
  `::test_the_date_formatter_writes_a_number_past_the_range_as_itself` pin
  `_format_date_value_standalone` → rewritten against `_dash_stata_date_text(value,
  "%td")` with Stata's text; `test/test_help_claims_5.py::TestTheStataDateText` likewise.
- CSV: `test/test_export.py::TestTheCsvFormatter::test_a_number_is_javascripts_shortest_spelling`
  (:166-171) → `dash_csv_number(v, storage)` with the same double cases plus float cases;
  `::test_csv_meta` (:548) → the meta gains `storage`.
- Colorvar: `test/test_colorvar_legend.py` assertions on `:g` labels, if any (grep
  `labels` there) → the variable's format; coordinate with section 16.
- `test/test_dates.py::TestNumericDisplayFormats::test_a_bokeh_tick_pattern_is_produced`
  (:480) and `::test_a_format_dash_does_not_reproduce_returns_none` (:488) and
  `test/test_adversarial_matrix.py::TestNumericFormatBounds::test_the_formats_stata_accepts_still_parse`
  (:1675) pin `_stata_numeric_pattern`/`_parse_stata_numeric_fmt` → rewritten against
  `_dash_fmt_parse`/`_dash_fmt_kind` when those two are retired (task 12-06).

## User stories

- **US-12.1** As a dashboard viewer, I want a dropdown over a `%td` variable to list
  `31dec2001` and one over auto's price to list `4,099`, so the widget reads as the data
  does in Stata.
- **US-12.2** As a dashboard viewer, I want a `%tm` range slider to step one month at a
  time and read `2000m1 .. 2019m12`, so I never stop mid-period.
- **US-12.3** As a dashboard viewer, I want a tooltip over a `%tc` variable to show its
  time and one over `%8.0gc` price to show `4,099`, in both modes.
- **US-12.4** As a Stata user, I want a `%tm` axis to read `2000m1` where twoway does, and
  `xlabel(, format(%9.0fc))` to draw `4,099`, in both modes.
- **US-12.5** As a Stata user, I want marker labels, `mlabformat(%9.3g)` and by() panel
  titles of a date variable written as Stata writes them, and a float-stored 0.1 labelled
  `.1`, not `0.10000000149011612`.
- **US-12.6** As a dashboard viewer downloading the CSV, I want a float-stored variable
  written with its float32 digits (`0.1`), so the file reads as Stata's data does.

## Business requirements

- **BR-12.1** A dropdown's option labels are the variable's value labels where they exist,
  else Stata's `display` text for the variable's format; the option values are unchanged.
- **BR-12.2** A slider or range slider's labels are Stata's `display` text for the
  variable's format; a `%tw/%tm/%tq/%th/%ty` slider moves over Stata's period numbers in
  steps of 1 and keeps exactly the rows whose period number is within its bounds; a
  `%td`/`%tc`/`%tC` slider is unchanged in behaviour and labelled in the variable's format.
- **BR-12.3** A tooltip row for a variable shows Stata's `display` text for its format;
  computed columns keep their spread-based precision.
- **BR-12.4** A date axis's tick labels are Stata's `display` text for the variable's
  format at each tick; an explicit `format()` on a numeric axis is honoured for every
  writable format.
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
  copy list and `function_test_map.py`:
  `_dash_fmt_tick_formatter(fmt, kind, storage, cache)` returning a
  `CustomJSTickFormatter(code=_DASH_FMT_JS + "\nreturn dash_fmt_text(kind ?
  dash_stata_value_of(tick, kind) : tick, fmt, storage);", args={"fmt": fmt or "%9.0g",
  "kind": kind or "", "storage": storage or ""})` and `_dash_fmt_hover(fmt, kind,
  storage, cache)` returning the same as a `CustomJSHover` over `value`. `cache` is a
  dict keyed by `(fmt, kind, storage)`; the saved renderer holds `self._fmt_models = {}`
  per render, the served template creates `_fmt_cache = {}` inside `make_document` (a
  Bokeh model belongs to one document). The format is always in `args`, never in `code`.
- **TR-12.2 Dropdown labels.** `_dash_filter_widget(ftype, varname, column, title,
  value_labels=None, date_kind="", max_options=None, fmt="", storage="")`: `_label(rv)`
  returns `vlabels[rv]` when present, else for a date `_dash_fmt_text(_dash_stata_value_of(ms,
  date_kind), fmt)`, else `_dash_fmt_text(float(rv), fmt or "%9.0g", storage)` when `rv`
  parses as a number, else `rv`. Both callers pass `fmt=formats.get(var, "")` (saved
  `self.formats`, served `_FORMATS`) and `storage=storage_types.get(var, "")`. The
  option value is untouched (section 17).
- **TR-12.3 Sliders.** Numeric and `%td`/clock sliders keep their widget classes and
  steps and gain `format=_dash_fmt_tick_formatter(fmt, kind, storage, cache)`. Period
  kinds (`date_kind in ("tw", "tm", "tq", "th", "ty")`): `RangeSlider`/`Slider` with
  `start`/`end` the min/max of `_dash_stata_value_of` over the column, `value` the same,
  `step=1`, the formatter as above with `kind=""` (the value is already a period number),
  `w._dash_is_date = True`, `w._dash_unit = date_kind`. The saved filter spec (:23707-23714)
  gains `"unit": getattr(_w, "_dash_unit", "")`; `_dash_frame_filter_mask`'s range and
  slider branches convert `col` with `_dash_stata_value_of` vectorised (`np.vectorize`
  over `_dash_unix_ms_to_unit` is acceptable; a missing value stays NaN) when
  `getattr(w, "_dash_unit", "")`; `_DASH_FILTER_MASK_JS`'s range and slider branches
  read `spec.unit` and compare `dash_stata_value_of(col[i], spec.unit)` (null → the row
  is dropped, as a missing value is today). `_date_slider_step_days` keeps serving `td`.
  `_at_full_extent` works unchanged on period numbers.
- **TR-12.4 Tooltips.** `_dash_hover_row(col, label, fmt="", kind="", storage="",
  cache=None)` returns `((label, f"@{{{col}}}{{custom}}"), (f"@{{{col}}}",
  _dash_fmt_hover(fmt, kind, storage, cache)))` for a variable with a writable format
  or a date kind, else `((label, f"@{{{col}}}"), None)`; `_dash_build_hover` gains
  `formats=None, storage_types=None, fmt_cache=None`, builds `formatters` from the
  returned pairs, and both call sites (:22348, :26451) pass them. The served app's
  import list (:25236-25262) gains `CustomJSHover` and `CustomJSTickFormatter`.
  `test_label_sinks.py` `_PLACEHOLDER` becomes
  `r"@\{[^\W\d]\w*\}(?:\{(?:[0-9.,%FT ]+|custom)\})?"` and a new test asserts every
  `{custom}` field maps to a `CustomJSHover` whose `args["fmt"]` is a string and whose
  `code` does not contain that string.
- **TR-12.5 Axes.** `_dash_date_axis_formatter(fmt, storage, cache)` =
  `_dash_fmt_tick_formatter(fmt, _stata_date_kind(fmt), storage, cache)`; the saved site
  (:22029-22034) and the served site (:26198-26200) call it with the axis variable's full
  format (`self.formats[var]` / `_FORMATS[var]`; the variable is the one whose kind set
  `_x_date`/`_y_date`). `_dash_apply_axis_spec` (:16800-16810): when
  `_dash_fmt_kind(fmt) in ("f", "g", "e")` set `_dash_fmt_tick_formatter(fmt, "", "",
  cache)`; a date `format()` on a numeric axis keeps today's behaviour; an unwritable
  explicit format keeps the warning. `_datetime_formatter_for` is deleted;
  `_stata_numeric_pattern` is deleted once no caller remains. The explicit-label
  formatter at :16786-16796 is section 14's; do not merge the two (§Notes hand-off).
- **TR-12.6 Marker labels.** In `_apply_mlabel_opts` the date branch becomes
  `["." if m else _dash_fmt_text(_dash_stata_value_of(v, _kind), _fmt) …]` with `_fmt =
  self.formats-equivalent` — the mapper holds `date_vars` (kind) and `numeric_formats`;
  add `mapper.formats` (full map) through `_dash_attach_labels(formats=None)` so the
  picture is available; the numeric branch uses `_dash_fmt_text(v, _numfmt,
  self.storage_types.get(var))`; the no-format branch uses `_dash_fmt_text(v, "%9.0g",
  storage)` (Stata's default for a variable with no format is its type's default:
  `%9.0g` float, `%10.0g` double, `%8.0g` int/byte, `%12.0g` long — a variable always
  carries a format from `st_varformat`, so this branch is reached only by hand-edited
  specs; use `%9.0g`). `_mlabformat_column` gates on `_dash_fmt_kind(fmt) in ("f", "g",
  "e")` and writes with `_dash_fmt_text`; a date variable keeps its note for a numeric
  `mlabformat` (§Boundaries). `_mlabel_date_texts` is deleted.
- **TR-12.7 Facet titles.** `_dash_stata_date_text(value, fmt)` takes the full format
  (kind from `_stata_date_kind(fmt)`) and writes `_dash_fmt_text(_dash_stata_value_of(ms,
  kind), fmt)`; `_dash_facet_label` gains `formats=None` and calls
  `date_formatter(val, formats.get(var) or "%" + _kind)`; both callers pass the full map;
  `DashRenderer._format_date_value` and `_format_date_value_standalone` are deleted.
- **TR-12.8 CSV.** `_dash_csv_meta` gains `"storage": {var: type}` from a new
  `storage_types` argument (both callers: :23855, :27090); `dash_csv_cell` passes
  `storage[j]` to `dash_csv_number(v, storage)`, which returns `dash_float32_text(v)`
  when `storage === "float"`, else today's `String(v)` with the `-0` rule. Dates stay
  `dash_csv_date`. `_DASH_FMT_JS` is already in both CSV scripts (section 04).
- **TR-12.9 Colorvar labels.** `_vlookup`'s fallback and the four cut-label expressions
  use `_dash_fmt_text(v, self.numeric_formats.get(varname, "%9.0g"),
  self.storage_types.get(varname))`. Nothing else in `_apply_colorvar` changes.
- **TR-12.10 Both renderers.** New/changed module functions in the function copy list;
  `_dash_hover_row`, `_dash_build_hover`, `_dash_filter_widget`, `_dash_facet_label`,
  `_dash_stata_date_text`, `_dash_csv_meta` are already copied; the served template's
  call sites listed above change; `function_test_map.py` gains
  `_dash_fmt_tick_formatter`, `_dash_fmt_hover`, `_dash_date_axis_formatter` and loses
  `_datetime_formatter_for`, `_format_date_value_standalone`, `_stata_numeric_pattern`,
  `_parse_stata_numeric_fmt`, `_format_stata_numeric` (once its last caller moves),
  `DashRenderer._format_date_value`, `GlyphMapper._mlabel_date_texts`.
- **TR-12.11 Security.** Formats reach BokehJS only as `args` values; option labels are
  text nodes (the comment at :17611-17616), slider titles and axis ticks are canvas or
  `textContent`, `LabelSet` text is canvas, tooltip values are inserted as text by
  BokehJS, the CSV cell is quoted and guarded as today, the facet title reaches a KPI
  card that escapes it. No new HTML sink is created.

## Boundaries

- Not the KPI card (section 11); not `_dash_option_value`, `_dash_dropdown_values`, the
  dropdown branches of either mask, or the exclusion rule (section 17); not
  `_apply_colorvar`'s cut logic, levels or gray rule (section 16); not tick *placement*
  on date or numeric axes (`_dash_tsnatscale_ticks`, section 14/18) nor the default axis
  format for a variable with no `format()` (GAPS2 G10, out of scope); not the explicit
  `xlabel(1 "text")` formatter (section 14).
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
- BUGS.md entries for E3 and G6 land closed in task 12-11's commit.

## Stata truth

None added. Every text this section writes is a `display` output already pinned by
section 04's `format_truth.json` (`numeric_formats`, `date_formats`) and by
`date_truth.json`; the tests assert the site's text equals `_dash_fmt_text` of the value
under the variable's format, and `_dash_fmt_text` is held to Stata by section 04. The
one twoway-drawn truth E3's plan names — the axis label text of a `%tm` variable — is
tick text at positions section 14/18 own; §Notes hands it to section 14's extract script
(one `%tm` probe), where the SVG helper of section 02 exists. Stata invocation, if a
cscript is added for the served widgets: rule 10's console command with its own
`STATATMP=<dir>/tmp/`.

## TDD test stubs

All in **`test/test_display_format_sites.py`** (new, task 12-01) unless noted; both-mode
helpers from `test/test_mode_parity.py` (`_standalone`, `_served`, `_spec`); the node
runner from `test/test_export.py` (`_run_js`) and section 03's stateful runner for the
slider-move case; auto from `test/fixtures/data/auto.csv` with `when` (`%td`), `whenm`
(`%tm`, 2000m1..2000m3), `whenq` (`%tq`), `whenc` (`%tc`), `f` (a float32-rounded
`price/7`, storage `float`). Each stub names its pre-fix failure.

- Test: `TestDropdown::test_labels_are_statas_text_in_both_modes` — dropdowns over
  `price` (`%8.0gc` → `4,099`), `when` (`%td` → `02jan2000`), `whenm` (`%tm` → `2000m1`),
  `f` (float → `.1`-style digits, `%9.0g`); values unchanged (compare to
  `_dash_option_value`). Pre-fix: `4099`, `2000-01-02 00:00:00`.
- Test: `TestDropdown::test_a_value_label_still_wins` — `foreign` with labels.
- Test: `TestSliders::test_numeric_and_td_sliders_carry_a_stata_formatter` — the
  `RangeSlider`/`DateRangeSlider` `format` is a `CustomJSTickFormatter` with
  `args["fmt"]` the variable's format; under node `format.code` on `value=4099` → `4,099`
  and on the `%td` slider's start (ms) → `02jan2000`. Pre-fix: `format == "0[.]00"`.
- Test: `TestSliders::test_period_kinds_are_numeric_sliders_over_period_numbers` —
  `whenm` range: `RangeSlider`, `start == 480`, `end == 482`, `step == 1`, formatter
  gives `2000m1`; `whenq`, `%th`, `%ty`, `%tw` likewise; `w._dash_unit` set; the saved
  filter spec holds `unit`. Pre-fix: `DateRangeSlider`.
- Test: `TestSliders::test_the_masks_agree_on_a_period_slider_in_both_modes` —
  `whenm` range set to `(481, 481)`: pandas mask (`_dash_frame_filter_mask`) equals the
  node mask (section 03's runner, one move) equals the rows whose month is February;
  a missing `whenm` row is dropped once moved and kept at full extent.
- Test: `TestSliders::test_a_period_move_reaches_a_card_and_a_graph` — after the move
  the graph source holds the February rows and a `count(price)` card reads their count,
  saved (node) and served.
- Test: `TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` — the
  HoverTool of a `scatter price when` figure has `("price", "@{price}{custom}")`,
  `("when", "@{when}{custom}")`, `formatters["@{price}"]` a `CustomJSHover` with
  `args["fmt"] == "%8.0gc"`, `"@{when}"` with `"%td"`, `code` not containing `%8.0gc`;
  under node the hover code on 4099 → `4,099`, on `when`'s ms → `02jan2000`; a `%tc`
  variable keeps its time; both modes. Pre-fix: `@{when}{%F}`.
- Test: `TestTooltips::test_one_formatter_model_per_format_triple` — three figures over
  `price` and `when`: the document holds exactly two `CustomJSHover` models (+ the
  computed-column ones, which are not `CustomJSHover`).
- Test: `TestTooltips::test_the_label_sink_pattern_admits_custom_only_with_a_formatter`
  (in `test/test_label_sinks.py`): every `{custom}` field has a formatter; no other
  `{…}` form appears but the numeric/date ones.
- Test: `TestDateAxis::test_ticks_read_as_stata_in_both_modes` — `line price when`:
  `fig.xaxis[0].formatter` is a `CustomJSTickFormatter` with `args["fmt"] == "%td"`, and
  its code under node on the ms of 02jan2000 → `02jan2000`; `%tm` → `2000m1`; `%tc` with
  a time; `%tdCCYY-NN-DD` honoured; `%ty` → `2000`. Pre-fix: `DatetimeTickFormatter`.
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

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Dropdown labels | pytest | format_truth.json (via `_dash_fmt_text`) | yes |
| Slider formatters; period sliders; masks agree | pytest + node (S03 runner) | none | yes |
| Tooltips: fields, formatters, args, node output, one model per triple | pytest + node | none | yes |
| Date-axis ticks and numeric `format()` | pytest + node | format_truth.json | yes |
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
- **AC-12.2** Every pinned test in §Evidence is flipped, none deleted, each named in a
  commit message with old and new text.
- **AC-12.3** The full pytest suite is green; `TestTheServedAppCarriesEveryName` and
  `TestTheServedAppDefinesEveryNameItReads` pass; `test_mode_parity.py` CORPUS profiles
  are equal between modes.
- **AC-12.4** BUGS.md carries E3 and G6 closed naming their tests; dash.sthlp :1110-1128,
  :1783-1784, :2361 and the CSV paragraph are updated; CHANGELOG lists every changed text.

## Tasks

<task type="auto" id="12-01">
  <name>Write the failing tests for every site</name>
  <files>test/test_display_format_sites.py (new), test/test_label_sinks.py</files>
  <action>
    Create `test/test_display_format_sites.py` with the helpers §TDD stubs name (import
    `_standalone`, `_served`, `_spec` from `test_mode_parity`; `_run_js` from
    `test_export`; the stateful runner from section 03's module; build the auto frame with
    `when`, `whenm`, `whenq`, `whenc`, `f`), and write every test in §TDD stubs with
    exactly those names; skip only when node is absent and assert in a module test that
    node tests ran. In `test/test_label_sinks.py` add
    `TestTooltips::test_the_label_sink_pattern_admits_custom_only_with_a_formatter` (it
    fails now because no `{custom}` field exists — write it to assert at least one such
    field per figure over a variable with a format, so it is not vacuous). Do not touch
    dash_render.py. Run both files against the post-section-04/03 tree and paste the
    failure summary (`2000-01-02 00:00:00`, `DateRangeSlider`, `@{when}{%F}`,
    `DatetimeTickFormatter`, `0.10000000149011612`) into the commit message.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_sites.py -q 2>&1 | tail -5` reports 0 passed, no collection error, failures with the old text rather than exceptions where a site exists today.]]></verify>
  <done>Every regression test of this section exists and fails for the recorded reason.</done>
</task>

<task type="auto" id="12-02">
  <name>Format dropdown and slider labels through cached formatter models</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Add `_dash_fmt_tick_formatter`, `_dash_fmt_hover` (TR-12.1) beside the section 04
    writer functions and to the function copy list. Extend `_dash_filter_widget` with
    `fmt=""`, `storage=""`, `fmt_cache=None` (TR-12.2, TR-12.3 for the non-period
    branches: every `RangeSlider`, `Slider`, `DateRangeSlider`, `DateSlider` and
    `DatetimeRangeSlider` gets `format=_dash_fmt_tick_formatter(...)`, kind `""` for a
    numeric column and the date kind for a date one). Pass the new arguments from the
    saved `_build_filter_widgets` (`self.formats`, `self.storage_types`, `self._fmt_models`)
    and from the served call (:26703-26706: `_FORMATS`, `_storage_types`, `_fmt_cache`,
    created at the top of `make_document`). Add the served imports `CustomJSHover`,
    `CustomJSTickFormatter` (:25236-25262). Do not touch the period-kind branch, the
    dropdown option values or the masks yet.
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k "TestDropdown or numeric_and_td_sliders"` passes; `python3 -m pytest test/test_filter_widget_data.py test/test_saved_filter_layers.py -q` shows only the `2001-12-31 00:00:00` pin failing (flipped in 12-08).</verify>
  <done>Dropdown labels and every slider label read as Stata's display text in both modes, from one cached formatter model per format.</done>
</task>

<task type="auto" id="12-03">
  <name>Move the period kinds onto numeric sliders and teach both masks the unit</name>
  <files>dash_render.py, test/test_filter_slider_step.py</files>
  <action>
    Implement TR-12.3's period branch in `_dash_filter_widget` (after the clock branch,
    before the `elif is_date` `td` branch), the `unit` field in the saved filter spec
    (:23707-23714), the conversion in `_dash_frame_filter_mask`'s range and slider
    branches (:13996-14008; leave the dropdown branch to section 17), and in
    `_DASH_FILTER_MASK_JS`'s slider and range branches (:14141-14160; leave the dropdown
    branch alone). Add a helper `_dash_period_values(column, unit)` (vectorised
    `_dash_stata_value_of`, NaN for missing) to the function copy list and the test map.
    Flip `test_filter_slider_step.py` (:180-215): the `tw/tm/tq/th` cases assert a
    `RangeSlider` with `step == 1` and `start/end` the period numbers; the `td` case and
    the monthly-series test's span assertion move to the period domain (`2010m1..2019m12`
    is 119 periods, step 1). If section 17's diff has landed, rebase this task's mask
    edits on it; if not, keep the dropdown branches byte-identical so its patch applies.
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k TestSliders` passes (pandas and node masks agree on one move; a card and a graph follow); `python3 -m pytest test/test_filter_slider_step.py test/test_export.py test/test_filter_exclude.py -q` passes.</verify>
  <done>A %tw/%tm/%tq/%th/%ty filter is a step-1 slider over Stata's period numbers, labelled in the variable's format, and both masks keep exactly the rows in its bounds.</done>
</task>

<task type="auto" id="12-04">
  <name>Format tooltip rows through CustomJSHover carrying the format in args</name>
  <files>dash_render.py, test/test_label_sinks.py, test/function_test_map.py</files>
  <action>
    Rewrite `_dash_hover_row` and extend `_dash_build_hover` as TR-12.4, building the
    `formatters` dict from the returned pairs and leaving the `_tooltip_precision`
    fallback for computed columns untouched. Pass `formats`, `storage_types` and the cache
    from the saved call (:22348) and the served call (:26451). Widen `_PLACEHOLDER` in
    `test/test_label_sinks.py` deliberately (comment: `{custom}` is admitted only with a
    `CustomJSHover` whose args carry the format). Update
    `test_server_layer_defects.py::TestTheHoverBuilder` only if its calls no longer
    match the signature (record it). Update the test map for `_dash_hover_row` and
    `_dash_build_hover` to this section's tests.
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k TestTooltips` and `python3 -m pytest test/test_label_sinks.py -q` pass; `python3 -m pytest test/test_date_range.py test/test_served_dates.py test/test_help_claims_4.py -q -k "hover or tooltip"` shows only the `@{date}{%F}` pins failing (flipped in 12-08).</verify>
  <done>Every tooltip row for a variable is written by the format writer in both modes, the format travels in args, and the label-sink test admits `{custom}` only with a formatter.</done>
</task>

<task type="auto" id="12-05">
  <name>Write date-axis ticks and numeric format() through the formatter</name>
  <files>dash_render.py, test/function_test_map.py, test/test_axis_options.py</files>
  <action>
    Add `_dash_date_axis_formatter(fmt, storage, cache)` (TR-12.5), use it at the saved
    site (:22029-22034) and the served site (:26198-26200) with the axis variable's full
    format, and change `_dash_apply_axis_spec` (:16800-16810) to set
    `_dash_fmt_tick_formatter` for every f/g/e `format()` (the cache is passed in; the
    saved renderer hands `self._fmt_models`, the served template `_fmt_cache`). Delete
    `_datetime_formatter_for`; delete `_stata_numeric_pattern` if this was its last
    caller (grep), else leave it for 12-06. Flip `test_axis_options.py` (:176-190) to
    assert a `CustomJSTickFormatter` with `args["fmt"]` and node output `4,099`;
    `test_help_claims_7.py:255-262`'s profile reads `args["fmt"]`. Keep the explicit-label
    formatter (:16786-16796) untouched (section 14).
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k "TestDateAxis or TestNumericAxis"` passes; `python3 -m pytest test/test_axis_options.py test/test_help_claims_7.py test/test_adversarial_matrix.py -q` passes except `test_dates.py`'s `DatetimeTickFormatter` pin (flipped in 12-10).</verify>
  <done>Date-axis ticks and explicit numeric formats are Stata's text in both modes, and the fixed per-kind formatter is gone.</done>
</task>

<task type="auto" id="12-06">
  <name>Format marker labels, mlabformat, facet titles and colorvar labels</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Implement TR-12.6 (`_apply_mlabel_opts` branches, `_mlabformat_column` gate and
    writer, delete `_mlabel_date_texts`; add `formats` to `_dash_attach_labels` and both
    callers), TR-12.7 (`_dash_stata_date_text(value, fmt)`, `_dash_facet_label(formats=)`,
    both callers pass the full map; delete `DashRenderer._format_date_value` and
    `_format_date_value_standalone`), and TR-12.9 (the two colorvar label sites —
    **after** section 16's diff has been merged if it is ready; otherwise confine the
    edit to the two expressions so its patch still applies). Delete
    `_parse_stata_numeric_fmt`, `_stata_numeric_pattern` and `_format_stata_numeric`
    once `grep` shows no caller in dash_render.py; leave their tests to 12-10. Make the
    test map current (additions and removals).
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k "TestMarkerLabels or TestFacetTitles or TestColorvarLabels or TestRetired"` passes; `python3 -m pytest test/test_function_test_map.py test/test_statistical_helpers.py -q -k "map or CarriesEveryName"` passes.</verify>
  <done>Marker labels, `mlabformat()`, by() titles and colorvar number labels are Stata's text in both modes, and the fixed-picture and `%f`-only helpers are gone.</done>
</task>

<task type="auto" id="12-07">
  <name>Write float-stored numbers in the CSV with their float32 digits</name>
  <files>dash_render.py, test/test_export.py</files>
  <action>
    Implement TR-12.8: `_dash_csv_meta(columns, formats, string_flags, value_labels,
    value_label_names, filename=…, storage_types=None)` adds `"storage"`; both callers
    (:23855 saved, :27090 served) pass the storage map; in `_DASH_CSV_JS`,
    `dash_csv_number(v, storage)` and `dash_csv_cell(v, is_text, kind, labels, storage)`
    thread it, and `dash_csv_text` reads `meta.storage`. Flip
    `test_export.py::TestTheCsvFormatter::test_a_number_is_javascripts_shortest_spelling`
    to the new signature (same double cases) and `::TestTheHelpers::test_csv_meta` to the
    new key; add float cases. Dates are untouched.
  </action>
  <verify>`python3 -m pytest test/test_display_format_sites.py -q -k TestCsv` and `python3 -m pytest test/test_export.py -q` pass.</verify>
  <done>The CSV writes a float-stored variable as its float32 digits in both modes and everything else as before.</done>
</task>

<task type="auto" id="12-08">
  <name>Flip the pinned tooltip, dropdown and date-range tests</name>
  <files>test/test_date_range.py, test/test_served_dates.py, test/test_saved_filter_layers.py</files>
  <action>
    Flip with a comment naming E3/G6 and this section: `test_date_range.py` :476-478
    `_LABELS`, :582, :609, :652, :790-860 and `test_the_date_formatter` (:944-961,
    rewritten against `_dash_stata_date_text(value, "%td")` etc. with Stata's text and
    `.` for missing); `test_served_dates.py` :129, :207, :229;
    `test_saved_filter_layers.py::TestADateDropdown::test_the_option_labels_still_read_as_dates`
    (`31dec2001`). Record each old/new text in the commit message.
  </action>
  <verify>`python3 -m pytest test/test_date_range.py test/test_served_dates.py test/test_saved_filter_layers.py -q` passes.</verify>
  <done>The date-range, served-dates and saved-filter tests pin Stata's text; none was deleted.</done>
</task>

<task type="auto" id="12-09">
  <name>Flip the pinned facet, marker-label and parity tests</name>
  <files>test/test_help_claims_5.py, test/test_mode_parity.py, test/test_twoway_option_parity.py</files>
  <action>
    Flip: `test_help_claims_5.py` :519-522, :565-573, :580-600 (`TestTheStataDateText`
    takes formats), :1110-1130 (dates as `03jan2000`; the `mlabformat(%9.2f)` note on a
    date variable stays); `test_mode_parity.py::_MUST_WARN` "a format mlabformat() cannot
    reproduce" (:1444) — change the CORPUS case's format to `%12s` so the entry still
    warns, or drop both the entry and the case, and re-profile any CORPUS entry whose
    recorded text changed; `test_twoway_option_parity.py::test_mlabformat_on_a_date_variable_is_named_and_the_dates_kept`
    (`16jan2020`) and `::test_a_format_dash_does_not_reproduce_is_named` (drop `%9.3g`
    from the parametrisation and add `test_mlabformat_g_is_honoured_in_both_modes`).
    Record each old/new text.
  </action>
  <verify>`python3 -m pytest test/test_help_claims_5.py test/test_mode_parity.py test/test_twoway_option_parity.py -q` passes.</verify>
  <done>The facet, marker-label and parity tests pin Stata's text and the honoured `%g`; none was deleted.</done>
</task>

<task type="auto" id="12-10">
  <name>Flip the remaining helper pins and run the full suite</name>
  <files>test/test_dates.py, test/test_adversarial_matrix.py, test/test_help_claims_4.py</files>
  <action>
    Rewrite `test_dates.py::TestNumericDisplayFormats` against `_dash_fmt_text` and
    `_dash_fmt_kind` (the 56 f/fc cases through `_dash_fmt_text`; the tick-pattern test
    becomes a `_dash_fmt_tick_formatter` args test; the "does not reproduce" test
    becomes `_dash_fmt_kind` None/x/H cases) and `TestDatetimeAxis`'s formatter assertion;
    `test_adversarial_matrix.py::TestNumericFormatBounds` against `_dash_fmt_parse` (same
    bounds and timing); `test_help_claims_4.py:1706` (`@{date}{custom}`). Then run
    `python3 -m pytest test/ -q` once; anything still failing that pins an old text is
    flipped with a comment, anything else is a regression of this section: fix the code.
    List every flipped assertion in the commit message.
  </action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no new skips; `python3 -m pytest test/test_resource_limits.py -q -k DefinesEveryName` passes.]]></verify>
  <done>The full suite is green with every re-baselined assertion recorded and the served app defines every name it reads.</done>
</task>

<task type="auto" id="12-11">
  <name>Close E3 and G6 in BUGS.md, help and changelog</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action>
    Append two closed BUGS.md entries with the five fields in order: `- [x] Title: Dates
    and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the
    variable's Stata display format` (Resolution naming
    `test/test_display_format_sites.py::TestDropdown::test_labels_are_statas_text_in_both_modes`,
    `::TestSliders::test_period_kinds_are_numeric_sliders_over_period_numbers`,
    `::TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format`,
    `::TestDateAxis::test_ticks_read_as_stata_in_both_modes` and section 11's card test)
    and `- [x] Title: %g formats (Stata's default) and float storage are not reproduced;
    values show full double expansions` (naming `::TestMarkerLabels::…`, `::TestCsv::…`
    and `test/test_display_format_writer.py::TestPythonWriter::test_every_numeric_display_matches_stata_exactly`).
    Rewrite dash.sthlp: :1110-1128 (dropdown labels in the display format; period sliders
    over Stata's period numbers, step 1), :1783-1784 (marker labels "in its display
    format" without the qualifier; `mlabformat()` takes any numeric display format),
    :2361 (date-axis ticks in the variable's format), :2441-2461 (tooltips in the
    variable's format), :862-866 (a float-stored number is written with its float32
    digits). CHANGELOG "Results that change": a `%td` dropdown `2001-12-31 00:00:00` →
    `31dec2001`; a `%9.0fc` dropdown `3799` → `3,799`; a `%tm` slider stepped days,
    now months; tooltip `%tC` time restored; a `%tm` axis `Jan 2000` → `2000m1`; a float
    0.1 marker label `0.10000000149011612` → `.1`; `mlabformat(%9.3g)` now applied; the
    CSV's float digits. No AI references; grep before and after committing.
  </action>
  <verify>`python3 -m pytest test/test_tracking_documents.py -q` passes (both entries parse, name existing tests, no open S1/S2 entry); `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.</verify>
  <done>E3 and G6 are closed in BUGS.md naming their tests, the help describes each site's format rule, and the changelog lists every text that changed.</done>
</task>

## Section completion criteria

- Every site in report B §1.3 rows 4-14 writes Stata's display text through the section
  04 writer in both modes; the period kinds filter over Stata's period numbers with both
  masks agreeing; formatter models are cached per document.
- `_datetime_formatter_for`, `_format_date_value_standalone`, `_stata_numeric_pattern`,
  `_parse_stata_numeric_fmt`, `_format_stata_numeric`, `_mlabel_date_texts` and
  `_format_date_value` are gone and the test map is current.
- The full pytest suite is green with no skips; every flipped test is recorded; the
  label-sink pattern admits `{custom}` only with a formatter carrying the format in args.
- BUGS.md carries E3 and G6 closed; dash.sthlp and CHANGELOG are updated.

## Notes

- **Merge order in batch 2.** Section 17 edits the dropdown branches of
  `_dash_filter_widget`, `_dash_frame_filter_mask` and `_DASH_FILTER_MASK_JS`; this
  section edits their slider/range branches and the label closure. Section 16 rewrites
  `_apply_colorvar`; this section changes two label expressions in it. Apply S17's and
  S16's patches first where they are ready; otherwise keep those branches byte-identical
  so their patches apply after.
- **Why the CSV keeps ISO dates and shortest doubles.** PRD §4 lists the CSV among the
  sites; dash.sthlp:862-866 documents a re-importable file with ISO dates and shortest
  round-trip numbers, and GAPS2 E3 names no CSV site; G6's CSV symptom is the float
  expansion. This section therefore changes only the float-storage digits. If the
  maintainer wants display-format text in the CSV (Stata's `export delimited, datafmt`),
  that is a documented behaviour change for a later package, not a gap closure.
- **Ticks are placed elsewhere.** The formatter only writes text for the positions
  Bokeh's ticker (or `_dash_tsnatscale_ticks`, section 14/18) chooses; on a `%tm` axis a
  tick at a mid-month position floors to the month. twoway's `%tm` axis-label truth (E3
  plan step 4) is one probe for section 14's extract script through section 02's SVG
  helper: hand it over in the commit message of 12-05.
- **Section 14's explicit-label formatter.** `xlabel(1 "text")` sets a
  `CustomJSTickFormatter` at :16786-16796 whose fallback is `String(tick)`; on a date axis
  that fallback should be the date formatter's code. Expose the code string
  (`_dash_fmt_tick_code(fmt, kind, storage)`) so section 14 can compose it; do not merge
  the two formatters here.
- **`args` strings.** The existing override formatter passes `json.dumps(labels)` as an
  `args` string; a bare string in `args` is accepted (AnyRef). Never put the format in
  `code`.
- **Models per document.** A `CustomJSTickFormatter` shared by several axes/sliders in
  one document is fine; sharing across served sessions is not. The cache lives per
  render/`make_document`.
- **Period sliders and exclusion.** `_dash_excluded` and the per-target masks (section
  17/E2) read widget values through `_dash_frame_filter_mask`; the unit conversion lives
  inside that function, so E2's per-target masks inherit it.
- **`_whole_number_step` stays** for numeric columns; period sliders bypass it with
  `step=1`.
- **Tooltip fallback.** Computed columns (`top`, `left`, fit `y`) keep
  `_tooltip_precision`; only variables get `{custom}`.
- **Line numbers** are section 04/11's post-edit neighbourhood; symbols are authoritative.
- **Stata sessions.** None required by this section's tests; if a cscript is added, cap
  concurrent runs at three and check `c(python_exec)` on any unexpected SKIP.
