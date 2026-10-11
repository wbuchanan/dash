# Section 17: Filters: exclude() and dropdowns (E2, X1)

> Part of: WP-28 · Gaps: E2, X1 · Risk: red · Batch: 2 · Depends on: 03, 07 · Blocks: 11, 12, 19 · Tasks: 15, 2 commits (X1, E2)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **03, 07** · Blocks **11, 12, 19** · Risk **red** · Commits: two commits, X1 then E2 → CHANGELOG `Results that change`

- D4, `index.md` step 2: S11 (batch 3) adapts `dash_apply_kpis` to this section's per-group call on the merged tree; S12 (batch 3) owns dropdown LABELS, this section owns VALUES, the grouping mechanism and the masks; the batch-2 merge order is S04, S05, S13, S17, S16, S14, so this section merges before S16 (which owns the rest of `_apply_colorvar`) and before S14 (which touches `_dash_csv_meta`, `_dash_facet_label`, the saved filter builder at 23598-23603 with one-line lookups; consistency #13).
- DISCOVERY Q26: this section owns the grouping mechanism — a numeric dropdown's option value is its group's first value, the saved spec entry carries `"groups": [[value, member, ...], ...]`, the served widget `_dash_groups = {value: (members,)}`, and both masks keep a row whose number equals any member of the selected group (NaN never); this section ships groups of one and pins the rule with `test_two_values_sharing_a_label_select_both`; S12 later forms the groups by display text.
- The KPI marker (section-11 and `test/test_kpi_brush.py:251` rely on it): the per-group KPI loop keeps the literal `dash_apply_kpis(new_data,` marker as a comment on the line it replaces, and its calls read `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`; `test/test_kpi_brush.py:251` and the brush wiring (23483-23485) slice up to the FIRST occurrence.
- section-03's fixed names: `JsSession` and `mask_parity` by those names; the pins S03 writes in `test_js_runner.py` for today's E2/X1 answers are flipped here (17-04 for X1, 17-10 for E2). Stub: `dcount` and string marker labels keep string codes as text after a move. consistency #22: the marker-label columns are `__dash_mlabel_*` (S07's rename).
- D11; `sections/BRIEF.md` "Certification scripts" and `index.md` R1: the X1/E2 comparisons with `count if` and `summarize` are a block `* ==== S17 X1 E2: filters vs count and summarize ====` … `* ==== end S17 ====` (cases FT-01..FT-06, gated by `GAPS2_ONLY`) inserted into `test/test_gaps2_truth.cscript` above its last line; the page-only row-count checks join `test_e2e_filters.cscript` (FL-X1-1, FL-E2-1, FL-E2-2); no new script, no runner edit, no pin change. `sections/BRIEF.md` "Running one cscript", `index.md` step 0a: a cscript runs through a two-line driver do-file in the scratch directory. D12; `sections/BRIEF.md` "Fixtures": `filter_truth.json` carries `_meta` with the four keys.
- D1, `index.md` step 1: two commits, one per gap, each made on the worktree branch `wp28-s17` by that gap's closing task (17-06 for X1, 17-15 for E2); the E2 tests are written only after the X1 commit so no commit carries a red tree. `index.md` R3, section-01 TR-01.7: the X1 and E2 markers sit in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list and are replaced in place. consistency #15, `index.md` R3: this section owns dash.sthlp 1109-1138 and writes S12's sentence into it.
- D7: 17-01, 17-04 and 17-07 (old ids) are split as feasibility.md proposes; ids are renumbered 17-01..17-15; names are 3-8 words; `<files>` carry no `(new)`; `<done>` is past tense.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

Two silent defects in the one mechanism that decides which rows a dashboard shows after a widget moves.

**E2** (GAPS2): "Each callback masks with all filters but writes only the targets it does not exclude (saved dash_render.py:23723-23771, :14346; served :26763-26772). An excluded item therefore keeps whatever the last non-excluding move wrote. Served probe: price to [4000,5000], then foreign=1, then price back to its full range gives g1=3, g2=5, k1=3, where the current widgets imply 5 under either rule." dash.sthlp:1128-1138 documents that behaviour as a rule ("An exclusion holds while its own filter is the one that moves"), and `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` (415-497) pins it, saying in its own docstring that when exclusion is made to hold against every move "the help and this test change together". After this section each graph, link group, aggregate layer, derived source and KPI card is masked by exactly the filters whose `exclude()` does not name it, recomputed on every move from the widgets as they now stand, in both modes; the state after a sequence of moves depends only on the widgets' current values.

**X1** (GAPS2): "`_dash_option_value` (17413-17438) turns any value that reads as a whole number into integer text, string values included. So '01', '1.0' and ' 2' all become '1' or '2'. `_dash_dropdown_values` (1806-1812) drops the categories 'nan', 'None' and 'NaT'. … Python writes `5e-05` where JavaScript writes `0.00005`. So on the saved page a numeric value in [1e-6, 1e-4), or at 1e21 or above, selects nothing." Research [B §2.1] measured more: the saved snapshot `_dash_json_value` (13828-13862) coerces string codes to numbers for `_orig_data`, every graph snapshot and every derived snapshot, so after a move a marker label "007" reads 7 and a `dcount` card merges '01' and '1'. (GAPS2's "keeps no row for '1'" did not reproduce: both modes select the same, wrong, merged rows.) After this section a numeric column carries numeric option values and both masks compare numbers as numbers (NaN never equal); a string column keeps its exact text, 'nan', 'None' and 'NaT' are ordinary categories, `""` is listed blank, numeric missing is not listed; and every snapshot keeps a string column as text.

The two gaps share this section because they are one code path: the widget's value, the mask built from it, and which targets that mask is written to, in `_DASH_FILTER_MASK_JS`/`_FILTER_JS` on the saved page and `_dash_frame_filter_mask`/`_on_filter_change` in the served app. Section 03's stateful node runner (`test/js_runner.py`: `JsSession(models)` with `.set(widget, value) -> old`, `.run(callback, cb_obj=None, *, commit=True) -> dict`, `.rows(source)`, `.ids(source)`, `.state() -> {"sources": {id: data}, "booleans", "divs": {id: text}, "widths"}`, and `mask_parity(df, filter_specs, widget_values, *, raw=False) -> (js_mask, pandas_mask)`, whose JS side runs `_DASH_FILTER_MASK_JS` on the specs it is given and encodes the frame through `_dash_json_value` exactly as the saved snapshot does) is what makes the multi-move and node-vs-pandas assertions possible. S03 also pins today's answers to E2's three-move sequence and X1's small-number case in `test/test_js_runner.py`, naming this section as the one that flips them.

**Test order (CLAUDE.md rule 7) and commit rule (D1): the section is two gap groups, X1 first.** Task 17-01 writes every failing X1 test, runs it against the unmodified tree and saves the failure text to `<scratch>/17-01-failure.txt` — it does not commit (a red tree is never committed, rule 4); 17-02 to 17-05 turn X1 green and certify it; 17-06 closes X1's BUGS.md entry and documents and makes the X1 commit, subject ending `(GAPS2 X1)`, body opening with the saved failure text (S01 TR-01.9). Only then does 17-07 write the failing E2 tests (they would otherwise be red inside the X1 commit) and save `<scratch>/17-07-failure.txt`; 17-08 measures the Stata truth; 17-09 to 17-14 turn E2 green and certify it; 17-15 closes E2 and makes the E2 commit, subject ending `(GAPS2 E2)`. Both commits are made on the worktree branch `wp28-s17`; the merger lands them on `s3-bugs` in that order (`index.md` step 1).

## Risk: [red] — the saved page's filter script is rewritten around per-target masks, the served callback's three loops change their frame, and every dropdown's value type changes under tests that pin strings

**Why.** `_FILTER_JS` (14177-14915) is one 740-line script with five consumers of the one `active` mask; each has to take its target's own mask or a target silently keeps the wrong rows — the exact shape of E2. The value-type change reaches every place a dropdown value is written or compared: the widget builder shared by both modes, the snapshot, the JS, the pandas mask, the CSV download, and a dozen tests that set `"1"`.

**Risk factors.**
1. A consumer of `active`/`_active_ids` in `_FILTER_JS` missed (the aggregate block at 14725-14915 is the easiest to miss) leaves one layer type on the old rule.
2. `_dash_json_value` is also the CSV download's value writer (13946) and `_dash_option_value`'s date path (17430); keeping strings as text must not change a date's milliseconds.
3. Section 12 (batch 3) edits the same dropdown branch of `_dash_filter_widget` (17570-17622) for LABELS and forms the value groups by display text; this section edits it for VALUES and ships groups of one. Same function, different lines — this section lands first and S12 rebases on it.
4. `test_linking_filters.py::TestTheShippedJavascriptMasksByIdentity` (331-360) reads `_FILTER_JS`'s text; the identity loop must keep its shape. `test/test_kpi_brush.py:251` and the brush wiring (23483-23485) slice `_FILTER_JS` up to the first `dash_apply_kpis(new_data,`; the per-group loop must keep that text where it is.
5. Bokeh `Select` with numeric values resolves a label back to the first value that carries it, so two values with one display text must be ONE entry (Q26): the entry's value is the group's first value and the mask matches every member — the mechanism this section builds and S12 fills.
6. S11 (batch 3) rewrites the body of `dash_apply_kpis` and the card config fields on the tree this section leaves; S16 (same batch, merged after this section) rewrites `_apply_colorvar` around the one line this section changes.

**Mitigation.** One documented rule in one place per mode, pinned by `mask_parity` over hostile columns and over a two-values-one-label group; a `JsSession` multi-move test per target kind (graph, link group, by() panel, aggregate, derived, KPI); the boundary with S12 written down and the merge order given; the KPI marker rule written verbatim (TR-17.10) and checked by a grep in the task that touches it.

## Dependencies

- **Depends on:** 03 — `test/js_runner.py` (`JsSession`, `mask_parity`, `NODE`) with the FIXED names above; 07 — the `__dash` prefix rule, the `ROW_ID` fill and the `__dash_mlabel_*` column names this section's tests read.
- **Blocks:** 11 (S11 adapts `dash_apply_kpis` to the per-group call and adds `fmt`/`storage` beside `use` in `kpi_config`), 12 (labels, `unit`, the display-text groups) and 19.
- **Parallel batch:** 2. **Can run with:** 04, 05, 13, 14, 16. **Merge order within the batch (`index.md` step 2 merge order):** S04, S05, S13, S17, S16, S14 — this section merges before S16 (which owns every other region of `_apply_colorvar`) and before S14 (whose one-line `_dash_value_labels_for` lookups in `_dash_csv_meta` 13909-13912, `_dash_facet_label` 15601-15607 and the saved filter builder 23598-23603 sit beside, not inside, this section's hunks; consistency #13). S12 (batch 3) then rebases its label change onto the float-valued `rv` and the `groups` mechanism; S11 (batch 3) rewrites `dash_apply_kpis`'s body under the marker this section keeps (section-11; `test/test_kpi_brush.py:251`).
- Why: S12 changes what a dropdown option *says*; this section changes what it *is*, what selecting it does and which values one entry stands for. S16 edits `_apply_colorvar`'s numeric paths; this section edits one line of its string path.

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

The snapshot: `_dash_json_value` (13828-13862) ends `f = float(v)` → `"01"` becomes 1.0, `"nan"` None; `DashRenderer._to_serialisable` (22983-22993) calls it, and is applied to `_orig_data` (23685-23688), each graph snapshot (23693-23700), each derived snapshot (23811-23816) and the CSV-only snapshot (23835). `_dash_csv_payload` (13946) also calls `_dash_json_value` per cell. The served app snapshots raw (`_orig_src_data`, 26728-26731) and does not coerce. The JS `dcount` is `new Set(vals.map(String)).size` (14525), so a coerced snapshot merges '01' and '1'; a marker label column (`__dash_mlabel_*` after S07's rename, S07 TR-07.2 `_DASH_MLABEL_PREFIX`) is coerced the same way.

The colorvar string path (6527): `strs = ["" if v is None or str(v) == "nan" else str(v) for v in raw_col]` — the text 'nan' is read as missing.

Bokeh: `Select.options` is `List(Either(String, Tuple(AnyRef, String)))` and `Select.value` is `AnyRef` since 3.4 ([W §1f], verified on 3.9.0: `Select(options=[('__all__','All'), (1.0,'one')])` builds); the declared floor is 3.8 (S09). Research [B §2.1]'s "Bokeh `Select` values must be strings" is superseded by [W §1f]. ECMAScript writes `5e-05` as `0.00005` and `1e21` as `1e+21`; Python writes `5e-05` and `1e+21` ([W §2]) — no string comparison can be made to agree across both; numbers must be compared as numbers. BokehJS maps a label back to the FIRST option value carrying it, so two values with one label cannot be two entries (Q26).

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
14650    dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);
14725    // agg_configs is parsed from the JSON string arg.
14726    const agg_configs = JSON.parse(agg_configs_json);
```

The consumers of the one mask: `new_data` (14191-14200) for the fallback `source` and the KPIs; the graph-source loop (14235-14263, by row identity through `_active_ids`); `view_filters` rebuilt from `_kept_ids_by_src` (14270-14277); the derived-source loop (14310-14340, `_active_ids` at 14318); the fallback write (14347-14351); `dash_apply_kpis` (14493-14648, the one call at 14650 — GAPS2's "14702" is the same line before WP-27's edits; `test/test_kpi_brush.py:251` and the brush wiring at 23483-23485 slice the script from `// ---- KPI recompute, shared by` up to the FIRST `dash_apply_kpis(new_data,`); the aggregate recount (14725-14915).

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

None for filters. `test/fixtures/data/auto.csv` holds only `mpg` and `weight`, so the E2 fixture carries the `mpg`, `price` and `foreign` columns it was measured on. `test/fixtures/stat_truth.json` is `scripts/extract_stat_truth.do`'s, which S05 extends in this batch — this section does not touch that script.

### Existing tests that pin today's behaviour (flip in the fix commit; never delete)

- `test/test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` (415-497): expects `{g1:3, g2:3, k1:"3"}` after price then foreign. **Rewritten** as the multi-move class of TR-17.12 (its docstring asked for exactly this) in 17-13.
- `test/test_help_claims_3.py` 452 (`w_for.value = "1"`), 494 (`tp._fire(w_for, "1")`), and `TestAnExcludedMemberOfALinkGroupIsFilteredWithIt` (`tfe._saved(..., "1")`, `tfe._served(..., "1")`): the value a foreign dropdown carries becomes `1.0`. They keep passing meanwhile (the mask coerces a string on a numeric column), and are flipped to the real value type in 17-13.
- `test/test_filter_exclude.py` `_MOVES["dropdown"]` (62-66) `"1"` → `1.0`; `_script_args` (434-455) `Select(value="1", options=["__all__","0","1"])` → `Select(value=1.0, options=[("__all__","All"),(0.0,"0"),(1.0,"1")])` and the spec gains `"numeric": True` and `"groups": [[0.0], [1.0]]`; `TestThePrimarySourceFallback` (469-496) keeps its three cases (the fallback guard stays); `TestTheCallbackKnowsWhatItProtects::test_every_graph_source_is_filtered_or_protected_not_both` (407-431) holds under TR-17.9's split; `test_an_unwired_callback_declares_the_argument` (433-441) holds and the new placeholder args join it (17-03 for the values, 17-11 for the `use` args).
- `test/test_saved_filter_layers.py::TestTheOptionValueOfADate` (1219-1245): `"1009756800000"` → `1009756800000.0` (1225, 1229, 1234: a float), `_dash_option_value(1.0) == "1"` → `== 1.0` (1244); the string case (1245) holds. **The date-label pin at 1213** (`labels[0] == "2001-12-31 00:00:00"`) is a LABEL and belongs to S12; this section does not touch it.
- `test/test_export.py::TestTheHelpers::test_json_value` (584-594) holds (`_to_serialisable("007") == _dash_json_value("007")` is true both before and after); `test_frame_filter_mask` (596-614) holds through the coercing mask, and gains a `0.0` case; the comment at 199-201 ("The saved snapshot holds "007" as 7") becomes stale and is corrected (17-03).
- `test/test_resource_limits.py::TestTheHelpersOneByOne::test_dropdown_values_are_the_listed_options_sorted` (1380-1384) holds (floats sort by value).
- `test/test_label_sinks.py` (`("Select","options.value"): DATA` at 531; Sink 600) holds; run it.
- `test/test_help_claims_4.py` `_saved_filter_move` (220): if it sets a dropdown to a string on a numeric column, flip to the float.
- `test/test_linking_filters.py::TestTheShippedJavascriptMasksByIdentity` (331-360): pins the identity loop's text; keep the loop's shape (see Notes).
- `test/test_kpi_brush.py:251` and `test/test_date_range.py:995-1012` slice `_FILTER_JS` on text near the KPI call; the marker rule of TR-17.10 keeps them green.
- `test/test_keyword_names.py::TestExcludeAByGraph::test_one_rule_matches_it` pins `_dash_excluded`, which stays.
- **S03's measurement pins (flip here, S03 says so):** `test/test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` (the two twins disagree on 5e-05 today → they agree, 17-04) and `test/test_js_runner.py::TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` (`{g1:3, g2:5, k1:"3"}` today → `{g1:5, g2:5, k1:"5"}`, 17-10); `test/test_js_runner.py::TestASessionCarriesState::test_two_moves_chain_on_one_session` sets the foreign dropdown to `"1"` — still selects through coercion; flip to `1.0` in 17-10 for honesty.
- S03 also turns `test_filter_exclude.py`'s `_run_callback` and `test_help_claims_3.py`'s `_run_saved` into shims over `JsSession` and deletes `_RUNNER_DIVS` (321-327), so the line numbers quoted for `test_help_claims_3.py` below are "about" once S03 has landed; the class and helper names are authoritative.
- `test/test_function_test_map.py` fails until every new helper is mapped (17-02, 17-09).

## User stories

- **US-17.1** As the dashboard viewer, I want every card and graph to reflect the widgets as they now stand after any sequence of moves, so that an excluded graph never shows a filter state that no longer exists.
- **US-17.2** As the Stata user, I want `exclude()` to mean "this filter never touches these targets" and nothing else, in both modes.
- **US-17.3** As the Stata user, I want a dropdown on a string variable to list every distinct text — '01' and '1' apart, 'nan' and 'None' as the categories they are, `""` as a blank row — and to keep exactly the rows equal to the chosen text, as `count if var == "<text>"` counts them.
- **US-17.4** As the dashboard viewer, I want a dropdown on a numeric variable to select 5e-05 or 1e21 on the saved page as it does when served.
- **US-17.5** As the dashboard viewer, I want a marker label "007" and a `dcount` of codes to read the same after a move as before it.
- **US-17.6** As the maintainer, I want one written matching rule shared by the saved page's script and the served app, pinned by a test that runs both on the same columns.
- **US-17.7** As the dashboard viewer, I want two numbers that display as the same text under the variable's format to be one dropdown entry that selects both (Q26), so that a listed entry never hides a row.

## Business requirements

- **BR-17.1** A target (a graph, a link group, a `by()` graph with its panels, an aggregate or derived layer of a graph, a KPI card) is masked by the AND of the filters whose `exclude()` does not name it. A link group is one target, excluded only when every member is. A `by()` panel follows its owner.
- **BR-17.2** Every move rewrites every target from the current values of every widget; the resulting state is a function of the widget values alone (order of moves irrelevant; moving a widget back restores the earlier state).
- **BR-17.3** A KPI in a filter's `exclude()` is recomputed on that filter's moves too, from the filters that do apply to it.
- **BR-17.4** A numeric or date column's dropdown carries numeric values; selection compares numbers as numbers; a missing number is never listed and never selected. An entry that stands for several values (values sharing one display text, Q26) selects every one of them.
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
- **TR-17.4** `_dash_filter_widget` dropdown branch: `raw_values` per TR-17.3; `options = [(sentinel, "All")] + [(rv, str(_label(rv))) for rv in raw_values]` with `rv` now a float or exact text; the sentinel loop unchanged (a float column never holds `"__all__"`); `w._dash_numeric = _dash_filter_numeric(series)`; on a numeric column `w._dash_groups = {rv: (rv,) for rv in raw_values}` (DISCOVERY Q26: a numeric entry's value is its group's FIRST value and the map lists every member; this section ships groups of one, S12 forms groups of the values sharing a display text and lists each group once, with no suffix). The `_label` closure is S12's: this section changes only its fallback line so an unlabelled float reads as today (`str(int(rv))` when `rv.is_integer()` else `str(rv)`), which S12 then replaces with the display-format writer.
- **TR-17.5** `filter_specs_json` (23707-23714) gains `"numeric": bool(getattr(_w, "_dash_numeric", False))` and, for a numeric dropdown, `"groups": [[v, *members] for v, members in _w._dash_groups.items()]` (each inner list opens with the entry's value; this section writes `[[v] for v in raw_values]`). `_dash_dropdown_mask(column, value, groups=None)` decides from `_dash_filter_numeric(column)`: numeric → `want = float(value)` (a `ValueError` or a non-finite `want` → all False), `members = (groups or {}).get(want, (want,))`, `col = _dash_float_values(column, coerce=True)`, `np.isin(col, members)` with NaN never equal; text → `want = str(value)`, each cell mapped as TR-17.3 maps it, `== want`. `_dash_frame_filter_mask` passes `getattr(w, "_dash_groups", None)` and is otherwise unchanged apart from the docstring.
- **TR-17.6** `_DASH_FILTER_MASK_JS` dropdown branch becomes the twin of TR-17.5: `if (spec.numeric) { const want = Number(val); const grp = (spec.groups || []).find(g => g[0] === want); const members = grp || [want]; ... keep row i only when present(col[i]) && Number.isFinite(want) && members.includes(Number(col[i])) } else { const want = String(val); const cell = (col[i] === null || col[i] === undefined) ? "" : String(col[i]); ... cell !== want }` (a `want` or a cell that is NaN never matches). The rule — numbers as numbers, an entry selects every member of its group, text exactly — is written once as a comment block above `dash_filter_mask` and once above `_dash_dropdown_mask`, each naming the other and `test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree` and `::test_two_values_sharing_a_label_select_both`. `dash_filter_mask` gains an optional fourth parameter `use` (an array of widget indices; `undefined` → every widget) for TR-17.9; the CSV button keeps calling it with three.
- **TR-17.7** `_dash_json_value`: `if isinstance(v, str): return v` before the date and float branches. Consequences, named in the docstring: string codes stay text in `_orig_data`, every graph and derived snapshot, and the CSV (`_dash_csv_payload`); `dcount` counts distinct texts; `__dash_mlabel_*` columns keep their text after a move. A date's milliseconds and a number's float are unchanged.
- **TR-17.8** `_apply_colorvar` string path (6527): `strs = ["" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v) for v in raw_col]`. That is this section's only edit inside `_apply_colorvar` (S16 owns the rest and merges after this section; S14 the `_vlookup` lookup; S12 the number-to-text expressions).
- **TR-17.9** Saved wiring (`_build_filter_widgets`): compute, for every target, `use` = the indices into `built_filter_specs` of the filters that apply, through a module-level `_dash_filter_applies(target, exclude, owner_of, members=None)` (True unless `_dash_excluded(target, exclude, owner_of)`; with `members`, True unless every member is excluded). Sources: `all_graph_sources` = every graph source (deduplicated by id) with a non-empty `use`, `graph_use_json` parallel to it; sources with an empty `use` (no filter applies) go in `excluded_sources` and are never written — so `test_every_graph_source_is_filtered_or_protected_not_both` keeps its invariant. A source's `use` is the AND over the graphs that draw from it (`members` = the graph names mapped to that source id, panels resolved through `_owner_of`); a link group's shared source therefore applies a filter unless every member is excluded. `agg_sources`/`agg_use_json` and `derived_sources`/`derived_use_json` likewise (empty `use` → left out). `kpi_config` holds every filter-mode KPI with a `"use"` list (empty → the card is never rewritten); S11 (batch 3) adds `fmt`/`storage` beside it. Every callback receives the same args; `FilterBuilder.build_*` placeholders gain `graph_use_json`, `agg_use_json`, `derived_use_json` as `"[]"`. `view_filters` stays indexed against `all_graph_sources`.
- **TR-17.10** `_FILTER_JS`: a memoised `dash_mask_for(use)` (keyed by `JSON.stringify(use)`) over `dash_filter_mask(orig, filter_specs, all_widgets, use)` and a memoised `dash_ids_for(use)` (the `Set` of row ids the mask keeps); `active`/`_active_ids`/`new_data` stay as the all-widgets mask for the fallback `source`; the graph-source loop reads `dash_ids_for(_graph_use[_si])` (positional fallback `dash_mask_for(...)[i]`); the derived loop reads `dash_ids_for(_derived_use[_di])`; the aggregate block reads its config's `use`; KPIs are grouped by `JSON.stringify(k.use)`, one `_grp_data` built per group from `dash_mask_for(use)`, and `dash_apply_kpis` runs per group. **The KPI marker (TR-17.10; section-11 and `test/test_kpi_brush.py:251` rely on it):** the line `dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);` (14650) is replaced by the per-group loop, and on that line stays the comment `// dash_apply_kpis(new_data, ...) runs once per exclusion group below`; every call inside the loop is written `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`, so the FIRST occurrence of the text `dash_apply_kpis(new_data,` in the script is that comment and the slices in `test/test_kpi_brush.py:251` and the brush wiring (23483-23485) still end where the helper ends; S11 (batch 3) rewrites only the body of `function dash_apply_kpis(` and asserts `index("// ---- KPI recompute, shared by") < index("function dash_apply_kpis(") < index("dash_apply_kpis(new_data,")` in the script text. The identity loop at 14235-14263 keeps its shape (`_kept_ids_by_src`, `vf.filter.booleans = kept.map(...)`).
- **TR-17.11** Served: module-level `_dash_widgets_for(target, widgets, owner_of, members=None)` → `[w for w in widgets if _dash_filter_applies(target, getattr(w, '_dash_exclude', []), owner_of, members)]`. In `_on_filter_change`: drop `excl` and the three `continue`s (26773, 26881, 26948); a per-call cache `_masks: dict[tuple, Series]` keyed by `tuple(id(w) for w in ws)`; `_mask_for(target, members=None)` → `_dash_frame_filter_mask(_df_ref, ws)` cached; the graph loop uses `_mask_for(gname)` (facet branch ANDs onto it), the shared source uses `_mask_for(None, _shared_members)` with `_shared_members` computed once outside the callback as the graph names whose sources include `_shared`; aggregates use `_mask_for(gname)`; KPIs use `_mask_for(kname)`; `_brush_rows` bookkeeping follows each target's frame.
- **TR-17.12** Tests: `test/test_dropdown_values.py` (X1), `test/test_filter_exclusion_sets.py` (E2), the `TestExcludeHoldsWhileItsOwnFilterMoves` rewrite, `scripts/extract_filter_truth.do` → `test/fixtures/filter_truth.json` (with `_meta` per D12; `sections/BRIEF.md` "Fixtures"), the block `* ==== S17 X1 E2: filters vs count and summarize ====` (FT-01..FT-06) of `test/test_gaps2_truth.cscript` and the cases FL-X1-1, FL-E2-1, FL-E2-2 of `test/test_e2e_filters.cscript` (D11; `index.md` R1: only comparisons with Stata's own values go in the truth script; page-only counts join the existing script; no new `.cscript`, no runner edit, no pin change — `test_e2e_filters.cscript` already carries the Python gate at :24-25, so its new Python cases leave `test_cscript_hygiene.py:308` alone).
- **TR-17.13** Copy lists: `_dash_filter_numeric`, `_dash_filter_applies`, `_dash_widgets_for` join the served function list after `"_dash_dropdown_values"` (24627, `index.md` R2 anchor table; `_dash_option_value` 24606, `_dash_dropdown_mask` 24611, `_dash_excluded` 24638, `_dash_json_value` 24551 and `_dash_frame_filter_mask` 24553 are already there); `test/function_test_map.py` names a test for each new function, keys in alphabetical place.
- **TR-17.14** Security: `Select.options` values, `_dash_groups` and `filter_specs_json` are data; nothing from a column value is concatenated into `CustomJS.code`; a text option `__proto__` is listed and selects its rows (the snapshot column loop already uses `dash_own_col`); `spec.groups` is read with `Array.prototype.find` over arrays of numbers, never as an object keyed by user text.
- **TR-17.15** dash.sthlp: this section owns 1109-1138 (consistency #15, DISCOVERY Q26). 17-06 rewrites 1109-1128 (`type(dropdown)` through the slider paragraph) with X1's facts AND S12's sentence — "a listed value is written in the variable's display format, or its value label, values that share one display text are one entry that selects them all, and a `%tw`/`%tm`/`%tq`/`%th`/`%ty` variable's range slider moves over Stata's period numbers in steps of one" — so S12 only verifies the wording after its own merge; 17-15 rewrites 1128-1138 (`exclude()`).

## Boundaries

- **S12 owns dropdown LABELS**: the `_label` closure (17598-17608), `date_text`'s label side (17593-17596), the date-label pin `test_saved_filter_layers.py:1213`, the Stata display format of a listed value, and the FORMING of value groups by display text (`_dash_fmt_text(v, fmt, storage)`; values sharing a label form one group, listed once, no suffixes). **S17 owns VALUES, the grouping mechanism and the masks**: `raw_values`, `_dash_option_value`, `_dash_dropdown_values`, the value side of `Select.options`, `_dash_numeric`, `_dash_groups`, the `numeric` and `groups` keys of `filter_specs_json`, `_dash_dropdown_mask`, `_DASH_FILTER_MASK_JS`, and `_dash_json_value`. Both edit `_dash_filter_widget`'s dropdown branch: this section lands in batch 2, S12 rebases its label change onto the float-valued `rv` and fills `_dash_groups`/`groups` in batch 3.
- **S16 owns `_apply_colorvar`** except line 6527, and merges after this section (`index.md` step 2 merge order).
- **S14** merges after this section and touches `_dash_csv_meta`, `_dash_facet_label` and the saved filter builder at 23598-23603 with one-line `_dash_value_labels_for` lookups beside this section's hunks (consistency #13); do not edit those lines here.
- **S11 (batch 3)** rewrites the body of `dash_apply_kpis` and adds `fmt`/`storage` to `kpi_config` on the tree this section leaves; this section changes the CALL (per group) and the config's `use`, never the function's body (section-11; `test/test_kpi_brush.py:251`).
- **S03 owns `test/js_runner.py`**; this section uses it and does not change it (its pins in `test/test_js_runner.py` are flipped here). If a needed accessor is missing, wrap it in a test-local helper.
- **S05 owns `scripts/extract_stat_truth.do`**; this section writes its own `scripts/extract_filter_truth.do`.
- **C4/E4 stay out**: nothing is ported into `_FILTER_JS` to re-estimate fitted or smoothed layers (PRD §7); the aggregate recount block only takes its target's mask.
- **The served download** (`_dash_csv_payload`) and the saved CSV button keep "every filter applies" (BR-17.9).
- **`_dash_excluded` stays** as the per-graph predicate; `_dash_filter_applies` is layered on it.
- **No change to what a range or slider compares** (numbers already) beyond docstrings.

## Stata truth

**Script:** `scripts/extract_filter_truth.do` → `test/fixtures/filter_truth.json`. Small, on the `extract_axis_truth.do` shape (`global ZA_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"` at its top as `extract_axis_truth.do:85` has, so every path hangs off the global and the script runs through the wrapper directly, `sections/BRIEF.md` "Running one cscript", `index.md` step 0a; a record file; one trailing `python:` block that never calls Stata, backtick as `\x60`). On `sysuse auto`:

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

Each `r(N)` and `r(mean)` written with `%21.17g`. Keys: `all`, `foreign_1`, `price_4000_5000`, `foreign_1_price_4000_5000`, each `{command, count, mean_mpg}`; `data: {mpg: [...], price: [...], foreign: [...]}` (74 entries each, dataset order); `_meta` (D12; `sections/BRIEF.md` "Fixtures") with `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (the do-file captures `git rev-parse HEAD` into a tempfile with `shell`, reads it into a local, and the python block reads it through `Macro.getLocal` — never `shell=True`, never a Stata call from the python block) and `extracted` (the date). Invocation (header comment; the slot wrapper of D6, `index.md` step 0, which takes one of three `mkdir` slots, sets `STATATMP=/tmp/dash-s17/tmp/` with the trailing slash and runs the CLAUDE.md rule 10 console command `arch -arm64 /usr/local/bin/stata-mp -b do`; never the GUI):

```
scripts/stata_slot.sh /tmp/dash-s17 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_filter_truth.do
```

`git add -f test/fixtures/filter_truth.json`; `test/test_filter_exclusion_sets.py` names it and asserts the four `_meta` keys exist (comparing nothing). The X1 and E2 truth-script cases measure their own `count if` and `summarize` live and need no fixture.

## TDD test stubs

New files `test/test_dropdown_values.py` (17-01) and `test/test_filter_exclusion_sets.py` (17-07). `_DF` (ten rows; `foreign==1` keeps 5, `price` in [4000, 5000] keeps 5, both keep 3), `_graph`, `_spec`, `_write_inputs`, `_load_app`, `_served_rows`, `_renderer_source`, `_rows` come from `test_filter_exclude.py`; `_kpi_card`, `_card_value` from `test_help_claims_3.py`; `_fire` from `test_mode_parity`.

Regression tests that fail at `91d97be` (X1, `test/test_dropdown_values.py`):

- Test: `test_a_string_code_keeps_its_exact_text` — `test/test_dropdown_values.py::TestOptionValues::...`: `_dash_option_value("01") == "01"`, `" 2" == " 2"`, `"1.0" == "1.0"`. Pre-fix: `"1"`, `"2"`, `"1"`.
- Test: `test_a_number_is_a_float_and_a_date_its_milliseconds` — `_dash_option_value(1.0) == 1.0`, `_dash_option_value(np.float32(0.1)) == float(np.float32(0.1))`, `_dash_option_value(pd.Timestamp("2001-12-31")) == 1009756800000.0`. Pre-fix: strings.
- Test: `test_nan_none_nat_and_blank_are_listed_on_a_string_column` — `_dash_dropdown_values(pd.Series(["01","1","1.0"," 2","None","nan","NaT","",None]))` lists exactly `["", " 2", "01", "1", "1.0", "NaT", "None", "nan"]` (sorted as `_dash_option_sort_key` sorts). Pre-fix: five entries.
- Test: `test_numeric_missing_is_not_listed` — `pd.Series([3.0, np.nan, 1.0])` → `[1.0, 3.0]`.
- Test: `test_the_numeric_test_is_the_dtype` — `_dash_filter_numeric` on float, datetime, object-of-str and object-of-None columns. Pre-fix: `AttributeError`.
- Test: `test_the_widget_carries_numbers_for_a_numeric_column_and_text_for_a_string_one` — `::TestTheWidget::...` through `_dash_filter_widget("dropdown", ...)`: `[v for v, _ in w.options][1:]` are floats for `foreign`, strings for the codes column; `w._dash_numeric`; `w._dash_groups == {0.0: (0.0,), 1.0: (1.0,)}` for `foreign`; the `filter_specs_json` of a rendered page carries `"numeric"` and `"groups": [[0.0], [1.0]]`. Pre-fix: strings, no attribute.
- Test: `test_the_snapshot_keeps_a_string_column_as_text` — `::TestTheSnapshot::...`: `_dash_json_value("01") == "01"`, `"nan" == "nan"`, `"" == ""`; a rendered page with a string column `s = ["01","1","1.0"]` has `orig_source.data["s"] == ["01","1","1.0"]`. Pre-fix: `1.0, 1.0, 1.0`.
- Test: `test_dcount_and_a_marker_label_survive_a_move` — a `dcount` card on `s` reads "3" after a `JsSession` move of an unrelated range widget (pre-fix "1"), and a `mlabel(s)` layer's label column (`__dash_mlabel_s`) still holds "007" (pre-fix 7).
- Test: `test_node_and_pandas_agree` — `::TestOneRule::...` via S03's `mask_parity(df, filter_specs, widget_values)`: `df` with `s = ['01','1','1.0',' 2','None','nan','NaT','']` and `x = [5e-05, 1e21, float(np.float32(0.1)), np.nan, 1.0, 2.0, 3.0, 4.0]`; for every option value of each column the node mask equals the pandas mask and equals the expected rows (exactly one row per text; for `x`, exactly the rows whose float equals; NaN never). Pre-fix: `s` options merge three rows and `5e-05`/`1e21` keep none under node.
- Test: `test_two_values_sharing_a_label_select_both` — `::TestOneRule::...` (Q26, DISCOVERY Q26): `x = [1.2, 1.4, 2.0]` with the spec `{"varname": "x", "type": "dropdown", "numeric": True, "groups": [[1.2, 1.4], [2.0]]}` (the grouping `%9.0f` would give; written by hand here, formed by S12 later) and the widget value `1.2` keeps rows 0 and 1 under node and pandas and nothing else; `y = [float(np.float32(0.1)), 0.1000000015, 0.5]` with `groups: [[float(np.float32(0.1)), 0.1000000015], [0.5]]` (the `%9.0g` pair) and the value `float(np.float32(0.1))` keeps rows 0 and 1; the served `_dash_dropdown_mask(column, value, groups={1.2: (1.2, 1.4)})` agrees. Pre-fix: `AttributeError`/`TypeError` (no `groups` argument; the JS branch compares strings).
- Test: `test_both_modes_select_the_same_rows` — `::TestBothModes::...` saved via `JsSession`, served via `_fire`, on `s` = "01" (1 row), "nan" (1 row), "" (1 row) and `x` = 5e-05, 1e21. Pre-fix: saved keeps 0 for 5e-05.
- Test: `test_colorvar_reads_the_text_nan_as_a_category` — `::TestColorvarStrings::...`: `_apply_colorvar` on `["nan", "a", None, ""]` gives factors `["a", "nan", "__missing__"]`. Pre-fix: `["a", "__missing__"]`.
- Test: `test_a_hostile_text_value_is_data` — `::TestHostileValues::...`: `s = ["__proto__", "<script>", "a\"b"]`: all three listed, each selects its row under node and pandas, none appears inside any `CustomJS.code`.

Regression tests that fail after the X1 commit (E2, `test/test_filter_exclusion_sets.py`; the E2 symptom is untouched by X1):

- Test: `test_saved_state_depends_only_on_the_widgets` — `test/test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved_state_depends_only_on_the_widgets`, the `TestExcludeHoldsWhileItsOwnFilterMoves` SPEC (foreign dropdown; price range with `exclude(g1 k1)`; k1 counts mpg) through `JsSession`: price → (4000, 5000) gives `{g1:10, g2:5, k1:"10"}`; foreign → 1.0 gives `{g1:5, g2:3, k1:"5"}`; price → (start, end) gives `{g1:5, g2:5, k1:"5"}`; foreign → sentinel gives `{g1:10, g2:10, k1:"10"}`. Pre-fix: the second state is `{3,3,"3"}` and the third `{3,5,"3"}`.
- Test: `test_served_state_depends_only_on_the_widgets` — the same four states through chained `tp._fire`.
- Test: `test_the_order_of_moves_does_not_matter` — `::TestTheOrderOfMoves::...`: foreign first then price reaches the same second state, both modes.
- Test: `test_an_excluded_kpi_is_recomputed_by_the_filters_that_apply_to_it` — `::TestAnExcludedKpi::...`: `TestAKpiCardCanBeExcluded`'s SPEC plus a foreign dropdown: moving foreign after price gives k1 "5" (foreign applies), k2 "3". Pre-fix: k1 "10".
- Test: `test_a_link_group_is_one_target` — `::TestALinkGroupIsOneTarget::...`: `link(g1 g2)`, `exclude(g1)`, a second filter: after both move, g1 == g2 == the rows the non-excluding filter set keeps for the GROUP (both filters, since g2 is not excluded); with `exclude(g1 g2)`, neither filter touches the group. Both modes.
- Test: `test_a_by_panel_follows_its_owner_across_moves` — `::TestAByPanelFollowsItsOwner::...`: `by(foreign)` graph excluded from one filter, two moves, both modes.
- Test: `test_an_aggregate_and_a_derived_layer_take_their_targets_mask` — `::TestAggregateAndDerivedLayers::...`: a `histogram` layer and a `line` (derived, sorted copy) on g1 excluded from price, two moves: their sources hold the foreign-only rows, not the intersection. Both modes. Pre-fix: the intersection.
- Test: `test_auto_matches_stata` — `::TestAutoAgainstStata::...` from `filter_truth.json`'s `data`: g1 (`exclude(price)`), g2, k1 `count mpg` (`exclude(price)`), k2 `count mpg`; foreign → 1.0 then price → (4000, 5000): k1 == `foreign_1.count`, k2 == `foreign_1_price_4000_5000.count`, `mean(g1 source mpg)` == `foreign_1.mean_mpg` and `mean(g2 source mpg)` == `foreign_1_price_4000_5000.mean_mpg` at rtol 1e-9, both modes. Missing fixture → `pytest.fail("section 17 task 17-08 must land first: test/fixtures/filter_truth.json is missing")`.
- Test: `test_the_fixture_meta_carries_the_four_provenance_keys` — `::TestAutoAgainstStata::...`: `_meta` holds `stata_version`, `born_date`, `dash_commit`, `extracted` (D12); nothing compares them. Pre-fix: the "must land first" failure.
- Test: `test_every_source_is_filtered_or_protected_and_use_is_recorded` — `::TestTheCallbackArgs::...`: for the specs of `test_filter_exclude.py::TestTheCallbackKnowsWhatItProtects`, `graph_use_json` is parallel to `all_graph_sources`, every listed source has a non-empty `use`, every `excluded_sources` entry has none, and the `use` lists are the same in every callback. Pre-fix: `KeyError: 'graph_use_json'`.
- Test: `test_the_kpi_marker_is_kept_once_before_the_loop` — `::TestTheCallbackArgs::...` (TR-17.10; section-11 and `test/test_kpi_brush.py:251` rely on it): in `dash_render._FILTER_JS`, `index("// ---- KPI recompute, shared by") < index("function dash_apply_kpis(") < index("dash_apply_kpis(new_data,")`, the text at the last index is the comment `// dash_apply_kpis(new_data, ...) runs once per exclusion group below`, and every other call reads `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`. Pre-fix: the single call, no comment.
- Test: `test_filter_applies_and_widgets_for` — `::TestTheHelpers::...`: unit tests of `_dash_filter_applies` (graph, panel through owner, group with one/all members excluded) and `_dash_widgets_for`. Pre-fix: `AttributeError`.

Pinned tests to flip (in the fix commits): `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` → rewritten as `TestAnExclusionHoldsAgainstEveryMove` delegating to the sequences above (17-13); the `"1"` → `1.0` values in `test_help_claims_3.py` (17-13) and `test_filter_exclude.py` (17-03); `_script_args` and `TestThePrimarySourceFallback` shapes (17-03, 17-11); `test_saved_filter_layers.py::TestTheOptionValueOfADate` (17-02); `test_export.py` comment 199-201 and a `0.0` case (17-03); `test/function_test_map.py` entries (17-02, 17-09); S03's `test_js_runner.py` pins (17-04 for X1, 17-10 for E2).

**Mutation table:**

| break this | test that must die |
|---|---|
| `_dash_option_value`: restore `str(int(f))` | `test_a_string_code_keeps_its_exact_text` |
| `_dash_dropdown_values`: restore the `("nan","None","NaT")` filter | `test_nan_none_nat_and_blank_are_listed_on_a_string_column` |
| `_dash_json_value`: drop the `isinstance(v, str)` branch | `test_the_snapshot_keeps_a_string_column_as_text` |
| JS: compare `String(col[i]) !== String(val)` on a numeric spec | `test_node_and_pandas_agree[x=5e-05]` |
| pandas: compare `str` on a numeric column | `test_node_and_pandas_agree[x=5e-05]` |
| JS: ignore `spec.groups` (`members = [want]` always) | `test_two_values_sharing_a_label_select_both` |
| `_FILTER_JS`: KPI groups all use `active` | `test_an_excluded_kpi_is_recomputed_by_the_filters_that_apply_to_it[saved]` |
| `_FILTER_JS`: drop the marker comment | `test_the_kpi_marker_is_kept_once_before_the_loop` and `test_kpi_brush.py` |
| `_FILTER_JS`: derived loop keeps `_active_ids` | `test_an_aggregate_and_a_derived_layer_take_their_targets_mask[saved]` |
| served: keep `excl` and `continue` in the KPI loop | `test_served_state_depends_only_on_the_widgets` |
| `_dash_filter_applies`: `any(...)` instead of `all(...)` for members | `test_a_link_group_is_one_target` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| option values, listing, numeric test, snapshot text | pytest unit | none | n/a (shared functions) |
| one matching rule, node vs pandas; a two-value group | pytest via `mask_parity` (node) | none | yes (the two masks) |
| rows selected for '01', 'nan', '', 5e-05, 1e21 | pytest `JsSession` + `_fire` | none | yes |
| dcount / marker label after a move | pytest `JsSession` | none | saved (the served app never coerced) |
| string codes and doubles from a Stata dataset vs `count if` | block `* ==== S17 X1 E2: … ====` of `test/test_gaps2_truth.cscript`, FT-01..FT-03 | live `count if` | yes |
| option lists and saved == served page counts | `test/test_e2e_filters.cscript` FL-X1-1 | none | yes |
| multi-move sequences per target kind | pytest `JsSession` + chained `_fire` | none | yes |
| counts and means on auto | pytest | `filter_truth.json` | yes |
| fixture provenance stamp (D12) | pytest `TestAutoAgainstStata` | `filter_truth.json` `_meta` | n/a |
| auto after two moves vs `count if`/`summarize` live | truth-script block FT-04..FT-06 | live | yes |
| the four-state sequence's page counts | `test/test_e2e_filters.cscript` FL-E2-1, FL-E2-2 | none | yes |
| callback args shape and the KPI marker | pytest | none | saved |
| parity corpus | `test_mode_parity` (existing dropdown/exclude cases) | its own | yes |
| security: hostile text values | pytest + FT-03 | none | yes |

Acceptance criteria:
- **AC-17.1** The four-state sequence of `test_saved_state_depends_only_on_the_widgets` holds in both modes, and reversing the order of moves reaches the same states.
- **AC-17.2** An excluded KPI, an excluded link-group member, a `by()` panel, an aggregate layer and a derived layer each show the rows their own filter set keeps after two moves, in both modes.
- **AC-17.3** On auto, after foreign → 1 and price → [4000, 5000], the excluded graph and card equal Stata's `foreign==1` count and mean of mpg, the others Stata's intersection.
- **AC-17.4** `mask_parity` over the hostile columns gives equal node and pandas masks and the expected rows for every option, and a two-value group selects both members.
- **AC-17.5** From Stata, `fips == "01"`, `"1"`, `"1.0"`, `"None"`, `"nan"` and `""` each keep exactly `count if fips == "<text>"` rows in both modes; a double 5e-05 keeps `count if tiny == 5e-05` rows.
- **AC-17.6** A `dcount` card and a marker label read the same before and after a move on the saved page.
- **AC-17.7** The full pytest suite is green with no skips before each of the two commits; `test_function_test_map.py`, the two served-name guards and `test_cscript_hygiene.py` (pins untouched) pass; the S17 block of `test/test_gaps2_truth.cscript` and the new `test_e2e_filters.cscript` cases pass through their driver do-files.

## Tasks

Commit boundary: **two commits, X1 then E2**, both on the worktree branch `wp28-s17` (`index.md` step 1). The **X1 commit** holds 17-01 to 17-06, subject ending `(GAPS2 X1)`, body per S01 TR-01.9 opening with `<scratch>/17-01-failure.txt`; the **E2 commit** holds 17-07 to 17-15, subject ending `(GAPS2 E2)`, body opening with `<scratch>/17-07-failure.txt`. The full pytest suite runs green once in the worktree before each commit (CLAUDE.md rules 4 and 11; two full runs in this section, one per gap); the merger lands the two commits on `s3-bugs` in that order. Every Stata run goes through `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6, `index.md` step 0); a cscript through its driver do-file (`sections/BRIEF.md` "Running one cscript", `index.md` step 0a). No AI references anywhere.

<task type="auto" id="17-01">
  <name>Write the failing X1 tests</name>
  <files>test/test_dropdown_values.py</files>
  <action><![CDATA[
    Create `test/test_dropdown_values.py`. Write only tests; no production change. Module docstring with X1's measured symptoms (the '01'/'1'/'1.0' merge, 'nan'/'None'/'NaT' unlisted, 5e-05 and 1e21 unselectable on the saved page, the "007" → 7 snapshot); header as `test_filter_exclude.py:31-52` plus `from js_runner import JsSession, mask_parity` (S03) and `import test_filter_exclude as tfe`, `import test_mode_parity as tp`. Classes `TestOptionValues`, `TestTheWidget`, `TestTheSnapshot`, `TestOneRule`, `TestBothModes`, `TestColorvarStrings` (the `_apply_colorvar` string test through `test_function_audit.py`'s `_bins` pattern with a string column), `TestHostileValues`, with exactly the test names of the X1 stubs, `test_two_values_sharing_a_label_select_both` included (its `filter_specs` carry the `groups` lists by hand and its docstring names Q26 and the two formats). Build frames with a string column `s` and a float column `x` as the stubs list them; write the spec through `tfe._spec`/`tfe._graph` with `filters` on `s` and on `x`; for the dcount/mlabel test add a `kpis` entry `{"stat": "dcount", "var": "s", ...}` (`_kpi_card` shape) and a `mlabel(s)` scatter, move a `range` on `x` through `JsSession`, read the card through `_card_value` and the `__dash_mlabel_s` column from the session state. Run the file on the unmodified tree. Do not commit: save the summary to `<scratch>/17-01-failure.txt` (the merged `'1'` values, the five-entry list and the empty 5e-05 selection are the CHANGELOG line's old values, Q24); it opens the X1 commit's body (S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_dropdown_values.py -q 2>&1 | tail -25` collects cleanly; `test_a_string_code_keeps_its_exact_text` fails showing `'1'`, `test_the_numeric_test_is_the_dtype` fails with `AttributeError`, `test_two_values_sharing_a_label_select_both` fails, and no regression stub passes; `<scratch>/17-01-failure.txt` exists; `git status --short` shows only the new file.]]></verify>
  <done>The X1 test file existed, collected, and every regression test in it failed on the unmodified tree for the reason its stub names, with nothing committed.</done>
</task>

<task type="auto" id="17-02">
  <name>Carry exact text and numeric values through Python</name>
  <files>dash_render.py, test/function_test_map.py, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
    In `dash_render.py`: add `_dash_filter_numeric(column)` beside `_dash_filter_rangeable` (17530) and use it at 1838-1839; rewrite `_dash_option_value` (17413-17441) per TR-17.2 with a new docstring; rewrite `_dash_dropdown_values` (1806-1812) per TR-17.3; in `_dash_filter_widget`'s dropdown branch set `w._dash_numeric = _dash_filter_numeric(series)` and, on a numeric column, `w._dash_groups = {rv: (rv,) for rv in raw_values}` after 17619 (TR-17.4, DISCOVERY Q26), and change only the fallback line of `_label` (17608) so an unlabelled float reads as today (`str(int(rv))` if `float(rv).is_integer()` else `str(rv)`) — leave every other line of `_label` and `date_text` to S12; rewrite `_dash_dropdown_mask(column, value, groups=None)` (17669-17675) per TR-17.5 with the shared-rule comment block naming `_DASH_FILTER_MASK_JS` and the two parity tests; make `_dash_frame_filter_mask` pass `getattr(w, "_dash_groups", None)`; add `"numeric"` and `"groups"` to `_filter_specs` (23707-23714); add the `isinstance(v, str)` branch to `_dash_json_value` (13840) with the docstring naming `_dash_csv_payload`, the snapshots, `dcount` and the `__dash_mlabel_*` labels; change line 6527 per TR-17.8 and nothing else in `_apply_colorvar`; add `_dash_filter_numeric` to the served function list after `"_dash_dropdown_values"` (24627, `index.md` R2 anchor table). `_dash_frame_filter_mask`'s docstring (13950-13961) is corrected. `test/function_test_map.py`: add `'_dash_filter_numeric': 'test/test_dropdown_values.py::TestOptionValues::test_the_numeric_test_is_the_dtype'` in alphabetical place; re-point `_dash_option_value` (443), `_dash_dropdown_mask` (318), `_dash_dropdown_values` and `_dash_json_value` (365) at the new tests if `fncov_mutate.py --map` shows the old ones no longer die. `test/test_saved_filter_layers.py::TestTheOptionValueOfADate` (1219-1245): milliseconds become `1009756800000.0` (a float; 1225, 1229) and `float(int(v.astype(np.int64)))` at 1234; `_dash_option_value(1.0) == 1.0` at 1244; the class docstring says values are floats. Do not touch 1213.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dropdown_values.py -q -k "OptionValues or TheWidget or TheSnapshot or Colorvar" 2>&1 | tail -3` passes; `python3 -m pytest test/test_saved_filter_layers.py test/test_export.py test/test_resource_limits.py test/test_label_sinks.py test/test_function_test_map.py -q 2>&1 | tail -3` passes; `python3 -m pytest test/test_statistical_helpers.py -q -k CarriesEveryName test/test_resource_limits.py -q -k DefinesEveryName` passes.]]></verify>
  <done>A dropdown carried floats and groups of one for a numeric column and exact text for a string one, the served mask compared by the column's kind and by group membership, every snapshot and the CSV kept strings as text, and the colorvar string path read 'nan' as a category.</done>
</task>

<task type="auto" id="17-03">
  <name>Make the saved mask the served one's twin</name>
  <files>dash_render.py, test/test_filter_exclude.py, test/test_export.py</files>
  <action><![CDATA[
    `dash_render.py` `_DASH_FILTER_MASK_JS` (14110-14164): rewrite the dropdown branch per TR-17.6 (the `spec.numeric` branch with `spec.groups` and `members.includes(Number(col[i]))`, the text branch comparing exactly) and add the optional `use` parameter (`const idx = (use === undefined || use === null) ? [...Array(filter_specs.length).keys()] : use;` and loop over `idx`); write the rule comment block above `dash_filter_mask` naming `_dash_dropdown_mask`, `test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree` and `::test_two_values_sharing_a_label_select_both`. `_DASH_CSV_SAVED_JS` is unchanged (three-argument call). `test/test_filter_exclude.py`: `_MOVES["dropdown"]` value `"1"` → `1.0`; `_script_args` (434-455): `Select(value=1.0, options=[("__all__", "All"), (0.0, "0"), (1.0, "1")])`, the spec gains `"numeric": True` and `"groups": [[0.0], [1.0]]`. `test/test_export.py`: correct the comment at 199-201 (the snapshot now holds "007" as text) and add `W("foreign", "dropdown", 0.0)` to `test_frame_filter_mask` beside the `"0"` case. Do not touch `test/test_js_runner.py` here (17-04 flips its X1 pin).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dropdown_values.py -q 2>&1 | tail -3` passes in full (parity, the two-value group, both modes, hostile); `python3 -m pytest test/test_filter_exclude.py test/test_export.py test/test_linking_filters.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_mode_parity.py -q -k "dropdown or filter or exclude or Select" 2>&1 | tail -3` passes; `python3 -m pytest test/test_js_runner.py -q -k small_number 2>&1 | tail -2` now FAILS (the twins agree; 17-04 flips the pin).]]></verify>
  <done>Node and pandas kept the same rows for every hostile column, option and two-value group, the saved page selected 5e-05 and 1e21, and the tests that set a dropdown by string carried the widget's real value.</done>
</task>

<task type="auto" id="17-04">
  <name>Flip the S03 X1 parity pin</name>
  <files>test/test_js_runner.py</files>
  <action><![CDATA[
    In `test/test_js_runner.py` (S03's file; only this pin is touched here) flip `TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1` to assert the twins now agree on 5e-05 and 1e21 and rename it `test_a_dropdown_on_a_small_number_agrees_since_x1`, keeping the docstring's history (what was measured at 91d97be and that this section flipped it). Leave `TestASessionMeasuresE2` and `TestASessionCarriesState` as they are (17-10, the E2 commit). Record the flip for the X1 commit body as `Flipped: test/test_js_runner.py::TestMaskParity::test_a_dropdown_on_a_small_number_disagrees_today_x1 -- the disagreement was the X1 defect`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -3` passes in full; `grep -c 'agrees_since_x1' test/test_js_runner.py` prints 1.]]></verify>
  <done>S03's X1 measurement pin asserted the twins' agreement under its new name, inside the X1 commit.</done>
</task>

<task type="auto" id="17-05">
  <name>Certify X1 against Stata's count</name>
  <files>test/test_gaps2_truth.cscript, test/test_e2e_filters.cscript</files>
  <action><![CDATA[
    Insert into `test/test_gaps2_truth.cscript` (S02 created and registered it as runner block `// 67.`; it opens with the standard Python gate, loads `cert_helpers.do` and `cert_svg.do` and ends with the line `* ==== append new blocks above this line ====`), above that last line and after the blocks of lower-numbered sections (R1), a block of the block form of `sections/BRIEF.md` "Certification scripts": `* ==== S17 X1 E2: filters vs count and summarize ====`, `local only : env GAPS2_ONLY`, `if inlist("`only'", "", "S17") {`, `display as text "S17 start `c(current_time)'"`, the cases, `display as text "S17 end `c(current_time)'"`, `}`, `* ==== end S17 ====` — opened here with FT-01..FT-03 (17-14 adds FT-04..FT-06 before the `S17 end` line). Data: `clear; set obs 12; gen str fips = string(_n, "%02.0f"); replace fips = "1" in 3; replace fips = "1.0" in 4; replace fips = "None" in 5; replace fips = "nan" in 6; replace fips = "" in 7; replace fips = "__proto__" in 8; gen double tiny = 5e-05; replace tiny = 1e21 in 4/6; replace tiny = 0.1 in 7/12; gen float f32 = 0.1; gen y = _n; gen x = _n`. FT-01: for each text in `01 1 1.0 None nan ""` compute `count if fips == "<text>"` into a local; register `dash scatter y x, name(g1)` and call `_dash_serve_spec, specpath("`s'") datapath("`d'") filter(fips, type(dropdown)) filter(tiny, type(dropdown)) filter(f32, type(dropdown))` (if `_dash_serve_spec` refuses a filter() written after its own options, put the filters where `test_help_claims_5.cscript:588` puts them); a `python:` block (`sys.path.insert(0, "<repo>")` and `"<repo>/test"`; `import dash_render`; `from js_runner import JsSession`) renders `DashRenderer(s, d, out)`, sets each `fips` option through `JsSession` and counts g1's rows, builds `ServerAppBuilder(s, d).build(app)`, loads the app with the `_load_app` recipe (exec with the curdoc attach replaced), `make_document(doc)`, sets `Select.value` and fires its `value` callbacks (as `test_filter_exclude._served` does), counting rows; write each count to `st_global` and assert in Stata that saved == served == the `count if` local for every text. FT-02: the same for `count if tiny == 5e-05`, `count if tiny == 1e21` and `count if f32 == float(0.1)`. FT-03: `__proto__` is listed, selects exactly `count if fips == "__proto__"` rows in both modes, and the text appears in no `CustomJS.code`. Each case displays `FT-0n PASS` or `FT-0n FAIL: <why>` and never `exit`s. In `test/test_e2e_filters.cscript` (it already gates on `c(python_exec)` at :24-25 and loads `cert_helpers.do` at :39, so the `:308` pin is untouched) add, before its final `All filter widget E2E tests PASSED.` line, case FL-X1-1 on the same constructed data: the three dropdowns' option lists contain `"None"`, `"nan"` and `""` and every option keeps the same row count saved and served (page-only checks: no Stata value is compared here), displaying `FL-X1-1 PASS: ...` in the file's style. Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11). Run the S17 block alone through the driver of `sections/BRIEF.md` "Running one cscript", `index.md` step 0a: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_gaps2_truth.cscript > /tmp/dash-s17/run_test_gaps2_truth.do` then `GAPS2_ONLY=S17 scripts/stata_slot.sh /tmp/dash-s17 /tmp/dash-s17/run_test_gaps2_truth.do`, and `test_e2e_filters.cscript` through its own driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_e2e_filters.cscript > /tmp/dash-s17/run_test_e2e_filters.do` then `scripts/stata_slot.sh /tmp/dash-s17 /tmp/dash-s17/run_test_e2e_filters.do`); a `python:` SKIP is a failure to investigate (`c(python_exec)`), and node must be installed (`JsSession` fails loudly, never skips).
  ]]></action>
  <verify><![CDATA[`grep -c '^\* ==== S17 X1 E2: filters vs count and summarize ====' test/test_gaps2_truth.cscript` prints 1 and `grep -c '^\* ==== end S17 ====' test/test_gaps2_truth.cscript` prints 1, the block sitting above `* ==== append new blocks above this line ====`; `/tmp/dash-s17/run_test_gaps2_truth.log` shows `S17 start`, `FT-01 PASS`, `FT-02 PASS`, `FT-03 PASS` and `S17 end` with `grep -c '^r([0-9]*);' /tmp/dash-s17/run_test_gaps2_truth.log` printing 0; `/tmp/dash-s17/run_test_e2e_filters.log` shows `FL-X1-1 PASS` and its final PASSED line with `grep -c '^r([0-9]*);' /tmp/dash-s17/run_test_e2e_filters.log` printing 0; `git diff --stat test/run_all_cscripts.do test/test_cscript_hygiene.py` prints nothing.]]></verify>
  <done>From Stata's own data and `count if`, both modes kept exactly the rows a string or double dropdown value names and listed every category including 'None', 'nan' and the blank, proved in the shared truth script and the existing e2e script.</done>
</task>

<task type="auto" id="17-06">
  <name>Close X1 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    `dash.sthlp` 1109-1128 (`type(dropdown)` through the slider paragraph; this section owns 1109-1138, consistency #15): "select widget listing every distinct value of varname: a numeric or date variable's values as numbers (a missing value is not listed), a string variable's exact text, its empty string as a blank row. Selecting a value keeps the observations equal to it — a number compared as a number, a text compared exactly, so '01' and '1' are two values — in the saved page and the served app alike. A listed value is written in the variable's display format, or its value label; values that share one display text are one entry that selects them all; and a %tw, %tm, %tq, %th or %ty variable's range slider moves over Stata's period numbers in steps of one." (the last sentence is S12's, written here so S12 only verifies it), keeping the limit sentence. `CHANGELOG.md`: replace in place the marker `<!-- WP-28 X1 -->` that S01 put in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list (CHANGELOG.md:10; D2, `index.md` R3, section-01 TR-01.7) with ONE line ending `(WP-28, X1)` naming the command, the old value as `<scratch>/17-01-failure.txt` recorded it (Q24) and the new one: a `filter(varname, type(dropdown))` on a string variable rewrote '01', '1.0' and ' 2' to '1' and '2' and merged their rows, dropped the categories 'None', 'nan' and 'NaT', and on the saved page could not select a number below 1e-4 or at or above 1e21; the saved page's snapshot and the CSV download turned a string code into a number after a move (a marker label '007' read 7; a dcount of codes merged them); now numbers are compared as numbers and text exactly, every category is listed, values sharing one display text are one entry, and snapshots and the CSV keep text, in both modes; add nothing anywhere else in the file. `BUGS.md`: append at the end of the file (S01 TR-01.8; never mid-file) one closed entry `- [x] Title: A dropdown rewrites string codes to numbers, drops the categories nan None and NaT, and cannot select small numbers on the saved page` (no `"` in the title) with File Names and Line Numbers (`dash_render.py: _dash_option_value, _dash_dropdown_values, _dash_filter_widget, _dash_dropdown_mask, _DASH_FILTER_MASK_JS, _dash_json_value`), Description (the GAPS2 X1 symptom, cited), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, X1). A numeric column's dropdown carries floats (each entry the first value of a group that selects every member), a string column's exact text with the blank listed, both masks compare numbers as numbers and text exactly, and _dash_json_value keeps strings as text in every snapshot and the CSV, in both renderers. Pinned by test/test_dropdown_values.py::TestOneRule::test_node_and_pandas_agree, ::TestOneRule::test_two_values_sharing_a_label_select_both, ::TestTheSnapshot::test_the_snapshot_keeps_a_string_column_as_text, ::TestBothModes::test_both_modes_select_the_same_rows, test/test_gaps2_truth.cscript FT-01..FT-03.` — exactly once each field, in order. Grep the three files for `claude|anthropic`. Run the full suite once in the worktree (`python3 -m pytest test/ -q`; the X1 run), then the S17 block and `test_e2e_filters.cscript` through the drivers of 17-05; commit 17-01 to 17-06 as ONE commit on the worktree branch `wp28-s17`, subject ending `(GAPS2 X1)`, body opening with `<scratch>/17-01-failure.txt` and carrying the `Regression:` / `Flipped:` (17-02, 17-03, 17-04 flips) / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (`index.md` step 1, `index.md` step 1).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips; `python3 -m pytest test/test_tracking_documents.py -q` passes; `grep -c '<!-- WP-28 X1 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, X1)' CHANGELOG.md BUGS.md` prints 2; `grep -c 'share one display text' dash.sthlp` prints 1; `git log -1 --format=%s | grep -c '(GAPS2 X1)'` prints 1 and `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>X1 was closed in BUGS.md naming its regression tests, dash.sthlp stated the value and matching rules with S12's sentence, the X1 CHANGELOG marker was replaced, and one green commit on the worktree branch `wp28-s17` carried the X1 group for the merger.</done>
</task>

<task type="auto" id="17-07">
  <name>Write the failing E2 tests</name>
  <files>test/test_filter_exclusion_sets.py</files>
  <action><![CDATA[
    Create `test/test_filter_exclusion_sets.py` on the tree the X1 commit leaves (the E2 symptom is unchanged by X1). Docstring with E2's measured sequence (g1=3, g2=5, k1=3 where 5 is implied); classes `TestAnExclusionHoldsAgainstEveryMove`, `TestTheOrderOfMoves`, `TestAnExcludedKpi`, `TestALinkGroupIsOneTarget`, `TestAByPanelFollowsItsOwner`, `TestAggregateAndDerivedLayers`, `TestAutoAgainstStata`, `TestTheCallbackArgs`, `TestTheHelpers`, with exactly the test names of the E2 stubs (`test_the_kpi_marker_is_kept_once_before_the_loop` and `test_the_fixture_meta_carries_the_four_provenance_keys` included). Saved sequences: render, build `JsSession` from every callback's args (all callbacks share the same models), then alternate `.set(widget, value)` / `.run(callback_of_that_widget)` / read the state through one local `_rows_and_cards(session, r)` that maps `session.rows(tfe._renderer_source(fig))` to figure titles and `session.state()["divs"][div.id]` through `_card_value` to card names. Served sequences: chained `tp._fire`. Widget values are the real ones: `1.0` for foreign, the sentinel (`w._dash_sentinel`) for "All", `(w.start, w.end)` for a range at rest. `TestAutoAgainstStata` reads `test/fixtures/filter_truth.json` through a `_truth()` that `pytest.fail`s when the file is missing. Run the file. Do not commit: save the summary to `<scratch>/17-07-failure.txt` (the `{'g1': 3, 'g2': 3, 'k1': '3'}` and `{3, 5, '3'}` states are the CHANGELOG line's old values, Q24); it opens the E2 commit's body.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_filter_exclusion_sets.py -q 2>&1 | tail -25` collects cleanly; `test_saved_state_depends_only_on_the_widgets` fails showing `{'g1': 3, 'g2': 3, 'k1': '3'}`, the helper and args tests fail with `AttributeError`/`KeyError`, the fixture tests with the "must land first" message, and no test passes; `<scratch>/17-07-failure.txt` exists; `git status --short` shows only the new file.]]></verify>
  <done>The E2 test file existed, collected, and every test in it failed on the post-X1 tree for the reason its stub names, with nothing committed.</done>
</task>

<task type="auto" id="17-08">
  <name>Measure the auto filter truth in Stata</name>
  <files>scripts/extract_filter_truth.do, test/fixtures/filter_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_filter_truth.do` as the "Stata truth" section specifies: `global ZA_REPO` at its top, `sysuse auto`, the eight commands, each `r(N)`/`r(mean)` written to a record file with `%21.17g`, the three columns written one line per observation, the provenance capture (D12; `sections/BRIEF.md` "Fixtures": `local stata_version = c(stata_version)`, `local born_date = c(born_date)`, `tempfile gh` then `shell git -C "${ZA_REPO}" rev-parse HEAD > "`gh'"` and `file read` it into `local dash_commit`), and a trailing `python:` block (never calling Stata; the locals read through `Macro.getLocal`; backtick as `\x60`) writing `test/fixtures/filter_truth.json` with keys `all`, `foreign_1`, `price_4000_5000`, `foreign_1_price_4000_5000`, `data`, `_meta` (`stata_version`, `born_date`, `dash_commit`, `extracted`). Run it through the wrapper: `scripts/stata_slot.sh /tmp/dash-s17 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_filter_truth.do` (D6; the script sets its own directories, `sections/BRIEF.md` "Running one cscript", `index.md` step 0a). `git add -f test/fixtures/filter_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/filter_truth.json'));print(d['all']['count'], d['foreign_1']['count'], len(d['data']['price']), sorted(k for k in d['_meta'] if k in ('stata_version','born_date','dash_commit','extracted')))"` prints `74 22 74 ['born_date', 'dash_commit', 'extracted', 'stata_version']`; `grep -c '^r([0-9]*);' /tmp/dash-s17/extract_filter_truth.log` prints 0; `python3 -m pytest test/test_fixtures_are_committed.py test/test_filter_exclusion_sets.py -q -k "committed or provenance"` passes.]]></verify>
  <done>Stata's counts and means for the four filter states on auto, with the columns they were measured on and the four-key `_meta` stamp, were committed as a fixture a test names.</done>
</task>

<task type="auto" id="17-09">
  <name>Mask each served target by its filters</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add module-level `_dash_filter_applies(target, exclude, owner_of, members=None)` and `_dash_widgets_for(target, widgets, owner_of, members=None)` beside `_dash_excluded` (17975), docstrings quoting BR-17.1 and dash.sthlp's link-group sentence; add both to the served function list after `"_dash_dropdown_values"` (`index.md` R2 anchor table) and to `test/function_test_map.py` (naming `test/test_filter_exclusion_sets.py::TestTheHelpers::test_filter_applies_and_widgets_for`, keys in alphabetical place). Served template: outside `_make_filter_cb`, compute `_shared_members = [g for g, s in graph_sources.items() if any(x is shared_source for x in (s if isinstance(s, list) else [s]))]` and pass it as a new keyword `_members=`. Inside `_on_filter_change` implement TR-17.11: delete `excl` (26768) and the three `continue`s (26773-26774, 26881-26882, 26948-26949); add `_masks = {}` and `_mask_for(target, members=None)`; the graph loop starts each `gname` with `mask = _mask_for(gname)` and `fdf = _df_ref[mask]` (the shared-source hit uses `_mask_for(None, _members)` for the group's write at 26870-26877 and its `_brush_rows` line); the facet branch ANDs onto that target's `mask`; the aggregate loop uses `_mask_for(gname)`; the KPI loop uses `_k_fdf` from `_mask_for(kname)`. Keep every other line — the qualifier re-application, `_dash_refresh_unlinked`, `_dash_refresh_linked`, the redraw and the throttle — as it is.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py -q -k "served or Helpers" 2>&1 | tail -3` passes; `python3 -m pytest test/test_filter_exclude.py test/test_help_claims_3.py test/test_linking_filters.py test/test_saved_filter_layers.py -q -k "served or Served" 2>&1 | tail -3` passes except `TestExcludeHoldsWhileItsOwnFilterMoves::test_served`, which now fails with `{'g1': 5, 'g2': 3, 'k1': '5'}` (17-13 rewrites it); the served-name guards and `test_function_test_map.py` pass.]]></verify>
  <done>The served app recomputed every graph, group, aggregate and card from the filters that apply to it on every move, cached per exclusion set, so its state depended only on the widgets.</done>
</task>

<task type="auto" id="17-10">
  <name>Flip the S03 E2 measurement pins</name>
  <files>test/test_js_runner.py</files>
  <action><![CDATA[
    In `test/test_js_runner.py` (S03's file) flip `TestASessionMeasuresE2::test_three_moves_leave_the_saved_page_where_measured` to the widget-implied `{"g1": 5, "g2": 5, "k1": "5"}` its docstring already states (keep the measured `{3, 5, "3"}` in the docstring as history), and set the foreign dropdown to `1.0` in `TestASessionCarriesState::test_two_moves_chain_on_one_session` (the real value type since X1). The first flip stays red until 17-13 lands; both flips are inside the one E2 commit, so no committed tree is red. Record them for the E2 commit body as `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_js_runner.py -q 2>&1 | tail -3` shows exactly one failure, `test_three_moves_leave_the_saved_page_where_measured`, reporting `{'g1': 3, 'g2': 5, 'k1': '3'}` against the expected `{'g1': 5, 'g2': 5, 'k1': '5'}`.]]></verify>
  <done>S03's E2 measurement pin asserted the widget-implied state (red until the saved wiring of 17-13, inside the E2 commit) and the chained-move test carried the real dropdown value.</done>
</task>

<task type="auto" id="17-11">
  <name>Compute per-target use lists in the saved wiring</name>
  <files>dash_render.py, test/test_filter_exclude.py</files>
  <action><![CDATA[
    In `_build_filter_widgets` implement TR-17.9: compute `use` per target once through `_dash_filter_applies`, build `_graph_srcs`/`_graph_use`/`_excluded_srcs`/`_agg_*`/`_der_*`/`_kpi_config` (with `"use"`)/`_kpi_divs` once and set the same args on every callback, adding `graph_use_json`, `agg_use_json`, `derived_use_json`; give `FilterBuilder.build_dropdown/build_slider/build_range` (15048-15065, 15130, 15189) the three placeholders as `"[]"`. Do not edit `_FILTER_JS` yet. In `test_filter_exclude.py` give `_script_args` and `TestThePrimarySourceFallback` the three keys (`[[0]]` for a listed source) and reword the section-1 docstrings (sources are listed with their `use` and protected when none applies).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py -k TheCallbackArgs test/test_filter_exclude.py -q 2>&1 | tail -3` passes except `test_the_kpi_marker_is_kept_once_before_the_loop` (17-13); the JS still uses `active`; sources are listed with their `use`.]]></verify>
  <done>Every callback carried the same per-target use lists and the protected-source invariant still held.</done>
</task>

<task type="auto" id="17-12">
  <name>Mask graph and derived sources per target</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `_FILTER_JS` add memoised `dash_mask_for(use)` and `dash_ids_for(use)` over `dash_filter_mask(orig, filter_specs, all_widgets, use)`; keep `active`/`_active_ids`/`new_data` for the fallback `source`; make the graph-source loop (14235-14263, shape kept) read `dash_ids_for(_graph_use[_si])` and the derived loop (14310-14340) `dash_ids_for(_derived_use[_di])`. Read the whole script end to end first (14177-14915).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py -k "saved and (ExclusionHolds or OrderOfMoves or LinkGroup or ByPanel)" test/test_linking_filters.py -q 2>&1 | tail -3` passes; the identity-loop text pin in `test_linking_filters.py:331-360` is untouched.]]></verify>
  <done>Graph and derived sources on the saved page took their own target's mask on every move.</done>
</task>

<task type="auto" id="17-13">
  <name>Mask KPIs and aggregates per target</name>
  <files>dash_render.py, test/test_help_claims_3.py</files>
  <action><![CDATA[
    Group `kpi_config` entries by `JSON.stringify(k.use)`, build one `_grp_data` per group from `dash_mask_for(use)` and call `dash_apply_kpis` per group in place of the single call at 14650, keeping the marker exactly as TR-17.10 says: the line `dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);` becomes the comment `// dash_apply_kpis(new_data, ...) runs once per exclusion group below` followed by the loop, whose calls read `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`, so that the FIRST `dash_apply_kpis(new_data,` in the script is that comment and `test/test_kpi_brush.py:251` and the brush wiring (23483-23485) still slice the helper whole; do not touch the body of `function dash_apply_kpis(` (S11's, batch 3). In the aggregate block (14725-14915) read each config's `use` wherever it read `active`, `_active_ids` or `new_data`; read the block end to end first. Rewrite `test_help_claims_3.py::TestExcludeHoldsWhileItsOwnFilterMoves` as `TestAnExclusionHoldsAgainstEveryMove` (docstring citing dash.sthlp:1128-1138; the four-state sequence in both modes, saved through `JsSession`, served through chained `tp._fire`) and flip `"1"` → `1.0` at 452, 494, 404, 408.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_exclusion_sets.py test/test_help_claims_3.py test/test_saved_filter_layers.py test/test_export.py test/test_dropdown_values.py test/test_kpi_brush.py test/test_date_range.py test/test_js_runner.py test/test_mode_parity.py -q 2>&1 | tail -3` passes (the E2 pin of 17-10 included); `python3 - <<'EOF'
import dash_render as d
js = d._FILTER_JS
a, b, c = js.index("// ---- KPI recompute, shared by"), js.index("function dash_apply_kpis("), js.index("dash_apply_kpis(new_data,")
assert a < b < c and js[c - 3:c] == "// " and js.count("dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)") >= 1, (a, b, c)
print("marker ok")
EOF` prints `marker ok`; the served-name guards pass.]]></verify>
  <done>Cards and aggregate layers on the saved page followed their own filters, both modes agreed on every sequence, and the KPI marker stayed exactly once before the per-group loop.</done>
</task>

<task type="auto" id="17-14">
  <name>Certify E2 against Stata's count and summarize</name>
  <files>test/test_gaps2_truth.cscript, test/test_e2e_filters.cscript</files>
  <action><![CDATA[
    Add FT-04..FT-06 inside the `* ==== S17 X1 E2: filters vs count and summarize ====` block of `test/test_gaps2_truth.cscript` (17-05), before its `S17 end` line. On `sysuse auto`: compute into locals `count if foreign==1`, `count if foreign==1 & inrange(price,4000,5000)`, and `summarize mpg if foreign==1` / `summarize mpg if foreign==1 & inrange(price,4000,5000)` (`r(mean)`); register `dash scatter mpg price, name(g1)`, `dash scatter mpg weight, name(g2)`, KPIs `k1`/`k2` counting mpg, a foreign dropdown and a price range with `exclude(g1 k1)`, and `_dash_serve_spec`; a `python:` block renders both modes, moves foreign → 1.0 then price → (4000, 5000) (saved through `JsSession`, served through the widget callbacks as `test_filter_exclude._served` fires them) and writes g1's and g2's row counts, k1's and k2's card texts and the mean of each source's `mpg` to `st_global`s. FT-04: g1 rows and k1 equal `count if foreign==1`, g2 rows and k2 equal the intersection count, in both modes. FT-05: the two means equal Stata's `r(mean)` at rtol 1e-9. FT-06: the moves in the reverse order give the same numbers. Each displays `FT-0n PASS` or `FT-0n FAIL: <why>`. In `test/test_e2e_filters.cscript` add, before its final PASSED line, FL-E2-1 (the four-state sequence of `test_saved_state_depends_only_on_the_widgets` on the block's ten-row data built in Stata: page row counts 10/5/5/10 for g1 and 5/3/5/10 for g2, saved == served) and FL-E2-2 (reverse order reaches the same second state), page-only checks in the file's style. Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11). Run both scripts through the drivers of 17-05 (`GAPS2_ONLY=S17 scripts/stata_slot.sh /tmp/dash-s17 /tmp/dash-s17/run_test_gaps2_truth.do` and `scripts/stata_slot.sh /tmp/dash-s17 /tmp/dash-s17/run_test_e2e_filters.do`).
  ]]></action>
  <verify><![CDATA[`/tmp/dash-s17/run_test_gaps2_truth.log` shows `FT-01 PASS` through `FT-06 PASS` between `S17 start` and `S17 end`, with `grep -c '^r([0-9]*);' /tmp/dash-s17/run_test_gaps2_truth.log` printing 0; `/tmp/dash-s17/run_test_e2e_filters.log` shows `FL-X1-1 PASS`, `FL-E2-1 PASS`, `FL-E2-2 PASS` and its final PASSED line with `grep -c '^r([0-9]*);' /tmp/dash-s17/run_test_e2e_filters.log` printing 0; `python3 -m pytest test/test_cscript_hygiene.py -q` passes with the pins untouched.]]></verify>
  <done>After two moves on auto, the excluded graph and card equalled Stata's own count and mean and the others Stata's intersection in both modes, live, and the e2e script pinned the four-state page counts.</done>
</task>

<task type="auto" id="17-15">
  <name>Close E2 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    `dash.sthlp` 1128-1138 (`exclude()`): "prevent the filter from affecting the specified graphs and KPI cards, each a registered name, whatever moves. Each graph, card, and link group is redrawn on every move from the observations kept by the filters that do not exclude it, so its state depends only on the widgets' current values. Excluding a by() graph excludes every one of its panels. A graph in a link() group draws from the group's one source, so the group is filtered by a filter unless every graph of the group is excluded from it." Delete the sentence "An exclusion holds while its own filter is the one that moves …". `CHANGELOG.md`: replace in place the marker `<!-- WP-28 E2 -->` in the bold group `**WP-28 (GAPS2 audit, 25sep2026)**` at the end of the release's `### Results that change` list (CHANGELOG.md:10; D2, `index.md` R3, section-01 TR-01.7; E2 is a result that changes: the rows of an excluded graph go from 3 to 5) with ONE line ending `(WP-28, E2)` naming the command, the old value as `<scratch>/17-07-failure.txt` recorded it (Q24) and the new one: an excluded graph or card kept the rows of the last move made by a filter that did not exclude it, so after price → [4000, 5000], foreign → 1, price → full range an excluded graph showed 3 rows where the widgets implied 5; every target is now masked by exactly the filters that do not exclude it, on every move, in both modes; add nothing anywhere else in the file. `BUGS.md`: append at the end of the file one closed entry `- [x] Title: An excluded graph or card keeps the rows of the last move made by a filter that does not exclude it` with File Names and Line Numbers (`dash_render.py: _build_filter_widgets, _FILTER_JS, _on_filter_change (served template), _dash_filter_applies, _dash_widgets_for`), Description (the GAPS2 E2 symptom, cited), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, E2). Every graph, link group, by() panel, aggregate layer, derived source and KPI card is masked on every move by the AND of the filters whose exclude() does not name it, through per-target use lists and memoised masks in the saved script and cached per-target masks in the served callback. Pinned by test/test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved_state_depends_only_on_the_widgets, ::TestAnExclusionHoldsAgainstEveryMove::test_served_state_depends_only_on_the_widgets, test/test_help_claims_3.py::TestAnExclusionHoldsAgainstEveryMove, test/test_gaps2_truth.cscript FT-04..FT-06; fixture test/fixtures/filter_truth.json.` — exactly once each field, in order. Grep the three files for `claude|anthropic`. Run the full suite once in the worktree (`python3 -m pytest test/ -q`; the E2 run, the section's second and last), then the S17 block and `test_e2e_filters.cscript` through the drivers of 17-05; commit 17-07 to 17-15 as ONE commit on the worktree branch `wp28-s17`, subject ending `(GAPS2 E2)`, body opening with `<scratch>/17-07-failure.txt` and carrying the `Regression:` / `Flipped:` (17-10, 17-11, 17-13 flips) / `Fixture: test/fixtures/filter_truth.json (scripts/extract_filter_truth.do)` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` after the X1 commit with this message (`index.md` step 1, `index.md` step 1).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips; `python3 -m pytest test/test_tracking_documents.py -q` passes; `grep -n 'holds while its own filter' dash.sthlp` prints nothing; `grep -c '<!-- WP-28 E2 -->\|<!-- WP-28 X1 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, E2)' CHANGELOG.md BUGS.md` prints 2; `git log -2 --format=%s` shows the E2 subject above the X1 subject, each with its `(GAPS2 <ID>)`, and `git log -2 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>E2 was closed in BUGS.md naming its regression tests, dash.sthlp stated the exclusion rule as it now holds, the E2 CHANGELOG marker was replaced, and the second green commit on the worktree branch `wp28-s17` carried the E2 group for the merger.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes in both modes where a page exists; every pinned test listed is flipped in the commit named, none deleted.
- Two commits on the worktree branch `wp28-s17`, X1 (17-01..17-06, `(GAPS2 X1)`) then E2 (17-07..17-15, `(GAPS2 E2)`), each holding its failing tests, fix, flips and closed BUGS.md entry; no test-only commit exists (D1); the merger lands them on `s3-bugs` in that order.
- `test/fixtures/filter_truth.json` is committed (`git add -f`), carries the four `_meta` keys (D12) and is read by `test_filter_exclusion_sets.py`.
- `_dash_option_value`, `_dash_dropdown_values`, `_dash_dropdown_mask`, `_DASH_FILTER_MASK_JS` and `_dash_json_value` implement the one rule; `mask_parity` passes on the hostile columns and on the two-value groups.
- `_dash_filter_numeric`, `_dash_filter_applies`, `_dash_widgets_for` are in the served function list (after `"_dash_dropdown_values"`) and in `test/function_test_map.py`.
- `filter_specs_json` carries `numeric` and `groups`; the widget carries `_dash_numeric` and `_dash_groups`; callbacks carry `graph_use_json`, `agg_use_json`, `derived_use_json`; `kpi_config` entries carry `use`; `_FILTER_JS` holds the marker comment `// dash_apply_kpis(new_data, ...) runs once per exclusion group below` exactly once before the per-group loop.
- The `* ==== S17 X1 E2: filters vs count and summarize ====` … `* ==== end S17 ====` block (FT-01..FT-06, gated by `GAPS2_ONLY`) is in `test/test_gaps2_truth.cscript` above its last line and FL-X1-1, FL-E2-1, FL-E2-2 are in `test_e2e_filters.cscript`; `test/run_all_cscripts.do` and the hygiene pins are untouched (D11); both scripts pass through their driver do-files; the full pytest suite is green with no skips.
- BUGS.md carries closed E2 and X1 entries in the D3 form; dash.sthlp 1109-1138 is rewritten (S12's sentence included); both CHANGELOG markers are replaced.

## Notes

- **Read `_FILTER_JS` end to end (14177-14915) before editing it.** The aggregate block (14725-14915) is the consumer of the mask most easily missed; `test_an_aggregate_and_a_derived_layer_take_their_targets_mask` exists to catch it.
- **The KPI marker (TR-17.10; section-11 and `test/test_kpi_brush.py:251` rely on it).** `test/test_kpi_brush.py:251` and the brush wiring (23483-23485) slice `_FILTER_JS` from `// ---- KPI recompute, shared by` to the FIRST `dash_apply_kpis(new_data,`. Keep that text as the comment on the line the single call stood on, write every per-group call as `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`, and never edit the body of `function dash_apply_kpis(` (S11 rewrites it in batch 3 and asserts the three indices' order).
- **Merge order (`index.md` step 2 merge order).** Batch 2 merges S04, S05, S13, S17, S16, S14: this section lands before S16 (`_apply_colorvar` except line 6527) and S14 (one-line lookups in `_dash_csv_meta`, `_dash_facet_label`, the saved filter builder 23598-23603); S12 (batch 3) rebases its label change onto the float-valued `rv`, fills `_dash_groups`/`groups` from `_dash_fmt_text`, and only verifies the dash.sthlp 1109-1128 wording written here; S11 (batch 3) rewrites `dash_apply_kpis`'s body and adds `fmt`/`storage` beside `use`.
- **Q26 (DISCOVERY Q26).** A numeric entry's value is its group's FIRST value; the spec's `groups` lists `[value, member, ...]` per entry; `_dash_groups` maps `value → (members,)`; both masks keep a row whose number equals any member. This section ships groups of one, so nothing changes on today's pages; S12 forms the real groups by display text and lists each once, with no suffix.
- **Coercion keeps the old tests alive, briefly.** After 17-02 a string `"1"` still selects on a numeric column (the pandas mask does `float(value)`, the JS `Number(val)`), so tests that set `"1"` do not fail before 17-03/17-13 flip them. Flip them anyway: the widget's real value is `1.0`.
- **`_dash_json_value` is the CSV's writer too** (13946). Keeping strings as text fixes the download of string codes (named in the X1 CHANGELOG line), and `test_export.py`'s `_dash_csv_text_value` table (566-570) is unaffected (it already returns text).
- **The identity loop's text is pinned** by `test_linking_filters.py:331-360`; keep `_kept_ids_by_src`, `_ids_i`, `_active_ids.has(...)` names or update that test in the same commit with the reason.
- **`excluded_sources` keeps a meaning**: sources no filter applies to. That keeps `TestTheCallbackKnowsWhatItProtects`'s invariant and the JS fallback guard true, and it is the correct behaviour (such a source never changes).
- **Served `Select.value` after a browser change is a JS number**, so the callback receives a float; the pandas mask must not `str()` it. `tp._served_after_move` picks by label and needs no change.
- **A dropdown over the option limit** on a numeric column becomes a range (`_dash_filter_effective_type`), unchanged; the string case still truncates to the first `limit` values in sort order.
- **Shared registries (rules R1-R6).** R1: FT-01..FT-06 are a block of `test/test_gaps2_truth.cscript` in the block form of `sections/BRIEF.md` "Certification scripts" (`* ==== S17 X1 E2: … ====`, the `GAPS2_ONLY` gate, `S17 start`/`S17 end` lines that S19 reads for wall time, `* ==== end S17 ====`), inserted above the script's last line in section order; the page-only cases join `test_e2e_filters.cscript`; no runner block, no hygiene-pin edit (D11). R2: the three helper names go into the served function list after `"_dash_dropdown_values"` (24627, `index.md` R2 anchor table) and `function_test_map.py` keys in alphabetical place; the merger resolves append conflicts by hand. R3: this section edits dash.sthlp 1109-1138 only, replaces only its two markers and appends its two BUGS.md entries at the end. R5: `filter_truth.json` is written once by 17-08, never patched. R6: the parity corpus is not edited here (its existing dropdown/exclude cases re-profile on their own); `ALLOWED` and `_MUST_WARN` are never edited here.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at <pre-fix tree> with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>` (one per flip), `Fixture: test/fixtures/filter_truth.json (scripts/extract_filter_truth.do)` (E2 only), `BUGS.md: "<title>" (closed)`.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6, `index.md` step 0): the wrapper takes one of three `mkdir` slots, sets `STATATMP=<scratch-dir>/tmp/` (trailing slash) and runs the CLAUDE.md rule 10 console command; never the GUI, never a bare `stata-mp`, never `make cert` inside a section (S19 runs the cert suite and records its wall time). A cscript is never given to the wrapper directly (it opens `cscript … adodir ".."` and `do "cert_helpers.do"` relative to `test/`): write the two-line driver `cd "<repo>/test"` / `do "<repo>/test/<script>.cscript"` into the scratch directory and run that (`sections/BRIEF.md` "Running one cscript", `index.md` step 0a); `GAPS2_ONLY=S17` in the environment runs only this section's block of the truth script. The extract script sets `global ZA_REPO` itself and runs directly. A `python:` SKIP means `python_exec` was dropped — check `c(python_exec)`, never count the run as a pass.
- **pytest**: only the changed files while iterating; the full suite once before each of the two commits (17-06 and 17-15) as `python3 -m pytest test/ -q`; never a second concurrent full run.
- **S03's runner is the only way to chain saved moves**; the older `_run_callback` in `test_filter_exclude.py` re-encodes from unchanged models and cannot express a sequence (research [B §2.3]).
- **Line numbers drift** by what S03, S04, S05 and S13 merged before this section and by what 17-02, 17-09 and 17-11 add; every anchor here is also a symbol. Locate by `def` and by the marker comments.
