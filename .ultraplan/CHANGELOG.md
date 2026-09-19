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


---

## S08 — display formats, dates, and a dashboard that contained no data

### The headline defect

`dash line close date` on `sysuse sp500` produced a dashboard with **zero
data points** and returned rc 0. Verified end to end: the embedded Bokeh
document held `"shape":[0]` for index, date and close.

The section's premise was wrong about why. It said a `%td` variable "arrives
as a raw Stata SIF integer and gets a linear axis reading 14.0k". Measured, it
does not arrive as a number at all: **jsonio renders every `%t*` variable
through its display format and emits a JSON string** — sp500's `date` arrived
as `"02jan2001"` — while still reporting `variableIsString = false` for it.
`_load_data` then ran `pd.to_numeric(errors="coerce")` over it, every date
became NaN, and every row was dropped.

dash now gives a date variable a plain numeric format for the duration of the
jsonio call, so the underlying value is transported intact, and carries the
display format separately in `build_options["formats"]`. jsonio is not
modified. A spec from an older dash.ado, still carrying display strings, is
parsed rather than coerced away.

### A second transport defect found alongside it

`_load_data` read **`variableTypeIsString`**. Real jsonio emits
**`variableIsString`**. The key dash looked for is never present in
production, so its string-column detection had never run outside the test
suite — and `conftest.make_data_json` fabricated the wrong key, so the suite
could not see it. Both keys are now honoured, and the helper emits both.

### What changed

| where | before | after |
|---|---|---|
| date columns | coerced to NaN, every row dropped | datetime64, all eight epochs |
| axes | linear | `DatetimeAxis` with a formatter matched to the date kind |
| `xscale(log)` on a date | silently a log axis | a date axis, with a warning |
| hover | raw variable NAMES, raw values, three different hardcoded precisions | variable labels, dates as dates, formatted numerics, one precision derived from the data |
| `filter(date, type(range))` | **no widget at all** — a datetime64 column fails `is_numeric_dtype` | `DateRangeSlider` with date bounds |
| `filter(date, type(slider))` | no widget | `DateSlider` |
| `filter(date, type(dropdown))` | epoch numbers | dates |
| `kpi max(date)` | `15340` | `31 Dec 2001` |
| a filtered date KPI | a raw number | still a date |
| `kpi sum(date)` | silent nonsense | still computed, now reported as meaningless |
| `by(datevar)` facet titles | raw values | dates |
| `mlabel(datevar)` | raw values | dates |
| a KPI with no `fmt()` | `%9.0f` | the variable's own Stata display format |

`%tC` is converted with the same epoch as `%tc` and **warns** that leap
seconds are not applied — measured at 9 s in 1980 rising to 27 s in 2020.
Leap-second data IS available in Stata, so this is an approximation, and it
says so rather than being silent.

### The wire-format trap the section warned about

The plan said the epoch-millisecond comparison in the filter JS "should work —
verify this rather than assuming, because a mismatch silently filters
nothing". Verified, and it did not work: Bokeh sends the live column as epoch
milliseconds, but dash's own `orig_data` snapshot serialised the same column
as date **strings**, because `_to_serialisable` calls `float(v)`, which raises
on a Timestamp and falls through to `str(v)`. Dragging the slider filtered
nothing and every date KPI collapsed to 0. Four tests now pin the two
representations together.

A related unit trap: pandas 3 preserves the resolution it inferred, so a
datetime column can be `datetime64[us]` or `[ns]`. Dividing a raw
`astype("int64")` by a fixed constant yields seconds for one and milliseconds
for the other; the cast is now to an explicit `datetime64[ms]`.

### Found but NOT fixed here — owned by S13

**`filter()` is inert on any plot type that derives its own ColumnDataSource.**
Found while checking the date filter in a browser, and it is not
date-specific. `map_line` sorts by x and builds a new ColumnDataSource, but
`render()` passes `self.sources` to the filter callback, so the callback
updates a source no glyph is bound to. Measured on a real sp500 build:

- `line`: four sources — two at n=248 that the figures render, two at n=5 that
  the callback filtered
- `scatter`: two sources, filtered and rendered, and the filter works

Recorded as a strict xfail in `test/test_filters.py`, written before any fix,
per project rule 8.

### Visually verified

The sp500 exemplar (`examples/sp500_dates.do`, new) was built from Stata and
opened in a browser: calendar dates on the x-axis, dates in both KPI cards, a
date range slider reading "02 Jan 2001 .. 31 Dec 2001", and KPIs that
recompute to "22 Oct 2001" and a lower peak close when the slider is dragged.
The graph itself does not move, for the S13 reason above.
