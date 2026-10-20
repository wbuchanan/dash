# Section 49: Filter widgets -- multi-select, "(missing)", slider direction, reset

> Part of: WP-31 · GAPS3 rows: H2f (H2 filter part; E13 note) · Risk: yellow · Batch: 16 · Depends on: 01 · Blocks: 54 · Tasks: 4, 1 commit · Case-id prefix: U49

## Overview

**What is wrong today.** GAPS3 H2 (GAPS3.md:239): "no multi-select filter, "(missing)" option, slider direction or reset button". `_DASH_FILTER_TYPES = ("dropdown", "range", "slider")` (dash_render.py:39238) and `_DASH_FILTER_SUBOPTS = frozenset({"type", "exclude", "label"})` (:39239) are the whole filter grammar. `_dash_filter_widget` (:34566) builds a `Select` whose first option is `(sentinel, "All")` and whose other options are the distinct non-missing values (`_dash_dropdown_values`, :4237: "a numeric missing value (Stata's `.`) is never listed"), so a reader cannot select the rows where a variable is missing, and cannot select two categories at once. A `Slider`/`RangeSlider` is always left-to-right. Nothing restores the widgets to their opening values but a page reload (saved) or a new session (served).

**After this section** `filter(rep78, type(multi))` draws a Bokeh `MultiChoice` whose chosen values select rows equal to any of them (none chosen = every row); a dropdown or multi over a variable with missing values lists one more option, `(missing)`, which selects exactly the rows where the variable is missing (numeric NaN, string ""); `filter(price, type(slider) direction(rtl))` (also on `range`) draws the slider right-to-left; and a dashboard with at least one filter draws a "Reset filters" `Button` at the end of the filter row that restores every widget's opening value and triggers one recompute. All of this is one rule in both modes: the widget comes from the shared `_dash_filter_widget`, the saved page's mask logic is `_DASH_FILTER_MASK_JS`'s `dash_filter_mask` with two new branches, and the served app's mask is `_dash_frame_filter_mask` with the same two branches.

**Why one section.** The four are edits to one builder (`_dash_filter_widget`), one grammar (`_DASH_FILTER_TYPES/_SUBOPTS` and the Mata filter reader), one JS mask function and one served mask function; they must stay in lock-step (the saved spec the page filters by is what the widget shows). The index makes S49 batch 16's `FilterBuilder`/`_build_filter_widgets` editor; S48 (same batch) edits neither `_FILTER_JS` nor the mask script (its D-48b), so S49 is also batch 16's one `_FILTER_JS` editor for the two mask branches (R12; recorded in both files).

**Test order and commit rule.** One cycle, one commit `(WP-31 H2f)`: 49-01 regression tests red (saved failure text); 49-02 grammar in dash.ado/Mata with the cscript cases; 49-03 widgets, masks and the reset button in both modes; 49-04 node and Chrome verification, help, closing, commit.

### Section decisions (binding on the executor)

- **D-49a. The type word is `multi`.** `filter(var, type(multi))` → `MultiChoice`. It has no twoway meaning (filter() is dash's own), so no refusal is measured. Alternatives considered: `multiselect` (Bokeh's native `<select multiple>` widget is `MultiSelect`; a word naming a Bokeh class would promise that class), `list` (ambiguous with Stata's `list`). `multi` is listed in `_DASH_FILTER_TYPES`, the help and `_dash_filter_effective_type`: over the option limit a `multi` on a numeric or date variable is drawn as `range` with the same note as a dropdown; on a string variable it keeps `multi` with the first `limit` values AND prints the dropdown's existing over-limit note (`_dash_warn_filter_limit` or its neighbour -- grep `filters_options` in `_dash_filter_widget`) naming the variable, the limit and the count dropped, so the truncation is never silent (REVIEW-4 R4-33); the help sentence says so.
- **D-49b. `(missing)` is an option value, never a data value.** Its option value is the per-widget sentinel `"__missing__"` (lengthened with `_` while it collides with a data value, as `"__all__"` is at :34604-34606). It is listed only when the column has at least one missing value (NaN in a numeric or date column; `""`, `None` or NaN in a string column, the fold `_dash_dropdown_values` already applies). Its label is the literal text `(missing)`. The mask branch: a dropdown whose value is the missing sentinel keeps rows where the value is missing; a multi whose chosen values include it keeps missing rows OR rows equal to another chosen value. The spec row carries `"missing_sentinel": "<sentinel>"` so JS and Python read the same token.
- **D-49c. `direction(rtl)` is a filter sub-option on slider and range only.** `direction(ltr)` is accepted and is the default; any other word is refused in dash.ado r(198) `dash: filter(): direction() takes ltr or rtl; got '<word>'`; `direction()` on a dropdown or multi is refused r(198) `dash: filter(): direction() applies to type(slider) and type(range)`. It maps to `Slider(direction="rtl")`/`RangeSlider(direction="rtl")` (the property exists on both and on the Date sliders, research/bokeh-web.md §6).
- **D-49d. The reset button is automatic, one per dashboard, at the end of the filter row.** It is drawn whenever at least one filter widget was built, labelled "Reset filters" (`Button(label=..., button_type="default", tags=["dash_filter_reset"])`). Saved: a `CustomJS` with `args={"widgets": [...], "initial_json": json.dumps([...])}` that sets each widget's `value` to its initial value; because each widget's own `js_on_change("value", ...)` fires per write, the script sets the first n-1 silently is impossible in BokehJS -- instead it sets every widget's value and relies on `_FILTER_JS` being idempotent (each run reads every widget's current value, so n runs end in the same state; the cost is n recomputes, bounded by the `filters` limit of 20). Served: `button.on_click(_dash_reset_filters)` which sets each widget's `value` (and `value_throttled` for sliders) under one `doc.hold("combine")`/`unhold()` so one move runs. Saved sliders: S52 (batch 17) moves their wiring to `value_throttled`, and a programmatic `value` write does not fire `value_throttled` in BokehJS, so S52 TR-52.7 adds to `_DASH_FILTER_RESET_JS`, after `w.value = v;`, the line `if (w.properties.value_throttled !== undefined) { w.value_throttled = v; }` (DECISIONS A28, REVIEW-4 R4-04); S49 writes the constant as below and S52 owns that one-line edit. No `nofilterreset`/opt-out option (keep the surface small; ratify).
- **D-49e. Initial values are recorded at build.** `widget._dash_initial = widget.value` on every filter widget in `_dash_filter_widget`; the saved script's `initial_json` and the served reset read it, so a later widget type needs no further edit.

## Risk: [yellow] -- the saved mask script changes, the filter grammar grows, and MultiChoice is a new widget class on the page

**Why.** `dash_filter_mask` runs on every move of every saved page with a filter; a wrong branch filters every dashboard wrongly. The grammar is read in Mata (by value), in dash.ado's refusals and in Python's `_DASH_FILTER_SUBOPTS`; three readers must agree.

**Risk factors.**
1. The `(missing)` sentinel must never equal a data value (string columns can hold anything).
2. MultiChoice emits `value` as a list; `_FILTER_JS` reads `w.value` and compares a scalar today.
3. The reset's n recomputes on the saved page: with 20 filters and a 100,000-row page this is 20 mask passes.
4. The served `MultiChoice` has no `value_throttled`; the wiring at template :50465-50473 falls back to `value` correctly (it tests `'value_throttled' in w.properties()`).
5. S48 in the same batch adds `__dash_tbl_*` columns; the mask script copies every column, so no interaction, but both sections' parity entries land in one `test_mode_parity.py`.

**Mitigation.**
1. The lengthening loop (D-49b) and `TestTheMissingOption::test_the_sentinel_never_collides` with a column holding `"__missing__"`.
2. A `type === "multi"` branch builds a `Set` of the chosen values; `TestTheMaskScript` runs `js_runner.run_filter_mask` under node with a list value.
3. Acceptable and measured once in `TestTheResetButton::test_n_runs_are_idempotent` (node); the hint in Notes names a future `hold` if BokehJS gains one.
4. `TestTheServedReset::test_one_move_runs` counts `_on_filter_change` calls under `doc.hold`.
5. Disjoint CORPUS entries; the merger applies S48 then S49.

## Dependencies

- **Depends on: 01.**
- **Blocks: 54** (ARIA labels on the new widgets and the reset button).
- **Parallel batch: 16** with S47 and S48. S49 owns `FilterBuilder`, `_dash_filter_widget`, `_build_filter_widgets`, `_DASH_FILTER_MASK_JS` (inside `_FILTER_JS`), the served filter twin (:50001-50015) and `_dash_frame_filter_mask`; S48 owns `_dash_layout_cell` and the table helpers; S47 owns the function mapper.

## Evidence

### The grammar and the builder

```python
39238 _DASH_FILTER_TYPES = ("dropdown", "range", "slider")
39239 _DASH_FILTER_SUBOPTS = frozenset({"type", "exclude", "label"})
```

`_dash_filter_widget` (:34566-34660): `from bokeh.models import (DateRangeSlider, DateSlider, DatetimeRangeSlider, RangeSlider, Select, Slider)` (:34597); the sentinel loop :34604-34606; `options = [(sentinel, "All")] + [...]` (:34640); `w = Select(title=title, value=sentinel, options=options)`; `w._dash_sentinel`, `w._dash_ftype`. `_dash_dropdown_values` (:4237-4268) drops numeric NaN and folds string None/NaN into `""`.

`FilterBuilder.build_dropdown/build_slider/build_range` (:25525-25760) each call `_dash_filter_widget` and attach `CustomJS(code=_FILTER_JS)` to `"value"`. `_build_filter_widgets` (:45427-45560) routes by `ftype` (`"dropdown"` → build_dropdown; `("slider", "range")` → the two builders after `_dash_filter_rangeable`; else `_dash_warn_filter_type`).

The served twin (template :50001-50015) calls the same `_dash_filter_widget` and wires `on_change('value_throttled' or 'value', _dash_event_throttle(doc, _dash_touch(cb)))` (:50465-50473).

### The mask

`_DASH_FILTER_MASK_JS` (the first component of `_FILTER_JS`, :24612) defines `dash_filter_mask(orig, specs, widgets)`; its dropdown branch compares `v === sel` (numbers through `_dash_groups` for labelled numerics, GAPS2 X1) and its slider/range branches compare bounds. The served twin is `_dash_frame_filter_mask(df, widgets)` (dash_render.py:23304; the spec rows are NOT a parameter -- it reads each widget's attributes), on the copy list.

### Mata and dash.ado readers

`_dash_extract_filters` (dash_parse.mata:4212ff) harvests `filter(...)` groups into `"var, type(dropdown) || var2, type(range)"`; `_dash_filter_refusal(filter, registry, vars_out)` (declared :361) validates each group's variable, `type()` word and `exclude()` names. The executor finds the type-word check with `grep -n '"dropdown"' dash_parse.mata dash.ado` and extends every hit's list.

### Existing tests that pin today's behaviour

- test/test_filters.py::TestBuildDropdown::test_all_option_present_first (:222) -- stays true (All first; `(missing)` goes last).
- test/test_filters.py::TestBuildDropdown::test_options_match_sorted_unique_values (:173) -- on a column with missing values the option count grows by one: flip to assert the extra last option is `(missing)` ONLY when the column has a missing value; `auto_df` `rep78` has 5 missing, so the pinned list changes (Flipped line).
- test/test_filter_widget_data.py (the shared builder's rules) -- any assertion on `w.options` length on `rep78`.
- test/test_unsupported_report_is_true.py / test_help_conformance.py -- the help's filter type list changes with the grammar (R10 counts if pinned).

## User stories

- **US-49.1** As a reader I want to pick two or three repair records at once so that I compare a chosen subset.
- **US-49.2** As a reader I want a "(missing)" choice so that I can see the observations with no value.
- **US-49.3** As an author I want a right-to-left slider so that "at least" thresholds read naturally.
- **US-49.4** As a reader I want one button that puts every filter back so that I recover the full picture without reloading.

## Business requirements

- **BR-49.1** `type(multi)` lists every distinct value (labels applied) as a multi-choice; nothing chosen shows every row; chosen values show rows equal to any of them.
- **BR-49.2** A dropdown or multi over a variable with missing values offers "(missing)" last; choosing it shows exactly the rows with a missing value.
- **BR-49.3** `direction(rtl)` reverses a slider's or range's travel; the bounds and the filtering rule are unchanged.
- **BR-49.4** "Reset filters" returns every widget to its opening value and the dashboard to its opening rows, in both modes.
- **BR-49.5** Unknown words in `type()` or `direction()`, and `direction()` on a dropdown, are refused in one sentence each.

## Technical requirements

- **TR-49.1 Grammar.** `_DASH_FILTER_TYPES = ("dropdown", "range", "slider", "multi")`; `_DASH_FILTER_SUBOPTS = frozenset({"type", "exclude", "label", "direction"})`. The Mata type-word list gains `"multi"`; `_dash_filter_refusal` learns `direction()` with D-49c's two refusals (texts in dash_parse.mata beside the `type()` refusal text); the filter JSON (`filter_json`, dash.ado :10535 region, written by the Mata reader) gains `"direction":"rtl"` when given.
- **TR-49.2 `_dash_filter_widget` multi branch.** After the dropdown branch: `if ftype == "multi":` build `raw_values`, labels and `_by_label` exactly as the dropdown does (factor the shared part into `_dash_dropdown_options(series, vlabels, fmt, storage, date_kind, limit, varname)` returning `(options_without_all, sentinel, has_missing)`), then `from bokeh.models import MultiChoice`; `w = MultiChoice(title=title, value=[], options=[(str(v), _dash_multi_label(text)) for v, text in options], placeholder="All", tags=["dash_filter"])`. **Labels are escaped (REVIEW-4 R4-08, DECISIONS A29).** Choices.js, the library behind `MultiChoice`, defaults `allowHTML: true` -- measured at bokeh 3.8.0: `allowHTML:!0` is in `bokeh/server/static/js/bokeh-widgets.min.js` -- and Bokeh's `multi_choice` view passes no override, so an option label from a value label (`<img onerror=...>`) would be injected as markup (CSP blocks the handler, the markup stays). 49-03 reads the installed bundle: if `allowHTML:!0` (or `allowHTML:true`) is present and no `allowHTML:!1` follows in the MultiChoice view's config, `_dash_multi_label(text) = html.escape(text, quote=False)` for MultiChoice labels ONLY (the native `Select` sets `textContent` and keeps raw text; `quote=False` so `"` and `'` read as typed); if the bundle sets `allowHTML:!1`, `_dash_multi_label` is the identity and the test asserts so. The bundle fact is recorded in `_DASH_BOKEH_INTERNALS` as `("Choices.js allowHTML default in MultiChoice", "_dash_multi_label", "test/test_label_sinks.py::TestMultiChoiceLabels::test_multichoice_labels_are_text")` (A109). MultiChoice option values must be strings: the spec row carries `"multi_values": {str(v): v}` so the masks map back to the number (`_dash_groups` already does this for labelled numerics; reuse its map). `w._dash_ftype = "multi"`, `w._dash_initial = []`.
- **TR-49.3 `(missing)` option.** In `_dash_dropdown_options`: `has_missing = bool(series.isna().any() or (not numeric and (series == "").any()))`; when true append `(missing_sentinel, "(missing)")` with `missing_sentinel = "__missing__"` lengthened while in `raw_values`. Set `w._dash_missing = missing_sentinel` (both dropdown and multi) and `w._dash_multi_values = {str(v): v}` (multi), and write them into the filter spec row as `"missing_sentinel"`/`"multi_values"` (`_build_filter_widgets` builds `fc`; the served twin builds `fspec` -- both add the keys from the widget attributes; `_dash_frame_filter_mask` reads the attributes directly, TR-49.6).
- **TR-49.4 Direction.** `_dash_filter_widget(..., direction="ltr")`: the slider and range branches pass `direction=direction` to `Slider/RangeSlider/DateSlider/DateRangeSlider/DatetimeRangeSlider`. `_build_filter_widgets` and the served twin pass `fc.get("direction", "ltr")`. `_dash_filter_effective_type`: `if ftype not in ("dropdown", "multi") or column is None: return ftype` and the numeric fallback returns `"range"` for both.
- **TR-49.5 Mask branches (JS).** In `dash_filter_mask`'s per-spec loop add, before the dropdown branch: `if (spec.type === 'multi') { const vals = Array.isArray(w.value) ? w.value : []; if (vals.length === 0) continue; const want = new Set(vals.map(v => spec.multi_values && (v in spec.multi_values) ? spec.multi_values[v] : v)); const miss = spec.missing_sentinel && vals.includes(spec.missing_sentinel); for (let i = 0; i < n; i++) { if (!keep[i]) continue; const v = col[i]; const ismiss = (v === null || v === undefined || (typeof v === 'number' && Number.isNaN(v)) || v === ''); keep[i] = (miss && ismiss) || (!ismiss && (want.has(v) || want.has(String(v)))); } continue; }` and in the dropdown branch, before the equality test: `if (spec.missing_sentinel && sel === spec.missing_sentinel) { keep[i] = ismiss; continue; }` (with `ismiss` computed as above). Column name: `col = orig[spec.varname]`, the loop's existing variables.
- **TR-49.6 Mask branches (Python).** `_dash_frame_filter_mask(df, widgets)` keeps its signature (REVIEW-4 R4-19): `spec` below is read from the WIDGET's attributes set by `_dash_filter_widget` -- `w._dash_missing` (the missing sentinel), `w._dash_multi_values` (the `{str(v): v}` map), `w._dash_ftype` -- not from a spec parameter (the served template and the copy-list entry at :46952 keep their two-argument calls). `elif ftype == "multi": vals = list(widget.value or []); if not vals: continue; miss = spec.get("missing_sentinel") in vals; want = {spec.get("multi_values", {}).get(v, v) for v in vals if v != spec.get("missing_sentinel")}; m = series.isna() | (series.astype(object) == "") if miss else pd.Series(False, index=series.index); mask &= m | series.isin(want) | series.astype(str).isin({str(w) for w in want})`; and the dropdown branch: `if sel == spec.get("missing_sentinel"): mask &= series.isna() | (series.astype(object) == ""); continue`.
- **TR-49.7 FilterBuilder.build_multi.** A copy of `build_dropdown`'s body calling `_dash_filter_widget("multi", ...)`, same CustomJS args, `widget.js_on_change("value", callback)`. `_build_filter_widgets`: `if ftype in ("dropdown", "multi"): _b = build_dropdown if ftype == "dropdown" else build_multi`.
- **TR-49.8 Reset button.** New shared `_dash_filter_reset_button(widgets)` (after `_dash_filter_widget`): returns `None` when `widgets` is empty, else `Button(label="Reset filters", button_type="default", tags=["dash_filter_reset"])`. Saved: `_build_filter_widgets` appends it to `filter_row_widgets` with `js_on_click(CustomJS(args={"widgets": widgets, "initial_json": json.dumps([_dash_json_value(w._dash_initial) for w in widgets])}, code=_DASH_FILTER_RESET_JS))` where `_DASH_FILTER_RESET_JS = "const init = JSON.parse(initial_json); for (let i = 0; i < widgets.length; i++) { const w = widgets[i]; const v = init[i]; if (JSON.stringify(w.value) !== JSON.stringify(v)) { w.value = v; } }"` (a changed value fires that widget's own filter callback). Served: after the widget loop at :50473, `_reset = _dash_filter_reset_button(_fwidgets)`; `if _reset is not None: _reset.on_click(lambda: _dash_reset_filters(doc, _fwidgets))` where the template-local `_dash_reset_filters` does `doc.hold('combine')` / sets `w.value = w._dash_initial` (and `w.value_throttled` where present) / `doc.unhold()`; the button joins the filter row. The initial values are plain JSON (numbers, strings, lists, 2-tuples) through `_dash_json_value`.
- **TR-49.9 Copy lists (R2).** Constant `_DASH_FILTER_RESET_JS` after `_DASH_STALE_STATUS_HTML`'s entry (after S48's two constants if S48 landed first; append after whichever is last); functions `_dash_dropdown_options`, `_dash_multi_label`, `_dash_filter_reset_button` after `_dash_reference_lines` (after S48's four). function_test_map entries for the four functions and `FilterBuilder.build_multi`.
- **TR-49.10 Help.** dash.sthlp `{title:Filters}` (:1680ff): `type(multi)`, the "(missing)" sentence, `direction(rtl)`, the reset button sentence, the over-limit sentence for `multi` on a string variable (the first `limit` values are listed and a note names the rest, D-49a); the Standalone-vs-server table gains "multi-select, reset: yes / yes".

## Boundaries

- No change to `_FILTER_JS` beyond `dash_filter_mask`'s two branches (S52 owns the error wrapper and throttle in batch 17; S10-S29 own the estimator blocks).
- No change to `_dash_layout_cell` or the table helpers (S48).
- No KPI, link or brush change (S50, S51).
- No slider `value_throttled` on the saved page (S52, H1).
- No new filter position or layout.

## Stata truth

None from twoway. Truth block `* ==== S49 H2f: filter widgets ====` in test/test_wp31_truth.cscript: `U49-1` `filter(rep78, type(multi))` writes `"type":"multi"`; `U49-2` `filter(price, type(slider) direction(rtl))` writes `"direction":"rtl"`; `U49-3` `direction(up)` r(198) with D-49c's first sentence; `U49-4` `direction(rtl)` on `type(dropdown)` r(198) with the second; `U49-5` `type(bogus)` keeps today's refusal text (regression guard, `cert_log_has`).

## TDD test stubs

Regression tests (red at 6370ca4), file `test/test_filter_widgets_ext.py`:
- `TestMulti::test_type_multi_builds_a_multichoice_in_both_modes`, `::test_options_are_labels_and_values_strings`, `::test_over_the_limit_a_numeric_multi_becomes_range`, `::test_over_the_limit_a_string_multi_is_truncated_with_a_note` (the note names the variable and the count dropped).
- `test/test_label_sinks.py::TestMultiChoiceLabels::test_multichoice_labels_are_text` (saved and served: a value label `<b>x</b>` reaches the MultiChoice option as `&lt;b&gt;x&lt;/b&gt;` when the bundle's `allowHTML` default is true, raw when it is false; the `Select` option keeps the raw text), `::test_the_bundle_fact_is_pinned` (reads `allowHTML` from the installed bokeh-widgets bundle and compares with `_DASH_BOKEH_INTERNALS`' entry); release Chrome arm `TestInChrome::test_a_label_with_markup_renders_literally` (`<b>` appears as text in the rendered option).
- `TestTheMissingOption::test_listed_last_only_when_the_column_has_missing` (rep78 yes, foreign no), `::test_the_sentinel_never_collides`, `::test_the_spec_row_carries_the_sentinel`.
- `TestTheMaskScript` (node, through `test/js_runner.py`): `::test_multi_any_of`, `::test_multi_empty_is_all`, `::test_missing_in_dropdown`, `::test_missing_in_multi_with_a_value`.
- `TestTheServedMask::test_python_agrees_with_the_script` (same four cases through `_dash_frame_filter_mask`).
- `TestDirection::test_rtl_reaches_slider_and_range_in_both_modes`, `::test_default_is_ltr`.
- `TestTheResetButton::test_present_when_a_filter_exists_absent_otherwise`, `::test_initial_values_recorded`, `::test_n_runs_are_idempotent` (node: run the reset code then `_FILTER_JS` per widget; the kept rows equal the opening rows), `::test_served_reset_runs_one_move`.
- Release (Chrome): `TestInChrome::test_saved_multi_missing_and_reset` through `_CspProbe`: choose two values, read the kept count; choose `(missing)`; press reset; count equals the opening count (after S52 lands, the reset also recomputes slider filters through `value_throttled`; S52's `TestSlidersFireOnRelease::test_reset_still_recomputes_a_slider` pins that).

cscript cases U49-1..U49-5 (above). Flips: test_filters.py:173 (`Flipped: ... -- the sorted-unique list was wrong because a column with missing values now lists "(missing)" last`), any `len(w.options)` pin on `rep78` in test_filter_widget_data.py.

Parity: `_case("multi filter", [plot_for("scatter")], bo={"filter": "rep78, type(multi)"})`; `_move_case("multi to 3 and 4", ("multi to 3 4", "rep78, type(multi)", ("MultiChoice", ["3", "4"]), "rep78 == 3 | rep78 == 4"), [plot_for("scatter")])` -- add the tuple to `_MOVES` as its fourth entry and teach `_served_after_move` to set a `MultiChoice.value` list; `_move_case("dropdown to (missing)", ("dropdown to missing", "rep78, type(dropdown)", ("Select", "(missing)"), "missing(rep78)"), ...)` with the Select set by LABEL (the oracle `if` is Stata's `missing()`; the saved renderer re-run evaluates it through `_dash_layer_frame`).

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| grammar, refusals, spec keys | cscript U49-1..5 | none | n/a |
| widgets, options, sentinel, direction | pytest | none | yes |
| masks | node + Python | none | yes |
| reset | pytest + node + served doc | none | yes |
| end to end | Chrome (release) | none | saved |
| parity | test_mode_parity entries | none | yes |

**AC-49.1** every stub green; **AC-49.2** U49-1..5 pass; **AC-49.3** test_filters.py, test_filter_widget_data.py, test_csp.py green; **AC-49.4** help lists `multi`, "(missing)", `direction()`, the reset button.

## Tasks

**Commit boundary.** 49-01..49-04 form the one commit `Add multi-select, (missing), slider direction and a reset button to filters (WP-31 H2f)`.

<task type="auto" id="49-01">
  <name>Write the failing filter-widget tests</name>
  <files>test/test_filter_widgets_ext.py, test/test_mode_parity.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_filter_widgets_ext.py with every class under "TDD test stubs" (TestInChrome marked release). Node tests slice dash_filter_mask from dash_render._FILTER_JS the way test/js_runner.py's helpers slice other functions and call it with a fake widget list ({value: [...]} objects). Append the parity entries and the _MOVES tuple; append the S49 block to test/test_wp31_truth.cscript with U49-1..U49-5. Run `python3 -m pytest test/test_filter_widgets_ext.py -q -m "not release"` on the unmodified tree; save the output to <scratch>/49-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The pytest tail prints only failures (no passes except none); test -s <scratch>/49-01-failure.txt]]></verify>
  <done>The regression tests exist and fail at 6370ca4.</done>
</task>

<task type="auto" id="49-02">
  <name>Extend the filter grammar in Stata</name>
  <files>dash.ado, dash_parse.mata, test/test_option_validation.cscript</files>
  <action><![CDATA[Find every type-word list with `grep -n '"dropdown"' dash_parse.mata dash.ado` and add "multi" to each; add direction() to the sub-option reader in _dash_filter_refusal with D-49c's two refusals; write "direction":"rtl" into the filter JSON row where "type" is written. Add U49-3 and U49-4 as area cases to test_option_validation.cscript too (same ids, the truth block holds the spec checks). Run both cscripts through scripts/stata_slot.sh drivers.]]></action>
  <verify><![CDATA[Both logs end in PASS with no FAIL; grep -c '"multi"' dash_parse.mata prints at least 1]]></verify>
  <done>dash accepts type(multi) and direction(ltr|rtl) and refuses the other forms with one sentence each.</done>
</task>

<task type="auto" id="49-03">
  <name>Build the widgets, masks and reset in both modes</name>
  <files>dash_render.py, test/function_test_map.py, test/test_filters.py</files>
  <action><![CDATA[First read the installed bundle: `grep -o 'allowHTML:![01]' $(python3 -c "import bokeh,os;print(os.path.dirname(bokeh.__file__))")/server/static/js/bokeh-widgets.min.js | sort | uniq -c` (TR-49.2; at 3.8.0 it prints `allowHTML:!0`, so labels are escaped). Apply TR-49.1..TR-49.9 in this order: the two constants/grammar tuples; _dash_dropdown_options factored from the dropdown branch of _dash_filter_widget with the (missing) option and _dash_initial; the multi branch with _dash_multi_label and the _DASH_BOKEH_INTERNALS entry; the string-variable over-limit note; direction on the slider branches; _dash_filter_effective_type; the JS branches in dash_filter_mask; the Python branches in _dash_frame_filter_mask; FilterBuilder.build_multi; _build_filter_widgets routing and the reset button; the served twin (template :50001-50015 direction/missing_sentinel/multi_values keys, :50473 reset wiring and _dash_reset_filters); copy-list entries; function_test_map entries. Add TestMultiChoiceLabels to test/test_label_sinks.py (a fourth file, named here). Flip test_filters.py:173 per the TDD stubs with a Flipped line. Run test/test_filter_widgets_ext.py -m "not release", test/test_filters.py, test/test_filter_widget_data.py, test/test_label_sinks.py, test/test_bokeh_internals.py, test/test_statistical_helpers.py -k CarriesEveryName, test/test_csp.py.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_filter_widgets_ext.py test/test_filters.py test/test_filter_widget_data.py test/test_label_sinks.py test/test_bokeh_internals.py test/test_csp.py -q -m "not release" prints all passed]]></verify>
  <done>Both modes draw MultiChoice, the (missing) option, rtl sliders and a working reset button from one widget builder and two mask twins.</done>
</task>

<task type="auto" id="49-04">
  <name>Verify in Chrome, document and commit H2f</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Run DASH_TEST_TIER=release python3 -m pytest test/test_filter_widgets_ext.py -m release -q (skip without Chrome, say so) and DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "multi or missing" -q. Edit the {title:Filters} paragraphs (TR-49.10). Replace the <!-- WP-31 H2f --> marker under "### Fixed in WP-31" with "filter() takes type(multi) and direction(rtl), lists (missing) where a variable has missing values, and every filter row ends in a Reset filters button, in both modes (WP-31, H2f)". Close BUGS.md "Dashboard extensions: filter widgets" and rewrite the GAPS3 H2f Tracked line to the Closed form with `commit pending` (DECISIONS A11). Commit on wp31-s49 with the body forms.]]></action>
  <verify><![CDATA[git log -1 --format=%s prints the subject ending "(WP-31 H2f)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q passes]]></verify>
  <done>H2f is committed with help, CHANGELOG, BUGS.md and GAPS3 updated.</done>
</task>

## Section completion criteria

- `type(multi)` → MultiChoice; `(missing)` listed only where missing values exist and selecting it keeps exactly them (node, Python and Chrome agree); `direction(rtl)` reaches the slider models; the reset button restores the opening rows in both modes.
- U49-1..5 pass; the flips carry reasons; one commit `(WP-31 H2f)`.

## Notes

- **Renderer order.** The spec row the saved page filters by (`filter_specs_json`) is built from the WIDGET attributes (`_dash_missing`, `_dash_ftype`, the `multi_values` map), so build the widget first, then the row; the served twin builds `fspec` the same way.
- **R12.** S49 is batch 16's `_FILTER_JS` editor (the two `dash_filter_mask` branches only) and its `_build_filter_widgets`/`FilterBuilder` editor; S48 touches neither.
- **Security (M11).** `Select` option labels are text nodes (BokehJS `option()` sets `textContent`); `MultiChoice` labels go through Choices.js, whose `allowHTML` default is true in the 3.8.0 bundle, so they are escaped by `_dash_multi_label` (TR-49.2, pinned by test_label_sinks.py and `_DASH_BOKEH_INTERNALS`); values are compared never displayed; `"(missing)"` is a fixed literal; the reset code reads no user text (`initial_json` holds values JSON-encoded through `_dash_json_value`). test_csp.py and test_label_sinks.py stay green.
- **Copy lists (R2):** append after S48's entries if present, else at the R2 anchors.
- **python_exec hazard:** cscript drivers through `scripts/stata_slot.sh` with `global dash_nobrowser 1`.
- **Commit body forms:** `Regression: test/test_filter_widgets_ext.py::TestMulti::test_type_multi_builds_a_multichoice_in_both_modes -- failed at 6370ca4 with UserWarning: dash: filter(rep78) type 'multi' is not one of dropdown, range, slider`; `Flipped: test/test_filters.py::TestBuildDropdown::test_options_match_sorted_unique_values -- ...`; `BUGS.md: "Dashboard extensions: filter widgets" (closed)`; `GAPS3: H2f Tracked`.
- **Decisions for ratification:** the type word `multi` (D-49a); the automatic reset button with no opt-out (D-49d); `(missing)` as fixed English text (D-49b; the interface is English-only, GAPS3 K6 scope). **Decided:** A29 (escape MultiChoice labels after probing `allowHTML`); A28 (S52 adds the `value_throttled` line to the reset code).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 49-01 appends the one H2f block.
