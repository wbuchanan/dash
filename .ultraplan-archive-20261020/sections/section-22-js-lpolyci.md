# Section 22: lpolyci refit on the saved page

> Part of: WP-31 · GAPS3 rows: F1e · Risk: red · Batch: 7 · Depends on: 19 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U22

## Overview

**What is wrong today.** GAPS3 F1 (GAPS3.md:208): `lpolyci` on a saved page keeps the build's smooth and band after a filter move, dimmed and keyed "(unfiltered)" on both the line and the band; the served app refits both (WP-29 P0.9, `_MOVED_LAYERS` lists lpolyci). At `6370ca4` `map_lpolyci` (dash_render.py:17219-17376) computes the smooth as `map_lpoly` does, the analytic standard error `_lpoly_se(x, y, x_grid, h, hp, degree, kernel, lw, lpvar)` (:22103-22176), `z = _dash_invnormal(.5(1 - level/100) + level/100)` (:22178), and draws through `_render_ci_band` with TWO sources: `line_src({"x_lp", "y_lp"})` with every valid smooth value and `band_src({"x_lp", "y_lp", "y_lower", "y_upper"})` with only the rows where the band is defined. It tags nothing; `_dash_stale_kind("lpolyci")` is `"fit"`.

**After this section** the saved page refits lpolyci: the smooth as S19's `dash_lpoly_fit`, the bandwidth `h` from `bwidth()` or the rule of thumb, the pilot `hp` from `pwidth()` or 1.5 x the rule of thumb (even with `bwidth()`), [R] lpoly eq. 4's standard error `se^2 = [A^-1 B A^-1]_00 sigma^2(x0)` with `A = Z'KwZ`, `B = Z' diag(K_h^2 w) Z`, and `sigma^2` from the degree p+2 pilot fit at `hp` (`sum K_hp w r^2 / (sum K_hp w - tr[(Z'K_hp w Z)^-1 Z' diag(K_hp^2 w) Z])`), or `var()`; a pilot with no residual degrees of freedom (`den <= 1e-10 tot`) pinches (se 0); fewer than two weighted observations in the main or pilot window give a missing se; the overflow guard (`dmax/h` or `dmax/hp` past `sqrt(DBL_MAX)`) gives missing. Both sources are rewritten: the line from every valid grid point, the band from the points where `y_fit`, `se`, `lo` and `hi` are finite. The stale cue stops marking lpolyci.

**Why this row is its own section (red).** Two sources per layer (the agg mechanism registers one source per tagged renderer, so BOTH renderers are tagged, with a `role` key), a sandwich variance with a pilot fit, and the normal quantile, which the page does not yet have.

**Test order and commit rule.** One cycle, one commit `(WP-31 F1e)`: 22-01 failing tests; 22-02 tagging, `dash_invnormal`, `dash_lpoly_se`, the branch; 22-03 flips, truth block, help, close, commit.

### Section decisions (binding on the executor)

- **D-22.a. Two tagged renderers, one computation.** `map_lpolyci` tags the LINE renderer with the full config plus `role: "line"` and the BAND renderer with the same config plus `role: "band"`. The JS branch computes the smooth and se ONCE per config (memoised by `JSON.stringify` of the config minus `role` in a per-run `Map`, `_dash_lpci_cache`, declared beside `agg_configs`), and writes `src` according to `ac.role`: the line's two columns from `valid`, the band's four columns from `banded`. Both renderers are registered by step 3b in `fig.renderers` order (band, its untagged outline, then line: `_render_ci_band` returns `(line_r, band_r)` but draws the band first); the cache makes the order irrelevant. `role` is S22's type-specific config key in S10's D-10.a schema list.
- **D-22.b. The normal quantile is computed, not tabulated.** `dash_invnormal(p)` inverts `dash_norm_cdf(x) = 0.5 * (1 + sign(x) * P(1/2, x^2/2))`, with `P` the regularised lower incomplete gamma by series (x < a+1) or continued fraction (Numerical Recipes `gser`/`gcf`, EPS 3e-16, ITMAX 300, using `dash_lgamma` from S10), by bisection to 1e-13 relative -- the same shape as `dash_t_ppf`. At p = .975 it returns 1.959963984540054 within 1e-14 (Stata's `invnormal(.975)`).
- **D-22.c. The float rule of thumb (S19 D-19.a) governs `h` and `hp` alike**; a NaN rule of thumb draws y = 0 and no band, as Python's `not np.isfinite(h)` path.
- **D-22.d. `lpvar` (`var()`) replaces sigma^2 everywhere**, as `_lpoly_se`'s `var` does; it travels in the config as `lpvar` (float or null).

## Risk: [red] -- a sandwich variance port with a pilot fit, two sources per layer, on top of S19's float divergence

**Why.** The se at a grid point depends on two local fits and a trace; a transposition error gives a plausible band. The two-source registration is new.

**Risk factors.** (1) `Ainv B Ainv` index conventions. (2) The pinch rule and the `den` tolerance. (3) The cache key must exclude `role` and `use`-independent fields only (`use` is per callback, identical for both renderers of one layer). (4) Batch partners S20 (`map_scatter` size path) and S21 (plot-type registration) do not touch lpolyci.

**Mitigation.** (1) `TestLpolySeTwin` runs every case of `lpolyci_truth.json` (`cases`: per id the grid, the se, degree, kernel, bwidth, pwidth, var, weights) against `_lpoly_se` at 1e-8 and against the fixture's Stata se where the fixture's `divergences` (D4) do not name the row. (2) `::test_pinch_rows` asserts se 0 exactly on D4's rows. (3) `TestTheConfig::test_both_renderers_are_tagged_with_roles` and `TestLpolyciBranch::test_the_cache_serves_both_roles`. (4) Boundaries.

## Dependencies

- **Depends on: 19** (`dash_lpoly_kw`, `dash_lpoly_local` (returns `Ainv`, `Z`, `pos`), `dash_lpoly_fit`, `dash_lpoly_rot`, `dash_lpoly_weights`, `dash_lpoly_grid_n`, `dash_linspace`) and through it S10 and S13 (`dash_ci_write`).
- **Blocks: none.**
- **Parallel batch: 7** with S20 and S21; merge order 22, 20, 21. S22 is batch 7's `_FILTER_JS` editor.

## Evidence

- `map_lpolyci` :17219-17376: `_draw(lx, ly, bx, by, blo, bhi)` builds `line_src` and `band_src` and calls `_render_ci_band(..., band_source=band_src)`; `len(x) < 2` -> `_draw([], [], [], [], [], [])`, `_mark_silent`; `_positive("bwidth"|"pwidth"|"lpvar")`; `degree`, `kernel`, `level = _resolve_level(options, self.default_level, "lpolyci")`; `n_grid = self._lpoly_grid_n(...)`; `lw = _dash_lpoly_weights`; `rot = _default_lpoly_bwidth(x, y, lw, degree, kernel)`; `h = bwidth or rot`; `hp = pwidth or 1.5*rot`; `not isfinite(h)` -> zeros line, empty band; `_compute_lpoly_fit`; `se = _lpoly_se(x, y, x_grid, h, hp, degree, kernel, lw, lpvar)`; `z = _dash_invnormal(0.5*(1 - level/100) + level/100)`; `valid = isfinite(y_fit)`; `banded = valid & isfinite(se) & isfinite(lo) & isfinite(hi)`; `_on_axis` on both sets; `_draw`; `_mark_silent` when nothing valid.
- `_lpoly_se` :22103-22176 (the overflow guard `dmax/h <= sqrt(finfo.max)`, `kw = kh*ow`, `< 2 -> continue` (NaN), `kpw = kph*ow`, `< 2 -> continue`, `m = _lpoly_local_wls(x, y, kw, x0, h, degree)`, `B = (Z * (kh[pos]*kw[pos])).T @ Z`, `V00 = (Ainv B Ainv)[0,0]`, `var` or the pilot `p = _lpoly_local_wls(x, y, kpw, x0, hp, degree+2)`, `r = y[ppos] - Zs bs`, `num = sum(kpw[ppos] r^2)`, `Bs = (Zs * (kph[ppos]*kpw[ppos])).T @ Zs`, `tot = sum(kpw[ppos])`, `den = tot - trace(As Bs)`, `den <= 1e-10 tot -> 0`, `s2 = max(num/den, 0)`, `se = sqrt(max(V00,0) s2)` finite else NaN).
- `_dash_invnormal` :22178 (`NormalDist().inv_cdf`). `_LPOLY_DF_TOL = 1e-10` (:22046).
- Fixture `lpolyci_truth.json`: `cases` (keyed by id: `a_d0`, `a_d0_bw100_pw150`, ..., each with the grid, smooth, se, lower/upper, options), `no_df` (the rows per case where Stata's pilot has no df), `divergences` D4, `datasets`, `serset`.
- Pins to flip: `_FROZEN` holds `"lpolyci"`; `test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked` (:242) -- after this section lpolyci is never dimmed: the test is flipped to assert NEITHER renderer is muted after the move (its name kept, docstring reason added); `test_lpolyci_band.py` (the Python band's tests) is untouched.

## User stories

- **US-22.1** As a reader of the saved file, I want the lpoly band to follow the filter, pinching and widening where the kept rows thin out.
- **US-22.2** As a Stata user, I want `pwidth()`, `var()` and `level()` honoured after a move.

## Business requirements

- **BR-22.1** After a move the saved lpolyci line and band equal the served app's to 1e-8 relative (NaN equal) wherever the rule of thumb is a property of the data.
- **BR-22.2** A pilot with no residual degrees of freedom pinches the band; fewer than two weighted observations in either window leave the band missing there.
- **BR-22.3** lpolyci is not marked "(unfiltered)" on the saved page.

## Technical requirements

- **TR-22.1 Tagging.** In `map_lpolyci`'s `_draw` closure, after `_render_ci_band` returns `(line_r, band_r)`: `line_r._dash_agg_source = line_src`, `line_r._dash_agg_config = dict(_cfg, role="line")`, `band_r._dash_agg_source = band_src`, `band_r._dash_agg_config = dict(_cfg, role="band")`, both `._dash_agg_rows = _rows`. `_cfg` and `_rows` are built BEFORE the `len(x) < 2` return: `_cfg = dict(self._fit_agg_config("lpolyci", xvar, yvar, wtype, w, fig, options, ["x_lp", "y_lp", "y_lower", "y_upper"], n_grid, None), bwidth=bwidth, pwidth=pwidth, lpvar=lpvar, degree=int(degree), kernel=str(kernel), level=float(level), n_dataset=int(_N), n_user=(float(_user) if _user is not None else None))` (bwidth/pwidth/lpvar are floats or None already); `_rows = self._agg_member_ids(source, view)`. Note `cols` names the BAND's columns; the line's are the first two.
- **TR-22.2** `_DASH_JS_REFIT_TYPES` gains `"lpolyci"`.
- **TR-22.3 Helpers** before `// DASH_FIT_HELPERS_END` (bodies in 22-02): `dash_gammainc_p(a, x)`, `dash_norm_cdf(x)`, `dash_invnormal(p)`, `dash_lpoly_se(x, y, xg, h, hp, degree, kernel, w, varv)`.
- **TR-22.4 Branch** before `// DASH_FIT_BRANCHES_END`:
  ```js
      } else if (ac.type === 'lpolyci') {
          const key = JSON.stringify(Object.assign({}, ac, {role: null}));
          let R = _dash_lpci_cache.get(key);
          if (!R) {
              const n = fx.length;
              R = {lx: [], ly: [], bx: [], by: [], bl: [], bu: []};
              if (n >= 2) {
                  const lw = dash_lpoly_weights(fw, ac.wtype);
                  const ng = dash_lpoly_grid_n(ac.n_dataset, ac.n_user);
                  const rot = dash_lpoly_rot(fx, fy, lw, ac.degree, ac.kernel);
                  const h = (ac.bwidth !== null && ac.bwidth !== undefined) ? ac.bwidth : rot;
                  const hp = (ac.pwidth !== null && ac.pwidth !== undefined) ? ac.pwidth : 1.5 * rot;
                  let lo = Infinity, hi = -Infinity; for (const v of fx) { if (v < lo) lo = v; if (v > hi) hi = v; }
                  const xg = dash_linspace(lo, hi, ng);
                  if (!isFinite(h)) { R.lx = xg; R.ly = xg.map(() => 0); }
                  else {
                      const yg = dash_lpoly_fit(fx, fy, h, ac.degree, ac.kernel, lw, xg);
                      const se = dash_lpoly_se(fx, fy, xg, h, hp, ac.degree, ac.kernel, lw, ac.lpvar);
                      const z = dash_invnormal(0.5 * (1 - ac.level / 100) + ac.level / 100);
                      for (let i = 0; i < xg.length; i++) {
                          if (!isFinite(yg[i])) continue;
                          R.lx.push(xg[i]); R.ly.push(yg[i]);
                          const l = yg[i] - z * se[i], u = yg[i] + z * se[i];
                          if (isFinite(se[i]) && isFinite(l) && isFinite(u)) { R.bx.push(xg[i]); R.by.push(yg[i]); R.bl.push(l); R.bu.push(u); }
                      }
                  }
              }
              _dash_lpci_cache.set(key, R);
          }
          if (ac.role === "band") dash_ci_write(src, ac, R.bx, R.by, R.bl, R.bu);
          else dash_fit_write(src, Object.assign({}, ac, {cols: ac.cols.slice(0, 2)}), R.lx, R.ly, null);
  ```
  and `const _dash_lpci_cache = new Map();` directly after `const agg_configs = JSON.parse(agg_configs_json);` (:25156) -- outside the helper slice, so `run_fit_js_block`'s harness defines it too (TR-22.5).
- **TR-22.5 js_runner**: `run_fit_js_block`'s harness gains `const _dash_lpci_cache = new Map();` before the loop; a new `run_fit_js_block_roles(ac, x, y, w)` runs the branch twice with `role` "line" and "band" in one harness (two `src` objects) and returns `{"line": ..., "band": ...}`.
- **TR-22.6 Flips**: `_FROZEN` loses `"lpolyci"`; `_REFIT` gains it; :242's test asserts not muted.
- **TR-22.7 Help**: dash.sthlp:1946 column 2 `lfit, qfit, lfitci, qfitci, lowess, lpoly, lpolyci; others marked`; the paragraph's list loses `{cmd:lpolyci},`; the S19 sentence gains `and its confidence band ({cmd:lpolyci}, with {cmd:pwidth()} and {cmd:var()})`.
- **TR-22.8 Timing**: `TestTheJsTwinsAreBounded::test_lpolyci_under_node_on_1e5_rows` under 2 s at degree 0 (the band costs two local fits per grid point: 50 x 2 x 1e5).
- **TR-22.9 Parity corpus**: `_move_case("lpolyci, dropdown", _MOVES[0], [_sc(), plot_for("lpolyci")])`, `_move_case("lpolyci degree(1) bwidth(400) pwidth(600) level(90), range", _MOVES[1], [plot_for("lpolyci", {"degree": "1", "bwidth": "400", "pwidth": "600", "level": "90"})])`, `_move_case("lpolyci var(4) [aw=weight], slider", _MOVES[2], [plot_for("lpolyci", {"lpvar": "4", "weight": "aweight", "wexp": "weight"})])`, `_move_case("lpolyci cosine [fw=rep], dropdown", _MOVES[0], [plot_for("lpolyci", {"kernel": "cosine", "weight": "fweight", "wexp": "rep"})])`.

## Boundaries

Do not edit `_lpoly_se`, `_lpoly_local_wls`, `_dash_invnormal` in Python, `map_lpoly`, S19's helpers' bodies, `_render_ci_band`, S20's `map_scatter`, S21's registration tables, `_BRUSH_JS`.

## Stata truth

No new extractor (`lpolyci_truth.json` pins the Python twin). Truth block `* ==== S22 F1e: lpolyci ====`, helpers `_u22_*`:
- **U22-01** `sysuse auto; dash scatter mpg weight || lpolyci mpg weight, filter(foreign, type(dropdown))`; saved moved to Foreign; `lpoly mpg weight if foreign == 1, ci se(s) nograph gen(lx ly) n(50)`; compare the saved line to `(lx, ly)` and the band to `ly -/+ invnormal(.975)*s` where `s != .`, at 1e-6 relative; where Stata's `s` is missing the saved band has no row at that x.
- **U22-02** `lpolyci mpg weight, degree(1) bwidth(400) pwidth(600) level(90)` with the price range to 4500-11385 versus `lpoly ... if inrange(price,4500,11385), degree(1) bwidth(400) pwidth(600) level(90) ci se(s) nograph gen()`.
- **U22-03** `lpolyci mpg weight [aw=displacement], var(4)` dropdown to Domestic versus Stata with `var(4)`.
- **U22-04** a move leaving two rows at one x: the saved line is empty or y = 0 (as Stata's missing bandwidth gives); recorded live.
- **U22-05** the pinch: `lpolyci mpg weight, bwidth(60) pwidth(60)` dropdown to Foreign: the rows `no_df` names for the full sample are re-measured on the subset (`lpoly ... if foreign == 1, bwidth(60) pwidth(60) ci se(s)`); where Stata's `s` is missing or below 1e-6 the saved band's half-width is 0 or absent (D4's documented rule).

## TDD test stubs

### Regression tests, `test/test_js_fit_refit.py` (appended under `# ---- WP-31 F1e: lpolyci ----`)

- Test: both renderers tagged with the same config apart from `role` -- `TestTheConfig::test_both_renderers_are_tagged_with_roles`, `::test_lpolyci_config_keys` (S19's plus `pwidth`, `lpvar`, `level`), `::test_lpolyci_empty_layer_is_tagged`.
- Test: `_dash_stale_kind("lpolyci")` is None -- `TestStaleKind::test_lpolyci_is_refit`.
- Test: `dash_invnormal(p)` equals `_dash_invnormal(p)` to 1e-13 for p in (.5, .75, .9, .95, .975, .995, .9995) -- `TestInvnormal::test_matches_python[p]`; `dash_gammainc_p` against `math.gamma`-based values at (0.5, 0.5), (0.5, 2), (0.5, 10) -- `::test_gammainc`.
- Test: `dash_lpoly_se` equals `_lpoly_se` on every `lpolyci_truth.json` case (`rtol=1e-8, atol=1e-10, equal_nan=True`) -- `TestLpolySeTwin::test_fixture_cases[id]`; se is exactly 0 on the `no_df` rows -- `::test_pinch_rows[id]`; the overflow guard gives NaN -- `::test_overflow_guard` (x0 = 2200, pwidth 1e-151 on auto, as `_lpoly_se`'s docstring measures).
- Test: the branch's two roles equal `map_lpolyci`'s two sources on: default, degree(1) bwidth pwidth level(90), var(4) aw, cosine fw, one row (both empty), x of 0/1 (zeros line, empty band) -- `TestLpolyciBranch::test_matches_python[case]`, `::test_the_cache_serves_both_roles` (the harness runs the branch twice, once per role, and prints `_dash_lpci_cache.size`: the test asserts it is 1 and that the line's columns equal the band's `x_lp`/`y_lp` on the banded points).
- Test: saved equals served after every `_MOVES` (both sources) -- `TestTheSavedPageRefits::test_saved_equals_served[lpolyci-move]`.
- `test_saved_stale_cue.py::TestARefitLayerIsNeverMarked[lpolyci-*]`.

### Cases in cscripts

- `test_wp31_truth.cscript` U22-01..U22-05.

### Flips

- `_FROZEN` loses lpolyci; :242's test asserts neither renderer muted.

### Parity corpus

TR-22.9's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Two-role tagging | pytest `TestTheConfig` | -- | saved |
| Normal quantile, se twin | node `TestInvnormal`, `TestLpolySeTwin` | `lpolyci_truth.json` | n/a |
| Branch vs mapper; saved vs served | node `TestLpolyciBranch`; `TestTheSavedPageRefits`; `MOVE_CORPUS` | -- | yes |
| Stata truth | U22-01..05 | live | saved vs lpoly, ci se() |
| Cost | `TestTheJsTwinsAreBounded` | -- | n/a |

**Acceptance criteria**
- **AC-22.1** `dash_lpoly_se` agrees with `_lpoly_se` on every fixture case to 1e-8; `dash_invnormal(.975)` is 1.959963984540054 within 1e-14.
- **AC-22.2** Saved equals served after every corpus move (both sources).
- **AC-22.3** lpolyci is not marked; the types marked at the section's base, less lpolyci, remain marked.
- **AC-22.4** U22-01..05 pass; the 1e5-row refit under 2 s.

## Tasks

**Commit boundary.** 22-01 to 22-03 form the F1e commit, subject `Refit lpolyci with its analytic band on the saved page (WP-31 F1e)`, on `wp31-s22`. Body as the S10 form with `Regression: test/test_js_fit_refit.py::TestTheSavedPageRefits::test_saved_equals_served[lpolyci-dropdown to Foreign] -- failed at <base> with <text>`; `Regression: test/test_wp31_truth.cscript U22-01`; `Flipped: test/test_saved_stale_cue.py::_FROZEN -- lpolyci was frozen because the page did not refit it (F1e)`; `Flipped: test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove::test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked -- lpolyci is refitted, so neither source is dimmed (F1e)`; `Fixture: none`; `BUGS.md: "<F1e title>" (closed)`; `GAPS3: F1e Tracked` (Partly closed, with `commit pending` -- the merger's step k.3b fills the sha, DECISIONS A11: the S19 residual applies to lpolyci's bandwidth too; the residual entry's text is widened to name lpolyci in the same commit).

<task type="auto" id="22-01">
  <name>Write the failing lpolyci refit tests</name>
  <files>test/test_js_fit_refit.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[Append the stubs under `# ---- WP-31 F1e: lpolyci ----`. `TestLpolySeTwin` loads `test/fixtures/lpolyci_truth.json`: for each id in `cases`, read the dataset and options (bwidth, pwidth, var, degree, kernel, weights -- the record's keys; read the fixture first and cite them), compute `h`/`hp` as `map_lpolyci` does (rule of thumb through `GM._default_lpoly_bwidth`), run `dash_lpoly_se` under node and compare with `dr._lpoly_se(...)`; `test_pinch_rows` asserts `js_se[k] == 0.0` for k in `no_df[id]`. `TestLpolyciBranch` uses `run_fit_js_block_roles` (ImportError is the expected red). Extend `_REFIT` with `"lpolyci"`. Run `python3 -m pytest test/test_js_fit_refit.py -k "lpolyci or Invnormal or LpolySe" test/test_saved_stale_cue.py::TestARefitLayerIsNeverMarked -q -n0 2>&1 | tee <scratch>/22-01-failure.txt`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED\|ERROR" <scratch>/22-01-failure.txt is at least 20; nothing staged.]]></verify>
  <done>Every F1e regression test exists and fails at the batch-7 base with the text saved.</done>
</task>

<task type="auto" id="22-02">
  <name>Tag lpolyci and add its JS twin</name>
  <files>dash_render.py, test/js_runner.py</files>
  <action><![CDATA[(1) `_DASH_JS_REFIT_TYPES` gains `"lpolyci"`. (2) `map_lpolyci` (:17219): move the option reads (`_positive` calls, `degree`, `kernel`, `level`, `n_grid, _N, _user = self._lpoly_grid_plan(options, "lpolyci", len(x))`) above the `len(x) < 2` return (they read options only; `_positive` warns once per value, unchanged); build `_cfg` and `_rows` (TR-22.1); in `_draw`, after `_render_ci_band` returns, tag both renderers and return them. (3) After `const agg_configs = JSON.parse(agg_configs_json);` add `const _dash_lpci_cache = new Map();`. (4) Insert before `// DASH_FIT_HELPERS_END`:
```js
// ---- lpolyci (S22): the normal quantile and [R] lpoly eq. 4's standard error.
// The regularised lower incomplete gamma P(a, x): series for x < a + 1,
// continued fraction otherwise (EPS 3e-16, 300 terms).
function dash_gammainc_p(a, x) {
    if (!(x > 0)) return 0;
    const gln = dash_lgamma(a);
    if (x < a + 1) {
        let ap = a, sum = 1 / a, del = sum;
        for (let n = 0; n < 300; n++) { ap += 1; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 3e-16) break; }
        return sum * Math.exp(-x + a * Math.log(x) - gln);
    }
    let b = x + 1 - a, c = 1 / 1e-300, d = 1 / b, h = d;
    for (let i = 1; i <= 300; i++) {
        const an = -i * (i - a); b += 2;
        d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300;
        c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300;
        d = 1 / d; const del = d * c; h *= del;
        if (Math.abs(del - 1) < 3e-16) break;
    }
    return 1 - Math.exp(-x + a * Math.log(x) - gln) * h;
}
function dash_norm_cdf(x) { const p = dash_gammainc_p(0.5, x * x / 2); return x >= 0 ? 0.5 * (1 + p) : 0.5 * (1 - p); }
// Stata's invnormal(p): the quantile, by bisection on dash_norm_cdf.
function dash_invnormal(p) {
    if (!(p > 0 && p < 1)) return NaN;
    if (Math.abs(p - 0.5) < 1e-16) return 0;
    let lo = -1, hi = 1;
    while (dash_norm_cdf(lo) > p) { lo *= 2; if (lo < -40) break; }
    while (dash_norm_cdf(hi) < p) { hi *= 2; if (hi > 40) break; }
    for (let i = 0; i < 200; i++) { const mid = 0.5 * (lo + hi); if (dash_norm_cdf(mid) < p) lo = mid; else hi = mid; if (hi - lo < 1e-14 * Math.max(1, Math.abs(mid))) break; }
    return 0.5 * (lo + hi);
}
// _lpoly_se: se^2 = [A^-1 B A^-1]_00 sigma^2(x0), B = Z' diag(K_h^2 w) Z;
// sigma^2 from the degree p+2 pilot at hp (or varv); NaN where fewer than
// two observations have positive main or pilot weight or the scaled
// distance overflows; 0 where the pilot has no residual degrees of freedom.
function dash_lpoly_se(x, y, xg, h, hp, degree, kernel, w, varv) {
    const n = x.length; const ow = w ? w : new Array(n).fill(1);
    const zlim = Math.sqrt(Number.MAX_VALUE);
    return xg.map(x0 => {
        if (!(h > 0 && hp > 0 && isFinite(h) && isFinite(hp))) return NaN;
        let dmax = 0; for (const v of x) { const d = Math.abs(v - x0); if (d > dmax) dmax = d; }
        if (!(dmax / h <= zlim && dmax / hp <= zlim)) return NaN;
        const kh = dash_lpoly_kw(x, x0, h, kernel); const kw = kh.map((v, i) => v * ow[i]);
        let c1 = 0; for (const v of kw) if (v > 0) c1++; if (c1 < 2) return NaN;
        const kph = dash_lpoly_kw(x, x0, hp, kernel); const kpw = kph.map((v, i) => v * ow[i]);
        let c2 = 0; for (const v of kpw) if (v > 0) c2++; if (c2 < 2) return NaN;
        const m = dash_lpoly_local(x, y, kw, x0, h, degree); if (m === null) return NaN;
        const q = m.K.length;
        const B = []; for (let a = 0; a < q; a++) B.push(new Array(q).fill(0));
        for (let r = 0; r < m.pos.length; r++) { const i = m.pos[r]; const u = kh[i] * kw[i]; for (let a = 0; a < q; a++) for (let b = 0; b < q; b++) B[a][b] += u * m.Z[r][a] * m.Z[r][b]; }
        // V00 = sum_a sum_b Ainv[0][a] B[a][b] Ainv[b][0]  (Ainv is symmetric; dash_lpoly_local's Ainv[c] is column c)
        let V00 = 0; for (let a = 0; a < q; a++) for (let b = 0; b < q; b++) V00 += m.Ainv[a][0] * B[a][b] * m.Ainv[b][0];
        let s2;
        if (varv !== null && varv !== undefined) s2 = varv;
        else {
            const p = dash_lpoly_local(x, y, kpw, x0, hp, degree + 2); if (p === null) return NaN;
            const qs = p.K.length;
            let num = 0, tot = 0; const Bs = []; for (let a = 0; a < qs; a++) Bs.push(new Array(qs).fill(0));
            for (let r = 0; r < p.pos.length; r++) { const i = p.pos[r]; let fit = 0; for (let a = 0; a < qs; a++) fit += p.Z[r][a] * p.beta[a]; const res = y[i] - fit; num += kpw[i] * res * res; tot += kpw[i]; const u = kph[i] * kpw[i]; for (let a = 0; a < qs; a++) for (let b = 0; b < qs; b++) Bs[a][b] += u * p.Z[r][a] * p.Z[r][b]; }
            let tr = 0; for (let a = 0; a < qs; a++) for (let b = 0; b < qs; b++) tr += p.Ainv[b][a] * Bs[b][a];
            const den = tot - tr;
            if (!(den > 1e-10 * tot)) return 0;
            s2 = Math.max(num / den, 0);
        }
        const se = Math.sqrt(Math.max(V00, 0) * s2);
        return isFinite(se) ? se : NaN;
    });
}
```
`dash_lpoly_local`'s `Ainv` layout (S19: `Ainv.push(col)` per column c, so `Ainv[c][r]` is row r of column c) is symmetric up to round-off, so `m.Ainv[a][0]` serves both factors of V00 as written, and the trace is `tr(As Bs) = sum_ab As[a][b] Bs[b][a]`. (5) The branch (TR-22.4). (6) js_runner: TR-22.5. Run `python3 -m pytest test/test_js_fit_refit.py test/test_js_runner.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_lpolyci_band.py test/test_saved_stale_cue.py -q`.]]></action>
  <verify><![CDATA[Green except the `_FROZEN` lpolyci nodes and :242 (flipped in 22-03); `node -e "<helpers>; console.log(dash_invnormal(0.975))"` (helpers extracted as in S10's verify) prints 1.959963984540054 (last digit may differ by one unit).]]></verify>
  <done>The saved page refits lpolyci's smooth and analytic band from the kept rows, writing both sources from one computation.</done>
</task>

<task type="auto" id="22-03">
  <name>Flip, certify, document and commit F1e</name>
  <files>test/test_wp31_truth.cscript, test/test_mode_parity.py, dash.sthlp</files>
  <action><![CDATA[Remove `"lpolyci"` from `_FROZEN`; flip :242's test to assert both renderers `muted is False` and no suffix after the move (docstring reason; test/test_saved_stale_cue.py is a flipped test, implied). Append TR-22.9's `MOVE_CORPUS` entries under `# WP-31 F1e: lpolyci refits on the saved page`. Append the U22 block `* ==== S22 F1e: lpolyci ====` (this section's one row, so its one block; helpers `_u22_move_roles` dumping both sources, `_u22_band_compare`) above the marker line; run `WP31_ONLY=S22 scripts/stata_slot.sh <scratch>/s22 <scratch>/run_test_wp31_truth.do`. dash.sthlp TR-22.7 and the conformance pin. Add `test_lpolyci_under_node_on_1e5_rows` to `TestTheJsTwinsAreBounded`. Run `python3 -m pytest test/test_js_fit_refit.py test/test_saved_stale_cue.py test/test_mode_parity.py -k "lpolyci or Refit" test/test_help_conformance.py test/test_estimator_cost.py::TestTheJsTwinsAreBounded -q`. Close BUGS.md F1e; widen the S19 residual entry's Title/Description to "lpoly's and lpolyci's default bandwidth..."; rewrite the GAPS3 F1e Tracked line (Partly closed, naming the residual entry, with `commit pending`; the merger's step k.3b fills the sha, DECISIONS A11); replace the `<!-- WP-31 F1e -->` markers (Results: `lpolyci on a saved page after a filter move: the build's smooth and band (marked) -> lpoly's smooth and its analytic band on the kept rows (WP-31, F1e)`). Grep for `claude|anthropic`; commit.]]></action>
  <verify><![CDATA[pytest green; slot log `U22-01 ok`..`U22-05 ok`; `git log -1 --format=%s` ends `(WP-31 F1e)`; `git log -1 --format=%B | grep -c "^Flipped:"` prints 2; `grep -c "F1e Tracked:\*\* Partly closed in WP-31 (section 22, commit pending)" GAPS3.md` prints 1.]]></verify>
  <done>F1e is one green commit: lpolyci refits with its band on the saved page and is no longer marked.</done>
</task>

## Section completion criteria

- AC-22.1 to AC-22.4; `_DASH_JS_REFIT_TYPES` has one member more and `_FROZEN` one fewer than at the section's base (measured there, A33); `_dash_lpci_cache` declared once in `_FILTER_JS` (after `agg_configs`) and once in `run_fit_js_block`'s harness; the markers intact.
- BUGS.md F1e closed; the S19 residual widened; GAPS3 F1e Tracked in the Partly-closed form with `commit pending`; marker replaced; help updated; one commit.

## Notes

- **Renderer order.** Step 3b registers tagged renderers in `fig.renderers` order: the band (and its outline, untagged) come before the line. The cache makes the computation order irrelevant; `use` is identical for both (same graph).
- **Decisions for maintainer ratification.** D-22.a (two tagged renderers with `role`, a per-run cache), D-22.b (the computed normal quantile).
- **R12.** S22 is batch 7's only `_FILTER_JS`/js_runner editor.
- **Cscript**: `lpoly, ci se(s)` writes the se at the grid rows; `invnormal(.975)` for level 95; compare the band only where `s != .`.

## Addendum (14oct2026, DECISIONS D17): row C11b added to this section

### C11b: lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app

**Gap.** S19's `dash_lpoly_rot` matches the Python twin on the "exact" route (737 fixture rows, 1.8e-10) but not on Python's "float" route (`_lpoly_rot_float`: exactly rounded sums and a float invsym sweep, which reproduce Stata's r(bwidth) where the rule-of-thumb global fit is exact -- y an exact polynomial in x, or no more rows than pe+4). On those 48 fixture rows the JS returns NaN and the saved page draws y = 0 after a move. Pinned by test/test_js_fit_refit.py `_ROT_DIVERGENT_COUNT = 48` (TestRotTwin::test_divergence_count_is_recorded).

**Requirement.** Port `_lpoly_rot_float` to JavaScript so the saved page's default bandwidth equals the served app's on every fixture row (the divergence count goes to 0 and the pin flips), for lpoly and for lpolyci, which this section builds on the same helpers. If a float emulation that agrees across platforms cannot be shown, the saved page instead marks a layer whose rule-of-thumb route is "float" with the existing stale cue after a move (M8: never y = 0 in silence), and the BUGS.md entry closes with that measured limit stated.

**Tests.** test/test_js_fit_refit.py (TestRotTwin, the divergence pin flipped) and a saved-equals-served move case for an exactly fitted y (the 5-row Foreign case S19 pinned at y = 0). One commit, subject ending `(WP-31 C11b)`, after F1e.

**Process (binding).** As every row: failing tests first with saved failure text; close the BUGS.md entry "lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app" (Resolution ending `Closes GAPS3 C11 (WP-31, C11b).`), delete its `"C11b":` WP31_OPEN line, rewrite GAPS3.md's `- **C11b Tracked:**` line to the Closed form with `commit pending`; S19's F1d line is "Partly closed ... (BUGS.md "<this title>")" -- when C11b closes, rewrite F1d's line to the Closed form (BUGS.md F1d entry's title, F1d's landed commit). Replace `<!-- WP-31 C11b -->` under `### Results that change` with a line ending `(WP-31, C11b)`. dash replaces twoway (D13).

