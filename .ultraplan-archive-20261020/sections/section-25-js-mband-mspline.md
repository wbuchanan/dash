# Section 25: mband and mspline refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1f · Risk: yellow · Batch: 8 · Depends on: 10 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U25

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): `mband` and `mspline` on a saved page keep the build's knots after a filter move, dimmed and keyed "(unfiltered)"; the served app recomputes them. At `6370ca4` `map_mband` (dash_render.py:20494-20566) and `map_mspline` (:20341-20430) read `bands()` (default `_mband_default_bands(N)` :20795, capped at `_MAX_MBANDS` 1000 :11706) and, for mspline, `n()` (default 10, 1-300), compute `GlyphMapper._cross_medians(x, y, n_bands)` (:20442-20492) and, for mspline with three or more knots, `_natural_cubic_spline(kx, ky, x_grid)` (:22385-22438) on `(K-1)*n + K` points; sources `x_mb, y_mb` and `x_sp, y_sp`. Neither tags; `_dash_stale_kind` gives `"fit"`.

**After this section** the saved page recomputes both from the kept rows: the default band count `max(min(N, 2), floor(min(sqrt(N), 10 log10 N) + .5))` when `bands()` is absent, the band of an observation `floor((x - min) * B / (max - min))` capped at `B - 1` (an x that does not vary is one band at (x, median y)), the cross medians (median x, median y) of each non-empty band with Stata's median (the mean of the two middle order statistics on an even count), straight segments for mband; for mspline the knots alone when fewer than three, else the natural cubic spline (second derivatives zero at the ends, the Thomas algorithm) at `n` equally spaced points strictly between each adjacent knot pair plus the knots. No rows draw nothing, silently. The stale cue stops marking both. Weights are inert on both (twoway accepts and ignores them; `_layer_weights` draws unweighted): `wvar` is null.

**Why these rows share this section.** Both are the cross medians; mspline adds the spline. Together they are the lightest port.

**Test order and commit rule.** One cycle, one commit `(WP-31 F1f)`: 25-01 failing tests; 25-02 tagging, helpers, branches; 25-03 flips, truth block, help, close, commit.

### Section decisions (binding on the executor)

- **D-25.a. The default band count is recomputed from the kept rows** (as `_default_lpoly_bwidth` is for lpoly): the config carries `bands` = the user's `bands()` as an int, or null for the default; the JS applies `_mband_default_bands`'s rule to the kept N. The served app does the same (its redraw calls the mapper on the kept frame).
- **D-25.b. `_MAX_MBANDS` travels as `max_bands`** so the JS clamps a hand-edited config as Python clamps the option (the saved page never generates a config above it; the clamp is defensive). `max_bands` is a key S25 adds to S10's D-10.a per-type key list (R2-15), beside `bands` and mspline's `n_between`.
- **D-25.c. The median is Stata's**: sort the band's values, take `(v[(m-1)/2] + v[m/2]) / 2` with integer division -- numpy's `np.median`, equal to Stata's `summarize, detail` median, which the fixture `mband` records pin.
- **D-25.d. mspline's grid** is `[linspace(kx[i], kx[i+1], n+2)[:-1] for i in 0..K-2] + [kx[K-1]]` exactly: `n + 1` points per interval starting at the left knot, then the last knot.

## Risk: [yellow] -- the bins' edge rule and the median on ties decide knot positions

**Why.** `floor((x - min) * B / range)` versus comparing against linspace edges moved 6 of 20 knots on rounded data (the `_cross_medians` docstring); the JS must use the same expression in the same order.

**Risk factors.** (1) Operator order in the band expression (`(x - min) * B / range`, not `(x - min) / range * B`). (2) An even-count band's median. (3) Batch partners S23 (`_dash_contour_*`) and S24 (axis ticker/LabelSet) do not touch these mappers.

**Mitigation.** (1) `TestCrossMediansTwin` runs every `stat_truth.json` `mband` and `mspline_knots` record (four datasets x bands) against `_cross_medians` -- exact equality on the knots. (2) `::test_even_band_median`. (3) Boundaries.

## Dependencies

- **Depends on: 10** (`dash_fit_rows`, `dash_fit_write`, `dash_solve` is NOT needed: the spline is tridiagonal, `run_fit_js_block`, `_fit_agg_config`, `_DASH_JS_REFIT_TYPES`).
- **Blocks: none.**
- **Parallel batch: 8** with S23 and S24; merge order 25, 23, 24. S25 is batch 8's `_FILTER_JS` editor.

## Evidence

- `map_mspline` :20341-20430: `requested = _stat_option_float(options, "bands", None, "mspline", lo=1, hi=_MAX_MBANDS)`; `n_bands = int(requested) or _mband_default_bands(len(x))`; `n_between = int(_stat_option_float(options, "n", 10, "mspline", lo=1, hi=300) or 10)`; `kx, ky = _cross_medians`; `len(kx) < 1` -> empty, `_mark_silent`; `len(kx) < 3` -> the knots; else the grid and `_natural_cubic_spline`; `_on_axis`; source `x_sp, y_sp`; recast; `_dash_join_glyph` with `plot_line_width(color_idx, "")`.
- `map_mband` :20494-20566: `bands` the same; `_cross_medians`; empty -> `_mark_silent`; source `x_mb, y_mb`.
- `_cross_medians` :20442-20492 (the band expression at :20480-20481; `x_max == x_min` -> one knot `(x_min, median(y))`).
- `_mband_default_bands` :20795-20826. `_natural_cubic_spline` :22385-22438 (Thomas algorithm; `K < 2` -> `ky[0]`; two knots -> the chord).
- Fixtures: `stat_truth.json` `mband` (per `dataset:bandsN`: `band_x`, `band_y`, `N_xy`), `mband_default_band_count`, `mband_default_band_count_rule_search`, `mspline` (per case `n_points`, `point_count_rule`, the curve), `mspline_knots`, `mspline_checks`.
- Pins to flip: `_FROZEN` holds `"mband"`, `"mspline"`; `_EMPTIED_LAYERS` lists both (guards; they stay).

## User stories

- **US-25.1** As a reader of the saved file, I want the median bands and the median spline to follow the filter.
- **US-25.2** As a Stata user, I want `bands()` and `n()` honoured after a move, and the default band count to follow the kept sample as twoway's does.

## Business requirements

- **BR-25.1** After a move the saved mband knots equal twoway's cross medians of the kept rows exactly; the mspline curve equals the served app's to 1e-9 relative.
- **BR-25.2** No kept row draws nothing; one or two knots draw the knots alone (mspline).
- **BR-25.3** Neither type is marked "(unfiltered)" on the saved page.

## Technical requirements

- **TR-25.1 Tagging.** `map_mband`: before the final `return [r]` and on the empty return: `r._dash_agg_source = mb_source` (or the empty renderer's source), `r._dash_agg_config = dict(self._fit_agg_config("mband", xvar, yvar, None, None, fig, options, ["x_mb", "y_mb"], _FIT_GRID, None), bands=(int(requested) if requested is not None else None), max_bands=int(_MAX_MBANDS))`, `r._dash_agg_rows = self._agg_member_ids(source, view)`. `map_mspline` likewise with `["x_sp", "y_sp"]`, `bands`, `max_bands`, `n_between=int(n_between)`. Not on the recast returns. `requested` and `n_between` are read before the empty return already.
- **TR-25.2** `_DASH_JS_REFIT_TYPES` gains `"mband", "mspline"`.
- **TR-25.3 Helpers** before `// DASH_FIT_HELPERS_END`:
  ```js
  // ---- mband / mspline (S25): Stata's cross medians and the natural cubic spline.
  function dash_median(v) { const s = v.slice().sort((a, b) => a - b); const m = s.length; if (!m) return NaN; return (m % 2) ? s[(m - 1) / 2] : (s[m / 2 - 1] + s[m / 2]) / 2; }
  // _mband_default_bands: round(min(10 log10 N, sqrt N)), at least min(N, 2).
  function dash_mband_default_bands(n) { if (n < 1) return 1; return Math.max(Math.min(n, 2), Math.floor(Math.min(Math.sqrt(n), 10 * Math.log10(n)) + 0.5)); }
  // _cross_medians: the observed x range cut into B equal-width bands, an
  // observation in band floor((x - min) B / range) capped at B - 1; the
  // median x and median y of each non-empty band.  One knot when x does
  // not vary.  Returns {kx, ky}.
  function dash_cross_medians(x, y, B) {
      const n = x.length; if (!n) return {kx: [], ky: []};
      let mn = Infinity, mx = -Infinity; for (const v of x) { if (v < mn) mn = v; if (v > mx) mx = v; }
      if (mx === mn) return {kx: [mn], ky: [dash_median(y)]};
      B = Math.max(1, Math.trunc(B));
      const groups = new Array(B); for (let b = 0; b < B; b++) groups[b] = null;
      for (let i = 0; i < n; i++) { let b = Math.floor((x[i] - mn) * B / (mx - mn)); if (b > B - 1) b = B - 1; if (groups[b] === null) groups[b] = {x: [], y: []}; groups[b].x.push(x[i]); groups[b].y.push(y[i]); }
      const kx = [], ky = [];
      for (let b = 0; b < B; b++) if (groups[b] !== null) { kx.push(dash_median(groups[b].x)); ky.push(dash_median(groups[b].y)); }
      return {kx, ky};
  }
  // _natural_cubic_spline through (kx, ky) at xg: second derivatives zero at
  // both ends, the interior ones from the tridiagonal system by the Thomas
  // algorithm; two knots are the chord.
  function dash_natural_cubic_spline(kx, ky, xg) {
      const K = kx.length;
      if (K < 2) return xg.map(() => K ? ky[0] : NaN);
      const h = []; for (let i = 0; i < K - 1; i++) h.push(kx[i + 1] - kx[i]);
      const M = new Array(K).fill(0);
      if (K > 2) {
          const m = K - 2; const a = [], b = [], c = [], rhs = [];
          for (let i = 0; i < m; i++) { a.push(h[i]); b.push(2 * (h[i] + h[i + 1])); c.push(h[i + 1]); rhs.push(6 * ((ky[i + 2] - ky[i + 1]) / h[i + 1] - (ky[i + 1] - ky[i]) / h[i])); }
          for (let i = 1; i < m; i++) { const f = a[i] / b[i - 1]; b[i] -= f * c[i - 1]; rhs[i] -= f * rhs[i - 1]; }
          const sol = new Array(m).fill(0); sol[m - 1] = rhs[m - 1] / b[m - 1];
          for (let i = m - 2; i >= 0; i--) sol[i] = (rhs[i] - c[i] * sol[i + 1]) / b[i];
          for (let i = 0; i < m; i++) M[i + 1] = sol[i];
      }
      return xg.map(v => {
          let seg = 0; while (seg < K - 2 && v >= kx[seg + 1]) seg++;   // searchsorted(side="right") - 1, clipped to K-2
          const x0 = kx[seg], x1 = kx[seg + 1], y0 = ky[seg], y1 = ky[seg + 1], m0 = M[seg], m1 = M[seg + 1];
          const hh = x1 - x0, t = x1 - v, u = v - x0;
          return m0 * t * t * t / (6 * hh) + m1 * u * u * u / (6 * hh) + (y0 / hh - m0 * hh / 6) * t + (y1 / hh - m1 * hh / 6) * u;
      });
  }
  ```
  `np.searchsorted(kx, xg, side="right") - 1` clipped to `[0, K-2]`: the while loop above advances while `v >= kx[seg+1]` and stops at `K-2` -- equal for `v` within `[kx[0], kx[K-1]]`; a `v` below `kx[0]` gives seg 0 in both.
- **TR-25.4 Branches** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'mband' || ac.type === 'mspline') {
          const n = fx.length;
          if (n < 1) { dash_fit_write(src, ac, [], [], null); continue; }
          let B = (ac.bands === null || ac.bands === undefined) ? dash_mband_default_bands(n) : ac.bands;
          B = Math.max(1, Math.min(Math.trunc(B), ac.max_bands || 1000));
          const cm = dash_cross_medians(fx, fy, B);
          if (ac.type === 'mband' || cm.kx.length < 3) { dash_fit_write(src, ac, cm.kx, cm.ky, null); continue; }
          const nb = Math.max(1, Math.min(300, Math.trunc(ac.n_between || 10)));
          const xg = [];
          for (let i = 0; i < cm.kx.length - 1; i++) { const a = cm.kx[i], b = cm.kx[i + 1]; for (let k = 0; k < nb + 1; k++) xg.push(a + (b - a) * k / (nb + 1)); }
          xg.push(cm.kx[cm.kx.length - 1]);
          dash_fit_write(src, ac, xg, dash_natural_cubic_spline(cm.kx, cm.ky, xg), null);
  ```
  (`linspace(a, b, nb+2)[:-1]` is `a + (b-a) k/(nb+1)` for k = 0..nb.)
- **TR-25.5 Flips**: `_FROZEN` loses both; `_REFIT` gains them.
- **TR-25.6 Help**: dash.sthlp:1946 column 2 `all but fpfit, fpfitci (marked)`; the paragraph's list loses `{cmd:mband}, {cmd:mspline}` and the text now reads "it does not refit a fractional-polynomial fit ({cmd:fpfit}, {cmd:fpfitci})"; add: `The median bands and median spline ({cmd:mband}, {cmd:mspline}) are recomputed from the kept rows, the default number of bands following their count as twoway's does.`
- **TR-25.7 Timing**: `TestTheJsTwinsAreBounded::test_mband_and_mspline_under_node_on_1e5_rows` under 2 s each (sorting 1e5 values once per band).
- **TR-25.8 Parity corpus**: `_move_case("mband, dropdown", _MOVES[0], [_sc(), plot_for("mband")])`, `_move_case("mspline bands(5) n(4), range", _MOVES[1], [plot_for("mspline", {"bands": "5", "n": "4"})])`, `_move_case("mband bands(20) [aw=weight] (inert), slider", _MOVES[2], [plot_for("mband", {"bands": "20", "weight": "aweight", "wexp": "weight"})])`, `_move_case("mspline on a date x, dropdown", _MOVES[0], [plot_for("mspline", yvar="mpg", xvar="when")])`.

## Boundaries

Do not edit `_cross_medians`, `_mband_default_bands`, `_natural_cubic_spline` in Python, the option reads at the top of either mapper, `_MAX_MBANDS`, S23's contour helpers, S24's ticker/LabelSet code, `_BRUSH_JS`.

## Stata truth

No new extractor (`stat_truth.json` `mband`/`mspline` pin the Python twins). Truth block `* ==== S25 F1f: mband and mspline ====`, helpers `_u25_*`:
- **U25-01** `sysuse auto; dash scatter mpg weight || mband mpg weight, filter(foreign, type(dropdown))`; saved moved to Foreign; `twoway mband mpg weight if foreign == 1` serset: the knots equal the saved `(x_mb, y_mb)` exactly (the serset holds float values: compare at 1e-6 relative); `r(bands)`-equivalent: the knot count equals `max(min(22,2), round(min(sqrt(22), 10*log10(22))))` = 5 (measured in the block).
- **U25-02** `mspline mpg weight, bands(5) n(4)` with the price range to 4500-11385 versus `twoway mspline mpg weight if inrange(price,4500,11385), bands(5) n(4)` serset: point count `(K-1)*4 + K` and values at 1e-5 relative (the serset is float32).
- **U25-03** `mband mpg weight, bands(20)` dropdown to Domestic versus `twoway mband ... if foreign == 0, bands(20)`.
- **U25-04** `mspline mpg weight` dropdown leaving two knots (`bands(2)` on Foreign): the saved curve is the two knots; twoway's serset has two points.
- **U25-05** a move leaving one row: mband's saved source is that one knot; `twoway mband mpg weight if price >= 15906` plots one point, rc 0.

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended under `# ---- WP-31 F1f: mband and mspline ----`)

- Test: both mappers tag with S10's keys plus `bands`, `max_bands` (mspline: `n_between`) -- `TestTheConfig::test_mband_config_keys`, `::test_mspline_config_keys`, `::test_mband_empty_layer_is_tagged`, `::test_weights_are_inert_in_the_config` (`wvar is None` with `[aw=]`).
- Test: `_dash_stale_kind` None for both -- `TestStaleKind::test_mband_and_mspline_are_refit`.
- Test: `dash_mband_default_bands(n)` equals `_mband_default_bands(n)` for n in 1..300 and the fixture's `mband_default_band_count` pairs -- `TestMbandTwin::test_default_bands`.
- Test: `dash_cross_medians` equals `_cross_medians` exactly on every `mband` and `mspline_knots` fixture record and on x = 0, .1, ..., 1 with bands(10) (10 knots) -- `::test_fixture_knots[case]`, `::test_edge_values_belong_above`; an even band's median -- `::test_even_band_median`; a constant x -- `::test_constant_x_is_one_knot`.
- Test: `dash_natural_cubic_spline` equals `_natural_cubic_spline` on the fixture `mspline` knots at the mspline grid (1e-9) and on two knots (the chord) -- `TestSplineTwin::test_fixture_curves[case]`, `::test_two_knots`.
- Test: the branches equal `map_mband`/`map_mspline` sources for: default, bands(5) n(4), bands(20), two knots, one row, no rows (empty) -- `TestMbandBranch::test_matches_python[case]`, `TestMsplineBranch::test_matches_python[case]`.
- Test: saved equals served after every `_MOVES` -- `TestTheSavedPageRefits::test_saved_equals_served[mband|mspline-move]`.
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked[mband|mspline-*]`.

### Cases in cscripts

- `test_wp31_truth.cscript` U25-01..U25-05.

### Flips

- `_FROZEN` loses mband, mspline.

### Parity corpus

TR-25.8's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tagging | pytest `TestTheConfig` | -- | saved |
| Bands, medians, spline twins | node `TestMbandTwin`, `TestSplineTwin` | `stat_truth.json` `mband`, `mspline`, `mspline_knots`, `mband_default_band_count` | n/a |
| Branches; saved vs served | node `TestMbandBranch`, `TestMsplineBranch`; `TestTheSavedPageRefits`; `MOVE_CORPUS` | -- | yes |
| Stata truth | U25-01..05 | live | saved vs twoway sersets |
| Cost | `TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-25.1** Knots equal Python's exactly on every fixture record; the spline to 1e-9.
- **AC-25.2** Saved equals served after every corpus move.
- **AC-25.3** Neither type is marked; fpfit and fpfitci remain marked.
- **AC-25.4** U25-01..05 pass; 1e5-row recomputes under 2 s.

## Tasks

**Commit boundary.** 25-01 to 25-03 form the F1f commit, subject `Recompute mband and mspline on the saved page after a filter move (WP-31 F1f)`, on `wp31-s25`. Body as the S10 form with `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[mband-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U25-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- mband and mspline were frozen because the page did not recompute them (F1f)`; `Fixture: none`; `BUGS.md: "<F1f title>" (closed)`; `GAPS3: F1f Tracked`.

<task type="auto" id="25-01">
  <name>Write the failing mband and mspline tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the stubs under `# ---- WP-31 F1f: mband and mspline ----`. `TestMbandTwin::test_fixture_knots` reads `stat_truth.json` `mband` (per `dataset:bandsN`: `band_x`, `band_y`; the dataset's x, y from `datasets`), runs `dash_cross_medians(x, y, N)` under node and asserts `kx == band_x` and `ky == band_y` exactly (lists of floats; the fixture holds Stata's exact values, which `_cross_medians` already reproduces). `TestSplineTwin` uses the `mspline` records' knots (`mspline_knots`) and grid (recompute the grid as `map_mspline` does) comparing with `dr._natural_cubic_spline`. Extend `_REFIT` with `"mband", "mspline"`. Run `python3 -m pytest test/test_js_fit_refit.py -k "mband or mspline or Mband or Spline" test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked -q -n0 2>&1 | tee <scratch>/25-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/25-01-failure.txt is at least 20; nothing staged.]]></verify>
  <done>Every F1f regression test exists and fails at the batch-8 base with the text saved.</done>
</task>

<task type="auto" id="25-02">
  <name>Tag mband and mspline and add their JS twins</name>
  <files>dash_render.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES` gains `"mband", "mspline"`. (2) `map_mband` (:20494) and `map_mspline` (:20341): build `_cfg` per TR-25.1 after the option reads and attach on the empty and the drawn returns (not recast). (3) Insert TR-25.3's helpers before `// DASH_FIT_HELPERS_END` and TR-25.4's branch before `// DASH_FIT_BRANCHES_END`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py -k "Median or Spline or Mband or FilterJavaScript or mband or mspline" test/test_saved_stale_cue.py -q`.]]></action>
  <verify><![CDATA[Green except the `_FROZEN` mband/mspline nodes; `grep -c "function dash_cross_medians\|function dash_natural_cubic_spline" dash_render.py` prints 2.]]></verify>
  <done>The saved page recomputes mband's knots and mspline's spline from the kept rows.</done>
</task>

<task type="auto" id="25-03">
  <name>Flip, certify, document and commit F1f</name>
  <files>test/test_saved_stale_cue.py, test/test_wp31_truth.cscript, dash.sthlp</files>
  <action><![CDATA[Remove `"mband", "mspline"` from `_FROZEN`. Append TR-25.8's `MOVE_CORPUS` entries under `# WP-31 F1f: mband and mspline recompute on the saved page`. Append the U25 block (helpers `_u25_move`, `_u25_serset` reading `.t.plotregion1.plot1.serset` x/y) above the marker line; run `WP31_ONLY=S25 scripts/stata_slot.sh <scratch>/s25 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-25.6 and the conformance pin. Add `test_mband_and_mspline_under_node_on_1e5_rows` to `TestTheJsTwinsAreBounded`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "mband or mspline or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1f; rewrite the GAPS3 F1f Tracked line to `- **F1f Tracked:** Closed in WP-31, BUGS.md "<F1f title>", commit pending.` (write `commit pending`; the merger's step k.3b fills the sha, DECISIONS A11); replace the `<!-- WP-31 F1f -->` markers (Results: `mband and mspline on a saved page after a filter move: the build's knots (marked) -> the cross medians and spline of the kept rows (WP-31, F1f)`). Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; slot log `U25-01 ok`..`U25-05 ok`; `grep -c "F1f Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 F1f)`.]]></verify>
  <done>F1f is one green commit: mband and mspline recompute on the saved page and are no longer marked.</done>
</task>

## Section completion criteria

- AC-25.1 to AC-25.4; `_DASH_JS_REFIT_TYPES` holds mband and mspline (two more than at the batch-8 base); `_FROZEN` holds fpfit, fpfitci, histogram, kdensity only; the markers intact.
- BUGS.md F1f closed; GAPS3 Tracked rewritten; marker replaced; help updated; one commit.

## Notes

- **Renderer order.** Class methods and the three Python helpers already travel to the served app (`_mband_default_bands`, `_natural_cubic_spline` are in the statistical helpers tuple :47446-47503); nothing new to copy.
- **Decisions for maintainer ratification.** D-25.a (the default band count follows the kept rows), D-25.b (`max_bands` in the config).
- **R12.** S25 is batch 8's only `_FILTER_JS` editor; S23 adds NEW module functions and S24 edits axis code -- no overlap.
- **Cscript**: `twoway mband`'s serset holds `__000000` x and y variables named after the plotted variables; read through `serset use`; values are float32 -- compare at 1e-5 relative.

## Addendum (14oct2026, DECISIONS D16): row C6b added to this section

### C6b: mband and mspline over data with missing y draw fewer vertices than twoway

**Gap.** S14 measured (test/fixtures/area_cmissing_truth.json E04, E05) that on data with missing y twoway mband draws 9 vertices where dash draws 8, and mspline 89 where dash draws 78; it is not a cmissing() effect.

**Requirement.** Before porting the twins to JavaScript, measure twoway's mband and mspline vertices (serset) on data with missing y (and missing x) and match them in `map_mband`/`map_mspline`; the JavaScript twins then match the corrected Python. Both modes.

**Tests.** pytest pinning the vertex counts and values to the fixture's E04/E05 (or a new extract), and a `* ==== S25 C6b: ... ====` truth block. One commit, subject ending `(WP-31 C6b)`, BEFORE the F1f commit, so F1f's twins are written against the corrected Python.

**Process (binding).** As every row: failing tests first with saved failure text; close the BUGS.md entry "mband and mspline over data with missing y draw fewer vertices than twoway" (Resolution ending `Closes GAPS3 C6 (WP-31, C6b).`), delete its `"C6b":` WP31_OPEN line, rewrite GAPS3.md's `- **C6b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 C6b -->` under `### Results that change` with a line ending `(WP-31, C6b)`. dash replaces twoway (D13).

