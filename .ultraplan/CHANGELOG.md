# CHANGELOG — behaviour changes from the conformance work

Every entry here changes a number or a picture a user has already seen. Each
one records the value before, the value after, and the evidence.

Ground truth throughout comes from Stata itself, recorded in
`test/fixtures/*.json` with the command that produced each value beside it.

---

## S07 — statistical defaults now come from the data, the user's options and `c(level)`

### Changed defaults

| layer | before | after | evidence |
|---|---|---|---|
| `histogram` bin count | **always 10** | `int(min(sqrt(N), 10·ln N/ln 10))` — 8 on auto/mpg, 33 on nlsw88/wage, 15 on sp500/close | `histogram_bin_rule_check`, 8 probes, 4 datasets |
| `histogram` y-axis | raw **counts** | **density** (bar areas sum to 1) | `help histogram`: "density is the default" |
| `kdensity` kernel | gaussian (scipy `gaussian_kde`) | **epanechnikov** | `help kdensity`, `r(kernel)` |
| `kdensity` bandwidth | scipy's Scott factor | `0.9·min(sd, IQR/1.349)·N^(-1/5)` | matches Stata's `r(bwidth)` to 1e-12 on 4 datasets |
| `kdensity` grid | 400 points | **300** | `help twoway_kdensity`: "The default is n(300)" |
| `lpoly` kernel | gaussian | **epanechnikov** | `help lpoly` |
| `lpoly` bandwidth | 0.5 × x-range, clamped to [0.01, 1.0] | absolute, in x units; default from a rule of thumb | `help lpoly`: bwidth is "the half-width of the kernel" |
| `lfitci`/`qfitci` grid | 200 points, x-range padded 10% each side | **100 points over the observed range** | `_gs_x_create.ado` |
| `qfitci` band | bootstrap, 500 resamples | **analytic `stdp`**, as Stata | `twoway__lfit_serset.ado:81-95` |
| `fpfit`/`fpfitci` domain | 1st–99th percentile | **full observed range** | measured: nlsw88 [0.115, 28.885], not [1.923, 21.417] |
| `fpfit`/`fpfitci` grid | 200 and 150 points | **the distinct observed x values**, as Stata | measured: 64/50/242/1546 points |
| `mband` bands | `clip(ceil(n/5), 2, 20)` — 15 on auto | `round(min(sqrt N, 10·log10 N))` — **9** on auto | reproduces all 14 measured (N, bands) pairs |
| `mband` x position | band **midpoint** | **median of x within the band** (Stata's cross-medians) | measured band points, 4 datasets × 2 band counts |
| `function` grid | 200 points | **300** | `help twoway_function`: "The default is n(300)" |
| confidence level | **95, hardcoded in four places** | `level()`, defaulting to `c(level)` | `twoway__lfit_serset.ado:10` |
| bootstrap resamples | 200 in three call sites, 500 in a fourth | one constant, 200 | — |

### Bugs fixed

- **`function y=x^2` drew nothing.** Stata spells exponentiation `^`; Python
  reads `^` as a bitwise XOR, which passed the AST whitelist and then raised
  `TypeError` on the float array, producing a silent empty red line. `^` is now
  translated to `**` *before* validation — the whitelist is unchanged, and an
  adversarial test confirms it.
- **The `lfitci` band was wrong by a factor of `sqrt(Sxx/(n-2))`.** The code
  multiplied the slope's standard error by `sqrt(n-2)` where `stdp` needs
  `sqrt(Sxx)`. On `sysuse auto` that is a band roughly 90 times too wide.
- **The `qfitci` band came out about half as wide as Stata's.** The Gram matrix
  of the raw design `[1, x, x²]` has a condition number near 2.6e16, at which
  point `pinv` discards a real singular value. The design is now centred and
  scaled.
- **`kdensity` jumped the first time any filter was touched**, even when no rows
  were removed: the first render used scipy's Scott factor and the filter
  callback used Silverman. Both now use Stata's rule, and a test executes the
  real JavaScript under node and compares it to the Python curve point for
  point.
- **`lowess, bwidth(notanumber)` killed the whole render.** A bare `float()`
  with no guard. All statistical options now go through one coercion helper
  that reports bad input and carries on.
- **`lpoly, bwidth(5)` did the opposite of what was asked.** Clamped to 1.0 and
  multiplied by the x-range, `bwidth(5)` on `weight` became a bandwidth of 3080
  — the entire dataset.
- **`bins()` was reported as unsupported.** Stata accepts `bin()`, `bins()` and
  `b()` for `twoway histogram`; dash declared only `bin()`.
- A density histogram under a filter now **renormalises** to the surviving rows.
  Bin boundaries deliberately stay put.
- `kdensity` no longer imports scipy at all. `qfitci` still does not: the
  Student-t quantile it now needs is computed from the regularised incomplete
  beta, agreeing with scipy to 5e-12 over 70 (p, df) pairs.

### Three places the plan's register was wrong, corrected from Stata

1. **`function` default range.** The plan required the x-axis range. Stata
   documents *and* plots `range(0 1)` — unchanged even when another plot is
   present. dash's existing behaviour was right; only ignoring an explicit
   `range()` was a bug.
2. **`fpfit` `bwidth()`/`degree()`.** The plan said to honour them because
   `dash.sthlp` documented them. Stata *rejects* both with r(198) — a
   fractional polynomial has no bandwidth, and its degree is spelled
   `estopts(degree(#))`. They are now accepted, reported as ignored, and the
   help has been corrected.
3. **`fpfit` grid size.** The plan asked for "one grid size". Stata uses no
   grid at all.

And one place Stata's own documentation is wrong: `help twoway_mband` documents
`max(10, round(10·log10 N))` bands, which gives 19 on auto where Stata draws 9.
The measured rule fits 14 of 14 probes; the documented one fits 3.

### Known approximation, stated rather than hidden

The **default** `lpoly` bandwidth approximates Stata's rather than reproducing
it. Stata computes its rule of thumb in compiled Mata and it is not derivable
from the published documentation. dash uses the Fan–Gijbels rule of thumb with
a constant measured against Stata on seven datasets; the implied constant
ranged over [0.597, 0.720], so the default lands within about ±11%. An explicit
`bwidth()` is exact. This is stated in `dash.sthlp`, in the function's
docstring, and pinned by a test with a 20% tolerance.
