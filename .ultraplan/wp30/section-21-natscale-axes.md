# Section 21: natscale ticker and twoway margin on non-date axes (P1.3 part a, M1)

> Part of: WP-30 · Items: P1.3 part a (entry `P1.3a`) · Risk: red · Batch: 7 · Depends on: 08, 15, 18 · Blocks: 27, 35, 44, 47, 49, 50, 52, 53 · Tasks: 25, 1 commit · Case prefix: NS

## Review amendments

- Fixed (blocker): TR-21.11 put `_DASH_AXIS_FINISH_JS` inside `_FILTER_JS`'s literal (18562), which runs before the natscale constants (22070-22082) and the new JS (after 22878) exist: a NameError at import. `_FILTER_JS` is now extended by one module-level statement directly after the new constants; its literal is not edited (TR-21.11, 21-13).
- Fixed (blocker): the saved page does not refit fits, CI fits, bins or grids after a move (WP-29 P0.17 stale cue), while the served app does, so `test_saved_equals_served_equals_the_redraw` over scatter+lfit and NS-10's saved Q06 could never pass. New D-21e2: a stale layer stays in the saved hull as drawn; saved equals served only where both draw the same layers. BR-21.5, NS-10, the Q06 test, a new `test_a_stale_fit_stays_in_the_saved_hull`, AC-21.5, the completion criteria and the CHANGELOG line follow.
- Fixed (major): the finish JS wrote `start` then `end`, firing the shared zoom callback on a half-updated range (and per end, per range, on 100 shared panels). It now writes each range with one `setv` under a `_dash_finishing` guard the zoom code honours; js_runner's Range1d stand-in gains `setv`.
- Fixed (major): 21-25's verify grepped `"P1.3a"` for 0, which `WP30_LISTS`/`WP30_SECTION` make impossible; it now checks `WP30_OPEN` by import. 21-25 now stages before the G6 check.
- Resolved D-21h (open question 1) without the maintainer: no batch-7 partner owns either paragraph, rule 2 forbids help the code makes false; S21 edits both sentences and index.md's R3 table is to name them (review-notes/g04.md).
- Fixed (minor, register P1.2.7): Dependencies credited S15 with removing Bokeh's minor ticks and made F25 conditional; P1.2.7 gives the minor-tick bullet and its flips to P1.3, so F25 is flipped here unconditionally (S15's own review agrees). S27's later retirement of `_dash_auto_base` is noted under Blocks.
- Fixed (minor): TR-21.11's token list names the real constants (`_DASH_NATSCALE_*`); S20's edits are listed correctly in Dependencies; the truth block's Python puts `test/` on `sys.path`.
- Checked: every E1, E2 and E9 anchor (22176, 22185, 22997, 23345, 23419, 23489, 23535, 23565, 23674, 23732, 23775, 23845, 23913, 30309, 30611, 30660-30679, 32707, 32942-32943, 33250-33251, 35095/35192, 35405, 35415-35430, 35650-35654, 35828/35854) matches `c96facd`; `_FILTER_JS` has no top-level `return`, so the appended finish always runs; brushing touches only KPIs, so it needs no re-finish.
- Checked (batch 7): S21 shares `_glyph_layer_lines` with S19 only at distinct R2 anchors, edits neither `_dash_axis_labels` nor `_dash_add_secondary_axes`, and is the batch's only `_make_figure_body`/`_generate_app_source`/finisher/scheme editor; M5 (no refusal) and M6 (no note) hold. index.md's 7.0 list lacks `DashRenderer.render` (CRITICAL) and `_glyph_layer_lines` (HIGH): filed in review-notes/g04.md.
- Rejected: "ratification items 1 and 3 must be settled here" (A151 puts them to the maintainer before batch 1; the file is written on them as stated).
- (cross-file pass) F33: the directive-count pin's bounds and help sentence are S15's measured ones (S15 15-18 now moves them from 80-140), not 80-140.
- The review pass applied both lenses.

## Overview

**Binding readings applied in this file** (decisions M1, M5, M6; register P1.3.1-P1.3.8, X.1, X.5; index A152, A153, IR-12, IR-17, R2, R11, R12):
- **M1 / P1.3.4.** Every default axis changes (ticks, extent, margin, fits no longer clipped), with no opt-out, and a CHANGELOG "Results that change" line names the command, the old value and the new.
- **P1.3.1 / A6 (ratification item 1, pending).** twoway's plot-region margin is r × min(W,H) on every side, converted at build into a per-axis fraction of the frame from the graph's canvas (xsize()/ysize(), else the scheme's graphsize). It may be up to about 0.8% of the figure width off twoway's; this is documented in the help.
- **P1.3.2.** Default and `#N` axes are re-ticked and re-ranged over the kept rows after every filter move, in both modes, y2/x2 included.
- **P1.3.3 / A7.** A zoom or pan re-ticks by natscale over the visible range, in both modes, through the same JS (D3 a). No BokehJS view internals are used.
- **P1.3.6 (M1 strict, IR-17).** An explicit-value axis re-hulls its data part after a move and keeps its label positions. dash.sthlp's "holds across filter moves" (:2852) is rewritten.
- **P1.3.7 / IR-12 (D7 a).** Default (not explicit) bar, area, spike and dropline bases are kept out of the tick input and the hull until S27. An explicit `base()` stays in the hull. S21's tests pin the hull rule, not the drawing.
- **P1.3.8 / A9 (ratification item 3, pending).** Budgets: the served re-finish adds at most 0.2 s per figure per move at 500k rows; 100 saved by() panels settle within 1 s of the time measured at the batch-7 base.
- **M5.** S21 adds no refusal. **M6.** S21 adds no note, in either mode, for anything it draws.
- **X.1 / A149, R2.** Copy lists are append-only at S21's two anchors. **X.5 / A148.** Map keys go under S21's anchor.
- **A152.** S21 is batch 7's scheme regenerator. It adds three scheme keys, regenerates all 26 files and `scheme_truth.json`, and lands last in the batch.
- **A153 / R11.** S21 creates `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`, `_dash_default_ticker` and `_dash_plot_margin`. Its call sites cover date axes too, so S44 never edits `_generate_app_source`.
- **R12.** S21 is batch 7's only editor of `_make_figure_body` and `_generate_app_source`. It edits neither `_build_sources_and_figures` nor `_build_filter_widgets` (D-21f).

**Section decisions (this file).**
- **D-21a. The margin key.** twoway's plot region takes its margin from `margin twoway` (`plotregionstyle-twoway.style:4` `set margin scheme twoway`), not from `margin plotregion`. The two keys are equal in all 26 shipped schemes: medsmall, and vsmall in economist (Evidence E8). The manifest's "margin plotregion key" is therefore read as Stata's `margin twoway`. It is transcribed into the dash files as `margin twoway <marginstyle>`, and SchemeParser reads it through `_DASH_MARGIN_RS`, s2color's `gsize *margin` ladder: zero 0, tiny 0.3, vsmall 0.6, small 1.2, medsmall 2.2, medium 3.5, medlarge 5, large 8 and vlarge 12, in relative units (% of min(W,H)). An unknown name keeps 2.2, silently, as every unreadable scheme value does.
- **D-21b. by() panels.** A panel's margin is its graph's margin times twoway's by() size multiplier f(G), from `grid.class` `scale_gmetric`: n = ceil(sqrt(G)); f = 1 − ((n−1)/n)·b1 − [n > k1]·(b2−b1)(n−k1)/n, with s2color's `special by_knot1 3`, `by_slope1 .3` and `by_slope2 1`, which all 26 shipped schemes inherit. These are held in `_DASH_BY_GMETRIC`, not added as scheme keys. Measured: G = 2, 3, 6, 10 give 0.85, 0.85, 0.8, 0.6 (Evidence E7); B01's SVG margin is 0.85 × 0.022. A user scheme's `special by_*` keys are not read, silently (Notes for the closeout).
- **D-21c. The default placeholder is a FixedTicker.** `_dash_default_ticker(n)` is a `FixedTicker(ticks=[], minor_ticks=[])` tagged with `_DASH_COUNT_TAG + str(n)` and `_DASH_DEFAULT_TAG`. `_dash_count_of` reads it as a count, so the existing `#N` machinery places it. `_dash_count_ticker` is not changed, because the colour key uses it.
- **D-21d. Zoom.** One shared `CustomJS` (`_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS`) is attached to `start` and `end` of every planned range, in both modes. When the visible range is the range's reset extent, it writes the ticks the finisher computes from the current data. Otherwise it writes natscale ticks over the visible range (the log and `%tc` rules apply). It writes only when the ticks differ. One model per document keeps a 100-panel page small.
- **D-21e. What a move holds, in both modes.** These keep their build-time positions after a move: `%td`-`%ty` `#N` ticks (S44 lifts this), `xtick(#N)`/`ytick(#N)` marks (a CustomJSTicker's `args` cannot be rewritten from the page), `minmax` positions and every explicit list. An axis whose kept rows draw nothing keeps its last extent and ticks. An axis with no finite value at build keeps Bokeh's autorange. The held positions still join the hull. The modes agree on each.
- **D-21e2. Layers the saved page does not recompute (review pass).** The saved page does not refit a fit, CI fit, bin or grid layer after a move: WP-29 P0.17's stale cue leaves it drawn from all rows, muted, its key suffixed by `_DASH_STALE_SUFFIX` (" (unfiltered)", " (bins unfiltered)", " (grid unfiltered)"). The served app refits it over the kept rows. Such a layer is still drawn, so it stays in the saved hull as drawn (clipping it would undo BR-21.2), and the two modes' re-finished axes then differ by exactly that layer's extent, the difference the stale cue already documents. Where both modes draw the same layers (no stale layer after the move) they agree within 1e-9 relative. The saved re-finish is checked against Python's `_dash_finish_count_ticks(fig, refinish=True)` over the saved page's own written data (`test_natscale_js.py::TestJsFinishEqualsPython`), and against twoway only for moves that leave no stale layer.
- **D-21f. Saved wiring.** The saved page's plans are written into the filter callbacks' args by a new step "5b" of `DashRenderer.render()`, right after `_build_filter_widgets` returns (Evidence E12). `build_dropdown`/`build_slider`/`build_range` carry the placeholders `axis_plans_json: "[]"` and `axis_models: []`. `_build_filter_widgets` (CRITICAL, R12) is not edited. `DashRenderer.render` is CRITICAL (13 impacted) and is reported at 7.0.
- **D-21g. Hull roles.** A new `_dash_tag_hull_roles(renderers, ptype, options)` runs per layer in both build loops. It stamps `_dash_auto_base` (the glyph property holding a default base: bar `bottom`, area `y1`, spike and dropline `y0`) when the layer has no `base()`. It stamps `_dash_raw_sif = True` on scatteri, pci, pcarrowi and function renderers, which every hull reader skips on a DatetimeAxis until S35. These are Python attributes and are never serialised.
- **D-21h. Help outside "Axis labels" (resolved, review pass).** Two sentences that S21 makes false are corrected in place, one sentence each: the by() paragraph's "stops that axis following later filter moves" (dash.sthlp:2084-2086), and the toolbar's Reset row, "the view the page opened with" (:1203-1204). R3/A155 exists so that parallel sections edit distinct hunks; no batch-7 section owns either paragraph (their owners, S28, S48, S53 and S22, S54, are in later batches and re-find their sentences by text), and project rule 2 forbids shipping help the code makes false. So S21 edits both; index.md's R3 table is to name the two rows (cross-file fix, review-notes/g04.md).
- **D-21i. The x pool.** `_dash_count_axes` stops reading a primary-limited x pool. Its comment that "a fit's line is drawn 10% past the data" is stale, because `_fit_grid` draws over the observed range (dash_render.py:`_fit_grid`).

**What is wrong today.** DROPIN-REMAINING.md:77 (P1.3): "Every default axis gets BasicTicker and 10% padding." GAPS2 B25 (GAPS2.md:635) measured the symptom: "On auto's mpg, dash draws 15(5)40 where twoway draws 10(10)40". The WP-29 S10 note adds that "twoway's by() common scale includes fit lines (c15); dash's shared range (P0.2, commit ab53f25) does not yet". S01's entry `P1.3a` reads: "Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ticks and plot-region margin, and fit lines are left out of the axis range".

Re-measured at `c96facd` (Evidence E3, E4), the saved page and the served app agree, and both are wrong:
- `scatter mpg weight` has `BasicTicker(desired_num_ticks=6)` over `DataRange1d(range_padding=0.1)`. The browser draws y 15(5)40 over 10.55-42.45 and x 2000(500)4500 over 1606-4994, with Bokeh's minor ticks. twoway draws y 10(10)40 over 10-41 and x 2000(1000)5000 over 1760-5000, plus a margin of 2.2% of min(W,H).
- Fit lines, CI bands, scatteri and function layers are left out of the autorange (`_dash_limit_ranges_to_primary`), so `(scatter price mpg)(lfit price mpg)` clips the fit at 2660 where it runs to 1458.39. by() panels clip it the same way (c15).
- `ylabel(#5)` pins the axis at its outermost tick (start = 10.0) with no margin.
- A second axis with no `ylabel2()` keeps Bokeh's ticks: y2 4000(2000)16000 where twoway draws 0(5000)15000.
- After a filter move the first axes follow Bokeh's autorange, but `#N` axes and y2/x2 hold their build-time ticks and extent. twoway re-ticks them under the same `if`.

**After this section,** in the saved page and the served app, before and after every filter move:
- every default numeric, log and `%tc` axis, and every y2/x2 without its own `ylabel2()`/`xlabel2()`, is ticked as `#N`, with N from the scheme's `numticks_g horizontal_major`/`vertical_major` (5 in all 26 schemes), through natscale. It draws no minor ticks.
- every continuous axis is a Range1d over the hull of every drawn layer (fits, bands, scatteri and function included; swatches, default bases, reference lines and text excluded), its ticks, label and tick positions and `range()` values, padded by twoway's plot-region margin.
- by() panels share one Range1d per shared axis over the union hull.
- after a move, the axes are re-finished over the kept rows (in Python when served, by `_DASH_AXIS_FINISH_JS` when saved), and Reset returns to the re-finished extent.
- a zoom re-ticks by natscale.

`%td`-`%ty` default axes keep Bokeh's DatetimeTicker until S44 (P1.3b), but they already get the hull and margin.

**Why one section.** Ticks, extent, margin and re-finish are one pipeline: `_dash_count_axes` → `_dash_place_count_ticks` → `_dash_axis_hull` → `_dash_hull_ranges` → `_dash_padded_range`, shared by `_dash_finish_count_ticks` and the by() path `_dash_common_count_ticks`/`_dash_share_by_scales`. Changing any one stage without the after-move re-finish makes the two modes disagree after a move (RK-1), so this section must not land without its re-finish.

**Test order and commit rule (rule 7, D1).** There is one entry, one cycle and one commit, `(WP-30 P1.3a)`.
- **21-01** writes the regression tests whose expectations are twoway's literal values (Evidence E5-E7), runs them on the unmodified batch-7 base and saves `<scratch>/21-P1.3a-failure.txt`. It never commits.
- **21-02** measures the two budgets at the base. **21-03** extracts the fixture. **21-04** adds the fixture-driven tests and the guards and appends their red lines.
- **21-05 to 21-23** make the fix, flip the pinned tests, add the parity cases, the truth block, the Chrome test and the help, and certify.
- **21-24** re-measures the red list, the mutation table and the digest. **21-25** closes the entry, replaces the marker and makes the one commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [red] — every dashboard's axes change, five CRITICAL symbols plus `DashRenderer.render`, and a new JS twin of the finisher that must agree with Python after every move

**Why.** M1 accepts a visible change to every dashboard (RK-4). The finisher chain runs for every figure in both modes. The saved page gains its first JavaScript that writes ranges and tickers, and it runs on every filter move and every zoom.

**Risk factors.**
1. **Blast radius** (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026 at `c96facd`):
   - CRITICAL: `_make_figure_body` (4 impacted), `_dash_padded_range` (10), `_dash_common_count_ticks` (4), `_dash_share_by_scales` (8), `FilterBuilder.build_dropdown` (6), `DashRenderer.render` (13, with `-f dash_render.py --kind Method`).
   - HIGH: `_generate_app_source` (5), `ServerAppBuilder._glyph_layer_lines` (4); `_dash_natscale_ticks` (8) and `_dash_axis_count_ticks` (10) are ported, not edited.
   - LOW: `_dash_apply_axis_options` (3), `_dash_finish_count_ticks` (3), `_dash_place_count_ticks` (6), `_dash_hull_ranges` (6), `_dash_axis_hull` (6), `_dash_count_axes` (3), `_dash_finish_secondary_axes` (3), `_dash_secondary_values` (5), `_dash_limit_ranges_to_primary` (3), `_dash_keep_primary_ranges` (3), `SchemeParser._init_properties` (1).
   - UNKNOWN, confirmed by grep: `build_slider` and `build_range` (one caller each, the dispatch at dash_render.py:32016-32017); `_FILTER_JS` (3 code sites, 19525/19587/19650; 27 test files); `_dash_range_hull` (TEST_ONLY; 10 test and cscript files).
2. **Twin drift.** The saved JS port (natscale, log and `%tc` rules, reader, hull, padding, by() union) must equal the Python finisher, or the modes disagree after a move.
3. **Budgets.** `_dash_count_axes` takes 0.58 s for one 500k-row scatter (p1-03 critic, Performance), so a naive served re-finish misses the 0.2 s budget. 100 saved panels each run the JS.
4. **Pinned tests.** About 40 tests pin DataRange1d, BasicTicker, the 5% pad or the renderer lists (Evidence E10). Each is flipped with its reason, never deleted.
5. **Page size.** Per-range zoom callbacks would multiply the JS 100-fold on a 100-panel page.
6. **Notes and help.** The 26 regenerated scheme files and the help paragraphs are shared surfaces (R3, R7).

**Mitigation.**
1. Impact runs at the batch-7 base (index 7.0), with a warning before each CRITICAL edit, and `DashRenderer.render` is added to the 7.0 list. Each edit is additive, or a named rewrite of one stage.
2. `test_natscale_js.py` checks JS against Python over `natscale_truth.json`, 5,000 seeded random ranges, the overflow cases and seeded random moves. `TestAfterAFilterMove` compares saved (node) with served and with the saved page drawn from the same rows.
3. A vectorised reader (`_dash_layer_extent`), the timed tests `TestTheRefinishBudget` and `TestTheHundredPanelBudget`, and the existing `test_hundred_panels_settle`.
4. 21-24 re-measures the red list; 21-16 to 21-19 flip exactly that list.
5. One shared zoom `CustomJS` per document (D-21d).
6. Regeneration is done by the extractor, never by hand (R7), and help edits stay at the named lines.

## Dependencies

- **Depends on: 08, 15, 18.**
  - S08 defines the relative unit: 1 rs = min(W,H)/100. The margin is a relative size (p1-03 §7).
  - S15 (batch 5) owns the scheme chrome: tick length, side and colour (including the colour of the minor ticks Bokeh still draws until this section), and the economist axis sides in `_dash_finish_secondary_axes`. It was the previous regenerator. S21's FixedTicker leaves its tick styling alone. Register P1.2.7 gives the minor-tick bullet and `test_help_claims_8.py`'s BasicTicker/minor-tick flips to this section (P1.3): the FixedTicker's `minor_ticks=[]` removes them on default axes, and F25 is flipped here.
  - S18 (batch 6) sets default tick formats through `_dash_axis_tick_formats`. S21 replaces tickers only and never a formatter.
  - S01 provides the open entry `P1.3a`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.3a -->` in the WP-30 group of `### Results that change`, the stub `* ==== S21 P1.3a: natscale ticker and twoway margin on non-date axes ====`, the map anchor `# WP-30 S21 (P1.3a): natscale ticker and twoway margin on non-date axes (P1.3 part a, M1)` and `test_every_listed_name_exists`.
  - S02 provides TR-02.9's extractor root stanza. S07 provides the 26 scheme files and their extractor. S14 provides one-x-unit bar widths, read by the hull.
- **Blocks: 27, 35, 44, 47, 49, 50, 52, 53.**
  - S27 replaces D7 a with clamped auto bases through `_dash_finish_auto_bases`, hooked into S21's finishers; it retires `_dash_auto_base` for a renderer tag `dash_base:` and adds `autobase`/`bases` keys to `_dash_axis_plan`'s per-axis plan (S27's file; informational).
  - S35 removes the raw-SIF exclusion and adds date transforms.
  - S44 adds the tsnatscale default and its JS port, and lifts the `%td`-`%ty` hold.
  - S47 adds `plotregion(margin())` through `_dash_plot_margin` and the inner box.
  - S49 adds HBar half-heights and transposed glyphs to the hull. S50 adds the extend Arrow over the hull. S52 makes `add` union with the default ticker. S53 draws outer axes under by().
- **Parallel batch: 7**, merge order S19, S20, S21. S21 lands last.
- **Can run with:**
  - S19 edits `_dash_axis_labels`, `_dash_add_secondary_axes` (titles), `_dash_legend_key(s)`, `_dash_layer_series`, `map_scatteri`, `_DASH_FIT_KEYS` (constants anchor after `"_DASH_FIT_TYPES", "_DASH_CI_TYPES",`), `_dash_axis_default_titles` (functions anchor after `"_dash_axis_labels",`) and dash.ado's `_dash_process_segment`.
  - S20 edits dash.ado's `_dash_parse_plot_opts`, `_dash_option_rules`, `_dash_validate_opts`, `_dash_fold_mlab`, the `_dash_validate_opts` call in `_dash_process_segment`, two new programs, and dash_parse.mata.
  - S21 touches none of these. It edits `_dash_finish_secondary_axes`, never `_dash_add_secondary_axes`.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines), re-read 03oct2026. Symbols are authoritative if lines drift after batches 1-6.

### E1 — the default axis is left to Bokeh

`_dash_apply_axis_options` (22997) changes the ticker only when `xlabel()`/`ylabel()` is given. With no rule, or sub-options only (mode "default"), Bokeh's ticker stays (23023-23031):
```python
            if kind:
                spec = _dash_date_axis_spec(spec, kind, ax_key)
            _dash_apply_axis_spec(axis_obj, grid_obj, spec,
                                  col, (numeric_formats or {}).get(var, ""),
                                  grid_color, vlabels, fmt_cache=fmt_cache)
        traw = graph_opts.get(tick_key, "")
        if traw:
            _dash_apply_tick_option(axis_obj, grid_obj, traw, tick_key, col,
                                    seen, key, grid_color, date_kind=kind)
```
The `#N` placeholder (22176-22182; its callers are 22793, 22924 and the colour key at 26172) is a BasicTicker:
```python
def _dash_count_ticker(count):
    from bokeh.models.tickers import BasicTicker
    return BasicTicker(desired_num_ticks=int(count),
                       tags=[_DASH_COUNT_TAG + str(int(count))])
```

### E2 — extent, margin and the layers left out

- `_dash_padded_range` (23489) pads 5% of the span a side. Its docstring (23498-23499) says "Stata's margin is 2.2% of the canvas instead (B25, left as it is)". The pad at 23517-23518:
  ```python
          pad = 0.05 * (hi - lo)
          s, e = lo - pad, hi + pad
  ```
  `_dash_range_hull` (23535) inverts it with `w = (b - a) / 1.1`.
- `_dash_axis_hull` (23565) gives no hull to an axis without an explicit value (23601-23603), so the axis keeps the DataRange1d:
  ```python
      explicit = [float(v) for v in explicit if ok(v)]
      if not explicit:
          return None
  ```
- `_dash_place_count_ticks` (23419) pins a `#N` axis at its outermost tick (23467-23476):
  ```python
      if isinstance(rng, DataRange1d):
          if getattr(rng, "flipped", False):
              return
          if common:
              rng.start, rng.end = float(min(t_lo, d_lo)), float(max(t_hi, d_hi))
              return
          if t_lo < d_lo:
              rng.start = t_lo
  ```
- `_dash_limit_ranges_to_primary` (23913) keeps only the graph's own source's renderers in both autoranges (23935-23945), so fits and bands are clipped:
  ```python
      prim = [r for r in fig.renderers
              if hasattr(r, "data_source")
              and any(r.data_source is s for s in srcs)]
      ...
          if isinstance(rng, DataRange1d):
              rng.renderers = prim
  ```
  `_dash_keep_primary_ranges` (23316) narrows that pool beside a second axis.
- `_dash_count_axes` (23345) reads x through the primary-limited pool (23397-23402). Its comment about fits drawn 10% past the data is stale (D-21i).
- `_dash_share_by_scales` (23845) shares one DataRange1d per axis across by() panels (23869-23880), which BokehJS spans over the listed renderers, fits excluded.
- `_dash_finish_secondary_axes` (23172) fits y2/x2 to the data hull with the 5% pad (23259-23271). With no `ylabel2()` the axis keeps Bokeh's ticker.

### E3 — measured at `c96facd`, both modes (model level)

Command: `python3 <scratch>/r-p1-03/dash_now.py` (research probe, re-run 03oct2026; `test_by_scales._frame("auto")`, saved `DashRenderer`, served `make_document`). The served lines equal the saved ones:
```
[saved] D01 scatter mpg weight
    y: DataRange1d(range_padding=0.1, start=nan, end=nan, renderers=[Scatter]) ticker=['BasicTicker(desired_num_ticks=6)']
[saved] D03 (scatter price mpg)(lfit price mpg)
    y: DataRange1d(range_padding=0.1, start=nan, end=nan, renderers=[Scatter]) ...      (the lfit is not listed)
[saved] D06 scatter price weight, yscale(log)    y ... ticker=['LogTicker(desired_num_ticks=6)']
[saved] D09 bar price rep78                       y: DataRange1d(range_padding=0.1, ..., renderers=[]) BasicTicker
[saved] D01b scatter mpg weight, ylabel(#5) xlabel(#5)
    y: DataRange1d(range_padding=0.1, start=10.0, end=nan, ...) ticker=['FixedTicker(...)[10.0, 20.0, 30.0, 40.0]']
    x: DataRange1d(range_padding=0.1, start=nan, end=5000.0, ...) ticker=['FixedTicker(...)[2000.0, 3000.0, 4000.0, 5000.0]']
```

### E4 — measured in the browser at `c96facd` (research p1-03 §2, headless Chrome over the saved page, BokehJS ranges and `tick_coords`)

```
D01 scatter mpg weight      y [10.55, 42.45] yticks 15(5)40 | x [1606, 4994] xticks 2000(500)4500
D03 (scatter price mpg)(lfit price mpg)  y [2660.25, 16536.8] yticks 4000(2000)16000   (the lfit reaches 1458.39: clipped)
c15 (scatter price mpg)(lfit price mpg), by(foreign)  both panels y [2660.25, 16536.8]; fits reach 1405.87 and 2321.91
D17 y2 (scatter price weight, yaxis(2))  y2 ticks 4000(2000)16000
D01 after the range slider's upper handle to 0.3 (price <= 7075.5): y [12.65,42.35] yticks 15(5)40; x [1641.5,4248.5] xticks 2000(500)4000
D01b after the same move: ranges and ticks unchanged (FixedTicker, start/end pinned)
```
Served y2 after a dropdown move to Foreign (p1-03 critic, `served_y2.py`): Range1d(3419.7, 11764.3) before and after, while its layer now draws 4453-11385.

### E5 — twoway truth (StataNow 19.5, stcolor in batch; p1-03 §3 truth1-3.log and this file's probes)

This file's probe (`<scratch>/wp30/s21/probe/p1.do`, `p2.do`, run through `scripts/stata_slot.sh`, 03oct2026; members read as `` `.Graph.plotregion1.yscale.curmin' `` etc.):
```
P01 y 10 41 x 1760 5000 ymaj 10 10 40                    (scatter mpg weight: cur and major min/delta/max)
P14 y 10.35823917388916 10 41                            ((scatter)(lfit): y min, curmin, curmax)
B01 y 12 10 41 ymaj 10 10 40                             (bar mpg weight: the 0 base is not a tick input)
Y2 10 10 40                                              ((scatter price weight)(scatter mpg weight, yaxis(2)))
X2 0 5000 15000                                          ((scatter mpg weight)(scatter mpg price, xaxis(2)))
P17 y2 0 5000 15000                                      ((scatter mpg weight)(scatter price weight, yaxis(2)))
Q08 y2 4000 2000 14000 y1 15 5 40                        (the same, if foreign)
Q01 y 14 41 15 5 40 x 1500 4130 1500 500 4000            (scatter mpg weight if price<=7075.5)
```
From p1-03 §3 and the critic's t1-t3.log:
- P03 lfit: y min 1458.39, cur [0, 15906], ticks 0(5000)15000.
- Q02 by(foreign): both panels min 1405.87, cur [0, 15906].
- P05 scatteri 50 1000: y cur [10, 50], x cur [1000, 5000].
- P06 log: y cur [3291, 15906], 5000(5000)15000.
- P08 histogram: y 0(.02).1. P09 bar price rep78: x cur [.5, 5.5], 1(1)5.
- P12 function: y 0(2)10, x 0(1)3. P15 kdensity: y 0(.02).08. P16 if foreign: y 15(5)40, x 1500(500)3500.
- P20 qfitci: y cur [9.97, 41]. Q06 lfit if price<=7075.5: y cur [13.79, 41], 15(5)40.
- Q09 rarea: y 10(10)50. Q10 spike, Q11 dropline, P22 area: y cur [10, 41]. B06 bar base(5): cur [5, 41], ticks still 10(10)40.
- Q12 log/log: y 10(10)40, x 2000(1000)5000.
- yline(50), xline(6000), text(50 6000 "hi") and mlabel(make) leave the scale unchanged; scatteri msymbol(none) and pcarrowi extend it (L01-L07).
- The default is `#5` (P01b equals P01), and stcolor, s1mono, s2color and economist tick alike.

### E6 — the margin rule (p1-03 §3, SVG exports read by `scripts/svg_truth.py`)

```
P01 stcolor 5400x3240: 71.4/71.2 SVG units each side = 0.0220 of min(W,H)
P02 s2color 3960x2880: 63.3 = 0.0220     P13 xsize(4) ysize(4): 63.4 = 0.0220
B02 title+legend+note: 71.2 = 0.0220     B03 s2color xsize(10) ysize(3) 7200x2160: 47.5 = 0.0220
B01 by(foreign), panel 1: 60.5 = 0.0187 = 0.85 x 0.0220
```
The share of the inner span is per-axis and per-aspect (P01 y 2.84%, x 1.54%), so D1 (b)'s build-time fraction f_x = r·min(W,H)/W, f_y = r·min(W,H)/H (P01: 0.0132, 0.022) is within A6's tolerance. The shipped graph sizes are stcolor 7.5 × 4.5, s2color 5.5 × 4 and economist 2.2 × 2.2 (dash-*.scheme `graphsize x/y`). In data units the pad is f/(1−2f) × span, in log10 units on a log axis.

### E7 — by()'s size multiplier

`bygraph_g.class:1254-1258` calls `.plotregion1.scale_gmetric ceil(sqrt(.full_n)) by_knot1 by_slope1 by_slope2`. `grid.class:1551-1572` gives `resz = 1 − (n−1)/n·b1 [− (b2−b1)(n−k1)/n when n > k1]`. scheme-s2color.scheme:62-64 has `by_slope1 .3`, `by_knot1 3` and `by_slope2 1`, and no other scheme in ado/base/s writes `special by_*` (grep). Measured, `.Graph.plotregion1.gmetric_mult`:
```
BY foreign gmetric .85      BY g3 gmetric .85      BY g6 gmetric .8      BY g10 gmetric .6
```

### E8 — scheme keys (Stata's own files)

- scheme-s2color.scheme:291-292 has `numticks_g horizontal_major 5` and `numticks_g vertical_major 5`; scheme-economist.scheme:103-104 has the same.
- scheme-s2color.scheme:719 has `margin twoway medsmall`; scheme-economist.scheme:235 has `margin twoway vsmall`.
- `margin-medsmall.style` sets each side to `scheme medsmmargin`, and scheme-s2color.scheme:197 has `gsize medsmmargin relative2p2`, which is 2.2.
- The ladder `margin-{zero,tiny,vsmall,small,medium,medlarge,large,vlarge}.style` → `gsize` 0, .3, .6, 1.2, 3.5, 5, 8, 12 (s2color:195-204).
- No other shipped scheme overrides `numticks_g` or `margin twoway`; all 26 reach them through `#include`.

### E9 — the move paths, the call sites and the copy lists

- **Saved.**
  - `_FILTER_JS` (18562) ends with the stale-cue block at 19286-19351, "Last, outside every loop above", then `""").replace("__DASH_ROW_ID__", json.dumps(_ROW_ID_COLUMN))` (19352). No statement writes a range or a ticker.
  - Its args are placeholders in `build_dropdown` (19495-19523; `code=_FILTER_JS` at 19525), `build_slider` (19587) and `build_range` (19650), filled by `_build_filter_widgets`' loop at 32248-32269.
  - `render()` calls `self._build_filter_widgets(filters_cfg, link_names, kpis)` at 32707, then `_wire_brush_callbacks` at 32713.
- **Served.**
  - `_make_filter_cb` (35828) defines `_on_filter_change` (35854): "2. Replace raw source data" (35856), "3. Recompute aggregated sources" (35978), "4. Recompute filter-mode KPIs" (36049). Nothing re-finishes an axis.
  - Widgets are wired at 36076. `figures` (34911), `_facet_map` (35531) and the per-graph `_dash_share_by_scales` call (35653-35654) are in scope.
- **Build calls, saved / served.**
  - `_dash_apply_axis_options`: 30405 / 35268.
  - `_dash_finish_secondary_axes`: 30660 / 35417.
  - `_dash_limit_ranges_to_primary`: 30674 / 35425.
  - `_dash_keep_primary_ranges`: 30677 / 35428.
  - `_dash_finish_count_ticks`: 30679 / 35430.
  - The by() share: 31669 / 35653.
  - Figure creation: `fig = bokeh_figure(**fig_kwargs)` at 30309 / `"        fig = bokeh_figure(**_fig_kw)",` at 35192.
  - Per-layer renderers: `_layer_renderers = list(fig.renderers[_r_before:])` at 30611 / the `_dash_note_empty_layer(gname, pi + 1, ptype, len(g_df),` line at 35405 (loop variables `opts`, `ptype`, `_r_before`).
- **Copy lists.**
  - Constants: `"_DASH_TICK_MAJOR_JS", "_DASH_TICK_EXTRA_JS",` / `"_DASH_TICK_EVERY_JS",` at 32942-32943.
  - Functions: `"_dash_natscale_ticks", "_dash_count_ticker",` / `"_dash_count_of", "_dash_finish_count_ticks",` at 33250-33251.
  - Already listed: `_dash_padded_range`, `_dash_range_hull`, `_dash_hull_ranges`, `_dash_axis_hull` (33255-33257), `_dash_count_axes`, `_dash_place_count_ticks`, `_dash_common_count_ticks`, `_dash_share_by_scales` (33269-33271), `_dash_secondary_values` and `_dash_finish_secondary_axes` (33245-33246).
- **Test harness.**
  - `test/js_runner.py` `stand_in` encodes only `value`/`start`/`end`/`step`/`indices`/`width` (:149-175). `RUNNER` returns only text/width/visible/muted/label (:207-217), and the commit (:314-336) writes back nothing else.
  - Range1d in bokeh 3.9 has `reset_start`/`reset_end`; FixedTicker has `minor_ticks` (default []).

### E10 — tests that pin today's behaviour (flip in place, never delete; 21-24 re-measures)

| # | Node | Pins today |
|---|---|---|
| F1 | `test/test_axis_extents.py::TestLabelValuesWidenTheAxis::test_norescale_draws_the_labels_and_keeps_the_extent` (:177) | y is a DataRange1d |
| F2 | `…::TestLabelValuesWidenTheAxis::test_ytick_50_widens_and_norescale_does_not` (:197) | DataRange1d |
| F3 | `…::TestRangeOnlyWidens::test_a_non_number_is_named_once_and_the_axis_left_alone` (:261) | DataRange1d |
| F4 | `…::TestLogAndDateAxes::test_a_log_hull_is_padded_in_log_space` (:304-312) | 5% in log space |
| F5 | `…::TestLogAndDateAxes::test_a_degenerate_hull_is_widened_by_one_unit` (:327-333) | 19.0 − 0.1 / 21.0 + 0.1 |
| F6 | `…::TestReverse::test_reverse_alone_keeps_the_flipped_datarange` (:348) | flipped DataRange1d |
| F7 | `…::TestComputedLayers::test_a_fit_beside_a_scatter_with_range_0` (:450) | `x_range.renderers` |
| F8 | `…::TestPrimaryRenderersInBothModes::test_the_served_datarange_is_limited_like_the_saved_one` (:490) | renderers = {Scatter} |
| F9 | `…::TestTheHelpers::test_limit_ranges_to_primary` (:542-544) | renderers == [ra] |
| F10 | `…::TestTheHelpers::test_hull_ranges_leaves_an_axis_without_a_hull` (:549) | DataRange1d kept |
| F11 | `…::TestTheHelpers::test_range_hull_inverts_padded_range` (:516) | 1.1 inverse only |
| F12 | `test/test_by_scales.py::TestPanelsShareOneScale::test_default_shares_x_and_y` (:319) | shared DataRange1d renderers |
| F13 | `…::TestPanelsShareOneScale::test_auto_ranged_layers_share` (:338) | renderers == [] |
| F14 | `…::TestPanelsShareOneScale::test_a_linked_by_graph_shares` (:360) | renderers |
| F15 | `…::TestSharingStaysInOneGraph::test_two_by_graphs` (:572-577) | renderers |
| F16 | `…::TestTheHelpers::test_share_by_scales_units` (:642-652) | DataRange1d |
| F17 | `…::TestAfterAFilterMove::test_the_shared_range_spans_the_union_after_a_move_served` | `_emulated_hull` of a DataRange1d |
| F18 | `…::TestAfterAFilterMove::test_the_shared_range_spans_the_union_after_a_move_saved` (:552) | no Range1d in any callback arg |
| F19 | `test/test_by_scales.py` module docstring (:177 `_emulated_hull`) and `test/test_by_scales_chrome.py` module docstring (:5-9) | "a DataRange1d shared …" (text only) |
| F20 | `test/test_help_claims_7.py::TestTheSecondAxisIsItsOwn::test_the_first_axis_is_scaled_to_its_own_layers` (:980-990) | DataRange1d renderers |
| F21 | `…::TestTheSecondAxisIsItsOwn::test_a_figure_without_a_second_axis_keeps_its_range` (:1003-1004) | `renderers == []` |
| F22 | `…::TestTheSecondAxisFitsTheLayer::test_the_right_hand_axis_spans_the_layer` and `::test_the_top_axis_spans_the_layer` | span ≤ 1.25 × data (ticks now widen it: P17 0..15906 over 3291..15906) |
| F23 | `test/test_help_claims_8.py::TestXtickDrawsMarksWithoutLabels::test_alone_it_keeps_the_default_labels`, `::test_ytick_alone_keeps_the_default_labels`, `::test_minmax_marks_the_extremes`, `::test_a_count_marks_about_that_many`, `::test_xtick_none_changes_nothing` (:178-257) | `("auto", "BasicTicker")` base |
| F24 | `…::TestTheTickMarkCodeCarriesNoUserText::test_a_huge_request_is_bounded` (:317) | BasicTicker base |
| F25 | `…::TestDashDrawsBokehsMinorTicks::test_the_default_axis_has_minor_ticks` (:1228) | BasicTicker (flipped here: register P1.2.7 gives this flip to P1.3) |
| F26 | `test/test_help_claims_2.py::TestLabelsUsedAutomatically::test_an_axis_is_labelled_with_numbers` (:597) | BasicTicker |
| F27 | `test/test_axis_options.py::TestAxisLabelGrammar::test_xtick_is_honoured` (:224-228) | base is a BasicTicker |
| F28 | `test/test_html_output.py::TestXrangeYrange::test_xrange_embeds_unique_start_value`, `::test_yrange_embeds_unique_end_value`, `::test_xrange_invalid_ignores_gracefully`, `::test_yrange_invalid_ignores_gracefully` (:1631-1692) | the other axis is a DataRange1d; 1.1 inverse |
| F29 | `test/test_function_audit.py::TestAColourKeyDoesNotWidenTheFirstAxis::test_a_colour_key_swatch_is_not_ranged_over` (:835) | `y_range.renderers` |
| F30 | `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (:393) | the single-y page digest (R10) |
| F31 | `test/test_gaps2_truth.cscript` S18 block AE-01..AE-05 (:1095-1180) | the page's hull inverted with `/1.1`; AE-05 "no Range1d on y" |
| F32 | `test/test_wp29_truth.cscript` S10 block BSC-01..BSC-07 (:3906-4023) | `_hull_of` compared with twoway's data `.min/.max`; S21's Range1d hull spans its ticks, twoway's `curmin/curmax` |
| F33 | `test/test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` | the bounds S15 measured (S15 15-18 moves them from 80-140; moves here only if S21's three keys cross S15's upper bound; R10) |

Guards expected to stay green unedited include `test_natscale.py::TestBothModesDrawTwowaysTicks`, `test_natscale_axes.py::TestByPanelsShareOneScale::test_ylabel_count` (≤/≥ assertions), `test_axis_options.py::TestSecondaryAxisRange` and `test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_hundred_panels_settle`. 21-24 measures them.

### E11 — fixtures on disk

`test/fixtures/natscale_truth.json` and `natscale_axes_truth.json` (S3), `axis_truth.json` (WP-28 B2, group `b2_extent`), `by_scales_truth.json` (WP-29 P0.2) and `scheme_truth.json` (S07/S15) are read only. A new `default_axes_truth.json` is added (Stata truth).

## User stories

- **US-21.1** As a twoway user, I want `scatter mpg weight` with no `xlabel()`/`ylabel()` labelled 10 20 30 40 and 2000 3000 4000 5000, as twoway labels it, with no minor ticks, so my dashboard reads like my Stata graph.
- **US-21.2** As a twoway user, I want a fit line, CI band, `scatteri` point or `function` curve inside the axis, as twoway draws it, so no layer is clipped, in by() panels too.
- **US-21.3** As a dashboard publisher, I want the plot-region margin twoway leaves around the data, under every shipped scheme (economist's narrower), so the points never touch the frame.
- **US-21.4** As a twoway user, I want a right-hand or top axis with no `ylabel2()`/`xlabel2()` ticked by the same rule.
- **US-21.5** As a dashboard publisher, I want each filter move to re-tick and re-range the default and `#N` axes over the rows it keeps, the second axes included, in the saved page and the served app alike, so the axes match what twoway draws for the same `if`.
- **US-21.6** As a dashboard publisher, I want zooming to keep sensible labels, and Reset to return to the current extent.

## Business requirements

- **BR-21.1** A default numeric, log or `%tc` axis, and a y2/x2 without its own label rule, shows twoway's natscale ticks for N = the scheme's `numticks_g horizontal_major` (x) or `vertical_major` (y), over the hull of every drawn layer and its `range()` values. It shows no minor ticks. `%td`-`%ty` default axes are S44's.
- **BR-21.2** The axis extent is the hull of every drawn layer, its ticks, its label and tick positions (unless `norescale`), its `range()` values and every bar's full width. Default bar, area, spike and dropline bases are not in it (until S27); an explicit `base()` is. Reference lines, text, marker labels and colour-key swatches are not in it. scatteri, pci, pcarrowi and function layers on a date axis are not in it (until S35).
- **BR-21.3** Around the hull is twoway's plot-region margin: r × min(W,H) a side, r = 2.2% (economist 0.6%), from the scheme's `margin twoway`. A by() panel's r is multiplied by f(G). It is placed within about 0.8% of the figure width of twoway's.
- **BR-21.4** A by() graph's shared axes are one range over the union of every panel's hull, fits included; rescaled axes are per panel.
- **BR-21.5** After every filter move, in both modes:
  - default and `#N` axes (y2/x2 included) are re-ticked and re-ranged over the kept rows;
  - explicit-value axes re-hull their data part and keep their labels;
  - the D-21e forms hold;
  - Reset returns to the new extent.
  - The saved page and the served app give equal ticks and equal ranges (within 1e-9 relative) whenever both draw the same layers after the move; a layer the saved page leaves unfiltered (D-21e2) stays in its saved hull as drawn.
- **BR-21.6** A zoom or pan re-ticks a default or `#N` axis by natscale over the visible range. Back at the reset extent, it shows the finisher's ticks.
- **BR-21.7** Budgets: the served re-finish adds ≤ 0.2 s per figure per move at 500k rows. 100 saved by() panels settle within 1 s of the batch-7 base's measured time.
- **BR-21.8** No note is printed for any of this (M6), and no option is refused.

## Technical requirements

- **TR-21.1 Scheme keys** (scripts/extract_scheme_truth.py; 26 files; `scheme_truth.json`; SchemeParser).
  - The extractor resolves `numticks_g horizontal_major`, `numticks_g vertical_major` and `margin twoway` through the include chain, with provenance. It records `numticks_horizontal_major`, `numticks_vertical_major`, `margin_twoway` (the marginstyle name) and `margin_twoway_rs` (its resolved relative value, after asserting that all four sides of the margin style are equal) in `scheme_truth.json`. It writes the three directives into each `dash-<name>.scheme` through `expected_directives`.
  - `SchemeParser._init_properties` gains:
    - `numticks_x = _bounded_int("numticks_g horizontal_major", 5, 1, 25, …)` and `numticks_y` likewise;
    - `plot_margin_rs`, from `_DASH_MARGIN_RS.get(self._props.get("margin twoway","").strip(), 2.2)`.
  - `_FALLBACK_PROPS` gains `"numticks_g horizontal_major": "5"`, `"numticks_g vertical_major": "5"` and `"margin twoway": "medsmall"`.
- **TR-21.2 New constants**, defined beside `_DASH_COUNT_TAG` (22085):
  - `_DASH_DEFAULT_TAG = "dash_default"`;
  - `_DASH_MARGIN_RS` (D-21a);
  - `_DASH_BY_GMETRIC = (3.0, 0.3, 1.0)` (D-21b);
  - `_DASH_AXIS_FINISH_JS` and `_DASH_AXIS_ZOOM_JS` (TR-21.10, TR-21.11).
- **TR-21.3 `_dash_default_ticker(n)`** (beside `_dash_count_ticker`). It returns `FixedTicker(ticks=[], minor_ticks=[], tags=[_DASH_COUNT_TAG + str(n), _DASH_DEFAULT_TAG])`, with n clamped to 1.._MAX_AXIS_TICKS.
- **TR-21.4 `_dash_plot_margin(scheme, graph_opts, panels=1)`** returns `{"x": fx, "y": fy}`:
  - W, H are xsize()/ysize() read through `_stat_option_float` with `_dash_figure_aspect`'s rule (a non-positive or unreadable value falls back silently here, since `_dash_figure_aspect` already named it), else the scheme's `graphsize_x/graphsize_y`, else 5.5 × 4;
  - r = scheme.plot_margin_rs / 100 × f(panels) (D-21b);
  - fx = r·min(W,H)/W and fy = r·min(W,H)/H, each clamped to [0, 0.45]; a non-finite value gives the s2color default.
  - It is pure: it reads no figure.
- **TR-21.5 Figure stamps, both modes.** Right after `fig = bokeh_figure(...)` (saved 30309 in `_make_figure_body`; served 35192 in `_dash_figure_for`):
  - `fig._dash_margin = _dash_plot_margin(<scheme>, <graph options>)`;
  - `fig._dash_margin_args = (<scheme>, <graph options>)`;
  - `fig._dash_numticks = {"x": scheme.numticks_x, "y": scheme.numticks_y}`.

  The saved scheme is `self.scheme`, the served one `_DASH_SCHEME`. These are Python attributes only. `_dash_share_by_scales` recomputes `_dash_margin` with `panels=len(figs)` from `_dash_margin_args`.
- **TR-21.6 Default tickers.**
  - `_dash_apply_axis_options` installs `_dash_default_ticker(fig._dash_numticks[letter])` on each primary axis that is a `ContinuousAxis` when `raw` is empty or its spec's mode is "default", and the axis's date kind is None, "tc" or "tC" (a LogAxis counts as numeric). It does so before `_dash_apply_tick_option`, so `xtick()` wraps it as `base`.
  - `_dash_finish_secondary_axes` installs the default ticker on a y2/x2 LinearAxis/LogAxis whose `ylabel2()`/`xlabel2()` is empty or mode "default". It records `fig._dash_scale_values2[name]` (the `range()` values `want`) and `fig._dash_scale_reverse2[name]`. It pads with `margin=fig._dash_margin[letter]`.
- **TR-21.7 Hull roles and the reader.**
  - `_dash_tag_hull_roles(renderers, ptype, options)` implements D-21g and is called right after each layer is drawn: saved after 30611, served before the 35405 call.
  - `_dash_layer_extent(renderers, range_attr, name, kind=None)` returns `(lo, hi)` or None. It reads, with numpy, every coordinate field of `_DASH_Y_COORDS`/`_DASH_X_COORDS` and every numeric constant over each renderer's view rows (IndexFilter `indices`, BooleanFilter `booleans`). It skips swatches, renderers on another range, the `_dash_auto_base` properties, and `_dash_raw_sif` renderers when `kind` is a date kind. Only finite values count (positive on "log").
  - `_dash_secondary_values` skips the `_dash_auto_base` properties too.
  - None of these define nested functions, so no `<locals>` map keys are needed.
- **TR-21.8 The finisher chain** (one code path for build and re-finish; ranges updated in place).
  - `_dash_count_axes(fig, every_axis=False)` takes lo/hi from `_dash_layer_extent` over `fig.renderers`. The primary-limited x pool and its comment are removed (D-21i). Each entry gains `default` (the ticker carries `_DASH_DEFAULT_TAG`) and `hold`: True on a re-finish for a `_DASH_TS_UNITS` kind and for `every`.
  - `_dash_place_count_ticks(e, lo, hi, common=False)` writes ticks only:
    - into a FixedTicker base, in place (`base.ticks = …`);
    - for a BasicTicker `#N` placeholder, through a new `FixedTicker(ticks=…, tags=list(base.tags))` set as `ax.ticker` or as `t.args["base"]`.

    The range-pinning block (23452-23486) is removed. `common` is kept for its callers and documented as not affecting the extent.
  - `_dash_axis_hull(fig, e)` always returns the hull of the explicit values, the data lo/hi, the placed or held ticks and the bar full widths, or None only when nothing is finite. On a y2/x2 entry it adds `fig._dash_scale_values2[name]`. The bar-width loop is vectorised.
  - `_dash_padded_range(lo, hi, kind=None, reverse=False, margin=None)`:
    - `margin` is a frame fraction f in [0, 0.45); the pad is f/(1−2f) × span (log10 span on "log");
    - None keeps today's 5% (for hand-built test ranges);
    - the result carries `_dash_margin_f = f` (None for legacy) and `reset_start/reset_end` equal to start/end.

    `_dash_range_hull(rng, kind=None, margin=None)` inverts it with p = f/(1−2f): `margin`, else `rng._dash_margin_f`, else 5%. It stays TEST_ONLY and is never called at run time.
  - `_dash_hull_ranges(fig, entries, common=None, made=None)` handles every name: the default ranges and `extra_*_ranges[name]`.
    - The margin is `fig._dash_margin[letter]`. Reverse is `fig._dash_scale_reverse` or `fig._dash_scale_reverse2[name]`.
    - When the current range is a Range1d carrying `_dash_margin_f`, it writes `reset_start`, `reset_end`, `start` and `end` in place. Otherwise it sets a new Range1d. `made` maps a by() hull key to the one shared object.
    - An entry with no hull keeps its range (hold).
  - `_dash_finish_count_ticks(fig, refinish=False)`: on `refinish`, entries with `hold` keep their ticks, which still join the hull. Otherwise it is as today, then `_dash_hull_ranges(fig, entries)`.
  - `_dash_common_count_ticks(figs, letters)` covers every range name (keys `(name, letter)`) and passes `made`, so the shared object is updated in place.
  - `_dash_share_by_scales(figs, rescale)`:
    1. recomputes each panel's `_dash_margin` with `panels=len(figs)`;
    2. re-pads rescaled letters per panel with `_dash_hull_ranges`;
    3. removes the DataRange1d-sharing block (23870-23896) and the y2/x2 block (23897-23909), which `_dash_common_count_ticks` now covers;
    4. calls `_dash_common_count_ticks(figs, letters)`.
  - `_dash_limit_ranges_to_primary(fig, source)` sets each remaining DataRange1d's renderers to every non-swatch renderer: the computed layers stay in. `source` is kept for its callers. `_dash_keep_primary_ranges` is unchanged in form; its pool now holds every layer.
- **TR-21.9 `_dash_refinish_axes(figures, facet_map)`** (served move path).
  - For each graph group (a by() graph's panels in `facet_map` order, else one figure), it runs `_dash_finish_count_ticks(f, refinish=True)` for each figure, then `_dash_common_count_ticks(group, letters)` with letters = x/y minus the first panel's `_dash_rescaled`.
  - It is idempotent. A figure with no stamps is skipped.
  - It is called in `_on_filter_change` after step 3 and before "# 4. Recompute filter-mode KPIs" (36049), through two new `_make_filter_cb` keyword parameters `_axis_figs=None, _axis_fmap=None`, passed `figures` and `_facet_map` at the wiring site (36076-36084).
- **TR-21.10 `_dash_axis_plan(figures, facet_map, zoom=True)`** returns `(plan_json, models)` for the saved re-finish and both modes' zoom.
  - `models` is a list of Range1d, FixedTicker, ColumnDataSource and filter models, deduplicated by identity.
  - The plan JSON (`json.dumps(…, allow_nan=False)`) holds, per group, `share` (letters), and per panel per axis:
    - `letter`, `name`, `kind` (None/"log"/"tc"/"tC"/a ts kind), `mode` ("count", "explicit" or "none"), `n`, `hold`;
    - `held` and `explicit` (numbers);
    - `extra` (the `#N` list's union ticks), `scale` (`range()` values);
    - `reverse`, `margin`;
    - `range` and `ticker` (model indexes, −1 for none);
    - `layers`: `[{"src": i, "filt": j or -1, "fields": [...], "consts": [...]}]`;
    - `bars`: `[{"src": i, "filt": j, "centre": field or number, "size": field or number}]`.
  - It holds no user text except field names (column names, length ≤ 255, read with a hasOwnProperty guard in JS). It never holds code.
  - With `zoom`, it attaches ONE `CustomJS(args={"plan_json": …, "models": models}, code=_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS)` to `start` and `end` of every planned Range1d whose axis is count or default.
- **TR-21.11 The saved re-finish.**
  - `_DASH_AXIS_FINISH_JS` (pure arithmetic, no DOM, no `eval`, no BokehJS view internals) defines:
    - `dash_natscale` (a line-for-line port of `_dash_natscale_ticks`, with `%.15g` as `Number(v.toPrecision(15))` and the same iteration and tie order);
    - `dash_axis_ticks` (the log, tc and linear rules; ts kinds return null);
    - `dash_axis_extent` (the reader);
    - `dash_axis_pad` (`_dash_padded_range`, with the degenerate widening, calendar months via UTC Date);
    - `dash_axis_compute` and `dash_axis_finish(plan, models)`.

    It writes ticks first, then each range with one `rng.setv({reset_start: s, reset_end: e, start: s, end: e})`, so the zoom callback on `start`/`end` never sees one end new and the other old. Around that write it sets the plain JS property `rng._dash_finishing = true` (never serialised), and `_DASH_AXIS_ZOOM_JS` returns at once while `cb_obj._dash_finishing` is true, so a re-finish does not run the zoom code once per range per end (100 shared panels would otherwise recompute the finisher several extra times per move). When start and end are unchanged but the ticks changed, it calls `rng.change.emit()`, the same public signal `_FILTER_JS` emits on sources. In served mode the Python writes reach the browser as separate events; the zoom code writes only when its ticks differ, and at the reset extent its ticks equal Python's (the twin), so the final state is the server's.
  - The `__DASH_*__` tokens for `_DASH_NATSCALE_UNCOVERED`, `_DASH_NATSCALE_DENSITY`, `_DASH_NATSCALE_SIDE`, `_DASH_NATSCALE_INT_LIMIT`, `_MAX_AXIS_TICKS` and `_STATA_EPOCH_UNIX_MS` are replaced with `repr()` at import.
  - `_FILTER_JS` is defined at 18562, before `_MAX_AXIS_TICKS` (22070), `_DASH_NATSCALE_*` (22078-22082) and `_DASH_TICK_EVERY_JS` (22878), so its literal cannot name `_DASH_AXIS_FINISH_JS` (a NameError at import; review pass). Instead, directly after `_DASH_AXIS_FINISH_JS` and `_DASH_AXIS_ZOOM_JS` are defined, one module-level statement extends it: `_FILTER_JS = _FILTER_JS + _DASH_AXIS_FINISH_JS + 'if (typeof axis_plans_json !== "undefined" && axis_models) { dash_axis_finish(JSON.parse(axis_plans_json), axis_models); }\n'`, with a comment naming WP-30 P1.3a. Nothing reads `_FILTER_JS` at import before that line (its other uses are inside functions or comments, measured at `c96facd`), and `_wire_brush_callbacks`' `index()` slices find their markers before the appended text. The finish JS holds no `__DASH_ROW_ID__` token, and its top-level names (`dash_natscale`, `dash_axis_*`) collide with none of `_FILTER_JS`'s (`dash_own_col`, `dash_mask_for`, `dash_scale`, `dash_pctl`, …). `_DASH_AXIS_ZOOM_JS` handles `cb_obj` (D-21d).
- **TR-21.12 Saved wiring** (D-21f).
  - `build_dropdown`, `build_slider` and `build_range` add `"axis_plans_json": "[]"` and `"axis_models": []` to their args.
  - `DashRenderer.render()` gains step "5b" after 32707:
    1. `_plan, _models = _dash_axis_plan(self.figures, self._facet_map)`;
    2. for each `cb` in `self.filter_callbacks`: `cb.args["axis_plans_json"] = _plan` and `cb.args["axis_models"] = _models`.
- **TR-21.13 Served template** (`_generate_app_source`):
  - the TR-21.5 stamps in `_dash_figure_for`;
  - the TR-21.7 call in the plot loop;
  - `_dash_axis_plan(figures, _facet_map, zoom=True)` once, after the graph loop (after 35654, before "# ---- Persist per-graph qualifier metadata");
  - the TR-21.9 parameters and call.
- **TR-21.14 Copy lists (R2 row S21).**
  - Constants, after `"_DASH_TICK_EVERY_JS",` (32943): `"_DASH_DEFAULT_TAG", "_DASH_MARGIN_RS", "_DASH_BY_GMETRIC", "_DASH_AXIS_FINISH_JS", "_DASH_AXIS_ZOOM_JS",`.
  - Functions, after `"_dash_count_of", "_dash_finish_count_ticks",` (33251): `"_dash_default_ticker", "_dash_plot_margin", "_dash_axis_plan", "_dash_layer_extent", "_dash_tag_hull_roles", "_dash_refinish_axes",`. `_dash_refinish_axes` stays last, so S27's anchor "after S21's `_dash_refinish_axes`" holds.
  - `SchemeParser` travels with its class.
- **TR-21.15 Maps.** Under S21's anchor in `test/function_test_map.py` `FUNCTIONS`, in alphabetical order: `_dash_axis_plan`, `_dash_default_ticker`, `_dash_layer_extent`, `_dash_plot_margin`, `_dash_refinish_axes` and `_dash_tag_hull_roles`, each naming its TestTheHelpers test. `test/program_coverage_map.py` is unchanged: there is no new Stata program.
- **TR-21.16 Security (rule 1).** Every JS string is a module constant with no user text. Plans and models travel in `args` as JSON text and model references. Field names are read with `Object.prototype.hasOwnProperty.call`. JSON numbers are finite (`allow_nan=False`). The extractor and the tests use no `shell=True`. The fixture writer never calls Stata.

## Boundaries

- **Not touched:** `_dash_count_ticker` (signature and body), `_dash_apply_axis_spec`, `_dash_apply_tick_option`, `_dash_natscale_ticks`, `_dash_axis_count_ticks`, `_dash_tsnatscale_ticks`, `_build_sources_and_figures`, `_build_filter_widgets`, `_dash_add_secondary_axes`, `_dash_apply_scale_ranges`, the four appliers and every mapper (`map_*`).
- **Batch partners.**
  - S19: `_dash_axis_labels`, `_dash_add_secondary_axes`, the legend helpers, `map_scatteri`, `_DASH_FIT_KEYS`, help "Statistical Layer Options".
  - S20: dash.ado validators, help :740-742 and :3233.
- **Later sections.**
  - S27: auto-base clamping (`_dash_finish_auto_bases`), replacing D7 a.
  - S35: raw-SIF layers on date axes, the CustomJSTransform, y2/x2 date kinds.
  - S44: the `%td`-`%ty` default ticker, its JS port, and lifting the date hold.
  - S47: `plotregion(margin())` and the inner box. S21 leaves `plotregion(margin())` ignored and silent, as today.
  - S49: horizontal and HBar hulls. S50: extend/noextend over the hull. S52: `add`.
  - S48: iscale (S21 uses only the default f(G)) and the by() grid. S53: outer axes, by() legend. S54: the toolbar row, except D-21h's one sentence. S57: the served worker.
- **Not in WP-30's scope:** an exact live-frame margin (D1 a); the colour key's ticks (`zlabel` default, 26172); categorical axes.

## Stata truth

**Extractor (new):** `scripts/extract_default_axes_truth.do`, in S02's path-free form.
- **Header.** A comment names the run line, then TR-02.9's root stanza with `<file>` = `extract_default_axes_truth.do`, then `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `clear all`, `set more off`, `set linesize 255` and `version 19`.
- **`_meta`.** Locals `c(stata_version)` and `c(born_date)`; `git -C "`repo'" rev-parse HEAD`, written by `shell` to a tempfile and read back with `file read`; and `c(current_date)`. These follow `extract_join_order_truth.do`'s form.
- **Recorder.** A program `_ns_rec` (p1-03's `rec1`) records for each graph, and for each by() panel (`.Graph.graphs[k]`): `y`/`x` `.plotregion1.{y,x}scale.{min,max,curmin,curmax}`, `.{y,x}axis1.major.{min,delta,max}`, and `yaxis2`/`xaxis2` major when present. `.Graph.plotregion1.gmetric_mult` is recorded for by() graphs.
- **SVGs.** Each SVG probe runs `graph export "<work>/<id>.svg", replace`.
- **Python block.** It reads the SVGs through `scripts/svg_truth.py`'s `svg_document` and `svg_axis_extent`. It writes `margin_rel` (distance from the plot-region edge to curmin's pixel, divided by min(W,H) of the SVG canvas) and `frame_frac` (the same distance over the plot-region extent) per axis. It writes `test/fixtures/default_axes_truth.json` with `json.dump(…, indent=1, sort_keys=True)`. It reads locals through `Macro.getLocal`, never calls Stata, never uses `shell=True`, and writes a backtick as `\x60`.

**Probe keys** (`probes.<id>`: `{cmd, scheme, data, y, x, y2?, x2?, panels?, gmetric?, svg?}`; data `sysuse auto` unless named; scheme stcolor unless named):
- `P01` `twoway scatter mpg weight` (svg); `P01b` …, `ylabel(#5) xlabel(#5)`; `P02` `scheme(s2color)` (svg); `P10` `scheme(economist)` (svg); `P13` `xsize(4) ysize(4)` (svg); `B03` `scheme(s2color) xsize(10) ysize(3)` (svg); `B02` with `title() legend(on) note()` (svg).
- `P03` `(scatter price mpg) (lfit price mpg)`; `P05` `(scatter mpg weight) (scatteri 50 1000)`; `P06` `scatter price weight, yscale(log)`; `P08` `histogram mpg`; `P09` `bar price rep78`; `P12` `function y=x^2, range(0 3)`; `P14` `(scatter mpg weight) (lfit mpg weight)`; `P15` `kdensity mpg`; `P16` `scatter mpg weight if foreign`; `P17` `(scatter mpg weight) (scatter price weight, yaxis(2))`; `X2` `(scatter mpg weight) (scatter mpg price, xaxis(2))`; `P20` `(scatter mpg weight) (qfitci mpg weight)`.
- `Q01` `scatter mpg weight if price<=7075.5`; `Q02` `(scatter price mpg) (lfit price mpg), by(foreign)`; `Q06` `(scatter mpg weight) (lfit mpg weight) if price<=7075.5`; `Q08` `P17 if foreign`; `Q09` `rarea mpg turn weight`; `Q10` `spike mpg weight`; `Q11` `dropline mpg weight`; `P22` `area mpg weight`; `B01` `bar mpg weight`; `B06` `bar mpg weight, base(5)`; `Q12` `scatter mpg weight, yscale(log) xscale(log)`.
- `L00` `scatter mpg weight`; `L01` `…, yline(50)`; `L02` `…, xline(6000)`; `L03` `…, text(50 6000 "hi")`; `L04` `…, mlabel(make)`; `L05` `(scatter mpg weight) (scatteri 50 6000, msymbol(none))`; `L07` `(scatter mpg weight) (pcarrowi 50 6000 45 5500)`.
- `TC` `scatter mpg t` with `t = clock("2001-01-01 00:00:00","YMDhms") + _n*7*3600000`, `format t %tc`.
- `BY2` `scatter mpg weight, by(foreign)` (svg), and `BY3`, `BY6`, `BY10` `… , by(g)` with `g = mod(_n, G)`: `gmetric` and panel cur.
- `schemes.<name>` `scatter mpg weight, scheme(<name>)` for the 26 names of `SchemeParser._BUILTIN_NAMES`: y and x major and cur.

`_meta` holds `stata_version`, `born_date`, `dash_commit` and `extracted`, plus `units` ("SVG 720 units per inch; margin_rel = edge-to-curmin distance / min(canvas W, H)") and `source`. The fixture is added with `git add -f test/fixtures/default_axes_truth.json` and read by `test/test_default_axes.py`, so `test_fixtures_are_committed.py` passes unedited (R7).

**Run (never the GUI, E5):**
```sh
mkdir -p <scratch>/s21/truth
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s21/truth $WT/scripts/extract_default_axes_truth.do
# log: <scratch>/s21/truth/extract_default_axes_truth.log ; fixture: $WT/test/fixtures/default_axes_truth.json
```

**Scheme regeneration** (A152): `python3 scripts/extract_scheme_truth.py` in `$WT` rewrites the 26 `dash-*.scheme` files and `test/fixtures/scheme_truth.json`. Every pre-existing probe's records are compared before and after, outside `_meta`: the only change allowed is the three new keys and their provenance lines (R7).

**Truth block** (`test/test_wp30_truth.cscript`, inside S01's S21 stub, gated by `WP30_ONLY=S21`).
- **Helpers.** Python helpers sit directly above the S21 header, in a `python:` block that `_w30` helpers call:
  - `_s21_saved(path)` reads a saved page's document (`Document.from_json` of its JSON script block);
  - `_s21_served(spec, data)` builds `make_document`;
  - `_s21_axes(fig, margin)` returns each axis's ticks and its inner hull through `dr._dash_range_hull(rng, kind, margin=)`, with the margin from `dr._dash_plot_margin` (the page loses `_dash_margin_f`);
  - `_s21_move_saved(spec, data, value)` runs the filter callback through `js_runner.JsSession` (the `python:` block puts `c(pwd)`, the driver's `test/` directory, first on `sys.path`; node is required, as for the pytest node tests);
  - `_s21_move_served(doc, value)` fires the widget's callbacks.

  Each case runs live twoway (`.Graph` members), `dash … , name(nsNN)` with `dash build` into `` `w30_work' ``, and the served document.
- **Cases** (ticks equal exactly; inner hull within 1e-6 × span of twoway's curmin/curmax):
  - **NS-01** P01: y 10(10)40, x 2000(1000)5000; inner [10,41], [1760,5000]; saved and served.
  - **NS-02** P06 log: 5000(5000)15000, inner [3291,15906]. Q12 log/log.
  - **NS-03** P03 and P14: the fit is inside the scale (curmin 0 and 10).
  - **NS-04** Q02: one Range1d object per shared axis; both panels' inner y = [0, 15906].
  - **NS-05** P17 y2 0(5000)15000; X2 x2 0(5000)15000.
  - **NS-06** B01, Q10, Q11, P22: ticks 10(10)40, inner [10,41]. B06: inner [5,41], ticks 10(10)40.
  - **NS-07** L01-L04 give L00's ticks and hull; L05 and L07 widen.
  - **NS-08** Margin: P01, P02, P10, P13, B03 `margin_rel` = r × 1 within 0.0005. Twoway's `frame_frac` and dash's `_dash_plot_margin` differ by ≤ 0.008 per axis.
  - **NS-09** by(): BY2, BY3, BY6, BY10 `gmetric` = f(G) within 1e-9, and BY2's `margin_rel` = 0.022 × 0.85 within 0.0005.
  - **NS-10** After a move, twoway `if` against the served move and the saved node move:
    - Q01 (range 3291-7075.5): y 15(5)40 [14,41], x 1500(500)4000 [1500,4130];
    - Q06: served y inner [13.79, 41]; the saved page keeps its unfiltered lfit (D-21e2), so its y inner hull is asserted equal to the hull of the kept scatter rows and the drawn fit's own y column, read from the page;
    - Q08 (dropdown Foreign): y2 4000(2000)14000, y 15(5)40.
  - **NS-11** `schemes.*`: every shipped scheme's default ticks equal twoway's in both modes.
  - **NS-12** TC: `%tc` ticks equal twoway's major positions (milliseconds) in both modes.

No area cscript gains a case: S21 adds no refusal, note or return code.

## TDD test stubs

### Regression tests, `test/test_default_axes.py` (new; red at the batch-7 base unless marked guard)

Module helpers:
- `_figs(mode, plots, go=None, scheme="stcolor", filt=None, data="auto")`, through `test_by_scales._write`/`_spec` and `test_axis_extents._figures`' two-mode form;
- `_ticks(fig, letter, name="default")`, the major ticks of the axis on that range (`ticker.ticks`, or `args["base"].ticks`);
- `_inner(fig, letter, name="default")`, `dr._dash_range_hull(rng, kind)`;
- `_T`, the fixture, loaded lazily in fixture classes only, so 21-01 runs before 21-03 writes it;
- `_served_move(doc, kind, value)`, `test_mode_parity._fire`;
- `_saved_move(r, kind, value)`, `js_runner.JsSession(r.filter_callbacks)` with the widget set and the callback run;
- `_oracle(spec, if_expr)`, `test_mode_parity._saved_with_qualifier`.

Every expectation is a literal from Evidence E5-E7.

- Test: `…::TestTheHelpers::test_the_default_ticker_is_a_tagged_fixed_ticker`. `_dash_default_ticker(5)` is a FixedTicker with `ticks == []`, `minor_ticks == []`, both tags, and `_dash_count_of(...) == 5`. Red: AttributeError.
- Test: `…::TestTheHelpers::test_the_plot_margin[stcolor|s2color|economist|xsize4]`. Expected (fx, fy): (0.0132, 0.022), (0.016, 0.022), (0.006, 0.006) and (0.022, 0.022) within 1e-12. Red: AttributeError.
- Test: `…::TestTheHelpers::test_the_by_factor[2|3|6|10]`. `_dash_plot_margin(stcolor, {}, panels=G)["y"] / 0.022` equals 0.85, 0.85, 0.8 and 0.6. Red: AttributeError.
- Test: `…::TestTheHelpers::test_a_hostile_size_is_bounded`. xsize `"1e400"`, `"-3"`, `"abc"` and `"x"*100000` each give finite fractions in [0, 0.45] in under 0.1 s. Red: AttributeError.
- Test: `…::TestTheHelpers::test_padded_range_takes_a_margin` and `::test_range_hull_inverts_any_margin`. `_dash_padded_range(10, 41, margin=0.022)` pads 0.022/0.956 × 31; the inverse is exact (1e-12) for f in {0, 0.006, 0.022, 0.2}, both kinds and both directions. Red: TypeError.
- Test: `…::TestTheHelpers::test_layer_extent_equals_the_python_reader`. Over 500 seeded random sources and views, `_dash_layer_extent` equals min/max of `_dash_secondary_values`. Red: AttributeError.
- Test: `…::TestTheHelpers::test_hull_roles[bar|bar_base|area|spike|dropline|scatteri|pci|pcarrowi|function|scatter]`. These give `{"bottom"}`, none, `{"y1"}`, `{"y0"}`, `{"y0"}`, then raw_sif True for the four literal types, and nothing for scatter. Red: AttributeError.
- Test: `…::TestTheHelpers::test_refinish_axes_is_idempotent` and `::test_axis_plan_shape`. Running twice changes nothing. The plan parses, its indexes are in range, and `models` holds no duplicate. Red: AttributeError.
- Test: `…::TestTheSchemeKeys::test_numticks_and_margin[<26 schemes>]`. `numticks_x == numticks_y == 5`; `plot_margin_rs == 2.2` (economist 0.6). Red: AttributeError.
- Test: `…::TestDefaultTicksAreTwoways::test_probe[<pid>-saved|served]`, with pid in P01, P06, P08, P09, P12, P15, P16, Q09, Q12: y and x ticks as E5. Red: BasicTicker has no `ticks`.
- Test: `…::TestNoMinorTicks::test_a_default_axis_draws_none[saved|served]`. Every default axis ticker is a FixedTicker with `minor_ticks == []`. Red: BasicTicker.
- Test: `…::TestSecondAxisDefaultTicks::test_y2[saved|served]` (0, 5000, 10000, 15000) and `::test_x2[saved|served]` (the same). Red: Bokeh's ticker.
- Test: `…::TestEveryLayerIsInTheScale::test_probe[P03|P14|P20|P05-saved|served]`. The inner y hull is [0,15906], [10,41], [9.97,41] and [10,50]; P05's x is [1000,5000]. Red: DataRange1d.
- Test: `…::TestByPanelsScaleTheirFits::test_q02[saved|served]`. Both panels share one Range1d object per axis, inner y [0, 15906]. Red: DataRange1d without the fit.
- Test: `…::TestTheExtentIsTwowaysHullAndMargin::test_p01[saved|served]`. Inner [10,41] and [1760,5000]; `rng._dash_margin_f == _dash_plot_margin(...)[letter]`. Red: DataRange1d.
- Test: `…::TestCountAxesHaveTheMargin::test_p01b[saved|served]`. `10 − 0.05×31 < y.start < 10` and `5000 < x.end`. Red: start == 10.0.
- Test: `…::TestDefaultBasesStayOut::test_type[bar|spike|dropline|area-saved|served]` (ticks 10(10)40, inner [10,41]) and `::test_an_explicit_base_widens[saved|served]` (B06 inner [5,41], ticks 10(10)40). Red: 0(10)40 or DataRange1d.
- Test: `…::TestNonRenderersStayOut::test_probe[L01|L02|L03|L04-saved|served]` (equal to L00, a Range1d) and `::test_these_widen[L05|L07-saved|served]`. Red: DataRange1d.
- Test: `…::TestRawSifDateLayersStayOut::test_scatteri_on_a_td_axis[saved|served]`. `(line close date) (scatteri 1200 15000)` on a %td frame: the x inner hull lies within the dates' span. Red: DataRange1d.
- Test: `…::TestAfterAFilterMove::test_range_move[saved|served]`. Q01 values after the RangeSlider is set to (3291, 7075.5). Red: unchanged ticks, or DataRange1d.
- Test: `…::TestAfterAFilterMove::test_fit_after_a_move[saved|served]`. Q06: served inner y [13.79, 41] (twoway's); saved inner y = the hull of the kept scatter rows and the stale lfit's drawn y column (D-21e2), so the stale lfit is not clipped. Red.
- Test: `…::TestAfterAFilterMove::test_y2_after_a_dropdown_move[saved|served]`. Q08 y2 4000(2000)14000. Red: held Range1d(3419.7, 11764.3).
- Test: `…::TestAfterAFilterMove::test_an_explicit_axis_rehulls_its_data[saved|served]`. With `xlabel(3000)` under Q01, the ticks stay [3000] and inner x = [min(rows.weight), max(rows.weight)] ∪ {3000}. Red.
- Test: `…::TestAfterAFilterMove::test_saved_equals_served_equals_the_redraw[<12 cases>]`. Over scatter, by(foreign), dual y and bar (no layer the saved page leaves unfiltered), × dropdown, range and slider: saved (node), served and the oracle agree on every axis's ticks and range within 1e-9 relative. Red.
- Test: `…::TestAfterAFilterMove::test_a_stale_fit_stays_in_the_saved_hull[dropdown|range|slider]`. scatter+lfit: served equals the oracle; the saved page's re-finished axes equal `_dash_finish_count_ticks(fig, refinish=True)` run in Python over the saved document's written data after the node move, and its y range contains the stale lfit's drawn y column (D-21e2). Red.
- Test: `…::TestAfterAMoveEdgeCases::test_a_move_that_empties_holds[saved|served]`, `::test_one_row_left[saved|served]` (natscale [v−1, v+1] reached), `::test_a_reversed_axis_stays_reversed[saved|served]` and `::test_a_log_axis_with_nothing_positive_holds[saved|served]`. Red: AttributeError, or a held DataRange1d.
- Test: `…::TestResetReturnsToTheCurrentExtent::test_reset_follows[saved|served]`. `reset_start/reset_end` equal `start/end` after the build and after a move. Red.
- Test: `…::TestZoomRetick::test_zoomed_in[saved|served]` and `::test_home_restores[saved|served]`. Run the attached zoom CustomJS through JsSession with `cb_obj` = P01's y range set to [20, 30]: ticks `_dash_natscale_ticks(20, 30, 5)`. Set it back to reset and the ticks are [10, 20, 30, 40]. Red: no callback.
- Test: `…::TestTheRefinishBudget::test_500k_rows_within_0_2_s`. A served scatter of 500k rows: `_dash_refinish_axes` takes ≤ 0.2 s (best of 3). Red: AttributeError (and 0.58 s at the base through `_dash_count_axes`, recorded by 21-02).
- Test: `…::TestThePlanCarriesNoUserText::test_code_is_constant_and_args_are_data[saved|served]`. Every filter callback's code is `_FILTER_JS`, and every zoom callback's is `_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS`. The plan's strings are only field names, letters, kinds and modes. A variable named `__proto__` and one holding `"</script>"` in its label build, and re-finish correctly. Red: no plan.

Guard tests (green at the base and after; listed apart in the failure file):
- Guard: `…::TestTheColourKeyKeepsItsTicker::test_zlabel_count_stays_basic`. The ColorBar's `#N` ticker is still `_dash_count_ticker`'s BasicTicker.
- Guard: `…::TestNoNote::test_no_axis_note[saved|served]`. Building P01, P03, P17 and Q02 raises no dash note (S06's helper).
- Guard: `…::TestPlotregionMarginIsStillIgnored::test_margin_zero_changes_nothing_yet[saved|served]`. `plotregion(margin(zero))` gives the same ranges as no option (S47's).

### `test/test_natscale_js.py` (new; node; red at the base: `_DASH_AXIS_FINISH_JS` is missing)

- Test: `…::TestJsNatscaleEqualsPython::test_the_fixture` (every `natscale_truth.json` range and n), `::test_random_ranges` (5,000 seeded), `::test_overflow` (the 72 overflow cases of `natscale_axes_truth.json`) and `::test_log_and_tc_rules`.
- Test: `…::TestJsPaddingEqualsPython::test_padded_ranges`. 2,000 seeded (lo, hi, f, kind, reverse), the degenerate date kinds included.
- Test: `…::TestJsFinishEqualsPython::test_random_moves`. 200 seeded moves over a built saved page: `dash_axis_finish` equals `_dash_finish_count_ticks(refinish=True)` run in Python on the same written data.

### `test/test_default_axes_chrome.py` (new; skipped without Chrome; red under DASH_STRICT if skipped)

- Test: `…::TestTheBrowserDrawsTwowaysAxes::test_saved_before_and_after_a_move`. P01's tick_coords are y [10,20,30,40] and x [2000,…,5000]. After `move_range_slider(0.3)`, y is [15,20,…,40] and x [2000,2500,…,4000]. There are no JS errors (under the shipped CSP). Red: 15(5)40 before the move.
- Test: `…::TestTheBrowserDrawsTwowaysAxes::test_a_zoom_keeps_labels`. Setting the y range to [20, 30] in the page gives ticks 20(2)30. Red.
- Test: `…::TestTheHundredPanelBudget::test_settles_within_the_budget`. 100 panels, one move: the shared case settles within `_BASE_SETTLE_S + 1.0` (the constant measured by 21-02, with a comment naming the base sha). Red: the re-finish is not there, so the y ticks are unchanged after the move (the assertion `_ys(after) != _ys(before)` on the ticks).

### Flips (in place; R9 `Flipped:` lines), from E10 F1-F33

- **F1-F3, F6, F10.** Assert a Range1d whose inner hull (with the figure's margin) is the data hull ∪ the natscale ticks.
- **F4.** The pad is f/(1−2f) in log space with `_dash_plot_margin`'s y.
- **F5.** Natscale on 20 gives [19, 21], reached, padded by f.
- **F7-F9, F12-F15, F20, F21, F29.** The renderer pools now hold every non-swatch layer (F9, `_dash_limit_ranges_to_primary` on a DataRange1d). Where the axis is a Range1d, assert the inner hull includes the fit or swatch exclusion directly.
- **F11.** Also inverts any margin.
- **F16.** One Range1d per shared axis.
- **F17.** `_dash_range_hull` of the shared Range1d after the move.
- **F18.** Range1d and FixedTicker models appear only in `axis_models`.
- **F19.** Docstrings rewritten.
- **F22.** The bound becomes "contains the layer and its ticks".
- **F23-F27.** The base or default ticker is a FixedTicker carrying the count tag and natscale ticks.
- **F28.** The other axis is a Range1d; the inverse uses `margin=` from `_dash_plot_margin`.
- **F30.** Re-derive the digest; the message says why.
- **F31.** The inverse uses the spec's `_dash_plot_margin`, and AE-05 expects a Range1d over the data hull.
- **F32.** `_s10_panels` records `curmin/curmax` for x and y, and `_s10_by` compares the shared hull with them.
- **F33.** Only if red: the new bounds measured, with the help's "<lo> to <hi> directives" sentence (as S15 left it) moved with it (R10).

### Guards appended to existing files

- `test/test_mode_parity.py` `CORPUS`, under `# WP-30 P1.3a: natscale ticks and twoway's margin`:
  - `_case("default axes take natscale and the margin", [plot_for("scatter", y="mpg", x="weight"), plot_for("lfit", y="mpg", x="weight")])`;
  - `_case("second axis default ticks", [plot_for("scatter", y="mpg", x="weight"), plot_for("scatter", y="price", x="weight", options={"yaxis": "2"})])`;
  - `_case("bar default base stays out", [plot_for("bar", y="mpg", x="weight")])`;
  - `_case("by() fits in the shared scale", [plot_for("scatter", y="price", x="mpg"), plot_for("lfit", y="price", x="mpg")], go={"by": "foreign"})`.

  `MOVE_CORPUS` gets `_move_case("default axes after a range move", _MOVES[1], [scatter, lfit])` and `_move_case("y2 after a dropdown move", _MOVES[0], [dual y])`. `ALLOWED` and `_MUST_WARN` are not edited (R8).
- `test/test_js_runner.py::TestRangesAndTickersCommit::test_start_end_reset_and_ticks_round_trip`. js_runner's extension: `stand_in` encodes `reset_start`, `reset_end` and `ticks` for Range1d and FixedTicker, and gives a Range1d stand-in a `setv(attrs)` method that assigns each attribute in turn, as BokehJS's `HasProps.setv` does (the finish JS writes ranges through it, TR-21.11); `RUNNER` returns `start`, `end`, `reset_start`, `reset_end` and `ticks` for those two types only; the commit writes them back.

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| `_dash_apply_axis_options` installs no default ticker | `TestDefaultTicksAreTwoways::test_probe[P01-saved]` |
| the default ticker's `n` read as 6 | `TestDefaultTicksAreTwoways::test_probe[P01-served]` (x 2000(500)…) |
| `_dash_tag_hull_roles` stamps nothing | `TestDefaultBasesStayOut::test_type[bar-saved]` |
| `_dash_limit_ranges_to_primary` keeps primaries | `TestEveryLayerIsInTheScale::test_probe[P03-saved]` (the DataRange1d fallback) and F9 |
| pad `f` instead of `f/(1-2f)` | `TestTheHelpers::test_padded_range_takes_a_margin` |
| `_dash_share_by_scales` skips f(G) | `TestByPanelsScaleTheirFits::test_q02[served]` (the margin assertion) |
| `_on_filter_change` skips `_dash_refinish_axes` | `TestAfterAFilterMove::test_range_move[served]` |
| `_FILTER_JS` drops the finish call | `TestAfterAFilterMove::test_range_move[saved]` |
| JS natscale ties broken the other way | `TestJsNatscaleEqualsPython::test_random_ranges` |
| the zoom JS returns home ticks always | `TestZoomRetick::test_zoomed_in[saved]` |
| `_dash_layer_extent` falls back to Python lists | `TestTheRefinishBudget::test_500k_rows_within_0_2_s` |
| `"_dash_refinish_axes"` dropped from the copy list | `TestTheServedAppCarriesEveryName` / any served move test (NameError) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Ticks, hull, margin, bases, roles | pytest `test_default_axes.py` | `default_axes_truth.json` (E5 literals in 21-01) | yes, `[saved\|served]` |
| After a move, reset, zoom | pytest `TestAfterAFilterMove`, `TestResetReturnsToTheCurrentExtent`, `TestZoomRetick` | the fixture's Q probes | saved (node), served, oracle |
| JS twin | pytest + node `test_natscale_js.py` | `natscale_truth.json`, `natscale_axes_truth.json` | JS against Python |
| Browser | `test_default_axes_chrome.py` (RangeProbe and a tick_coords reader in the test) | — | saved page; served doc via `file_html` for the initial draw |
| Budgets | `TestTheRefinishBudget`, `TestTheHundredPanelBudget`, `test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_hundred_panels_settle` | — | served; saved |
| Parity | `test_mode_parity.py` CORPUS and MOVE_CORPUS | — | yes |
| Scheme keys | `TestTheSchemeKeys`, `test_scheme_fidelity.py` (unedited), the regeneration diff | `scheme_truth.json` | n/a |
| twoway against dash | `test_wp30_truth.cscript` S21 block NS-01..NS-12 | live twoway | yes, plus moves |
| Registries | `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | — | served names |
| Help | `test_help_conformance.py`, `test_help_claims_*.py` | dash.sthlp | n/a |
| End to end | the truth block builds pages with `dash build` and served documents; `scripts/regen_dashboards.py` runs clean | — | yes |

**Acceptance criteria.**
- **AC-21.1** P01 is labelled y 10(10)40 and x 2000(1000)5000 in both modes. P06, P08, P09, P12, P15, P16, Q09 and Q12 match twoway. No default axis has a minor tick.
- **AC-21.2** The inner hulls of P01, P03, P05, P14, P20, Q02, B01, B06, Q10, Q11, P22 and L00-L07 equal twoway's curmin/curmax within 1e-6 × span, in both modes.
- **AC-21.3** `_dash_plot_margin` gives D1 (b)'s fractions (E6) with f(G) (E7). NS-08 and NS-09 pass.
- **AC-21.4** y2/x2 without labels are ticked 0(5000)15000 (P17, X2).
- **AC-21.5** After the Q01 and Q08 moves the axes equal twoway's under the same `if`, in both modes; after Q06 the served axes equal twoway's and the saved axes span the kept rows and the stale lfit as drawn (D-21e2). Saved, served and the oracle agree on the 4 × 3 move cases with no stale layer. Reset returns to the moved extent.
- **AC-21.6** A zoom to [20, 30] shows 20(2)30, and Reset restores 10(10)40, in both modes.
- **AC-21.7** The served re-finish takes ≤ 0.2 s at 500k rows. 100 saved panels settle within `_BASE_SETTLE_S + 1.0`.
- **AC-21.8** `WP30_ONLY=S21` prints NS-01..NS-12 PASS, then `ALL CHECKS PASSED`.
- **AC-21.9** F1-F33 are flipped with `Flipped:` lines, as 21-24 measured them; no test was deleted, and the collected count did not fall.
- **AC-21.10** One full run is green through the queue (E6 for the known flaky tests). The registries and both served-name guards pass. No note was added in either mode.

## Tasks

**Commit boundary.** Tasks 21-01 to 21-25 form the one commit of entry `P1.3a`, made by 21-25 on `wp30-s21` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s21` after one full run through the queue. The subject is `Tick and range default axes as twoway does, with its plot-region margin, after every filter move (WP-30 P1.3a)`. `$S` is `<scratch>/s21`, where `<scratch>` is the orchestrator's WP-30 scratch directory. Every command runs from `$WT`.
- The body:
  1. opens with `<scratch>/21-P1.3a-failure.txt`;
  2. then gives the measured defect (E3-E5) and the budgets measured at the base (21-02);
  3. then says what changed and where, in both modes (TR-21.1 to TR-21.14), and why the single-y digest moved (R10).
- It then carries one line each of:
  - `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-7 base sha> with <text>`;
  - `Flipped: <node> -- <old expectation> was wrong because dash now ticks and ranges default axes as twoway does, with its plot-region margin, over every drawn layer (WP-30 P1.3a, measured in twoway 03oct2026)`, one per line of `$S/21-flips.txt`;
  - `Fixture: test/fixtures/default_axes_truth.json (scripts/extract_default_axes_truth.do)` and `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
  - `BUGS.md: "Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ticks and plot-region margin, and fit lines are left out of the axis range" (closed)`.

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7): `grep -Eic 'claude|anthropic'` prints 0 on the message file before committing and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="21-01">
  <name>Write the failing default-axis regression tests</name>
  <files>test/test_default_axes.py, test/test_natscale_js.py, test/test_default_axes_chrome.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-7-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s21`; otherwise stop.
    Read `<scratch>/batch-7-impact.txt`. Confirm it records CRITICAL for _make_figure_body, _dash_padded_range, _dash_common_count_ticks, _dash_share_by_scales, FilterBuilder.build_dropdown and DashRenderer.render, HIGH for _generate_app_source and _glyph_layer_lines, and the grep-confirmed UNKNOWN for build_slider, build_range, _FILTER_JS and _dash_range_hull, each with its approval. If any is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it, and report every HIGH or CRITICAL result before editing.
    Create the three test files with exactly the classes and names of "TDD test stubs" (regression tests and guards), every expectation a literal from Evidence E5-E7. The fixture classes load `test/fixtures/default_axes_truth.json` lazily and are written by 21-04, not here.
    Run `python3 -m pytest test/test_default_axes.py test/test_natscale_js.py test/test_default_axes_chrome.py -q -n0 -p no:cacheprovider -rf > "$S/21-01.log" 2>&1`. Then write `<scratch>/21-P1.3a-failure.txt`: the base sha, each FAILED line with its first assertion text, and the passing guards under the heading "Guard tests (pass before and after)".
    Do not edit dash_render.py, and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/21-01.log"` prints at least 60; `grep -E 'TestTheColourKeyKeepsItsTicker|TestNoNote|TestPlotregionMarginIsStillIgnored' "$S/21-01.log" | grep -c PASSED` equals the guard count, or the guards are listed passing in the -rA summary; `test -s <scratch>/21-P1.3a-failure.txt`.]]></verify>
  <done>Every regression test existed with twoway's literal values and was shown failing on the unfixed tree, the guards passed, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="21-02">
  <name>Measure both re-finish budgets at the base</name>
  <files>none</files>
  <action><![CDATA[
    On the unmodified tree, time two things.
    First, HEAD's 100-panel settle: run `python3 -m pytest test/test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_hundred_panels_settle -q -n0 -s -p no:cacheprovider` three times and record the printed "hundred panels: shared … s" values.
    Second, the served reader's cost: in a scratch script, time `dr._dash_count_axes(fig, every_axis=True)` on a served figure of one 500k-row scatter (best of 3).
    Write both measurements, the median settle as `_BASE_SETTLE_S`, the machine (`sysctl -n machdep.cpu.brand_string`) and the base sha to `$S/budgets.txt`. Nothing in the repository changes.
  ]]></action>
  <verify><![CDATA[`grep -E '^_BASE_SETTLE_S = [0-9.]+$' "$S/budgets.txt"` matches; `grep -c 'count_axes 500k' "$S/budgets.txt"` prints 1.]]></verify>
  <done>The base's 100-panel settle time and the reader's 500k-row cost were measured and recorded for the budget tests and the commit body.</done>
</task>

<task type="auto" id="21-03">
  <name>Extract the default-axis truth from Stata</name>
  <files>scripts/extract_default_axes_truth.do, test/fixtures/default_axes_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_default_axes_truth.do exactly as "Stata truth" specifies:
    - TR-02.9's root stanza, then `adopath ++` and `global dash_nobrowser 1`;
    - the `_ns_rec` recorder, and every probe key with its command;
    - SVG exports into the run directory;
    - the D12 stamp through `shell git -C` into a tempfile;
    - one trailing python block that uses scripts/svg_truth.py's svg_document and svg_axis_extent, never calls Stata, never uses shell=True, and spells a backtick \x60.
    Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/truth" "$WT/scripts/extract_default_axes_truth.do"` and read `$S/truth/extract_default_axes_truth.log`.
    Check the fixture against Evidence E5-E7: P01 y cur [10,41] with major 10/10/40; Q01 y cur [14,41]; P17 y2 major 0/5000/15000; BY6 gmetric 0.8; P01 margin_rel 0.0220 ± 0.0005. A difference is investigated and reported, never patched by hand (R7).
    Run `git add -f test/fixtures/default_axes_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/default_axes_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));p=d['probes'];assert p['P01']['y']['major']==[10,10,40];assert abs(p['BY6']['gmetric']-0.8)<1e-9;assert len(d['schemes'])==26;print(len(p))"` prints the probe count; `git ls-files test/fixtures/default_axes_truth.json` prints the path; the log ends with the python block's line `default_axes_truth: wrote <N> probes` and holds no uncaptured `r(` error.]]></verify>
  <done>twoway's ticks, scales, by() multipliers and SVG margins for every probe were recorded in a stamped fixture staged with git add -f.</done>
</task>

<task type="auto" id="21-04">
  <name>Add fixture-driven tests and record red lines</name>
  <files>test/test_default_axes.py</files>
  <action><![CDATA[
    Add these fixture-driven classes to test/test_default_axes.py:
    - `TestStataTruth::test_probe[<every probe id>-saved|served]`: ticks equal major; inner hull equals cur within 1e-6 × span;
    - `TestStataTruth::test_scheme[<26 names>-saved|served]`;
    - `TestStataTruth::test_margin[<svg ids>]`: `margin_rel` = r × f(G) within 0.0005, and the frame-fraction difference ≤ 0.008;
    - `TestStataTruth::test_the_meta_stamp`, a guard.
    Run the file on the unmodified renderer, `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -rf > "$S/21-04.log" 2>&1`. Append the new FAILED lines, and the meta-stamp guard under the guard heading, to `<scratch>/21-P1.3a-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/21-04.log"` is larger than the count for test_default_axes.py in `$S/21-01.log`; `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k meta_stamp` passes.]]></verify>
  <done>The fixture-driven tests failed on the unfixed renderer, the stamp guard passed, and both were added to the saved failure text.</done>
</task>

<task type="auto" id="21-05">
  <name>Regenerate schemes with numticks and margin keys</name>
  <files>scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json, dash-*.scheme (the 26 generated files)</files>
  <action><![CDATA[
    In scripts/extract_scheme_truth.py's `extract`, resolve `numticks_g horizontal_major`, `numticks_g vertical_major` and `margin twoway` through getsrc with provenance (TR-21.1, D-21a). Resolve the marginstyle file's four sides to gsize relative values, assert they are equal, and record `margin_twoway` and `margin_twoway_rs`. Add the three directives to `expected_directives` in the existing scalar form.
    Copy scheme_truth.json to `$S/scheme_truth.before.json`, then run `python3 scripts/extract_scheme_truth.py` from $WT. Compare every probe's pre-existing keys before and after, outside `_meta`: only the new keys and provenance lines may differ, and a difference elsewhere stops the task and is reported (R7).
    Run `git add -f test/fixtures/scheme_truth.json`. Generated files are never edited by hand.
  ]]></action>
  <verify><![CDATA[`grep -c '^numticks_g horizontal_major *5$' dash-*.scheme | grep -c ':1$'` prints 26; `grep -h '^margin twoway' dash-*.scheme | sort | uniq -c` shows 25 medsmall and 1 vsmall; a second run of the extractor changes nothing (`git status --porcelain dash-*.scheme test/fixtures/scheme_truth.json` is unchanged by it); `python3 -m pytest test/test_scheme_fidelity.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every shipped scheme file and scheme_truth.json carried twoway's tick count and plot-region margin, regenerated by the extractor with no other change.</done>
</task>

<task type="auto" id="21-06">
  <name>Add margin and default ticker helpers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add these in dash_render.py:
    - `_DASH_DEFAULT_TAG`, `_DASH_MARGIN_RS` and `_DASH_BY_GMETRIC`, beside `_DASH_COUNT_TAG` (about 22085);
    - `_dash_default_ticker(n)`, after `_dash_count_ticker` (TR-21.3);
    - `_dash_plot_margin(scheme, graph_opts, panels=1)` (TR-21.4).
    In `SchemeParser._init_properties` (after the graphsize lines about 7015-7016), add `numticks_x`, `numticks_y` and `plot_margin_rs` (TR-21.1), and add the three `_FALLBACK_PROPS` entries.
    Do not change `_dash_count_ticker`. Run `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "TestTheHelpers and (default_ticker or plot_margin or by_factor or hostile) or TestTheSchemeKeys"`.
  ]]></action>
  <verify><![CDATA[The -k selection above passes; `python3 -m pytest test/test_natscale.py -q -n0 -p no:cacheprovider` passes (the colour-key and #N paths are unchanged).]]></verify>
  <done>The scheme's tick count and margin were readable in both modes, and the default ticker and margin helpers existed and were tested.</done>
</task>

<task type="auto" id="21-07">
  <name>Pad by the margin and tag roles</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log: `_dash_padded_range` is CRITICAL (10 impacted). Then:
    - add `margin=None` to `_dash_padded_range` and `margin=None` to `_dash_range_hull`, per TR-21.8 (the `_dash_margin_f` stamp; reset_start/reset_end; legacy 5% when None);
    - add `_dash_layer_extent(renderers, range_attr, name, kind=None)` and `_dash_tag_hull_roles(renderers, ptype, options)` after `_dash_secondary_values` (TR-21.7), as module-level functions with no nested defs;
    - make `_dash_secondary_values` skip each renderer's `_dash_auto_base` properties.
    `_dash_range_hull` stays TEST_ONLY: no run-time code calls it. Run the TestTheHelpers padding, inverse, extent and roles tests, and `python3 -m pytest test/test_axis_extents.py -q -n0 -p no:cacheprovider -k TestTheHelpers`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "padded_range or range_hull_inverts or layer_extent or hull_roles"` passes; `grep -n "_dash_range_hull(" dash_render.py | grep -v "^.*def _dash_range_hull" | grep -vc '"_dash_range_hull"'` prints 0.]]></verify>
  <done>Ranges could be padded by twoway's margin and inverted for any margin, a vectorised reader existed, and each layer could be tagged with its hull roles.</done>
</task>

<task type="auto" id="21-08">
  <name>Rework the count and hull chain</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-21.8 to `_dash_count_axes` (23345), `_dash_place_count_ticks` (23419), `_dash_axis_hull` (23565), `_dash_hull_ranges` (23674) and `_dash_finish_count_ticks` (23732):
    - `_dash_count_axes`: use the `_dash_layer_extent` reader, remove the x-pool special case and its stale comment (D-21i), and add the `default`/`hold` entries;
    - `_dash_place_count_ticks`: write ticks in place, keep the tags on a new FixedTicker, and remove the pinning block (23452-23486);
    - `_dash_axis_hull`: always return a hull, add the y2/x2 `range()` values, and vectorise the bar widths;
    - `_dash_hull_ranges`: every range name, margin and reverse per name, in-place updates, `made` reuse, and hold;
    - `_dash_finish_count_ticks`: `refinish=False`.
    Each changed docstring states the new rule and cites WP-30 P1.3a. Run `python3 -m pytest test/test_default_axes.py test/test_natscale.py test/test_natscale_axes.py -q -n0 -p no:cacheprovider`, and record the reds that remain for 21-09 to 21-14.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_natscale.py test/test_natscale_axes.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "TestCountAxesHaveTheMargin or TestTheExtentIsTwowaysHullAndMargin"` passes in the saved mode (served may still fail until 21-14).]]></verify>
  <done>Every continuous axis's ticks, hull and padded Range1d came from one in-place chain that a re-finish could run again.</done>
</task>

<task type="auto" id="21-09">
  <name>Share by() ranges over every layer</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log before each edit: `_dash_common_count_ticks` is CRITICAL (4) and `_dash_share_by_scales` is CRITICAL (8). Then:
    - `_dash_common_count_ticks` covers every range name and updates the shared object in place through `made`;
    - `_dash_share_by_scales` recomputes `_dash_margin` with `panels=len(figs)`, re-pads rescaled letters, and removes both the DataRange1d-sharing block and the y2/x2 block (TR-21.8);
    - `_dash_limit_ranges_to_primary` (23913) keeps every non-swatch layer.
    `_dash_keep_primary_ranges` is left in form. Run `python3 -m pytest test/test_by_scales.py test/test_default_axes.py -q -n0 -p no:cacheprovider -k "by or Q02 or EveryLayer"`, and list the by_scales reds for 21-16.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "TestByPanelsScaleTheirFits and saved"` passes; the remaining red nodes in test_by_scales.py are exactly F12-F18 of Evidence E10 (`$S/21-09.log`).]]></verify>
  <done>A by() graph's shared axes were one Range1d over every panel's layers, fits included, with twoway's by() margin.</done>
</task>

<task type="auto" id="21-10">
  <name>Install default tickers on every axis</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-21.6:
    - `_dash_apply_axis_options` (22997) installs `_dash_default_ticker` on continuous primary axes in default mode, of a numeric, log or %tc kind, before `_dash_apply_tick_option`;
    - `_dash_finish_secondary_axes` (23172) installs it on y2/x2 without a label rule, records `_dash_scale_values2`/`_dash_scale_reverse2`, and pads with the figure's margin.
    Both read `fig._dash_numticks` and fall back to 5. `%td`-`%ty` axes keep their DatetimeTicker. Run the TestDefaultTicksAreTwoways, TestNoMinorTicks and TestSecondAxisDefaultTicks saved cases.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "(TestDefaultTicksAreTwoways or TestNoMinorTicks or TestSecondAxisDefaultTicks) and saved"` passes once 21-11 stamps the figure; until then the run is recorded in `$S/21-10.log`.]]></verify>
  <done>Every default numeric, log and %tc axis and every unlabelled second axis carried the scheme's natscale placeholder.</done>
</task>

<task type="auto" id="21-11">
  <name>Stamp the saved figure body</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log: `_make_figure_body` is CRITICAL (4). In `_make_figure_body`, right after `fig = bokeh_figure(**fig_kwargs)` (30309), add the TR-21.5 stamps with `self.scheme` and `graph_opts`. After `_layer_renderers = list(fig.renderers[_r_before:])` (30611), add `_dash_tag_hull_roles(_layer_renderers, ptype, popts)`.
    Nothing else in the method changes: the finisher calls at 30660-30679 keep their order. Run every saved-mode case of test_default_axes.py except the move, zoom, plan and budget classes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "saved and not (AfterA or Zoom or Plan or Budget or Reset)"` passes.]]></verify>
  <done>Saved figures carried twoway's margin, the scheme's tick counts and each layer's hull roles, and drew twoway's default axes.</done>
</task>

<task type="auto" id="21-12">
  <name>Add the Python re-finish and plan</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log: `build_dropdown` (CRITICAL, 6) and `DashRenderer.render` (CRITICAL, 13) are about to be edited.
    Add `_dash_refinish_axes(figures, facet_map)` (TR-21.9) and `_dash_axis_plan(figures, facet_map, zoom=True)` (TR-21.10) after `_dash_tag_hull_roles`.
    Add the two placeholder args to `build_dropdown`, `build_slider` and `build_range` (TR-21.12). Add step "5b" to `DashRenderer.render()` right after the `_build_filter_widgets` call (32707). Do not edit `_build_filter_widgets` (R12, D-21f).
    Run TestTheHelpers' refinish and plan tests and TestResetReturnsToTheCurrentExtent's saved case.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "refinish_axes_is_idempotent or axis_plan_shape or (TestResetReturnsToTheCurrentExtent and saved)"` passes; `python3 -m pytest test/test_filters.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>A Python re-finish and a data-only plan of every planned axis existed, and every saved filter callback carried the plan and its models.</done>
</task>

<task type="auto" id="21-13">
  <name>Port the finisher and zoom to JS</name>
  <files>dash_render.py, test/js_runner.py, test/test_js_runner.py</files>
  <action><![CDATA[
    Add `_DASH_AXIS_FINISH_JS` and `_DASH_AXIS_ZOOM_JS` after `_DASH_TICK_EVERY_JS` (22878), per TR-21.11 and D-21d, with the `__DASH_*__` constant tokens replaced at import by `repr()`. Directly after them, extend `_FILTER_JS` by the one module-level statement of TR-21.11 (`_FILTER_JS = _FILTER_JS + _DASH_AXIS_FINISH_JS + <the guarded call>`); do not edit `_FILTER_JS`'s literal at 18562-19352, which is defined before the constants the finish JS needs. Write each range with one `setv` and the `_dash_finishing` guard (TR-21.11).
    Extend test/js_runner.py's `stand_in` (with the Range1d `setv` method), `RUNNER` and commit for Range1d and FixedTicker only, and add `TestRangesAndTickersCommit` to test/test_js_runner.py.
    Run `python3 -m pytest test/test_natscale_js.py test/test_js_runner.py -q -n0 -p no:cacheprovider`, then the saved move, zoom and plan classes of test_default_axes.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_natscale_js.py test/test_js_runner.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "saved and (AfterA or Zoom or Plan or Reset)"` passes; `python3 -m pytest test/test_help_claims_4.py test/test_scheme_review_fixes.py test/test_security_surface.py test/test_saved_stale_cue.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The saved page re-finished its axes at the end of every filter callback and re-ticked on zoom, through constant JavaScript equal to the Python finisher.</done>
</task>

<task type="auto" id="21-14">
  <name>Wire the served template and copy lists</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log: `_generate_app_source` is HIGH (5) and `_glyph_layer_lines` is HIGH (4). In `_generate_app_source`, add:
    - the TR-21.5 stamps in `_dash_figure_for` after `"        fig = bokeh_figure(**_fig_kw)",` (35192);
    - the TR-21.7 call before the `_dash_note_empty_layer(gname, pi + 1, ptype, len(g_df),` line (35405);
    - `_dash_axis_plan(figures, _facet_map, zoom=True)` after the graph loop (after 35654);
    - the two `_make_filter_cb` keyword parameters, passed at the wiring call (36077-36084);
    - `_dash_refinish_axes(_axis_figs, _axis_fmap)` before "# 4. Recompute filter-mode KPIs" (36049).
    Add the R2 copy-list entries of TR-21.14 at their two anchors (32943, 33251). Run every served case of test_default_axes.py and both served-name guards.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider` passes except TestTheRefinishBudget if 21-15 is pending; `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The served app drew twoway's default axes, re-finished them after every filter move and re-ticked on zoom, with every new name on its copy list.</done>
</task>

<task type="auto" id="21-15">
  <name>Meet the served and saved budgets</name>
  <files>test/test_default_axes.py, test/test_default_axes_chrome.py</files>
  <action><![CDATA[
    Set `_BASE_SETTLE_S` in test/test_default_axes_chrome.py to the value in `$S/budgets.txt`, with a comment naming the base sha and the machine.
    Run `python3 -m pytest test/test_default_axes.py::TestTheRefinishBudget test/test_default_axes_chrome.py -q -n0 -s -p no:cacheprovider` and `python3 -m pytest test/test_by_scales_chrome.py -q -n0 -s -p no:cacheprovider`. If a budget fails, profile the reader (`_dash_layer_extent`, the bar widths) or the JS reader; do not loosen the bound.
    Record the measured seconds in `$S/budgets.txt` under "after".
  ]]></action>
  <verify><![CDATA[Both pytest commands pass with no skip (`grep -c SKIP` on their output prints 0, with Chrome present); `$S/budgets.txt` holds an "after" line for each budget.]]></verify>
  <done>The served re-finish stayed within 0.2 s per figure at 500k rows and 100 saved panels settled within a second of the base's time.</done>
</task>

<task type="auto" id="21-16">
  <name>Flip extent and by-scale pins</name>
  <files>test/test_axis_extents.py, test/test_by_scales.py, test/test_by_scales_chrome.py</files>
  <action><![CDATA[
    Flip F1-F19 of Evidence E10 in place, each to the new expectation in "Flips", with a one-line comment `# WP-30 P1.3a: <old> was wrong because <why>`. Rewrite `_emulated_hull`'s and the chrome module's docstrings. Never delete a test.
    Append each flipped node to `$S/21-flips.txt` as `<node> | <old expectation> | <why>`. Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_extents.py test/test_by_scales.py test/test_by_scales_chrome.py -q -n0 -p no:cacheprovider` passes; `git diff --stat -- test/test_axis_extents.py test/test_by_scales.py` shows no net loss of `def test_` lines (`git diff -U0 ... | grep -c '^-    def test_'` prints 0).]]></verify>
  <done>Every extent and by() pin of today's DataRange1d model asserted twoway's hull and margin instead, with its reason recorded.</done>
</task>

<task type="auto" id="21-17">
  <name>Flip ticker pins in the help claims</name>
  <files>test/test_help_claims_7.py, test/test_help_claims_8.py, test/test_help_claims_2.py</files>
  <action><![CDATA[
    Flip F20-F26 in place, as in "Flips". F25 is flipped here (register P1.2.7: P1.3 owns the minor-tick flips; S15 only colours the minor ticks Bokeh draws until now). Append each to `$S/21-flips.txt`. Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_7.py test/test_help_claims_8.py test/test_help_claims_2.py -q -n0 -p no:cacheprovider` passes (F33 excepted until 21-24 decides it).]]></verify>
  <done>The help-claim tests asserted the natscale FixedTicker and the layer-inclusive second axes.</done>
</task>

<task type="auto" id="21-18">
  <name>Flip option and output pins</name>
  <files>test/test_axis_options.py, test/test_html_output.py, test/test_function_audit.py</files>
  <action><![CDATA[
    Flip F27-F29 in place. F28's inverse passes `margin=dr._dash_plot_margin(dr.SchemeParser…, go)[letter]` for the page's scheme. Append each to `$S/21-flips.txt`. Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_options.py test/test_html_output.py test/test_function_audit.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The option, page-output and audit tests asserted the new tickers, ranges and inclusive pools.</done>
</task>

<task type="auto" id="21-19">
  <name>Flip the truth blocks and digest</name>
  <files>test/test_gaps2_truth.cscript, test/test_wp29_truth.cscript, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Flip F31 (the AE-01..AE-05 inverse and AE-05's Range1d) and F32 (`_s10_panels` records x/y curmin/curmax; `_s10_by` compares the shared and per-panel hulls with them), keeping every case id, and edit only those cases (R1).
    Re-derive F30's `_SINGLE_Y_BASELINE_SHA256` with `normalise_bokeh_html(_single_y_html())` and write it with the comment `# <old> -> <new>: P1.3a default axes take natscale ticks and twoway's margin`.
    Run each cscript through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_gaps2_truth.cscript > "$S/run_test_gaps2_truth.do"` and `GAPS2_ONLY=S18 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_gaps2_truth.do"`, then the same with `WP29_ONLY=S10` for test_wp29_truth.cscript.
  ]]></action>
  <verify><![CDATA[`grep -cE 'AE-0[1-5] PASS' "$S/run_test_gaps2_truth.log"` prints 5 and the log holds no FAIL; `grep -cE 'BSC-0[1-7] PASS' "$S/run_test_wp29_truth.log"` prints at least 7 and no FAIL; `python3 -m pytest test/test_varlist_expansion.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The GAPS2 and WP-29 truth blocks compared dash's new hull with twoway's scale, and the single-y digest was re-derived with its reason.</done>
</task>

<task type="auto" id="21-20">
  <name>Add parity cases and map entries</name>
  <files>test/test_mode_parity.py, test/function_test_map.py</files>
  <action><![CDATA[
    Append the four CORPUS and two MOVE_CORPUS cases of "Guards appended" under `# WP-30 P1.3a: natscale ticks and twoway's margin`. Do not edit `ALLOWED` or `_MUST_WARN` (R8).
    Add the six TR-21.15 keys under `# WP-30 S21 (P1.3a): …` in `FUNCTIONS`, in alphabetical order, each naming its TestTheHelpers node.
    Run `python3 -m pytest test/test_mode_parity.py test/test_function_test_map.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[Both files pass; `grep -c "WP-30 P1.3a" test/test_mode_parity.py` prints 1.]]></verify>
  <done>Both modes were shown to draw the new axes alike in the parity corpus, and every new function named its test in the map.</done>
</task>

<task type="auto" id="21-21">
  <name>Fill the S21 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Write the `_s21_*` python helpers directly above `* ==== S21 P1.3a: … ====`. Write cases NS-01..NS-12 between S21's own start and end lines, through `_w30_expect`/`_w30_done`, writing only under `` `w30_work' `` and erasing it before the end line (S01 TR-01.10 item 4).
    Run `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"` and `WP30_ONLY=S21 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`.
  ]]></action>
  <verify><![CDATA[`grep -cE '^NS-(0[1-9]|1[0-2]) PASS' "$S/run_test_wp30_truth.log"` prints 12; the log ends `ALL CHECKS PASSED` and holds no FAIL or SKIP; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>Live twoway and dash's saved page and served app agreed on every default axis, margin and after-move case of the S21 block.</done>
</task>

<task type="auto" id="21-22">
  <name>Run the browser checks</name>
  <files>test/test_default_axes_chrome.py</files>
  <action><![CDATA[
    Run `DASH_STRICT=1 python3 -m pytest test/test_default_axes_chrome.py test/test_by_scales_chrome.py -q -n0 -p no:cacheprovider`. The saved page must show twoway's ticks before and after a move and on zoom, with `js_errors() == []` under the shipped CSP.
    If a check fails because a range or ticker change does not repaint, fix the write order in `_DASH_AXIS_FINISH_JS` (TR-21.11). Use no BokehJS view internals in shipped code; the test's tick reader may read them.
  ]]></action>
  <verify><![CDATA[The command passes with 0 skipped.]]></verify>
  <done>A real browser drew twoway's ticks on the saved page before and after a filter move and on zoom, with no script error.</done>
</task>

<task type="auto" id="21-23">
  <name>Rewrite the help on default axes</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In "Axis labels" (about :2843-2876), rewrite the extent sentence ending "…margin of 5% of that span at each end … and holds across filter moves." Say instead:
    - the axis spans the hull of every drawn layer (fits, bands, scatteri and function included; reference lines, text, marker labels and default bar/area/spike/dropline bases not), its ticks, positions and `range()` values;
    - plus twoway's plot-region margin (2.2% of the graph's smaller side, economist 0.6%, a by() panel's scaled as twoway scales it, placed within about 0.8% of the figure's width of twoway's);
    - after a filter move a default or `#N` axis is ticked and spanned again over the rows kept, a second axis included, while an axis with explicit positions keeps them and spans its data again;
    - `%td`-`%ty` `#N` ticks, `xtick(#N)`/`ytick(#N)` marks and `minmax` keep their places.
    Add one paragraph after the `#N` paragraph: with no `xlabel()`/`ylabel()` rule, numeric, log and `%tc` axes, and a second axis with no `ylabel2()`/`xlabel2()`, are ticked as `#5` (the scheme's tick count) with no minor ticks, and a zoom ticks the visible range by the same rule. Rewrite "and the axis reaches its outermost tick" to "and the axis spans its outermost ticks", and say the by() common scale includes fits.
    Then, per D-21h, make two one-sentence edits:
    - in the by() paragraph (:2084-2086), "Panning or zooming one panel moves the others; a filter move spans the axes again over the rows kept";
    - in the toolbar's Reset row (:1203-1204), "return to the extent the last filter move gave the axes".
    Then run `python3 scripts/regen_dashboards.py` (its pages are ignored by .gitignore; nothing is staged).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_7.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider` passes; `grep -c "margin of 5% of that span" dash.sthlp` prints 0; `python3 scripts/regen_dashboards.py` exits 0; `git status --porcelain '*.html'` prints nothing.]]></verify>
  <done>The help described twoway's default ticks, extent, margin, after-move and zoom behaviour as dash now draws them, and the demo pages regenerated cleanly.</done>
</task>

<task type="auto" id="21-24">
  <name>Re-measure reds, mutations and digest</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file named in Evidence E10, plus test_natscale.py, test_natscale_axes.py, test_scheme_fidelity.py, test_mode_parity.py, test_served_filter_move.py, test_filters.py and test_dates.py. Write `$S/21-red-at-fix.txt`: the nodes that fail when each flipped file's base version (`git -C $WT show $(cat <scratch>/batch-7-base.txt):test/<file> > $S/base/test/<file>`, run with `PYTHONPATH=$WT:$WT/test`) runs against the fixed renderer. That list must equal `$S/21-flips.txt`; a node red there but not listed is flipped in its file's task (21-16 to 21-19), with F33 decided here.
    Then apply each mutation of the mutation table to a copy of dash_render.py in `$S/mut/` (never to $WT's file, never through a stash), run the named test with `PYTHONPATH=$S/mut:$WT/test`, and record `RED as expected` or not, per mutation, in `$S/21-mutations.txt`.
  ]]></action>
  <verify><![CDATA[`diff <(cut -d'|' -f1 "$S/21-flips.txt" | sort) <(sort "$S/21-red-at-fix.txt")` prints nothing; `grep -c 'RED as expected' "$S/21-mutations.txt"` prints 12.]]></verify>
  <done>The flipped tests were exactly those the fix turned red, and every mutation of a new rule turned its named test red.</done>
</task>

<task type="auto" id="21-25">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    In BUGS.md, change the entry titled "Default numeric axes use Bokeh's ticker and 10 percent padding, not twoway's natscale ticks and plot-region margin, and fit lines are left out of the axis range" to `- [x]`, and replace its Resolution line in place with `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.3a). …`, saying:
    - natscale ticks for N = the scheme's numticks on default numeric, log and %tc axes and unlabelled y2/x2 (`_dash_default_ticker`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`);
    - the hull of every drawn layer plus twoway's margin r x min(W,H) as a build-time frame fraction (`_dash_plot_margin`, `_dash_padded_range`, `_dash_hull_ranges`);
    - by() panels on one Range1d (`_dash_share_by_scales`);
    - a re-finish after every move in both modes (`_dash_refinish_axes`; `_DASH_AXIS_FINISH_JS` at the end of `_FILTER_JS`) and natscale on zoom.
    It then gives "Pinned by" with the main nodes, `test/test_wp30_truth.cscript NS-01..NS-12` and both fixtures, and ends: "Residual, deferred (WP-30): %td-%ty default ticks are P1.3b (S44); default bases P1.17b (S27); raw-SIF date layers P1.23a (S35); xtick(#N), minmax and an axis with no value at build hold after a move."
    Delete `"P1.3a": …` from `WP30_OPEN` in test/test_tracking_documents.py.
    Replace `<!-- WP-30 P1.3a -->` in CHANGELOG.md, in place, with the Results line of "Notes", ending `(WP-30, P1.3a)`.
    Then:
    - run `python3 -m pytest test/test_tracking_documents.py -q -n0`;
    - run `git -C $WT merge --no-edit main` and expect `Already up to date.`;
    - run `<scratch>/full_suite_queue.sh $WT <scratch>/21-full-1.log` in the background, wait for its `exit=` line, and require 0 failed (E6 for the known flaky tests);
    - `git add` the section's files (`git add -f` for the two fixtures);
    - check scope (G6: `git -C $WT diff --cached --name-only` holds only this section's files) and the message file (G7);
    - check that `git -C $WT branch --show-current` prints `wp30-s21`, and commit once.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/21-full-1.log` is `exit=0` with 0 failed above it; `grep -c '<!-- WP-30 P1.3a -->' CHANGELOG.md` prints 0; `cd test && python3 -c "import test_tracking_documents as t; print('P1.3a' in t.WP30_OPEN, 'P1.3a' in t.WP30_LISTS)"` prints `False True` (`WP30_LISTS`/`WP30_SECTION` keep the key for good, TR-01.2); `git -C $WT log -1 --format=%s` ends `(WP-30 P1.3a)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C $WT show --name-only --format= HEAD | grep -cE '^(CLAUDE.md|\.gitignore|AGENTS.md|\.ultraplan/)|\.html$'` prints 0.]]></verify>
  <done>Entry P1.3a was closed in place with its tests named, its key and marker were replaced, and one green commit (WP-30 P1.3a) held the whole fix on wp30-s21.</done>
</task>

## Section completion criteria

- In the saved page and the served app, before and after every filter move:
  - every default numeric, log and `%tc` axis, and every y2/x2 without its own label rule, shows twoway's natscale ticks for the scheme's count, with no minor ticks;
  - every continuous axis spans the hull of every drawn layer, its ticks and positions, plus twoway's margin;
  - by() panels share one Range1d over the union hull.
- After a move, default and `#N` axes are re-ticked and re-ranged over the kept rows, explicit axes re-hull their data part, the D-21e forms hold, Reset returns to the new extent, and a zoom re-ticks. The saved page and the served app agree wherever both draw the same layers, and both equal twoway's drawing under the same `if` (NS-10); a layer the saved page leaves unfiltered stays in its saved hull as drawn (D-21e2).
- The budgets of BR-21.7 pass. `test_wp30_truth.cscript` prints NS-01..NS-12 PASS under `WP30_ONLY=S21`. The GAPS2 S18 and WP-29 S10 blocks pass, as flipped.
- `default_axes_truth.json` and the regenerated `scheme_truth.json` exist with their stamps and are committed with `git add -f`. The 26 scheme files carry the three keys.
- There is one green commit `(WP-30 P1.3a)` on `wp30-s21`, with its failure text and its `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines, and no AI reference.
- The BUGS.md entry is closed in place, `WP30_OPEN["P1.3a"]` is deleted, and the marker is replaced. No other entry, key, marker, copy-list anchor, runner block, hygiene pin or partner function is touched.

## Notes

**Traps for the executor.**
- **Order of the build calls.** `_dash_finish_secondary_axes` runs before `_dash_finish_count_ticks` in both modes (30660/30679, 35417/35430). The y2/x2 extent must therefore be finalised in `_dash_hull_ranges`, not in `_dash_finish_secondary_axes`, or the y2 ticks are left out of its hull.
- **In place, not new.** A re-finish must update the existing Range1d and FixedTicker objects. The zoom callback, the plan's `models` and by()'s shared object all hold references, and a new object in served mode would orphan them. Only the first build replaces DataRange1d.
- **The tags must survive.** `_dash_place_count_ticks` used to replace the `#N` BasicTicker with an untagged FixedTicker. Without the tags, a re-finish no longer sees the axis as counted.
- **`_dash_range_hull` is TEST_ONLY** (function_test_map.py TEST_ONLY). Any run-time call fails `test_function_test_map.py`. A page read back from JSON has no `_dash_margin_f`, so page-level tests pass `margin=`.
- **js_runner** commits only what its RUNNER returns. Extend both, for Range1d and FixedTicker only, so the existing slider stand-ins (which carry `start`/`end`) are never written back.
- **JS parity** depends on the same candidate order (z ascending, m in 1, 2, 5, j0 and j1 ascending), the same `1e-12` tie rule and `Number(v.toPrecision(15))`. Do not "simplify" the port.
- **Served notes.** `_dash_tag_hull_roles` and the finisher emit nothing (M6). A `warnings.warn` added by mistake would turn `test_mode_parity.py`'s note checks red.
- **python_exec.** Run Stata only through the slot. If many sessions drop `python_exec` from `~/.stata19/console/stata19.rc`, restore the maintainer's value (E12) and re-run; never re-run with a different interpreter.

**Merge rules cited** (index "Merge rules within a batch").
- R1: the S21 stub only; the in-place AE/BSC flips edit only their cases.
- R2: the two copy-list anchors, with `_dash_refinish_axes` kept last for S27, and the map anchor.
- R3: "Axis labels", plus D-21h's two sentences (resolved: allowed).
- R4: one marker, in Results that change. R5: own entry and key only.
- R7 and A152: the regeneration is never hand-patched and lands last in batch 7.
- R8: CORPUS and MOVE_CORPUS appended. R9: the flips. R10: the single-y digest; F33 only if moved.
- R11: S21 is batch 7's finisher editor. R12: `_make_figure_body` and `_generate_app_source`, with no `_build_sources_and_figures` or `_build_filter_widgets` edit.

**Commit-body line forms** are in "Commit boundary". The body also quotes `$S/budgets.txt`'s before and after values (A9).

**CHANGELOG line** (replaces `<!-- WP-30 P1.3a -->` in Results that change):
- `dash scatter mpg weight`, and every axis with no `xlabel()`/`ylabel()` rule, was ticked by Bokeh: y 15(5)40 and x 2000(500)4500 with minor ticks, over the data padded 5% a side (y 10.55 to 42.45).
- It is now ticked as twoway ticks it: y 10(10)40 and x 2000(1000)5000, with no minor ticks, over the hull of every drawn layer and its ticks (y 10 to 41, x 1760 to 5000), plus twoway's plot-region margin of 2.2% of the graph's smaller side (economist 0.6%, a by() panel's scaled by twoway's by() factor).
- A fit, CI band, `scatteri` point or `function` curve now widens the axis instead of being clipped, by() panels included: `(scatter price mpg) (lfit price mpg)` runs y from 0 to 15,906, not 2,660 to 16,537.
- `ylabel(#5)` keeps a margin past its outermost tick. A second axis without `ylabel2()` is ticked 0(5000)15000, not 4000(2000)16000.
- After every filter move, default and `#N` axes are re-ticked and re-ranged over the rows kept, in the saved page and the served app, second axes included (on the saved page a fit or histogram it does not recompute, marked "(unfiltered)", stays inside the range as drawn). An axis with explicit positions spans its data again.
- A zoom ticks the visible range by the same rule, and Reset returns to the last filter move's extent (WP-30, P1.3a).

**Open questions for the maintainer.**
1. **D-21h** is resolved in the section (review pass): S21 edits the two sentences; index.md's R3 table is to name them.
2. **Ratification items 1 and 3** (A6 margin tolerance; A9 budgets) are pending. This file is written on them as stated.

**Notes for the closeout (S58; A145).**
- **GAPS2.md B25.** B25 is carried by P1.2a (S15), P1.3a (S21) and P1.3b (S44). The Tracked line is written only when S44 closes, as `Closed in WP-30, BUGS.md "<P1.3b title>", commit <S44 sha>`. Its text should name S21's commit for B25-a on numeric, log and %tc axes and y2/x2, and for B25-b. S21's Resolution gains `(WP-30, GAPS2-B25)` only then.
- **DROPIN-REMAINING.md P1.3** row: "Part a closed by WP-30 S21 (`<sha>`): natscale ticks with the scheme's count on default numeric, log and %tc axes and unlabelled second axes; every layer in the hull; twoway's plot-region margin; by() panels on one range including fits (closes the WP-29 S10 c15 note); re-finished after every filter move in both modes; natscale on zoom."
- **New P2 rows to file:**
  1. `xtick(#N)`/`ytick(#N)` marks and `xlabel(minmax)` positions are placed at build and held after a filter move, in both modes (twoway re-places them under `if`);
  2. the plot-region margin is a build-time per-axis fraction of the canvas (A6), so a resize, a title or the 560 px height cap moves it up to about 0.8% of the width off twoway's;
  3. a user scheme's `special by_knot1/by_slope1/by_slope2` and `gsize *margin` overrides are not read;
  4. an axis with no finite value at build keeps Bokeh's autorange after a move.
- **TWOWAY_COVERAGE_AUDIT.md:** tag the default-axis rows as drawn. **ROADMAP:** none beyond the rows above. P2.19 stays S44's.
