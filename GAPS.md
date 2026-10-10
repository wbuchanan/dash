# GAPS.md — what `dash` promises versus what `dash` does

Source review of `dash.ado`, `dash_setup.ado`, `dash_parse.mata`, `dash_render.py`
and `schemes/*.scheme`, against `187a786`
(`feature/batch4-interactive-layer`, 62 commits ahead of `main`).

Reviewed 2026-09-21.

---

## Scope and method

"Intended capability" is taken from four sources, in this order of authority:

1. **`dash.sthlp`** — the promise made to the user. 1196 lines.
2. **The accepted option surface** — an option that `syntax` accepts is a
   promise the command will honour it. `dash.ado` declares 66 graph-level and
   137 plot-level options.
3. **Stata `twoway` parity** — `dash.sthlp:123,162` claims a copy-pasted
   `twoway` command runs unchanged.
4. **`CLAUDE.md`** — the project's own standing rules (testing, input
   hardening, resource limits, health checks, environment verification).

Findings are labelled by how they were established:

| Label | Meaning |
|---|---|
| **MEASURED** | Reproduced by executing Stata or the renderer and reading the result back. |
| **READ** | Established by reading the code; the behaviour is unambiguous. |
| **SUSPECTED** | Inferred; needs a runtime check before acting on it. |

Severity:

| | |
|---|---|
| **S1** | Produces silently wrong output, or breaks a documented feature outright. |
| **S2** | A documented or accepted capability does not work, but fails visibly or is reported. |
| **S3** | Fidelity, hygiene, coverage, or documentation drift. |

---

## Executive summary

The structure is built and the standalone renderer is broadly faithful. Eight
gaps stand between this tree and the product `dash.sthlp` describes:

1. **Every computed layer ignores its row filter.** `lfit`, `qfit`, `lowess`,
   `lpoly`, `kdensity`, `histogram`, `mband`, `mspline` and the four CI
   variants compute from the *whole* dataset regardless of a per-plot `if`,
   a linked `by()` facet, or a graph-level filter. The numbers are wrong and
   nothing warns. **S1.**
2. **The parser silently deletes plots and rewrites titles.** A `(` inside a
   quoted option value makes every later `||` segment vanish; the word
   `filter(` inside a quoted title is harvested as a real filter widget and
   cut out of the user's text. Both return `rc=0`. **S1.**
3. **A real `net install` makes all 14 schemes unreachable.** Stata fans the
   package into letter subdirectories; the renderer searches two directories,
   neither of which is one of them. Every installed user gets built-in
   fallback defaults whatever `scheme()` says. **S1.**
4. **`dash serve` aborts on every option it documents.** `dash serve,
   port(5006)` — the example in the help — returns `r(198) invalid 'port'`. **S1.**
5. **The generated server app is a separate hand-written renderer that has
   drifted.** 1 of 38 plot types delegates to the shared `GlyphMapper`; the
   rest are re-implemented. `pci` draws nothing, `fpfitci` loses its band,
   `pc*` types crash or vanish on a shared variable, `hover()` is ignored,
   per-plot and KPI qualifiers are not read, and `by()` silently drops 20
   plot types. The parity guard covers 17 of 38 types and none of these
   features. **S1/S2.**
6. **39 accepted options are inert**, plus a further set dropped with *no*
   report — `link()` and `filter()` at plot level, `saving()` on a named
   graph, and all four weight types. **S2.**
7. **Schemes are consumed only in part**, and the renderer draws a dark
   `#505050` minor grid on every figure that Stata never draws. **S2.**
8. **There is no image or data export** anywhere in the product. **S2.**

---

## A. Correctness — input silently discarded or rewritten

Two families of defect, both producing `rc=0` and plausible-looking output
from the wrong input: the computed layers ignore the rows they were given
(A1–A5), and the Mata parser discards or edits the command text before
anything downstream sees it (A6–A9).

### A1. Per-plot `if`/`in` is dropped before every statistical computation — S1, MEASURED, CLOSED by WP-02 (8efee0b)

`dash.ado` does its part: the qualifier is parsed, stripped and written into
each plot object as `if_expr` (`dash.ado:1098-1109`, emitted at `:1240`).
`DashRenderer` builds a correct `CDSView` from it (`dash_render.py:9979-9989`)
and passes it to the mapper as `view=`.

**Thirteen `map_*` methods accept `view=` and never reference it.** They read
the whole source instead — `map_lfit` at `dash_render.py:3845-3846`:

```python
x = np.array(source.data[xvar], dtype=float)
y = np.array(source.data[yvar], dtype=float)
```

Affected: `map_lfit` (3821), `map_qfit` (3873), `map_lfitci` (3918),
`map_qfitci` (3998), `map_lowess` (4091), `map_lpoly` (4272),
`map_lpolyci` (4344), `map_fpfit` (4517), `map_fpfitci` (4569),
`map_histogram` (4636), `map_kdensity` (4806), `map_mspline` (5912),
`map_mband` (5983). `map_area` (3592) has the same defect.

Measured on data where the subset answer is unmistakable (`y = x` for `g==0`,
`y ≈ 50 + 2x` for `g==1`):

| layer | rendered with `if_expr: "g==0"` | correct answer |
|---|---|---|
| `lfit` | 25.5 → 30.0 | **1.0 → 4.0** |
| `qfit` | 25.5 → 30.0 | **1.0 → 4.0** |

25.5 → 30.0 is the *full-data* fit. The qualifier changed nothing, and no
warning was emitted.

So `dash (scatter mpg weight) (lfit mpg weight if foreign==1)` draws the
all-cars regression line labelled as the foreign-cars one.

**Closed by 8efee0b (WP-02)**, with 9179359 and 7c6a2fe for the mappers
that attached a mask sized to the original source to one they had rebuilt,
or took a derived width from every row.  The fourteen mappers (the thirteen
above and `map_area`) mask their input arrays before computing
(`GlyphMapper._view_mask`, `_masked`).  Measured 23sep2026 at `4ede074`,
with the console binary on `sysuse auto`: `dash (scatter mpg weight) (lfit
mpg weight if foreign==1)` draws a 100-point line over weights 1760 to 3420
whose slope and intercept are -0.0104259575877988 and 48.9182972317432,
exactly what `regress mpg weight if foreign==1` reports.  Tests:
`test/test_computed_layer_rows.py` (every one of the fourteen, qualified
equals the same mapper on the pre-filtered rows) and
`test/test_view_alignment.py`.  ROADMAP.md does not yet head WP-02 DONE;
its planned `test_qualified_layers.cscript` was never written.

### A2. The same defect makes linked `by()` facets identical — S1, MEASURED, CLOSED by WP-02 (8efee0b)

`_linked_graph_views` builds a per-panel `BooleanFilter`/`CDSView`
(`dash_render.py:11466-11480`) which the computed mappers then discard.
`histogram mpg, by(foreign) link(_all)` produces byte-identical bars in both
panels (`tops=[0.075, 0.0563, 0.0562]`). Unlinked `by()` is correct, because
`:11455` builds a genuinely separate source per facet — so the same command
gives different answers depending on whether `link()` is present.

**Closed by 8efee0b (WP-02)**, the same change as A1: the linked panels'
views reach the computation, and linked and unlinked `by()` give the same
numbers (`test/test_computed_layer_rows.py::TestLinkedFacetsComputeSeparately`,
passing at `4ede074`).

### A3. Weights are parsed and silently discarded — S2, CLOSED by WP-13 (reported) and WP-18 (honoured)

`_dash_parse_varpart_*` declares `[aweight fweight pweight iweight]`
(`dash.ado:781, 795, 809, 823`) and stores the type in `s(_weight)`
(`:784, 798, 812, 826`). Nothing ever reads it, and `sreturn clear` at
`dash.ado:1112` destroys it before the option parse. The weight *expression*
is discarded outright. There is no weight handling anywhere in
`dash_render.py`.

The code comment at `dash.ado:782-783` claims "it is reported as ignored".
It is not. Measured: `dash scatter mpg weight [aw=price], name(w1)` → `rc=0`,
"graph 'w1' registered", **no note**. Stata's `lfit`, `qfit`, `lowess`,
`lpoly`, `fpfit`, `histogram` and `kdensity` all honour weights.

**Closed by WP-13.** The weight TYPE is carried across the `sreturn clear`
and appended to the segment's ignored list, so the note reads
`dash: ignoring unsupported option(s): [aweight]` -- by type, never by
variable, once per distinct type per command. The weight is still not
applied (WP-18). Certified by `test_option_surface.cscript` AC-13.1a-c.

**Finished by WP-18**, 23sep2026, measured first at `fe3b12a`. The premise
above -- that `lowess` honours weights -- was false: `twoway lowess` and
`lowess` return r(101) `weights not allowed` for every type
(`lowess.ado:9`, `twoway_lowess_parse.class:35`). The rest of the grid,
18 commands by 4 types on auto (`weight_acceptance`, 72 probes;
`weight_acceptance_table`): `iweight` is r(101) on every twoway statistical
type; `histogram` takes `fweight` only (aw/pw r(101)); `kdensity`, `lpoly`
and `lpolyci` refuse `pweight`; `lfit`, `qfit`, `lfitci`, `qfitci`,
`fpfit`, `fpfitci`, `mspline` and `mband` take aw, fw and pw, the last two
inertly. dash carried the type across the clear and nothing else: the
expression was dropped in the parsers, the variable never exported, the
plot JSON weightless, and `[iw=price]` on scatter or `[pw=price]` on
histogram was rc 0 with the note where twoway is r(101). Now
`_dash_process_segment` refuses exactly what twoway refuses, with its rc
and its words, requires the expression to be one existing variable
(abbreviations expanded; `[aw=price+1]` is r(198) with a `generate` hint,
since dash cannot evaluate an expression before the data leave Stata,
and a range such as `price-price` that `unab` would read as one variable
is refused the same way), checks an `fweight` where twoway checks it (a
non-integer one r(401) on lfit, lfitci, lpoly, lpolyci, histogram and
kdensity, a negative one r(402) on the last four), and splices
`"weight":"<type>","wexp":"<var>"` into the plot's options only when a
weight is present, so the unweighted JSON stays byte for byte what
`test_varlist_expansion.cscript` and `test_pipeline_integration.py` pin;
`_dash_extract_vars` exports the variable on both routes;
`_DASH_OPT_VAR_KEYS` carries it into either mode's source, and the twelve
layers read it with each type's own semantics (aweights normalised to sum
N with df_r = N - 2, fweights replicated with N = sum w, pweights the
aweight estimates with an HC1 band). The WP-13 note stays on the glyph
layers. Truth: `weighted` (55 probes over auto `[aw=price]` and
`[fw=int(price/1000)]`, census `[aw=pop]`, sp500 `[aw=volume]`, nlsw88
`[aw=hours]`), `weighted_data`, `weighted_fit_check` (15 of 15 weighted
lfit/qfit/lfitci sersets equal the weighted `regress`), pinned by
`test_statistical_truth.py::TestWeightedLayers`; the refusals and the
JSON by `test_statistical_options.cscript`. The verification tally is
ROADMAP.md WP-18's.

### A4. Estimator divergences from Stata — S2, CLOSED by WP-18

- **`mspline` is a different estimator.** Stata fits a cubic spline through
  the cross-medians of `bands()` bands. `dash_render.py:5953-5972`
  PCHIP-interpolates through *every* observation after averaging duplicate x.
  No band computation exists in the function, and `bands()` and `n()` are both
  ignored — the grid is hardcoded to 200 points at `:5973`.
- **`fpfit` never fits a repeated-power FP2.** `_fit_fp2` (`:4483`) iterates
  `combinations_with_replacement`, which yields `(p, p)` pairs, but
  `_fp_transform` (`:4452-4459`) has no repeated-power branch. Royston–Altman
  requires `β₁·xᵖ + β₂·xᵖ·ln x` when `p₁ == p₂`; instead `z1 == z2`, the design
  matrix is singular, and the model collapses to FP1. About a third of Stata's
  FP2 candidates are unreachable.
- **`fpfit` applies no origin shift.** `:4456-4458` maps `x <= 0` to NaN and
  drops those rows. Stata's `fp`/`fracpoly` shifts x so all values are
  positive.

**Closed by WP-18.** Measured first, 23sep2026 at `fe3b12a`, against the
sersets of the saved `.gph` files (the regenerated
`test/fixtures/stat_truth.json`, 52 sections, the 25 pre-existing ones
byte-identical), with dash's mappers called as `test_statistical_truth.py`
calls them and every error a fraction of the raw y range:

| layer | at `fe3b12a` | Stata's rule | after |
|---|---|---|---|
| `mspline` | PCHIP through every distinct-x/mean-y point, 200-point grid, `bands()`/`n()` unread (`dash_render.py:6985-7057`) | cross medians of B equal-width bands (K non-empty; B default `round(min(10 log10 N, sqrt N))`, `_gs_default_bands.ado:5-17`), a cubic spline through the K knots at (K-1)n + K points, n default 10; the spline is serset 2 of the `.gph` | 14.0 mpg max error on auto default (y range 29), 9.2 at bands(8), 5.3 at bands(4); a natural cubic spline through the knots reproduces all 20 probes to 9.65e-6 abs (float32 sersets); not-a-knot 2.76, clamped 1.62, PCHIP-through-knots 0.96, Akima 1.02 rejected |
| `fpfit`, repeated powers | `(p, p)` built as `[1, z, z]`, rank 2 of 3, never wins (`:5357-5408`) | `x^p` and `x^p ln x` (`ln^2 x` at p = 0), `fracgen.ado:193-212`; 36 pairs by deviance | `fracpoly` picks (-2,-2) on auto price~mpg and mpg~weight, (2,2) on nlsw88 wage~ttl_exp and on the synthetic sample; dash chose (-2,-1) (9.0e-3) and (1,3) (2.7e-2); with the design, 1.5e-7 on all four |
| `fpfit`, shift and scale | x <= 0 dropped, no scaling, grid capped at 1000 (`:5361-5363`, `_FP_GRID_MAX`) | shift by (smallest positive spacing) - min(x) when min(x) <= 0, then ALWAYS divide by `10^(sign(log10 s) int(abs(log10 s)))`, s the range (`frac_xo.ado:81-106`); predict at every distinct x | census death~pop: cond 3.6e21 unscaled, dash (0,.5) vs Stata (1,3), 3.9e-2; `xs = weight - 3000` (35 non-positive): e(fp_shft) 1250, e(fp_sfac) 1000, powers (0,0), rc 0 in twoway, 35 rows dash would drop; `xz = mpg - 12` (min 0): shift 1, scale 10, (-2,-2); nlsw88 1546 distinct x against a 1000-point linspace |
| `fpfitci` | bootstrap percentile band, 200 resamples, seed 42 (`:5531-5535`) | `fracpred, stdp` times `invttail(N - 3, (100 - level)/200)` (`twoway__fpfit_serset.ado:31-50`) | band off by 1.1e-1 (auto), 2.3e-1 (census), 1.17 (sp500, past the y range at the first sample), 1.1e-1 (nlsw88); width ratio 0.67 to 4.72; analytic stdp reproduces auto to 6.3e-8 |
| `lowess` | statsmodels `lowess(frac=bw)`: nearest-by-distance window, 3 robustness iterations, tied x identical (`:5041`) | [R] lowess: stable sort, index window k = int((N bw - .5)/2), tricube on d/(1.0001 max d), local line, no iterations; ties in dataset order | 1.08e-1 (auto, 3.13 mpg), 1.19e-1 (census), 1.92e-1 (sp500), 3.67e-2 (nlsw88); the rule reproduces all 20 probes to 1.5e-10 abs |
| `lpoly` degree >= 1 | `np.polyfit(w=K)`, which squares the weight (`:5167`) | weighted least squares, w = sqrt(K) | 2.8e-2 (auto), 2.9e-2 (sp500), 3.5e-2 (nlsw88) at Stata's own bandwidth; 1.3e-15 with sqrt(K) |
| `lpoly` null rule and grid | a point drawn with one positive-weight observation; 200-point grid, `n()` unread | missing when fewer than 2 observations have positive weight; `n()` points, default 50 capped at the dataset's _N (_N when the dataset has fewer than 50 rows) | dash finite at 5 of 11 samples where Stata is null (auto bwidth(5)); as drawn 1.58e-2 (auto default), 5.5e-2 (degree(1)) |
| `kdensity` | grid [min - 3h, max + 3h] x 300 (`:5781`) | twoway: [min, max] x n(), default 300 | estimator exact (2.7e-12) but as drawn 1.0 on census bwidth(2): grid step 617 against a kernel support of 4.5 |
| `lfitci`, `qfitci`, `mband` | stdp band; equal-width cross medians | the same | exact: 2.7e-7, 2.8e-7, 1.5e-7 -- locked before anything was touched |

The `lpoly` weighting, null rule and grid, the `fpfitci` band and the
`kdensity` grid were not in this finding's text; they are in `BUGS.md`,
one entry each, with the fixture sections that pin them (`mspline`,
`mspline_knots`, `fpfit_repeated`, `fpfit_repeated_data`, `fpfit_shift`,
`fpfit_shift_curve`, `lowess_more`, `lpoly`, `lpoly_twoway`, `kdensity_twoway`,
`rules_wp18`). What stays as it was: the `lpoly` rule-of-thumb bandwidth
(`_LPOLY_ROT_C`), which lives in compiled Mata and agrees with `r(bwidth)`
to -9.7% (auto), +14.2% (census), +5.7% (sp500), +6.8% (nlsw88), the help
now saying so in those numbers; `lpolyci`'s bootstrap band (recorded as a
follow-up in ROADMAP WP-18); and the cubic spline's end condition, which
is inside the builtin `serset create_cspline` and is pinned by the recorded
curves rather than by any `.ado`. Tests, written before the renderer
changed: `test_statistical_truth.py::TestMsplineAgainstStata`,
`TestFpfitRepeatedPowers`, `TestFpfitShift`, `TestLowessIsStatasSmoother`,
`TestLpolyDegreeOne`, `TestLpolyNullRule`, `TestKdensityAsDrawn`; the
parity corpus carries `mspline bands(5) n(4)`. The verification tally is
ROADMAP.md WP-18's.

**Since WP-29 (P0.7, commit 758cf59; P0.9, commit e32be3a).** The `lpoly` and `lpolyci` default bandwidth is Stata's rule of thumb per kernel and degree, as `lpoly` computes it, and no longer the WP-18 approximation quoted above; `lpolyci` draws Stata's analytic band with `pwidth()` and `var()`, and the bootstrap band is gone. The sentence above that both stay as they were no longer holds.

### A5. Statistical sub-options with no implementation — S3, CLOSED by WP-18

Zero occurrences in `dash_render.py`: `histogram, discrete`;
`lfitci`/`qfitci` `stdf`/`stdp`/`stdr` (only one band type is ever drawn);
`lowess` `mean`, `noweight`, `logit`, `adjust`.

**What is honoured** (verified): `lfit`/`qfit`/`fpfit` `n()`; `lowess`
`bwidth()`; `lpoly` `bwidth()`/`degree()`/`kernel()`; `histogram`
`start()`/`width()`/`bin()`/`frequency`/`percent`/`fraction`/`density`;
`kdensity` `kernel()`/`bwidth()`/`n()`; `mband` `bands()`; `level()` with
session `c(level)` inheritance and a proper t quantile (`_t_ppf`, `:6373`).
`fpfit` correctly *rejects* `bwidth()`/`degree()` the way Stata does
(`_fp_report_unsupported`, `:6474-6490`).

**Closed by WP-18.** Measured first, 23sep2026 at `fe3b12a`: none of the
seven was declared in `dash.ado`'s plot syntax block (`:757-816`), so each
fell through the trailing `*` into the unknown-option note -- `dash lfitci
mpg weight, stdf name(w7)` rc 0 with `stdf()` named, `dash lowess mpg
weight, mean noweight logit adjust name(w8)` rc 0 with all four named,
`dash histogram rep78, discrete name(w9)` rc 0 with `discrete()` named,
every one registered with `"options":{}` and drawn as the default. What
they draw in Stata, now in the fixture: `fitci_std` (24 probes, 4
datasets by lfitci/qfitci by stdp/stdf/stdr; on auto lfitci at x = 1760
stdp [27.34, 30.39] around 28.865, stdf [21.84, 35.89], stdr [22.18,
35.55]; stdf = sqrt(stdp^2 + rmse^2), stdr = sqrt(rmse^2 - stdp^2), the
same t; `fitci_std_rebuild` agrees on all 12, and stdp equals the level-95
`ci_bands` on all 8), `histogram_discrete` (12; auto rep78: 5 bins of width
1 from .5, densities .02899 .11594 .43478 .26087 .15942; auto mpg: 30 bins
of width 1, 21 occupied; width(2) 15 bins; `discrete bin(3)` r(198)) with
`histogram_discrete_twoway` (9, the drawn serset equals the generator),
and the logit/adjust keys of `lowess_more` (adjust = smooth x
mean(y)/mean(smooth), `lowess.ado:203-209`; logit clamps to 1/N and 1 - 1/N
under the .0001 rule then ln(s/(1 - s)), `:213-221`, adjust before logit).
twoway declares them `DISCrete`, `STDP STDF STDR` (no abbreviation; two of
them `may not combine`, r(198)) and `Mean noWeight Adjust LOgit`, and
refuses each outside its type (`option discrete not allowed`, r(198)).
Now `dash.ado` declares the seven as twoway does, carries each as a flag
in the plot JSON, refuses it outside its type through a flag-applicability
list in `_dash_option_rules`, refuses two of stdp/stdf/stdr together and
`discrete` with `bin()`; the renderer honours them in both modes, and
`dash.sthlp` documents them beside the layers that take them. Pinned by
`test_statistical_truth.py::TestFitciBandTypes`, `TestHistogramDiscrete`
and `TestLowessIsStatasSmoother`, `test_unsupported_report_is_true.py`
(each flag present against absent; stdp against its stdf sibling, since
stdp names the default), the parity corpus (`lfitci stdf`, `qfitci stdr`,
`histogram discrete`, `lowess mean`, `lowess noweight logit adjust`) and
`test_statistical_options.cscript`. The verification tally is ROADMAP.md
WP-18's.

### A6. A paren inside a quoted option value deletes every later `||` segment — S1, MEASURED, CLOSED by WP-01 (9c7dbf7)

`_dash_split_segs` gates its double-quote and compound-quote checks on
`depth == 0` (`dash_parse.mata:468, 473`). Paren mode (`:410, 415`) has **no
such gate**. So in flat (`||`) mode, any `(` inside a quoted option value
permanently unbalances `depth`, and every subsequent `||` stops being a
separator. `_first_comma_pos` carries the identical defect at `:303, 308`.

Measured, with and without the paren:

```
. dash scatter mpg weight, title("a b")   name(ctl) || line mpg weight
dash: graph 'ctl' registered.

. dash scatter mpg weight, title("a ( b") name(bad) || line mpg weight
dash: ignoring unsupported option(s): |() line() mpg() weight()
dash: graph 'bad' registered.
```

The `line` plot is **silently deleted**, the user is handed a nonsense
diagnostic naming four options that do not exist, and `rc=0`. Real `twoway`
accepts the identical line and draws both plots.

The same shape appears with `legend(label(1 "a ( b"))` — the sort of value a
user writes without thinking about it.

**Fix:** drop `& depth == 0` at `dash_parse.mata:468, 473, 303, 308` so flat
mode matches paren mode.

**Closed by 9c7dbf7 (WP-01).** Every scanner in `dash_parse.mata` now steps
through quotes with one shared `_dash_quote_step`, so a quoted value is
opaque at any paren depth.  Measured 23sep2026 at `4ede074` with the console
binary: `dash scatter mpg weight, title("a ( b") name(g) || line mpg weight`
registers one graph whose JSON holds both the scatter and the line, and
prints no "ignoring unsupported option(s)" note.  Certified by
`test/test_parser_integrity.cscript` P1B-01 to P1B-12 (re-run at `4ede074`:
passed).  ROADMAP.md does not yet head WP-01 DONE.

### A7. `filter(` inside a quoted title becomes a real filter and is cut from the text — S1, MEASURED, CLOSED by WP-01 (9c7dbf7)

`_dash_extract_filters` (`dash_parse.mata:752-828`) scans the raw `0` for
`filt|filte|filter` with only a preceding-character word-boundary test
(`:787`). It never tracks quotes, and it lower-cases the text first, so the
match is case-insensitive too.

Measured end to end:

```
. dash scatter mpg weight, name(g1)
. dash build, title("Q1 filter(foreign) report") saving("b2.html") replace nobrowser
dash: dashboard saved to b2.html
```

`rc=0`, no warning — and the rendered dashboard title is **`Q1 report`**.
`foreign` became a live filter widget the user never asked for, and their
title was silently edited. `note("see FILTER(abc) here")` behaves the same
way.

This fires on `dash build` and `dash serve` (`dash.ado:2368, 2536`);
`_dash_plot` does not call it. No test covers it.

**Closed by 9c7dbf7 (WP-01).** `_dash_extract_filters` skips a match inside
a quote and matches only at paren depth 0.  Measured 23sep2026 at `4ede074`:
`dash build, title("Q1 filter(foreign) report")` writes a page whose title
is `Q1 filter(foreign) report` and which holds no Select or RangeSlider
widget.  Certified by `test/test_parser_integrity.cscript` P1B-19 to P1B-22
(passed at `4ede074`).

### A8. The splitter accepts malformed input that `twoway` rejects — S2, MEASURED, CLOSED by WP-01 (9c7dbf7)

Paren mode `break`s at the first top-level comma (`dash_parse.mata:439`), so
anything after it is treated as graph options regardless of shape:

| Input | `twoway` | `dash` | dash behaviour |
|---|---|---|---|
| `(a) junk (b)` | `r(198)` | `rc=0` | `junk` silently discarded |
| `(a)) (b)` | `r(198)` | `rc=0` | the extra `)` silently ignored |
| `(a), (b)` | `r(198)` | `rc=0` | `(b)` swallowed into the graph-option string |

There is also **no balance check at end of scan** — `depth != 0` or
`in_dq != 0` on exit should be an error but is not. So an unclosed `(` or an
unterminated `"` yields one segment and no message:

- `scatter y x, legend(off || line y2 x` → 1 segment, silent
- `scatter y x, title("oops || line y2 x` → 1 segment, silent

Empty groups `()` are dropped silently at `:428`.

`test/test_tokenizer.cscript` passes 20/20 with all of the above live. No test
constructs a quote containing a paren.

**Closed by 9c7dbf7 (WP-01).** Both modes check quote and paren state at
the end of the scan, and paren mode refuses an unmatched `)`, stray text
between groups and a group after the graph-option comma.  Measured
23sep2026 at `4ede074`, each against `twoway` in the same run:
`(scatter mpg weight) junk (line price weight)`, `(scatter mpg weight))
(line mpg weight)` and `(scatter mpg weight), (line mpg weight)` are r(198)
in both; `scatter mpg weight, legend(off || line price weight` is r(198)
"unbalanced parentheses in the plot specification", and an unterminated
quote r(198).  An empty group `()` is dropped by both (`twoway () (scatter
mpg weight)` rc 0; dash rc 0 with one plot), so that line is not a gap.
Certified by `test/test_parser_integrity.cscript` P1B-13 to P1B-18 and
`test/test_tokenizer.cscript` (both passed at `4ede074`).

### A9. The UTF-8 gate passes the encodings it exists to stop — S2, MEASURED, CLOSED by WP-08

**RESOLVED (WP-08).** Every sequence in the table below was measured to be
accepted by the old validator, and every one is now rejected. The rewrite
applies RFC 3629 s.4's per-lead second-byte ranges and was verified against
Python's own decoder over 41,976 sequences with zero mismatches; 2,245 are
committed as `test/fixtures/utf8_cases.txt`. C0 control bytes remain accepted
here on purpose — they are well-formed UTF-8, and it is `_dash_json_str`'s
job to escape them. See the BUGS.md entries.

`_is_utf8` (`dash_parse.mata:90-109`) checks only the **lead-byte range** and
that continuation bytes are `0x80-0xBF`. It never constrains the second byte
per lead byte, which RFC 3629 requires:

| Input | `_is_utf8` | should be |
|---|---|---|
| overlong `E0 80 AF` | **passes** | reject |
| overlong `E0 9F BF` | **passes** | reject |
| UTF-16 surrogate `ED A0 80` | **passes** | reject |
| surrogate `ED B0 80` | **passes** | reject |
| overlong `F0 80 80 80` | **passes** | reject |
| above U+10FFFF `F4 90 80 80` | **passes** | reject |
| NUL, ESC, BEL, DEL | **passes** | policy |

Correctly rejected: `C0 80`, `C1 BF`, a bare continuation byte, 5-byte `F8`,
truncated `C3`.

The validator exists to give a clean `r(198)` before bad bytes reach the
backend. It does the opposite — measured:

- `title("x" + char(237)+char(160)+char(128) + "y")` →
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xed`, **`r(7102)`**,
  raw Python traceback.
- `title("bad" + char(1) + "title")` →
  `json.decoder.JSONDecodeError: Invalid control character`, **`r(7102)`** —
  because `_dash_json_str` leaves C0 control bytes raw (see E6).

This is not code injection; no user text reaches Python as code. It is an
availability and diagnostics defect against CLAUDE.md rules 14 and 16, at the
rule's own designated enforcement point.

Related: `_dash_option_names` (`dash_parse.mata:945`) toggles its in-quote
flag on every `"` with no compound-quote handling, so an odd quote count
drops trailing options — measured, `title("unbalanced quote) xlabel(1)`
reports only `title`.

That related defect was fixed by 9c7dbf7 (WP-01): an unbalanced quote no
longer drops trailing option names (`test/test_parser_integrity.cscript`
P1B-23 to P1B-25).  The gate itself: `test/test_utf8_validation.cscript`
UTF-01 to UTF-12, re-run 23sep2026 at `4ede074`: passed.

---

## B. Packaging — `net install` makes every scheme unreachable

### B1. The scheme search path does not survive installation — S1, MEASURED, CLOSED by WP-05

`dash_render.py:1524-1532` searches exactly two directories, both derived
from `__file__`:

```python
_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")
_SCHEME_SEARCH_DIRS = (_SCHEMES_DIR, os.path.dirname(os.path.abspath(__file__)))
```

A real `net install` from this repo's `stata.toc` + `dash.pkg` into a sandbox
PLUS produces:

```
plus/d/dash.ado   plus/d/dash.sthlp   plus/d/dash_parse.mata
plus/d/dash_setup.ado                 plus/d/dash_setup.sthlp
plus/py/dash_render.py                 <- .py routed to py/, not d/
plus/e/economist.scheme                <- letter subdirectory, flattened
plus/s/s1color.scheme … plus/s/stsj.scheme   (13 files)
```

So the search path evaluates to `plus/py/schemes` (does not exist) and
`plus/py` (holds only `dash_render.py`). Measured against the installed copy:

```
resolve_or_fallback('stcolor') -> name='s2color', is_fallback=True
UserWarning: dash: scheme 'stcolor' was not found …
UserWarning: dash: no scheme file could be resolved … Falling back to built-in defaults.
```

The build returns `rc=0` and writes a file, so nothing fails loudly. **Every
installed user gets `_FALLBACK_PROPS` (`:1552-1569`) whatever `scheme()`,
`theme()` or `c(scheme)` says, and all 14 schemes collapse to one look** —
one that is not even s2color. Measured deltas: `grid_line_width` 0.8 vs 1.5;
`bar_alpha`/`area_alpha` 0.8 vs 1.0; text 10pt vs 11pt; heading 13pt vs 14pt;
`graphsize` absent; **no horizontal grid at all**; and no `symbol p#` or
`linepattern` keys, so every mono scheme loses its whole symbol and dash
cycle (`p_symbols` measures all-`circle`).

The comment above those lines anticipates *one* flattening
(`<install dir>/x.scheme`); Stata uses a third layout it does not cover.

`findfile s2color.scheme` **does** locate the installed file (`plus/s/…`,
rc=0). `dash.ado` never looks, and never tells Python where to look.

**RESOLVED (WP-05).** `SchemeParser` now has a `_PLUS_ROOT` guarded on the
package directory being named `py`, and an `_installed_letter_dir(name)` that
returns a directory only for one of the fourteen literal `_BUILTIN_NAMES`.
The lookup is an isolated block *after* the candidate loop and does not extend
`allowed`: doing so would also authorise the caller-controlled CWD candidate,
letting a symlink named `s2color.scheme` reach any file in `PLUS/s`. That
over-broad variant was built and measured — 25 files reachable under the test
PLUS, the whole subtree once CWD was inside it, and the entire home tree when
`dash_render.py` was not under `py/`. Verified end to end against a real
install: `scheme(s1color)` now emits zero warnings and the HTML no longer
carries s2color's `#eaf2f3`. The `_FALLBACK_PROPS` deltas this section
measured are fixed too — it now carries s2color's grid, graphsize, gsize,
linewidth, symbolsize and intensity values, held there by
`test_scheme_fallback_provenance.py`. Tests: `test/test_installed_layout.py`
(INST-01..16).

### B2. The hardcoded fallback renderer path points at the wrong directory — S3, READ, CLOSED by WP-05

`dash.ado:1747`, `:2480`, `:2621` all fall back to
`` `c(sysdir_plus)'d/dash_render.py ``. The installer puts it in `py/`. Masked
today because `findfile` succeeds first.

**RESOLVED (WP-05), with a correction.** Measured: `findfile dash_render.py`
does succeed on an installed tree — it searches the *extension* subdirectory,
returning `PLUS/py/dash_render.py` — so neither fallback was ever reached by a
real user and this was never a live failure. What made it worth removing is
that nothing confirmed the file existed before the path reached
`runpy.run_path`, so when a branch *was* reached the user got a Python
`FileNotFoundError` naming a Stata internal directory, `r(7102)`, and no
message from dash; `dash serve` announced the server first and died after. All
three copies are replaced by one `_dash_find_render` holding only the two
candidates that can succeed, exiting 601 with a dash-authored message
otherwise. Tests: `test/test_render_locate.cscript` (LOC-01..09).

### B3. Schemes install under names Stata cannot see, and may collide — S3, READ, CLOSED by WP-05 (a documented limitation)

They install as bare `s2color.scheme`, not `scheme-s2color.scheme`, so they
are invisible to Stata's own `set scheme`. `plus/s/sj.scheme` and friends also
sit in the shared PLUS letter directories, where they can collide with other
packages.

**CORRECTED, then CLOSED as a documented limitation (WP-05).** "Invisible" is
the wrong word, and the mechanism matters. Stata's own
`/Applications/StataNow/ado/base/s/scheme.class:171-173` reads:

```
capture findfile scheme-`scheme'.scheme
if (_rc) capture findfile `scheme'.scheme
```

so a bare `<name>.scheme` is *second in line*, not unseen. dash's files are
shadowed rather than invisible, and shadowed by StataCorp's own copy for all
fourteen names, so `set scheme s2color` is unaffected — measured, rc 0 with
StataCorp's background colour.

The collision with other packages is real but was measured to be inert for
dash: `net install` refuses a duplicated basename with `rc 602` and
`, replace` overwrites it, which is generic packaging behaviour for any
duplicated name rather than anything specific to schemes. Renaming to
`dash_<name>.scheme` would end it, but `scheme(<file>.scheme)` is a supported
way to name a file, so the names are kept and the limitation is now stated in
`dash.sthlp` rather than left implicit.

### B4. `dash.pkg` cannot be updated by `adoupdate`, and states the wrong version — S3, READ, CLOSED by WP-05; release verification CLOSED by WP-27

The manifest carries its version only as prose (`dash.pkg:25`,
`d Version: 1.0.0 25mar2026`). There is no `v` line and no
`d Distribution-Date:` line, so `adoupdate` can never detect an update.

It is also **out of step with the code**: `dash.ado` and `dash_parse.mata`
both declare `v2.0 27mar2026`. An installed package reports 1.0.0.

**RESOLVED (WP-05), with a correction.** The joint attribution above is wrong.
`v` is the manifest's **file-format** version — the same field `stata.toc`
sets to 3, maximum 3, with `v 4` being `r(610)` — not the package's version,
and `net install` does not copy it into `stata.trk`, so it cannot take part in
an update comparison at all. Only `d Distribution-Date:` can. `dash.pkg` now
leads with `v 3` (StataCorp conformance, not the fix) and carries
`d Version: 2.0  27mar2026` and `d Distribution-Date: 20260327`;
`dash_setup.ado`, `dash.sthlp` and `dash_setup.sthlp` were moved to the same
version so all six agree. Tests: `test/test_pkg_metadata.py` (PKG-01..08),
which asserts the date and the format version **separately** so the two
reasons cannot be conflated again.

All 20 declared files exist and nothing shippable is missing; `stata.toc` is
correct and minimal.

---

## C. `dash serve` — every documented option aborts the command


**Verified at release by WP-27** (24sep2026): `make gate` net installs
dash from a copy of exactly what `dash.pkg` ships; against that source
`adoupdate dash` reports nothing to update, and against a copy one day newer
it reports dash (`r(pkglist)`), so an installed dash sees a release.
`dash.pkg` carries `d Distribution-Date: 20260924` and every shipped file's
version line reads 2.0 24sep2026 (test/test_pkg_metadata.py).

### C1. The option string is forwarded with its leading comma — S1, CLOSED by WP-03 and WP-23 (fixed by 81ebbc5, broken again by 7ddbc08, fixed again by WP-23)

`_dash_serve` forwards `` `0' `` verbatim at `dash.ado:2601`:

```stata
_dash_serve_spec, specpath("`master_json_path'") datapath("`data_json_path'") `0'
```

`` `0' `` still carries the leading comma, so the call becomes
`…datapath("…") , port(5006)` — two commas on one line, and everything after
the second is read as a positional argument. This is the exact defect
`_dash_build` fixes with `: subinstr local _fwd_opts "," ""` at `dash.ado:2440`
and documents at `:2434-2439`. It was never applied here.

Measured:

```
. dash scatter mpg weight, name(g1)
dash: graph 'g1' registered.
. dash serve, port(5099) timeout(1) nobrowser
invalid 'port'
r(198);
. dash serve
dash serve: starting Bokeh Server on port 5006.
```

So `port()`, `timeout()`, `nobrowser` and every inherited build option are
unreachable. Only the bare form runs. `dash serve, port(5006)` is the
documented example at `dash.sthlp`.

`_dash_serve_spec` itself is correct and complete — it validates the port
range, the timeout, and inherits the build options. The defect is one line
above it.

**Fixed by 81ebbc5 (WP-03), then broken again by 7ddbc08, so still open.**
81ebbc5 strips the comma, and `test/test_serve_launch.cscript` SRV-01 to
SRV-16 drive `dash serve` itself through option parsing (passed at
`4ede074`).  But measured 23sep2026 at `4ede074` with the console binary
(`sysuse auto`, one registered scatter, a `dash build` with a filter first):
`dash serve, port(5487) timeout(1) nobrowser` prints "starting Bokeh Server
on port 5487" and then a Python traceback ending `ValueError: dash_render:
--output must end in .py for mode 'server'`, r(7102), and nothing listens on
the port.  `_dash_serve` hands the renderer an extension-less `tempfile`
path on purpose, and 7ddbc08 (WP-08's TR-08.8) made `main()` refuse any
server-mode output not ending in `.py`, so every launch aborts, the bare
form included.  The documented example fails again, for a new reason;
recorded in BUGS.md ("`dash serve` aborts with r(7102) on every launch").

**Closed by WP-23.**  On the `--launch` route the renderer now accepts a
`.py` name or a name no file holds yet, so `_dash_serve`'s extension-less
tempfile is taken while no existing file that is not a `.py` can be
overwritten; `dash build, server` still needs `.py`, and the other path
checks hold on every route.  Measured on the WP-23 tree: `dash serve,
timeout(1)` answers `/health` with 200 while it blocks, returns rc 0 after
61 s and leaves no copy of the app; Ctrl+C stops it in under a second
(test/test_help_claims_4.cscript HC4-19 to HC4-21, test/test_help_claims_4.py
`TestTheOutputPathRule` and `TestTheRealHandoffServes`).

### C2. Nothing could catch it — S2, CLOSED by WP-03 and WP-23 (the command run by 81ebbc5's test_serve_launch.cscript, the real launch by WP-23)

`test_serve_options.cscript` deliberately calls `_dash_serve_spec` *directly*
(`:55, 99, 113, 137-146`), bypassing the only line where the defect lives.
Its own header at `:28` says it covers "everything `dash serve` does except
the launch". All five of its PASS banners are labelled "dash serve …" and none
of them runs `dash serve`. The other five Stata-level `dash serve`
invocations in the suite are all `capture` + `assert _rc == 198` error-path
tests. **The happy path has zero coverage.**

**Still open, measured 23sep2026 at `4ede074`.** `test_serve_launch.cscript`
(81ebbc5) now runs `dash serve` as a command, which is what would have
caught C1, but it stops at the empty-registry check so as not to hold the
suite for the sixty seconds a launch costs; `test_serve_browser.cscript`
launches a stub renderer; `test_server_serves.py` runs the generated app,
not the command.  No test runs the real launch, and the regression now
recorded under C1 went unnoticed for exactly that reason.

**Closed by WP-23.**  test/test_help_claims_4.cscript HC4-19 to HC4-21 run
the real `dash serve, timeout(1)` in the certification suite -- a server
that must answer `/health` while Stata blocks, the command's return code
after the timeout, and no app file left behind -- at the cost of the
minute a launch takes; test/test_help_claims_4.py `TestTheRealHandoffServes`
runs the renderer exactly as `_dash_serve` does and stops it with SIGINT.

### C3. An unexplained diagnostic on the bare form — S3, MEASURED, CLOSED by WP-03 (81ebbc5)

Bare `dash serve` prints `(file /var/…/S_26952.000002 not found)` before
starting the server, and starts it anyway. The same message appears on a
plain `dash build`. It is suppressed in normal use and surfaces only under
`capture noisily`; the cause was not isolated. Worth tracing — it indicates a
`capture confirm file` failing somewhere in the spec path.

**Closed by 81ebbc5 (WP-03).** Traced with `set trace`: the note came from
the two spec writers' `file open ..., write replace` on a freshly declared
tempfile, never from a `capture confirm file`; both write quietly now.
Measured 23sep2026 at `4ede074`: `capture noisily dash build` prints only
"dash: dashboard saved to ...".  No regression test reads a build log for
the note (BUGS.md, "Every successful `dash build' prints an unexplained
'file not found'", records that).

**Regression test, WP-24.**  test/test_bug_regressions.cscript BR-02 reads
the logs of `capture noisily dash build`, of the immediate route and of
`capture noisily dash serve` up to its launch for the note, after showing
that its search finds the note itself; with `quietly` taken off either spec
writer on a copy of the tree, it fails (ROADMAP WP-03's AC-03.4).

---

## D. Standalone versus server — one product, two renderers

`dash.sthlp:516-533` carries a Server Mode comparison table. Every one of its
13 rows is accurate. The gap is everything the table does not list.

### D1. The unification never happened — S1, READ, CLOSED by WP-09

`ServerAppBuilder` emits `_DASH_MAPPER = GlyphMapper(...)` at
`dash_render.py:12432` and calls it **once**, for `scatter` (`:14090`). The
other 37 plot types remain a hand-written `if/elif` chain in generated string
literals (`:14058-14890`), plus **two further near-duplicate reduced chains**
for facet and "Total" panels (`:15144-15212`, `:15245-15315`). Three dispatch
tables, independently maintained.

The comment at `:12318-12327` claims the server branches call the shared
mapper. They do not.

**Closed by WP-09** (cf7094c, 878529c, 5422974), with WP-11's 151c6cb
removing the two facet chains.  Every plot type the code dispatches draws
through `GlyphMapper` in both modes, from one family dispatch
(`_dash_draw_layer`) copied into the app.  Pinned by
`test/test_server.py::TestTheServerDispatchesThroughTheSharedTable`,
`test/test_server_facets.py::TestTheGeneratedAppHasOneDispatch`,
`test/test_server_layer_defects.py::TestTheUnificationKeepsD2Closed` and the
parity corpus of `test/test_mode_parity.py`, which carries a bare entry for
every dispatched type (all passing at `4ede074`).

### D2. Confirmed divergences — S1, CLOSED by WP-10 (with WP-09's dispatch, which closed the pci, fpfitci and pc* rows)

| Plot / feature | Standalone | Server |
|---|---|---|
| `pci` | `[Segment]` | **`[]` — draws nothing, silently.** `:14781-14796` reads `y1var/x1var/y2var/x2var`; `dash.ado:1164-1212` emits `"values"` for `pci`. The gate is never true. This is the same bug already fixed standalone (see the note at `:10015-10018`), never ported. |
| `fpfitci` | `[VArea, Line]` | **`[Line]` — no confidence band.** `:14253-14263` is a verbatim copy of the `fpfit` branch. `lfitci` (`:14375`) and `qfitci` (`:14402`) do draw bands. |
| `pcspike`/`pcarrow`/`pcbarrow` with a repeated variable | draws | **`ValueError: Expected unique column names`** — `:14681-14683`, `:14697-14699` build `cols` with no de-duplication. |
| `pcscatter` with a repeated variable | `[Scatter]` | **`[]`** — `dict.fromkeys` dedupe at `:14788` shortens the list, so `if len(_cols) == 4` at `:14789` is false. |
| `bar` / `histogram` / `area` hover | 1 HoverTool | **none** |
| `hover(foreign)` | `[weight, mpg, foreign]` | **`[weight, mpg]` — `hover()` ignored** |

`HoverTool` is imported at `:12879` and never instantiated. The only server
hovers that appear come indirectly from the three mappers the server does
delegate to.


**Closed.** WP-09 closed `pci`, `fpfitci` and the `pc*` repeated-variable
cases; WP-10 closed hover. Measured after: all 38 plot types, bare and with
`hover(foreign)`, produce identical tooltips in both modes, and the saved
renderer's own duplicate HoverTool is gone with them. The one hover fact
this entry did not record: `dash line mpg weight, hover(foreign)` drew NO
tooltip at all when saved.

### D3. Qualifiers are not read at all in server mode — S1, CLOSED by WP-10

There is no `plot.get('if_expr')` anywhere past `dash_render.py:12700`; the
server reads only graph-level qualifiers (`:13812/13819`, `:15011-15012`,
`:15528-15529`). KPI `if`/`in` is likewise ignored (`:15331`, `:15645`,
`:15694`) — producing a wrong-but-plausible number, the exact failure
`dash.ado:1938-1945` was written to fix on the standalone side.

`dash.ado:1484`'s comment ("per-plot qualifiers are not read in build/server
flows") is now stale for standalone and accurate for server.


**Closed by WP-10.** One `_dash_qualified_frame` reads every qualifier in
both modes -- graph, plot and KPI -- through `_validate_if_expr`'s whitelist.
The app's own `_safe_g` is an alias of it now. `dash.ado:1787` and `:2023`
were corrected.

### D4. `by()` drops 20 plot types in server mode — S1, CLOSED by WP-11

The facet and Total chains (`:15144-15212`, `:15245-15302`) handle 18 types.
Missing: `lfitci qfitci rarea rbar rspike rcap rline rconnected rcapsym
rscatter scatteri pci pcspike pcarrow pcbarrow pcscatter tsline tsrline
mspline function`. They fall off the end of the `elif` chain with no `else`
and no warning. Standalone's facet path reuses `_make_figure` and therefore
the full dispatch.

Those blocks also hardcode the style the parity test exists to catch:
`size=6` at `:15145, 15200, 15246`; `width=0.8` at `:15150`.


**Closed by WP-11.** The two chains are gone; every by() panel is built by
the same emitted figure body as the graph, through one family dispatch.
Measured after: 0 of 38 types differ under `by(foreign)`, every panel
compared. Found alongside and fixed: the SAVED dashboard grouped the
unqualified frame (the reverse of D3), a served histogram ignored its
qualifier, and — a WP-09 regression — no served computed layer was
recomputed after a filter move.

### D5. `mlabel()` excludes all range types in server mode — S2, CLOSED by WP-10

`dash.sthlp:698-700` says `mlabel()` applies to "scatter, line, connected,
bar, spike, dot, dropline, and all range plot types". Standalone honours
every one (`_apply_mlabel_opts:3301`, wired at 13 call sites).
`dash_render.py:14897-14901` skips the mlabel block for every range type, and
for `scatteri`, the `pc*` family, `lfit`, `qfit`, `lfitci`, `qfitci`,
`lowess`, `mspline`, `function`, `histogram` and `kdensity`.


**Closed by WP-10, in the opposite direction to the one recorded here.** By
the time WP-09 had routed every type through `GlyphMapper`, the mapper drew
each layer's labels and the app's own "common mlabel block" drew a SECOND
set over them: `line`, `connected`, `dot`, `dropline` and `tsline` carried
two LabelSets when served, and `lpoly`, `lpolyci`, `fpfit`, `fpfitci` and
`mband` carried one where the saved dashboard carries none. The block is
deleted. Measured after: identical labels for all 38 types.

`rscatter` carries no marker labels in EITHER mode, although `dash.sthlp`
lists every range type as taking `mlabel()`. That is a coverage gap, not a
divergence; it belongs to WP-13.

### D6. No "drew nothing" warning in server mode — S2, CLOSED by WP-10

Standalone warns at `:10078-10091` when a layer adds no data from a non-empty
source. The generated app has no equivalent, which is why D2's silent
failures are silent.


**Closed by WP-10.** `_dash_layer_drew_anything` and
`_dash_report_empty_layer` are module-level and run by both modes, so the
report cannot be worded differently in one of them.

### D7. Smaller divergences — S3, READ, CLOSED by WP-09 (with WP-10's TR-10.8 and WP-20's served policy)

- Server `ptype` is not lower-cased (`:14031`) while the facet chains are
  (`:15137, 15237`); the main chain lacks the `'hist'` alias the facet chains
  have. Unreachable through `dash.ado` today, but three tables disagree.
- `layout(name:row,col)` is 1-indexed in server mode (`:15795`) and accepts
  **0-based too** standalone (`:11126-11128`) — one spec, two meanings.
- Tabs: an unassigned item is drawn *below* the tabs in plain-grid and server
  modes (`:11981, 12072, 15855`) as documented, but *above* them under
  `layout(bs)` (`:10888-10889`).
- KPI `fmt()`: server `_format_kpi` (`:13665-13682`) always comma-groups,
  ignores the `c` suffix, and has no `%9.0g` default or width-overflow
  fallback. `fmt(%12.0fc)` ≡ `fmt(%12.0f)` when served.
- Legend text size: standalone uses `text_font_size` (`:9067-9068`), server
  uses `tick_label_font_size` (`:12660`). These differ for 13 of 14 schemes.
- `_MAX_EXPR_CHARS` is a module constant standalone (`:2271`) and hardcoded
  `5000` in the server copy (`:14872`).
- No CSP in server mode: `_CSP_META` (`:660-668`) is injected at `:10897` and
  `:12139`, both standalone.

**Closed by WP-09**, which put every type through one dispatch that
lower-cases the type (TR-09.3), with the rest done by WP-10's TR-10.8 and
the last row by WP-20.  Each row, at `4ede074`: one dispatch table, copied
into the app (`test/test_server.py::TestTheServerDispatchesThroughTheSharedTable`);
`layout()` placement reads both index bases in both modes
(`test/test_server_layer_defects.py::TestLayoutPlacementMeansOneThing`);
an unassigned item sits below the tabs under every layout
(`::TestTabsAreWhereTheHelpSaysTheyAre`); one KPI formatter
(`::TestTheKpiCardIsFormattedTheSameWay`); one legend text size
(`::TestTheLegendSaysTheSameThing`); one `_MAX_EXPR_CHARS`
(`test/test_resource_limits.py::TestTheBoundsThatAlreadyWorkedAreKept`);
and the served app sends and embeds a content security policy
(`test/test_csp.py::TestTheServedTemplate`, `::TestTheServedApp`).

### D8. The parity guard covers less than half the surface — S2, CLOSED by WP-12

`test/test_mode_parity.py` `CORPUS` (`:186-274`) covers **17 of 38** plot
types: scatter, line, area, bar, histogram, kdensity, mband, dropline, spike,
connected, lfit, lpoly, lpolyci, dot, rcapsym, scatteri, mspline.

**Uncovered (21):** `function pci pcspike pcarrow pcbarrow pcscatter lfitci
qfit qfitci fpfit fpfitci lowess rarea rbar rspike rcap rline rconnected
rscatter tsline tsrline`.

No corpus entry sets `by()`, `link()`, `filter()`, `tabs()` or a KPI, and
`_glyph_profile` (`:128-147`) collects neither tools nor tooltips. **Every
finding in D2–D6 would have been caught by a corpus that did.**


**Closed by WP-12.** The corpus covers every plot type the code dispatches
(the list is derived from the dispatch tables and cross-checked against
`dash.ado`'s Supported: text and the Mata table, so a type cannot be added
without an entry) and every cross-cutting feature; the profile is the whole
document -- layout tree, widgets, KPI cards, and per figure the glyphs with
the rows and coordinates they draw, annotations, legend, tools with
tooltips, axes and chrome -- plus a filter move compared against the saved
renderer given the equivalent qualifier. Measured the day it was widened:
twelve further divergences (legend click policy and sub-options, univariate
axis titles, xlabel() grammar, yaxis(2), colorvar(), the session level,
dropdown values, slider titles, the saved widgets' data source, KPI order,
the header, facets in tabs), every one fixed as one implementation; see
BUGS.md. The one open server gap the guard now names is dates, asserted to
still fail so its fix is noticed.

---

## E. The option surface

### E1. 39 options are accepted, reported, and inert — S2, READ; nodraw CLOSED by WP-13; the other 38 deferred by WP-27 (documented as unsupported, and named when given)

Two `_dash_pending` blocks: graph-level at `dash.ado:364-384` (20 entries)
and plot-level at `:593-632` (39, a strict superset).

**Union, 39 distinct:**

```
at          b1title     b2title     blabel      ciopts      cmissing
colorlist   coloruseplegend         connect     fitopts     fxsize
fysize      horizontal  l1title     l2title     lineopts    lstyle
mlabwidth   mlpattern   mlstyle     mstyle      nodraw      play
pstyle      r1title     r2title     recast      scale       sort
subtitle2   t1title     t2title     text        title2      vertical
xmlabel     xmtick      ymlabel     ymtick
```

This list matches `dash.sthlp`'s "Unsupported Stata twoway options" section
exactly, in both directions — help and code agree, and
`test_unsupported_report_is_true.py` enforces it. **This is honest reporting,
not a silent gap**, and it is the best-governed part of the surface.

Two nuances:

- The 19 plot-level entries are still written into the JSON by
  `_dash_plot_opts_to_json` (`dash.ado:862-874`); they are dropped by the
  *renderer*, not the ado. Two are read and explicitly discarded
  (`coloruseplegend` at `dash_render.py:3037`, `mlabwidth` at `:3398`).
- **`nodraw` is on both pending lists but is actually honoured**
  (`dash.ado:1765` suppresses the browser launch). So dash prints
  "ignoring unsupported option(s): nodraw()" for an option it just applied —
  precisely the stale-list failure the comment at `dash.ado:578-592` was
  written to prevent. It slips past the enforcing test because `nodraw`
  changes browser behaviour, not file output.

**nodraw closed by WP-13.** It is off both pending lists and honoured on
`dash build` as well as on an immediate render (the help had claimed the
former and the registry's graph_options were never read for it). The
launch decision is `_dash_browser_wanted`, a program a script can call
without launching anything; `test_nodraw_honoured.cscript` certifies both
halves, and `test_unsupported_report_is_true.py` pins that nodraw is never
on a pending list and that the launch decision still reads it.

**The other 38 deferred by WP-27** (24sep2026), explicitly, as AC-27.3
allows.  Each is a twoway option dash does not implement; dash.sthlp's
"Unsupported Stata twoway options" lists every one, and dash names it in its
"ignoring unsupported option(s)" note whenever it is given
(`test_unsupported_report_is_true.py` holds the list, the help and the note
together).  Nothing is drawn wrong and nothing is dropped in silence, so
what is left is the scope of twoway dash covers, not a defect of what it
does: implementing any of them is new work, not release closeout.  `sort`
was the one whose note misstated the page -- dash already draws what a bare
sort asks for -- and since the S3 batch a bare sort on the connected types
is taken without a note; sort(varlist) is still named.

**Since WP-29 (P0.1, commit b0d170d).** `sort` and `sort(varlist)` are honoured on line, connected, area, rline, rarea and rconnected, which otherwise join in the data's order as twoway does; tsline and tsrline join in time order. The remark above that sort(varlist) is still named holds only for the other plot types.

### E2. Options dropped with *no* report — S2, CLOSED by WP-13

These are not on either pending list, so `_dash_report_ignored` never names
them:

| Option | Declared | Behaviour |
|---|---|---|
| `link()` at plot/graph level | `dash.ado:289, 507` | Stored, promoted, written to `graph_options.link` (`:1465`). The renderer reads only `build_options["link"]` (`dash_render.py:11288, 12763`). Silently inert. |
| `filter()` at plot/graph level | `dash.ado:289, 507` | Same path; renderer reads only `build_options["filter"]` (`:11295, 12764, 8726`). |
| `saving()` on a **named** graph | `dash.ado:283, 506` | `_dash_plot` routes to `_dash_register_graph` (`:1487`) and never reaches the `saving` extraction at `:1602`. `dash build`'s own `saving()` wins. |
| weights | `dash.ado:781-826` | See A3. |

**Closed by WP-13.** `link()` and `filter()` written on a graph are on both
pending lists and named in the note (they belong to `dash build`; the help
says so under Unsupported); `saving()` on a named graph is named at the
route decision in `_dash_plot`, since the immediate route honours it;
weights are A3. The converse of the inertness guard now exists:
`test_unsupported_report_is_true.py` classifies every option the two syntax
blocks declare as pending, alias, route, or live, and renders every live
one twice to prove it changes the document -- 86 options, all live.
`test_option_surface.cscript` O2-08 to O2-10 certify the three from Stata.
The `_dash_prepare_spec` row is unchanged.
| `saving()`, `replace`, `server` in `_dash_prepare_spec` | `:2009, 2019, 2020` | Declared and never referenced in the body. Harmless for `dash build`; `dash serve` forwards them through its `*`, so they would be accepted-and-ignored if C1 were fixed. |

### E3. Sub-options vanish without a note — S2, CLOSED by WP-14

`legend()`, `xlabel()`, `yscale()`, `by()`, `xline()`, `filter()` are all
declared `string asis`, so unknown *sub*-keys never reach the ignored-option
report. `dash.sthlp:162-163` claims "Nothing is ever dropped without being
named". Measured as silently accepted and unhandled:

`legend(span|stack|colfirst|holes()|keygap()|symxsize()|textwidth()|bmargin())`,
`xlabel(, valuelabel)`, `ylabel(, labcolor())`,
`yscale(reverse|noline|titlegap())`, `xtitle(, orientation())`,
`xline(3000, lcolor() lpattern())`.

`_rebuild_legend` (`dash_render.py:8956`) has no unknown-key warning. Only
`xscale`/`yscale` get one (`_report_unhandled_scale_opts:805`), and only for
5 tokens.

`by()` is the same shape: `_parse_by_raw` (`:8669-8701`) regex-matches
`cols()`, `total` and `missing` and discards everything else with no
diagnostic. Stata's `by()` also takes `rows()`, `holes()`, `iscale()`,
`compact`, `noedgelabel`, `style()`, `colfirst`, `norescale`, `yrescale`,
`xrescale`, `noixlabel`, `noiylabel`, `noixtick`, `noiytick`, `imargin()`,
`ixaxes`, `iyaxes`, `altshowyvars`, plus its own `title()`/`note()`/`legend()`.

`_parse_filter_raw` (`:8730-8774`) is worse: a spec whose text contains
`;` `` ` `` `$` `\` `__` or the words `import`/`eval`/`exec`/`open`/`getattr`
is discarded **whole**, with `rc=0` and no message. A legitimate
`label("R&D __ spend")` makes the entire filter widget vanish. An
unrecognised `type()` is likewise skipped silently (`:11804-11805`, server
`:15462-15463`).

**Closed by WP-14.** One reporter, in by()'s words -- `dash: <option>()
sub-option(s) not implemented and ignored: <tokens as written>` -- from code
both render modes run, once per graph per render: `legend()`,
`xlabel()`/`ylabel()`/`xtick()`/`ytick()`, `xscale()`/`yscale()`,
`title()`/`subtitle()`/`note()`/`caption()`/`xtitle()`/`ytitle()`,
`xline()`/`yline()` and `filter()`. The filter parser refuses aloud, and
only for a name that is not a name or a `type()` it does not build: the
label reaches nothing but a Bokeh widget title and a `repr` literal, so the
old gate refused `label("R&D __ spend")` and protected nothing. On the way:
`xtitle("Weight", size(large))` no longer titles the axis with the
sub-option text; `ylabel(#5, grid)` was silently ignored (the stripped
sub-option left its comma behind); and three served divergences the parity
guard now names -- `title()` size()/color(), `xscale(range())`, and the
caption's position. Not covered, and said so: `plotregion()`,
`graphregion()`, `xlabel2()`/`ylabel2()`/`xscale2()`/`yscale2()`,
`colorcuts()` and `tabs()` still drop their sub-options in silence.

**Since WP-30 (P1.20a, commit 2207ddb; P1.20b, commit 6e2af0c).** `plotregion()` and `graphregion()` sub-options, Stata's abbreviations included, are drawn or named; none is dropped in silence. The plot-region margin and inner box are drawn (P1.20b).

### E4. `bw()` silently changes meaning — S2, CLOSED by WP-13

`dash.ado:560` folds `bw` → `barwidth` unconditionally. Real Stata accepts
`bw(400)` on `twoway lpoly` (measured `rc=0`) and rejects it on `twoway bar`
(`r(198)`). So `dash (lpoly mpg weight, bw(400))` sets `barwidth`, not
`bwidth`, with no note — a valid twoway command whose meaning changes. This
directly undercuts the drop-in claim at `dash.sthlp:123, 162`.

**Closed by WP-13.** `_dash_fold_bw` resolves `bw()` once the plot type is
known: `bwidth()` on lpoly, lpolyci, lowess and kdensity (twoway rc 0);
`barwidth()` on bar, rbar, histogram, dot and spike (dash's documented
superset, where twoway rejects `bw()` but takes `barwidth()`); named in the
note on every other type; and `bw()` beside `bwidth()` is twoway's r(198).
`test_alias_semantics.cscript` measures twoway's own rc for each type in
the same run and certifies dash against it.

### E5. Validation is applied to exactly one option — S2, CLOSED by WP-15

`level()` is validated in the ado (`dash.ado:549-558`) with a clear message.
All 69 other plot-level values and all 54 graph-level values are emitted
verbatim as JSON strings. Some get downstream validation
(`_stat_option_float` for `xsize`/`ysize`/`aspectratio`,
`dash_render.py:9228-9254`; `_resolve_kpi_color`, `:10484-10485`), but it is
not systematic.

`dash kpi` is the best-validated surface — statspec regex (`:1839`), stat
whitelist (`:1845`), percentile bounds (`:1850`), `confirm variable`
(`:1863`), name regex (`:1865`), `update()` whitelist (`:1871`). Its one gap
is `fmt()`, which is unvalidated and interpolated into an evaluating context:
`local kpi_display : display `fmt' `kpi_value'` (`:1918`). Measured:
`fmt("HACKED" %9.2f)` → `r(111) HACKED not found`. **Not an injection
vector** — the quotes are stripped by `syntax` and the token is then resolved
as an identifier — but a confusing failure where `level()` gets a clear one.

**Closed by WP-15.** Measured first, against twoway itself, 22sep2026: 248
probes, 60 refused, 188 accepted, 36 of the accepted with `(note: named
style X not found in class Y, default attributes used)`. twoway never
refuses a style name -- `mcolor(notacolour)`, `msymbol(nonsense)`,
`msize(abc)`, `lwidth(abc)`, `lpattern(bogus)`, `msangle(abc)`,
`mlabposition(13)`, `xsize(abc)` all draw with that note, and
`scheme(nonsense)` with its own `(note: scheme nonsense not found, using
s2color)` -- but it does refuse a number outside a range it has
(`msangle(400)`, `lwidth(-1)`, `yaxis(0|10|abc|1.5)`, `xsize(0|101)`,
`bin(0|abc|2.5)`, `bands(0|abc|2000)`, `degree(-1|x|1.5)`, `bwidth(0|-1)`
on lpoly and `bwidth(-1|abc)` on kdensity (kdensity accepts `bwidth(0)`
itself; dash's positive rule is its own there), `n(0|abc|2.5)`,
`kernel(bogus)`, `aspectratio(abc)`,
`barwidth(abc)`, lfitci `level(abc)`) and answers `mlabel(nosuchvar)` and
`by(nosuchvar)` with r(111); and it silently accepts values dash cannot
use: `jitter(abc|-3|31)`, `jitterseed(abc|-1|2.5)`, `level(150|0|-5)`,
lowess `bwidth(5|0|-0.5)`, `msize(-1|0)`, `degree(5)`, `n(1)`,
`yaxis(3..9)`. Every value in every corpus (the 299-command
`twoway_corpus.do`, `conformance_corpus.txt`, the help examples,
`examples/*.do`, every cert script: 1015 values across 205 options and 70
sub-option keys) is a plain number, keyword, variable or quoted RGB
triplet, and the rules were checked against all of them before they were
written down.

The rule: dash refuses a value where twoway refuses it, refuses a word
where a number-only option got one twoway would have swallowed, and, like
twoway's own note, reports and falls back on the scheme where a style name
(colour, symbol, size, line width, pattern, angle, clock position,
intensity) is unknown. One declarative table, `_dash_option_rules`
(`option=kind[,p1[,p2[,p3]]][@type1|type2]`; kinds `num`, `int`, `pos`,
`style`, `istyle`, `enum`, `numlist`, `var`, `varlist`, `byvarlist`,
`format`), read by `_dash_validate_value` and applied once per segment by
`_dash_validate_opts` right after `_dash_fold_bw` -- the graph rules too,
against the segment's own `xsize`, `ysize`, `aspectratio`, `hover` and
`by`, so `(scatter mpg weight, xsize(500)) , xsize(5)` is refused as
twoway refuses it -- and once per graph in `_dash_plot` for the
after-comma winners; the hand-written `level()` block is now a row of it.
A refusal is one `display as error` line, `dash: opt() must be ... (got:
V)`, then r(198), or r(111) for a variable that does not exist (`dash:
by(): variable X not found`), with a second sentence for the five bounds
named below. A value that passes is written back normalised: an enum in
lower case, an integer as an integer (`yaxis(2.0)`, `yaxis(02)`,
`yaxis(+2)` and `n(1E3)` reach the renderer as 2, 2, 2 and 1000), a
numlist expanded (`colorcuts(1(1)5)` as `1 2 3 4 5`, `range(0,10)` as
`0 10`), a variable list as full names, and every value `ustrtrim()`ed
first so a tab-padded `jitter(5)` passes as it does in twoway. The `var`,
`varlist` and `byvarlist` kinds use `unab` alone: a head it cannot expand
but `tsrevar ..., list` can is a time-series expression dash cannot draw
and is refused, `dash: colorvar() must name a variable, not a time-series
expression (got: L.price)`, r(198); `tsunab`, tried first in the first
cut, is sclass and its `sreturn clear` wiped every option of the segment,
so `_dash_validate_opts` now also restores any s() macro a value check
emptied. In `_dash_kpi` the `update()` check and the `fmt()` gate both
run before the `name(k, replace)` block destroys the old KPI, so `name(k,
replace) fmt(bogus)` leaves the registry as it was and the next `dash
build` runs. KPI `fmt()` is a character gate (a single leading `%`, then
only `[A-Za-z0-9_.,:!/+-]`, at most 60 characters) followed by `confirm
numeric format`, measured over 26 probes to return 0 for
`%9.2f %9.0gc %-12.3e %09.2f %9,2fc %12.0fc %tdCCYY-NN-DD %tcHH:MM:SS %21x
%16H %tc %td %tm %9.2fc %-9.2f %10.0g %8.0e` and 7 for `%12s bogus 9.2f
%9.2 %9.2f_n %9.2f%9.2f %c % %%9.2f`; `: display` stays the formatter, on a
token proven to be one numeric format (two further probes: `strofreal(x,
"bogus")` returns "" with rc 0, in silence, so it is no validator).

Deliberately not gated: `scheme()`, every colour option, `msymbol()` and
`marker()`, `lpattern()`, the structured options (legend, the axis grammar,
`xline()`, by()'s sub-options, `plotregion()`, `graphregion()`, `filter()`,
the title family) and `name()`/`saving()`, which keep their existing
checks. An unknown style inside one of them (`title(T, size(bogus))`,
`plotregion(lwidth(abc))`, `graphregion(color(notacolour))`) gets a note
and the default in twoway and in dash alike; an unknown sub-option word,
which twoway refuses (`legend(garbage)`, `xscale(bogus)`: r(198)), dash
names in its sub-option note and draws without. The renderer's note is one
helper in both modes, `_dash_style_note` (`dash: lwidth(abc) is not a
recognised line width; using the scheme's default.`), printed once per
option, value and kind per render (`_DASH_NOTED`, cleared by
`_dash_reset_notes()` at the start of `DashRenderer.render()` and of the
served `make_document`, so `connected`'s line and marker border,
`rcapsym`'s spine and dot and every `by()` panel say it once), where it
was silent on every marker layer, aborted the whole render on `scatteri`,
on `plotregion(lwidth(abc))` and on `msize(1e400)`, and swallowed the bad
value in silence for `area color()`, `bar`/`histogram` `color()` beside
`blcolor()`, `bgcolor()`, `plotbgcolor()`, `plotregion(color)`,
`graphregion(color)`, `xline(lpattern())`, `legend(size())` and the KPI
`color()`.

Deliberate deviations from twoway, which accepts each of these values with
rc 0. Five say so in a second sentence of the message: `yaxis()` and
`xaxis()` 1..2 (`dash draws two axes.`; twoway allows nine); `degree()`
0..3 (dash fits up to cubic; twoway any nonnegative integer); `n()`
2..10000 and `bin()` 1..1000 (the renderer already capped them there with
a warning; the cap is the resource guard CLAUDE.md rule 18 asks for);
lowess `bwidth()` in (0, 1] (a fraction of the sample; twoway accepts 5
silently and computes nonsense). The rest are dash's own rules too, but
their message carries no second sentence: `colornlevels()` 2..256 (a
dash-only option); `jitter()` 0..100 (documented as a percent of the axis
range); `level()` strictly inside 0 and 100 (dash's existing rule; twoway
does not check); `barwidth()` > 0 (twoway draws `barwidth(0|-1)`);
`aspectratio()` >= 0 (twoway draws `aspectratio(-1)`); `jitterseed()` and
`jseed()` >= 0 (twoway accepts `jitterseed(abc|-1|2.5)`); kdensity
`bwidth()` > 0 (kdensity accepts `bwidth(0)`). `bands()` 1..200 is
twoway's own bound. `mlabposition()` and `fintensity()` are not bounded
in Stata: like `msize()`, a name or any number passes, and the renderer
notes `mlabposition(13)` or `fintensity(150)` and draws the default, as
twoway does (with a note for the first, in silence for the second). Two
deliberate supersets, where dash accepts what twoway refuses with r(198):
`kernel(GAUSSIAN)` is normalised to `gaussian`, and `lwidth(())` passes
as a name, which the renderer then reports. Not fixed here, follow-ups:
`dash (scatter mpg weight, level(95))` is accepted and `level` lands in
the JSON where twoway's `scatter` refuses `level()` as not allowed -- the
table judges values, not which plot type takes an option, which is E1's
territory; and `by(a) by(b)` prints `dash: ignoring unsupported
option(s): by()`, a misleading note for a repeated option twoway accepts
with rc 0. The line references in the body above were measured at the
WP-15 baseline (cc3c4ac): `level()` was at `dash.ado:830-842`, the
`: display` at `:2410`, `_stat_option_float` at `dash_render.py:7050` and
`_resolve_kpi_color` at `:7486`; the table moved them.

### E6. Escaping and encoding holes — S2, READ, CLOSED by WP-08

- **`_dash_json_str` (`dash.ado:224-232`) handles `\`, `"`, TAB, LF, CR and
  nothing else.** `\b` (8), `\f` (12) and every other C0 control byte are
  illegal raw inside a JSON string and would surface as a Python
  `JSONDecodeError` rather than a Stata-side diagnostic.
- **`theme()` is the one build option written unescaped** — `"theme":"`theme'"`
  at `dash.ado:2343`, while `title`, `subtitle`, `tabs`, `scheme` and `filter`
  all go through `_dash_json_str` first.
- **`saving()` backslashes are doubled and never un-escaped.** `_dash_json_str`
  turns `\` into `\\`; the extractor at `dash.ado:1602-1607` slices the raw
  JSON text and uses it as a filesystem path. Measured: `C:\dir\out.html`
  comes back as `C:\\dir\\out.html`. **Breaks every Windows `saving()` path on
  the immediate-render route.** `dash build` is unaffected — it uses the local
  directly.
- **`_dash_check_utf8` is called once**, at `dash.ado:1385`, on `` `0' `` in
  `_dash_plot`. `_dash_kpi`, `_dash_build`, `_dash_prepare_spec`,
  `_dash_serve` and `_dash_serve_spec` do not call it. So KPI `title()`,
  build `title()`/`subtitle()`/`tabs()` and `filter(… label("…"))` reach the
  JSON with no UTF-8 gate — contrary to CLAUDE.md rule 16.

**Closed by WP-08** (7ddbc08), row by row: `_dash_json_str` writes `\b` and
`\f` in their short forms and every other C0 byte as `\u00XX`
(`test/test_json_escaping.cscript` JSE-01 to JSE-08); `theme()` was escaped
by WP-05 and is now refused unless it names one of the six themes, WP-17
(`test/test_theme_escaping.cscript` THM-01 to THM-09); `saving()` is read
back through `_dash_json_get_str`, so a backslash reaches the path the user
gave (JSE-09, JSE-10); and `_dash_check_utf8` runs at every command entry
point (`test/test_utf8_validation.cscript` UTF-11).  All three scripts
re-run 23sep2026 at `4ede074`: passed.

### E7. `_dash_validate_path` — what slips through — S3, MEASURED, CLOSED by WP-08

`dash.ado:157` rejects `" \` $ ; & | < >`, TAB/LF/CR, a literal `..` anywhere,
and enforces the extension. Measured to pass with `rc=0`:

`~/x.html` · `out.HTML` · `a*b.html` · `a?b.html` · `-rf.html` ·
`/etc/passwd.html` · `a!b.html` · `a\b.html` · `a#b.html` · `a%b.html`

Notable: **no directory confinement** — any absolute path is writable; `~` is
accepted but expanded by neither `shell open` nor Python; a **leading `-`**
survives, and `shell open "-e.html"` has the target parsed as a flag.
Conversely a legitimate `my..report.html` is refused.

`main()` in `dash_render.py:16121-16157` does not validate `output_path` at
all — the protection is real via the Stata entry point and absent if the
renderer is invoked directly.

**Closed by WP-08** (7ddbc08): `..` is a path-segment rule, so
`my..report.html` is accepted and a `..` segment still refused; a leading
`-` on the file name is refused with the `./name` remedy; a leading `~/` is
expanded from `$HOME`; and `main()` validates `--output` itself
(`_validate_output_path`).  Certified by `test/test_path_validation.cscript`
PV-13 to PV-19 (re-run at `4ede074`: passed) and the output-path cases of
`test/test_adversarial_matrix.py`.  Directory confinement was left out, as
TR-08.7 allowed ("consider"): an absolute path the user names is still
written, as `twoway`'s own `saving()` writes it.  One consequence belongs
elsewhere: `_validate_output_path` requires `.py` in server mode, which the
extension-less path `dash serve` passes never has -- see C1.

**Since WP-30 (P1.29, commit 0e8fbaf; P1.27, commit 6906236).** The Windows `%` and `!` opener case is closed: a page path holding a cmd metacharacter is written but never passed to the shell (P1.29). The over-refusal of `..` and `; & | < >` is removed; `saving()` accepts them as twoway does and keeps the sink-tied checks (P1.27).

---

## F. `twoway` parity

### F1. Four real `twoway` plot types are rejected outright — S2, MEASURED, CLOSED by WP-22
**Closed by WP-22.**  `pcarrowi` and `pccapsym` are drawn in both modes.
`contour` and `contourline` -- and `rpcap` and `rpspike`, which
StataNow 19.5 added -- are refused by name, r(198), each with what to use
instead, and the help's Plot types section names them.  Tests:
`test_pccapsym_pcarrowi.py`, `test_help_plot_types.py`,
`test_parser.cscript` P1A-49..59.


`contour`, `contourline`, `pcarrowi`, `pccapsym` → `r(198) unrecognised plot
type` (`dash.ado:938-948`, against the 38-row table at
`dash_parse.mata:174-211`). They appear nowhere in `dash_render.py` either.

`dash.sthlp:174` claims "An unknown option is never an error, so a command
copy-pasted from a do-file always runs." That is true of *options* and false
of *plot types* — **and the help lists no supported plot types anywhere**, so
a user has no way to anticipate it. The error message itself does list all 38.

### F2. Eleven supported plot types are undocumented — S3, READ, CLOSED by WP-22
**Closed by WP-22.**  `dash.sthlp`'s Plot types section lists every type
dash draws, in `twoway`'s groups, and `test_help_plot_types.py` holds it to
the renderer's own list in both directions.


Present in `dash_parse.mata:174-211`, routed in `dash.ado`, rendered in
`dash_render.py`, and mentioned nowhere in `dash.sthlp`:

`rconnected rscatter pcspike pcarrow pcbarrow pci pcscatter tsline tsrline
mband function`

`tsline`/`tsrline` even carry bespoke `tsset` fallback logic and error text
(`dash.ado:1013-1024, 1080-1092`).

### F3. Common twoway options land in "unknown" rather than the documented list — S3, MEASURED, CLOSED by WP-22
**Closed by WP-22.**  Measured against `twoway` itself: `clcolor()`,
`clpattern()` and `clwidth()` are honoured as `twoway` defines them (the
connecting line only, over the l-options); `mlabangle()` and `mlabformat()`
are honoured; `sort(varlist)`, `mlabvposition()`, `mlabtextstyle()` and
`xoverhangs`/`yoverhangs` are declared and listed in the help's
Unsupported section; the rest are not `twoway` options where they were
written, stay unknown and named in the note, and the help gives
`twoway`'s own spelling for each.  Tests: `test_twoway_option_parity.py`,
`test_twoway_option_parity.cscript`.

**Since WP-29 (P0.1, commit b0d170d).** `sort(varlist)` is honoured on line, connected, area, rline, rarea and rconnected; the help's Unsupported section names it, with a bare `sort`, only for the other plot types.


These are reported — correct behaviour — but none appears in the help's
"Unsupported twoway options" list, so the note arrives as a surprise:

`clcolor() clpattern() clwidth()` (the standard `line`/`connected` styling
triple), `addplot()`, `margin()`, `region()`, `bargap()`, `xreverse`
`yreverse`, `xalternate` `yalternate`, `xoverhang` `yoverhang`, `xcommon`
`ycommon`, `lockaspect`, `zoom()`, `altaxis`, `mlabangle()`, `mlabformat()`,
`mlabvposition()`, `mlabtextstyle()`, `ddensity`, and `sort(varname)` — dash
declares `SORT` as a flag, so the twoway `sort(x)` form is *unknown* rather
than merely ignored.

**Since WP-30 (P1.24, commit 390d964).** `mlabvposition()` and `mlabtextstyle()` are drawn in both modes, finishing WP-22's partial fix for the marker-label options; with E1, they are no longer accepted and inert.

### F4. Documented capabilities that do not work as described — S2, CLOSED by WP-23; bare-name row CLOSED by WP-17

| Claim | `dash.sthlp` | Reality |
|---|---|---|
| "`p97.5`" — any percentile | 466-467 | **`dash kpi p97.5(price)` → `r(198)`.** The statspec regex (`dash.ado:1839`) rejects the `.`, and `:1849` is integers-only. Both renderers already accept fractional percentiles (`dash_render.py:8339, 7278`); it can never be entered. |
| "`nodraw` has the same effect [as `nobrowser`]" — in the **`dash build`** table | 296 | **False for `dash build`.** `dash.ado:2509` tests only `` `nobrowser' `` and `$dash_nobrowser`. The help contradicts itself at `:1149-1152`. |
| "put its `.scheme` file in the working directory and give its **base name**" | 1084-1086 | **Fails at build level.** `dash_render.py:7967-7970` rejects any name that is neither an alias nor a builtin unless it ends in `.scheme`, *before* the CWD bare-name branch (`:1704-1716`, added for exactly this) can run. Measured: `scheme(mycustom)` → s2color + warning; `scheme(mycustom.scheme)` → works. Graph-level `scheme()` *does* work (`:9484-9487` bypasses the gate) — so the same name behaves differently on `dash scatter` and `dash build`. **Fixed by WP-17**, 22sep2026: the bare name and the `.scheme` name resolve on every entry point and the page and the figure take the same file; measured and closed under G8. |
| "joins them with a **semicolon** internally" | 408 | Joiner is `" \|\| "` (`dash_parse.mata:812`). Semicolon is only a legacy accepted separator. Mechanism description wrong; behaviour unaffected. |
| scipy needed for "lfitci, qfitci, **kdensity** and mspline" | 1182-1183; `dash_setup.sthlp:76-77` | **2 of 4 wrong.** `qfitci` uses `np.polyfit` + a hand-written `_t_ppf` (`:6373-6400`, docstring says "WITHOUT scipy"); `kdensity` uses the hand-rolled `_KERNELS` table (`:6592-6600`). |
| `xtick()`/`ytick()` = "tick positions **without labels**" | 866-869 | **Inert when combined, wrong when alone.** `dash_render.py:9906-9913` does `spec = self._parse_axis_spec(raw_ax or raw_tick)` — `xtick()` is discarded whenever `xlabel()` is also given (the normal Stata idiom), and alone it produces *labelled* ticks. No `MinorTicker` is touched anywhere. |
| `colorvar()` — "a **plot layer** may take its colour from a third variable" | 926-948 | Scatter family only. `_apply_colorvar` (`:2995`) has one call site, `map_scatter:3480`. Silently dropped on bar, area, spike, dropline, rarea, rbar, pcscatter, rscatter, histogram — and it is not on the pending list, so nothing tells the user. |
| `legend(top\|bottom\|left\|right)` | 853 | Honoured but with wrong geometry — mapped to `leg.location="top_center"` etc. (`:10139-10157`), i.e. *inside* the plot. Stata places these outside. `_move_legend` (`:9193`) exists and is used for `position(#)` but not the bare keywords. |
| `ylabel2()`/`xlabel2()` | 905-912 | Plain numlists only. `#5`, `10(5)40`, `minmax`, `none`, `format()`, `labsize()`, `grid` all yield **zero ticks, silently** — it uses the bare `_parse_axis_label_opt` (`:9393`), which keeps only `float()`-able tokens, not `_parse_axis_spec` (`:9304`). |

**Closed by WP-23** (23sep2026), each row measured again at `4ede074`:
fractional percentiles are read by dash.ado as any p strictly between 0
and 100 and give Stata's `_pctile` value in both modes (and both renderers'
percentile rule, which disagreed with Stata at large n, is Stata's); `nodraw`
on a registered graph keeps `dash build`'s window shut, as does
`$dash_nobrowser` (already true, now pinned); filter groups are joined with
`||`, a label may hold any character, and the reader is quote- and
paren-aware in both languages; no layer imports scipy or statsmodels
(tested with both unimportable); `xtick()`/`ytick()` -- recorded above as
fixed by WP-14/15, which they were not -- draw ticks without labels beside
the labels, and `grid` as twoway draws it; `colorvar()` is drawn on
scatter, connected, rconnected and dot and named in the note elsewhere;
`legend(top|bottom|left|right)` is refused as twoway refuses it; and
`ylabel2()`/`xlabel2()` take `ylabel()`'s grammar.  The whole help was
audited with them: test/test_help_claims_1.py to _8.py and .cscript, and
test/test_help_examples.cscript.

### F5. Every documented example runs as the help says — S3, CLOSED by WP-23

All numbered examples in `dash.sthlp:613-1000` were executed through the real
`syntax` declarations: **all `rc=0`, empty `_pending`, empty `_unknown`** —
including `xtitle(Weight (lbs))`, `note(Source: 1978 Automobile Data)`,
`xlabel(#8, grid) ylabel(10(5)40, format(%9.0f))`,
`legend(order(1 2) cols(2) size(small) label(1 "A"))` and the two-`filter()`
form. The negative examples behave as documented. `dash kpi` values match
`summarize, detail` exactly (p25 = 4195, skewness = 1.6534335,
mean if foreign==1 = 24.772727), confirming the Hyndman-Fan type 2
percentile claim at `:467-471`.

That was a one-time check of parsing, and it was not enough: run as a
user runs them, one after another, the examples at `4ede074` held an
`lpoly` example that drew one point of its curve (a bandwidth written as a
fraction) and exposed a weight left behind in `s()` by a refused command
that the next command used; three `dash build` examples needed graphs no
earlier line registered, one needed variables no shipped dataset has, and
the help rendered as raw SMCL from the Faceting example to its end.
**Closed by WP-23**: test/test_help_examples.cscript reads every example
out of the help at run time and runs each group from a fresh session,
holding it to the return code and output the help shows, and renders both
help files, holding them to no SMCL left as text; test/test_help_examples.py
pins the reader.

---

## G. Schemes

### G1. Twelve of Stata's 26 schemes are not translated — S3, CLOSED by WP-17

Shipped (14): `economist s1color s1mono s1rcolor s2color s2gcolor s2mono sj
stcolor stcolor_alt stgcolor stmono1 stmono2 stsj`.

Missing and user-selectable: **`s2manual`, `s1manual`, `s2gmanual`,
`s2color8`, `sttrans`, `stgcolor_alt`**. The rest (`meta`, `stcolor_meta`,
`stgcolor_meta`, `stcolor_mv`, `stgcolor_mv`, `stcoloralias`) are internal.

`dash` can also reach **none** of the 129 third-party `scheme-*.scheme` files
installed on this machine — see F4's bare-name row and §G5.

**Closed by WP-17.** Shipped (20): the fourteen above plus `s2manual`,
`s1manual`, `s2gmanual`, `s2color8`, `sttrans` and `stgcolor_alt`,
extracted by the same `scripts/extract_scheme_truth.py` from Stata's own
files (s2manual and s2gmanual `#include s2mono`, s1manual `#include s1mono`,
s2color8 and sttrans `#include s2color`, stgcolor_alt `#include
stcolor_alt`) and created by the same writer as the fourteen, which were
re-run and reported no changed value. Measured first, 22sep2026 at
`0112221`: s2mono and s2gmanual are the only two StataCorp schemes that
declare a `lineplot` directive at all (s2mono `color plineplot` and fifteen
`linepattern p#lineplot`; s2gmanual fifteen `color p#lineplot` and fifteen
`linepattern p#lineplot`), so s2gmanual is the one scheme whose
`p_lineplot_colors` must come from a declared directive rather than the
`p#stub` fallback, and `test_scheme_fidelity.py` anchors that through the
fixture's `lineplot_declared` and `sources`. The six internal schemes
(`meta`, `stcolor_meta`, `stgcolor_meta`, `stcolor_mv`, `stgcolor_mv`,
`stcoloralias`) stay out, by design: none is user-selectable. The 129
third-party files in `PLUS/s` stay unread, also by design (WP-05's
containment: the letter directories are shared); the help now says so and
says to copy the file into the working directory, where G8's closure makes
the bare name work. `EXPECTED_SCHEMES`, `_BUILTIN_NAMES`, the extractor's
`SCHEMES` and the Stata-side list in `_dash_shipped_schemes` are pinned
equal by `test/test_scheme_resolution.py`. One thing the six files brought
with them: sttrans declares every `color p#` with a `%20` opacity suffix
(Paul Tol's muted palette at 20% opacity), which the extractor at `0112221`
stripped into its `unresolved` list and did not fold into the hex; the
shipped `sttrans.scheme` now keeps it (`color p1 #1a476f%20`), the fixture
records it in `p_colors_opacity` and its twins, and the renderer carries it
into the glyphs in both modes (a declared colour opacity wins over the
intensity approximation; a user's `mcolor(x%NN)` still wins).

### G2. The translations are exact, but they are not Stata scheme files — S3, CLOSED by WP-17

Flattening every Stata `#include` chain and resolving every colour name
through `style/color-*.style` gives **0 mismatches across all 14 schemes**, on
every directive Stata's chain declares. s2color's `p1`–`p15`
(`navy`→`#1a476f` … `bluishgray`→`#d9e6eb`) match byte-for-byte.

But Stata's `scheme-s2color.scheme` has **2060** directives; dash's has
**118**. The ~1940 absent ones cover bar/box/pie/dot/matrix styling, margins,
tick geometry, `draw_minor_*`, `alignstroke`, and the `linestyle`/`textboxstyle`
stubs. They are also flattened (no `#include`), so they are **not drop-in
Stata scheme files**. Per scheme, 46–76 keys are dash's own inference rather
than transcription (`color p#line`, `color p#bar`, `color p#mark`, `symbol p#`,
`linepattern p#line`, `intensity area`) — defensible and traceable through
`test/fixtures/scheme_truth.json`'s `sources` map, but the provenance does not
survive into the shipped files.

**Closed by WP-17.** The exactness was never in question; the gap was that
the provenance lived in one fixture and the help did not say what the files
were. Measured first, 22sep2026 at `0112221`: dash's `s2color.scheme`
carried 136 directives (118 at `187a786`; WP-16 added the eighteen textbox,
minor-grid, axis-line and legend-rows keys), 135 to 166 across the fourteen
files (the s2mono family's lineplot cycles are the difference), against
Stata's 2060; every `color` line in every file `#rrggbb`; no `#include`
directive in any file; and the `sources` map in
`test/fixtures/scheme_truth.json` the only record of which of those
directives were transcribed and which inferred. Now every shipped file
carries a `* provenance:` block, one line per directive, `transcribed from
scheme-X.scheme:<directive>` or `inferred: <rule>` (the `p#line`, `p#bar`,
`p#mark`, `symbol p#`, `linepattern p#line` and `intensity area` rules),
written by the same writer that creates and updates the files, so a re-run
is a no-op and the provenance survives into the tree a user installs; and
`dash.sthlp` says what the files are: dash-format translations of about
135 directives with the `#include` chain flattened and every colour
resolved to hex (sttrans's with its declared `%20` opacity kept as
`#rrggbb%20`), carrying their provenance, not drop-in Stata scheme files
and never read by `graph`. What the absent directives cover (bar, box, pie,
dot and matrix styling, margins, tick geometry, the `linestyle` and
`textboxstyle` stubs) is unchanged: dash draws none of it.

### G3. Every dashboard draws a dark grid Stata never draws — S1, CLOSED by WP-16

`dash_render.py:2185` sets the minor grid unconditionally:

```python
grid.minor_grid_line_color = self.minor_grid_color
```

Bokeh's `BasicTicker.num_minor_ticks == 5` and `minor_grid_line_alpha == 1.0`,
so these lines render. Measured on real figures:

| scheme | major x | major y | **minor x** | **minor y** |
|---|---|---|---|---|
| s2color | none | `#eaf2f3` | **`#505050`** | **`#505050`** |
| s1color | none | none | **`#505050`** | **`#505050`** |
| stmono1 | none | none | **`#505050`** | **`#505050`** |
| economist | none | `#ffffff` | `#ffffff` | `#ffffff` |

Stata's own s2color declares `draw_minor_grid no`, `draw_minor_hgrid no`,
`draw_minor_vgrid no`. dash's translated file carries no `draw_minor_*` key at
all. So schemes that draw **no grid whatsoever** get a dark grid on both axes.

**Closed by WP-16.** Measured first, 22sep2026, on real figures for all 14
schemes in both modes: `minor_grid_line_color` set on both axes everywhere
(`#505050` in twelve, `#808080` s1rcolor, `#ffffff` economist) at Bokeh's
`minor_grid_line_alpha` 1.0, so every dashboard drew it. The major grid was
already right at that baseline -- per axis from `draw_major_hgrid` and
`draw_major_vgrid`, none under s1color, s1mono, s1rcolor and stmono1 -- so
the minor grid was the whole of this gap. Stata's truth, read from the style
files: `draw_minor_hgrid no` and `draw_minor_vgrid no` in every chain,
economist's y axis through its `vertical_nolinetick` axis style and
`draw_minor_nlt_vgrid no`; the bare `draw_minor_grid` key is read by no
style file. Now `scripts/extract_scheme_truth.py` records the effective
per-axis minor flags, the fourteen shipped files carry them, `SchemeParser`
parses `draw_minor_hgrid`/`draw_minor_vgrid` (default no, with
`_FALLBACK_PROPS` entries), and `apply_to_figure` colours a minor grid only
where the axis's flag is yes, else `None`, at `linewidth minor_grid`; the
served app runs that same method in place of its hand-copied body. After:
minor `None` on both axes under all 14 schemes in both modes, and major
`None` too under the four no-grid schemes, pinned for every scheme and mode
by `test_scheme_rendered_output.py`. The adversarial review of the package
(22sep2026) added one guard on the same path: a negative `linewidth` in a
user scheme (`linewidth major_grid -4` drew a zero-width, invisible grid in
silence) is refused with the `dash scheme:` warning and the default used,
pinned by `test_scheme_review_fixes.py`. The line reference in the body
above was measured at `187a786`; at the WP-16 baseline (`52c473c`) the
assignment was at `dash_render.py:2365` and its served copy at `:14617`.

### G4. Parsed scheme attributes with no consumer — S2, CLOSED by WP-16

Confirmed by reference count (a count of 1 means the assignment and nothing
else):

| Directive | Parsed at | Status |
|---|---|---|
| `gsize note` → `note_font_size` | `:2047` | **Fully dead.** Note/caption sizes hardcoded 11.0/12.0 px at `:9866-9868`. |
| `color p#mark` → `p_mark_colors` | `:1980-1982` | **Fully dead.** `default_color()` (`:2103-2112`) never indexes it. Invisible today only because `p_mark_colors == p_colors` in all 14 shipped schemes; a user scheme declaring it gets nothing. |
| `clockdir legend_position` | `:2086-2087` | **Dead in both modes.** Standalone has no consumer; the server sets `lg.location = 6` (`:12661-12662`), and Bokeh 3.9 raises `ValueError` on a numeric `Legend.location`. All 14 schemes declare a numeric clock position. |
| `numstyle legend_cols` | `:2088` | **Dead in both modes** — it sits *after* the failing assignment **inside the same `try:`** (`:12655-12666`), so the `ValueError` skips it too. |
| `color heading` / `gsize heading` | `:1965, 2044` | Reach only the dashboard CSS (`.db-title`), never a Bokeh figure title. Measured: `fig.title.text_color == '#444444'` and `text_font_size == '13px'` under s2color, s2mono, stmono1 and economist alike — all Bokeh defaults. |
| `graphsize x/y` | `:2054-2055` | Ratio only (`:9244-9245`); absolute size never used. |

Parser branches no shipped scheme exercises (dead code, not a rendering gap):
`color plineplot`, `linepattern plineplot`, `linepattern p`, `linepattern
p1`–`p15`, bare `graphsize`, and `#include` support (`:1786-1800`) — **zero**
of the 14 files contain an `#include`, whereas 25 of Stata's 26 do.

**Closed by WP-16.** Measured first, 22sep2026, all 14 schemes, both modes:
`fig.title` Bokeh's `#444444`/`13px` everywhere; the subtitle, note and
caption Labels 13px `#444444`, 11px `#555555` and 12px `#555555` dash
literals everywhere; axis titles and tick labels `#444444` everywhere, dark
grey on black under s1rcolor; the legend `top_right`, vertical, `ncols`
auto everywhere, while the schemes say 6 o'clock in 2 columns (nine
schemes), 3 o'clock in 1 (stcolor, stgcolor, stmono1, stmono2) or 12
o'clock in 3 (economist); `p_mark_colors` read by nothing. Two rows of the
table above were stale by then: the served legend already went through the
shared `_dash_apply_legend`, so the `lg.location = 6` `ValueError` no
longer existed and `legend_position`/`legend_cols` were simply unread in
both modes; and the served app already built a real `SchemeParser` from
`_SCHEME_PROPS`, so the glyph cycles were in parity. One row was wrong
about Stata: `gsize note` exists in every scheme, but Stata's note textbox
is `small_body` (its title is `heading`, subtitle `subheading`, caption
`body`, legend entries `key_label`, axis titles `axis_title`, tick labels
`tick_label`), so `note_font_size` read a key Stata does not read either.
Now each element takes the size and colour of the textbox style that draws
it in Stata: `apply_to_figure` sets the figure title from `color
heading`/`gsize heading` and the axis-title and tick-label colours from
`color axis_title`/`color tick_label`, an explicit `title(, size() color())`
still running after it; `_dash_text_annotations` takes the scheme, subtitle
at subheading, note at small_body in its own colour, caption at body; one
`_dash_scheme_chrome(scheme)` builds the legend chrome for both modes with
`key_label` text, and `_dash_apply_legend` places the legend from `clockdir
legend_position` and `numstyle legend_cols`/`legend_rows` when no
`position()`, `ring()` or keyword was given (6 below and horizontal in the
scheme's columns, 12 above, 3 right, 9 left; `cols()`/`rows()` win);
`default_color` reads `p_mark_colors` for the marker types; the unread
served constants are gone. `note_font_size` stays parsed for the fidelity
check and is read for nothing, by design; `graphsize x/y` stays ratio-only,
as the figure-proportions help documents. After: under s1rcolor every text
is white; economist's title 17.28pt over an 11pt subtitle; s2color's legend
below in two columns, stcolor's right in one, economist's above in three;
pinned in both modes by `test_scheme_rendered_output.py`. The adversarial
review of the package (22sep2026) found four more consumers to put right on
this gap, closed in the same package: the scheme-placed legend was the
outermost item on its side and right-aligned (Stata's `legend_ring 3` is
nearest the plot, and a 6 or 12 o'clock legend is centred) and a user
`legend(rows(1))` inherited the scheme's `ncols` -- now inserted after the panel's axis, before every Label
of the panel, `location` center, and `rows()` alone sets `ncols` auto
(`cols()` alone `nrows` auto); `color p#mark` had reached the Segments of
the spike family and the line halves of dropline and rcapsym through the
"scatter" alias -- now marker glyphs only; `linewidth axisline` was
extracted and carried but read by nothing -- now `axis_line_width` on each
axis; and a hostile `clockdir legend_position 99` or `numstyle legend_rows
1000` passed in silence -- now range-checked with the colour path's
warning. `color foreground` joins `note_font_size` as a directive carried
and read for nothing, by design. Pinned in both modes by
`test_scheme_review_fixes.py`. The line
references above were measured at `187a786`; at `52c473c` the parser rows
were at `dash_render.py:2145-2268`, `default_color` at `:2274` and the
textbox literals at `:10018`.

### G5. Numeric scale factors are wrong — S2, CLOSED by WP-16

- **`gsize`**: `dash_render.py:1846-1849` computes `int(val * 1.2)`. Stata's
  relative-size unit is fixed — `gsize-medium.style` = `3.8194` = 11 pt on a
  4-inch graph; `gsize-large.style` = `4.8611` = 14 pt. The factor is **2.880**.
  `economist` declares `gsize heading 6.0` → Stata means **≈17 pt**; dash
  produces **7 pt**. Measured: economist's dashboard title renders *smaller*
  than its 11 pt subtitle.
- **`linewidth`**: `:1899-1911` takes the number as pixels. Stata
  `linewidth medium` = `.30`; economist declares `linewidth p 1.2`, i.e. 4×
  medium. Measured `default_line_width`: s2color/s2mono/stcolor = **1.5**,
  economist = **1.2** — economist's deliberately heavy lines render *thinner*
  than every other scheme's.

**Closed by WP-16.** The factor was verified against the style files,
22sep2026: every `gsize-*`, `symbolsize-*` and `linewidth-*` style sets
`sztype relative`, `size.sthlp` defines 100 as the graph's smaller
dimension, and the measured `test/fixtures/scheme_visual/truth.json`
(stcolor's title 15.74pt = 4.859% of a 4.5-inch height) confirms it, so one
unit is 2.88pt on the four-inch reference and `gsize heading 6.0` is
17.28pt. Measured before: economist's title 7pt under an 11pt subtitle in
both modes; economist's `linewidth p 1.2` at 1.2px against 1.5px for every
other scheme's medium; `_GSIZE_PT` had minuscule 2pt (Stata 1pt) and vhuge
24pt (Stata 28pt); symbolsize keywords were scaled through the text ladder,
so `large` markers were 10.18px where Stata's symbolsize ratio (7pt over
medium's 4.4pt) gives 12.73px, and stcolor's `small` 5.82px where it gives
5.45px. Now `_gsize` numeric is `val * 2.88` pt, no floor, no truncation;
the two table entries are corrected; `_lwidth` numeric is Stata's unit at
`val * 5.0` px (medium .30 stays 1.5px, economist 6.0px); a
`_SYMBOLSIZE_PT` ladder from the `symbolsize-*.style` files, anchored at
medium 4.4pt = 8px, sizes the markers; the fixture's `_meta.units` records
the three ladders and the formula. Not changed, a follow-up: the linewidth
keyword ladder `_LWIDTH_MAP` (thin .8px to vvthick 5.0px) keeps ratios that
are not Stata's (Stata's thin is 0.667 of medium, vthick 4.667). After:
economist's title 17.28pt over 11pt, its line 6.0 over s2color's 1.5,
markers 5.45px (stcolor), 8px (s2color), 12.73px (economist), in both
modes. The adversarial review of the package (22sep2026) found that the
numeric branch's `%g` formatting turned `gsize body 0.00001` into
`2.88e-05pt`, which Bokeh's FontSize validator rejects, aborting the whole
figure where the old floor had drawn 6pt; `_gsize` now formats fixed
decimals and a point size outside (0, 1000] falls back to the default with
the `dash scheme:` warning, pinned by `test_scheme_review_fixes.py`.

### G6. Inline styles defeat the scheme on KPI cards — S2, CLOSED by WP-16

`css_block()` (`:2214-2215`) emits `.db-kpi-card { background-color: …;
border-color: …; }`, but the Div is written with an inline
`style="background:…; border:1px solid #dee2e6;"` (`:10484-10495`). Inline
shorthand wins, so `color legend` / `color legend_line` never reach a card.
Verified under `economist`: scheme wants `#c6d3df`, card renders `#f8f9fa`
with a `#dee2e6` border. Same in the server path (`:12977-12982`).

Similarly `:9188` hardcodes `g.grid_line_color = "#e5e5e5"` when
`xlabel(, grid)` turns on a grid the scheme left off, ignoring the scheme's
`color major_grid`.

**Closed by WP-16.** Measured first, 22sep2026, all 14 schemes, both modes:
every card `background:#f8f9fa; ... border:1px solid #dee2e6` inline (a
light card on s1rcolor's black page; `#f8f9fa` where economist's legend box
is `#c6d3df`), and the `.db-kpi-card` rule reached no card Div at all,
because a Bokeh 3 Div renders in a shadow root and only the header Divs
carried `css_block()` as an `InlineStyleSheet`; the whitespace of that Div
was the only place the two modes disagreed. `xlabel(, grid)` drew `#e5e5e5`
on the ten schemes whose x grid is off (`#e0e0e0` wanted under s1color,
`#ffffff` economist, `#505050` s1rcolor, `#eaf2f3` s2color, `#e8e8e8`
s2mono). Now one module-level `_dash_kpi_card_html(...)` writes the card for
`_make_kpi_div`, the served `_dash_kpi_card` and the JS filter rebuild
alike: class `db-kpi-card`, layout-only inline properties, no inline
background or border unless `bgcolor()` was given (then inline, and it
wins), value colour `color()` or the scheme's `color text`, title and
subtitle `color text`; every card Div carries
`stylesheets=[InlineStyleSheet(scheme.css_block())]` and the rule is
`background-color: <color legend>; border: 1px solid <color legend_line>;
color: <color text>`. `_dash_apply_axis_options` takes the scheme's grid
colour for the `grid` branch. After: economist's card `#c6d3df`, s1rcolor's
black with white text, `bgcolor(#ecf0f1)` still inline, `xlabel(, grid)`
under s1color `#e0e0e0`; both modes, pinned by
`test_scheme_rendered_output.py`. The adversarial review of the package
(22sep2026) found the seven `#212529` pins in `test_kpi_security.py` that
no owner had restated (7 failed, 25 passed against the tree; restated to
the scheme's `color text`), one byte the JS rebuild still got wrong (the
value div's `id="kpi_val_<name>"`, pre-existing, now emitted from the
config), and, pre-existing and outside this gap, that every `layout(bs)`
page carrying a KPI or a filter widget was blank, because
`_render_bootstrap_html`'s non-greedy head scrape stopped at the literal
`<head></head>` inside Bokeh 3.9's inlined widgets bundle -- so the card's
stylesheet reached the bs page only at the JSON level until the head was
taken up to the last `</head>`; each in `BUGS.md` and pinned by
`test_scheme_review_fixes.py`. The line references above were measured
at `187a786`; at `52c473c` the card markup was at `dash_render.py:12362-12369`
(served `:14910-14917`, JS `:8163-8168`) and the grid literal at `:9379`.

### G7. What works — no gap

Scheme-then-option precedence is correct throughout: `apply_to_figure`
(`:9606`) runs before `_apply_marker_opts` (`:3478`), so explicit options win.
Measured: s2color two scatters → `#1a476f`/`#90353b`, circle, 8.0px;
`mcolor(red) msymbol(triangle) msize(large)` → `#ff0000`, triangle, 15px;
s2mono symbol cycle circle/diamond; s2mono line `p#lineplot` split with
dashes `[]`/`[8,4]`; stmono1 `symbolsize p small` → 5.82px; `lcolor(green)
lwidth(thick) lpattern(dash)` → `#008000`, 2.5, `[8,4]`. Grid orientation
(`draw_major_hgrid`→`xgrid`, `draw_major_vgrid`→`ygrid`) is correct.

Path traversal is **properly contained** — `_resolve_path` (`:1718-1752`)
validates both `abspath` and `realpath` against `{CWD, schemes dirs}`.
Measured: `../../../../etc/hosts.scheme` → `ValueError`; a symlink to
`/etc/passwd` → `ValueError`; an absolute path into Stata's own scheme
directory → `ValueError`.

### G8. `scheme()` warns and falls back where it could error — S3, CLOSED by WP-17

`dash.ado` performs **no** validation of `scheme()`; it is escaped and passed
through verbatim (`:2341-2343`). All policy is Python-side, and it is
warn-and-fall-back, never error (`:7967-7983`, `:1589-1622`). A typo in
`scheme()` therefore produces a dashboard in the wrong scheme with a warning
buried in the log rather than a refusal.

**Closed by WP-17.** Measured first, 22sep2026 at `0112221`, with the
console binary, a `mytheme.scheme` in the working directory that is a copy
of s1rcolor (black background, white heading) and the session scheme read
back from `c(scheme)`:

| entry point | value | at `0112221` |
|---|---|---|
| `dash scatter ..., scheme(mytheme)` (immediate) | bare name, file in the CWD | rc 0; `dash: 'mytheme' is not a known theme or scheme; using s2color`; the figure drawn with mytheme (`background_fill_color` `#000000`) under s2color page chrome (`.db-title { color: #1e2d53 }`, `#eaf2f3`): half applied |
| `dash scatter ..., scheme(mytheme.scheme)` | file name | works throughout (`.db-title { color: #ffffff }`, no s2color colour on the page) |
| `dash build, scheme(mytheme)` | bare name | rc 0, the warning, s2color throughout |
| `dash build, scheme(mytheme.scheme)` | file name | works |
| graph registered with `scheme(mytheme)`, then `dash build` | bare name | half applied, as the immediate route |
| `scheme(nosuchthing)` / `theme(nosuchtheme)`, either entry point | a typo | rc 0, the warning, s2color; two warnings on the immediate route (the gate's and the per-graph swap's), each a raw Python block naming `dash_render.py` and a line |
| `scheme(d3colors)` | one of 129 third-party `scheme-*.scheme` files in `PLUS/s` | rc 0, the warning, s2color: dash reads its own translations and the working directory only, by design (WP-05) |
| `set scheme s2color8`, then any unschemed dash | inherited `c(scheme)` | rc 0, `'s2color8' is not a known theme or scheme; using s2color`; `cscript` sets s2color8 for every session (`c(scheme_cscript)`, cscript.ado:35), so the runner's log of the WP-16 verification run carried the line 49 times across 13 of the 41 scripts |
| `set scheme d3colors`, then any unschemed dash | inherited third-party | the same line with that name |

`twoway scatter mpg weight, scheme(nosuchthing)` is rc 0 with `(note:
scheme nosuchthing not found, using s2color)`, `set scheme nosuchthing` is
r(111), and `twoway ..., scheme(s2color8)` draws it: dash had copied
twoway's note for the explicit case where a saved dashboard wants `set
scheme`'s refusal. The cause of the half application: `_resolve_scheme_name`
(`dash_render.py:8941`; the branch at `:9018-9029`) rejected any name that
was neither a theme alias nor one of the fourteen `_BUILTIN_NAMES`
(`:1624-1631`) unless it ended in `.scheme`, blanking it and warning,
before `SchemeParser._resolve_path` (`:1910`, whose bare-name branch at
`:1930-1931` tries `<cwd>/<name>.scheme` first and was added for exactly
this route) could run; the per-graph swap in `_make_figure` (`:12317-12325`)
calls `resolve_or_fallback` directly and did find the file, so the figure
had the scheme the page had already lost. Now one rule on every entry point
(BR-17.1, BR-17.2): a scheme is named by one of the twenty shipped
translations, a theme alias, or a `.scheme` file in the working directory
given by bare name or with the extension. An explicitly requested name that
resolves to none of those is refused in Stata before any Python runs,
through WP-15's table -- a `scheme` kind that accepts a shipped name or a
theme (with or without the `.scheme` extension: `scheme(s2color.scheme)`
needs no file in the working directory), or a name with no `/`, `\` or
`..` that `confirm file` finds in the working directory as written or with
`.scheme` appended, else `P: scheme()
must be a shipped scheme, a theme, or a .scheme file in the working
directory (got: V)`, r(198); `theme()` an `enum` of its six names, `dash
build: theme() must be one of clean, dark, default, economist, mono, sj
(got: V)`; the graph rule token `scheme=scheme` covering the immediate
route, a registered graph and a per-segment `scheme()`, and
`_dash_prepare_spec` covering `dash build` and `dash serve` before anything
is written. The Python gate asks the new `SchemeParser.can_resolve` before
it warns, so a resolvable name passes untouched and the page chrome and the
figure come from the same file in both modes; it stays as the second line
of defence for a spec built without `dash.ado`. The inherited `c(scheme)`
stays warn-and-fall-back, never fatal, one line that now says the name was
inherited from the session because no `scheme()` or `theme()` was given.
Pinned by `test/test_scheme_resolution.py` (both modes) and certified by
`test/test_custom_scheme.cscript` CS-01 to CS-13; `test_theme_escaping.cscript`
THM-01 to THM-06 restated to r(198) at the gate. F4's bare-name row and
WP-05's AC-05.3 close with this. The line references in the body above were
measured at `187a786`; at `0112221` the pass-through was at
`dash.ado:3357-3369`, `_dash_validate_value` at `:1257`, and the gate at
`dash_render.py:9018-9029`.

---

## H. The interactive layer

### H1. There is no export of any kind — S2, CLOSED by WP-21

Zero occurrences of `SaveTool`, `download`, `export` or `to_csv` in
`dash_render.py`. Both toolbars are fixed:

- standalone `"pan,wheel_zoom,box_select,lasso_select,reset"` (`:9552`)
- server `[PanTool, WheelZoomTool, BoxSelectTool, LassoSelectTool, ResetTool]`
  (`:13801, 15127, 15230`)

No PNG save, no CSV download, no `BoxZoomTool`, no `UndoTool`/`RedoTool`, no
`CrosshairTool`. For a product whose output is a dashboard someone will want
to put in a paper or a deck, this is the most conspicuous single omission.

**Closed by WP-21.**  Every figure, in both modes, carries pan, wheel zoom,
box zoom, box select, lasso select, undo, redo, reset and save -- no
crosshair, which a shared toolbar would draw across every figure -- and each
served figure owns its tools (they were one shared set).  A grid's save
button writes the whole grid as `dashboard.png`; under `layout(bs)` each
item saves under its own name.  `dash build, csv` adds a Download CSV
button: the rows the filters leave, every variable the dashboard uses, as
`dashboard.csv` -- written in both modes by ONE JavaScript formatter, so the
two files are identical (tested under node, and in Chromium).  Opt-in,
because a served dashboard otherwise sends the browser only what it plots.
Text a spreadsheet would run as a formula is defused; dates are ISO 8601;
UTF-8 with a BOM, which Excel needs and Stata's `import delimited` reads.
Tests: `test_toolbar.py`, `test_export.py`, `test_export.cscript`.

### H2. What is built — no gap

Linking/shared source (`:11300-11460`), brushing→KPI (`:11645`, server
`:15664-15732`), non-selection dimming (`:9438`, α = 0.15), cross-filter
widgets (dropdown/slider/range, `FilterBuilder:7557-7890`, 33 `CustomJS`
callbacks; server via `on_change` `:15477-15662`), tabs (`:10914, 11013`;
server `:15746-15809`, both validating names against the registry), KPI tiles
with 11 statistics and `update(filter|brush|both)`, Bootstrap 12-column and
plain-grid layouts, responsive `sizing_mode` and viewport meta.

The live-recompute-versus-JS-rescale difference between modes is real,
documented in the help's comparison table, and explicitly allowed by the
parity test.

### H3. Bootstrap layout in server mode is unverified — SUSPECTED, CLOSED by WP-21

`_render_bootstrap_html` is standalone-only. What `layout(bs…)` does when
served needs a runtime check.

**Closed by WP-21.**  Measured at `ed41e8a`: the served app read a `bs`
layout with the placement parser, found nothing, and drew the automatic
grid without a word.  It now draws the saved page's rows and spans on a
12-column `GridBox`, from the one reader both modes share, without the
saved page's reflow at narrow widths (dash.sthlp says so).  Tests:
`test_served_bs_layout.py`, and `test_mode_parity.py`'s `layout(bs)` entry,
which had been skipped.

---

## I. Resource limits and security

### I1. The bounded quantities — no gap

`_MAX_BINS = 1000` (`:4725, 4767`), `_MAX_MBANDS = 1000` (`:2313`),
`_MAX_EXPR_CHARS = 5000` (`:2271`), function points capped at 10 000
(`:10056, 14824`), `_WEBGL_THRESHOLD = 10_000` (`:569`), port clamped to
`[1024, 65535]` (`:16153`).

The generated server app has a genuine per-IP sliding-window rate limiter
(`_RATE_LIMIT_RPM = 60`, `_HEALTH_LIMIT_RPM = 600`), separate buckets for
sessions and health checks, an LRU `_MAX_IPS = 10000` eviction, and a
`/health` endpoint returning 200/429 — satisfying CLAUDE.md rules 3 and 17.
It binds loopback by default.  *(WP-19: the LRU eviction was the defect I2
records, and is gone; the limiter now has three bounds -- per client, new
clients, all sessions -- and never evicts a live key.  See I2.)*

### I2. The unbounded ones — S2, CLOSED by WP-19

No constant exists for any of these — grep for
`_MAX_FILTER_OPTIONS`, `_MAX_DROPDOWN`, `_MAX_BY_GROUPS`, `_MAX_FACETS`,
`_MAX_TABS`, `_MAX_OBS`, `_MAX_ROWS`, `_MAX_GRAPHS`, `_MAX_PLOTS` returns
**0 hits each**:

- **Dropdown filters emit one `<option>` per distinct value, uncapped.**
  `build_dropdown` (`:7628-7660`) takes `set(source.data[varname])` with no
  ceiling and no warning — 200 001 options on 200 000 observations.
- **`by()` has no group cap.** `by(id)` builds one figure per value.
- **No row, column, graph or facet cap.** `_report_dataset_size`
  (`:538-567`) *warns* — its own docstring records 2 M rows → 90.6 MB of HTML
  at 1.71 GB RSS — but never refuses or truncates.
- **`_MAX_IPS` is an eviction primitive, not a limiter.** A client cycling
  10 000 forwarded keys took 300 sessions inside a 60-second window against a
  nominal 60.

**Closed by WP-19.** Remeasured first, 23sep2026 at `f1321c6`: a dropdown on
200,000 distinct values was 200,001 options, a 38.8 MB page and a 14.8 MB
served app; `by()` on 1,000 groups drew 1,000 figures in 29.2 s; 300 graphs
took 7.9 s and 3,000 tabs 14.4 s; 4,000,000 cells made a 94.9 MB page at
2.1 GB RSS with rc 0; and the forged-key cycle, with the header trusted, got
10,120 sessions in 60 s (the 300 above predates the peer-address default),
flushing the real client's own key.  Each quantity is now a limit with a
default, a hard ceiling and a global macro that moves it for the session --
`dash_max_cells` (5,000,000; at most 20,000,000), `dash_max_graphs` and
`dash_max_plots` (100; 1,000), `dash_max_filter_options` (1,000; 100,000),
`dash_max_by_groups` (100; 1,000), `dash_max_tabs` (50; 500),
`dash_max_filters` (20; 200) -- held in one table in each language, which a
test keeps equal.  dash.ado refuses cells (before the export), graphs and
plots with r(134); the renderer clamps the rest in both render modes, and
every clamp names its limit and the global.  A numeric or date dropdown
over the limit becomes `type(range)`; a string one lists its first values.
The limiter's eviction is replaced by three bounds and a swept store that
never evicts a live key: the same attack now gets 59 sessions, the real
client its 60.  Help: `dash.sthlp`, "Resource limits" and "Server Mode".
Tests: `test_resource_limits.py`, `test_server_rate_limit.py`,
`test_served_throttle.py`, `test_resource_limits.cscript`,
`test_adversarial.cscript` P19.

### I3. Escaping — mostly solid — S3, CLOSED by WP-20

`html.escape` is applied at 20 sites (KPI title/value/subtitle, dashboard
title/subtitle, facet labels, tick-label maps, legend overrides, scheme CSS,
filter widget values with `quote=True`). Colours go further —
`_sanitize_css_color` (`:7013`) and `_resolve_kpi_color` (`:6970`) exist
because `html.escape` does not neutralise `{`/`}`/`;` inside a `style=`
attribute.

`function` expression evaluation is a real AST whitelist
(`_stata_expr_to_python:6763` → `_validate` → `compile:6173` →
`eval(code, {"__builtins__": {}}, ns):6204`), with keyword args and `*args`
rejected and int literals coerced to float to stop `9^9^9^9`. `if`
expressions go through `_stata_if_to_pandas` (`:6852`) with string-literal
masking and validation.

Remaining:

- **CSP is standalone-only** and thin: `script-src 'unsafe-inline'
  'unsafe-eval'` with no `default-src`, `object-src`, `base-uri` or
  `frame-ancestors`.
- **Hover tooltip labels are not escaped** — `:10234` appends
  `self._axis_label(col)`, a user-controlled variable label, into `tooltips`.
  Bokeh 3.x builds tooltip rows as DOM text nodes so this is almost certainly
  safe, but the safety comes from BokehJS, not from dash. **SUSPECTED** —
  worth a version-pinned check.
- `dash_setup.ado:158` interpolates `` `pkgver' `` — unsanitised distribution
  metadata — into a `python:` line as `Version("`pkgver'")`.
  `_dash_pkg_version` guards the package *name* (`:307`) but not the returned
  version string. The only unvalidated interpolation into executable Python in
  the file.

**Closed by WP-20.** Measured first, 23sep2026 at `e932446`: the served app
answered `/` with no Content-Security-Policy and none of the other security
headers; the saved page's policy had no `default-src`, `object-src`,
`base-uri` or `form-action`, and the `layout(bs)` page placed it after the
inlined BokehJS, where it governed nothing BokehJS did.  The hover label
was safe -- a variable label `<img src=x onerror=...>` showed as text in the
axis title, the legend and the tooltip in both modes, with no `<img>` in the
document -- but a walk of every sink found three that were not: a slider or
range filter title holding a TeX pair is written with `innerHTML` after
`process_tex`, which copies the surrounding text raw; a Div's text goes
through MathJax, where `\href{javascript:...}` is a live link; and a
tooltip field `@{name}` is parsed as HTML after it is filled, so a column
name that closed the brace left markup behind.  `dash_setup`'s version gate
and scheme probe ran a crafted version string and a crafted renderer path as
Python, which created a marker file.

Now both pages carry a `default-src 'none'` policy ahead of every script and
style in `<head>` -- the first element of both saved pages', and after only
`<meta charset>` and `<title>` on the served page -- scripts and styles
inline only, images and fonts from `data:`,
`connect-src 'none'`, `object-src 'none'`, `base-uri 'none'`,
`form-action 'none'`; the served policy adds `'self'` and `connect-src
'self'` for the websocket -- and the served app's own launcher sends the
policy with `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY` and `Referrer-Policy: no-referrer` on every
response, `/health` included (`bokeh serve` sends none of them, and the help
says so).  Checked in Chromium: no violation, and the CustomJS filters, the
hover, the websocket and a server callback all still work.  Every sink a
label reaches is classified and pinned to the Bokeh version it was verified
on; slider-family titles have their TeX pairs broken, every Div dash writes
sets `disable_math`, a tooltip field is built only for a plain Stata name,
and the text sinks get the raw text.  `dash_setup` reads every value with
`sfi.Macro.getLocal`, and keeps a version only when it is made of version
characters.  The existing defences -- the function whitelist (whose literal
check let strings and `True` towers through, now closed), the qualifier
whitelist, scheme containment, the colour sanitiser, the filter-name check
and loopback binding -- are pinned in `test_security_surface.py`.  The
three-case adversarial matrix (AC-20.3) registers 24 input surfaces
(`test_adversarial_matrix.py`) and the gaps it exposed are fixed, each in
`BUGS.md`: every echo of the user's text drew it as SMCL (23 sites in
`dash.ado`, one of which ran it as display directives), `port()` and
`timeout()` took a trailing newline, a `layout()` backslash broke the spec,
`EXCLUDE()` skipped its check, a `layout()` grid of any size was built, and
the renderer could be made to recurse or allocate without bound by a scheme
`#include` chain, an `if` qualifier, an axis label, a format, a limit or a
function.  Tests: `test_csp.py`, `test_label_sinks.py`,
`test_security_surface.py`, `test_adversarial_matrix.py`,
`test_setup_injection.cscript`, `test_echo_text.cscript`,
`test_adversarial.cscript` P20.

**Since WP-30 (P1.29, commit 0e8fbaf).** script-src `'unsafe-inline'` is removed: hashes on the saved page, a per-page nonce on the served page, and a Chrome test of both modes. The `'unsafe-inline'` retained above no longer holds for scripts.

---

## J. `dash_setup` and environment verification

### J1. It reports failure and then declares success — S1, READ, CLOSED by WP-06

`dash_setup.ado:53-57` prints "Python … version X is below the minimum" — and
there is **no `exit`**. Execution continues, installs packages against the
too-old interpreter, and ends at `:199` with:

```
dash_setup complete. All dependencies are satisfied.
```

`exit` appears only at `:37, 141, 185, 190, 309` — never on this branch.

**RESOLVED (WP-06), and the branch was never even reached.** The fall-through
is real and is fixed by a failure accumulator plus `_dash_setup_summary`. But
measuring it turned up something worse: `_dash_pyver_ok` is correct when
called from a certification script and returned **1 for every input** when
called from `dash_setup`, which declares `version 16.0` — `return scalar`
followed by `exit` inside its `forvalues` took effect under neither, so every
comparison fell through to the closing `ok = 1`. Measured: `3.7.9 >= 3.8`
gave 1, `0.9 >= 1.5` gave 1. So this branch never ran at all and the user was
told "Python ............. OK (version 3.7.9)". The comparator now decides
once and returns after the loop, and `test_setup_python_gate.cscript` gained
seven cases that call it through a `version 16.0` program — the calling
context none of its fourteen existing cases covered, which is why it passed
throughout. See the BUGS.md entries.

### J2. Version minimums are declared but never enforced by pip — S2, READ, CLOSED by WP-06

Minimums are declared (`:106-110`) and compared with
`packaging.version.Version` (`:155-159`), but pip gets a **bare name, no
specifier** — `:123` is `pip install bokeh`, never `bokeh>=3.0`. A package
present but below minimum is warned about and **never upgraded**, and the
summary still claims all dependencies are satisfied.

Worse, if `packaging` itself failed to install, the `else` at `:169-171`
prints "OK (version unknown)" for *every* package, although
`_dash_pkg_version` already retrieved the real version. A below-minimum bokeh
is then reported as OK.

**RESOLVED (WP-06), partly, and one part corrected.** The bare pip name is
fixed: pip now receives `<pkg>>=<min>` built from the minimum declared beside
it. The "below minimum is never upgraded" half is deliberate rather than
fixed — an importable package below its minimum is now *reported as unmet*,
with the exact upgrade command printed, rather than upgraded behind the
user's back, because something else in their environment may depend on the
version they have. AC-06.2 accepts either. The `packaging`-unavailable
masking is fixed by `_dash_setup_gate` (see J6 and BUGS.md).

### J3. Python availability is probed by running Python — S2, MEASURED, CLOSED by WP-07

`c(python_exec)` appears **nowhere** in `dash.ado` or `dash_setup.ado`.
`dash_setup.ado:32` probes with `capture python query`, and package presence
with `capture python: import …` — i.e. by running Python, contrary to the
project convention. There is no `shell` invocation of Python anywhere (pip
runs via `subprocess` *inside* `python:`), so that half of the rule holds.

`test/test_cscript_hygiene.py:12-14` enforces the rule only for `.cscript`
files, so `dash_setup.ado` is outside the net.

**RESOLVED (WP-07).** `_dash_python_ok` takes the value as an argument and
`_dash_require_python` passes it `c(python_exec)`. Split that way because the
failing state cannot otherwise be reached on a machine that has Python: `c()`
is read-only and `set python_exec` refuses a nonexistent path (measured,
r(601)). `dash_setup`'s `capture python query` is replaced by the same probe;
`python query` is kept for *reporting* the version. `test_cscript_hygiene.py`
now applies its rule to `dash.ado` and `dash_setup.ado` — enforcing it for
`.cscript` files only is how `dash_setup` kept that probe.

### J4. `dash` itself never checks that Python is available — S2, READ, CLOSED by WP-07

`_dash_do_render` goes straight to `python:`. A user without a linked Python
gets a raw Stata Python error rather than the "run dash_setup" message the
`jsonio` check (`dash.ado:1683-1687`) gives for the other dependency.
CLAUDE.md rule 15 asks for environment verification at startup.

**Closed by WP-07** (a4e6522): `_dash_require_python` probes
`c(python_exec)` before every path that reaches `python:` and exits 198 with
a message naming `dash_setup`, modelled on the `jsonio` one.  Certified by
`test/test_env_guards.cscript` ENV-05 to ENV-07 (re-run 23sep2026 at
`4ede074`: passed).

### J5. The Mata library's compile status is never checked — S2, READ, CLOSED by WP-07

**RESOLVED (WP-07), and this section's account is wrong twice over.** It names
`_dash_split_segs()`; the function actually reached first is
`_dash_check_utf8()`. And "a failed Mata compile surfaces much later as
r(3499)" is only one of three measured outcomes — with one unrelated function
broken, `dash scatter mpg weight` returned **rc 0** and reported "graph
registered", which is worse, because the user has no reason to look.

ROADMAP TR-07.4's remedy — check the return code of the `run` — was measured
to be a regression. A benign *second* load returns r(3000), the same code as a
total compile failure, so vetoing on a non-zero code breaks every user and
every cscript that loads `dash_parse.mata` before `dash.ado`.

`_dash_require_mata` instead checks whether the functions dash calls are
present and, on a miss, **loads the library itself** before re-checking and
reporting. It therefore cannot false-positive, and it repairs a library
cleared by `clear all` rather than complaining about it. See the BUGS.md
entries.

`dash.ado:55` does `capture run "`_dash_matalib'"` and **discards the return
code**. A failed Mata compile therefore surfaces much later as
`_dash_split_segs() not found`, r(3499) — a message that names an internal
function and gives the user nothing to act on.

### J6. Smaller gaps — S3, READ; all but rollback CLOSED by WP-06; rollback deferred by WP-27 (a failed install is reported, not undone)

**RESOLVED (WP-06)** for: the missing `syntax` line (added; measured, a bare
`syntax` gives r(101), not r(198)); the uncaptured `Version(...)` (now
captured, with a fallback); the missing `--user` retry (added, tried once
after a failed install); pip output discarded on the `packaging` install (now
printed, as the package loop already did); no check that `dash_render.py` and
the schemes are reachable (added as `_dash_setup_check_files`, which asks the
RENDERER rather than `findfile`, because `findfile s2color.scheme` succeeds
on the very install where the renderer could read none); and the two sections
both numbered 3 (now 1-6). Rollback is NOT addressed.  **Deferred by WP-27** (24sep2026): a failed install is reported as a failure, never as success (J1, closed by WP-06), and every install is guarded and idempotent, so a rerun of dash_setup completes what a failed one left; undoing a partial pip install is outside what a Stata command should do to a user's Python.

Re-measured 23sep2026 at `4ede074`: `dash_setup.ado` and its help still
contain no rollback or uninstall path, so the heading marks this gap closed
except for rollback, and ROADMAP.md WP-06 lists it the same way, "J6 (all but
rollback)".  The closed rows are certified by
`test/test_setup_honesty.cscript` HON-01 to HON-18 (re-run at `4ede074`:
passed), and since WP-24 by HON-19 to HON-25, which run `dash_setup` itself
with pip replaced by a recorder, and test_program_coverage.cscript PC-15 to
PC-26, which run it end to end in a sandbox that starts no process.

- **`dash_setup` has no `syntax` line at all** (`:15-17`), so
  `dash_setup, garbage(1)` runs normally, silently ignoring the input.
- **No rollback**: bokeh can install before pandas fails, leaving a
  half-configured state.
- **`Version(...)` at `:155-159` has no `capture`** — an unparseable version
  string kills `dash_setup` outright with `r(7102)`.
- **No `--user` retry** on a permission-denied system Python (`:120-127`).
- `r.returncode` from pip is never checked; success is judged by re-import,
  which is the more robust choice but hides *why* an install failed.
- pip output is discarded (`capture_output=True`, `:72-73`), so a `packaging`
  install failure produces no diagnostic.
- `dash_setup` never verifies that `dash_render.py` or the schemes are
  installed and findable — which is why B1 survives a "successful" setup.
- Two sections are both numbered "3" (`:90`, `:175`).
- Idempotency is genuine — every install is guarded (`:67, 117, 177`).
- jsonio from SSC is handled correctly, with `exit 198` on either failure
  (`:177-192`).
- `_dash_pyver_ok` is **correct**, and unit-tested against the classic trap:
  `3.10 vs 3.8`→1, `3.9`→1, `3.7`→0, `3.8.0rc1`→1, `2.7`→0,
  `""`/`abc`/`3.x`→−1, `3.8.19+local`→1.

---

## K. State management

### K1. A KPI silently erases a graph of the same name — S1, MEASURED, CLOSED by WP-04 (ab19c74)

`_dash_register_graph` (`dash.ado:1556-1575`) refuses a duplicate name unless
`name(g1, replace)` is given. **`_dash_kpi` has no such check** — it writes
its globals and appends to the registry unconditionally (`:1928-1956`).

At build time the KPI marker wins: `_dash_prepare_spec:2280` does
`if "${dash_kpi_`gname'}" != "" continue`, skipping the graph.

Measured end to end:

```
. dash scatter mpg weight, name(g1)
dash: graph 'g1' registered.
. dash kpi mean(mpg), name(g1) title("Avg")
dash: KPI 'g1' registered (mean(mpg) = 21.2972972972973).
. dash build, saving("collide_out.html") replace nobrowser
dash: dashboard saved to collide_out.html
```

`rc=0` throughout, no warning. The built file contains **0 Figure models and
0 Scatter models** — the scatter plot is gone. The graph's JSON is still in
`${dash_json_g1}`; it is simply never read.

**Closed by ab19c74 (WP-04).** `_dash_kpi` refuses a registered name unless
`name(x, replace)` is given, both registrars retire the item they replace
(`_dash_drop_item`), and a build names an entry that holds both.  Measured
23sep2026 at `4ede074` with the console binary: after `dash scatter mpg
weight, name(g1)`, `dash kpi mean(mpg), name(g1) title("Avg")` is r(198)
"name 'g1' already exists. Use name(g1, replace) to overwrite."; with
`name(g1, replace)` the graph's `$dash_json_g1` is empty, the registry holds
`g1` once, and the build writes the KPI card and no Scatter.  Certified by
`test/test_registry_collision.cscript` REG-01 to REG-15 (re-run at
`4ede074`: passed).  ROADMAP.md does not yet head WP-04 DONE.

### K2. The registry lives in user-writable globals, read back unvalidated — S3, READ, CLOSED by WP-04 (ab19c74, a documented limitation)

`dash_json_*`, `dash_opts_*`, `dash_graph_registry` and `dash_kpi_*` are
ordinary Stata globals, read back at `dash.ado:2038, 2159, 2167` and flowed
into the JSON spec without revalidation. A user or a stray do-file can
overwrite any of them between `dash … name()` and `dash build`. This is a
design consequence of using globals for session state rather than an
exploitable hole, but it is the one place where spec content bypasses every
input check the command applies at entry.

**Closed by ab19c74 (WP-04), as a documented limitation (TR-04.5).**
`dash.sthlp` says so under "The registry lives in Stata globals": setting
those macros by hand is not supported, and dash validates what it
registers, not what is assigned afterwards.  A hand-made entry holding both
a graph and a KPI is named at build time rather than skipped
(`test/test_registry_collision.cscript` REG-15).  Moving session state out
of globals stays out of scope, as TR-04.5 records.

### K3. Graph-level option precedence across segments — S3, MEASURED, CLOSED by WP-04 (ce65324, its TR-04.4)

Was: "`dash.ado:1125-1133` propagates only non-empty values, so a later segment
can override an earlier one but never clear it, silently." Half right, and it
was READ off the propagation loop rather than measured.

Measured, and against `twoway`'s own answer read out of a saved `.gph`:

- A later segment DOES override an earlier one — as `twoway` does. Correct.
- A later segment CAN clear an earlier value: `title("")` blanks it, in both
  `dash` and `twoway`. The "never clear" half was wrong.
- The real divergence, which neither this entry nor TR-04.4 named: an option
  written after the top-level comma LOST to one written inside a segment.
  `twoway ... , title("AFTER")` over a segment's `title("INSIDE")` gives
  "AFTER"; `dash` gave "INSIDE", because `_dash_plot` fills the `g_*`
  accumulators from the after-comma parse first and the segment loop then
  overwrites them through `c_local`.

Fixed: after-comma values are held in `_gafter_<key>` and restored once the
segment loop has run. `test/test_graph_option_scope.cscript` (GOS-01..08).

**Closed by ce65324** (ROADMAP.md TR-04.4, marked done there); the
certification script re-run 23sep2026 at `4ede074`: passed.

A separate claim — that a graph-level option inside a segment is dropped
entirely — was raised against this entry and is FALSE; it came from a probe
that ran `dash clear` between registrations. See the retracted `BUGS.md` entry.

---

## L. Test coverage

The suite is large and, in several places, genuinely rigorous: **3536 pytest
tests across 84 files**, 25 `.cscript` files, all 38 plot types rendered twice
by `test_every_plot_type_draws.py`, all 14 schemes exercised, 17 real
subprocess server tests (measured: 17 passed in 19.75 s), and a runner that
tracks skips separately and exits 1 if nothing passed. On this machine only
~37 of 3536 pytest tests skip (~1.0%) and **no** cscript skips.

The gaps:

### L1. No CI, no Makefile, no pytest config — S2, MEASURED, CLOSED by WP-25

No `.github`, `.gitlab`, `travis` or `circle` config; no `pytest.ini`,
`pyproject.toml` or `setup.cfg`. Both suites are invoked by hand. **Nothing
enforces that either runs before a commit.**

**Closed by WP-25** (24sep2026): the maintainer chose local CI -- GitHub's
runners have no Stata, and `wbuchanan/dash` is private with nothing pushed
to it -- so `make check` runs pytest under the Python Stata ships and under
the development interpreter, both strict, then the certification suite,
judged from its log by `scripts/cert_verdict.py`; `make hooks` has `git
push` run it first (`scripts/git-hooks/pre-push`), and `pyproject.toml` is
the committed pytest configuration.  Held by `test/test_cert_verdict.py`
and `test/test_strict_mode.py`.

### L2. The two suites run under different interpreters — S2, MEASURED, CLOSED by WP-25

pytest runs on `/opt/homebrew/bin/python3` 3.14.5 (bokeh 3.9.0, pandas 3.0.1);
Stata's `c(python_exec)` is `/opt/anaconda3/bin/python3` (bokeh 3.8.0, pandas
2.3.3). `conftest.py:41-52` documents this exactly and only `warnings.warn`s.
**A green pytest run does not prove the Stata path works against the libraries
it actually loads.**

**Closed by WP-25** (24sep2026): `make test` runs the whole pytest suite
under Stata's `c(python_exec)`, read from Stata itself, and `make test-dev`
under the development interpreter; under `DASH_STRICT=1` conftest.py stops a
run whose environment differs from its baseline (`stata` or `dev`) and fails
any skip.  The first run under Stata's Python found six failures the
development interpreter never showed -- the served app's origin check
admitting `localhost.evil.example` under bokeh 3.8, a date column blanked by
one far-future value under pandas 2.3, and three tests that depended on the
environment -- each fixed (BUGS.md).

### L3. The UTF-8 guard's rejection branch has never executed — S1, READ, CLOSED by 7ddbc08 and WP-24 (WP-08's test_utf8_validation.cscript, and WP-24's UTF-13 and exact gates)

`_dash_check_utf8` is called by exactly two tests
(`test_ado_loads.cscript:94`, `test_mata_autoload.cscript:52`) and **both pass
`""`**, which is trivially valid. The failure path (`dash_parse.mata:149-153`)
and all of `_is_utf8` (`:90-133`) are unproven. No test feeds invalid UTF-8,
overlong encodings, or surrogate halves — precisely the "string encoding to
bypass standard injection vectors" case CLAUDE.md rule 16 names, at the rule's
designated enforcement point.

**Closed by 7ddbc08**, WP-08's test plan row written for this gap:
`test/test_utf8_validation.cscript` feeds `_is_utf8` every sequence of
`test/fixtures/utf8_cases.txt` against Python's own decoder (UTF-01 to
UTF-10) and runs `_dash_check_utf8` itself on a UTF-16 surrogate, which it
rejects (UTF-12).  Re-run 23sep2026 at `4ede074`: passed.  The traceability
matrix gives L3 to WP-24 (with WP-08).

**Tightened by WP-24** (24sep2026).  Measured: with the gate's message
reduced to "invalid input" UTF-01..12 all passed, and with its exit code
changed UTF-01..12 did; a fixture cut to its comments was a skip; a gate
moved from one program to another, or commented out with `*`, still counted
six.  UTF-13 runs every sequence of A9's table through the gate for r(198)
and "non-UTF-8"; UTF-10 holds exactly 2,245 fixture sequences and exits 601
on a missing fixture; UTF-11 names the program each of the six gates sits
in.

### L4. Tests that assert a name exists rather than a behaviour — S2, READ, CLOSED by WP-24

`_dash_json_get_str` — added *as the fix* for the "immediate render truncates
quoted `if` expressions" bug — is covered only by
`assert "_dash_json_get_str" in src` (`test_server.py:4694-4712, 4828-4833`).
The regression test for the fix asserts the fix's *name* exists. Same shape at
`test_paired_coordinate_plots.py:139,151` and `test_serve_options.py:71-157`,
which parse `dash.ado` as a string.

`test_server.py` is 474 KB / 423 test functions and **never starts a server** —
all coverage is `ServerAppBuilder` text/AST inspection. So ~420 "server" tests
prove the generated *source* is right and 17 prove it *runs*.

**Closed by WP-24** (24sep2026).  Every test that reads source text was
classified -- 481 of them: 46 were the only coverage of their behaviour, 89
deliberate structural guards (each now says so in its docstring), 205
duplicated by a behavioural test, 141 not source tests at all.  All 46 run
the code now: `_dash_json_get_str` has 43 behavioural cases and
`test_qualifier_literals.cscript` QL-01..15; the paired-coordinate checks
are `test_parser.cscript` P1A-56; `test_serve_options.cscript` [6/7] and
[7/7] run `_dash_serve_spec`; the Windows browser commands run through one
opener, `_dash_open_page`, whose command each platform's case reads
without running it (`test_serve_browser.cscript` SB-13..20); `dash_setup`'s
eight source checks are held by runs of `dash_setup` itself in a sandbox
(`test_setup_honesty.cscript` HON-19..28, `test_program_coverage.cscript`
PC-15..26); the layout and websocket-origin checks of
`test_adversarial_matrix.py` drive both modes and a live server.  Of
`test_server.py`'s 39 app-source tests, 35 had a behavioural twin, 2 are
structural guards, and the other 2 now run the app: a filter move leaves a
pci segment where it was, and `by_total` adds its panel in both modes.

### L5. Three tests cannot fail — S2, READ, CLOSED by WP-24

- `test_filter_label.py:155-161`, `test_a_payload_does_not_reach_the_document`:
  wraps the render in `except Exception: return`, so any exception is green;
  its `out = dr.render() if False else None` at `:159` is dead code, so the
  render it claims to inspect never runs; and it asserts only that a widget
  list is non-empty — it never checks the payload.
- `test_options.py:260-262` catches `AssertionError`, so it cannot fail by
  construction.
- `test_filters.py:209-211` swallows `ValueError`/`KeyError`.

A further 19 of 2340 test functions have no verification at all. Eleven are
honest "does not crash" cases; the rest promise more than they check —
notably `test_resource_limits.py:206`
`test_a_power_tower_does_not_hang_the_served_app`, a resource-exhaustion test
with no assertion and no timeout.

**Closed by WP-24** (24sep2026).  Measured at `a2c7502`: 23 of 4367 test
functions verified nothing (the count above predates the suite's growth),
and the `if False` line is gone.  All 23, and the three above, assert what
they name, each shown to fail under a break of its subject;
`test_options.py`'s claim was false -- nothing clamps an out-of-range RGB --
and three tests of what Stata does replace it.  `test/test_test_integrity.py`
fails a test that catches AssertionError, swallows an exception, verifies
nothing, returns before verifying or asserts what cannot be false, with an
empty allowlist.

### L6. Pass conditions that go vacuously green on a wording change — S2, READ, CLOSED by WP-24

`test_conformance.cscript:126-146` (C-03) detects failure by string-matching
`"drew nothing"` in a Stata log. `test_every_plot_type_draws.py:77-95` derives
its parametrization from a regex over the display string at `dash.ado:940-944`;
reflow that message and a type silently drops out, and the `>= 30` guard at
`:139` would not notice losing one or two.

**Closed by WP-24** (24sep2026).  C-03 and C-04 read the saved page's
document, C-01's corpus is the renderer's own list of plot types, and C-00
tests the readers; `test_every_plot_type_draws.py` is parametrized by
`_dash_plot_type_names()`, held equal to the Mata table.  The same shapes
were found throughout and replaced with checks of what the page or the app
draws: floors made exact, needles that the inlined BokehJS carries on every
page read from the document instead, absence checks given controls, loops
that could run zero times guarded, a skip where a failure belonged made a
failure.  `cert_file_has` searched 32,768-character pieces alone and log
searches depended on the checkout's path; `cert_helpers.do` reads files
whole and `cert_log_has` searches a log's logical lines.

### L7. Untested programs and functions — S2, READ, CLOSED by WP-24

Never named in any test file: `_dash_formats_json` (`dash.ado:1266`),
`_dash_date_fmts_swap` (`:1309`), `_dash_date_fmts_restore` (`:1322`). These
three are also the only three omitted from the existence loop at
`test_ado_loads.cscript:69-77`. Format strings are user-supplied and flow into
the spec JSON.  (Corrected by WP-24: the loop listed 22 of the 56 programs
then, not all but these three.)

**`dash_setup` itself is never executed** — 75 textual hits, zero invocations.

`dash serve`'s happy path: zero coverage (see C2).

**Closed by WP-24** (24sep2026).  Instrumented, the certification suite
entered 61 of 63 ado programs (`dash_setup`'s body never) and 52 of 55 Mata
functions, and pytest executed 434 of 440 renderer functions.
`test_program_coverage.cscript` PC-01..11 and PC-31 test the three programs
with ordinary, edge, hostile and abbreviated input on both routes -- they
lost a hostile date format, and a failing jsonio left dates `%12.0g`, both
fixed -- and PC-15..26 run `dash_setup` end to end in a sandbox that starts
no process.  `test/program_coverage_map.py` names the behavioural test of
every ado program and Mata function, and `test/function_test_map.py` that of
every renderer function, each measured to fail when the function's body is
skipped; their guards fail on a unit with no test.  `dash serve`'s happy
path is C2's, closed by WP-23.

### L8. Dead test assets — S3, MEASURED, CLOSED by WP-25

15 of 17 `.do` files in `test/` are referenced by nothing
(`test_build_s3.do`, `test_r_trace{,2..6}.do`, `test_if_expr{,2}.do`, …).
`test/fixtures/scheme_visual/` (9 PNGs + `truth.json`) is referenced by zero
test files, yet `test_fixtures_are_committed.py:83-90` enforces them as
git-tracked with a docstring claiming each is "read by the test suite" —
false for these 9.

`test_scheme_fidelity.py:213-234, 721-731` asserts the parser *exposes*
`symbolsize`, `graphsize_x/y`, `legend_position`, `legend_cols` — never that
they reach rendered output. That is exactly why G4's dead attributes pass the
suite today.

`test/fixtures/abbrev_truth.json` records 7 historical option-key
mis-mappings and 18 declared options that rejected Stata's minimum
abbreviation. **All 25 were verified fixed in current code** (measured live,
reading the key back out of the emitted JSON): `xl`→`xlabel`, `yl`→`ylabel`,
`m`→`msymbol`, `mlc`→`mlcolor`, `mlw`→`mlwidth`, `mls`→`mlstyle`,
`mlp`→`mlpattern`, plus `ml c xli yli psty mlabc aspect barw cmiss colorcut
colordis colorv mlabg mlabp mlabs xt yt`. The fixture is a **stale pre-fix
record, not current behaviour**, and should say so — otherwise the next
auditor re-reports 25 resolved items as live gaps.

**Closed by WP-25** (24sep2026): the 15 dead `.do` files are deleted -- none
held an assertion, and the certification suite holds what they probed
(JSE-12, HC1-05 and QL-01 fail with the March strip restored).
`scheme_visual/` -- 8 PNGs, not 9, and `truth.json` -- is read by
`test/test_scheme_visual_truth.py`, which holds the scheme parser's colours,
symbols, patterns and sizes, not only their presence, to what Stata drew,
and each PNG to its record; it found two disagreements, pinned as strict
xfails (BUGS.md).  `test/test_fixtures_are_committed.py` fails any fixture
no test names and any `.do` file nothing runs.  `abbrev_truth.json`'s
`_meta.status` says it is the pre-fix record.

### L9. Bug-regression convention — S3, READ, CLOSED by WP-24

`BUGS.md` holds 73 entries, all `[x]`. 67 name a regression test in their
Resolution; **six do not** (`BUGS.md:341, 359, 383, 395, 413, 431`), two of
which are security fixes. CLAUDE.md rule 8 asks for a test per fixed defect.

Re-measured 23sep2026 at `4ede074` (WP-23, TR-23.5): of 253 closed
entries, 26 named no test that exists -- 23 named none, and 3 named a test
class that 0591142 had deleted.  Of the six above, one names a test by
`4ede074` (the sixteen glyph properties, `test_mode_parity.py`), four had a
test all along that was never named (the long `function()` expression, the
`mband` clamp, `pci`, the custom scheme's bare name) and now name it, and
one has none.  With 19 others, 23 entries now point at the test that covers
them.  Three closed entries have no covering test at all and say so:
`comprehensive_demo.do`'s fills, the "file not found" note on every
`dash build`, and `ylabel(#5, grid)`.
`test/test_tracking_documents.py` now fails any closed entry that names no
existing test, except those three, which it lists by name
(`CLOSED_WITHOUT_A_TEST`).

**Closed by WP-24** (24sep2026): `test/test_bug_regressions.cscript` BR-01
(the fills, in both modes), BR-02 (no "file not found" on `dash build`, the
one-line form or `dash serve`; WP-03's AC-03.4) and BR-03 (`ylabel(#5,
grid)` against twoway), with `test/test_bug_regressions.py`, each failing
with its fix reverted.  `CLOSED_WITHOUT_A_TEST` is empty.

### L10. Auth bypass — not a gap — standing note (WP-20)

`dash` has no auth model, and `test_security_surface.py:95` establishes that
the help does not claim one. CLAUDE.md rule 19 is N/A. Worth stating
explicitly rather than leaving as an apparent hole.

**Standing note, recorded by WP-20.** CLAUDE.md rule 19 does not apply to
dash, by design and not by omission: dash has no accounts, no
administrators and no administrative component.  Every dashboard is built
by the Stata user who runs the command; the served app binds loopback by
default and offers no privileged route (`/health` reports liveness and
nothing else).  So for rule 18's three adversarial cases, "auth bypass"
means getting past a surface's own guard -- its validation, escaping, path
containment, origin check or rate limit -- and that is how
`test_adversarial_matrix.py` (whose module docstring carries this note) and
`test_adversarial.cscript`'s P20 section read it.  If dash ever gains
accounts or an administrative surface, this note is wrong and rule 19
applies.

**Since WP-29 (P0.12a, commit 7f5c8f5).** The served app now requires a per-launch secret token: without it no session, page, autoload, metadata or row reaches a client, `/health` and BokehJS's static files stay open, and the token is compared in constant time. The app never runs without its token: started without one, it makes its own and writes its link to a file only the user can read; only when no such file can be written anywhere does it print the link, once, after a warning, to the output of whoever started it. The sentence above that dash has no auth model no longer describes the served app. dash still has no accounts, administrators or administrative component, so rule 19 still does not apply; the adversarial reading of "auth bypass" above now also covers getting a session without the token. Guarded by `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_the_page_without_the_token_is_403`, `test/test_serve_token.py::TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`, `test/test_serve_token.py::TestTheLauncherPassesTheToken::test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served` and `test/test_serve_launch.cscript` TOK-03.

---

## M. Documentation and repository hygiene

### M1. The tracking documents no longer describe reality — S2, CLOSED by WP-23

`TODO.md` holds 555 items, **all checked**. `BUGS.md` holds 73, **all
closed**. Yet 39 options are inert, `dash serve` aborts on every option, and
every `net install` loses its schemes. The tracking documents and the code
disagree.

`PLAN.md` and `TODO.md` were last touched at `5f857fc`. `REMAINING.md` (198 KB)
and `phases/` (31 phase documents, 249 work items) are the current record;
the older two describe an overtaken roadmap.

The two paragraphs above are the audit of 2026-09-21 at `187a786`.  What
is true at `4ede074`, measured 23sep2026 by WP-23's TR-23.5:

- **`TODO.md` and `PLAN.md` are retired**: deleted from the tree, not
  reconciled.  Their last change is `5f857fc` and they are unchanged
  through `4ede074`, the last commit that holds them (`git show
  4ede074:TODO.md`).  ROADMAP.md, this document and BUGS.md are the record,
  with `REMAINING.md` and `phases/` beside them.
- **`BUGS.md`** held 260 entries at `4ede074`, 253 closed and 7 open.  Two
  of the open ones were already fixed (the served `layout(bs)`, 31e76e0;
  the linked `by()` filter move, 7c2c918) and are closed with the commit
  and the test that fails without it; the other five are open with a
  measurement of 23sep2026 and the reason.  Two defects found while
  measuring are added, open: `dash serve` aborting on every launch (C1) and
  a served `by()` title that ignores the variable's format.  Of the closed
  entries, 26 named no test that exists -- 23 named none, and 3 named a
  test class 0591142 had deleted; 23 of them now point at the test that
  covers them, and 3 have no covering test (L9, WP-24).  Two closed entries
  that left part of their fix open now record the commit that finished
  it.
- **This document**: every gap a DONE work package lists is marked closed
  and every closed gap names the work package or commit that closed it,
  except J6, whose rollback no package has done (ROADMAP.md WP-06 lists J6
  unqualified).  The gaps of WP-01, WP-02 and WP-04, whose work is
  committed but which ROADMAP.md does not head DONE, are closed by commit;
  WP-03's were not all closed at `4ede074`, because `dash serve` aborted
  again (C1) -- WP-23 fixed it and closes C1 and C2.
- `test/test_tracking_documents.py` holds all of this mechanically.

**Closed by WP-23.**  With its other parts integrated, BUGS.md holds every
defect WP-23 found and fixed, with the test that fails without the fix, and
the open entries it changed record what is still open and why; GAPS.md
and ROADMAP.md agree on every gap a DONE work package closes; and
test/test_tracking_documents.py holds the three to it.  `.ultraplan/`,
`REMAINING.md` and `phases/` are the user's own records, with uncommitted
changes in the user's checkout, and are left to them.

### M2. Branch state — S3, MEASURED, CLOSED by WP-27 (the merge is the maintainer's to run; their planning files stay uncommitted by their choice)

62 commits ahead of `main`, with 53 uncommitted working-tree entries
(a `.ultraplan` reorganisation, an archive directory, and a modified
`REMAINING.md`). None of this has been merged or released.

Those two numbers are a snapshot of 2026-09-21 at `187a786`.  Re-measured
23sep2026 at `4ede074`: the branch is 107 commits ahead of `main` and none
behind (`git rev-list --count main..4ede074` and `4ede074..main`); `main`
(`3948ce8`) is an ancestor, so nothing has been merged into it or released.
The uncommitted entries live in the user's main checkout and were not
re-counted: they are the user's own work, which WP-27's TR-27.6 commits or
discards, and this measurement did not touch them.  The status of that
checkout at the start of the 23sep2026 session still listed the
`.ultraplan` reorganisation, the archive directory and a modified
`REMAINING.md`, `CLAUDE.md` and `test/conftest.py`.

**Closed by WP-27** (24sep2026): every commit of the roadmap's work is on
the working branch, with the merge command reported to the maintainer
rather than run (CLAUDE.md rule 6).  The uncommitted entries were the
maintainer's own planning files -- the `.ultraplan` reorganisation and its
archive, `phases/`, `REMAINING.md` and `CLAUDE.md`; asked whether to commit
or discard them, the maintainer chose to leave them uncommitted, so they
are outside the package's history by decision, and nothing of the
package's own work is left uncommitted.

### M3. Development artefacts in the package root — S3, READ, CLOSED by WP-26

`regen_bootstrap_examples.py`, `regen_comprehensive.py`, `regen_dashboards.py`
and eight generated `*.html` files (1.2–2.0 MB each, ~13 MB total) sit
alongside the shippable sources. They are not in `dash.pkg`, so they do not
ship, but they dominate the repository.

**Closed by WP-26** (24sep2026): the three `regen_*.py` scripts are in
`scripts/`, and still write the example pages to the package root.  The
pages -- eleven on this machine -- were never in the repository:
`.gitignore`'s `*.html` has always dropped them, so they cluttered only the
working tree.  `test/test_packaging.py` now fails when git tracks a file in
the root that neither ships nor is one of the repository's documents or
configuration.

### M4. Duplicated source blocks — S3, CLOSED by WP-23

The generator NOTE comment appears twice back-to-back at `dash.ado:266-275`
and again at `:459-469`. The T/B/L/R folding block is duplicated verbatim
within `_dash_parse_graph_opts` (`:316-319` and `:340-343`). The rationale
those comments give is also measurably wrong: `T1title` yields minimum
abbreviation `t`, not `t1` — measured, `_dash_parse_plot_opts , t("Top")`
resolves to `t1title` without any `T(string)` declaration, so the explicit
`T B L R` declarations at `:301-302` are redundant.

**Closed by WP-23.**  All four copies of the generator NOTE (two in each
option parser) and three copies of the t/b/l/r fold (two in
`_dash_parse_graph_opts`, one dead in `_dash_parse_plot_opts`) were still
there at `4ede074`; each is gone, and the one NOTE left says truthfully that
the block is no longer generated.  The rationale was re-measured with
Stata's `syntax` and is as recorded: `T1title()` admits `t`, so the
explicit `T() B() L() R()` were reached only by a third spelling after
`t1title()` and `t2title()`, which the fold then dropped without a word at
graph level -- a bug the removal fixes (BUGS.md; test/test_alias_semantics.cscript
AS-06b and test/test_abbreviations.py's fold checks).

### M5. Latent `inlist()` ceiling — S3, CLOSED by WP-23 (the ceiling went with WP-22's ad13a0f, which WP-23 verified)

`dash.ado:1004-1005` and `:1146-1147` carry exactly 9 literals plus `ptype` —
Stata's 10-argument `inlist()` limit. **A tenth range plot type will fail to
compile.**

The ceiling itself is gone at `4ede074`: ad13a0f (WP-22's TR-22.4) made
every plot-type test in `dash.ado` a `: list ptype in <family>` over family
lists defined once, and no `inlist()` on a plot type is left
(`test/test_plottype_families.py`; `test/test_parser.cscript` P1A-56, where
a tenth range member is found while `inlist()` of the same list is r(130)).
**Closed by WP-23**, which lists it: re-measured on the WP-23 tree, no
string `inlist()` of ten or more arguments is left in dash.ado (the largest
holds seven) and dash_setup.ado has none; in Stata a value and nine
literals run, a value and ten are r(130), and a ten-member `: list ... in`
finds its tenth member.

---

## N. Dead code — S3, READ, CLOSED by WP-26

| Item | Location | Evidence |
|---|---|---|
| `_dash_graph_opts_to_json` | `dash.ado:891-913` | Zero callers. Graph JSON is assembled inline at `:1462-1480`. The dead helper emits a *smaller* key set, so it is a trap: an auditor reading it would report ~26 false inert options. Corrected 24sep2026 by WP-24's program coverage: it emits nothing at all -- it reads the `g_*` locals of its own scope, which are always empty, so it returns `{}` whatever its caller holds (test/program_coverage_map.py records it). |
| `_dash_kv_json` | `dash.ado:242-251` | Zero callers. |
| `_json_escape`, `_html_escape` | `dash_parse.mata:53, 71` | Called only by `_dash_json_esc`/`_dash_html_esc`… |
| `_dash_json_esc`, `_dash_html_esc` | `dash_parse.mata:82, 85` | …which have zero callers anywhere. `dash.ado` escapes in `_dash_json_str` (`:224`) instead. |
| `map_pci` | `dash_render.py:5516` | Unreachable — delegates to `map_pcspike`, which needs variable names, but `pci` is emitted as a literal `values` array. The live path is `map_pci_literal` (`:5548`). Still listed in `pc_dispatch` (`:10454`). |
| `"sc"`, `"li"`, `"hist"` dispatch aliases | `dash_render.py:10362, 10365, 10379` | Unreachable — `_expand_plottype_str` always writes the full name. |
| Scheme `#include` support | `dash_render.py:1786-1800` | Zero of the 14 shipped schemes use it. |
| The ambiguity branch in `_expand_plottype_str` | `dash_parse.mata:225` | **Unreachable.** Brute-forcing every prefix of all 38 plot-type names gives a maximum hit count of 1: the `strlen(name) >= strlen(minab)` gate at `:218` structurally suppresses the longer candidate in every colliding pair. The comment "or an ambiguous prefix" describes nothing that can happen. |
| 15 `.do` files, 9 PNG fixtures | `test/` | See L8. |

**Closed by WP-26** (24sep2026).  Deleted: `_dash_graph_opts_to_json`,
`_dash_kv_json`, `_html_escape`, `_dash_json_esc`, `_dash_html_esc` and
`map_pci`, and two more that only tests called, `_dash_imm_gettoken` and
`_dash_pc_immediate` (their tests now call `_dash_imm_next` and
`_dash_immediate`, what production runs); `_json_escape` stays, used since
WP-24.  The `"sc"`, `"li"` and `"hist"` aliases are gone from both modes.
The ambiguity branch is gone: measured in Stata, no prefix of the table's
40 rows reaches two, and twoway itself has no ambiguous plot type (of 209
prefixes of 45 names, 127 are "not a twoway plot type", 82 resolve to one).
`#include` and the other scheme-parser branches are kept and now tested
against Stata's drawing, which found four open defects (BUGS.md).  The
renderer's DEAD list (10) is deleted and its TEST_ONLY list (13) is down to
four test seams kept on purpose.  The 15 `.do` files and the PNGs were
closed by WP-25 (L8).  `test/test_no_orphans.py` and
`test/test_function_test_map.py` fail when an uncalled definition returns.

### N1. Stale file headers — S3, READ, CLOSED by WP-26

`dash_parse.mata`'s header **lists `_dash_json_esc` and `_dash_html_esc` as
"Public API (called from dash.ado)"** at lines 34-35. Both are dead. The same
header claims at line 8 that Mata performs option-key abbreviation expansion
— that code was removed (`dash_parse.mata:239-268`); Stata's `syntax` resolves
option prefixes now. `dash.ado:14-16` repeats the same stale architecture
claim. The Public API list also omits four functions that *are* called:
`_dash_extract_filters`, `_dash_extract_qual_vars`, `_dash_option_names`,
`_dash_path_badchar`.

**Closed by WP-26** (24sep2026): measured, the list omitted eight of the 27
functions dash.ado calls, not four, and named two it does not call beside
the dead pair.  It is now exactly `_dash_require_mata`'s `_needed` list;
neither header claims the expansion; three caller notes name every caller.
Held by `test/test_file_headers.py`.

---

## Prioritised remediation

**Wave 1 — wrong numbers and broken installs**

1. **A6/A7** — two one-line-ish parser fixes with the worst
   consequence-to-effort ratio in the list. Drop `& depth == 0` at
   `dash_parse.mata:468, 473, 303, 308`; add quote tracking to
   `_dash_extract_filters`. Add a cert case for a paren inside a quoted
   option value, and one for `filter(` inside a quoted title.
2. **A1/A2** — pass `view` (or a pre-filtered frame) into the 13 computed
   mappers. One defect, three user-visible wrong-answer bugs, and the facet
   one produces confidently wrong statistics with no warning.
3. **B1** — make installed schemes reachable: add the PLUS letter fan-out to
   `_SCHEME_SEARCH_DIRS`, or have `dash.ado` `findfile` each scheme and pass a
   directory into the spec. Add a `net install`-and-render gate to the suite.
4. **C1** — strip the leading comma at `dash.ado:2601`, exactly as
   `_dash_build` does at `:2440`. Then give `dash serve` a happy-path test
   (C2).
5. **K1** — make `_dash_kpi` check the registry and require `replace`, as
   `_dash_register_graph` does.
6. **J1** — add `exit 198` after `dash_setup.ado:53-57`, or stop claiming
   success at `:199`.

**Wave 2 — the server-unification lever**

7. **D1** — route the server's plot dispatch through `GlyphMapper`. Once a
   type delegates, it inherits every standalone fix instead of needing its own
   copy. Doing the dependent work first means doing it twice.
8. **D2/D3/D4/D5** — `pci`, `fpfitci`, the `pc*` shared-variable cases, hover,
   per-plot and KPI qualifiers, and the facet dispatch.
9. **D8** — extend `test_mode_parity.py`'s `CORPUS` to all 38 types plus
   `by()`/`link()`/`tabs()`/KPI, and make `_glyph_profile` collect tools and
   tooltips.

**Wave 3 — honesty of the surface**

10. **A3/E2** — either honour weights, `link()`, `filter()` and named-graph
    `saving()`, or report them. Silence is the problem.
11. **E1** — take `nodraw` off both pending lists.
12. **E3** — give `by()`, `legend()` and `filter()` an unknown-sub-option
    warning; stop discarding a whole `filter()` group in silence.
13. **E4** — make the `bw` fold plot-type-aware, or drop the alias.
14. **E6/A9** — `\uXXXX`-escape all C0 controls in `_dash_json_str`; tighten
    `_is_utf8`'s second-byte ranges to reject surrogates, overlongs and
    anything above U+10FFFF; escape `theme()`; un-escape the extracted
    `saving()` path; and call `_dash_check_utf8` from `_dash_kpi`,
    `_dash_build` and `_dash_serve`.
15. **A8** — make the splitter error on an unbalanced `(` or `"` at
    end of scan, instead of silently returning one segment.

**Wave 4 — fidelity, limits, coverage**

16. **G3** — stop drawing the minor grid unconditionally.
17. **G5/G4/G6** — fix the `gsize` and `linewidth` scale factors; wire or
    remove `note_font_size`, `p_mark_colors`, `legend_position`,
    `legend_cols`; stop the inline KPI style overriding `css_block()`.
18. **I2** — add caps for dropdown cardinality, `by()` groups, facets and
    dataset size; replace `_MAX_IPS` with a structure that actually limits.
19. **L3/L5/L6** — test `_dash_check_utf8` with real invalid UTF-8; fix the
    three tests that cannot fail; replace the string-matching pass conditions.
20. **J3/J4/J5** — probe Python with `c(python_exec)` before the first
    `python:`; give `dash` the same "run dash_setup" diagnostic it gives for
    `jsonio`; check `_rc` from the Mata `run` at `dash.ado:55`.
21. **L1/L2** — add a CI config that runs both suites, and make the
    interpreter-drift warning a failure there.
22. **L8** — annotate `test/fixtures/abbrev_truth.json` as a pre-fix record,
    and fix or delete the stale file headers (N1).
23. **F4/F2/F1** — reconcile the help: fractional percentiles, `nodraw` on
    `dash build`, bare-name custom schemes, the scipy attribution, the
    semicolon claim, the `xtick()` semantics, `colorvar()`'s scatter-only
    scope, and a supported-plot-types list naming the 11 undocumented types
    and the 4 that error.
24. **N** — delete the dead code, especially `_dash_graph_opts_to_json`.

**Wave 5 — release**

25. **H1** — add a `SaveTool` to both toolbars.
26. **B4** — give `dash.pkg` a `v` line and a `Distribution-Date:`, and sync
    its version to the 2.0 the code declares.
27. **M1** — reconcile `TODO.md`, `PLAN.md` and `BUGS.md` against the code,
    or retire them in favour of `REMAINING.md` and `phases/`.
28. **G1** — translate the six missing user-selectable schemes.

---

## Appendix — environment this review ran in

| | |
|---|---|
| Stata | StataNow 19.5 (StataMP), plus Stata 14–18 present |
| Stata's Python | `/opt/anaconda3/bin/python3` — bokeh 3.8.0, pandas 2.3.3 |
| pytest's Python | `/opt/homebrew/bin/python3` 3.14.5 — bokeh 3.9.0, pandas 3.0.1, numpy 2.4.3, scipy 1.17.1, pytest 9.0.2 |
| `jsonio` | installed, `which jsonio` rc=0 |
| `statsmodels` | installed but **unimportable** in the homebrew interpreter (`ModuleNotFoundError: No module named 'packaging'`), so every `lowess` layer renders empty here |
| node | v24.13.1 |

All Stata probes were run with `global dash_nobrowser 1` set, under
`arch -arm64`, writing to the session scratchpad. No repository files were
modified by this review, and no probe artefacts were left in the tree.

One Bokeh server was started by the `dash serve` probe and was stopped; port
5006 was verified free afterwards.
