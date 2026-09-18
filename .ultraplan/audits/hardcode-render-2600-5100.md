# Hardcoded-value audit — `dash_render.py` lines 2600–5100

Scope: `map_lowess` .. `_load_data`. All line numbers verified by reading the code.

## Reachability ground truth (verified, not assumed)

`dash.ado` parses plot options with `_dash_parse_plot_opts` (`dash.ado:291-326`).
Its `syntax` block accepts **only** these statistically-relevant keys:

```
bwidth(string)   degree(string)
```

Nothing else. `bin()`, `n()`, `range()`, `kernel()`, `level()`, `width()`, `start()`,
`at()`, `bands()`, `percent`, `frequency`, `density`, `fraction`, `discrete`, `mean`,
`noweight`, `logit`, `adjust` are **absent**.

Three independent confirmations that these can never reach the renderer:

1. `dash_parse.mata:179-253` (`_expand_optkey`) **passes unknown option keys through
   unchanged** (`return(name)` at line 252) — it does not drop them.
2. `dash.ado:668` calls `_dash_parse_plot_opts , \`opts_exp'` with **no `capture`**, so an
   unrecognised key is a hard `exit 198` ("option bin() not allowed"). The user's command
   *aborts*; the default is not merely unused, it is unusable.
3. Even if `syntax` accepted them, `_dash_plot_opts_to_json` (`dash.ado:468-493`) only
   serialises a fixed `foreach key in ...` list (lines 476-482) that likewise excludes them.

=> Every `options.get("bin"…)`, `popts["range"]`, `popts["n"]` read in the renderer is an
**UNREACHABLE DEFAULT**. Marked `[UNREACHABLE]` below.

Conversely `bwidth()` and `degree()` **are** reachable — which makes the mappers that
*ignore* them (kdensity, fpfit, fpfitci) worse, not better.

`scheme()` is reachable (`dash.ado:239`, `:319`), so scheme-derived values are user-controllable.

---

## Findings

### A. `map_histogram` (2967–3031)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| A1 | `dash_render.py:3001` | `10` in `options.get("bin", 10)` | Fixed 10 bins for **every** histogram, any N | Stata's rule `min(sqrt(N), 10*ln(N)/ln(10))` rounded, from `len(arr)` | `bin(#)` — **yes in Stata, [UNREACHABLE] in dash** (`syntax` at `dash.ado:293-326` rejects `bin()`) | HIGH |
| A2 | `dash_render.py:3003` | `np.histogram(arr, bins=n_bins)` | y = **raw counts** always | Stata `histogram`'s default y-axis is **density**, not frequency | `density`/`fraction`/`percent`/`frequency` — yes in Stata, **none reachable** | HIGH |
| A3 | `dash_render.py:3003` | edges implicit = `arr.min()`..`arr.max()` | Bin origin/width always spans observed data | `start()` / `width()` | `start(#)`, `width(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| A4 | `dash_render.py:2967-3031` | — (absent) | No discrete-variable handling; a 0/1 var gets 10 continuous bins | `discrete` auto-detect from `np.unique(arr)` | `discrete` — yes in Stata, **[UNREACHABLE]** | MEDIUM |
| A5 | `dash_render.py:3000` | `_MAX_BINS = 1000` | DoS cap | Fine as a guard, but it is the only thing between `bin` and `np.histogram` | n/a | LOW |
| A6 | `dash_render.py:3001` | `int(...)` unguarded | `int("abc")` raises uncaught `ValueError` (contrast `map_lpoly:2666-2669` which try/excepts) | — | n/a | LOW (unreachable today) |
| A7 | `dash_render.py:3013` | `line_color="white"` | Bin border always white — invisible on a white `plotregion`, wrong on dark schemes | `self.scheme.plotregion_color` / `scheme.axis_line_color` | `blcolor()` reachable but not read here | MEDIUM |
| A8 | `dash_render.py:3014` | `fill_alpha=0.8` | Fixed | `self.scheme.bar_alpha` (exists at `:966`, **never read anywhere**) | `fintensity()` does reach via `_apply_fill_opts` | MEDIUM |

### B. `map_kdensity` (3033–3088) and its JS twin

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| B1 | `dash_render.py:3066` | `gaussian_kde(arr)` | Kernel hardcoded **Gaussian** | Stata `kdensity` default kernel is **epanechnikov** | `kernel()` — yes in Stata, **[UNREACHABLE]** | HIGH |
| B2 | `dash_render.py:3068` | `kde.covariance_factor()*arr.std()` | Bandwidth = scipy **Scott's rule**. `bwidth` is **never read**, although `bwidth()` *is* a reachable dash option (`dash.ado:309`) | `options.get("bwidth")`, else Stata's ROT | `bwidth(#)` — yes, **reachable and silently ignored** | HIGH |
| B3 | `dash_render.py:3069` | `400` | 400 grid points always | `n()`; Stata's default is `min(N, 50)` | `n(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| B4 | `dash_render.py:3069` | `3 * bw` padding | Domain = `min-3bw .. max+3bw` | `at()` / explicit range; the factor 3 is arbitrary | `at()`, `range()` — yes in Stata, **[UNREACHABLE]** | MEDIUM |
| B5 | `dash_render.py:4617` vs `:3068` | JS `h = 0.9*bw_scale*n^-0.2` (**Silverman**) | The filter-callback KDE uses a **different bandwidth rule** from the Python initial render (Scott's). Touching any filter makes the curve visibly jump even when no rows are removed. Comment at `:3080-3081` admits this ("consistent approximation") | Both sides must use one rule, ideally the user's `bwidth()` | same as B2 | HIGH |
| B6 | `dash_render.py:4616` | `iqr / 1.34` | Silverman constant | Constant is standard; but it is dead-reckoned in JS with no Python counterpart | n/a | LOW |
| B7 | `dash_render.py:4613-4614` | `Math.floor(0.25*(n-1))`, `Math.floor(0.75*(n-1))` | Nearest-rank quartiles, **no interpolation** — disagrees with `np.percentile`/`pandas.quantile` used elsewhere (`:5134-5137`) | Linear-interpolated quantile to match the Python path | n/a | MEDIUM |
| B8 | `dash_render.py:4619` | `INV_SQRT_2PI` | Hardcodes the **Gaussian** kernel again in JS | Must follow `kernel()` once B1 is fixed | n/a | HIGH (with B1) |

### C. `map_lowess` (2525–2572)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| C1 | `dash_render.py:2560` | `"0.8"` | Default `frac=0.8`. Matches Stata's default, **but** it is `float()` with **no try/except and no clamp** — unlike `map_lpoly:2666-2669`. `bwidth(abc)` → uncaught `ValueError` traceback; `bwidth(0)`/`bwidth(5)` → statsmodels error | `max(0.01, min(1.0, ...))` like lpoly | `bwidth(#)` reachable; value validation missing | HIGH |
| C2 | `dash_render.py:2561` | `lowess(y, x, frac=bw, return_sorted=True)` | `it` (robustness iterations) left at statsmodels' default 3; `mean`, `noweight`, `logit`, `adjust` have **no code path at all** | `options.get("mean"/"noweight"/"logit"/"adjust")` | `mean`, `noweight`, `logit`, `adjust` — yes in Stata, **[UNREACHABLE]** (not in `syntax`) | HIGH |
| C3 | `dash.sthlp:559-565` vs code | doc says `bwidth()` applies to "lpoly, lpolyci, fpfit, fpfitci" | `bwidth` for **lowess** is undocumented, and for **fpfit/fpfitci** is documented but ignored (see E4) | — | doc/code mismatch | MEDIUM |

### D. `map_lpoly` / `map_lpolyci` / `_compute_lpoly_fit` (2578–2768)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| D1 | `dash_render.py:2667`, `:2734`, `:2582` | `0.5` default + clamp `[0.01, 1.0]` | Treats `bwidth` as a **fraction of the x-range** (`h = bwidth * x_range`, `:2604`). Stata's `lpoly bwidth()` is an **absolute bandwidth in data units**. A user writing `bwidth(5)` for `weight` (range ~3000) gets silently clamped to `1.0` = the entire x-range — the exact opposite of the requested narrow window | Stata's rule-of-thumb bandwidth from the data (Fan & Gijbels ROT), and `bwidth()` interpreted in data units | `bwidth(#)` — yes, **reachable but semantically wrong** | HIGH |
| D2 | `dash_render.py:2611` | `np.exp(-0.5*((x-x0)/h)**2)` | Kernel hardcoded **Gaussian** | Stata's `lpoly` default kernel is **epanechnikov** | `kernel()` — yes in Stata, **[UNREACHABLE]** | HIGH |
| D3 | `dash_render.py:2584` (`n_grid=200`), `:2744` (`n_grid = 100`) | `200` / `100` | Evaluation-point count fixed; the CI variant silently uses a *different, coarser* grid than the non-CI variant, so `lpoly` and `lpolyci` on the same data draw different curves | `n()`; Stata's default is `min(N, 50)` | `n(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| D4 | `dash_render.py:2606` | `np.linspace(x.min(), x.max(), n_grid)` | Domain always observed x-range | `at()` / `range()` | yes in Stata, **[UNREACHABLE]** | MEDIUM |
| D5 | `dash_render.py:2673`, `:2740` | `min(3, ...)` degree cap | Caps degree at 3 | arbitrary but harmless; default 0 does match Stata | `degree()` reachable | LOW |

### E. Fit CI bands + fractional polynomial (1297–1345, 2843–2965)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| E1 | `dash_render.py:1343-1344` | `np.percentile(boot_preds, 2.5)` / `97.5` | **Confidence level hardcoded at 95%** for `lpolyci`, `fpfitci`, `qfitci` (`:2512`) and every other `*ci` type. `level()` has no code path anywhere | `c(level)` (Stata default 95) with `level()` override → `(100-level)/2` and `100-(100-level)/2` | `level(#)` — yes in Stata, **[UNREACHABLE]**; `c(level)` never read | HIGH |
| E2 | `dash_render.py:1303` (`n_boot=200`), `:2755`, `:2953` | `200` | Bootstrap resample count fixed; also means the band is a *bootstrap* band, not Stata's analytic prediction SE band | `reps()`-style option, or analytic SE | no Stata analogue (Stata uses analytic CI) | MEDIUM |
| E3 | `dash_render.py:1304` | `seed: int = 42` | Fixed RNG seed | `set seed` / `jseed()`-style; `jseed()` is already reachable for jitter | no direct analogue | LOW |
| E4 | `dash_render.py:2843-2896`, `:2898-2965` | — | `map_fpfit`/`map_fpfitci` **never read `bwidth` or `degree`**, yet `dash.sthlp:559-560` states those options "apply specifically to lpoly, lpolyci, **fpfit, and fpfitci**". Degree is permanently 2 | `options.get("degree")` to pick FP1 vs FP2 | `degree()` reachable, **silently ignored** | HIGH |
| E5 | `dash_render.py:2880-2883` | `np.percentile(x, 1)`, `np.percentile(x, 99)`, `200` | FP curve is **truncated to the 1st–99th percentile** of x. Stata plots `fpfit` across the full estimation range. Visually the curve stops short of the scatter on both ends | `x[x>0].min()` / `x.max()`, plus `range()` and `n()` | `range()`, `n()` — yes in Stata, **[UNREACHABLE]** | HIGH |
| E6 | `dash_render.py:2941-2944` | `np.percentile(x,1)`, `np.percentile(x,99)`, `150` | Same truncation as E5, **and a different point count (150 vs 200)** than `map_fpfit`, so `fpfit` and `fpfitci` disagree | as E5 | as E5 | HIGH |
| E7 | `dash_render.py:2775` | `_FP_POWERS = (-2,-1,-0.5,0,0.5,1,2,3)` | Fixed power set | Correct — this *is* Stata's set (Royston & Altman) | `powers()` exists in `fp` but not `twoway fpfit` | LOW |
| E8 | `dash_render.py:2806-2807`, `:2814` | `best_p1,best_p2 = 1.0,2.0`; `valid.sum() < 4` | Fallback powers and minimum-N threshold | `4` should be `n_params+1`; the silent fallback masks a failed fit | n/a | LOW |
| E9 | `dash_render.py:1287`, `:2725`, `:2932` | `fill_alpha=0.2` | CI band opacity fixed | `self.scheme.fill_alpha` (`:965`, never read) | `falpha()`/`fintensity()` reach via `_apply_fill_opts` on the non-empty path only | MEDIUM |

### F. `map_function` + AST validator (4117–4252, caller at 5949–5967)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| F1 | `dash_render.py:4121` (`x_range=(0.0,1.0)`) and `:5951` (`x_lo, x_hi = 0.0, 1.0`) | `(0.0, 1.0)` | **Every** `twoway function` in dash is plotted over x ∈ [0,1]. The `range` read at `:5953` is dead because `range()` is rejected by `dash.ado`'s `syntax` | The figure's x-axis data range (Stata's documented default), or `range()` | `range(# #)` — yes in Stata, **[UNREACHABLE]** — `dash (function y=x^2), range(0 10)` **aborts with "option range() not allowed"** | HIGH |
| F2 | `dash_render.py:4122` (`n_points=200`) and `:5952` (`n_pts = 200`) | `200` | Stata's `twoway function` default is **`n(300)`**. The `popts["n"]` read at `:5960` is dead for the same reason | `n()`; default 300 | `n(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| F3 | `dash_render.py:4249`, `:4213`, `:4245` | `line_color="#d62728"` | Function curves are **always matplotlib-red**, ignoring the scheme. Every other mapper in this range uses `self.scheme.default_color(color_idx, "line")`. `map_function` is not even passed a `color_idx` (`:4117-4124`) | `self.scheme.default_color(color_idx, "line")` | `lcolor()` does still override via `_apply_line_opts` at `:4251`, but the *default* is off-scheme | HIGH |
| F4 | `dash_render.py:4250` | `expr[:40]` | Legend label truncated at 40 chars with no ellipsis | `legend()` / full expr | `legend()` is reachable at graph level | LOW |
| F5 | `dash_render.py:4155-4159` | `_SAFE_NAMES`, `_SAFE_FUNCS` | Whitelist omits Stata `twoway function` staples: `min`, `max`, `mod`, `round`, `int`, `sum`, `normal`, `invnormal`, `ln`, `cond()` | Extend whitelist (keeping the AST gate) | Stata allows any expression | MEDIUM |
| F6 | `dash_render.py:5963` | `min(int(popts["n"]), 10000)` | DoS cap | Reasonable guard | n/a | LOW |
| F7 | `dash_render.py:4216` | `int(n_points)` after `float()` of range | No guard that `x_lo < x_hi`; reversed range silently yields a descending grid | validate | n/a | LOW |

### G. `map_mspline` (3975–4042) and `map_mband` (4044–4115)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| G1 | `dash_render.py:4033` | `np.linspace(..., 200)` | 200 output points always; and PCHIP is fit through **every** data point — there is no banding stage at all | `n()`; Stata's `mspline` cross-medians the data into `bands()` bands first (default `min(#unique x, 100)`) then splines | `bands(#)`, `n(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| G2 | `dash_render.py:4085` | `np.clip(ceil(len/5), 2, 20)` | Band count for `mband` invented as "~5 obs per band, capped at 20" | `bands()`; Stata's `twoway mband` default is `bands(#)` chosen from N, not capped at 20 | `bands(#)` — yes in Stata, **[UNREACHABLE]** | HIGH |
| G3 | `dash_render.py:4091` | `np.linspace(x_min, x_max, n_bands+1)` | Equal-**width** bands | Stata's `mband` uses equal-**count** (cross-median) bands by default | `bands()` semantics | MEDIUM |
| G4 | `dash_render.py:4080` | `len(x_clean) < 4` | Arbitrary minimum-N | n/a | no | LOW |

### H. Scheme values that exist but are never consumed (systemic)

`SchemeParser._init_properties` (`dash_render.py:918-974`) computes:
`default_line_width` (`:961`), `fill_alpha` (`:965`), `bar_alpha` (`:966`), `area_alpha`
(`:967`), and the public `default_symbol()` (`:996`) / `default_line_pattern()` (`:1000`).

**Verified by grep: none of these six is read anywhere in the 10,455-line file** — the only
hits are their own definitions. Every mapper hardcodes the value instead, so
`scheme(s1mono)` / `scheme(economist)` cannot change line weight, fill opacity, marker
symbol, or dash pattern.

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| H1 | `2686, 2728, 2893, 2935, 3075, 4039, 4112, 4249` and `1291` | `line_width=2.0` | All smoother/fit lines 2.0px | `self.scheme.default_line_width` (`:961`) | `scheme()` reachable; `lwidth()` overrides per-plot but the default is off-scheme | HIGH |
| H2 | `3206, 3260, 3264, 3267, 3306, 3310, 3438, 3505, 3508, 3510, 3634, 3771, 3843` | `line_width=1.5` | All range/pc/dropline segments 1.5px | same as H1 | same | HIGH |
| H3 | `1287, 2725, 2932` (`0.2`), `3123` (`0.5`), `3014` (`0.8`) | three different fill alphas | Band 0.2, rarea 0.5, histogram 0.8 — no common source | `scheme.fill_alpha` / `area_alpha` / `bar_alpha` | `scheme()` | HIGH |
| H4 | `3440, 3716, 3967` (`size=8`), `3512, 3514` (`size=7`) | marker px sizes | Fixed marker sizes, inconsistent between `rcap` caps (7) and others (8) | `OptionTranslator.translate_msize(options.get("msize","medium"))` — already exists at `:606` | `msize()` reachable | HIGH |
| H5 | `3785, 3856-3857` | `OpenHead(size=10)`, `NormalHead(size=10)` | Arrowhead size fixed | `msize()` (Stata `pcarrow` sizes the head with `msize()`) | `msize()` reachable, ignored | MEDIUM |
| H6 | `3168` | `line_alpha=0` | `rbar` outline forced fully transparent | `blcolor()`/`lcolor()`; `_apply_fill_opts` at `:3173` cannot restore it | `blcolor()` reachable | MEDIUM |

### I. Reachable options silently dropped by specific mappers

| # | file:line | Literal / omission | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| I1 | `dash_render.py:3415`, `:3425` | `zeros = np.zeros_like(x_arr)`; `"y0": zeros` | `dropline` drops are **always to y=0**. Contrast `map_bar` (`:2094`), `map_area` (`:2186`), `:2258` which all honour `base` | `float(options["base"])` | `base(#)` — **reachable** (`dash.ado:302`), silently ignored | HIGH |
| I2 | `dash_render.py:3440` + `:3446-3448` | `size=8`; only `_apply_line_opts(seg)` and `_apply_mlabel_opts` are called — **`_apply_marker_opts(dot, options)` is never called** | `dropline`'s dot ignores `msymbol()`, `msize()`, `mfcolor()`, `mlcolor()`, `malpha()`, `msangle()` | `self._apply_marker_opts(dot, options)` | `msymbol()`, `msize()` etc. — **reachable**, ignored | HIGH |
| I3 | `dash_render.py:3161-3164` | `0.8 *` min x-spacing, `default=0.8` | `rbar` bar width from data spacing only. `map_bar` at `:2175-2176` *does* honour `barwidth`/`width`; `map_rbar` does not, and `_apply_fill_opts` (`:1488-1521`) handles only `fcolor`/`fintensity` | `options.get("barwidth")` | `barwidth(#)` — **reachable**, ignored | HIGH |
| I4 | `dash_render.py:3246`, `:3248`, `:3486`, `:3488` | `cap_hw = 0.2 * min(diff)`, fallback `0.2` | `rcap`/`rcapsym` cap half-width fixed at 20% of x-spacing. Stata sizes rcap caps via `msize()` | `translate_msize(options.get("msize"))` scaled to data units | `msize()` — **reachable**, ignored | HIGH |
| I5 | `dash_render.py:3158` | `width=0.8` | Empty-`rbar` placeholder width | data spacing | as I3 | LOW |
| I6 | `dash_render.py:3309` | `color_idx + 1` | `rline`/`tsrline` upper line silently consumes the *next* palette slot, so the following plot's colour shifts | explicit per-boundary colour | `lcolor()` applies to **both** lines (`:3316-3317`), so the two can't be coloured separately | MEDIUM |
| I7 | `dash_render.py:3352-3379` | `map_dot` = `map_scatter` verbatim | `twoway dot` renders as a plain scatter — no dotted droplines, no categorical y | Stata `dot` options (`dotextend`, `ndots`, …) | none reachable | MEDIUM |
| I8 | `dash_render.py:3869-3894`, `:3896-3923` | `map_tsline`/`map_tsrline` delegate verbatim | No time-axis handling: no `DatetimeTickFormatter`, no `tlabel()`/`ttitle()`, no `%td` awareness. Combined with J1, a `tsline` x-axis shows days-since-1960 as bare integers | Stata display format of the `tsset` timevar | `tlabel()`, `ttick()` — **[UNREACHABLE]** | HIGH |

### J. `_load_data` (5051–5083) and `__init__` (4946–5045)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| J1 | `dash_render.py:5061-5083` | keys `values`, `variableLabels`, `valueLabels`, `valueLabelNames`, `variableTypeIsString` | **Stata display formats are never read.** No `variableFormats` / `displayFormat` key is requested anywhere. Confirmed upstream: `dash.ado:959-961` calls `jsonio out ..., metaprint(varnames varlabels vallabs labelnames)` — formats are **not even asked for**. Consequence: `%td` dates render as `22646`, `%tc` as milliseconds, `%9.0fc` loses thousands separators, `%9.2f` loses fixed decimals — on axes, hover tooltips, dropdown labels and slider ends | `jsonio ... metaprint(... formats)` → map `%td`/`%tc` to `pd.to_datetime` + `DatetimeTickFormatter`, `%*fc` to `NumeralTickFormatter("0,0")` | Stata's `twoway` honours the display format automatically on every axis | HIGH |
| J2 | `dash_render.py:5081-5083` | `pd.to_numeric(..., errors="coerce")` for every non-string column | Forces **float64** on all numerics. Stata `byte`/`int`/`long` lose integrality; `int64` IDs > 2^53 lose precision; a coercion failure becomes a silent `NaN` with no log line | `variableTypes` from jsonio → `Int64`/`float64` | n/a (data property) | MEDIUM |
| J3 | `dash_render.py:5083` | `errors="coerce"` | Silent data loss, no warning/log despite CLAUDE.md #14 (robust logging) | log coerced-count per column | n/a | MEDIUM |
| J4 | `dash_render.py:4983-4989` | `_THEME_SCHEME_MAP` = 5 fixed entries | Only `default/clean/mono/economist/sj` alias | scheme directory listing (`schemes/`) | `scheme()` reachable; unknown names fall through to `SchemeParser` then `s2color` | LOW |
| J5 | `dash_render.py:5000`, `:5005` | `"s2color"` fallback | Hardcoded twice | `c(scheme)` — Stata's *current* scheme | Stata's default follows `set scheme` | MEDIUM |
| J6 | `dash_render.py:5002-5005` | `except (ValueError, OSError): self.scheme = SchemeParser("s2color")` | A bad `scheme()` is swallowed **silently** — the user gets s2color with no message | warn | n/a | MEDIUM |
| J7 | `dash_render.py:4940-4943` | `g_spec["graph_options"]["hover"]` | Reads a `hover` graph option that **does not exist in `dash.ado` at all** (grep: zero hits for "hover" in `dash.ado`). Dead code; hover-variable selection is unreachable | add `hover(varlist)` to `_dash_parse_graph_opts` (`dash.ado:230-246`) | none — **[UNREACHABLE]** | MEDIUM |

### K. `_FILTER_JS` / KPI recompute (4389–4633)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| K1 | `dash_render.py:4504-4528` | statistic list `count, mean, sum, min, max, median/p50, dcount, sd` | **`p25` and `p75` are missing.** Both are accepted by `dash kpi` (`dash.ado:1080`: `valid_stats "mean sum count dcount min max median sd p25 p50 p75"`) and both are computed correctly for the initial render (`dash_render.py:5134-5137`). On the first filter interaction a p25/p75 KPI falls through to `let result = 0` (`:4502`) and **displays 0** | Add p25/p75 (and match `pandas.quantile` interpolation) | `dash kpi p25(var)` — **reachable, silently broken** | HIGH |
| K2 | `dash_render.py:4523` | `stat === 'sd' && vals.length > 1` | With exactly 1 surviving row `sd` shows **0**, not missing. `float(col.std(ddof=1))` gives `NaN` on the Python side — initial render and filtered render disagree | emit `NaN`/`.` | n/a | MEDIUM |
| K3 | `dash_render.py:4531` | `result.toFixed(k.decimals)` | `k.decimals` **is** derived from `fmt()` (`:7278` via `_parse_fmt`), so this one is *not* hardcoded — but the upstream default `_kdef.get("fmt", "%9.0f")` at `:7277` means an unformatted KPI silently rounds to **0 decimals** | `c(format)` of the variable (see J1) | `fmt()` reachable | MEDIUM |
| K4 | `dash_render.py:4542-4547` | `padding:20px`, `min-width:160px`, `min-height:110px`, `border-radius:8px`, `border:1px solid #dee2e6`, `font-size:13px/36px/11px`, `color:#6c757d` | KPI card CSS baked into the JS string. **Duplicated verbatim at `dash_render.py:6294-6299`** (the Python initial-render template) — two copies that must be kept in sync by hand. Both ignore `scheme.heading_font_size` (`:971`), `scheme.text_font_size` (`:970`), `scheme.background_color` (`:921`) | one shared template fed from `SchemeParser` | `scheme()` reachable | MEDIUM |
| K5 | `dash_render.py:4534` | `/\B(?=(\d{3})+(?!\d))/g` | Thousands grouping hardcoded to 3-digit, comma-only | locale / Stata format | n/a | LOW |
| K6 | `dash_render.py:4417` | `spec.sentinel \|\| '__all__'` | Sentinel fallback duplicated from `:4733`; correct, but the literal lives in two places | single constant | n/a | LOW |
| K7 | `dash_render.py:4566-4597` | histogram JS recompute reuses `ac.bin_edges` | Bins are **frozen at the unfiltered edges**. Correct for axis stability, but combined with A2 the y-axis stays raw counts and cannot become density | see A2 | n/a | MEDIUM |

### L. Widget builders (4649–4884) — `build_dropdown`, `build_slider`, `build_range`

**Checked and clean:** there are **no hardcoded pixel `width=`/`height=`** on `Select`,
`Slider` or `RangeSlider` in `4650-4884` (verified by grep over the range). Widgets inherit
Bokeh's sizing.

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| L1 | `dash_render.py:4809`, `:4862` | `vstep = (vmax - vmin)/100.0 or 1.0` | Step is always 1/100th of the range. For an integer variable (`rep78` 1–5) the step becomes `0.04`, letting the user select `2.36` on a variable that only takes integers; for a 0/1 dummy the step is `0.01` | integrality of the column (`np.allclose(arr, np.round(arr))` → step 1) and/or the Stata display format (J1) | no Stata analogue — **MEDIUM, must track the data** | MEDIUM |
| L2 | `dash_render.py:4807-4808`, `:4860-4861` | `vmax = vmin + 1.0` | Constant column → artificial +1 span | disable widget instead | n/a | LOW |
| L3 | `dash_render.py:4802-4803`, `:4855-4856` | `start=0, end=1, value=0, step=1` | Empty-column placeholder | n/a (disabled) | n/a | LOW |
| L4 | `dash_render.py:4798-4799` | `_raw_lbl + " ≥"` | Appends " ≥" to every slider title. Not overridable: if `label` already ends in ≥ it is skipped, otherwise forced. A user-supplied `label("Weight (lbs)")` becomes `"Weight (lbs) ≥"` | the `label` parameter alone, or a separate suffix option | partially — `label` is honoured for the stem only | MEDIUM |
| L5 | `dash_render.py:4733-4735` | `_sentinel = "__all__"` and its `"All"` display text | The "All" option label is hardcoded English, not derived from the variable's value-label set or any option | a `filter()` sub-option | no | LOW |
| L6 | `dash_render.py:4709` | `str(v) not in ("nan", "None")` | Missing-value detection by **string comparison** — a genuine string value `"None"` in the data is dropped from the dropdown | `pd.isna()` / `self.string_vars` | n/a (data property) | MEDIUM |
| L7 | `dash_render.py:4696-4705` | `_int_normalized` | Collapses `2.0` → `"2"`; a float variable whose values are whole numbers loses the distinction | display format (J1) | n/a | LOW |
| L8 | `dash_render.py:4741`, `:4797`, `:4853` | title falls back to `safe_var` | Falls back to the raw **variable name**, never to `self.variable_labels[varname]`, although those labels are loaded at `:5068` and propagated to the mapper at `:5043` | `variable_labels.get(varname, varname)` | Stata uses the variable label on axes by default | MEDIUM |

### M. `_sanitize_css_color` / `_validate_if_expr` (4260–4376)

| # | file:line | Literal | Currently does | Should derive from | Stata option? | Sev |
|---|---|---|---|---|---|---|
| M1 | `dash_render.py:4267` | `[a-zA-Z]{2,30}` | Accepts **any** 2–30 letter token as a "named color", including `inherit`, `initial`, `unset`, `revert`. Not exploitable on its own (no `;`/quotes can pass), but it means a typo'd colour silently renders as an inherited colour rather than falling back to `default` | the CSS named-colour list, or `OptionTranslator.translate_mcolor` (`:525`) which already maps Stata colour names | `color()`/`bgcolor()` on `dash kpi` are reachable | MEDIUM |
| M2 | `dash_render.py:4262` | `#[0-9a-fA-F]{3,8}` | Accepts 5- and 7-digit hex, which are invalid CSS and render as inherited | `{3}\|{4}\|{6}\|{8}` | n/a | LOW |
| M3 | `dash_render.py:4263-4264` | `\d{1,3}` per channel | Accepts `rgb(999,999,999)` | `0-255` | n/a | LOW |
| M4 | `dash_render.py:4313-4315` | `_IF_EXPR_SAFE_NAMES` | Omits Stata's missing-value literals `.`, `.a`–`.z` — an `if` expression using Stata missing syntax is rejected | Stata missing-value handling | `if` qualifier is reachable | MEDIUM |
| M5 | `dash_render.py:7293`, `:7296` | `"#212529"`, `"#f8f9fa"` | The two `_sanitize_css_color` **defaults** at the call sites are hardcoded greys, ignoring `scheme.title_color` (`:930`) and `scheme.background_color` (`:921`). (Call sites are outside 2600–5100 but are the only consumers of the in-range function.) | `SchemeParser` | `scheme()` reachable | MEDIUM |

---

## Severity counts

| Severity | Count |
|---|---|
| HIGH | 31 |
| MEDIUM | 32 |
| LOW | 18 |
| **Total** | **81** |

## UNREACHABLE-DEFAULT summary

Renderer code that reads an option `dash.ado` can never deliver — the user's command
**errors out** if they try to set it:

| Renderer read | Line | Blocked by |
|---|---|---|
| `options.get("bin", 10)` | `3001` | `dash.ado:293-326` syntax |
| `popts["range"]` | `5953` | `dash.ado:293-326` syntax + `:476-482` JSON whitelist |
| `popts["n"]` | `5960` | same |
| `graph_options["hover"]` | `4940` | `hover` absent from `dash.ado` entirely |

Options with **no renderer code at all**, so doubly unreachable: `kernel()`, `level()`,
`width()`, `start()`, `at()`, `bands()`, `percent`, `frequency`, `density`, `fraction`,
`discrete`, `mean`, `noweight`, `logit`, `adjust`, `tlabel()`, `ttitle()`.

Options that **are** reachable but are **silently ignored** by the mapper that should use
them (the worst category — no error, wrong output):

| Option | Reaches renderer | Ignored at |
|---|---|---|
| `bwidth()` | yes (`dash.ado:309`) | `map_kdensity` `:3033-3088`; `map_fpfit` `:2843`; `map_fpfitci` `:2898` |
| `degree()` | yes (`dash.ado:309`) | `map_fpfit` `:2843`; `map_fpfitci` `:2898` |
| `base()` | yes (`dash.ado:302`) | `map_dropline` `:3415` |
| `barwidth()` | yes (`dash.ado:302`) | `map_rbar` `:3161` |
| `msize()`/`msymbol()` | yes (`dash.ado:294`) | `map_dropline` dot `:3440`; `map_rcap` `:3246`; `map_rcapsym` `:3486`; `pcarrow` heads `:3785` |
| `scheme()` | yes (`dash.ado:319`) | every `line_width`/`fill_alpha`/marker-size literal — §H |
