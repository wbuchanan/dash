# Section 19: lpoly refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1d · Risk: red · Batch: 6 · Depends on: 10 · Blocks: 22 · Tasks: 3, 1 commit · Case-id prefix: U19

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): `lpoly` on a saved page keeps the build's smooth after a filter move, dimmed and keyed "(unfiltered)"; the served app refits it, deriving Stata's default bandwidth from the kept rows (WP-29 P0.7, `MOVE_CORPUS` "lpoly biweight degree 2, dropdown"). At `6370ca4` `map_lpoly` (dash_render.py:17107-17218) reads `bwidth()`, `degree()`, `kernel()`, `n()`, computes `GlyphMapper._default_lpoly_bwidth` (:16922 -> `_lpoly_rot_detail` :21621-21780) when no bandwidth is given, then `_compute_lpoly_fit` (:16960-17077) on `_lpoly_grid_n` (:17079) points, and writes `ColumnDataSource({"x_lp", "y_lp"})`; it tags nothing. `_dash_stale_kind("lpoly")` is `"fit"`.

**After this section** the saved page refits lpoly from the kept rows: the kernel weights `K((x - x0)/h)` with strict support (`_lpoly_kernel_weights` :22049), observation weights as lpoly uses them (aw normalised to mean 1, fw raw: `_dash_lpoly_weights` :22032), a grid point missing where fewer than two observations have positive weight, degree 0 the weighted mean, degree 1-3 the local weighted least squares in powers of `(x - x0)` on the columns Stata's `invsym` keeps (`_lpoly_kept_columns` :21545), the grid of `_lpoly_grid_n` (n = `_N` when the DATASET has fewer than 50 rows, else `n()` capped at `_N`, 50 by default), and -- when `bwidth()` is absent -- Stata's rule-of-thumb bandwidth recomputed from the kept rows (`_lpoly_rot_detail`: the Fan-Gijbels constant `_LPOLY_ROT_CONSTANTS[(kernel, pe)]`, a global fit of degree pe+3, `s2`, the integral of the squared (pe+1)th derivative over the central 90%). A missing rule-of-thumb draws y = 0 at every grid point, as twoway does. The stale cue stops marking lpoly.

**Why this row is its own section (red).** The rule of thumb is the one estimator whose Python twin uses EXACT rational arithmetic (`fractions.Fraction` in `_lpoly_rot_detail` and `_stata_invsym_keep`) to decide which raw-power columns Stata's `invsym` keeps; JavaScript has no such type. D-19.a bounds the port.

**Test order and commit rule.** One cycle, one commit `(WP-31 F1d)`: 19-01 failing tests; 19-02 tagging, helpers, branch, `_DASH_JS_REFIT_TYPES`; 19-03 flips, truth block, help, close, commit.

### Section decisions (binding on the executor)

- **D-19.a. The rule of thumb is computed on the centred and scaled design, in float64.** `_lpoly_rot_detail` forms the Gram of RAW powers exactly (Fractions) to reproduce `invsym`'s column drops, then fits. The JS twin computes `z = (x - c)/s` (c the midrange, s the half-range, as Python's `V`), the weighted Gram `Gz` and `gz` in float64 with plain sums (the scaled design is well conditioned; no compensation), keeps EVERY column (the Vandermonde in z on 2 or more distinct x is full rank for d+1 <= distinct values), solves with `dash_solve`, and computes `s2`, the derivative polynomial `D = polyder(a, pe+1) / s^(pe+1)`, `I = s * (Pi(zu) - Pi(zl))`, `h = C * (s2 (u-l) / (W I))^(1/(2pe+3))`. Where Python's row has `kept` all ones and route `"exact"` (the fixture's `class` is `"exact"`), the two agree to 1e-6 relative (the residual polynomial is the same function; only round-off differs). Where Python drops a column (fewer distinct x than d+1 -- then the JS Gram is singular and `dash_solve` returns null -> h NaN -> the line at 0, which is also Stata's outcome on `x` of 0/1 only, measured in `_lpoly_rot_detail`'s docstring) or takes the `"float"` route (an exact global fit: `s2 <= 1e-24 vy`) the JS returns NaN and draws y = 0, where Python's `_lpoly_rot_float` emulates Stata's round-off. This is a documented divergence (D1/D2 of lpoly_rot_truth.json's `divergences` already record Python-vs-Stata there), filed under M12 as an open BUGS.md entry "lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app" by 19-03. The quadcross overflow guard (sums of `w|x|^k` past DBL_MAX) is ported in logs as Python has it (`_lse`).
- **D-19.b. Local fits keep the columns a FLOAT sweep keeps.** `_lpoly_kept_columns` first sweeps the window's raw Gram in float (intercept first, then largest pivot; a pivot below 1e-6 of its diagonal or 1e-16 fails) and keeps all columns when every pivot passes (933 of 1191 fixture windows); otherwise it takes the exact `_stata_invsym_keep(G, order=(0,))` (rel 1e-9, floor 1e-19). The JS `dash_invsym_keep(G, order, rel, floor)` ports the SWEEP in float with the exact rule's thresholds (1e-9, 1e-19) when the 1e-6/1e-16 sweep fails. On the fixture's curves (`lpoly_rot_truth.json` `curves`, `stat_truth.json` `lpoly`) agreement is asserted at 1e-8 relative; a window where the float sweep and the exact decision differ is a documented divergence under the same BUGS.md entry.
- **D-19.c. `n_dataset` travels in the config.** `_lpoly_grid_n` reads `len(self.dataset)`: the config carries `n_dataset` (int; the layer's row count when the mapper has no dataset) and `n_user` (the `n()` value or null), and the JS applies the rule: `N < 50 -> N`; else `n = (n_user is null or <= 1) ? 50 : trunc(n_user)`, `min(n, N)`, at least 1. `N` is the dataset's size and does not change with a filter (twoway's `_N` is every row in memory). S19's five type-specific config keys are `bwidth` (null for the rule of thumb), `degree`, `kernel`, `n_dataset` and `n_user`; S10's D-10.a per-section schema list names them under S19.
- **D-19.d. The kernel table is `dash_kernel` (:25124).** Its functions match `_KERNELS` (:21442) by value; the strict support is applied in `dash_lpoly_kw` (`|z| < support`, supports: epanechnikov sqrt(5), epan2/biweight/rectangle/triangle/parzen 1, cosine .5, gaussian infinite).

## Risk: [red] -- an exact-arithmetic estimator ported to float, on every lpoly dashboard

**Why.** A wrong bandwidth draws a plausible curve. The rule-of-thumb constants table has 32 entries to transcribe. The local fit's column rule decides curves on tied x.

**Risk factors.** (1) Transcription errors in `_LPOLY_ROT_CONSTANTS`. (2) The D-19.a divergences. (3) Cost: a 100,000-row lpoly at 50 grid points is 5e6 kernel evaluations plus the global degree-4 fit -- fine; degree 3 at 1e5 rows with a window covering the data is 1e5 x 50 x 16 multiply-adds -- fine. (4) Batch partners S17 (colorvar option readers) and S18 (map_dot) do not touch `map_lpoly`.

**Mitigation.** (1) The table is emitted from Python: `_FILTER_JS` is a module string; the constants are spliced by `.replace("__DASH_LPOLY_ROT_CONSTANTS__", json.dumps({f"{k}|{p}": v for (k, p), v in _LPOLY_ROT_CONSTANTS.items()}))` beside the existing `__DASH_ROW_ID__` replacement (:25467) -- no hand transcription. (2) `TestRotTwin` runs all 785 fixture rows: exact-class rows with all columns kept at 1e-6; the others asserted to give NaN or the row's recorded outcome. (3) `TestTheJsTwinsAreBounded::test_lpoly_under_node_on_1e5_rows` at degree 0 and 3. (4) Boundaries.

## Dependencies

- **Depends on: 10** (`dash_fit_rows`, `dash_fit_write`, `dash_solve`, `dash_weight_norm`, `run_fit_js_block`, `_fit_agg_config`, `_DASH_JS_REFIT_TYPES`).
- **Blocks: 22** (lpolyci reuses `dash_lpoly_kw`, `dash_lpoly_local`, `dash_lpoly_rot`, `dash_lpoly_fit`).
- **Parallel batch: 6** with S17 and S18; merge order 19, 17, 18. S19 is batch 6's `_FILTER_JS` editor.

## Evidence

- `map_lpoly` :17107-17218: `len(x) < 2` -> empty, `_mark_silent`; `bwidth` (<= 0 -> None with a note); `degree` 0-3; `kernel` in `_KERNELS` else epanechnikov; `n_grid = self._lpoly_grid_n(options, "lpoly", len(x))`; `lw = _dash_lpoly_weights(w, wtype)`; `bw = bwidth or _default_lpoly_bwidth(x, y, lw, degree, kernel)`; not finite -> `linspace(min, max, n_grid)` and zeros; else `_compute_lpoly_fit`; `valid = ~isnan`; `_on_axis`; source `x_lp, y_lp`; recast; `_mark_silent` when nothing valid.
- `_compute_lpoly_fit` :16960-17077: per grid point `kw = _lpoly_kernel_weights(x, x0, h, kernel) * ow`; `pos = kw > 0`; `< 2 -> NaN`; degree 0 `dot(kw, y)/sum`; else `X = vander(x[pos] - x0, degree+1)`, `G = X' diag(kp) X`; non-finite -> NaN; `K = _lpoly_kept_columns(G)`; all kept -> `polyfit(xp, y[pos], degree, w=sqrt(kp))` at x0 (equal to solving the normal equations; the twin solves them); `0 not in K` -> NaN; else solve `G[K,K] b = g[K]`, `b[0]`.
- `_lpoly_grid_n` :17079-17105. `_dash_lpoly_weights` :22032. `_lpoly_kernel_weights` :22049. `_lpoly_kept_columns` :21545; `_stata_invsym_keep` :21494. `_lpoly_rot_detail` :21621-21780; `_lpoly_rot_float` :21580; `_LPOLY_ROT_CONSTANTS` :486-504; `_LPOLY_ROT_GRID` :479.
- Fixtures: `lpoly_rot_truth.json` (`rows` 785: `id`, `ds`, `idx`, `w`, `degree`, `kernel`, `bwidth`, `class`, `kept`, `tol`, `n_grid`; `curves`; `datasets`; `divergences` D1-D3), `stat_truth.json` `lpoly`, `lpoly_twoway`.
- Pins to flip: `_FROZEN` holds `"lpoly"`; `test_mode_parity.py` `_MOVED_LAYERS` already lists lpoly (served refit vs saved cue agreed because the cue dims; after this both refit).

## User stories

- **US-19.1** As a reader of the saved file, I want the lpoly smooth, and its default bandwidth, to follow the filter as the served app's do.
- **US-19.2** As a Stata user, I want `bwidth()`, `degree()`, `kernel()` and `n()` honoured after a move.

## Business requirements

- **BR-19.1** After a move the saved lpoly equals the served app's to 1e-8 relative wherever Stata's bandwidth is a property of the data (not round-off), and draws y = 0 where Stata's `r(bwidth)` is missing.
- **BR-19.2** Fewer than two rows draw nothing; a grid point with fewer than two weighted observations is missing.
- **BR-19.3** lpoly is not marked "(unfiltered)"; the help says so and names the exact-fit divergence.

## Technical requirements

- **TR-19.1 Tagging.** In `map_lpoly`, on the empty return and before the final `return r`: `_dash_agg_source = lp_src` (or the empty renderer's source), `_dash_agg_config = dict(self._fit_agg_config("lpoly", xvar, yvar, wtype, w, fig, options, ["x_lp", "y_lp"], n_grid, None), bwidth=(float(bwidth) if bwidth is not None else None), degree=int(degree), kernel=str(kernel), n_dataset=int(N), n_user=(float(user) if user is not None else None))` where `N` and `user` are what `_lpoly_grid_n` computed -- refactor `_lpoly_grid_n` to return `(n, N, user)` through a new `_lpoly_grid_plan(options, layer, n_sample)` and keep `_lpoly_grid_n` as `return self._lpoly_grid_plan(...)[0]`; `_dash_agg_rows` as always. Compute the option reads before the `len(x) < 2` return (they are pure).
- **TR-19.2** `_DASH_JS_REFIT_TYPES` gains `"lpoly"`. `_FILTER_JS`'s trailing `.replace(...)` chain gains `.replace("__DASH_LPOLY_ROT_CONSTANTS__", json.dumps({"%s|%d" % k: v for k, v in _LPOLY_ROT_CONSTANTS.items()}))` and `.replace("__DASH_LPOLY_SUPPORT__", json.dumps({k: (None if math.isinf(s) else s) for k, (s, _f) in _KERNELS.items()}))`. `_LPOLY_ROT_CONSTANTS` (:486) and `_KERNELS` (:21442) are both defined before `_FILTER_JS` (:24612), so both tables exist when the module statement runs.
- **TR-19.3 JS helpers** before `// DASH_FIT_HELPERS_END` (full bodies in 19-02): `const _DASH_LPOLY_ROT_C = JSON.parse('__DASH_LPOLY_ROT_CONSTANTS__');` and `const _DASH_LPOLY_SUPPORT = JSON.parse('__DASH_LPOLY_SUPPORT__');` (string literals; `json.dumps` output holds no quote), `dash_lpoly_weights(w, wtype)` (a null-safe wrapper over S10's `dash_weight_norm`: aw/pw scaled to sum n, fw raw -- R2-23), `dash_lpoly_kw(x, x0, h, kernel)`, `dash_invsym_keep(G, order, rel, floor)`, `dash_lpoly_kept(G)`, `dash_lpoly_local(x, y, kw, x0, h, degree)` (returns `{pos, Z, Ainv, beta}` in the scaled powers `(x-x0)/h` on the kept columns, as `_lpoly_local_wls`; S22 needs `Ainv`), `dash_lpoly_fit(x, y, h, degree, kernel, w, xg)`, `dash_polyder(a, m)`, `dash_polyint(a)`, `dash_polymul(a, b)`, `dash_polyval(a, z)`, `dash_lpoly_rot(x, y, w, degree, kernel)`, `dash_lpoly_grid_n(nDataset, nUser)`, `dash_linspace(lo, hi, n)`.
- **TR-19.4 Branch** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'lpoly') {
          const n = fx.length;
          if (n < 2) { dash_fit_write(src, ac, [], [], null); continue; }
          const lw = dash_lpoly_weights(fw, ac.wtype);
          const ng = dash_lpoly_grid_n(ac.n_dataset, ac.n_user);
          const h = (ac.bwidth !== null && ac.bwidth !== undefined) ? ac.bwidth : dash_lpoly_rot(fx, fy, lw, ac.degree, ac.kernel);
          let lo = Infinity, hi = -Infinity; for (const v of fx) { if (v < lo) lo = v; if (v > hi) hi = v; }
          const xg = dash_linspace(lo, hi, ng);
          let yg;
          if (!isFinite(h)) yg = xg.map(() => 0);
          else yg = dash_lpoly_fit(fx, fy, h, ac.degree, ac.kernel, lw, xg);
          const kx = [], ky = [];
          for (let i = 0; i < xg.length; i++) if (isFinite(yg[i])) { kx.push(xg[i]); ky.push(yg[i]); }
          dash_fit_write(src, ac, kx, ky, null);
  ```
- **TR-19.5 Flips**: `_FROZEN` loses `"lpoly"`; `_REFIT` gains it.
- **TR-19.6 Help**: dash.sthlp:1946 column 2 `lfit, qfit, lfitci, qfitci, lowess, lpoly; others marked`; the paragraph's list loses `{cmd:lpoly},`; add: `An {cmd:lpoly} smooth is refitted with its default bandwidth recomputed from the kept rows; where that bandwidth is Stata's round-off of an exact global fit (y an exact polynomial in x) the saved page draws the line at 0 where {cmd:dash serve} reproduces Stata's value.`
- **TR-19.7 Timing**: `TestTheJsTwinsAreBounded::test_lpoly_under_node_on_1e5_rows[degree]` for degree 0 and 3, default bandwidth, under 2 s each.
- **TR-19.8 Parity corpus**: `_move_case("lpoly, dropdown", _MOVES[0], [_sc(), plot_for("lpoly")])`, `_move_case("lpoly degree(1) bwidth(400) n(20), range", _MOVES[1], [plot_for("lpoly", {"degree": "1", "bwidth": "400", "n": "20"})])`, `_move_case("lpoly biweight degree(3) [aw=weight], slider", _MOVES[2], [plot_for("lpoly", {"kernel": "biweight", "degree": "3", "weight": "aweight", "wexp": "weight"})])`, `_move_case("lpoly gaussian [fw=rep], dropdown", _MOVES[0], [plot_for("lpoly", {"kernel": "gaussian", "weight": "fweight", "wexp": "rep"})])`. The existing "lpoly biweight degree 2, dropdown" case becomes a saved-vs-served refit comparison automatically.
- **TR-19.9 function_test_map.py**: `GlyphMapper._lpoly_grid_plan` -> `test/test_js_fit_refit.py::TestTheConfig::test_lpoly_grid_plan`.

## Boundaries

Do not edit `_compute_lpoly_fit`, `_lpoly_rot_detail`, `_stata_invsym_keep`, `_lpoly_kept_columns`, `_lpoly_se`, `map_lpolyci` (S22), `_KERNELS`, `dash_kernel`'s body, the kdensity branch, `_BRUSH_JS`, S17's colorvar readers, S18's `map_dot`.

## Stata truth

No new extractor (`lpoly_rot_truth.json` and `stat_truth.json` `lpoly` pin the Python twin). Truth block `* ==== S19 F1d: lpoly ====`, helpers `_u19_*`:
- **U19-01** `sysuse auto; dash scatter mpg weight || lpoly mpg weight, filter(foreign, type(dropdown))`; saved moved to Foreign; `lpoly mpg weight if foreign == 1, nograph gen(lx ly) n(50)` -- note `_N` is 74 so n is 50; compare `(lx, ly)` to the saved `(x_lp, y_lp)` at 1e-6 relative; the JS's `h` is not exposed, so `r(bwidth)` is checked through the curves, which agree only when the bandwidth does.
- **U19-02** `lpoly mpg weight, degree(1) bwidth(400) n(20)` with the price range filter to 4500-11385 versus `lpoly ... if inrange(price,4500,11385), degree(1) bwidth(400) n(20) nograph gen(lx ly)`.
- **U19-03** `lpoly mpg weight [aw=displacement], kernel(biweight) degree(2)` dropdown to Domestic versus Stata's `lpoly ... [aw=displacement] if foreign == 0, kernel(biweight) degree(2) nograph gen()`.
- **U19-04** `webuse uslifeexp` (a dataset of 100 rows): `dash lpoly le year, filter(year, type(range))` moved to 1900-1950 versus `lpoly le year if inrange(year,1900,1950), nograph gen()` -- the offset-x case (fixture tolerance 5e-5 for Python; the cscript uses 1e-4).
- **U19-05** a move leaving one row: the saved source is empty; `twoway lpoly mpg weight if price >= 15906` in a `by()`-free context refuses r(2001) -- measured live and recorded, the saved page draws nothing.

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended under `# ---- WP-31 F1d: lpoly ----`)

- Test: `map_lpoly` tags with S10's keys plus `bwidth`, `degree`, `kernel`, `n_dataset`, `n_user` -- `TestTheConfig::test_lpoly_config_keys`, `::test_lpoly_grid_plan` (N < 50 -> N; n(100) on 74 -> 74; default -> 50), `::test_lpoly_empty_layer_is_tagged`.
- Test: `_dash_stale_kind("lpoly")` is None -- `TestStaleKind::test_lpoly_is_refit`.
- Test: the constants table in `_FILTER_JS` equals `_LPOLY_ROT_CONSTANTS` (parse the spliced JSON) -- `TestLpolyTables::test_rot_constants_are_spliced`, `::test_supports_are_spliced`.
- Test: `dash_lpoly_kw` equals `_lpoly_kernel_weights` for the eight kernels at the support's edge (|z| = support gives 0; 0.999 support gives the kernel) -- `TestLpolyKw::test_each_kernel[kernel]`.
- Test: `dash_lpoly_rot` equals `_lpoly_rot_detail(...)["h"]` on every `lpoly_rot_truth.json` row with `class == "exact"` and `kept` all ones (1e-6 relative); rows with a dropped column or `class != "exact"` give NaN or Python's value within 1e-3 (assert one of the two and RECORD which in the test's output, so the divergence count is measured) -- `TestRotTwin::test_fixture_rows[id]`; `::test_overflow_guard` (x = 1e60, degree 0: NaN as Python).
- Test: `dash_lpoly_fit` equals `_compute_lpoly_fit` on the fixture `curves` (bwidth, degree, kernel, idx, w) at 1e-8 relative with NaN equal -- `TestLpolyFitTwin::test_fixture_curves[id]`; the two-distinct-x degree-2 window keeps {1, d^2} (foreign biweight at 287.78) -- `::test_kept_columns_two_values`.
- Test: the branch equals `map_lpoly`'s source for: default, bwidth(400) degree(1) n(20), biweight degree(3) aw, gaussian fw, one row (empty), x of 0/1 only (y = 0 line) -- `TestLpolyBranch::test_matches_python[case]`.
- Test: saved equals served after every `_MOVES` -- `TestTheSavedPageRefits::test_saved_equals_served[lpoly-move]`.
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked[lpoly-*]`.

### Cases in cscripts

- `test_wp31_truth.cscript` U19-01..U19-05.

### Flips

- `_FROZEN` loses lpoly.

### Parity corpus

TR-19.8's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Tagging, grid plan | pytest `TestTheConfig` | -- | saved |
| Tables spliced | pytest `TestLpolyTables` | -- | n/a |
| Kernel, rule of thumb, local fit twins | node `TestLpolyKw`, `TestRotTwin`, `TestLpolyFitTwin` | `lpoly_rot_truth.json`, `stat_truth.json` `lpoly` | n/a |
| Branch vs mapper; saved vs served | node `TestLpolyBranch`; `TestTheSavedPageRefits`; `MOVE_CORPUS` | -- | yes |
| Stata truth | U19-01..05 | live | saved vs lpoly |
| Cost | `TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-19.1** `dash_lpoly_rot` agrees with Python on every exact-class, all-kept fixture row to 1e-6; `dash_lpoly_fit` on every fixture curve to 1e-8; the divergence rows are counted and named in the BUGS.md residual entry.
- **AC-19.2** Saved equals served after every corpus move (1e-8).
- **AC-19.3** lpoly is not marked; the types marked at the section's base, less lpoly, remain marked.
- **AC-19.4** U19-01..05 pass; 1e5-row refits under 2 s at degree 0 and 3.

## Tasks

**Commit boundary.** 19-01 to 19-03 form the F1d commit, subject `Refit lpoly with Stata's rule-of-thumb bandwidth on the saved page (WP-31 F1d)`, on `wp31-s19`. Body as the S10 form with: `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[lpoly-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U19-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- lpoly was frozen because the page did not refit it (F1d)`; `Fixture: none`; `BUGS.md: "<F1d title>" (closed); "lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app" (opened, S3)`; `GAPS3: F1d Tracked` (the Partly-closed form naming the residual, with `commit pending`; the merger's step k.3b fills the sha, DECISIONS A11).

<task type="auto" id="19-01">
  <name>Write the failing lpoly refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the stubs under `# ---- WP-31 F1d: lpoly ----`. `TestRotTwin` loads `test/fixtures/lpoly_rot_truth.json`, and for each row builds x, y from `datasets[row["ds"]]` at `row["idx"]` (the dataset record names its x and y columns; read the fixture's `_meta`/`datasets` layout first and cite it in the test's docstring), w from `row["w"]` (empty string: None; else the named column, normalised as `_dash_lpoly_weights`), runs `dash_lpoly_rot` under node through `run_js(helpers + ...)` and compares with `dr._lpoly_rot_detail(x, y, w, row["degree"], row["kernel"])`: when `detail["route"] == "exact" and all(k == "1" for k in row["kept"])` assert `rel <= 1e-6`; else assert `isnan(js) or abs(js - detail["h"]) <= 1e-3 * abs(detail["h"])` and append the id to a module list `_ROT_DIVERGENT` printed by a final `test_divergence_count_is_recorded` (asserts the list is a subset of the fixture's `divergences` rows plus rows with a dropped column, and writes the count to `<scratch>/19-rot-divergences.txt`). `TestLpolyFitTwin` uses `curves` (`gx` and the recorded curve; `bwidth`, `degree`, `kernel`, `cond`): compare `dash_lpoly_fit(x, y, bwidth, degree, kernel, w, gx)` with `GM._compute_lpoly_fit(x, y, bwidth=..., degree=..., kernel=..., w=..., x_grid=gx)[1]` at `rtol=1e-8, atol=1e-10, equal_nan=True`. Extend `_REFIT` with `"lpoly"`. Run `python3 -m pytest test/test_js_fit_refit.py -k "lpoly or Rot or Lpoly" test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked -q -n0 2>&1 | tee <scratch>/19-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/19-01-failure.txt is at least 20; nothing staged.]]></verify>
  <done>Every F1d regression test exists and fails at the batch-6 base with the text saved.</done>
</task>

<task type="auto" id="19-02">
  <name>Tag lpoly and add its JS twin</name>
  <files>dash_render.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES` gains `"lpoly"`. (2) Refactor `_lpoly_grid_n` (:17079) into `_lpoly_grid_plan` returning `(n, N, user)` with `_lpoly_grid_n` delegating. (3) `map_lpoly` (:17107): move the `bwidth`/`degree`/`kernel` reads and `n_grid, _N, _user = self._lpoly_grid_plan(options, "lpoly", len(x))` above the `len(x) < 2` return; build `_cfg` per TR-19.1; attach on both returns (not recast). (4) At `_FILTER_JS`'s closing `.replace("__DASH_ROW_ID__", ...)` (:25467) chain the two TR-19.2 replacements. (5) Insert before `// DASH_FIT_HELPERS_END`:
```js
// ---- lpoly (S19): Stata's local polynomial smoother and its rule of thumb.
const _DASH_LPOLY_ROT_C = JSON.parse('__DASH_LPOLY_ROT_CONSTANTS__');
const _DASH_LPOLY_SUPPORT = JSON.parse('__DASH_LPOLY_SUPPORT__');
function dash_linspace(lo, hi, n) { const k = Math.max(1, Math.trunc(n)); if (k === 1) return [lo]; const o = new Array(k); for (let i = 0; i < k; i++) o[i] = lo + (hi - lo) * i / (k - 1); o[k - 1] = hi; return o; }
function dash_lpoly_grid_n(nDataset, nUser) { const N = nDataset; if (N < 50) return Math.max(1, N); const n = (nUser === null || nUser === undefined || nUser <= 1) ? 50 : Math.trunc(nUser); return Math.max(1, Math.min(n, N)); }
function dash_lpoly_weights(w, wtype) { return w ? dash_weight_norm(w, wtype, w.length) : null; }   // S10's helper: aw/pw scaled to sum n, fw raw (R2-23)
function dash_lpoly_kw(x, x0, h, kernel) {
    const kfn = dash_kernel(kernel); const sup = _DASH_LPOLY_SUPPORT[kernel];
    return x.map(v => { const z = (v - x0) / h; if (sup !== null && sup !== undefined && !(Math.abs(z) < sup)) return 0; return kfn(z); });
}
// invsym's sweep (_stata_invsym_keep, in float): the columns in `order' first,
// then the largest current pivot (ties to the lowest index); a pivot below
// rel of its own diagonal or below floor is dropped.  Returns the kept
// indices, sorted.
function dash_invsym_keep(G, order, rel, floor) {
    const n = G.length; const S = G.map(r => r.slice()); const d0 = S.map((r, i) => r[i]);
    let rem = []; for (let i = 0; i < n; i++) rem.push(i);
    const kept = [];
    const sweep = (k) => { const piv = S[k][k]; rem = rem.filter(c => c !== k); if (piv > 0 && piv >= rel * d0[k] && piv >= floor) { kept.push(k); for (const i of rem) { if (S[i][k] === 0) continue; const q = S[i][k] / piv; for (const j of rem) S[i][j] -= q * S[k][j]; } } };
    for (const k of (order || [])) if (rem.indexOf(k) >= 0) sweep(k);
    while (rem.length) { let best = rem[0]; for (const c of rem) if (S[c][c] > S[best][best]) best = c; sweep(best); }
    return kept.sort((a, b) => a - b);
}
// _lpoly_kept_columns (D-19.b): every column when a float sweep, intercept
// first, finds every pivot at least 1e-6 of its diagonal and 1e-16; else
// the sweep with invsym's thresholds.
function dash_lpoly_kept(G) {
    const n = G.length; const A = G.map(r => r.slice()); const d0 = A.map((r, i) => r[i]);
    let rem = []; for (let i = 0; i < n; i++) rem.push(i);
    let k = 0;
    while (rem.length) {
        const piv = A[k][k];
        if (!(piv >= 1e-6 * d0[k] && piv >= 1e-16)) return dash_invsym_keep(G, [0], 1e-9, 1e-19);
        rem = rem.filter(c => c !== k);
        for (const i of rem) { const f = A[i][k] / piv; for (let j = 0; j < n; j++) A[i][j] -= f * A[k][j]; }
        if (rem.length) { let best = rem[0]; for (const c of rem) if (A[c][c] > A[best][best]) best = c; k = best; }
    }
    const all = []; for (let i = 0; i < n; i++) all.push(i); return all;
}
// _lpoly_local_wls: the local fit at x0 on the kept columns in powers of
// (x - x0)/h.  {pos, Z, Ainv, beta} or null.
function dash_lpoly_local(x, y, kw, x0, h, degree) {
    const pos = []; for (let i = 0; i < kw.length; i++) if (kw[i] > 0) pos.push(i);
    if (pos.length < 1) return null;
    const p = degree + 1;
    const G = []; for (let a = 0; a < p; a++) G.push(new Array(p).fill(0));
    for (const i of pos) { const d = x[i] - x0; const pw = [1]; for (let a = 1; a < p; a++) pw.push(pw[a - 1] * d); for (let a = 0; a < p; a++) for (let b = 0; b < p; b++) G[a][b] += kw[i] * pw[a] * pw[b]; }
    for (const r of G) for (const v of r) if (!isFinite(v)) return null;
    const K = dash_lpoly_kept(G); if (K.indexOf(0) < 0) return null;
    const Z = pos.map(i => { const d = (x[i] - x0) / h; const pw = [1]; for (let a = 1; a < p; a++) pw.push(pw[a - 1] * d); return K.map(c => pw[c]); });
    const q = K.length; const A = []; for (let a = 0; a < q; a++) A.push(new Array(q).fill(0)); const g = new Array(q).fill(0);
    for (let r = 0; r < pos.length; r++) { const wi = kw[pos[r]]; for (let a = 0; a < q; a++) { g[a] += wi * Z[r][a] * y[pos[r]]; for (let b = 0; b < q; b++) A[a][b] += wi * Z[r][a] * Z[r][b]; } }
    const Ainv = []; for (let c = 0; c < q; c++) { const e = new Array(q).fill(0); e[c] = 1; const col = dash_solve(A, e); if (col === null) return null; Ainv.push(col); }
    const beta = new Array(q).fill(0); for (let a = 0; a < q; a++) for (let b = 0; b < q; b++) beta[a] += Ainv[b][a] * g[b];
    for (const v of beta) if (!isFinite(v)) return null;
    return {pos, Z, Ainv, beta, K};
}
// _compute_lpoly_fit on a given grid: NaN where fewer than two observations
// have positive weight; degree 0 the weighted mean; else the local fit's
// intercept.
function dash_lpoly_fit(x, y, h, degree, kernel, w, xg) {
    return xg.map(x0 => {
        let kw = dash_lpoly_kw(x, x0, h, kernel); if (w) kw = kw.map((v, i) => v * w[i]);
        let cnt = 0, sw = 0, sy = 0; for (let i = 0; i < kw.length; i++) if (kw[i] > 0) { cnt++; sw += kw[i]; sy += kw[i] * y[i]; }
        if (cnt < 2) return NaN;
        if (degree === 0) return sy / sw;
        const m = dash_lpoly_local(x, y, kw, x0, h, degree);
        return m === null ? NaN : m.beta[0];
    });
}
function dash_polyder(a, m) { let c = a.slice(); for (let k = 0; k < m; k++) { const d = []; for (let i = 1; i < c.length; i++) d.push(i * c[i]); c = d.length ? d : [0]; } return c; }
function dash_polyint(a) { const o = [0]; for (let i = 0; i < a.length; i++) o.push(a[i] / (i + 1)); return o; }
function dash_polymul(a, b) { const o = new Array(a.length + b.length - 1).fill(0); for (let i = 0; i < a.length; i++) for (let j = 0; j < b.length; j++) o[i + j] += a[i] * b[j]; return o; }
function dash_polyval(a, z) { let s = 0; for (let i = a.length - 1; i >= 0; i--) s = s * z + a[i]; return s; }
// lpoly's rule of thumb (_lpoly_rot_detail; D-19.a: on the centred and
// scaled design, every column kept): h = C (s2 (u-l) / (W I))^(1/(2pe+3)),
// pe the degree if odd else degree+1, the global fit of degree pe+3, l/u 5%
// in from the ends.  NaN where Stata's r(bwidth) is missing or the design
// is singular (then the caller draws y = 0).
function dash_lpoly_rot(x, y, w, degree, kernel) {
    const n = x.length; if (n < 2) return NaN;
    const ww = w ? w : new Array(n).fill(1);
    const pe = (degree % 2) ? degree : degree + 1; if (pe > 7) return NaN;
    const d = pe + 3;
    let mn = Infinity, mx = -Infinity; for (const v of x) { if (v < mn) mn = v; if (v > mx) mx = v; }
    if (!(mx > mn)) return NaN;
    for (let i = 0; i < n; i++) if (!isFinite(x[i]) || !isFinite(y[i]) || !isFinite(ww[i])) return NaN;
    const rng = mx - mn, l = mn + 0.05 * rng, u = mx - 0.05 * rng;
    // quadcross overflow guard, in log10 (Python _lse).
    const lmax = Math.log10(Number.MAX_VALUE);
    const lse = (vs) => { if (!vs.length) return -Infinity; let top = -Infinity; for (const v of vs) if (v > top) top = v; let s = 0; for (const v of vs) s += Math.pow(10, v - top); return top + Math.log10(s); };
    const pw = [], lw = [], lx = [], ly = [], nzx = [], nzy = [];
    for (let i = 0; i < n; i++) if (ww[i] > 0) { lw.push(Math.log10(ww[i])); const ax = Math.abs(x[i]), ay = Math.abs(y[i]); nzx.push(ax > 0); nzy.push(ay > 0); lx.push(ax > 0 ? Math.log10(ax) : 0); ly.push(ay > 0 ? Math.log10(ay) : 0); }
    if (lse(lw) > lmax) return NaN;
    for (let k = 1; k <= 2 * d; k++) { const t = []; for (let i = 0; i < lw.length; i++) if (nzx[i]) t.push(lw[i] + k * lx[i]); if (lse(t) > lmax) return NaN; }
    for (let k = 0; k <= d; k++) { const t = []; for (let i = 0; i < lw.length; i++) if (k === 0 ? nzy[i] : (nzx[i] && nzy[i])) t.push(lw[i] + k * lx[i] + ly[i]); if (lse(t) > lmax) return NaN; }
    let W = 0; for (const v of ww) W += v;
    let ybar = 0; for (let i = 0; i < n; i++) ybar += ww[i] * y[i]; ybar /= W;
    let vy = 0; for (let i = 0; i < n; i++) vy += ww[i] * (y[i] - ybar) * (y[i] - ybar); vy /= W;
    let ymin = Infinity, ymax = -Infinity; for (const v of y) { if (v < ymin) ymin = v; if (v > ymax) ymax = v; }
    const ycon = ymax === ymin;
    if (!isFinite(vy) || (vy < 2.2250738585072014e-308 && !ycon)) return NaN;
    const c = (mn + mx) / 2, s = (mx - mn) / 2;
    const G = []; for (let a = 0; a <= d; a++) G.push(new Array(d + 1).fill(0)); const g = new Array(d + 1).fill(0);
    for (let i = 0; i < n; i++) { const z = (x[i] - c) / s; const zp = [1]; for (let a = 1; a <= d; a++) zp.push(zp[a - 1] * z); for (let a = 0; a <= d; a++) { g[a] += ww[i] * zp[a] * y[i]; for (let b = 0; b <= d; b++) G[a][b] += ww[i] * zp[a] * zp[b]; } }
    const a = dash_solve(G, g); if (a === null) return NaN;
    let s2 = 0; for (let i = 0; i < n; i++) { const z = (x[i] - c) / s; const r = y[i] - dash_polyval(a, z); s2 += ww[i] * r * r; } s2 /= W;
    if (ycon || s2 <= 1e-24 * vy) return NaN;   // Python's "float" route: Stata's round-off (D-19.a)
    const D = dash_polyder(a, pe + 1).map(v => v / Math.pow(s, pe + 1));
    const Pi = dash_polyint(dash_polymul(D, D));
    const zl = (l - c) / s, zu = (u - c) / s;
    const I = s * (dash_polyval(Pi, zu) - dash_polyval(Pi, zl));
    let dmax2 = 0; for (let k = 0; k <= 200; k++) { const v = dash_polyval(D, zl + (zu - zl) * k / 200); if (v * v > dmax2) dmax2 = v * v; }
    if (!(isFinite(s2) && isFinite(I)) || !(dmax2 >= 2.2250738585072014e-308) || !(I > 0)) return NaN;
    const C = _DASH_LPOLY_ROT_C[kernel + "|" + pe];
    if (C === undefined) return NaN;
    const h = C * Math.pow(s2 * (u - l) / (W * I), 1 / (2 * pe + 3));
    return (isFinite(h) && h > 0) ? h : NaN;
}
```
The three accumulations are plain float64 sums, as D-19.a says. (6) The branch (TR-19.4). (7) function_test_map.py TR-19.9 (a test map; implied by A13). Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_lpoly_rot.py test/test_saved_stale_cue.py test/test_function_test_map.py -q` (test_lpoly_rot.py is the existing Python ROT test file; find it with `ls test/test_lpoly*.py` and run every match).]]></action>
  <verify><![CDATA[Green except the `_FROZEN` lpoly nodes; `python3 -c "import dash_render as d, json; js=d._FILTER_JS; i=js.index('_DASH_LPOLY_ROT_C = JSON.parse(')+len('_DASH_LPOLY_ROT_C = JSON.parse(')+1; t=json.loads(js[i:js.index(\"')\", i)]); print(len(t), t['epanechnikov|1'])"` prints `32 0.7688119451983404`; `<scratch>/19-rot-divergences.txt` exists and names only rows in the fixture's `divergences` or with a dropped column.]]></verify>
  <done>The saved page refits lpoly from the kept rows with Stata's kernel weights, local fits and rule-of-thumb bandwidth, within the documented float divergence.</done>
</task>

<task type="auto" id="19-03">
  <name>Flip, certify, document and commit F1d</name>
  <files>test/test_wp31_truth.cscript, test/test_mode_parity.py, dash.sthlp</files>
  <action><![CDATA[Remove `"lpoly"` from `_FROZEN` (test/test_saved_stale_cue.py, a flipped test). Append TR-19.8's `MOVE_CORPUS` entries under `# WP-31 F1d: lpoly refits on the saved page`. Append the U19 block `* ==== S19 F1d: lpoly ====` (this section's one row, so its one block; helpers `_u19_move`, `_u19_gen_compare` reading `gen(lx ly)` through `Data.get` on the non-missing rows) above the marker line; run `WP31_ONLY=S19 scripts/stata_slot.sh <scratch>/s19 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-19.6 and the conformance pin. Add `test_lpoly_under_node_on_1e5_rows[degree]` to `TestTheJsTwinsAreBounded`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "lpoly or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1d (Resolution names `map_lpoly`, `_lpoly_grid_plan`, `dash_lpoly_*`, the residual sentence "Residual, deferred (WP-31): the rule of thumb on an exactly fitted y, or a design with fewer distinct x than pe+4, draws the line at 0 on the saved page where the served app reproduces Stata's round-off value (GAPS3 F1d Tracked)"); OPEN the residual entry at the end of BUGS.md in the BRIEF's open form, graded S3, pinned by `TestRotTwin::test_divergence_count_is_recorded`; rewrite the GAPS3 F1d Tracked line in the Partly-closed form, writing `commit pending` (the merger's step k.3b fills the sha, DECISIONS A11); replace the `<!-- WP-31 F1d -->` markers (Results: `lpoly on a saved page after a filter move: the build's smooth (marked) -> Stata's local polynomial on the kept rows with its rule-of-thumb bandwidth recomputed (WP-31, F1d)`). Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; slot log `U19-01 ok`..`U19-05 ok`; `git log -1 --format=%s` ends `(WP-31 F1d)`; `grep -c "^- \[ \] Title: lpoly's default bandwidth on an exactly fitted y" BUGS.md` prints 1; `grep -c "F1d Tracked:\*\* Partly closed in WP-31 (section 19, commit pending)" GAPS3.md` prints 1.]]></verify>
  <done>F1d is one green commit: lpoly refits on the saved page with the exact-fit divergence filed as an open residual.</done>
</task>

## Section completion criteria

- AC-19.1 to AC-19.4; `_DASH_JS_REFIT_TYPES` has one member more and `_FROZEN` one fewer than at the section's base (measured there, A33); the two spliced tables parse; the S10 markers intact.
- BUGS.md F1d closed and the residual opened; GAPS3 F1d Tracked in the Partly-closed form with `commit pending`; marker replaced; help updated; one commit.

## Notes

- **Renderer order.** The served app refits lpoly through `_dash_redraw_for` with the Python estimator (exact arithmetic); the saved page uses the float twin. The divergence is D-19.a's and is visible (y = 0 line vs Stata's curve) only on exactly fitted data; the help names it (TR-19.6) per M8.
- **Decisions for maintainer ratification.** D-19.a (float rule of thumb on the scaled design; the exact-fit and dropped-column cases filed as a residual), D-19.b (float invsym sweep in the local fit), D-19.c (`n_dataset` frozen in the config, as `_N` is).
- **R12.** S19 is batch 6's only `_FILTER_JS` editor; S17 and S18 do not touch `map_lpoly` or js_runner.
- **Splice safety.** `json.dumps` output for a dict of str keys and float/None values holds no `'`, so the single-quoted `JSON.parse('...')` literal is safe; `test_rot_constants_are_spliced` re-parses it.
- **Cscript**: `lpoly ..., nograph gen(lx ly)` needs `n()` at most `_N`; `gen()` writes the first n rows; read rows with `lx != .`.
