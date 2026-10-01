# Section 07: Saved filter rows and colorvar domain

> Part of: WP-29 · P0: P0.15, P0.16 · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 12, 14 · Tasks: 16, 2 commits (P0.15, then P0.16) · Case prefixes: QF, CQV

## Review amendments (design review of u13, "sound with amendments") — binding; they override any conflicting text below

Every amendment from the u13 review is applied in this file. Each one is listed here with where it lands.

1. **Date colorvar, served.** `_dash_colorvar_domain` never calls `list()` on a column. Numeric and date columns go through `_dash_float_values(col)` and come back as a float ndarray in epoch ms, so a served datetime64 `g_df` column converts. Only a column that `_dash_float_values` refuses (a string column) comes back as a list. A `%td` colorvar with a layer `if`, continuous and `colorlevels(3)`, is tested in BOTH modes (TR-07.6, `test_date_range.py::TestADateColorvarUnderALayersIf`). Re-measured: `_dash_float_values(list(series))` raises `TypeError: float() argument must be a string or a real number, not 'Timestamp'`. `_dash_float_values(series)` and `_dash_float_values(series.to_numpy())` give `[9.783936e+11 9.786528e+11 nan]`.
2. **Derived field names use the reserved prefix.** Each name is unique per layer: `f"{_DASH_CVAR_PREFIX}{k}_{varname}"` with `_DASH_CVAR_PREFIX = "__dash_cvar"`, where `k` is the first integer from 1 whose name is absent from the source (TR-07.4). The `_cvar_<var>_bin` name and the equality-checked suffix are dropped. The loader refuses user data holding a `__dash` column (`_dash_take_qual_columns`, dash_render.py:24302), so a user variable can never collide. The r2 collision has a regression test that fails first, in two forms:
   - on the saved page;
   - in the served app after a move. This form is newly measured; see Evidence E-16.6.
3. **The collision is not limited to linked sources.** The first-absent rule applies on every source. The r3 regression test (two colorvar layers on one unlinked graph) fails first. **Decision on open question 3:** dash keeps accepting two colorvar layers in one graph in this section, and twoway's refusal is routed to S15 as a new residual item (Notes for the closeout). The reasons:
   - The refusal would be a `dash.ado` change outside this section's files, in a batch where S02, S04, S06 and S08 all edit `dash.ado`.
   - It is a Changed-behaviour item, not part of P0.16.
   - Unique names fix the correctness defect on their own.
4. **No missing sentinel.** `"__missing__"` is replaced by `None` in `_dash_colorvar_bins` and in every `_apply_colorvar` path. The mapper is `CategoricalColorMapper(factors=<levels only>, palette=<one colour per level>, nan_color=missing_color)`, and the "(missing)" key entry comes from the domain's `has_missing`. The r4 regression test (a value label `"__missing__"`) fails first. A `None` value is drawn in `nan_color` by BokehJS whether the row is missing or outside the domain, so the separate Chrome check for null is no longer needed.
5. **P0.15 expected ids, dispute resolved by re-measurement.** The two `test_per_plot_qualifier_linking.py` tests use THAT file's own `_DF` (8 rows, its own module constant), not `test_mode_parity._DF`. On that frame the design's numbers are correct. Re-measured at `7421d3d` (probe `p_ids.py`):
   - `link(_all)` + graph `if foreign == 1` + layer `if weight < 3000` registers `[0, 2, 3, 6]`, where the view's true rows are `[3, 6]`.
   - `by(foreign)` linked: panel 0 registers `[0, 2, 3, 6]`, true `[0, 2]`; panel 1 registers `[0, 2, 3, 6]`, true `[3, 6]`.

   The reviewer's `{3, 7, 9}` is `test_mode_parity._DF`'s intersection, also re-measured, and is not the frame these tests use. Either way the tests DERIVE their expected ids from the frame in the test, never from literals (TDD stubs).
6. **Served redraw keeps the build-time domain.** `_dash_redraw_for(g, plot, pi, gname, cv_domain=None)` captures the build's domain, and `_redraw` passes it to `_dash_draw_layer(..., cv_domain=...)`. Re-measured (r1) at HEAD: after a served move to 4500-11385, rconnected `colorlevels(3)`'s redrawn Line copy held `'4749–6961'` and `'9173–11385'`, neither of them in the build's factors `['3799–6327.67', '6327.67–8856.33', '8856.33–11385']`. Pinned by `TestTheServedRedrawKeepsTheBuildDomain` (fails first).
7. **rconnected draws one key.** This answers open question 5 and is fixed here. `map_scatter(..., colorvar_key=True)` passes `add_key` to `_apply_colorvar`, and `map_rconnected` passes `colorvar_key=False` on its second end. Twoway truth: `twoway rconnected lo mpg weight, colorvar(price)` has one "Price" title. dash at HEAD has 2 ColorBars saved and 2 served (re-measured).
8. **The missing-row rule covers x and connected too.** Open question 1 is answered yes, re-measured. Each of `scatter y2 weight`, `scatter mpg x2` and `connected y2 weight` with `colorlevels(2)` gives key `9,598.5`. Probes `missing_x_lv2` and `missing_y_connected` are added to the fixture and to `TestTheKeyIsDrawnFromTheLayersRows` (CQV-07, CQV-08).
9. **Mask mismatch warns.** On a mask whose length differs from the column's, `_dash_colorvar_domain` warns `dash: <where>: its colour key could not be restricted to its observations (<m> flags for <n> rows); the key is drawn from every row.` and returns None. A unit test pins the warning.
10. **`_dash_colorvar_bins(bin_values=)` gets its own unit tests** (`TestTheBinHelperOverADomain`):
    - labels and closed-end bounds come from the domain;
    - there is one bin per bin value;
    - `has_missing` comes from the domain only;
    - a bin value outside the domain's range gets `None` and is never clamped into an end bin;
    - with `bin_values=None` the domain itself is binned, with HEAD's labels and assignment except that missing is `None`.
11. **String colorvar is a dash extension.** twoway refuses it: `'orig' found where numeric variable expected`, r(7) (rv2.log). The help keeps the existing sentence saying so and does not claim twoway takes strings. BUGS.md lists the string path as a drop-in deviation.
12. **P0.15 repeated moves.** `TestALinkedLayersOwnIfAcrossMoves` moves, moves again, then resets through `_FILTER_JS`. Re-measured on `test_mode_parity._DF` (`p_rep.py`):
    - At HEAD all three steps differ from the oracle, and the reset too, because the booleans are rebuilt from the wrong `member_ids` on every move.
    - With the fixed registration all three agree, and the reset equals the first paint.
13. **The flip list is complete.** Every `_cvar_` and `"__missing__"` reader is listed in Evidence E-16.9 and routed through one helper module, `test/colour_bins.py`, which reads the field from `renderer.glyph.fill_color`. No test hard-codes a derived name. **This forces edits outside the manifest's file list.** They are flips under R7, not new behaviour:
    - `test/test_function_audit.py`, `test/test_glyphs.py`, `test/test_dropdown_values.py`, `test/test_help_claims_7.py`, `test/test_server.py`, `test/test_internal_column_names.py`;
    - and `test/test_gaps2_truth.cscript` CV-01 (four lines, an **R1 exception**: R1 gives that script to S06 only. S06's AL-19 hunk and this CV-01 hunk are disjoint, and S06 merges first. Notes, "Merge rules".)

Open questions, decided:
- **1** (missing x/y rows count): yes, in this section (amendment 8).
- **2** (by() key presence): routed to P1.15 with the measured truth; documented here.
- **3** (two colorvar layers): unique names now; the refusal goes to S15 as a residual (amendment 3).
- **4** (`"__missing__"` collision): fixed here (amendment 4).
- **5** (rconnected): fixed here (amendment 7).
- **6** (all-missing key shows "(missing)" where twoway shows the title alone): kept, as a documented deviation.

## Overview

**P0.15.** On the saved page, a linked `by()` panel or a linked graph that has its own `if`, holding a layer with its own `if`, draws the wrong rows after any filter move. `_make_figure_body` builds the layer's view mask correctly: the layer qualifier AND the panel's or graph's view. It then registers, for the filter callback to rebuild that view, the ids of every row the layer's qualifier selects in the WHOLE dataset (`self._row_ids_for(_pdf)`, dash_render.py:26212-26213). `_FILTER_JS` rebuilds `vf.filter.booleans` from those ids (:15961-15967), so after the first move each panel's layer draws the other panel's rows as well.
- Measured on `test_mode_parity._DF` with the price range moved to 4500-11385, layer 2 `if price > 4500`: both panels of a linked `by(foreign)` drew observations `[1, 3, 4, 6, 7, 9]`, where the oracle draws `[4, 6]` and `[1, 3, 7, 9]`.
- On Stata's auto, after a move to 5,000-15,906, the saved page draws 23 rows in each panel's second layer, where Stata's `count` gives 14 and 9 and the served app draws 14 and 9.
- `test_per_plot_qualifier_linking.py` passes 7/7 because it checks only the first paint.

After this section the registered ids are exactly the source's row ids the view keeps. The page then equals the served app and the oracle after every move, including a second move and a reset.

**P0.16.** `GlyphMapper._apply_colorvar` computes the colour bar range, the `colorcuts()`/`colorlevels()` cuts, the `colordiscrete` levels and the string categories from every row of the source it is handed (`raw_col = source.data[varname]`, :6952). It never reads the layer's view.
- On the saved page a layer's own `if`, a linked graph's qualifier and a linked `by()` panel all live in the view, so the key spans the whole dataset. `dash (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)` draws its bar over 3,291-15,906 where twoway draws 3,748-12,990.
- The served app is right for an unlinked layer `if` but spans the whole dataset for linked layers.
- Both modes drop rows with a missing x or y from the key, because `map_scatter`'s `clean_source` and the served `_dash_layer_source` run `dropna` first, while twoway counts those rows.

After this section the key in both modes is computed from the layer's **colour rows**: the rows its graph `if`/`in`, its own `if`/`in` and its `by()` panel select, including rows whose x or y is missing. The key is fixed at build time and a filter move never re-ranges it, as today. The rewrite also does three more things:
- removes the `"__missing__"` sentinel;
- moves derived colour columns under the reserved `__dash` prefix with a name unique per layer;
- draws one key for `rconnected`.

**Why one section.** Both gaps are the saved page's linked-view rows. P0.15 is which rows a view is rebuilt from; P0.16 is which rows the colour key is drawn from. Both read the same `_plot_view` in `_make_figure_body`'s per-plot block, and S12 (stale cue) and S14 (embed rows) consume both results.

**Test order and commit rule.** Two P0 entries, two commits, never red (D1, rule 4, rule 7).
- **P0.15 cycle:** 07-01 and 07-02 write every P0.15 regression test and run it against the batch-1 base (`<scratch>/batch-1-base.txt`), saving the failure text to `<scratch>/07-P0.15-failure.txt`. 07-03 fixes, and 07-04 closes the entry and makes commit 1 with the subject ending `(WP-29 P0.15)`.
- **P0.16 cycle:** 07-05 extracts the Stata fixture. 07-06 to 07-08 write every P0.16 regression test and run it against the tree commit 1 leaves, saving to `<scratch>/07-P0.16-failure.txt`. 07-09 to 07-11 fix. 07-12 to 07-14 flip the pins. 07-15 documents, and 07-16 closes the entry and makes commit 2 with the subject ending `(WP-29 P0.16)`.

No test-only commit exists.

## Risk: [yellow] — `_apply_colorvar` and the per-plot view block are shared by every colorvar layer and every linked qualifier in both modes

**Why.** A binning or naming regression recolours every colorvar dashboard. A wrong registration breaks every linked qualified layer after a move. The served template is code emitted as strings, so a typo surfaces only at app import.

**Risk factors.**
1. The derived-field rename and the sentinel removal touch 9 test files' pins (E-16.9).
2. A domain attribute left set could leak into a later layer, figure, session or served redraw.
3. Date columns are datetime64 in served `g_df` and epoch-ms arrays in the saved CDS.
4. Unlinked graphs whose x or y has missing values change result: the key now includes those rows, as twoway's does.
5. Merge contention in batch 1:
   - S02 flips x-order pins in `test_saved_filter_layers.py`;
   - S05 edits `_make_figure_body` and `_FILTER_JS` after this section;
   - S06 owns `test_gaps2_truth.cscript`.

**Mitigation.**
1. Every flip goes through `test/colour_bins.py` and is recorded as a `Flipped:` line. Twelve existing parity colorvar cases (the CORPUS entries "colorvar()" through "colorvar() zscale(log)") and the `colorvar_truth.json` probes must stay green.
2. The attribute is set for every layer before its dispatch and reset in `finally`: the saved `_make_figure` and the served `_dash_draw_layer`. Tests pin the reset, including on an exception path, in both modes.
3. The domain is always read through `_dash_float_values(col)` on the column object. Date cases are tested in both modes.
4. CHANGELOG "Results that change" names the command, the old cut 8,895.5 and the new cut 9,598.5.
5. S07 changes no JavaScript. Its `_make_figure_body` hunks are the one-line registration fix and one inserted block. The CV-01 edit is four lines (R1 exception, Notes).

## Dependencies

- **Depends on:** S01. It places the `<!-- WP-29 P0.15 -->` and `<!-- WP-29 P0.16 -->` markers in the `**WP-29 (drop-in P0, 30sep2026)**` group of `### Results that change`, opens both BUGS.md entries in the open form with the `WP29_OPEN` keys `"P0.15"` and `"P0.16"` in `test/test_tracking_documents.py`, and creates `test/test_wp29_truth.cscript` with its tally helpers, its work directory and the marker line.
- **Blocks:**
  - **S12.** Its stale rule reads `self._view_filters`; this section makes every entry obey "ids are the source's row ids the filter keeps".
  - **S14.** Its embed restriction must keep a colorvar layer's colour rows, including rows with a missing x or y, or the key's range shrinks (index K11; contract in Notes).
- **Parallel batch:** 1. Can run with: S02, S03, S04, S05, S06, S08, S09. Merge order: S01, S09, S03, S02, S04, S06, **S07**, S05, S08.
- **Why:** this section changes no JavaScript and no Stata code. S05 (JavaScript and `_make_figure_body`) lands after it and rebases onto its two `_make_figure_body` hunks.

## Evidence

All line numbers are at `7421d3d`. Symbols are authoritative.

### E-15.1 The registration (P0.15)

`DashRenderer._make_figure_body`, the per-plot qualifier block, dash_render.py:26195-26213:

```python
26195                    _ids = list(source.data.get(_ROW_ID_COLUMN, []))
...
26199                    _wanted = {_pos.get(i, -1) for i in _pdf.index}
26200                    _mask = [bool(r in _wanted) for r in _ids]
...
26206                    _prev_bools = getattr(_prev, "booleans", None)
26207                    if _prev_bools is not None and len(_prev_bools) == len(_mask):
26208                        _mask = [bool(a and b)
26209                                 for a, b in zip(_prev_bools, _mask)]
26210                    _pf = BooleanFilter(booleans=_mask)
26211                    _plot_view = CDSView(filter=_pf)
26212                    self._register_view_filter(
26213                        source, _pf, self._row_ids_for(_pdf))
```

`_pdf` is `_apply_graph_filter` of the layer's own qualifier over `self.df`, so `_row_ids_for(_pdf)` is every row the layer's `if` selects in the whole dataset, not `_mask`'s rows.

`_FILTER_JS`, :15961-15967, rebuilds each registered view from those ids:

```js
for (const vf of (view_filters || [])) {
    ...
    const member = new Set(vf.member_ids || []);
    vf.filter.booleans = kept.map(id => member.has(id));
```

The other three registration sites already obey the invariant:
- `_linked_scatter_view`, :25534, uses `[int(i) for i, keep in zip(ids, mask) if keep]`;
- the linked graph qualifier, :27164, uses `_row_ids_for(_g_fdf)` over a source holding every row;
- the linked by() panel, :27255, uses `[i for i, keep in enumerate(mask_r) if keep]`.

**Measured** (`test_saved_filter_layers` helpers on `test_mode_parity._DF`; range move to (4500, 11385); graphs `g1` + `g2` linked; layer 2 `plot_for(t, if_expr="price > 4500")`):

| layout | type | after the move (observations drawn by layer 2) | oracle (saved page given the move as an `if`) |
|---|---|---|---|
| `by(foreign)` panel 0 | scatter, connected, dot, rspike, rconnected | `[1, 3, 4, 6, 7, 9]` | `[4, 6]` |
| `by(foreign)` panel 1 | same | `[1, 3, 4, 6, 7, 9]` | `[1, 3, 7, 9]` |
| graph `if foreign == 1` | same | `[1, 3, 4, 6, 7, 9]` | `[1, 3, 7, 9]` |
| either | line | agrees | — |

With `_register_view_filter` patched to take the ids from `source.data["__dash_row__"]` where the filter is True, all 12 cases agree. Repeated moves (4500, 11385), then (5000, 11385), then a reset to (`w.start`, `w.end`) = (3799, 11385):
- at HEAD every step DIFFERS, the reset too, for both layouts;
- patched, every step AGREES.

The served app equals the oracle for all five types (research probe3), because it recomputes each layer from `_dash_layer_frame(df, frame, graph qual)` and then the layer qualifier.

**Stata truth (rv.log, StataNow 19.5):**
- `count if foreign==0 & price>6000 & inrange(price,5000,15906)` gives `14`;
- `count if foreign==1 & price>6000 & inrange(price,5000,15906)` gives `9`.

On the Stata-written spec (research e15: `dash (scatter mpg weight) (scatter mpg weight if price>6000), by(foreign)` linked with a plain graph, `filter(price, type(range))`, move to (5000, 15906)):
- the saved page draws 23 and 23;
- the served app draws 14 and 9.

Research e15b (graph `if foreign==1`): saved 23, served 9.

**Registered ids, measured** (`p_ids.py`, `test_per_plot_qualifier_linking._render` on that file's `_DF`, see amendment 5):

```
A linked graph-if + layer-if: [([1,3,5,6],[1,3,5,6],True), ([0,2,3,6],[3,6],False)]
B linked by(foreign) + layer-if: [([0,2,4,7],[0,2,4,7],True), ([0,2,3,6],[0,2],False),
                                  ([1,3,5,6],[1,3,5,6],True), ([0,2,3,6],[3,6],False)]
```

Each tuple is (registered, the source's row ids where the filter is True, equal?).

### E-16.1 The colour key's rows (P0.16)

`GlyphMapper._apply_colorvar`, :6916-7258:
- :6952 `raw_col = source.data[varname]`;
- :7050-7056 `col_vals = _dash_float_values(raw_col)` decides numeric versus string;
- :7083-7091 cuts and bins over `col_vals`;
- :7096-7108 colordiscrete levels over `col_vals`;
- :7124-7134 string categories over `raw_col`;
- :7207-7210 continuous `lo = float(np.nanmin(col_vals))`, `hi = float(np.nanmax(col_vals))`.

It is called once, from `map_scatter` :7822, `self._apply_colorvar(fig, r, plot_source, options)`. `map_connected` (:7983), `map_rconnected` (:10951 and :10954, twice) and `map_dot` (:10984) reach it through `map_scatter`.

What source it is handed:
- **Saved, unlinked:** `map_scatter` drops rows with a missing x or y into a copy before colouring:

  ```python
  7781            x_series = pd.Series(source.data[xvar])
  7782            y_series = pd.Series(source.data[yvar])
  7783            has_nan = x_series.isna().any() or y_series.isna().any()
  7784            if has_nan:
  7785                df = pd.DataFrame({col: source.data[col] for col in source.data})
  7786                df = df.dropna(subset=[xvar, yvar])
  ```
- **Saved, with a view** (a layer's own `if`, a linked panel, a linked graph qualifier): `clean_source = source`, the graph's whole source (:7775-7777), so every row is coloured.
- **Served:** `_dash_layer_source` (:23233) runs `clean = g_df[cols].dropna(subset=_drop_on)` (:23259), and a linked layer gets the shared source plus an `IndexFilter` view (:23263-23266).

**Measured on `test_mode_parity._DF`** (`p_cv.py`, `p_my.py`, at `7421d3d`):

| case | saved | served | twoway's rule |
|---|---|---|---|
| layer `if foreign==1`, continuous | (3799, 11385) | (4453, 11385) | (4453, 11385) |
| linked graph `if foreign==1` | (3799, 11385) | (3799, 11385) | (4453, 11385) |
| linked `by(foreign)`, each panel | (3799, 11385) | (3799, 11385) | (3799, 5788) and (4453, 11385) |
| `y2 = mpg if price < 11000`, colorlevels(2), unlinked | cut 7085.5 | cut 7085.5 | cut 7592 = (3799+11385)/2 |
| same, linked | cut 7592 | cut 7592 | 7592 (right only because the qualifier is ignored altogether) |

Research measurements on Stata's auto (e16d, e16f):
- layer `if` continuous: saved 3291-15906, served 3748-12990;
- colordiscrete on rep78 under `if foreign==1`: saved factors 1..5, served 3, 4, 5.

### E-16.2 twoway's rule (measured in StataNow 19.5 through `scripts/stata_slot.sh`; this pass's `tw7.do`, the review's `rv.do`/`rv3.do`)

- **A layer's own rows.**
  - `twoway (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)` gives key ticks `4,000 6,000 8,000 10,000 12,000 14,000`. The foreign layer's fills are `{00ff00:4, 00ffaa:5, 00aaff:10, 0000ff:5, ffaa00:2, aaff00:2}`, which is 22 markers plus 6 swatches. The unqualified graph's key is 0/5,000/10,000/15,000 (research t01).
  - `summarize price if foreign==1` gives min 3748, max 12990; `if foreign==0` gives 3291 and 15906.
- **colordiscrete.** `(scatter ... if foreign==1, colorvar(rep78) colordiscrete) (scatter ... if foreign==0)`: the key axis reads `3 3.5 4 4.5 5`, three levels plus one gray marker (the foreign car with a missing rep78).
- **colorlevels(3) under the layer if:** key `6,828.7` and `9,909.3`, which are 3748 + k·(12990−3748)/3.
- **by() is per panel.**
  - `twoway scatter mpg weight, colorvar(price) colorlevels(4) by(foreign)` gives fills `{0000ff:54, 00ffaa:8, aaff00:6, ff0000:6}` and no key.
  - Single panels: `if foreign==0` gives `{42, 4, 5, 5}` with key `6,444.8 9,598.5 12,752`; `if foreign==1` gives `{14, 6, 3, 3}` with key `6,058.5 8,369 10,680`. Each includes one swatch per colour.
  - 41+13=54, 3+5=8, 4+2=6, 4+2=6, so each panel maps its own rows.
  - by() draws no key by default.
  - `by(, clegend(on))` draws one key, the first panel's (research t32-t34; routed to P1.15).
- **Missing x or y counts.** With `y2 = mpg if price < 15000`, `x2 = weight if price < 15000`, and each of `twoway scatter y2 weight`, `scatter mpg x2` and `connected y2 weight` with `colorvar(price) colorlevels(2)`, the key is `9,598.5` = (3291+15906)/2. Excluding the row would give 8,895.5.
- **rconnected.** `gen lo = mpg - 2`, then `twoway rconnected lo mpg weight, colorvar(price)` draws one key: "Price" appears once.
- **Edges.**
  - Two colorvar layers in one graph: `multiple contour, patch, or colorvar plots not allowed`, r(198).
  - `(scatter mpg weight if price>20000, colorvar(price)) (scatter mpg weight)` stops with `_calc_levels(): 3001 incorrect number of arguments`, r(3001).
  - `(scatter mpg weight if missing(rep78), colorvar(rep78))` gives rc 0, 5 gray markers, and a key showing only the title "Repair record 1978".
  - A string colorvar is `'orig' found where numeric variable expected`, r(7).

### E-16.3 The served redraw (amendment 6)

The emitted `_dash_redraw_for._redraw` (:30288-30303) calls `_dash_draw_layer(_tfig, _fr, ...)` with the FILTERED frame, so a domain computed inside `_dash_draw_layer` from `g_df` would be the post-move rows. At HEAD the redrawn rconnected line copy already re-bins on post-move cuts (measured: `{'Line': ['4749–6961', '9173–11385']}` outside the factors). The marker source (`_ly`) is not copied back (`return [_s for _s in _srcs if _s is not _ly]`), so only the copies are affected.

### E-16.4 rconnected's second key

`map_rconnected` (:10912-10955) calls `map_scatter` once per end, and each call runs `_apply_colorvar` and adds a key. Measured: `plot_for("rconnected", {"colorvar": "price"})` gives `saved ColorBars [2] served 2`.

### E-16.5 The sentinel (amendment 4)

`"__missing__"` is written at :5863, :5871, :5875, :5907 and :5913 (`_dash_colorvar_bins`), and at :7107, :7111, :7113, :7131, :7134, :7139, :7155 and :7181 (`_apply_colorvar`). Measured (`p_r34.py`): `colorvar(rep) colordiscrete` with value label `3 → "__missing__"` and one missing `rep` gives factors `['__missing__', 'four', '5', '__missing__']` with a 3-colour palette (Bokeh W-1008, PALETTE_LENGTH_FACTORS_MISMATCH). The missing row and every rep==3 row map to the first factor's colour `#1a476f`, not gray.

### E-16.6 Derived field collisions (amendments 2, 3)

Names: `color_field = f"_cvar_{varname}_bin"` (:7067, :7124), outside `_DASH_RESERVED_PREFIX = "__dash"` (:24238). Measured (`p_coll.py`; `_DF` plus a user variable `_cvar_price_bin` = 0..9; layer 1 `colorvar(price) colorlevels(3)`, layer 2 `colorvar(_cvar_price_bin)`, dropdown filter on foreign):
- **Saved.** The user column was overwritten with layer 1's labels. Layer 2 took the string path: field `_cvar__cvar_price_bin_bin`, with factors that are layer 1's labels instead of a continuous 0..9 bar.
- **Served before the move:** right (separate sources).
- **Served after the dropdown move to Foreign:** layer 1's colour column held `['1.0', '3.0', '5.0', '7.0', '9.0']`, none of them in its factors, so every marker drew in nan colour. The cause is `_dash_refresh_unlinked` (:21739), which refreshes any source column whose NAME is a frame column from the frame (`elif col in rows.columns:`, also `_dash_refresh_linked` :21631). A `__dash`-prefixed name can never be a frame column.
- **Two layers on one unlinked graph** (`p_r34.py`; `colorlevels(3)` then `colorlevels(5)`): layer 1's field held `['3799–5316.2', '5316.2–6833.4', '9867.8–11385']`, which are layer 2's labels and none of them layer 1's factors.

### E-16.7 Code sites this section changes

- `GlyphMapper.__init__` (:5971; `z_options` at :6016-6017): declare `self.colorvar_domain = None`.
- `_dash_colorvar_bins` (:5828-5916): add `bin_values=None`; `None` for missing.
- New module function `_dash_colorvar_domain`, after `_dash_option_columns` (:22397-22412).
- New module function `_dash_colorvar_field`, after it.
- New constant `_DASH_CVAR_PREFIX`, after `_DASH_JITTER_Y` (:2213).
- `GlyphMapper._apply_colorvar` (:6916-7258).
- `GlyphMapper.map_scatter` (:7720-7822).
- `GlyphMapper.map_rconnected` (:10912-10955).
- `DashRenderer._make_figure` (:25884-25918): `finally` reset.
- `DashRenderer._make_figure_body`: registration (:26212-26213); domain block inserted before `# Snapshot renderer list` (:26221).
- Served copy lists: the constants tuple, `"_DASH_CVAR_PREFIX"` after `"_DASH_JITTER_Y"` (:28383); the functions tuple, `"_dash_colorvar_domain", "_dash_colorvar_field"` after `"_dash_colorvar_bins"` (:28796).
- `ServerAppBuilder._generate_app_source` (:29269): the emitted `_dash_draw_layer` (:30162-30245), `_dash_redraw_for` (:30264-30304), and the redraw registration (:30588).
- No change: `_FILTER_JS`, `dash.ado`, `dash_parse.mata`. Stata-written specs already carry per-plot `qual_col` and graph qualifiers.

### E-16.8 Blast radius (R8)

At plan time the GitNexus server did not hold this repository: `impact` answered `Repository "dash" not found. Available: TYME, PhotoShootPlannerPro`. The executor runs `npx gitnexus analyze`, then `gitnexus_impact({target, direction: "upstream"})` for each edited symbol, and records the result in the commit body. The callers by grep at `7421d3d`:
- `_apply_colorvar`: 1 (`map_scatter` :7822).
- `_dash_colorvar_bins`: 1 (:7089), plus the app copy.
- `map_scatter`: 4 direct, plus the dynamic dispatch through `_add_glyph`/`_dash_add_glyph` for every scatter layer in both modes.
- `_make_figure_body`: 2 (`_make_figure` :25915, :25918). It is expected HIGH (index R8): every figure of every saved dashboard. **Report HIGH to the maintainer before editing.**
- `_register_view_filter`: 4 (:25534, :26212, :27164, :27255).
- Emitted `_dash_draw_layer`: 2 (:30302, :30560). Emitted `_dash_redraw_for`: 1 (:30588).

### E-16.9 Tests that pin today's behaviour (flip, never delete; R7)

Field-name readers (route through `test/colour_bins.py`):
- `test/test_colorvar_forms.py:62` (`_bins` helper) and `:340` (`TestBothModes::test_both_modes_draw_the_same_bins`);
- `test/test_colorvar_truth.py:95` (`TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does`), `:162` and `:167` (`TestColorlevelsOutsideTwoToAHundred`);
- `test/test_function_audit.py:302` (`_bins`), `:364`, `:372-373` and `:418-420`;
- `test/test_glyphs.py:3453-3454` (`TestApplyColorvarOptions::test_colordiscrete_derived_bin_column_created`);
- `test/test_dropdown_values.py:360`;
- `test/test_server.py:7487` (the `colour_bins` parameter of `TestServerFilterPreservesDerivedColumns::test_a_derived_column_keeps_each_kept_rows_value_after_a_move`);
- `test/test_gaps2_truth.cscript:781-782` (CV-01).

Sentinel readers (`"__missing__"` becomes `None`):
- `test/test_colorvar_forms.py:92-94`, `:127-128`, `:203-210`, `:224`;
- `test/test_function_audit.py:330-331`, `:340-341`, `:395-396`;
- `test/test_glyphs.py:3470` and `:3498` (the filter becomes a no-op: drop the `!= "__missing__"` condition) and `:3550-3555` (`test_colormissing_included_in_palette_for_discrete` becomes a test of `nan_color` plus a "(missing)" key entry);
- `test/test_dropdown_values.py:361`;
- `test/test_help_claims_7.py:515-516` (`TestAStringColorvar::test_a_repeated_value_is_one_level`: factors become `["D", "F"]`, and `mapper.nan_color` becomes `#ff0000`).

Guards that need no new code:
- `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` fail if a new name is read by the app but missing from a copy list;
- `test_function_test_map.py` requires the new map entries.

No test pins the P0.15 wrong rows: `test_per_plot_qualifier_linking.py` is 7/7 green at HEAD, and `test_the_filter_callback_knows_about_it` counts booleans, which the fix does not change. No colorvar test asserts the all-rows range under a qualifier.

## User stories

- **US-07.1** As a dashboard reader, I want a plot with its own `if` inside a linked `by()` panel, or inside a linked graph with its own `if`, to keep to that panel's or graph's observations after every filter move, a second move and a reset, so the saved page shows what the served app and Stata's `count` show.
- **US-07.2** As a twoway user, I want `colorvar()`'s colour bar, its `colorcuts()`/`colorlevels()` cuts and its `colordiscrete` levels to come from the observations the plot draws (its own `if`/`in`, the graph's and its `by()` panel's), counting observations whose x or y is missing, so the key reads as twoway's does.
- **US-07.3** As a dashboard reader of a linked `by()` graph, I want each panel coloured over its own observations, as twoway colours them.
- **US-07.4** As a dashboard reader, I want the colours and the key to stay as built when I move a filter, in both modes, so a colour means the same thing before and after.
- **US-07.5** As a Stata user with a variable that happens to be named like a column dash makes, I want my variable never overwritten, so my second plot's colours are my data.
- **US-07.6** As a Stata user whose value labels say anything at all (even `__missing__`), I want missing values drawn in `colormissing()`'s colour and each labelled level in its own colour.
- **US-07.7** As a twoway user, I want one colour key per `rconnected` plot, as twoway draws.
- **US-07.8** As the maintainer, I want these rules pinned against live twoway exports and Stata's `summarize`/`count`, in both modes, so they cannot drift.

## Business requirements

- **BR-07.1** After any sequence of filter moves on a saved page, a layer whose view is a per-plot qualifier intersected with a linked `by()` panel or a linked graph qualifier draws exactly the observations that are in its panel or graph, satisfy its own qualifier, and pass the filters. This equals the served app, and Stata's `count if`. A reset to the full range draws the first paint again.
- **BR-07.2** The colour rows of a colorvar layer are the observations its graph's `if`/`in`, its own `if`/`in` and, under `by()`, its panel select, including observations whose x or y is missing. The same definition holds in both modes, for a linked and an unlinked graph.
- **BR-07.3** The colour bar's range, the cuts of `colorcuts()`/`colorlevels()`, the `colordiscrete` levels, a string variable's categories, and whether a "(missing)" key entry exists are computed from the colour rows only.
- **BR-07.4** The key and each observation's colour are fixed at build time, in both modes, and a filter move never re-ranges them.
- **BR-07.5** A colour is never taken from, written to, or confused with a user variable or a user value. A missing value is drawn in `colormissing()`'s colour, and no value or label text can turn a level into "missing" or "missing" into a level.
- **BR-07.6** A colorvar plot draws exactly one key; `rconnected` colours both ends from it.
- **BR-07.7** A plot whose colour rows are empty draws no key and stops nothing (twoway: r(3001), documented). A plot whose colour rows are all missing draws its markers in `colormissing()`'s colour with a "(missing)" key entry (twoway: the key's title only, documented).
- **BR-07.8** Every changed result is in CHANGELOG "Results that change" with the command, the old value and the new.

## Technical requirements

- **TR-07.1 (P0.15) Registration.**
  - In `_make_figure_body`'s per-plot block, replace `self._register_view_filter(source, _pf, self._row_ids_for(_pdf))` (:26212-26213) with `self._register_view_filter(source, _pf, [int(r) for r, keep in zip(_ids, _mask) if keep])`, under a comment naming WP-29 P0.15.
  - `_register_view_filter`'s signature and the three other call sites are unchanged.
  - Invariant (pinned by the test): for every `(source, flt, ids)` in `self._view_filters`, `sorted(ids) == [int(i) for i, b in zip(source.data["__dash_row__"], flt.booleans) if b]`.
  - The served app is not changed.
- **TR-07.2 Constant.**
  - `_DASH_CVAR_PREFIX = "__dash_cvar"` goes after `_DASH_JITTER_Y` (:2213), with a comment saying it is the colour bins of colorvar(), one column per layer (WP-29 P0.16).
  - Add it to the served constants tuple after `"_DASH_JITTER_Y"` (:28383).
  - `test_internal_column_names.py` lists it in `test_every_column_constant_starts_with_the_prefix`.
- **TR-07.3 `_dash_colorvar_domain(columns, options, mask=None, where="")`.** A module function placed after `_dash_option_columns`.
  - It returns None when any of these holds:
    - `options["colorvar"]` is empty;
    - the name fails `_dash_is_stata_name`;
    - `columns[var]` raises `KeyError`/`TypeError`/`IndexError`;
    - `mask` is not None and `np.asarray(mask, dtype=bool).shape != (len(col),)`. In this case it first warns once per call: `dash: {where or 'a layer'}: its colour key could not be restricted to its observations ({m} flags for {n} rows); the key is drawn from every row.`
  - Otherwise it tries `vals = _dash_float_values(col)` on the column object itself (Series, ndarray or list; never `list(col)` first) and returns `vals[mask]` (or `vals`).
  - On `ValueError`/`TypeError` (a string column) it returns the list `col.tolist() if hasattr(col, "tolist") else list(col)`, filtered by `mask`.
  - It accepts a DataFrame (served `g_df`) and a CDS `.data` dict (saved).
  - A `__proto__` column is an ordinary Stata name and is returned like any other.
  - Add it to the functions tuple after `"_dash_colorvar_bins"` (:28796), and to `function_test_map.py` (TR-07.11).
- **TR-07.4 `_dash_colorvar_field(data, varname)`.** A module function placed after `_dash_colorvar_domain`.
  - It returns None if `not _dash_is_stata_name(varname)`.
  - Otherwise it returns the first `f"{_DASH_CVAR_PREFIX}{k}_{varname}"`, for k = 1, 2, …, that is not a key of `data`.
  - It always terminates within `len(data) + 1` steps.
  - It goes on the functions tuple after `"_dash_colorvar_domain"`.
- **TR-07.5 `_dash_colorvar_bins(col_vals, cuts, discrete, label_of, closed_ends=False, number_text=None, bin_values=None)`.** `col_vals` is the domain, and `rows = col_vals if bin_values is None else bin_values` (both as float arrays).
  - The labels (interval labels, closed-end bounds from the domain's `nanmin`/`nanmax`, discrete cut labels) and `has_missing` are computed from the domain only:
    - interval mode: any domain NaN;
    - discrete mode: any domain value NaN or equal to no cut;
    - empty `cuts`: True when the domain has a row.
  - `binned` has one entry per row of `rows`. An entry is `None` for NaN, `None` for a value below the domain's finite minimum or above its maximum (never clamped), and `None` in discrete mode for a value equal to no cut. Otherwise it is the label.
  - Returns `(labels, binned, has_missing)`. The docstring states the `None` rule and drops every mention of `"__missing__"`.
  - The nested `_interval_labels` and `_assign` keep their names (`function_test_map.py` :451-452).
- **TR-07.6 `GlyphMapper`.**
  - `__init__` sets `self.colorvar_domain = None` beside `z_options`, with a comment saying callers set it per layer and reset it in `finally`.
  - `_apply_colorvar(self, fig, renderer, source, options, add_key=True)`:
    1. After the name checks, read `dom = self.colorvar_domain`. If `dom is not None and len(dom) == 0`, return without changing the glyph or adding anything (empty domain).
    2. The numeric/string decision stays on the full column (`col_vals`). If numeric, `dom_vals = col_vals if dom is None else _dash_float_values(dom)`. If the domain cannot be read as numbers, warn `dash: colorvar({varname}): the colour key's observations could not be read; the key is drawn from every row.` and use `col_vals`.
    3. If numeric and `dom_vals` has no finite value, take the discrete path with no levels: every row `None`, key "(missing)" only.
    4. Continuous: `lo, hi = np.nanmin(dom_vals), np.nanmax(dom_vals)`.
    5. Cuts and levels: `eff_cuts = _dash_colorvar_cuts(dom_vals, cuts, nlevels, minmax)`, then `_dash_colorvar_bins(dom_vals, eff_cuts, force_discrete, _vlookup, closed_ends=_closed, number_text=_num_text, bin_values=col_vals)`.
    6. colordiscrete without cuts: levels from the distinct finite `dom_vals`; each source row takes `None` if NaN, else `val_label.get(v)`; `has_missing` is "any NaN in `dom_vals`".
    7. String: `strs` of the domain (`raw_col` when `dom is None`) give `labels = sorted({s for s in strs_dom if s != ""})` and `has_missing = "" in strs_dom`. Each source row takes `None` if its text is `""` or not in `labels`, else its text.
    8. `color_field = _dash_colorvar_field(source.data, varname)`; on None, return.
    9. `factors = labels`; return when `not labels and not has_missing`. The palette is one colour per label.
    10. `CategoricalColorMapper(factors=labels, palette=pal_colors, nan_color=missing_color)`. The legend has one swatch per label, plus a "(missing)" swatch (`missing_color`) when `has_missing`. The missing swatch keeps its model name `f"{_DASH_SWATCH_PREFIX}__missing__"`: it is a model name, never a factor.
    11. `add_key=False` builds the mapper exactly as `add_key=True` does, `_dash_apply_z_options` included, so a log mapper is shared. It skips only the swatch renderers and the `fig.add_layout` of the Legend or ColorBar.
    12. The auto legend item is stripped in both cases.
  - `map_scatter(..., color_idx=0, colorvar_key=True)` passes `add_key=colorvar_key`.
  - `map_rconnected` passes `colorvar_key=False` to its second `map_scatter` (:10954).
- **TR-07.7 Saved wiring.**
  - In `_make_figure_body`, immediately after the per-plot block's `except` and before `# Snapshot renderer list` (:26221), insert:

    ```python
    _cv_mask = None
    if _plot_view is not None and str(popts.get("colorvar") or "").strip():
        _cv_mask = self.mapper._view_mask(
            _plot_view, len(next(iter(source_for_plot.data.values()), [])))
    self.mapper.colorvar_domain = _dash_colorvar_domain(
        source_for_plot.data, popts, _cv_mask,
        where=f"graph {graph_opts.get('name', '') or '(unnamed)'} plot {pi + 1}")
    ```

    `_plot_view` here is the facet or linked view intersected with the per-plot view. It does not yet carry `_linked_scatter_view`'s missing-x/y mask, which is folded in later inside the dispatch.
  - Every layer sets the attribute, so none inherits another's.
  - `_make_figure`'s body (both `return` paths) is wrapped in `try: ... finally: self.mapper.colorvar_domain = None`, so no figure, exception or later render inherits it.
- **TR-07.8 Served wiring (emitted lines in `_generate_app_source`).**
  - `_dash_draw_layer(fig, g_df, plot, pi, gname, _ln, _shared, _fallback, sidx=None, cv_domain=None)`.
  - After `_ly_src = None` it emits `_DASH_MAPPER.colorvar_domain = (cv_domain if cv_domain is not None else _dash_colorvar_domain(g_df, opts))`, then `try:`. The family dispatch (from `if ptype == 'scatteri':` to the end of the `else:` branch) is indented one level inside the `try`, followed by `finally:` and `_DASH_MAPPER.colorvar_domain = None`. `g_df` is the layer frame before `_dash_layer_source`/`_dash_range_source` drop missing x or y.
  - `_dash_redraw_for(g, plot, pi, gname, cv_domain=None)` binds `_cv_dom = cv_domain`, and `_redraw` calls `_dash_draw_layer(_tfig, _fr, plot, pi, gname, set(), None, None, sidx=_sidx, cv_domain=_cv_dom)`.
  - The registration at :30588 becomes `'redraw': _dash_redraw_for(g, plot, pi, gname, cv_domain=_dash_colorvar_domain(g_df, plot.get('options', {}))),`.
  - No user text enters the emitted code: every emitted line is a fixed string.
- **TR-07.9 Parity profile (`test/test_mode_parity.py`).**
  - `_glyph_profile` records, for a `fill_color` that is a field with a transform, `entry["colour"]` = `{"mapper": type name, "factors": list or None, "palette": list, "low": _num, "high": _num, "nan_color": str, "values": [the field's value at each drawn row, None kept as None]}`.
  - When the field name starts with `dr._DASH_CVAR_PREFIX` or `_cvar_`, the recorded `fill_color`/`line_color` spec is replaced with `("field", "<colour bins>")`. The two modes are compared on colours, not on a renumbered column name.
  - `_annotations` records a `ColorBar` as `{"kind": "ColorBar", "title": r.title, "mapper": type(r.color_mapper).__name__, "low": _num(low), "high": _num(high), "side": panel.get(id(r))}`.
  - `ALLOWED` and `_MUST_WARN` are not edited (R6).
- **TR-07.10 Truth helpers (`test/filter_truth_check.py`).**
  - `layer_rows(spec_path, data_path, moves)` returns `{"saved": [[rows drawn by each visible glyph renderer] per figure in layout order], "served": [...]}` after `moves`, given as `[(filter index, value)]`.
    - Saved: `DashRenderer` plus `js_runner.JsSession` (as `saved()` does).
    - Served: the app built and fired (as `served()` does). The filter order is read from the spec JSON's `build_options["filters"]`.
    - Rows are counted through each renderer's view, using `test_mode_parity._layout_tree` profiles' `rows`.
  - `colour_keys(spec_path, data_path)` returns `{"saved": [fig...], "served": [fig...]}` in layout order, each `{"bars": [[low, high], ...], "factors": [[...] per colour-mapped renderer], "keys": <ColorBars + Legends named dr._COLORVAR_LEGEND_NAME>}`.
  - Neither calls Stata, nor uses `shell=True` or `eval`.
- **TR-07.11 Maps.** `test/function_test_map.py`:
  - `DashRenderer._register_view_filter` becomes `test/test_per_plot_qualifier_linking.py::TestTheRegisteredRowsAreTheViewsOwn::test_every_registered_view_names_exactly_its_true_rows`;
  - new `_dash_colorvar_domain` is `test/test_colorvar_forms.py::TestTheColourDomain::test_rows_with_a_missing_y_are_kept`;
  - new `_dash_colorvar_field` is `test/test_colorvar_forms.py::TestTheColourFieldName::test_the_field_helper_takes_the_first_free_name`;
  - `_dash_colorvar_bins` becomes `test/test_colorvar_forms.py::TestTheBinHelperOverADomain::test_a_value_outside_the_domain_is_none`;
  - `GlyphMapper._apply_colorvar` stays as it is.
  - Keys go in alphabetical place (R2). No `program_coverage_map.py` change: no Stata program changes.
- **TR-07.12 Security (rule 1).**
  - The colorvar name passes `_dash_is_stata_name` before any column, field or warning use, and the warning text bounds it at 32 characters by that check.
  - Derived names are the fixed prefix, decimal digits, `_` and the validated name. The loader's `__dash` refusal makes a collision with data impossible.
  - Missing is `None`, never a string, so no user value or label can collide with it.
  - Emitted app lines are fixed strings.
  - The domain costs O(rows) per colorvar layer, inside the existing plot and row caps.
  - The help gives no new user text a path into HTML.

## Boundaries

- **Changes allowed:**
  - JavaScript: none in `_FILTER_JS` or any other script.
  - `dash.ado` and `dash_parse.mata`: none.
- **Not here:**
  - by() key presence and `clegend()` (P1.15; truth recorded in the fixture's `by_clegend_*` probes and in Notes).
  - twoway's refusal of two colorvar layers (residual to S15).
  - A key that re-ranges after a filter move (BR-07.4 keeps it fixed).
  - S05's date units: the colour domain of a date colorvar stays in epoch ms, as the colour bar is drawn today. If S05 changes that, S05 flips this section's date tests in its own commit.
- **Kept as they are:**
  - the `_DASH_SWATCH_PREFIX` names;
  - `_rebuild_legend`;
  - `_dash_apply_z_options`;
  - colorlevels() 0/1/over-100 handling (WP-28 follow-up);
  - the string-path rule that `'nan'` is a category.
- **Tracking documents (A5):** `REMAINING.md`, `.ultraplan/handoff/DROPIN-REMAINING.md`, `ROADMAP.md`, `GAPS2.md` and `AGENTS.md` are not edited here. Their text goes to S15 (Notes for the closeout).
- **Cscript scripts:**
  - No new `.cscript`.
  - `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` pins are not edited (R1).
  - `test_gaps2_truth.cscript` is touched only at CV-01's four lines (R1 exception, Notes).
- **Silent when honoured:** no new note is printed on the success path. The only new warnings are the mask-mismatch warning and the unreadable-domain warning, which a correct spec never triggers.

## Stata truth

**Fixture.** A new script, `scripts/extract_colorvar_qualifier_truth.do`, writes the new fixture `test/fixtures/colorvar_qualifier_truth.json`. `colorvar_truth.json` is untouched (R5).

**Run it** through the wrapper only (rule 10):
`DASH_REPO=<worktree> dash_nobrowser=1 scripts/stata_slot.sh <scratch> <worktree>/scripts/extract_colorvar_qualifier_truth.do`. Read `<scratch>/extract_colorvar_qualifier_truth.log` and never relaunch to check.

**Script frame.** It follows `scripts/extract_colorvar_truth.do`:
- `global ZQ_REPO` defaults to the main checkout, and `local zq_env : env DASH_REPO` overrides it;
- `adopath ++ "${ZQ_REPO}"`, `quietly do` of `dash_parse.mata` and `dash.ado`, and `global dash_nobrowser 1`;
- the work directory is `"`c(tmpdir)'dash_colorvar_qualifier_probe"`;
- it exits 601 if `c(python_exec)` is empty.

**Per probe it records:**
- the twoway command, its rc and its message (rc probes run under `capture noisily` and a log);
- `qual_obs`, the 1-based observation numbers where the probe's qualifier is true;
- `fills`, the in-plot-region `circles` fills of `svg_document()` in document order;
- `fill_counts` over every circle;
- `key_texts`, the `svg_texts()` whose `x` exceeds `plotregion["right"]`;
- `key_title_count`, the number of texts equal to the colorvar's variable label;
- `summ_min`/`summ_max` from `summarize <colorvar> if <qualifier>`, with r(min) and r(max) written into locals before the python block.

**`_data.auto`** holds `mpg`, `weight`, `foreign`, `price` and `rep78` in observation order, with missing as null. `_meta` holds `stata_version`, `born_date`, `dash_commit` (from `quietly shell git -C "${ZQ_REPO}" rev-parse HEAD > <work>/git_head.txt`, read in Python from the file, never `shell=True`), `extracted`, `qualified_order_selfcheck` and `by_panel_selfcheck`. The python block never calls back into Stata, and writes a backtick as `\x60` if one is ever needed.

Probes (sysuse auto; `gen y2 = mpg if price < 15000`, `gen x2 = weight if price < 15000`, `gen lo = mpg - 2`, `gen dom = 1 - foreign`, with label `dom` 0 "Domestic" 1 "Foreign" swapped so the first panel is Foreign):

| id | command | measured (must be recorded) |
|---|---|---|
| `q_if_cont` | `twoway (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)` | key `4,000`…`14,000`; summ 3748/12990 |
| `q_cmd_if` | `twoway scatter mpg weight if foreign==1, colorvar(price)` | same key |
| `q_unqual` | `twoway scatter mpg weight, colorvar(price)` | key `0 5,000 10,000 15,000` |
| `q_if_disc` | `twoway (scatter mpg weight if foreign==1, colorvar(rep78) colordiscrete) (scatter mpg weight if foreign==0)` | 3 levels + 1 gray; key 3..5 |
| `q_if_lv3` | the same with `colorvar(price) colorlevels(3)` | key `6,828.7`, `9,909.3` |
| `q_if_cuts` | the same with `colorvar(price) colorcuts(5000 10000)` | key `5,000`, `10,000` |
| `by_lv4` | `twoway scatter mpg weight, colorvar(price) colorlevels(4) by(foreign)` | fills 54/8/6/6, no key |
| `by_lv4_p0`, `by_lv4_p1` | `twoway scatter mpg weight if foreign==0` (and `==1`)`, colorvar(price) colorlevels(4)` | 42/4/5/5, key `6,444.8 9,598.5 12,752`; 14/6/3/3, key `6,058.5 8,369 10,680` |
| `by_cont` | `twoway scatter mpg weight, colorvar(price) by(foreign)` | no "Price" text |
| `by_if_lv4` (+ `_p0`, `_p1`) | `twoway scatter mpg weight if price<6000, colorvar(price) colorlevels(4) by(foreign)` | totals 9/21/12/9 (research t35) |
| `by_total` | `twoway scatter mpg weight, colorvar(price) by(foreign, total)` | recorded |
| `by_clegend_cont`/`_lv4`/`_disc` | `by(dom, clegend(on))` with `colorvar(price)` / `colorlevels(4)` / `colorvar(rep78) colordiscrete` | first panel's key: 4,000–14,000 / 6,058.5 8,369 10,680 / 3..5. Recorded for P1.15; no S07 test asserts it |
| `missing_y_lv2` | `twoway scatter y2 weight, colorvar(price) colorlevels(2)` | key `9,598.5` |
| `missing_x_lv2` | `twoway scatter mpg x2, colorvar(price) colorlevels(2)` | key `9,598.5` |
| `missing_y_connected` | `twoway connected y2 weight, colorvar(price) colorlevels(2)` | key `9,598.5` |
| `rconnected_key` | `twoway rconnected lo mpg weight, colorvar(price)` | `key_title_count` 1 |
| `all_missing` | `twoway (scatter mpg weight if missing(rep78), colorvar(rep78))` | rc 0, `fill_counts` {#808080: 5}, title only |
| `empty_layer` | `twoway (scatter mpg weight if price>20000, colorvar(price)) (scatter mpg weight)` | rc 3001 |
| `multi_colorvar` | `twoway (scatter mpg weight, colorvar(price)) (scatter mpg weight, colorvar(rep78))` | rc 198, message `multiple contour, patch, or colorvar plots not allowed` |

**Self-checks written into `_meta`** (`"held"` or `"failed: <why>"`):
1. `qualified_order_selfcheck`: in `q_if_disc`, the canonical partition of the first `len(qual_obs)` in-region fills equals the canonical partition of `rep78` over `qual_obs` (missing as its own group). This proves document order is observation order for a qualified first layer.
2. `by_panel_selfcheck`: for `by_lv4` and `by_if_lv4`, each colour's `fill_counts` total equals the sum of its two single-panel probes' totals minus one key swatch per colour.

Add the fixture with `git add -f test/fixtures/colorvar_qualifier_truth.json`. `test_colorvar_truth.py` names it, which satisfies `test_fixtures_are_committed.py` without editing that file.

**Live certification (A3).** `test/test_wp29_truth.cscript` block `* ==== S07 P0.16: colorvar key from the layer's rows ====`, gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S07")`, holds CQV-01..CQV-09. Each case exports its twoway SVG live (`cert_svg_export`) and compares with the saved and served pages built from `_dash_serve_spec` through `filter_truth_check.colour_keys`. Run it with the driver:

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_wp29_truth.cscript" > <scratch>/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S07 scripts/stata_slot.sh <scratch> <scratch>/run_test_wp29_truth.do
```

QF-01 and QF-02 compute their truth inline with `count if` and need no fixture.

## TDD test stubs

The first stubs of each cycle are its regression tests. **(red)** means the test fails at the cycle's base for the reason stated; **(guard)** means it passes there and must still pass. Each failure text is saved verbatim.

### P0.15 (base: the batch-1 base sha)

- **Test:** `test/test_saved_filter_layers.py::TestEveryLayerFollowsAMove::test_the_page_draws_the_kept_rows`, new `_CORPUS` entries for `t` in `("scatter", "connected", "dot", "rspike", "rconnected", "line", "area", "bar", "rcap")`. Each type gets two cases:
  - `_case(f"{t} with its own if under a linked by(), {_MOVES[1][0]}", _MOVES[1], graphs=[("g1", [plot_for("scatter"), plot_for(t, if_expr="price > 4500")], {"by": "foreign"}), ("g2", [plot_for("scatter")])], bo={"link": "g1 g2"})`;
  - `_case(f"{t} with its own if in a linked graph with its own if, {_MOVES[1][0]}", _MOVES[1], graphs=[("g1", [plot_for("scatter"), plot_for(t, if_expr="price > 4500")], None, {"if_expr": "foreign == 1"}), ("g2", [plot_for("scatter")])], bo={"link": "g1 g2"})`.

  scatter, connected, dot, rspike and rconnected are **red** (10 ids; the panel draws `[1, 3, 4, 6, 7, 9]`). line, area, bar and rcap are guards. `test_the_move_changed_what_is_drawn` runs for every new id (guard).
- **Test:** `test/test_saved_filter_layers.py::TestALinkedLayersOwnIfAcrossMoves::test_every_step_draws_the_kept_rows[by|graph-if]`. The layer `plot_for("scatter", if_expr="price > 4500")` sits under the by() and graph-if layouts above. The RangeSlider moves through `(4500.0, 11385.0)`, `(5000.0, 11385.0)` and `(w.start, w.end)` with `_move` on ONE rendered page. After each step `_profile(r)` equals `_saved_of_rows(spec, "price >= 4500 & price <= 11385")`, then `"price >= 5000 & price <= 11385"`, then the first paint's `_profile`. **Red** at every step.
- **Test:** `test/test_saved_filter_layers.py::TestTheSavedPageAgreesWithTheServedApp::test_a_qualified_layer_in_a_linked_graph[by|graph-if]`, with layer 2 `plot_for("scatter", if_expr="price > 4500")` in the two layouts above. The glyphs of `_saved_after_move(spec, action)` equal the glyphs of `test_mode_parity._served_after_move(spec, action)[0]`, figure by figure, with `_diff`. **Red** (saved side).
- **Test:** `test/test_saved_filter_layers.py::TestTheTruthCheckHelpers::test_layer_rows_reads_both_modes` (written in 07-02). A spec of one plain scatter with a dropdown on foreign, written with `_write`: `filter_truth_check.layer_rows(sp, dp, [(0, 1.0)])` gives `{"saved": [[5]], "served": [[5]]}`. Guard (helper unit test).
- **Test:** `test/test_per_plot_qualifier_linking.py::TestTheRegisteredRowsAreTheViewsOwn::test_every_registered_view_names_exactly_its_true_rows`, parametrised:
  - `linked by() with a layer if` (**red**);
  - `linked graph if with a layer if` (**red**);
  - `linked scatter with a missing y` (guard; `_DF` copy with `mpg` NaN on row 2);
  - `linked jittered scatter` (guard; `{"jitter": "5", "jitterseed": "1"}`).

  `_render` gains an optional `df=None` argument, defaulting to `_DF`. For every entry of `r._view_filters`: `sorted(ids) == [int(i) for i, b in zip(src.data["__dash_row__"], flt.booleans) if b]`.
- **Test:** `::test_a_linked_graph_if_and_a_layer_if_register_their_intersection`. The expected ids are derived as `sorted(int(i) for i in _DF.index[(_DF.foreign == 1) & (_DF.weight < 3000)])` (`[3, 6]` on this file's `_DF`). The test asserts the per-plot entry's ids equal them. **Red**: `[0, 2, 3, 6]`.
- **Test:** `::test_a_linked_by_panel_layer_registers_only_its_panels_rows`. The expected ids per panel are derived from `_DF` (`[0, 2]` and `[3, 6]`). **Red**: `[0, 2, 3, 6]` for both.
- **Test:** `test/test_mode_parity.py` `MOVE_CORPUS` gains two entries; all their `TestAFilterMoveAgrees` tests are guards (served equals the oracle at HEAD):
  - `_move_case("a layer's own if under a linked by(), range", _MOVES[1], graphs=[("g1", [_sc(), plot_for("scatter", if_expr="price > 4500")], {"by": "foreign"}), ("g2", [_sc()])], bo={"link": "g1 g2"})`;
  - `_move_case("a layer's own if in a linked graph with its own if, range", _MOVES[1], graphs=[("g1", [_sc(), plot_for("scatter", if_expr="price > 4500")], None, {"if_expr": "foreign == 1"}), ("g2", [_sc()])], bo={"link": "g1 g2"})`.
- **Cscript** `test/test_e2e_filters.cscript`:
  - **QF-01** (**red**: saved 23/23). In sysuse auto, Stata builds `dash (scatter mpg weight) (scatter mpg weight if price > 6000), by(foreign) title("g1") name(g1)` and `dash scatter mpg weight, title("g2") name(g2)`, then `_dash_serve_spec, specpath(...) datapath(...) link(g1 g2) filter(price, type(range))`. `layer_rows(..., [(0, (5000.0, 15906.0))])`: in both modes, figure 0's second count equals `count if foreign==0 & price>6000 & inrange(price,5000,15906)` (14), and figure 1's equals the `foreign==1` count (9).
  - **QF-02** (**red**: saved 23). The same with `dash (scatter mpg weight) (scatter mpg weight if price > 6000) if foreign == 1, title("g1") name(g1)`: figure 0's second count is 9 in both modes.

### P0.16 (base: the P0.15 commit)

`test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows` loads `colorvar_qualifier_truth.json`. A missing fixture is `pytest.fail` naming task 07-05, never a skip. The class builds a frame from `_data.auto` with `y2`/`x2` as in Stata, renders through `test_mode_parity._standalone`/`_served` with `monkeypatch.setattr(tp, "_DF", frame)`, and reads keys through `test/colour_bins.py`. Every test is parametrised `mode` in `("saved", "served")`; the layout tests are also parametrised `linked` in `(False, True)`.
- `test_a_layers_own_if[...]`: the spec `[plot_for("scatter", {"colorvar": "price"}, if_expr="foreign == 1"), plot_for("scatter", if_expr="foreign == 0")]`. `colour_bars` equals `[(q_if_cont.summ_min, summ_max)]` = (3748, 12990). **Red** saved (3291, 15906); served guard.
- `test_colordiscrete_levels_of_a_layers_own_if[...]`: rep78 `colordiscrete`. The factors are `["3", "4", "5"]`, and the colorvar Legend's last item is "(missing)". **Red** saved (1..5); served guard.
- `test_colorlevels_cuts_of_a_layers_own_if[...]`: `colorlevels(3)`. `colour_bins.interval_bounds(factors)` has outer bounds 3748 and 12990 and interior bounds within 0.01 of 6828.667 and 9909.333, with `round(b, 1)` equal to `q_if_lv3`'s key texts read as numbers. The canonical partition of the 22 drawn foreign rows equals the canonical partition of `q_if_lv3.fills[:len(qual_obs)]`. **Red** saved; served guard.
- `test_a_linked_graphs_own_if[...]`: g1 `if foreign == 1` with colorvar(price), linked with g2. The range is (3748, 12990). **Red** in both modes (3291/15906).
- `test_each_by_panel_maps_its_own_rows[linked x mode]`: by(foreign), colorlevels(4).
  - Domestic outer bounds are 3291/15906 and Foreign's are 3748/12990.
  - Each panel's canonical partition equals `by_lv4_p0`/`by_lv4_p1`'s fill partition over their qualifying rows.
  - The continuous form gives the ranges (3291, 15906) and (3748, 12990).
  - Linked **red** in both modes; unlinked guard.
- `test_rows_with_a_missing_y_count[linked x mode]`: `scatter y2 weight, colorvar(price) colorlevels(2)`. The single interior bound is 9598.5 (= `missing_y_lv2` key text). Unlinked **red** in both modes (8895.5); linked guard.
- `test_rows_with_a_missing_x_count[...]`: `scatter mpg x2`, the same rule. Unlinked **red**.
- `test_a_connected_layer_with_a_missing_y_counts[...]`: `connected y2 weight`. Unlinked **red**.
- `test_the_qualifier_fixture_carries_its_provenance_and_self_checks`: the four `_meta` keys, both self-checks `"held"`, `rconnected_key.key_title_count == 1`, `multi_colorvar.rc == 198`, `empty_layer.rc == 3001`. Guard after 07-05.

`test/test_date_range.py::TestADateColorvarUnderALayersIf` uses `_spread_frame()` with `{"type": "scatter", "yvar": "lo", "xvar": "hi", "options": {"colorvar": "date"}, "if_expr": "lo >= 6"}`, through `_saved` and `_served`:
- `test_the_key_spans_the_layers_dates[saved|served]`: the LinearColorMapper's (low, high) equals the epoch ms of `_SPREAD[6]` and `_SPREAD[11]`. **Red** saved; served guard. The test fails if `_served` raises TypeError.
- `test_colorlevels_cut_the_layers_dates[saved|served]`: with `colorlevels(3)`, the two interior bounds are the ms values `lo + k*(hi-lo)/3`. **Red** saved.

`test/test_mode_parity.py`:
- TR-07.9's profile additions apply to every corpus.
- `CORPUS` gains five cases:
  - `"colorvar() with a layer's own if"`;
  - `"colorvar() colordiscrete with a layer's own if"` (rep);
  - `"colorvar() colorlevels(3) with a layer's own if"`;
  - `"colorvar() on a linked graph with its own if"`;
  - `"colorvar() under a linked by()"` (`{"by": "foreign"}`, `link g1 g2`).
- `TestTheTwoModesAgree::test_same_glyphs`/`test_same_annotations` are **red** for the three unlinked layer-if cases (saved range or levels differ from served), and guards for the two linked cases (both modes are equally wrong at base).

`test/test_colorvar_forms.py`:
- `TestTheColourBinsHelpers` — unit tests of every `test/colour_bins.py` function on hand-built models. Guard.
- `TestTheColourDomain` (**red**: no attribute `_dash_colorvar_domain`):
  - `test_no_colorvar_gives_none`;
  - `test_a_refused_name_gives_none`, parametrised over `["price; x", "a\x60b", 'a"b', "", "x" * 33]`;
  - `test_a_proto_column_is_data` (`__proto__` present returns its values);
  - `test_an_absent_column_gives_none`;
  - `test_a_misaligned_mask_warns_and_gives_none` (exactly one warning containing `could not be restricted`);
  - `test_a_frame_and_a_cds_dict_give_the_same_values`;
  - `test_rows_with_a_missing_y_are_kept`;
  - `test_a_date_series_reads_in_milliseconds` (datetime64[ms] Series with NaT gives `[978393600000.0, nan]`; never TypeError);
  - `test_a_string_column_is_a_list`.
- `TestTheBinHelperOverADomain` (**red**: unexpected keyword `bin_values`):
  - `test_labels_come_from_the_domain`;
  - `test_one_bin_per_bin_value`;
  - `test_has_missing_comes_from_the_domain_only`;
  - `test_a_value_outside_the_domain_is_none` (a value below the domain minimum under closed ends is None, not the first label);
  - `test_without_bin_values_the_domain_is_binned` (HEAD's labels; NaN gives None).
- `TestApplyColorvarOverADomain` (**red**):
  - `test_rows_outside_the_domain_are_none_and_not_a_factor`;
  - `test_the_missing_entry_follows_the_domain`;
  - `test_an_empty_domain_adds_no_key_and_raises_nothing`;
  - `test_an_all_missing_domain_keys_missing_only`;
  - `test_nan_color_is_colormissing`.
- `TestTheDomainIsReset` (**red**: no attribute):
  - `test_a_later_layer_is_not_restricted[saved|served]`: layer 1 `if foreign == 1` colorvar(price), layer 2 colorvar(price). Layer 2's bar is (3799, 11385).
  - `test_the_attribute_is_none_after_the_render[saved|served]`.
  - `test_the_attribute_is_none_after_a_layer_raises[saved|served]`: monkeypatch the mapper's `map_scatter` to raise `RuntimeError`, then assert `colorvar_domain is None` after `pytest.raises`.
- `TestTheColourFieldName` (**red**):
  - `test_the_field_helper_takes_the_first_free_name`;
  - `test_a_derived_field_is_under_the_reserved_prefix[colordiscrete|colorlevels(3)|string]`;
  - `test_a_user_variable_named_like_the_old_field_is_untouched[saved|served-after-move]`: `_DF` plus `_cvar_price_bin` = 0..9. The user column is unchanged, layer 2's mapper is a LinearColorMapper (0, 9), and after the served dropdown move to Foreign layer 1's drawn colour values lie within its factors.
  - `test_two_colorvar_layers_on_one_graph_keep_their_own_bins[saved|served]`;
  - `test_two_linked_graphs_keep_their_own_bins[saved|served]`: two fields differ, each field's non-None values lie within its own factors, and both columns survive a move with one value per row.
- `TestAValueLabelCalledMissing::test_a_label_is_a_level_and_missing_is_missing[saved|served]` (**red**). Value label `3 → "__missing__"`, rep row 0 missing:
  - factors are `["__missing__", "four", "5"]`, with no duplicate;
  - the palette length equals the factor count;
  - the missing row's value is None;
  - `nan_color == "#808080"`;
  - the Legend's labels end with "(missing)".
- `TestOneKeyPerLayer::test_rconnected_draws_one_key[saved|served]` (**red**: 2). `colour_keys(fig) == 1`, and both ends' Scatter renderers are colour-mapped.
- `TestTheServedRedrawKeepsTheBuildDomain::test_a_redrawn_copy_keeps_the_build_bins` (**red**): rconnected colorlevels(3) under a price range filter, fired to (4500, 11385). Every column named by any renderer's `colour_field` holds, on every source in the document, values within the union of the build's factors or None.
- `test_colour_keys_reads_both_modes` (in `TestTheColourBinsHelpers`, written in 07-08): `filter_truth_check.colour_keys` on a written colorvar spec equals the bars read from `_standalone` and `_served`. Guard.

`test/test_saved_filter_layers.py::TestTheColourKeyHoldsThroughAMove`, saved through node and served through `_fire`, with the range move to (4500, 11385). Cases:
- `{scatter, connected, rconnected, dot}` x `colorlevels(3)`, unlinked;
- `scatter` x `{colorlevels(3), colordiscrete on rep, colorcuts(4500 9000)}` x `{unlinked, linked graph if foreign == 1, linked by(foreign), unlinked by(foreign)}`.

Tests:
- `test_every_colour_value_is_a_key_level[...]`: for every colour-mapped CategoricalColorMapper renderer, the drawn values lie within its factors or None. Guards: the saved key is fixed at base.
- `test_the_colour_bar_keeps_its_range[...]`: for continuous `colorvar(price)` across the four layouts, the ColorBar (low, high) after equals before. Guard.

**Cscript** `test/test_wp29_truth.cscript` block S07 (sysuse auto; dash pages from `_dash_serve_spec`; dash values through `filter_truth_check.colour_keys`):
- **CQV-01** (**red** saved): q_if_cont. Twoway's key texts are `4,000 … 14,000` and differ from the unqualified graph's. Dash's bar equals `summarize price if foreign==1` in both modes.
- **CQV-02** (**red** saved): q_if_disc. Twoway's non-gray in-region fill groups among the first `r(N)` markers number 3. Dash's factors are `levelsof rep78 if foreign==1` (3 4 5) in both modes.
- **CQV-03** (**red** saved): q_if_lv3. Dash's interior bounds, rounded to 0.1, equal twoway's key texts `6,828.7` and `9,909.3` in both modes.
- **CQV-04** (**red** both): `dash scatter mpg weight if foreign == 1, colorvar(price) name(c4a)` linked with `c4b`. The bar equals summarize.
- **CQV-05** (**red** both): `by(foreign)` colorlevels(4) linked.
  - Each panel's interior bounds round to the single-panel twoway key texts (`6,444.8 9,598.5 12,752`; `6,058.5 8,369 10,680`).
  - The by() graph's fill totals equal the panel sums minus swatches (live re-check of the per-panel rule).
- **CQV-06** (**red** both): `missing_y_lv2`, unlinked. Twoway `9,598.5`; dash's bound 9598.5 in both modes.
- **CQV-07** (**red** both): `missing_x_lv2`.
- **CQV-08** (**red** both): `missing_y_connected`.
- **CQV-09** (**red** both): `rconnected_key`. Twoway's "Price" count is 1; dash `keys == 1` in both modes.

**Mutation table:**

| break this | test that must die |
|---|---|
| register `self._row_ids_for(_pdf)` again | `TestTheRegisteredRowsAreTheViewsOwn`, `TestALinkedLayersOwnIfAcrossMoves`, QF-01 |
| compute the domain after `_linked_scatter_view` | `test_rows_with_a_missing_y_count[linked-*]` |
| drop the `finally` in `_make_figure` | `TestTheDomainIsReset::test_the_attribute_is_none_after_a_layer_raises[saved]` |
| emit `list(g_df[var])` in the domain | `test_a_date_series_reads_in_milliseconds`, `TestADateColorvarUnderALayersIf[served]` |
| pass the filtered `_fr` domain in `_redraw` | `TestTheServedRedrawKeepsTheBuildDomain` |
| name the field `_cvar_<var>_bin` | `TestTheColourFieldName`, `test_internal_column_names.py` guard |
| clamp an out-of-domain value into an end bin | `test_a_value_outside_the_domain_is_none` |
| put `"__missing__"` back as a factor | `TestAValueLabelCalledMissing` |
| add the key on rconnected's second end | `TestOneKeyPerLayer`, CQV-09 |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Linked qualified layer after one move | pytest + node (`TestEveryLayerFollowsAMove`) | none (saved oracle) | saved; served by `TestAFilterMoveAgrees` |
| Repeated moves and reset | pytest + node | none | saved |
| Saved after move equals served after move | pytest + node + `_fire` | none | yes |
| Registered ids invariant | pytest | none | saved (served has no registration) |
| Stata count after a move | `test_e2e_filters.cscript` QF-01, QF-02 | none (`count if`) | yes |
| Key range, levels and cuts from the layer's rows | pytest (`TestTheKeyIsDrawnFromTheLayersRows`) | colorvar_qualifier_truth.json | yes |
| Per-panel mapping, linked and unlinked | pytest | same | yes |
| Missing x/y rows count | pytest | same | yes |
| Date colorvar under a layer `if` | pytest | none | yes |
| Initial-draw parity with the colour profile | `test_mode_parity.py` CORPUS | none | yes |
| Domain, field, bins and apply units; reset; collisions; sentinel; one key; served redraw | pytest (`test_colorvar_forms.py`) | none | yes |
| Colours fixed through a move | pytest + node + `_fire` | none | yes |
| Live twoway against both pages | `test_wp29_truth.cscript` CQV-01..09 | none (live SVG + summarize) | yes |
| Help states the rules | pytest `test_help_claims_2.py`/`_7.py` stay green; grep of the new sentences | none | n/a |

**Acceptance criteria:**
- **AC-07.1** `python3 -m pytest test/test_saved_filter_layers.py test/test_per_plot_qualifier_linking.py test/test_mode_parity.py -q` passes, with the 18 P0.15 red ids green and no new skip.
- **AC-07.2** `test_e2e_filters.cscript` prints `QF-01 PASS` and `QF-02 PASS`, and its log has no `r(` error line after them.
- **AC-07.3** `python3 -m pytest test/test_colorvar_truth.py test/test_colorvar_forms.py test/test_date_range.py test/test_internal_column_names.py -q` passes with no skip. `grep -c '"__missing__"\|_cvar_' dash_render.py` prints 0: no quoted sentinel, and no old prefix in code or comments. `grep -n '__missing__' dash_render.py` shows only the swatch model name `f"{_DASH_SWATCH_PREFIX}__missing__"`.
- **AC-07.4** The S07 block prints `CQV-01 PASS` … `CQV-09 PASS` under `WP29_ONLY=S07`, and `CV-01 PASS` still prints under `GAPS2_ONLY=S16`.
- **AC-07.5** BUGS.md holds the P0.15 and P0.16 entries closed in place with `(WP-29, P0.15)` / `(WP-29, P0.16)`; both markers are replaced; both `WP29_OPEN` keys are gone; `test_tracking_documents.py` is green.
- **AC-07.6** Two commits on `wp29-s07`, subjects ending `(WP-29 P0.15)` and `(WP-29 P0.16)`, each made after one green full suite. Neither message matches `claude|anthropic`.

## Tasks

**Commit boundary.**
- Commit 1 (P0.15) holds 07-01 to 07-04, subject `Keep a linked layer's own if inside its panel after a saved filter move (WP-29 P0.15)`.
- Commit 2 (P0.16) holds 07-05 to 07-16, subject `Draw the colour key from the rows each colorvar layer draws (WP-29 P0.16)`.

Both are made on `wp29-s07` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s07`. Each body opens with its saved failure text and carries `Regression:` lines (`-- failed at <sha> with <text>`; the sha is `<scratch>/batch-1-base.txt` for P0.15 and commit 1's sha for P0.16), `Flipped:` lines, `Fixture:` (P0.16 only) and `BUGS.md: "<title>" (closed)`.

Every Stata run is `dash_nobrowser=1 scripts/stata_slot.sh <scratch> <file>.do` (rule 10), and a cscript runs through the two-line driver of "Stata truth". `<repo>` is the worktree, and `<scratch>` is the section's scratch directory. No AI reference appears anywhere.

<task type="auto" id="07-01">
  <name>Write the failing P0.15 pytest cases</name>
  <files>test/test_saved_filter_layers.py, test/test_per_plot_qualifier_linking.py, test/test_mode_parity.py</files>
  <action><![CDATA[
In `test/test_saved_filter_layers.py`:
- Add the 18 `_CORPUS` entries of "TDD test stubs, P0.15" (9 types x 2 layouts), using `_case`, `_MOVES[1]` and `plot_for`.
- Add the classes `TestALinkedLayersOwnIfAcrossMoves` and `TestTheSavedPageAgreesWithTheServedApp`, exactly as the stubs specify. Import `_served_after_move` from `test_mode_parity` beside the existing imports.

In `test/test_per_plot_qualifier_linking.py`:
- Give `_render` an optional `df=None` argument that defaults to `_DF`.
- Add `TestTheRegisteredRowsAreTheViewsOwn` with its three tests. The expected ids are DERIVED from that file's `_DF` with pandas, never literals.

In `test/test_mode_parity.py`, append the two `MOVE_CORPUS` guard entries; do not touch `ALLOWED` or `_MUST_WARN`.

Touch no product file. Run the three files against the unmodified tree and save the complete failure output (node ids and assertion text) to `<scratch>/07-P0.15-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_filter_layers.py test/test_per_plot_qualifier_linking.py test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "linked or Registered or AcrossMoves or AgreesWithTheServed" 2>&1 | tail -25` fails exactly these and nothing else:
- the 10 `test_the_page_draws_the_kept_rows` ids for scatter, connected, dot, rspike and rconnected (each assertion shows the panel drawing `[1, 3, 4, 6, 7, 9]`-sized rows against the oracle);
- 2 `TestALinkedLayersOwnIfAcrossMoves`;
- 2 `TestTheSavedPageAgreesWithTheServedApp`;
- `test_every_registered_view_names_exactly_its_true_rows[linked by() with a layer if]` and `[linked graph if with a layer if]`;
- `test_a_linked_graph_if_and_a_layer_if_register_their_intersection` (registered `[0, 2, 3, 6]`, wanted `[3, 6]`);
- `test_a_linked_by_panel_layer_registers_only_its_panels_rows`.

That is 18 failed. Every new `TestAFilterMoveAgrees` id passes, and `<scratch>/07-P0.15-failure.txt` exists.]]></verify>
  <done>Every P0.15 pytest regression test existed and failed for its recorded reason on the batch-1 base, the guards passed, and nothing was committed.</done>
</task>

<task type="auto" id="07-02">
  <name>Write the failing P0.15 Stata cases</name>
  <files>test/filter_truth_check.py, test/test_e2e_filters.cscript, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
Add `layer_rows(spec_path, data_path, moves)` to `test/filter_truth_check.py` as TR-07.10 says:
- import `test_mode_parity as tp` inside the function;
- the saved side mirrors `saved()` but reads the given files;
- the served side mirrors `served()`, taking the filter order from `json.load(open(spec_path))["build_options"]["filters"]`;
- count rows with `tp._layout_tree` profiles, `[[g["rows"] for g in f["glyphs"] if g["visible"]] for f in figs]`;
- give it a docstring naming QF-01/QF-02.

Add `TestTheTruthCheckHelpers::test_layer_rows_reads_both_modes` to `test/test_saved_filter_layers.py`.

In `test/test_e2e_filters.cscript`, before the `// Cleanup` block:
- Add QF-01 and QF-02 inside `preserve`/`restore`, with `sysuse auto, clear`, `dash clear`, the `dash` commands of the stubs, and `tempfile` paths for `_dash_serve_spec`.
- Compute the truth with `quietly count if ...` into globals `qf_want0` and `qf_want1`.
- In a `python:` block, `import filter_truth_check as ftc` (the runner's cwd is test/), call `ftc.layer_rows(Macro.getGlobal(...), ..., [(0, (5000.0, 15906.0))])`, `print` both modes' counts, and `ftc.put("qf_01", int(ok))`. After `end`: `assert "${qf_01}" == "1"` and `display "QF-01 PASS: ..."`. QF-02 likewise.
- Add `QF-01 and QF-02` to the header's `Tests:` comment.

Run the script through the driver against the unmodified dash_render.py and append the log's QF lines (the printed counts and the `assertion is false` r(9)) to `<scratch>/07-P0.15-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_saved_filter_layers.py -q -n0 -p no:cacheprovider -k TruthCheckHelpers` passes.
- The driver run's log `<scratch>/run_test_e2e_filters.log` shows the QF-01 python print with saved `23` and `23` and served `14` and `9`, followed by `assertion is false` and `r(9);`.
- `grep -c "QF-0[12]" test/test_e2e_filters.cscript` prints at least 4.]]></verify>
  <done>The Stata-certified P0.15 cases existed, used Stata's own counts, and failed on the saved page at the base with 23 and 23 where Stata counts 14 and 9.</done>
</task>

<task type="auto" id="07-03">
  <name>Register the intersected rows of each view</name>
  <files>dash_render.py, test/function_test_map.py, dash.sthlp</files>
  <action><![CDATA[
1. Run `npx gitnexus analyze` if the index lacks this repository, then `gitnexus_impact({target: "_make_figure_body", direction: "upstream"})`. Report the HIGH result to the maintainer before editing, and record it in `<scratch>/07-impact.txt`.
2. Apply TR-07.1 at dash_render.py:26212-26213 (`DashRenderer._make_figure_body`, the per-plot qualifier block), with the comment it describes. Change nothing else.
3. Repoint `function_test_map.py`'s `DashRenderer._register_view_filter` entry as TR-07.11 says.
4. In dash.sthlp's "What a filter move redraws" paragraph (1394-1409), after "-- each layer from its own rows among them --", add the sentence: `A plot's own {cmd:if} or {cmd:in} inside a linked {cmd:by()} panel, or inside a linked graph with its own {cmd:if} or {cmd:in}, keeps to that panel's or graph's observations after every move, in both.`
5. Run the changed tests, then the e2e cscript through the driver.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_saved_filter_layers.py test/test_per_plot_qualifier_linking.py test/test_mode_parity.py test/test_function_test_map.py -q 2>&1 | tail -3` reports 0 failed.
- `<scratch>/run_test_e2e_filters.log` contains `QF-01 PASS`, `QF-02 PASS` and `All filter widget E2E tests PASSED.`
- `git diff -U0 -- dash_render.py | grep -c '^@@'` prints 1.]]></verify>
  <done>The saved page registered each qualified linked view with exactly the rows its mask keeps, and every P0.15 test and both QF cases passed in both modes.</done>
</task>

<task type="auto" id="07-04">
  <name>Close P0.15 and make commit one</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
1. In BUGS.md, find the open entry whose title is `WP29_OPEN["P0.15"]` (test_tracking_documents.py). Close it in place:
   - Change `- [ ]` to `- [x]`.
   - Set File Names and Line Numbers to `dash_render.py: DashRenderer._make_figure_body (the per-plot qualifier registration)`.
   - Rewrite its Resolution to: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.15). DashRenderer._make_figure_body registers a layer's own if/in view with the source row identities its mask keeps -- the layer's qualifier AND the linked by() panel's or linked graph's view -- so _FILTER_JS rebuilds it inside its panel or graph after every move, a second move and a reset; the served app already recomputed each layer from its own frame. Pinned by test/test_per_plot_qualifier_linking.py::TestTheRegisteredRowsAreTheViewsOwn::test_every_registered_view_names_exactly_its_true_rows, test/test_saved_filter_layers.py::TestALinkedLayersOwnIfAcrossMoves::test_every_step_draws_the_kept_rows, test/test_saved_filter_layers.py::TestTheSavedPageAgreesWithTheServedApp::test_a_qualified_layer_in_a_linked_graph, test/test_e2e_filters.cscript QF-01.`
   - Keep the title free of `"`.
2. In CHANGELOG.md, replace the marker `<!-- WP-29 P0.15 -->` in the `**WP-29 (drop-in P0, 30sep2026)**` group of `### Results that change` with one line ending `(WP-29, P0.15)`. The line names the command (`dash (scatter mpg weight) (scatter mpg weight if price>6000), by(foreign)` linked with a second graph, price range moved to 5,000-15,906), the old value (23 observations in each panel's second plot; quote `<scratch>/07-P0.15-failure.txt`) and the new (14 and 9, as count gives and the served app draws). Write nothing elsewhere.
3. Delete the `"P0.15"` key line from `WP29_OPEN`.
4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0`, then the full suite once (`python3 -m pytest test/ -q`), then `gitnexus_detect_changes()`. Read the log; never relaunch.
5. Stage only the changed paths: never CLAUDE.md, .gitignore, scratch or `*.html`.
6. Grep the message for `claude|anthropic` before and after committing.
7. Commit with the subject `Keep a linked layer's own if inside its panel after a saved filter move (WP-29 P0.15)` and a body that opens with `<scratch>/07-P0.15-failure.txt` and carries the measured defect, the `Regression:` lines (one per red test class plus QF-01/QF-02, each `-- failed at <batch-1 base sha> with <text>`) and `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[- The full suite's tail reports 0 failed and no new skip.
- `grep -c '<!-- WP-29 P0.15 -->' CHANGELOG.md` prints 0, and `grep -c '(WP-29, P0.15)' CHANGELOG.md BUGS.md` prints at least 2.
- `git log -1 --format=%s | grep -c '(WP-29 P0.15)'` prints 1, and `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0.
- `git show --stat HEAD` lists only this cycle's files.]]></verify>
  <done>P0.15 was closed in BUGS.md naming its tests, its CHANGELOG marker was replaced with the measured old and new counts, its allowance key was gone, and one green commit carried the cycle.</done>
</task>

<task type="auto" id="07-05">
  <name>Extract the colorvar qualifier truth</name>
  <files>scripts/extract_colorvar_qualifier_truth.do, test/fixtures/colorvar_qualifier_truth.json</files>
  <action><![CDATA[
Create `scripts/extract_colorvar_qualifier_truth.do` to "Stata truth"'s specification:
- the frame copied from `scripts/extract_colorvar_truth.do`, with the `ZQ_` globals, the `DASH_REPO` override and the `c(python_exec)` exit 601;
- every probe of the table, each exported with `graph export ... .svg` and recorded;
- `summarize` r(min)/r(max) captured into locals per qualified probe and written to the records file;
- the rc probes run under `capture noisily` and a log;
- `_data.auto`;
- the `_meta` stamp with `git rev-parse` captured by `quietly shell` into a file;
- both self-checks, written as `"held"` or `"failed: <why>"`.

The python block reads the SVGs through `scripts/svg_truth.py` (`svg_document`, `svg_texts`), never calls Stata, never uses `shell=True`, and writes the JSON with `sort_keys=True, indent=1`.

Run it once with `DASH_REPO=<worktree> dash_nobrowser=1 scripts/stata_slot.sh <scratch> <worktree>/scripts/extract_colorvar_qualifier_truth.do` and read `<scratch>/extract_colorvar_qualifier_truth.log`. `git add -f test/fixtures/colorvar_qualifier_truth.json`. Never patch the fixture by hand: a wrong value is fixed in the script and the script rerun (R5).
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/colorvar_qualifier_truth.json'));p=d['probes'];m=d['_meta'];print(p['q_if_cont']['summ_min'],p['q_if_cont']['summ_max'],[t for t in p['q_if_lv3']['key_texts'] if t in ('6,828.7','9,909.3')],'9,598.5' in p['missing_y_lv2']['key_texts'],'9,598.5' in p['missing_x_lv2']['key_texts'],'9,598.5' in p['missing_y_connected']['key_texts'],sorted(p['by_lv4']['fill_counts'].values()),p['rconnected_key']['key_title_count'],p['multi_colorvar']['rc'],p['empty_layer']['rc'],p['all_missing']['rc'],m['qualified_order_selfcheck'],m['by_panel_selfcheck'],all(k in m for k in ('stata_version','born_date','dash_commit','extracted')))"` prints `3748.0 12990.0 ['6,828.7', '9,909.3'] True True True [6, 6, 8, 54] 1 198 3001 0 held held True`. `git ls-files test/fixtures/colorvar_qualifier_truth.json` prints the path.]]></verify>
  <done>A committed-ready fixture held twoway's own keys, fills, counts and refusals for every qualifier, by() and missing-row probe, with its provenance and both self-checks held.</done>
</task>

<task type="auto" id="07-06">
  <name>Write the failing key domain tests</name>
  <files>test/test_colorvar_truth.py, test/test_date_range.py, test/test_mode_parity.py</files>
  <action><![CDATA[
- **`test/test_colorvar_truth.py`:** add `_qtruth()`, which `pytest.fail`s naming task 07-05 if `colorvar_qualifier_truth.json` is absent, plus a frame builder from `_data.auto` (y2/x2 as Stata built them) and `TestTheKeyIsDrawnFromTheLayersRows` with every test of "TDD test stubs, P0.16". It renders through `test_mode_parity._standalone`/`_served` with `monkeypatch.setattr(tp, "_DF", frame)`. Read factors and bars from the colour-mapped renderers' `glyph.fill_color["transform"]` and the ColorBar models directly; `test/colour_bins.py` arrives in 07-07, after which 07-12 routes these reads through it.
- **`test/test_date_range.py`:** add `TestADateColorvarUnderALayersIf`.
- **`test/test_mode_parity.py`:** add TR-07.9's profile additions and the five CORPUS cases. Use `plot_for(..., if_expr=...)` and pass no variable labels the assertions depend on (A7).

Run the three files against the tree commit 1 left. Save the failures to `<scratch>/07-P0.16-failure.txt`, keeping the old values the CHANGELOG quotes: the saved bar (3291, 15906), factors 1..5, cut 8895.5. Do not commit.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_truth.py -q -n0 -p no:cacheprovider -k TheKeyIsDrawn 2>&1 | tail -20` fails exactly the ids the stubs mark red: saved (3291.0, 15906.0) for the layer if; both modes for the linked cases; both modes for unlinked missing x/y and connected. The guards pass.
- `python3 -m pytest test/test_date_range.py -q -n0 -k ADateColorvar` fails only the two `saved` ids.
- `python3 -m pytest test/test_mode_parity.py -q -k "colorvar"` fails only the three unlinked layer-if CORPUS cases, and every pre-existing colorvar case passes with the new profile.]]></verify>
  <done>Every fixture- and parity-backed P0.16 regression test existed and failed for its recorded reason on commit 1's tree, and the existing colorvar parity cases still agreed under the stronger profile.</done>
</task>

<task type="auto" id="07-07">
  <name>Write the failing domain unit tests</name>
  <files>test/colour_bins.py, test/test_colorvar_forms.py, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
Create `test/colour_bins.py`, a module docstring naming WP-29 S07, with:
- `colour_renderers(model)`: GlyphRenderers under a figure or Document whose `glyph.fill_color` is a field spec with a transform, swatches excluded via `dr._dash_is_swatch`;
- `colour_field(renderer)`;
- `colour_mapper(renderer)`;
- `colour_values(renderer)`;
- `drawn_colour_values(renderer)`, through a BooleanFilter or IndexFilter view;
- `colour_bars(model)`, a list of (low, high);
- `colour_keys(model)`, counting ColorBars plus Legends named `dr._COLORVAR_LEGEND_NAME`;
- `interval_bounds(labels)`: strip `,`, split on U+2013, read U+2264 and `>` as open ends, giving `(lo, hi)` floats or None;
- `figures_by_title(model)`.

Each handles both `dict` and object specs, as `test_help_claims_7._colour_mapped_one` does.

In `test/test_colorvar_forms.py` add every P0.16 class of "TDD test stubs" that lives there, including `TestTheColourBinsHelpers`, with a small `_served_ns(spec)` helper that builds the app with `ServerAppBuilder` and execs it into a namespace (the `test_date_range._served` pattern), so the tests can read `_DASH_MAPPER`.

In `test/test_saved_filter_layers.py` add `TestTheColourKeyHoldsThroughAMove`.

Run the two test files. Append their failures to `<scratch>/07-P0.16-failure.txt`: the AttributeError for `_dash_colorvar_domain`, the r2/r3/r4 measurements, rconnected's 2 keys, and the redraw labels `4749–6961`. Do not commit.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_forms.py -q -n0 -p no:cacheprovider -k "Domain or BinHelperOverADomain or OverADomain or Reset or FieldName or CalledMissing or OneKeyPerLayer or ServedRedraw" 2>&1 | tail -30` shows every listed red id failing, and `TestTheColourBinsHelpers` passing.
- `python3 -m pytest test/test_saved_filter_layers.py -q -k ColourKeyHolds` passes (guards).
- The failure file names r2's overwritten column and served values `['1.0', '3.0', '5.0', '7.0', '9.0']`.]]></verify>
  <done>Every unit, collision, sentinel, reset and redraw regression test of P0.16 existed and failed for its recorded reason, and the after-move colour guards passed.</done>
</task>

<task type="auto" id="07-08">
  <name>Write the failing CQV truth block</name>
  <files>test/test_wp29_truth.cscript, test/filter_truth_check.py, test/test_colorvar_forms.py</files>
  <action><![CDATA[
Add `colour_keys(spec_path, data_path)` to `test/filter_truth_check.py` (TR-07.10) and its guard test `TestTheColourBinsHelpers::test_colour_keys_reads_both_modes`.

In `test/test_wp29_truth.cscript`:
- Above the line `* ==== append new blocks above this line ====`, after every lower-numbered section's block (R1), append the block `* ==== S07 P0.16: colorvar key from the layer's rows ====` gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S07") {`, with `display` of `S07 start`/`S07 end` and `* ==== end S07 ====`.
- First read the scaffold's top to learn its tally helper names and its work-directory local (S01 copied test_gaps2_truth.cscript's `_gt_expect`/`_gt_done` frame), and use exactly those.
- Each CQV case:
  1. exports twoway live with `cert_svg_export`;
  2. computes `summarize`/`levelsof` into globals;
  3. builds the dash dashboard with `dash ... name()` and `_dash_serve_spec, specpath() datapath()`;
  4. in a `python:` block, reads `ftc.colour_keys` and `svg_truth.svg_texts`/`svg_document`, and sets globals `cqv_ok`/`cqv_why` (numbers only);
  5. calls the scaffold's expect/done helpers.
- No case `exit`s on failure. Update the header's block list.

Run the block with the driver under `WP29_ONLY=S07` against the unmodified dash_render.py, and append the FAIL lines to `<scratch>/07-P0.16-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_forms.py -q -k colour_keys_reads_both_modes` passes.
- `grep -c "CQV-0[1-9] FAIL" <scratch>/run_test_wp29_truth.log` prints 9, and `grep -c "W29-01 PASS" <scratch>/run_test_wp29_truth.log` prints 0 (the block ran alone).
- `grep -n "SKIP" <scratch>/run_test_wp29_truth.log` prints nothing.]]></verify>
  <done>The live twoway certification of the colour key existed as section 07's block of the WP-29 truth script and failed all nine cases at commit 1's tree.</done>
</task>

<task type="auto" id="07-09">
  <name>Add the domain, field and bin helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
1. Run `gitnexus_impact` upstream on `_dash_colorvar_bins` and append the result to `<scratch>/07-impact.txt`.
2. Add `_DASH_CVAR_PREFIX` (TR-07.2), `_dash_colorvar_domain` (TR-07.3) and `_dash_colorvar_field` (TR-07.4) with full docstrings.
3. Rewrite `_dash_colorvar_bins` as TR-07.5 says. Keep the nested function names and the duplicate-label fallback.
4. Add `"_DASH_CVAR_PREFIX"` to the constants tuple after `"_DASH_JITTER_Y"` (:28383), and `"_dash_colorvar_domain", "_dash_colorvar_field"` to the functions tuple after `"_dash_colorvar_bins"` (:28796).
5. Add or repoint the `function_test_map.py` entries of TR-07.11, in alphabetical place.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_forms.py -q -n0 -k "ColourDomain or BinHelperOverADomain or first_free_name"` passes.
- `python3 -m pytest test/test_function_test_map.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q` passes.]]></verify>
  <done>The domain, field-name and domain-aware bin helpers existed in both renderers' copy, warned on a misaligned mask, and passed their unit tests.</done>
</task>

<task type="auto" id="07-10">
  <name>Map each colorvar layer from its domain</name>
  <files>dash_render.py</files>
  <action><![CDATA[
1. Run `gitnexus_impact` upstream on `_apply_colorvar`, `map_scatter` and `map_rconnected`, and record the results.
2. Apply TR-07.6:
   - `GlyphMapper.__init__` declares `colorvar_domain`.
   - `_apply_colorvar` gains `add_key=True` and every rule 1-12, with no remaining `"__missing__"` factor or binned value. The swatch model name stays as written.
   - `map_scatter` gains `colorvar_key=True`.
   - `map_rconnected` passes `colorvar_key=False` on its second end, with a comment citing twoway's one key (E-16.2).
3. Update the docstrings: `_apply_colorvar` states the domain, None and add_key rules.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_forms.py -q -n0 -k "OverADomain or CalledMissing or OneKeyPerLayer or FieldName"` passes, except the tests that need the wiring of 07-11 (`TestTheDomainIsReset`, the served after-move collision).
- `python3 -m pytest test/test_glyphs.py -q -k Colorvar` shows only the pins 07-13 flips failing.]]></verify>
  <done>Every colorvar layer was coloured from its domain with missing as None, a unique reserved field name and one key per plot.</done>
</task>

<task type="auto" id="07-11">
  <name>Hand each layer its domain in both modes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
1. Apply TR-07.7 in `DashRenderer._make_figure_body`, inserted after the per-plot block and before `# Snapshot renderer list`. Wrap `_make_figure`'s body in `try`/`finally`.
2. Apply TR-07.8 to the emitted `_dash_draw_layer`, `_dash_redraw_for` and the redraw registration in `ServerAppBuilder._generate_app_source`. The emitted dispatch lines are re-indented by exactly four spaces inside the new `try`, and nothing else in them changes.
3. Build one app with `ServerAppBuilder(sp, dp).build(ap)` and `python3 -m py_compile` it.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_colorvar_truth.py test/test_colorvar_forms.py test/test_date_range.py test/test_saved_filter_layers.py -q -k "TheKeyIsDrawn or Domain or Reset or FieldName or ServedRedraw or ADateColorvar or ColourKeyHolds"` passes.
- `python3 -m pytest test/test_mode_parity.py -q` passes, with `ALLOWED` unchanged (`git diff test/test_mode_parity.py | grep -c "^[-+].*ALLOWED"` prints 0).
- The CQV block under `WP29_ONLY=S07` prints `CQV-01 PASS` to `CQV-09 PASS`.]]></verify>
  <done>Both modes drew every colour key from the layer's qualified rows with missing x or y counted, kept the build's domain through served redraws, and reset the domain after every layer, figure and exception.</done>
</task>

<task type="auto" id="07-12">
  <name>Flip the first colour pins</name>
  <files>test/test_colorvar_forms.py, test/test_colorvar_truth.py, test/test_function_audit.py</files>
  <action><![CDATA[
Route every field-name read listed in E-16.9 for these three files through `colour_bins.colour_field`/`colour_values`:
- `test_colorvar_forms.py:62`, `:340`;
- `test_colorvar_truth.py:95`, `:162`, `:167`, plus 07-06's direct reads;
- `test_function_audit.py:302`, `:364` (now "no column under `dr._DASH_CVAR_PREFIX`"), `:372-373`, `:418-420`.

Replace every `"__missing__"` expectation with `None` in binned values, and drop it from factors:
- `test_colorvar_forms.py:92-94`, `:127-128`, `:203-210`, `:224`;
- `test_function_audit.py:330-331`, `:340-341`, `:395-396`.

Each flip carries a comment `WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar`. Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per changed assertion in `<scratch>/07-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_truth.py test/test_function_audit.py -q 2>&1 | tail -3` reports 0 failed and no new skip; `grep -c "_cvar_\|__missing__" test/test_colorvar_forms.py test/test_colorvar_truth.py test/test_function_audit.py` prints 0 for each file except mentions inside comments.]]></verify>
  <done>The first group of pins read colours through one helper and expected None for missing, each flip recorded.</done>
</task>

<task type="auto" id="07-13">
  <name>Flip the second colour pins</name>
  <files>test/test_glyphs.py, test/test_dropdown_values.py, test/test_help_claims_7.py</files>
  <action><![CDATA[
Flip the following, as E-16.9 lists them:
- `test_glyphs.py::TestApplyColorvarOptions::test_colordiscrete_derived_bin_column_created` (:3445-3454): the field starts with `dr._DASH_CVAR_PREFIX` and its values are `{"0", "1"}`;
- `:3470` and `:3498`: drop the sentinel filter;
- `test_colormissing_included_in_palette_for_discrete` (:3537-3555): becomes `mapper.nan_color == "#ff0000"`, with a "(missing)" Legend entry and `"__missing__" not in mapper.factors`;
- `test_dropdown_values.py:360-361`: the values through `colour_bins`, giving `{None, "a", "nan"}`;
- `test_help_claims_7.py::TestAStringColorvar::test_a_repeated_value_is_one_level` (:515-516): factors `["D", "F"]`, `str(mapper.nan_color).lower() == "#ff0000"`, and the labels still `["D", "F", "(missing)"]`.

Append the `Flipped:` lines to `<scratch>/07-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_glyphs.py test/test_dropdown_values.py test/test_help_claims_7.py -q 2>&1 | tail -3` reports 0 failed and no new skip.]]></verify>
  <done>The second group of pins expected the reserved field, nan_color for missing and no sentinel factor, each flip recorded.</done>
</task>

<task type="auto" id="07-14">
  <name>Flip the third colour pins</name>
  <files>test/test_server.py, test/test_internal_column_names.py, test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
- **`test_server.py:7487`:** replace the `colour_bins` parameter's column `"_cvar_foreign_bin"` with a sentinel `None` that the test resolves to the Scatter renderer's `colour_field`, keeping the rest of the test unchanged.
- **`test_internal_column_names.py`:**
  - add `"_DASH_CVAR_PREFIX"` to `test_every_column_constant_starts_with_the_prefix`'s list;
  - add `or v.startswith("_cvar_")` to `test_no_column_literal_escapes_the_prefix`'s condition, as a new guard;
  - keep `"__missing__"` in `_ALLOWED_DUNDER_PREFIXES`, because the swatch name's literal part still holds it.
- **`test_gaps2_truth.cscript` CV-01 (:778-783, the R1 exception):** replace the `_cvar_rep78_bin` lookup with a loop over the figures' Scatter GlyphRenderers. Take `_f = _rr.glyph.fill_color`, then `_fld = _f.get("field") if isinstance(_f, dict) else getattr(_f, "field", None)` and `_tr = _f.get("transform") if isinstance(_f, dict) else getattr(_f, "transform", None)`. If `_tr` is not None, `_bins = set(_rr.data_source.data[_fld])`. Missing is None, so the set still has three members.
- Run CV-01's block through the driver under `GAPS2_ONLY=S16`.
- Append `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_server.py test/test_internal_column_names.py -q -k "DerivedColumns or Internal or prefix"` passes.
- `<scratch>/run_test_gaps2_truth.log` contains `CV-01 PASS` and no `FAIL`.
- `git diff -U0 test/test_gaps2_truth.cscript | grep -c '^@@'` prints 1, inside CV-01.]]></verify>
  <done>The served snapshot test, the column-prefix guard and the S16 certification read the renamed colour field, and a literal `_cvar_` column name could no longer return unnoticed.</done>
</task>

<task type="auto" id="07-15">
  <name>Document which rows set the colours</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
In dash.sthlp's Mapping a Variable to Colour (2635-2713), insert a new `{pstd}` paragraph `{ul:Which observations set the colours.}` after the paragraph ending "drawn in {cmd:colormissing()}'s colour." and before "The colour key's own axis options". It states, in SMCL:
- The colours, the colour bar's range, the cuts of colorcuts() and colorlevels(), the levels of colordiscrete and a string variable's categories (dash's own; twoway is r(7)) come from the observations the plot draws, as twoway takes them: those its own if and in, the graph's if and in and, under by(), its panel select. An observation whose y or x is missing counts too.
- The example `dash (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)` spans 3,748 to 12,990.
- Under by() each panel colours its own observations as twoway does. dash draws each panel's key, where twoway draws none unless by(, clegend(on)) asks for the first panel's, and clegend() is named in the note.
- A filter move keeps the colours and key chosen at build, in both modes.
- rconnected draws one key.
- A plot whose if selects nothing draws no key (twoway stops with r(3001)), and one whose observations are all missing on the variable draws a "(missing)" entry where twoway draws the key's title alone.

Keep every existing sentence (test_help_claims_2.py pins `{cmd:colorvar()} takes a string variable` elsewhere).
  ]]></action>
  <verify><![CDATA[- `grep -c "Which observations set the colours" dash.sthlp` prints 1.
- `python3 -m pytest test/test_help_claims_2.py test/test_help_claims_7.py -q` passes.
- `grep -n "3,748 to 12,990" dash.sthlp` prints one line.]]></verify>
  <done>The help stated which observations set the colours, the by() and filter-move behaviour and the documented deviations.</done>
</task>

<task type="auto" id="07-16">
  <name>Close P0.16 and make commit two</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
1. Close in place the BUGS.md entry titled `WP29_OPEN["P0.16"]`:
   - Change `- [ ]` to `- [x]`.
   - Set File Names and Line Numbers to `dash_render.py: GlyphMapper._apply_colorvar, _dash_colorvar_bins, new _dash_colorvar_domain and _dash_colorvar_field, GlyphMapper.map_scatter, GlyphMapper.map_rconnected, DashRenderer._make_figure, DashRenderer._make_figure_body, the served _dash_draw_layer and _dash_redraw_for`.
   - Write the Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.16). The colour bar, colorcuts()/colorlevels() cuts, colordiscrete levels, string categories and the (missing) entry are computed from the layer's colour rows -- its graph's and its own if/in and its by() panel, rows with a missing x or y included -- in both renderers (saved from the layer's view before the missing-x/y mask, served from the layer frame before dropna; a served redraw keeps the build's rows); missing is None with nan_color, never a sentinel; each layer's bins are a column of its own under the reserved __dash_cvar prefix; rconnected draws one key. Pinned by test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows::test_a_layers_own_if, test/test_colorvar_forms.py::TestTheColourDomain::test_rows_with_a_missing_y_are_kept, test/test_colorvar_forms.py::TestTheColourFieldName::test_a_user_variable_named_like_the_old_field_is_untouched, test/test_colorvar_forms.py::TestAValueLabelCalledMissing::test_a_label_is_a_level_and_missing_is_missing, test/test_wp29_truth.cscript CQV-01; fixture test/fixtures/colorvar_qualifier_truth.json. Residual, deferred (WP-29): by() draws a key per panel where twoway draws none unless by(, clegend(on)) (P1.15); two colorvar plots in one graph are drawn where twoway refuses them r(198); an empty colorvar plot draws no key where twoway stops r(3001); an all-missing one shows (missing) where twoway shows the title alone; a string colorvar is dash's own (twoway r(7)).`
2. Replace `<!-- WP-29 P0.16 -->` in the WP-29 group of `### Results that change` with one line ending `(WP-29, P0.16)`. It names `dash (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)` (saved bar 3,291-15,906, now 3,748-12,990 in both modes; colordiscrete on rep78 there 1-5, now 3-5); a linked graph with its own if and each linked by() panel (the whole dataset, now their own observations); `scatter y2 weight, colorvar(price) colorlevels(2)` with y2 missing on the 15,906 car (cut 8,895.5, now 9,598.5, as twoway); rconnected (two keys, now one); and the colour column now under the reserved prefix. Take the old values from `<scratch>/07-P0.16-failure.txt`.
3. Delete the `"P0.16"` key from `WP29_OPEN`.
4. Run, in order:
   - `python3 -m pytest test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -n0`;
   - the full suite once (`python3 -m pytest test/ -q`); a pin it exposes that 07-12 to 07-14 missed is flipped in that task's files first, with its `Flipped:` line;
   - the S07 block (`WP29_ONLY=S07`), `test_e2e_filters.cscript` and the S16 block (`GAPS2_ONLY=S16`), each through the driver;
   - `gitnexus_detect_changes()`.
5. Grep the message for `claude|anthropic` before and after.
6. Commit with the subject `Draw the colour key from the rows each colorvar layer draws (WP-29 P0.16)`. The body opens with `<scratch>/07-P0.16-failure.txt` and carries the `Regression:` lines (`-- failed at <commit 1 sha> with <text>`), the `Flipped:` lines from `<scratch>/07-flips.txt`, `Fixture: test/fixtures/colorvar_qualifier_truth.json (scripts/extract_colorvar_qualifier_truth.do)` and `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[- The full suite's tail reports 0 failed and no new skip.
- The S07 log has 9 `CQV-0[1-9] PASS` and 0 `FAIL`, the e2e log ends `All filter widget E2E tests PASSED.`, and the S16 log has `CV-01 PASS`.
- `grep -c '<!-- WP-29 P0.16 -->' CHANGELOG.md` prints 0, and `grep -c '(WP-29, P0.16)' CHANGELOG.md BUGS.md` prints at least 2.
- `git log -1 --format=%s | grep -c '(WP-29 P0.16)'` prints 1, `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0, and `git show --stat HEAD` includes `test/fixtures/colorvar_qualifier_truth.json`.]]></verify>
  <done>P0.16 was closed in BUGS.md naming its tests, fixture and residuals, its CHANGELOG marker carried the measured old and new values, and one green commit on wp29-s07 carried the cycle.</done>
</task>

## Section completion criteria

- **P0.15.** After any move, a second move and a reset, a qualified layer in a linked `by()` panel or a linked qualified graph draws its own rows on the saved page. Every `_view_filters` entry obeys the row-id invariant. QF-01 and QF-02 match Stata's `count` in both modes.
- **P0.16.** In both modes, every colorvar key is drawn from the layer's colour rows, missing x or y included: unlinked, linked, `by()` and dates. A filter move or a served redraw never re-bins it. Missing is `None` with `nan_color`. Derived columns are `__dash_cvar<k>_<var>`, unique per layer. `rconnected` draws one key. CQV-01..09 pass against live twoway.
- **Commits.** Two commits on `wp29-s07` with subjects `(WP-29 P0.15)` and `(WP-29 P0.16)`, each after one green full suite, with no test-only commit. Both BUGS.md entries are closed in place, both markers are replaced, and both `WP29_OPEN` keys are deleted.
- **Records.** Every flip is recorded. `ALLOWED` and `_MUST_WARN` are untouched. No new `.cscript`, runner or hygiene-pin edit is made. The fixture is committed with its `_meta` stamp.

## Notes

- **Merge rules.**
  - **R1:** QF cases go into `test_e2e_filters.cscript` as one contiguous run at its end (S07 is that script's only batch-1 user). The CQV block goes into `test_wp29_truth.cscript` in section order. **R1 exception:** S07 edits `test_gaps2_truth.cscript` at CV-01 only (four lines at :778-783), because the binding rename removes the column CV-01 looks up by name. S06's AL-19 edit is elsewhere in that script and S06 merges first, so the merger applies S07's hunk after it.
  - **R2:** `_DASH_CVAR_PREFIX` goes after `"_DASH_JITTER_Y"`, and the two functions after `"_dash_colorvar_bins"`, as the R2 table's S07 row says (extended by the constant and `_dash_colorvar_field`). `function_test_map.py` keys go in alphabetical place.
  - **R3:** this section owns the dash.sthlp paragraphs "What a filter move redraws" (one added sentence) and the new "Which observations set the colours". S05 merges later and rewrites the first paragraph's histogram sentence if it must; it keeps this sentence.
  - **R5:** a new fixture, `git add -f`, never hand-patched.
  - **R6:** CORPUS appends and profile additions only.
  - **R7:** every flip has a `Flipped:` line.
  - **R8:** `_make_figure_body` is expected HIGH; report before editing.
- **Files outside the manifest list (amendment 13):** `test/colour_bins.py` (new), `test/test_function_audit.py`, `test/test_glyphs.py`, `test/test_dropdown_values.py`, `test/test_help_claims_7.py`, `test/test_server.py`, `test/test_internal_column_names.py` and `test/test_gaps2_truth.cscript` (CV-01). `test/test_fixtures_are_committed.py` needs no edit: it finds the fixture by the name `test_colorvar_truth.py` reads.
- **Traps.**
  - `test_per_plot_qualifier_linking.py` and `test_mode_parity.py` each define their own `_DF`. Derive expected ids from the frame the test renders.
  - `_view_mask` warns and returns None on a misaligned view, and the domain helper does the same. Neither may silently restrict to the wrong rows.
  - A served `g_df` date column is datetime64. Never `list()` it before `_dash_float_values`.
  - The emitted app is text: after 07-11, build one app and `py_compile` it before running tests.
  - The served name guards do not walk the module-level `__main__` block (index R2), and `_dash_colorvar_domain` is only read inside `make_document`, so the existing guard covers it.
  - Swatch renderers are excluded from `colour_renderers` through `dr._dash_is_swatch`.
- **Contracts for later sections.**
  - **S12:** `self._view_filters` entries satisfy "ids are the source's row ids the filter keeps". Its stale rule may rely on this.
  - **S14:** a colorvar layer's colour rows (its qualified rows, including those with a missing x or y) are rows the colour key reads. If S14 narrows a saved source, it must keep the colorvar column on those rows, or `TestTheKeyIsDrawnFromTheLayersRows::test_rows_with_a_missing_y_count[linked-*]` goes red.
- **python_exec hazard.** Concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then prints SKIP and exits 222, and a SKIP is not a pass.
- **Line numbers** are `7421d3d`'s. S01, S09, S03, S02, S04 and S06 merge before this section in batch 1 and shift them. Locate by symbol.

### Notes for the closeout (A5; S15 writes these, S07 does not)

- **REMAINING.md 06-06:** mark "Register the INTERSECTED row set" and "re-check `_apply_colorvar`" done, citing commit 1 (P0.15) and commit 2 (P0.16).
- **DROPIN-REMAINING.md:** annotate P0.15 (REM-06-06-C7) and P0.16 (REM-06-06-C8b, REM-06-06-C8b-link) with their commits.
- **New residual items to file (measured, StataNow 19.5):**
  - **Two colorvar layers in one graph.** twoway refuses them with `multiple contour, patch, or colorvar plots not allowed`, r(198), and dash draws them. Suggested P1: a refusal in `dash.ado` with a `test_twoway_option_parity.cscript` case.
  - **by() key presence (P1.15).** twoway draws no key under `by()` unless `by(, clegend(on))`, and then one key showing the first panel's mapping (fixture `by_clegend_*`). dash draws one per panel and names `clegend(on)` in its note.
  - **Empty colorvar layer:** twoway r(3001) from `_calc_levels()`; dash draws no key.
  - **All-missing layer:** twoway's key shows the title only; dash shows "(missing)".
- **AGENTS.md invariants (S15.4):**
  - "a registered view's ids are exactly the source's row ids its filter keeps" (`TestTheRegisteredRowsAreTheViewsOwn`);
  - "a colour key is drawn from the layer's colour rows, fixed at build; derived colour columns are `__dash_cvar<k>_<var>` and missing is None" (`TestTheKeyIsDrawnFromTheLayersRows`, `TestTheColourFieldName`).
