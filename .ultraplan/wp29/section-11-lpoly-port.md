# Section 11: lpoly port: bandwidth and analytic band

> Part of: WP-29 · P0: P0.7 then P0.9 · Risk: red · Batch: 2 · Depends on: 05 · Blocks: 14, 15 (closeout) · Tasks: 24, 2 commits (P0.7, then P0.9) · Case prefixes: LW, LB

## Review amendments (binding; they override any conflicting text below)

This section carries two designs, u07a (P0.7) and u07b (P0.9). Both were reviewed "sound with amendments", and every amendment is folded into the text below. This list is the index:

- **u07a A1 (absolute pivot floor).** Mata `invsym` also drops a column whose current pivot is below 1e-19, whatever its diagonal. `_stata_invsym_keep` applies both the relative rule (1e-9 of the column's own diagonal) and this floor. With the floor, the two "tiny-scale divergences" the design recorded disappear, and Stata's `.` at `weight*1e-6..1e-8` (degree 2/3) and `weight*1e-9` and below is reproduced. No `unverified` fixture section and no help caveat about small x. → TR-11.2; Evidence "x-scale rows".
- **u07a A2 (Part C floor).** The local fit's kept-column rule applies the same floor. → TR-11.6; `TestLocalFitRank::test_tiny_scale_windows_follow_the_absolute_floor`.
- **u07a A3 (overflow guard).** The guard is Stata's `quadcross` overflow, computed in the log domain: NaN when any `sum w|x|^k` (k ≤ 2(pe+3)) or `sum w|x|^k|y|` (k ≤ pe+3) exceeds DBL_MAX. The design's `|x|>1e150` guard is not used. → TR-11.3 step 3.
- **u07a A4 (non-finite and y-scale).** Every non-finite result maps to NaN. NaN always means "Stata's `r(bwidth)` is missing or 0": twoway then draws a line at y=0 on every grid point (measured: `mpg*1e160` degree 2 gives `r(bwidth)=0` and a zero line). There is no "0.0 = draw nothing" sentinel (SD-2). → TR-11.3, TR-11.7.
- **u07a A5 (degenerate rule).** `mx-mn` is not used for exactly-polynomial y. Every exact-fit case (Stata's h is round-off) goes through an emulation of Stata's float64 arithmetic, `_lpoly_rot_float` (SD-2). → TR-11.4.
- **u07a A6 / u07b constant x (lpolyci at a missing bandwidth).** When the resolved h is NaN, `map_lpolyci` draws the y=0 line at every grid point with an EMPTY band and computes no standard error. → TR-11.7, TR-11.15.
- **u07a A7 (strict support).** `_lpoly_rot_constant` masks `|z| < support` itself. Measured below: `_KERNELS['rectangle']` returns 0.5 at |z|=1, and leaving the mask out moves C by -1.2687% (p=1) and -1.3620% (p=3). → TR-11.1; `TestRotConstants::test_support_is_strict`.
- **u07a A8 (served copy safety).** No module-level `Fraction` constant. Tolerances are float default arguments, converted with `Fraction(float)` inside. `fractions` and `statistics` are imported locally inside the helpers, so the served header gains no import. No `assert`: an explicit check returns NaN. → TR-11.9.
- **u07a A9 (%tc).** A `%tc` row (sp500 `close` on `cofd(date)`) joins the fixture. It is tagged `noisy` (5e-5). → Stata truth; `TestRotAgainstStata::test_tc_datetime`.
- **u07a A10 (tests that stay green).** These stay green with Part C: `test_statistical_helpers.py::TestLpolyDegreeAgainstStata` (both tests), `test_statistical_truth.py::TestLpolyDegreeOne`, `::TestLpolyNullRule`, and `test_statistical_defaults.py::test_lpoly_default_bwidth_comes_from_the_data`. → task 11-09 verify.
- **u07b BLOCKER (`lpvar`).** The JSON key for `var()` is `lpvar`, never `var` (index A8). `_dash_extract_vars` (dash_parse.mata:2148-2156) matches `"var":` anywhere in a plot's JSON and adds the value to the variable list. → TR-11.19; LB-41..LB-43.
- **u07b check order.** The refusals run in twoway's measured order. The r(7) checks, the level syntax and range, and pwidth sit in `_dash_fold_bw`. The `var() ≤ 0` check runs after the kernel, bwidth and degree rules of `_dash_validate_opts`. The remaining differences are pinned and documented. → TR-11.18; LB-18.
- **u07b value grammar.** The measured spellings (`1e1`, `9.5d1`, `95 96`, `95.`, `+95`, `95.000`, `10 20`, `800 900`, `price`, `1d3`, `1e-320`) are reproduced. `p(800)` is `pstyle()`, so the minimum abbreviation is `pw`. → TR-11.18; LB-11..LB-19.
- **u07b legend level.** One resolver gives both the level the band is drawn at and the legend key's `"<level>% CI"`. → TR-11.16.
- **u07b empty branch.** The empty layer is built through `_render_ci_band` with the same three sources, so its line carries `lcolor()`/`lpattern()`. → TR-11.15.
- **u07b notes once.** `map_lpolyci`'s notes about a bad spec value use `_dash_warn_once`, keyed by option and value, so a served filter move does not repeat them. → TR-11.15.
- **u07b open question 1 (no residual df).** PINCH: se=0, and the row is kept. NaN only where Stata's se is missing for a structural reason (fewer than two positive main or pilot weights). This section re-measured the rule (Evidence "No-df pilot rows"): Stata's round-off is missing at 9 of 12 such rows on `a_d2`/`a_d3` and tiny at the rest. Pinching is kept as the binding answer. The rows where Stata is missing are documented divergence D4. → TR-11.13.
- **u07b cost test.** The spy/counter tests are primary. The wall-clock bound goes into `test/test_estimator_cost.py` at ≤ 20× `map_lpoly`. That file is outside the manifest's list and is added because of this amendment. → task 11-21.
- **u07b constant x.** `lpoly mpg cx, ci n(5)` with cx≡3000 gives `r(bwidth)=.`, `r(pwidth)=.`, gy=0 and gse=. on every row. dash: no band, no exception, no RankWarning. → TR-11.13; `TestTheVarianceRule::test_constant_x_has_no_band`.
- **u07b zero aweights.** `[aw=price*(rep78>2&rep78<.)]` gives N=59, identical to missing weights. Zero weights are dropped before the mean-1 normalisation. → `TestTheVarianceRule::test_zero_aweights_are_dropped_before_normalising`.
- **Disputes resolved by re-measurement (this section, 30sep2026).** Each is quoted in Evidence:
  - the exact-fit rule (SD-2);
  - the `y*1e-150` rows (D3);
  - the no-df rows (D4);
  - the rank-deficient main window at degree ≥ 2. u07b proposed a NEW open BUGS entry for it. Part C closes it instead: auto `degree(3)` at x=4400 is 7.0604, equal to Stata's, where dash gives −6.6719 today.

## Section decisions (the designs' open questions and plan deviations, settled here)

| Id | Question | Decision | Why / evidence |
|---|---|---|---|
| SD-1 | Accuracy contract. PLAN BR-29.6 asks for 1e-9 relative everywhere. | Tolerance is set per row. `exact` rows (degree 0/1, x centre within 3 half-ranges of 0): 1e-7 relative to `r(bwidth)`. `noisy` rows (degree ≥ 2, or an offset x such as years, dates or `weight+20000`): 5e-5. Stata's own last bits vary between runs (302.44936813331043 without `generate()` vs 302.44936813331037 with it), so nothing is asserted bit-exact. At fixed h and hp the lpolyci band is held at 1e-8. | Measured port-vs-Stata on 398 rows (Evidence "Port accuracy"). `exact` rows reach 4.3e-8 at worst (most ≤ 1e-8; census 7.0e-10, nlsw88 1.2e-9). `noisy` rows reach 1.6e-5 (uslifeexp year, degree 2/3), where Stata's own float64 arithmetic on raw powers is inexact. Handed to S15 to restate BR-29.6. |
| SD-2 | Degenerate cases (u07a open question 1, A4, A5). | (a) Stata missing (`.` or 0) gives NaN, which draws the y=0 line on every grid point, in silence. (b) An exact global fit (y constant, or exact residual variance ≤ 1e-24·var_w(y)) uses `_lpoly_rot_float`, an emulation of Stata's float64 arithmetic. (c) Otherwise the exact rule applies. | (b) reproduces Stata's DRAWN outcome on every measured exact-fit row except D1/D2: ycon, ysq, and `in 1/2..1/5` at degrees 0-3 (Evidence "Exact-fit rows"). |
| SD-3 | Part C (the local fit in rank-deficient windows) lands in P0.7. | Yes. It lands in the P0.7 commit, sharing `_stata_invsym_keep`. P0.9's standard error reuses the same kept set. | It closes the 8.857-mpg error at foreign==1 biweight degree 2, and u07b's proposed open entry (auto degree 3 at x=4400; rep78×1000 degree 2). |
| SD-4 | Rows where the pilot has no residual df. | Pinch (review amendment). | See the Review amendments and D4. |
| SD-5 | `pwidth()`/`var()` on lpoly, scatter, lfitci and kdensity (twoway r(198)). | Keep today's "unsupported option(s)" note. | That is the pending A12 refuse-vs-note decision. Recorded as D9 and handed to S15. |
| SD-6 | `pwidth(+800)` (twoway r(3000) "expression invalid") and `level(99.990)` (r(198), two decimals as typed). | `+800` is accepted as 800, silently, and documented in the help (D8). The `level` decimals rule is matched. | Silent when honoured. The decimals rule is a refusal twoway makes on a value dash would otherwise accept. |
| SD-7 | Constants for pe=5 and 7 (degree 4-7; dash caps degree at 3, `degree=int,0,3`, dash.ado:1900). | Include them in `_LPOLY_ROT_CONSTANTS`, unit-tested against the quadrature only. Fixture rows at degree 4/5 are recorded with `class` `noisy` and a 5e-4 tolerance. They are not used by any drawing path until P1.14. | Measured: the port matches the constants within 2.9e-4 there, which is Stata's own noise. |
| SD-8 | Help accuracy wording (u07a open question 3). | "As Stata computes it". The measured exceptions are listed (D1-D3), with no numeric tolerance in the help. | The tolerances belong to the tests. The user needs the exceptions. |
| SD-9 | Hybrid: pass Stata's `r(bwidth)` from dash.ado (u07a open question 5). | No. | It would add a second source of truth and a Stata call per panel, and cannot help served recomputes (M2). |
| SD-10 | twoway's two-observation rule counts a gaussian weight only above about 1e-14 (measured below). dash counts any positive weight. | Not fixed here: explicit-`bwidth()` behaviour, outside P0.7/P0.9. Handed to S15 as a residual. | g1: `lpoly mpg weight, kernel(gaussian) bwidth(1)` draws 3 points in Stata and 23 in dash. |
| SD-11 | R2 anchor for the new module helpers ("after `_t_ppf` (28569)", which is in `_glyph_layer_lines`' tuple). | They go in `_shared_stat_lines`' function tuple, after `_dash_lpoly_weights` (dash_render.py:28975 at 7421d3d). | Only `_shared_stat_lines`' output is scanned for referenced constants (29006-29035). `_LPOLY_ROT_GRID`/`_LPOLY_ROT_CONSTANTS`/`_LPOLY_DF_TOL` then travel without an explicit list. `_glyph_layer_lines` skips any def `_shared_stat_lines` already emitted (`_emitted_names`, 28532). |
| SD-12 | R2 says to remove `GlyphMapper._bootstrap_ci` once nothing calls it. | Keep it. | qfitci's LinAlgError fallback still calls it (dash_render.py:8980). Only its docstring's lpolyci mention goes. |
| SD-13 | A new BUGS.md entry for Part C (u07a) or for rank-deficient windows (u07b). | None. Each is recorded inside the P0.7 Resolution and CHANGELOG line. | index A4: sections close their own entries in place, with no end-of-file appends. |

## Overview

**P0.7.** DROPIN-REMAINING.md P0.7 (sources GAPS2-A9-a/b, C1, C13, C12-e, AUDIT-24): the lpoly/lpolyci default bandwidth is not Stata's. Today `GlyphMapper._default_lpoly_bwidth` (dash_render.py:9246-9303) computes `0.65·(s²/S)^(1/5)` from a global quartic. It ignores `kernel()` and `degree()` and returns `range/10` below 8 observations. Measured on `sysuse auto`:

- `lpoly mpg weight, kernel(biweight) degree(2)`: dash 63.80, Stata 302.45 (-78.9%). dash draws 34 points where Stata draws 50, with a worst curve error of 39.1 mpg.
- After a served dropdown move to Foreign: dash recomputes 26.88, Stata 287.78 (-90.7%), with 5 points vs 50.
- `in 1/7`: dash 185, Stata 77.35.
- `mpg` on `foreign`: dash draws a 42-point curve between the group means, where twoway draws y=0 from x=0 to x=1.

After P0.7, in both modes and after every served recompute, the default bandwidth is Stata's `r(bwidth)`: for every kernel, degree, weight, `by()` panel and qualifier, as Stata computes it in compiled Mata. That means:

- the per-kernel, per-degree Fan-Gijbels rule;
- the global fit of degree pe+3 in raw powers;
- Stata's `invsym` column dropping, including the 1e-19 floor;
- its overflow;
- its round-off where the fit is exact.

The local fit in rank-deficient windows follows the same `invsym` rule, with the intercept swept first (Part C).

**P0.9.** DROPIN-REMAINING.md P0.9 (AUDIT-23, GAPS2-A10-a/b, C7-a/b/c/e): lpolyci draws a 200-resample bootstrap percentile band. Its width is 0.85-1.55× Stata's at given bandwidths, and its edges are off by up to 44.7 mpg at `degree(1)`. `pwidth()` and `var()` are ignored with a note, and `level(5)` is accepted where twoway refuses it.

After P0.9, the band is lpoly's analytic band ([R] lpoly eq. 4): smooth ± `invnormal(.5(1-level/100)+level/100)`·σ_m(x0). That is a sandwich variance with a degree p+2 pilot fit at `pwidth()` (default 1.5× the rule-of-thumb bandwidth of degree p, even when `bwidth()` is given), or `var()`. It is computed by one Python function in both modes, at build time and in served recomputes.

dash.ado accepts `pwidth()` and `var()` on lpolyci (JSON keys `pwidth`, `lpvar`). It refuses every value and `level()` twoway refuses, with twoway's return code and words, in twoway's order. The bootstrap is gone from lpolyci; it stays only as qfitci's LinAlgError fallback.

**Why one section (index A1).** The two items share:
- `_stata_invsym_keep`;
- the kernel-weight code;
- the default pilot (1.5 × u07a's rule);
- the local fit's kept columns (Part C), which P0.9's standard error must reuse.

P0.9 depends on P0.7 (u07b's dependency), so P0.7 lands first in the same worktree.

**Test order and commit rule (CLAUDE.md rule 7, index step 1).** The section runs two cycles on worktree branch `wp29-s11`:

1. **P0.7 cycle.** Task 11-01 extracts the fixture. Tasks 11-02 and 11-03 write every P0.7 regression test, run it against the batch-2 base and save the failure text to `<scratch>/11-P0.7-failure.txt`. Tasks 11-04 to 11-11 fix, flip, certify and document. Task 11-12 closes the entry and makes the P0.7 commit, subject ending `(WP-29 P0.7)`.
2. **P0.9 cycle.** Tasks 11-13 to 11-15 repeat this on the tree the P0.7 commit leaves, saving `<scratch>/11-P0.9-failure.txt`. Tasks 11-16 to 11-23 fix, flip, certify and document. Task 11-24 makes the P0.9 commit, subject ending `(WP-29 P0.9)`.

No test-only commit exists, and no commit is red.

## Risk: [red] — a numerical port whose exactness rests on reproducing Stata's floating-point column-dropping, and a band change that moves every existing lpolyci and default lpoly dashboard

**Why.**
- Every default lpoly/lpolyci curve in every existing dashboard changes (auto biweight degree 2: 63.8 → 302.4; up to 39 mpg).
- The rule reproduces Stata's arithmetic, including where that arithmetic is round-off.
- The band replaces a bootstrap with a new estimator, changes the layer's source structure (two sources become three), and adds refusals to dash.ado.

**Risk factors.**
1. Borderline column-drop decisions: dash decides on exact pivots, Stata on double-rounded ones.
2. Stata's own noise: up to 1.6e-5 relative on degree 2/3 with year x.
3. Exact-fit rows, where Stata's h is round-off (D1-D3).
4. Served copy omissions surface as NameError at draw time, not at build.
5. Fraction arithmetic on pathological floats.
6. Part C changes values in rank-deficient windows, which existing truth pins must survive.
7. The served zip refresh (dash_render.py:31211-31232) copies sources by position, so drawn and empty branches must yield the same three sources.
8. The `var` key would be read as a variable name by `_dash_extract_vars`. A spec carrying `var(10)` would put `10` in the export variable list used without `confirm variable` (dash.ado:5981-6060, 6957). That is a security-relevant bug.
9. GitNexus has no `dash` index (`list_repos` at plan time lists only `TYME` and `PhotoShootPlannerPro`).

**Mitigation.**
1. The fixture carries per-row `class` and `tol`; `kept` patterns are compared to Stata's own `invsym(quadcross())` diagonals.
2. The tiers of SD-1.
3. Outcome tests (point counts, zero lines) on exact-fit rows. D1-D3 are listed in the fixture's `divergences` and pinned there, so a change is noticed.
4. `TestTheServedAppCarriesTheRule` and `TestTheServedAppCarriesTheBandHelpers` exec the generated app and call the helpers. The two existing guards run in every verify.
5. `pe ≤ 7` is checked; the log-domain overflow guard runs before any Fraction work; `test_never_raises_and_is_fast` bounds N=1e5 under 1 s. Measured 0.268 s at N=1e6, degree 3.
6. A fast path keeps `np.polyfit` on every well-conditioned window (float sweep pivots ≥ 1e-6·diagonal and ≥ 1e-16). Measured: the existing pins are unchanged, and 933 of 1191 windows take the fast path on the truth sets.
7. `TestSources::test_three_sources_drawn_or_empty` and a served move that empties a by() panel.
8. `lpvar` (A8), with `TestNoVarKey` and LB-41.
9. Tasks 11-01 and 11-13 run `npx gitnexus analyze` and then `gitnexus_impact`. Until then the blast radius below is grep-based.

## Dependencies

- **Depends on: S05 (batch 1, u08 date units).**
  - Computed layers on a date x run in Stata units, so `r(bwidth)` on `%td`/`%tc` x, `bwidth()` and `pwidth()` are in days/ms as Stata holds them.
  - The date rows (`sp500 close~date`, `close~cofd(date)`) and LW-05 are gated only by S05 being merged. A test that needs S05's helper (`dr._dash_date_units`, index R2) fails with `pytest.fail("needs S05 (u08 date units)")`, never a skip.
- **Blocks:**
  - S14 (batch 3): its u10 row rule needs lpoly/lpolyci's final inputs;
  - S15 (closeout).
- **Parallel batch:** 2, with S10, S12 and S13. Merge order: S10, S11, S12, S13.
  - S10 edits `dash.ado` option validation and `dash_parse.mata` (`_dash_route_axis2`) and merges first. Its hunks are in other functions. This section's `dash.ado` edits are in `_dash_fold_bw`, `_dash_option_rules`, `_dash_validate_value`, `_dash_validate_opts`' tail and `_dash_plot_opts_to_json`.
  - S12 (stale cue, u14) merges after this section. Its cue must tag lpolyci's NEW band source as well as the line and outline (u07b open question 5). Handed to S12 in Notes.
  - S13 (token) merges last. If it gates `make_document`, it updates `test_mode_parity._served` and this section's served helpers.
- **Why P0.7 before P0.9:** the default pilot is 1.5 × P0.7's rule-of-thumb, and the band's standard error reuses P0.7's local-fit kept set.

## Evidence

Line numbers are `7421d3d`'s. Batch 1 shifts them, so locate everything by symbol. Measurements marked **[s11]** were made for this section on 30sep2026. Planning prototypes live in the session scratchpad and are quoted here, not cited. Stata ran through `scripts/stata_slot.sh`.

### Blast radius (R8; grep-based: GitNexus has no `dash` index)

| Symbol | Callers at 7421d3d | Expected risk |
|---|---|---|
| `GlyphMapper._default_lpoly_bwidth` | `_compute_lpoly_fit` (9348); served staticmethod copy (28998) | LOW |
| `GlyphMapper._compute_lpoly_fit` | `map_lpoly` (9503), `map_lpolyci` (9603, 9619 bootstrap closure); served copy (28999) | MEDIUM |
| `GlyphMapper.map_lpoly` / `map_lpolyci` | dispatch table (24716-24717), served redraw through `agg['redraw']` (31211) | MEDIUM |
| `GlyphMapper._render_ci_band` | lfitci 8873, qfitci 8989, lpolyci 9637, fpfitci 10106 | MEDIUM (optional new parameter only) |
| `GlyphMapper._ci_band_glyphs` | 6275, 8831, 8945, 9561, 10068 | LOW (unchanged) |
| `_resolve_level` | 8861, 8961, 9626, 10093, legend 23632 | MEDIUM (new optional `ptype`) |
| `_dash_fold_bw` (ado) | dash.ado:3952 | MEDIUM |
| `_dash_validate_opts` (ado) | dash.ado:3956 | MEDIUM |
| `_dash_extract_vars` (Mata) | dash.ado:5981, 6957 | unchanged (the key avoids it) |

### P0.7: Stata's rule (lpoly.ado, StataNow 19.5, `/Applications/StataNow/ado/base/l/lpoly.ado`)

What twoway runs:
- `twoway lpoly` and `lpolyci` call `lpoly y x [w] if touse1, n() degree() bwidth() kernel() generate() nograph` (twoway_lpoly_parse.class:90-96; twoway_lpolyci_parse.class:96-106), so the bandwidth is `r(bwidth)` on each view's own sample.
- `by()` is per panel. `twoway lpoly mpg weight, kernel(biweight) degree(2) by(foreign)` has serset 0 equal to `lpoly … if foreign==0` (bw 316.80385769239462) and serset 1 equal to `if foreign==1` (bw 287.77974373265636).

The ado lines that matter:

```stata
297	if `"`weight'"' == "aweight" {
298		summ `wgt' if `touse', meanonly
299		qui replace `wgt' = `wgt'*r(N)/r(sum)
...
305	qui sum `x' if `touse', detail
306	local l = r(min) + 0.05*(r(max) - r(min))
307	local u = r(max) - 0.05*(r(max) - r(min))
...
311	mata: _lpoly_work(`degree',`pwidth', `l', `u', ///
...
315	ret scalar ngrid = r(N)          // the count of NON-MISSING yhat
```

`_lpoly_work` is compiled. The rule below was reverse-engineered from `r(bwidth)` and verified on 525 + 77 + 100 rows (u07a research; review rev-u07a):

- `h = C(K,pe) · [ s²·(u−l) / (W · ∫_l^u m^(pe+1)(x)² dx) ]^(1/(2pe+3))`.
- `pe` = degree if odd, else degree+1 (degree 0 ≡ 1, 2 ≡ 3, 4 ≡ 5, measured exactly).
- `m` is the weighted least-squares fit of degree pe+3 in RAW powers `1, x, …, x^(pe+3)`, solved as `invsym(quadcross(X,w,X))·quadcross(X,w,y)`.
- `s² = Σw r² / Σw`, and `W = Σw` (the fweight sum; N for aweights). There is no density term.
- `invsym` sweeps the largest current pivot first, ties to the lowest index. It drops a column when the pivot is below 1e-9 × that column's original diagonal OR below 1e-19 absolute.
  - Measured: 2×2 `[[1,1],[1,1+e]]` keeps the column at e=1e-9 and drops it at 9.9e-10, at both scales.
  - `invsym(1e-19)` is kept, and the next double below is dropped.
  - `diag(1e10,5e-20)` drops column 2.
  - `(1,1e-6\1e-6,1e-12+5e-20)` drops column 2 at 5e-8 of its diagonal.
  - A greedy-order test kept pattern `101`.
- `C(K,p)` is the Fan-Gijbels `C_{0,p}(K)` by TRAPEZOID quadrature on Stata's grid (half-width, points): epanechnikov (√5, 101), gaussian (5, 101), cosine (0.5, 41), and epan2/biweight/parzen/rectangle/triangle (1, 81). The kernel's support is strict.

**[s11] the constants, computed with dash's own `_KERNELS` and a strict `|z| < support` mask.** They are identical to the research prototype to the last bit:

| kernel | p=1 | p=3 | p=5 | p=7 |
|---|---|---|---|---|
| epanechnikov | 0.7688119451983404 | 1.4510983654380067 | 2.119707526564211 | 2.7849289975849043 |
| epan2 | 1.7193092621259016 | 3.245668826171823 | 4.74230800612505 | 6.232578887244081 |
| biweight | 2.0361684221829894 | 3.6333572150005558 | 5.158207981435779 | 6.659696773488038 |
| cosine | 4.261325461635762 | 7.465910256468045 | 10.516178558247534 | 13.52565407786959 |
| gaussian | 0.7763932398225403 | 1.1605364963657514 | 1.4508015133135794 | 1.7147660572783578 |
| parzen | 2.679241025642047 | 4.354113262700628 | 5.908520000476076 | 7.422676088655606 |
| rectangle | 1.3681484904911154 | 2.849598716697929 | 4.338920614551152 | 5.832847955090462 |
| triangle | 1.8887652986701782 | 3.420486711722465 | 4.917653569707844 | 6.4077843560534875 |

Rectangle without the strict mask: −1.2687% (p=1), −1.3620% (p=3).

### P0.7: Stata, measured values this section pins

| Case | `r(bwidth)` | ngrid |
|---|---|---|
| auto mpg weight, epanechnikov degree 0/1 | 70.642921355391806 | 46 |
| auto mpg weight, biweight degree 2 | 302.44936813331043 | 50 |
| auto mpg weight, gaussian degree 0/1 | 71.3395348813057 | 50 |
| auto mpg weight, gaussian degree 3 | 96.605841168692692 | 50 |
| auto mpg weight `[aw=price]`, degree 0 | 57.6601811789739 | 45 |
| auto mpg weight if foreign==1 / ==0, biweight degree 2 | 287.77974373265636 / 316.80385769239462 | 50 / 50 |
| uslifeexp le year, degree 0/1 / 2/3 | 3.6430833364289748 / 31.878433756089901 | 50 |
| sp500 close date (days), degree 0/1 / 2/3 | 14.545570460491128 / 200.51125382378513 | — |
| sp500 close `cofd(date)` (%tc), degree 0 / 2 | 32504400.964425806 (ngrid 17) / 2274141561.3559403 | — |
| `mpg` on `3+5*foreign`, degree 0 | .187505019578592 (kept 00011) | 10 |
| test_server.py's 30-row frame (`default_rng(42)`), mpg weight | 63.42135953323416 | 27 |
| `mpg` on `foreign`, `one`, or `weight*1e200` | `.`; the smooth is 0 at all 50 grid points | 50 |
| `mpg*1e160` degree 2 | 0; a zero line at 50 points | 50 |

Small samples, `in 1/n` (h, ngrid):

| n | degree 0/1 | degree 2/3 |
|---|---|---|
| 2 | .000664217435613764, 0 | .37008968514260904, 0 |
| 3 | .002112273036104641, 0 | .95459217923479389, 0 |
| 4 | .092964328574340768, 0 | 3.0130769909009119, 0 |
| 5 | .31083794797910769, 0 | 9.2678838025456027, 0 |
| 6 | 24.381543710253624, 0 | 100.6519557736362, 24 |
| 7 | 77.352734999842937, 10 | 80.907491936302563, 11 |
| 8 | 61.647876740894603, 7 | 85.540085515882211, 14 |
| 9 | 56.850040100762691, 10 | 108.53581888156181, 35 |

### P0.7: dash today

dash_render.py:9286-9303, `GlyphMapper._default_lpoly_bwidth`:

```python
        if n < 8:
            return fallback                      # span / 10
        try:
            ww = np.ones(n) if w is None else np.asarray(w, dtype=float)
            n_eff = float(ww.sum())
            coeffs = np.polyfit(x, y, 4, w=np.sqrt(ww))
            resid = y - np.polyval(coeffs, x)
            sigma2 = float(np.dot(ww, resid * resid)) / max(1.0, n_eff - 5)
            d2 = np.polyder(np.poly1d(coeffs), 2)
            denom = float(np.dot(ww, d2(x) ** 2))
            ...
            h = _LPOLY_ROT_C * (sigma2 / denom) ** 0.2     # _LPOLY_ROT_C = 0.65 (:229)
```

Its caller passes neither kernel nor degree (9347-9348): `if bwidth is None or not (bwidth > 0): bwidth = GlyphMapper._default_lpoly_bwidth(x, y, w)`. The local fit drops the top powers by the count of distinct x (9384-9386), which is not Stata's rule (Part C). lpolyci's bootstrap closure passes `bwidth=None` (9617-9622), so each resample derives its own default.

### P0.7 [s11]: port accuracy

The prototype is the exact rule of TR-11.3 with the A1 floor, the A3 overflow guard and SD-2. It was compared on 398 rows: u07a's m1 and m3 sets over auto, census, sp500, nlsw88 and uslifeexp (from the `.dta` files, exact doubles), plus 64 x-scale and 18 y-scale rows from rev-u07a. Relative error against `r(bwidth)` at degree 0-3, excluding exact-fit rows:

| Tier | Rows | Worst |
|---|---|---|
| degree 0/1, centred x | 42 | 4.3e-8 (`in 1/6`); 32 rows ≤ 1e-8; auto 1.9e-10, census 7.0e-10, nlsw88 1.2e-9 |
| degree 0/1, offset x (`weight+20000`, `weight·86400000+1.9e12`, sp500 date) | 8 | 1.1e-6 |
| degree 2/3 | 160 | 1.6e-5 (uslifeexp le/le_male year); auto mpg weight 2.3e-6; `in 1/8` 7.8e-6 |

- On the repository's own CSVs (`test/fixtures/data/*.csv`) against `test_help_claims_6.py::_STATA_ROT`: auto 1.89e-10, census 1.06e-12, sp500 2.16e-11, nlsw88 7.60e-12.
- On `3+5*foreign` the port gives .187505019578595 (1.6e-14).
- Cost: 0.009 s at N=1e3, 0.032 s at 1e5, 0.268 s at 1e6 (degree 3, biweight).

**x-scale rows (A1, A3).**
- `weight·10^k` at degree 0-3: every row matches Stata. That includes `.` at `·1e-6..1e-8` degree 2/3, `·1e-9..1e-100` every degree, `·1e22/1e25/1e30` degree 2 and `·1e35..1e140` degree 0 (the overflow guard).
- The values are within 5e-5 elsewhere. `·1e-5` degree 2: 1.130876e-2 (was −62% without the floor). `·1e-6` degree 0: .00123220251685904.

**y-scale rows (A4).**

| `mpg·s` | Stata d0 | Stata d2 | port |
|---|---|---|---|
| 1e100, 1e150, 1e-100 | 70.6429213547… | 120.792908… | equal within 3e-6 |
| 1e160 | `.` | 0 | NaN, NaN: zero line, matches |
| 1e200, 1e-160, 1e-200, 1e-300 | `.` | `.` | NaN: matches |
| 1e-150 | `.` | 57.50621527011689 (45 points) | d0: NaN, matches (the squared derivative underflows); d2: NaN, Stata 57.506. This is **divergence D3**. |

**Exact-fit rows (SD-2; Stata's h is round-off).** dash's h comes from `_lpoly_rot_float`; the drawn outcome is compared with dash's own `_compute_lpoly_fit` at each h.

| Case | Stata h | dash h | Points, Stata / dash | Curve |
|---|---|---|---|---|
| ycon=5, d0/1 | 397.81 | 137.61 | 50 / 50 | equal (flat) |
| ycon=5, d2/3 | 525.13 | 548.26 | 50 / 50 | equal (flat) |
| ysq=(weight/1000)², d0/1 | .035 | .0419 | 1 / 1 | equal |
| ysq, d2/3 | 535.40 | 482.14 | 50 / 50 | equal to 3.6e-14 |
| `in 1/2..1/5`, d0-3 (16 rows) | .00066 … 9.27 | .00066 … 10.04 | 0 / 0 | — |
| ylin=2·weight+1, d1/2/3 | 155.94 / 706.42 | 115.91 / 571.18 | 50 / 50 | equal to 2e-11 |
| ylin, d0 | 155.94 | 115.91 | 50 / 50 | up to 239 on a range of 6160: **divergence D1** |
| yw=weight, d2/3 | 482.07 | 729.62 | 50 / 50 | equal |
| yw, d1 | 107.65 | 122.11 | 49 / 50 | equal where both are drawn: **divergence D2** (count) |
| yw, d0 | 107.65 | 122.11 | 49 / 50 | up to 36.6: **divergence D2** |

### P0.7 [s11]: Part C, the local fit

Rule (TR-11.6), as follows:
- a degree-0 window keeps Nadaraya-Watson;
- for degree ≥ 1, a fast path keeps today's `np.polyfit` when the float sweep (intercept first, then the largest pivot) keeps every column with every pivot ≥ 1e-6·diagonal and ≥ 1e-16;
- otherwise the kept set is `_stata_invsym_keep(G, order=(0,))` on the raw local Gram, with `m(x0)=b0`.

| Check | Stata | Part C | dash today |
|---|---|---|---|
| foreign==1 biweight degree 2, bw 287.77974373265636, grid indices 41-48 (0-based) | 17.018155991956533, 17.00884440400364, 17.167440598142775, 17.87839549612948, 24.482964137111367, 11.34778718474287, 13.518830077485545, 13.924429919784265 | max error 1.76e-12 | max error 8.857 |
| `test_statistical_helpers.py::TestLpolyDegreeAgainstStata` (rep78, bw .3 degree 1; bw .6 degree 2) | pinned | 4.93e-10, missing rows identical | green |
| `r10=rep78*10`, degree 1, bwidth 3, n(41) | 4564.5 ×4, 5125.75, 5266.0625, 5406.375, 5967.625 | identical | — |
| `mpg` on `weight·s`, bw 300s; s=1e-6 d3, 1e-7 d2/d3 | Stata curves | ≤ 1.6e-13 / 1.14e-12 / 1.13e-12 | 1.43 / 0.873 / 1.43 mpg |
| auto mpg weight degree 3, bw 120.792907978892, x=4400 | 7.0604 | 7.0604 | −6.6719 (u07b) |
| rep78·1000 on price degree 2, bwidth(600) | Stata yhat | max 1.92e-9 | (u07b "unverifiable") |

Cost:
- N=20000, degree 1-3, 50 grid points: Part C 0.021-0.026 s, equal to today (every window on the fast path).
- rep78 at `n(10000)` degree 3 (every window exact): 0.78 s, 0.08 ms per exact window.

### P0.7 [s11]: twoway's two-observation rule with gaussian weights (SD-10, not fixed)

- `lpoly mpg weight, kernel(gaussian) bwidth(1) degree(0|1|2)`: Stata `r(ngrid)=3`, with no zeros. dash draws 23.
- Two observations at distance d from x0, bwidth(1), degree 0: Stata's yhat is finite up to d=7.9 (weight 1.12e-14) and missing from d=7.95.
- With an fweight of 1e6 on the far observation it is finite at d=8.5. So the threshold is on K·w near 1e-14, not a truncation of z.

### P0.9: Stata's band (lpoly.ado:319-324; [R] lpoly eq. 4)

```stata
qui if "`ci'" != "" {
	local prob = 0.5*(1 - `level'/100) + `level'/100
	local crval = invnormal(`prob')
	gen double `cil' = `yhat' -  `crval'*`SE' if `tousegrid'
	gen double `ciu' = `yhat' +  `crval'*`SE' if `tousegrid'
```

The standard error was verified to round-off on 1,599 grid points across 38 cases (u07b; worst band edge 4.9e-12 relative, gaussian 3.4e-9):

- `SE² = [(X'WX)⁻¹ X'W₂X (X'WX)⁻¹]₀₀ · σ²(x0)`, where:
  - X = powers of (x−x0) up to p;
  - W = diag(K·w), W₂ = diag(K²·w);
  - aweights are mean-1 and fweights raw.
- `σ²(x0) = Σ K_p w r² / (Σ K_p w − tr[(X*'W*X*)⁻¹ X*' diag(K_p² w) X*])`. This is a degree p+2 local fit at the pilot `hp`, same kernel. `var(#)` replaces σ².
- The pilot needs two or more positive weights even under `var()` (`bwidth(500) var(10)` degree 1 at x=4588.57: se missing).

Default pilot `hp = 1.5 × rule-of-thumb(degree p)`, even when `bwidth()` is given (`r(pwidth)`):

| Case | bwidth | pwidth |
|---|---|---|
| auto mpg weight | 70.6429213553918 | 105.964382033088 |
| `bwidth(500)` | 500 | 105.964382033088 |
| degree 2/3 | 120.792907978892 | 181.189361968338 |
| gaussian | 71.3395 | 107.0093 |
| biweight degree 1 | 187.0950 | 280.6425 |
| `[aw=price]` | 57.6602 | 86.4903 |
| `[fw=rep78]` | 48.8650 | 73.2975 |
| if foreign==1 | 34.9044 | 52.3566 |
| nlsw88 wage ttl_exp | 0.744013593218203 | 1.1160203898273 |

What twoway draws:
- `twoway lpolyci` draws exactly lpoly's band, stored as floats. Its serset differs from gy±z·gse by at most 5.45e-8 relative.
- Its `rarea` skips rows whose ci is missing and joins their neighbours.
- 2-4 observations with `bwidth(1000)`: the smooth on all 50 grid points, se missing everywhere, rc 0.
- `set level 90` gives z=1.6449. `invnormal(0.975)`=1.959963984540054 equals `statistics.NormalDist().inv_cdf(.975)`.

**[s11] SE with Part C's kept set.** Stata's own h and hp; scaled design on the kept columns:

| Case | Result |
|---|---|
| `a_d2` | se max relative 5.9e-13 |
| `a_d1_bw500_pw800` | 1.5e-13 |
| `rep_d2_bw06` | 3.2e-15 |
| `a_d3` | yhat 6.9e-10; se equal except at no-df rows |
| `r1000_d2_bw600` | yhat 1.92e-9; se equal except at 2 of 50 rows (1243.3323470880446 vs 1238.48; 660.0387356384502 vs 618.55): pilot windows at round-off, **divergence D5** |

**[s11] No-df pilot rows** (σ² = 0/0 in exact arithmetic; dash pinches, SD-4):

| Case | Rows (grid index) | Stata se |
|---|---|---|
| `a_d2` | 44-49 | missing at 44, 45, 47, 48, 49; 6.684e-6 at 46 |
| `a_d3` | 44-49 | missing at 44, 45, 46, 49; 32.01627014879946 at 47; 1.379e-7 at 48 |
| qualified_stat_truth `foreign1` | x 1760, 1861.6, 2403.7, 2606.9 | 1.9e-7 to 2.1e-6: twoway's band pinches |

### P0.9: option values, twoway (StataNow 19.5, `twoway lpolyci mpg weight, <opts> nodraw`)

| Option | rc | Message |
|---|---|---|
| `level(5)`, `(9.99)`, `(99.995)`, `(100)`, `(0)`, `(-95)`, `(.95)` | 198 | `level() must be between 10 and 99.99 inclusive` |
| `level(10)`, `(99.99)`, `(10.0)`, `(95.)`, `(+95)`, `(95.00)` | 0 | |
| `level(99.990)`, `(95.000)` | 198 | `level() can have at most two digits after the decimal point` |
| `level(1e1)`, `(9.5d1)` | 198 | `<text> found where number expected` |
| `level(abc)` | 7 | `'abc' found where number expected` |
| `level(95 96)` | 7 | `'96' found where nothing expected` |
| `pwidth(0)`, `(-1)`, `(abc)`, `(.)`, `(800 900)`, `(price)` | 198 | `pwidth() must be a positive number` |
| `pwidth(1e-300)`, `(1e-320)`, `(1e3)`, `(.5e3)`, `(1d3)` | 0 | (1e-300: se missing everywhere) |
| `pwidth(+800)` | 3000 | `expression invalid` (D8) |
| `var(0)`, `(-1)` | 198 | `var() must be a positive number` |
| `var(abc)`, `(price)`, `(.)` | 7 | `'abc' found where number expected` |
| `var(10 20)` | 7 | `'20' found where nothing expected` |
| `var(8e307)`, `(1e1)`, `(1d1)`, `(+10)`, `(1e-320)` | 0 | (8e307: se 2.8e153) |
| `pwidth()` / `var()` twice | 198 | `option pwidth() not allowed` / `option var() not allowed` |
| `pw(800)`, `v(10)` | 0 | `p(800)` is `pstyle()`: `named style 800 not found` |
| `pwidth()` or `var()` on lpoly, scatter, lfitci, kdensity | 198 | `option pwidth() not allowed` |

Order, measured:

| Options | twoway's result |
|---|---|
| `level(5) var(abc)` | r(7) |
| `pwidth(0) var(0)` | pwidth message |
| `level(5) pwidth(0)` | level message |
| `level(5) degree(abc)`, `level(5) degree(1.5)` | `option degree() not allowed` |
| `level(5) n(abc)`, `pwidth(0) n(abc)` | `option n() not allowed` |
| `pwidth(0) degree(-1)`, `pwidth(0) n(-1)`, `pwidth(0) kernel(foo)` | pwidth message |
| `level(5) kernel(foo)`, `bwidth(0) level(5)`, `level(5) bwidth(abc)` | level message |
| `var(0) bwidth(0)` | bwidth message |
| `var(0) kernel(foo)` | `invalid kernel function` |
| `var(0) degree(-1)` | `degree() must be a nonnegative number` |
| `if _n==1, pwidth(0)` | r(2001) `insufficient observations` |
| `if _n<=2, pwidth(0)` | pwidth message |
| `if _n==0, level(5)` | level message |

dash today, for comparison:
- `pwidth()`/`var()` are named "dash: ignoring unsupported option(s)" with rc 0, even for invalid values.
- `level(5)` and `level(99.995)` give rc 0 (`level=num,0,100,x`, dash.ado:1899).
- `degree(abc)` gives `dash: degree() must be an integer between 0 and 3 (got: abc). …` r(198).

### P0.9: dash today

`map_lpolyci` (dash_render.py:9525-9644) calls `GlyphMapper._bootstrap_ci` (9624-9628): 200 resamples on seed 42 (`jitterseed()`), a percentile band, with NaN predictions replaced by the point estimate.

| Case | Band width, dash / Stata | Worst edge error (mpg) |
|---|---|---|
| bwidth(500) pwidth(800) | 0.85-1.55 | 0.759 |
| degree(1) | 0.00-9.17 | 44.68 (at x=3080 the lower edge is −28.0 vs 16.68) |
| level(90) | 0.26-1.32 | 3.344 |
| served, after a move to Foreign | 0.29-1.31 | 4.325 |

- Cost at N=20000: 4.23 s, against 0.022 s for lpoly.
- `len(x) < 3` returns an empty layer (9558), so two observations at `bwidth(1000)` draw nothing where twoway draws the smooth.
- The empty branch (9559-9570) builds one shared empty source, skips `_apply_line_opts`, and yields 2 sources where the drawn branch yields 2 (the shared ci source and the outline). After the split the count is 3.

### Tests that pin today's behaviour (flip, never delete; R7)

P0.7:
- `test/test_help_claims_6.py::TestDefaultBandwidth::test_the_rule_is_the_one_the_help_writes_down` (:1014): pins `_LPOLY_ROT_C == 0.65` and the quartic. It becomes "the rule is Stata's" on the eight `_STATA_ROT` cases at ≤ 1e-8. Measured on the repository CSVs: 1.9e-10 at worst. The `in 1/7` case is `noisy`, ≤ 5e-5.
- `::test_the_gap_to_statas_rule_is_the_one_the_help_gives` (:1027): pins −9.7/−22/−17/+5.7/+6.8/+14.2%. It becomes `abs(rel) <= 1e-8` on the same keys (`_HELP_PCT` is deleted; `_STATA_ROT` stays as truth).
- `::test_below_eight_observations_it_is_a_tenth_of_the_range` (:1034): pins `range/10` and 185. It becomes the `in 1/2..1/7` outcomes: `in 1/7` h = 77.35273499984294 (noisy tolerance), drawn points 10 at n_grid 50; `in 1/2..1/5` draw nothing.
- `::test_the_help_gives_those_numbers` (:1043): pins "9.7% below" … "185 against Stata's 77.4". It becomes the new paragraph's sentences (TR-11.11).
- `test/test_statistical_truth.py::TestLpolyAgainstStata::test_default_bandwidth_is_within_the_documented_tolerance` (:398): pins worst ≤ 20%. It becomes ≤ 1e-8 on the four `<ds>:default` rows.
- `test/test_server.py::TestServerLpolyFpfit::test_lpoly_make_document_runs` (:3669): pins `len(served[""]) == 21`. Stata's `r(ngrid)` on that frame is 27 (h 63.42135953323416). Flip to 27. The docstring's "21 of them" becomes 27.
- `test/function_test_map.py:133` (`GlyphMapper._compute_lpoly_fit`) and `:135` (`GlyphMapper._default_lpoly_bwidth`) point at the new tests. New names are added (TR-11.10).
- `test/test_mode_parity.py:2665-2680` (`TestTheCopiedHelpersBringTheirCallees` docstring names `_LPOLY_ROT_C`): text only.

P0.9:
- `test/test_help_claims_6.py::TestLpolyciBand::test_every_resample_is_evaluated_on_the_drawn_grid` (:651): asserts 200 resamples. It becomes `test_no_resample_is_drawn`: the spy sees exactly one `_compute_lpoly_fit` call, and `_bootstrap_ci` is never called.
- `::test_the_line_is_statas_and_the_band_is_not[saved|served]` (:682): asserts `abs(y_lower − 26.2413) > 0.1`. It becomes `test_the_line_and_band_are_statas`: first row 26.2413063049316 … 29.4909420013428 at rtol 1e-6 (twoway's float serset, `bwidth(400)`, default pilot). The class docstring is rewritten.
- `test/test_help_claims_6.cscript` HC6-24: `dash lpolyci mpg weight, level(5)` rc 0 becomes r(198) with twoway's message. HC6-55: the pairs `lpolyci mpg weight|pwidth(500)|pwidth` and `|var(2)|var` are removed, and HC6-55b is added (honoured, no note).
- `test/test_lpolyci_options.py`: the module docstring (:22-23, "The bootstrap resamples …") and the comments at about :85 and :161 describe the bootstrap. Text only. `TestTheBandSurroundsTheLineThatIsDrawn::test_the_ci_brackets_the_fit` keeps its assertion and finds the 4-column band source.
- `test/test_option_validation.py::CONTRACT_PLOT_RULES` (:69-83) is a pinned copy of the plot rule table. It gains `level=num,10,99.99@lpolyci` before `level=num,0,100,x`.
- `test/function_test_map.py:592` (`_resolve_seed` → the bootstrap seed test) is unchanged. `:128` `GlyphMapper._bootstrap_ci` stays (qfitci).
- Re-run, not flip, expected green: `test_layer_reports.py::TestASmootherTwowayDrawsInSilenceIsSilent::test_two_or_three_observations[lpolyci]` (notes stay []), and `test_help_claims_7.py::TestJitter::test_the_types_jitter_moves[lpolyci-saved]`.

## User stories

- **US-11.1** As an analyst, I want `lpoly`/`lpolyci` with no `bwidth()` to use the bandwidth Stata's `lpoly` reports, for my kernel, degree, weights, `by()` panel and qualifier, so the curve I publish from dash is the one Stata draws.
- **US-11.2** As a dashboard reader of a served app, I want the default bandwidth recomputed from the rows a filter keeps, so the smooth after a move is `lpoly … if <filter>`.
- **US-11.3** As a twoway user, I want the edge cases drawn as twoway draws them: a 0/1 or constant x gives a line at 0, too few points give nothing, and a constant y gives a flat line.
- **US-11.4** As an analyst, I want `lpolyci`'s band to be Stata's analytic band, honouring `pwidth()`, `var()` and `level()`, so I can report the interval dash shows.
- **US-11.5** As a twoway user, I want every `pwidth()`, `var()` and `level()` value twoway refuses on lpolyci refused with twoway's return code and words, and every value it accepts accepted.
- **US-11.6** As the maintainer, I want every number pinned to a Stata fixture or a live Stata block, so the port cannot drift unnoticed.

## Business requirements

- **BR-11.1** With no `bwidth()`, the lpoly/lpolyci bandwidth equals Stata's `r(bwidth)` for the layer's own sample, within SD-1's tolerance, for every kernel, degree 0-3, aweight and fweight, by() panel, per-plot qualifier and linked qualifier, in both modes and after every served recompute.
- **BR-11.2** Where Stata's `r(bwidth)` is missing or 0, dash draws y=0 at every grid point and says nothing. Where Stata's value is round-off of an exact fit, dash draws Stata's outcome, except the documented divergences D1-D3.
- **BR-11.3** At a given bandwidth, the local fit equals Stata's `lpoly … generate()` at every grid point, including windows whose design is rank-deficient or below `invsym`'s floor.
- **BR-11.4** The lpolyci band at given `bwidth()`/`pwidth()` (or `var()`) equals `lpoly …, ci` within 1e-8 × max(1,|y|), at every grid point where Stata's se is defined and non-round-off. Rows with fewer than two positive main or pilot weights have no band. Rows whose pilot has no residual df are pinched (D4). At the default bandwidths the band is as exact as BR-11.1.
- **BR-11.5** `level()` on lpolyci is 10 to 99.99 with at most two decimals. `pwidth()` and `var()` are positive numbers. Each refusal matches twoway's rc and words, in twoway's order except D6/D7. The legend key reads the level the band is drawn at.
- **BR-11.6** No bootstrap is run for lpolyci. A served filter move costs at most a few lpoly fits.
- **BR-11.7** No input (hostile spec values, extreme scales, NaN, inf) raises out of the renderer or the served session, or puts a non-finite number in a source.
- **BR-11.8** CHANGELOG "Results that change" names each changed result with the command, the old value and the new.

## Technical requirements

### P0.7 (default bandwidth and the local fit)

- **TR-11.1 Constants and the kernel constant.** In dash_render.py, replace `_LPOLY_ROT_C` (:227-229) in place with:
  - `_LPOLY_ROT_GRID = {"epanechnikov": (math.sqrt(5.0), 101), "gaussian": (5.0, 101), "cosine": (0.5, 41), "epan2": (1.0, 81), "biweight": (1.0, 81), "parzen": (1.0, 81), "rectangle": (1.0, 81), "triangle": (1.0, 81)}`;
  - `_LPOLY_ROT_CONSTANTS = {(kernel, p): value}` for p in 1, 3, 5, 7, the 32 values of the Evidence table pasted as `repr(_lpoly_rot_constant(k, p))`.

  Add `def _lpoly_rot_constant(kernel: str, pe: int) -> float` beside `_KERNELS` (after its closing brace, :13222). It computes:
  - `z = np.linspace(-L, L, m)`, trapezoid weights `wq` (h at the interior, h/2 at both ends);
  - `f = np.where(np.abs(z) < support, kfn(z), 0.0)` from `_KERNELS` (strict mask; gaussian support `inf` masks nothing);
  - moments `mu_j = Σ wq z^j f` for j ≤ 2pe+2;
  - `S = [mu_{i+j}]`, i, j ≤ pe; `e = solve(S, e1)`; `K* = (Σ e_j z^j) f`;
  - `C = [((pe+1)!)² Σwq K*² / (2(pe+1) (Σ wq z^(pe+1) K*)²)]^(1/(2pe+3))`, with `math.factorial`.

  An unknown kernel uses epanechnikov's grid. `_default_lpoly_bwidth` reads `_LPOLY_ROT_CONSTANTS.get((kernel, pe))` and falls back to the function.
- **TR-11.2 `_stata_invsym_keep(G, order=(), rel=1e-9, floor=1e-19) -> list`** (module level, after `_lpoly_rot_constant`):
  - Inside: `from fractions import Fraction`. `S = [[Fraction(float(v)) for v in row] for row in G]`; `d0 = [S[i][i] …]`; `relF, floorF = Fraction(rel), Fraction(floor)` (the exact values of the doubles 1e-9 and 1e-19).
  - Sweep the `order` columns first, in that order, skipping any out of range. Then repeatedly take the remaining column with the largest current `S[k][k]`, ties to the lowest index.
  - A column is kept when `piv > 0 and piv >= relF*d0[k] and piv >= floorF`. When kept, eliminate it from the remaining rows and columns: `S[i][j] -= S[i][k]/piv * S[k][j]`.
  - Return `sorted(kept)`.
  - No module-level Fraction exists (A8). Cost O(d³) on at most 11×11.
- **TR-11.3 `GlyphMapper._default_lpoly_bwidth(x, y, w=None, degree=0, kernel="epanechnikov") -> float`** (signature extended; a staticmethod as today) returns `_lpoly_rot_detail(x, y, w, degree, kernel)["h"]`. The new module function `_lpoly_rot_detail(...) -> dict` returns `{"h": float, "route": "exact"|"float"|"missing", "kept": list}`, computed in order:
  1. `x, y, w` to float arrays (`w` None → ones). NaN if `n < 2`, any value is non-finite, or `pe = degree if degree % 2 else degree + 1` exceeds 7 (an explicit check, no assert). `d = pe + 3`.
  2. `mn, mx` from x; NaN if `not mx > mn`. `rng = mx − mn; l = mn + 0.05*rng; u = mx − 0.05*rng`, computed in float64 exactly as lpoly.ado:306-307.
  3. Overflow guard (A3), in log10. With `lx = log10|x|` over x≠0, `lw = log10 w`, `ly = log10|y|`, the result is NaN if `logsumexp10(lw + k·lx) > log10(DBL_MAX)` for any k in 0..2d, or `logsumexp10(lw + k·lx + ly)` over rows with y≠0 exceeds it for any k in 0..d. Compute the logs once.
  4. `W = Σw; ȳ = Σwy/W; vy = Σw(y−ȳ)²/W` under `np.errstate(all="ignore")`. `ycon = (y.max() == y.min())`. NaN if `vy` is not finite, or `vy < sys.float_info.min and not ycon`.
  5. Exact path:
     - `c = (mn+mx)/2; s = (mx−mn)/2; z = (x−c)/s; V = np.vander(z, d+1, increasing=True); Gz = (V*w[:,None]).T @ V; gz = (V*w[:,None]).T @ y`.
     - `T[j][k] = comb(k, j)·c^(k−j)·s^j` as Fractions of the floats; `G = Tᵀ Gz T`, `g = Tᵀ gz` exactly (G is the raw-power Gram `quadcross` builds).
     - `K = _stata_invsym_keep(G)`. Solve `G[K,K] b = g[K]` exactly (Gauss-Jordan on Fractions with partial pivoting by |value|).
     - `a = T[:,K] b` gives the z-basis coefficients; `af = float(a)`.
  6. With `r = y − V@af`: `s2 = Σw r²/W`; `D = polyder(af, pe+1)/s^(pe+1)`; `I = s·(P(zu) − P(zl))` with `P = polyint(D·D)` and `zl, zu = (l−c)/s, (u−c)/s`; `dmax2 = max over 201 equally spaced z in [zl, zu] of D(z)²`.
  7. If `ycon or s2 <= 1e-24*vy` (an exact fit), return `route="float"` with `h = _lpoly_rot_float(x, y, w, pe, l, u, C)` (NaN if it is not finite and positive) (TR-11.4).
  8. NaN (route `missing`) if `s2` or `I` is not finite, `dmax2 < sys.float_info.min`, or `not I > 0`.
  9. Otherwise `h = C·(s2·(u−l)/(W·I))^(1/(2pe+3))`, with `C = _LPOLY_ROT_CONSTANTS.get((kernel, pe))` or `_lpoly_rot_constant(kernel, pe)`. Return it if finite and > 0, else NaN.

  The whole body sits in `try: … except (ArithmeticError, ValueError, np.linalg.LinAlgError): NaN`, under `np.errstate(all="ignore")`. It never raises and never warns (no `np.polyfit`, so no RankWarning).
- **TR-11.4 `_lpoly_rot_float(x, y, w, pe, l, u, C) -> float`.** It emulates Stata's float64 path for exact fits (SD-2):
  - `X[:,k] = x**k` for k ≤ pe+3; `G[i][j] = math.fsum(w*X[:,i]*X[:,j])`, `g[i] = math.fsum(w*X[:,i]*y)`.
  - A float sweep in largest-current-pivot order (ties to the lowest index). Drop when `not (piv > 0 and piv >= 1e-9*d0[k] and piv >= 1e-19)`: zero row and column k. When kept: `A -= outer(col,row)/piv; A[k,:] = row/piv; A[:,k] = col/piv; A[k,k] = −1/piv`.
  - `b = (−A) @ g`; `r = y − X@b`; `s2 = Σw r²/Σw`; `Dc = polyder(b, pe+1)`; `I = P(u) − P(l)`, `P = polyint(Dc·Dc)` in raw x.
  - `h = C·(s2(u−l)/(W·I))^(1/(2pe+3))` if `I > 0`, else NaN. Non-finite becomes NaN.
- **TR-11.5 Weights.** The rule receives `_dash_lpoly_weights(w, wtype)` (aweights mean-1 after `_layer_weights` dropped zero/missing weights; fweights raw), unchanged (dash_render.py:13485-13494).
- **TR-11.6 Part C, the local fit.** `_lpoly_kept_columns(G) -> list` (module level):
  - Run a float sweep on G, intercept first, then the largest pivot. If every pivot satisfies `piv >= 1e-6*G[k][k] and piv >= 1e-16`, return all columns.
  - Otherwise return `_stata_invsym_keep(G, order=(0,))`.

  In `_compute_lpoly_fit` (9306-9407), for each grid point with ≥ 2 positive weights and `degree ≥ 1`:
  - `dd = x[pos] − x0`; `X = np.vander(dd, degree+1, increasing=True)`; `G = (X*kw[pos,None]).T @ X`; `K = _lpoly_kept_columns(G)`.
  - `len(K) == degree+1`: today's `np.polyfit(x[pos], y[pos], deg=degree, w=np.sqrt(kw[pos]))`, evaluated at x0 (existing pins unchanged).
  - `0 not in K`: NaN (unmeasured; Notes).
  - Otherwise `b = np.linalg.solve(G[K,K], g[K])` with `g = (X*kw[pos,None]).T @ y[pos]`, and `y_fit = b[0]`.

  The `min(degree, distinct−1)` reduction (9384-9386) is deleted. Degree 0 keeps Nadaraya-Watson. The default call (9347-9348) becomes `GlyphMapper._default_lpoly_bwidth(x, y, w, degree, kernel)`, and a NaN bandwidth there returns a NaN `y_fit` everywhere (callers decide, TR-11.7). The kernel loop (9363-9372) moves into `_lpoly_kernel_weights` in P0.9 (TR-11.12) and is kept inline for now.
- **TR-11.7 Callers.** `map_lpoly` (9437-9522) and `map_lpolyci` (9525-9644) resolve `bw` once, after `_layer_weights`, as the user's `bwidth()` if > 0, else `GlyphMapper._default_lpoly_bwidth(x, y, lw, degree, kernel)`, where `lw = _dash_lpoly_weights(w, wtype)` on the layer's own masked rows (per-plot if/in, by() panel, linked qualifier). Then:
  - if `bw` is NaN: `x_grid = np.linspace(x.min(), x.max(), n_grid)` with `n_grid = self._lpoly_grid_n(...)` and `y_fit = np.zeros(n_grid)`. The line is drawn with no note: `_mark_silent` is NOT called, because twoway draws a line. lpolyci's band is empty and its se is not computed;
  - otherwise `_compute_lpoly_fit(x, y, bwidth=bw, …)`.

  In P0.7, the lpolyci bootstrap closure (9617-9622) receives `bwidth=bw` (the number) until P0.9 removes it. Update `map_lpoly`'s docstring (:9458-9461 says "default 0.5").
- **TR-11.8 Served app.** `_default_lpoly_bwidth` and `_compute_lpoly_fit` stay in `_shared_stat_lines`' staticmethod tuple (28997-29001). In the function tuple (28950-28986), add `_lpoly_rot_constant, _stata_invsym_keep, _lpoly_rot_detail, _lpoly_rot_float, _lpoly_kept_columns` directly after `_dash_lpoly_weights` (SD-11). Remove `"_LPOLY_ROT_C"` from the constants tuple (28364). The scanner (29006-29035) writes `_LPOLY_ROT_GRID` and `_LPOLY_ROT_CONSTANTS` (literal dict/tuple reprs round-trip; tested). Update the comments that name `_LPOLY_ROT_C` (29013, 31741-31742; test_mode_parity.py:2665-2680 docstring).
- **TR-11.9 Security (rule 1).**
  - The rule reads only numeric arrays.
  - `degree` is bounded (0-3 by dash.ado's `degree=int,0,3` and `_stat_option_float(hi=3)`); pe ≤ 7 is checked explicitly.
  - `kernel` is checked against `_KERNELS`, with the existing epanechnikov fallback and note.
  - Overflow and underflow give NaN; exceptions are contained; nothing raises into a render or a served callback.
  - No I/O, network or user string.
  - The exact path is bounded by d ≤ 10 and the guard; the timing is pinned (`test_never_raises_and_is_fast`).
- **TR-11.10 Registries.** `test/function_test_map.py`, in alphabetical place:
  - `GlyphMapper._default_lpoly_bwidth` → `test/test_lpoly_rot.py::TestRotAgainstStata::test_r_bwidth`;
  - `GlyphMapper._compute_lpoly_fit` → `test/test_lpoly_rot.py::TestLocalFitRank::test_two_point_window_at_degree_two_keeps_the_square`;
  - `_lpoly_kept_columns` → `::TestLocalFitRank::test_well_conditioned_windows_keep_the_polyfit_path`;
  - `_lpoly_rot_constant` → `::TestRotConstants::test_table_is_statas_trapezoid_quadrature`;
  - `_lpoly_rot_detail` → `::TestRotAgainstStata::test_kept_columns_match_invsym_quadcross_on_raw_powers`;
  - `_lpoly_rot_float` → `::TestRotDegenerate::test_an_exact_fit_uses_statas_float_arithmetic`;
  - `_stata_invsym_keep` → `::TestStataInvsym::test_a_pivot_below_1e9_of_its_own_diagonal_is_dropped`.
- **TR-11.11 Help (dash.sthlp).**
  - Rewrite "Default bandwidth" (2058-2073): lpoly's rule of thumb as Stata computes it ([R] lpoly, Methods and formulas). That is a global polynomial of degree p+3 in powers of x (an even degree uses the next odd one), with Stata's handling of nearly collinear powers; the residual variance as the weighted mean squared residual; the squared (p+1)th derivative integrated over the central 90% of the range of x; and Stata's kernel constant. It is computed per by() panel and per qualifier, and recomputed from the rows kept after a served filter move.
  - Edge cases as twoway draws them: an x of 0 and 1 only, or a constant x, gives a line at 0; too few distinct points draw nothing. Exceptions D1-D3 are named. The 0.65 rule and the −9.7%…185 numbers are removed.
  - In the lpoly/lpolyci paragraph (2037-2048), replace "where the degree drops as Stata's does" with: a window whose powers of x are nearly collinear keeps the intercept and the powers Stata's `invsym` keeps.
  - The synopsis entry (1915-1925) keeps "by the rule of thumb under Default bandwidth".

### P0.9 (the analytic band, pwidth(), var(), level())

- **TR-11.12 Kernel weights.** `_lpoly_kernel_weights(x, x0, h, kernel) -> np.ndarray` (module level, after `_dash_lpoly_weights`) holds the support/kfn code of `_compute_lpoly_fit` (9363-9372), with identical arithmetic. `_compute_lpoly_fit` calls it.
- **TR-11.13 `_lpoly_local_wls(x, y, kw, x0, h, degree)`** returns `(pos, Z, Ainv, beta)` or None:
  - `pos = kw > 0`; None if `pos.sum() < 1`.
  - `K = _lpoly_kept_columns(raw Gram of (x[pos]−x0) powers)`; None if `0 not in K`.
  - `Z = np.vander((x[pos]−x0)/h, degree+1, increasing=True)[:, K]` (scaled; V00, b0, residuals and trace are invariant to column scaling); `A = Zᵀ diag(kw[pos]) Z`; `Ainv = np.linalg.inv(A)`; `beta = Ainv @ Zᵀ(kw[pos]·y[pos])`.
  - None on LinAlgError or any non-finite value.

  `_lpoly_se(x, y, x_grid, h, hp, degree, kernel, w=None, var=None) -> np.ndarray` returns NaN per grid point unless all of the following hold:
  - `h > 0` and `hp > 0`, both finite;
  - ≥ 2 positive main weights `kw = K_h·w`, and the main WLS is not None;
  - ≥ 2 positive pilot weights `kpw = K_hp·w` (even under `var`).

  Then `V00 = [Ainv Zᵀ diag(K_h² w) Z Ainv]₀₀`, and σ² is `var` if given, else:
  - from the degree+2 pilot WLS at hp: `num = Σ kpw r²` and `den = Σkpw − tr(As Zsᵀ diag(K_hp² w) Zs)`;
  - if `den <= _LPOLY_DF_TOL*Σkpw` (`_LPOLY_DF_TOL = 1e-10`) the row is pinched: se = 0 (SD-4);
  - else `σ² = max(num/den, 0)`.

  `se = sqrt(max(V00, 0)·σ²)`, NaN if not finite. The whole function runs under `np.errstate(all="ignore")`.

  `_dash_invnormal(p)` returns `statistics.NormalDist().inv_cdf(p)`, imported locally.
- **TR-11.14 Level.** `_resolve_level(options, default, ptype="")`: when `ptype == "lpolyci"` the valid range is 10 ≤ level ≤ 99.99 (inclusive); otherwise it stays `0 < level < 100`. Out of range or not a number: `_dash_warn_once(("level", ptype, str(raw)), "dash: level(<raw>) must be …; using <default>.")` and the default. `map_lpolyci` and `_dash_legend_keys` (23632) both pass the plot type.
- **TR-11.15 `map_lpolyci`.**
  1. `x, y, w, wtype = _layer_weights(...)`; `lw = _dash_lpoly_weights(w, wtype)`.
  2. Guard: `len(x) < 2` (was 3) gives the empty layer.
  3. `degree` and `kernel` as today.
  4. `bwidth` and `pwidth` via `_stat_option_float(options, key, None, "lpolyci", lo=0.0)`, then `lpvar` the same way. Any value ≤ 0 gives `_dash_warn_once(("lpolyci", key, raw), …)` and None.
  5. `level = _resolve_level(options, self.default_level, "lpolyci")`.
  6. `rot = _default_lpoly_bwidth(x, y, lw, degree, kernel)`; `h = bwidth or rot`; `hp = pwidth or 1.5*rot`.
  7. h NaN gives the zero line (TR-11.7) and an empty band.
  8. Otherwise:
     - `y_fit` from `_compute_lpoly_fit(h)`;
     - `se = _lpoly_se(x, y, x_grid, h, hp, degree, kernel, lw, lpvar)`;
     - `z = _dash_invnormal(0.5*(1−level/100)+level/100)`;
     - `line_src = {x_lp, y_lp}` on finite y_fit;
     - `band_src = {x_lp, y_lp, y_lower, y_upper}` on rows with finite y_fit and finite se.
  9. `_render_ci_band(fig, line_src, …, band_source=band_src)` returns (line, band). The layer always yields three sources (band, outline, line) in that order, drawn or empty. The empty branch goes through `_render_ci_band` with three empty sources, so `_ci_line_restyle` and `_apply_line_opts` run.
  10. `_mark_silent` only when y_fit is all NaN.

  `_bootstrap_ci`, `_N_BOOT_DEFAULT` and `_resolve_seed` stay (qfitci, jitter). Rewrite the docstring.
- **TR-11.16 `_render_ci_band(…, band_source=None)`** (6237) passes `band_source or source` to `_ci_band_glyphs` and draws the line on `source`. The callers at 8873, 8989 and 10106 are unchanged. The legend's band key uses TR-11.14's level.
- **TR-11.17 Served app.** Add `_lpoly_kernel_weights, _lpoly_local_wls, _lpoly_se, _dash_invnormal` to `_shared_stat_lines`' function tuple after P0.7's entries. `_LPOLY_DF_TOL` travels through the scan. Reword the comment "lpolyci's band is a bootstrap" (28950). The served refresh zip (31212) is unchanged.
- **TR-11.18 dash.ado and Mata.** New `void _dash_lpolyci_opts(string scalar unk, string scalar ptype)` in dash_parse.mata, beside `_dash_kernel_flag` (:4819-4870), with a header-index line (R4).
  - On `ptype == "lpolyci"` only, it takes from the catch-all, by value, every word `pw…pwidth(…)` (minimum `pw`) and `v…var(…)` (minimum `v`). It leaves `p(…)` (pstyle) and everything else.
  - It sets the locals `_lpo_pwidth`, `_lpo_var`, `_lpo_rest`, `_lpo_rc`, `_lpo_msg`.
  - A value is a number when it is one token and `strtoreal()` is not missing.

  Called from `_dash_fold_bw` after `_dash_kernel_flag`, its checks run in this order (each prints through `_dash_say` and exits):
  1. `var` text, not a number: r(7) `'<tok>' found where number expected`, or `'<2nd tok>' found where nothing expected` for two tokens.
  2. `s(level)`, not a number: r(7), the same words.
  3. Only when every typed `degree()`/`n()` value is an integer: `level` with an e/E/d/D exponent → r(198) `<text> found where number expected`; then the range check (r(198) `level() must be between 10 and 99.99 inclusive`); then more than two digits after the decimal point as typed → r(198) `level() can have at most two digits after the decimal point`.
  4. `pwidth`, not a number or ≤ 0: r(198) `pwidth() must be a positive number`.

  Without step 3's condition, a malformed `degree()`/`n()` is refused later by the table rule, naming that option (D7). Then:
  - `sreturn local pwidth` / `lpvar` hold `strofreal(v, "%21.0g")`, and `_unknown` holds the rest.
  - In `_dash_option_rules` (1899), add `level=num,10,99.99@lpolyci` before `level=num,0,100,x`, as a backstop.
  - At the end of `_dash_validate_opts`, after the rules loop, for lpolyci: `lpvar ≤ 0` → `var() must be a positive number`, r(198).
  - `_dash_plot_opts_to_json` (2991-3001) gains `pwidth lpvar`.
  - `pwidth()`/`var()` stay undeclared, so `_dash_rep_und_tab` (4489, 4491) still refuses repeats.
  - On every other type the words stay in the catch-all (SD-5).
- **TR-11.19 `lpvar`.** No JSON key named `var` is ever written for an option. LB-41 runs `_dash_extract_vars` on `{"type":"lpolyci","yvar":"mpg","xvar":"weight","options":{"pwidth":"800","lpvar":"10"}}` and gets `mpg weight`.
- **TR-11.20 Registries.**
  - `function_test_map.py`: `_dash_invnormal` → `test/test_lpolyci_band.py::TestDashInvnormal::test_matches_stata`; `_lpoly_kernel_weights` → `::TestTheVarianceRule::test_degree0_closed_form`; `_lpoly_local_wls` → `::TestTheVarianceRule::test_rank_deficient_windows_share_the_local_fits_kept_columns`; `_lpoly_se` → `::TestTheBandIsStatas::test_at_given_bandwidths`; `_resolve_level` → `::TestLegendKey::test_the_key_reads_the_level_the_band_is_drawn_at`.
  - `program_coverage_map.py`: `_dash_lpolyci_opts` → `("test_statistical_options.cscript:LB-11",)`.
- **TR-11.21 Help.**
  - Ignored list (1900-1912): drop pwidth()/var() on lpolyci.
  - New `{synopt}` entries `pwidth(#)` (pilot bandwidth, default 1.5 × the rule of thumb even with `bwidth()`; a positive number) and `var(#)` (a constant residual variance; the pilot window still needs two observations, as in Stata) after `bwidth(#)`.
  - lpoly/lpolyci paragraph (2037-2048): the band is smooth ± invnormal·σ_m(x0) by [R] lpoly eq. 4. It is exact at given bandwidths, and at defaults as exact as the rule of thumb. A row whose pilot fit has no residual degrees of freedom is drawn with zero width (Stata's value there is round-off, often missing: D4). The saved page keeps the build-time band (S12's cue); the served app refits.
  - Level text (2166-2183, and 591, 643): lpolyci's level() is 10 to 99.99 with at most two decimals, r(198), and a non-number is r(7), as in twoway. Delete "a bootstrap percentile band" and "(so dash draws an lpolyci band at level(5) …)". Document D8 and D9.
- **TR-11.22 Security (rule 1).**
  - Option values are read by value, never macro-expanded, and echoed through `_dash_say`.
  - The renderer accepts only finite positive pwidth/lpvar and a bounded level; hand-edited values give one note and the default.
  - No inf or NaN reaches a band source.
  - LinAlgError and overflow are contained.
  - `lpvar` closes the extract-vars injection.
  - The 200× bootstrap CPU per served move is gone.

## Boundaries

- Do not touch:
  - `_FILTER_JS` (the saved page recomputes only histogram and kdensity; the stale cue is S12's, M3);
  - the kdensity/histogram rules;
  - `_lpoly_grid_n` (twoway's grid rule is already right);
  - the qfitci bootstrap fallback.
- No JavaScript estimator (M3). No Stata call at registration (SD-9).
- `degree()` stays capped at 3 (P1.14). SD-7's constants are dormant.
- `pwidth()`/`var()` on other plot types keep today's note (SD-5).
- The gaussian 1e-14 counting rule is not changed (SD-10).
- Tracking documents (ROADMAP beyond S01's entry, GAPS2, REMAINING, AUDIT, DROPIN, AGENTS) belong to S15 (A5). Text for them goes in "Notes for the closeout".
- No new `.cscript`, no runner edit, no hygiene-pin edit (A3, R1). Truth blocks go in `test/test_wp29_truth.cscript`; refusals in `test_statistical_options.cscript`, `test_help_claims_6.cscript` and `test_parser.cscript` (R1 table).
- No new BUGS.md entry (SD-13). `ALLOWED` and `_MUST_WARN` in test_mode_parity.py are never edited (R6).

## Stata truth

Two new fixtures. Each comes from an extract script that reads its repository root from the global `W29_REPO`, so it runs through a two-line driver. `<repo>` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s11`. `<scratch>` is the section's scratch directory (the one holding `batch-2-base.txt`). Stata runs from `<scratch>/s11`:

```sh
mkdir -p <scratch>/s11
printf 'global W29_REPO "%s"\ndo "%s/scripts/extract_lpoly_rot_truth.do"\n' "<repo>" "<repo>" > <scratch>/s11/run_extract_lpoly_rot_truth.do
dash_nobrowser=1 <repo>/scripts/stata_slot.sh <scratch>/s11 <scratch>/s11/run_extract_lpoly_rot_truth.do   # log <scratch>/s11/run_extract_lpoly_rot_truth.log
```

The same two lines with `extract_lpolyci_truth` run the second. Each script:
- opens with `version 19`, `if "${W29_REPO}" == "" exit 198`, `adopath ++ "${W29_REPO}/"`, `set more off`, `graphics off`;
- captures `shell cd "${W29_REPO}" && git rev-parse HEAD > "<tempfile>"` and reads it into a local (the extract_axis_truth.do:107-114 pattern);
- records every result into Stata variables or locals at full double precision (`postfile … double`, never `%g` strings);
- writes the JSON from `python:` blocks that read Stata only through `sfi.Macro.getLocal`, `sfi.Scalar` and `sfi.Data`, and never call Stata. Numbers are written by `json.dump` (repr round-trips every double). Stata's missing becomes `null`. A backtick is written `\x60`.

`_meta` (D12) holds `stata_version`, `born_date`, `dash_commit`, `extracted` and `method`. Both fixtures are `git add -f`'d and named in `test/test_fixtures_are_committed.py`. Expected runtime: about 2 minutes and 1 minute.

- **`scripts/extract_lpoly_rot_truth.do` → `test/fixtures/lpoly_rot_truth.json`.**
  - **`datasets`:** for each sample source, the columns read by `sfi.Data.get` after `sysuse`: exact doubles, float-stored variables promoted exactly. The sources:
    - `auto` (mpg weight price rep78 trunk headroom foreign);
    - `census` (death pop);
    - `sp500` (close volume date, date in days; `datetc` = `cofd(date)`);
    - `nlsw88` (wage ttl_exp hours grade);
    - `uslifeexp` (le le_male year);
    - `server30`: test_server.py's frame, generated in a first `python:` block with `np.random.default_rng(42)` exactly as `test/test_server.py::auto_df` (n=30; mpg 12-40, weight 1800-4800, price 3000-15000, foreign 0-1), written to a tempfile CSV and read back with `import delimited`.

    Derived columns are computed in Stata and stored: `ycon=5`, `ysq=(weight/1000)^2`, `ylin=2*weight+1`, `yw=weight`, `one=1`, `f38=3+5*foreign`, `wtd=weight+20000`, `wtc=weight*86400000+1.9e12`, and the scale columns `weight*10^k` and `mpg*10^k` of the row list.
  - **`rows`:** one record per probe `{id, ds, y, x, w, wtype, idx, kernel, degree, n_grid, rc, bwidth, ngrid, N, kept, s2_mata, vy, class, tol}`:
    - `idx` holds the 0-based indices of the observations lpoly used: the condition, non-missing y and x, and a positive non-missing weight;
    - `n_grid = min(50, _N)`;
    - `kept` is the 0/1 diagonal pattern of Mata `invsym(quadcross(X,w,X))` on raw powers of degree pe+3, and `s2_mata` the residual variance of that fit, computed in a Mata block per probe;
    - `class` is `missing` when `bwidth` is null; else `noise` when y is constant or `s2_mata <= 1e-12*vy`; else `noisy` when degree ≥ 2 or the sample's |(min+max)/2| > 3·(max−min)/2; else `exact`;
    - `tol`: exact 1e-7, noisy 5e-5, degree 4/5 5e-4 (SD-7), noise and missing null.

    The probes:
    - auto: 8 kernels × degree 0-5 on mpg~weight, price~mpg, price~rep78, mpg~headroom;
    - auto `[aw=price]`, `[aw=rep78]`, `[aw=trunk]`, `[fw=rep78]`, `[fw=trunk]` on mpg~weight (degree 0-3, epanechnikov), plus `[aw=price*(rep78>2&rep78<.)]` (the zero-aweight case);
    - auto `in 1/2` … `in 1/12` and `if foreign==0`, `if foreign==1` (epanechnikov and gaussian, degree 0-3);
    - census death~pop, sp500 close~volume, nlsw88 wage~ttl_exp and wage~hours (8 kernels × degree 0-3); nlsw88 `[aw=hours]`, `[fw=grade]`;
    - uslifeexp le~year (epanechnikov) and le_male~year (gaussian), degree 0-3; sp500 close~date (epanechnikov) and volume~date (biweight), degree 0-3; sp500 close~datetc, degree 0 and 2;
    - the offset sweep `weight+{1..9}e{0..7}` (degree 0 and 2);
    - the scale sweep `weight*10^k` for k = −9…−1, 1…6, 10, 20, 22, 25, 30, 35, 40, 50, 75, 100, 140, and −10, −20, −40, −60, −100 (degree 0-3, or 0 and 2 for |k| ≥ 10);
    - the y scales `mpg*{1e100,1e150,1e160,1e200,1e-100,1e-150,1e-160,1e-200,1e-300}` (degree 0 and 2);
    - edge cases: ycon, ysq, ylin, yw, one, foreign, f38, rep78 if `inlist(rep78,3,4)` and `inlist(rep78,2,3,4)`, rep78 if `rep78>=3`, `weight*1e200`, each degree 0-3;
    - server30 mpg~weight, degree 0.
  - **`curves`:** `lpoly … nograph generate(gx gy)` (50 points) for:
    - auto biweight degree 2 (full and if foreign==1, 0);
    - epanechnikov degree 0 and gaussian degree 1 (full and if foreign==1);
    - `ylin`, `yw` degree 0 and 1;
    - `r10=rep78*10` price degree 1 `bwidth(3) n(41)`;
    - `mpg` on `weight*s`, s ∈ {1, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7}, degree 1-3, `bwidth(300*s)` (Part C).
  - **`serset`:** `twoway lpoly mpg weight, kernel(biweight) degree(2) by(foreign) nodraw saving()`, then `graph use`, `serset set k`, `serset use`: per panel, the first point and the count.
  - **`divergences`:** ids and reasons for D1 (ylin degree 0), D2 (yw degree 0/1) and D3 (`mpg*1e-150` degree 2).
- **`scripts/extract_lpolyci_truth.do` → `test/fixtures/lpolyci_truth.json`.**
  - **`cases`:** the 38 u07b cases, each `lpoly y x [w] [if], ci nograph degree() kernel() bwidth() pwidth() var() level() n() generate(gx gy) se(gse) generateci(cl cu)` (in names each case below). Per case:
    - `cmd`, `rc`, `bwidth`, `pwidth`, `N`, `ngrid`, `degree`, `kernel`, `level`, `z = invnormal(.5*(1-level/100)+level/100)`;
    - `idx`, the observations used;
    - `gx`, `gy`, `gse` (double), `cl`, `cu` (float).

    The cases:
    - auto mpg weight: `a_d0..a_d3`; the kernels rectangle, triangle, parzen, cosine and epan2 at `bwidth(400) pwidth(600)` (`a_d0_rec_bw400_pw600` …); `a_d0_bw500` with and without `pwidth(800)`; `a_d1_bw500_pw800`; `a_d0_var10`; `a_d1_bw500_var10`; `a_d0_aw`, `a_d0_fw`, `a_d1_aw_bw500_pw800`, `a_d1_fw_bw500_pw800`; `a_d0_bw100_pw150`, `a_d0_bw60_pw60`; levels 10, 90 and 99.99 at `bwidth(500) pwidth(800)`; `a_d0_n20` and an explicit-bw `n(20)`;
    - `a_d0_foreign` and an explicit `bwidth(400) pwidth(600)` if foreign==1;
    - `a_price_rep78_d0`; `rep_d2_bw06`; `r1000_d0`; `r1000_d2_bw600` (D5 rows listed under `divergences`);
    - `in 1/2..1/9` at default and at `bwidth(1000)`;
    - nlsw88 wage ttl_exp: `n_d0`, `n_d1`, `n_d2`, `n_d1_bw2_pw3`, `n_d0_aw` (`[aw=hours]`);
    - the review's `cx≡3000` `n(5)` (constant x);
    - `[aw=price*(rep78>2&rep78<.)]`.
  - **`serset`:** for 6 cases (`a_d1_bw500_pw800`, `a_d0`, `a_d0_foreign`, `a_d1_bi`, `n_d1_bw2_pw3`, `a_d0_lvl90`), the `twoway lpolyci` serset rows `(x, y, lower, upper)` as floats.
  - **`no_df`:** for `a_d2`, `a_d3` and `a_d0_foreign`, the grid indices where the exact pilot denominator is ≤ 1e-10·ΣK_p w. These are computed in the python block from the embedded data, NOT by dash (D4).
- **Live truth blocks** in `test/test_wp29_truth.cscript` (no fixture): `* ==== S11 P0.7: lpoly default bandwidth ====` (LW-01..LW-07) and `* ==== S11 P0.9: lpolyci analytic band ====` (LB-01..LB-05).
  - Both are gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S11") {`, and appended above `* ==== append new blocks above this line ====` after S10's blocks (R1).
  - The page reader is a `python:` block defining `_lw_read(path, prefix)`, the way `test_gaps2_truth.cscript`'s S05 block defines `_he5_read` (:233-273). It parses the page's `<script type="application/json">` blocks, applies `Document.from_json`, and finds the ColumnDataSource with `x_lp` (and, for LB, `y_lower`). It sets globals `<prefix>_x`, `<prefix>_y` (and `_lo`, `_hi`) as space-separated reprs, which are read into locals and dropped at once.

  Run:

  ```sh
  printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_wp29_truth.cscript" > <scratch>/s11/run_test_wp29_truth.do
  dash_nobrowser=1 WP29_ONLY=S11 <repo>/scripts/stata_slot.sh <scratch>/s11 <scratch>/s11/run_test_wp29_truth.do
  ```

  Read the log; never relaunch to check. The script exits 222 when `c(python_exec)` is empty. A SKIP is not a pass.

## TDD test stubs

A saved figure comes from `dr.DashRenderer(spec_path, data_path)._build_figures()`. A served one comes from `dr.ServerAppBuilder(sp, dp).build(app_path)`, then import, then `make_document(Document())`; move helpers are `test_mode_parity._served` and `_fire`. Tests parametrised `mode in ("saved", "served")` assert both. Fixture loaders `pytest.fail` naming the extract script if a fixture is absent; nothing skips. Counts use `dr.GlyphMapper._compute_lpoly_fit(x, y, bwidth=h, degree=d, kernel=k, n_grid=row["n_grid"], w=lw)`, because `_lpoly_grid_n` without a dataset uses the sample size.

### P0.7: `test/test_lpoly_rot.py` (new, task 11-02)

Regression tests are marked (R): they FAIL at the batch-2 base.
- `TestStataInvsym::test_a_pivot_below_1e9_of_its_own_diagonal_is_dropped` (R, AttributeError): `[[1,1],[1,1+e]]` keeps `[0]` at e=9.9e-10 and `[0,1]` at e=1e-9; `[[1e6,1e3],[1e3,1+e]]` behaves the same.
- `::test_an_absolute_pivot_below_1e_19_is_dropped` (R): `[[1e-19]]` keeps `[0]`; `[[np.nextafter(1e-19,0)]]` keeps `[]`; `diag(1e10,5e-20)` keeps `[0]`; `[[1,1e-6],[1e-6,1e-12+5e-20]]` keeps `[0]`.
- `::test_the_largest_current_pivot_is_swept_first` (R): `V=[[0,9,10],[2,1,0],[2e-6,0,0]]` with `G=VᵀV` keeps `[0,2]`; an exact tie keeps the first column.
- `::test_the_order_argument_sweeps_those_columns_first` (R): `order=(0,)` keeps the intercept of a two-point window `[1,d,d²]` with d=(−100,100) and drops `d` (the `{1,d²}` set of Part C).
- `TestRotConstants::test_table_is_statas_trapezoid_quadrature` (R): `_LPOLY_ROT_CONSTANTS` equals `_lpoly_rot_constant` at 1e-13 and the Evidence table at 1e-15. The implied constant `r(bwidth)/term` of every `exact` row matches within 2e-9.
- `::test_support_is_strict` (R): the rectangle constant computed without the mask differs by −1.2687% (p=1); the table holds the strict value.
- `TestRotAgainstStata::test_r_bwidth[<row id>]` (R): every `exact` and `noisy` row satisfies `abs(h/r(bwidth) − 1) <= row["tol"]`. Pre-fix: auto mpg weight biweight degree 2 is 63.80 vs 302.44936813331043.
- `::test_kept_columns_match_invsym_quadcross_on_raw_powers` (R): `_lpoly_rot_detail(...)["kept"]` equals the row's `kept` pattern on every `exact`/`noisy` row (auto weight+20000 pe1 `01111`, sp500 date pe3 `0000111`, uslifeexp year pe3 `1000111`, rep78 pe3 `1010111`, f38 `00011`).
- `::test_even_degree_takes_the_next_odd_rule` (R): degree 0 equals 1 and 2 equals 3 exactly, for all 8 kernels.
- `::test_years_and_dates_follow_statas_raw_power_arithmetic` (R): uslifeexp le~year 3.6430833364289748 (d0) and 31.878433756089901 (d2), and NOT the exact-math 2.7119/7.32. sp500 close~date 14.545570460491128 and 200.51125382378513 (needs S05).
- `::test_tc_datetime` (R, A9): close~cofd(date) 32504400.964425806 (d0) and 2274141561.3559403 (d2) at 5e-5 (needs S05).
- `::test_small_x_scales` (R): `weight*1e-1..1e-9` at degree 0-3 match the fixture, including NaN where Stata is `.`.
- `::test_weights` (R): the aw/fw rows; an fweight row equals the same data with rows duplicated; the zero-aweight row equals the row with those weights missing.
- `TestRotDegenerate::test_x_of_zeros_and_ones_draws_a_line_at_zero[mode]` (R): `lpoly mpg foreign` draws 50 points, x from 0 to 1, y all 0, and no note. Pre-fix: a 42-point curve between the group means.
- `::test_constant_x_and_huge_x_are_statas_missing_bandwidth` (R): `one` and `weight*1e200` give NaN; route `missing`.
- `::test_quadcross_overflow_is_statas_missing` (R): `weight*1e22/1e25/1e30` degree 2 and `*1e35/1e40/1e50` degree 0 give NaN; `*1e20` degree 2 and `*1e30` degree 0 are finite and match.
- `::test_y_scale_extremes` (R): the nine `mpg*s` rows match outcome (finite within tol, or NaN where Stata is `.` or 0). `mpg*1e-150` degree 2 is NaN and is listed in `divergences` (D3).
- `::test_an_exact_fit_uses_statas_float_arithmetic` (R): every `noise` row has route `float`. The drawn count equals Stata's `ngrid` for ycon, ysq and `in 1/2..1/5` at degree 0-3, and the drawn curve equals Stata's generate() curve where Stata's curve does not depend on h (ycon, ysq at degree 2/3, ylin at degree 1-3, yw at degree 2/3). D1 and D2 are asserted only for a finite positive h and for their ids being in `divergences`.
- `::test_small_samples_draw_statas_ngrid` (R): `in 1/n`, n=2..12, degree 0-3: the drawn count equals `ngrid` (0,0,0,0 for n=2..5; 24 at n=6 degree 2; 10 at n=7 degree 0; …).
- `::test_never_raises_and_is_fast` (R): a fuzz over subnormals, ±1e300, duplicates, n=2, all-equal arrays and `weight*1e75` degree 0 always returns a float that is NaN or > 0, never inf, with no warning (`warnings.simplefilter("error")`). N=1e5 runs under 1 s.
- `TestMapLpolyUsesTheRule::test_kernel_degree_and_weights_reach_the_rule` (R): a spy on `_default_lpoly_bwidth` sees `(x, y, lw, 2, "biweight")`. The drawn auto biweight degree 2 curve equals the fixture curve within 1e-4 mpg, at 50 points.
- `::test_lpolyci_line_uses_the_resolved_bandwidth` (R): the lpolyci line equals the lpoly line, and (in P0.7) every bootstrap call receives a float bandwidth.
- `::test_by_panels_use_their_own_bandwidth[mode]` (R): by(foreign) biweight degree 2 panels at 316.80385769239462 and 287.77974373265636 (fixture `serset`), drawn curves within 1e-4.
- `::test_a_missing_bandwidth_draws_a_zero_line[lpoly|lpolyci][mode]` (R): `mpg` on `foreign` draws 50 points at y=0, and the lpolyci band source is empty.
- `TestLocalFitRank::test_two_point_window_at_degree_two_keeps_the_square` (R): at bw 287.77974373265636 on foreign==1, grid indices 41-48 equal the Evidence values at 1e-9. Pre-fix: error 8.857.
- `::test_one_value_window_at_degree_one_is_the_group_mean`: r10 degree 1 `bwidth(3) n(41)` gives 4564.5 ×4, 5125.75, 5266.0625, 5406.375, 5967.625 (a guard: green before and after).
- `::test_tiny_scale_windows_follow_the_absolute_floor` (R): `weight*s` at bw 300s, s=1e-6 degree 3 and s=1e-7 degree 2/3, within 1e-9 of the fixture curves. Pre-fix: 1.43, 0.873, 1.43.
- `::test_well_conditioned_windows_keep_the_polyfit_path` (R, AttributeError): `_lpoly_kept_columns` returns all columns on auto biweight degree 2 at bw 302.45 for every grid point. A spy on `np.polyfit` sees one call per grid point.
- `TestTheServedAppCarriesTheRule::test_the_app_defines_the_new_helpers_and_constants` (R): build an app, read its text, and assert each of `def _stata_invsym_keep(`, `def _lpoly_rot_constant(`, `def _lpoly_rot_detail(`, `def _lpoly_rot_float(`, `def _lpoly_kept_columns(`, `_LPOLY_ROT_GRID =` and `_LPOLY_ROT_CONSTANTS =` appears, and `_LPOLY_ROT_C =` and `Fraction(` at module level (column 0) do not. Exec the app into a dict, call its `_default_lpoly_bwidth` on auto mpg weight biweight degree 2, and get 302.449368… within 1e-7.

### P0.7: mode and served (task 11-03)

- `test/test_mode_parity.py` CORPUS (guards): `_case("lpoly, kernel(biweight) degree(2)", [plot_for("lpoly", {"kernel": "biweight", "degree": "2"})])` and `_case("lpolyci, kernel(gaussian) degree(3) aweight", …)`. MOVE_CORPUS: `_move_case("lpoly biweight degree 2, dropdown", _MOVES[0], [plot_for("lpoly", {"kernel": "biweight", "degree": "2"})])`.
- `test/test_server_statistics.py::TestServedDefaultBandwidth::test_served_default_is_statas` (R): the served app on auto (`test/fixtures/data/auto.csv`), lpoly biweight degree 2 with `foreign` as a dropdown, after `_fire` to Foreign. The curve equals the fixture `curves` foreign==1 biweight degree 2 within 1e-4, at 50 points. Pre-fix: bandwidth 26.88, 5 points.
- `::test_a_served_recompute_reaches_the_floor_and_overflow_paths` (R): `weight*1e-7` degree 2 with a move gives a zero line; `weight*1e22` degree 2 gives a zero line; neither raises.

### P0.9: `test/test_lpolyci_band.py` (new, task 11-14)

- `TestTheBandIsStatas::test_at_given_bandwidths[<case>-<mode>]` (R): cases `a_d0_bw500_pw800`, `a_d1_bw500_pw800`, `a_d1_bw500_var10`, `a_d0_{rec,tri,par,cos,ep2}_bw400_pw600`, `a_d0_bw100_pw150`, `a_d0_bw60_pw60`, `a_d1_aw_bw500_pw800`, `a_d1_fw_bw500_pw800`, `n_d1_bw2_pw3`, `rep_d2_bw06`, levels 10/90/99.99, the explicit-bw `n(20)`. The band source's `(x_lp, y_lower, y_upper)` equals `gy ∓ z·gse` at `1e-8·max(1,|gy|)` on rows where `gse` is finite and the row is not in `no_df`. Rows where `gse` is missing for fewer than two positive weights are absent. Pre-fix: width ratio 0.85-1.55.
- `::test_at_default_bandwidths[<case>-<mode>]` (R): `a_d0`, `a_d1`, `a_d2`, `a_d3`, `a_d0_gau`, `a_d1_bi`, `a_d0_aw`, `a_d0_fw`, `a_price_rep78_d0`, `a_d0_foreign`, `n_d0`, `n_d1`, `n_d2`, `n_d0_aw`, `r1000_d0`. Tolerance is `1e-8·max(1,|y|)` plus what the rule-of-thumb's tier implies: `noisy` cases at 1e-4 relative of the band half-width. `r1000_d2_bw600`'s D5 rows are excluded by id.
- `::test_pwidth_default_is_one_and_a_half_rot`: `hp == 1.5·rot` for `a_d0_bw500` (105.964382033088 with bwidth 500).
- `::test_matches_twoways_drawn_serset[<case>]` (R): the 6 serset cases at rtol 1e-6, pinched rows included. Also `qualified_stat_truth.json` `layers.lpolyci` `all` and `foreign1` (1760 pinched: lower = upper = 27.6727848).
- `TestTheVarianceRule` (unit tests of `_lpoly_se`, R by AttributeError):
  - `test_degree0_closed_form` (V00 = ΣK²w/(ΣKw)²);
  - `test_var_replaces_sigma2`;
  - `test_a_pilot_window_of_one_is_missing_even_with_var` (`a_d1_bw500_var10` at x=4588.57 is NaN);
  - `test_no_residual_df_pinches` (`a_d2` indices 44-49 give se == 0.0);
  - `test_fweight_equals_replication`;
  - `test_aweight_rescaling_invariant`;
  - `test_x_scale_invariant` (x, h, hp ×1000);
  - `test_rank_deficient_windows_share_the_local_fits_kept_columns` (`r1000_d2_bw600` yhat within 2e-9; `a_d3` at x=4400 gives 7.0604…);
  - `test_zero_aweights_are_dropped_before_normalising` (N=59 equals the missing-weight case at 3e-8);
  - `test_constant_x_has_no_band` (cx≡3000: band empty, y all 0, no warning, no RankWarning).
- `TestDashInvnormal::test_matches_stata`: z at levels 10, 90, 95 and 99.99 equals the fixture `z` at 1e-15; `_dash_invnormal(.975) == 1.959963984540054` at 1e-15.
- `TestNoBootstrap::test_never_resamples` (R): a spy on `_bootstrap_ci` sees 0 calls. `::test_jitterseed_changes_nothing` (R): the band under `jitterseed(7)` equals the default exactly. `::test_two_local_fits_per_grid_point` (R): a spy on `_lpoly_local_wls` sees ≤ 2 calls per grid point.
- `TestFewObservations::test_bwidth_1000_draws_statas_smooth_and_no_band[2|3-<mode>]` (R): fixture `two_bw1000`/`three_bw1000`: the line equals Stata's `gy` on 50 points, the band source is empty, and there is no note. Pre-fix: nothing drawn (`len(x) < 3`).
- `TestSources::test_the_band_joins_across_a_missing_ci[mode]`: the band source has no NaN and skips the missing rows.
  - `::test_three_sources_drawn_or_empty[mode]` (R): both branches yield band, outline and line sources, in that order.
  - `::test_the_empty_branch_keeps_line_styling[mode]` (R): `lcolor(red) lpattern(dash)` on 1 row gives `line_color "#ff0000"` and `line_dash [8, 4]`.
  - `::test_a_served_refit_that_empties_a_panel_warns_nothing` (R): by(foreign) with a move that empties one panel raises no "redrew N source(s)" warning.
- `TestServedRefit::test_a_move_to_foreign_redraws_statas_band` (R): explicit `bwidth(400) pwidth(600)` after the move equals the fixture's foreign==1 explicit case at 1e-8. Pre-fix: edge error 4.3.
- `TestHostileValues::test_hostile_spec_values[<value>-<mode>]` (R):
  - `pwidth 1e-300` gives no band and no exception;
  - `lpvar 8e307` puts no inf in any source;
  - `pwidth`/`lpvar` of `abc`, `-1` or `nan`, and `level` 5 or `abc`, give exactly one note naming the option and value, and the default.
  - `::test_a_bad_spec_value_is_noted_once_across_moves` (R): three served moves give the note once.
- `TestLegendKey::test_the_key_reads_the_level_the_band_is_drawn_at[<level>-<mode>]` (R): a spec level of 5 or `abc` gives the key `95% CI` and z at 95; a level of 90 gives `90% CI` and z 1.6448536269514722.
- `TestNoVarKey::test_no_option_key_is_named_var`: a spec whose lpolyci options are `{"pwidth": "800", "lpvar": "10"}` gives `dr.DashRenderer._collect_plot_vars` (it reads `_VAR_KEYS` at the plot level and `_DASH_OPT_VAR_KEYS = ("colorvar", "mlabel", "wexp")` in options, dash_render.py:22376, 24952) exactly `["mpg", "weight"]`. A source scan asserts that dash.ado's `_dash_plot_opts_to_json` key list holds `lpvar` and not ` var `. The Stata side is LB-41/LB-43.
- `TestTheServedAppCarriesTheBandHelpers::test_names_defined` (R): the app text defines the four helpers and `_LPOLY_DF_TOL`, and its exec'd `_lpoly_se` matches the saved value on `a_d1_bw500_pw800`.
- `test/test_estimator_cost.py::TestLpolyciCost::test_the_band_costs_a_few_lpolys` (R): at N=20000, `map_lpolyci` takes ≤ 20× `map_lpoly`. Today it is about 190×.
- `test/test_mode_parity.py`: `_MOVED_LAYERS` gains `"lpolyci"` (a guard: green before and after).

### P0.9: Stata cases (task 11-15)

Each case runs twoway's command under its own named log, so its first error line is read and used as dash's needle. Failures append to `nfail`/`faillist`, print `LB-nn FAIL: <why>`, and continue.

`test/test_statistical_options.cscript`, after SO-74 and before `// Summary`:
- **LB-11** `pwidth(800) var(10)`, `pw(800) v(10)`, `pwidth(1d3) var(1d1)`, `pwidth(1e-320) var(1e-320)`, `pwidth(.5e3) var(+10)`: rc 0; no note naming pwidth()/var(); the spec JSON carries `"pwidth"` and `"lpvar"` and no `"var"` option.
- **LB-12** `pwidth()` of `0`, `-1`, `abc`, `.`, `800 900`, `price`: r(198), twoway's words.
- **LB-13** `var(0)`, `var(-1)`: r(198), twoway's words.
- **LB-14** `var()` of `abc`, `price`, `.`, `10 20`: r(7), twoway's words.
- **LB-15** `level()` of `5`, `9.99`, `99.995`, `100`, `0`, `-95`, `.95`: r(198), range words. `level()` of `10`, `99.99`, `10.0`, `95.`, `+95`, `95.00`: rc 0.
- **LB-16** `level(99.990)`, `level(95.000)`: r(198), the decimals words.
- **LB-17** `level(abc)`: r(7). `level(95 96)`: r(7), `'96' found where nothing expected`. `level(1e1)`, `level(9.5d1)`: r(198), `found where number expected`.
- **LB-18** order. These match twoway: `level(5) var(abc)` (7), `pwidth(0) var(0)` (pwidth), `level(5) pwidth(0)` (level), `bwidth(0) level(5)` (level), `pwidth(0) degree(-1)` (pwidth), `if _n<=2, pwidth(0)` (pwidth). These name the same option in dash's words (D7): `var(0) bwidth(0)` (bwidth), `var(0) kernel(foo)` (kernel), `var(0) degree(-1)` (degree), `level(5) degree(abc)` (degree), `pwidth(0) n(abc)` (n). This one is pinned as D6: `if _n==1, pwidth(0)` (twoway r(2001), dash r(198) pwidth).
- **LB-19** `p(800)` on lpolyci is `pstyle()`: no `"pwidth"` key in the spec.
- **LB-20** `pwidth(800)` and `var(2)` on lpoly, scatter, lfitci and kdensity: dash rc 0 with the note naming each (SD-5, D9). twoway's r(198) is recorded in the log.

`test/test_parser.cscript` (Mata units), at the end of its last case block:
- **LB-41** `_dash_extract_vars` on the lpvar spec gives `mpg weight`.
- **LB-42** `_dash_lpolyci_opts` on each LB-11..LB-17 input sets `_lpo_rc`, `_lpo_msg`, `_lpo_pwidth`, `_lpo_var` and `_lpo_rest` as expected; on `ptype == "lpoly"` it takes nothing.
- **LB-43** `dash lpolyci mpg weight, pwidth(800) var(10) saving()`: rc 0, and the data file holds exactly `mpg weight` (plus dash's row id).

`test/test_help_claims_6.cscript`: HC6-24 is flipped (TR above) and HC6-55 is split (HC6-55b added).

### Truth blocks (tasks 11-10 and 11-22, `test/test_wp29_truth.cscript`)

- **LW-01** auto mpg weight, 8 kernels × degree 0-3 (32 runs): `dash lpoly …, saving(page)` against `lpoly …, nograph generate(gx gy)`. The count of drawn points equals `r(ngrid)`. Each drawn y is within `1e-6·(max−min of y)` (degree 0/1) or `1e-4·` (degree 2/3) of `gy` at the same `gx`.
- **LW-02** `[aw=price]` and `[fw=rep78]` at degree 0 and 2, the same checks.
- **LW-03** `by(foreign)` biweight degree 2: each panel equals `lpoly … if foreign==k`.
- **LW-04** uslifeexp le year at degree 0 and 2.
- **LW-05** sp500 close date at degree 0 and 2 (S05 units). dash draws `x_lp` in epoch ms on its date axis (D05-1 struck, ratified 01oct2026: "Keep the date axis."), so each drawn x is compared with `(gx - td(01jan1970))*86400000`, never `gx`; the bandwidth stays in days. The same applies to any S11 pytest that compares a date lpoly's drawn x; for `%tc`, compare with `gx - tc(01jan1970 00:00:00)`.
- **LW-06** `mpg` on `foreign`: 50 points with y=0 and x from 0 to 1. `in 1/5`: the page's lpoly source is empty.
- **LW-07** the lpolyci line equals the lpoly line (same options).
- **LB-01** auto `degree(1) bwidth(500) pwidth(800)`: the band source equals `gy ∓ z·gse` from `lpoly …, ci nograph … generate(gx gy) se(gse)` within `1e-8·max(1,|gy|)`.
- **LB-02** nlsw88 wage ttl_exp `[aw=hours] bwidth(2) pwidth(3)`.
- **LB-03** auto `kernel(biweight) degree(1)` at defaults (pilot 1.5·rot), within `1e-6·max(1,|gy|)`.
- **LB-04** `by(foreign)` panel 1 with `bwidth(400) pwidth(600)`.
- **LB-05** `set level 90`, then `bwidth(500) pwidth(800)`: z = invnormal(.95).

**Mutation table:**

| Break this | Test that must die |
|---|---|
| drop the 1e-19 floor in `_stata_invsym_keep` | `TestStataInvsym::test_an_absolute_pivot_below_1e_19_is_dropped`, `TestRotAgainstStata::test_small_x_scales`, `TestLocalFitRank::test_tiny_scale_windows_follow_the_absolute_floor` |
| pure greedy without `order=(0,)` in the local fit | `TestLocalFitRank::test_two_point_window_at_degree_two_keeps_the_square` |
| leave the strict support out of `_lpoly_rot_constant` | `TestRotConstants::test_support_is_strict`, the rectangle `test_r_bwidth` rows |
| use the n−k variance or a density term | `test_r_bwidth` (every row) |
| treat an exact fit with the exact rule | `test_an_exact_fit_uses_statas_float_arithmetic` (`in 1/2..1/5` draw points) |
| `_mark_silent` / draw nothing on NaN | `test_x_of_zeros_and_ones_draws_a_line_at_zero` |
| key `var` in `_dash_plot_opts_to_json` | LB-41, LB-43, `TestNoVarKey` |
| `_resolve_level` without `ptype` in the legend | `TestLegendKey` |
| empty branch with one shared source | `TestSources::test_three_sources_drawn_or_empty` |
| pinch replaced by NaN | `test_no_residual_df_pinches`, `test_matches_twoways_drawn_serset[a_d0_foreign]` |
| omit `_lpoly_se` from the served tuple | `TestTheServedAppCarriesTheBandHelpers`, `TestTheServedAppCarriesEveryName` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| invsym emulation, constants, rule against r(bwidth), kept patterns | pytest `test_lpoly_rot.py` | lpoly_rot_truth.json | n/a (helpers) |
| drawn lpoly at default h: kernels, degrees, weights, by(), edge cases | pytest `test_lpoly_rot.py` | lpoly_rot_truth.json | yes |
| served recompute after a move | pytest `test_server_statistics.py`, `test_mode_parity.py` MOVE_CORPUS | lpoly_rot_truth.json | yes |
| local fit rank rule (Part C) | pytest `test_lpoly_rot.py::TestLocalFitRank` + existing truth pins | lpoly_rot_truth.json curves | n/a |
| lpoly against live Stata | truth block LW-01..LW-07 | none | saved |
| analytic band at given and default bandwidths, serset, variance rule | pytest `test_lpolyci_band.py` | lpolyci_truth.json, qualified_stat_truth.json | yes |
| no bootstrap; cost | pytest spies; `test_estimator_cost.py` | none | yes |
| sources, styling, legend level, hostile values, notes once | pytest `test_lpolyci_band.py` | none | yes |
| option values, refusals, order, lpvar | cscript LB-11..LB-20, LB-41..LB-43; HC6-24, HC6-55b | none (twoway asked live) | n/a |
| band against live Stata | truth block LB-01..LB-05 | none | saved |
| registries and served guards | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_fixtures_are_committed.py` | — | n/a |

Acceptance criteria:

- **AC-11.1** `python3 -m pytest test/test_lpoly_rot.py test/test_lpolyci_band.py test/test_help_claims_6.py test/test_statistical_truth.py test/test_statistical_helpers.py test/test_statistical_defaults.py test/test_server.py test/test_server_statistics.py test/test_mode_parity.py test/test_lpolyci_options.py test/test_layer_reports.py test/test_help_claims_7.py test/test_option_validation.py test/test_estimator_cost.py -q -n0` passes, with no skip.
- **AC-11.2** Under `WP29_ONLY=S11`, `test/test_wp29_truth.cscript` prints `LW-01 PASS` … `LW-07 PASS` and `LB-01 PASS` … `LB-05 PASS`. `test_statistical_options.cscript` prints `LB-11 PASS` … `LB-20 PASS`. `test_parser.cscript` prints `LB-41 PASS` … `LB-43 PASS`. `test_help_claims_6.cscript` prints `HC6-24 PASS`, `HC6-55 PASS` and `HC6-55b PASS`. None prints `FAIL` or `SKIP`.
- **AC-11.3** Both served guards, `test_function_test_map.py`, `test_program_coverage_map.py` and `test_fixtures_are_committed.py` pass. `grep -c "_LPOLY_ROT_C\b" dash_render.py` prints 0.
- **AC-11.4** BUGS.md carries the P0.7 and P0.9 entries closed (`- Resolution: Fixed <ddmonyyyy> (WP-29, P0.7).` / `(WP-29, P0.9).`), naming tests that exist. Their `WP29_OPEN` keys are gone. `grep -c '<!-- WP-29 P0.7 -->\|<!-- WP-29 P0.9 -->' CHANGELOG.md` prints 0. `test_tracking_documents.py` passes.
- **AC-11.5** `git log --format=%s wp29-p0..wp29-s11` shows exactly two commits, ending `(WP-29 P0.7)` and `(WP-29 P0.9)` in that order, and neither message matches `claude|anthropic`.

## Tasks

**Commit boundary.**
- Tasks 11-01 to 11-12 form the P0.7 commit, subject `Compute lpoly's default bandwidth by Stata's rule of thumb (WP-29 P0.7)`, made by 11-12.
- Tasks 11-13 to 11-24 form the P0.9 commit, subject `Draw lpolyci's analytic band with pwidth() and var() (WP-29 P0.9)`, made by 11-24.

Both commits go on worktree branch `wp29-s11` (`/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s11`), after one full suite run each (`python3 -m pytest test/ -q`; read its log). Each body opens with its saved failure text, then the measured defect, then what changed and where, then the line forms in Notes. The merger lands them on `wp29-p0` in order with `patch -p1` (index step 1).

Every Stata run is `<repo>/scripts/stata_slot.sh <scratch>/s11 <file>.do` with `dash_nobrowser=1`. No AI references anywhere. Never stage `CLAUDE.md`, `.gitignore`, scratch or `*.html`.

<task type="auto" id="11-01">
  <name>Extract the rule-of-thumb truth fixture</name>
  <files>scripts/extract_lpoly_rot_truth.do, test/fixtures/lpoly_rot_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[
Run `npx gitnexus analyze` in the worktree, then `gitnexus_impact({target, direction: "upstream"})` for `_default_lpoly_bwidth`, `_compute_lpoly_fit`, `map_lpoly`, `map_lpolyci`, `_render_ci_band`, `_resolve_level` and `ServerAppBuilder._shared_stat_lines`. Write the results to `<scratch>/11-impact.txt`, and report any HIGH or CRITICAL result to the orchestrator before editing. If the index cannot be built, copy the grep table of "Blast radius" there and say so.

Create `scripts/extract_lpoly_rot_truth.do` as "Stata truth" specifies, with these parts:
- the `W29_REPO` guard, `adopath ++` and the `git rev-parse` capture;
- a first `python:` block that writes test_server.py's 30-row frame (`np.random.default_rng(42)`, the column order and ranges of `test/test_server.py::auto_df`) to a tempfile CSV named in a local;
- per dataset, a `python:` block reading the columns with `sfi.Data.get` into a tempfile JSON;
- a `program lw_rec` that runs `capture lpoly <y> <x> [<w>] <cond>, nograph kernel() degree()`, stores rc, `r(bwidth)`, `r(ngrid)` and `r(N)` through `post` into a `postfile` of doubles and strings;
- a Mata block that, on the same sample, computes the raw-power `X`, `G = quadcross(X,w,X)`, `Gi = invsym(G)`, the `kept` pattern `diag(Gi) :!= 0`, `b = Gi*quadcross(X,w,y)`, `s2_mata` and `vy`, and returns them to the post;
- a `postfile` of the observation indices per probe (`idx`);
- the `curves` and `serset` sections;
- a final `python:` block assembling `test/fixtures/lpoly_rot_truth.json` with `_meta` (`method`: "lpoly r(bwidth)/r(ngrid) and Mata invsym(quadcross()) on raw powers"), `datasets`, `rows` (with `class` and `tol` by the "Stata truth" rules), `curves`, `serset` and `divergences` (D1, D2, D3 ids with Stata's value and the reason text from Evidence).

Run it through the two-line driver of "Stata truth". `git add -f` the fixture, and add `lpoly_rot_truth.json` to the committed-fixture list in `test/test_fixtures_are_committed.py`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' <scratch>/s11/run_extract_lpoly_rot_truth.log` prints 0. `python3 -c "import json;d=json.load(open('test/fixtures/lpoly_rot_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));rows=d['rows'];a=[r['bwidth'] for r in rows if r['ds']=='auto' and r['y']=='mpg' and r['x']=='weight' and r['w']=='' and r['kernel']=='biweight' and r['degree']==2 and len(r['idx'])==74];s=[r['bwidth'] for r in rows if r['ds']=='server30'];print(len(rows)>600, a[0], s[0])"` prints `True` and values within 1e-12 of 302.44936813331043 and 63.42135953323416. `python3 -m pytest test/test_fixtures_are_committed.py -q -n0` passes. `<scratch>/11-impact.txt` exists.]]></verify>
  <done>Stata's r(bwidth), r(ngrid), invsym kept patterns and curves for every P0.7 probe were recorded in a stamped fixture, and the blast radius was recorded.</done>
</task>

<task type="auto" id="11-02">
  <name>Write the failing P0.7 unit tests</name>
  <files>test/test_lpoly_rot.py</files>
  <action><![CDATA[
Create `test/test_lpoly_rot.py` with every test under "P0.7: test/test_lpoly_rot.py", using exactly those class and test names, and the parametrisations by fixture row id (`f"{ds}-{y}-{x}-{w}-{kernel}-d{degree}-n{len(idx)}"`).

Helpers:
- `_sample(row)` returns `x, y, lw` from `datasets` and `idx`: aw rows normalised to mean 1 over idx, fw rows raw.
- `_count(x, y, h, row)` calls `dr.GlyphMapper._compute_lpoly_fit` with `n_grid=row["n_grid"]` and counts the finite values.
- `_saved(spec)` and `_served(spec)` build figures as "TDD test stubs" says. Use `test/fixtures/data/auto.csv` with `var_labels` passed explicitly (A7) for the drawn tests.

Reference the new names (`dr._stata_invsym_keep`, `dr._lpoly_rot_constant`, `dr._LPOLY_ROT_CONSTANTS`, `dr._lpoly_rot_detail`, `dr._lpoly_kept_columns`) inside the tests, never at import, so they fail with AttributeError and not with a collection error. The S05-dependent tests call `pytest.fail("needs S05 (u08 date units)")` if `dr._dash_date_units` is absent. Do not touch dash_render.py.

Run `python3 -m pytest test/test_lpoly_rot.py -q -n0 -p no:cacheprovider 2>&1 | tail -60` against the unmodified batch-2 base. Save the output to `<scratch>/11-P0.7-failure.txt`, headed with the sha in `<scratch>/batch-2-base.txt`, and list the guard tests (green now) separately at its end. Do not commit.
  ]]></action>
  <verify><![CDATA[The run collects without error. `test_r_bwidth[auto-mpg-weight--biweight-d2-n74]` fails with 63.8 against 302.449. `test_x_of_zeros_and_ones_draws_a_line_at_zero[saved]` fails on the y values. `test_two_point_window_at_degree_two_keeps_the_square` fails with an error near 8.857. `TestStataInvsym::*` fail with AttributeError. `test_one_value_window_at_degree_one_is_the_group_mean` passes and is listed as a guard. `<scratch>/11-P0.7-failure.txt` exists.]]></verify>
  <done>Every P0.7 unit and drawing regression test existed and failed for its recorded reason at the batch-2 base, with the guards named and nothing committed.</done>
</task>

<task type="auto" id="11-03">
  <name>Write the failing P0.7 served tests</name>
  <files>test/test_mode_parity.py, test/test_server_statistics.py</files>
  <action><![CDATA[
In `test/test_mode_parity.py`:
- append to `CORPUS` the two `_case` entries of "P0.7: mode and served";
- append to `MOVE_CORPUS` the `_move_case("lpoly biweight degree 2, dropdown", …)` entry.

Edit neither `ALLOWED` nor `_MUST_WARN` (R6).

In `test/test_server_statistics.py`, add `class TestServedDefaultBandwidth` with `test_served_default_is_statas` and `test_a_served_recompute_reaches_the_floor_and_overflow_paths`, as specified, using the file's `_spec`/`_write` helpers and the served move pattern of `test_mode_parity._fire`. The truth comes from `lpoly_rot_truth.json` `curves` (foreign==1 biweight degree 2).

Run `python3 -m pytest test/test_server_statistics.py -q -n0 -k ServedDefaultBandwidth` and `python3 -m pytest test/test_mode_parity.py -q -n0 -k "biweight"` at the base. Append their outputs to `<scratch>/11-P0.7-failure.txt`, with the parity cases listed as guards (both modes run the same Python today). Do not commit.
  ]]></action>
  <verify><![CDATA[`test_served_default_is_statas` fails, showing 5 drawn points against 50. The new CORPUS and MOVE_CORPUS cases pass, listed as guards. `python3 -m pytest test/test_mode_parity.py -q -n0 -k "CorpusIsComplete"` passes.]]></verify>
  <done>The served-recompute regression test failed at the base for its recorded reason, and the parity corpus gained the default-bandwidth cases as guards.</done>
</task>

<task type="auto" id="11-04">
  <name>Add the invsym and constant helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
In dash_render.py, replace `_LPOLY_ROT_C = 0.65` and its comment (:227-229) in place with `_LPOLY_ROT_GRID` and `_LPOLY_ROT_CONSTANTS` (TR-11.1). Paste the constant values as `repr(_lpoly_rot_constant(k, p))`, generated once with the new function, and keep a comment naming the quadrature.

After the `_KERNELS` literal's closing brace (:13222), add:
- `_lpoly_rot_constant` (TR-11.1);
- `_stata_invsym_keep` (TR-11.2): local `from fractions import Fraction`, float default arguments, no assert, no module-level Fraction;
- `_lpoly_kept_columns` (TR-11.6).

Give each a docstring citing the Evidence measurements. Add the function_test_map entries of TR-11.10 for these three names.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_rot.py -q -n0 -k "TestStataInvsym or TestRotConstants"` passes. `python3 -c "import dash_render as d, ast; assert ast.literal_eval(repr(d._LPOLY_ROT_CONSTANTS)) == d._LPOLY_ROT_CONSTANTS and ast.literal_eval(repr(d._LPOLY_ROT_GRID)) == d._LPOLY_ROT_GRID; print(d._stata_invsym_keep([[1,1],[1,1+9.9e-10]]), d._stata_invsym_keep([[1e-19]]))"` prints `[0] [0]`.]]></verify>
  <done>Stata's invsym column rule, the per-kernel constants and the local kept-column test existed as module helpers with literal-safe constants.</done>
</task>

<task type="auto" id="11-05">
  <name>Port Stata's rule-of-thumb bandwidth</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Add the module functions `_lpoly_rot_float` (TR-11.4) and `_lpoly_rot_detail` (TR-11.3, steps 1-9, in that order) after `_lpoly_kept_columns`. Rewrite `GlyphMapper._default_lpoly_bwidth` (9246-9303) as a staticmethod with the signature `(x, y, w=None, degree=0, kernel="epanechnikov")` returning `_lpoly_rot_detail(...)["h"]`.

The docstring states:
- the rule;
- the SD-1 tolerance tiers;
- that NaN means Stata's missing (the caller draws a zero line);
- the D1-D3 divergences.

Delete the "HONESTY NOTE" text. Use `math.comb` and `math.factorial`; import `fractions` locally; wrap the body as TR-11.3 says. Add the function_test_map entries for `_lpoly_rot_detail` and `_lpoly_rot_float` and repoint `GlyphMapper._default_lpoly_bwidth` (TR-11.10).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_rot.py -q -n0 -k "TestRotAgainstStata or TestRotDegenerate and not draws and not ngrid"` passes. `python3 -m pytest test/test_lpoly_rot.py -q -n0 -k test_never_raises_and_is_fast` passes in under 10 s.]]></verify>
  <done>The default bandwidth became Stata's r(bwidth) on every fixture row within its tier, NaN wherever Stata's is missing, and the float emulation on exact fits.</done>
</task>

<task type="auto" id="11-06">
  <name>Follow invsym in the local fit</name>
  <files>dash_render.py</files>
  <action><![CDATA[
In `GlyphMapper._compute_lpoly_fit` (9306-9407), apply TR-11.6:
- the default call passes `w, degree, kernel`;
- for degree at least 1, build the raw local design, call `_lpoly_kept_columns`, and keep today's `np.polyfit` branch when every column is kept;
- otherwise solve on the kept columns with the intercept's coefficient as `y_fit`, or NaN when the intercept is dropped.

Delete the `min(degree, distinct-1)` reduction and rewrite its comment to cite Part C's measurements (foreign==1 biweight degree 2; `TestLpolyDegreeAgainstStata`). Keep Nadaraya-Watson at degree 0. Keep the kernel loop inline (P0.9 moves it).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_rot.py -q -n0 -k TestLocalFitRank` passes. `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k "TestLpolyDegreeAgainstStata or TestLpolyGridAgainstStata"` and `python3 -m pytest test/test_statistical_truth.py -q -n0 -k "TestLpolyDegreeOne or TestLpolyNullRule or test_explicit_bwidth_is_absolute"` pass. `python3 -m pytest test/test_help_claims_6.py -q -n0 -k "TestLpolyAtEveryDegree or TestLpolyGrid"` passes.]]></verify>
  <done>Rank-deficient and below-floor windows were fitted as Stata's invsym fits them, with every existing Stata pin still green.</done>
</task>

<task type="auto" id="11-07">
  <name>Resolve one bandwidth per layer</name>
  <files>dash_render.py</files>
  <action><![CDATA[
In `map_lpoly` (9437-9522) and `map_lpolyci` (9525-9644), resolve `bw` once after `_layer_weights` (TR-11.7):
- the user's positive `bwidth()`, else `GlyphMapper._default_lpoly_bwidth(x, y, lw, degree, kernel)` with `lw = _dash_lpoly_weights(w, wtype)`;
- when `bw` is NaN, draw `y = 0` on `np.linspace(x.min(), x.max(), n_grid)` with no note and no `_mark_silent`;
- in `map_lpolyci`, a NaN `bw` also gives an empty band;
- pass the number to `_compute_lpoly_fit` and to the bootstrap closure (9617-9622), which P0.9 deletes.

Fix `map_lpoly`'s docstring (":9458-9461: bwidth (default 0.5)").
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_rot.py -q -n0` passes except `TestTheServedAppCarriesTheRule` (11-08). `python3 -m pytest test/test_lpolyci_options.py test/test_layer_reports.py -q -n0 -k "lpoly"` passes.]]></verify>
  <done>Both mappers drew Stata's default bandwidth for the layer's own rows, and a zero line where Stata's bandwidth is missing.</done>
</task>

<task type="auto" id="11-08">
  <name>Copy the rule into the served app</name>
  <files>dash_render.py, test/test_lpoly_rot.py</files>
  <action><![CDATA[
In `ServerAppBuilder._shared_stat_lines`' function tuple (28950-28986), add `_lpoly_rot_constant, _stata_invsym_keep, _lpoly_rot_detail, _lpoly_rot_float, _lpoly_kept_columns` directly after `_dash_lpoly_weights` (SD-11), with a comment saying the served recompute calls them. Remove `"_LPOLY_ROT_C"` from `_glyph_layer_lines`' constants tuple (28364), and update the comments at 29013 and 31741-31742.

Do not add an import to the app header (29375-29400); the helpers import `fractions` locally. Confirm that `test/test_lpoly_rot.py::TestTheServedAppCarriesTheRule` is written as the stub says. Edit its assertions only if the generated text's spelling differs (for example, an annotated constant), and record why.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_rot.py -q -n0 -k TestTheServedAppCarriesTheRule` passes. `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k TestTheServedAppCarriesEveryName` and `python3 -m pytest test/test_resource_limits.py -q -n0 -k TestTheServedAppDefinesEveryNameItReads` pass. `python3 -m pytest test/test_server_statistics.py -q -n0 -k ServedDefaultBandwidth` passes.]]></verify>
  <done>The served app carried and ran the same rule, and a served filter move recomputed Stata's bandwidth for the kept rows.</done>
</task>

<task type="auto" id="11-09">
  <name>Flip the P0.7 pinned tests</name>
  <files>test/test_help_claims_6.py, test/test_statistical_truth.py, test/test_server.py</files>
  <action><![CDATA[
Flip, each with a comment naming P0.7 and this section, and never delete:
- the four `TestDefaultBandwidth` tests, as the "Tests that pin today's behaviour" list says. Delete `_HELP_PCT` and keep `_STATA_ROT` as truth; the `in 1/7` case uses 5e-5;
- `test_statistical_truth.py::TestLpolyAgainstStata::test_default_bandwidth_is_within_the_documented_tolerance`, which becomes `test_default_bandwidth_is_statas` at 1e-8. Rewrite its docstring;
- `test_server.py::TestServerLpolyFpfit::test_lpoly_make_document_runs`: 21 becomes 27, and the docstring says Stata's `r(ngrid)` is 27 at h 63.42135953323416.

The help-text assertion in `test_the_help_gives_those_numbers` reads the sentences of TR-11.11 written in 11-11. Write it now against those exact sentences. It stays red until 11-11, as the only expected failure.

Record each change as a `Flipped: <node> -- <old expectation> was wrong because <why>` line in `<scratch>/11-flips-P0.7.txt`. Then run the test_mode_parity.py docstring fix (text only, :2665-2680).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_6.py test/test_statistical_truth.py test/test_server.py test/test_statistical_defaults.py -q -n0 -k "lpoly or Lpoly or DefaultBandwidth"` fails only `test_the_help_gives_those_numbers`. `<scratch>/11-flips-P0.7.txt` holds one line per flip.]]></verify>
  <done>Every test that pinned the 0.65 rule, its gaps or its point counts pinned Stata's values instead, with each flip recorded.</done>
</task>

<task type="auto" id="11-10">
  <name>Certify lpoly against live Stata</name>
  <files>test/test_wp29_truth.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
Append the block `* ==== S11 P0.7: lpoly default bandwidth ====` … `* ==== end S11 P0.7 ====` to `test/test_wp29_truth.cscript`, above `* ==== append new blocks above this line ====` and after S10's blocks (R1). Gate it with `local only : env WP29_ONLY` / `if inlist("`only'", "", "S11") {`.

Define the `_lw_read` python reader as "Stata truth" says, then add LW-01..LW-07 as "Truth blocks" specifies. Each case:
- writes its page to a tempfile `.html`;
- runs Stata's `lpoly … generate()` in the same run;
- compares through Mata on the globals the reader set;
- prints `LW-0n PASS` or `LW-0n FAIL: <why>` through the script's PASS/FAIL helper, without exiting.

LW-05 prints `LW-05 FAIL: needs S05` if dash's date path is absent. Add `test_wp29_truth.cscript:LW-01` as an `e2e` reference for the `dash` lpoly path in `test/program_coverage_map.py` if the file has an entry form for it; otherwise leave it.

Run the block through the driver of "Stata truth".
  ]]></action>
  <verify><![CDATA[`grep -c "LW-0[1-7] PASS" <scratch>/s11/run_test_wp29_truth.log` prints 7. `grep -c " FAIL\|SKIP" <scratch>/s11/run_test_wp29_truth.log` prints 0. `grep -c '^r([0-9]*);' <scratch>/s11/run_test_wp29_truth.log` prints 0. `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q -n0` passes.]]></verify>
  <done>Live Stata certified dash's default lpoly curves, panels, weights, dates and edge cases on the saved page.</done>
</task>

<task type="auto" id="11-11">
  <name>Rewrite the Default bandwidth help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
Rewrite dash.sthlp's "Default bandwidth" paragraph (2058-2073) and the lpoly/lpolyci paragraph's rank sentence (2037-2048), as TR-11.11 gives them. The new text:
- names D1-D3 in one sentence each, without tolerances (SD-8);
- states that a `by()` panel and a filtered served view each get their own bandwidth.

Keep the synopsis wording (1915-1925). Use only SMCL the file already uses; no `{bf:}` around user text.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_6.py -q -n0` passes. `grep -c "0.65 (s^2/S)\|185 against" dash.sthlp` prints 0. `python3 -m pytest test/test_help_conformance.py -q -n0` passes.]]></verify>
  <done>The help described Stata's rule of thumb, the per-panel and per-filter recompute, the edge cases and the documented divergences.</done>
</task>

<task type="auto" id="11-12">
  <name>Close P0.7 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
In BUGS.md, close in place the entry S01 opened for P0.7. Its exact title is the value of key `"P0.7"` in `WP29_OPEN`.
- `- [ ]` becomes `- [x]`.
- File Names and Line Numbers: dash_render.py `_default_lpoly_bwidth`, `_lpoly_rot_detail`, `_lpoly_rot_float`, `_lpoly_rot_constant`, `_stata_invsym_keep`, `_lpoly_kept_columns`, `_compute_lpoly_fit`, `map_lpoly`, `map_lpolyci`, `ServerAppBuilder._shared_stat_lines`.
- The Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.7). The default lpoly and lpolyci bandwidth is Stata's rule of thumb as lpoly computes it (per-kernel constant, degree p+3 raw-power fit with Stata's invsym column rule and 1e-19 floor, quadcross overflow, float64 arithmetic on exact fits), per layer sample, by() panel and served filter view, in both renderers; Stata's missing bandwidth draws a line at 0. The local fit keeps the intercept and the powers Stata's invsym keeps in rank-deficient windows (Part C), which also fixes foreign==1 biweight degree(2) (8.857 mpg) and degree(3) at large x. Pinned by test/test_lpoly_rot.py::TestRotAgainstStata::test_r_bwidth, test/test_lpoly_rot.py::TestLocalFitRank::test_two_point_window_at_degree_two_keeps_the_square, test/test_server_statistics.py::TestServedDefaultBandwidth::test_served_default_is_statas, test/test_wp29_truth.cscript LW-01; fixture test/fixtures/lpoly_rot_truth.json. Residual, deferred (WP-29): exact-fit divergences D1-D3 (y exactly linear in x at degree 0/1; mpg*1e-150 at degree 2); the gaussian two-observation weight threshold (SD-10).`

Delete the `"P0.7"` key line from `WP29_OPEN` in `test/test_tracking_documents.py`.

In CHANGELOG.md, replace the `<!-- WP-29 P0.7 -->` marker in `### Results that change` with ONE line ending `(WP-29, P0.7)`. It names:
- `lpoly mpg weight, kernel(biweight) degree(2)` (old bandwidth 63.80 and 34 points, new 302.45 and 50);
- `in 1/7` (old 185, new 77.35);
- `lpoly mpg foreign` (old a curve between the group means, new a line at 0);
- the served recompute after a move (old 26.88, new 287.78);
- Part C.

Run `python3 -m pytest test/ -q` once (rule 4; read its log), then the S11 P0.7 truth block through the driver. Run `gitnexus_detect_changes()` and check `git diff --cached --name-only` against the files of tasks 11-01 to 11-12. Grep the message for `claude|anthropic`. Commit on `wp29-s11` with the subject `Compute lpoly's default bandwidth by Stata's rule of thumb (WP-29 P0.7)`. The body opens with `<scratch>/11-P0.7-failure.txt` and then carries:
- `Regression: test/test_lpoly_rot.py::<Class>::<test> -- failed at <batch-2 base sha> with <text>` lines;
- the `Flipped:` lines from `<scratch>/11-flips-P0.7.txt`;
- `Fixture: test/fixtures/lpoly_rot_truth.json (scripts/extract_lpoly_rot_truth.do)`;
- `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.7 -->' CHANGELOG.md` prints 0, and `grep -c '(WP-29, P0.7)' CHANGELOG.md BUGS.md` totals 2. `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0. `git log -1 --format=%s | grep -c '(WP-29 P0.7)$'` prints 1.]]></verify>
  <done>P0.7 was closed in BUGS.md naming existing tests, its marker was replaced, its tracking key was deleted, and one green commit on wp29-s11 carried the cycle.</done>
</task>

<task type="auto" id="11-13">
  <name>Extract the lpolyci band truth fixture</name>
  <files>scripts/extract_lpolyci_truth.do, test/fixtures/lpolyci_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[
Run `gitnexus_impact` (after `npx gitnexus analyze` if the P0.7 commit made the index stale) for `map_lpolyci`, `_render_ci_band`, `_resolve_level`, `_dash_legend_keys`, `_dash_fold_bw`, `_dash_validate_opts` and `_dash_plot_opts_to_json`. Append the results to `<scratch>/11-impact.txt`.

Create `scripts/extract_lpolyci_truth.do` as "Stata truth" specifies:
- the `W29_REPO` guard;
- per case, `capture lpoly …, ci nograph … generate(gx gy) se(gse) generateci(cl cu)`, with the scalars posted;
- the grid variables read in a `python:` block through `sfi.Data`;
- `z` computed in Stata with `invnormal()` and posted;
- the serset of the 6 cases via `twoway lpolyci … nodraw saving()`, `graph use`, `serset set 0`, `serset use`;
- the embedded datasets (auto, nlsw88) for the tests, with `idx` per case;
- `no_df` computed in the final python block with numpy from the embedded data: the exact pilot denominator relative to its weight sum, at most 1e-10.

Write `test/fixtures/lpolyci_truth.json` with `_meta` (`method`: "lpoly, ci se() generateci() and the twoway lpolyci serset"), `cases`, `serset`, `no_df` and `divergences` (D4 rows and D5's two `r1000_d2_bw600` indices). Run it through the driver. `git add -f` the fixture, and add it to `test/test_fixtures_are_committed.py`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' <scratch>/s11/run_extract_lpolyci_truth.log` prints 0. `python3 -c "import json;d=json.load(open('test/fixtures/lpolyci_truth.json'));c={x['id']:x for x in d['cases']};print(len(c)>=38, c['a_d0_bw500']['pwidth'], c['a_d0']['z'], d['no_df']['a_d2'])"` prints `True`, a value within 1e-12 of 105.964382033088, 1.959963984540054 and `[44, 45, 46, 47, 48, 49]`. `python3 -m pytest test/test_fixtures_are_committed.py -q -n0` passes.]]></verify>
  <done>Stata's lpoly ci grids, standard errors, pilot widths, z values and twoway sersets for every P0.9 case were recorded in a stamped fixture.</done>
</task>

<task type="auto" id="11-14">
  <name>Write the failing band tests</name>
  <files>test/test_lpolyci_band.py, test/test_mode_parity.py</files>
  <action><![CDATA[
Create `test/test_lpolyci_band.py` with every test under "P0.9: test/test_lpolyci_band.py", using exactly those names. Reference the new names (`dr._lpoly_se`, `dr._lpoly_local_wls`, `dr._lpoly_kernel_weights`, `dr._dash_invnormal`) inside the tests. Build saved and served documents as the stubs say.

Use spies through `monkeypatch.setattr(dr.GlyphMapper, "_bootstrap_ci", staticmethod(spy))` and `monkeypatch.setattr(dr, "_lpoly_local_wls", spy)`. Write `TestHostileValues` specs with `options` holding the raw string values. In `test/test_mode_parity.py`, add `"lpolyci"` to `_MOVED_LAYERS` (2021).

Run `python3 -m pytest test/test_lpolyci_band.py -q -n0 -p no:cacheprovider 2>&1 | tail -60` and `python3 -m pytest test/test_mode_parity.py -q -n0 -k lpolyci` at the P0.7 commit. Save the output to `<scratch>/11-P0.9-failure.txt`, headed with that commit's sha, with guards listed separately. Do not commit.
  ]]></action>
  <verify><![CDATA[The run collects without error. `test_at_given_bandwidths[a_d1_bw500_pw800-saved]` fails on the band edges. `TestNoBootstrap::test_never_resamples` fails (200 calls). `TestFewObservations::*` fail (nothing drawn). `TestTheVarianceRule::*` fail with AttributeError. The `_MOVED_LAYERS` lpolyci cases pass and are listed as guards. `<scratch>/11-P0.9-failure.txt` exists.]]></verify>
  <done>Every P0.9 band regression test existed and failed for its recorded reason on the tree the P0.7 commit left, with guards named and nothing committed.</done>
</task>

<task type="auto" id="11-15">
  <name>Write the failing option-check cases</name>
  <files>test/test_statistical_options.cscript, test/test_parser.cscript, test/test_help_claims_6.cscript</files>
  <action><![CDATA[
Append LB-11..LB-20 to `test/test_statistical_options.cscript`, after SO-74 and before `// Summary` (:876), and add one header "Groups:" line per case. Each case:
- runs `capture noisily twoway lpolyci mpg weight, <opts> nodraw` under a named log, reads twoway's rc and first error line, and uses that line as the needle;
- runs `dash lpolyci mpg weight, <opts> saving(<tempfile>.html, replace)` the same way;
- compares rc and text, prints `LB-nn PASS` or `LB-nn FAIL: <why>`, and continues.

LB-11 reads the spec JSON dash writes (the build's spec tempfile, found as the existing SO-73 case finds it) for `"pwidth"`, `"lpvar"` and no `"var"` in `options`. LB-18 asserts the D6/D7 rows as documented differences: the same option named, with dash's words, and twoway's rc recorded.

Append LB-41..LB-43 to `test/test_parser.cscript` after its last case block. LB-41 and LB-42 call the Mata functions inside `capture`, so the script runs to the end while `_dash_lpolyci_opts` does not exist.

In `test/test_help_claims_6.cscript`:
- flip HC6-24 (`dash lpolyci mpg weight, level(5)` gives r(198) with twoway's message);
- remove the two lpolyci pairs from HC6-55's `pairs` list (:805);
- add HC6-55b, in which `dash lpolyci mpg weight, pwidth(500) var(2)` gives rc 0 and a note naming neither.

Run the three scripts through the cd-test driver. Append every LB and HC6 FAIL line to `<scratch>/11-P0.9-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "LB-1[1-9] FAIL\|LB-20 FAIL" <scratch>/s11/run_test_statistical_options.log` is at least 7 (LB-11..LB-17 fail; LB-20 passes). `grep -c "LB-4[1-3] FAIL" <scratch>/s11/run_test_parser.log` is at least 2. `grep -c "HC6-24 FAIL\|HC6-55b FAIL" <scratch>/s11/run_test_help_claims_6.log` prints 2. `grep -c "SO-[0-9]* PASS" <scratch>/s11/run_test_statistical_options.log` equals its count before the edit.]]></verify>
  <done>The Stata-side P0.9 cases measured twoway in the same run and failed against the P0.7 commit for their recorded reasons.</done>
</task>

<task type="auto" id="11-16">
  <name>Add the analytic band helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
After `_dash_lpoly_weights` (13485-13494), add `_LPOLY_DF_TOL = 1e-10`, `_lpoly_kernel_weights` (TR-11.12), `_lpoly_local_wls` and `_lpoly_se` (TR-11.13), and `_dash_invnormal`. Each has a docstring citing eq. 4 and the Evidence measurements; the pinch rule names D4.

Make `_compute_lpoly_fit`'s kernel loop call `_lpoly_kernel_weights`, with identical arithmetic: `test_help_claims_6.py::TestLpolyAtEveryDegree` holds at rtol 1e-11. Add the function_test_map entries of TR-11.20.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpolyci_band.py -q -n0 -k "TestTheVarianceRule or TestDashInvnormal"` passes. `python3 -m pytest test/test_help_claims_6.py test/test_lpoly_rot.py -q -n0` passes.]]></verify>
  <done>Stata's sandwich standard error with the degree p+2 pilot, var(), the kept-column rule and the pinch existed as module helpers.</done>
</task>

<task type="auto" id="11-17">
  <name>Draw the analytic band in lpolyci</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Rewrite `GlyphMapper.map_lpolyci` per TR-11.15:
- delete the bootstrap closure and call;
- add the `pwidth`/`lpvar` readers with `_dash_warn_once`;
- add the level resolver;
- compute rot, h and hp;
- build `line_src` and `band_src`;
- add the guard `len(x) < 2`;
- build the empty branch through `_render_ci_band` with three empty sources.

Add `band_source=None` to `_render_ci_band` (TR-11.16). Extend `_resolve_level` with `ptype=""` and `_dash_warn_once` keys (TR-11.14), and pass the plot type from `_dash_legend_keys` (23632). Update `_bootstrap_ci`'s docstring (qfitci only) and `_resolve_seed`'s comment (13000).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpolyci_band.py -q -n0` passes except `TestTheServedAppCarriesTheBandHelpers` and the served-mode parameters that need 11-18. `python3 -m pytest test/test_lpolyci_options.py test/test_ci_band_style.py test/test_ci_plot_index.py -q -n0` passes, or fails only on bootstrap wording flipped in 11-20.]]></verify>
  <done>The saved page drew lpolyci's analytic band with pwidth(), var() and twoway's level bounds, in three stable sources, with the legend reading the level drawn.</done>
</task>

<task type="auto" id="11-18">
  <name>Copy the band helpers into the app</name>
  <files>dash_render.py, test/test_lpolyci_band.py</files>
  <action><![CDATA[
Add `_lpoly_kernel_weights, _lpoly_local_wls, _lpoly_se, _dash_invnormal` to `_shared_stat_lines`' function tuple after P0.7's entries (TR-11.17), and reword the comment at 28950. Confirm `_LPOLY_DF_TOL` is written by the scan.

Run the served tests. If the served zip refresh (31212) warns "redrew N source(s)" on a panel the move empties, the empty branch did not yield three sources: fix `map_lpolyci`, not the refresh. Confirm `TestTheServedAppCarriesTheBandHelpers` as written.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpolyci_band.py -q -n0` passes. `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k TestTheServedAppCarriesEveryName` and `python3 -m pytest test/test_resource_limits.py -q -n0 -k TestTheServedAppDefinesEveryNameItReads` pass. `python3 -m pytest test/test_mode_parity.py -q -n0 -k "lpoly"` passes.]]></verify>
  <done>The served app drew and refitted the same analytic band after every filter move, with no source-count warning.</done>
</task>

<task type="auto" id="11-19">
  <name>Read pwidth() and var() in dash.ado</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
In dash_parse.mata, add `_dash_lpolyci_opts` beside `_dash_kernel_flag` (:4819-4870), with a header-index line (R4), per TR-11.18. Read every value by value with `st_global`/`st_local`; never expand it. Echo it through `_dash_say`.

In dash.ado:
- call it in `_dash_fold_bw` after `_dash_kernel_flag` (:1532), printing `_lpo_msg` and exiting `_lpo_rc` when non-zero;
- `sreturn local pwidth`, `lpvar` and `_unknown` by `: copy local`;
- add `level=num,10,99.99@lpolyci` before `level=num,0,100,x` in `_dash_option_rules` (:1899);
- add the `lpvar <= 0` check after the rules loop of `_dash_validate_opts` for lpolyci;
- add `pwidth lpvar` to `_dash_plot_opts_to_json`'s key list (:2991-3001).

Leave `_dash_rep_und_tab` (4489, 4491) as it is. Add `"_dash_lpolyci_opts": ("test_statistical_options.cscript:LB-11",)` to `test/program_coverage_map.py` in alphabetical place.
  ]]></action>
  <verify><![CDATA[The statistical-options, parser and help-claims-6 scripts, re-run through their drivers, print `LB-11 PASS` … `LB-20 PASS`, `LB-41 PASS` … `LB-43 PASS`, `HC6-24 PASS`, `HC6-55 PASS` and `HC6-55b PASS`, with no earlier case newly failing. `python3 -m pytest test/test_program_coverage_map.py test/test_unsupported_report_is_true.py -q -n0` passes.]]></verify>
  <done>dash.ado honoured pwidth() and var() on lpolyci under the lpvar key and refused every value twoway refuses, in twoway's order apart from the pinned differences.</done>
</task>

<task type="auto" id="11-20">
  <name>Flip the P0.9 pinned tests</name>
  <files>test/test_help_claims_6.py, test/test_lpolyci_options.py, test/test_option_validation.py</files>
  <action><![CDATA[
Flip, with comments naming P0.9:
- `test_help_claims_6.py::TestLpolyciBand`: rename `test_every_resample_is_evaluated_on_the_drawn_grid` to `test_no_resample_is_drawn`, and `test_the_line_is_statas_and_the_band_is_not` to `test_the_line_and_band_are_statas` (26.2413063049316 / 29.4909420013428 at rtol 1e-6), and rewrite the class docstring;
- `test_lpolyci_options.py`: the module docstring and the bootstrap comments (:22-23, about :85, :161);
- `test_option_validation.py::CONTRACT_PLOT_RULES` gains `level=num,10,99.99@lpolyci`.

Then run every file that names lpolyci (`grep -l lpolyci test/*.py`). Flip any assertion on the bootstrap band, the two-source structure or the `len(x) < 3` rule with its reason. Anything else is a regression of this section: fix the code. Record every flip in `<scratch>/11-flips-P0.9.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $(grep -l lpolyci test/*.py) test/test_option_validation.py -q -n0 2>&1 | tail -3` reports no failures and no new skips. `<scratch>/11-flips-P0.9.txt` holds one line per flip.]]></verify>
  <done>Every test that pinned the bootstrap band, its resamples or the old level rule pinned Stata's band and twoway's bounds, with each flip recorded.</done>
</task>

<task type="auto" id="11-21">
  <name>Bound the band cost generously</name>
  <files>test/test_estimator_cost.py</files>
  <action><![CDATA[
Add `class TestLpolyciCost` with `test_the_band_costs_a_few_lpolys` to `test/test_estimator_cost.py`, following the file's generous-bound style (its module docstring: load average 50-180). The data is N=20000 synthetic (seeded). The test times `map_lpolyci` and `map_lpoly` on the same data with the minimum of three runs each, and asserts at most 20×. Note in a comment that the spy tests in `test_lpolyci_band.py` are the primary assertion (u07b review). This file is outside the manifest list and is added under that binding amendment.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_estimator_cost.py -q -n0 -k Lpolyci` passes.]]></verify>
  <done>The lpolyci band's cost was bounded against lpoly with a ratio robust to a loaded machine.</done>
</task>

<task type="auto" id="11-22">
  <name>Certify the band against live Stata</name>
  <files>test/test_wp29_truth.cscript</files>
  <action><![CDATA[
Append `* ==== S11 P0.9: lpolyci analytic band ====` … `* ==== end S11 P0.9 ====` after the P0.7 block, above the marker, gated the same way. Reuse `_lw_read` (extended to `y_lower`/`y_upper`), and add LB-01..LB-05 as "Truth blocks" specifies. Each runs `lpoly …, ci nograph generate(gx gy) se(gse)` in the same run and compares the saved page's band source to `gy ∓ invnormal(.5*(1-l/100)+l/100)*gse`, in Mata. LB-05 runs `set level 90` and restores `set level 95` after. Run under `WP29_ONLY=S11`.
  ]]></action>
  <verify><![CDATA[`grep -c "LB-0[1-5] PASS" <scratch>/s11/run_test_wp29_truth.log` prints 5. `grep -c "LW-0[1-7] PASS" <scratch>/s11/run_test_wp29_truth.log` prints 7. `grep -c " FAIL\|SKIP" <scratch>/s11/run_test_wp29_truth.log` prints 0.]]></verify>
  <done>Live Stata certified the saved page's lpolyci band at given and default widths, with weights, panels and level.</done>
</task>

<task type="auto" id="11-23">
  <name>Document the analytic band</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
Edit dash.sthlp per TR-11.21:
- the ignored list (1900-1912);
- new `pwidth(#)` and `var(#)` synopt entries after `bwidth(#)`;
- the band sentences in the lpoly/lpolyci paragraph (2037-2048);
- the level text at 2166-2183, 591 and 643;
- D8 (`pwidth(+800)` accepted) and D9 (pwidth()/var() named on other types).

Grep `test/test_help_claims_*.py` and `test/test_help_claims_*.cscript` for the changed sentences and update any pin, recording it in `<scratch>/11-flips-P0.9.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "bootstrap percentile" dash.sthlp` prints 0. `python3 -m pytest test/test_help_claims_6.py test/test_help_conformance.py -q -n0` passes.]]></verify>
  <done>The help described the analytic band, pwidth(), var(), the level bounds and the documented differences.</done>
</task>

<task type="auto" id="11-24">
  <name>Close P0.9 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
Close in place the BUGS.md entry under `WP29_OPEN["P0.9"]`'s title:
- `- [x]`.
- File Names and Line Numbers: dash_render.py `map_lpolyci`, `_lpoly_se`, `_lpoly_local_wls`, `_lpoly_kernel_weights`, `_dash_invnormal`, `_render_ci_band`, `_resolve_level`, `_dash_legend_keys`; dash.ado `_dash_fold_bw`, `_dash_option_rules`, `_dash_validate_opts`, `_dash_plot_opts_to_json`; dash_parse.mata `_dash_lpolyci_opts`.
- The Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.9). lpolyci draws lpoly's analytic band, smooth +/- invnormal times the sandwich standard error with a degree p+2 pilot at pwidth() (default 1.5 times the rule of thumb) or var(), in both renderers and in served refits; no bootstrap is run. dash.ado honours pwidth() and var() (JSON key lpvar) and refuses the values and level() twoway refuses, in twoway's order. Rank-deficient windows share Part C's kept columns, which also closes the degree(3) and rep78*1000 degree(2) windows at large x. Pinned by test/test_lpolyci_band.py::TestTheBandIsStatas::test_at_given_bandwidths, test/test_lpolyci_band.py::TestNoBootstrap::test_never_resamples, test/test_statistical_options.cscript LB-12, test/test_wp29_truth.cscript LB-01; fixture test/fixtures/lpolyci_truth.json. Residual, deferred (WP-29): rows whose pilot has no residual degrees of freedom are pinched where Stata's round-off is often missing (D4); two r1000 degree(2) pilot rows (D5); the count-before-pwidth order (D6); pwidth()/var() on other types are named, not refused (D9).`

Delete the `"P0.9"` key line from `WP29_OPEN`.

Replace `<!-- WP-29 P0.9 -->` in `### Results that change` with ONE line ending `(WP-29, P0.9)`. It names:
- `lpolyci mpg weight, degree(1) bwidth(500) pwidth(800)` (old a bootstrap band 0.85-1.55 times Stata's width, edges off by up to 44.7 mpg at degree(1); new Stata's band);
- pwidth()/var() honoured (old named as ignored);
- `level(5)` refused r(198) (old drawn);
- two observations at bwidth(1000) draw the smooth (old nothing);
- about 70 times faster at N=20000.

Run the full suite once, then the S11 truth blocks and the three area scripts through their drivers. Run `gitnexus_detect_changes()` and check `git diff --cached --name-only`. Grep the message. Commit on `wp29-s11` with the subject `Draw lpolyci's analytic band with pwidth() and var() (WP-29 P0.9)`. The body opens with `<scratch>/11-P0.9-failure.txt` and carries the `Regression:` lines, the `Flipped:` lines from `<scratch>/11-flips-P0.9.txt`, `Fixture: test/fixtures/lpolyci_truth.json (scripts/extract_lpolyci_truth.do)` and `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.9 -->' CHANGELOG.md` prints 0, and `grep -c '(WP-29, P0.9)' CHANGELOG.md BUGS.md` totals 2. `git log -2 --format=%s` shows the P0.9 subject above the P0.7 subject. `git log -2 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>P0.9 was closed in BUGS.md naming existing tests, its marker was replaced, its tracking key was deleted, and a second green commit on wp29-s11 carried the cycle.</done>
</task>

## Section completion criteria

- In both modes and after every served filter move, the default lpoly/lpolyci bandwidth is Stata's `r(bwidth)` within SD-1's tiers on every fixture row.
  - A missing or zero Stata bandwidth draws a line at 0.
  - Exact fits draw Stata's outcome, except D1-D3, which are listed in the fixture.
  - The local fit follows `invsym` (Part C).
  - LW-01..LW-07 pass.
- lpolyci draws Stata's analytic band (1e-8 at given widths, 1.5×rot pilot by default), with `pwidth()`, `var()` and twoway's level bounds, and no bootstrap. dash.ado refuses what twoway refuses, in its order apart from D6/D7, and writes `lpvar`, never `var`. LB-01..LB-05, LB-11..LB-20, LB-41..LB-43, HC6-24 and HC6-55b pass.
- Two commits on `wp29-s11`, P0.7 then P0.9, each holding its failing tests, fix, flips, fixture and closed BUGS.md entry. No test-only commit exists, and the full suite was green before each.
- No `.cscript` was created, and neither the runner nor the hygiene pins were edited. Both fixtures carry `_meta` and are committed. Every flip is recorded as a `Flipped:` line.

## Notes

- **Line numbers** are `7421d3d`'s and batch 1 shifts them (S03, S05, S07 and S08 edit `dash_render.py` and `dash.ado`). Locate everything by symbol. S05 changes how a date column reaches the mappers (Stata units). This section's mappers read whatever `_layer_weights` returns, so no date code is touched here.
- **The two NaN meanings never mix.** In `_compute_lpoly_fit`, a NaN `y_fit` at a grid point means "fewer than two weights" (missing, not drawn). A NaN BANDWIDTH means "Stata's `r(bwidth)` is missing or 0", which draws zeros. The mappers short-circuit a NaN bandwidth before calling `_compute_lpoly_fit`, whose own default path (`bwidth is None or not > 0`) would otherwise re-derive one.
- **Intercept dropped in a local window** (`0 not in K`) happens only when ΣK·w < 1e-19, a gaussian window far from every observation. It is NaN here and was not measured against Stata. SD-10's 1e-14 threshold makes Stata missing there anyway in every measured case.
- **Fast path.** The float pre-check keeps `np.polyfit` on every well-conditioned window, which is why `TestLpolyAtEveryDegree` (rtol 1e-11) and the other pins do not move. Do not route all windows through the exact path.
- **Constants and the scanner (A8).** Only literal-safe values live at module level (`_LPOLY_ROT_GRID`, `_LPOLY_ROT_CONSTANTS`, `_LPOLY_DF_TOL`). The scanners (`_shared_stat_lines` 29006-29035 and `_supply_missing_constants` 31736-31782) silently skip anything whose `repr` is not a literal, and the app would then NameError at draw time.
- **Copy lists (R2), deviations recorded as SD-11/SD-12.** P0.7's names go after `_dash_lpoly_weights` in `_shared_stat_lines`' tuple, and P0.9's after them. `"_LPOLY_ROT_C"` leaves the constants tuple. `_bootstrap_ci` stays.
- **S12 (stale cue) merges after this section.** lpolyci now has a band source separate from its line. The cue must mark the band, its outline and the line (u07b open question 5). The three sources come in the order band, outline, line.
- **S13 merges last.** If its token gates `make_document`, it updates `test_mode_parity._served` and the served helpers of `test_lpoly_rot.py`, `test_lpolyci_band.py` and `test_server_statistics.py`.
- **Shared files (R1-R8).**
  - R1: LW/LB truth blocks above the marker after S10's; LB-11..LB-20 at the end of `test_statistical_options.cscript`; LB-41..LB-43 at the end of `test_parser.cscript`.
  - R2: map keys in alphabetical place.
  - R3: only the help paragraphs named in 11-11/11-23; only the P0.7/P0.9 markers; only these two BUGS.md entries and `WP29_OPEN` keys.
  - R4: `pwidth`/`lpvar` are this section's keys; `_dash_lpolyci_opts` sits beside `_dash_kernel_flag`.
  - R5: two new fixtures, none regenerated.
  - R6: CORPUS/MOVE_CORPUS/`_MOVED_LAYERS` appends only.
  - R7: flips are recorded.
  - R8: impact before each edit, and `gitnexus_detect_changes()` before each commit.
- **Commit-body line forms (index Deltas):**
  - `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`
  - `Flipped: <node> -- <old expectation> was wrong because <why>`
  - `Fixture: test/fixtures/<name>.json (scripts/<extract script>)`
  - `BUGS.md: "<title>" (closed)`
- **Stata.** Use only `<repo>/scripts/stata_slot.sh <scratch>/s11 <file>.do` with `dash_nobrowser=1`: the extract scripts through their `W29_REPO` driver, the cscripts through the cd-test driver. Never the GUI, never a bare `stata-mp`, never `make cert`. Many concurrent sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, so check `c(python_exec)` before trusting a skip.
- **pytest.** While iterating, run only the changed files (`-n0 -p no:cacheprovider` for single nodes). Run the full suite once per commit and read its log.

### Documented divergences (each pinned by id)

| Id | What | Stata | dash |
|---|---|---|---|
| D1 | `ylin=2*weight+1`, degree 0 | h 155.93927432859499 (round-off), 50 points | float emulation (prototype 115.9), 50 points; curve up to about 239 on a range of 6160 |
| D2 | `yw=weight`, degree 0/1 | h 107.65464854502504, 49 points | prototype 122.1, 50 points; degree 1 curve exact, degree 0 up to about 37 |
| D3 | `mpg*1e-150`, degree 2 | 57.50621527011689, 45 points | zero line |
| D4 | lpolyci rows whose pilot has no residual df | missing at 9 of 12 measured rows, round-off (1.4e-7 to 6.7e-6) or 32.0 at the rest | pinched (se 0) |
| D5 | `r1000_d2_bw600` se at 2 of 50 rows | 1243.3323470880446, 660.0387356384502 | 1238.48, 618.55 (pilot at round-off) |
| D6 | `if _n==1, pwidth(0)` | r(2001) | r(198) pwidth message (count checked after options) |
| D7 | `level(5) degree(abc)`, `pwidth(0) n(abc)`, `var(0) bwidth(0)`, `var(0) kernel(foo)`, `var(0) degree(-1)` | twoway's words | the same option named, in dash's words |
| D8 | `pwidth(+800)` | r(3000) `expression invalid` | accepted as 800 |
| D9 | `pwidth()`/`var()` on lpoly, scatter, lfitci, kdensity | r(198) | rc 0 with the unsupported note (A12 pending) |

### Notes for the closeout (S15 only, A5)

- **GAPS2.md:**
  - A9 (A9-a, A9-b), C1 and C13: closed by P0.7.
  - C12: only its "lpoly default bandwidth for degree 2/3 and other kernels" bullet (C12-e) is closed by P0.7; the rest stays.
  - A10 (A10-a, A10-b) and C7 (C7-a, C7-b, C7-c, C7-e): closed by P0.9.
  - C4/E4 stay with S12.
- **TWOWAY_COVERAGE_AUDIT.md:**
  - rows 92-93 (lpoly/lpolyci) and line 18: remove "default bandwidth is an approximation";
  - row 93 and line 27: the band is Stata's analytic band;
  - AUDIT-23 and AUDIT-24 are closed.
- **ROADMAP.md:**
  - the WP-18 follow-up "lpolyci bootstrap" (about :2530 "`_bootstrap_ci` remains for lpolyci", and :2704) is closed by P0.9;
  - record the measured cost (lpolyci at N=20000, from the P0.9 commit body).
- **PLAN.md BR-29.6 / K4:** restate "1e-9 relative" as SD-1's tiers. The measured floor of agreement is Stata's own float64 arithmetic (1.6e-5 on years at degree 2/3).
- **New residuals to record:**
  - SD-10: twoway counts a gaussian weight toward the two-observation rule only above about 1e-14 (`kernel(gaussian) bwidth(1)` on auto: 3 points in Stata, 23 in dash). Suggested grade S3; the owner is the next lpoly unit.
  - D1-D3 and D4-D9 above.
  - SD-7: degree 4-7 constants are dormant until P1.14 lifts `degree=int,0,3`.
  - SD-5: the A12 refuse-vs-note decision for pwidth()/var() on other types.
- **AGENTS.md invariants:**
  - "lpoly/lpolyci bandwidths come from `_lpoly_rot_detail` (NaN = Stata missing = a zero line); local fits keep `_lpoly_kept_columns`; the band is `_lpoly_se` with a pinch on no-df rows; the option key is `lpvar`, never `var` (test_lpolyci_band.py::TestNoVarKey, test_parser.cscript LB-41)."
  - "No module-level non-literal constant may be read by a copied helper."
