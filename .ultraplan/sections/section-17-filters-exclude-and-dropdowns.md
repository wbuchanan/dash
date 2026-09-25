# Section 17: Filters: exclude() and dropdowns (E2, X1)

> Part of: WP-28 · Gaps: E2, X1 · Risk: red · Batch: 2 · Depends on: 03, 07 · Blocks: 11, 12, 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **03, 07** · Blocks **11, 12, 19** · Risk **red** · Commits: two commits: E2 and X1 → CHANGELOG `Results that change`

- D4: S11 (later) adapts `dash_apply_kpis` to this section's per-group call; S12 (later) owns dropdown LABELS, this section owns VALUES and masks.
- Q26: when S12 groups several values under one display text, the mask matches every value whose display text equals the entry's; `mask_parity` gains a case with two values sharing a label.
- The pins S03 writes in `test_js_runner.py` for today's E2/X1 answers are in this section's flip list. Stub: `dcount` and string marker labels keep string codes as text after a move.
- D7: split 17-01, 17-04, 17-07.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Two silent defects in the one mechanism that decides which rows a dashboard shows after a widget moves.

**E2** (GAPS2): "Each callback masks with all filters but writes only the targets it does not exclude (saved dash_render.py:23723-23771, :14346; served :26763-26772). An excluded item therefore keeps whatever the last non-excluding move wrote. Served probe: price to [4000,5000], then foreign=1, then price back to its full range gives g1=3, g2=5, k1=3, where the current widgets imply 5 under either rule." dash.sthlp:1128-1138 documents that behaviour as a rule ("An exclusion holds while its own filter is the one that moves"), and `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` (415-497) pins it, saying in its own docstring that when exclusion is made to hold against every move "the help and this test change together". After this section each graph, link group, aggregate layer, derived source and KPI card is masked by exactly the filters whose `exclude()` does not name it, recomputed on every move from the widgets as they now stand, in both modes; the state after a sequence of moves depends only on the widgets' current values.

**X1** (GAPS2): "`_dash_option_value` (17413-17438) turns any value that reads as a whole number into integer text, string values included. So '01', '1.0' and ' 2' all become '1' or '2'. `_dash_dropdown_values` (1806-1812) drops the categories 'nan', 'None' and 'NaT'. … Python writes `5e-05` where JavaScript writes `0.00005`. So on the saved page a numeric value in [1e-6, 1e-4), or at 1e21 or above, selects nothing." Research [B §2.1] measured more: the saved snapshot `_dash_json_value` (13828-13862) coerces string codes to numbers for `_orig_data`, every graph snapshot and every derived snapshot, so after a move a marker label "007" reads 7 and a `dcount` card merges '01' and '1'. (GAPS2's "keeps no row for '1'" did not reproduce: both modes select the same, wrong, merged rows.) After this section a numeric column carries numeric option values and both masks compare numbers as numbers (NaN never equal); a string column keeps its exact text, 'nan', 'None' and 'NaT' are ordinary categories, `""` is listed blank, numeric missing is not listed; and every snapshot keeps a string column as text.

The two gaps share this section because they are one code path: the widget's value, the mask built from it, and which targets that mask is written to, in `_DASH_FILTER_MASK_JS`/`_FILTER_JS` on the saved page and `_dash_frame_filter_mask`/`_on_filter_change` in the served app. Section 03's stateful node runner (`test/js_runner.py`: `JsSession(models)` with `.set(widget, value) -> old`, `.run(callback, cb_obj=None, *, commit=True) -> dict`, `.rows(source)`, `.ids(source)`, `.state() -> {"sources": {id: data}, "booleans", "divs": {id: text}, "widths"}`, and `mask_parity(df, filter_specs, widget_values, *, raw=False) -> (js_mask, pandas_mask)`, whose JS side encodes the frame through `_dash_json_value` exactly as the saved snapshot does) is what makes the multi-move and node-vs-pandas assertions possible. S03 also pins today's answers to E2's three-move sequence and X1's small-number case in `test/test_js_runner.py`, naming this section as the one that flips them.

**Test order (CLAUDE.md rule 7): task 17-01 writes every failing test**, runs them on the unmodified tree and records the failures. 17-02 measures the Stata truth. 17-03 to 17-05 close X1 (values, the JS rule, the cscript); 17-06 and 17-07 close E2 (served, then saved); 17-08 closes both BUGS.md entries and the documents.

## Risk: [red] — the saved page's filter script is rewritten around per-target masks, the served callback's three loops change their frame, and every dropdown's value type changes under tests that pin strings

**Why.** `_FILTER_JS` (14177-14915) is one 740-line script with five consumers of the one `active` mask; each has to take its target's own mask or a target silently keeps the wrong rows — the exact shape of E2. The value-type change reaches every place a dropdown value is written or compared: the widget builder shared by both modes, the snapshot, the JS, the pandas mask, the CSV download, and a dozen tests that set `"1"`.

**Risk factors.**
1. A consumer of `active`/`_active_ids` in `_FILTER_JS` missed (the aggregate block at 14725-14915 is the easiest to miss) leaves one layer type on the old rule.
2. `_dash_json_value` is also the CSV download's value writer (13946) and `_dash_option_value`'s date path (17430); keeping strings as text must not change a date's milliseconds.
3. Section 12 edits the same dropdown branch of `_dash_filter_widget` (17570-17622) for LABELS; this section edits it for VALUES. Same function, different lines — merge order matters.
4. `test_linking_filters.py::TestTheShippedJavascriptMasksByIdentity` (331-360) reads `_FILTER_JS`'s text; the identity loop must keep its shape.
5. Bokeh `Select` with numeric values requires unique labels (BokehJS resolves a label back to the first value that carries it); an S12 display format that collapses two values to one label would select the wrong value.

**Mitigation.** One documented rule in one place per mode, pinned by `mask_parity` over hostile columns; a `JsSession` multi-move test per target kind (graph, link group, by() panel, aggregate, derived, KPI); the boundary with S12 written down and a merge order given; a note to S12 on label uniqueness.

## Dependencies

- **Depends on:** 03 — `test/js_runner.py` (`JsSession`, `mask_parity`) with the FIXED names above.
- **Blocks:** 19.
- **Parallel batch:** 2. **Can run with:** 11, 13, 14, 15, 16; **coordinate with 12** (the dropdown branch of `_dash_filter_widget`; see Boundaries).
- Why: S12 changes what a dropdown option *says*; this section changes what it *is* and what selecting it does. S16 edits `_apply_colorvar`'s numeric paths; this section edits one line of its string path.

## Evidence

### X1 — where a dropdown value is made, listed, compared and stored

`_dash_option_value` (`dash_render.py:17413-17441`), the one value a dropdown carries:

```python
17427        if isinstance(v, (pd.Timestamp, np.datetime64)) or (
17428                hasattr(v, "year") and hasattr(v, "month")):
17429            ms = _dash_json_value(v)
17430            if isinstance(ms, float) and math.isfinite(ms):
17431                return str(int(ms))
17432        s = str(v)
17433        try:
17434            f = float(s)
17435            i = int(f)
17436            if f == i:
17437                return str(i)
17438        except (ValueError, TypeError, OverflowError):
17439            pass
17440        return s
```

`_dash_dropdown_values` (1806-1812) — `{_dash_option_value(v) for v in series.tolist() if v is not None and str(v) not in ("nan", "None", "NaT")}` sorted by `_dash_option_sort_key` (17444-17448: `(0, float(rv))` else `(1, rv)`). `_dash_filter_effective_type` (1815-1854) calls it at 1835 and tests numeric-ness at 1838-1839 with `is_numeric_dtype or is_datetime64_any_dtype` — the same test this section makes the rule.

`_dash_filter_widget` (17547-17675), the one builder both modes run (served call at 26703): dropdown branch 17570-17622 — `raw_values = _dash_dropdown_values(series)` (17573), the sentinel loop (17576-17578), `date_text` (17593-17596), the `_label` closure (17598-17608, **S12's**), and

```python
17615        options = [(sentinel, "All")] + [
17616            (rv, str(_label(rv))) for rv in raw_values]
17617        w = Select(title=title, value=sentinel, options=options)
17618        w._dash_sentinel = sentinel
17619        w._dash_ftype = "dropdown"
```

The saved mask, `_DASH_FILTER_MASK_JS` (14110-14164), shared with the CSV button (`_DASH_CSV_SAVED_JS` 14168-14176):

```js
14131            if (ftype === 'dropdown') {
14132                const val = w.value;
14135                const sentinel = spec.sentinel || '__all__';
14136                if (val === sentinel) continue;
14137                for (let i = 0; i < n_rows; i++) {
14138                    if (active[i] && (!present(col[i]) || String(col[i]) !== val))
14139                        active[i] = false;
```

The served mask, `_dash_dropdown_mask` (17669-17675): `want = _dash_option_value(value)`; `pd.Series(column).map(_dash_option_value).to_numpy() == want`, called from `_dash_frame_filter_mask` (13950-14008) at 13988. `filter_specs_json` is built at 23707-23714 with `varname`, `type`, `sentinel` only.

The snapshot: `_dash_json_value` (13828-13862) ends `f = float(v)` → `"01"` becomes 1.0, `"nan"` None; `DashRenderer._to_serialisable` (22983-22993) calls it, and is applied to `_orig_data` (23685-23688), each graph snapshot (23693-23700), each derived snapshot (23811-23816) and the CSV-only snapshot (23835). `_dash_csv_payload` (13946) also calls `_dash_json_value` per cell. The served app snapshots raw (`_orig_src_data`, 26728-26731) and does not coerce. The JS `dcount` is `new Set(vals.map(String)).size` (14525), so a coerced snapshot merges '01' and '1'; a marker label column `__mlabel__*` is coerced the same way.

The colorvar string path (6527): `strs = ["" if v is None or str(v) == "nan" else str(v) for v in raw_col]` — the text 'nan' is read as missing.

Bokeh: `Select.options` is `List(Either(String, Tuple(AnyRef, String)))` and `Select.value` is `AnyRef` since 3.4 ([W §1f], verified on 3.9.0: `Select(options=[('__all__','All'), (1.0,'one')])` builds); the declared floor is 3.8 (S09). Research [B §2.1]'s "Bokeh `Select` values must be strings" is superseded by [W §1f]. ECMAScript writes `5e-05` as `0.00005` and `1e21` as `1e+21`; Python writes `5e-05` and `1e+21` ([W §2]) — no string comparison can be made to agree across both; numbers must be compared as numbers.

### E2 — where the mask is written, and to what

`_dash_excluded(key, excluded, owner_of)` (17975-17985): `return key in excluded or owner_of.get(key) in excluded`; the saved `_owner_of` is built at 23719-23721 from `self._facet_map`, the served `_facet_to_orig` at 26656-26659.

Saved wiring, `_build_filter_widgets` (23535-23842). One `CustomJS` per widget (`FilterBuilder.build_dropdown` 14993, placeholder args 15048-15065; `build_slider`/`build_range` 15130/15189). Per callback (23723-23826): KPIs in that filter's `exclude()` are left out of `kpi_config` (23727-23735); `all_graph_sources` holds the sources that filter does not exclude (23745-23751), `excluded_sources` the rest (23763-23771), `view_filters` indexed against the first list (23776, `_view_filter_args` 21534-21555), `all_graph_sources_orig` (23785-23787), `agg_sources`/`agg_configs_json` skipped when excluded (23789-23798), `derived_sources` likewise (23802-23826). The script masks with **all** widgets and writes only what it was handed:

```js
14186    const active = dash_filter_mask(orig, filter_specs, all_widgets);
...
14227    const _active_ids = new Set();
...
14235    for (let _si = 0; _si < _srcs.length; _si++) {
...
14347    if (!_srcs.includes(source) && !(excluded_sources || []).includes(source)) {
14348        source.data = new_data;
...
14702    dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);
14725    // agg_configs is parsed from the JSON string arg.
14726    const agg_configs = JSON.parse(agg_configs_json);
```

The consumers of the one mask: `new_data` (14191-14200) for the fallback `source` and the KPIs; the graph-source loop (14235-14263, by row identity through `_active_ids`); `view_filters` rebuilt from `_kept_ids_by_src` (14270-14277); the derived-source loop (14310-14340, `_active_ids` at 14318); the fallback write (14347-14351); `dash_apply_kpis` (14493-14700, call at 14702); the aggregate recount (14725-14915).

Served, `_make_filter_cb` / `_on_filter_change` (26758-26964):

```python
26765            mask = _dash_frame_filter_mask(_df_ref, _all_widgets)
26766            fdf = _df_ref[mask]
26768            excl = getattr(_trig_widget, '_dash_exclude', [])
26770            for gname, srcs in _all_sources.items():
26773                if _dash_excluded(gname, excl, _gfac_to_orig):
26774                    continue
...
26879            for key, agg in _agg_srcs.items():
26881                if _dash_excluded(gname, excl, _gfac_to_orig):
...
26948                if kname in excl:
26949                    continue
```

The link group's one source is written once through `_dash_refresh_linked` (26870-26877, helper at 18058) whenever a member the filter does not exclude draws from it; `widget._dash_exclude = fexcl` is set at 26719; the callbacks are wired per widget at 26966-26988 with `_make_filter_cb(w, filter_widgets, graph_sources, agg_sources, kpi_divs, kpi_defs, df, _facet_map, _facet_group_vals, _orig_src_data, _graph_qualifiers, _facet_to_orig, _redrawn_ids, _shared=shared_source, ...)`.

The rule for a link group (dash.sthlp:1130-1137, pinned by `test_help_claims_3.py::TestAnExcludedMemberOfALinkGroupIsFilteredWithIt` 397-412 and `test_filter_exclude.py`): one shared source, excluded only when every member is.

### Stata's rule

There is no twoway rule for a dashboard filter; the truth is Stata's own `count` and `summarize` over the rows the widgets describe: `count if foreign==1`, `count if foreign==1 & inrange(price,4000,5000)`, `summarize mpg if ...` on auto (GAPS2 E2 plan step 5), and `count if fips == "<text>"` on a constructed string variable (X1 plan step 4). A Stata string variable compares by exact text: `"01" != "1"`; a double compares by value: `count if tiny == 5e-05`.

### Fixtures on disk

None for filters. `test/fixtures/data/auto.csv` holds only `mpg` and `weight`, so the E2 fixture carries the `mpg`, `price` and `foreign` columns it was measured on. `test/fixtures/stat_truth.json` is `scripts/extract_stat_truth.do`'s, which S05 extends in batch 1 — this section does not touch that script.

### Existing tests that pin today's behaviour (flip in the fix commit; never delete)

- `test/test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` (415-497): expects `{g1:3, g2:3, k1:"3"}` after price then foreign. **Rewritten** as the multi-move class of TR-17.12 (its docstring asked for exactly this).
- `test/test_help_claims_3.py` 452 (`w_for.value = "1"`), 494 (`tp._fire(w_for, "1")`), and `TestAnExcludedMemberOfALinkGroupIsFilteredWithIt` (`tfe._saved(..., "1")`, `tfe._served(..., "1")`): the value a foreign dropdown carries becomes `1.0`. They keep passing meanwhile (the mask coerces a string on a numeric column), and are flipped to the real value type in 17-07.
- `test/test_filter_exclude.py` `_MOVES["dropdown"]` (62-66) `"1"` → `1.0`; `_script_args` (434-455) `Select(value="1", options=["__all__","0","1"])` → `Select(value=1.0, options=[("__all__","All"),(0.0,"0"),(1.0,"1")])` and the spec gains `"numeric": True`; `TestThePrimarySourceFallback` (469-496) keeps its three cases (the fallback guard stays); `TestTheCallbackKnowsWhatItProtects::test_every_graph_source_is_filtered_or_protected_not_both` (407-431) holds under TR-17.9's split; `test_an_unwired_callback_declares_the_argument` (433-441) holds and the new placeholder args join it.
- `test/test_saved_filter_layers.py::TestTheOptionValueOfADate` (1219-1245): `"1009756800000"` → `1009756800000.0` (1225, 1229, 1234: a float), `_dash_option_value(1.0) == "1"` → `== 1.0` (1244); the string case (1245) holds. **The date-label pin at 1213** (`labels[0] == "2001-12-31 00:00:00"`) is a LABEL and belongs to S12; this section does not touch it.
- `test/test_export.py::TestTheHelpers::test_json_value` (584-594) holds (`_to_serialisable("007") == _dash_json_value("007")` is true both before and after); `test_frame_filter_mask` (596-614) holds through the coercing mask, and gains a `0.0` case; the comment at 199-201 ("The saved snapshot holds "007" as 7") becomes stale and is corrected.
- `test/test_resource_limits.py::TestTheHelpersOneByOne::test_dropdown_values_are_the_listed_options_sorted` (1380-1384) holds (floats sort by value).
- `test/test_label_sinks.py` (`("Select","options.value"): DATA` at 531; Sink 600) holds; run it.
- `test/test_help_claims_4.py` `_saved_filter_move` (220): if it sets a dropdown to a string on a numeric column, flip to the float.
- `test/test_linking_filters.py::TestTheShippedJavascriptMasksByIdentity` (331-360): pins the identity loop's text; keep the loop's shape (see Notes).
- `test/test_keyword_names.py::TestExcludeAByGraph::test_one_rule_matches_it` pins `_dash_excluded`, which stays.
- **S03's measurement pins (flip here, S03 says so):** `test/test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` (the two twins disagree on 5e-05 today → they agree, 17-04) and `test/test_js_runner.py::TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` (`{g1:3, g2:5, k1:"3"}` today → `{g1:5, g2:5, k1:"5"}`, 17-07); `test/test_js_runner.py::TestASessionCarriesState::test_two_moves_chain_on_one_session` sets the foreign dropdown to `"1"` — still selects through coercion; flip to `1.0` in 17-07 for honesty.
- S03 also turns `test_filter_exclude.py`'s `_run_callback` and `test_help_claims_3.py`'s `_run_saved` into shims over `JsSession` and deletes `_RUNNER_DIVS` (321-327), so the line numbers quoted for `test_help_claims_3.py` below are "about" once S03 has landed; the class and helper names are authoritative.
- `test/test_function_test_map.py` fails until every new helper is mapped.

## User stories

- **US-17.1** As the dashboard viewer, I want every card and graph to reflect the widgets as they now stand after any sequence of moves, so that an excluded graph never shows a filter state that no longer exists.
- **US-17.2** As the Stata user, I want `exclude()` to mean "this filter never touches these targets" and nothing else, in both modes.
- **US-17.3** As the Stata user, I want a dropdown on a string variable to list every distinct text — '01' and '1' apart, 'nan' and 'None' as the categories they are, `""` as a blank row — and to keep exactly the rows equal to the chosen text, as `count if var == "<text>"` counts them.
- **US-17.4** As the dashboard viewer, I want a dropdown on a numeric variable to select 5e-05 or 1e21 on the saved page as it does when served.
- **US-17.5** As the dashboard viewer, I want a marker label "007" and a `dcount` of codes to read the same after a move as before it.
- **US-17.6** As the maintainer, I want one written matching rule shared by the saved page's script and the served app, pinned by a test that runs both on the same columns.

## Business requirements

- **BR-17.1** A target (a graph, a link group, a `by()` graph with its panels, an aggregate or derived layer of a graph, a KPI card) is masked by the AND of the filters whose `exclude()` does not name it. A link group is one target, excluded only when every member is. A `by()` panel follows its owner.
- **BR-17.2** Every move rewrites every target from the current values of every widget; the resulting state is a function of the widget values alone (order of moves irrelevant; moving a widget back restores the earlier state).
- **BR-17.3** A KPI in a filter's `exclude()` is recomputed on that filter's moves too, from the filters that do apply to it.
- **BR-17.4** A numeric or date column's dropdown carries numeric values; selection compares numbers as numbers; a missing number is never listed and never selected.
- **BR-17.5** A string column's dropdown carries each distinct text exactly; 'nan', 'None', 'NaT', ' 2', '01' are ordinary values; `""` is listed as a blank row and selects the rows equal to `""`.
- **BR-17.6** The saved page and the served app keep the same rows for the same widget values, on every column type, including values below 1e-4 and at or above 1e16.
- **BR-17.7** A string column is text in every snapshot the saved page carries and in the CSV download; `dcount` counts distinct texts; a marker label reads the same text after a move.
- **BR-17.8** `colorvar()` on a string column treats the text 'nan' as a category; only `None` and `""` are missing.
- **BR-17.9** The CSV download still holds exactly the rows every filter keeps.
- **BR-17.10** Security (rule 1): a dropdown value is data — it travels in `Select.options`/`value` and `filter_specs_json`, never in script text; a string option value containing `__proto__`, quotes or angle brackets is listed, selectable and never interpreted.

## Technical requirements

- **TR-17.1** New module-level `_dash_filter_numeric(column) -> bool` (`is_numeric_dtype or is_datetime64_any_dtype` of `pd.Series(column)`), the one test of "numeric column"; `_dash_filter_effective_type` (1838-1839) calls it.
- **TR-17.2** `_dash_option_value(v)` returns the VALUE a dropdown carries: a date → its epoch milliseconds as a `float`; an `int`/`float`/numpy number → `float(v)`; anything else → its exact `str(v)`. No integer rewriting of strings. Docstring rewritten (it still describes `String(v)`).
- **TR-17.3** `_dash_dropdown_values(series)`: numeric (per TR-17.1) → sorted `{float(v)}` over finite values (NaN/NaT dropped); otherwise → sorted `{"" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)}` — `""` kept, 'nan'/'None'/'NaT' kept. `_dash_option_sort_key` unchanged.
- **TR-17.4** `_dash_filter_widget` dropdown branch: `raw_values` per TR-17.3; `options = [(sentinel, "All")] + [(rv, str(_label(rv))) for rv in raw_values]` with `rv` now a float or exact text; the sentinel loop unchanged (a float column never holds `"__all__"`); `w._dash_numeric = _dash_filter_numeric(series)`. The `_label` closure is S12's: this section changes only its fallback line so an unlabelled float reads as today (`str(int(rv))` when `rv.is_integer()` else `str(rv)`), which S12 then replaces with the display-format writer.
- **TR-17.5** `filter_specs_json` (23707-23714) gains `"numeric": bool(getattr(_w, "_dash_numeric", False))`; `_dash_dropdown_mask(column, value)` decides from `_dash_filter_numeric(column)`: numeric → `want = float(value)` (a `ValueError` → all False), `col = _dash_float_values(column, coerce=True)`, `col == want` (NaN never equal); text → `want = str(value)`, each cell mapped as TR-17.3 maps it, `== want`. `_dash_frame_filter_mask` unchanged apart from the docstring.
- **TR-17.6** `_DASH_FILTER_MASK_JS` dropdown branch becomes the twin of TR-17.5: `if (spec.numeric) { const want = Number(val); ... (!present(col[i]) || Number(col[i]) !== want) } else { const want = String(val); const cell = (col[i] === null || col[i] === undefined) ? "" : String(col[i]); ... cell !== want }`. The rule is written once as a comment block above `dash_filter_mask` and once above `_dash_dropdown_mask`, each naming the other and `test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree`. `dash_filter_mask` gains an optional fourth parameter `use` (an array of widget indices; `undefined` → every widget) for TR-17.9; the CSV button keeps calling it with three.
- **TR-17.7** `_dash_json_value`: `if isinstance(v, str): return v` before the date and float branches. Consequences, named in the docstring: string codes stay text in `_orig_data`, every graph and derived snapshot, and the CSV (`_dash_csv_payload`); `dcount` counts distinct texts; `__mlabel__*` columns keep their text after a move. A date's milliseconds and a number's float are unchanged.
- **TR-17.8** `_apply_colorvar` string path (6527): `strs = ["" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v) for v in raw_col]`. That is this section's only edit inside `_apply_colorvar` (S16 owns the rest).
- **TR-17.9** Saved wiring (`_build_filter_widgets`): compute, for every target, `use` = the indices into `built_filter_specs` of the filters that apply, through a module-level `_dash_filter_applies(target, exclude, owner_of, members=None)` (True unless `_dash_excluded(target, exclude, owner_of)`; with `members`, True unless every member is excluded). Sources: `all_graph_sources` = every graph source (deduplicated by id) with a non-empty `use`, `graph_use_json` parallel to it; sources with an empty `use` (no filter applies) go in `excluded_sources` and are never written — so `test_every_graph_source_is_filtered_or_protected_not_both` keeps its invariant. A source's `use` is the AND over the graphs that draw from it (`members` = the graph names mapped to that source id, panels resolved through `_owner_of`); a link group's shared source therefore applies a filter unless every member is excluded. `agg_sources`/`agg_use_json` and `derived_sources`/`derived_use_json` likewise (empty `use` → left out). `kpi_config` holds every filter-mode KPI with a `"use"` list (empty → the card is never rewritten). Every callback receives the same args; `FilterBuilder.build_*` placeholders gain `graph_use_json`, `agg_use_json`, `derived_use_json` as `"[]"`. `view_filters` stays indexed against `all_graph_sources`.
- **TR-17.10** `_FILTER_JS`: a memoised `dash_mask_for(use)` (keyed by `JSON.stringify(use)`) over `dash_filter_mask(orig, filter_specs, all_widgets, use)` and a memoised `dash_ids_for(use)` (the `Set` of row ids the mask keeps); `active`/`_active_ids`/`new_data` stay as the all-widgets mask for the fallback `source`; the graph-source loop reads `dash_ids_for(_graph_use[_si])` (positional fallback `dash_mask_for(...)[i]`); the derived loop reads `dash_ids_for(_derived_use[_di])`; the aggregate block reads its config's `use`; KPIs are grouped by `JSON.stringify(k.use)`, one `new_data_<g>` built per group from `dash_mask_for(use)`, and `dash_apply_kpis(new_data_g, group, divs_g, ROW_ID)` runs per group. The identity loop at 14235-14263 keeps its shape (`_kept_ids_by_src`, `vf.filter.booleans = kept.map(...)`).
- **TR-17.11** Served: module-level `_dash_widgets_for(target, widgets, owner_of, members=None)` → `[w for w in widgets if _dash_filter_applies(target, getattr(w, '_dash_exclude', []), owner_of, members)]`. In `_on_filter_change`: drop `excl` and the three `continue`s (26773, 26881, 26948); a per-call cache `_masks: dict[tuple, Series]` keyed by `tuple(id(w) for w in ws)`; `_mask_for(target, members=None)` → `_dash_frame_filter_mask(_df_ref, ws)` cached; the graph loop uses `_mask_for(gname)` (facet branch ANDs onto it), the shared source uses `_mask_for(None, _shared_members)` with `_shared_members` computed once outside the callback as the graph names whose sources include `_shared`; aggregates use `_mask_for(gname)`; KPIs use `_mask_for(kname)`; `_brush_rows` bookkeeping follows each target's frame.
- **TR-17.12** Tests: `test/test_dropdown_values.py` (X1), `test/test_filter_exclusion_sets.py` (E2), `test/test_dropdown_values.cscript` (X1 end to end), the `TestExcludeHoldsWhileItsOwnFilterMoves` rewrite, `scripts/extract_filter_truth.do` → `test/fixtures/filter_truth.json`.
- **TR-17.13** Copy lists: `_dash_filter_numeric`, `_dash_filter_applies`, `_dash_widgets_for` join the served function list (24466-24687; `_dash_option_value` 24606, `_dash_dropdown_mask` 24611, `_dash_dropdown_values` 24627, `_dash_excluded` 24638, `_dash_json_value` 24551 and `_dash_frame_filter_mask` 24553 are already there); `test/function_test_map.py` names a test for each new function.
- **TR-17.14** Security: `Select.options` values and `filter_specs_json` are data; nothing from a column value is concatenated into `CustomJS.code`; a text option `__proto__` is listed and selects its rows (the snapshot column loop already uses `dash_own_col`).

## Boundaries

- **S12 owns dropdown LABELS**: the `_label` closure (17598-17608), `date_text`'s label side (17593-17596), the date-label pin `test_saved_filter_layers.py:1213`, and the Stata display format of a listed value. **S17 owns VALUES and masks**: `raw_values`, `_dash_option_value`, `_dash_dropdown_values`, the value side of `Select.options`, `_dash_numeric`, `_dash_dropdown_mask`, `_DASH_FILTER_MASK_JS`, `filter_specs_json`, and `_dash_json_value`. Both edit `_dash_filter_widget`'s dropdown branch: merge S17's diff first, then S12 rebases its label change onto the float-valued `rv`. S12 must keep labels unique per widget (append the value when a format collapses two values), or BokehJS selects the first value with that label.
- **S16 owns `_apply_colorvar`** except line 6527.
- **S03 owns `test/js_runner.py`**; this section uses it and does not change it. If a needed accessor is missing, wrap it in a test-local helper.
- **S05 owns `scripts/extract_stat_truth.do`**; this section writes its own `scripts/extract_filter_truth.do`.
- **C4/E4 stay out**: nothing is ported into `_FILTER_JS` to re-estimate fitted or smoothed layers (PRD §7); the aggregate recount block only takes its target's mask.
- **The served download** (`_dash_csv_payload`) and the saved CSV button keep "every filter applies" (BR-17.9).
- **`_dash_excluded` stays** as the per-graph predicate; `_dash_filter_applies` is layered on it.
- **No change to what a range or slider compares** (numbers already) beyond docstrings.

## Stata truth

**Script:** `scripts/extract_filter_truth.do` → `test/fixtures/filter_truth.json`. Small, on the `extract_axis_truth.do` shape (record file, one trailing `python:` block that never calls Stata, backtick as `\x60`). On `sysuse auto`:

```
count
count if foreign==1
count if inrange(price,4000,5000)
count if foreign==1 & inrange(price,4000,5000)
summarize mpg
summarize mpg if foreign==1
summarize mpg if inrange(price,4000,5000)
summarize mpg if foreign==1 & inrange(price,4000,5000)
```

Each `r(N)` and `r(mean)` written with `%21.17g`. Keys: `all`, `foreign_1`, `price_4000_5000`, `foreign_1_price_4000_5000`, each `{command, count, mean_mpg}`; `data: {mpg: [...], price: [...], foreign: [...]}` (74 entries each, dataset order); `_meta` with the Stata version and date. Invocation (header comment):

```
mkdir -p /tmp/dash-s17 && cd /tmp/dash-s17 && STATATMP=/tmp/dash-s17/tmp/ \
  arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_filter_truth.do
```

`git add -f test/fixtures/filter_truth.json`; `test/test_filter_exclusion_sets.py` names it. The X1 cscript measures its own `count if fips == "..."` live and needs no fixture.

## TDD test stubs

New files `test/test_dropdown_values.py` and `test/test_filter_exclusion_sets.py` (17-01). `_DF` (ten rows; `foreign==1` keeps 5, `price` in [4000, 5000] keeps 5, both keep 3), `_graph`, `_spec`, `_write_inputs`, `_load_app`, `_served_rows`, `_renderer_source`, `_rows` come from `test_filter_exclude.py`; `_kpi_card`, `_card_value` from `test_help_claims_3.py`; `_fire` from `test_mode_parity`.

Regression tests that fail at `91d97be`:

- Test: `test_a_string_code_keeps_its_exact_text` — `test/test_dropdown_values.py::TestOptionValues::...`: `_dash_option_value("01") == "01"`, `" 2" == " 2"`, `"1.0" == "1.0"`. Pre-fix: `"1"`, `"2"`, `"1"`.
- Test: `test_a_number_is_a_float_and_a_date_its_milliseconds` — `_dash_option_value(1.0) == 1.0`, `_dash_option_value(np.float32(0.1)) == float(np.float32(0.1))`, `_dash_option_value(pd.Timestamp("2001-12-31")) == 1009756800000.0`. Pre-fix: strings.
- Test: `test_nan_none_nat_and_blank_are_listed_on_a_string_column` — `_dash_dropdown_values(pd.Series(["01","1","1.0"," 2","None","nan","NaT","",None]))` lists exactly `["", " 2", "01", "1", "1.0", "NaT", "None", "nan"]` (sorted as `_dash_option_sort_key` sorts). Pre-fix: five entries.
- Test: `test_numeric_missing_is_not_listed` — `pd.Series([3.0, np.nan, 1.0])` → `[1.0, 3.0]`.
- Test: `test_the_numeric_test_is_the_dtype` — `_dash_filter_numeric` on float, datetime, object-of-str and object-of-None columns. Pre-fix: `AttributeError`.
- Test: `test_the_widget_carries_numbers_for_a_numeric_column_and_text_for_a_string_one` — `::TestTheWidget::...` through `_dash_filter_widget("dropdown", ...)`: `[v for v, _ in w.options][1:]` are floats for `foreign`, strings for the codes column; `w._dash_numeric`; the `filter_specs_json` of a rendered page carries `"numeric"`. Pre-fix: strings, no attribute.
- Test: `test_the_snapshot_keeps_a_string_column_as_text` — `::TestTheSnapshot::...`: `_dash_json_value("01") == "01"`, `"nan" == "nan"`, `"" == ""`; a rendered page with a string column `s = ["01","1","1.0"]` has `orig_source.data["s"] == ["01","1","1.0"]`. Pre-fix: `1.0, 1.0, 1.0`.
- Test: `test_dcount_and_a_marker_label_survive_a_move` — a `dcount` card on `s` reads "3" after a `JsSession` move of an unrelated range widget (pre-fix "1"), and a `mlabel(s)` layer's label column still holds "007" (pre-fix 7).
- Test: `test_node_and_pandas_agree` — `::TestOneRule::...` via S03's `mask_parity(df, filter_specs, widget_values)`: `df` with `s = ['01','1','1.0',' 2','None','nan','NaT','']` and `x = [5e-05, 1e21, float(np.float32(0.1)), np.nan, 1.0, 2.0, 3.0, 4.0]`; for every option value of each column the node mask equals the pandas mask and equals the expected rows (exactly one row per text; for `x`, exactly the rows whose float equals; NaN never). Pre-fix: `s` options merge three rows and `5e-05`/`1e21` keep none under node.
- Test: `test_both_modes_select_the_same_rows` — `::TestBothModes::...` saved via `JsSession`, served via `_fire`, on `s` = "01" (1 row), "nan" (1 row), "" (1 row) and `x` = 5e-05, 1e21. Pre-fix: saved keeps 0 for 5e-05.
- Test: `test_colorvar_reads_the_text_nan_as_a_category` — `_apply_colorvar` on `["nan", "a", None, ""]` gives factors `["a", "nan", "__missing__"]`. Pre-fix: `["a", "__missing__"]`.
- Test: `test_a_hostile_text_value_is_data` — `s = ["__proto__", "<script>", "a\"b"]`: all three listed, each selects its row under node and pandas, none appears inside any `CustomJS.code`.
- Test: `test_saved_state_depends_only_on_the_widgets` — `test/test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved`, the `TestExcludeHoldsWhileItsOwnFilterMoves` SPEC (foreign dropdown; price range with `exclude(g1 k1)`; k1 counts mpg) through `JsSession`: price → (4000, 5000) gives `{g1:10, g2:5, k1:"10"}`; foreign → 1.0 gives `{g1:5, g2:3, k1:"5"}`; price → (start, end) gives `{g1:5, g2:5, k1:"5"}`; foreign → sentinel gives `{g1:10, g2:10, k1:"10"}`. Pre-fix: the second state is `{3,3,"3"}` and the third `{3,5,"3"}`.
- Test: `test_served_state_depends_only_on_the_widgets` — the same four states through chained `tp._fire`.
- Test: `test_the_order_of_moves_does_not_matter` — foreign first then price reaches the same second state, both modes.
- Test: `test_an_excluded_kpi_is_recomputed_by_the_filters_that_apply_to_it` — `TestAKpiCardCanBeExcluded`'s SPEC plus a foreign dropdown: moving foreign after price gives k1 "5" (foreign applies), k2 "3". Pre-fix: k1 "10".
- Test: `test_a_link_group_is_one_target` — `link(g1 g2)`, `exclude(g1)`, a second filter: after both move, g1 == g2 == the rows the non-excluding filter set keeps for the GROUP (both filters, since g2 is not excluded); with `exclude(g1 g2)`, neither filter touches the group. Both modes.
- Test: `test_a_by_panel_follows_its_owner_across_moves` — `by(foreign)` graph excluded from one filter, two moves, both modes.
- Test: `test_an_aggregate_and_a_derived_layer_take_their_targets_mask` — a `histogram` layer and a `line` (derived, sorted copy) on g1 excluded from price, two moves: their sources hold the foreign-only rows, not the intersection. Both modes. Pre-fix: the intersection.
- Test: `test_auto_matches_stata` — `::TestAutoAgainstStata::...` from `filter_truth.json`'s `data`: g1 (`exclude(price)`), g2, k1 `count mpg` (`exclude(price)`), k2 `count mpg`; foreign → 1.0 then price → (4000, 5000): k1 == `foreign_1.count`, k2 == `foreign_1_price_4000_5000.count`, `mean(g1 source mpg)` == `foreign_1.mean_mpg` and `mean(g2 source mpg)` == `foreign_1_price_4000_5000.mean_mpg` at rtol 1e-9, both modes. Missing fixture → `pytest.fail("section 17 task 17-02 must land first: ...")`.
- Test: `test_every_source_is_filtered_or_protected_and_use_is_recorded` — `::TestTheCallbackArgs::...`: for the specs of `test_filter_exclude.py::TestTheCallbackKnowsWhatItProtects`, `graph_use_json` is parallel to `all_graph_sources`, every listed source has a non-empty `use`, every `excluded_sources` entry has none, and the `use` lists are the same in every callback. Pre-fix: `KeyError: 'graph_use_json'`.
- Test: `test_filter_applies_and_widgets_for` — unit tests of `_dash_filter_applies` (graph, panel through owner, group with one/all members excluded) and `_dash_widgets_for`. Pre-fix: `AttributeError`.

Pinned tests to flip (in the fix commits): `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` → rewritten as `TestAnExclusionHoldsAgainstEveryMove` delegating to the sequences above (17-07); the `"1"` → `1.0` values in `test_help_claims_3.py` and `test_filter_exclude.py` (17-07 and 17-04); `_script_args` and `TestThePrimarySourceFallback` shapes (17-04, 17-07); `test_saved_filter_layers.py::TestTheOptionValueOfADate` (17-03); `test_export.py` comment 199-201 and a `0.0` case (17-04); `test/function_test_map.py` entries (17-03, 17-06).

**Mutation table:**

| break this | test that must die |
|---|---|
| `_dash_option_value`: restore `str(int(f))` | `test_a_string_code_keeps_its_exact_text` |
| `_dash_dropdown_values`: restore the `("nan","None","NaT")` filter | `test_nan_none_nat_and_blank_are_listed_on_a_string_column` |
| `_dash_json_value`: drop the `isinstance(v, str)` branch | `test_the_snapshot_keeps_a_string_column_as_text` |
| JS: compare `String(col[i]) !== String(val)` on a numeric spec | `test_node_and_pandas_agree[x=5e-05]` |
| pandas: compare `str` on a numeric column | `test_node_and_pandas_agree[x=5e-05]` |
| `_FILTER_JS`: KPI groups all use `active` | `test_an_excluded_kpi_is_recomputed_by_the_filters_that_apply_to_it[saved]` |
| `_FILTER_JS`: derived loop keeps `_active_ids` | `test_an_aggregate_and_a_derived_layer_take_their_targets_mask[saved]` |
| served: keep `excl` and `continue` in the KPI loop | `test_served_state_depends_only_on_the_widgets` |
| `_dash_filter_applies`: `any(...)` instead of `all(...)` for members | `test_a_link_group_is_one_target` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| option values, listing, numeric test, snapshot text | pytest unit | none | n/a (shared functions) |
| one matching rule, node vs pandas | pytest via `mask_parity` (node) | none | yes (the two masks) |
| rows selected for '01', 'nan', '', 5e-05, 1e21 | pytest `JsSession` + `_fire` | none | yes |
| dcount / marker label after a move | pytest `JsSession` | none | saved (the served app never coerced) |
| string codes from a real Stata dataset | cscript `test_dropdown_values.cscript` (python: block renders both, node via `JsSession`) | live `count if` | yes |
| multi-move sequences per target kind | pytest `JsSession` + chained `_fire` | none | yes |
| counts and means on auto | pytest | `filter_truth.json` | yes |
| callback args shape | pytest | none | saved |
| parity corpus | `test_mode_parity` (existing dropdown/exclude cases) | its own | yes |
| security: hostile text values | pytest + cscript | none | yes |

Acceptance criteria:
- **AC-17.1** The four-state sequence of `test_saved_state_depends_only_on_the_widgets` holds in both modes, and reversing the order of moves reaches the same states.
- **AC-17.2** An excluded KPI, an excluded link-group member, a `by()` panel, an aggregate layer and a derived layer each show the rows their own filter set keeps after two moves, in both modes.
- **AC-17.3** On auto, after foreign → 1 and price → [4000, 5000], the excluded graph and card equal Stata's `foreign==1` count and mean of mpg, the others Stata's intersection.
- **AC-17.4** `mask_parity` over the hostile columns gives equal node and pandas masks and the expected rows for every option.
- **AC-17.5** From Stata, `fips == "01"`, `"1"`, `"1.0"`, `"None"`, `"nan"` and `""` each keep exactly `count if fips == "<text>"` rows in both modes; a double 5e-05 keeps `count if tiny == 5e-05` rows.
- **AC-17.6** A `dcount` card and a marker label read the same before and after a move on the saved page.
- **AC-17.7** The full pytest suite is green with no skips; `test_function_test_map.py`, the two served-name guards and `test_cscript_hygiene.py` pass; the new cscript passes.

## Tasks

<task type="auto" id="17-01">
  <name>Write the failing tests for both gaps</name>
  <files>test/test_dropdown_values.py (new), test/test_filter_exclusion_sets.py (new)</files>
  <action>
    Create both files. Write only tests; no production change.
    1. `test_dropdown_values.py`: module docstring with X1's measured symptoms (the '01'/'1'/'1.0' merge, 'nan'/'None'/'NaT' unlisted, 5e-05 and 1e21 unselectable on the saved page, the "007" → 7 snapshot); header as `test_filter_exclude.py:31-52` plus `from js_runner import JsSession, mask_parity` (S03) and `import test_filter_exclude as tfe`, `import test_mode_parity as tp`. Classes `TestOptionValues`, `TestTheWidget`, `TestTheSnapshot`, `TestOneRule`, `TestBothModes`, `TestColorvarStrings` (the `_apply_colorvar` string test through `test_function_audit.py`'s `_bins` pattern with a string column), `TestHostileValues`, with exactly the test names of the stubs. Build frames with a string column `s` and a float column `x` as the stubs list them; write the spec through `tfe._spec`/`tfe._graph` with `filters` on `s` and on `x`; for the dcount/mlabel test add a `kpis` entry `{"stat": "dcount", "var": "s", ...}` (`_kpi_card` shape) and a `mlabel(s)` scatter, move a `range` on `x` through `JsSession`, read the card through `_card_value` and the label column from the session state.
    2. `test_filter_exclusion_sets.py`: docstring with E2's measured sequence (g1=3, g2=5, k1=3 where 5 is implied); classes `TestAnExclusionHoldsAgainstEveryMove`, `TestTheOrderOfMoves`, `TestAnExcludedKpi`, `TestALinkGroupIsOneTarget`, `TestAByPanelFollowsItsOwner`, `TestAggregateAndDerivedLayers`, `TestAutoAgainstStata`, `TestTheCallbackArgs`, `TestTheHelpers`. Saved sequences: render, build `JsSession` from every callback's args (all callbacks share the same models), then alternate `.set(widget, value)` / `.run(callback_of_that_widget)` / read the state through one local `_rows_and_cards(session, r)` that maps `session.rows(tfe._renderer_source(fig))` to figure titles and `session.state()["divs"][div.id]` through `_card_value` to card names. Served sequences: chained `tp._fire`. Widget values are the real ones: `1.0` for foreign, the sentinel (`w._dash_sentinel`) for "All", `(w.start, w.end)` for a range at rest. `TestAutoAgainstStata` reads `test/fixtures/filter_truth.json` through a `_truth()` that `pytest.fail`s when the file is missing.
    3. Run both files on the unmodified tree; paste the summary into the commit message (wrong numbers for the value and sequence tests; `AttributeError`/`KeyError` for the helper and args tests; the "must land first" failure for the fixture tests).
    Commit on `s3-bugs`; no AI references.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_dropdown_values.py test/test_filter_exclusion_sets.py -q 2>&1 | tail -25` collects cleanly; `test_saved_state_depends_only_on_the_widgets` fails showing `{'g1': 3, 'g2': 3, 'k1': '3'}` and `test_a_string_code_keeps_its_exact_text` fails showing `'1'`.]]></verify>
  <done>Both files exist, collect, and every regression test fails on the unmodified tree for the reason its stub names.</done>
</task>

<task type="auto" id="17-02">
  <name>Measure the auto filter truth in Stata</name>
  <files>scripts/extract_filter_truth.do (new), test/fixtures/filter_truth.json (new)</files>
  <action>
    Write `scripts/extract_filter_truth.do` as the "Stata truth" section specifies: `sysuse auto`, the eight commands, each `r(N)`/`r(mean)` written to a record file with `%21.17g`, the three columns written one line per observation, a trailing `python:` block (never calling Stata, backtick as `\x60`) writing `test/fixtures/filter_truth.json` with keys `all`, `foreign_1`, `price_4000_5000`, `foreign_1_price_4000_5000`, `data`, `_meta`. Run it under `arch -arm64 /usr/local/bin/stata-mp -b do` from `/tmp/dash-s17` with `STATATMP=/tmp/dash-s17/tmp/`. `git add -f test/fixtures/filter_truth.json`.
  </action>
  <verify>`python3 -c "import json;d=json.load(open('test/fixtures/filter_truth.json'));print(d['all']['count'], d['foreign_1']['count'], len(d['data']['price']))"` prints `74 22 74`; `python3 -m pytest test/test_fixtures_are_committed.py -q` passes.</verify>
  <done>Stata's counts and means for the four filter states on auto, with the columns they were measured on, are committed as a fixture a test names.</done>
</task>

<task type="auto" id="17-03">
  <name>Carry exact text and numeric values through Python</name>
  <files>dash_render.py, test/function_test_map.py, test/test_saved_filter_layers.py</files>
  <action>
    In `dash_render.py`: add `_dash_filter_numeric(column)` beside `_dash_filter_rangeable` (17530) and use it at 1838-1839; rewrite `_dash_option_value` (17413-17441) per TR-17.2 with a new docstring; rewrite `_dash_dropdown_values` (1806-1812) per TR-17.3; in `_dash_filter_widget`'s dropdown branch set `w._dash_numeric = _dash_filter_numeric(series)` after 17619 and change only the fallback line of `_label` (17608) so an unlabelled float reads as today (`str(int(rv))` if `float(rv).is_integer()` else `str(rv)`) — leave every other line of `_label` and `date_text` to S12; rewrite `_dash_dropdown_mask` (17669-17675) per TR-17.5 with the shared-rule comment block naming `_DASH_FILTER_MASK_JS` and the parity test; add `"numeric"` to `_filter_specs` (23707-23714); add the `isinstance(v, str)` branch to `_dash_json_value` (13840) with the docstring naming `_dash_csv_payload`, the snapshots, `dcount` and marker labels; change line 6527 per TR-17.8 and nothing else in `_apply_colorvar`; add `_dash_filter_numeric` to the served function list (24466-24687). `_dash_frame_filter_mask`'s docstring (13950-13961) is corrected.
    `test/function_test_map.py`: add `'_dash_filter_numeric': 'test/test_dropdown_values.py::TestOptionValues::test_the_numeric_test_is_the_dtype'`; re-point `_dash_option_value` (443), `_dash_dropdown_mask` (318), `_dash_dropdown_values` and `_dash_json_value` (365) at the new tests if `fncov_mutate.py --map` shows the old ones no longer die.
    `test/test_saved_filter_layers.py::TestTheOptionValueOfADate` (1219-1245): milliseconds become `1009756800000.0` (a float; 1225, 1229) and `float(int(v.astype(np.int64)))` at 1234; `_dash_option_value(1.0) == 1.0` at 1244; the class docstring says values are floats. Do not touch 1213.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_dropdown_values.py -q -k "OptionValues or TheWidget or TheSnapshot or Colorvar" 2>&1 | tail -3` passes; `python3 -m pytest test/test_saved_filter_layers.py test/test_export.py test/test_resource_limits.py test/test_label_sinks.py test/test_function_test_map.py -q 2>&1 | tail -3` passes; `python3 -m pytest test/test_statistical_helpers.py -q -k CarriesEveryName test/test_resource_limits.py -q -k DefinesEveryName` passes.]]></verify>
  <done>A dropdown carries floats for a numeric column and exact text for a string one, the served mask compares by the column's kind, every snapshot and the CSV keep strings as text, and the colorvar string path reads 'nan' as a category.</done>
</task>

<task type="auto" id="17-04">
  <name>Make the saved page's mask the twin of the served one</name>
  <files>dash_render.py, test/test_filter_exclude.py, test/test_export.py</files>
  <action>
    `dash_render.py` `_DASH_FILTER_MASK_JS` (14110-14164): rewrite the dropdown branch per TR-17.6 and add the optional `use` parameter (`const idx = (use === undefined || use === null) ? [...Array(filter_specs.length).keys()] : use;` and loop over `idx`); write the rule comment block above `dash_filter_mask` naming `_dash_dropdown_mask` and `test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree`. `_DASH_CSV_SAVED_JS` is unchanged (three-argument call).
    `test/test_filter_exclude.py`: `_MOVES["dropdown"]` value `"1"` → `1.0`; `_script_args` (434-455): `Select(value=1.0, options=[("__all__", "All"), (0.0, "0"), (1.0, "1")])`, the spec gains `"numeric": True`. `test/test_export.py`: correct the comment at 199-201 (the snapshot now holds "007" as text) and add `W("foreign", "dropdown", 0.0)` to `test_frame_filter_mask` beside the `"0"` case. Flip S03's `test/test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` to assert the twins now agree (rename it `..._agree_since_x1`, keep the docstring's history); if that file counts against this task's three-file limit, flip it in 17-07 with the other `test_js_runner.py` pin and say so in both commit messages.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_dropdown_values.py -q 2>&1 | tail -3` passes in full (parity, both modes, hostile); `python3 -m pytest test/test_filter_exclude.py test/test_export.py test/test_linking_filters.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_mode_parity.py -q -k "dropdown or filter or exclude or Select" 2>&1 | tail -3` passes.]]></verify>
  <done>Node and pandas keep the same rows for every hostile column and option, the saved page selects 5e-05 and 1e21, and the tests that set a dropdown by string carry the widget's real value.</done>
</task>

<task type="auto" id="17-05">
  <name>Certify X1 from a Stata dataset</name>
  <files>test/test_dropdown_values.cscript (new), test/run_all_cscripts.do</files>
  <action><![CDATA[
    Write `test/test_dropdown_values.cscript` (`cscript` header, `cert_helpers.do`, `global dash_nobrowser 1`): `clear; set obs 12; gen str fips = string(_n, "%02.0f"); replace fips = "1" in 3; replace fips = "1.0" in 4; replace fips = "None" in 5; replace fips = "nan" in 6; replace fips = "" in 7; gen double tiny = 5e-05; replace tiny = 1e21 in 4/6; replace tiny = 0.1 in 7/12; gen float f32 = 0.1; gen y = _n; gen x = _n`. For each text in `01 1 1.0 None nan ""` compute `count if fips == "<text>"` into a local (six values), and `count if tiny == 5e-05`, `count if tiny == 1e21`, `count if f32 == float(0.1)`. Register `dash scatter y x, name(g1)` and call `_dash_serve_spec, specpath("`s'") datapath("`d'") filter(fips, type(dropdown)) filter(tiny, type(dropdown)) filter(f32, type(dropdown))` (if `_dash_serve_spec` refuses a filter() written after its own options, put the filters where `test_help_claims_5.cscript:588` puts them). A `python:` block (`sys.path.insert(0, "<repo>")` and `"<repo>/test"`; `import dash_render`; `from js_runner import JsSession`): render `DashRenderer(s, d, out)`, for each dropdown option set it through `JsSession` and count the g1 source's rows; build `ServerAppBuilder(s, d).build(app)`, load the app with the `_load_app` recipe (exec with the curdoc attach replaced), `make_document(doc)`, and for each option set `Select.value` and fire its `value` callbacks (as `test_filter_exclude._served` does), counting rows. Write each count to `st_global` and assert in Stata against the `count if` locals: saved == served == Stata for every value, and the option lists contain `"None"`, `"nan"` and `""`. Add a hostile row `replace fips = "__proto__" in 8` and assert it is listed and selects one row in both modes and the text appears in no `CustomJS.code`. Register the script in `test/run_all_cscripts.do` (copy the test_help_claims_7 block). Run it: `cd /tmp/dash-s17 && STATATMP=/tmp/dash-s17/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <repo>/test/test_dropdown_values.cscript`; a `python:` SKIP is a failure to investigate (`c(python_exec)`), and node must be installed (`JsSession` fails loudly, never skips).
  ]]></action>
  <verify>The cscript's log ends without `r(` and with its PASS line; `grep -c 'test_dropdown_values.cscript' test/run_all_cscripts.do` is at least 4; `python3 -m pytest test/test_cscript_hygiene.py -q` passes.</verify>
  <done>From Stata's own data and `count if`, both modes keep exactly the rows a string or double dropdown value names, and list every category including 'None', 'nan' and the blank.</done>
</task>

<task type="auto" id="17-06">
  <name>Mask each served target by the filters that apply to it</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Add module-level `_dash_filter_applies(target, exclude, owner_of, members=None)` and `_dash_widgets_for(target, widgets, owner_of, members=None)` beside `_dash_excluded` (17975), docstrings quoting BR-17.1 and dash.sthlp's link-group sentence; add both to the served function list and to `test/function_test_map.py` (naming `test/test_filter_exclusion_sets.py::TestTheHelpers::test_filter_applies_and_widgets_for`).
    Served template: outside `_make_filter_cb`, compute `_shared_members = [g for g, s in graph_sources.items() if any(x is shared_source for x in (s if isinstance(s, list) else [s]))]` and pass it as a new keyword `_members=`. Inside `_on_filter_change` implement TR-17.11: delete `excl` (26768) and the three `continue`s (26773-26774, 26881-26882, 26948-26949); add `_masks = {}` and `_mask_for(target, members=None)`; the graph loop starts each `gname` with `mask = _mask_for(gname)` and `fdf = _df_ref[mask]` (the shared-source hit uses `_mask_for(None, _members)` for the group's write at 26870-26877 and its `_brush_rows` line); the facet branch ANDs onto that target's `mask`; the aggregate loop uses `_mask_for(gname)`; the KPI loop uses `_k_fdf` from `_mask_for(kname)`. Keep every other line — the qualifier re-application, `_dash_refresh_unlinked`, `_dash_refresh_linked`, the redraw and the throttle — as it is.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py -q -k "served or Helpers" 2>&1 | tail -3` passes; `python3 -m pytest test/test_filter_exclude.py test/test_help_claims_3.py test/test_linking_filters.py test/test_saved_filter_layers.py -q -k "served or Served" 2>&1 | tail -3` passes except `TestExcludeHoldsWhileItsOwnFilterMoves::test_served`, which now fails with `{'g1': 5, 'g2': 3, 'k1': '5'}` (17-07 rewrites it); the served-name guards and `test_function_test_map.py` pass.]]></verify>
  <done>The served app recomputes every graph, group, aggregate and card from the filters that apply to it on every move, cached per exclusion set; the state depends only on the widgets.</done>
</task>

<task type="auto" id="17-07">
  <name>Mask each saved target by the filters that apply to it</name>
  <files>dash_render.py, test/test_help_claims_3.py, test/test_filter_exclude.py</files>
  <action>
    `dash_render.py` `_build_filter_widgets` (23723-23826): replace the per-callback exclusion filtering with TR-17.9 — compute `use` per target once (graph sources by id with their member graph names, aggregates and derived sources by graph name, KPIs by name), build `_graph_srcs`, `_graph_use`, `_excluded_srcs` (empty `use`), `_agg_srcs`/`_agg_use`, `_der_srcs`/`_der_use`, `_kpi_config` (with `"use"`) and `_kpi_divs` ONCE, then set the same args on every callback: the existing keys plus `graph_use_json`, `agg_use_json`, `derived_use_json` (JSON lists of index lists). `FilterBuilder.build_dropdown`/`build_slider`/`build_range` placeholders (15048-15065, 15130, 15189) gain the three keys as `"[]"`. `_FILTER_JS`: implement TR-17.10 — `dash_mask_for`, `dash_ids_for`, per-source `use` in the graph loop (14235-14263, keeping the identity loop's shape) and the derived loop (14310-14340), per-group KPI application replacing the single call at 14702, and the aggregate block (14725-14915) reading `ac.use` wherever it reads `active`, `_active_ids` or `new_data` — read that block end to end first. The fallback write (14347-14351) keeps `active`/`new_data`.
    `test/test_js_runner.py` (S03): flip `TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` to the widget-implied `{"g1": 5, "g2": 5, "k1": "5"}` its docstring already states, and set the foreign dropdown to `1.0` in `TestASessionCarriesState::test_two_moves_chain_on_one_session`; this task then touches four files — commit `test_js_runner.py`'s flips with `test_help_claims_3.py`'s, as one flip commit, immediately before the `dash_render.py` commit, and say so in both messages.
    `test/test_help_claims_3.py`: rewrite `TestExcludeHoldsWhileItsOwnFilterMoves` (about 415-497 once S03 has landed) as `TestAnExclusionHoldsAgainstEveryMove` — docstring stating the new rule and citing dash.sthlp:1128-1138 — asserting the four-state sequence in both modes (saved through `JsSession`, served through chained `tp._fire`); flip `"1"` → `1.0` at 452 and 494 and in `TestAnExcludedMemberOfALinkGroupIsFilteredWithIt` (404, 408). `test/test_filter_exclude.py`: `TestThePrimarySourceFallback` and `_script_args` gain `graph_use_json` (`[[0]]` for a listed source) and the other two keys; the class docstrings of section 1 say sources are listed with their `use` and protected when none applies.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py test/test_filter_exclude.py test/test_help_claims_3.py test/test_linking_filters.py test/test_saved_filter_layers.py test/test_export.py test/test_dropdown_values.py -q 2>&1 | tail -3` passes; `python3 -m pytest test/test_mode_parity.py -q 2>&1 | tail -3` passes; the served-name guards pass.]]></verify>
  <done>The saved page's script computes one mask per distinct exclusion set and rewrites every graph, group, aggregate, derived source and card on every move from the widgets' current values; both modes agree on every sequence.</done>
</task>

<task type="auto" id="17-08">
  <name>Close E2 and X1 in BUGS.md, dash.sthlp and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action>
    `dash.sthlp` 1109-1116 (`type(dropdown)`): "select widget listing every distinct value of varname: a numeric or date variable's values as numbers (a missing value is not listed), a string variable's exact text, its empty string as a blank row. Selecting a value keeps the observations equal to it — a number compared as a number, a text compared exactly, so '01' and '1' are two values — in the saved page and the served app alike. Value labels are used for display text when available. …" keeping the limit sentence. 1128-1138 (`exclude()`): "prevent the filter from affecting the specified graphs and KPI cards, each a registered name, whatever moves. Each graph, card, and link group is redrawn on every move from the observations kept by the filters that do not exclude it, so its state depends only on the widgets' current values. Excluding a by() graph excludes every one of its panels. A graph in a link() group draws from the group's one source, so the group is filtered by a filter unless every graph of the group is excluded from it." Delete the sentence "An exclusion holds while its own filter is the one that moves …".
    `CHANGELOG.md` `### Results that change` → `**Qualifiers, filters and KPIs**` (60): "An excluded graph or card kept the rows of the last move made by a filter that did not exclude it, so after price → [4000, 5000], foreign → 1, price → full range an excluded graph showed 3 rows where the widgets implied 5. Every target is now masked by exactly the filters that do not exclude it, on every move, in both modes. (WP-28, E2)"; "A dropdown on a string variable rewrote '01', '1.0' and ' 2' to '1' and '2' and merged their rows, dropped the categories 'None', 'nan' and 'NaT', and on the saved page could not select a number below 1e-4 or at or above 1e21; the saved page's snapshot also turned a string code into a number after a move (a marker label '007' read 7; a dcount of codes merged them). Numbers are now compared as numbers and text exactly, in both modes. (WP-28, X1)". Under `### Fixed`: the CSV download keeps string codes as text.
    `BUGS.md`: two closed entries in the file's shape (Title / File Names and Line Numbers / Description / Suggested fix / Resolution, once each): E2 naming `test/test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved_state_depends_only_on_the_widgets` and `::test_served_state_depends_only_on_the_widgets` and `test/test_help_claims_3.py::TestAnExclusionHoldsAgainstEveryMove`; X1 naming `test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree`, `::TestTheSnapshot::test_the_snapshot_keeps_a_string_column_as_text` and `test/test_dropdown_values.cscript`. Grep all three files for `claude|anthropic`.
    Full suite once: `python3 -m pytest test/ -q`; then the two new cscripts and `test_help_claims_3`-adjacent cscripts (`test_filter_label.cscript`, `test_export.cscript`) under `arch -arm64 /usr/local/bin/stata-mp -b` from a scratch dir with `STATATMP`.
  </action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips; `python3 -m pytest test/test_tracking_documents.py -q` passes; `grep -n 'holds while its own filter' dash.sthlp` prints nothing; the cscript logs end without `r(`.]]></verify>
  <done>E2 and X1 are closed in BUGS.md naming their regression tests, dash.sthlp states the exclusion and matching rules as they now hold, CHANGELOG records the rows that change, and the full suite is green.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes in both modes where a page exists; every pinned test listed is flipped in the commit named, none deleted.
- `test/fixtures/filter_truth.json` is committed (`git add -f`) and read by `test_filter_exclusion_sets.py`.
- `_dash_option_value`, `_dash_dropdown_values`, `_dash_dropdown_mask`, `_DASH_FILTER_MASK_JS` and `_dash_json_value` implement the one rule; `mask_parity` passes on the hostile columns.
- `_dash_filter_numeric`, `_dash_filter_applies`, `_dash_widgets_for` are in the served function list and in `test/function_test_map.py`.
- `filter_specs_json` carries `numeric`; callbacks carry `graph_use_json`, `agg_use_json`, `derived_use_json`; `kpi_config` entries carry `use`.
- `test_dropdown_values.cscript` passes under `arch -arm64 /usr/local/bin/stata-mp -b`; the full pytest suite is green with no skips.
- BUGS.md carries closed E2 and X1 entries; dash.sthlp 1109-1116 and 1128-1138 are rewritten; CHANGELOG has both "Results that change" lines.

## Notes

- **Read `_FILTER_JS` end to end (14177-14915) before editing it.** The aggregate block (14725-14915) is the consumer of the mask most easily missed; `test_an_aggregate_and_a_derived_layer_take_their_targets_mask` exists to catch it.
- **Merge order with S12.** Both sections edit the dropdown branch of `_dash_filter_widget`; apply S17's diff first (values, `_dash_numeric`), then S12's (labels). S12 must keep labels unique per widget: with numeric values BokehJS maps a label back to the first value that carries it.
- **Coercion keeps the old tests alive, briefly.** After 17-03 a string `"1"` still selects on a numeric column (the pandas mask does `float(value)`, the JS `Number(val)`), so tests that set `"1"` do not fail before 17-04/17-07 flip them. Flip them anyway: the widget's real value is `1.0`.
- **`_dash_json_value` is the CSV's writer too** (13946). Keeping strings as text fixes the download of string codes (a `### Fixed` line), and `test_export.py`'s `_dash_csv_text_value` table (566-570) is unaffected (it already returns text).
- **The identity loop's text is pinned** by `test_linking_filters.py:331-360`; keep `_kept_ids_by_src`, `_ids_i`, `_active_ids.has(...)` names or update that test in the same commit with the reason.
- **`excluded_sources` keeps a meaning**: sources no filter applies to. That keeps `TestTheCallbackKnowsWhatItProtects`'s invariant and the JS fallback guard true, and it is the correct behaviour (such a source never changes).
- **Served `Select.value` after a browser change is a JS number**, so the callback receives a float; the pandas mask must not `str()` it. `tp._served_after_move` picks by label and needs no change.
- **A dropdown over the option limit** on a numeric column becomes a range (`_dash_filter_effective_type`), unchanged; the string case still truncates to the first `limit` values in sort order.
- **Stata invocation**: only `arch -arm64 /usr/local/bin/stata-mp -b do` from a scratch dir with `STATATMP=<dir>/tmp/`; at most three concurrent sessions across the batch; a `python:` SKIP means `python_exec` was dropped — check `c(python_exec)`, never count the run as a pass.
- **pytest**: only the changed files while iterating; the full suite once, in 17-08, as `python3 -m pytest test/ -q`; never a second concurrent full run.
- **S03's runner is the only way to chain saved moves**; the older `_run_callback` in `test_filter_exclude.py` re-encodes from unchanged models and cannot express a sequence (research [B §2.3]).
