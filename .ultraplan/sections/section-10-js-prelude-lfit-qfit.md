# Section 10: JavaScript prelude, lfit and qfit refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1a · Risk: red · Batch: 3 · Depends on: 01 · Blocks: 13, 16, 19, 22, 25, 28, 29 · Tasks: 4, 1 commit · Case-id prefix: U10

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): "The saved page recomputes only histogram and kdensity after a filter move; lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline show a stale cue (decision WP-29 M3). The served app refits everything." Evidence: `_dash_agg_config` is set only in `map_histogram` (dash_render.py:18012) and `map_kdensity` (:18381); `_dash_stale_kind` (:1913-1929) returns `"fit"` for every other member of `_DASH_COMPUTED_ONLY_TYPES` (:1884-1888); `_FILTER_JS` (:24612-25447) reads ONE variable per aggregate config (`const raw_col = _pick(_ac_data[ac.varname])`, :25174) and holds two branches, `if (ac.type === 'histogram')` (:25213) and `} else if (ac.type === 'kdensity')` (:25285). After `dash scatter mpg weight || lfit mpg weight, filter(foreign, type(dropdown))` is saved and the dropdown moved to Foreign, the lfit line stays the all-cars regression at 0.3 alpha with the key "mpg (unfiltered)"; the served app redraws it from the 22 foreign cars (`_dash_redraw_for`, research/codebase-mechanics.md §4).

**After this section** the saved page refits `lfit` and `qfit` after every filter move exactly as the served app does: the same rows (joint x, y, weight masking; the layer's own `member_ids`; the filters its `use` list names), the same estimator (the weighted mean of y on an x with no spread; otherwise weighted least squares on the centred design; qfit's two-value rule from `_qfit_design`), the same grid (`_fit_grid`: `n()` points over the kept rows' observed range, or `range()`), the same date handling (Stata units in, axis milliseconds out), and the same empty-layer rule (fewer than two rows draw nothing). The stale cue no longer marks these two types (`_dash_stale_kind` returns None for them) and `test_saved_stale_cue.py::_FROZEN` loses them. The section also lays the shared ground every later JavaScript section (S13, S16, S19, S22, S25, S28, S29) builds on (index A9): the aggregate prelude reads `ac.xvar`, `ac.yvar`, `ac.wvar` jointly, and the helpers `dash_fit_rows`, `dash_weight_norm`, `dash_fit_grid`, `dash_axis_value_of`, `dash_solve`, `dash_wls`, `dash_fitci_se`, `dash_lgamma`, `dash_betainc`, `dash_t_cdf`, `dash_t_ppf` and `dash_qfit_design` exist in `_FILTER_JS` and `js_runner.run_fit_js_block` runs any fit branch under node.

**Why these rows share this section.** F1 is seven commits across seven batches (index A1: F1a..F1g); the first must carry the prelude and the linear-algebra helpers because every estimator needs rows, a grid and (for the bands) a solver and a t quantile. lfit and qfit are the two estimators that need nothing else, so they prove the prelude. This section defines the `_dash_agg_config` schema for every fit type (D-10.a) so that S13-S28 fill keys, never invent them.

**Test order and commit rule (rule 7, BRIEF).** One cycle, one commit `(WP-31 F1a)`: 10-01 writes the failing tests and saves `<scratch>/10-01-failure.txt`, never commits; 10-02 writes the Python side (config tagging, `_dash_stale_kind`, the helpers' Python twins where new); 10-03 writes the JavaScript (prelude, helpers, the two branches) and the js_runner block runner; 10-04 flips the pinned tests, appends the truth block and parity entries, updates the help, closes the entry and commits. No test-only commit exists; no commit is red.

### Section decisions (binding on the executor)

- **D-10.a. The fit config schema.** A fit mapper tags its FIRST returned renderer (the line; for a ci layer the line renderer of `_render_ci_band`) with `r._dash_agg_source = <its own ColumnDataSource>`, `r._dash_agg_rows = self._agg_member_ids(source, view)` and `r._dash_agg_config = {...}` whose keys are, for every type: `type` (the plot type string), `xvar`, `yvar` (source column names), `wvar` (column name or None), `wtype` (`"aw"|"fw"|"pw"|"iw"|None`; None when `_layer_units` returned no weight), `xdatekind`, `ydatekind`, `wdatekind` (the variable's `date_vars` kind or None), `xaxiskind`, `yaxiskind` (the kind `_axis_kind(fig, "x"|"y", options)` gives, or None when the axis draws Stata values), `cols` (the source's column names in order, e.g. `["x", "y"]`), `n` (the grid count `_fit_grid` used, an int), `range` (`[lo, hi]` from `_dash_range_pair` or None), `join` (`{"style": <connect style>}` when `_dash_join_spec(options)[0]` is not `"direct"`, else absent, as kdensity records it). Type-specific keys are added by the owning section and listed there; the complete list (R2-15; S13-S29 fill exactly these): S13 `level`, `std`; S16 `bwidth`, `mean`, `noweight`, `adjust`, `logit`, `y_all_mean`, `max_ops`; S19 `bwidth` (null for the rule of thumb), `degree`, `kernel`, `n_dataset`, `n_user`; S22 S19's plus `pwidth`, `lpvar`, `level`, `role`; S25 `bands` (null for the default), `n_between`, `max_bands`; S28 `level`, `powers`, `max_grid`, `std`; S29 (contour, a non-fit config written by S26's `map_contour`, read by S29): `zvar`, `cuts`, `interp`, `cap`, `capped`, `horizontal`, `fill_color`, `lo`, `hi`, `part`, `fill_index` (section-29 D-29d). S11's `estopts()`/`predopts()`/`estcmd()` points layers carry NO `_dash_agg_*` tags (DECISIONS D3, A20). A key's value is always JSON-serialisable (`float`, `int`, `str`, `None`, list) -- never a numpy scalar.
- **D-10.b. One prelude, two shapes.** The prelude keeps today's `ac.varname` path byte for byte for histogram and kdensity (under `if (ac.varname) { ... }`), and adds an `else` path for a config with `ac.xvar` and `ac.yvar` that calls `dash_fit_rows(ac, _ac_data, _pick)`. The two shapes never mix; `vals`/`wts` keep their names and meaning; `fx`, `fy`, `fw` are the fit path's.
- **D-10.c. `dash_wls` is normal equations, not SVD.** The Python `_dash_wls` (:22185) uses Gram-Schmidt for exact collinearity, then an SVD on a centred and scaled copy. The twin uses the same Gram-Schmidt drop (a column whose residual on the earlier kept ones is below 1e-12 of its norm is omitted, coefficient 0), the same centring and scaling `T`, then Gaussian elimination with partial pivoting (`dash_solve`) on `Z'WZ`. Predictions agree with Python to 1e-9 relative on every corpus row (verified under node for this file; AC-10.2 holds it), bands to 1e-8. The near-singular rank cut (`s_raw > eps*max(n,k)*s_raw[0]`) is NOT ported: the saved page accepts `dash_solve` returning null as "no fit" (an empty layer), and S13's parity test lists the two-valued-x and 5-minute-%tc cases where the rule matters as corpus rows with their own tolerance. Reported for ratification.
- **D-10.d. A date x or y round-trips through `dash_stata_value_of` and the new `dash_axis_value_of`.** The source holds epoch milliseconds for a date column; the JS converts kept values to Stata units with `dash_stata_value_of(v, ac.xdatekind)` (as the histogram branch does), computes in Stata units, and converts the outputs back with `dash_axis_value_of(v, ac.xaxiskind)` -- the twin of `_dash_units_to_axis` (:809) -- or leaves them as Stata values when the axis kind is null (a date sharing a numeric axis, `_on_axis` :15921). A non-finite result is dropped with its row, as `_drop_off_dates` drops it.
- **D-10.e. Empty and degenerate layers write empty columns**, never `continue`: `src.data = {<each col of ac.cols>: []}` then `src.change.emit()` (the kdensity lesson, test_statistical_helpers.py:838-845).
- **D-10.f. The grid moves with the rows.** `_fit_grid` is Stata's: the kept rows' min and max (or `range()`), so the JS recomputes it per move; the served app already does. The grid is NOT frozen at the build's span (histogram's bin edges are, by WP-28's choice; a fit has no such choice in twoway).

## Risk: [red] -- the first edit to `_FILTER_JS`'s prelude since WP-28, shared by every saved page with a filter, and a numerical port whose errors are silent

**Why.** The prelude runs for every aggregate on every move; a fault there breaks histogram and kdensity recounts too. A least-squares port that is slightly wrong draws a plausible, wrong line with no error. `js_runner.run_filter_js_block` slices the script by literal markers; moving a marker breaks three test files.

**Risk factors.** (1) The marker strings `"function dash_pctl"`, `"// agg_sources is a Bokeh model list"`, `"if (ac.type === 'histogram') {"`, `"} else if (ac.type === 'kdensity') {"`, `"// DASH_KDE_RULE"`, `"src.data = { x: xs, y: ys };"` and, for the brush script, `"// ---- KPI recompute, shared by"`, `"dash_apply_kpis(new_data,"`, `"function dash_pctl("`, `"// Stata's kernels ([R] kdensity)"` (:45374-45389). (2) `_dash_wls` subtleties: centring with the constant column, pw sandwich, df. (3) Date x: the grid is computed in Stata units and drawn in ms. (4) Page size: no new per-row JSON (the config carries names and scalars only). (5) Batch partners S08 (Mata table) and S09 (`_dash_add_secondary_axes`) touch neither `_FILTER_JS` nor the mappers.

**Mitigation.** (1) Every helper goes between `dash_kernel`'s closing brace and the "agg_sources" comment; the two new branches go after the kdensity branch's closing `}` and before the loop's closing `}`; `test_js_runner.py` and `TestFilterJavaScript` are run after 10-03. (2) `TestWlsTwin` compares `dash_wls` with `_dash_wls` on nine designs (unweighted, aw, fw, pw, constant x, two-valued x, 1e7 offset) at 1e-9. (3) `TestADateFitRefits` runs the page's own callback on `when` (a `%td` column) and compares with the served document. (4) `TestThePageSize::test_a_fit_config_is_small` bounds a config's JSON under 600 bytes. (5) Boundaries below.

## Dependencies

- **Depends on: 01** (the tracking foundation: BUGS.md entry F1a, the GAPS3 Tracked line, the CHANGELOG marker, the truth script's S10 stub).
- **Blocks: 13, 16, 19, 22, 25, 28, 29.** Each adds branches and helpers after this prelude and uses `dash_fit_rows`, `dash_fit_grid`, `dash_axis_value_of`, `dash_wls`, `dash_t_ppf`, `js_runner.run_fit_js_block`.
- **Parallel batch: 3** with S08 (abbreviations, dash.ado/dash_parse.mata) and S09 (axes 3-9, `_dash_add_secondary_axes`). Merge order 10, 08, 09. S10 is batch 3's one `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind` and `test_saved_stale_cue.py` editor (index A2, R12).

## Evidence

All anchors at `6370ca4` (dash_render.py 51,xxx lines); re-read before editing.

### The prelude reads one variable

dash_render.py:25163-25211 (inside `_FILTER_JS`):

```js
25173    const _ac_data = dash_data_for(ac.use);
25174    let _keep = null;
25175    if (ac.member_ids) { ... }
25183    const _pick = (c) => (_keep === null || !c) ? c : _keep.map(i => c[i]);
25184    const raw_col = _pick(_ac_data[ac.varname]);
25185    if (!raw_col) continue;
25193    let vals, wts = null;
25194    if (ac.wvar && _ac_data[ac.wvar]) { ... pairs, dash_stata_value_of, w > 0 ... }
25212    if (ac.type === 'histogram') {
25285    } else if (ac.type === 'kdensity') {
25374    }
25375 }
25376 // ---- Marks on the layers a saved page does not recompute (WP-29 P0.17) ----
```

### The registration and wiring

`DashRenderer.render()` step 3b (:46219-46237) collects `(r._dash_agg_source, dict(r._dash_agg_config) + member_ids)` for every renderer carrying both attributes; `_build_filter_widgets` (:45706-45717) adds `use` and sets `agg_sources`/`agg_configs_json` on every callback (:45787-45788). Nothing there is type-specific: a fit mapper that tags its renderer is registered with no change.

### The Python estimators (the twin's source)

- `GlyphMapper.map_lfit` (:16244-16340): `_layer_units` -> fewer than 2 rows draw an empty line (`_mark_unfit`, `_mark_insufficient` on one) -> `ptp(x) == 0` gives `[0, average(y, weights=w)]` else `np.polyfit(x, y, 1, w=sqrt(w))` -> `_fit_grid(x, options)` with `n="3"` when the join is a stair or `recast` is set and `n()` absent -> `_on_axis` both -> `ColumnDataSource({"x": x_fit, "y": y_fit})`.
- `GlyphMapper.map_qfit` (:16340-16420): fewer than 2 rows empty; `n()` of exactly 3 is dropped (`qfit, n(3)` plots 100); `_qfit_design(x, x_fit)` (:22293) -> `_dash_wls(X, y, w, _wt)["beta"]`; `LinAlgError` draws empty.
- `_fit_grid` (:20969): `n = _stat_option_float(options, "n", 100, lo=2, hi=10000)`, `linspace(min, max, n)` or `linspace(range lo, hi, n)`.
- `_dash_wls` (:22185-22292), `_qfit_design` (:22293-22341), `_dash_weight_norm` (:22020): aw/pw scaled to sum n, fw raw.
- `_t_ppf` (:20887), `_t_cdf`, `_betainc` (:20858), `_betacf` (:20828): the incomplete-beta inversion by bisection.
- `_dash_units_to_axis` (:809), `_on_axis` (:15921), `GlyphMapper._axis_kind` (:15894).
- `_dash_stale_kind` (:1913-1929); `_DASH_STALE_STATUS_HTML` (:1904-1910) names the three suffixes and "a saved page does not recompute them".

### Tests that pin today's behaviour (to flip, never delete)

- `test/test_saved_stale_cue.py::_FROZEN` (:58) lists lfit and qfit; `TestTheCueAppearsOnAMove::test_a_layer_the_move_took_rows_from_is_marked[lfit|qfit-*]` (:203), `TestTheStaleKind::test_each_type` (:620), `TestTheFrozenTag::test_the_tag_of_each_kind` (:729), `TestTheRegistry::test_one_entry_per_layer_by_figure` (:783) iterate `_FROZEN`.
- `test/test_mode_parity.py::_MOVED_LAYERS` (:2848-2855) lists lfit and qfit as "agreed already" through the stale cue's dimming: after this section they agree because both modes REFIT; the comment at :2850 is updated.
- `test/test_help_claims_*.py` pins the help table line `Fit-line recompute on filter{col 38}No; marked{col 59}Yes` (dash.sthlp:1946) via test_help_conformance's table reader: grep `"No; marked"` in test/ before 10-04 and flip what matches.
- `test/function_test_map.py` entries: `_dash_stale_kind` (:337), `_dash_wls` (:685), `_t_ppf` (:747) stay; new Python helpers (TR-10.6) get entries.

## User stories

- **US-10.1** As a dashboard reader with the saved .html, I want the lfit and qfit lines to follow the filter so that the line I see is the regression on the rows I selected, as it is in the served app.
- **US-10.2** As a Stata user who published a dashboard by email, I want no "(unfiltered)" mark on lfit or qfit after a move so that the page needs no server to be truthful.
- **US-10.3** As a maintainer, I want every later estimator port to reuse one prelude and one solver so that eleven ports do not mean eleven row-masking rules.

## Business requirements

- **BR-10.1** After any filter move on a saved page, an lfit or qfit layer shows the fit twoway draws for the kept rows (same values to 1e-9 relative as `dash` draws for the same rows with an equivalent `if`).
- **BR-10.2** A move that leaves fewer than two usable rows draws no lfit/qfit line, as twoway draws nothing and notes "regress could not fit model".
- **BR-10.3** No lfit or qfit layer is dimmed or suffixed "(unfiltered)" on a saved page; histogram, kdensity and the nine not-yet-ported types keep their cue until their section lands.
- **BR-10.4** The help's Server Mode table says the saved page refits lfit and qfit.
- **BR-10.5** A saved page with a date x or y refits in Stata units and draws on the axis as before the move.

## Technical requirements

- **TR-10.1 Tagging.** `map_lfit` and `map_qfit` set, on the renderer they return (after `_dash_join_glyph`, before `return r`; NOT on the `recast` path, which returns through `_dash_draw_xy_as` -- GAPS3 C16's residual, S46): `r._dash_agg_source = fit_source`, `r._dash_agg_config = self._fit_agg_config("lfit"|"qfit", xvar, yvar, wtype, w, fig, options, ["x", "y"], n_used, rng)`, `r._dash_agg_rows = self._agg_member_ids(source, view)`. The empty-layer returns (`_mark_unfit`) are tagged too, with the same config, so a move that brings rows back refits (the empty source's columns are `x`, `y`). `n_used` is the int `_fit_grid` used (`_lf_opts`' `n` for lfit; `_qopts`' for qfit); `rng` is `_dash_range_pair(options, layer, "")` or None.
- **TR-10.2 `GlyphMapper._fit_agg_config(self, ptype, xvar, yvar, wtype, w, fig, options, cols, n, rng)`** (new staticmethod-like instance method, placed directly after `_layer_units` :15885-15893): returns the D-10.a dict. `wvar` is `options.get("wexp")` when `wtype` is not None else None; `xdatekind = (self.date_vars or {}).get(xvar)`; `xaxiskind = self._axis_kind(fig, "x", options)` (None when the axis is numeric); `join` from `_dash_join_spec(options)[0]`. A class method travels with `GlyphMapper` (no copy-list entry, R2).
- **TR-10.3 `_dash_stale_kind`** (:1913): add, after the kdensity branch, `if t in _DASH_JS_REFIT_TYPES: return None`; new module constant `_DASH_JS_REFIT_TYPES = frozenset({"lfit", "qfit"})` directly after `_DASH_COMPUTED_ONLY_TYPES` (:1888) with the comment `# The computed types the saved page refits in JavaScript (WP-31 F1); each JS section adds its own.` Copy-list entry: constants tuple after `_DASH_STALE_STATUS_HTML` (R2 anchor). Later sections add their types to this frozenset.
- **TR-10.4 The prelude** (`_FILTER_JS` :25184-25211): wrap lines 25184-25211 in `if (ac.varname) { ... }` unchanged, and add:
  ```js
      } else if (ac.xvar && ac.yvar) {
          // WP-31 F1: a fit layer reads x, y (and a weight) jointly.
          const _fr = dash_fit_rows(ac, _ac_data, _pick);
          if (_fr === null) continue;
          fx = _fr.x; fy = _fr.y; fw = _fr.w;
      } else { continue; }
  ```
  with `let fx = null, fy = null, fw = null;` declared beside `let vals, wts = null;`. Nothing else in the prelude changes.
- **TR-10.5 Helpers in `_FILTER_JS`**, inserted after `dash_kernel`'s closing `}` (:25149) and before `// agg_sources is a Bokeh model list` (:25150), in this order, as named function declarations (full bodies in task 10-03): `dash_fit_rows`, `dash_weight_norm`, `dash_fit_grid`, `dash_axis_value_of`, `dash_wmean`, `dash_solve`, `dash_wls`, `dash_fitci_se`, `dash_lgamma`, `dash_betacf`, `dash_betainc`, `dash_t_cdf`, `dash_t_ppf`, `dash_qfit_design`, `dash_fit_write`. The last line before the "agg_sources" comment is `// DASH_FIT_HELPERS_END` (a marker later sections insert before).
- **TR-10.6 Branches**: after the kdensity branch's closing `}` (:25374) and before the loop's `}` (:25375): `} else if (ac.type === 'lfit') { ... } else if (ac.type === 'qfit') { ... }` ending with the marker comment `// DASH_FIT_BRANCHES_END` on the line before the loop's closing brace (later sections insert their branch before it).
- **TR-10.7 `js_runner.run_fit_js_block(ac, x, y, w=None)`** (new, after `run_filter_js_block`): slices `helpers = js[js.index("function dash_pctl"):js.index("// agg_sources is a Bokeh model list")]`, the branch `js[js.index("} else if (ac.type === '%s') {" % ac["type"]) + len(...):<next "} else if (ac.type === '" or "// DASH_FIT_BRANCHES_END">]`, and runs it with `const ac = <json>; const fx = <json x>; const fy = <json y>; const fw = <json w or null>; const src = {data: null, change: {emit: () => {}}}; for (let _i = 0; _i < 1; _i++) { <branch> }` then prints `src.data`. x, y are passed in Stata units (the harness bypasses `dash_fit_rows`; `TestFitRows` tests that function alone). Also `run_fit_rows(ac, data)` running `dash_fit_rows` on a `{col: list}` object.
- **TR-10.8 Flips**: `_FROZEN` loses `"lfit"`, `"qfit"`; a new module list `_REFIT = ["lfit", "qfit"]` and a class `TestARefitLayerIsNeverMarked` parametrised over `_REFIT` asserting no `muted`, no suffix, the status Div hidden after `_MOVES[0]` (red at base: they are marked).
- **TR-10.9 Help**: dash.sthlp:1946 becomes `{col 5}Fit-line recompute on filter{col 38}lfit, qfit; others marked{col 59}Yes`; the paragraph at :1962-1980 lists the eleven types: remove `{cmd:lfit}, {cmd:qfit},` from the "does not refit" list and add the sentence `A straight or quadratic fit ({cmd:lfit}, {cmd:qfit}) is refitted from the rows that pass the filter, on {cmd:n()} points over their range or {cmd:range()}.` directly before "When a move removes observations". `_DASH_STALE_STATUS_HTML` is unchanged (it names kinds, not types).
- **TR-10.10 Timing (M10)**: `test_estimator_cost.py::TestTheJsTwinsAreBounded::test_lfit_and_qfit_under_node_on_1e5_rows`: `run_fit_js_block` on 100,000 rows completes under 2 s of node wall time each (node's own `process.hrtime` printed beside the data).
- **TR-10.11 Parity corpus (R8)**: `MOVE_CORPUS` gains, under `# WP-31 F1a: lfit and qfit refit on the saved page`, `_move_case("lfit, dropdown", _MOVES[0], [_sc(), plot_for("lfit")])`, `_move_case("qfit, range", _MOVES[1], [_sc(), plot_for("qfit")])`, `_move_case("lfit [aw=weight], slider", _MOVES[2], [plot_for("lfit", {"weight": "aweight", "wexp": "weight"})])`, `_move_case("lfit on a date x, range", _MOVES[1], [plot_for("lfit", yvar="mpg", xvar="when")])`, `_move_case("qfit with range(1500 5500) n(7), dropdown", _MOVES[0], [plot_for("qfit", {"range": "1500 5500", "n": "7"})])`.
- **TR-10.12 function_test_map.py**: `GlyphMapper._fit_agg_config` -> `test/test_js_fit_refit.py::TestTheConfig::test_lfit_config_keys`; `js_runner.run_fit_js_block`, `js_runner.run_fit_rows` are test infrastructure (test_js_runner.py gains one test each).

## Boundaries

- Do not touch `map_lfitci`, `map_qfitci`, `map_lowess`, `map_lpoly*`, `map_mband`, `map_mspline`, `map_fpfit*` (S13-S28), the `recast` path (S46), `_BRUSH_JS` (S51/S52), `_build_filter_widgets` (R12), the histogram/kdensity branches, `dash_pctl`/`dash_wpctl`/`dash_kernel`, `_dash_wls` in Python, `_FIT_GRID`, `_dash_option_rules`, `_make_figure_body`, `_generate_app_source`.
- Do not change the stale cue's constants or its JS marking block; only `_dash_stale_kind`'s answer changes.
- No per-row data in a config (`member_ids` is render()'s, as today).

## Stata truth

No new extractor: twoway's lfit/qfit values on a subset are measured live in the truth block (`capture noisily twoway lfit mpg weight if foreign == 1, n(5)` and the serset read through `serset use`), as WP-30 EW-02 did; `test/fixtures/stat_truth.json` keys `datasets`, `weighted`, `weighted_fit_check` (regress coefficients on auto by weight type) are the Python twin's existing pins and the parity test reuses them.

**Truth block** (R1) in `test/test_wp31_truth.cscript`, under S01's stub header `* ==== S10 F1a: JavaScript prelude, lfit and qfit ====`, helpers `_u10_*` above the header:
- **U10-01** `sysuse auto; dash scatter mpg weight || lfit mpg weight, filter(foreign, type(dropdown)) name(zu10a)`; `_dash_serve_spec, specpath() datapath()`; python: render the saved page (`DashRenderer`), move the Select to Foreign through `js_runner.JsSession`, read the lfit source; Stata: `quietly twoway lfit mpg weight if foreign == 1, n(100) name(t, replace)` then `serset`-read `.t.plotregion1.plot1.serset` x and y; compare every point to 1e-8 relative (`_u10_close`).
- **U10-02** the same for `qfit mpg weight, n(50)` with the range filter `price, type(range)` moved to `4500 11385` versus `twoway qfit mpg weight if inrange(price, 4500, 11385), n(50)`.
- **U10-03** `lfit mpg weight [aw=displacement]` dropdown to Domestic versus `twoway lfit mpg weight [aw=displacement] if foreign == 0`.
- **U10-04** a move leaving one row (`price` slider to 15906): the saved lfit source is empty; twoway on `if price >= 15906` notes "regress could not fit model" (`cert_file_has` on the log).
- **U10-05** `set obs 10; gen x = _n; gen y = 2*x + 1; gen d = mdy(1,_n,2020); format d %td; dash lfit y d, filter(x, type(slider))`: after the slider to 4, the saved source's x values equal `_dash_units_to_axis(twoway's serset x, "td")` to 1 ms.

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_render`, `_move`, `_MOVES` from test_saved_filter_layers; `_served_after_move`, `_spec`, `plot_for` from test_mode_parity; `JsSession`, `run_fit_js_block`, `run_fit_rows`, `requires_node` from js_runner; `_DF` with its `when` column.

- Test: `map_lfit` and `map_qfit` tag the renderer with `_dash_agg_source`, `_dash_agg_config` (every D-10.a key) and `_dash_agg_rows` -- `TestTheConfig::test_lfit_config_keys`, `::test_qfit_config_keys`, `::test_an_empty_layer_is_tagged`, `::test_a_recast_layer_is_not_tagged` (guard) (red: AttributeError).
- Test: a date x records `xdatekind == "td"` and `xaxiskind == "td"`; a date on a numeric axis records `xaxiskind is None` -- `::test_date_kinds`.
- Test: `_dash_stale_kind("lfit", {})` and `("qfit", {})` are None; the other nine are `"fit"` -- `TestStaleKind::test_lfit_and_qfit_are_refit` (red).
- Test: `dash_fit_rows` drops a row whose x, y or w is null/NaN, keeps only `w > 0`, converts dates, honours `member_ids`, returns null for a missing column -- `TestFitRows::test_joint_drop`, `::test_positive_weights`, `::test_dates`, `::test_member_ids`, `::test_missing_column` (red: ReferenceError).
- Test: `dash_fit_grid` equals `_fit_grid` for n in (2, 3, 100), with and without range, on a constant x -- `TestFitGrid::test_matches_python[case]`.
- Test: `dash_axis_value_of` equals `_dash_units_to_axis` for td, tc, tC, tw, tm, tq, th, ty at integers and halves -- `TestAxisValueOf::test_every_kind[kind]`.
- Test: `dash_wls` beta, df, s2 and `dash_fitci_se` equal `_dash_wls`/`_dash_fitci_se` on nine designs -- `TestWlsTwin::test_design[case]` (1e-9 relative on beta and se; exact on df).
- Test: `dash_t_ppf(p, df)` equals `_t_ppf` to 1e-12 for p in (.75, .95, .975, .995) and df in (1, 2, 5, 30, 72, 1e4) -- `TestTPpf::test_matches_python[p-df]`; `dash_lgamma` against `math.lgamma` to 1e-13 relative -- `::test_lgamma`.
- Test: `dash_solve` returns null on a singular system and the solution on a 3x3 pivot-needing one -- `TestSolve::test_singular`, `::test_pivot`.
- Test: the lfit branch under node equals `map_lfit`'s source on the same subset for: unweighted, aw, fw, pw, constant x, one row (empty), n(3), range(1500 5500) -- `TestLfitBranch::test_matches_python[case]` (`assert_allclose(rtol=1e-9, atol=1e-12)`).
- Test: the qfit branch equals `map_qfit` for: default, two-valued x with |a+b| > 1 (x^2 kept), two-valued x with |a+b| <= 1 (x kept), n(3) (100 points), aw -- `TestQfitBranch::test_matches_python[case]`.
- Test: after `_MOVES[k]` the saved page's lfit/qfit source equals the served document's after the same move -- `TestTheSavedPageRefits::test_saved_equals_served[type-move]` (red: the saved source is the build's).
- Test: a date x (`when`) refits and draws in ms -- `TestADateFitRefits::test_td_x_round_trips`.
- Test: a config's JSON is under 600 bytes -- `TestThePageSize::test_a_fit_config_is_small` (guard).
- Test: no lfit/qfit renderer is muted, no legend suffix, the status Div hidden after a move -- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked::test_not_marked[type]` (red).
- Test: the histogram and kdensity recounts still pass -- `test_statistical_helpers.py::TestFilterJavaScript` (guard, run after 10-03).

### Cases in cscripts

- `test_wp31_truth.cscript` U10-01..U10-05 (red at base: the saved source is the build's).

### Flips (in place, each with a `Flipped:` line)

- `test_saved_stale_cue.py::_FROZEN` loses lfit and qfit (the parametrised tests shrink); docstring reason "lfit and qfit are refitted by the saved page (WP-31 F1a)".
- `test_mode_parity.py:2850` comment; `_MOVED_LAYERS` unchanged (both still agree).
- Any help-conformance pin of `No; marked` (grep in 10-04).

### Parity corpus (R8)

TR-10.11's five `MOVE_CORPUS` entries (guards after the fix; red before: the saved fit differs from the served).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Config schema and tagging | pytest `TestTheConfig` | -- | saved (served reads none) |
| Row masking, grid, dates, solver, t quantile | pytest under node `TestFitRows`, `TestFitGrid`, `TestAxisValueOf`, `TestWlsTwin`, `TestTPpf`, `TestSolve` | -- | n/a |
| lfit/qfit branch vs Python mapper | pytest under node `TestLfitBranch`, `TestQfitBranch` | `stat_truth.json` `weighted_data` rows for the weighted cases | n/a |
| Saved page after a move vs served app | pytest `TestTheSavedPageRefits`, `TestADateFitRefits`; `MOVE_CORPUS` | -- | yes |
| Stale cue stops marking | pytest `TestARefitLayerIsNeverMarked`, `TestStaleKind` | -- | saved |
| Stata truth on a subset | cscript U10-01..05 | live | saved vs twoway |
| Cost | pytest `test_estimator_cost.py::TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-10.1** After every `_MOVES` move, the saved page's lfit and qfit sources equal the served document's to 1e-9 relative, on `_DF` and on auto.
- **AC-10.2** `dash_wls`/`dash_fitci_se` agree with `_dash_wls`/`_dash_fitci_se` to 1e-9 relative on all nine designs; `dash_t_ppf` to 1e-12.
- **AC-10.3** No lfit/qfit is marked; the nine other fit types and histogram/kdensity are marked exactly as at base.
- **AC-10.4** `test_statistical_helpers.py`, `test_js_runner.py`, `test_saved_filter_layers.py`, `test_filter_exclude.py`, `test_histogram_edge_rule.py`, `test_csp.py` are green after 10-03.
- **AC-10.5** U10-01..05 pass under the console binary; 100,000-row lfit and qfit refits under node take under 2 s each.

## Tasks

**Commit boundary.** Tasks 10-01 to 10-04 form the one F1a commit, subject `Refit lfit and qfit on the saved page after a filter move (WP-31 F1a)`, made by 10-04 on `wp31-s10` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s10`. The body opens with `<scratch>/10-01-failure.txt`, then the measured defect (the lfit source after the Foreign move equals the build's; the served app's differs), then what changed where (both renderers: the mappers tag, `_FILTER_JS` refits, `_dash_stale_kind` stops marking), then one line each: `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[lfit-dropdown to Foreign] -- failed at 6370ca4 with <text>`, `Regression: test/test_wp31_truth.cscript U10-01`, `Flipped: test/test_saved_stale_cue.py::_FROZEN -- lfit and qfit were listed as frozen because the saved page did not refit them (F1a)`, `Fixture: none`, `BUGS.md: "<F1a title>" (closed)`, `GAPS3: F1a Tracked`. No tool or vendor name anywhere.

<task type="auto" id="10-01">
  <name>Write the failing refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py, test/test_js_runner.py</files>
  <action><![CDATA[Create test/test_js_fit_refit.py with every stub of "TDD test stubs" (module docstring: "WP-31 F1a: lfit and qfit refit on the saved page; the JS prelude and helpers every later estimator port uses"). Import `_render`, `_move`, `_MOVES` from test_saved_filter_layers, `_served_after_move`, `_spec`, `_DF`, `plot_for` from test_mode_parity, and from js_runner `JsSession`, `requires_node`, `run_js`, and the two functions this section adds, `run_fit_js_block` and `run_fit_rows` (an ImportError is the expected red for the node classes; guard the import with `getattr(js_runner, "run_fit_js_block", None)` and `pytest.skip` is NOT allowed -- let the import fail). `TestWlsTwin`'s nine designs: (a) x=[1..8], y=auto mpg[:8], no weight; (b) aw=rep78-like [3,3,4,2,5,3,4,1]; (c) fw same; (d) pw same; (e) constant x=[2]*8; (f) x two-valued [1,3,1,3,1,3,1,3]; (g) x two-valued [-1,2,...]; (h) x = 1e7 + [1..8]; (i) 5-minute %tc-like x = 1.3e12 + 300000*[0..7]. For each, build the design as the mapper does (lfit: [1, x-mean(x)]; qfit: `_qfit_design`), call `dr._dash_wls` and run `dash_wls` under node on the same JSON arrays through `run_js(helpers + "...process.stdout.write(JSON.stringify(dash_wls(X, y, w, wtype)))")` where `helpers = dr._FILTER_JS[dr._FILTER_JS.index("function dash_pctl"):dr._FILTER_JS.index("// agg_sources is a Bokeh model list")]`; compare `beta` (rtol 1e-9, atol 1e-12), `df` exactly, `s2` (rtol 1e-9). In test_saved_stale_cue.py add `_REFIT = ["lfit", "qfit"]` after `_FROZEN` and the class `TestARefitLayerIsNeverMarked` (parametrised over `_REFIT` and `_MOVES`): render `_spec([_sc(), plot_for(t)], {"filter": filt})`, run the move through `_session(r)`, assert every GlyphRenderer of the fit layer has `muted is False`, every LegendItem label lacks " (unfiltered)", and the status Div (`tags == ["dash_stale_status"]`, as `_stale_cue_args` tags it -- read the tag name at :45817-45899) is `visible is False`. In test_js_runner.py add `TestRunFitJsBlock::test_runs_the_lfit_branch_on_three_rows` (expects `{"x": [...], "y": [...]}` of length 100) and `TestRunFitRows::test_joint_masking`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked test/test_js_runner.py -q -n0 2>&1 | tee <scratch>/10-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/10-01-failure.txt prints a number of at least 30; grep -c "passed" prints the guard count only (TestTheConfig::test_a_recast_layer_is_not_tagged and TestThePageSize may pass); `git -C $WT status --porcelain | grep -c '^A\|^M'` prints 0 (nothing staged).]]></verify>
  <done>Every F1a regression test exists and fails against the unmodified tree, with the failure text saved and nothing committed.</done>
</task>

<task type="auto" id="10-02">
  <name>Tag lfit and qfit and stop marking them</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[In dash_render.py: (1) after `_DASH_COMPUTED_ONLY_TYPES` (:1884-1888) add `_DASH_JS_REFIT_TYPES = frozenset({"lfit", "qfit"})` with the TR-10.3 comment; in `_dash_stale_kind` (:1913) insert, after the `if t == "kdensity":` block and before `return "fit"`, the two lines `if t in _DASH_JS_REFIT_TYPES:` / `    return None`; add `"_DASH_JS_REFIT_TYPES",` to the constants copy tuple directly after the `"_DASH_STALE_STATUS_HTML",` entry (R2; grep the tuple at :46584-46784 for that line). (2) Add `GlyphMapper._fit_agg_config` after `_layer_units` (:15893):
```python
    def _fit_agg_config(self, ptype, xvar, yvar, wtype, w, fig, options,
                        cols, n, rng):
        """The saved page's refit config for a fit layer (WP-31 F1a, D-10.a)."""
        dv = dict(self.date_vars or {})
        wvar = str(options.get("wexp", "") or "").strip() or None
        if wtype is None or w is None:
            wvar, wtype = None, None
        cfg = {"type": str(ptype), "xvar": str(xvar), "yvar": str(yvar),
               "wvar": wvar, "wtype": wtype,
               "xdatekind": dv.get(xvar), "ydatekind": dv.get(yvar),
               "wdatekind": dv.get(wvar) if wvar else None,
               "xaxiskind": self._axis_kind(fig, "x", options),
               "yaxiskind": self._axis_kind(fig, "y", options),
               "cols": [str(c) for c in cols], "n": int(n),
               "range": ([float(rng[0]), float(rng[1])] if rng else None)}
        style = _dash_join_spec(options)[0]
        if style not in ("direct", None, ""):
            cfg["join"] = {"style": str(style)}
        return cfg
```
Check `_axis_kind`'s return at :15894-15920 and coerce to `str` or None. (3) In `map_lfit` (:16244): compute `_n_used = int(_stat_option_float(_lf_opts, "n", float(_FIT_GRID), "lfit", lo=2.0, hi=10000.0) or _FIT_GRID)` and `_rng = _dash_range_pair(_lf_opts, "lfit", "drawing over the observed range of x")` beside the `_fit_grid` call (reuse: `_fit_grid` warns on an unreadable range -- call `_dash_range_pair` under `warnings.catch_warnings(); simplefilter("ignore")` to avoid a second note); before the final `return r` add `r._dash_agg_source = fit_source`, `r._dash_agg_config = self._fit_agg_config("lfit", xvar, yvar, _wt, w, fig, options, ["x", "y"], _n_used, _rng)`, `r._dash_agg_rows = self._agg_member_ids(source, view)`. For the `len(x) < 2` return, tag the empty renderer the same way with `n = _FIT_GRID`, `rng` from options, `wtype` from `_wt`, and `fit_source` = the renderer's `data_source`. Do the same in `map_qfit` (:16340) with `_qopts`, layer "qfit". Do not tag the `recast` return. (4) Update test/function_test_map.py: add `'GlyphMapper._fit_agg_config': 'test/test_js_fit_refit.py::TestTheConfig::test_lfit_config_keys',` in alphabetical place. Run `python3 -m pytest test/test_js_fit_refit.py::TestTheConfig test/test_js_fit_refit.py::TestStaleKind test/test_saved_stale_cue.py test/test_function_test_map.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName -q -n0`.]]></action>
  <verify><![CDATA[The command's last line reports 0 failed apart from `TestARefitLayerIsNeverMarked` (still red: the JS does not refit yet) and the four `_FROZEN`-parametrised classes' lfit/qfit nodes (red until the flip in 10-04); `python3 -c "import dash_render as d; print(d._dash_stale_kind('lfit',{}), d._dash_stale_kind('lowess',{}))"` prints `None fit`.]]></verify>
  <done>Both mappers tag their renderers with the D-10.a config and the stale cue no longer marks lfit or qfit.</done>
</task>

<task type="auto" id="10-03">
  <name>Add the prelude, helpers and two branches</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[In `_FILTER_JS`: (A) TR-10.4's prelude edit at :25184-25211. (B) Insert the helpers after `dash_kernel`'s closing `}` and before `// agg_sources is a Bokeh model list`:
```js
// ---- WP-31 F1: the fit layers' shared helpers (S10); every later
// estimator port (lfitci..fpfitci, contour) builds on these.  Named
// functions, so js_runner.run_fit_js_block's helper slice carries them.
// The kept rows of a fit: x, y (and a weight) as PAIRS, a row surviving
// only when every one is a finite number (a date converted to its Stata
// units) and the weight, when the layer has one, is positive -- the
// joint drop GlyphMapper._layer_units applies.  null when a column is
// missing.
function dash_fit_rows(ac, data, pick) {
    const xc = pick(data[ac.xvar]), yc = pick(data[ac.yvar]);
    if (!xc || !yc) return null;
    const wc = (ac.wvar && data[ac.wvar]) ? pick(data[ac.wvar]) : null;
    if (ac.wvar && !wc) return null;
    const fin = (v) => v !== null && v !== undefined && typeof v === "number" && isFinite(v);
    const x = [], y = [], w = wc ? [] : null;
    for (let i = 0; i < xc.length; i++) {
        let xv = xc[i], yv = yc[i];
        if (!fin(xv) || !fin(yv)) continue;
        if (ac.xdatekind) { xv = dash_stata_value_of(xv, ac.xdatekind); if (xv === null) continue; }
        if (ac.ydatekind) { yv = dash_stata_value_of(yv, ac.ydatekind); if (yv === null) continue; }
        if (wc) {
            let wv = wc[i];
            if (!fin(wv)) continue;
            if (ac.wdatekind) { wv = dash_stata_value_of(wv, ac.wdatekind); if (wv === null) continue; }
            if (!(wv > 0)) continue;
            w.push(wv);
        }
        x.push(xv); y.push(yv);
    }
    return {x: x, y: y, w: w};
}
// Weights as regress uses them (_dash_weight_norm): aw/pw scaled to sum n,
// fw raw, unit weights when none.
function dash_weight_norm(w, wtype, n) {
    if (!w) return new Array(n).fill(1);
    if (wtype === "fw") return w.slice();
    let s = 0; for (const v of w) s += v;
    return w.map(v => v * (n / s));
}
// Stata's grid (_fit_grid): n points from min to max (or range()).
function dash_fit_grid(x, n, range) {
    let lo = Infinity, hi = -Infinity;
    for (const v of x) { if (v < lo) lo = v; if (v > hi) hi = v; }
    if (range) { lo = range[0]; hi = range[1]; }
    const k = Math.max(2, Math.floor(n));
    const out = new Array(k);
    for (let i = 0; i < k; i++) out[i] = lo + (hi - lo) * i / (k - 1);
    out[k - 1] = hi;
    return out;
}
// _dash_units_to_axis: a Stata value of a date kind as epoch ms; the
// value itself when kind is null (a date on a numeric axis); NaN when
// not a number or outside Stata's dates.
function dash_axis_value_of(v, kind) {
    if (!(typeof v === "number" && isFinite(v))) return NaN;
    if (!kind) return v;
    const E = -315619200000;
    if (kind === "td") return v * 86400000 + E;
    if (kind === "tc" || kind === "tC") return v + E;
    if (!(Math.abs(v) < 1e7)) return NaN;
    const f = Math.floor(v);
    const start = (u) => {
        if (kind === "ty") return Date.UTC(1960 + u, 0, 1);
        if (kind === "th") return Date.UTC(1960 + Math.floor(u / 2), 6 * (((u % 2) + 2) % 2), 1);
        if (kind === "tq") return Date.UTC(1960 + Math.floor(u / 4), 3 * (((u % 4) + 4) % 4), 1);
        if (kind === "tm") return Date.UTC(1960 + Math.floor(u / 12), ((u % 12) + 12) % 12, 1);
        if (kind === "tw") return Date.UTC(1960 + Math.floor(u / 52), 0, 1 + 7 * (((u % 52) + 52) % 52));
        return NaN;
    };
    const a = start(f);
    if (v === f) return a;
    const b = start(f + 1);
    return a + (v - f) * (b - a);
}
function dash_wmean(v, w) {
    let s = 0, sw = 0;
    for (let i = 0; i < v.length; i++) { s += w[i] * v[i]; sw += w[i]; }
    return s / sw;
}
// A k x k linear system by Gaussian elimination with partial pivoting;
// null when singular or not finite.
function dash_solve(A, b) {
    const k = b.length;
    const M = A.map((row, i) => row.slice().concat([b[i]]));
    for (let col = 0; col < k; col++) {
        let p = col;
        for (let r = col + 1; r < k; r++) if (Math.abs(M[r][col]) > Math.abs(M[p][col])) p = r;
        if (!(Math.abs(M[p][col]) > 0)) return null;
        if (p !== col) { const t = M[p]; M[p] = M[col]; M[col] = t; }
        for (let r = col + 1; r < k; r++) {
            const f = M[r][col] / M[col][col];
            if (f === 0) continue;
            for (let c = col; c <= k; c++) M[r][c] -= f * M[col][c];
        }
    }
    const x = new Array(k).fill(0);
    for (let r = k - 1; r >= 0; r--) {
        let s = M[r][k];
        for (let c = r + 1; c < k; c++) s -= M[r][c] * x[c];
        x[r] = s / M[r][r];
        if (!isFinite(x[r])) return null;
    }
    return x;
}
// regress y X [w], as _dash_wls reports it (D-10.c): X is an array of
// rows [1, x1, ...]; exact collinearity dropped in column order by a
// twice-orthogonalised Gram-Schmidt (below 1e-12 of the column's norm);
// centred and scaled through T when every kept column is usable; the
// normal equations solved by dash_solve.  Returns {beta (length k, 0 for
// an omitted column), keep, T, Ainv (on the T basis), resid, rss, N, df,
// s2, meat (pw: the HC1 sandwich's middle, else null)} or null.
function dash_wls(X, y, w, wtype) {
    const n = X.length; if (!n) return null;
    const k = X[0].length;
    const ww = dash_weight_norm(w, wtype, n);
    const sw = ww.map(Math.sqrt);
    const keep = [], Q = [];
    for (let j = 0; j < k; j++) {
        let v = X.map((r, i) => r[j] * sw[i]);
        let nv0 = Math.sqrt(v.reduce((a, b) => a + b * b, 0));
        if (!(nv0 > 0) || !isFinite(nv0)) continue;
        for (let pass = 0; pass < 2; pass++) {
            for (const q of Q) {
                let d = 0; for (let i = 0; i < n; i++) d += q[i] * v[i];
                for (let i = 0; i < n; i++) v[i] -= d * q[i];
            }
        }
        const nv = Math.sqrt(v.reduce((a, b) => a + b * b, 0));
        if (nv > 1e-12 * nv0) { keep.push(j); Q.push(v.map(e => e / nv)); }
    }
    if (!keep.length) return null;
    const kk = keep.length;
    const Xk = X.map(r => keep.map(j => r[j]));
    const W = ww.reduce((a, b) => a + b, 0);
    const T = [];
    for (let i = 0; i < kk; i++) { T.push(new Array(kk).fill(0)); T[i][i] = 1; }
    const isConst = (j) => { let lo = Infinity, hi = -Infinity; for (const r of Xk) { if (r[j] < lo) lo = r[j]; if (r[j] > hi) hi = r[j]; } return hi - lo === 0; };
    const consts = []; for (let j = 0; j < kk; j++) if (isConst(j)) consts.push(j);
    for (let j = 0; j < kk; j++) {
        if (consts.indexOf(j) >= 0) continue;
        let mu = 0; if (consts.length) { for (let i = 0; i < n; i++) mu += ww[i] * Xk[i][j]; mu /= W; }
        let ss = 0; for (let i = 0; i < n; i++) ss += ww[i] * (Xk[i][j] - mu) * (Xk[i][j] - mu);
        const sd = Math.sqrt(ss / W) || 1;
        if (consts.length) T[consts[0]][j] = -mu / sd;
        T[j][j] = 1 / sd;
    }
    const Z = Xk.map(r => T[0].map((_, c) => { let s = 0; for (let m = 0; m < kk; m++) s += r[m] * T[m][c]; return s; }));
    const A = [], g = new Array(kk).fill(0);
    for (let a = 0; a < kk; a++) { A.push(new Array(kk).fill(0)); }
    for (let i = 0; i < n; i++) {
        for (let a = 0; a < kk; a++) {
            g[a] += ww[i] * Z[i][a] * y[i];
            for (let b = 0; b < kk; b++) A[a][b] += ww[i] * Z[i][a] * Z[i][b];
        }
    }
    const bz = dash_solve(A, g);
    if (bz === null) return null;
    const Ainv = [];
    for (let c = 0; c < kk; c++) {
        const e = new Array(kk).fill(0); e[c] = 1;
        const col = dash_solve(A, e); if (col === null) return null;
        Ainv.push(col);
    }
    const resid = new Array(n);
    let rss = 0;
    for (let i = 0; i < n; i++) { let p = 0; for (let a = 0; a < kk; a++) p += Z[i][a] * bz[a]; resid[i] = y[i] - p; rss += ww[i] * resid[i] * resid[i]; }
    const beta = new Array(k).fill(0);
    for (let m = 0; m < kk; m++) { let s = 0; for (let c = 0; c < kk; c++) s += T[m][c] * bz[c]; beta[keep[m]] = s; }
    const df = W - kk;
    const s2 = df > 0 ? rss / df : NaN;
    let meat = null;
    if (wtype === "pw") {
        meat = []; for (let a = 0; a < kk; a++) meat.push(new Array(kk).fill(0));
        const fac = n / Math.max(n - kk, 1);
        for (let i = 0; i < n; i++) { const u = ww[i] * ww[i] * resid[i] * resid[i] * fac; for (let a = 0; a < kk; a++) for (let b = 0; b < kk; b++) meat[a][b] += u * Z[i][a] * Z[i][b]; }
    }
    return {beta, keep, T, Ainv, resid, rss, N: W, df, s2, meat};
}
// _dash_fitci_se at the grid design Xg (rows [1, xg, ...]): stdp =
// sqrt(z0' V z0) in the T basis, V = s2 Ainv (pw: Ainv meat Ainv);
// stdf = sqrt(stdp^2 + s2); stdr = sqrt(s2 - stdp^2), NaN below 0;
// "none" is every value NaN.
function dash_fitci_se(Xg, fit, std) {
    const kk = fit.keep.length;
    return Xg.map(r => {
        const zk = fit.keep.map(j => r[j]);
        const z = new Array(kk).fill(0);
        for (let c = 0; c < kk; c++) for (let m = 0; m < kk; m++) z[c] += zk[m] * fit.T[m][c];
        let v = 0;
        if (fit.meat === null) {
            for (let a = 0; a < kk; a++) for (let b = 0; b < kk; b++) v += z[a] * fit.Ainv[a][b] * z[b];
            v *= fit.s2;
        } else {
            const az = new Array(kk).fill(0);
            for (let a = 0; a < kk; a++) for (let b = 0; b < kk; b++) az[a] += fit.Ainv[a][b] * z[b];
            for (let a = 0; a < kk; a++) for (let b = 0; b < kk; b++) v += az[a] * fit.meat[a][b] * az[b];
        }
        const stdp2 = Math.max(v, 0);
        if (std === "none") return NaN;
        if (std === "stdf") return Math.sqrt(stdp2 + fit.s2);
        if (std === "stdr") { const d = fit.s2 - stdp2; return d >= 0 ? Math.sqrt(d) : NaN; }
        return Math.sqrt(stdp2);
    });
}
```
then the t quantile (verified under node for this plan: `dash_t_ppf(0.975, 10)` = 2.228138851986344, `(0.975, 72)` = 1.993463566661859, `(0.995, 3)` = 5.840909309733348, equal to `_t_ppf` to 1e-15; `dash_lgamma(5)` = 3.178053830347944):
```js
// Student's t quantile as _t_ppf computes it: the regularised incomplete
// beta (Lentz's continued fraction, _betacf) through lgamma (Lanczos,
// g = 7, nine terms), inverted by bisection.  NaN for p outside (0, 1) or
// df <= 0, where Python raises (a config never carries those).
function dash_lgamma(x) {
    const C = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
               771.32342877765313, -176.61502916214059, 12.507343278686905,
               -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - dash_lgamma(1 - x);
    x -= 1;
    let a = C[0];
    const t = x + 7.5;
    for (let i = 1; i < 9; i++) a += C[i] / (x + i);
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function dash_betacf(a, b, x) {
    const TINY = 1e-300, EPS = 3e-16, ITMAX = 300;
    const qab = a + b, qap = a + 1, qam = a - 1;
    let c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < TINY) d = TINY;
    d = 1 / d;
    let h = d;
    for (let m = 1; m <= ITMAX; m++) {
        const m2 = 2 * m;
        let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
        d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
        c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
        d = 1 / d; h *= d * c;
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
        d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
        c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
        d = 1 / d;
        const delta = d * c;
        h *= delta;
        if (Math.abs(delta - 1) < EPS) break;
    }
    return h;
}
function dash_betainc(a, b, x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const lb = dash_lgamma(a + b) - dash_lgamma(a) - dash_lgamma(b);
    const front = Math.exp(lb + a * Math.log(x) + b * Math.log1p(-x));
    if (x < (a + 1) / (a + b + 2)) return front * dash_betacf(a, b, x) / a;
    return 1 - front * dash_betacf(b, a, 1 - x) / b;
}
function dash_t_cdf(t, df) {
    const xx = df / (df + t * t);
    const p = 0.5 * dash_betainc(0.5 * df, 0.5, xx);
    return t > 0 ? 1 - p : p;
}
function dash_t_ppf(p, df) {
    if (!(p > 0 && p < 1) || !(df > 0)) return NaN;
    if (Math.abs(p - 0.5) < 1e-15) return 0;
    let lo = -1, hi = 1;
    while (dash_t_cdf(lo, df) > p) { lo *= 2; if (lo < -1e12) break; }
    while (dash_t_cdf(hi, df) < p) { hi *= 2; if (hi > 1e12) break; }
    for (let i = 0; i < 200; i++) {
        const mid = 0.5 * (lo + hi);
        if (dash_t_cdf(mid, df) < p) lo = mid; else hi = mid;
        if (hi - lo < 1e-13 * Math.max(1, Math.abs(mid))) break;
    }
    return 0.5 * (lo + hi);
}
```
then
```js
// _qfit_design: the quadratic design on x and the grid, centred and
// scaled; an x with exactly two values keeps x^2 when |a + b| > 1 and x
// otherwise.  Returns {X, Xg}.
function dash_qfit_design(x, xg) {
    const vals = Array.from(new Set(x)).sort((a, b) => a - b);
    if (vals.length === 2 && Math.abs(vals[0] + vals[1]) > 1) {
        const s = Math.max(Math.abs(vals[0]), Math.abs(vals[1])) || 1;
        const q = x.map(v => (v / s) * (v / s)), qg = xg.map(v => (v / s) * (v / s));
        const qmu = q.reduce((a, b) => a + b, 0) / q.length;
        const qsd = Math.sqrt(q.reduce((a, b) => a + (b - qmu) * (b - qmu), 0) / q.length) || 1;
        return {X: q.map(v => [1, (v - qmu) / qsd]), Xg: qg.map(v => [1, (v - qmu) / qsd])};
    }
    const mu = x.reduce((a, b) => a + b, 0) / x.length;
    const sd = Math.sqrt(x.reduce((a, b) => a + (b - mu) * (b - mu), 0) / x.length) || 1;
    const z = x.map(v => (v - mu) / sd), zg = xg.map(v => (v - mu) / sd);
    return {X: z.map(v => [1, v, v * v]), Xg: zg.map(v => [1, v, v * v])};
}
// Write a fit's columns: xs/ys in Stata units are placed on the axes
// (dash_axis_value_of), a row dropped when any value is not finite
// (_drop_off_dates); extra columns (a band) travel in `more`.  Empty
// arrays clear the layer (D-10.e).
function dash_fit_write(src, ac, xs, ys, more) {
    const out = {}; for (const c of ac.cols) dash_own_col(out, c);
    const names = ac.cols;
    for (let i = 0; i < xs.length; i++) {
        const xv = dash_axis_value_of(xs[i], ac.xaxiskind), yv = dash_axis_value_of(ys[i], ac.yaxiskind);
        const extra = (more || []).map(col => dash_axis_value_of(col[i], ac.yaxiskind));
        if (!isFinite(xv) || !isFinite(yv) || extra.some(v => !isFinite(v))) continue;
        out[names[0]].push(xv); out[names[1]].push(yv);
        for (let k = 0; k < extra.length; k++) out[names[2 + k]].push(extra[k]);
    }
    src.data = (ac.join) ? dash_join_rebuild(out, {x: names[0], y: names[1], style: ac.join.style, cmiss: "y"}, null) : out;
    src.change.emit();
}
// DASH_FIT_HELPERS_END
```
Note `np.std` is the population sd (divides by n): the qfit design above divides by `q.length`, not `q.length - 1`. (C) The branches, before the loop's closing `}`:
```js
    } else if (ac.type === 'lfit') {
        const n = fx.length;
        if (n < 2) { dash_fit_write(src, ac, [], [], null); continue; }
        const ww = dash_weight_norm(fw, ac.wtype, n);
        const xg = dash_fit_grid(fx, ac.n, ac.range);
        let lo = Infinity, hi = -Infinity; for (const v of fx) { if (v < lo) lo = v; if (v > hi) hi = v; }
        let yg;
        if (hi - lo === 0) { const m = dash_wmean(fy, ww); yg = xg.map(() => m); }
        else {
            const mu = dash_wmean(fx, ww);
            const fit = dash_wls(fx.map(v => [1, v - mu]), fy, fw, ac.wtype);
            if (fit === null) { dash_fit_write(src, ac, [], [], null); continue; }
            yg = xg.map(v => fit.beta[0] + fit.beta[1] * (v - mu));
        }
        dash_fit_write(src, ac, xg, yg, null);
    } else if (ac.type === 'qfit') {
        const n = fx.length;
        if (n < 2) { dash_fit_write(src, ac, [], [], null); continue; }
        const xg = dash_fit_grid(fx, ac.n, ac.range);
        const d = dash_qfit_design(fx, xg);
        const fit = dash_wls(d.X, fy, fw, ac.wtype);
        if (fit === null) { dash_fit_write(src, ac, [], [], null); continue; }
        const yg = d.Xg.map(r => { let s = 0; for (let j = 0; j < r.length; j++) s += r[j] * fit.beta[j]; return s; });
        dash_fit_write(src, ac, xg, yg, null);
    // DASH_FIT_BRANCHES_END
    }
```
map_lfit's unweighted `np.polyfit(x, y, 1)` and the weighted sqrt(w) polyfit are the same least squares as `dash_wls` on `[1, x - mu]` (D-10.c); `TestLfitBranch` holds it. (D) In test/js_runner.py add after `run_filter_js_block`:
```python
def run_fit_js_block(ac, x, y, w=None):
    """Run one fit branch of dash's REAL ``_FILTER_JS`` (WP-31 F1) on the
    kept rows *x*, *y* (Stata units) and weights *w*; return ``src.data``."""
    js = dr._FILTER_JS
    helpers = js[js.index("function dash_pctl"):
                js.index("// agg_sources is a Bokeh model list")]
    head = "} else if (ac.type === '%s') {" % ac["type"]
    lo = js.index(head) + len(head)
    nxt = js.find("} else if (ac.type === '", lo)
    end = js.index("// DASH_FIT_BRANCHES_END", lo)
    hi = nxt if (nxt != -1 and nxt < end) else end
    block = js[lo:hi]
    harness = (helpers + "\nconst ROW_ID = " + json.dumps(dr._ROW_ID_COLUMN)
               + ";\nconst ac = " + json.dumps(ac)
               + ";\nconst fx = " + json.dumps([float(v) for v in x])
               + ";\nconst fy = " + json.dumps([float(v) for v in y])
               + ";\nconst fw = " + (json.dumps([float(v) for v in w]) if w is not None else "null")
               + ";\nconst src = { data: null, change: { emit: () => {} } };"
               + "\nfor (let _i = 0; _i < 1; _i++) {\n" + block + "\n}"
               + "\nprocess.stdout.write(JSON.stringify(src.data));")
    return run_js(harness)


def run_fit_rows(ac, data):
    """``dash_fit_rows`` on a ``{column: list}`` *data* object."""
    js = dr._FILTER_JS
    helpers = js[js.index("function dash_pctl"):
                js.index("// agg_sources is a Bokeh model list")]
    return run_js(helpers + "\nconst d = JSON.parse(" + json.dumps(json.dumps(data))
                  + ");\nprocess.stdout.write(JSON.stringify(dash_fit_rows("
                  + json.dumps(ac) + ", d, (c) => c)));")
```
`dash_fit_write` uses `dash_own_col` and `dash_join_rebuild`, which are declared ABOVE `dash_pctl` in `_FILTER_JS` and so outside the helper slice: the harness must prepend them -- extend both runners' `helpers` with `js[js.index("function dash_own_col"):js.index("const ROW_ID = ")]` placed first. Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py test/test_saved_filter_layers.py test/test_filter_exclude.py test/test_histogram_edge_rule.py test/test_saved_stale_cue.py test/test_csp.py -q`.]]></action>
  <verify><![CDATA[All listed files are green except the `_FROZEN`-parametrised lfit/qfit nodes of test_saved_stale_cue.py (flipped in 10-04); `node -e "$(python3 -c "import dash_render as d; js=d._FILTER_JS; print(js[js.index('function dash_pctl'):js.index('// agg_sources')])"); console.log(dash_t_ppf(0.975, 10))"` prints 2.228138851986344; `grep -c "DASH_FIT_HELPERS_END\|DASH_FIT_BRANCHES_END" dash_render.py` prints 2.]]></verify>
  <done>The saved page's filter script refits lfit and qfit from the kept rows with the shared prelude and helpers, and js_runner runs any fit branch under node.</done>
</task>

<task type="auto" id="10-04">
  <name>Flip, certify, document and commit F1a</name>
  <files>test/test_saved_stale_cue.py, test/test_wp31_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[(1) Remove `"lfit", "qfit"` from `_FROZEN` (:58) and add the comment `# lfit and qfit are refitted by the saved page (WP-31 F1a); see _REFIT.`; update the docstring "The thirteen layers" to "The eleven layers". (2) Append TR-10.11's five entries to `MOVE_CORPUS` in test/test_mode_parity.py and change the comment at :2850 to `# lfit and qfit refit in both modes (WP-31 F1a); the others agree through the cue.` (3) Append the U10 truth block (Stata truth section) above `* ==== append new blocks above this line ====` in test/test_wp31_truth.cscript, helpers `_u10_move(sp, dp, widget_kind, value, out)` (python: DashRenderer + JsSession + json dump of the fit source) and `_u10_close(case, a_json, b_json, rtol)` above the header; run it with the two-line driver through `scripts/stata_slot.sh <scratch>/s10 <scratch>/run_test_wp31_truth.do` with `WP31_ONLY=S10` and `global dash_nobrowser 1`. (4) dash.sthlp TR-10.9 edits (the help, BUGS.md, GAPS3.md, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md and test_estimator_cost.py are the closing task's implied files, DECISIONS A13); grep test/ for `No; marked` and flip the pin in place with the new text. (5) Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "lfit or qfit or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q` (add the `TestTheJsTwinsAreBounded` class to test/test_estimator_cost.py in this task: 100,000 rows `rng.uniform(1000, 5000)` and a linear y with noise, `run_fit_js_block` for lfit and qfit, each under 2.0 s wall). (6) Close the BUGS.md F1a entry (Resolution form of BRIEF; names `GlyphMapper._fit_agg_config`, `_FILTER_JS` lfit/qfit branches, `_dash_stale_kind`, both renderers -- the served app refit already), rewrite the GAPS3 `F1a Tracked` line to `- **F1a Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (DECISIONS A11: the merger's step k.3b rewrites `pending` to the landed sha on s3-bugs; no amend, no quoted subject), replace the `<!-- WP-31 F1a -->` markers (Results that change: `lfit and qfit on a saved page after a filter move: the build's fit (marked "(unfiltered)") -> the fit on the kept rows (WP-31, F1a)`; Fixed in WP-31: one line), update TWOWAY_COVERAGE_AUDIT.md's row if it names the saved-page cue for lfit/qfit. grep the message for `claude|anthropic` (rule 6). Commit with the body of "Commit boundary".]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_statistical_helpers.py test/test_js_runner.py -q` ends `passed` with 0 failed; the slot log of the S10 block holds `U10-01 ok` .. `U10-05 ok` and no `FAIL`; `git log -1 --format=%s` prints the subject ending `(WP-31 F1a)`; `git show --stat --name-only --format= HEAD | grep -cE '^(test/test_js_fit_refit.py|dash_render.py|test/js_runner.py|test/test_saved_stale_cue.py|dash.sthlp|BUGS.md|GAPS3.md|CHANGELOG.md)$'` prints 8 (the commit also touches test/test_mode_parity.py, test/test_wp31_truth.cscript, test/test_estimator_cost.py, test/function_test_map.py and TWOWAY_COVERAGE_AUDIT.md); `grep -c "F1a Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>F1a is one green commit on wp31-s10: lfit and qfit refit on the saved page, the cue no longer marks them, the help says so, and the entry, Tracked line and marker are closed.</done>
</task>

## Section completion criteria

- The four tasks ran in order; 10-01's failure text opens the commit body.
- AC-10.1 to AC-10.5 hold; `test_js_fit_refit.py` has at least 45 nodes; no node skips under `DASH_STRICT=1`.
- `_FILTER_JS` holds the two markers `// DASH_FIT_HELPERS_END` and `// DASH_FIT_BRANCHES_END` exactly once each; `run_filter_js_block`'s six markers are unmoved.
- `_dash_stale_kind` returns None for lfit and qfit only (of the fit types); `_DASH_JS_REFIT_TYPES` is in the constants copy tuple.
- BUGS.md F1a closed; GAPS3 F1a Tracked rewritten; CHANGELOG markers replaced; help table and paragraph updated; one commit `(WP-31 F1a)`.

## Notes

- **Renderer order.** `_fit_agg_config` is a `GlyphMapper` method, copied whole into the served app (R2: no copy-list entry); `_DASH_JS_REFIT_TYPES` is a module constant and NEEDS the entry after `_DASH_STALE_STATUS_HTML` or `TestTheServedAppCarriesEveryName` fails at draw time in the app. The served app never reads `_dash_agg_config`; `_dash_redraw_for` refits by rebuilding the mapper's sources (research §4).
- **Marker discipline (R12, risk factor 1).** Never insert between `function dash_pctl` and `// Stata's kernels ([R] kdensity)` (the brush slice); never between `// ---- KPI recompute, shared by` and `dash_apply_kpis(new_data,`. Later JS sections (S13, S16, S19, S22, S25, S28, S29) insert helpers before `// DASH_FIT_HELPERS_END` and branches before `// DASH_FIT_BRANCHES_END`, and reuse `dash_solve` rather than redefining it (DECISIONS A19).
- **`dash_own_col`/`dash_join_rebuild` are above `dash_pctl`**: the node harnesses prepend `js[js.index("function dash_own_col"):js.index("const ROW_ID = ")]`.
- **numpy conventions in the twin.** `np.std` divides by n; `np.average(y, weights=w)` is `dash_wmean` with RAW weights (normalisation cancels); `_fit_grid`'s `linspace` end point is exact -- `dash_fit_grid` sets `out[k-1] = hi`.
- **Dates (D-10.d).** The histogram branch converts with `dash_stata_value_of`; `dash_axis_value_of` is its inverse for the output. `_axis_kind` returns the kind of the axis the LAYER draws on (`xaxis(2)`): record it, not the figure's primary kind.
- **Decisions for maintainer ratification.** D-10.c (normal equations in place of the SVD and the rank cut; parity at 1e-9 on nine designs, the near-singular cases listed in S13); D-10.f (the grid moves with the kept rows, as the served app's does).
- **Cscript hazards** (project memory): `cert_file_has` clobbers r(); globals drop across cscript; concurrent runs need `STATATMP=<dir>/`; `python_exec` may drop from `~/.stata19/console/stata19.rc` under many sessions -- re-check `c(python_exec)` before blaming the block.
- **Commit-body line forms**: as in "Commit boundary"; `Fixture: none` is written literally since no fixture is added. The GAPS3 Tracked line is written with `commit pending` (A11); the merger fills the sha at k.3b.
