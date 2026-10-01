# Section 12: Stale cue and served redraw widths

> Part of: WP-29 · P0: P0.17, P0.18 · Risk: yellow · Batch: 2, second wave (worktree cut after S10 and S11 land) · Depends on: 05, 07, 11 · Blocks: none (S15 closes the package) · Tasks: 20, 2 commits (P0.17, then P0.18) · Case prefixes: SCU, EW

## Critic amendment C1 (hidden S11 → S12 dependency) — binding; overrides any conflicting text below

S11 hands this section a requirement: the cue must mark lpolyci's NEW band source as well as its outline and line (section-11 Dependencies, "S12 (stale cue, u14) merges after this section", and Notes, "S12 (stale cue) merges after this section"). S11 also rewrites `map_lpoly`, whose empty branch 12-17 restyles. A worktree cut from `<scratch>/batch-2-base.txt` cannot see either. **Resolution: option (a), 12 ← 11.**
- **Sequencing.** S10, S11 and S13 start from `<scratch>/batch-2-base.txt` as before. After S10 and then S11 land on `wp29-p0` (merge order unchanged), the merger runs the R2 registry tests and the full suite once in the main checkout. Only when that run is green does the merger record `git rev-parse HEAD > <scratch>/batch-2-s12-base.txt` and cut `git worktree add /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s12 -b wp29-s12 wp29-p0`. S12 then runs alongside whatever of S13 remains. The merge order stays `S10, S11, S12, S13`.
- **Base sha.** Every "fails at" and "base" reference for P0.17 in this file means `<scratch>/batch-2-s12-base.txt`, not `<scratch>/batch-2-base.txt`. 12-01 checks the worktree is on that sha and holds S11's commits.
- **New test.** `TestTheCueAppearsOnAMove::test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked` (P0.17 stubs, red at the S12 base) moves, then moves back, and checks the band, outline and line of an lpolyci layer on S11's three-source structure. It also checks that an empty lpolyci, which has three empty sources, is never marked. A mutation row pins it.
- **map_lpoly.** 12-17 edits S11's landed text in the worktree. Nothing is re-applied by hand at merge time.
- **index.md must record it.** This file is the only one this amendment may edit, so the orchestrator applies these index.md changes before batch 2 starts:
  - the section table: S12's "Depends on" becomes `05, 07, 11`, and S11's "Blocks" gains `12`;
  - "Why the dependencies" gains: **12 ← 11:** u14's cue must mark lpolyci's band, outline and line sources, which u07b creates (u07b open question 5). 12-17 also restyles `map_lpoly`'s empty branch on u07a's text;
  - the batch diagram gains the 11 → 12 edge, and "Batch 2" says S12's worktree is cut after S10 and S11 land, from a green interim run, with its base in `<scratch>/batch-2-s12-base.txt`;
  - section-11's "Parallel batch" line is updated to match.

## Review amendments (design review of u14, "sound with amendments") — binding; they override any conflicting text below

Every amendment, missed site, missed test and truth dispute from the u14 review is applied in this file. Each is listed with where it lands.

1. **Weight rule.** The estimation sample is the one `GlyphMapper._layer_weights` fits from, not "a finite weight". A row with a zero or negative weight is outside it (Stata agrees, E-17.4: `regress mpg weight [aw=w]` gives N=9 with one `w=0` row among 10, and dropping that row leaves N=9 and b=-0.00701112). `_layer_weights`' acceptance decision is extracted into `GlyphMapper._layer_weight_column` (returns `(wtype, wexp, why)`) and its value decision into `GlyphMapper._layer_weight_values_state` (returns `"negative"`, `"nonint"` or None). The frozen tag carries `wrule`: `"positive"` (a row counts only when its weight is finite and > 0) or `"any"` (the build drew nothing because of a weight state, so any removed row with finite variables and a finite weight marks the layer). TR-12.4, TR-12.6, TR-12.10; tests `TestTheWeightColumn`, `TestTheWeightedSample` (12-03).
2. **JS finiteness.** The scan tests `typeof v === "number" && Number.isFinite(v)`, never `Number(v)` (`Number(null) === 0`; the snapshot holds NaN, ±inf and NaT as null). TR-12.10; `TestNoFalseCue::test_a_move_that_removes_only_rows_the_fit_never_used[y null]`.
3. **Empty member list.** `member_ids` is set when `rows is not None and len(rows) < len(self.df)`, the rule of `render()` step 3b (dash_render.py:28172-28174), so a fit whose own `if` selects nothing keeps `[]` and is never marked. TR-12.6; `TestNoFalseCue::test_an_empty_fit_is_never_marked`.
4. **Width family.** `_empty_fit_line` takes the width family from its caller: mspline and mband draw with `plot_line_width(color_idx, "")` (dash_render.py:12309, 12426), every other fit with `"lineplot"`. TR-12.16; `TestTheEmptyFitLine::test_mspline_and_mband_keep_their_own_width_family_when_empty`, built on a scheme whose two widths differ (the shipped schemes set both equal, so the parametrised test alone cannot see it).
5. **Scope against decision M3.** M3 names "computed layers (fits, smooths, densities that are frozen)", and GAPS2 C4 counts the frozen histogram bins and kdensity grid as part of the gap. Measured (E-17.2): after a move the saved histogram has 3 bins from 14.0 where the qualified draw has 2 from 17.0, and the kdensity grid starts at 14.0 against 17.0. **This section cues histogram and kdensity too**, with their own suffixes (" (bins unfiltered)", " (grid unfiltered)"). A kdensity drawn over `range()` keeps the user's grid, which is twoway's, so it is not marked (`_dash_stale_kind`). The decision is not narrowed.
6. **Page size.** Member ids never travel inside the per-callback JSON. Each distinct member set is one `ColumnDataSource({"id": [...]}, tags=["dash_stale_members"])`, shared by every callback, which Bokeh serialises once (E-17.6: `agg_configs_json` is written once per filter, 0.80 MB → 1.35 MB from 1 to 4 filters). TR-12.8; `TestThePageSize`.
7. **Title placement.** The cue Title goes to index 0 of `fig.above` (`fig.above = [cue] + list(fig.above)`), nearest the frame, below a top legend and the subtitle. With `title()`, `subtitle()` and `legend(position(12))`, `fig.above` is `["Title", "Legend", "Label"]` afterwards (E-17.7). `TestTheTitlePlacement`, and the same spec in `test_stale_cue_browser.py`.
8. **Block placement.** The JS block is the last top-level statement of `_FILTER_JS`, after the aggregate loop and the derived-copy loop and outside every loop that uses `continue`, wrapped in `if (typeof stale_configs_json !== "undefined") { … }` so an older caller's args keep working. TR-12.10; `TestTheCueAgainstHostileInput::test_the_block_is_last_and_declares_no_arg`.
9. **EW-01 asserts parity, not 0.8 × gap.** twoway's bar width is one x unit (P1.17). The certification case asserts saved-after-move == served-after-move == saved-qualified. TR-12.20.
10. **One rbar fallback.** 0.64 is the styled path's width at one distinct x (`0.8 * min(..., default=0.8)`, dash_render.py:10667-10670). Measured: saved-qualified rbar at slider 11385 = 0.64, saved after the JS move = 0.64. map_rbar computes `_rb_fallback = 0.8 * 0.8` once and uses it for the drawn width and the `_tag_spacing` fallback. map_bar does the same with 0.8. The three paths cannot drift. TR-12.18; `TestTheBarWidthFallback`.

**Missed sites, now in the Technical requirements.** `_layer_weights` 8496-8536 (TR-12.4); mspline/mband width family 12309/12426 (TR-12.16); the step 3b member rule 28172-28174 (TR-12.6); per-callback string args 27838-27855 (TR-12.8); `fig.above` content (TR-12.8); the aggregate loop's `continue`s 16420-16471 (TR-12.10); the js_runner Div stand-in and the elif write-back 150-151/293-303 (TR-12.13).

**Missed tests, now in the TDD stubs.** Zero-weight row; negative-weight fpfit; null y; empty fit; date filter with a fit on a date x; fit on the second axis; by(, total); title order with a top legend and subtitle; page size across filter counts; a scheme whose two width families differ; a direct unit test of `_empty_fit_line` with its map entry; `muted` in the parity glyph profile; histogram and kdensity on a move and back.

**Truth disputes, resolved.**
- The sample rule: amendment 1 (re-measured: E-17.4).
- "histogram and kdensity are re-estimated": only their heights and values are. Amendment 5 (re-measured: E-17.2).
- "the empty branches draw … no legend_label": wrong. The key is present at HEAD. The defect is the colour and width (re-measured: E-18.3, `('Line', '#1f77b4', 1)` with keys `[('mpg', 1), ('Fitted values', 1)]`).
- Everything else was re-measured and confirmed (E-17.1, E-17.3, E-18.1, E-18.4).

**Decisions this section makes (inside the binding decisions; flagged for S15).**
- **D12-1 (R6, E4).** The saved-only status Div is the standalone half of the EXISTING allowance `"aggregate layers recompute live"`. `ALLOWED` is not edited: no key and no reason changes. The parity readers skip a Div tagged `dash_stale_status` through `_allowed("aggregate layers recompute live")`. The design's new key is dropped because index R6 says nobody edits `ALLOWED` and E4 requires it unchanged. TR-12.12.
- **D12-2.** The `stale_*` args are set only on pages that have a config. There are no builder defaults, so the models of a filter page with no frozen layer are unchanged (`_FILTER_JS`'s text grows on every filter page).
- **D12-3.** No build-time note (DISCOVERY Q22, and the parity guard compares warnings). GAPS2 C4's plan item 3 ("print a build-time note") is recorded as not done in Notes for the closeout.
- **D12-4.** Static refusal parity is already true, so `dash.ado` is unchanged (measured E-18.4: dash refuses fpfit, mband and mspline on 0 rows with r(198), lpoly with r(2000), and lfit and kdensity on 1 row with r(2001), as twoway does).
- **D12-5. Copy.** These are module constants: title `Marked layers were computed before the filter`; suffixes ` (unfiltered)`, ` (bins unfiltered)`, ` (grid unfiltered)`; the status line in TR-12.1.

## Overview

**P0.17 — the saved page's frozen layers go stale with no cue.** A saved page's filter callback (`_FILTER_JS`) redraws every row layer from the kept rows. A fitted or smoothed line keeps the fit it had at build: lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline. A histogram keeps its bins and a density its grid.
- Measured on `test_mode_parity._DF` with the dropdown moved to Foreign: the lfit still starts at 29.1052, Stata's all-rows `regress mpg weight` value at weight 1800 (29.105207). The subset fit `regress mpg weight if foreign==1` gives 29.91739.
- Every renderer has `muted False`. No caption, legend change or text says anything.
- The served app refits (29.9174 at 1800, 16.9993 at 3350), which is right.

Decision M3 binds: a visible cue, no JavaScript estimator. After this section, the saved page marks a layer while the filters that reach it have removed at least one row of its estimation sample:
- the layer is dimmed to 30% of each of its own alphas, keeping colour, width and dash;
- its legend key gains " (unfiltered)", " (bins unfiltered)" or " (grid unfiltered)";
- its graph shows a pale-amber caption under the title, `Marked layers were computed before the filter`;
- one status line in the filter area says the same in DOM text with `role="status"`.

A move back to every row of the sample clears every mark. A move that removes only rows the layer never used (a missing y, x or weight, a zero weight, a row outside its own `if`) marks nothing. The served app is unchanged and carries no cue.

**P0.18 — the served redraw keeps build-time bar widths, and an emptied layer loses its style.**
- After a served move, bar and rbar keep the build's width: 56 where the qualified saved draw gives 168 (dropdown Foreign), 512 (slider 10000) or 0.8/0.64 (slider 11385). Under `by(rep)` the served widths are 136/280/1824 where the saved page draws 0.8/512/0.8. The cause is that the emitted step 3 copies only `_new.data` onto `_live.data`, and the width is a glyph scalar.
- A layer left with no drawable rows is drawn as a bare Bokeh glyph, `#1f77b4` at width 1, where twoway keys it in its own p# style (`stroke:#90353B;stroke-width:8.64` for the second plot under s2color). This affects the initial draw in both modes (fits and smooths at 0-2 rows; histogram at 0) and the served initial draw of bar, rbar, rarea and rspike at 0 rows. The handoff names it "an emptied lowess panel keeps its style".
- bar and rbar are not in the moved-layer parity tests.

After this section, the served redraw copies the redrawn glyph's width onto the live glyph. Every empty branch draws the same styled glyph its populated branch draws, and both are pinned by parity cases that move, empty and redraw.

**Why one section.** Both items are "what a filter move leaves on the page" for the computed and spacing-derived layers. Both read the same build-time tags (`_dash_agg_*`, `_tag_spacing`) and the same `_FILTER_JS`/served step-3 pair, and both are verified by the same moved-layer parity machinery.

**Test order and commit rule.** Two P0 entries, two commits, never red (D1, rules 4 and 7).
- **P0.17 cycle.** 12-01 records the blast radius. 12-02 extends the node runner's write-back (test infrastructure, guard tests only). 12-03 and 12-04 write every P0.17 regression test and run it against the S12 base (`<scratch>/batch-2-s12-base.txt`: `wp29-p0` after S10 and S11 land, amendment C1), saving the failure text to `<scratch>/12-P0.17-failure.txt`. 12-05 to 12-08 fix. 12-09 adjusts the parity readers and flips docstrings. 12-10 adds the Stata-certified cases. 12-11 and 12-12 close the entry and make commit 1, with the subject ending `(WP-29 P0.17)`.
- **P0.18 cycle.** 12-13 extracts the Stata fixture. 12-14 and 12-15 write every P0.18 regression test and run it against the tree commit 1 leaves, saving to `<scratch>/12-P0.18-failure.txt`. 12-16 and 12-17 fix. 12-18 adds the certification cases. 12-19 and 12-20 close the entry and make commit 2, with the subject ending `(WP-29 P0.18)`.

No test-only commit exists.

## Risk: [yellow] — a new saved-page script block and new models on every filtered page with a computed layer, plus a sweep of thirteen empty branches in both modes

**Why.**
- The cue adds a JavaScript block that runs on every move and three kinds of models (Title, Div, member CDS).
- The block is wrong in a costly direction either way: a missed cue leaves the user trusting a stale fit, and a false cue tells them a correct one is stale.
- The empty-branch sweep changes pictures in both modes.

**Risk factors.**
1. Saved/served layout parity: the status Div exists only on the saved page, and the parity readers would report it on every spec with a computed layer and a filter (D12-1).
2. BokehJS semantics (`renderer.muted`, `Title.visible`, `LegendItem.label = {value}`) are only proved in a browser. Node runs stand-ins.
3. Layout shift: the caption takes about 14 px above the frame when it appears (prototype screenshots, research). A `by()` grid's panels can lose alignment while one panel is marked.
4. Bokeh's sticky toolbar pairs an `above` toolbar with the FIRST Title in the panel (`bokeh.js:44765-44790`, E-17.7). An index-0 cue Title would capture it. At HEAD no dash figure has `toolbar_location == "above"` (measured: None, or "right" for a lone layout(bs) item).
5. Ordering in batch 2:
   - S10 and S11 also edit `_make_figure_body`, `dash.ado` and `map_lpoly`/`map_lpolyci`. S11 rewrites map_lpoly, whose empty branch this section restyles, and gives lpolyci the separate band source the cue must mark. Under C1 this section's worktree is cut after both land, so their text is already on its tree.
   - S13 merges after and edits `ServerAppBuilder` beside step 3.
6. A browser cost of O(rows × marked layers) per move.

**Mitigation.**
1. D12-1, with a test that the skip is narrow: only a `Div` tagged `dash_stale_status` is skipped, and the served document never holds one.
2. `test_stale_cue_browser.py` drives the real page in headless Chrome in both layouts and both filter positions. It is red under `DASH_STRICT=1` when Chrome is absent.
3. The caption sits outside the frame and never occludes data, which is why an in-frame Label was rejected. The shift is recorded in the help ("the graph shows a caption").
4. `TestTheTitlePlacement::test_no_marked_figure_has_its_toolbar_above` fails if a later change puts a toolbar above a marked figure.
5. C1 removes the S10/S11 contention. The map_lpoly hunk, the one-line empty-branch call, is written on S11's landed text. `test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked` proves the cue reaches S11's three sources. The only merge left is S13's, and the step-3 hunk there is three comment lines and one call, anchored by symbol (Notes, "Merge rules").
6. Early exit per layer, memoised masks (`dash_mask_for`), and one shared member Set per config. 12-08 records the move time on a 100,000-row page in the commit body.

## Dependencies

- **Depends on:**
  - **S01.** It places `<!-- WP-29 P0.17 -->` under `### Fixed in WP-29` and `<!-- WP-29 P0.18 -->` in the `**WP-29 (drop-in P0, 30sep2026)**` group of `### Results that change`. It opens both BUGS.md entries (`grep -n "WP-29 section 12" BUGS.md`) with the `WP29_OPEN` keys `"P0.17"`/`"P0.18"`. It creates `test/test_wp29_truth.cscript` with `_w29_expect`/`_w29_done`, the work-directory local `w29_work` and the marker line.
  - **S05.** It converts computed-layer inputs to Stata units through `GlyphMapper._masked(..., units=)`/`_layer_units` and rewrites the `_FILTER_JS` aggregate loop. This section's weight-state check calls `_masked(..., units=...)` the same way, and its JS block sits after that loop.
  - **S07.** It fixes the view registration in `_make_figure_body`'s per-plot block (P0.15). This section's tag hunk sits a few lines below it, so S07's hunk must already be on the tree.
  - **S11 (batch 2, amendment C1).** Two things depend on it:
    - S11 splits lpolyci into three sources, in the order band, outline, line, drawn or empty (its TR-11.15 and `TestSources::test_three_sources_drawn_or_empty`). It hands this section the requirement that the cue mark all three.
    - S11 rewrites `map_lpoly`, whose empty branch 12-17 restyles.

    This section's worktree is therefore cut from `wp29-p0` only after S10 and S11 have landed and the merger's interim full-suite run is green. Its base is `<scratch>/batch-2-s12-base.txt`. A stub that needs S11's structure fails with `pytest.fail("needs S11 (P0.9 three-source lpolyci)")` and never skips (S11's convention).
- **Blocks:** none. S15 records the residuals.
- **Batch:** 2, second wave (C1). S10, S11 and S13 start from `<scratch>/batch-2-base.txt`. S12 starts once S10 and S11 have landed and runs alongside the rest of S13. Merge order: S10, S11, **S12**, S13.
- **Contract for S14 (batch 3).** The stale scan is a consumer of the saved snapshot. For every frozen layer it reads the cells of its variables and weight on every row of its member set (every row when the set is absent). S14's embed restriction must keep those cells. `TestTheCueFollowsEachTarget::test_only_an_lfit_with_no_scatter_is_marked` goes red if it does not.

## Evidence

Line numbers are at `7421d3d`. Batch 1 (S02-S09) moves them, so symbols are authoritative. Probe scripts live in the session scratchpad and are quoted here, not cited (index "Deltas").

### E-17.1 The saved page after a move (P0.17)

The probe renders `_spec([plot_for("scatter"), plot_for(t)], {"filter": "foreign, type(dropdown)"})` and runs `test_saved_filter_layers._move(r, ("Select", "Foreign"))` under node. It prints the last data column's first two values before and after the move, and every renderer's `muted`:

```
lfit     before ('Line', 100, [29.1052, 28.9418])   after ('Line', 100, [29.1052, 28.9418])   muted [False, False]
lowess   before ('Line', 10, [30.1793, 27.7322])    after ('Line', 10, [30.1793, 27.7322])    muted [False, False]
lfitci   VArea/Patch/Line unchanged (100/201/100 points)                                     muted [False]*4
mspline  ('Line', 23, [28.0, 27.4571]) unchanged                                              muted [False, False]
served lfit after move ends: 1800.0 3350.0 29.9174 16.9993
```

No Label or Title is added. The pinned "keeps its line" test passes at HEAD: `python3 -m pytest "test/test_help_claims_4.py::TestAFitLineOnAFilterMove" "test/test_saved_filter_layers.py::TestTheSpacingTag" -q -n0 -p no:cacheprovider` gives `5 passed`. `python3 -m pytest "test/test_mode_parity.py::TestAFilterMoveAgrees" -k lfit -q -n0 -p no:cacheprovider` gives `32 passed` (the served refit agrees with the saved-qualified draw).

### E-17.2 Histogram bins and kdensity grid are frozen too (amendment 5)

The saved page after the JS move (dropdown Foreign), diffed against the saved page drawn from `if foreign == 1`:

```
histogram [('/glyphs[0]/coords/left[1]/len', 3, 2), ('/glyphs[0]/coords/left[1][0]', 14.0, 17.0),
           ('/glyphs[0]/coords/left[1][1]', 19.3333, 23.5), ('/glyphs[0]/coords/right[1]/len', 3, 2)]
kdensity  [('/glyphs[0]/coords/x[1][0]', 14.0, 17.0), ('/glyphs[0]/coords/x[1][1]', 14.0535, 17.0435), ...]
```

The JS recomputes the heights (histogram) and the density values with a bandwidth re-derived from the kept rows (kdensity, `_FILTER_JS` agg loop, about :16480-16495). The kdensity grid is `ac.x_grid` (built over the data's min..max), unless `range()` gave it (`map_kdensity`, :10514-10519: `_rng = _dash_range_pair(options, "kdensity", …)`). With `range()` given, the grid is the user's and twoway's, so the page draws twoway's curve and is not marked.

### E-17.3 Stata truth for P0.17

All runs go through `scripts/stata_slot.sh <scratch> <do>` with `dash_nobrowser=1` and s2color.

On the 10-row `_DF` (typed with `input`), from the research `truth.log`:
```
ALL  b=-.00709441 cons=41.875145 at1800=29.105207 at4080=12.929953
FOR  b=-.00833426 cons=44.919055 at1800=29.91739 at3350=16.999289
RNG  b=-.00719634 cons=42.424357
SLIDERMIN b=-.00709441 N=10
```

On `sysuse auto`, re-measured this pass (`scu.do`):
```
SCU1 N=22 b=-.0104259575877988005 cons= 48.91829723174325295 minw=1760 maxw=3420
SCU1 yhat_min= 30.56861187721736428 yhat_max= 13.26152228147135759
ALL N=74 b=-.0060086868119993289
SCU2 pmin=3291 N=74 b=-.0060086868119993289
```

A move that keeps every row (the slider at its minimum) keeps Stata's N and fit, so no cue is due. twoway has no filter widget. Its truth for a move is the refit on the subset, which the served app draws, and the saved page's cue says it does not (M3).

### E-17.4 The weighted sample (amendment 1)

Review `t1.do` on `_DF` with `w = 1 0 2 1 1 3 1 2 1 1` (the zero weight is on the row with price 4749):

```
regress mpg weight [aw=w]                    AW N=9 b= -0.00701112
regress mpg weight [aw=w] if w>0             AW w>0 N=9 b= -0.00701112
regress mpg weight [aw=w] if price!=4749     AW drop zero-w row N=9 b= -0.00701112
regress mpg weight [fw=w]                    FW N=13 b= -0.00701112
regress mpg weight [fw=w] if price!=4749     FW drop zero-w row N=13 b= -0.00701112
```

dash's rule is `GlyphMapper._layer_weights`, dash_render.py:8436-8536.
- The type is refused per layer (`_DASH_WEIGHT_ACCEPTS`, :148-156). lowess takes none.
- mspline and mband ignore it (`_DASH_WEIGHT_INERT`, :158).
- A negative weight makes the layer draw nothing, except on lfit, qfit, lfitci and qfitci (`_DASH_WEIGHT_NEG_EXCLUDED`, :165).
- A non-integer fweight draws nothing (:517-528).
- Then `w > 0` is kept:

```python
8529        pos = w > 0
8530        if not pos.all():
8531            _dash_warn_once(
8532                ("weight-nonpositive", layer, wexp), ...)
8535            cols = tuple(c[pos] for c in cols)
```

### E-17.5 The code the cue builds on

**Member rows.** `GlyphMapper._agg_member_ids(source, view)` (:8387-8408) returns the source's `__dash_row__` values that the view selects. `render()` step 3b (:28163-28180) sets `member_ids` only on a strict subset:

```python
28171                _rows = getattr(_r, "_dash_agg_rows", None)
28172                if _rows is not None and len(_rows) < _n_rows:
28173                    _cfg["member_ids"] = _rows
```

**The per-plot loop.** In `_make_figure_body` (:25920) the per-plot loop dispatches each layer, then snapshots its renderers:

```python
26280            _layer_renderers = list(fig.renderers[_r_before:])
26281            _plot_renderers.append((plot, _layer_renderers))
```

The univariate branch names its variable as `pyvar = plot.get("yvar", "") or plot.get("var", "") or yvar` (:26247-26248). The default branch uses `pyvar = plot.get("yvar", yvar)` and `pxvar` (:26259-26265). The legend is rebuilt after the loop (`self._rebuild_legend(fig, …)`, :26326), so legend items are final when render() step 5 runs.

**Callback wiring.** `_build_filter_widgets` (:27507) writes one set of args per callback (:27838-27855). A string arg is serialised once per callback, and a model once per document (the orig snapshot comment, :27640-27650). `_use_for(target, members=None)` (:27723-27727) resolves a by() panel through `_owner_of`. The status Div goes into `filter_row_widgets` before the CSV button (:27861-27869).

**The script.** `_FILTER_JS` (:15812-16497):
- `dash_mask_for(use)` (:15879) memoises one mask per use list.
- `const n_rows`, `orig` and `_primary_ids = orig[ROW_ID]` are top-level.
- The derived-copy loop and `dash_spacing` are at :15989-16030.
- The aggregate loop is at :16308-16495 and ends the script; it uses `continue` at :16313, :16332, :16383, :16424, :16447 and :16480.
- There is no top-level `return` (`awk` over the range finds none).

The brush code slices only `// ---- KPI recompute, shared by` … `dash_apply_kpis(new_data,` and `function dash_pctl(` … the kernels. `test/js_runner.py:417-445` slices the histogram and kdensity branches. Neither slice reaches the end of the script.

**muted glyphs.** `click_policy` is left at Bokeh's default (dash_render.py:18454), and no code sets `muted`, so `GlyphRenderer.muted` is free for this use. `Glyph.clone()` works on bokeh 3.9.0 (measured: `Line(line_alpha=0.8).clone()` then ×0.3 gives 0.24, keeping colour, dash and width). Bokeh's automatic muted glyph is built when the renderer is, and does not follow a later restyle (research: it stayed red after `line_color` became green). So the muted glyph is rebuilt at wiring time.

### E-17.6 Page size (amendment 6)

Review `p_size.py`, re-run this pass. 4,000 rows, `by(foreign)` histogram:

```
1 callbacks; agg_configs_json chars per cb 24635 total 24635
4 callbacks; agg_configs_json chars per cb 24653 total 98612
price, type(slider) member_ids occurrences in doc: 6 doc chars 802009
(4 filters)         member_ids occurrences in doc: 24 doc chars 1346757
```

### E-17.7 Where the caption goes (amendment 7)

Review `p_legend.py`, re-run: with `title("T") subtitle("S") legend(position(12))`, `fig.above` is `['Legend', 'Label']`. Two lfits keep two "Fitted values" items, and lfitci keys `95% CI` → [VArea, Patch] and `Fitted values` → [Line].

BokehJS 3.9.0 (`bokeh/server/static/js/bokeh.js:44748-44790`) copies `model.above`, pushes the plot title LAST (outermost), and with `toolbar_sticky` pairs an `above` toolbar with the first `Title` in the list. Index 0 is therefore nearest the frame.

Measured `toolbar_location` (title_location `above`) across layouts: auto `None`; auto `by()` `None`; bs `by()` panels `None`; a lone bs item `"right"`.

### E-17.8 The parity readers (D12-1)

`test/test_mode_parity.py`:
- `_layout_tree` (:787) spells a `Div` as `("Div", ("text", m.text))` (:817), so a saved-only Div makes the trees differ;
- `_bs_markup_page` (:894) profiles every root in the filter-bar chunk (:923);
- `_glyph_profile` (:328) records type, `visible`, dims, style and coordinates, but not `muted` (:346);
- `_annotations` handles LabelSet, Label, Span, Legend, BoxAnnotation, Band and Arrow, and skips a `Title`;
- `_chrome` reads `fig.title` only.

`ALLOWED["aggregate layers recompute live"]` (:106-112) reads "The server recomputes histogram bins, fitted lines and kernel densities from the filtered rows on every widget move; standalone precomputes them …". At HEAD it is looked up only inside docstrings (:337, :2223). `TestTheAllowanceListIsExplicit` (:2647-2662) needs each key spelled `_allowed("<key>")` in the module body.

### E-17.9 The node runner (TR-12.13)

`test/js_runner.py`:
- `stand_in` (:139-160) encodes a Div as `{"__type__": "Div", "text": …}` and any other model by `value/start/end/step/indices/width` only;
- `RUNNER`'s output (:286-292) is an `if/else if` chain;
- `JsSession.run_code`'s write-back (:293-303) is an `elif` chain, so a model can commit only one of `data`, `booleans`, `text` and `width`.

`muted` (GlyphRenderer), `visible` (Title, Div) and `label` (LegendItem) are never encoded or written back.

### E-18.1 Served widths (P0.18)

Review `p_width.py`, re-run this pass:

```
bar  dropdown Foreign saved-JS [168] | saved-qual [('value', 168.0)] | served [('value', 56.0)]
bar  slider 10000     saved-JS [512] | saved-qual [('value', 512.0)] | served [('value', 56.0)]
bar  slider 11385     saved-JS [0.8] | saved-qual [('value', 0.8)]   | served [('value', 56.0)]
rbar dropdown Foreign saved-JS [168] | saved-qual [('value', 168.0)] | served [('value', 56.0)]
rbar slider 10000     saved-JS [512] | saved-qual [('value', 512.0)] | served [('value', 56.0)]
rbar slider 11385     saved-JS [0.64]| saved-qual [('value', 0.64)]  | served [('value', 56.0)]
```

The emitted `_on_filter_change` step 3 (`ServerAppBuilder._generate_app_source`, :31207-31240) copies data only:

```python
31212            "                _fresh = agg['redraw'](agg_fdf)",
31213            "                for _live, _new in zip(agg['sources'], _fresh):",
...
31222            "                    _live.data = _dash_keep_jitter(",
31223            "                        dict(_new.data), _orig_src_data.get(id(_live), {}))",
```

The redraw's glyph already has the kept rows' width. `GlyphMapper._tag_spacing` (:8252-8267) records `source._dash_spacing_glyphs`, and `map_bar` (:8216-8219) and `map_rbar` (:10682-10683) are its only callers that pass glyphs. The rcap callers (:10822, :11167) write columns, which the data copy already carries.

Research prototype: patching the app to copy the redrawn glyph's width made served == saved-qualified for bar and rbar × 5 moves, `by(rep)`, `by(foreign)` with a range, and a linked pair. Unpatched `by(rep)` gives served 136/280/1824 where saved gives 0.8/512/0.8.

### E-18.2 The width rules

- `map_bar` (:8159-8163): `bar_width = 0.8 * min(gaps)` with ≥ 2 distinct x, else `0.8`. `_tag_spacing(clean_source, xvar, 0.8, 0.8, …)`. barwidth()/width() and a string x set `_bar_numeric = False`, leaving it untagged.
- `map_rbar` (:10667-10683): `0.8 * min(gaps, default=0.8)`, which is 0.64 with fewer than two x. `_tag_spacing(source, xvar, 0.8, 0.64, …)`.
- The JS `dash_spacing` (:15994-16004) returns `sp.fallback` with fewer than two values.
- The early returns draw an unstyled `fig.vbar(..., width=0.8)` for both (:8111-8113, :10647-10649), with no tag.

### E-18.3 The empty branches

Bare glyphs at HEAD, found by `awk 'NR>=8641 && NR<=12440 && /source=empty[_a-z]*\)|source=empty_src/'`:
- lfit 8682;
- qfit 8750 and 8775 (LinAlgError);
- lowess 9049;
- lpoly 9478;
- fpfit 9997;
- histogram 10141 (`_is_empty`) and 10154 (no row in the sample);
- kdensity 10470 and 10499 (bandwidth ≤ 0);
- rarea 10586;
- rbar 10649;
- rspike 10752;
- mspline 12289;
- mband 12419;
- bar 8111-8113.

lpolyci and fpfitci already draw their styled empty glyphs (:9555-9570, :10064-10075). On this section's base (C1), S11 has rebuilt lpolyci's empty branch: it runs through `_render_ci_band` with three empty sources and is still styled. This section leaves it alone. `scatteri` (:11249) is a literal type and out of scope.

Review `p_empty.py`, re-run: `(scatter mpg weight) (<t> mpg weight if price > 20000)` on the saved page:

```
lowess   [('Scatter', '#1a476f', 1.5), ('Line', '#1f77b4', 1)] [('mpg', 1), ('Fitted values', 1)]
lfit     [('Scatter', '#1a476f', 1.5), ('Line', '#1f77b4', 1)] [('mpg', 1), ('Fitted values', 1)]
kdensity [('Scatter', '#1a476f', 1.5), ('Line', '#1f77b4', 1)] [('mpg', 1), ('mpg', 1)]
bar      [('Scatter', '#1a476f', 1.5), ('VBar', '#90353b', 0.8)] [('mpg', 1), ('mpg', 1)]
```

The saved bar keeps its style because its view filters a non-empty source. The served build of the same layer has an empty source and draws it bare (research `probe_empty_sweep.py`: served bar, rbar, rarea and rspike at 0 rows). After a served move the live glyph keeps its build style. That is twoway's behaviour, so lowess `slider to 10000` diffs saved-qualified against served as `[('[0]/line_color', '#1f77b4', '#1a476f'), ('[0]/line_width', 1, 1.5)]`.

### E-18.4 twoway's truth for an emptied layer

Measured by the research (`truth2.log`, `truth3.log`, `empty0_*.svg`, `lowess_two.svg`) and re-read this pass with `grep -o 'stroke:#[0-9A-F]\{6\};stroke-width:[0-9.]*' <svg> | sort | uniq -c`:

| layer at 0 rows (`if price > 20000`) | rc | key stroke |
|---|---|---|
| lfit, qfit, lowess, rarea, rspike, kdensity | 0 | `#90353B;stroke-width:8.64` |
| bar, rbar | 0 | `#90353B;stroke-width:5.76` |
| histogram | 0 | `#D7D29E;stroke-width:8.64` (hist colour, P1.4) |
| fpfit, mband, mspline | 198 | — |
| lpoly | 2000 | — |

- One row: lfit, lpoly and kdensity give r(2001).
- `twoway (scatter mpg weight) (lowess mpg weight) if price>=10000` (2 rows) gives rc 0, with `<path d="">` and the same key, `#90353B;8.64`.
- `… if price>=10000, by(foreign)` with lowess gives rc 0.

**Rule:** a layer left with no drawable rows keeps its p# style and its key.

dash's static refusals already match (this pass, `dashrc.do`, the same 10 rows, `dash (scatter mpg weight) <layer>, saving(...) replace`):

```
DASHRC 1 rc=0    :: (lfit mpg weight if price > 20000)
DASHRC 2 rc=198  :: (fpfit mpg weight if price > 20000)
DASHRC 3 rc=198  :: (mband mpg weight if price > 20000)
DASHRC 4 rc=198  :: (mspline mpg weight if price > 20000)
DASHRC 5 rc=2000 :: (lpoly mpg weight if price > 20000)
DASHRC 6 rc=2001 :: (lfit mpg weight if price >= 11385)
DASHRC 7 rc=2001 :: (kdensity mpg if price >= 11385)
DASHRC 8 rc=0    :: (lowess mpg weight if price >= 10000)
```

So the emptied style is reached through by() panels, layer qualifiers that leave 0 rows on rc-0 types, lowess at 2 rows, hand-written specs, and every served move.

### E-18.5 Coverage gap

`_MOVED_LAYERS` (test_mode_parity.py:2021) is `scatter, line, lfit, lfitci, histogram, kdensity, lpoly, rarea, pcspike, function, connected, pcarrow, pcbarrow`. It has no bar, rbar, lowess, qfit, fpfit, mband, mspline, lpolyci, qfitci or fpfitci. No `MOVE_CORPUS` move empties a layer.

The review's `p_moved.py` found that lowess, qfit, fpfit, mband, mspline, lpolyci, qfitci and fpfitci already agree after the three `_MOVES`. Only bar and rbar fail.

### E-12.0 Blast radius (R8)

At plan time the GitNexus server holds no `dash` repository (`list_repos` lists TYME and PhotoShootPlannerPro only). The executor runs `npx gitnexus analyze` in the worktree, never stages `.gitnexus/`, then runs `gitnexus_impact({target, direction: "upstream"})` on each symbol below. Grep counts at `7421d3d`:
- `GlyphMapper._layer_weights` — 14 occurrences: the 13 computed mappers plus its definition. S05 measured it HIGH.
- `DashRenderer._make_figure_body` — 3: the definition plus 2 calls from `_make_figure`. Expected HIGH (index R8).
- `DashRenderer._build_filter_widgets` — 2.
- `DashRenderer.render` — the entry point of every saved page.
- `_FILTER_JS` — 25 references in dash_render.py, and named by 24 test files.
- `map_bar` 7, `map_rbar` 3, `map_lfit` 5, `map_lowess` 2, `map_kdensity` 2 and `map_histogram` 4 in dash_render.py. Each also runs through the dispatch table `_add_glyph` (:24709 for bar) and the served `_dash_draw_layer`.
- `ServerAppBuilder._generate_app_source` — emits the app for every served dashboard.
- `test/js_runner.py` — 12 test files.

**Report every HIGH or CRITICAL result to the maintainer before editing (12-01).**

### E-12.1 Tests that pin today's behaviour (flip, never delete; R7)

- `test/test_help_claims_4.py::TestAFitLineOnAFilterMove::test_the_saved_page_keeps_its_line` stays true, because the line's data is unchanged. `test_the_saved_page_marks_its_line` is added beside it.
- `test/test_saved_filter_layers.py`, the comment above `_ROW_TYPES` (:71-74, "the saved page's documented exception (a fitted line is not redrawn …)"), becomes "is not refitted, and is marked (WP-29 P0.17)". It is a docstring flip.
- `test/test_mode_parity.py`:
  - `_MOVED_LAYERS` (:2021) is extended (P0.18), not edited;
  - `_layout_tree`/`_bs_markup_page` gain the D12-1 skip;
  - `_glyph_profile` gains `"muted"`.
- `test/test_glyphs.py:3268-3310` (HARD-2 empty-source tests) stays green and gains style assertions.
- `test/test_kpi_brush.py:7-8` quotes the help table in a docstring. It is updated to the new row text in 12-11.
- No test asserts the bare `#1f77b4` empty glyph or the served width 56. Each new failure is a new regression test.

## User stories

- **US-12.1** As a dashboard reader of a saved page, I want a fitted or smoothed line, a histogram's bins and a density's grid that no longer match the filtered points to be visibly marked, so I do not read a fit of rows I filtered out as a fit of the rows I see.
- **US-12.2** As a dashboard reader, I want the mark to go when I move the filters back to every row the layer was computed from, and never to appear for a move that removes only rows the layer never used, so it means exactly "this layer is stale".
- **US-12.3** As a dashboard reader using a screen reader, high contrast or a translator, I want the stale notice as real text, not only as dimming, so I learn it the same way.
- **US-12.4** As a dashboard reader of a served app, I want bar and rbar widths after a move to follow the bars I see, as the saved page draws them.
- **US-12.5** As a twoway user, I want a layer that my qualifier or a filter leaves empty to keep its colour, width and legend key, as twoway keys it.
- **US-12.6** As the maintainer, I want these behaviours pinned against live twoway exports, Stata's `regress`, and both modes after a move, so they cannot drift.

## Business requirements

- **BR-12.1** On a saved page, after any sequence of filter moves, a frozen layer is marked exactly when the filters that apply to its graph have removed at least one row of its estimation sample.
  - The frozen layers are lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline, histogram, and kdensity without `range()`.
  - The estimation sample is the rows of its graph, panel and own `if`/`in`, with every variable it reads present and, when weighted, the weight as dash applies it.
- **BR-12.2** A marked layer is dimmed and keeps its colour, width and dash. Its legend key reads its text followed by " (unfiltered)" (fits and smooths), " (bins unfiltered)" (histogram) or " (grid unfiltered)" (kdensity). Its graph shows the caption `Marked layers were computed before the filter`. One status line in the filter area says the same as text with `role="status"`.
- **BR-12.3** When no layer is stale, nothing is marked, the caption and the status line are hidden, and every legend key reads as built.
- **BR-12.4** A graph that every filter excludes is never marked. A page with no filter, or with no frozen layer an applicable filter reaches, carries no cue model at all.
- **BR-12.5** The served app refits every layer and carries no cue.
- **BR-12.6** After a served move, a bar's and an rbar's width is the width the saved page draws from the same kept rows: 0.8 × the smallest gap between distinct x values, or 0.8 for bar and 0.64 for rbar with fewer than two. A width the user fixed with `barwidth()`/`width()` stays.
- **BR-12.7** A computed, bar or range layer that a qualifier, a by() panel or a filter move leaves with no drawable rows keeps its scheme colour, width and legend key in both modes, as twoway keys it.
- **BR-12.8** No user text reaches the page's code or HTML through the cue. Labels are data drawn as canvas text, and the caption and status line are fixed text.
- **BR-12.9** Every changed result is listed in CHANGELOG with the command, the old value and the new.

## Technical requirements

### P0.17

- **TR-12.1 Constants** (module level, directly after `_DASH_COMPUTED_ONLY_TYPES`, dash_render.py:920-924), each with a comment naming WP-29 P0.17 and decision M3:
  ```python
  _DASH_STALE_ALPHA = 0.3
  _DASH_STALE_SUFFIX = {"fit": " (unfiltered)", "bins": " (bins unfiltered)",
                        "grid": " (grid unfiltered)"}
  _DASH_STALE_CUE_TEXT = "Marked layers were computed before the filter"
  _DASH_STALE_STATUS_HTML = (
      '<p role="status" aria-live="polite" aria-atomic="true" '
      'style="margin:0;padding:2px 6px;background:#fff4ce;color:#3d2f00;'
      'font-size:12px">Layers marked (unfiltered), (bins unfiltered) or '
      '(grid unfiltered) were computed before the filter was applied, and a '
      'saved page does not recompute them; dash serve does.</p>')
  ```
  The text colour #3d2f00 on #fff4ce has a contrast ratio of about 11.9:1. The `style` attribute is allowed by the saved page's `style-src 'unsafe-inline'` (`_DASH_CSP_STANDALONE`, :2301-2311). These are saved-page constants, and the served app reads none of them, so no copy-list entry is needed.
- **TR-12.2 `_dash_stale_kind(ptype, options) -> str | None`** (module function after the constants):
  - `None` unless `ptype.lower()` is in `_DASH_COMPUTED_ONLY_TYPES`;
  - `"bins"` for histogram;
  - for kdensity, `None` when `_dash_range_pair(options, "kdensity", "")` returns a pair (call it inside `warnings.catch_warnings()` with `simplefilter("ignore")`, because the mapper has already named a bad range), else `"grid"`;
  - `"fit"` for every other computed type.
- **TR-12.3 `_dash_stale_glyph(glyph)`** (module function): returns `glyph.clone()` with each of `line_alpha`, `fill_alpha` and `hatch_alpha` that the glyph type has replaced.
  - A number (not a bool) becomes `v * _DASH_STALE_ALPHA`, so 0 stays 0.
  - Anything else (a field name string, a `Field`/`Value` spec, None) becomes `_DASH_STALE_ALPHA`.
  - Colours, widths, dash and every other property stay as cloned.
- **TR-12.4 The weight decision, extracted** (behaviour of `_layer_weights` unchanged, including S05's `units=` keyword and every warning text):
  - `GlyphMapper._layer_weight_column(source, options, layer) -> (wtype, wexp, why)` is a `@staticmethod` with no warnings. It runs `_dash_weight_spec(options)` and returns:
    - `why = "none"` when there is no clause;
    - `"missing"` when `wexp not in source.data`;
    - `"not-numeric"` when `_dash_float_values(source.data[wexp])` raises TypeError/ValueError;
    - `"refused"` when the type is not in `_DASH_WEIGHT_ACCEPTS.get(layer, ())`;
    - `"inert"` when the layer is in `_DASH_WEIGHT_INERT`;
    - `None` when the weight is applied.
  - `GlyphMapper._layer_weight_values_state(w, wtype, layer) -> str | None` is a `@staticmethod`. It returns `"negative"` when `(w < 0).any()` and the layer is not in `_DASH_WEIGHT_NEG_EXCLUDED`; else `"nonint"` when `wtype == "fw"` and `np.any(w != np.floor(w))`; else None. This is the order `_layer_weights` checks them in.
  - `_layer_weights` calls the two helpers and maps each `why`/state to its existing warning and return value. The `weight-refused` message keeps its lowess special case. The `weight-nonpositive` drop stays in `_layer_weights`.
- **TR-12.5 Tagging in `_make_figure_body`.**
  - Before the dispatch of each plot, set `_frozen_vars = None`. In the `_UNIVARIATE_TYPES` branch, after `pyvar` is computed, set `_frozen_vars = [pyvar]`. In the final `else` branch, after `pyvar`, set `_frozen_vars = [pyvar, pxvar]`.
  - Directly after `_plot_renderers.append((plot, _layer_renderers))` (:26281):
    ```python
    if _frozen_vars and ptype.lower() in _DASH_COMPUTED_ONLY_TYPES:
        _ftag = self._frozen_layer_tag(ptype.lower(), popts, source_for_plot,
                                       _plot_view, _frozen_vars)
        if _ftag is not None:
            for _fr in _layer_renderers:
                if not _dash_is_swatch(_fr):
                    _fr._dash_frozen = _ftag   # ONE dict per layer
    ```
    The attribute is private to the Python object and never serialised.
- **TR-12.6 `DashRenderer._frozen_layer_tag(ptype, options, source, view, varnames) -> dict | None`:**
  - `kind = _dash_stale_kind(ptype, options)`; return None when it is None.
  - `wtype, wexp, why = GlyphMapper._layer_weight_column(source, options, ptype)`.
  - When `why is None`:
    - `cols = GlyphMapper._masked(source, view, *varnames, wexp, units=dict(getattr(self.mapper, "date_vars", None) or {}) or None)` (S05's keyword);
    - `state = GlyphMapper._layer_weight_values_state(cols[-1], wtype, ptype)`;
    - `wvar, wrule = wexp, ("any" if state else "positive")`.
  - Otherwise `wvar = wrule = None`.
  - `rows = GlyphMapper._agg_member_ids(source, view)`.
  - Tag `{"type": ptype, "kind": kind, "vars": [str(v) for v in varnames], "wvar": wvar, "wrule": wrule}`. Add `tag["member_ids"] = rows` when `rows is not None and len(rows) < len(self.df)` (amendment 3; `[]` is kept).
  - Any KeyError/TypeError/ValueError from the reads returns None. A layer whose columns cannot be read drew nothing to mark, and a unit test pins this.
- **TR-12.7 Registry.** In `render()`, add step 3d after 3c (:28182-28183): `self.frozen_layer_registry = self._collect_frozen_layers()`.
  - `DashRenderer._collect_frozen_layers()` returns `{fig_key: [(tag, [renderers])]}`. It walks `self.figures.items()` in order and groups each figure's renderers that carry `_dash_frozen` by the identity of the tag dict, in renderer order.
  - Figures with none are absent.
- **TR-12.8 `DashRenderer._stale_cue_args(use_for, filter_row_widgets) -> dict | None`**, called from `_build_filter_widgets` only when `self.filter_callbacks` is non-empty:
  1. Collect every `Legend` in every figure of `self.figures` (`fig.center`, `above`, `below`, `left`, `right`).
  2. For each `fig_key, entries` of `getattr(self, "frozen_layer_registry", {})`, take `use = use_for(fig_key)`; skip the figure when it is empty (an excluded graph gets nothing).
  3. On the figure's first kept entry, create `Title(text=_DASH_STALE_CUE_TEXT, visible=False, tags=["dash_stale_cue"], text_font_size="9pt", text_font_style="normal", text_color="#3d2f00", background_fill_color="#fff4ce", border_line_color="#8a6d00", align="left")`. Place it with `fig.above = [cue] + list(fig.above)` and append it to `titles`.
  4. For each `(tag, rends)` of the figure:
     - Set `r.muted_glyph = _dash_stale_glyph(r.glyph)` and `r.muted = False` on each renderer.
     - Find every LegendItem whose `renderers` include one of `rends` (by `id`). Give it one index in `items` (dedup by `id`) and record `[index, text]`, where `text` is `item.label.value` (a `Value`) or `item.label["value"]` (a dict). Skip an item whose label is a field.
     - When `"member_ids" in tag`, look up or create the shared `ColumnDataSource({"id": ids}, tags=["dash_stale_members"])` keyed by `tuple(ids)`, and record its index. Otherwise record -1.
     - Append `{"use": use, "vars": tag["vars"], "wvar": tag["wvar"], "wrule": tag["wrule"], "members": <index or -1>, "title": <title index>, "items": [[k, text], …], "suffix": _DASH_STALE_SUFFIX[tag["kind"]]}` to `configs`, and `list(rends)` to `rend_lists`.
  5. Return None when `configs` is empty, so nothing is added.
  6. Otherwise create `status = Div(text="", visible=False, tags=["dash_stale_status"], sizing_mode="stretch_width")`, append it to `filter_row_widgets` (never to `self.filter_widgets`), and return:
     ```python
     {"stale_configs_json": json.dumps(configs, allow_nan=False),
      "stale_members": members, "stale_renderers": rend_lists,
      "stale_titles": titles, "stale_legend_items": items,
      "stale_status": status,
      "stale_text_json": json.dumps({"status_html": _DASH_STALE_STATUS_HTML})}
     ```
- **TR-12.9 Wiring.**
  - In `_build_filter_widgets`, after the `_kpi_config_all` loop (:27831) and before the per-callback loop: `_stale_args = self._stale_cue_args(_use_for, filter_row_widgets) if self.filter_callbacks else None`.
  - In the loop, after `derived_spacing_glyphs` (:27855): `if _stale_args: for _k, _v in _stale_args.items(): _cb.args[_k] = _v`. Every callback gets the SAME objects (GAPS2 E2).
  - The status Div lands before the CSV button, which is appended after the loop (:27861-27869).
  - The builders `build_dropdown`/`build_slider`/`build_range` are NOT given defaults (D12-2).
- **TR-12.10 The `_FILTER_JS` block**, appended as the last top-level statement: after the closing `}` of `for (let ai = 0; ai < agg_configs.length; ai++)`, immediately before the closing `""").replace("__DASH_ROW_ID__", …)`. No other line of the script changes.
  ```js
  // ---- Marks on the layers a saved page does not recompute (WP-29 P0.17) ----
  // A fit or smooth, a histogram's bins and a density's grid are computed
  // when the page is built.  A layer is marked while the filters that apply
  // to it (c.use) remove a row of its estimation sample: a row of its own
  // (c.members; every row when -1) whose variables are finite numbers and,
  // when weighted, whose weight is finite and -- under c.wrule "positive"
  // -- above zero: the rows GlyphMapper._layer_weights fits from.  Labels
  // arrive as JSON data and are drawn as canvas text; the status note is a
  // module constant.  Last, outside every loop above.
  if (typeof stale_configs_json !== "undefined") {
      const _stl_cfgs = JSON.parse(stale_configs_json);
      const _stl_text = (typeof stale_text_json !== "undefined")
          ? JSON.parse(stale_text_json) : {};
      const _stl_rends = (typeof stale_renderers !== "undefined" && stale_renderers) ? stale_renderers : [];
      const _stl_titles = (typeof stale_titles !== "undefined" && stale_titles) ? stale_titles : [];
      const _stl_items = (typeof stale_legend_items !== "undefined" && stale_legend_items) ? stale_legend_items : [];
      const _stl_members = (typeof stale_members !== "undefined" && stale_members) ? stale_members : [];
      const _stl_fin = (v) => typeof v === "number" && Number.isFinite(v);
      const _stl_col = (name) =>
          Object.prototype.hasOwnProperty.call(orig, name) ? orig[name] : null;
      const _stl_ids = orig[ROW_ID] || null;
      const _stl_sets = {};
      const _stl_title_on = _stl_titles.map(() => false);
      const _stl_item_text = _stl_items.map(() => null);
      const _stl_item_suffix = _stl_items.map(() => null);
      let _stl_any = false;
      for (let ci = 0; ci < _stl_cfgs.length; ci++) {
          const c = _stl_cfgs[ci];
          const keep = dash_mask_for(c.use);
          let mset = null;
          if (c.members >= 0) {
              if (!(c.members in _stl_sets)) {
                  const ms = _stl_members[c.members];
                  _stl_sets[c.members] = new Set((ms && ms.data && ms.data.id) || []);
              }
              mset = _stl_sets[c.members];
          }
          const vcols = (c.vars || []).map(_stl_col);
          const wcol = c.wvar ? _stl_col(c.wvar) : null;
          let stale = false;
          for (let i = 0; i < n_rows && !stale; i++) {
              if (keep[i]) continue;
              if (mset !== null && !(_stl_ids && mset.has(_stl_ids[i]))) continue;
              let used = true;
              for (const col of vcols) {
                  if (col !== null && !_stl_fin(col[i])) { used = false; break; }
              }
              if (used && wcol !== null) {
                  const w = wcol[i];
                  used = _stl_fin(w) && (c.wrule === "any" || w > 0);
              }
              stale = used;
          }
          for (const r of (_stl_rends[ci] || [])) { r.muted = stale; }
          if (stale) {
              _stl_any = true;
              if (c.title >= 0 && c.title < _stl_title_on.length) _stl_title_on[c.title] = true;
          }
          for (const [k, text] of (c.items || [])) {
              if (!(k >= 0 && k < _stl_items.length)) continue;
              _stl_item_text[k] = text;
              if (stale) _stl_item_suffix[k] = c.suffix || "";
          }
      }
      for (let k = 0; k < _stl_items.length; k++) {
          if (_stl_item_text[k] === null) continue;
          _stl_items[k].label = {value: _stl_item_suffix[k] === null
              ? _stl_item_text[k] : _stl_item_text[k] + _stl_item_suffix[k]};
      }
      for (let t = 0; t < _stl_titles.length; t++) _stl_titles[t].visible = _stl_title_on[t];
      if (typeof stale_status !== "undefined" && stale_status) {
          stale_status.visible = _stl_any;
          stale_status.text = _stl_any ? String(_stl_text.status_html || "") : "";
      }
  }
  ```
  - An item shared by two layers is suffixed when either is stale.
  - No literal `dash_stale_` string appears in the script, so a page's needle counts see only the model tags.
  - No `const`/`let`/`function` named `stale_…` is declared at the top level. A parameter redeclared there is a SyntaxError, and a test pins it.
- **TR-12.11 Served.** No change for P0.17. `ServerAppBuilder` builds its own document, so no Title, Div or member CDS tagged `dash_stale_*` and no muted renderer exists there. `TestTheServedAppHasNoStaleCue` pins it.
- **TR-12.12 Parity readers** (test infrastructure, D12-1). In `test/test_mode_parity.py`, add `_is_stale_status(m)` above `_layout_tree`:
  ```python
  def _is_stale_status(m):
      """The saved page's hidden note that it does not refit (WP-29 P0.17):
      the standalone half of the allowance below, never a served model."""
      if isinstance(m, Div) and "dash_stale_status" in (m.tags or []):
          _allowed("aggregate layers recompute live")
          return True
      return False
  ```
  - In `_layout_tree`'s list branch, use `[_layout_tree(x, figures) for x in m if not _is_stale_status(x)]`.
  - In `_bs_markup_page`'s filter-bar comprehension, add `and not _is_stale_status(embedded[rid])`.
  - In `_glyph_profile`, after `entry = {...}` (:346), add `entry["muted"] = bool(getattr(r, "muted", False))`.
  - `ALLOWED` and `_MUST_WARN` are not edited (R6).
- **TR-12.13 Node runner** (`test/js_runner.py`):
  - **Encoding.** `stand_in` encodes:
    - a `Div` as `{"__type__": "Div", "text", "visible"}`;
    - a `GlyphRenderer` as `{"__type__": "GlyphRenderer", "muted", "visible"}`;
    - a `Title` as `{"__type__": "Title", "visible"}`;
    - a `LegendItem` as `{"__type__": "LegendItem", "label": {"value": <text>}}` (text from `.value` or a dict's `"value"`).
    Every other model is encoded as before.
  - **RUNNER output.** For a ColumnDataSource `{data}`, for a BooleanFilter `{booleans}`, else every key of `text`, `width`, `visible`, `muted` and `label` present in the stand-in.
  - **Write-back** (`run_code`). Each key commits independently:
    - `data` and `booleans` as today;
    - `text` as a string;
    - `width` when it is a number;
    - `visible` and `muted` when bool;
    - `label` with a `"value"` → `m.label = value(text)` (`from bokeh.core.properties import value`).
  - **`state()`** gains `"muted"`, `"visible"` and `"labels"` maps.
  - Existing callers see the same behaviour, and the module docstring gains one sentence naming WP-29 S12.
- **TR-12.14 Security (rule 1).**
  - Configs, labels and the status HTML travel as JSON string args parsed with `JSON.parse`, and `cb.code` stays `_FILTER_JS` exactly.
  - Labels are assigned as `{value: text}` and drawn on the canvas, never as HTML. The status HTML and the caption are module constants, and no user text is concatenated into HTML.
  - Column names are looked up as own properties, so a `__proto__` variable is a column, never the prototype.
  - `json.dumps(…, allow_nan=False)`: the configs hold no float.
  - Work is bounded: one O(rows) early-exit scan per config, memoised masks, configs bounded by the existing graph, panel and by-group limits, and member ids bounded by the row limit already enforced.

### P0.18

- **TR-12.15 Served redraw geometry.** Add a module function after `_dash_keep_jitter` (:21790):
  ```python
  def _dash_copy_redraw_geometry(live, new):
      """Give each live glyph whose width is its rows' spacing the width the
      redraw drew from the kept rows (WP-29 P0.18).  GlyphMapper._tag_spacing
      lists those glyphs on their source (`_dash_spacing_glyphs`); a served
      move copied the redraw's data onto the live source and left the
      build's width, 56 where the kept rows give 168.  A width that is not
      a finite positive number is left alone, so Bokeh's "Distances must
      be positive" can never be raised in a session."""
      for lg, ng in zip(getattr(live, "_dash_spacing_glyphs", None) or (),
                        getattr(new, "_dash_spacing_glyphs", None) or ()):
          w = getattr(ng, "width", None)
          w = getattr(w, "value", w)
          if isinstance(w, bool) or not isinstance(w, (int, float)):
              continue
          if np.isfinite(w) and w > 0:
              lg.width = float(w)
  ```
  - In the served functions copy list, add `"_dash_copy_redraw_geometry",` immediately after `"_dash_keep_jitter",` (:28761, the R2 anchor `"_dash_refresh_unlinked"`).
  - In the emitted step 3, after the two-line `_live.data = _dash_keep_jitter(...)` statement (:31222-31223), emit:
    ```python
    "                    # A bar's or rbar's width is the kept rows' spacing",
    "                    # (GlyphMapper._tag_spacing); the redraw's glyph",
    "                    # holds it, the live one the build's (WP-29 P0.18).",
    "                    _dash_copy_redraw_geometry(_live, _new)",
    ```
  - `_dash_redraw_for` is unchanged: the mapper tags the redraw's sources.
- **TR-12.16 `GlyphMapper._empty_fit_line(self, fig, xcol, ycol, options, color_idx, yvar, width_kind="lineplot")`.** It draws `fig.line(x=xcol, y=ycol, source=ColumnDataSource({xcol: [], ycol: []}), line_color=self.scheme.default_color(color_idx, "line"), line_width=self.scheme.plot_line_width(color_idx, width_kind), legend_label=yvar)`, then `self._apply_line_opts(r, options)`, and returns r. It replaces each bare empty `fig.line(…)` listed in E-18.3, keeping each caller's marks (`_mark_unfit`, `_mark_insufficient`, `_mark_silent`) and column names:
  - lfit (`"x"`, `"y"`);
  - qfit, both branches;
  - lowess (`"x_lw"`, `"y_lw"`; drop its now-duplicate `_apply_line_opts`);
  - lpoly (`"x_lp"`, `"y_lp"`);
  - fpfit (`"x_fp"`, `"y_fp"`; drop its duplicate `_apply_line_opts`);
  - kdensity, both branches;
  - mspline (`"x_sp"`, `"y_sp"`, `width_kind=""`);
  - mband (`"x_mb"`, `"y_mb"`, `width_kind=""`).

  The unused local `empty = ColumnDataSource(...)` lines are removed. The served app copies `GlyphMapper` whole (:28839-28842), so no copy-list entry is needed.
- **TR-12.17 `GlyphMapper._histogram_quads(self, fig, source, options, color_idx, yvar)`** moves map_histogram's styled `fig.quad(...)` call (:10175-10183), its `color()` override (:10184-10190), `_apply_fill_opts` and `_apply_line_opts` into one method. It returns the renderer. The populated branch and both empty branches (:10138-10141, :10146-10155) call it, the empty ones with `ColumnDataSource({"top": [], "left": [], "right": []})`. The second empty branch keeps `_mark_silent`. Tagging `_dash_agg_*` stays in the populated branch.
- **TR-12.18 Bar and range empty paths.**
  - **`map_bar` and `map_rbar`:** replace the early returns (:8111-8113, :10647-10649) with `source = ColumnDataSource({<the named columns>: []}); view = None` and fall through to the styled path.
  - **`map_bar` fallback:** set `_bar_fallback = 0.8` once and use it for `bar_width` with fewer than two x and in `_tag_spacing(clean_source, xvar, 0.8, _bar_fallback, …)`.
  - **`map_rbar` fallback:** set `_rb_fallback = 0.8 * 0.8` once and use it for `bar_width = 0.8 * min(gaps) if len(x_vals) >= 2 else _rb_fallback` and in `_tag_spacing(source, xvar, 0.8, _rb_fallback, …)`.
  - **`map_rarea` and `map_rspike`:** replace the early returns (:10584-10586, :10750-10752) the same way and fall through to their styled path.
  - Each change keeps the HARD-2 no-crash tests green.
- **TR-12.19 Maps.** `test/function_test_map.py` gains, in alphabetical place:
  - **commit 1:** `_dash_stale_glyph`, `_dash_stale_kind`, `DashRenderer._collect_frozen_layers`, `DashRenderer._frozen_layer_tag`, `DashRenderer._stale_cue_args`, `GlyphMapper._layer_weight_column`, `GlyphMapper._layer_weight_values_state`;
  - **commit 2:** `_dash_copy_redraw_geometry`, `GlyphMapper._empty_fit_line`, `GlyphMapper._histogram_quads`.

  Each names the test in the stubs that fails when the body is skipped. Verify with `python3 scripts/fncov/fncov_mutate.py --map --keys <the new keys>`.
- **TR-12.20 Certification.**
  - **`test/test_e2e_filters.cscript` (R1 area script).** SCU-01, SCU-02 and SCU-03 (commit 1) and EW-01 (commit 2), through new helpers in `test/filter_truth_check.py`:
    - `fit_graph(name, y, x, ptype="lfit", options=None, if_expr="")`;
    - `bar_graph(name, y, x, ptype="bar", if_expr="")`;
    - `stale_state(r)`, which returns `{"titles": [visible…], "muted": [bool… of every renderer carrying _dash_frozen], "labels": [text…], "status_visible": bool, "status_text": str}`;
    - `served_stale_models(doc)`, the count of models whose `tags` hold a string starting `dash_stale`;
    - `line_ends(fig)`, `(x[0], y[0], x[-1], y[-1])` of the figure's single Line glyph source;
    - `vbar_width(fig)`.
  - **`test/test_wp29_truth.cscript`.** Block `* ==== S12 P0.18: emptied layers keep their style ====` with EW-02 and EW-03 (commit 2).
  - **Fixture.** `test/fixtures/emptied_layer_truth.json`, from `scripts/extract_emptied_layer_truth.do` ("Stata truth").
- **TR-12.21 Help, CHANGELOG, BUGS** (texts in 12-11 and 12-19).

## Boundaries

- **No JavaScript estimator** (M3). `_FILTER_JS` gains only the block of TR-12.10; the histogram and kdensity recounts are S05's and stay.
- **Not touched:**
  - the lpoly bandwidth or band arithmetic (S11);
  - the date-unit conversions (S05);
  - the view registration (S07);
  - line join order (S02);
  - the token, the launcher and the private root (S08, S13);
  - embed rows (S14; contract in Dependencies).
- **Not changed:** twoway's 1-x-unit bar width (P1.17); the histogram key colour (P1.4); legend text (P1); P2.24's recompute of bins and grid; `dash.ado` and `dash_parse.mata` (D12-4); `ALLOWED` and `_MUST_WARN` (R6, D12-1).
- **No build-time note** (D12-3, Q22). The served app gains no cue (M3).
- **Tracking documents are S15's** (A5): no edit to ROADMAP.md, GAPS2.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md or AGENTS.md. Their text is in "Notes for the closeout".
- **Shared files:** no new `.cscript` file and no edit to `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py` (A3, R1). `test/test_fixtures_are_committed.py` needs no edit: it scans `test/fixtures/` and is satisfied because `test_emptied_layer_style.py` names the new fixture and git tracks it.
- **Not staged:** `CLAUDE.md`, `.gitignore`, `.gitnexus/`, scratch files or `*.html`.

## Stata truth

**Fixture (P0.18).** Create `scripts/extract_emptied_layer_truth.do` on the frame of `scripts/extract_colorvar_truth.do`:
- a header comment (purpose, output path, the wrapper command, METHOD);
- `clear all`, `set more off`, `set linesize 200`;
- `global ZE_REPO` defaults to `/Users/billy/Desktop/Programs/StataPrograms/d/dash`, overridden by `local ze_env : env DASH_REPO`;
- `adopath ++ "${ZE_REPO}"`, then `quietly do` of `dash_parse.mata` and `dash.ado`, then `global dash_nobrowser 1`;
- the work directory `` "`c(tmpdir)'dash_emptied_probe" ``;
- exit 601 when `c(python_exec)` is empty;
- the data typed with `input` (the 10 rows of `test_mode_parity._DF`: mpg weight foreign price).

For each scheme in `s2color s1mono` (`set scheme`), it runs:
- **the base** `twoway scatter mpg weight, legend(on)`, exported to `base_<scheme>.svg`;
- **for each type**, the populated reference `twoway (scatter mpg weight) (<type> <vars>)` and the probes `twoway (scatter mpg weight) (<type> <vars> if <q>)`:
  - `<vars>` is `mpg weight` for lfit, qfit, fpfit, lowess, lpoly, mband, mspline and bar; `mpg price weight` for rarea, rbar and rspike; `mpg` for histogram and kdensity;
  - `<q>` is `price > 20000` (key `rows0`), `price >= 11385` (`rows1`) or `price >= 10000` (`rows2`);
  - each probe runs under `capture noisily`, recording `_rc`, and is exported to SVG with `graph export … , replace` only when rc is 0.

The trailing `python:` block never calls back into Stata:
- for each SVG it reads the set of `(stroke, stroke-width)` pairs matched by `stroke:(#[0-9A-Fa-f]{6});stroke-width:([0-9.]+)`, lower-casing the colour;
- `key_styles` = probe set − base set, sorted, as `[[colour, width], …]`;
- it writes `{"_meta": {...}, "schemes": {"<scheme>": {"base_styles": [...], "probes": {"<type>": {"populated": {"rc", "key_styles"}, "rows0": {"qualifier", "rc", "key_styles"|null}, "rows1": …, "rows2": …}}}}}`.

`_meta` holds:
- `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` and `extracted` (`c(current_date) c(current_time)`). `dash_commit` comes from `quietly shell git -C "${ZE_REPO}" rev-parse HEAD > <work>/git_head.txt`, read from the file in Python, never with `shell=True`;
- `empty_matches_populated`: `"held"` when every rc-0 probe of a type other than histogram has `key_styles` ⊆ that type's populated `key_styles`, else `"failed: <type/probe>"`;
- `base_has_no_layer_colour`: `"held"` when no colour of any probe's `key_styles` is in `base_styles`.

The block writes a backtick as `\x60` if one is ever needed, and erases every SVG it wrote.

Run it through the wrapper only:

```sh
DASH_REPO=<W> dash_nobrowser=1 scripts/stata_slot.sh <scratch> <W>/scripts/extract_emptied_layer_truth.do
```

Read `<scratch>/extract_emptied_layer_truth.log`; never relaunch to check. Expected (E-18.4), s2color `rows0`:
- lfit, qfit, lowess, rarea, rspike and kdensity: rc 0 with key `[["#90353b", 8.64]]`;
- bar and rbar: `[["#90353b", 5.76]]`;
- histogram: `[["#d7d29e", 8.64]]`;
- fpfit, mband and mspline: rc 198; lpoly: rc 2000.

`rows1`: lfit, lpoly and kdensity rc 2001. `rows2`: lowess rc 0 with `[["#90353b", 8.64]]`.

`git add -f test/fixtures/emptied_layer_truth.json`. It is never patched by hand (R5).

**Live certification.**
- **SCU-01..SCU-03 and EW-01** (`test/test_e2e_filters.cscript`, R1 area script, appended after S07's QF cases, before `// Cleanup`). Each computes its own truth with `regress`, `summarize` or `count` before its `python:` block and is judged with `assert` plus `display "<ID> PASS: …"`, as FL-E2-1 is.
  - **SCU-01:** `sysuse auto`; an lfit-only graph (`ftc.fit_graph("g1", "mpg", "weight")`) and a `foreign` dropdown. Truth: `regress mpg weight if foreign==1` and `summarize weight if foreign==1` give ŷ(1760) = 30.56861187721736 and ŷ(3420) = 13.26152228147136 (E-17.3).
    - Saved, after a move to 1: the lfit is muted, its caption visible, its key ends " (unfiltered)", and the status is visible with `dr._DASH_STALE_STATUS_HTML`.
    - Saved, moved back to the sentinel: all cleared.
    - Served, after the move: `line_ends` equal Stata's within 1e-9 relative, and `served_stale_models(doc) == 0`.
  - **SCU-02:** a `price` slider moved to its start (3291). Stata: `regress mpg weight if price >= 3291` has N = 74 and b equal to the all-rows b. The saved page holds one caption, hidden, and no muted renderer.
  - **SCU-03:** `dash (scatter mpg weight) (lfit mpg weight), name(gscu)`.
    - `dash build, saving("<tmp>.html") replace` holds 0 of `dash_stale_cue` and 0 of `dash_stale_status` (`cert_file_count`).
    - `dash build, saving("<tmp2>.html") replace filter(foreign, type(dropdown))` holds 1 of each.
  - **EW-01:** the 10 `_DF` rows typed with `input`; a bar-only graph (`ftc.bar_graph`) and a `foreign` dropdown. Saved after the move to 1 == served after the move == saved drawn with the graph `if foreign == 1` and no filter; the served width after the move differs from the served width before it.
- **EW-02 and EW-03** (`test/test_wp29_truth.cscript`, block S12, gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S12")`, above the marker and after S11's blocks).
  - **EW-02:** for each `t` in `lfit qfit lowess rarea rbar rspike bar kdensity`, on the 10 rows, export `twoway (scatter mpg weight) (<t> <vars> if price > 20000)` live with `cert_svg_export`. Then register `dash (scatter mpg weight) (<t> <vars> if price > 20000), name(zew<k>)`, write the spec with `_dash_serve_spec`, and in Python render the saved page (`DashRenderer`) and the served document (`ServerAppBuilder` and `make_document(Document())`, the KF-03 loader pattern). The colour of the second layer's first glyph (`line_color`, or `fill_color` for VArea) lower-cased equals the colour of the probe SVG's style set minus the base set, in both modes.
  - **EW-03:** `(lowess mpg weight) if price >= 10000` (two rows, graph `if`): the same comparison. dash's empty lowess line width equals the populated lowess line width in both modes.

Run with the S01 driver:

```sh
W=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s12
printf 'adopath ++ "%s/"\ncd "%s/test"\ndo "%s/test/%s"\n' "$W" "$W" "$W" test_e2e_filters.cscript > <scratch>/run_test_e2e_filters.do
cd "$W" && dash_nobrowser=1 scripts/stata_slot.sh <scratch> <scratch>/run_test_e2e_filters.do
printf 'adopath ++ "%s/"\ncd "%s/test"\ndo "%s/test/%s"\n' "$W" "$W" "$W" test_wp29_truth.cscript > <scratch>/run_test_wp29_truth.do
cd "$W" && dash_nobrowser=1 WP29_ONLY=S12 scripts/stata_slot.sh <scratch> <scratch>/run_test_wp29_truth.do
```

A SKIP (exit 222, empty `c(python_exec)`) is not a pass.

## TDD test stubs

**(red)** marks a test that fails at the cycle's base for the reason stated. **(guard)** marks one that passes there and must still pass. Every red failure text is saved verbatim.

### P0.17 (base: `<scratch>/batch-2-s12-base.txt`, amendment C1)

**`test/test_saved_stale_cue.py` (new).**

Imports:
- `_render`, `_move`, `_MOVES` from `test_saved_filter_layers`;
- `_DF`, `_spec`, `_layout_tree`, `_served_after_move` from `test_mode_parity`;
- `plot_for` from `test_server_layer_defects`;
- `JsSession`, `requires_node` from `js_runner`.

Helpers:
- `_set(r, kind, raw)` sets a widget's raw value and runs its own callback through one shared `JsSession` per render, which commits.
- `_back(r, kind)` uses a Select's `_dash_sentinel`, a RangeSlider's `(start, end)` or a Slider's `start`.
- `_cue(r)` returns `{"titles": {fig_key: [t.visible for t in fig.above if "dash_stale_cue" in t.tags]}, "muted": {fig_key: [r.muted for r in fig.renderers if hasattr(r, "_dash_frozen")]}, "labels": {fig_key: [label text of each legend item]}, "status": (Div.visible, Div.text) of callbacks[0].args.get("stale_status")}`.

Every node class carries `@requires_node`. At base, every red case fails with `AssertionError: no Title tagged dash_stale_cue on g1 (0 found)` or `AttributeError: module 'dash_render' has no attribute …`.

- `TestTheCueAppearsOnAMove::test_a_layer_the_move_took_rows_from_is_marked[<t>-<move>]`, for the 13 frozen types × the 3 `_MOVES`, spec `[plot_for("scatter"), plot_for(t)]` (red).
  - Before the move: one hidden caption, nothing muted, the labels as built.
  - After: every frozen renderer muted, the caption visible, each label of the layer ends with `_DASH_STALE_SUFFIX[kind]`, the scatter's label is unchanged, and the status is `(True, dr._DASH_STALE_STATUS_HTML)`.
- `TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` — lfitci: VArea, Patch and Line muted; `95% CI (unfiltered)` and `Fitted values (unfiltered)` (red).
- `TestTheCueAppearsOnAMove::test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked[dropdown|range|slider]` (amendment C1; red at the S12 base with `no Title tagged dash_stale_cue`). The spec is `[plot_for("scatter"), plot_for("lpolyci")]`.
  - **Precondition.** The lpolyci layer's renderers draw from three distinct `ColumnDataSource`s in S11's order: band (holds `y_lower` and `y_upper`), outline, then line (`x_lp` and `y_lp` only). If they do not, the test fails with `pytest.fail("needs S11 (P0.9 three-source lpolyci)")`.
  - **Tag.** All three renderers carry the same `_dash_frozen` dict (`is`).
  - **After each `_MOVES` move.** The band, outline and line renderers are all muted. Each `muted_glyph`'s alphas are 0.3 × its glyph's. The caption is visible. The band's key and the line's key both end with `" (unfiltered)"`, and the scatter's key is unchanged.
  - **After `_back`.** Nothing is muted, the caption is hidden, and both keys equal the build's text.
  - **Empty case.** A second spec, `plot_for("lpolyci", if_expr="price > 20000")` beside a scatter, holds three empty sources. None of its renderers is ever muted under any move, because its member CDS has `data["id"] == []`.
- `TestTheCueClears::test_moving_back_to_every_row_clears_it[dropdown|range|slider]` — the move, then `_back`: nothing muted, the caption hidden, the labels equal the build's text exactly, the status `(False, "")` (red).
- `TestTheCueClears::test_a_second_move_keeps_it_and_the_reset_clears_it` — dropdown to Foreign, then the range to 4500-11385 (both remove rows): marked; then both back: cleared (red).
- `TestNoFalseCue::test_a_move_that_removes_only_rows_the_fit_never_used[y null|x null|weight null]`. `_DF` with mpg (or weight, or the aweight `w`) set to NaN on the five domestic rows, an lfit, and the dropdown to Foreign. The caption exists and stays hidden; nothing is muted. The snapshot holds null there, which guards `Number(null) === 0` (red: no caption).
- `TestNoFalseCue::test_the_slider_at_its_minimum_marks_nothing` — slider to `w.start`: hidden (Stata: SLIDERMIN N=10, same b; E-17.3) (red).
- `TestNoFalseCue::test_an_empty_fit_is_never_marked` — `plot_for("lfit", if_expr="price > 20000")` beside a scatter, each `_MOVES` move: never muted. Its config's `members` points at a member CDS with `data["id"] == []` (red).
- `TestNoFalseCue::test_row_layers_and_function_are_never_marked` — scatter, line, bar and function with a filter: no caption, no `stale_configs_json` arg (guard).
- `TestNoFalseCue::test_a_density_over_its_own_range_is_never_marked` — `plot_for("kdensity", {"range": "10 35"})`: no caption (guard).
- `TestTheWeightedSample`. Frame `_DF` with `w = [1, 0, 2, 1, 1, 3, 1, 2, 1, 1]` and `z = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]`, and a dropdown on `z` moved to 0, which drops only row 2, the zero-weight row:
  - `test_dropping_only_a_zero_weight_row_marks_nothing` — lfit `{"weight": "aweight", "wexp": "w"}`. Stata N=9 with or without the row, b=-0.00701112 (E-17.4). Hidden (red: no caption).
  - `test_dropping_a_positive_weight_row_marks_it` — `z` = 1 on row 1 instead (w=1): marked (red).
  - `test_dropping_the_negative_weight_rows_of_an_fpfit_marks_it` — fpfit `[aw=w]` with `w[3] = -1` and `z` = 1 on row 4. The build drew nothing (`wrule "any"`), and the move drops that row: marked (red).
  - `test_a_negative_weight_on_lfit_is_outside_the_sample` — lfit `[aw=w]` with `w[3] = -1`, dropping row 4: hidden (red).
  - `test_a_weight_twoway_refuses_is_not_read` — lowess `[aw=w]` (refused, drawn unweighted) dropping the zero-weight row: marked (red).
- `TestTheCueFollowsEachTarget` (all red):
  - `test_by_panels` — `go={"by": "foreign"}`, dropdown to Foreign: the Domestic panel's lfit is muted and its caption visible; the Foreign panel's is not.
  - `test_by_with_total` — `{"by": "foreign, total"}`: Domestic and Total are marked; Foreign is not (identify panels by `fig.title.text`).
  - `test_a_layers_own_if` — `plot_for("lfit", if_expr="foreign == 1")`: the dropdown to Foreign leaves it hidden; the range 4500-11385 (it drops the foreign car at 4453) marks it.
  - `test_an_excluded_graph_has_no_cue` — graphs g1 (scatter, lfit) and g2 (scatter, lfit), with `filters=[{"varname": "foreign", "type": "dropdown", "exclude": ["g1"]}]` (the `test_filter_exclude.py::_spec` form): g1 has no caption and no config; g2 is marked after the move.
  - `test_a_linked_pair` — g1 a scatter, g2 an lfit, `link: "g1 g2"`: g2 is marked.
  - `test_a_date_filter_and_a_fit_on_a_date_x` — `formats={"when": "%td"}`, `filter: "when, type(range)"`, `plot_for("lfit", xvar="when")`. Move to `(w.start + (w.end - w.start) / 2, w.end)`: marked; back to `(w.start, w.end)`: cleared.
  - `test_a_fit_on_the_second_axis` — `plot_for("lfit", {"yaxis": "2"})`: marked after the move.
  - `test_only_an_lfit_with_no_scatter_is_marked` — `[plot_for("lfit")]` alone: marked (the S14 contract).
- `TestNoCueWithoutAFilter::test_the_page_gains_no_model[no filter|a filter with a scatter only]` — no Title tagged `dash_stale_cue`, no Div tagged `dash_stale_status`, no `stale_` arg, and `muted_glyph` of every renderer is still Bokeh's own (guard).
- `TestTheStaleGlyph` (unit; red with AttributeError):
  - `test_colour_width_and_dash_are_kept_and_every_alpha_scaled` — a `Line(line_color="green", line_width=2, line_dash="dashed", line_alpha=0.8)` gives 0.24 and keeps the rest;
  - `test_alpha_zero_stays_zero_and_a_field_alpha_becomes_the_constant`;
  - `test_a_band_and_its_outline` — VArea gives `fill_alpha`/`hatch_alpha` × 0.3; Patch gives all three;
  - `test_it_follows_a_restyle_made_after_the_draw` — an lfit with `{"lcolor": "green", "lpattern": "dash"}` and a filter: after render, `muted_glyph.line_color == glyph.line_color` and `muted_glyph.line_dash == glyph.line_dash`.
- `TestTheStaleKind::test_each_type` — 11 fits → `"fit"`, histogram → `"bins"`, kdensity → `"grid"`, kdensity `range(10 35)` → None, kdensity `range(x)` → `"grid"` with no warning, scatter → None (red).
- `TestTheWeightColumn` (red):
  - `test_it_decides_as_layer_weights_does[none|missing|not-numeric|refused|inert|applied]`;
  - `test_the_value_state` — fpfit with a negative weight → `"negative"`; lfit → None; qfit fw 1.5 → `"nonint"`; positive → None.
- `TestTheWeightColumn::test_layer_weights_still_names_every_refusal[missing|not-numeric|refused|lowess|inert|negative|nonint|nonpositive]` — after `dr._dash_reset_notes()`, the warning text equals the literal HEAD message, written into the test from HEAD's `_layer_weights` (guard: it passes before and after the extraction).
- `TestTheFrozenTag::test_the_tag_of_each_kind` (red):
  - vars `[y, x]` for fits and `[var]` for histogram/kdensity;
  - `member_ids` absent for an unqualified layer, `[]` for `if price > 20000`, the panel's ids under `by(foreign)`;
  - `wvar`/`wrule` for each weight case;
  - None when a column is missing.
- `TestTheRegistry::test_one_entry_per_layer_by_figure` — two lfits in g1 and an lfit per by() panel (red).
- `TestTheCueArgs::test_the_models_and_lists` (red):
  - one caption per marked figure and one status Div, appended last before the CSV button;
  - member CDSs deduplicated by id set;
  - `json.loads(stale_configs_json)` holds no `member_ids` key;
  - every renderer's `muted_glyph` rebuilt;
  - each config's `items` text equals the legend label.
- `TestTheTitlePlacement` (red):
  - `test_the_cue_sits_nearest_the_frame_with_a_top_legend_and_subtitle` — `go={"title": "T", "subtitle": "S", "legend": "position(12)"}`: `[type(m).__name__ for m in fig.above] == ["Title", "Legend", "Label"]` and `fig.above[0].tags == ["dash_stale_cue"]`;
  - `test_no_marked_figure_has_its_toolbar_above` — over auto, bs, by() and a lone bs item: every figure with a caption has `toolbar_location != "above"`, and at least one figure has a caption.
- `TestThePageSize` (red):
  - `test_member_ids_are_one_shared_model_per_set` — `by(foreign)` scatter+lfit with 1 and with 3 filters: `stale_members` is the same list object on every callback, `len == 2`, the HTML holds `dash_stale_members` twice in both builds, and `len(stale_configs_json) < 2048`;
  - `test_page_size_grows_sublinearly_in_filters` — 4,000 rows (`np.random.default_rng(0)`, columns as E-17.6), `by(foreign)` lfit. `(html(4 filters) − html(1 filter))` for the lfit spec minus the same difference for a scatter-only spec is `< 3 * 2048` characters.
- `TestTheCueAgainstHostileInput` (red):
  - `test_a_hostile_label_is_data_not_markup` — a histogram whose variable label is `</p><img src=x onerror=alert(1)>`. After the move its legend label is that text plus `" (bins unfiltered)"`, as `{value}` (`.value`); the status text equals the constant; `cb.code == dr._FILTER_JS`; the page HTML holds no `<img src=x onerror` (case-insensitive).
  - `test_a_variable_named_proto_is_a_column` — `_DF` with mpg renamed `__proto__`, lfit `__proto__ weight`, the dropdown to Foreign: marked. With `__proto__` NaN on the domestic rows: hidden.
  - `test_every_callback_carries_the_same_lists` — three filters: every `stale_*` arg is the same object (`is`) on all three callbacks.
  - `test_the_block_is_last_and_declares_no_arg` — `dr._FILTER_JS` contains `if (typeof stale_configs_json !== "undefined")` after `for (let ai = 0; ai < agg_configs.length; ai++)`; `re.search(r"\b(const|let|var|function)\s+stale_", dr._FILTER_JS)` is None; `"dash_stale_" not in dr._FILTER_JS`.
  - `test_the_brush_code_holds_no_stale_block` — a spec with an `update(brush)` KPI, an lfit and a filter: no brush CustomJS code contains `stale_configs_json` (guard).
- `TestBothLayouts::test_the_title_is_in_each_figure_and_the_status_in_the_filter_area[auto-top|auto-left|bs-top|bs-left]` (red).
  - Every marked figure carries its caption.
  - On the plain path, the status Div is a descendant of the filter Row (top) or Column (left) of `r._last_layout_root`.
  - On bs, its `data-root-id` is inside the `<div class="db-row db-filter-bar">` chunk (top) or the `db-sidebar-col` chunk (left) of `r.render()`'s page.

**`test/test_help_claims_4.py::TestAFitLineOnAFilterMove::test_the_saved_page_marks_its_line`** — the existing spec and move: the line's data is unchanged AND its renderer is muted with the caption visible (red).

**`test/test_mode_parity.py`:**
- `TestTheServedAppHasNoStaleCue::test_no_model_tagged_dash_stale[lfit dropdown|histogram by() range|lfitci slider]` — the served document after `_served_after_move` holds no model whose tags start `dash_stale` and no muted renderer (guard);
- `TestTheGlyphProfile::test_it_records_muted` — a figure with one renderer muted shows `"muted": True` in `_glyph_profile` (guard once TR-12.12's key is added in 12-04).

**`test/test_stale_cue_browser.py` (new)** — `TestInChrome::test_bokehjs_marks_and_clears[auto-top|auto-left|bs-top|bs-left]` (red; skips without Chrome, red under `DASH_STRICT=1`).
- **Page.** It builds the saved page of `_spec([plot_for("scatter"), plot_for("lfit")], {"filter": "foreign, type(dropdown)", "layout": <l>, "filter_position": <p>}, {"title": "T", "subtitle": "S", "legend": "position(12)"})` with `r.render()`, and appends a probe `<script>` before `</body>`.
- **Probe, step 1.** It waits for `window.Bokeh.documents`, finds the `Select` model in any document, and snapshots across every document's `all_models`: `muted` of each `GlyphRenderer` whose glyph is a `Line`, `visible` of each `Title` whose `tags` include `dash_stale_cue`, the label `value` of each `LegendItem`, and the text of the first `[role="status"]` element found by walking shadow roots.
- **Probe, step 2.** It sets the Select to the option labelled Foreign and snapshots after 300 ms. It sets it back to the first option and snapshots after 300 ms. It writes `JSON.stringify` of the three snapshots into `<pre id="r">`.
- **Run.** Chrome is found by `responsive_probe.find_chrome()` and runs with `--headless=new --disable-gpu --no-first-run --no-default-browser-check --allow-file-access-from-files --user-data-dir=<tmp> --virtual-time-budget=9000 --dump-dom file://<page>`, polling the dump and killing the process as `responsive_probe` does.
- **Assert.**
  - before: muted `[false]`, caption `[false]`, label `Fitted values`, no status element;
  - after: `[true]`, `[true]`, `Fitted values (unfiltered)`, and the status text equals the constant's text content (`re.sub("<[^>]+>", "", dr._DASH_STALE_STATUS_HTML)`);
  - back: as before.

**`test/test_js_runner.py::TestTheNewWriteBacks`:**
- `test_muted_visible_and_label_round_trip` — a `run_code("r.muted = true; t.visible = true; d.visible = true; it.label = {value: 'x'};", {...})` commits all four into the Python models; `commit=False` commits none;
- `test_a_div_still_commits_its_text_and_a_widget_its_width` (guard).

**Cscripts.** SCU-01 (red: the saved state shows no caption), SCU-02 (red: no caption to be hidden), SCU-03 (red: the filter build holds 0 `dash_stale_cue`).

### P0.18 (base: commit 1)

**`test/test_mode_parity.py`:**
- `_MOVED_LAYERS += ["bar", "rbar", "lowess", "qfit", "fpfit", "mband", "mspline", "lpolyci", "qfitci", "fpfitci"]`. `TestAFilterMoveAgrees::test_same_glyphs_after_the_move[bar, dropdown to Foreign]` and the other five bar/rbar moves are red with `('[0]/coords/width[1]', 168.0, 56.0)`, 512 vs 56, and 0.8/0.64 vs 56. The other eight types are guards (E-18.5).
- `MOVE_CORPUS` gains `_move_case("bar under by(rep), dropdown", _MOVES[0], [plot_for("bar")], {"by": "rep"})`, `_move_case("rbar under by(foreign), range", _MOVES[1], [plot_for("rbar")], {"by": "foreign"})` and `_move_case("a linked pair with a bar, dropdown", _MOVES[0], graphs=[("g1", [_sc()]), ("g2", [plot_for("bar")])], bo={"link": "g1 g2"})` (red: widths 0.8/512/0.8 against 136/280/1824; the linked pair as measured in 12-14).
- `_EMPTYING_MOVES = [("slider to 10000", "price, type(slider)", ("Slider", 10000.0), "price >= 10000"), ("slider to 11385", "price, type(slider)", ("Slider", 11385.0), "price >= 11385")]` keep 2 and 1 rows. `_EMPTIED_LAYERS = ["lowess", "lfit", "qfit", "fpfit", "lpoly", "kdensity", "mband", "mspline", "histogram", "bar", "rbar", "rarea", "rspike"]`. `MOVE_CORPUS` gains:
  - `f"{t} emptied, {m[0]}"` for each type and each move;
  - `f"{t} with its own if emptied, slider to 10000"` with `plot_for(t, if_expr="foreign == 0")` (0 rows).

  Red where E-18.3 lists a bare empty glyph, e.g. lowess at 2 rows `('[0]/line_color', '#1f77b4', '#1a476f')`. Guard elsewhere.
- `CORPUS` gains `_case(f"{t} with its own if that keeps no row", [_sc(), plot_for(t, if_expr="price > 20000")])` for t in bar, rbar, rarea, rspike. Red in `TestTheTwoModesAgree`: the saved page is styled and the served one bare.

**`test/test_emptied_layer_style.py` (new):**
- `TestAnEmptiedLayerKeepsItsStyle::test_saved[<t>-<n>]` and `::test_served[<t>-<n>]`, for t in `_EMPTIED_LAYERS` and n in 0, 1, 2 (qualifier `price > 20000`, `>= 11385`, `>= 10000` on the second layer).
  - Each second-layer renderer's `(type, line_color, fill_color, line_width, line_dash, line_alpha, fill_alpha)` (those it has) equals the same layer's with no qualifier, and the legend labels equal too.
  - Red at base: lfit/qfit/fpfit at 0 and 1; lowess at 0, 1 and 2; lpoly and kdensity at 0 and 1; mband, mspline and histogram at 0 (both modes); bar, rbar, rarea and rspike at 0 (served).
- `TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour[<scheme>-<t>]` — for s2color and s1mono and every t whose `rows0` rc is 0 except histogram (P1.4): the saved page's empty second-layer colour (`line_color`, or `fill_color` for VArea) lower-cased is a colour of the fixture's `rows0.key_styles` (red: `#1f77b4`).
- `TestTheFixture::test_meta_is_stamped_and_the_selfchecks_held` — the four `_meta` keys exist and both self-checks read `held` (guard: 12-13 writes the fixture before these tests run).
- `TestTheEmptyFitLine` (red with AttributeError):
  - `test_it_draws_the_populated_style` — `_empty_fit_line(fig, "x", "y", {}, 1, "mpg")` on s2color equals `map_lfit`'s populated glyph style;
  - `test_it_takes_the_width_family_it_is_given`;
  - `test_mspline_and_mband_keep_their_own_width_family_when_empty` — `monkeypatch.chdir(tmp_path)`, write `w29lw.scheme` holding `#include s2color\nlinewidth plineplot vvthick\n`, and use `GlyphMapper(OptionTranslator(), SchemeParser("w29lw"))`:
    - `sp.plot_line_width(1, "lineplot") != sp.plot_line_width(1, "")`;
    - empty mspline and mband widths equal their populated widths and differ from lfit's.
- `TestTheHistogramQuads::test_the_empty_and_populated_quads_share_a_style` (red).
- `TestTheBarWidthFallback::test_one_rule_for_none_one_and_the_tag` — bar at 0 and 1 rows and its tag fallback are all 0.8; rbar's are all 0.64 (red: the empty bar is untagged).

**`test/test_glyphs.py`** — HARD-2 class: `test_<t>_empty_source_keeps_the_scheme_style` for histogram, bar, rbar, rarea and rspike. The empty glyph's colour equals `gm.scheme.default_color(0, <kind>)` with kind `histogram`, `bar`, `bar`, `rarea` and `rspike` (as each populated branch reads it) (red).

**`test/test_served_filter_move.py`:**
- `TestTheRedrawGeometry` (unit; red with AttributeError):
  - `test_a_bar_takes_the_redraws_width` — sources with `_dash_spacing_glyphs = [VBar(width=56)]` and `[VBar(width=168)]`: the live width becomes 168;
  - `test_an_untagged_source_is_left_alone`;
  - `test_a_non_finite_or_non_positive_width_is_ignored[nan|inf|0|-1|text|None]`;
  - `test_extra_glyphs_are_zipped_to_the_shorter`.
- `TestTheServedBarAfterAMove::test_the_served_width_is_the_kept_rows_spacing[bar|rbar]` — `_served_after_move` on `_DF` with the dropdown to Foreign: width 168 (red: 56).

**Registry guards, unchanged:** `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` stay green with the new copy-list entry. They go red if the emitted call lands without it.

**Cscripts.** EW-01 (red: the served width is unchanged by the move), EW-02 (red: dash's empty lfit is `#1f77b4` where twoway keys `#90353b`), EW-03 (red: lowess `#1f77b4`/1).

**Mutation table.**

| break this | test that must die |
|---|---|
| tag only the first or the last renderer of a layer (S11's lpolyci band source left unmarked) | `TestTheCueAppearsOnAMove::test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked` |
| count a removed row whose y is null (`Number(v)`) | `TestNoFalseCue::test_a_move_that_removes_only_rows_the_fit_never_used[y null]` |
| count a zero-weight row | `TestTheWeightedSample::test_dropping_only_a_zero_weight_row_marks_nothing` |
| treat `member_ids == []` as every row | `TestNoFalseCue::test_an_empty_fit_is_never_marked` |
| put member ids in `stale_configs_json` | `TestThePageSize::test_member_ids_are_one_shared_model_per_set` |
| append the caption to `fig.above` | `TestTheTitlePlacement::test_the_cue_sits_nearest_the_frame_with_a_top_legend_and_subtitle` |
| keep Bokeh's auto muted glyph | `TestTheStaleGlyph::test_it_follows_a_restyle_made_after_the_draw` |
| not reset labels on moving back | `TestTheCueClears::test_moving_back_to_every_row_clears_it` |
| splice the label into HTML | `TestTheCueAgainstHostileInput::test_a_hostile_label_is_data_not_markup` |
| read `orig[name]` without the own-property check | `TestTheCueAgainstHostileInput::test_a_variable_named_proto_is_a_column` |
| drop `_dash_copy_redraw_geometry` from the emitted step 3 | `TestTheServedBarAfterAMove`, `TestAFilterMoveAgrees[bar, …]`, EW-01 |
| hard-code `"lineplot"` in `_empty_fit_line` | `TestTheEmptyFitLine::test_mspline_and_mband_keep_their_own_width_family_when_empty` |
| leave map_rbar's empty early return | `TestAnEmptiedLayerKeepsItsStyle::test_served[rbar-0]`, `TestTheBarWidthFallback` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Marked after a move that removes sample rows; cleared on moving back | pytest + node (`JsSession`) | none (rows in the test) | saved; served pinned to no cue |
| lpolyci's three S11 sources (band, outline, line) marked and cleared together; an empty lpolyci never marked (C1) | pytest + node | none | saved |
| No false cue (null cells, zero weight, empty fit, slider minimum, own if) | pytest + node | E-17.3/E-17.4 values inline | saved |
| Weighted sample equals `_layer_weights`' | pytest unit + node | none | saved |
| by(), total, own if, exclude(), link(), date, axis(2), fit alone | pytest + node | none | saved |
| Caption order, toolbar guard, layouts auto/bs × top/left | pytest | none | saved |
| BokehJS semantics of muted/visible/label and the DOM status | headless Chrome | none | saved |
| Page size: member ids once | pytest | none | saved |
| Hostile label and `__proto__` | pytest + node | none | saved |
| Served refits and carries no cue | pytest (parity file) | none | served |
| Saved after move vs served refit vs Stata's regress | cscript SCU-01..03 | none (Stata live) | both |
| Served bar/rbar width after a move | pytest parity `TestAFilterMoveAgrees`, unit tests of the helper | none | both |
| Emptied layer style equals populated, both modes | pytest | none | both |
| Emptied layer colour equals twoway's key | pytest | `emptied_layer_truth.json` | saved |
| Bar width three ways after a move | cscript EW-01 | none | both |
| Emptied layer vs live twoway export | cscript EW-02, EW-03 | none (Stata live) | both |

Acceptance criteria:
- **AC-12.1** `python3 -m pytest test/test_saved_stale_cue.py test/test_emptied_layer_style.py test/test_js_runner.py test/test_help_claims_4.py test/test_saved_filter_layers.py test/test_served_filter_move.py test/test_glyphs.py -q -n0 -p no:cacheprovider` passes, and the node tests ran (not skipped).
- **AC-12.2** `python3 -m pytest test/test_mode_parity.py -q` passes with every new `MOVE_CORPUS` and `CORPUS` entry, and `ALLOWED` and `_MUST_WARN` are byte-identical to the base (`git diff <base> -- test/test_mode_parity.py | grep -c '^[-+].*ALLOWED\|_MUST_WARN'` prints 0).
- **AC-12.3** `test/test_stale_cue_browser.py` passes in headless Chrome for the four layouts.
- **AC-12.4** The driver logs show `SCU-01 PASS`, `SCU-02 PASS`, `SCU-03 PASS` and `EW-01 PASS` in `test_e2e_filters.cscript`, and `EW-02 PASS` and `EW-03 PASS` under `WP29_ONLY=S12` in `test_wp29_truth.cscript`, with no ` FAIL` and no `r(` error.
- **AC-12.5** The registry tests (R2) pass, and `test/fixtures/emptied_layer_truth.json` is tracked with its `_meta` stamp.
- **AC-12.6** BUGS.md closes both entries in place, naming existing tests. CHANGELOG has no `<!-- WP-29 P0.17 -->` or `<!-- WP-29 P0.18 -->` left, and `WP29_OPEN` has no `"P0.17"` or `"P0.18"` key. `test_tracking_documents.py` passes.

## Tasks

**Commit boundary.**
- **Commit 1 (P0.17)** holds 12-01 to 12-12, subject `Mark the layers a saved page does not recompute after a filter move (WP-29 P0.17)`.
- **Commit 2 (P0.18)** holds 12-13 to 12-20, subject `Redraw served bar widths and keep an emptied layer's style (WP-29 P0.18)`.

Both are made on `wp29-s12` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s12` (`<W>`). Each body opens with its saved failure text and then carries, one per line:
- `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`, where `<sha>` is `<scratch>/batch-2-s12-base.txt` (C1) for P0.17 and commit 1's sha for P0.18;
- `Flipped:`;
- `Fixture: test/fixtures/emptied_layer_truth.json (scripts/extract_emptied_layer_truth.do)` (P0.18 only);
- `BUGS.md: "<title>" (closed)`;
- the impact results of 12-01.

No AI reference and no co-author trailer appear anywhere (CLAUDE.md rule 6). Every Stata run is `dash_nobrowser=1 scripts/stata_slot.sh <scratch> <file>.do` (rule 10). pytest runs the changed files while iterating, and the full suite once per commit (rule 11).

<task type="auto" id="12-01">
  <name>Record the blast radius before editing</name>
  <files>none</files>
  <action><![CDATA[
**Precondition (amendment C1).** Before anything else, confirm the worktree was cut after S11 landed:
- `git -C <W> rev-parse HEAD` equals `<scratch>/batch-2-s12-base.txt`;
- `git -C <W> log --format=%s | grep -cE '\(WP-29 P0\.(7|9)\)'` prints 2;
- `python3 -c "import sys, inspect; sys.path.insert(0, '<W>'); import dash_render as d; print('band_source' in inspect.signature(d.GlyphMapper._render_ci_band).parameters)"` prints `True` (S11's TR-11.16; at `7421d3d` it prints `False`).

If any check fails, stop and report to the orchestrator. Never cut or rebase the worktree yourself.

In `<W>` run `npx gitnexus analyze`; the index lacks this repository at plan time (E-12.0). Never stage the `.gitnexus/` it writes.

Run `gitnexus_impact({target, direction: "upstream"})` for each of these targets:
- `GlyphMapper._layer_weights`, `DashRenderer._make_figure_body`, `DashRenderer._build_filter_widgets`, `DashRenderer.render`;
- `GlyphMapper.map_bar`, `map_rbar`, `map_rarea`, `map_rspike`, `map_lfit`, `map_qfit`, `map_lowess`, `map_lpoly`, `map_fpfit`, `map_kdensity`, `map_histogram`, `map_mspline`, `map_mband`;
- `ServerAppBuilder._generate_app_source`;
- `JsSession.run_code` and `stand_in` in test/js_runner.py.

Write each risk level, direct-caller count and affected process into `<scratch>/12-impact.txt`. Report every HIGH or CRITICAL result to the maintainer in this agent's output BEFORE any edit (index R8; `_make_figure_body` and `_layer_weights` are expected HIGH). Edit nothing.
  ]]></action>
  <verify><![CDATA[The three precondition checks print the stated values; `test -s <scratch>/12-impact.txt` succeeds; `git -C <W> status --porcelain | grep -v '^?? .gitnexus' | wc -l` prints 0.]]></verify>
  <done>The blast radius of every symbol this section edits was recorded and every HIGH or CRITICAL result was reported before any edit.</done>
</task>

<task type="auto" id="12-02">
  <name>Teach the node runner the new write-backs</name>
  <files>test/js_runner.py, test/test_js_runner.py</files>
  <action><![CDATA[
Apply TR-12.13 to `test/js_runner.py`:
- in `stand_in`, encode GlyphRenderer (`muted`, `visible`), Title (`visible`), LegendItem (`label` as `{"value": text}`) and Div (`text`, `visible`), importing `GlyphRenderer`, `LegendItem` and `Title` from `bokeh.models`;
- in `RUNNER`'s output, give each non-source, non-filter model every one of `text`, `width`, `visible`, `muted` and `label` that its stand-in has;
- in `run_code`, replace the `elif` write-back with independent `if` blocks: `visible` and `muted` only when bool, `width` only when a number, and `label` through `bokeh.core.properties.value`;
- in `state()`, add the `muted`, `visible` and `labels` maps;
- add one docstring sentence naming WP-29 S12.

Add `TestTheNewWriteBacks` with its two tests to `test/test_js_runner.py`. Touch no product file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_js_runner.py test/test_saved_filter_layers.py test/test_filter_exclude.py -q -n0 -p no:cacheprovider 2>&1 | tail -2` reports 0 failed and no new skips.]]></verify>
  <done>The node runner committed muted, visible and label back into the Python models, independently of each other, and every existing caller passed unchanged.</done>
</task>

<task type="auto" id="12-03">
  <name>Write the failing stale-cue unit and node tests</name>
  <files>test/test_saved_stale_cue.py</files>
  <action><![CDATA[
Create `test/test_saved_stale_cue.py` with the module docstring:
- what P0.17 is;
- decision M3;
- the measured symptom of E-17.1;
- the Stata numbers of E-17.3 and E-17.4 quoted as the oracle.

Write the helpers and every test of "TDD test stubs, P0.17, test/test_saved_stale_cue.py" with exactly those class and test names. Derive expected ids, rows and panels from the frames in the test with pandas, never from literals. Write the HEAD warning texts of `test_layer_weights_still_names_every_refusal` by copying them from HEAD's `_layer_weights` (dash_render.py:8451-8536) and run that test first: it must pass at base.

Run the file against the unmodified tree. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_stale_cue.py -q -n0 -p no:cacheprovider 2>&1 | tail -3` collects without error. It fails every test the stubs mark red, with `no Title tagged dash_stale_cue` or `has no attribute` messages, and passes exactly the guards: `TestNoFalseCue::test_row_layers_and_function_are_never_marked`, `::test_a_density_over_its_own_range_is_never_marked`, `TestNoCueWithoutAFilter` (2), `TestTheWeightColumn::test_layer_weights_still_names_every_refusal` (8) and `TestTheCueAgainstHostileInput::test_the_brush_code_holds_no_stale_block`.]]></verify>
  <done>Every stale-cue regression test in the new file existed and failed for its recorded reason on the S12 base (`<scratch>/batch-2-s12-base.txt`, C1), while the guards passed.</done>
</task>

<task type="auto" id="12-04">
  <name>Write the remaining failing P0.17 tests</name>
  <files>test/test_help_claims_4.py, test/test_mode_parity.py, test/test_stale_cue_browser.py</files>
  <action><![CDATA[
Make these changes:
1. Add `TestAFitLineOnAFilterMove::test_the_saved_page_marks_its_line` to `test/test_help_claims_4.py`.
2. In `test/test_mode_parity.py`:
   - add `entry["muted"]` to `_glyph_profile` (TR-12.12, third bullet only; the skip helper comes in 12-09);
   - add `TestTheServedAppHasNoStaleCue` and `TestTheGlyphProfile`;
   - leave `ALLOWED` and `_MUST_WARN` untouched.
3. Create `test/test_stale_cue_browser.py` as the stubs specify, following `test/responsive_probe.py`'s Chrome lookup, `--dump-dom` polling and temporary-profile cleanup. Skip with a reason naming `DASH_CHROME` when `find_chrome()` is None.

Run the three files and `test/test_saved_stale_cue.py` against the unmodified tree. Save the complete failure output (node ids and assertion text, Chrome included when present) to `<scratch>/12-P0.17-failure.txt`. The cscript cases SCU-01..03 are written in 12-10 and run red there against a stashed dash_render.py. Do not commit.
  ]]></action>
  <verify><![CDATA[- `python3 -m pytest test/test_help_claims_4.py test/test_mode_parity.py test/test_stale_cue_browser.py -q -n0 -p no:cacheprovider -k "marks_its_line or NoStaleCue or GlyphProfile or InChrome" 2>&1 | tail -3` fails `test_the_saved_page_marks_its_line` and the four Chrome cases (when Chrome is present) and passes `TestTheServedAppHasNoStaleCue` and `TestTheGlyphProfile`.
- `python3 -m pytest test/test_mode_parity.py -q 2>&1 | tail -1` reports 0 failed.
- `<scratch>/12-P0.17-failure.txt` exists.]]></verify>
  <done>Every P0.17 pytest and browser regression test existed and failed on the S12 base (`<scratch>/batch-2-s12-base.txt`, C1), the parity profile recorded muted, and the failure text was saved.</done>
</task>

<task type="auto" id="12-05">
  <name>Extract the weight decision and add cue helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Make these changes in `dash_render.py`:
- Apply TR-12.4: add `GlyphMapper._layer_weight_column` and `GlyphMapper._layer_weight_values_state` beside `_layer_weights`, and rewrite `_layer_weights` to call them, keeping S05's `units=` keyword, every `_dash_warn_once` key and every message character for character.
- Add the TR-12.1 constants after `_DASH_COMPUTED_ONLY_TYPES`.
- Add `_dash_stale_kind` (TR-12.2) and `_dash_stale_glyph` (TR-12.3) after the constants.

Add the four keys to `test/function_test_map.py` in alphabetical place, naming `TestTheWeightColumn::test_it_decides_as_layer_weights_does`, `::test_the_value_state`, `TestTheStaleKind::test_each_type` and `TestTheStaleGlyph::test_colour_width_and_dash_are_kept_and_every_alpha_scaled`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_stale_cue.py -q -n0 -p no:cacheprovider -k "WeightColumn or StaleKind or (StaleGlyph and not restyle)" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k LayerWeights` passes; `python3 scripts/fncov/fncov_mutate.py --map --keys GlyphMapper._layer_weight_column,GlyphMapper._layer_weight_values_state,_dash_stale_kind,_dash_stale_glyph` reports each key's test failing with the body skipped.]]></verify>
  <done>The weight acceptance and value decisions became two tested helpers that _layer_weights used with unchanged behaviour, and the cue constants and its two pure helpers existed with map entries.</done>
</task>

<task type="auto" id="12-06">
  <name>Tag frozen layers and collect the registry</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Apply TR-12.5:
- the `_frozen_vars` captures in the `_UNIVARIATE_TYPES` and default dispatch branches of `DashRenderer._make_figure_body`;
- the tagging block after `_plot_renderers.append((plot, _layer_renderers))`.

Add `DashRenderer._frozen_layer_tag` (TR-12.6, with the step 3b member rule copied exactly) and `DashRenderer._collect_frozen_layers` (TR-12.7). Add step 3d to `render()` after 3c. Change no other line of `_make_figure_body`. S07's registration hunk and S05's hunks above stay as they are.

Add both keys to `test/function_test_map.py` (`TestTheFrozenTag::test_the_tag_of_each_kind`, `TestTheRegistry::test_one_entry_per_layer_by_figure`).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_stale_cue.py -q -n0 -p no:cacheprovider -k "FrozenTag or Registry" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_mode_parity.py test/test_per_plot_qualifier_linking.py -q 2>&1 | tail -1` reports 0 failed.]]></verify>
  <done>Every renderer of a frozen layer carried one tag naming its kind, variables, weight rule and member rows, and render() collected them by figure.</done>
</task>

<task type="auto" id="12-07">
  <name>Build the cue models and callback args</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Add `DashRenderer._stale_cue_args` as TR-12.8 specifies, importing `Title` and `Legend` from `bokeh.models` where dash_render.py imports its models. Wire it in `_build_filter_widgets` as TR-12.9 specifies:
- one call;
- the same objects on every callback;
- no change to `build_dropdown`, `build_slider` or `build_range`.

Add the key to `test/function_test_map.py` (`TestTheCueArgs::test_the_models_and_lists`). The JS block is 12-08's, so the node tests still fail here.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_stale_cue.py -q -n0 -p no:cacheprovider -k "CueArgs or TitlePlacement or PageSize or NoCueWithoutAFilter or every_callback or restyle" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_filter_payload_size.py test/test_filter_exclude.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed.]]></verify>
  <done>A saved page with a frozen layer a filter reaches carried one hidden caption per marked figure at index 0 of fig.above, rebuilt muted glyphs, one hidden status Div in the filter area and one shared member source per distinct row set, with every callback holding the same args.</done>
</task>

<task type="auto" id="12-08">
  <name>Add the stale block to the filter script</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Append TR-12.10's block to `_FILTER_JS` as its last top-level statement, after the closing brace of the aggregate loop and before `""").replace("__DASH_ROW_ID__", ...)`, character for character. Change no other script line.

Confirm the slices still find their markers:
- `test/js_runner.py`'s `run_filter_js_block`;
- the brush wiring;
- `test_kpi_brush.py`'s marker.

Measure one move on a 100,000-row page (`np.random.default_rng(0)`; scatter, lfit and histogram; one dropdown) under node with `time.perf_counter()` around `JsSession.run`, against the same page without the lfit and histogram. Write both times into `<scratch>/12-timing.txt` for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_stale_cue.py test/test_help_claims_4.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py test/test_kpi_brush.py test/test_js_runner.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `test -s <scratch>/12-timing.txt` succeeds.]]></verify>
  <done>The saved page marked, and on moving back cleared, every frozen layer whose estimation sample a move cut, under node, with the block last in the script and no arg name redeclared.</done>
</task>

<task type="auto" id="12-09">
  <name>Skip the status note in parity readers</name>
  <files>test/test_mode_parity.py, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
In `test/test_mode_parity.py`:
- add `_is_stale_status` above `_layout_tree`;
- use it in `_layout_tree`'s list branch and in `_bs_markup_page`'s filter-bar comprehension, exactly as TR-12.12 specifies;
- add `TestTheStaleStatusSkip` with two tests:
  - `test_only_a_div_tagged_dash_stale_status_is_skipped` (a Div tagged otherwise is kept);
  - `test_a_saved_page_with_a_fit_and_a_filter_compares_equal_to_its_served_twin` (the `_render_pair` trees of `[_sc(), plot_for("lfit")]` with a dropdown are equal).

Do not edit `ALLOWED` or `_MUST_WARN` (R6, D12-1).

In `test/test_saved_filter_layers.py`, change the comment above `_ROW_TYPES` from "is not redrawn" to "is not refitted, and is marked (WP-29 P0.17)" and record the `Flipped:` line in `<scratch>/12-flips.txt`.

Run `test/test_stale_cue_browser.py`, which must now pass in Chrome.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_toolbar.py test/test_saved_filter_layers.py test/test_stale_cue_browser.py -q 2>&1 | tail -1` reports 0 failed with the Chrome cases run (not skipped) when Chrome is installed; `git diff -- test/test_mode_parity.py | grep -c '^[-+]ALLOWED\|^[-+]_MUST_WARN'` prints 0.]]></verify>
  <done>The parity readers ignored only the saved page's hidden status note, through the existing allowance, and the browser test proved BokehJS marked and cleared the layer in both layouts and both filter positions.</done>
</task>

<task type="auto" id="12-10">
  <name>Certify the cue against Stata's regress</name>
  <files>test/filter_truth_check.py, test/test_e2e_filters.cscript</files>
  <action><![CDATA[
Add `fit_graph`, `bar_graph`, `stale_state`, `served_stale_models`, `line_ends` and `vbar_width` to `test/filter_truth_check.py` (TR-12.20), each with a docstring naming its cases.

Append SCU-01, SCU-02 and SCU-03 to `test/test_e2e_filters.cscript` after S07's QF cases and before `// Cleanup`, as "Stata truth" specifies:
- the truth is computed in Stata into globals before each `python:` block;
- the Python reads it through `sfi.Macro.getGlobal` and calls `ftc.put("scu_0n", int(ok))`;
- after `end`: `assert "${scu_0n}" == "1"` and `display "SCU-0n PASS: ..."`;
- each case sits inside `preserve`/`restore`, with `dash clear` where `dash` commands are used;
- add the three ids to the header's `Tests:` comment.

Run the script through the driver once with this cycle's dash_render.py stashed (`git -C <W> stash push dash_render.py`), append its SCU lines to `<scratch>/12-P0.17-failure.txt`, `git -C <W> stash pop`, and run it again.
  ]]></action>
  <verify><![CDATA[The red run's log shows the first SCU assertion failing with `assertion is false` and `r(9);`. The green run's `<scratch>/run_test_e2e_filters.log` contains `SCU-01 PASS`, `SCU-02 PASS`, `SCU-03 PASS` and `All filter widget E2E tests PASSED.`, with no `r(` error before the last line.]]></verify>
  <done>Stata itself certified that the saved page marked the lfit a move left stale and cleared it on moving back, that the served refit equalled regress on the kept rows, and that a page without a filter carried no cue model.</done>
</task>

<task type="auto" id="12-11">
  <name>Document P0.17 in help, BUGS and CHANGELOG</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
**dash.sthlp, the comparison table** (about :1378-1381). Change the three rows to:
- `Histogram recompute on filter{col 38}heights; bins marked{col 59}heights and bins`
- `Kernel density on filter{col 38}same grid, marked{col 59}grid recomputed`
- `Fit-line recompute on filter{col 38}No; marked{col 59}Yes`

**dash.sthlp, "What a filter move redraws".** Keep S02's and S07's sentences as they stand on the tree. Replace only `; it does not redraw a fitted line.` with: `; it does not refit a fitted or smoothed line ({cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}, {cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci}, {cmd:mband}, {cmd:mspline}).  When a move removes observations such a line, a histogram's bins or a density's grid was computed from, the page marks the layer: it is dimmed, its legend key reads "(unfiltered)", "(bins unfiltered)" or "(grid unfiltered)", the graph shows "Marked layers were computed before the filter", and a note under the filters says the same in text a screen reader reads.  A density drawn over {cmd:range()} keeps the grid you gave and is not marked.  The marks go when the filters again keep every observation the layer was computed from; a move that removes only observations the layer never used (a missing y, x or weight, a zero weight, or one outside the plot's own {cmd:if} or {cmd:in}) marks nothing, and a graph {cmd:exclude()} protects is never marked.`

**test/test_kpi_brush.py:7-8.** Update the docstring rows to the new table text (12-12 stages it).

**BUGS.md.** Find the P0.17 entry (`grep -n "WP-29 section 12" BUGS.md`, the one about saved fits). Change `- [ ]` to `- [x]` in place and rewrite its Resolution line: `  - Resolution: Fixed <ddmonyyyy> (WP-29, P0.17). The saved page marks a fit, smooth, histogram or kernel density (lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline, histogram, kdensity without range()) while the filters that reach it have removed a row of its estimation sample: the layer is dimmed to 30 percent of its alphas, its legend key gains (unfiltered), (bins unfiltered) or (grid unfiltered), its graph shows a caption and one role=status line in the filter area says the same; moving back clears every mark. Built by DashRenderer._frozen_layer_tag, _collect_frozen_layers and _stale_cue_args and the last block of _FILTER_JS; the sample is the one GlyphMapper._layer_weights fits from (_layer_weight_column, _layer_weight_values_state). The served app refits and carries no cue. Pinned by test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_a_layer_the_move_took_rows_from_is_marked, ::TestTheWeightedSample::test_dropping_only_a_zero_weight_row_marks_nothing, ::TestTheCueClears::test_moving_back_to_every_row_clears_it, test/test_stale_cue_browser.py::TestInChrome::test_bokehjs_marks_and_clears, test/test_e2e_filters.cscript SCU-01. Residual, deferred (WP-29): the saved page still does not refit (decision M3, GAPS2 C4 plan items 1-2) and prints no build-time note (DISCOVERY Q22).`

**CHANGELOG.md.** Replace `<!-- WP-29 P0.17 -->` under `### Fixed in WP-29` in place with ONE item ending `(WP-29, P0.17)`: `- A saved page now marks a fitted or smoothed line, a histogram's bins and a density's grid that a filter move left computed from observations the filter removed: the layer is dimmed, its legend key gains (unfiltered), (bins unfiltered) or (grid unfiltered), the graph shows a caption and the filter area a status line. Before, dash (scatter mpg weight) (lfit mpg weight) with filter(foreign) kept the all-rows line (29.105 at weight 1800, where the Foreign cars' fit is 29.917) under the filtered points with no sign that it ignored the filter. The served app refits as before (WP-29, P0.17)`.

Grep the three files for `claude|anthropic` (none).
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-29 P0.17 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.17)' CHANGELOG.md BUGS.md | awk -F: '{s+=$2} END {print s}'` prints 2; `grep -c 'No; marked' dash.sthlp` prints 1; `git -C <W> diff -- dash.sthlp BUGS.md CHANGELOG.md | grep -ciE '^\+.*(claude|anthropic)'` prints 0.]]></verify>
  <done>The help stated what a saved page marks and when, the P0.17 entry was closed in place naming existing tests, and its CHANGELOG marker was replaced by one item.</done>
</task>

<task type="auto" id="12-12">
  <name>Close P0.17 and make commit one</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
Delete only the `"P0.17": ...` line of `WP29_OPEN` in `test/test_tracking_documents.py`.

Run, in order:
1. `python3 -m pytest test/test_tracking_documents.py test/test_function_test_map.py test/test_statistical_helpers.py -q -n0 -p no:cacheprovider`.
2. `gitnexus_detect_changes()`, which must name only this section's symbols.
3. The full suite once: `python3 -m pytest test/ -q`. Read its log and never relaunch. A pin it exposes that 12-09 did not list is flipped in place, with a `Flipped:` line added to `<scratch>/12-flips.txt`. Any other failure is a defect of this cycle and is fixed in the code.
4. The 12-10 driver run.

Then:
- stage only these files: dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, test/js_runner.py, test/test_js_runner.py, test/test_saved_stale_cue.py, test/test_stale_cue_browser.py, test/test_help_claims_4.py, test/test_mode_parity.py, test/test_saved_filter_layers.py, test/test_kpi_brush.py, test/function_test_map.py, test/filter_truth_check.py, test/test_e2e_filters.cscript, test/test_tracking_documents.py;
- write the message (the subject of "Commit boundary"; the body opening with `<scratch>/12-P0.17-failure.txt`, then the measured defect, what changed, `Regression:` lines, the `Flipped:` lines from `<scratch>/12-flips.txt`, `BUGS.md: "<title>" (closed)`, the 12-01 impact summary and the 12-08 timing);
- grep it for `claude|anthropic` before and after committing;
- commit on `wp29-s12`.
  ]]></action>
  <verify><![CDATA[The full suite's last line reports 0 failed and no new skips; `git -C <W> log -1 --format=%s | grep -c '(WP-29 P0.17)'` prints 1; `git -C <W> log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0; `git -C <W> show --stat HEAD | grep -cE 'CLAUDE.md|\.gitignore|\.gitnexus|\.html'` prints 0.]]></verify>
  <done>P0.17 was closed in one green commit on wp29-s12 holding its failing tests, the fix, the flips and the closed entry.</done>
</task>

<task type="auto" id="12-13">
  <name>Extract twoway's emptied-layer key truth</name>
  <files>scripts/extract_emptied_layer_truth.do, test/fixtures/emptied_layer_truth.json</files>
  <action><![CDATA[
Create `scripts/extract_emptied_layer_truth.do` exactly as "Stata truth, Fixture" specifies (probes, key-style reader, `_meta` stamp, both self-checks, erase the SVGs). Run it through the wrapper with `DASH_REPO=<W>` and read the log once it ends.

Then:
- confirm the expected values listed under "Stata truth" probe by probe;
- check that both self-checks read `held`;
- `git -C <W> add -f test/fixtures/emptied_layer_truth.json`.

A value that differs from E-18.4 is reported to the maintainer, not patched (R5).
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/emptied_layer_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));assert m['empty_matches_populated']=='held' and m['base_has_no_layer_colour']=='held';p=d['schemes']['s2color']['probes'];assert p['lfit']['rows0']['key_styles']==[['#90353b',8.64]] and p['bar']['rows0']['key_styles']==[['#90353b',5.76]] and p['fpfit']['rows0']['rc']==198 and p['lpoly']['rows0']['rc']==2000"` prints nothing; `git -C <W> ls-files test/fixtures/emptied_layer_truth.json` prints the path.]]></verify>
  <done>twoway's legend key style for every computed, bar and range layer at 0, 1 and 2 rows under s2color and s1mono was recorded with its rc in a stamped, committed-ready fixture.</done>
</task>

<task type="auto" id="12-14">
  <name>Write the failing emptied-style and parity tests</name>
  <files>test/test_mode_parity.py, test/test_emptied_layer_style.py, test/test_glyphs.py</files>
  <action><![CDATA[
Make these changes:
1. In `test/test_mode_parity.py`, extend `_MOVED_LAYERS`, add the three `MOVE_CORPUS` cases, `_EMPTYING_MOVES`, `_EMPTIED_LAYERS`, their `MOVE_CORPUS` entries and the four `CORPUS` entries, as "TDD test stubs, P0.18" specifies. Do not touch `ALLOWED` or `_MUST_WARN`. If a new `CORPUS` entry differs at base only in warnings, which this section does not change, remove that entry and record it in `<scratch>/12-notes.txt` for the closeout rather than editing `_MUST_WARN`.
2. Create `test/test_emptied_layer_style.py` with every class of the stubs.
3. Add the five HARD-2 style tests to `test/test_glyphs.py`.

Run the three files against the tree commit 1 left and save the complete failure output to `<scratch>/12-P0.18-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_emptied_layer_style.py test/test_glyphs.py -q 2>&1 | tail -3` fails:
- the six bar/rbar `_MOVED_LAYERS` moves (`168.0, 56.0` and the rest);
- the two by() cases;
- the emptying cases E-18.3 predicts;
- the four `CORPUS` empty-layer cases;
- the red classes of the new file and the five HARD-2 style tests.

It passes every guard listed in the stubs. `<scratch>/12-P0.18-failure.txt` exists.]]></verify>
  <done>Every P0.18 parity and style regression test existed and failed for its recorded reason on commit 1's tree, while the guards passed.</done>
</task>

<task type="auto" id="12-15">
  <name>Write the failing served-geometry unit tests</name>
  <files>test/test_served_filter_move.py</files>
  <action><![CDATA[
Add `TestTheRedrawGeometry` (four tests) and `TestTheServedBarAfterAMove` (bar and rbar) to `test/test_served_filter_move.py` as the stubs specify:
- import `VBar` from `bokeh.models`;
- reach the helper as `dr._dash_copy_redraw_geometry`, so collection succeeds before it exists.

Run the file and append its failures to `<scratch>/12-P0.18-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_filter_move.py -q -n0 -p no:cacheprovider -k "RedrawGeometry or ServedBarAfterAMove" 2>&1 | tail -2` reports 6 or more failed (AttributeError for the unit tests, `56.0` for the served widths) and no collection error.]]></verify>
  <done>The served width regression and the new helper's unit tests existed and failed on commit 1's tree.</done>
</task>

<task type="auto" id="12-16">
  <name>Copy the redrawn width in the served app</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Apply TR-12.15:
- add `_dash_copy_redraw_geometry` after `_dash_keep_jitter`;
- add its copy-list entry after `"_dash_keep_jitter",` (R2);
- emit the four lines after the `_live.data = _dash_keep_jitter(...)` statement in `ServerAppBuilder._generate_app_source`'s step 3, with the surrounding 20-space indent.

Add `_dash_copy_redraw_geometry` to `test/function_test_map.py` (`TestTheRedrawGeometry::test_a_bar_takes_the_redraws_width`).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_filter_move.py -q -n0 -p no:cacheprovider -k "RedrawGeometry or ServedBarAfterAMove" 2>&1 | tail -1` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py -q -n0 -p no:cacheprovider -k "CarriesEveryName or DefinesEveryNameItReads"` passes; `python3 -m pytest test/test_mode_parity.py -q -k "bar or rbar" 2>&1 | tail -1` shows the width cases passing.]]></verify>
  <done>After a served move, every bar and rbar took the width its redraw drew from the kept rows, as the saved page draws it.</done>
</task>

<task type="auto" id="12-17">
  <name>Draw every empty layer in its own style</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Apply in `dash_render.py`:
- **TR-12.16:** add `GlyphMapper._empty_fit_line` and replace each bare empty line of E-18.3 with it, passing `width_kind=""` in map_mspline and map_mband;
- **TR-12.17:** add `GlyphMapper._histogram_quads` and route map_histogram's three quad calls through it;
- **TR-12.18:** fall through to the styled path in map_bar, map_rbar, map_rarea and map_rspike, with the single fallback expressions.

The worktree was cut after S11 landed (C1; 12-01 checked it), so map_lpoly's empty branch is S11's text: replace only its bare `fig.line(...)` call. Keep every `_mark_*` call. Leave map_lpolyci's empty branch alone: S11 routes it through `_render_ci_band` with three empty sources.

Add `GlyphMapper._empty_fit_line` (`TestTheEmptyFitLine::test_it_draws_the_populated_style`) and `GlyphMapper._histogram_quads` (`TestTheHistogramQuads::test_the_empty_and_populated_quads_share_a_style`) to `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_emptied_layer_style.py test/test_glyphs.py test/test_mode_parity.py test/test_function_test_map.py -q 2>&1 | tail -1` reports 0 failed; `awk '/def map_lfit/,/def map_rconnected/' dash_render.py | grep -cE 'fig\.(line|vbar|varea|segment|quad)\([^)]*source=empty'` prints 0; `python3 scripts/fncov/fncov_mutate.py --map --keys GlyphMapper._empty_fit_line,GlyphMapper._histogram_quads,_dash_copy_redraw_geometry` reports each key's test failing with the body skipped.]]></verify>
  <done>Every computed, bar and range layer left with no drawable rows drew its own scheme colour, width family and legend key in both modes, and bar and rbar used one fallback width on every path.</done>
</task>

<task type="auto" id="12-18">
  <name>Certify widths and emptied keys against Stata</name>
  <files>test/filter_truth_check.py, test/test_e2e_filters.cscript, test/test_wp29_truth.cscript</files>
  <action><![CDATA[
**test/test_e2e_filters.cscript.** Append EW-01 after SCU-03, as "Stata truth" specifies, using the 12-10 helpers (`bar_graph`, `vbar_width`). Add any helper it needs to `test/filter_truth_check.py`, with a docstring.

**test/test_wp29_truth.cscript.** First read the scaffold's top for `_w29_expect`, `_w29_done` and `w29_work`. Add the block above the marker and after S11's blocks (R1 order):

```
* ==== S12 P0.18: emptied layers keep their style ====
local only : env WP29_ONLY
if inlist("`only'", "", "S12") {
    display as text "S12 start `c(current_time)'"
    ... EW-02, EW-03 ...
    ... erase every file the block wrote, under `w29_work' ...
    display as text "S12 end `c(current_time)'"
}
* ==== end S12 ====
```

EW-02 and EW-03 follow "Stata truth":
- cases are judged with `_w29_expect`/`_w29_done` and never `exit` on a failure;
- the Python block loads the app with the KF-03 loader pattern and never calls back into Stata;
- add one line to the header comment's block list.

Run both scripts through the driver once with dash_render.py stashed (append the EW lines to `<scratch>/12-P0.18-failure.txt`) and once restored.
  ]]></action>
  <verify><![CDATA[The restored runs' logs contain `EW-01 PASS` and `All filter widget E2E tests PASSED.` (`<scratch>/run_test_e2e_filters.log`), and `EW-02 PASS`, `EW-03 PASS` and `test_wp29_truth: ALL CHECKS PASSED` (`<scratch>/run_test_wp29_truth.log`), with `grep -c ' FAIL' <scratch>/run_test_wp29_truth.log` printing 0; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Stata certified that the served and saved bar widths agreed after a move and that dash's emptied layers took the colour twoway keys them in, in both modes.</done>
</task>

<task type="auto" id="12-19">
  <name>Document P0.18 in help, BUGS and CHANGELOG</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
**dash.sthlp, "What a filter move redraws".** Change the served sentence's `bins, grid and fitted line included.` to `bins, grid, fitted line and bar widths included.`. Add after the sentence that ends `… shows.`: `In both, a layer that a filter, a {cmd:by()} panel or its own {cmd:if} or {cmd:in} leaves with no observations keeps its colour, width and legend key, as twoway draws it.`

**BUGS.md.** Close the P0.18 entry in place (`- [x]`), with its Resolution rewritten: `  - Resolution: Fixed <ddmonyyyy> (WP-29, P0.18). The served redraw copies each redrawn bar or rbar glyph's width onto the live glyph (_dash_copy_redraw_geometry, called by the emitted _on_filter_change step 3), so after a move the served width is the kept rows' spacing the saved page draws (168, not 56, for the Foreign cars of the parity frame); an empty fitted, smoothed, histogram, bar or range layer is drawn in its own scheme colour, width and legend key in both modes (GlyphMapper._empty_fit_line, _histogram_quads and the styled empty paths of map_bar, map_rbar, map_rarea and map_rspike), as twoway keys it (#90353B for the second plot under s2color); bar and rbar take one fallback width (0.8, 0.64) on every path. Pinned by test/test_mode_parity.py::TestAFilterMoveAgrees::test_same_glyphs_after_the_move, test/test_emptied_layer_style.py::TestAnEmptiedLayerKeepsItsStyle::test_served, ::TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour, test/test_served_filter_move.py::TestTheRedrawGeometry::test_a_bar_takes_the_redraws_width, test/test_e2e_filters.cscript EW-01, test/test_wp29_truth.cscript EW-02; fixture test/fixtures/emptied_layer_truth.json. Residual, deferred (WP-29): twoway draws a bar one x unit wide, not 0.8 of the smallest gap (P1.17); the empty histogram key colour (P1.4).`

**CHANGELOG.md.** Replace `<!-- WP-29 P0.18 -->` in the `**WP-29 (drop-in P0, 30sep2026)**` group of `### Results that change` in place with ONE item ending `(WP-29, P0.18)`. It names the commands, the old values (from `<scratch>/12-P0.18-failure.txt`) and the new: `- In the served app, after a filter move a bar's and an rbar's width follows the kept rows: dash bar mpg weight served with filter(foreign) drew the Foreign cars' bars 56 wide (the build's spacing), now 168, as the saved page draws them. A computed, bar or range layer left with no observations -- dash (scatter mpg weight) (lowess mpg weight if price >= 10000), or a served layer with its own if that selects nothing -- was drawn in Bokeh's #1f77b4 at width 1, now in its own scheme colour and width with its legend key (#90353b, 1.5 for the second plot under s2color), as twoway keys it (WP-29, P0.18)`.

Grep the three files for `claude|anthropic`.
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-29 P0.18 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.18)' CHANGELOG.md BUGS.md | awk -F: '{s+=$2} END {print s}'` prints 2; `grep -c 'bar widths included' dash.sthlp` prints 1.]]></verify>
  <done>The help said the served app redraws bar widths and that an emptied layer keeps its style, the P0.18 entry was closed in place naming existing tests and the fixture, and its marker was replaced by one item.</done>
</task>

<task type="auto" id="12-20">
  <name>Close P0.18 and make commit two</name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
Delete only the `"P0.18": ...` line of `WP29_OPEN`.

Run, in order:
1. `python3 -m pytest test/test_tracking_documents.py test/test_fixtures_are_committed.py test/test_function_test_map.py -q -n0 -p no:cacheprovider`.
2. `gitnexus_detect_changes()`.
3. The full suite once (`python3 -m pytest test/ -q`; read its log, never relaunch).
4. The 12-18 driver runs.

Then:
- stage only these files: dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_emptied_layer_truth.do, test/fixtures/emptied_layer_truth.json, test/test_mode_parity.py, test/test_emptied_layer_style.py, test/test_glyphs.py, test/test_served_filter_move.py, test/function_test_map.py, test/filter_truth_check.py, test/test_e2e_filters.cscript, test/test_wp29_truth.cscript, test/test_tracking_documents.py;
- commit with the subject of "Commit boundary" and the body of TR-01.10, including `Fixture:`;
- grep the message for `claude|anthropic` before and after committing.

Hand `<scratch>/12-notes.txt` and "Notes for the closeout" to S15 in this agent's output.
  ]]></action>
  <verify><![CDATA[The full suite reports 0 failed and no new skips; `git -C <W> log -1 --format=%s | grep -c '(WP-29 P0.18)'` prints 1; `git -C <W> log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0; `git -C <W> log --oneline -2` shows the P0.17 commit below the P0.18 commit.]]></verify>
  <done>P0.18 was closed in a second green commit on wp29-s12 holding its fixture, failing tests, fix and closed entry, with the closeout notes handed to S15.</done>
</task>

## Section completion criteria

- On the saved page, every frozen layer is marked exactly while a move has removed a row of its estimation sample, and cleared when every such row is back. This includes all three of S11's lpolyci sources: band, outline and line (C1). This is proved under node, in headless Chrome in both layouts and both filter positions, and by SCU-01..03 against Stata's `regress`.
- The served app refits, carries no cue model, and draws bar and rbar widths from the kept rows after a move (`TestAFilterMoveAgrees` with bar and rbar, EW-01).
- Every empty computed, bar and range layer keeps its style and key in both modes, as twoway keys it (`test_emptied_layer_style.py`, the fixture, EW-02 and EW-03).
- `ALLOWED` and `_MUST_WARN` are unchanged, and the parity file is green with every new case.
- There are two commits on `wp29-s12`, ending `(WP-29 P0.17)` and `(WP-29 P0.18)`, each green under the full suite. There is no test-only commit, no AI reference and no co-author trailer.
- BUGS.md closes both entries in place, both CHANGELOG markers are replaced, and both `WP29_OPEN` keys are gone.

## Notes

- **Two languages, one rule.** The estimation sample is defined once, in Python (`_layer_weight_column`, `_layer_weight_values_state`, `_agg_member_ids`). It reaches the script as `vars`, `wvar`, `wrule` and `members`. A change to `_layer_weights` must change the tag in the same commit, and `TestTheWeightedSample` fails if it does not.
- **Null, never 0.** The snapshot writes NaN, ±inf and NaT as null (`_dash_json_value`). Test finiteness with `typeof v === "number" && Number.isFinite(v)` only.
- **The caption and the toolbar.** Bokeh pairs a sticky `above` toolbar with the first Title in `fig.above` (E-17.7). dash never puts a figure's toolbar above today, and `test_no_marked_figure_has_its_toolbar_above` guards it. A later change that does must move the cue into a wrapper instead.
- **Layout shift.** A visible caption takes about 14 px from the frame. In a `by()` grid, a marked panel's frame is shorter than an unmarked one's while marked. This is accepted (the caption must not occlude data) and stated in the help.
- **The sidebar gap.** Under `layout(bs) filterposition(left)`, the hidden status Div sits in its own `db-sidebar-item` wrapper with a 16 px bottom margin. This is cosmetic and recorded for S15.
- **Accessibility.** `aria-live` on text replaced inside a Bokeh Div's shadow DOM is announced inconsistently across screen readers. The text is in the DOM either way, and the accessibility scope is P3.12's.
- **S14 contract.** See Dependencies. `test_only_an_lfit_with_no_scatter_is_marked` is the tripwire.
- **Merge rules.**
  - **R1:** SCU-01..03 and EW-01 are appended after S07's QF cases in `test_e2e_filters.cscript`. The S12 block of `test_wp29_truth.cscript` goes after S11's. No runner or hygiene-pin edit is made.
  - **R2:** the copy-list entry `_dash_copy_redraw_geometry` goes after `_dash_keep_jitter` (anchor `_dash_refresh_unlinked`). The `function_test_map.py` keys go in alphabetical place, and the merger keeps every entry.
  - **R3:** this section owns, in dash.sthlp, only the three table rows and the sentences quoted in 12-11 and 12-19. S02's and S07's sentences in the same paragraph are kept as found. In BUGS.md and CHANGELOG.md it touches only its own entries and markers, and in `WP29_OPEN` only its own two keys.
  - **R5:** one new fixture, `git add -f`, never patched.
  - **R6:** CORPUS and MOVE_CORPUS appends only; `ALLOWED` and `_MUST_WARN` untouched (D12-1).
  - **R7:** the flips are listed in `<scratch>/12-flips.txt`.
  - **R8:** 12-01, and `gitnexus_detect_changes()` before each commit.
- **Merge conflicts to expect.**
  - **S10 and S11: none.** Under C1 both are on this section's base. The map_lpoly hunk and the `_frozen_vars` lines (one per dispatch branch) are written on their landed text, and nothing is re-applied by hand.
  - **S13** edits `_generate_app_source`. This section's four emitted lines sit inside step 3's loop.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch> <file>.do` with `dash_nobrowser=1` and the do-file opening `adopath ++`. Never the GUI, never a bare `stata-mp`, and never the full cert suite in this section. A SKIP (exit 222, `c(python_exec)` dropped under concurrency) is not a pass.
- **Line numbers** are `7421d3d`'s, shifted by batch 1. Symbols are authoritative.

### Notes for the closeout (A5; S15 writes these, S12 does not)

- **GAPS2.md C4 (:755) and E4 (:1148).** Tracked line: `Partly closed in WP-29 (P0.17, commit <sha>); open: the saved page does not refit (decision M3; plan items 1-2), no build-time note (Q22), histogram bins and kdensity grid are not recomputed (P2.24)`.
- **REMAINING.md REM-15-03-C15:** closed by P0.18's commit. **TWOWAY_COVERAGE_AUDIT.md AUDIT-38:** partly closed by P0.17's commit (the cue).
- **DROPIN-REMAINING.md:** P0.17 and P0.18 annotated with their commits.
- **ROADMAP.md WP-29 results:**
  - the caption's 14 px layout shift and the sidebar gap;
  - the 12-08 timing (100,000 rows, with and without the cue);
  - the copy strings (D12-5), which the maintainer may still change as constants.
- **AGENTS.md invariants:**
  - "a saved page marks a frozen layer while a move has removed a row of its estimation sample, and the served app carries no cue" (`test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove`);
  - "an empty layer keeps its scheme style and key in both modes" (`test/test_emptied_layer_style.py`);
  - "the served redraw copies spacing-derived glyph widths" (`test/test_served_filter_move.py::TestTheRedrawGeometry`).
- **D12-1 to record:** the saved-only status Div is honoured by the existing `ALLOWED["aggregate layers recompute live"]`; no key was added.
- **Residuals:**
  - twoway's bar width (P1.17);
  - the histogram key colour (P1.4);
  - any CORPUS entry 12-14 dropped for a warning-only difference (`<scratch>/12-notes.txt`);
  - accessibility of `aria-live` in shadow DOM (P3.12).
