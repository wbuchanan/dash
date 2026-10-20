# Section 51: Several link groups, brush as a filter, brushing bars and histograms

> Part of: WP-31 · GAPS3 rows: H2l (H2 link/brush part; H1's bar/histogram selection and concurrent-brush intersection, E5/E9 notes) · Risk: red · Batch: 17 · Depends on: 01, 48 · Blocks: 52, 60 · Tasks: 4, 1 commit · Case-id prefix: U51

## Overview

**What is wrong today.** GAPS3 H2 (GAPS3.md:239): "one link group; brush cannot act as a filter". GAPS3 H1 (:238): "A box or lasso selection on bars or histograms drives nothing; concurrent brushes are not intersected on the saved page (served intersects)". `link()` is one `LINK(string)` option (dash.ado:941, :9712) whose names `_dash_link_names` (dash_render.py:35539-35555) flattens into ONE list; both renderers build ONE shared `ColumnDataSource` for those names (saved `_build_sources_and_figures`, served template :49022-49080 `shared_source`). A brush on a linked graph only dims the other graphs' non-selected glyphs (`_dash_dim_nonselection`, :42434) and recomputes `update(brush|both)` KPI cards (`_BRUSH_JS`, :25467-25490; served `_make_brush_cb`, :50477ff). A histogram's or bar's source holds bins, so `box_select` on it selects bin indices that no script maps to rows. Two brushes on two sources each recompute the cards from their own selection; the served app intersects them (`_brush_rows`, :50049-50066), the saved page does not.

**After this section** `link()` may be given several times (`link(g1 g2) link(g3 g4)`), each copy a group with its own shared source in both modes; `dash build, brush(filter)` makes a selection on any graph of a group hide the non-selected rows of the group's other graphs (alpha 0, the glyph's own value restored on clearing) and recompute every KPI card the group reaches from the selected rows; a selection on a bar, rbar or histogram layer is translated bin → rows through the layer's `_dash_agg_rows` members and applied to the raw source's selection; and on the saved page concurrent brushes on different sources are intersected by row identity exactly as the served app intersects them.

**Why one section.** All four live in the link/brush machinery: `_dash_link_names`, the shared-source construction in both modes, `_BRUSH_JS`, `_wire_brush_callbacks` (dash_render.py:45345; REVIEW-4 R4-18), `_make_brush_cb` and `_dash_dim_nonselection`. The index names S51 batch 17's owner of them.

**Test order and commit rule.** One cycle, one commit `(WP-31 H2l)`: 51-01 regression tests red; 51-02 link groups (dash.ado, Mata, both renderers); 51-03 brush-as-filter, bin→rows and the intersection (saved and served); 51-04 verification, help, close, commit. GAPS3 H1's bar/histogram and intersection clauses are closed HERE under the H2l entry (DECISIONS A21, REVIEW-4 R4-10): S01 opens ONE `H1` entry (S52's: errors and sliders) and the `H2l` entry's text already names "a brush on bars or histograms drives nothing and concurrent brushes are not intersected"; there is no `H1b` entry, no second commit and no second Tracked line. S51's H2l Tracked line ends "; GAPS3 H1's bar/histogram selection and intersection clauses are closed here."; S52's H1 Resolution says the selection clauses are closed by H2l (section 51).

### Section decisions (binding on the executor)

- **D-51a. Repeated `link()` = several groups; the spec joins them with ` || `.** dash.ado's `_dash_parse_graph_opts` and `_dash_build`/`_dash_serve` syntaxes keep `LINK(string)`; a Mata scanner `_dash_extract_links(link_out, cmd_out)` modelled on `_dash_extract_filters` (dash_parse.mata:4212ff) harvests every top-level `link(...)` before `syntax` runs and joins them with ` || ` into `build_options["link"]` (`"g1 g2 || g3 g4"`). `_dash_link_refusal` is applied per group and additionally refuses a name in two groups (`link() name 'g2' is in more than one group`) and `_all` beside any other group (`link(_all) links every graph; give it alone`). A single `link()` writes no separator, so every existing spec and test reads unchanged.
- **D-51b. `_dash_link_names` keeps its flat return; `_dash_link_groups` is new.** `_dash_link_groups(link, graph_names) -> list[list[str]]` splits on `||`, applies `_dash_link_names`'s rules per group (`_all` → every graph, one group), drops empty groups and names not in `graph_names`, and returns groups of at least two names (a one-name group is not a link; a note is printed once). `_dash_link_names` is rewritten as the flattened union of `_dash_link_groups` so its five callers (:2230, :41444, :44916, :47877, :49022) behave as today for one group. test_mode_parity.py's `ALLOWED` is untouched (R8): "linked graphs share one source" stays true per group.
- **D-51c. One shared source per group.** Saved: `self.sources[name]` for every member of group k is one `ColumnDataSource` (today's construction, repeated per group; the group index is `fig._dash_link_group = k`). Served: `shared_source` becomes `_shared_sources: list` and `_EMBED_LINK` a list of row masks (`_EMBED['link_rows']` becomes a list; dash.ado's embed plan writer emits one mask per group); every read of `shared_source`/`_EMBED_LINK` in the template (:49044, :49073-49079, :50065, :50315 and the `_shared` argument of `_make_filter_cb`) loops over the list. The filter mask of a group is the AND of the widgets that apply to any member (`_dash_filter_applies(..., members=group)`, unchanged).
- **D-51d. `brush(filter)` is a build option.** `dash build`/`dash serve` syntax gains `BRush(string)` with values `highlight` (today's behaviour, default) and `filter`; any other word r(198) `dash build: brush() takes highlight or filter`. The spec carries `build_options["brush"]`. Under `filter`: `_dash_dim_nonselection(fig, alpha=0.0)` on every linked figure (hidden non-selected rows; `nonselection_glyph` also `line_alpha 0`), and every KPI card whose `update` is `filter` behaves as `both` for the group's selections (saved: the KPI config row gets `"brush_filter": true` and `dash_apply_kpis` is called from `_BRUSH_JS` for every card; served: `_make_brush_cb` recomputes every card). No per-graph table/other-group effect: a selection masks its own group only. (Alternative considered and rejected: a per-KPI `update(brush)` already exists; a build-wide switch is what "brush as a filter" means.)
- **D-51e. Bin → rows.** A bar/rbar/histogram renderer tagged with `_dash_agg_rows` (:18056, :18414; `GlyphMapper._agg_member_ids`) gets a per-bin column `__dash_bin_rows` on its aggregate source: a list of the `__dash_row__` ids each bin counts (the mapper knows the bin edges and the member rows; write the column in `map_histogram`/`map_bar` where `_dash_agg_rows` is set -- `_dash_bin_members(edges, x_values, row_ids)` shared helper). The saved page's refit rewrites the bins on a filter move, so the column is recomputed there too by a JavaScript twin, `dash_bin_members(edges, xs, ids)`, that S52 (batch 17's `_FILTER_JS` editor) inserts verbatim from the code text TR-51.6 supplies (S52 D-52.e; DECISIONS A28, REVIEW-4 R4-07; M25: both twins); S51 writes no JS constant, so S52 builds against the batch-17 base. `_BRUSH_JS` begins: if `brush_source.data.__dash_bin_rows` exists, the selected bin indices are mapped to the union of their row ids, and the RAW source of the layer (`raw_source` arg) gets `selected.indices = positions of those ids`; the raw source's own selection handler then runs the usual path. Served: `_make_brush_cb` does the same mapping in Python with the registry `agg_sources[(gname, pi)]`'s `_dash_agg_rows`.
- **D-51f. Concurrent brushes intersect by row identity on the saved page.** A page-level `ColumnDataSource` named `dash_brush_state` holds one COLUMN per brushed source, keyed by `src_key`, each column one row holding that source's selected id array (`data[src_key] = [ids]`; every column has length 1, so BokehJS's length check holds); no JSON (REVIEW-4 R4-34: re-serialising every brushed source's id list on each selection event is ~600 kB per drag step at 100,000 rows). `_BRUSH_JS` writes its own column (an empty array on clear) and computes the KPI rows as the intersection of every non-empty column (none non-empty → every row, today's fallback), then calls `dash_apply_kpis`. Under `brush(filter)` the hidden rows of a group's figures are the complement of that intersection restricted to the group. The served twin is the existing `_brush_rows` logic (:50049-50066) extended to the per-group sources.

## Risk: [red] -- the shared-source construction changes in both modes, the brush script grows, and three brush behaviours interact

**Why.** `shared_source` is read in a dozen template lines; a missed one breaks every linked served dashboard. `_BRUSH_JS` runs on every selection of every brushable source (raw and derived copies, :45394-45420). Bin→rows adds a column of lists to aggregate sources (serialisation size).

**Risk factors.** (1) A missed `shared_source` read; (2) `__dash_bin_rows` on a 1,000-bin histogram of 100,000 rows is 100,000 ids once (fine) but is rewritten on every redraw (served) and must be recomputed by the saved JS refit: after a saved filter move the histogram branch refits with NEW edges, so a stale map would send bin j to the rows of the OLD bin j -- wrong rows, not merely absent ones (R4-07); S51 cannot edit `_FILTER_JS` (S52 is batch 17's editor); (3) `brush(filter)` hiding rows on a shared source hides them on the brushed graph too (its own non-selected glyphs); (4) KPI cards with `update(filter)` recomputed from a brush change meaning under `brush(filter)`.

**Mitigation.** (1) `grep -n "shared_source\|_EMBED_LINK" dash_render.py` must print only list-aware lines after 51-02 (verify step); (2) the JS twin (DECISIONS A28): S52 inserts `function dash_bin_members(edges, xs, ids)` between `dash_kernel` and the agg_sources comment and, in the histogram and bar refit branches after the bins are written, `if (src.data.__dash_bin_rows !== undefined) src.data.__dash_bin_rows = dash_bin_members(edges, xs, ids);`; S51 TR-51.6 supplies the code text and `test_members_agree_with_numpy_histogram` gains a node arm, xfail until S52's twin lands (flipped by S52's 52-05 or the merger, S52 D-52.e); the Chrome test covers one move then one brush. Fallback if the twin is refused: the refit sets `__dash_bin_rows = null` and `_BRUSH_JS` prints the stale cue for a bin selection after a move; (3) that is the filter semantics: the brushed graph shows the selection only (documented in help); (4) help sentence under `brush(filter)`: "every card follows the selection".

## Dependencies

- **Depends on: 01, 48** (the table's `IndexFilter` and `dash_table_cap=` tag that TR-51.8 rewrites). **Blocks: 52** (the `dash_bin_members` code text), **60** (H6's saved-JS move oracle and brush parity entries build on the brush state model).
- **Parallel batch: 17** with S50 (KPI statistics: `_kpi_statistic`, `dash_apply_kpis`' arithmetic, `_compute_kpi`) and S52 (`_FILTER_JS` wrapper, slider `value_throttled`, the `document_ready` `_hooks` list). Recorded R12 exception (DECISIONS A28): S51 edits `_BRUSH_JS`, `_wire_brush_callbacks` (the new args and the state CDS -- not `_need` :45400-45401, S50's two lines, and not the `CustomJS(args=..., code=...)` construction, S52's), `_dash_link_names` and neighbours, `_dash_dim_nonselection`, the saved source construction, the template's link/brush blocks. S51 does NOT edit `_FILTER_JS`. Merge order 50 → 51 → 52.

## Evidence

### One link list

```python
35549    if isinstance(link, (list, tuple)):
35550        names = [str(x) for x in link]
35551    else:
35552        names = str(link or "").replace(";", " ").split()
35553    if "_all" in names:
35554        return [n for n in graph_names if n]
35555    return names
```

test/test_linking.py::TestLinkedBrushing::test_a_semicolon_does_not_create_a_second_link_group (:167) pins that `;` is a blank, not a group separator -- unchanged (groups come from repeated `link()`, joined with ` || `).

### Served shared source

Template :49022 `linked_names = set(_dash_link_names(...))`, :49044 `_EMBED_LINK = _EMBED['link_rows'].to_numpy(dtype=bool)`, :49073 `_ldf = df[_EMBED_LINK]`, :49079 `shared_source = ColumnDataSource(_shared_data)`, :50065 `_brush_rows[id(shared_source)] = df.index[_EMBED_LINK]`, :50315 `_shared_fdf = _df_ref[_shared_mask & _EMBED_LINK]`.

### The brush

`_BRUSH_JS` (:25467-25490): `idx = cb_obj.indices`, `sel` built from `brush_source.data`, `dash_apply_kpis(sel, kpi_config, kpi_divs, ROW_ID)`. Wired in `_wire_brush_callbacks` (:45345-45420; `_need` :45400-45401) on every raw source and every derived copy holding the KPI variables and `__dash_row__`. Served: `_brush_on`, `_brush_rows` (:50049-50066), `_make_brush_cb` (:50477ff) with `_on_selection_change(attr, old, new)`.

### Bins know their rows

`r._dash_agg_rows = self._agg_member_ids(source, view)` at :18056 (histogram) and :18414 (bar); `_agg_member_ids` (:15675-15697) returns the member `__dash_row__` ids of the whole layer (not per bin). `_DASH_FIGURE_TOOLS` (:35259) includes `box_select,lasso_select` on every figure, bars and histograms included.

### Existing tests that pin today's behaviour

- test/test_linking.py::TestLinkedBrushing::test_linked_renderers_have_nonselection_alpha (:141) -- alpha `_NONSELECTION_ALPHA` under highlight; add a `brush(filter)` arm asserting 0.0, keep the default arm.
- test/test_kpi_brush.py::TestTheShippedBrushJsActuallyComputes (:238-335) -- runs `_BRUSH_JS` under node with `brush_source`, `kpi_config_json`, `kpi_divs`; the script gains `brush_state`, `raw_source`, `group_json` args -- the test's arg dict is extended (flip with reason, not deleted).
- test/test_server_link.py::TestLinkSharesASource (:92-117) -- one group; add a two-group class.
- test/test_mode_parity.py `ALLOWED["linked graphs share one source"]` -- untouched.

## User stories

- **US-51.1** As an author I want `link(g1 g2) link(g3 g4)` so that two pairs brush independently.
- **US-51.2** As a reader I want `brush(filter)` so that selecting points in one graph shows only those rows elsewhere and in the cards.
- **US-51.3** As a reader I want to drag over histogram bars and see the cards and linked graphs follow the rows in those bins.
- **US-51.4** As a reader I want two selections on two graphs to act together on the saved page as they do when served.

## Business requirements

- **BR-51.1** Each `link()` copy is a group; a graph in two groups, or `_all` beside a group, is refused in one sentence.
- **BR-51.2** A selection acts within its group: the group's other graphs dim (highlight) or hide (filter) their non-selected rows; cards the group reaches recompute.
- **BR-51.3** A selection on bars or histogram bins selects the rows those bins count.
- **BR-51.4** Selections on several sources intersect by observation in both modes; clearing one restores the others' effect.

## Technical requirements

- **TR-51.1 Stata.** `_dash_extract_links(link_out, cmd_out)` in dash_parse.mata (after `_dash_extract_filters`; header index entry; `_dash_require_mata` `_needed` in alphabetical place; program_coverage_map `"dash_parse.mata": {"_dash_extract_links": ("test_wp31_truth.cscript:U51-1", ...)}`); called in `_dash_build` and `_dash_serve_spec` before `syntax` exactly where `_dash_extract_filters` is called; `link` then holds the joined text. `_dash_link_refusal` iterates groups split on `||` (new helper `_dash_link_split`) and adds the two refusals of D-51a. `dash build`/`dash serve` syntaxes gain `BRush(string)` with D-51d's refusal; `build_options` JSON gains `"brush":"`_brush_esc'"`; the embed plan writer emits `link_rows` as a list of masks (one per group; the Python reader `_EMBED['link_rows']` accepts the old single mask as a one-element list for hand-built specs).
- **TR-51.2 `_dash_link_groups`** (new, shared, after `_dash_link_names`; copy list after `_dash_reference_lines`): per D-51b. `_dash_link_names` body becomes `return [n for g in _dash_link_groups(link, graph_names) for n in g]` with the old `_all`/`;` rules inside `_dash_link_groups`.
- **TR-51.3 Saved sources.** In `_build_sources_and_figures` (grep `linked = set(_dash_link_names(`, :41444 and :44916): replace the single shared-source branch by a loop over `_dash_link_groups`, building one source per group and assigning it to every member; `fig._dash_link_group = k`; `_build_filter_widgets`'s `fsource` (:45470) becomes the first group's source.
- **TR-51.4 Served sources.** Template: `_link_groups = _dash_link_groups(...)`; `_EMBED_LINKS = [m.to_numpy(dtype=bool) for m in _EMBED['link_rows']]`; `_shared_sources = [ColumnDataSource(...) for each]`; every former `shared_source` read loops (`for _k, _ss in enumerate(_shared_sources)`), `_make_filter_cb(_shared=...)` takes the list, `_dash_move_apply` step 2 writes each group's source once with `_df_ref[_shared_mask_k & _EMBED_LINKS[k]]`. Verify: `grep -n "shared_source\b" dash_render.py` prints nothing after the edit (the name is retired).
- **TR-51.5 `brush(filter)`.** `_dash_brush_mode(build_options) -> "highlight"|"filter"` (shared). Both modes: `_dash_dim_nonselection(fig, alpha=0.0 if mode == "filter" else _NONSELECTION_ALPHA)` where it is called today (grep `_dash_dim_nonselection(` in both the saved renderer and the template). KPI config rows gain `"brush_filter": mode == "filter"`; `dash_apply_kpis` skips a card only when `k.update === 'filter' && !k.brush_filter` on the brush path (today's three-valued rule otherwise). Served `_make_brush_cb` recomputes every card when the mode is `filter`.
- **TR-51.6 Bin rows.** `_dash_bin_members(edges, xs, row_ids) -> list[list[int]]` (shared, after `_agg_member_ids`' module neighbours; copy list): for bin j the ids with `edges[j] <= x < edges[j+1]` (last bin inclusive), the rule `np.histogram` applies (the histogram mapper's own binning function is reused so the two agree -- read `map_histogram`'s edge computation and call the same). `map_histogram` and `map_bar` write `source.data["__dash_bin_rows"] = members` where they set `_dash_agg_rows` (:18056, :18414); the served redraw (`_dash_redraw_for`) returns the mapper's source, so the column is rewritten on every served move with no extra code. **The JS twin's text (for S52 to insert, A28):** `function dash_bin_members(edges, xs, ids) { const k = edges.length - 1; const out = []; for (let j = 0; j < k; j++) out.push([]); for (let i = 0; i < xs.length; i++) { const x = xs[i]; if (x === null || x === undefined || Number.isNaN(x) || x < edges[0] || x > edges[k]) continue; let j = k - 1; if (x < edges[k]) { let lo = 0, hi = k - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (edges[m] <= x) lo = m; else hi = m - 1; } j = lo; } out[j].push(ids[i]); } return out; }` (bin j holds `edges[j] <= x < edges[j+1]`, the last bin inclusive -- `np.histogram`'s rule, so the two twins agree). S52 inserts this text verbatim in `_FILTER_JS` between `dash_kernel` and the agg_sources comment (S52 D-52.e); S51 writes NO module constant for it (S52's worktree is cut from the batch-17 base and cannot read one). `TestBinRows::test_members_agree_with_numpy_histogram` gains a node arm running `js_runner.run_filter_js_block`'s helper slice (which carries `dash_bin_members` once S52 lands) against `_dash_bin_members` on the same edges, xs and ids, marked `xfail(strict=False, reason="S52 inserts the twin")` and flipped by S52's 52-05 when S51's file is in its worktree, else by the merger after S52 lands (batch-17 merge note).
- **TR-51.7 `_BRUSH_JS`.** New args: `raw_source` (the layer's raw source, or null), `brush_state` (the page's `dash_brush_state` CDS), `group_json` (`{"figs": [...ids], "group": k}` -- not needed for KPIs; omit), `src_key` (a string id). Code, prepended: `if (brush_source.data.__dash_bin_rows && raw_source) { const bins = cb_obj.indices || []; const ids = new Set(); for (const b of bins) for (const r of (brush_source.data.__dash_bin_rows[b] || [])) ids.add(r); const rid = raw_source.data[ROW_ID] || []; const pos = []; for (let i = 0; i < rid.length; i++) if (ids.has(rid[i])) pos.push(i); raw_source.selected.indices = pos; return; }` then the intersection: `const own = idx.map(i => brush_source.data[ROW_ID][i]); const st = Object.assign({}, brush_state.data); st[src_key] = [own]; brush_state.data = st; const lists = Object.keys(st).map(k => st[k][0]).filter(l => l && l.length); let keep = null; for (const l of lists) { const s = new Set(l); keep = keep === null ? s : new Set([...keep].filter(x => s.has(x))); }` (one column per source, each one row holding the id array; no JSON, D-51f) and `sel` is built from `brush_source` rows whose id is in `keep` (every row when `keep === null`). The page-level `dash_brush_state` CDS (`ColumnDataSource(data={})`) is created once in `_wire_brush_callbacks` and passed to every brush callback; `src_key` is `"s" + str(id(src))`.
- **TR-51.8 Hiding under filter (saved).** The filters are BUILT IN PYTHON and MUTATED in JS (REVIEW-4 R4-06, DECISIONS A28): the served bundle is `bokeh, bokeh-gl, bokeh-widgets, bokeh-tables` with no `bokeh-api`, so `new Bokeh.IndexFilter(...)` has no constructor on the global. At build, under `brush(filter)`, every renderer of a linked figure gets `view.filter = IndexFilter(indices=<its kept positions>)` (the positions `GlyphMapper._view_mask` keeps; every position when the renderer has no mask), and `r.view.tags = ["dash_brush_view", "qual=<the __dashq<k> marker column name or empty>"]`. Appended to `_BRUSH_JS` under `brush_filter`: for each figure of the brushed source's group (arg `group_figs`), for each renderer with a `dash_brush_view` tag, set `r.view.filter.indices = pos` where `pos` are the kept positions in that renderer's source (same-source: positions whose `ROW_ID` is in `keep`; a derived copy: likewise over its own `ROW_ID` column) -- a property write re-runs `compute_indices`; `keep === null` restores the full list: every position whose qualifier marker column (the `qual=` tag's column, when named) is nonzero, else every position of the source's current length (`src.get_length()`), so a restore after a saved filter move lists the rewritten rows. No model constructor in JS; no `_DASH_BOKEH_INTERNALS` entry. **S48's table follows too (R4-05a, A29):** arg `tables` holds each group figure's `fig._dash_table[1]` (the `DataTable`) when present; its `view.filter.indices` is set to `pos.slice(0, cap)` with `cap` read from the table's `dash_table_cap=<n>` tag, and restored to the first `cap` kept positions on clear. (A `view.filter` write hides rows outright; `nonselection_glyph` alpha 0 is then unnecessary but harmless -- keep both, the alpha for the brushed figure's own glyphs.) Served twin in `_make_brush_cb` (the served app rebuilds its sources, so it writes `IndexFilter.indices` the same way).
- **TR-51.9 Maps and copy lists.** function_test_map: `_dash_link_groups`, `_dash_brush_mode`, `_dash_bin_members`, `_dash_link_split`; copy list after `_dash_reference_lines` (after S48/S49/S50 entries if present); no new constant. program_coverage_map: `_dash_extract_links`, `_dash_link_split`.
- **TR-51.10 Help.** dash.sthlp `{title:Linking and Brushing}` (:1585ff): repeated `link()`, `brush(filter)`, bars/histograms, intersection; the Standalone-vs-server table rows.

## Boundaries

- No `_FILTER_JS` edit (S52 owns batch 17's; the derived-copy loop copies ROWS of raw sources; aggregate sources are rewritten by the estimator branches, where S52 inserts the `dash_bin_members` twin from TR-51.6's text, D-51e/A28).
- No `CustomJS(...)` construction change in `_wire_brush_callbacks` (S52 wraps it) and no `_need` change (S50).
- No KPI arithmetic change (S50).
- No new tool on `_DASH_FIGURE_TOOLS`.
- No change to `_dash_filter_applies`/`_dash_widgets_for` semantics (members = the group).

## Stata truth

None from twoway. Truth block `* ==== S51 H2l: link groups and brush ====`: `U51-1` `link(g1 g2) link(g3 g4)` writes `"link":"g1 g2 || g3 g4"`; `U51-2` `link(g1 g2) link(g2 g3)` r(198) "in more than one group"; `U51-3` `link(_all) link(g1 g2)` r(198); `U51-4` `brush(filter)` writes `"brush":"filter"`; `U51-5` `brush(bogus)` r(198); `U51-6` a single `link(g1 g2)` writes no `||` (regression guard). test_option_validation.cscript: `U51-7` `brush()` on `dash serve` r(198) same text.

## TDD test stubs

Regression (red at 6370ca4), file `test/test_link_groups_brush.py`:
- `TestLinkGroups::test_two_groups_two_sources_saved`, `::test_two_groups_two_sources_served`, `::test_a_name_in_two_groups_is_refused_by_the_reader` (Python side drops the second occurrence with a note), `::test_one_group_is_unchanged` (same sources as today), `::test_flat_names_are_the_union`.
- `TestBrushFilter::test_nonselection_alpha_is_zero_under_filter_both_modes`, `::test_highlight_default_keeps_the_alpha`, `::test_every_card_follows_under_filter` (node: `_BRUSH_JS` with `brush_filter` cards), `::test_served_cb_recomputes_every_card`.
- `TestBinRows::test_histogram_source_carries_bin_members`, `::test_bar_source_carries_bin_members`, `::test_members_agree_with_numpy_histogram` (Python arm, and the xfail node arm over the `_FILTER_JS` helper slice, TR-51.6), `::test_the_script_maps_bins_to_raw_rows` (node), `::test_served_cb_maps_bins_to_rows`.
- `TestBrushFilter::test_the_view_filters_are_python_built` (every linked renderer under `brush(filter)` has an `IndexFilter` and the `dash_brush_view` tag), `::test_the_script_mutates_indices_and_restores` (node: `view.filter.indices` after a selection equals the kept positions; after clearing, the full list), `::test_the_table_view_follows_a_brush` (node: a `table` figure's DataTable `indices` equals the kept positions capped by its `dash_table_cap=` tag).
- `TestIntersection::test_two_sources_intersect` (node: two runs of `_BRUSH_JS` with a shared `brush_state`, the cards equal the intersection's mean), `::test_clearing_one_restores_the_other`, `::test_the_state_holds_one_column_per_source_and_no_json`, `::test_the_served_app_agrees` (its `_brush_rows` path).
- Release (Chrome): `TestInChrome::test_box_select_on_a_histogram_then_a_scatter` on the saved page through `_CspProbe` (`view.export`-free: read `source.selected.indices` lengths and a card's text).
- Flips: test_kpi_brush.py:238-335 arg dict extended (`Flipped:` line); test_linking.py:141 gains the filter arm (not a flip, an addition).

cscript cases U51-1..U51-7 (above). Parity: `_case("two link groups", [..4 graphs..], bo={"link": "g1 g2 || g3 g4"})`, `_case("brush filter", [...], bo={"link": "_all", "brush": "filter"})` (CORPUS; the layout tree and the glyph alphas are compared), `_move_case("two link groups, dropdown to Foreign", _MOVES[0], ..., bo={"link": "g1 g2 || g3 g4"})`.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| link() repeats, brush() words | cscript U51-1..7 | none | n/a |
| groups → sources | pytest | none | yes |
| brush filter alpha, cards | pytest + node + served doc | none | yes |
| bin → rows | pytest + node + served doc | none | yes |
| intersection | node + served doc | none | yes |
| end to end | Chrome (release) | none | saved |
| parity | corpus entries | none | yes |

**AC-51.1** every stub green; **AC-51.2** U51-1..7 pass; **AC-51.3** test_linking.py, test_server_link.py, test_kpi_brush.py, test_csp.py green; **AC-51.4** `grep -c "shared_source\b" dash_render.py` prints 0.

## Tasks

**Commit boundary.** 51-01..51-04 form the one commit `Link several groups, brush as a filter, brush bars and histograms, intersect brushes (WP-31 H2l)`.

<task type="auto" id="51-01">
  <name>Write the failing link and brush tests</name>
  <files>test/test_link_groups_brush.py, test/test_mode_parity.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_link_groups_brush.py with the classes above (node tests build the brush code string the way _wire_brush_callbacks does, from dash_render._DASH_FMT_JS, the helper slice, the pctl slice and _BRUSH_JS, and run it through test/js_runner.py with the arg objects; the served arms use test/test_server_link.py's _served_doc helper). Append the parity entries and the S51 truth block with U51-1..U51-6; U51-7 to test_option_validation.cscript. Run `python3 -m pytest test/test_link_groups_brush.py -q -m "not release"` on the unmodified tree and save to <scratch>/51-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The pytest tail prints failures only; test -s <scratch>/51-01-failure.txt]]></verify>
  <done>The regression tests exist and fail at 6370ca4.</done>
</task>

<task type="auto" id="51-02">
  <name>Build one source per link group</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[Apply TR-51.1 (the Mata scanner, the per-group refusals, brush(), the embed plan's list of link masks), TR-51.2 (_dash_link_groups, _dash_link_names rewritten as its union), TR-51.3 (saved sources per group) and TR-51.4 (served _shared_sources list; retire the name shared_source). Add the Mata names to _dash_require_mata's _needed list, the header index and program_coverage_map; the Python names to function_test_map and the copy list. Run test/test_link_groups_brush.py -k LinkGroups, test/test_linking.py, test/test_server_link.py, test/test_statistical_helpers.py -k CarriesEveryName, and the two cscript drivers through scripts/stata_slot.sh.]]></action>
  <verify><![CDATA[grep -c "shared_source\b" dash_render.py prints 0; python3 -m pytest test/test_link_groups_brush.py -k LinkGroups test/test_linking.py test/test_server_link.py -q passes; the cscript logs show U51-1..U51-7 PASS]]></verify>
  <done>Repeated link() copies make independent groups with one shared source each in both modes.</done>
</task>

<task type="auto" id="51-03">
  <name>Brush as a filter, bins to rows, intersection</name>
  <files>dash_render.py, test/test_kpi_brush.py, test/test_linking.py</files>
  <action><![CDATA[Apply TR-51.5 (_dash_brush_mode, alpha 0 under filter, brush_filter in kpi_config and dash_apply_kpis' skip rule, the served _make_brush_cb), TR-51.6 (_dash_bin_members written by map_histogram and map_bar; no JS constant), TR-51.7 and TR-51.8 (_BRUSH_JS prelude, intersection through the dash_brush_state CDS's per-source columns, Python-built IndexFilters with dash_brush_view tags mutated through view.filter.indices, the table views through the tables arg; _wire_brush_callbacks creates the state CDS and passes raw_source, brush_state, src_key, group_figs, tables, brush_filter -- editing its args and the state CDS only, not the CustomJS(...) construction nor _need) and the served twins. Flip test_kpi_brush.py's arg dicts with a Flipped line; add the filter arm to test_linking.py:141. Run test/test_link_groups_brush.py -m "not release", test/test_kpi_brush.py, test/test_kpi_values.py, test/test_csp.py.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_link_groups_brush.py test/test_kpi_brush.py test/test_kpi_values.py test/test_csp.py -q -m "not release" prints all passed]]></verify>
  <done>Selections act as filters when asked, bins select their rows, and concurrent selections intersect on the saved page as they do served.</done>
</task>

<task type="auto" id="51-04">
  <name>Verify in Chrome, document and commit H2l</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Run DASH_TEST_TIER=release python3 -m pytest test/test_link_groups_brush.py -m release -q (skip without Chrome, say so) and DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "link groups or brush filter". Edit the Linking and Brushing help paragraphs (TR-51.10). Replace the <!-- WP-31 H2l --> marker under "### Fixed in WP-31" with "link() may be repeated for several groups; dash build takes brush(filter); a box or lasso selection on bars or histogram bins selects their rows; concurrent selections are intersected on the saved page as when served (WP-31, H2l)". Close BUGS.md "Dashboard extensions: link groups and brush" (its Resolution names GAPS3 H1's bar/histogram selection and intersection clauses as closed here) and rewrite the H2l Tracked line to the Closed form with `commit pending` (DECISIONS A11), ending "; GAPS3 H1's bar/histogram selection and intersection clauses are closed here." (A21). No H1b entry exists; H1's own line is S52's. Commit on wp31-s51 with the body forms.]]></action>
  <verify><![CDATA[git log -1 --format=%s ends "(WP-31 H2l)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q passes]]></verify>
  <done>H2l is committed with help, CHANGELOG, BUGS.md and GAPS3 updated, its Tracked line naming H1's selection clauses as closed.</done>
</task>

## Section completion criteria

- Two `link()` copies give two shared sources in both modes; one copy is byte-identical to today's spec.
- `brush(filter)` hides non-selected rows in the group and every card follows; a histogram box-select selects its rows; two brushes intersect on the saved page (node and Chrome).
- U51-1..7 pass; flips carry reasons; one commit `(WP-31 H2l)`.

## Notes

- **Renderer order.** `_dash_bin_members` must be written in the mapper AFTER the bins are final and BEFORE `_agg_member_ids` is read; the served redraw returns that source, so the column travels.
- **Merge order (batch 17, A28):** S50, then S51, then S52. S50's two `_need` lines (:45400-45401) in `_wire_brush_callbacks`, S51's new args and state CDS, and S52's `CustomJS(code=_dash_js_guarded(...))` construction are three disjoint hunks of one function; S52 wraps `_FILTER_JS` at the :31459 assembly and inserts the `dash_bin_members` text of TR-51.6 (S51 does not touch `_FILTER_JS`). After S52 lands the merger flips S51's xfail node arm if 52-05 could not.
- **Copy lists (R2):** after `_dash_reference_lines`, following S48-S50's entries.
- **Security (M11):** `src_key` is `"s" + str(id(src))` (a letter and digits); `brush_state` holds integer arrays; `group_figs` and `tables` are models; no user text. `view.filter` writes mutate Python-built `IndexFilter.indices` (no constructor, no `Bokeh.Models.get`); nothing new reaches the CSP.
- **python_exec hazard:** cscripts via `scripts/stata_slot.sh`, `global dash_nobrowser 1`.
- **Commit body forms:** `Regression: test/test_link_groups_brush.py::TestLinkGroups::test_two_groups_two_sources_saved -- failed at 6370ca4 with AssertionError: g1 and g3 share one source`; `Flipped: test/test_kpi_brush.py::TestTheShippedBrushJsActuallyComputes::test_a_selection_gives_the_mean_of_the_selected_rows -- the arg set was wrong because the script now takes brush_state, raw_source and src_key`; `BUGS.md: "Dashboard extensions: link groups and brush" (closed)`; `GAPS3: H2l Tracked`.
- **Decisions for ratification:** `||` as the spec separator and repeated `link()` as the grammar (D-51a); `brush(filter|highlight)` as a build option (D-51d). **Decided:** the `dash_bin_members` JS twin inserted by S52 replaces the stale-map rule (A28, R4-07); H1's selection clauses close under H2l with no `H1b` entry (A21); Python-built filters mutated in JS (A28, R4-06).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 51-01 appends the one H2l block.
