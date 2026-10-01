# Section 14: Embed only the rows a consumer reads

> Part of: WP-29 · P0: P0.11 · Risk: red · Batch: 3 · Depends on: 02, 06, 07, 08, 11 · Blocks: 15 · Tasks: 16, 1 commit (P0.11) · Case prefix: ER

## Review amendments (design review of u10-excluded-rows, "sound with amendments") — binding; they override any conflicting text below

- **Ratified 01oct2026:** the maintainer answered index.md's "Decisions for maintainer ratification" (answer 4, verbatim: "Resolve the server app's index known gap."). SD1, SD2, SD4, SD5 and SD6 are ratified as written. SD3's served half is STRUCK: the served app's `index` column is no longer a residual. Every served source, the shared source, both placeholders, every per-layer source and every source a move or the redraw writes now numbers its rows with the saved page's dense ranks. One relabel of the served frame does this when the document is built (TR-14.18, A8 as rewritten below). Removed: the planned open S3 BUGS.md entry (old TR-14.16) and `TestTheServedIndexResidual`. Added: the failing-first class `TestTheServedIndexIsARank` (both modes, after a move, linked selection, brush and filter cards, csv), two helpers `_dash_page_index` and `_dash_relabel` (served functions tuple and `function_test_map.py`), one more flip (E-7 item 10), Evidence E-8 (measured), and new mutation rows. Task 14-01 copies the ratified rows instead of asking, and reads impact from the main checkout's GitNexus index, as index R8 requires (no `npx gitnexus analyze` in the worktree). Tasks changed: 14-01, 14-03, 14-04, 14-06, 14-07, 14-11, 14-12 and 14-16. New finding, carried as a guard in E-8: a saved mapper copy also carries an `index` column (`index` = position in its source). Before this section's restriction that position is the observation number (measured). After TR-14.5 it is a position among planned rows only, and `test_no_index_label_outside_the_pages_ranks` pins this in both modes.

> Batch **3** · Depends on **02, 06, 07, 08, 11** · Blocks **15** · Risk **red** · Commits: one (P0.11) → CHANGELOG `### Security` (the one marker S01 places for P0.11)

Every amendment of the u10 review is applied in this file. Each is listed with where it lands.

- **A1 (blocking: a spurious "(missing)" colour key).** `GlyphMapper._apply_colorvar` read the whole source column (dash_render.py:6956 at `7421d3d`), so a blanked cell became `"__missing__"`. Re-measured on this section's scratch prototype WITHOUT S07 (Evidence E-6): the saved `colorlevels(3)` key on `(scatter, qual __dashq1, colorvar(price)) (scatter, qual __dashq2)` gained `'(missing)'` (factors `['4453–6763.67', '6763.67–9074.33', '9074.33–11385', '__missing__']`), and the served linked key gained it too. S07 (P0.16, batch 1) computes the domain from the layer's view rows (`_dash_colorvar_domain`, TR-07.3/TR-07.7/TR-07.8) and removes the sentinel. This section therefore **depends on S07** (index "14 ← 07") and carries the review's missed test as a GUARD that must pass at the batch-3 base and stay green: `TestColorvarReadsTheLayersRows` (TR-14.13, task 14-04). If it fails at the base, S07 is not on the tree: stop and report.
- **A2 (csv moves no dashboard row set).** Under `csv` only `need` (and so `rows`, the snapshot and the CSV text source) widens to every row. `graph_rows`, `link_rows` and `filter_rows` are computed the same way with or without csv (TR-14.2). Measured on the prototype: with and without csv, `filter(price, type(range))` under `if price > 4500` spans 4749–11385 and the graph source holds 6 rows; only the snapshot differs (10 rows with csv, 6 without). Pinned by `TestCsvDoesNotMoveTheDashboard`.
- **A3 (two row-identity functions).** `_row_ids_for` becomes the ALIGNED function: one rank per frame row, and a label the page does not hold raises `ValueError` (the own-position fallback `pos.get(idx, i)` at :25619-25620 and the `except` fallback at :25621-25622 are removed). A new `_row_ids_kept` is the DROPPING function, used for member ids, `_kpi_qualifier_row_ids` (:25597) and the per-plot `_wanted` set (:26198-26199). Pinned by `TestRowIdentitiesAreDense::test_an_unranked_label_raises_in_the_aligned_path` and `::test_member_ids_never_fall_back_to_positions` (TR-14.4).
- **A4 (order in render()).** `render()` parses `link()`/`filter()` FIRST, computes the plan, THEN calls `_report_dataset_shape` with the page's row count (TR-14.8). The warning text is unchanged ("dash exports every observation of the variables it uses" stays true of the export); its comment at :849-853 is corrected, and the help states that the saved and served estimates may differ on qualified data (the served builder still counts every row, `test_dataset_size_warning.py::test_the_builder_warns_on_the_same_data` unchanged).
- **A5 (linked-view guard).** `if len(_g_fdf) < len(self.df)` (:27157) is replaced: the mask is built over the link frame's labels and the view is made `if not all(mask)`. Facet masks (:27178) and the BooleanFilter (:27161) have exactly the link frame's length, so `len(_prev_bools) == len(_mask)` (:26207) never silently skips an intersection (TR-14.6). Pinned by `TestAfterAMoveBothModesDrawTheSameRows` (node-run saved vs served).
- **A6 (the prototype must cover the design).** Done before this plan was finalised: a scratch prototype implemented every code change of TR-14.1 to TR-14.10 (dense ranks, linked source and views, facet masks, panel member ids, agg threshold, report order, every served change, the build-time type) except `_page_sort_keys`/`_page_labels`, which need S02's code, on a copy of `7421d3d` plus S07's one-line registration fix, and ran 20,804 test nodes of 184 test files. Results and the complete measured flip list are in Evidence E-6; nothing else failed.
- **A7 (help accuracy for an empty reach).** Measured (`_dash_filter_widget` on an empty column, both modes share it): range and slider → disabled `RangeSlider`/`Slider` over [0, 1], a `%td` range included; dropdown → `Select(disabled=False, options=[('__all__','All')])`. The dropdown is NOT changed; the help is worded per widget type (TR-14.15) and pinned by `TestTheHelpSaysSo::test_the_filters_paragraph_names_each_empty_widget`.
- **A8 (row identities in both modes; rewritten by the 01oct2026 ratification).** At `7421d3d` the served sources' `index` column carries original observation labels. This covers the shared source (`_shared_data['index'] = list(df.index)`, :30112) and every per-layer source that `ColumnDataSource(<frame>)` builds (`_dash_layer_source` :23268/:23275, `_dash_range_source` :23331, `_dash_pc_source` :23362), and the same holds for every source a move rewrites (`_dash_refresh_linked` :21658, `_dash_refresh_unlinked` :21775) or the redraw rebuilds from a frame. Measured in E-8: a served `scatter … if price > 4500` sends `index` `[1, 3, 4, 6, 7, 9]`, which shows that observations 1, 3, 6 and 9 were excluded. Ratified fix: the served frame is relabelled ONCE per document, right after the plan (TR-14.18). The rows the plan keeps get labels 0..m-1 in data order, which are exactly the saved page's `__dash_row__` ranks (`_page_labels`). Every other row gets m..N-1, and those labels never reach a source. `_qual_masks`, S02's `_sort_keys` and the plan's own Series are relabelled with it. Every served consumer matches rows by label (`_shared_pos`, `_dash_linked_views`, `_dash_refresh_*`, `_owner_rows`, `_brush_rows`, `_kpi_qual_rows`, the brush's `_df_ref.loc[labels]`, `_dash_keep_jitter`, S02's `rank.reindex(labels)`), so none of them changes. Row order is untouched, so `in` (`iloc`) and the csv rows keep their meaning. Measured in E-8: under an adversarial non-monotonic relabel, 57 of 16,117 nodes in 101 served test files failed, and each one fails only because its oracle reads a label as an observation position. Under the rank relabel the same 57 nodes leave one, which is flipped (E-7 item 10). Pinned by `TestTheServedIndexIsARank` (TR-14.16).
- **A9 (strings and dates in the battery).** The sentinel battery writes its data with `variableIsString`/`variableTypeIsString` True for its string column and `build_options.formats = {"when": "%td"}` (the `test_dates._jsonio_payload` form), and the served scanner walks every property of every model with no depth cutoff, strings and value-label text included (TR-14.12).
- **A10 (the effective type follows the reach).** `_dash_filter_effective_type` sees only the reach in both modes: the saved `_build_filter_widgets` (:27584-27585) and the served build-time plan (:29340-29357). Measured on the prototype: `filter(price, type(dropdown))` under `if price > 4500` with `limits: {filter_options: 7}` stays a 6-option dropdown in both modes (HEAD: a range in both). CHANGELOG line and `TestTheFilterTypeFollowsTheReach` (both modes, type and warnings).
- **A11 (one key tuple).** The served template's hand-written plot-key tuples are replaced by `_DASH_PLOT_VAR_KEYS`: `all_vars` (:30089), the unlinked placeholder (:30130, which listed only five keys) and the by() `_gvars` loop (:30786).
- **A12 (per-source snapshots).** `_snapshot_of`/`all_graph_sources_orig` (:27668-27673, :27848) and `derived_sources_orig` (:27800-27808, :27852) are copies of the restricted sources and are covered by the battery (the page decoder reads every embedded JSON document).
- **A13 (ER-07 loads the app in-process).** The served truth case `exec`s the generated app with the `make_document(curdoc())` attach replaced (`test_adversarial_matrix._load_app`'s rule, as `test/filter_truth_check.py::served` does) and calls `make_document(Document())`; no listener, so no S13 token is involved.

**Missed sites, each carried:** `_apply_colorvar` (A1, via S07); `_row_ids_for` fallback (A3); the report order (A4); :27157 and :26207 (A5); the snapshots (A12); `_kpi_qualifier_row_ids` (A3); :30089/:30131 (A11); the served `index` (A8, fixed by TR-14.18); the saved mapper copies' `index` (E-8, closed by TR-14.5 and pinned); `_fs['var']` vs `'varname'` (the plan reads both, TR-14.2).

**Missed tests, each carried:** `TestColorvarReadsTheLayersRows` (string, colorlevels, linked); `TestCsvDoesNotMoveTheDashboard`; `TestTheFilterTypeFollowsTheReach`; `TestAFilterEveryTargetExcludes`; `TestAnEmptyReach::test_date_range_both_modes`; `TestRowIdentitiesAreDense::test_an_unranked_label_raises_in_the_aligned_path` and `::test_member_ids_never_fall_back_to_positions`; the node-run saved-vs-served after-move test `TestAfterAMoveBothModesDrawTheSameRows`; `TestABrushCountsTheRowsTheGraphShows::test_a_by_panel_with_a_layer_qualifier_both_modes`; the string/date sentinel cases; `TestTheServedIndexIsARank` (replaces the struck `TestTheServedIndexResidual`).

**Truth disputes, resolved by re-measuring (StataNow 19.5 through `scripts/stata_slot.sh`, and Python probes of `7421d3d` and of the prototype):**
1. *"The prototype validated the design."* It did not (u10patch.py patched four sites). Re-done in full (A6, Evidence E-6).
2. *Which `TestASelectionAfterAMove` nodes flip.* All three parametrised tests read the one tuple `_SELECTIONS[4]`, so the flip is one edit of its expected text, `'23.4'` → `'25.66667'`. Re-measured: only `test_the_card_is_the_saved_pages_and_statas[update(brush), the layer's own in]` fails under the change; `test_the_selection_is_cleared` and `test_the_brush_itself_changed_the_card` pass before and after the edit. The design's spelling `test_the_card_is_the_saveds_and_statas` is wrong; the node is `test_the_card_is_the_saved_pages_and_statas`. The prototype ALSO found a flip the design missed: `TestAdversarialFilterMoves::test_a_selection_cannot_outlive_the_rows_it_named` (served card `'23.4'` → `'25.66667'`).
3. *Empty dropdown "greyed out".* False (A7); help worded per type.
4. *levelsof truth.* A dropdown never lists missing, so the truth cited is `levelsof rep78 if foreign` → `3 4 5` (measured, t14b.log), not the `, missing` form (`3 4 5 .`).
5. *"drawn stays 53-60" in the flipped node-run test.* Wrong under dense ranks: the runner reports `ids + 1`, which are now page ranks (prototype: `drawn [14, …]`, `rows 8`). The flip maps ranks back to observations through `r._page_labels` (TR-14.4).

**Decisions of the design (ratified 01oct2026 at step 0f; 14-01 copies them from `<scratch>/wp29-ratified.txt` and does not ask):**
- **SD1 csv (ratified):** today's contract is kept. With `csv` the page holds every row of every exported column (help :888-895, :921-926), and csv moves no other row set (A2).
- **SD2 brush count (ratified):** a cleared or after-move brush card counts the rows its graph shows (dash.sthlp:1407-1409 already says so), and a qualified link group's rows. Results change (measured, both modes): 23.4 → 25.66667, 21.5 → 22.83333, 21.2973 → 22.13333 (E-6).
- **SD3 dense ranks (saved half ratified; served half struck and replaced):** the saved page numbers its rows 0..m-1 (TR-14.4). Per the maintainer ("Resolve the server app's index known gap."), the served app numbers them the same way in this section and this commit. The served frame's labels become the saved page's ranks for the planned rows (TR-14.18), so every served `index` value is in 0..m-1. A row of the shared source or of a per-layer source carries the same number as that observation's `__dash_row__` on the saved page. No residual and no BUGS.md entry remain.
- **SD4 empty reach (ratified):** the shared builder's existing widgets (A7). This includes a filter that every graph and card excludes, and a dashboard whose only layers are literal (`function`, `scatteri`, `pci`, `pcarrowi`).
- **SD5 follow-ups (ratified):** out of scope and handed to S15 as residuals (Notes for the closeout). They are the rows used only by computed layers, `$dash_max_cells` counting planned rows, and the served `.py` holding only planned rows. Re-checked against SD3's served fix: no contradiction. The relabel happens in memory when each document is built. The `.py` and its data on disk are unchanged: every row and every value, in Stata's order, read by the server and never sent. SD5's residual is about what the server keeps on disk; SD3 is about what a browser receives.
- **SD6 P0.16 (ratified):** owned by S07; this section's colorvar test is a guard.

## Overview

GAPS2 I2 and DROPIN-REMAINING P0.11: the saved page embeds observations that `if`/`in` exclude, and the help does not say so. twoway keeps only the rows each layer's qualifier selects: `twoway (scatter mpg weight if foreign) (scatter mpg weight if price>10000)` holds sersets of 22 and 10 observations, and a saved `.gph` reloads exactly those (truth1/truth3, Evidence E-1). dash's saved page for the same command embeds all 74 rows of mpg and weight (`dash (...)(...), saving()` → 74 distinct `__dash_row__`; the union is 30). The leak is wider than the GAPS2 entry said:
- **Saved:** a layer's own `if` (the graph's source is the graph's rows, the layer a view over it), a `link()` group (its one source is every row), `by()` with a layer qualifier, and every filter: the snapshot the filter script reads holds every column of every row (:27649-27664), and each widget's options and bounds come from the whole data (:27584).
- **Served:** the per-layer sources are right, but a `link()` group's shared source holds every row (:30110-30119; measured 74 rows where the union is 30), and every widget's domain comes from the whole data (:30965; measured: a slider's start was the price of a row the graph's `if` excluded).
- **Positions:** the saved row identities are positions in the whole data, so their gaps show which observations were excluded. The served `index` column carries the same observation numbers (E-8: `[1, 3, 4, 6, 7, 9]` for a layer `if price > 4500`).

After this section a page holds a cell (observation × variable) only when some consumer of the page reads that variable on that observation: a layer on its graph's and its own rows (with by(, total)'s Total rows), a card the page recomputes (a filter reaches it, or `update(brush|both)`), a filter on the rows of the graphs, link group and cards it applies to, and, with `csv`, the download (every row, the documented contract). What Stata computes from the whole data keeps reading the whole data and writes only results: KPI first values, fits, `lowess, adjust`'s mean, lpoly's `_N` grid, the by() panel list (twoway's empty panels included) and text qualifiers with a positional `in`. The restriction is applied at embed time only — `self.df` (saved) and `df` (served) stay Stata's whole data — through one plan function both modes run. The saved page numbers its rows itself (dense ranks). The served app numbers its rows the same way: it relabels its frame from the same plan when each document is built, so no browser receives an observation's own number. The help says what a saved page holds.

**Why one section.** One rule (BR-29.9), one plan function and one commit; every consumer of the page reads through it, so the saved and served renderers must change together or the parity guard breaks.

**Test order (CLAUDE.md rule 7) and commit rule (index step 1).**
1. 14-01 records impact and copies the decisions ratified 01oct2026; it asks nothing. 14-02 extracts the Stata fixture (no code change).
2. 14-03 to 14-05 write every new test (pytest unit, the sentinel battery and behaviour tests, the cscript block) against the unmodified batch-3 base. 14-06 runs them and saves the failure text to `<scratch>/14-P0.11-failure.txt`. Nothing is committed.
3. 14-07 to 14-11 make the fix; 14-12 and 14-13 flip the pinned tests and add the parity cases; 14-14 writes the help; 14-15 runs the truth block.
4. 14-16 closes the entry, runs the full suite once and makes the section's ONE commit, subject ending `(WP-29 P0.11)`, whose body opens with the saved failure text. No test-only commit exists.

## Risk: [red] — every saved source, the filter snapshot, the linked views and five served structures change shape in one commit, in both modes

**Why.** The plan decides which cells exist on the page. A consumer the plan did not foresee reads a blank and draws a gap or a `.`; a mask sized to the wrong frame selects the wrong rows after a move; a row identity read as a position (S02's join key) orders a line wrongly. Each of these is silent.

**Risk factors.**
1. Unforeseen consumers of a blanked cell (mapper whole-column readers: colorvar, jitter range, mlabel kind).
2. BooleanFilters, facet masks and panel member ids sized or numbered against the wrong frame (A5).
3. Code that reads `__dash_row__` as a position in `self.df` — S02's `_dash_join_key` does (`rank.to_numpy(float)[ids]`, section-02 TR-02.4), and batch-2 code (S12's stale cue) may.
4. Behaviour changes users see: widget domains, the effective widget type, brush counts, disabled widgets.
5. Five batch-1/2 sections edited the same functions (S02 `_make_figure_body`'s `_jo`; S05 `_FILTER_JS`; S06 the export lists; S07 the per-plot block and colorvar; S12 the stale cue; S13 the served template).
6. The served relabel (TR-14.18, ratified 01oct2026). Any served map keyed by row that the relabel misses silently picks other rows: a qualifier mask, S02's sort keys, or a structure a batch-1/2 section added between the loader and the relabel. So does any served code that reads a label as a position.

**Mitigation.**
1. Blank only at the embed choke points (`_make_source`, the snapshot, the CSV text source, the served shared source, placeholders and `_dash_refresh_linked`), with the plan's columns built from the same collectors the sources use (`_DASH_PLOT_VAR_KEYS`, `_dash_option_columns`, graph hover, by() variables); S07's view-row colour domain (A1) is a prerequisite and a guard test; the jitter and mlabel readers were exercised by the full prototype run (E-6: `test_jitter.py`, `test_saved_filter_layers.py` green apart from one id-numbering pin).
2. A5's rewrite, plus node-run after-move tests in both modes for linked by() + layer `if` and linked graph `if` + layer `if`.
3. `_set_embed` builds `self._page_sort_keys` (S02's ranks re-indexed to page ranks) and the `_jo` call reads it; task 14-08 greps for every other positional reader and routes it through `_row_ids_for`/`_row_ids_kept`; `TestTheJoinKeyFollowsThePagesRows` pins the S02 case in both modes.
4. Decisions ratified 01oct2026 (14-01 copies them); one CHANGELOG Security item naming each change with its old and new value; help paragraphs.
5. The batch-3 base already holds batches 1-2; every anchor below is `7421d3d`'s and is located by symbol and quoted text, never by number.
6. The relabel is one emitted block placed right after the plan. Each row-keyed map is relabelled through `_dash_relabel`, which raises when a Series is not indexed like the frame, so a missed map fails loudly. Task 14-11 audits the emitted lines between the loader and the relabel for any other row-keyed capture. The relabel keeps row order and is the identity when no qualifier excludes a row: an unqualified dashboard's labels do not change. E-8 measured the served suite under a harsher, non-monotonic relabel: no served code read a label as a position. Every failure was a test oracle doing so.

## Dependencies

- **Depends on:**
  - **S01** — the open BUGS.md entry "The saved page embeds every row of each drawn variable, including rows that if and in exclude", the marker `<!-- WP-29 P0.11 -->` under `### Security`, the key `"P0.11"` in `WP29_OPEN` (test_tracking_documents.py), and `test/test_wp29_truth.cscript` with `_w29_expect`/`_w29_done`, `w29_work` and the marker line.
  - **S02** — `_join_order`/`_dash_join_key` read drawn rows by `__dash_row__` as positions; this section re-indexes the sort keys to page ranks (TR-14.4). S02's Notes ask exactly this ("If S14 changes `self.df`'s rows… the saved `_dash_join_key` is positional"). On the served side, S02's `_sort_keys` (indexed like `df`, read by `rank.reindex(labels)`) is relabelled with the frame (TR-14.18).
  - **S06** — hover() variables are exported; the plan lists each graph's hover() names as layer columns, so they are kept on the layer's rows.
  - **S07** — the registration invariant ("ids are exactly the source's row ids the filter keeps", TR-07.1) and the colour domain from the view rows (A1).
  - **S08** — the private writer. The served `.py` and its data on disk hold every row, the residual this section discloses (SD5). As ratified 01oct2026 (S08 codes struck), the writer makes each file 0600 where it can and notes a root that is not private instead of refusing it. This section's text therefore says "written privately where the system allows", never "0600 in a 0700 root".
  - **S11** — lpoly's default bandwidth, band and grid read `mapper.dataset` (the whole data), which this section leaves untouched.
- **Blocks:** S15 (closeout).
- **Parallel batch:** 3, alone. Worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s14`, branch `wp29-s14`, cut from `wp29-p0` after batch 2 is green (base sha in `<scratch>/batch-3-base.txt`).
- **Why:** every consumer's final row rule must exist before the plan lists it (index "14 ← 02, 06, 07, 08, 11").

## Evidence

Line numbers are `7421d3d`'s; the worktree is cut after batches 1-2, so locate every site by its symbol and the quoted text.

### E-1 twoway truth (StataNow 19.5, `scripts/stata_slot.sh`, `sysuse auto` unless noted)

```
. twoway (scatter mpg weight if foreign) (scatter mpg weight if price>10000), nodraw
. serset set 0 / serset / return list        r(N) =  22
. serset set 1 / serset / return list        r(N) =  10
. count if foreign | price>10000             30
. twoway scatter rep78 weight if !foreign, nodraw ; serset dir
  0.  52 observations on 2 variables          (count if !foreign = 52; & !missing(rep78) = 48)
. twoway (scatter mpg weight if foreign, colorvar(price)) (scatter mpg weight if price > 10000), nodraw
  0.  22 observations on 3 variables  mpg weight price      <- price only on its layer's rows
  1.  10 observations on 2 variables  mpg weight
. twoway lowess mpg weight if foreign, adjust nodraw ; serset use ; summarize
    __000000 |  22  21.2973 ...                (the whole-data mean of mpg: lowess.ado adjust)
```

by() panels (exported to SVG; subtitles read from the file):

| command | sersets | panel subtitles |
|---|---|---|
| `twoway (scatter mpg weight if foreign==0), by(foreign)` | 52 | Domestic |
| `twoway (scatter mpg weight if foreign==0) (scatter mpg weight if price>15000), by(foreign)` | 52, 1, 0 | Domestic, Foreign (empty) |
| `twoway (scatter mpg weight if foreign==0) (scatter mpg weight), by(foreign)` | 52, 0, 22 | Domestic, Foreign |

So the panel list needs only the graph-level selection's panel keys, never the rows. Stata's answers for the widget and card values (t14.do, t14b.do, truth4.do):

```
sysuse auto:  summarize price if foreign     min 3748  max 12990      (all rows: 3291 15906)
              levelsof rep78 if foreign      3 4 5                    (all rows: 1 2 3 4 5)
              summarize mpg if foreign | price > 10000    mean %9.0g  22.13333   (30 obs)
              count if foreign==1 in 40/60   8
              levelsof obs if foreign | price > 10000:  9 11 12 13 26 27 28 41 53 54 ... 74 (30 values)
parity frame (test_mode_parity._DF typed in with input):
              summarize price if price > 4500            min 4749  max 11385   (all: 3799 11385)
              levelsof price if price > 4500             4749 4816 5189 5788 10372 11385
              summarize mpg if foreign == 1 in 3/8       %9.0g  25.66667
              summarize mpg in 3/8                       %9.0g  22.83333
              summarize mpg if foreign == 1              %9.0g  23.4
              summarize mpg                              %9.0g  21.5
```

### E-2 dash at `7421d3d`, through Stata (dashnow.do; pages decoded, base64 arrays included)

| case | distinct row ids on the page | union / truth |
|---|---|---|
| D1 `dash scatter mpg weight if foreign, saving()` | 22 | 22 (a lone segment's `if` is promoted to the graph, dash.ado:5104-5137) |
| D2 `dash (scatter … if foreign) (scatter … if price>10000), saving()` | 74 | 30 |
| D3 build: g1 `if foreign`, `kpi mean(price)`, `filter(rep78)` | 74 (64 distinct weights, every domestic car) | mpg needed on 22, price on 74 |
| D4 build `link(g1 g2)`, g1 `if foreign`, g2 `if price>10000` | 74 | 30 |
| D5 build, csv | 74 | 74 (contract) |
| D7 `dash build, link(g1 g2) server` loaded in Python | shared CDS `[mpg, price, weight, index]`, 74 rows | 30 |

### E-3 Sentinel probe at `7421d3d` (10 rows with unique values; `__dashq1` = rows 2,4,6,8,10; `__dashq2` = rows 1-3; rerun for this plan)

| case | saved: excluded rows found in the page | served: excluded rows found in the document |
|---|---|---|
| A graph-if scatter | none | none |
| B plot-if scatter | 1,3,5,7,9 | none |
| C two plots q1, q2 | 5,7,9 | none |
| D link(g1 q1, g2 q2) | 5,7,9 | 5,7,9 (shared CDS 10 rows) |
| E dropdown + graph q1 | 1,3,5,7,9 (snapshot 10 rows) | none |
| G csv + graph q1 | 1,3,5,7,9 (contract) | none |
| J by(foreign) + plot q2 | 4-10 | none before a move; row 10 after a range move (the RangeSlider's end is row 10's price) |
| L slider(price) + graph q1 | 1,3,5,7,9 | row 1 (Slider start 5001.75 = row 1's price) |
| F, K static KPIs; H line; I histogram; M lfit | none | none |

### E-4 The mechanisms (code at `7421d3d`)

`DashRenderer._make_source`, :25404-25438 — every saved source passes here; it copies every row of the frame it is given and stamps positions in `self.df`:

```python
25425        frame = df if df is not None else self.df
25426        available = [v for v in varnames if v in frame.columns]
...
25437        data_dict[_ROW_ID_COLUMN] = self._row_ids_for(frame)
```

`_row_ids_for`, :25604-25622 — positions in the whole frame, with two silent fallbacks (A3):

```python
25618        try:
25619            pos = {idx: i for i, idx in enumerate(self.df.index)}
25620            return [int(pos.get(idx, i)) for i, idx in enumerate(frame.index)]
25621        except (AttributeError, TypeError):
25622            return list(range(len(frame)))
```

`_build_sources_and_figures`, :27038-27305 — the linked source is the whole frame, and its views and facet masks are sized to it:

```python
27137            linked_source = self._make_source(linked_vars)
...
27156                    _g_fdf = self._apply_graph_filter(g)
27157                    if len(_g_fdf) < len(self.df):
27159                        _bool_mask = [
27160                            bool(i in _df_idx_set) for i in self.df.index
...
27178                            mask = [i in group_df.index for i in self.df.index]
...
27255                            self._register_view_filter(
27256                                shared_src_render, _pf,
27257                                [i for i, keep in enumerate(mask_r) if keep])
```

The unlinked sources (:27187, :27198) take the graph-qualified frame and the per-plot qualifiers are views over it (:26176-26215), so a layer's own `if` leaves every graph row on the page. `_build_filter_widgets`, :27507-27870 — the widget domain and the snapshot are the whole data:

```python
27584            _fcol = self.df[fvar]
27585            _eff = _dash_filter_effective_type(
...
27659            for _col in self.df.columns:
27660                _orig_data[str(_col)] = [DashRenderer._to_serialisable(v)
27661                                         for v in self.df[_col]]
27662            _orig_data[_ROW_ID_COLUMN] = list(self._row_ids_for(self.df))
```

(the same at :27862-27867 for csv; the CSV text source at :27890-27892). `render()` reports before it parses (A4): `_report_dataset_shape(self.df.shape[0], …)` at :28119, `self._parse_link_and_filters(build)` at :28130; the aggregate member-id threshold is `_n_rows = len(self.df)` at :28167.

The served template (strings emitted by `ServerAppBuilder._generate_app_source`, :29269):

```python
30110    "    _shared_data = {v: _dash_column_values(df[v]) if v in df.columns else []",
30112    "    _shared_data['index'] = list(df.index)",
30119    "    _shared_pos = {_lbl: _i for _i, _lbl in enumerate(df.index)}",
30130    "                for k in ('yvar', 'xvar', 'var', 'yvar1', 'yvar2'):",      # A11: 5 keys
30966    "            ftype, fvar, df[fvar], _ftitle, vlabels,",                   # widget domain
31010    "                _brush_rows[id(_bs)] = _owner_rows[_bgn]",
31011    "    _brush_rows[id(shared_source)] = df.index",
31119    "                                  else _own_rows.intersection(fdf.index))",
31162    "                _shared_fdf = _df_ref[_shared_mask]",
```

and the build-time dropdown plan at :29340-29357 reads `_fdf[_fs["var"]]` over the whole frame. `_filter_specs` is emitted at :30930-30940, AFTER the shared source is built (:30108), so the template must emit it earlier for the plan (TR-14.10).

What stays on whole data on purpose: `self.mapper.dataset = self.df` (saved, :25117) and `_DASH_MAPPER.dataset = df` (served, :30078) — lowess adjust (:9072-9091) and lpoly's grid (:9409-9433, S11); `_expand_by_groups` (:25660-25780) and `_dash_by_panel_dropped` (:2089) — the panel list; `_build_kpi_html` first values; the served CSV `_csv_rows`; the WebGL threshold `n_rows = len(self.df)` (:25951); dash.ado's export (every row is still exported, dash.ado:6037-6046, 7086-7140) and `_dash_cell_cap`.

### E-5 Blast radius (R8; grep, because GitNexus has no `dash` index)

`mcp gitnexus impact` at plan time answered `Repository "dash" not found. Available: TYME, PhotoShootPlannerPro`. Task 14-01 runs `gitnexus_impact({target, direction: "upstream"})` against the main checkout's index (index R8; never `npx gitnexus analyze` in the worktree) for each symbol below, records the output in `<scratch>/14-impact.txt` and reports HIGH/CRITICAL before editing. By grep at `7421d3d` (dash_render.py hits / test files naming the symbol): `_make_source` 8/5, `_row_ids_for` 7/1, `_kpi_qualifier_row_ids` 2/1, `_build_sources_and_figures` 5/3 (callers `render`, `_setup_sources`; `_build_figures` has 21 test files), `_build_filter_widgets` 3/4, `_csv_button` 2/1, `_report_dataset_shape` 3/4 (callers render :28119 and the served builder :29132), `_dash_refresh_linked` 4/2, `_generate_app_source` 2/3, `_make_figure_body` 3/1 (expected HIGH per index R8; this section changes one line in it plus S02's `_jo` argument). 127 test files render a saved page and 102 a served one, so every change reaches most of the suite.

### E-6 The scratch prototype (A6; this plan's own measurement)

A copy of the `7421d3d` tree, with S07's TR-07.1 registration line folded in, patched with this section's design (379 changed lines, 40 hunks: every code change of TR-14.1 to TR-14.10 except `_page_sort_keys` and `_page_labels`, which need S02's code). Results:

- **Sentinel probe (E-3 cases):** no excluded row in any saved page or served document, before or after a move, for A-F and H-M; G (csv) still holds every row (contract). Row ids are dense (`B plot-if` → ids 0..4). After moves (range, dropdown, slider; linked, two plots, by()): served documents hold no excluded row.
- **Behaviour (both modes equal in every row):**

| case | HEAD saved / served | prototype saved / served |
|---|---|---|
| `filter(price, range)`, graph `if price > 4500` | 3799–11385 / same | 4749–11385 / same |
| `filter(price, slider)`, same | start 3799 / same | start 4749 / same |
| same + unqualified filter-mode card | 3799–11385 | 3799–11385 (the card reads every row) |
| `filter(price, range exclude(g1 k1))` (no target) | 3799–11385 | disabled RangeSlider [0,1] |
| `filter(rep, dropdown exclude(g1 k1))` | All, 3, 4, 5 | All only (enabled) |
| `%td` range, graph selects no row | DateRangeSlider over the data | disabled RangeSlider [0,1] |
| csv on/off, `if price > 4500` range | snapshot 10/10, source 6/6 | snapshot 10/6, source 6/6, widget 4749–11385 both |
| dropdown price, `filter_options` 7, reach 6 values | range (whole data 10 values) | dropdown of 6 |
| brush card, layer `in 3/8`, after a move to Foreign | 23.4 / 23.4 | 25.66667 / 25.66667 |
| same, brush cleared, no move | 21.5 / 21.5 | 22.83333 / 22.83333 |
| auto, `link(g1 g2)` g1 `if foreign`, g2 `if price>10000`, brush cleared | 21.2973 / 21.2973 | 22.13333 / 22.13333 |
| colorlevels(3) price, layer q1 + layer q2, WITHOUT S07 | saved 3799–…, served 4453–… (P0.16) | saved 4453–… plus `'(missing)'` unlinked and linked; served unlinked clean, served linked plus `'(missing)'` (A1: needs S07) |
| by(foreign) on auto, layers `if foreign==0` and `if price>15000` | panels Domestic, Foreign; page rows 74 | panels Domestic, Foreign (twoway's empty Foreign kept); page rows 52 |

- **Test runs on the prototype** (`python3 -m pytest <files> -q -n 6 -p no:cacheprovider`; 184 files, 20,804 nodes):
  - run A, 29 files (filters, linking, brush, KPIs, qualifiers, dates, export, colorvar, jitter, registries): 1861 passed, 7 failed — `test_served_filter_move.py::TestTheReportedCase::test_the_saved_pages_own_script_draws_the_same`, `::TestASelectionAfterAMove::test_the_card_is_the_saved_pages_and_statas[update(brush), the layer's own in]`, `::TestAdversarialFilterMoves::test_a_selection_cannot_outlive_the_rows_it_named`, `test_filters.py::TestTheFilterReadsTheWholeDataset::test_a_range_under_a_graph_if_still_spans_every_row`, `test_linking_filters.py::TestLinkAll::test_the_token_is_expanded_exactly_once` (`code.count("_dash_link_names(") == 5`), `test_saved_filter_layers.py::TestAJitteredScatterFollowsAMove::test_the_kept_points_stay_where_they_were[qual1]` (`{0, 2, 3, 5, 6} == {1, 3, 4, 6, 7}`: ids are ranks), `test_function_test_map.py::test_every_function_has_an_entry` (the new functions).
  - run B, 41 files including `test_mode_parity.py`: 9284 passed, 4 failed — `test_mode_parity.py::TestAFilterMoveAgrees::*[function, dropdown to Foreign]` (`no option labelled 'Foreign': [('__all__', 'All')]`: a `function` layer reads no row, so the dropdown lists only All). Trial flip (an unqualified filter-mode card on the literal-type move cases, TR-14.14): `-k function` 47 passed.
  - run C, the other 114 files: 9576 passed, 48 skipped, 3 xfailed, 21 failed — all 21 in `test_responsive_layout.py` (Chrome page-fit timing under `-n 6` load). The file again at `-n 2`: 55 passed, 7 failed; each of those 7 alone (`-n0`): `2 passed in 122.13s` and `5 passed in 301.52s`; `test_saved_page_fits[tabs]` alone passes on both trees (`58.45s` prototype, `58.53s` HEAD). No layout regression.
- Not covered by the prototype, because the code does not exist at `7421d3d`: S02's join key, S05's units, S06's hover export, S07's colour domain, S11's lpoly, S12's stale cue, S13's token. The executor re-measures the flip list at the batch-3 base (R7).

### E-8 The served `index` column and the relabel (measured 01oct2026 at `7421d3d`; the ratification's re-plan)

Probe 1, `index` and `__dash_row__` of every ColumnDataSource. The parity frame (`test_mode_parity._DF`, ten rows; `price > 4500` keeps positions 1, 3, 4, 6, 7, 9), with `filter(price, type(range))`. Spec: `tp._spec([plot_for(t, if_expr="price > 4500")], build_options={"filter": "price, type(range)"})`. Saved from `r._last_layout_root.references()`, served from `doc.roots[*].references()`. Each entry is `(index, __dash_row__)`:

```
scatter plot-if  saved : [(None, [0..9]), (None, [0..9]), (None, [0..9])]
                 served: [([1, 3, 4, 6, 7, 9], None)]                  <- observation numbers
line plot-if     saved : [..., ([3, 7, 9, 4, 1, 6], [3, 7, 9, 4, 1, 6]), ...]   <- mapper copy: position in the whole-frame source
                 served: [([1, 4, 5, 2, 0, 3], None)]                  <- mapper copy: position in the layer's source
pcspike plot-if  saved : [..., ([1, 3, 4, 6, 7, 9], [1, 3, 4, 6, 7, 9]), ...]
                 served: [([0, 1, 2, 3, 4, 5], None)]
line graph-if    saved : [([1, 4, 5, 2, 0, 3], [3, 7, 9, 4, 1, 6]), ...]   <- graph source already restricted: positions 0..5
```

What this shows:
- The served leak is every source built from a DataFrame with `df`'s labels: per-layer, shared, refreshed and redrawn sources.
- A mapper copy (`map_line` :7910, `map_pcspike` :11369, `ColumnDataSource(df)` :7788) numbers rows by position in the source it was handed. Saved, that source is the graph's source; at `7421d3d` it holds every row, so the position IS the observation number. After TR-14.5 the graph source holds only planned rows, so the copy's `index` is below m. The `line graph-if` row shows this today, because the graph qualifier already restricts the source.

Probe 2, sources the brush or a refresh would read with no row identity. In every ColumnDataSource of the served document, a frame-variable column (mpg, weight, price, foreign, rep, when) and no `index`. Types: scatter, line, connected, lfit, histogram, kdensity, rarea, rspike, pcspike, area, bar, dropline, dot, lpoly and function, each under `if price > 4500` with a range filter, unlinked and `link(g1)`. Output: `done`, with no source listed. So `_dash_refresh_unlinked`'s no-`index` branch, which reads a label as a position, reaches no rendered source (guard `test_every_row_source_carries_an_index`).

Probe 3, does served code read a label as a position? A pytest plugin wrapped `ServerAppBuilder._generate_app_source`. Right after the emitted `    _qual_masks = meta['qual_masks']` it inserted a NON-MONOTONIC relabel: odd positions get 0.., even positions follow, and `df.index` and every `_qual_masks` Series are relabelled. Run: `DASH_PERM_PROBE=1 PYTHONPATH=<probe dir> python3 -m pytest <the 101 test files that build a served app> -q -n 8 -p no:cacheprovider -p perm_plugin -rf`. The files are every `test/*.py` naming `ServerAppBuilder`, `_load_app`, `tp._served` or `_served(`, except `test_responsive_layout.py`. Result: `57 failed, 16060 passed, 3 xfailed … in 784.17s`. Every failure was checked: in each one the test's own oracle reads a served `index` label as an observation position. Examples:
- `test_server_brush.py::…::test_brushing_two_points_gives_their_mean`: `_DF.loc[ids]`.
- `test_adversarial_matrix.py:2772`, `test_served_throttle.py:550`: `_DF.loc[src.data["index"][…]]`.
- `test_help_claims_4.py:1052-1058`: `df["price"].to_numpy()[labels]`.
- `test_served_linked_views.py::_drawn_served` against positions: served `[0, 1, 3, 4]` is positions `{1, 3, 7, 9}` under the probe's map, and the oracle wants `[1, 3, 7, 9]`.
- `test_saved_filter_layers.py::TestALinked/AnUnlinkedJitteredScatterServed`: label + 1.

Mapped back through the probe's permutation, every drawn row set and every card was right.

Probe 4, the rank relabel itself. Same plugin form; the plan was approximated by graph & layer & by(, total) & card qualifiers (the real plan adds filter reach, which lies within those rows). Planned rows got 0..m-1 in data order and the rest m..N-1. Run: the 57 node ids of probe 3. Result: `1 failed, 56 passed in 7.22s`. The one failure:
```
test_served_filter_move.py::TestAdversarialFilterMoves::test_no_widget_value_widens_a_layers_own_rows
AssertionError: ('__all__', [1, 2, 3, 4, 5, 6], [0, 1, 2, 3, 4, 6, ...])
assert ({1, 2, 3, 4, 5, 6} <= {2, 3, 4, 5, 6, 7}
```
The layers `in 3/8` and `if mpg > 18` plan rows {0, 2, 3, 4, 5, 6, 7, 9}. `in 3/8`'s rows 2..7 are ranks 1..6, which is right; the test expects observation positions (E-7 item 10). Sanity line, same plugin: served `scatter plot-if` now sends `index` `[0, 1, 2, 3, 4, 5]`.

Probe 5, a latent served mis-mapping that is NOT this section's. A served mapper copy's `index` is a position in the layer's source (probe 1, `line`), but the served brush reads it as a label (`_df_ref.loc[labels]`). Spec: `tp._spec([plot_for("line", if_expr="price > 4500")], kpis=[tp._kpi(var="price", stat="mean", update="brush")])`. Setting `indices = [0]` on the line's wired source gives a card of `4749` (observation 1). Position 0 of that sorted line is weight 1800, observation 3, price 4816. The served toolbar is `['PanTool', 'WheelZoomTool', 'BoxZoomTool', 'BoxSelectTool', 'LassoSelectTool', …]`. BokehJS's Line glyph hit-tests points and spans only, not boxes or lassos, so a browser should not reach this; that was not measured in a browser. The relabel changes nothing here, because the copy's positions are below m, so no observation number leaks. Handed to S15 as a residual candidate (Notes for the closeout).

### E-7 Tests that pin today's behaviour (flip, never delete)

1. `test/test_filters.py::TestTheFilterReadsTheWholeDataset::test_a_range_under_a_graph_if_still_spans_every_row` (:1769-1772): `(3799.0, 11385.0)` → `(4749.0, 11385.0)`; renamed `test_a_range_under_a_graph_if_spans_the_rows_the_graph_draws`; class docstring rewritten (a widget describes the rows its targets select). `test_a_range_under_by_spans_every_row`, `test_a_dropdown_under_by_offers_every_category`, `test_the_snapshot_holds_every_row_under_by` stay (unqualified graph).
2. `test/test_served_filter_move.py::TestTheReportedCase::test_the_saved_pages_own_script_draws_the_same` (:341-364): `out["rows"] == 22` → `8` (`count if foreign==1 in 40/60`); `out["drawn"] == list(range(53, 61))` → `[r._page_labels[i - 1] + 1 for i in out["drawn"]] == list(range(53, 61))`; docstring "of the 22 foreign rows it writes" → "of the 8 rows its layers draw".
3. `test/test_served_filter_move.py::_SELECTIONS[4]` (`"update(brush), the layer's own in"`, :548-553): `"23.4"` → `"25.66667"`, comment rewritten (the graph's source holds the rows its layers draw).
4. `test/test_served_filter_move.py::TestAdversarialFilterMoves::test_a_selection_cannot_outlive_the_rows_it_named` (:668-688): `{"k1": "23.4"}` → `{"k1": "25.66667"}`, comment `summarize mpg if foreign == 1 in 3/8`. The module docstring (:36-40) "the card reads 23.4" keeps its measured history and gains one sentence for the layer-qualified case.
5. `test/test_linking_filters.py::TestLinkAll::test_the_token_is_expanded_exactly_once` (:176): `== 5` → `== 6`, comment adds `_dash_embed_plan` (it CALLS the one implementation; no copy).
6. `test/test_saved_filter_layers.py::TestAJitteredScatterFollowsAMove::test_the_kept_points_stay_where_they_were` (:356-359): `want` built from observation positions → mapped through the page's ranks: `want = {r._row_pos[r.df.index[p]] for p in want_positions}`.
7. `test/test_mode_parity.py::MOVE_CORPUS` (:2156-2157): the literal-type entries get `kpis=[_kpi()]` (TR-14.14).
8. `test/test_help_claims_2.py::TestTheCsvCarriesEveryVariableTheDashboardUses` (:878-911): docstring quotes the replaced help sentence → the new one; `test_a_saved_page_with_filters_holds_every_row_without_csv` renamed `test_a_saved_page_holds_the_rows_its_graphs_cards_and_filters_select` (passes unchanged: the spec is unqualified); add `test_a_graph_if_keeps_its_variables_on_its_rows_only` (graph `if foreign == 1`, no csv: `mpg` non-blank on exactly the foreign rows of the snapshot).
9. `test/test_filter_widget_data.py` module docstring (:25-30): "already read from the whole data" and "a linked group's source is the whole data" become false; rewritten (tests unchanged: every shape carries the unqualified filter-mode card `k1`, so the reach is every row).
10. `test/test_served_filter_move.py::TestAdversarialFilterMoves::test_no_widget_value_widens_a_layers_own_rows` (:655-668; ratification 01oct2026, E-8 probe 4). `_rows(doc)` maps each served `index` label through the page's labels: `labels = tp._standalone(self._SPEC)[0]._page_labels` (computed once in `_after`) and `sorted(int(labels[int(i)]) for i in r.data_source.data["index"])`. `own_in` (`set(range(2, 8))`) and `own_if` stay observation positions. The docstring gains "(served labels are page ranks, mapped back through the saved page's `_page_labels`; WP-29 P0.11)". Old expectation: labels equal positions. New: labels are ranks of the planned rows {0, 2, 3, 4, 5, 6, 7, 9} (`in 3/8` → ranks 1..6).
Not flipped, but re-run at the batch-3 base: the 56 other nodes of E-8 probe 3 passed under the rank relabel (probe 4; at `7421d3d`, without the rest of this section). The executor re-measures them on the real tree (R7).

## User stories

- **US-14.1** As a dashboard publisher, I want a saved page to hold nothing of an observation every `if`/`in` of my dashboard excludes, so that sharing the file does not publish rows I chose to leave out.
- **US-14.2** As a dashboard publisher serving a `link()` group, I want the browser to receive only the rows the group's graphs draw.
- **US-14.8** As a dashboard publisher serving a dashboard, I want the browser to receive row numbers that show nothing about which observations my `if`/`in` excluded, numbered as the saved page numbers them. Brushing, linked selection, filter moves, cards and the download must keep working exactly as before.
- **US-14.3** As a dashboard reader, I want a filter's options and bounds to describe the rows the graphs and cards it filters select, so a dropdown never offers a category no graph can show and a slider never starts at a value nothing on the page has.
- **US-14.4** As a dashboard reader, I want a card that follows the brush to count, when nothing is brushed, the rows its graph shows — the same number in both modes and Stata's `summarize` over those rows.
- **US-14.5** As a twoway user, I want lowess `adjust`, lpoly's grid, by() panels and card first values to keep Stata's whole-data rules, so restricting the page changes no number Stata computes.
- **US-14.6** As a dashboard publisher using `csv`, I want the download to keep every row the filters leave, as documented.
- **US-14.7** As the maintainer, I want the rule proven by a sentinel battery in both modes and by Stata's own sersets and counts.

## Business requirements

- **BR-14.1** A saved page holds a cell of variable *v* on observation *i* only when (a) a non-literal layer that reads *v* (its plot variables, `colorvar`, `mlabel`, `wexp`, its graph's `hover()` and `by()` variables) selects *i* through its graph's and its own qualifiers (by(, total)'s Total rows included); or (b) a card the page recomputes reads *v* and selects *i* (a filter applies to it, or it follows the brush on a source holding *i*); or (c) a filter on *v* applies to a graph, link group or recomputed card that selects *i*; or (d) `csv` is given. The page holds no other observation.
- **BR-14.2** A served document never holds a value of an observation outside BR-14.1's rows, before or after any filter move.
- **BR-14.3** A filter widget's options, bounds and effective type come from the observations its targets select (BR-14.1(c)), in both modes. A filter that reaches no observation draws a greyed-out range or slider, or a dropdown listing only All.
- **BR-14.4** A brush card with nothing selected counts the rows its graph's source holds — the union of its layers' rows — or the link group's rows, in both modes, before and after a move.
- **BR-14.5** Stata's whole-data rules are unchanged: KPI first values, every fit and smoother, lowess `adjust`, lpoly's grid, the by() panel list, text `in` qualifiers.
- **BR-14.6** With `csv` the page holds every observation of every exported variable; the widgets, the graphs' rows and the link group's rows are the same as without csv.
- **BR-14.7** Both modes number rows 0..m-1, ranking the m rows BR-14.1 keeps in data order, so no excluded position is revealed. The saved page's `__dash_row__` and the served `index` of a row-identity source give the same number for the same observation, before and after any filter move. Any other `index` column (a mapper's copy) holds positions within a source of planned rows, so every `index` value either mode sends is below m. The relabel changes no value: brush and filter cards (BR-14.4), linked selection, the served redraw and the csv download give what the restriction alone gives. (Ratified 01oct2026; no residual.)
- **BR-14.8** The help says what a saved page holds, what a served one sends, what a widget spans, and that the data limit's count may exceed what the page holds.
- **BR-14.9** Every changed result is in CHANGELOG with the command, the old value and the new.

## Technical requirements

- **TR-14.1 Constant.** After `_DASH_OPT_VAR_KEYS` (:22376) add `_DASH_PLOT_VAR_KEYS = ("yvar", "xvar", "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var")` with a comment (one tuple for the saved column lists, the served app and the embed plan, WP-29 P0.11). `DashRenderer._VAR_KEYS` (:24951-24953) becomes `_DASH_PLOT_VAR_KEYS`. Served constants tuple: after `"_DASH_OPT_VAR_KEYS"` (:28393).
- **TR-14.2 `_dash_embed_rows_of(obj, frame, masks)` and `_dash_embed_plan(spec, frame, masks, link_names, filters, csv=False)`.** Module functions placed after `_dash_layer_frame` (:24485-24524). Reference implementation (validated by the prototype; no nested functions, no lambdas, no `eval`):

  ```python
  def _dash_embed_rows_of(obj, frame, masks):
      """The rows of *frame* an object's qualifier selects, as a boolean
      Series indexed like *frame* (WP-29 P0.11): its qualifier column's mask
      (_dash_qual_mask; an unknown column raises ValueError), else its
      if_expr/in_expr text through _dash_qualified_frame -- the one
      translator, its whitelist and no eval -- quietly, since the renderer
      that draws the object names a qualifier it cannot apply; every row
      when it has neither, or when *obj* is not a dict."""
      idx = frame.index
      if not isinstance(obj, dict):
          return pd.Series(True, index=idx)
      q = _dash_qual_mask(obj, masks)
      if q is not None:
          return q.reindex(idx, fill_value=False).astype(bool)
      _if = str(obj.get("if_expr", "") or "").strip()
      _in = str(obj.get("in_expr", "") or "").strip()
      if not _if and not _in:
          return pd.Series(True, index=idx)
      with warnings.catch_warnings():
          warnings.simplefilter("ignore")
          sel = _dash_qualified_frame(frame, _if, _in, copy=False)
      return pd.Series(idx.isin(sel.index), index=idx)
  ```

  `_dash_embed_plan` returns `{"rows": Series, "need": {column: Series}, "graph_rows": {graph name: Series}, "link_rows": Series, "filter_rows": [Series per entry of filters]}`, every Series boolean and indexed like *frame*:
  1. `need` starts all-False for every column of *frame*; `names` are the graphs' `graph_options.name`; `linked = set(_dash_link_names(link_names, names))` (the one rule; *link_names* may be raw).
  2. Per graph: `gq = _dash_embed_rows_of(g, …)`; when `g` has no `qual_col` and `graph_options` carries an `if_expr`/`in_expr` different from `g`'s (the served app reads `go` first, :30744-30745), OR in the rows of that text too (identical for every spec dash.ado writes; never drops a row either mode draws). `gt = _dash_total_spec(g)`; `gq_t` is its rows when `gt is not g`. `extra` = the graph's `hover()` names and its `by()` variables (`_dash_parse_by(…, warn=False)[0]`) that are columns.
  3. Per non-literal plot `p` (`type` not in `_DASH_LITERAL_TYPES`): `r = gq & rows_of(p)`, OR-ed with `gq_t & rows_of(total plot)` when `gq_t` exists; for every column in `[p[k] for k in _DASH_PLOT_VAR_KEYS] + _dash_option_columns(p["options"]) + extra`: `need[c] |= r`. `graph_rows[name] = OR of r` (all-False for a graph of literal layers only).
  4. `link_rows = OR of graph_rows[n] for n in linked`.
  5. Brush cards (`update` in brush/both): `need[var] |= link_rows | OR(graph_rows)` (every source carries a brush card's variable, :27091-27100).
  6. Per filter (keys `varname` or `var`; `exclude`): `reach |= link_rows` when `_dash_filter_applies("", excl, {}, members=<linked graph names>)`; `reach |= graph_rows[n]` for each unlinked graph it applies to (`_dash_filter_applies(n, excl, {})`); for each card with `update` in filter/both that it applies to, `kr = rows_of(card)`, `reach |= kr`, `need[card var] |= kr`. Then `need[fvar] |= reach`; append `reach` to `filter_rows` (one entry per filter, aligned with *filters*, also for a filter whose variable is absent).
  7. `csv`: every `need[c]` becomes all-True; nothing else changes (A2).
  8. `rows = OR of need`.
  The filters are passed ALREADY PARSED (saved `filters_cfg`, served `_filter_specs`); the plan never parses (re-parsing duplicated the `type(bogus)` warning in the u10 prototype, `test_same_warnings[filter() with an unknown type]`). Cost: O((plots + cards + filters) × N) boolean operations, inside the existing graph, plot and filter limits.
- **TR-14.3 `_dash_embed_values(series, need)` and `_dash_embed_frame(frame, plan, columns, rows=None)`.** After `_dash_embed_plan`.
  - `_dash_embed_values`: `keep` = *need* reindexed to `series.index` (False where absent; all-False when *need* is None); returns *series* itself when every flag is True; otherwise `series.where(keep, blank)` with `blank` = `pd.NaT` for datetime64, `np.nan` for numeric or bool, `""` otherwise (Stata's missing string). It never sees `__dash_row__`.
  - `_dash_embed_frame`: the rows of *frame* that `plan["rows"]` (or *rows*) keeps, the *columns* that are in *frame* (order kept, duplicates dropped), each through `_dash_embed_values(sub[c], plan["need"].get(str(c)))`; returns a DataFrame with *frame*'s index.
  - Served functions tuple: `"_dash_embed_rows_of", "_dash_embed_plan", "_dash_embed_values", "_dash_embed_frame", "_dash_page_index", "_dash_relabel"` on one line after `"_dash_layer_frame",` (:28597; index R2, amended by the 01oct2026 ratification; TR-14.18 defines the last two). Their callees are already copied (`_dash_qual_mask` :28601, `_dash_qualified_frame` :28591, `_dash_total_spec` :28604, `_dash_parse_by` :28638, `_dash_filter_applies` :28742, `_dash_link_names` :28753, `_dash_option_columns` :28785, `_DASH_LITERAL_TYPES` :28389).
- **TR-14.4 Row identities (saved).**
  - `DashRenderer._set_embed(self, plan)`: `self._embed = plan`; `pos = np.flatnonzero(plan["rows"].to_numpy(dtype=bool))`; `self._page_labels = list(self.df.index[pos])`; `self._row_pos = {label: rank for rank, label in enumerate(self._page_labels)}`; when `getattr(self, "sort_keys", None)` (S02) is a non-empty dict, `self._page_sort_keys = {col: pd.Series(np.asarray(s.to_numpy(dtype=float))[pos]) for col, s in self.sort_keys.items()}`, else `{}`.
  - `DashRenderer._ensure_embed(self, graphs, kpis, link_names, filters_cfg)`: when `getattr(self, "_embed", None) is None`, `self._set_embed(_dash_embed_plan(dict(self.master_spec, graphs=graphs, kpis=kpis), self.df, getattr(self, "qual_masks", None), link_names, filters_cfg, _dash_csv_wanted(self.master_spec.get("build_options", {}))))`; returns `self._embed`.
  - `_row_ids_for(frame)` (aligned): `pos = getattr(self, "_row_pos", None)`; when None (a test seam that built no plan), positions over `self.df.index`; each label of `frame.index` maps to its rank; an unranked label raises `ValueError("dash: a row the page does not hold reached a source")`. The `pos.get(idx, i)` and `except` fallbacks are deleted (A3).
  - `_row_ids_kept(frame)` (dropping): the same map, skipping unranked labels.
  - `_kpi_qualifier_row_ids` (:25597) calls `_row_ids_kept`.
  - `_make_figure_body`'s per-plot block: `_pos = {…}` / `_wanted = {_pos.get(i, -1) for i in _pdf.index}` (:26198-26199) becomes `_wanted = set(self._row_ids_kept(_pdf))`. S07's registration (`[int(r) for r, keep in zip(_ids, _mask) if keep]`) is unchanged.
  - S02's `_jo` line in `_make_figure_body` reads `getattr(self, "_page_sort_keys", None) or {}` in place of `getattr(self, "sort_keys", None) or {}`; `_dash_join_key` itself is unchanged (its `0 <= id < len(rank)` check then holds against page ranks).
  - Audit (task 14-08): `grep -n "enumerate(self.df.index)\|range(len(self.df))\|self.df.index.get_indexer\|self.df.index.get_loc" dash_render.py` at the batch-3 base; at `7421d3d` the hits are :25619 and :26198 only (both replaced). Any other hit that numbers rows (S12's stale cue, if it does) is routed through `_row_ids_for`/`_row_ids_kept`. After the change the command prints only `_row_ids_for`'s and `_row_ids_kept`'s no-plan fallback lines.
- **TR-14.5 `_make_source(varnames, df=None, rows=None)`.** When `self._embed` is set: `keep = plan["rows"] if rows is None else (rows & plan["rows"])`; `frame = frame[keep.reindex(frame.index, fill_value=False).to_numpy(dtype=bool)]`; every requested column present in the frame goes through `_dash_embed_values(frame[v], plan["need"].get(str(v)))` before the existing datetime/list conversion; `__dash_row__` = `self._row_ids_for(frame)` (aligned: every row is ranked by construction). Docstring states the rule. No plan (a renderer a test made without `render()`/`_build_sources_and_figures`): unchanged behaviour.
- **TR-14.6 `_build_sources_and_figures`.**
  - After `link_names[:] = _dash_link_names(…)` (:27081): `_plan = self._ensure_embed(graphs, kpis, link_names, filters_cfg)`.
  - Linked source (:27137): `self._link_index = self.df.index[_plan["link_rows"].to_numpy(dtype=bool)]`; `linked_source = self._make_source(linked_vars, rows=_plan["link_rows"])`.
  - Linked graph views (:27156-27165, A5): `_df_idx_set = frozenset(_g_fdf.index)`; `_bool_mask = [bool(i in _df_idx_set) for i in self._link_index]`; `if not all(_bool_mask):` build the BooleanFilter and CDSView; member ids `[int(r) for r, keep in zip(linked_source.data[_ROW_ID_COLUMN], _bool_mask) if keep]`.
  - Facet masks (:27178): `_gidx = frozenset(group_df.index)`; `mask = [i in _gidx for i in self._link_index]`.
  - Unlinked graph sources (:27187, :27198): `self._make_source(g_vars, df=filtered_df, rows=_plan["graph_rows"].get(name))`.
  - Unlinked by() panel sources (:27234): `self._make_source(g_vars, df=group_df, rows=_plan["graph_rows"].get(name))`. The panel list is still `_expand_by_groups(g, base_df=self._apply_graph_filter(g))` over the whole data (twoway's empty Foreign panel stays).
  - Linked panel member ids (:27255-27257): `_lids = list(shared_src_render.data[_ROW_ID_COLUMN])`; ids `[int(_lids[i]) for i, keep in enumerate(mask_r) if keep]`.
- **TR-14.7 `_build_filter_widgets` and `_csv_button`.**
  - `for _fi, fc in enumerate(filters_cfg):`; `_frows = self._embed["filter_rows"]`; `_fcol = self.df[fvar][_frows[_fi].reindex(self.df.index, fill_value=False).to_numpy(dtype=bool)]` when `_fi < len(_frows)` (it always is when the plan came from the same `filters_cfg`), else `self.df[fvar]`; `_fcol` feeds `_dash_filter_effective_type` and every builder (dtype kept, so an empty numeric reach is a disabled widget, A7).
  - Snapshot (:27649-27664 and :27862-27867): `_snap = _dash_embed_frame(self.df, self._embed, list(self.df.columns))`; `_orig_data[c]` from `_snap[c]`; `_orig_data[_ROW_ID_COLUMN] = list(self._row_ids_for(_snap))`. Every column is kept (blank where not needed) so the snapshot's shape is unchanged.
  - `_csv_button` text source (:27890-27892): from `_dash_embed_frame(self.df, self._embed, <string columns in self.df>)` (under csv every cell is needed, so the output is unchanged).
  - The docstring (:27515-27518) and the comment block at :27536-27546 and :27654-27658 say "the rows its targets select" instead of "the WHOLE frame".
- **TR-14.8 `render()`.** Move `link_names, filters_cfg = self._parse_link_and_filters(build)` above the report; then `self._embed = None` and `self._ensure_embed(graphs, kpis, link_names, filters_cfg)` (raw `link_names`; the plan expands `_all`); then `_report_dataset_shape(int(self._embed["rows"].sum()), len(self._embedded_row_cols), "dashboard", extra=self._embedded_extra)`. `_n_rows` (:28167) = `int(self._embed["rows"].sum())`. `_report_dataset_shape`'s comment at :849-853 is rewritten: a saved page holds the rows its graphs, cards and filters select (P0.11); the served app's file holds every row; the message text is unchanged.
- **TR-14.9 `_dash_refresh_linked(source, frame, views, snapshot=None, pos_of=None, need=None)`.** A column written from *frame* goes through `_dash_embed_values(frame[col], need[col])` when `need` is given and holds the column; docstring adds the argument. Every existing caller that passes no `need` is unchanged.
- **TR-14.10 Served build and template (`ServerAppBuilder._generate_app_source`).**
  - Build-time plan (:29340-29357): `_eplan = _dash_embed_plan(self.spec, _fdf, getattr(self, "_qual_masks_cache", None), link_opt, filter_specs, _dash_csv_wanted(bo))` inside `try/except ValueError` (None on error); for each dropdown `filter_specs[_fi]`, the effective type is read from `_fdf[var][_eplan["filter_rows"][_fi]]` (A10). `self._frame()` (:29185) already loads the frame and `_qual_masks_cache`.
  - Template: the `_filter_specs = <repr>` lines (:30930-30940) move up to just after `linked_names = set(…)` (:30080-30083); then emit `_EMBED = _dash_embed_plan(spec, df, _qual_masks, sorted(linked_names), _filter_specs, _dash_csv_wanted(bo))`, THEN the relabel block of TR-14.18, THEN `_EMBED_GROWS = {g: df.index[m.to_numpy(dtype=bool)] for g, m in _EMBED['graph_rows'].items()}` and `_EMBED_LINK = _EMBED['link_rows'].to_numpy(dtype=bool)`. `_EMBED_GROWS` therefore holds page ranks. `spec`, `df`, `_qual_masks` and `bo` are bound above (:30028, :30032, :30035).
  - `all_vars` (:30089) and the by() `_gvars` loop (:30786): `for k in _DASH_PLOT_VAR_KEYS:` (A11).
  - Shared source (:30108-30119): `_ldf = df[_EMBED_LINK]`; `_shared_data = {v: _dash_column_values(_dash_embed_values(_ldf[v], _EMBED['need'].get(v))) if v in df.columns else [] for v in linked_vars}`; `_shared_data['index'] = list(_ldf.index)`; `_shared_pos` over `_ldf.index`.
  - Unlinked placeholder (:30121-30136): keys `_DASH_PLOT_VAR_KEYS` (A11); rows `df[df.index.isin(_EMBED_GROWS.get(gname, df.index[0:0]))]`, blanked; plus an `index` column of those labels, so `_dash_refresh_unlinked` refreshes it by identity, never with every row a move keeps. The by() panel placeholder (:30823-30826) the same over `_gdf`'s rows that are in `_EMBED_GROWS[gname]`.
  - Widget loop (:30943): `for _fi, fspec in enumerate(_filter_specs):`; the builder's column (:30966) is `df[fvar][_EMBED['filter_rows'][_fi].to_numpy(dtype=bool)]`.
  - `_brush_rows` (:31004-31011): `_owner_rows[_bgn].intersection(_EMBED_GROWS.get(_facet_to_orig.get(_bgn, _bgn), df.index))`; the shared source's `df.index[_EMBED_LINK]`. After a move (:31115-31121): `_kept_rows = _kept_rows.intersection(_EMBED_GROWS.get(_orig_gn_cb, _kept_rows))`. `_owner_rows` itself is unchanged (the Total panel's aggregate recompute reads it, :31190).
  - Linked move (:31152-31169): `_shared_fdf = _df_ref[_shared_mask & _EMBED_LINK]`; `_dash_refresh_linked(…, pos_of=_shared_pos, need=_EMBED['need'])`.
  - Unchanged in code on purpose: per-layer sources (built from each layer's own rows), `_DASH_MAPPER.dataset = df`, `_csv_rows` and every server-side recompute (they read `df`, which is never sent). After TR-14.18 their frames carry page ranks as labels, so every `index` they write is a rank. No label-reading site is edited (A8 lists them).
- **TR-14.11 Maps.** `test/function_test_map.py` (alphabetical place): `_dash_embed_rows_of` → `test/test_embedded_rows.py::TestEmbedRowsOf::test_a_qualifier_column_is_read_by_index`; `_dash_embed_plan` → `::TestThePlan::test_a_layer_qualifier_intersects_the_graphs`; `_dash_embed_values` → `::TestEmbedValues::test_each_dtype_is_blanked_as_stata_misses_it`; `_dash_embed_frame` → `::TestEmbedFrame::test_rows_and_columns_are_restricted_and_blanked`; `_dash_page_index` → `::TestThePageIndex::test_kept_rows_are_ranked_first_in_data_order`; `_dash_relabel` → `::TestRelabel::test_series_dicts_and_lists_are_relabelled_in_order`; `DashRenderer._set_embed` → `::TestRowIdentitiesAreDense::test_ids_are_ranks_of_the_pages_rows`; `DashRenderer._ensure_embed` → `::TestThePlan::test_the_renderer_computes_the_plan_once`; `DashRenderer._row_ids_kept` → `::TestRowIdentitiesAreDense::test_member_and_qual_ids_are_within_the_ids`; `DashRenderer._row_ids_for` → `::TestRowIdentitiesAreDense::test_an_unranked_label_raises_in_the_aligned_path`; `DashRenderer._make_source` → `::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[plot-if scatter]`. No `program_coverage_map.py` change (no Stata program changes).
- **TR-14.12 The sentinel battery (`test/test_embedded_rows.py`).**
  - Frame `_sentinel_frame()` (10 rows, i = 1..10): `mpg = 9000 + i + 0.5`, `weight = 7000 + i + 0.25`, `price = 5000 + i + 0.75`, `foreign = float(i % 2 == 0)`, `rep = [3,4,3,5,4,3,5,4,3,4]`, `when = 15340 + i` (`%td`), `name = "sent-%02d" % i` (a string variable), `lab = 60 + i` with value labels `{60+i: "lab-%02d" % i}`, `__dashq1` = 1 on rows 2,4,6,8,10, `__dashq2` = 1 on rows 1-3, `__dashq3` = 1 on rows 4-6.
  - Written with `conftest.make_data_json`, then `variableIsString`/`variableTypeIsString` set True for `name` (A9), the value labels passed, and `build_options.formats = {"when": "%td"}`. Before writing, `_write_inputs` drops every `__dash…` column the spec does not name (`dr._dash_qual_cols_named(spec)`, and S02's `build_options.sort_cols` values): `_dash_take_qual_columns` refuses data holding a reserved column the spec does not name (measured: `ValueError: dash: the data hold a column named '__dashq2'; …`).
  - `_page_values(page)`: every `<script type="application/json">` document decoded with `json.loads`; every ndarray (`{"type": "ndarray", "array": {"type": "bytes", "data": …}, "dtype": …}`) decoded with `np.frombuffer(base64.b64decode(...), dtype)`; returns (numbers, strings).
  - `_doc_values(models)`: every property of every model (`properties_with_values(include_defaults=False)`), recursively through dicts, lists, tuples and numpy arrays (datetime64 → epoch ms), with a visited set instead of a depth cutoff; returns (numbers, strings). Used for the served document and for the saved renderer's models after a node-run move.
  - `_excluded_hits(numbers, strings, renderer_df, allowed)`: for every row outside *allowed* and every column in (mpg, weight, price, when as epoch ms read from the renderer's own frame) a number equal within 1e-9, and for `name` a string containing its text. Returns `[(row, column)]`.
  - Value-label text is NOT scanned page-wide (a label set is metadata that lists every code); `TestTheFilterWidgetSpansItsReach::test_a_label_only_excluded_rows_carry_is_not_listed` checks a dropdown's options instead.
- **TR-14.13 Colour-key guard.** `TestColorvarReadsTheLayersRows::test_no_missing_key_both_modes[string|colorlevels|linked]`: `g1 = (scatter mpg weight, qual __dashq1, colorvar(name)) (scatter mpg weight, qual __dashq2)` → the saved and served `CategoricalColorMapper.factors` are both `['sent-02', 'sent-04', 'sent-06', 'sent-08', 'sent-10']` and no legend item reads `(missing)`; `colorvar(price) colorlevels(3)` → the three bins over 5002.75–5010.75 in both modes, no `(missing)`; a linked variant (`link(g1 g2)`, g2 `qual __dashq2`). Passes at the batch-3 base (S07) and after.
- **TR-14.14 Parity corpus (`test/test_mode_parity.py`, R6: appends only, plus E-7 item 7).** `MOVE_CORPUS`'s generated entries pass `kpis=([_kpi()] if t in dr._DASH_LITERAL_TYPES else None)`. Append to `CORPUS`: `_case("two layers with their own qualifiers, range filter (embed rows)", [plot_for("scatter", if_expr="price > 4500"), plot_for("scatter", in_expr="1/3")], bo={"filter": "price, type(range)"})`; `_case("a linked pair with graph qualifiers (embed rows)", bo={"link": "g1 g2", "filter": "price, type(range)"}, graphs=[("g1", [_sc()], None, {"if_expr": "foreign == 1", "in_expr": ""}), ("g2", [_sc()], None, {"if_expr": "price > 10000", "in_expr": ""})])`; `_case("a dropdown under a graph if (embed rows)", [_sc()], bo={"filter": "rep, type(dropdown)"}, if_expr="foreign == 1")`. Append to `MOVE_CORPUS`: the first two with `_MOVES[1]`. `ALLOWED` and `_MUST_WARN` are not edited.
- **TR-14.15 Help (`dash.sthlp`, R3: only these paragraphs).**
  1. Description, after the qualifier paragraph that ends "…is read as your data." (:172), a new `{pstd}` paragraph headed `{ul:What a saved page holds.}`: a saved dashboard holds, for each variable, only the observations that some graph, recomputed card or filter selects with its `if` and `in` (the rows a layer draws, its graph's qualifier and its own together; the rows a card that follows a filter or the brush recomputes over; the rows a filter acts on); nothing of an observation every qualifier excludes is written into the page, and the page numbers its own rows, so no gap shows where one was; anyone who opens the file can read what it holds with View Source; a card's first value and every fitted line and smoother are computed over their own rows and only the result is written, so `lowess, adjust` and `lpoly`'s grid still read every observation in memory, as twoway does, and a `by()` graph finds its panels among every observation its graph's qualifier selects; with `csv`, the page holds every observation of every variable it uses.
  2. Exporting (:923-925): replace "A saved dashboard with filters already contains those rows (the filters need them), but a served one sends the browser only what it draws." with "Without {cmd:csv} a saved dashboard holds only the observations its graphs, cards and filters select (see {help dash##description:Description}); with it the page holds them all, so that the download can be written in the browser, but a served one sends the browser only what it draws."
  3. Filters, a new `{pmore2}` after the paragraph ending "…(see {help dash##export:Exporting})." (:1175-1177): "A widget lists the values of, or spans the range of, the observations that the graphs, link group and cards it filters select, after {cmd:exclude()}; an observation every {it:if} or {it:in} excludes adds no option or bound, and the 1,000-value limit of a dropdown counts those observations only. A filter that reaches no observation -- every graph and card excluded, or graphs that draw no observation -- draws a range or slider greyed out, and a dropdown that lists only All."
  4. Linking (:1047-1048): after the first sentence add "That source holds the observations the group's graphs draw -- each graph's and each layer's {it:if} and {it:in} together -- and no other."
  5. Server Mode (the paragraph beginning "The generated app embeds every observation", :1574; S08 rewrites its middle — append, keep S08's text): "A browser receives only the observations the dashboard draws or filters, as a saved page holds them, numbered as the saved page numbers them, so no row number shows where an excluded observation was; the {cmd:.py} file and its data still hold every observation."
  6. Resource limits (the paragraph headed `{ul:What the data limit counts.}`, :1645; S06 may have edited it — append): "A saved page may hold fewer observations than the limit counts: only those its graphs, cards and filters select (see {help dash##description:Description}); the size the dashboard reports when it is large counts those, and a served app's report counts every observation."
- **TR-14.16 The served `index` carries no observation number (ratified 01oct2026; replaces the struck residual entry).** No BUGS.md entry is opened: S01's P0.11 entry closes with the served `index` among its fixes (14-16). `TestTheServedIndexResidual` is not written. In its place, `test/test_embedded_rows.py::TestTheServedIndexIsARank` (TDD test stubs) pins, failing first:
  1. In both modes, every `index` value of every ColumnDataSource is an integer below m (m = the number of rows BR-14.1 keeps). The battery's `_CASES` are checked before a move and, served, after the case's move.
  2. A row-identity source numbers each row as the saved page numbers that observation.
  3. Guards that must stay green through the relabel: a brush selection, a linked selection, a qualified filter card after a move, the csv download, and the presence of an `index` on every source that carries frame columns.
- **TR-14.17 Security (rule 1).** Data minimisation by construction at the choke points (TR-14.5, 14.7, 14.9, 14.10), and identity minimisation by one relabel (TR-14.18). Both are checked black-box: the battery covers every embedded JSON document and every served model property before and after moves, and `TestTheServedIndexIsARank` covers every `index` column. Qualifier columns stay validated by `_dash_take_qual_columns`, and text qualifiers go through `_dash_qualified_frame`'s whitelist. There is no new input surface, no `eval` and no user text in emitted code: the emitted plan and relabel lines are fixed strings, and `_filter_specs` is the existing `repr`. `_dash_relabel` refuses (ValueError) a row map not indexed like the frame, so it never re-pairs rows silently. Disclosed residuals: csv; observations selected only for computed layers; the served `.py` and data on disk (SD5; written privately where the system allows, S08 as ratified 01oct2026).
- **TR-14.18 The served relabel (ratified 01oct2026, SD3).** Two module functions placed after `_dash_embed_frame`, with no nested functions, no lambdas and no `eval`:

  ```python
  def _dash_page_index(index, rows):
      """The served frame's row labels under the page plan (WP-29 P0.11):
      the rows *rows* keeps are numbered 0..m-1 in the data's order --
      the saved page's __dash_row__ ranks -- and every other row m..N-1,
      also in the data's order.  A source holds planned rows only, so no
      browser receives a label of m or more, and no label shows where an
      excluded observation was.  The order of the rows is not changed:
      `in' (iloc) and every label-aligned mask keep their meaning.  The
      identity when *rows* keeps every row."""
      keep = rows.reindex(index, fill_value=False).to_numpy(dtype=bool)
      order = np.concatenate([np.flatnonzero(keep), np.flatnonzero(~keep)])
      new = np.empty(len(index), dtype=np.int64)
      new[order] = np.arange(len(index), dtype=np.int64)
      return pd.Index(new)


  def _dash_relabel(obj, old, new):
      """*obj* with every pandas Series in it -- itself, or nested in dicts
      and lists -- given the labels *new* in place of *old*, row for row
      (WP-29 P0.11).  Anything else is returned unchanged.

      Raises:
          ValueError: a Series is not indexed exactly like *old*, so
              re-pairing it by position would mix rows.
      """
      if isinstance(obj, pd.Series):
          if not obj.index.equals(old):
              raise ValueError("dash: a row map is not indexed like the data.")
          return obj.set_axis(new)
      if isinstance(obj, dict):
          return {k: _dash_relabel(v, old, new) for k, v in obj.items()}
      if isinstance(obj, list):
          return [_dash_relabel(v, old, new) for v in obj]
      return obj
  ```

  - Emitted in `_generate_app_source` right after the `_EMBED = _dash_embed_plan(…)` line of TR-14.10 and before `_EMBED_GROWS`, as fixed strings:
    ```
    "    # WP-29 P0.11: the browser receives the saved page's row numbers,",
    "    # never an observation's own (_dash_page_index).  Every map keyed",
    "    # by row is relabelled with the frame, row for row.",
    "    _dash_old_index = df.index",
    "    df.index = _dash_page_index(_dash_old_index, _EMBED['rows'])",
    "    _qual_masks = _dash_relabel(_qual_masks, _dash_old_index, df.index)",
    "    _sort_keys = _dash_relabel(_sort_keys, _dash_old_index, df.index)",
    "    _EMBED = _dash_relabel(_EMBED, _dash_old_index, df.index)",
    ```
    The `_sort_keys` line is emitted only when the batch-3 base binds `_sort_keys` in `make_document` (S02 TR-02.6; grep `"    _sort_keys = meta['sort_keys']"`). `df.index = …` changes the one frame object in place, so `_DASH_MAPPER.dataset` (the same object) agrees.
  - Audit (task 14-11): in the emitted app of a spec with a layer qualifier, every line between `spec, df, meta = _load_spec_and_data()` and `_dash_old_index = df.index` that reads `.index` or builds a `pd.Series`/`dict` keyed by rows is listed in `<scratch>/14-relabel-audit.txt`. At `7421d3d` there are none: `_qual_masks` is the only row-keyed object bound in that span, and the loader built it. Any line a batch-1/2 section added there (for example S02's `_sort_keys`) is relabelled through `_dash_relabel` in the block above.
  - The saved renderer is unchanged by TR-14.18. Its ranks come from `_row_pos` (TR-14.4), and `_set_embed`'s `_page_labels` is the list `[_dash_old_index[i] for i in flatnonzero(rows)]`, the served relabel's inverse on the planned rows. So `r._page_labels[label]` turns a served `index` label into the observation's original label (TDD tests).
  - The build-time plan in `ServerAppBuilder` (TR-14.10) reads values only and is not relabelled.

## Boundaries

- **Not changed:** `dash.ado` and `dash_parse.mata` (every row is still exported, because Stata's whole-data rules read the data file); `_dash_cell_cap` and `_dash_embedded_cells` (a conservative upper bound); `_FILTER_JS`, `_BRUSH_JS`, `_DASH_CSV_SAVED_JS` (they match rows by identity; the prototype's node runs passed); `self.mapper.dataset`/`_DASH_MAPPER.dataset`; `_expand_by_groups`, `_dash_by_panel_dropped`; `_build_kpi_html` first values; the served `_csv_rows`; per-layer served sources' code (their `index` becomes a rank through TR-14.18's relabel, with no edit); every served label reader (A8); the WebGL threshold (:25951); `_dash_filter_widget` (the empty dropdown stays enabled, A7).
- **Not this section's:** the served brush reading a mapper copy's position as a label (E-8 probe 5; S15 residual candidate); the colour domain (S07, A1 guard only); join order (S02, only the `_jo` argument); lpoly (S11); the stale cue (S12; only the row-id audit of TR-14.4); the token (S13); twoway's refusal of two colorvar layers (S07 residual).
- **Tracking documents (A5):** `GAPS2.md`, `ROADMAP.md`, `AGENTS.md`, `REMAINING.md`, `DROPIN-REMAINING.md` are S15's; their text is in "Notes for the closeout".
- **cscripts (R1):** one block `S14` in `test/test_wp29_truth.cscript`; no new script, no runner or hygiene-pin edit; `test_gaps2_truth.cscript` is not touched.
- **Silent when honoured:** no new note on the success path. A10 removes the "drawn as type(range)" note where the reach is within the limit (CHANGELOG).

## Stata truth

**Fixture.** New `scripts/extract_embedded_rows_truth.do` writes `test/fixtures/embedded_rows_truth.json` (D12 `_meta`: `stata_version`, `born_date`, `dash_commit` read through `Macro.getLocal` after `shell git -C "${ZA_REPO}" rev-parse HEAD`, `extracted`, `source`), in the form of `scripts/extract_filter_truth.do` (its header, `ZA_REPO` global, tempfile + `file read` for the sha; the python block never calls Stata, writes a backtick as `\x60`, and dumps with `indent=1, sort_keys=True`). Probes:
- `p1`: `twoway (scatter mpg weight if foreign) (scatter mpg weight if price>10000), nodraw`; for k = 0, 1 `serset set k`, `serset`, `r(N)` → `serset_n: [22, 10]`; `gen long obs = _n`; `levelsof obs if foreign`, `levelsof obs if price>10000`, `levelsof obs if foreign | price>10000` → `layer_obs`, `union_obs` (30 values), `union_n: 30`.
- `p2`: `twoway scatter rep78 weight if !foreign, nodraw` → `serset_n: 52`, `count_if: 52`, `count_nonmissing: 48`.
- `p3`: the three by() commands of E-1, each `graph export` to `.svg` under a `tempfile` stem; subtitles read with `cert_svg_texts` from `test/cert_svg.do` (run `do "<repo>/test/cert_svg.do"` first) and kept only if equal to a `foreign` value label; `serset dir` counts → `{"single": {"subtitles": ["Domestic"], "serset_n": [52]}, "two": {"subtitles": ["Domestic", "Foreign"], "serset_n": [52, 1, 0]}, "with_all": {"subtitles": ["Domestic", "Foreign"], "serset_n": [52, 0, 22]}}`.
- `p4` (auto): `price_if_foreign: [min, max]` and `price_all: [min, max]` (`summarize price [if foreign]`), `rep78_if_foreign` and `rep78_all` (`levelsof rep78 [if foreign]`, as floats), `mpg_union: {"mean": …, "text": …}` (`summarize mpg if foreign | price > 10000`, the text `%9.0g`, trimmed), `count_foreign_in_40_60` (`count if foreign==1 in 40/60`).
- `p5` (the parity frame typed in with `input`, the ten rows of E-1): `price_gt_4500: [min, max]`, `price_levels_gt_4500` (`levelsof price if price > 4500`), and `{"mean", "text"}` records `mpg_foreign_in_3_8`, `mpg_in_3_8`, `mpg_foreign`, `mpg_all`.
- `p6`: `twoway lowess mpg weight if foreign, adjust nodraw`, `serset set 0`, `serset use, clear`, `summarize __000000` → `{"mean": …, "mean_text": "21.2973"}`.
- Every probe record also carries `"command"`: the Stata command text that produced it.

Run: `dash_nobrowser=1 scripts/stata_slot.sh <scratch>/s14 <W>/scripts/extract_embedded_rows_truth.do` with `ZA_REPO` set by the do-file's default or by `global ZA_REPO "<W>"` in a two-line wrapper; `git add -f test/fixtures/embedded_rows_truth.json`. `test/test_fixtures_are_committed.py` finds the fixture by the name `test_embedded_rows.py` reads; it needs no edit unless its counts are pinned (run it; edit only on failure).

**Certification block** (`test/test_wp29_truth.cscript`, above the marker, after any lower-numbered block, R1; the header comment gains `*!   S14  embed rows: what a saved page holds against twoway's sersets and Stata's counts (ER-01..ER-08)`), gated `WP29_ONLY=S14`, every case measured live on `sysuse auto` against twoway or Stata; files under `w29_work`, erased at the end; pages and apps read through `test/embed_truth_check.py` in `python:` blocks that never call Stata back except `sfi.Macro.setGlobal`:
- **ER-01** `dash (scatter mpg weight if foreign) (scatter mpg weight if price>10000), saving(er01.html, replace)`: page distinct row ids == `count if foreign | price>10000` (30); the two scatter views select 22 and 10 rows == twoway's `serset` `r(N)` for the same command. At the base: 74.
- **ER-02** `dash (scatter mpg weight if foreign==0) (scatter mpg weight if price>15000), by(foreign) saving()`: panel titles == twoway's SVG subtitles (`Domestic`, `Foreign`); page rows == `count if foreign==0 | price>15000`.
- **ER-03** `dash scatter mpg weight if foreign, name(g1)`, `dash scatter price weight if price>10000, name(g2)`, `dash build, link(g1 g2) saving()`: page rows 30; non-blank `mpg` cells == `count if foreign` (22), `price` cells == `count if price>10000` (10). At the base: 74/74/74.
- **ER-04** g1 `if foreign` + `dash kpi mean(price)` + `filter(rep78)`: `mpg` cells 22, `price` cells == `_N` (74: the card recomputes over every row). At the base: mpg 74.
- **ER-05** g1 `if foreign` with `filter(price, type(slider))`, `filter(rep78, type(dropdown))`, saved page and served app (in-process): slider start/end == `summarize price if foreign` (3748, 12990) in both; dropdown labels == `levelsof rep78 if foreign` (3 4 5) in both. At the base: 3291/15906 and 1-5.
- **ER-06** g1 `if foreign`, `dash build, csv`: snapshot rows == `_N`; graph source rows == `count if foreign`.
- **ER-07** ER-03's registry + `filter(price, type(range))`, `dash build, server saving(er07.py) replace`, app loaded in-process (A13): shared source rows == 30; after setting the range to (5000, 15906) and firing its callbacks, shared rows == `count if (foreign | price>10000) & inrange(price,5000,15906)`. At the base: 74.
- **ER-08** `dash lowess mpg weight if foreign, adjust saving()`: the page's lowess y values == twoway's serset (`twoway lowess mpg weight if foreign, adjust nodraw`, `serset use`) to 1e-6, their mean 21.2973 (whole-data rule kept). Passes at the base (guard).

Driver (index "The cscript driver"):

```sh
printf 'adopath ++ "%s/"\ncd "%s/test"\ndo "%s/test/%s"\n' "<W>" "<W>" "<W>" test_wp29_truth.cscript > <scratch>/s14/run_test_wp29_truth.do
cd "<W>" && dash_nobrowser=1 WP29_ONLY=S14 scripts/stata_slot.sh <scratch>/s14 <scratch>/s14/run_test_wp29_truth.do   # log: <scratch>/s14/run_test_wp29_truth.log
```

Read the log; never relaunch to check. A SKIP (exit 222, `c(python_exec)` empty) is not a pass.

## TDD test stubs

All in **`test/test_embedded_rows.py`** (new) unless noted. Expected base results are `7421d3d`'s measured ones; 14-06 re-measures them at the batch-3 base.

**Units (fail at base with AttributeError: the functions do not exist)**
- `TestEmbedRowsOf::test_a_qualifier_column_is_read_by_index`, `::test_a_text_qualifier_counts_in_over_the_frame` (`in 3/8` on a 10-row frame → rows 2..7), `::test_no_qualifier_is_every_row`, `::test_an_unknown_column_raises`, `::test_a_qualifier_the_whitelist_refuses_is_every_row_quietly` (no warning recorded).
- `TestThePlan::test_a_graph_qualifier_selects_the_graphs_rows`, `::test_a_layer_qualifier_intersects_the_graphs`, `::test_the_total_panel_adds_its_own_rows`, `::test_a_literal_layer_reads_no_row`, `::test_hover_and_by_columns_are_needed_on_the_layers_rows`, `::test_option_columns_are_needed_on_the_layers_rows` (colorvar, mlabel, wexp), `::test_a_brush_card_needs_its_variable_on_every_source`, `::test_a_filter_reaches_the_graphs_it_applies_to`, `::test_exclude_narrows_the_reach`, `::test_a_link_group_is_reached_unless_every_member_is_excluded`, `::test_a_filter_mode_card_adds_its_own_rows`, `::test_a_static_card_adds_nothing`, `::test_csv_needs_every_cell_and_moves_no_row_set`, `::test_an_empty_frame`, `::test_served_filter_keys_are_read` (`var` and `varname`), `::test_a_graph_options_qualifier_is_ored`, `::test_link_all_is_expanded`, `::test_the_filters_are_never_parsed` (a raw string `filter` in build_options is ignored), `::test_the_renderer_computes_the_plan_once`.
- `TestEmbedValues::test_each_dtype_is_blanked_as_stata_misses_it` (float NaN, datetime NaT, object `""`, bool NaN), `::test_all_needed_returns_the_series_itself`, `::test_none_blanks_everything`.
- `TestEmbedFrame::test_rows_and_columns_are_restricted_and_blanked`, `::test_an_absent_column_is_skipped_and_order_kept`.
- `TestThePageIndex` (TR-14.18; values measured on the reference implementation):
  - `::test_kept_rows_are_ranked_first_in_data_order`: `RangeIndex(10)`, rows True at 1, 3, 5, 7, 9 → `[5, 0, 6, 1, 7, 2, 8, 3, 9, 4]`.
  - `::test_every_row_kept_is_the_identity`: `[0..9]`.
  - `::test_an_empty_frame`: `[]`.
  - `::test_a_non_range_index`: `Index([10, 20, 30])`, rows `[False, True, True]` → `[2, 0, 1]`.
- `TestRelabel`:
  - `::test_series_dicts_and_lists_are_relabelled_in_order`: a plan-shaped dict (`rows`, `need` dict, `graph_rows` dict, `link_rows`, `filter_rows` list) comes back with every Series' index equal to the new labels and its values unchanged in order.
  - `::test_a_series_not_indexed_like_the_data_raises`: `pd.Series([1, 2])` against `RangeIndex(10)` → `ValueError` whose message contains "not indexed like the data".
  - `::test_other_values_pass_through`: `"x"` and `None` are returned unchanged.

**Regressions (fail at base, measured in E-2/E-3/E-6)**
- `TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[case]` — one module-level list `_CASES` of `(id, spec builder, allowed rows)`, ids exactly: `plot-if scatter` (q1), `two plots q1 q2`, `link q1 q2` (g1 graph q1, g2 graph q2), `dropdown + graph q1` (`filter(foreign)`), `slider + graph q1` (`filter(price, type(slider))`), `by(foreign) + plot q2`, `by(foreign, total) + plot q2` (plot `qual_col_total` `__dashq2`), `line plot q1 + range`, `area plot q1 + range`, `bar plot q1 + range`, `rarea plot q1 + range`, `rspike plot q1 + range`, `pcspike plot q1 + range` (each with `filter(price, type(range))`), `histogram plot q1 + range`, `kdensity plot q1 + range`, `option columns` (scatter q1 with `mlabel(name) colorvar(price)`, graph `hover(name when)`, a second layer `lfit` q1 with `weight: aweight, wexp: price`), `date x + date range` (`line mpg when` q1, `filter(when, type(range))`), `brush card + link` (link q1/q2 and an `update(brush)` card on mpg), `layout(bs)` (plot-if scatter under `layout: bs`), `tabs` (g1 with a layer q1, g2 with a layer q2, `tabs: "A: g1 / B: g2"`). Fails at base for every case whose sentinel rows are excluded by a layer qualifier, a link group or a filter's snapshot (e.g. `plot-if scatter` → hits rows 1,3,5,7,9); `layout(bs)` and `tabs` fail with them.
- `TestTheSavedPageHoldsOnlySelectedRows::test_none_after_a_move[case]` — the same cases with a range move run under node (`js_runner.JsSession`), then `_doc_values` over every model.
- `TestTheServedDocumentHoldsOnlySelectedRows::test_no_excluded_value_is_sent[case]` and `::test_none_after_a_filter_move[case]` — base: `link q1 q2` rows 5,7,9; `slider + graph q1` row 1; `by(foreign) + plot q2` after a move row 10.
- `TestTheRowsAreTheUnionOfTheQualifiers::test_distinct_row_ids_both_modes` — parity frame, two plots q1/q2: 7 saved ids `0..6`; served shared (linked variant) 7 rows. `::test_the_page_rows_are_statas_union_on_auto` — fixture `p1.union_obs` == `[l + 1 for l in r._page_labels]`. Base: 10 and 74.
- `TestTheFilterWidgetSpansItsReach::test_slider_and_range_bounds_both_modes` (graph `if price > 4500`, `(4749.0, 11385.0)` = fixture `p5`; base 3799), `::test_dropdown_values_both_modes` (auto, g1 `if foreign`, `filter(rep78)` → `['All', '3', '4', '5']` = fixture `p4`; base `['All', '1', '2', '3', '4', '5']`), `::test_exclude_narrows_the_reach`, `::test_an_unqualified_filter_mode_card_spans_every_row` (guard: 3799–11385), `::test_a_label_only_excluded_rows_carry_is_not_listed` (`filter(lab)` under graph q1: no `lab-01`, `lab-03` … option; base lists them).
- `TestAnEmptyReach::test_range_slider_and_dropdown_both_modes` (graph selects no row: disabled [0,1] range/slider, Select `['All']`; base: the data's range), `::test_date_range_both_modes` (`%td`: disabled RangeSlider [0,1] in both, no exception; base: DateRangeSlider).
- `TestAFilterEveryTargetExcludes::test_widget_state_both_modes` (`exclude(g1 k1)`: disabled range, `['All']` dropdown, equal in both modes; base: whole-data widget) and `::test_a_literal_only_dashboard` (`function` graph + `filter(foreign)`: `['All']` both modes).
- `TestTheFilterTypeFollowsTheReach::test_a_dropdown_within_the_limit_on_its_reach_both_modes` (`limits: {filter_options: 7}`, price dropdown under `if price > 4500`: a 7-entry Select in both, no "drawn as type(range)" warning in either; base: RangeSlider and the note).
- `TestCsvDoesNotMoveTheDashboard::test_widgets_sources_and_cards_equal_with_and_without_csv` (widget start/end/options, linked source ids, the cleared brush card of a qualified link group equal; only the snapshot and text source row counts differ). Base: passes for widgets only by accident (both whole data); fails on the snapshot count assertion (`10 != 6` without csv).
- `TestRowIdentitiesAreDense::test_ids_are_ranks_of_the_pages_rows` (plot q1 → `[0..4]`; base `[1,3,5,7,9]`), `::test_member_and_qual_ids_are_within_the_ids` (graph `if foreign` + plot `if price>10000` + qualified brush card: every `member_ids`/`qual_ids` ⊆ the page's ids), `::test_an_unranked_label_raises_in_the_aligned_path`, `::test_member_ids_never_fall_back_to_positions`.
- `TestABrushCountsTheRowsTheGraphShows::test_a_layers_own_in_after_a_move_both_modes` (`'25.66667'` = fixture p5; base 23.4), `::test_a_layers_own_in_cleared_both_modes` (`'22.83333'`; base 21.5), `::test_a_qualified_link_groups_cleared_brush_both_modes` (auto, `'22.13333'` = p4; base 21.2973), `::test_a_by_panel_with_a_layer_qualifier_both_modes` (by(foreign), layer `if price > 4500`: each panel's cleared card == pandas mean over that panel's layer rows, equal in both modes).
- `TestAfterAMoveBothModesDrawTheSameRows::test_linked_by_with_a_layer_if` and `::test_linked_graph_if_with_a_layer_if` — saved via node, served via callbacks, each renderer's drawn rows equal across modes and equal to the oracle (`_saved_with_qualifier`).
- `TestTheJoinKeyFollowsThePagesRows::test_sort_varlist_under_a_layer_if_both_modes` — one graph, one layer `line mpg weight` with `qual_col "__dashq3"` (rows 4-6), `"sortvars": "price"`, `build_options.sort_cols = {"price": "__dashs1"}`, and the data column `__dashs1 = [1, 2, 3, 6, 5, 4, 7, 8, 9, 10]` (rows 1-3 ascending, rows 4-6 descending): the saved line's row order (`__dash_row__` mapped through `r._page_labels`) == the served line's `index` order mapped through the same `r._page_labels` (served labels are page ranks after 14-11, TR-14.18; identity when the attribute is absent) == labels `[5, 4, 3]` (rows 6, 5, 4). It PASSES at the batch-3 base (ids are still positions there); its red run is made inside 14-09 on the tree with dense ranks and restricted sources but S02's `_jo` still reading `self.sort_keys` (the page holds rows 4-6 as ranks 0-2, so the positional key reads rows 1-3's ascending ranks and joins 4, 5, 6), and that failure text is added to `<scratch>/14-P0.11-failure.txt`.
- `TestTheServedIndexIsARank` (TR-14.16/TR-14.18; ratified 01oct2026; replaces the struck `TestTheServedIndexResidual`). Helpers: `_index_values_doc(doc)`, every `data["index"]` value of every ColumnDataSource in `doc.roots[*].references()`; `_index_values_page(page)`, every ColumnDataSource's `index` array in every embedded JSON document, ndarrays decoded as `_page_values` decodes them. *m* = `len(allowed)` of the case.
  - `::test_no_index_label_outside_the_pages_ranks[case]` (`_CASES`, ids as the battery). Saved: every `_index_values_page` value is an integer in `range(m)`. Served (message `served:`): every `_index_values_doc` value is too. Fails at base: served `[plot-if scatter]` labels {1, 3, 5, 7, 9} with m = 5. Saved `[line plot q1 + range]` fails on the mapper copy's whole-frame positions (E-8 probe 1: `[3, 7, 9, 4, 1, 6]` on the parity frame).
  - `::test_none_after_a_filter_move[case]`: served only, the same assertion after the case's move fired through the widget's `_callbacks`. The saved page's copies are filtered from their own snapshots by row id (`_FILTER_JS`), so they can only shrink.
  - `::test_a_row_is_numbered_as_the_saved_page_numbers_it[case]` for `plot-if scatter`, `two plots q1 q2`, `link q1 q2` and `by(foreign) + plot q2`. For each scatter renderer, each drawn row (through its view) carries a sentinel `mpg`. Its served `index` label must equal the saved `__dash_row__` of the row with the same `mpg`, and `r._page_labels[label]` must equal that observation's original label. Fails at base: `AttributeError: … '_page_labels'`, then the label check (served 5, 7, 9 against ranks 2, 3, 4).
  - `::test_a_linked_selection_names_the_same_observations_both_modes`, sentinel spec `link q1 q2`: (a) the served shared source's `index` == `list(range(m))` == the saved linked source's `__dash_row__`; (b) selecting positions `[0, 1]` of the shared source with a `update(brush)` card on `mpg` gives, in both modes (`test_served_filter_move._saved_selection`/`_served_selection`), the pandas mean of `mpg` over observations `r._page_labels[0:2]`; (c) both linked graphs' views list those two positions. Fails at base: (a) shared `index` is `[0..9]` with m = 7.
  - Guards (pass at base and after; the relabel must not break them):
    - `::test_a_brush_selection_names_its_observations_both_modes`. Parity frame, `scatter mpg weight if price > 4500`, `filter(price, type(range))` and `kpi mean(mpg), update(brush)`. In each mode, brush the first two positions the scatter DRAWS: the view's selected positions (`BooleanFilter`/`IndexFilter`), or `[0, 1]` with no view. As a browser's box or lasso can only select drawn points, never brush undrawn ones. The card is `23.5` in both modes, the mean of `_DF.mpg` at observations 1 and 3 (17, 30). Measured at `7421d3d` with `test_served_filter_move._served_selection(spec, 0, [0, 1], [])` → `({'k1': '23.5'}, …)` and `_saved_selection(spec, 0, [1, 3], [])` → `({'k1': '23.5'}, …)`. The saved view is `BooleanFilter [F, T, F, T, T, F, T, T, F, T]`. After 14-09 the saved source holds the six planned rows, so the drawn positions are `[0, 1]` there too. Trap, measured: brushing saved `[0, 1]` at the base reads `19.5`, because position 0 is observation 0, which the layer does not draw. The test must take the drawn positions from the view, never hard-code them.
    - `::test_a_qualified_card_after_a_move_both_modes`. Sentinel; graph `qual_col __dashq1`; a card `mean(mpg)`, `update(filter)`, `qual_col __dashq3` (rows 4-6); `filter(price, type(range))` moved to `(5003.0, 5010.75)`. The card equals the pandas mean of `mpg` over rows 4-6 with price in range, in both modes. Mutation: relabelling `df` but not `_qual_masks` makes it fail.
    - `::test_csv_makes_the_relabel_the_identity`. `test_export._export_spec()` with its scatter given `in_expr "2/3"`: `test_export._saved_file(...) == test_export._served_file(...)` at `{}` and at `{"mpg": (26.0, 40.0)}`, and the served scatter source's `index` equals the original positions (csv plans every row). Measured at `7421d3d`: `saved == served` is True at both states, the first lines are `'mpg,foreign,make,day\r\n22,Domestic,007,2020-01-16\r\n17,Foreign…'` and `'mpg,foreign,make,day\r\n30,Domestic,,\r\n'`, and the scatter's `index` is `[1]` (rows 2-3; row 3's missing mpg is dropped). Both must hold unchanged after 14-11.
    - `::test_every_row_source_carries_an_index`. E-8 probe 2's fifteen types × unlinked/`link(g1)`: no served ColumnDataSource holds a frame-variable column without an `index` column.

**Guards (pass at base and after)**
- `TestColorvarReadsTheLayersRows::test_no_missing_key_both_modes[string|colorlevels|linked]` (TR-14.13; fails only if S07 is absent).
- `TestWholeDataRulesStillRead::test_lowess_adjust_reads_every_row` (`test/fixtures/qualified_stat_truth.json`), `::test_lpoly_grid_follows_the_datasets_n` (the same fixture's lpoly probe; S11's grid), `::test_by_panels_are_twoways` (fixture `p3`: one panel for a single `if foreign==0` plot; two with Foreign empty for two plots), `::test_missing_values_stay_selected` (fixture `p2`: `scatter rep78 weight if !foreign` holds 52 rows), `::test_a_static_card_reads_every_row_while_the_page_holds_the_graphs`, `::test_a_text_in_qualifier_is_counted_on_the_whole_data`.
- `TestTheCsvContract::test_csv_still_embeds_every_row_both_modes`.
- `TestTheHelpSaysSo::test_the_description_says_what_a_saved_page_holds`, `::test_the_old_csv_sentence_is_gone`, `::test_the_filters_paragraph_names_each_empty_widget` (A7: "greyed out" and "lists only All"), `::test_the_brush_sentence_stays` (:1407-1409), `::test_the_linking_server_and_limit_sentences` (the Server Mode sentence includes "numbered as the saved page numbers them", TR-14.15 item 5) — whitespace-collapsed help text; fail at base except the brush one.

**Flipped (E-7)** — ten items, each with a `Flipped:` line (item 10 added by the 01oct2026 ratification).

**Mutation table**

| break this | test that must die |
|---|---|
| `_make_source` ignores `rows` | `TestTheSavedPageHoldsOnlySelectedRows[plot-if scatter]` |
| skip `_dash_embed_values` in `_make_source` | `[two plots q1 q2]` (rows 5,7,9's mpg on layer 2's rows) |
| linked source built without `rows=` | `[link q1 q2]`, `TestTheRowsAreTheUnionOfTheQualifiers` |
| linked view mask over `self.df.index` (A5) | `TestAfterAMoveBothModesDrawTheSameRows` |
| snapshot from `self.df` | `[dropdown + graph q1]` |
| `_fcol = self.df[fvar]` | `TestTheFilterWidgetSpansItsReach::test_slider_and_range_bounds_both_modes` |
| served widget from `df[fvar]` | the same, served half |
| served shared from `df` | `TestTheServedDocumentHoldsOnlySelectedRows[link q1 q2]` |
| `_dash_refresh_linked` without `need` | `::test_none_after_a_filter_move[link q1 q2]` |
| csv widens `filter_rows` | `TestCsvDoesNotMoveTheDashboard` |
| `_row_ids_for` keeps `pos.get(idx, i)` | `::test_an_unranked_label_raises_in_the_aligned_path` |
| `_jo` reads `self.sort_keys` | `TestTheJoinKeyFollowsThePagesRows` |
| plan drops by(, total) rows | `[by(foreign, total) + plot q2]` (Total panel draws fewer rows) and `test_mode_parity` |
| plan re-parses filters | `test_mode_parity.py::TestTheTwoModesAgree::test_same_warnings[filter() with an unknown type]` |
| served sources built from `df` without the TR-14.18 relabel | `TestTheServedIndexIsARank::test_no_index_label_outside_the_pages_ranks[plot-if scatter]` |
| relabel `df` but not `_qual_masks` | `TestTheServedIndexIsARank::test_a_qualified_card_after_a_move_both_modes`, `TestTheServedDocumentHoldsOnlySelectedRows::test_no_excluded_value_is_sent[two plots q1 q2]` |
| relabel `df` but not S02's `_sort_keys` | `TestTheJoinKeyFollowsThePagesRows` (served half) |
| `_dash_page_index` ranks the kept rows in another order (e.g. reversed) | `TestThePageIndex::test_kept_rows_are_ranked_first_in_data_order`, `TestTheServedIndexIsARank::test_a_row_is_numbered_as_the_saved_page_numbers_it` |
| `_dash_relabel` re-pairs a Series by position without the index check | `TestRelabel::test_a_series_not_indexed_like_the_data_raises` |
| relabel placed after the shared source is built | `TestTheServedIndexIsARank::test_a_linked_selection_names_the_same_observations_both_modes` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| plan, rows-of, values, frame units | pytest | none | n/a |
| no excluded value on the page / in the document, before and after moves | pytest + node (saved), callbacks (served) | none (sentinels) | yes |
| rows are the union of the qualifiers | pytest | `p1` | yes |
| widget domain, empty reach, every target excluded, effective type | pytest | `p4`, `p5` | yes |
| csv moves nothing else; csv contract | pytest | none | yes |
| dense ids; aligned vs dropping | pytest | none | saved |
| brush counts | pytest + node | `p4`, `p5` | yes |
| S02 join key on page ranks | pytest | none | yes |
| colour key guard | pytest | none | yes |
| whole-data rules | pytest | `qualified_stat_truth.json`, `p2`, `p3` | yes |
| parity corpus and move corpus | `test_mode_parity.py` | none | yes |
| Stata's sersets, counts and summaries against dash's pages and app | block S14, ER-01..ER-08 | live Stata | yes |
| help sentences | pytest | none | n/a |
| `index` columns hold page ranks only; served row numbers equal the saved page's; brush, linked selection, qualified card after a move and csv unchanged by the relabel | pytest (+ node for the saved selections) | none (sentinels, parity frame, `test_export._export_spec`) | yes |
| relabel helpers | pytest | none | n/a |

Acceptance criteria:
- **AC-14.1** `python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider` passes with no skip other than node-absent skips (and a module test asserts the node cases ran).
- **AC-14.2** Under `WP29_ONLY=S14`, `test_wp29_truth.cscript` prints `ER-01 PASS` .. `ER-08 PASS` (8 lines), no `FAIL`, no `r(` error.
- **AC-14.3** `test_mode_parity.py`, the R2 registry tests and every E-7 file pass; each flip has a `Flipped:` line; `ALLOWED` and `_MUST_WARN` unchanged.
- **AC-14.4** The full suite is green once in the worktree. BUGS.md's P0.11 entry is closed in place, naming existing tests including `TestTheServedIndexIsARank`. No BUGS.md entry is opened: `grep -c '^- \[ \] Title:' BUGS.md` prints the same number in the worktree as at the batch-3 base (4 at `7421d3d`, as S15's AC-15.1 expects). `WP29_OPEN` has no `"P0.11"`. The `<!-- WP-29 P0.11 -->` marker is replaced by one line ending `(WP-29, P0.11)` under `### Security`.
- **AC-14.5** `cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "ServedIndexIsARank or ThePageIndex or TestRelabel"` passes. `grep -c "TestTheServedIndexResidual" <W>/test/test_embedded_rows.py <W>/BUGS.md` prints 0 for both files.

## Tasks

**Commit boundary:** ONE commit (P0.11) holding 14-02 to 14-16, subject `Embed only the rows a page's graphs, cards and filters read (WP-29 P0.11)`, made by 14-16 on `wp29-s14` after one green full suite in the worktree; the body opens with `<scratch>/14-P0.11-failure.txt`. `<W>` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s14`; `<scratch>` the session scratchpad. Every Stata run goes through `scripts/stata_slot.sh` with `dash_nobrowser=1`; every pytest run is targeted (`-q -n0 -p no:cacheprovider`) except the one full run of 14-16.

<task type="checkpoint" id="14-01">
  <name>Record impact and copy the ratified decisions</name>
  <files>none</files>
  <action><![CDATA[
Impact part (index R8: one GitNexus index, of the main checkout, built by step 0c and rebuilt after each batch lands; `npx gitnexus analyze` never runs in a worktree). Verify the per-batch impact approval that step k.0 recorded (`<scratch>/batch-3-impact.txt`). Then run `gitnexus_impact({target, direction: "upstream"})` against that index for `_make_source`, `_row_ids_for`, `_kpi_qualifier_row_ids`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, `_csv_button`, `render`, `_report_dataset_shape`, `_dash_refresh_linked`, `_generate_app_source`, `_load_spec_and_data` (the relabel sits after its call). Write each result to `<scratch>/14-impact.txt`; if the index cannot be read, copy Evidence E-5's grep table there and say so. Report every HIGH/CRITICAL result (expected: `_make_figure_body`, `render`, `_build_sources_and_figures`, `_generate_app_source`).
Decision part (index "Decisions for maintainer ratification"; no question is asked). Copy the `S14 SD1-SD6` row and the maintainer's verbatim answer 4 from `<scratch>/wp29-ratified.txt` into `<scratch>/14-decisions.txt`, followed by this section's reading of them: SD1, SD2, SD4, SD5 and SD6 ratified as written; SD3 saved ratified; SD3 served struck and replaced by TR-14.16/TR-14.18 (no S3 entry, served `index` = page ranks). If the S14 row is missing or reads "pending", stop before any edit (step 1 was broken).
  ]]></action>
  <verify><![CDATA[`<scratch>/14-impact.txt` exists and names each of the twelve symbols. `grep -c "Resolve the server app's index known gap" <scratch>/14-decisions.txt` prints 1. `grep -ci "pending" <scratch>/14-decisions.txt` prints 0.]]></verify>
  <done>The blast radius was recorded, HIGH symbols were reported, and the ratified decisions, with the struck served half of SD3, were on disk before any code changed.</done>
</task>

<task type="auto" id="14-02">
  <name>Extract the embed-rows Stata fixture</name>
  <files>scripts/extract_embedded_rows_truth.do, test/fixtures/embedded_rows_truth.json</files>
  <action><![CDATA[
Create `scripts/extract_embedded_rows_truth.do` in the form of `scripts/extract_filter_truth.do` (header comment with the run line, `if "${ZA_REPO}" == "" global ZA_REPO "<repo>"`, `clear all`, the `_meta` locals and the sha read through a tempfile), computing probes p1-p6 of "Stata truth" with `serset`, `count`, `levelsof`, `summarize` and, for p3, `graph export … .svg` plus `cert_svg_texts` after `do "${ZA_REPO}/test/cert_svg.do"`; keep a subtitle only when it equals a value label of `foreign`. Each number goes through a local (`%21.17g` for means, `%9.0g` text beside it); the closing `python:` block reads every local with `sfi.Macro.getLocal`, builds `{"p1": …, …, "p6": …, "_meta": {stata_version, born_date, dash_commit, extracted, source}}` and writes `${ZA_REPO}/test/fixtures/embedded_rows_truth.json` with `json.dump(…, indent=1, sort_keys=True)`; no `shell=True`, no call back into Stata, temp SVGs erased. Run it with `global ZA_REPO "<W>"` in a two-line wrapper through `dash_nobrowser=1 scripts/stata_slot.sh <scratch>/s14 <scratch>/s14/run_extract.do`, read the log, and `git add -f test/fixtures/embedded_rows_truth.json`.
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' <scratch>/s14/run_extract.log` prints 0. `python3 -c "import json;d=json.load(open('<W>/test/fixtures/embedded_rows_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));print(d['p1']['serset_n'],d['p1']['union_n'],d['p2']['serset_n'],d['p3']['two']['subtitles'],d['p4']['price_if_foreign'],d['p4']['rep78_if_foreign'],d['p5']['mpg_foreign_in_3_8']['text'],d['p6']['mean_text'])"` prints `[22, 10] 30 52 ['Domestic', 'Foreign'] [3748.0, 12990.0] [3.0, 4.0, 5.0] 25.66667 21.2973` (the key names of "Stata truth"; the numbers are E-1's).]]></verify>
  <done>Stata's sersets, counts, levels, means and panel titles for every probe were committed as a stamped fixture.</done>
</task>

<task type="auto" id="14-03">
  <name>Write the failing plan unit tests</name>
  <files>test/test_embedded_rows.py</files>
  <action><![CDATA[
Create `test/test_embedded_rows.py` with the module docstring (P0.11, the rule of BR-14.1, the fixture), the imports used by the rest of the file (dash_render as dr, pandas, numpy, json, base64, re, warnings, `test_mode_parity as tp`, `test_server_layer_defects.plot_for`, `test_adversarial_matrix._load_app`, `js_runner`, `conftest.make_data_json`), the helpers of TR-14.12 (`_sentinel_frame`, `_write_inputs`, `_saved`, `_served`, `_page_values`, `_doc_values`, `_excluded_hits`) and the unit classes `TestEmbedRowsOf`, `TestThePlan`, `TestEmbedValues`, `TestEmbedFrame`, `TestThePageIndex`, `TestRelabel` with exactly the names in "TDD test stubs". Build each plan test on small hand-made frames and masks (`pd.Series(bool, index=frame.index)`) and assert whole Series with `.tolist()`; `test_the_filters_are_never_parsed` passes a spec whose build_options carries `filter: "price, type(bogus)"` and asserts no warning is recorded and `filter_rows == []` when *filters* is empty. Do not touch dash_render.py. Run against the batch-3 base.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "EmbedRowsOf or ThePlan or EmbedValues or EmbedFrame or ThePageIndex or TestRelabel" 2>&1 | tail -1` reports only failures (AttributeError: module 'dash_render' has no attribute '_dash_embed_plan', '_dash_embed_rows_of', '_dash_page_index', '_dash_relabel' …) and no collection error.]]></verify>
  <done>Every unit test of the plan helpers existed and failed for the missing functions, with nothing committed.</done>
</task>

<task type="auto" id="14-04">
  <name>Write the failing battery and behaviour tests</name>
  <files>test/test_embedded_rows.py</files>
  <action><![CDATA[
Add every remaining class of "TDD test stubs" to `test/test_embedded_rows.py`: the saved and served batteries (parametrised over the listed cases, ids exactly as written; the saved after-move variant runs the page's own filter callbacks through `js_runner.JsSession` as `test/filter_truth_check.py::saved` does and then scans `_doc_values` of every model reachable from `r._last_layout_root`; the served after-move variant fires each widget's `_callbacks` as `filter_truth_check.served` does), the union, widget, empty-reach, every-target-excluded, effective-type, csv, dense-id, brush (reusing `test_served_filter_move._served_selection`/`_saved_selection` and `_auto`), after-move parity, join-key, `TestTheServedIndexIsARank` (with `_index_values_doc`/`_index_values_page`; its brush guard takes the drawn positions from the scatter's view, never hard-coded; its csv guard reuses `test_export._export_spec`, `_saved`, `_served`, `_saved_file` and `_served_file`), colour-key guard, whole-data guard, csv contract and help classes. Do not write `TestTheServedIndexResidual` (struck 01oct2026). Read Stata's values from `test/fixtures/embedded_rows_truth.json` (fail, never skip, when it is absent) and from `test/fixtures/qualified_stat_truth.json`. The join-key test builds `__dashs1` and `build_options.sort_cols` in S02's form (section-02 TR-02.4) and maps saved ids through `r._page_labels` when the attribute exists, else positions. Assert the node cases ran with a module-level test that counts them. In every both-modes test assert the saved half first and give the served assertion a message beginning `served:`, so a partial tree fails on a line that names its mode. Do not touch dash_render.py.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider 2>&1 | tail -3` shows no collection error; the regression classes fail with the base values of "TDD test stubs" (e.g. `[plot-if scatter]` hits rows 1,3,5,7,9; `test_slider_and_range_bounds_both_modes` 3799.0; `test_a_layers_own_in_after_a_move_both_modes` '23.4'; `TestTheServedIndexIsARank::test_no_index_label_outside_the_pages_ranks[plot-if scatter]` with served labels {1, 3, 5, 7, 9} ≥ 5 among them; `::test_a_linked_selection_names_the_same_observations_both_modes` with a 10-row shared `index`). The guard classes and nodes pass: `TestColorvarReadsTheLayersRows`, `TestWholeDataRulesStillRead`, `TestTheCsvContract`, `TestTheJoinKeyFollowsThePagesRows`, `::test_the_brush_sentence_stays`, and `TestTheServedIndexIsARank`'s four guards (`test_a_brush_selection_names_its_observations_both_modes` '23.5' in both modes, `test_a_qualified_card_after_a_move_both_modes`, `test_csv_makes_the_relabel_the_identity`, `test_every_row_source_carries_an_index`). A guard that fails is reported before going on (a failing `TestColorvarReadsTheLayersRows` means S07 is missing from the base).]]></verify>
  <done>Every regression test of the section existed and failed for its measured reason at the batch-3 base, every guard passed, and nothing was committed.</done>
</task>

<task type="auto" id="14-05">
  <name>Write the failing ER truth block</name>
  <files>test/embed_truth_check.py, test/test_wp29_truth.cscript</files>
  <action><![CDATA[
Create `test/embed_truth_check.py` (docstring as `test/filter_truth_check.py`'s; nothing here calls Stata): `page_rows(path)` → `{"rows": distinct __dash_row__ count over every ColumnDataSource of the page, "cells": {column: number of distinct row ids carrying a non-null, non-empty value}, "view_counts": [booleans True per BooleanFilter of each scatter renderer, layout order], "panels": [figure titles]}` by decoding every application/json script (ndarrays included); `page_widgets(path)` → `[(type, start, end, option labels)]`; `served_state(app_path, moves)` → loads the app with `test_adversarial_matrix._load_app`, builds `make_document(Document())`, returns the shared source's row count, its `index` labels and the widgets' states, applies `moves` by firing callbacks and returns the same again; `page_curve(path)` → the lowess line's y values; `put(name, value)` → `sfi.Macro.setGlobal`. Append block `* ==== S14 P0.11: what a saved page holds ====` to `test/test_wp29_truth.cscript` above the marker and after any block numbered below 14 (R1), gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S14")`, with `S14 start/end` lines, cases ER-01..ER-08 of "Stata truth" through `_w29_expect`/`_w29_done`, files under `w29_work` erased at the end, and the header comment line. Run it through the driver against the base and save the log as `<scratch>/s14/run_base.log`.
  ]]></action>
  <verify><![CDATA[In `<scratch>/s14/run_base.log`: `ER-08 PASS` appears; ER-01, ER-03, ER-04, ER-05 and ER-07 print `FAIL` with the base values of "Stata truth" (74 rows; 3291/15906; 1-5); `grep -c '^r([0-9]*);'` reports 0 apart from the summary's `r(9);`; `cd <W> && python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The S14 truth block existed in the one WP-29 truth script and failed against the base for every leak it certifies, with its guard case passing.</done>
</task>

<task type="auto" id="14-06">
  <name>Record the red-first failure text</name>
  <files>none</files>
  <action><![CDATA[
Run `cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -rf 2>&1 | tail -80` and copy the summary (one `FAILED` line per regression node with its first assertion line) plus the failing ER lines of `<scratch>/s14/run_base.log` into `<scratch>/14-P0.11-failure.txt`, headed `S14 tests at <batch-3 base sha>:`. Also run the tests of E-7 items 1-8 and 10 and record that they PASS at the base (they pin today's behaviour; item 9 is a docstring). Nothing is committed.
  ]]></action>
  <verify><![CDATA[`<scratch>/14-P0.11-failure.txt` exists, starts with `S14 tests at `, and holds at least the lines for `test_no_excluded_value_is_embedded[plot-if scatter]`, `test_no_excluded_value_is_sent[link q1 q2]`, `test_slider_and_range_bounds_both_modes`, `test_a_layers_own_in_after_a_move_both_modes`, `test_no_index_label_outside_the_pages_ranks[plot-if scatter]`, `ER-01 FAIL`; `git -C <W> status --porcelain` lists no staged file.]]></verify>
  <done>The saved failure text of every regression test and truth case was on disk for the commit body, with nothing committed.</done>
</task>

<task type="auto" id="14-07">
  <name>Add the plan helpers and copy lists</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Add `_DASH_PLOT_VAR_KEYS` after `_DASH_OPT_VAR_KEYS` and alias `DashRenderer._VAR_KEYS` to it (TR-14.1). Add `_dash_embed_rows_of`, `_dash_embed_plan`, `_dash_embed_values` and `_dash_embed_frame` after `_dash_layer_frame` exactly as TR-14.2/TR-14.3 specify, and `_dash_page_index` and `_dash_relabel` after them exactly as TR-14.18 specifies, each with a docstring naming WP-29 P0.11 and its rule. Add `"_DASH_PLOT_VAR_KEYS"` to the served constants tuple after `"_DASH_OPT_VAR_KEYS"` and the six function names on one line after `"_dash_layer_frame",` in the functions tuple (R2, as amended 01oct2026). Add the nine new TR-14.11 entries to `test/function_test_map.py` in alphabetical place, the three DashRenderer ones pointing at tests that turn green in 14-08/14-09 (the map test is run in 14-13).
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "(EmbedRowsOf or ThePlan or EmbedValues or EmbedFrame or ThePageIndex or TestRelabel) and not renderer_computes" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k CarriesEveryName` and `python3 -m pytest test/test_resource_limits.py -q -n0 -p no:cacheprovider -k DefinesEveryName` pass.]]></verify>
  <done>The one plan function both modes run, with its three helpers, the two relabel helpers and the shared key tuple, existed, was unit-tested and was copied into the served app.</done>
</task>

<task type="auto" id="14-08">
  <name>Rank the saved page's row identities</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Add `DashRenderer._set_embed` (with `_page_labels`, `_row_pos` and `_page_sort_keys`), `_ensure_embed` and `_row_ids_kept`, and rewrite `_row_ids_for` as the aligned function with both fallbacks deleted (TR-14.4). `_kpi_qualifier_row_ids` calls `_row_ids_kept`; in `_make_figure_body`'s per-plot block replace the `_pos`/`_wanted` pair with `_wanted = set(self._row_ids_kept(_pdf))`. Leave S02's `_jo` line as it is (14-09 changes it after its red run). Run the TR-14.4 audit grep on the base text first and route every other positional row numbering it finds through `_row_ids_for`/`_row_ids_kept`, recording the hits and what was done with each in `<scratch>/14-audit.txt`.
  ]]></action>
  <verify><![CDATA[`cd <W> && grep -n "pos.get(idx, i)\|_pos = {idx: i for i, idx in enumerate(self.df.index)}" dash_render.py` prints nothing; `grep -n "enumerate(self.df.index)" dash_render.py` prints only the no-plan fallbacks of `_row_ids_for` and `_row_ids_kept`; `<scratch>/14-audit.txt` exists; `python3 -c "import sys;sys.path.insert(0,'<W>');import dash_render as d;assert hasattr(d.DashRenderer,'_row_ids_kept') and hasattr(d.DashRenderer,'_set_embed')"` prints nothing.]]></verify>
  <done>The saved renderer could number the page's rows densely, one function aligned ids and refused an unranked row while another dropped them, and no other code numbered rows by position.</done>
</task>

<task type="auto" id="14-09">
  <name>Restrict every saved source to its rows</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Give `_make_source` the `rows=` argument and the plan restriction and blanking of TR-14.5. In `_build_sources_and_figures` make every change of TR-14.6: `_ensure_embed` after the link expansion, the linked source over `link_rows` with `self._link_index`, the linked graph views over the link frame built `if not all(mask)` with member ids from the source (A5, replacing the `len(_g_fdf) < len(self.df)` guard), the facet masks over `self._link_index`, the unlinked and by() panel sources with `rows=_plan["graph_rows"].get(name)`, and the linked panel member ids through the source's ids. In `render()` apply TR-14.8 (parse first, `self._embed = None`, `_ensure_embed` with the raw link names, the report with the page's rows, the agg threshold) and rewrite `_report_dataset_shape`'s comment. Then make the join-key red run: run `TestTheJoinKeyFollowsThePagesRows` with S02's `_jo` line still reading `self.sort_keys`, append its failure (`[3, 4, 5]` where `[5, 4, 3]` is wanted, or the equivalent order the test prints) to `<scratch>/14-P0.11-failure.txt` under the heading `join key without page ranks:`, and only then change the `_jo` line to `getattr(self, "_page_sort_keys", None) or {}` (TR-14.4).
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest "test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[plot-if scatter]" "test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[two plots q1 q2]" "test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[link q1 q2]" "test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[by(foreign) + plot q2]" "test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[by(foreign, total) + plot q2]" -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 5 passed (the filter cases need 14-10's snapshot); `python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "RowIdentitiesAreDense or JoinKey or WholeDataRules" 2>&1 | tail -1` reports 0 failed; `grep -c 'join key without page ranks:' <scratch>/14-P0.11-failure.txt` prints 1; `python3 -m pytest test/test_per_plot_qualifier_linking.py test/test_view_alignment.py test/test_saved_filter_layers.py test/test_kpi_brush.py -q -n0 -p no:cacheprovider` shows only the E-7 item-6 jitter pin failing.]]></verify>
  <done>Every saved source, linked view, facet mask and panel id was built over the rows its graph or link group reads, the report counted the page's rows, S02's join key read page-aligned ranks after a recorded red run, and the whole-data rules still read every row.</done>
</task>

<task type="auto" id="14-10">
  <name>Restrict the saved filters and snapshot</name>
  <files>dash_render.py</files>
  <action><![CDATA[
In `_build_filter_widgets` iterate with `enumerate`, read each widget's column from its reach and feed it to `_dash_filter_effective_type` and the builders, build both snapshot sites from `_dash_embed_frame(self.df, self._embed, list(self.df.columns))` with aligned ids, and rewrite the docstring and the three comment blocks (TR-14.7). In `_csv_button` build the text source through `_dash_embed_frame`. Leave `fsource`, `_snapshot_of`, the derived snapshots, `_use_for` and every callback argument as they are: they follow the restricted sources.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "TestTheSavedPageHoldsOnlySelectedRows" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k "FilterWidgetSpansItsReach or AnEmptyReach or EveryTargetExcludes or FilterTypeFollows or CsvDoesNotMove or TheCsvContract" -rf 2>&1 | grep '^FAILED'` lists only failures whose message names the served document (each both-modes test asserts its saved half first); `python3 -m pytest test/test_filter_exclude.py test/test_filter_exclusion_sets.py test/test_export.py test/test_kpi_values.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Each saved widget spanned the rows its targets select, and the snapshot and CSV text held only the page's planned cells.</done>
</task>

<task type="auto" id="14-11">
  <name>Restrict the served document to its rows</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Apply TR-14.9 (`_dash_refresh_linked`'s `need`) and every item of TR-14.10 in `ServerAppBuilder._generate_app_source`: the build-time plan for the dropdown type, the moved `_filter_specs` emission and the three `_EMBED` lines after `linked_names`, `_DASH_PLOT_VAR_KEYS` in the three loops, the shared source and `_shared_pos` over `_ldf`, both placeholders restricted, blanked and given an `index` column, the enumerated widget loop with the reach column, `_brush_rows` and the after-move `_kept_rows` intersected with `_EMBED_GROWS`, and the linked move over `_EMBED_LINK` with `need=`. Then apply TR-14.18: emit the relabel block between the `_EMBED = …` line and `_EMBED_GROWS`, with the `_sort_keys` line only if `grep -c "    _sort_keys = meta\['sort_keys'\]" dash_render.py` prints 1 at the base. Every emitted line is a fixed string. Build one app from a spec with a layer qualifier and a linked pair (`test_mode_parity._spec([plot_for("scatter", if_expr="price > 4500")], {"filter": "price, type(range)", "link": "g1"})`) and `py_compile` it before running tests. Then write the relabel audit: in that app's text, list every line between `spec, df, meta = _load_spec_and_data()` and `_dash_old_index = df.index` that contains `.index` or `pd.Series(` or builds a row-keyed dict, with what the relabel block does with it, in `<scratch>/14-relabel-audit.txt`. Every row-keyed object bound there must be passed through `_dash_relabel`. The expected list at `7421d3d` plus this section is `_qual_masks` (and S02's `_sort_keys` at the base).
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_served_linked_views.py test/test_server_link.py test/test_server_brush.py test/test_server_facets.py test/test_served_dates.py test/test_served_throttle.py test/test_adversarial_matrix.py test/test_help_claims_4.py test/test_served_bs_layout.py test/test_saved_filter_layers.py test/test_export.py -q -n0 -p no:cacheprovider` passes, apart from E-7 item 6's jitter pin (flipped in 14-13). These are the files of E-8 probe 3 whose oracles read served labels; probe 4 measured them green under the rank relabel. Both served-name guards (14-07's commands) pass. `<scratch>/14-relabel-audit.txt` exists. `grep -c "_dash_old_index = df.index" <the built app>` prints 1, and that line comes after the `_EMBED = _dash_embed_plan(` line and before `shared_source = ColumnDataSource(` (check with `grep -n`).]]></verify>
  <done>The served document held only planned rows and cells before and after every move. Its widgets spanned their reach, its brush counts matched the saved page's, and every `index` it sent was a page rank equal to the saved page's number for the same observation.</done>
</task>

<task type="auto" id="14-12">
  <name>Flip the tests that pin the leak</name>
  <files>test/test_filters.py, test/test_served_filter_move.py, test/test_help_claims_2.py</files>
  <action><![CDATA[
Apply E-7 items 1-4, 8 and 10 exactly as written there: the renamed range test and its class docstring in `test/test_filters.py`; in `test/test_served_filter_move.py` the reported case's `rows` 22 → 8 and `drawn` through `r._page_labels`, `_SELECTIONS[4]`'s `"23.4"` → `"25.66667"` with its comment, `TestAdversarialFilterMoves::test_a_selection_cannot_outlive_the_rows_it_named`'s card and comment, `TestAdversarialFilterMoves::test_no_widget_value_widens_a_layers_own_rows`'s `_rows` mapped through `_page_labels` (item 10), and one added docstring sentence; in `test/test_help_claims_2.py` the docstring, the rename and the added qualified variant. Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per changed assertion in `<scratch>/14-flips.txt` (old value, new value, the Stata command that gives the new one).
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_filters.py test/test_served_filter_move.py test/test_help_claims_2.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `grep -c '^Flipped:' <scratch>/14-flips.txt` prints at least 7; `python3 -m pytest --collect-only -q -n0 -p no:cacheprovider test/test_filters.py test/test_served_filter_move.py test/test_help_claims_2.py | tail -1` reports one more node than at the base (the added variant) and none fewer.]]></verify>
  <done>Every test that pinned the leak pinned Stata's answer, none was deleted, and each flip was recorded with its reason.</done>
</task>

<task type="auto" id="14-13">
  <name>Flip the rest and extend parity</name>
  <files>test/test_saved_filter_layers.py, test/test_linking_filters.py, test/test_mode_parity.py</files>
  <action><![CDATA[
Apply E-7 items 5, 6 and 7, and append TR-14.14's CORPUS and MOVE_CORPUS cases; add the `Flipped:` lines (item 9, a docstring, is 14-14's). Then run, one command each, the files the prototype ran in its runs A and B (Evidence E-6) plus `test/test_function_test_map.py`, `test/test_cscript_hygiene.py` and `test/test_program_coverage_map.py`. Any failure outside E-7 is a regression of this section: fix the code, not the test (R7); a further pin found here is flipped with its `Flipped:` line only if the new value is Stata's or the parity oracle's.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_saved_filter_layers.py test/test_linking_filters.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `git -C <W> diff -U0 test/test_mode_parity.py | grep -c '^-ALLOWED\|^-_MUST_WARN'` prints 0.]]></verify>
  <done>The remaining pins were flipped with reasons, three parity cases and two move cases covered the restricted pages, and the related suites were green.</done>
</task>

<task type="auto" id="14-14">
  <name>Say what a saved page holds</name>
  <files>dash.sthlp, test/test_filter_widget_data.py</files>
  <action><![CDATA[
Rewrite the module docstring of `test/test_filter_widget_data.py` (E-7 item 9: a widget now describes the rows its targets select; every shape in the file carries the unqualified filter-mode card `k1`, so its reach is every row and its expectations are unchanged) and add its `Flipped:` line. Make the six help edits of TR-14.15 exactly, in SMCL, locating each by its quoted text (other sections' edits in batches 1-2 moved the lines): the new Description paragraph after "…is read as your data.", the Exporting sentence replaced, the new Filters `{pmore2}` after the paragraph ending "(see {help dash##export:Exporting}).", the Linking sentence, the Server Mode sentence appended to the paragraph that begins "The generated app embeds every observation", the Resource-limits sentence appended to the `{ul:What the data limit counts.}` paragraph. Keep lines under 80 characters as the file does. Then grep `test/test_help_claims_*.py` and `test/test_help_claims_*.cscript` for any sentence you changed and update a pin only if it quoted the replaced text.
  ]]></action>
  <verify><![CDATA[`cd <W> && python3 -m pytest test/test_embedded_rows.py -q -n0 -p no:cacheprovider -k TheHelpSaysSo` passes; `grep -c "already contains" dash.sthlp` prints 0; `python3 -m pytest test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_5.py test/test_filter_widget_data.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The help said what a saved page holds, what a served one sends, what a widget spans including each empty widget, and that the data limit may count more than the page holds.</done>
</task>

<task type="auto" id="14-15">
  <name>Certify against twoway in Stata</name>
  <files>none</files>
  <action><![CDATA[
Run the S14 block through the driver of "Stata truth" with `WP29_ONLY=S14` and read `<scratch>/s14/run_test_wp29_truth.log`; then run the whole truth script once with `WP29_ONLY` unset (every earlier section's block must still pass on this tree), and `test_e2e_filters.cscript` and `test_export.cscript` through the same driver (they build filter and csv pages). A failing ER case is fixed in the code of 14-07..14-11, never in the expected value, unless the case itself misreads Stata (then fix the case and say so in the commit body).
  ]]></action>
  <verify><![CDATA[`grep -c '^ER-0[1-8] PASS' <scratch>/s14/run_test_wp29_truth.log` prints 8; `grep -c 'FAIL' <scratch>/s14/run_test_wp29_truth.log` prints 0; the all-blocks log ends `test_wp29_truth: ALL CHECKS PASSED`; the two area logs show no `FAIL` and no `r(` error.]]></verify>
  <done>Stata certified that dash's saved pages and served app hold twoway's rows and Stata's widget values and counts, and every earlier truth block still passed.</done>
</task>

<task type="auto" id="14-16">
  <name>Close P0.11 and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
In BUGS.md close S01's entry "The saved page embeds every row of each drawn variable, including rows that if and in exclude" in place (`- [ ]` → `- [x]`) with `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.11). <the rule of BR-14.1; _dash_embed_plan computed once per render and per served document; every saved source, the linked source and its views, the snapshot and the CSV text through _make_source/_dash_embed_frame; the served shared source, placeholders, widgets, brush rows and linked refresh; dense row identities in both modes (saved __dash_row__ ranks; the served frame relabelled to the same ranks by _dash_page_index/_dash_relabel, so no index column carries an observation number); the help>. Pinned by test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded, test/test_embedded_rows.py::TestTheServedDocumentHoldsOnlySelectedRows::test_none_after_a_filter_move, test/test_embedded_rows.py::TestTheFilterWidgetSpansItsReach::test_slider_and_range_bounds_both_modes, test/test_embedded_rows.py::TestTheServedIndexIsARank::test_no_index_label_outside_the_pages_ranks, test/test_wp29_truth.cscript ER-01; fixture test/fixtures/embedded_rows_truth.json. Residual, deferred (WP-29): csv embeds every row (documented); rows selected only for computed layers are embedded; the served .py and its data hold every row on disk (written privately where the system allows, S08).` Open no new entry (the served index residual was struck on 01oct2026; TR-14.16). Delete the `"P0.11"` line of `WP29_OPEN`. Replace `<!-- WP-29 P0.11 -->` under `### Security` with ONE item ending `(WP-29, P0.11)` that names: the saved page holds only selected observations and ranks its own rows; a served link() group sends only its rows; `filter(price, type(range))` under a graph `if price > 4500` spanned 3799–11385 and now 4749–11385, in both modes; a dropdown within its limit on its reach stays a dropdown; a filter that reaches no observation is greyed out (range, slider) or lists only All; a card following the brush counts the rows its graph shows (`update(brush)` on a layer with `in 3/8`, after a move to Foreign, 23.4 → 25.66667); the served app numbers its rows as the saved page does, so no row number a browser receives shows where an excluded observation was (a layer `if price > 4500` sent `index` 1, 3, 4, 6, 7, 9 and now sends 0-5); with csv the page still holds every row. Then run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, the full suite once (`python3 -m pytest test/ -q`, read its log), `gitnexus_detect_changes()` and `git diff --cached --name-only`; grep the message for `claude|anthropic`; commit on `wp29-s14` with the subject of the commit boundary, the body opening with `<scratch>/14-P0.11-failure.txt`, then the measured defect, what changed and where, the `Regression:` lines (one per regression class and ER case, `-- failed at <batch-3 base sha> with <text>`), the `Flipped:` lines from `<scratch>/14-flips.txt`, `Fixture: test/fixtures/embedded_rows_truth.json (scripts/extract_embedded_rows_truth.do)` and `BUGS.md: "The saved page embeds every row of each drawn variable, including rows that if and in exclude" (closed)`. No `(opened, S3)` line (struck 01oct2026).
  ]]></action>
  <verify><![CDATA[`tail -1` of the full-suite log reports 0 failed and 0 errors; `cd <W> && python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c '<!-- WP-29 P0.11 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.11)' CHANGELOG.md BUGS.md` prints 1 for each file; `git log -1 --format=%s` ends `(WP-29 P0.11)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git show --name-only --format= HEAD` lists no CLAUDE.md, AGENTS.md, .gitignore, .gitnexus or *.html; `grep -c '^- \[ \] Title:' BUGS.md` prints the batch-3 base's count (AC-14.4).]]></verify>
  <done>P0.11 was closed in BUGS.md naming existing tests, the served index among its fixes and no new entry opened, the marker was replaced by one Security line with the old and new values, the WP29_OPEN key was gone, and one green commit on wp29-s14 carried the section.</done>
</task>

## Section completion criteria

- A saved page holds no value of an observation outside BR-14.1's rows, and a served document none, before and after every filter move, in every battery case (strings and dates included); with csv the page holds every row (contract).
- Widgets span their reach in both modes; empty reaches draw the documented widgets; the effective type follows the reach; csv moves no row set but the snapshot's.
- Brush cards count the graph's or link group's rows in both modes (25.66667, 22.83333, 22.13333), Stata's numbers from the fixture.
- Saved ids are dense; `_row_ids_for` refuses an unranked row; S02's join key reads page-aligned ranks. Every served `index` is a page rank equal to the saved page's number for the same observation, before and after moves; brush, linked selection, qualified cards and csv are unchanged by the relabel.
- lowess adjust, lpoly's grid, by() panels, card first values and text `in` qualifiers read the whole data, unchanged.
- ER-01..ER-08 pass in StataNow; the whole truth script passes.
- Ten pins flipped with `Flipped:` lines, none deleted; three CORPUS and two MOVE_CORPUS cases added; `ALLOWED`/`_MUST_WARN` unchanged.
- One commit on `wp29-s14` ending `(WP-29 P0.11)`; P0.11 closed in place; no BUGS.md entry opened; marker replaced; `WP29_OPEN` key gone; the full suite green once.

## Notes

- **Merge rules.**
  - R1: one block `S14` in `test_wp29_truth.cscript`; no runner or hygiene edit; batch 3 has no other section, so no ordering conflict.
  - R2: `_DASH_PLOT_VAR_KEYS` after `"_DASH_OPT_VAR_KEYS"`; the six functions (`_dash_embed_rows_of`, `_dash_embed_plan`, `_dash_embed_values`, `_dash_embed_frame`, `_dash_page_index`, `_dash_relabel`) on one line after `"_dash_layer_frame",` (index R2 S14 row, which must name the six: see the ratification line at the top); nine new `function_test_map.py` entries in alphabetical place.
  - R3: dash.sthlp only the six TR-14.15 places (appending to S06's limits paragraph and S08's server paragraph, never rewriting their text); CHANGELOG only the P0.11 marker; BUGS.md only the P0.11 entry (no new entry, 01oct2026); `test_tracking_documents.py` only the `"P0.11"` line.
  - R5: a new fixture, `git add -f`, never hand-patched.
  - R6: CORPUS/MOVE_CORPUS appends and the E-7 item-7 flip; `ALLOWED`, `_MUST_WARN` untouched.
  - R7: ten flips, each with `Flipped:`; the node count never falls.
  - R8: 14-01 and 14-16.
- **Files outside the manifest list:** `test/test_saved_filter_layers.py`, `test/test_linking_filters.py`, `test/test_mode_parity.py` (flips found by the prototype, E-6/E-7). `test/test_fixtures_are_committed.py` needs no edit unless its run says so (it finds a fixture by the name a test reads).
- **Traps.**
  - Never restrict `self.df`/`df` themselves: a prototype that swapped a restricted frame into `_build_filter_widgets` broke three `test_kpi_values.py::TestQualifiedKpiUnderFiltering` tests, because text-qualifier card ids were evaluated on the blanked frame. Restrict at the embed points only.
  - Never re-parse filters for the plan (duplicate `type(bogus)` warning, `test_same_warnings`).
  - The plan's `filter_rows` is aligned with the PARSED filter list; the saved loop must `enumerate` that same list, and the served loop the emitted `_filter_specs`.
  - `_dash_link_names(` is counted by `test_linking_filters.py` (5 → 6): the plan calls it; `render()` must not add a seventh call (pass the raw names).
  - Ids are ranks in BOTH modes: any test or code that turns `__dash_row__` or a served `index` label into an observation number goes through `r._page_labels`. The served app keeps no `_page_labels` of its own (nothing there needs one); a test takes it from the saved renderer of the same spec, which runs the same plan.
  - The served relabel goes after the plan and before anything reads `df.index` (TR-14.18). Pass every row-keyed map through `_dash_relabel`, and never rebuild one from `meta` after the relabel. Never sort the frame or reset its index: row order is what `in` and the csv read.
  - Dates in the served frame are datetime64; blank with `pd.NaT`, never `np.nan` on a datetime column.
  - The emitted app is text: `py_compile` one after 14-11 before running tests.
  - `test_responsive_layout.py`'s Chrome cases time out under heavy `-n` parallelism (E-6 run C); rerun a failing one alone before treating it as a regression.
  - python_exec hazard: many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the truth script then exits 222, and a SKIP is not a pass.
- **Commit-body line forms.** `Regression: test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded[plot-if scatter] -- failed at <sha> with hits [(1, 'mpg'), …]`; `Regression: test/test_wp29_truth.cscript ER-01 -- failed at <sha> with ER-01 FAIL: page rows 74, count 30`; `Flipped: …`; `Fixture: …`; `BUGS.md: "…" (closed)`.
- **Case prefix.** `grep -n "ER-[0-9]" test/*.cscript test/*.py` printed nothing at `7421d3d`; re-run it at the batch-3 base before first use (index "Section numbers in case ids").
- **Line numbers** are `7421d3d`'s; batches 1-2 moved them. Symbols and quoted text are authoritative.

### Notes for the closeout (A5; S15 writes these, S14 does not)

- **GAPS2.md I2** Tracked line: `Closed in WP-29, BUGS.md "The saved page embeds every row of each drawn variable, including rows that if and in exclude", commit <sha>` if S15 judges I2-a (embedding) and I2-b (the help) both closed; the csv contract is recorded beside it, not as an open I2 sub-item, unless S15 decides it is. The served `index` is fixed in the same commit (ratified 01oct2026) and is not a residual.
- **DROPIN-REMAINING.md P0.11** (GAPS2-I2-a, GAPS2-I2-b): annotate with the commit.
- **ROADMAP.md WP-29:** record the measured results of E-6 (widget 3799 → 4749; brush 23.4 → 25.66667), the served row numbers (a layer `if price > 4500` sent `index` 1, 3, 4, 6, 7, 9 and now sends 0-5, E-8) and the residuals.
- **AGENTS.md invariant (S15.4):** "a page holds a cell only if a consumer reads it (`_dash_embed_plan`, one function both modes run); whole-data rules read `self.df`/`df`, never a source; row ids are ranks of the page's rows in both modes (the served frame is relabelled by `_dash_page_index` right after the plan; every served row-keyed map goes through `_dash_relabel`)" — tests `test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded` and `test/test_embedded_rows.py::TestTheServedIndexIsARank::test_no_index_label_outside_the_pages_ranks`.
- **Residuals for S15.7:** csv embeds every row (contract); observations selected only for computed layers are embedded (no JS refit, M3); the served `.py` and data JSON hold every row on disk (written privately where the system allows; S08 as ratified 01oct2026 notes a root that is not private instead of refusing it); a served mapper copy's `index` is a position in its layer's source while the served brush reads it as a row label (E-8 probe 5: a line's first point read observation 1's price, 4749, for observation 3's 4816; BokehJS's Line takes no box or lasso hit, so it was not reached from a browser; no leak); the served `index` is NOT a residual (fixed, ratified 01oct2026); `$dash_max_cells` counts every exported row, not the planned ones; the saved and served dataset-size notes may differ on qualified data.
