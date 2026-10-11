# Section 28: fpfit and fpfitci refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1g · Risk: red · Batch: 9 · Depends on: 13 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U28

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): `fpfit` and `fpfitci` on a saved page keep the build's fractional-polynomial fit after a filter move, dimmed and keyed "(unfiltered)"; the served app refits (wrapped in `_dash_memo_wrap`, :35168). At `6370ca4` `map_fpfit` (dash_render.py:17684-17764) and `map_fpfitci` (:17765-17860) call `GlyphMapper._fp_fit(x, y, w, wtype)` (:17577-17628: `_fp_prepare`'s shift and scale :17389, the 36 power pairs `p1 <= p2` of `_FP_POWERS` :17378 through `_fp_screen` :17451 and `_dash_wls`, the smallest weighted rss), predict on `_fp_grid(x)` (:21007: the sorted distinct x, an even grid above `_FP_GRID_MAX` 20000) or `_fp_plot_grid` (:17630, weighted), and for fpfitci the `stdp` band with `_t_ppf` at `df = N - 3`; sources `x_fp, y_fp` and `x_fp, y_fp, y_lower, y_upper`. Neither tags; `_dash_stale_kind` gives `"fit"`. These are the last two of the eleven types (M16); after this section `_FROZEN` holds histogram and kdensity only and `_DASH_STALE_SUFFIX["fit"]` is unreachable from a spec dash writes.

**After this section** the saved page refits both: `fracpoly regress y x [w]` with degree 2 -- `shift = min positive spacing - min(x)` when `min(x) <= 0`, `scale = 10^(sign(log10 s) int|log10 s|)` with `s` the shifted range, the design `[1, h1, h2]` with `h = x^p` (`ln x` at p = 0) and `h2 = h1 ln x` for a repeated power, every pair fitted by `dash_wls` (S10) and the smallest rss kept -- predicted at the distinct kept x (or the weighted plot grid), the `stdp` band at `level()` with `dash_t_ppf(df)` (df >= 1, else a missing band). A constant y, fewer than two rows or one distinct x draw nothing (twoway: "fracpoly could not fit model"). The stale cue stops marking fpfit and fpfitci.

**Why these rows share this section (red).** The 36-pair search is the costliest estimator (2-7 s per 1e6 rows in Python before the screen); in JavaScript at 1e5 rows it is 36 weighted least squares of three columns with a Gram-Schmidt pass each -- about 1e8 operations, near M10's bound.

**Test order and commit rule.** One cycle, one commit `(WP-31 F1g)`: 28-01 failing tests; 28-02 tagging, helpers, branches; 28-03 flips (the last `_FROZEN` shrink, the stale-cue status text for fits), truth block, help, close, commit.

### Section decisions (binding on the executor)

- **D-28.a. No screen in JavaScript.** `_fp_screen` is an optimisation that is provably conservative (it never excludes the winner); the JS fits all 36 pairs in full with `dash_wls`. The winner is the same pair whenever the full-search rss ordering is the same, which `TestFpTwin::test_fixture_pairs` checks on the fixture's `fpfit`, `fpfit_repeated`, `fpfit_shift` records (the winning powers are recorded per dataset). Cost is bounded by TR-28.7's test; if 1e5 rows exceed 2 s under node, 28-02 adds a Gram-based rss screen in JS as a documented follow-up -- NOT silently.
- **D-28.b. Ties in rss keep the first pair in search order** (`fit["rss"] < best["rss"]` strict), as Python.
- **D-28.c. The weighted plot grid** (`_fp_plot_grid`: the plot's rows with x and y non-missing, whatever the weight, sorted by (x, y), distinct x whose FIRST row is in the estimation sample) needs the rows `dash_fit_rows` dropped for a missing or non-positive weight. The branch re-reads x and y with a config copy whose `wvar` is null (`dash_fit_rows(Object.assign({}, ac, {wvar: null}), _ac_data, _pick)`) when `ac.wvar` is set, and applies the rule in `dash_fp_plot_grid`. Unweighted, the grid is `dash_fp_grid` (distinct sorted x; above `max_grid` = `_FP_GRID_MAX` an even grid).
- **D-28.d. Date x.** `_fp_prepare` and the powers run on Stata units (as Python); the shift/scale are recomputed from the kept rows every move.

## Risk: [red] -- the heaviest port, a 36-fold least squares per move

**Why.** A browser's main thread blocks while the search runs; a transcription error in the design for a repeated power (`h2 = h1 ln x`) changes the winner silently.

**Risk factors.** (1) Cost at 1e5 rows. (2) The repeated-pair design and the p = 0 log. (3) The weighted plot grid's first-row rule. (4) Batch partners S26 (map_contour + registration) and S27 (title placement) do not touch these mappers.

**Mitigation.** (1) `dash_wls` is called with `X` as rows; the Gram-Schmidt pass is the cost -- `dash_fp_fit` builds `lnx` and each power column ONCE (eight columns plus eight `h ln x` columns) and reuses them across pairs. (2) `TestFpTwin::test_fixture_pairs` and `::test_repeated_pair_design`. (3) `::test_weighted_plot_grid` against `_fp_plot_grid` on nlsw88's `[aw=hours]` case (1543 of 1544). (4) Boundaries.

## Dependencies

- **Depends on: 13** (`dash_ci_write`, the ci branch pattern) and through it S10 (`dash_wls`, `dash_fitci_se`, `dash_t_ppf`, `dash_fit_rows`, `dash_fit_write`, `run_fit_js_block`).
- **Blocks: none.**
- **Parallel batch: 9** with S26 and S27; merge order 28, 26, 27. S28 is batch 9's `_FILTER_JS` editor.

## Evidence

- `map_fpfit` :17684-17764: `_layer_units`; `_fp_report_unsupported`; `fit = self._fp_fit(x, y, w, wtype) if len(x) >= 2 else None`; None -> empty, `_mark_unfit` when `len(x) < 2`; `x_grid = _fp_grid(x)`, weighted: `x_all, y_all = self._masked(source, view, xvar, yvar, units=...)`, `x_grid = self._fp_plot_grid(x_all, y_all, x, y)`; `y_fit = self._predict_fp2(x_grid, fit)`; `valid`; `_on_axis`; source `x_fp, y_fp`; recast.
- `map_fpfitci` :17765-17860: the same, then `se_fit = self._fp_stdp(x_grid, fit)` (`_dash_fitci_se(Xg, fit, "stdp")`), `t_crit = _t_ppf(0.5 + level/200, df=fit["df"]) if fit["df"] >= 1 else nan`; source `x_fp, y_fp, y_lower, y_upper`.
- `_fp_prepare` :17389-17422; `_fp_design` :17424-17449; `_fp_fit` :17577-17628 (constant y -> None; `scale <= 0` -> None; non-finite design skipped; `LinAlgError` skipped; non-finite rss skipped); `_fp_plot_grid` :17630-17675; `_predict_fp2` :17677; `_fp_stdp` :17680; `_fp_grid` :21007-21040; `_FP_GRID_MAX` :385; `_FP_POWERS` :17378.
- Fixtures: `stat_truth.json` `fpfit` (per dataset: `fit_x`, `fit`, the winning powers in `fp_powers`), `fpfit_repeated`, `fpfit_repeated_data`, `fpfit_repeated_pairs_found`, `fpfit_shift`, `fpfit_shift_curve`, `fpfit_shift_rule_check`, `ci_bands` (fpfitci), `weighted`.
- `test_estimator_cost.py::TestFpfitFitsWhatItFitted` (:194) pins the screened search against `_old_fp_fit` (:83, the full search).
- Pins to flip: `_FROZEN` holds `"fpfit"`, `"fpfitci"`; `test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` (re-pointed to fpfitci by S13) -- now no ci layer is frozen: the test is flipped to a kdensity-over-default-grid check of the "grid" kind on both renderers? No -- kdensity has one renderer. Flip it to assert that NO ci layer (lfitci, qfitci, fpfitci, lpolyci) is dimmed after a move (a guard of M16's completion), keeping its name; `TestTheStaleKind::test_each_type` (:620) iterates `fits = [t for t in _FROZEN if t not in ("histogram", "kdensity")]` -- empty after this section; add an explicit assertion that every member of `_DASH_JS_REFIT_TYPES` returns None and that the set equals the eleven types.

## User stories

- **US-28.1** As a reader of the saved file, I want the fractional-polynomial fit and its band to follow the filter.
- **US-28.2** As a Stata user, I want the saved page to refit every fitted line twoway draws, so that no "(unfiltered)" mark remains on a fit.

## Business requirements

- **BR-28.1** After a move the saved fpfit/fpfitci equal the served app's to 1e-8 relative (the same winning powers).
- **BR-28.2** A constant y, fewer than two rows or one distinct x draw nothing; `df < 1` draws the fit and no band.
- **BR-28.3** No fit type is marked "(unfiltered)" on a saved page; only a histogram's bins and a density's grid are marked.
- **BR-28.4** The help's table says "Yes" for fit-line recompute on the saved page.

## Technical requirements

- **TR-28.1 Tagging.** `map_fpfit`: on the empty return and the drawn return (not recast): `_dash_agg_source = fp_src`, `_dash_agg_config = dict(self._fit_agg_config("fpfit", xvar, yvar, wtype, w, fig, options, ["x_fp", "y_fp"], _FIT_GRID, None), powers=[float(p) for p in self._FP_POWERS], max_grid=int(_FP_GRID_MAX))`, `_dash_agg_rows`. `map_fpfitci`: the LINE renderer (as S13) with `["x_fp", "y_fp", "y_lower", "y_upper"]`, `powers`, `max_grid`, `level=float(_resolve_level(options, self.default_level))`, `std="stdp"`.
- **TR-28.2** `_DASH_JS_REFIT_TYPES` gains `"fpfit", "fpfitci"` and now equals `_DASH_COMPUTED_ONLY_TYPES - {"histogram", "kdensity"}`; add a module-level assertion comment (not an `assert`: the served app copies constants) and the test `TestStaleKind::test_every_fit_type_is_refit`.
- **TR-28.3 Helpers** before `// DASH_FIT_HELPERS_END`:
  ```js
  // ---- fpfit / fpfitci (S28): fracpoly regress y x, degree 2.
  // _fp_prepare: {shift, scale}; scale 0 when x does not vary.
  function dash_fp_prepare(x) {
      let mn = Infinity, mx = -Infinity; for (const v of x) { if (v < mn) mn = v; if (v > mx) mx = v; }
      let shift = 0;
      if (mn <= 0) { const s = x.slice().sort((a, b) => a - b); let d = Infinity; for (let i = 1; i < s.length; i++) { const g = s[i] - s[i - 1]; if (g > 0 && g < d) d = g; } if (!isFinite(d)) return {shift: 0, scale: 0}; shift = d - mn; }
      const range = (mx + shift) - (mn + shift);
      if (!(range > 0)) return {shift, scale: 0};
      const l10 = Math.log10(range);
      return {shift, scale: Math.pow(10, Math.sign(l10) * Math.trunc(Math.abs(l10)))};
  }
  // _fp_design on prepared x: [1, h1, h2], h = xx^p (ln xx at p 0), h2 = h1 ln xx for a repeated power.
  function dash_fp_design(xx, p1, p2) {
      return xx.map(v => { const l = Math.log(v); const h1 = p1 === 0 ? l : Math.pow(v, p1); const h2 = (p1 === p2) ? h1 * l : (p2 === 0 ? l : Math.pow(v, p2)); return [1, h1, h2]; });
  }
  // _fp_fit without the screen (D-28.a): every pair p1 <= p2, the smallest
  // weighted rss; null when y is constant, x does not vary, or no pair fits.
  function dash_fp_fit(x, y, w, wtype, powers) {
      const n = x.length; if (n < 2) return null;
      let ymin = Infinity, ymax = -Infinity; for (const v of y) { if (v < ymin) ymin = v; if (v > ymax) ymax = v; }
      if (!(ymax - ymin > 0)) return null;
      const pr = dash_fp_prepare(x); if (!(pr.scale > 0)) return null;
      const xx = x.map(v => (v + pr.shift) / pr.scale);
      const lnx = xx.map(Math.log);
      const col = {}; for (const p of powers) col[p] = (p === 0) ? lnx : xx.map(v => Math.pow(v, p));
      let best = null;
      for (let i = 0; i < powers.length; i++) for (let j = i; j < powers.length; j++) {
          const p1 = powers[i], p2 = powers[j];
          const h1 = col[p1]; const h2 = (p1 === p2) ? h1.map((v, k) => v * lnx[k]) : col[p2];
          let ok = true; for (let k = 0; k < n && ok; k++) if (!isFinite(h1[k]) || !isFinite(h2[k])) ok = false;
          if (!ok) continue;
          const X = new Array(n); for (let k = 0; k < n; k++) X[k] = [1, h1[k], h2[k]];
          const fit = dash_wls(X, y, w, wtype);
          if (fit === null || !isFinite(fit.rss)) continue;
          if (best === null || fit.rss < best.rss) best = Object.assign(fit, {p1, p2, shift: pr.shift, scale: pr.scale});
      }
      return best;
  }
  // _fp_grid: sorted distinct x; an even grid of maxGrid points above it.
  function dash_fp_grid(x, maxGrid) {
      const u = Array.from(new Set(x)).sort((a, b) => a - b);
      if (u.length === 0) return [1e-6, 1];
      if (u.length === 1) return [u[0]];
      if (u.length > maxGrid) return dash_linspace(u[0], u[u.length - 1], maxGrid);
      return u;
  }
  // _fp_plot_grid: the distinct x of ALL plot rows whose first row in (x, y)
  // order is in the estimation sample.
  function dash_fp_plot_grid(xAll, yAll, xEst, yEst, maxGrid) {
      if (xAll.length === xEst.length) return dash_fp_grid(xEst, maxGrid);
      const firstMin = (xs, ys) => { const o = xs.map((v, i) => i).sort((a, b) => (xs[a] - xs[b]) || (ys[a] - ys[b])); const m = new Map(); for (const i of o) if (!m.has(xs[i])) m.set(xs[i], ys[i]); return m; };
      const all = firstMin(xAll, yAll), est = firstMin(xEst, yEst);
      const grid = []; for (const [xv, yv] of all) if (est.has(xv) && est.get(xv) === yv) grid.push(xv);
      grid.sort((a, b) => a - b);
      if (grid.length > maxGrid) return dash_linspace(grid[0], grid[grid.length - 1], maxGrid);
      return grid;
  }
  function dash_fp_predict(xg, fit) { const xx = xg.map(v => (v + fit.shift) / fit.scale); return {Xg: dash_fp_design(xx, fit.p1, fit.p2)}; }
  ```
  (`dash_linspace` is S19's; `_fp_grid`'s empty case `[1e-6, 1]` is unreachable after the `n < 2` guard but kept for parity.)
- **TR-28.4 Branches** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'fpfit' || ac.type === 'fpfitci') {
          const isci = ac.type === 'fpfitci';
          const empty = () => isci ? dash_ci_write(src, ac, [], [], [], []) : dash_fit_write(src, ac, [], [], null);
          const fit = dash_fp_fit(fx, fy, fw, ac.wtype, ac.powers);
          if (fit === null) { empty(); continue; }
          let xg;
          if (ac.wvar) { const all = dash_fit_rows(Object.assign({}, ac, {wvar: null}), _ac_data, _pick); xg = all ? dash_fp_plot_grid(all.x, all.y, fx, fy, ac.max_grid) : dash_fp_grid(fx, ac.max_grid); }
          else xg = dash_fp_grid(fx, ac.max_grid);
          const P = dash_fp_predict(xg, fit);
          const yg = P.Xg.map(r => { let s = 0; for (let j = 0; j < 3; j++) s += r[j] * fit.beta[j]; return s; });
          if (!isci) {
              const kx = [], ky = []; for (let i = 0; i < xg.length; i++) if (isFinite(yg[i])) { kx.push(xg[i]); ky.push(yg[i]); }
              dash_fit_write(src, ac, kx, ky, null); continue;
          }
          const se = dash_fitci_se(P.Xg, fit, "stdp");
          const t = (fit.df >= 1) ? dash_t_ppf(0.5 + ac.level / 200, fit.df) : NaN;
          dash_ci_write(src, ac, xg, yg, yg.map((v, i) => v - t * se[i]), yg.map((v, i) => v + t * se[i]));
  ```
  `dash_ci_write` drops rows where y is not finite (matching `valid`).
- **TR-28.5 Flips**: `_FROZEN` becomes `["histogram", "kdensity"]`; `_REFIT` the eleven; :226's test (ci layers) asserts none dimmed; `TestTheStaleKind::test_each_type` gains the TR-28.2 assertion; the module docstring of test_saved_stale_cue.py says "the two layers".
- **TR-28.6 Help**: dash.sthlp:1946 becomes `{col 5}Fit-line recompute on filter{col 38}Yes{col 59}Yes`; the paragraph at :1962-1980 is rewritten: "...and keeps the bin edges and the grid chosen when the dashboard was built, so neither moves as you filter; it refits every fitted or smoothed line ({cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}, {cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci}, {cmd:mband}, {cmd:mspline}) from the rows that pass the filter, with the notes above on lowess's operation cap and lpoly's exact-fit bandwidth. When a move removes observations a histogram's bins or a density's grid was computed from, the page marks the layer: ... "(bins unfiltered)" or "(grid unfiltered)"..." -- remove "(unfiltered)" from the list of marks; `_DASH_STALE_STATUS_HTML` (:1904) loses `(unfiltered), ` so it reads `Layers marked (bins unfiltered) or (grid unfiltered) were computed before the filter...`; `_DASH_STALE_SUFFIX` keeps its `"fit"` key (a hand-written spec with an unknown computed type could still reach `_dash_stale_kind`? No: `_DASH_COMPUTED_ONLY_TYPES` is closed; keep the key, document it dormant). `test_stale_cue_browser.py:177` reads the constant's text: re-run it.
- **TR-28.7 Timing**: `TestTheJsTwinsAreBounded::test_fpfit_and_fpfitci_under_node_on_1e5_rows` under 2 s each (x uniform 1-100, y = ln x + noise). If red, D-28.a's follow-up applies: port `_fp_screen`'s centred 2x2 rss screen (its arithmetic at :17451-17575) as `dash_fp_screen` and fit only the vouched pairs; the section then records the port in its commit body.
- **TR-28.8 Parity corpus**: `_move_case("fpfit, dropdown", _MOVES[0], [_sc(), plot_for("fpfit")])`, `_move_case("fpfitci level(90), range", _MOVES[1], [_sc(), plot_for("fpfitci", {"level": "90"})])`, `_move_case("fpfit [aw=weight] (plot grid rule), slider", _MOVES[2], [plot_for("fpfit", {"weight": "aweight", "wexp": "weight"})])`, `_move_case("fpfitci [fw=rep], dropdown", _MOVES[0], [plot_for("fpfitci", {"weight": "fweight", "wexp": "rep"})])`, `_move_case("fpfit on an x with non-positive values, range", _MOVES[1], [plot_for("fpfit", yvar="mpg", xvar="shifted")])` -- only if `_DF` has such a column; else `TestFpBranch::test_shifted_x` covers it.

## Boundaries

Do not edit `_fp_fit`, `_fp_screen`, `_fp_prepare`, `_fp_design`, `_fp_plot_grid`, `_fp_grid`, `_fp_report_unsupported` in Python, `_dash_memo_wrap`, the served template, S26's `map_contour` and registration, S27's title placement, `_BRUSH_JS`.

## Stata truth

No new extractor (`stat_truth.json` `fpfit*` and `ci_bands` pin the Python twin). Truth block `* ==== S28 F1g: fpfit and fpfitci ====`, helpers `_u28_*`:
- **U28-01** `sysuse auto; dash scatter mpg weight || fpfit mpg weight, filter(foreign, type(dropdown))`; saved moved to Foreign; `twoway fpfit mpg weight if foreign == 1` serset x/y versus the saved `(x_fp, y_fp)` at 1e-6 relative; and `fracpoly regress mpg weight if foreign == 1` -> `e(fp_k1)`, `e(fp_k2)`... (the chosen powers: `fp` in Stata 19 reports `e(fp_terms)`; read whichever the installed `fracpoly`/`fp` returns and cite it) equal the JS winner (exposed by `TestFpTwin`, not the cscript -- the cscript compares the curve).
- **U28-02** `fpfitci mpg weight, level(90)` with the price range to 4500-11385 versus `twoway fpfitci ... if inrange(price,4500,11385), level(90)` serset (line, lower, upper).
- **U28-03** `fpfit mpg weight [aw=displacement]` dropdown to Domestic versus `twoway fpfit mpg weight [aw=displacement] if foreign == 0`.
- **U28-04** `webuse nlsw88; dash fpfit wage ttl_exp [aw=hours], filter(union, type(dropdown))` moved to one value: the saved point count equals twoway's serset count under the same `if` (the first-row rule on the subset).
- **U28-05** a move leaving three rows (fpfitci): the saved line has three points and NaN band (df 0); twoway on the same `if` draws the fit with missing limits (serset).

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended under `# ---- WP-31 F1g: fpfit and fpfitci ----`)

- Test: tagging with `powers`, `max_grid` (fpfitci: `level`, `std`) -- `TestTheConfig::test_fpfit_config_keys`, `::test_fpfitci_config_keys`, `::test_fp_empty_layer_is_tagged`.
- Test: `_dash_stale_kind` None for both; `_DASH_JS_REFIT_TYPES == _DASH_COMPUTED_ONLY_TYPES - {histogram, kdensity}` -- `TestStaleKind::test_fpfit_and_fpfitci_are_refit`, `::test_every_fit_type_is_refit`.
- Test: `dash_fp_prepare` equals `_fp_prepare` on auto weight, census pop, a shifted x (min <= 0), a constant x -- `TestFpTwin::test_prepare[case]`; `dash_fp_design` for (0, 0), (-2, -2), (1, 3), (0, .5) -- `::test_repeated_pair_design`; `dash_fp_fit` picks the fixture's winning powers and matches `_fp_fit`'s beta/rss/df on `fpfit`, `fpfit_repeated_data`, `fpfit_shift` records -- `::test_fixture_pairs[case]`; `dash_fp_plot_grid` equals `_fp_plot_grid` on nlsw88 `[aw=hours]` (1543 points) -- `::test_weighted_plot_grid`.
- Test: the branches equal the mappers' sources for: default, aw (plot grid), fw, pw, shifted x, constant y (empty), one row (empty), three rows fpfitci (NaN band), level(90) -- `TestFpBranch::test_fpfit_matches_python[case]`, `::test_fpfitci_matches_python[case]`.
- Test: saved equals served after every `_MOVES` -- `TestTheSavedPageRefits::test_saved_equals_served[fpfit|fpfitci-move]`.
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked[fpfit|fpfitci-*]`; `::TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked` flipped to "no ci layer is dimmed".
- Test: `_DASH_STALE_STATUS_HTML` no longer says "(unfiltered)" and the help table says Yes -- `TestTheCueText::test_only_bins_and_grid_are_named` (in test_saved_stale_cue.py).

### Cases in cscripts

- `test_wp31_truth.cscript` U28-01..U28-05.

### Flips

- `_FROZEN` -> `["histogram", "kdensity"]`; :226 flipped; `TestTheStaleKind::test_each_type` extended; `test_stale_cue_browser.py` re-run (reads the constant).

### Parity corpus

TR-28.8's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tagging; the closed set | pytest `TestTheConfig`, `TestStaleKind` | -- | saved |
| Prepare, design, search, grids | node `TestFpTwin` | `stat_truth.json` `fpfit*`, `datasets`, `weighted_data` | n/a |
| Branches; saved vs served | node `TestFpBranch`; `TestTheSavedPageRefits`; `MOVE_CORPUS` | `ci_bands` sanity | yes |
| Cue text and help | `TestTheCueText`, test_help_conformance, test_stale_cue_browser | -- | saved |
| Stata truth | U28-01..05 | live | saved vs twoway sersets |
| Cost | `TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-28.1** The JS search picks the same powers as `_fp_fit` on every fixture record; beta to 1e-9, the band to 1e-8.
- **AC-28.2** Saved equals served after every corpus move.
- **AC-28.3** `_FROZEN` is histogram and kdensity; no fit is marked; the status text names bins and grid only; the help table says Yes.
- **AC-28.4** U28-01..05 pass; 1e5-row fpfit and fpfitci under 2 s each under node (or the screen port is recorded).

## Tasks

**Commit boundary.** 28-01 to 28-03 form the F1g commit, subject `Refit fpfit and fpfitci on the saved page, completing the estimator ports (WP-31 F1g)`, on `wp31-s28`. Body as the S10 form with `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[fpfit-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U28-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- fpfit and fpfitci were frozen because the page did not refit them (F1g)`; `Flipped: test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked -- no ci layer is frozen once every estimator is ported (F1g)`; `Fixture: none`; `BUGS.md: "<F1g title>" (closed)`; `GAPS3: F1g Tracked`; and the line `Retires decision WP-29 M3 (DISCOVERY Q27).`

<task type="auto" id="28-01">
  <name>Write the failing fpfit refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the stubs under `# ---- WP-31 F1g: fpfit and fpfitci ----`. `TestFpTwin::test_fixture_pairs` reads `stat_truth.json` `fp_powers` (the winning pair per dataset; read the record shape first) and `datasets`, runs `dash_fp_fit(x, y, null, null, [-2,-1,-0.5,0,0.5,1,2,3])` under node and asserts `(p1, p2)` equal the fixture's and `GM._fp_fit(x, y)`'s, `beta` to 1e-9, `df` exactly. `test_weighted_plot_grid` builds nlsw88-like data from the fixture's `weighted_data` if it holds the hours case, else from a synthetic frame with a missing weight on the lowest-y row of one x (the docstring's rule) and compares `dash_fp_plot_grid` with `GM._fp_plot_grid`. Add `TestTheCueText::test_only_bins_and_grid_are_named` to test_saved_stale_cue.py (asserts `"(unfiltered)" not in dr._DASH_STALE_STATUS_HTML` and `dr._DASH_JS_REFIT_TYPES == dr._DASH_COMPUTED_ONLY_TYPES - {"histogram", "kdensity"}`). Extend `_REFIT` with `"fpfit", "fpfitci"`. Run `python3 -m pytest test/test_js_fit_refit.py -k "fpfit or Fp" test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked test/test_saved_stale_cue.py::TestTheCueText -q -n0 2>&1 | tee <scratch>/28-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/28-01-failure.txt is at least 20; nothing staged.]]></verify>
  <done>Every F1g regression test exists and fails at the batch-9 base with the text saved.</done>
</task>

<task type="auto" id="28-02">
  <name>Tag fpfit and fpfitci and add their JS twins</name>
  <files>dash_render.py, test/test_estimator_cost.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES` gains `"fpfit", "fpfitci"` with the comment `# Equals _DASH_COMPUTED_ONLY_TYPES less histogram and kdensity (M16 complete).`; `_DASH_STALE_STATUS_HTML` loses `(unfiltered), ` (TR-28.6). (2) `map_fpfit` (:17684) and `map_fpfitci` (:17765): build `_cfg` per TR-28.1 before the `fit is None` return and attach on the empty and drawn returns (fpfitci: the LINE renderer). (3) Insert TR-28.3's helpers before `// DASH_FIT_HELPERS_END` and TR-28.4's branch before `// DASH_FIT_BRANCHES_END`. (4) Add `test_fpfit_and_fpfitci_under_node_on_1e5_rows` to `TestTheJsTwinsAreBounded` and run it alone first: `python3 -m pytest test/test_estimator_cost.py::TestTheJsTwinsAreBounded -k fpfit -q -n0`. If it exceeds 2 s, port `_fp_screen` (:17451-17575) as `dash_fp_screen(xx, y, w, wtype, powers)` returning the set of `"p1|p2"` keys to fit (the same thresholds `_FP_SCREEN_MARGIN` 1e-9 and `_FP_SCREEN_COND` 1e6, a 3x3 singular-value check replaced by the condition `cbb*(1-r^2) > 1e-12*rawb` alone -- document the omission), call it in `dash_fp_fit` and re-run. Then `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_estimator_cost.py::TestFpfitFitsWhatItFitted test/test_saved_stale_cue.py test/test_stale_cue_browser.py -q`.]]></action>
  <verify><![CDATA[Green except the `_FROZEN` fpfit/fpfitci nodes and :226 (flipped in 28-03); `python3 -c "import dash_render as d; print(d._DASH_JS_REFIT_TYPES == d._DASH_COMPUTED_ONLY_TYPES - {'histogram','kdensity'}, '(unfiltered)' in d._DASH_STALE_STATUS_HTML)"` prints `True False`.]]></verify>
  <done>The saved page refits fpfit and fpfitci from the kept rows; every one of the eleven estimators now has a JavaScript twin.</done>
</task>

<task type="auto" id="28-03">
  <name>Flip, certify, document and commit F1g</name>
  <files>test/test_saved_stale_cue.py, test/test_wp31_truth.cscript, dash.sthlp</files>
  <action><![CDATA[`_FROZEN = ["histogram", "kdensity"]` with the docstring "The two layers a saved page computes at build and marks: the bins and the grid are the build's; every fit is refitted (WP-31 F1a-F1g)"; flip :226 to assert no ci layer (lfitci, qfitci, lpolyci, fpfitci) is dimmed after a move; extend `TestTheStaleKind::test_each_type` with the TR-28.2 assertion. Append TR-28.8's `MOVE_CORPUS` entries under `# WP-31 F1g: fpfit and fpfitci refit on the saved page`. Append the U28 block (helpers `_u28_move`, `_u28_serset`) above the marker line; run `WP31_ONLY=S28 scripts/stata_slot.sh <scratch>/s28 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-28.6 (the table line and the paragraph rewrite) and the conformance pin. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_stale_cue_browser.py test/test_mode_parity.py -k "fpfit or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1g (Resolution names the two mappers, `dash_fp_*`, the status text change, "retires WP-29 M3"); rewrite the GAPS3 F1g Tracked line and ADD under GAPS3 §9 the sentence `F1 (all parts): closed in WP-31 sections 10, 13, 16, 19, 22, 25, 28; residual: the lpoly/lpolyci exact-fit bandwidth (BUGS.md "lpoly's and lpolyci's default bandwidth on an exactly fitted y...")` as a plain line after the F1g Tracked line (the reader ignores lines not in the Tracked form); replace the `<!-- WP-31 F1g -->` markers (Results: `fpfit and fpfitci on a saved page after a filter move: the build's fit (marked) -> fracpoly's degree-2 fit on the kept rows and its stdp band (WP-31, F1g)`; Changed behaviour: `A saved page no longer marks any fitted line "(unfiltered)"; only a histogram's bins and a density's grid are marked (WP-31, F1g)`); update TWOWAY_COVERAGE_AUDIT.md's saved-page note if one names the cue for fits. Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; slot log `U28-01 ok`..`U28-05 ok`; `git log -1 --format=%s` ends `(WP-31 F1g)`; `python3 -c "import test.test_saved_stale_cue as t; print(t._FROZEN)"` (run from the repo root with `PYTHONPATH=test`) prints `['histogram', 'kdensity']`; `grep -c "No; marked" dash.sthlp` prints 0.]]></verify>
  <done>F1g is one green commit: fpfit and fpfitci refit on the saved page, every fit type is refitted, and the cue, help and tracking say so.</done>
</task>

## Section completion criteria

- AC-28.1 to AC-28.4; `_DASH_JS_REFIT_TYPES` equals the eleven types; `_FROZEN` is the two; `_DASH_STALE_STATUS_HTML` names bins and grid only; the markers intact.
- BUGS.md F1g closed; GAPS3 F1g Tracked rewritten and the F1 summary line added; markers replaced; help rewritten; one commit; WP-29 M3 retired in the body.

## Notes

- **Renderer order.** The served app refits through `_dash_redraw_for` with `_dash_memo_wrap(fpfit)`; the saved page has no memo (each move recomputes; a dropdown toggled back and forth recomputes twice -- acceptable at the measured cost; a `Map` memo keyed by the kept row ids is a possible follow-up, not in scope).
- **Decisions for maintainer ratification.** D-28.a (no screen unless the timing test demands it), D-28.c (the weighted plot grid's second read of the rows).
- **R12.** S28 is batch 9's only `_FILTER_JS` editor; S26 registers a new type (contour) and S27 edits title placement.
- **S29 (js-contour) follows in batch 10** and uses `dash_solve` on an (n+3) system; it adds `"contour", "contourline"` to `_DASH_JS_REFIT_TYPES` and `_DASH_COMPUTED_ONLY_TYPES` together, with the cap rule of index A8 -- after S26 registers the types. `_DASH_STALE_SUFFIX["fit"]` stays for S29's above-the-cap contour (index A8: "tags the layer frozen on the saved page"), so the `"fit"` key is NOT removed here and TR-28.6's status text must be re-widened by S29 to name its cue; note this in S29's hand-off.
- **Cscript**: `twoway fpfit`'s serset x is the distinct x of the sample; `fracpoly`/`fp` for the chosen powers is informational -- the block compares curves.
