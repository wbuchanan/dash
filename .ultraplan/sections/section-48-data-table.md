# Section 48: Per-graph data table

> Part of: WP-31 · GAPS3 rows: H2t (new requirement, DISCOVERY Q35a, Q38-Q40) · Risk: yellow · Batch: 16 · Depends on: 01 · Blocks: 51, 53, 54 · Tasks: 4, 1 commit · Case-id prefix: U48

## Overview

**What is wrong today.** GAPS3 H2 (GAPS3.md:239) lists the dashboard extensions and the maintainer added one more in DISCOVERY Q35: "formatted tables containing the data displayed in the graph". No `DataTable` exists anywhere in dash_render.py at `6370ca4` (research/codebase-mechanics.md §9: "no `DataTable` exists anywhere today"), although `bokeh-tables` is already inlined in every saved page (dash_render.py:4939) and both installed Bokehs carry `DataTable` and `TableColumn` with identical property sets (research/bokeh-web.md §6, §10). A user who wants the numbers behind a graph has only the CSV button (`_csv_button`, :45901-45937), which writes raw values -- shortest floats, ISO dates -- not Stata's display text (research §9: `_DASH_CSV_JS` "writes raw numbers ... not Stata display formats"), and writes the whole dataset, not one graph's drawn rows.

**After this section** a graph given the new `table` option draws, under its figure, a `Toggle` labelled "Data table" and a `DataTable` that is folded away until the toggle is pressed (Q38: "folded away by default with a toggle; the layout is unchanged until opened"). The table lists the rows the graph currently draws -- after filters, brush and qualifiers (Q39) -- with one column per variable the graph plots plus every `hover()` variable, each shown in the variable's Stata display format with value labels applied (Q39). It scrolls virtually through every drawn row, sorts by column, and lists at most `rows()` rows (default the new `table_rows` limit, 1,000) with a fixed note when more are drawn (Q40). It follows every filter move in both modes because it is bound to the figure's own source and view: the drawn source carries precomputed text columns, so a saved-page move (which rewrites the source's rows) and a served move (which re-slices the frame) both carry the text along with no new JavaScript (D-48b).

**Why one section.** The option, the text columns, the table, the toggle and the cell layout are one feature with one shared seat, `_dash_layout_cell` (:35899), which the saved grid, the saved tabs and the served app all call (research §9). The index makes S48 batch 16's one `_dash_layout_cell` editor (R12).

**Test order and commit rule (rule 7, M2).** One cycle, one commit `(WP-31 H2t)`: 48-01 writes the regression tests red and saves the failure text; 48-02 adds the option end to end in dash.ado and the Mata repeat tables with the cscript cases; 48-03 adds the text columns, the shared table builder, the layout-cell change and the served twin; 48-04 certifies, writes the help paragraph, closes the BUGS.md entry and makes the one commit.

### Section decisions (binding on the executor)

- **D-48a. `table` is a graph-level option; its declaration is PROBED first (REVIEW-4 R4-15).** Stata's `syntax` cannot declare one option both bare and with parentheses, and no `X X2(...)` pair exists in dash.ado at `6370ca4` (`grep -E '[A-Z]+[a-z]* +[A-Z]+[a-z]*2\('` finds none), so the two-declaration idiom (`TABle` the bare flag, `TABle2(string asis)` the argument form) is asserted, not measured. 48-02 opens with a 6-line probe do-file through the slot: `program _u48probe` / `syntax [, TABle TABle2(string asis)]` / `display "[\`table'][\`table2']"` / `end`, fed `table`, `table(rows(5))`, `table table(x)` and `table()`, with `capture noisily` and the rc and output recorded in `<scratch>/s48/syntax-probe.log`. If `syntax` resolves bare `table` to the flag and `table(...)` to the argument form (both abbreviate to `tab`), the idiom is used and the two locals fold into ONE spec key `graph_options["table"]`: `"on"` for the bare flag, else the typed sub-option text. If `syntax` refuses either form, the fallback is ONE declaration `TABle(string asis)`: `table(on)` is the bare form, `table()` is accepted as the bare form when `syntax` passes it (the probe says), bare `table` is refused by `syntax` itself, and the help's `{marker:table}` paragraph says so; the spec key and every later rule are unchanged (the value `on` or the sub-option text). The seven graph key lists (dash.ado:5776, 6714, 6748, 6849, 6924, 6956, 7339) gain the word `table`. Mata: `_dash_rep_unique` (dash_parse.mata:6200) lists `table`, so a second copy is refused r(198) "option table() not allowed" exactly as `name()` is; `_dash_rep_cat` returns its default `"R"` (last copy) and needs no edit. The option is dash's own, not twoway's, so `_dash_rep_und_tab` (:6250) is untouched and no twoway refusal is measured.
- **D-48b. Formatted text travels as columns of the drawn source.** For every variable the table lists, both renderers add a string column `__dash_tbl_<var>` to the data frame before any source is built (`_dash_table_text_frame`, shared). Its text is `_dash_fmt_text(value, fmt, storage)` for a number, the value label when one applies (`_dash_value_labels_for`), the date's display text through `_dash_date_fmt` for a date variable, and `"."` for a missing value -- the rules `_dash_filter_widget`'s `_label` closure applies (:34610-34640). The DataTable's `TableColumn.field` is the text column and its `title` is the variable's label (`variable_labels`) or name. No `HTMLTemplateFormatter` and no JavaScript formatting: the saved `_FILTER_JS` copies every column of every kept row and the served move re-slices `_df_ref`, so both carry the text unchanged. S48 therefore edits neither `_FILTER_JS` nor the served move path.
- **D-48c. One table per registered graph, bound to the figure's source and the first renderer's view.** `source = fig.renderers[0].data_source` when that renderer draws from the graph's raw source (its data holds `__dash_row__`), and `view = fig.renderers[0].view` (a linked or qualified graph's `CDSView` carries its mask; research/bokeh-web.md §6: "a table bound to the same source and a CDSView with the same filter follows every filter move with no extra code"). A graph whose first renderer draws from a derived copy (a sorted line, a histogram's bins) uses the next renderer whose source holds `__dash_row__`; a graph with none (`function`, `scatteri`, a lone histogram) gets no table and one note (D-48e). The table's view is an `IndexFilter` built in Python; S51 (batch 17) rewrites its `indices` on a `brush(filter)` selection (S51 TR-51.8; the cap travels in the table's tags, D-48e), so the table follows a brush too (Q39).
- **D-48d. A by() graph gets ONE table under its grid (DECISIONS D6; no residual).** The table holds every panel's drawn rows and a leading panel column. Source: the graph's own row source, `self.sources[name]` (saved; it holds every row of the graph with `__dash_row__`, and the panel sources are sliced from it) and the graph's frame source in the served app (the one `_dash_move_apply` rewrites on a move; if the by() path builds only per-panel sources, build the graph-level one with `_dash_layer_source` for the table and add it to the list `_dash_move_apply` rewrites -- read the template's by() branch first). Columns: the by() variable(s) first (`_dash_table_vars` prefixes `graph_options["by"]`'s variable names), then the plotted and `hover()` variables; the by() column's text is the panel label the grid shows (the value label when one applies, else `_dash_fmt_text` with the variable's format; the same `__dash_tbl_<byvar>` rule as every other column) and its title is the variable's label or name. View: `IndexFilter(indices=flatnonzero(mask)[:cap])` where `mask` is the graph's qualifier mask over that source (`GlyphMapper._view_mask`; all rows when the graph has no qualifier); the cap applies to the union of the panels' rows, in source order (the panel column is sortable, so a reader groups by panel). Toggle, note and `_dash_table` attribute as for a plain graph, the attribute set on the first panel figure (`figs[0]._dash_table`, read by S53 and S54). Layout: `_dash_layout_cell`'s facet branch (:35968 `return _dash_name_save(_dash_reflow(grid))`) returns `column(_dash_name_save(_dash_reflow(grid)), *figs[0]._dash_table, sizing_mode="stretch_width")` when the attribute is set. The saved page's `_FILTER_JS` rewrites the graph's row source on a move and the served move rewrites the frame source, so the by() table follows a move with no new JavaScript, as a plain graph's does (D-48b).
- **D-48e. Row cap.** `_DASH_LIMITS["table_rows"] = (1_000, 100_000, "dash_max_table_rows")`; `table(rows(#))` sets the cap for its graph within `[1, 100_000]`. The table's view is a `CDSView` whose filter is ONE `IndexFilter` of the first `cap` DRAWN rows (DECISIONS A29, REVIEW-4 R4-05b): `kept = np.flatnonzero(mask)` with `mask` the renderer's view mask (`GlyphMapper._view_mask`; the qualifier and link mask), `IndexFilter(indices=kept[:cap].tolist())`; when the renderer has no mask, `IndexFilter(indices=list(range(min(cap, n))))`. Capping by source position (`range(cap)` under the renderer's filter) was wrong: a qualified graph whose mask drops the first rows would list fewer than `cap` rows, or none. After a saved move the page rewrites every source to its kept rows, so the kept positions are `range(n_kept)` and the Python-built list stays right up to the cap (the node test below says so); S51's brush(filter) rewrite mutates the same `IndexFilter.indices`. The cap travels in the table's tags, `tags=["dash_table", "dash_table_cap=<cap>"]`, so S51's JS reads it. The note below the table is the fixed text `_DASH_TABLE_CAP_NOTE = "The table lists at most {cap:,} rows of those drawn."`, shown (a `Div` with `role="note"`) whenever the drawn row count at build time exceeds `cap`; a move does not rewrite the note (its text is true whatever the move keeps).
- **D-48f. Sub-options.** `table(rows(#) open)`: `rows(#)` the cap, `open` starts the table unfolded. Anything else in the parentheses is refused in dash.ado: `dash: table() takes rows(#) and open; '<text>' is not one of them` r(198), the text bounded to 40 characters through `_dash_imm_echo`'s rule.

## Risk: [yellow] -- a new Bokeh model class in every table dashboard, and a shared layout function changes

**Why.** `_dash_layout_cell` is called by the saved grid, the saved tabs and the served app; a wrong return type breaks every dashboard, table or not. `bokeh-tables` is a third bundle; the saved page already inlines it, but the served `Resources(mode="server")` must serve it too (it does: Bokeh adds `bokeh-tables` when a DataTable is in the document, research/bokeh-web.md §10).

**Risk factors.**
1. On a source rewrite the saved page's `IndexFilter` indices beyond the new length must be ignored by BokehJS, not throw; the first-N-drawn rule (D-48e) must hold at build for a qualified graph and after a move.
2. A toggled-hidden DataTable may need a resize when shown (research §6: "SlickGrid may need `dt.visible=true` then a resize -- not verified in a browser").
3. The text columns add one string column per listed variable to the frame; 100,000 rows × 6 variables is 600,000 strings in the page.
4. parity: the served document must hold the same `DataTable` columns and the same `visible` flag as the saved page.

**Mitigation.**
1. `TestTheTableFollowsAMove::test_saved_page_in_chrome` (release tier) rewrites the source through a filter move in headless Chrome and reads the table's row count; `TestTheView::test_a_qualified_graph_lists_its_first_drawn_rows` pins the build-time rule and `::test_after_a_saved_move_the_kept_positions_are_a_range` (node: run `_FILTER_JS` through `js_runner`, then assert the rewritten source's kept rows are positions `0..n_kept-1`, so the Python-built index list is right up to the cap) the post-move case (indices are filtered `i < length` in BokehJS `IndexFilter.compute_indices`, read from the bundle by `test_the_index_filter_drops_out_of_range_indices`).
2. The toggle's CustomJS sets `dt.visible = cb_obj.active` and then calls `Bokeh.index.find_one(dt)?.invalidate_layout?.()` inside a `try`; the Chrome test asserts a row is rendered after the toggle.
3. The text columns are added only for `table` graphs and only for the listed variables, each distinct value formatted once (TR-48.7); `test_estimator_cost.py::test_table_text_frame_under_two_seconds_at_100k` pins the cost and `test_the_text_columns_are_only_added_for_table_graphs` pins that a dashboard without `table` adds none.
4. The parity corpus entry `_case("scatter table", ...)` compares the layout tree, which `_layout_tree` already walks (test_mode_parity.py:1001); S48 adds `DataTable` to the model kinds it records.

## Dependencies

- **Depends on: 01** (tracking entry H2t, CHANGELOG markers, the truth script block).
- **Blocks: 51** (S51's brush(filter) rewrites `fig._dash_table[1].view.filter.indices`, A29), **53** (the composite export draws the table's toggle state and omits a folded table; S53 reads `fig._dash_table`), **54** (`html_attributes` on the toggle and the table).
- **Parallel batch: 16** with S47 (function fallback + fixtures) and S49 (FilterBuilder). S48 edits `_dash_layout_cell`, `_make_figure_body`'s caller `_build_sources_and_figures` (one new call) and the served `_dash_figure_for` (one new call); S49 edits `FilterBuilder`, `_dash_filter_widget`, `_build_filter_widgets` and `_DASH_FILTER_MASK_JS`; S47 edits the function mapper and fixtures. No function is shared.

## Evidence

Anchors at `6370ca4` (dash_render.py 51,5xx lines; dash.ado 11,0xx).

### Nothing draws a table

`grep -n "DataTable" dash_render.py` prints nothing at `6370ca4`. The one place every registered name becomes a renderable is `_dash_layout_cell` (:35899-35971; :36009-36013 is `_dash_parse_tabs`, REVIEW-4 R4-17), ending:

```python
35968        return _dash_name_save(_dash_reflow(grid))
35969    if name in figures:
35970        return figures[name]
35971    return kpi_divs.get(name)
```

### The option surface

`_dash_parse_graph_opts` declares every graph option in one `syntax` (dash.ado:933-966); the last declared line before `*` is:

```
962        TLABEL2(string asis)      TTICK2(string asis)       TLINE2(string asis) ///
963        TSCALE2(string asis)      TTITLE2(string asis) ///
964        * ///
```

The plot parser repeats the graph options so they can be written inside a segment (:1167-1239; `XLIne(string asis)` at :1209). The sreturns are at :1050-1060 (graph parser, `sreturn local xline : copy local xline`) and :1538-1546 (`sreturn local g_xline : copy local xline`). The seven graph key lists -- six `foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ...` lists at :6714, :6748, :6849, :6924, :6956, :7339 and the `foreach gkey in ...` list at :5776 (R4-17) -- are; `test_abbreviations.py::TestTheAxisRouteKnowsDashsSpellings::test_the_seven_graph_key_lists_agree` (test/test_abbreviations.py:773) pins them equal.

`_dash_rep_unique` (dash_parse.mata:6200-6215) lists the options twoway takes once; the list ends `"colorvarminmax"), k)) return(1)`.

### Formatting rules already in the tree

`_dash_fmt_text(value, fmt, storage=None)` (:27909) and its JS twin `dash_fmt_text` (:24340); `_dash_value_labels_for(var, value_labels, value_label_names)` (:36606); `_dash_hover_layer_vars(plot)` (:40053-40079) returns a layer's plotted variables in tooltip order; the graph's `hover()` extras are `graph_opts["hover"]` split on blanks (`_dash_build_hover`, :40081). The dropdown label closure (:34610-34640) is the rule D-48b copies.

### The limits table

`_DASH_LIMITS` (:1862-1875) maps a name to `(default, ceiling, global)`; dash.ado writes the user's globals into `build_options["limits"]` (:10535 `"limits":`_dash_lim_json'`). `_dash_limit_hint(name, verb)` writes the "set global ..." hint.

### Existing tests that pin today's behaviour

- test/test_layout.py (grid cells are figures or Divs): any `isinstance(cell, (Figure, Div))` assertion -- the executor greps `_dash_layout_cell` in test/ and flips a pinned kind list, if any, to admit `Column`.
- test/test_mode_parity.py `_layout_tree` (:1001) records model kinds; a `Column` wrapping a figure must be unwrapped or recorded in both modes alike (TR-48.9).

## User stories

- **US-48.1** As a dashboard author I want `dash scatter mpg weight, table` to add a folded data table under the graph so that a reader can see the drawn numbers without leaving the page.
- **US-48.2** As a reader I want the table to show `price` as `4,099` and `foreign` as `Foreign`, as Stata shows them, so that the table reads like Stata's `list`.
- **US-48.3** As a reader I want the table to shrink to the rows a filter or brush keeps so that it always matches the picture above it.
- **US-48.4** As an author of a large dataset I want the table to list at most a known number of rows with a note, so that the page stays usable.

## Business requirements

- **BR-48.1** `table` on a graph draws nothing more until its toggle is pressed; the graph's size and position are unchanged.
- **BR-48.2** The table's columns are the graph's plotted variables, in tooltip order, then its `hover()` variables; the column header is the variable label, else the name.
- **BR-48.3** Every cell shows Stata's display text for the variable's format and value labels; a missing value shows `.`.
- **BR-48.4** The rows are exactly the rows the graph draws at that moment, in both modes, after every filter move.
- **BR-48.5** The table sorts by any column and scrolls through all its rows; it lists at most `rows()` rows (default 1,000), and says so when more are drawn.
- **BR-48.6** `table` twice, `table(bogus)` and `rows(0)` are refused with one sentence each; `table` on a by() graph draws one table under the grid, with a leading panel column, holding every panel's drawn rows (D6).

## Technical requirements

- **TR-48.1 dash.ado declarations.** In `_dash_parse_graph_opts` add, after line 963 (`TSCALE2(string asis)      TTITLE2(string asis) ///`), the line `        TABle                     TABle2(string asis) ///`. In `_dash_parse_plot_opts` add the same line after the line holding `XLIne(string asis)` (:1209). After each parser's `syntax`, fold: `if "`table'" != "" & `"`table2'"' != "" { display as error "dash: table may not be combined with table()"; exit 198 }` then `if "`table'" != "" local table on` / `else local table : copy local table2`. sreturn `table` beside `xline` (:1056) and `g_table` beside `g_xline` (:1542).
- **TR-48.2 Sub-option check.** New program `_dash_table_check` (dash.ado, `version 19`, after `_dash_line_check` :7669): takes the text; `on` passes; otherwise tokens are read with `_dash_rep_toks`/`_dash_rep_optname` (as `_dash_barwidth_typed` reads them); `rows(#)` must be an integer 1..100000 (else `dash: table(rows()) takes an integer from 1 to 100,000; got '<text>'` r(198)); `open` is a bare word; any other token is refused per D-48f. Called from `_dash_plot` beside `_dash_line_check` (near :6984). Program added to test/program_coverage_map.py `COVERAGE["dash.ado"]` as `"_dash_table_check": ("test_wp31_truth.cscript:U48-3", "test_option_validation.cscript:U48-5")`.
- **TR-48.3 Key lists and JSON.** Append ` table` as the last word of each of the seven graph key lists (the six `foreach gk in ...` lists and the `foreach gkey in ...` list at :5776; the word before `{`). The JSON writer (:7339-7415) then writes `"table":"on"` or `"table":"rows(50) open"` with no further edit (it writes every key with a value).
- **TR-48.4 Mata.** `_dash_rep_unique`: insert `"table",` before `"colorvarminmax"` with the comment `// WP-31 H2t: dash's own option, taken once.`
- **TR-48.5 `_dash_table_spec(graph_opts, limits)`** (new, shared, dash_render.py after `_dash_hover_layer_vars`): returns `None` when `graph_opts.get("table")` is empty, else `{"rows": cap, "open": bool}` with `cap = limits["table_rows"]` unless `rows(#)` is given (clamped to `[1, limits ceiling]`).
- **TR-48.6 `_dash_table_vars(graph)`** (new, shared): the by() variable names first (`graph["graph_options"].get("by", "")`'s leading varlist, read with the by() grammar S36 landed -- the words before the first `,`), then `[v for p in graph["plots"] for v in _dash_hover_layer_vars(p)]` deduplicated in order, then `graph["graph_options"].get("hover","").split()` deduplicated against the earlier lists; every name must pass `_dash_is_stata_name` (a hand-built spec's other text is dropped).
- **TR-48.7 `_dash_table_text_frame(df, vars, formats, storage_types, value_labels, value_label_names, variable_labels, date_vars)`** (new, shared): for each var in `vars` present in `df.columns`, sets `df["__dash_tbl_" + var]` to the text per D-48b, formatting each DISTINCT value once (REVIEW-4 R4-16: `uniq = col.dropna().unique(); text = col.map({v: _dash_fmt_text(v, fmt, st) for v in uniq}).fillna(".")`, the value-label and date branches applied to the same `uniq` -- never one `_dash_fmt_text` call per row: 100,000 rows x 6 variables would be 600,000 calls); `test_estimator_cost.py::test_table_text_frame_under_two_seconds_at_100k` pins it (M10); returns `[(var, title)]` with `title = variable_labels.get(var) or var`. Called in the saved renderer in `_build_sources_and_figures` before `_collect_plot_vars` builds the first source, for every graph whose `_dash_table_spec` is not None, and in the served template after `df` is decoded (the line after `_FORMATS` is defined), with the same arguments. The text column names are added to the saved column list through `_DASH_OPT_VAR_KEYS`'s neighbour mechanism: `_collect_plot_vars` gains `+ [c for c in df.columns if c.startswith("__dash_tbl_")]` for table graphs only (so the source carries them), and the served `_dash_layer_source`'s `extra_cols` gets the same names.
- **TR-48.8 `_dash_data_table(fig, columns, spec, n_drawn)`** (new, shared, imports `DataTable, TableColumn, CDSView, IndexFilter, Toggle, CustomJS, Div, column` inside the function; signature gains `source=None, mask=None` for the by() table of D-48d, which passes the graph's row source and qualifier mask instead of reading the first renderer): picks the renderer per D-48c; builds `TableColumn(field="__dash_tbl_"+var, title=title, sortable=True)` per column; `kept = np.flatnonzero(mask)` (the renderer's `GlyphMapper._view_mask` when it has one, else `np.arange(len(src.data[_ROW_ID_COLUMN]))`), `DataTable(source=src, view=CDSView(filter=IndexFilter(indices=kept[:spec["rows"]].tolist())), columns=cols, index_position=None, sortable=True, height=min(400, 28 + 25 * min(n_drawn, spec["rows"])), sizing_mode="stretch_width", visible=spec["open"], tags=["dash_table", "dash_table_cap=%d" % spec["rows"]])` (D-48e; no `AllIndices`, no composite filter); `note = Div(text=html.escape(_DASH_TABLE_CAP_NOTE.format(cap=spec["rows"])), visible=spec["open"] and n_drawn > spec["rows"], tags=["dash_table_note"], html_attributes={"role": "note"})`; `toggle = Toggle(label="Data table", active=spec["open"], button_type="light", tags=["dash_table_toggle"])` with `toggle.js_on_change("active", CustomJS(args=dict(dt=dt, note=note, capped=bool(n_drawn > spec["rows"])), code=_DASH_TABLE_TOGGLE_JS))` where `_DASH_TABLE_TOGGLE_JS = "dt.visible = cb_obj.active; note.visible = cb_obj.active && capped; try { const v = Bokeh.index.find_one(dt); if (v && v.invalidate_layout) v.invalidate_layout(); } catch (e) {}"`. Sets `fig._dash_table = (toggle, dt, note)` and returns it. The CustomJS runs in both modes (BokehJS), so the served app needs no Python twin.
- **TR-48.9 `_dash_layout_cell` change.** Replace :35969-35970 (`if name in figures:` / `return figures[name]`) with: `if name in figures: f = figures[name]; t = getattr(f, "_dash_table", None); return column(f, *t, sizing_mode="stretch_width") if t else f` (import `column` from `bokeh.layouts` inside the function). The facet branch at :35968 (`return _dash_name_save(_dash_reflow(grid))`) becomes `g = _dash_name_save(_dash_reflow(grid)); t = getattr(figs[0], "_dash_table", None); return column(g, *t, sizing_mode="stretch_width") if t else g` (D-48d). test_mode_parity.py `_layout_tree` (:1001) unwraps a `Column` whose first child is a figure (or a by() grid) carrying `_dash_table` into that child plus a `{"kind": "DataTable", "columns": [...titles], "visible": bool}` record in both modes.
- **TR-48.10 Call sites.** Saved: after `_make_figure_body` returns the figure for a graph (in `_build_sources_and_figures`), `if spec: _dash_data_table(fig, cols, spec, n_drawn)` where `n_drawn` is the view's kept row count (`GlyphMapper._view_mask`). Served: in `_dash_figure_for` (template :49474 region) after the figure is finished, the same call. by() graphs (D-48d): when `graph_opts.get("by")` is non-empty and `table` is set, call `_dash_data_table(figs[0], cols, spec, n_drawn, source=<the graph's row source>, mask=<the graph's qualifier mask over it>)` after the panel figures are built (saved: in `_build_sources_and_figures` where the facet figures are returned; served: in `_dash_figure_for`'s by() branch, with the frame source `_dash_move_apply` rewrites), where `n_drawn` is the mask's kept count over every panel; no note is printed.
- **TR-48.11 Served copy lists (R2).** Constants `_DASH_TABLE_CAP_NOTE`, `_DASH_TABLE_TOGGLE_JS` after `_DASH_STALE_STATUS_HTML`'s entry; functions `_dash_table_spec`, `_dash_table_vars`, `_dash_table_text_frame`, `_dash_data_table` after `_dash_reference_lines` (:47223). `_DASH_LIMITS` gains the `table_rows` row after `added_text`; dash.ado's limit-global reader lists `dash_max_table_rows` where it lists `dash_max_added_text`.
- **TR-48.12 Maps.** test/function_test_map.py entries for the four functions and `_dash_data_table.<locals>` none; test/program_coverage_map.py for `_dash_table_check`.
- **TR-48.13 Help.** dash.sthlp: a new paragraph `{marker:table}` under the graph options (after `hover()`), the Standalone-vs-server table row "data table: yes / yes", and dash.pkg/README untouched (S59).

## Boundaries

- No edit to `_FILTER_JS`, `_DASH_FILTER_MASK_JS`, `_build_filter_widgets`, `FilterBuilder` (S49, same batch), `_dash_move_apply` or `_make_filter_cb` (S51/S52, batch 17).
- No CSV change: the download's column rule stays every dataset column (`__dash_tbl_*` columns are excluded from `_dash_csv_meta` by its existing `__dash_` prefix rule; verify with `test_the_csv_omits_the_text_columns`).
- No export change (S53), no ARIA beyond the note's `role` (S54).
- No plot-level `table` (D-48a); no per-panel table under by() (D-48d draws one table under the grid).

## Stata truth

None measured from twoway (the option is dash's own). The truth block U48 checks the spec and the refusal texts only; `test/test_wp31_truth.cscript` block `* ==== S48 H2t: data table ====` with cases U48-1..U48-4; test_option_validation.cscript cases U48-5, U48-6.

## TDD test stubs

Regression tests (red at 6370ca4), file `test/test_data_table.py`:
- Test: `dash scatter mpg weight, table` spec renders a `DataTable` under the figure in both modes -- `TestATableIsDrawn::test_saved_cell_is_a_column_of_figure_toggle_table_note`, `::test_served_cell_is_the_same`.
- Test: no `table` → no DataTable, no `__dash_tbl_` column -- `TestATableIsDrawn::test_without_the_option_nothing_is_added`.
- Test: columns are plotted vars then hover vars, titles are variable labels -- `TestTheColumns::test_order_and_titles`.
- Test: text is Stata's display text (`price` `%8.0gc` → `4,099`; `foreign` → `Foreign`; a missing `rep78` → `.`) -- `TestTheText::test_formats_labels_and_missing` (fixture-free: `_dash_fmt_text` is the oracle, as `test_filters.py` uses it).
- Test: the table's view is one IndexFilter of the first `rows` DRAWN positions -- `TestTheView::test_first_n_drawn_rows`, `::test_a_qualified_graph_lists_its_first_drawn_rows` (a qualifier dropping the first rows: the list starts at the first kept position, has `min(cap, n_kept)` entries), `::test_after_a_saved_move_the_kept_positions_are_a_range` (node), `::test_the_cap_is_in_the_tags`.
- Test: `rows(5)` caps and shows the note; default is 1,000; the note is hidden when fewer rows are drawn -- `TestTheCap::test_rows_sub_option`, `::test_the_note_is_fixed_text`.
- Test: folded by default, `open` unfolds; the toggle's CustomJS code is `_DASH_TABLE_TOGGLE_JS` -- `TestTheToggle::test_default_folded`, `::test_open`.
- Test: a by() graph draws one table under the grid -- `TestByGraphs::test_one_table_under_the_grid_both_modes` (the cell is `column(grid, Toggle, DataTable, Div)`), `::test_rows_come_from_every_panel` (row count = every panel's drawn rows, capped), `::test_the_panel_column_leads_with_the_panel_labels` (first column titled by the by() variable's label; its text equals the panel labels the grid shows), `::test_the_cap_applies_to_the_union` (`rows(5)` on `by(foreign)` lists 5 rows in all).
- Test: formatting is done once per distinct value and stays under 2 s at 100,000 rows x 6 variables -- `test/test_estimator_cost.py::test_table_text_frame_under_two_seconds_at_100k` (M10).
- Test: the four names are on the served copy lists -- `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` (existing guard, extended by its parametrisation).
- Test (release, Chrome): after a dropdown move the table shows the kept row count and a toggled table renders a row -- `TestTheTableFollowsAMove::test_saved_page_in_chrome`, `::test_served_doc_in_chrome` (through `_CspProbe`).
- Test: `test_the_index_filter_drops_out_of_range_indices` reads BokehJS `IndexFilter` source from the installed bundle.

cscript cases (test_wp31_truth.cscript block S48): `U48-1` bare `table` writes `"table":"on"`; `U48-2` `table(rows(50) open)` writes the text; `U48-3` `table(rows(0))` r(198) with the sentence; `U48-4` `table table` r(198) "option table() not allowed". test_option_validation.cscript: `U48-5` `table(bogus)` r(198) bounded echo; `U48-6` `table` beside `table()` r(198).

Pinned tests to flip: any layout test asserting a cell is a `Figure`/`Div` only (grep `_dash_layout_cell` and `isinstance(` in test/test_layout*.py; flip to admit `Column` with a `Flipped:` line).

Parity corpus: `_case("scatter table", [plot_for("scatter")], go={"table": "on"})`, `_case("by table", [plot_for("scatter")], go={"table": "on", "by": "foreign"})` and `_move_case("scatter table, dropdown to Foreign", _MOVES[0], [plot_for("scatter")], go={"table": "rows(20)"})` appended to CORPUS and MOVE_CORPUS (R8). Release (Chrome): `TestTheTableFollowsAMove::test_by_table_follows_a_move` (saved) beside the two existing Chrome tests.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| option declared, spec key, refusals | cscript U48-1..6 | none | n/a |
| table model, columns, text, view, cap, toggle, by() table | pytest test_data_table.py | none | yes |
| text frame cost at 100k rows | pytest test_estimator_cost.py | none | -- |
| text columns absent without the option; CSV omits them | pytest | none | yes |
| follows a move; toggle renders rows | Chrome (release tier) | none | yes |
| copy lists, maps | existing guards | none | yes |
| layout parity | test_mode_parity.py entries | none | yes |

Acceptance: **AC-48.1** every stub green; **AC-48.2** U48-1..6 pass under the console binary; **AC-48.3** `make test`-tier files touched (test_layout*, test_abbreviations, test_mode_parity collection) green; **AC-48.4** the help names `table`.

## Tasks

**Commit boundary.** 48-01..48-04 form the one commit `Draw a folded, formatted data table under a graph given table (WP-31 H2t)`.

<task type="auto" id="48-01">
  <name>Write the failing data-table tests</name>
  <files>test/test_data_table.py, test/test_mode_parity.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_data_table.py with the stubs under "TDD test stubs" (classes TestATableIsDrawn, TestTheColumns, TestTheText, TestTheView, TestTheCap, TestTheToggle, TestByGraphs, TestTheTableFollowsAMove marked release, and test_the_index_filter_drops_out_of_range_indices; the node test of TestTheView through test/js_runner.py) and append test_table_text_frame_under_two_seconds_at_100k to test/test_estimator_cost.py (a fourth file, named here). Render through conftest.render_models on an auto spec with graph_options {"table": "on"} and read the layout root; the served arm builds the app through the existing test helper in test/test_server_link.py (_served_doc) and walks doc.roots. Append the two parity entries to CORPUS and MOVE_CORPUS, and the S48 block to test/test_wp31_truth.cscript above the marker line with cases U48-1..U48-4 (each `capture dash scatter mpg weight, table ...` then `_dash_serve_spec` and a python: block reading graph_options["table"]; the refusals check _rc == 198 and cert_log_has the sentence). Run `python3 -m pytest test/test_data_table.py -q` against the unmodified tree and save its output to <scratch>/48-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_data_table.py -q 2>&1 | tail -3 prints "failed" with every test red (ImportError on _dash_data_table or AssertionError); test -s <scratch>/48-01-failure.txt]]></verify>
  <done>The regression tests exist, fail at 6370ca4, and their failure text is saved.</done>
</task>

<task type="auto" id="48-02">
  <name>Declare table in dash.ado and Mata</name>
  <files>dash.ado, dash_parse.mata, test/test_option_validation.cscript</files>
  <action><![CDATA[First run D-48a's 6-line syntax probe through scripts/stata_slot.sh (the `_u48probe` program fed `table`, `table(rows(5))`, `table table(x)`, `table()`; rc and output to <scratch>/s48/syntax-probe.log) and choose the declaration form it supports (the two-declaration idiom, else the single `TABle(string asis)` with `table(on)` as the bare form); record the choice in the commit body. Then apply TR-48.1 (the chosen declaration(s) in both parsers, the fold, the sreturns), TR-48.2 (_dash_table_check after _dash_line_check, called beside it), TR-48.3 (append ` table` to the seven key lists at :5776, :6714, :6748, :6849, :6924, :6956, :7339 and add dash_max_table_rows beside dash_max_added_text in the limits reader) and TR-48.4 (_dash_rep_unique). Add _dash_table_check to _dash_require_mata's _needed list only if it is a Mata function (it is an ado program: do NOT add it; add it to test/program_coverage_map.py COVERAGE["dash.ado"]). Append U48-5 and U48-6 to test_option_validation.cscript under its last block. Run the two cscripts through scripts/stata_slot.sh with a two-line driver each (global dash_nobrowser 1).]]></action>
  <verify><![CDATA[Both drivers' logs end with the scripts' PASS summary and no FAIL line; python3 -m pytest test/test_abbreviations.py -k seven_graph_key_lists -q prints 1 passed; python3 -m pytest test/test_program_coverage_map.py -q passes]]></verify>
  <done>dash writes graph_options["table"] from bare table and table(rows(#) open), refuses the other forms, and the key lists agree.</done>
</task>

<task type="auto" id="48-03">
  <name>Build the table in both renderers</name>
  <files>dash_render.py, test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[Apply TR-48.5..TR-48.11: the two constants after _DASH_STALE_STATUS_HTML (:1910), the table_rows limit row, the four shared functions after _dash_hover_layer_vars (:40079) with TR-48.7's format-once rule and TR-48.8's first-N-drawn IndexFilter and tags, the _dash_layout_cell replacement and facet-branch wrap (TR-48.9), the saved call sites in _build_sources_and_figures (plain and by() graphs) and the served calls in _dash_figure_for (TR-48.10, D-48d), the text-frame call in both modes (TR-48.7), the copy-list entries at the R2 anchors, and the function_test_map entries. Make _layout_tree unwrap the table Column (TR-48.9). Run test/test_data_table.py (not the Chrome class), test/test_estimator_cost.py -k table_text_frame, test/test_statistical_helpers.py -k CarriesEveryName, test/test_layout.py, test/test_csv*.py and test/test_mode_parity.py -k "table" with DASH_TEST_TIER=batch.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_data_table.py -q -m "not release" prints all passed; python3 -m pytest test/test_statistical_helpers.py -k CarriesEveryName -q passes; DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k table -q passes]]></verify>
  <done>Both renderers draw the folded, formatted, capped table bound to the figure's source and view.</done>
</task>

<task type="auto" id="48-04">
  <name>Certify, document and commit H2t</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Run DASH_TEST_TIER=release python3 -m pytest test/test_data_table.py -m release -q when Chrome is present (skip is allowed, say so in the body); rerun the S48 truth block driver. Add the {marker:table} paragraph to dash.sthlp after hover() and the Standalone-vs-server row. Replace the <!-- WP-31 H2t --> CHANGELOG marker under "### Fixed in WP-31" with "Graphs take a table option: a folded, sortable data table of the drawn rows in Stata's display formats, in both modes (WP-31, H2t)". Close BUGS.md "Dashboard extensions: per-graph data table" (Resolution per BRIEF; no residual: by() graphs draw one table under the grid, D6), rewrite the GAPS3 H2t Tracked line to the Closed form with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha). Commit on wp31-s48 with the body forms (Regression:, Fixture: none, BUGS.md:, GAPS3:) and the saved failure text first.]]></action>
  <verify><![CDATA[git log -1 --format=%s prints "Draw a folded, formatted data table under a graph given table (WP-31 H2t)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q passes]]></verify>
  <done>H2t is committed with help, CHANGELOG, BUGS.md and GAPS3 updated.</done>
</task>

## Section completion criteria

- `dash scatter mpg weight, table` gives a cell `column(figure, Toggle, DataTable, Div)` in both modes; without `table` the cell is the figure; `by(foreign) table` gives `column(grid, Toggle, DataTable, Div)` with a leading panel column (D6).
- The table's cells read as Stata displays the variable; it follows a move in both modes (Chrome test or a documented skip).
- U48-1..6 pass; the copy-list guard, the key-list guard and the maps are green; one commit `(WP-31 H2t)`.

## Notes

- **Renderer order.** The text frame must be built BEFORE `_collect_plot_vars` builds sources (saved) and before `_dash_layer_source` (served), or the columns are missing from the source and the table shows blank cells.
- **Copy lists (R2, A7):** constants after `_DASH_STALE_STATUS_HTML`; functions after `_dash_reference_lines`. Misspelling fails `TestTheServedAppCarriesEveryName`.
- **CSP (M11):** the toggle's code is a `CustomJS`; the note is a `Div` with escaped fixed text; no raw `<script>`/`<style>`. test_csp.py stays green.
- **Security:** column titles are variable labels through `html.escape` is NOT needed for `TableColumn.title` (BokehJS sets textContent), but `Div.text` is innerHTML -- the note is fixed text. Variable names pass `_dash_is_stata_name` before becoming field names.
- **python_exec hazard:** the cscript drivers set `global dash_nobrowser 1`; run through `scripts/stata_slot.sh` only.
- **Commit body line forms:** `Regression: test/test_data_table.py::TestATableIsDrawn::test_saved_cell_is_a_column_of_figure_toggle_table_note -- failed at 6370ca4 with ImportError: cannot import name '_dash_data_table'`; `Flipped: <node> -- <old> was wrong because a table graph's cell is a Column`; `BUGS.md: "Dashboard extensions: per-graph data table" (closed)`; `GAPS3: H2t Tracked`.
- **Decided (DECISIONS):** D6 -- one table under a by() grid with a panel column (D-48d, no residual); A29 -- the cap is the first N drawn rows and S51's brush(filter) rewrites the table's `IndexFilter.indices` (D-48e). **For ratification:** the option's name (`table`), its level (graph) and the declaration form the 48-02 probe selects (D-48a).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 48-01 appends the one H2t block.
