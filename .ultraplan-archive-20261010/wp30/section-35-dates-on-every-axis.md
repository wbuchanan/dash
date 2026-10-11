# Section 35: Date positions on every axis (P1.23 part a)

> Part of: WP-30 · Items: P1.23 part a (entry `P1.23a`) · Risk: yellow · Batch: 12 · Depends on: 21, 27 · Blocks: 44, 49, 51, 56, 57 · Tasks: 16, 1 commit · Case prefix: DA

## Review amendments

- Moved the binding readings and section decisions out of this heading into Overview (they are the section's content, not amendments).
- Parity could not see the transform: `test_mode_parity._spec_of` drops `transform`, and both modes keep epoch ms in the source, so a served app without the transform compared equal. 35-03 now appends `TestTheTwoModesAgreeOnDateUnits` (red at base), an off-range literal CORPUS case and a y2-fit MOVE_CORPUS case; every S35 case name starts `P1.23a: ` so `-k P1.23a` selects them.
- After-move coverage closed for every scope item: added `TestRangeAndPcLayersGetADateAxis::test_after_a_filter_move`, `TestABaseOnADateAxis::test_after_a_filter_move`, and the y2 move test now carries the lfit (the redraw's four-kind `_rkinds` path).
- Added `test_function_range_is_in_days[norange]` for `literals.function_norange_td`, which no test or DA case read.
- D-35f: the served note is verified through S23's trial relay before it ships; parity is unaffected because `test_mode_parity._served` captures `make_document`'s warnings in both modes (critic decision 4 vs M6/R8 checked; `ALLOWED`/`_MUST_WARN` untouched).
- TR-35.8: `_dash_date_transform` and `_dash_spec_units` import `CustomJSTransform` locally (copied-function form; no header import exists); the pass names its 13 computed types and reads each renderer's/annotation's range name for the axis.
- TR-35.9/TR-35.15: the plan's `units` is a list of `[field, kind]` pairs, not an object keyed by a variable name (`__proto__` is a valid Stata name).
- TR-35.7: S31's `option`/`by_graph`/`colours`/`ref_in` keywords on the y2/x2 label and tick calls are kept; 35-01's contract records S26, S31, S32 and S33's lines in the functions S35 edits.
- The JS twin test prepends `'use strict';` as BokehJS's `CustomJSTransform._make_transform` does (bokeh 3.9 `use_strict`).
- Dependencies/Boundaries: S34 edits four `_generate_app_source` lines (R12 exception, its Q1) and the scheme block of `_glyph_layer_lines`; S35's hunks are disjoint and named. "Neither touches…" corrected.
- Chrome harness: `_Launched` is `test_server_serves._Launched`; helpers name their modules (`test_date_range._saved/_served`, `test_display_format_sites.js_texts`).
- 35-02 gives the driver's two lines; 35-14 adds the `{pstd}` line; 35-15 quotes the Appendix B title verbatim and names it in the commit body.
- Anchors corrected: E5 (23096-23097, 23311-23313), `_drop_off_dates` (10673-10693), the help paragraph (2896-2911). Added a source-id → bullet → test → fix table (Notes).
- Rejected: moving the constants anchor into the R2 table here (index.md is not this file's; reported to the orchestrator). Rejected: adding a `_MUST_WARN` entry for the off-range note (R8 reserves edits to the section that silences one; the pytest node pins the note in both modes).
- (cross-file pass) 35-15 verify: added the key-deletion check `grep -c '^    "P1.23a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- (ratification 06oct2026) Row 12 / A77 / P1.23.4 answered CHANGED, "Draw it anyway": a `scatteri`, `pci` or `pcarrowi` coordinate, a `function` point and an explicit `base()` outside 01jan0100-31dec9999 on a date axis are drawn at their number, as twoway draws them, with no note. The drop, its note, `test_an_off_range_literal_is_dropped_with_one_note`, `test_the_served_build_names_the_dropped_literal`, `test_an_off_range_base_is_the_default_with_a_note` and the help's "is not used, and a note says so" sentence are removed.
- (ratification 06oct2026) New D-35j / TR-35.16 and task 35-04a: literal dates are converted by millisecond arithmetic only (`_dash_literal_to_ms`, `_dash_days_from_civil`), never through pandas' nanosecond Timestamp, `_stata_dates_to_datetime`, `datetime.date` or `Date.UTC(year, …)`; finite and `|ms| <= 8.64e15` (the browser's Date range, below 2**53) is the one bound. Only a value past that bound is left out, with one note (M6: dash then differs from twoway).
- (ratification 06oct2026) A date axis reaching past Stata's dates leaves Bokeh's `DatetimeTicker` (its YearsTicker builds `Date.UTC(year, 0, 1)`, which turns years 0-99 into 1900-1999) for natscale ticks over its Stata numbers (`_dash_off_date_ticks`, `_dash_finish_off_date_axes`, and a branch in `_dash_axis_count_ticks`), and its labels there are the number Stata's `display` writes (`dash_stata_number_of` in `_DASH_FMT_JS`, two lines in `_DASH_FMT_MODEL_JS`), where HEAD's formatter writes ".".
- (ratification 06oct2026) Tests added: `TestOffDateLiterals` (converter boundaries at years 99/100/9999/10000, negative years, ±8.64e15 ms, NaN/±inf/1e300; the JS number reader under node with the two-digit-year cases; drawing in both modes, before and after a move; the browser-limit note in both modes and through S23's trial), `TestABaseOnADateAxis::test_an_off_range_base_is_drawn_at_its_date`/`::test_a_base_past_the_browser_is_the_default_with_a_note`, Chrome `TestOffDateAxesInTheBrowser`, DA-10 rewritten and DA-12 added, CORPUS case "P1.23a: a literal past the browser's dates" (8 CORPUS cases). Truth key `literals.scatteri_ty_negative` is recorded by 35-01, not compared.
- (ratification 06oct2026) Axis-option numbers (`xline()`, `xlabel()`, `xscale(range())` and their `axis(2)` forms) keep HEAD's `_dash_axis_positions`/`_dash_note_not_dates` rule (dash.sthlp:2909's `range()` sentence); A77 named literal coordinates only. Reported to the orchestrator.

## Overview

**Binding readings applied in this file** (decisions M1, M5, M6; register P1.23.1-P1.23.4, P1.6.9, P1.9.4, P1.3.6-P1.3.8, X.1, X.2, X.5; index A146, A149, A150, A153, R1-R12; ratification items 3, 11 and 12):
- **P1.23.1 (M1).** A date layer that shares an axis with a plain number is drawn in Stata units, and the axis is labelled in the first layer's date format, the label text written at build. The tick *positions* of such an axis are the P1.3 ticker's: S21's natscale until S44 gives date-labelled axes twoway's date ticks (D-35e).
- **P1.23.3 / A76 (ratification item 11, pending).** The mixed axis is drawn through a CustomJSTransform, with a Python twin in `_dash_secondary_values` and in every other coordinate reader, and one headless-Chrome check under the shipped CSP (S04 keeps `'unsafe-eval'`). No column is rewritten on a refresh.
- **P1.23.4 / A77 (ratification item 12, answered 06oct2026, CHANGED: "Draw it anyway").** A `scatteri`, `pci` or `pcarrowi` coordinate, a `function` point and an explicit `base()` outside 01jan0100-31dec9999 on a date axis are drawn at the position their number denotes, as twoway draws them, with no note, in both modes, before and after a move. The conversion is millisecond arithmetic that holds every year the browser can draw (D-35j, TR-35.16). The help says so beside dash.sthlp:2909.
- **M6.** Nothing S35 draws as twoway draws it prints a note. Only a literal coordinate, `function` point or `base()` past the dates a browser can draw (`|ms| > 8.64e15`, years -271821 to 275760) is named, because only there does dash differ from twoway.
- **M5.** S35 adds no refusal.
- **X.2 / A150.** The notes go through S06's channel (`_dash_warn_once`, the `dash: ` prefix, printed as `(note:  dash: …)` in Stata). The served note reaches Stata through S23's trial relay.
- **R11 / A153.** S35 is batch 12's one finisher editor: it extends S21's readers and `_DASH_AXIS_FINISH_JS` (as S27 left them) with date units, and keeps A9's budgets (ratification item 3).
- **R12.** S35 is batch 12's one editor of `_make_figure_body` and `_generate_app_source`. It does not edit `_build_sources_and_figures` (D-35b), `_build_filter_widgets` or the four appliers.

**Section decisions (this file).**
- **D-35a. One axis decision per axis.** `_dash_figure_date_kind(plots, key, fallback, date_vars, axis_no=1)` counts a layer only on its own axis (`options.xaxis`/`options.yaxis` stripped equal to `"2"` is axis 2, anything else axis 1, as `_dash_add_secondary_axes` reads it).
  - On x it reads `var` (histogram, kdensity), `x1var`/`x2var` (pc types) or `xvar`. On y it reads `yvar1`/`yvar2` (range types), `y1var`/`y2var` (pc types) or `yvar`; a univariate layer counts nothing on y.
  - `scatteri`, `pci`, `pcarrowi` and `function` (`_DASH_LITERAL_TYPES`) are never counted. They name no variable, and they are placed on whatever the axis is.
  - A layer that names nothing on that key counts the fallback, as today.
  - **D-35g.** For axis 1 only: if no layer is on axis 1, every non-literal layer counts (today's rule). `_dash_lone_second_axes` (dash_render.py:3115) rewrites a lone second axis before this runs, so the fallback keeps today's answer for any spec that rewrite leaves.
- **D-35b. The unit pass runs per layer, in both build loops.** `_dash_layer_in_axis_units` runs right after each layer is drawn: saved in `_make_figure_body` after `_dash_assign_axis_ranges` (:30649), served inside the generated `_dash_draw_layer` after its `_dash_assign_axis_ranges` (:35009). Both run before the finishers, which read the transforms through the twin.
  - The manifest's "post-draw pass in `_build_sources_and_figures`" is placed here because the saved finishers run inside `_make_figure_body` (:30660-30679). The by() union (`_dash_share_by_scales`, called from `_build_sources_and_figures` :31669) reads entries already in Stata units.
  - `_build_sources_and_figures` and `_dash_common_count_ticks` (both CRITICAL) are read, not edited. They stay on the 12.0 impact list.
- **D-35c. Units follow the axis a layer is drawn on, in one rule.** `GlyphMapper._unit_kind(fig, var, axis, options)` gives the date kind a variable's values are drawn in. It is None for a variable that is no date. On a marked figure it is the kind of the axis the layer is on (`x`/`y`, or `x2`/`y2` when the layer's options say axis 2), so it is None on a numeric or mixed axis. On an unmarked figure (a mapper used alone) it is the variable's own kind.
  - It replaces the variable-only reads in `_on_axis`, S14's `_bar_extent` and S27's `_base_zero`.
  - On a mixed axis a period bar is therefore one Stata unit wide on the transformed `xvar` field, and a default base is Stata's 0.
- **D-35d. The transform.** There is one `CustomJSTransform` per date kind per document, tagged `dash_date_units:<kind>`, with `args={"kind": kind}` and fixed code (`_DASH_DATE_UNITS_JS`, a JS port of `_dash_date_units`). It is applied per coordinate property, never per column:
  - only on a raw layer (not literal, not one of the 13 computed types);
  - only on a property whose axis has no date kind;
  - only to a field holding one of the layer's own date variables, or a dash column derived from them (`_DASH_JITTER_X*`/`_DASH_JITTER_Y*`, `_DASH_MLABEL_X`/`_DASH_MLABEL_Y`) when every variable of the layer on that letter has one date kind;
  - on `glyph`, `selection_glyph`, `nonselection_glyph`, `hover_glyph` and `muted_glyph` (whichever are Glyph models), and on the layer's `LabelSet` (`x`, `y`) and `Arrow` (`x_start`, `x_end`, `y_start`, `y_end`) annotations;
  - never on a spec that already carries a transform, and never on a value (constant) spec.

  The source keeps epoch ms, so filters, brushing, the CSV, tooltips, the saved row copy and the served data copy are unchanged.
- **D-35e. Labels of a mixed axis.** The label format is the date format of the variable whose layer S18's `_dash_axis_tick_formats` picks for that axis. `_dash_axis_unit_format` asks S18's helper with the date variables' own formats passed as its `numeric_formats` and no `date_vars`, so S18's table decides: a raw date first gives `%td`, an `lfit`/`kdensity`/literal first gives `%9.0g` and stays numbers.
  - The format is written on Stata values (`date_kind=None`), so 0 reads 01jan1960.
  - The tick positions stay S21's natscale (0 5000 10000 15000) until S44 gives date-labelled axes twoway's date ticks (01jan1960 01jan1970 … 01jan2000). This is the batch-12 state on `wp30-p1` only, and it is recorded as the entry's residual and in "Notes for S44".
- **D-35f. Out of Stata's dates (A77 ratified 06oct2026: draw it).** On a date axis, a literal coordinate, `function` point or explicit `base(#)` whose number is no date Stata shows (outside 01jan0100-31dec9999: `%td` below -679350 or above 2936549, and likewise per kind) is drawn where its number falls on the axis, as twoway draws `(line close date) (scatteri 1300 99999999)` (X 14977..1.000e+08, `literals.scatteri_offrange`). There is no note and nothing is dropped.
  - The one exception is a value the browser cannot hold as a date: a non-finite result or `|ms| > 8.64e15` (TR-35.16). Such a coordinate is left out jointly with its record (labels and clocks too), and `_drop_off_dates(…, reach="browser")` names the count once: `dash: scatteri: 1 point(s) past the dates a browser can draw (years -271821 to 275760) not drawn.` (`point(s)` for scatteri and function, `segment(s)` for pci, `arrow(s)` for pcarrowi). Such a `base(#)` draws from the default base with one note: `dash: bar: base(1e+300) is past the dates a browser can draw (years -271821 to 275760); drawn from the default base.` The number is written by `_fmt_num` and cut to 40 characters.
  - A missing or non-finite input keeps each mapper's HEAD handling (map_scatteri's `_keep`, dash_render.py:13664-13665; map_function's NaN gaps). The converter returns NaN for it and never marks it off, so no new note names a missing value.
  - **Served mode (critic decision 4).** S23 (batch 8) has landed, so S35 verifies the relay for the one remaining note: `test_the_served_build_names_the_literal_past_the_browser` must show it exactly once. If it cannot pass, 35-11 stops and reports; S35 never ships a note that only one mode prints.
  - **Parity (M6, R8).** No mode difference arises: `test_mode_parity._served` records the warnings of `build()` and `make_document`, and the copied `GlyphMapper._drop_off_dates` raises the same note there as the saved render. `ALLOWED` and `_MUST_WARN` are not edited. The CORPUS case "P1.23a: an off-range scatteri on a date axis" now makes `test_same_warnings` compare two silent lists and `_glyph_profile` compare the drawn positions; "P1.23a: a literal past the browser's dates" compares the one note.
- **D-35j. Converting an off-date literal (A77, ratified 06oct2026).** HEAD's `_dash_units_to_axis` (dash_render.py:569-616) NaNs every result outside `[_STATA_MS_MIN + E, _STATA_MS_MAX + E]` (:613-615), and for a period kind goes through `_stata_dates_to_datetime`, which places only years 0100-9999 (:450-452). pandas' nanosecond Timestamp holds only 1677-2262 (:292-297), `datetime.date` only years 1-9999, and JavaScript's `Date.UTC(y, …)` and `new Date(y, …)` read a year 0-99 as 1900-1999. So a literal is converted by a new function that uses none of them (TR-35.16):
  - millisecond arithmetic for `td`/`tc`/`tC`, and integer days-from-civil arithmetic (proleptic Gregorian, astronomical year 0, any integer year) for `tw`/`tm`/`tq`/`th`/`ty`;
  - inside 0100-9999 it equals `_dash_units_to_axis` exactly, so a literal at a real date is where S35 places it either way;
  - its one bound is the browser's: a finite result with `|ms| <= 8.64e15` (`_DASH_JS_MS_LIMIT`; `new Date(8.64e15 + 1)` is an Invalid Date). That is below 2**53, so every whole millisecond stays exact in a double, in Python and JS alike. Past it the value is NaN and its record is left out with the D-35f note: twoway would draw it, but no tick, formatter or `Date` call on the page could read it. NaN and ±Infinity never reach a ColumnDataSource.
  - `_dash_units_to_axis` itself is not edited: computed layers keep WP-29 P0.8's rule (a bar or point computed outside 0100-9999 is not drawn, with a note; dash.sthlp:2908-2909).
- **D-35k. Ticks and labels past Stata's dates.** At HEAD a date axis keeps Bokeh's `DatetimeTicker` unless an option ticks it. Its YearsTicker builds `Date.UTC(year, 0, 1)` (bokeh 3.9.0 `bokeh.js`:31192), so a tick at year 0-99 lands in 1900-1999, and its MonthsTicker loop (`date_range_by_year`, :31120-31131) never ends on an Invalid Date. dash's formatter answers "." for a tick outside Stata's dates, because `_DASH_FMT_MODEL_JS` (dash_render.py:21124-21128) returns "." when `dash_stata_value_of` is null.
  - A date axis whose layers reach past Stata's dates is therefore ticked by natscale over its Stata numbers, each tick placed by `_dash_literal_to_ms` (`_dash_off_date_ticks`). `_dash_finish_off_date_axes` replaces a `DatetimeTicker` on such an axis, and `_dash_axis_count_ticks` (dash_render.py:22578-22581, where `_dash_unix_ms_to_unit` gives None) uses the same rule for `#N`. Bokeh's `DatetimeTicker` never stays on such an axis.
  - A tick outside Stata's dates is labelled with its Stata number written as Stata's `display` writes it (`dash_fmt_date`'s fallback, dash_render.py:18206-18222; header :295-297, "`display %td 2936550' prints 2936550"). Measured at `c96facd` through the Python twin: `_dash_fmt_text(25000000, "%td")` is `2.50e+07` and `_dash_fmt_text(99999999, "%td")` is `1.00e+08`, twoway's own label text on `literals.scatteri_offrange`; `-679351` (31dec0099) writes `-679351`, `-1500000` (year -2147) `-1500000`, `%tm 96480` (10000m1) `96480`, `%ty -500` `-5.0e+02`. No label is ever an ISO `±YYYYYY` year, and none is ".".
  - Tick positions are natscale's (`0 2e7 4e7 … 1e8` over 14977..99999999), where twoway draws `2.50e+07 … 1.00e+08`; DA-10 prints twoway's and asserts dash's rule. S44's date ticker gives no answer past 0100-9999 and keeps this rule ("Notes for S44").
  - Axis-option numbers (`xline()`, `xlabel()`, `xscale(range())` and their `axis(2)` forms) are not literal coordinates: they keep HEAD's `_dash_axis_positions` rule (:847-878), named by `_dash_note_not_dates` (:881-890), as dash.sthlp:2909's ratified `range()` sentence describes. A77 does not change them.
- **D-35h. Copy-list reconciliation (R2).** The R2 row for S35 lists only the functions anchor. S35 also adds two constants after `"_STATA_MS_MAX", "_STATA_EPOCH_UNIX_MS",` (dash_render.py:33024), an anchor no section of any batch uses (checked against the R2 table). The JS and tag must reach the served app as values.
- **D-35i. minmax.** On a numeric or mixed axis, `xlabel(minmax)` and `xtick(minmax)` read the first layer's date column in Stata units (`_dash_date_units`). The all-layer rule twoway uses (`[1, 15340]` against dash's `[14977, 15340]` on sp500) is P2.20's, unchanged.

**What is wrong today.** DROPIN-REMAINING.md:134-144 (P1.23) lists, for part a: "scatteri/pci/pcarrowi coordinates and `function range()` are drawn at raw SIF values (1970)"; "Range and pc plots with date y get no date axis"; "A layer on `yaxis(2)`/`xaxis(2)` turns the primary date axis numeric, and the secondary date axis shows epoch ms"; "A date layer beside a numeric layer on one axis is drawn at epoch ms with no warning"; and the explicit-`base()` half of "Base 0 is 1970, not 1960". The WP-29 S04/S05 note adds: "`xlabel(minmax)` on a mixed numeric axis whose first layer's variable is a date reads epoch ms, function/scatteri/pci/pcarrowi on a date axis … each fix should reuse `_dash_units_to_axis`". S01's entry `P1.23a` carries the REM-08-04 ids (C7, C7b, C3b, C3c, C4, B2b, B7a, B4), matched by content to REMAINING.md:1935-2110.

Re-measured at `c96facd` (Evidence E11), the saved page and the served app agree, and both are wrong:
- `(line close date) (scatteri 1300 15400)`: the point is at x = 15400 ms (1970) on a DatetimeAxis. twoway puts it at 01mar2002 (X 14976..15431).
- `rarea date d2 close` has a LinearAxis y in epoch ms. twoway labels it 01jan2001 … 01jan2002.
- `(scatter date close) (scatter volume close, yaxis(2))`: the left axis becomes LinearAxis in ms. twoway keeps it dates.
- `(line close date) (line d2 date, yaxis(2))`: the right axis is a LinearAxis from 9.795e11 to 1.007e12. twoway's y2 is dates.
- `(scatter close date) (scatter close obs)`: the dates sit at 9.78e11..1.007e12 beside 1..12, with no note. twoway draws X 0..15340, labelled 01jan1960 … 01jan2000.

**After this section,** in the saved page and the served app, before and after a filter move:
- every axis is decided by its own layers, range and pc layers included, so a second axis no longer takes the first axis's dates away;
- a second axis of dates is a date axis whose options, `#N` ticks and `range()` read dates;
- literal coordinates, `function` points and an explicit `base()` are placed in date units on a date axis, those outside 01jan0100-31dec9999 included (drawn at their number, as twoway draws them, with ticks and labels there in Stata numbers);
- a raw date beside a number is drawn at its Stata values through a browser-side transform whose Python twin feeds every hull and the by() scale, and the axis carries the first layer's date format.

**Why one section.** Every sub-claim is the same defect: a date reaches an axis in a unit the axis does not use. They share the date-kind decision (`_dash_figure_date_kind`, `_dash_axis_date_kind`), the unit rule (`_on_axis` and its siblings) and S21's readers. Part b (the text of keys and tooltips) is S17's, and it does not depend on this part.

**Test order and commit rule (rule 7, D1).** There is one entry, one cycle and one commit, `(WP-30 P1.23a)`:
- **35-01** checks the contract of the landed sections and writes the extractor and fixture. It appends the regression classes to S17's `test/test_date_axis_residuals.py`, runs them on the unmodified batch-12 base and saves `<scratch>/35-P1.23a-failure.txt`. It never commits.
- **35-02** writes the DA truth block and the Chrome check (both red). **35-03** flips S21's two pins and adds the parity cases.
- **35-04 to 35-12** make the fix. **35-13** certifies in both modes, in Chrome and against Stata. **35-14** writes the help.
- **35-15** closes the entry, replaces the marker and makes the one commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every figure passes through the changed date decision in both modes, two CRITICAL helpers change, and one new browser-side transform must agree with its Python twin

**Why.** The date-kind decision runs for every figure in both modes, and `_dash_axis_date_kind` and `_on_axis` feed every axis option and computed layer. The transform moves positions in the browser only, so any Python reader that misses the twin ranges an axis in the wrong unit, with every point against one edge (research p1-23 "Critic additions", Gap 1, measured: Range1d -5.03e10..1.057e12).

**Risk factors.**
1. **Blast radius** (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026 at `c96facd`):
   - CRITICAL: `_dash_axis_date_kind` (23 impacted), `GlyphMapper._on_axis` (14), `_make_figure_body` (4), `_build_sources_and_figures` (14; read only), `_dash_common_count_ticks` (4; read only), `_dash_date_units` (12; read only).
   - HIGH: `ServerAppBuilder._generate_app_source` (5), `ServerAppBuilder._glyph_layer_lines` (4), `_dash_apply_tick_option` (4; not edited, its callers pass the kind).
   - LOW: `_dash_figure_date_kind`, `_dash_axis_vars`, `_dash_mark_date_axes`, `DashRenderer._figure_date_kind`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_count_axes`, `_dash_refline_draw`, `_dash_apply_axis_options` (3 each), `_dash_secondary_values` (5), `_dash_axis_hull` (6), `map_scatteri`, `map_pci_literal`, `map_pcarrowi`, `map_function` (3 each).
   - UNKNOWN, confirmed by grep: `map_bar`, `map_area`, `map_spike`, `map_dropline` are dispatched by name through `_dash_glyph_dispatch` (dash_render.py:28522-28537) in both modes. S21's and S27's new symbols are measured at 12.0.
   - Generated code the index cannot see: `_dash_figure_date_kind`, `_dash_axis_vars` and `_dash_mark_date_axes` are also called from emitted app text (:35069-35088, :35134, :35171-35193).
2. **Twin drift.** `_DASH_DATE_UNITS_JS` must equal `_dash_date_units` value for value, or the browser draws where the Python hull did not range.
3. **CSP.** The transform is one more `new Function` consumer. S04 keeps `'unsafe-eval'` (measured necessity for BokehJS; dash_render.py:3684, :3701 today).
4. **Budgets.** The twin adds a numpy conversion per transformed field in the served re-finish (A9: at most 0.2 s per figure per move at 500k rows).
5. **Pins.** S21 pins the raw-SIF exclusion that S35 removes, and S27's date-base tests read the variable's kind.
6. **Off-date literals (A77, ratified 06oct2026).** A literal drawn past 0100-9999 reaches every reader of the axis. pandas' ns Timestamp, `_stata_dates_to_datetime`, `datetime.date` and JS `Date.UTC(y, …)` each fail somewhere in that span (D-35j), and Bokeh's `DatetimeTicker` misplaces years 0-99 (D-35k). Impact of the two shared edits, run before 35-04a: `_dash_axis_count_ticks` and the `_DASH_FMT_MODEL_JS` constant (the index does not see a constant; confirm its users with `grep -n "_DASH_FMT_MODEL_JS" dash_render.py`).

**Mitigation.**
1. Impact at the batch-12 base (12.0), with a warning before each CRITICAL edit. Every change is gated on a date kind, and a guard class shows non-date figures unchanged (`TestNonDateFiguresAreUnchanged`, plus the single-y page digest of R10).
2. `TestTheDateTransform::test_the_js_twin_equals_the_python_twin` runs the JS under node over 10,000 seeded values per kind, the bounds and the hostile values.
3. `TestTheDateTransformUnderTheCsp` renders saved, WebGL and served pages in Chrome with zero violations.
4. A timed mixed-axis case is added to S21's re-finish budget test.
5. 35-03 flips S21's pins in place. 35-13 re-measures the red list over every date, axis and bar test file (R9).
6. `TestOffDateLiterals` pins the converter at years 99, 100, 9999 and 10000, at negative years, at ±8.64e15 ms ±1 and at NaN/±Infinity/1e300 against numpy's `datetime64[ms]` as the oracle, and runs the JS number reader under node with the two-digit-year cases. Its drawing tests run in both modes before and after a move, and `TestOffDateAxesInTheBrowser` renders the pages in Chrome. A guard asserts `"Date.UTC("` occurs in neither `_DASH_FMT_JS` nor `_DASH_DATE_UNITS_JS`.

## Dependencies

- **Depends on 21 and 27.**
  - S21 (batch 7) built the finisher chain S35 extends: `_dash_layer_extent`, `_dash_axis_hull`, `_dash_axis_plan`, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS` and `_dash_tag_hull_roles`, whose `_dash_raw_sif` stamp keeps literal layers out of date hulls "until S35" (S21 D-21g, BR-21.2).
  - S27 (batch 9) gave the four bar mappers `_base_value`, `_base_zero` and `_tag_base`, and `_dash_finish_auto_bases`. Its hand-off: "Read an explicit `base(#)` in the y variable's date units at the four `_base_value` call sites … A mixed date and numeric axis's transform must leave the base column in axis units".
- **Relies on (landed in earlier batches):**
  - S04: the CSP that keeps `'unsafe-eval'`, and `test/test_csp_browser.py`.
  - S06: the note channel.
  - S14: `GlyphMapper._bar_extent`, whose D-14d leaves mixed axes to S35.
  - S17: `test/test_date_axis_residuals.py`, to which S35 appends.
  - S18: `_dash_axis_tick_formats`, `_dash_layer_tick_format`, and the `plots`/`date_vars` keywords of `_dash_apply_axis_options` and `_dash_finish_secondary_axes`; S18 says "A date variable on axis 2 gives `""` (S35 owns date second axes)".
  - S23: the trial relay (`ServerAppBuilder.build(…, trial=True)`).
  - S26 (batch 9): `map_function`'s fallback mark. S35 converts `x_arr` before `fn_source` and leaves the mark.
  - Batch 11, read at the batch-12 base: S31 gives `_dash_apply_axis_spec` `option`/`by_graph`/`colours`, `_dash_apply_tick_option` `by_graph`/`ref_in`, and threads them through `_dash_apply_axis_options` and `_dash_finish_secondary_axes` (S31 TR-31.6, TR-31.7); S35 adds `date_kind`/`formats` beside them and drops none. S32 adds `_style_restyle` after `fig.scatter` in `map_scatteri`; S33 passes `color_idx` to `_immediate_labels` from `map_scatteri` and `map_pcarrowi`. S35's literal conversion sits before `si_source`/the pc sources and filters `_labels`/`_clocks` by the same mask, so those lines are untouched.
- **Blocks 44, 49, 51, 56, 57.**
  - S44 ticks `%td`-`%ty` axes and reads S35's Stata-unit hulls; it also takes over the mixed date-labelled axes (D-35e).
  - S49 swaps date kinds under `horizontal`, on S35's per-axis decision.
  - S51 routes `tlabel()`/`tline()` with `axis(2)` onto S35's y2/x2 kinds, and the register's P1.6.9 puts S35 before it.
  - S56 draws `text()` on a date second axis and on mixed axes in Stata units.
  - S57 audits the final served move path, including the redraw's unit pass.
- **Parallel batch: 12**, merge order S34, S35, S36. S35 lands second.
- **Can run with:**
  - S34 edits `SchemeParser._resolve_path`, `resolve_or_fallback`, `_include`, `DashRenderer._scheme_for`, `DashRenderer._make_figure` (one call), `ServerAppBuilder.__init__`, the scheme block of `_glyph_layer_lines` (after `"_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)",`, :33479), four `_generate_app_source` lines (:35093, :35562, :35584, :35646; the R12 exception its Q1 asks the orchestrator to grant at 12.0), dash.ado's scheme lookup, and the help's scheme remedy.
  - S36 edits `SchemeParser.style_bundle`, its table and extractor, GlyphMapper's `_STYLE_FACTORS`/`_ci_*` style methods, and regenerates the 26 scheme files.
  - Neither touches a date, axis or mapper symbol S35 edits. In the two functions S34 shares with S35, the hunks are disjoint: S35's `_glyph_layer_lines` edits are the two tuple anchors (:33024, :33105), and its template edits are :35009-35010, :35069-35073, :35134, :35171-35199, :35206-35208, :35268-35273 and :35417-35423. S35 leaves S34's four template lines as they are at the base (`_dash_mark_date_axes(_tfig, *_rkinds)` and `return _redraw` included).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines), re-read 03oct2026. Batches 1-11 move lines; symbols and the quoted text are authoritative.

### E1 — the date decision reads three keys and ignores the axis a layer is on

`_dash_figure_date_kind` (788-818), its loop (806-818):
```python
    kinds = set()
    for plot in plots or []:
        if str(plot.get("type", "")).lower() in _DASH_UNIVARIATE_TYPES:
            if key != "xvar":
                continue
            name = plot.get("var", "") or fallback
        else:
            name = plot.get(key, "") or fallback
        if not name:
            continue
        kinds.add(date_vars.get(name))
    if not kinds or len(kinds) > 1 or None in kinds:
        return None
```
dash.ado writes range types as `"yvar1","yvar2","xvar"` and pc types as `"y1var","x1var","y2var","x2var"` (dash.ado:4296-4307), so a range or pc layer counts only the fallback. Every layer counts on one axis, so a `yaxis(2)` number puts `None` in `kinds`. Callers: `DashRenderer._figure_date_kind` (30119-30137; called at 30282-30283), the emitted `_rkinds` (35070-35073) and `_x_date`/`_y_date` (35171-35172).

### E2 — the axis variables and the marks hold the first axis only

```python
def _dash_axis_vars(plots):                                     # 821
    p0 = (plots or [{}])[0] or {}
    if str(p0.get("type", "")).lower() in _DASH_UNIVARIATE_TYPES:
        return (p0.get("var", "") or p0.get("xvar", "") or "", "")
    return (p0.get("xvar", "") or "", p0.get("yvar", "") or "")

def _dash_mark_date_axes(fig, x_kind, y_kind):                  # 834
    fig._dash_date_kinds = (x_kind or None, y_kind or None)

def _dash_axis_date_kind(fig, axis):                            # 841
    kinds = getattr(fig, "_dash_date_kinds", None) or (None, None)
    return kinds[0] if axis == "x" else kinds[1]
```
A range first layer gives `yv = ""`, so its date axis formatter falls back to the bare `%td` picture. Both modes mark the figure right after `bokeh_figure` (saved :30312, served :35193) and the redraw's throwaway figure (:35088).

### E3 — computed layers read the first axis's kind whatever axis they are on

`GlyphMapper._on_axis` (10646-10670), its rule (10660-10670):
```python
        kind = (self.date_vars or {}).get(var)
        none = np.zeros(vals.shape, dtype=bool)
        if kind not in _STATA_DATE_KINDS:
            return vals, none
        if getattr(fig, "_dash_date_kinds", None) is not None:
            kind = _dash_axis_date_kind(fig, axis)
            if not kind:
                return vals, none
        drawn = _dash_units_to_axis(vals, kind)
```
It has 13 direct callers, each a mapper with an `options` parameter: `map_lfit` (10908-10909), `map_qfit` (10985-10986), `map_lfitci` (11084-11087), `map_qfitci` (11212-11215), `map_lowess` (11350-11351), `map_lpoly` (11765-11766), `map_lpolyci` (11896, inside its local `_on`), `map_fpfit` (12311-12312), `map_fpfitci` (12405-12408), `map_histogram` (12514), `map_kdensity` (12881), `map_mspline` (14720-14721) and `map_mband` (14842-14843). `_drop_off_dates` (10673-10693) names dropped points once per layer through `_dash_warn_once`.

### E4 — literal layers are placed at their raw numbers

```python
        y_vals = np.array([y_all[i] for i in _keep], dtype=float)       # map_scatteri 13666
        x_vals = np.array([x_all[i] for i in _keep], dtype=float)
        ...
        si_source = ColumnDataSource({"x": x_vals.tolist(), "y": y_vals.tolist()})   # 13681
```
- `map_pci_literal` builds `ColumnDataSource({"y0": y1, "x0": x1, "y1": y2, "x1": x2})` (13841).
- `map_pcarrowi` builds `{"y1": y1, "x1": x1, "y2": y2, "x2": x2}` (14454) and labels the tails from the same lists (14457-14465).
- `map_function` builds `fn_source = ColumnDataSource({"x_fn": x_arr, "y_fn": y_arr})` (14943) from stored points (14913-14917) or the fallback grid (14931-14941).

None of them reads an axis kind.

### E5 — second axes are never date axes

`_dash_add_secondary_axes` builds `ax = (LogAxis if is_log else LinearAxis)(**{kw: name}, axis_label=text)` (23096-23097). `_dash_finish_secondary_axes` reads `range()` values, labels and ticks as numbers, and passes no kind (23311-23313):
```python
            _dash_apply_tick_option([ax], tgrids, tick_raw, f"{n}tick2",
                                    col_vals or None, seen, key, grid_color,
                                    date_kind=None)
```
`_dash_count_axes` gives a second axis no kind and skips a DatetimeAxis without one (23392-23396):
```python
                elif isinstance(ax, DatetimeAxis):
                    kind = (_dash_axis_date_kind(fig, letter)
                            if name == "default" else None)
                    if kind is None:
                        continue        # a date axis of no known unit
```
`_dash_refline_draw`'s docstring says "a second axis is never a date axis" (26331-26334); its kind is `… if range_name == "default" else None` (26357-26358).

### E6 — every coordinate reader reads the column as stored

`_dash_secondary_values` (23117-23169) reads a field with `col = _dash_float_values(data[field], coerce=True)` (23149-23160) and ignores any `transform`. `_dash_axis_hull`'s bar loop reads the centre the same way (23644-23652). Both feed `_dash_count_axes` (23406-23407), `_dash_finish_secondary_axes` (23250) and the finishers (`_dash_finish_count_ticks` 23732, `_dash_common_count_ticks` 23775). S21 adds `_dash_layer_extent` (TR-21.7), its JS reader `dash_axis_extent` (TR-21.11) and the plan's `layers`/`bars` (TR-21.10). All of them read stored ms unless S35 converts.

### E7 — minmax reads the first layer's stored column

`_dash_apply_axis_options` passes `col = frame[var]` (23015) to `_dash_apply_axis_spec`, whose minmax branch (22778-22786) and `_dash_apply_tick_option`'s (22926-22931) both write `[min, max]` of the stored column:
```python
    elif mode == "minmax" and values is not None:
        # A date in milliseconds, a missing one dropped (24sep2026).
        vals = pd.Series(_dash_float_values(values, coerce=True)).dropna()
```
On a mixed axis this is ms, so the ticks are `[978393600000.0, 1006905600000.0]` (research D4).

### E8 — the four bar mappers read base() as a raw number

At `c96facd`: `map_area` (10074-10080), `map_bar` (10223-10229), `map_spike` (10339-10345) and `map_dropline` (13443-13444):
```python
        base_val = 0.0
        if "base" in options:
            try:
                base_val = float(options["base"])
```
S27 rewrites all four to `_base = self._base_value(options, layer)` and `_zero = self._base_zero(yvar)` (S27 TR-27.2-27.5). `_base_zero` reads `self.date_vars.get(yvar)`, so on a mixed y axis it would write -315619200000 into a Stata-unit axis. An explicit `base(14970)` on a date y is 14970 ms.

### E9 — the wiring points

- Saved, `_make_figure_body`:
  - `_xa, _ya = _dash_axis_vars(plots)` at 30221;
  - the kinds at 30282-30283; the mark at 30312;
  - the primary date formatters at 30314-30322;
  - `_dash_add_secondary_axes(fig, plots, graph_opts, _source_frame(source, self.df), _seen, _gkey, self.variable_labels, self.scheme)` at 30385-30387;
  - `_dash_apply_axis_options(…, fmt_cache=…)` at 30405-30412;
  - `_dash_assign_axis_ranges(fig, _layer_renderers, popts, list(fig.center[_c_before:]))` at 30649-30650;
  - `_dash_finish_secondary_axes(…)` at 30660-30666.
- Served, `_generate_app_source` text:
  - `_rax`/`_rkinds` at 35069-35073 and `_dash_mark_date_axes(_tfig, *_rkinds)` at 35088;
  - `_xa, _ya` at 35134; `_x_date`/`_y_date` at 35171-35172; the mark at 35193; the formatters at 35194-35199;
  - `_dash_add_secondary_axes(…)` at 35206-35208;
  - `_dash_apply_axis_options(…)` at 35268-35273;
  - `_dash_draw_layer`'s `_dash_assign_axis_ranges(fig, fig.renderers[_before:], opts, list(fig.center[_before_c:]))` at 35009-35010;
  - `_dash_finish_secondary_axes(…)` at 35417-35423.
- `_date_vars` (34781) and `_fmt_cache` (34790) are `make_document` locals, visible to `_dash_draw_layer` (34922) and `_dash_figure_for`. `_FORMATS` (33689) holds every display format, dates included.
- Copy-list anchors (R2): functions `"_dash_axis_date_kind", "_dash_axis_positions",` (33105); constants `"_STATA_MS_MAX", "_STATA_EPOCH_UNIX_MS",` (33024). `GlyphMapper` methods travel with the class (33436).

### E10 — the policy the transform runs under

`_DASH_CSP_STANDALONE` holds `"script-src 'unsafe-inline' 'unsafe-eval'; "` (3684) and `_DASH_CSP_SERVED` holds `"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "` (3701). The comment at 3674-3676 explains: "'unsafe-eval' because Bokeh's CustomJS compiles each callback with `new Function(...)`". S04 replaces `'unsafe-inline'` with hashes and a nonce, and keeps `'unsafe-eval'` (S04 scope, notes: "S35's CustomJSTransform … must run under these policies").

### E11 — measured at HEAD, both modes

The critic's probe, re-run 03oct2026 at `c96facd` (`python3 <scratch>/c-p1-23/k.py`: `test_date_range._spec`, `_saved`, `_served`; 12 rows, `date = 14977 + 30*i` `%td`):
```
A1 scatteri saved {'below': ['DatetimeAxis', 'Legend'], 'left': ['LinearAxis']} kinds ('td', None)
     Scatter x=15400..15400 y=1300..1300
A4 function range served ... Line x=15400..15450 y=1300..1300
C2 y date + y2 numeric saved {'below': ['LinearAxis', ...], 'left': ['LinearAxis'], 'right': ['LinearAxis']} kinds (None, None)
C3 y2 date saved ... 'right': ['LinearAxis']} ... Line ... y=9.79517e+11..1.00708e+12
D1 mixed raw served ... Scatter x=9.78394e+11..1.00691e+12  /  Scatter x=1..12
B1 rarea date y saved {'below': ['LinearAxis', 'Legend'], 'left': ['LinearAxis']} kinds (None, None)
E bar date obs served ... VBar x=1..12 top=9.78394e+11..1.00691e+12 bottom=const 0
```
Saved and served print the same for every case. Research p1-23 §1 records the rest:
- `ylabel(#5, axis(2))` on y2 dates places nothing (Gap 2);
- `yline(15200, axis(2))` is drawn at 15200 ms (H3);
- a mixed axis with `xlabel(0 5000 10000 15000)` or `xscale(range(0 16000))` gets x Range1d -5.03e10..1.057e12 (Gap 1, k2.py);
- `xlabel(minmax)` there ticks `[978393600000.0, 1006905600000.0]` (D4, D5).

### E12 — existing tests that pin today's behaviour

A search of test/ at `c96facd` (`grep -ln` for scatteri, pci, pcarrowi, function, the range and pc types, `yaxis`/`xaxis` and `LinearAxis`, crossed with `date`/`%td`) found no committed test that asserts a literal at its raw number, a range/pc date y on a LinearAxis, a numeric second axis over dates, or ms for a raw date on a mixed axis. The pins are the batch-7 ones S35 replaces, plus guards that must stay green. Batches 1-11 add tests, so 35-13 re-measures the red list over every date, axis and bar test file (R9).

**Flipped in 35-03 (R9), never deleted:**
- `test/test_default_axes.py::TestRawSifDateLayersStayOut::test_scatteri_on_a_td_axis[saved|served]` (S21). Its literal moves to 15400, past the dates, and it asserts the hull reaches `_ms(15400)`. The old expectation was wrong because twoway's scale spans a literal on a date axis (X 14976..15431).
- `test/test_default_axes.py::TestTheHelpers::test_hull_roles[scatteri|pci|pcarrowi|function]` (S21). It asserts no `_dash_raw_sif` attribute. The old expectation was wrong because the exclusion existed only until literals were placed in date units.

**Guards (stay green, re-run in 35-13):**
- `test/test_date_units.py::TestTheUnitHelpers::test_axis_vars_reads_a_univariate_first_layer`, `::test_on_axis_follows_the_figures_axis` (positional calls keep working);
- `test/test_date_units.py::TestTheAxisRule` (every case) and `::TestEveryComputedLayer::test_a_date_layer_on_a_numeric_axis_is_drawn_in_its_units`;
- `test/test_served_dates.py::TestTheServedFigureReadsTheDateAsTheSavedOne::test_a_date_and_a_number_on_one_axis_is_no_date_axis` (still a LinearAxis, still silent) and `::TestANumberOnADateAxisIsAStataDate` (every case);
- `test/test_date_range.py::TestAComputedLayerIsDrawnOnTheDateAxis::test_a_date_on_a_second_axis_is_ranged_in_milliseconds` (a date y2 is ranged in ms, now on a DatetimeAxis) and `::test_xlabel_minmax_ticks_the_first_and_last_date` (a date axis keeps ms ticks);
- `test/test_dates.py::TestDatetimeAxis` (every case);
- `test/test_dual_axis.py` (every class);
- `test/test_bar_range_geometry.py::TestTheMappersMarkTheirBase::test_base_zero` and `::TestTheBaseOnADateAxis` (S27: unmarked figure and date axis unchanged);
- S14's `TestTheBarExtent::test_each_kind` (unmarked mapper unchanged);
- `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (R10 digest; a page with no date is unchanged).

## User stories

- **US-35.1** As a twoway user, I want `(line close date) (scatteri 1300 15400)`, `pci`, `pcarrowi` and `function, range(15400 15450)` drawn at the dates their numbers denote, so annotations land where twoway puts them.
- **US-35.2** As a twoway user, I want `rarea date d2 close` and `pcspike date open d2 close` to get a date axis, so range and paired plots of dates read as dates.
- **US-35.3** As a dashboard publisher, I want a `yaxis(2)` layer of a number to leave my date axis alone, and a second axis of dates to show dates and read `ylabel(#5, axis(2))`, `yline(15200, axis(2))` and `yscale(range(…) axis(2))` in days, as twoway does.
- **US-35.4** As a twoway user, I want `(scatter close date) (scatter close obs)` drawn on one axis in Stata units, labelled in the date's format, with `xlabel(minmax)` reading the same units, so the picture matches twoway's.
- **US-35.5** As a dashboard publisher, I want `bar date obs, base(14970)` to stand on 26dec2000, and a date bar beside a number to stand on Stata's 0.
- **US-35.6** As a dashboard viewer, I want all of this to hold after I move a filter, in a saved file and in a served app, under the page's security policy.
- **US-35.7** As a twoway user, I want `(line close date) (scatteri 1300 99999999)` and `(line close yr) (scatteri 1300 -500)` drawn where twoway draws them, past Stata's dates, with no note, and the axis there labelled with the numbers Stata's `display` writes, so an annotation I placed by number is never silently moved, dropped or labelled "." (A77, ratified 06oct2026).

## Business requirements

- **BR-35.1** Literal coordinates of `scatteri`, `pci`, `pcarrowi` and the points of `function` are placed in the date units of the axis they are drawn on, in both modes, before and after a move. A coordinate that is no date Stata can show (outside 01jan0100-31dec9999) is drawn where its number falls, as twoway draws it, with no note (A77, ratified 06oct2026). Only one past the dates a browser can draw (`|ms| > 8.64e15`) is left out, and one note says how many.
- **BR-35.2** An axis is a date axis when every non-literal layer drawn on it carries a date variable of one kind there. Range bounds and paired coordinates count.
- **BR-35.3** A layer on `yaxis(2)`/`xaxis(2)` does not change the first axis's kind. A second axis of dates is a date axis in its first layer's format, and its label, tick, line and `range()` numbers, its `#N` ticks and its extent are in date units.
- **BR-35.4** A computed layer drawn on a second date axis is placed in that axis's units.
- **BR-35.5** A raw date on an axis that also carries a plain number is drawn at its Stata values, with every hull, `#N` tick set and by() scale computed in those values. The axis is labelled in the first layer's date format when that layer draws the date's own values. `xlabel(minmax)` there ticks Stata values.
- **BR-35.6** An explicit `base(#)` of bar, spike, dropline and area is a date on a date axis, outside 01jan0100-31dec9999 included (BR-35.1's bound applies). On a mixed axis it is a Stata value, and the default base is Stata's 0, clamped as S27 clamps it.
- **BR-35.7** The transformed axis renders with no policy violation, saved (canvas and WebGL) and served.
- **BR-35.8** A figure with no date is unchanged.
- **BR-35.9** Converting a literal date never depends on a library's year range: years 0-99, negative years and years past 9999 are placed exactly in both modes, and no NaN or infinity reaches the page. A date axis that reaches past Stata's dates is ticked and labelled in Stata numbers (as Stata's `display` writes them), never "." and never at a tick Bokeh's year ticker misplaces.

## Technical requirements

- **TR-35.1 The axis decision** (dash_render.py, `_dash_figure_date_kind` 788).
  - It gains `axis_no=1` (last positional, defaulted) and implements D-35a/D-35g.
  - It adds the private helper `_dash_layer_axis_names(plot, key)` directly below it: `(axis_no, [names])` for one layer, `(None, [])` for a literal.
  - `DashRenderer._figure_date_kind(self, plots, key, fallback, axis_no=1)` passes it through.
- **TR-35.2 `_dash_axis_vars(plots, axis_no=1)`** (821). Per letter it reads the first non-literal layer on that letter's axis `axis_no`.
  - x: `var` for a univariate layer, else `xvar`, else `x1var`.
  - y: `""` for a univariate layer, else `yvar`, else `yvar1`, else `y1var`.
  - With no such layer: plots[0]'s answer for axis 1 (today's), `""` for axis 2. `_dash_axis_vars(plots)` keeps its two-tuple.
- **TR-35.3 Marks.**
  - `_dash_mark_date_axes(fig, x_kind, y_kind, x2_kind=None, y2_kind=None)` also sets `fig._dash_date_kinds2 = (x2_kind or None, y2_kind or None)`.
  - `_dash_axis_date_kind(fig, axis)` answers `"x"`, `"y"`, `"x2"` and `"y2"` (reading `_dash_date_kinds2`, default `(None, None)`), and None for anything else.
  - Both are Python attributes, never serialised.
- **TR-35.4 GlyphMapper unit rule** (methods; they travel with the class).
  - `_axis_kind(self, fig, axis, options=None)`: the axis name is `axis + "2"` when `str((options or {}).get(axis + "axis", "1")).strip() == "2"`, else `axis`. It returns `_dash_axis_date_kind(fig, name)`.
  - `_unit_kind(self, fig, var, axis, options=None)` implements D-35c.
  - `_on_axis(self, fig, values, var, axis, options=None)` uses `_unit_kind`. Its output for a call without `options` is unchanged, and each of the 13 callers passes its `options`.
  - `_literal_on_axis(self, fig, values, axis, options=None)` returns `(drawn, off)`. On an unmarked figure, or an axis with no date kind, values are unchanged. Otherwise they go through `_dash_literal_to_ms(vals, kind)` (TR-35.16, never `_dash_units_to_axis`), and `off` marks a finite value with a NaN result, which is only a value past `|ms| <= 8.64e15` (A77, ratified 06oct2026). A value outside 0100-9999 within that bound is drawn, `off` False.
  - `_base_in_axis_units(self, base, var, fig, options, layer)` implements D-35f for `base()`: on a date axis `_dash_literal_to_ms([base], kind)[0]`, on a mixed axis the number itself. It returns a float in axis units, outside 0100-9999 included, or None (the default base, with D-35f's browser-limit note) only when the conversion is NaN.
- **TR-35.5 Literal mappers.**
  - `map_scatteri`: after jitter and before `si_source`, x and y go through `_literal_on_axis`. Records past the browser's dates (and only those) are dropped jointly through `_drop_off_dates("scatteri", "point(s)", …, reach="browser")`, with `_labels`/`_clocks` filtered by the same mask.
  - `_drop_off_dates(self, layer, what, off, *arrays, reach="stata")` gains the keyword-only `reach`. `"stata"` keeps HEAD's words and key exactly (computed layers, WP-29 P0.8). `"browser"` writes D-35f's `past the dates a browser can draw (years -271821 to 275760) not drawn.` under the warn-once key `("off-browser", layer, what)`.
  - `map_pci_literal`: the four lists, `segment(s)`.
  - `map_pcarrowi`: the four lists plus `labels`/`clocks`, `arrow(s)`.
  - `map_function`: `x_arr`/`y_arr` before `fn_source`, `point(s)`. This covers both stored points and the fallback grid.
  - Each of the four passes `reach="browser"`; none drops a value only because it is outside 0100-9999.
- **TR-35.6 Bars and bases** (S14's and S27's methods, edited in place).
  - `_bar_extent(self, xvar, xs, width, fig=None, options=None)` takes its kind from `_unit_kind(fig, xvar, "x", options)`. `map_bar` and `map_rbar` pass `fig` and `options`.
  - `_base_zero(self, yvar, fig=None, options=None)` takes its kind from `_unit_kind(fig, yvar, "y", options)`.
  - At each of S27's four `_base_value` call sites, `_base = self._base_in_axis_units(_base, yvar, fig, options, "<layer>")`, and `_base_zero` gets `fig, options`. S27's tag, its JSON form and `_dash_finish_auto_bases` are unchanged.
- **TR-35.7 Second axes.**
  - `_dash_add_secondary_axes` gains `date_axes=None, fmt_cache=None`. `date_axes` maps `"y2"`/`"x2"` to `(var, fmt)` for each marked date kind.
    - For a marked kind it builds `DatetimeAxis(**{kw: name}, axis_label=text)`. After `scheme.apply_to_axis(ax)` it sets `ax.formatter = _dash_date_axis_formatter(fmt or _dash_date_fmt("", kind), "", fmt_cache)`.
    - With `log` asked it gives one note, ``f"dash: {n}scale2(log) is meaningless for the date variable '{_dash_display(var, 32)}'; drawing a date axis instead."``, and builds the date axis.
  - `_dash_finish_secondary_axes` reads `kind = _dash_axis_date_kind(fig, name)`. With a kind:
    - `range()` values go through `_dash_axis_positions` (non-dates named by `_dash_note_not_dates(f"{n}scale2", …)`);
    - `spec`/`tspec` go through `_dash_date_axis_spec(…, f"{n}label2"/f"{n}tick2")`;
    - `_dash_apply_tick_option(…, date_kind=kind)`, S18's `_dash_apply_axis_spec(…, date_kind=kind, option=f"{n}label2")`, the pad kind (`"log" if is_log else kind`) and the recorded hull kind follow. S31's keywords on those two calls (`option`, `by_graph`, `colours` on the label call; `by_graph`, `ref_in` on the tick call) stay as S31 wrote them; only `date_kind` changes from `None`.
  - It gains `formats=None` (TR-35.10).
  - `_dash_count_axes`: `kind = _dash_axis_date_kind(fig, letter if name == "default" else letter + "2")`.
  - `_dash_refline_draw`: `kind = _dash_axis_date_kind(fig, (("x" if opt == "xline" else "y") if range_name == "default" else range_name))`. The docstring's "a second axis is never a date axis" is replaced with "a second axis of dates reads dates, as the first does".
- **TR-35.8 The transform** (D-35d). The constants are defined directly after `_dash_units_to_axis` (ends near 620):
  - `_DASH_DATE_UNITS_TAG = "dash_date_units:"`.
  - `_DASH_DATE_UNITS_JS`, a self-contained JS port of `_dash_date_units`:
    - `function dash_date_units(v, kind)` returns NaN for a value that is not finite or is outside `[__DASH_MS_MIN__ + __DASH_EPOCH__, __DASH_MS_MAX__ + __DASH_EPOCH__]`;
    - it returns `(ms - E) / 86400000` for `td` and `ms - E` for `tc`/`tC`;
    - for `tw`, `tm`, `tq`, `th` and `ty` it takes `day = Math.floor(ms / 86400000)`, the proleptic-Gregorian civil date of `day` (days-from-civil arithmetic, no `Date`), and `_dash_period_values`' formulas (`tw` with `Math.min(51, Math.floor((day - jan1) / 7))`).
    - The tokens are replaced with `repr(float(...))` of `_STATA_MS_MIN`, `_STATA_MS_MAX` and `_STATA_EPOCH_UNIX_MS` at import.
    - It holds no `eval`, no `Function`, no DOM and no user text, and is at most 3,000 characters.
  - `_dash_date_transform(kind, cache=None)` imports `CustomJSTransform` inside its body (`from bokeh.models import CustomJSTransform`, the form copied functions use, e.g. `_dash_add_secondary_axes` :23071; neither dash_render.py's header nor the generated app's imports it today). It raises `ValueError` unless `kind in _STATA_DATE_KINDS`. It returns `cache[("date-units", kind)]` when present. Otherwise it makes `CustomJSTransform(args={"kind": kind}, func=_DASH_DATE_UNITS_JS + "return dash_date_units(x, kind);", v_func=_DASH_DATE_UNITS_JS + "var out = new Float64Array(xs.length); for (var i = 0; i < xs.length; i++) { out[i] = dash_date_units(xs[i], kind); } return out;", tags=[_DASH_DATE_UNITS_TAG + kind])` and stores it.
  - `_dash_spec_units(spec)` gives the kind for a field spec (str, dict or `Field`; bokeh 3.9 returns a `bokeh.core.property.vectorization.Field` for a transformed spec, measured) whose transform is a `CustomJSTransform` (local import) carrying a well-formed tag (suffix in `_STATA_DATE_KINDS`), else None. It never raises.
  - `_dash_layer_in_axis_units(fig, renderers, annotations, plot, date_vars, cache=None)` implements D-35d and returns how many properties it transformed. It reads `_DASH_X_COORDS`/`_DASH_Y_COORDS` for glyphs and `("x", "x_start", "x_end")`/`("y", "y_start", "y_end")` for `LabelSet`/`Arrow` (the only coordinate annotations dash makes, :9499, :14017). It skips swatches (`_dash_is_swatch`) and does nothing on an unmarked figure.
    - A property's axis is its letter when the model's `x_range_name`/`y_range_name` is `"default"`, else `letter + "2"` (set by `_dash_assign_axis_ranges`, which runs first); its kind is `_dash_axis_date_kind(fig, axis)`.
    - The 13 computed types of E3 are a local `frozenset` inside the function (no new module constant), with `_DASH_LITERAL_TYPES` the other exclusion.
- **TR-35.9 The twin in every reader.** After a field is read into `col`: `k = _dash_spec_units(v)`; if `k`, then `col = _dash_date_units(col, k)`. This applies in:
  - `_dash_secondary_values`;
  - `_dash_axis_hull`'s bar centre;
  - S21's `_dash_layer_extent` (vectorised);
  - S21's `_dash_axis_plan`, where each plan layer gains `"units": [[field, kind], …]` (a list of pairs, empty when none) and each bar `"cunits": kind or null` (kinds only from `_STATA_DATE_KINDS`). A list, not an object keyed by field, because a field is a variable name and `__proto__` is a valid Stata name.
  - `_DASH_AXIS_FINISH_JS`, which gets `_DASH_DATE_UNITS_JS` prepended once. `dash_axis_extent` and the bar reader look a field up by a loop over `units` (`units[i][0] === f`) and convert a value with `dash_date_units(v, units[i][1])`; a field not listed is read as stored.

  The `_dash_raw_sif` stamp in `_dash_tag_hull_roles` and every reader's skip of it (Python and plan) are deleted.
- **TR-35.10 Mixed-axis labels and minmax.**
  - `_dash_axis_unit_format(plots, axis, date_vars, formats)` (new; pure) builds `fake = {v: _dash_date_fmt((formats or {}).get(v), k) for v, k in (date_vars or {}).items() if k in _STATA_DATE_KINDS}`. It then calls `fmt, by_opt = _dash_axis_tick_formats(plots, fake, {})[axis]` and returns `fmt` when `not by_opt` and `_dash_fmt_kind(fmt) == "t"`, else `""`.
  - `_dash_apply_axis_options` gains `formats=None`. On an axis with no date kind:
    - when `var` is a date variable (S18's `date_vars`) and `col` is not None, `col = pd.Series(_dash_date_units(col, vk))`, so minmax reads Stata values;
    - when S18's `fb` is empty and `by_opt` is false, `fb = _dash_axis_unit_format(plots, letter, date_vars, formats)`, applied by S18's code with `date_kind=None`.
  - `_dash_finish_secondary_axes` does the same for a mixed `"y2"`/`"x2"`.
- **TR-35.11 Saved wiring** (`_make_figure_body`, CRITICAL: warn first).
  - After 30221: `_xa2, _ya2 = _dash_axis_vars(plots, axis_no=2)`.
  - After 30283: `_x2_date = self._figure_date_kind(plots, "xvar", _xa2, axis_no=2)` and `_y2_date` likewise.
  - 30312: `_dash_mark_date_axes(fig, _x_date, _y_date, _x2_date, _y2_date)`.
  - 30385: `date_axes={nm: (v, _dash_date_fmt(getattr(self, "formats", {}).get(v), k)) for nm, v, k in (("y2", _ya2, _y2_date), ("x2", _xa2, _x2_date)) if k}, fmt_cache=getattr(self, "_fmt_models", None)`.
  - 30405 and 30660: `formats=getattr(self, "formats", {}) or {}`.
  - Directly after the `_dash_finish_secondary_axes(…)` call (30660-30666): `_dash_finish_off_date_axes(fig)` (TR-35.16, ratification 06oct2026).
  - After 30650: `_dash_layer_in_axis_units(fig, _layer_renderers, list(fig.center[_c_before:]), plot, getattr(self, "date_vars", {}) or {}, getattr(self, "_fmt_models", None))`.
- **TR-35.12 Served wiring** (`_generate_app_source`, HIGH: warn first). The same calls in the generated text:
  - `_rax2` and the four-kind `_rkinds` (35069-35073), still unpacked by `_dash_mark_date_axes(_tfig, *_rkinds)`;
  - `_xa2, _ya2` (after 35134); `_x2_date`/`_y2_date` (after 35172); the four-kind mark (35193);
  - `date_axes=…, fmt_cache=_fmt_cache` (35206), using `_FORMATS`;
  - `formats=_FORMATS` (35268, 35417);
  - `_dash_finish_off_date_axes(fig)` directly after the generated `_dash_finish_secondary_axes(…)` (35417-35423; TR-35.16, ratification 06oct2026);
  - in `_dash_draw_layer` after 35010: `_dash_layer_in_axis_units(fig, fig.renderers[_before:], list(fig.center[_before_c:]), plot, _date_vars, _fmt_cache)`.
  - The redraw's throwaway figure takes the pass too, which is harmless: only its data is copied.
- **TR-35.13 Copy lists (R2, X.1 append only).**
  - Functions, after `"_dash_axis_date_kind", "_dash_axis_positions",` (33105): `"_dash_layer_axis_names", "_dash_date_transform", "_dash_spec_units", "_dash_layer_in_axis_units", "_dash_axis_unit_format", "_dash_days_from_civil", "_dash_civil_from_days", "_dash_literal_to_ms", "_dash_stata_number_of", "_dash_off_date_ticks", "_dash_finish_off_date_axes",` (the last six by the 06oct2026 ratification, TR-35.16).
  - Constants, after `"_STATA_MS_MAX", "_STATA_EPOCH_UNIX_MS",` (33024): `"_DASH_DATE_UNITS_TAG", "_DASH_DATE_UNITS_JS", "_DASH_JS_MS_LIMIT",` (D-35h; the last by the 06oct2026 ratification).
  - `_DASH_AXIS_FINISH_JS` is copied by value as S21 listed it.
- **TR-35.14 Maps (A148, X.5).** These go under `# WP-30 S35 (P1.23a): Date positions on every axis (P1.23 part a)` in `test/function_test_map.py`, alphabetical, each mapped to a node of `test/test_date_axis_residuals.py`:
  - `'GlyphMapper._axis_kind'` → `TestTheUnitRule::test_axis_kind_reads_the_layers_axis`;
  - `'GlyphMapper._base_in_axis_units'` → `TestABaseOnADateAxis::test_the_base_reader`;
  - `'GlyphMapper._literal_on_axis'` → `TestLiteralLayersOnADateAxis::test_the_literal_reader`;
  - `'GlyphMapper._unit_kind'` → `TestTheUnitRule::test_unit_kind_follows_the_axis`;
  - `'_dash_axis_unit_format'` → `TestADateBesideANumber::test_the_unit_format_rule`;
  - `'_dash_date_transform'` → `TestTheDateTransform::test_one_shared_model_per_kind`;
  - `'_dash_layer_axis_names'` → `TestRangeAndPcLayersGetADateAxis::test_the_axis_names_rule`;
  - `'_dash_layer_in_axis_units'` → `TestTheDateTransform::test_the_layer_pass_rule`;
  - `'_dash_spec_units'` → `TestTheDateTransform::test_spec_units_reads_only_dash_transforms`;
  - `'_dash_civil_from_days'` → `TestOffDateLiterals::test_the_civil_calendar_round_trips`;
  - `'_dash_days_from_civil'` → `TestOffDateLiterals::test_the_civil_calendar_round_trips`;
  - `'_dash_finish_off_date_axes'` → `TestOffDateLiterals::test_the_off_date_axis_is_ticked_in_stata_numbers`;
  - `'_dash_literal_to_ms'` → `TestOffDateLiterals::test_the_literal_converter`;
  - `'_dash_off_date_ticks'` → `TestOffDateLiterals::test_the_off_date_ticks_rule`;
  - `'_dash_stata_number_of'` → `TestOffDateLiterals::test_the_number_reader`.
  The fifteen entries stay alphabetical within the anchor (the last six by the 06oct2026 ratification).

  `test/program_coverage_map.py` is unchanged (no Stata program).
- **TR-35.15 Security (rule 1).**
  - The transform's code is a module constant with no user text. Its one argument is a kind from a fixed set, checked before use (a hostile kind raises).
  - Field names attached to a transform are the layer's own validated variable names or dash's `__dash_` columns.
  - The plan's `units` hold `[field, kind]` pairs: kinds only from the fixed set, field names as data in the CustomJS args (JSON-serialised by Bokeh), never pasted into code, and never used as object keys.
  - The notes carry a layer type, a count and a number written by `_fmt_num`, cut to 40 characters.
  - Literal conversion (TR-35.16) never raises and never warns on any input (NaN, ±Infinity, 1e300, text); it bounds a period's year before integer arithmetic, so no int64 overflow, and NaN or ±Infinity never reaches a ColumnDataSource or a FixedTicker. `dash_stata_number_of` is fixed code with a kind from the fixed set and no `Date`, `eval` or `Function`.
  - No `shell=True`, no `eval`/`exec` of user text. The extractor's python block never calls Stata.

- **TR-35.16 Literal dates past Stata's range (A77, ratified 06oct2026; D-35j, D-35k).** All new names are placed directly after `_dash_units_to_axis` (dash_render.py:569-616) unless stated, and none edits `_dash_units_to_axis`, `_dash_date_units`, `_dash_stata_value_of` or `_stata_dates_to_datetime`.
  - `_DASH_JS_MS_LIMIT = 8_640_000_000_000_000`, the largest `|ms|` a JavaScript `Date` holds (`new Date(8.64e15 + 1)` is invalid). It is below 2**53, so every whole millisecond within it is exact in a double.
  - `_dash_days_from_civil(y, m, d)` and `_dash_civil_from_days(z)` (numpy int64, vectorised): proleptic-Gregorian days since 1970-01-01 by the era/400-year arithmetic (`era = floor(y'/400)`, `doe = yoe*365 + yoe//4 - yoe//100 + doy`), valid for every integer year, astronomical numbering (year 0 is 1 BC). They use no `datetime`, pandas or `datetime64` parsing, and the caller bounds `|y| <= 300000` first.
  - `_dash_literal_to_ms(values, kind)` gives a float64 array of epoch ms:
    - it reads values as `_dash_units_to_axis` does (:584-588; text is NaN);
    - for `td`, `v * 86_400_000.0 + E`; for `tc`/`tC`, `v + E` (`E = _STATA_EPOCH_UNIX_MS`);
    - for a period kind, `f = floor(v)`, then the year and sub-period by floor division (`tm`: `y = 1960 + f // 12`, month `f % 12 + 1`; `tq`: 3 months a quarter; `th`: 6 months a half; `tw`: `jan1(y) + 7 * (f % 52)` days with `y = 1960 + f // 52`; `ty`: `y = f`). The start of `f` and of `f + 1` come from `_dash_days_from_civil(…) * 86_400_000`, and a fraction lies linearly between them, as `_dash_units_to_axis` places it (:608);
    - a period value whose year is not finite or has `|y| > 300000` is NaN before any integer conversion;
    - the result is NaN unless it is finite and `abs(ms) <= _DASH_JS_MS_LIMIT`. Every operation runs under `np.errstate(all="ignore")` and `warnings.catch_warnings()`, so it never raises and never warns;
    - inside `[_STATA_MS_MIN + E, _STATA_MS_MAX + E]` it equals `_dash_units_to_axis(values, kind)` element for element (exact equality; the test proves it).
  - `_dash_stata_number_of(ms, kind)` is the scalar inverse, the Stata number at a position: None for a non-finite value, `abs(ms) > _DASH_JS_MS_LIMIT` or a kind outside `_STATA_DATE_KINDS`. `td` gives `(ms - E) / 86_400_000` (fraction kept); `tc`/`tC` give `ms - E`; a period kind gives the floored period of `_dash_civil_from_days(floor(ms / 86_400_000))` (`tw`: `(y - 1960) * 52 + min(51, (day - jan1) // 7)`, as `_dash_period_values` :21190-21223). Inside Stata's dates it equals `_dash_stata_value_of` (:21028-21060).
  - `_DASH_FMT_JS` (dash_render.py:17458) gains, at its end, `dash_civil_from_days(z)` and `dash_stata_number_of(ms, kind)`, line-for-line twins of the two Python functions. They use integer arithmetic only, with no `Date` object and no `Date.UTC(`. `_DASH_FMT_MODEL_JS` (:21124-21128) gains one line after its first: `if ((_dash_v === null || _dash_v === undefined) && kind) { _dash_v = dash_stata_number_of(%s, kind); }`, with the same `%s` substitution as the line above it (`tick` or `value`). A tick or value outside Stata's dates is then written by `dash_fmt_text` as Stata's `display` writes that number (D-35k), not ".". A data column never holds such a value (the loader makes it missing, :472-489), so tooltips, sliders and the CSV are unchanged.
  - `_dash_off_date_ticks(lo, hi, n, kind)` (placed, with `_dash_finish_off_date_axes`, directly after `_dash_axis_count_ticks`) takes `a = _dash_stata_number_of(lo, kind)` and `b` likewise, and gives None if either is None. Otherwise it takes `_dash_natscale_ticks(a, b, n)` (for a period kind, whole periods only) and places each tick by `_dash_literal_to_ms(t, kind)`, dropping NaN; None when empty.
  - `_dash_axis_count_ticks` (:22550-22591): where `_dash_unix_ms_to_unit` gives None for an end (:22578-22581), it returns `_dash_off_date_ticks(lo, hi, n, kind)` instead of None. One branch; nothing else in the function changes. Run `gitnexus impact _dash_axis_count_ticks -d upstream -r dash` first and warn if HIGH or CRITICAL.
  - `_dash_finish_off_date_axes(fig)` acts on each `DatetimeAxis` of *fig* (below, left, above, right) whose ticker is Bokeh's `DatetimeTicker` (an option's ticker is left alone). It reads the axis's kind (`_dash_axis_date_kind(fig, letter or letter + "2")`) and the values on its range (`_dash_secondary_values` over the axis's range name). When `min` or `max` lies outside `[_STATA_MS_MIN + E, _STATA_MS_MAX + E]`, it sets `ax.ticker = FixedTicker(ticks=_dash_off_date_ticks(lo, hi, n, kind) or [])` with `n = getattr(fig, "_dash_numticks", {}).get(letter, 5)`. It returns how many axes it changed. It is called in both modes directly after `_dash_finish_secondary_axes` (saved :30660-30666 in TR-35.11; served :35417-35423 in TR-35.12). S21's date hold (D-21e) keeps the fixed ticks after a move.
  - Every date axis's formatter is already dash's `CustomJSTickFormatter` (primary :30314-30322 saved, :35194-35199 served; y2/x2 by TR-35.7). Bokeh's `DatetimeTickFormatter` never labels an axis, and a guard test asserts it.

## Boundaries

- **Batch partners:** S34 (scheme lookup: `SchemeParser._resolve_path`, `resolve_or_fallback`, `_include`, `DashRenderer._scheme_for`, dash.ado's lookup, help "Stata scheme support" remedy) and S36 (`SchemeParser.style_bundle`, its table, its extractor, the 26 scheme files, `scheme_truth.json`). S35 touches none of these, nor any scheme file.
  - **Shared functions, disjoint hunks.** `_generate_app_source` is S35's (R12); S34's four one-line edits there (:35093, :35562, :35584, :35646) stand only if the orchestrator grants S34's Q1 at 12.0, and S35 does not edit those lines. `_glyph_layer_lines` takes S35's two tuple anchors and S34's scheme block (:33479); neither is the other's. All three sections append to `test/test_mode_parity.py`'s `CORPUS` (R8: the merger keeps every case); only S35 appends a class there.
- **S17 (landed) owns part b:** `_apply_colorvar`, `_dash_colorvar_cuts`, `_dash_colorvar_bins`, `_dash_apply_z_options`, `_dash_build_hover`, `map_histogram`'s measure tag and `key_text_truth.json`. S35 only appends classes to their shared test file.
- **Later sections:**
  - S44: the date ticker for `%td`-`%ty` axes and mixed date-labelled axes, and lifting D-21e's date hold.
  - S49: `horizontal` swaps of `_dash_figure_date_kind` keys, `_dash_axis_vars`, `_axis_kind` letters and the pass's letter map.
  - S51: `t*` options and their `axis(2)` routing. S52: `add`. S56: `text()`/`ttext()`. S57: the worker.
- **Not touched:**
  - `_build_sources_and_figures`, `_dash_common_count_ticks`, `_dash_share_by_scales`, `_build_filter_widgets`, the four appliers;
  - `_dash_units_to_axis`, `_dash_date_units`, `_dash_axis_positions`, `_dash_date_axis_spec`, `_dash_apply_tick_option`, `_dash_apply_axis_spec` (S18's form);
  - `_FILTER_JS` except through `_DASH_AXIS_FINISH_JS`;
  - dash.ado, dash_parse.mata, the tracking documents (A145), `ALLOWED` and `_MUST_WARN` in `test_mode_parity.py` (R8).
- **Edited by the 06oct2026 ratification (TR-35.16), nothing else in them:** `_DASH_FMT_JS` (two functions appended at its end), `_DASH_FMT_MODEL_JS` (one line), `_dash_axis_count_ticks` (one branch), `GlyphMapper._drop_off_dates` (the keyword-only `reach`; HEAD's words unchanged for `"stata"`).
- **Not in scope:** axis-option numbers outside Stata's dates (HEAD's `_dash_axis_positions` rule, D-35k); the all-layer `minmax` (P2.20); twoway's `#N` date tick choice (P2.19, S44); the colour key and tooltips (S17); fractional periods (P2.32).

## Stata truth

**New extractor** `scripts/extract_date_axis_truth.do`. It copies the head of `scripts/extract_date_units_truth.do` (path-free: `local repo : env DASH_REPO`, refused with exit 198 if empty; `version 19`; `set graphics off`). Its work directory comes from `tempfile` plus a suffix, made with `mkdir` or exit 9, never a fixed name under `c(tmpdir)`. It opens with `adopath ++ "<repo>/"` and `global dash_nobrowser 1`, and is run only as:
```sh
mkdir -p <scratch>/s35/x
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s35/x $WT/scripts/extract_date_axis_truth.do
```
It writes `test/fixtures/date_axis_truth.json` (`git add -f`).
- `_meta` holds `stata_version`, `born_date`, `dash_commit` (`git rev-parse HEAD` written by `shell` to a file and read back, as the copied head does; never `shell=True`) and `extracted`, plus `generated_by` and `method`.
- It runs twoway only, so it is the same before and after the fix.
- Data: `sysuse sp500, clear`; `gen obs = _n`; `gen d2 = date + 30` (`%td`); `gen int m = mofd(date)` (`%tm`); `gen int yr = year(date)` (`%ty`). `set scheme s2color`. Every graph is `name(g, replace)`.
- Per case it records `.g.plotregion1.xscale.curmin/curmax`, `.yscale.curmin/curmax` and, with a second axis, `.g.plotregion2.yscale`/`.xscale` (the y2 scale lives in `plotregion2`; measured below). It also records the SVG label texts read by `scripts/svg_truth.py` `svg_texts`, and whether a `ddmonCCYY`/`CCYYmM` date label is shown.
- Each key holds `x` and `y` (and `x2`/`y2` where a second axis is drawn) as `[curmin, curmax]` floats, `labels` (the SVG texts in document order) and `dates_shown` (which axes show a date label).
- A backtick is written `\x60`.

| Key | twoway command | Measured 03oct2026 (StataNow 19.5) |
|---|---|---|
| `literals.scatteri_td` | `(line close date) (scatteri 1300 15400)` | X 14976..15431; labels 01jan2001 … 01apr2002 |
| `literals.pci_td`, `pcarrowi_td` | `(line close date) (pci 1200 15400 1400 15450)`; `pcarrowi` | X 14976..15450 |
| `literals.function_range_td` | `(line close date) (function y=1300, range(15400 15450))` | X 14976..15450 |
| `literals.function_norange_td` | `(line close date) (function y=1300)` | X 0..15340; labels 01jan1960 … 01jan2000 |
| `literals.scatteri_tm` | `(line close m) (scatteri 1300 504)` | X 492..504; labels 2001m1 … 2002m1 |
| `literals.scatteri_offrange` | `(line close date) (scatteri 1300 99999999)` | X 14977..1.000e+08; labels 02jan2001 2.50e+07 … 1.00e+08 (twoway draws it) |
| `literals.scatteri_ty_negative` | `(line close yr) (scatteri 1300 -500)` | recorded by 35-01, not compared (added by the 06oct2026 ratification; no Stata run at planning) |
| `range.rarea_datey`, `range.rcap_datey` | `rarea date d2 close`; `rcap date d2 close` | Y 14976..15370; y labels dates, title Date/d2 |
| `pc.datey`, `pc.datex` | `pcspike date open d2 close`; `pcspike open date close d2` | date axis on y (Y 14976..15370) / on x (X 14976..15370) |
| `axis2.datey_y2num` | `(scatter date close) (scatter volume close, yaxis(2))` | Y 14976..15341 (dates); Y2 4103..25000 |
| `axis2.datex_x2num` | `(scatter close date) (scatter close obs, xaxis(2))` | X 14976..15341 (dates); x2 numbers |
| `axis2.y2date` | `(line close date) (line d2 date, yaxis(2))` | Y2 14976..15370; y2 labels dates |
| `axis2.y2date_n5` | the same, `ylabel(#5, axis(2))` | Y2 14976..15370; labels 01jan2001 01apr2001 01jul2001 01oct2001 01jan2002 |
| `axis2.y2date_range` | the same, `yline(15200, axis(2)) yscale(range(14900 15500) axis(2))` | Y2 14900..15500 |
| `axis2.y2_lfit` | `(line close date) (line d2 date, yaxis(2)) (lfit d2 date, yaxis(2))` | Y2 14976..15370 |
| `mixed.date_first`, `obs_first`, `td_tm` | `(scatter close date) (scatter close obs)`; reversed; `(scatter close date) (scatter close m)` | X 0..15340; labels 01jan1960 … 01jan2000 / 0 5000 10000 15000 / %td |
| `mixed.minmax_date_first`, `minmax_lfit_first`, `minmax_obs_first` | each with `xlabel(minmax)` (lfit: `(lfit close date) (scatter close obs)`) | X 1..15340; labels `02jan1960 31dec2001` / `1 15340` / `1 15340` |
| `mixed.bar_date_y` | `(bar date obs in 1/20) (scatter close obs in 1/20)` | Y 0..15005; labels 01jan1960 … |
| `base.bar_date_base` | `bar date obs in 1/20, base(14970)` | Y 14970..15005 |

The measured column is from research p1-23's `truth1.do`-`truth5.do` and this file's probes `<scratch>/s35/p35.do`, `p35c.do` (run 03oct2026 through the slot). Representative lines:
```
q0 Y2: 14976 .. 15370        (line close date) (line d2 date, yaxis(2))
q2 Y2: 14900 .. 15500        ... yline(15200, axis(2)) yscale(range(14900 15500) axis(2))
q4 Y2: 14976 .. 15370        ... (lfit d2 date, yaxis(2))
q5 Y: 14976 .. 15341   Y2: 4103 .. 25000     (scatter date close) (scatter volume close, yaxis(2))
p3_scatteri_offrange X: 14977 .. 1.000e+08
p5_mixed_n5 labels ['01jan1960', '01jan1970', '01jan1980', '01jan1990', '01jan2000']   (xlabel(#5) on the mixed axis)
p7_bar_date_mixed_y Y: 0 .. 15005
p8_bar_date_base Y: 14970 .. 15005
```
- One measured twoway quirk is not S35's. In `(line close date) (scatteri 15400 15400, yaxis(2))`, twoway labels x `15000 … 15400` in numbers, because S18's format rule picks the literal's group. dash keeps the date labels on its date axis, the documented first-layer divergence (dash.sthlp:2909).
- dash's y2 `#5` ticks are its tsnatscale model's (15007 15066 15127 …) where twoway draws 01jan2001 01apr2001 … (P2.19, S44). DA-05 asserts dash's rule and prints twoway's.

**Truth block (R1).** In `test/test_wp30_truth.cscript`, between S01's `S35 start` and `S35 end` lines, under `* ==== S35 P1.23a: Date positions on every axis ====`.
- Its python helpers sit directly above the header, at top level, with no brace inside the gate:
  - `_da_read(path)` is the saved page's one document (WP-29 `_du_read` form);
  - `_da_app(path)` is one session of the generated app with its attach replaced (`_du_app` form);
  - `_da_axes(doc)`, `_da_units(doc, ptype)`, `_da_hull(doc, letter, name)` and `_da_move(doc, value)` read dash's values.
- Each case loads sp500 as the extractor does, runs twoway and reads its values, then runs `dash …, name(zdaK)`, `dash build, saving("<work>/zdaK.html")`, `_dash_serve_spec, specpath() datapath()` and the generated app. It compares through `_w30_expect`/`_w30_done`.

The cases:
- **DA-01** The four literal commands of `literals.*_td`: in both modes the literal's x, back through `_dash_stata_value_of(v, "td")`, equals 15400 (and 15450 for pci, pcarrowi and function), and the x axis is a DatetimeAxis.
- **DA-02** `(line close m) (scatteri 1300 504)`: the literal is at month 504, and the x axis is a DatetimeAxis, both modes.
- **DA-03** `rarea`/`rcap date d2 close`, `pcspike date open d2 close` and `pcspike open date close d2`: the axis twoway labels with dates is a DatetimeAxis in dash, whose formatter's `fmt` is `%td`. dash's data hull in units is `[14977, 15370]`, inside twoway's extent. Both modes.
- **DA-04** `axis2.datey_y2num` and `axis2.datex_x2num`: the first axis is a DatetimeAxis whose hull in units lies within twoway's `plotregion1` extent, and the second is a LinearAxis. Both modes.
- **DA-05** `axis2.y2date`, `_range`, `_n5`:
  - the right axis is a DatetimeAxis;
  - with the range, dash's y2 inner hull in units equals twoway's `plotregion2` `[14900, 15500]` within 1e-6, and the y2 Span is at `_dash_units_to_axis(15200, "td")`;
  - with `#5`, every y2 tick is a whole day and the ticks equal `_dash_axis_count_ticks(lo, hi, 5, "td")` of dash's own `lo`/`hi`; twoway's labels are printed (P2.19).
  - Both modes.
- **DA-06** `axis2.y2_lfit`: the lfit's y in units lies in `[15007, 15370]`, both modes.
- **DA-07** `mixed.date_first` and `obs_first`:
  - dash's x axis is not a DatetimeAxis, and its inner hull in Stata units equals twoway's `[0, 15340]` within 1e-6 (S21's natscale 0(5000)15000 plus the data);
  - the date layer's x carries the `td` transform, and its twin positions equal the variable's values;
  - the first tick text is `01jan1960` (date first) or `0` (obs first), as twoway's first label.
  - Both modes.
- **DA-08** `mixed.minmax_date_first`: dash's ticks equal `[r(min), r(max)]` of `summarize date` (14977, 15340). twoway's `[1, 15340]` is printed (P2.20).
- **DA-09** `mixed.bar_date_y`: dash's y inner hull equals twoway's `[0, 15005]`, and the bar's filled base is 0. `base.bar_date_base`: the bar's bottom, back in units, is 14970, and the y hull equals twoway's `[14970, 15005]`. Both modes.
- **DA-10** `literals.scatteri_offrange` (A77 ratified 06oct2026: drawn):
  - in both modes the scatteri's x is `99999999 * 86400000 + (-315619200000)` = 8639684294400000 exactly, and `_dash_stata_number_of(x, "td")` is 99999999;
  - dash's x data hull in Stata numbers reaches 99999999, as twoway's X max `1.000e+08` does (dash's hull ⊇ `[14977, 99999999]`);
  - neither `dash build, saving(<work>/da10.html)` nor `dash build, saving(<work>/da10.py) server` (S23's trial) prints a `(note:  dash: scatteri` line;
  - the x axis is a DatetimeAxis whose ticker is not Bokeh's `DatetimeTicker`, its ticks equal `_dash_off_date_ticks` of dash's own hull, and every tick text equals `_dash_fmt_text(_dash_stata_number_of(t, "td"), "%td")`; twoway's labels are printed.
- **DA-11** The DA-07 graph with a range filter on `close`, moved in the generated app: the date layer's x still carries the transform, and the x hull after S21's re-finish is in Stata units (below 1e6), as the saved re-finish computes it under node.
- **DA-12** `literals.scatteri_ty_negative` (A77 ratified 06oct2026): in both modes the scatteri's x is `-77945673600000` (01jan of year -500, astronomical, by `_dash_days_from_civil`), `_dash_stata_number_of(x, "ty")` is -500, no `(note:  dash:` line names it, and no x tick lies at -2208988800000 (01jan1900, where `Date.UTC(0, 0, 1)` would put year 0); dash's ticks over its hull (natscale(-500, 2002, 5) is -500 0 500 … 2000) put year 0 at -62167219200000. twoway's X extent and labels are printed.

## TDD test stubs

### Regression tests, appended to `test/test_date_axis_residuals.py` (S17's file) under a banner `# ==== WP-30 P1.23a (section 35): date positions on every axis ====`

Red at the batch-12 base unless marked guard. Every class that draws is parametrized `mode in MODES`.

**Helpers** (S35's, prefixed `_da`):
- `_da_frame()`: 12 rows, `date = 14977 + 30*i` (`%td`), `d2 = date + 30` (`%td`), `m = 492 + i` (`%tm`), `yr = 1990 + i` (`%ty`, added by the 06oct2026 ratification), `close = 1200 + 10*i`, `volume = 5000 + 100*i`, `obs = 1..12`, `g = i % 2`.
- `_da_fig(mode, plots, go=None, filters=None, data=None)`: the saved figure (`test_date_range._saved(tmp_path, …)[0].figures["g1"]`) or the served one (`test_served_dates._served_fig` of `test_date_range._served(tmp_path, …)[0]`), plus the warnings. `js_texts` is `test_display_format_sites.js_texts`.
- `_da_layer(fig, glyph_type, k=0)`: the k-th renderer of that glyph type.
- `_da_units(r, prop)`: the drawn values in axis units, `dr._dash_date_units(col, k)` when `k = dr._dash_spec_units(spec)`, else the column.
- `_da_inner(fig, letter, name="default")`: S21's `dr._dash_range_hull` of that range.
- `_da_move_saved(r)` / `_da_move_served(doc)`: S21's `_saved_move`/`_served_move` with a `RangeSlider` on `close` set to its lower 60%.
- `_ms(d)`: S17's constant.

**Literal layers.**
- Test: `TestLiteralLayersOnADateAxis::test_the_literal_reader` (unit). `_literal_on_axis` on a figure marked `("td", None)` gives `[_ms(15400)]` and `off [False]`. On an unmarked or `(None, None)` figure the values are unchanged. `99999999` gives `[8639684294400000.0]` and off `[False]` (drawn, A77 ratified 06oct2026); `1e9` (past 8.64e15 ms) gives NaN and off `[True]`; NaN gives NaN and off `[False]`. Red: AttributeError.
- Test: `::test_scatteri_is_placed_at_its_date[mode]`. `(line close date) (scatteri 1300 15400)` (`values [[1300.0, 15400.0]]`): Scatter x `== [_ms(15400)]`, y `[1300.0]`. Red: x 15400.
- Test: `::test_pci_and_pcarrowi_are_placed_at_their_dates[pci|pcarrowi-mode]`. Segment `x0 == [_ms(15400)]`, `x1 == [_ms(15450)]`, y unchanged. Red: 15400.
- Test: `::test_function_range_is_in_days[points|fallback|norange-mode]`. `function`, `expr "1300"`, `range "15400 15450"`, with stored `points` and without: Line `x_fn` runs from `_ms(15400)` to `_ms(15450)`. Red: 15400..15450. `norange` (`literals.function_norange_td`, no `range`, fallback grid 0..1): `x_fn` runs from `_ms(0)` to `_ms(1)` and `_da_inner(fig, "x")[0] <= _ms(0)`, as twoway's X reaches 0. Red: 0..1 ms.
- Test: `::test_a_monthly_scatteri[mode]`. `(line close m) (scatteri 1300 504)` with `m` `%tm`: x `== [dr._dash_units_to_axis([504], "tm")[0]]`. Red.
- Test: `::test_a_date_y_literal_and_one_on_a_second_date_axis[mode]`. `(line date obs) (scatteri 15000 6)` gives y `[_ms(15000)]`. `(line close date) (line d2 date, yaxis(2)) (scatteri 15300 15300, yaxis(2))` gives y `[_ms(15300)]` on range `y2`. Red.
- Test: `::test_an_off_range_literal_is_drawn_at_its_number[mode]` (A77 ratified 06oct2026; replaces the dropped-with-a-note test). `(line close date) (scatteri 1300 99999999) (scatteri 1300 15400)`: the first scatteri's x is `[8639684294400000.0]` and y `[1300.0]`, the second's x `[_ms(15400)]`, and no recorded warning contains `scatteri` or `not drawn`. Red: x 99999999 (raw).
- Test: `::test_the_literal_is_in_the_hull[mode]`. `(line close date) (scatteri 1300 15400)`: `_da_inner(fig, "x")[1] >= _ms(15400)`. Red: S21's raw-SIF exclusion.
- Test: `::test_the_positions_hold_after_a_filter_move[mode]`. With the range filter, after the move the scatteri x is still `[_ms(15400)]`. Red.
- Test: `::test_a_literal_on_a_numeric_axis_is_unchanged[mode]` (guard). `(scatter close obs) (scatteri 1300 6)`: x `[6.0]`. `(scatter close obs) (scatteri 1300 99999999)`: x `[99999999.0]`, no note.

**Literals past Stata's dates (A77, ratified 06oct2026; TR-35.16).** Class `TestOffDateLiterals`. `E = -315619200000`. The oracle for a civil date is numpy, `_np_ms(y, m, d) = int(((np.datetime64(y - 1970, "Y").astype("datetime64[M]") + (m - 1)).astype("datetime64[D]") + (d - 1)).astype("datetime64[ms]").astype(np.int64))`, which holds every year used here (measured at `c96facd`: `_np_ms(50, 1, 1) == -60589296000000`, `_np_ms(0, 1, 1) == -62167219200000`). Each unit test runs under `warnings.simplefilter("error")`, so a warning fails it.
- Test: `::test_the_literal_converter[<case>]` (unit). `dr._dash_literal_to_ms([v], kind)[0]` equals the expected value exactly. Cases:
  - `td` -679351 (31dec0099) → -59011545600000; -679350 (01jan0100) → -59011459200000; 2936549 (31dec9999) → 253402214400000; 2936550 (01jan10000) → 253402300800000; -1500000 (20feb-2147) → -129915619200000; 99999999 → 8639684294400000; 100003653 → 8.64e15; 100003654 → NaN; -99996347 → -8.64e15; -99996348 → NaN; 14977.5 → `_ms(14977) + 43200000`;
  - `tc` 8640315619200000 → 8.64e15; 8640315619200001 → NaN; -8639684380800000 → -8.64e15; -8639684380800001 → NaN;
  - `tm` 96479 (9999m12) → `_np_ms(9999, 12, 1)`; 96480 (10000m1) → `_np_ms(10000, 1, 1)`; -22321 (0099m12) → `_np_ms(99, 12, 1)`; -23520 (0000m1) → `_np_ms(0, 1, 1)`; -22920 (0050m1) → `_np_ms(50, 1, 1)`; 96480.5 → halfway between 10000m1 and 10000m2;
  - `ty` 50 → `_np_ms(50, 1, 1)` (never 1950's -631152000000); 0 → `_np_ms(0, 1, 1)`; -500 → -77945673600000; 99, 100, 9999, 10000 → `_np_ms(y, 1, 1)`; 275760 → `_np_ms(275760, 1, 1)` (inside the bound); 275761 → NaN (8640009504000000 is past 8.64e15); 300001 → NaN (the year guard);
  - `tw`, `tq`, `th` at year 99 and year 10000 → `_np_ms` of their first day;
  - every kind: NaN, `inf`, `-inf`, `1e300`, `-1e300` and `"A"` → NaN, with no warning and no exception.
- Test: `::test_it_equals_the_stata_rule_inside_stata_dates[<kind>]` (unit). 10,000 seeded values per kind inside 0100-9999, fractions included, plus both ends: `_dash_literal_to_ms` equals `_dash_units_to_axis` element for element (`np.array_equal`, NaN never present).
- Test: `::test_the_civil_calendar_round_trips` (unit). `_dash_days_from_civil` equals `_np_ms(y, m, d) // 86400000` for every month's first and last day of years -1000..-990, -1..101, 1959..1961, 9998..10001 and 275759, and `_dash_civil_from_days` inverts it.
- Test: `::test_the_number_reader` (unit). `dr._dash_stata_number_of(ms, kind)` inverts every finite case of `test_the_literal_converter` (floored for a period kind; the `td` fraction kept), equals `_dash_stata_value_of` on 10,000 seeded in-range positions, and is None for NaN, ±inf, `8.64e15 + 1` and a kind outside the fixed set.
- Test: `::test_the_js_number_reader_equals_the_python_one[<kind>]`. `js_runner.run_js` runs `_DASH_FMT_JS` under node (prefixed `'use strict';`) and calls `dash_stata_number_of(ms, kind)` over the cases above and 10,000 seeded positions in ±8.64e15. It equals `_dash_stata_number_of` (null for None). The two-digit-year cases are explicit: `ty` 50 → 50, `ty` 0 → 0, `tm` -22920 → -22920, `td` of `_np_ms(50, 1, 1)` → -697612. Also `"Date.UTC(" not in dr._DASH_FMT_JS` and `"Date" not in dr._DASH_DATE_UNITS_JS`. Red: no `dash_stata_number_of`.
- Test: `::test_the_tick_text_past_stata_dates` (unit, node). `js_texts(dr._dash_fmt_tick_formatter("%td", "td", "", {}), [8639684294400000.0, -59011545600000.0, _ms(14977)], "tick") == ["1.00e+08", "-679351", "02jan2001"]`, each equal to `dr._dash_fmt_text(dr._dash_stata_number_of(t, "td"), "%td")`; `%ty` of `_np_ms(-500, 1, 1)` writes `-5.0e+02` and of `_np_ms(50, 1, 1)` writes `50`. No text is `.` and none matches `^[+-]\d{6}`. Red: `.`.
- Test: `::test_the_off_date_ticks_rule` (unit). `_dash_off_date_ticks(_ms(14977), 8639684294400000.0, 5, "td")` equals `[_dash_literal_to_ms([t], "td")[0] for t in _dash_natscale_ticks(14977, 99999999, 5)]`; for `ty` over `_np_ms(-500, 1, 1)`..`_np_ms(2002, 1, 1)` it holds `_np_ms(0, 1, 1)` and not -2208988800000; None for a NaN end. `_dash_axis_count_ticks` of the same `td` ends and 5 gives the same list (where HEAD gives None). Red: AttributeError / None.
- Test: `::test_drawn_in_both_modes[<case>-mode]` (A77's drawing tests). Each case's literal positions equal `_dash_literal_to_ms` of its numbers exactly, its x axis is a DatetimeAxis, `_da_inner(fig, "x")` reaches them, and no warning names the layer:
  - `scatteri_10000`: `(line close date) (scatteri 1300 2936550)` → x `[253402300800000.0]`;
  - `scatteri_year99`: `(line close date) (scatteri 1300 -679351)` → x `[-59011545600000.0]`;
  - `pci_negative`: `(line close date) (pci 1200 -1500000 1400 15400)` → `x0 [-129915619200000.0]`, `x1 [_ms(15400)]`;
  - `pcarrowi_10000`: `(line close date) (pcarrowi 1200 15400 1400 2936550)` → `x2 [253402300800000.0]`;
  - `function_offrange`: `(line close date) (function y=1300, range(-700000 -679000))` → `x_fn` runs from `_dash_literal_to_ms([-700000], "td")` to that of -679000;
  - `ty_negative`: `(line close yr) (scatteri 1300 -500)` → x `[-77945673600000.0]`;
  - `tm_10000`: `(line close m) (scatteri 1300 96480)` → x `[_np_ms(10000, 1, 1)]`;
  - `y_axis`: `(line date obs) (scatteri 99999999 6)` → y `[8639684294400000.0]`.
  Red: raw numbers on the date axis.
- Test: `::test_drawn_after_a_filter_move[mode]`. `scatteri_10000` and `ty_negative` with the range filter: after the move the literal x is unchanged, `_da_inner(fig, "x")` still reaches it, and the axis ticker is still the build's FixedTicker. Red.
- Test: `::test_the_off_date_axis_is_ticked_in_stata_numbers[mode]`. `literals.scatteri_offrange`'s spec: `_dash_finish_off_date_axes` has replaced the `DatetimeTicker` with a FixedTicker whose ticks equal `_dash_off_date_ticks` of the axis's own values; the `ty_negative` spec has a tick at `_np_ms(0, 1, 1)` and none at -2208988800000; no axis of either figure carries a `DatetimeTicker` or a `DatetimeTickFormatter`. Red: DatetimeTicker.
- Test: `::test_a_literal_past_the_browser_is_left_out_with_one_note[mode]`. `(line close date) (scatteri 1300 1e9) (scatteri 1300 1e300) (scatteri 1300 15400)`: the first two draw 0 points, the warnings hold exactly one `dash: scatteri: 1 point(s) past the dates a browser can draw (years -271821 to 275760) not drawn.` per layer (two in all), and `json.dumps` of every ColumnDataSource's data with `allow_nan=False` succeeds. Red: drawn at 1e9 raw.
- Test: `::test_the_served_build_names_the_literal_past_the_browser`. The `1e9` spec through `dr.ServerAppBuilder(sp, dp).build(ap, trial=True)` under `catch_warnings(record=True)` gives that note exactly once (S23's relay). Red.

**Range and pc layers.**
- Test: `TestRangeAndPcLayersGetADateAxis::test_the_axis_names_rule` (unit). `dr._dash_layer_axis_names` for each type family and axis option, a literal, and an empty name. Red: AttributeError.
- Test: `::test_a_range_type_of_a_date_y[rarea|rbar|rspike|rcap|rline|rconnected|rcapsym|rscatter|tsrline-mode]`. `yvar1 "date"`, `yvar2 "d2"`, `xvar "close"`: y is a DatetimeAxis whose formatter args hold `fmt "%td"`, and x is not. Red: LinearAxis.
- Test: `::test_a_pc_type_of_a_date_y[pcspike|pccapsym|pcarrow|pcbarrow|pcscatter-mode]` and `::test_a_pc_type_of_a_date_x[…]`. The date side is a DatetimeAxis. Red.
- Test: `::test_a_pc_with_one_date_end_is_mixed[mode]`. `y1var "date"`, `y2var "close"`: y is not a DatetimeAxis, the `y0` property carries the `td` transform and `y1` none, and `_da_units` of `y0` equals the dates. Red: ms.
- Test: `::test_the_axis_reads_the_first_bounds_format[mode]`. `rarea date d2 close` with `date` `%tdCCYY-NN-DD`: the y formatter's `fmt` is `%tdCCYY-NN-DD`. Red: no date axis.
- Test: `::test_after_a_filter_move[mode]`. `(rarea date d2 close) (lfit date close)` with the range filter: after the move y is still a DatetimeAxis, the rarea's `y1`/`y2` carry no transform, and the lfit's y (refit in served, frozen in saved) lies in `[_ms(14977), _ms(15337)]`. Red: LinearAxis; the served redraw's `_rkinds` reads no range key.

**Second axes.**
- Test: `TestASecondAxisLeavesThePrimaryDate::test_the_decision_partitions_by_axis` (unit). `_dash_figure_date_kind(plots, "yvar", "", dv, axis_no=1/2)` for `axis2.datey_y2num`'s plots gives `"td"`/None; `_dash_axis_vars(plots, axis_no=2) == ("", "volume")`. Red: TypeError (no `axis_no`).
- Test: `::test_a_numeric_y2_keeps_the_date_y[mode]` and `::test_a_numeric_x2_keeps_the_date_x[mode]`. The left (below) axis is a DatetimeAxis, and the right (above) one is a LinearAxis that is not a DatetimeAxis. Red: LinearAxis.
- Test: `TestASecondDateAxis::test_a_date_y2_is_a_date_axis[mode]`. `(line close date) (line d2 date, yaxis(2))`:
  - the right axis is a DatetimeAxis with `fmt "%td"`;
  - `dr._dash_axis_date_kind(fig, "y2") == "td"`;
  - the y2 inner hull lies in `[_ms(15007), _ms(15337)]`.
  Red: LinearAxis.
- Test: `::test_a_date_x2[mode]`. `(scatter close obs) (scatter close date, xaxis(2))`: the above axis is a DatetimeAxis. Red.
- Test: `::test_count_ticks_on_a_date_y2[mode]`. `go {"ylabel2": "#5"}`: the y2 ticks equal `dr._dash_axis_count_ticks(lo, hi, 5, "td")` and each converts back to a whole day. Red: ticks unplaced.
- Test: `::test_line_range_and_labels_on_a_date_y2_are_dates[mode]`. `go {"yline2": "15200", "yscale2": "range(14900 15500)", "ylabel2": "15000 15300"}`: the Span on y2 is at `_ms(15200)`, the inner y2 hull is `[_ms(14900), _ms(15500)]`, and the ticks are `[_ms(15000), _ms(15300)]`. Red: 15200 ms; range stretched.
- Test: `::test_a_fit_on_a_date_y2_is_in_ms[mode]`. Adding `(lfit d2 date, yaxis(2))`, the fit's y lies in `[_ms(15007), _ms(15337)]`. Red: 15007..15337 raw.
- Test: `::test_a_date_y2_after_a_filter_move[mode]`. `(line close date) (line d2 date, yaxis(2)) (lfit d2 date, yaxis(2))` with the range filter: after the move the y2 range is still in ms, the lfit's y (refit by the served redraw on its four-kind `_rkinds` figure) lies in `[_ms(15007), _ms(15337)]`, and the saved (node) and served values agree. Red.
- Test: `::test_yscale2_log_on_a_date_axis_draws_dates[mode]`. `go {"yscale2": "log"}`: a DatetimeAxis and one note naming `d2`. Red: LogAxis.

**A date beside a number.**
- Test: `TestTheUnitRule::test_axis_kind_reads_the_layers_axis` and `::test_unit_kind_follows_the_axis` (unit), over marked, unmarked and four-kind figures. Red: AttributeError.
- Test: `TestADateBesideANumber::test_the_unit_format_rule` (unit). `_dash_axis_unit_format` gives `%td` for date-first, `""` for obs-first, lfit-first and literal-first, and `%tm` for `(scatter close m) (scatter close obs)`. Red: AttributeError.
- Test: `::test_the_raw_date_is_drawn_in_stata_units[mode]`. `(scatter close date) (scatter close obs)`:
  - x is not a DatetimeAxis;
  - the date renderer's `glyph.x` gives `dr._dash_spec_units(...) == "td"`, and `_da_units` equals `14977 + 30*i`;
  - the obs renderer's x carries no transform.
  Red: no transform.
- Test: `::test_every_glyph_variant_carries_the_transform[mode]`. glyph, selection, nonselection, hover and muted glyphs (where Glyph models) all carry it. Red.
- Test: `::test_labels_and_jitter_follow[mode]`. `(scatter close date, mlabel(close) jitter(5)) (scatter close obs)`: the LabelSet x and the jitter column's spec carry `td`. Red.
- Test: `::test_the_hull_is_in_stata_units[mode]`. `_da_inner(fig, "x")` lies in `[0, 20000]`. Red: about 1e12.
- Test: `::test_explicit_labels_count_and_range[xlabel_list|xlabel_count|xscale_range-mode]`. `xlabel(0 5000 10000 15000)`, `xlabel(#5)` and `xscale(range(0 16000))` each give an inner hull within `[0, 16000]`, and the `#5` ticks equal `dr._dash_natscale_ticks(1, 15307, 5)`. Red: Range1d -5.03e10..1.057e12 (Gap 1).
- Test: `::test_by_panels_share_one_scale_in_stata_units[mode]`. `by(g)`: both panels share one x Range1d, inner within `[0, 20000]`. Red.
- Test: `::test_the_labels_are_the_first_layers_format[mode]`. Date-first: `js_texts(fig.xaxis[0].formatter, [0.0, 15000.0], "tick") == ["01jan1960", "25jan2001"]`. Obs-first and lfit-first: no `%t` format. Red: Bokeh's default formatter.
- Test: `::test_minmax_reads_stata_units[xlabel|xtick-date_first|lfit_first-mode]`. Ticks (xtick: the CustomJSTicker's `extra`) `== [14977.0, 15307.0]`. Red: ms. Guard row: obs-first gives `[1.0, 12.0]`.
- Test: `::test_after_a_filter_move[mode]`. After the move the date renderer still carries the transform, and the x Range1d is in Stata units; saved under node equals served. Red.
- Test: `::test_the_refinish_budget_holds`. S21's `TestTheRefinishBudget` harness on a 500k-row mixed axis: the served re-finish adds at most 0.2 s per figure per move (A9). Red: the axis is ranged in ms, so the hull assertion of the harness fails.
- Test: `::test_a_date_bar_beside_a_number[mode]`. `(bar date obs) (scatter close obs)`: `top` carries `td`, and the filled `__dash_base` is 0.0. Red: -315619200000 or 1970.
- Test: `::test_a_period_bar_on_a_mixed_axis_is_one_unit_wide[mode]`. `(bar close m) (scatter close obs)`: `width == 1.0`, the x field is `m` with the `tm` transform, and there is no `_BAR_XC` column. Red: ms width.
- Test: `::test_xline_on_a_mixed_axis_is_a_stata_value[mode]` (guard). `xline(15200)`: the Span is at 15200.0.

**The transform.**
- Test: `TestTheDateTransform::test_one_shared_model_per_kind` (unit). Two calls with one cache return the same object; it has the tag, `args == {"kind": "td"}`, and no `eval(`, `Function(` or `document.` in either code. Red: AttributeError.
- Test: `::test_a_hostile_kind_is_refused`. `"td'); alert(1); //"`, `""`, `None` and `"t" * 10000` raise ValueError. Red.
- Test: `::test_spec_units_reads_only_dash_transforms`. A str, a field without transform, a foreign CustomJSTransform, a bad tag, and a `dash_date_units:xx` tag give None; a good one gives its kind. Red.
- Test: `::test_the_js_twin_equals_the_python_twin[td|tc|tC|tw|tm|tq|th|ty]`. `js_runner.run_js` runs the transform's `v_func` through `new Function("kind", "xs", "'use strict';\n" + code)` (BokehJS's `_make_transform` form, `use_strict` in bokeh 3.9's bokeh.js) over 10,000 seeded values per kind. The values cover Stata's whole range, the bounds ±1 ms, NaN, ±Infinity and 1e300. The output equals `_dash_date_units` (NaN for NaN, exact otherwise). Red.
- Test: `::test_the_layer_pass_rule` (unit). On hand-built figures it transforms 0 properties for a computed type, a literal type, a date axis or an unmarked figure. A foreign transform is never stacked. It returns the count. Red.
- Test: `TestTheDateAxisTruth::test_the_fixture_is_stamped` and `::test_the_cases_are_there` (guards once 35-01 has written the fixture). The four `_meta` keys exist, and every key of the Stata truth table is present.

**Bases.**
- Test: `TestABaseOnADateAxis::test_the_base_reader` (unit). `_base_in_axis_units` gives `_ms(14970)` on a marked `td` y, 14970.0 on a mixed axis, `8639684294400000.0` with no note for 99999999 (A77 ratified 06oct2026), and None with one note for `1e300`. Red: AttributeError.
- Test: `::test_an_explicit_base_is_a_date[bar|spike|dropline|area-mode]`. `<t> date obs, base(14970)`: the base property equals `_ms(14970)`. Red: 14970 ms.
- Test: `::test_an_off_range_base_is_drawn_at_its_date[mode]` (replaces the default-with-a-note test, ratification 06oct2026). `bar date obs, base(2936550)`: the base property equals `253402300800000.0`, and no warning names `base(`. Red: 2936550 ms.
- Test: `::test_a_base_past_the_browser_is_the_default_with_a_note[mode]`. `bar date obs, base(1e300)`: the bar stands on the default base, with exactly one `dash: bar: base(1e+300) is past the dates a browser can draw` note. Red: drawn at 1e300 ms.
- Test: `::test_after_a_filter_move[mode]`. `bar date obs, base(14970)` with the range filter: after the move the bar's base property is still `_ms(14970)` and `top` carries no transform. Red: 14970 ms.

**Guards.**
- Test: `TestNonDateFiguresAreUnchanged::test_no_transform_and_the_same_axes[scatter|lfit|bar|yaxis2|xaxis2|by|colorvar-mode]`. There is no tagged CustomJSTransform, axis classes are as at the base (recorded in the failure file), and `_dash_date_kinds2 == (None, None)`.
- Test: `::test_a_date_axis_layer_carries_no_transform[mode]`. `line close date` has no transform.

### Chrome, appended to S04's `test/test_csp_browser.py`

- Test: `TestTheDateTransformUnderTheCsp::test_saved_page[canvas|webgl]`. The mixed page (12 rows, then 12,000 rows over `_WEBGL_THRESHOLD`) renders with zero policy violations, and the x range read by `_CspProbe` (or `range_probe.RangeProbe`) satisfies `start < 14977 < 15307 < end < 1e6`. After the range filter moves, it still holds. Red: end about 1e12.
- Test: `::test_served_page`. The same under the launcher, through `test_server_serves._Launched` and `_build_app` as S04's served tests use them. Red.
- Test: `TestOffDateAxesInTheBrowser::test_saved_page[scatteri_offrange|ty_negative]` (A77, ratified 06oct2026). The saved page of each `TestOffDateLiterals` spec loads within S04's probe timeout (no hung ticker) with zero console errors and zero policy violations. The x range read by `_CspProbe` reaches the literal's ms. The drawn x tick positions read from the page equal the build's FixedTicker; `ty_negative` has one at -62167219200000 and none at -2208988800000. Every drawn tick text equals `_dash_fmt_text(_dash_stata_number_of(t, kind), fmt)`, none is `.` and none matches `^[+-]\d{6}`. After the range filter moves, the same holds. Red: `.` labels and a DatetimeTicker.
- Test: `::test_served_page[scatteri_offrange|ty_negative]`. The same under the launcher. Red.

### Flips in `test/test_default_axes.py` (35-03)

The two nodes of E12. Each gets a docstring reason and a `Flipped:` line.

### Parity corpus (`test/test_mode_parity.py`, R8, appended)

Under a comment `# WP-30 P1.23a (section 35)`. Every name starts `P1.23a: `, so `-k P1.23a` selects them.
- `CORPUS` (8): "P1.23a: scatteri and function on a date axis", "P1.23a: rarea of a date y", "P1.23a: a date second axis with yline2 and yscale2 range", "P1.23a: a date beside a number", "P1.23a: a date beside a number under by()", "P1.23a: an explicit base on a date axis", "P1.23a: an off-range scatteri on a date axis" (drawn since the 06oct2026 ratification: `test_same_warnings` compares two silent lists and `_glyph_profile` the drawn position), "P1.23a: a literal past the browser's dates" (`scatteri 1300 1e9` on a date axis: `test_same_warnings` compares the one browser-limit note in both modes).
- `MOVE_CORPUS` (2): "P1.23a: a date beside a number after a range move", "P1.23a: a date second axis with a fit after a range move".
- `ALLOWED` and `_MUST_WARN` are not edited.
- New class, appended at the end of the file: `TestTheTwoModesAgreeOnDateUnits::test_the_same_properties_carry_the_same_units[<each S35 CORPUS and MOVE_CORPUS name>]`. `_spec_of` drops a spec's `transform`, and both modes keep epoch ms in the source, so `_glyph_profile` cannot see a served page that lacks the transform. Per renderer (glyph, selection, nonselection, hover and muted glyph) and per `LabelSet`/`Arrow`, it lists `(model type, property, dr._dash_spec_units(spec))` for every coordinate property, saved and served (for the MOVE cases: served through `_served_after_move`, saved through `_saved_with_qualifier`, as `TestAFilterMoveAgrees` pairs them), and asserts the lists are equal. For each case whose name contains "a date beside a number" it also asserts at least one `"td"` (red at base: none in either mode).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Literal placement, after a move | pytest `TestLiteralLayersOnADateAxis` | `date_axis_truth.json` | yes |
| Literals past Stata's dates: converter, number reader (Python and node), ticks and labels, drawing, browser-limit note (ratification 06oct2026) | pytest `TestOffDateLiterals`; Chrome `TestOffDateAxesInTheBrowser` | numpy `datetime64[ms]` oracle | yes (+ S23 trial build), before and after a move |
| Range/pc date axes, after a move | pytest `TestRangeAndPcLayersGetADateAxis` | — | yes |
| Axis partition, second date axes, `#N`, lines, range, fits, after a move | pytest `TestASecondAxisLeavesThePrimaryDate`, `TestASecondDateAxis` | — | yes (saved under node) |
| Mixed axes: transform, hull, by(), labels, minmax, bars, budget | pytest `TestADateBesideANumber`, `TestTheUnitRule` | — | yes |
| Transform and twins | pytest `TestTheDateTransform` (node) | — | n/a |
| Bases, after a move | pytest `TestABaseOnADateAxis` | — | yes |
| Non-date unchanged | pytest `TestNonDateFiguresAreUnchanged`; R10 digest | — | yes |
| Policy | Chrome `TestTheDateTransformUnderTheCsp`, `TestOffDateAxesInTheBrowser` | — | yes (+ WebGL for the transform) |
| twoway truth | `test_wp30_truth.cscript` DA-01..DA-12 via the driver, `WP30_ONLY=S35` | live twoway + fixture | yes |
| Parity | G3 `test_mode_parity.py`: 8 CORPUS + 2 MOVE_CORPUS cases, `TestTheTwoModesAgreeOnDateUnits` (the transform per property) | — | yes, before and after a move |
| Registries | R2 registry tests | — | — |

Acceptance criteria:
- **AC-35.1** Every regression node above fails at the batch-12 base and passes after 35-12. The failure text is in `<scratch>/35-P1.23a-failure.txt`.
- **AC-35.2** `python3 -m pytest test/test_date_axis_residuals.py test/test_default_axes.py test/test_date_units.py test/test_date_range.py test/test_served_dates.py test/test_dates.py test/test_dual_axis.py test/test_bar_range_geometry.py test/test_mode_parity.py -q -p no:cacheprovider` reports 0 failed.
- **AC-35.3** `python3 -m pytest test/test_csp_browser.py -q -n0 -p no:cacheprovider -k "DateTransform or OffDateAxes"` reports 7 passed, not skipped, on this Mac with Chrome.
- **AC-35.4** The driver run of `test_wp30_truth.cscript` with `WP30_ONLY=S35` prints DA-01..DA-12 PASS and `ALL CHECKS PASSED`, with no SKIP and no `r(` error.
- **AC-35.5** `grep -c "_dash_raw_sif" dash_render.py` prints 0, and `grep -c '"_dash_layer_in_axis_units"' dash_render.py` prints 1. The registry tests are green, and `test_single_y_output_matches_prefix_baseline` is unchanged.
- **AC-35.6** One full run through the queue is green before the commit.
- **AC-35.7** (ratification 06oct2026) `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "OffDateLiterals or off_range or past_the_browser"` reports 0 failed and 0 skipped; `grep -c "Date.UTC(" dash_render.py` equals its batch-12-base count (no new use); `grep -c "outside Stata's dates (01jan0100 to 31dec9999) not drawn" test/test_date_axis_residuals.py` prints 0.

## Tasks

**Commit boundary.** Tasks 35-01 to 35-15 form the one P1.23a commit, made by 35-15 on `wp30-s35` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s35` after one full run through the queue. Subject: `Place dates in their Stata units on every axis (WP-30 P1.23a)`.
- The body opens with `<scratch>/35-P1.23a-failure.txt`, then the measured defect (E11), then what changed and where, in both modes. It names the threat-free design of the transform (fixed code, a kind from a fixed set).
- Then one line each of:
  - `Regression: test/test_date_axis_residuals.py::<Class>::<test> -- failed at <batch-12 base sha> with <text>` (and the Chrome nodes, and `Regression: test/test_wp30_truth.cscript DA-0k`);
  - `Flipped: <node> -- <old expectation> was wrong because <E12's reason>` (one per flip, from `<scratch>/s35/35-flips.txt`);
  - `Fixture: test/fixtures/date_axis_truth.json (scripts/extract_date_axis_truth.do)`;
  - `BUGS.md: "Dates on range, pc, immediate and second axes are drawn at raw or millisecond positions, and a date layer beside a numeric one is drawn in epoch milliseconds" (closed)`.

Every command runs from `$WT`. `<scratch>` is the orchestrator's WP-30 scratch directory; this file's probes ran in its `s35/` subdirectory. No body, BUGS, CHANGELOG or help line names a tool or vendor (G7).

<task type="auto" id="35-01">
  <name>Check contracts, measure twoway, write failing tests</name>
  <files>scripts/extract_date_axis_truth.do, test/fixtures/date_axis_truth.json, test/test_date_axis_residuals.py</files>
  <action><![CDATA[
    1. Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-12-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s35`. Confirm `<scratch>/batch-12-impact.txt` records the maintainer's approval of S35's CRITICAL rows (Risk factor 1). Run `mkdir -p <scratch>/s35/x`.
    2. Write the contract of the landed sections, each with its file:line, to `<scratch>/s35/contract.txt`. It lists:
       - S21: `def _dash_layer_extent`, `def _dash_axis_plan`, `def _dash_refinish_axes`, `def _dash_tag_hull_roles`, `^_DASH_AXIS_FINISH_JS`, every `_dash_raw_sif` line, and the plan's `layers`/`bars` keys;
       - S27: `def _base_value`, `def _base_zero`, the four call sites, `def _dash_finish_auto_bases`;
       - S14: `def _bar_extent` and its two callers;
       - S18: `def _dash_axis_tick_formats`, `_dash_apply_axis_options`' `plots`/`date_vars` keywords, `_dash_apply_axis_spec`'s `date_kind`/`option` keywords, `_dash_finish_secondary_axes`' `numeric_formats`/`date_vars`;
       - S17: the file test/test_date_axis_residuals.py, its `MODES` and `_ms`;
       - S04: test/test_csp_browser.py, `_CspProbe` and the `_Launched` harness;
       - S23: `def build(` with `trial`;
       - S01: the stub lines `S35 start`/`S35 end` and the map anchor `# WP-30 S35 (P1.23a)`;
       - S26: `map_function`'s fallback mark and the line building `fn_source`;
       - S31: the `option`/`by_graph`/`colours`/`ref_in` keywords on `_dash_apply_axis_spec`, `_dash_apply_tick_option` and their calls in `_dash_apply_axis_options` and `_dash_finish_secondary_axes`;
       - S32/S33: `_style_restyle` after `fig.scatter` in `map_scatteri`, and the `_immediate_labels(…, color_idx=…)` calls in `map_scatteri` and `map_pcarrowi`;
       - S34 (same batch, for the record): the four template lines of its TR-34.13 and its `_glyph_layer_lines` scheme block, which S35 must not touch.
       If any is missing or named differently, record the landed name. If a function is missing outright, stop and report to the orchestrator without editing.
    3. Create scripts/extract_date_axis_truth.do by "Stata truth", run it through the slot, and run `git add -f test/fixtures/date_axis_truth.json`. Every value must match the table's "Measured" column; a mismatch stops the task. `literals.scatteri_ty_negative` (ratification 06oct2026) is recorded, not compared: write its extent and labels to `<scratch>/s35/35-01-recorded.txt`.
    4. Append to test/test_date_axis_residuals.py exactly the banner, helpers, classes and tests of "TDD test stubs / Regression tests", importing S21's `_saved_move`/`_served_move`/`TestTheRefinishBudget` harness from test/test_default_axes.py as the contract file names them.
    5. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -rf -k "Literal or OffDate or RangeAndPc or SecondAxis or SecondDate or Beside or UnitRule or DateTransform or BaseOnADate or NonDate or DateAxisTruth" > <scratch>/s35/35-01.log 2>&1`. Write `<scratch>/35-P1.23a-failure.txt`: the base sha, each failing node with its one-line reason, then the guards that passed and the axis classes `TestNonDateFiguresAreUnchanged` recorded. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/date_axis_truth.json'));print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), d['axis2']['y2date_range']['y2'])"` prints `True [14900.0, 15500.0]`; `grep -c FAILED <scratch>/s35/35-01.log` is at least 90 (the 06oct2026 ratification added `TestOffDateLiterals`); no `NonDate`, `test_a_literal_on_a_numeric_axis_is_unchanged`, `test_xline_on_a_mixed_axis` or `DateAxisTruth` node is FAILED; `test -s <scratch>/35-P1.23a-failure.txt && test -s <scratch>/s35/contract.txt`.]]></verify>
  <done>The landed contracts were recorded, twoway's date extents and labels were stored in a stamped fixture, and every regression test was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="35-02">
  <name>Write the DA truth block and Chrome check</name>
  <files>test/test_wp30_truth.cscript, test/test_csp_browser.py</files>
  <action><![CDATA[
    In test_wp30_truth.cscript, add the `_da_` python helpers directly above `* ==== S35 P1.23a: Date positions on every axis ====` (top level, no brace inside the gate). Write DA-01 to DA-12 of "Stata truth / Truth block" between S01's `S35 start` and `S35 end` lines. Each case ends with `_w30_done DA-kk "<what>"`, with its expectations through `_w30_expect`. Every file goes under the scaffold's work directory and is erased; `dash clear` and the scheme are restored.
    Append `TestTheDateTransformUnderTheCsp` and `TestOffDateAxesInTheBrowser` (ratification 06oct2026) to test/test_csp_browser.py (S04's file), using its probe and harness and no inline script of its own beyond S04's admitted probe.
    Run the truth script through the driver on the unmodified renderer:
      printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "test_wp30_truth.cscript" > <scratch>/s35/run_test_wp30_truth.do
      WP30_ONLY=S35 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s35 <scratch>/s35/run_test_wp30_truth.do
    (log: `<scratch>/s35/run_test_wp30_truth.log`). Then check that `~/.stata19/console/stata19.rc` still holds `python_exec`. Run the Chrome class. Append their FAIL lines and failing nodes to `<scratch>/35-P1.23a-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "DA-[01][0-9] FAIL" <scratch>/s35/run_test_wp30_truth.log` is at least 11; `grep -c "SKIP" <scratch>/s35/run_test_wp30_truth.log` prints 0; `python3 -m pytest test/test_csp_browser.py -q -n0 -p no:cacheprovider -k "DateTransform or OffDateAxes"` reports 7 failed and 0 skipped.]]></verify>
  <done>Live twoway was compared with dash's saved page and served app in twelve cases and the browser checks were written, and all of them failed on the unmodified tree.</done>
</task>

<task type="auto" id="35-03">
  <name>Flip S21 pins and add parity cases</name>
  <files>test/test_default_axes.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Flip in place, keeping each node name, the two nodes of Evidence E12. `TestRawSifDateLayersStayOut::test_scatteri_on_a_td_axis` moves its literal to 15400 and asserts that the inner x hull reaches `_ms(15400)`. `TestTheHelpers::test_hull_roles` asserts no `_dash_raw_sif` attribute for scatteri, pci, pcarrowi and function. Each gets a docstring reason. Append one `Flipped:` line per parametrized id to `<scratch>/s35/35-flips.txt`.
    Append the parity cases and the `TestTheTwoModesAgreeOnDateUnits` class of "TDD test stubs / Parity corpus" to test_mode_parity.py and nothing else (not `ALLOWED`, `_MUST_WARN` or any profile helper). Run both files on the unmodified renderer, and append the red nodes under `Pinned, red at base after the flip` to the failure file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "RawSif or hull_roles"` fails exactly 6 ids (2 + 4); `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "P1.23a"` collects at least 10 case names and `TestTheTwoModesAgreeOnDateUnits` fails only the ids whose name contains "a date beside a number"; `grep -c '"P1.23a: ' test/test_mode_parity.py` is at least 10; `git diff -U0 test/test_mode_parity.py | grep -c '^-'` prints 1 (the `---` header only: nothing removed).]]></verify>
  <done>S21's two pins asserted literals inside date hulls, keeping their names, and the parity corpus held S35's cases in both modes.</done>
</task>

<task type="auto" id="35-04">
  <name>Decide date kinds per axis</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Run `gitnexus impact _dash_axis_date_kind -d upstream -r dash` in the main checkout (read only) and warn that it is CRITICAL before editing. Make TR-35.1 (with `_dash_layer_axis_names` directly below `_dash_figure_date_kind`), TR-35.2 and TR-35.3. Make `DashRenderer._figure_date_kind` pass `axis_no`. Touch no caller yet: every existing call keeps its meaning. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "axis_names_rule or partitions_by_axis"` and test/test_date_units.py, test/test_served_dates.py and test/test_dates.py.
  ]]></action>
  <verify><![CDATA[The two unit tests pass; the three files report 0 failed; `python3 -c "import dash_render as d, inspect; print(list(inspect.signature(d._dash_figure_date_kind).parameters)[-1], list(inspect.signature(d._dash_mark_date_axes).parameters)[-2:])"` prints `axis_no ['x2_kind', 'y2_kind']`.]]></verify>
  <done>Each axis's date kind could be decided from the layers drawn on it, reading range and paired keys, and a figure could carry its second axes' kinds.</done>
</task>

<task type="auto" id="35-04a">
  <name>Convert literal dates past Stata's range</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Ratification 06oct2026 (A77, "Draw it anyway"). Run `gitnexus impact _dash_axis_count_ticks -d upstream -r dash` and `grep -n "_DASH_FMT_MODEL_JS\|_DASH_FMT_JS" dash_render.py` in the main checkout (read only), record both in `<scratch>/s35/35-04a-impact.txt`, and warn before editing if either is HIGH or CRITICAL.
    Make TR-35.16 exactly:
      - `_DASH_JS_MS_LIMIT`, `_dash_days_from_civil`, `_dash_civil_from_days`, `_dash_literal_to_ms` and `_dash_stata_number_of` directly after `_dash_units_to_axis`;
      - `dash_civil_from_days` and `dash_stata_number_of` appended at the end of `_DASH_FMT_JS`, and the one line in `_DASH_FMT_MODEL_JS`;
      - `_dash_off_date_ticks` and `_dash_finish_off_date_axes` directly after `_dash_axis_count_ticks`, and the one branch in `_dash_axis_count_ticks`.
    Do not edit `_dash_units_to_axis`, `_dash_date_units`, `_dash_stata_value_of`, `_stata_dates_to_datetime` or `_dash_unix_ms_to_unit`. Use no pandas Timestamp, no `datetime`, no `datetime64` string parsing and no `Date.UTC(` or `new Date(<year>, …)`. Wiring of `_dash_finish_off_date_axes` waits for 35-10 and 35-11.
    Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "literal_converter or equals_the_stata_rule or civil_calendar or number_reader or tick_text_past or off_date_ticks_rule"`, then test/test_display_format_writer.py, test/test_display_format_sites.py, test/test_natscale_axes.py and test/test_default_axes.py (HEAD's formatter and count-tick behaviour inside Stata's dates must be unchanged).
  ]]></action>
  <verify><![CDATA[The six named node groups pass with no skip; the four files report 0 failed; `python3 -c "import dash_render as d; print(d._DASH_JS_MS_LIMIT == 8.64e15, 'Date.UTC(' in d._DASH_FMT_JS, d._DASH_FMT_JS.count('function dash_stata_number_of('), d._dash_literal_to_ms([50], 'ty')[0], d._dash_literal_to_ms([1e300], 'td')[0])"` prints `True False 1 -60589296000000.0 nan`.]]></verify>
  <done>A literal date of any year a browser can draw converted exactly to its position and back, in Python and in the page's JavaScript, with no library year range in the way, and a tick past Stata's dates was placed by natscale and labelled with its number as Stata's display writes it.</done>
</task>

<task type="auto" id="35-05">
  <name>Route mapper units through the axis</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `GlyphMapper._on_axis` is CRITICAL (14 impacted). Add `_axis_kind`, `_unit_kind` and `_literal_on_axis` to GlyphMapper beside `_on_axis` (TR-35.4). Give `_on_axis` its `options` parameter and pass `options` at all 13 callers of E3, including the call inside map_lpolyci's local `_on` (which reads `options` from its enclosing scope). Make TR-35.5 in map_scatteri, map_pci_literal, map_pcarrowi and map_function through `_literal_on_axis` (which calls 35-04a's `_dash_literal_to_ms`): a coordinate outside 0100-9999 is drawn at its number with no note (A77, ratified 06oct2026), and only one past the browser's dates is dropped jointly through `_drop_off_dates(…, reach="browser")` with the D-35f words. Add the `reach` keyword to `_drop_off_dates`, leaving HEAD's words and key for `"stata"`. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "literal_reader or UnitRule or drawn_in_both_modes or past_the_browser_is_left_out"` and test/test_date_units.py, test/test_function_expr.py, test/test_immediate_values.py, test/test_pccapsym_pcarrowi.py and test/test_glyphs.py.
  ]]></action>
  <verify><![CDATA[Those runs report 0 failed; `grep "self._on_axis(fig, " dash_render.py | grep -vc "options"` prints 0.]]></verify>
  <done>Computed layers took the kind of the axis they are drawn on, and literal layers were placed in date units on a date axis, past Stata's dates included, with only a value past the browser's dates left out and named once.</done>
</task>

<task type="auto" id="35-06">
  <name>Put bar widths and bases in axis units</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-35.6. Give S14's `_bar_extent` the `fig`/`options` keywords and `_unit_kind`, and pass them from map_bar and map_rbar. Give S27's `_base_zero` the same keywords. Add `_base_in_axis_units` (converting through 35-04a's `_dash_literal_to_ms`, so a base outside 0100-9999 is drawn with no note and only one past the browser's dates falls back with the D-35f note) and call it at S27's four `_base_value` call sites (map_bar, map_area, map_spike, map_dropline, as the contract file records them). Touch no tag, width, colour, applier or label line. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "BaseOnADate or period_bar"` (the off-range and past-the-browser base nodes included), test/test_bar_range_geometry.py and test/test_internal_column_names.py.
  ]]></action>
  <verify><![CDATA[`TestABaseOnADateAxis::test_the_base_reader` and every test_bar_range_geometry.py node pass; `grep -c "_base_in_axis_units(" dash_render.py` prints 5 (the def and four calls).]]></verify>
  <done>Bar widths and default bases followed the axis a layer is drawn on, and an explicit base() was a date on a date axis.</done>
</task>

<task type="auto" id="35-07">
  <name>Build second date axes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-35.7 in `_dash_add_secondary_axes` (the `date_axes` and `fmt_cache` keywords, DatetimeAxis with its formatter, the log note), `_dash_finish_secondary_axes` (kind-aware range(), label, tick, padding and hull record), `_dash_count_axes` (the y2/x2 kind) and `_dash_refline_draw` (the y2/x2 kind and its docstring). Callers pass nothing new yet, so second axes stay numeric until 35-10. Run test/test_dual_axis.py, test/test_axis_options.py, test/test_natscale_axes.py and test/test_default_axes.py.
  ]]></action>
  <verify><![CDATA[Those files report 0 failed; `grep -n "never a date axis" dash_render.py` prints nothing.]]></verify>
  <done>A second axis marked with a date kind could be built as a date axis whose options, ticks and extent read dates.</done>
</task>

<task type="auto" id="35-08">
  <name>Add the date transform and its twins</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_DASH_DATE_UNITS_TAG` and `_DASH_DATE_UNITS_JS` directly after `_dash_units_to_axis`, with the token replacement at import (TR-35.8). Add `_dash_date_transform`, `_dash_spec_units` and `_dash_layer_in_axis_units` directly after `_dash_axis_positions`. Make TR-35.9's Python readers: `_dash_secondary_values`, `_dash_axis_hull`'s centre, and S21's `_dash_layer_extent`. Delete the `_dash_raw_sif` stamp and each skip of it, Python and plan builder. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "DateTransform"`, test/test_default_axes.py (with the 35-03 flips) and test/test_help_claims_7.py.
  ]]></action>
  <verify><![CDATA[`TestTheDateTransform` passes (the JS twin under node included); test_default_axes.py and test_help_claims_7.py report 0 failed; `grep -c "_dash_raw_sif" dash_render.py` prints 0; `python3 -c "import dash_render as d; s=d._DASH_DATE_UNITS_JS; print(len(s) <= 3000, 'eval(' in s, 'Function(' in s, '__DASH_' in s)"` prints `True False False False`.]]></verify>
  <done>A shared, fixed browser-side transform per date kind existed with a Python twin that every coordinate reader applied, and literals were no longer kept out of date hulls.</done>
</task>

<task type="auto" id="35-09">
  <name>Label mixed axes and read minmax</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_dash_axis_unit_format` after `_dash_layer_in_axis_units` (TR-35.10). Give `_dash_apply_axis_options` and `_dash_finish_secondary_axes` the `formats` keyword. On an axis with no date kind, convert the first layer's date column for minmax and fill an empty S18 fallback with `_dash_axis_unit_format`, written with `date_kind=None`. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "unit_format_rule"` and test/test_axis_options.py, test/test_axis_format_fallback.py (S18's file) and test/test_date_range.py.
  ]]></action>
  <verify><![CDATA[The unit test passes and the three files report 0 failed (the date axis's own minmax test stays green).]]></verify>
  <done>A mixed axis could be labelled in its first layer's date format and could read minmax in Stata values.</done>
</task>

<task type="auto" id="35-10">
  <name>Wire the saved figure body</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_make_figure_body` is CRITICAL (4 impacted) before editing. Make TR-35.11's edits, including the call `_dash_finish_off_date_axes(fig)` directly after `_dash_finish_secondary_axes(…)` (TR-35.16, ratification 06oct2026), and nothing else in that method. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "saved and not after_a_filter_move"`, test/test_date_units.py, test/test_date_range.py, test/test_dual_axis.py and test/test_bar_range_geometry.py.
  ]]></action>
  <verify><![CDATA[Every saved-mode regression node except the after-move ones passes; the four files report 0 failed.]]></verify>
  <done>The saved page placed dates on every axis, built second date axes and transformed raw dates on mixed axes, before any move.</done>
</task>

<task type="auto" id="35-11">
  <name>Wire the served app and registries</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn that `_generate_app_source` and `_glyph_layer_lines` are HIGH before editing. Make TR-35.12 in the generated text, plus `_dash_finish_off_date_axes(fig)` directly after the generated `_dash_finish_secondary_axes(…)` call (TR-35.16), and TR-35.13 in the two tuples, at the named anchors only; leave S34's four template lines and its scheme block as they are. Add TR-35.14's fifteen map entries under S35's anchor. If `test_the_served_build_names_the_literal_past_the_browser` cannot be made to pass through S23's trial, stop and report (D-35f): the note never ships in one mode only. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "served and not after_a_filter_move"`, test/test_function_test_map.py, `"test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName"`, `"test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads"`, test/test_served_dates.py and test/test_serve_lifecycle.py.
  ]]></action>
  <verify><![CDATA[Every run reports 0 failed; `grep -c '"_dash_date_transform"' dash_render.py`, `grep -c '"_DASH_DATE_UNITS_JS"' dash_render.py`, `grep -c '"_dash_literal_to_ms"' dash_render.py`, `grep -c '"_dash_finish_off_date_axes"' dash_render.py` and `grep -c '"_DASH_JS_MS_LIMIT"' dash_render.py` each print 1.]]></verify>
  <done>The served app made the same axes, positions and transforms as the saved page from module names it carries.</done>
</task>

<task type="auto" id="35-12">
  <name>Extend the saved re-finish with units</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[
    In S21's `_dash_axis_plan`, write each layer's `units` and each bar's `cunits` (TR-35.9). Prepend `_DASH_DATE_UNITS_JS` once to `_DASH_AXIS_FINISH_JS`, and convert in `dash_axis_extent` and the bar reader with the hasOwnProperty guard. Touch no other line of the constant and none of `_FILTER_JS`. Add a stand-in field to js_runner.py only if the node session lacks one the plan now carries. Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "after_a_filter_move or budget or drawn_after_a_filter_move"`, test/test_default_axes.py, test/test_saved_filter_layers.py, test/test_js_runner.py, test/test_default_axes_chrome.py and test/test_by_scales_chrome.py.
  ]]></action>
  <verify><![CDATA[Every run reports 0 failed and the Chrome tests report passed, not skipped; `python3 -c "import dash_render as d; s=d._DASH_AXIS_FINISH_JS; print(s.count('function dash_date_units('), 'eval(' in s)"` prints `1 False`.]]></verify>
  <done>After a saved move the page's own script ranged mixed and second date axes in the same units as the served re-finish, within the time budget.</done>
</task>

<task type="auto" id="35-13">
  <name>Certify against Stata and Chrome</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file changed in 35-01 to 35-12, plus every test file that names date, `%td`, DatetimeAxis, yaxis, xaxis, scatteri, pci, function, base or minmax (`grep -l`), plus test/test_axis_extents.py and test/test_by_scales.py: `python3 -m pytest <those files> -q -p no:cacheprovider`. A failure outside the flipped list is a pin the list missed: flip it in place with a `Flipped:` line (R9), never delete it, and re-run.
    Then run G3 (`python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider`), `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (expected unchanged), and `python3 -m pytest test/test_csp_browser.py -q -n0 -p no:cacheprovider` (`TestOffDateAxesInTheBrowser` included). Check AC-35.7.
    Through the driver, run test_wp30_truth.cscript with `WP30_ONLY=S35`. Afterwards check that `~/.stata19/console/stata19.rc` still holds `python_exec`.
  ]]></action>
  <verify><![CDATA[All pytest runs report 0 failed and the Chrome runs no skip; `grep -c "DA-[01][0-9] PASS" <scratch>/s35/run_test_wp30_truth.log` prints 12; `grep -c " FAIL\|SKIP" <scratch>/s35/run_test_wp30_truth.log` prints 0; `grep -c python_exec ~/.stata19/console/stata19.rc` is at least 1.]]></verify>
  <done>Stata certified literal, range, second-axis, mixed-axis and base positions against twoway, literals past Stata's dates included, both modes drew alike before and after a move, and the transform and the off-date axes rendered under the page's policy.</done>
</task>

<task type="auto" id="35-14">
  <name>Describe dates on every axis</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In "Axis and Display Options" (R3: S35's title), after the "Computed layers of a date" paragraph (2896-2911; the blank line :2912 follows), add a blank line, a `{pstd}` line, then one paragraph:
    "{ul:Dates on every axis.}  A date is placed in its variable's own units on every axis, as {cmd:twoway} places it, in the saved page and the served app, before and after any filter move. The bounds of the range plots ({cmd:rarea}, {cmd:rbar}, {cmd:rspike}, {cmd:rcap}, {cmd:rline}, {cmd:rconnected}, {cmd:rcapsym}, {cmd:rscatter}, {cmd:tsrline}) and the coordinates of the paired plots ({cmd:pcspike}, {cmd:pccapsym}, {cmd:pcarrow}, {cmd:pcbarrow}, {cmd:pcscatter}) count toward the axis they are drawn on, so {cmd:dash rarea date d2 close} has a date y axis. Each axis is decided by its own layers: a {opt yaxis(2)} or {opt xaxis(2)} layer of a plain number leaves the first axis's dates alone, and a second axis whose layers are dates of one kind is a date axis whose {cmd:axis(2)} labels, ticks, lines and {cmd:range()} read dates, as on the first axis. On a date axis the coordinates of {cmd:scatteri}, {cmd:pci} and {cmd:pcarrowi}, the points of {cmd:function} and an explicit {cmd:base()} of {cmd:bar}, {cmd:spike}, {cmd:dropline} and {cmd:area} are dates too: {cmd:scatteri 1300 15400} on a {cmd:%td} axis is drawn at 01mar2002. A date that shares an axis with a plain number is drawn at its Stata values, the axis labelled in the first layer's date format when that layer draws the date itself ({cmd:(scatter close date) (scatter close obs)} reads 01jan1960 at 0), and {cmd:xlabel(minmax)} there ticks those values. A literal coordinate, a {cmd:function} point or a {cmd:base()} outside 01jan0100 to 31dec9999 is drawn where its number falls on the date axis, as {cmd:twoway} draws it ({cmd:scatteri 1300 99999999} reaches 1.00e+08), and a tick there is labelled with its number, as {cmd:display} writes it. {it:Difference from twoway:} a value past the dates a browser can draw (years -271821 to 275760) is not drawn, and a note says so; the ticks of an axis that reaches past Stata's dates are {cmd:dash}'s natscale ticks over its numbers (0 2.00e+07 ... 1.00e+08 where {cmd:twoway} draws 2.50e+07 ... 1.00e+08). Where the first layer is {cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} or {cmd:function}, which {cmd:twoway} labels with numbers, {cmd:dash} keeps the date axis, as for the fits above."
    Touch no other paragraph: the computed-layers paragraph's "a date layer that shares an axis with a plain number is drawn at its Stata values" is now true for every layer and stays as written. Run `python3 -m pytest test/test_help_conformance.py $(grep -l "Computed layers of a date\|Secondary axes\|scatteri" test/test_help_claims_*.py) -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "Dates on every axis" dash.sthlp` prints 1; `grep -Eic 'claude|anthropic' dash.sthlp` prints 0.]]></verify>
  <done>The help stated where dates are placed on every axis, the second-axis and mixed-axis rules, that literals past Stata's dates are drawn as twoway draws them, and the browser-limit and tick differences from twoway.</done>
</task>

<task type="auto" id="35-15">
  <name>Close P1.23a and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. The title is `WP30_OPEN["P1.23a"]`, verbatim from section-01 Appendix B: `Dates on range, pc, immediate and second axes are drawn at raw or millisecond positions, and a date layer beside a numeric one is drawn in epoch milliseconds`. Re-read the entry's Description. Each REM-08-04 id it lists must name a bullet this commit closes: the range and pc keys (REMAINING.md:1965-1979 (b), (c)), the axis partition (:1980-1990), the literal coordinates (:2015-2022), or a part-a bullet of DROPIN P1.23 (second axis, mixed axis, explicit base). If one does not, stop and report.
       Close the entry in place (`- [x]`) and replace its Resolution with: `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.23a). Each axis's date kind is decided by the layers drawn on it, reading the range (yvar1, yvar2) and paired (y1var, x1var, y2var, x2var) keys and skipping scatteri, pci, pcarrowi and function (_dash_figure_date_kind and _dash_axis_vars with axis_no, _dash_layer_axis_names), so a yaxis(2) or xaxis(2) layer leaves the first axis's dates, and a second axis of dates is a date axis in its variable's format whose axis(2) labels, ticks, lines, range() and #N ticks read dates (_dash_mark_date_axes, _dash_axis_date_kind for y2 and x2, _dash_add_secondary_axes, _dash_finish_secondary_axes, _dash_count_axes, _dash_refline_draw). Computed layers, bar widths and default bases follow the axis a layer is drawn on (GlyphMapper._unit_kind through _on_axis, _bar_extent and _base_zero); scatteri, pci and pcarrowi coordinates and function points are placed in date units on a date axis (GlyphMapper._literal_on_axis), and an explicit base() is read in date units (GlyphMapper._base_in_axis_units); one outside 01jan0100 to 31dec9999 is drawn at its number as twoway draws it, with no note, converted by millisecond and civil-calendar arithmetic that holds every year a browser can draw (_dash_literal_to_ms, _dash_days_from_civil), and only a value past the browser's dates (|ms| > 8.64e15) is left out with one note. An axis reaching past Stata's dates is ticked by natscale over its Stata numbers (_dash_off_date_ticks, _dash_finish_off_date_axes) and labelled with each number as display writes it (_dash_stata_number_of, dash_stata_number_of), never by Bokeh's DatetimeTicker. A raw date beside a plain number on one axis is drawn at its Stata values through one shared browser-side transform per date kind (_dash_date_transform, _dash_layer_in_axis_units), whose Python twin (_dash_spec_units with _dash_date_units) feeds _dash_secondary_values, the hull readers and the by() scale and whose JS twin feeds the saved re-finish; the axis is labelled in the first layer's date format (_dash_axis_unit_format) and xlabel(minmax) reads Stata values. Both renderers draw alike, before and after a filter move, and the transform renders under the page's security policy. Its REM-08-04 ids are confirmed by content against REMAINING.md:1935-2110. Pinned by test/test_date_axis_residuals.py::TestLiteralLayersOnADateAxis::test_scatteri_is_placed_at_its_date, test/test_date_axis_residuals.py::TestRangeAndPcLayersGetADateAxis::test_a_range_type_of_a_date_y, test/test_date_axis_residuals.py::TestASecondDateAxis::test_a_date_y2_is_a_date_axis, test/test_date_axis_residuals.py::TestADateBesideANumber::test_the_raw_date_is_drawn_in_stata_units, test/test_date_axis_residuals.py::TestOffDateLiterals::test_drawn_in_both_modes, test/test_csp_browser.py::TestTheDateTransformUnderTheCsp::test_saved_page, test/test_csp_browser.py::TestOffDateAxesInTheBrowser::test_saved_page, test/test_wp30_truth.cscript DA-01, DA-10; fixture test/fixtures/date_axis_truth.json. Residual, deferred (WP-30): an axis labelled in dates on Stata values ticks by natscale until section 44 gives date-labelled axes twoway's date ticks; an axis reaching past Stata's dates ticks by natscale over its numbers where twoway's ticks differ (2.50e+07 steps on DA-10); xlabel(minmax) reads the first layer only (P2.20); horizontal layers swap their date kinds in section 49.`
    2. Delete the `"P1.23a"` key line from `WP30_OPEN`. `WP30_LISTS["P1.23a"]` stays `("Results that change",)`.
    3. In CHANGELOG.md, replace `<!-- WP-30 P1.23a -->` in place with one line, taking the old values from the failure file: `- Dates are placed in their Stata units on every axis. scatteri, pci and pcarrowi coordinates and function's range() on a date axis were drawn at 1970 (scatteri 1300 15400 at 15400 ms); they are now drawn at the dates they denote (01mar2002), and one outside 01jan0100 to 31dec9999 is drawn at its number, as twoway draws it (scatteri 1300 99999999 reaches 1.00e+08), with its axis's ticks there labelled by number where they read "."; only a value past the dates a browser can draw is left out, with a note. Range plots of a date y (rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, tsrline) and paired plots of a date y or x now get a date axis where dash drew milliseconds on a numeric axis. A yaxis(2) or xaxis(2) layer no longer turns the first date axis numeric, and a second axis of dates shows dates and reads ylabel(#5, axis(2)), yline(15200, axis(2)) and yscale(range(14900 15500) axis(2)) in days, where it showed numbers near 1e12. A date that shares an axis with a plain number is drawn at its Stata values, as twoway draws (scatter close date) (scatter close obs) (dash drew the dates near 9.8e11 beside 1 to 12), labelled in the first layer's date format, and xlabel(minmax) there ticks Stata values. An explicit base() of bar, spike, dropline or area on a date axis is a date (base(14970) is 26dec2000, where dash drew from 1970). (WP-30, P1.23a)`
    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then `git -C $WT merge --no-edit main` (expect `Already up to date.`), then one full run `<scratch>/full_suite_queue.sh $WT <scratch>/35-full-1.log`, launched in the background and waited for on its `exit=` line (E1, E6).
    5. Stage only: `dash_render.py dash.sthlp BUGS.md CHANGELOG.md scripts/extract_date_axis_truth.do test/test_date_axis_residuals.py test/test_default_axes.py test/test_mode_parity.py test/test_csp_browser.py test/function_test_map.py test/test_tracking_documents.py test/test_wp30_truth.cscript`, `test/js_runner.py` if changed, any file 35-13 flipped, and `git add -f test/fixtures/date_axis_truth.json`. Check `git diff --cached --name-only` (G6: never CLAUDE.md, .gitignore, AGENTS.md, .ultraplan/ or *.html). Write the message to `<scratch>/s35/msg.txt` in the boundary's form. Run G7 before and after `git commit -F <scratch>/s35/msg.txt`, and report the sha and the message.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/35-full-1.log` prints `exit=0`, and the summary line above it names no `failed` or `error`; `git log -1 --format=%s` ends `(WP-30 P1.23a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.23a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.23a": "' test/test_tracking_documents.py` prints 0; `grep -c "(WP-30, P1.23a)" CHANGELOG.md` prints 1; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.23a was closed in BUGS.md naming tests that exist, its key was removed, its CHANGELOG marker became the measured Results line, and one green commit on wp30-s35 was ready for the merger.</done>
</task>

## Section completion criteria

- Literal coordinates and function points are at their dates on `%td` and `%tm` axes, y and y2 included, in both modes and after a move. A literal outside 0100-9999 is drawn at its number with no note, its axis ticked and labelled in Stata numbers; only one past the browser's dates is left out with one note, saved and in a served build.
- Range and pc layers of dates get date axes, formatted by their first variable.
- A numeric second axis leaves the first axis's dates. A second axis of dates is a DatetimeAxis whose `#N` ticks, lines, labels, `range()` and computed layers are dates.
- A raw date beside a number is drawn in Stata units through one tagged transform per kind; every Python reader and the saved re-finish read Stata units; the by() scale and `#N` ticks follow; the labels are the first layer's date format; `minmax` reads Stata values.
- Explicit bases are dates on a date axis. Mixed axes stand bars on Stata's 0, one unit wide.
- `date_axis_truth.json` is stamped and named by its test. DA-01..DA-12 PASS through the driver. The Chrome policy check passes in canvas, WebGL and served modes, and the off-date pages render and label their ticks in both modes. Every flip is recorded.
- The registry tests, G3 parity, S21's budgets and the single-y digest are green or unchanged.
- There is one green commit `(WP-30 P1.23a)` on `wp30-s35`: the entry closed in place, its key deleted, its marker replaced.

## Notes

- **Order of the build.** The unit pass must run after the layer is drawn and before the finishers. In the saved page that is inside `_make_figure_body`, before `_dash_finish_secondary_axes` (:30660). In the served app it is inside `_dash_draw_layer`, before `_dash_figure_for` reaches `_dash_finish_secondary_axes` (:35417). Moving it later would range every mixed axis in ms.
- **The source never changes.** A raw date column stays epoch ms in every ColumnDataSource. Do not "fix" a mixed axis by writing a Stata-unit column: the saved row copy, the served data copy, the CSV, hover and brushing all read the source (ratified A76).
- **Glyph variants.** Bokeh draws a selection's other points with `nonselection_glyph`. A transform on `glyph` alone would throw them back to 1e12 on the first brush; the pass covers all five variants.
- **Readers that ignore `transform`.** Any new reader of glyph coordinates (S44's ticker, S47's inner box, S49's transposition, S50's extent, S52's `add`, S56's text) must call `_dash_spec_units`. "Notes for later sections" repeats this.
- **Twin values.** `_dash_date_units` floors period values to whole periods (`_dash_period_values`), and the JS twin does the same. Do not port `dash_unix_ms_to_unit`'s fractional months into the transform.
- **python_exec hazard** (project memory): concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass. Check after 35-02 and 35-13.
- **Shared files (R1-R13).**
  - **R1:** only S35's block of the truth script, with its helpers directly above its header. No area cscript is edited.
  - **R2:** the functions anchor of the S35 row, plus the constants anchor of D-35h, which the merger records as a reconciliation. Map entries go under S35's anchor.
  - **R3:** "Axis and Display Options" only, one new paragraph after :2912. No batch-12 partner edits that title.
  - **R4:** the one Results marker. **R5:** the one entry and its key line.
  - **R7:** the new extractor is run only by S35, and the fixture is never hand-patched.
  - **R8:** `CORPUS` and `MOVE_CORPUS` appended, plus the one class `TestTheTwoModesAgreeOnDateUnits` at the end of the file; `ALLOWED`, `_MUST_WARN` and the profile helpers untouched.
  - **R9:** flips in place, recorded.
  - **R10:** no combined pin moves, and the single-y digest is unchanged (no date on that page). 35-13 checks it.
  - **R11:** S35 is batch 12's finisher editor and keeps A9's budgets.
  - **R12:** `_make_figure_body` and `_generate_app_source` are S35's in batch 12. `_build_sources_and_figures` is not edited.
- **Commit body line forms** are BRIEF's with WP-30 ids. `failed at` is `batch-12-base.txt`'s sha.
- **Notes for later sections.**
  - **S44 (batch 15).** S44 takes over the tick positions D-35e leaves:
    - A mixed axis whose `_dash_axis_unit_format(plots, axis, date_vars, formats)` is a `%td`-`%ty` format takes twoway's date ticks in Stata units, for the default ticker and `#N` alike. twoway measured: 01jan1960 01jan1970 … 01jan2000 for `(scatter close date) (scatter close obs)`, also under `xlabel(#5)`.
    - It drops this file's residual sentence through its own entry.
    - Second date axes (`_dash_axis_date_kind(fig, "y2")`) are date axes for its default ticker too.
    - S44's section file must carry this, because it was not yet written when this file was.
    - (ratification 06oct2026) A date axis whose layers reach past 0100-9999 (a literal or `base()` drawn there, A77) has no tsnatscale answer: `_dash_unix_ms_to_unit` and S44's `dash_ms_to_ts_unit` give None/null there. S35's `_dash_axis_count_ticks` branch answers with `_dash_off_date_ticks` in Python. S44 must keep that branch, must not put Bokeh's `DatetimeTicker` or its own default ticker over `_dash_finish_off_date_axes`' FixedTicker, and its JS `dash_axis_ticks` null keeps the build's ticks (hold) after a move. S44's "a tick past 31dec9999 is dropped" applies to its own model's ticks inside Stata's dates only.
  - **S49 (batch 17):** under `horizontal`, swap the x/y keys of `_dash_layer_axis_names`, the letter in `_axis_kind`/`_unit_kind` callers, and the pass's letter map, in one place each.
  - **S51 (batch 18):** a `t*` option with `axis(2)` reads `_dash_axis_date_kind(fig, "x2")`, and a folded date literal on a mixed axis is a Stata value (register P1.6.9).
  - **S56 (batch 19):** `text()` on axis 2 reads `_dash_axis_date_kind(fig, "y2"/"x2")`. On a mixed axis its coordinates are Stata values, with no transform (value coordinates).
  - **S57 (batch 20):** `_dash_layer_in_axis_units` runs in the redraw on throwaway figures, and the per-document transform cache is `_fmt_cache`. Name both in the thread-safety audit.
- **Scope → test → fix.** The REM-08-04 ids have no literal anchor except C3b/C3c (REMAINING.md:1979); S01 matched all eight to :1935-2110 by content, and 35-15 step 1 re-checks it. Every scope item, both modes, before and after a move:

  | Scope item (bullet) | Tests (after a move) | Truth | Fix |
  |---|---|---|---|
  | Range and pc keys, :1965-1979 (b) (c) (C3b, C3c); DROPIN bullet 2 | `TestRangeAndPcLayersGetADateAxis` (`::test_after_a_filter_move`) | DA-03 | TR-35.1, TR-35.2 |
  | Axis partition, :1980-1990; DROPIN bullet 3 (numeric axis 2) | `TestASecondAxisLeavesThePrimaryDate` | DA-04 | TR-35.1, TR-35.3 |
  | Second date axes, ticks, lines, range, fits (sub-claim 3c); reference lines :1991-1999 on axis 2 | `TestASecondDateAxis` (`::test_a_date_y2_after_a_filter_move`) | DA-05, DA-06 | TR-35.3, TR-35.4, TR-35.7 |
  | Literal coordinates, :2015-2022; DROPIN bullet 1; WP-29 S04/S05 note (function/scatteri/pci/pcarrowi) | `TestLiteralLayersOnADateAxis` (`::test_the_positions_hold_after_a_filter_move`), `TestOffDateLiterals` (`::test_drawn_after_a_filter_move`) | DA-01, DA-02, DA-10, DA-12 | TR-35.4, TR-35.5, TR-35.16 |
  | A date beside a number; DROPIN bullet 4 | `TestADateBesideANumber`, `TestTheDateTransform`, Chrome class (`::test_after_a_filter_move`) | DA-07, DA-11 | TR-35.8, TR-35.9, TR-35.10 |
  | xlabel(minmax) on a mixed axis (sub-claim 4b; WP-29 S04/S05 note) | `TestADateBesideANumber::test_minmax_reads_stata_units` | DA-08 | TR-35.10 |
  | Explicit base; DROPIN bullet 5 (explicit half) | `TestABaseOnADateAxis` (`::test_after_a_filter_move`) | DA-09 | TR-35.6 |

  The remaining ids (C7, C7b, C4, B2b, B7a, B4) fall on these bullets by S01's content match. The WP-29 note's tooltip part is P1.23b (S17).
- **What the row-12 strike changes (answered 06oct2026, CHANGED: "Draw it anyway").** Applied in this file: D-35f, D-35j, D-35k, BR-35.1, BR-35.6, BR-35.9, TR-35.4, TR-35.5, TR-35.16, the tests, DA-10/DA-12, task 35-04a, the help, BUGS and CHANGELOG text. Nothing remains open for this row.
- **Notes for the closeout (S58).**
  - **DROPIN P1.23:** bullets 1-4 ("scatteri/pci/pcarrowi … 1970", "Range and pc plots …", "A layer on yaxis(2)/xaxis(2) …", "A date layer beside a numeric layer …") are closed by P1.23a, commit `<sha>`. Bullet 5 ("Base 0 is 1970, not 1960") is closed by P1.17b (default) and P1.23a (explicit). Bullets 6-8 are P1.23b's (S17). The WP-29 S04/S05 note's minmax and literal parts are closed by P1.23a; its tooltip part by P1.23b.
  - **REMAINING.md:** tag the 08-04 bullets at :1965-1979 ((b), (c)), :1980-1990 and :2015-2022 with `[WP-30 P1.23a, commit <sha>: closed]`. Note on :1965-1979 that (a) was closed by WP-29 P0.8.
  - **BUGS.md:2771** (WP-29 P0.8's residual sentence): S58 notes that its minmax and function/scatteri/pci parts are closed by P1.23a.
  - **GAPS2 / TWOWAY_COVERAGE_AUDIT:** P1.23 cites no GAPS2 or AUDIT id, so no Tracked line changes.
  - **Documented divergences for S58.7:** (ratification 06oct2026, row 12 answered CHANGED) off-range date literals and bases are no longer a divergence: they are drawn as twoway draws them. What remains is that a value past the browser's dates (|ms| > 8.64e15) is left out with a note, and the natscale ticks of an axis reaching past Stata's dates differ from twoway's. The first-layer divergence is extended to literal first layers (help paragraph). PLAN.md:388's "off-range date literals dropped [R12]" is reworded by the orchestrator.
  - **ROADMAP:** the WP-30 entry lists P1.23a and its commit. P2.20 keeps the all-layer minmax.
  - **AGENTS.md invariant** (E7): "A date column stays epoch ms in every source. A layer on an axis that is not a date axis reads it through the one tagged dash_date_units transform per kind, and every Python and JS reader of glyph coordinates converts a field carrying that transform (_dash_spec_units with _dash_date_units, dash_date_units)."
- **Line numbers** are `c96facd`'s, and S01-S34 land first. Symbols and the quoted excerpts are authoritative.
