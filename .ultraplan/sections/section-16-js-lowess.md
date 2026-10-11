# Section 16: lowess refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1c · Risk: yellow · Batch: 4 · Depends on: 10 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U16

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): `lowess` on a saved page keeps the build's smooth after a filter move, dimmed and keyed "(unfiltered)"; the served app re-smooths the kept rows. At `6370ca4` `map_lowess` (dash_render.py:16655-16800) computes `GlyphMapper._stata_lowess(x, y, bw, mean, noweight)` (:16801-16920), applies `adjust` and `logit`, drops missing values and writes `ColumnDataSource({"x_lw", "y_lw"})`; it tags nothing. `_dash_stale_kind("lowess")` is `"fit"`.

**After this section** the saved page re-smooths lowess from the kept rows with Stata's own algorithm as the Python twin reproduces it (test/fixtures/stat_truth.json `lowess`, `lowess_more`, `lowess_full_resolution_check`: 1.5e-10 absolute on every probe): a STABLE sort by x, `k = int((N*bw - .5)/2)`, the index-symmetric window `max(0, i-k)..min(N-1, i+k)`, `Delta = 1.0001 * max|x_j - x_i|` from the window's ends, tricube weights `(1 - (d/Delta)^3)^3` (unit under `noweight`), the weighted least-squares line through the window at `x_i` (or the weighted mean under `mean`), missing where the window has no x spread, then `adjust` (multiply by `mean(y over every observation in memory) / mean(smooth)`) and `logit` (clamp to `[1/N, 1-1/N]`, missing becomes `1-1/N`, then `ln(s/(1-s))`), the finite values drawn. Fewer than three rows, or an x range under 1e-30, draw nothing. The stale cue stops marking lowess.

**Why this row is its own section.** lowess is the one estimator that is neither a regression nor a kernel smoother; its loop is O(N·window) and the only cost risk among the simple ports (M10).

**Test order and commit rule.** One cycle, one commit `(WP-31 F1c)`: 16-01 failing tests; 16-02 tagging, the JS helper and branch, `_DASH_JS_REFIT_TYPES`; 16-03 flips, truth block, help, close, commit.

### Section decisions (binding on the executor)

- **D-16.a. `adjust`'s numerator is a build-time scalar.** Stata's `summ y, mean` with no `if` runs over EVERY observation in memory (map_lowess :16738-16760), so the mean does not change with a filter; the config carries `y_all_mean` (float, NaN when none is finite) and the JS reuses it. The served app's `_dash_redraw_for` passes the mapper's `dataset`, so it does the same.
- **D-16.b. Ties keep dataset order.** The JS sort is `order.sort((a, b) => fx[a] - fx[b] || a - b)` -- a stable sort on the kept rows in their data order, which is the dataset order filtered (the source's rows are in dataset order; `dash_fit_rows` keeps that order; `member_ids` picks preserve it).
- **D-16.c. `k` uses `Math.trunc`**, as Python's `int()` truncates toward zero; for `N*bw - .5 < 0` (N = 1 with a small bw) `k` is 0 -- unreachable here because N >= 3 and bw > 0 give `N*bw - .5 > -0.5`, truncating to 0 at worst.
- **D-16.d. The window arithmetic is a direct transcription of the LOOP, not of the vectorised numpy** (:16864-16919): one pass per observation computing `sw`, `ym`, `xm`, `sxx`, `b`. Agreement with Python is 1e-12 relative (the numpy version differs from the loop by under 1e-12, per its own comment), so the parity tolerance is `rtol=1e-9, atol=1e-10`.

## Risk: [yellow] -- an O(N·window) loop in the browser on every move

**Why.** At N = 100,000 with bw .8 the window is 80,000 rows: 8e9 operations is far beyond 2 s. Python takes 0.3 s at N = 10,000 and would take minutes at 1e5; the served app wraps lowess in `_dash_memo_wrap` (:35168) but still pays the first draw.

**Risk factors.** (1) M10's 2 s bound at 100,000 rows cannot be met by Stata's own algorithm at default bandwidth in JavaScript or in Python (`test_lowess_on_ten_thousand_rows` allows 20 s for 1e4). (2) A long-running CustomJS blocks the page's main thread.

**Mitigation.** (1) The timing test for lowess is written at N = 10,000 (under 2 s under node; measured expectation about 0.6 s) and the 100,000-row bound is recorded as a documented divergence from M10 for lowess ONLY, with the reason (twoway's algorithm is O(N²) at fixed bw) -- raised for ratification (Notes). (2) The JS branch skips the refit and leaves the layer EMPTY with the stale cue's status text when `N * (2k+1) > _DASH_LOWESS_JS_MAX_OPS` (module constant 2e8, carried in the config as `max_ops`); the served app has no such bound. Reported for ratification as D-16.e.

- **D-16.e. Operation cap.** `_DASH_LOWESS_JS_MAX_OPS = 2e8` (a module constant, copy-list entry after `_DASH_JS_REFIT_TYPES`); the config carries it as `max_ops`; above it the branch writes empty columns and sets `src._dash_capped = true` (a plain JS property the status block does not read -- the visible cue is the empty line; the help names the cap). Measured: 2e8 multiply-adds take about 0.5 s under node.

## Dependencies

- **Depends on: 10.** `dash_fit_rows` (lowess has no weight: `wvar` null), `dash_fit_write`, `run_fit_js_block`, `_DASH_JS_REFIT_TYPES`, `_fit_agg_config`.
- **Blocks: none.**
- **Parallel batch: 4** with S11 (fit options: `map_lfit`..`map_fpfitci`, `map_lpolyci`, `_render_ci_band`, `_make_figure_body`) and S12 (histogram/kdensity/function/area/bar mappers). Merge order 16, 11, 12. **Can run with S11 and S12**: neither edits `map_lowess`, `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind` or `test_saved_stale_cue.py`; S16 is batch 4's editor of those (A2; DECISIONS A22 swapped S13 and S16 so S13's `map_lfitci`/`map_qfitci` edits do not share S11's batch). As batch 4's `_FILTER_JS` owner S16 also reads the config keys its partners write: S12's `gap`, `baroffset`, `area` in the histogram and kdensity branches (TR-16.10) and S11's `atobs` in `dash_fit_grid` (TR-16.11); every read is default-safe when the key is absent, so the three worktrees merge in any order.

## Evidence

- `map_lowess` :16655-16800: `bw = _stat_option_float(options, "bwidth", 0.8, "lowess", lo=0, hi=1)`, reset to .8 outside (0,1) with a note; `_layer_units` (weights refused by `_layer_weights`: `w` None); `if len(x) < 3 or not (ptp(x) >= 1e-30)`: empty line, `_mark_silent` when `len(x) < 3`; `mean`, `noweight` flags; `_stata_lowess`; adjust (:16738-16760); logit (:16767-16772); `_keep = isfinite(y_lw)`; `_on_axis`; source `x_lw, y_lw`; recast path; `_dash_join_glyph`; `_mark_silent(r)` when nothing drawn.
- `_stata_lowess` :16801-16920 (the docstring states the algorithm; the loop at :16864-16919).
- Fixture `stat_truth.json`: `lowess` (auto/census/nlsw88/sp500 x default/mean/noweight curves), `lowess_more`, `lowess_adjust_check`, `lowess_logit_check`, `lowess_default_bwidth_check`, `lowess_full_resolution_check`.
- `test_estimator_cost.py::TestLowessDrawsWhatItDrew` (:165) pins the loop against `_old_lowess` (:51) on the fixture datasets; `TestTheCostIsBounded::test_lowess_on_ten_thousand_rows` (:301).
- Pins to flip: `test_saved_stale_cue.py::_FROZEN` holds `"lowess"` (eleven entries after S10; ten after S16); `test_mode_parity.py::_MOVED_LAYERS` comment; `_EMPTIED_LAYERS` (:2865) includes lowess -- these compare saved vs served after an emptying move and already agree (both empty); they stay as guards.

## User stories

- **US-16.1** As a reader of the saved file, I want the lowess smooth to follow the filter so that the smooth describes the rows I kept.
- **US-16.2** As a Stata user, I want `bwidth()`, `mean`, `noweight`, `adjust` and `logit` honoured after a move as at build.

## Business requirements

- **BR-16.1** After a move the saved lowess equals twoway's `lowess` on the kept rows (1e-9 relative to the served app).
- **BR-16.2** Fewer than three kept rows, or no x spread, draw nothing, silently.
- **BR-16.3** lowess is not marked "(unfiltered)" on the saved page; above the operation cap the layer is empty and the help says why.
- **BR-16.4** The help names lowess among the refitted types and states the cap.

## Technical requirements

- **TR-16.1 Tagging.** In `map_lowess`, before the final `return r` (and on the empty return `_r_empty`, before `return _r_empty`): `r._dash_agg_source = lw_source` (the empty renderer's `data_source` on that path), `r._dash_agg_config = dict(self._fit_agg_config("lowess", xvar, yvar, None, None, fig, options, ["x_lw", "y_lw"], _FIT_GRID, None), bwidth=float(bw), mean=bool(mean), noweight=bool(noweight), adjust=bool(adjust_flag), logit=bool(logit_flag), y_all_mean=(float(_my) if adjust and isfinite(_my) else None), max_ops=float(_DASH_LOWESS_JS_MAX_OPS))`, `r._dash_agg_rows = self._agg_member_ids(source, view)`. Compute `mean`, `noweight`, the adjust and logit flags and `_my` BEFORE the empty return (they are pure option reads; `_my` needs `self.dataset` -- factor the `y_all` block at :16738-16754 into a local closure `_lowess_y_all_mean()` called on both paths). `n` and `range` are irrelevant to lowess (no grid) but the schema requires them: `_FIT_GRID` and None. Not on the recast path.
- **TR-16.2** `_DASH_JS_REFIT_TYPES` gains `"lowess"`; new constant `_DASH_LOWESS_JS_MAX_OPS = 2e8` after it, with a copy-list entry after `"_DASH_JS_REFIT_TYPES",`.
- **TR-16.3 JS helper** before `// DASH_FIT_HELPERS_END`:
  ```js
  // Stata's lowess ([R] lowess, Methods and formulas) as GlyphMapper.
  // _stata_lowess reproduces it (S16): a stable sort by x, k =
  // trunc((N bw - .5)/2), the window max(0,i-k)..min(N-1,i+k), Delta =
  // 1.0001 max|x_j - x_i| at the window's ends, tricube weights (unit under
  // noweight), the weighted line at x_i (the weighted mean under mean), NaN
  // where the window's x do not vary.  Returns {xs, ys} of length N.
  function dash_lowess(x, y, bw, mean, noweight) {
      const n = x.length;
      const order = x.map((v, i) => i).sort((a, b) => (x[a] - x[b]) || (a - b));
      const xs = order.map(i => x[i]), ys = order.map(i => y[i]);
      const k = Math.trunc((n * bw - 0.5) / 2);
      const out = new Array(n);
      for (let i = 0; i < n; i++) {
          const lo = Math.max(0, i - k), hi = Math.min(n - 1, i + k);
          const c = xs[i];
          const delta = 1.0001 * Math.max(c - xs[lo], xs[hi] - c);
          const unit = noweight || delta === 0;
          let sw = 0, sy = 0, sx = 0;
          const w = new Array(hi - lo + 1);
          for (let j = lo; j <= hi; j++) {
              let wj = 1;
              if (!unit) { const t = Math.abs(xs[j] - c) / delta; const t3 = t * t * t; const u = 1 - t3; wj = u * u * u; }
              w[j - lo] = wj; sw += wj; sy += wj * ys[j]; sx += wj * xs[j];
          }
          const ym = sy / sw;
          if (mean) { out[i] = ym; continue; }
          if (delta === 0) { out[i] = NaN; continue; }
          const xm = sx / sw;
          let sxx = 0, sxy = 0;
          for (let j = lo; j <= hi; j++) { const dx = xs[j] - xm; sxx += w[j - lo] * dx * dx; sxy += w[j - lo] * (ys[j] - ym) * dx; }
          if (!(sxx > 0)) { out[i] = NaN; continue; }
          out[i] = ym + (sxy / sxx) * (c - xm);
      }
      return {xs: xs, ys: out};
  }
  ```
  (Python's unit-weight branch sums `yi` and divides by `m`; the loop above with `wj = 1` is the same sum.)
- **TR-16.4 Branch** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'lowess') {
          const n = fx.length;
          let lo = Infinity, hi = -Infinity; for (const v of fx) { if (v < lo) lo = v; if (v > hi) hi = v; }
          if (n < 3 || !(hi - lo >= 1e-30)) { dash_fit_write(src, ac, [], [], null); continue; }
          const k = Math.trunc((n * ac.bwidth - 0.5) / 2);
          if (n * (2 * k + 1) > ac.max_ops) { dash_fit_write(src, ac, [], [], null); src._dash_capped = true; continue; }
          const sm = dash_lowess(fx, fy, ac.bwidth, !!ac.mean, !!ac.noweight);
          let ys = sm.ys;
          if (ac.adjust) {
              let s = 0, c = 0; for (const v of ys) if (isFinite(v)) { s += v; c++; }
              const ms = c ? s / c : NaN;
              const my = (ac.y_all_mean === null || ac.y_all_mean === undefined) ? NaN : ac.y_all_mean;
              ys = (isFinite(ms) && ms !== 0 && isFinite(my)) ? ys.map(v => v * (my / ms)) : ys.map(() => NaN);
          }
          if (ac.logit) {
              const adj = 1 / ys.length;
              ys = ys.map(v => { let s = isNaN(v) ? 1 - adj : v; if (s < 0.0001) s = adj; if (s > 1 - 0.0001) s = 1 - adj; return Math.log(s / (1 - s)); });
          }
          const kx = [], ky = [];
          for (let i = 0; i < ys.length; i++) if (isFinite(ys[i])) { kx.push(sm.xs[i]); ky.push(ys[i]); }
          dash_fit_write(src, ac, kx, ky, null);
  ```
  Python's adjust falls back to the sample's y when the dataset has no finite y (`y_all = y`): mirror it -- when `ac.y_all_mean` is null, use the kept rows' mean of `fy` (compute `my` from `fy` in that case).
- **TR-16.5 Flips**: `_FROZEN` loses `"lowess"`; `_REFIT` gains it.
- **TR-16.6 Help**: dash.sthlp:1946 column 2 (after S10: `lfit, qfit; others marked`) becomes `lfit, qfit, lowess; others marked` (S13 adds lfitci, qfitci in batch 5); the paragraph's list loses `{cmd:lowess},`; add after the S10 sentence: `A {cmd:lowess} smooth is recomputed with Stata's algorithm; a page whose smooth would take more than about half a second (over 200 million window operations, about 15,000 rows at the default bandwidth) leaves the line empty after a move rather than freezing the browser.` (R2-22: at bw .8, N(2k+1) is about 0.8 N²; 2e8 is crossed near N = 15,800; 10,000 rows is 8e7, under the cap, as TR-16.7's timing test assumes.)
- **TR-16.7 Timing**: `TestTheJsTwinsAreBounded::test_lowess_under_node_on_1e4_rows` (under 2 s at N = 10,000, bw .8) and `::test_lowess_is_capped_above_max_ops` (N = 20,000, bw .8 gives `20000*16001 = 3.2e8 > 2e8`: the branch returns empty columns in under 0.2 s).
- **TR-16.8 Parity corpus**: `_move_case("lowess, dropdown", _MOVES[0], [_sc(), plot_for("lowess")])`, `_move_case("lowess bwidth(.4) mean, range", _MOVES[1], [plot_for("lowess", {"bwidth": ".4", "mean": "mean"})])`, `_move_case("lowess noweight adjust, slider", _MOVES[2], [plot_for("lowess", {"noweight": "noweight", "adjust": "adjust"})])`, `_move_case("lowess logit on a 0/1 y, dropdown", _MOVES[0], [plot_for("lowess", {"logit": "logit"}, yvar="foreign", xvar="weight")])`.
- **TR-16.9 function_test_map.py**: `GlyphMapper.map_lowess.<locals>._lowess_y_all_mean` -> `test/test_js_fit_refit.py::TestTheConfig::test_lowess_adjust_mean_is_the_datasets`.

- **TR-16.10 S12's keys in the histogram and kdensity branches (DECISIONS A22; S12 D-12b).** Histogram branch (:25213-25284): both `src.data = {...}` writes build `left: edges.slice(0, n_bins), right: edges.slice(1)`; replace each pair by `left: _hl, right: _hr` computed just above from `const _gap = ac.gap || 0, _off = ac.baroffset || 0; const _hl = [], _hr = []; for (let k = 0; k < n_bins; k++) { const w = edges[k+1] - edges[k], bw = w * (100 - _gap) / 100, c = (edges[k] + edges[k+1]) / 2 + _off * bw; _hl.push(c - bw / 2); _hr.push(c + bw / 2); }` (S12 TR-12.4's formula; `gap`/`baroffset` absent gives the old edges exactly). Kdensity branch (:25285-25370): the line `src.data = { x: xs, y: ys };` (a `run_filter_js_block` marker -- keep it byte for byte) is preceded by `const ys = xe.map(...)`; insert directly after that statement `const _area = (ac.area === undefined || ac.area === null) ? 1 : ac.area; for (let i = 0; i < ys.length; i++) ys[i] *= _area;` (S12 TR-12.5). `boundary` needs no JS read: the build's `x_grid` already spans one bandwidth past the data and the saved page keeps the build's grid (WP-28). The six `run_filter_js_block` markers (section-10 risk factor 1) are not moved.
- **TR-16.11 S11's `atobs` in `dash_fit_grid`.** Change S10's `function dash_fit_grid(x, n, range)` to `function dash_fit_grid(x, n, range, atobs)` with, as its first statement, `if (atobs) return Array.from(new Set(x)).sort((a, b) => a - b);` (the twin of S11 TR-11.6 a, `np.unique`), and pass `ac.atobs` as the fourth argument at the two S10 call sites (`const xg = dash_fit_grid(fx, ac.n, ac.range);` in the lfit and qfit branches) and in the lowess branch if it calls it. `atobs` absent or false leaves every grid unchanged. `test_js_fit_refit.py::TestFitGrid::test_matches_python` keeps its three-argument calls (JS fills `undefined`).

## Boundaries

Do not edit `_stata_lowess` in Python, the option validation at the top of `map_lowess` (:16676-16690), `_dash_memo_wrap`, the served template, other mappers, the histogram/kdensity branches beyond TR-16.10's `left/right` and `_area` lines, `_BRUSH_JS`, S11's fit mappers, S12's mappers, S14's `_dash_connect_opt`/`_dash_recast_opt`, S15's colorvar code.

## Stata truth

No new extractor (the `lowess` fixture keys pin the Python twin; the cscript measures live). Truth block `* ==== S16 F1c: lowess ====`, helpers `_u16_*`:
- **U16-01** `sysuse auto; dash scatter mpg weight || lowess mpg weight, filter(foreign, type(dropdown))`; saved moved to Foreign; `lowess mpg weight if foreign == 1, gen(s) nograph` then compare the saved `(x_lw, y_lw)` with `(weight, s)` sorted stably on the 22 rows, 1e-8 relative.
- **U16-02** `lowess mpg weight, bwidth(.4) mean` with the price range filter to 4500-11385 versus `lowess mpg weight if inrange(price,4500,11385), bwidth(.4) mean gen(s) nograph`.
- **U16-03** `lowess mpg weight, noweight adjust` dropdown to Domestic versus `lowess ... if foreign == 0, noweight adjust gen(s)` -- the adjust mean is all 74 cars' (the Stata side's `adjust` also uses `summ mpg, mean` over all rows).
- **U16-04** `lowess foreign weight, logit` dropdown to Domestic: the Stata side's `logit` on a constant 0 y gives `ln(N-1)` everywhere; the saved page the same (`cert` compares the single value).
- **U16-05** a move leaving two rows: the saved source is empty; `twoway lowess mpg weight if price >= 14500` rc 0 with no note (`cert_file_has` on the log holds no `(note:`).

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended under `# ---- WP-31 F1c: lowess ----`)

- Test: `map_lowess` tags with S10's keys plus `bwidth`, `mean`, `noweight`, `adjust`, `logit`, `y_all_mean`, `max_ops` -- `TestTheConfig::test_lowess_config_keys`, `::test_lowess_adjust_mean_is_the_datasets` (a mapper with `dataset` set: `y_all_mean` is the dataset's mean, not the layer's), `::test_lowess_empty_layer_is_tagged`.
- Test: `_dash_stale_kind("lowess")` is None -- `TestStaleKind::test_lowess_is_refit`.
- Test: `dash_lowess` equals `_stata_lowess` on the fixture's `lowess` datasets (auto, census, nlsw88, sp500) x (default, mean, noweight) -- `TestLowessTwin::test_fixture_curves[dataset-variant]` (`rtol=1e-9, atol=1e-10, equal_nan=True`); on a tie-heavy sample (ten of twenty rows at x = 1, bw .2: NaN at the tied rows) -- `::test_ties_are_missing`.
- Test: the branch equals `map_lowess`'s source for: default, bwidth(.4) mean, noweight, adjust (with `y_all_mean`), logit on 0/1 y, two rows (empty), constant x (empty) -- `TestLowessBranch::test_matches_python[case]`.
- Test: above `max_ops` the branch writes empty columns -- `::test_capped` (N = 20,000 synthetic, `max_ops` forced to 1e6 in the config copy).
- Test: the histogram branch with `gap: 20, baroffset: 0.5` in a hand-written config writes `right - left == 0.8 * width` and centres shifted by `0.5 * 0.8 * width`; without the keys the edges are byte-identical to the base's -- `TestPartnerKeys::test_histogram_gap_and_offset`, `::test_histogram_without_keys_unchanged` (red / guard; `run_filter_js_block("histogram", ...)`).
- Test: the kdensity branch with `area: 2` doubles every density; without the key it is unchanged -- `TestPartnerKeys::test_kdensity_area` (red), `::test_kdensity_without_key_unchanged` (guard).
- Test: `dash_fit_grid(x, n, null, true)` returns the sorted distinct x; the lfit branch with `atobs: true` evaluates at them -- `TestPartnerKeys::test_atobs_grid` (red). (These pin S16's JS reads; the Python keys are S11's and S12's, written in the same batch; the whole-page tests of the pairs live in test_fit_options.py and test_distribution_odds.py.)
- Test: saved equals served after every `_MOVES` -- `TestTheSavedPageRefits::test_saved_equals_served[lowess-move]`.
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked[lowess-*]`.

### Cases in cscripts

- `test_wp31_truth.cscript` U16-01..U16-05.

### Flips

- `_FROZEN` loses lowess.

### Parity corpus

TR-16.8's four entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tagging and config | pytest `TestTheConfig` | -- | saved |
| Algorithm twin | node `TestLowessTwin` | `stat_truth.json` `lowess`, `datasets` | n/a |
| Branch vs mapper | node `TestLowessBranch` | -- | n/a |
| Saved vs served | `TestTheSavedPageRefits`; `MOVE_CORPUS` | -- | yes |
| Cap and cost | `TestTheJsTwinsAreBounded`, `test_capped` | -- | n/a |
| Stata truth | U16-01..05 | live | saved vs Stata's lowess |

**Acceptance criteria**
- **AC-16.1** `dash_lowess` reproduces every fixture curve to 1e-9 relative; the saved page equals the served app after every corpus move.
- **AC-16.2** Fewer than three rows or no x spread draw nothing; the cap empties the layer in under 0.2 s.
- **AC-16.3** lowess is not marked; six fit types remain marked.
- **AC-16.4** N = 10,000 refits under 2 s under node; U16-01..05 pass.

## Tasks

**Commit boundary.** 16-01 to 16-03 form the F1c commit, subject `Re-smooth lowess on the saved page after a filter move (WP-31 F1c)`, on `wp31-s16`. Body: `<scratch>/16-01-failure.txt`; the measured defect; the change (`map_lowess` tags, `dash_lowess`, the branch, `_DASH_LOWESS_JS_MAX_OPS`); `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[lowess-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U16-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- lowess was frozen because the page did not re-smooth it (F1c)`; `Fixture: none`; `BUGS.md: "<F1c title>" (closed)`; `GAPS3: F1c Tracked`.

<task type="auto" id="16-01">
  <name>Write the failing lowess refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the stubs under `# ---- WP-31 F1c: lowess ----`. `TestLowessTwin` reads `test/fixtures/stat_truth.json` `datasets` (x, y arrays per dataset) and `lowess` (per dataset x variant: the curve), runs `run_js(helpers + "process.stdout.write(JSON.stringify(dash_lowess(x, y, bw, mean, noweight)))")` with `helpers` as S10's harness slice (prepend the `dash_own_col` slice), maps null to nan and compares with `GM._stata_lowess(x, y, bw, mean, noweight)` (both arrays) and with the fixture curve where the fixture holds full resolution (`lowess_full_resolution_check` names which). `TestLowessBranch` uses `GM().map_lowess(figure(), ColumnDataSource(sub), "mpg", "weight", opts)`; for the adjust case set `m.dataset = pd.DataFrame(full_df)` before mapping so `y_all_mean` is the dataset's. Extend `_REFIT` in test_saved_stale_cue.py with `"lowess"`. Run `python3 -m pytest test/test_js_fit_refit.py -k lowess test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked -q -n0 2>&1 | tee <scratch>/16-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/16-01-failure.txt is at least 15; nothing staged.]]></verify>
  <done>Every F1c regression test exists and fails at the batch-4 base with the text saved.</done>
</task>

<task type="auto" id="16-02">
  <name>Tag lowess and add its JS twin</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES` gains `"lowess"`; add `_DASH_LOWESS_JS_MAX_OPS = 2e8` after it with the comment `#: WP-31 F1c (D-16.e): the saved page re-smooths a lowess only when N*(2k+1) is at most this; above it the layer is left empty after a move.`; add `"_DASH_LOWESS_JS_MAX_OPS",` to the constants copy tuple after `"_DASH_JS_REFIT_TYPES",`. (2) In `map_lowess` (:16655): move the `mean`/`noweight` reads (:16729-16730) and define `_adj = bool(str(options.get("adjust", "") or "").strip())`, `_lgt = bool(str(options.get("logit", "") or "").strip())` directly after the `_layer_units` call; factor :16738-16754 into a nested `def _lowess_y_all_mean():` returning `float(np.nanmean(y_all))` or `None` when nothing is finite (fall back to `y`'s mean when the dataset has none, as the existing code does), called as `_my = _lowess_y_all_mean() if _adj else None`; keep the existing adjust arithmetic using `_my`. Build `_cfg = dict(self._fit_agg_config("lowess", xvar, yvar, None, None, fig, options, ["x_lw", "y_lw"], _FIT_GRID, None), bwidth=float(bw), mean=bool(mean), noweight=bool(noweight), adjust=_adj, logit=_lgt, y_all_mean=_my, max_ops=float(_DASH_LOWESS_JS_MAX_OPS))` once, before the `len(x) < 3` test, and attach `_dash_agg_source`/`_dash_agg_config`/`_dash_agg_rows` on `_r_empty` before its return and on `r` before the final return (not on the recast return). (3) Insert `dash_lowess` (TR-16.3) before `// DASH_FIT_HELPERS_END` and the branch (TR-16.4) before `// DASH_FIT_BRANCHES_END`. (4) function_test_map.py TR-16.9 entry. Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_estimator_cost.py::TestLowessDrawsWhatItDrew test/test_saved_stale_cue.py test/test_function_test_map.py -q`.]]></action>
  <verify><![CDATA[Green except the `_FROZEN` lowess nodes; `python3 -c "import dash_render as d; print('lowess' in d._DASH_JS_REFIT_TYPES, d._DASH_LOWESS_JS_MAX_OPS)"` prints `True 200000000.0`; `grep -c "function dash_lowess" dash_render.py` prints 1; `grep -c "function dash_fit_grid(x, n, range, atobs)" dash_render.py` prints 1; `grep -c "src.data = { x: xs, y: ys };" dash_render.py` is unchanged from the base.]]></verify>
  <done>The saved page re-smooths lowess from the kept rows with Stata's algorithm, bounded by the operation cap.</done>
</task>

<task type="auto" id="16-03">
  <name>Flip, certify, document and commit F1c</name>
  <files>test/test_saved_stale_cue.py, test/test_wp31_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Remove `"lowess"` from `_FROZEN`. Append TR-16.8's `MOVE_CORPUS` entries under `# WP-31 F1c: lowess re-smooths on the saved page`. Append the U16 block (helpers `_u16_move`, `_u16_gen_compare` reading Stata's `gen(s)` variable through the python block's `Data.get` on the `if` sample sorted stably by x) above the marker line; run `WP31_ONLY=S16 scripts/stata_slot.sh <scratch>/s16 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-16.6 and the conformance pin. Add `test_lowess_under_node_on_1e4_rows` and `test_lowess_is_capped_above_max_ops` to `TestTheJsTwinsAreBounded`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "lowess or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1c (Resolution names `map_lowess`, `dash_lowess`, the cap with its constant; residual: none, the cap is documented behaviour), rewrite the GAPS3 F1c Tracked line, replace the `<!-- WP-31 F1c -->` markers (Results: `lowess on a saved page after a filter move: the build's smooth (marked) -> Stata's lowess on the kept rows; above 200 million window operations the line is left empty (WP-31, F1c)`). Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; slot log `U16-01 ok`..`U16-05 ok`; `git log -1 --format=%s` ends `(WP-31 F1c)`.]]></verify>
  <done>F1c is one green commit: lowess re-smooths on the saved page and is no longer marked.</done>
</task>

## Section completion criteria

- AC-16.1 to AC-16.4; `_DASH_JS_REFIT_TYPES` has three members (lfit, qfit, lowess); `_FROZEN` ten; TR-16.10 and TR-16.11 in place with `TestPartnerKeys` green; `dash_lowess` defined once; the S10 markers intact.
- BUGS.md F1c closed; GAPS3 Tracked rewritten (`- **F1c Tracked:** Closed in WP-31, BUGS.md "<F1c title>", commit pending.`, A11); marker replaced; help updated; one commit.

## Notes

- **Renderer order.** The served app refits lowess through `_dash_redraw_for` with `_dash_memo_wrap`; it has no operation cap (the server pays the cost once per distinct filter state). The saved page's cap is the ONE deliberate mode difference this section adds, visible (an empty line) and documented (TR-16.6) per M8.
- **Decisions for maintainer ratification.** D-16.e (the operation cap and its constant 2e8); the M10 divergence for lowess (2 s at 10,000 rows, not 100,000: twoway's algorithm is O(N·window)); D-16.a (`adjust`'s numerator fixed at build).
- **R12.** S16 is batch 4's only `_FILTER_JS` editor (A22); it carries S12's and S11's JS reads (TR-16.10, TR-16.11) because those sections may not edit the script. S11 and S12 edit no line S16 edits.
- **Stable sort.** `Array.prototype.sort` is stable in every engine since ES2019 (node 12+); the comparator's `|| (a - b)` tie-break makes it stable regardless.
- **Cscript**: `lowess ..., gen(s) nograph` writes the smooth in dataset order; sort the Stata side by `(weight, _n)` before comparing to the saved `x_lw` order.
